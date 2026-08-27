# Review P3-01b-chan-gia-tri-hong — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-01b-chan-gia-tri-hong.md` |
| **Nhánh** | `feat/p3-01b-chan-gia-tri-hong` (HEAD `2e4b2b2`) |
| **Ngày** | 2026-08-27 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — được commit ngay. Không có 🔴, không có 🟡. Bốn mục 🔵 còn lại **đều nằm ngoài phạm vi người cài đặt** |

Kiểm định độc lập: mọi phép kiểm dưới đây được dựng lại từ đầu, **không dùng lại** kết quả của
`docs/kiem-may/P3-01b-chan-gia-tri-hong.coder.ps1`. Ba phép đột biến mà đặc tả §7.2 chỉ định được
viết lại từ con số không, cộng thêm bốn phép do người review tự nghĩ ra.

---

## 1. Hai kịch bản sinh ra số liệu

| Kịch bản | Người dùng chạy | Nội dung |
|---|---|---|
| `docs/kiem-may/P3-01b-chan-gia-tri-hong.review.ps1` | 2026-08-27, lượt 1 | 26 đoạn: phạm vi tệp, ba lệnh nền, quét mẫu vi phạm, chín phép đột biến, bộ 22 cấu hình thù địch. Bốn đoạn container (12–15) **đổ vì Docker daemon chưa bật** |
| `docs/kiem-may/P3-01b-chan-gia-tri-hong.review-container.ps1` | 2026-08-27, lượt 2 | 5 đoạn C1–C5: chỉ phần container, làm lại phần lượt 1 bỏ lỡ |

Tệp `.review.ps1` **không được sửa** sau lượt 1 — nó phải giữ nguyên đúng bản đã sinh ra khối kết quả
đã dán về, nếu không thì không còn truy được số nào ra từ kịch bản nào
(`docs/kiem-may/README.md`). Phần container vì thế đi vào một tệp thứ hai.

---

## 2. Kết quả kiểm máy

Mỗi ô ghi rõ **kịch bản nào · đoạn số mấy**. Ô nào không có đoạn chống lưng thì không có dấu ✅.

### 2.1. Phạm vi tệp và dữ liệu

| Kiểm | Nguồn | Kết quả |
|---|---|---|
| Danh sách trắng §3 (đúng 3 tệp) | `.review.ps1` đoạn 3/26 | `so tep ngoai danh sach trang = 0` ✅ |
| `git diff --stat` | `.review.ps1` đoạn 2/26 | `arcface_backend.py` 32 dòng · `test_recognizer.py` 185 dòng · **212 insertions, 5 deletions** ✅ |
| Dữ liệu cấm lọt git (`jpg/png/npy/npz/onnx/pt/pth/env/db/sqlite`) | `.review.ps1` đoạn 4/26 | `RONG - khong co tep cam` ✅ |
| Vùng cấm chạm (`configs/`, `base.py`, `results/`, `report/`, `CLAUDE.md`, `models/`) | `.review.ps1` đoạn 5/26 | `RONG - khong cham vung cam` ✅ |
| 38 ca cũ có bị sửa không | `.review.ps1` đoạn 7/26 | `(khong xoa dong nao)` trong `tests/test_recognizer.py` — **0 deletions** ✅ |
| Tổng số ca | `.review.ps1` đoạn 7/26 | `So ham test_dong* : 47` ✅ |

**0 deletions trong tệp test là bằng chứng mạnh hơn việc đếm 47 ca.** Không xoá dòng nào nghĩa là
không ca cũ nào bị sửa để đi qua — điều §3 đặc tả xếp vào CHẶN-A. Năm dòng bị xoá còn lại nằm trọn
trong `arcface_backend.py`, đúng bằng 1 dòng docstring `_doc_so_thuc` + 1 dòng `return float(...)` +
3 dòng `if do_dai == 0.0`, khớp chính xác §5.1 và §5.3 đặc tả.

### 2.2. Ba lệnh nền

| Lệnh | Nguồn | Kết quả |
|---|---|---|
| `black --check --line-length 100 src tests` | `.review.ps1` đoạn 8/26 | `All done! 29 files would be left unchanged`, mã thoát 0 ✅ |
| `ruff check src tests` | `.review.ps1` đoạn 9/26 | `All checks passed!`, mã thoát 0 ✅ |
| `pytest -q` toàn kho, host | `.review.ps1` đoạn 10/26 | **388 passed** (379 cũ + 9 mới), mã thoát 0 ✅ — khớp §7.1 đoạn 3 đặc tả |
| `pytest tests/test_recognizer.py -rs`, host | `.review.ps1` đoạn 11/26 | **47 passed, 0 skipped** ✅ |

Mười sáu warning ở đoạn 10 là `PytestUnknownMarkWarning` và `TracerWarning` của
`tests/test_export_detector.py` + `tests/test_yolo_face.py`, thuộc `P2-02`, không liên quan.

### 2.3. Container `faceid:arm64`

| Kiểm | Nguồn | Kết quả |
|---|---|---|
| Đúng **một** image, không dựng image mới (R43) | `.review-container.ps1` C1/5 | `faceid:arm64` `sha256:607e6061…`, kiến trúc `arm64`, `1.05GB`, dựng `2026-08-25T04:34:37Z`. Danh sách `faceid*` chỉ một dòng ✅ |
| Container là ARM64 thật | `.review-container.ps1` C2/5 | `machine = aarch64` · `python = 3.11.16` ✅ |
| `pytest tests/test_recognizer.py`, có gắn thư mục | `.review-container.ps1` C3/5 | **47 passed in 248,64 s**, 0 skipped ✅ |
| §8 `P3-01`: 0 failed / 0 error khi thiếu `models/` và `data/` | `.review-container.ps1` C4/5 | **36 passed, 11 skipped**, 0 failed, 0 error ✅ |
| Ca 47 **không được skip** (§6.4 đặc tả) | `.review-container.ps1` C4/5 góc nhìn 2 | `test_dong47 … PASSED` ✅ |
| Dòng 39–45 chạy thật khi thiếu mô hình | `.review-container.ps1` C4/5 góc nhìn 2 | 39, 40, 41, 42, 43, 44, 45 đều `PASSED`; chỉ 46 `SKIPPED` ✅ |
| Skip **có thông báo nêu rõ thiếu gì** | — | ⚠️ **[KHÔNG ĐO ĐƯỢC LƯỢT NÀY]** — xem §6 |

Điều kiện của C4 được xác nhận trước khi chạy, không phải giả định: `models: []`, `data: []`,
`configs/recognize.yaml co: True`, và `ma CO chot isfinite: True` — tức bộ test chạy trên **đúng bản
mã đang review**, không phải bản nào khác.

Phép cộng khớp với lượt `P3-01`: trước 28 passed / 10 skipped trên 38 ca; nay 36 / 11 trên 47.
Tám trong chín ca mới chạy được trong container, một skip. `28 + 8 = 36`, `10 + 1 = 11`.

### 2.4. Quét mẫu vi phạm (`code-review.instructions.md` §2)

`.review.ps1` đoạn 16/26 và 17/26. Chín trong mười mẫu **rỗng**: `print()` · `except` trần ·
import phần cứng · `import torch` · log f-string · đường dẫn tuyệt đối · secret · `assert True` ·
số viết cứng `127.5|128|512|112` trong `arcface_backend.py`.

Hai mẫu có kết quả, đã rà tay, **không phải vi phạm**:

- `InferenceSession` tại `arcface_backend.py:207` và `yolo_face.py:181` — cả hai nằm trong `__init__`,
  không nằm trong vòng lặp frame (CB-5 không áp dụng).
- Số float trần tại `tests/test_recognizer.py:394, 395, 396, 417` — là ngưỡng của `test_dong27/28`,
  thuộc `P3-01`, và `0 deletions` chứng minh chúng không bị đụng tới ở mã việc này.

Đoạn 17/26 xác nhận đúng bốn chốt `math.isfinite` tại `arcface_backend.py:89, 282, 318, 324` — không
thừa, không thiếu — và `import math` nằm ở dòng 13, đúng nhóm thư viện chuẩn trên `from pathlib`.

### 2.5. Chín phép đột biến — tất cả trúng dự đoán

`sha256` khớp ở **cả chín** lần khôi phục. `So lan mau khop` đúng số dự kiến ở mọi phép.

| # | Nguồn | Phá gì | Ca đỏ | Kết luận |
|---|---|---|---|---|
| **ĐB8** | đoạn 18/26 | bỏ `math.isfinite` trong `_doc_so_thuc` | 39, 40, 41, 42 — **43 xanh** | ✅ đúng §7.2. Không vá quá tay |
| **ĐB11** | đoạn 19/26 | *thêm* `gia_tri <= 0` cho cả `mean` (mô phỏng vá quá tay) | **chỉ 43** | ✅ dòng 43 **không phải ca chết** |
| **ĐB9a** | đoạn 20/26 | bỏ chốt NaN ở `:282` | chỉ 44 | ✅ |
| **ĐB9b** | đoạn 21/26 | bỏ chốt NaN ở `:318` | **không ca nào** | xem 🔵-3 |
| **ĐB9c** | đoạn 22/26 | bỏ chốt NaN ở `:324` | **không ca nào** | xem 🔵-3 |
| **ĐB9** | đoạn 23/26 | bỏ cả ba chốt | 44, 45 | ✅ đúng §7.2 |
| **ĐB10** | đoạn 24/26 | vô hiệu chốt `input_size` | **chỉ 46** | ✅ đúng §7.2 |
| **ĐB2** | đoạn 25/26 | bỏ `(x−mean)/scale` (chạy lại từ `P3-01`) | 11, 12, 13, 14, 27, 28, 43 | ✅ lá chắn cũ còn nguyên |
| **ĐB12** | đoạn 26/26 | đổi `scale: 128.0 → 64.0` trong `configs/recognize.yaml` **thật** | **chỉ 47** | ✅ ca 47 đọc tệp thật |

Hai phép đáng nói vì chúng trả lời câu hỏi mà đặc tả không đặt ra:

- **ĐB11.** ĐB8 chỉ chứng minh dòng 43 *không đỏ oan*. Một ca luôn xanh trong mọi hoàn cảnh cũng cho
  kết quả y hệt. ĐB11 mô phỏng đúng lỗi mà §6.1 đặc tả dựng dòng 43 để phòng — chặn cả giá trị không
  dương cho `mean`, làm hỏng phương án `x/255` — và dòng 43 đỏ **một mình**. Dòng 43 biết đỏ khi phải đỏ.
- **ĐB12.** Ca 47 là ca duy nhất canh bốn con số đã chốt bằng thực nghiệm. Nếu nó vô tình đọc
  `_cfg_hop_le()` thay vì tệp thật thì nó vô dụng mà vẫn xanh. ĐB12 đổi tệp thật, chỉ 47 đỏ.

**ĐB2 làm đỏ dòng 43 là đúng logic, không phải dấu hiệu vá quá tay**: bỏ hết chuẩn hoá thì `mean = 0`
và `mean = −127,5` cho cùng một tensor, nên phép assert `not np.allclose(ra_0, ra_am)` phải hỏng.

### 2.6. Bộ 22 cấu hình thù địch tự dựng

`.review.ps1` đoạn `[BO SUNG]`. Bốn kết quả đáng ghi:

| Cấu hình | Trước `P3-01b` (đo ở `P3-01` §11.2) | Nay |
|---|---|---|
| `scale = inf` | chấp nhận → **mọi khuôn mặt tương đồng 1,0000** | `LoiCauHinh: 'scale' phải là số hữu hạn` ✅ |
| `scale`/`mean = nan`, `mean = ±inf` | chấp nhận → embedding toàn `NaN` | `LoiCauHinh` ✅ |
| `input_size = [64, 64]` / `[112, 113]` / `[2**40, 2**40]` | lọt `__init__`, rò `InvalidArgument` của `onnxruntime` | `LoiCauHinh` nêu cả hai cặp số ✅ |
| `mean = 0`, `mean = −127.5`, `input_size` dạng tuple, `channel_order = "RGB"` | chấp nhận | vẫn chấp nhận ✅ **không vá quá tay** |

`scale = 1e-320` — ca mà §6.1 đặc tả **cố ý không yêu cầu chặn** — nay ném
`ValueError: Vectơ đặc trưng có độ dài 0`. Chốt `math.isfinite(do_dai)` ở `:282` biến một lỗi câm
thành lỗi ồn **mà không cần đặt bất kỳ ngưỡng tuỳ tiện nào vào mã** (R16). `mean = ±1e308` cũng vậy.
Đây là lợi ích ngoài dự kiến của cách vá mà §5.1 đặc tả chọn, đáng ghi nhận.

---

## 3. Một con số trong đầu ra kiểm máy **không được dùng**

Phần 2 của đoạn `[BO SUNG]` in dòng:

```
doi chung: scale=128, mean=127.5 -> tuong dong giua 3 ANH KHAC NHAU=[0.8008, 0.8193, 0.8082]
```

**Con số 0,80 là vô nghĩa và không được đưa vào bất kỳ đâu.** Ba "ảnh khác nhau" ở đó là nhiễu ngẫu
nhiên `np.random.default_rng(42).integers(0, 256, (112,112,3))` — không phải khuôn mặt, không có nhãn
danh tính. Mô hình ánh xạ ba mẫu nhiễu cùng phân bố về gần cùng một điểm, nên 0,80 phản ánh đầu vào
không có cấu trúc chứ không phản ánh năng lực phân biệt. Đặt nó cạnh mốc `khác người ≈ 0,0079`
(`models/README.md` §3.3) là so sai đơn vị.

Đây là **khiếm khuyết trong kịch bản của người review**, ghi lại để không lặp: một tệp dò không được
in ra thứ trông như số đo mà không có nhãn dữ liệu đằng sau (R6).

Bằng chứng phủ định báo động, đo trên khuôn mặt LFW thật: `test_dong27` khẳng định
`tb_khac_nguoi < 0,20` và `tb_cung_nguoi − tb_khac_nguoi > 0,30`, **xanh** ở đoạn 10/26 và 11/26, và
**đỏ** dưới ĐB2 ở đoạn 25/26 — tức nó thật sự chạy trên dữ liệu thật chứ không âm thầm skip.

---

## 4. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §3 Danh sách trắng | ✅ đúng 3 tệp; không chạm `configs/`, `base.py`, `models/`, `results/`, `report/`, `CLAUDE.md` (đoạn 3, 5/26) |
| §4.1 Giá trị hợp lệ không được chặn | ✅ `mean = 0`, `mean = −127,5`, `channel_order = "RGB"` vẫn qua (đoạn `[BO SUNG]` Phần 1; dòng 43 + ĐB11) |
| §4.2 Trục động của đồ thị ONNX | ✅ có nhánh `la_kich_thuoc_tinh` tại `arcface_backend.py:225-227`. Mô hình thật cho trục **tĩnh** (dòng 46 xanh trên host), nên nhánh trục động chưa được ca nào chạy qua — xem 🔵-4 |
| §5.1 `_doc_so_thuc` thêm chốt hữu hạn | ✅ `arcface_backend.py:89`, đúng chỗ đặc tả chỉ định (không phải trong `_doc_ty_le`); docstring nêu đúng lý do |
| §5.2 `_doc_ty_le` giữ nguyên | ✅ `:132` vẫn `phải lớn hơn 0`, thông báo cũ nguyên vẹn |
| §5.3 Ba chốt độ dài không hữu hạn | ✅ `:282`, `:318`, `:324`, giữ nguyên loại ngoại lệ và thông báo cũ |
| §5.4 Đối chiếu `input_size` | ✅ `:221-232`, đặt **ngay cạnh** chốt `embedding_dim`, cùng kiểu ngoại lệ, nêu cả hai cặp số |
| §6.1 dòng 39–43 | ✅ 5/5, ghim bằng ĐB8 + ĐB11 |
| §6.2 dòng 44–45 | ✅ 2/2, ghim bằng ĐB9a + ĐB9 |
| §6.3 dòng 46 | ✅ 1/1, ghim bằng ĐB10; skip đúng cách khi thiếu mô hình (C4/5) |
| §6.4 dòng 47 | ✅ 1/1, ghim bằng ĐB12; **chạy thật** trong container (C4/5) |
| §7.1 tám đoạn bắt buộc | ✅ 8/8, dựng lại độc lập |
| §7.2 ba phép đột biến | ✅ 3/3 đúng ca đỏ yêu cầu, cộng ĐB2 chạy lại và bốn phép người review tự thêm |
| §8 Ràng buộc kỹ thuật | ✅ chỉ `math` chuẩn thêm vào; không đụng `requirements.txt`; dùng `math.isfinite` chứ không `np.isfinite`; `LoiCauHinh`/`LoiMoHinh`/`ValueError` đúng vai; không `print()`; log không f-string |
| §9 Ngoài phạm vi | ✅ không có backend dlib, không `scripts/enroll.py`, không ROC; `threshold: TBD` trong `configs/recognize.yaml` giữ nguyên (đoạn 5/26 xác nhận `configs/` không bị sửa) |
| §10 Ba tình huống phải báo | ✅ không tình huống nào xảy ra: trục ONNX là tĩnh, không ca cũ nào phải sửa, dòng 43 không đỏ dưới ĐB8 |

Hai điểm sống còn, soi riêng theo checklist:

- **Trung thực số liệu (R5/R6).** Không có giá trị mặc định giả nào trong mã mới. Bốn con số mà ca 47
  canh (`rgb`, `127.5`, `128.0`, `512`, `[112,112]`) nằm trong **tệp cấu hình**, không viết cứng trong
  `src/` — đoạn 17/26 xác nhận quét số viết cứng cho kết quả rỗng. `threshold` vẫn là `TBD`, không bị
  mã "đỡ" bằng một số bịa. Docstring mới không chứa con số nào trông như kết quả đo. ✅
- **An toàn phần cứng (R22/R24).** Mã việc không chạm GPIO/camera. `ort.InferenceSession` vẫn nạp một
  lần trong `__init__` (đoạn 16/26). Không có tài nguyên phần cứng cần đóng. ✅

---

## 5. Hai câu hỏi được giao soi riêng — trả lời

### 5.1. Bốn ca `test_dong39`–`test_dong42` không gọi `_bo_qua_neu_thieu(_MODEL_PATH)`

Lập luận trong docstring của chúng — "mọi tham số cấu hình được xác thực **trước khi** `__init__` chạm
tới hệ thống tệp và ONNX" — **đúng với mã hiện tại**: sáu lệnh đọc cấu hình ở
`arcface_backend.py:195-200` chạy hết trước phép `duong_dan.exists()` ở `:203`.

Và nó **đã được kiểm bằng máy**, không còn là suy luận: C4/5 cho thấy bốn ca đó `PASSED` trong
container không có `models/`.

**Kết luận: thiết kế chấp nhận được, không ghi lỗi.** Ngược lại, chính bốn ca này giữ cho điều khoản
§8 của `P3-01` còn tác dụng — nếu chúng cũng skip thì lá chắn container rỗng thêm bốn ca. Điểm giòn
duy nhất: `LoiMoHinh` không kế thừa `LoiCauHinh` (`src/common/exceptions.py:8, 20`), nên nếu về sau ai
đó đảo thứ tự trong `__init__` thì bốn ca này đổ, mà đổ **chỉ trong container** — trên máy phát triển
sẽ không ai thấy. Đây là rủi ro cần biết, không phải lỗi hiện tại; ghi ở 🔵-4.

### 5.2. `scale = 1e-320`

Không báo là lỗi — §6.1 đặc tả cố ý không yêu cầu chặn. Hành vi thực tế đã ghi nhận ở §2.6: nay ném
`ValueError` thay vì im lặng. Ghi nhận như **điểm cộng**, không phải yêu cầu sửa.

---

## 6. Phạm vi bằng chứng — biên bản này đứng trên cái gì

Ghi để người đọc sau biết chính xác chỗ nào có số máy chống lưng, chỗ nào không.

| Yêu cầu | Trạng thái | Nguồn / lý do |
|---|---|---|
| Skip đúng ca khi thiếu `models/`, `data/` — trong `tests/test_recognizer.py` | ✅ **đo trực tiếp** | `.review-container.ps1` C4/5, 11 ca skip đúng danh sách |
| Ca 47 và dòng 39–45 không skip | ✅ **đo trực tiếp** | C4/5 góc nhìn 2 |
| Skip **có thông báo nêu rõ thiếu gì** | ⚠️ **gián tiếp, chưa đo lượt này** | Xem khối dưới bảng |
| Bộ test **toàn kho** không sinh failed/error mới trong container | ⚠️ **không đo trực tiếp** — đánh đổi có ý thức | Xem khối dưới bảng |
| 8 failed + 2 errors tồn đọng của `P2-02` còn hay hết | ❌ **không đo** | Ngoài phạm vi P3-01b; số cũ ở `P3-01` §10.3 |
| Hiệu năng, FPS, FAR | ❌ **không đo** | Việc của Cổng C, agent `training` |

**Về ô "skip có thông báo".** Góc nhìn 3 của C4/5 đặt tiêu đề như thể sẽ in ra lý do skip, nhưng bộ
lọc `Select-String 'SKIPPED|skipped'` chỉ bắt được dòng trạng thái của `-v`, không bắt khối tóm tắt
của `-rs` (dạng `SKIPPED [3] tests/test_recognizer.py:40: chưa có models/…`). **Lỗi của kịch bản
người review, không phải của mã.** Không ghi ✅ cho ô này.

Lập luận gián tiếp thay thế, và nó **là gián tiếp**, nói đúng như vậy: hai hàm sinh thông báo skip là
`_bo_qua_neu_thieu` (`tests/test_recognizer.py:66-68`) và `_bo_qua_neu_thieu_lfw` (`:71-73`), nội dung
`"chưa có {duong_dan}, xem models/README.md để tải mô hình"` và `"chưa có {_LFW_DIR}, chạy
scripts/preprocess.py trước"`; `git diff` cho **0 deletions** trong tệp này (đoạn 7/26), nên hai hàm đó
**không bị đụng tới**; và biên bản `P3-01` §4 đã xác minh chính chúng in ra thông báo nêu rõ thiếu gì
khi chạy thật. Chuỗi lập luận này đủ chắc để **không** đòi thêm 4–5 phút giả lập, nhưng không đủ để
ghi ✅. Nếu người dùng muốn khép kín, chỉ cần đổi bộ lọc góc nhìn 3 thành `Select-String 'chưa có'`.

**Về ô "toàn kho trong container".** Lệnh `pytest -q` toàn kho trong container đã được **bỏ có chủ ý**
khỏi `.review-container.ps1` (lý do ghi ngay trong đầu tệp kịch bản): giả lập ARM64 chạy 47 ca mất
248 s, toàn kho 388 ca mất hàng chục phút, trong khi `P3-01` §10.3 đã đo và đã chứng minh bằng máy
rằng `8 failed + 2 errors` khi đó thuộc trọn về `tests/test_export_detector.py` của `P2-02`. Thay
bằng hai bằng chứng rẻ hơn: 388 passed trên host (đoạn 10/26) và **bán kính ảnh hưởng tĩnh** (C2/5) —
ngoài nội bộ `src/recognizer/` và `tests/test_recognizer.py`, không tệp nào trong `src/`, `tests/`,
`scripts/` nhắc tới `arcface_backend` hay `src.recognizer`; hai kết quả duy nhất là một chú thích ở
`base.py:5` và dòng import của chính module tại `arcface_backend.py:48`. Không có đường nào để mã việc
này làm đổ mã việc khác. **Đây là đánh đổi có ý thức giữa chi phí giả lập và giá trị thông tin, không
phải bỏ sót phép kiểm.**

**Ghi chú phương pháp — dùng lại ở mọi mã việc sau.** C5/5 in `CO_ISFINITE=False`: mã nguồn nướng
trong `faceid:arm64` (dựng `2026-08-25T04:34:37Z`) là mã **trước** P3-01b. Vì `deploy/Dockerfile.arm64:17`
là `COPY . .` còn R43 cấm dựng lại image cho từng mã việc, **chạy container không gắn thư mục sẽ kiểm
nhầm một bản mã không phải bản đang review**. Cách đúng, và là cách C4/5 dùng: vẫn gắn `-v` để lấy mã
hiện tại, rồi che khuất `models/` và `data/` bằng `--tmpfs`. Chừng nào hai điều kiện trên còn giữ
nguyên thì mọi lượt review sau phải làm như vậy.

---

## 7. Lỗi phải sửa

**Không có.** Không có 🔴 CHẶN-A, không có 🔴 CHẶN-B, không có 🟡 CẦN SỬA.

Bản cài đặt thoả đúng và đủ chín tiêu chí nghiệm thu §6, ba sửa đổi §5 đặt đúng chỗ đặc tả chỉ định,
không mở rộng ra ngoài §9, và không sửa một dòng nào của 38 ca cũ.

---

## 8. 🔵 Góp ý (không chặn — người dùng quyết định)

Không mục nào dưới đây là lý do trả lại người cài đặt. Ghi rõ mục nào thuộc về ai.

### 🔵-1 — `mean`/`scale` là số nguyên Python quá lớn làm rò `OverflowError`
**Vị trí**: `src/recognizer/arcface_backend.py:88`
```python
gia_tri_float = float(gia_tri)
```
**Đo được**: `.review.ps1` đoạn `[BO SUNG]` Phần 1 — `mean = 10**400` và `scale = 10**400` cho
`*** RO OverflowError : int too large to convert to float`, không phải `LoiCauHinh`.
**Vì sao đáng quan tâm**: YAML sinh ra số nguyên lớn tuỳ ý được, nên đây là đường vào có thật từ tệp
cấu hình. Người gọi bắt `LoiCauHinh` theo hợp đồng §5 sẽ không bắt được ngoại lệ này, và
`OverflowError` không nói gì về khoá cấu hình nào sai.
**Thuộc về ai**: lỗ hổng **có từ `P3-01`** — dòng `float(gia_tri)` đã tồn tại trước mã việc này, và
`10**400` không nằm trong danh sách §6.1 mà đặc tả liệt kê. Khiếm khuyết của `spec-writer`, **không
phải** của người cài đặt (R38/R39).
**Sửa nếu người dùng đồng ý**: bọc `float(gia_tri)` trong `try/except OverflowError` rồi ném
`LoiCauHinh` nêu tên khoá — một mã việc con vài dòng, gộp được với 🔵-2.

### 🔵-2 — `do_tuong_dong` còn chốt `== 0.0` trần, gallery `NaN` cho ra `(None, -inf)`
**Vị trí**: `src/recognizer/base.py:93`
```python
if do_dai_a == 0.0 or do_dai_b == 0.0:
```
**Đo được**: `.review.ps1` đoạn 17/26 (quét) và đoạn `[BO SUNG]` Phần 3 — `identify` với gallery chứa
vectơ `NaN` trả `(None, -inf)` và ghi log `"Người lạ: similarity cao nhất -inf dưới ngưỡng 0.5000"`.
**Vì sao đáng quan tâm**: `-inf` không phải một độ tương đồng, trái hợp đồng §5 của `P3-01`
("trả `(None, độ_tương_đồng_cao_nhất)`"). Đường vào không còn là cấu hình hỏng nữa — nay là vectơ
`NaN` đọc từ `data/embeddings/*.npy`, tức từ đĩa.
**Thuộc về ai**: `src/recognizer/base.py` bị §3 đặc tả P3-01b **cấm chạm**. Người cài đặt làm đúng khi
không sửa. Việc của `spec-writer` khi mở mã việc kế tiếp.

### 🔵-3 — Hai chốt `NaN` trong `enroll` che nhau, không chốt nào được ghim riêng
**Vị trí**: `src/recognizer/arcface_backend.py:318` và `:324`
**Đo được**: `.review.ps1` đoạn 21/26 (ĐB9b) và 22/26 (ĐB9c) — phá riêng từng chốt, **47 passed**, không
ca nào đỏ. Chỉ khi phá cả ba (đoạn 23/26) thì 44 và 45 mới đỏ.
**Kết luận**: **dư thừa có chủ ý theo §5.3 đặc tả**, không phải lỗi. §5.3 nêu đích danh ba vị trí và
yêu cầu đổi cả ba; người cài đặt làm đúng ba chỗ. Yêu cầu §6.2 dòng 45 được thoả bởi *một trong hai*
chốt, nên bộ test hiện tại đã làm đúng chữ đặc tả.
**Rủi ro còn lại**: ai đó gỡ một trong hai về `== 0.0` thì 47 ca vẫn xanh.
**Sửa nếu người dùng đồng ý**: thêm một ca ghim riêng `:324` — các vectơ **hữu hạn** nhưng trung bình
tràn thành không hữu hạn ở biên `float32`. Là ca mới ngoài bảng §6, nên phải đi qua `spec-writer`.

### 🔵-4 — Hai nhánh chưa có ca test nào đi qua
**Vị trí**: `src/recognizer/arcface_backend.py:225-227` (nhánh trục động của đồ thị ONNX) và thứ tự gọi
ở `:195-204`.
**Vì sao ghi**: mô hình `mobilefacenet.onnx` cho trục **tĩnh**, nên nhánh "gặp trục động thì bỏ qua
phép đối chiếu" mà §4.2 đặc tả yêu cầu **chưa từng được chạy**. Tương tự, không ca nào canh việc
`__init__` phải xác thực cấu hình trước khi chạm hệ thống tệp — giả định mà bốn ca 39–42 dựa vào (§5.1).
**Thuộc về ai**: cả hai đều **ngoài bảng §6** đặc tả. `spec-writer` quyết định có mở mã việc không.
**Chi phí/lợi ích**: một ca dựng `_session` giả có `shape = ['batch', 3, 'H', 'W']` là đủ cho nhánh
thứ nhất, chừng mười dòng; nhánh thứ hai cần một ca đọc thứ tự gọi, giá trị thấp hơn.

---

## 9. Việc tiếp theo

Phán quyết 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — **được commit ngay**. Điều kiện duy nhất là bốn mục 🔵 ở §8, và
**không mục nào thuộc trách nhiệm người cài đặt**: 🔵-1 và 🔵-2 là khiếm khuyết đặc tả, 🔵-3 là dư thừa
mà chính đặc tả yêu cầu, 🔵-4 nằm ngoài bảng nghiệm thu. Không có gì để trả lại.

Thông điệp commit đề xuất, theo R29 (tiếng Việt, giữ mã việc để nối chuỗi truy vết):

```
feat(recognizer): P3-01b chặn cấu hình mean/scale không hữu hạn và đối chiếu input_size với đồ thị ONNX
```
gồm: `src/recognizer/arcface_backend.py`, `tests/test_recognizer.py`,
`docs/kiem-may/P3-01b-chan-gia-tri-hong.coder.ps1`.

Commit thứ hai cho phần kiểm định:

```
docs(review): P3-01b biên bản kiểm định và hai kịch bản kiểm máy
```
gồm: tệp này, `docs/kiem-may/P3-01b-chan-gia-tri-hong.review.ps1`,
`docs/kiem-may/P3-01b-chan-gia-tri-hong.review-container.ps1`.

`docs/kiem-may/README.md` đang sửa dở là **khung quy trình**, theo CLAUDE.md §2.9 nên đi riêng với
loại `chore(quy-trinh)`, không trộn vào hai commit trên. Năm tệp `.docx` trong `docs/bao-cao-tuan/`
không thuộc mã việc nào.

Sau khi gộp: `P3-02` (backend dlib) và `P3-03` (`scripts/enroll.py`) — cả hai chạy được trên LFW,
không cần camera. Nếu người dùng muốn khép 🔵-1 và 🔵-2 thì gộp chung thành một mã việc nhỏ
`P3-01c` trước, vì cả hai đều là một dòng sửa cùng loại.

---

### Phụ lục — trạng thái cây làm việc sau review

`.review-container.ps1` đoạn `[CUOI]`: `sha256` của `src/recognizer/arcface_backend.py`,
`tests/test_recognizer.py` và `configs/recognize.yaml` **khớp y nguyên** giá trị trước chín phép đột
biến của lượt 1. Không phép nào để lại rác.

```
8B1F4CF340E4F5A50BAEB3009E78DB34A1CDE1625650E76000B9137F686D8EC0  src/recognizer/arcface_backend.py
25E6F21C668384E298A460E839170589B7FB139AE3CD2F9C1A261179CC5B4BA8  tests/test_recognizer.py
028924C5EBFA42F33D8F63254EB38D29724FB158A2770431FCFAD526BB36053B  configs/recognize.yaml
```

Ba tệp `.ps1` chưa theo dõi trong `docs/kiem-may/` là sản phẩm hợp lệ của hai vai `coder` và
`code-reviewer` theo ranh giới ghi tệp ở CLAUDE.md §2.9 — trong đó
`P3-01b-chan-gia-tri-hong.review-container.ps1` nằm ngoài danh sách trắng §3 đặc tả vì nó do người
review viết ở lượt chạy máy thứ hai, **không phải** sản phẩm của người cài đặt. Dòng
` M docs/kiem-may/README.md` không thuộc mã việc này.
