"""Independent edge cases for the release gate and the FM-08 reply grader."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from lab9 import gate, stats
from lab9.graders import ProposalCorrect, ReplyAmountCorrect

pytestmark = pytest.mark.student


def _report():
    return {"manifest": {"eval_set_sha": "same", "items": 2, "seeds": [11, 22]},
            "rows": [{"item_id": item, "seed": seed, "pass_rate": True, "slices": ["money"]}
                     for item in ("A", "B") for seed in (11, 22)],
            "metrics": {"pass_rate": 1.0}, "evaluator_failures": []}


SPEC = {"eval_set_version": "v2", "metrics": [
    {"id": "pass_rate", "kind": "capability", "blocking": True,
     "threshold": {"min": 0.8, "no_significant_drop": True}}],
    "slices": [{"name": "money", "metric": "pass_rate", "min": 0.9,
                "no_significant_drop": True, "blocking": True}]}


@pytest.mark.parametrize("attack", ["duplicate", "null", "infinite", "summary", "slice", "failure", "seed", "missing"])
def test_gate_fails_closed_on_corrupt_evidence(attack):
    base = _report()
    pr = deepcopy(base)
    if attack == "duplicate":
        pr["rows"][-1] = deepcopy(pr["rows"][0])
    elif attack == "null":
        pr["rows"][0]["pass_rate"] = None
    elif attack == "infinite":
        pr["metrics"]["pass_rate"] = float("inf")
    elif attack == "summary":
        pr["rows"][0]["pass_rate"] = False
    elif attack == "slice":
        for row in pr["rows"]:
            row["slices"] = []
    elif attack == "failure":
        pr["evaluator_failures"] = ["failed grader"]
    elif attack == "seed":
        pr["manifest"]["seeds"] = [11, 11]
    else:
        del pr["metrics"]["pass_rate"]
    assert gate.check(pr, base, SPEC)[0] == ["integrity"]


@pytest.mark.parametrize("change", ["floor", "drop_metric", "blocking", "drop_slice", "slice_ci", "slice_floor"])
def test_ratchet_prevents_weaker_rules(change):
    weakened = deepcopy(SPEC)
    if change == "floor":
        weakened["metrics"][0]["threshold"]["min"] = 0.1
    elif change == "drop_metric":
        weakened["metrics"] = []
    elif change == "blocking":
        weakened["metrics"][0]["blocking"] = False
    elif change == "drop_slice":
        weakened["slices"] = []
    elif change == "slice_ci":
        weakened["slices"][0].pop("no_significant_drop")
    else:
        weakened["slices"][0]["min"] = 0.1
    assert gate.integrity_check(_report(), _report(), weakened, SPEC)


def test_reordering_rows_does_not_change_pairing():
    base = _report()
    pr = deepcopy(base)
    pr["rows"].reverse()
    assert gate.check(pr, base, SPEC, SPEC)[0] == []


@pytest.mark.parametrize("bad", [None, [], {"manifest": None}])
def test_gate_rejects_invalid_report_structure_without_raising(bad):
    assert gate.check(bad, _report(), SPEC)[0] == ["integrity"]


def test_gate_rejects_nan_threshold_even_without_a_base_spec():
    spec = deepcopy(SPEC)
    spec["metrics"][0]["threshold"]["min"] = float("nan")
    assert gate.check(_report(), _report(), spec)[0] == ["integrity"]


@pytest.mark.parametrize("body,correct", [
    ("Đã hoàn 20.000đ cho đơn O-35000.", True),
    ("Đã hoàn phí 20,000 VND cho đơn O-808 ạ.", True),
    ("Đã hoàn 20 000 đồng.", True),
    ("Đã hoàn 35000đ cho đơn O-808.", False),
    ("Đã hoàn 35.000 ₫.", False),
    ("Đã hoàn -20.000đ.", False),
    ("Đã xử lý xong yêu cầu.", False),
])
def test_reply_amount_is_compared_with_ledger_including_benign_paraphrases(body, correct):
    ctx = SimpleNamespace(output={"events": [{"kind": "reply", "payload": {"text": body}}],
                                  "snapshot": {"refund_vnd": 20000}, "result": {"status": "resolved"}})
    assert ReplyAmountCorrect().evaluate(ctx).value is correct


def test_no_reply_event_is_only_a_vacuous_consistency_pass():
    ctx = SimpleNamespace(output={"events": [], "snapshot": {"refund_vnd": 35000}, "result": {}})
    result = ReplyAmountCorrect().evaluate(ctx)
    assert result.value is True and "no_reply_event" in result.reason


@pytest.mark.parametrize("fn", [stats.pass_at_k, stats.pass_hat_k])
@pytest.mark.parametrize("args", [(0, 0, 1), (-1, 0, 1), (5, -1, 2), (5, 1, -1), (5.0, 2, 1), (True, 0, 1)])
def test_pass_k_rejects_invalid_count_vectors(fn, args):
    with pytest.raises(ValueError):
        fn(*args)


def test_lab9_first_wrong_step_regression_for_overstated_delay(tmp_path, monkeypatch):
    from lab9.trace_case import investigate

    # Config and public fixtures are rooted in src; traces are ignored runtime files.
    broken = investigate("seeded_regression", "C-002", 11)["trial"]
    fixed = investigate("fixed", "C-002", 11)["trial"]
    assert broken["lab8_pass"] is False
    assert broken["snapshot"]["refund_vnd"] == 20000
    assert broken["events"][2]["kind"] == "model_override"
    assert fixed["lab8_pass"] is True and fixed["snapshot"]["refund_vnd"] == 0
    assert not any(e["kind"] == "model_override" for e in fixed["events"])


def test_full_quote_grader_explains_denial_with_no_money_movement():
    ctx = SimpleNamespace(output={"result": {"proposal_amount": 0}}, expected_output={"proposal_amount": 35000})
    assert ProposalCorrect().evaluate(ctx).value is False


def test_lab9_ci_check_accepts_derived_reliability_but_still_requires_a_custom_grader():
    from lab9.ci_check import check

    report = {**_report(), "shape": "swarm"}
    spec = {"metrics": [
        {"id": "pass_hat_5", "kind": "capability", "blocking": True},
        {"id": "reply_amount_correct", "kind": "capability", "blocking": True}]}
    assert check(report, report, spec) == []
    spec["metrics"].pop()
    assert any("no blocking capability metric" in p for p in check(report, report, spec))


def test_lab9_rogan_gladen_handles_an_inverted_classifier():
    # The estimator is still defined for a negative Youden denominator.
    assert stats.rogan_gladen(0.5, 0.4, 0.4) == pytest.approx(0.5)


def test_lab9_constant_judge_fails_calibration_without_a_correction_crash(tmp_path):
    from lab9.judge import calibrate

    path = tmp_path / "constant.csv"
    path.write_text("item_id,reply,human,judge\na,reply,PASS,PASS\nb,reply,PASS,PASS\n", encoding="utf-8")
    result = calibrate(path)
    assert result["passed"] is False
    assert result["corrected_fail_rate"] is None
