# Day09 — Evaluation & Failure Analysis cho LogiX-VN

Bài thực hành của **Đinh Hoài Nam — 2A202603762, K5 L3B** xây dựng hệ thống đánh giá chất lượng agent xử lý claim hoàn tiền. Phạm vi đã hoàn thành gồm Core, Advanced và Expert, với kết quả được kiểm chứng local trên dữ liệu public.

## 1. Tóm tắt kết quả

| Hạng mục | Kết quả ghi nhận |
| --- | --- |
| Kiểm thử tự động | 124 kiểm thử đạt, gồm 57 kiểm thử host và 67 kiểm thử Day09 |
| Eval set v1 | 14 item × 5 seed; kiểm tra dữ liệu có 0 lỗi |
| Eval set v2 | 28 item × 5 seed; kiểm tra dữ liệu có 0 lỗi |
| Mutation gate | Chặn đúng 3/3 biến thể hồi quy; chấp nhận hai biến thể hợp lệ, không báo nhầm |
| Integrity traps | Chặn 4/4 tình huống can thiệp report hoặc metric spec |
| Thử nghiệm A/A | Δ=0 ở mọi metric trên hai bộ seed đã khảo sát |
| Nguồn Day08 | 33 file được bảo vệ giữ nguyên theo checksum |

Gate local chấp nhận `fixed` và `honest_refactor`, đồng thời chặn `seeded_regression`, `slice_regression` và `flaky_regression`. Kết luận này phản ánh chất lượng trên bộ kiểm tra hiện tại; chưa tương đương với PR đã được merge hoặc phê duyệt triển khai sản phẩm.

## 2. Cơ sở đánh giá

Hệ thống sử dụng MockLLM và SQLite riêng cho từng trial. Tiền, approval, ledger và full quote được chấm bằng code. Các phép kiểm ở mức trace giúp xác định cơ chế lỗi, trong khi paired bootstrap và slice gate đánh giá mức suy giảm chất lượng giữa các biến thể.

Eval set v1 sử dụng 14 case public của Day08. Phiên bản v2 bổ sung 14 case adversarial, lưu nhãn tách khỏi item và gắn mã failure mode. Nguồn Day08 tại commit `034c6c4` được đối chiếu qua [source manifest](artifacts/day8_source_manifest.json) và [kết quả checksum](src/reports/source_verification.json).

Judge tone đạt ngưỡng calibration trên replay với κ=0.757, precision=0.857 và recall=0.800. Judge helpful bị loại do κ=0.375 và recall=0.300. Các nhận xét ngôn ngữ không được dùng để thay thế phép kiểm tiền hoặc approval.

## 3. Hồ sơ báo cáo

| Tài liệu | Nội dung |
| --- | --- |
| [Báo cáo tổng hợp](SUBMISSION.md) | Kết quả, nhận định và trạng thái cuối cùng |
| [Thông tin học viên](STUDENT.md) | Tác giả, phạm vi công việc và công cụ hỗ trợ |
| [Eval card](docs/eval_card.md) | Metric, baseline, khoảng tin cậy, A/A và giới hạn kết luận |
| [PRD v1.1](docs/PRD_v1.1.md) | Tiêu chí chất lượng, phạm vi sản phẩm và cổng release |
| [Failure taxonomy](docs/failure_taxonomy.md) | Phân loại lỗi và bằng chứng trace |
| [Judge audit](docs/judge_audit.md) | Calibration và phân tích bảy bất đồng |
| [Trace case](docs/trace_case.md) | Bước sai đầu tiên của C-002@11 và regression test đối chứng |
| [Báo cáo thay đổi](docs/PR_DESCRIPTION.md) | Kết quả Core, mutation và integrity phục vụ đánh giá thay đổi |
| [Danh mục bằng chứng](src/reports/README.md) | Các report JSON và phạm vi sử dụng |

## 4. Khả năng tái lập

Kết quả đã được kiểm chứng trên Windows với Python 3.13. Môi trường package được lưu trong [requirements lock](src/requirements-lock-win-py313.txt); mã nguồn, cấu hình và mẫu báo cáo được nhận diện bằng [implementation manifest](src/reports/implementation_manifest.json).

Module `python -m lab9.reproduce`, thực thi trong thư mục `src/` với môi trường đã cài dependency, tái tạo eval set, report và scorecard từ các trial thực tế. Module `python -m lab9.reporting` tổng hợp tài liệu từ report đã có. Các lệnh này phục vụ kiểm chứng kết quả; evaluation không cần API key hoặc model trực tuyến.

## 5. Giới hạn và trạng thái ghi nhận

Bộ public đã được sử dụng khi phát triển, nên không phải tập held-out. Quy mô 14 hoặc 28 item với năm seed chưa bảo đảm phát hiện mọi lỗi hiếm. MockLLM, judge replay và một cặp A/A cũng chưa phản ánh đầy đủ hành vi production.

Phần triển khai và kiểm chứng local đã hoàn tất. Cấu hình CI cho Core và v2 đã được bổ sung, nhưng chưa có kết quả GitHub Actions từ xa hoặc hidden grading. Tại thời điểm ghi nhận 18/11/2026, các thay đổi chưa được commit/push; PR, merge và nộp LMS chưa được thực hiện trong phiên làm việc này.
