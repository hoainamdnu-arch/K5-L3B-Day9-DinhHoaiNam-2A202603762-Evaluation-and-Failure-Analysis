# Kết quả hoàn thiện Day09 — Evaluation & Failure Analysis

## 1. Nội dung thay đổi

Phần triển khai bao gồm thống kê calibration, code graders, eval set có taxonomy, paired bootstrap, slice gate và kiểm tra integrity/ratchet. Nguồn Day08 được giữ nguyên và đối chiếu bằng checksum. Các report JSON cung cấp bằng chứng kết quả cho Core, Advanced và Expert trên dữ liệu public.

## 2. Kết quả Core

Baseline có run ID `$baseline1_run`. `fixed` được gate chấp nhận với pass rate $fixed_pass; `seeded_regression` có run ID `$regression_run`, pass rate $regression_pass và bị chặn tại $core_blocked.

Kết quả gate ghi nhận mức giảm pass rate có ý nghĩa thống kê:

```text
$regression_gate_line
exit 1 — blocked: $core_blocked_raw
```

Kết luận trên phản ánh phép kiểm local giữa candidate và baseline, chưa phải trạng thái merge trên GitHub.

## 3. Kết quả Advanced và Expert

[Mutation scorecard](../src/reports/mutation_scorecard.json) xác nhận **$mutation_killed/3 hồi quy bị chặn**, với **$mutation_false_alarm báo nhầm**. Cả `fixed` và `honest_refactor` được chấp nhận. Thử nghiệm A/A có Δ=0 ở mọi metric và khoảng tin cậy chênh lệch pass rate $aa_ci.

| Tình huống can thiệp | Exit code của gate | Kết luận |
| --- | ---: | --- |
$trap_rows

Bốn trường hợp đều bị chặn tại kiểm tra integrity. Gate đối chiếu số dòng, cặp item–seed, điểm tổng hợp, slice và mức độ chặt của metric spec.

## 4. Phạm vi kết luận

Các phép đo sử dụng MockLLM, SQLite và dữ liệu public, chưa bao gồm hidden grading hoặc đánh giá production. [Eval card](eval_card.md) trình bày run ID, khoảng tin cậy và giới hạn; [báo cáo tổng hợp](../SUBMISSION.md) ghi nhận trạng thái triển khai và bàn giao.
