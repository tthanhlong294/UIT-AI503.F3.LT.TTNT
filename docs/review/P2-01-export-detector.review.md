# Review P2-01-export-detector — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-01-export-detector.md` |
| **Nhánh** | `feat/p2-01-export-detector` |
| **HEAD khi review** | `54f82f7` |
| **Ngày** | 2026-08-18 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — 1 × CHẶN-B, 3 × CẦN SỬA, 4 × GÓP Ý |

---

## 1. Kết luận về hai nghi vấn ưu tiên

### 1.1. Bản ONNX **CÓ** được chạy thật — bác bỏ giả thuyết "so mô hình với chính nó"

Không kết luận từ việc đọc mã. Bốn phép kiểm độc lập, chạy trực tiếp trên
`kiem_chung_tuong_duong` với trọng số và ảnh thật:

| Phép | Cách làm | Kết quả quan sát được |
|---|---|---|
| **P1** | Truyền `onnx_path` trỏ tới tệp rác (200 byte ngẫu nhiên) | **Hỏng to tiếng**: `onnxruntime … InvalidProtobuf : Load model from …rac.onnx failed:Protobuf parsing failed.` — **không** quay về `.pt`, **không** cho IoU ≈ 1 |
| **P2** | `onnx_path` trỏ tệp không tồn tại | `FileNotFoundError: '…khong_ton_tai.onnx' does not exist` |
| **P3** | Giữ nguyên đồ thị, **nhân 0,5 vào 3 initializer conv** rồi lưu ra `hong.onnx` | Số đo **sụp đổ**: `n_khop_so_mat 1/5`, `iou_trung_binh 0.9279`, `sai_so_moc 3.82 px`, `dat: False` — chứng minh **giá trị số do ONNX sinh ra** mới là thứ đem so, không phải một bản sao của `.pt` |
| **P4** | Nội soi đối tượng sau khi nạp | `type = ultralytics.nn.autobackend.AutoBackend`; `backend.session = onnxruntime…InferenceSession`; `session._model_path = …\models\yolov8n-face-320.onnx`; `input = [('images', [1, 3, 320, 320])]`; provider `CPUExecutionProvider` |

**P3 là phép quyết định.** Nếu ONNX không được chạy, việc làm hỏng trọng số bên trong tệp
`.onnx` sẽ **không** ảnh hưởng gì tới kết quả. Ở đây nó phá tan kết quả. Ba phép còn lại loại
trừ nốt khả năng nạp nhầm đường dẫn hay fallback im lặng.

Nguyên nhân IoU = 0,9999995 **là chính đáng**: `scripts/export_detector.py:371` truyền
`task="pose"` khi nạp, ONNX chạy đúng nhánh hậu xử lý pose, và sai khác còn lại chỉ là thứ
tự phép toán float32 giữa PyTorch CPU và onnxruntime CPU.

### 1.2. Tái lập được **từng chữ số** con số đã báo cáo

Chạy lại độc lập khối `320` với cùng seed 42, cùng 50 ảnh:

```
TOI DO LAI  : {"n_anh": 50, "n_khop_so_mat": 50, "iou_trung_binh": 0.9999995612093268,
               "iou_nho_nhat": 0.9999962742557785,
               "sai_so_diem_moc_trung_binh": 1.9229614461161672e-05,
               "sai_so_diem_moc_lon_nhat": 3.411968959808029e-05, "dat": true}
BAO CAO GHI : (khối "320" trong results/export_detector_20260818_0942.json — GIỐNG HỆT)
KHOP HOAN TOAN: True
```

Số trong `results/` là số thật, tái lập được, đạt R6.

### 1.3. So sánh **công bằng** về độ phân giải — đạt

`scripts/export_detector.py:379` và `:382` truyền `imgsz=imgsz` cho **cả hai** phía. Kiểm
bằng số đo chứ không chỉ đọc mã:

| Cách chạy | IoU trung bình | Ghi chú |
|---|---|---|
| `.pt@320` vs `.onnx@320` (mã hiện tại) | **0,9999996** | số đã báo cáo |
| `.pt@320` vs `.pt@640` (mô phỏng lỗi "quên truyền imgsz") | **0,7720** | một ảnh IoU = 0, sai số mốc 117 px |

Nếu `imgsz` chỉ được truyền cho một phía, con số sẽ rơi về mức ~0,77 chứ không thể là
0,99999. Thêm một chốt chặn cứng: đồ thị ONNX xuất ra có **đầu vào kích thước cố định**, nên
chạy bản 640 ở `imgsz=320` **ném lỗi ngay**:

```
onnxruntime … InvalidArgument : Got invalid dimensions for input: images
 index: 2 Got: 320 Expected: 640
```

Lệch độ phân giải **không thể lọt qua im lặng** trong thiết kế này.

---

## 2. Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `black --check --line-length 100 scripts/… tests/…` | `2 files would be left unchanged` ✅ |
| `black --check --line-length 100 src tests scripts` | `24 files would be left unchanged` ✅ |
| `ruff check scripts/… tests/…` | `All checks passed!` ✅ |
| `ruff check src tests scripts` | `All checks passed!` ✅ |
| `pytest tests/test_export_detector.py -v` | **44 passed**, 15 warnings, 34.79s ✅ |
| `pytest tests/test_export_detector.py -m "not slow" -q` | **38 passed, 6 deselected** ✅ |
| `pytest -q` (toàn repo) | **199 passed** (155 cũ + 44 mới) ✅ |
| `git status --short --untracked-files=all` | 2 tệp mã nguồn ✅ · **4** tệp `results/` ❌ (xem CS-1) |
| **Container ARM64** | ❌ **KHÔNG chạy được** — xem CHẶN-B-1. Docker daemon không khởi động được trên máy này (`npipe:////./pipe/dockerDesktopLinuxEngine` không tồn tại), nên đã **mô phỏng đúng tập gói của `deploy/Dockerfile.arm64`** bằng cách chặn `onnx`/`ultralytics`/`torch` qua `sys.meta_path` |

### Bốn lệnh `grep` §9

| Lệnh | Kết quả | Giải trình |
|---|---|---|
| `grep -n "print("` | **12 dòng** | Tất cả nằm trong `main()` và đều là giao diện CLI: `:568–582` bảng kế hoạch dry-run, `:588` và `:597` thông báo lỗi cho người dùng (**bắt buộc** — dòng 37/38 §8 assert bằng `capsys.readouterr().out`), `:668–681` bảng kết quả. Ngoài `main()` **không có** `print()` nào; phần còn lại dùng `logger`. **Hợp lệ theo ghi chú §9.** |
| `grep -nE "0\.5\|0\.45\|320\|640\|\b12\b"` | **rỗng** ✅ | Không hardcode giá trị thực nghiệm |
| `grep -n "except Exception"` | **rỗng** ✅ | |
| `grep -nE "raise (ValueError\|TypeError)"` | **6 dòng** (`:251, :253, :255, :257, :260, :265`) | Toàn bộ nằm trong `so_sanh_mot_anh` và **do chính đặc tả §5 bắt buộc** (`Raises: ValueError: mảng sai hình dạng`) cùng dòng 25b (`pytest.raises(ValueError)`). Đây là **mâu thuẫn nội bộ của đặc tả** (§9 đòi rỗng ≠ §5 đòi `ValueError`), không phải lỗi người cài đặt — xem GÓP Ý-3 |

### Quét mẫu vi phạm §2 rubric

| Mẫu | Kết quả |
|---|---|
| `except:` trần / nuốt lỗi | rỗng ✅ |
| Đường dẫn tuyệt đối máy cá nhân | rỗng ✅ |
| Secret trong code | rỗng ✅ |
| Test giả (`assert True`, `pass` trần) | rỗng ✅ |
| `logger.<lv>(f"…")` | rỗng ✅ — dùng lazy formatting `%s` đúng chuẩn |
| Số magic trong so sánh `[<>]=?\s*0\.\d` | rỗng ✅ |
| Nạp model trong vòng lặp (CB-5) | ✅ **Không vi phạm** — `:370–371` nạp `YOLO` **ngoài** vòng `for anh in danh_sach_anh:` (`:378`) |
| `import torch` đầu file | ✅ `torch`/`ultralytics` chỉ import **cục bộ trong thân hàm** (`:175, :368, :498–501`), đúng §10 |

---

## 3. Kiểm đột biến — tự chạy lại, không tin báo cáo

Mỗi phép: đọc/ghi bằng `open(..., newline="")`, chạy `pytest -m "not slow"`, khôi phục,
đối chiếu `sha256`.

`sha256` gốc: `0a08e66c936b825081f95f5d73ecb9c2c5f52bad6ad12a03c25b66da1d2d3681`

| # | Phép đột biến | Đặc tả đòi đỏ | **Thực đo** | Kết luận | sha256 khôi phục |
|---|---|---|---|---|---|
| **ĐB1** | Xoá khối kiểm `conf_threshold` (`:108–115`) | 10, 12 | **10, 12** (2 failed / 36 passed) | ✅ Dòng 12 **thật sự** phủ đủ năm khoá | khớp ✅ |
| **ĐB2a** | Chỉ `:300` → `dat = True` | 21, 23, 23b, 24 | 23, 23b, 24 (3 failed) | dòng 21 không đỏ vì `dat` của nhánh lệch số mặt nằm ở `return` sớm `:274–282`, không đi qua `:300` | khớp ✅ |
| **ĐB2b** | **"luôn gán `dat = True`"** đúng nghĩa — cả `:300` lẫn mọi `"dat": False` | 21, 23, 23b, 24 | **21, 23, 23b, 24** (4 failed) | ✅ Đạt đúng đặc tả | khớp ✅ |
| **ĐB3** | Xoá nhánh chặn `danh_sach_anh` rỗng (`:365–366`) | 29 | **29** (1 failed) | ✅ | khớp ✅ |
| **ĐB4** | `dat = bool(sai_so_diem_moc_max <= sai_so_diem_moc_toi_da)` — bỏ `iou_toi_thieu` | 23, 23b | **23, 23b** (2 failed) | ✅ Tham số ngưỡng IoU **không** bị bỏ qua | khớp ✅ |

`sha256` cuối cùng khớp gốc. `git status` sau toàn bộ phép kiểm **không phát sinh tệp nào**;
`sha256` của `models/yolov8n-face-320.onnx` giữ nguyên `437e2092…`.

> ĐB2a/ĐB2b: đặc tả viết "luôn gán `dat = True`" — cách đọc trung thành nhất (ĐB2b) cho đủ
> bốn ca đỏ. Bộ kiểm thử **đạt** yêu cầu ĐB2.

---

## 4. Quét AST — đối chiếu 1–1 với 44 dòng §8

```
Tổng hàm test: 44
Mã ca: 01…12, 13…19, 20, 21, 22, 23, 23b, 24, 25, 25b, 26, 29, 27, 28, 30…35, 36…42
THIẾU: []      THỪA: []
```

**44/44, ánh xạ 1–1 tuyệt đối.** Không dòng nào thiếu ca test, không ca test nào mồ côi.

Hàm phụ trợ (không phải ca test): `_cfg_co_ban`, `_sao_chep_weights_tam`, `_vai_anh_lfw_that`,
`_ban_ghi_hop_le`, fixture `_onnx_module_export`.

---

## 5. Bộ cấu hình hỏng tự dựng — không tin danh sách của đặc tả

Tự sinh **244 trường hợp**: 8 khoá × 26 giá trị thù địch (`None`, `""`, `[]`, `{}`, `True`,
`False`, `nan`, `inf`, `-0.0`, `b"320"`, `(320,)`, `[[320]]`, `[320, True]`, `10**9`, …)
+ 10 ca cấu trúc hỏng (`cfg=None`, `cfg="chuỗi"`, `cfg=[1,2]`, `export=None`, `export="abc"`,
`export=[1]`, `inference=None`, `inference="x"`, thiếu `export`, thiếu `inference`)
+ 8 ca thiếu từng khoá.

| Tiêu chí | Kết quả |
|---|---|
| Rò `ValueError` / `TypeError` thay vì `LoiCauHinh` | **0** ✅ |
| Không ném gì trong khi đáng lẽ phải ném | **0** ✅ |
| `LoiCauHinh` không nêu giá trị gây lỗi | **0** ✅ |
| Ca "không ném" còn lại (21) | đều là **giá trị hợp lệ thật** (`'abc'` là đường dẫn khác rỗng, `[320]`, `opset=1`, `conf=0.0/1.0` nằm trong `[0,1]`) — đúng, không phải lỗ hổng |

Đáng ghi nhận: `nan` và `inf` **bị chặn đúng** (`0.0 <= nan <= 1.0` cho `False`), `True/False`
bị chặn tường minh bằng `isinstance(x, bool)` trước `isinstance(x, int)` — đây là bẫy Python
mà nhiều bản cài đặt bỏ sót. **`doc_cau_hinh` không còn lỗ nào ngoài danh sách đặc tả.**

---

## 6. Kiểm `.meta.json`

| Trường | Có | Giá trị có thật? |
|---|---|---|
| `commit` | ✅ | `546ba0d428c60ce4117f13e35ee474d2d991b1f1` — `git cat-file -t` xác nhận là **commit thật**, chính là HEAD tại thời điểm chạy 09:42; HEAD sau đó mới nhích lên `54f82f7` (commit sửa §9 đặc tả) ✅ |
| `cau_hinh` | ✅ | Khớp **từng giá trị** với `configs/detect.yaml` (`kich_thuoc [320,640]`, `opset 12`, `batch 1`, `simplify true`, `conf 0.5`, `iou 0.45`) ✅ |
| `phien_ban` | ✅ | `ultralytics 8.4.39 · onnx 1.19.1 · onnxruntime 1.20.1 · torch 2.5.1+cpu` — khớp **chính xác** thư viện đang cài (đã kiểm bằng `python -c "import …"`) ✅ |
| `thiet_bi` | ✅ | `ThanhLong-X1` / `Windows-11-10.0.26200-SP0` ✅ |
| `thoi_diem` | ✅ | `2026-08-18T09:42:17.857716+07:00`, có offset múi giờ ✅ |
| `seed` | ✅ | `42` (thêm, đúng R15) ✅ |

**5/5 trường bắt buộc, mọi giá trị đều truy được.**

---

## 7. Dòng 37 vs 38 — phân biệt được

| Ca | Nhánh | Thông báo |
|---|---|---|
| 37 | `:586–592` thư mục không tồn tại | `"… Chạy 'python scripts/download_lfw.py' để tải bộ dữ liệu LFW trước."` |
| 38 | `:595–598` thư mục rỗng | `"Thư mục ảnh '…' rỗng, không có ảnh hợp lệ nào để kiểm chứng."` |

Hai nhánh mã **tách biệt**, hai thông báo **khác hẳn**. Ca test dòng 38 còn chủ động
assert `"download_lfw" not in ra` (`tests/test_export_detector.py:471`) để chặn khả năng một
nhánh lỗi chung qua được cả hai. ✅ **Đúng tinh thần đặc tả.**

---

## 8. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §2 Phạm vi file | ⚠️ 2 tệp mã nguồn đúng danh sách trắng; **dư một bộ tệp `results/`** (CS-1) |
| §4 Tham số → config | ✅ Đủ 8 khoá, không hardcode, đọc qua `nap_cau_hinh`/`lay_gia_tri` |
| §5 Giao diện hàm | ✅ Sáu chữ ký **khớp từng ký tự** (tên, thứ tự tham số, mặc định, kiểu trả về). ⚠️ `so_sanh_mot_anh` không thực thi đủ ràng buộc hình dạng đã hứa (CS-3) |
| §6 CLI | ✅ Đủ 5 cờ, đúng mặc định |
| §7 Thiết kế kiểm chứng | ✅ Dùng `ultralytics` cho cả hai phía, `imgsz` công bằng, 3 đại lượng đo, ghi `results/` + `.meta.json` |
| §8 Bảng nghiệm thu | ✅ 44/44 ca, ánh xạ 1–1 |
| §9 Lệnh kiểm | ❌ ARM64 không chạy được (CHẶN-B-1); dư bộ tệp kết quả (CS-1) |
| §10 Ràng buộc kỹ thuật | ❌ `pytest -m "not slow"` **không** chạy được khi thiếu `onnx` (CHẶN-B-1); còn lại đạt: type hints, docstring tiếng Việt Google, `pathlib`, không thêm dependency vào `requirements.txt` |

---

## 9. Lỗi phải sửa

### 🔴 CHẶN-B-1 — `import onnx` ở đầu tệp test làm **chết cả bộ test trên container ARM64**

**Vị trí**: `tests/test_export_detector.py:14`

```python
import numpy as np
import onnx          # ← dòng 14
import onnxruntime   # ← dòng 15
```

**Vì sao**: `deploy/Dockerfile.arm64` chỉ cài `requirements.txt` (onnxruntime, opencv, numpy,
pyyaml, flask, telegram) cộng `pytest|black|ruff` lọc từ `requirements-dev.txt`. **`onnx`
không có trong tệp nào** — đúng như §10 đặc tả đã ghi (`onnx` cố ý không nằm trong
`requirements.txt` vì Pi 5 không cần). Vì `import onnx` nằm ở **mức module**, pytest hỏng
ngay ở khâu **collection**, trước cả khi `-m "not slow"` kịp lọc:

```
ERROR collecting tests/test_export_detector.py
tests\test_export_detector.py:14: in <module>
    import onnx
E   ModuleNotFoundError: No module named 'onnx'
!!! Interrupted: 1 error during collection !!!    EXIT: 2
```

Hậu quả cụ thể, theo thứ tự nghiêm trọng:
1. **Cả 44 ca chết**, kể cả 38 ca `not slow` vốn không hề cần `onnx`.
2. Lỗi collection làm **`pytest tests/` toàn repo dừng ở exit 2** → bộ 199 test đang xanh trên
   ARM64 chuyển sang đỏ. Cổng B của Phase 2 ("code chạy được trên Docker ARM64 trước") không
   qua được.
3. Đánh dấu `@pytest.mark.slow` **mất tác dụng** với mục đích chính của nó: §8.2 đặc tả yêu
   cầu "bảo đảm `pytest -m "not slow"` vẫn chạy được toàn bộ phần còn lại".
4. Docstring `tests/test_export_detector.py:5–6` đang khẳng định điều **ngược với thực tế**:
   *"`pytest -m "not slow"` chạy được toàn bộ phần còn lại … không cần các thư viện đó (chỉ
   cần cho phần import ở mức hàm)"* — một tuyên bố sai trong sản phẩm bàn giao.

> Đã mô phỏng đúng tập gói của container bằng cách chặn `onnx`/`ultralytics`/`torch` qua
> `sys.meta_path` (Docker daemon trên máy này không khởi động được). Cùng phép mô phỏng đó
> xác nhận `scripts/export_detector.py` **import sạch** khi thiếu ba thư viện — phần mã sản
> phẩm đã làm đúng, chỉ tệp test làm sai.

**Sửa**: chuyển hai import xuống **trong thân** hai ca `@pytest.mark.slow` duy nhất cần chúng
(dòng 16 và 17), đúng khuôn mẫu mà chính `scripts/export_detector.py:175` đang dùng:

```python
@pytest.mark.slow
def test_dong16_export_that_tao_tep_onnx_doc_duoc(tmp_path):
    import onnx  # chỉ ca slow mới cần; container ARM64 không cài onnx

    weights = _sao_chep_weights_tam(tmp_path)
    ...


@pytest.mark.slow
def test_dong17_export_dau_vao_dung_hinh_dang(tmp_path):
    import onnxruntime

    ...
```

Sau khi sửa, chạy lại đúng lệnh mô phỏng để tự xác nhận: bộ `not slow` phải cho
**38 passed, 6 deselected** khi không có `onnx`.

---

### 🟡 CẦN SỬA-1 — Dư một bộ tệp kết quả trùng nội dung (vi phạm §9)

**Vị trí**: `results/export_detector_20260818_0943.json` và
`results/export_detector_20260818_0943.meta.json`

```
$ diff results/export_detector_20260818_0942.json results/export_detector_20260818_0943.json
(không khác một byte)

$ diff results/…_0942.meta.json results/…_0943.meta.json
39c39
<   "thoi_diem": "2026-08-18T09:42:17.857716+07:00"
>   "thoi_diem": "2026-08-18T09:43:25.247344+07:00"
```

**Vì sao**: `.gitignore` chỉ chặn ảnh/video trong `results/`, nên **cả bốn tệp sẽ vào git**.
Khi Chương 4 trích nguồn theo R6, có hai tệp cùng nội dung mà khác tên thì không xác định
được đâu là tệp chuẩn để dẫn; lần đo sau sẽ phải đoán. Đặc tả §9 đã ghi rõ: *"giữ lại một bộ
và xoá phần dư — mỗi lần chạy có ý nghĩa mới một tệp, không phải mỗi lần bấm chạy."*

**Sửa**: xoá hai tệp `…_0943.json` và `…_0943.meta.json`, giữ bộ `…_0942`. (Việc hai lần chạy
cho kết quả trùng **từng chữ số** là dấu hiệu tốt — chứng tỏ quy trình tái lập được — nhưng
chỉ nên lưu một bộ.)

---

### 🟡 CẦN SỬA-2 — `n_anh: 100` ở mức cao nhất của tệp kết quả là số **đếm trùng**

**Vị trí**: `scripts/export_detector.py:620` và `:645`

```python
n_anh_tong = sum(kq["n_anh"] for kq in ket_qua_theo_kich_thuoc.values())
...
"n_anh": n_anh_tong,
```

**Vì sao**: chỉ có **50 ảnh** được dùng, mỗi ảnh chạy ở hai độ phân giải. Khoá `n_anh` ở đầu
`results/export_detector_20260818_0942.json` ghi `100`, và `n_khop_so_mat` ghi `100`. Người
viết Chương 4 mở tệp này ra sẽ đọc thấy "kiểm chứng trên 100 ảnh" và viết đúng như vậy vào
báo cáo — trong khi số ảnh thật là 50. Đây chính là đường dẫn để một con số **chưa từng được
đo** lọt vào báo cáo (R5/R6). Hai khoá `iou_trung_binh` và `sai_so_diem_moc_trung_binh` ở
mức này cũng là **trung bình của trung bình**, không phải trung bình trên mẫu.

Đặc tả §7 chỉ đòi ngưỡng "áp cho **từng độ phân giải**" và §11.4 chỉ đòi báo cáo số đo cho
320 và 640 — phần tổng gộp là do người cài đặt tự thêm.

**Sửa**: đổi tên khoá cho đúng nghĩa và tách bạch số ảnh với số phép so sánh, ví dụ:

```python
"n_anh": danh_sach_anh_len,              # 50 — số ảnh phân biệt
"n_phep_so_sanh": n_anh_tong,            # 100 — 50 ảnh x 2 độ phân giải
"n_khop_so_mat": n_khop_tong,
```

Hoặc gọn hơn: bỏ hẳn khối tổng gộp ở mức cao nhất, chỉ giữ `theo_kich_thuoc` + `dat`, vì
`theo_kich_thuoc` đã là số đo đúng nghĩa. Nếu bỏ thì nhớ chỉnh
`_KHOA_BAT_BUOC_KET_QUA` (`:44–53`) và các ca dòng 28/31/33/34 cho khớp.

---

### 🟡 CẦN SỬA-3 — `so_sanh_mot_anh` **broadcast im lặng** khi số điểm mốc hai bên khác nhau

**Vị trí**: `scripts/export_detector.py:254–257` và `:297`

```python
if diem_pt.ndim != 3 or diem_pt.shape[-1] != 2:      # :254 — không kiểm chiều giữa
    raise ValueError(...)
...
khoang_cach = np.linalg.norm(diem_pt - diem_onnx, axis=-1)   # :297
```

**Vì sao**: hàm kiểm `ndim == 3` và chiều cuối `== 2`, nhưng **không kiểm chiều giữa bằng 5**
như docstring §5 đã hứa (`hình dạng (N, 5, 2)`). Khi một bên có 1 điểm mốc, NumPy
**broadcast** thay vì báo lỗi — hàm trả về kết quả bình thường:

```
so_sanh_mot_anh(k1, diem(1,5,2), k1, diem(1,1,2), 0.9, 5.0)
→ {'khop_so_mat': True, 'iou_min': 1.0, 'sai_so_diem_moc_max': 141.42, 'dat': False}
   (KHÔNG ném ValueError)
```

Đây đúng loại lỗi mà cả mã việc này sinh ra để ngăn: §1 đặc tả nêu *"mất nhánh xử lý điểm mốc
đều cho ra một tệp `.onnx` chạy được nhưng kết quả lệch"*. `P2-02` sẽ tự giải mã tensor bằng
`onnxruntime` thuần — nếu bản giải mã đó trả về sai số điểm mốc, phép so sánh này sẽ đưa ra
một con số **trông có nghĩa** thay vì báo lỗi hình dạng. Đặc tả §5 đã cam kết
`Raises: ValueError: mảng sai hình dạng`; mảng `(N, 1, 2)` là sai hình dạng mà không ném.

**Sửa**: siết ràng buộc ở `:254–257` — kiểm đủ ba chiều, và thêm một kiểm hai bên cùng số
điểm mốc:

```python
if diem_pt.ndim != 3 or diem_pt.shape[1:] != (5, 2):
    raise ValueError(f"diem_pt phải có hình dạng (N, 5, 2), nhận được {diem_pt.shape}")
if diem_onnx.ndim != 3 or diem_onnx.shape[1:] != (5, 2):
    raise ValueError(f"diem_onnx phải có hình dạng (M, 5, 2), nhận được {diem_onnx.shape}")
```

Bổ sung một ca test cạnh dòng 25b: `diem_onnx` hình dạng `(1, 1, 2)` → `pytest.raises(ValueError)`.

---

## 10. 🔵 Góp ý (không chặn — người dùng quyết định)

- **GY-1 — Lỗi `onnxruntime` lọt ra ngoài `main()`.** `main` chỉ bắt `LoiMoHinh` ở
  `scripts/export_detector.py:616`, còn `kiem_chung_tuong_duong` để nguyên ngoại lệ của
  `onnxruntime`. Tái hiện: chạy `.onnx` 640 với `imgsz=320` → `InvalidArgument` dội ra thành
  traceback thô thay vì `return 1`. Đặc tả không có tiêu chí nào cho ca này nên **không tính
  là lỗi**; nếu muốn chặt hơn thì bọc vòng lặp `:378–398` và đổi thành `LoiMoHinh`.
  Chi phí ~4 dòng, lợi ích: CLI luôn giữ giao ước "0 hoặc 1".
- **GY-2 — Mark `slow` chưa đăng ký** → 6 cảnh báo `PytestUnknownMarkWarning`. Đăng ký cần
  sửa `pyproject.toml`, **nằm ngoài danh sách trắng §2** nên người cài đặt đã đúng khi không
  đụng vào. Đề xuất `spec-writer` thêm `markers = ["slow: ..."]` vào `[tool.pytest.ini_options]`
  trong một mã việc `chore` riêng.
- **GY-3 — Đặc tả tự mâu thuẫn**: §9 đòi `grep -nE "raise (ValueError|TypeError)"` cho kết quả
  rỗng, trong khi §5 và dòng 25b **bắt buộc** `so_sanh_mot_anh` ném `ValueError`. Lệnh grep đó
  nên giới hạn phạm vi vào `doc_cau_hinh` (ý đồ thật của nó là bắt lỗi cấu hình ném sai loại).
  Việc của `spec-writer`, không phải của người cài đặt.
- **GY-4 — Dòng 13 §8 viết `pytest.raises(LoiMoHinh, match="")`** khiến pytest cảnh báo
  *"matching against an empty string will always pass"*. Người cài đặt chép đúng đặc tả
  (`tests/test_export_detector.py:208`). Nên sửa đặc tả thành
  `match="Không tìm thấy trọng số nguồn"` để ca test thật sự kiểm được thông báo.

---

## 11. Việc tiếp theo

🔴 **TRẢ LẠI cho người cài đặt** — bốn mục: CHẶN-B-1, CS-1, CS-2, CS-3.
Bốn mục đều gọn, ước tính dưới 30 dòng thay đổi, chỉ động vào hai tệp đã có trong danh sách
trắng cộng việc xoá hai tệp `results/` dư.

Sau khi sửa, người cài đặt phải tự chạy lại và dán nguyên văn:
1. `pytest tests/test_export_detector.py -v` (kỳ vọng 44 passed);
2. bộ `not slow` **trong môi trường không có `onnx`** (kỳ vọng 38 passed, 6 deselected) —
   bằng container ARM64 hoặc phép chặn `sys.meta_path`;
3. `git status --short --untracked-files=all` (kỳ vọng đúng 2 tệp mã nguồn + **2** tệp `results/`).

Không cần chạy lại `scripts/export_detector.py` để sinh số đo mới: số trong
`results/export_detector_20260818_0942.json` đã được người review **tái lập độc lập, khớp
từng chữ số**, và không có sửa đổi nào ở trên chạm vào đường tính số đo — trừ CS-2, vốn chỉ
đổi tên/cấu trúc khoá tổng gộp. Nếu chọn phương án đổi khoá cho CS-2 thì **phải** chạy lại một
lần để tệp kết quả khớp mã, và khi đó nhớ xoá bộ cũ.

**Chưa được commit** (R40). Sau khi vòng 2 cho phán quyết ✅ ĐẠT, commit message đề xuất:

```
feat(detector): P2-01 export YOLOv8n-face sang ONNX 320/640 + kiem chung tuong duong
```

---
---

# Review P2-01-export-detector — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-01-export-detector.md` (đã cập nhật §10 sau vòng 1) |
| **Nhánh** | `feat/p2-01-export-detector` |
| **HEAD khi review** | `dcfc8bd` |
| **Ngày** | 2026-08-18 |
| **Phán quyết** | ✅ **ĐẠT** — hết 🔴 và 🟡; còn 4 mục 🔵 không chặn (3/4 thuộc `spec-writer`) |

Đã đọc lại §9 và §10 bản cập nhật. §10 nay có ràng buộc mới: *"`ultralytics`, `onnx`, `torch`
chỉ được import BÊN TRONG thân hàm test cần chúng, không bao giờ ở mức module"*, kèm lệnh kiểm
`pytest … -m "not slow" --collect-only`. Vòng này review theo bản đó.

---

## 1. CHẶN-B-1 (vòng 1) — ĐÃ SỬA, xác nhận bằng môi trường thiếu gói

Dựng lại đúng tập gói của `deploy/Dockerfile.arm64` bằng cách chặn import qua `sys.meta_path`
(Docker daemon trên máy này vẫn không khởi động được). Vòng này chặn **bốn** gói — thêm cả
`onnxruntime` — để siết chặt hơn vòng 1:

| Phép kiểm (thiếu `onnx`, `ultralytics`, `torch`, `onnxruntime`) | Kết quả | Exit |
|---|---|---|
| `pytest tests/test_export_detector.py -m "not slow" --collect-only` — **lệnh §10 yêu cầu** | `39/45 tests collected (6 deselected)` | **0** ✅ |
| `pytest tests/test_export_detector.py -m "not slow"` (chạy thật) | `39 passed, 6 deselected` | **0** ✅ |
| `pytest tests --collect-only` (**toàn repo**) | `200 tests collected` | **0** ✅ |
| `import scripts.export_detector` | `IMPORT OK, NGUONG_IOU_TOI_THIEU = 0.9` | **0** ✅ |

Vòng 1 lệnh đầu cho `ERROR collecting … ModuleNotFoundError: No module named 'onnx'`, exit 2,
kéo đổ cả bộ test của repo. Nay **trót lọt cả bốn**.

Rà nguồn gốc chứ không chỉ tin kết quả — quét toàn bộ import mức module của **cả hai** tệp:

```
tests/test_export_detector.py : re, shutil, pathlib, numpy, pytest,
                                scripts.export_detector, src.common.exceptions
scripts/export_detector.py    : sys, pathlib, argparse, datetime, json, platform,
                                random, subprocess, numpy, src.common.*
```

Không tệp nào còn gói nặng ở mức module. `onnx` và `onnxruntime` nay nằm trong thân hai ca
`@pytest.mark.slow` duy nhất cần chúng (`tests/test_export_detector.py:235` và `:245`), kèm chú
thích dẫn §10. Docstring đầu tệp đã sửa cho khớp thực tế.

---

## 2. Ba mục 🟡 vòng 1

### CS-1 — Bộ kết quả dư: ĐÃ XOÁ ✅

`git status --short --untracked-files=all` chỉ còn **một** bộ:
`results/export_detector_20260818_1140.json` + `.meta.json`. Hai bộ `…_0942.*` và `…_0943.*`
đã biến mất.

### CS-2 — `n_anh` đếm trùng: ĐÃ SỬA ✅

`scripts/export_detector.py:623–624, 649–650`:

```python
so_anh_rieng_biet = len(danh_sach_anh)
n_phep_so_sanh = sum(kq["n_anh"] for kq in ket_qua_theo_kich_thuoc.values())
...
"n_anh": so_anh_rieng_biet,        # 50
"n_phep_so_sanh": n_phep_so_sanh,  # 100
```

Tệp kết quả nay ghi `"n_anh": 50`, `"n_phep_so_sanh": 100`, `"n_khop_so_mat": 100`. Hai khái
niệm tách bạch, tên khoá nói đúng nội dung: 50 ảnh phân biệt, 100 phép so sánh (50 × 2 độ phân
giải), khớp số mặt 100/100 phép. Người viết Chương 4 không còn đường đọc nhầm thành "100 ảnh".
Có chú thích giải thích ngay tại `:620–622`.

### CS-3 — Broadcast im lặng khi lệch số điểm mốc: ĐÃ SỬA ✅

`scripts/export_detector.py:254–257` đổi từ `diem_pt.shape[-1] != 2` sang
`diem_pt.shape[1:] != (5, 2)`.

**Không tin một ca test** — tự dựng 22 trường hợp lệch (0, 1, 2, 3, 4, 6, 10 điểm mốc; lệch một
bên, lệch cả hai bên; chiều cuối = 3; `ndim` = 2 và 4):

| Nhóm ca | Số ca | Kết quả |
|---|---|---|
| `pt`=5 mốc vs `onnx`∈{0,1,2,3,4,6,10} mốc | 7 | **7/7 ném `ValueError`**, thông báo nêu đúng hình dạng nhận được |
| `pt`∈{0,1,2,3,4,6,10} mốc vs `onnx`=5 mốc | 7 | **7/7 ném `ValueError`** |
| Cả hai bên cùng sai (1, 3, 4, 6, 10 mốc) | 5 | **5/5 ném `ValueError`** |
| Chiều cuối = 3, `ndim` = 2, `ndim` = 4 | 3 | **3/3 ném `ValueError`** |
| **Đường broadcast im lặng còn lại** | | **0** ✅ |

Ví dụ thông báo: `diem_onnx phải có hình dạng (M, 5, 2), nhận được (1, 3, 2)` — nêu rõ hình dạng
nhận được, đúng yêu cầu.

Hai ca **không ném** đã kiểm là **đúng ý đồ**, không phải lỗ hổng: `(2,5,2)` vs `(1,5,2)` là ca
lệch **số mặt** → trả `khop_so_mat: False, dat: False` theo dòng 21; hai mảng rỗng `(0,5,2)` →
`dat: True` theo dòng 25.

Người cài đặt còn bổ sung ca `test_diem_moc_khong_du_nam_diem_nem_loi`
(`tests/test_export_detector.py:352`) đúng như CS-3 yêu cầu, có docstring ghi lại nguyên nhân.

---

## 3. Hồi quy số đo — KHÔNG XÊ DỊCH ✅

Đây là mục quan trọng nhất của vòng này: các sửa đổi **không được** chạm vào đường tính toán.

Chạy lại độc lập `kiem_chung_tuong_duong` cho **cả hai** độ phân giải, cùng seed 42, cùng 50 ảnh,
rồi đối chiếu với tệp kết quả vòng 2 **và** số vòng 1:

| Đại lượng | Vòng 1 (`…_0942`) | Vòng 2 (`…_1140`) | Tôi đo lại | Khớp |
|---|---|---|---|---|
| **320** khớp số mặt | 50/50 | 50/50 | 50/50 | ✅ |
| **320** IoU trung bình | 0.9999995612093268 | 0.9999995612093268 | 0.9999995612093268 | ✅ |
| **320** IoU nhỏ nhất | 0.9999962742557785 | 0.9999962742557785 | 0.9999962742557785 | ✅ |
| **320** sai số mốc TB | 1.9229614461161672e-05 | 1.9229614461161672e-05 | 1.9229614461161672e-05 | ✅ |
| **320** sai số mốc max | 3.411968959808029e-05 | 3.411968959808029e-05 | 3.411968959808029e-05 | ✅ |
| **640** khớp số mặt | 50/50 | 50/50 | 50/50 | ✅ |
| **640** IoU trung bình | 0.9999995409057081 | 0.9999995409057081 | 0.9999995409057081 | ✅ |
| **640** IoU nhỏ nhất | 0.9999959766387992 | 0.9999959766387992 | 0.9999959766387992 | ✅ |
| **640** sai số mốc TB | 1.7664862217886365e-05 | 1.7664862217886365e-05 | 1.7664862217886365e-05 | ✅ |
| **640** sai số mốc max | 6.103701886672839e-05 | 6.103701886672839e-05 | 6.103701886672839e-05 | ✅ |
| Tổng: IoU TB | 0.9999995510575175 | 0.9999995510575175 | — | ✅ |
| Tổng: sai số mốc TB | 1.8447238339524018e-05 | 1.8447238339524018e-05 | — | ✅ |

**Khớp từng chữ số ở cả ba cột.** Không xê dịch. `dat: true` cho cả hai độ phân giải.

> Ghi chú: `sha256` của `models/yolov8n-face-320.onnx` có đổi (`437e2092…` → `3f7155e3…`) vì lần
> chạy 11:40 export lại tệp. Đây **không** phải vấn đề: tệp nằm trong `models/` đã gitignore, và
> số đo tái lập **y hệt** trên tệp mới — tôi đo lại trực tiếp trên chính tệp đó.

**ONNX vẫn thực sự được chạy** sau khi sửa (kiểm lại vì mã có thay đổi):

| Phép | Kết quả |
|---|---|
| `.onnx` là tệp rác | `InvalidProtobuf` — hỏng to tiếng, không fallback ✅ |
| `.onnx` bị nhân 0,5 vào 3 initializer conv | `n_khop 1/3`, IoU 0.9279, `dat: False` — sụp đổ ✅ |
| `.onnx` thật, cùng 3 ảnh | `n_khop 3/3`, IoU 0.9999998, `dat: True` ✅ |

---

## 4. Bốn phép đột biến — chạy lại trên mã vòng 2

`sha256` gốc: `de98dde8ba8c8cdb5201871e98fc4f9a31d2b6bad386166eff852d941cb690f6`

| # | Phép đột biến | Đặc tả đòi đỏ | **Thực đo** | sha256 khôi phục |
|---|---|---|---|---|
| **ĐB1** | Xoá khối kiểm `conf_threshold` | 10, 12 | **10, 12** (2 failed / 37 passed) ✅ | khớp ✅ |
| **ĐB2a** | Chỉ dòng `dat = …` → `True` | 21, 23, 23b, 24 | 23, 23b, 24 (nhánh lệch số mặt trả `dat` ở `return` sớm) | khớp ✅ |
| **ĐB2b** | **"luôn `dat = True`"** đúng nghĩa (mọi nhánh) | 21, 23, 23b, 24 | **21, 23, 23b, 24** (4 failed) ✅ | khớp ✅ |
| **ĐB3** | Bỏ nhánh chặn danh sách ảnh rỗng | 29 | **29** (1 failed) ✅ | khớp ✅ |
| **ĐB4** | Bỏ dùng `iou_toi_thieu` | 23, 23b | **23, 23b** (2 failed) ✅ | khớp ✅ |

`sha256` cuối cùng khớp gốc. Kết quả **giống hệt vòng 1** — việc sửa ba mục 🟡 không làm mất
hiệu lực của bộ kiểm thử.

---

## 5. Ba lệnh máy · bốn `grep` · AST · phạm vi file

| Lệnh | Kết quả |
|---|---|
| `black --check --line-length 100` (2 tệp) | `2 files would be left unchanged` ✅ |
| `black --check --line-length 100 src tests scripts` | `24 files would be left unchanged` ✅ |
| `ruff check` (2 tệp / toàn repo) | `All checks passed!` ✅ |
| `pytest tests/test_export_detector.py -v` | **45 passed** ✅ |
| `pytest -q` (toàn repo) | **200 passed** ✅ (vòng 1: 199 — thêm ca CS-3) |
| `pytest -m "not slow"` | **39 passed, 6 deselected** ✅ |

| `grep` §9 | Kết quả | Giải trình |
|---|---|---|
| `print(` | 12 dòng | Quét bằng **AST**: cả 12 lời gọi đều nằm **trong `main()`** — bảng dry-run `:568–582`, thông báo lỗi `:588`/`:597` (dòng 37/38 assert qua `capsys`), bảng kết quả `:673–686`. Ngoài `main()` không có `print()` nào. Hợp lệ theo ghi chú §9 |
| `0\.5\|0\.45\|320\|640\|\b12\b` | **rỗng** ✅ | |
| `except Exception` | **rỗng** ✅ | |
| `raise (ValueError\|TypeError)` | 6 dòng | Toàn bộ trong `so_sanh_mot_anh`, **do §5 và dòng 25b bắt buộc**. Mâu thuẫn nội bộ đặc tả, không phải lỗi người cài đặt — GÓP Ý-3 vẫn để ngỏ cho `spec-writer` |

**Quét AST**: 45 hàm test. Đối chiếu 44 dòng §8 (01–42 + 23b + 25b): **THIẾU = [] · 44/44 ✅**.
Một hàm ngoài bảng là `test_diem_moc_khong_du_nam_diem_nem_loi` — chính là ca mà **biên bản vòng
1 (CS-3) yêu cầu bổ sung**, không phải người cài đặt tự mở rộng phạm vi.

**Phạm vi file** theo §9 cập nhật — đúng, không thừa không thiếu:

```
?? scripts/export_detector.py                        ← mã nguồn (1/2)
?? tests/test_export_detector.py                     ← mã nguồn (2/2)
?? results/export_detector_20260818_1140.json        ← đúng MỘT bộ kết quả
?? results/export_detector_20260818_1140.meta.json
?? docs/review/P2-01-export-detector.review.md       ← biên bản của người review
```

Không tệp nào thuộc `configs/`, `src/`, `docs/` (ngoài `docs/review/`), `.claude/`,
`requirements*.txt`, `CLAUDE.md`. Lọc `\.(jpg|png|npy|npz|onnx|pt|pth|env|db|sqlite3?)$`:
**rỗng** ✅ — không có dữ liệu cấm lọt git (R25).

**`.meta.json`** (`…_1140.meta.json`): đủ 5 trường bắt buộc.
`commit = dcfc8bd19564aee8f260e3e67004a167a9289789` — `git cat-file -t` xác nhận là commit thật,
**chính là HEAD hiện tại**. `phien_ban` khớp thư viện đang cài (`ultralytics 8.4.39 ·
onnx 1.19.1 · onnxruntime 1.20.1 · torch 2.5.1+cpu`). `cau_hinh` khớp `configs/detect.yaml`.
`thiet_bi`, `thoi_diem` (có offset múi giờ), `seed 42` đầy đủ. ✅

**Chống hồi quy `doc_cau_hinh`** (vòng 1 đã quét sạch 244 ca, vòng này không đụng hàm đó nên chỉ
chạy tập nhỏ): 27 ca — 19 giá trị hỏng phủ 5 khoá (gồm `nan`, `inf`, `bool`, chuỗi số), 5 ca
thiếu khoá, 3 ca cấu trúc hỏng. **0 ca lệch** (không ca nào ném `ValueError`/`TypeError` hay im
lặng bỏ qua). Cấu hình hợp lệ vẫn trả đủ 8 khoá. ✅

---

## 6. Đối chiếu đặc tả — chốt

| Mục | Vòng 1 | Vòng 2 |
|---|---|---|
| §2 Phạm vi file | ⚠️ dư bộ kết quả | ✅ đúng |
| §4 Tham số → config | ✅ | ✅ |
| §5 Giao diện hàm | ⚠️ ràng buộc hình dạng chưa đủ | ✅ khớp từng ký tự, ràng buộc đã siết |
| §6 CLI | ✅ | ✅ |
| §7 Thiết kế kiểm chứng | ✅ | ✅ số đo không xê dịch |
| §8 Bảng nghiệm thu | ✅ 44/44 | ✅ 44/44 (+1 ca do review yêu cầu) |
| §9 Lệnh kiểm + phạm vi | ❌ | ✅ |
| §10 Ràng buộc kỹ thuật | ❌ import mức module | ✅ import cục bộ, `--collect-only` trót lọt |

---

## 7. 🔵 Góp ý còn để ngỏ (không chặn commit)

Bốn mục dưới đây **không** yêu cầu người cài đặt làm gì thêm; ba trong bốn thuộc về `spec-writer`.

- **GY-1 → cho mã việc sau.** `onnxruntime.InvalidArgument` vẫn lọt ra ngoài `main()`
  (`scripts/export_detector.py:616` chỉ bắt `LoiMoHinh`). Tái hiện: chạy `.onnx` 640 ở
  `imgsz=320`. Đặc tả không có tiêu chí cho ca này. Chi phí sửa ~4 dòng.
- **GY-2 → `spec-writer`.** Mark `slow` chưa đăng ký, sinh 6 `PytestUnknownMarkWarning`. Đăng ký
  phải sửa `pyproject.toml` — **ngoài danh sách trắng §2**, nên người cài đặt đã đúng khi không
  đụng. Nên gom vào một mã việc `chore(quy-trinh)`.
- **GY-3 → `spec-writer`.** §9 đòi `grep "raise (ValueError|TypeError)"` rỗng, trong khi §5 và
  dòng 25b **bắt buộc** ném `ValueError`. Nên giới hạn lệnh grep đó vào `doc_cau_hinh`.
- **GY-4 → `spec-writer`.** Dòng 13 §8 viết `match=""`, khiến pytest cảnh báo *"matching against
  an empty string will always pass"*. Nên đổi thành `match="Không tìm thấy trọng số nguồn"`.

---

## 8. Tổng kết hai vòng

| | Vòng 1 | Vòng 2 |
|---|---|---|
| Phán quyết | 🔴 TRẢ LẠI | ✅ **ĐẠT** |
| 🔴 CHẶN | 1 (`import onnx` mức module giết bộ test ARM64) | 0 |
| 🟡 CẦN SỬA | 3 (bộ kết quả dư · `n_anh` đếm trùng · broadcast im lặng) | 0 |
| 🔵 GÓP Ý | 4 | 4 (giữ nguyên, không chặn) |
| Test | 44 passed / 199 toàn repo | 45 passed / 200 toàn repo |
| `-m "not slow"` khi thiếu gói | ❌ exit 2, collection error | ✅ exit 0, 39 passed |

Bốn mục vòng 1 **đều được sửa đúng chỗ, không sinh lỗi mới** — không rơi vào triệu chứng "sửa chỗ
này hỏng chỗ khác" của trần 2 vòng. Hai điểm sống còn đã soi riêng:

- **Trung thực số liệu**: số trong `results/` được người review **tái lập độc lập, khớp từng chữ
  số** ở cả hai vòng; `.meta.json` truy được về commit thật; khoá `n_anh` đã hết mập mờ. Bản ONNX
  được chứng minh **có chạy thật** bằng phép phá trọng số, không phải "so mô hình với chính nó".
- **An toàn phần cứng**: mã việc này chạy trên PC phát triển, không chạm GPIO/relay/camera —
  không có bề mặt rủi ro phần cứng.

## 9. Việc tiếp theo

✅ **ĐẠT — được commit.** Đề xuất commit message (R29):

```
feat(scripts): export YOLOv8n-face sang ONNX 320 và 640
```

Ghi trong thân commit (không nhồi vào tiêu đề): tệp số đo
`results/export_detector_20260818_1140.json`, mã việc `P2-01-export-detector`, biên bản
`docs/review/P2-01-export-detector.review.md`.

Sau khi gộp vào `dev`: bước **2.3** (`src/detector/yolo_face.py`, chạy `onnxruntime` thuần) và
**2.6** (ma trận benchmark ONNX/NCNN × 320/640 × luồng). Lưu ý cho `spec-writer` khi soạn
`P2-02`: ràng buộc `(N, 5, 2)` vừa siết ở `so_sanh_mot_anh` chính là hợp đồng mà bản giải mã
tensor thuần của `P2-02` phải tuân theo.
