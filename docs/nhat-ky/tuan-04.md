# Tuần 4 — 05/08 đến 11/08/2026

**Phase**: 0 — Khởi tạo & Môi trường · **Kết thúc Phase 0** (trừ bước phụ thuộc phần cứng)

---

## Mục tiêu tuần

Hoàn tất khai báo phụ thuộc và môi trường giả lập ARM64 để đóng Phase 0; chuẩn bị trọng số mô hình
và khởi động phần cơ sở lý thuyết của báo cáo.

## Đã thực hiện

### 1. Mã việc `P0-02` — khai báo phụ thuộc

Tách phụ thuộc thành hai tập: `requirements.txt` cho môi trường chạy trên thiết bị đích và
`requirements-dev.txt` cho máy phát triển. Lý do tách: gói `ultralytics` kéo theo `torch` dung lượng
lớn, chỉ cần cho việc chuyển đổi mô hình ở Phase 2 và không bao giờ được nạp trên thiết bị nhúng.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 TRẢ LẠI — 1 lỗi mức chặn |
| Review vòng 2 | ✅ ĐẠT |

**Lỗi phát hiện**: một tệp trung gian 318 dòng chứa danh sách toàn bộ gói của máy phát triển bị để lại
cạnh tệp khai báo phụ thuộc chính. Tệp này liệt kê cả những thư viện học sâu dung lượng lớn, rất dễ bị
hiểu nhầm là danh sách cần cài trên thiết bị đích, phá đúng mục tiêu tách hai tập của mã việc.

**Một lỗi thuộc về bản đặc tả**, không phải bản cài đặt: hai mục của đặc tả đưa ra yêu cầu mâu thuẫn về
thứ tự dòng trong tệp. Đã sửa đặc tả; lỗi biến mất mà tệp không cần thay đổi gì.

### 2. Mã việc `P0-03` — môi trường giả lập ARM64

Dựng container mô phỏng kiến trúc ARM64 trên máy phát triển x86-64, cho phép kiểm chứng tính đúng đắn
của mã nguồn trên kiến trúc đích trước khi có phần cứng thật.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 TRẢ LẠI — 1 lỗi cần sửa |
| Review vòng 2 | ✅ ĐẠT |

**Lỗi phát hiện — đáng chú ý về phương pháp**: tệp cấu hình container thiếu khai báo kiến trúc đích ở
dòng đầu. Toàn bộ 13 phép kiểm của đặc tả đều báo đạt, vì mỗi phép kiểm **tự truyền tham số kiến trúc
vào dòng lệnh**. Khi dựng container không kèm tham số đó, kết quả là ảnh container kiến trúc x86-64
mang tên ARM64 — chạy trơn tru, không có dấu hiệu sai lệch, và mọi số đo hiệu năng lấy từ nó ở các
giai đoạn sau đều sai.

Rút ra quy tắc chung, đã bổ sung vào khung viết đặc tả: **phép kiểm không được tự cung cấp thứ mà mã
nguồn phải tự khai báo**. Với mỗi yêu cầu, phải có ít nhất một phép kiểm chạy ở điều kiện trần.

### 3. Chuẩn bị trọng số mô hình

Tải và kiểm chứng năm tệp trọng số, ghi nhận đầy đủ nguồn, giấy phép, dung lượng và mã băm SHA256 vào
`models/README.md`.

**Ba kết quả kiểm chứng đáng ghi nhận:**

- Mô hình phát hiện khuôn mặt **có đủ 5 điểm mốc**, không phải chỉ khung bao. Nhờ vậy bước căn chỉnh
  khuôn mặt về kích thước chuẩn thực hiện trực tiếp được, không cần bổ sung một mô hình định vị điểm
  mốc riêng — tiết kiệm cả tài nguyên tính toán lẫn khối lượng công việc.
- Mô hình trích xuất đặc trưng cho vectơ **512 chiều**, giữ nguyên trục so sánh với phương án 128 chiều
  đã dự kiến trong đề cương.
- Mô hình chống giả mạo xuất ra **logits chứ không phải xác suất** — hàm chuẩn hoá xác suất nằm ở lớp
  bọc ngoài mô hình trong mã nguồn gốc và không được đưa vào tệp đã chuyển đổi. Khối nhận diện phải tự
  áp bước này trước khi so với ngưỡng.

Chốt **dùng một mô hình chống giả mạo** thay vì tổ hợp hai như kho nguồn, do ràng buộc tốc độ xử lý.
Ba hệ quả về cài đặt đã ghi lại đầy đủ để áp dụng ở Phase 4.

### 4. Điều chỉnh quy trình làm việc

- **Bỏ cơ chế thư mục làm việc tách rời**, chuyển sang dùng nhánh thông thường. Cơ chế cũ gây ba loại
  vướng mắc lặp lại, trong đó nghiêm trọng nhất là tồn tại hai bản đặc tả ở hai nơi có thể lệch nhau.
  Điều kiện an toàn thay thế: cây làm việc phải sạch trước mỗi lần bàn giao.
- Bổ sung ba quy tắc vào khung viết đặc tả, tất cả đều rút ra từ lỗi thật gặp trong tuần.

### 5. Báo cáo

- **Chương 2** — dựng khung 7 mục và viết hoàn chỉnh mục cơ sở lý thuyết về phát hiện giả mạo, gồm
  phân loại tấn công theo tiêu chuẩn quốc tế, đối chiếu hai hướng tiếp cận và giải trình lựa chọn.
- **Chương 5** — dựng khung, gom các hướng phát triển đã khảo sát nhưng nằm ngoài phạm vi.

## Số liệu

| Hạng mục | Giá trị | Nguồn |
|---|---|---|
| Dung lượng ảnh container | **252 MB** | `docker images`, cột content size |
| Thời gian dựng lần đầu | **1053 s ≈ 17 ph 33** | Đo khi dựng lại hoàn toàn, không dùng bộ nhớ đệm |
| Thời gian dựng lại có bộ nhớ đệm | 3–7 s | |
| Python trong container | 3.11.15 | |
| OpenCV / ONNX Runtime | 4.13.0 / 1.20.1 | |
| Ca kiểm thử chạy trong container ARM64 | 26 passed | |
| Số mã việc hoàn tất trong tuần | 2 | `docs/review/` |
| Số vòng sửa mỗi mã việc | 1 | |

> ⚠️ Thời gian chạy kiểm thử trong container **không dùng làm số hiệu năng**. Cùng một bộ kiểm thử đo
> được 16,21 s ở lần chạy nguội và 2,22 s ở lần chạy ấm — chênh hơn bảy lần chỉ do trạng thái bộ nhớ
> đệm của máy chủ giả lập. Đã bổ sung điều cấm này vào giao thức thực nghiệm.

## Kết quả phụ có giá trị

Container dựng thành công trên kiến trúc ARM64 với Python 3.11 mà **không phải thay đổi phiên bản gói
nào**. Điều này xác nhận bộ phiên bản đã cố định ở `P0-02` — vốn được chọn trên máy Windows x86-64 và
ghi chú là "bản nháp chờ kiểm chứng" — nay đã hợp lệ trên kiến trúc đích.

## Vướng mắc

- **Chưa có Raspberry Pi 5.** Bước 0.4 của Phase 0 phải hoãn. Bốn trong sáu chỉ tiêu cam kết chỉ đo
  được trên phần cứng thật; container giả lập chỉ kiểm được tính đúng đắn, không thay thế được phép đo.
- Một thông số tiền xử lý của mô hình chống giả mạo (khoảng giá trị chuẩn hoá đầu vào) **chưa chốt
  được** — cần một ảnh khuôn mặt thật để đối chứng. Phải xong trước Phase 4.

## Kế hoạch tuần sau

- Đóng Phase 0: viết mục môi trường triển khai của Chương 3, gắn thẻ phiên bản
- Bắt đầu Phase 1: quy ước đặt tên dữ liệu, đặc tả script thu thập ảnh, tải bộ dữ liệu đối chứng
- Phần thu thập dữ liệu thật vẫn chờ camera của hệ thống

---

*Nguồn: lịch sử git từ `ae41382` đến `f1aa944`; biên bản `docs/review/P0-02-dependency.review.md` và
`docs/review/P0-03-docker-arm64.review.md`.*
