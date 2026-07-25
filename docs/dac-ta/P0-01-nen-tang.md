# P0-01-nen-tang — Module nền tảng `src/common/`

| | |
|---|---|
| **Phase** | 0 — Khởi tạo & Môi trường |
| **Bước CLAUDE.md** | §5 Phase 0, bước 0.5 (`src/common/config.py` + `src/common/logging.py`) |
| **Nhánh** | `feat/p0-01-nen-tang` |
| **Phụ thuộc** | không — đây là mã việc đầu tiên |
| **Ước lượng** | 8 file, ~350 dòng |

---

## 1. Mục tiêu

Xây dựng bốn module nền tảng trong `src/common/` (kiểu dữ liệu, ngoại lệ, nạp cấu hình, logging)
mà **mọi khối khác của hệ thống đều phụ thuộc vào**.

---

## 2. DANH SÁCH TRẮNG — chỉ được tạo/sửa các file sau

| File | Thao tác |
|---|---|
| `pyproject.toml` | tạo mới |
| `src/__init__.py` | tạo mới (để trống) |
| `src/common/__init__.py` | tạo mới (để trống) |
| `src/common/types.py` | tạo mới |
| `src/common/exceptions.py` | tạo mới |
| `src/common/config.py` | tạo mới |
| `src/common/logging.py` | tạo mới |
| `tests/test_common.py` | tạo mới |

> Mọi file khác: **cấm chạm**. Sửa file ngoài danh sách = lỗi CHẶN-A khi review.
> Đặc biệt **không tạo `requirements.txt`** — file đó thuộc mã việc `P0-02`.
> Thư viện cần cho mã việc này: `pyyaml`, `numpy`, `pytest`, `black`, `ruff`.
> Nếu môi trường chưa có, cài bằng `pip install` — **không** ghi vào file nào cả.

---

## 3. Interface bắt buộc — giữ nguyên tên và kiểu, không đổi

### 3.1. `src/common/exceptions.py`

```python
class LoiHeThong(Exception):
    """Lỗi gốc của hệ thống — mọi ngoại lệ tự định nghĩa đều kế thừa lớp này."""

class LoiCauHinh(LoiHeThong):
    """Lỗi liên quan tới file cấu hình: không tồn tại, sai cú pháp, thiếu key bắt buộc."""

class LoiCamera(LoiHeThong):
    """Lỗi thiết bị thu hình: không mở được camera, mất kết nối, frame không hợp lệ."""

class LoiPhanCung(LoiHeThong):
    """Lỗi phần cứng chấp hành: GPIO, relay, module phát IR."""

class LoiMoHinh(LoiHeThong):
    """Lỗi mô hình: không nạp được weights, sai kích thước đầu vào, inference thất bại."""
```

### 3.2. `src/common/types.py`

```python
from dataclasses import dataclass, field
import numpy as np


@dataclass(frozen=True)
class FaceBox:
    """Một khuôn mặt phát hiện được trong frame."""

    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    landmarks: np.ndarray | None = field(default=None, compare=False, repr=False)

    @property
    def chieu_rong(self) -> int: ...

    @property
    def chieu_cao(self) -> int: ...

    @property
    def dien_tich(self) -> int: ...


@dataclass(frozen=True)
class Identity:
    """Kết quả nhận diện danh tính cho một khuôn mặt."""

    user_id: str | None          # None = người lạ
    similarity: float
    is_live: bool
    backend: str                 # "dlib" | "arcface"

    @property
    def la_nguoi_la(self) -> bool: ...


@dataclass(frozen=True)
class Command:
    """Một lệnh điều khiển thiết bị do khối quyết định sinh ra."""

    thiet_bi: str                # tên thiết bị trong configs/actuator.yaml
    hanh_dong: str               # "bat" | "tat"
    nguon: str | None            # user_id đã kích hoạt; None nếu hệ thống tự phát
    thoi_diem: float             # dấu thời gian Unix, đơn vị giây
```

> ⚠️ `landmarks` **bắt buộc** khai báo `field(compare=False, repr=False)`.
> Nếu để mặc định, `__eq__` do dataclass sinh ra sẽ so sánh mảng NumPy và ném
> `ValueError: truth value of an array is ambiguous` ngay lần đầu so sánh hai `FaceBox`.

### 3.3. `src/common/config.py`

```python
from pathlib import Path
from typing import Any


def nap_cau_hinh(duong_dan: str | Path) -> dict[str, Any]:
    """Nạp file cấu hình YAML và mở rộng biến môi trường dạng ${TEN_BIEN}."""


def lay_gia_tri(cfg: dict[str, Any], duong_dan_key: str, mac_dinh: Any = ...) -> Any:
    """Lấy giá trị lồng nhau theo đường dẫn dạng "a.b.c"."""
```

- Tham số `mac_dinh` dùng một **sentinel riêng** (ví dụ `_KHONG_CO = object()`) làm giá trị mặc định,
  **không dùng `None`** — vì `None` là một giá trị cấu hình hợp lệ.

### 3.4. `src/common/logging.py`

```python
import logging
from pathlib import Path


def thiet_lap_log(muc: str = "INFO", file_log: str | Path | None = None) -> None:
    """Thiết lập logging toàn hệ thống. Gọi một lần khi khởi động."""


def lay_logger(ten: str) -> logging.Logger:
    """Trả về logger con theo tên module, thường truyền __name__."""
```

---

## 4. Tham số → config

Mã việc này **xây dựng bộ nạp cấu hình**, chưa tiêu thụ file cấu hình nào.
Không tạo file trong `configs/` — các mã việc sau sẽ tạo.

Giá trị cố định được phép hardcode ở mã việc này (không phải tham số thực nghiệm):

| Hằng số | Giá trị | Nơi đặt |
|---|---|---|
| Kích thước tối đa file log | `10 * 1024 * 1024` byte | `logging.py`, hằng số module viết HOA |
| Số file log xoay vòng | `3` | như trên |
| Định dạng log | `"%(asctime)s %(levelname)-8s %(name)s: %(message)s"` | như trên |

---

## 5. Hành vi & ca biên

### 5.1. `nap_cau_hinh`

| Đầu vào | Kỳ vọng |
|---|---|
| File YAML hợp lệ | Trả về `dict` đúng nội dung |
| File **không tồn tại** | raise `LoiCauHinh`, thông báo chứa đường dẫn |
| File YAML **sai cú pháp** | raise `LoiCauHinh` (bọc `yaml.YAMLError`, dùng `raise ... from e`) |
| File **rỗng** | Trả về `{}`, không raise |
| Nội dung gốc **không phải mapping** (ví dụ một list) | raise `LoiCauHinh` |
| Giá trị chuỗi chứa `${TEN_BIEN}` và biến **có** trong `os.environ` | Thay bằng giá trị biến |
| Giá trị chuỗi chứa `${TEN_BIEN}` và biến **không** có | raise `LoiCauHinh`, thông báo **nêu đúng tên biến thiếu** |
| `${TEN_BIEN}` nằm trong list hoặc dict lồng nhau | Vẫn được mở rộng (đệ quy toàn cây) |
| Chuỗi chứa `$` nhưng không đúng dạng `${...}` | Giữ nguyên, không raise |
| File chứa tiếng Việt có dấu | Đọc đúng — **bắt buộc `open(..., encoding="utf-8")`** |

- Chỉ dùng `yaml.safe_load`, **không** `yaml.load`.
- Không đọc biến môi trường nào ngoài những biến được tham chiếu trong file.

### 5.2. `lay_gia_tri`

| Đầu vào | Kỳ vọng |
|---|---|
| `lay_gia_tri({"a": {"b": 1}}, "a.b")` | `1` |
| Key không tồn tại, **có** truyền `mac_dinh` | Trả `mac_dinh` |
| Key không tồn tại, **không** truyền `mac_dinh` | raise `LoiCauHinh`, thông báo chứa đường dẫn key đầy đủ |
| Đi xuyên qua giá trị không phải dict (`"a.b.c"` khi `a.b` là `int`) | raise `LoiCauHinh` |
| Giá trị hợp lệ là `None`, có truyền `mac_dinh` | Trả `None`, **không** trả `mac_dinh` |

### 5.3. `thiet_lap_log`

| Đầu vào | Kỳ vọng |
|---|---|
| Mặc định | Logger gốc có **đúng 1** handler ra `stdout`/`stderr`, mức `INFO` |
| `muc="DEBUG"` | Mức logger gốc là `DEBUG` |
| `muc` không hợp lệ (`"XYZ"`) | raise `LoiCauHinh` |
| `file_log` được truyền | Thêm `RotatingFileHandler` (10 MB × 3 bản, `encoding="utf-8"`); ghi log → file tồn tại và chứa nội dung |
| Thư mục cha của `file_log` chưa tồn tại | Tự tạo, không raise |
| **Gọi hai lần liên tiếp** | Handler **không bị nhân đôi** (log không xuất hiện 2 lần) |

- `lay_logger(__name__)` trả về đối tượng `logging.Logger`; gọi hai lần cùng tên trả về **cùng một** đối tượng.

---

## 6. Tiêu chí nghiệm thu — phải kiểm được bằng máy

- [ ] `pytest -q` xanh, **tối thiểu 18 ca test**, phủ hết mọi dòng của ba bảng ở §5
- [ ] `black --check --line-length 100 src tests` sạch
- [ ] `ruff check src tests` sạch
- [ ] `python -c "from src.common.config import nap_cau_hinh; print('ok')"` chạy được
- [ ] Test **không ghi ra ngoài `tmp_path`** — sau khi chạy `pytest`, `git status --short` không có file mới
- [ ] Toàn bộ test chạy được trên máy **không có Raspberry Pi**
- [ ] `git status --short` không có file ngoài danh sách trắng §2

---

## 7. Quy tắc áp dụng

| Mã | Vì sao liên quan ở mã việc này |
|---|---|
| **G2, G3** | `logging.py` là nơi dễ lọt `print()` nhất; log phải dùng lazy formatting |
| **G4** | Mọi hàm public cần type hints + docstring tiếng Việt kiểu Google |
| **G5** | Bắt đúng loại ngoại lệ (`FileNotFoundError`, `yaml.YAMLError`), bọc lại bằng `LoiCauHinh` với `raise ... from e` |
| **G10** | Bộ nạp cấu hình là đường đi của secret — **không log giá trị biến môi trường đã mở rộng**, chỉ log tên file cấu hình |

Thêm hai điểm riêng của mã việc này:
- **Encoding**: máy phát triển chạy Windows, mặc định không phải UTF-8.
  Mọi lần mở file phải ghi rõ `encoding="utf-8"`, kể cả trong test.
- `src/common/` **không được import** bất kỳ module nào khác của `src/` — đây là tầng đáy.

---

## 8. Ngoài phạm vi — KHÔNG làm ở mã việc này

- `requirements.txt`, `Dockerfile.arm64`, `docker-compose.yml` → mã việc `P0-02`, `P0-03`
- Bất kỳ file nào trong `configs/` → do `spec-writer` tạo ở các mã việc sau
- Module camera, detector, recognizer, actuator → Phase 1 trở đi
- Hợp nhất nhiều file cấu hình, biến thể theo môi trường (dev/prod), hot-reload config →
  ý tưởng hợp lý nhưng **ngoài đề cương**, ghi vào phần "đề xuất" của báo cáo bàn giao nếu muốn
- Nạp cấu hình từ JSON/TOML — dự án chỉ dùng YAML
- Cú pháp giá trị mặc định `${TEN:-mac_dinh}` — chỉ hỗ trợ `${TEN}` đơn giản
