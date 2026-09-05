# P3-05 — Script quét ngưỡng và đo khối nhận diện

| | |
|---|---|
| **Bước CLAUDE.md** | §5 Phase 3, bước **3.5** — mở đường cho 3.6, 3.7, 3.7b, 3.7c, 3.8 |
| **Nhánh** | `feat/p3-05-benchmark-recognize` |
| **Phụ thuộc** | `dev` tại `bfc9026` — cần `src/recognizer/{base,factory,dlib_backend,arcface_backend}.py` và `scripts/enroll.py` |
| **Đặc tả viết** | 06/09/2026 |

---

## 1. Mục tiêu

Viết `scripts/benchmark_recognize.py` — sinh hai tập điểm số (genuine và impostor) cho một backend
nhận diện, quét ngưỡng cosine similarity, ghi số liệu thô cùng bảng quét ra `results/` để bước 3.7c
chốt ngưỡng và bước 3.8 lập bảng so sánh hai phương án.

**Script này chỉ ĐO và GHI SỐ. Nó không vẽ gì cả.** ROC/DET thuộc `notebooks/06_nguong_va_roc.ipynb`
hoặc một `scripts/plot_*.py` riêng — `CLAUDE.md` §2.9 tách đo, vẽ và minh hoạ thành ba việc.

**Script là công cụ, không phải phép đo.** Con số kết luận chỉ tiêu §1 phải đến từ gallery **2–3
người nhà** đo trên **Raspberry Pi 5 thật**. Cả hai điều kiện đó hiện chưa có — xem §3.

---

## 2. Phạm vi file — danh sách trắng

| Tệp | Trạng thái | Vai trò |
|---|---|---|
| `scripts/benchmark_recognize.py` | tạo mới | Script CLI |
| `tests/test_benchmark_recognize.py` | tạo mới | Bộ kiểm thử |

**Không sửa**: `src/**`, `configs/**`, `scripts/**` khác, `requirements.txt`, `docs/**`, `.claude/**`,
`notebooks/**`, `report/**`, `.gitignore`.

⚠️ Mã việc này **cần hai khoá cấu hình mới** trong `configs/recognize.yaml` (§5.2). Người cài đặt
**không được tự thêm** — người dùng thêm ở §12a, trước lượt chạy thật §12b. Ca kiểm thử tự dựng tệp
YAML tạm trong `tmp_path`, nên §9 vẫn xanh khi `configs/recognize.yaml` chưa có hai khoá đó.

Ước lượng: script ~600 dòng, test ~750 dòng. Vượt mốc thông thường của một mã việc, chấp nhận vì
tách đôi sẽ cắt ngang một luồng dữ liệu duy nhất (ảnh → điểm số → bảng ngưỡng → tệp kết quả) và
sinh ra một interface trung gian chỉ dùng một lần.

---

## 3. Dữ kiện đã kiểm — 05–06/09/2026

### 3.1. Gallery hiện có trên đĩa

| Dữ kiện | Giá trị |
|---|---|
| Thư mục | `data/embeddings/dlib/` và `data/embeddings/arcface/` |
| Nội dung mỗi thư mục | 8 tệp `.npy` + `manifest.csv` + `gallery.meta.json` |
| `commit` trong meta | `bfc902658b7438cf6f233cc32f961b66e263ea4e` |
| `git_dirty` | `false` |
| `moi_truong` | `pc_x86` |
| `min_images_per_user_da_dung` | `3` (cấu hình đặt `10`) |
| `so_chieu` | dlib `128`, arcface `512` |
| Người đã đăng ký | `Colin_Powell` 9 ảnh · `George_W_Bush` 9 · `Jennifer_Capriati` 4 · `Jiri_Novak` 4 · `Donald_Rumsfeld` 3 · `Jacques_Chirac` 3 · `Meryl_Streep` 3 · `Vicente_Fox` 3 — **tổng 38 ảnh** |
| Danh tính bị bỏ qua | **143**, trạng thái `thieu_anh`, mỗi người 1–2 ảnh |
| Thư mục ảnh nguồn | `data/processed/lfw_original` (meta ghi `data\\processed\\lfw_original`, dấu tách kiểu Windows) |

### 3.2. ⚠️ Hệ quả chịu lực: gallery trên đĩa KHÔNG có probe genuine nào

`scripts/enroll.py` dùng **toàn bộ** ảnh trong thư mục của mỗi người để đăng ký (`liet_ke_anh_nguoi`
→ `backend.enroll`, `enroll.py:567-576`). Cột `so_anh_dung` bằng đúng `so_anh_tim_thay` ở cả 8 người.

Nghĩa là: mọi ảnh của 8 người đã đăng ký **đều nằm trong tập enroll**. Dùng chúng làm probe genuine
là đo mô hình trên chính dữ liệu đã dùng để dựng gallery — điểm số sẽ cao giả tạo, FRR gần 0, và
đường ROC vô nghĩa. Đây chính là chế độ hỏng mà §4.1 sinh ra để chặn.

Hệ quả thiết kế bắt buộc: script phải có **chế độ tự chia enroll/probe** (§4.4 chế độ `chia`), nếu
không thì bước 3.5 không chạy được với dữ liệu hiện có.

### 3.3. Bộ kiểm thử hiện tại — mốc để đối chiếu

| Nơi chạy | Lệnh | Kết quả 05/09/2026 |
|---|---|---|
| Host — Windows, Python 3.12.5, **có** `models/` | `python -m pytest -q` | **541 passed** |
| Container `faceid:arm64` — **không** có `models/`, `data/`, `docs/`, `.git/` | `python3 -m pytest -q -m "not slow"` | **508 passed, 1 skipped, 32 deselected** |

### 3.4. Container thiếu những gì — mọi ca test phải sống được không cần chúng

`deploy/Dockerfile.arm64` + `.dockerignore` khiến container **không có**: nhị phân `git`, thư mục
`.git/`, `docs/`, `models/`, `data/`, `results/`, `report/`, và các gói `ultralytics`, `torch`,
`onnx`. Chỉ có `requirements.txt` (`onnxruntime`, `ncnn`, `dlib-bin`, `opencv-python`, `numpy`,
`pyyaml`, `flask`, `python-telegram-bot`) cộng `pytest`/`black`/`ruff`.

⭐ **Toàn bộ ca test của mã việc này dùng backend giả** (§4.6) và **không ca nào cần `models/`**,
nên **không ca nào được mang `@pytest.mark.slow`**. Kiểm được: số ca mới phải cộng đủ vào cả hai
dòng của bảng §3.3.

### 3.5. `.gitignore` — đã kiểm bằng cách đọc tệp

`results/` **không** bị ignore ở mức thư mục: `.gitignore` dòng 245–250 chỉ chặn
`results/**/*.{jpg,jpeg,png,mp4,avi}` và `results/alerts/`. Tệp `.csv` và `.meta.json` trong
`results/` **được git theo dõi** và phải được commit (R6).

Ngược lại `data/*` (dòng 228) chặn toàn bộ `data/`, nên `data/embeddings/` **không** vào git.

---

## 4. Thiết kế bắt buộc

### 4.1. ★ Ảnh đã dùng để đăng ký KHÔNG bao giờ được làm probe

Đây là điểm chịu lực nhất của mã việc. Trộn vào thì mọi con số lạc quan giả tạo mà **không có gì
báo lỗi** — hệ thống trông hoàn hảo.

Quy tắc chốt: loại theo **mã băm sha256 nội dung tệp**, không theo đường dẫn.

Vì sao không theo đường dẫn: khi có gallery người nhà, thư mục enroll và thư mục test là hai thư mục
khác nhau, và một ảnh bị chép sang cả hai chỗ sẽ **lọt qua** phép so đường dẫn trong khi vẫn là cùng
một ảnh. Phép so mã băm bắt được cả hai trường hợp; phép so đường dẫn chỉ bắt được một. Dòng 28 của
§8 phân biệt đúng hai cài đặt này.

### 4.2. ★ Bài toán là open-set, không phải phân loại

Gallery 8 người, 143 danh tính lạ. Mỗi probe của người lạ phải bị **từ chối**, không phải gán cho
người gần nhất. Ngưỡng quyết định điều đó.

> Accuracy tính theo kiểu "chọn người gần nhất" mà không có ngưỡng là con số **vô nghĩa** với đề tài:
> nó không đo được năng lực an ninh, vì trong bài toán đó người lạ không có lựa chọn "không ai cả".

Do đó mọi chỉ số ở §7.2 đều là **hàm của ngưỡng**, và bảng quét ngưỡng là sản phẩm chính. Không có
chỉ số nào được tính "một lần, không kèm ngưỡng".

⚠️ Script **không đọc khoá `threshold`** của `configs/recognize.yaml`. Khoá đó hiện mang giá trị
chuỗi `TBD` (dòng 64), cố ý — ngưỡng chưa chốt. §9.2 có lệnh `grep` canh điều này.

### 4.3. ★ Tách val và test

Bước 1.11 yêu cầu chia đôi tập impostor không trùng danh tính; `data/splits/` **chưa tồn tại** (đã
kiểm bằng glob 06/09/2026). Script không tạo tệp chia tập — nó **nhận** tệp đó và ghi vào metadata.

| `--tap` | `--danh-sach-impostor` | Hành vi |
|---|---|---|
| `val` | **bắt buộc** | Thiếu → `main()` trả `1`, thông báo nêu tên cờ |
| `test` | **bắt buộc** | Thiếu → `main()` trả `1`, thông báo nêu tên cờ |
| `kiem-chuc-nang` | không bắt buộc | Chạy được, nhưng meta **bắt buộc** có khoá `canh_bao_chia_tap` không rỗng, và câu cảnh báo đi vào `notes` |

Cờ `--tap` **bắt buộc**, không có mặc định: chọn ngưỡng trên tập test là lỗi phương pháp nghiêm
trọng (`experiment-protocol` §5), và một giá trị mặc định im lặng là cách chắc chắn nhất để mắc lỗi
đó mà không ai biết.

Tệp danh sách: mỗi dòng một `user_id`; bỏ qua dòng rỗng và dòng bắt đầu bằng `#`. Danh tính impostor
không có trong tệp bị **loại khỏi lượt đo**. Tệp liệt kê một danh tính **đang có trong gallery** →
`main()` trả `1` (impostor không được là người đã đăng ký).

### 4.4. Hai chế độ dựng gallery

| Chế độ | Cờ | Gallery từ đâu | Dùng khi nào |
|---|---|---|---|
| `tep` (mặc định) | `--gallery-dir` | Nạp `.npy` từ `data/embeddings/<backend>/` | Khi tập probe nằm ở thư mục **khác** thư mục đã đăng ký — đây là cách đo hệ thống đã triển khai |
| `chia` | `--enroll-moi-nguoi K` | Dựng trong bộ nhớ từ `--vao` | Khi chỉ có **một** thư mục ảnh — trường hợp LFW hiện nay (§3.2) |

**Chế độ `tep`** — bắt buộc theo thứ tự:

1. Đường dẫn mặc định `<enroll.gallery_dir>/<backend>`. Thư mục không tồn tại → `LoiCauHinh`, thông
   báo liệt kê các backend có sẵn trong thư mục cha, **bỏ qua mọi thư mục con có tên bắt đầu bằng
   dấu chấm** (quy ước `P3-04` §4.4: `.dlib.dang-ghi`, `.dlib.cu` là trạng thái trung gian, không
   phải gallery).
2. Thiếu `manifest.csv` **hoặc** thiếu `gallery.meta.json` → `LoiCauHinh`. Thư mục chỉ có `.npy` là
   gallery dở dang, mất toàn bộ dấu vết R17.
3. Nạp `.npy` **không đệ quy**, chỉ ở tầng ngay dưới thư mục gallery.
4. Vectơ có số chiều lệch `so_chieu` trong meta → `LoiCauHinh`, thông báo chứa cả hai số.
5. Ghi `commit`, `git_dirty`, `so_nguoi_da_dang_ky`, `min_images_per_user_da_dung` từ
   `gallery.meta.json` vào `meta.dataset` của lượt đo (§7.4).
6. Suy ra tập ảnh đã dùng đăng ký: với mỗi người có `trang_thai == da_dang_ky` trong manifest, liệt
   kê ảnh trong `<duong_dan_vao>/<user_id>/` theo **đúng quy tắc của `enroll.py`** (không đệ quy,
   đuôi `.jpg`/`.jpeg`/`.png` không phân biệt hoa thường, đã sắp xếp). Số ảnh tìm được **phải bằng**
   `so_anh_dung` trong manifest; lệch → `LoiCauHinh` nêu cả hai số (thư mục nguồn đã đổi kể từ lượt
   đăng ký, không còn suy được tập enroll).
7. `duong_dan_vao` trong meta có thể ghi bằng dấu `\` (§3.1). Trước khi dựng `Path`, đổi `\` thành
   `/`. Không làm bước này thì chế độ `tep` **hỏng trên Linux và trên Pi 5** với đúng tệp meta đang
   có. Cờ `--anh-da-dang-ky` cho phép ghi đè khi thư mục đã dời chỗ.

**Chế độ `chia`** — bắt buộc theo thứ tự:

1. Liệt kê ảnh theo người từ `--vao`.
2. Với mỗi `user_id`, dựng bộ sinh ngẫu nhiên riêng `random.Random(f"{seed}:{user_id}")` rồi lấy `K`
   ảnh từ danh sách **đã sắp xếp**. Seed theo từng người, **không** một seed chung cho cả lượt: thêm
   hay bớt một danh tính khi đó **không** làm đổi phép chia của những người còn lại — điều kiện cần
   để so được hai lượt đo trên hai tập con khác nhau. Dòng 16 của §8 canh đúng tính chất này.
3. Người có **≥ K+1** ảnh: `K` ảnh vào enroll, phần còn lại vào probe genuine.
4. Người có **≤ K** ảnh: **không** được đăng ký; **toàn bộ** ảnh của họ thành probe impostor. Đây là
   quyết định có chủ đích, không phải bỏ sót — phải ghi vào manifest phần in ra và vào metadata.
5. Gọi `backend.enroll(danh_sach_anh_enroll, {"min_images_per_user": K})` **đúng một lần cho mỗi
   người**. ⛔ Script **tuyệt đối không tự tính vectơ trung bình** — cùng lý do đã ghi ở đầu
   `scripts/enroll.py`: phép chuẩn hoá L2 trước khi trung bình là quyết định phương pháp đã chốt và
   đã có ca kiểm thử ở cả hai backend; một bản sao thứ hai sẽ trôi khỏi bản gốc mà không ai phát
   hiện. §9.2 có lệnh `grep` canh, §8 dòng 20 và §10 ĐB10 canh bằng test.
6. `--enroll-moi-nguoi` mặc định lấy `enroll.min_images_per_user` từ cấu hình.

### 4.5. ★ Dấu vết của chính tập ảnh đã dùng

`scripts/benchmark_detect.py` chỉ ghi `dataset.anh_dir` và `dataset.n_anh_tong` — không tái dựng
được đúng tập ảnh nếu thư mục nguồn đổi. Không lặp lại.

`meta.dataset` phải mang **hai mã băm**:

- `bam_danh_sach_anh_probe` — trên tập ảnh **thật sự đo được**, không phải danh sách ứng viên;
- `bam_danh_sach_anh_da_dang_ky` — trên tập ảnh đã dùng đăng ký.

Cách tính, chốt cứng: với mỗi tệp dựng dòng `f"{đường_dẫn_tương_đối_POSIX}:{sha256_nội_dung}"`, sắp
xếp toàn bộ dòng, nối bằng `"\n"`, mã hoá UTF-8, rồi `sha256` chuỗi đó.

Băm **cả nội dung**, không chỉ đường dẫn: đổi nội dung một ảnh mà giữ nguyên tên là chế độ hỏng mà
phép băm danh sách đường dẫn thuần **không bắt được**, và nó đúng là chuyện xảy ra khi chạy lại
`preprocess.py` với tham số khác. Dòng 04 và 05 của §8 phân biệt hai cài đặt này.

### 4.6. Backend giả cho ca kiểm thử

Ca test dựng một lớp con của `src.recognizer.base.BoNhanDien` với:

- `so_chieu` cố định (nhỏ, ví dụ 4);
- `trich_dac_trung` sinh vectơ **tất định từ nội dung ảnh** rồi chuẩn hoá L2 — cùng ảnh cho cùng
  vectơ, ảnh khác cho vectơ khác;
- `enroll` gọi được thật, và **đếm số lần được gọi** (phục vụ dòng 20 §8);
- `identify` cài đặt tối thiểu để thoả hợp đồng lớp trừu tượng.

Script nhận backend qua `src.recognizer.factory.tao_bo_nhan_dien`; ca test `monkeypatch` hàm đó
trong không gian tên của **script**. Không ca nào cần `models/`, không ca nào cần mạng.

### 4.7. Cảnh báo, không chặn

Ba tình huống sau **không** làm `main()` trả `1`; chúng ghi một khoá cảnh báo **không rỗng** vào meta
và nối câu cảnh báo vào `notes`:

| Tình huống | Khoá meta |
|---|---|
| `moi_truong != "pi5"` | `canh_bao_hieu_nang` |
| Tổng probe < `SO_MAU_TOI_THIEU`, **hoặc** số probe genuine < `SO_MAU_TOI_THIEU` | `canh_bao_co_mau` |
| Có ảnh bị bỏ qua khi đo (`imread` trả `None`, hoặc backend ném `ValueError`) | `canh_bao_anh_bo_qua` |
| `--tap kiem-chuc-nang` | `canh_bao_chia_tap` |

Lý do không chặn: cỡ mẫu do dữ liệu quyết định, không do cờ. Chặn thì lượt kiểm chức năng hiện nay
(22 probe genuine — xem §12b) không chạy được, mà nó là thứ duy nhất chứng minh script hoạt động.
Cảnh báo đi kèm tệp kết quả suốt đời tệp đó, không biến mất khi đóng cửa sổ.

---

## 5. Giao diện dòng lệnh và cấu hình

### 5.1. Dòng lệnh

```
python scripts/benchmark_recognize.py --vao DIR --backend {dlib,arcface}
       --tap {val,test,kiem-chuc-nang} --device-name TÊN
       [--che-do-gallery {tep,chia}] [--gallery-dir DIR] [--anh-da-dang-ky DIR]
       [--enroll-moi-nguoi K] [--danh-sach-impostor TỆP] [--config CONFIG]
       [--warmup W] [--seed SEED] [--ghi-chu GHI_CHU] [--dry-run]
```

| Cờ | Mặc định | Ý nghĩa |
|---|---|---|
| `--vao` | *(bắt buộc)* | Thư mục ảnh probe, cấu trúc `<vao>/<user_id>/*.{jpg,jpeg,png}` |
| `--backend` | *(bắt buộc)* | `dlib` hoặc `arcface`. Không lấy từ cấu hình: bảng so sánh bước 3.8 cần chạy cả hai bất kể khoá `backend` đang trỏ đâu |
| `--tap` | *(bắt buộc)* | `val` · `test` · `kiem-chuc-nang` — xem §4.3 |
| `--device-name` | *(bắt buộc)* | Tên thiết bị đo (R8) |
| `--che-do-gallery` | `tep` | `tep` hoặc `chia` — xem §4.4 |
| `--gallery-dir` | `<enroll.gallery_dir>/<backend>` | Chỉ dùng ở chế độ `tep` |
| `--anh-da-dang-ky` | lấy `duong_dan_vao` từ `gallery.meta.json` | Chỉ dùng ở chế độ `tep` |
| `--enroll-moi-nguoi` | `enroll.min_images_per_user` | Chỉ dùng ở chế độ `chia` |
| `--danh-sach-impostor` | không có | Tệp danh tính impostor của tập đang đo |
| `--config` | `configs/recognize.yaml` | Đường dẫn cấu hình |
| `--warmup` | `10` | Số probe chạy làm nóng trước vòng đo, **không** loại khỏi kết quả |
| `--seed` | `42` | Seed phép chia enroll/probe (R15) |
| `--ghi-chu` | rỗng | Vào `notes` của meta |
| `--dry-run` | tắt | In kế hoạch; **không dựng backend, không băm tệp, không ghi tệp nào** |

Ai chặn cờ thiếu: `--vao`, `--backend`, `--tap` do **argparse** (`required=True`, `--backend` và
`--tap` thêm `choices`) → thiếu thì `SystemExit`. `--device-name` do **`main()`** kiểm rồi trả `1`
kèm thông báo — giữ đúng tiền lệ `scripts/benchmark_detect.py:475-481`.

Làm nóng: chạy `trich_dac_trung` trên `W` ảnh probe đầu tiên **trước** vòng đo và **bỏ** thời gian
đó. Vòng đo sau đó xử lý **toàn bộ** probe, kể cả `W` ảnh vừa dùng — tập điểm số không bị hụt.

### 5.2. Hai khoá cấu hình mới — người dùng thêm ở §12a

| Tham số | Tệp | Key | Giá trị | Bắt buộc |
|---|---|---|---|---|
| Số bước quét ngưỡng | `configs/recognize.yaml` | `benchmark.so_buoc_nguong` | `200` | có |
| Chỉ tiêu FAR để chốt ngưỡng | `configs/recognize.yaml` | `benchmark.far_muc_tieu` | `0.01` | có |

Thiếu một trong hai → `LoiCauHinh` nêu **đích danh tên key thiếu**, `main()` trả `1`.

`so_buoc_nguong = 200` lấy từ `experiment-protocol.instructions.md` §5 điểm 2.
`far_muc_tieu = 0.01` là dạng **máy đọc được** của khoá `tieu_chi_chot_nguong: "FAR_adapt <= 0.01"`
đã có sẵn ở `configs/recognize.yaml` dòng 70 (chuỗi mô tả, không phân giải được).

Kiểm giá trị — không chỉ kiểm kiểu, phải kiểm **hữu hạn** bằng `math.isfinite`:

| Key | Hợp lệ | Phải ném `LoiCauHinh` |
|---|---|---|
| `so_buoc_nguong` | số nguyên `>= 2` | `1` · `0` · `-5` · `2.5` · `"abc"` · `None` · `inf` · `nan` |
| `far_muc_tieu` | số thực, `0 < x <= 1` | `0` · `-0.1` · `1.5` · `"abc"` · `None` · `inf` · `-inf` · `nan` |

⚠️ Ba giá trị `inf`, `-inf`, `nan` phải có ca riêng cho **mỗi** key. Chúng lọt qua mọi phép kiểm kiểu
và mọi phép so sánh miền thông thường; `far_muc_tieu = nan` khiến `far <= nan` luôn `False` nên
`nguong_far_muc_tieu` âm thầm thành `None` mà không có gì báo lỗi.

### 5.3. Hằng số có tên trong mã — không phải số magic

| Hằng số | Giá trị | Nguồn |
|---|---|---|
| `SO_MAU_TOI_THIEU` | `100` | R9 / `experiment-protocol` §6 |
| `_MOI_TRUONG_PHAN_CUNG_DICH` | `"pi5"` | `experiment-protocol` §2 |

---

## 6. Giao diện hàm — giữ nguyên tên và kiểu

```python
def bam_noi_dung(duong_dan: Path) -> str:
    """Mã băm sha256 nội dung một tệp, dạng hex."""

def bam_danh_sach_tep(danh_sach: list[Path], goc: Path) -> str:
    """Mã băm của cả tập tệp, theo công thức chốt ở §4.5. Bất biến với thứ tự truyền vào."""

def liet_ke_anh_theo_nguoi(thu_muc: Path) -> dict[str, list[Path]]:
    """Liệt kê ảnh theo user_id, cấu trúc <thu_muc>/<user_id>/*.{jpg,jpeg,png}, không đệ quy.

    Raises:
        LoiCauHinh: thư mục không tồn tại, hoặc không có thư mục con nào.
    """

def doc_danh_sach_danh_tinh(duong_dan: Path) -> list[str]:
    """Đọc tệp danh sách user_id; bỏ dòng rỗng và dòng bắt đầu bằng '#'.

    Raises:
        LoiCauHinh: tệp không tồn tại, hoặc không còn dòng hợp lệ nào.
    """

def nap_gallery_tu_dia(thu_muc: Path) -> tuple[dict[str, np.ndarray], dict, list[dict]]:
    """Nạp gallery đã dựng sẵn — xem §4.4 chế độ `tep`, các bước 1 đến 4.

    Returns:
        (gallery, nội_dung_gallery_meta_json, bản_ghi_manifest).

    Raises:
        LoiCauHinh: thiếu thư mục, thiếu manifest.csv, thiếu gallery.meta.json,
            hoặc vectơ lệch số chiều.
    """

def suy_tap_anh_da_dang_ky(
    meta_gallery: dict, ban_ghi_manifest: list[dict], goc_ghi_de: Path | None
) -> list[Path]:
    """Suy ra tập ảnh đã dùng để đăng ký — xem §4.4 chế độ `tep`, các bước 6 và 7.

    Raises:
        LoiCauHinh: thư mục nguồn không tồn tại, hoặc số ảnh tìm được lệch `so_anh_dung`.
    """

def chia_enroll_probe(
    anh_theo_nguoi: dict[str, list[Path]], so_anh_enroll: int, seed: int
) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    """Chia enroll/probe theo từng người — xem §4.4 chế độ `chia`, các bước 2 đến 4.

    Returns:
        (ảnh_enroll_theo_người, ảnh_probe_theo_người). Người không đủ ảnh không có mặt
        trong từ điển thứ nhất; toàn bộ ảnh của họ nằm ở từ điển thứ hai.

    Raises:
        LoiCauHinh: `so_anh_enroll` < 1.
    """

def dung_gallery_trong_bo_nho(
    anh_enroll: dict[str, list[Path]], backend: BoNhanDien, so_anh_enroll: int
) -> dict[str, np.ndarray]:
    """Dựng gallery bằng cách gọi `backend.enroll` — xem §4.4 chế độ `chia`, bước 5.

    Raises:
        LoiMoHinh: `backend.enroll` ném `ValueError` dù người đó đủ ảnh.
    """

def do_diem_probe(
    danh_sach_probe: list[tuple[str, Path]],
    gallery: dict[str, np.ndarray],
    backend: BoNhanDien,
    so_lam_nong: int,
) -> tuple[list[dict], list[Path]]:
    """Trích đặc trưng từng probe và so với toàn bộ gallery.

    Returns:
        (bản_ghi, ảnh_bị_bỏ_qua). Mỗi bản ghi gồm đủ các khoá của `_COT_CSV_THO`
        trừ `run_id`, `backend` và `tap` — nơi gọi điền ba khoá đó.

    Raises:
        LoiCauHinh: gallery rỗng.
    """

def quet_nguong(ban_ghi: list[dict], so_buoc: int) -> list[dict]:
    """Quét ngưỡng trên lưới đều — xem §7.2.

    Raises:
        LoiCauHinh: `ban_ghi` rỗng, hoặc `so_buoc` < 2.
    """

def chot_diem_can_bang(bang_nguong: list[dict], far_muc_tieu: float) -> dict:
    """Chốt EER và ngưỡng tại chỉ tiêu FAR — xem §7.3.

    Raises:
        LoiCauHinh: `far_muc_tieu` không hữu hạn hoặc ngoài khoảng (0, 1].
    """

def tong_hop_toc_do(ban_ghi: list[dict]) -> dict:
    """Tổng hợp latency — xem §7.3.

    Raises:
        LoiCauHinh: danh sách bản ghi rỗng.
    """

def ghi_ket_qua(
    thu_muc: Path, run_id: str, ban_ghi: list[dict], bang_nguong: list[dict], meta: dict
) -> tuple[Path, Path, Path]:
    """Ghi ĐÚNG BA tệp — xem §7.4.

    Raises:
        LoiCauHinh: meta thiếu khoá bắt buộc, hoặc một trong ba tệp đích đã tồn tại.
    """

def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 thành công, 1 thất bại."""
```

Hai hàm **dùng lại, không viết lại**: `doc_nhiet_do_cpu` từ `scripts.benchmark_detect` và
`xac_dinh_moi_truong` từ `scripts.export_detector_ncnn` (`scripts/enroll.py:37` đã có tiền lệ).

---

## 7. Chỉ số và định dạng kết quả

### 7.1. Một probe được xử lý thế nào

1. `vec = backend.trich_dac_trung(anh)` — đo `latency_trich_ms`.
2. So `vec` với **toàn bộ** vectơ gallery bằng `src.recognizer.base.do_tuong_dong` — đo
   `latency_so_khop_ms`. Ghi `top1_user` (điểm cao nhất; hoà thì lấy `user_id` nhỏ nhất theo thứ tự
   từ điển, để tất định) và `top1_score`.
3. `latency_identify_ms = latency_trich_ms + latency_so_khop_ms`. Đây là chi phí tương đương một lần
   `BoNhanDien.identify` — hàm đó làm đúng hai việc trên. Không gọi `identify` trực tiếp vì nó chỉ
   trả người khớp nhất, còn ta cần thêm điểm với **người thật** để phân tích.
4. `nhan = "genuine"` nếu `user_id_that` có trong gallery, ngược lại `"impostor"`.
5. `diem_dung_nguoi` = độ tương đồng với vectơ của chính người đó; **rỗng** với probe impostor.
6. `imread` trả `None`, hoặc `trich_dac_trung` ném `ValueError` → ghi cảnh báo, đếm vào
   `so_anh_bo_qua`, **bỏ dòng đó**, tiếp tục. Không dừng cả lượt đo.

### 7.2. Định nghĩa chỉ số tại một ngưỡng `t` — chốt cứng

Lưới ngưỡng: `so_buoc` điểm chia đều từ `min(top1_score)` tới `max(top1_score)` của toàn bộ bản ghi.
Chấp nhận khi `top1_score >= t` (dấu bằng **được** chấp nhận — §10 ĐB4 canh chỗ này).

Đặt `G` = số probe genuine, `I` = số probe impostor.

| Cột | Định nghĩa |
|---|---|
| `tp` | số genuine có `top1_score >= t` **và** `top1_user == user_id_that` |
| `fp_impostor` | số impostor có `top1_score >= t` |
| `fp_nham_nguoi` | số genuine có `top1_score >= t` **và** `top1_user != user_id_that` |
| `fn` | số genuine có `top1_score < t` |
| `tn` | số impostor có `top1_score < t` |
| `far` | `fp_impostor / I`; `I == 0` → ô rỗng |
| `frr` | `fn / G` |
| `ti_le_gan_nham` | `fp_nham_nguoi / G` |
| `accuracy` | `(tp + tn) / (G + I)` |
| `precision` | `tp / (tp + fp_impostor + fp_nham_nguoi)`; mẫu `0` → ô rỗng |
| `recall` | `tp / G` |

Ba loại lỗi của probe genuine được tách rời (`fn` bị từ chối · `fp_nham_nguoi` gán nhầm người ·
phần còn lại là `tp`) thay vì gộp vào một "FRR mở rộng": với gallery nhỏ, gán nhầm người là lỗi
khác hẳn về bản chất so với từ chối, và gộp lại thì mất khả năng phân biệt.

### 7.3. Chốt điểm cân bằng và tốc độ

`chot_diem_can_bang` trả về từ điển gồm `nguong_eer`, `eer`, `far_tai_eer`, `frr_tai_eer`,
`nguong_far_muc_tieu`, `far_tai_nguong_chot`, `frr_tai_nguong_chot`, `accuracy_tai_nguong_chot`.

- `nguong_eer` = điểm trên lưới có `|far - frr|` **nhỏ nhất**; hoà → lấy ngưỡng **nhỏ nhất**.
  `eer = (far + frr) / 2` tại điểm đó.
- `nguong_far_muc_tieu` = ngưỡng **nhỏ nhất** trên lưới có `far <= far_muc_tieu`. `far` không tăng
  theo ngưỡng, nên ngưỡng nhỏ nhất thoả điều kiện cũng là ngưỡng cho `frr` thấp nhất.
- Không ngưỡng nào đạt → cả bốn khoá liên quan bằng `None`, `main()` vẫn trả `0`, in cảnh báo.

⚠️ EER **chỉ để so sánh hai phương án**, không dùng chốt ngưỡng triển khai — `configs/recognize.yaml`
dòng 66–70 đã chốt: ấn định `FAR_adapt <= 1 %` rồi đọc FRR tương ứng. Bảng in ra phải ghi rõ điều này.

`tong_hop_toc_do` trả về `latency_tb_ms`, `latency_do_lech_ms`, `latency_p50_ms`, `latency_p95_ms`,
`fps_suy_ra` (`1000 / latency_tb_ms`), tính trên cột `latency_identify_ms`.

### 7.4. Ba tệp kết quả

`run_id = f"bench_recognize_{backend}_{YYYYMMDD_HHMM}"`.

| Tệp | Nội dung |
|---|---|
| `results/<run_id>.csv` | Điểm số thô — **một dòng mỗi probe** |
| `results/<run_id>.nguong.csv` | Bảng quét — **một dòng mỗi ngưỡng** |
| `results/<run_id>.meta.json` | Ngữ cảnh |

⭐ **`run_id` mang tên backend, lệch với khuôn `bench_recognize_<YYYYMMDD_HHMM>` của
`experiment-protocol` §4.** Lý do: bước 3.8 chạy hai backend **nối tiếp nhau**, thường trong cùng một
phút; giữ khuôn cũ thì lượt thứ hai **ghi đè** lượt thứ nhất — đúng điều §4 của giao thức cấm. Kèm
theo, `ghi_ket_qua` **từ chối ghi đè**: một trong ba tệp đích đã tồn tại → `LoiCauHinh`.

Cột CSV thô, đúng thứ tự — **14 cột**:

```csv
run_id,backend,tap,user_id_that,nhan,anh_bam,top1_user,top1_score,diem_dung_nguoi,so_chieu,latency_trich_ms,latency_so_khop_ms,latency_identify_ms,cpu_temp_c
```

`anh_bam` = **12 ký tự đầu** của `bam_noi_dung(ảnh)`, **không phải đường dẫn**. Truy vết được (tính
lại mã băm là ra tệp) mà không đưa đường dẫn ảnh khuôn mặt vào một tệp được commit — `results/*.csv`
nằm trong git (§3.5), và R25 cấm đưa dữ liệu ảnh khuôn mặt vào đó. Mã băm dùng lại từ phép loại trừ
§4.1, không phải chi phí thêm.

Cột CSV ngưỡng, đúng thứ tự — **17 cột**:

```csv
run_id,backend,tap,nguong,so_genuine,so_impostor,tp,fp_impostor,fp_nham_nguoi,fn,tn,far,frr,ti_le_gan_nham,accuracy,precision,recall
```

Khoá bắt buộc của `.meta.json` — **23 khoá**, liệt kê đích danh:

`run_id`, `timestamp`, `git_commit`, `git_dirty`, `git_dirty_toan_cay`, `script`, `command`,
`device`, `moi_truong`, `software`, `config_file`, `config_snapshot`, `backend`, `tap`, `dataset`,
`seed`, `warmup_probes`, `cpu_temp_start_c`, `cpu_temp_max_c`, `duration_s`, `notes`, `tep_ket_qua`,
`tom_tat`.

- `device`: đủ **bốn** trường con `name`, `os`, `machine`, `processor`.
- `software`: đủ **năm** khoá `python`, `onnxruntime`, `opencv-python`, `numpy`, `dlib-bin`.
- `tep_ket_qua`: đủ **ba** khoá `tho`, `nguong`, `meta` — đường dẫn tương đối của ba tệp.
- `git_dirty` giới hạn phạm vi `("src", "scripts", "configs", "requirements.txt",
  "requirements-dev.txt")` như `benchmark_detect.py` và `enroll.py`; `git_dirty_toan_cay` xét cả cây.
- `moi_truong` lấy từ `xac_dinh_moi_truong()`, nhận đúng một trong `pc_x86` · `docker_arm64` · `pi5`.

Khoá con bắt buộc của `meta.dataset` — **16 khoá**, liệt kê đích danh (giá trị có thể là `null`
nhưng khoá **luôn phải có mặt**):

`che_do_gallery`, `gallery_dir`, `gallery_commit`, `gallery_git_dirty`,
`gallery_so_nguoi_da_dang_ky`, `gallery_min_images_per_user_da_dung`, `so_anh_enroll_moi_nguoi`,
`anh_dir`, `tep_danh_sach_impostor`, `so_nguoi_gallery`, `so_anh_da_dang_ky`,
`bam_danh_sach_anh_da_dang_ky`, `so_anh_probe`, `so_anh_bo_qua`, `so_danh_tinh_impostor`,
`bam_danh_sach_anh_probe`.

`tom_tat` gộp đầu ra của `chot_diem_can_bang` và `tong_hop_toc_do`, cộng `so_nguoi_gallery`,
`so_probe_genuine`, `so_probe_impostor`, `far_muc_tieu`.

### 7.5. Bảng in ra cuối

Bảng Markdown gồm: số người gallery, số probe genuine / impostor, `nguong_eer` và `eer`,
`nguong_far_muc_tieu` cùng `far`/`frr`/`accuracy` tại đó, `latency_p50`/`p95`, `fps_suy_ra`, và
đường dẫn ba tệp kết quả. Kèm dòng nhắc: kết luận chỉ tiêu §1 chỉ có giá trị với gallery người nhà
đo trên Pi 5 thật.

---

## 8. Bảng tiêu chí nghiệm thu

Mỗi dòng là **một ca test** tên `test_dong<nn>` trong `tests/test_benchmark_recognize.py`.
Mỗi ô "Assert tối thiểu" là **một** điều kiện; không gộp.

### 8.1. Mã băm và dấu vết tập ảnh (§4.5)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Cùng nội dung, khác tên → cùng mã băm | `bam_noi_dung(a) == bam_noi_dung(b)` |
| 02 | Lệch một byte → khác mã băm | `bam_noi_dung(a) != bam_noi_dung(c)` |
| 03 | Bất biến với thứ tự truyền vào | `bam_danh_sach_tep([a, b], g) == bam_danh_sach_tep([b, a], g)` |
| 04 | ★ Đổi **nội dung** một tệp, giữ nguyên tên → mã băm đổi | `bam_danh_sach_tep([a, b], g) != bam_sau_khi_ghi_de_a` |
| 05 | Đổi **tên** một tệp, giữ nguyên nội dung → mã băm đổi | `bam_danh_sach_tep([a, b], g) != bam_danh_sach_tep([a2, b], g)` |

### 8.2. Liệt kê ảnh và chia enroll/probe (§4.4)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 06 | Khoá là tên thư mục con | `set(liet_ke_anh_theo_nguoi(d)) == {"u1", "u2"}` |
| 07 | Bỏ tệp không phải ảnh | Thư mục `u1` có `a.jpg` và `ghi_chu.txt` ⇒ `len(kq["u1"]) == 1` |
| 08 | Thư mục không tồn tại → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 09 | Không thư mục con nào → `LoiCauHinh`, thông báo **khác** dòng 08 | Thông báo chứa `"rỗng"` |
| 10 | Người có `K+1` ảnh → đúng `K` ảnh vào enroll | `len(enroll["u1"]) == 3` với `K=3`, 4 ảnh |
| 11 | ★ Enroll và probe **giao rỗng** | `set(enroll["u1"]) & set(probe["u1"]) == set()` |
| 12 | Người có **đúng** `K` ảnh → không được đăng ký | `"u2" not in enroll` với `K=3`, 3 ảnh |
| 13 | Cùng người đó: toàn bộ ảnh vào probe | `len(probe["u2"]) == 3` |
| 14 | Cùng seed → cùng phép chia | `chia_enroll_probe(a, 2, 42) == chia_enroll_probe(a, 2, 42)` |
| 15 | Khác seed → khác phép chia | Mỗi người 6 ảnh ⇒ `chia_enroll_probe(a, 2, 42) != chia_enroll_probe(a, 2, 7)` |
| 16 | ★ Thêm danh tính mới **không** đổi phép chia của danh tính cũ | `chia_enroll_probe({"u1": ds}, 2, 42)[0]["u1"] == chia_enroll_probe({"u1": ds, "u9": ds9}, 2, 42)[0]["u1"]` |
| 17 | `so_anh_enroll` < 1 → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 18 | Người đủ ảnh nhưng backend giả ném `ValueError` → `LoiMoHinh` | `pytest.raises(LoiMoHinh)` gọi thẳng `dung_gallery_trong_bo_nho` |
| 19 | Cặp đối chứng dòng 18: backend giả bình thường → dựng đủ người | `len(dung_gallery_trong_bo_nho(...)) == 2` |
| 20 | ★ Gọi `backend.enroll` **đúng một lần cho mỗi người** | Backend giả đếm ⇒ `backend.so_lan_enroll == 2` |

### 8.3. Nạp gallery từ đĩa (§4.4 chế độ `tep`)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 21 | Nạp đủ người từ các tệp `.npy` | `set(nap_gallery_tu_dia(gd)[0]) == {"u1", "u2"}` |
| 22 | **Không đệ quy**: `.npy` trong thư mục con bị bỏ qua | Tạo `<gd>/con/y.npy` ⇒ `"y" not in gallery` |
| 23 | Thiếu `manifest.csv` → `LoiCauHinh` | Thông báo chứa `"manifest.csv"` |
| 24 | Thiếu `gallery.meta.json` → `LoiCauHinh` | Thông báo chứa `"gallery.meta.json"` |
| 25 | Vectơ lệch số chiều so với meta → `LoiCauHinh` | Meta ghi `so_chieu: 4`, `.npy` dài 8 ⇒ thông báo chứa `"(8,)"` |
| 26 | Cặp đối chứng của 23–25: đủ tệp, đúng số chiều → nạp được | `len(gallery) == 2` |
| 27 | Thư mục gallery không tồn tại → thông báo liệt kê backend có sẵn | Cạnh `<cha>/dlib/` có `<cha>/.dlib.dang-ghi/` ⇒ thông báo chứa `"dlib"` |
| 28 | ★ Cùng tình huống 27: thư mục dấu chấm **không** được liệt kê | Thông báo **không** chứa `"dang-ghi"` |

### 8.4. ★ Loại ảnh đã đăng ký khỏi probe (§4.1) — phần chịu lực

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 29 | Chỉ lấy ảnh của người `da_dang_ky`, bỏ người `thieu_anh` | `len(suy_tap_anh_da_dang_ky(...)) == 3` với manifest 1 người 3 ảnh + 1 người `thieu_anh` |
| 30 | Số ảnh tìm được lệch `so_anh_dung` → `LoiCauHinh` | Manifest ghi `so_anh_dung=3`, thư mục có 2 ảnh ⇒ thông báo chứa `"3"` |
| 31 | Cùng tình huống 30: thông báo nêu **cả** số thật | Thông báo chứa `"2"` |
| 32 | Cặp đối chứng của 30: số khớp → trả danh sách, không ném | `len(...) == 3` |
| 33 | `duong_dan_vao` ghi bằng dấu `\` vẫn phân giải được | Thư mục thật `<t>/a/b`, meta ghi `"a\\b"` ⇒ `len(...) == 2` |
| 34 | ★ Probe trùng **đường dẫn** với ảnh đã đăng ký → bị loại | Sau `main(...)`, `anh_bam` của ảnh đó **không** xuất hiện trong cột `anh_bam` của CSV thô |
| 35 | ★★ Probe là **bản sao khác tên** của ảnh đã đăng ký → vẫn bị loại | `shutil.copyfile("enroll/u1/x.jpg", "probe/u1/z.jpg")` (chép byte, mã băm trùng); sau `main(...)`, `anh_bam` đó **không** xuất hiện trong CSV thô |
| 36a | ★ Không còn probe genuine nào sau khi loại → `main()` trả `1` | `main([...]) == 1` |
| 36b | Cùng tình huống 36a: thông báo nêu rõ nguyên nhân | `capsys`: đầu ra chứa `"genuine"` |
| 37 | Cùng tình huống 36: **không** ghi tệp nào | `list(thu_muc_ket_qua.rglob("*")) == []` |
| 38 | Cặp đối chứng của 36: còn probe genuine → `main()` trả `0` | `main([...]) == 0` |
| 39 | Cùng tình huống 38: CSV thô có ≥ 1 dòng genuine | `sum(1 for r in rows if r["nhan"] == "genuine") >= 1` |
| 40 | Probe của danh tính không có trong gallery được gắn nhãn impostor | `{r["nhan"] for r in rows if r["user_id_that"] == "u9"} == {"impostor"}` |

Dòng 34 và 35 là cặp **phân biệt hai cài đặt gần giống nhau**: loại theo đường dẫn qua được 34 nhưng
trượt 35. Đây là lý do §4.1 chốt băm nội dung.

### 8.5. Chia tập val/test (§4.3)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 41a | `--tap val` thiếu `--danh-sach-impostor` → `main()` trả `1` | `main([...]) == 1` |
| 41b | Cùng tình huống 41a: thông báo nêu tên cờ còn thiếu | `capsys`: đầu ra chứa `"--danh-sach-impostor"` |
| 42a | `--tap test` thiếu `--danh-sach-impostor` → `main()` trả `1` | `main([...]) == 1` |
| 42b | Cùng tình huống 42a: thông báo nêu tên cờ còn thiếu | `capsys`: đầu ra chứa `"--danh-sach-impostor"` |
| 43 | `--tap kiem-chuc-nang` chạy được, meta có cảnh báo **không rỗng** | `meta["canh_bao_chia_tap"] != ""` |
| 44 | Cặp đối chứng của 43: `--tap val` + tệp hợp lệ → **không** có khoá đó | `"canh_bao_chia_tap" not in meta` |
| 45 | Danh tính impostor ngoài tệp bị loại | Tệp liệt kê 2 trong 5 danh tính ⇒ `meta["dataset"]["so_danh_tinh_impostor"] == 2` |
| 46a | Tệp liệt kê một người **đang có trong gallery** → `main()` trả `1` | `main([...]) == 1` |
| 46b | Cùng tình huống 46a: thông báo nêu đích danh người đó | `capsys`: đầu ra chứa `"u1"` |
| 47 | `doc_danh_sach_danh_tinh` bỏ dòng rỗng và dòng `#` | `doc_danh_sach_danh_tinh(f) == ["a", "b"]` |
| 48 | Tệp không còn dòng hợp lệ nào → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 49 | `tap` được ghi vào mọi dòng CSV thô | `{r["tap"] for r in rows} == {"val"}` |

### 8.6. Quét ngưỡng và chỉ số (§7.2)

Mọi ca dưới đây dựng bản ghi **bằng tay**, không chạy mô hình.

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 50 | Trả đúng `so_buoc` dòng | `len(quet_nguong(bg, 200)) == 200` |
| 51 | Ngưỡng đầu bằng điểm nhỏ nhất | `bang[0]["nguong"] == pytest.approx(min(scores))` |
| 52 | Ngưỡng cuối bằng điểm lớn nhất | `bang[-1]["nguong"] == pytest.approx(max(scores))` |
| 53 | `far` không tăng theo ngưỡng | `all(bang[i]["far"] >= bang[i + 1]["far"] for i in range(len(bang) - 1))` |
| 54 | `frr` không giảm theo ngưỡng | `all(bang[i]["frr"] <= bang[i + 1]["frr"] for i in range(len(bang) - 1))` |
| 55 | `far` đúng trên ví dụ tay | 4 impostor, 1 vượt ngưỡng ⇒ `dong["far"] == pytest.approx(0.25)` |
| 56 | `frr` đúng trên ví dụ tay | 4 genuine, 1 dưới ngưỡng ⇒ `dong["frr"] == pytest.approx(0.25)` |
| 57 | `ti_le_gan_nham` đúng | 4 genuine, 1 vượt ngưỡng nhưng sai người ⇒ `pytest.approx(0.25)` |
| 58 | `accuracy` đúng | Ví dụ tay ⇒ `dong["accuracy"] == pytest.approx((tp + tn) / (G + I))` với số cụ thể |
| 59 | ★ `precision` tính **cả** genuine gán nhầm vào mẫu số | 1 `tp`, 1 `fp_impostor`, 1 `fp_nham_nguoi` ⇒ `pytest.approx(1 / 3)` |
| 60 | `recall` đúng | `dong["recall"] == pytest.approx(tp / G)` với số cụ thể |
| 61a | ★ Điểm **bằng đúng** ngưỡng được tính vào `tp` | Bản ghi genuine duy nhất có `top1_score` trùng điểm lưới cuối ⇒ `bang[-1]["tp"] == 1` |
| 61b | Cùng tình huống 61a: **không** tính vào `fn` | `bang[-1]["fn"] == 0` |
| 62 | `I == 0` → ô `far` rỗng, không chia cho 0 | `bang[0]["far"] == ""` |
| 63 | `so_buoc` < 2 → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 64 | Bản ghi rỗng → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |

### 8.7. Chốt điểm cân bằng (§7.3)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 65 | EER lấy điểm `\|far - frr\|` **nhỏ nhất** | Bảng tay có đúng một điểm `far == frr` ⇒ `kq["nguong_eer"] == 0.5` |
| 66 | Hoà EER → lấy ngưỡng **nhỏ nhất** | Bảng tay có hai điểm cùng `\|far - frr\|` ⇒ `kq["nguong_eer"] == 0.3` |
| 67 | ★ `nguong_far_muc_tieu` lấy ngưỡng **nhỏ nhất** thoả `far <= muc_tieu` | Bảng tay ⇒ `kq["nguong_far_muc_tieu"] == 0.6` |
| 68 | Không ngưỡng nào đạt → `None` | `kq["nguong_far_muc_tieu"] is None` |
| 69 | Cùng tình huống 68: `main()` vẫn trả `0` | `main([...]) == 0` |
| 70 | `far_muc_tieu = inf` → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 71 | `far_muc_tieu = -inf` → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 72 | `far_muc_tieu = nan` → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 73 | `far_muc_tieu = 0` → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 74 | `far_muc_tieu = 1.5` → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 75 | Cặp đối chứng của 70–74: `far_muc_tieu = 0.01` → không ném | `chot_diem_can_bang(bang, 0.01)["eer"] >= 0.0` |

### 8.8. Tốc độ (§7.3)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 76 | `latency_p50_ms` khớp `np.percentile` | 100 bản ghi `1..100` ⇒ `pytest.approx(np.percentile(v, 50))` |
| 77 | `latency_p95_ms` khớp `np.percentile` | Cùng dữ liệu ⇒ `pytest.approx(np.percentile(v, 95))` |
| 78 | `latency_do_lech_ms` khớp `np.std` | Cùng dữ liệu ⇒ `pytest.approx(np.std(v))` |
| 79 | `fps_suy_ra` là nghịch đảo latency trung bình | Latency đều 50 ms ⇒ `pytest.approx(20.0)` |
| 80 | Từng dòng: `identify == trich + so_khop` | `all(abs(r["latency_identify_ms"] - r["latency_trich_ms"] - r["latency_so_khop_ms"]) < 1e-9 for r in rows)` |
| 81 | ★ Warm-up **không** làm hụt số dòng CSV | `--warmup 3` với 10 probe ⇒ `len(rows) == 10` |
| 82 | Bản ghi rỗng → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |

### 8.9. Ghi tệp và metadata (§7.4)

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 83 | Ghi **đúng ba** tệp | `len(list(thu_muc.iterdir())) == 3` |
| 84 | Tên CSV thô đúng khuôn | `re.fullmatch(r"bench_recognize_(dlib\|arcface)_\d{8}_\d{4}\.csv", p_tho.name)` |
| 85 | Tên CSV ngưỡng đúng khuôn | `re.fullmatch(r"bench_recognize_(dlib\|arcface)_\d{8}_\d{4}\.nguong\.csv", p_ng.name)` |
| 86 | Tên meta đúng khuôn | `re.fullmatch(r"bench_recognize_(dlib\|arcface)_\d{8}_\d{4}\.meta\.json", p_meta.name)` |
| 87 | CSV thô đúng **14 cột**, đúng thứ tự | So `next(csv.reader(f))` với danh sách 14 tên nguyên văn §7.4 |
| 88 | CSV ngưỡng đúng **17 cột**, đúng thứ tự | So `next(csv.reader(f))` với danh sách 17 tên nguyên văn §7.4 |
| 89 | Số dòng CSV thô bằng số probe đo được | `len(rows) == meta["dataset"]["so_anh_probe"]` |
| 90 | Số dòng CSV ngưỡng bằng `so_buoc_nguong` | `len(rows_ng) == 200` |
| 91 | Meta đủ **23 khoá** bắt buộc | `set(meta) >= {"run_id","timestamp","git_commit","git_dirty","git_dirty_toan_cay","script","command","device","moi_truong","software","config_file","config_snapshot","backend","tap","dataset","seed","warmup_probes","cpu_temp_start_c","cpu_temp_max_c","duration_s","notes","tep_ket_qua","tom_tat"}` |
| 92 | `device` đủ **bốn** trường con | `set(meta["device"]) >= {"name","os","machine","processor"}` |
| 93 | `software` đủ **năm** khoá | `set(meta["software"]) >= {"python","onnxruntime","opencv-python","numpy","dlib-bin"}` |
| 94 | `tep_ket_qua` đủ **ba** khoá | `set(meta["tep_ket_qua"]) == {"tho","nguong","meta"}` |
| 95 | `meta["dataset"]` đủ **16 khoá con** | `set(meta["dataset"]) >= {"che_do_gallery","gallery_dir","gallery_commit","gallery_git_dirty","gallery_so_nguoi_da_dang_ky","gallery_min_images_per_user_da_dung","so_anh_enroll_moi_nguoi","anh_dir","tep_danh_sach_impostor","so_nguoi_gallery","so_anh_da_dang_ky","bam_danh_sach_anh_da_dang_ky","so_anh_probe","so_anh_bo_qua","so_danh_tinh_impostor","bam_danh_sach_anh_probe"}` |
| 96 | ★ Chế độ `tep` ghi lại `commit` của gallery | `meta["dataset"]["gallery_commit"] == <giá trị trong gallery.meta.json giả>` |
| 97 | Chế độ `tep` ghi lại `min_images_per_user_da_dung` | `meta["dataset"]["gallery_min_images_per_user_da_dung"] == 3` |
| 98 | ★ `bam_danh_sach_anh_probe` tính trên ảnh **đo được**, không trên ứng viên | Thêm một ảnh hỏng (0 byte) vào thư mục probe ⇒ mã băm **bằng** mã băm lượt chạy không có ảnh hỏng đó |
| 99 | Ảnh hỏng được đếm | Cùng tình huống 98 ⇒ `meta["dataset"]["so_anh_bo_qua"] == 1` |
| 100 | Ảnh hỏng sinh cảnh báo không rỗng | Cùng tình huống ⇒ `meta["canh_bao_anh_bo_qua"] != ""` |
| 101 | Cặp đối chứng của 100: không ảnh hỏng → không có khoá đó | `"canh_bao_anh_bo_qua" not in meta` |
| 102 | Meta thiếu khoá → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` với `meta={}` |
| 103 | Cặp đối chứng của 102: meta đủ khoá → ghi thành công | Cả ba tệp `.exists()` |
| 104 | ★ Tệp đích đã tồn tại → `LoiCauHinh`, **không** ghi đè | Tạo sẵn `<run_id>.csv` với nội dung `"cu"` ⇒ `pytest.raises(LoiCauHinh)` |
| 105 | Cùng tình huống 104: nội dung tệp cũ **nguyên vẹn** | `p_tho.read_text() == "cu"` |
| 106 | `cpu_temp_c` rỗng khi không có cảm biến | Ô tương ứng là chuỗi rỗng, **không** phải `"None"` |

### 8.10. Cấu hình, CLI và cảnh báo

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 107a | Thiếu `--device-name` → `main()` trả `1` | `main([...]) == 1` |
| 107b | Cùng tình huống 107a: thông báo nêu tên cờ | `capsys`: đầu ra chứa `"device-name"` |
| 108 | Thiếu `--tap` → argparse thoát | `pytest.raises(SystemExit)` |
| 109a | Thiếu `benchmark.so_buoc_nguong` → `main()` trả `1` | `main([...]) == 1` |
| 109b | Cùng tình huống 109a: thông báo nêu **đích danh** key thiếu | `capsys`: đầu ra chứa `"so_buoc_nguong"` |
| 110a | Thiếu `benchmark.far_muc_tieu` → `main()` trả `1` | `main([...]) == 1` |
| 110b | Cùng tình huống 110a: thông báo nêu **đích danh** key thiếu | `capsys`: đầu ra chứa `"far_muc_tieu"` |
| 111 | `so_buoc_nguong = 1` → `main()` trả `1` | `main([...]) == 1` |
| 112 | `so_buoc_nguong = 2.5` → `main()` trả `1` | `main([...]) == 1` |
| 113 | `so_buoc_nguong = "abc"` → `main()` trả `1` | `main([...]) == 1` |
| 114 | `so_buoc_nguong = inf` → `main()` trả `1` | `main([...]) == 1` |
| 115 | `so_buoc_nguong = nan` → `main()` trả `1` | `main([...]) == 1` |
| 116 | Cặp đối chứng 111–115: `so_buoc_nguong = 20` → `main()` trả `0` | `main([...]) == 0` |
| 117 | ★ `--dry-run` **không ghi tệp nào** | `list(thu_muc_ket_qua.rglob("*")) == []` |
| 118 | ★ `--dry-run` **không dựng backend** | `monkeypatch` `tao_bo_nhan_dien` ném `AssertionError` ⇒ `main([..., "--dry-run"]) == 0` |
| 119 | `--backend` sai → `SystemExit` từ argparse | `pytest.raises(SystemExit)` |
| 120 | Số probe < `SO_MAU_TOI_THIEU` → `main()` vẫn trả `0` | `main([...]) == 0` |
| 121 | Cùng tình huống 120: meta có cảnh báo cỡ mẫu không rỗng | `meta["canh_bao_co_mau"] != ""` |
| 122 | `moi_truong != "pi5"` → meta có `canh_bao_hieu_nang` không rỗng | `meta["canh_bao_hieu_nang"] != ""` |
| 123 | Cặp đối chứng 122: `monkeypatch` `xac_dinh_moi_truong` → `"pi5"` ⇒ không có khoá đó | `"canh_bao_hieu_nang" not in meta` |
| 124 | `moi_truong` trong meta thuộc ba mã hợp lệ | `meta["moi_truong"] in {"pc_x86", "docker_arm64", "pi5"}` |
| 125 | Câu cảnh báo môi trường cũng vào `notes` | `"pi5" in meta["notes"]` khi chạy ngoài `pi5` |
| 126 | Bảng in ra nêu rõ EER không dùng chốt ngưỡng | `capsys`: đầu ra chứa `"EER"` |
| 127 | Bảng in ra nêu chỉ tiêu FAR | `capsys`: đầu ra chứa `"FAR"` |
| 128 | Gallery rỗng → `do_diem_probe` ném `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |

**Không ca nào mang `@pytest.mark.slow`, không ca nào cần `models/`, không ca nào chạm mạng.**
Mọi ca ghi tệp phải dùng `tmp_path`.

---

## 9. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

### 9.1. Định dạng, lint, kiểm thử

```bash
python -m black --check --line-length 100 scripts/benchmark_recognize.py tests/test_benchmark_recognize.py
```

```bash
python -m ruff check scripts/benchmark_recognize.py tests/test_benchmark_recognize.py
```

```bash
python -m pytest tests/test_benchmark_recognize.py -v
```

Kỳ vọng: **mọi ca xanh, 0 skipped**. Một ca `skipped` ở đây nghĩa là ca đó đang phụ thuộc `models/`
hoặc `data/` — sai §3.4, sửa ca test.

```bash
python -m pytest -q
```

Kỳ vọng, **kèm điều kiện môi trường**: trên host Windows Python 3.12.5 **có** `models/`, mốc trước
mã việc là **541 passed** (§3.3). Sau mã việc phải là **541 + số ca mới**, `0 failed`, `0 skipped`.
Ghi con số thật bạn thấy, không ghi lại con số ở đây.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

Kỳ vọng: mốc trước mã việc là **508 passed, 1 skipped, 32 deselected** (container **không** có
`models/`, `data/`, `docs/`, `.git/`). Sau mã việc, số `passed` phải tăng **đúng bằng** số ca mới —
bằng số ca mới trên host. Lệch nghĩa là có ca đang phụ thuộc thứ container không có.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest --collect-only -q tests/test_benchmark_recognize.py
```

Kỳ vọng: thu thập được **đủ** số ca, **không** lỗi import. Lệnh này bắt riêng chế độ hỏng "import ở
mức module một thứ container không có".

```bash
git status --short --untracked-files=all
```

Kỳ vọng: **đúng hai** tệp của §2. Cờ `--untracked-files=all` là bắt buộc — thiếu nó git gộp cả thư
mục mới thành một dòng và phép đếm sai.

### 9.2. Quét mẫu vi phạm

```bash
grep -nE "\bthreshold\b" scripts/benchmark_recognize.py
```

Phải **rỗng**. Khoá `threshold` của `configs/recognize.yaml` đang mang chuỗi `TBD`; đọc nó vào là
hỏng, và ngưỡng chưa chốt thì script không có quyền dùng ngưỡng nào cả (§4.2).

```bash
grep -n "except Exception" scripts/benchmark_recognize.py
```

```bash
grep -rnE "ultralytics|import torch|matplotlib|seaborn|plotly" scripts/benchmark_recognize.py
```

Phải **rỗng**. Script không vẽ gì (§1) và phải chạy được trên Pi 5.

```bash
grep -n "\.enroll(" scripts/benchmark_recognize.py
```

Kỳ vọng **đúng một dòng mã thi hành**, ở `dung_gallery_trong_bo_nho`. Dòng nằm trong docstring hoặc
comment giải trình được, nêu rõ khi báo cáo. **Bằng 0 dòng** là dấu hiệu script tự tính vectơ trung
bình thay vì gọi backend (§4.4 chế độ `chia` bước 5) — vi phạm chặn.

```bash
grep -nE "\b(100|200|0\.01|112|128|512)\b" scripts/benchmark_recognize.py
```

Giải trình **từng dòng** không rỗng. Ngoại lệ hợp lệ: `SO_MAU_TOI_THIEU = 100` (R9) đặt thành hằng
số có tên kèm chú thích dẫn nguồn. `200` và `0.01` **không** được xuất hiện — chúng đến từ
`configs/recognize.yaml` (§5.2). Giá trị mặc định của tham số CLI không tính là hardcode.

```bash
grep -nE "raise (ValueError|TypeError|Exception)" scripts/benchmark_recognize.py
```

Phải **rỗng** — ngoại lệ dùng lớp trong `src/common/exceptions.py`.

---

## 10. Phép đột biến bắt buộc

Mỗi phép: sao lưu tệp **ra ngoài repo** → sửa → chạy `pytest tests/test_benchmark_recognize.py -q`
→ ghi ca đỏ → khôi phục → đối chiếu `sha256`. Tuyệt đối không `git checkout -- <tệp>`.

| # | Phép đột biến | Ca **phải** đỏ |
|---|---|---|
| ĐB1 | Bỏ hẳn phép loại ảnh đã đăng ký khỏi tập probe | 34, 35 |
| ĐB2 | ★ Loại theo **đường dẫn** thay vì theo mã băm nội dung | **35** (34 vẫn xanh) |
| ĐB3 | `bam_danh_sach_tep` băm danh sách đường dẫn, bỏ mã băm nội dung | 04 |
| ĐB4 | Đổi `>=` thành `>` trong điều kiện chấp nhận `top1_score >= t` | 61 |
| ĐB5 | `nguong_far_muc_tieu` lấy ngưỡng **lớn nhất** thoả điều kiện | 67 |
| ĐB6 | EER lấy `\|far - frr\|` **lớn nhất** | 65 |
| ĐB7 | Bỏ chốt "không còn probe genuine" | 36a |
| ĐB8 | Bỏ đối chiếu `so_anh_dung` với số ảnh tìm được | 30 |
| ĐB9 | Dựng backend cả khi `--dry-run` | 118 |
| ĐB10 | Tự tính vectơ trung bình thay vì gọi `backend.enroll` | 20 |
| ĐB11 | Dùng một `random.Random(seed)` chung cho cả lượt thay vì theo từng người | 16 |
| ĐB12 | Bỏ chốt từ chối ghi đè tệp đã tồn tại | 104, 105 |
| ĐB13 | Bỏ `math.isfinite` khi kiểm `far_muc_tieu` | 70, 71, 72 |
| ĐB14 | `bam_danh_sach_anh_probe` tính trên danh sách ứng viên thay vì ảnh đo được | 98 |

**ĐB2 là phép quan trọng nhất.** Nó dựng lại một cài đặt **tự nhất quán**: loại theo đường dẫn trông
hoàn toàn hợp lý, qua được ca 34, và chỉ trượt ca 35. Nếu ĐB2 không làm ca nào đỏ thì ca 35 chưa
canh đúng chỗ — sửa ca test, đừng sửa mã sản phẩm.

**ĐB13** canh đúng lỗi đã xảy ra ở `P3-01`: liệt kê đủ `0`, số âm, chuỗi mà quên ba giá trị không
hữu hạn, để rồi chúng lọt qua mọi phép kiểm kiểu.

---

## 11. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black --line-length 100`, `ruff` sạch. Type hints, docstring tiếng Việt kiểu Google.
- **Thư viện được phép**: thư viện chuẩn (`hashlib`, `csv`, `json`, `math`, `random`, `argparse`,
  `datetime`, `platform`, `subprocess`, `time`, `importlib.metadata`, `pathlib`), cộng `numpy`,
  `cv2`, `onnxruntime`, và `src/**` + `scripts/**` của dự án. **Không thêm phụ thuộc mới**, không
  `matplotlib`, không `scipy`, không `sklearn`, không `pandas`.
- Đọc ảnh **chỉ bằng `cv2.imread`** — cùng thư viện mà `enroll.py` và `preprocess.py` dùng.
  Ca kiểm thử **tạo** ảnh mẫu bằng `cv2.imwrite` từ mảng `numpy`; không cần thêm thư viện nào và
  không được đọc ảnh thật trong `data/` (thư mục đó không có trong container).
- Đo thời gian bằng `time.perf_counter()`, không `time.time()`.
- `logging` qua `src.common.logging.lay_logger`; `print()` chỉ cho bảng tóm tắt CLI (G2).
- Log lazy formatting (G3). **Không log đường dẫn ảnh khuôn mặt ở mức `INFO`** — mức `DEBUG`.
- Đọc cấu hình qua `src.common.config.nap_cau_hinh` / `lay_gia_tri`.
- Ngoại lệ: `LoiCauHinh` cho lỗi cấu hình/đầu vào, `LoiMoHinh` cho lỗi mô hình. Không `except
  Exception` trần.
- Thư mục kết quả mặc định đặt thành **hằng số module** để ca test `monkeypatch` ra `tmp_path` —
  cùng cách `benchmark_detect.py:61` làm. Ca test **không được** ghi vào `results/` thật.
- Chạy được trên Windows lẫn Linux: `pathlib`, `newline=""` khi mở CSV, `encoding="utf-8"`.
- **Không chạy** `scripts/benchmark_recognize.py` ở chế độ ghi thật — đó là lượt của người dùng §12b.
- Không commit, không dựng image, không `pip install`.

---

## 12. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Vẽ ROC/DET, vẽ bất kỳ hình nào.** Thuộc `notebooks/06_nguong_va_roc.ipynb` và `scripts/plot_*.py`.
- **Ghi ngưỡng đã chốt vào `configs/recognize.yaml`.** Script chỉ **báo cáo**; việc chốt là bước
  3.7c, do người dùng làm sau khi có số trên dữ liệu thật.
- **Domain adaptation** và ba con số `FAR_lfw` / `FAR_adapt` / `FAR_indomain` — bước 1.8, 3.7, 3.7b.
  `data/impostor/lfw_adapted/` và `data/impostor/indomain/` chưa tồn tại.
- **Kiểm định thống kê** (McNemar, Mann–Whitney) khi so hai backend — thuộc bước 3.8.
- **Tạo `data/splits/`** — bước 1.11. Script chỉ **nhận** tệp danh sách danh tính.
- **Đo trên Raspberry Pi 5** — cần phần cứng chưa có.
- **Sửa `scripts/enroll.py`** để ghi danh sách tệp đã dùng đăng ký vào manifest. Sẽ làm cho chế độ
  `tep` chắc chắn hơn (khỏi phải suy lại tập enroll ở §4.4 bước 6), nhưng là mã việc riêng —
  ghi lại đây để không quên.

---

## 12a. Việc người dùng phải làm TRƯỚC khi chạy §12b

Thêm khối sau vào `configs/recognize.yaml` (§5.2). `configs/` không nằm trong danh sách trắng của
người cài đặt.

```yaml
# --- Tham số quét ngưỡng (bước 3.5) ---
benchmark:
  # Số bước quét ngưỡng — experiment-protocol.instructions.md §5 điểm 2.
  so_buoc_nguong: 200

  # Chỉ tiêu FAR để chốt ngưỡng, dạng số để máy đọc được.
  # Đây là bản máy-đọc-được của khoá tieu_chi_chot_nguong ở trên ("FAR_adapt <= 0.01").
  # ⚠️ Hai khoá phải nhất quán: sửa một thì sửa cả hai.
  far_muc_tieu: 0.01
```

## 12b. Lượt chạy thật — người dùng chạy, sau khi §9 xanh

Ba lệnh đầu chạy ở chế độ `chia` vì gallery LFW trên đĩa **không còn probe genuine nào** (§3.2).

```bash
python scripts/benchmark_recognize.py --vao data/processed/lfw_original --backend dlib --tap kiem-chuc-nang --che-do-gallery chia --enroll-moi-nguoi 2 --device-name "PC phát triển"
```

```bash
python scripts/benchmark_recognize.py --vao data/processed/lfw_original --backend arcface --tap kiem-chuc-nang --che-do-gallery chia --enroll-moi-nguoi 2 --device-name "PC phát triển"
```

Kỳ vọng cả hai: mã trả về `0`; gallery **8 người**; probe genuine **22**; probe impostor bằng tổng
ảnh của 143 danh tính còn lại; meta có `canh_bao_co_mau` (22 < 100) và `canh_bao_chia_tap` và
`canh_bao_hieu_nang` (`moi_truong = pc_x86`); ba tệp `results/bench_recognize_{dlib,arcface}_*`.

```bash
python scripts/benchmark_recognize.py --vao data/processed/lfw_original --backend dlib --tap kiem-chuc-nang --device-name "PC phát triển"
```

⭐ Lệnh này **phải hỏng**, mã trả về `1`, thông báo nêu không còn probe genuine nào. Đây là chốt
§4.1 hoạt động đúng trên dữ liệu thật, không phải sự cố. Xác nhận **không tệp nào** được ghi thêm
vào `results/`.

```bash
python scripts/benchmark_recognize.py --vao data/processed/lfw_original --backend dlib --tap kiem-chuc-nang --che-do-gallery chia --enroll-moi-nguoi 2 --device-name "PC phát triển" --dry-run
```

Kỳ vọng: in kế hoạch, mã trả về `0`, **không** tệp nào được ghi.

⚠️ Mọi con số của bốn lệnh trên là **số kiểm chức năng trên LFW**, không phải số báo cáo. Gallery
8 người LFW không phải gallery của đồ án; số kết luận chỉ tiêu §1 phải đến từ gallery **2–3 người
nhà** đo trên **Raspberry Pi 5 thật**. Điều này phải được nói rõ ở mọi chỗ trích dẫn các tệp kết quả
này.

---

## 13. Báo cáo khi xong

1. Kết quả **bảy** lệnh §9.1, trên host **và** trong container, kèm số ca mới đếm được ở cả hai nơi.
2. Kết quả **sáu** lệnh `grep` §9.2, giải trình từng dòng không rỗng.
3. Kết quả **mười bốn** phép đột biến §10, kèm `sha256` khôi phục. Nêu rõ ĐB2 làm ca nào đỏ.
4. Đối chiếu từng nhóm của bảng §8: mỗi dòng có ca test tương ứng chưa.
5. Chỗ nào của đặc tả bạn phải tự diễn giải, và diễn giải theo hướng nào.
6. Vướng mắc.

**Không commit.** Không chạy §12b. Để nguyên cây làm việc cho người review.
