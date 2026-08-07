# Nhật ký điều chỉnh phạm vi & mục tiêu

Ghi lại **mọi sai khác giữa đề cương gốc** (`docs/DE-CUONG-CHI-TIET.md`, `DC DATN ....pdf`)
**và những gì thực sự được triển khai**, kèm lý do.

Đến Phase 8, bảng ở đây được chuyển thẳng thành một mục trong **Chương 1 §Phạm vi** và
**Chương 5 §Hạn chế** — đáp ứng dòng checklist *"Đã nêu điều chỉnh phạm vi so với đề cương gốc
và lý do"* (`CLAUDE.md` §7). Không có file này thì đến lúc viết báo cáo sẽ không ai nhớ vì sao đã đổi.

---

## Ai ghi mục nào

| Bảng | Người ghi | Khi nào |
|---|---|---|
| **A — Điều chỉnh triển khai** | Claude tự ghi, **không cần hỏi trước** | Ngay khi phát sinh |
| **B — Thay đổi mục tiêu / chỉ tiêu** | **Sinh viên ghi**, sau khi đã trao đổi với GVHD | Sau khi có ý kiến GVHD |

Claude **không tự thêm dòng nào vào bảng B**. Nếu Claude thấy một chỉ tiêu có vấn đề,
việc của Claude là nêu vấn đề kèm số liệu, không phải sửa chỉ tiêu.

---

## A. Điều chỉnh triển khai

Thay đổi về cách làm, quy mô dữ liệu, công cụ, cấu trúc báo cáo — **không đụng tới 5 chỉ tiêu cam kết**.

| Ngày | Nội dung đề cương gốc | Thực tế triển khai | Lý do | Bằng chứng |
|---|---|---|---|---|
| ≤ 25/07/2026 | Gallery **5–7 người** đăng ký | Gallery **2–3 người** (sinh viên + gia đình) | Định vị lại đề tài là ứng dụng cá nhân trong một hộ gia đình; hạn chế tối đa việc thu thập dữ liệu sinh trắc học của người ngoài (R28) | `CLAUDE.md` §1 |
| ≤ 25/07/2026 | Không nêu tập impostor | Bổ sung **ba tập impostor**: LFW gốc, LFW domain-adapted, in-domain 5–7 người có đồng ý | Gallery 2–3 người không thể trích một phần làm "người lạ" → không có tập impostor thì **không đo được FAR** | `CLAUDE.md` §1, `.claude/instructions/experiment-protocol.instructions.md` §3.3 |
| ≤ 25/07/2026 | Số ảnh mỗi người ~50 | **≥ 100 ảnh/người** | Bù đắp cho việc giảm số danh tính trong gallery | `CLAUDE.md` §1 |
| 25/07/2026 | Không nêu quy trình phát triển | Quy trình **5 nhịp** Claude ↔ Gemini, đặc tả và biên bản review lưu trong `docs/` | Phân vai để mọi dòng code đều qua kiểm định; đồng thời tạo bằng chứng quy trình cho phụ lục báo cáo | `CLAUDE.md` §2.9, PR #1 |
| 02/08/2026 | Không nêu số lượng công trình khảo sát | §1.2 phân tích sâu **4 công trình: 2 nước ngoài + 2 trong nước** (bài báo hoặc đồ án/luận văn) | Yêu cầu về thành phần tài liệu khảo sát; ít công trình hơn nhưng mỗi công trình được phân tích kỹ 0,5–0,7 trang thay vì điểm lướt | `report/chapters/ch1-tong-quan.md` §1.2 |
| 07/08/2026 | Phase 0 gồm 6 bước, hoàn tất trong tuần 1 | **Bước 0.4 (cài Raspberry Pi OS, bật camera) hoãn sang khi có phần cứng.** Phase 0 đóng với 5/6 bước, gắn thẻ `phase-0-done` | Chưa mua được Raspberry Pi 5. Theo R36, làm hết phần không phụ thuộc phần cứng rồi ghi rõ phần còn lại. Giữ Phase 0 mở sẽ chặn toàn bộ tiến độ phía sau trong khi phần lớn Phase 1 và Phase 2 không cần thiết bị | `docs/nhat-ky/tuan-04.md`, thẻ `phase-0-done` |
| 07/08/2026 | Đề cương nêu MiniFASNet, không nói rõ cấu hình | **Dùng một mô hình MiniFASNetV2** thay vì tổ hợp hai mô hình như kho nguồn | Ngân sách tốc độ xử lý là chỉ tiêu cam kết; tổ hợp làm chi phí khối chống giả mạo tăng gấp đôi. Hệ quả: kết quả không đối chiếu trực tiếp được với số liệu công bố của nhóm tác giả — phải nêu rõ ở Chương 4 | `models/README.md` §3.4 |

## B. Thay đổi mục tiêu / chỉ tiêu cam kết

Năm chỉ tiêu ở `CLAUDE.md` §1 (≥ 95 % độ chính xác · ≥ 5 FPS pipeline · ≥ 10 FPS detect ·
< 2 s độ trễ · ≥ 90 % phát hiện giả mạo) **chỉ đổi qua bảng này**, sau khi có ý kiến GVHD.

| Ngày | Chỉ tiêu | Cũ | Mới | Lý do | GVHD đã duyệt |
|---|---|---|---|---|---|
| *(chưa có)* | | | | | |

### Lý do hợp lệ và không hợp lệ

| ✅ Hợp lệ | ❌ Không hợp lệ |
|---|---|
| GVHD yêu cầu đổi trọng tâm đề tài | **"Đo ra 91 % nên hạ chỉ tiêu xuống 90 %"** |
| Phát hiện chỉ tiêu ban đầu đặt sai đơn vị hoặc sai định nghĩa | Muốn bảng đối chiếu ở Chương 5 toàn dấu ✅ |
| Phần cứng thay đổi (Pi 5 → thiết bị khác) | Sắp hết thời gian |
| Bổ sung chỉ tiêu **chặt hơn** (ví dụ thêm `FAR_adapt` ≤ 1 %) | |

**Kết quả đo không đạt thì báo cáo trung thực kèm phân tích nguyên nhân** (R7), không hạ ngưỡng.
Hội đồng đọc được đề cương gốc; một chỉ tiêu bị sửa xuống đúng bằng con số đo được là thứ lộ ngay,
và gây thiệt hại lớn hơn nhiều so với việc thừa nhận một chỉ tiêu chưa đạt.

---

## Cách dùng ở Phase 8

1. **Chương 1 §Phạm vi** — tóm tắt bảng A thành 1–2 đoạn: đề tài đã thu hẹp/mở rộng ở đâu, vì sao.
2. **Chương 4 §4.2** — nêu điều chỉnh về dữ liệu (gallery, impostor) ngay khi mô tả cơ sở dữ liệu.
3. **Chương 5 §Hạn chế** — những gì bảng A cho thấy là **giới hạn của kết quả**, đặc biệt hệ quả
   của gallery nhỏ: accuracy không khái quát hoá được cho hệ thống nhiều người dùng.
4. Bảng B, nếu có dòng nào, phải được nêu **rõ ràng ở cả Chương 1 lẫn Chương 5** kèm ý kiến GVHD.
