# Review P3-01-recognizer — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-01-recognizer.md` |
| **Nhánh** | `feat/p3-01-recognizer` |
| **Ngày** | 2026-08-23 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — không còn 🔴 và 🟡, chỉ còn 🔵 góp ý. Được commit. |

---

## 1. Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | đúng **4** tệp trong danh sách trắng ✅ |
| `black --check --line-length 100 src tests` | sạch — 29 tệp không đổi ✅ |
| `ruff check src tests` | `All checks passed!` ✅ |
| `pytest -q` (toàn bộ) | **379 passed**, 0 failed, 0 error ✅ |
| `pytest tests/test_recognizer.py -v` | **38 passed** — đủ `test_dong01`…`test_dong38` ✅ |

Phạm vi tệp (`--untracked-files=all`):

```
?? src/recognizer/__init__.py
?? src/recognizer/arcface_backend.py
?? src/recognizer/base.py
?? tests/test_recognizer.py
?? docs/bao-cao-tuan/*.docx   (4 tệp — của sinh viên, §7 đặc tả dặn bỏ qua)
```

Không có tệp cấm lọt git (`.jpg/.png/.npy/.onnx/.pt/.env/.db`) — lệnh lọc trả rỗng.
`configs/`, `requirements.txt`, `models/`, `docs/`, `.claude/` **không bị chạm** ✅

> Ghi chú nhỏ, không phải lỗi: §7 đặc tả viết "**ba** tệp `.docx`", thực tế có **bốn**. Cả bốn đều là
> báo cáo tuần của sinh viên, không do người cài đặt sinh ra.

---

## 2. Quét mẫu vi phạm — cả tám lệnh đều rỗng

| Mẫu quét | Kết quả |
|---|---|
| `dlib\|import torch\|ultralytics` trong `src/recognizer/` | rỗng ✅ |
| `\b(127\.5\|128\|512\|112)\b` trong `arcface_backend.py` | **rỗng** ✅ — không số nào viết cứng |
| `except\s*:\|except Exception` | rỗng ✅ |
| `print(` | rỗng ✅ |
| `[A-Z]:\\\|/home/\|/Users/` (đường dẫn máy cá nhân) | rỗng ✅ |
| `token=\|api_key=\|password=` | rỗng ✅ |
| `assert True\|^\s*pass$` trong test | rỗng ✅ |
| `logger\.\w+\(f"` (log dùng f-string) | rỗng ✅ |
| `[<>]=?\s*0\.[0-9]` (ngưỡng float trần) | rỗng ✅ |
| `InferenceSession` nằm trong `for`/`while` | không — chỉ ở `__init__:198` ✅ |

Hằng số có tên duy nhất là `SO_KENH_MAU = 3` (`arcface_backend.py:63`) — đúng ngoại lệ mà §7 đặc tả
cho phép ("hằng số có tên cho số chiều tensor NCHW").

---

## 3. Kiểm đột biến — tự chạy độc lập, không tin lời báo

Quy trình mỗi phép: sao lưu → ghi `sha256` → sửa từ bản sao lưu → chạy → khôi phục → đối chiếu `sha256`.
`sha256` gốc và sau mọi lần khôi phục: `02f57fabba6e6b98230772ddff0c8bf204fd8eb47f586ff3bf87c99d4c750b5e`.

| # | Phép đột biến | Ca đỏ **yêu cầu** | Ca đỏ **thực tế** | Kết luận |
|---|---|---|---|---|
| **ĐB1** | Bỏ `cv2.cvtColor(..., COLOR_BGR2RGB)`, gán thẳng `anh_dung_kenh = anh` | dòng 11 | **dòng 11**, dòng 12 | ✅ có hiệu lực |
| **ĐB2** | Bỏ `(x − mean)/scale`, đưa thẳng `astype(np.float32)` 0–255 vào mô hình | dòng 12 **và** 27 | **dòng 12, 27**, kèm 11, 13, 14, 28 | ✅ có hiệu lực |
| **ĐB4** | Trong `enroll`, trung bình thô rồi mới chuẩn hoá một lần | dòng 30 | **chỉ dòng 30** | ✅ có hiệu lực |
| **ĐB6** | `identify` trả người **đầu tiên** vượt ngưỡng | dòng 38 | **chỉ dòng 38** | ✅ có hiệu lực |

Ba nhận xét đáng ghi lại:

1. **ĐB2 — phép quan trọng nhất theo §7 — đỏ đúng cả dòng 12 lẫn dòng 27.** Dòng 27 chạy trên
   `data/processed/lfw_original/` thật (không skip trên máy phát triển), nên bẫy "mọi khuôn mặt giống
   nhau 0,87–0,91 mà không báo gì" ở §4.2 **thực sự được canh**, không phải canh trên giấy.
2. **ĐB1 KHÔNG làm dòng 27 đỏ** — đúng như §6.4 đặc tả đã cảnh báo (0,6010 so với 0,5673, quá gần).
   Đây là bằng chứng độc lập rằng dòng 11 là ca duy nhất chặn được lỗi thứ tự kênh, và nó có tồn tại.
3. ĐB1 và ĐB2 làm đỏ thêm vài ca lân cận. Không phải "đỏ lan man": các ca này (11–14) cùng dùng một
   ảnh mẫu và cùng soi một hàm `chuan_bi_dau_vao`, nên định vị lỗi vẫn chính xác.

### Số đo dòng 27, tự đo lại (§10.4 đặc tả)

Chạy lại chuỗi xử lý của bộ test trên 20 danh tính LFW đầu tiên có ≥ 2 ảnh:

| | Đo lại (20 danh tính) | Mốc §4.2 đặc tả (60 danh tính) |
|---|---|---|
| Trung bình cùng người | **0,6057** | 0,6088 |
| Trung bình khác người | **0,0122** | 0,0079 |
| Tách biệt | **0,5935** | 0,6010 |

Lệch dưới 0,008 trên cả ba giá trị, cỡ mẫu khác nhau. Chuỗi tiền xử lý → suy luận → chuẩn hoá L2
trong `arcface_backend.py` **cho ra đúng con số mà đặc tả đã đo độc lập trước đó**.

---

## 4. Kiểm điều kiện container ARM64 (§8 đặc tả)

Mô phỏng bằng cách chạy bộ test từ một thư mục làm việc **không có** `models/` và `data/`
(đường dẫn trong test là tương đối nên phân giải sang thư mục rỗng):

```
28 passed, 10 skipped in 0.34s   — 0 failed, 0 error ✅
```

Mọi ca skip đều **có thông báo nêu rõ thiếu gì**: `"chưa có models\mobilefacenet.onnx, xem
models/README.md để tải mô hình"`. Đúng yêu cầu §8.

---

## 5. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §3 Danh sách trắng | ✅ đúng 4 tệp, không chạm tệp cấm |
| §4 Dữ kiện đã kiểm chứng | ✅ RGB + `(x−127,5)/128` đọc từ cấu hình, không viết cứng |
| §5 Giao diện | ✅ **khớp từng ký tự** — `so_chieu`, `trich_dac_trung`, `enroll`, `identify`, `do_tuong_dong`, `chuan_bi_dau_vao`, `ArcFaceBackend.__init__` |
| §6.1 dòng 01–08 | ✅ 8/8 |
| §6.2 dòng 09–16 | ✅ 8/8 |
| §6.3 dòng 17–26 | ✅ 10/10 |
| §6.4 dòng 27–28 | ✅ 2/2, chạy trên dữ liệu thật, số đo khớp mốc |
| §6.5 dòng 29–38 | ✅ 10/10 (xem §6 biên bản về hai chỗ suy diễn) |
| §7 Bốn lệnh máy + bốn grep | ✅ sạch |
| §7 Bảy phép đột biến | ✅ 4/7 tự xác minh lại, đều đúng ca đỏ yêu cầu |
| §8 Ràng buộc kỹ thuật | ✅ chỉ `numpy`/`cv2`/`onnxruntime`/`src.**`; `lay_logger`; `LoiCauHinh`/`LoiMoHinh`/`ValueError` đúng vai; container sạch |
| §9 Ngoài phạm vi | ✅ không có backend dlib, không `scripts/enroll.py`, không ROC, `threshold: TBD` giữ nguyên |

Kiểm riêng hai điểm sống còn:

- **Trung thực số liệu (R5/R6)**: các con số 0,6088 / 0,0079 / 0,6010 xuất hiện ở
  `tests/test_recognizer.py:346` và trong chú thích module đều **ghi rõ nguồn** (§4.2 đặc tả /
  `models/README.md` §3.3), không có giá trị mặc định giả nào trông như kết quả đo. `threshold` vẫn
  là `TBD` trong `configs/recognize.yaml`, không bị mã nguồn "đỡ" bằng một số bịa. ✅
- **An toàn phần cứng (R22/R24)**: mã việc này không chạm GPIO/camera. Không có tài nguyên phần cứng
  cần đóng. `ort.InferenceSession` nạp **một lần** trong `__init__`, không nằm trong vòng lặp frame. ✅

---

## 6. Hai chỗ người cài đặt tự suy diễn ngoài chữ đặc tả — thẩm định

### 6.1. Backend giả cho nhóm dòng 29–38 — **chấp nhận**

`tests/test_recognizer.py:68-84` dựng `ArcFaceBackend` bằng `object.__new__` (bỏ qua `__init__`) và
thay `trich_dac_trung` bằng hàm trả sẵn vectơ biết trước.

Ba lý do chấp nhận:

1. **Không phải test giả (CB-6).** `enroll()` và `identify()` **thật** vẫn được thi hành nguyên vẹn;
   chỉ phần suy luận ONNX bị thay. Phần bị thay đã được kiểm riêng ở dòng 17–21 bằng mô hình thật.
   Chứng minh bằng máy: ĐB4 và ĐB6 — hai phép đột biến nhắm thẳng vào `enroll`/`identify` — đều đỏ
   đúng một ca, không thừa không thiếu. Nếu đây là test giả thì hai phép này đã xanh.
2. **Đáp ứng §8 tốt hơn phương án dùng mô hình thật.** Trong container ARM64, 10 ca skip thay vì 20;
   toàn bộ logic quyết định (chuẩn hoá trước khi trung bình, chọn điểm cao nhất, áp ngưỡng, gallery
   rỗng) vẫn **chạy thật**. Nếu bám chữ "dùng mô hình thật", nhóm dòng 29–38 sẽ skip sạch trong
   container và §8 mất tác dụng bảo vệ.
3. **§6.5 của đặc tả không hề chỉ định nguồn vectơ.** Các assert của dòng 29–38 nói về *quan hệ giữa
   các vectơ*, không về giá trị embedding thật. Suy diễn nằm trong khoảng trống mà đặc tả để lại.

### 6.2. Dòng 30 dùng hai vectơ **khác hướng** thay vì "cùng hướng" — **chấp nhận; lỗi ở đặc tả**

Đặc tả dòng 30 viết: *"hai vectơ giả **cùng hướng** nhưng độ dài 1 và 100; kết quả phải nằm đúng giữa
theo góc"*. Câu này **tự mâu thuẫn**: hai vectơ cùng hướng thì không có "đúng giữa theo góc".

Kiểm bằng máy, với `v = [1, 0]` và `100·v`:

```
cùng hướng  -> cài đặt đúng: [1. 0.]        ĐB4: [1. 0.]        KHÁC NHAU? False
khác hướng  -> cài đặt đúng: [0.707 0.707]  ĐB4: [0.010 1.000]  KHÁC NHAU? True
```

Bám đúng chữ đặc tả thì ca dòng 30 **không thể đỏ** dưới ĐB4 — nó sẽ là một ca test xanh vĩnh viễn,
đúng loại "xanh vì không chạm tới chỗ cần kiểm" mà `code-review.instructions.md` §2b cảnh báo.
Người cài đặt chọn hai trục x/y, độ dài 1 và 100 (`tests/test_recognizer.py:409-412`), giữ nguyên
**ý đồ** của đặc tả (§7 ĐB4 bắt buộc dòng 30 đỏ) và bỏ chữ sai. Đã xác minh: **ĐB4 làm đỏ đúng dòng 30
và chỉ dòng 30.**

Đây là **lỗi của đặc tả, không phải của người cài đặt**. Cách xử lý đúng theo R39 là sửa đặc tả rồi
commit, không để lại lời giải thích trong hội thoại — xem §8 biên bản này.

---

## 7. 🔵 Góp ý (không chặn — người dùng quyết định)

- **G1 — Chưa có ca test nào buộc `configs/recognize.yaml` thật phải chạy được.** Bộ test dựng cấu
  hình bằng `_cfg_hop_le()` (`tests/test_recognizer.py:32-41`) với giá trị viết tay. Đã đối chiếu thủ
  công: tệp YAML thật **khớp hoàn toàn** (`rgb` / `127.5` / `128.0` / `512` / `[112, 112]`), nên hiện
  không có sai lệch. Nhưng theo đúng §4.2, một giá trị sai trong YAML **không gây lỗi** — nó chỉ làm
  mọi khuôn mặt giống nhau. Chi phí: một ca test đọc `nap_cau_hinh("configs/recognize.yaml")` rồi
  assert `channel_order == "rgb"` và `mean/scale` khớp mốc đã đo. Lợi ích: bịt cửa hỏng duy nhất mà
  38 ca hiện tại không canh. Ngoài phạm vi mã việc này (§3 cấm chạm `configs/`) — nên đưa vào `P3-02`
  hoặc mã việc `scripts/enroll.py`.
- **G2 — Nhóm dòng 29–38 không bao giờ chạy qua `enroll` → `identify` bằng vectơ thật.** Xem §6.1:
  quyết định là hợp lý, nhưng vẫn còn một khoảng trống nhỏ — không ca nào đăng ký một người từ ảnh
  thật rồi nhận diện lại người đó. Chi phí: **một** ca test, dùng 10 ảnh LFW của một danh tính để
  `enroll`, rồi `identify` ảnh thứ 11 với gallery hai người, `pytest.skip` khi thiếu mô hình/dữ liệu.
  Lợi ích: bắt được lỗi đấu nối giữa hai nửa mà cả hai nửa vẫn đúng riêng lẻ.
- **G3 — Chú thích ở `tests/test_recognizer.py:230` ghi sai tên kênh.** Dòng ghi
  `# kênh 0 (R) ứng với giá trị B gốc = 30` — trong ảnh BGR `[10, 20, 30]` thì **30 là kênh R**, không
  phải B (dòng 231 ngay dưới ghi đúng). **Assert hoàn toàn đúng**, chỉ chú thích sai. Đáng sửa vì đây
  là dòng canh "nguồn sai lầm nguy hiểm nhất" theo §4.2 — người bảo trì sau đọc chú thích sai có thể
  tưởng assert sai và "sửa" nó, làm mất lá chắn duy nhất chống lỗi thứ tự kênh.
- **G4 — `arcface_backend.py:22-42` import bảy lớp ngoại lệ từ
  `onnxruntime.capi.onnxruntime_pybind11_state`, là API nội bộ của `onnxruntime`.** Đổi lại được
  `except` đích danh thay vì `except Exception` — đánh đổi này **đúng** và đã có chú thích giải trình
  (dòng 19-21). Rủi ro có giới hạn vì `requirements.txt` ghim `onnxruntime==1.20.1`. Chỉ cần nhớ:
  nâng phiên bản `onnxruntime` phải chạy lại `pytest tests/test_recognizer.py` trước, vì lỗi sẽ là
  `ImportError` lúc nạp module chứ không phải lỗi lúc chạy.

---

## 8. Việc tiếp theo

1. **Sửa đặc tả** `docs/dac-ta/P3-01-recognizer.md` dòng 244 (§6.5 dòng 30): thay
   *"hai vectơ giả cùng hướng nhưng độ dài 1 và 100"* thành *"hai vectơ giả **khác hướng** (ví dụ trục
   x và trục y) với độ dài 1 và 100"*. Lý do ghi ở §6.2 biên bản này. Việc của `spec-writer`, đi
   **commit riêng** loại `docs(dac-ta)`.
2. **Được commit** phần mã nguồn. Gợi ý thông điệp:

   ```
   feat(recognizer): interface BoNhanDien và backend ArcFace ONNX — P3-01
   ```

3. Bốn góp ý G1–G4: G3 sửa được ngay trong vòng này nếu người dùng muốn (một dòng chú thích);
   G1 và G2 nên thành mã việc sau; G4 chỉ là ghi nhớ vận hành.

---

### Phụ lục — trạng thái cây làm việc sau review

Người review **không sửa dòng mã nào**. `sha256` ba tệp mã nguồn sau khi kết thúc:

```
02f57fabba6e6b98230772ddff0c8bf204fd8eb47f586ff3bf87c99d4c750b5e  src/recognizer/arcface_backend.py
3a1f23003dec68d3efad75121a8caef58875ecbd0b3976f93168737956eff748  src/recognizer/base.py
ab89dcae6c2e745dc47a823123bf6451eeb451e9167af393ebc7ed3dd89aad27  tests/test_recognizer.py
```

Giá trị của `arcface_backend.py` trùng với `sha256` ghi trước phép đột biến đầu tiên.

---
---

# Review P3-01-recognizer — bổ sung: ba phép đột biến còn lại và container thật

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-01-recognizer.md` |
| **Nhánh** | `feat/p3-01-recognizer` |
| **Ngày** | 2026-08-23 |
| **Phạm vi** | Ba việc còn thiếu của vòng 1: ĐB3/ĐB5/ĐB7 · container ARM64 thật · bộ cấu hình hỏng |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN — GIỮ NGUYÊN** (không phát sinh 🔴 hay 🟡 mới) |

Đây **không phải** review lại từ đầu. Ba mục dưới đây bổ sung đúng ba chỗ vòng 1 còn nợ.
`sha256` của `arcface_backend.py` trước khi bắt đầu:
`02f57fabba6e6b98230772ddff0c8bf204fd8eb47f586ff3bf87c99d4c750b5e` — **khớp** giá trị ghi ở vòng 1.

---

## 9. Ba phép đột biến còn lại — tự chạy, đủ 7/7

Quy trình mỗi phép giống vòng 1: đọc bản sao lưu → sửa → ghi bằng `newline=""` → chạy
`pytest tests/test_recognizer.py -v` → ghi ca đỏ → khôi phục từ bản sao lưu → đối chiếu `sha256`.

| # | Phép đột biến | Ca đỏ **yêu cầu** | Ca đỏ **thực tế** | Tổng kết chạy | Kết luận |
|---|---|---|---|---|---|
| **ĐB3** | `return vec.astype(np.float32)` — bỏ chia cho `do_dai` ở cuối `trich_dac_trung` | dòng 18 | **chỉ dòng 18** | 1 failed, 37 passed | ✅ có hiệu lực |
| **ĐB5** | Vẫn gọi `_doc_so_thuc`/`_doc_ty_le` (để không đổi hành vi lỗi cấu hình) nhưng gán đè `do_lech = 127.5`, `ty_le = 128.0` | dòng **13** | **chỉ dòng 13** | 1 failed, 37 passed | ✅ có hiệu lực |
| **ĐB7** | `if False:` thay cho `if so_chieu_thuc_te != embedding_dim_cfg:` | dòng **05** | **chỉ dòng 05** | 1 failed, 37 passed | ✅ có hiệu lực |

`sha256` sau **mỗi** lần khôi phục và sau khi kết thúc toàn bộ:
`02f57fabba6e6b98230772ddff0c8bf204fd8eb47f586ff3bf87c99d4c750b5e` — **khớp**.

Ba nhận xét:

1. **ĐB5 — phép quan trọng nhất trong ba phép này — đỏ đúng dòng 13.** Phép đột biến được dựng cẩn
   thận để *vẫn* gọi `_doc_so_thuc(cfg, "mean")` và `_doc_ty_le(cfg)` rồi mới gán đè, nên các ca kiểm
   lỗi cấu hình (dòng 06–08) vẫn xanh y nguyên. Nhờ vậy dòng 13 đỏ **một mình**, chứng minh nó canh
   đúng thứ nó phải canh: giá trị `mean`/`scale` thật sự chảy từ cấu hình vào phép tính, chứ không
   phải chỉ được đọc ra rồi vứt đi. Mục chuẩn hoá trong `configs/recognize.yaml` **không phải trang
   trí** — đổi giá trị ở đó có tác dụng thật.
2. **ĐB7 đỏ đúng dòng 05, không lan sang ca khác.** Chốt so `embedding_dim` với số chiều thật đọc từ
   đồ thị ONNX có tồn tại và có tác dụng: thay nhầm sang một bản MobileFaceNet khác số chiều sẽ bị
   chặn ngay ở `__init__`.
3. **Cả ba phép đều đỏ đúng một ca, không thừa.** Cộng với 4 phép của vòng 1: **7/7 phép đột biến
   của §7 đặc tả đã được người review tự xác minh**, không phép nào phải tin lời báo.

---

## 10. Container ARM64 **thật** (§8 đặc tả) — thay cho phần mô phỏng ở vòng 1

Vòng 1 chỉ mô phỏng bằng thư mục làm việc rỗng. Lần này dựng ảnh mới **từ chính cây làm việc đang
review** rồi chạy trong container:

```
docker build --platform linux/arm64 -f deploy/Dockerfile.arm64 -t faceid-arm64-review:p3-01 .
docker run --rm faceid-arm64-review:p3-01 python3 -m pytest tests/test_recognizer.py -v
```

Đúng lưu ý môi trường: build và run **từ PowerShell**, và **không** đặt `--platform` ở `docker run`.

### 10.1. Xác nhận đây là container ARM64 thật, thiếu đúng những thứ §8 nói

| Kiểm | Kết quả |
|---|---|
| `platform.machine()` | **`aarch64`** ✅ (không phải x86_64) |
| Python | 3.11.16 ✅ |
| `/app/models/` · `/app/data/` · `/app/docs/` · `/app/.git/` | **KHÔNG có** cả bốn ✅ |
| nhị phân `git` | **KHÔNG có** ✅ |
| `torch` · `ultralytics` · `onnx` · `dlib` | **KHÔNG import được** cả bốn ✅ |

(`.dockerignore` loại `data/`, `models/`, `docs/`, `.git/`, `results/`, `report/` — khớp giả định §8.)

### 10.2. Kết quả bắt buộc của §8

```
28 passed, 10 skipped in 24.30s          mã thoát = 0
```

**0 `failed`, 0 `error`** — đúng yêu cầu §8. Mười ca skip là đúng mười ca cần `models/` hoặc `data/`:
dòng 01, 02, 05 (mô hình), 17–21 (mô hình), 27, 28 (LFW). Hai mươi tám ca còn lại — gồm **toàn bộ**
nhóm `chuan_bi_dau_vao` (09–16) và **toàn bộ** nhóm `enroll`/`identify` (29–38) — **chạy thật** trên
ARM64. Đây chính là lợi ích của lựa chọn "backend giả" đã thẩm định ở §6.1 biên bản vòng 1: nếu nhóm
29–38 bám chữ "dùng mô hình thật" thì trong container sẽ skip sạch và §8 mất tác dụng bảo vệ.

### 10.3. `pytest -q` toàn kho trong container — P3-01 **không** làm đổ mã việc nào khác

```
8 failed, 335 passed, 34 skipped, 2 errors
```

Toàn bộ 8 failed + 2 errors nằm ở **`tests/test_export_detector.py`** (mã việc `P2-02`), không có ca
nào của `test_recognizer.py`. Đã chứng minh bằng máy rằng chúng **không liên quan tới P3-01**: xoá
hẳn `src/recognizer/` và `tests/test_recognizer.py` **bên trong container** rồi chạy lại toàn kho cho
ra **đúng cùng 8 failed + 2 errors** (307 passed thay vì 335 — chênh đúng 28 ca của P3-01).

Nguyên nhân: `scripts/export_detector.py:166` ném `LoiMoHinh` vì `models/yolov8n-face.pt` không có
trong container (`models/` bị `.dockerignore`), mà các ca đó **không `pytest.skip`** khi thiếu trọng
số.

> 🔵 **Ghi chú ngoài phạm vi P3-01** — đây là khiếm khuyết tồn đọng của mã việc `P2-02`: các ca
> `test_dong14–19, 27, 28, 36, 40` của `test_export_detector.py` vi phạm cùng điều khoản §8 mà P3-01
> tuân thủ ("mọi ca chạm `models/` phải skip có thông báo"). P3-01 **không** gây ra và **không** có
> trách nhiệm sửa. Nêu ở đây để người dùng quyết định có mở mã việc vá `P2-02` hay không.

---

## 11. Bộ cấu hình hỏng tự dựng — 60 biến thể, phủ đủ sáu key

Vòng 1 chỉ đọc ca dòng 08 sẵn có. Lần này tự dựng bộ riêng: **60 biến thể** trên sáu key
`model_path` · `embedding_dim` · `input_size` · `channel_order` · `mean` · `scale`, gồm cả kiểu lạ
`True` / `None` / danh sách / dict / chuỗi số / số âm / `0` / `inf` / `nan` / `2**40` / `1e-320` /
byte `NUL`.

### 11.1. Bốn key **kín hoàn toàn**

| Key | Biến thể thử | Kết quả |
|---|---|---|
| `model_path` | 8 (`""`, `None`, `True`, `123`, danh sách, dict, đường dẫn thư mục, chuỗi có byte `NUL`) | 6 × `LoiCauHinh`, 2 × `LoiMoHinh` — **không rò `ValueError`/`TypeError`** ✅ |
| `embedding_dim` | 10 (`0`, `-1`, `"512"`, `512.0`, `True`, `None`, `[512]`, `2**40`, `inf`, `nan`) | 10 × `LoiCauHinh` ✅ |
| `channel_order` | 8 (`"xyz"`, `""`, `"RGB"`, `None`, `True`, `5`, `["rgb"]`, `"rgba"`) | 7 × `LoiCauHinh`; `"RGB"` được chấp nhận do `.lower()` — **đúng ý đồ**, không phải lỗ hổng ✅ |
| `input_size` | 14 | 11 × `LoiCauHinh`; ba ca chấp nhận, xem §11.2 |

Đáng ghi nhận: kiểu tấn công `2**40` từng lọt ở `P2-02` **không tái diễn** — `embedding_dim = 2**40`
bị chặn đúng bởi chính chốt ĐB7 (không khớp 512 thật). Chuỗi có byte `NUL` cũng ra `LoiMoHinh` sạch,
không rò `ValueError` từ `pathlib`.

### 11.2. Ba lỗ hổng tìm được — **đều nằm NGOÀI danh sách đặc tả liệt kê**

⚠️ Ba mục dưới đây **không phải lỗi của người cài đặt**. §6.1 dòng 07 của đặc tả liệt kê **đích danh**
năm biến thể cần chặn (`channel_order:"xyz"`, `scale:0`, `scale:-1`, `mean:"abc"`, `input_size:[112]`)
và dòng 08 liệt kê mười hai biến thể — **người cài đặt chặn đủ cả mười bảy, không sót ca nào**.
Ba lỗ hổng này là **khiếm khuyết của đặc tả**, thuộc trách nhiệm `spec-writer` (R38/R39).

#### 🔵 G5 — `scale: inf` bị chấp nhận, và đây là **đúng thảm hoạ mà §4.2 đặc tả cảnh báo**

`_doc_ty_le` chỉ chặn `gia_tri <= 0`. Với `inf`, phép `(x − mean)/inf` cho tensor **toàn số 0** —
mô hình nhận cùng một ảnh trống cho **mọi** khuôn mặt.

Đo thật trên 6 danh tính LFW khác nhau:

| Cấu hình | Tương đồng giữa 6 **người khác nhau** | Vectơ hữu hạn? | `enroll` | `identify` người đã đăng ký |
|---|---|---|---|---|
| Đúng (`scale=128`) | min −0,1161 · tb 0,0169 · max 0,1354 | có | norm 1,0 | `('Abdoulaye_Wade', 1,0)` |
| **`scale=inf`** | **min 1,0000 · tb 1,0000 · max 1,0000** | có | norm 1,0 | `('Abdoulaye_Wade', 1,0000)` |

Đây là kịch bản nguy hiểm nhất trong cả mã việc: **hệ thống trông hoàn hảo** — vectơ chuẩn hoá đẹp,
`enroll` chạy trót lọt, `identify` trả đúng người với điểm 1,0 — trong khi thực chất **mọi khuôn mặt
đều giống hệt nhau**, tức FAR = 100 %. Không ca nào trong 38 ca hiện tại bắt được, vì cả 38 ca đều
dùng `_cfg_hop_le()` viết tay, không ca nào nạp `configs/recognize.yaml` thật (trùng với góp ý **G1**
của vòng 1 — nay đã có bằng chứng định lượng cho thấy G1 nghiêm trọng hơn vẻ ngoài của nó).

**Cách sửa** (một dòng trong `_doc_ty_le`, và một dòng tương tự cho `mean`):

```python
if not math.isfinite(gia_tri) or gia_tri <= 0:
    raise LoiCauHinh(f"Cấu hình 'scale' phải là số hữu hạn lớn hơn 0, nhận {gia_tri!r}")
```

#### 🔵 G6 — `mean` và `scale` nhận `nan` / `±inf` / `1e308` / `1e-320` → embedding **NaN** chạy xuyên hệ thống

`nan <= 0` là `False`, nên `nan` lọt qua **mọi** bộ lọc hiện có.

| Cấu hình bị chấp nhận | Vectơ | `enroll` | `identify` |
|---|---|---|---|
| `scale = nan` | toàn `NaN`, norm = `nan` | **không ném lỗi**, trả vectơ `NaN` | `(None, -inf)` |
| `mean = inf` / `-inf` / `nan` / `1e308` | toàn `NaN`, norm = `nan` | **không ném lỗi**, trả vectơ `NaN` | `(None, -inf)` |
| `scale = 1e-320` | tràn thành `inf` | không ném lỗi | — |

Hai hệ quả đáng ghi:

1. Chốt `if do_dai == 0.0` trong `trich_dac_trung` và `enroll` **không bắt được `NaN`** (`nan == 0.0`
   là `False`). Cả gallery có thể được đăng ký thành `NaN` mà không một dòng log cảnh báo nào.
2. `identify` trả `(None, -inf)` — **vi phạm hợp đồng §5** ("trả `(None, độ_tương_đồng_cao_nhất)`"):
   `-inf` không phải một độ tương đồng. Đường đi: mọi `diem` là `NaN` ⇒ `diem > diem_tot_nhat` luôn
   `False` ⇒ `diem_tot_nhat` giữ nguyên giá trị khởi tạo `float("-inf")`. Chỉ tới được khi cấu hình
   đã hỏng, nên không phải lỗi độc lập.

**Cách sửa**: cùng một chốt `math.isfinite` như G5, đặt trong `_doc_so_thuc` để phủ cả `mean` lẫn
`scale`; và đổi `if do_dai == 0.0` thành `if not math.isfinite(do_dai) or do_dai == 0.0`.

#### 🔵 G7 — `input_size` **không** được đối chiếu với đồ thị ONNX, khác hẳn `embedding_dim`

`input_size: [64, 64]` qua `__init__` trót lọt. Tới `trich_dac_trung` với ảnh 64×64 thì
`onnxruntime` ném thẳng **`InvalidArgument`** (`INVALID_ARGUMENT : Got invalid dimensions...`) —
không phải `ValueError`, không phải `LoiMoHinh`, và là **API nội bộ của `onnxruntime` rò ra ngoài**
cho người gọi, trái hợp đồng §5 của `trich_dac_trung` ("Raises: `ValueError`").

Điều này **không nhất quán** với chính lý lẽ của đặc tả: `embedding_dim` được đối chiếu với đồ thị
(ĐB7) đúng vì lý do "canh việc thay nhầm mô hình" — nhưng thay nhầm mô hình thì `input_size` cũng
lệch y hệt, mà chốt cho nó lại không có. `[2**40, 2**40]` cũng lọt qua `__init__`.

**Cách sửa**: trong `__init__`, sau khi có `dau_vao = self._session.get_inputs()[0]`, so
`dau_vao.shape[2:]` với `kich_thuoc_vao` khi hai chiều đó là số cụ thể (không phải trục động), ném
`LoiCauHinh` nêu **cả hai** cặp số — hoàn toàn đối xứng với chốt `embedding_dim` sẵn có.

### 11.3. Ba ca được chấp nhận nhưng **đúng**, không phải lỗ hổng

Ghi lại để lần review sau khỏi báo động nhầm:

- `input_size = (112, 112)` (tuple) — hợp lệ; YAML không bao giờ sinh ra tuple.
- `channel_order = "RGB"` — `.lower()` là khoan dung có chủ ý.
- `mean = 0` và `mean = -127.5` — **giá trị hợp lệ thật sự**. Chính §4.2 đặc tả liệt kê phương án
  `x/255` (tức `mean = 0`); chặn chúng mới là sai.

---

## 12. Cập nhật đối chiếu đặc tả

| Mục | Vòng 1 | Sau bổ sung |
|---|---|---|
| §7 Bảy phép đột biến | 4/7 tự xác minh | ✅ **7/7 tự xác minh**, phép nào cũng đỏ đúng ca yêu cầu |
| §8 Container ARM64 | mô phỏng bằng thư mục rỗng | ✅ **container `aarch64` thật**, 28 passed / 10 skipped / 0 failed / 0 error |
| §6.1 dòng 08 Bộ cấu hình hỏng | đọc ca sẵn có | ✅ 60 biến thể tự dựng; **đủ 17/17 biến thể đặc tả liệt kê đều ra `LoiCauHinh`**; 3 lỗ hổng ngoài danh sách → G5–G7 |
| Không hồi quy mã việc khác | 379 passed trên host | ✅ host 379 passed; container: xoá P3-01 vẫn đúng 8 failed + 2 errors của `P2-02` |

Kiểm lại máy sau khi kết thúc mọi phép đột biến (host):

| Lệnh | Kết quả |
|---|---|
| `python -m black --check --line-length 100 src tests` | 29 tệp không đổi ✅ |
| `python -m ruff check src tests` | `All checks passed!` ✅ |
| `python -m pytest -q` | **379 passed** ✅ |
| `git status --short --untracked-files=all` | y nguyên 4 tệp danh sách trắng ✅ |

---

## 13. Phán quyết sau bổ sung

🟡 **ĐẠT CÓ ĐIỀU KIỆN — GIỮ NGUYÊN phán quyết vòng 1.**

Lý do giữ nguyên, không nâng và không hạ:

- **Không hạ xuống 🔴.** Ba lỗ hổng G5–G7 nằm **ngoài** danh sách biến thể mà §6.1 dòng 07–08 liệt kê
  đích danh. Người cài đặt chặn **đủ 17/17** biến thể được yêu cầu, và **7/7** phép đột biến đều có ca
  đỏ đúng như đặc tả đòi. Trả lại mã nguồn vì một yêu cầu chưa từng được viết ra là vi phạm nguyên
  tắc "không mở rộng đặc tả khi review" — và sẽ đổ lỗi nhầm người.
- **Không nâng lên ✅.** Vẫn còn góp ý, và ba góp ý mới có bằng chứng định lượng nên đáng được người
  dùng cân nhắc trước khi khép Phase 3.

Ba việc còn thiếu của vòng 1 nay đã xong, không phát sinh 🔴 hay 🟡 mới.

---

## 14. Việc tiếp theo (thay cho §8 biên bản vòng 1)

1. **Được commit** phần mã nguồn, thông điệp như vòng 1 đề xuất:
   `feat(recognizer): interface BoNhanDien và backend ArcFace ONNX — P3-01`
2. **Sửa đặc tả** — việc của `spec-writer`, đi **commit riêng** loại `docs(dac-ta)`:
   - Dòng 244 (§6.5 dòng 30): sửa "cùng hướng" thành "khác hướng" — đã nêu ở §6.2 vòng 1.
   - §6.1 dòng 07: bổ sung `mean`/`scale` = `inf`, `-inf`, `nan` vào danh sách "giá trị ngoài miền".
   - §5: nêu rõ `input_size` phải được đối chiếu với đồ thị ONNX, đối xứng với `embedding_dim`.
3. **G5–G7 nên gộp thành một mã việc vá nhỏ** (`P3-01b`, ước lượng ~6 dòng mã + ~6 ca test): thêm
   chốt `math.isfinite` cho `mean`/`scale`, chốt `NaN` cho `do_dai`, và chốt `input_size` với đồ thị.
   **G5 đáng làm trước tiên** — nó là cửa duy nhất còn lại dẫn tới đúng thảm hoạ "mọi khuôn mặt giống
   nhau mà không báo gì" mà §4.2 đặc tả dựng cả nhóm dòng 27–28 để phòng.
4. Góp ý cũ: **G1 nay đã có bằng chứng định lượng** (xem §11.2 G5) — nên nâng độ ưu tiên, gộp luôn
   vào `P3-01b`. G2 giữ nguyên. G3 (chú thích sai tên kênh) sửa một dòng. G4 chỉ là ghi nhớ vận hành.
5. 🔵 Ngoài P3-01: cân nhắc mở mã việc vá `tests/test_export_detector.py` (`P2-02`) cho đủ điều kiện
   §8 trong container — xem §10.3.

---

### Phụ lục bổ sung — trạng thái cây làm việc

Người review **không sửa dòng mã nào**. Mọi phép đột biến đều khôi phục từ bản sao lưu đặt ngoài repo
(thư mục tạm), đối chiếu `sha256` sau từng lần. Giá trị cuối cùng:

```
02f57fabba6e6b98230772ddff0c8bf204fd8eb47f586ff3bf87c99d4c750b5e  src/recognizer/arcface_backend.py
3a1f23003dec68d3efad75121a8caef58875ecbd0b3976f93168737956eff748  src/recognizer/base.py
ab89dcae6c2e745dc47a823123bf6451eeb451e9167af393ebc7ed3dd89aad27  tests/test_recognizer.py
```

Cả ba **trùng khớp** giá trị ghi ở phụ lục vòng 1. Không commit.
