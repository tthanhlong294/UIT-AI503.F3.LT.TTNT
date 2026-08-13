# Review P1-01-capture — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-01-capture.md` |
| **Nhánh** | `feat/p1-01-capture` |
| **Ngày** | 2026-08-08 |
| **Phán quyết** | 🔴 **TRẢ LẠI** |

Tổng: **3 lỗi 🔴 CHẶN-B** · **4 lỗi 🟡 CẦN SỬA** · **4 mục 🔵 GÓP Ý** · 0 lỗi 🔴 CHẶN-A.

---

## Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short` | đúng **7 file**, khớp danh sách trắng §2 ✅ |
| `git diff dev -- configs/capture.yaml` | rỗng — config **không bị sửa** ✅ |
| Quét file cấm lọt git (`.jpg/.npy/.onnx/.env/.db`…) | không có ✅ |
| `black --check --line-length 100 src tests` | `14 files would be left unchanged` ✅ |
| `ruff check src tests` | `All checks passed!` ✅ |
| `pytest -q` (Windows) | **47 passed** (26 cũ + 21 mới) ✅ |
| `pytest -q` (container ARM64, `aarch64`) | **1 failed, 46 passed** ❌ |

Chi tiết phạm vi file — đúng 7 file, không thừa không thiếu:

```
?? src/capture/__init__.py        ?? src/capture/base.py
?? src/capture/factory.py         ?? src/capture/mock_camera.py
?? src/capture/opencv_camera.py   ?? tests/fixtures/__init__.py
?? tests/test_capture.py
```

Sau khi chạy `pytest`, `git status --short` **không sinh file lạ** (chỉ `__pycache__/` đã bị `.gitignore` chặn) ✅

### Quét mẫu vi phạm (`code-review.instructions.md` §2)

| Mẫu | Kết quả |
|---|---|
| `print()` trong `src/` | không có ✅ |
| `except:` trần / `except Exception: pass` | không có ✅ |
| `import torch`, `import RPi`, `import pigpio` | không có ✅ |
| `logger.xxx(f"...")` — f-string trong log | không có, đều lazy formatting ✅ |
| Đường dẫn tuyệt đối máy cá nhân | không có ✅ |
| Secret trong code | không có ✅ |
| Test giả (`assert True` / thân rỗng) | **có 1** — `test_21` ❌ (xem CHẶN-B-1) |
| Nạp model trong vòng lặp | không áp dụng ✅ |

---

## Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §2 Danh sách trắng | ✅ đúng 7 file, `configs/capture.yaml` nguyên vẹn |
| §3 Interface | ✅ khớp từng ký tự: `BoThuHinh`, `mo/doc_frame/dong/dang_mo`, `CameraOpenCV(cfg)`, `CameraGiaLap(cfg)`, `tao_bo_thu_hinh(cfg) -> BoThuHinh`; `__enter__/__exit__` cài sẵn ở lớp cơ sở |
| §4 Tham số → config | ⚠️ 10/10 key được **đọc** đúng tên, mặc định khớp bảng; nhưng `mock.source = "directory"` **đọc rồi bỏ qua** (CHẶN-B-3) |
| §5 Ca biên | ⚠️ **20/21 dòng có test thật**; dòng 21 có tên hàm nhưng thân rỗng; dòng 1 test sai (CHẶN-B-1, B-2) |
| §6 Nghiệm thu | ❌ **4/6** — hỏng tiêu chí container ARM64 và tiêu chí "mỗi dòng §5 có ca test" |
| §7 Quy tắc | ⚠️ `import cv2` cô lập đúng ✅, R21 phân tầng đúng ✅, G5/G6 chưa đạt, quy ước BGR không được ghi |
| §8 Ngoài phạm vi | ✅ không làm thừa: không có `scripts/`, không detect, không đọc video/RTSP, không thread |

### Ba điểm soi kỹ — kết quả kiểm chứng bằng chạy thật

**Dòng 20 — `backend = "opencv"` mở thất bại → PHẢI raise `LoiCamera`, không âm thầm về mock.**
Đã tự viết đoạn kiểm chứng giả lập `cv2.VideoCapture` trả `isOpened() = False`:

```
[20] factory tra ve: CameraOpenCV | la CameraOpenCV: True
[20] mo() raise LoiCamera: OK
```

✅ **ĐẠT.** Nhánh `elif backend == "opencv"` (`factory.py:28-31`) không có bất kỳ đường rơi về mock nào.
Đây là điểm quan trọng nhất của mã việc và code làm đúng.

**Dòng 19 — `backend = "auto"` trên máy không camera → rơi về mock êm thấm.**

```
[19] auto khong camera -> CameraGiaLap
```

✅ **ĐẠT**, kèm log `WARNING` nêu lý do (`factory.py:45-47`) — người vận hành vẫn biết đã rơi về mock.

**§7 — `import cv2` chỉ trong `opencv_camera.py`; máy thiếu OpenCV vẫn dùng được mock.**
Đã giả lập máy không có OpenCV bằng cách chặn `__import__("cv2")`:

```
[A] import factory KHONG can cv2: OK
[B] backend=mock khi thieu cv2 -> CameraGiaLap
[C] backend=auto khi thieu cv2 -> CameraGiaLap
[D] backend=opencv khi thieu cv2 -> NEM LOI ImportError
```

✅ **ĐẠT phần chính**: `grep -rn "import cv2" src/` chỉ trả về `src/capture/opencv_camera.py:3`.
`factory.py` import backend bên trong hàm (`factory.py:25, 29, 33, 36`), `base.py` không đụng cv2.
⚠️ Riêng trường hợp `[D]` rò ra `ImportError` trần — xem CẦN SỬA-2.

**R15 — tái lập theo seed** (dòng 4, 5 bảng §5):

```
[R15-b] doi tuong moi cung seed == lan 1 ?  True    <- dòng 4 ĐẠT
[R15-a] cung doi tuong, mo lai lan 2 == lan 1 ?  False  <- xem CẦN SỬA-1
```

Dòng 5 (khác seed → khác khung hình) và dòng 6 (hai khung liên tiếp khác nhau): ✅ đạt.

**Thứ tự kênh màu BGR**: `grep -rn "cvtColor\|COLOR_\|RGB\|BGR" src/capture/` trả về **rỗng**.
Không có chuyển đổi màu ngầm nào ✅ — nhưng cũng **không có chỗ nào ghi quy ước** (CẦN SỬA-4).

---

## Lỗi phải sửa

### 🔴 CHẶN-B-1 — `test_21` là test rỗng, không kiểm gì (CB-6)

**Vị trí**: `tests/test_capture.py:223-224` (hai dòng cuối file)

```python
def test_21_chay_duoc_khong_can_camera():
    """Đảm bảo mọi test trên chạy được, đã được kiểm chứng bởi pytest."""
```

**Vì sao**: hàm chỉ có docstring, không một câu `assert` nào. Nó luôn xanh kể cả khi mọi thứ hỏng,
nên nó **làm số ca test tăng lên 21 mà độ phủ thật chỉ có 20**. Nguy hiểm hơn ở chỗ nó tạo cảm giác
dòng 21 của bảng §5 đã được kiểm — trong khi thứ nó phải chặn (một ca test lén yêu cầu camera thật)
hoàn toàn không được kiểm. Đúng lúc `P1-02` thêm ca đọc camera thật thì không có gì bắt được.

**Sửa**: thay bằng một khẳng định thật — chứng minh không module nào trong `src/capture` mở thiết bị
khi chỉ dùng mock. Ví dụ dùng `unittest.mock.patch` để `cv2.VideoCapture` ném lỗi nếu bị gọi:

```python
@patch("cv2.VideoCapture", side_effect=AssertionError("Không được chạm camera thật"))
def test_21_chay_duoc_khong_can_camera(_mvc):
    """Toàn bộ luồng mock chạy được mà không đụng tới thiết bị thật."""
    cfg = {"backend": "mock", "mock": {"width": 16, "height": 16, "seed": 1}}
    with tao_bo_thu_hinh(cfg) as cam:
        assert cam.doc_frame().shape == (16, 16, 3)
```

---

### 🔴 CHẶN-B-2 — `test_01` làm hỏng `pytest` trong container ARM64 (tiêu chí §6)

**Vị trí**: `tests/test_capture.py:17-27`

```python
    try:
        output = subprocess.check_output(
            ["git", "status", "--short"], text=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError:
        pytest.skip("Không phải git repo hoặc lỗi git")
    ...
    assert len(lines) <= 7  # Thực tế có thể < 7 nếu chưa thêm hết
```

**Vì sao — hai hậu quả riêng biệt:**

*(a) Sập trong container.* Ảnh `faceid:arm64` **không cài `git`**. Khi `git` không tồn tại,
`subprocess` ném `FileNotFoundError`, **không phải** `CalledProcessError`, nên khối `except` không bắt được:

```
$ docker run --rm -v ...:/app -w /app faceid:arm64 pytest -q
FAILED tests/test_capture.py::test_01_danh_sach_file_trang - FileNotFoundError: [Errno 2] ... 'git'
1 failed, 46 passed in 6.82s
```

Đây là **tiêu chí nghiệm thu §6 dòng 5** và nó đang đỏ. Nặng hơn: đây là môi trường chuẩn của dự án
(CLAUDE.md §0 điều 3 — "giả lập trước, phần cứng sau"), nên mọi mã việc sau sẽ thừa hưởng một
bộ test đỏ sẵn và người ta sẽ quen với việc bỏ qua nó.

*(b) Khẳng định bị nới lỏng.* Bảng §5 dòng 1 yêu cầu đếm trả **`7`**; code assert **`<= 7`**.
Ngay khi 7 file này được commit, `git status --short` trả 0 dòng → `0 <= 7` → test vĩnh viễn xanh
mà không kiểm gì. Ngược lại, khi lập trình viên đang có 8 file dơ vì việc khác, cả bộ test đỏ
vì một lý do không liên quan gì tới `src/capture`.

**Sửa**: bỏ phụ thuộc vào `git` và vào trạng thái cây làm việc. Kiểm trực tiếp **tập file** của mã việc
tồn tại đúng như danh sách trắng §2:

```python
def test_01_danh_sach_file_trang():
    """Đúng các file trong danh sách trắng §2, không thừa file nào trong src/capture."""
    goc = Path(__file__).resolve().parents[1]
    assert {p.name for p in (goc / "src" / "capture").glob("*.py")} == {
        "__init__.py", "base.py", "opencv_camera.py", "mock_camera.py", "factory.py",
    }
```

Việc đếm `git status` giữ lại ở **cổng nghiệm thu §6** (chạy tay/CI có `git`), không đưa vào `pytest`.

---

### 🔴 CHẶN-B-3 — `mock.source = "directory"` được kiểm rồi bị bỏ qua, âm thầm trả ảnh nhiễu

**Vị trí**: `src/capture/mock_camera.py:32-36` (kiểm) và `src/capture/mock_camera.py:60` (đọc)

```python
        self._source = self.cfg.get("source", "synthetic")
        if self._source == "directory":
            source_dir = self.cfg.get("source_dir", "")
            if not source_dir or not os.path.isdir(source_dir):
                raise LoiCauHinh(f"Thư mục source_dir không tồn tại hoặc rỗng: {source_dir}")
```

```python
        frame = self._rng.integers(0, 256, (self._height, self._width, 3), dtype=np.uint8)
        return frame
```

`self._source` được gán rồi **không bao giờ được đọc lại**. `doc_frame()` luôn sinh nhiễu ngẫu nhiên.

**Vì sao**: đây đúng cùng một loại lỗi mà đặc tả §5 ghi chú ở dòng 20 — *hệ thống chạy bằng ảnh giả
mà không ai biết*. Code còn đi xa hơn: nó **kiểm tra thư mục có tồn tại không** rồi vẫn phớt lờ,
nên người dùng có mọi lý do để tin là ảnh đã được đọc. Kiểm chứng bằng chạy thật, với `source_dir`
hợp lệ có chứa ảnh:

```
[source=directory] frame GIONG HET synthetic cung seed ?  True
```

Tức là `source: directory` và `source: synthetic` cho ra **cùng một mảng bit-for-bit**.
`configs/capture.yaml:27` mô tả rõ `directory : đọc lần lượt ảnh trong source_dir`.
Hậu quả cụ thể: sang Phase 2, khi kiểm thử `yolo_face.detect()` bằng mock camera trỏ vào thư mục ảnh
mẫu, detector sẽ nhận nhiễu trắng, phát hiện 0 khuôn mặt, và người ta sẽ đi sửa detector thay vì sửa
camera giả lập.

**Sửa** — chọn một trong hai, không được để nguyên:

1. *(ưu tiên)* Cài đặt thật: lưu danh sách file ảnh đã sắp xếp trong `__init__`, `doc_frame()` đọc
   `cv2.imread` tuần tự → nhưng **không được** vì `import cv2` bị cấm ngoài `opencv_camera.py` (§7).
   Vậy dùng `PIL` hoặc `np.load`… → **thực tế là đặc tả chưa quyết**, nên chọn phương án 2.
2. *(làm ngay ở vòng này)* Từ chối thẳng thay vì giả vờ hỗ trợ — thêm ngay sau khối kiểm ở dòng 36:

```python
            raise LoiCauHinh(
                "mock.source='directory' chưa được hỗ trợ ở P1-01, dùng 'synthetic'"
            )
```

và bổ sung một ca test khẳng định `source="directory"` với thư mục **hợp lệ** vẫn ném `LoiCauHinh`.
Như vậy không có đường nào trả về nhiễu trong khi người dùng nghĩ mình đang đọc ảnh.

> Ghi chú cho `spec-writer`: bảng §5 dòng 15 chỉ đặc tả **đường lỗi** của `source=directory`,
> không nói gì về đường thành công. Đây là khoảng trống của đặc tả, không phải Gemini bịa ra.
> Mã việc sau cần một dòng riêng cho ca `source_dir` hợp lệ.

---

### 🟡 CẦN SỬA-1 — `mo()` không đặt lại RNG, phá tái lập khi mở lại (R15)

**Vị trí**: `src/capture/mock_camera.py:43` (khởi tạo RNG) và `src/capture/mock_camera.py:46-49` (`mo()`)

```python
    def mo(self) -> None:
        """Mở camera giả lập."""
        self._dang_mo = True
        logger.info("Đã mở camera giả lập (độ phân giải %dx%d)", self._width, self._height)
```

**Vì sao**: `self._rng` chỉ được tạo một lần trong `__init__`. Đóng rồi mở lại **cùng một đối tượng**
sẽ tiếp tục chuỗi ngẫu nhiên cũ chứ không quay về đầu:

```
[R15-a] cung doi tuong, mo lai lan 2 == lan 1 ?  False
```

Sang Phase 2/3, script benchmark thường mở–đóng camera nhiều lượt trong một tiến trình để đo
nhiều cấu hình. Với cách này, lượt đo thứ hai nhận chuỗi khung hình khác lượt đầu dù `seed` không đổi
— hai con số trong `results/` không so sánh được với nhau, và chạy lại cũng không ra số cũ.
`_frames_read` cũng không được đặt lại nên `max_frames` tính dồn qua các lượt mở.

**Sửa**: đặt lại cả hai trong `mo()`:

```python
    def mo(self) -> None:
        """Mở camera giả lập, đặt lại luồng sinh số để bảo đảm tái lập (R15)."""
        self._rng = np.random.default_rng(self._seed)
        self._frames_read = 0
        self._dang_mo = True
        logger.info(...)
```

Bổ sung ca test: `cam.mo(); f1 = cam.doc_frame(); cam.dong(); cam.mo(); assert np.array_equal(f1, cam.doc_frame())`.

---

### 🟡 CẦN SỬA-2 — Lỗi của OpenCV không được bọc thành `LoiCamera` (G5, R24)

**Vị trí**: `src/capture/opencv_camera.py:41-47`, `src/capture/opencv_camera.py:64`, `src/capture/factory.py:29`

```python
        self._cap = cv2.VideoCapture(self._device_index)
        ...
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
```

```python
            ret, frame = self._cap.read()
```

Trong toàn bộ `src/capture/` **không có một `raise ... from e` nào**, dù §7 của đặc tả liệt kê G5
là quy tắc bắt buộc.

**Vì sao**: `cv2.VideoCapture(...)`, `.set(...)` và `.read()` có thể ném `cv2.error` (thiết bị bị rút
giữa chừng, backend V4L2 từ chối, `device_index` sai kiểu sau khi sửa YAML). Khi đó ngoại lệ bay ra
là `cv2.error`, **không phải** `LoiCamera` — trái với hợp đồng ghi ngay trong `base.py:13` và
`base.py:17` ("Raises LoiCamera"). Vòng lặp chính ở Phase 5/6 sẽ bắt `LoiCamera` để đưa relay về
trạng thái tắt; `cv2.error` lọt qua khối đó và làm sập tiến trình **trong khi relay vẫn đang bật**.
Đây chính là kịch bản R24 cấm.

Tương tự ở factory, nhánh `backend = "opencv"` rò `ImportError` trần khi máy thiếu OpenCV — đã kiểm chứng:

```
[D] backend=opencv khi thieu cv2 -> NEM LOI ImportError : Khong co module cv2
```

Người gọi bắt `(LoiCamera, LoiCauHinh)` sẽ không bắt được.

**Sửa**:

1. `opencv_camera.py` — bọc mọi lời gọi cv2 trong `mo()` và `doc_frame()`:

```python
        try:
            self._cap = cv2.VideoCapture(self._device_index)
            ...
        except cv2.error as e:
            self._cap = None
            raise LoiCamera(f"Lỗi OpenCV khi mở device_index={self._device_index}") from e
```

2. `factory.py:28-31` — bọc import:

```python
    elif backend == "opencv":
        try:
            from .opencv_camera import CameraOpenCV
        except ImportError as e:
            raise LoiCauHinh("backend='opencv' nhưng máy không có OpenCV") from e
```

3. Bổ sung ca test: `patch("cv2.VideoCapture", side_effect=cv2.error("hong"))` → `pytest.raises(LoiCamera)`.

---

### 🟡 CẦN SỬA-3 — `dong()` của `CameraOpenCV` không bảo đảm giải phóng khi có lỗi (G6)

**Vị trí**: `src/capture/opencv_camera.py:71-78`

```python
    def dong(self) -> None:
        """Đóng camera."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None
        if self._dang_mo:
            self._dang_mo = False
```

**Vì sao**: nếu `release()` ném lỗi (hay gặp khi thiết bị USB đã bị rút), `self._cap = None` và
`self._dang_mo = False` **không chạy**. Đối tượng kẹt ở trạng thái `dang_mo == True` với một handle
chết. Lần `doc_frame()` sau sẽ vượt qua kiểm tra ở dòng 60 và thao tác trên handle đã hỏng, còn
`__exit__` thì ném lỗi ra khỏi khối `with` che mất ngoại lệ gốc bên trong. Đặc tả §5 dòng 9 và dòng 12
đòi `dong()` an toàn khi gọi nhiều lần và giải phóng được kể cả khi đang có lỗi — hiện chỉ đúng ở
nhánh không lỗi.

**Sửa**: dùng `try/finally` để trạng thái luôn được hạ xuống:

```python
    def dong(self) -> None:
        """Giải phóng camera. An toàn khi gọi nhiều lần và khi release() lỗi."""
        try:
            if self._cap is not None:
                self._cap.release()
        except Exception as e:  # noqa: BLE001 — đóng thiết bị không được phép làm sập hệ thống
            logger.warning("Lỗi khi giải phóng camera: %s", e)
        finally:
            self._cap = None
            if self._dang_mo:
                self._dang_mo = False
                logger.info("Đã đóng camera OpenCV")
```

---

### 🟡 CẦN SỬA-4 — Docstring thiếu `Returns` và không ghi quy ước kênh màu BGR (G4, §7)

**Vị trí**: `src/capture/mock_camera.py:51-52` và `src/capture/opencv_camera.py:58-59`

```python
    def doc_frame(self) -> np.ndarray:
        """Đọc khung hình."""
```

**Vì sao**: §7 của đặc tả chốt "khung hình trả về theo thứ tự kênh **BGR**, toàn hệ thống thống nhất
BGR". Hiện code **làm đúng** (đã quét: không có `cvtColor`/`COLOR_`/`RGB` ở đâu trong `src/capture/`),
nhưng quy ước này không được ghi ở bất kỳ đâu. Khối tiêu thụ tiếp theo — `src/detector/` ở Phase 2 —
sẽ phải đoán. Đoán sai một lần là kênh R và B hoán vị: YOLO vẫn chạy, vẫn ra bbox, chỉ là kém chính
xác hơn một chút và **không có gì báo lỗi**. Loại sai lệch đó rơi thẳng vào bảng số liệu Chương 4.
Docstring Google style cũng bắt buộc có `Returns` cho hàm có giá trị trả về (G4).

**Sửa**: bổ sung mục `Returns` cho `doc_frame()` ở **cả hai** backend:

```python
    def doc_frame(self) -> np.ndarray:
        """Đọc một khung hình.

        Returns:
            np.ndarray: khung hình `(height, width, 3)`, `dtype=uint8`, thứ tự kênh **BGR**.

        Raises:
            LoiCamera: khi chưa gọi `mo()` hoặc đọc thất bại.
        """
```

Bổ sung tương ứng vào ca test dòng 3 (`tests/test_capture.py:45-51`) một khẳng định rằng khối thu hình
không hoán vị kênh — với backend `opencv` có thể `patch` `cap.read()` trả mảng mốc
`[[[1, 2, 3]]]` rồi assert `doc_frame()[0, 0].tolist() == [1, 2, 3]`.

---

## 🔵 Góp ý (không chặn — người dùng quyết định)

- **`loop: true` hiện không thật sự "quay vòng"** (`mock_camera.py:56`). Đã kiểm: với `max_frames=2,
  loop=True`, khung thứ 3 **không** trùng khung thứ 1. Với nguồn `synthetic` thì khái niệm quay vòng
  gần như vô nghĩa, nên hiện trạng vô hại; nhưng khi `source=directory` được cài đặt thật (CHẶN-B-3)
  thì phải xử lý đúng. *Chi phí*: ~5 dòng, nên gộp vào mã việc cài đặt `directory`.
- **`opencv.fps: 30` trong `configs/capture.yaml:14` không được dùng** — code không gọi
  `cap.set(cv2.CAP_PROP_FPS, ...)`. Bảng §4 của đặc tả không liệt kê key này nên **không tính là lỗi**.
  *Lợi ích nếu thêm*: FPS đo được ở Phase 2 phụ thuộc trực tiếp vào FPS cảm biến; để lệch giữa config
  và thực tế sẽ khó giải thích số đo. *Chi phí*: 1 dòng code + 1 dòng bảng §4 của đặc tả sau.
- **`test_02` (`tests/test_capture.py:30-42`) kiểm bằng cách tìm chuỗi `"30"` trong mã nguồn** — rất
  giòn: một `range(30)` hợp lệ hay thậm chí một chuỗi con trong comment cũng làm đỏ, còn
  `width = 1281` thì lọt. Đặc tả §5 dòng 2 vốn ghi "rà tay". *Đề xuất*: chuyển thành khẳng định
  hành vi — dựng `cfg` với `width/height` lạ (ví dụ 37×53) và assert `frame.shape == (53, 37, 3)`;
  như vậy bất kỳ giá trị hardcode nào cũng lộ ra.
- **`backend: auto` mở rồi đóng camera thật ngay trong factory** (`factory.py:41-42`), sau đó trả về
  đối tượng **đã đóng** để người gọi mở lại. Trên Pi 5 với camera V4L2, mở–đóng–mở liên tiếp đôi khi
  cần độ trễ giữa hai lần, và tổng thời gian khởi động tăng thêm ~0,5–2 s. *Phương án gọn hơn*: giữ
  nguyên phiên đã mở và trả về đối tượng đang mở, hoặc dò bằng `cv2.VideoCapture(idx).isOpened()`
  trên một handle tạm. Cả hai đều đổi hợp đồng của factory nên **thuộc thẩm quyền `spec-writer`**,
  không phải lỗi của Gemini.

---

## Nhận xét về chất lượng đặc tả (gửi `spec-writer`)

Đặc tả này **tốt trên trung bình**: bảng §5 có cột `Assert tối thiểu` nên 20/21 dòng được cài đặt đúng
ngay vòng đầu, và ghi chú in đậm ở dòng 20 rõ ràng đến mức Gemini không sai chỗ nguy hiểm nhất.
Hai điểm cần rút kinh nghiệm:

1. **Dòng 15 chỉ đặc tả đường lỗi của `source=directory`, bỏ trống đường thành công** → sinh ra
   CHẶN-B-3. Quy tắc rút ra: mỗi khi bảng ca biên có một dòng dạng "X sai → lỗi", phải có dòng cặp
   "X đúng → hành vi gì".
2. **Cột `Assert tối thiểu` của dòng 1 và dòng 2 là lệnh shell, không phải khẳng định pytest** →
   Gemini gói chúng thành test và kéo `git`/`subprocess` vào bộ test, làm đỏ container ARM64
   (CHẶN-B-2). Quy tắc rút ra: tách rõ hai loại — "kiểm ở cổng nghiệm thu §6" và "ca test trong §5" —
   đừng để lệnh shell nằm trong cột assert của bảng ca biên.

Không có dấu hiệu mã việc quá to (7 file, ~380 dòng, đúng ước lượng) và không có dấu hiệu Gemini hiểu
sai lặp lại. Dự kiến vòng 2 xử lý được toàn bộ.

---

## Việc tiếp theo

Giao lại Gemini (nhịp 4) trên nhánh `feat/p1-01-capture`, sửa đúng **3 lỗi 🔴 + 4 lỗi 🟡** ở trên,
**không chạm file nào ngoài `src/capture/` và `tests/test_capture.py`**. Sau khi sửa, phải xanh cả ba lệnh
máy **và** lệnh container:

```bash
black --check --line-length 100 src tests
ruff check src tests
pytest -q
docker run --rm --platform linux/arm64 -v "$(pwd)":/app -w /app faceid:arm64 pytest -q
```

Xong thì gọi lại `code-reviewer` cho **vòng 2**, ghi nối tiếp vào chính file này.

---
---

# Review P1-01-capture — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-01-capture.md` (**bản đã cập nhật** sau vòng 1: §5 bỏ dòng 1–2, thêm 15a/15b/15c; §6 thêm 3 tiêu chí) |
| **Nhánh** | `feat/p1-01-capture` |
| **Ngày** | 2026-08-13 |
| **Phán quyết** | 🔴 **TRẢ LẠI** |

Tổng: **1 lỗi 🔴 CHẶN-A** · **1 lỗi 🔴 CHẶN-B** · **1 lỗi 🟡 CẦN SỬA** · 2 mục 🔵 GÓP Ý.

> ⚠️ Đây là **vòng 2 — vòng cuối** theo CLAUDE.md §2.9. Lỗi CHẶN-B còn lại **có nguyên nhân gốc từ
> đặc tả, không phải từ cài đặt** — xem mục "Chẩn đoán trần 2 vòng" ở cuối. Kiến nghị **sửa đặc tả
> trước**, rồi mới giao lại Gemini.

---

## Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short` | **9 dòng** — 7 file danh sách trắng + `docs/review/` + **`test.png` lạ** ❌ |
| `git diff dev -- configs/capture.yaml` | rỗng — config **không bị sửa** ✅ |
| Quét file cấm lọt git | **có `test.png`** ❌ |
| `black --check --line-length 100 src tests` | `14 files would be left unchanged` ✅ |
| `ruff check src tests` | `All checks passed!` ✅ |
| `pytest -q` (host Windows) | **52 passed in 1.60s** ✅ |
| `pytest -q` (container ARM64 `aarch64`) | **2 failed, 50 passed in 7.09s** ❌ |
| `grep -n "subprocess\|shutil.which" tests/test_capture.py` | không kết quả ✅ |

---

## Xác minh các lỗi vòng 1 — **7/7 đã sửa đúng**

| Vòng 1 | Trạng thái | Bằng chứng |
|---|---|---|
| 🔴 CHẶN-B-1 test rỗng | ✅ **đã sửa** | `tests/test_capture.py:322-327` — `test_21` nay `patch` `cv2.VideoCapture` bằng `side_effect=AssertionError` và assert `shape == (16, 16, 3)` |
| 🔴 CHẶN-B-2 `subprocess`/`git` | ✅ **đã sửa** | `tests/test_capture.py:15-24` — so khớp tập tên file bằng `Path.glob`, không còn `subprocess`; container không còn đỏ vì lý do này |
| 🔴 CHẶN-B-3 `directory` âm thầm trả nhiễu | ✅ **đã sửa thật** | kiểm chứng độc lập bên dưới |
| 🟡 CS-1 `mo()` reset RNG | ✅ **đã sửa** | `mock_camera.py:56-61` reset cả `_rng` lẫn `_frames_read`; test `test_04b` |
| 🟡 CS-2 bọc lỗi cv2 | ✅ **đã sửa** | `opencv_camera.py:55-57` và `:80-81` `raise LoiCamera(...) from e`; `factory.py:29-32` bọc `ImportError` thành `LoiCauHinh`; test `test_20` có nhánh `cv2.error` |
| 🟡 CS-3 `dong()` fail-safe | ✅ **đã sửa** | `opencv_camera.py:85-96` có `try/except/finally`, trạng thái luôn hạ xuống |
| 🟡 CS-4 docstring `Returns` + BGR | ✅ **đã sửa** | `mock_camera.py:63-71`, `opencv_camera.py:62-70` ghi rõ "thứ tự kênh **BGR**"; test `test_03b` |

### Kiểm chứng độc lập (tự chạy, không dựa vào test của Gemini)

Ghi hai ảnh khác nhau ra thư mục tạm bằng `cv2.imwrite`, đọc lần lượt, so bit-for-bit:

```
[15a] doc dung anh 1 (bit-for-bit)? True
[15a] doc dung anh 2 (bit-for-bit)? True
[15a] anh 3 quay vong ve anh 1?     True
[15b] directory KHAC synthetic cung seed? True     <- phép thử bắt trực tiếp lỗi vòng 1
[15c] thu muc rong -> LoiCauHinh: OK
[R15] mo lai cung seed cho cung khung hinh? True
[14]  loop=True synthetic: f[2]==f[0]? True | f[3]==f[1]? True
[dir loop=False] doc qua so anh -> LoiCamera: OK
```

**Lỗi nghiêm trọng nhất của vòng 1 đã được xử lý dứt điểm**: `source=directory` nay đọc đúng tệp ảnh,
và không còn trùng với `synthetic` cùng seed. Đáng ghi nhận thêm: `loop=true` giờ **thực sự quay vòng**
cho cả hai nguồn (góp ý vòng 1 đã được tiếp thu, `mock_camera.py:76-88`).

Kiểm riêng quy ước **BGR** bằng ảnh một màu xanh lam thuần (`BGR = [255,0,0]`) ghi ra rồi đọc lại:

```
[BGR] pixel doc ra: [255, 0, 0] -> giu BGR: True
```

Phép lật kênh `frame[:, :, ::-1]` ở `mock_camera.py:97` là **đúng** (PIL trả RGB, hệ thống cần BGR).

### Đối chiếu bảng §5 bản mới — **22/22 dòng có test, không thiếu dòng nào** ✅

| Dòng §5 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 15a | 15b | 15c | 16 | 17 | 18 | 19 | 20 | 21 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Có test | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

Thêm 2 ca **ngoài yêu cầu** nhưng đúng hướng: `test_03b` (không hoán vị kênh BGR), `test_04b` (mở lại
cùng seed). Mọi ca đều có assert thật — không còn test giả. 26 ca mới + 26 ca `P0-01` = 52 ✅

### Đối chiếu tiêu chí §6

| Tiêu chí | Kết luận |
|---|---|
| Mỗi dòng §5 có test, mỗi ca có assert thật | ✅ |
| Không ca test nào gọi `subprocess` | ✅ |
| `pytest -q` xanh toàn dự án (host) | ✅ 52 passed |
| Kiểm phạm vi file trả `7` | ❌ trả **8** (có `test.png`) |
| Không hardcode `1280/720/30/42` | ✅ rà tay `src/capture/*.py`: mọi giá trị đến từ `cfg` |
| `black` + `ruff` sạch | ✅ |
| Nạp config thật in `CameraGiaLap` | ✅ |
| Chạy được trong container ARM64 | ❌ **2 failed** |
| Test không ghi file ra ngoài `tmp_path` | ✅ (đã kiểm — xem CHẶN-A-1) |
| `git status` không có file ngoài danh sách trắng | ❌ `test.png` |

---

## Lỗi phải sửa

### 🔴 CHẶN-A-1 — `test.png` ở gốc repo, ngoài DANH SÁCH TRẮNG (CA-5 + CA-4)

**Vị trí**: `test.png` (thư mục gốc repo)

```
$ git status --short
?? test.png
$ file test.png
test.png: PNG image data, 10 x 10, 8-bit/color RGB, non-interlaced   (378 bytes, 21:22 ngày 13/08)
```

**Đã truy nguồn gốc** — không phải do ca test sinh ra:

```
mtime TRUOC pytest: 2026-08-13 21:22:58.492141700
mtime SAU  pytest: 2026-08-13 21:22:58.492141700
>>> KET LUAN: pytest KHONG tao lai test.png
```

`grep -rn "test\.png"` trên toàn repo **không có kết quả** — không tệp nguồn nào tham chiếu tới nó.
Các ca `test_15a/15b` đều ghi ảnh vào `tmp_path` đúng chuẩn (`tests/test_capture.py:201-206, 228-230`).
Vậy đây là **rác còn lại từ một script chạy tay** trong lúc phát triển, không được dọn.

**Vì sao**: `.gitignore` chỉ chặn `results/**/*.png` (dòng 247), **không chặn `*.png` ở gốc repo** —
đã kiểm. Nên một lệnh `git add -A` khi commit sẽ đưa thẳng tệp ảnh này vào lịch sử git. Với đồ án
này, mọi tệp ảnh lọt vào git đều phải bị chặn phản xạ (R25): hôm nay là ảnh nhiễu 10×10 vô hại, nhưng
đúng quy trình đó áp lên `data/raw/` là ảnh khuôn mặt người thân, và **lịch sử git thì không xoá được
bằng một commit sau**. Mục checklist §7 CLAUDE.md "Không có secret / ảnh khuôn mặt / weights lớn trong
git history" là mục không được phép sai một lần nào.

**Sửa**: xoá tệp, không commit:

```bash
rm test.png
git status --short | grep -v "docs/review/" | wc -l   # phải trả 7
```

Nếu cần ảnh tạm khi thử tay, ghi vào thư mục tạm của hệ điều hành (`tempfile.mkdtemp()`), không ghi
vào cây làm việc. *(Việc bổ sung `*.png` ở gốc vào `.gitignore` là hợp lý nhưng `.gitignore` **không**
nằm trong danh sách trắng §2 — đề xuất này chuyển cho người dùng, xem 🔵 GÓP Ý.)*

---

### 🔴 CHẶN-B-2 — `pytest` đỏ trong container ARM64: phụ thuộc `Pillow` không được khai báo

**Vị trí**: `src/capture/mock_camera.py:92`

```python
            try:
                from PIL import Image

                img = Image.open(file_path).convert("RGB")
```

**Vì sao**: `Pillow` **không có trong `requirements.txt`** (đã kiểm — tệp chỉ pin `onnxruntime`,
`opencv-python`, `numpy`, `pyyaml`, `flask`, `python-telegram-bot`) và **không có trong container ARM64**:

```
$ docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 sh -lc "python -c 'import PIL'"
ModuleNotFoundError: No module named 'PIL'

$ docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q
FAILED tests/test_capture.py::test_15a_mock_source_directory_hop_le
FAILED tests/test_capture.py::test_15b_directory_va_synthetic_khac_nhau
2 failed, 50 passed in 7.09s
```

Máy Windows của sinh viên tình cờ có `Pillow` (kéo theo từ gói khác) nên host xanh 52/52 — **đúng loại
lỗi mà cổng container sinh ra để bắt**. Hậu quả cụ thể: `configs/capture.yaml` cho phép
`mock.source: directory`; khi triển khai lên Pi 5 bằng đúng `requirements.txt` đã pin, bật chế độ đó
sẽ hỏng ngay ở khung hình đầu tiên, trong khi trên máy dev nó chạy hoàn hảo.

**Sửa**: xem mục **"Chẩn đoán trần 2 vòng"** bên dưới — **không giao lại Gemini ngay**, vì đặc tả hiện
hành không cho phép cách sửa nào hợp lệ. Phương án khuyến nghị (rẻ nhất, không phải dựng lại ảnh
container, không thêm dependency) là dùng `cv2.imread` ngay trong nhánh `directory`:

```python
        if self._source == "directory":
            ...
            import cv2  # import trong hàm: chế độ synthetic vẫn chạy khi máy thiếu OpenCV

            frame = cv2.imread(file_path, cv2.IMREAD_COLOR)   # trả về BGR sẵn
            if frame is None:
                raise LoiCamera(f"Không đọc được ảnh {file_path}")
            frame = cv2.resize(frame, (self._width, self._height))
```

Cách này còn **bỏ được phép lật kênh thủ công** `frame[:, :, ::-1]` (`mock_camera.py:97`) — một chỗ dễ
sai thầm lặng. Nhưng nó **đòi sửa §7 của đặc tả trước** (xem chẩn đoán).

---

### 🟡 CẦN SỬA-1 — `except Exception` biến lỗi thiếu thư viện thành thông báo sai địa chỉ

**Vị trí**: `src/capture/mock_camera.py:99-100`

```python
            except Exception as e:
                raise LoiCamera(f"Không thể đọc ảnh {file_path}") from e
```

**Vì sao**: khối `try` bao trùm cả câu lệnh `from PIL import Image`, nên `ModuleNotFoundError` bị gộp
chung với lỗi đọc tệp. Đã kiểm chứng bằng cách chặn `import PIL`:

```
[thieu PIL] loai: LoiCamera
[thieu PIL] thong bao nguoi dung thay: Không thể đọc ảnh C:\...\tmp...\1.png
[thieu PIL] nguyen nhan that bi giau trong __cause__: ImportError("No module named 'PIL'")
```

Người vận hành trên Pi 5 đọc log thấy "Không thể đọc ảnh &lt;đường dẫn&gt;" sẽ đi kiểm tra tệp ảnh,
quyền thư mục, thẻ nhớ — trong khi nguyên nhân thật là thiếu một thư viện. Nguyên nhân thật chỉ nằm
trong `__cause__`, thứ mà log dạng một dòng không in ra. Đây là bẫy chẩn đoán, và nó **đã bắt đúng
người review**: kết quả host xanh che mất lỗi cho tới khi chạy container.

**Sửa**: tách import ra khỏi khối `try` đọc tệp và cho nó thông báo riêng; đồng thời đưa import lên
đầu nhánh thay vì thực thi lại **ở mỗi khung hình** (hàm `doc_frame()` chạy mỗi frame):

```python
        if self._source == "directory":
            try:
                import cv2
            except ImportError as e:
                raise LoiCauHinh("mock.source='directory' cần OpenCV, hãy cài opencv-python") from e
            ...
            try:
                frame = ...
            except (OSError, ValueError) as e:
                raise LoiCamera(f"Không thể đọc ảnh {file_path}") from e
```

Bắt `(OSError, ValueError)` thay cho `Exception` để lỗi lập trình không bị nguỵ trang thành lỗi đọc tệp.

---

## 🔵 Góp ý (không chặn — người dùng quyết định)

- **`.gitignore` không chặn ảnh ở gốc repo.** Hiện chỉ có `results/**/*.png` (dòng 247). Đề xuất thêm
  `/*.png` và `/*.jpg` ở gốc để loại rác kiểu `test.png` một cách hệ thống thay vì trông chờ người
  nhớ xoá. *Chi phí*: 2 dòng. *Lợi ích*: một lớp chặn phản xạ cho R25 — đáng làm trước khi Phase 1 bắt
  đầu thu ảnh thật. `.gitignore` **không nằm trong danh sách trắng §2**, nên việc này phải do người
  dùng hoặc `spec-writer` làm, không giao Gemini trong mã việc này.
- **`img.resize((self._width, self._height))` (`mock_camera.py:95`) co giãn ảnh không giữ tỉ lệ khung.**
  Đúng đặc tả (khung hình phải khớp `mock.width/height`) nên **không tính lỗi**. Nhưng khi Phase 2 dùng
  `source=directory` để nạp ảnh khuôn mặt thật 1280×720 vào cấu hình mock 640×480, ảnh sẽ bị bóp méo
  tỉ lệ và bbox đo được sẽ lệch so với ảnh gốc. *Đề xuất*: mã việc sau cân nhắc thêm khoá
  `mock.giu_ti_le` (letterbox), hoặc ghi rõ trong tài liệu rằng thư mục nguồn phải cùng tỉ lệ với
  `mock.width/height`.

---

## Chẩn đoán trần 2 vòng — **nguyên nhân gốc là ĐẶC TẢ, không phải cài đặt**

Theo CLAUDE.md §2.9, hết vòng 2 còn 🔴 thì dừng và chẩn đoán. Kết luận: **đặc tả hiện hành tự mâu
thuẫn, không tồn tại cách cài đặt nào hợp lệ cho dòng 15a**. Ba ràng buộc khoá lẫn nhau:

| Ràng buộc | Nội dung | Hệ quả |
|---|---|---|
| §5 dòng 15a/15b | `source=directory` phải **đọc đúng tệp ảnh** (`.png` ghi bằng `cv2.imwrite`) | cần một thư viện giải mã ảnh |
| §7 gạch đầu dòng 1 | "**`import cv2` chỉ được đặt trong `opencv_camera.py`**" | cấm dùng `cv2.imread` trong `mock_camera.py` |
| §2 DANH SÁCH TRẮNG | 7 tệp, **không có `requirements.txt`** | cấm khai báo thư viện thay thế |

Gemini bị kẹt giữa ba điều này và đã chọn lối thoát tệ nhất trong các lối thoát: lấy một dependency
không khai báo. Đó là lỗi đáng ghi nhận của cài đặt — **lẽ ra phải dừng và báo xung đột** thay vì tự
xoay xở — nhưng gốc rễ nằm ở đặc tả. Xét theo bảng chẩn đoán CLAUDE.md §2.9, đây là ô
"**yêu cầu bất khả thi về kỹ thuật → sai thiết kế → trình người dùng, sửa kiến trúc**", không phải ô
"Gemini bỏ qua yêu cầu".

Bằng chứng ủng hộ kết luận này: **7/7 lỗi vòng 1 đều được sửa đúng và đủ**, kể cả lỗi khó nhất
(`directory` âm thầm trả nhiễu). Gemini không hiểu sai lặp lại điều gì; mã việc cũng không quá to.

### Ba phương án sửa đặc tả — người dùng chọn một

| | Phương án | Sửa gì | Chi phí | Đánh giá |
|---|---|---|---|---|
| **A** | **Nới §7**: cho phép `import cv2` **bên trong hàm** ở nhánh `directory` của `mock_camera.py` | 1 dòng đặc tả §7 | thấp nhất — `opencv-python` đã pin sẵn, container đã có, **không phải dựng lại ảnh** | ✅ **khuyến nghị**. Vẫn giữ nguyên lý do gốc của §7: chế độ `synthetic` (mặc định) chạy được trên máy thiếu OpenCV. Còn bỏ được phép lật kênh thủ công vì `cv2.imread` trả BGR sẵn |
| **B** | Thêm `requirements.txt` vào danh sách trắng §2 + pin `pillow==<ver>` | §2 + `requirements.txt` + **dựng lại ảnh ARM64** | cao — phải build lại container 1,05 GB, đụng vào phạm vi `P0-03` | dùng nếu về sau thật sự cần Pillow |
| **C** | Đổi dòng 15a/15b sang tệp `.npy` đọc bằng `numpy` | §5 hai dòng | thấp | ❌ không nên: mất khả năng nạp ảnh khuôn mặt thật `.jpg` vào pipeline để kiểm thử Phase 2/3 — đúng công dụng chính của chế độ `directory` |

Nếu chọn **A**, câu chữ §7 nên sửa thành:

> `import cv2` **ở cấp module** chỉ được đặt trong `opencv_camera.py`. `factory.py` và `base.py` không
> được import `cv2` dưới bất kỳ hình thức nào. `mock_camera.py` được phép `import cv2` **bên trong
> nhánh `source=directory`** để giải mã ảnh; chế độ `synthetic` (mặc định) phải chạy được khi máy
> không có OpenCV.

Nên bổ sung luôn vào §6 một tiêu chí bắt đúng lớp lỗi vừa gặp:

> - [ ] **Không thêm thư viện ngoài `requirements.txt`**:
>   `grep -rnE "^\s*(import|from)\s+(PIL|matplotlib|scipy|skimage|torch)" src/` không có kết quả

---

## Việc tiếp theo

**Không giao lại Gemini ngay.** Trình tự đề nghị:

1. **Người dùng chọn phương án A / B / C** ở trên.
2. `spec-writer` cập nhật `docs/dac-ta/P1-01-capture.md` (§7 và §6), commit đặc tả trước — theo R39,
   sửa đặc tả rồi commit, không giải thích miệng.
3. Giao Gemini **vòng 3** với phạm vi hẹp, chỉ 3 việc: xoá `test.png`; thay `PIL` theo phương án đã
   chọn; tách `import` khỏi khối `try` đọc tệp (CẦN SỬA-1). Không chạm tệp nào khác.
4. Điều kiện nghiệm thu vòng 3 — phải xanh **cả bốn** lệnh, đặc biệt hai lệnh cuối:

```bash
black --check --line-length 100 src tests
ruff check src tests
pytest -q
docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q
git status --short | grep -v "docs/review/" | wc -l    # phải trả 7
```

5. Review vòng 3 ghi nối tiếp vào chính tệp này.

> Ghi chú: phần thân mã nguồn đã **rất gần đạt**. Sau khi gỡ nút thắt `PIL` và xoá `test.png`, mã việc
> này đủ điều kiện commit với message theo R29:
> `feat(capture): khoi thu hinh KHOI 1a voi backend mock va opencv — P1-01-capture`

---
---

# Review P1-01-capture — vòng 3

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-01-capture.md` (**bản đã sửa theo phương án A**: §7 cho phép `import cv2` trong nhánh `directory`; §6 thêm cổng container ARM64 và lệnh chặn thư viện ngoài) |
| **Nhánh** | `feat/p1-01-capture` |
| **Ngày** | 2026-08-13 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN — được commit** |

Tổng: **0 lỗi 🔴** · **0 lỗi 🟡** · **3 mục 🔵 GÓP Ý** (không chặn, người dùng quyết định).

> Cả hai lỗi 🔴 của vòng 2 đã được xử lý dứt điểm. **Cổng quyết định của vòng này — `pytest` trong
> container ARM64 — nay xanh hoàn toàn 52/52**, trong khi container **vẫn không có Pillow**, tức là
> mã nguồn thật sự đã cắt được phụ thuộc không khai báo chứ không phải may mắn.

---

## Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | đúng **7 file** danh sách trắng (+ biên bản review) ✅ |
| `test.png` | **đã bị xoá** ✅ |
| Quét file cấm lọt git | không có kết quả ✅ |
| `git diff dev -- configs/capture.yaml` | rỗng ✅ |
| `git diff dev -- requirements.txt` | rỗng — **không tự thêm dependency** ✅ |
| `black --check --line-length 100 src tests` | `14 files would be left unchanged` ✅ |
| `ruff check src tests` | `All checks passed!` ✅ |
| `pytest -q` (host Windows) | **52 passed in 1.39s** ✅ |
| **`pytest -q` (container ARM64 `aarch64`)** | **52 passed in 7.65s** ✅ ⭐ |
| `grep -n "subprocess\|shutil.which" tests/test_capture.py` | không kết quả ✅ |
| `git status` sau khi chạy `pytest` | không sinh file mới ✅ |

### Cổng quyết định — container ARM64

```
$ docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 sh -lc "uname -m; python -c 'import PIL'; pytest -q"
aarch64
ModuleNotFoundError: No module named 'PIL'      <- container VAN khong co Pillow
....................................................              [100%]
52 passed in 7.65s                              <- van xanh toan bo
```

Đây là bằng chứng mạnh nhất của vòng này: container **không hề được cài thêm gì**, `Pillow` vẫn vắng
mặt, nhưng toàn bộ 52 ca đều đạt. So với vòng 2 (`2 failed, 50 passed`), phụ thuộc không khai báo đã
bị loại bỏ thật sự chứ không phải bị che đi.

---

## Xác minh ba việc của vòng 3

### 1. `test.png` — ✅ đã xoá

```
$ ls test.png
>>> test.png DA BI XOA
$ git status --short --untracked-files=all | grep -Ei '\.(jpg|png|npy|onnx|env|db)$'
>>> khong co file cam
```

Không có tệp lạ mới nào thay thế. Phạm vi trở về đúng 7 tệp danh sách trắng.

### 2. `PIL` → `cv2.imread` đặt trong nhánh — ✅ đúng yêu cầu §7

Lệnh chặn của §6 **không có kết quả**:

```
$ grep -nE "^\s*(import|from) (PIL|imageio|skimage|scipy|matplotlib|torch)" src/capture/*.py
>>> khong co ket qua
$ grep -rn --include=*.py "PIL\|Pillow\|imageio\|skimage" src/
>>> KHONG con trong src/**/*.py
```

> Ghi chú kỹ thuật: lần quét đầu có vẻ "dính" ba kết quả, nhưng cả ba là **dương tính giả** —
> `src/common/config.py:16` chứa `re.com`**`pil`**`e` (khớp khi tìm không phân biệt hoa thường), và hai
> tệp `__pycache__/*.pyc` là bytecode cũ của vòng 2. Không có vi phạm thật.

Vị trí `import cv2` trong toàn bộ `src/`:

| Tệp:dòng | Cấp | Hợp lệ? |
|---|---|---|
| `src/capture/opencv_camera.py:3` | cấp module | ✅ đúng — đây là backend camera thật |
| `src/capture/mock_camera.py:92` | **bên trong nhánh `if self._source == "directory"`**, thụt 16 dấu cách | ✅ đúng ngoại lệ có kiểm soát của §7 |
| `factory.py`, `base.py` | không có ở cấp module (chỉ import backend bên trong hàm) | ✅ |

**Kiểm chứng lý do gốc của §7** — chặn `__import__("cv2")` để giả lập máy thiếu OpenCV:

```
[§7] synthetic KHI THIEU cv2 -> chay duoc, shape (8, 8, 3) | lop: CameraGiaLap
[§7] auto     KHI THIEU cv2 -> CameraGiaLap
[thieu cv2 + directory] loai: LoiCauHinh | thong bao: Cần cài đặt OpenCV để đọc ảnh từ thư mục
   nguyen nhan goc giu duoc trong __cause__: ImportError("No module named 'cv2'")
```

Chế độ `synthetic` (mặc định) **vẫn chạy được trên máy không có OpenCV** — đúng mục đích ban đầu của
quy tắc. Đây là điều kiện then chốt để phương án A hợp lệ, và nó thoả.

### 3. `except Exception` → bắt đúng loại — ✅ đã sửa, thông báo đúng địa chỉ

**Vị trí**: `src/capture/mock_camera.py:99-102`

```python
            except ImportError as e:
                raise LoiCauHinh("Cần cài đặt OpenCV để đọc ảnh từ thư mục") from e
            except cv2.error as e:
                raise LoiCamera(f"Lỗi OpenCV khi đọc ảnh {file_path}") from e
```

`except Exception` trần đã biến mất khỏi nhánh đọc ảnh. Trường hợp thiếu thư viện nay cho
**`LoiCauHinh` với thông báo chỉ thẳng nguyên nhân** ("Cần cài đặt OpenCV…") thay vì thông báo sai địa
chỉ "Không thể đọc ảnh &lt;đường dẫn&gt;" của vòng 2, và `__cause__` vẫn giữ ngoại lệ gốc. Phân loại
ngoại lệ cũng đúng ngữ nghĩa: thiếu thư viện là lỗi **cấu hình môi trường** (`LoiCauHinh`), lỗi giải mã
là lỗi **thu hình** (`LoiCamera`).

> `except Exception` duy nhất còn lại trong `src/capture/` là ở `opencv_camera.py:90` — nằm trong
> `dong()`, có `# noqa: BLE001` và ghi log cảnh báo. Đây **chính là đoạn do biên bản vòng 1 đề nghị**
> (fail-safe khi `release()` lỗi), không phải vi phạm.

---

## Kiểm hồi quy `source=directory` — không mất hành vi nào của vòng 2

Chạy độc lập, không dựa vào test của Gemini:

```
[15a] doc dung anh 1 bit-for-bit? True
[15a] doc dung anh 2 bit-for-bit? True
[15a] anh 3 quay vong ve anh 1?   True
[15a] dtype/shape: uint8 (10, 10, 3)
[15b] directory KHAC synthetic cung seed? True
[15c] thu muc rong -> LoiCauHinh: OK
[BGR] pixel doc ra: [255, 0, 0] -> giu BGR: True
[R15] mo lai cung seed cho cung khung hinh? True
[14]  loop=True synthetic: f[2]==f[0]? True
[dir loop=False] doc qua so anh -> LoiCamera: OK
```

Bổ sung hai ca **ngoài phạm vi test của Gemini** để dò hồi quy do đổi thư viện giải mã:

```
[resize]   anh JPG 40x60 -> cau hinh 15x20, shape thuc te (15, 20, 3): dung
[anh hong] tep .png khong phai anh -> LoiCamera "Không thể đọc ảnh ...": dung
```

Kết luận: việc chuyển từ `PIL.Image` sang `cv2.imread` **không làm hỏng hành vi nào**, và còn gỡ được
phép lật kênh thủ công `frame[:, :, ::-1]` của vòng 2 — `cv2.imread` trả BGR sẵn nên quy ước màu giờ
đúng **theo cấu trúc** chứ không nhờ một dòng dễ sai. Nhánh `img is None` (`mock_camera.py:95-96`) xử
lý đúng trường hợp tệp có đuôi ảnh nhưng nội dung hỏng.

---

## Đối chiếu bảng §5 — **22/22 dòng vẫn có test, không dòng nào mất** ✅

| Dòng §5 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 15a | 15b | 15c | 16 | 17 | 18 | 19 | 20 | 21 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Có test | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

26 ca mới + 26 ca `P0-01` = **52**, giữ nguyên số ca của vòng 2 — lần sửa này không xoá test nào để
"cho qua". Đã rà bằng AST toàn bộ 26 ca: không ca nào có thân rỗng.

### Đối chiếu tiêu chí §6 (bản mới, 11 mục)

| Tiêu chí | Kết luận |
|---|---|
| Mỗi dòng §5 có test, mỗi ca có assert thật | ✅ (2 ca dùng dạng "không ném ngoại lệ" đúng như cột assert của §5 — xem 🔵-2) |
| Không ca test nào gọi `subprocess` | ✅ |
| `pytest -q` xanh toàn dự án (host) | ✅ 52 passed |
| Kiểm phạm vi file trả `7` | ✅ về thực chất — **lệnh trong §6 cần sửa**, xem 🔵-1 |
| Không hardcode `1280/720/30/42` | ✅ rà tay: mọi giá trị đến từ `cfg` |
| `black` + `ruff` sạch | ✅ |
| Nạp config thật in `CameraGiaLap` | ✅ |
| **`pytest` xanh trong container ARM64** | ✅ **52 passed** ⭐ |
| Không import thư viện ngoài `requirements.txt` | ✅ lệnh grep không kết quả |
| Test không ghi file ra ngoài `tmp_path` | ✅ |
| `git status` không có file ngoài danh sách trắng | ✅ |

---

## 🔵 Góp ý (không chặn — người dùng quyết định)

### 🔵-1 — Lệnh đếm phạm vi file trong §6 trả `3`, không phải `7` (lỗi **đặc tả**, không phải mã nguồn)

`git status --short` **gộp thư mục chưa theo dõi** thành một dòng:

```
$ git status --short                          $ git status --short --untracked-files=all
?? docs/review/P1-01-capture.review.md        ?? docs/review/P1-01-capture.review.md
?? src/capture/                               ?? src/capture/__init__.py
?? tests/fixtures/                            ?? src/capture/base.py
?? tests/test_capture.py                      ?? src/capture/factory.py
-> bo docs/review: 3 dong                     ?? src/capture/mock_camera.py
                                              ?? src/capture/opencv_camera.py
                                              ?? tests/fixtures/__init__.py
                                              ?? tests/test_capture.py
                                              -> bo docs/review: 7 dong ✓
```

**Yêu cầu thực chất đã đạt** (đúng 7 tệp, không thừa). Nhưng lệnh viết trong §6 nếu chạy đúng chữ sẽ
trả `3` và gây hiểu nhầm là thiếu tệp. *Sửa đặc tả* — thêm cờ `--untracked-files=all`:

```bash
git status --short --untracked-files=all | grep -v "docs/review/" | wc -l   # phải trả 7
```

Nên sửa ngay vì lệnh này sẽ được chép lại sang mọi đặc tả `P1-02`, `P2-xx`…

### 🔵-2 — Hai ca test kiểm bằng "không ném ngoại lệ" thay vì `assert` tường minh

**Vị trí**: `tests/test_capture.py:124-130` (`test_09`) và `tests/test_capture.py:172-179` (`test_14`)

Cả hai **đúng y cột "Assert tối thiểu" của §5** (dòng 9: "`cam.dong(); cam.dong()` không lỗi"; dòng 14:
"Đọc `N+2` lần không ném ngoại lệ"), nên **không tính lỗi** — Gemini làm đúng đặc tả. Chúng cũng thật
sự bắt được hồi quy: nếu `dong()` ném lỗi thì ca test đỏ.

*Đề xuất rẻ*: thêm một dòng `assert` nêu rõ ý định, giúp người đọc sau biết ca test đang bảo vệ điều gì:

```python
    cam.dong()
    cam.dong()
    assert not cam.dang_mo        # test_09
```

```python
    fs = [cam.doc_frame() for _ in range(4)]
    assert np.array_equal(fs[2], fs[0])   # test_14: xác nhận THẬT SỰ quay vòng
```

Riêng `test_14` sẽ mạnh hơn hẳn: hiện nó chỉ kiểm "không lỗi", trong khi hành vi quay vòng đã được cài
đúng (tôi đã đo `f[2] == f[0]` là `True`) — nên khẳng định này chắc chắn xanh và sẽ khoá được hành vi đó.

### 🔵-3 — `except cv2.error` sinh `UnboundLocalError` nếu `import cv2` hỏng bằng lỗi **không phải** `ImportError`

**Vị trí**: `src/capture/mock_camera.py:91-102`

```python
            try:
                import cv2
                ...
            except ImportError as e:
                raise LoiCauHinh("Cần cài đặt OpenCV để đọc ảnh từ thư mục") from e
            except cv2.error as e:                    # <- danh 'cv2' la bien CUC BO cua ham
```

Python phải **định trị biểu thức `cv2.error`** để so khớp mệnh đề `except`. Nếu `import cv2` thất bại
bằng một ngoại lệ không phải `ImportError` thì `cv2` chưa được gán, và lỗi gốc bị thay bằng một lỗi
khác hẳn. Đã dựng lại được:

```
[import cv2 loi OSError] loai: UnboundLocalError
   thong bao: cannot access local variable 'cv2' where it is not associated with a value
```

**Vì sao chỉ là góp ý**: đường dẫn này rất hẹp. Các kiểu hỏng thực tế của OpenCV trên Linux/Pi
(`libGL.so.1`, `libopenblas.so.0` thiếu) đều ném `ImportError` và **đã được bắt đúng** — tôi đã kiểm.
Không tiêu chí §6 nào, không dòng §5 nào bị ảnh hưởng; container xanh; không liên quan an toàn phần
cứng hay trung thực số liệu. *Chi phí sửa*: 2 dòng, đưa import ra ngoài khối `try` đọc ảnh:

```python
            try:
                import cv2
            except Exception as e:   # ImportError, OSError khi thiếu thư viện hệ thống…
                raise LoiCauHinh("Cần cài đặt OpenCV để đọc ảnh từ thư mục") from e

            try:
                img = cv2.imread(file_path)
                ...
            except cv2.error as e:
                raise LoiCamera(f"Lỗi OpenCV khi đọc ảnh {file_path}") from e
```

Đề nghị gộp vào mã việc `P1-02` thay vì mở thêm một vòng bàn giao cho hai dòng.

---

## Tổng kết ba vòng — `P1-01-capture`

| | Vòng 1 | Vòng 2 | Vòng 3 |
|---|---|---|---|
| Phán quyết | 🔴 TRẢ LẠI | 🔴 TRẢ LẠI | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** |
| 🔴 CHẶN-A | 0 | 1 | **0** |
| 🔴 CHẶN-B | 3 | 1 | **0** |
| 🟡 CẦN SỬA | 4 | 1 | **0** |
| 🔵 GÓP Ý | 4 | 2 | 3 |
| `pytest` host | 47 passed | 52 passed | **52 passed** |
| `pytest` container ARM64 | 1 failed, 46 passed | 2 failed, 50 passed | **52 passed** ⭐ |
| Dòng §5 có test | 20/21 | 22/22 | **22/22** |

### Ba bài học rút ra cho các mã việc sau

**1. Cổng container bắt được lớp lỗi mà host không bao giờ bắt được.**
Cả ba vòng, host và container cho kết quả **khác nhau** ở hai vòng đầu: vòng 1 host xanh 47/47 nhưng
container đỏ vì thiếu `git`; vòng 2 host xanh 52/52 nhưng container đỏ vì thiếu `Pillow`. Nếu chỉ chạy
trên máy phát triển thì cả hai lỗi đã lọt vào `dev`, và lỗi thứ hai sẽ chỉ phát tác khi triển khai lên
Pi 5 — đúng lúc không còn thời gian. **Kiến nghị: đưa lệnh container thành cổng bắt buộc của mọi mã
việc từ `P1-02` trở đi**, không phải tuỳ chọn.

**2. Lỗi nguy hiểm nhất là lỗi không báo lỗi.**
Lỗi nặng nhất của cả ba vòng — `mock.source = "directory"` kiểm tra thư mục tồn tại rồi **phớt lờ và
trả về ảnh nhiễu ngẫu nhiên** (vòng 1) — không làm đỏ một ca test nào, không làm sập gì cả. Nó chỉ lộ
ra khi so bit-for-bit khung hình của chế độ `directory` với chế độ `synthetic` cùng seed. Cùng loại đó:
thông báo "Không thể đọc ảnh &lt;đường dẫn&gt;" trong khi nguyên nhân thật là thiếu thư viện (vòng 2).
**Kiến nghị: với mọi mã việc sinh dữ liệu, luôn có ít nhất một ca test đối chứng dạng "hai chế độ khác
nhau phải cho kết quả khác nhau"** — chính dòng 15b đã bắt đúng lỗi này.

**3. Vòng lặp thất bại thứ hai là lỗi đặc tả, không phải lỗi người viết mã.**
Vòng 2 bế tắc vì ba ràng buộc khoá lẫn nhau: §5 đòi đọc tệp ảnh thật, §7 cấm `import cv2` ngoài
`opencv_camera.py`, §2 không cho sửa `requirements.txt` — **không tồn tại cách cài đặt hợp lệ**.
Sửa một dòng trong §7 (ngoại lệ có kiểm soát) là đủ để vòng 3 xong gọn. Điều đáng ghi nhận về phía
cài đặt: Gemini sửa **đúng 7/7 lỗi vòng 1 và 2/2 lỗi vòng 2**, không lần nào hiểu sai lặp lại, không
lần nào sinh lỗi mới ở chỗ khác — tức mã việc không quá to. **Kiến nghị: khi vòng 2 vẫn đỏ, đọc lại
đặc tả trước khi đổ cho công cụ sinh mã.**

*(Ba bài học trên dùng được cho `docs/nhat-ky/tuan-04.md` và cho phần bàn về quy trình phát triển
trong Chương 3 của báo cáo.)*

---

## Việc tiếp theo

Mã việc **đủ điều kiện commit** (R40: đã có biên bản review với phán quyết đạt). Ba mục 🔵 ở trên
không chặn — đề nghị gộp 🔵-2 và 🔵-3 vào `P1-02`, còn 🔵-1 giao `spec-writer` sửa mẫu lệnh §6.

Commit message đề nghị theo R29:

```
feat(capture): khoi thu hinh KHOI 1a voi backend mock va opencv — P1-01-capture
```

Phần thân commit đề nghị ghi kèm để giữ chuỗi truy vết đặc tả → nhánh → review → commit:

```
Cai dat lop truu tuong hoa phan cung cho khoi thu hinh (R22):
- BoThuHinh: interface chung, context manager o lop co so
- CameraGiaLap: backend mock, nguon synthetic (tai lap theo seed, R15) va directory
- CameraOpenCV: backend camera that, fail-safe khi mat thiet bi (R24)
- tao_bo_thu_hinh: chon backend theo configs/capture.yaml; auto roi ve mock,
  opencv chi dinh ro thi bao loi chu khong am tham roi ve mock

Dac ta: docs/dac-ta/P1-01-capture.md
Review: docs/review/P1-01-capture.review.md (3 vong, phan quyet DAT CO DIEU KIEN)
Kiem thu: 52 passed tren host va trong container ARM64
```

Sau khi commit: gộp vào `dev`, rồi chuyển sang mã việc `P1-02` (`scripts/collect_faces.py`).
