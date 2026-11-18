# Danh mục bằng chứng đánh giá Day09

## 1. Phạm vi dữ liệu

Các artifact trong thư mục này ghi nhận kết quả Core, Advanced và Expert trên dữ liệu public của LogiX-VN. Report được sinh từ các trial MockLLM/SQLite, với nhãn ở file riêng và các lần chạy có run ID.

Eval set v1 gồm 14 item × 5 seed; v2 gồm 28 item × 5 seed. Các kết quả tổng hợp được trình bày trong [eval card](../../docs/eval_card.md) và [báo cáo tổng hợp](../../SUBMISSION.md).

## 2. Danh mục report

| Artifact | Nội dung bằng chứng |
| --- | --- |
| [baseline_v1.json](baseline_v1.json), [eval_fixed.json](eval_fixed.json), [eval_seeded_regression.json](eval_seeded_regression.json) | Kết quả Core trên 70 trial cho mỗi biến thể |
| [baseline_v2.json](baseline_v2.json) và các file `eval_*_v2.json` | Kết quả v2 trên 140 trial cho mỗi biến thể |
| [gate_v1.json](gate_v1.json) | Quyết định gate Core và khoảng tin cậy paired bootstrap |
| [judge_calibration.json](judge_calibration.json) | Calibration của hai judge replay và các mẫu bất đồng |
| [grader_detection.json](grader_detection.json) | Tỷ lệ giải thích trial lỗi và báo nhầm trên các biến thể public |
| [mutation_scorecard.json](mutation_scorecard.json) | Quyết định gate cho năm biến thể public |
| [aa_alternate_v2.json](aa_alternate_v2.json), [aa_comparison.json](aa_comparison.json) | Replay với bộ seed thay thế và chênh lệch metric trong A/A |
| [trap_scorecard.json](trap_scorecard.json), `traps/` | Bốn tình huống can thiệp report/spec và lý do từ chối |
| [trace_evidence.json](trace_evidence.json) | Tám lỗi được gài và một trường hợp kiểm soát principal bị chặn đúng |
| [source_verification.json](source_verification.json) | Commit nguồn Day08 và kết quả checksum 33 file được bảo vệ |
| [implementation_manifest.json](implementation_manifest.json) | Fingerprint mã nguồn, cấu hình, kiểm thử, mẫu báo cáo và phiên bản package |

## 3. Nhận định kết quả

Gate chặn đúng ba biến thể hồi quy, không báo nhầm hai biến thể hợp lệ và từ chối bốn integrity trap. A/A ghi nhận Δ=0 ở mọi metric trên hai bộ seed đã khảo sát. Bộ grader bổ sung giải thích được 100% trial lỗi của `seeded_regression`, với tỷ lệ báo nhầm 0% trên `fixed`.

Các file trong `traps/` là đầu vào giả lập đã bị làm sai lệch để kiểm tra gate; một số có giá trị thiếu hoặc NaN theo thiết kế. Chúng được lưu làm bằng chứng của phép thử từ chối, khác với các baseline hợp lệ.

Payload chứa secret trong probe FM-01 đã được che khỏi `trace_evidence.json`. Raw trace, SQLite, venv và log runtime được loại khỏi tập artifact bàn giao.

## 4. Nguồn gốc và giới hạn

Report và scorecard do chương trình sinh; bảng và tài liệu phân tích được tổng hợp từ các JSON này. Run ID được xác định theo shape, ngày và eval-set SHA; implementation manifest cung cấp fingerprint bổ sung cho bộ mã nguồn và mẫu báo cáo hiện tại.

Kết quả chỉ phản ánh simulation public. Chưa có hidden grading, CI từ xa hoặc đánh giá production trong lần ghi nhận này.
