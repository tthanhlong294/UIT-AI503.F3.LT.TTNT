# Review P2-05-detector-ncnn — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-05-detector-ncnn.md` (sửa đổi vòng 2 ngày 30/08/2026, commit `29d76a6`) |
| **Nhánh** | `feat/p2-05-detector-ncnn` — mã **chưa commit** |
| **Ngày** | 31/08/2026 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — 0 lỗi 🔴, 0 lỗi 🟡, 5 mục 🔵 |

> **Vì sao file này mở thẳng ở "vòng 2".** Vòng 1 không sinh ra biên bản review: lượt chạy
> ngày 30/08/2026 lộ ra khiếm khuyết của **đặc tả** (ngưỡng IoU tuyệt đối ở ca dòng 22), nên vòng 1
> kết thúc bằng việc sửa đặc tả — `29d76a6` — chứ không bằng một phán quyết. Vòng 2 vì thế là lượt
> kiểm định độc lập **đầu tiên** của mã việc này, và nó phủ toàn bộ mã (cả phần viết ở vòng 1), không
> chỉ phần sửa theo §0b.

---

## 1. Kết quả kiểm máy

**Người dùng chạy ngày 31/08/2026** · 38/39 lệnh · lệnh chép nguyên văn dưới đây.
Shell: PowerShell trên Windows 11; container là `faceid:arm64` (R43, không dựng image mới).

### 1.1. Phạm vi thay đổi và ranh giới ghi tệp

| # | Lệnh | Kết quả |
|---|---|---|
| [1/39] | `git --no-pager log --oneline -3` | HEAD = `29d76a6` trên `feat/p2-05-detector-ncnn` ✅ |
| [2/39] | `git status --short --untracked-files=all` | đúng 8 tệp §2 + `docs/nhat-ky/tuan-06.md` (M) + 5 tệp `docs/bao-cao-tuan/*.docx` (??); **không tệp lạ nào trong `src/`, `tests/`, `scripts/`, `configs/`, `models/`** ✅ |
| [3/39] | `git --no-pager diff --stat` | 5 tệp đã theo dõi, 325 insertions / 72 deletions ✅ |
| [4/39] | `git status --short --untracked-files=all \| Select-String -Pattern '\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$'` | **không dòng nào** ✅ (R25) |
| [5/39] | `git --no-pager diff -- docs/nhat-ky/tuan-06.md` | nội dung nói về `P3-01b`, ngày 27/08, **không nhắc P2-05 một chữ** → tệp của người dùng, **CA-5 không thành lập** ✅ |

`docs/bao-cao-tuan/*.docx` là báo cáo tuần bản Word của sinh viên. Cả hai mục `docs/` này nằm ngoài
danh sách trắng §2 nhưng **không do mã việc này sinh ra** — kết luận dựa trên nội dung diff ở [5/39],
không dựa trên suy đoán.

### 1.2. Diff của phép trích §5.1

| # | Lệnh | Kết quả |
|---|---|---|
| [6/39] | `git --no-pager diff -U15 -- src/detector/yolo_face.py` | **[CHƯA CHẠY]** — xem §2.1 |
| [7/39] | `git --no-pager diff -- tests/test_yolo_face.py` | **chỉ dòng thêm, 0 dòng xoá** trong `test_dong01`–`test_dong42`; thay đổi duy nhất trên dòng cũ là bổ sung `giai_ma_dau_ra` vào câu import dòng 20 ✅ §7.1 dòng 09 đạt, CB-6 không thành lập |
| [8/39] | `git --no-pager diff -- requirements.txt src/detector/__init__.py` | `requirements.txt` thêm **đúng một dòng** `ncnn==1.0.20260526`; `__init__.py` chỉ thêm export, `__all__` 6 tên ✅ |

### 1.3. Ba lệnh nền + ràng buộc thu thập (host `pc_x86`)

| # | Lệnh | Kết quả |
|---|---|---|
| [9/39] | `python -m black --check --line-length 100 src tests` | `All done! 34 files would be left unchanged` ✅ |
| [10/39] | `python -m ruff check src tests` | `All checks passed!` ✅ |
| [11/39] | `python -m pytest -q` | `446 passed, 26 warnings in 67.06s` — **0 failed** ✅ |
| [12/39] | `python -m pytest tests/test_yolo_face.py tests/test_ncnn_backend.py tests/test_detector_factory.py -v -rs` | `69 passed` — 51 + 13 + 5, **0 skip**; `test_dong21`, `test_dong22` PASSED thật ✅ |
| [13/39] | `python -m pytest --collect-only -q -m "not slow"` | `433/446 tests collected (13 deselected)`, **0 error** ✅ §7.3 |

Số ca khớp dự kiến của bảng §7: `test_yolo_face.py` 42 ca cũ + `test_doi_chieu_ultralytics…` + 8 ca mới
(§7.1 hàng 01–08) = 51 · `test_ncnn_backend.py` 13 (§7.2 dòng 10–22) · `test_detector_factory.py` 5
(§7.3 dòng 23–27).

### 1.4. Container `faceid:arm64` (`docker_arm64`)

| # | Lệnh | Kết quả |
|---|---|---|
| [14/39] | `docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -rs -m "not slow"` | `432 passed, 1 skipped, 13 deselected` — 0 failed ✅ |
| [15/39] | `… python3 -m pytest -q -rs -m slow` | `5 failed, 4 passed, 2 skipped, 2 errors` — bảy mục đỏ đều là `ModuleNotFoundError` ở dòng `import`, xem §2.4 |
| [16/39] | `… python3 -c "import ncnn; n=ncnn.Net(); ex=n.create_extractor(); …"` | `Extractor __enter__: True __exit__: True` · `Net.clear: True` · `ncnn 1.0.20260526` ✅ |
| [17/39] | `… python3 -c "import ncnn; …; n.load_param('/tmp/rac.param')"` | `load_param -> -1`, `load_model -> -1`, **không ném ngoại lệ** — xem 🔵-1 |
| [18/39] | `… python3 -c "… [D(P,cfg).close() for _ in range(30)] …"` | `RSS sau 1 lượt 153 800 kB · sau 31 lượt 167 136 kB · delta 30 lượt 13 336 kB` |
| [19/39] | `… python3 -c "… [bool(D(P,cfg)) for _ in range(30)] …"` | `delta 30 lượt 13 060 kB` — lệch [18/39] **2 %** |

Ca skip duy nhất ở [14/39] là `tests/test_benchmark_detect.py:468` ("container không có `.git/`"),
tài sản của `P2-03`, không liên quan `src/detector/`. **Số skip không tăng so với lần chạy trước** —
đúng kỳ vọng §12b: wheel `ncnn` `aarch64` đã có trong image nên ca nhanh của backend NCNN chạy thật.

### 1.5. Năm phép đột biến

Bốn bước mỗi phép: sao lưu ra `$env:TEMP` → sửa → `pytest` → khôi phục + đối chiếu `sha256`.
**Không dùng `git checkout`** (mã chưa commit). **Mọi hash khôi phục đều KHỚP:**
`yolo_face.py` `15789E49…E437D0` (khớp cả 3 lần) · `ncnn_backend.py` `EADFCD15…C7293` ·
`factory.py` `DB26C7E2…9CC1B`.

| # | Phép | Lệnh gây đột biến | Ca đỏ dự đoán | Ca đỏ thật | Kết luận |
|---|---|---|---|---|---|
| ĐB1 [20–23/39] | bỏ kẹp toạ độ vào biên | `.Replace('np.clip((khung[i, 0] - dx) / r, 0, rong_goc)','((khung[i, 0] - dx) / r)')` ×4 cạnh | dòng 07 | `test_dong49` (`assert 0 <= -200`) + `test_dong40` (nhiễu BOM) | ✅ phép kiểm có hiệu lực |
| ĐB2 [24–27/39] | bỏ cắt `max_faces` | `.Replace('chi_so_giu = chi_so_giu[:max_faces]','chi_so_giu = chi_so_giu[:]')` | dòng 04 | `test_dong46` (`assert 5 == 2`) + `test_dong31` (`assert 5 <= 2`) + `test_dong40` (nhiễu) | ✅ |
| ĐB3 [28–31/39] | `kich_thuoc_vao` tách từ tên thư mục | chèn `_so = thu_muc.name.split('_')[0].split('-')[-1]` rồi ghi đè | dòng 17 | **đúng một ca**: `test_dong17` (`assert 999 == 320`) | ✅ mạnh nhất — xem §2.2 |
| ĐB4 [32–35/39] | mọi đường dẫn rơi vào nhánh NCNN | chèn `return NcnnFaceDetector(p, cfg)` ngay sau `p = Path(duong_dan)` | dòng 23 | `test_dong23`, `test_dong25`, `test_dong26`; `test_dong24`/`test_dong27` vẫn xanh | ✅ |
| ĐB5 [36–39/39] *(người review bổ sung)* | hoán vị `cao_goc, rong_goc` tại điểm gọi | `.Replace('cao_goc, rong_goc = khung_hinh.shape[:2]','rong_goc, cao_goc = …')` | dòng 27 | `test_dong27` (`abs(720 - 880.68) = 160.68 ≥ 2.0`) + `test_dong40` (nhiễu) | ✅ xem §2.3 |

`test_dong40` đỏ ở ĐB1/ĐB2/ĐB5 là **nhiễu do công cụ của người review**, không phải khuyết tật của
mã — xem §4.

---

## 2. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §0b việc vòng 2 (3 mục) | ✅ đủ cả ba — xem §2.5 |
| §2 danh sách trắng 8 tệp | ✅ [2/39], [3/39] |
| §3 dữ kiện (blob `in0`/`out0`, CHW không batch, `metadata.yaml`) | ✅ đã dùng đúng, xác nhận thêm bằng [16/39] |
| §4 tham số → `configs/detect.yaml` | ✅ đúng 4 khoá `inference.*`, không thêm khoá, config không đổi |
| §5.1 phép trích `giai_ma_dau_ra` | ✅ **có điều kiện** — §2.1 |
| §5.2 giao diện `NcnnFaceDetector` | ✅ khớp từng ký tự: `__init__(duong_dan_thu_muc, cfg)`, `kich_thuoc_vao`, `ten_backend`, `detect` |
| §5.3 factory `tao_bo_phat_hien` | ✅ đúng thứ tự 3 nhánh, ĐB4 chứng minh thứ tự có ca canh |
| §6.1 không nhân đôi hậu xử lý | ✅ `ncnn_backend.py:20-27` dùng chung `giai_ma_dau_ra`, `_kiem_tra_khung_hinh`, `_tien_xu_ly`, `letterbox` |
| §6.2 nạp/chạy NCNN | ✅ — §2.3 |
| §6.3 `kich_thuoc_vao` từ `metadata.yaml` | ✅ — §2.2 |
| §6.4 dung sai 2 px (tiêu chí mới vòng 2) | ✅ — §2.5 |
| §7.1 dòng 01–09 | ✅ 8 ca `test_dong43`–`test_dong50` + ca cũ nguyên vẹn |
| §7.2 dòng 10–22b | ✅ 13 ca, dòng 21/22 xanh **cả host lẫn ARM64** |
| §7.3 dòng 23–27 + ràng buộc thu thập | ✅ 5 ca, `--collect-only -m "not slow"` 0 error |
| §9 ràng buộc kỹ thuật | ✅ `black`/`ruff` sạch, type hints, docstring Google tiếng Việt, `logging` không `print`, `yaml.safe_load`, `ncnn` chỉ trong thân hàm, không thêm gói |
| §11 ngoài phạm vi | ✅ `scripts/benchmark_detect.py` không bị đụng (vẫn `backend = "onnx"` cứng ở `:477`); không đo hiệu năng; không dọn marker; không chốt backend vào config |

### 2.1. Phép trích §5.1 — kết luận khi thiếu [6/39]

Lệnh [6/39] là thứ tôi tự xếp hạng "bằng chứng số một" và nó **chưa chạy**. Không được coi như đã kiểm.
Nhưng bốn dữ kiện sau **cộng lại** đủ để kết luận, và tôi nêu rõ vì sao:

1. **`giai_ma_dau_ra` là hàm thuần** — chứng minh bằng đọc mã: thân hàm (`yolo_face.py:210-255`) không
   tham chiếu `self`, không đọc biến đóng, chỉ dùng tham số + năm hằng số module + `nms`. Nếu phép
   trích làm rơi một `self.<gì đó>` thì hàm `NameError` ngay khi chạy.
2. ⭐ **Các ca cũ đối chiếu với hằng số đo TRƯỚC phép trích** — đây là dữ kiện mạnh nhất và nó không
   phải hồi quy tự tham chiếu. `tests/test_yolo_face.py:29-34` giữ bốn bộ số đối chứng đo ngày
   18/08/2026 (`_KHUNG_DOI_CHUNG = [82.81, 66.45, 169.56, 183.96]`, `_CONF_DOI_CHUNG = 0.8564`,
   `_DIEM0_DOI_CHUNG`, `_KHUNG_KHONG_VUONG_DOI_CHUNG`) với dung sai `< 1.0` px (`< 2.0` px cho ca
   dòng 27). Bất kỳ thay đổi hành vi nào ở letterbox, ngưỡng, NMS, quy toạ độ hay trích điểm mốc đều
   làm lệch quá dung sai đó. Các ca này xanh ở [11/39] và [12/39].
3. ⭐ **Một nguồn sự thật độc lập hoàn toàn với repo**: `test_doi_chieu_ultralytics_tren_anh_lfw_mau`
   (`:460-476`) so kết quả sau phép trích với `models/yolov8n-face.pt` chạy qua `ultralytics`, dung sai
   2 px. Ca này **xanh trên host** ([11/39] `446 passed`, [12/39] `69 passed`). Nghĩa là đường ONNX sau
   phép trích vẫn khớp trọng số gốc, không cần diff cũng biết hành vi không trôi.
4. **Ba đường dẫn trong hàm đều được canh**: ĐB1 (kẹp biên), ĐB2 (cắt `max_faces`), ĐB5 (thứ tự hai
   tham số kích thước ảnh gốc) đều đỏ đúng ca. Guard không phải mã chết.

**Đủ để kết luận** rằng phép trích không đổi hành vi **trên mọi đường mà bộ kiểm thử chạm tới**.
Ba lớp vẫn nằm ngoài tầm với của bốn dữ kiện trên, ghi ra để không ai hiểu nhầm là đã phủ hết:

| Nằm ngoài tầm | Vì sao không ca nào phân biệt được |
|---|---|
| Nhánh `if not chi_so_giu: return []` (`:226-227`) | `nms` không bao giờ trả rỗng khi đầu vào khác rỗng → nhánh chết. Nếu bản gốc ở đó làm việc khác, không ca nào thấy |
| Một bước hậu xử lý bị **bỏ hẳn** mà ảnh đối chứng không kích hoạt (ví dụ lọc khung nhỏ hơn ngưỡng kích thước) | ba ảnh LFW đối chứng đều có khuôn mặt lớn; bước bị bỏ sẽ không đổi kết quả trên chúng |
| Đổi **độ chính xác số** không đổi giá trị làm tròn (ví dụ `landmarks` từ `float32` sang `float64`) | dung sai 1 px của ca đối chứng không phân biệt được |

Không lớp nào trong ba lớp đó ảnh hưởng tới bước 2.6, nhưng chúng là lý do vẫn nên chạy [6/39] trước
khi commit — chi phí bằng không, và nó biến "đủ suy ra" thành "đã đọc thấy".

### 2.2. §6.3 — `kich_thuoc_vao` (điểm soi kỹ số 2): ĐẠT, có bằng chứng đột biến

`_doc_kich_thuoc_vao` (`ncnn_backend.py:41-83`) ném `LoiMoHinh` ở đủ **năm** đường lỗi: tệp không mở
được / YAML sai cú pháp (`:61-62`), không phải mapping hoặc thiếu `imgsz` (`:64-65`), không phải list
2 phần tử — kể cả `imgsz: 320` (`:68-69`), không phải int dương hoặc là `bool` (`:72-79`), hai phần tử
khác nhau (`:80-81`). **Không nhánh nào rơi về giá trị đoán**; tên thư mục không xuất hiện ở bất kỳ
đâu ngoài thông báo lỗi. `yaml.safe_load` đúng §9. Thứ tự trong `__init__` cũng đúng: đọc metadata ở
`:130` **trước** `import ncnn` ở `:133`, nên các ca dòng 13–16 không cần gói `ncnn`.

ĐB3 [30/39] làm đỏ **đúng một ca** `test_dong17` và không lan sang ca nào khác. Đây là kết quả sạch
nhất trong năm phép: nó chứng minh ca dòng 17 canh **đúng** chỗ hỏng im lặng mà §6.3 mô tả, chứ không
xanh nhờ đi vòng.

### 2.3. §6.2 — vòng đời `ncnn.Net` (điểm soi kỹ số 3): KHÔNG có rò rỉ ở mức chặn

**Ba giả định của mã đều đúng**, xác nhận bằng [16/39]: `Extractor.__enter__`/`__exit__` tồn tại (nên
`with` ở `:189` hợp lệ), `Net.clear` tồn tại (nên `close()` ở `:220` không phải câu thần chú).

Đọc mã cho thấy bốn điểm đúng, không điểm nào phát hiện được bằng `pytest`:

- `Net` tạo **một lần** trong `__init__` (`:137`), không tạo trong `detect` → không vi phạm CB-5.
- `_da_dong = True` đặt ở **dòng đầu tiên** của `__init__` (`:102`), trước mọi phép có thể ném; cộng
  `getattr(self, "_net", None)` ở `:218`. Nên `__init__` đỏ ở khâu validate cfg hay đọc metadata thì
  `__del__` → `close()` thoát sớm, không chạm thuộc tính chưa tồn tại. **Đường thoát ngoại lệ không
  bỏ sót giải phóng.**
- `np.array(dau_ra)` ở `:193` **copy** (không phải `np.asarray`). Đây là chỗ dễ hỏng nhất: nếu là view
  thì nó trỏ vào bộ nhớ blob mà `Extractor.__exit__` vừa dọn ở `:189-191` và đọc ra rác. Mã hiện tại
  đúng, và ca dòng 22 xanh trên ARM64 là phép kiểm gián tiếp cho điều đó.
- Không tham chiếu vòng: `NcnnFaceDetector` giữ `_net`, `_net` không giữ ngược lại đối tượng Python
  nào → refcount về 0 là `__del__` chạy ngay, GC không bị trì hoãn.

**Phán quyết về số đo rò rỉ** [18/39] và [19/39]: **không phải rò rỉ ở mức chặn.** Ba căn cứ:

| Căn cứ | Số |
|---|---|
| Kích thước một bản trọng số `model.ncnn.bin` (imgsz 320) | **12 354 804 B ≈ 12 065 kB** — nguồn: `docs/dac-ta/P2-04-export-ncnn.md:86`, mức "đã kiểm" |
| Mức tăng RSS mỗi lượt tạo+huỷ detector | 13 336 kB / 30 = **≈ 444 kB**, tức **3,7 %** một bản trọng số |
| Tổng tăng sau 30 lượt | 13 336 kB ≈ **1,1 lần** một bản trọng số, không phải 30 lần |

Nếu `Net` bị giữ nguyên vẹn mỗi lượt, delta phải ≈ 30 × 12 MB ≈ 360 MB. Thực đo nhỏ hơn **27 lần**, và
tổng delta của cả 30 lượt chỉ nhỉnh hơn **một** bản trọng số — chữ ký của bộ cấp phát giữ lại arena
(glibc không trả `malloc` arena về HĐH) và phân mảnh, không phải của rò rỉ tuyến tính theo mô hình.
Thêm nữa, `close()` tường minh và phó mặc `__del__` cho kết quả lệch **2 %** (13 336 vs 13 060 kB) —
`__del__` làm đúng việc của `close()`, không có đường nào bỏ sót.

Quy về đúng câu hỏi mà §6.2 và §10 đặt ra — "bước 2.6 tạo và huỷ hàng chục detector, rò rỉ sẽ thành
số đo trôi dần": ma trận bước 2.6 là `{ONNX, NCNN} × {320, 640} × {1, 2, 4}` = 12 ô, **6 ô** dùng NCNN
→ 6 × 444 kB ≈ **2,7 MB** trên máy 8 GB. Không đủ để làm trôi bất kỳ số đo nào.

*Nếu muốn phân định dứt điểm* (tuỳ chọn, **không đổi phán quyết P2-05**): chạy 200 lượt thay vì 30 và
xem delta có tuyến tính không.

```powershell
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -c "import gc; from src.detector.ncnn_backend import NcnnFaceDetector as D; cfg={'inference':{'conf_threshold':0.5,'iou_threshold':0.45,'max_faces':10,'num_threads':0}}; P='models/yolov8n-face-320_ncnn_model'; m=lambda: int(open('/proc/self/statm').read().split()[1])*4; D(P,cfg).close(); gc.collect(); a=m(); [D(P,cfg).close() for _ in range(200)]; gc.collect(); b=m(); print('delta 200 luot (kB):', b-a, '| moi luot (kB):', (b-a)/200)"
```

Đọc kết quả: delta ≈ 89 000 kB (tuyến tính) → có rò rỉ thật ~444 kB/lượt; vẫn **không** chặn P2-05
(6 ô ma trận = 2,7 MB) nhưng phải ghi vào mục rủi ro của `P2-06` để bước 2.6 không chạy hàng nghìn
vòng trong một tiến trình. Delta bão hoà quanh 13–20 MB → xác nhận là phân mảnh bộ cấp phát, đóng lại
hoàn toàn rủi ro §10.

### 2.4. Bảy mục đỏ của [15/39] — xác nhận không liên quan P2-05

Đặc tả §0b và §11 đã xếp chúng ngoài phạm vi. Kiểm chứng bằng chứng cứ chứ không bằng lời:

| Ca đỏ | Dừng ở | Có chạm mã P2-05 không |
|---|---|---|
| ERROR `test_dong27_kiem_chung_tuong_duong_dung_so_anh` | fixture `_onnx_module_export` → `scripts/export_detector.py:175 from ultralytics import YOLO` | không |
| ERROR `test_dong28_kiem_chung_tuong_duong_du_bay_khoa` | cùng fixture | không |
| FAILED `test_dong16_export_that_tao_tep_onnx_doc_duoc` | `tests/test_export_detector.py:235 import onnx` | không |
| FAILED `test_dong17`, `test_dong18`, `test_dong19` (`test_export_detector.py`) | `export_detector.py:175` ultralytics | không |
| FAILED `test_doi_chieu_ultralytics_tren_anh_lfw_mau` | `tests/test_yolo_face.py:462 from ultralytics import YOLO` | không |

Cả bảy dừng ở **đúng dòng `import`**, tức chưa chạy được một dòng logic nào. Không ca nào import
`factory.py`, `ncnn_backend.py` hay gọi `giai_ma_dau_ra`. Riêng ca cuối nằm trong tệp mà P2-05 có sửa
(`test_yolo_face.py`), nên cần một lớp kiểm nữa: [7/39] cho thấy khối `test_doi_chieu_ultralytics…`
**không bị đụng một dòng nào**, và chính ca đó **xanh trên host** ([11/39]) nơi có `ultralytics`. Nó đỏ
trong container vì container cố ý không cài gói, đúng như §12b mô tả. **P2-05 không làm phát sinh ca
đỏ nào so với trước.**

Bốn ca xanh của [15/39] là `test_dong21`, `test_dong22`, `test_dong23`, `test_dong24` — toàn bộ phần
`slow` của mã việc này.

### 2.5. §0b — ba việc của vòng 2

| # | Việc | Vị trí | Kết luận |
|---|---|---|---|
| 1 | Bỏ ngưỡng IoU, dùng dung sai 2 px trên từng cạnh và từng toạ độ điểm mốc | `tests/test_ncnn_backend.py:214` `_DUNG_SAI_PX = 2.0`; vòng lặp cạnh `:239-249`, vòng lặp điểm mốc `:251-260` | ✅ |
| 2 | Thông báo assert nêu tên ảnh, cạnh nào, độ lệch thật | `:246-249` (`f"{p.name} mặt #{idx}: cạnh {ten} lệch {lech} px (NCNN {gn}, ONNX {go}); dung sai {_DUNG_SAI_PX:g} px"`) và `:256-260` | ✅ |
| 3 | Ca dòng 22 dùng `pytest.importorskip("ncnn")`, không `import ncnn` trần | `:221`, kèm comment "dòng 22b" | ✅ |

Ràng buộc "không sửa gì trong `src/`" của §0b **không kiểm chứng độc lập được** bằng git, vì mã vòng 1
chưa commit nên mọi diff đều gộp cả hai vòng. Rủi ro này được bù bằng ĐB1–ĐB5 và bốn dữ kiện ở §2.1,
vốn kiểm tính đúng đắn của `src/` **ở trạng thái hiện tại** chứ không kiểm lịch sử sửa. Ghi nhận như
một hạn chế của quy trình "không commit giữa hai vòng", không phải lỗi của người cài đặt.

---

## 3. Lỗi phải sửa

**Không có lỗi 🔴 CHẶN-A, 🔴 CHẶN-B hay 🟡 CẦN SỬA.**

Hai ứng viên đã cân nhắc và **bác bỏ**, ghi lại để vòng sau không xét lại:

- *Thiếu ca `giai_ma_dau_ra` với `rong_goc != cao_goc`* (cả 7 ca mới đều dùng ảnh vuông). Bác bỏ:
  ĐB5 [38/39] cho thấy `test_dong27` đỏ với độ lệch 160,68 px, tức lưới an toàn **có tồn tại** và có
  hiệu lực. Hạ xuống 🔵-4 vì ca đó phụ thuộc tệp mô hình.
- *Bỏ qua mã trả về `-1` của `load_param`*. Bác bỏ ở mức chặn: đặc tả §5.2 liệt kê `Raises` gồm đúng
  bốn tình huống và **không** có "không nạp được mô hình"; §7.2 cũng không có dòng test tương ứng. Mã
  cài đặt đúng danh sách đó. Theo §5 của `code-review.instructions.md`, đây là khiếm khuyết của **đặc
  tả**, không phải của người cài đặt → chuyển thành 🔵-1.

---

## 4. Khuyết điểm của chính lượt kiểm định này

`test_dong40` đỏ ở ĐB1, ĐB2 và ĐB5 với `SyntaxError: invalid non-printable character U+FEFF`.
Đây là **lỗi công cụ của người review**, không phải khuyết tật của mã đang chấm.

Nguyên nhân: `Set-Content -Encoding utf8` trên Windows PowerShell 5.1 ghi BOM vào đầu tệp;
`test_dong40` đọc `src/detector/yolo_face.py` rồi `ast.parse` (`tests/test_yolo_face.py:421-422`) nên
vỡ vì BOM chứ không vì nội dung đột biến.

Bằng chứng cho chẩn đoán này, không phải suy đoán:

1. Nó đỏ ở **cả ba** phép sửa **ba chỗ khác nhau** của cùng một tệp — dấu hiệu của nguyên nhân chung
   nằm ở khâu ghi tệp, không ở nội dung sửa.
2. Nó **không** đỏ ở ĐB3 và ĐB4 — hai phép đó sửa `ncnn_backend.py` và `factory.py`, hai tệp không có
   ca `ast.parse` nào trỏ tới.
3. `sha256` khôi phục khớp ở cả ba lần → tệp gốc không hỏng, nhiễu chỉ tồn tại trong lúc đột biến.

Hệ quả: cột "ca đỏ thật" của ĐB1/ĐB2/ĐB5 phải **trừ** `test_dong40` ra trước khi đọc. Sau khi trừ,
cả ba phép đều đỏ đúng ca đặc tả chỉ định.

**Đề xuất bổ sung cho `docs/kiem-may/README.md` §"Phép đột biến bằng lệnh rời"** — mẫu lệnh hiện tại
ở dòng 66 của tệp đó dùng `Set-Content -Encoding utf8` và sẽ tái sinh lỗi này ở mọi mã việc sau. Thay
bằng một trong hai dạng không BOM:

```powershell
[System.IO.File]::WriteAllText((Resolve-Path src/detector/yolo_face.py), ((Get-Content src/detector/yolo_face.py -Raw).Replace('<gốc>','<đột biến>')), (New-Object System.Text.UTF8Encoding($false)))
```

hoặc, nếu chạy PowerShell 7+: `Set-Content … -Encoding utf8NoBOM`.

---

## 5. 🔵 Góp ý (không chặn — người dùng quyết định)

### 🔵-1 — Backend NCNN không có guard nào cho mô hình hỏng

**Vị trí**: `src/detector/ncnn_backend.py:140-141`
```python
        self._net.load_param(str(tep_param))
        self._net.load_model(str(tep_bin))
```
**Bằng chứng**: [17/39] — `load_param -> -1`, `load_model -> -1`, ncnn in `parse magic failed` /
`network graph not ready` ra stderr nhưng **không ném ngoại lệ**, chương trình chạy tiếp.
**Vì sao đáng quan tâm**: backend ONNX có guard tương đương ở hai lớp (`yolo_face.py:293-298` bắt ngoại
lệ khi tạo session, `:303-308` kiểm số kênh đầu ra). Backend NCNN không có lớp nào. Một tệp `.param`
hỏng hoặc lệch phiên bản sẽ nạp "thành công" và `detect` trả rác — đúng loại lỗi im lặng mà §6.3 lấy
làm lý do để cấm đoán kích thước từ tên thư mục. Ở bước 2.6 nó sẽ thành một cột số đo trông hợp lý mà
sai.
**Chi phí/lợi ích**: 4 dòng mã + 1 ca test, đổi lấy việc đóng một đường hỏng im lặng.
**Sửa** (thuộc `spec-writer` trước, vì §5.2 phải bổ sung `Raises` và §7.2 phải thêm một dòng):
```python
        if self._net.load_param(str(tep_param)) != 0:
            raise LoiMoHinh(f"Không nạp được {_TEP_PARAM} trong {thu_muc}")
        if self._net.load_model(str(tep_bin)) != 0:
            raise LoiMoHinh(f"Không nạp được {_TEP_BIN} trong {thu_muc}")
```
Tham chiếu: `P2-04` đã đi trước một bước cùng hướng — `docs/dac-ta/P2-04-export-ncnn.md:181` liệt kê
"hoặc có tệp kích thước 0" trong `Raises`.

### 🔵-2 — Không kiểm số kênh tensor ra ở backend NCNN

**Vị trí**: `src/detector/ncnn_backend.py:193`
```python
        mang_tho = np.array(dau_ra).T  # (SO_KENH_DAU_RA, N) -> (N, SO_KENH_DAU_RA)
```
**Vì sao**: comment khẳng định 20 kênh nhưng không có gì kiểm. Đồ thị khác bố cục → `mang[:, 4]` lấy
nhầm kênh làm độ tin cậy, không có dấu hiệu nào báo. Bất đối xứng với `yolo_face.py:303-308`.
**Sửa**: một `if mang_tho.shape[1] != SO_KENH_DAU_RA: raise LoiMoHinh(...)`, hoặc kiểm một lần trong
`__init__` bằng một lượt chạy giả.

### 🔵-3 — `close()` không vô hiệu hoá `detect()`

**Vị trí**: `src/detector/ncnn_backend.py:216-221` — `close()` gọi `net.clear()` nhưng giữ nguyên
`self._net`.
**Vì sao**: gọi `detect()` sau `close()` chạy trên một `Net` đã bị `clear()` → trả rác thay vì ném.
Không ca nào chạm đường này.
**Sửa**: sau `net.clear()` đặt `self._net = None`, và ở đầu `detect` kiểm `if self._da_dong: raise ...`.

### 🔵-4 — Lưới an toàn của phép trích §5.1 phụ thuộc tệp mô hình

ĐB5 chứng minh guard thứ tự `(rong_goc, cao_goc)` **có** ca canh, nhưng ca đó là `test_dong27` — cần
`models/yolov8n-face-320.onnx` và ảnh LFW, sẽ `skip` trên máy thiếu tệp. Bảy ca mới `test_dong43`–
`test_dong49` đều dùng ảnh vuông nên không thay thế được.
**Sửa (nếu người dùng muốn)**: một ca thuần số, không phụ thuộc tệp — `giai_ma_dau_ra(..., rong_goc=200,
cao_goc=100, ...)` với ứng viên tràn biên, assert `x1 <= 200` và `y1 <= 100`. Chi phí 5 dòng.

### 🔵-5 — `PytestUnknownMarkWarning` (nợ có sẵn, P2-05 chỉ làm nhiều thêm)

`pyproject.toml:7-9` chỉ có `testpaths` và `pythonpath`, **không khai báo `markers`** — đã kiểm bằng
đọc tệp. Vì vậy mọi `@pytest.mark.slow` trong repo sinh cảnh báo, và điều đó **đúng từ trước P2-05**:
`tests/test_yolo_face.py:460` có từ `P2-02`, `tests/test_export_detector_ncnn.py` từ `P2-04`. P2-05
thêm 4 chỗ (`test_ncnn_backend.py:194,218`, `test_detector_factory.py:39,46`), nâng tổng lên 13 cảnh
báo — **làm nợ nhiều lên, không tạo ra nợ**. Marker vẫn hoạt động đúng: [13/39] deselect chính xác 13
ca. Đặc tả §11 đã xếp việc dọn dẹp này vào một mã việc riêng, nên **không** tính vào P2-05.
Rủi ro của việc để nguyên (chép lại từ §11): một marker gõ sai tên sẽ không bị loại khỏi lượt
`-m "not slow"` mà cũng không ai báo.

### 🔵-6 — `test_dong40` giòn với BOM

`tests/test_yolo_face.py:421-422` đọc mã nguồn bằng `read_text(encoding="utf-8")` rồi `ast.parse`, nên
vỡ với `SyntaxError` khó hiểu khi tệp có BOM (§4). Dùng `encoding="utf-8-sig"` sẽ chịu được cả hai.
Ca này thuộc `P2-02`, **ngoài phạm vi P2-05** — chỉ ghi nhận.

---

## 6. Hai điểm sống còn — soi riêng

| | Kết luận |
|---|---|
| **Trung thực số liệu (R5, R6)** | ✅ Mã việc này không sinh con số hiệu năng nào, đúng §1 đặc tả. Không có giá trị mặc định giả, không có số ví dụ trong docstring trông như kết quả đo. Bốn hằng số đối chứng ở `tests/test_yolo_face.py:29-34` đều ghi rõ ngày đo và nguồn (`docs/dac-ta/P2-02-detector.md` §3.5). `_DUNG_SAI_PX = 2.0` có comment giải trình vì sao 2 px, trỏ về §6.4 — là **tiêu chí kiểm thử**, không phải số đo. `configs/detect.yaml` không đổi nên ngưỡng khởi điểm vẫn chờ Cổng C chốt |
| **An toàn phần cứng (R22, R24)** | Không áp dụng trực tiếp — mã việc này không chạm GPIO/relay/camera. Phần tương đương ở đây là **tài nguyên gốc C++**: đã soi ở §2.3, đường thoát ngoại lệ không bỏ sót giải phóng, `__del__` tương đương `close()` (lệch 2 %), mức tăng bộ nhớ 3,7 % một bản trọng số mỗi lượt |

---

## 7. Việc tiếp theo

1. *(khuyến nghị, 10 giây)* Chạy nốt lệnh còn thiếu để đóng ô `[CHƯA CHẠY]` ở §1.2 — biến kết luận
   §2.1 từ "đủ để suy ra" thành "đã đọc thấy":
   ```powershell
   git --no-pager diff -U15 -- src/detector/yolo_face.py
   ```
   Kỳ vọng: chỉ ba nhóm thay đổi — thêm `_kiem_tra_khung_hinh` + `giai_ma_dau_ra` ở mức module,
   `detect` rút gọn, thêm property `ten_backend`; mọi phép biến đổi trong khối bị xoá xuất hiện lại
   nguyên văn, cùng thứ tự. Có hằng số / thứ tự / `clip` / `round` nào đổi → báo lại, biên bản sẽ mở
   vòng 3.

2. **Được commit.** Mã đã ĐẠT ở mọi tiêu chí nghiệm thu §7 và không còn lỗi 🔴/🟡. Gợi ý message
   (R29, mã việc ở cuối theo chuỗi truy vết):
   ```
   feat(detector): backend NCNN và factory chọn backend theo đường dẫn — P2-05
   ```

3. **Sáu mục 🔵 — người dùng quyết định.** Nếu đồng ý, gộp 🔵-1, 🔵-2, 🔵-3 thành một mã việc nhỏ
   `P2-05b` (chúng cùng một chủ đề: đóng các đường hỏng im lặng của backend NCNN, và cả ba đều cần
   `spec-writer` sửa §5.2/§7.2 trước). 🔵-5 và 🔵-6 đã có chỗ trong mã việc dọn dẹp marker mà §11 nêu.

4. **Sửa khung quy trình** (§4) — mẫu lệnh đột biến trong `docs/kiem-may/README.md:66` sinh BOM và sẽ
   tái sinh nhiễu này ở mọi mã việc sau. Đây là `.claude/**`-loại thay đổi khung, nên đi **commit
   riêng** với loại `chore(quy-trinh)`, không trộn vào commit của P2-05.
