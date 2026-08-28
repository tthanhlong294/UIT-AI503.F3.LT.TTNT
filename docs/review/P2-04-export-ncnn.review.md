# Review P2-04-export-ncnn — vòng 1

> ⬇️ **Phán quyết cuối cùng nằm ở phần "Vòng 2" cuối tệp (28/08/2026): 🟡 ĐẠT CÓ ĐIỀU KIỆN.**
> Phần vòng 1 dưới đây giữ nguyên như lúc ghi, làm hồ sơ của lượt kiểm định đầu tiên.

> Đây là **lượt review đầu tiên** của mã việc. Bản mã được chấm là bản đã qua **vòng 2 cài đặt**
> (đặc tả `fcb3a95` §0 bổ sung bốn việc: `xac_dinh_moi_truong`, khoá `moi_truong`, ba ca 20b–20d,
> chạy lại lượt sinh kết quả). Vòng 1 cài đặt không đi qua review nên không có biên bản trước đó.

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-04-export-ncnn.md` (commit `fcb3a95`) |
| **Nhánh** | `feat/p2-04-export-ncnn` |
| **HEAD khi review** | `fcb3a9536f1a2f051f5deade0339fa07cf9de43e` — mã chấm **chưa commit** |
| **Ngày** | 2026-08-28 |
| **Người chạy lệnh kiểm định** | người dùng, 27–28/08/2026 (65 lệnh, Git Bash + PowerShell) |
| **Phán quyết** | 🔴 **TRẢ LẠI** — 0 × CHẶN, **1 × CẦN SỬA**, 6 × GÓP Ý |

Phán quyết 🔴 đến từ **đúng một mục 🟡**, sửa trong một hàm, ước lượng dưới 10 dòng. Mọi phần còn
lại — phạm vi tệp, ba lệnh nền, container, năm phép đột biến, và nghi vấn lớn nhất của mã việc —
đều **đạt**.

---

## 1. Kết luận về nghi vấn trung tâm: H1 hay H2

Đặc tả §7.3 nêu rằng số đo `sai số điểm mốc 2,3 × 10⁻⁵ px` / `IoU 0,9999996` khớp với **hai** giả
thuyết cho ra số liệu giống hệt nhau:

- **H1** — chuyển đổi fp32 gần như không mất mát (`metadata.yaml` ghi `half: false`);
- **H2** — hai phía của phép so sánh vô tình nạp **cùng một mô hình**, tức bản NCNN không hề chạy.

Số liệu không phân biệt được hai giả thuyết. Phải phân biệt bằng **phép thử chủ động**.

### 1.1. Nơi hai đường nạp tách nhau — trả lời yêu cầu §12 mục 2

| Chặng | Vị trí |
|---|---|
| Hai phía được tạo ra | `scripts/export_detector_ncnn.py:273` (`.pt`) và `:274` (NCNN) |
| Cùng đi qua một nhà máy | `scripts/export_detector_ncnn.py:57-73`, kết thúc ở `:73` `YOLO(duong_dan, task=task)` |
| Nguồn đường dẫn phía `.pt` | `cfg["weights_pt"]` — `:449` |
| Nguồn đường dẫn phía NCNN | giá trị trả về của `export_ncnn_mot_kich_thuoc` (`:163`, `:193`), truyền vào ở `main:484` |

Khác biệt giữa hai phía **chỉ là chuỗi đường dẫn**; việc chọn bộ suy luận nằm hoàn toàn bên trong
`ultralytics.AutoBackend`. Mã dự án **không có** dòng nào khẳng định phía NCNN thật sự chạy `ncnn`
— `kiem_tra_thu_muc_ncnn` (`:196-231`) chỉ kiểm ba tệp tồn tại và khác rỗng. Đọc mã vì thế **không
đủ** để loại H2.

### 1.2. Phép thử chủ động ĐB6 — H2 **bị bác bỏ**

Phá đúng **một** phía: ghi đè `model.ncnn.bin` của bản 320 bằng `model.ncnn.bin` của bản 640 (tệp
NCNN hợp lệ nhưng thuộc đồ thị khác), giữ nguyên bản `.pt`, rồi chạy lại đúng phép đo của lệnh
`[35/65]`:

| Trạng thái bản NCNN | Khớp số mặt | IoU TB | Sai số mốc TB | `dat` | Lệnh |
|---|---|---|---|---|---|
| Nguyên vẹn | **10/10** | 0,9999996902584559 | 2,6585523717988638e-05 | `True` | `[35/65]` |
| **Đã phá trọng số** | **0/10** | `None` | `None` | **`False`** | `[40/65]` |

Nếu H2 đúng — nếu phía NCNN không được dùng — thì phá trọng số bên trong `model.ncnn.bin` sẽ
**không ảnh hưởng gì**, và lệnh `[40/65]` phải cho lại đúng con số của `[35/65]`. Thực tế kết quả
sụp từ 10/10 xuống 0/10 và `dat` lật từ `True` sang `False`.

**⇒ Phía NCNN thật sự được nạp và thật sự tham gia phép so sánh. H2 bị loại. Con số 2,3 × 10⁻⁵ px
là hệ quả của H1.**

Ba bằng chứng độc lập củng cố cùng kết luận:

1. `[34/65]` — nội soi đối tượng sau khi nạp: phía NCNN có `net = <class 'ncnn.ncnn.Net'>`, phía
   `.pt` có `net = NoneType`.
2. Nhật ký của chính lượt chạy thật 21:44: `Loading models\yolov8n-face-320_ncnn_model for NCNN
   inference...` xuất hiện **cho từng độ phân giải**.
3. Nhật ký PNNX của lượt đó in `fp16 = 0` — bằng chứng độc lập cho `half: false` ở `metadata.yaml`,
   tức trọng số giữ ở fp32 và sai số ở mức làm tròn float32 là **hợp lý về mặt số học**.

⚠️ **Bài học phương pháp, ghi lại để lần sau không mắc**: trong `ultralytics 8.4.39`, hai thuộc tính
`AutoBackend.pt` và `AutoBackend.ncnn` **đều trả `None`** ở cả hai phía (`[34/65]`). Dùng chúng làm
tiêu chí phân biệt backend sẽ cho **báo động giả**. Tiêu chí dùng được là `AutoBackend.net`
(`ncnn.ncnn.Net` với NCNN, `NoneType` với `.pt`), hoặc dòng nhật ký `for NCNN inference`.

---

## 2. Kết quả kiểm máy

**Người dùng chạy ngày 27–28/08/2026.** Lệnh chép nguyên văn dưới đây; ba khối `python -c` dài đặt
sau bảng (P-A, P-B, P-C). Chạy từ gốc repo.

### 2.1. Phạm vi tệp

| # | Lệnh | Kết quả |
|---|---|---|
| `[1/65]` | `git status --short --untracked-files=all` | 6 tệp `M` + 13 tệp `??`; trong `src/ scripts/ tests/` chỉ có hai tệp mới của §2 ✅ |
| `[2/65]` | `git diff --stat` | **không** đụng `scripts/export_detector.py`, `configs/`, `src/`, `requirements.txt`, `models/README.md` ✅ (§11) |
| `[3/65]` | `git diff -- requirements-dev.txt` | đúng **một dòng `+`**: `ncnn==1.0.20260526`, ngay sau `ultralytics==8.4.39`, 0 dòng `-` ✅ |
| `[4/65]` | `git status --short --untracked-files=all \| grep -Ei '\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$'` | rỗng ✅ (không có CA-4) |
| `[5/65]` | `git status --short --untracked-files=all -- src scripts tests configs` | đúng 2 dòng `??` ✅ |
| `[6/65]` | `git log -1 --format=%H` | `fcb3a953…` — khớp trường `commit` của `.meta.json` |
| `[7/65]` | `ls -1 results/ \| grep export_ncnn` | đúng 2 tệp `…_2144.{json,meta.json}`; bộ `_2027` vòng 1 đã xoá ✅ |

**Kết luận phạm vi**: danh sách trắng §2 **được tôn trọng tuyệt đối**. Mười ba tệp `??`/`M` còn lại
thuộc `.claude/`, `docs/`, `notebooks/`, `results/` — sản phẩm của phiên thiết kế và của lượt chạy
người dùng, **không** phải sản phẩm của người cài đặt. Không có CA-5.

### 2.2. Ba lệnh nền — host

| # | Lệnh | Kết quả |
|---|---|---|
| `[8/65]` | `python -m black --check --line-length 100 src tests scripts` | `37 files would be left unchanged` ✅ |
| `[9/65]` | `python -m ruff check src tests scripts` | `All checks passed!` ✅ |
| `[10/65]` | `python -m pytest -q -m "not slow"` | **410 passed, 9 deselected** — không ca nào của `P2-01` bị vỡ ✅ |
| `[11/65]` | `python -m pytest tests/test_export_detector_ncnn.py -v -m "not slow"` | **29 passed, 2 deselected**; có đủ `test_dong08b`, `test_dong20b`, `test_dong20c`, `test_dong20d` ✅ |
| `[12/65]` | `python -m pytest tests/test_export_detector_ncnn.py --collect-only -q -m "not slow"` | `29/31 tests collected` ✅ |

### 2.3. Container `faceid:arm64` (image có sẵn, không dựng lại — R43)

| # | Lệnh | Kết quả |
|---|---|---|
| `[13/65]` | `MSYS_NO_PATHCONV=1 docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"` | **409 passed, 1 skipped, 9 deselected** trong 12 phút (QEMU) ✅ |
| `[14/65]` | `… faceid:arm64 python3 -m pytest tests/test_export_detector_ncnn.py --collect-only -q -m "not slow"` | `29/31 tests collected`, **không lỗi import** ✅ — ràng buộc thu thập cuối §8 thoả |
| `[15/65]` | `… faceid:arm64 python3 -c "from scripts.export_detector_ncnn import xac_dinh_moi_truong; print(xac_dinh_moi_truong())"` | in **`docker_arm64`** ✅ — dòng 20b/20c đúng trong môi trường **thật**, không monkeypatch |

`[14/65]` là phép kiểm quan trọng: container không có `ncnn`/`ultralytics`/`torch`, thu thập vẫn
trót lọt ⇒ ba gói nặng chỉ được import trong thân hàm (§7.2, tránh CA-9).

### 2.4. Quét mẫu vi phạm

| # | Lệnh | Kết quả |
|---|---|---|
| `[16/65]` | `grep -nE "^(import\|from)[[:space:]]+(ncnn\|torch\|ultralytics)" scripts/export_detector_ncnn.py tests/test_export_detector_ncnn.py` | rỗng ✅ |
| `[17/65]` | `grep -nE "0\.5\|0\.45\|320\|640\|0\.90\|0\.95\|5\.0" scripts/export_detector_ncnn.py` | rỗng ✅ — không hardcode tham số thực nghiệm (CA-1) |
| `[18/65]` | `grep -n "except Exception" scripts/export_detector_ncnn.py` | rỗng ✅ |
| `[19/65]` | `grep -nE "raise (ValueError\|TypeError)" scripts/export_detector_ncnn.py` | rỗng ✅ |
| `[20/65]` | `grep -nE "except[[:space:]]*:" scripts/export_detector_ncnn.py tests/test_export_detector_ncnn.py` | rỗng ✅ (CB-4) |
| `[21/65]` | `grep -nE "[A-Z]:\\\\\|/home/\|/Users/" scripts/export_detector_ncnn.py tests/test_export_detector_ncnn.py` | rỗng ✅ |
| `[22/65]` | `grep -nEi "token[[:space:]]*=[[:space:]]*[\"']\|api_key…\|password…" (hai tệp)` | rỗng ✅ |
| `[23/65]` | `grep -nE "assert True\|^[[:space:]]*pass$" tests/test_export_detector_ncnn.py` | rỗng ✅ (CB-6) |
| `[24/65]` | `grep -nE "logger\.[a-z]+\(f\"" scripts/export_detector_ncnn.py` | rỗng ✅ (CS-5) |
| `[25/65]` | `grep -n "print(" scripts/export_detector_ncnn.py` | 12 dòng, **toàn bộ** nằm trong `_in_bang_ket_qua` (`:385-406`) và nhánh in bảng/thông báo CLI của `main` (`:453-478`, `:553`) ✅ đúng ngoại lệ G2/R23 của §10 |
| `[26/65]` | `grep -nE "^[[:space:]]*for \|_tao_mo_hinh_yolo\(" scripts/export_detector_ncnn.py` | nạp mô hình ở `:273-274`, vòng lặp ảnh bắt đầu `:281` ⇒ **không** nạp model trong vòng lặp ✅ (CB-5) |

### 2.5. Truy vết số đo (R17)

| # | Lệnh | Kết quả |
|---|---|---|
| `[27/65]` | khối **P-A** dưới bảng | `moi_truong = pc_x86` · `commit = fcb3a953…` · `seed = 42` · `phien_ban` có `ncnn 1.0.20260526` (không phải `khong-xac-dinh`) · `du bay khoa = True` ✅ |
| `[28/65]` | `grep -n "^date:" models/yolov8n-face-320_ncnn_model/metadata.yaml models/yolov8n-face-640_ncnn_model/metadata.yaml` | `22:42:56` và `22:43:05` — **muộn hơn** `thoi_diem` 21:44:21 của `.meta.json` ⚠️ xem §5 GÓP Ý-4 |
| `[29/65]` | `sha256sum` bốn tệp `model.ncnn.{bin,param}` | khớp từng chữ với bảng mục 2.1 của `notebooks/03_xac_minh_export_ncnn.ipynb` ✅ |
| `[30/65]` | `ls -la --time-style=long-iso results/ \| grep export_ncnn` | hai tệp, mốc `2026-08-27 21:44`, khớp `thoi_diem` ✅ |

### 2.6. Lượt chạy thật §12b

| # | Lệnh | Kết quả |
|---|---|---|
| `[31/65]` | `python -m pytest tests/test_export_detector_ncnn.py -v -m slow` | **2 passed** (dòng 05, 06) trong 19,17 s; export thật vào `tmp_path` ✅ |
| `[32/65]` | `python scripts/export_detector_ncnn.py --dry-run; echo "MA THOAT=$?"` | in bảng kế hoạch hai độ phân giải; `MA THOAT=True` (PowerShell trả boolean, không phải mã thoát số) — xem ghi chú dưới |
| `[33/65]` | `git status --short --untracked-files=all -- results models` | chỉ hai tệp `…_2144.*` ⇒ `[31]` và `[32]` **không sinh thêm tệp nào** ✅ (dòng 23 §8) |

Ghi chú `[32/65]`: `$?` trong PowerShell là boolean nên **mã thoát số chưa được kiểm trực tiếp bằng
shell**. Đây là hạn chế của phép kiểm, không phải khiếm khuyết của mã: `test_dong23` khẳng định
`main(["--dry-run"]) == 0` ở mức Python và đã xanh ở `[11/65]`, còn `[33/65]` xác nhận vế "không ghi
tệp nào". Tiêu chí dòng 23 vì vậy **đạt**.

Lượt chạy thật sinh ra số liệu chính thức (người dùng, 27/08 lúc 21:44) đã dán lại scrollback: log
PNNX ghi `fp16 = 0`, `inputshape = [1,3,320,320]f32` và `[1,3,640,640]f32`, hai dòng `Loading …
for NCNN inference...`, bảng kết quả `DAT` cho cả hai độ phân giải, tệp ra
`results/export_ncnn_20260827_2144.json`.

### 2.7. Kiểm đột biến — năm phép bắt buộc, dựng lại từ đầu

Sao lưu ra ngoài repo `~/p204-backup` (`[43]`–`[45]`), mã băm gốc:

```
ff3ee1282b04d88527754fd12aa4a975507ccfac54479d31990c12fa0af3a586 *scripts/export_detector_ncnn.py
b4d48d7ac2dff166e50ec0a56dfcef60d55ac753d08426fd40846cc218fffb38 *tests/test_export_detector_ncnn.py
```

| # | Phép đột biến | Ca dự đoán đỏ | Ca **thật sự** đỏ | `sha256` sau khôi phục |
|---|---|---|---|---|
| ĐB1 `[46]`–`[49]` | bỏ kiểm tồn tại `model.ncnn.param` | dòng 08 | **`test_dong08`** — `1 failed, 28 passed` | `OK` / `OK` ✅ |
| ĐB2 `[50]`–`[53]` | bỏ kiểm tệp rỗng | dòng 11 | **`test_dong11`** — `DID NOT RAISE LoiMoHinh`, `1 failed` | `OK` / `OK` ✅ |
| ĐB3 `[54]`–`[57]` | vô hiệu guard thiếu điểm mốc (§7.3) | dòng 14 | **`test_dong14`** — `1 failed, 28 passed` | `OK` / `OK` ✅ |
| ĐB4 `[58]`–`[61]` | ghim `"dat": True` | dòng 18 | **`test_dong18`** — `assert True is False`, `1 failed` | `OK` / `OK` ✅ |
| ĐB5 `[62]`–`[65]` | `xac_dinh_moi_truong` luôn trả `pc_x86` | dòng 20c **và** 20d | **`test_dong20c` + `test_dong20d`** — `2 failed, 27 passed`; `test_dong20b` vẫn xanh | `OK` / `OK` ✅ |
| ĐB6 `[36]`–`[42]` | phá `model.ncnn.bin` của bản 320 (phép loại H2) | số đo phải bùng | 10/10 → **0/10**, `dat` `True` → **`False`** | `model.ncnn.bin: OK` ✅ |

**Cả sáu phép đều bị bắt, không phép nào lọt.** Cây làm việc đã trở lại nguyên trạng: `sha256sum -c`
cho `OK` sau mỗi lần khôi phục, kể cả hiện vật nhị phân trong `models/`.

Hai ghi chú phương pháp về **cơ chế** bắt lỗi (không đổi kết luận, xem GÓP Ý-2):

- ĐB1 làm dòng 08 đỏ qua `FileNotFoundError` rò từ vòng kiểm tệp rỗng phía sau, không qua
  `LoiMoHinh` của chính guard bị gỡ.
- ĐB3 làm dòng 14 đỏ qua `AttributeError: 'NoneType' object has no attribute 'xy'` rò ra từ
  `scripts/export_detector.py:322`, tức luồng đi tiếp rồi sập ở nơi khác.

Cả hai ca vẫn **assert đúng ngữ nghĩa đặc tả đòi** (`pytest.raises(LoiMoHinh, match=…)`), nên đây là
đặc tính của phép đột biến, không phải khiếm khuyết của ca kiểm thử.

### Khối lệnh `python -c` đã dùng

**P-A — `[27/65]`**

```bash
PYTHONIOENCODING=utf-8 python -c "import json; d=json.load(open('results/export_ncnn_20260827_2144.meta.json',encoding='utf-8')); print('moi_truong =',d.get('moi_truong')); print('commit     =',d.get('commit')); print('seed       =',d.get('seed')); print('phien_ban  =',d.get('phien_ban')); print('thoi_diem  =',d.get('thoi_diem')); print('du bay khoa=',set(d)>={'commit','cau_hinh','phien_ban','thiet_bi','thoi_diem','seed','moi_truong'})"
```

**P-B — `[34/65]`** (nội soi backend hai phía)

```bash
PYTHONIOENCODING=utf-8 python -c "
from pathlib import Path
from scripts.export_detector import _chon_mau_anh
from scripts.export_detector_ncnn import _tao_mo_hinh_yolo
anh = _chon_mau_anh(Path('data/impostor/lfw_original'), 1, 42)[0]
for duong_dan in ['models/yolov8n-face.pt', 'models/yolov8n-face-320_ncnn_model']:
    m = _tao_mo_hinh_yolo(duong_dan)
    m.predict(source=str(anh), imgsz=320, verbose=False)
    b = m.predictor.model
    print(duong_dan, '->', type(b).__name__, '| pt =', getattr(b,'pt',None), '| ncnn =', getattr(b,'ncnn',None), '| net =', type(getattr(b,'net',None)))
"
```

**P-C — `[35/65]` và `[40/65]`** (phép đo độc lập 10 ảnh; `[40]` chạy lại y hệt trên bản đã phá)

```bash
PYTHONIOENCODING=utf-8 python -c "
from pathlib import Path
from scripts.export_detector import NGUONG_SAI_SO_DIEM_MOC_TOI_DA_PX, _chon_mau_anh, doc_cau_hinh
from scripts.export_detector_ncnn import kiem_chung_tuong_duong_ncnn
from src.common.config import nap_cau_hinh
cfg = doc_cau_hinh(nap_cau_hinh('configs/detect.yaml'))
anh = _chon_mau_anh(Path('data/impostor/lfw_original'), 10, 42)
kq = kiem_chung_tuong_duong_ncnn(Path(cfg['weights_pt']), Path('models/yolov8n-face-320_ncnn_model'), anh, 320, cfg['conf_threshold'], cfg['iou_threshold'], NGUONG_SAI_SO_DIEM_MOC_TOI_DA_PX)
print('khop_so_mat =', kq['n_khop_so_mat'], '/', kq['n_anh'])
print('iou_trung_binh =', kq['iou_trung_binh'])
print('sai_so_diem_moc_trung_binh =', kq['sai_so_diem_moc_trung_binh'])
print('dat =', kq['dat'])
"
```

Phép đột biến ĐB6 nằm giữa hai lượt chạy P-C:

```bash
cp models/yolov8n-face-640_ncnn_model/model.ncnn.bin models/yolov8n-face-320_ncnn_model/model.ncnn.bin   # [39/65]
cp ~/p204-backup/model.ncnn.bin.320 models/yolov8n-face-320_ncnn_model/model.ncnn.bin                    # [41/65]
sha256sum -c ~/p204-backup/SHA256.bin320                                                                 # [42/65] -> OK
```

---

## 3. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §0 — bốn việc của vòng 2 | ✅ đủ cả bốn: `xac_dinh_moi_truong` (`:336-354`), khoá `moi_truong` (`:379`), ba ca 20b/20c/20d (`tests:371-384`, xanh ở `[11]`), lượt chạy lại sinh `…_2144.*` (`[7]`, `[27]`, `[30]`) |
| §2 — danh sách trắng | ✅ đúng ba tệp, `requirements-dev.txt` thêm đúng một dòng (`[3]`, `[5]`) |
| §4 — tham số từ `configs/detect.yaml` | ✅ sáu khoá đọc qua `doc_cau_hinh`; `opset`/`simplify` có comment giải trình tại `:446-448`; grep hardcode rỗng (`[17]`) |
| §5.1 — tái dùng, không viết lại | ✅ chín ký hiệu import nguyên vẹn từ `scripts/export_detector.py` (`:31-41`); `git diff --stat` xác nhận tệp nguồn không bị sửa (`[2]`) |
| §5.2 — chữ ký sáu hàm mới | ✅ khớp từng ký tự: `export_ncnn_mot_kich_thuoc` (`:130-136`), `kiem_tra_thu_muc_ncnn` (`:196`), `kiem_chung_tuong_duong_ncnn` (`:234-242`), `xac_dinh_moi_truong` (`:336`), `thu_thap_metadata_ncnn` (`:357`), `main` (`:410`) |
| §6 — giao diện dòng lệnh | ✅ năm cờ đúng tên và đúng mặc định (`:423-435`), xác nhận bằng bảng dry-run `[32]` |
| §7.1 — không export thăm dò | ✅ không có vết chạy nào ngoài lượt của người dùng (`[33]`) |
| §7.2 — export qua `ultralytics`, import cục bộ | ✅ `[16]`, `[14]` |
| §7.3 — ba ngưỡng, so sánh cùng độ phân giải, guard điểm mốc | ✅ ngưỡng lấy từ hằng số import; `imgsz` truyền cho **cả hai** phía (`:282`, `:286`); guard `:101-127` gọi ở `:289` **chỉ** cho phía NCNN; ĐB3 chứng minh guard có ca canh |
| §7.3 — nghi vấn H1/H2 | ✅ **H2 bị bác bỏ bằng ĐB6** — xem §1 |
| §7.4 — ghi `.json` + `.meta.json`, đủ bảy khoá, `moi_truong` hợp lệ | ✅ `[27]`, `[15]` |
| §8 — 31 ca kiểm thử (27 dòng + 08b, 20b, 20c, 20d) | ✅ 29 không-slow xanh (`[11]`) + 2 slow xanh (`[31]`); ĐB1–ĐB5 chứng minh 6 ca canh đúng chỗ |
| §10 — ràng buộc kỹ thuật | ✅ `black`/`ruff` sạch; type hints và docstring tiếng Việt đủ; `print()` chỉ ở phần in bảng CLI (`[25]`); `pathlib` xuyên suốt |
| §11 — ngoài phạm vi | ✅ không đụng `src/detector/`, không đo hiệu năng, không sửa `configs/`, không sửa `models/README.md`, không sửa `scripts/export_detector.py` (`[2]`) |
| **Trình bày số đo trên bảng CLI** | ❌ **xem CẦN SỬA-1** |

---

## 4. Lỗi phải sửa

### 🟡 CẦN SỬA-1 — Bảng CLI làm tròn số đo thành "0.00 px" và "1.0000", nói mạnh hơn thứ đã đo (R5)

**Vị trí**: `scripts/export_detector_ncnn.py:392-406` (hàm `_in_bang_ket_qua`)

```python
iou_tb = "n/a" if kq["iou_trung_binh"] is None else f"{kq['iou_trung_binh']:.4f}"
iou_min = "n/a" if kq["iou_nho_nhat"] is None else f"{kq['iou_nho_nhat']:.4f}"
ss_tb = (
    "n/a"
    if kq["sai_so_diem_moc_trung_binh"] is None
    else f"{kq['sai_so_diem_moc_trung_binh']:.2f}"
)
```

Bảng in ra ở lượt chạy thật 21:44 vì thế là:

```
| 320 | 50 | 50 | 1.0000 | 1.0000 | 0.00 | 0.00 | DAT |
| 640 | 50 | 50 | 1.0000 | 1.0000 | 0.00 | 0.00 | DAT |
```

trong khi số thật trong `results/export_ncnn_20260827_2144.json` là `iou_trung_binh
0.9999996117008513` và `sai_so_diem_moc_trung_binh 2.3293407740554064e-05`.

**Vì sao**: đây là bảng mà con người đọc và chép — vào nhật ký tuần, vào báo cáo tuần, vào Chương 2
§2.6.3. Đọc "sai số 0.00 px, IoU 1.0000" thì kết luận tự nhiên là *"bản NCNN khớp tuyệt đối với bản
gốc"*. Đó là một tuyên bố **mạnh hơn hẳn** thứ đã đo — thứ đã đo là *"khớp tới mức 10⁻⁵ px"* — và
nó không chứng minh được. Chính notebook của dự án đã nhận diện và từ chối cách trình bày này:
`notebooks/03_xac_minh_export_ncnn.ipynb`, ô markdown mục 3.2 — *"Nếu hiển thị làm tròn hai chữ số
thập phân, cột sai số hiện ra `0.00` và bảng sẽ nói sai… Giữ nguyên bậc độ lớn là cách trình bày
trung thực (R5)"* — rồi in bằng ký hiệu khoa học. Cùng một đại lượng, cùng một repo mà hai nơi
trình bày ngược nhau, và nơi **sai** lại là nơi sinh ra số chính thức.

**Sửa**: đổi định dạng của bốn cột số trong `_in_bang_ket_qua` sang ký hiệu khoa học, giữ nguyên mọi
thứ khác (hàm này không tính toán gì, chỉ hiển thị — dữ liệu trong `.json` đã đúng, không phải sửa):

```python
iou_tb = "n/a" if kq["iou_trung_binh"] is None else f"{kq['iou_trung_binh']:.9f}"
iou_min = "n/a" if kq["iou_nho_nhat"] is None else f"{kq['iou_nho_nhat']:.9f}"
ss_tb = (
    "n/a"
    if kq["sai_so_diem_moc_trung_binh"] is None
    else f"{kq['sai_so_diem_moc_trung_binh']:.3e}"
)
ss_max = (
    "n/a"
    if kq["sai_so_diem_moc_lon_nhat"] is None
    else f"{kq['sai_so_diem_moc_lon_nhat']:.3e}"
)
```

Không cần chạy lại lượt sinh số liệu: `results/export_ncnn_20260827_2144.json` **không đổi** vì
`ghi_ket_qua` ghi giá trị đầy đủ, không qua `_in_bang_ket_qua`. Chỉ cần `[8]`, `[9]`, `[11]` xanh
lại và dán bảng CLI mới (chạy lại `--dry-run` là đủ để chứng minh mã còn chạy; bảng số thật lấy từ
`.json` đã có).

---

## 5. 🔵 Góp ý (không chặn — người dùng quyết định)

1. **`P2-01` mắc đúng lỗi trình bày của CẦN SỬA-1** tại `scripts/export_detector.py:680-685`
   (`:.4f` cho IoU, `:.2f` cho sai số). Tệp này bị §11 cấm sửa trong mã việc hiện tại, và lượt
   review `P2-01` đã bỏ sót. *Đề xuất*: mở mã việc nhỏ `P2-01c` sửa đúng bốn chuỗi định dạng, để
   bảng ONNX và bảng NCNN đặt cạnh nhau được trong Chương 4. Chi phí ~10 phút, lợi ích: hai bảng
   cùng thước đo, cùng cách trình bày.
2. **Ghi cơ chế bắt lỗi vào ca dòng 08 và 14.** ĐB1 và ĐB3 đều làm ca đỏ, nhưng qua ngoại lệ rò từ
   chỗ khác (`FileNotFoundError`, `AttributeError` ở `scripts/export_detector.py:322`) chứ không qua
   `LoiMoHinh` của guard. Ca vẫn assert đúng ngữ nghĩa đặc tả đòi nên **không phải lỗi**. Nếu muốn
   chặt hơn, dòng 14 có thể thêm một ca cho nhánh `kp.xy` **rỗng** (`scripts/export_detector_ncnn.py:121`)
   — hiện chỉ nhánh `keypoints is None` được phủ. Đặc tả §8 dòng 14 không đòi, nên đây là góp ý.
3. **Ghi bằng chứng backend vào `.meta.json`.** Mã việc này phải huy động một phép đột biến thủ công
   (ĐB6) mới trả lời được câu hỏi "bản NCNN có thật sự chạy không". Nếu `thu_thap_metadata_ncnn` ghi
   thêm `backend_thuc_te` lấy từ `type(mo_hinh.predictor.model.net).__module__`, câu hỏi đó tự trả
   lời trong mọi lượt chạy về sau, kể cả trên Pi 5. Chi phí ~5 dòng; lợi ích: `P2-05` và bước 2.6
   không phải dựng lại phép thử này.
   ⚠️ Nếu làm, **không** dùng `AutoBackend.pt` / `AutoBackend.ncnn`: `[34/65]` cho thấy cả hai trả
   `None` trong `ultralytics 8.4.39`.
4. **Hiện vật trong `models/` là bản 22:42–22:43, muộn hơn lượt đo 21:44** (`[28]`, `[30]`). Chúng
   do `notebooks/03_…ipynb` export lại sinh ra, không phải hiện vật đã tạo ra con số. Nội dung khớp
   `sha256` với bảng notebook (`[29]`) nên **dùng được**, nhưng khi điền bảng B3 của
   `models/README.md` nên ghi rõ nguồn `sha256` là lượt notebook 27/08 22:42, không phải lượt script
   21:44. Không có thư mục thừa `models/yolov8n-face_ncnn_model` còn sót (đã kiểm).
5. **Chuỗi truy vết R17 đứt một mắt**: `.meta.json` ghi `commit = fcb3a95` — commit của **đặc tả**,
   vì mã sinh ra số đo chưa được commit khi chạy. Đây là hệ quả của quy trình "đo trước, commit sau",
   không phải lỗi của người cài đặt. *Đề xuất*: sau khi gộp mã việc, chạy lại một lượt §12b để
   `.meta.json` mang commit của mã đã gộp, đối chiếu thấy số trùng khớp rồi mới xoá bộ `_2144`
   (đúng cách đã làm với bộ `_2027`). Chi phí một lượt chạy vài phút; lợi ích: mỗi con số trong
   Chương 4 truy được về đúng dòng mã đã sinh ra nó. Nếu bỏ qua, phải ghi chú trong báo cáo.
6. **`pyproject.toml` không đăng ký marker `slow`** (`[tool.pytest.ini_options]` chỉ có `testpaths`
   và `pythonpath`), nên mọi lượt chạy đều kèm `PytestUnknownMarkWarning` ở
   `test_export_detector.py`, `test_export_detector_ncnn.py`, `test_yolo_face.py`. Không ảnh hưởng
   kết quả — `-m "not slow"` vẫn lọc đúng, xác nhận ở `[11]` và `[31]`. Tệp nằm ngoài danh sách
   trắng §2 nên **không** sửa ở mã việc này. *Đề xuất*: thêm hai dòng
   `markers = ["slow: ca cần export/nạp mô hình thật"]` trong một commit `chore` riêng.

---

## 6. Việc tiếp theo

Giao lại cho `coder` **một mục duy nhất**:

> Sửa `CẦN SỬA-1` trong biên bản `docs/review/P2-04-export-ncnn.review.md`: đổi định dạng bốn cột số
> của `_in_bang_ket_qua` (`scripts/export_detector_ncnn.py:392-406`) sang ký hiệu khoa học theo đoạn
> mã thay thế đã ghi trong biên bản. Không sửa gì khác. Chạy lại §9 đặc tả (`black`, `ruff`,
> `pytest -m "not slow"` trên host, `--collect-only`) và dán kết quả về.

Sau khi mục đó xanh, vòng review 2 chỉ cần kiểm lại `[3]`, `[5]`, `[8]`, `[9]`, `[11]` và bảng CLI
mới — **không** phải dựng lại năm phép đột biến, vì thay đổi nằm ngoài mọi guard đã kiểm.

Commit dự kiến khi đạt:

```
feat(export): export YOLOv8n-face sang NCNN và kiểm chứng tương đương — P2-04
```

---
---

# Review P2-04-export-ncnn — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-04-export-ncnn.md` (commit `fcb3a95`) |
| **Nhánh** | `feat/p2-04-export-ncnn` (xác nhận bằng `git branch --show-current`) |
| **Ngày** | 2026-08-28 |
| **Người chạy lệnh kiểm định** | người dùng |
| **Phạm vi vòng này** | đúng như §6 vòng 1 đã hẹn: `[3]`, `[5]`, `[8]`, `[9]`, `[11]` + bảng CLI mới; **không** dựng lại ĐB1–ĐB6 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — 0 × CHẶN, 0 × CẦN SỬA, **8 × GÓP Ý** (6 cũ + 2 mới); có **2 điều kiện** trước khi gộp |

---

## 7. Vòng 2 — kiểm định bản đã sửa

### 7.1. Tôi tự đọc lại mã, không dùng đoạn chép của người khác

Đã đọc trực tiếp **toàn bộ** `scripts/export_detector_ncnn.py` (562 dòng) và
`tests/test_export_detector_ncnn.py` (485 dòng) bằng tool đọc tệp, rồi đối chiếu từng vùng với bản
đã chấm ở vòng 1.

**`scripts/export_detector_ncnn.py` — đúng một thay đổi:**

| Vùng | Trạng thái |
|---|---|
| `:1-380` (docstring, import, sáu hàm, guard `_bao_dam_ncnn_co_diem_moc`, `kiem_tra_thu_muc_ncnn`, `kiem_chung_tuong_duong_ncnn`, `xac_dinh_moi_truong`, `thu_thap_metadata_ncnn`) | **giữ nguyên từng dòng**, số dòng không đổi |
| `:383-409` `_in_bang_ket_qua` | **đã sửa** — bốn chuỗi định dạng + 2 dòng comment nêu xuất xứ `CẦN SỬA-1, R5` |
| `:412-562` `main` và `__main__` | **giữ nguyên từng dòng**, dịch đúng `+2` do hai dòng comment |

Ba điểm cần khẳng định vì chúng là nơi dễ hỏng nhất khi sửa hiển thị:

- **Nhánh `"n/a"` còn nguyên** cho cả bốn cột (`:394`, `:395`, `:396-400`, `:401-405`) ⇒ ca "cả hai
  bên không có mặt nào" (dòng 15) vẫn in được, không sập vì format `None`.
- **`_in_bang_ket_qua` vẫn thuần hiển thị**, không tính toán, không đụng `ban_ghi`.
- **`ghi_ket_qua(duong_dan_ra, ban_ghi)` ở `:549` không bị đụng** ⇒ dữ liệu ghi ra `.json` không đi
  qua hàm hiển thị. Xác nhận bằng số: nội dung `results/export_ncnn_20260827_2144.json` **không đổi
  một chữ số nào** so với vòng 1 (`iou_trung_binh 0.9999996117008513`,
  `sai_so_diem_moc_trung_binh 2.3293407740554064e-05`, `dat true`). Không phải chạy lại lượt đo.

**`tests/test_export_detector_ncnn.py` — đúng hai thay đổi, không có thay đổi thứ ba:**

| Vùng | Trạng thái |
|---|---|
| `:28` | **thêm** `_in_bang_ket_qua,` vào khối import |
| `:39-446` — toàn bộ tiện ích chung, năm lớp giả lập, và **29 ca cũ** | **giữ nguyên từng dòng**, dịch đúng `+1` |
| `:448-485` | **thêm** `test_dong28_bang_cli_dung_ky_hieu_khoa_hoc` |

Đây là điểm biên bản vòng 1 đã cảnh báo — "nới ca kiểm thử để lấy màu xanh là lỗi nặng" (CB-6) —
nên tôi đối chiếu **từng ca một**, không chỉ đếm tên:

- `test_dong08/09/10` vẫn `pytest.raises(LoiMoHinh, match="param"/"bin"/"metadata")` (`:223`, `:229`,
  `:246`) — không ca nào bị hạ xuống `pytest.raises(Exception)` hay bỏ `match`.
- `test_dong11` vẫn ghi `.bin` rỗng bằng `write_bytes(b"")` rồi đòi `LoiMoHinh` (`:254-256`).
- `test_dong14` vẫn đòi `LoiMoHinh` **và** `"điểm mốc" in str(exc_info.value)` (`:283-287`).
- `test_dong17` vẫn `assert kq["dat"] is True` + `iou_nho_nhat == 1.0`; `test_dong18` vẫn
  `assert kq["dat"] is False` với 2/10 ảnh lệch (`:326-327`, `:330-346`).
- `test_dong20c/20d` vẫn monkeypatch đủ hai yếu tố `/.dockerenv` và `platform.machine` (`:376-385`).
- `test_dong23` vẫn `assert main(["--dry-run"]) == 0` kèm hai phép chụp `rglob` (`:410-419`).

**Không một assert nào bị nới, xoá hay đổi giá trị.** Số học của bộ test khớp với kết luận đó:

| | Vòng 1 | Vòng 2 | Chênh |
|---|---|---|---|
| Ca trong tệp `test_export_detector_ncnn.py` | 31 | 32 | **+1** |
| Toàn repo, host, `-m "not slow"` | 410 passed | 411 passed | **+1** |
| Toàn repo, container `faceid:arm64` | 409 passed, 1 skipped | 410 passed, 1 skipped | **+1** |

Tăng đúng một ở cả ba nơi ⇒ không ca nào bị xoá hay đổi tên để giấu một ca đỏ.

### 7.2. Kết quả kiểm máy vòng 2

**Người dùng chạy ngày 28/08/2026**, PowerShell (host) và Git Bash (container).

| # | Lệnh | Kết quả |
|---|---|---|
| `[V2-1]` | `git branch --show-current` | `feat/p2-04-export-ncnn` ✅ đúng nhánh |
| `[V2-2]` | `python -m black --check --line-length 100 scripts\export_detector_ncnn.py tests\test_export_detector_ncnn.py` | `2 files would be left unchanged` ✅ |
| `[V2-3]` | `python -m ruff check scripts\export_detector_ncnn.py tests\test_export_detector_ncnn.py` | `All checks passed!` ✅ |
| `[V2-4]` | `python -m pytest tests/test_export_detector_ncnn.py -v -m "not slow"` | `collected 32 items / 2 deselected / 30 selected` → **30 passed** ✅, ca cuối là `test_dong28_bang_cli_dung_ky_hieu_khoa_hoc` |
| `[V2-5]` | `python -m pytest tests/test_export_detector_ncnn.py --collect-only -m "not slow"` | `30/32 tests collected` ✅ — không gói nặng nào import ở mức module |
| `[V2-6]` | `python -m pytest -q -m "not slow"` | **411 passed, 9 deselected** ✅ (vòng 1: 410) |
| `[V2-7]` | `docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"` | **410 passed, 1 skipped, 9 deselected** trong 12 phút ✅ (vòng 1: 409) |
| `[V2-8]` | `git status --short --untracked-files=all` | so vòng 1 **chỉ thêm** `?? docs/review/P2-04-export-ncnn.review.md` — chính biên bản này ✅ |
| `[V2-9]` | `git status … -- src scripts tests configs` (suy ra từ `[V2-8]`) | vẫn đúng hai tệp §2 ✅ |
| `[V2-10]` | `git diff -- requirements-dev.txt` | vẫn đúng một dòng `+ncnn==1.0.20260526` ✅ |
| `[V2-11]` | `Select-String … '^import ncnn\|^import torch\|^from ultralytics'` | rỗng ✅ |
| `[V2-12]` | `Select-String … '0\.5\|0\.45\|320\|640\|0\.90\|0\.95\|5\.0'` (script) | rỗng ✅ — bản sửa **không** đưa hằng số nào vào mã |
| `[V2-13]` | `Select-String … 'except Exception'` | rỗng ✅ |
| `[V2-14]` | `Select-String … 'raise (ValueError\|TypeError)'` | rỗng ✅ |
| `[V2-15]` | `results/` sau vòng sửa | vẫn đúng bộ `_2144`, **không** tệp mới ⇒ `coder` **không** chạy lượt ghi thật (đúng R42 và §9 đặc tả) ✅ |

Lệnh sinh ra bảng CLI mới (chỉ đọc, không ghi gì):

```powershell
python -c "import json; from scripts.export_detector_ncnn import _in_bang_ket_qua; _in_bang_ket_qua(json.load(open('results/export_ncnn_20260827_2144.json',encoding='utf-8'))['theo_kich_thuoc'])"
```

### 7.3. CẦN SỬA-1 — **ĐÃ ĐÓNG**

Cùng một tệp số liệu, cùng một hàm, hai cách trình bày:

| Cột | Vòng 1 (320) | Vòng 2 (320) | Số thật trong `.json` |
|---|---|---|---|
| IoU TB | `1.0000` | **`0.999999600`** | `0.9999995998221927` |
| IoU min | `1.0000` | **`0.999997537`** | `0.9999975374391337` |
| Sai số mốc TB (px) | `0.00` | **`2.487e-05`** | `2.4870081959611645e-05` |
| Sai số mốc max (px) | `0.00` | **`5.502e-05`** | `5.501634636633284e-05` |

Bảng mới:

```
| Kích thước | Số ảnh | Khớp số mặt | IoU TB | IoU min | Sai số mốc TB (px) | Sai số mốc max (px) | Đạt |
|---|---|---|---|---|---|---|---|
| 320 | 50 | 50 | 0.999999600 | 0.999997537 | 2.487e-05 | 5.502e-05 | DAT |
| 640 | 50 | 50 | 0.999999624 | 0.999997180 | 2.172e-05 | 3.815e-05 | DAT |
```

Bậc độ lớn được giữ đúng ở cả bốn cột. Bảng không còn tuyên bố "khớp tuyệt đối"; nó nói đúng thứ đã
đo là "khớp tới mức 10⁻⁵ px". Cách trình bày này giờ **thống nhất** với
`notebooks/03_xac_minh_export_ncnn.ipynb` mục 3.2 — cùng một đại lượng, cùng một quy ước.
Số liệu trong `results/*.json` không đổi, nên mọi kết luận của vòng 1 vẫn nguyên giá trị.

### 7.4. Ca kiểm thử thêm ngoài §8 — chấp nhận, kèm kiến nghị sửa đặc tả

`tests/test_export_detector_ncnn.py:453-484`, `test_dong28_bang_cli_dung_ky_hieu_khoa_hoc`.

**Đánh giá độc lập** (tôi đọc mã ca, không dựa nhận xét của ai):

- Ca **cô lập đúng dòng dữ liệu** trước khi assert: lọc dòng bắt đầu `"| 320 |"`, khẳng định
  `len(dong_320) == 1`, tách theo `|` rồi lấy `o[6]`, `o[7]` — đúng hai cột sai số. Không phải phép
  tìm chuỗi trên toàn đầu ra, nên không xanh nhờ may mắn.
- Assert có **cả vế phủ định lẫn vế khẳng định** (`"0.00" not in …` và `"e-05" in …`), tức bắt được
  cả trường hợp quay về `:.2f` lẫn trường hợp in ra chuỗi vô nghĩa.
- Số trong ca là **dữ liệu dựng cho phép thử hiển thị**, không ghi vào `results/`, không đi vào báo
  cáo ⇒ không phải CA-7.
- Docstring **ghi rõ xuất xứ** ("CẦN SỬA-1, `docs/review/P2-04-export-ncnn.review.md`. Chưa có dòng
  tương ứng trong §8 đặc tả") ⇒ người đọc sau phân biệt được với ca do người cài đặt tự thêm.

**Kết luận**: **không** phải vi phạm phạm vi. `tests/test_export_detector_ncnn.py` nằm **trong** danh
sách trắng §2; ca mới chỉ ghim lại đúng khiếm khuyết mà biên bản vòng 1 vừa bắt, không nới bất kỳ ca
nào, và làm CẦN SỬA-1 khó tái phát trong lần refactor sau. Đây là kết quả tốt, không phải lỗi.

Nhưng nó tạo ra một khe lệch **giữa mã và đặc tả**: §8 mô tả bảng nghiệm thu là nguồn sự thật, và
bảng đó hiện **không có** dòng 28. Để đặc tả tiếp tục là thứ đọc-là-đủ, cần một kiến nghị:

> **Kiến nghị `spec-writer`** — bổ sung vào `docs/dac-ta/P2-04-export-ncnn.md` §8 một mục §8.6
> *"Trình bày số đo"*, dòng 28: *"Bảng CLI giữ đúng bậc độ lớn, không làm tròn sai số về `0.00`
> — assert tối thiểu: cột sai số của dòng `| 320 |` không chứa `0.00` và chứa `e-05`"*. Kèm theo,
> sửa câu "Chưa có dòng tương ứng trong §8 đặc tả" trong docstring của ca cho khỏi lạc hậu.
> Chi phí: một commit `docs(dac-ta)`. Lợi ích: đặc tả và mã khớp lại, `P2-05` kế thừa được quy ước
> trình bày này thay vì phát minh lại.

Ghi nhận thêm cho minh bạch: việc thêm ca này do **phiên chính cho phép**, không phải người cài đặt
tự ý mở rộng phạm vi.

### 7.5. Đối chiếu lại các mục đặc tả bị ảnh hưởng

| Mục | Kết luận vòng 2 |
|---|---|
| §2 danh sách trắng | ✅ không đổi — vẫn đúng ba tệp (`[V2-8]`, `[V2-10]`) |
| §8 bảng nghiệm thu (31 ca) | ✅ 30 không-slow xanh + 2 slow đã xanh ở vòng 1; **thêm** ca 28 ngoài bảng — xem §7.4 |
| §10 ràng buộc kỹ thuật | ✅ `black`/`ruff` sạch (`[V2-2]`, `[V2-3]`); `print()` vẫn chỉ ở phần in bảng CLI |
| §11 ngoài phạm vi | ✅ không đụng `scripts/export_detector.py`, `configs/`, `src/`, `models/README.md` |
| §7.3 nghi vấn H1/H2 | ✅ kết luận vòng 1 giữ nguyên — thay đổi vòng 2 nằm ngoài mọi guard, và số liệu `.json` không đổi |
| Trung thực số liệu (R5) | ✅ **đã đóng** — xem §7.3 |

Năm phép đột biến ĐB1–ĐB5 **không cần dựng lại**: vùng mã chúng nhắm tới (`:196-231`, `:101-127`,
`:316-333`, `:336-354`) không bị chạm, đã xác nhận bằng đọc mã ở §7.1, và 29 ca cũ vẫn nguyên văn.

---

## 8. Phán quyết vòng 2

### 🟡 ĐẠT CÓ ĐIỀU KIỆN

Không còn mục 🔴 hay 🟡. Ba lệnh máy sạch trên host, bộ test xanh cả trên host lẫn trong
`faceid:arm64`, mọi tiêu chí §8 thoả, và nghi vấn trung tâm của mã việc đã được đóng bằng phép thử
chủ động chứ không bằng lập luận.

**Được commit**, với **hai điều kiện** — cả hai là việc của người dùng, không phải của người cài đặt:

1. **`.claude/**` không đi chung commit của mã việc.** `git status` cho thấy `CLAUDE.md`,
   `.claude/agents/coder.agent.md`, `.claude/instructions/experiment-protocol.instructions.md`,
   `docs/quy-tac-cai-dat.md` đang sửa dở. Theo `CLAUDE.md` §2.9, chúng thuộc khung quy trình và phải
   đi commit riêng loại `chore(quy-trinh)`. Commit của `P2-04` chỉ gồm:
   `scripts/export_detector_ncnn.py`, `tests/test_export_detector_ncnn.py`, `requirements-dev.txt`,
   `notebooks/03_xac_minh_export_ncnn.ipynb`, `results/export_ncnn_20260827_2144.{json,meta.json}`,
   `docs/review/P2-04-export-ncnn.review.md`.
2. **Kiến nghị §7.4 được xử lý** — hoặc bổ sung dòng 28 vào §8 đặc tả (một commit `docs(dac-ta)`),
   hoặc người dùng quyết định giữ nguyên và ghi nhận rằng mã có một ca ngoài bảng nghiệm thu.
   Không xử lý thì lần review sau sẽ lại phải điều tra ca này từ đầu.

Commit message đề xuất:

```
feat(export): export YOLOv8n-face sang NCNN và kiểm chứng tương đương — P2-04
```

### Tình trạng tám mục 🔵 GÓP Ý

| # | Mục | Tình trạng sau vòng 2 |
|---|---|---|
| 1 | `P2-01` cũng làm tròn bảng CLI (`scripts/export_detector.py:680-685`) | **còn nguyên, và giờ cấp thiết hơn**: bảng NCNN đã dùng ký hiệu khoa học, bảng ONNX thì chưa ⇒ hai bảng trong Chương 4 đang lệch quy ước. Đề xuất mã việc `P2-01c` |
| 2 | Thêm ca cho nhánh `kp.xy` rỗng (`:121`) | còn nguyên |
| 3 | Ghi `backend_thuc_te` vào `.meta.json` | còn nguyên — nếu làm thì hợp lý nhất là gộp vào `P2-05` |
| 4 | `sha256` hiện vật `models/` là của lượt notebook 22:42, không phải lượt script 21:44 | còn nguyên — nhớ ghi rõ khi điền bảng B3 `models/README.md` |
| 5 | `.meta.json.commit` là commit đặc tả, không phải commit mã | còn nguyên — chạy lại §12b **sau khi gộp** thì mắt xích truy vết liền lại |
| 6 | `pyproject.toml` chưa đăng ký marker `slow` | còn nguyên — commit `chore` riêng |
| **7** | **Ca 28 chưa có dòng tương ứng trong §8 đặc tả** | **mới** — xem §7.4, là điều kiện 2 ở trên |
| **8** | **Ca 28 chỉ ghim hai cột sai số, chưa ghim hai cột IoU** (`tests:479-484` dùng `o[6]`, `o[7]`) | **mới** — nếu ai đó đưa IoU về `:.4f`, bảng lại in `1.0000` mà ca vẫn xanh. Thêm hai dòng `assert o[4] != "1.0000"` là đủ. Không chặn vì hại của cột IoU nhẹ hơn hẳn cột sai số |

### Việc tiếp theo sau khi gộp

1. Cập nhật `models/README.md` bảng B3 bằng kích thước và `sha256` ở lệnh `[29/65]`, ghi rõ nguồn
   là lượt export 27/08 22:42 (GÓP Ý-4).
2. Ghi `docs/nhat-ky/tuan-06.md`: `P2-04` xong, trích số từ
   `results/export_ncnn_20260827_2144.json` — **dùng ký hiệu khoa học**, không chép "0.00".
3. Mở `P2-05` (backend NCNN trong `src/detector/`) — mã việc thật sự mở khoá ma trận đo bước 2.6.
   Chương 2 §2.6.3 vẫn treo `[CHƯA VIẾT — CHẶN VÌ CHƯA ĐO]` cho tới khi có Pi 5.
