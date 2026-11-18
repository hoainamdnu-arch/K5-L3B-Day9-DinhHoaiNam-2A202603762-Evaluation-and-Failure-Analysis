# Kết quả hoàn thiện Day09 — Evaluation & Failure Analysis

## 1. Nội dung thay đổi

Phần triển khai bao gồm thống kê calibration, code graders, eval set có taxonomy, paired bootstrap, slice gate và kiểm tra integrity/ratchet. Nguồn Day08 được giữ nguyên và đối chiếu bằng checksum. Các report JSON cung cấp bằng chứng kết quả cho Core, Advanced và Expert trên dữ liệu public.

## 2. Kết quả Core

Baseline có run ID `E-swarm-20261118-20d5`. `fixed` được gate chấp nhận với pass rate 1.0000; `seeded_regression` có run ID `E-seeded_regression-20261118-20d5`, pass rate 0.7143 và bị chặn tại `refund_amount_correct`, `pass_rate`, `reply_amount_correct`, `proposal_correct`.

Kết quả gate ghi nhận mức giảm pass rate có ý nghĩa thống kê:

```text
pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_correct, proposal_correct
```

Kết luận trên phản ánh phép kiểm local giữa candidate và baseline, chưa phải trạng thái merge trên GitHub.

## 3. Kết quả Advanced và Expert

[Mutation scorecard](../src/reports/mutation_scorecard.json) xác nhận **3/3 hồi quy bị chặn**, với **0 báo nhầm**. Cả `fixed` và `honest_refactor` được chấp nhận. Thử nghiệm A/A có Δ=0 ở mọi metric và khoảng tin cậy chênh lệch pass rate [0.000, 0.000].

| Tình huống can thiệp | Exit code của gate | Kết luận |
| --- | ---: | --- |
| `evaluator_errors_as_nan` | 1 | Chặn tại integrity |
| `dropped_failing_rows` | 1 | Chặn tại integrity |
| `cherry_picked_seeds` | 1 | Chặn tại integrity |
| `loosened_spec` | 1 | Chặn tại integrity |

Bốn trường hợp đều bị chặn tại kiểm tra integrity. Gate đối chiếu số dòng, cặp item–seed, điểm tổng hợp, slice và mức độ chặt của metric spec.

## 4. Phạm vi kết luận

Các phép đo sử dụng MockLLM, SQLite và dữ liệu public, chưa bao gồm hidden grading hoặc đánh giá production. [Eval card](eval_card.md) trình bày run ID, khoảng tin cậy và giới hạn; [báo cáo tổng hợp](../SUBMISSION.md) ghi nhận trạng thái triển khai và bàn giao.
