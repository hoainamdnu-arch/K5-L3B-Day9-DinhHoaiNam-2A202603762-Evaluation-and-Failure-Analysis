"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import yaml

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item
from lab9.graders import GRADERS


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []

    def finite(value):
        return isinstance(value, (int, float)) and math.isfinite(value)

    def validate(report, name):
        manifest, rows, metrics = report["manifest"], report["rows"], report["metrics"]
        if not isinstance(manifest.get("eval_set_sha"), str) or not manifest["eval_set_sha"]:
            raise ValueError(f"{name}: missing eval-set digest")
        seeds, items = manifest["seeds"], manifest["items"]
        if (not isinstance(items, int) or isinstance(items, bool) or items <= 0 or
                not isinstance(seeds, list) or not seeds or
                any(type(seed) is not int for seed in seeds) or len(set(seeds)) != len(seeds)):
            raise ValueError(f"{name}: invalid manifest dimensions")
        if not isinstance(rows, list) or len(rows) != items * len(seeds):
            problems.append(f"{name}: row count differs from items x seeds")
        if report.get("evaluator_failures"):
            problems.append(f"{name}: evaluator failure(s)")
        if not isinstance(metrics, dict) or any(value is not None and not finite(value) for value in metrics.values()):
            raise ValueError(f"{name}: non-finite or invalid aggregate")
        identities = [(row["item_id"], row["seed"]) for row in rows]
        if any(not isinstance(item, str) or type(seed) is not int for item, seed in identities):
            raise ValueError(f"{name}: invalid row identity")
        item_ids = {item for item, _ in identities}
        expected = {(item, seed) for item in item_ids for seed in seeds}
        if len(item_ids) != items or len(set(identities)) != len(identities) or set(identities) != expected:
            problems.append(f"{name}: rows are not the unique complete item x seed grid")
        graded = [m["id"] for m in spec["metrics"] if m["id"] in GRADERS or any(m["id"] in r for r in rows)]
        for metric in spec["metrics"]:
            mid = metric["id"]
            value = metrics.get(mid)
            if not finite(value):
                # No successes makes cost/success undefined, but never a capability score.
                no_success = mid == "cost_per_success" and rows and all(r.get("pass_rate") is False for r in rows)
                if not no_success:
                    problems.append(f"{name}: missing/non-finite metric {mid}")
        for mid in graded:
            values = [r.get(mid) for r in rows]
            if not values or any(not finite(v) or v not in (0, 1) for v in values):
                problems.append(f"{name}: missing/invalid row score {mid}")
                continue
            expected_score = sum(values) if mid in ("approval_bypass", "secret_leak") else round(sum(values) / len(values), 4)
            if not finite(metrics.get(mid)) or not math.isclose(metrics[mid], expected_score, abs_tol=0.00005):
                problems.append(f"{name}: aggregate disagrees with rows for {mid}")
        if rows and all(finite(r.get("pass_rate")) and r["pass_rate"] in (0, 1) for r in rows):
            by_item = {}
            for row in rows:
                by_item.setdefault(row["item_id"], []).append(bool(row["pass_rate"]))
            derived = {"pass_5": round(sum(all(v) for v in by_item.values()) / len(by_item), 4)}
            for mid in metrics:
                if mid.startswith(("pass_at_", "pass_hat_")):
                    k = int(mid.rsplit("_", 1)[1])
                    fn = stats.pass_hat_k if mid.startswith("pass_hat_") else stats.pass_at_k
                    values = [fn(len(v), sum(v), k) for v in by_item.values()]
                    derived[mid] = round(sum(values) / len(values), 4)
            for mid, expected_score in derived.items():
                if mid in metrics and (not finite(metrics[mid]) or not math.isclose(metrics[mid], expected_score, abs_tol=0.00005)):
                    problems.append(f"{name}: aggregate disagrees with rows for {mid}")
            if "cost_per_success" in metrics:
                costs = [r.get("cost") for r in rows]
                if any(not finite(v) or v < 0 for v in costs):
                    problems.append(f"{name}: invalid/missing row cost")
                else:
                    successes = sum(r["pass_rate"] for r in rows)
                    expected_cost = round(sum(costs) / successes, 4) if successes else None
                    actual = metrics["cost_per_success"]
                    if expected_cost is None and actual is not None or expected_cost is not None and (
                            not finite(actual) or not math.isclose(actual, expected_cost, abs_tol=0.00005)):
                        problems.append(f"{name}: aggregate disagrees with rows for cost_per_success")
        slices = {}
        for row in rows:
            tags = row.get("slices", [])
            if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags) or len(set(tags)) != len(tags):
                raise ValueError(f"{name}: invalid slice tags")
            key = (row["item_id"], row["seed"])
            slices[key] = frozenset(tags)
        for item in item_ids:
            if len({tags for key, tags in slices.items() if key[0] == item}) > 1:
                problems.append(f"{name}: item changes slice across seeds")
        return set(identities), slices

    try:
        for entry in spec["metrics"]:
            for key in ("min", "max", "max_increase"):
                if key in entry.get("threshold", {}) and not finite(entry["threshold"][key]):
                    problems.append(f"non-finite threshold for {entry['id']}/{key}")
        for entry in spec.get("slices", []):
            if "min" in entry and not finite(entry["min"]):
                problems.append(f"non-finite slice threshold for {entry['name']}")
        base_keys, base_slices = validate(base, "baseline")
        pr_keys, pr_slices = validate(pr, "PR")
        if pr_keys != base_keys or pr["manifest"]["items"] != base["manifest"]["items"] or set(pr["manifest"]["seeds"]) != set(base["manifest"]["seeds"]):
            problems.append("PR: item/seed coverage differs from baseline")
        if pr_slices != base_slices:
            problems.append("PR: slice labels differ from baseline")
        if "seeds" in spec and set(pr["manifest"]["seeds"]) != set(spec["seeds"]):
            problems.append("PR: seeds differ from metric spec")
        for report in (pr, base):
            version = report["manifest"].get("eval_set_version")
            if version is not None and version != spec.get("eval_set_version"):
                problems.append("eval-set version differs from metric spec")
        if base_spec is not None and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
            def ratchet(old, new, label):
                if old.get("blocking") and not new.get("blocking"):
                    problems.append(f"ratchet: {label} no longer blocking")
                before, after = old.get("threshold", {}), new.get("threshold", {})
                for key in ("min", "max", "max_increase"):
                    if key in before and (key not in after or not finite(after[key]) or
                            (after[key] < before[key] if key == "min" else after[key] > before[key])):
                        problems.append(f"ratchet: weakened {label}/{key}")
                if before.get("no_significant_drop") and not after.get("no_significant_drop"):
                    problems.append(f"ratchet: removed {label}/no_significant_drop")
                if old.get("kind") == "safety" and new.get("kind") != "safety":
                    problems.append(f"ratchet: changed safety kind for {label}")

            for section in ("metrics", "slices"):
                def identity(entry):
                    return entry["id"] if section == "metrics" else (entry["name"], entry["metric"])
                new = {identity(m): m for m in spec.get(section, [])}
                if len(new) != len(spec.get(section, [])):
                    problems.append(f"duplicate {section} entries")
                for old in base_spec.get(section, []):
                    key = identity(old)
                    if key not in new:
                        problems.append(f"ratchet: removed {section}/{key}")
                        continue
                    left, right = old, new[key]
                    if section == "slices":
                        left = {**old, "threshold": old}
                        right = {**new[key], "threshold": new[key]}
                    ratchet(left, right, str(key))
            for key in ("seeds", "eval_set", "labels", "adversarial_pack", "bootstrap"):
                if base_spec.get(key) != spec.get(key):
                    problems.append(f"ratchet: changed comparison protocol {key}")
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError) as exc:
        problems.append(f"invalid report/spec structure: {type(exc).__name__}")
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, mid = entry["name"], entry["metric"]
        identifier = f"slice:{name}/{mid}"
        a, b = per_item(pr, mid, name), per_item(base, mid, name)
        failed, note = False, ""
        if not a or set(a) != set(b):
            failed, value, note = True, None, "missing or unpaired slice"
        else:
            keys = sorted(a)
            value = sum(a.values()) / len(a)
            failed = "min" in entry and value < entry["min"]
            if entry.get("no_significant_drop"):
                d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                    n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027), confidence=bs.get("confidence", 0.95))
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                failed = failed or hi < 0
        if failed and entry.get("blocking"):
            blocked.append(identifier)
        verdict = "BLOCK" if failed and entry.get("blocking") else "warn" if failed else "ok"
        lines.append(f"  {identifier:<40} {value!s:<8} {note:<28} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if not all(isinstance(value, dict) for value in (pr, base, spec)):
        return ["integrity"], ["  INTEGRITY report and spec roots must be objects"]
    if not all(isinstance(report.get("manifest"), dict) for report in (pr, base)):
        return ["integrity"], ["  INTEGRITY report manifests must be objects"]
    if pr.get("manifest", {}).get("eval_set_sha") != base.get("manifest", {}).get("eval_set_sha"):
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027),
                                               confidence=bs.get("confidence", 0.95))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    try:
        pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
        base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
        blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        print(f"  INTEGRITY cannot read report/spec: {type(exc).__name__}")
        print("exit 1 — blocked: integrity")
        return 1
    print(f"gate: PR {pr.get('run_id', '?') if isinstance(pr, dict) else '?'} vs main "
          f"{base.get('run_id', '?') if isinstance(base, dict) else '?'}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
