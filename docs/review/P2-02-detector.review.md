# Review P2-02-detector — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-02-detector.md` |
| **Nhánh** | `feat/p2-02-detector` (chưa commit, cây làm việc để nguyên) |
| **HEAD khi review** | `8c385ba` |
| **Ngày** | 2026-08-18 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — 0 × CHẶN, **1 × CẦN SỬA**, 6 × GÓP Ý |

> Mã việc gần đạt. Lõi thuật toán **đúng đến từng chữ số** khi đối chiếu độc lập với
> `ultralytics`. Chỉ một lỗ hổng cấu hình phải bịt (~4 dòng) trước khi commit.

---

## 1. Kết luận về bẫy letterbox — ưu tiên số một

### 1.1. Cài đặt letterbox là **ĐÚNG** — chứng minh bằng phép đo độc lập, không đọc mã suông

Tự dựng ảnh **1280×720** (nền xám 200, dán ảnh LFW `Aaron_Peirsol_0001` tại `(800, 300)`),
chạy `detect` rồi chạy `ultralytics` trên **cùng mảng ảnh đó**, `imgsz=320`, `conf=0.5`:

| Nguồn | Khung bao | Tâm khung |
|---|---|---|
| `src/detector/yolo_face.py` | `[881, 368, 972, 483]` conf 0.8071 | `(926.50, 425.50)` |
| `ultralytics` (chuẩn) | `[880.67, 368.51, 972.34, 482.97]` conf 0.8084 | `(926.51, 425.74)` |
| **Sai lệch từng cạnh** | **0.33 · 0.51 · 0.34 · 0.03 px** | 0.01 · 0.24 px |

Sai lệch dưới 0,6 px trên ảnh **không vuông** — chỉ letterbox mới cho được con số này.
Năm điểm mốc trên ảnh LFW gốc khớp `ultralytics` **0.00 px** ở cả 5 điểm.

### 1.2. Nhưng ca test dòng 27 chỉ đóng được **một nửa** bẫy

ĐB1 theo đúng chữ trong §7 (thay thân `letterbox` bằng `cv2.resize` kéo giãn, giữ nguyên `r`)
**làm đỏ dòng 27** như đặc tả đòi. Tuy nhiên tôi chạy thêm **ĐB1b — kéo giãn "đúng cách"**:
`cv2.resize` thẳng ra 320×320 kèm **hai hệ số tỉ lệ riêng** `rx = S/W`, `ry = S/H` và đưa toạ độ
về ảnh gốc theo từng trục (đây mới là cách một người cài đặt thật sự viết sai sẽ viết):

```
ĐB1b áp vào src/detector/yolo_face.py  ->  42 passed, 1 deselected   ❌ KHÔNG ca nào đỏ
```

Số đo giải thích vì sao, đo trên chính ảnh 1280×720 của ca dòng 27:

| Đại lượng | Letterbox (đúng) | Kéo giãn hai hệ số | Chênh |
|---|---|---|---|
| Cạnh khung | `[881, 368, 972, 483]` | `[873.92, 372.22, 979.43, 481.52]` | **7.1 · 3.7 · 7.4 · 1.5 px** |
| **Tâm khung** | `(926.50, 425.50)` | `(926.67, 426.87)` | **0.17 · 1.37 px** |
| Lệch so với tâm kỳ vọng của ca test | 0.32 · 0.29 px | 0.49 · **1.67 px** | dung sai cho phép **15 px** |

Kéo giãn làm **méo kích thước** khung (cạnh lệch tới 7,4 px) nhưng gần như **không dịch tâm**
(1,67 px). Ca dòng 27 chỉ assert **tâm** với dung sai **15 px**, tức rộng gấp ~9 lần mức chênh
thực tế → không phân biệt được hai cách. Dòng 23 (assert từng cạnh, dung sai 1 px) thì lại chạy
trên ảnh LFW **vuông** 250×250, nơi hai cách cho kết quả y hệt.

**Trách nhiệm**: cột bảng §6 ghi "Assert **tối thiểu**", và dòng 27 của đặc tả viết đúng chữ
"assert tâm khung … sai lệch < 15 px". Người cài đặt làm **đúng đặc tả**; chỗ lỏng nằm ở đặc tả.
→ ghi thành **GY-1** cho `spec-writer`, kèm bộ số tham chiếu đã đo sẵn để siết lại. Không chặn.

---

## 2. Kết quả kiểm máy

### 2.1. Trên host (Windows, Python 3.12.5)

| Lệnh | Kết quả |
|---|---|
| `black --line-length 100 --check src/detector tests/test_yolo_face.py` | **3 files unchanged**, exit 0 ✅ |
| `ruff check src/detector tests/test_yolo_face.py` | **All checks passed**, exit 0 ✅ |
| `python -m pytest tests/test_yolo_face.py -v` | **43 passed** (12,26 s) ✅ |
| `git status --short --untracked-files=all` | đúng **3 tệp mới** của mã việc ✅ |
| `black --check src tests` (toàn repo) | 23 files unchanged ✅ |
| `ruff check src tests` (toàn repo) | All checks passed ✅ |
| `pytest -q` (toàn repo) | **243 passed** (93 s) ✅ — trước mã việc là 200 |

### 2.2. Trên container ARM64 (`faceid-arm64-test:p2-02`, `uname -m` = `aarch64`)

Lần này Docker daemon chạy được (khác hai vòng của `P2-01`), nên đã chạy **thật** chứ không mô phỏng.

| Lệnh | Kết quả |
|---|---|
| `black … --check` | 3 files unchanged ✅ |
| `ruff check` | 3 × `EXE002 file is executable but no shebang` ⚠️ — **nhiễu môi trường**, xem GY-5 |
| `pytest tests/test_yolo_face.py -q` | **42 passed, 1 failed** (236 s) — ca `slow` thiếu `ultralytics`, xem GY-2 |
| `pytest tests/test_yolo_face.py -m "not slow" -q` | **42 passed** ✅ |

### 2.3. Môi trường thiếu gói (chặn `ultralytics`, `torch`, `torchvision`, `onnx` qua `sys.meta_path`)

| Lệnh | Kết quả |
|---|---|
| `pytest tests/test_yolo_face.py -m "not slow" --collect-only` | `42/43 collected (1 deselected)`, exit **0** ✅ |
| `pytest --collect-only` (**toàn repo**) | `243 tests collected`, exit **0** ✅ |
| `pytest tests/test_yolo_face.py -m "not slow"` | `42 passed, 1 deselected` ✅ |

Bài học `P2-01` (import gói nặng ở mức module giết cả bộ test) **không tái diễn**.

### 2.4. Bốn lệnh `grep` §7 — giải trình từng dòng không rỗng

| Lệnh | Kết quả | Kết luận |
|---|---|---|
| `ultralytics\|import torch` | 1 dòng: `yolo_face.py:4` | **Chú thích trong docstring** ("không được kéo theo…"), không phải import ✅ |
| `print(` | rỗng | ✅ |
| `\b(114\|320\|640\|0\.5\|0\.45\|20\|2100\|8400)\b` | `:7` docstring · `:26 MAU_NEN_LETTERBOX = 114` · `:28` chú thích · `:29 SO_KENH_DAU_RA = 20` | Đúng ngoại lệ §7 cho phép: hằng số **có tên**, kèm chú thích dẫn `§3.2`/`§3.3`. **Không** còn `320/640/0.5/0.45/2100/8400` nào ✅ |
| `raise (ValueError\|TypeError)` | `:226 :230 :234 :236` | Cả 4 nằm trong 4 guard đầu `detect` (đầu vào sai — dòng 34–38 cho phép). Không dòng nào là lỗi **cấu hình** ✅ |

Quét thêm theo `code-review.instructions.md` §2: `except:` trần — không có · `logger.<x>(f"…")` —
không có · đường dẫn tuyệt đối máy cá nhân — không có · `assert True` / `pass` trong test — không có ·
`InferenceSession` — nằm trong `__init__` (`:177`), **không** trong vòng lặp frame ✅ ·
`git status | grep -Ei '\.(jpg|png|npy|onnx|pt|env|db)$'` — **rỗng** ✅.

---

## 3. Phạm vi file

```
?? src/detector/__init__.py        ← danh sách trắng §2
?? src/detector/yolo_face.py       ← danh sách trắng §2
?? tests/test_yolo_face.py         ← danh sách trắng §2
?? docs/bao-cao-tuan/*.docx (3)    ← tài liệu của sinh viên, KHÔNG thuộc mã việc — bỏ qua
```

`git diff --stat` rỗng (chưa commit, đúng §10). Không đụng `configs/`, `src/common/`,
`src/preprocess/`, `scripts/`, `requirements.txt`, `pyproject.toml`, `docs/`, `.claude/` ✅.

---

## 4. Năm phép đột biến §7 — tự chạy lại

`sha256` gốc `src/detector/yolo_face.py` = `43a47a7b3147209496ccc6f6425cb5ea1f595e04113aecea9e96438fb4ee1ee7`
(tệp dùng LF; harness đọc/ghi bằng `open(..., newline="")`).

| # | Phép đột biến | Đặc tả đòi đỏ | Thực tế đỏ | Khôi phục |
|---|---|---|---|---|
| ĐB1 | `letterbox` → `cv2.resize` kéo giãn thẳng | 27 | **12, 13, 15, 17, 27** ✅ | sha khớp ✅ |
| ĐB2 | Bỏ đưa toạ độ về ảnh gốc (`r,dx,dy = 1,0,0`) | 23, 25, 27 | **23, 25, 27**, 33, 42 ✅ | sha khớp ✅ |
| ĐB3 | `nms` luôn giữ mọi khung | 18, 21 | **18, 21** ✅ | sha khớp ✅ |
| ĐB4 | Bỏ cắt `max_faces` | 31 | **31** (`assert 5 <= 2`) ✅ | sha khớp ✅ |
| ĐB5 | Bỏ `cvtColor` BGR→RGB | 23 **hoặc** 24 | **23**, 42 ✅ | sha khớp ✅ |
| ĐB1b | Kéo giãn **hai hệ số riêng** (thêm, ngoài §7) | — | **không ca nào đỏ** ❌ | sha khớp ✅ |

Năm phép bắt buộc đều nhắm đúng chỗ, không đỏ lan man. ĐB1b là lỗ hổng đã phân tích ở §1.2.
`git status` sau toàn bộ phép đột biến: nguyên trạng, không sót thay đổi nào trong mã sản phẩm.

---

## 5. Đối chiếu bảng §6 — 42/42 ca, ánh xạ 1–1

Quét `ast` tệp test: **43 hàm** `test_*`, trong đó **42 hàm** `test_dong<nn>` với `nn` = 01…42,
**không thiếu, không trùng**; 1 hàm ngoài bảng là ca `@pytest.mark.slow` đối chiếu `ultralytics`.

**Số đo thực tế** (tự chạy, không lấy từ báo cáo của người cài đặt), `imgsz=320`, ảnh LFW mẫu,
nạp bằng **`configs/detect.yaml` thật**:

| Dòng | Đối chứng §3.5 | Đo được | Sai lệch |
|---|---|---|---|
| 23 | `[82.81, 66.45, 169.56, 183.96]` | `[83, 66, 170, 184]` | `0.19 · 0.45 · 0.44 · 0.04` px |
| 24 | `0.8564` | `0.8564` | `0.0000` |
| 25 | `[105.36, 115.41]` | `[105.36, 115.41]` | `0.000 · 0.005` px |
| 26 | `(5, 2)` | `(5, 2)`, `float64` | — |
| 27 | tâm `(926.19, 425.21)` | `(926.50, 425.50)` | `0.32 · 0.29` px |
| 33 | tâm 640 lệch < 10 px | lệch `0.5 · 2.0` px | ✅ |
| 39 | ảnh 1×1 không ném lỗi | trả `[]` | ✅ |

| Mục đặc tả | Kết luận |
|---|---|
| §3.1–3.2 hình dạng & bố cục 20 kênh | ✅ đọc `kich_thuoc_vao` từ đồ thị (`:194`), kiểm 20 kênh (`:187`) |
| §3.3 letterbox | ✅ đúng công thức, khớp `ultralytics` < 0,6 px trên ảnh 16:9 |
| §3.4 đưa toạ độ về ảnh gốc | ✅ áp cho **cả** khung (`:267–270`) lẫn điểm mốc (`:275–276`) |
| §4 tham số → config | ✅ 4/4 khoá đọc qua `lay_gia_tri`, đường dẫn `.onnx` truyền lúc khởi tạo, **không hardcode** |
| §5 giao diện | ✅ khớp từng ký tự: tên lớp, `kich_thuoc_vao` là `@property`, `letterbox`/`nms` tách riêng, dùng lại `FaceBox`/`LoiCauHinh`/`LoiMoHinh` |
| §6 bảng nghiệm thu | ✅ 42/42 ca, chạy thật 43 passed |
| §8 ràng buộc kỹ thuật | ⚠️ đạt, trừ điểm ARM64 ở GY-2 |
| §9 ngoài phạm vi | ✅ không đo FPS, không NCNN, không xử lý mẻ, không bám vết |

---

## 6. Kiểm sâu ngoài bảng nghiệm thu

### 6.1. Ràng buộc triển khai — quét `ast` độc lập ✅

Duyệt `ast.walk` toàn bộ `src/detector/*.py`, bắt cả `Import`/`ImportFrom` **trong thân hàm** lẫn
`importlib.import_module` / `__import__` / `load_module`:

```
src/detector/__init__.py  -> ['yolo_face']
src/detector/yolo_face.py -> ['pathlib','cv2','numpy','onnxruntime',
                              'src.common.config','src.common.exceptions',
                              'src.common.logging','src.common.types']
VI PHAM: KHONG CO
```

Chiều ngược lại ở tệp test: import mức module chỉ có `ast, pathlib, cv2, numpy, pytest,
src.common.exceptions, src.detector.yolo_face`. `ultralytics` nằm **trong thân**
`test_doi_chieu_ultralytics_tren_anh_lfw_mau` (dòng 463), hàm có `@pytest.mark.slow` ✅.

### 6.2. `nms` — đối chiếu với tính tay ✅

| Cấu hình | IoU tính tay | `nms` trả về | Đúng? |
|---|---|---|---|
| Ba khung **chồng dây chuyền** A(0,0,10,10) .9 · B(6,0,16,10) .8 · C(12,0,22,10) .7 | AB = 0,250 · BC = 0,250 · AC = 0 | ngưỡng 0,20 → `[0, 2]`; ngưỡng 0,30 → `[0, 1, 2]` | ✅ đúng NMS tham lam: A loại B, C sống vì không chồng khung **còn lại** |
| Khung lồng nhau A(0,0,100,100) ⊃ B(10,10,50,50) | 0,1600 | ngưỡng 0,45 → `[0, 1]` | ✅ |
| Khung diện tích 0 | — | `[0, 1]`, không chia 0 | ✅ |
| Hai khung conf **bằng nhau**, tách rời | — | `[0, 1]` ổn định | ✅ |
| Mảng rỗng | — | `[]` | ✅ |

Biên `iou <= nguong` (giữ) khớp đúng ý dòng 21: IoU 0,1428 bị loại ở ngưỡng 0,10 và được giữ ở 0,20.

### 6.3. Thứ tự 5 điểm mốc ✅ — đây là chỗ sai lặng lẽ nhất, đã soi riêng

| Điểm | Cài đặt | `ultralytics` | Lệch |
|---|---|---|---|
| 0 mắt trái | `(105.36, 115.41)` | `(105.36, 115.41)` | 0.00 |
| 1 mắt phải | `(146.52, 114.58)` | `(146.52, 114.58)` | 0.00 |
| 2 mũi | `(127.28, 140.83)` | `(127.28, 140.83)` | 0.00 |
| 3 miệng trái | `(109.33, 152.55)` | `(109.33, 152.55)` | 0.00 |
| 4 miệng phải | `(144.74, 151.88)` | `(144.74, 151.88)` | 0.00 |

Trùng khớp `thu_tu_diem_moc: [mat_trai, mat_phai, mui, mieng_trai, mieng_phai]` của
`configs/detect.yaml`, tức **đưa thẳng sang `align.can_chinh()` không cần hoán vị** như §1 đặc tả
cam kết. Bốn bất biến hình học của dòng 29 đúng **12/12** ảnh LFW ngẫu nhiên (seed 42) tôi tự chọn.

### 6.4. Bộ cấu hình hỏng tự dựng — **78 ca**, phủ 4 khoá × 17 biến thể + 6 ca cấu trúc

Đây là phép tìm ra lỗ hổng duy nhất của vòng này.

| Nhóm ca | Kết quả |
|---|---|
| `None`, `[]`, `{}`, `True`, `False`, `"abc"`, `"0.5"`, `nan`, `inf`, `-1`, `1.5`, `10.0`, `-0.1`, `2.0` cho cả 4 khoá | **LoiCauHinh** đủ, thông điệp nêu đúng tên khoá ✅ |
| Thiếu `conf_threshold` / `iou_threshold` / `max_faces` | **LoiCauHinh** ✅ (thiếu `num_threads` → mặc định 0, đúng §4) |
| `cfg = {}` · `None` · `[]` · `inference = None/'abc'/[]` | **LoiCauHinh** ✅ |
| Loại trừ `bool` tường minh (`True` không lọt qua `isinstance(int)`) | ✅ xử lý đúng |
| **`num_threads = 10**9`** | ❌ `LoiMoHinh("Không nạp được mô hình ONNX … bad alloc")` — đổ tội cho tệp model |
| **`num_threads = 2**40`** | ❌ **`TypeError` thô lọt ra ngoài** → **CẦN SỬA-1** |

---

## 7. Lỗi phải sửa

### 🟡 CẦN SỬA-1 — `num_threads` quá lớn làm lọt `TypeError` thô, vi phạm tiêu chí dòng 10 (CB-1)

**Vị trí**: `src/detector/yolo_face.py:164–166` và `:172–174`

```python
        self._num_threads = int(
            _lay_so_trong_khoang(cfg, "inference.num_threads", int, 0, float("inf"), mac_dinh=0)
        )
        ...
        tuy_chon = ort.SessionOptions()
        if self._num_threads > 0:
            tuy_chon.intra_op_num_threads = self._num_threads   # ← nằm NGOÀI khối try
```

Tái hiện (đã chạy, `models/yolov8n-face-320.onnx` có thật):

```
num_threads = 1099511627776  ->  TypeError: (): incompatible function arguments…
num_threads = 1000000000     ->  LoiMoHinh: Không nạp được mô hình ONNX từ
                                 models\yolov8n-face-320.onnx: bad alloc
```

**Vì sao**: dòng 10 bảng §6 đòi *"Mọi lỗi cấu hình là `LoiCauHinh`, không phải
`ValueError`/`TypeError`"*. Ở đây một giá trị trong `configs/detect.yaml` làm ngoại lệ của
pybind11 lọt thẳng ra ngoài — người gọi ở `src/main.py` bắt `LoiCauHinh`/`LoiMoHinh` sẽ **không
bắt được**, cả pipeline sập ngay lúc khởi động thay vì báo một dòng cấu hình sai. Ca `10**9` còn
tệ hơn về chẩn đoán: thông điệp nói "không nạp được mô hình ONNX", đẩy người gỡ lỗi đi tìm tệp
model hỏng trong khi lỗi thật nằm ở một số thừa mấy con số 0. Miền `[0, +∞)` hiện tại là **vô
biên**, trong khi Pi 5 chỉ có 4 lõi và ma trận benchmark bước 2.6 chỉ quét `{1, 2, 4}`.

**Sửa** — hai thao tác nhỏ, giữ nguyên kiến trúc hiện có:

1. Thêm hằng số có tên ở đầu module, kèm chú thích như các hằng số đang có:

```python
# Trần số luồng cho onnxruntime — Pi 5 có 4 lõi; giá trị lớn hơn chắc chắn là lỗi cấu hình,
# và làm onnxruntime ném ngoại lệ thô (bad_alloc / TypeError) thay vì LoiCauHinh.
SO_LUONG_TOI_DA = 64
```

2. Đổi cận trên khi đọc khoá (`:165`):

```python
_lay_so_trong_khoang(cfg, "inference.num_threads", int, 0, SO_LUONG_TOI_DA, mac_dinh=0)
```

3. Bổ sung 2 biến thể vào `tests/test_yolo_face.py::test_dong10...` để ca này chặn được hồi quy:

```python
        ("num_threads", 10**9),
        ("num_threads", 2**40),
```

Nếu muốn chặt hơn nữa: chuyển hai dòng `:173–174` vào trong khối `try` của `:176–181` để mọi
ngoại lệ của `SessionOptions` cũng thành `LoiMoHinh` thay vì lọt thô.

---

## 8. 🔵 Góp ý — không chặn, người dùng quyết định

- **GY-1 → `spec-writer` (quan trọng nhất).** Dòng 27 §6 chỉ assert **tâm** khung với dung sai
  **15 px**, trong khi kéo giãn "đúng cách" chỉ dịch tâm **1,67 px** mà làm méo **cạnh tới 7,4 px**
  (số đo §1.2) → tiêu chí hiện tại không phân biệt được hai cách; ĐB1b xanh toàn bộ. Đề nghị siết
  dòng 27 thành assert **từng cạnh** trên ảnh không vuông, dùng bộ số tôi vừa đo bằng `ultralytics`
  trên đúng ảnh dựng của ca test (LFW `Aaron_Peirsol_0001` dán tại `(800, 300)` trên nền xám 200,
  ảnh 1280×720, `imgsz=320`):

  ```
  khung chuẩn = [880.67, 368.51, 972.34, 482.97]   # sai lệch mỗi cạnh < 2 px
  ```

  Chi phí: sửa 4 dòng đặc tả + 4 dòng test. Lợi ích: bịt hẳn bẫy kéo giãn thay vì bịt một nửa.
  Vì mã việc dù sao cũng quay lại vòng 2 cho CẦN SỬA-1, có thể gộp luôn nếu người dùng đồng ý.

- **GY-2 → `spec-writer`.** Trên container ARM64, lệnh §7 `pytest tests/test_yolo_face.py -v`
  (không lọc mark) cho **1 failed** vì `import ultralytics` trong thân ca `slow` ném
  `ModuleNotFoundError`. `-m "not slow"` thì 42 passed. `tests/test_export_detector.py` của
  `P2-01` cũng vậy — đây là hệ quả của quy ước chung, người cài đặt làm đúng §8. Cách bịt gọn:
  đổi `import ultralytics` thành `pytest.importorskip("ultralytics")`, khi đó ca tự **SKIP** và
  lệnh §7 xanh ở mọi môi trường. Nên sửa quy ước ở cả hai tệp trong một mã việc `chore`.

- **GY-3 → `spec-writer`.** Mark `slow` vẫn **chưa đăng ký** trong `pyproject.toml` →
  `PytestUnknownMarkWarning`. Đúng như GY-2 của biên bản `P2-01`, `pyproject.toml` **ngoài danh
  sách trắng §2** nên người cài đặt đã đúng khi không đụng. Gom vào commit `chore(quy-trinh)`.

- **GY-4 → mã việc sau.** `src/detector/yolo_face.py:194` — `int(dau_vao.shape[2])` sẽ ném
  `ValueError` **thô** nếu đồ thị ONNX có trục đầu vào động (chiều là chuỗi `'height'`). Hai tệp
  hiện tại đều tĩnh (`batch: 1`, §3.1) nên chưa gặp; nếu sau này export lại với `dynamic=True`
  thì lỗi sẽ không mang dạng `LoiMoHinh`. Chi phí sửa ~3 dòng.

- **GY-5 → ghi chú môi trường, không ai phải sửa.** `ruff` trong container báo `EXE002` cho cả ba
  tệp mới; kiểm chứng cho thấy nó cũng báo y hệt cho `src/preprocess/align.py` và
  `tests/test_export_detector.py` **đã gộp vào `dev` từ trước** — nguyên nhân là bind-mount
  Windows đưa toàn bộ tệp vào container ở mode 777. Không phải lỗi mã việc. Ghi lại để vòng sau
  khỏi mất công truy lại.

- **GY-6 → nhỏ.** `_lay_so_trong_khoang` (`:119–121`) chú kiểu `kieu: type` nhưng thực tế nhận cả
  tuple `(int, float)`, và khai báo trả `float` trong khi có nhánh trả `int`. Không ảnh hưởng chạy
  (`ruff` sạch, repo chưa dùng `mypy`); chỉnh chú kiểu thành `type | tuple[type, ...]` cho khớp.

---

## 9. Hai điểm sống còn đã soi riêng

- **Trung thực số liệu**: mã việc **không** ghi gì vào `results/`. Ba hằng số đối chứng trong tệp
  test (`_KHUNG_DOI_CHUNG`, `_CONF_DOI_CHUNG`, `_DIEM0_DOI_CHUNG`) chép từ §3.5 đặc tả và đã được
  tôi **đo lại độc lập bằng `ultralytics`**, khớp trong 0,51 px / 0,0000 conf / 0,005 px. Không có
  giá trị mặc định giả, không có số ví dụ trong docstring có thể bị chép nhầm vào báo cáo.
- **An toàn phần cứng**: khối này không chạm GPIO/relay/camera — không có bề mặt rủi ro. Phiên
  `onnxruntime` nạp **một lần** trong `__init__` (`:177`), `detect` không cấp phát lại phiên trong
  vòng lặp frame; `detect` không nuốt lỗi, mọi nhánh sai đầu vào đều dừng sớm và nói rõ nguyên nhân.

---

## 10. Việc tiếp theo

🔴 **TRẢ LẠI cho người cài đặt — vòng 2.** Chỉ một hạng mục bắt buộc:

1. **CẦN SỬA-1** — chặn trần `num_threads` (`SO_LUONG_TOI_DA = 64`), sửa `:165`, thêm 2 biến thể
   vào ca `test_dong10`. Danh sách trắng không đổi: chỉ `src/detector/yolo_face.py` và
   `tests/test_yolo_face.py`.
2. *(tuỳ người dùng duyệt)* **GY-1** — siết dòng 27 sang assert từng cạnh với bộ số ở §8. Nếu
   duyệt thì `spec-writer` sửa đặc tả **trước**, rồi người cài đặt sửa test theo bản mới.

Chạy lại đủ: 4 lệnh §7 trên host **và** container ARM64 (lệnh pytest kèm `-m "not slow"` cho
ARM64), 5 phép đột biến §7 kèm `sha256`. **Không commit.**

Sau khi vòng 2 ĐẠT, đề xuất commit message (R29):

```
feat(detector): khối phát hiện khuôn mặt YOLOv8n-face chạy ONNX Runtime
```

Thân commit ghi: mã việc `P2-02-detector`, biên bản `docs/review/P2-02-detector.review.md`,
43 ca test, đối chiếu `ultralytics` sai lệch < 0,6 px trên ảnh 1280×720.

---
---

# Review P2-02-detector — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-02-detector.md` (bản cập nhật sau vòng 1 — dòng 27 assert từng cạnh, thêm §6.6 và ĐB1b) |
| **Nhánh** | `feat/p2-02-detector` (chưa commit) |
| **HEAD khi review** | `0d2a303` |
| **Ngày** | 2026-08-19 |
| **sha256 mã sản phẩm** | `yolo_face.py` = `67ccf6fe…4558338` · `test_yolo_face.py` = `bf5d26ce…07a30020` |
| **Phán quyết** | ✅ **ĐẠT** — hết 🔴 và 🟡; còn 5 mục 🔵 không chặn (4/5 thuộc `spec-writer`) |

---

## 1. ĐB1b — phép quyết định: **ĐỎ đúng dòng 27, và chỉ dòng 27**

Chạy lại **đúng** phép đã cho 42 test xanh ở vòng 1: `cv2.resize` thẳng ra 320×320 với **hai hệ
số tỉ lệ riêng** `rx = S/W`, `ry = S/H`, ánh xạ ngược **khớp theo từng trục** cho cả khung bao lẫn
điểm mốc — một cài đặt sai nhưng **tự nhất quán**, không lộ ra ở bất kỳ ca test nội bộ nào của
`letterbox`.

| Vòng | Kết quả ĐB1b |
|---|---|
| Vòng 1 | `42 passed, 1 deselected` — ❌ **không ca nào đỏ** |
| **Vòng 2** | `1 failed, 41 passed` — ✅ **`test_dong27_anh_khong_vuong_cho_ket_qua_dung`** |

Đỏ **đúng một ca**, không lan man — ca test định vị được lỗi chứ không chỉ báo động.

### 1.1. Dung sai 2,0 px có nằm giữa hai nhóm không — đo thực tế bốn cạnh

Tự dựng lại ảnh theo §6.6 (nền 128, dán `Aaron_Peirsol_0001.jpg` vào `anh[300:550, 800:1050]`),
`imgsz=320`, đối chứng `[880.68, 368.38, 972.30, 483.01]`:

| Nguồn | Bốn cạnh đo được | Lệch từng cạnh | Kết luận với ngưỡng 2,0 px |
|---|---|---|---|
| **Cài đặt hiện tại** | `[881, 368, 972, 483]` | `0.32 · 0.38 · 0.30 · 0.01` | ✅ xanh, cạnh xấu nhất **0,38 px** — còn **1,62 px biên an toàn** |
| `ultralytics` (tôi chạy lại độc lập) | `[880.80, 368.74, 972.29, 482.95]` | `0.12 · 0.36 · 0.01 · 0.06` | số đối chứng của đặc tả **là số thật**, tái lập được |
| **ĐB1b kéo giãn 2 hệ số** | `[874.12, 371.28, 979.30, 481.56]` | `6.56 · 2.90 · 7.00 · 1.45` | ❌ đỏ, **3/4 cạnh vượt ngưỡng**, cạnh xấu nhất 7,00 px |

Ngưỡng **2,0 px** nằm gọn giữa hai nhóm: cách nhóm đúng **5,3 lần** (0,38 → 2,0) và cách cạnh
vi phạm gần nhất của nhóm sai **1,45 lần** (2,0 → 2,90). Ca test **không mong manh**: sai số của
bản đúng chủ yếu là lượng tử hoá khi ép `int` (± 0,5 px), vẫn còn cách ngưỡng khoảng ba lần mức đó.

Đối chiếu ngược lại vì sao tiêu chí cũ vô dụng: cùng phép ĐB1b đó chỉ dịch **tâm** khung
**0,22 / 0,72 px** — dưới xa mọi dung sai dùng được. Số này khớp với con số điều phối viên tự đo.

### 1.2. Ca test dựng ảnh **đúng** §6.6 — kiểm từng chi tiết

`tests/test_yolo_face.py:286–288`:

```python
    canvas = np.full((720, 1280, 3), 128, dtype=np.uint8)
    canvas[300:550, 800:1050] = anh_lfw
```

Đúng ảnh (`anh_lfw` là fixture đọc `Aaron_Peirsol_0001.jpg`), đúng nền **128**, đúng vị trí dán
`[300:550, 800:1050]`, đúng kích thước 1280×720. Assert **cả bốn cạnh** với hằng số
`_KHUNG_KHONG_VUONG_DOI_CHUNG = [880.68, 368.38, 972.30, 483.01]` (`:33`), dung sai `< 2.0`.
**Không còn** assert tâm khung — đúng lệnh cấm của dòng 27 bản mới.

---

## 2. CẦN SỬA-1 (vòng 1) — ĐÃ SỬA, xác nhận bằng đo lại

`src/detector/yolo_face.py:39–41` thêm hằng số có tên kèm chú thích; `:169` dùng nó làm cận trên.

```python
# Trần số luồng cho onnxruntime — Pi 5 có 4 lõi; giá trị lớn hơn chắc chắn là lỗi cấu hình,
# và làm onnxruntime ném ngoại lệ thô (bad_alloc / TypeError) thay vì LoiCauHinh.
SO_LUONG_TOI_DA = 64
```

| `num_threads` | Vòng 1 | **Vòng 2** |
|---|---|---|
| `2**40` | ❌ `TypeError` thô lọt ra ngoài | ✅ `LoiCauHinh: … phải trong khoảng [0, 64], nhận 1099511627776` |
| `10**9` | ❌ `LoiMoHinh: … bad alloc` (đổ tội cho tệp model) | ✅ `LoiCauHinh: … phải trong khoảng [0, 64]` |
| `2**63`, `2**63 - 1` | (chưa thử) | ✅ `LoiCauHinh` |
| `65`, `100` | — | ✅ `LoiCauHinh` |
| `63`, `64` | — | ✅ nạp được — biên trên **đúng, bao gồm 64** |
| `0`, `1`, `2`, `4` | ✅ | ✅ nạp được |
| `-1`, `True`, `False`, `1.5`, `"2"`, `None` | ✅ `LoiCauHinh` | ✅ `LoiCauHinh` (giữ nguyên) |

Thông điệp lỗi nay nêu **đúng tên khoá và đúng miền**, không còn dẫn người gỡ lỗi đi tìm tệp model.

`tests/test_yolo_face.py:138–155` — ca `test_dong10` **thật sự** có hai biến thể mới:

```python
        ("num_threads", 10**9),
        ("num_threads", 2**40),
```

Bộ hỏng nay 10 biến thể, phủ 4 khoá × ≥ 2 biến thể như dòng 10 đòi.

**Hồi quy ba khoá còn lại** (tập nhỏ 14 ca + 3 ca thiếu key): `conf_threshold` / `iou_threshold` /
`max_faces` với `-0.1`, `1.5`, `"0.5"`, `None`, `True`, `nan`, `-1`, `0`, `"10"` và ba ca thiếu key
— **tất cả vẫn `LoiCauHinh`** ✅. Không có hồi quy.

---

## 3. Hồi quy phần tính toán — **số đo không xê dịch một chút nào**

Vòng này chỉ thêm 4 dòng hằng số + đổi một tham số; `letterbox`, `nms`, `_tien_xu_ly` và toàn bộ
thân `detect` (`:242–294`) **y nguyên**. Đo lại để chắc:

| Dòng | Đối chứng §3.5 | Vòng 1 | **Vòng 2** |
|---|---|---|---|
| 23 khung | `[82.81, 66.45, 169.56, 183.96]` | lệch `0.19 · 0.45 · 0.44 · 0.04` | **giống hệt** ✅ |
| 24 conf | `0.8564` | lệch `0.0000` | **giống hệt** ✅ |
| 25 điểm mốc 0 | `[105.36, 115.41]` | lệch `0.000 · 0.005` | **giống hệt** ✅ |
| 26 hình dạng | `(5, 2)` | `(5, 2)` `float64` | **giống hệt** ✅ |

---

## 4. Sáu phép đột biến — sha256 `67ccf6fedc4cad4f3944a566e9a310e2fc7447018b5a73d75d5faae534558338`

| # | Đặc tả đòi đỏ | Thực tế đỏ | Khôi phục |
|---|---|---|---|
| ĐB1 kéo giãn thẳng | 27 | **12, 13, 15, 17, 27** ✅ | sha khớp ✅ |
| **ĐB1b kéo giãn 2 hệ số** | **27** | **27** (duy nhất) ✅ | sha khớp ✅ |
| ĐB2 bỏ đưa về ảnh gốc | 23, 25, 27 | **23, 25, 27**, 33, 42 ✅ | sha khớp ✅ |
| ĐB3 `nms` giữ mọi khung | 18, 21 | **18, 21** ✅ | sha khớp ✅ |
| ĐB4 bỏ `max_faces` | 31 | **31** ✅ | sha khớp ✅ |
| ĐB5 đảo RGB/BGR | 23 hoặc 24 | **23**, 42 ✅ | sha khớp ✅ |

Sáu lần khôi phục đều khớp `sha256`; `git status` sau cùng nguyên trạng, không sót thay đổi nào
trong mã sản phẩm.

---

## 5. Kiểm máy

| Lệnh | Host (Win, Py 3.12.5) | Container ARM64 (`aarch64`) |
|---|---|---|
| `black --line-length 100 --check src/detector tests/test_yolo_face.py` | 3 files unchanged ✅ | 3 files unchanged ✅ |
| `ruff check src/detector tests/test_yolo_face.py` | All checks passed ✅ | All checks passed ✅ (bỏ `EXE002` — nhiễu bind-mount, đã chứng minh ở vòng 1 GY-5) |
| `pytest tests/test_yolo_face.py` | **43 passed** ✅ | **42 passed, 1 deselected** với `-m "not slow"` ✅ |
| `pytest --collect-only` toàn repo | 243 ✅ | **243 collected**, exit 0 ✅ |
| `black`/`ruff`/`pytest` toàn repo | 23 files unchanged · sạch · **243 passed** ✅ | — |

Môi trường **thiếu gói** (chặn `ultralytics`, `torch`, `torchvision`, `onnx` qua `sys.meta_path`):
`-m "not slow" --collect-only` cho `42/43 collected (1 deselected)` exit 0 · chạy thật cho
`42 passed` · `--collect-only` toàn repo cho `243 collected` exit 0 ✅.

**Bốn lệnh `grep`** — kết quả y hệt vòng 1, giải trình không đổi: `ultralytics` chỉ xuất hiện ở
docstring `:4`; `print(` rỗng; số hardcode chỉ còn hằng số có tên `MAU_NEN_LETTERBOX = 114`,
`SO_KENH_DAU_RA = 20` kèm chú thích dẫn §3 (hằng số mới `SO_LUONG_TOI_DA = 64` cũng có tên và chú
thích); bốn `raise ValueError` (`:230, :234, :238, :240`) đều là guard đầu vào của `detect`
(dòng 34–38 cho phép), không dòng nào là lỗi cấu hình.

**Quét `ast`**: `src/detector/` chỉ import `pathlib, cv2, numpy, onnxruntime, src.common.*` —
không `ultralytics`/`torch`/`importlib`/`__import__` ✅. Tệp test: mức module chỉ có
`ast, pathlib, cv2, numpy, pytest, src.common.exceptions, src.detector.yolo_face`; `ultralytics`
nằm trong thân hàm `:461` có `@pytest.mark.slow` ✅. **43 hàm test, 42 ca `test_dong01…42`, không
thiếu, không trùng** ✅.

**Phạm vi**: đúng ba tệp `src/detector/__init__.py`, `src/detector/yolo_face.py`,
`tests/test_yolo_face.py` (+ biên bản này). Không đụng `configs/`, `pyproject.toml`, `src/common/`,
`scripts/`, `.claude/`. Lọc đuôi tệp cấm (`.jpg/.onnx/.npy/.env/.db…`) — **rỗng** ✅.
Ba tệp `.docx` trong `docs/bao-cao-tuan/` là tài liệu của sinh viên, không thuộc mã việc.

---

## 6. 🔵 Góp ý còn để ngỏ — không chặn commit

Không mục nào yêu cầu người cài đặt làm thêm; bốn trên năm thuộc `spec-writer` hoặc mã việc sau.

- **GY-2 → `spec-writer`.** Trên ARM64, lệnh §7 `pytest tests/test_yolo_face.py -v` (không lọc mark)
  vẫn cho 1 failed vì `import ultralytics` trong thân ca `slow`. Đổi sang
  `pytest.importorskip("ultralytics")` thì ca tự SKIP và lệnh §7 xanh mọi nơi. Áp cho cả
  `tests/test_export_detector.py` của `P2-01` trong một mã việc `chore`.
- **GY-3 → `spec-writer`.** Mark `slow` vẫn chưa đăng ký trong `pyproject.toml` (ngoài danh sách
  trắng §2 — người cài đặt đúng khi không đụng). Gom vào commit `chore(quy-trinh)`.
- **GY-4 → mã việc sau.** `yolo_face.py:198` — `int(dau_vao.shape[2])` ném `ValueError` thô nếu
  đồ thị ONNX có trục vào động. Hai tệp hiện tại đều tĩnh nên chưa gặp.
- **GY-6 → nhỏ.** `_lay_so_trong_khoang` (`:123–125`) chú kiểu `kieu: type` nhưng nhận cả tuple
  `(int, float)`, khai báo trả `float` trong khi có nhánh trả `int`.
- **GY-7 (mới) → `spec-writer`.** Đặc tả bản cập nhật có **hai mục cùng đánh số §6.6**: "Cách dựng
  ảnh không vuông cho dòng 27" và "Ràng buộc triển khai" (dòng 40–42). Không gây hiểu nhầm cho vòng
  này vì nội dung khác hẳn nhau, nhưng nên đổi mục dựng ảnh thành **§6.4b** để tham chiếu trong
  docstring ca test trỏ đúng một chỗ.

---

## 7. Tổng kết hai vòng

| | Vòng 1 | Vòng 2 |
|---|---|---|
| Phán quyết | 🔴 TRẢ LẠI | ✅ **ĐẠT** |
| 🔴 CHẶN | 0 | 0 |
| 🟡 CẦN SỬA | 1 (`num_threads` làm lọt `TypeError` thô) | **0** |
| 🔵 GÓP Ý | 6 | 5 (GY-1 đã được `spec-writer` xử lý, thêm GY-7) |
| Test tệp / toàn repo | 43 / 243 passed | 43 / 243 passed |
| **ĐB1b** | ❌ 42 xanh, không bắt được lỗi | ✅ **đỏ đúng dòng 27** |

Hai vòng **không** rơi vào triệu chứng "sửa chỗ này hỏng chỗ khác": hai việc được sửa đúng chỗ,
số đo dòng 23–25 không xê dịch một chữ số, không sinh lỗi mới. Đúng chẩn đoán của trần 2 vòng —
lỗ hổng vòng 1 là **lỗi đặc tả** (tiêu chí dòng 27 chọn sai đại lượng), không phải lỗi người cài
đặt; sửa đặc tả xong thì vòng 2 qua ngay.

### Bài học cho nhật ký tuần và Chương 3 — **chọn đại lượng assert theo độ nhạy với khuyết tật**

Tiêu chí nghiệm thu ban đầu của dòng 27 assert **tâm khung** với dung sai 15 px. Nó xanh với cả
cài đặt đúng lẫn cài đặt kéo giãn sai. Lý do có thể nêu bằng một câu: khuyết tật cần bắt là **sai
tỉ lệ khung hình**, tức một sai số **theo tỉ lệ**; ánh xạ ngược theo từng trục **khôi phục gần
đúng vị trí** nhưng **không khôi phục được kích thước**. Vậy nên sai số dồn vào **cạnh** (tới
7,0 px) trong khi **tâm** — đại lượng dễ đo và dễ nghĩ tới nhất — gần như không đổi (0,22–0,72 px).

Ba điều rút ra, áp cho mọi tiêu chí nghiệm thu về sau:

1. **Hỏi "đại lượng này có đổi khi cài đặt sai không?" trước khi hỏi "đại lượng này có dễ đo không?"**
   Trung bình, tâm, tổng — các đại lượng gộp — thường **triệt tiêu** đúng loại sai số cần bắt.
2. **Dung sai phải đặt giữa hai phân bố đã đo**, không đặt theo cảm tính: ở đây 0,38 px (đúng)
   → **2,0 px** → 2,90 px (sai). Dung sai không nằm giữa hai nhóm thì hoặc vô dụng, hoặc mong manh.
3. **Kiểm đột biến phải mô phỏng cài đặt sai *tự nhất quán***, không chỉ phá cho hỏng. ĐB1 (phá thô)
   đỏ ngay ở vòng 1 và tạo cảm giác an tâm giả; chỉ ĐB1b — bản sai nhưng hợp lý, đúng thứ một người
   viết code thật sự sẽ viết — mới lộ ra rằng ca test chưa đủ chặt.

Hai điểm sống còn đã soi riêng: **trung thực số liệu** — mã việc không ghi gì vào `results/`; các
hằng số đối chứng trong tệp test đều được tôi đo lại độc lập bằng `ultralytics` và khớp trong
0,36 px. **An toàn phần cứng** — khối này không chạm GPIO/relay/camera; phiên `onnxruntime` nạp một
lần trong `__init__` (`:181`), không nạp lại trong vòng lặp frame.

---

## 8. Việc tiếp theo

✅ **ĐẠT — được commit.** Đề xuất commit message (R29):

```
feat(detector): khối phát hiện khuôn mặt YOLOv8n-face chạy ONNX Runtime
```

Ghi trong **thân** commit (không nhồi vào tiêu đề): mã việc `P2-02-detector`; biên bản
`docs/review/P2-02-detector.review.md`; 43 ca test, 243 toàn repo, xanh trên host và container
ARM64; đối chiếu `ultralytics` sai lệch < 0,4 px trên ảnh 1280×720.

Sau khi gộp vào `dev`: bước **2.4** (chạy trên video mẫu trong Docker ARM64) và **2.6** (ma trận
benchmark ONNX × {320, 640} × {1, 2, 4} luồng) — thuộc Cổng C, cần Pi 5 thật.
Ba mục `chore` gom được từ hai mã việc: đăng ký mark `slow` (GY-3), đổi sang `importorskip` (GY-2),
sửa đánh số §6.6 trùng trong đặc tả (GY-7).
