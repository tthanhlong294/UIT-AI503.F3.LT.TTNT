# Tuần 6 — 19/08 đến 25/08/2026

**Phase**: 2 — Phát hiện khuôn mặt · khép phần không phụ thuộc camera của Phase 1 · mở Phase 3

---

## Mục tiêu tuần

Hoàn thiện khối phát hiện khuôn mặt và công cụ đo hiệu năng, ghép thành mẻ tiền xử lý chạy được trên
dữ liệu thật, rồi mở Phase 3 — phần đóng góp chính của đồ án.

## Đã thực hiện

Bốn mã việc hoàn tất, sáu mục báo cáo, một notebook phân tích.

### 1. Mã việc `P2-02` — khối phát hiện khuôn mặt

Bọc mô hình ONNX thành một khối có giao diện rõ ràng: đưa vào một khung hình, trả về danh sách khuôn
mặt kèm khung bao, độ tin cậy và 5 điểm mốc.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 Trả lại — 1 lỗi cần sửa |
| Review vòng 2 | ✅ Đạt |

### 2. Mã việc `P2-03` — script đo hiệu năng

Đo theo ma trận cấu hình, mỗi ô 100 mẫu, ghi kết quả kèm tệp mô tả ngữ cảnh chạy.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 Trả lại — 1 lỗi chặn, 3 lỗi cần sửa |
| Review vòng 2 | ✅ Đạt |
| Vòng kiểm bổ sung trong container | ✅ Giữ nguyên phán quyết |

### 3. Mẻ đo đầu tiên — chạy trên máy phát triển

| Cấu hình | FPS trung bình | Độ lệch chuẩn | Độ trễ trung bình |
|---|---|---|---|
| 320 px, 4 luồng | 21,7 | 4,5 | 47,6 ms |
| 320 px, 2 luồng | 21,2 | 5,1 | 49,4 ms |
| 320 px, 1 luồng | 15,8 | 2,1 | 64,4 ms |
| 640 px, 2 luồng | 5,1 | 0,8 | 198,3 ms |
| 640 px, 4 luồng | 5,0 | 1,4 | 226,6 ms |
| 640 px, 1 luồng | 4,0 | 0,5 | 256,5 ms |

Nguồn: `results/bench_detect_20260819_1453.csv`, 100 mẫu mỗi cấu hình.

> ⚠️ **Đây không phải số của Raspberry Pi 5.** Tệp mô tả ngữ cảnh ghi rõ thiết bị là máy phát triển
> chạy Windows trên vi xử lý Intel x86-64. Chỉ tiêu cam kết ≥ 10 FPS là **đo trên Pi 5**, nên bảng
> trên chỉ dùng để kiểm tra script chạy đúng và để thấy xu hướng giữa các cấu hình, tuyệt đối không
> dùng làm căn cứ kết luận đạt hay không đạt. **Cổng C của Phase 2 vẫn đang mở.**

Xu hướng đọc được: tăng số luồng từ 1 lên 2 có tác dụng rõ, từ 2 lên 4 gần như không thêm gì. Kích
thước đầu vào là yếu tố quyết định — giảm từ 640 xuống 320 làm tốc độ tăng khoảng bốn lần.

### 4. Mã việc `P1-05` — mẻ tiền xử lý ảnh

Ghép khối phát hiện với khối căn chỉnh thành một mẻ chạy được trên cả bốn nguồn dữ liệu.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 Trả lại — 3 lỗi cần sửa |
| Review vòng 2 | ✅ Đạt |

Chạy thật trên 200 ảnh LFW: **198 ảnh xử lý thành công (99,00 %)**, 2 ảnh bị loại vì khuôn mặt quá
nhỏ. Đọc lại toàn bộ 198 tệp từ đĩa để kiểm: tất cả đúng kích thước 112×112, số tệp khớp số dòng
manifest, cây thư mục con phản chiếu đúng nguồn. Chạy lại với cùng seed chọn đúng cùng 200 ảnh.

**Một lỗi thuộc về bản đặc tả, tìm ra nhờ chạy trên dữ liệu thật.** Đặc tả viết: khi một ảnh có nhiều
khuôn mặt thì lấy khuôn mặt có độ tin cậy cao nhất. Chạy bộ phát hiện trên 49 ảnh có nhiều hơn một
khuôn mặt trong mẻ 200 thì thấy **5 ảnh bị ghi nhầm người**: một khuôn mặt ở hậu cảnh, bị cắt cụt, có
độ tin cậy nhỉnh hơn khuôn mặt chính đúng 0,001 đến 0,036, trong khi khuôn mặt chính lớn gấp 2–3 lần
về diện tích. Tỉ lệ 5/198 ≈ 2,5 %; ngoại suy lên toàn bộ 9 164 ảnh là khoảng 230 ảnh sai nhãn — đủ
làm lệch mọi con số đo về sau. Đã sửa đặc tả sang **chọn theo diện tích lớn nhất**; chạy lại mẻ 200
cho 198/198 dòng đúng.

### 5. Mã việc `P3-01` — khối nhận diện

Giao diện chung cho hai phương án nhận diện, cùng bản cài đặt phương án B dùng mô hình ArcFace.

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🟡 Đạt có điều kiện |
| Vòng kiểm bổ sung | 🟡 Giữ nguyên phán quyết |

Đây là mã việc đầu tiên **đạt ngay vòng đầu**, không phải trả lại lần nào.

Kiểm định gồm: 38 ca kiểm thử riêng cho khối này, 379 ca trên toàn bộ kho, 7/7 phép đột biến đều làm
đỏ đúng ca mà đặc tả yêu cầu, và một lượt chạy trong container ARM64 thật cho 28 ca chạy được, 10 ca
bỏ qua vì thiếu mô hình hoặc dữ liệu, không ca nào lỗi.

**Chốt cách chuẩn hoá đầu vào bằng thực nghiệm.** Tài liệu mô hình yêu cầu ghi lại cách chuẩn hoá
nhưng bản gốc không nói rõ. Chạy 60 danh tính LFW qua sáu phương án, so độ tương đồng trung bình giữa
các cặp cùng người và khác người:

| Chuẩn hoá | Cùng người | Khác người | Tách biệt |
|---|---|---|---|
| **RGB, `(x − 127,5)/128`** | 0,6088 | 0,0079 | **0,6010** |
| Thô, không chuẩn hoá | 0,9110 | 0,8754 | 0,0356 |

Nguồn: `models/README.md` §3.3. Khoảng cách giữa 0,6010 và 0,0356 đủ xa để kết luận dứt khoát. Con số
này quan trọng vì chọn sai cách chuẩn hoá **không gây lỗi** — mô hình vẫn chạy, vẫn trả vectơ đẹp,
chỉ có điều mọi khuôn mặt trông giống hệt nhau.

**Ba lỗ hổng tìm được khi dựng bộ cấu hình hỏng.** Người review tự dựng 60 biến thể cấu hình sai trên
sáu khoá. Mười bảy biến thể mà đặc tả liệt kê đích danh đều bị chặn đúng. Ba biến thể **không nằm
trong danh sách** thì lọt:

- Đặt hệ số chia bằng vô cùng thì mọi giá trị đầu vào thành 0. Đo thật trên 6 danh tính khác nhau:
  độ tương đồng giữa **những người khác nhau** ra đúng 1,0000 cho mọi cặp. Hệ thống trông hoàn hảo —
  vectơ chuẩn hoá đẹp, đăng ký trót lọt, nhận diện trả đúng người với điểm 1,0 — trong khi thực chất
  tỉ lệ chấp nhận sai là 100 %.
- Giá trị `nan` lọt qua mọi bộ lọc, vì phép so `nan <= 0` cho kết quả sai. Cả gallery có thể đăng ký
  thành vectơ `nan` mà không một dòng log nào cảnh báo.
- Kích thước ảnh đầu vào không được đối chiếu với đồ thị mô hình, khác với số chiều vectơ vốn có chốt
  này. Thay nhầm mô hình thì lỗi rò ra ngoài dưới dạng ngoại lệ nội bộ của thư viện suy luận.

Cả ba là **khiếm khuyết của bản đặc tả**, không phải của bản cài đặt. Đã bổ sung hai trong ba vào đặc
tả; phần vá mã nguồn để thành mã việc riêng.

### 6. Báo cáo

- **Chương 2** — viết xong 5 mục: mạng nơ-ron tích chập, mô hình phát hiện khuôn mặt, trích xuất đặc
  trưng, học đo lường và độ tương đồng cosin, suy luận trên thiết bị biên. Chương 2 nay xong 6/7 mục.
  Mục còn lại nói về nền tảng phần cứng, chưa viết được vì chưa có thiết bị; lý do và điều kiện gỡ
  chặn đã ghi ngay trong tệp.
- **Chương 3** — viết xong mục kiến trúc bốn khối.

### 7. Notebook phân tích hiệu năng

`notebooks/02_phan_tich_hieu_nang_detect.ipynb` — 17 ô, 4 biểu đồ, đọc số từ `results/`, không tự
sinh số liệu nào.

### 8. Dọn dẹp cuối tuần (25/08)

- Sửa thông điệp commit của `P3-01` cho đúng quy ước; gộp biên bản review vào cùng commit với mã
  nguồn, theo đúng tiền lệ của các mã việc trước
- Gộp nhánh `P3-01` vào `dev` và đẩy lên máy chủ — trước đó 7 commit chỉ nằm trên một ổ đĩa
- Sửa nốt chỗ đặc tả `P3-01` mà biên bản review đã chỉ ra

## Số liệu

| Hạng mục | Giá trị | Nguồn |
|---|---|---|
| Số mã việc hoàn tất | **4** | `docs/review/` |
| Số vòng sửa trung bình | 0,75 | 1 vòng cho `P2-02`, `P2-03`, `P1-05`; 0 vòng cho `P3-01` |
| Ca kiểm thử toàn kho | **379 passed** | biên bản `P3-01` |
| Ảnh xử lý thành công trong mẻ thử | 198/200 = **99,00 %** | `data/processed/lfw_original/manifest.csv` |
| Độ tách biệt của mô hình nhận diện | **0,6010** | `models/README.md` §3.3 |
| Mục báo cáo viết trong tuần | 6 | `report/chapters/` |

## Vướng mắc

- **Vẫn chưa có Raspberry Pi 5 và camera.** Đã sang tuần thứ ba kể từ khi vướng mắc này được ghi lần
  đầu. Hệ quả cụ thể tính đến hôm nay: Phase 2 không đóng được cổng C vì số đo đang có là của máy
  phát triển; Phase 1 còn chín bước đứng; Phase 4 chưa mở được vì chưa có bộ ảnh giả mạo.
- **Ba Phase đang mở song song** — Phase 1, 2 và 3 đều dở dang. Quy tắc gốc là chưa qua cổng D thì
  không mở Phase sau; ở đây phải phá quy tắc đó vì mọi thứ chặn đều chặn ở cùng một chỗ là phần cứng.
- **Còn 4 tuần tới hạn nộp 23–24/09.** Phase 4, 5, 6, 7 chưa bắt đầu, trong khi kế hoạch gốc dành hai
  tuần cuối cho riêng việc viết báo cáo và làm slide.

## Kế hoạch tuần sau

- Vá ba lỗ hổng cấu hình của khối nhận diện thành một mã việc nhỏ
- Viết phương án nhận diện thứ hai và script đăng ký, quét ngưỡng, dựng đường cong ROC — phần lớn
  việc này chạy được trên LFW, không cần camera
- Làm trước phần không phụ thuộc phần cứng của khối chấp hành và khối giám sát
- Quyết định về phần cứng: mua bo mạch, hoặc tách camera ra mua riêng để mở khoá phần thu thập dữ liệu

---

*Nguồn: lịch sử git từ `6ff0111` đến `ff27b6b`; biên bản trong `docs/review/` của các mã việc
`P2-02`, `P2-03`, `P1-05`, `P3-01`; `results/bench_detect_20260819_1453.csv` và tệp mô tả đi kèm.*
