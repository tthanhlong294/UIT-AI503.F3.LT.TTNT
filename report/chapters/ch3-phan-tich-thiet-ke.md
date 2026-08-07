# Chương 3 — Phân tích và Thiết kế

> **Khung làm việc.** Ngân sách **~10 trang**. Viết dần theo Cổng D của từng Phase.
>
> Chương này trình bày **hệ thống được thiết kế thế nào**, không trình bày kết quả đo. Mọi số liệu
> hiệu năng thuộc Chương 4.

| Mục | Trang | Viết ở Cổng D của | Trạng thái |
|---|---|---|---|
| 3.1 Yêu cầu chức năng và phi chức năng | ~1,5 | Phase 0 | ⬜ |
| **3.2 Môi trường phát triển và triển khai** | ~2 | Phase 0 | ✅ **bản nháp 1** |
| 3.3 Kiến trúc hệ thống — bốn khối | ~2,5 | Phase 6 | ⬜ |
| 3.4 Thiết kế cơ sở dữ liệu | ~1,5 | Phase 6 | ⬜ |
| 3.5 Thiết kế khối chấp hành và phân quyền | ~1,5 | Phase 5 | ⬜ |
| 3.6 Sơ đồ đấu nối phần cứng | ~1 | Phase 5 | ⬜ |

---

## 3.1. Yêu cầu chức năng và phi chức năng

`[CHƯA VIẾT]` — dàn ý: yêu cầu chức năng theo bốn khối · yêu cầu phi chức năng gắn với sáu chỉ tiêu
cam kết · ràng buộc về quyền riêng tư (xử lý cục bộ) · ràng buộc tài nguyên của thiết bị biên.

---

## 3.2. Môi trường phát triển và triển khai

### 3.2.1. Vấn đề khác biệt kiến trúc

Thiết bị đích của hệ thống là Raspberry Pi 5, sử dụng vi xử lý kiến trúc **ARM64** chạy hệ điều hành
Linux. Trong khi đó, quá trình phát triển diễn ra trên máy tính cá nhân kiến trúc **x86-64** chạy
Windows. Hai kiến trúc tập lệnh này không tương thích ở mức mã máy, dẫn tới hai rủi ro cụ thể:

1. Một thư viện cài đặt được trên môi trường phát triển có thể **không có bản phân phối biên dịch sẵn**
   cho kiến trúc ARM64, hoặc chỉ có ở phiên bản khác.
2. Mã nguồn chạy đúng trên môi trường phát triển vẫn có thể lỗi trên thiết bị đích do khác biệt về thư
   viện hệ thống hoặc về cách xử lý số thực.

Nếu chỉ phát hiện những khác biệt này khi đã có phần cứng trong tay, chi phí sửa chữa sẽ cao và rơi vào
giai đoạn muộn của tiến độ.

### 3.2.2. Giải pháp — container giả lập kiến trúc đích

Nghiên cứu xây dựng một môi trường container mô phỏng kiến trúc ARM64 ngay trên máy phát triển, sử
dụng cơ chế giả lập tập lệnh của nền tảng container. Container này cho phép kiểm chứng tính đúng đắn
của mã nguồn trên đúng kiến trúc và đúng phiên bản Python của thiết bị đích, trước khi phần cứng sẵn sàng.

**Ba quyết định thiết kế:**

| Quyết định | Lý do |
|---|---|
| Dùng **Python 3.11**, không dùng phiên bản mới hơn có trên máy phát triển | Khớp với phiên bản mặc định của hệ điều hành Raspberry Pi OS 64-bit; môi trường mô phỏng phải phản ánh đúng thiết bị đích |
| **Khai báo kiến trúc đích ngay trong tệp cấu hình container**, không dựa vào tham số dòng lệnh | Nếu để người dựng tự truyền tham số, một lần quên sẽ tạo ra ảnh container sai kiến trúc mà vẫn chạy được, khiến mọi số đo sau đó sai mà không có dấu hiệu cảnh báo |
| **Tách phụ thuộc thành hai tập**: môi trường chạy và môi trường phát triển | Thư viện phục vụ chuyển đổi mô hình có dung lượng rất lớn và chỉ cần trên máy phát triển; đưa vào ảnh container sẽ làm phình dung lượng vô ích |

Ngoài ra, tệp cấu hình sắp xếp các lớp sao cho bước cài đặt thư viện đứng **trước** bước sao chép mã
nguồn. Nhờ vậy, khi chỉ sửa mã nguồn thì lớp cài đặt thư viện được tái sử dụng từ bộ nhớ đệm — điều
này đặc biệt quan trọng vì cài đặt thư viện dưới môi trường giả lập rất tốn thời gian.

### 3.2.3. Kết quả

**Bảng 3.x.** Thông số môi trường giả lập ARM64

| Hạng mục | Giá trị |
|---|---|
| Kiến trúc ảnh container | `arm64` |
| Hệ điều hành nền | Debian Bookworm |
| Python | 3.11.15 |
| OpenCV | 4.13.0 |
| ONNX Runtime | 1.20.1 |
| **Dung lượng ảnh container** | **252 MB** |
| Thời gian dựng lần đầu | 1053 s (≈ 17 phút 33 giây) |
| Thời gian dựng lại khi chỉ sửa mã nguồn | 3–7 s |

*Nguồn: `docs/review/P0-03-docker-arm64.review.md`. Đo trên máy phát triển Windows x86-64.*

Chênh lệch giữa 1053 giây và 3–7 giây xác nhận cơ chế bộ nhớ đệm theo lớp hoạt động đúng như thiết kế
ở mục 3.2.2.

Môi trường này đã được kiểm chứng bằng cách chạy toàn bộ **26 ca kiểm thử** của khối nền tảng bên trong
container, tất cả đều đạt. Ngoài ra, việc dựng thành công trên kiến trúc ARM64 với Python 3.11 mà không
phải thay đổi phiên bản thư viện nào đã xác nhận bộ phiên bản cố định — vốn được chọn trên môi trường
Windows x86-64 — là hợp lệ trên kiến trúc đích.

### 3.2.4. Giới hạn của môi trường giả lập

Container giả lập dùng để kiểm chứng **tính đúng đắn**, không dùng để **đo hiệu năng**. Cơ chế giả lập
dịch từng lệnh máy giữa hai kiến trúc, nên thời gian thực thi vừa chậm hơn nhiều lần vừa không ổn định.

Một minh chứng đo được trong quá trình phát triển: cùng một bộ kiểm thử, cùng ảnh container, thời gian
chạy là 16,21 giây ở lần chạy nguội và 2,22 giây ở lần chạy ấm — chênh lệch hơn bảy lần chỉ do trạng
thái bộ nhớ đệm của máy chủ.

Do đó, toàn bộ chỉ số tốc độ khung hình, độ trễ và nhiệt độ trình bày ở Chương 4 đều được đo **trên
Raspberry Pi 5 thật**. Kết quả từ môi trường giả lập không được đưa vào bảng đối chiếu chỉ tiêu.

`[BỔ SUNG SAU]` — mục môi trường triển khai trên phần cứng thật (hệ điều hành, cấu hình camera, tản
nhiệt) viết khi có Raspberry Pi 5.

---

## 3.3. Kiến trúc hệ thống — bốn khối

`[CHƯA VIẾT]` — dàn ý: sơ đồ khối tổng thể · luồng dữ liệu từ thu hình tới chấp hành · quy tắc phụ
thuộc một chiều giữa các khối · giao diện giữa các khối · cơ chế trừu tượng hoá phần cứng cho phép
kiểm thử không cần thiết bị thật.

---

## 3.4. Thiết kế cơ sở dữ liệu

`[CHƯA VIẾT]` — dàn ý: lược đồ các bảng người dùng, nhật ký nhận diện, cảnh báo, trạng thái thiết bị ·
cách lưu vectơ đặc trưng · chính sách lưu trữ ảnh cảnh báo.

---

## 3.5. Thiết kế khối chấp hành và phân quyền

`[CHƯA VIẾT]` — dàn ý: bảng ánh xạ danh tính sang quyền điều khiển thiết bị · logic chống nhiễu theo
số khung hình liên tiếp · cơ chế chờ giữa hai lần kích hoạt · nguyên tắc an toàn khi lỗi.

---

## 3.6. Sơ đồ đấu nối phần cứng

`[CHƯA VIẾT]` — cần Raspberry Pi 5 và linh kiện. Dàn ý: bảng chân cắm · sơ đồ nối module chuyển mạch
và đèn báo · mạch phát hồng ngoại · nguồn cấp.

---

## Checklist hoàn thành Chương 3

- [ ] Mọi mục không còn `[CHƯA VIẾT]`
- [ ] Chương trình bày **thiết kế**, không lẫn số liệu kết quả (thuộc Chương 4)
- [ ] Mỗi quyết định thiết kế đều nêu **lý do**, không chỉ mô tả đã làm gì
- [ ] Sơ đồ kiến trúc khớp với cấu trúc mã nguồn thực tế
- [ ] Bảng/hình có số, tiêu đề, nguồn và được dẫn trong thân bài
- [ ] Không dùng ngôi thứ nhất
- [ ] Độ dài ~10 trang
