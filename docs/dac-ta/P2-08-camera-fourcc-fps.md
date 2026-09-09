# P2-08 — Đặt FOURCC/FPS cho camera thật và phơi ra thông số webcam thực sự cho

| | |
|---|---|
| **Phase** | 2 — Phát hiện khuôn mặt |
| **Bước CLAUDE.md** | §5 Phase 2, hệ quả của bước 2.5 (đo FPS từ camera thật) |
| **Nhánh** | `feat/p2-08-camera-fourcc-fps` |
| **Phụ thuộc** | `P2-07` đã gộp `dev` (`1c0bf57`, gộp bởi `7d83b4e`); đầu `dev` khi viết đặc tả: `b33cb97` |
| **Ước lượng** | 2 tệp mã (`src/capture/opencv_camera.py` sửa, `tests/test_capture.py` chỉ thêm) + 1 tệp cấu hình **đã do người viết đặc tả sửa sẵn** · ~120 dòng mã sản phẩm, ~450 dòng test |

---

## 1. Mục tiêu

`CameraOpenCV` phải **đặt được** định dạng khung hình (FOURCC) và tốc độ khung mà cấu hình yêu cầu,
đúng thứ tự mà driver V4L2 chấp nhận, và **phơi ra bên ngoài** thông số webcam **thực sự** trả về để
việc bị từ chối im lặng không còn lọt qua mà không ai biết.

---

## 2. DANH SÁCH TRẮNG — chỉ được tạo/sửa các tệp sau

| Tệp | Thao tác |
|---|---|
| `src/capture/opencv_camera.py` | **sửa** — thêm mã, không đổi chữ ký ba phương thức đã có |
| `tests/test_capture.py` | **sửa — CHỈ THÊM**, không xoá và không sửa một ký tự nào của 26 ca cũ |

**Tệp đã được sửa sẵn, bạn KHÔNG được chạm:**

| Tệp | Ai sửa | Tình trạng |
|---|---|---|
| `configs/capture.yaml` | người viết đặc tả (vùng ghi của `spec-writer`, CLAUDE.md §2.9) | **đã thêm khoá `opencv.fourcc: MJPG`** và chú thích; xong rồi, đừng đụng vào |

**Cấm chạm tuyệt đối** (nằm ngoài danh sách trắng): `src/capture/base.py`, `src/capture/factory.py`,
`src/capture/mock_camera.py`, `src/capture/__init__.py`, `scripts/benchmark_detect.py`,
`scripts/collect_faces.py`, `tests/test_benchmark_detect.py`, `requirements.txt`.
Sửa bất kỳ tệp nào trong danh sách này = lỗi CHẶN-A khi review.

---

## 3. Dữ kiện đã kiểm — 09/09/2026

### 3.1. Số đo bước 2.5 trên Pi 5 thật, ba lượt, `--n-frames 300`, NCNN 320 px, 4 luồng

| Lượt | `fps_tb` | `fps_tong_tb` | `lay_khung_p50` | `latency_p50` (suy luận) | `ti_le_phat_hien` |
|---|---|---|---|---|---|
| 1 — sáng đủ, có người | 51,18 | 10,02 | 80,2 ms | 19,7 ms | 100,00 % |
| 2 — sáng yếu, có người | 51,86 | 10,02 | 80,1 ms | 19,7 ms | 100,00 % |
| 3 — sáng đủ, không người | 51,87 | 10,02 | 80,4 ms | 19,4 ms | 15,67 % |

Nguồn: `results/bench_detect_camera_20260909_{2119,2120,2123}.csv`. Nhiệt 42,2 → 43,9 °C,
`throttled=0x0`.

⚠️ **Trạng thái nhiệt**: ba lượt trên chạy ở 42–44 °C, tức máy **mát**, xa mốc 65,55 °C của bước 2.7.
Các con số này dùng để bắt sai lệch **hàng lần**, không dùng để phán xét chênh lệch vài phần trăm.

Điều đáng chú ý: `lay_khung_p50 ≈ 80 ms` **giống nhau ở cả ba lượt**, kể cả lượt sáng yếu. Đó không
phải hiện tượng phơi sáng — đó là một **trần cứng** ≈ 12,5 khung/s.

### 3.2. `v4l2-ctl --list-formats-ext` trên chính webcam đó

| Định dạng | Tốc độ khung khả dụng ở 1280×720 |
|---|---|
| `YUYV` — OpenCV lấy **mặc định** khi không đặt FOURCC | **10 · 5 · 1 fps** |
| `MJPG` | **30 · 25 · 24 · 20 · 15 · 10 · 5 fps** |
| `NV12` | 30 · 25 · 24 · 20 · 15 · 10 · 5 fps |

Ở 640×480 thì `YUYV` cũng có 30 fps — tức tập tốc độ khung hợp lệ phụ thuộc **cả định dạng lẫn độ
phân giải**. Dữ kiện này là lý do §4.1 chốt thứ tự các lời gọi `set`.

Kết luận: webcam **không hỗ trợ** 720p 30 fps ở YUYV. `lay_khung_p50 ≈ 80 ms` khớp với trần 10 fps
của YUYV (100 ms trừ phần chồng lấn với suy luận).

### 3.3. Trạng thái mã hiện tại — đã đọc, không suy đoán

`src/capture/opencv_camera.py` có 102 dòng. Trong `mo()` (dòng 39–60):

| Dữ kiện | Vị trí |
|---|---|
| Chỉ đặt `CAP_PROP_FRAME_WIDTH` và `CAP_PROP_FRAME_HEIGHT` | `:47-48` |
| **Không** gọi `CAP_PROP_FOURCC`, **không** gọi `CAP_PROP_FPS` | toàn tệp |
| Vòng warmup đọc `self._warmup_frames` khung, cảnh báo khi `ret` sai | `:51-54` |
| Toàn bộ thân `mo()` nằm trong `try ... except cv2.error` → `LoiCamera` | `:41-57` |
| `dong()` có **một** dòng `except Exception ... # noqa: BLE001` (đã có từ `P1-01`) | `:90` |
| Kiểm khoá bắt buộc `device_index`, `width`, `height` trong `__init__` | `:23-28` |
| `warmup_frames` và `max_retry` lấy bằng `cfg.get(...)` có mặc định | `:33-34` |

⇒ Khoá `opencv.fps: 30` trong cấu hình là **giá trị khai báo chưa bao giờ được áp**. `P2-07` §3.4 đã
ghi nhận điều này bằng cách đọc mã; §3.1 nay là số đo xác nhận.

### 3.4. ⚠️⚠️ Bẫy lớn nhất của mã việc này: ca test cũ `test_02` cấm ba chuỗi ký tự

`tests/test_capture.py:27-39` quét **mọi tệp `.py` trong `src/capture/`** và khẳng định:

```python
assert "1280" not in content
assert "720" not in content
assert "30" not in content
```

Đây là phép kiểm **chuỗi con trên toàn văn bản tệp**, không phải kiểm số hạng. Nghĩa là:

- Viết `self._fps = self.cfg.get("fps", 30)` ⇒ **đỏ**.
- Viết trong docstring hay comment câu "MJPG cho phép 30 fps" ⇒ **đỏ**.
- Viết bất kỳ literal nào **chứa** chuỗi con `30`, `720`, `1280`: `300`, `130`, `0.30`, `1.30`, `4320` ⇒ **đỏ**.

`test_02` là ca cũ, thuộc chốt chịu lực §6 — **cấm sửa nó**. Bạn phải viết mã sao cho không có ba
chuỗi ấy. Hệ quả trực tiếp lên thiết kế:

1. Khoá `fps` **không có giá trị mặc định trong mã**. Cấu hình không có `fps` ⇒ **không gọi**
   `set(CAP_PROP_FPS)`. Nguồn sự thật duy nhất của con số 30 là `configs/capture.yaml`.
2. Hằng số dung sai, ngưỡng ký tự in được… viết bằng dạng không chứa ba chuỗi trên
   (`0x20`, `0x7E`, `0.5`, `4` đều an toàn).

### 3.5. Container `faceid:arm64` thiếu những gì

Không có: nhị phân `git`, thư mục `.git/`, `docs/`, `models/`, `data/`, `results/`, `report/`, và các
gói `ultralytics`, `torch`, `onnx`. **Không có camera.** Chỉ có `requirements.txt` cộng
`pytest`/`black`/`ruff`.

⭐ Mọi ca kiểm thử mới **phải** thay `cv2.VideoCapture` bằng lớp giả (§5.6). **Không ca nào** được mở
camera thật, mang `@pytest.mark.slow`, chạm mạng, hay đọc `models/`/`data/`/`results/`. Số ca mới phải
cộng đủ vào **cả hai** dòng host và container của §3.6.

### 3.6. Bộ kiểm thử — mốc để đối chiếu

| Nơi chạy | Lệnh | Mốc |
|---|---|---|
| `tests/test_capture.py` | đếm hàm `def test_` | **26 ca** (`test_01`…`test_21`, kể cả `test_03b`, `test_04b`, `test_15a/b/c`) |
| Host `pc_x86`, Windows | `python -m pytest -q`, **không** lọc marker | `789 passed` — mốc **cũ**, đo trên `dev` lúc gộp `P2-07` |
| Container `faceid:arm64` | `python3 -m pytest -q -m "not slow"` | `756 passed, 1 skipped, 32 deselected` — mốc **cũ**, cùng thời điểm |

⭐ Hai mốc dưới **không còn đúng chắc chắn**: `dev` đã nhận thêm commit sau khi gộp `P2-07` (đầu `dev`
hiện là `b33cb97`). Vì vậy **việc đầu tiên** của bạn là chạy hai lệnh §9.0 **trước khi sửa một dòng
nào**, ghi lại con số thu được làm mốc, rồi mới bắt đầu. Không có mốc thì con số "sau" không nói lên
điều gì.

Ghi mốc theo đúng dạng: `<số> ca thu thập trên <commit>, môi trường <pc_x86 / docker_arm64>, lệnh
<có/không lọc marker>`.

### 3.7. Cấu hình đã được sửa sẵn — bạn chỉ đọc

`configs/capture.yaml`, nhánh `opencv`, nay có **bảy** khoá:

```yaml
opencv:
  device_index: 0
  fourcc: MJPG      # ← khoá MỚI
  width: 1280
  height: 720
  fps: 30
  warmup_frames: 5
  max_retry: 3
```

Thứ tự khoá trong YAML **không** quyết định thứ tự lời gọi `set` trong mã — thứ tự đó do §4.1 chốt.

---

## 4. Ba quyết định thiết kế — chốt và lý do

### 4.1. ★ Thứ tự lời gọi `set` là phần chịu lực: FOURCC → WIDTH → HEIGHT → FPS

**Chốt**: trong `mo()`, ngay sau khi `isOpened()` trả `True`, gọi đúng bốn lệnh theo **đúng thứ tự**:

```python
self._cap.set(cv2.CAP_PROP_FOURCC, _ma_hoa_fourcc(self._fourcc))
self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
if self._fps is not None:
    self._cap.set(cv2.CAP_PROP_FPS, self._fps)
```

Lý do **không** hoán vị được, cả hai chiều:

> **FOURCC phải đứng trước width/height.** Driver V4L2 chốt định dạng khung trước, rồi mới nhận độ
> phân giải hợp lệ *trong định dạng đó*. Đặt FOURCC sau thì driver đã chốt xong ở độ phân giải cũ,
> và việc đổi định dạng hoặc **bị bỏ qua im lặng**, hoặc **reset luôn** độ phân giải vừa đặt. Cả hai
> chế độ hỏng đều không ném ngoại lệ.
>
> **FPS phải đứng sau width/height.** Bảng §3.2 cho thấy tập tốc độ khung hợp lệ phụ thuộc **cả**
> định dạng **lẫn** độ phân giải: cùng `YUYV`, 640×480 có 30 fps còn 1280×720 chỉ có 10 fps. Đặt FPS
> khi độ phân giải chưa chốt là đặt vào một tập giá trị chưa xác định.

⛔ Vì hai chiều hỏng trên **không ném ngoại lệ và không đổi bất kỳ giá trị trả về nào**, ca kiểm thử
**không được** chỉ khẳng định "có gọi `set` với `CAP_PROP_FOURCC`". Phải khẳng định vào **dãy thứ tự
các lời gọi `set`** — xem §5.6 và các dòng 21–24 của §8. Đây chính là mục "đại lượng đem assert phải
nhạy với khuyết tật cần bắt": phép đo "có gọi hay không" cho **cùng một kết quả** ở bản đúng và bản
hoán vị thứ tự; phép đo "dãy thứ tự" phân biệt được tuyệt đối.

### 4.2. ★ Tự mã hoá/giải mã FOURCC, KHÔNG dùng hàm trợ giúp của OpenCV

`cv2.VideoWriter_fourcc` là API cũ, đã bị thay bằng `cv2.VideoWriter.fourcc` ở các bản OpenCV gần đây;
repo pin `opencv-python==4.13.0.92` và **không có cách kiểm chứng sự tồn tại của nó mà không chạy thử
trên cả ba môi trường**. Một đặc tả viết "dùng A hoặc B" ở đây là đặc tả hỏng.

**Chốt**: viết hai hàm trợ giúp mức module trong `src/capture/opencv_camera.py`. Đây là **hai ràng
buộc bắt buộc**, viết thẳng ra vì thứ tự byte sai sẽ hỏng **im lặng** (`cap.set` vẫn nhận, webcam vẫn
chạy, chỉ là chạy sai định dạng):

```python
def _ma_hoa_fourcc(ma: str) -> int:
    return int.from_bytes(ma.encode("ascii"), "little")


def _giai_ma_fourcc(gia_tri: float) -> str:
    bon_byte = (int(gia_tri) & 0xFFFFFFFF).to_bytes(4, "little")
    return "".join(chr(b) if 0x20 <= b <= 0x7E else "?" for b in bon_byte)
```

Ba tính chất phải giữ, mỗi tính chất một dòng kiểm ở §8:

- **Little-endian**, đúng quy ước FOURCC: `_ma_hoa_fourcc("MJPG") == 0x47504A4D`,
  `_ma_hoa_fourcc("YUYV") == 0x56595559`.
- **Khép kín**: `_giai_ma_fourcc(_ma_hoa_fourcc(x)) == x` với mọi `x` hợp lệ.
- **Không bao giờ ném**: `cap.get(CAP_PROP_FOURCC)` có thể trả `0.0`, số âm, hay giá trị vô nghĩa
  (đặc biệt khi camera là đối tượng giả trong ca test cũ). Phép `& 0xFFFFFFFF` chặn `OverflowError`;
  byte ngoài khoảng in được thành `"?"` để chuỗi log luôn an toàn.

### 4.3. ★★ Phơi ra thông số THỰC TẾ — đây là phần quan trọng nhất, không phải phần trang trí

Nếu chỉ làm §4.1 mà bỏ phần này thì rơi vào **đúng chế độ hỏng vừa tốn ba lượt đo trên Pi 5 để phát
hiện**: `cap.set()` bị webcam từ chối im lặng, hệ thống chạy ở định dạng và tốc độ khung sai, không có
một dòng log nào báo, và cách duy nhất biết được là đem `v4l2-ctl` ra soi thủ công.

**Chốt bốn điều:**

| # | Điều chốt | Lý do |
|---|---|---|
| C1 | Độ phân giải thật đọc từ **`.shape` của một khung đã lấy về**, **cấm** dùng `cap.get(CAP_PROP_FRAME_WIDTH/HEIGHT)` | Cùng lý lẽ `P2-07` §5.4: `cap.get` trả lại **thứ driver nói**, `.shape` trả lại **thứ thật sự đến tay ứng dụng**. Hai giá trị này lệch nhau chính là chế độ hỏng cần bắt |
| C2 | FOURCC thật và FPS thật đọc bằng `cap.get(...)`, rồi **so** với giá trị yêu cầu | Không có `.shape` tương đương cho hai đại lượng này; `cap.get` là nguồn duy nhất |
| C3 | Lệch ⇒ **`logger.warning`**, mỗi mục lệch một dòng, mỗi dòng nêu **cả** giá trị yêu cầu **và** giá trị thực tế | Không nêu cả hai thì đọc log xong vẫn không biết phải sửa cấu hình thành gì |
| C4 | **Cảnh báo, KHÔNG chặn.** Không ném ngoại lệ, không đặt `dang_mo = False` | Webcam khác có tập định dạng khác (§3.2 chỉ đúng cho webcam của đồ án). Chặn cứng làm hệ thống không chạy được trên phần cứng khác — đổi một lỗi hiệu năng thành một lỗi khả dụng |

**Hình dạng của thứ phơi ra**: **một** property `thong_so_thuc_te` trả về `dict`. Chọn dict một khối
thay vì nhiều property rời vì nơi tiêu thụ đầu tiên sẽ là `.meta.json` của `benchmark_detect.py` —
một dict cập nhật thẳng vào meta bằng một lời gọi, không phải sáu.

⚠️ **Không mâu thuẫn với `benchmark_detect.py` hiện có**: script đó tự đọc `khung_mau.shape` để dựng
khoá `do_phan_giai_that` và **vẫn tiếp tục làm như vậy**. Mã việc này **không sửa** script. Khoá của
dict ở đây mang hậu tố `_thuc_te`, khác tên với `do_phan_giai_that` của script, nên khi một mã việc
sau nối hai thứ lại thì không có va chạm tên nào.

---

## 5. Thiết kế chi tiết

### 5.1. Hằng số mức module

| Tên | Giá trị | Vì sao không vào `configs/` |
|---|---|---|
| `FOURCC_MAC_DINH` | `"MJPG"` | Giá trị **dự phòng** khi cấu hình cũ thiếu khoá `fourcc`. Nguồn sự thật vẫn là `configs/capture.yaml`; hằng số này chỉ để cấu hình cũ (và các dict cấu hình dựng tay trong ca test cũ) không vỡ. Chọn `MJPG` vì đó là định dạng **duy nhất trong §3.2 cho 30 fps ở 720p**; để mặc định là `YUYV` tức là mặc định giữ nguyên đúng lỗi mà mã việc này sinh ra để sửa |
| `DUNG_SAI_FPS` | `0.5` | Dung sai của **phép so**, không phải tham số vận hành. Driver hay trả `29.97` hoặc `30.000030` cho cùng một yêu cầu; đưa vào config sẽ tạo một khoá không ai chỉnh và không ai hiểu |

### 5.2. Kiểm cấu hình trong `__init__` — cả đường lỗi lẫn đường thành công

Bổ sung sau khối kiểm ba khoá bắt buộc đã có (`:23-28`). **Không** thêm khoá bắt buộc mới.

**Khoá `fourcc`** — `self._fourcc = self.cfg.get("fourcc", FOURCC_MAC_DINH)`, rồi kiểm:

| Điều kiện | Kết quả |
|---|---|
| là `str`, dài **đúng 4**, mọi ký tự nằm trong `0x20`–`0x7E` | hợp lệ, dùng nguyên văn (phân biệt hoa thường) |
| bất kỳ điều nào ở trên sai | `raise LoiCauHinh(...)` — thông báo **phải chứa chuỗi `opencv.fourcc`** và **giá trị đã nhận** |

**Khoá `fps`** — `self._fps`:

| Điều kiện | Kết quả |
|---|---|
| khoá **vắng mặt** | `self._fps = None`; `mo()` **không gọi** `set(CAP_PROP_FPS)` |
| có mặt, là `int` hoặc `float`, **không phải `bool`**, `math.isfinite(...)` đúng, **> 0** | `self._fps = float(gia_tri)` |
| có mặt nhưng sai bất kỳ điều nào ở trên | `raise LoiCauHinh(...)` — thông báo **phải chứa chuỗi `opencv.fps`** |

⚠️ `bool` là lớp con của `int` trong Python: `fps: true` sẽ lọt qua `isinstance(x, int)` và trở thành
`1.0`. Phải loại `bool` **tường minh**.

⚠️ `math.isfinite` là bắt buộc: `inf`, `-inf`, `nan` **lọt qua mọi phép kiểm kiểu**, và `nan > 0` trả
`False` nên `nan` vô tình bị chặn bởi phép so `> 0` — nhưng `inf > 0` là `True` và sẽ đi thẳng vào
`cap.set`. Chốt hữu hạn phải có, và §8 phủ **đích danh** cả ba giá trị.

### 5.3. `mo()` — trình tự đầy đủ

1. `cv2.VideoCapture(device_index)` — **giữ nguyên**.
2. `isOpened()` sai ⇒ `LoiCamera` — **giữ nguyên**, không đổi một ký tự nào của thông báo.
3. **Bốn lệnh `set` theo đúng thứ tự §4.1.** Giá trị trả về của `set` **bị bỏ qua**: nhiều driver trả
   `True` cả khi từ chối, nên nó không phải bằng chứng — bằng chứng là bước 6.
4. Vòng warmup `self._warmup_frames` khung — **giữ nguyên**.
5. **Đúng một lần đọc thử** (`read()`) sau vòng warmup, để lấy khung dò độ phân giải.
   - `ret` đúng và khung khác `None` ⇒ `do_phan_giai_thuc_te = (khung.shape[1], khung.shape[0])`
     (⚠️ `shape` là `(cao, rộng, kênh)` — hoán vị sai ở đây cũng hỏng im lặng khi ảnh vuông).
   - ngược lại ⇒ `do_phan_giai_thuc_te = None`, ghi `logger.warning` với thông báo bắt đầu bằng
     `"Không lấy được khung thử"`, và **không** ném ngoại lệ.
6. Dò và so ba thông số ⇒ dựng `canh_bao` (§5.4), ghi WARNING cho từng mục lệch (§5.5).
7. `self._dang_mo = True`.
8. Dòng `logger.info` cuối cùng: **mở rộng** thành ghi cả `device_index`, fourcc thực tế, độ phân giải
   thực tế và fps thực tế, dùng lazy formatting `%s`.

Toàn bộ bước 3–6 nằm **trong** khối `try ... except cv2.error` đã có: một `cv2.error` phát ra từ `set`
hay `read` vẫn phải hoá thành `LoiCamera` như hành vi hiện tại.

### 5.4. Quy tắc dựng `canh_bao` — thứ tự cố định, để khẳng định được bằng `==`

Duyệt **đúng thứ tự sau**, mỗi mục lệch thì `append` đúng một chuỗi:

| Thứ tự | Mục | Điều kiện lệch | Chuỗi thêm vào |
|---|---|---|---|
| 1 | fourcc | `fourcc_thuc_te != fourcc_yeu_cau` (so chuỗi, phân biệt hoa thường) | `"fourcc"` |
| 2 | độ phân giải | `do_phan_giai_thuc_te is not None` **và** khác `do_phan_giai_yeu_cau` | `"do_phan_giai"` |
| 2' | độ phân giải | `do_phan_giai_thuc_te is None` (bước 5 đọc thử thất bại) | `"khong_lay_duoc_khung"` |
| 3 | fps | `fps_yeu_cau is not None` **và** `abs(fps_thuc_te - fps_yeu_cau) > DUNG_SAI_FPS` | `"fps"` |

Mục 2 và 2' loại trừ nhau: không đọc được khung thì **không** thêm `"do_phan_giai"` (không có gì để so).
`fps_yeu_cau is None` ⇒ **không** so fps, **không** thêm gì.

Thứ tự cố định này là thứ cho phép §8 dòng 49 khẳng định
`canh_bao == ["fourcc", "do_phan_giai", "fps"]` bằng một phép `==` thay vì phép so tập hợp — phép so
tập hợp sẽ bỏ lọt một cài đặt sinh cảnh báo trùng lặp.

### 5.5. Thông báo WARNING — chốt nguyên văn khuôn dạng để khẳng định được

Mỗi mục lệch ghi **đúng một** bản ghi WARNING, dùng lazy formatting:

```python
logger.warning("Camera từ chối %s — yêu cầu %s, thực tế %s", ten_muc, yeu_cau, thuc_te)
```

`ten_muc` là chính chuỗi đã thêm vào `canh_bao` (`"fourcc"`, `"do_phan_giai"`, `"fps"`). Trường hợp
`"khong_lay_duoc_khung"` dùng thông báo riêng ở §5.3 bước 5, **không** dùng khuôn dạng này.

Tiền tố `"Camera từ chối"` là phần chịu lực: nó cho ca test đếm được đúng số bản ghi thuộc loại này
mà không lẫn với `"Đọc khung hình warmup thất bại"` (đã có sẵn, cũng mức WARNING).

Khớp hết ⇒ **không có** bản ghi nào chứa `"Camera từ chối"`. Đây là dòng cặp cho đường thành công,
§8 dòng 33.

### 5.6. Lớp camera giả trong `tests/test_capture.py`

Đây là công cụ đo của toàn bộ mã việc. Ngữ nghĩa của nó quyết định các ca có bắt được lỗi hay không,
nên chốt nguyên văn, **không** để tự diễn giải:

```python
_TEN_THUOC_TINH = {
    cv2.CAP_PROP_FOURCC: "FOURCC",
    cv2.CAP_PROP_FRAME_WIDTH: "FRAME_WIDTH",
    cv2.CAP_PROP_FRAME_HEIGHT: "FRAME_HEIGHT",
    cv2.CAP_PROP_FPS: "FPS",
}


class VideoCaptureGia:
    """Camera giả: ghi lại THỨ TỰ các lời gọi set() và mô phỏng việc từ chối im lặng."""

    def __init__(
        self,
        chi_so,
        *,
        tu_choi=(),                    # tên thuộc tính bị từ chối, ví dụ ("FOURCC",)
        fourcc_ban_dau="YUYV",
        fps_ban_dau=10.0,
        kich_thuoc_ban_dau=(1280, 720),   # (rộng, cao) mà get() báo cáo
        kich_thuoc_khung=None,            # (rộng, cao) mà read() thực sự trả về; None = theo get()
        mo_duoc=True,
        doc_duoc=True,
    ):
        ...
```

Hợp đồng — **mỗi dòng là một ràng buộc, sai một dòng là hỏng cả bộ ca test**:

| Phương thức | Hành vi bắt buộc |
|---|---|
| `isOpened()` | trả `self.mo_duoc` |
| `set(prop, gia_tri)` | ① `self.thu_tu_set.append(_TEN_THUOC_TINH[prop])` ② `self.gia_tri_set.append((ten, gia_tri))` ③ nếu `ten in self.tu_choi`: **không** đổi trạng thái nội bộ, trả `False` ④ ngược lại: cập nhật trạng thái nội bộ tương ứng (`FOURCC` → `_giai_ma_fourcc(gia_tri)`, `FRAME_WIDTH`/`FRAME_HEIGHT` → kích thước báo cáo, `FPS` → fps), trả `True` |
| `get(prop)` | trả **trạng thái nội bộ hiện tại**: `FOURCC` → `float(_ma_hoa_fourcc(fourcc_hien_tai))`, `FPS` → `fps_hien_tai`, `FRAME_WIDTH`/`FRAME_HEIGHT` → kích thước báo cáo |
| `read()` | `self.so_lan_read += 1`; `doc_duoc` sai ⇒ `(False, None)`; ngược lại ⇒ `(True, np.zeros((cao, rong, 3), np.uint8))` với `(rong, cao)` lấy từ `kich_thuoc_khung` nếu khác `None`, ngược lại từ kích thước báo cáo |
| `release()` | `self.da_release = True` |

⭐ **Vì sao `get()` phải trả trạng thái nội bộ chứ không phải giá trị vừa `set`**: đây là điểm khiến bộ
ca test **không tự cấp** thứ mà mã sản phẩm phải tự khai báo. Nếu mã quên gọi `set(CAP_PROP_FOURCC)`
thì `get` vẫn trả `"YUYV"` (giá trị ban đầu) ⇒ lệch ⇒ các dòng 31–33 đỏ. Một lớp giả trả về "thứ vừa
được set, hoặc MJPG nếu chưa set bao giờ" sẽ làm mọi ca xanh với mã sai.

⭐ **Vì sao cần `kich_thuoc_khung` tách khỏi `kich_thuoc_ban_dau`**: đó là cách duy nhất phân biệt một
cài đặt đọc độ phân giải từ `.shape` (đúng, C1) với một cài đặt đọc từ `cap.get` (sai, tự nhất quán,
mọi ca khác đều xanh). Xem dòng 44–45 §8 và ĐB5 §10.

Lắp vào bằng `monkeypatch.setattr(cv2, "VideoCapture", <hàm dựng trả VideoCaptureGia>)` — module sản
phẩm gọi `cv2.VideoCapture(...)` ở mức thuộc tính module nên phép vá này có hiệu lực.

---

## 6. ★ Chốt chịu lực — bốn bất biến

| # | Bất biến | Kiểm ở đâu |
|---|---|---|
| B1 | **26 ca test cũ còn nguyên**: không đổi tên, không sửa assert, không xoá | §9.2 lệnh đếm `::test_[0-9]` == 26 và lệnh liệt kê dòng bị xoá phải **rỗng** |
| B2 | **Backend `mock` không đổi hành vi một chút nào**; `CameraGiaLap` **không** có `thong_so_thuc_te` | §8 dòng 59; §9.2 lệnh `git diff --name-only` |
| B3 | `src/capture/{base,factory,mock_camera,__init__}.py` **không bị sửa** | §9.2 `git diff --name-only dev -- src/capture/` trả **đúng một** tệp |
| B4 | Chữ ký và ngữ nghĩa của `mo()`, `doc_frame()`, `dong()`, `dang_mo` giữ nguyên; đường lỗi `isOpened()` sai vẫn ném `LoiCamera` | ca cũ `test_19`, `test_20`; §8 dòng 61 |

**Phân tích tương thích ngược đã làm sẵn — bạn không phải suy lại.** Ba ca cũ dùng `MagicMock` cho đối
tượng camera (`test_03b`, `test_19`, `test_20`). Với thiết kế trên, chúng vẫn xanh:

- `test_19`, `test_20`: `isOpened()` trả `False` ⇒ ném `LoiCamera` **trước** mọi lệnh `set`. Không đổi.
- `test_03b`: `MagicMock.get(...)` trả một `MagicMock`; `int(MagicMock())` cho `1` (mock cài sẵn
  `__int__`), nên `_giai_ma_fourcc` cho `"????"` ⇒ lệch fourcc ⇒ một WARNING, **không** ngoại lệ.
  Cấu hình của ca đó **không có** khoá `fps` nên nhánh fps bị bỏ qua hoàn toàn (đây là lý do §5.2 chốt
  "vắng mặt ⇒ không so"). `read()` trả ảnh 1×1 ⇒ `do_phan_giai_thuc_te == (1, 1)`, khớp
  `width=1, height=1` ⇒ không thêm cảnh báo. Ca chỉ khẳng định giá trị điểm ảnh ⇒ vẫn xanh.

⛔ Nếu một ca cũ đỏ, **sửa mã sản phẩm, tuyệt đối không sửa ca test**. Báo cáo ngay ca nào đỏ và vì sao.

---

## 7. Giao diện — giữ nguyên tên và kiểu

```python
FOURCC_MAC_DINH: str = "MJPG"
DUNG_SAI_FPS: float = 0.5


def _ma_hoa_fourcc(ma: str) -> int:
    """Đổi chuỗi FOURCC 4 ký tự thành mã số nguyên theo thứ tự byte little-endian."""


def _giai_ma_fourcc(gia_tri: float) -> str:
    """Đổi mã FOURCC do OpenCV trả về thành chuỗi 4 ký tự; byte không in được thành '?'."""


class CameraOpenCV(BoThuHinh):
    def __init__(self, cfg: dict) -> None: ...   # chữ ký giữ nguyên
    def mo(self) -> None: ...                    # chữ ký giữ nguyên
    def doc_frame(self) -> np.ndarray: ...       # KHÔNG SỬA
    def dong(self) -> None: ...                  # KHÔNG SỬA
    @property
    def dang_mo(self) -> bool: ...               # KHÔNG SỬA

    @property
    def thong_so_thuc_te(self) -> dict:
        """Thông số yêu cầu và thông số webcam thực sự trả về. Trả BẢN SAO, không phải dict nội bộ."""
```

`thong_so_thuc_te` trả về dict có **đúng 8 khoá**, không thừa không thiếu:

| Khoá | Kiểu | Trước `mo()` | Sau `mo()` |
|---|---|---|---|
| `fourcc_yeu_cau` | `str` | giá trị cấu hình (hoặc `FOURCC_MAC_DINH`) | như trái |
| `fourcc_thuc_te` | `str \| None` | `None` | 4 ký tự giải mã từ `cap.get` |
| `fps_yeu_cau` | `float \| None` | `float(cfg["fps"])` hoặc `None` | như trái |
| `fps_thuc_te` | `float \| None` | `None` | `float(cap.get(CAP_PROP_FPS))` |
| `do_phan_giai_yeu_cau` | `tuple[int, int]` | `(width, height)` | như trái |
| `do_phan_giai_thuc_te` | `tuple[int, int] \| None` | `None` | `(rộng, cao)` từ `khung.shape` |
| `canh_bao` | `list[str]` | `[]` | theo §5.4 |
| `khop` | `bool \| None` | `None` | `len(canh_bao) == 0` |

`khop is None` **phân biệt** "chưa dò lần nào" với "đã dò và khớp" (`True`). Đây là lý do khoá này
kiểu ba trạng thái chứ không phải `bool`.

`dong()` **giữ nguyên** các giá trị đã dò — người gọi cần ghi chúng vào `.meta.json` **sau** khi đã
đóng camera. `mo()` gọi lại thì dò lại và **ghi đè**.

---

## 8. Bảng ca kiểm thử — mỗi dòng đúng MỘT điều kiện

Tên ca: `test_fourcc_dong<NN>_<mô_tả>`. Tiền tố `test_fourcc_` là bắt buộc để §9.2 đếm tách khỏi 26 ca cũ.

### Nhóm A — kiểm khoá `fourcc` trong cấu hình (đường thành công lẫn đường lỗi)

| # | Tiền đề | Assert tối thiểu |
|---|---|---|
| 01 | cfg `opencv` **không có** khoá `fourcc` | `CameraOpenCV(cfg).thong_so_thuc_te["fourcc_yeu_cau"] == "MJPG"` |
| 02 | `fourcc: "YUYV"` | `CameraOpenCV(cfg).thong_so_thuc_te["fourcc_yeu_cau"] == "YUYV"` |
| 03 | `fourcc: ""` | `pytest.raises(LoiCauHinh)` |
| 04 | `fourcc: "MJP"` (3 ký tự) | `pytest.raises(LoiCauHinh)` |
| 05 | `fourcc: "MJPGX"` (5 ký tự) | `pytest.raises(LoiCauHinh)` |
| 06 | `fourcc: 1234` (kiểu `int`) | `pytest.raises(LoiCauHinh)` |
| 07 | `fourcc: None` | `pytest.raises(LoiCauHinh)` |
| 08 | `fourcc: ["M", "J", "P", "G"]` | `pytest.raises(LoiCauHinh)` |
| 09 | `fourcc: "MJP\n"` (ký tự điều khiển) | `pytest.raises(LoiCauHinh)` |
| 10 | `fourcc: "MJPé"` (ngoài ASCII in được) | `pytest.raises(LoiCauHinh)` |
| 11 | `fourcc: "MJP "` (khoảng trắng cuối, `0x20` hợp lệ) | `CameraOpenCV(cfg).thong_so_thuc_te["fourcc_yeu_cau"] == "MJP "` |
| 12 | ca 03 | `"opencv.fourcc" in str(exc_info.value)` |

### Nhóm B — kiểm khoá `fps` trong cấu hình

| # | Tiền đề | Assert tối thiểu |
|---|---|---|
| 13 | cfg **không có** khoá `fps` | `CameraOpenCV(cfg).thong_so_thuc_te["fps_yeu_cau"] is None` |
| 14 | `fps: 30` | `CameraOpenCV(cfg).thong_so_thuc_te["fps_yeu_cau"] == 30.0` |
| 15 | `fps: 0` | `pytest.raises(LoiCauHinh)` |
| 16 | `fps: -1` | `pytest.raises(LoiCauHinh)` |
| 17 | `fps: float("inf")` | `pytest.raises(LoiCauHinh)` |
| 18 | `fps: float("-inf")` | `pytest.raises(LoiCauHinh)` |
| 19 | `fps: float("nan")` | `pytest.raises(LoiCauHinh)` |
| 20 | `fps: "abc"` | `pytest.raises(LoiCauHinh)` |
| 21 | `fps: None` | `pytest.raises(LoiCauHinh)` |
| 22 | `fps: True` (kiểu `bool`) | `pytest.raises(LoiCauHinh)` |
| 23 | ca 15 | `"opencv.fps" in str(exc_info.value)` |

### Nhóm C — ★ THỨ TỰ lời gọi `set` (§4.1)

Tiền đề chung: `VideoCaptureGia` mặc định (không từ chối gì), cfg đủ `fourcc`, `width`, `height`, `fps`.

| # | Tiền đề | Assert tối thiểu |
|---|---|---|
| 24 | cfg **có** `fps` | `cam_gia.thu_tu_set == ["FOURCC", "FRAME_WIDTH", "FRAME_HEIGHT", "FPS"]` |
| 25 | cfg **không có** `fps` | `cam_gia.thu_tu_set == ["FOURCC", "FRAME_WIDTH", "FRAME_HEIGHT"]` |
| 26 | cfg có `fps` | `cam_gia.thu_tu_set.index("FOURCC") < cam_gia.thu_tu_set.index("FRAME_WIDTH")` |
| 27 | cfg có `fps` | `cam_gia.thu_tu_set.index("FPS") > cam_gia.thu_tu_set.index("FRAME_HEIGHT")` |
| 28 | `fourcc: "MJPG"` | `int(dict(cam_gia.gia_tri_set)["FOURCC"]) == 0x47504A4D` |
| 29 | `fps: 25` | `dict(cam_gia.gia_tri_set)["FPS"] == 25.0` |
| 30 | `width: 800`, `height: 600` | `dict(cam_gia.gia_tri_set)["FRAME_WIDTH"] == 800` |

> ⚠️ Dòng 26 và 27 **trùng thông tin** với dòng 24 một cách có chủ ý: dòng 24 vỡ ngay khi có ai thêm
> một lời gọi `set` thứ năm, còn 26–27 vẫn canh đúng ràng buộc chịu lực. Giữ cả ba.

### Nhóm D — hai hàm trợ giúp FOURCC (§4.2)

| # | Tiền đề | Assert tối thiểu |
|---|---|---|
| 31 | — | `_ma_hoa_fourcc("MJPG") == 0x47504A4D` |
| 32 | — | `_ma_hoa_fourcc("YUYV") == 0x56595559` |
| 33 | — | `_giai_ma_fourcc(_ma_hoa_fourcc("MJPG")) == "MJPG"` |
| 34 | — | `_giai_ma_fourcc(_ma_hoa_fourcc("NV12")) == "NV12"` |
| 35 | — | `_giai_ma_fourcc(0) == "????"` |
| 36 | — | `_giai_ma_fourcc(-1.0) == "????"` |
| 37 | — | `_giai_ma_fourcc(float(_ma_hoa_fourcc("YUYV"))) == "YUYV"` |

### Nhóm E — ★★ dò thông số thực tế và cảnh báo (§4.3)

**Tiền đề chung của cả nhóm, áp dụng trừ khi dòng ghi khác:** cfg `opencv` có
`fourcc: "MJPG"`, `width: 1280`, `height: 720`, `warmup_frames: 0`; `VideoCaptureGia` khởi tạo với
`fourcc_ban_dau="YUYV"`, `fps_ban_dau=10.0`, `kich_thuoc_ban_dau=(1280, 720)`, `kich_thuoc_khung=None`.
Nghĩa là: **ba thông số ban đầu của webcam giả đều KHÁC thứ cấu hình yêu cầu** (trừ độ phân giải, được
đặt bằng nhau để `tu_choi` là biến duy nhất thay đổi ở các dòng 44–52). Cách bố trí này bảo đảm ca test
**không tự cấp** thứ mã sản phẩm phải tự khai báo: mã quên gọi `set` nào thì thông số đó ở nguyên giá
trị ban đầu và dòng tương ứng đỏ.

Với dòng 53, 54, 61: đặt `kich_thuoc_ban_dau=(640, 480)` để độ phân giải cũng lệch.

| # | Tiền đề | Assert tối thiểu |
|---|---|---|
| 38 | webcam tuân thủ hết, khung trả về đúng `width`×`height`, cfg có `fps` | `cam.thong_so_thuc_te["khop"] is True` |
| 39 | như 38 | `cam.thong_so_thuc_te["canh_bao"] == []` |
| 40 | như 38, `caplog.at_level(logging.WARNING)` | `sum(1 for r in caplog.records if "Camera từ chối" in r.getMessage()) == 0` |
| 41 | như 38 | `cam.thong_so_thuc_te["fourcc_thuc_te"] == "MJPG"` |
| 42 | như 38, `fps: 30` | `cam.thong_so_thuc_te["fps_thuc_te"] == 30.0` |
| 43 | như 38 | `cam.thong_so_thuc_te["do_phan_giai_thuc_te"] == (1280, 720)` |
| 44 | `tu_choi=("FOURCC",)`, `fourcc_ban_dau="YUYV"` | `cam.thong_so_thuc_te["canh_bao"] == ["fourcc"]` |
| 45 | như 44 | `cam.thong_so_thuc_te["khop"] is False` |
| 46 | như 44 | `cam.thong_so_thuc_te["fourcc_thuc_te"] == "YUYV"` |
| 47 | như 44, `caplog` | `sum(1 for r in caplog.records if "Camera từ chối" in r.getMessage()) == 1` |
| 48 | như 44, `caplog` | `"MJPG" in <bản ghi WARNING "Camera từ chối" duy nhất>.getMessage()` |
| 49 | như 44, `caplog` | `"YUYV" in <bản ghi WARNING "Camera từ chối" duy nhất>.getMessage()` |
| 50 | `tu_choi=("FPS",)`, `fps_ban_dau=10.0`, cfg `fps: 30` | `cam.thong_so_thuc_te["canh_bao"] == ["fps"]` |
| 51 | như 50 | `cam.thong_so_thuc_te["fps_thuc_te"] == 10.0` |
| 52 | `tu_choi=("FPS",)`, `fps_ban_dau=29.97`, cfg `fps: 30` (lệch < `DUNG_SAI_FPS`) | `cam.thong_so_thuc_te["canh_bao"] == []` |
| 53 | `tu_choi=("FRAME_WIDTH", "FRAME_HEIGHT")`, `kich_thuoc_ban_dau=(640, 480)`, cfg `width: 1280`, `height: 720` | `cam.thong_so_thuc_te["do_phan_giai_thuc_te"] == (640, 480)` |
| 54 | như 53 | `cam.thong_so_thuc_te["canh_bao"] == ["do_phan_giai"]` |
| 55 | ★ webcam **chấp nhận** hết (`get` báo `(1280, 720)`) nhưng `kich_thuoc_khung=(640, 480)` | `cam.thong_so_thuc_te["do_phan_giai_thuc_te"] == (640, 480)` |
| 56 | như 55 | `cam.thong_so_thuc_te["canh_bao"] == ["do_phan_giai"]` |
| 57 | `doc_duoc=False` | `cam.thong_so_thuc_te["do_phan_giai_thuc_te"] is None` |
| 58 | `doc_duoc=False` | `cam.thong_so_thuc_te["canh_bao"] == ["khong_lay_duoc_khung"]` |
| 59 | `doc_duoc=False` | `cam.dang_mo is True` (cảnh báo, không chặn — C4 §4.3) |
| 60 | `doc_duoc=False`, `caplog` | `any("Không lấy được khung thử" in r.getMessage() for r in caplog.records)` |
| 61 | `tu_choi=("FOURCC", "FRAME_WIDTH", "FRAME_HEIGHT", "FPS")`, mọi thứ lệch | `cam.thong_so_thuc_te["canh_bao"] == ["fourcc", "do_phan_giai", "fps"]` |
| 62 | cfg **không có** `fps`, webcam trả `fps_ban_dau=10.0`, mọi thứ khác khớp | `cam.thong_so_thuc_te["canh_bao"] == []` |

> Dòng 62 là dòng cặp cho §5.4 mục 3: thiếu khoá `fps` ⇒ **không so**, không cảnh báo. Thiếu nó thì
> một cài đặt so `fps` với `None` sẽ ném `TypeError` mà không ca nào bắt.

### Nhóm F — vòng đời và hình dạng dict

| # | Tiền đề | Assert tối thiểu |
|---|---|---|
| 63 | `CameraOpenCV(cfg)` chưa gọi `mo()` | `cam.thong_so_thuc_te["khop"] is None` |
| 64 | như 63 | `cam.thong_so_thuc_te["fourcc_thuc_te"] is None` |
| 65 | như 63 | `cam.thong_so_thuc_te["do_phan_giai_thuc_te"] is None` |
| 66 | như 63 | `cam.thong_so_thuc_te["canh_bao"] == []` |
| 67 | đã `mo()` rồi `dong()` | `cam.thong_so_thuc_te["fourcc_thuc_te"] == "MJPG"` (giữ nguyên sau khi đóng) |
| 68 | `mo()` với webcam A (`YUYV`, từ chối), `dong()`, rồi `mo()` với webcam B (tuân thủ) | `cam.thong_so_thuc_te["canh_bao"] == []` (dò lại, ghi đè) |
| 69 | đã `mo()` | `set(cam.thong_so_thuc_te) == {"fourcc_yeu_cau", "fourcc_thuc_te", "fps_yeu_cau", "fps_thuc_te", "do_phan_giai_yeu_cau", "do_phan_giai_thuc_te", "canh_bao", "khop"}` |
| 70 | đã `mo()`; gọi `cam.thong_so_thuc_te["canh_bao"].append("bay")` | `cam.thong_so_thuc_te["canh_bao"] == []` (trả bản sao) |
| 71 | `warmup_frames: 0` | `cam_gia.so_lan_read == 1` (đúng một lần đọc thử) |
| 72 | `warmup_frames: 2` | `cam_gia.so_lan_read == 3` (2 warmup + 1 đọc thử) |
| 73 | đã `mo()`, `caplog.at_level(logging.INFO)` | `any("MJPG" in r.getMessage() for r in caplog.records if r.levelno == logging.INFO)` |

### Nhóm G — không hồi quy (đường thành công của các hành vi cũ)

| # | Tiền đề | Assert tối thiểu |
|---|---|---|
| 74 | webcam tuân thủ, `kich_thuoc_khung=(64, 48)`, `mo()` rồi `doc_frame()` | `cam.doc_frame().shape == (48, 64, 3)` |
| 75 | như 74 | `cam.doc_frame().dtype == np.uint8` |
| 76 | `mo_duoc=False` | `pytest.raises(LoiCamera)` khi gọi `mo()` |
| 77 | `mo_duoc=False`, đã bắt `LoiCamera` | `cam_gia.thu_tu_set == []` (không `set` gì khi chưa mở được) |
| 78 | `CameraGiaLap({"width": 10, "height": 10})` | `not hasattr(cam_mock, "thong_so_thuc_te")` (chốt B2 — mock không bị sửa) |
| 79 | — | `issubclass(CameraOpenCV, BoThuHinh)` |
| 80 | `mo()` với `VideoCaptureGia`, `device_index: 0` | `cam_gia.chi_so == 0` |
| 81 | `mo()` rồi `dong()` | `cam_gia.da_release is True` |

**Tổng: 81 dòng.** Mỗi dòng **phải** có ít nhất một hàm test tương ứng. Không gộp hai dòng vào một hàm.

---

## 9. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

### 9.0. Lấy mốc TRƯỚC khi sửa bất kỳ dòng nào

```bash
python -m pytest -q
```

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

Mốc cũ để tham chiếu: `789 passed` và `756 passed, 1 skipped, 32 deselected` (§3.6). **Con số bạn thu
được chính là mốc thật** — ghi lại kèm commit đang đứng (`git rev-parse --short HEAD`) rồi mới sửa mã.

### 9.1. Sau khi cài đặt xong — định dạng và ca test của riêng khối

```bash
python -m black --check --line-length 100 src/capture/opencv_camera.py tests/test_capture.py
```

```bash
python -m ruff check src/capture/opencv_camera.py tests/test_capture.py
```

```bash
python -m pytest tests/test_capture.py -q
```

Kỳ vọng: **mọi ca xanh, 0 skipped, 0 failed**. Một ca `skipped` nghĩa là ca đó đang phụ thuộc camera
thật hay `models/` — sai §3.5, sửa ca test.

### 9.2. Chốt phạm vi và chốt chịu lực §6

```bash
python -m pytest tests/test_capture.py --collect-only -q | grep -cE "::test_[0-9]"
```

Kỳ vọng: **đúng `26`** (chốt B1). Ca mới mang tiền tố `test_fourcc_dong` nên không lọt vào phép đếm.

```bash
python -m pytest tests/test_capture.py --collect-only -q | grep -c "::test_fourcc_dong"
```

Kỳ vọng: **≥ 81** — mỗi dòng §8 ít nhất một ca.

```bash
git diff dev -- tests/test_capture.py | grep "^-[^-]"
```

Kỳ vọng: **rỗng hoàn toàn**. Tệp test chỉ được **thêm** dòng. Bất kỳ dòng nào hiện ra là vi phạm chốt
B1 — liệt kê và giải trình khi báo cáo.

```bash
git diff --name-only dev -- src/capture/
```

Kỳ vọng: **đúng một dòng** `src/capture/opencv_camera.py` (chốt B2, B3).

```bash
git status --short --untracked-files=all
```

Kỳ vọng — **đúng bốn nhóm dòng, không có nhóm thứ năm**:

| Dòng | Ai tạo ra |
|---|---|
| ` M src/capture/opencv_camera.py` | **bạn** |
| ` M tests/test_capture.py` | **bạn** |
| ` M configs/capture.yaml` | người viết đặc tả (§2) — bạn **không** được sửa thêm |
| `?? docs/dac-ta/P2-08-camera-fourcc-fps.md` và các tệp `.docx` trong `docs/bao-cao-tuan/` | có từ trước mã việc này |

Bất kỳ dòng nào khác là vi phạm phạm vi. Cờ `--untracked-files=all` là bắt buộc: thiếu nó git gộp cả
thư mục mới thành một dòng và phép đếm sai.

⚠️ Khi thêm `import cv2` và `import logging` vào đầu `tests/test_capture.py`, **chèn đúng vị trí theo
thứ tự isort** (`logging` trước `os`; `cv2` trước `numpy`) để phép chèn là thuần thêm dòng — nếu không,
`ruff`/`black` sắp lại và lệnh `git diff ... | grep "^-[^-]"` ở trên sẽ hiện dòng bị xoá, làm chốt B1
báo động giả.

### 9.3. Chạy toàn bộ, hai môi trường

```bash
python -m pytest -q
```

Kỳ vọng: `<mốc §9.0> + <số ca mới>` passed, `0 failed`, `0 skipped`. Ghi con số thật bạn thấy.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

Kỳ vọng: số `passed` tăng **đúng bằng** số ca mới trên host. Lệch nghĩa là có ca đang phụ thuộc thứ
container không có (§3.5).

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest --collect-only -q tests/test_capture.py
```

Kỳ vọng: thu thập **đủ** số ca, **không** lỗi import. Lệnh này bắt riêng chế độ hỏng "import ở mức
module một thứ container không có".

### 9.4. Quét mẫu vi phạm

```bash
grep -nE "1280|720|30" src/capture/opencv_camera.py
```

Phải **rỗng**. Đây là bản sao chính xác của ca cũ `test_02` (§3.4) — chạy riêng để bạn thấy ngay dòng
vi phạm thay vì chỉ thấy một ca đỏ.

```bash
grep -n "except Exception" src/capture/opencv_camera.py
```

Kỳ vọng: **đúng một dòng**, chính là dòng đã có sẵn trong `dong()` từ `P1-01`. Không được thêm dòng
thứ hai, cũng **không được xoá** dòng đó (xoá là sửa hành vi ngoài phạm vi).

```bash
grep -nE "raise (ValueError|TypeError|Exception)\(" src/capture/opencv_camera.py
```

Phải **rỗng** — ngoại lệ dùng lớp trong `src/common/exceptions.py`.

```bash
grep -n "get(cv2.CAP_PROP_FRAME" src/capture/opencv_camera.py
```

Phải **rỗng**. Đây là chốt C1 §4.3: độ phân giải thật chỉ đến từ `.shape` của khung, không từ
`cap.get`.

```bash
grep -nE "print\(|VideoWriter" src/capture/opencv_camera.py
```

Phải **rỗng** — R23, và §4.2 cấm dựa vào `cv2.VideoWriter_fourcc`.

```bash
grep -nE "cv2\.VideoCapture" tests/test_capture.py | grep -v "monkeypatch\|patch\|VideoCaptureGia"
```

Phải **rỗng** — không ca nào mở camera thật. Phép loại trừ ở vế sau là **cố ý**: `monkeypatch`/`patch`
chính là cách phòng thủ đúng đắn trước rủi ro này, cấm luôn cả nó thì lệnh kiểm tự phá biện pháp mạnh
nhất.

```bash
grep -n "pytest.mark.slow" tests/test_capture.py
```

Phải **rỗng** (§3.5).

---

## 10. Phép đột biến bắt buộc

Mỗi phép: sao lưu tệp **ra ngoài repo** → sửa → chạy `python -m pytest tests/test_capture.py -q` →
ghi ca đỏ → khôi phục → đối chiếu `sha256`. Tuyệt đối **không** `git checkout -- <tệp>`.

| # | Phép đột biến | Dòng §8 **phải** đỏ |
|---|---|---|
| ĐB1 | Bỏ hẳn lệnh `set(cv2.CAP_PROP_FOURCC, ...)` | 24, 26, 38, 39, 40 |
| ĐB2 | ★★ Chuyển lệnh FOURCC xuống **sau** `FRAME_HEIGHT` | 24, 26 |
| ĐB3 | ★ Chuyển lệnh FPS lên **trước** `FRAME_WIDTH` | 24, 27 |
| ĐB4 | Bỏ hẳn lệnh `set(cv2.CAP_PROP_FPS, ...)` | 24, 29, 39 |
| ĐB5 | ★★ Đọc độ phân giải bằng `cap.get(CAP_PROP_FRAME_WIDTH/HEIGHT)` thay vì `khung.shape` | 55, 56 |
| ĐB6 | Hoán vị `khung.shape[0]` và `khung.shape[1]` khi dựng `do_phan_giai_thuc_te` | 43 |
| ĐB7 | Đổi `"little"` thành `"big"` trong `_ma_hoa_fourcc` | 31, 32, 33 |
| ĐB8 | Bỏ `math.isfinite` khi kiểm `fps` | 17, 18 |
| ĐB9 | Bỏ phép loại `bool` khi kiểm `fps` | 22 |
| ĐB10 | Chấp nhận `fourcc` có độ dài khác 4 | 04, 05 |
| ĐB11 | `khop` gán cứng `True` sau khi `mo()` | 45 |
| ĐB12 | Bỏ toàn bộ `logger.warning`, chỉ ghi `logger.info` | 47 |
| ĐB13 | `thong_so_thuc_te` trả thẳng dict nội bộ, không sao chép | 70 |
| ĐB14 | `dong()` đặt lại các khoá `*_thuc_te` về `None` | 67 |
| ĐB15 | `mo()` ném `LoiCamera` khi lần đọc thử thất bại | 59 |
| ĐB16 | Bỏ lần đọc thử, lấy độ phân giải từ khung warmup cuối | 71 |
| ĐB17 | `FOURCC_MAC_DINH = "YUYV"` | 01 |
| ĐB18 | So `fps` **không** dùng dung sai (so bằng `!=`) | 52 |

★★ **ĐB2 và ĐB5 là hai phép quan trọng nhất** — cả hai đều dựng lại một cài đặt **tự nhất quán**:

- **ĐB2**: mọi lệnh `set` vẫn được gọi đủ, camera giả vẫn báo cáo đúng thứ vừa được set, `canh_bao`
  vẫn rỗng, `khop` vẫn `True`. **Chỉ dãy thứ tự phân biệt được.** Nếu ĐB2 không làm dòng 24 và 26 đỏ
  thì bộ ca test đang canh sai chỗ — sửa ca test, đừng sửa mã sản phẩm.
- **ĐB5**: độ phân giải vẫn được phơi ra, vẫn có kiểu đúng, vẫn khớp trong mọi kịch bản webcam tuân
  thủ. Chỉ kịch bản "driver nói một đằng, khung về một nẻo" (dòng 55–56) phân biệt được — mà đó chính
  là chế độ hỏng đã tốn ba lượt đo để phát hiện.

---

## 11. Ràng buộc kỹ thuật

- Python ≥ 3.11. `black --line-length 100` sạch, `ruff check` sạch. Type hints cho mọi hàm, docstring
  tiếng Việt kiểu Google.
- ⚠️ **Không có ba chuỗi con `1280`, `720`, `30` trong `src/capture/opencv_camera.py`** — kể cả trong
  comment và docstring (§3.4). Đây là ràng buộc dễ vi phạm nhất của mã việc này.
- Ngoại lệ chỉ dùng `LoiCamera` / `LoiCauHinh` từ `src/common/exceptions.py`. Không `raise ValueError`,
  không `except Exception` **mới** (dòng đã có trong `dong()` giữ nguyên).
- Log qua `src.common.logging.lay_logger`, **lazy formatting** (`logger.warning("... %s", x)`), không
  f-string trong lời gọi log. Không `print()`.
- **Không thêm phụ thuộc mới.** Chỉ dùng `cv2`, `numpy`, và thư viện chuẩn (`math` cho `isfinite`).
  Không dùng `cv2.VideoWriter_fourcc` (§4.2).
- Mọi ca test dùng `monkeypatch.setattr(cv2, "VideoCapture", ...)`; **không** mở camera thật, **không**
  chạm mạng, **không** đọc `models/`/`data/`/`results/`, **không** `@pytest.mark.slow`.
- Không tạo tệp mới trong `src/capture/` — ca cũ `test_01` khoá cứng đúng năm tệp `.py` ở đó.

---

## 12. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Sửa `scripts/benchmark_detect.py` để ghi `thong_so_thuc_te` vào `.meta.json`.** Hợp lý, và là mã
  việc riêng — ghi lại đây để không quên. Mã việc này chỉ **tạo ra** thứ để dùng.
- **Thêm `thong_so_thuc_te` cho `CameraGiaLap`.** Chốt B2 §6 cấm; backend `mock` không có webcam để dò.
- **Tự dò danh sách định dạng khả dụng** (`v4l2-ctl`, `CAP_PROP_FORMAT`, thử lần lượt nhiều FOURCC rồi
  chọn cái tốt nhất). Ý hay nhưng ngoài đề cương, và phụ thuộc V4L2 nên không chạy được trên Windows.
- **Đổi mặc định `width`/`height`, hay tự hạ độ phân giải khi webcam từ chối.** Đó là quyết định vận
  hành, phải chốt bằng số đo ở §12b trước.
- **Tách luồng thu hình khỏi luồng suy luận, frame skipping, tuỳ chỉnh `CAP_PROP_BUFFERSIZE`.** Bước 6.7.
- **Chạy §12b.** Người dùng chạy, sau khi mã đạt.
- **Cập nhật Chương 4, vẽ hình, viết notebook.** Cổng D.

---

## 12a. Kiểm rẻ TRƯỚC khi đo — nói ngay định dạng đang dùng thật

Chạy trên Pi 5, **trong lúc** hệ thống đang giữ camera (mở hai cửa sổ terminal):

```bash
python -c "import yaml,sys; sys.path.insert(0,'.'); from src.capture.factory import tao_bo_thu_hinh; cfg=yaml.safe_load(open('configs/capture.yaml')); cfg['backend']='opencv'; cam=tao_bo_thu_hinh(cfg); cam.mo(); print(cam.thong_so_thuc_te); input('Đang giữ camera, chạy v4l2-ctl ở terminal khác rồi Enter...'); cam.dong()"
```

Ở terminal thứ hai:

```bash
v4l2-ctl --device=/dev/video0 --get-fmt-video
```

Kỳ vọng: dòng `Pixel Format` ghi `'MJPG'`, `Width/Height` ghi `1280/720`. Nếu vẫn là `'YUYV'` thì
**dừng lại**, đừng đo — `thong_so_thuc_te["canh_bao"]` in ra ở terminal thứ nhất sẽ nói lệch ở đâu.

Ngoài ra, **gộp nhánh và commit trước khi đo** để `.meta.json` ghi `git_dirty: false`
(`experiment-protocol` §9). Đo trên cây làm việc bẩn thì số liệu không tái lập được.

---

## 12b. Lượt chạy thật — NGƯỜI DÙNG chạy, sau khi §9 xanh

⭐ Mục đích: có bộ số đầu-cuối **cùng điều kiện** với ba tệp `results/bench_detect_camera_20260909_*`
để so trực tiếp. Mọi yếu tố phải giữ y hệt lượt cũ.

### Điều kiện đo — cố định trong suốt phiên

| Yếu tố | Giá trị (giống hệt lượt 09/09) |
|---|---|
| Thiết bị | Raspberry Pi 5 8 GB, webcam USB |
| Mô hình | NCNN 320 px, `--threads 4` |
| Khoảng cách | **1,0 m**, theo vạch đã đánh dấu trên sàn |
| Vị trí camera | cố định, không dời giữa các lượt |
| Cỡ mẫu | `--n-frames 300` |
| Nghỉ giữa các lượt | **2 phút** |
| Trạng thái nhiệt | ghi `vcgencmd measure_temp` trước và sau **mỗi** lượt |

### Lệnh 1 — sáng đủ, có người (đối chiếu `..._2119`)

```bash
python scripts/benchmark_detect.py --nguon camera --capture-backend opencv --models models/yolov8n-face-320_ncnn_model --threads 4 --n-frames 300 --anh-sang "trong nhà, đèn LED trần, ~300 lux" --khoang-cach-m 1.0 --noi-dung-khung co-nguoi --device-name "Raspberry Pi 5 8GB" --ghi-chu "sau P2-08 (FOURCC=MJPG), lượt 1, đối chiếu bench_detect_camera_20260909_2119"
```

### Lệnh 2 — sáng yếu, có người (đối chiếu `..._2120`)

```bash
python scripts/benchmark_detect.py --nguon camera --capture-backend opencv --models models/yolov8n-face-320_ncnn_model --threads 4 --n-frames 300 --anh-sang "trong nhà ban đêm, chỉ đèn ngủ, rèm kín" --khoang-cach-m 1.0 --noi-dung-khung co-nguoi --device-name "Raspberry Pi 5 8GB" --ghi-chu "sau P2-08 (FOURCC=MJPG), lượt 2, đối chiếu bench_detect_camera_20260909_2120"
```

### Lệnh 3 — sáng đủ, không người (đối chiếu `..._2123`)

```bash
python scripts/benchmark_detect.py --nguon camera --capture-backend opencv --models models/yolov8n-face-320_ncnn_model --threads 4 --n-frames 300 --anh-sang "trong nhà, đèn LED trần, ~300 lux" --khoang-cach-m 1.0 --noi-dung-khung khong-nguoi --device-name "Raspberry Pi 5 8GB" --ghi-chu "sau P2-08 (FOURCC=MJPG), lượt 3, đối chiếu bench_detect_camera_20260909_2123"
```

### Kỳ vọng — và phép tính đằng sau, để không ai đọc nhầm

| Đại lượng | Trước (09/09) | Kỳ vọng sau | Vì sao |
|---|---|---|---|
| `lay_khung_p50` | ≈ 80 ms | **≈ 33 ms** | Trần tốc độ khung đi từ 10 fps (YUYV) lên 30 fps (MJPG); chu kỳ khung 1/30 s ≈ 33,3 ms |
| `latency_p50` (suy luận) | 19,4–19,7 ms | **không đổi đáng kể** | Suy luận không phụ thuộc định dạng thu hình. MJPG có thêm chi phí giải nén nhưng nó nằm trong `lay_khung`, không nằm trong `detect` |
| `fps_tb` | 51,2–51,9 | **không đổi đáng kể** | `fps_tb` là nghịch đảo của `latency_ms` — năng lực suy luận thuần, không phải tốc độ khung |
| `fps_tong_tb` | 10,02 | **≈ 19, dải hợp lý 19–25** | Vòng lặp **tuần tự**: 33,3 + 19,7 ≈ 53 ms ⇒ ≈ 19 fps. Kiểm chéo với số cũ: 80,2 + 19,7 = 99,9 ms ⇒ 10,01 fps, khớp `fps_tong_tb = 10,02` |
| `ti_le_phat_hien` | 100 % / 100 % / 15,67 % | **giữ nguyên bậc** | Đổi định dạng nén không được làm sập chất lượng phát hiện. Tụt mạnh ⇒ MJPG nén hỏng ảnh, phải báo cáo |

⚠️ **Đừng kỳ vọng `fps_tong_tb ≈ 25`.** Con số đó chỉ đạt được nếu `doc_frame()` trả về khung từ bộ
đệm nội bộ thay vì chờ khung mới — mà đó chính là chế độ hỏng `canh_bao_dem_khung` của `P2-07` §4.1.
Nếu `fps_tong_tb` vượt 27 **và** `lay_khung_p50` xuống dưới 20 ms thì kiểm khoá `canh_bao_dem_khung`
trong `.meta.json` trước khi mừng.

⚠️ Ba lượt cũ đo ở 42–44 °C. Giữ nguyên nếp đo (nghỉ 2 phút, ghi nhiệt) để phép so không bị lẫn với
hiệu ứng nhiệt. Chênh lệch **hàng lần** ở `lay_khung_p50` mới là thứ mã việc này muốn thấy; chênh vài
phần trăm ở `fps_tb` không kết luận gì.

### Sau khi chạy

- Commit **cả 6 tệp** (`.csv` + `.meta.json` của 3 lượt) — `results/*.csv` được git theo dõi.
- Dán `vcgencmd measure_temp` và `vcgencmd get_throttled` trước/sau phiên vào biên bản review.
- Dán nguyên văn đầu ra của §12a (dòng `Pixel Format` và dict `thong_so_thuc_te`) vào biên bản review —
  đó là bằng chứng trực tiếp rằng FOURCC đã được áp thật trên phần cứng, không phải chỉ đúng với
  camera giả.

---

## 13. Báo cáo khi xong

1. Hai con số mốc §9.0, kèm commit đang đứng, lấy **trước** khi sửa mã. Ghi theo dạng
   `<số> ca thu thập trên <commit>, môi trường <pc_x86 / docker_arm64>, lệnh <có/không lọc marker>`.
2. Kết quả **ba** lệnh §9.1 và **năm** lệnh §9.2, kèm số ca mới đếm được.
3. Kết quả **ba** lệnh §9.3 — số `passed` trên host và trong container, và độ chênh so với mốc §9.0.
4. Kết quả **bảy** lệnh `grep` §9.4, giải trình từng dòng không rỗng.
5. Kết quả **mười tám** phép đột biến §10, kèm `sha256` khôi phục. Nêu rõ **ĐB2** và **ĐB5** làm dòng
   nào đỏ — nếu một trong hai không làm ca nào đỏ thì bộ ca test chưa canh đúng chỗ, báo ngay.
6. Đối chiếu từng dòng bảng §8: dòng nào có ca test nào.
7. Chỗ nào của đặc tả bạn phải tự diễn giải, và diễn giải theo hướng nào.
8. Vướng mắc.

**Không commit.** Không chạy §12a, §12b. Để nguyên cây làm việc cho người review.
