# Review P2-06b — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-06b-doi-khang-backend.md` |
| **Nhánh** | `feat/p2-06b-doi-khang-backend` (mã **chưa commit** lúc review) |
| **Ngày** | 2026-09-03 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — 0 lỗi 🔴 CHẶN-A, 0 lỗi 🔴 CHẶN-B, 0 lỗi 🟡 CẦN SỬA, 4 mục 🔵 GÓP Ý. **Được commit ngay**, không có việc nào phải sửa. |

**Nguồn số liệu**: toàn bộ con số trong biên bản này đến từ **lượt chạy của người dùng ngày 03/09/2026**,
gồm 35 lệnh `K01`–`K35` do người review soạn cộng ba lệnh bổ sung `K36`–`K38`. Không con số nào lấy
từ bảng tự kiểm của người cài đặt (R5, R6, `code-review.instructions.md` §0). Mỗi dữ kiện dưới đây dẫn
mã lệnh `[Kxx]` đã sinh ra nó; lệnh được chép nguyên văn để chạy lại được mà không cần tệp kịch bản.

Môi trường lượt chạy: `pc_x86` — Windows, Python 3.12.5, pytest 9.1.1, ruff 0.16.1 `[K03]` `[K37]`;
container `faceid:arm64` qua Docker Desktop bind-mount `[K07]`–`[K09]`.

---

## 1. Kết quả kiểm máy

### A. Ba lệnh nền trên host

| # | Lệnh | Kết quả |
|---|---|---|
| [K01] | `python -m black --check --line-length 100 src/detector/factory.py scripts/benchmark_detect.py tests/test_detector_factory.py tests/test_benchmark_detect.py` | `4 files would be left unchanged.` ✅ |
| [K02] | `python -m ruff check src/detector/factory.py scripts/benchmark_detect.py tests/test_detector_factory.py tests/test_benchmark_detect.py` | `All checks passed!` ✅ |
| [K03] | `python -m pytest tests/test_detector_factory.py tests/test_benchmark_detect.py -v -m "not slow"` | **70 passed, 3 deselected**, 9,94 s ✅ — khớp đúng dự kiến (7 ca không-`slow` của `test_detector_factory.py` + 63 ca của `test_benchmark_detect.py`). **Đây là mốc so sánh của ĐB1 và ĐB3.** |
| [K04] | `python -m pytest -q -m "not slow"` | **453 passed, 14 deselected**, 0 failed, 17,74 s ✅ |
| [K05] | `python -m pytest tests/test_detector_factory.py tests/test_benchmark_detect.py -q` | **73 passed**, **0 skipped**, 5,32 s ✅ — ca `slow` dòng 05 **chạy thật**, không skip. **Mốc so sánh của ĐB2.** |
| [K06] | `python -m pytest -q` | **467 passed**, 0 failed, 65,39 s ✅ — khớp 458 (mốc `P2-06`) + 9 ca mới |

Chín ca mới phân bố đúng như §6 đặc tả mô tả: 5 ca ở `tests/test_detector_factory.py` (dòng 01–05,
trong đó dòng 05 mang `@pytest.mark.slow`) và 4 ca ở `tests/test_benchmark_detect.py` (dòng 06–09).
Con số `453 = 467 − 14 slow` `[K04]` `[K06]` tự nhất quán.

### B. Ba lệnh nền trong container `faceid:arm64` (R43 — không dựng image mới)

| # | Lệnh | Kết quả |
|---|---|---|
| [K07] | `docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m black --check --line-length 100 <4 tệp>` | `4 files would be left unchanged.` ✅ |
| [K08] | `docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m ruff check <4 tệp>` | **`Found 4 errors.`** — cả bốn là `EXE002 The file is executable but no shebang is present`, một lỗi/tệp, đều ở `:1:1` ⚠️ **artifact môi trường, không phải khuyết tật mã — xem §1.1** |
| [K09] | `docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"` | **452 passed, 1 skipped, 14 deselected**, 0 failed, 739,58 s ✅ — khớp mốc `P2-06` (444/1/13) + 8 ca mới không-`slow`. Ca skip là `test_dong30` (container không có `git`) |

#### 1.1. Phân định `EXE002` — không tính lỗi của mã việc

Ba dữ kiện độc lập, đủ để kết luận dứt điểm:

1. **File mode trong git index** (`git ls-files -s`, chỉ-đọc): cả bốn tệp của mã việc đều `100644`.
   Bốn tệp **ngoài** mã việc (`src/common/config.py`, `src/detector/ncnn_backend.py`,
   `tests/test_yolo_face.py`, `scripts/export_detector.py`) cũng `100644`. **Không tệp nào mang bit
   thực thi trong repo** — nghĩa là không có thay đổi quyền nào do mã việc này gây ra.
2. **[K36]** — cùng lệnh `ruff` trong container, chạy trên ba tệp **ngoài** danh sách trắng:
   `Found 3 errors.`, cả ba là `EXE002` (`src/common/config.py:1:1`, `src/detector/ncnn_backend.py:1:1`,
   `tests/test_yolo_face.py:1:1`). Rule này đánh **mọi** tệp `.py` của repo khi soi qua bind-mount.
3. **[K37]** — `ruff 0.16.1` ở **cả host lẫn container**, cùng `pyproject.toml`
   (chỉ có `[tool.ruff] line-length = 100`, không `select`/`ignore`). Biến duy nhất khác nhau giữa
   `[K02]` xanh và `[K08]` đỏ là **quyền tệp**: Docker Desktop gắn ổ Windows với mode 0755 cho mọi tệp,
   còn Windows không có khái niệm bit thực thi nên host không kích hoạt rule.

⇒ `EXE002` là **artifact của bind-mount Windows→Linux**, không chặn `P2-06b`. Nhưng nó sẽ **tái diễn ở
mọi mã việc sau**, nên được ghi thành mục 🔵-1 với hai hướng xử lý để người dùng chọn.

### C. Phạm vi tệp và quét mẫu vi phạm

| # | Lệnh | Kết quả |
|---|---|---|
| [K10] | `git status --short --untracked-files=all` | **đúng 4 dòng `M`**: `scripts/benchmark_detect.py`, `src/detector/factory.py`, `tests/test_benchmark_detect.py`, `tests/test_detector_factory.py`. Không tệp `??` nào ✅ — khớp tuyệt đối danh sách trắng §2, **CA-5 không thành lập** |
| [K11] | `git --no-pager diff --stat` | `4 files changed, 219 insertions(+), 52 deletions(-)` — `benchmark_detect.py` 52 · `factory.py` 55 · `test_benchmark_detect.py` 102 · `test_detector_factory.py` 62. Không có `requirements*.txt`, `configs/`, `models/` ✅ |
| [K12] | `git status --short --untracked-files=all \| Select-String -Pattern '\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$'` | không in gì ✅ — **CA-4 không thành lập** |
| [K13] | `Select-String -Path 'scripts\benchmark_detect.py' -Pattern 'tra_ten_backend' -SimpleMatch` | **đúng 1 dòng**: `:459  ten_backend = detector_factory.tra_ten_backend(m)`. Không dòng nào trong thân `do_mot_cau_hinh` (`:169`–`:239`) ✅ — §5.1 xác nhận bằng dữ kiện |
| [K14] | `Select-String -Path 'src\detector\factory.py','scripts\benchmark_detect.py' -Pattern '["'']onnx["'']\|["'']ncnn["'']'` | **3 dòng** (dự kiến 2) — hai dòng hằng số ở `factory.py:21,22` ✅ + `benchmark_detect.py:254` ⚠️ **không tính lỗi — xem §1.2** |
| [K15] | `Select-String -Path 'scripts\benchmark_detect.py','tests\test_benchmark_detect.py' -Pattern '_ten_backend_du_kien' -SimpleMatch` | không in gì ✅ — hàm đã xoá đúng §4.2 |
| [K16] | `Select-String -Path <4 tệp> -Pattern 'except\s*:\|except Exception:\s*pass\|assert True\|import torch\|[A-Z]:\\\|/home/\|/Users/'` | không in gì ✅ — CB-4, CB-6, CA-9, đường dẫn tuyệt đối: đều không thành lập |
| [K17] | `Select-String -Path 'src\detector\factory.py' -Pattern '\bprint\('` | không in gì ✅ — **CA-2 không thành lập** |
| [K38] | `git status --short --untracked-files=all` (chạy lại sau cả ba phép đột biến) | đúng 4 dòng `M`, không sót tệp đột biến nào ✅ — cây làm việc trở về đúng bản người cài đặt bàn giao |

#### 1.2. Dòng thứ ba của `[K14]` — vì sao KHÔNG phải lỗi

```python
# scripts/benchmark_detect.py:254 — trong _lay_phien_ban_ncnn
return importlib.metadata.version("ncnn")
```

Chuỗi `"ncnn"` ở đây là **tên gói PyPI** truyền cho `importlib.metadata.version`, không phải **tên
backend**. Hai khái niệm này trùng chuỗi một cách ngẫu nhiên nhưng độc lập về danh nghĩa: tên gói do
PyPI quy định, tên backend do `factory.py` quy định. Thay nó bằng `detector_factory.TEN_BACKEND_NCNN`
sẽ **ghép hai thứ độc lập vào một hằng** — nếu sau này một trong hai đổi, chỗ còn lại đổi theo một cách
âm thầm. Đó đúng là loại lỗi mà chính mã việc `P2-06b` sinh ra để chống. Ghi rõ ở đây vì đây là điểm
người đọc biên bản về sau dễ hiểu nhầm thành vi phạm §7. Phương án làm rõ danh nghĩa — nếu người dùng
muốn — ghi ở 🔵-3.

Ràng buộc §7 của đặc tả ("trong `benchmark_detect.py` phải rỗng") vẫn được thoả về **thực chất**: không
có tên backend nào viết cứng trong script; khối `software` của meta dùng khoá
`detector_factory.TEN_BACKEND_NCNN` (`benchmark_detect.py:587`), không dùng chuỗi trần.

---

## 2. Ba phép đột biến — dựng lại từ đầu, kể cả phép người cài đặt nói đã chạy

Quy trình mỗi phép: sao lưu ra `$env:TEMP\p2-06b-backup\` `[K19]` → ghi `sha256` `[K20]` → đột biến bằng
`[System.IO.File]::WriteAllText(..., UTF8Encoding($false))` → **xác nhận đột biến đã ăn** → `pytest` →
khôi phục **bằng bản sao lưu ngoài repo** (không `git checkout`, vì mã chưa commit) → đối chiếu `sha256`.

`sha256` mốc `[K20]`: `factory.py` = `2E23A8BD…FB28C` · `benchmark_detect.py` = `CA4F6F24…65025`.
Cả ba lần khôi phục `[K25]` `[K30]` `[K35]` đều **trùng khít** mốc này ⇒ không thay đổi nào bị bỏ lại
trong mã sản phẩm (`code-review.instructions.md` §2b).

| # | Phép đột biến | Lệnh sửa | Ca **phải** đỏ theo §7 | Kết quả thật | |
|---|---|---|---|---|---|
| ĐB1 | Trong `do_mot_cau_hinh`, đổi nguồn của `backend` sang phép đoán theo đường dẫn | `'ten_backend = detector.ten_backend'` → `'ten_backend = detector_factory.tra_ten_backend(duong_dan_mo_hinh)'` `[K21]`, xác nhận `[K22]` | **dòng 06** | **3 failed, 67 passed, 3 deselected** `[K23]` | ✅ xem §3 |
| ĐB2 | `tra_ten_backend` luôn trả `TEN_BACKEND_ONNX` | `'if p.suffix == _DUOI_ONNX:'` → `'if True:  # DB2'` `[K26]`, xác nhận `[K27]` | dòng 02, 05, 10 | **8 failed, 65 passed** `[K28]` | ✅ |
| ĐB3 | Bỏ khoá `ncnn` khỏi khối `software` | xoá `'detector_factory.TEN_BACKEND_NCNN: phien_ban_ncnn,'` `[K31]`, xác nhận `[K32]` | dòng 07 | **2 failed, 68 passed, 3 deselected** `[K33]` | ✅ |

### ĐB2 `[K28]` — chi tiết

Ba ca bắt buộc, đỏ đúng chỗ:

- `test_dong02_thu_muc_co_param_tra_ve_ncnn` — `assert 'onnx' == 'ncnn'` (dòng 02)
- `test_dong05_hai_nguon_dong_thuan_tren_mo_hinh_that` — ca `slow`, **chạy thật** (`[K05]` chứng minh
  không skip) — `LoiMoHinh: Không tìm thấy tệp mô hình ONNX: models\yolov8n-face-320_ncnn_model` (dòng 05)
- `test_dong53_dry_run_co_cot_backend_khong_ghi_tep` — `assert 'ncnn' in '…| onnx | 1 |…'` (dòng 10)

Năm ca đỏ kèm — **không phải "đỏ lan man"** mà là hệ quả tất yếu của việc hai hàm dùng chung một bộ điều
kiện: `test_dong03`, `test_dong04` (`DID NOT RAISE LoiCauHinh`), `test_dong24`, `test_dong25`,
`test_dong26`.

Ba ca cuối đáng ghi riêng: chúng đỏ vì `tao_bo_phat_hien` rơi xuống `YoloFaceDetector` khi
`tra_ten_backend` bị làm hỏng. Đây là **bằng chứng chạy được cho §5.2** — nếu `tao_bo_phat_hien` giữ một
bản sao điều kiện riêng thay vì uỷ quyền, ba ca này đã xanh và ĐB2 đã không chạm tới chúng.

### ĐB3 `[K33]` — chi tiết

- `test_dong56_meta_software_co_khoa_ncnn` — `assert 'ncnn' in {'python': '3.12.5', 'onnxruntime': '1.20.1', 'opencv-python': '4.13.0', 'numpy': '2.2.0'}` (dòng 07)
- `test_dong57_thieu_goi_ncnn_khong_hong_luot_do` — `KeyError: 'ncnn'` (đỏ kèm tất yếu, cùng đọc một khoá)

Log của `test_dong57` ở lượt `[K33]` đồng thời là **bằng chứng chạy được cho §4.2 dòng 08**:
`WARNING scripts.benchmark_detect:benchmark_detect.py:564 Không tra được phiên bản gói ncnn: No package
metadata was found for ncnn`, sau đó `main` vẫn `return 0`, bảng tổng kết vẫn in, hai tệp kết quả vẫn ghi.
Thiếu một dòng metadata **không** làm hỏng một lượt đo dài.

---

## 3. ĐB1 — lỗ hổng của `P2-06` đã được bịt ⭐

Đây là lý do tồn tại của cả mã việc, nên tách thành mục riêng.

**Sự kiện `P2-06`** (biên bản `docs/review/P2-06-benchmark-ncnn.review.md`, ĐB5, lệnh [40–43]): phép đột
biến thay `detector.ten_backend` bằng phép đoán theo đuôi đường dẫn — đúng thứ mà §6.1 của `P2-06` gọi là
yêu cầu trung tâm và cấm tuyệt đối — cho kết quả **59 passed, 0 failed**. Mã đột biến **sống sót**. Ràng
buộc trung tâm khi đó chỉ được canh bằng `grep`, một dụng cụ không chạy tự động ở bất kỳ vòng nào sau này.

**Kết quả lần này** `[K23]`, cùng phép đột biến, dựng lại từ đầu bởi người dùng:

```
3 failed, 67 passed, 3 deselected in 9.64s
```

| Ca đỏ | Chứng cứ |
|---|---|
| ⭐ `test_dong55_backend_lay_tu_doi_tuong_khong_tu_duong_dan` | `AssertionError: assert {'onnx'} == {'ncnn'}` tại `tests/test_benchmark_detect.py:1023` — **đúng ca canh dòng 06, đúng dạng sai lệch mà đặc tả mô tả** |
| `test_dong45_thu_muc_ncnn_cho_backend_ncnn` | `LoiCauHinh: Không nhận dạng được backend từ đường dẫn: '…\gia_ncnn_model'`, ném từ `src/detector/factory.py:49` qua `scripts/benchmark_detect.py:212` |
| `test_dong47_tron_hai_loai_csv_co_hai_gia_tri_backend` | `assert 1 == 0`; stdout `Benchmark thất bại: Không nhận dạng được backend…`; log `ERROR benchmark_detect.py:540` |

Hai ca đỏ kèm được **dự đoán trước khi có số liệu** trong danh sách lệnh (mục kết quả mong đợi của `[K23]`),
và trùng khít với kết quả thật — dấu hiệu cho thấy mô hình về hành vi của mã là đúng, không phải trùng hợp.

**Kết luận**: mục A của đặc tả có răng thật. Ràng buộc "cột `backend` của CSV phải nói *cái gì đã thật sự
sinh ra con số bên cạnh*, không nói *tên tệp trông như gì*" giờ được canh bởi một ca test chạy tự động ở
mọi lượt `pytest`, không còn phụ thuộc vào việc có ai nhớ chạy `grep` hay không. Đây là ràng buộc bảo vệ
**tính trung thực của số liệu** (R5, R6): nếu nó trôi, cột `backend` trong `results/*.csv` — và từ đó bảng
so sánh ONNX vs NCNN ở Chương 4 — có thể mô tả sai nguồn gốc của chính con số nó đứng cạnh.

---

## 4. Ba ràng buộc kiến trúc — đọc mã **và** chạy máy

Mỗi ràng buộc được xác nhận bằng hai loại bằng chứng độc lập.

### §5.1 — `tra_ten_backend` không được dùng trong đường ghi số đo: **ĐẠT**

| Loại bằng chứng | Nội dung |
|---|---|
| Đọc mã | `scripts/benchmark_detect.py:212` — `ten_backend = detector.ten_backend`, đọc từ chính đối tượng vừa chạy phép đo; giá trị đi thẳng vào bản ghi ở `:228`. `tra_ten_backend` chỉ xuất hiện ở `:459`, trong nhánh `if args.dry_run:` (`:452`–`:467`), và nhánh này `return 0` ở `:467` **trước** vòng đo — không có lối nào cho giá trị phỏng đoán chạm vào CSV. Comment `:457-458` ghi rõ lý do |
| Chạy máy | `[K13]` grep cho đúng một dòng, không dòng nào trong `do_mot_cau_hinh`; `[K23]` ĐB1 làm đỏ đúng `test_dong55` |

### §5.2 — một bộ điều kiện nhận dạng, hai hàm: **ĐẠT**

| Loại bằng chứng | Nội dung |
|---|---|
| Đọc mã | Cơ chế dùng chung là **uỷ quyền hàm**, không phải hằng hay bảng tra: `src/detector/factory.py:75` — `ten_backend = tra_ten_backend(p)`, rồi `:77` phân nhánh theo hằng `TEN_BACKEND_ONNX`. Điều kiện nhận dạng chỉ tồn tại **một bản**, ở `factory.py:43-53`; hai hằng dữ liệu `_DUOI_ONNX` (`:18`), `_TEP_NHAN_DANG_NCNN` (`:19`) giữ nguyên từ `P2-05`, không chép lại. **Thông báo lỗi**: chỉ có một chỗ `raise LoiCauHinh` trong cả tệp (`:49-53`), nằm bên trong `tra_ten_backend`; `tao_bo_phat_hien` không tự ném chuỗi nào ⇒ hai lối vào cho ra chuỗi giống hệt **do cấu trúc**, không do trùng hợp |
| Chạy máy | `test_dong04` (`tests/test_detector_factory.py:114-123`) assert `str(e1) == str(e2)`, xanh ở `[K03]`; `[K28]` ĐB2 làm đỏ `test_dong24`/`test_dong25`/`test_dong26` — ba ca đi qua `tao_bo_phat_hien` — chứng minh `tao_bo_phat_hien` thật sự phụ thuộc vào `tra_ten_backend`; `test_dong05` (`slow`, chạy thật theo `[K05]`) buộc hằng trong `factory.py` phải khớp thuộc tính mà hai lớp backend thật trả về |

### §4.2 dòng 08 — thiếu gói `ncnn` không làm hỏng lượt đo dài: **ĐẠT**

| Loại bằng chứng | Nội dung |
|---|---|
| Đọc mã | `scripts/benchmark_detect.py:561-565`: `try` bọc **đúng một** lệnh gọi `_lay_phien_ban_ncnn()`, bắt **đúng một** loại ngoại lệ hẹp `importlib.metadata.PackageNotFoundError` (lớp con của `ModuleNotFoundError`), **có ghi log** `logger.warning` ở `:564` với lazy formatting, rồi gán `"khong-xac-dinh"`. Không phải `except:` trần, không nuốt im lặng (CB-4 không thành lập). **Vị trí trong luồng**: khối này nằm **sau** vòng đo (`:519-542`) và **trước** khi ghi tệp (`:614`) — số đo của cả 12 ô đã nằm trong bộ nhớ khi việc tra phiên bản diễn ra. Không hàng nào của ma trận bị bỏ, nên không phát sinh nhu cầu đánh dấu hàng bị bỏ trong CSV. `_lay_phien_ban_ncnn` tách thành hàm mức module (`:242-254`) nên monkeypatch được |
| Chạy máy | `test_dong57` xanh ở `[K03]`; ở `[K33]` log cho thấy nhánh chạy đúng: `WARNING … Không tra được phiên bản gói ncnn`, `main` vẫn `return 0`, tệp vẫn ghi; `[K28]`/`[K33]` chứng minh khoá `software["ncnn"]` có ca canh |

---

## 5. Đối chiếu đặc tả

### §2 Phạm vi file

| Mục | Kết luận | Chứng cứ |
|---|---|---|
| Đúng 4 tệp danh sách trắng | ✅ | `[K10]`, `[K11]`, `[K38]` |
| Không sửa `yolo_face.py`, `ncnn_backend.py`, `configs/**`, `requirements*.txt`, `models/**` | ✅ | `[K11]` — `diff --stat` chỉ liệt kê 4 tệp |
| Không thêm gói, không `docker build` | ✅ | `[K11]` không đụng `requirements*.txt`; `[K07]`–`[K09]` dùng image `faceid:arm64` có sẵn (R43) |

### §4 Giao diện

| Mục | Kết luận | Chứng cứ |
|---|---|---|
| §4.1 `TEN_BACKEND_ONNX` / `TEN_BACKEND_NCNN` | ✅ | `factory.py:21-22`, `[K14]` |
| §4.1 `tra_ten_backend(duong_dan: Path \| str) -> str`, docstring Google tiếng Việt, không nạp mô hình | ✅ khớp từng ký tự | `factory.py:25-53` |
| §4.1 `tao_bo_phat_hien` gọi lại `tra_ten_backend` | ✅ | `factory.py:75`, xác nhận bằng ĐB2 `[K28]` |
| §4.2 Xoá `_ten_backend_du_kien` | ✅ | `[K15]` không in gì |
| §4.2 Dry-run gọi thẳng `tra_ten_backend(m)` | ✅ | `benchmark_detect.py:459`, `[K13]` |
| §4.2 `software` thêm khoá `ncnn`, gói vắng → giá trị báo vắng, không ném | ✅ | `benchmark_detect.py:587` + `:561-565`, `[K33]` |

### §6.1 `tests/test_detector_factory.py`

| # | Yêu cầu | Kết luận | Chứng cứ |
|---|---|---|---|
| 01 | `.onnx` → `"onnx"`, không nạp mô hình | ✅ | `test_dong01`, `[K03]` |
| 02 | Thư mục có `model.ncnn.param` → `"ncnn"` | ✅ **có răng** | `test_dong02`; ĐB2 làm đỏ `[K28]` |
| 03 | Đường dẫn lạ → `LoiCauHinh`, ba ca | ✅ | `test_dong03` (`.pt`, không đuôi, thư mục rỗng); ĐB2 làm đỏ `[K28]` |
| 04 | Thông báo lỗi giống hệt `tao_bo_phat_hien` | ✅ | `test_dong04` assert `str(e1) == str(e2)`, `[K03]`; ĐB2 làm đỏ `[K28]` |
| 05 | Hai nguồn đồng thuận trên mô hình thật (`slow`) | ✅ **chạy thật, không skip** | `[K05]` 73 passed / 0 skipped; ĐB2 làm đỏ `[K28]` |

### §6.2 `tests/test_benchmark_detect.py`

| # | Yêu cầu | Kết luận | Chứng cứ |
|---|---|---|---|
| 06 | Bản ghi lấy `backend` từ đối tượng, không từ tên đường dẫn | ✅ ⭐ **có răng** | `test_dong55`; **ĐB1 làm đỏ** `[K23]` — xem §3 |
| 07 | Meta có `software["ncnn"]` | ✅ **có răng** | `test_dong56`; ĐB3 làm đỏ `[K33]` |
| 08 | Thiếu gói `ncnn` → meta vẫn ghi, lượt đo không hỏng | ✅ | `test_dong57` xanh `[K03]`; log nhánh xử lý quan sát được ở `[K33]` |
| 09 | `--dry-run` không khởi tạo mô hình nào | ✅ | `test_dong58` đếm số lần gọi factory `== 0`, xanh `[K03]`; `[K13]` cho thấy dry-run không đi qua `tao_bo_phat_hien` |
| 10 | `--dry-run` vẫn in đúng cột backend | ✅ **có răng** | `test_dong53`; ĐB2 làm đỏ `[K28]` |
| 11 | Mọi ca cũ vẫn xanh | ✅ | `[K06]` 467 passed = 458 (`P2-06`) + 9; `[K09]` container 452 passed |

Ghi chú về dòng 10: docstring của `test_dong53` (`tests/test_benchmark_detect.py:952-964`) nêu rõ tên thư
mục mô hình **cố tình không chứa chuỗi con `ncnn`**, để chuỗi `ncnn` trong `stdout` không thể đến từ cột
đường dẫn được in ra. Không có ca này thì assert dòng 10 xanh giả kể cả khi cột backend sai — đây là chỗ
người cài đặt xử lý cẩn thận hơn mức đặc tả đòi hỏi.

### §8 Ràng buộc kỹ thuật · §9 Ngoài phạm vi

| Mục | Kết luận | Chứng cứ |
|---|---|---|
| `black` 100, `ruff` sạch, type hints, docstring tiếng Việt Google | ✅ | `[K01]`, `[K02]`, `[K07]`; đọc `factory.py:25-40`, `:57-73`, `benchmark_detect.py:242-254` |
| Không thêm gói; `importlib.metadata` thuộc thư viện chuẩn | ✅ | `[K11]` |
| `factory.py` không import `ncnn`/`onnxruntime` ở mức module | ✅ | `factory.py:9-13` chỉ import `pathlib`, `src.common.*`, hai lớp backend; `ncnn_backend.py` để `import ncnn` trong thân hàm (`:133`, `:187`) |
| Giữ nguyên cỡ mẫu, warm-up, lược đồ CSV, cách tổng hợp | ✅ | `test_dong54` (lược đồ CSV) và toàn bộ 47 ca cũ vẫn xanh `[K03]`; `_COT_CSV` `benchmark_detect.py:76-87` không đổi |
| Không làm việc thuộc §9 (🔵-4 cột định danh mô hình, 🔵-6 marker, `P2-05b`, chạy ma trận) | ✅ | `[K11]` — không tệp nào ngoài 4 tệp bị đụng; không tệp nào trong `results/` được sinh ra `[K10]` |
| **Không commit** | ✅ | `[K10]` cho thấy 4 tệp còn ở trạng thái `M`, chưa vào index |

---

## 6. Lỗi phải sửa

**Không có.** 0 lỗi 🔴 CHẶN-A · 0 lỗi 🔴 CHẶN-B · 0 lỗi 🟡 CẦN SỬA.

Hai điểm sống còn được soi riêng theo `code-review.instructions.md` §6:

- **Trung thực số liệu (R5)**: không giá trị mặc định giả, không số ví dụ trong docstring trông như kết
  quả đo, không test dùng số bịa. Ngược lại, mã việc này **củng cố** tính trung thực số liệu — xem §3.
- **An toàn phần cứng**: mã việc không đụng tới `src/actuator/**` hay bất kỳ đường điều khiển thiết bị
  nào; không phát sinh rủi ro fail-safe.

---

## 7. 🔵 Góp ý (không chặn — người dùng quyết định)

### 🔵-1 — `ruff` trong container luôn đỏ vì `EXE002`: vấn đề **quy trình**, sẽ tái diễn

**Hiện tượng**: `[K08]` `Found 4 errors.`, `[K36]` `Found 3 errors.` trên tệp ngoài mã việc — cùng một
rule `EXE002`, đánh mọi tệp `.py` khi soi qua bind-mount Windows→Linux (`[K37]`: cùng `ruff 0.16.1`, cùng
`pyproject.toml`, khác duy nhất quyền tệp 0755 do Docker Desktop gán).

**Vì sao đáng xử lý**: từ nay **mọi** lượt review sau đều gặp ô đỏ này. Một ô đỏ mà lần nào cũng phải
giải trình rồi bỏ qua sẽ dần bị đọc lướt, và đến lúc nó đỏ vì lý do thật thì không ai để ý nữa.

**Hai hướng, người dùng chọn một** — làm ở mã việc quy trình riêng, commit `chore(quy-trinh)`:

- (a) **Bỏ `ruff` trong container** khỏi bộ lệnh kiểm chuẩn. Lý lẽ: host đã phủ lint bằng đúng phiên bản
  `ruff`; container tồn tại để kiểm **tính khả chuyển của hành vi runtime**, không phải kiểm style.
  Chi phí: 0 dòng mã, chỉ sửa tài liệu quy trình.
- (b) **Thêm `EXE002` vào `ignore`** của `[tool.ruff.lint]` trong `pyproject.toml`. Chi phí: 3 dòng.
  Đánh đổi: tắt rule cho cả repo, kể cả khi sau này có tệp thật sự cần shebang (`scripts/*.py` chạy trực
  tiếp trên Pi 5).

⚠️ `pyproject.toml` **ngoài danh sách trắng §2** của `P2-06b`, nên không được sửa trong mã việc này.

### 🔵-2 — Marker `slow` chưa đăng ký (`PytestUnknownMarkWarning`) — nợ có sẵn

Cảnh báo lặp ở mọi lượt `[K03]`–`[K06]`, `[K09]`, tại `tests/test_detector_factory.py:40,47,126` và ở
nhiều tệp ngoài mã việc (`test_export_detector.py`, `test_export_detector_ncnn.py`, `test_ncnn_backend.py`,
`test_yolo_face.py`). Nguồn gốc: `pyproject.toml` không khai `[tool.pytest.ini_options] markers`.

Đây là **hiện tượng có sẵn từ trước `P2-06b`** — đã được ghi ở `P2-05` 🔵-5 và `P2-06` 🔵-6. Mã việc này
chỉ làm nó xuất hiện thêm một lần (ca `slow` mới ở dòng 05). `pyproject.toml` ngoài danh sách trắng.
Gộp chung với 🔵-1 thành một mã việc dọn dẹp `chore(quy-trinh)` là hợp lý — cả hai đều sửa cùng một tệp.

### 🔵-3 — Tách danh nghĩa "tên gói PyPI" khỏi "tên backend"

`scripts/benchmark_detect.py:254` dùng chuỗi trần `"ncnn"` làm **tên gói** cho
`importlib.metadata.version` (xem §1.2 — không phải lỗi). Nếu muốn hai danh nghĩa tách bạch tường minh,
có thể đặt một hằng riêng trong `benchmark_detect.py`:

```python
_TEN_GOI_NCNN = "ncnn"  # tên gói PyPI — KHÔNG phải tên backend, xem factory.TEN_BACKEND_NCNN
```

Lợi: người đọc `[K14]` về sau không phải suy luận lại. Chi phí: 2 dòng, và bản thân comment mới là thứ
mang thông tin, không phải hằng số. Người dùng quyết.

### 🔵-4 — Gói `ncnn` vắng mặt vẫn làm chết cả 12 ô ma trận (hành vi có từ `P2-06`)

Ngoài phạm vi `P2-06b` — §4.2 chỉ yêu cầu bảo vệ **dòng metadata**, và yêu cầu đó đã đạt. Nhưng nếu máy
đo thiếu gói `ncnn`, sáu ô NCNN sẽ chết ở `src/detector/ncnn_backend.py:133-135` (`LoiMoHinh`), và
`scripts/benchmark_detect.py:539-542` bắt `LoiMoHinh` rồi `return 1` ⇒ **mất cả 12 ô, kể cả 6 ô ONNX đã
đo xong**. Trên Pi 5, một lượt 12 ô mất hàng chục phút.

Phương án — nếu người dùng thấy đáng, mở mã việc riêng: bắt lỗi ở **mức từng ô**, ghi ô hỏng vào bảng tổng
kết với trạng thái rõ ràng và ghi lý do vào `notes` của meta, thay vì bỏ cả lượt. Ràng buộc kèm theo: ô bị
bỏ **phải** phân biệt được với ô đo được trong CSV, nếu không thì bảng Chương 4 sẽ im lặng thiếu dòng —
đúng loại lỗi trung thực số liệu mà `P2-06b` vừa dựng hàng rào để chống.

---

## 8. Việc tiếp theo

1. **Commit và gộp nhánh — việc của người dùng.** Chỉ người dùng được `git commit`/`push` (R42);
   người review không chạy lệnh ghi. Mã đã có biên bản phán quyết đạt nên đủ điều kiện vào `dev` (R40).

   ```
   feat(benchmark): ca đối kháng backend, dry-run không nạp mô hình, phiên bản ncnn trong meta — P2-06b
   ```

   Bốn tệp: `src/detector/factory.py`, `scripts/benchmark_detect.py`, `tests/test_detector_factory.py`,
   `tests/test_benchmark_detect.py`.

2. **Chạy ba lượt đo §10b của đặc tả** sau khi gộp. Kiểm trước khi chạy: `git status --short` **không in
   gì**, để `.meta.json` có `git_dirty: false` — điều mà hai lượt đo ngày 02/09 chưa đạt (`P2-06` 🔵-5).
   Ba lượt cách nhau ≥ 10 phút, ghi `--ghi-chu "lượt k/3"`, để báo cáo được trung bình kèm độ phân tán
   giữa các lượt (R9).

3. **Bốn mục 🔵 — người dùng quyết định.** Gợi ý: gộp 🔵-1 và 🔵-2 thành một mã việc dọn dẹp
   `chore(quy-trinh)` vì cùng sửa `pyproject.toml`; 🔵-3 để lại nếu thấy không đáng; 🔵-4 cân nhắc **trước
   khi đo trên Pi 5**, vì sau đó phải đo lại.
