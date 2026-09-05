# P0-04 — Tương thích Python 3.11.2 của Raspberry Pi OS và dọn phụ thuộc

| | |
|---|---|
| **Nguồn** | Lượt chạy `pytest` đầu tiên trên Raspberry Pi 5 thật, 05/09/2026 |
| **Phase / bước** | Phase 0, bước 0.2 và 0.4 (mở lại sau khi phần cứng về) |
| **Nhánh** | `feat/p0-04-tuong-thich-pi-os` |
| **Phụ thuộc** | `dev` tại `57b874c` |
| **Chặn** | Mọi lượt đo trên `pi5` — Cổng C của Phase 2, 3, 4 |
| **Ước lượng** | 7 tệp, ~250 dòng mã sản phẩm + kiểm thử |

---

## 1. Mục tiêu

Làm cho toàn bộ bộ kiểm thử chạy xanh trên **Python 3.11.2** của Raspberry Pi OS Bookworm, và
làm cho việc cài đặt trên thiết bị đích không kéo theo gói không cần thiết.

Bốn việc, ba chế độ hỏng khác nhau:

| Việc | Chế độ hỏng đã quan sát trên Pi |
|---|---|
| 1 | `giai_nen` gọi API chỉ có từ Python 3.11.4 → **7 ca đỏ** |
| 2 | Dấu `pytest.mark.slow` chưa khai báo → 33 cảnh báo, và sẽ thành 33 ca đỏ nếu ai bật `--strict-markers` |
| 3 | Hai ca kiểm thử phụ thuộc thư mục bị `.gitignore` → **1 ca đỏ + 1 ca xanh giả** |
| 4 | `requirements-dev.txt` kéo `ultralytics` → `torch` → **~2,5 GB thư viện CUDA** lên máy không có GPU NVIDIA |

---

## 2. Phạm vi tệp — danh sách trắng

| # | Tệp | Thao tác |
|---|---|---|
| 1 | `scripts/download_lfw.py` | sửa — chỉ hàm `giai_nen` và phần hằng số/`import` nó cần |
| 2 | `tests/test_download_lfw.py` | sửa — **chỉ cộng ca mới 29–36**, không xoá, không đổi ca 01–28 |
| 3 | `tests/test_export_detector.py` | sửa — ca 39, 40 và hai hàm trợ giúp; cộng ca 43, 44 |
| 4 | `tests/test_cau_hinh_pytest.py` | **tạo mới** |
| 5 | `pyproject.toml` | sửa — chỉ mục `[tool.pytest.ini_options]` |
| 6 | `requirements-dev.txt` | sửa |
| 7 | `README.md` | sửa — thêm mục cài đặt trên Raspberry Pi 5 |

**Tệp cấm chạm, kèm lý do:**

| Tệp | Vì sao không sửa |
|---|---|
| `requirements.txt` | Xem §7.1 — `ncnn` **đã** nằm ở dòng 9, không có gói nào phải thêm hay bớt. Sửa tệp này, dù chỉ sửa dòng chú thích, buộc dựng lại `faceid:arm64` theo R43 (~18 phút) mà không đổi một gói nào. |
| `deploy/Dockerfile.arm64` | Không có việc gì cần đổi; sửa nó cũng buộc dựng lại image (R43). |
| `configs/**` | Mã việc này không sinh tham số cấu hình nào. |
| `src/**` | Lỗi nằm ở `scripts/` và ở cấu hình kiểm thử, không nằm trong mã sản phẩm của `src/`. |

> Sửa tệp ngoài danh sách trắng = lỗi CHẶN-A khi review.

---

## 3. Dữ kiện — đã kiểm ngày 05/09/2026

### 3.1. Môi trường

| Dữ kiện | Giá trị |
|---|---|
| Pi 5 | Raspberry Pi OS Bookworm 64-bit, `Linux-6.12.93+rpt-rpi-2712-aarch64-with-glibc2.36` |
| Python trên Pi | **3.11.2** |
| Python trên máy phát triển | 3.12.5 |
| Ảnh nền container | `python:3.11-slim-bookworm` (`deploy/Dockerfile.arm64:1`) — Python 3.11.**x mới nhất**, tức ≥ 3.11.4 |
| `pytest -q -m "not slow"` trên Pi | **7 failed, 490 passed, 2 skipped, 32 deselected** (531 ca thu thập) |

### 3.2. Việc 1 — API `tarfile` không tồn tại ở 3.11.2

| Dữ kiện | Vị trí |
|---|---|
| `tf.extractall(dich, filter="data")` | `scripts/download_lfw.py:110` |
| `except tarfile.FilterError as e:` | `scripts/download_lfw.py:111` |
| Thông báo "vượt ra ngoài" | `:114-116` |
| Thông báo "hỏng" | `:118` |
| `getmembers()` đã được gọi sẵn trước khi giải nén | `:109` |

Tham số `filter=` của `TarFile.extractall` và lớp `tarfile.FilterError` xuất hiện từ Python 3.12,
được backport về nhánh 3.11 **kể từ 3.11.4**. Bookworm đóng gói 3.11.2 nên cả hai đều vắng mặt:

```
TypeError: TarFile.extractall() got an unexpected keyword argument 'filter'
AttributeError: module 'tarfile' has no attribute 'FilterError'
```

Bảy ca đỏ, tất cả trong `tests/test_download_lfw.py`: `test_03_giai_nen_thanh_cong`,
`test_04_giai_nen_tep_hong`, `test_05_giai_nen_chan_duong_dan_vuot_ra_ngoai`,
`test_24a_main_expect_sha256_khop`, `test_27_main_chay_lai_lech_seed_tra_ve_1`,
`test_27a_main_lech_seed_giu_nguyen_du_lieu_cu`, `test_28_main_chay_lai_cung_seed_thanh_cong`.

Hai ca canh **thông báo phân biệt** đã có sẵn và phải tiếp tục xanh nguyên văn:

- `tests/test_download_lfw.py:129-130` — `"hỏng" in thong_bao` và `"vượt ra ngoài" not in thong_bao`
- `tests/test_download_lfw.py:147-148` — `"vượt ra ngoài" in thong_bao` và `"hỏng" not in thong_bao`

### 3.3. Việc 2 — dấu kiểm thử

| Dữ kiện | Giá trị |
|---|---|
| `[tool.pytest.ini_options]` hiện có | `testpaths`, `pythonpath` — `pyproject.toml:7-9` |
| Không có `conftest.py` nào trong kho | đã quét toàn kho |
| Dấu tuỳ biến đang dùng | **duy nhất `slow`**, 33 chỗ trong 10 tệp |
| Dấu dựng sẵn đang dùng | `parametrize` (`test_collect_faces.py:368`, `test_enroll.py:420`) — không cần khai báo |

Đã quét toàn bộ `tests/` bằng `@pytest\.mark\.[a-zA-Z_]+`: chỉ có hai tên trên. Không có dấu tuỳ
biến nào khác bị bỏ sót.

### 3.4. Việc 3 — ca phụ thuộc thư mục bị gitignore

| Dữ kiện | Vị trí |
|---|---|
| `_DUONG_DAN_LFW_THAT = Path("data/impostor/lfw_original")` | `tests/test_export_detector.py:34` |
| `_DUONG_DAN_WEIGHTS_THAT = Path("models/yolov8n-face.pt")` | `:33` |
| `_vai_anh_lfw_that` — `rglob("*.jpg")[:n]`, không kiểm rỗng | `:62-64` |
| `_sao_chep_weights_tam` — `shutil.copy2` thẳng, không kiểm tồn tại | `:55-59` |
| `test_dong39_chon_mau_anh_cung_seed_tai_lap` | `:495-498` |
| `test_dong40_chon_mau_anh_khac_seed_khac_ket_qua` | `:501-504` |
| `_chon_mau_anh` — lọc **theo đuôi tệp**, không đọc nội dung ảnh | `scripts/export_detector.py:468-477` |
| `.gitignore` chặn `data/*` và `models/*` | `.gitignore:228, 233` |

Khi `data/impostor/lfw_original/` vắng mặt, `_chon_mau_anh` trả về `[]`:

- ca 40 **đỏ** vì `[] != []` là sai;
- ca 39 **xanh giả** vì `[] == []` là đúng — ca này xanh bất kể `_chon_mau_anh` đúng hay sai.

**Kết quả rà toàn bộ `tests/`** tìm ca cùng dạng khuyết tật (chạm `data/` hoặc `models/` mà không
có người gác). Mọi tệp còn lại **đều đã có** hàm `_bo_qua_neu_thieu` hoặc `pytest.skip` tương đương:
`test_enroll.py:165-173`, `test_ncnn_backend.py:43-45`, `test_dlib_backend.py:76-84,123,130`,
`test_recognizer.py:66-73,147`, `test_detector_factory.py:35-37`, `test_recognizer_factory.py:28-36`,
`test_yolo_face.py:49-51`. `test_export_detector.py` là **tệp duy nhất không có người gác nào**.

Hai điểm cận biên đã xem xét và **không** đưa vào phạm vi, ghi ở §14 kèm lý do:
`test_export_detector.py:465-474` và `test_export_detector_ncnn.py:410-419` so hai tập
`Path("models").rglob("*")` trước/sau `--dry-run`. Cả hai thư mục `models/` và `results/` **có tồn
tại** trong kho (`.gitignore:234` giữ `models/README.md`), nên phép so không rỗng và không phải
xanh giả.

### 3.5. Việc 4 — phụ thuộc

Gói bên thứ ba được `src/` import **ở mức module** (chạy là cần ngay):

| Gói | Vị trí dẫn chứng |
|---|---|
| `numpy` | `src/common/types.py:5`, `src/detector/yolo_face.py:13`, `src/recognizer/base.py:11` |
| `pyyaml` | `src/common/config.py:8`, `src/detector/ncnn_backend.py:15` |
| `opencv-python` | `src/preprocess/align.py:8`, `src/recognizer/dlib_backend.py:31`, `src/capture/opencv_camera.py:3` |
| `onnxruntime` | `src/detector/yolo_face.py:14`, `src/recognizer/arcface_backend.py:18` |

Gói được `src/` import **bên trong thân hàm** (vẫn là phụ thuộc chạy, chỉ nạp muộn):

| Gói | Vị trí dẫn chứng |
|---|---|
| `ncnn` | `src/detector/ncnn_backend.py:133` và `:187` |
| `dlib` | `src/recognizer/dlib_backend.py:201` |
| `opencv-python` | `src/capture/mock_camera.py:92` |

Gói **chỉ** `scripts/export_*.py` cần:

| Gói | Vị trí dẫn chứng |
|---|---|
| `ultralytics` | `scripts/export_detector.py:175`, `:368`, `:501`; `scripts/export_detector_ncnn.py:71` |
| `onnx`, `torch` | `scripts/export_detector.py:498`, `:500` — cả hai chỉ trong thân hàm |

Trạng thái hai tệp requirements hiện tại:

| Dữ kiện | Vị trí |
|---|---|
| `ncnn==1.0.20260526` | `requirements.txt:9` **và** `requirements-dev.txt:10` — **trùng lặp** |
| `ultralytics==8.4.39` | `requirements-dev.txt:9` |
| `-r requirements.txt` | `requirements-dev.txt:8` |
| Dockerfile lọc gói công cụ bằng `grep -E "^(pytest\|black\|ruff)=="` | `deploy/Dockerfile.arm64:13` |

Đo trên Pi: cài `requirements-dev.txt` → `.venv` khoảng **2,9 GB**, trong đó `nvidia-cudnn-cu13`
651 MB, `nvidia-cublas` 543 MB, `torch` 454 MB, `triton` 226 MB và hơn mười gói `nvidia-*` khác.
Dựng lại chỉ với `requirements.txt` cộng bốn gói công cụ → **420 MB**.

### 3.6. Chú thích đã lỗi thời, cố ý để ngoài phạm vi

`tests/test_export_detector_ncnn.py:7-10` viết rằng `ncnn` "không có trong `requirements.txt`/
container ARM64". Câu này **sai** kể từ khi `ncnn` được đưa vào `requirements.txt:9`. Sửa nó không
đổi hành vi ca test nào và sẽ mở rộng danh sách trắng — ghi ở §14.

---

## 4. Tham số → config

**Không có.** Mã việc này không đưa ra hằng số nào thuộc về miền bài toán. Ba hằng số kỹ thuật
sinh ra ở đây đều đặt trong tệp dùng chúng, có tên rõ ràng:

| Hằng số | Đặt ở | Giá trị | Vì sao không vào `configs/` |
|---|---|---|---|
| Thông báo lỗi "vượt ra ngoài" | `scripts/download_lfw.py` | xem §5.2 | Chuỗi thông báo, không phải tham số vận hành |
| Thông báo lỗi "hỏng" | `scripts/download_lfw.py` | xem §5.2 | như trên |
| `_TOI_THIEU_ANH_LAY_MAU = 100` | `tests/test_export_detector.py` | 100 | Ngưỡng của **ca kiểm thử**, không của mã sản phẩm |

---

## 5. Thiết kế bắt buộc — Việc 1: `giai_nen`

### 5.1. Chữ ký giữ nguyên

```python
def giai_nen(archive: Path, dich: Path) -> Path: ...
```

Không đổi tên, không thêm tham số, không đổi kiểu trả về, không đổi lớp ngoại lệ (`LoiCauHinh`).
Mọi lời gọi hiện có (`scripts/download_lfw.py:363`) phải chạy y nguyên.

### 5.2. Ba thông báo lỗi, đặt thành hằng số ở mức module

Hai nhánh cài đặt sẽ tồn tại song song. Cách duy nhất bảo đảm chúng nói cùng một câu là **cùng
đọc một hằng số**, chứ không phải hai chuỗi giống nhau viết ở hai chỗ.

| Hằng số | Nội dung bắt buộc chứa | Bắt buộc **không** chứa |
|---|---|---|
| `_MSG_VUOT_RA_NGOAI` | `vượt ra ngoài` | `hỏng`, `không an toàn` |
| `_MSG_HONG` | `hỏng` | `vượt ra ngoài`, `không an toàn` |
| `_MSG_KHONG_AN_TOAN` | `không an toàn` | `hỏng`, `vượt ra ngoài` |

Nội dung hai hằng đầu phải giữ nguyên câu chữ hiện có ở `:114-116` và `:118` (kèm đường dẫn
`archive`), để ca 04 và ca 05 không phải sửa. Hằng thứ ba là mới — xem §5.4.

### 5.3. Chọn nhánh **tại thời điểm gọi**, không tại thời điểm import

```python
if hasattr(tarfile, "data_filter"):   # phải nằm TRONG thân giai_nen
```

Lý do bắt buộc: đây là chốt duy nhất cho phép ép chạy nhánh dự phòng trên máy Python 3.12 bằng
`monkeypatch.delattr(tarfile, "data_filter", raising=False)`. Nếu người cài đặt tính sẵn
`_CO_DATA_FILTER = hasattr(...)` ở mức module thì phép ép mất tác dụng và **nhánh dự phòng sẽ không
bao giờ được kiểm ở đâu ngoài Pi** — tức là quay lại đúng chỗ hỏng mà mã việc này sinh ra để sửa.
Phép đột biến ĐB5 ở §11 canh đúng điều này.

Dùng `hasattr(tarfile, "data_filter")` chứ không dùng `sys.version_info`: điều kiện thật là "thư
viện chuẩn có sẵn cơ chế lọc hay không", và bản backport 3.11.4 làm mệnh đề theo số phiên bản trở
nên rắc rối không cần thiết.

### 5.4. Quét thành viên — chạy ở **cả hai** nhánh

Trước khi giải nén, duyệt danh sách đã có ở `:109` và từ chối mọi thành viên **không phải** tệp
thường hoặc thư mục — liên kết mềm, liên kết cứng, tệp thiết bị ký tự, tệp thiết bị khối, FIFO:

```python
if not (tv.isfile() or tv.isdir()):
    raise LoiCauHinh(_MSG_KHONG_AN_TOAN...)
```

Phép quét này **cố ý đặt ngoài** nhánh `if/else`. Bộ lọc `data` của thư viện chuẩn cho phép liên
kết trỏ vào bên trong thư mục đích, còn nhánh dự phòng thì không có cách nào kiểm điều đó cho rẻ.
Nếu để mỗi nhánh tự xử lý, hai nhánh sẽ **khác nhau ở đúng chỗ khó thấy nhất**. Đặt phép quét ra
ngoài làm hai nhánh xử lý liên kết y hệt nhau, đổi lại `giai_nen` chặt hơn bộ lọc `data` một bậc.

Cái giá của việc chặt hơn: nếu một ngày nào đó tệp nén nguồn có liên kết mềm hợp lệ, `giai_nen` sẽ
từ chối. Chấp nhận được — LFW chỉ gồm thư mục và tệp `.jpg` thường, và một thông báo lỗi rõ ràng
tốt hơn một khác biệt âm thầm giữa hai nền tảng.

### 5.5. Nhánh A — thư viện chuẩn có `data_filter`

Giữ nguyên `tf.extractall(dich, filter="data")` và giữ nguyên thứ tự bắt ngoại lệ hiện có:
`FilterError` **trước** `TarError` (ghi chú ở `:112-113` giải thích vì sao, giữ lại ghi chú đó).

### 5.6. Nhánh B — dự phòng cho Python < 3.11.4

Tự kiểm từng thành viên trước khi gọi `tf.extractall(dich)` **không có** tham số `filter`.

Phép kiểm bắt buộc, **duy nhất một phép**, là phép chứa trong thư mục đích:

```
dich_that = dich.resolve()
đích_thành_viên = (dich / tv.name).resolve()
nếu không đích_thành_viên.is_relative_to(dich_that)  →  raise LoiCauHinh(_MSG_VUOT_RA_NGOAI...)
```

Vì sao **không** dùng `Path(tv.name).is_absolute()` làm phép kiểm chính: trên Windows,
`PurePath("/tmp/x").is_absolute()` trả về `False` vì thiếu ký tự ổ đĩa, nên phép kiểm đó bỏ lọt
đúng ca 32 ở §10. Phép hợp đường dẫn rồi `resolve()` bắt được cả hai nền tảng: trên POSIX
`Path("/a/b") / "/tmp/x"` cho `/tmp/x`, trên Windows `Path("D:/a/b") / "/tmp/x"` cho `D:/tmp/x` —
cả hai đều nằm ngoài `dich`.

`dich` đã được `mkdir(parents=True, exist_ok=True)` ở `:106` nên `resolve()` không phụ thuộc thứ
tự tạo thư mục. Phải `resolve()` **cả hai vế** để không lệch nhau khi đường dẫn tạm đi qua liên
kết mềm (macOS đặt `/tmp` là liên kết tới `/private/tmp`).

### 5.7. Thư viện được phép dùng

**Chỉ thư viện chuẩn**: `tarfile`, `pathlib`, `os`. Không thêm phụ thuộc nào — docstring đầu tệp
`scripts/download_lfw.py:3-4` đã cam kết điều đó và cam kết ấy vẫn giữ nguyên.

### 5.8. Cảnh báo `DeprecationWarning` là bình thường

Trên Python ≥ 3.12, khi ca test ép chạy nhánh B, lời gọi `extractall(dich)` không có `filter` sẽ
phát `DeprecationWarning`. Đây là hành vi đúng của thư viện chuẩn, **không** phải khuyết tật.
**Cấm** thêm `-W error` hay `filterwarnings = ["error"]` vào `pyproject.toml` ở mã việc này; nếu
tiếng ồn gây khó chịu thì bọc lời gọi trong ca test bằng `warnings.catch_warnings()`, không sửa
cấu hình toàn kho.

---

## 6. Thiết kế bắt buộc — Việc 2: dấu kiểm thử

Trong `[tool.pytest.ini_options]` của `pyproject.toml`, thêm đúng hai khoá:

```toml
markers = [
    "slow: ca cần mô hình/dữ liệu thật hoặc chạy lâu; lọc bằng -m \"not slow\"",
]
addopts = ["--strict-markers"]
```

Giữ nguyên `testpaths` và `pythonpath`. Không thêm khoá nào khác.

**Chốt bật `--strict-markers`.** Lý do: dấu viết sai chính tả hiện nay **không** làm gì cả — ca
mang dấu sai vẫn chạy, vẫn xanh, và vẫn lọt qua `-m "not slow"` khiến một ca lẽ ra phải bị loại
lại chạy trên máy thiếu mô hình. Bật cờ này biến lỗi im lặng thành lỗi ồn ào ngay lượt chạy đầu.
Giá phải trả bằng không: toàn kho chỉ dùng một dấu tuỳ biến duy nhất (§3.3).

---

## 7. Thiết kế bắt buộc — Việc 3 và Việc 4

### 7.1. Việc 4 — hai tệp requirements

**`requirements.txt`: không sửa.** `ncnn` đã ở dòng 9, `dlib-bin` ở dòng 10, `onnxruntime` dòng 8,
`opencv-python` dòng 11, `numpy` dòng 12, `pyyaml` dòng 13 — đúng khớp danh sách phụ thuộc chạy
xác minh được ở §3.5. Không gói nào phải thêm, không gói nào phải bớt.

> Tiền đề của việc này trong bản giao việc — "`ncnn` đang nằm trong `requirements-dev.txt` chứ
> không phải `requirements.txt`" — **không đúng với trạng thái kho tại `57b874c`**. Nó nằm ở **cả
> hai**. Sai lệch thực tế là một dòng **trùng lặp**, không phải một gói xếp nhầm nhóm.

**`requirements-dev.txt`: hai thay đổi.**

1. Xoá dòng 10 `ncnn==1.0.20260526`. Tệp này đã có `-r requirements.txt` ở dòng 8 nên `ncnn` vẫn
   được cài đủ; giữ hai chỗ ghim phiên bản cho cùng một gói là mời gọi hai chỗ lệch nhau.
2. Thay khối chú thích đầu tệp (dòng 1–7, đã lỗi thời — nó nói `P0-03` "sẽ" kiểm chứng, mà `P0-03`
   đã đóng) bằng chú thích nêu rõ:
   - `ultralytics` **chỉ** `scripts/export_*.py` cần, dẫn `scripts/export_detector.py:175`;
   - nó kéo theo `torch` bản đầy đủ và khoảng **2,5 GB** thư viện CUDA của NVIDIA;
   - vì vậy **không cài tệp này lên Raspberry Pi 5** — thiết bị đích chỉ chạy, không export;
   - trỏ sang mục cài đặt Pi trong `README.md`.

**Không tạo `requirements-pi.txt`.** Đã cân nhắc và loại: `deploy/Dockerfile.arm64:13` lấy bộ gói
công cụ bằng `grep -E "^(pytest|black|ruff)==" requirements-dev.txt`. Thêm một tệp thứ ba nữa thì
có ba nguồn sự thật cho cùng một danh sách, và tệp mới không được Dockerfile nhìn tới nên sẽ lặng
lẽ trôi lệch. `README.md` chỉ cần dạy đúng một câu lệnh dùng lại chính hai tệp đang có.

### 7.2. Việc 4 — mục cài đặt trong `README.md`

**Chọn `README.md`, không chọn `models/README.md`.** `models/README.md` là sổ ghi trọng số — cấu
trúc của nó là hai bảng A/B về nguồn tải và cách sinh tệp, một mục cài đặt môi trường đặt vào đó sẽ
lạc chỗ và không ai tìm thấy. `README.md` hiện chỉ có hai dòng, trong khi checklist trước khi nộp
(`CLAUDE.md` §7) đòi "`README.md` cho phép người khác dựng lại hệ thống từ đầu".

Mục mới phải nêu, mỗi ý một dòng kiểm được:

1. Python của Raspberry Pi OS Bookworm là **3.11.2**; dự án yêu cầu ≥ 3.11.
2. Lệnh cài trên thiết bị đích — đúng một lệnh, không kèm `ultralytics`:
   `pip install -r requirements.txt`
3. Lệnh cài thêm bộ công cụ để chạy được `pytest` trên thiết bị, ghim đúng phiên bản đang có ở
   `requirements-dev.txt:11-13`.
4. Câu cảnh báo: **không** chạy `pip install -r requirements-dev.txt` trên Pi, kèm con số 2,5 GB
   và lý do (kéo `torch` bản CUDA lên máy không có GPU NVIDIA).
5. Việc export mô hình (`scripts/export_detector.py`, `scripts/export_detector_ncnn.py`) làm trên
   máy phát triển, rồi **chép tệp kết quả** sang Pi — thiết bị đích chỉ nạp mô hình đã export.

### 7.3. Việc 3 — sửa ca 39 và ca 40

`_chon_mau_anh` lọc theo **đuôi tệp**, không mở ảnh (`scripts/export_detector.py:468-472`). Hai ca
39/40 vì thế **chưa bao giờ cần ảnh thật**. Sửa chúng dùng `tmp_path` chứa 100 tệp `.jpg` rỗng do
chính ca test tạo ra. Kết quả: hai ca chạy được ở mọi nơi, và lần đầu tiên chúng thật sự canh được
tính tái lập của `random.Random(seed)`.

Chọn **100** tệp chứ không phải 21: hàm trả nguyên danh sách khi `len(danh_sach) <= so_anh`
(`:473-474`), nên phải có **nhiều hơn** 20 tệp thì phép lấy mẫu mới thực sự diễn ra. Với 21 tệp,
xác suất hai seed khác nhau chọn trúng cùng 20 tệp là 1/21 — ca 40 sẽ đỏ ngẫu nhiên. Với 100 tệp,
xác suất đó là 1/C(100,20) ≈ 10⁻²⁰.

Đặt ngưỡng thành hằng số có tên `_TOI_THIEU_ANH_LAY_MAU = 100` để ca 43 dùng lại.

### 7.4. Việc 3 — người gác cho hai hàm trợ giúp

Thêm vào `tests/test_export_detector.py` một hàm `_bo_qua_neu_thieu(duong_dan: Path) -> None` theo
đúng khuôn đã dùng ở `tests/test_yolo_face.py:49-51`, rồi gọi nó:

- trong `_sao_chep_weights_tam` — trước `shutil.copy2`, để thiếu `models/yolov8n-face.pt` cho
  **skip có thông báo** thay vì `FileNotFoundError`;
- trong `_vai_anh_lfw_that` — sau khi quét, `pytest.skip` nếu tìm được **ít hơn** `so_luong` ảnh,
  thông báo nêu tên thư mục và số ảnh tìm được.

Cả hai chỉ phục vụ ca `@pytest.mark.slow`, nên không đổi kết quả lượt `-m "not slow"`.

---

## 8. Bảng tiêu chí nghiệm thu

Đánh số liên tục. Mỗi dòng phải có ít nhất một ca `pytest` tương ứng.

### 8.1. `tests/test_download_lfw.py` — ca mới 29–36

Mọi ca dựng tệp `.tgz` tại chỗ bằng `tarfile`, **không chạm mạng**. Thành viên liên kết mềm dựng
bằng `TarInfo` với `info.type = tarfile.SYMTYPE` và `info.linkname = ...`, **không** dùng
`os.symlink` (trên Windows lời gọi đó cần quyền quản trị).

| # | Ca | Tiền đề | Kỳ vọng — assert tối thiểu |
|---|---|---|---|
| 29 | Nhánh B, tệp nén hợp lệ một thư mục gốc | `monkeypatch.delattr(tarfile, "data_filter", raising=False)`; tệp nén chứa `lfw/A/a_0001.jpg` | `assert (dich / "lfw" / "A" / "a_0001.jpg").exists()` |
| 29b | như 29 | như 29 | `assert giai_nen(archive, dich) == dich / "lfw"` |
| 30 | Nhánh B, thành viên `../../thoat.txt` | đã ẩn `data_filter`; tệp nén **hợp lệ**, chỉ tên thành viên là độc hại | `with pytest.raises(LoiCauHinh)` và `assert "vượt ra ngoài" in str(exc.value)` |
| 30b | như 30 | như 30 | `assert "hỏng" not in str(exc.value)` |
| 30c | như 30 | như 30 | `assert not any(tmp_path.rglob("thoat.txt"))` |
| 31 | Nhánh B, tệp nén hỏng | đã ẩn `data_filter`; tệp là byte ngẫu nhiên, **không** mở được bằng `tarfile` | `assert "hỏng" in str(exc.value)` |
| 31b | như 31 | như 31 | `assert "vượt ra ngoài" not in str(exc.value)` |
| 32 | Nhánh B, thành viên tên tuyệt đối `/tmp/thoat.txt` | đã ẩn `data_filter`; tệp nén hợp lệ | `assert "vượt ra ngoài" in str(exc.value)` |
| 33 | Nhánh B, thành viên là liên kết mềm trỏ ra ngoài | đã ẩn `data_filter`; tệp nén hợp lệ, thành viên `SYMTYPE` | `assert "không an toàn" in str(exc.value)` |
| 34 | **Nhánh A**, cùng tệp nén của ca 33 | `pytest.skip` nếu `not hasattr(tarfile, "data_filter")` | `assert "không an toàn" in str(exc.value)` — chứng minh hai nhánh xử lý liên kết y hệt |
| 35 | **Hai nhánh, cùng tệp nén `../../thoat.txt`** | skip nếu thiếu `data_filter`; chạy nhánh A rồi chạy lại nhánh B trên bản sao tệp nén | `assert str(loi_A) == str(loi_B)` |
| 36 | **Hai nhánh, cùng tệp nén hợp lệ** | skip nếu thiếu `data_filter`; giải nén vào hai thư mục đích khác nhau | `assert tap_duong_dan_tuong_doi_A == tap_duong_dan_tuong_doi_B` |

Ca 34 và 35 là **cặp then chốt**: chúng là thứ duy nhất chứng minh nhánh dự phòng không âm thầm
khác nhánh chính. Ca 36 là dòng cặp đường thành công của ca 35 — không có nó, một cài đặt luôn ném
lỗi ở cả hai nhánh vẫn qua được ca 35.

Ca 29–33 chạy được trên **cả** Python 3.11.2 lẫn 3.12; ca 34–36 skip trên 3.11.2.

Bảy ca cũ ở §3.2 phải xanh trở lại trên Pi mà **không sửa một dòng nào** trong ca 01–28.

### 8.2. `tests/test_export_detector.py` — sửa ca 39, 40; ca mới 43, 44

| # | Ca | Tiền đề | Kỳ vọng — assert tối thiểu |
|---|---|---|---|
| 39 | `_chon_mau_anh` cùng seed tái lập | `tmp_path` chứa 100 tệp `.jpg` rỗng do ca test tạo | `assert a == b` với `a`, `b` gọi seed 42 |
| 39b | ca 39 không còn chạm dữ liệu thật | — | `assert _DUONG_DAN_LFW_THAT` không xuất hiện trong thân ca 39 (kiểm bằng `grep` ở §10, không bằng pytest) |
| 40 | `_chon_mau_anh` khác seed cho kết quả khác | như 39 | `assert a != b` với seed 42 và seed 7 |
| 40b | kết quả luôn được sắp xếp | như 39 | `assert a == sorted(a)` |
| 43 | `_chon_mau_anh` trên **dữ liệu LFW thật**, cùng seed | `pytest.skip(...)` nếu thư mục có `< _TOI_THIEU_ANH_LAY_MAU` ảnh, thông báo nêu tên thư mục và số ảnh đếm được | `assert a == b` |
| 43b | ca 43 không xanh giả | như 43 | `assert len(a) == 20` |
| 44 | `_chon_mau_anh` trên thư mục **rỗng** | `tmp_path` rỗng | `assert _chon_mau_anh(tmp_path, 20, 42) == []` |

Ca 44 chốt tường minh chính hành vi đã sinh ra xanh giả, để lần sau không ai phải suy đoán.
Ca 43b là người gác của ca 43: thiếu nó, ca 43 tái sinh đúng khuyết tật cũ khi thư mục có đủ 100
ảnh nhưng hàm trả về rỗng vì một lý do khác.

### 8.3. `tests/test_cau_hinh_pytest.py` — tệp mới, ca 45–48

Đọc `pyproject.toml` bằng `tomllib` của thư viện chuẩn. Ca 47/48 gọi pytest con bằng
`subprocess.run([sys.executable, "-m", "pytest", ...])` với `cwd` = gốc kho
(`Path(__file__).resolve().parents[1]`), kèm `-c pyproject.toml` để cấu hình được áp dụng, và
`-p no:cacheprovider` để không ghi `.pytest_cache` vào thư mục tạm. **Không** cần `git`, **không**
cần mạng, **không** cần gói ngoài `requirements.txt`.

| # | Ca | Tiền đề | Kỳ vọng — assert tối thiểu |
|---|---|---|---|
| 45 | `markers` khai báo `slow` | — | `assert any(m.startswith("slow:") for m in cfg["markers"])` |
| 46 | `addopts` bật kiểm dấu nghiêm ngặt | — | `assert "--strict-markers" in cfg["addopts"]` |
| 47 | Dấu **sai chính tả** bị chặn | tệp test tạm trong `tmp_path` có `@pytest.mark.slowww` và một ca luôn `assert True` | `assert kq.returncode != 0` |
| 47b | thông báo chỉ đúng dấu sai | như 47 | `assert "slowww" in kq.stdout` |
| 48 | Dấu **đúng** vẫn chạy được | cùng tệp tạm nhưng dùng `@pytest.mark.slow` | `assert kq.returncode == 0` |

Ca 48 là dòng cặp đường thành công của ca 47: thiếu nó, một cấu hình chặn **mọi** dấu — kể cả
`slow` — vẫn qua được ca 47.

### 8.4. `requirements-dev.txt` và `README.md`

Kiểm bằng lệnh ở §10, không bằng `pytest`.

---

## 9. Lệnh tự kiểm — `coder` chạy, dán nguyên văn kết quả về

Mỗi khối một lệnh. Chạy theo thứ tự; đỏ ở đâu thì sửa rồi chạy lại từ đầu.

```bash
python -m black --check --line-length 100 src tests scripts
```
Mong đợi: `All done!`, 0 tệp cần định dạng lại.

```bash
python -m ruff check src tests scripts
```
Mong đợi: `All checks passed!`

```bash
python -m pytest tests/test_download_lfw.py -v
```
Mong đợi trên máy phát triển Python 3.12: **40 ca** (32 cũ + 8 mới 29–36), **40 passed**, 0 failed,
0 skipped.

```bash
python -m pytest tests/test_export_detector.py -q
```
Mong đợi: **47 ca** thu thập (45 cũ + 2 mới). Số `passed`/`skipped` tuỳ máy có `models/` và
`data/impostor/lfw_original/` hay không — **0 failed** trong mọi trường hợp. Dán nguyên văn dòng
tổng kết.

```bash
python -m pytest tests/test_cau_hinh_pytest.py -v
```
Mong đợi: **4 passed**.

```bash
python -m pytest -q
```
Mong đợi: **545 ca thu thập** (531 hiện có + 14 ca mới), **0 failed**. Nếu con số lệch, nêu rõ ca
nào thêm hoặc bớt so với bảng §8 và vì sao — **không** tự ý chỉnh cho khớp.

```bash
python -m pytest -q -m "not slow"
```
Mong đợi: 0 failed, 32 deselected.

```bash
docker run --rm faceid:arm64 python3 -VV
```
Mong đợi: một bản Python 3.11.**≥ 4** — con số này là bằng chứng cho §13, dán nguyên văn.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```
Mong đợi: 0 failed. Trong container, ca 43 **skip** (không có `data/`), ca 34–36 **chạy** (Python
trong container ≥ 3.11.4 nên có `data_filter`).

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest --collect-only -q
```
Mong đợi: thu thập đủ 545 ca, không lỗi ở khâu thu thập.

```bash
git status --short --untracked-files=all
```
Mong đợi: đúng 7 dòng của §2, không tệp lạ, **không tệp nào trong `data/`, `models/`, `results/`**.

**Thứ container `faceid:arm64` KHÔNG có** — mọi ca test phải chịu được:
`git` (nhị phân) · `.git/` · `docs/`, `models/`, `data/`, `results/`, `report/` (bị `.dockerignore`)
· `ultralytics`, `torch`, `onnx`. Chỉ có `requirements.txt` cộng `pytest`, `black`, `ruff`.
Ca mới ở §8 không đụng tới thứ nào trong danh sách này ngoài `data/` ở ca 43 — ca đó đã có
`pytest.skip`.

---

## 10. Quét mẫu vi phạm

```bash
grep -n "FilterError\|filter=\|data_filter" scripts/download_lfw.py
```
Mọi lần xuất hiện của `FilterError` và `filter="data"` phải nằm **bên trong** nhánh được
`hasattr(tarfile, "data_filter")` bảo vệ. `hasattr(...)` phải nằm trong thân `giai_nen`, không ở
mức module — đối chiếu số dòng với `def giai_nen`.

```bash
grep -rnoE "@pytest\.mark\.[a-zA-Z_]+" tests | grep -oE "[a-zA-Z_]+$" | sort -u
```
Mong đợi đúng hai dòng: `parametrize` và `slow`.

```bash
grep -n "ncnn\|ultralytics" requirements.txt requirements-dev.txt
```
Mong đợi: `ncnn` chỉ xuất hiện ở `requirements.txt`; `ultralytics` chỉ ở `requirements-dev.txt`.

```bash
git diff --stat 57b874c -- requirements.txt deploy/Dockerfile.arm64 configs src
```
Mong đợi: **không có dòng nào** — bốn đường dẫn này nằm ngoài danh sách trắng.

```bash
grep -n "_DUONG_DAN_LFW_THAT" tests/test_export_detector.py
```
Mong đợi: không dòng nào nằm trong thân `test_dong39` hoặc `test_dong40` (§8.2 dòng 39b).

```bash
grep -rn "pip install -r requirements-dev.txt" README.md
```
Mong đợi: nếu có xuất hiện thì phải nằm trong câu cảnh báo **không** làm điều đó trên Pi (§7.2
điều 4), không phải trong hướng dẫn cài đặt thiết bị đích.

---

## 11. Phép đột biến — bốn bước: sao lưu ra ngoài kho → sửa → chạy → khôi phục và đối chiếu `sha256`

| # | Phép sửa | Ca **phải đỏ** |
|---|---|---|
| ĐB1 | Xoá nhánh B, luôn gọi `extractall(filter="data")` | 29 |
| ĐB2 | Trong nhánh B, bỏ phép kiểm chứa-trong-thư-mục-đích | 30c |
| ĐB3 | Trong nhánh B, dùng `_MSG_HONG` thay cho `_MSG_VUOT_RA_NGOAI` | 30, 35 |
| ĐB4 | Bỏ phép quét liên kết/thiết bị ở §5.4 | 33, 34 |
| ĐB5 | Chuyển `hasattr(tarfile, "data_filter")` lên mức module thành `_CO_DATA_FILTER` | 29 |
| ĐB6 | Trong nhánh B, đổi `is_relative_to` thành phép kiểm `Path(tv.name).is_absolute()` | 30c (trên POSIX), 32 (trên Windows) |
| ĐB7 | Xoá `--strict-markers` khỏi `addopts` | 46, 47 |
| ĐB8 | Xoá khoá `markers` khỏi `pyproject.toml` | 45, 48 |
| ĐB9 | Trong `_chon_mau_anh`, thay `rng.sample(...)` bằng `danh_sach[:so_anh]` | 40 |
| ĐB10 | Trỏ `_DUONG_DAN_LFW_THAT` sang một thư mục không tồn tại | **không ca nào đỏ**; ca 43 và 43b chuyển sang `skipped` |

ĐB5 là phép quan trọng nhất của Việc 1: nó dựng lại đúng tình huống "nhánh dự phòng không được
kiểm ở đâu cả".

ĐB10 là phép quan trọng nhất của Việc 3, và nó là phép **duy nhất mong đợi không có ca nào đỏ** —
đó chính là định nghĩa của "khuyết tật đã hết". Dán nguyên văn dòng tổng kết để thấy số `skipped`
tăng đúng 2.

ĐB9 chứng minh ca 40 giờ canh được thuật toán thật, chứ không phải đỏ vì danh sách rỗng như trước.

---

## 12. Ràng buộc kỹ thuật

- Mã chạy được trên **Python 3.11.2** trở lên. Không dùng cú pháp hay API chỉ có từ 3.12.
- `scripts/download_lfw.py` chỉ dùng thư viện chuẩn (§5.7).
- `black` line-length 100, `ruff` sạch.
- Không `except Exception` trần; ngoại lệ dùng lớp trong `src/common/exceptions.py`.
- Ca test ghi vào `tmp_path`, không ghi vào `data/`, `models/`, `results/`.
- Không ca test nào chạm mạng.
- Không commit, không dựng image, không `pip install`.

### 12b. Lượt của người dùng — sau khi §9 và §11 xanh

**Về `faceid:arm64`.** Theo R43, image chỉ phải dựng lại khi `requirements.txt` **hoặc**
`deploy/Dockerfile.arm64` đổi. Mã việc này **cố ý không chạm** cả hai (§2, §7.1), nên
**không phải dựng lại image**. Chỉ khi người cài đặt phát hiện một lý do bắt buộc phải sửa
`requirements.txt` thì mới dừng lại, báo cáo, và **người dùng** — không vai nào khác (R42) — chạy:

```bash
docker build -f deploy/Dockerfile.arm64 -t faceid:arm64 .
```

Cấm đặt tag khác. Cấm để `coder` chạy lệnh này.

**Trên Raspberry Pi 5**, người dùng chạy để nghiệm thu Việc 1 và Việc 4:

```bash
python3 -VV
```
Mong đợi: `3.11.2`.

```bash
python3 -m pytest -q -m "not slow"
```
Mong đợi: **0 failed**. Ca 34, 35, 36 báo `skipped` (Python 3.11.2 không có `data_filter`), cộng
với các ca skip sẵn có.

```bash
python3 -m pytest tests/test_download_lfw.py -q
```
Mong đợi: 40 ca, 0 failed, 3 skipped (ca 34–36). **Bảy ca ở §3.2 phải xanh.**

```bash
du -sh .venv
```
Mong đợi: khoảng **420 MB**, không phải 2,9 GB. Ghi con số đo được vào biên bản review.

---

## 13. Vì sao container `faceid:arm64` không bắt được lỗi này

`deploy/Dockerfile.arm64:1` dùng ảnh nền `python:3.11-slim-bookworm`. Ảnh đó lấy Debian Bookworm
làm hệ điều hành nhưng **tự biên dịch Python 3.11.x mới nhất**, chứ không dùng gói `python3` của
Bookworm. Raspberry Pi OS thì dùng đúng gói của Bookworm — **3.11.2**, đóng băng từ tháng 02/2023.

Khoảng cách ấy chứa đúng bản backport 3.11.4. Container báo "Python 3.11, ARM64, Bookworm" —
trùng khớp với Pi trên cả ba chữ — nhưng vẫn bỏ lọt lỗi. Lệnh `python3 -VV` ở §9 là bằng chứng của
đoạn này.

**Bài học quy trình**, và nó đúng bằng luận điểm đã ghi ở Chương 4 §4.1: `docker_arm64` là môi
trường **tham khảo**, không thay thế được `pi5`. Trước đây luận điểm ấy chỉ nói về **số đo hiệu
năng** (QEMU giả lập nên thời gian không quy đổi được). Mã việc này bổ sung một vế mạnh hơn:
container còn không bảo đảm cả **tính đúng đắn chức năng**, vì bản vá phiên bản phiên dịch khác
nhau. Đề nghị `paper-writer` bổ sung ý này vào §4.1 khi viết — nằm ngoài phạm vi mã việc này.

Hệ quả vận hành: mọi mã việc từ nay chỉ được coi là qua Cổng B khi `pytest` xanh trên **cả**
container **và** Pi 5. Trước 05/09/2026 vế thứ hai không kiểm được vì chưa có phần cứng.

---

## 14. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Sửa chú thích lỗi thời ở `tests/test_export_detector_ncnn.py:7-10`** (nói `ncnn` không có
  trong `requirements.txt`, xem §3.6). Sửa nó phải mở rộng danh sách trắng thêm một tệp và không
  đổi hành vi ca test nào. Ghi lại để mã việc dọn dẹp sau nhặt.
- Hai phép so `Path("models").rglob("*")` trước/sau `--dry-run` ở `test_export_detector.py:465-474`
  và `test_export_detector_ncnn.py:410-419` — đã kiểm ở §3.4, **không** phải xanh giả vì cả hai thư
  mục đều tồn tại trong kho.
- Tạo `requirements-pi.txt` — đã cân nhắc và loại ở §7.1.
- Thêm `filterwarnings` hay `-W error` vào `pyproject.toml` — cấm ở §5.8.
- Nới `giai_nen` để chấp nhận liên kết mềm trỏ vào bên trong thư mục đích — chặt hơn là chủ ý
  (§5.4).
- Cập nhật `docs/dieu-chinh-pham-vi.md`, `CLAUDE.md` §8, hay Chương 4 §4.1 — việc của
  `paper-writer` ở Cổng D.
- Mọi việc thuộc bước 0.4 khác (bật camera, `libcamera-hello`, `systemd`).
- Đo hiệu năng trên Pi 5 — thuộc Cổng C của Phase 2.

---

## 15. Quy tắc áp dụng

`docs/quy-tac-cai-dat.md` — mã liên quan và lý do một dòng:

- **R15/R16** — không đưa hằng số mới vào mã sản phẩm ngoài ba thông báo lỗi (§4).
- **R18** — `requirements-dev.txt` giữ ghim `==`; xoá dòng trùng chứ không nới ghim.
- **R19** — `black` 100 ký tự, `ruff` sạch.
- **R20** — hàm sửa xong vẫn phải có type hints và docstring tiếng Việt kiểu Google.
- **R23** — không `print()` trong `scripts/download_lfw.py` ngoài các bảng kết quả đã có sẵn.
- **R38/R40** — `coder` viết mã, không commit; phải có biên bản review ĐẠT mới gộp.
- **R42** — `coder` chỉ chạy §9 và §11; §12b là lượt của người dùng.
- **R43** — một image duy nhất `faceid:arm64`, và mã việc này cố ý không tạo lý do dựng lại nó.
