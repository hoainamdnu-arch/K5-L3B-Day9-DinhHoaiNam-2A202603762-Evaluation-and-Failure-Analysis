"""Render submission documents from the recorded evaluation evidence."""

from __future__ import annotations

import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
from string import Template

import yaml


def render() -> None:
    root = Path(__file__).resolve().parents[2]
    reports = root / "src/reports"
    templates = root / "src/lab9/templates"

    def read(name):
        return json.loads((reports / name).read_text(encoding="utf-8"))

    def number(value):
        return str(value) if isinstance(value, int) else f"{value:.4f}"

    def metric(spec, name):
        return next(entry for entry in spec["metrics"] if entry["id"] == name)

    def ci_summary(lines, name):
        line = next(line for line in lines if re.match(rf"\s*{re.escape(name)}\s", line))
        match = re.search(r"Δ\s+([+-][\d.]+)\s+CI\s+\[([+-][\d.]+),\s*([+-][\d.]+)\]", line)
        if match is None:
            raise ValueError(f"Missing recorded confidence interval for {name}")
        delta, low, high = match.groups()
        return f"Δ = {delta}, CI 95% [{low}, {high}]"

    def threshold(entry):
        rule = entry.get("threshold", {})
        parts = []
        if "max" in rule:
            parts.append("= 0" if rule["max"] == 0 else f"≤ {rule['max']}")
        if "min" in rule:
            parts.append(f"≥ {rule['min']}")
        if "max_increase" in rule:
            parts.append(f"Tăng không quá {rule['max_increase']:.0%} so với baseline")
        if rule.get("no_significant_drop"):
            parts.append("CI của Δ không nằm hoàn toàn dưới 0")
        return "; ".join(parts)

    baseline1, baseline2 = read("baseline_v1.json"), read("baseline_v2.json")
    fixed, regression = read("eval_fixed.json"), read("eval_seeded_regression.json")
    gates, score = read("gate_v1.json"), read("mutation_scorecard.json")
    aa, traps = read("aa_comparison.json"), read("trap_scorecard.json")
    judges, source_check = read("judge_calibration.json"), read("source_verification.json")
    detection = read("grader_detection.json")
    spec1 = yaml.safe_load((root / "src/config/metric_spec.yaml").read_text(encoding="utf-8"))
    spec2 = yaml.safe_load((root / "src/config/metric_spec_v2.yaml").read_text(encoding="utf-8"))

    digest = hashlib.sha256()
    files = sorted({*root.glob("src/lab9/*.py"), *root.glob("src/lab9/templates/*.md"),
                    *root.glob("src/config/*.yaml"), *root.glob("src/tests/test_lab9*.py")})
    hashes = {}
    for path in files:
        name = path.relative_to(root).as_posix()
        data = path.read_bytes()
        hashes[name] = hashlib.sha256(data).hexdigest()
        digest.update(name.encode() + b"\0" + data)
    packages = {name: version(name) for name in ("pydantic-evals", "numpy", "scipy", "pytest", "PyYAML")}
    implementation = {"sha256": digest.hexdigest(), "files": hashes, "packages": packages}
    (reports / "implementation_manifest.json").write_text(
        json.dumps(implementation, indent=2) + "\n", encoding="utf-8", newline="\n")

    core_rows = "\n".join(
        f"| `{name}` | {number(baseline1['metrics'][name])} | {number(fixed['metrics'][name])} | {number(regression['metrics'][name])} |"
        for name in baseline1["metrics"])
    advanced_rows = []
    for row in score["rows"]:
        report = read(f"eval_{row['shape']}_v2.json")
        verdict = "Chấp nhận" if row["actual"] == "merge" else "Chặn"
        advanced_rows.append(f"| `{row['shape']}` | {number(report['metrics']['pass_rate'])} | "
                             f"{number(report['metrics']['pass_hat_5'])} | {verdict} |")
    kinds = {"safety": "An toàn", "capability": "Năng lực", "system": "Hệ thống"}
    threshold_rows = "\n".join(
        f"| `{entry['id']}` | {kinds[entry['kind']]} | {threshold(entry)} | "
        f"{'Có' if entry.get('blocking') else 'Không'} | {number(baseline1['metrics'][entry['id']])} |"
        for entry in spec1["metrics"])
    dataset_rows = "\n".join(
        f"| v{index} | {report['manifest']['items']} item × {len(report['manifest']['seeds'])} seed | "
        f"`{report['run_id']}` | `{report['manifest']['eval_set_sha']}` |"
        for index, report in ((1, baseline1), (2, baseline2)))
    slice_report = read("eval_slice_regression_v2.json")
    slice_rows = [row for row in slice_report["rows"] if "money_movement" in row["slices"]]
    money_rate = sum(row["pass_rate"] for row in slice_rows) / len(slice_rows)
    floor = metric(spec2, "pass_hat_5")["threshold"]["min"]
    tone, helpful = judges["tone"], judges["helpful"]
    labels = json.loads((root / "src/data/eval/labels_v2.json").read_text(encoding="utf-8"))
    blocked = gates["seeded_regression"]["blocked"]
    bootstrap = spec1["bootstrap"]
    values = {
        "dataset_rows": dataset_rows, "core_rows": core_rows, "advanced_rows": "\n".join(advanced_rows),
        "threshold_rows": threshold_rows, "baseline1_run": baseline1["run_id"],
        "baseline1_sha": baseline1["manifest"]["eval_set_sha"],
        "items1": baseline1["manifest"]["items"], "items2": baseline2["manifest"]["items"],
        "seeds": ",".join(map(str, baseline1["manifest"]["seeds"])),
        "alternate_seeds": ",".join(map(str, read("aa_alternate_v2.json")["manifest"]["seeds"])),
        "confidence": round(bootstrap["confidence"] * 100),
        "resamples": f"{bootstrap['n_resamples']:,}".replace(",", "."), "rng": bootstrap["rng"],
        "core_blocked": ", ".join(f"`{name}`" for name in blocked), "core_blocked_raw": ", ".join(blocked),
        "fixed_ci": ci_summary(gates["fixed"]["lines"], "pass_rate"),
        "regression_ci": ci_summary(gates["seeded_regression"]["lines"], "pass_rate"),
        "regression_gate_line": next(line.strip() for line in gates["seeded_regression"]["lines"] if re.match(r"\s*pass_rate\s", line)),
        "regression_run": regression["run_id"], "fixed_pass": number(fixed["metrics"]["pass_rate"]),
        "regression_pass": number(regression["metrics"]["pass_rate"]),
        "baseline2_pass": number(baseline2["metrics"]["pass_rate"]),
        "baseline2_hat": number(baseline2["metrics"]["pass_hat_5"]),
        "slice_pass": number(slice_report["metrics"]["pass_rate"]),
        "pass_floor": metric(spec2, "pass_rate")["threshold"]["min"],
        "money_slice_pass": f"{money_rate:.2f}",
        "money_slice_floor": f"{next(s['min'] for s in spec2['slices'] if s['name']=='money_movement'):.2f}",
        "flaky_hat": number(read("eval_flaky_regression_v2.json")["metrics"]["pass_hat_5"]),
        "reliability_floor": floor,
        "aa_ci": f"[{aa['paired_pass_rate_ci'][1]:.3f}, {aa['paired_pass_rate_ci'][2]:.3f}]",
        "aa_hat": number(aa["pass_hat_5"]["baseline"]),
        "reliability_margin": f"{aa['pass_hat_5']['baseline'] - floor:.4f}",
        "mutation_killed": score["regressions_blocked"], "mutation_false_alarm": score["false_alarms"],
        "traps_blocked": sum(result["exit_code"] == 1 for result in traps.values()),
        "detection": f"{detection['detection'] * 100:.0f}",
        "grader_false_alarm": f"{detection['false_alarm_rate'] * 100:.0f}",
        "judge_summary": (f"Judge tone đạt κ={tone['kappa']:.3f}, precision={tone['precision']:.3f}, recall={tone['recall']:.3f}, "
                          f"đáp ứng ngưỡng calibration trên replay. Judge helpful có κ={helpful['kappa']:.3f}, "
                          f"precision={helpful['precision']:.3f}, recall={helpful['recall']:.3f} và bị loại do κ và recall thấp."),
        "source_commit": source_check["source_commit"], "locked_files": source_check["locked_files_checked"],
        "implementation_sha": digest.hexdigest()[:16],
        "packages": ", ".join(f"{name} {value}" for name, value in packages.items()),
        "maximum_quote": f"{max(label['proposal_amount'] for label in labels.values()):,}".replace(",", "."),
        "refund_floor_v2": f"{metric(spec2, 'refund_amount_correct')['threshold']['min']:.2f}",
        "trap_rows": "\n".join(f"| `{name}` | {result['exit_code']} | Chặn tại integrity |" for name, result in traps.items()),
    }
    for template, target in (("eval_card.md", "docs/eval_card.md"), ("prd.md", "docs/PRD_v1.1.md"),
                             ("pr_description.md", "docs/PR_DESCRIPTION.md")):
        body = Template((templates / template).read_text(encoding="utf-8")).substitute(values)
        (root / target).write_text(body.rstrip() + "\n", encoding="utf-8", newline="\n")
    print("Rendered eval card, PRD and PR report from recorded evidence and editorial templates.")


if __name__ == "__main__":
    render()
