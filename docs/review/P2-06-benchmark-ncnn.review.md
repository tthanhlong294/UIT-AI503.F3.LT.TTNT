# Review P2-06-benchmark-ncnn — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-06-benchmark-ncnn.md` (commit `4b37c97`, viết ngày 01/09/2026) |
| **Nhánh** | `feat/p2-06-benchmark-ncnn` — mã **chưa commit** |
| **Ngày** | 02/09/2026 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — 0 lỗi 🔴 CHẶN-A, 0 lỗi 🔴 CHẶN-B, 0 lỗi 🟡 CẦN SỬA, 6 mục 🔵 GÓP Ý |

> **Nguồn số liệu.** Toàn bộ bảng dưới đây đến từ **44 lệnh do người dùng chạy ngày 02/09/2026**,
> không có ô nào chép lại từ bảng tự kiểm của người cài đặt (`code-review.instructions.md` §0:
> "bảng kết quả mà `coder` dán về là lời khai của bên bị chấm"). Cả **năm** phép đột biến đều được
> dựng lại từ đầu, kể cả ba phép mà đặc tả §8 đã giao cho người cài đặt tự chạy.
> Shell: PowerShell 5.1 trên Windows 11; container là `faceid:arm64` (R43, **không** dựng image mới).

---

## 1. Kết quả kiểm máy

### 1.1. Phạm vi thay đổi và ranh giới ghi tệp

| # | Lệnh | Kết quả |
|---|---|---|
| [1/44] | `git --no-pager log --oneline -3` | HEAD = `4b37c97` trên `feat/p2-06-benchmark-ncnn`; chưa có commit nào của mã việc ✅ |
| [2/44] | `git status --short --untracked-files=all` | đúng **2 tệp §2** ở trạng thái `M` + `docs/nhat-ky/tuan-06.md` (M) + 7 tệp `docs/bao-cao-tuan/*.docx` (??) + 2 tệp `results/bench_detect_20260902_0926.*` (??). **Không** tệp lạ nào trong `src/`, `configs/`, `models/`, `requirements.txt` ✅ |
| [3/44] | `git --no-pager diff --stat` | 3 tệp đã theo dõi, 473 insertions / 61 deletions ✅ |
| [4/44] | `git status --short --untracked-files=all \| Select-String -Pattern '\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$'` | **rỗng** ✅ (R25) |
| [5/44] | `git --no-pager diff -- docs/nhat-ky/tuan-06.md` | nhật ký do người dùng viết (mục 11 về `P3-01b`, bảng số liệu 4→5 mã việc, 379→388 passed); **không nhắc P2-06** như sản phẩm của người cài đặt → **CA-5 không thành lập** ✅ |
| [6/44] | `git --no-pager diff -U0 -- scripts/benchmark_detect.py \| Select-String -Pattern '^-[^-]'` | dòng xoá đúng danh mục §5: `YoloFaceDetector(...)`, `duong_dan_onnx`, `r["backend"] = "onnx"`, `r["imgsz"] = imgsz`, khối `detector_do_kich_thuoc … del`, `--models` cũ 2 phần tử, `if not m.exists() or not m.is_file()`. **Không dòng xoá nào chạm** `time.perf_counter`, warm-up, cách ghi CSV, `tong_hop` ✅ §11 |
| [7/44] | `git --no-pager diff -U0 -- tests/test_benchmark_detect.py \| Select-String -Pattern '^-[^-]'` | dòng xoá **chỉ** gồm docstring cũ, `_lam_lop_detector_gia` và **11 dòng** `monkeypatch.setattr(bd, "YoloFaceDetector", …)`. **Không assert nào của ca cũ bị xoá hay nới lỏng** ✅ **CB-6 không thành lập** |

**Ba mục ngoài danh sách trắng §2 — đã phân định, không mục nào là CA-5:**

| Mục | Phân định | Căn cứ |
|---|---|---|
| `docs/nhat-ky/tuan-06.md` | tài sản của người dùng | nội dung diff [5/44] nói về `P3-01b`, không về P2-06 |
| `docs/bao-cao-tuan/*.docx` | báo cáo tuần bản Word của sinh viên | đã ghi nhận từ biên bản `P2-05` §1.1, không do mã việc sinh ra |
| `results/bench_detect_20260902_0926.{csv,meta.json}` | **đúng quy trình §10b** | người dùng **tự khẳng định đã tự chạy**; không phải `coder` → **không vi phạm R42**, không CA-5 |

### 1.2. Ba lệnh nền + container

| # | Lệnh | Kết quả |
|---|---|---|
| [8/44] | `python -m black --check --line-length 100 src tests scripts` | `All done!` — 41 tệp giữ nguyên ✅ |
| [9/44] | `python -m ruff check src tests scripts` | `All checks passed!` ✅ |
| [10/44] | `python -m pytest -q` | **458 passed, 0 failed**, 26 warnings, 85,20 s ✅ — khớp đúng dự kiến 446 (`P2-05`) + 12 ca mới |
| [11/44] | `python -m pytest tests/test_benchmark_detect.py -q --durations=10` | **59 passed**, 3,46 s ✅ — 47 ca cũ + 12 ca mới (`test_dong44`–`test_dong54` + `test_dong51b`) |
| [12/44] | `docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"` | **444 passed, 1 skipped, 13 deselected, 0 failed**, 617,98 s ✅ |

26 cảnh báo ở [10/44] là `PytestUnknownMarkWarning` (13 chỗ, nợ có sẵn từ `P2-02`/`P2-04` — xem
`P2-05` 🔵-5) và `TracerWarning` của torch/ultralytics. **Không cảnh báo nào sinh ra từ mã việc này.**
Ca skip duy nhất ở [12/44] là `test_dong30` (container không có `.git/`), tài sản của `P2-03`.

⭐ [12/44] còn là bằng chứng máy cho ràng buộc §11 *"không import gì chỉ có trên máy phát triển ở mức
module"*: chuỗi import mới `benchmark_detect → scripts.export_detector_ncnn → scripts.export_detector`
nạp được trong container **không có `ultralytics`/`torch`** (bảy ca `slow` của `P2-05` đỏ vì thiếu đúng
hai gói đó). Nếu có gói nặng nào lọt lên mức module thì toàn bộ 444 ca đã không collect được.

### 1.3. Quét mẫu — điểm (a) và (b)

| # | Lệnh | Kết quả |
|---|---|---|
| [13/44] | `Select-String -Path scripts\benchmark_detect.py -Pattern 'onnx\|ncnn'` | 13 dòng, **toàn bộ** thuộc bốn nhóm được phép: docstring (3, 8, 387, 487, 494), `import` (31, 33), **đường dẫn tệp** trong `--models` mặc định (397–400) và chuỗi trợ giúp (402), `"onnxruntime": ort.__version__` (595). **Không dòng nào gán chuỗi tên backend** ✅ §6.1 |
| [14/44] | `Select-String -Path scripts\benchmark_detect.py -Pattern '\.stem\|\.suffix\|endswith\|_ncnn_model'` | `.stem` **đúng hai lần** (554 ghi khoá `tom_tat`, 641 đọc lại khoá đó để in bảng) — cùng một mục đích, không dùng đoán backend. `.suffix` **một lần** (159) là lọc **đuôi ảnh** `_DINH_DANG_ANH_HOP_LE`. **Không `endswith`** ✅ |
| [15/44] | `Select-String -Path scripts\benchmark_detect.py -Pattern 'tao_bo_phat_hien'` | **đúng hai điểm gọi**: `:213` (trong `do_mot_cau_hinh`) và `:262` (trong `_ten_backend_du_kien`, chỉ chạy ở `--dry-run`); còn lại là `import` và docstring ✅ §6.2 |
| [16/44] | `Select-String -Path scripts\benchmark_detect.py -Pattern 'YoloFaceDetector\|NcnnFaceDetector\|detector_do_kich_thuoc\|del '` | **rỗng** ✅ — detector tạm đã biến mất, script không gọi thẳng lớp backend nào |

### 1.4. Cái giá của `--dry-run` — điểm (c)

| # | Lệnh | Kết quả |
|---|---|---|
| [17/44] | `python scripts/benchmark_detect.py --device-name "PC kiem dinh" --dry-run` | bảng **12 dòng**, cột backend `onnx`×6 rồi `ncnn`×6, đúng ma trận bước 2.6; **không tệp nào được tạo** ✅ §10b bước 1 |
| [18/44] | `(Measure-Command { python scripts/benchmark_detect.py --device-name "PC kiem dinh" --dry-run }).TotalSeconds` | **0,7008 s** |
| [19/44] | `(Measure-Command { python scripts/benchmark_detect.py --device-name "PC kiem dinh" --models khong/co/mo/hinh.onnx --dry-run }).TotalSeconds` | **0,4359 s**, kèm `logger.warning` "Chưa tra được bộ suy luận…" và cột `chua-xac-dinh` |
| [20/44] | `python -m pytest "tests/…::test_dong38_dry_run_khong_ghi_tep" -q -o log_cli=true --log-cli-level=INFO` | 1 passed, 1,02 s. Log in **4 cặp dòng** `Factory chọn backend …` + `Đã nạp mô hình detector …` → ca này **nạp 4 mô hình thật** |

**Cái giá thời gian đo được: 0,7008 − 0,4359 ≈ 0,265 s cho 4 mô hình trên `pc_x86`** (≈ 66 ms/mô hình).

### 1.5. Đối chiếu tệp kết quả `results/bench_detect_20260902_0926.*`

| # | Lệnh | Kết quả |
|---|---|---|
| [21/44] | `(Import-Csv results\bench_detect_20260902_0926.csv \| Measure-Object).Count` | **1200** ✅ = 12 ô × 100 khung |
| [22/44] | `Import-Csv … \| Group-Object backend \| Select-Object Name, Count` | `onnx` 600 · `ncnn` 600 ✅ |
| [23/44] | `Import-Csv … \| Group-Object backend, imgsz, threads \| Select-Object Name, Count` | **đúng 12 nhóm, mỗi nhóm đúng 100 dòng**: {onnx, ncnn} × {320, 640} × {1, 2, 4} ✅ |

Kèm đọc trực tiếp `results/bench_detect_20260902_0926.meta.json`: `moi_truong: "pc_x86"` (dòng 14),
`notes` mang nguyên văn câu cấm dùng kết luận chỉ tiêu (dòng 58), `tom_tat` đủ **12 khoá** (dòng 59–180),
`n_frames_moi_cau_hinh: 100`, `seed: 42`, `warmup_frames: 10`. Đây là bằng chứng end-to-end rằng §5.4
và §6.3 hoạt động ngoài đời, không chỉ trong `monkeypatch`.

### 1.6. Năm phép đột biến

Bốn bước mỗi phép: sao lưu ra `$env:TEMP\p206_bd.bak` → sửa bằng
`[System.IO.File]::WriteAllText(…, UTF8Encoding($false))` → `pytest` → khôi phục + đối chiếu `sha256`.
**Không dùng `git checkout`** (mã chưa commit). Lệnh ghi có chốt in `KHONG THAY DOI - DUNG LAI` nếu
không tìm thấy chuỗi gốc — cả 5 lần đều in `DA SUA`.

⭐ **Cả năm lần khôi phục đều cho cùng một hash:**
`8E01B3E066E0885663C66F46CDD22BE6F01E713B9EA073037D4A553AF5BFEF10`
([24], [27], [28], [31], [32], [35], [36], [39], [40], [43] — mười lần đo, một giá trị).
[44/44] `git status --short --untracked-files=all` **giống hệt** [2/44] → cây làm việc nguyên trạng.

| # | Phép đột biến | Chuỗi thay thế | Ca đỏ **dự đoán** | Ca đỏ **thật** | Kết luận |
|---|---|---|---|---|---|
| ĐB1 [24–27] | gán cứng backend | `'"backend": ten_backend,'` → `'"backend": "onnx",'` | dòng 02, 04 | **2 failed, 57 passed**: `test_dong45` (`assert {'onnx'} == {'ncnn'}`, `:820`), `test_dong47` (`assert {'onnx'} == {'ncnn','onnx'}`, `:851`) | ✅ đúng hai ca, không lan |
| ĐB2 [28–31] | bỏ khoá `moi_truong` | `'"moi_truong",'`→`''` và `'"moi_truong": moi_truong,'`→`''` | dòng 06 | **2 failed, 57 passed**: `test_dong49` (`assert 'moi_truong' in {…}`, `:881`), `test_dong50` (`KeyError`, `:895`) | ✅ (dòng 07 đỏ kèm là hệ quả tất yếu, không phải lan man) |
| ĐB3 [32–35] | vô hiệu cảnh báo `notes` | `'if moi_truong != _MOI_TRUONG_PHAN_CUNG_DICH:'` → `'if False:'` | dòng 08 | **1 failed, 58 passed**: đúng `test_dong51` (`:910`); `test_dong51b` (ca biên `pi5`) **vẫn xanh** | ✅ sạch nhất |
| ĐB4 [36–39] *(người review bổ sung)* | nạp mô hình **thừa một lần** mỗi ô | chèn `tao_bo_phat_hien(m, cfg_combo);` trước `ban_ghi = do_mot_cau_hinh(…)` | dòng 09 | **1 failed, 58 passed**: đúng `test_dong52` (`assert 2 == 1`, `:942`) | ✅ ca đếm của §6.2 **có răng** |
| ĐB5 [40–43] *(người review bổ sung)* | **đoán backend từ đuôi đường dẫn** — đúng thứ §6.1 cấm | `'ten_backend = detector.ten_backend'` → `'ten_backend = "ncnn" if str(duong_dan_mo_hinh).endswith("_ncnn_model") else "onnx"'` | *(dự đoán: sống sót)* | **59 passed** — mã đột biến **SỐNG SÓT** | ⚠️ xem §4 và 🔵-1 |

---

## 2. Đối chiếu đặc tả

| Mục | Kết luận | Bằng chứng |
|---|---|---|
| §2 danh sách trắng 2 tệp | ✅ | [2/44], [3/44]; ba mục `docs/`+`results/` đã phân định ở §1.1 |
| §3 dữ kiện (factory, `.ten_backend`, `.kich_thuoc_vao`, `xac_dinh_moi_truong`) | ✅ dùng đúng, không dựng lại | [13/44] dòng 33, [15/44] |
| §4 `configs/detect.yaml` KHÔNG đổi | ✅ | [2/44] không có `configs/` trong diff; `config_snapshot` của meta giữ nguyên 4 khoá `inference.*` |
| §5.1 `do_mot_cau_hinh` đổi tên tham số, dùng factory, tự điền `backend`+`imgsz` | ✅ khớp từng ký tự | [6/44], `benchmark_detect.py:171-177`, `:213-215`, `:228-239` |
| §5.2 `main` bỏ gán cứng, giữ `threads`/`run_id`, khoá `tom_tat` nguyên dạng | ✅ | [6/44] (hai dòng gán đã bị xoá), `:547-554` |
| §5.3 `--models` mặc định 4 mô hình + trợ giúp mới | ✅ đúng 4 chuỗi, đúng câu trợ giúp | `:396-402`, [17/44] cho 12 ô |
| §5.4 meta thêm `moi_truong` từ `xac_dinh_moi_truong()` | ✅ | `:99`, `:572`, `:592`; ĐB2; meta thật dòng 14 |
| §6.1 backend đến từ đối tượng, không từ tên tệp | ✅ **đạt** (xem §3-(a)) | [13]–[16], ĐB1 |
| §6.2 mỗi ô nạp mô hình đúng một lần | ✅ **đạt** (xem §3-(b)) | [15], [16], ĐB4 |
| §6.3 cảnh báo QEMU giữ nguyên **và** thêm vào `notes` | ✅ cả hai chỗ | `:520-527` không bị đụng ([6/44]), `:574-576`; ĐB3; `test_dong34/35/36` xanh |
| §7 dòng 01 → `test_dong44` | ✅ | [11/44]; ĐB1 |
| §7 dòng 02 → `test_dong45` | ✅ | ĐB1 đỏ đúng ca |
| §7 dòng 03 → `test_dong46` (`kich_thuoc_vao=999` vs tên tệp `320`) | ✅ | `tests/…:823-828` |
| §7 dòng 04 → `test_dong47` | ✅ | ĐB1 đỏ đúng ca |
| §7 dòng 05 → `test_dong48` | ✅ **mạnh hơn đặc tả**: kiểm cả (a) đường dẫn không tồn tại lẫn (b) tệp có thật nhưng đuôi lạ đi tới factory **thật**, và assert `not thu_muc_kq.exists()` | `tests/…:854-866` |
| §7 dòng 06 → `test_dong49` | ✅ | ĐB2 |
| §7 dòng 07 → `test_dong50` | ✅ | ĐB2 |
| §7 dòng 08 → `test_dong51` **+ `test_dong51b`** (ca biên `pi5`, người cài đặt tự thêm) | ✅ | ĐB3 làm đỏ 51, giữ xanh 51b |
| §7 dòng 09 → `test_dong52` | ✅ | ĐB4 |
| §7 dòng 10 → `test_dong53` | ✅ *(nhưng xem 🔵-2)* | [11/44]; [17/44] xác nhận ngoài đời |
| §7 dòng 11 → `test_dong54` | ✅ | header CSV == `_COT_CSV`, 10 khoá đúng thứ tự |
| §7 dòng 12 — mọi ca cũ vẫn xanh, **không sửa ca cũ** | ✅ | [7/44]: chỉ đổi đích `monkeypatch` 11 chỗ; 47 ca cũ xanh ở [11/44] |
| §7 ràng buộc "không ca nào nạp mô hình thật hay ghi vào `results/`" (áp cho 12 dòng của bảng) | ✅ với **12 ca mới**; `test_dong38` là ca **cũ**, ngoài bảng — xem 🔵-2 | [20/44] |
| §9 ranh giới số đo dùng vào đâu | ✅ | `notes` của meta thật mang nguyên văn câu cấm dùng kết luận chỉ tiêu |
| §10 ngoài phạm vi | ✅ không chạy phân tích, không chốt backend vào config, không chuyển `xac_dinh_moi_truong` sang `src/common/`, không đụng bước 2.7 | [2/44], [13/44] dòng 33 |
| §11 ràng buộc kỹ thuật | ✅ `black`/`ruff` sạch, không thêm gói (`requirements.txt` không trong diff), không import nặng ở mức module | [8], [9], [2], [12] |

---

## 3. Trả lời dứt điểm ba điểm người dùng chỉ đích danh

### (a) §6.1 — nguồn của cột `backend`: **ĐẠT**

Chỉ tồn tại **một** nơi sinh giá trị backend trên đường đo:

```python
# scripts/benchmark_detect.py:213-215
    detector = tao_bo_phat_hien(duong_dan_mo_hinh, cfg)
    ten_backend = detector.ten_backend
    imgsz = detector.kich_thuoc_vao
```

Bốn lớp bằng chứng, không lớp nào là suy đoán:

1. **[16/44] rỗng** — không còn `YoloFaceDetector`, `NcnnFaceDetector`, `detector_do_kich_thuoc`, `del`
   nào trong script. `main` không gán `r["backend"]` nữa ([6/44] cho thấy hai dòng đó nằm trong phần bị xoá).
2. **[13/44]** — không dòng nào gán một chuỗi `"onnx"`/`"ncnn"` vào biến hay khoá; 13 dòng khớp đều là
   docstring, `import`, **đường dẫn tệp**, hoặc `"onnxruntime": ort.__version__`.
3. **[14/44]** — không `endswith`; `.suffix` duy nhất là bộ lọc đuôi ảnh ở `:159`; `.stem` hai lần đều là
   khoá `tom_tat` (ghi ở `:554`, đọc lại ở `:641`). Đặc tả §8 viết *".stem được phép đúng một chỗ"*, thực
   tế là **một mục đích, hai điểm dùng đối xứng** (ghi/đọc cùng một khoá) — cả hai có từ `P2-03`, không
   liên quan đoán backend. Không phải vi phạm.
4. **ĐB1** — gán cứng `"onnx"` làm đỏ **đúng hai ca** `test_dong45` và `test_dong47`, không lan sang ca nào.

**Hạn chế đã đo được, ghi ra để không ai hiểu nhầm là đã phủ hết:** ĐB5 chứng minh **không ca `pytest`
nào phân biệt được "đọc từ đối tượng" với "đoán từ đuôi đường dẫn"** — mọi factory giả trong tệp test đều
khai `ten_backend` **trùng** với tên đường dẫn, nên phép đoán vẫn cho kết quả đúng. Nói cách khác, §6.1
hiện được canh bằng **`grep` + đọc mã**, không bằng bộ kiểm thử. Đây **không** phải khuyết điểm của người
cài đặt: chính đặc tả §8 chỉ định `grep` làm dụng cụ kiểm §6.1, và bảng §7 chỉ yêu cầu phép đối kháng cho
`imgsz` (dòng 03) chứ không cho `backend`. Lượt kiểm định này đã chạy đúng dụng cụ đó và nó sạch → §6.1 **đạt**.
Việc bịt lỗ hổng thuộc `spec-writer`, ghi ở 🔵-1.

### (b) §6.2 — mỗi ô ma trận nạp mô hình đúng một lần: **ĐẠT**

Đoạn tạo `detector_do_kich_thuoc` rồi `del` ở `main` **đã biến mất** ([6/44] liệt kê nó trong phần bị xoá;
[16/44] xác nhận không còn dấu vết). `imgsz` cho bảng tổng kết nay lấy lại từ dữ liệu đã đo:

```python
# scripts/benchmark_detect.py:551-553
                # `backend` và `imgsz` do do_mot_cau_hinh đọc từ chính đối tượng phát hiện
                # (P2-06 §6.1). Lấy lại imgsz ở đây chỉ để in bảng tổng kết cuối.
                imgsz_theo_mo_hinh[i] = ban_ghi[0]["imgsz"]
```

[15/44] cho thấy **đúng hai điểm gọi** `tao_bo_phat_hien`: `:213` trên đường đo và `:262` trong
`_ten_backend_du_kien`. Điểm gọi thứ hai **không** ảnh hưởng §6.2 vì `--dry-run` `return` ở `:484`, trước
toàn bộ vòng đo — hai đường loại trừ nhau, không có lượt chạy nào đi qua cả hai.

**ĐB4** là bằng chứng quyết định: chèn một lượt nạp thừa vào đúng vòng lặp ma trận làm đỏ **đúng một ca**
`test_dong52` với `assert 2 == 1`. Ca đếm không xanh nhờ đi vòng.

Kiểm thêm hai rủi ro mà đặc tả không nêu:
- **CB-5 (nạp model trong vòng lặp xử lý frame)**: không thành lập — `tao_bo_phat_hien` nằm **ngoài** vòng
  `for idx, anh in enumerate(...)` ở `:221`, vùng đo `time.perf_counter` chỉ bọc `detector.detect`.
- **CB-3 (rò rỉ tài nguyên)**: `do_mot_cau_hinh` không gọi `close()` tường minh, nhưng biến `detector` hết
  phạm vi khi hàm trả về → refcount về 0 → `__del__` → `close()` (`src/detector/ncnn_backend.py:223-225`).
  `P2-05` §2.3 đã đo: `close()` tường minh và phó mặc `__del__` lệch **2 %**. Sáu ô NCNN ≈ 2,7 MB. **Không
  phải rò rỉ ở mức chặn.**

### (c) `_ten_backend_du_kien` (`scripts/benchmark_detect.py:244-272`) — cái giá là thật nhưng nhỏ; **lỗi thuộc ĐẶC TẢ**

**Câu 1 — cái giá cụ thể là gì.** Bốn khoản, ba khoản đo được:

| Khoản | Số đo | Nguồn |
|---|---|---|
| Thời gian nạp 4 mô hình thật mỗi lần `--dry-run` | **0,265 s** (≈ 66 ms/mô hình) trên `pc_x86` | [18/44] − [19/44] |
| Bộ nhớ tạm | ≈ một bản trọng số mỗi lượt, giải phóng ngay: `finally` gọi `close()` nếu có (`:269-272`) | đọc mã + `P2-05` §2.3 |
| Phụ thuộc tệp mô hình | máy chưa export → cột in `chua-xac-dinh` + 4 dòng `logger.warning`, **không hỏng** | [19/44] |
| ⭐ Nhiễm sang bộ kiểm thử | `test_dong38_dry_run_khong_ghi_tep` — ca **cũ**, **không** đánh dấu `slow`, **không** monkeypatch factory — nạp **4 mô hình thật** mỗi lần chạy `pytest` | **[20/44]**, log in đủ 4 cặp `Factory chọn backend…` / `Đã nạp mô hình detector…` |

**Hai dự đoán ban đầu của tôi bị số liệu bác bỏ, ghi lại để không ai đọc biên bản này mà tưởng chúng đúng:**
tôi dự đoán dry-run sẽ "đắt" và `test_dong38` sẽ đứng đầu bảng `durations`. Thực tế: **0,265 s** cho cả bốn
mô hình, và `test_dong38` chỉ **0,25 s**, đứng **thứ hai** sau `test_dong34` (0,37 s) ([11/44]).
Luận điểm "tốn kém" **không** thành lập.

**Câu 2 — có đáng không.** Ở `pc_x86` thì **đáng**: 0,265 s đổi lấy việc xác nhận ma trận chia đúng 6 ô
ONNX / 6 ô NCNN **trước** một lượt chạy 112 s (`duration_s` của meta thật) là món hời. Điều còn lại đáng
bàn **không phải chi phí mà là tính chất**: một lệnh tự mô tả là *"In kế hoạch, không đo, không ghi tệp"*
(`:425`) nay khởi tạo bộ suy luận thật, và nó kéo theo một ca test cũ cũng làm vậy. Trên `pi5` — nơi
`--dry-run` được dùng đúng vào lúc người ta muốn xem trước một lượt chạy dài — 66 ms/mô hình của x86 sẽ
lớn hơn nhiều lần. Đó là lý do mục này nên được xem lại **trước Cổng C**, chứ không phải bây giờ.

Cần nói rõ một điều để không thổi phồng: `test_dong38` **không vi phạm** ràng buộc §10 của `P2-03`
(*"ca test không được **đòi hỏi** mô hình thật"*) — nó chạy **xanh cả khi không có mô hình** ([19/44]
chứng minh đường thoát `chua-xac-dinh` hoạt động). Nó *dùng* mô hình khi có, không *đòi hỏi*. Docstring
`tests/test_benchmark_detect.py:3` (*"Không cần mô hình thật cho bất kỳ ca nào ở đây"*) vì thế vẫn đúng
theo nghĩa đen. Hệ quả thật là **thời gian chạy phụ thuộc máy**, không phải kết quả test phụ thuộc máy.

**Câu 3 — lỗi thuộc đặc tả hay thuộc mã: thuộc ĐẶC TẢ.** Ba câu chữ khoá lại thành một vòng khép kín,
trích nguyên văn:

1. §7 dòng 10: *"`--dry-run` in bảng kế hoạch **có cột backend**, không ghi tệp nào"* → cột backend là **bắt buộc**.
2. §6.1: *"`backend` phải đọc từ `detector.ten_backend`. **Cấm** suy từ đuôi hay tên đường dẫn trong `benchmark_detect.py`"* → cấm đường rẻ.
3. §2: *"Tuyệt đối không sửa: `src/**` (**kể cả `factory.py` — nó đã đúng**)"* → cấm nốt cách đúng đắn còn lại, tức thêm vào `factory.py` một hàm tra backend **theo dạng đường dẫn mà không khởi tạo** (khả thi: `factory.py:43-49` quyết định xong backend **trước** khi dựng đối tượng, nên tách phần quyết định ra là chuyện 5 dòng và vẫn giữ đúng một nguồn sự thật).

Ba ràng buộc cộng lại **buộc** người cài đặt phải nạp mô hình thật. Trong không gian mà đặc tả để lại, cài
đặt hiện tại là phương án tốt nhất: đi qua factory (không đoán), bắt **cả hai** `LoiMoHinh` và `LoiCauHinh`,
`try/finally` gọi `close()` nếu backend có, suy biến an toàn về `chua-xac-dinh` thay vì làm hỏng dry-run,
và docstring `:247-250` giải trình rõ vì sao chọn cách này. **Không có gì để trả lại người cài đặt.**
Việc sửa — nếu người dùng muốn — nằm ở `spec-writer`, ghi ở 🔵-2.

---

## 4. Khuyết điểm của chính lượt kiểm định này

**ĐB5 sống sót**, đúng như dự đoán nêu trước khi chạy. Ý nghĩa phải đọc cho đúng:

- Nó **không** chứng minh mã hiện tại sai. Mã hiện tại đọc `detector.ten_backend` — đã xác nhận bằng
  [13]–[16] và bằng mắt.
- Nó chứng minh **bộ kiểm thử không phải là thứ bảo vệ §6.1**. Nếu một mã việc sau vô tình thay dòng `:214`
  bằng phép đoán theo tên, 59 ca vẫn xanh và không ai biết.
- Theo `code-review.instructions.md` §2b, "vẫn xanh" thường là **ghi lỗi**. Ở đây tôi **không** ghi thành
  lỗi, vì đặc tả §8 chỉ định `grep` làm dụng cụ kiểm §6.1 và bảng §7 cố ý chỉ đặt phép đối kháng cho `imgsz`.
  Người cài đặt làm đúng thứ được yêu cầu. Chuyển thành 🔵-1 để người dùng quyết.

Không có nhiễu công cụ nào ở lượt này: cảnh báo BOM đã được nêu trước, mọi lệnh ghi dùng
`UTF8Encoding($false)`, và **mười lần đo `sha256` cho cùng một giá trị** xác nhận cây làm việc không hề
bị bẩn giữa các phép.

---

## 5. Lỗi phải sửa

**Không có lỗi 🔴 CHẶN-A, 🔴 CHẶN-B, hay 🟡 CẦN SỬA.**

Ba ứng viên đã cân nhắc và **bác bỏ**, ghi lại để vòng sau không xét lại:

| Ứng viên | Vì sao bác bỏ |
|---|---|
| *`test_dong38` nạp mô hình thật → vi phạm §10 `P2-03`* | §10 cấm ca test **đòi hỏi** mô hình thật; ca này chạy xanh cả khi không có mô hình ([19/44]). Nguyên nhân gốc là §7 dòng 10 của đặc tả, và §7 dòng 12 lại **cấm sửa ca cũ** — người cài đặt không có nước đi hợp lệ nào. → 🔵-2 |
| *`.stem` xuất hiện hai lần, đặc tả §8 nói "đúng một chỗ"* | Hai điểm dùng đối xứng của **cùng một khoá `tom_tat`** (ghi `:554`, đọc `:641`), cả hai có từ `P2-03`, không dùng đoán backend. Câu chữ đặc tả đếm **mục đích**, không đếm **dòng**. |
| *`do_mot_cau_hinh` không gọi `close()`* | `__del__` chạy ngay khi hàm trả về; `P2-05` §2.3 đo được độ lệch 2 % giữa `close()` tường minh và `__del__`; 6 ô NCNN ≈ 2,7 MB trên máy 8 GB. Không phải CB-3. |

---

## 6. 🔵 Góp ý (không chặn — người dùng quyết định)

### 🔵-1 — Bảng §7 thiếu phép đối kháng cho `backend` (có bằng chứng máy: ĐB5)
**Vị trí**: `docs/dac-ta/P2-06-benchmark-ncnn.md` §7 dòng 01–02 · `tests/test_benchmark_detect.py:805-820`
**Bằng chứng**: [42/44] — thay `ten_backend = detector.ten_backend` bằng phép đoán theo đuôi đường dẫn,
**59/59 ca vẫn xanh**.
**Vì sao đáng quan tâm**: §6.1 là yêu cầu trung tâm của mã việc này, và lý do đặc tả đưa ra cho nó là
*"cột `backend` trong CSV nói sai về chính dòng số đo bên cạnh nó… đi thẳng vào Chương 4"*. Một yêu cầu
quan trọng như vậy hiện chỉ được canh bằng `grep` — dụng cụ không chạy tự động ở bất kỳ vòng nào sau này.
**Sửa** (thuộc `spec-writer`: thêm một dòng vào bảng §7, rồi `coder` viết 5 dòng test):
```python
def test_dong55_backend_lay_tu_doi_tuong_khong_tu_ten_duong_dan(monkeypatch, tmp_path):
    """Tên tệp nói 'onnx', đối tượng phát hiện nói 'ncnn' — bản ghi phải theo đối tượng."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia(ten_backend="ncnn"))
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 10, _anh_gia(15), 5)
    assert {r["backend"] for r in bg} == {"ncnn"}
```
Đây đúng là phép mà dòng 03 đã làm cho `imgsz` (999 vs tên tệp `320`), chỉ chuyển sang trục `backend`.

### 🔵-2 — `--dry-run` khởi tạo mô hình thật; ba ràng buộc của đặc tả không để lại lối khác
**Vị trí**: `scripts/benchmark_detect.py:244-272` · đặc tả §7 dòng 10 + §6.1 + §2
**Số đo**: 0,265 s cho 4 mô hình trên `pc_x86` ([18]−[19]); kéo theo `test_dong38` nạp 4 mô hình thật ([20]).
**Vì sao**: chi phí trên `pc_x86` không đáng kể, nhưng trên `pi5` và trong container QEMU thì khác hẳn — mà
đó lại đúng là hai nơi `--dry-run` có ích nhất (xem trước một lượt chạy dài trên máy chậm).
**Ba phương án, người dùng chọn**:
1. **Giữ nguyên**, sửa chuỗi trợ giúp `:425` thành *"In kế hoạch, không đo, không ghi tệp (có nạp mô hình để tra backend)"* — 1 dòng, trung thực với hành vi.
2. **Mã việc nhỏ `P2-06b`**: thêm vào `src/detector/factory.py` một hàm `tra_ten_backend(duong_dan) -> str`
   quyết định theo dạng đường dẫn **mà không khởi tạo**, rồi cả `tao_bo_phat_hien` lẫn `_ten_backend_du_kien`
   cùng gọi nó → vẫn **một nguồn sự thật**, dry-run trở lại "khô", và `test_dong38` hết nạp mô hình.
   Chi phí ≈ 10 dòng mã + 2 ca test; cần `spec-writer` mở danh sách trắng cho `factory.py`.
3. **Bỏ cột backend khỏi dry-run** — rẻ nhất nhưng mất đúng thứ có ích: xác nhận 6/6 trước lượt chạy dài.
Khuyến nghị của tôi: **phương án 2, làm trước khi đo trên Pi 5**, vì nó cũng dọn luôn 🔵-1 về mặt kiến trúc.

### 🔵-3 — `.meta.json` không ghi phiên bản `ncnn`, dù 6/12 ô số đo do NCNN sinh ra ⭐
**Vị trí**: `scripts/benchmark_detect.py:593-598` · bằng chứng: `results/bench_detect_20260902_0926.meta.json:15-20`
```json
  "software": { "python": "3.12.5", "onnxruntime": "1.20.1", "opencv-python": "4.13.0", "numpy": "2.2.0" },
```
**Vì sao**: `experiment-protocol.instructions.md` §2 đòi *"Phiên bản thư viện — dict đầy đủ"*, và §9 checklist
đòi điều kiện đo ghi đầy đủ. Bảng so sánh ONNX vs NCNN của Chương 4 sẽ nói *"NCNN nhanh hơn/chậm hơn x %"*
mà **không có chỗ nào ghi bản NCNN nào đã chạy** — trong khi phiên bản `onnxruntime` của phía đối chứng thì
lại có. Đây là bất đối xứng đúng ở trục biến thiên của phép so sánh.
**Sửa** (3 dòng, nằm trong danh sách trắng, không cần import gói nặng):
```python
        "software": {
            ...,
            "ncnn": importlib.metadata.version("ncnn"),
        },
```
**Nên làm trước lượt đo trên Pi 5** — lượt đo Cổng C là lượt đi vào bảng chỉ tiêu, sửa sau thì phải đo lại.

### 🔵-4 — CSV không có cột định danh mô hình
**Vị trí**: `scripts/benchmark_detect.py:78-89` (`_COT_CSV`)
**Vì sao**: một ô được nhận diện trong CSV bằng `backend × imgsz × threads` — đủ cho ma trận 12 ô hiện nay
([23/44] cho đúng 12 nhóm × 100). Nhưng hai mô hình **cùng backend, cùng `imgsz`** (ví dụ so hai bản export
khác `opset` — chính tình huống mà `test_dong40b` bảo vệ ở phía `tom_tat`) sẽ **lẫn vào nhau trong CSV**,
trong khi `tom_tat` vẫn tách được nhờ khoá có chỉ số ô. Hai nửa của cùng một tệp kết quả có sức phân giải
khác nhau.
**Sửa (nếu người dùng muốn)**: thêm cột `mo_hinh` (đường dẫn) vào `_COT_CSV` — nhưng việc này **đổi lược đồ
CSV**, va vào `test_dong54` và vào các tệp `results/` đã có, nên phải là mã việc riêng có cân nhắc.

### 🔵-5 — Lượt đo 09:26 sinh ra từ mã chưa commit (`git_dirty: true`)
**Vị trí**: `results/bench_detect_20260902_0926.meta.json:5`
**Vì sao**: `experiment-protocol.instructions.md` §9 yêu cầu `git_dirty = false` cho số liệu đưa vào báo cáo,
và §4 ghi rõ *"`git_dirty: true` là cảnh báo — kết quả đo từ code chưa commit khó tái lập"*. Số hiện tại
truy về commit `4b37c97` **cộng với** một tập thay đổi không tên.
**Sửa**: sau khi commit mã việc này, chạy lại đúng lệnh §10b bước 2 — mất khoảng 2 phút (`duration_s` = 112 s),
rồi dùng tệp mới cho Chương 4 và giữ tệp cũ như lịch sử đo. Số liệu đã có **không sai**, chỉ là không tái lập
được về một commit.

### 🔵-6 — `PytestUnknownMarkWarning` (nợ có sẵn, chỉ nhắc lại)
13 cảnh báo ở [10/44], đúng con số của `P2-05` 🔵-5, sinh từ `pyproject.toml` không khai `markers`.
**P2-06 không làm nợ này nhiều thêm** (không thêm `@pytest.mark.slow` nào). Đã có chỗ trong mã việc dọn dẹp
marker mà `P2-05` §11 nêu.

---

## 7. Hai điểm sống còn — soi riêng

| | Kết luận |
|---|---|
| **Trung thực số liệu (R5, R6)** | ✅ **Đạt, và mã việc này còn củng cố nó.** Không giá trị mặc định giả, không số ví dụ trong docstring trông như kết quả đo, không test dùng số bịa (mọi ca dùng `monkeypatch` + `tmp_path`). Ba cơ chế trung thực **đều đã được đột biến chứng minh là có răng**: cột `backend` không nói sai về dòng số đo bên cạnh (ĐB1), `.meta.json` bắt buộc có `moi_truong` (ĐB2), và `notes` mang câu cấm dùng kết luận chỉ tiêu khi không đo trên Pi 5 (ĐB3). Tệp kết quả thật `results/bench_detect_20260902_0926.meta.json` mang đủ cả ba. Hai khiếm khuyết còn lại đã ghi ở 🔵-3 (thiếu phiên bản `ncnn`) và 🔵-5 (`git_dirty`), cả hai đều **không** làm con số nào sai, chỉ làm nó khó truy nguồn hơn mức đáng có |
| **An toàn phần cứng (R22, R24)** | Không áp dụng trực tiếp — mã việc không chạm GPIO/relay/camera. Phần tương đương là **tài nguyên gốc C++ của `ncnn.Net`**: đường đo tạo đúng một detector mỗi ô (ĐB4), giải phóng qua `__del__`→`close()`, và `_ten_backend_du_kien` giải phóng tường minh trong `finally` (`:269-272`). Không CB-3, không CB-5 |

---

## 8. Việc tiếp theo

1. **Được commit.** Mã đạt mọi tiêu chí nghiệm thu §7, không còn lỗi 🔴 hay 🟡. Gợi ý message (R29, mã việc
   ở cuối theo chuỗi truy vết):
   ```
   feat(benchmark): đo được cả ONNX và NCNN trong một ma trận 12 ô — P2-06
   ```
   Lưu ý [1/44]: nhánh `dev` đang trỏ **cùng commit** với `feat/p2-06-benchmark-ncnn`. Đây là bình thường
   (nhánh feat vừa tách ra và chưa commit gì), nhưng khi gộp thì nhớ commit **trên nhánh feat** rồi mới
   gộp vào `dev`, để chuỗi truy vết đặc tả → nhánh → biên bản → commit không đứt.

2. **Chạy lại lượt đo §10b sau khi commit** (🔵-5) — 2 phút, để `git_dirty: false`:
   ```powershell
   python scripts/benchmark_detect.py --device-name "PC phát triển"
   ```
   Giữ cả tệp cũ lẫn tệp mới; lịch sử đo là dữ liệu có giá trị (`experiment-protocol` §4).

3. **Sáu mục 🔵 — người dùng quyết định.** Nếu đồng ý, gộp 🔵-1, 🔵-2, 🔵-3 thành một mã việc nhỏ
   `P2-06b` **làm trước Cổng C**: cả ba đều rẻ (≈ 20 dòng mã + 3 ca test), cả ba đều cần `spec-writer` mở
   danh sách trắng hoặc thêm dòng vào bảng §7 trước, và cả ba đều **đắt hơn nhiều nếu sửa sau khi đã đo
   trên Pi 5** — vì lúc đó phải đo lại. 🔵-4 và 🔵-6 để lại cho mã việc dọn dẹp về sau.

4. **Ranh giới của số liệu đã có, nhắc lại cho Cổng D** (đặc tả §9): 12 ô trong
   `results/bench_detect_20260902_0926.csv` là **`pc_x86`**, vào Chương 4 dưới nhan đề *"kết quả sơ bộ trên
   máy phát triển"*, **không** dùng kết luận chỉ tiêu ≥ 10 FPS và **không** dùng chọn backend — thứ tự nhanh
   chậm ONNX/NCNN hoàn toàn có thể đảo dấu trên ARM. Câu cảnh báo đó đã nằm sẵn trong `notes` của tệp meta,
   nên nó đi cùng số liệu kể cả khi ai đó mở lại tệp sau ba tuần.
