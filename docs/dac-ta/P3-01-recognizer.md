# P3-01-recognizer — Interface nhận diện và backend ArcFace

> Mã việc: `P3-01-recognizer` · Bước **3.1 và 3.3** trong `CLAUDE.md` §5 Phase 3
> Nhánh: `feat/p3-01-recognizer` · Đặc tả viết ngày 22/08/2026
> Phụ thuộc: `P1-04` (`align.py`) và `P1-05` (`preprocess.py`) đã gộp

---

## 1. Mục tiêu

Viết `src/recognizer/` gồm interface chung cho khối nhận diện và **một** bản cài đặt dùng
MobileFaceNet định dạng ONNX.

Khối này biến ảnh khuôn mặt 112 × 112 đã căn chỉnh thành **vectơ đặc trưng 512 chiều**, và so khớp
vectơ đó với danh sách đã đăng ký để trả về danh tính.

**Không cần phần cứng.** Mô hình đã có trong `models/`, dữ liệu đã có 9 164 ảnh LFW, và toàn bộ mã
việc chạy trên máy phát triển.

---

## 2. Vì sao chỉ làm MỘT backend ở mã việc này

Đề cương yêu cầu so sánh **hai** phương án nhận diện, và đó là đóng góp khoa học chính của đồ án.
Mã việc này vẫn chỉ làm phương án B, vì:

**Thư viện `dlib` chưa cài và không có trong `requirements.txt`** (kiểm 22/08/2026). Cài `dlib` đòi
hỏi trình biên dịch C++ và CMake trên Windows, và **biên dịch từ mã nguồn trên ARM64** khi triển khai
lên Raspberry Pi 5 — một quá trình tốn thời gian, cần bộ nhớ tráo đổi, và có thể thất bại.

Gộp việc dựng môi trường `dlib` vào mã việc này sẽ khiến toàn bộ khối nhận diện bị chặn bởi một rủi
ro cài đặt không liên quan tới thiết kế. Tách ra thì phương án B chạy được ngay, và phương án A xử
lý riêng ở `P3-02` — mã việc đó **bắt đầu bằng việc thẩm định tính khả thi của cài đặt**, trước khi
viết dòng mã nào.

Interface ở §5 được thiết kế để backend thứ hai lắp vào mà không sửa gì phần đã có.

---

## 3. Phạm vi file — danh sách trắng

| File | Trạng thái | Vai trò |
|---|---|---|
| `src/recognizer/__init__.py` | tạo mới | Khai báo gói |
| `src/recognizer/base.py` | tạo mới | Interface trừu tượng dùng chung hai backend |
| `src/recognizer/arcface_backend.py` | tạo mới | Bản cài MobileFaceNet ONNX |
| `tests/test_recognizer.py` | tạo mới | Bộ kiểm thử |

**Không sửa**: `configs/**`, `src/common/**`, `src/detector/**`, `src/preprocess/**`, `scripts/**`,
`requirements.txt`, `models/**`, `docs/**`, `.claude/**`.

Thiếu tham số trong `configs/recognize.yaml` → **dừng và báo**, không tự thêm key.

---

## 4. Dữ kiện đã kiểm chứng — dùng luôn, TUYỆT ĐỐI không đoán lại

Đo ngày 22/08/2026 trên chính `models/mobilefacenet.onnx`. Chi tiết ở `models/README.md` §3.3.

### 4.1. Hình dạng tensor

| | |
|---|---|
| Tên đầu vào | `input.1`, hình dạng `[N, 3, 112, 112]`, `float32` |
| Tên đầu ra | `516`, hình dạng `[1, 512]` |

Trục đầu tiên của đầu vào là **động**, nhưng mã việc này chỉ xử lý **một ảnh mỗi lần** (`N = 1`).

### 4.2. Chuẩn hoá đầu vào — nguồn sai lầm nguy hiểm nhất

**Thứ tự kênh RGB, công thức `(x − 127,5) / 128`.**

Xác định bằng cách chạy 60 danh tính LFW qua sáu phương án, đo tách biệt giữa cặp cùng người và cặp
khác người:

| Chuẩn hoá | Cùng người | Khác người | Tách biệt |
|---|---|---|---|
| **RGB `(x − 127,5)/128`** | 0,6088 | 0,0079 | **0,6010** |
| RGB `x/255` | 0,5964 | 0,0113 | 0,5852 |
| BGR `(x − 127,5)/128` | 0,5799 | 0,0126 | 0,5673 |
| **Thô, không chuẩn hoá** | 0,9110 | 0,8754 | **0,0356** |

⚠️ **Sai chuẩn hoá KHÔNG gây lỗi.** Mô hình vẫn trả về đủ 512 số. Với ảnh thô, mọi khuôn mặt cho độ
tương đồng 0,87–0,91 với nhau — đặt ngưỡng 0,9 thì hệ thống trông vẫn chạy mà thực chất không phân
biệt được ai với ai. Đây là lý do §6.4 có nhóm ca kiểm thử riêng về năng lực phân biệt.

⚠️ **OpenCV đọc ảnh ra BGR**, nên bước đảo kênh là **bắt buộc**, không phải tuỳ chọn.

---

## 5. Giao diện — giữ nguyên tên và kiểu

```python
class BoNhanDien(ABC):
    """Interface chung cho mọi backend nhận diện."""

    @property
    @abstractmethod
    def so_chieu(self) -> int:
        """Số chiều vectơ đặc trưng, đọc từ mô hình chứ không từ cấu hình."""

    @abstractmethod
    def trich_dac_trung(self, anh: np.ndarray) -> np.ndarray:
        """Trích vectơ đặc trưng từ MỘT ảnh khuôn mặt đã căn chỉnh.

        Args:
            anh: Ảnh BGR uint8, hình dạng (112, 112, 3).

        Returns:
            Vectơ đặc trưng hình dạng (so_chieu,), kiểu float32,
            **đã chuẩn hoá L2** — độ dài bằng 1.

        Raises:
            ValueError: ảnh sai hình dạng, sai kiểu, hoặc rỗng.
        """

    @abstractmethod
    def enroll(self, danh_sach_anh: list[np.ndarray], cfg: dict) -> np.ndarray:
        """Đăng ký một người từ nhiều ảnh.

        Chuẩn hoá L2 TỪNG vectơ trước, rồi lấy trung bình, rồi chuẩn hoá L2 lần nữa.
        Không chuẩn hoá trước khi trung bình thì ảnh có vectơ dài sẽ lấn át phần còn lại,
        trong khi độ dài không mang thông tin về danh tính.

        Raises:
            ValueError: danh sách rỗng, hoặc ít hơn `enroll.min_images_per_user`.
        """

    @abstractmethod
    def identify(
        self, anh: np.ndarray, gallery: dict[str, np.ndarray], nguong: float
    ) -> tuple[str | None, float]:
        """So khớp một khuôn mặt với danh sách đã đăng ký.

        Returns:
            (mã_người_dùng, độ_tương_đồng). Trả về (None, độ_tương_đồng_cao_nhất)
            khi không ai vượt ngưỡng — người lạ.
            Với gallery rỗng, trả về (None, 0.0).
        """


def do_tuong_dong(a: np.ndarray, b: np.ndarray) -> float:
    """Độ tương đồng cosin giữa hai vectơ.

    Raises:
        ValueError: hai vectơ khác số chiều, hoặc có vectơ độ dài bằng 0.
    """


def chuan_bi_dau_vao(anh: np.ndarray, cfg: dict) -> np.ndarray:
    """Chuyển ảnh BGR uint8 thành tensor đầu vào của mô hình.

    Thực hiện: đảo kênh theo `channel_order`, đổi sang float32,
    áp `(x − mean) / scale`, chuyển bố cục HWC sang NCHW.

    Returns:
        Mảng hình dạng (1, 3, H, W), kiểu float32.

    Raises:
        ValueError: ảnh sai hình dạng hoặc sai kiểu.
        LoiCauHinh: thiếu key hoặc giá trị ngoài miền hợp lệ.
    """


class ArcFaceBackend(BoNhanDien):
    def __init__(self, cfg: dict) -> None:
        """Nạp mô hình ONNX và chốt tham số.

        Raises:
            LoiMoHinh: không tìm thấy hoặc không nạp được mô hình.
            LoiCauHinh: thiếu key bắt buộc, hoặc `embedding_dim` trong cấu hình
                không khớp số chiều thật đọc từ đồ thị ONNX.
        """
```

Tách `chuan_bi_dau_vao` thành hàm riêng là bắt buộc: nó cho phép kiểm **trực tiếp** thứ tự kênh và
công thức chuẩn hoá bằng mảng nhỏ, thay vì suy đoán gián tiếp qua embedding.

---

## 6. Bảng tiêu chí nghiệm thu

Mỗi dòng là một ca test tên `test_dong<nn>` trong `tests/test_recognizer.py`.

### 6.1. Cấu hình và khởi tạo

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Nạp cấu hình hợp lệ thành công | `ArcFaceBackend(cfg)` không ném lỗi |
| 02 | `so_chieu` đọc từ đồ thị ONNX, bằng 512 | `b.so_chieu == 512` |
| 03 | Tệp mô hình không tồn tại → `LoiMoHinh` | `pytest.raises(LoiMoHinh)` |
| 04 | Tệp không phải ONNX → `LoiMoHinh` | Byte rác trong `tmp_path/x.onnx` |
| 05 | `embedding_dim` cấu hình lệch số chiều thật → `LoiCauHinh` | Đặt `embedding_dim: 128`; thông báo phải nêu **cả hai** số |
| 06 | Thiếu key bắt buộc → `LoiCauHinh` | Duyệt **đích danh năm key**: `model_path`, `embedding_dim`, `input_size`, `channel_order`, `mean`, `scale` |
| 07 | Giá trị ngoài miền → `LoiCauHinh` | Duyệt đích danh: `channel_order: "xyz"`, `scale: 0`, `scale: -1`, `mean: "abc"`, `input_size: [112]` |
| 08 | **Mọi lỗi cấu hình là `LoiCauHinh`** | Bộ cấu hình hỏng phủ đủ sáu key, mỗi key ≥ 2 biến thể; không ca nào ném `ValueError`/`TypeError` |

### 6.2. `chuan_bi_dau_vao` — kiểm trực tiếp chuẩn hoá

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 09 | Hình dạng ra đúng `(1, 3, 112, 112)` | `chuan_bi_dau_vao(anh, cfg).shape == (1, 3, 112, 112)` |
| 10 | Kiểu ra là `float32` | `.dtype == np.float32` |
| 11 | **Đảo kênh BGR sang RGB** | Ảnh mọi điểm bằng `[10, 20, 30]` (BGR). Kênh 0 của kết quả phải ứng với giá trị **30**, kênh 2 ứng với **10**. ⚠️ Đây là ca chặn lỗi thứ tự kênh — embedding **không** phân biệt được lỗi này |
| 12 | **Công thức `(x − 127,5)/128` đúng** | Cùng ảnh trên: kênh 0 phải bằng `pytest.approx((30 − 127.5)/128)` |
| 13 | **Tham số thật sự được dùng** | Cùng ảnh, đổi `scale` từ 128 sang 64 ⇒ giá trị ra gấp đôi. Bảo đảm `mean`/`scale` không bị viết cứng |
| 14 | `channel_order: bgr` thì **không** đảo | Cùng ảnh, kênh 0 phải ứng với 10 |
| 15 | Ảnh sai hình dạng → `ValueError` | Mảng `(112, 112)` hai chiều |
| 16 | Ảnh sai kiểu → `ValueError` | Mảng `float32` thay vì `uint8` |

### 6.3. `trich_dac_trung` và `do_tuong_dong`

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 17 | Hình dạng ra `(512,)`, kiểu `float32` | Cả hai |
| 18 | **Vectơ đã chuẩn hoá L2** | `abs(np.linalg.norm(e) - 1.0) < 1e-5` |
| 19 | Cùng một ảnh cho cùng một vectơ | Gọi hai lần; `np.allclose(e1, e2)` |
| 20 | Ảnh sai hình dạng → `ValueError` | Mảng `(64, 64, 3)` |
| 21 | Ảnh rỗng → `ValueError` | Mảng `(0, 0, 3)` |
| 22 | `do_tuong_dong` của vectơ với chính nó bằng 1 | `pytest.approx(1.0, abs=1e-6)` |
| 23 | Hai vectơ vuông góc cho 0 | `[1,0]` và `[0,1]` ⇒ `pytest.approx(0.0, abs=1e-6)` |
| 24 | Hai vectơ ngược hướng cho −1 | `[1,0]` và `[-1,0]` ⇒ `pytest.approx(-1.0, abs=1e-6)` |
| 25 | Khác số chiều → `ValueError` | Vectơ 512 và vectơ 128 |
| 26 | Vectơ độ dài 0 → `ValueError`, **không** chia cho 0 | `np.zeros(512)` |

### 6.4. Năng lực phân biệt trên dữ liệu thật — nhóm quan trọng nhất

Dùng ảnh trong `data/processed/lfw_original/`. Nếu thư mục chưa có, `pytest.skip` với thông báo
nhắc chạy `scripts/preprocess.py` trước.

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 27 | **Cùng người giống nhau hơn khác người** | Lấy ≥ 10 danh tính có ≥ 2 ảnh. `mean(cùng_người) > 0.40` **và** `mean(khác_người) < 0.20` **và** hiệu hai giá trị `> 0.30`. Mốc đo được ở §4.2: 0,6088 / 0,0079 / 0,6010 |
| 28 | Ảnh của cùng người luôn xếp trên | Với mỗi danh tính có ≥ 2 ảnh, ảnh cùng người phải có độ tương đồng cao hơn **mọi** ảnh khác người trong mẫu; assert tỉ lệ đạt `> 0.90` |

> ⚠️ Dòng 27 **không** phân biệt được RGB với BGR (0,6010 so với 0,5673 — quá gần). Việc đó do dòng
> 11 đảm nhiệm. Hai dòng bảo vệ hai lỗi khác nhau, cần cả hai.

### 6.5. `enroll` và `identify`

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 29 | Vectơ đăng ký đã chuẩn hoá L2 | `abs(norm(v) - 1.0) < 1e-5` |
| 30 | **Chuẩn hoá TỪNG vectơ trước khi trung bình** | Dựng hai vectơ giả cùng hướng nhưng độ dài 1 và 100; kết quả phải nằm đúng giữa theo góc, không bị vectơ dài kéo lệch |
| 31 | Danh sách rỗng → `ValueError` | `pytest.raises(ValueError)` |
| 32 | Ít hơn `min_images_per_user` → `ValueError` nêu cả hai số | Thông báo chứa số có và số cần |
| 33 | Đủ số ảnh → thành công | Cặp đối chứng của dòng 32 |
| 34 | `identify` trả đúng người khi vượt ngưỡng | Gallery hai người, đưa ảnh của người thứ nhất, ngưỡng thấp ⇒ trả mã người thứ nhất |
| 35 | Không ai vượt ngưỡng → `(None, điểm_cao_nhất)` | Ngưỡng 0,99; assert phần tử đầu là `None` và phần tử sau **không** phải 0 |
| 36 | Gallery rỗng → `(None, 0.0)`, không ném lỗi | Cả hai |
| 37 | **Ngưỡng thật sự được dùng** | Cùng ảnh, cùng gallery: ngưỡng 0,3 ⇒ trả ra mã người; ngưỡng 0,95 ⇒ trả `None` |
| 38 | Chọn người có điểm **cao nhất**, không phải người đầu danh sách | Gallery ba người, người đúng đặt ở vị trí cuối |

---

## 7. Lệnh kiểm bắt buộc

```bash
black --line-length 100 --check src/recognizer tests/test_recognizer.py
```

```bash
ruff check src/recognizer tests/test_recognizer.py
```

```bash
python -m pytest tests/test_recognizer.py -v
```

```bash
git status --short --untracked-files=all
```

Lệnh cuối: **đúng bốn** tệp mới. Ba tệp `.docx` trong `docs/bao-cao-tuan/` là của sinh viên — bỏ qua.

### Quét mẫu vi phạm — cả bốn phải rỗng

```bash
grep -rn "dlib\|import torch\|ultralytics" src/recognizer/
```

```bash
grep -nE "\b(127\.5|128|512|112)\b" src/recognizer/arcface_backend.py
```

```bash
grep -n "except Exception" src/recognizer/
```

```bash
grep -n "print(" src/recognizer/
```

Lệnh hai bắt số viết cứng: bốn giá trị đó **phải** đến từ `configs/recognize.yaml`. Ngoại lệ hợp lệ
duy nhất là hằng số có tên cho số chiều tensor NCHW; giải trình từng dòng.

### Kiểm đột biến bắt buộc

| # | Phép đột biến | Ca test **phải** đỏ |
|---|---|---|
| ĐB1 | Bỏ bước đảo kênh trong `chuan_bi_dau_vao` | dòng **11** |
| ĐB2 | Bỏ chuẩn hoá, đưa thẳng ảnh thô 0–255 vào mô hình | dòng **12** và dòng **27** |
| ĐB3 | Bỏ chuẩn hoá L2 ở `trich_dac_trung` | dòng 18 |
| ĐB4 | Trong `enroll`, trung bình trước rồi mới chuẩn hoá | dòng 30 |
| ĐB5 | Viết cứng `mean=127.5`, `scale=128` thay vì đọc cấu hình | dòng 13 |
| ĐB6 | `identify` trả người đầu tiên vượt ngưỡng thay vì người điểm cao nhất | dòng 38 |
| ĐB7 | Bỏ so `embedding_dim` với số chiều thật | dòng 05 |

**ĐB2 là phép quan trọng nhất.** Nó mô phỏng đúng lỗi đã đo được ở §4.2 — lỗi khiến mọi khuôn mặt
giống nhau 0,87–0,91 mà không báo gì. Nếu dòng 27 không đỏ thì ca test đó chưa đủ chặt.

Mỗi phép: sửa → chạy → ghi ca đỏ → khôi phục → đối chiếu `sha256`. Dùng `newline=""`.

---

## 8. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` 100, `ruff` sạch. Type hints, docstring tiếng Việt kiểu Google.
- Chỉ `numpy`, `cv2`, `onnxruntime` và `src/**`. **Không** `dlib`, **không** `torch`,
  **không** `ultralytics`. Không thêm phụ thuộc vào `requirements.txt`.
- Dùng `logging` qua `src.common.logging.lay_logger`, không `print()`.
- Đọc cấu hình qua `src.common.config.nap_cau_hinh` / `lay_gia_tri`.
- Ngoại lệ: `LoiCauHinh` cho lỗi cấu hình, `LoiMoHinh` cho lỗi mô hình, `ValueError` cho lỗi dữ liệu
  đầu vào của một lần gọi.
- ⚠️ **Container ARM64 không có** `models/`, `data/`, `.git/`, nhị phân `git`, và các gói
  `ultralytics`/`torch`/`onnx`. Mọi ca test chạm tới chúng phải `pytest.skip` **có thông báo nêu rõ
  thiếu gì**. Trong container, `pytest tests/test_recognizer.py -v` phải **không có `error`,
  không có `failed`** — chỉ `passed` và `skipped`.

---

## 9. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Backend dlib** — mã việc `P3-02`, xem §2.
- **Script đăng ký** `scripts/enroll.py` — bước 3.4, mã việc riêng.
- **Quét ngưỡng, vẽ ROC, đo FAR** — bước 3.5 và 3.7, thuộc Cổng C.
- **Chốt giá trị ngưỡng** — phải đến từ số đo, `configs/recognize.yaml` đang để `TBD`.
- Đo tốc độ khối nhận diện — cần Raspberry Pi 5.

---

## 10. Báo cáo khi xong

1. Kết quả bốn lệnh máy §7, trên host **và** container ARM64.
2. Kết quả bốn lệnh `grep`, giải trình từng dòng không rỗng.
3. Kết quả **bảy** phép đột biến, kèm `sha256` khôi phục.
4. **Số đo thực tế của dòng 27** trên dữ liệu LFW: trung bình cùng người, trung bình khác người,
   và hiệu hai giá trị. Đối chiếu với mốc ở §4.2 (0,6088 / 0,0079 / 0,6010) — lệch nhiều nghĩa là
   có gì đó sai trong chuỗi xử lý.
5. Vướng mắc.

**Không commit.** Để nguyên cây làm việc cho người review.
