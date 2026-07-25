---
applyTo: "src/**/*.py, scripts/**/*.py, tests/**/*.py"
description: Chuẩn viết code Python cho hệ thống nhúng trên Raspberry Pi 5 — kiến trúc module, trừu tượng hoá phần cứng, quản lý cấu hình, logging, xử lý lỗi fail-safe và tối ưu hiệu năng.
---

# Instructions: Python cho hệ thống nhúng

Áp dụng cho **mọi file Python** trong `src/`, `scripts/`, `tests/`.

---

## 1. Nền tảng

- Python **≥ 3.11**. Format: `black --line-length 100`. Lint: `ruff`.
- **Type hints bắt buộc** cho mọi hàm public.
- **Docstring tiếng Việt** kiểu Google:

```python
def nhan_dien(self, khuon_mat: np.ndarray) -> tuple[str | None, float]:
    """Nhận diện danh tính từ ảnh khuôn mặt đã align.

    Args:
        khuon_mat: Ảnh RGB đã align, kích thước 112x112x3, dtype uint8.

    Returns:
        Cặp (user_id, diem_tuong_dong). user_id là None nếu điểm tương đồng
        thấp hơn ngưỡng trong cấu hình (người lạ).

    Raises:
        ValueError: Nếu kích thước ảnh đầu vào không đúng 112x112x3.
    """
```

- Tên biến/hàm: tiếng Anh cho khái niệm kỹ thuật phổ biến (`detect`, `embedding`, `threshold`),
  tiếng Việt không dấu chấp nhận được cho logic nghiệp vụ (`nguoi_la`, `quyen_dieu_khien`).
  **Nhất quán trong cùng một module.**

---

## 2. Kiến trúc — ánh xạ 4 khối

```
src/
├── capture/      KHỐI 1a  camera → frame
├── detector/     KHỐI 1b  frame → List[FaceBox]
├── antispoof/    KHỐI 1c  face_crop → (is_live, score)
├── recognizer/   KHỐI 1d  face_crop → (user_id, similarity)
├── decision/     KHỐI 2   user_id → List[Command]
├── actuator/     KHỐI 3   Command → tác động phần cứng
├── monitor/      KHỐI 4   Flask + Telegram + DB log
├── common/       config, logging, types, exceptions dùng chung
└── main.py       vòng lặp chính
```

**Quy tắc phụ thuộc:**
- Mỗi khối chỉ **import từ `common/`** và từ khối đứng **ngay trước** nó trong luồng.
- ❌ `detector` không được import `actuator`. ❌ `recognizer` không được import `monitor`.
- Kiểu dữ liệu chung (`FaceBox`, `Identity`, `Command`) định nghĩa **một chỗ** trong `src/common/types.py`.

```python
# src/common/types.py
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class FaceBox:
    """Khuôn mặt phát hiện được trong một frame."""
    x1: int; y1: int; x2: int; y2: int
    confidence: float
    landmarks: np.ndarray | None = None   # (5, 2) — mắt trái/phải, mũi, 2 khoé miệng

@dataclass(frozen=True)
class Identity:
    """Kết quả nhận diện danh tính."""
    user_id: str | None            # None = người lạ
    similarity: float
    is_live: bool
    backend: str
```

---

## 3. Trừu tượng hoá phần cứng — QUY TẮC CỨNG (R22)

**Mọi truy cập phần cứng (camera, GPIO, IR) phải qua interface có backend `mock`.**
Không có quy tắc này thì không thể phát triển trên Docker/PC.

```python
# src/actuator/base.py
from abc import ABC, abstractmethod

class BoDieuKhien(ABC):
    """Interface trừu tượng cho mọi bộ điều khiển thiết bị."""

    @abstractmethod
    def bat(self, thiet_bi: str) -> bool:
        """Bật thiết bị. Trả về True nếu thành công."""

    @abstractmethod
    def tat(self, thiet_bi: str) -> bool: ...

    @abstractmethod
    def trang_thai(self, thiet_bi: str) -> bool: ...

    @abstractmethod
    def dong(self) -> None:
        """Giải phóng tài nguyên, đưa mọi thiết bị về trạng thái an toàn (tắt)."""
```

```python
# src/actuator/factory.py
def tao_bo_dieu_khien(cfg: dict) -> BoDieuKhien:
    """Tạo bộ điều khiển theo cấu hình. Tự động dùng mock nếu không có phần cứng."""
    loai = cfg.get("backend", "auto")
    if loai == "auto":
        loai = "gpio" if _co_gpio() else "mock"
    if loai == "gpio":
        from .gpio_backend import GpioController
        return GpioController(cfg)
    if loai == "mock":
        from .mock_backend import MockController
        return MockController(cfg)
    raise ValueError(f"Backend không hợp lệ: {loai}")
```

Backend `mock` phải **ghi log đầy đủ** hành động giả lập để test kiểm chứng được:
```python
logger.info("MOCK: bật thiết bị %s (trạng thái mới: ON)", thiet_bi)
```

**Import phần cứng phải nằm trong hàm/nhánh**, không ở đầu file — nếu không code sẽ crash
khi import trên máy không có `RPi.GPIO`.

---

## 4. Cấu hình — không hardcode (R16)

```python
# src/common/config.py
from pathlib import Path
import yaml

def nap_cau_hinh(duong_dan: str | Path) -> dict:
    """Nạp file cấu hình YAML và mở rộng biến môi trường dạng ${TEN_BIEN}."""
    ...
```

Mọi tham số vào `configs/*.yaml`:

```yaml
# configs/recognize.yaml
backend: arcface              # dlib | arcface
model_path: models/mobilefacenet.onnx
input_size: [112, 112]
embedding_dim: 512
threshold: 0.42               # ngưỡng cosine similarity — chốt từ Phase 3, xem results/
gallery_path: data/embeddings/arcface/gallery.npz
n_frame_xac_nhan: 3           # số frame liên tiếp cùng danh tính mới kích hoạt
```

❌ Cấm tuyệt đối: `if similarity > 0.42:` trực tiếp trong code.
✅ Đúng: `if similarity > self.cfg["threshold"]:`

Mọi ngưỡng phải có **comment ghi nguồn**: xác định ở Phase nào, từ file results nào.

---

## 5. Logging (R23)

```python
# src/common/logging.py
import logging, sys
from logging.handlers import RotatingFileHandler

def thiet_lap_log(muc: str = "INFO", file_log: str | None = None) -> None:
    """Thiết lập logging toàn hệ thống, xoay vòng file tối đa 10MB x 3 bản."""
```

- ❌ **Không dùng `print()`** trong `src/`. `scripts/` chỉ được `print` bảng tóm tắt cuối cùng.
- Mức log:
  - `DEBUG` — giá trị similarity từng frame, toạ độ bbox
  - `INFO` — nhận diện thành công, lệnh điều khiển đã phát
  - `WARNING` — người lạ, phát hiện giả mạo, FPS tụt dưới ngưỡng, nhiệt độ CPU cao
  - `ERROR` — mất camera, lỗi GPIO, không nạp được model
- **Không log dữ liệu nhạy cảm**: không log embedding thô, không log đường dẫn ảnh khuôn mặt
  ở mức INFO, không log token Telegram.
- Log dùng lazy formatting: `logger.info("FPS: %.1f", fps)` — không f-string.

---

## 6. Xử lý lỗi — fail-safe (R24)

Nguyên tắc: **lỗi phần cứng không được làm sập toàn hệ thống, và phải đưa thiết bị về trạng thái an toàn (tắt).**

```python
# src/common/exceptions.py
class LoiHeThong(Exception):
    """Lỗi gốc của hệ thống."""

class LoiCamera(LoiHeThong): ...
class LoiPhanCung(LoiHeThong): ...
class LoiMoHinh(LoiHeThong): ...
```

Vòng lặp chính:

```python
def vong_lap_chinh(...) -> None:
    so_loi_lien_tiep = 0
    try:
        while dang_chay:
            try:
                frame = camera.doc_frame()
                ...
                so_loi_lien_tiep = 0
            except LoiCamera:
                so_loi_lien_tiep += 1
                logger.error("Mất kết nối camera (lần %d), thử kết nối lại...", so_loi_lien_tiep)
                if so_loi_lien_tiep >= MAX_LOI:
                    logger.critical("Vượt quá số lần thử, dừng hệ thống an toàn.")
                    break
                camera.ket_noi_lai()
            except LoiPhanCung as e:
                logger.error("Lỗi phần cứng: %s — bỏ qua lệnh, hệ thống tiếp tục.", e)
    finally:
        actuator.dong()      # LUÔN đưa thiết bị về trạng thái an toàn
        camera.dong()
        logger.info("Đã dừng hệ thống và giải phóng tài nguyên.")
```

- ❌ Không dùng `except:` trần hoặc `except Exception: pass`.
- Mọi tài nguyên phần cứng dùng context manager hoặc `try/finally`.
- Đăng ký handler cho `SIGINT`/`SIGTERM` để systemd dừng dịch vụ sạch sẽ.

---

## 7. Hiệu năng trên ARM

| Kỹ thuật | Cách làm |
|---|---|
| **Tách thread capture** | Thread riêng đọc camera vào queue `maxsize=2`, thread chính xử lý — tránh xử lý chậm làm nghẽn camera |
| **Bỏ frame cũ** | Queue đầy thì bỏ frame cũ nhất, luôn xử lý frame mới nhất (realtime > đầy đủ) |
| **Frame skipping** | Chỉ detect mỗi N frame, giữa các frame dùng tracking bbox cũ |
| **Nạp model một lần** | Khởi tạo session ONNX ở constructor, tuyệt đối không trong vòng lặp |
| **Cấu hình luồng ONNX** | `sess_options.intra_op_num_threads = 4` (Pi 5 có 4 nhân) — đo để chọn số tối ưu |
| **Tiền cấp phát buffer** | Tránh `np.zeros()` trong vòng lặp |
| **Anti-spoofing thưa** | Chỉ chạy khi phát hiện danh tính mới, không chạy mỗi frame |
| **Cache gallery** | Nạp `gallery.npz` một lần vào RAM, so khớp bằng một phép nhân ma trận |

```python
# So khớp gallery hiệu quả — 1 phép nhân ma trận thay vì vòng lặp
diem = self.gallery_emb @ emb          # (N, D) @ (D,) → (N,)
idx = int(np.argmax(diem))
return (self.user_ids[idx], float(diem[idx])) if diem[idx] >= nguong else (None, float(diem[idx]))
```

❌ Không `import torch` trong code chạy trên Pi — quá nặng. Chỉ dùng `onnxruntime` / `ncnn`.

---

## 8. Kiểm thử

- **Mọi test phải chạy được KHÔNG cần Raspberry Pi** — dùng backend `mock` và ảnh mẫu trong `tests/fixtures/`.
- Test tối thiểu cho mỗi khối:
  - `detector`: ảnh có 1 mặt → trả 1 box; ảnh không mặt → trả rỗng
  - `recognizer`: ảnh người đã enroll → đúng user_id; ảnh người lạ → `None`
  - `antispoof`: mẫu live → `True`; mẫu print → `False`
  - `decision`: user không có quyền → không sinh lệnh
  - `actuator` (mock): gọi `bat()` → `trang_thai()` trả `True`
- Test không được ghi vào `data/` hoặc `results/` — dùng `tmp_path` của pytest.
- Chạy: `pytest -q` phải xanh trước mọi commit.

---

## 9. Chuẩn viết script trong `scripts/`

Mọi script phải có:
- `argparse` với `--help` mô tả tiếng Việt
- `--config <đường dẫn>` để nạp YAML
- `--dry-run` in ra sẽ làm gì mà không thực thi
- `--seed 42` nếu có yếu tố ngẫu nhiên (R15)
- `if __name__ == "__main__": main()`
- Thoát bằng mã lỗi có nghĩa: `sys.exit(0)` thành công, `sys.exit(1)` lỗi
- In **bảng tóm tắt Markdown** ở cuối để dán vào nhật ký tuần

---

## 10. Checklist trước khi commit code

- [ ] `black --check` và `ruff check` sạch
- [ ] `pytest -q` xanh (chạy được không cần Pi)
- [ ] Không có `print()` trong `src/`
- [ ] Không có số magic — mọi tham số ở `configs/`
- [ ] Truy cập phần cứng đều qua interface có backend mock
- [ ] Không có secret / đường dẫn tuyệt đối máy cá nhân trong code
- [ ] Hàm public có type hints và docstring tiếng Việt
- [ ] Xử lý lỗi phần cứng theo nguyên tắc fail-safe
