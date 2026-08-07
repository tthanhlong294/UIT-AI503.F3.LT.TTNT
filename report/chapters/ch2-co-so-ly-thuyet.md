# Chương 2 — Cơ sở lý thuyết

> **Khung làm việc.** Ngân sách **~11 trang** — chương dài nhất báo cáo.
> Không phụ thuộc kết quả thực nghiệm nên viết được sớm, viết dần theo Cổng D của từng Phase.
>
> Nguyên tắc: chương này trình bày **phương pháp**, không trình bày **kết quả**. Mọi con số đo được
> của nghiên cứu này thuộc Chương 4. Số liệu của công trình khác phải kèm trích dẫn và nói rõ đó là
> kết quả của họ.

| Mục | Trang | Viết ở Cổng D của | Trạng thái |
|---|---|---|---|
| 2.1 Mạng nơ-ron tích chập | ~1,5 | Phase 2 | ⬜ |
| 2.2 Phát hiện khuôn mặt — YOLOv8n-face | ~2 | Phase 2 | ⬜ |
| 2.3 Trích xuất đặc trưng khuôn mặt | ~2,5 | Phase 3 | ⬜ |
| 2.4 Học đo lường và độ tương đồng cosine | ~1,5 | Phase 3 | ⬜ |
| **2.5 Phát hiện giả mạo** | ~2 | Phase 4 | ✅ **bản nháp 1** |
| 2.6 Suy luận trên thiết bị biên | ~1 | Phase 2 | ⬜ |
| 2.7 Điều khiển thiết bị — GPIO và hồng ngoại | ~0,5 | Phase 5 | ⬜ |

---

## 2.1. Mạng nơ-ron tích chập trong thị giác máy tính

`[CHƯA VIẾT]` — dàn ý: phép tích chập và trường tiếp nhận · lớp gộp · hàm kích hoạt · tích chập tách
theo chiều sâu (depthwise separable) và vì sao nó là nền tảng của mọi mạng nhẹ dùng trong đồ án.

---

## 2.2. Phát hiện khuôn mặt — YOLOv8n-face

`[CHƯA VIẾT]` — dàn ý: bài toán phát hiện đối tượng · **hai giai đoạn so với một giai đoạn**, vì sao
một giai đoạn phù hợp với suy luận thời gian thực · kiến trúc YOLOv8 (backbone, neck, head) · biến thể
`n` và đánh đổi độ chính xác ↔ tốc độ · đầu ra khung bao, độ tin cậy và 5 điểm mốc · NMS.

> Mục này phải nối lại với §1.3: khoảng trống đã nêu là các công trình khảo sát đều dùng phương pháp
> xếp tầng hoặc đa giai đoạn, không dùng mô hình một giai đoạn.

---

## 2.3. Trích xuất đặc trưng khuôn mặt

`[CHƯA VIẾT]` — dàn ý: khái niệm vectơ đặc trưng · dlib/ResNet 128 chiều · MobileFaceNet và ArcFace
512 chiều · hàm mất mát biên góc · **trình bày cả hai phương án** vì Chương 4 so sánh chúng.

---

## 2.4. Học đo lường và độ tương đồng cosine

`[CHƯA VIẾT]` — dàn ý: không gian đặc trưng và khoảng cách · cosine similarity so với khoảng cách
Euclid · chuẩn hoá L2 · ngưỡng quyết định · **bài toán tập đóng so với tập mở** · định nghĩa FAR, FRR,
EER và đường cong ROC/DET.

---

## 2.5. Phát hiện giả mạo (liveness detection)

### 2.5.1. Bài toán và phân loại tấn công trình diện

Hệ thống nhận diện khuôn mặt chỉ so khớp đặc trưng sinh trắc học mà không tự phân biệt được nguồn gốc
của khuôn mặt trong khung hình. Một bức ảnh in hoặc màn hình điện thoại hiển thị ảnh người đã đăng ký
vẫn tạo ra vectơ đặc trưng gần như trùng khớp với người thật. Khối phát hiện giả mạo (anti-spoofing,
hay liveness detection) có nhiệm vụ trả lời câu hỏi độc lập: khuôn mặt đang xuất hiện là **người thật
hiện diện trước camera** hay là một bản sao.

Tiêu chuẩn ISO/IEC 30107-3 gọi các hình thức này là **tấn công trình diện** (presentation attack) và
phân loại theo phương tiện tấn công `[n]`:

| Nhóm | Phương tiện | Trong phạm vi nghiên cứu này |
|---|---|---|
| Tấn công 2D — in | Ảnh in trên giấy, có thể cắt lỗ mắt | **Có** |
| Tấn công 2D — phát lại | Ảnh hoặc video hiển thị trên màn hình điện thoại, máy tính bảng | **Có** |
| Tấn công 3D | Mặt nạ silicon, mô hình đầu 3D | Không |
| Tấn công số | Video giả mạo tổng hợp (deepfake) đưa trực tiếp vào luồng dữ liệu | Không |

Nghiên cứu này giới hạn ở hai nhóm tấn công 2D. Đây là hai hình thức có chi phí thực hiện thấp nhất —
chỉ cần một bức ảnh của chủ nhà — nên cũng là mối đe doạ thực tế nhất đối với hệ thống trong hộ gia
đình. Hai nhóm còn lại đòi hỏi chi phí và điều kiện tiếp cận cao hơn nhiều, nằm ngoài mô hình đe doạ
được xét.

### 2.5.2. Hai hướng tiếp cận

**Hướng thứ nhất — phân loại nhị phân trên đặc trưng kết cấu.** Mô hình nhận ảnh khuôn mặt đã cắt và
đưa ra một điểm số thật/giả. Cơ sở nhận biết nằm ở dấu vết mà quá trình tái tạo để lại: mạng lưới điểm
mực của ảnh in, vân lưới điểm ảnh và hiện tượng moiré của màn hình, phản xạ ánh sáng bất thường trên
bề mặt phẳng, mất chi tiết tần số cao do đã qua một vòng chụp lại. Ưu điểm là kiến trúc gọn và chi phí
suy luận thấp; hạn chế là mô hình dễ học vào đặc thù của thiết bị và điều kiện chụp trong tập huấn
luyện, nên khả năng khái quát hoá sang miền dữ liệu mới thường giảm.

**MiniFASNet**, thuộc dự án Silent Face Anti-Spoofing, là đại diện của hướng này `[n]`. Mô hình dùng
kiến trúc nhẹ kiểu MobileNet với ảnh đầu vào kích thước nhỏ, xử lý toàn bộ trên một khung hình đơn
mà không cần chuỗi thời gian hay tương tác từ người dùng.

**Hướng thứ hai — giám sát theo điểm ảnh.** Thay vì huấn luyện mô hình đưa ra một nhãn nhị phân, hướng
này buộc mạng dự đoán một bản đồ có ý nghĩa vật lý — thường là **bản đồ độ sâu** của khuôn mặt. Trực
giác đứng sau: khuôn mặt thật là một bề mặt ba chiều nên bản đồ độ sâu có cấu trúc lồi lõm, còn ảnh in
hay màn hình là mặt phẳng nên bản đồ độ sâu gần như phẳng đều. Tín hiệu giám sát dày đặc theo từng
điểm ảnh cung cấp nhiều thông tin hơn một nhãn nhị phân, giúp mô hình khái quát hoá tốt hơn.

**CDCN** (Central Difference Convolutional Network) là công trình tiêu biểu của hướng này `[n]`. Đóng
góp cốt lõi là **tích chập sai phân trung tâm**: bên cạnh tổng có trọng số như tích chập thông thường,
phép toán cộng thêm thành phần chênh lệch giữa các điểm lân cận và điểm trung tâm, với tham số `θ`
điều tiết mức đóng góp của thành phần gradient. Cơ sở của thiết kế này là dấu vết giả mạo thể hiện ở
**biến thiên cục bộ của cường độ** rõ hơn ở giá trị cường độ tuyệt đối. Mạng nhận ảnh 3 × 256 × 256 và
dự đoán bản đồ độ sâu mức xám 32 × 32, huấn luyện bằng tổ hợp sai số bình phương trung bình và hàm mất
mát độ sâu tương phản. Phiên bản mở rộng CDCN++ bổ sung backbone tìm bằng tìm kiếm kiến trúc tự động
và khối hợp nhất chú ý đa tỉ lệ, đạt thứ hạng cao tại các cuộc thi phát hiện tấn công trình diện.

### 2.5.3. Lựa chọn của nghiên cứu này

**Bảng 2.x.** Đối chiếu hai hướng tiếp cận theo ràng buộc triển khai của nghiên cứu

| Tiêu chí | MiniFASNet | CDCN |
|---|---|---|
| Hướng tiếp cận | Phân loại nhị phân trên kết cấu | Giám sát theo điểm ảnh, bản đồ độ sâu |
| Kích thước ảnh đầu vào | 80 × 80 | **256 × 256** — gấp khoảng 10 lần số điểm ảnh |
| Đầu ra | Điểm số phân lớp | Bản đồ độ sâu 32 × 32, cần hậu xử lý |
| Trọng số huấn luyện sẵn | **Có, do nhóm tác giả phát hành** | **Không công bố trong công trình gốc** |
| Định dạng triển khai | Có bản ONNX sẵn | Mã nguồn nghiên cứu, PyTorch |
| Độ chính xác trên bộ chuẩn | Thấp hơn | **Cao hơn** |
| Khái quát hoá chéo bộ dữ liệu | Yếu hơn | **Tốt hơn** |

*Nguồn: tổng hợp từ tài liệu `[n]`, `[n]`. Các đánh giá về độ chính xác là kết quả công bố của các
công trình tương ứng, không phải kết quả đo của nghiên cứu này.*

Nghiên cứu này lựa chọn **MiniFASNet**. Lý do xếp theo mức quyết định:

1. **Ràng buộc về trọng số huấn luyện sẵn.** Phạm vi nghiên cứu loại trừ việc huấn luyện lại mô hình,
   do đó chỉ những mô hình có trọng số được phát hành mới sử dụng được. Công trình CDCN gốc không công
   bố trọng số; các bản cài đặt lại của bên thứ ba không được nhóm tác giả xác nhận và không có số liệu
   chuẩn để đối chiếu.
2. **Ràng buộc tài nguyên tính toán.** Hệ thống đặt chỉ tiêu tốc độ xử lý toàn luồng, trong đó khối
   phát hiện giả mạo chỉ chiếm một phần nhỏ ngân sách mỗi khung hình. Chênh lệch khoảng mười lần về số
   điểm ảnh đầu vào, cộng với chi phí cao hơn của phép tích chập sai phân, khiến CDCN khó khả thi trên
   nền tảng đã chọn.
3. **Phạm vi tấn công được xét.** Ưu thế của hướng giám sát theo độ sâu thể hiện rõ nhất khi cần khái
   quát hoá sang nhiều loại tấn công và nhiều miền dữ liệu. Nghiên cứu này giới hạn ở hai hình thức
   tấn công 2D trong một môi trường sử dụng cố định, nên phần năng lực vượt trội đó không được khai
   thác tương xứng với chi phí phải trả.

Đây là lựa chọn có đánh đổi được nêu rõ, không phải khẳng định MiniFASNet tốt hơn CDCN. Trong điều kiện
không bị ràng buộc về tài nguyên và có sẵn trọng số, hướng giám sát theo điểm ảnh là lựa chọn mạnh hơn.

### 2.5.4. Chỉ số đánh giá theo ISO/IEC 30107-3

Đánh giá hệ thống phát hiện tấn công trình diện dùng ba chỉ số chuẩn hoá `[n]`:

| Chỉ số | Định nghĩa | Ý nghĩa |
|---|---|---|
| **APCER** | Tỉ lệ mẫu tấn công bị phân loại nhầm thành mẫu thật | Tấn công lọt qua hệ thống |
| **BPCER** | Tỉ lệ mẫu thật bị phân loại nhầm thành tấn công | Người dùng hợp lệ bị từ chối |
| **ACER** | Trung bình cộng của APCER và BPCER | Chỉ số tổng hợp |

APCER phải được **báo cáo tách riêng cho từng loại tấn công** rồi lấy giá trị lớn nhất, vì một hệ thống
có thể chặn tốt ảnh in nhưng yếu trước màn hình. Chỉ tiêu "phát hiện tối thiểu 90 % tấn công" của nghiên
cứu này tương đương APCER ≤ 10 %.

Đối với hệ thống điều khiển thiết bị trong hộ gia đình, **APCER được ưu tiên hơn BPCER**: một lần tấn
công lọt qua cấp quyền điều khiển thiết bị điện cho người lạ, trong khi một lần từ chối nhầm chỉ gây
bất tiện và người dùng có thể thử lại.

---

## 2.6. Suy luận trên thiết bị biên

`[CHƯA VIẾT]` — dàn ý: đồ thị tính toán và định dạng ONNX · ONNX Runtime trên ARM · NCNN và tối ưu cho
di động · lượng tử hoá · cấu hình số luồng · vì sao không dùng khung học sâu đầy đủ trên thiết bị đích.

---

## 2.7. Điều khiển thiết bị — GPIO và hồng ngoại

`[CHƯA VIẾT]` — dàn ý: chân GPIO trên Raspberry Pi 5 · module relay và cách ly quang · giao thức điều
khiển hồng ngoại, mã hoá NEC · nguyên tắc an toàn khi thao tác điện.

---

## Checklist hoàn thành Chương 2

- [ ] Mọi mục không còn `[CHƯA VIẾT]`
- [ ] Chương trình bày **phương pháp**, không lẫn kết quả đo của nghiên cứu này
- [ ] Số liệu của công trình khác đều kèm trích dẫn và nói rõ là kết quả của họ
- [ ] Thuật ngữ tiếng Anh lần đầu ghi kèm tiếng Việt, các lần sau dùng nhất quán
- [ ] §2.2 nối lại được với khoảng trống đã nêu ở §1.3
- [ ] §2.3 trình bày **cả hai** phương án nhận diện, không thiên vị bên nào trước khi có số đo
- [ ] Mọi `[n]` đã thay bằng số trích dẫn thật, có mục trong `refs.bib`
- [ ] Không dùng ngôi thứ nhất
- [ ] Độ dài ~11 trang
