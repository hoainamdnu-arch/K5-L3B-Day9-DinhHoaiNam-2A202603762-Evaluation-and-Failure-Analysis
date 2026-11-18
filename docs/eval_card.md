# Eval card — LogiX-VN

**Học viên:** Đinh Hoài Nam · **MSSV:** 2A202603762 · **Lớp:** K5 L3B

## 1. Phạm vi đánh giá

Hệ thống đánh giá đã được kiểm chứng trên dữ liệu public của LogiX-VN với MockLLM. Mục tiêu là xác định biến thể đáp ứng tiêu chí chất lượng, phát hiện hồi quy và kiểm tra tính toàn vẹn của bằng chứng đánh giá. Các kết luận chấp nhận hoặc chặn dưới đây là kết quả của gate local.

| Phiên bản | Quy mô | Baseline run ID | Eval set SHA |
| --- | --- | --- | --- |
| v1 | 14 item × 5 seed | `E-swarm-20261118-20d5` | `20d58cff7a1f` |
| v2 | 28 item × 5 seed | `E-swarm-20261118-7205` | `7205b932d3b2` |

Eval set v1 sử dụng các case public của Day08. Phiên bản v2 bổ sung 14 case adversarial, giữ nhãn tách khỏi item và phân nhóm theo `denial`, `money_movement`, `adversarial`. Cả hai bộ dữ liệu đều vượt qua kiểm tra tính hợp lệ với 0 lỗi.

Các trial sử dụng cùng bộ seed `11,22,33,44,55` và SQLite riêng cho từng lần chạy. Paired bootstrap lấy mẫu trên điểm trung bình theo item qua các seed, với khoảng tin cậy 95%, 1.000 lần lấy mẫu và `rng=2027`. Phương pháp này giữ quan hệ ghép cặp giữa baseline và biến thể được so sánh.

## 2. Kết quả Core

Số liệu được tổng hợp từ [baseline v1](../src/reports/baseline_v1.json), [fixed](../src/reports/eval_fixed.json) và [seeded_regression](../src/reports/eval_seeded_regression.json).

| Metric | Swarm baseline | Fixed | Seeded regression |
| --- | ---: | ---: | ---: |
| `approval_bypass` | 0 | 0 | 0 |
| `secret_leak` | 0 | 0 | 0 |
| `db_fact_kept` | 0.9857 | 1.0000 | 0.9286 |
| `refund_amount_correct` | 0.9857 | 1.0000 | 0.8571 |
| `pass_rate` | 0.9857 | 1.0000 | 0.7143 |
| `reply_amount_correct` | 1.0000 | 1.0000 | 0.7857 |
| `proposal_correct` | 0.9857 | 1.0000 | 0.7857 |
| `pass_5` | 0.9286 | 1.0000 | 0.7143 |
| `cost_per_success` | 49.5670 | 48.7157 | 81.2020 |

Theo [gate v1](../src/reports/gate_v1.json), baseline được chấp nhận khi so với chính nó; `fixed` cũng được chấp nhận. `seeded_regression` bị chặn tại `refund_amount_correct`, `pass_rate`, `reply_amount_correct`, `proposal_correct`.

Chênh lệch pass rate của `fixed` so với baseline là Δ = +0.014, CI 95% [+0.000, +0.043]. Khoảng tin cậy còn chứa 0, vì vậy kết quả chưa chứng minh mức cải thiện có ý nghĩa thống kê. Ngược lại, `seeded_regression` có Δ = -0.271, CI 95% [-0.500, -0.057], thể hiện mức giảm có ý nghĩa thống kê và không đạt sàn chất lượng.

`ReplyAmountCorrect` đối chiếu số tiền công bố trong reply với ledger. `ProposalCorrect` kiểm tra full quote, kể cả khi claim bị từ chối và không phát sinh chuyển tiền. Trong [phép đo grader](../src/reports/grader_detection.json), bộ grader bổ sung giải thích được 100% trial lỗi của `seeded_regression`, với tỷ lệ báo nhầm 0% trên `fixed`.

Swarm gốc không phát sinh reply event. Do đó, kết quả đạt của `reply_amount_correct` ở baseline chỉ phản ánh không có phát biểu tiền tệ để đối chiếu, chưa chứng minh chất lượng lời phản hồi. Parser hiện hỗ trợ số nguyên VND và các cách viết thông dụng với đ, ₫, đồng hoặc VND.

## 3. Kết quả Advanced và Expert

Baseline v2 đạt pass rate **0.9786** và `pass_hat_5` **0.8929**. `Pass^5` biểu thị khả năng một item đạt yêu cầu ở toàn bộ năm lần chạy, còn `pass@k` biểu thị khả năng có ít nhất một lần đạt trong k lần thử.

| Biến thể | Pass rate | Pass^5 | Kết luận gate local |
| --- | ---: | ---: | --- |
| `fixed` | 1.0000 | 1.0000 | Chấp nhận |
| `honest_refactor` | 1.0000 | 1.0000 | Chấp nhận |
| `seeded_regression` | 0.6429 | 0.6429 | Chặn |
| `slice_regression` | 0.9357 | 0.8929 | Chặn |
| `flaky_regression` | 0.9143 | 0.5714 | Chặn |

`slice_regression` có pass rate 0.9357, vượt sàn tổng thể 0.85. Tuy nhiên, slice `money_movement` chỉ đạt 0.85, thấp hơn sàn 0.90, nên bị chặn. Metric full quote cũng phát hiện sai sót trong biến thể này. Kết quả cho thấy điểm trung bình toàn bộ dữ liệu có thể che khuất hồi quy ở nhóm nghiệp vụ quan trọng.

`flaky_regression` bị chặn dù không có event `model_override`; `pass_hat_5=0.5714` thấp hơn sàn 0.85. `honest_refactor` được chấp nhận dù có cảnh báo chi phí, do chi phí là metric theo dõi và không phải điều kiện chặn.

[Mutation scorecard](../src/reports/mutation_scorecard.json) ghi nhận **3/3 biến thể hồi quy bị chặn**, với **0 báo nhầm** trên các biến thể hợp lệ. [Trap scorecard](../src/reports/trap_scorecard.json) xác nhận **4/4 tình huống can thiệp bằng chứng bị từ chối** tại kiểm tra integrity.

## 4. Độ ổn định và tính toàn vẹn

Thử nghiệm A/A so sánh swarm trên hai bộ seed `11,22,33,44,55` và `66,77,88,99,110`. [Kết quả](../src/reports/aa_comparison.json) cho thấy Δ=0 ở mọi metric, với khoảng tin cậy của chênh lệch pass rate [0.000, 0.000]. `pass_hat_5` ở cả hai bộ là 0.8929, cao hơn sàn 0.85 một khoảng 0.0429.

Quan sát này cho thấy sàn đã chọn không gây báo nhầm trong cặp thử nghiệm hiện tại. Một cặp seed set chưa đủ ước lượng đầy đủ phân phối nhiễu hoặc bảo đảm khả năng phát hiện lỗi hiếm.

Integrity kiểm tra giá trị NaN, inf, None, lỗi evaluator, độ đầy đủ và tính duy nhất của cặp item–seed, sự khớp nhau giữa điểm tổng hợp và từng dòng, cùng tính nhất quán của slice. Cơ chế ratchet phát hiện việc nới ngưỡng hoặc bỏ điều kiện chặn trên cùng phiên bản eval set. Cấu hình CI sử dụng base spec từ base commit của PR; baseline được đối chiếu với replay swarm mới.

## 5. Judge và phân tích trace

Judge tone đạt κ=0.757, precision=0.857, recall=0.800, đáp ứng ngưỡng calibration trên replay. Judge helpful có κ=0.375, precision=1.000, recall=0.300 và bị loại do κ và recall thấp.

Rogan–Gladen hiệu chỉnh tỷ lệ lỗi quan sát thành 0.30 ở cả hai CSV. Giá trị này là ước lượng tỷ lệ lỗi trong điều kiện calibration, không thay thế nhãn từng case. [Judge audit](judge_audit.md) phân tích bảy bất đồng dựa trên nhãn người có sẵn và có Codex hỗ trợ đối chiếu.

[Trace case](trace_case.md) xác định bước sai đầu tiên của `C-002@11` là event thứ 3, `model_override`: số ngày trễ trong DB bị thay từ 2 thành 5 theo ticket. Regression test xác nhận biến thể lỗi hoàn sai 20.000 VND, trong khi `fixed` từ chối đúng và không ghi refund.

## 6. Nguồn dữ liệu và giới hạn kết luận

Nguồn Day08 tại commit `034c6c421c198dae67a9211d15e2587d5a378972` được giữ nguyên; [checksum](../src/reports/source_verification.json) xác nhận 33 file được bảo vệ không thay đổi. Bộ mã nguồn và mẫu báo cáo hiện tại được nhận diện bằng fingerprint `94b9da74596fe81d`, với thông tin package trong [implementation manifest](../src/reports/implementation_manifest.json). Môi trường đã kiểm chứng gồm pydantic-evals 2.68.0, numpy 2.5.5, scipy 1.18.1, pytest 8.4.2, PyYAML 6.0.3.

Bộ public đã được sử dụng trong phát triển nên không phải tập held-out. Quy mô 14 hoặc 28 item với năm seed chưa bảo đảm phát hiện ổn định lỗi chỉ xuất hiện ở một phần seed. MockLLM và judge replay cũng chưa phản ánh hành vi của model hoặc người dùng thật.

Các kiểm tra integrity phát hiện được nhiều hình thức làm sai lệch report, nhưng không xác thực nguồn gốc thực thi nếu toàn bộ bằng chứng bị giả mạo đồng thời. Kết quả hiện tại chưa bao gồm hidden grading, latency production hoặc pilot khách hàng. Trạng thái hoàn thiện và bàn giao được ghi nhận trong [báo cáo tổng hợp](../SUBMISSION.md).
