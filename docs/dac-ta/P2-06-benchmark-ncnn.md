# P2-06-benchmark-ncnn — Đo được cả hai bộ suy luận trong một ma trận

> Mã việc: `P2-06-benchmark-ncnn` · Hoàn tất bước **2.6** về mặt công cụ
> Nhánh: `feat/p2-06-benchmark-ncnn` · Đặc tả viết ngày 01/09/2026
> Tiền đề: `P2-05` đã gộp vào `dev` (`121968a`) — `src/detector/factory.py` đã có

---

## 1. Mục tiêu

Cho `scripts/benchmark_detect.py` đo được **cả ONNX Runtime lẫn NCNN** trong cùng một lần chạy, và
ghi đúng backend nào sinh ra dòng số đo nào.

Vì sao cần: bước 2.6 quy định ma trận `{ONNX, NCNN} × {320, 640} × {1, 2, 4 luồng}` — 12 ô. Hiện
script chỉ đo được 6 ô. `scripts/benchmark_detect.py:477` gán cứng `r["backend"] = "onnx"`, và
`do_mot_cau_hinh` gọi thẳng `YoloFaceDetector` chứ không qua factory, nên đưa thư mục NCNN vào sẽ
hỏng ngay ở bước nạp mô hình.

`P2-05` đã làm NCNN **chạy được**; mã việc này làm nó **được đo**.

**Mã việc này không tự sinh số đo.** Lượt chạy ma trận là của người dùng (§10b), và số đó dùng cho
Chương 4 chứ không phải Chương 2 — xem §9.

---

## 2. Phạm vi file — danh sách trắng

| File | Trạng thái | Vai trò |
|---|---|---|
| `scripts/benchmark_detect.py` | **sửa có kiểm soát** | Dùng factory, ghi backend thật, nhận thư mục NCNN, thêm `moi_truong` vào meta |
| `tests/test_benchmark_detect.py` | sửa | Ca cho backend NCNN và trường meta mới |

**Tuyệt đối không sửa**: `src/**` (kể cả `factory.py` — nó đã đúng), `configs/**`, `models/**`,
`requirements*.txt`, `docs/**`, `.claude/**`.

Không thêm gói nào. `ncnn` đã có trong `requirements.txt` từ `P2-05`, image `faceid:arm64` đã dựng
lại — **không** `docker build` ở mã việc này.

---

## 3. Dữ kiện — đã kiểm, dùng luôn

| Dữ kiện | Giá trị |
|---|---|
| Factory | `src/detector/factory.py::tao_bo_phat_hien(duong_dan, cfg)` — trả `YoloFaceDetector` cho tệp `.onnx`, `NcnnFaceDetector` cho thư mục có `model.ncnn.param`, còn lại ném `LoiCauHinh` |
| Thuộc tính nhận dạng | Cả hai lớp có `.ten_backend` (`"onnx"` / `"ncnn"`) và `.kich_thuoc_vao` |
| Thư mục NCNN sẵn có | `models/yolov8n-face-{320,640}_ncnn_model/` |
| Cột CSV hiện có | `benchmark_detect.py:58-69` — 10 cột, đã có sẵn `backend` |
| Khoá meta hiện có | `benchmark_detect.py:71-90` — **chưa có `moi_truong`** |
| Hàm suy ra môi trường | `scripts/export_detector_ncnn.py::xac_dinh_moi_truong()` — trả `pc_x86` / `docker_arm64` / `pi5` |
| Cảnh báo QEMU | `benchmark_detect.py:443-450` đã có, giữ nguyên |

---

## 4. Tham số — `configs/detect.yaml` KHÔNG đổi

Cả hai backend đọc chung bốn khoá `inference.*` như `P2-05` §4 đã chốt. Điều kiện so sánh công bằng
ở bước 2.6 chính là điều này: **chỉ đổi một biến** (backend hoặc độ phân giải hoặc số luồng), mọi
thứ khác giữ nguyên.

---

## 5. Thay đổi giao diện

### 5.1. `do_mot_cau_hinh` — dùng factory, tự điền `backend` và `imgsz`

```python
def do_mot_cau_hinh(
    duong_dan_mo_hinh: Path,   # đổi tên từ `duong_dan_onnx`
    cfg: dict,
    so_luong: int,
    anh_da_nap: list[np.ndarray],
    so_lam_nong: int,
) -> list[dict]:
    """Đo một ô của ma trận benchmark (một mô hình tại một mức số luồng).

    Mỗi bản ghi trả về có thêm hai khoá so với trước: `backend` và `imgsz`, lấy từ chính
    đối tượng phát hiện — KHÔNG suy từ tên tệp, và không để hàm gọi gán sau.
    """
```

Bên trong: thay `YoloFaceDetector(duong_dan_onnx, cfg)` bằng `tao_bo_phat_hien(duong_dan_mo_hinh, cfg)`.

Hai khoá `backend` và `imgsz` điền **ngay trong hàm này**, lấy từ `detector.ten_backend` và
`detector.kich_thuoc_vao`. Nhờ vậy `main` bỏ được đoạn tạo detector tạm chỉ để đọc `kich_thuoc_vao`
(`benchmark_detect.py:464-467`) — bớt một lượt nạp mô hình mỗi ô, đáng kể với NCNN.

### 5.2. `main` — bỏ gán cứng

Xoá `r["backend"] = "onnx"` (`:477`) và `r["imgsz"] = imgsz` (`:478`); hai giá trị này nay đến từ
`do_mot_cau_hinh`. Giữ `r["threads"] = t` và `r["run_id"]`.

Khoá của `tom_tat` giữ nguyên dạng `f"{i:02d}_{m.stem}_t{t}"` — `Path("...._ncnn_model").stem` cho
`yolov8n-face-320_ncnn_model`, vẫn phân biệt được các ô.

### 5.3. `--models` — mặc định đủ bốn mô hình

```python
default=[
    "models/yolov8n-face-320.onnx",
    "models/yolov8n-face-640.onnx",
    "models/yolov8n-face-320_ncnn_model",
    "models/yolov8n-face-640_ncnn_model",
]
```

Bốn mô hình × ba mức luồng = **12 ô**, đúng ma trận bước 2.6. Trợ giúp của cờ đổi thành
`"Danh sách mô hình cần đo — tệp .onnx hoặc thư mục *_ncnn_model"`.

### 5.4. Meta — thêm `moi_truong`

Thêm `"moi_truong"` vào `_KHOA_META_BAT_BUOC`, giá trị lấy từ
`scripts.export_detector_ncnn.xac_dinh_moi_truong()`.

Import chéo giữa hai script là **có chủ đích**: ba mã môi trường phải có đúng một định nghĩa, hai
bản cài đặt sẽ trôi khỏi nhau và làm hỏng phép gộp của
`notebooks/04_so_sanh_moi_truong.ipynb`. Module đó không import gói nặng ở mức module nên an toàn
khi chạy trên Pi 5.

---

## 6. Thiết kế bắt buộc

### 6.1. Backend đến từ đối tượng, không từ tên tệp

`backend` phải đọc từ `detector.ten_backend`. **Cấm** suy từ đuôi hay tên đường dẫn trong
`benchmark_detect.py`.

Lý do: factory đã là nơi duy nhất quyết định backend nào cho đường dẫn nào (`P2-05` §5.3). Nếu
script đoán lại một lần nữa, hai chỗ có thể lệch nhau, và khi lệch thì **cột `backend` trong CSV nói
sai về chính dòng số đo bên cạnh nó**. Đó là loại sai không ai phát hiện được lúc đọc bảng kết quả,
và nó đi thẳng vào Chương 4.

### 6.2. Không nạp mô hình hai lần cho một ô

Sau khi sửa, mỗi ô ma trận nạp mô hình **đúng một lần**, trong `do_mot_cau_hinh`. Đoạn tạo
`detector_do_kich_thuoc` rồi `del` ở `main` phải biến mất.

Ngoài chi phí, còn một lý do đúng đắn: `NcnnFaceDetector` giữ tài nguyên gốc C++ và có `close()`
(`P2-05` §6.2). Tạo thêm một bản rồi phó mặc cho bộ thu gom rác là đúng đường mà biên bản `P2-05`
🔵-3 đã cảnh báo.

### 6.3. Cảnh báo QEMU giữ nguyên, và mạnh hơn

`benchmark_detect.py:443-450` in cảnh báo khi chạy trong container. Giữ nguyên, và **thêm** dòng
tương tự vào `notes` của meta khi `moi_truong != "pi5"`, nội dung nêu rõ: số đo chỉ dùng để kiểm
quy trình và so sánh tương đối, **không** dùng kết luận chỉ tiêu ≥ 10 FPS.

Vì sao cần cả hai chỗ: cảnh báo trên màn hình biến mất khi cửa sổ đóng lại; câu trong `.meta.json`
đi cùng số liệu suốt đời tệp đó, kể cả khi ai đó mở lại nó sau ba tuần.

---

## 7. Bảng tiêu chí nghiệm thu

Ca mới đặt tên `test_dong<nn>`, nối tiếp số hiện có trong `tests/test_benchmark_detect.py`.

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Đường dẫn `.onnx` → bản ghi có `backend == "onnx"` | giả lập detector bằng monkeypatch factory; assert khoá `backend` |
| 02 | Thư mục NCNN → bản ghi có `backend == "ncnn"` | như trên |
| 03 | `imgsz` trong bản ghi lấy từ `detector.kich_thuoc_vao`, **không** từ tên tệp | detector giả có `kich_thuoc_vao = 999` và tên tệp chứa `320`; assert `imgsz == 999` |
| 04 | Trộn cả hai loại trong một lần chạy → CSV có **hai giá trị** cột `backend` | `main` với hai mô hình giả; đọc CSV, assert `set(cot_backend) == {"onnx", "ncnn"}` |
| 05 | Đường dẫn không hợp lệ (đuôi lạ) → `main` trả `1`, không để ngoại lệ lọt ra | `main(["--models", "khong/ton/tai.txt", ...]) == 1` |
| 06 | Meta có khoá `moi_truong` | `set(meta) >= set(_KHOA_META_BAT_BUOC)` và `"moi_truong" in meta` |
| 07 | `moi_truong` nhận một trong ba mã hợp lệ | `meta["moi_truong"] in {"pc_x86","docker_arm64","pi5"}` |
| 08 | `moi_truong != "pi5"` → `notes` chứa câu cảnh báo không dùng kết luận chỉ tiêu | assert chuỗi con trong `meta["notes"]` |
| 09 | Mỗi ô nạp mô hình **đúng một lần** | đếm số lần factory được gọi qua monkeypatch; với 1 mô hình × 1 mức luồng, assert `== 1` |
| 10 | `--dry-run` in bảng kế hoạch có cột backend, **không ghi tệp nào** | chụp `rglob` thư mục kết quả trước/sau; assert bằng nhau và `"backend" in stdout` |
| 11 | Cột CSV vẫn đúng 10 khoá, đúng thứ tự `_COT_CSV` | đọc dòng tiêu đề CSV, assert bằng `_COT_CSV` |
| 12 | **Mọi ca cũ của `test_benchmark_detect.py` vẫn xanh** | không sửa ca cũ; chúng là lưới an toàn của phép đổi §5.1 |

⚠️ Không ca nào trong bảng này được nạp mô hình thật hay ghi vào `results/` — dùng `monkeypatch` cho
factory và `tmp_path` cho thư mục kết quả, theo đúng mẫu mà `test_benchmark_detect.py` đang dùng.

---

## 8. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

```bash
python -m black --check --line-length 100 scripts/benchmark_detect.py tests/test_benchmark_detect.py
```

```bash
python -m ruff check scripts/benchmark_detect.py tests/test_benchmark_detect.py
```

```bash
python -m pytest tests/test_benchmark_detect.py -v -m "not slow"
```

```bash
python -m pytest -q -m "not slow"
```

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

Image đã có sẵn từ `P2-05` — **không** `docker build`.

```bash
git status --short --untracked-files=all
```

Phải cho thấy đúng hai tệp của §2.

### Quét mẫu vi phạm — cả hai lệnh phải rỗng

```bash
grep -nE "\"onnx\"|'onnx'|\"ncnn\"|'ncnn'" scripts/benchmark_detect.py
```

Cấm mọi chuỗi tên backend viết cứng trong script (§6.1). Chuỗi trong `--models` mặc định là **đường
dẫn tệp**, không phải tên backend — nếu lệnh này bắt được dòng nào khác đường dẫn, phải giải trình.

```bash
grep -nE "\.stem|\.suffix|endswith|_ncnn_model" scripts/benchmark_detect.py
```

`.stem` được phép **đúng một chỗ**: khoá của `tom_tat` (§5.2). Mọi chỗ khác dùng để đoán backend là
vi phạm §6.1.

### Kiểm đột biến bắt buộc

Ba phép. Sao lưu ra `$env:TEMP` → sửa → `pytest` → khôi phục → đối chiếu `sha256`.
**Không** dùng `git checkout` (mã chưa commit), và **không** dùng `Set-Content -Encoding utf8` —
nó ghi BOM và làm ca `ast.parse` đỏ giả, đúng lỗi đã xảy ra ở lượt review `P2-05`. Dùng:

```powershell
[System.IO.File]::WriteAllText((Resolve-Path <tệp>), $noiDungMoi, (New-Object System.Text.UTF8Encoding($false)))
```

| # | Phép đột biến | Ca **phải** đỏ |
|---|---|---|
| ĐB1 | Gán cứng `backend = "onnx"` cho mọi bản ghi | dòng 02 và 04 |
| ĐB2 | Bỏ khoá `moi_truong` khỏi meta | dòng 06 |
| ĐB3 | Bỏ câu cảnh báo trong `notes` khi không phải `pi5` | dòng 08 |

---

## 9. Ranh giới quan trọng — số đo này dùng vào đâu

Lượt chạy ma trận trên máy phát triển (§10b) cho ra **12 ô số liệu thật**, nhưng chúng chỉ chứng
minh được ba điều: quy trình đo chạy đúng, hai backend cho cùng kết quả phát hiện, và ảnh hưởng của
độ phân giải cùng số luồng tới độ trễ **trên x86-64**.

Chúng **không** chứng minh được backend nào phù hợp Raspberry Pi 5. NCNN tối ưu quanh tập lệnh vectơ
NEON của ARM; trên x86-64 nó đi đường SSE/AVX ít được chăm sóc hơn, còn ONNX Runtime thì ngược lại.
Thứ tự nhanh chậm hoàn toàn có thể **đảo dấu** khi chuyển sang ARM.

Hệ quả cho báo cáo: số của mã việc này vào **Chương 4** dưới nhan đề "kết quả sơ bộ trên máy phát
triển", kèm câu cảnh báo trên. Kết luận chọn backend đặt ở Cổng C sau khi đo trên Pi 5 thật.
Chương 2 §2.6.3 chỉ mô tả **nguyên lý** hai bộ suy luận, không mang con số nào.

---

## 10. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Chạy ma trận và phân tích số liệu** — lượt của người dùng (§10b), rồi vai `training`.
- **Chốt backend chính thức** vào `configs/detect.yaml` — Cổng C, cần Pi 5.
- **Chuyển `xac_dinh_moi_truong` sang `src/common/`** — hiện hai nơi dùng nó, còn chấp nhận được;
  khi có nơi thứ ba thì tách thành mã việc riêng.
- **Đo nhiệt độ và giảm xung 10 phút** — bước 2.7, cần Pi 5.
- Ba mục 🔵-1, 🔵-2, 🔵-3 của biên bản `P2-05` — thuộc `P2-05b` nếu người dùng đồng ý.

---

## 11. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` dài dòng 100, `ruff` sạch. Type hints, docstring tiếng Việt kiểu Google.
- Thư viện: thư viện chuẩn, `numpy`, `cv2`, và `src/**`, `scripts/**` của dự án. Không thêm gói.
- `benchmark_detect.py` chạy trên **Pi 5 không màn hình** — không import gì chỉ có trên máy phát
  triển ở mức module.
- Giữ nguyên mọi hành vi hiện có mà đặc tả này không nhắc tới: cỡ mẫu tối thiểu 100 khung, warm-up,
  cách ghi CSV, cách tính tổng hợp.

---

## 12. Báo cáo khi xong

Theo mẫu §12 của [`docs/quy-tac-cai-dat.md`](../quy-tac-cai-dat.md):

1. Kết quả các lệnh §8, dán nguyên văn dòng tổng kết.
2. Kết quả hai lệnh `grep`, giải trình dòng nào không rỗng.
3. Bảng ba phép đột biến: ca dự đoán đỏ · ca thật sự đỏ · `sha256` khôi phục.
4. Số ca của `test_benchmark_detect.py` trước và sau, khẳng định không ca cũ nào bị sửa.
5. Vướng mắc.

**Không commit.**

## 10b. Lượt của người dùng — sau khi §8 xanh

```bash
python scripts/benchmark_detect.py --dry-run
```

Kết quả mong đợi: bảng kế hoạch **12 ô** (4 mô hình × 3 mức luồng), cột backend hiện `onnx` cho hai
dòng đầu và `ncnn` cho hai dòng sau. Không tệp nào được tạo.

```bash
python scripts/benchmark_detect.py --device-name "PC phát triển"
```

Kết quả mong đợi: `results/bench_detect_<YYYYMMDD_HHMM>.csv` với **1200 dòng** (12 ô × 100 khung) và
`.meta.json` có `moi_truong: pc_x86` cùng câu cảnh báo trong `notes`. Lượt này mất vài phút.

Đây là **bước 3** của trình tự đã thống nhất ngày 01/09/2026. Số liệu thu được đi vào Chương 4 với
đúng ranh giới nêu ở §9 — không dùng kết luận chỉ tiêu, không dùng chọn backend.
