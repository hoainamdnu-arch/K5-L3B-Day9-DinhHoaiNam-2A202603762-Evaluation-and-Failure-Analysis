# Báo cáo kết quả Day09 — Evaluation & Failure Analysis

**Học viên:** Đinh Hoài Nam · **MSSV:** 2A202603762 · **Lớp:** K5 L3B

**Thời điểm ghi nhận:** 18/11/2026.

## 1. Tóm tắt kết quả

Bài thực hành đã hoàn thành các hạng mục Core, Advanced và Expert trong phạm vi kiểm chứng local trên dữ liệu public của LogiX-VN. Hệ thống đánh giá phân biệt được các biến thể hoạt động đúng với các biến thể gây hồi quy, đồng thời phát hiện những trường hợp làm sai lệch bằng chứng đánh giá.

Tổng cộng **124 kiểm thử tự động đã vượt qua**, gồm 57 kiểm thử host và 67 kiểm thử Day09. Mutation gate chặn đúng **3/3 biến thể hồi quy**, chấp nhận cả hai biến thể hợp lệ và không ghi nhận báo nhầm. Cơ chế kiểm tra tính toàn vẹn từ chối **4/4 tình huống can thiệp vào report hoặc metric spec**.

## 2. Phạm vi và cơ sở đánh giá

Eval set v1 gồm **14 item × 5 seed**, tương ứng 70 trial cho mỗi biến thể. Eval set v2 mở rộng thành **28 item × 5 seed**, tương ứng 140 trial, với 14 item adversarial bổ sung. Cả hai bộ dữ liệu đều được gắn `failure_modes`, lưu nhãn tách khỏi item và vượt qua kiểm tra tính hợp lệ với **0 lỗi**.

Các lần đánh giá sử dụng MockLLM, cùng bộ seed `11,22,33,44,55` và SQLite riêng cho từng trial. Paired bootstrap được tính trên điểm trung bình theo item qua các seed, với khoảng tin cậy 95%, 1.000 lần lấy mẫu và `rng=2027`.

Nguồn Day08 được giữ nguyên tại commit `034c6c4`. Kết quả đối chiếu checksum xác nhận **33 file được bảo vệ không thay đổi**, bao gồm mã host, dữ liệu và cấu hình gốc. Bằng chứng được lưu trong [source verification](src/reports/source_verification.json).

## 3. Kết quả đánh giá các biến thể

### Core — eval set v1

Baseline được ghi nhận tại run **`E-swarm-20261118-20d5`**. Kết quả trong [gate v1](src/reports/gate_v1.json) cho thấy:

| Biến thể | Pass rate | Kết luận của gate local |
| --- | ---: | --- |
| `swarm` — baseline | 0.9857 | Chấp nhận khi so với chính baseline |
| `fixed` | 1.0000 | Chấp nhận |
| `seeded_regression` | 0.7143 | Chặn |

`seeded_regression` bị chặn tại các metric `pass_rate`, `refund_amount_correct`, `reply_amount_correct` và `proposal_correct`. Chênh lệch pass rate so với baseline là −0.271, với khoảng tin cậy [−0.500, −0.057], cho thấy mức giảm có ý nghĩa thống kê.

`fixed` đạt pass rate 1.0000, nhưng khoảng tin cậy của mức cải thiện vẫn chứa 0. Kết quả này xác nhận biến thể đáp ứng gate trong bộ kiểm tra hiện tại, chưa đủ để khẳng định chất lượng tổng thể đã cải thiện có ý nghĩa thống kê.

### Advanced và Expert — eval set v2

Baseline v2 có run **`E-swarm-20261118-7205`**, pass rate **0.9786** và `pass_hat_5` **0.8929**. [Mutation scorecard](src/reports/mutation_scorecard.json) ghi nhận:

| Biến thể | Pass rate | Pass^5 | Kết luận của gate local |
| --- | ---: | ---: | --- |
| `fixed` | 1.0000 | 1.0000 | Chấp nhận |
| `honest_refactor` | 1.0000 | 1.0000 | Chấp nhận |
| `seeded_regression` | 0.6429 | 0.6429 | Chặn |
| `slice_regression` | 0.9357 | 0.8929 | Chặn |
| `flaky_regression` | 0.9143 | 0.5714 | Chặn |

`slice_regression` vẫn vượt sàn pass rate tổng thể 0.85, nhưng slice `money_movement` chỉ đạt 0.85, thấp hơn sàn 0.90. Gate phát hiện hồi quy ở slice này; metric kiểm full quote cũng ghi nhận lỗi. Trường hợp này cho thấy điểm trung bình toàn bộ dữ liệu có thể che khuất sai sót trong nhóm nghiệp vụ quan trọng.

`flaky_regression` bị chặn dù không có event `model_override`, trong đó `pass_hat_5=0.5714` thấp hơn sàn 0.85. Ngược lại, `honest_refactor` được chấp nhận dù phát sinh cảnh báo chi phí, vì metric chi phí được dùng để theo dõi và không phải điều kiện chặn.

Phép thử A/A so sánh swarm trên hai bộ seed `11,22,33,44,55` và `66,77,88,99,110` cho **Δ=0 ở mọi metric**; khoảng tin cậy của chênh lệch pass rate là [0, 0]. Hai bộ seed đều có `pass_hat_5=0.8929`, cao hơn sàn 0.85. Kết quả chi tiết nằm trong [A/A comparison](src/reports/aa_comparison.json).

## 4. Chất lượng grader và judge

Bộ grader bổ sung giải thích được **100% trial lỗi của `seeded_regression`**, với **tỷ lệ báo nhầm 0% trên `fixed`** trong phép đo public. `ReplyAmountCorrect` đối chiếu số tiền công bố trong reply với ledger; `ProposalCorrect` kiểm tra full quote, kể cả trường hợp bị từ chối và không phát sinh chuyển tiền.

Kết quả hiệu chuẩn judge từ hai CSV replay được tổng hợp trong [judge audit](docs/judge_audit.md):

| Tiêu chí | Cohen’s κ | Precision | Recall | Nhận định |
| --- | ---: | ---: | ---: | --- |
| `tone_ok` | 0.757 | 0.857 | 0.800 | Đạt ngưỡng hiệu chuẩn trong phạm vi replay |
| `helpful` | 0.375 | 1.000 | 0.300 | Bị loại do κ và recall thấp |

Tiền và approval được đánh giá bằng code. Phần audit định tính đối chiếu bảy bất đồng với nhãn người có sẵn trong CSV, có Codex hỗ trợ phân tích; đây không phải tập nhãn người mới hoặc đánh giá held-out.

## 5. Tính toàn vẹn và tài liệu kết quả

Gate kiểm tra số dòng, tính duy nhất của cặp item–seed, độ khớp giữa điểm tổng hợp và từng dòng, lỗi evaluator, giá trị không hợp lệ và sự nhất quán của slice. Cơ chế ratchet đối chiếu với base spec để phát hiện việc nới ngưỡng hoặc gỡ điều kiện chặn trên cùng phiên bản eval set.

[Trap scorecard](src/reports/trap_scorecard.json) xác nhận gate từ chối cả bốn tình huống: che lỗi evaluator bằng giá trị thiếu hoặc NaN, bỏ dòng thất bại, chọn lọc seed và nới metric spec. Mỗi tình huống đều nhận kết quả `exit 1` tại kiểm tra integrity.

Hồ sơ kết quả gồm [failure taxonomy](docs/failure_taxonomy.md), [trace case kèm regression test](docs/trace_case.md), [judge audit](docs/judge_audit.md), [eval card](docs/eval_card.md) và [PRD v1.1](docs/PRD_v1.1.md). Các report JSON được sinh bằng chương trình; `harness_map.yaml` đã tích hợp phần evaluation ở phiên bản 1.2.

## 6. Giới hạn và trạng thái cuối cùng

Kết quả hiện tại được đo trên dữ liệu public, MockLLM và judge replay. Quy mô 14 hoặc 28 item với 5 seed chưa bảo đảm phát hiện ổn định các lỗi hiếm; một cặp thử nghiệm A/A cũng chưa đủ mô tả đầy đủ phân phối nhiễu. Chưa có bằng chứng từ bộ hidden, người dùng thật hoặc môi trường production.

Phần triển khai và kiểm chứng local đã hoàn tất. Cấu hình CI cho Core và v2 đã được bổ sung, nhưng chưa có kết quả chạy GitHub Actions từ xa. Các thay đổi vẫn chưa được commit/push; việc mở và merge PR, xác nhận nội dung của tác giả và nộp LMS chưa được thực hiện trong lần ghi nhận này.
