# P3-02-dlib-backend — Phương án A: nhận diện bằng dlib

> Mã việc: `P3-02-dlib-backend` · Bước **3.2** trong `CLAUDE.md` §5 Phase 3
> Nhánh: `feat/p3-02-dlib-backend` · Đặc tả viết ngày 04/09/2026
> Tiền đề: `P3-01` đã gộp — `src/recognizer/base.py` định nghĩa hợp đồng `BoNhanDien`

---

## 1. Mục tiêu

Cài đặt **phương án A** của khối nhận diện danh tính, dùng mô hình ResNet của thư viện dlib, sau
đúng giao diện `BoNhanDien` mà phương án B (ArcFace) đang tuân theo.

Vì sao đây là mã việc quan trọng nhất còn lại của Phase 3: đề tài đặt trọng tâm ở **so sánh định
lượng hai phương án nhận diện** — đó là đóng góp khoa học chính, và là mục dài nhất của Chương 4.
Hiện mới có một nửa. Không có phương án A thì không có bảng so sánh, và mục quan trọng nhất của báo
cáo không tồn tại.

Toàn bộ mã việc này **không cần camera và không cần Raspberry Pi 5**: kiểm thử chạy trên ảnh LFW đã
tải sẵn.

---

## 2. Phạm vi file — danh sách trắng

| File | Trạng thái | Vai trò |
|---|---|---|
| `src/recognizer/dlib_backend.py` | tạo mới | Backend phương án A |
| `src/recognizer/__init__.py` | sửa | Xuất tên mới |
| `tests/test_dlib_backend.py` | tạo mới | Bộ kiểm thử |
| `requirements.txt` | sửa — **thêm đúng một dòng** | `dlib-bin==20.0.1` |

**Không sửa**: `src/recognizer/base.py`, `src/recognizer/arcface_backend.py`, `configs/**`,
`scripts/**`, `models/**`. Không thêm gói nào khác.

⚠️ `requirements.txt` đổi ⟹ **phải dựng lại image `faceid:arm64`** (R43). Lệnh dựng thuộc lượt của
người dùng ở §11b.

> Vì sao `dlib-bin` vào `requirements.txt` chứ không phải `requirements-dev.txt`: khi Cổng C của
> Phase 3 chạy trên Raspberry Pi 5, script đo phải chạy được **cả hai** phương án trên chính thiết
> bị đó. Gói này nằm ở phía thiết bị, không phải phía máy phát triển.

---

## 3. Dữ kiện — đã kiểm ngày 04/09/2026

| Dữ kiện | Giá trị | Nguồn |
|---|---|---|
| Gói `dlib` gốc | **chỉ phát hành mã nguồn** `.tar.gz`, phải biên dịch trên mọi nền tảng | `pip download dlib` |
| Gói `dlib-bin`, Windows | `dlib_bin-20.0.1-cp312-cp312-win_amd64.whl` | `pip download dlib-bin` |
| Gói `dlib-bin`, ARM64 | `dlib_bin-20.0.1-cp311-cp311-manylinux_2_27_aarch64.manylinux_2_28_aarch64.whl` | `pip download` trong `faceid:arm64` |
| Trọng số nhận diện | `models/dlib/dlib_face_recognition_resnet_model_v1.dat`, 22,5 MB | `models/README.md` A3 |
| Bộ dò điểm mốc | `models/dlib/shape_predictor_68_face_landmarks.dat`, 99,7 MB | `models/README.md` A2 |
| Số chiều vectơ đặc trưng | **128** | `configs/recognize.yaml` |
| Ảnh đầu vào của pipeline | BGR uint8, 112 × 112, đã căn chỉnh theo 5 điểm mốc | `configs/preprocess.yaml` |

Wheel ARM64 là `cp311`, khớp Python 3.11 của cả `faceid:arm64` lẫn Raspberry Pi OS Bookworm. Nghĩa
là phương án A **triển khai được lên thiết bị đích mà không phải biên dịch** — điều mà `P3-01` §2 để
ngỏ như một rủi ro, nay đã loại bỏ.

---

## 4. Tham số — đọc từ `configs/recognize.yaml`, mục `dlib`

| Khoá | Ý nghĩa |
|---|---|
| `dlib.model_path` | Trọng số mô hình nhận diện |
| `dlib.shape_predictor` | Bộ dò 68 điểm mốc |
| `dlib.embedding_dim` | Số chiều kỳ vọng — **dùng để kiểm chéo**, không dùng để định hình mảng |
| `dlib.num_jitters` | Số lần lấy mẫu nhiễu, hiện đặt 0 |
| `enroll.min_images_per_user` | Số ảnh tối thiểu để đăng ký |

`configs/recognize.yaml` **đã được cập nhật** cho mã việc này — không sửa thêm. Thấy thiếu tham số →
dừng và báo (R16).

`embedding_dim` phải được đối chiếu với số chiều thật mà mô hình trả về, và **lệch thì ném lỗi** —
cùng cách `arcface_backend.py` đối chiếu `input_size` với đồ thị ONNX. Cấu hình nói một đằng mô hình
làm một nẻo là loại lỗi không có triệu chứng nào ngoài độ chính xác thấp bất thường.

---

## 5. Giao diện

```python
class DlibFaceRecognizer(BoNhanDien):
    """Khối nhận diện danh tính dùng mô hình ResNet của dlib — phương án A."""

    def __init__(self, cfg: dict) -> None:
        """Nạp hai mô hình dlib và chốt tham số.

        Args:
            cfg: Toàn bộ nội dung configs/recognize.yaml.

        Raises:
            LoiMoHinh: chưa cài gói `dlib`, tệp trọng số không tồn tại, hoặc không nạp được.
            LoiCauHinh: thiếu khoá bắt buộc, hoặc giá trị ngoài miền hợp lệ.
        """

    @property
    def so_chieu(self) -> int:
        """Số chiều vectơ đặc trưng, ĐỌC TỪ MÔ HÌNH chứ không từ cấu hình."""
```

Ba phương thức còn lại — `trich_dac_trung`, `enroll`, `identify` — giữ **nguyên hợp đồng** đã khai
trong `src/recognizer/base.py`, kể cả loại ngoại lệ và hành vi ở ca biên. Hai backend phải thay thế
được cho nhau ở mọi chỗ gọi.

---

## 6. Thiết kế bắt buộc

### 6.1. Tiền xử lý: để dlib tự căn chỉnh, không tự làm thay

Pipeline đưa vào ảnh BGR 112 × 112 đã căn chỉnh theo 5 điểm mốc. dlib thì có quy ước căn chỉnh
riêng: mô hình của nó chờ ảnh đã căn theo **68 điểm mốc** và đưa về 150 × 150.

**Cách làm bắt buộc**: đổi BGR sang RGB, chạy bộ dò 68 điểm mốc trên toàn bộ khung ảnh 112 × 112,
rồi truyền cả ảnh lẫn kết quả dò cho hàm trích đặc trưng của dlib. dlib sẽ tự căn chỉnh nội bộ theo
quy ước của nó.

**Cấm** tự phóng ảnh lên 150 × 150 rồi truyền thẳng. Cách đó bỏ qua bước căn chỉnh mà mô hình dlib
được huấn luyện cùng, và hậu quả là vectơ đặc trưng lệch có hệ thống — mô hình vẫn trả về đủ 128 số,
không có lỗi nào được ném ra, chỉ có độ chính xác thấp mà không rõ nguyên nhân. Đây đúng chế độ hỏng
mà `P3-01` đã gặp với chuẩn hoá đầu vào của ArcFace, ghi ở `models/README.md` §3.3.

Đổi kênh màu là **bắt buộc**: OpenCV đọc ảnh ra BGR, dlib chờ RGB.

### 6.2. Khác biệt tiền xử lý giữa hai phương án là đặc tính, không phải sai lệch

ArcFace nhận ảnh 112 × 112 chuẩn hoá `(x − 127,5) / 128`; dlib nhận ảnh RGB rồi tự căn chỉnh theo 68
điểm mốc. Hai đường tiền xử lý khác nhau vì hai mô hình được huấn luyện khác nhau.

Điều này **phải được nêu trong Chương 4** khi trình bày bảng so sánh: hai phương án nhận cùng một
ảnh đầu vào từ pipeline, nhưng mỗi phương án áp quy ước tiền xử lý của riêng nó. Đó là cách so sánh
đúng — ép cả hai dùng chung một quy ước sẽ làm hỏng ít nhất một trong hai.

### 6.3. Không có khuôn mặt trong ảnh thì sao

Bộ dò điểm mốc chạy trên **toàn bộ khung ảnh** đã căn chỉnh, không dò lại vị trí khuôn mặt — ảnh vào
đây vốn đã là ảnh khuôn mặt do khối phát hiện cắt ra. Vì vậy nó luôn trả về 68 điểm, kể cả với ảnh
không phải khuôn mặt.

Đây là hành vi **chấp nhận được và đúng thiết kế**: việc quyết định "có phải khuôn mặt không" thuộc
khối phát hiện, không thuộc khối nhận diện. Không thêm phép kiểm nào ở đây.

### 6.4. Import `dlib` chỉ trong thân hàm

Cùng ràng buộc đã áp cho `ncnn` ở `P2-05` §6.2: một dòng `import dlib` ở mức module làm `pytest`
chết ngay khâu thu thập trên máy chưa cài gói, kéo đổ toàn bộ bộ kiểm thử của cả repo.

Thiếu gói → `LoiMoHinh` nêu đúng lệnh khắc phục `pip install dlib-bin`.

### 6.5. Hai mô hình nạp một lần trong `__init__`

Bộ dò điểm mốc nặng 99,7 MB. Nạp nó trong mỗi lần gọi `trich_dac_trung` sẽ làm phép đo tốc độ ở Cổng
C vô nghĩa — con số thu được khi đó là thời gian đọc đĩa, không phải thời gian suy luận.

---

## 7. Bảng tiêu chí nghiệm thu

Mỗi dòng là một ca kiểm thử trong `tests/test_dlib_backend.py`, đặt tên `test_dong<nn>`.

### 7.1. Khởi tạo và cấu hình

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Thiếu gói `dlib` → `LoiMoHinh`, thông báo nêu lệnh cài | monkeypatch chặn import; `pytest.raises(LoiMoHinh, match="dlib-bin")` |
| 02 | Tệp trọng số không tồn tại → `LoiMoHinh` nêu tên tệp | cfg trỏ đường dẫn sai |
| 03 | Tệp bộ dò điểm mốc không tồn tại → `LoiMoHinh` nêu tên tệp | như trên |
| 04 | Thiếu khoá `dlib.model_path` → `LoiCauHinh` | cfg khuyết khoá |
| 05 | `num_jitters` âm → `LoiCauHinh` | `num_jitters = -1` |
| 06 | `num_jitters` không phải số nguyên → `LoiCauHinh` | `num_jitters = "nhiều"` |
| 07 | `embedding_dim` lệch số chiều thật của mô hình → `LoiMoHinh` | `@pytest.mark.slow`; đặt `embedding_dim = 512` |
| 08 | `so_chieu` đọc từ mô hình, **không** từ cấu hình | `@pytest.mark.slow`; đặt `embedding_dim` đúng 128, assert `so_chieu == 128` sau khi nạp mô hình thật |

### 7.2. Trích đặc trưng

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 09 | Ảnh sai kiểu → `ValueError` | truyền danh sách Python |
| 10 | Ảnh sai hình dạng → `ValueError` | mảng `(112, 112)` hai chiều |
| 11 | Ảnh sai dtype → `ValueError` | `float32` thay vì `uint8` |
| 12 | Ảnh rỗng → `ValueError` | hình dạng `(0, 0, 3)` |
| 13 | Ảnh hợp lệ → vectơ `(128,)` kiểu `float32` | `@pytest.mark.slow`; kiểm cả `shape` lẫn `dtype` |
| 14 | Vectơ trả về **đã chuẩn hoá L2** | `@pytest.mark.slow`; `abs(norm - 1.0) < 1e-5` |
| 15 | **Cùng ảnh cho cùng vectơ** | `@pytest.mark.slow`; gọi hai lần, `np.allclose` |
| 16 | **Đổi kênh màu làm đổi kết quả** | `@pytest.mark.slow`; so vectơ của ảnh gốc với ảnh đã đảo kênh; assert độ tương đồng < 0,99 — ca này canh §6.1 |

### 7.3. Đăng ký và so khớp

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 17 | Danh sách ảnh rỗng → `ValueError` | `enroll([], cfg)` |
| 18 | Ít hơn `min_images_per_user` → `ValueError` nêu số ảnh thiếu | 3 ảnh, ngưỡng 10 |
| 19 | Đủ ảnh → vectơ `(128,)` đã chuẩn hoá L2 | `@pytest.mark.slow` |
| 20 | Gallery rỗng → `(None, 0.0)` | không cần mô hình thật nếu giả lập `trich_dac_trung` |
| 21 | Không ai vượt ngưỡng → `(None, độ_tương_đồng_cao_nhất)` | ngưỡng 0,99 với gallery ngẫu nhiên |
| 22 | Có người vượt ngưỡng → trả đúng mã người đó | gallery chứa chính vectơ của ảnh truy vấn |

### 7.4. Hai backend thay thế được cho nhau

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 23 | `DlibFaceRecognizer` là thể hiện của `BoNhanDien` | `isinstance` |
| 24 | Ba phương thức có **cùng chữ ký** với `ArcFaceRecognizer` | dùng `inspect.signature`, so tên và thứ tự tham số |
| 25 | **Cùng ảnh LFW, cùng người, hai backend đều cho độ tương đồng cao** | `@pytest.mark.slow`; hai ảnh của cùng một danh tính LFW; assert độ tương đồng > 0,4 ở **cả hai** backend |

Dòng 24 là ca chốt của tính thay thế: nếu chữ ký lệch, script so sánh ở Cổng C sẽ phải viết hai
nhánh riêng và phép so sánh mất tính công bằng.

Dòng 25 dùng ngưỡng rất lỏng, chủ ý. Nó **không** đo độ chính xác — đó là việc của Cổng C. Nó chỉ
bắt trường hợp một backend bị hỏng hoàn toàn, ví dụ sai tiền xử lý khiến mọi cặp ảnh đều cho độ
tương đồng gần bằng nhau.

⚠️ **Ràng buộc thu thập**: `pytest --collect-only -m "not slow"` phải chạy trót lọt kể cả khi máy
chưa cài `dlib`. Ca nào cần gói thật phải đánh dấu `slow` hoặc giả lập.

---

## 8. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

```bash
pip install dlib-bin==20.0.1
```

Lệnh duy nhất được phép cài gói trong mã việc này, vì §2 đã chốt phiên bản.

```bash
python -m black --check --line-length 100 src/recognizer tests/test_dlib_backend.py
```

```bash
python -m ruff check src/recognizer tests/test_dlib_backend.py
```

```bash
python -m pytest tests/test_dlib_backend.py -v
```

```bash
python -m pytest -q -m "not slow"
```

```bash
git status --short --untracked-files=all
```

Phải cho thấy đúng bốn tệp của §2.

### Quét mẫu vi phạm — cả ba lệnh phải rỗng

```bash
grep -nE "^import dlib|^from dlib" src/recognizer/dlib_backend.py
```

```bash
grep -nE "\b(150|128|112|127\.5)\b" src/recognizer/dlib_backend.py
```

Số 128 chỉ được xuất hiện qua cấu hình, không viết cứng. Số 150 xuất hiện là dấu hiệu tự phóng ảnh —
vi phạm §6.1.

```bash
grep -n "except Exception" src/recognizer/dlib_backend.py
```

### Kiểm đột biến bắt buộc

Ghi tệp bằng `[System.IO.File]::WriteAllText` với `UTF8Encoding($false)`.

| # | Phép đột biến | Ca **phải** đỏ |
|---|---|---|
| ĐB1 | Bỏ bước đổi BGR sang RGB | **dòng 16** |
| ĐB2 | Bỏ chuẩn hoá L2 ở `trich_dac_trung` | dòng 14 |
| ĐB3 | Bỏ đối chiếu `embedding_dim` với số chiều thật | dòng 07 |
| ĐB4 | Bỏ kiểm `min_images_per_user` trong `enroll` | dòng 18 |

ĐB1 quan trọng nhất: nó đúng loại lỗi im lặng mà §6.1 mô tả — mô hình vẫn trả về đủ 128 số, không
ngoại lệ nào được ném, chỉ có kết quả sai.

---

## 9. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` 100, `ruff` sạch. Type hints, docstring tiếng Việt kiểu Google.
- Thư viện được phép: thư viện chuẩn, `numpy`, `cv2`, `dlib`, và `src/**`. **Không** `torch`,
  **không** `ultralytics`, **không** `onnxruntime` trong tệp này.
- `dlib` chỉ import trong thân hàm (§6.4).
- `logging` qua `src.common.logging.lay_logger`; không `print()` trong `src/`.
- Ngoại lệ đúng loại: `LoiCauHinh` cho cấu hình, `LoiMoHinh` cho mô hình, `ValueError` cho dữ liệu
  đầu vào — giữ nguyên hợp đồng của `base.py`.
- Container ARM64 **không có** `models/`. Ca test cần trọng số thật phải `pytest.skip` có thông báo
  nêu rõ thiếu gì.

---

## 10. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **`scripts/enroll.py`** — bước 3.4, mã việc `P3-03`.
- **Quét ngưỡng, vẽ ROC, đo FAR** — bước 3.5 và 3.7, thuộc Cổng C.
- **Chốt ngưỡng** trong `configs/recognize.yaml` — đang để `TBD`, phải đến từ số đo.
- **Chốt phương án chính thức** — bước 3.8, sau khi có bảng so sánh.
- **Đo tốc độ hai phương án** — cần Raspberry Pi 5.
- Sửa `arcface_backend.py` dưới bất kỳ hình thức nào.

---

## 11. Báo cáo khi xong

Theo mẫu §12 của [`docs/quy-tac-cai-dat.md`](../quy-tac-cai-dat.md):

1. Kết quả các lệnh §8, dán nguyên văn dòng tổng kết.
2. Kết quả ba lệnh `grep`, giải trình dòng nào không rỗng.
3. Bảng bốn phép đột biến — đặc biệt **ĐB1**.
4. **Số chiều thật** mà mô hình trả về, đối chiếu với `embedding_dim` trong cấu hình.
5. Vướng mắc.

**Không commit.**

## 11b. Lượt của người dùng — sau khi §8 xanh

```bash
docker build -f deploy/Dockerfile.arm64 -t faceid:arm64 .
```

Bắt buộc vì `requirements.txt` đã đổi (R43).

```bash
docker run --rm faceid:arm64 python3 -c "import dlib; print(dlib.__version__)"
```

Kết quả mong đợi: in ra phiên bản. Đây là phép kiểm rằng wheel `aarch64` thật sự cài được vào image,
điều mà lượt `pip download` chưa chứng minh.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

```bash
python -m pytest -m slow -v
```

Lượt cuối chạy các ca cần mô hình thật, trong đó **dòng 16 và dòng 25** là hai ca quan trọng nhất:
một ca canh việc đổi kênh màu, một ca xác nhận cả hai backend đều nhận ra cùng một người.
