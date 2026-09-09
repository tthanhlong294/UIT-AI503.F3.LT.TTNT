# Chương 4 — Triển khai và Thực nghiệm

> **Đây là khung chương, chưa phải bản thảo hoàn chỉnh.** Mục nào còn `[CHƯA ĐO]` là mục chưa có số
> liệu thật; theo quy tắc R5 của đồ án, không viết câu nào chứa số liệu chưa đo được.
>
> Quy ước trích nguồn: mọi bảng và hình đều ghi tệp nguồn trong `results/` hoặc `notebooks/`. Một
> con số không truy được về tệp là một con số không được phép xuất hiện ở đây (R6).

---

## 4.1. Môi trường thực nghiệm và quy ước đo

### 4.1.1. Ba môi trường và vai trò của từng môi trường

Nghiên cứu này chạy trên ba môi trường khác nhau, và **không** trộn lẫn số liệu giữa chúng:

| Mã | Môi trường | Vai trò | Số hiệu năng dùng được |
|---|---|---|---|
| `pc_x86` | Máy phát triển Windows, bộ xử lý Intel x86-64 | Phát triển mã, kiểm chứng quy trình đo | Có, nhưng **không phải phần cứng đích** |
| `docker_arm64` | Container ARM64 chạy qua lớp giả lập QEMU | Kiểm tính đúng đắn của mã trên kiến trúc ARM | **Không** — thời gian không quy đổi được |
| `pi5` | Raspberry Pi 5 8 GB | **Đo chính thức** | **Có** — số kết luận chỉ tiêu |

Cột cuối cùng là ràng buộc phương pháp quan trọng nhất của chương này. Container ARM64 chạy trên
lớp giả lập, nên thời gian đo được ở đó không phản ánh tốc độ của phần cứng thật: cùng một bộ kiểm
thử, cùng kiến trúc, cùng ảnh máy ảo, nghiên cứu đo được 16,21 giây ở lần chạy nguội và 2,22 giây ở
lần chạy ấm — chênh hơn bảy lần chỉ do trạng thái bộ nhớ đệm của máy chủ. Vì vậy container chỉ dùng
để trả lời câu hỏi *"mã có chạy đúng trên ARM64 không"*, không bao giờ dùng để trả lời *"chạy nhanh
bao nhiêu"*.

Mỗi tệp kết quả trong `results/` mang một trường `moi_truong` nhận đúng một trong ba mã trên, để
việc gộp số liệu từ nhiều máy không thể nhầm lẫn.

### 4.1.2. Điều kiện bảo đảm khả năng tái lập

Mỗi lượt đo sinh ra hai tệp: tệp `.csv` chứa số đo thô của từng khung hình, và tệp `.meta.json` ghi
ngữ cảnh. Tệp ngữ cảnh gồm mã commit của mã nguồn tại thời điểm đo, phiên bản từng thư viện suy
luận, cấu hình đã dùng, hạt giống sinh số ngẫu nhiên, số khung làm nóng, và nhiệt độ bộ xử lý.

Hai điều kiện được kiểm tự động trước khi số liệu được đưa vào chương này:

1. **Mã nguồn sinh ra số đo phải đã được lưu vào lịch sử phiên bản.** Số đo từ mã còn sửa đổi chưa
   lưu không dựng lại được, nên không dùng để kết luận.
2. **Các lượt cùng một phép so sánh phải chạy trên cùng một phiên bản mã** và cùng một hạt giống
   chọn ảnh, để khác biệt quan sát được không đến từ việc đổi đầu vào.

*Nguồn: `notebooks/02_phan_tich_hieu_nang_detect.ipynb` mục 1.*

### 4.1.3. Số lượt đo và cách báo cáo

Mỗi cấu hình đo trên 100 khung hình liên tiếp, sau 10 khung làm nóng không tính vào kết quả. Kết quả
báo cáo dưới dạng giá trị trung bình kèm mức dao động, không lấy giá trị tốt nhất của một lần chạy.

Ngoài ra, mỗi phép so sánh được **lặp lại nhiều lượt** ở những thời điểm khác nhau. Lý do trình bày
ở §4.3.3: mức dao động giữa các lượt trên máy phát triển lớn tới mức một lượt đo đơn lẻ không đủ để
xếp hạng hai phương án.

---

## 4.2. Xây dựng cơ sở dữ liệu khuôn mặt

`[CHƯA ĐO]` — chặn vì chưa có camera của hệ thống.

Dàn ý: quy ước đặt tên và tổ chức thư mục · thu thập ảnh 2–3 người trong gia đình · ba tập impostor
và vai trò từng tập · quy trình hiệu chỉnh miền dữ liệu và kết luận kiểm chứng · thống kê phân bố
sau tiền xử lý.

Phần đã hoàn thành và có thể trình bày ngay: tập impostor quy mô lớn lấy từ bộ dữ liệu LFW, gồm
1 680 danh tính và 9 164 ảnh. *Nguồn: `configs/data.yaml`, `data/impostor/lfw_original/manifest.csv`.*

---

## 4.3. Kết quả khối phát hiện khuôn mặt

### 4.3.1. Kiểm chứng chuyển đổi mô hình

Mô hình YOLOv8n-face được huấn luyện ở định dạng PyTorch, nhưng thiết bị đích không cài PyTorch
(§2.6.1). Mô hình vì thế phải qua chuyển đổi, và mỗi phép chuyển đổi là một chỗ có thể làm sai lệch
kết quả mà vẫn cho ra tệp chạy được. Nghiên cứu này không chấp nhận bản chuyển đổi cho tới khi
kiểm chứng bằng số đo.

Phương pháp: chạy bản gốc và bản chuyển đổi trên **cùng một tập ảnh**, ở **cùng độ phân giải**, rồi
đo ba đại lượng — tỉ lệ ảnh cho cùng số khuôn mặt, độ chồng khớp giữa hai khung bao, và sai lệch vị
trí của năm điểm mốc.

**Bảng 4.1 — Độ khớp giữa bản NCNN và bản PyTorch gốc**

| Độ phân giải | Số ảnh | Khớp số khuôn mặt | Độ chồng khớp khung bao | Sai lệch điểm mốc trung bình |
|---|---|---|---|---|
| 320 × 320 | 50 | 50/50 | 0,9999996 | 2,49 × 10⁻⁵ px |
| 640 × 640 | 50 | 50/50 | 0,9999996 | 2,17 × 10⁻⁵ px |

*Nguồn: `results/export_ncnn_20260827_2144.json`.*

Sai lệch ở mức 10⁻⁵ pixel là mức làm tròn của chính kiểu số thực 32 bit, tức phép chuyển đổi **không
làm mất mát gì đáng kể** về mặt số học. Kết quả này phù hợp với việc bản chuyển đổi giữ nguyên định
dạng dấu phẩy động 32 bit, không kèm lượng tử hoá (§2.6.4).

Cùng phép kiểm được lặp lại trên một tập lớn hơn nhiều trong quá trình đo hiệu năng: trên **1 800
khung hình**, hai bộ suy luận cho **cùng số khuôn mặt ở mọi khung**, với tỉ lệ phát hiện 100 % và độ
tin cậy trung bình trùng nhau tới bốn chữ số thập phân (0,8538).
*Nguồn: `notebooks/02_phan_tich_hieu_nang_detect.ipynb` mục 6.*

Hệ quả cho phần còn lại của chương: **việc chọn bộ suy luận nào là quyết định thuần về hiệu năng**,
không đánh đổi gì về độ chính xác phát hiện.

### 4.3.2. Kết quả sơ bộ trên máy phát triển

> ⚠️ Số liệu mục này đo trên `pc_x86`, **không** dùng để kết luận chỉ tiêu ≥ 10 FPS và **không** dùng
> để chọn bộ suy luận chính thức. Lý do nêu ở cuối mục.

Ma trận đo gồm 12 cấu hình — hai bộ suy luận × hai độ phân giải × ba mức số luồng — lặp lại ba lượt
vào ba thời điểm khác nhau, tổng cộng 3 600 phép đo.

**Bảng 4.2 — Tốc độ khung hình trung bình và mức dao động giữa ba lượt**

| Độ phân giải | Số luồng | ONNX Runtime | NCNN | Chênh lệch | Dao động lớn nhất | Đủ căn cứ kết luận |
|---|---|---|---|---|---|---|
| 320 | 1 | 26,5 | 24,7 | −6,5 % | 22,5 % | chưa đủ |
| 320 | 2 | 31,5 | 36,2 | +14,6 % | 168,3 % | chưa đủ |
| 320 | 4 | 40,2 | 39,2 | −2,3 % | 25,9 % | chưa đủ |
| 640 | 1 | 5,5 | 6,9 | +25,6 % | 18,4 % | **đủ** |
| 640 | 2 | 8,9 | 8,9 | −0,7 % | 11,3 % | chưa đủ |
| 640 | 4 | 11,5 | 10,2 | −10,8 % | 4,0 % | **đủ** |

*Đơn vị: khung hình mỗi giây. Nguồn: `notebooks/02_phan_tich_hieu_nang_detect.ipynb` mục 4, từ ba
tệp `results/bench_detect_20260903_{2022,2040,2044}.csv`.*

Cột **dao động lớn nhất** là mức chênh giữa lượt nhanh nhất và lượt chậm nhất của cùng một cấu hình,
tính trên bộ suy luận dao động nhiều hơn. Cột cuối so sánh hai cột trước đó: khi mức dao động của
chính phép đo lớn hơn khác biệt giữa hai bộ suy luận, khác biệt ấy chưa đủ căn cứ để kết luận.

Chỉ **2 trong 6 cấu hình** vượt được ngưỡng đó.

### 4.3.3. Vì sao số liệu trên máy phát triển không kết luận được

Hai quan sát giải thích cột cuối của Bảng 4.2.

**Thứ nhất, mức dao động khi đo lại rất lớn.** Cấu hình `320 × 320, hai luồng` của ONNX Runtime cho
15,8 · 36,3 · 42,5 khung hình mỗi giây qua ba lượt — lượt cao gấp 2,7 lần lượt thấp. Nếu chỉ chạy
một lượt rồi báo cáo, con số thu được có thể là bất kỳ giá trị nào trong khoảng đó.

**Bảng 4.3 — Mức dao động giữa các lượt, gộp theo bộ suy luận**

| Bộ suy luận | Thấp nhất | Cao nhất | Trung bình |
|---|---|---|---|
| NCNN | 2,5 % | 18,8 % | **7,7 %** |
| ONNX Runtime | 1,7 % | 168,3 % | **41,4 %** |

*Nguồn: `notebooks/02_phan_tich_hieu_nang_detect.ipynb` mục 3.*

Đây là kết quả có ý nghĩa riêng, độc lập với tốc độ tuyệt đối: trên cùng một máy, NCNN cho kết quả
lặp lại ổn định hơn khoảng năm lần. Với hệ thống xử lý thời gian thực, mức ổn định quan trọng không
kém giá trị trung bình.

**Thứ hai, thứ tự nhanh chậm giữa hai bộ suy luận có thể đảo chiều theo kiến trúc.** NCNN tối ưu
quanh tập lệnh vectơ NEON của ARM, còn ONNX Runtime được tối ưu kỹ nhất trên x86 (§2.6.4). Kết luận
rút ra trên máy phát triển vì thế không suy ra được cho Raspberry Pi 5.

Hệ quả phương pháp, và cũng là lý do mục này tồn tại trong báo cáo: **phép đo trên máy phát triển
xác nhận quy trình đo chạy đúng và hai bộ suy luận cho cùng kết quả phát hiện, nhưng không thay thế
được phép đo trên phần cứng đích.** Kết luận chọn bộ suy luận đặt ở §4.3.4.

### 4.3.4. Kết quả trên Raspberry Pi 5

Ba lượt đo độc lập được thực hiện trên phần cứng đích ngày 05/09/2026, cách nhau vài phút, mỗi lượt
lặp lại đầy đủ ma trận 12 cấu hình như ở §4.3.2 (hai bộ suy luận × hai độ phân giải × ba mức số
luồng), mỗi ô 100 khung hình sau 10 khung làm nóng, cùng `seed=42` và cùng 110 ảnh chọn ra từ 9 164
ảnh của `data/impostor/lfw_original`. Thiết bị: Raspberry Pi 5 8 GB,
`Linux-6.12.93+rpt-rpi-2712-aarch64-with-glibc2.36`, Python 3.11.2, ONNX Runtime 1.20.1, ncnn
1.0.20260526, chạy không màn hình qua SSH, không bật cửa sổ xem trước. Cả ba lượt cùng commit
`57b874c`, cây làm việc sạch (`git_dirty: false`).

**Bảng 4.4 — Tốc độ khung hình trên Raspberry Pi 5, trung bình và độ lệch chuẩn của ba lượt đo**

| Bộ suy luận | Kích thước | Số luồng | FPS trung bình | Độ lệch chuẩn | Latency p50 (ms) | Latency p95 (ms) | Tỉ lệ phát hiện | Đạt ≥ 10 FPS |
|---|---|---|---|---|---|---|---|---|
| ONNX Runtime | 320 | 1 | 10,58 | 0,02 | 94,4 | 95,3 | 100 % | Đạt |
| ONNX Runtime | 320 | 2 | 18,9 | 0,05 | 52,8 | 54,1 | 100 % | Đạt |
| ONNX Runtime | 320 | 4 | 27,5 | 0,34 | 35,3 | 42,9 | 100 % | Đạt |
| ONNX Runtime | 640 | 1 | 2,60 | 0,00 | 383,8 | 385,3 | 100 % | Không đạt |
| ONNX Runtime | 640 | 2 | 4,83 | 0,00 | 206,5 | 209,2 | 100 % | Không đạt |
| ONNX Runtime | 640 | 4 | 6,61 | 0,02 | 149,0 | 158,1 | 100 % | Không đạt |
| NCNN | 320 | 1 | 35,5 | 0,12 | 28,1 | 28,7 | 100 % | Đạt |
| NCNN | 320 | 2 | 53,8 | 0,34 | 18,5 | 18,7 | 100 % | Đạt |
| NCNN | 320 | 4 | 60,6 | 0,29 | 16,4 | 17,0 | 100 % | Đạt |
| NCNN | 640 | 1 | 8,62 | 0,03 | 115,7 | 117,5 | 100 % | Không đạt |
| NCNN | 640 | 2 | 12,4 | 0,05 | 80,3 | 83,0 | 100 % | Đạt |
| NCNN | 640 | 4 | 13,7 | 0,08 | 72,3 | 78,7 | 100 % | Đạt |

*Nguồn: `results/bench_detect_20260905_1911.csv`, `results/bench_detect_20260905_1914.csv`,
`results/bench_detect_20260905_1916.csv` và ba tệp `.meta.json` tương ứng — trường `tom_tat` của mỗi
tệp. Điều kiện: Raspberry Pi 5 8 GB có tản nhiệt chủ động, ảnh vào từ đĩa (không qua camera), 100
khung hình mỗi ô mỗi lượt, 3 lượt, `seed=42`, không bật cửa sổ xem trước, chạy qua SSH.*

**Kết luận chỉ tiêu: chỉ tiêu FPS riêng module phát hiện ≥ 10 FPS ĐẠT.** Tám trên mười hai cấu hình đã
kiểm vượt ngưỡng, trải từ 10,58 FPS (ONNX Runtime, 320 px, 1 luồng — vượt ngưỡng khoảng 5,8 %) đến
60,6 FPS (NCNN, 320 px, 4 luồng — vượt ngưỡng hơn 6 lần). Tỉ lệ phát hiện đạt 100 % ở toàn bộ 12 cấu
hình qua cả ba lượt, tức không cấu hình nào bỏ sót khuôn mặt trên tập ảnh kiểm thử.

**So sánh NCNN với ONNX Runtime.** Bảng 4.5 quy đổi Bảng 4.4 thành tỉ lệ tăng tốc của NCNN so với ONNX
Runtime, ở cùng độ phân giải và cùng số luồng.

**Bảng 4.5 — Tỉ lệ tăng tốc của NCNN so với ONNX Runtime, tính từ Bảng 4.4**

| Kích thước | Số luồng | ONNX Runtime (FPS) | NCNN (FPS) | Tỉ lệ tăng tốc |
|---|---|---|---|---|
| 320 | 1 | 10,58 | 35,5 | 3,35 lần |
| 320 | 2 | 18,9 | 53,8 | 2,85 lần |
| 320 | 4 | 27,5 | 60,6 | 2,20 lần |
| 640 | 1 | 2,60 | 8,62 | 3,32 lần |
| 640 | 2 | 4,83 | 12,4 | 2,57 lần |
| 640 | 4 | 6,61 | 13,7 | 2,07 lần |

NCNN nhanh hơn ONNX Runtime từ 2,07 đến 3,35 lần trên cùng một mô hình và cùng đầu vào — không có
cấu hình nào ONNX Runtime nhanh hơn. Chênh lệch lớn nhất xuất hiện ở một luồng (khoảng 3,3 lần) và
thu hẹp dần khi tăng số luồng (còn khoảng 2,1–2,2 lần ở bốn luồng). Cách đọc này khớp với §2.6.4: NCNN
là bộ suy luận được viết và tối ưu riêng cho tập lệnh vectơ NEON của kiến trúc ARM, còn ONNX Runtime
là bộ chạy đa nền tảng, phải đánh đổi bớt phần tối ưu chuyên biệt để giữ khả năng chạy trên nhiều kiến
trúc khác nhau. Khi số luồng tăng, phần thời gian xử lý song song hoá chiếm tỉ trọng lớn hơn trong
tổng thời gian suy luận, nên phần chênh lệch do tối ưu tập lệnh mang lại bị pha loãng bớt.

**Cấu hình 640 px.** ONNX Runtime không đạt ngưỡng 10 FPS ở bất kỳ mức số luồng nào tại độ phân giải
640 px (cao nhất 6,61 FPS ở 4 luồng). NCNN đạt ngưỡng ở 2 và 4 luồng (12,4 FPS và 13,7 FPS) nhưng
không đạt ở 1 luồng (8,62 FPS). Kết quả này có ý nghĩa cho bước 7.1: kịch bản kiểm thử tổng hợp có mốc
khoảng cách 2 m, và ở khoảng cách đó khuôn mặt chiếm ít điểm ảnh hơn hẳn so với khoảng cách 0,5 m —
đầu vào 640 px giữ được nhiều chi tiết hơn cho những khuôn mặt nhỏ. Vì vậy độ phân giải 640 px được
giữ lại như một **phương án mở** cho khoảng cách xa, chưa loại bỏ dù chậm hơn 320 px; quyết định chốt
giữa hai độ phân giải đặt sau khi có số liệu tỉ lệ nhận đúng theo khoảng cách ở bước 7.2.

**So sánh với máy phát triển.** Ở cấu hình ONNX Runtime, 320 px, 4 luồng — cấu hình xuất hiện ở cả hai
môi trường — máy phát triển Windows x86-64 cho 40,2 FPS (Bảng 4.2), còn Raspberry Pi 5 cho 27,5 FPS
(Bảng 4.4), tức máy phát triển nhanh hơn khoảng 1,5 lần. Đây là kết quả bình thường và không mâu thuẫn
với luận điểm của đề tài: mục tiêu đặt ra là chứng minh hệ thống **chạy được và đạt chỉ tiêu** trên một
thiết bị biên giá rẻ, tiêu thụ ít điện, không phải chứng minh thiết bị đó nhanh hơn máy tính cá nhân.

Điều đáng chú ý hơn tốc độ tuyệt đối là **độ ổn định**. Ở cùng cấu hình, mức dao động lớn nhất giữa ba
lượt đo trên Raspberry Pi 5 là 2,5 % (Bảng 4.4: ba lượt 27,11 · 27,49 · 27,79 FPS), trong khi trên máy
phát triển là 25,9 % (Bảng 4.2) — chênh nhau khoảng mười lần. Nguyên nhân hợp lý là Raspberry Pi 5
chạy không màn hình, qua SSH, không có tiến trình nền của môi trường làm việc thông thường (trình
duyệt, trình soạn thảo, phần mềm nền) tranh chấp CPU trong lúc đo, trong khi máy phát triển là máy
đang dùng cho nhiều việc khác song song. Quan sát này củng cố thêm cho lập luận đã nêu ở §4.3.3.

Hai máy khác hệ điều hành và khác bản dựng thư viện suy luận, nên khác biệt tốc độ quan sát được ở
trên **không** tách bạch được thành phần do kiến trúc phần cứng với thành phần do bản dựng phần mềm —
đây là giới hạn phương pháp đã nêu ở §4.1.1 và §4.3.3, áp dụng cho mọi so sánh trực tiếp giữa hai
môi trường trong chương này.

**Bảng 4.6 — Đối chiếu tốc độ và độ ổn định giữa hai môi trường, cùng cấu hình ONNX Runtime 320 px 4 luồng**

| Môi trường | FPS trung bình | Dao động lớn nhất giữa các lượt | Số lượt đo |
|---|---|---|---|
| `pc_x86` | 40,2 | 25,9 % | 3 |
| `pi5` | 27,5 | 2,5 % | 3 |

*Nguồn: cột `pc_x86` lấy từ Bảng 4.2 (§4.3.2), tính từ ba tệp
`results/bench_detect_20260903_{2022,2040,2044}.csv`; cột `pi5` lấy từ Bảng 4.4 (§4.3.4), tính từ ba
tệp `results/bench_detect_20260905_{1911,1914,1916}.csv` (ba giá trị FPS 27,11 · 27,49 · 27,79).*

Một mẻ đo trước đó trên `pc_x86` (19/08/2026, `results/bench_detect_20260819_1453.csv`) từng cho
21,7 FPS ở cấu hình này. Mẻ đo đó đã lỗi thời: nó được thực hiện trước khi `scripts/benchmark_detect.py`
được sửa lại ở các mã việc `P2-06`, `P2-06b` và `P2-06c` (bổ sung bộ suy luận NCNN vào cùng một ma
trận đo và giới hạn lại phạm vi cờ `git_dirty`), nên không dùng làm mốc đối chiếu cho `pc_x86` nữa —
Bảng 4.6 chỉ dùng số liệu từ Bảng 4.2, sinh ra bởi bản script hiện hành.

**Nhiệt độ bộ xử lý và giảm xung.** Nhiệt độ khởi động và đỉnh của ba lượt lần lượt là 43,0 → 57,85 °C
(lượt A), 46,3 → 60,6 °C (lượt B), 49,6 → 62,8 °C (lượt C) — tăng khoảng 2,5 °C mỗi lượt qua ba lượt
liên tiếp, tương ứng khoảng 7 phút tải liên tục (ba lượt × ~139 giây). Lệnh `vcgencmd get_throttled`
chạy sau mỗi lượt đều trả `0x0`, tức không phát hiện giảm xung hay hạ áp trong suốt quá trình đo.
Thiết bị có tản nhiệt chủ động. *Nguồn: `cpu_temp_start_c`, `cpu_temp_max_c`, `duration_s` trong ba
tệp `.meta.json` nêu trên.*

⚠️ Số liệu nhiệt độ trên **chưa phải** kết quả của bước 2.7. Bước đó yêu cầu 10 phút chạy liên tục ở
một cấu hình cố định để quan sát xu hướng nhiệt dài hạn, trong khi ba lượt ở đây là ba lần chạy trọn
ma trận 12 cấu hình, tổng cộng khoảng 7 phút. Bước 2.7 giữ nguyên `[CHƯA ĐO]`.

**Giới hạn của số liệu mục này.** Toàn bộ số đo trong Bảng 4.4 lấy ảnh đầu vào từ đĩa
(`data/impostor/lfw_original`), không qua camera thật. Bước 2.5 — đo FPS thời gian thực từ camera —
**chưa được thực hiện**. Số liệu ở đây phản ánh năng lực suy luận thuần của mô hình và bộ suy luận,
chưa gồm chi phí thu khung hình, giải mã và tiền xử lý từ luồng camera; FPS đo được khi ghép với
camera thật nhiều khả năng thấp hơn các con số trong Bảng 4.4. Mục này giữ `[CHƯA ĐO]` riêng cho phần
đo từ camera thật.

**Kết luận chọn bộ suy luận.** Dựa trên Bảng 4.4 và Bảng 4.5, NCNN vượt trội ONNX Runtime ở mọi cấu
hình đã đo trên Pi 5, không đánh đổi độ chính xác phát hiện (§4.3.1). Độ phân giải 320 px đáp ứng chỉ
tiêu FPS thoải mái ở cả hai bộ suy luận; độ phân giải 640 px giữ làm phương án dự phòng cho khoảng
cách xa, quyết định chốt sau bước 7.2. Việc cập nhật giá trị chính thức vào `configs/detect.yaml`
thuộc phạm vi của đặc tả, không thuộc phạm vi ghi tệp của chương này.

---

## 4.4. Kết quả nhận diện danh tính

`[CHƯA ĐO]` — chặn vì chưa có cơ sở dữ liệu khuôn mặt.

Dàn ý: bảng so sánh hai phương án theo độ chính xác, FAR, FRR, tốc độ và độ trễ · ba con số FAR trên
ba tập impostor · kết luận kiểm chứng hiệu chỉnh miền dữ liệu · đường cong ROC và ngưỡng đã chốt.

---

## 4.5. Kết quả chống giả mạo

`[CHƯA ĐO]` — chặn vì chưa có bộ dữ liệu tấn công.

Dàn ý: kết quả tách riêng cho ảnh in và màn hình điện thoại · ba chỉ số APCER, BPCER, ACER · chi phí
tốc độ khi bật khối chống giả mạo.

---

## 4.6. Bảng đối chiếu chỉ tiêu cam kết

**Bảng 4.7 — Đối chiếu chỉ tiêu cam kết với số liệu thực nghiệm hiện có**

| Chỉ tiêu cam kết | Ngưỡng | Đạt được | Kết luận |
|---|---|---|---|
| Độ chính xác nhận diện người đã đăng ký | ≥ 95 % | `[CHƯA ĐO]` | `[CHƯA ĐO]` |
| FPS toàn pipeline | ≥ 5 FPS | `[CHƯA ĐO]` | `[CHƯA ĐO]` |
| FPS riêng module phát hiện | ≥ 10 FPS | 10,58–60,6 FPS tuỳ cấu hình, đạt ở 8/12 cấu hình đã đo (xem Bảng 4.4) | ✅ Đạt |
| Độ trễ điều khiển thiết bị | < 2 s | `[CHƯA ĐO]` | `[CHƯA ĐO]` |
| Tỉ lệ phát hiện tấn công giả mạo | ≥ 90 % | `[CHƯA ĐO]` | `[CHƯA ĐO]` |

*Nguồn dòng FPS phát hiện: Bảng 4.4, mục §4.3.4 — `results/bench_detect_20260905_{1911,1914,1916}.csv`
và `.meta.json` tương ứng. Bốn dòng còn lại chờ số liệu từ §4.2, §4.4, §4.5 và Phase 7.*

---

## Checklist hoàn thành Chương 4

- [ ] Mọi mục không còn `[CHƯA ĐO]`
- [ ] Mỗi bảng và hình đều ghi tệp nguồn trong `results/` hoặc `notebooks/`
- [ ] Số hiệu năng kết luận chỉ tiêu **chỉ** lấy từ môi trường `pi5`
- [ ] Mỗi phép so sánh đều báo cáo mức dao động, không chỉ giá trị trung bình
- [ ] Kết quả không đạt chỉ tiêu được trình bày trung thực kèm phân tích nguyên nhân
