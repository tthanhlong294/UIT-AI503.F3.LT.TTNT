# ĐỀ CƯƠNG CHI TIẾT ĐỒ ÁN TỐT NGHIỆP

> Bản Markdown hoá từ `docs/DC DATN Trần Thanh Long - 25410088 ... .pdf` và
> `docs/Don DKDA Trần Thanh Long - 25410088.docx`. Đây là **nguồn sự thật (source of truth)**
> về phạm vi, mục tiêu và tiến độ của đồ án. Mọi thay đổi phạm vi phải cập nhật file này trước.

---

## 1. Thông tin chung

| Mục | Nội dung |
|---|---|
| **Tên đề tài (VI)** | Nghiên cứu và triển khai hệ thống nhận diện khuôn mặt trên Raspberry Pi 5 ứng dụng điều khiển thiết bị trong nhà thông minh |
| **Tên đề tài (EN)** | Research and implementation of a facial recognition system on Raspberry Pi 5 for smart home device control |
| **Sinh viên** | Trần Thanh Long — MSSV 25410088 |
| **Lớp** | AI503.F3.LT.TTNT |
| **Cán bộ hướng dẫn** | ThS. Phan Đình Duy |
| **Đơn vị** | Trường ĐH Công nghệ Thông tin — ĐHQG TP. HCM, Khoa Khoa học Máy tính |
| **Học kỳ** | HK3, Năm học 2025 – 2026 |
| **Thời gian thực hiện** | 07/07/2026 – 30/09/2026 (thực thi chính: 15/07/2026 – 23/09/2026, 10 tuần) |
| **Mốc nộp báo cáo** | 23 – 24/09/2026 |
| **Mốc bảo vệ** | Dự kiến 10/10/2026 |

---

## 2. Mục tiêu

### 2.1. Mục tiêu tổng quát

Nghiên cứu, xây dựng và triển khai một **hệ thống nhúng hoàn chỉnh trên Raspberry Pi 5** có khả năng:

1. Nhận diện khuôn mặt **thời gian thực** từ camera;
2. Tích hợp cơ chế **chống giả mạo khuôn mặt (anti-spoofing)**;
3. **Tự động điều khiển thiết bị điện trong nhà** (đèn, tivi) theo danh tính người dùng đã đăng ký;
4. **Cảnh báo khi phát hiện người lạ**;
5. Cho phép **giám sát hệ thống từ xa** qua ứng dụng web.

Hệ thống dùng **kiến trúc hai tầng**: `YOLOv8n-face` (phát hiện khuôn mặt) → mô hình **embedding**
(nhận diện danh tính), **xử lý hoàn toàn cục bộ trên thiết bị nhúng (edge AI)** — không gửi dữ liệu
khuôn mặt lên cloud.

Quy trình phát triển: **giả lập trước → phần cứng thật sau**, chỉ deploy lên Pi 5 khi pipeline đã ổn định.

### 2.2. Mục tiêu cụ thể

| # | Mục tiêu | Đầu ra kiểm chứng được |
|---|---|---|
| MT1 | Nghiên cứu cơ sở lý thuyết nhận diện khuôn mặt trên thiết bị nhúng tài nguyên hạn chế | Chương 2 báo cáo + bảng khảo sát công trình liên quan |
| MT2 | Xây dựng pipeline phát hiện khuôn mặt thời gian thực bằng YOLOv8n-face (Ultralytics) | Module `detector` chạy ≥ 10 FPS trên Pi 5 |
| MT3 | Cài đặt và **đánh giá so sánh thực nghiệm 2 phương pháp nhận diện danh tính**: `face_recognition` (dlib) vs. **MobileFaceNet/ArcFace (ONNX)** theo độ chính xác, FPS, độ trễ → chọn phương án tối ưu | Bảng benchmark có số liệu đo thực tế + kết luận lựa chọn |
| MT4 | Tích hợp module chống giả mạo (liveness detection: MiniFASNet / Silent Face Anti-Spoofing), phát hiện tấn công bằng **ảnh in** và **ảnh/video trên màn hình điện thoại** | Tỉ lệ phát hiện tấn công ≥ 90% trên bộ test giả mạo |
| MT5 | Xây dựng khối điều khiển thiết bị đa phương thức: **relay qua GPIO** (đèn), **phát lệnh IR** (tivi), có **phân quyền theo danh tính**; mở rộng **MQTT/WiFi** nếu còn thời gian | Điều khiển thành công 2 nhóm thiết bị, độ trễ < 2 s |
| MT6 | Xây dựng chức năng **cảnh báo người lạ** (chụp ảnh, ghi log, gửi Telegram) và **web giám sát** (trạng thái, lịch sử nhận diện, quản lý người dùng) | Web chạy ổn định trong LAN + bot Telegram gửi được cảnh báo |

---

## 3. Đối tượng nghiên cứu

### 3.1. Mô hình học sâu dạng nhẹ cho thiết bị nhúng

| Vai trò | Mô hình | Ghi chú |
|---|---|---|
| Phát hiện khuôn mặt | **YOLOv8n-face** | Ultralytics; export ONNX / NCNN |
| Nhận diện danh tính — Phương án A | **`face_recognition` (dlib)** | Baseline, dễ triển khai |
| Nhận diện danh tính — Phương án B | **MobileFaceNet / ArcFace (ONNX)** | Embedding, kỳ vọng nhanh hơn trên ARM |
| Chống giả mạo | **MiniFASNet** (Silent Face Anti-Spoofing) | Chạy sau bước detect |

### 3.2. Phần cứng

- **Raspberry Pi 5 (8 GB RAM)** — máy tính nhúng chính.
- Camera Module hoặc **USB Webcam**.
- **Module relay**, **LED** (mô phỏng đèn), **đèn phát hồng ngoại IR** (điều khiển tivi).

### 3.3. Môi trường & dữ liệu

- **Môi trường giả lập Docker ARM64** trên máy cá nhân — phát triển & kiểm thử trước.
- **Cơ sở dữ liệu khuôn mặt đăng ký (gallery)**: sinh viên thực hiện + thành viên gia đình
  (**2 – 3 người**) — đây là những người được cấp quyền điều khiển thiết bị.
- **Tập người lạ (impostor)** phục vụ đo FAR, gồm **ba nguồn**:
  1. **LFW gốc** (Labeled Faces in the Wild) — ≥ 100 danh tính, đủ mẫu để đo FAR ở mức 1 %;
  2. **LFW domain-adapted** — LFW được xử lý cho khớp điều kiện camera thực tế của hệ thống;
  3. **Tập in-domain** — **5 – 7 người quen có đồng ý** (bạn cùng lớp/người quen), chụp bằng
     **chính camera của hệ thống**, dùng để kiểm chứng khoảng cách miền dữ liệu.
- ❌ **Không thu thập hình ảnh của người không được thông báo và không đồng ý** (hàng xóm, người
  qua đường qua camera an ninh) — trái với Nghị định 13/2023/NĐ-CP về dữ liệu cá nhân nhạy cảm
  và mâu thuẫn với luận điểm bảo vệ quyền riêng tư của chính đề tài.

---

## 4. Phạm vi nghiên cứu

### 4.1. Dữ liệu

- CSDL khuôn mặt tự thu thập của **2 – 3 người dùng đăng ký** (sinh viên thực hiện và thành viên
  gia đình), chụp trong **nhiều góc nhìn và điều kiện ánh sáng**, **≥ 100 ảnh/người**.
- Tập **người lạ** để đánh giá khả năng từ chối, ba nguồn:
  **≥ 100 danh tính LFW gốc** · **LFW domain-adapted** · **5 – 7 người quen có đồng ý**
  (≥ 20 ảnh/người, chụp bằng chính camera hệ thống). Nhóm 5 – 7 người này **không được đăng ký
  vào gallery**, chỉ dùng để đo FAR.
- Bộ dữ liệu kiểm thử giả mạo: **ảnh in** + **ảnh/video hiển thị trên màn hình điện thoại**.

> **Điều chỉnh phạm vi so với đề cương gốc (nộp 15/07/2026)**
> Đề cương gốc dự kiến 5 – 7 người dùng đăng ký. Phạm vi được điều chỉnh thành:
> **gallery 2 – 3 người** (sinh viên thực hiện + gia đình) vì hệ thống hướng tới **ứng dụng cá nhân
> trong hộ gia đình**; **5 – 7 người quen có đồng ý** được giữ lại nhưng chuyển vai trò thành
> **tập impostor in-domain** thay vì người dùng đăng ký.
>
> Cách bù đắp để giữ nguyên độ tin cậy của phép đo:
> - Tăng số ảnh mỗi người đăng ký từ 50 lên **≥ 100**;
> - Bổ sung **LFW (≥ 100 danh tính)** làm tập impostor chính — đủ cỡ mẫu để đo FAR ở mức 1 %;
> - Bổ sung bước **domain adaptation** cho LFW để thu hẹp khoảng cách với điều kiện camera thực tế;
> - Dùng **5 – 7 người in-domain** để **kiểm chứng** rằng FAR đo trên LFW đã adapt là đáng tin.
>
> Điều chỉnh này **phải được nêu rõ** trong Chương 4 (§4.2) và Chương 5 (Hạn chế) của báo cáo,
> và **cần thông báo với CBHD** trước khi triển khai.

### 4.2. Chức năng

- Nhận diện **một người trong khung hình chính**, khoảng cách **0,5 – 2 m**, điều kiện **ánh sáng trong nhà**.
- Điều khiển **2 nhóm thiết bị đại diện**: đèn (relay/GPIO), tivi (IR).
- Cảnh báo người lạ.
- Giám sát qua **mạng LAN/nội bộ**.

### 4.3. Quy trình triển khai

Ưu tiên phát triển + kiểm thử trên **môi trường giả lập** trước → triển khai lên **Raspberry Pi 5 thật**.
Tuỳ tiến độ thực tế, sản phẩm demo là **mô phỏng bằng LED** hoặc **lắp đặt thật trong một phòng**.

### 4.4. Giới hạn (ngoài phạm vi — KHÔNG làm)

- ❌ Không nhận diện đồng thời **nhiều người trong đám đông**.
- ❌ Không nhận diện qua **camera giám sát tầm xa**.
- ❌ **Không huấn luyện mô hình nhận diện từ đầu** — dùng pre-trained + đăng ký khuôn mặt bằng embedding.
- ⚠️ Điều khiển qua **MQTT là mục tiêu mở rộng, không bắt buộc**.

---

## 5. Phương pháp thực hiện

### 5.1. Phương pháp nghiên cứu tài liệu

- Kiến trúc và cách dùng **YOLOv8n-face** qua tài liệu chính thức Ultralytics.
- Các phương pháp trích xuất đặc trưng khuôn mặt: **dlib**, **ArcFace/MobileFaceNet**.
- Kỹ thuật **chống giả mạo khuôn mặt dựa trên học sâu**.
- Khảo sát nghiên cứu liên quan: nhận diện khuôn mặt trên thiết bị nhúng + hệ thống nhà thông minh.

### 5.2. Phương pháp thực nghiệm so sánh

- Cài đặt **2 pipeline nhận diện trên cùng phần cứng** Raspberry Pi 5.
- Xây dựng **kịch bản đo thống nhất**: cùng CSDL khuôn mặt, cùng điều kiện ánh sáng.
- Thu thập số liệu: **độ chính xác nhận diện, tỉ lệ nhận nhầm, FPS, độ trễ**.
- Thống kê, phân tích → **lựa chọn phương án triển khai chính thức**.
- Kiểm thử anti-spoofing với **ít nhất 2 hình thức tấn công** (ảnh in, màn hình điện thoại).

### 5.3. Phương pháp phân tích – thiết kế hệ thống

Kiến trúc tổng thể gồm **4 khối**:

```
┌──────────────────────────────────────────────────────────────────────┐
│ KHỐI 1 — THU NHẬN & XỬ LÝ ẢNH                                        │
│  Camera → Phát hiện khuôn mặt → Chống giả mạo → Nhận diện danh tính  │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ KHỐI 2 — QUYẾT ĐỊNH & PHÂN QUYỀN                                     │
│  Ánh xạ danh tính → quyền điều khiển thiết bị                        │
└───────────────┬──────────────────────────────┬───────────────────────┘
                ▼                              ▼
┌───────────────────────────────┐  ┌───────────────────────────────────┐
│ KHỐI 3 — CHẤP HÀNH            │  │ KHỐI 4 — GIÁM SÁT & CẢNH BÁO      │
│  GPIO/relay · IR · MQTT (mở   │  │  Web app (Flask) · Telegram bot · │
│  rộng)                        │  │  CSDL log                         │
└───────────────────────────────┘  └───────────────────────────────────┘
```

- Ngôn ngữ chính: **Python**.
- Web giám sát: **Flask** (gọn nhẹ). Giao diện **ReactJS là mục tiêu mở rộng**.
- Phát triển trên **Docker ARM64** trước khi lên thiết bị thật.

### 5.4. Phương pháp kiểm thử và đánh giá

- Kiểm thử **từng module** và **toàn hệ thống** theo 3 kịch bản: **người hợp lệ / người lạ / tấn công giả mạo**.
- Đo: **độ chính xác, FPS, độ trễ điều khiển** trong **ít nhất 2 điều kiện ánh sáng**.
- **Đo FAR trên ba tập impostor** (LFW gốc, LFW domain-adapted, in-domain 5–7 người) — do gallery
  chỉ 2–3 người, FAR là chỉ số phản ánh đúng năng lực từ chối người lạ, quan trọng hơn độ chính xác
  closed-set. Việc so sánh FAR giữa ba nguồn cho phép **định lượng ảnh hưởng của khoảng cách miền
  dữ liệu** — một nội dung bàn luận có giá trị của đề tài.
- Kịch bản "người lạ" kiểm chứng thực địa ở giai đoạn cuối được thực hiện **không lưu ảnh**,
  chỉ ghi nhận kết quả chấp nhận/từ chối.
- Tổng hợp thành **bảng benchmark**.

---

## 6. Kết quả mong đợi & tiêu chí nghiệm thu

### 6.1. Sản phẩm phần cứng

Hệ thống nhúng hoàn chỉnh trên Raspberry Pi 5, kết nối camera + module relay điều khiển đèn
(hoặc LED mô phỏng) + mạch phát IR điều khiển tivi, **hoạt động độc lập, tự khởi động cùng thiết bị**.

### 6.2. Sản phẩm phần mềm — chỉ tiêu định lượng

| Chỉ tiêu | Ngưỡng đạt |
|---|---|
| Độ chính xác nhận diện (người đã đăng ký) | **≥ 95 %** |
| **FAR trên tập impostor LFW** *(bổ sung)* | **≤ 1 %** |
| Tốc độ toàn pipeline | **≥ 5 FPS** |
| Độ trễ điều khiển thiết bị | **< 2 giây** |
| Tỉ lệ phát hiện tấn công giả mạo (ảnh in + màn hình ĐT) | **≥ 90 %** |
| Cảnh báo Telegram + web giám sát | Hoạt động ổn định trong mạng nội bộ |
| FPS riêng module phát hiện khuôn mặt (Tuần 2–3) | **≥ 10 FPS** trên Pi 5 |

> ⚠️ Các con số này là **chỉ tiêu cam kết trong đề cương**. Mọi báo cáo phải đối chiếu số đo thực tế
> với bảng này; nếu không đạt phải giải thích nguyên nhân và phương án khắc phục, **tuyệt đối không sửa số liệu**.

> ⚠️ **Lưu ý về chỉ tiêu độ chính xác khi gallery chỉ 2–3 người**
> Với gallery nhỏ, đạt độ chính xác ≥ 95 % là điều **dự kiến** và **không** phản ánh năng lực thật
> của hệ thống — phân biệt 3 danh tính đơn giản hơn nhiều so với hàng chục danh tính.
> Vì vậy nghiên cứu **bổ sung chỉ tiêu FAR ≤ 1 % trên tập impostor LFW** làm thước đo chính cho
> khả năng chống người lạ, và báo cáo phải **nêu FAR trước, accuracy sau**, kèm cảnh báo cỡ mẫu.

### 6.3. Giá trị khoa học

**Bảng số liệu so sánh thực nghiệm** các phương pháp nhận diện khuôn mặt trên Raspberry Pi 5 —
có giá trị tham khảo cho nghiên cứu và đồ án tương tự về edge AI.

### 6.4. Tài liệu

Một cuốn **báo cáo khoá luận đúng chuẩn (~50 trang)** kèm **toàn bộ mã nguồn** và **sơ đồ thiết kế phần cứng**.

---

## 7. Kế hoạch thực hiện

### 7.1. Phân công

**Trần Thanh Long – 25410088** thực hiện **toàn bộ** hạng mục: nghiên cứu tài liệu, thu thập dữ liệu,
xây dựng mô hình và pipeline AI, đấu nối phần cứng, lập trình điều khiển thiết bị, xây dựng web giám sát,
kiểm thử đánh giá và viết báo cáo.

### 7.2. Chiến lược giảm rủi ro

Do **chỉ có một thiết bị Raspberry Pi 5 và một người thực hiện**:

1. **Phát triển và kiểm thử phần mềm trên Docker ARM64** trước khi triển khai lên thiết bị thật.
2. **Ưu tiên chức năng cốt lõi** (nhận diện, chống giả mạo, điều khiển đèn/tivi) trước;
   chức năng mở rộng (**MQTT**) chỉ làm khi còn thời gian.
3. **Viết báo cáo song song** theo từng giai đoạn — không dồn vào cuối.

### 7.3. Bảng tiến độ dự kiến

| Tuần | Giai đoạn | Nhiệm vụ cụ thể | Kết quả cần đạt |
|---|---|---|---|
| **1** | Khởi động & Chuẩn bị | • Nghiên cứu tài liệu (YOLOv8n-face, các phương pháp nhận diện, anti-spoofing, GPIO/IR trên Pi 5). Hoàn thiện và nộp đề cương (15/07).<br>• Tạo GitHub repo; cài OS + môi trường Python trên Pi 5; setup Docker ARM64 trên máy cá nhân. | Đề cương hoàn chỉnh nộp đúng hạn. Môi trường phát triển sẵn sàng. |
| **2 – 3** | Dữ liệu & Phát hiện khuôn mặt | • Thu thập, chuẩn hoá CSDL khuôn mặt **2–3 người** (bản thân + gia đình), ≥ 100 ảnh/người, nhiều góc nhìn & ánh sáng; chuẩn bị tập impostor từ LFW; xây quy trình đăng ký người dùng mới.<br>• Cài YOLOv8n-face, export ONNX/NCNN, chạy detect realtime trên Pi 5, đo FPS. | CSDL khuôn mặt hoàn chỉnh. Phát hiện khuôn mặt **≥ 10 FPS** trên Pi 5. |
| **3 – 5** | Nhận diện & Chống giả mạo | • Cài & so sánh 2 phương pháp nhận diện (dlib vs. MobileFaceNet/ArcFace ONNX) theo độ chính xác, FPS, độ trễ → chọn tối ưu.<br>• Tích hợp MiniFASNet sau bước phát hiện; chuẩn bị bộ dữ liệu tấn công, kiểm thử & tinh chỉnh ngưỡng. | Bảng so sánh 2 phương pháp. Pipeline nhận diện + anti-spoofing chạy ổn định trên Pi 5. |
| **5 – 7** | Điều khiển thiết bị & Cảnh báo | • Đấu nối phần cứng, lập trình khối điều khiển: LED/relay qua GPIO, phát IR cho tivi; gán quyền theo danh tính.<br>• Cảnh báo người lạ: chụp ảnh, ghi log, gửi Telegram bot. | Điều khiển đèn/tivi thành công theo khuôn mặt. Cảnh báo người lạ hoạt động. |
| **7 – 8** | Web giám sát & Tích hợp | • Web giám sát Flask: trạng thái thiết bị, lịch sử nhận diện, ảnh cảnh báo, quản lý người dùng.<br>• Tích hợp toàn hệ thống, cấu hình tự khởi động (systemd), tối ưu hiệu năng, sửa lỗi. Nếu còn thời gian: MQTT. | Web giám sát hoạt động trong LAN. Hệ thống tích hợp hoàn chỉnh. |
| **8 – 10** | Kiểm thử, Báo cáo & Bảo vệ | • Kiểm thử tổng thể theo kịch bản (hợp lệ / người lạ / giả mạo) trong ≥ 2 điều kiện ánh sáng; đo FPS, độ chính xác, độ trễ; lập bảng benchmark.<br>• Viết báo cáo (~50 trang), đẩy mã nguồn lên GitHub, làm slide, quay video demo. Nộp báo cáo 23–24/09; bảo vệ 10/10. | Bảng benchmark. Báo cáo, slide, demo hoàn chỉnh nộp đúng hạn. |

### 7.4. Quy đổi tuần → ngày (mốc lịch cụ thể)

| Tuần | Từ ngày | Đến ngày |
|---|---|---|
| 1 | 15/07/2026 | 21/07/2026 |
| 2 | 22/07/2026 | 28/07/2026 |
| 3 | 29/07/2026 | 04/08/2026 |
| 4 | 05/08/2026 | 11/08/2026 |
| 5 | 12/08/2026 | 18/08/2026 |
| 6 | 19/08/2026 | 25/08/2026 |
| 7 | 26/08/2026 | 01/09/2026 |
| 8 | 02/09/2026 | 08/09/2026 |
| 9 | 09/09/2026 | 15/09/2026 |
| 10 | 16/09/2026 | 22/09/2026 |
| — | **Nộp báo cáo** | **23 – 24/09/2026** |
| — | **Bảo vệ Hội đồng** | **~10/10/2026** |

---

## 8. Cấu trúc báo cáo dự kiến (~50 trang)

| Chương | Nội dung | Số trang ước tính |
|---|---|---|
| Mở đầu | Lý do chọn đề tài, mục tiêu, phạm vi, cấu trúc báo cáo | 3 |
| **Chương 1** | Tổng quan đề tài & khảo sát công trình liên quan (nhận diện khuôn mặt trên edge, smart home) | 7 |
| **Chương 2** | Cơ sở lý thuyết: CNN, YOLOv8n-face, face embedding (ArcFace/MobileFaceNet, dlib), liveness detection, GPIO/IR/MQTT | 11 |
| **Chương 3** | Phân tích & thiết kế hệ thống: kiến trúc 4 khối, sơ đồ luồng dữ liệu, thiết kế CSDL, sơ đồ đấu nối phần cứng | 10 |
| **Chương 4** | Triển khai & thực nghiệm: môi trường Docker ARM64 → Pi 5, xây dựng CSDL và **ba tập impostor**, **domain adaptation & kiểm chứng**, kịch bản đo, **bảng benchmark so sánh 2 phương pháp**, kết quả anti-spoofing | 14 |
| **Chương 5** | Kết luận & hướng phát triển | 3 |
| Phụ lục | Tài liệu tham khảo, hướng dẫn cài đặt, sơ đồ mạch, mã nguồn tiêu biểu | 2 |

---

## 9. Rủi ro & phương án dự phòng

| Rủi ro | Mức độ | Phương án dự phòng |
|---|---|---|
| Chỉ có 1 Raspberry Pi 5 — hỏng phần cứng giữa chừng | Cao | Phát triển song song trên Docker ARM64; commit thường xuyên; backup image thẻ nhớ |
| Không đạt ≥ 5 FPS toàn pipeline | Trung bình | Giảm độ phân giải input, chạy detect cách frame (frame skipping), export NCNN, giảm tần suất anti-spoofing |
| Gallery chỉ 2–3 người → bài toán nhận diện "dễ", độ chính xác cao không phản ánh năng lực thật | **Cao** | Bắt buộc đo FAR trên tập impostor LFW (≥ 100 danh tính); nêu rõ hạn chế ở Ch.4 và Ch.5; không so sánh trực tiếp con số accuracy với các công trình dùng gallery lớn |
| Khoảng cách miền dữ liệu: LFW là ảnh web, khác điều kiện camera thực tế → FAR đo được lạc quan hơn thực tế | Trung bình | Bổ sung bước domain adaptation cho LFW; kiểm chứng bằng tập in-domain 5–7 người; báo cáo cả ba con số FAR để người đọc tự đánh giá |
| Không mời đủ 5–7 người cho tập in-domain | Thấp | Ưu tiên bạn cùng lớp (chỉ cần ~1 phút/người); tối thiểu chấp nhận 3 người, ghi rõ hạn chế cỡ mẫu |
| Thành viên gia đình không sẵn sàng chụp đủ số ảnh | Thấp | Chia nhiều buổi chụp; tối thiểu chấp nhận 2 người nếu người thứ 3 không tham gia được |
| Anti-spoofing < 90 % | Trung bình | Tinh chỉnh ngưỡng, bổ sung dữ liệu tấn công, kết hợp heuristic (kích thước bbox, moiré) |
| Không kịp làm MQTT | Thấp | Đã được đề cương xác định là **mở rộng, không bắt buộc** — bỏ qua, ghi rõ ở phần Hướng phát triển |
| Trễ tiến độ viết báo cáo | Cao | Viết song song từng giai đoạn theo quy trình trong `CLAUDE.md` (Cổng D của mỗi Phase) |

---

## 10. Tham chiếu

- Đề cương gốc: `docs/DC DATN Trần Thanh Long - 25410088 - ... .pdf`
- Đơn đăng ký đề tài: `docs/Don DKDA Trần Thanh Long - 25410088.docx`
- Quy trình làm việc & bộ quy tắc: [`../CLAUDE.md`](../CLAUDE.md)
