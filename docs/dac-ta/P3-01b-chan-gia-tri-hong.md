# Đặc tả P3-01b — chặn giá trị cấu hình hỏng ở khối nhận diện

| | |
|---|---|
| **Mã việc** | `P3-01b-chan-gia-tri-hong` |
| **Nhánh** | `feat/p3-01b-chan-gia-tri-hong` |
| **Phase** | 3 — Nhận diện danh tính |
| **Phụ thuộc** | `P3-01` đã gộp vào `dev` (commit `74131b0`) |
| **Nguồn** | `docs/review/P3-01-recognizer.review.md` §11.2 (G5, G6, G7) và §14.3 |
| **Quy trình** | 6 nhịp — **người cài đặt không chạy gì**, xem `CLAUDE.md` §2.9 R42 |

---

## 1. Mục tiêu

Vá đúng ba lỗ hổng mà lượt kiểm định `P3-01` tìm ra, không hơn. Cả ba đều là **khiếm khuyết của bản
đặc tả P3-01**, không phải của bản cài đặt — người cài đặt đã chặn đủ 17/17 biến thể mà đặc tả cũ
liệt kê đích danh.

| | Lỗ hổng | Hậu quả đã đo được |
|---|---|---|
| **G5** | `scale = inf` được chấp nhận | Tensor đầu vào thành **toàn số 0**. Đo thật trên 6 danh tính LFW khác nhau: độ tương đồng giữa **những người khác nhau** ra đúng **1,0000** ở mọi cặp. Tức FAR 100 % |
| **G6** | `mean`/`scale` nhận `nan`, `±inf`, `1e308`, `1e-320` | Vectơ đặc trưng toàn `NaN`, độ dài `nan`. Chốt `if do_dai == 0.0` **không bắt được** vì `nan == 0.0` là `False`. Cả gallery đăng ký thành `NaN` mà không một dòng log cảnh báo |
| **G7** | `input_size` không đối chiếu với đồ thị ONNX | `input_size: [64, 64]` lọt qua `__init__`; tới `trich_dac_trung` thì `onnxruntime` ném `InvalidArgument` — API nội bộ của thư viện rò ra ngoài, trái hợp đồng §5 của `P3-01` ("Raises: `ValueError`") |

**G5 là nguy hiểm nhất và phải làm trước.** Nó dẫn thẳng tới kịch bản "mọi khuôn mặt giống hệt nhau
mà hệ thống trông vẫn hoàn hảo" — vectơ chuẩn hoá đẹp, `enroll` trót lọt, `identify` trả đúng người
với điểm 1,0. Đây đúng là thảm hoạ mà §4.2 của đặc tả `P3-01` dựng cả nhóm dòng 27–28 để phòng, và
nhóm đó **không bắt được** vì nó chạy trên cấu hình đúng.

Kèm theo: bịt luôn góp ý **G1** — hiện **không ca test nào nạp `configs/recognize.yaml` thật**. Toàn
bộ 38 ca của `P3-01` dùng cấu hình viết tay trong `_cfg_hop_le()`. Một giá trị sai trong tệp YAML
thật sẽ không ca nào phát hiện, mà theo G5 thì hậu quả của nó là FAR 100 %.

---

## 2. Vì sao ba lỗ hổng này lọt

Ghi lại để `spec-writer` không lặp lại, chứ không phải để trách ai.

Đặc tả `P3-01` §6.1 dòng 07–08 **liệt kê đích danh** các biến thể cần chặn: `channel_order:"xyz"`,
`scale:0`, `scale:-1`, `mean:"abc"`, `input_size:[112]`, và mười hai biến thể nữa ở dòng 08. Người
cài đặt chặn đủ cả mười bảy.

Sai lầm nằm ở chỗ đặc tả nghĩ theo kiểu **liệt kê ca xấu**, thay vì theo kiểu **nêu tính chất mà giá
trị hợp lệ phải có**. Danh sách liệt kê bao giờ cũng thiếu; "phải là số hữu hạn dương" thì không.
Bài học này đã ghi vào `.claude/agents/spec-writer.agent.md` (commit `45e22e3`).

Kiểu tấn công `nan` nguy hiểm riêng vì nó **lách qua mọi phép so sánh**: `nan <= 0`, `nan > 0`,
`nan == 0` đều cho `False`. Bộ lọc viết bằng phép so sánh không bao giờ chặn được `nan` — bắt buộc
phải hỏi thẳng `math.isfinite`.

---

## 3. Phạm vi file — danh sách trắng

Chỉ được tạo hoặc sửa đúng ba tệp:

| Tệp | Thao tác | Ước lượng |
|---|---|---|
| `src/recognizer/arcface_backend.py` | sửa | ~10 dòng |
| `tests/test_recognizer.py` | sửa — **thêm** ca mới, không đổi 38 ca cũ | ~9 ca |
| `docs/kiem-may/P3-01b-chan-gia-tri-hong.coder.ps1` | tạo mới | kịch bản kiểm |

**Cấm chạm**: `configs/` (kể cả `recognize.yaml` — ca test mới chỉ **đọc** tệp này),
`src/recognizer/base.py`, `models/`, `docs/` ngoài `kiem-may/`, `results/`, `report/`, `CLAUDE.md`.

Ba mươi tám ca test cũ **phải giữ nguyên và vẫn xanh**. Sửa một ca cũ = CHẶN-A.

---

## 4. Dữ kiện đã kiểm chứng — dùng luôn, không đoán lại

### 4.1. Giá trị hợp lệ thật sự, KHÔNG được chặn

Lượt kiểm định `P3-01` §11.3 đã xác minh ba giá trị sau là **đúng**, chặn chúng mới là sai:

| Giá trị | Vì sao hợp lệ |
|---|---|
| `mean = 0` | Chính là phương án `x/255` mà §4.2 đặc tả `P3-01` liệt kê |
| `mean = -127,5` | Số âm hợp lệ với `mean`; chỉ `scale` mới bắt buộc dương |
| `channel_order = "RGB"` | `.lower()` là khoan dung có chủ ý |

Điểm mấu chốt: **`mean` chỉ cần hữu hạn, `scale` cần hữu hạn VÀ dương.** Hai ràng buộc khác nhau,
đừng áp chung một hàm kiểm.

### 4.2. Số chiều và kích thước đọc từ đồ thị ONNX

`mobilefacenet.onnx` cho `output.shape[-1] == 512` và đầu vào NCHW với hai chiều cuối là `112, 112`.
Chốt `embedding_dim` đã có sẵn ở `arcface_backend.py:206` — **chốt `input_size` phải đối xứng hoàn
toàn với nó**, cùng chỗ, cùng kiểu ngoại lệ, cùng cách nêu cả hai giá trị trong thông báo.

⚠️ Hai chiều cuối của đầu vào ONNX **có thể là trục động** (chuỗi kiểu `"None"`, `"?"`, hoặc `None`
thay vì số nguyên). Gặp trục động thì **bỏ qua phép đối chiếu**, không ném lỗi — mô hình khi đó chấp
nhận nhiều kích thước và không có gì để đối chiếu.

### 4.3. Giá trị hiện có trong `configs/recognize.yaml`

Đã đối chiếu thủ công ở lượt review `P3-01` §7 G1, khớp hoàn toàn:

```
channel_order: rgb · mean: 127.5 · scale: 128.0 · embedding_dim: 512 · input_size: [112, 112]
```

Bốn con số này là **mốc đã chốt bằng thực nghiệm** (`models/README.md` §3.3, tách biệt 0,6010).
Ca test dòng 47 dưới đây canh đúng chúng.

---

## 5. Giao diện — thay đổi tối thiểu

Không thêm hàm public nào. Không đổi chữ ký hàm nào. Ba sửa đổi:

### 5.1. `_doc_so_thuc` — thêm chốt hữu hạn

```python
def _doc_so_thuc(cfg: dict, khoa: str) -> float:
    """Đọc một tham số kiểu số (int hoặc float) trong `cfg`, ném `LoiCauHinh` nếu sai.

    Giá trị phải **hữu hạn**: `nan`, `inf`, `-inf` đều bị từ chối. Lý do: `nan` lách qua
    mọi phép so sánh (`nan <= 0` là `False`), còn `inf` làm phép chia cho ra tensor toàn 0
    khiến mọi khuôn mặt giống hệt nhau mà không có dấu hiệu lỗi nào.
    """
```

Đặt chốt trong `_doc_so_thuc` **chứ không phải** trong `_doc_ty_le` — như vậy phủ được cả `mean` lẫn
`scale` bằng một chỗ sửa, và mọi tham số số thực thêm về sau tự động thừa hưởng.

Thông báo lỗi phải nêu **tên khoá** và **giá trị nhận được**, giữ nguyên văn phong các thông báo hiện
có trong tệp.

### 5.2. `_doc_ty_le` — giữ nguyên chốt dương

Sau khi 5.1 xong, `_doc_ty_le` đã được `_doc_so_thuc` bảo vệ khỏi `inf`/`nan`. Chốt `gia_tri <= 0`
**giữ nguyên**, không đụng tới. Thông báo lỗi của nó cũng giữ nguyên — có ca test cũ đang canh.

### 5.3. `trich_dac_trung` và `enroll` — chốt độ dài không hữu hạn

Ba chỗ hiện viết `if do_dai == 0.0` (dòng 260, 296, 302) phải đổi thành dạng bắt được cả `NaN`:

```python
if not math.isfinite(do_dai) or do_dai == 0.0:
```

Giữ nguyên loại ngoại lệ và nội dung thông báo mà mỗi chỗ đang dùng — chỉ mở rộng điều kiện.

### 5.4. `__init__` — đối chiếu `input_size` với đồ thị ONNX

Sau `dau_vao = self._session.get_inputs()[0]`, so hai chiều cuối của `dau_vao.shape` với
`kich_thuoc_vao`. Lệch → `LoiCauHinh` nêu **cả hai** cặp số. Trục động → bỏ qua.

Đặt **ngay cạnh** chốt `embedding_dim` sẵn có để người đọc sau thấy hai chốt là một cặp.

---

## 6. Bảng tiêu chí nghiệm thu

Chín ca mới, đánh số nối tiếp bộ cũ: `test_dong39` đến `test_dong47`.
Ba mươi tám ca cũ giữ nguyên → tổng **47 ca** trong `tests/test_recognizer.py`.

### 6.1. Chặn giá trị không hữu hạn — G5 và G6

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 39 | `scale = inf` → `LoiCauHinh` | `pytest.raises(LoiCauHinh)`; thông báo chứa `scale` |
| 40 | `scale = nan` → `LoiCauHinh` | như trên |
| 41 | `mean = inf` → `LoiCauHinh` | `pytest.raises(LoiCauHinh)`; thông báo chứa `mean` |
| 42 | `mean = -inf` và `mean = nan` → `LoiCauHinh` | Hai lần `pytest.raises`, mỗi giá trị một lần |
| 43 | **Cặp đối chứng**: `mean = 0` và `mean = -127.5` **được chấp nhận** | Không ném lỗi, và tensor trả về khác nhau giữa hai cấu hình |

> Dòng 43 là dòng chống việc vá quá tay. Không có nó, cách "sửa" đơn giản nhất là chặn mọi giá trị
> không dương cho cả `mean`, làm hỏng phương án `x/255` mà §4.2 đặc tả `P3-01` công nhận là hợp lệ.

⚠️ `scale = 1e-320` **tràn thành `inf`** khi chia, nhưng bản thân nó là số hữu hạn dương nên
`math.isfinite` không chặn. **Không yêu cầu chặn ca này** — chặn nó cần một ngưỡng tuỳ tiện, mà đặt
ngưỡng tuỳ tiện vào mã là đúng thứ R16 cấm. Ghi lại ở đây để lượt review sau khỏi báo động nhầm.

### 6.2. Chốt `NaN` cho độ dài vectơ — G6

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 44 | `trich_dac_trung` gặp vectơ độ dài `NaN` → ném lỗi, **không** trả vectơ `NaN` | Backend giả trả vectơ chứa `nan`; `pytest.raises`; và assert **không** có đường thoát nào trả về mảng chứa `NaN` |
| 45 | `enroll` gặp một ảnh cho vectơ `NaN` → ném lỗi, không đăng ký | `pytest.raises`; gallery không nhận vectơ nào |

### 6.3. Đối chiếu `input_size` với đồ thị — G7

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 46 | `input_size: [64, 64]` với mô hình 112×112 → `LoiCauHinh` ngay ở `__init__` | `pytest.raises(LoiCauHinh)`; thông báo chứa **cả** `64` **và** `112`. Skip có thông báo khi thiếu `models/mobilefacenet.onnx` |

> Assert phải đòi **cả hai** con số. Thông báo chỉ nêu một bên thì người sửa lỗi không biết cấu hình
> sai hay mô hình sai — đúng lý lẽ mà chốt `embedding_dim` đã áp dụng.

### 6.4. Tệp cấu hình thật — G1, ca quan trọng nhất của mã việc này

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 47 | `configs/recognize.yaml` **thật** nạp được và khớp mốc đã đo | Nạp tệp thật (không phải `_cfg_hop_le()`), lấy nhánh `arcface`, assert `channel_order == "rgb"`, `mean == 127.5`, `scale == 128.0`, `embedding_dim == 512`, `input_size == [112, 112]` |

Ca này **không được skip** khi thiếu mô hình — nó chỉ đọc YAML, không cần `models/`. Nó phải chạy
được cả trong container ARM64.

Vì sao đây là ca quan trọng nhất: bốn giá trị đó là **kết quả thực nghiệm đã chốt**
(`models/README.md` §3.3). Đổi nhầm một trong bốn thì không có lỗi nào xảy ra — hệ thống chạy y
nguyên, chỉ có điều không phân biệt được ai với ai. Ca 47 là lá chắn duy nhất.

---

## 7. Kịch bản kiểm — người cài đặt viết, NGƯỜI DÙNG chạy

⚠️ Theo R42, người cài đặt **không chạy bất kỳ lệnh nào**. Viết
`docs/kiem-may/P3-01b-chan-gia-tri-hong.coder.ps1` theo khung ở `docs/kiem-may/README.md`.

### 7.1. Các đoạn bắt buộc

| Đoạn | Nội dung | Kết quả mong đợi |
|---|---|---|
| 1 | `black --check --line-length 100 src tests` | sạch |
| 2 | `ruff check src tests` | `All checks passed!` |
| 3 | `pytest -q` toàn kho | **388 passed** (379 cũ + 9 mới) |
| 4 | `pytest tests/test_recognizer.py -v` | **47 passed** |
| 5 | `pytest` trong `faceid:arm64` | 0 failed, 0 error. Ca 47 **phải chạy**, không skip |
| 6 | Quét: `Grep "== 0\.0"` trong `arcface_backend.py` | Không còn chốt `== 0.0` đứng một mình |
| 7 | Quét: `Grep "\b(127\.5\|128\|512\|112)\b"` trong `arcface_backend.py` | **rỗng** — vẫn không số nào viết cứng |
| 8 | `git status --short --untracked-files=all` | đúng 3 tệp danh sách trắng (+ `.docx` của sinh viên) |

Đoạn 5 dùng đúng image `faceid:arm64`, **không dựng image mới** (R43).

### 7.2. Ba phép đột biến bắt buộc

Dùng hàm `DotBien` ở `docs/kiem-may/README.md`. Mỗi phép khai báo trước ca nào phải đỏ:

| # | Phá gì | Ca **phải** đỏ |
|---|---|---|
| **ĐB8** | Bỏ chốt `math.isfinite` trong `_doc_so_thuc`, trả thẳng `float(gia_tri)` | dòng 39, 40, 41, 42 — và **chỉ** bốn dòng đó |
| **ĐB9** | Đổi `not math.isfinite(do_dai) or do_dai == 0.0` về lại `do_dai == 0.0` | dòng 44, 45 |
| **ĐB10** | Thay chốt `input_size` bằng `if False:` | dòng 46, **chỉ** dòng 46 |

> **ĐB8 không được làm đỏ dòng 43.** Nếu dòng 43 cũng đỏ thì chốt đã chặn nhầm giá trị hợp lệ —
> lỗi vá quá tay, nghiêm trọng hơn lỗ hổng ban đầu vì nó làm hỏng một phương án chuẩn hoá đúng.

Ngoài ra kịch bản phải **chạy lại ĐB2 của `P3-01`** (bỏ chuẩn hoá, đưa thẳng 0–255 vào mô hình) để
chứng minh mã việc này **không làm hỏng** lá chắn cũ. ĐB2 phải vẫn đỏ dòng 12 và 27 như trước.

---

## 8. Ràng buộc kỹ thuật

- Thư viện được phép: `math` (chuẩn), `numpy`, `cv2`, `onnxruntime`, `src.**`, và trong test thì thêm
  `pytest` cùng bộ nạp cấu hình sẵn có của dự án. **Không thêm gói nào vào `requirements.txt`.**
- `import math` đặt cùng nhóm thư viện chuẩn ở đầu tệp, đúng thứ tự `ruff` yêu cầu.
- Dùng `math.isfinite`, **không** dùng `np.isfinite` cho giá trị vô hướng đọc từ cấu hình —
  `np.isfinite` ném `TypeError` khi gặp chuỗi, làm rò một loại ngoại lệ khác ra ngoài.
- Mọi ngoại lệ cấu hình là `LoiCauHinh`; lỗi tệp mô hình là `LoiMoHinh`; lỗi đối số hàm là
  `ValueError`. Giữ đúng phân vai này của `P3-01`.
- Ca test chạm `models/` hoặc `data/` phải `pytest.skip` **có thông báo nêu rõ thiếu gì**.
  Ca 47 không thuộc nhóm này.
- Không `print()`. Log qua `lay_logger`, không dùng f-string trong lời gọi log.

---

## 9. Ngoài phạm vi — KHÔNG làm ở mã việc này

- ❌ Backend dlib (phương án A) — mã việc `P3-02` riêng
- ❌ `scripts/enroll.py` — mã việc `P3-03` riêng
- ❌ Quét ngưỡng, ROC, DET — bước 3.5, cần agent `training`
- ❌ Chốt `threshold` trong `configs/recognize.yaml` — vẫn để `TBD` cho tới khi có số đo (R7)
- ❌ Góp ý **G2** của biên bản (ca `enroll` → `identify` bằng vectơ thật) — để mã việc sau
- ❌ Góp ý **G3** (chú thích sai tên kênh ở `tests/test_recognizer.py:230`) — sửa được thì sửa,
  một dòng chú thích, nhưng **không bắt buộc** và không phải lý do trả lại
- ❌ Vá `tests/test_export_detector.py` của `P2-02` — vấn đề riêng, xem biên bản `P3-01` §10.3

---

## 10. Báo cáo khi xong

Theo mẫu §12 của `docs/quy-tac-cai-dat.md`. Bảng kết quả kiểm để `[CHƯA CHẠY]` — điền lại **sau khi**
người dùng dán kết quả về.

Nêu rõ ở đầu báo cáo nếu gặp bất kỳ điều nào sau:

- Hai chiều cuối của đầu vào ONNX là trục động → nói rõ đã xử lý thế nào (§4.2)
- Có ca cũ nào trong 38 ca phải sửa để 9 ca mới xanh → **đây là dấu hiệu vá sai**, dừng và báo,
  không tự sửa ca cũ
- Chốt `math.isfinite` làm đỏ dòng 43 → vá quá tay, dừng và báo
