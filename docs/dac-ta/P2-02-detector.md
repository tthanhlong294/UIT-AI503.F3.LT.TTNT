# P2-02-detector — Khối phát hiện khuôn mặt chạy ONNX Runtime thuần

> Mã việc: `P2-02-detector` · Bước **2.3** trong `CLAUDE.md` §5 Phase 2
> Nhánh: `feat/p2-02-detector` · Đặc tả viết ngày 18/08/2026
> Phụ thuộc: `P2-01` đã gộp vào `dev` — cần `models/yolov8n-face-{320,640}.onnx`

---

## 1. Mục tiêu

Viết `src/detector/yolo_face.py` — khối phát hiện khuôn mặt đọc tệp ONNX do `P2-01` xuất ra,
trả về danh sách `FaceBox` gồm khung bao, độ tin cậy và 5 điểm mốc.

**Chỉ dùng `onnxruntime`, `numpy`, `cv2`.** Tuyệt đối không import `ultralytics` hay `torch`
trong `src/` — Raspberry Pi 5 không cài hai gói đó (`requirements.txt` chỉ pin `onnxruntime`).
Đây là khối chạy thật trên thiết bị, khác với `P2-01` là công cụ chỉ chạy trên PC.

Đầu ra của khối này nối thẳng vào `src/preprocess/align.py` đã có: thứ tự 5 điểm mốc **trùng
khớp** `reference_landmarks` trong `configs/preprocess.yaml`, không cần hoán vị.

---

## 2. Phạm vi file — danh sách trắng

| File | Trạng thái | Vai trò |
|---|---|---|
| `src/detector/__init__.py` | tạo mới | Khai báo gói |
| `src/detector/yolo_face.py` | tạo mới | Khối phát hiện |
| `tests/test_yolo_face.py` | tạo mới | Bộ kiểm thử |

**Không sửa**: `configs/**`, `src/common/**`, `src/preprocess/**`, `scripts/**`,
`requirements.txt`, `docs/**`, `.claude/**`.

Thấy `configs/detect.yaml` thiếu tham số → **dừng và báo**, không tự thêm key.

---

## 3. Dữ kiện đã kiểm chứng — dùng luôn, KHÔNG đoán lại

Đo ngày 18/08/2026 trên chính hai tệp ONNX trong `models/`. Đây là **tiền đề**.
Tự suy diễn lại những điều này là nguồn sai sót lớn nhất của mã việc này.

### 3.1. Hình dạng tensor

| | 320 | 640 |
|---|---|---|
| Tên đầu vào | `images` | `images` |
| Hình dạng vào | `[1, 3, 320, 320]` | `[1, 3, 640, 640]` |
| Tên đầu ra | `output0` | `output0` |
| Hình dạng ra | `[1, 20, 2100]` | `[1, 20, 8400]` |

Kích thước đầu vào **cố định cứng** trong đồ thị. Đưa ảnh sai kích thước vào sẽ ném
`onnxruntime.capi.onnxruntime_pybind11_state.InvalidArgument`.

### 3.2. Bố cục 20 kênh của `output0`

Trục giữa có 20 phần tử, thứ tự:

| Chỉ số kênh | Nội dung |
|---|---|
| 0–3 | `cx, cy, w, h` — tâm và kích thước khung, **toạ độ trong ảnh đã letterbox** |
| 4 | Độ tin cậy, đã ở thang `[0, 1]`, **không cần sigmoid** |
| 5–19 | 5 điểm mốc × 3 giá trị `(x, y, visibility)` |

Điểm mốc thứ `i` (đếm từ 0) nằm ở kênh `5 + i*3` và `6 + i*3`; kênh `7 + i*3` là visibility
(đề tài **không dùng** giá trị này).

Thứ tự 5 điểm: **mắt trái · mắt phải · mũi · khoé miệng trái · khoé miệng phải**.

### 3.3. Tiền xử lý — BẮT BUỘC dùng letterbox, không kéo giãn

Đã đo trên ảnh 1280×720 có khuôn mặt thật, đối chiếu với `ultralytics`:

| Cách làm | Khung bao thu được |
|---|---|
| `ultralytics` (chuẩn) | `[580.81, 267.02, 671.58, 382.07]` |
| **Letterbox** | `[580.81, 267.02, 671.58, 382.07]` ✅ khớp từng chữ số |
| Kéo giãn thẳng | `[575.96, 273.14, 679.60, 381.27]` ❌ lệch |

Với ảnh **vuông** thì hai cách cho kết quả như nhau — nên bộ test **bắt buộc phải có ca ảnh
không vuông**, nếu không lỗi này lọt lưới hoàn toàn và chỉ lộ ra khi cắm camera thật.

Tham số letterbox đã kiểm chứng:

- Tỉ lệ `r = min(imgsz / chieu_cao, imgsz / chieu_rong)` — **không** phóng to quá 1 thì vẫn giữ
  công thức này (mô hình nhận ảnh nhỏ hơn thì vẫn phóng lên).
- Kích thước mới: `nw = round(chieu_rong * r)`, `nh = round(chieu_cao * r)`.
- Màu nền chèn: **114** cho cả ba kênh (xám).
- Chèn **căn giữa**: `dx = (imgsz - nw) // 2`, `dy = (imgsz - nh) // 2`.
- Thứ tự kênh đưa vào mô hình: **RGB** (đảo từ BGR của OpenCV), bố cục `NCHW`,
  kiểu `float32`, chia 255 về thang `[0, 1]`.

### 3.4. Đưa toạ độ về ảnh gốc

`x_gốc = (x_letterbox - dx) / r` và `y_gốc = (y_letterbox - dy) / r`.
Áp dụng cho **cả** khung bao lẫn điểm mốc.

### 3.5. Đối chứng đã có sẵn

Trên ảnh `data/impostor/lfw_original/Aaron_Peirsol/Aaron_Peirsol_0001.jpg` với `imgsz=320`,
giải mã thô bằng `onnxruntime` cho **đúng** kết quả của `ultralytics`:

```
khung  = [82.81, 66.45, 169.56, 183.96]
conf   = 0.8564
điểm 0 = [105.36, 115.41]
```

Dùng bộ số này làm ca kiểm thử hồi quy.

---

## 4. Tham số — đọc từ `configs/detect.yaml`

| Khoá | Dùng để |
|---|---|
| `inference.conf_threshold` | Loại khung có độ tin cậy thấp hơn |
| `inference.iou_threshold` | Ngưỡng gộp khung chồng lấn (NMS) |
| `inference.max_faces` | Số khuôn mặt tối đa giữ lại |
| `inference.num_threads` | Số luồng cho `onnxruntime`; `0` = để runtime tự quyết |

Đường dẫn tệp `.onnx` **không** nằm trong config — truyền vào lúc khởi tạo, vì cùng một cấu hình
phải dùng được cho cả bản 320 lẫn 640 khi chạy ma trận benchmark ở bước 2.6.

---

## 5. Giao diện — giữ nguyên tên và kiểu

```python
class YoloFaceDetector:
    """Khối phát hiện khuôn mặt dùng YOLOv8n-face định dạng ONNX."""

    def __init__(self, duong_dan_onnx: Path | str, cfg: dict) -> None:
        """Nạp mô hình ONNX và chốt tham số suy luận.

        Args:
            duong_dan_onnx: Đường dẫn tệp .onnx.
            cfg: Toàn bộ nội dung configs/detect.yaml.

        Raises:
            LoiMoHinh: tệp không tồn tại, hoặc không nạp được bằng onnxruntime.
            LoiCauHinh: thiếu key bắt buộc trong cfg, hoặc giá trị ngoài miền hợp lệ.
        """

    @property
    def kich_thuoc_vao(self) -> int:
        """Cạnh ảnh đầu vào của mô hình, đọc từ đồ thị ONNX chứ không từ cfg."""

    def detect(self, khung_hinh: np.ndarray) -> list[FaceBox]:
        """Phát hiện mọi khuôn mặt trong một khung hình.

        Args:
            khung_hinh: Ảnh BGR, hình dạng (H, W, 3), kiểu uint8.

        Returns:
            Danh sách FaceBox sắp xếp theo độ tin cậy GIẢM DẦN, tối đa `max_faces` phần tử.
            Toạ độ đã quy về hệ của ảnh gốc và ép về kiểu int.
            Trả về danh sách RỖNG khi không thấy khuôn mặt nào — không ném ngoại lệ.

        Raises:
            ValueError: khung_hinh sai hình dạng, sai kiểu, hoặc rỗng.
        """
```

Hai hàm phụ trợ **phải tách riêng** để kiểm thử được độc lập:

```python
def letterbox(anh: np.ndarray, kich_thuoc: int) -> tuple[np.ndarray, float, int, int]:
    """Thu ảnh về hình vuông, giữ nguyên tỉ lệ, chèn nền xám.

    Returns:
        (ảnh_đã_letterbox, tỉ_lệ_r, dx, dy)
    """

def nms(khung: np.ndarray, diem_tin_cay: np.ndarray, nguong_iou: float) -> list[int]:
    """Gộp khung chồng lấn, giữ khung có độ tin cậy cao nhất.

    Args:
        khung: hình dạng (N, 4), thứ tự (x1, y1, x2, y2).
        diem_tin_cay: hình dạng (N,).

    Returns:
        Danh sách chỉ số được giữ lại, theo thứ tự độ tin cậy giảm dần.
    """
```

`FaceBox` đã có sẵn trong `src/common/types.py` — **dùng lại, không định nghĩa mới**.
Ngoại lệ dùng `LoiCauHinh` và `LoiMoHinh` từ `src/common/exceptions.py`.

---

## 6. Bảng tiêu chí nghiệm thu

Mỗi dòng là một ca test tên `test_dong<nn>` trong `tests/test_yolo_face.py`.
Cột "Assert tối thiểu" là **biểu thức chạy được**.

### 6.1. Khởi tạo

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Nạp tệp ONNX hợp lệ thành công | `YoloFaceDetector("models/yolov8n-face-320.onnx", cfg)` không ném lỗi |
| 02 | Tệp không tồn tại → `LoiMoHinh` | `pytest.raises(LoiMoHinh)` |
| 03 | Tệp tồn tại nhưng không phải ONNX → `LoiMoHinh` | Ghi vài byte rác vào `tmp_path/x.onnx`; `pytest.raises(LoiMoHinh)` |
| 04 | `kich_thuoc_vao` đọc từ đồ thị, đúng 320 | `d320.kich_thuoc_vao == 320` |
| 05 | `kich_thuoc_vao` đúng 640 với bản 640 | `d640.kich_thuoc_vao == 640` |
| 06 | Thiếu `inference.conf_threshold` → `LoiCauHinh` | `pytest.raises(LoiCauHinh, match="conf_threshold")` |
| 07 | Thiếu `inference.iou_threshold` → `LoiCauHinh` | `pytest.raises(LoiCauHinh, match="iou_threshold")` |
| 08 | Thiếu `inference.max_faces` → `LoiCauHinh` | `pytest.raises(LoiCauHinh, match="max_faces")` |
| 09 | Giá trị ngoài miền → `LoiCauHinh` | Duyệt **đích danh sáu biến thể**: `conf_threshold` nhận `-0.1`, `1.5`, `"0.5"`; `max_faces` nhận `0`, `-1`, `"10"` |
| 10 | **Mọi lỗi cấu hình là `LoiCauHinh`**, không phải `ValueError`/`TypeError` | Gom danh sách hỏng phủ đủ **bốn khoá** `conf_threshold`, `iou_threshold`, `max_faces`, `num_threads` — mỗi khoá ≥ 2 biến thể |

### 6.2. `letterbox`

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 11 | Ảnh ra luôn vuông đúng kích thước | `letterbox(np.zeros((720,1280,3),np.uint8), 320)[0].shape == (320,320,3)` |
| 12 | Ảnh **ngang** 1280×720 → `r`, `dx`, `dy` đúng | `r == pytest.approx(0.25)`, `dx == 0`, `dy == (320-180)//2 == 70` |
| 13 | Ảnh **dọc** 720×1280 → hoán đổi đúng | `r == pytest.approx(0.25)`, `dx == 70`, `dy == 0` |
| 14 | Ảnh **vuông** → không chèn viền | `dx == 0 and dy == 0` và `r == pytest.approx(320/250)` với ảnh 250×250 |
| 15 | Vùng chèn mang giá trị **114** | Ảnh 1280×720: `set(np.unique(ra[0:70, :])) == {114}` |
| 16 | Ảnh nhỏ hơn kích thước đích vẫn phóng lên | Ảnh 100×100 → `r == pytest.approx(3.2)` |
| 17 | **Giữ nguyên tỉ lệ** — vật thể không méo | Ảnh 1280×720 có ô vuông trắng 100×100; sau letterbox chiều rộng và chiều cao của ô sai lệch nhau không quá 1 px |

### 6.3. `nms`

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 18 | Hai khung trùng hoàn toàn → giữ 1 | Hai khung `(0,0,10,10)`, conf `[0.9, 0.8]`, `nguong=0.5` ⇒ `nms(...) == [0]` |
| 19 | Hai khung tách rời → giữ cả 2 | `(0,0,10,10)` và `(50,50,60,60)` ⇒ `len(nms(...)) == 2` |
| 20 | Kết quả sắp theo độ tin cậy giảm dần | conf `[0.3, 0.9, 0.6]`, ba khung tách rời ⇒ `nms(...) == [1, 2, 0]` |
| 21 | Ngưỡng có tác dụng thật | Cặp khung IoU = 25/175 ≈ 0,143: `nguong=0.10` ⇒ giữ 1; `nguong=0.20` ⇒ giữ 2 |
| 22 | Mảng rỗng → danh sách rỗng, không ném lỗi | `nms(np.zeros((0,4)), np.zeros((0,)), 0.5) == []` |

### 6.4. `detect` — đối chiếu với số đã kiểm chứng

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 23 | Ảnh LFW mẫu cho **đúng** khung ở §3.5 | Với `Aaron_Peirsol_0001.jpg`, `imgsz=320`: mỗi cạnh khung sai lệch < 1 px so với `[82.81, 66.45, 169.56, 183.96]` |
| 24 | Độ tin cậy khớp §3.5 | `abs(kq[0].confidence - 0.8564) < 0.01` |
| 25 | Điểm mốc thứ nhất khớp §3.5 | `np.abs(kq[0].landmarks[0] - [105.36, 115.41]).max() < 1.0` |
| 26 | Trả về đúng **5** điểm mốc, hình dạng `(5, 2)` | `kq[0].landmarks.shape == (5, 2)` |
| 27 | **Ảnh KHÔNG vuông** cho kết quả đúng — assert **TỪNG CẠNH**, không phải tâm | Dựng đúng như §6.6 dưới đây; assert **cả bốn cạnh** lệch < **2,0 px** so với `[880.68, 368.38, 972.30, 483.01]`. ⚠️ **Không** assert tâm khung: đã đo, kéo giãn làm lệch cạnh tới 7,0 px nhưng chỉ dịch tâm 0,22–0,72 px — assert tâm với bất kỳ dung sai dùng được nào cũng **không** phân biệt được đúng/sai |
| 28 | Ảnh không có mặt → danh sách **rỗng**, không ném lỗi | Ảnh xám trơn 480×640 ⇒ `detect(...) == []` |
| 29 | Thứ tự điểm mốc đúng quy ước hình học | Trên ảnh LFW mẫu: `lm[0][0] < lm[1][0]`, `max(lm[0][1],lm[1][1]) < lm[2][1]`, `lm[2][1] < min(lm[3][1],lm[4][1])`, `lm[3][0] < lm[4][0]` |
| 30 | Sắp theo độ tin cậy giảm dần | Ảnh ghép hai khuôn mặt; `[f.confidence for f in kq] == sorted(..., reverse=True)` |
| 31 | Tôn trọng `max_faces` | Ảnh ghép 3 mặt, `max_faces=2` ⇒ `len(kq) <= 2` |
| 32 | Toạ độ nằm trong ảnh và là số nguyên | `0 <= f.x1 < f.x2 <= W`, `0 <= f.y1 < f.y2 <= H`, `isinstance(f.x1, int)` |
| 33 | Bản 640 cũng phát hiện được cùng khuôn mặt | Cùng ảnh LFW mẫu qua bản 640; tâm khung lệch so với bản 320 < 10 px |

### 6.6. Cách dựng ảnh không vuông cho dòng 27 — pin chặt, không được đổi

```python
face = cv2.imread("data/impostor/lfw_original/Aaron_Peirsol/Aaron_Peirsol_0001.jpg")  # 250×250
anh = np.full((720, 1280, 3), 128, np.uint8)
anh[300:550, 800:1050] = face
```

Số đối chứng đo ngày 18/08/2026, `imgsz=320`:

| Cách cài đặt | Khung bao | Lệch từng cạnh so với chuẩn | Lệch tâm |
|---|---|---|---|
| `ultralytics` (chuẩn) | `[880.68, 368.38, 972.30, 483.01]` | — | — |
| Letterbox đúng | ≈ chuẩn | **< 0,6 px** | < 0,6 px |
| Kéo giãn 2 hệ số | `[874.12, 371.28, 979.30, 481.56]` | **tới 7,0 px** | **0,22 / 0,72 px** |

Dung sai **2,0 px** cho từng cạnh nằm gọn giữa hai nhóm: bản đúng qua thoải mái, bản kéo giãn
đỏ chắc chắn.

### 6.5. Đầu vào sai

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 34 | Không phải mảng NumPy → `ValueError` | `pytest.raises(ValueError)` với `detect("anh.jpg")` |
| 35 | Sai số chiều → `ValueError` | `pytest.raises(ValueError)` với mảng `(480, 640)` hai chiều |
| 36 | Sai số kênh → `ValueError` | Mảng `(480, 640, 4)` |
| 37 | Sai kiểu dữ liệu → `ValueError` | Mảng `float32` thay vì `uint8` |
| 38 | Ảnh rỗng → `ValueError` | Mảng `(0, 0, 3)` |
| 39 | Ảnh hợp lệ nhỏ nhất vẫn chạy được | Ảnh `(1, 1, 3)` uint8 ⇒ không ném lỗi, trả về danh sách (rỗng cũng được) |

### 6.6. Ràng buộc triển khai

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 40 | **Không import `ultralytics` hoặc `torch`** trong `src/detector/` | Đọc mã nguồn bằng `ast`, duyệt mọi `Import`/`ImportFrom` kể cả trong thân hàm; assert không có tên nào bắt đầu bằng `ultralytics` hay `torch` |
| 41 | `num_threads = 0` để runtime tự quyết, không ném lỗi | Khởi tạo với `num_threads: 0`; assert nạp được |
| 42 | `num_threads = 2` áp đúng vào phiên | Khởi tạo với `num_threads: 2`; assert không ném lỗi và `detect` vẫn cho kết quả như dòng 23 |

---

## 7. Lệnh kiểm bắt buộc

```bash
black --line-length 100 --check src/detector tests/test_yolo_face.py
```

```bash
ruff check src/detector tests/test_yolo_face.py
```

```bash
python -m pytest tests/test_yolo_face.py -v
```

```bash
git status --short --untracked-files=all
```

Lệnh cuối phải cho thấy **đúng ba** tệp mới, không hơn.

### Quét mẫu vi phạm — cả bốn phải rỗng

```bash
grep -rn "ultralytics\|import torch" src/detector/
```

```bash
grep -n "print(" src/detector/yolo_face.py
```

```bash
grep -nE "\b(114|320|640|0\.5|0\.45|20|2100|8400)\b" src/detector/yolo_face.py
```

```bash
grep -nE "raise (ValueError|TypeError)" src/detector/yolo_face.py
```

Lệnh thứ ba bắt **số hardcode**. Ngoại lệ hợp lệ: `114` của letterbox và bố cục 20 kênh là
**đặc tính cố hữu của mô hình**, không phải tham số điều chỉnh được — đặt làm hằng số có tên
ở đầu module kèm chú thích dẫn về §3 của đặc tả này, rồi giải trình trong báo cáo.
Lệnh thứ tư: `ValueError` **được phép** cho lỗi dữ liệu đầu vào của `detect` (dòng 34–38);
giải trình từng dòng. Lỗi **cấu hình** thì phải là `LoiCauHinh`.

### Kiểm đột biến bắt buộc

| # | Phép đột biến | Ca test **phải** đỏ |
|---|---|---|
| ĐB1 | Thay `letterbox` bằng `cv2.resize` kéo giãn thẳng, giữ nguyên phần ánh xạ ngược | dòng **27** (và có thể 12, 13, 15, 17) |
| **ĐB1b** | Kéo giãn với **hai hệ số tỉ lệ riêng cho từng trục**, và ánh xạ ngược cũng theo từng trục cho **khớp** — tức một cài đặt sai nhưng *tự nhất quán* | dòng **27** |
| ĐB2 | Bỏ bước đưa toạ độ về ảnh gốc (§3.4) | dòng 23, 25, 27 |
| ĐB3 | Trong `nms`, luôn giữ mọi khung | dòng 18, 21 |
| ĐB4 | Bỏ áp `max_faces` | dòng 31 |
| ĐB5 | Đảo thứ tự kênh RGB/BGR khi tiền xử lý | dòng 23 hoặc 24 |

**ĐB1 và ĐB1b mà không làm đỏ dòng 27 là lỗi nghiêm trọng nhất của mã việc này** — nghĩa là
lỗi kéo giãn sẽ đi thẳng lên phần cứng mà không ai biết. Sửa ca test dòng 27 trước, đừng báo xong.

ĐB1b là phép quan trọng hơn: nó mô phỏng một cài đặt sai **tự nhất quán**, không lộ ra ở bất kỳ
ca test nội bộ nào của `letterbox`, chỉ lộ khi so với kết quả chuẩn trên ảnh không vuông.
Đây chính là phép đã cho 42 test xanh ở vòng 1.

Mỗi phép: sửa → chạy → ghi ca đỏ → khôi phục → đối chiếu `sha256`. Dùng `newline=""`.

---

## 8. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` 100, `ruff` sạch. Type hints và docstring tiếng Việt kiểu Google.
- **Chỉ `onnxruntime`, `numpy`, `cv2`** trong `src/detector/`. Không thêm phụ thuộc mới.
- `ultralytics` được phép dùng **trong tệp test** để đối chiếu, nhưng phải **import bên trong
  thân hàm test**, không ở mức module — nó không có trong container ARM64. Kèm
  `@pytest.mark.slow` cho ca cần nó. Xem bài học `P2-01`.
- Dùng `logging` qua `src.common.logging.lay_logger`, không `print()`.
- Đọc cấu hình qua `src.common.config.nap_cau_hinh` / `lay_gia_tri`.
- Ca test cần mô hình thật (`models/*.onnx`) phải **bỏ qua có thông báo** nếu tệp chưa có:
  `pytest.skip("chưa có models/yolov8n-face-320.onnx, chạy scripts/export_detector.py trước")`.
- Mọi ca test chạy được trên Windows; dùng `pathlib`.

---

## 9. Ngoài phạm vi — KHÔNG làm ở mã việc này

- Đo tốc độ khung hình. Đó là bước 2.5–2.6, thuộc Cổng C, cần Pi 5 thật.
- Xuất NCNN. Bước 2.2 phần còn lại, mã việc riêng.
- Xử lý mẻ nhiều ảnh. Đó là `P1-05` (`scripts/preprocess.py`).
- Bám vết khuôn mặt qua nhiều khung hình, lọc nhiễu theo thời gian. Bước 5.5.

---

## 10. Báo cáo khi xong

1. Kết quả bốn lệnh máy §7, chạy trên host **và** container ARM64.
2. Kết quả bốn lệnh `grep`, giải trình từng dòng không rỗng.
3. Kết quả **năm** phép đột biến: ca nào đỏ, `sha256` khôi phục có khớp không.
4. **Số đo thực tế** của dòng 23–25 và 27: sai lệch bao nhiêu pixel so với giá trị ở §3.5.
5. Vướng mắc: chỗ nào trong đặc tả mơ hồ, thiếu, hoặc mâu thuẫn.

**Không commit.** Để nguyên cây làm việc cho người review.
