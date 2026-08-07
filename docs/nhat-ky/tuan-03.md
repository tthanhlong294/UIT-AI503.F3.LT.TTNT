# Tuần 3 — 29/07 đến 04/08/2026

**Phase**: 0 — Khởi tạo & Môi trường

---

## Mục tiêu tuần

Viết phần khảo sát của Chương 1 và chạy thử trọn một vòng quy trình 5 nhịp với mã việc đầu tiên.

## Đã thực hiện

### 1. Chương 1 — Tổng quan (04/08)

Hoàn thành ba mục viết được ở thời điểm hiện tại (`a547941` — 697 dòng):

- **§1.1 Bối cảnh** — nhu cầu xác thực sinh trắc học trong nhà thông minh; hạn chế kỹ thuật và pháp lý
  của mô hình xử lý trên đám mây theo Nghị định 13/2023/NĐ-CP; trí tuệ nhân tạo biên; đánh giá năng lực
  Raspberry Pi 5 kèm giới hạn (không có bộ xử lý thần kinh chuyên dụng, cần tản nhiệt chủ động).
- **§1.2 Khảo sát công trình liên quan** — phân tích sâu **4 công trình: 2 quốc tế + 2 trong nước**,
  kèm **Bảng 1.1** đối chiếu phạm vi.
- **§1.3 Xác định vấn đề** — ba khoảng trống rút ra từ bảng khảo sát.

§1.4 (Đóng góp) và §1.5 (Cấu trúc báo cáo) để lại cho Phase 8 vì phụ thuộc kết quả thực nghiệm.

**Ba khoảng trống xác định được từ khảo sát:**

1. Chưa có cơ sở đối chiếu định lượng giữa các phương án thuật toán trên cùng điều kiện đo. Riêng khâu
   phát hiện, cả bốn công trình đều dùng phương pháp xếp tầng hoặc đa giai đoạn; **không công trình nào
   dùng mô hình phát hiện một giai đoạn** hướng thời gian thực.
2. **Không công trình nào tích hợp cơ chế phát hiện giả mạo.**
3. **Không công trình nào báo cáo tỉ lệ chấp nhận sai** — cả bốn chỉ đánh giá theo bài toán tập đóng.

Một quan sát phụ có giá trị phòng thủ: các công trình đã công bố trên thiết bị nhúng cũng đánh giá ở
quy mô nhỏ (7 và 10 danh tính), giúp đặt đúng ngữ cảnh cho hạn chế gallery 2–3 người của nghiên cứu này.

### 2. Mã việc `P0-01-nen-tang` — vòng 5 nhịp đầu tiên (04/08)

Module nền tảng `src/common/`: `types.py`, `exceptions.py`, `config.py`, `logging.py` cùng bộ kiểm thử
(`2835cb7` — 9 file, 944 dòng).

| Nhịp | Kết quả |
|---|---|
| N1 Đặc tả | `docs/dac-ta/P0-01-nen-tang.md` — 8 file danh sách trắng, 3 bảng ca biên |
| N2 Sinh mã | Đủ 8 file, không chạm file ngoài phạm vi |
| N3 Review vòng 1 | 🔴 TRẢ LẠI — 0 lỗi chặn, **1 lỗi cần sửa** |
| N4 Sửa | Sửa đúng phạm vi, chỉ đụng file kiểm thử |
| N5 Review vòng 2 | ✅ **ĐẠT** |

**Kết quả kiểm máy**: `black` sạch · `ruff` sạch · `pytest` **26 ca xanh** (đặc tả yêu cầu ≥ 18).

**Lỗi phát hiện được**: bộ kiểm thử dùng điều kiện lỏng `>= 1` trong khi đặc tả yêu cầu **đúng 1**
bộ ghi log ra luồng chuẩn. Hậu quả nếu bỏ qua: khi chuyển sang ghi log ra tệp, toàn bộ 26 ca kiểm thử
vẫn báo xanh trong khi hệ thống mất log console lúc chạy trên thiết bị từ xa. Kiểm chứng bổ sung cho
thấy lớp ghi log ra tệp kế thừa từ lớp ghi ra luồng, nên phép kiểm kiểu dữ liệu đơn thuần không phân
biệt được — điều kiện siết lại bắt được 4/4 trường hợp cài đặt sai trong phép thử đột biến.

**Cải tiến quy trình rút ra**: nguyên nhân gốc là một ô trong bảng ca biên gộp ba điều kiện. Khung đặc
tả được bổ sung cột **"Assert tối thiểu"** ghi thẳng biểu thức kiểm, và đổi tiêu chí nghiệm thu từ
"tối thiểu N ca kiểm thử" sang "mỗi dòng bảng ca biên có ít nhất một ca kiểm thử" (`5235f3d`).

## Số liệu

| Hạng mục | Giá trị | Nguồn |
|---|---|---|
| Ca kiểm thử `src/common/` | 26 passed | `pytest -q` |
| Số vòng review tới khi ĐẠT | 1 | `docs/review/P0-01-nen-tang.review.md` |
| Lỗi mức chặn | 0 | như trên |

Chưa có số liệu hiệu năng — chưa có phần cứng.

## Vướng mắc

- **Chưa có Raspberry Pi 5.** Bốn trong sáu chỉ tiêu cam kết chỉ đo được trên phần cứng thật.
- Chưa cài Docker nên chưa dựng được môi trường giả lập ARM64.

## Kế hoạch tuần sau

- Mã việc `P0-02` (khai báo phụ thuộc) và `P0-03` (môi trường giả lập ARM64)
- Hoàn tất Cổng D của Phase 0

---

*Nguồn: lịch sử git từ `a547941` đến `d691785`; biên bản `docs/review/P0-01-nen-tang.review.md`.*
