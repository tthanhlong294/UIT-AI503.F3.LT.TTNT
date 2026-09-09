# Chương 3 — Phân tích và Thiết kế

> **Khung làm việc.** Ngân sách **~10 trang**. Viết dần theo Cổng D của từng Phase.
>
> Chương này trình bày **hệ thống được thiết kế thế nào**, không trình bày kết quả đo. Mọi số liệu
> hiệu năng thuộc Chương 4.

| Mục | Trang | Viết ở Cổng D của | Trạng thái |
|---|---|---|---|
| 3.1 Yêu cầu chức năng và phi chức năng | ~1,5 | Phase 0 | ⬜ |
| **3.2 Môi trường phát triển và triển khai** | ~2 | Phase 0 | ✅ **bản nháp 1** |
| **3.3 Kiến trúc hệ thống — bốn khối** | ~2,5 | Phase 6 | ✅ **nháp 1 — phần đã cài đặt** |
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

> **Ghi chú về trạng thái.** Mục này được viết khi hệ thống đã cài đặt xong phần thu hình, phát hiện
> và căn chỉnh, còn các khối phía sau mới ở mức thiết kế. Phần mô tả kiến trúc đã cài đặt dựa trên
> mã nguồn thật và có thể kiểm chứng trong kho mã; phần còn lại được ghi rõ là **thiết kế dự kiến**
> và sẽ được cập nhật khi triển khai xong.

### 3.3.1. Bốn khối và trách nhiệm của từng khối

Hệ thống được phân rã thành bốn khối chức năng, mỗi khối đảm nhiệm một giai đoạn của chuỗi xử lý và
được cài đặt thành một gói mã nguồn độc lập.

**Hình 3.x.** `[CHƯA VẼ]` Sơ đồ khối tổng thể — bốn khối, luồng dữ liệu một chiều từ camera tới thiết
bị chấp hành, và các nhánh phụ đi tới khối giám sát.

**Bảng 3.x.** Bốn khối, module tương ứng và trạng thái cài đặt

| Khối | Trách nhiệm | Module | Trạng thái |
|---|---|---|---|
| 1a — Thu hình | Mở camera, cấp khung hình liên tục, xử lý mất kết nối | `src/capture/` | **Đã cài đặt** |
| 1b — Phát hiện | Tìm khuôn mặt, trả về khung bao và 5 điểm mốc | `src/detector/` | **Đã cài đặt** |
| — Căn chỉnh | Đưa khuôn mặt về ảnh chuẩn 112 × 112 | `src/preprocess/` | **Đã cài đặt** |
| 1c — Chống giả mạo | Phân biệt người thật với ảnh in hoặc màn hình | `src/antispoof/` | Thiết kế dự kiến |
| 1d — Nhận diện | Sinh vectơ đặc trưng, so khớp với danh sách đã đăng ký | `src/recognizer/` | Thiết kế dự kiến |
| 2 — Quyết định | Áp bảng phân quyền, chống nhiễu theo thời gian | `src/decision/` | Thiết kế dự kiến |
| 3 — Chấp hành | Điều khiển relay qua GPIO, phát mã hồng ngoại | `src/actuator/` | Thiết kế dự kiến |
| 4 — Giám sát | Giao diện web, cảnh báo Telegram, ghi nhật ký | `src/monitor/` | Thiết kế dự kiến |

Khối 1 được chia thành bốn thành phần nhỏ vì bốn thành phần này chạy nối tiếp trên cùng một khung hình
và có thể được thay thế độc lập với nhau. Riêng bước căn chỉnh không tạo thành một khối riêng trong
kiến trúc bốn khối, mà là cầu nối kỹ thuật giữa phát hiện và hai thành phần phía sau — cả chống giả
mạo lẫn nhận diện đều cần ảnh khuôn mặt đã chuẩn hoá.

### 3.3.2. Luồng dữ liệu qua chuỗi xử lý

Dữ liệu đi một chiều qua chuỗi, và mỗi chặng chuyển giao một kiểu dữ liệu xác định:

```
Camera ──► khung hình      (mảng ảnh BGR, H × W × 3)
       ──► phát hiện       (danh sách FaceBox: khung bao, độ tin cậy, 5 điểm mốc)
       ──► căn chỉnh       (ảnh 112 × 112 × 3)
       ──► chống giả mạo   (nhãn thật/giả kèm điểm số)
       ──► nhận diện       (Identity: mã người dùng, độ tương đồng, backend)
       ──► quyết định      (Command: thiết bị, hành động, nguồn, thời điểm)
       ──► chấp hành       (thay đổi trạng thái thiết bị)
```

Việc quy định rõ kiểu dữ liệu tại từng ranh giới mang lại hai lợi ích. Thứ nhất, mỗi khối có thể được
kiểm thử độc lập bằng dữ liệu dựng sẵn, không cần các khối lân cận. Thứ hai, thay thế một khối chỉ đòi
hỏi bản cài mới tuân thủ đúng kiểu vào và kiểu ra, không kéo theo sửa đổi ở nơi khác.

**Thứ tự chống giả mạo trước nhận diện là bắt buộc.** Nếu đặt ngược lại, hệ thống sẽ tốn chi phí trích
xuất đặc trưng cho những khuôn mặt rốt cuộc bị loại vì là ảnh in hoặc màn hình. Đặt khối chống giả mạo
lên trước cho phép loại sớm, giữ lại ngân sách tính toán cho những khung hình thực sự cần xử lý đầy đủ.
Thứ tự này cũng đúng về mặt an ninh: quyết định "có phải người thật không" độc lập với quyết định
"người này là ai", và câu hỏi thứ nhất cần được trả lời trước.

### 3.3.3. Quy tắc phụ thuộc một chiều

Kiến trúc tuân theo một quy tắc phụ thuộc chặt: **`src/common/` là nền tảng chung và không phụ thuộc
bất kỳ khối nào; mọi khối chỉ được phép phụ thuộc vào `src/common/`, không import chéo lẫn nhau.**

Gói `src/common/` chứa những thứ mọi khối đều cần: các kiểu dữ liệu chuyển giao (`FaceBox`, `Identity`,
`Command`), cây phân cấp ngoại lệ, bộ nạp cấu hình và bộ ghi nhật ký.

Quy tắc này không chỉ là quy ước trên giấy mà kiểm chứng được bằng cách quét câu lệnh `import` trong mã
nguồn. Ở trạng thái hiện tại, ba khối đã cài đặt đều chỉ import từ `src.common` và từ chính gói của
mình; không tồn tại đường phụ thuộc giữa hai khối bất kỳ.

Ràng buộc này phục vụ trực tiếp một mục tiêu của đề tài. Chương 4 phải đối chiếu **hai phương án nhận
diện** trên cùng điều kiện. Phép so sánh đó chỉ thực hiện được nếu khối nhận diện thay thế được mà
không đụng tới phần còn lại của hệ thống — điều mà quy tắc phụ thuộc một chiều bảo đảm. Nếu các khối
tham chiếu lẫn nhau, việc đổi backend nhận diện sẽ kéo theo sửa đổi lan rộng và hai phương án sẽ không
còn chạy trên cùng một hệ thống nữa.

### 3.3.4. Giao diện giữa các khối

**Bảng 3.x.** Giao diện đã cài đặt và kiểm định

| Khối | Giao diện |
|---|---|
| Thu hình | `BoThuHinh` — lớp trừu tượng với `mo()`, `doc_frame() -> ndarray`, `dong()`, `dang_mo` |
| | `tao_bo_thu_hinh(cfg) -> BoThuHinh` — chọn bản cài theo cấu hình |
| Phát hiện | `YoloFaceDetector.detect(khung_hinh) -> list[FaceBox]` |
| | thuộc tính `kich_thuoc_vao` — đọc từ đồ thị mô hình, không từ cấu hình |
| Căn chỉnh | `can_chinh(anh, diem_moc, cfg) -> ndarray` |
| Nền tảng | `nap_cau_hinh(duong_dan) -> dict`, `lay_gia_tri(cfg, khoa)`, `lay_logger(ten)` |

Các giao diện dự kiến cho những khối chưa triển khai, theo đề cương: khối nhận diện cung cấp
`enroll(images) -> Embedding` và `identify(face) -> (user_id, score)`; khối chống giả mạo cung cấp
`is_live(face_crop) -> (bool, score)`; khối chấp hành định nghĩa một lớp trừu tượng chung cho các bản
cài GPIO, hồng ngoại và giả lập.

Toàn bộ tham số điều chỉnh được — ngưỡng, kích thước ảnh, số luồng, đường dẫn — nằm trong các tệp cấu
hình YAML, không viết thẳng vào mã. Nhờ vậy việc quét ngưỡng ở Chương 4 thực hiện được bằng cách đổi
cấu hình, không phải sửa mã nguồn, và mỗi lần đo có thể ghi lại đúng cấu hình đã dùng.

### 3.3.5. Trừu tượng hoá phần cứng

Hệ thống phụ thuộc vào ba nhóm thiết bị: camera, chân GPIO và bộ phát hồng ngoại. Nếu mã nguồn gọi
trực tiếp tới chúng, toàn bộ hệ thống sẽ chỉ chạy được trên thiết bị đích, và việc kiểm thử tự động
trở nên bất khả thi.

Giải pháp là **trừu tượng hoá phần cứng**: mỗi nhóm thiết bị được che sau một lớp trừu tượng, với ít
nhất hai bản cài đặt — một bản làm việc với thiết bị thật, một bản **giả lập** dùng khi không có thiết
bị. Việc chọn bản nào do tệp cấu hình quyết định, mã gọi không cần biết.

Khối thu hình đã áp dụng khuôn mẫu này: lớp trừu tượng `BoThuHinh` có bản cài `opencv_camera` làm việc
với camera thật và bản cài `mock_camera` sinh khung hình tổng hợp theo một seed cho trước, hoặc đọc
lần lượt ảnh từ một thư mục.

Hiệu quả của thiết kế này quan sát được trực tiếp trong quá trình phát triển: toàn bộ bộ kiểm thử tự
động của hệ thống chạy được trên máy phát triển **không có camera**, và chạy được cả trong môi trường
container mô phỏng kiến trúc ARM64. Nhờ đó, phần lớn công việc phát triển và kiểm định đã hoàn thành
trước khi phần cứng đích sẵn sàng.

Cùng khuôn mẫu sẽ được áp dụng cho khối chấp hành: lớp trừu tượng chung cho thao tác bật/tắt thiết bị,
với bản cài GPIO cho thiết bị thật và bản cài giả lập ghi nhật ký thay vì tác động vật lý. Điều này đặc
biệt cần thiết với khối chấp hành, vì lỗi lập trình ở đây có hậu quả vật lý chứ không chỉ là kết quả
sai trên màn hình.

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
