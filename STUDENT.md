# Thông tin học viên — Day09

## 1. Tác giả

| Thông tin | Giá trị |
| --- | --- |
| Họ tên | Đinh Hoài Nam |
| MSSV | 2A202603762 |
| Lớp | K5 L3B |
| GitHub | hoainamdnu-arch |
| Bài thực hành | Evaluation & Failure Analysis cho LogiX-VN |

Repository bài làm là [K5-L3B-Day9-DinhHoaiNam-2A202603762-Evaluation-and-Failure-Analysis](https://github.com/hoainamdnu-arch/K5-L3B-Day9-DinhHoaiNam-2A202603762-Evaluation-and-Failure-Analysis).

## 2. Phạm vi công việc

Bài làm bao gồm Core M0–M4, Advanced M5–M6 và Expert M7. Phần triển khai tập trung vào thống kê calibration, code graders, eval set có taxonomy, paired bootstrap, slice gate và cơ chế integrity/ratchet.

Nguồn Day08 được lấy từ commit gốc `034c6c421c198dae67a9211d15e2587d5a378972`. Kết quả checksum xác nhận 33 file được bảo vệ giữ nguyên. Phần đánh giá sử dụng swarm tham chiếu để duy trì cơ sở so sánh thống nhất.

## 3. Kết quả và đóng góp

Hồ sơ ghi nhận 124 kiểm thử tự động đạt yêu cầu. Gate chặn đúng ba biến thể hồi quy, không báo nhầm hai biến thể hợp lệ và từ chối cả bốn tình huống can thiệp bằng chứng. Hai eval set được gắn failure mode, có nhãn tách riêng và vượt qua kiểm tra dữ liệu.

Các kết quả được trình bày trong [báo cáo tổng hợp](SUBMISSION.md), [eval card](docs/eval_card.md), [failure taxonomy](docs/failure_taxonomy.md), [judge audit](docs/judge_audit.md) và [PRD v1.1](docs/PRD_v1.1.md). Trạng thái triển khai và bàn giao được ghi nhận thống nhất trong báo cáo tổng hợp.

## 4. Công cụ hỗ trợ và cơ sở xác nhận

Codex được sử dụng để đọc yêu cầu, hỗ trợ viết mã và kiểm thử, thực thi evaluation và biên tập báo cáo. Số liệu được lấy từ các lần chạy có report JSON và run ID; nội dung phân tích được đối chiếu với trace, ledger và metric spec.

Audit judge sử dụng nhãn người đã có trong CSV public, có Codex hỗ trợ phân tích bất đồng. Hồ sơ không bao gồm nhãn người mới, hidden grading hoặc kết quả từ người dùng thật.
