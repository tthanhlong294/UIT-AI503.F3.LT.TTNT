# Tuần 5 — 12/08 đến 18/08/2026

**Phase**: 1 — Dữ liệu khuôn mặt · bắt đầu Phase 2 — Phát hiện khuôn mặt

---

## Mục tiêu tuần

Dựng xong phần dữ liệu không phụ thuộc camera: quy ước đặt tên, script thu thập ảnh, tập đối chứng
quy mô lớn và khối căn chỉnh khuôn mặt. Sau đó mở Phase 2 bằng việc chuyển đổi mô hình phát hiện.

## Đã thực hiện

Năm mã việc hoàn tất trong tuần, nhiều nhất từ đầu đồ án.

### 1. Bước 1.1 — quy ước dữ liệu

Chốt cách đặt tên và tổ chức thư mục cho cả bốn nguồn ảnh: gallery người nhà, LFW gốc, LFW đã xử lý
cho khớp camera, và nhóm người quen chụp bằng chính camera hệ thống. Quy ước này phải có trước script
thu thập, nếu không mỗi nguồn sẽ đặt tên một kiểu và bước chia tập về sau không ghép lại được.

### 2. Mã việc `P1-01` — khối thu hình

Lớp trừu tượng cho camera, kèm hai bản cài đặt: một bản giả để chạy trên máy không có camera, một bản
thật dùng OpenCV. Đây là điều kiện để mọi thứ phía sau chạy được khi chưa có phần cứng.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 Trả lại |
| Review vòng 2 | 🔴 Trả lại |
| Review vòng 3 | 🟡 Đạt có điều kiện |

### 3. Mã việc `P1-02` — script thu thập ảnh

Chụp có hướng dẫn từng tư thế, đếm đủ số ảnh cho mỗi điều kiện góc và ánh sáng, ghi manifest.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 Trả lại |
| Review vòng 2 | 🔴 Trả lại — còn một lỗi, sửa ba dòng trong tệp kiểm thử |
| Review vòng 3 | ✅ Đạt |

### 4. Mã việc `P1-03` — tải bộ dữ liệu đối chứng

Tải LFW, xác thực bằng mã băm, lọc lấy các danh tính có từ hai ảnh trở lên.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 Trả lại |
| Review vòng 2 | 🔴 Trả lại |
| Review vòng 3 | ✅ Đạt |

Hai điều chỉnh phát sinh trong lúc làm, cả hai đã ghi vào `docs/dieu-chinh-pham-vi.md`:

- **Máy chủ gốc của bộ dữ liệu đã ngừng hoạt động** — tra DNS công cộng trả về không tìm thấy tên
  miền. Chuyển sang một địa chỉ thay thế, lấy từ mã nguồn của thư viện `scikit-learn`. Mã băm SHA256
  khớp với bản UMass từng phát hành, nên tệp đúng là bản gốc chứ không phải bản chép lại đã sửa.
- **Nâng số danh tính lấy về từ 100 lên toàn bộ phần đủ điều kiện.** Đề cương chỉ yêu cầu tối thiểu
  100 danh tính, tương ứng 384 ảnh; sau khi chia đôi val/test còn 192 phép thử ở nửa test. Với cỡ mẫu
  đó, ngay cả khi không có mẫu nào bị chấp nhận sai thì cận trên khoảng tin cậy 95 % của tỉ lệ chấp
  nhận sai vẫn là 1,56 % — không đủ để kết luận đạt mức 1 % như bước 3.7c đòi hỏi. Lấy hết thì cận
  trên xuống 0,07 %. Tập đối chứng không bao giờ được đưa vào gallery nên tăng số danh tính không
  đánh đổi gì về mặt phương pháp.

### 5. Mã việc `P1-04` — căn chỉnh khuôn mặt

Đưa khuôn mặt về khung 112×112 bằng phép biến đổi tương tự dựa trên 5 điểm mốc.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 Trả lại — 2 lỗi chặn, 1 lỗi cần sửa |
| Review vòng 2 | 🔴 Trả lại — còn 1 lỗi cần sửa |
| Review vòng 3 | ✅ Đạt |

**Một lỗi thuộc về bản đặc tả.** Đặc tả đưa ra bốn phép kiểm hình học để bắt lỗi hoán vị điểm mốc,
nhưng bốn phép đó có thể cùng đúng với một bộ điểm mốc nằm thẳng hàng theo đường chéo. Đã bổ sung
phép kiểm thứ năm: độ lệch của điểm mũi so với đường nối hai mắt.

### 6. Mã việc `P2-01` — chuyển đổi mô hình phát hiện sang ONNX

Xuất mô hình ở hai kích thước đầu vào 320 và 640.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 Trả lại — 1 lỗi chặn, 3 lỗi cần sửa |
| Review vòng 2 | ✅ Đạt |

Kiểm chứng bản chuyển đổi cho kết quả giống hệt bản gốc: trên 50 ảnh với 100 phép so sánh, số khuôn
mặt phát hiện khớp 100/100, độ chồng lấn khung bao trung bình 0,999999, sai số vị trí điểm mốc lớn
nhất 6,1 × 10⁻⁵ điểm ảnh. Tức là bước chuyển đổi không làm mất độ chính xác.

### 7. Điều chỉnh quy trình làm việc

- **Chuyển vai cài đặt mã nguồn sang một tác tử chạy cùng môi trường** thay vì công cụ ngoài. Bỏ được
  khâu chép lệnh thủ công mỗi vòng bàn giao, vốn đã lặp 11 lần. Ba nguyên tắc giữ nguyên: người kiểm
  định làm việc trong phiên riêng với ngữ cảnh sạch, không có quyền sửa mã, và mọi bàn giao vẫn đi qua
  tệp trong repo. Đổi lại rủi ro hai vai cùng mắc một điểm mù tăng lên, nên bù bằng việc bắt buộc
  kiểm bằng phép đột biến ở mỗi lượt review.
- **Bổ sung kiểm bằng phép đột biến vào chuẩn review.** Cách làm: cố ý phá một chỗ trong mã nguồn rồi
  chạy lại bộ kiểm thử, xem có ca nào đỏ đúng chỗ đã phá không. Ca kiểm thử xanh mà không đỏ khi mã bị
  phá thì nó không canh gì cả.
- Thêm hai quy tắc vào khung viết đặc tả, đều rút từ lỗi thật gặp trong tuần.

## Số liệu

| Hạng mục | Giá trị | Nguồn |
|---|---|---|
| Số mã việc hoàn tất | **5** | `docs/review/` |
| Số vòng sửa trung bình | 1,8 | 2 vòng cho `P1-01` đến `P1-04`, 1 vòng cho `P2-01` |
| Danh tính trong tập đối chứng | **1 680** | `data/impostor/lfw_original/manifest.csv` |
| Ảnh trong tập đối chứng | **9 164** | như trên |
| Ảnh kiểm chứng bản ONNX | 50 ảnh / 100 phép so sánh | `results/export_detector_20260818_1140.json` |
| Độ chồng lấn khung bao, ONNX so với bản gốc | **0,999999** trung bình | như trên |
| Sai số điểm mốc lớn nhất | 6,1 × 10⁻⁵ điểm ảnh | như trên |

## Vướng mắc

- **Vẫn chưa có Raspberry Pi 5 và camera.** Chín bước của Phase 1 phụ thuộc camera vẫn đứng: thu thập
  ảnh người nhà, mời nhóm người quen chụp đối chứng, đo đặc trưng miền dữ liệu, xử lý LFW cho khớp
  camera thật, kiểm chất lượng, chia tập, thu bộ ảnh giả mạo và phân tích thống kê.
- Phase 1 chưa đóng được cổng D nhưng đã phải mở Phase 2. Lý do và cách xử lý đã ghi vào
  `docs/dieu-chinh-pham-vi.md`: chờ cổng D là dừng vô thời hạn, mà bước tiền xử lý ảnh của Phase 1
  lại cần bộ phát hiện khuôn mặt của Phase 2 mới chạy được — thứ tự phụ thuộc thực tế ngược với thứ
  tự đánh số.

## Kế hoạch tuần sau

- Viết khối phát hiện khuôn mặt và script đo hiệu năng, chạy thử mẻ đo trên máy phát triển
- Ghép bộ phát hiện với khối căn chỉnh thành một mẻ tiền xử lý hoàn chỉnh
- Viết tiếp phần cơ sở lý thuyết của báo cáo
- Mở Phase 3 bằng khối nhận diện

---

*Nguồn: lịch sử git từ `cffe520` đến `0d2a303`; biên bản trong `docs/review/` của các mã việc
`P1-01`, `P1-02`, `P1-03`, `P1-04`, `P2-01`.*
