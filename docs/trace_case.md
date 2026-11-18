# Trace case — Bước sai đầu tiên của claim C-002@11

## 1. Case và triệu chứng

Case được phân tích là `seeded_regression C-002@11`, thuộc eval run **`E-seeded_regression-20261118-20d5`** và trace `R-seeded_regression-C-002-s11`. Order trong DB trễ 2 ngày, trong khi ticket khai trễ 5 ngày.

Nhãn đúng là `denied`, proposal 0 và không ghi refund. Biến thể lỗi trả `resolved` và ghi 20.000 VND vào ledger. Sai lệch được phát hiện bởi `TrialPass`, `RefundAmountCorrect`, `ProposalCorrect` và `DbFactKept`.

## 2. Diễn biến dẫn đến lỗi

| Bước | Event | Dữ kiện ghi nhận | Nhận định |
| --- | --- | --- | --- |
| 1 | handoff | Gói chuyển giao chỉ cấp các tool đọc. | Chưa có bằng chứng quyết định sai. |
| 2 | investigator | Order view trả `delay_days=2` từ DB. | Nguồn dữ kiện chính xác đã có. |
| 3 | model_override | Payload `{"delay_days": 5}` thay dữ kiện DB bằng con số trong ticket. | Đây là bước sai đầu tiên. |

Lỗi được xác định tại bước 3 vì dữ liệu ở hai bước trước vẫn đúng. Việc ghi tiền sai là hệ quả của quyết định tin ticket hơn DB, thuộc **FM-03 — ticket_trust**. Approval của case vẫn hợp lệ, nên đây không phải trường hợp bypass approval.

## 3. Đối chứng với fixed

| Tiêu chí | Seeded regression | Fixed |
| --- | --- | --- |
| Nguồn số ngày trễ | Ticket: 5 ngày | DB: 2 ngày |
| Event model_override | Có | Không |
| Trạng thái | resolved | denied |
| Proposal | 20.000 VND | 0 VND |
| Ledger refund | 20.000 VND | 0 VND |
| Kết luận Lab08 | Không đạt | Đạt |

Hai biến thể dùng cùng claim, world và seed. Reply của biến thể lỗi nói đúng số tiền đã ghi sai vào ledger, nên riêng `ReplyAmountCorrect` vẫn đạt. Điều này cho thấy kiểm tính nhất quán của reply không thay thế được phép kiểm entitlement hoặc dữ kiện DB.

## 4. Bằng chứng hồi quy

Regression test `test_lab9_first_wrong_step_regression_for_overstated_delay` trong [test_lab9_regressions.py](../src/tests/test_lab9_regressions.py) đã vượt qua. Test kiểm event thứ 3, ledger 20.000 VND ở biến thể lỗi và ledger 0 ở `fixed`, đồng thời xác nhận kết luận Lab08 tương ứng không đạt/đạt.

[Trace evidence](../src/reports/trace_evidence.json) lưu đoạn bằng chứng an toàn của cùng cơ chế lỗi tại `probe_fm03`. Ở cấp toàn bộ eval set, [gate v1](../src/reports/gate_v1.json) ghi nhận `seeded_regression` có Δ pass rate −0.271 và CI 95% [−0.500, −0.057], dẫn đến kết luận chặn.

## 5. Giới hạn phân tích

Trace và bug switch xác nhận đường đi của dữ kiện trong simulation, không cho biết quá trình suy luận nội bộ của model thật hoặc tần suất lỗi production. Case này cung cấp bằng chứng cho một cơ chế lỗi cụ thể và một regression test đối chứng.
