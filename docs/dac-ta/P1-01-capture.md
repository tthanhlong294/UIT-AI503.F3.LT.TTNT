# P1-01-capture — Khối thu hình `src/capture/`

| | |
|---|---|
| **Phase** | 1 — Dữ liệu khuôn mặt |
| **Bước CLAUDE.md** | Nền tảng cho §5 Phase 1 bước 1.2; là KHỐI 1a của kiến trúc §3 |
| **Nhánh** | `feat/p1-01-capture` |
| **Phụ thuộc** | `P0-01-nen-tang` (dùng `LoiCamera`, `LoiCauHinh`, `nap_cau_hinh`, `lay_logger`) |
| **Ước lượng** | 7 file, ~380 dòng |

---

## 1. Mục tiêu

Xây dựng khối thu hình với **interface trừu tượng và backend giả lập**, cho phép toàn bộ hệ thống phát
triển và kiểm thử trên máy không có camera, đồng thời chạy được với camera thật mà không đổi mã gọi.

---

## 2. DANH SÁCH TRẮNG

| File | Thao tác |
|---|---|
| `src/capture/__init__.py` | tạo mới |
| `src/capture/base.py` | tạo mới — interface trừu tượng |
| `src/capture/opencv_camera.py` | tạo mới — backend camera thật |
| `src/capture/mock_camera.py` | tạo mới — backend giả lập |
| `src/capture/factory.py` | tạo mới — chọn backend theo cấu hình |
| `tests/test_capture.py` | tạo mới |
| `tests/fixtures/__init__.py` | tạo mới (để trống, giữ chỗ thư mục) |

> **Cấm chạm** mọi file khác. Đặc biệt: `configs/capture.yaml` **đã tồn tại**, chỉ đọc, không sửa.
> Không đụng `src/common/`, không tạo `scripts/`.

---

## 3. Interface bắt buộc

### 3.1. `src/capture/base.py`

```python
from abc import ABC, abstractmethod
import numpy as np


class BoThuHinh(ABC):
    """Interface trừu tượng cho mọi nguồn khung hình."""

    @abstractmethod
    def mo(self) -> None:
        """Mở nguồn thu hình. Raises LoiCamera nếu không mở được."""

    @abstractmethod
    def doc_frame(self) -> np.ndarray:
        """Đọc một khung hình. Raises LoiCamera nếu chưa mở hoặc đọc thất bại."""

    @abstractmethod
    def dong(self) -> None:
        """Giải phóng tài nguyên. Gọi nhiều lần phải an toàn."""

    @property
    @abstractmethod
    def dang_mo(self) -> bool: ...

    def __enter__(self) -> "BoThuHinh": ...
    def __exit__(self, *args: object) -> None: ...
```

`__enter__` và `__exit__` **cài đặt sẵn ở lớp cơ sở** (không trừu tượng): `__enter__` gọi `mo()` rồi
trả `self`; `__exit__` gọi `dong()`. Lớp con không cần cài lại.

### 3.2. `src/capture/opencv_camera.py`

```python
class CameraOpenCV(BoThuHinh):
    def __init__(self, cfg: dict) -> None: ...
```

`cfg` là **nhánh `opencv` của `configs/capture.yaml`**, không phải toàn bộ file.

### 3.3. `src/capture/mock_camera.py`

```python
class CameraGiaLap(BoThuHinh):
    def __init__(self, cfg: dict) -> None: ...
```

`cfg` là **nhánh `mock`**.

### 3.4. `src/capture/factory.py`

```python
def tao_bo_thu_hinh(cfg: dict) -> BoThuHinh:
    """Tạo bộ thu hình theo cấu hình. cfg là TOÀN BỘ nội dung configs/capture.yaml."""
```

---

## 4. Tham số → config

Đọc từ `configs/capture.yaml`. **Không hardcode giá trị nào dưới đây.**

| Tham số | Key | Bắt buộc | Mặc định |
|---|---|---|---|
| Backend | `backend` | có | — |
| Chỉ số thiết bị | `opencv.device_index` | có khi backend opencv | — |
| Độ phân giải | `opencv.width`, `opencv.height` | có | — |
| Khung hình khởi động | `opencv.warmup_frames` | không | `0` |
| Số lần thử lại | `opencv.max_retry` | không | `3` |
| Kích thước giả lập | `mock.width`, `mock.height` | có khi backend mock | — |
| Nguồn giả lập | `mock.source` | không | `synthetic` |
| Seed | `mock.seed` | không | `42` |
| Lặp vòng | `mock.loop` | không | `true` |
| Giới hạn khung hình | `mock.max_frames` | không | `0` (không giới hạn) |

Thiếu key bắt buộc → `LoiCauHinh` nêu rõ tên key.

---

## 5. Hành vi & ca biên

> **Bảng này chỉ chứa ca kiểm thử pytest.** Kiểm phạm vi file và kiểm số liệu là **lệnh shell**, đã
> chuyển xuống §6 — tuyệt đối **không viết ca test gọi `subprocess`** để chạy `git` hay `docker`.

| # | Điều kiện | Kỳ vọng | Assert tối thiểu |
|---|---|---|---|
| 3 | `mock`: `doc_frame` trả đúng định dạng | ảnh BGR | `f.shape == (h, w, 3) and f.dtype == np.uint8` |
| 4 | `mock`: cùng `seed` cho cùng khung hình | tái lập được (R15) | `np.array_equal(cam1.doc_frame(), cam2.doc_frame())` với hai đối tượng cùng seed |
| 5 | `mock`: khác `seed` cho khung hình khác nhau | không phải ảnh hằng | `not np.array_equal(...)` với hai seed khác nhau |
| 6 | `mock`: hai khung hình liên tiếp khác nhau | mô phỏng luồng thật | `not np.array_equal(cam.doc_frame(), cam.doc_frame())` |
| 7 | `doc_frame` khi **chưa** gọi `mo()` | raise `LoiCamera` | `pytest.raises(LoiCamera)` |
| 8 | `doc_frame` sau khi `dong()` | raise `LoiCamera` | `pytest.raises(LoiCamera)` |
| 9 | `dong()` gọi hai lần liên tiếp | không ném ngoại lệ | `cam.dong(); cam.dong()` không lỗi |
| 10 | `dang_mo` phản ánh đúng trạng thái | | `False` trước `mo()`, `True` sau `mo()`, `False` sau `dong()` |
| 11 | Dùng làm context manager | tự mở và tự đóng | `with tao_bo_thu_hinh(cfg) as cam: assert cam.dang_mo` rồi sau khối `assert not cam.dang_mo` |
| 12 | Ngoại lệ **bên trong** khối `with` | vẫn giải phóng tài nguyên | Sau `pytest.raises`, `cam.dang_mo is False` |
| 13 | `mock.max_frames = N`, đọc quá N, `loop=false` | raise `LoiCamera` | `pytest.raises(LoiCamera)` ở lần đọc thứ N+1 |
| 14 | `mock.max_frames = N`, `loop=true` | quay vòng, không lỗi | Đọc `N+2` lần không ném ngoại lệ |
| 15 | `mock.source = directory`, `source_dir` rỗng hoặc không tồn tại | raise `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 15a | `mock.source = directory`, thư mục **có ảnh hợp lệ** | **Đọc đúng ảnh từ thư mục**, không sinh ảnh tổng hợp | Ghi 2 ảnh khác nhau vào `tmp_path` bằng `cv2.imwrite`, đọc lần lượt: `np.array_equal(cam.doc_frame(), anh_1)` và `np.array_equal(cam.doc_frame(), anh_2)` |
| 15b | `directory` và `synthetic` **không** cho cùng kết quả | Hai chế độ phải thực sự khác nhau | `not np.array_equal(cam_dir.doc_frame(), cam_syn.doc_frame())` với cùng `seed` |
| 15c | `mock.source = directory`, thư mục tồn tại nhưng **không có ảnh nào** | raise `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 16 | `backend = mock` | trả về `CameraGiaLap` | `isinstance(tao_bo_thu_hinh(cfg), CameraGiaLap)` |
| 17 | `backend` không hợp lệ (`"xyz"`) | raise `LoiCauHinh`, thông báo nêu tên backend | `pytest.raises(LoiCauHinh)` |
| 18 | Thiếu key bắt buộc `mock.width` | raise `LoiCauHinh`, thông báo nêu tên key | `pytest.raises(LoiCauHinh)` |
| 19 | `backend = auto` trên máy **không có camera** | rơi về `mock`, không ném ngoại lệ | Giả lập `cv2.VideoCapture` trả `isOpened() = False`, assert trả về `CameraGiaLap` |
| 20 | `backend = opencv` mà mở thất bại | raise `LoiCamera` — **không** âm thầm rơi về mock | `pytest.raises(LoiCamera)` |
| 21 | **Toàn bộ test chạy được trên máy không có camera** | | `pytest tests/test_capture.py -q` xanh; không ca nào cần thiết bị thật |

> Dòng 20 là ranh giới quan trọng: `auto` được phép rơi về mock, nhưng khi người dùng **chỉ định rõ**
> `opencv` thì phải báo lỗi. Rơi về mock âm thầm sẽ khiến hệ thống chạy bằng ảnh giả mà không ai biết —
> và nếu điều đó xảy ra lúc thu thập dữ liệu thì toàn bộ dữ liệu thu được là vô nghĩa.

---

## 6. Tiêu chí nghiệm thu

- [ ] **Mỗi dòng bảng §5 có ít nhất một ca kiểm thử tương ứng**, và **mỗi ca có assert thật** —
      hàm test rỗng hoặc chỉ gọi hàm mà không kiểm gì là **test giả**, tính lỗi CHẶN-B
- [ ] **Không ca test nào gọi `subprocess`** để chạy `git`, `docker` hay lệnh hệ thống —
      `grep -n "subprocess\|shutil.which" tests/test_capture.py` không có kết quả
- [ ] `pytest -q` xanh **toàn bộ dự án** — 26 ca cũ của `P0-01` vẫn đạt, cộng ca mới
- [ ] **Kiểm phạm vi file** (lệnh shell, không phải ca test):
      `git status --short | grep -v "docs/review/" | wc -l` trả `7`
- [ ] **Kiểm không hardcode**: rà `src/capture/*.py`, mọi giá trị `1280`, `720`, `30`, `42` đều phải
      đến từ config chứ không nằm trong mã
- [ ] `black --check --line-length 100 src tests` và `ruff check src tests` sạch
- [ ] Nạp được cấu hình thật: `python -c "from src.common.config import nap_cau_hinh; from src.capture.factory import tao_bo_thu_hinh; c=nap_cau_hinh('configs/capture.yaml'); c['backend']='mock'; print(type(tao_bo_thu_hinh(c)).__name__)"` in `CameraGiaLap`
- [ ] Chạy được **trong container ARM64**: `docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q`
- [ ] Test **không ghi file nào ra ngoài `tmp_path`** — sau khi chạy, `git status --short` không có file mới
- [ ] `git status --short` không có file ngoài danh sách trắng §2

---

## 7. Quy tắc áp dụng

| Mã | Vì sao liên quan |
|---|---|
| **R22 / G7** | Đây **chính là** lớp trừu tượng hoá phần cứng. Không có backend mock thì mọi khối phía sau không kiểm thử được |
| **G1** | Mọi tham số camera đọc từ `configs/capture.yaml` |
| **G2, G3** | Dùng `lay_logger(__name__)` từ `src/common/logging.py`, lazy formatting |
| **G4** | Type hints + docstring tiếng Việt cho mọi hàm public |
| **G5** | Bắt đúng ngoại lệ, bọc lại thành `LoiCamera` bằng `raise ... from e` |
| **G6** | `dong()` phải giải phóng tài nguyên kể cả khi đang có lỗi |
| **R15** | `mock` nhận `seed`, cùng seed cho cùng khung hình |
| **R21** | `src/capture/` **chỉ import từ `src/common/`**, không import khối nào khác |

Thêm hai điểm riêng:

- **`import cv2` chỉ được đặt trong `opencv_camera.py`**, không đặt ở `factory.py` hay `base.py`.
  Factory phải import backend **bên trong hàm**, để máy thiếu OpenCV vẫn dùng được backend mock.
- Khung hình trả về theo thứ tự kênh **BGR** — mặc định của OpenCV. Toàn hệ thống thống nhất BGR;
  chuyển đổi màu (nếu có) là việc của khối tiêu thụ, không phải của khối thu hình.

---

## 8. Ngoài phạm vi — KHÔNG làm

- `scripts/collect_faces.py` → mã việc `P1-02`
- Quy ước đặt tên tệp ảnh → tài liệu riêng, không thuộc mã việc này
- Phát hiện khuôn mặt, cắt ảnh, căn chỉnh → Phase 1 bước 1.9 và Phase 2
- Đọc video từ tệp, đọc luồng RTSP, camera IP → ngoài đề cương
- Tách luồng đọc camera sang thread riêng, hàng đợi khung hình → tối ưu hiệu năng thuộc Phase 6 bước 6.7
- Sửa `configs/capture.yaml` — file đã có, chỉ đọc
