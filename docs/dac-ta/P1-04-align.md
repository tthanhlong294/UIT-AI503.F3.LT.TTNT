# P1-04-align — Khối căn chỉnh khuôn mặt `src/preprocess/`

| | |
|---|---|
| **Phase** | 1 — Dữ liệu khuôn mặt |
| **Bước CLAUDE.md** | §5 Phase 1, bước 1.9 — phần **căn chỉnh** |
| **Nhánh** | `feat/p1-04-align` |
| **Phụ thuộc** | `P0-01-nen-tang` (dùng `LoiCauHinh`, `nap_cau_hinh`, `lay_logger`) |
| **Ước lượng** | 3 file, ~260 dòng |

---

## 1. Mục tiêu

Cài đặt **phép căn chỉnh khuôn mặt về 112×112 bằng biến đổi tương tự từ 5 điểm mốc** — phần toán thuần
tuý, không phụ thuộc mô hình phát hiện, dùng chung cho cả tiền xử lý dữ liệu lẫn suy luận thời gian thực.

> **Vì sao tách riêng khỏi `preprocess.py`**: đây là chỗ sai thì **hỏng âm thầm**. Lệch vài pixel hoặc
> sai bộ điểm chuẩn cho ra ảnh trông vẫn đúng mặt, nhưng embedding lệch hệ thống — độ chính xác tụt mà
> không có lỗi nào báo. Tách ra thì kiểm được đầy đủ bằng dữ liệu tổng hợp, không cần mô hình.

---

## 2. DANH SÁCH TRẮNG

| File | Thao tác |
|---|---|
| `src/preprocess/__init__.py` | tạo mới (để trống) |
| `src/preprocess/align.py` | tạo mới |
| `tests/test_align.py` | tạo mới |

> **Cấm chạm** mọi file khác. `configs/preprocess.yaml` **đã tồn tại**, chỉ đọc.
> Không tạo `scripts/preprocess.py` — đó là mã việc `P1-05`.

---

## 3. Interface bắt buộc

```python
import numpy as np


def kiem_diem_moc(diem_moc: np.ndarray) -> None:
    """Kiểm tính hợp lệ của mảng điểm mốc.

    Hợp lệ: mảng số thực hình dạng (5, 2), không chứa NaN hoặc vô cực.

    Raises:
        ValueError: nếu sai hình dạng, sai kiểu, hoặc chứa giá trị không hữu hạn.
    """


def uoc_luong_bien_doi(diem_moc: np.ndarray, diem_chuan: np.ndarray) -> np.ndarray:
    """Ước lượng ma trận biến đổi tương tự 2×3 đưa `diem_moc` về `diem_chuan`.

    Biến đổi tương tự gồm xoay, phóng đại đều và tịnh tiến — KHÔNG có cắt xiên
    và KHÔNG phóng đại khác nhau theo hai trục (xem §3.1).

    Raises:
        LoiCauHinh: nếu không ước lượng được (điểm suy biến, ví dụ 5 điểm trùng nhau).
    """


def can_chinh(
    anh: np.ndarray,
    diem_moc: np.ndarray,
    cfg: dict,
) -> np.ndarray:
    """Căn chỉnh khuôn mặt về kích thước chuẩn.

    Args:
        anh: Ảnh BGR, hình dạng (H, W, 3), kiểu uint8.
        diem_moc: 5 điểm mốc trên `anh`, hình dạng (5, 2), thứ tự theo §3.2.
        cfg: Toàn bộ nội dung `configs/preprocess.yaml`.

    Returns:
        Ảnh BGR đã căn chỉnh, đúng kích thước `cfg["output_size"]`, kiểu uint8.

    Raises:
        ValueError: nếu `anh` sai hình dạng hoặc sai kiểu; nếu `diem_moc` không hợp lệ.
        LoiCauHinh: nếu thiếu key bắt buộc trong `cfg`, hoặc điểm mốc suy biến.
    """
```

### 3.1. Vì sao dùng biến đổi **tương tự**, không dùng affine đầy đủ

Biến đổi affine đầy đủ có 6 bậc tự do, cho phép **cắt xiên** và **phóng đại khác nhau theo hai trục**.
Áp lên khuôn mặt, nó sẽ kéo giãn để năm điểm mốc khớp đúng tuyệt đối vào điểm chuẩn — nghĩa là **bóp
méo hình dạng thật của khuôn mặt** để bù cho tư thế.

Hệ quả: hai người có tỉ lệ khuôn mặt khác nhau sẽ bị kéo về cùng một tỉ lệ, làm mất chính đặc trưng
dùng để phân biệt họ. Với đồ án đo FAR thì đó là mất mát trực tiếp vào chỉ số quan trọng nhất.

Biến đổi tương tự chỉ có 4 bậc tự do — xoay, phóng đại **đều**, tịnh tiến — nên giữ nguyên tỉ lệ khuôn
mặt. Đây cũng là phép biến đổi mà họ mô hình ArcFace được huấn luyện cùng.

Trong OpenCV: `cv2.estimateAffinePartial2D` cho biến đổi tương tự; `cv2.estimateAffine2D` cho affine
đầy đủ. **Dùng cái thứ nhất.**

### 3.2. Thứ tự năm điểm mốc

| Chỉ số | Điểm |
|---|---|
| 0 | Mắt trái |
| 1 | Mắt phải |
| 2 | Mũi |
| 3 | Khoé miệng trái |
| 4 | Khoé miệng phải |

"Trái" và "phải" theo **góc nhìn của người xem ảnh**, không phải theo người trong ảnh. Đây là quy ước
của bộ điểm chuẩn trong `configs/preprocess.yaml` — đảo thứ tự sẽ cho ảnh lật ngược mà vẫn trông hợp lý.

---

## 4. Tham số → config

Đọc từ `configs/preprocess.yaml`. **Không hardcode giá trị nào**, kể cả toạ độ điểm chuẩn.

| Tham số | Key | Bắt buộc |
|---|---|---|
| Kích thước ra | `output_size` | có |
| Điểm chuẩn 5 mốc | `reference_landmarks` | có |
| Kiểu nội suy | `interpolation` | không, mặc định `bilinear` |
| Màu viền | `border_value` | không, mặc định `[0, 0, 0]` |

Thiếu key bắt buộc → `LoiCauHinh` nêu rõ tên key.

> ⛔ **Toạ độ điểm chuẩn tuyệt đối không được viết cứng trong mã.** Bộ số này gắn với mô hình nhận
> diện đang dùng; đổi mô hình thì phải đổi nó. Nằm trong mã thì lần đổi sau sẽ bị bỏ sót, và embedding
> lệch hệ thống mà không ai biết.

---

## 5. Hành vi & ca biên

> **Bảng này chỉ chứa ca kiểm thử pytest.** Lệnh shell nằm ở §6.
> **Không ca nào cần mô hình hay tệp ảnh thật** — dựng ảnh và điểm mốc bằng `numpy` tại chỗ.

| # | Điều kiện | Kỳ vọng | Assert tối thiểu |
|---|---|---|---|
| 1 | `kiem_diem_moc` với mảng `(5, 2)` số thực hữu hạn — **đường thành công** | không ném | Gọi xong không có ngoại lệ |
| 2 | `kiem_diem_moc` với hình dạng `(4, 2)` | raise `ValueError` | `pytest.raises(ValueError)`, thông báo chứa `(5, 2)` |
| 3 | `kiem_diem_moc` với hình dạng `(5, 3)` | raise `ValueError` | `pytest.raises(ValueError)`, thông báo chứa `(5, 2)` |
| 4 | `kiem_diem_moc` với `NaN` | raise `ValueError` | `pytest.raises(ValueError)`, thông báo nói về giá trị không hữu hạn |
| 5 | `kiem_diem_moc` với `inf` | raise `ValueError` | như dòng 4 |
| 6 | `uoc_luong_bien_doi` khi `diem_moc` **trùng đúng** `diem_chuan` | ma trận gần đơn vị | `np.allclose(M, [[1,0,0],[0,1,0]], atol=1e-6)` |
| 7 | `uoc_luong_bien_doi` với 5 điểm **trùng nhau hoàn toàn** (suy biến) | raise `LoiCauHinh` | `pytest.raises(LoiCauHinh)` **và** thông báo nói về điểm suy biến — phân biệt với `LoiCauHinh` do thiếu key config |
| 8 | Ma trận trả về có hình dạng đúng | dùng được cho `warpAffine` | `M.shape == (2, 3)` |
| 9 | **Biến đổi là tương tự, không phải affine đầy đủ** | giữ nguyên tỉ lệ khuôn mặt | Dựng điểm mốc bị **kéo giãn theo một trục** so với điểm chuẩn; ma trận thu được phải thoả `abs(hypot(M[0,0],M[0,1]) - hypot(M[1,0],M[1,1])) < 1e-6` — hai vectơ hàng cùng độ dài, tức phóng đại đều |
| 10 | `can_chinh` trả **đúng kích thước** trong config | | `kq.shape == (112, 112, 3)` khi `output_size` là `[112, 112]` |
| 11 | `can_chinh` **đọc kích thước từ config**, không viết cứng | | Đổi `output_size` thành `[64, 64]` → `kq.shape == (64, 64, 3)` |
| 12 | `can_chinh` trả về kiểu `uint8` | | `kq.dtype == np.uint8` |
| 13 | **Điểm mốc rơi đúng vị trí chuẩn TRONG ẢNH RA** | phép căn chỉnh làm đúng việc của nó, đo trên ảnh chứ không chỉ trên ma trận | Dựng ảnh nền đen, đặt **chấm sáng 255 tại đúng 5 vị trí điểm mốc**; căn chỉnh; lấy mẫu ảnh ra tại **5 toạ độ điểm chuẩn** (làm tròn) → cả 5 giá trị `>= 250` |
| 13a | Dòng 13 vẫn đúng sau khi **tịnh tiến** | dịch mặt trong khung hình không ảnh hưởng | Dịch **cả ảnh lẫn điểm mốc** đi `(+30, +20)`, lặp phép đo dòng 13 → cả 5 giá trị `>= 250` |
| 14 | Dòng 13 vẫn đúng sau khi **phóng đại** | mặt to nhỏ khác nhau cho cùng kết quả | Phóng ảnh và điểm mốc lên 2 lần, lặp phép đo dòng 13 → cả 5 giá trị `>= 250` |
| 15 | Dòng 13 vẫn đúng sau khi **xoay** | mặt nghiêng được nắn thẳng | Xoay ảnh và điểm mốc 20°, lặp phép đo dòng 13 → cả 5 giá trị `>= 250` |
| 16 | Điểm mốc **được đưa đúng về vị trí chuẩn** | phép căn chỉnh làm đúng việc của nó | Biến đổi `diem_moc` bằng ma trận `M` thu được, kết quả sai khác điểm chuẩn `< 1.0` pixel mỗi điểm |
| 17 | **Giữ nguyên thứ tự kênh BGR** | không hoán đổi màu | Ảnh vào toàn `[255, 0, 0]` (xanh lam trong BGR); vùng giữa ảnh ra vẫn có kênh 0 lớn nhất |
| 18 | `can_chinh` với ảnh **không phải 3 kênh** | raise `ValueError` | `pytest.raises(ValueError)` với ảnh `(H, W)` |
| 19 | `can_chinh` với ảnh **không phải uint8** | raise `ValueError` | `pytest.raises(ValueError)` với ảnh `float32` |
| 20 | `can_chinh` với `cfg` **thiếu** `reference_landmarks` | raise `LoiCauHinh` nêu tên key | `pytest.raises(LoiCauHinh)`, thông báo chứa `reference_landmarks` |
| 21 | `can_chinh` với `cfg` **thiếu** `output_size` | raise `LoiCauHinh` nêu tên key | `pytest.raises(LoiCauHinh)`, thông báo chứa `output_size` |
| 22 | `can_chinh` với `cfg` **đủ key** — đường thành công | chạy bình thường | Không ném, trả ảnh đúng kích thước |
| 23 | **Điểm chuẩn lấy từ config, không viết cứng** | đổi config là đổi hành vi | Đổi `reference_landmarks` sang bộ khác hẳn → ảnh ra **khác** ảnh với bộ gốc |
| 24 | Vùng nằm ngoài ảnh gốc được điền bằng `border_value` | không để rác | Mặt sát mép ảnh, góc ảnh ra bằng đúng giá trị `border_value` |
| 26 | `cfg["output_size"]` là `[0, 0]` | raise `LoiCauHinh` — **không** được trả về ảnh gốc | `pytest.raises(LoiCauHinh)`, thông báo chứa `output_size` |
| 27 | `cfg["output_size"]` chứa số âm | raise `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 28 | `cfg["reference_landmarks"]` **sai số lượng** (4 điểm thay vì 5) | raise `LoiCauHinh` nêu số điểm | `pytest.raises(LoiCauHinh)`, thông báo chứa `reference_landmarks` |
| 29 | `cfg["reference_landmarks"]` chứa giá trị **không phải số** | raise `LoiCauHinh`, **không** phải `ValueError` hay `TypeError` | `pytest.raises(LoiCauHinh)` |
| 30 | **Mọi lỗi cấu hình đều là `LoiCauHinh`** — quy ước §7, kiểm gộp | tầng gọi phân biệt được "bỏ qua ảnh" với "dừng cả mẻ" | Duyệt danh sách ≥ 6 cấu hình hỏng khác nhau, **mỗi cấu hình** phải ném `LoiCauHinh`; assert **không** cấu hình nào ném `ValueError` hoặc `TypeError` |
| 31 | **Mọi lỗi dữ liệu đầu vào đều là `ValueError`** — quy ước §7, kiểm gộp | như trên, chiều ngược lại | Duyệt danh sách ảnh/điểm mốc hỏng, **mỗi ca** phải ném `ValueError`; assert **không** ca nào ném `LoiCauHinh` |
| 25 | Nạp được **file config thật** của dự án | không lệch với `configs/preprocess.yaml` | `nap_cau_hinh("configs/preprocess.yaml")` rồi gọi `can_chinh` → trả ảnh `(112, 112, 3)` |

> **Dòng 13 là dòng chịu lực nhất, và cách đo của nó không phải ngẫu nhiên.**
>
> Phiên bản đầu của đặc tả này đo bằng **sai khác mức xám trung bình** giữa hai ảnh ra. Cách đó
> **không dùng được**, đã kiểm chứng bằng đột biến: thay phép căn chỉnh bằng cắt ảnh theo khung bao
> thì ba ca vẫn xanh (đo được 0,000 / 0,285 / 3,934 so với ngưỡng 2,0 / 3,0 / 5,0). Hai lý do:
>
> 1. **Ngưỡng mức xám phụ thuộc ảnh thử** — cùng một bản cài đặt đúng cho sai khác 0,203 với ảnh mượt
>    và 8,999 với ảnh có kết cấu. Tiêu chí phụ thuộc vào thứ đặc tả không kiểm soát.
> 2. **Bất biến với tịnh tiến và phóng đại không phân biệt được gì** — phép cắt theo khung bao *vốn đã*
>    bất biến với hai phép đó. Không ngưỡng nào cứu được.
>
> Cách đo hiện tại — **chấm sáng tại điểm mốc, lấy mẫu tại điểm chuẩn** — đo trực tiếp thứ cần đo:
> điểm mốc có rơi đúng vị trí quy định trong ảnh ra hay không. Nó **độc lập với ảnh thử** và phân biệt
> được cắt khung bao: bản đúng cho `[255]×5`, bản cắt khung bao cho `[0, 255, 255, 0, 0]`.

---

## 6. Tiêu chí nghiệm thu

- [ ] **Mỗi dòng bảng §5 có ít nhất một ca test, mỗi ca có assert thật**
- [ ] **Phép đột biến bắt buộc — thay toàn bộ phép căn chỉnh bằng cắt ảnh theo khung bao**
      (lấy vùng bao quanh 5 điểm mốc rồi `resize` về `output_size`) → **phải làm đỏ dòng 13**.
      Vẫn xanh nghĩa là bộ kiểm thử không phân biệt được căn chỉnh với cắt ảnh — lỗi CHẶN-B.
      Ghi kết quả phép này vào báo cáo bàn giao.
- [ ] `pytest -q` xanh toàn bộ — **118 ca cũ vẫn đạt**, cộng ca mới
- [ ] `pytest -q` **xanh trong container ARM64**:
      `MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q`
- [ ] `black --check --line-length 100 src tests scripts` và `ruff check src tests scripts` sạch
- [ ] **Không ca test nào cần mô hình, tệp ảnh thật, hay mạng**:
      `grep -nE "\.pt\b|\.onnx|urlopen|requests\.|models/" tests/test_align.py` không có kết quả
- [ ] **Không hardcode toạ độ điểm chuẩn**:
      `grep -nE "38\.29|51\.69|73\.53|56\.02" src/preprocess/align.py` không có kết quả
- [ ] **Kiểm phạm vi file**:
      `git status --short --untracked-files=all | grep -v "docs/review/" | wc -l` trả `3`
- [ ] **Không thư viện ngoài `requirements.txt`**:
      `grep -nE "^\s*(import|from) (PIL|imageio|skimage|scipy|pandas|torch)" src/preprocess/*.py`
      không có kết quả

---

## 7. Quy tắc áp dụng

| Mã | Vì sao |
|---|---|
| **G1** | Kích thước ra và toạ độ điểm chuẩn đọc từ config |
| **G4** | Type hints + docstring tiếng Việt |
| **G5** | Bắt đúng loại; lỗi ước lượng bọc thành `LoiCauHinh` bằng `raise ... from e` |
| **R21** | `src/preprocess/` chỉ import từ `src/common/`, **không** import `src/capture/` hay khối nào khác |

**Thư viện được phép**: `cv2`, `numpy`, và thư viện chuẩn. **Không thêm gì khác.**

**Quy ước lỗi**: dữ liệu đầu vào sai (hình dạng, kiểu, giá trị) → `ValueError`; cấu hình sai hoặc
không ước lượng được biến đổi → `LoiCauHinh`. Hai loại này **không được lẫn**, vì tầng gọi phải phân
biệt "ảnh này bỏ qua" với "cấu hình hỏng, dừng cả mẻ".

⚠️ Lẫn hai loại này gây lỗi **âm thầm và nghiêm trọng**: `P1-05` bắt `ValueError` để bỏ qua ảnh hỏng.
Nếu lỗi cấu hình cũng ném `ValueError`, cả mẻ sẽ chạy hết với **100 % ảnh bị bỏ** mà không báo gì.

Quy ước này được kiểm bằng **dòng 30 và 31** của bảng §5 — không chỉ nêu ở đây.

---

## 8. Ngoài phạm vi — KHÔNG làm

- **Phát hiện khuôn mặt** — khối này nhận điểm mốc từ bên ngoài, không tự tìm mặt
- `scripts/preprocess.py`, duyệt thư mục, ghi ảnh ra đĩa, manifest → mã việc `P1-05`
- Kiểm chất lượng ảnh (loại ảnh mờ, ảnh không có mặt) → bước 1.10
- Hiệu chỉnh miền dữ liệu → bước 1.8
- Căn chỉnh bằng nhiều hơn 5 điểm mốc, hoặc bằng mô hình 3D
- Phương án dự phòng khi **không có** điểm mốc (cắt theo khung bao). Cố ý không làm: ảnh không có
  điểm mốc phải bị **bỏ qua và đếm lại**, không được đưa vào tập bằng một phép căn chỉnh kém chất
  lượng — số ảnh bị loại là số liệu phải báo cáo ở Chương 4
- Sửa `configs/preprocess.yaml`
