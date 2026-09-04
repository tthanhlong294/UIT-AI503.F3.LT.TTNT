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

`[CHƯA ĐO]` — chặn vì chưa có phần cứng.

Dàn ý: ma trận 12 cấu hình lặp ba lượt trên thiết bị thật · bảng đối chiếu ba môi trường chứng minh
tính khả chuyển · nhiệt độ bộ xử lý và hiện tượng giảm xung trong 10 phút chạy liên tục · kết luận
chọn bộ suy luận và độ phân giải chính thức, ghi vào `configs/detect.yaml`.

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

`[CHƯA ĐO]` — cần số liệu từ §4.3.4, §4.4, §4.5 và Phase 7.

---

## Checklist hoàn thành Chương 4

- [ ] Mọi mục không còn `[CHƯA ĐO]`
- [ ] Mỗi bảng và hình đều ghi tệp nguồn trong `results/` hoặc `notebooks/`
- [ ] Số hiệu năng kết luận chỉ tiêu **chỉ** lấy từ môi trường `pi5`
- [ ] Mỗi phép so sánh đều báo cáo mức dao động, không chỉ giá trị trung bình
- [ ] Kết quả không đạt chỉ tiêu được trình bày trung thực kèm phân tích nguyên nhân
