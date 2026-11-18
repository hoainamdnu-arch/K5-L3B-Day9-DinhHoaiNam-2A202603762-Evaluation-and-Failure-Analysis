# Judge audit — Kết quả calibration và phân tích bất đồng

## 1. Phạm vi và phương pháp

Báo cáo sử dụng hai CSV public để đối chiếu phán quyết judge với nhãn người trong điều kiện replay. Mỗi tiêu chí có 100 mẫu; **FAIL là lớp dương**, vì nhiệm vụ của judge là phát hiện lỗi. Ngưỡng calibration gồm Cohen’s κ ≥ 0.6, precision ≥ 0.8 và recall ≥ 0.7.

Số liệu được lưu trong [judge_calibration.json](../src/reports/judge_calibration.json). Các phán quyết này là dữ liệu replay, chưa phải kết quả chạy judge mới trên tập độc lập.

## 2. Kết quả calibration

| Tiêu chí | n | Cohen’s κ | Precision | Recall | TP / FP / FN / TN | Kết luận |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | 24 / 4 / 6 / 66 | Đạt calibration trong phạm vi replay |
| helpful | 100 | 0.375 | 1.000 | 0.300 | 9 / 0 / 21 / 70 | Loại do κ và recall thấp |

Judge tone đạt cả ba ngưỡng, nhưng vẫn bỏ lọt sáu lỗi và báo nhầm bốn mẫu. Judge helpful không tạo false positive trong tập này, song bỏ lọt 21 lỗi; precision cao không bù được recall thấp.

Với tone, tỷ lệ lỗi quan sát là 0.28, sensitivity 0.8 và specificity 66/70. Với helpful, các giá trị tương ứng là 0.09, 0.3 và 1. Rogan–Gladen hiệu chỉnh tỷ lệ lỗi thành 0.30 cho cả hai tiêu chí. Đây là ước lượng prevalence trong điều kiện calibration, không phải phép sửa nhãn cho từng mẫu.

## 3. Phân tích bảy bất đồng

Các nhận xét dưới đây do Codex đối chiếu reply với nhãn người và chú thích đã có trong CSV. Chúng không đại diện cho bảy nhãn người mới.

| Case | Judge / human | Nhận định |
| --- | --- | --- |
| H-008 | PASS / FAIL | Các cách nói “em”, “nha”, “anh check” bị rubric tone xem là quá suồng sã. Judge đã đồng nhất sự thân thiện với cách xưng hô phù hợp. |
| H-017 | PASS / FAIL | “bạn”, “rồi nha” bị nhãn người đánh giá không phù hợp ngữ cảnh. Riêng reply không đủ dữ kiện để xác định tuổi khách; kết luận dựa trên nhãn và chú thích có sẵn. |
| H-029 | PASS / FAIL | Cụm “không cần nhắn thêm” mang tính ra lệnh. Các từ lịch sự ở đầu câu đã che khuất mệnh đề gây khó chịu trong phán quyết của judge. |
| H-042 | FAIL / PASS | Reply ngắn vẫn cung cấp số tiền và thời gian nhận tiền. Việc thiếu lời xin lỗi đã bị đánh giá quá mức trong tình huống đã xử lý xong. |
| H-051 | FAIL / PASS | Thuật ngữ “refund” được rubric CS cho phép. Judge đã phạt cách dùng thuật ngữ thay vì tập trung vào mức độ lịch sự. |
| HL-015 | PASS / FAIL | Reply nói hoàn 55.000 VND trong khi chú thích ledger ghi 40.000 VND. Phán quyết helpful đã bỏ qua sai lệch tiền tệ. |
| HL-016 | PASS / FAIL | Reply có nhiều lời xin lỗi nhưng nói hoàn 55.000 VND, trong khi ledger ghi 35.000 VND. Mức độ trôi chảy đã che sai số tiền. |

Các bất đồng cho thấy rubric tone cần phân biệt cách xưng hô, giọng ra lệnh và thuật ngữ nghiệp vụ. Đối với helpful, vấn đề chính là phán quyết ngôn ngữ không kiểm chứng được tính đúng của tiền đã hoàn. Chưa có phép đo sau khi sửa rubric để kết luận các điều chỉnh sẽ cải thiện κ.

## 4. Kết luận sử dụng

Judge tone đủ điều kiện calibration trên replay hiện tại, nhưng chưa được tích hợp để chấm toàn bộ trial của release gate. Judge helpful bị loại khỏi vai trò đánh giá chất lượng trong phạm vi kết quả này.

Tiền, approval, ledger và full quote được chấm bằng code. [FM-08](failure_taxonomy.md) được kiểm tra bằng `ReplyAmountCorrect`, đối chiếu trực tiếp số tiền trong reply với ledger. Kết luận về judge vẫn giới hạn ở dữ liệu public, chưa có tập held-out hoặc phép đo với người dùng thật.
