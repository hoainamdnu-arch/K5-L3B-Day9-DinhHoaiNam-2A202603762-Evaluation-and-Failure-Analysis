"""Generate all Core/Advanced/Expert evidence from code; run from src/.

python -m lab9.reproduce
No model API, source changes, commits, or remote writes are performed.
"""

from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile

from lab8.console import utf8_stdio
from lab8.shapes import SHAPES
from lab9 import ci_check, evalset, gate, mutation, stats, traps, variants
from lab9.eval import load_spec, load_world, make_task, per_item, run_eval
from lab9.graders import GRADERS
from lab9.judge import calibrate
from lab9.variant_agent import make_shape

OUT = Path("reports")


def write(name: str, value: dict) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
                            encoding="utf-8", newline="\n")


def verify_day8() -> dict:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "artifacts/day8_source_manifest.json").read_text(encoding="utf-8"))
    locked = [record for record in manifest["files"] if record["path"].startswith("src/lab8/") or
              record["path"].startswith("src/data/") or record["path"].startswith("src/config/")]
    changed = [record["path"] for record in locked
               if hashlib.sha256((root / record["path"]).read_bytes()).hexdigest() != record["sha256"]]
    if changed:
        raise RuntimeError(f"original Day08 files changed: {changed}")
    return {"source_commit": manifest["commit"], "locked_files_checked": len(locked), "changed": changed}


def evaluate(shape: str, spec: dict, filename: str) -> dict:
    report = run_eval(shape, spec)
    if report["evaluator_failures"]:
        raise RuntimeError(f"evaluator failures for {shape}; refusing to save evidence")
    write(filename, report)
    print(f"{report['run_id']}: pass_rate={report['metrics']['pass_rate']} → {filename}", flush=True)
    return report


def decision(pr: dict, base: dict, spec: dict) -> dict:
    blocked, lines = gate.check(pr, base, spec, spec)
    return {"run_id": pr["run_id"], "baseline_run_id": base["run_id"], "blocked": blocked,
            "exit_code": int(bool(blocked)), "lines": lines}


def trace_evidence(spec: dict) -> dict:
    """Store safe trace excerpts; the intentional FM-01 raw trace stays ignored."""
    probes = [
        ("FM-01", "C-001", {"no_override", "leaky_trace"}, "debug_claim_row"),
        ("FM-02", "C-007", {"no_override", "ignore_denied"}, "reply"),
        ("FM-03", "C-002", {"ticket_trust"}, "model_override"),
        ("FM-04", "C-014", {"no_override", "sum_parts"}, "proposal"),
        ("FM-05", "C-014", {"no_override", "pre_deducted"}, "proposal"),
        ("FM-06", "C-006", {"no_override", "stale_clause"}, "quote"),
        ("FM-07", "C-001", {"no_override", "sibling_refund"}, "batch_refund"),
        ("FM-08", "C-008", {"no_override", "misreport"}, "reply"),
        ("FM-09", "C-110", {"no_override"}, None),
    ]
    world, claims = load_world(spec)
    labels = json.loads(Path(spec["labels"]).read_text(encoding="utf-8"))
    from pydantic_evals.evaluators import EvaluatorContext

    records = []
    with tempfile.TemporaryDirectory(prefix="lab9-probes-", ignore_cleanup_errors=True) as tmp:
        for mode, claim, bugs, first_kind in probes:
            name = "probe_" + mode.lower().replace("-", "")
            SHAPES[name] = make_shape(name, bugs)
            try:
                trial = make_task(name, world, claims, labels, Path(tmp))({"claim_id": claim, "seed": 11})
            finally:
                SHAPES.pop(name)
            ctx = EvaluatorContext(name=mode, inputs={}, metadata=None, expected_output=labels[claim], output=trial,
                                   duration=0.0, _span_tree=None, attributes={}, metrics={})
            events = []
            for index, event in enumerate(trial["events"], 1):
                payload = event["payload"] if event["kind"] != "debug_claim_row" else {"redacted": True}
                events.append({"step": index, "kind": event["kind"], "payload": payload})
            records.append({"failure_mode": mode, "claim_id": claim, "seed": 11,
                            "run_id": trial["result"]["run_id"],
                            "first_wrong_step": next((e["step"] for e in events if e["kind"] == first_kind), None),
                            "status": trial["result"]["status"],
                            "proposal_amount": trial["result"]["proposal_amount"], "snapshot": trial["snapshot"],
                            "expected": {key: labels[claim][key] for key in ("status", "refund_vnd", "proposal_amount")},
                            "graders": {mid: bool(grader().evaluate(ctx).value) for mid, grader in GRADERS.items()},
                            "events": events})
    return {"scope": "eight injected faults plus a correctly blocked cross-principal control",
            "redaction": "debug_claim_row payload omitted; raw traces are ignored", "cases": records}


def main() -> int:
    utf8_stdio()
    original = verify_day8()
    variants.register()
    evalset.build()
    assert not evalset.check(), evalset.check()
    evalset.build_v2()
    assert not evalset.check(evalset.ITEMS_V2, evalset.LABELS_V2)
    v1, v2 = load_spec(), load_spec(Path("config/metric_spec_v2.yaml"))
    calibration = {name: calibrate(Path(f"data/eval/judge_{name}_public.csv")) for name in ("tone", "helpful")}
    write("judge_calibration.json", calibration)
    assert calibration["tone"]["passed"] and not calibration["helpful"]["passed"]

    baseline = evaluate("swarm", v1, "baseline_v1.json")
    fixed = evaluate("fixed", v1, "eval_fixed.json")
    regressed = evaluate("seeded_regression", v1, "eval_seeded_regression.json")
    core = {name: decision(report, baseline, v1) for name, report in
            (("swarm", baseline), ("fixed", fixed), ("seeded_regression", regressed))}
    assert core["swarm"]["exit_code"] == core["fixed"]["exit_code"] == 0, core
    assert "pass_rate" in core["seeded_regression"]["blocked"], core
    assert not ci_check.check(baseline, baseline, v1)
    write("gate_v1.json", core)
    detection, false_alarms = mutation.detect(v1)
    write("grader_detection.json", {"detection": detection, "false_alarm_rate": false_alarms})
    assert detection >= 0.80 and false_alarms <= 0.10

    baseline2 = evaluate("swarm", v2, "baseline_v2.json")
    card = []
    evaluations = {}
    for name, expected in mutation.EXPECTED.items():
        evaluations[name] = evaluate(name, v2, f"eval_{name}_v2.json")
        verdict = decision(evaluations[name], baseline2, v2)
        got = "block" if verdict["blocked"] else "merge"
        card.append({"shape": name, "expected": expected, "actual": got, **verdict})
        print(f"gate {name}: {got} ({', '.join(verdict['blocked']) or 'clean'})", flush=True)
        assert got == expected, card[-1]
    write("mutation_scorecard.json", {"rows": card, "regressions_blocked": sum(r["actual"] == r["expected"] == "block" for r in card),
                                       "false_alarms": sum(r["actual"] == "block" and r["expected"] == "merge" for r in card)})
    alternate = run_eval("swarm", v2, [66, 77, 88, 99, 110])
    write("aa_alternate_v2.json", alternate)
    comparison = {}
    for metric in baseline2["metrics"]:
        left, right = baseline2["metrics"][metric], alternate["metrics"].get(metric)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            comparison[metric] = {"baseline": left, "alternate": right, "delta": right - left}
    a, b = per_item(alternate, "pass_rate"), per_item(baseline2, "pass_rate")
    keys = sorted(a)
    comparison["paired_pass_rate_ci"] = list(stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys]))
    write("aa_comparison.json", comparison)
    assert comparison["pass_hat_5"]["delta"] == 0
    assert baseline2["metrics"]["pass_hat_5"] > next(m["threshold"]["min"] for m in v2["metrics"] if m["id"] == "pass_hat_5")
    assert not gate.check(baseline2, baseline2, v2, v2)[0]
    trap_results = {}
    for name, (report, weakened) in traps.build(evaluations["slice_regression"], v2).items():
        blocked, lines = gate.check(report, baseline2, weakened or v2, v2)
        trap_results[name] = {"exit_code": int(bool(blocked)), "blocked": blocked, "lines": lines}
        assert blocked, name
    write("trap_scorecard.json", trap_results)
    output = io.StringIO()
    with redirect_stdout(output):
        status = traps.main(["--pr", "reports/eval_slice_regression_v2.json", "--baseline", "reports/baseline_v2.json",
                             "--spec", "config/metric_spec_v2.yaml"])
    (OUT / "traps.log").write_text(output.getvalue(), encoding="utf-8")
    assert status == 0
    write("trace_evidence.json", trace_evidence(v2))
    assert verify_day8() == original
    write("source_verification.json", original)
    from lab9.reporting import render
    render()
    print(f"Complete: Core gates correct; mutation 3/3, false alarms 0; traps 4/4; detection {detection:.1%}; Day08 locked files unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
