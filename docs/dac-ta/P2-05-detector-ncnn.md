# P2-05-detector-ncnn — Backend NCNN cho khối phát hiện khuôn mặt

> Mã việc: `P2-05-detector-ncnn` · Bước **2.3** mở rộng, chuẩn bị cho ma trận đo **2.6**
> Nhánh: `feat/p2-05-detector-ncnn` · Đặc tả viết ngày 28/08/2026 · **sửa đổi vòng 2 ngày 30/08/2026**
> Tiền đề: `P2-04` đã đóng (merge `8ff1063`) — hai thư mục NCNN đã có trong `models/`

---

## 0b. Vòng 2 — GIAO LẠI, đọc mục này trước

Mã vòng 1 đã cài đặt xong và **giữ nguyên**. Lượt chạy trong container ARM64 ngày 30/08/2026 cho
435 ca xanh, nhưng lộ ra **một khiếm khuyết của đặc tả này** — không phải lỗi của bạn:

| # | Việc | Chỗ sửa |
|---|---|---|
| 1 | Ca dòng 22 đổi tiêu chí: bỏ ngưỡng IoU, dùng **dung sai 2 px trên từng cạnh và từng toạ độ điểm mốc** | `tests/test_ncnn_backend.py`, xem §6.4 |
| 2 | Thông báo assert của ca dòng 22 phải nêu tên ảnh, cạnh nào, độ lệch thật | cùng tệp |
| 3 | Bảo đảm ca dòng 22 dùng `pytest.importorskip("ncnn")` (dòng 22b) | cùng tệp |

Lý do: ngưỡng `IoU ≥ 0,99` mà vòng 1 đặt phụ thuộc kích thước khuôn mặt trong ảnh, nên nó đo sai thứ
cần đo. Chi tiết ở §6.4. **Không sửa gì trong `src/`** trừ khi §8 chỉ ra lỗi thật.

Bảy ca đỏ còn lại của lượt chạy đó (`test_export_detector.py`, `test_yolo_face.py`) **nằm ngoài phạm
vi mã việc này** — chúng thiếu `pytest.importorskip` từ `P2-01`/`P2-04`, và sẽ được xử lý bằng một mã
việc dọn dẹp riêng. Đừng động vào chúng.

---

## 1. Mục tiêu

Cho khối phát hiện khuôn mặt chạy được bằng **hai bộ suy luận**: ONNX Runtime (đã có) và **NCNN**
(mã việc này), sau **cùng một giao diện** `detect(khung_hinh) -> list[FaceBox]`.

Vì sao cần: bước 2.6 quy định ma trận `{ONNX, NCNN} × {320, 640} × {1, 2, 4 luồng}`. `P2-04` đã
chứng minh **tệp mô hình** NCNN đúng, nhưng hệ thống vẫn chưa **chạy** được nó —
`src/detector/yolo_face.py` gắn chặt với `onnxruntime`, và `scripts/benchmark_detect.py:477` vì thế
gán cứng `backend = "onnx"`. Thiếu mã việc này thì nửa NCNN của ma trận không tồn tại, và câu hỏi
"bộ suy luận nào phù hợp với Raspberry Pi 5" không có dữ liệu để trả lời.

Vì sao đáng làm dù chưa có Pi 5: toàn bộ phần cài đặt và kiểm tính đúng đắn không cần phần cứng
đích. Khi Pi 5 về, chỉ còn việc chạy `benchmark_detect.py` — không phải viết mã.

**Mã việc này không sinh ra con số hiệu năng nào.** So sánh tốc độ hai backend thuộc bước 2.6.

---

## 2. Phạm vi file — danh sách trắng

| File | Trạng thái | Vai trò |
|---|---|---|
| `src/detector/ncnn_backend.py` | tạo mới | Backend NCNN |
| `src/detector/factory.py` | tạo mới | Chọn backend theo đường dẫn mô hình |
| `src/detector/yolo_face.py` | **sửa có kiểm soát** | Trích phần hậu xử lý dùng chung ra hàm module-level; thêm thuộc tính `ten_backend` |
| `src/detector/__init__.py` | sửa | Xuất tên mới |
| `tests/test_ncnn_backend.py` | tạo mới | Bộ kiểm thử backend NCNN |
| `tests/test_detector_factory.py` | tạo mới | Bộ kiểm thử factory |
| `tests/test_yolo_face.py` | sửa | Ca cho hàm vừa trích ra và `ten_backend` |
| `requirements.txt` | sửa — **thêm đúng một dòng** | `ncnn==1.0.20260526` |

**Tuyệt đối không sửa**: `scripts/**` (kể cả `benchmark_detect.py` — xem §11), `configs/**`,
`src/preprocess/**`, `src/recognizer/**`, `models/**`, `docs/**`, `.claude/**`.

⚠️ `requirements.txt` đổi ⟹ **phải dựng lại image `faceid:arm64`** (R43). Lệnh dựng thuộc lượt của
người dùng ở §12b, không phải của bạn.

---

## 3. Dữ kiện — đọc kỹ cột cuối

| Dữ kiện | Giá trị | Mức |
|---|---|---|
| Blob đầu vào / đầu ra của đồ thị NCNN | `in0` / `out0` | **đã kiểm** — `model.ncnn.param` dòng 3 và dòng cuối |
| Quy mô đồ thị | 234 lớp, 279 blob | **đã kiểm** — `model.ncnn.param` dòng 2 |
| API nạp và chạy | `ncnn.Net()` · `load_param(...)` · `load_model(...)` · `create_extractor()` · `ex.input("in0", ncnn.Mat(...))` · `ex.extract("out0")` | **đã kiểm** — `model_ncnn.py` do PNNX sinh |
| Hình dạng tensor vào của NCNN | **CHW, KHÔNG có chiều batch** — `(3, imgsz, imgsz)` float32 | **đã kiểm** — `model_ncnn.py` dùng `squeeze(0)` |
| Hình dạng tensor ra | `(20, 2100)` cho imgsz 320 — cùng bố cục 20 kênh với ONNX, chỉ thiếu chiều batch | **đã kiểm** |
| `metadata.yaml` trong thư mục NCNN | có, ghi `imgsz: [320, 320]`, `task: pose`, `half: false` | **đã kiểm** — `P2-04` §3 |
| Sai số NCNN so với `.pt` | IoU lệch ~3 × 10⁻⁷ · điểm mốc lệch ~2,5 × 10⁻⁵ px | **đã kiểm** — `results/export_ncnn_20260827_2144.json` |
| **Wheel `ncnn` cho `linux/arm64`** | **có** — `ncnn-1.0.20260526-cp311-cp311-manylinux_2_24_aarch64.manylinux_2_28_aarch64.whl` | **đã kiểm** — `pip download` trong `faceid:arm64`, 28/08/2026 |

Wheel là `cp311`, khớp `python:3.11-slim-bookworm` mà `deploy/Dockerfile.arm64:1` dùng. Backend NCNN
vì thế chạy được **cả trong container ARM64 lẫn trên Pi 5 native**, và các ca `slow` không phải skip
trong container. Phương án dự phòng ở §10 không cần dùng tới.

---

## 4. Tham số — `configs/detect.yaml` KHÔNG đổi

Backend NCNN dùng lại đúng bốn khoá mà backend ONNX đang dùng: `inference.conf_threshold`,
`inference.iou_threshold`, `inference.max_faces`, `inference.num_threads`.

`num_threads` đặt qua `net.opt.num_threads` thay vì `SessionOptions`, nhưng **ý nghĩa và miền giá
trị giữ nguyên** — `0` nghĩa là để thư viện tự quyết. Cùng một khoá cấu hình điều khiển cả hai
backend là điều kiện để bước 2.6 so sánh công bằng: chỉ đổi một biến, mọi thứ khác giữ nguyên.

**Không thêm khoá mới.** Thấy thiếu tham số → dừng và báo, không tự thêm (R16).

---

## 5. Giao diện

### 5.1. Trích phần dùng chung khỏi `yolo_face.py`

Chuyển đoạn hậu xử lý hiện nằm trong `YoloFaceDetector.detect` (`yolo_face.py:247-293`) thành một
hàm **module-level** trong chính `yolo_face.py`:

```python
def giai_ma_dau_ra(
    mang_tho: np.ndarray, r: float, dx: int, dy: int,
    rong_goc: int, cao_goc: int,
    conf_threshold: float, iou_threshold: float, max_faces: int,
) -> list[FaceBox]:
    """Giải mã tensor thô 20 kênh của YOLOv8n-face thành danh sách FaceBox.

    Args:
        mang_tho: Mảng (N, 20) — đã chuyển vị, mỗi hàng một ứng viên.
        r, dx, dy: Tỉ lệ và độ lệch của phép letterbox, để quy toạ độ về ảnh gốc.
        rong_goc, cao_goc: Kích thước ảnh gốc, dùng để kẹp toạ độ.

    Returns:
        Danh sách FaceBox theo độ tin cậy giảm dần, tối đa `max_faces` phần tử.
        Rỗng khi không có ứng viên nào vượt ngưỡng.
    """
```

`YoloFaceDetector.detect` sau khi sửa chỉ còn: kiểm đầu vào → `letterbox` → `_tien_xu_ly` →
`session.run` → `giai_ma_dau_ra(...)`. **Hành vi không được đổi một chút nào** — toàn bộ
`tests/test_yolo_face.py` hiện có phải xanh y nguyên, và đó chính là lưới an toàn của phép trích này.

### 5.2. Backend NCNN — `src/detector/ncnn_backend.py`

```python
class NcnnFaceDetector:
    """Khối phát hiện khuôn mặt dùng YOLOv8n-face định dạng NCNN."""

    def __init__(self, duong_dan_thu_muc: Path | str, cfg: dict) -> None:
        """Nạp mô hình NCNN và chốt tham số suy luận.

        Args:
            duong_dan_thu_muc: Thư mục `*_ncnn_model` gồm `model.ncnn.param`,
                `model.ncnn.bin`, `metadata.yaml`.
            cfg: Toàn bộ nội dung configs/detect.yaml.

        Raises:
            LoiMoHinh: thư mục không tồn tại, thiếu tệp bắt buộc, chưa cài gói `ncnn`,
                `metadata.yaml` không đọc được hoặc thiếu khoá `imgsz`.
            LoiCauHinh: thiếu key bắt buộc trong cfg, hoặc giá trị ngoài miền hợp lệ.
        """

    @property
    def kich_thuoc_vao(self) -> int: ...

    @property
    def ten_backend(self) -> str:
        """Luôn trả 'ncnn'."""

    def detect(self, khung_hinh: np.ndarray) -> list[FaceBox]:
        """Giống hợp đồng của YoloFaceDetector.detect — cùng đầu vào, cùng đầu ra, cùng ngoại lệ."""
```

`YoloFaceDetector` nhận thêm thuộc tính `ten_backend` trả `'onnx'`.

### 5.3. Factory — `src/detector/factory.py`

```python
def tao_bo_phat_hien(duong_dan: Path | str, cfg: dict):
    """Chọn backend theo dạng đường dẫn mô hình.

    Quy tắc, theo đúng thứ tự:
      · tệp có đuôi `.onnx`                       -> YoloFaceDetector
      · thư mục chứa `model.ncnn.param`           -> NcnnFaceDetector
      · còn lại                                   -> LoiCauHinh nêu rõ đã nhận gì

    Suy ra từ đường dẫn thay vì bắt khai báo trong config: bước 2.6 quét một danh sách
    mô hình trộn cả hai định dạng trong cùng một lần chạy, nên backend là thuộc tính
    của từng mô hình chứ không phải của cả phiên đo.
    """
```

---

## 6. Thiết kế bắt buộc

### 6.1. Không nhân đôi phần hậu xử lý

Hai backend **chỉ khác nhau ở hai chỗ**: cách nạp mô hình, và cách chạy một tensor qua mô hình.
Toàn bộ phần còn lại — letterbox, chuẩn hoá, ngưỡng tin cậy, NMS, quy toạ độ về ảnh gốc, trích năm
điểm mốc — **phải dùng chung mã**.

Đây là ràng buộc chịu lực của mã việc. Nếu viết hai bản hậu xử lý, chúng sẽ trôi khỏi nhau; đến bước
2.6 ta sẽ đo được một khác biệt và **không phân biệt được** đó là khác biệt giữa hai bộ suy luận hay
giữa hai bản cài đặt hậu xử lý. Cả mã việc mất ý nghĩa.

### 6.2. Nạp và chạy NCNN

- Import `ncnn` **chỉ trong thân hàm**, không ở mức module. Container ARM64 có thể chưa có gói này
  (§0 chưa kiểm), và một dòng import ở đầu tệp làm `pytest` chết ngay khâu thu thập, kéo đổ toàn bộ
  bộ kiểm thử của cả repo.
- Thiếu gói → `LoiMoHinh` nêu đúng lệnh khắc phục.
- Tensor vào: **CHW, không có chiều batch** (§3). Đây là khác biệt duy nhất về hình dạng so với
  đường ONNX; lấy sai chỗ này thì `ncnn` không báo lỗi mà trả về rác.
- Tensor ra: chuyển vị thành `(N, 20)` rồi đưa thẳng vào `giai_ma_dau_ra`.
- Số luồng: `net.opt.num_threads` khi `num_threads > 0`.
- `ncnn.Net` giữ tài nguyên gốc C++ — giải phóng tường minh trong `__del__` hoặc `close()`, đừng phó
  mặc cho bộ thu gom rác. Bước 2.6 tạo và huỷ hàng chục detector trong một lần chạy, rò rỉ ở đây sẽ
  hiện ra thành số đo trôi dần mà không rõ nguyên nhân.

### 6.3. Kích thước đầu vào đọc từ `metadata.yaml`, không đoán từ tên thư mục

Backend ONNX đọc `kich_thuoc_vao` từ chính đồ thị (`yolo_face.py:198`). Đồ thị NCNN **không mang
thông tin đó** ở dạng đọc được dễ dàng, nên lấy từ `metadata.yaml` khoá `imgsz` (dạng `[320, 320]`,
lấy phần tử đầu).

**Không** suy từ tên thư mục `yolov8n-face-320_ncnn_model`. Tên thư mục là quy ước của dự án, người
đổi tên được; `metadata.yaml` do công cụ export sinh ra cùng lúc với trọng số. Đoán từ tên là loại
lỗi im lặng: đổi tên thư mục cho gọn, mô hình vẫn chạy, kết quả sai lệch có hệ thống mà không có gì
báo.

`imgsz` không phải số nguyên dương, hoặc hai phần tử khác nhau → `LoiMoHinh`.

### 6.4. Hai backend phải cho cùng kết quả — dung sai tính bằng PIXEL, không bằng IoU

Trên cùng ảnh, cùng cấu hình, hai backend phải trả về **cùng số khuôn mặt**, và:

| Đại lượng | Dung sai |
|---|---|
| Từng cạnh khung bao (`x1`, `y1`, `x2`, `y2`) | lệch ≤ **2 px** |
| Từng toạ độ điểm mốc | lệch ≤ **2 px** |

**Không dùng ngưỡng IoU tuyệt đối.** Vòng 1 đặt `IoU ≥ 0,99` và ca dòng 22 đỏ trong container ARM64:

```
_iou((190, 180, 250, 250), (191, 180, 250, 250)) = 0,9833  <  0,99
```

Hai backend lệch **đúng một pixel** ở cạnh trái, nhưng khung chỉ 60 × 70 px nên IoU tụt dưới ngưỡng.
Cùng độ lệch một pixel đó trên khung 200 px cho IoU 0,995 — qua ngưỡng dễ dàng. Nghĩa là ngưỡng IoU
đo *kích thước khuôn mặt trong ảnh* nhiều hơn đo *hai backend có khớp nhau không*: cùng một lỗi sẽ
bị bắt hay bị bỏ qua tuỳ người trong ảnh đứng gần hay xa camera. Đó là tiêu chí sai, không phải
ngưỡng đặt chưa khéo.

Vì sao 2 px là mức đúng: `giai_ma_dau_ra` ép toạ độ về `int` bằng `round()`, nên một giá trị float
rơi sát mốc `.5` sẽ nhảy một đơn vị khi hai nền tảng tính lệch nhau ở chữ số thứ sáu — đúng hiện
tượng quan sát được giữa host x86 và container ARM64. Hai pixel cho biên an toàn qua các nền tảng,
trong khi lỗi thật (sai chuẩn hoá đầu vào, sai letterbox, sai thứ tự kênh) làm lệch **hàng chục**
pixel chứ không phải một.

Ca dòng 22 phải chạy được **cả trên host lẫn trong container ARM64** với cùng bộ dung sai này.

---

## 7. Bảng tiêu chí nghiệm thu

Mỗi dòng là một ca kiểm thử, đặt tên `test_dong<nn>`.

### 7.1. Hàm `giai_ma_dau_ra` — `tests/test_yolo_face.py`

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Mảng rỗng `(0, 20)` → danh sách rỗng, không ném lỗi | `giai_ma_dau_ra(np.zeros((0,20)), ...) == []` |
| 02 | Mọi ứng viên dưới ngưỡng tin cậy → danh sách rỗng | dựng mảng có `conf = 0.1`, ngưỡng `0.5`; assert `== []` |
| 03 | Một ứng viên hợp lệ → đúng một `FaceBox`, toạ độ đã quy về ảnh gốc | dựng mảng biết trước, `r=0.5, dx=10, dy=20`; assert từng toạ độ bằng giá trị tính tay |
| 04 | `max_faces` cắt đúng số lượng | 5 ứng viên rời nhau, `max_faces=2`; assert `len(...) == 2` |
| 05 | Kết quả sắp xếp theo độ tin cậy giảm dần | assert danh sách `confidence` không tăng |
| 06 | Năm điểm mốc được trích đúng vị trí | assert `landmarks.shape == (5, 2)` và một giá trị tính tay |
| 07 | Toạ độ bị kẹp trong biên ảnh gốc | ứng viên tràn ra ngoài; assert `0 <= x1 <= x2 <= rong_goc` |
| 08 | `YoloFaceDetector.ten_backend == "onnx"` | assert trực tiếp |
| 09 | **Toàn bộ ca cũ của `test_yolo_face.py` vẫn xanh** | không sửa ca cũ; chúng là lưới an toàn của phép trích §5.1 |

### 7.2. Backend NCNN — `tests/test_ncnn_backend.py`

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 10 | Thư mục không tồn tại → `LoiMoHinh` | `pytest.raises(LoiMoHinh)` |
| 11 | Thiếu `model.ncnn.param` → `LoiMoHinh`, thông báo nêu tên tệp | thư mục giả trong `tmp_path`; `match="param"` |
| 12 | Thiếu `model.ncnn.bin` → `LoiMoHinh`, thông báo nêu tên tệp | `match="bin"` |
| 13 | Thiếu `metadata.yaml` → `LoiMoHinh` | `match="metadata"` |
| 14 | `metadata.yaml` thiếu khoá `imgsz` → `LoiMoHinh` | dựng YAML không có `imgsz` |
| 15 | `imgsz` không phải số nguyên dương → `LoiMoHinh` | thử `imgsz: [0, 0]` và `imgsz: ["a", "a"]` |
| 16 | `imgsz` hai phần tử khác nhau → `LoiMoHinh` | `imgsz: [320, 640]` |
| 17 | `kich_thuoc_vao` đọc từ `metadata.yaml`, **không** từ tên thư mục | đặt thư mục tên `mo-hinh-999_ncnn_model` với `imgsz: [320, 320]`; assert `== 320` |
| 18 | `ten_backend == "ncnn"` | assert trực tiếp |
| 19 | `num_threads` ngoài miền → `LoiCauHinh` | `num_threads = -1` và `= 999` |
| 20 | `detect` với đầu vào sai kiểu/hình dạng/rỗng → `ValueError` | ba ca, cùng hợp đồng với `YoloFaceDetector` |
| 21 | Nạp mô hình thật và chạy được trên một ảnh LFW | `@pytest.mark.slow`; assert trả về `list[FaceBox]` |
| 22 | **Hai backend cho cùng kết quả trên cùng ảnh** | `@pytest.mark.slow`; ≥ 3 ảnh; assert bằng số mặt, **mỗi cạnh khung lệch ≤ 2 px**, **mỗi toạ độ điểm mốc lệch ≤ 2 px** (§6.4). Thông báo assert phải nêu tên ảnh, cạnh nào, và độ lệch thật — để lượt sau không phải chạy lại mới biết lệch bao nhiêu |
| 22b | Ca dòng 22 dùng `pytest.importorskip("ncnn")`, **không** `import ncnn` trần | đọc mã; ca phải skip chứ không đỏ ở nơi thiếu gói |

### 7.3. Factory — `tests/test_detector_factory.py`

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 23 | Đường dẫn `.onnx` → `YoloFaceDetector` | `@pytest.mark.slow`; `isinstance(...)` |
| 24 | Thư mục có `model.ncnn.param` → `NcnnFaceDetector` | `@pytest.mark.slow`; `isinstance(...)` |
| 25 | Thư mục không có `model.ncnn.param` → `LoiCauHinh` | thư mục rỗng trong `tmp_path` |
| 26 | Đuôi lạ (`.pt`, `.bin`, không đuôi) → `LoiCauHinh`, thông báo nêu đã nhận gì | ba ca |
| 27 | Đường dẫn không tồn tại → `LoiCauHinh` hoặc `LoiMoHinh`, **không** `FileNotFoundError` trần | `pytest.raises((LoiCauHinh, LoiMoHinh))` |

⚠️ **Ràng buộc thu thập**: `pytest --collect-only -m "not slow"` phải chạy trót lọt **kể cả khi máy
không có `ncnn`**. Mọi ca cần gói thật phải đánh dấu `slow` hoặc giả lập bằng `monkeypatch`.

---

## 8. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

```bash
python -m black --check --line-length 100 src/detector tests/test_ncnn_backend.py tests/test_detector_factory.py tests/test_yolo_face.py
```

```bash
python -m ruff check src/detector tests/test_ncnn_backend.py tests/test_detector_factory.py tests/test_yolo_face.py
```

```bash
python -m pytest tests/test_yolo_face.py -v
```

Lệnh trên là lưới an toàn của phép trích §5.1 — mọi ca cũ phải xanh, không ca nào được sửa.

```bash
python -m pytest tests/test_ncnn_backend.py tests/test_detector_factory.py -v
```

```bash
python -m pytest -q
```

```bash
git status --short --untracked-files=all
```

Phải cho thấy đúng tám tệp của §2, không hơn.

### Quét mẫu vi phạm — cả ba lệnh phải rỗng

```bash
grep -nE "^import ncnn|^from ncnn" src/detector/*.py tests/test_ncnn_backend.py
```

```bash
grep -nE "0\.5|0\.45|320|640|2100|in0|out0" src/detector/ncnn_backend.py
```

Lệnh thứ hai: `in0`/`out0` được phép xuất hiện **đúng một lần mỗi tên**, dưới dạng hằng số có tên
đặt ở đầu tệp kèm comment nêu xuất xứ (`model.ncnn.param`), không rải rác trong thân hàm. Mọi số
khác phải giải trình.

```bash
grep -n "except Exception" src/detector/ncnn_backend.py src/detector/factory.py
```

### Kiểm đột biến bắt buộc

Bốn phép. Mỗi phép: sao lưu ra `$env:TEMP` → sửa → `pytest` → khôi phục → đối chiếu `sha256`.
**Không dùng `git checkout`** để khôi phục — mã chưa commit.

| # | Phép đột biến | Ca **phải** đỏ |
|---|---|---|
| ĐB1 | Trong `giai_ma_dau_ra`, bỏ phép kẹp toạ độ vào biên ảnh | dòng 07 |
| ĐB2 | Trong `giai_ma_dau_ra`, bỏ cắt theo `max_faces` | dòng 04 |
| ĐB3 | Trong `NcnnFaceDetector`, lấy `kich_thuoc_vao` bằng cách tách số từ tên thư mục thay vì đọc `metadata.yaml` | dòng 17 |
| ĐB4 | Trong `factory`, đổi thứ tự hai nhánh nhận dạng để mọi đường dẫn rơi vào NCNN | dòng 23 |

ĐB3 canh đúng chỗ hỏng im lặng ở §6.3.

---

## 9. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` dài dòng 100, `ruff` sạch (R19). Type hints, docstring tiếng Việt kiểu
  Google (R20).
- `logging` qua `src.common.logging.lay_logger`; **không** `print()` trong `src/` (R23).
- Thư viện được phép: thư viện chuẩn, `numpy`, `cv2`, `onnxruntime`, `ncnn`, `pyyaml`, và `src/**`.
  **Không thêm gói nào khác.**
- `ncnn` chỉ import trong thân hàm (§6.2).
- Đọc `metadata.yaml` bằng `yaml.safe_load`, **không** `yaml.load`.
- Ngoại lệ đúng loại: `LoiCauHinh` cho lỗi cấu hình, `LoiMoHinh` cho lỗi mô hình, `ValueError` cho
  dữ liệu đầu vào của `detect` — giữ nguyên hợp đồng của `YoloFaceDetector`.

---

## 10. Rủi ro đã biết

**Rủi ro wheel ARM64 đã được loại** — xem dòng cuối bảng §3. Giữ lại phương án dự phòng ở đây phòng
khi phiên bản `ncnn` sau này rút wheel `aarch64`: khi đó chuyển `ncnn` về `requirements-dev.txt`,
để ca `slow` skip trong container, và ghi lý do vào `docs/dieu-chinh-pham-vi.md`. Backend vẫn chạy
được trên Pi 5 cài native, còn container vốn chỉ dùng kiểm tính đúng đắn.

Quyết định đó **không thuộc quyền người cài đặt**. Gặp tình huống này thì dừng và báo.

**Rủi ro còn lại, cần theo dõi khi review**: `ncnn.Net` giữ tài nguyên gốc C++ (§6.2). Rò rỉ không
làm ca kiểm thử nào đỏ — nó chỉ hiện ra ở bước 2.6 dưới dạng số đo trôi dần qua các ô ma trận, và
lúc đó rất khó truy ngược. Đây là loại lỗi phải bắt bằng đọc mã, không bắt được bằng `pytest`.

---

## 11. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Sửa `scripts/benchmark_detect.py`** để dùng factory và ghi cột `backend` thật — mã việc `P2-06`.
  Tách riêng vì đây là hai trách nhiệm khác nhau: mã việc này làm cho NCNN **chạy được**, `P2-06`
  làm cho nó **được đo**.
- **Đo hiệu năng**, so sánh tốc độ hai backend — bước 2.6, cần Pi 5 thật.
- **Dọn dẹp marker `pytest`** — đăng ký `markers` trong `pyproject.toml`, bật `--strict-markers`, và
  đổi bảy ca cũ trong `test_export_detector.py`/`test_yolo_face.py` sang `pytest.importorskip`.
  Ba việc cùng một loại, thuộc mã việc dọn dẹp riêng. Hiện `pyproject.toml:7-9` không khai báo
  `markers`, nên mọi ca `@pytest.mark.slow` đều sinh `PytestUnknownMarkWarning` — và quan trọng hơn,
  một marker gõ sai tên sẽ **không** bị loại khỏi lượt `-m "not slow"` mà cũng không ai báo.
- **Chốt backend chính thức** vào `configs/detect.yaml` — Cổng C của Phase 2, quyết định từ số đo.
- Quantization, fp16, hay bất kỳ tối ưu NCNN nào — chưa bàn tới khi chưa có số đo cơ sở.

---

## 12. Báo cáo khi xong

Theo mẫu §12 của [`docs/quy-tac-cai-dat.md`](../quy-tac-cai-dat.md), tối thiểu gồm:

1. Kết quả các lệnh §8, dán nguyên văn dòng tổng kết.
2. Bảng bốn phép đột biến: ca dự đoán đỏ · ca thật sự đỏ · `sha256` khôi phục.
3. **Xác nhận phép trích §5.1 không đổi hành vi**: số ca của `tests/test_yolo_face.py` trước và sau,
   và khẳng định không ca cũ nào bị sửa.
4. Vướng mắc: chỗ nào trong đặc tả mơ hồ, thiếu, hoặc mâu thuẫn.

**Không commit.**

## 12b. Lượt của người dùng — sau khi §8 xanh

```bash
docker build -f deploy/Dockerfile.arm64 -t faceid:arm64 .
```

Bắt buộc vì `requirements.txt` đã đổi (R43). Vẫn đúng một tên image, không tag khác.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

⚠️ **Bắt buộc có `-m "not slow"`.** Vòng 1 đặc tả này ghi thiếu, và lượt chạy ngày 30/08/2026 đỏ
bảy ca vì lý do chẳng liên quan gì tới mã đang chấm: các ca `slow` cần `ultralytics`/`onnx`, hai gói
mà container **cố ý không cài** (Pi 5 chỉ chạy `onnxruntime`, xem `P0-02`). Container dùng để kiểm
**tính đúng đắn trên ARM64**, không phải để chạy phần phụ thuộc công cụ của máy phát triển.

Kết quả mong đợi: **không ca nào đỏ**, và số ca xanh tăng so với lần chạy trước vì có thêm các ca
của `P2-05`. Số ca skip không được tăng — wheel `ncnn` `aarch64` đã cài được vào image (§3), nên ca
nhanh của backend NCNN phải chạy thật chứ không bị bỏ qua.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m slow
```

Lượt riêng cho ca `slow` trong container. Ở đây các ca cần `ultralytics`/`onnx` **phải skip**, còn
**ca dòng 22 phải xanh** — đó là phép kiểm rằng hai backend khớp nhau trên chính kiến trúc ARM64,
nơi lệch làm tròn một pixel đã từng xuất hiện (§6.4). Ca nào đỏ vì `ModuleNotFoundError` là lỗi của
ca đó, không phải của mã việc này: nó thiếu `pytest.importorskip`.

```bash
python -m pytest -m slow -v
```

Các ca `slow` nạp mô hình thật, trong đó dòng 22 là ca quan trọng nhất của cả mã việc: **hai backend
cho cùng kết quả trên cùng ảnh**.
