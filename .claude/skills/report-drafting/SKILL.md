---
name: report-drafting
description: Hướng dẫn soạn thảo từng chương báo cáo khoá luận tốt nghiệp — dàn ý chi tiết, checklist nội dung bắt buộc, ngân sách trang, cách chèn số liệu có trích nguồn, và mẫu câu học thuật tiếng Việt. Dùng khi bắt đầu viết hoặc mở rộng bất kỳ chương nào trong report/.
---

# Skill: Soạn thảo báo cáo khoá luận (Report Drafting)

Dùng cho báo cáo ~50 trang của đề tài "Nhận diện khuôn mặt trên Raspberry Pi 5 ứng dụng
điều khiển thiết bị trong nhà thông minh". **Viết bằng tiếng Việt học thuật.**

---

## Ngân sách trang (bám sát để không phình/thiếu)

| Phần | Trang | Tích luỹ |
|---|---|---|
| Trang bìa, lời cảm ơn, mục lục, danh mục hình/bảng/từ viết tắt | (không tính) | — |
| Mở đầu | 3 | 3 |
| Chương 1 — Tổng quan | 7 | 10 |
| Chương 2 — Cơ sở lý thuyết | 11 | 21 |
| Chương 3 — Phân tích & Thiết kế | 10 | 31 |
| Chương 4 — Triển khai & Thực nghiệm ⭐ | 14 | 45 |
| Chương 5 — Kết luận | 3 | 48 |
| Tài liệu tham khảo + Phụ lục | 2 | 50 |

> Chương 4 là **trái tim** của đồ án (đóng góp khoa học). Nếu phải cắt trang, cắt Chương 1 và 2 trước.

---

## Dàn ý chi tiết từng phần

### MỞ ĐẦU (3 trang)

1. **Lý do chọn đề tài** — bối cảnh nhà thông minh phát triển; nhu cầu xác thực người dùng
   không tiếp xúc; hạn chế của giải pháp cloud (độ trễ, phụ thuộc mạng, **rủi ro quyền riêng tư
   với dữ liệu sinh trắc học**); xu hướng edge AI; Raspberry Pi 5 đủ mạnh cho suy luận cục bộ.
2. **Mục tiêu đề tài** — nêu lại mục tiêu tổng quát + 6 mục tiêu cụ thể (bảng §2.2 đề cương).
3. **Đối tượng và phạm vi** — tóm tắt, **nêu rõ giới hạn** (không đám mông, không train from scratch,
   MQTT là mở rộng).
4. **Phương pháp nghiên cứu** — 4 phương pháp: nghiên cứu tài liệu, thực nghiệm so sánh,
   phân tích–thiết kế hệ thống, kiểm thử & đánh giá.
5. **Bố cục báo cáo** — 1 đoạn tóm tắt 5 chương.

### CHƯƠNG 1 — TỔNG QUAN (8 trang)

| Mục | Nội dung | Trang |
|---|---|---|
| 1.1 | Tổng quan về hệ thống nhà thông minh và bài toán xác thực người dùng | 2 |
| 1.2 | Tổng quan nhận diện khuôn mặt: từ phương pháp truyền thống (Eigenface, LBP) đến học sâu | 2 |
| 1.3 | **Khảo sát công trình liên quan** — bảng so sánh ≥ 6 công trình: nền tảng phần cứng, mô hình, độ chính xác, FPS, có anti-spoofing không, có điều khiển thiết bị không | 2,5 |
| 1.4 | Thách thức khi triển khai trên thiết bị nhúng: tài nguyên hạn chế, nhiệt độ/throttling, đánh đổi tốc độ–độ chính xác, tấn công giả mạo | 1 |
| 1.5 | **Đóng góp của đồ án** — 3 gạch đầu dòng, nêu rõ điểm khác biệt: so sánh thực nghiệm 2 phương án trên cùng phần cứng Pi 5 | 0,5 |

**Bảng 1.x bắt buộc** — Khảo sát công trình liên quan:

| Công trình | Năm | Phần cứng | Mô hình nhận diện | Độ chính xác | FPS | Anti-spoofing | Điều khiển TB |
|---|---|---|---|---|---|---|---|
| [ref] | | | | | | | |

Kết đoạn: chỉ ra **khoảng trống** mà đồ án lấp — chưa có công trình nào so sánh trực tiếp
dlib vs ArcFace trên Raspberry Pi 5 kèm anti-spoofing và điều khiển thiết bị thật.

### CHƯƠNG 2 — CƠ SỞ LÝ THUYẾT (12 trang)

| Mục | Nội dung | Trang |
|---|---|---|
| 2.1 | Mạng nơ-ron tích chập (CNN): convolution, pooling, batch norm, activation | 2 |
| 2.2 | **Phát hiện đối tượng và YOLOv8**: kiến trúc backbone–neck–head, anchor-free, NMS; biến thể **YOLOv8n-face** (thêm 5 landmark) | 2,5 |
| 2.3 | **Trích xuất đặc trưng khuôn mặt (face embedding)**: ý tưởng ánh xạ ảnh → vector; hàm mất mát **ArcFace** (additive angular margin) kèm công thức; **MobileFaceNet** (depthwise separable conv, global depthwise conv); **dlib/ResNet-29** với triplet loss | 3,5 |
| 2.4 | **So khớp danh tính**: cosine similarity, khoảng cách Euclid, ngưỡng quyết định, FAR/FRR/EER, bài toán closed-set vs **open-set** | 1,5 |
| 2.5 | **Chống giả mạo khuôn mặt**: phân loại tấn công (print, replay, mask); phương pháp texture-based / depth-based / rPPG; **MiniFASNet** và Silent Face Anti-Spoofing; chỉ số **APCER/BPCER/ACER** (ISO/IEC 30107-3) | 2 |
| 2.6 | **Nền tảng triển khai**: Raspberry Pi 5 (BCM2712, Cortex-A76), ONNX Runtime & NCNN trên ARM, lượng tử hoá; GPIO & relay; giao thức hồng ngoại NEC; MQTT | 2,5 |

Công thức phải đánh số và được dẫn trong thân bài. Ví dụ ArcFace:

$$L = -\frac{1}{N}\sum_{i=1}^{N}\log\frac{e^{s(\cos(\theta_{y_i}+m))}}{e^{s(\cos(\theta_{y_i}+m))}+\sum_{j\neq y_i}e^{s\cos\theta_j}} \tag{2.3}$$

### CHƯƠNG 3 — PHÂN TÍCH & THIẾT KẾ (10 trang)

| Mục | Nội dung | Trang |
|---|---|---|
| 3.1 | Phân tích yêu cầu: **chức năng** (nhận diện, chống giả mạo, điều khiển, cảnh báo, giám sát) và **phi chức năng** (5 chỉ tiêu định lượng, hoạt động offline, tự khởi động) | 1,5 |
| 3.2 | **Kiến trúc tổng thể 4 khối** — Hình 3.1 (TikZ), mô tả trách nhiệm từng khối và giao diện giữa các khối | 2 |
| 3.3 | Thiết kế khối 1 — thu nhận & xử lý ảnh: sơ đồ luồng `capture → detect → antispoof → align → embed → match`; giải thích **vì sao anti-spoofing đặt trước nhận diện** | 2 |
| 3.4 | Thiết kế khối 2 — quyết định & phân quyền: bảng ánh xạ `user_id → thiết bị → hành động`; cơ chế **N frame liên tiếp** và **cooldown** chống nhiễu | 1,5 |
| 3.5 | Thiết kế khối 3 — chấp hành: sơ đồ đấu nối GPIO (Hình 3.x), bảng chân, mạch phát IR, lớp trừu tượng hoá phần cứng có backend mock | 1,5 |
| 3.6 | Thiết kế khối 4 — giám sát: **lược đồ CSDL** (`users`, `recognition_log`, `alerts`, `device_state`), luồng cảnh báo Telegram, các màn hình web | 1 |
| 3.7 | Thiết kế bảo mật & quyền riêng tư: xử lý cục bộ, không truyền ảnh ra ngoài, xác thực trang quản trị, quản lý secret qua biến môi trường | 0,5 |

### CHƯƠNG 4 — TRIỂN KHAI & THỰC NGHIỆM ⭐ (14 trang)

**Đây là chương có giá trị khoa học cao nhất. Mọi số liệu phải từ `results/`.**

| Mục | Nội dung | Trang |
|---|---|---|
| 4.1 | Môi trường triển khai: cấu hình Pi 5, OS, phiên bản thư viện (bảng), môi trường Docker ARM64, quy trình dev→deploy | 1 |
| 4.2 | **Xây dựng CSDL khuôn mặt**: quy trình thu thập, **gallery 2–3 người + lý do điều chỉnh phạm vi**, số ảnh, phân bố điều kiện (Hình 4.1), tiền xử lý (crop/align 112×112), QC, cách chia tập, **ba tập impostor (LFW gốc / adapted / in-domain 5–7 người)**, **vấn đề đạo đức & đồng ý** | 2 |
| 4.2b | **Domain adaptation cho tập impostor** ⭐: đo đặc trưng miền dữ liệu thật, các bước biến đổi áp dụng lên LFW, **kiểm chứng bằng phân bố và Wasserstein distance** (Hình `fig_domain_adaptation`) | 1 |
| 4.3 | Xây dựng bộ dữ liệu tấn công giả mạo: ảnh in (khổ, chất liệu, khoảng cách), màn hình điện thoại (model, độ sáng), số mẫu mỗi loại | 0,5 |
| 4.4 | **Kịch bản đo thống nhất**: mô tả điều kiện chuẩn hoá, số lần lặp, cách đo FPS/latency, quy trình warm-up — *phần này quyết định tính khoa học của toàn chương* | 1 |
| 4.5 | Kết quả phát hiện khuôn mặt: bảng ma trận 12 cấu hình, Hình so sánh FPS, kết luận chọn cấu hình | 1,5 |
| 4.6 | **So sánh thực nghiệm hai phương án nhận diện** ⭐⭐ — bảng chỉ số đầy đủ, **FAR trên tập impostor LFW (nêu trước accuracy)**, ROC, FAR/FRR, ma trận nhầm lẫn, phân tích đánh đổi, **kết luận chọn phương án kèm lý do định lượng**, **cảnh báo cỡ mẫu** | 3 |
| 4.7 | Kết quả chống giả mạo: APCER/BPCER/ACER tách riêng ảnh in và màn hình, chọn ngưỡng, chi phí FPS | 1,5 |
| 4.8 | Kết quả điều khiển thiết bị: độ trễ end-to-end phân rã theo khâu (Hình), kiểm chứng phân quyền | 1 |
| 4.9 | Kiểm thử tổng thể & benchmark tổng hợp: 3 kịch bản × 2 ánh sáng × 3 khoảng cách, thử nghiệm ổn định 2 giờ, **bảng đối chiếu 5 chỉ tiêu** | 1,5 |
| 4.10 | Bàn luận: nút thắt hiệu năng, các bước tối ưu đã áp dụng và mức cải thiện, so sánh với công trình liên quan ở Chương 1 | 0,5 |

### CHƯƠNG 5 — KẾT LUẬN (3 trang)

1. **Kết quả đạt được** — bảng đối chiếu 5 chỉ tiêu cam kết (Đạt/Không đạt + số thật).
2. **Đóng góp** — nhắc lại 3 đóng góp, nhấn mạnh bảng số liệu so sánh có giá trị tham khảo cho edge AI.
3. **Hạn chế** — trung thực: **gallery chỉ 2–3 người** nên accuracy không khái quát hoá được cho
   hệ thống nhiều người dùng; chưa đánh giá suy giảm độ chính xác khi gallery mở rộng;
   chỉ 1 người trong khung hình; chưa test tấn công mask 3D; chưa test ngoài trời; chưa đánh giá dài hạn.
4. **Hướng phát triển** — MQTT/Home Assistant, giao diện ReactJS, nhận diện đa người,
   camera IR cho điều kiện thiếu sáng, tăng tốc bằng Hailo AI HAT, cập nhật gallery trực tuyến.

---

## Quy trình viết một mục (áp dụng mọi lần)

1. **Xác định nguồn dữ liệu**: mục này cần số liệu từ file nào trong `results/`? Cần code nào trong `src/`?
   → Nếu chưa có, **dừng lại và báo**, không viết chay.
2. **Lập dàn ý** 3–5 ý chính. Mục dài > 2 trang thì trình dàn ý trước khi viết.
3. **Viết theo trình tự**: câu dẫn nhập → nội dung → bảng/hình → nhận xét → câu chuyển tiếp.
4. **Chèn số liệu** kèm trích nguồn.
5. **Tự kiểm** bằng checklist skill `academic-editing`.

---

## Mẫu câu học thuật tiếng Việt

**Dẫn nhập mục:**
> "Mục này trình bày quá trình xây dựng cơ sở dữ liệu khuôn mặt phục vụ huấn luyện và đánh giá hệ thống."

**Giới thiệu bảng/hình:**
> "Bảng 4.6 tổng hợp kết quả so sánh hai phương án nhận diện trên cùng điều kiện thực nghiệm."
> "Hình 4.7 biểu diễn đường cong ROC của hai phương án."

**Nhận xét kết quả:**
> "Kết quả cho thấy phương án MobileFaceNet đạt độ chính xác 96,8 %, cao hơn 2,7 điểm phần trăm
> so với phương án dlib, đồng thời độ trễ suy luận giảm 57 % (từ 42,7 ms xuống 18,4 ms)."

**Giải thích nguyên nhân:**
> "Sự chênh lệch này xuất phát từ việc MobileFaceNet sử dụng tích chập tách biệt theo chiều sâu
> (depthwise separable convolution), giúp giảm đáng kể số phép nhân–cộng so với kiến trúc
> ResNet-29 của dlib [12]."

**Thừa nhận hạn chế:**
> "Cần lưu ý rằng kết quả này được đo trên cơ sở dữ liệu quy mô nhỏ gồm 3 người dùng đăng ký,
> phù hợp với định vị ứng dụng cá nhân trong hộ gia đình, song chưa thể khái quát hoá cho các
> hệ thống có số lượng người dùng đăng ký lớn hơn."

**Chuyển tiếp:**
> "Trên cơ sở phương án đã lựa chọn, mục tiếp theo trình bày quá trình tích hợp module chống giả mạo."

---

## Lỗi thường gặp cần tránh

| Lỗi | Sửa thành |
|---|---|
| "Em đã cài đặt hệ thống…" | "Hệ thống được cài đặt…" |
| "Kết quả rất tốt" | "Độ chính xác đạt 96,8 %, vượt chỉ tiêu 95 %" |
| Bảng xuất hiện không có câu dẫn | Thêm "Bảng 4.3 trình bày…" trước bảng |
| Chương 2 chép lại tài liệu không trích dẫn | Diễn đạt lại + trích `[n]` |
| Chương 4 thiếu mô tả điều kiện đo | Bổ sung mục 4.4 kịch bản đo thống nhất |
| Kết luận nêu chỉ tiêu chung chung | Bảng đối chiếu 5 chỉ tiêu với số cụ thể |
| Copy hình từ internet | Vẽ lại bằng TikZ/matplotlib, hoặc trích nguồn rõ ràng |
