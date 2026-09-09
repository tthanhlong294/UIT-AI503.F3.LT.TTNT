# P2-07 — Đường vào từ camera cho `benchmark_detect.py`

| | |
|---|---|
| **Bước CLAUDE.md** | §5 Phase 2, bước **2.5** — phép đo duy nhất còn thiếu để đóng Cổng C của Phase 2 |
| **Nhánh** | `feat/p2-07-benchmark-detect-camera` |
| **Phụ thuộc** | `dev` **sau khi `P3-05` đã gộp**. Không có phụ thuộc mã nguồn vào `P3-05`; điều kiện này chỉ để mốc đếm ca kiểm thử ở §3.3 đúng |
| **Đặc tả viết** | 07/09/2026 |

---

## 1. Mục tiêu

Thêm cờ `--nguon {dia,camera}` vào `scripts/benchmark_detect.py` để đo hiệu năng khối phát hiện
trên **khung hình lấy trực tiếp từ camera**, tách riêng chi phí thu hình và chi phí suy luận thành
hai cột số liệu độc lập.

Bước 2.6 đã đo **năng lực suy luận thuần** (ảnh nạp sẵn trong RAM, vùng bấm giờ ôm đúng `detect()`).
Bước 2.5 đo **hệ thống thật**: khung hình phải được lấy về trước khi suy luận, và chi phí đó không
biến mất chỉ vì bước 2.6 đã cố tình loại nó ra.

---

## 2. Phạm vi file — danh sách trắng

| Tệp | Trạng thái | Vai trò |
|---|---|---|
| `scripts/benchmark_detect.py` | **sửa** | Thêm nhánh `camera`, không đụng nhánh `dia` |
| `tests/test_benchmark_detect.py` | **sửa — CHỈ THÊM** | Bộ kiểm thử mới, nối vào cuối tệp |

**Không sửa**: `src/**` (kể cả `src/capture/**`), `configs/**`, `scripts/**` khác, `requirements.txt`,
`docs/**`, `.claude/**`, `notebooks/**`, `report/**`, `results/**`, `.gitignore`.

⚠️ Mã việc này **không thêm khoá cấu hình mới** và **không sửa `configs/capture.yaml`**. Mọi tham số
camera đã có sẵn ở đó (§3.4); `configs/capture.yaml` giữ nguyên `backend: auto` vì đó là mặc định
đúng cho pipeline sản phẩm — riêng script benchmark **cấm** giá trị `auto`, lý do ở §4.3.

Ước lượng: script **+~260 dòng**, test **+~470 dòng**.

---

## 3. Dữ kiện đã kiểm — 07/09/2026

### 3.1. `benchmark_detect.py` hiện đọc ảnh từ đĩa

| Dữ kiện | Vị trí |
|---|---|
| `chon_anh()` liệt kê thư mục rồi `random.sample` theo seed | `scripts/benchmark_detect.py:150-178` |
| Toàn bộ ảnh `cv2.imread` vào `anh_da_nap` **trước** vòng đo | `:544-550` |
| Vùng bấm giờ ôm **đúng một** lệnh `detector.detect(anh)` | `:231-234` |
| `--device-name` chỉ là nhãn ghi vào `meta.device.name`, không ảnh hưởng nguồn ảnh | `:631`, in ở `:520` |
| `_COT_CSV` có **10 cột** | `:87-98` |
| `_KHOA_META_BAT_BUOC` có **20 khoá** | `:100-121` |
| Cảnh báo khi `moi_truong != "pi5"` ghi vào `notes` | `:78-85`, `:609-613` |
| Ngưỡng chỉ tiêu `NGUONG_FPS_TOI_THIEU = 10.0`, cỡ mẫu `SO_FRAME_TOI_THIEU = 100` | `:45`, `:49` |

Chi phí đọc tệp và giải mã nằm **hoàn toàn ngoài** phép đo — đó là chủ ý của bước 2.6, không phải
thiếu sót. Mã việc này **không sửa** điều đó.

### 3.2. Kết quả bước 2.6 trên Pi 5 — mốc để đối chiếu

12 cấu hình, cao nhất **60,6 FPS** (NCNN, 320 px, 4 luồng), thấp nhất **2,60 FPS** (ONNX, 640 px,
1 luồng). Nguồn: `results/bench_detect_20260905_{1911,1914,1916}.csv`.

⚠️ Hai con số trên đo ở **lượt chạy trên máy đã ổn định nhiệt** (bước 2.7: 10,7 phút tải liên tục,
`throttled=0x0`, đỉnh 65,55 °C, lệch dưới 1,4 % so với lượt ngắn). Chúng dùng để **bắt sai lệch hàng
chục lần**, không dùng để phán xét chênh lệch vài chục phần trăm giữa hai lượt đo.

### 3.3. Bộ kiểm thử — mốc để đối chiếu

| Nơi chạy | Lệnh | Mốc |
|---|---|---|
| `tests/test_benchmark_detect.py` | đếm hàm `def test_` | **72 ca** |
| Host `pc_x86`, Windows, **có** `models/` | `python -m pytest -q`, **không** lọc marker | **689 ca thu thập** trên `dev` sau khi gộp `P3-05` ⇒ `689 passed` |
| Container `faceid:arm64` | `python3 -m pytest -q -m "not slow"` | ⚠️ **chưa được ghi lại ở đâu** cho mốc `dev` sau `P3-05` |

⭐ Vì dòng thứ ba chưa có mốc, **việc đầu tiên** của người cài đặt là chạy hai lệnh §9.1 **trước khi
sửa một dòng nào**, dán kết quả về làm mốc, rồi mới bắt đầu. Không có mốc thì con số "sau" không nói
lên điều gì.

### 3.4. Khối thu hình đã có — đã qua review ở `P1-01`, KHÔNG sửa

`src/capture/__init__.py` xuất `tao_bo_thu_hinh(cfg) -> BoThuHinh`. `BoThuHinh` có `mo()`,
`doc_frame() -> np.ndarray`, `dong()`, thuộc tính `dang_mo`, và hỗ trợ `with`.

| Backend | Lớp | Ghi chú |
|---|---|---|
| `opencv` | `CameraOpenCV` | Camera thật |
| `mock` | `CameraGiaLap` | Khung tổng hợp theo seed, hoặc đọc thư mục ảnh |
| `auto` | tự dò | Mở thử `opencv`, **hỏng thì âm thầm rơi về `mock`** (`factory.py:35-51`) |

`configs/capture.yaml` có: `backend` · `opencv.{device_index,width,height,fps,warmup_frames,max_retry}`
· `mock.{width,height,source,source_dir,seed,loop,max_frames}`.

⚠️⚠️ **Hai sự thật phải nói rõ trong báo cáo, đã kiểm bằng cách đọc mã:**

1. `CameraOpenCV` **không bao giờ gọi `cv2.CAP_PROP_FPS`** (`opencv_camera.py:39-60` chỉ đặt
   `FRAME_WIDTH` và `FRAME_HEIGHT`). Khoá `opencv.fps: 30` là **giá trị khai báo**, không phải giá
   trị được áp. Tốc độ khung thật do webcam tự quyết. Vì vậy meta gọi khoá này là
   `fps_khai_bao_trong_cau_hinh`, và tốc độ thật **phải đo**, không được suy từ cấu hình.
2. `CameraOpenCV` **không phơi ra độ phân giải thật**. `cap.set(...)` có thể bị webcam từ chối im
   lặng. Cách duy nhất biết độ phân giải thật là đọc `frame.shape` của khung đã lấy về — §5.4.

Webcam USB đã kiểm mở được trên Pi 5 bằng chính mã của đồ án, 1280×720, ảnh thật không phải khung đen.

### 3.5. Container `faceid:arm64` thiếu những gì

Không có: nhị phân `git`, thư mục `.git/`, `docs/`, `models/`, `data/`, `results/`, `report/`, và các
gói `ultralytics`, `torch`, `onnx`. **Không có camera.** Chỉ có `requirements.txt` cộng
`pytest`/`black`/`ruff`.

⭐ **Mọi ca kiểm thử mới dùng bộ thu hình giả** (§5.7) và **không ca nào được mang
`@pytest.mark.slow`** — số ca mới phải cộng đủ vào **cả hai** dòng host và container của §3.3.

### 3.6. `.gitignore`

`results/` **không** bị chặn ở mức thư mục — chỉ chặn `results/**/*.{jpg,jpeg,png,mp4,avi}` và
`results/alerts/`. Tệp `.csv` và `.meta.json` sinh ra ở §12b **được git theo dõi và phải commit** (R6).

---

## 4. Ba quyết định thiết kế — chốt và lý do

### 4.1. ★ Ranh giới bấm giờ: đo HAI khoảng riêng cho mỗi khung, ghi thành ba cột

Ở chế độ `dia`, vùng bấm giờ ôm đúng `detect()`. Nếu chế độ `camera` cũng chỉ ôm `detect()` thì con
số **giống hệt bước 2.6** và mã việc này vô nghĩa. Nếu ngược lại, chỉ ghi **một** con số tổng thì mất
khả năng phân tích — mà phân tích đó chính là thứ Chương 4 cần nói.

**Chốt**: mỗi khung đo **hai khoảng tách rời**, ghi **ba cột**:

| Cột CSV | Vùng bấm giờ | Ý nghĩa |
|---|---|---|
| `latency_lay_khung_ms` | ôm đúng `bo_thu_hinh.doc_frame()` | chi phí thu hình + giải mã |
| `latency_ms` | ôm đúng `detector.detect(frame)` | **cùng định nghĩa với chế độ `dia`** — so trực tiếp được với bước 2.6 |
| `latency_tong_ms` | **tổng số học** của hai cột trên | chi phí một vòng đầu-cuối |

⛔ `latency_tong_ms` **phải là phép cộng**, không phải một cặp `perf_counter()` thứ ba bao ngoài. Lý
do: cặp thứ ba sẽ nuốt thêm cả phần ghi bản ghi và đọc nhiệt độ, làm ba cột không còn cộng khớp, và
người đọc báo cáo không giải thích được phần chênh. Dòng 21 §8 canh đúng bằng đẳng thức từng dòng.

Cột `latency_ms` **giữ nguyên nghĩa "chỉ suy luận"** ở cả hai chế độ. Đây là quyết định có chủ đích:
nó là cây cầu duy nhất cho phép đặt số bước 2.5 cạnh số bước 2.6 trong cùng một bảng.

**Trần cứng của tốc độ khung — kết luận cho báo cáo, không phải khuyết điểm.**
Nếu webcam chạy ở 30 khung/s thì `latency_lay_khung_ms` có **sàn ≈ 33 ms**, nên `fps_tong_tb` **không
thể vượt ~30** dù khối phát hiện đạt 60,6 FPS. Chỉ tiêu §1 là "FPS **riêng module detect** ≥ 10", đo
bằng `fps_tb` — trần này không đe doạ chỉ tiêu, nhưng phải nói ra để không ai đọc `fps_tong_tb ≈ 29`
rồi tưởng hệ thống chậm đi.

⚠️ **Chiều hỏng ngược lại, phải canh bằng máy.** `cv2.VideoCapture` có bộ đệm nội bộ: nếu suy luận
chậm hơn tốc độ khung, `doc_frame()` có thể trả về **tức thì một khung cũ** thay vì chờ khung mới.
Khi đó `latency_lay_khung_ms` gần 0 và con số đầu-cuối **đẹp một cách giả tạo**, trong khi khung hình
đã cũ vài trăm ms. Vì vậy: `lay_khung_p50 < _NGUONG_NGHI_NGO_DEM_KHUNG_MS` **và** `latency_p50` (suy
luận) lớn hơn `lay_khung_p50` ít nhất 10 lần ⇒ ghi khoá cảnh báo `canh_bao_dem_khung` (§5.6). Cảnh
báo, không chặn — bộ đệm là hành vi của thư viện, không phải lỗi của phép đo; nhưng nó phải đi cùng
tệp kết quả suốt đời tệp đó.

### 4.2. ★ Chế độ `camera` đo ĐÚNG MỘT cấu hình, không quét ma trận

**Chốt**: `--nguon camera` bắt buộc `--models` có **đúng một** phần tử và `--threads` có **đúng một**
mức. Vi phạm → `main()` trả `1`, thông báo nêu **cả hai** tên cờ và số phần tử nhận được.

Lý do **quyết định** là tính công bằng, không phải thời gian chạy:

> Chế độ `dia` nạp sẵn **cùng một tập ảnh** và dùng lại cho **mọi ô** của ma trận — đó chính là điều
> làm phép so 12 ô có nghĩa (`experiment-protocol` §2, "chỉ được thay đổi đúng một biến"). Với camera
> thật thì **không tồn tại cách nào** giữ đầu vào giống nhau giữa các ô: người trong khung nhúc nhích,
> mây che nắng, camera tự hiệu chỉnh phơi sáng. Một bảng 12 ô đo từ camera trông giống bảng bước 2.6
> nhưng **không so sánh được**, và không có gì trên tệp kết quả cho biết điều đó.

Hệ quả thời gian chạy, tính thật để người dùng biết trước: ở `--n-frames 300` cộng `--warmup 10`, mỗi
lượt ≈ 310 khung. Nếu camera chạy 30 khung/s thì ô nhanh **bị chặn ở ~10,3 s**; ô chậm nhất của bước
2.6 (2,60 FPS) mất ≈ 119 s. Tức là quét cả 12 ô cũng chỉ vài phút — **thời gian không phải lý do**.
Lý do là phép so không còn công bằng.

Kèm theo: camera được **mở đúng một lần** cho cả lượt đo (§4.3), nên câu hỏi "12 lần mở/đóng camera"
không còn đặt ra.

### 4.3. ★ Cấm `auto`, bắt buộc `--capture-backend`

`tao_bo_thu_hinh` với `backend: auto` mở thử camera thật, **hỏng thì âm thầm rơi về `mock`**
(`factory.py:47-51`, chỉ ghi một dòng `logger.warning`). Trong pipeline sản phẩm đó là hành vi đúng.
Trong một script benchmark thì đó là chế độ hỏng tệ nhất có thể: nó sinh ra một tệp `results/` đầy đủ,
mang nhãn `--device-name "Raspberry Pi 5 8GB"`, mà **số bên trong là nhiễu ngẫu nhiên tổng hợp**.

**Chốt**: `--capture-backend` **bắt buộc** ở chế độ `camera`, `choices=["opencv", "mock"]`. Giá trị
này **ghi đè** khoá `backend` của `configs/capture.yaml` trước khi gọi `tao_bo_thu_hinh`. Giá trị
`auto` bị argparse từ chối. Chạy với `mock` vẫn được — nhưng meta **bắt buộc** mang khoá
`canh_bao_nguon_gia_lap` không rỗng (§5.6).

---

## 5. Thiết kế chi tiết

### 5.1. Giao diện dòng lệnh

```
python scripts/benchmark_detect.py [--nguon {dia,camera}] --device-name TÊN
       [--config CONFIG] [--models M ...] [--threads T ...] [--n-frames N] [--warmup W]
       [--ghi-chu GHI_CHU] [--dry-run]
       # chỉ chế độ dia:
       [--anh-dir DIR] [--seed SEED]
       # chỉ chế độ camera:
       [--capture-config CONFIG] --capture-backend {opencv,mock}
       --anh-sang MÔ_TẢ --khoang-cach-m SỐ --noi-dung-khung {co-nguoi,khong-nguoi}
```

| Cờ | Mới? | Mặc định | Ý nghĩa |
|---|---|---|---|
| `--nguon` | mới | `dia` | `dia` = hành vi hiện tại, `camera` = đường vào từ khối thu hình |
| `--capture-config` | mới | `None` → `configs/capture.yaml` | Chỉ chế độ `camera` |
| `--capture-backend` | mới | `None` | Chỉ chế độ `camera`, **bắt buộc**, `choices=["opencv","mock"]` |
| `--anh-sang` | mới | `None` | Chỉ chế độ `camera`, **bắt buộc**. Mô tả tự do, ví dụ `"trong nhà, đèn LED trần, ~300 lux"` |
| `--khoang-cach-m` | mới | `None` | Chỉ chế độ `camera`, **bắt buộc**, `type=float` |
| `--noi-dung-khung` | mới | `None` | Chỉ chế độ `camera`, **bắt buộc**, `choices=["co-nguoi","khong-nguoi"]` |
| `--anh-dir` | **đổi mặc định** | `None` → `_ANH_DIR_MAC_DINH` | Chỉ chế độ `dia` |
| `--seed` | **đổi mặc định** | `None` → `_SEED_MAC_DINH` | Chỉ chế độ `dia` |
| còn lại | không đổi | không đổi | |

Hai hằng số module mới, giữ nguyên giá trị đang hardcode trong `add_argument`:
`_ANH_DIR_MAC_DINH = "data/impostor/lfw_original"`, `_SEED_MAC_DINH = 42`.

⭐ Vì sao phải đổi `default` của `--anh-dir` và `--seed` thành `None`: với `default` là giá trị thật,
script **không phân biệt được** "người dùng gõ vào" với "argparse điền hộ", nên không thể chặn được
việc dùng nhầm cờ. Chế độ `dia` **không đổi hành vi**: `main()` phân giải `None` về đúng hai giá trị
cũ trước khi dùng, kể cả trong nhánh `--dry-run`. Dòng 49–53 §8 canh điều này.

### 5.2. ★ Một cờ thuộc đúng một chế độ

**Chốt**: dùng cờ của chế độ kia → `main()` trả `1`, thông báo nêu **tên cờ** và **tên chế độ đang
chạy**. Không "bỏ qua kèm cảnh báo".

| Chế độ | Cờ bị cấm |
|---|---|
| `camera` | `--anh-dir`, `--seed` |
| `dia` | `--capture-config`, `--capture-backend`, `--anh-sang`, `--khoang-cach-m`, `--noi-dung-khung` |

Vì sao báo lỗi chứ không cảnh báo: cảnh báo in ra màn hình **biến mất khi đóng cửa sổ**, còn tệp
`.meta.json` thì sống mãi. Một meta của lượt đo camera mang `"seed": 42` và `"anh_dir":
"data/impostor/lfw_original"` là **lời khẳng định sai về tính tái lập** — nó nói rằng lượt đo này lặp
lại được bằng cách cố định seed, trong khi đầu vào là camera thật, không có gì tái lập được. Báo lỗi
tốn của người dùng một lần gõ lại; bỏ qua im lặng tốn của báo cáo độ tin cậy.

Ở chế độ `camera`: `meta["seed"] = None` và `meta["dataset"]` **không** có khoá `anh_dir`.

Kiểm giá trị `--khoang-cach-m`: phải **hữu hạn** (`math.isfinite`) và `> 0`. `argparse` với
`type=float` nhận `inf`, `-inf`, `nan` mà không kêu một tiếng nào — ba giá trị này lọt qua mọi phép
kiểm kiểu và mọi phép so sánh miền thông thường, rồi đi thẳng vào `.meta.json`.

### 5.3. Vòng lặp đo ở chế độ `camera`

```
main() mở camera ĐÚNG MỘT LẦN  →  do_mot_cau_hinh_camera(...)  →  finally: dong()
```

Trong `do_mot_cau_hinh_camera`, với mỗi khung:

1. `t0 = perf_counter()`; `frame = bo_thu_hinh.doc_frame()`; `t1 = perf_counter()`
2. `khuon_mat = detector.detect(frame)`; `t2 = perf_counter()`
3. `latency_lay_khung_ms = (t1 - t0) * 1000`, `latency_ms = (t2 - t1) * 1000`,
   `latency_tong_ms` = tổng hai số trên
4. Đọc nhiệt độ CPU **sau** khi kết thúc cả hai vùng bấm giờ — giữ đúng tiền lệ `:237`

`so_lam_nong` khung đầu chạy đủ cả hai bước nhưng **không** ghi bản ghi.

⛔ `do_mot_cau_hinh_camera` **không được gọi `mo()` hay `dong()`**. Nó nhận vào một `BoThuHinh` **đã
mở**. Lý do: mở lại camera giữa lượt đo làm cảm biến hiệu chỉnh lại phơi sáng, và khung ngay sau khi
mở là khung xấu — `CameraOpenCV.mo()` bỏ `warmup_frames` chính vì thế. Dòng 25–27 §8 canh bằng AST và
bằng bộ đếm.

`doc_frame()` ném `LoiCamera` → **không bắt trong vòng đo**. `main()` bắt, đóng camera trong `finally`,
in thông báo, trả `1`, **không ghi tệp nào**. Lý do: mất camera giữa chừng làm phần khung còn lại
không tồn tại, khác hẳn ca "một ảnh hỏng trong 130 ảnh" của chế độ `dia`. R24 đòi đưa thiết bị về
trạng thái an toàn — ở đây là đóng camera rồi thoát sạch, không phải chạy tiếp với số liệu khuyết.

### 5.4. Mô tả nguồn camera trong meta

```python
def mo_ta_nguon_camera(cfg_capture: dict, backend_thu_hinh: str, khung_mau: np.ndarray) -> dict:
```

`meta["dataset"]` ở chế độ `camera` gồm **tám khoá**, liệt kê đích danh (giá trị có thể `null`,
khoá **luôn phải có mặt**):

| Khoá | Nguồn |
|---|---|
| `backend_thu_hinh` | giá trị `--capture-backend` |
| `do_phan_giai_yeu_cau` | `f"{w}x{h}"` từ `opencv.{width,height}` hoặc `mock.{width,height}` |
| `do_phan_giai_that` | `f"{khung_mau.shape[1]}x{khung_mau.shape[0]}"` |
| `khop_do_phan_giai` | hai chuỗi trên có bằng nhau không |
| `fps_khai_bao_trong_cau_hinh` | `opencv.fps`; backend `mock` → `null` |
| `warmup_frames_thu_hinh` | `opencv.warmup_frames`; backend `mock` → `null` |
| `n_frame_do` | số dòng CSV **thật**, không phải cờ `--n-frames` |
| `n_frame_lam_nong` | `--warmup` |

⛔ `do_phan_giai_that` **phải lấy từ `khung_mau.shape`**, tuyệt đối không từ cấu hình. Webcam từ chối
`cap.set()` một cách im lặng là chuyện thường (§3.4); lấy từ cấu hình thì báo cáo sẽ ghi "1280×720"
trong khi thiết bị trả 640×480, và **không có gì báo lỗi**. Dòng 35–37 §8 và ĐB9 canh chỗ này.

`khop_do_phan_giai is False` → khoá cảnh báo `canh_bao_do_phan_giai` (§5.6). Cảnh báo, không chặn:
độ phân giải khác không làm phép đo sai, chỉ làm nhãn sai — và nhãn sai thì phải sửa nhãn.

### 5.5. Khoá meta mới ở chế độ `camera`

Bốn khoá **mức trên cùng**, ngoài 20 khoá cũ:

| Khoá | Giá trị |
|---|---|
| `nguon` | `"camera"` |
| `conditions` | đủ **ba** khoá con `anh_sang`, `khoang_cach_m`, `noi_dung_khung` |
| `config_file_capture` | đường dẫn `--capture-config` đã phân giải |
| `config_snapshot_capture` | toàn bộ nội dung cấu hình thu hình **sau khi** đã ghi đè `backend` |

`_KHOA_META_BAT_BUOC_CAMERA = _KHOA_META_BAT_BUOC + ("nguon", "conditions", "config_file_capture",
"config_snapshot_capture")` — **24 khoá**.

⚠️ **Bất đối xứng có chủ đích, phải hiểu đúng**: khoá `nguon` được ghi ở **cả hai** chế độ
(`"dia"` / `"camera"`), nhưng **chỉ** danh sách bắt buộc của chế độ `camera` mới đòi nó. Lý do:
`_KHOA_META_BAT_BUOC` đang được tám ca kiểm thử hiện có dựng meta bằng tay để gọi thẳng
`ghi_ket_qua` (`_meta_hop_le()` ở `tests/test_benchmark_detect.py:202-229`); thêm khoá vào danh sách
đó là **đổi hành vi chế độ `dia`**, điều §6 cấm. Ở chế độ `dia`, khoá `nguon` được canh bằng ca test
đi qua `main()` (dòng 51 §8).

**Quy ước đọc tệp cũ**: các tệp `results/bench_detect_*.meta.json` sinh trước mã việc này **không có**
khoá `nguon`. Quy ước: **thiếu khoá ⇒ `"dia"`**. Notebook và Chương 4 phải dùng đúng quy ước này khi
nhóm số liệu.

### 5.6. Bốn khoá cảnh báo — cảnh báo, không chặn

Ghi một khoá **không rỗng** vào meta **và** nối câu cảnh báo vào `notes`:

| Tình huống | Khoá meta |
|---|---|
| `moi_truong != "pi5"` | `canh_bao_hieu_nang` — **hành vi cũ, giữ nguyên** |
| `--capture-backend mock` | `canh_bao_nguon_gia_lap` |
| `khop_do_phan_giai is False` | `canh_bao_do_phan_giai` |
| Nghi bộ đệm khung (§4.1) | `canh_bao_dem_khung` |

Ba khoá sau **chỉ xuất hiện ở chế độ `camera`**, và **chỉ khi** tình huống xảy ra.

Hằng số mới, có tên và có nguồn: `_NGUONG_NGHI_NGO_DEM_KHUNG_MS = 1.0` (một khung lấy về dưới 1 ms
không thể đến từ cảm biến chạy 30–60 khung/s) và `_HE_SO_NGHI_NGO_DEM_KHUNG = 10.0`.

### 5.7. Bộ thu hình giả cho ca kiểm thử

Ca test dựng một lớp con của `src.capture.base.BoThuHinh` với: `mo()`/`dong()` **đếm số lần gọi**;
`doc_frame()` trả mảng `uint8` shape cấu hình được, tuỳ chọn `time.sleep` một khoảng cho trước, tuỳ
chọn ném `LoiCamera` ở khung thứ `k`; `dang_mo` phản ánh trạng thái thật.

Script nhận bộ thu hình qua `tao_bo_thu_hinh`; ca test `monkeypatch` hàm đó **trong không gian tên của
script** (`bd.tao_bo_thu_hinh`), đúng cách các ca hiện có làm với `bd.tao_bo_phat_hien`.

⛔ **Không ca test nào được dùng `--capture-backend opencv`, và tuyệt đối không dùng `auto`.** Máy
phát triển có webcam thật; một ca test lỡ mở nó sẽ chạy được trên máy đó và **hỏng ở mọi nơi khác**.

---

## 6. ★ Chốt chịu lực: chế độ `dia` KHÔNG đổi một chút nào

Đây là ràng buộc quan trọng nhất của mã việc. Bước 2.6 đã đóng, số liệu đã vào Chương 4 §4.3.4
(Bảng 4.4–4.6) và §4.6 Bảng 4.7. Một thay đổi âm thầm ở nhánh `dia` làm toàn bộ số đó mất giá trị mà
không ai biết.

Bốn điều **bất biến**, mỗi điều một cách kiểm bằng máy:

| # | Bất biến | Kiểm ở đâu |
|---|---|---|
| B1 | **72 ca test cũ còn nguyên, không đổi tên, không sửa assert** | §9.1 lệnh đếm `::test_dong` == 72 và lệnh liệt kê dòng bị xoá |
| B2 | `ghi_ket_qua(...)` gọi theo chữ ký cũ vẫn ghi **10 cột** đúng thứ tự cũ | ca test cũ `test_dong27`, `test_dong54` |
| B3 | `_KHOA_META_BAT_BUOC` vẫn **20 khoá**, `_COT_CSV` vẫn **10 cột** | dòng 49–50 §8 |
| B4 | Tệp `results/bench_detect_2026090*.csv` cũ vẫn đọc được bằng `csv.DictReader` với 10 cột | dòng 53 §8 |

Hai hàm cũ `do_mot_cau_hinh` và `tong_hop` **không được sửa thân**. Chức năng mới đi vào **hàm mới**:

- `do_mot_cau_hinh_camera` — không đụng `do_mot_cau_hinh`
- `tong_hop_camera` — không đụng `tong_hop`; `tong_hop` vẫn đọc `latency_ms` và `n_faces`, mà bản ghi
  camera có đủ hai khoá đó, nên **dùng lại nguyên vẹn**, không sao chép

`ghi_ket_qua` là hàm duy nhất được mở rộng, và chỉ bằng **hai tham số có mặc định**:

```python
def ghi_ket_qua(
    thu_muc: Path,
    run_id: str,
    ban_ghi: list[dict],
    meta: dict,
    cot: list[str] | None = None,
    khoa_bat_buoc: tuple[str, ...] | None = None,
) -> tuple[Path, Path]:
```

`cot=None` ⇒ `_COT_CSV`; `khoa_bat_buoc=None` ⇒ `_KHOA_META_BAT_BUOC`. Mọi lời gọi cũ giữ nguyên nghĩa.

---

## 7. Giao diện hàm — giữ nguyên tên và kiểu

```python
def do_mot_cau_hinh_camera(
    duong_dan_mo_hinh: Path,
    cfg: dict,
    bo_thu_hinh: BoThuHinh,
    so_luong: int,
    so_lam_nong: int,
) -> list[dict]:
    """Đo một cấu hình với khung hình lấy trực tiếp từ bộ thu hình ĐÃ MỞ.

    Args:
        duong_dan_mo_hinh: Đường dẫn mô hình cần đo.
        cfg: Cấu hình phát hiện (đã đặt sẵn inference.num_threads).
        bo_thu_hinh: Bộ thu hình **đã gọi `mo()`**. Hàm này KHÔNG mở và KHÔNG đóng nó.
        so_luong: Số khung hình cần đo (không tính khung làm nóng).
        so_lam_nong: Số khung chạy làm nóng trước, không ghi bản ghi.

    Returns:
        Danh sách bản ghi, mỗi khung một bản ghi, gồm các khoá `backend`, `imgsz`,
        `sample_idx`, `latency_lay_khung_ms`, `latency_ms`, `latency_tong_ms`,
        `fps_instant`, `fps_tong_instant`, `n_faces`, `conf_top`, `cpu_temp_c`.

    Raises:
        LoiMoHinh: không nạp được mô hình.
        LoiCauHinh: cấu hình sai, hoặc `so_luong` < 1.
        LoiCamera: bộ thu hình chưa mở, hoặc đọc khung thất bại — KHÔNG bắt tại đây.
    """


def tong_hop_camera(ban_ghi: list[dict]) -> dict:
    """Tổng hợp phần số liệu riêng của chế độ camera.

    Returns:
        Từ điển gồm `lay_khung_tb`, `lay_khung_do_lech`, `lay_khung_p50`, `lay_khung_p95`,
        `tong_tb`, `tong_do_lech`, `tong_p50`, `tong_p95`, `fps_tong_tb`,
        `dat_chi_tieu_tong`. Không khoá nào trùng với `tong_hop`.

    Raises:
        LoiCauHinh: danh sách bản ghi rỗng.
    """


def mo_ta_nguon_camera(cfg_capture: dict, backend_thu_hinh: str, khung_mau: np.ndarray) -> dict:
    """Dựng khối `meta.dataset` cho chế độ camera — xem §5.4, đủ tám khoá.

    Raises:
        LoiCauHinh: `backend_thu_hinh` không thuộc {"opencv", "mock"}, hoặc thiếu nhánh
            cấu hình tương ứng.
    """
```

`dat_chi_tieu_tong = fps_tong_tb >= NGUONG_FPS_TOI_THIEU`, dùng lại đúng hằng số cũ, **không** thêm
ngưỡng mới.

⚠️ Phân biệt hai kết luận, phải in ra và phải ghi trong báo cáo:
`dat_chi_tieu` (từ `tong_hop`, dựa trên `fps_tb`) là kết luận cho **chỉ tiêu §1 "FPS riêng module
detect ≥ 10"**. `dat_chi_tieu_tong` là **số bổ sung** mô tả đường vào camera + phát hiện; nó **không**
phải chỉ tiêu "FPS toàn pipeline ≥ 5" vì pipeline còn có anti-spoofing và nhận diện chưa tích hợp.

`tom_tat` ở chế độ camera: `tom_tat[<khoá ô>] = {**tong_hop(ban_ghi), **tong_hop_camera(ban_ghi)}`,
đúng một ô.

`run_id` ở chế độ camera: `f"bench_detect_camera_{YYYYMMDD_HHMM}"`. Chế độ `dia` giữ nguyên
`f"bench_detect_{YYYYMMDD_HHMM}"`. Lý do tách tên: `results/` đã có 4 tệp `bench_detect_2026090*` của
bước 2.6; một tệp camera trùng khuôn tên sẽ lọt vào mọi phép `glob` gom số bước 2.6 và trộn hai loại
số vào một bảng. Tên khác nhau là hàng rào thứ nhất, khoá `nguon` là hàng rào thứ hai, số cột CSV
khác nhau (13 so với 10) là hàng rào thứ ba — hàng rào thứ ba làm phép trộn nhầm **hỏng to tiếng**
thay vì sai im lặng.

Cột CSV chế độ camera, đúng thứ tự — **13 cột**:

```csv
run_id,backend,imgsz,threads,sample_idx,latency_lay_khung_ms,latency_ms,latency_tong_ms,fps_instant,fps_tong_instant,n_faces,conf_top,cpu_temp_c
```

`fps_instant = 1000 / latency_ms` (giữ nguyên nghĩa cũ: FPS của riêng suy luận).
`fps_tong_instant = 1000 / latency_tong_ms`.

Bảng in ra cuối ở chế độ camera phải có: `fps_tb`, `fps_tong_tb`, `lay_khung_p50`, `lay_khung_p95`,
`latency_p50`, `latency_p95`, `ti_le_phat_hien`, kết luận `dat_chi_tieu`, và **một dòng chữ** giải
thích trần tốc độ khung theo §4.1.

---

## 8. Bảng tiêu chí nghiệm thu

Mỗi dòng là **một ca test** tên `test_camera_dong<nn>` trong `tests/test_benchmark_detect.py`,
**nối vào cuối tệp**. Tiền tố `test_camera_dong` là bắt buộc — lệnh đếm ở §9.1 dựa vào nó để tách ca
mới khỏi 72 ca cũ. Mỗi ô "Assert tối thiểu" là **một** điều kiện; không gộp.

### 8.1. Cờ, chế độ và ranh giới giữa hai chế độ (§5.1, §5.2)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Không truyền `--nguon` → chạy chế độ `dia`, meta ghi đúng | `meta["nguon"] == "dia"` |
| 02 | `--nguon lung-tung` → argparse thoát | `pytest.raises(SystemExit)` |
| 03 | `--nguon camera` thiếu `--capture-backend` → `main()` trả `1` | `main([...]) == 1` |
| 04 | Cùng tình huống 03: thông báo nêu tên cờ | `capsys`: đầu ra chứa `"--capture-backend"` |
| 05 | `--capture-backend auto` → argparse thoát | `pytest.raises(SystemExit)` |
| 06 | `--nguon camera` + `--anh-dir` → `main()` trả `1` | `main([...]) == 1` |
| 07 | Cùng tình huống 06: thông báo nêu tên cờ | `capsys`: đầu ra chứa `"--anh-dir"` |
| 08 | `--nguon camera` + `--seed` → `main()` trả `1` | `main([...]) == 1` |
| 09 | Cùng tình huống 08: thông báo nêu tên cờ | `capsys`: đầu ra chứa `"--seed"` |
| 10 | `--nguon dia` + `--anh-sang` → `main()` trả `1` | `main([...]) == 1` |
| 11 | Cùng tình huống 10: thông báo nêu tên cờ | `capsys`: đầu ra chứa `"--anh-sang"` |
| 12 | `--nguon dia` + `--capture-backend mock` → `main()` trả `1` | `main([...]) == 1` |
| 13 | `--nguon camera` thiếu `--anh-sang` → `main()` trả `1` | `main([...]) == 1` |
| 14 | `--nguon camera` thiếu `--khoang-cach-m` → `main()` trả `1` | `main([...]) == 1` |
| 15 | `--nguon camera` thiếu `--noi-dung-khung` → `main()` trả `1` | `main([...]) == 1` |
| 16 | `--noi-dung-khung dung-dau` → argparse thoát | `pytest.raises(SystemExit)` |
| 17 | `--khoang-cach-m 0` → `main()` trả `1` | `main([...]) == 1` |
| 18 | `--khoang-cach-m -1` → `main()` trả `1` | `main([...]) == 1` |
| 19 | ★ `--khoang-cach-m inf` → `main()` trả `1` | `main([...]) == 1` |
| 20 | ★ `--khoang-cach-m -inf` → `main()` trả `1` | `main([...]) == 1` |
| 21 | ★ `--khoang-cach-m nan` → `main()` trả `1` | `main([...]) == 1` |
| 22 | Cặp đối chứng 17–21: `--khoang-cach-m 1.0` → `main()` trả `0` | `main([...]) == 0` |
| 23 | Cùng tình huống 22: giá trị vào meta đúng | `meta["conditions"]["khoang_cach_m"] == pytest.approx(1.0)` |
| 24 | `--nguon camera` → `meta["seed"]` là `null` | `meta["seed"] is None` |

### 8.2. ★★ Ranh giới bấm giờ (§4.1) — phần chịu lực

Mọi ca dưới đây gọi **thẳng** `do_mot_cau_hinh_camera` với `so_luong=5`, `so_lam_nong=1`, bộ thu hình
giả `sleep` **40 ms** mỗi `doc_frame`, bộ phát hiện giả `sleep` **2 ms** mỗi `detect`.

Số đo kỳ vọng, ghi ra để người review kiểm được dung sai nằm giữa hai nhóm:

| Cài đặt | `latency_lay_khung_ms` | `latency_ms` |
|---|---|---|
| **Đúng** | ≈ 40–43 | ≈ 2–5 |
| **Sai — hai cột hoán đổi** (ĐB2) | ≈ 2–5 | ≈ 40–43 |
| **Sai — cả hai vùng ôm trọn vòng lặp** (ĐB1) | ≈ 42–46 | ≈ 42–46 |

Cách chọn hai mốc: tách 20 lần (40 so với 2) chứ không phải 20 % — trên container QEMU tải nặng, chi
phí Python mỗi vòng có thể lên vài ms, nên mọi mốc dựa trên chênh lệch nhỏ đều sẽ bập bênh.

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 25 | ★ Vùng lấy khung đo đúng phần lấy khung | `all(r["latency_lay_khung_ms"] > 30 for r in bg)` |
| 26 | ★ Vùng suy luận đo đúng phần suy luận | `all(r["latency_ms"] < 20 for r in bg)` |
| 27 | ★ `latency_tong_ms` là **tổng số học**, từng dòng | `all(abs(r["latency_tong_ms"] - r["latency_lay_khung_ms"] - r["latency_ms"]) < 1e-9 for r in bg)` |
| 28 | `fps_instant` là nghịch đảo của `latency_ms` | `all(r["fps_instant"] == pytest.approx(1000.0 / r["latency_ms"]) for r in bg)` |
| 29 | `fps_tong_instant` là nghịch đảo của `latency_tong_ms` | `all(r["fps_tong_instant"] == pytest.approx(1000.0 / r["latency_tong_ms"]) for r in bg)` |
| 30 | Số bản ghi đúng `so_luong`, không tính khung làm nóng | `len(bg) == 5` |
| 31 | Bộ thu hình được đọc đủ `so_lam_nong + so_luong` lần | `cam_gia.so_lan_doc == 6` |
| 32 | `sample_idx` liên tục từ 0 | `[r["sample_idx"] for r in bg] == [0, 1, 2, 3, 4]` |
| 33 | `backend` và `imgsz` đọc từ đối tượng phát hiện | `bg[0]["imgsz"] == 320` với bộ phát hiện giả khai 320 |
| 34 | `so_luong` < 1 → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |

### 8.3. Vòng đời camera và fail-safe (§5.3)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 35 | ★ `main()` mở camera **đúng một lần** | `cam_gia.so_lan_mo == 1` |
| 36 | ★ `do_mot_cau_hinh_camera` **không** gọi `mo()`/`dong()` — quét AST thân hàm | `vi_pham == []` với tập cấm `{"mo", "dong"}` (mẫu theo `test_dong16`) |
| 37 | `main()` đóng camera ở đường thành công | `cam_gia.so_lan_dong >= 1` |
| 38 | ★ `doc_frame` ném `LoiCamera` giữa chừng → `main()` trả `1` | `main([...]) == 1` |
| 39 | Cùng tình huống 38: camera vẫn được đóng (fail-safe R24) | `cam_gia.so_lan_dong >= 1` |
| 40 | Cùng tình huống 38: **không** tệp nào được ghi | `list(thu_muc_ket_qua.rglob("*")) == []` |
| 41 | Cùng tình huống 38: thông báo nêu nguyên nhân camera | `capsys`: đầu ra chứa `"camera"` |
| 42 | Cặp đối chứng 38: camera bình thường → `main()` trả `0` | `main([...]) == 0` |
| 43 | ★ `--dry-run` ở chế độ camera **không mở camera** | `monkeypatch` `tao_bo_thu_hinh` ném `AssertionError` ⇒ `main([..., "--dry-run"]) == 0` |
| 44 | Cùng tình huống 43: **không** tệp nào được ghi | `list(thu_muc_ket_qua.rglob("*")) == []` |
| 45 | Bảng dry-run camera nêu backend thu hình | `capsys`: đầu ra chứa `"mock"` |

### 8.4. Một cấu hình, không ma trận (§4.2)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 46 | `--nguon camera` với **hai** mô hình → `main()` trả `1` | `main([...]) == 1` |
| 47 | Cùng tình huống 46: thông báo nêu `--models` | `capsys`: đầu ra chứa `"--models"` |
| 48 | `--nguon camera` với `--threads 1 2` → `main()` trả `1` | `main([...]) == 1` |
| 49 | Cùng tình huống 48: thông báo nêu `--threads` | `capsys`: đầu ra chứa `"--threads"` |
| 50 | Cặp đối chứng 46–49: một mô hình, một mức luồng → `main()` trả `0` | `main([...]) == 0` |
| 51 | Cùng tình huống 50: `tom_tat` có **đúng một** ô | `len(meta["tom_tat"]) == 1` |

### 8.5. ★ Không hồi quy chế độ `dia` (§6)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 52 | `_COT_CSV` vẫn **10 cột**, đúng thứ tự | `bd._COT_CSV == [<10 tên nguyên văn §3.1>]` |
| 53 | `_KHOA_META_BAT_BUOC` vẫn **20 khoá** | `len(bd._KHOA_META_BAT_BUOC) == 20` |
| 54 | ★ Mặc định `--anh-dir` sau khi phân giải đúng giá trị cũ | Chạy `main()` chế độ `dia` không truyền cờ ⇒ `meta["dataset"]["anh_dir"] == "data/impostor/lfw_original"` |
| 55 | ★ Mặc định `--seed` sau khi phân giải đúng giá trị cũ | Cùng lượt chạy ⇒ `meta["seed"] == 42` |
| 56 | Bảng `--dry-run` chế độ `dia` vẫn in thư mục ảnh mặc định | `capsys`: đầu ra chứa `"lfw_original"` |
| 57 | `ghi_ket_qua` gọi theo **chữ ký cũ** vẫn ghi 10 cột | `header == [<10 tên>]` (gọi 4 tham số như `test_dong27`) |
| 58 | ★ Tệp CSV cũ vẫn đọc được | Ghi tệp bằng chữ ký cũ rồi `csv.DictReader` ⇒ `len(rows[0]) == 10` |

### 8.6. CSV và metadata chế độ camera (§5.4, §5.5, §7)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 59 | Ghi **đúng hai** tệp | `len(list(thu_muc.iterdir())) == 2` |
| 60 | Tên CSV đúng khuôn camera | `re.fullmatch(r"bench_detect_camera_\d{8}_\d{4}\.csv", p_csv.name)` |
| 61 | Tên meta đúng khuôn camera | `re.fullmatch(r"bench_detect_camera_\d{8}_\d{4}\.meta\.json", p_meta.name)` |
| 62 | CSV camera đúng **13 cột**, đúng thứ tự | So `next(csv.reader(f))` với danh sách 13 tên nguyên văn §7 |
| 63 | Số dòng CSV bằng `--n-frames` | `len(rows) == 100` |
| 64 | `meta["nguon"]` bằng `"camera"` | `meta["nguon"] == "camera"` |
| 65 | Meta đủ **24 khoá** bắt buộc | `set(meta) >= set(bd._KHOA_META_BAT_BUOC_CAMERA)` |
| 66 | `conditions` đủ **ba** khoá con | `set(meta["conditions"]) == {"anh_sang","khoang_cach_m","noi_dung_khung"}` |
| 67 | `meta["dataset"]` đủ **tám** khoá con | `set(meta["dataset"]) == {"backend_thu_hinh","do_phan_giai_yeu_cau","do_phan_giai_that","khop_do_phan_giai","fps_khai_bao_trong_cau_hinh","warmup_frames_thu_hinh","n_frame_do","n_frame_lam_nong"}` |
| 68 | `meta["dataset"]` **không** có `anh_dir` | `"anh_dir" not in meta["dataset"]` |
| 69 | ★ `do_phan_giai_that` lấy từ khung, không từ cấu hình | Cấu hình khai `1280x720`, camera giả trả khung `(480, 640, 3)` ⇒ `meta["dataset"]["do_phan_giai_that"] == "640x480"` |
| 70 | Cùng tình huống 69: `do_phan_giai_yeu_cau` vẫn ghi giá trị cấu hình | `meta["dataset"]["do_phan_giai_yeu_cau"] == "1280x720"` |
| 71 | Cùng tình huống 69: `khop_do_phan_giai` là `False` | `meta["dataset"]["khop_do_phan_giai"] is False` |
| 72 | Cùng tình huống 69: có cảnh báo không rỗng | `meta["canh_bao_do_phan_giai"] != ""` |
| 73 | Cặp đối chứng 69–72: khung khớp cấu hình → **không** có khoá đó | `"canh_bao_do_phan_giai" not in meta` |
| 74 | `n_frame_do` là **số dòng thật**, không phải cờ | `meta["dataset"]["n_frame_do"] == len(rows)` |
| 75 | `fps_khai_bao_trong_cau_hinh` là `null` với backend `mock` | `meta["dataset"]["fps_khai_bao_trong_cau_hinh"] is None` |
| 76 | ★ Backend `mock` sinh cảnh báo nguồn giả lập không rỗng | `meta["canh_bao_nguon_gia_lap"] != ""` |
| 77 | Cùng tình huống 76: câu cảnh báo cũng vào `notes` | `"giả lập" in meta["notes"]` |
| 78 | `config_snapshot_capture` ghi backend **đã ghi đè**, không phải `auto` | `meta["config_snapshot_capture"]["backend"] == "mock"` |
| 79 | Cấu hình thu hình hỏng → `main()` trả `1` | `main([...]) == 1` với `--capture-config` trỏ tệp không tồn tại |
| 80 | Meta camera thiếu `conditions` → `ghi_ket_qua` ném `LoiCauHinh` | `pytest.raises(LoiCauHinh)` khi truyền `khoa_bat_buoc=bd._KHOA_META_BAT_BUOC_CAMERA` |
| 81 | Cặp đối chứng 80: meta đủ khoá → ghi thành công | Cả hai tệp `.exists()` |
| 82 | `mo_ta_nguon_camera` với backend lạ → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 83 | `cpu_temp_c` rỗng khi không có cảm biến | Ô tương ứng là chuỗi rỗng, **không** phải `"None"` |

### 8.7. Tổng hợp và bảng in ra (§7)

Mọi ca dưới đây dựng bản ghi **bằng tay**, không chạy mô hình, không chạy camera.

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 84 | `lay_khung_tb` khớp `np.mean` | 100 bản ghi ⇒ `pytest.approx(np.mean(v))` |
| 85 | `lay_khung_do_lech` khớp `np.std` | Cùng dữ liệu ⇒ `pytest.approx(np.std(v))` |
| 86 | `lay_khung_p50` khớp `np.percentile` | Cùng dữ liệu ⇒ `pytest.approx(np.percentile(v, 50))` |
| 87 | `lay_khung_p95` khớp `np.percentile` | Cùng dữ liệu ⇒ `pytest.approx(np.percentile(v, 95))` |
| 88 | `tong_p95` khớp `np.percentile` trên cột tổng | Cùng dữ liệu ⇒ `pytest.approx(np.percentile(v_tong, 95))` |
| 89 | `fps_tong_tb` là nghịch đảo `tong_tb` | Tổng đều 50 ms ⇒ `pytest.approx(20.0)` |
| 90 | `dat_chi_tieu_tong` đúng trên ngưỡng | Tổng đều 50 ms ⇒ `kq["dat_chi_tieu_tong"] is True` |
| 91 | `dat_chi_tieu_tong` đúng dưới ngưỡng | Tổng đều 200 ms ⇒ `kq["dat_chi_tieu_tong"] is False` |
| 92 | ★ `tong_hop` cũ dùng lại được trên bản ghi camera | `bd.tong_hop(bg_camera)["fps_tb"] == pytest.approx(1000.0 / np.mean(lat_detect))` |
| 93 | ★ Hai từ điển tổng hợp **không trùng khoá nào** | `set(bd.tong_hop(bg)) & set(bd.tong_hop_camera(bg)) == set()` |
| 94 | Bản ghi rỗng → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 95 | Bảng in ra có cột FPS đầu-cuối | `capsys`: đầu ra chứa `"đầu-cuối"` |
| 96 | Bảng in ra nêu trần tốc độ khung | `capsys`: đầu ra chứa `"trần"` |
| 97 | ★ Nghi bộ đệm khung → cảnh báo không rỗng | Camera giả `doc_frame` không sleep, detect sleep 40 ms ⇒ `meta["canh_bao_dem_khung"] != ""` |
| 98 | Cặp đối chứng 97: lấy khung chậm hơn suy luận → **không** có khoá đó | `"canh_bao_dem_khung" not in meta` |
| 99 | Ngoài `pi5` vẫn có `canh_bao_hieu_nang` ở chế độ camera | `meta["canh_bao_hieu_nang"] != ""` |
| 100 | `moi_truong` thuộc ba mã hợp lệ | `meta["moi_truong"] in {"pc_x86","docker_arm64","pi5"}` |

**Không ca nào mang `@pytest.mark.slow`, không ca nào cần `models/`, không ca nào cần camera thật,
không ca nào chạm mạng.** Mọi ca ghi tệp phải `monkeypatch` `bd._THU_MUC_KET_QUA_MAC_DINH` ra
`tmp_path`.

---

## 9. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

### 9.0. Lấy mốc TRƯỚC khi sửa bất kỳ dòng nào

```bash
python -m pytest -q
```

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

Kỳ vọng lệnh đầu: **689 passed** (§3.3). Lệnh thứ hai: **chưa có mốc ghi lại** — con số bạn thu được
chính là mốc, ghi lại rồi mới bắt đầu sửa mã.

### 9.1. Sau khi cài đặt xong

```bash
python -m black --check --line-length 100 scripts/benchmark_detect.py tests/test_benchmark_detect.py
```

```bash
python -m ruff check scripts/benchmark_detect.py tests/test_benchmark_detect.py
```

```bash
python -m pytest tests/test_benchmark_detect.py -q
```

Kỳ vọng: **mọi ca xanh, 0 skipped**. Một ca `skipped` nghĩa là ca đó đang phụ thuộc `models/`,
`data/` hoặc camera thật — sai §3.5, sửa ca test.

```bash
python -m pytest tests/test_benchmark_detect.py --collect-only -q | grep -c "::test_dong"
```

Kỳ vọng: **đúng `72`**. Đây là chốt B1 §6 — 72 ca cũ còn nguyên tên. Ca mới mang tiền tố
`test_camera_dong` nên không lọt vào phép đếm này.

```bash
python -m pytest tests/test_benchmark_detect.py --collect-only -q | grep -c "::test_camera_dong"
```

Kỳ vọng: **≥ 100** — mỗi dòng §8 ít nhất một ca.

```bash
git diff dev -- tests/test_benchmark_detect.py | grep "^-[^-]"
```

Kỳ vọng: **chỉ những dòng `import`**. Mọi dòng khác bị xoá hoặc sửa trong tệp test là vi phạm chốt B1
— liệt kê từng dòng và giải trình khi báo cáo.

```bash
python -m pytest -q
```

Kỳ vọng: `689 + <số ca mới>` passed, `0 failed`, `0 skipped`. Ghi con số thật bạn thấy.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

Kỳ vọng: số `passed` tăng **đúng bằng** số ca mới trên host. Lệch nghĩa là có ca đang phụ thuộc thứ
container không có (§3.5).

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest --collect-only -q tests/test_benchmark_detect.py
```

Kỳ vọng: thu thập **đủ** số ca, **không** lỗi import. Lệnh này bắt riêng chế độ hỏng "import ở mức
module một thứ container không có".

```bash
git status --short --untracked-files=all
```

Kỳ vọng: **đúng hai** tệp của §2. Cờ `--untracked-files=all` là bắt buộc — thiếu nó git gộp cả thư
mục mới thành một dòng và phép đếm sai.

### 9.2. Quét mẫu vi phạm

```bash
grep -n "except Exception" scripts/benchmark_detect.py
```

Phải **rỗng**.

```bash
grep -nE "raise (ValueError|TypeError|Exception)" scripts/benchmark_detect.py
```

Phải **rỗng** — ngoại lệ dùng lớp trong `src/common/exceptions.py`.

```bash
grep -nE "\bauto\b" scripts/benchmark_detect.py
```

Giải trình **từng dòng** không rỗng. Chỉ được xuất hiện ở chuỗi thông báo/trợ giúp giải thích vì sao
`auto` bị cấm (§4.3). **Không** được xuất hiện trong `choices` của `--capture-backend`.

```bash
grep -nE "CAP_PROP|VideoCapture" scripts/benchmark_detect.py
```

Phải **rỗng**. Script **không** được nói chuyện thẳng với OpenCV về camera — mọi truy cập đi qua
`src/capture` (R22). Đây cũng là điều làm ca test chạy được trong container không có camera.

```bash
grep -nE "\b(30|33|1280|720|640|480)\b" scripts/benchmark_detect.py
```

Giải trình **từng dòng** không rỗng. Không được có độ phân giải hay tốc độ khung viết cứng — chúng
đến từ `configs/capture.yaml` và từ `frame.shape` (§5.4). Giá trị mặc định của tham số CLI đã có từ
trước không tính.

```bash
grep -nE "^_COT_CSV = |^_KHOA_META_BAT_BUOC = " -A 2 scripts/benchmark_detect.py
```

Kỳ vọng: hai hằng số cũ còn nguyên vị trí, **không** bị đổi tên hay gộp (chốt B3 §6).

---

## 10. Phép đột biến bắt buộc

Mỗi phép: sao lưu tệp **ra ngoài repo** → sửa → chạy `pytest tests/test_benchmark_detect.py -q` → ghi
ca đỏ → khôi phục → đối chiếu `sha256`. Tuyệt đối không `git checkout -- <tệp>`.

| # | Phép đột biến | Ca **phải** đỏ |
|---|---|---|
| ĐB1 | Cả hai vùng bấm giờ ôm trọn vòng lặp (`lay_khung` và `latency_ms` cùng đo `doc_frame + detect`) | 26 |
| ĐB2 | ★★ **Hoán đổi hai cột**: ghi thời gian `detect` vào `latency_lay_khung_ms` và ngược lại | 25, 26 |
| ĐB3 | `latency_tong_ms` đo bằng một cặp `perf_counter()` thứ ba bao ngoài, thay vì cộng | 27 |
| ĐB4 | Gọi `bo_thu_hinh.mo()` bên trong vòng đo | 35, 36 |
| ĐB5 | Bỏ `finally: dong()` ở đường lỗi | 39 |
| ĐB6 | Bỏ chốt "đúng một mô hình, đúng một mức luồng" | 46, 48 |
| ĐB7 | Bỏ chốt cờ sai chế độ, chuyển thành cảnh báo | 06, 10 |
| ĐB8 | Bỏ `math.isfinite` khi kiểm `--khoang-cach-m` | 19, 20, 21 |
| ĐB9 | ★ `do_phan_giai_that` lấy từ cấu hình thay vì từ `khung_mau.shape` | 69 |
| ĐB10 | Bỏ khoá `nguon` khỏi meta | 01, 64 |
| ĐB11 | Dùng `_COT_CSV` (10 cột) cho chế độ camera | 62 |
| ĐB12 | Thêm `"nguon"` vào `_KHOA_META_BAT_BUOC` | 53 **và ít nhất một ca cũ** `test_dong25`–`test_dong33` |
| ĐB13 | Bỏ ghi đè `backend` bằng `--capture-backend`, để nguyên `auto` của cấu hình | 78 |
| ĐB14 | Bỏ chốt nghi bộ đệm khung | 97 |
| ĐB15 | Đổi `default` của `--anh-dir` về chuỗi cũ thay vì `None` (mất khả năng phát hiện cờ sai chế độ) | 06 |

★★ **ĐB2 là phép quan trọng nhất.** Nó dựng lại một cài đặt **tự nhất quán**: hai vùng bấm giờ vẫn
tách rời, tổng vẫn cộng khớp từng dòng, số cột vẫn đúng, `fps_instant` vẫn khớp nghịch đảo — **mọi ca
kiểm cấu trúc đều xanh**. Chỉ độ lớn phân biệt được đúng và sai. Nếu ĐB2 không làm ca nào đỏ thì dòng
25–26 chưa canh đúng chỗ; sửa ca test, đừng sửa mã sản phẩm.

**ĐB12** canh chiều ngược lại của chốt B3: nếu người cài đặt "làm cho chặt hơn" bằng cách bắt buộc
khoá `nguon` ở cả hai chế độ thì các ca cũ dựng meta bằng tay sẽ đỏ — đó là bằng chứng phép đổi ấy
**có** làm đổi hành vi chế độ `dia`, đúng thứ §6 cấm.

---

## 11. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black --line-length 100`, `ruff` sạch. Type hints, docstring tiếng Việt kiểu Google.
- **Thư viện được phép**: thư viện chuẩn (`argparse`, `csv`, `json`, `math`, `random`, `datetime`,
  `platform`, `subprocess`, `time`, `importlib.metadata`, `pathlib`), cộng `numpy`, `cv2`,
  `onnxruntime`, và `src/**` + `scripts/**` của dự án. **Không thêm phụ thuộc mới.**
- Truy cập camera **chỉ qua `src.capture.tao_bo_thu_hinh`** (R22). Không `cv2.VideoCapture` trực tiếp
  — §9.2 có lệnh `grep` canh.
- Đo thời gian bằng `time.perf_counter()`, không `time.time()`.
- `logging` qua `src.common.logging.lay_logger`; `print()` chỉ cho bảng tóm tắt CLI (G2).
- Log lazy formatting (G3).
- Đọc cấu hình qua `src.common.config.nap_cau_hinh`.
- Ngoại lệ: `LoiCauHinh` cho lỗi cấu hình/đầu vào, `LoiCamera` cho lỗi thu hình, `LoiMoHinh` cho lỗi
  mô hình. Không `except Exception` trần.
- Ca test **không được** ghi vào `results/` thật — `monkeypatch` `bd._THU_MUC_KET_QUA_MAC_DINH`.
- Chạy được trên Windows lẫn Linux: `pathlib`, `newline=""` khi mở CSV, `encoding="utf-8"`.
- **Không chạy** `scripts/benchmark_detect.py` ở chế độ ghi thật — đó là lượt của người dùng §12b.
- Không commit, không dựng image, không `pip install`.

**Có tồn tại cách cài đặt thoả mọi ràng buộc §2, §5, §6, §8, §11 cùng lúc không?** Có, và nó dùng
những thứ sau, đều đã có trong `requirements.txt` hoặc trong repo: `src.capture.tao_bo_thu_hinh` (đã
có, không sửa), `numpy` (đã có), `math.isfinite` (thư viện chuẩn), hai tham số mặc định thêm vào
`ghi_ket_qua` (không đổi lời gọi cũ), hai hàm mới đứng cạnh hai hàm cũ. Ca kiểm thử dựng bộ thu hình
giả bằng cách kế thừa `BoThuHinh` và trả mảng `numpy` — **không cần camera, không cần `cv2`, không
cần tệp ảnh**, nên chạy được trong container.

---

## 12. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Sửa `src/capture/**`.** Kể cả việc thêm `cv2.CAP_PROP_FPS` vào `CameraOpenCV` (§3.4) hay phơi ra
  độ phân giải thật — cả hai đều hợp lý và **đều là mã việc riêng**, ghi lại đây để không quên.
- **Đa luồng, tách thread thu hình khỏi thread suy luận.** Đó là bước 6.7 (tối ưu hiệu năng). Mã việc
  này đo đường vào **tuần tự**, và chính con số của nó là căn cứ định lượng để quyết định có cần tách
  luồng hay không.
- **Frame skipping, tracking, bộ đệm khung tự viết.** Bước 6.7.
- **Đo RAM đỉnh, đọc `vcgencmd get_throttled`.** `benchmark_detect.py` hiện không làm, mã việc này
  không thêm.
- **Đổi `ghi_ket_qua` thành từ chối ghi đè tệp** (như `P3-05` làm). Đó là đổi hành vi chế độ `dia`.
- **Vẽ hình, viết notebook, cập nhật Chương 4.** Cổng D, sau khi có số của §12b.
- **Chốt lại cấu hình triển khai chính thức.** Bước 2.6 đã chốt; mã việc này chỉ bổ sung một góc nhìn.

---

## 12a. Việc người dùng phải làm TRƯỚC khi chạy §12b

Không có khoá cấu hình mới. Chỉ cần: **gộp nhánh và commit trước khi đo**, để `.meta.json` ghi
`git_dirty: false` (`experiment-protocol` §9). Đo trên cây làm việc bẩn thì số liệu không tái lập được
và không dùng cho báo cáo.

## 12b. Lượt chạy thật — NGƯỜI DÙNG chạy, sau khi §9 xanh

⭐ Đây là điểm mấu chốt của mã việc: phép đo này **chỉ có nghĩa trên phần cứng đích với camera thật**.
Số từ `pc_x86` hay từ backend `mock` **không** kết luận được gì cho Cổng C.

### Lệnh 1 — kiểm chức năng trên máy phát triển, backend giả lập

```bash
python scripts/benchmark_detect.py --nguon camera --capture-backend mock --models models/yolov8n-face-320.onnx --threads 4 --n-frames 100 --anh-sang "không áp dụng — khung tổng hợp" --khoang-cach-m 1.0 --noi-dung-khung khong-nguoi --device-name "PC phát triển" --ghi-chu "kiểm chức năng, không phải số báo cáo"
```

Kỳ vọng: mã trả về `0`; hai tệp `results/bench_detect_camera_*`; meta có **cả ba** khoá
`canh_bao_nguon_gia_lap`, `canh_bao_hieu_nang`, và `nguon == "camera"`. Giữ lại tệp, commit, nhưng
**không trích vào báo cáo** ngoài mục mô tả quy trình.

### Lệnh 2 — dry-run, xác nhận không chạm camera

```bash
python scripts/benchmark_detect.py --nguon camera --capture-backend opencv --models models/yolov8n-face-320_ncnn_model --threads 4 --anh-sang "trong nhà" --khoang-cach-m 1.0 --noi-dung-khung co-nguoi --device-name "Raspberry Pi 5 8GB" --dry-run
```

Kỳ vọng: in kế hoạch, mã trả về `0`, **không** tệp nào được ghi, **đèn camera không sáng**.

### Điều kiện đo cho các lệnh trên Pi 5 — cố định trong suốt phiên

| Yếu tố | Giá trị |
|---|---|
| Thiết bị | Raspberry Pi 5 8 GB, webcam USB |
| Cấu hình mô hình | NCNN 320 px, 4 luồng — cấu hình nhanh nhất của bước 2.6 (60,6 FPS) |
| Khoảng cách | **1,0 m**, đánh dấu vạch trên sàn để lặp lại được |
| Vị trí camera | cố định, không dời giữa các lượt |
| Cỡ mẫu | `--n-frames 300` ≈ 10 s ở 30 khung/s, vượt mức tối thiểu 100 khung của R9 |
| Tản nhiệt / nguồn | ghi vào `--ghi-chu` đúng như thực tế |
| Trạng thái nhiệt | chạy lệnh 3 trước, nghỉ ~2 phút giữa các lượt; ghi vào `--ghi-chu` lượt nào chạy trước |

### Lệnh 3 — Pi 5, ánh sáng đủ, có người trong khung

```bash
python scripts/benchmark_detect.py --nguon camera --capture-backend opencv --models models/yolov8n-face-320_ncnn_model --threads 4 --n-frames 300 --anh-sang "trong nhà, đèn LED trần, ~300 lux" --khoang-cach-m 1.0 --noi-dung-khung co-nguoi --device-name "Raspberry Pi 5 8GB" --ghi-chu "tản nhiệt <ghi thật>, nguồn <ghi thật>, máy nguội, lượt 1"
```

Kỳ vọng: mã trả về `0`; `ti_le_phat_hien` gần 100 %; `fps_tb` cùng bậc với 60,6 FPS của bước 2.6;
`fps_tong_tb` **thấp hơn hẳn** và bị chặn quanh tốc độ khung của webcam. Meta **không** có
`canh_bao_hieu_nang` (đang ở `pi5`).

### Lệnh 4 — Pi 5, ánh sáng yếu, có người trong khung

```bash
python scripts/benchmark_detect.py --nguon camera --capture-backend opencv --models models/yolov8n-face-320_ncnn_model --threads 4 --n-frames 300 --anh-sang "trong nhà ban đêm, chỉ đèn ngủ, rèm kín" --khoang-cach-m 1.0 --noi-dung-khung co-nguoi --device-name "Raspberry Pi 5 8GB" --ghi-chu "tản nhiệt <ghi thật>, nguồn <ghi thật>, lượt 2, cùng vị trí camera với lượt 1"
```

Kỳ vọng: đủ điều kiện "≥ 2 điều kiện ánh sáng" của `experiment-protocol` §9. ⚠️ Ánh sáng yếu thường
làm webcam **tự hạ tốc độ khung** để tăng thời gian phơi sáng — nếu `lay_khung_p50` tăng rõ so với
lượt 3 thì đó là **kết quả có giá trị cho báo cáo**, không phải sự cố.

### Lệnh 5 — Pi 5, ánh sáng đủ, không có người trong khung

```bash
python scripts/benchmark_detect.py --nguon camera --capture-backend opencv --models models/yolov8n-face-320_ncnn_model --threads 4 --n-frames 300 --anh-sang "trong nhà, đèn LED trần, ~300 lux" --khoang-cach-m 1.0 --noi-dung-khung khong-nguoi --device-name "Raspberry Pi 5 8GB" --ghi-chu "tản nhiệt <ghi thật>, nguồn <ghi thật>, lượt 3, đối chứng chi phí hậu xử lý"
```

Kỳ vọng: `ti_le_phat_hien` gần 0 %; `fps_tb` cao hơn lượt 3 một chút (không phải chạy NMS trên khung
có mặt). Đây là lượt **đối chứng** để tách chi phí hậu xử lý khỏi chi phí suy luận thuần.

### Sau khi chạy

- Commit **cả 8 tệp** (`.csv` + `.meta.json` của 4 lượt) — `results/*.csv` được git theo dõi (§3.6).
- Ghi lại `vcgencmd measure_temp` và `vcgencmd get_throttled` trước và sau phiên đo, dán vào biên bản
  review — script chưa đọc `get_throttled` (§12 ngoài phạm vi).
- Số dùng kết luận bước 2.5 lấy từ **lượt 3** (`fps_tb` cho chỉ tiêu §1, `fps_tong_tb` cho con số
  đầu-cuối). Lượt 4 và 5 là bối cảnh, không thay thế lượt 3.

---

## 13. Báo cáo khi xong

1. Hai con số mốc §9.0, lấy **trước** khi sửa mã.
2. Kết quả **mười** lệnh §9.1, trên host **và** trong container, kèm số ca mới đếm được ở cả hai nơi.
3. Kết quả **sáu** lệnh `grep` §9.2, giải trình từng dòng không rỗng.
4. Kết quả **mười lăm** phép đột biến §10, kèm `sha256` khôi phục. Nêu rõ **ĐB2** làm ca nào đỏ và
   **số đo thật** của hai cột trong lượt đột biến đó.
5. Danh sách dòng bị xoá trong `tests/test_benchmark_detect.py` (lệnh `git diff ... | grep "^-[^-]"`)
   và giải trình từng dòng.
6. Đối chiếu từng nhóm của bảng §8: mỗi dòng có ca test tương ứng chưa.
7. Chỗ nào của đặc tả bạn phải tự diễn giải, và diễn giải theo hướng nào.
8. Vướng mắc.

**Không commit.** Không chạy §12b. Để nguyên cây làm việc cho người review.
