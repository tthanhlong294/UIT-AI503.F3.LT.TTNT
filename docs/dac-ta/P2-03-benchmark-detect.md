# P2-03-benchmark-detect — Script đo hiệu năng khối phát hiện khuôn mặt

> Mã việc: `P2-03-benchmark-detect` · Bước **2.6** trong `CLAUDE.md` §5 Phase 2
> Nhánh: `feat/p2-03-benchmark-detect` · Đặc tả viết ngày 18/08/2026
> Phụ thuộc: `P2-02` đã gộp vào `dev` — cần `src/detector/yolo_face.py`

---

## 1. Mục tiêu

Viết `scripts/benchmark_detect.py` — chạy ma trận cấu hình, đo tốc độ khối phát hiện khuôn mặt,
ghi kết quả đúng chuẩn `results/` để đối chiếu với **chỉ tiêu chặn ≥ 10 FPS** của Cổng C.

Ma trận theo `CLAUDE.md` bước 2.6: **{độ phân giải} × {số luồng}**.
Phần NCNN của ma trận **chưa làm ở mã việc này** — xem §9.

**Script này là công cụ, không phải phép đo.** Con số chính thức chỉ có giá trị khi chạy trên
**Raspberry Pi 5 thật**. Viết trước để ngày có phần cứng là đo được ngay, không mất thêm thời
gian vào việc lập trình.

---

## 2. Phạm vi file — danh sách trắng

| File | Trạng thái | Vai trò |
|---|---|---|
| `scripts/benchmark_detect.py` | tạo mới | Script CLI |
| `tests/test_benchmark_detect.py` | tạo mới | Bộ kiểm thử |

**Không sửa**: `src/**`, `configs/**`, `requirements.txt`, `docs/**`, `.claude/**`.
Cần tham số mới trong `configs/detect.yaml` → **dừng và báo**, không tự thêm.

---

## 3. Dữ kiện đã kiểm chứng

Đo ngày 18/08/2026 trên **máy phát triển** (không phải Pi 5), 60 ảnh LFW, `num_threads=0`:

| Độ phân giải | Thời gian mỗi ảnh | Tốc độ | Tỉ lệ phát hiện |
|---|---|---|---|
| 320 | 39,4 ± 4,5 ms | ~25,4 FPS | 60/60 |
| 640 | 136,9 ± 15,6 ms | ~7,3 FPS | 60/60 |

Dùng làm mốc kiểm tính hợp lý: nếu script cho ra con số lệch hàng chục lần so với đây trên
cùng máy, tức là phép đo sai.

⚠️ Bản 640 đã dưới 10 FPS ngay trên máy để bàn. Đây là **cảnh báo sớm** rằng chỉ tiêu Cổng C
có thể không đạt ở 640 — nhưng **không được kết luận** cho tới khi đo trên Pi 5 thật (R5, R7).

---

## 4. Giao diện dòng lệnh

```
python scripts/benchmark_detect.py [--config CONFIG] [--models M [M ...]]
                                   [--threads T [T ...]] [--n-frames N]
                                   [--warmup W] [--anh-dir DIR] [--seed SEED]
                                   [--device-name TEN] [--ghi-chu GHI_CHU] [--dry-run]
```

| Cờ | Mặc định | Ý nghĩa |
|---|---|---|
| `--config` | `configs/detect.yaml` | Đường dẫn cấu hình |
| `--models` | `models/yolov8n-face-320.onnx models/yolov8n-face-640.onnx` | Danh sách tệp ONNX cần đo |
| `--threads` | `1 2 4` | Các mức số luồng cần quét |
| `--n-frames` | `100` | Số khung hình đo mỗi cấu hình, **tối thiểu 100** (R9) |
| `--warmup` | `10` | Số khung hình chạy làm nóng, **không** tính vào kết quả |
| `--anh-dir` | `data/impostor/lfw_original` | Nguồn ảnh |
| `--seed` | `42` | Seed chọn mẫu ảnh (R15) |
| `--device-name` | *(bắt buộc nhập)* | Tên thiết bị, ví dụ `"Raspberry Pi 5 8GB"` hoặc `"PC phát triển"` |
| `--ghi-chu` | rỗng | Ghi chú tự do, vào `notes` của meta |
| `--dry-run` | tắt | In kế hoạch, **không đo, không ghi tệp** |

`--device-name` **bắt buộc** vì R8 đòi mọi số đo phải kèm ngữ cảnh thiết bị. Thiếu cờ này →
`main` trả về `1` và in hướng dẫn.

---

## 5. Giao diện hàm

```python
def doc_nhiet_do_cpu() -> float | None:
    """Đọc nhiệt độ CPU, đơn vị độ C.

    Trả về None trên máy không có cảm biến (Windows, macOS) — KHÔNG ném ngoại lệ.
    Trên Linux/Raspberry Pi đọc từ /sys/class/thermal/thermal_zone0/temp (milli-độ C).
    """

def dang_trong_container() -> bool:
    """Nhận biết đang chạy trong container (kiểm tra /.dockerenv)."""

def chon_anh(thu_muc: Path, so_luong: int, seed: int) -> list[Path]:
    """Chọn ngẫu nhiên có tái lập một tập ảnh.

    Raises:
        LoiCauHinh: thư mục không tồn tại, rỗng, hoặc không đủ ảnh.
    """

def do_mot_cau_hinh(
    duong_dan_onnx: Path, cfg: dict, so_luong: int,
    anh_da_nap: list[np.ndarray], so_lam_nong: int,
) -> list[dict]:
    """Đo một ô của ma trận.

    Nhận ảnh ĐÃ NẠP SẴN vào bộ nhớ — thời gian đọc tệp KHÔNG được tính vào phép đo.

    Returns:
        Danh sách bản ghi, mỗi khung hình một bản ghi, gồm các khoá
        `sample_idx`, `latency_ms`, `fps_instant`, `n_faces`, `conf_top`, `cpu_temp_c`.

    Raises:
        LoiMoHinh: không nạp được mô hình.
    """

def tong_hop(ban_ghi: list[dict]) -> dict:
    """Tổng hợp một ô của ma trận.

    Returns:
        Từ điển gồm `n_frames`, `latency_tb`, `latency_do_lech`, `latency_p50`,
        `latency_p95`, `fps_tb`, `ti_le_phat_hien`, `dat_chi_tieu`.
        `dat_chi_tieu` là True khi `fps_tb >= 10.0`.

    Raises:
        LoiCauHinh: danh sách bản ghi rỗng.
    """

def ghi_ket_qua(thu_muc: Path, run_id: str, ban_ghi: list[dict], meta: dict) -> tuple[Path, Path]:
    """Ghi ĐÚNG HAI tệp: <run_id>.csv (dữ liệu thô) và <run_id>.meta.json (ngữ cảnh).

    Raises:
        LoiCauHinh: meta thiếu khoá bắt buộc.
    """

def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 thành công, 1 thất bại."""
```

Ngoại lệ: `LoiCauHinh` cho lỗi cấu hình/đầu vào, `LoiMoHinh` cho lỗi mô hình.

---

## 6. Định dạng kết quả — theo `experiment-protocol.instructions.md` §4

### Tệp 1 — `results/bench_detect_<YYYYMMDD_HHMM>.csv`

Mỗi dòng là **một lần đo đơn lẻ**, không phải giá trị đã tổng hợp:

```csv
run_id,backend,imgsz,threads,sample_idx,latency_ms,fps_instant,n_faces,conf_top,cpu_temp_c
```

- `backend` — `onnx` ở mã việc này; để sẵn cột cho NCNN sau.
- `imgsz` — đọc từ **đồ thị ONNX** qua `detector.kich_thuoc_vao`, không suy từ tên tệp.
- `conf_top` — độ tin cậy của khuôn mặt tin cậy nhất; rỗng nếu không phát hiện được.
- `cpu_temp_c` — rỗng khi máy không có cảm biến.

Lưu thô để tính lại được mọi chỉ số về sau mà không phải chạy lại.

### Tệp 2 — `results/bench_detect_<YYYYMMDD_HHMM>.meta.json`

Bắt buộc có các khoá: `run_id`, `timestamp`, `git_commit`, `git_dirty`, `script`, `command`,
`device`, `software`, `config_file`, `config_snapshot`, `dataset`, `seed`, `warmup_frames`,
`cpu_temp_start_c`, `cpu_temp_max_c`, `duration_s`, `notes`, `tom_tat`.

- `device` là từ điển gồm ít nhất `name` (từ `--device-name`), `os`, `machine`, `processor`.
- `software` ghi phiên bản `python`, `onnxruntime`, `opencv-python`, `numpy`.
- `tom_tat` chứa kết quả tổng hợp từng ô ma trận (đầu ra của `tong_hop`).
- `git_dirty: true` khi cây làm việc còn thay đổi chưa commit — **cảnh báo**, không chặn.

### ⚠️ Chốt chặn container — bắt buộc

Nếu `dang_trong_container()` trả `True`:

1. Thêm khoá `canh_bao_hieu_nang` vào meta với nội dung nêu rõ số đo **không dùng được** làm
   số hiệu năng.
2. In cảnh báo ra màn hình.
3. Vẫn chạy bình thường (hữu ích để kiểm tính đúng đắn).

Lý do: container ARM64 chạy qua QEMU nên thời gian **không quy đổi được**
(`experiment-protocol.instructions.md` §2). Không có chốt này thì một con số QEMU có thể lọt
vào báo cáo mà không ai nhận ra.

---

## 7. Bảng tiêu chí nghiệm thu

Mỗi dòng là một ca test tên `test_dong<nn>` trong `tests/test_benchmark_detect.py`.

### 7.1. Chọn ảnh và đọc môi trường

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Cùng seed chọn cùng tập ảnh | `chon_anh(d, 20, 42) == chon_anh(d, 20, 42)` |
| 02 | Khác seed chọn khác tập ảnh | `chon_anh(d, 20, 42) != chon_anh(d, 20, 7)` với thư mục ≥ 100 ảnh |
| 03 | Trả về đúng số lượng yêu cầu | `len(chon_anh(d, 20, 42)) == 20` |
| 04 | Thư mục không tồn tại → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 05 | Thư mục rỗng → `LoiCauHinh`, thông báo **khác** dòng 04 | Thông báo chứa `rỗng` hoặc `không có ảnh` |
| 06 | Không đủ ảnh → `LoiCauHinh` nêu rõ số có và số cần | Thư mục 5 ảnh, xin 100; thông báo chứa cả `5` lẫn `100` |
| 07 | `doc_nhiet_do_cpu` không ném lỗi khi thiếu cảm biến | Gọi trực tiếp; assert kết quả là `None` hoặc `float` |
| 08 | `doc_nhiet_do_cpu` đọc đúng khi có tệp cảm biến | Giả lập tệp chứa `52341` ⇒ `pytest.approx(52.341)` |
| 09 | `dang_trong_container` trả `True` khi có `/.dockerenv` | Giả lập bằng `monkeypatch`; assert `True` |
| 10 | `dang_trong_container` trả `False` khi không có | Giả lập ngược lại; assert `False` |

### 7.2. Đo và tổng hợp

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 11 | Số bản ghi bằng đúng `so_luong`, **không** tính khung làm nóng | `len(do_mot_cau_hinh(..., so_luong=12, so_lam_nong=5)) == 12` |
| 12 | Mỗi bản ghi có đủ **sáu** khoá | `set(r) >= {"sample_idx","latency_ms","fps_instant","n_faces","conf_top","cpu_temp_c"}` |
| 13 | `sample_idx` chạy từ 0 và liên tục | `[r["sample_idx"] for r in bg] == list(range(len(bg)))` |
| 14 | `fps_instant` khớp nghịch đảo `latency_ms` | `abs(r["fps_instant"] - 1000/r["latency_ms"]) < 1e-6` |
| 15 | `latency_ms` là số dương | `all(r["latency_ms"] > 0 for r in bg)` |
| 16 | Ảnh truyền vào đã nạp sẵn, **không đọc tệp trong vòng đo** | Quét `ast` thân `do_mot_cau_hinh`: không gọi `imread`, `open`, `Path.read_bytes` |
| 17 | `tong_hop` tính trung bình đúng | Bản ghi latency `[10, 20, 30]` ⇒ `latency_tb == pytest.approx(20.0)` |
| 18 | `tong_hop` tính độ lệch chuẩn đúng | Cùng dữ liệu ⇒ `latency_do_lech == pytest.approx(np.std([10,20,30]))` |
| 19 | `tong_hop` tính p50 và p95 đúng | 100 bản ghi latency `1..100` ⇒ `latency_p50` và `latency_p95` khớp `np.percentile` |
| 20 | `dat_chi_tieu` True khi `fps_tb >= 10` | Latency đều 50 ms ⇒ `fps_tb == 20.0` và `dat_chi_tieu is True` |
| 21 | `dat_chi_tieu` False khi `fps_tb < 10` | Latency đều 200 ms ⇒ `fps_tb == 5.0` và `dat_chi_tieu is False` |
| 22 | Biên đúng tại 10 FPS | Latency đều 100 ms ⇒ `fps_tb == 10.0` và `dat_chi_tieu is True` |
| 23 | `ti_le_phat_hien` tính đúng | 10 bản ghi, 7 bản có `n_faces >= 1` ⇒ `pytest.approx(0.7)` |
| 24 | Danh sách rỗng → `LoiCauHinh`, không chia cho 0 | `pytest.raises(LoiCauHinh)` |

### 7.3. Ghi kết quả

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 25 | Ghi **đúng hai** tệp `.csv` và `.meta.json` | Cả hai `.exists()` |
| 26 | Tên tệp đúng khuôn | `re.fullmatch(r"bench_detect_\d{8}_\d{4}\.csv", csv.name)` |
| 27 | CSV có **đúng mười** cột, đúng thứ tự §6 | So `next(csv.reader(...))` với danh sách cột nguyên văn |
| 28 | Số dòng CSV bằng số bản ghi (không kể tiêu đề) | `len(list(csv.DictReader(...))) == len(ban_ghi)` |
| 29 | `meta.json` đủ **mười tám** khoá bắt buộc §6 | `set(meta) >= {"run_id","timestamp","git_commit","git_dirty","script","command","device","software","config_file","config_snapshot","dataset","seed","warmup_frames","cpu_temp_start_c","cpu_temp_max_c","duration_s","notes","tom_tat"}` — liệt kê đích danh, không viết `{...}` |
| 29b | `device` có đủ **bốn** trường con | `set(meta["device"]) >= {"name","os","machine","processor"}` |
| 29c | `software` ghi đủ **bốn** phiên bản thư viện | `set(meta["software"]) >= {"python","onnxruntime","opencv-python","numpy"}` |
| 30 | `git_commit` khớp kho thật | `meta["git_commit"] == subprocess git rev-parse HEAD` |
| 31 | `meta` thiếu khoá → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` với `meta={}` |
| 32 | `meta` **đủ khoá** → ghi thành công | Cặp đối chứng của dòng 31 |
| 33 | `cpu_temp_c` rỗng trong CSV khi cảm biến trả `None` | Ô tương ứng là chuỗi rỗng, **không** phải `"None"` |

### 7.4. Chốt chặn container

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 34 | Trong container → meta có `canh_bao_hieu_nang` | Giả lập `dang_trong_container` trả `True`; assert khoá tồn tại và **không rỗng** |
| 35 | Trong container → in cảnh báo ra màn hình | `capsys`: đầu ra chứa `QEMU` hoặc `không dùng được` |
| 36 | **Ngoài** container → **không** có khoá đó | Cặp đối chứng của dòng 34; assert `"canh_bao_hieu_nang" not in meta` |

### 7.5. Luồng chính

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 37 | Thiếu `--device-name` → trả về `1` | `main([]) == 1`; đầu ra chứa `device-name` |
| 38 | `--dry-run` **không ghi tệp nào** vào `results/` | Chụp `rglob("*")` trước và sau; assert bằng nhau; `main([...]) == 0` |
| 39 | `--n-frames` nhỏ hơn 100 → trả về `1`, nhắc R9 | `main([..., "--n-frames", "50"]) == 1`; đầu ra chứa `100` |
| 40 | Ma trận đúng số ô | 2 mô hình × 3 mức luồng ⇒ `tom_tat` có 6 mục |
| 41 | Mô hình không tồn tại → trả về `1`, không để ngoại lệ lọt | `main([..., "--models", "khong/co.onnx"]) == 1` |
| 42 | Cấu hình hỏng → trả về `1` | `main(["--config", cfg_hong, ...]) == 1` |
| 43 | Bảng tổng kết in ra có cột Đạt/Không đạt | `capsys`: đầu ra chứa `10` và (`Đạt` hoặc `KHÔNG`) |

---

## 8. Lệnh kiểm bắt buộc

```bash
black --line-length 100 --check scripts/benchmark_detect.py tests/test_benchmark_detect.py
```

```bash
ruff check scripts/benchmark_detect.py tests/test_benchmark_detect.py
```

```bash
python -m pytest tests/test_benchmark_detect.py -v
```

```bash
git status --short --untracked-files=all
```

Lệnh cuối: **đúng hai** tệp mã nguồn mới, cộng tệp `results/bench_detect_*` nếu có chạy thật
(chúng **không** bị gitignore — `.gitignore` chỉ chặn ảnh/video trong `results/`).
Ba tệp `.docx` trong `docs/bao-cao-tuan/` là của sinh viên, bỏ qua.

### Quét mẫu vi phạm — cả bốn phải rỗng

```bash
grep -nE "\b(10|100|320|640)\b" scripts/benchmark_detect.py
```

```bash
grep -n "except Exception" scripts/benchmark_detect.py
```

```bash
grep -rn "ultralytics\|import torch" scripts/benchmark_detect.py
```

```bash
grep -nE "raise (ValueError|TypeError)" scripts/benchmark_detect.py
```

Lệnh đầu bắt số hardcode. Ngoại lệ hợp lệ: ngưỡng **10 FPS** là chỉ tiêu cam kết ở `CLAUDE.md` §1
và **100 frame** là quy định R9 — đặt thành hằng số có tên (`NGUONG_FPS_TOI_THIEU`,
`SO_FRAME_TOI_THIEU`) kèm chú thích dẫn nguồn, rồi giải trình. Giá trị mặc định của tham số CLI
không tính là hardcode.

### Kiểm đột biến bắt buộc

| # | Phép đột biến | Ca test **phải** đỏ |
|---|---|---|
| ĐB1 | Tính cả khung làm nóng vào kết quả | dòng 11 |
| ĐB2 | Đổi `>=` thành `>` ở `dat_chi_tieu` | dòng **22** (ca biên 10 FPS) |
| ĐB3 | Bỏ chốt chặn container | dòng 34, 35 |
| ĐB4 | Dùng `np.std` thay `np.mean` (hoặc ngược lại) trong `tong_hop` | dòng 17, 18 |
| ĐB5 | Đọc ảnh bằng `imread` **bên trong** vòng đo | dòng 16 |
| ĐB6 | Bỏ kiểm `--n-frames >= 100` | dòng 39 |

ĐB2 là phép quan trọng: ca biên đúng 10 FPS quyết định một cấu hình được xếp Đạt hay Không đạt,
và con số đó đi thẳng vào bảng đối chiếu chỉ tiêu ở Chương 4.

Mỗi phép: sửa → chạy → ghi ca đỏ → khôi phục → đối chiếu `sha256`. Dùng `newline=""`.

---

## 9. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Export và đo NCNN.** Cần cài `ncnn` + `pnnx`, và giá trị của NCNN chỉ đo được trên ARM thật.
  Để lại mã việc riêng khi đã có Pi 5. Cột `backend` trong CSV để sẵn chỗ.
- **Đo nhiệt độ và throttling trong 10 phút** (bước 2.7) — mã việc riêng, cần Pi 5.
- **Kết luận Đạt/Không đạt chính thức.** Script chỉ ghi số; kết luận thuộc Cổng C sau khi chạy
  trên Pi 5 thật.
- Đo khối nhận diện hay chống giả mạo — Phase 3 và 4.

---

## 10. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` 100, `ruff` sạch. Type hints, docstring tiếng Việt kiểu Google.
- Chỉ dùng thư viện chuẩn cộng `numpy`, `cv2`, `onnxruntime` và `src/**` của dự án.
  **Không** `ultralytics`, **không** `torch` — script này phải chạy được trên Pi 5.
- Dùng `logging` qua `src.common.logging.lay_logger`; `print()` chỉ cho bảng tổng kết CLI.
- Đọc cấu hình qua `src.common.config.nap_cau_hinh` / `lay_gia_tri`.
- Đo thời gian bằng `time.perf_counter()`, **không** dùng `time.time()`.
- Ca test **không được** đòi hỏi mô hình thật trừ khi đánh dấu `@pytest.mark.slow`; ca cần mô
  hình phải `pytest.skip` có thông báo nếu tệp `.onnx` chưa có.
- Chạy được trên Windows lẫn Linux: đường dẫn dùng `pathlib`, đọc nhiệt độ phải chịu được
  việc không có `/sys/class/thermal`.

---

## 11. Báo cáo khi xong

1. Kết quả bốn lệnh máy §8, trên host **và** container ARM64.
2. Kết quả bốn lệnh `grep`, giải trình từng dòng không rỗng.
3. Kết quả **sáu** phép đột biến, kèm `sha256` khôi phục.
4. **Một lần chạy thật trên máy phát triển** với `--device-name "PC phát triển"`:
   dán bảng tổng kết, và đối chiếu với mốc ở §3 (320 ≈ 39 ms, 640 ≈ 137 ms) xem có hợp lý không.
5. Xác nhận meta của lần chạy đó **không** có `canh_bao_hieu_nang` (vì chạy ngoài container),
   và có `git_dirty` phản ánh đúng trạng thái.
6. Vướng mắc.

**Không commit.** Để nguyên cây làm việc cho người review.
