# Review P2-03-benchmark-detect — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-03-benchmark-detect.md` |
| **Nhánh** | `feat/p2-03-benchmark-detect` (chưa commit, cây làm việc để nguyên) |
| **HEAD khi review** | `86df4fc` |
| **Ngày** | 2026-08-19 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — **1 × CHẶN-B**, **3 × CẦN SỬA**, 6 × GÓP Ý |

> Kết luận quan trọng nhất trước: **phép đo của script là SẠCH**. Không có chi phí nào lọt vào
> vòng đo. Khoảng cách 20 %/45 % so với mốc §3 đến **hoàn toàn** từ trạng thái nhiệt/turbo của
> máy khi chạy liên tục cả ma trận 93 giây — đã chứng minh bằng bốn phép chạy độc lập ở §1.
> Script **không** báo Pi 5 chậm hơn thực tế.
>
> Bốn lỗi phải sửa đều nằm ngoài đường đo: một ca test chết trên container ARM64, hai lỗ hổng
> cho phép tệp sai lọt vào `results/`, một ca test không cô lập thư mục kết quả.

---

## 1. Ưu tiên số một — vì sao số đo chậm hơn mốc §3

### 1.1. Kết luận

**Nguyên nhân 1 (chính đáng) — nhưng KHÔNG phải `num_threads`.**
Thủ phạm là **trạng thái nhiệt/turbo của máy phát triển**: đây là laptop Tiger Lake 4 lõi vật lý /
8 luồng logic; chạy sáu ô ma trận liên tục 93 giây làm cạn ngân sách turbo, mọi ô sau ô đầu chậm
đi 40–70 %. `num_threads` chỉ giải thích được phần nhỏ.

**Không tìm thấy bất kỳ chi phí nào trong vòng đo** — bốn giả thuyết trong yêu cầu review đều bị
bác bỏ bằng phép chạy, xem 1.2–1.5.

### 1.2. Phép quyết định — chạy CHÍNH script, một ô duy nhất, máy đã nghỉ

Nghỉ 90 s (rồi 120 s) cho máy nguội, chạy `scripts/benchmark_detect.py` **nguyên bản** với đúng
một ô ma trận, 100 khung, cùng 110 ảnh LFW seed 42 (chỉ đổi thư mục kết quả sang thư mục tạm để
không rác `results/`):

| Ô | Mốc §3 (18/08, `num_threads=0`) | Script chạy đơn ô, máy nghỉ | Kết luận |
|---|---|---|---|
| 320 / 4 luồng | 39,4 ms | **31,8 ms** (FPS 31,45 · p50 31,3 · p95 39,3) | script **nhanh hơn** mốc 19 % |
| 640 / 2 luồng | 136,9 ms | **132,3 ms** (FPS 7,56 · p50 126,4 · p95 171,0) | khớp mốc, lệch 3 % |

Chính script đó, chính những hàm đó, chính tập ảnh đó — khi máy nguội thì tái lập được mốc §3
đến 3 %. **Overhead trong vòng đo = 0.**

### 1.3. Tách bạch hai yếu tố — số luồng vs thứ tự chạy

Phép đo độc lập (vòng lặp tự viết, chỉ bọc `detector.detect`, 100 khung sau 10 khung làm nóng,
cùng 110 ảnh), một tiến trình chạy tuần tự từ máy nguội:

| imgsz | `num_threads=0` | `=4` | `=2` | `=1` |
|---|---|---|---|---|
| 320 | 34,6 ± 10,3 ms | 34,4 ± 6,2 | 35,9 ± 10,2 | 46,2 ± 11,6 |
| 640 | **135,0 ± 26,4** | 216,9 ± 78,7 | 195,0 ± 36,9 | 248,5 ± 36,6 |

Nhìn bảng này dễ tưởng `num_threads=0` nhanh gấp rưỡi `=4` ở 640. **Sai** — đó là hiệu ứng thứ tự.
Chạy **xen kẽ** `4 → 0` ba vòng liền (40 khung mỗi lần, máy đã nóng sẵn):

| Vòng | 640 `=4` | 640 `=0` |
|---|---|---|
| 0 | 227,4 ms | 201,2 ms |
| 1 | 231,3 ms | 217,4 ms |
| 2 | 213,7 ms | 209,0 ms |

Hai mức luồng **hội tụ về 200–230 ms**, và con số 135 ms không bao giờ quay lại. Tức là 135 ms ở
bảng trên là giá trị của **ô chạy đầu tiên trên máy nguội**, không phải công lao của `num_threads=0`.
Ở 320 thì `0` và `4` bằng nhau trong sai số (34,6 vs 34,4) — đúng như dự đoán vì máy có 4 lõi vật lý.

Suy ra cho lần chạy thật `results/bench_detect_20260819_1453`: ô 320/1 luồng chạy **đầu tiên** nên
được lợi (64,4 ms dù chỉ 1 luồng), ô 640/4 luồng chạy **cuối cùng** nên bị phạt nặng nhất —
độ lệch chuẩn 103,9 ms và p95 489,9 ms là chữ ký của throttling, không phải của thuật toán.

### 1.4. `InferenceSession` — tạo một lần mỗi ô, không tạo trong vòng đo

Bọc đếm `ort.InferenceSession` rồi chạy `main()` thật với **1 mô hình × 2 mức luồng**:

```
main() ma=0  so_InferenceSession=3   (1 lần đọc imgsz + 2 ô ma trận)   660 lần detect
```

3 phiên cho 2 ô, **không phải 200 phiên cho 200 khung**. Mã ở `scripts/benchmark_detect.py:185`
nằm **ngoài** vòng `for` ở dòng 191. Đạt.

### 1.5. `doc_nhiet_do_cpu()` — gọi mỗi khung nhưng **ngoài** cửa sổ đo

`scripts/benchmark_detect.py:192–206`: `ket_thuc = time.perf_counter()` ở **dòng 194**, lời gọi
`doc_nhiet_do_cpu()` ở **dòng 205** — tức sau khi latency đã chốt. Đo chi phí thật trên Windows
(đường dẫn `/sys/...` không tồn tại → `OSError` → `None`):

```
1000 lần gọi = 0,0265 s  →  26,5 µs mỗi lần
```

660 lần trong cả lần chạy = **0,017 s** trên tổng 93,1 s. Không lọt một mili-giây nào vào `latency_ms`.

### 1.6. Kiểm chéo bằng ngân sách thời gian — không còn chỗ cho chi phí ẩn

Cộng dồn từ chính tệp CSV thật:

| Hạng mục | Giây |
|---|---|
| Tổng `latency_ms` của 600 khung đo | 84,3 |
| Ước tính 60 khung làm nóng (10 × 6 ô, theo latency trung bình từng ô) | 8,4 |
| **Cộng** | **92,7** |
| `duration_s` trong meta | **93,1** |
| **Phần dư** cho 660 lần đọc nhiệt độ + 9 lần nạp mô hình + ghi 2 tệp | **0,4** |

0,4 giây trên 93,1 giây (0,43 %). Không còn chỗ cho `imread` trong vòng lặp, ép kiểu thừa hay
nạp lại mô hình.

### 1.7. Ép kiểu / sao chép mảng

`anh_da_nap[so_lam_nong:tong_can]` cắt lát **một lần** ở đầu `for`, ngoài cửa sổ đo. Trong thân
vòng lặp chỉ có `detector.detect(anh)` giữa hai `perf_counter`. Ca dòng 16 quét `ast` xác nhận
không có `imread`/`open`/`read_bytes`; ĐB5 chứng minh ca đó có hiệu lực (§4).

### 1.8. Hệ quả cho phép đo trên Pi 5 — góp ý, không chặn

Thứ tự ma trận cố định cộng với một máy nóng dần lên tạo **sai lệch hệ thống có hướng**: ô chạy
sớm luôn được lợi. Pi 5 throttling ở 80–85 °C nên vấn đề này **nặng hơn** trên phần cứng đích.
Đây là chỗ đặc tả chưa phủ → xem GY-1.

---

## 2. Ưu tiên số hai — ĐB2, ca biên đúng 10 FPS

Đổi `>=` thành `>` tại `scripts/benchmark_detect.py:243`:

```
1 failed, 44 passed
ca đỏ: ['test_dong22_bien_dung_tai_10fps']
```

**Đúng dòng 22 đỏ, đúng một mình nó.** Dòng 20 (20 FPS) và dòng 21 (5 FPS) vẫn xanh — đúng như
đặc tả dự đoán. Ca dòng 22 dựng đúng ca biên: `_bg_tu_latency([100.0] * 10)` ⇒
`np.mean = 100,0 ms` ⇒ `fps_tb = 1000/100 = 10,0` chằn chặn, rồi assert cả
`fps_tb == approx(10.0)` lẫn `dat_chi_tieu is True` (`tests/test_benchmark_detect.py:351–356`).

Con số quyết định cột Đạt/Không đạt của Chương 4 **được một ca test canh đúng ranh giới**.

---

## 3. Kết quả kiểm máy

### 3.1. Trên host (Windows 11, Python 3.12.5)

| Lệnh | Kết quả |
|---|---|
| `black --line-length 100 --check scripts/benchmark_detect.py tests/test_benchmark_detect.py` | ✅ 2 files unchanged |
| `ruff check` (hai tệp) | ✅ All checks passed |
| `python -m pytest tests/test_benchmark_detect.py -v` | ✅ **45 passed** in 6,38 s |
| `git status --short --untracked-files=all` | ✅ đúng 2 tệp mã + cặp `results/bench_detect_20260819_1453.*` + 3 `.docx` của sinh viên |
| `black --check src tests scripts` (toàn kho) | ✅ 29 files unchanged |
| `ruff check src tests scripts` (toàn kho) | ✅ All checks passed |
| `pytest -q` (toàn kho) | ✅ **288 passed** in 51 s |

### 3.2. Trên container ARM64 — ❌ **CHƯA KIỂM ĐƯỢC**

Docker daemon trên máy này hỏng (`500 Internal Server Error` trên cả hai context `desktop-linux`
và `default`). Không dựng được image.

Bù lại bằng **phân tích tĩnh + giả lập môi trường container trên host**, và phát hiện được một lỗi
chặn thật — xem CHẶN-B-1. Người cài đặt phải chạy lại §8 trên container sau khi sửa và dán kết quả.

### 3.3. Bốn lệnh `grep` §8 — giải trình

```
grep -nE "\b(10|100|320|640)\b" scripts/benchmark_detect.py
```
| Dòng | Nội dung | Kết luận |
|---|---|---|
| 39–40 | `# ... CLAUDE.md §1: "FPS riêng module detect >= 10 FPS"` + `NGUONG_FPS_TOI_THIEU = 10.0` | ✅ hằng số có tên, chú thích dẫn nguồn — đúng ngoại lệ đặc tả cho phép |
| 43–44 | `# R9 (experiment-protocol §6) ...` + `SO_FRAME_TOI_THIEU = 100` | ✅ như trên |
| 332 | `default=["models/yolov8n-face-320.onnx", "models/yolov8n-face-640.onnx"]` | ✅ giá trị mặc định CLI, đặc tả nói rõ không tính là hardcode |
| 345 | `--warmup ... default=10` | ✅ giá trị mặc định CLI |

Ba lệnh còn lại (`except Exception`, `ultralytics|import torch`, `raise ValueError|TypeError`):
**rỗng cả ba** ✅.

### 3.4. Quét mẫu vi phạm §2 rubric — sạch

`except:` trần · `logger.x(f"...")` · đường dẫn tuyệt đối máy cá nhân · secret ·
`assert True`/`pass` trong test · `InferenceSession` trong tệp script · `print()` trong `src/` ·
`time.time` · float trần trong so sánh — **không dòng nào khớp**.

`git status | grep -Ei '\.(jpg|png|npy|onnx|pt|env|db)$'` → rỗng ✅.

### 3.5. Đối chiếu AST — 45 hàm test ↔ 45 dòng bảng §7

```
số hàm test: 45 · thiếu: [] · thừa: [] · trùng: [] · đúng thứ tự: True
```
Ánh xạ 1–1 với `01..43` cộng `29b`, `29c`. Không hàm test nào thiếu `assert`.

---

## 4. Sáu phép đột biến §8 — đủ sáu, đúng ca

`sha256` trước khi động vào: `72ecd5b6465fe0e9a18c60bbfdafeaace7725297b163fc7779aa7601a633dc9c`
Ghi/đọc bằng `open(..., newline="")` để không đổi kiểu xuống dòng.

| # | Phép đột biến | Đặc tả đòi đỏ | Thực tế đỏ | |
|---|---|---|---|---|
| ĐB1 | `anh_da_nap[so_lam_nong:tong_can]` → `anh_da_nap[:tong_can]` | 11 | `test_dong11` (1 failed) | ✅ |
| ĐB2 | `fps_tb >= NGUONG` → `fps_tb > NGUONG` | **22** | `test_dong22` (1 failed) | ✅ |
| ĐB3 | `trong_container = dang_trong_container()` → `= False` | 34, 35 | `test_dong34`, `test_dong35` (2 failed) | ✅ |
| ĐB4a | `latency_tb = np.mean(...)` → `np.std(...)` | 17 | `test_dong17` + 20, 21, 22, 23 (5 failed) | ✅ |
| ĐB4b | `latency_do_lech = np.std(...)` → `np.mean(...)` | 18 | `test_dong18` (1 failed) | ✅ |
| ĐB5 | chèn `cv2.imread(...)` ngay trước `bat_dau` | 16 | `test_dong16` (1 failed) | ✅ |
| ĐB6 | `if args.n_frames < SO_FRAME_TOI_THIEU:` → `if False:` | 39 | `test_dong39` (1 failed) | ✅ |

ĐB4 chạy **cả hai chiều** vì đặc tả ghi "hoặc ngược lại"; chiều a chỉ làm đỏ dòng 17, phải có
chiều b mới chạm dòng 18. ĐB4a đỏ lan sang 20–23 là hợp lý (bốn ca đó đều đọc `latency_tb`
qua `fps_tb`), không phải ca test quá rộng.

`sha256` sau khôi phục: `72ecd5b6...a633dc9c` — **KHỚP** ✅.

> ⚠️ ĐB6 để lộ một tác dụng phụ: khi guard bị gỡ, `test_dong39` chạy **benchmark thật** và ghi
> hai cặp tệp `bench_detect_20260819_{1553,1555}.*` vào `results/` thật. Tôi đã xoá chúng, cây
> làm việc trở về đúng trạng thái ban đầu (`git status` xác nhận). Đây là bằng chứng cho CẦN SỬA-3.

---

## 5. Kiểm tệp kết quả thật `results/bench_detect_20260819_1453.*`

| Mục | Yêu cầu | Thực tế |
|---|---|---|
| Cột CSV | 10 cột, đúng thứ tự §6 | ✅ `run_id,backend,imgsz,threads,sample_idx,latency_ms,fps_instant,n_faces,conf_top,cpu_temp_c` |
| Số dòng | 600 = 6 ô × 100 khung | ✅ 600, mỗi cặp (imgsz, threads) đúng 100 |
| `meta.json` | đủ 18 khoá | ✅ **đúng 18 khoá**, không thừa không thiếu |
| `device` | 4 trường con | ✅ `name` = "PC phát triển", `os` = Windows-11-10.0.26200-SP0, `machine` = AMD64, `processor` = Intel64 Family 6 Model 140 |
| `software` | 4 phiên bản | ✅ python 3.12.5 · onnxruntime 1.20.1 · opencv-python 4.13.0 · numpy 2.2.0 |
| `canh_bao_hieu_nang` | **không** có (chạy ngoài container) | ✅ vắng mặt |
| `git_commit` | khớp kho | ✅ `86df4fcce25016f43cff3dd7bf10af51e453ac84` = `git rev-parse HEAD` |
| `git_dirty` | `true` (code chưa commit) | ✅ `true` |
| `cpu_temp_c` trong CSV | chuỗi **rỗng**, không phải `"None"` | ✅ tập giá trị phân biệt = `{''}` |
| `imgsz` | đọc từ đồ thị ONNX | ✅ 320 và 640, lấy qua `detector.kich_thuoc_vao` (`benchmark_detect.py:457`), khớp `yolo_face.py:198` `int(dau_vao.shape[2])` |
| `seed`, `warmup_frames` | 42, 10 | ✅ |
| `notes` | ghi chú người chạy | ✅ không rỗng |

### 5.1. Trung thực số liệu — tự tính lại `tom_tat` từ CSV thô

Tính lại `latency_tb`, `latency_do_lech`, `latency_p50/p95`, `fps_tb` cho cả 6 ô trực tiếp từ 600
dòng CSV rồi so với `tom_tat`:

```
cả 6/6 ô: khớp tới 1e-9  (dat_chi_tieu: 320 → True ×3, 640 → False ×3)
```

**Không có con số nào trong meta mà CSV không đẻ ra được.** Đây là điều kiện R6 (truy vết) —
đạt tuyệt đối.

### 5.2. Đối chiếu với mốc §3 — hợp lý

Mốc §3 đo ở `num_threads=0`; bảng kết quả đo ở 1/2/4 luồng và trong điều kiện máy nóng dần.
Sau khi khử hai yếu tố đó (§1.2), script tái lập mốc trong 3 %. Không có dấu hiệu "lệch hàng chục
lần" mà §3 dùng làm tiêu chí báo động. ✅

Cảnh báo sớm ở §3 đặc tả được xác nhận: **640 không đạt 10 FPS ngay trên máy để bàn** (3,9–5,0 FPS).
Đúng như §9, script chỉ ghi số, không kết luận — dòng cuối bảng tổng kết in nguyên câu nhắc rằng
kết luận chính thức phải đợi Pi 5 thật (`benchmark_detect.py:557–560`). ✅

---

## 6. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §4 Giao diện CLI | ✅ đủ 11 cờ, đúng tên, đúng mặc định. `--device-name` bắt buộc, thiếu → trả `1` |
| §5 Giao diện hàm | ✅ 7 hàm đúng tên, đúng thứ tự tham số, đúng kiểu trả về, docstring tiếng Việt kiểu Google, type hints đủ |
| §6 Định dạng kết quả | ✅ CSV 10 cột thô, meta 18 khoá — xem §5 biên bản |
| §6 Chốt chặn container | ✅ hoạt động đầu-cuối — xem §7 biên bản |
| §7 Bảng nghiệm thu (45 dòng) | ✅ 45/45 ca, ánh xạ 1–1, đủ sáu phép đột biến |
| §8 Lệnh kiểm | 🟡 host sạch; **container chưa kiểm được** (docker hỏng) và có lỗi sẽ nổ ở đó |
| §9 Ngoài phạm vi | ✅ không đụng NCNN, không đo throttling 10 phút, không kết luận Đạt/Không đạt |
| §10 Ràng buộc kỹ thuật | ✅ chỉ `numpy`/`cv2`/`onnxruntime`/`src/**`; `logging` qua `lay_logger`; `print()` chỉ ở bảng CLI; `perf_counter`; `pathlib`; không ca nào cần mô hình thật |
| §2 Danh sách trắng | ✅ đúng 2 tệp mã nguồn mới, không chạm `src/`, `configs/`, `docs/`, `.claude/` |

---

## 7. Chốt chặn container — kiểm đầu-cuối bằng `/.dockerenv` thật

Ca dòng 34/35/36 giả lập ở tầng hàm (`monkeypatch.setattr(bd, "dang_trong_container", lambda: True)`),
tức **không** đi qua đường phát hiện thật. Tôi kiểm lại bằng cách tạo một tệp `.dockerenv` thật và
trỏ `_DUONG_DAN_DOCKERENV` vào đó, rồi chạy `main()` nguyên bản:

```
dang_trong_container() = True
[stdout] CẢNH BÁO: đang chạy trong container ARM64 (QEMU) — số đo thời gian KHÔNG quy đổi được...
[log]    WARNING Đang chạy trong container — số đo hiệu năng không dùng được (QEMU)
ma = 0 · có canh_bao_hieu_nang: True
    → "Đo trong container ARM64 giả lập qua QEMU — thời gian KHÔNG quy đổi được sang Raspberry Pi 5
       thật, KHÔNG dùng số này làm số hiệu năng chính thức trong báo cáo..."

xoá /.dockerenv → dang_trong_container() = False · có canh_bao_hieu_nang: False
```

Chốt ngăn số liệu QEMU lọt vào báo cáo **hoạt động thật**, cả ba yêu cầu §6 (thêm khoá, in màn
hình, vẫn chạy bình thường) đều đạt. ✅

---

## 8. Bộ đầu vào hỏng tự dựng

29 ca đầu vào hỏng cho `chon_anh`, `tong_hop`, `ghi_ket_qua`, cộng 5 ca ở tầng CLI. Hai ca có hậu
quả thật → CẦN SỬA-1 và CẦN SỬA-2 dưới đây. Phần còn lại là lỗi lập trình viên (sai kiểu tham số),
đặc tả không đòi phải thành `LoiCauHinh` → gom vào GY-3.

| Đầu vào | Kết quả |
|---|---|
| `chon_anh(d, 20, 42)` trên thư mục là **tệp** | ✅ `LoiCauHinh` |
| `chon_anh(d, -5, 42)` | ⚠️ `ValueError: Sample larger than population or is negative` |
| `chon_anh(d, "20", 42)` / `20.5` | ⚠️ `TypeError` |
| `chon_anh(d, 0, 42)` | ⚠️ trả `[]`, không báo gì |
| `tong_hop(None)` / `[]` | ✅ `LoiCauHinh` |
| `tong_hop([{"n_faces": 1}])` (thiếu `latency_ms`) | ⚠️ `KeyError` |
| `tong_hop([{"latency_ms": 0.0, ...}])` | ⚠️ `ZeroDivisionError` |
| `tong_hop([{"latency_ms": -10.0, ...}])` | ⚠️ không ném, trả `fps_tb = -100` |
| `ghi_ket_qua(..., meta=["a"])` | ✅ `LoiCauHinh` liệt kê 18 khoá thiếu |
| `ghi_ket_qua(..., meta` chứa object không JSON-hoá được`)` | ⚠️ `TypeError` **sau khi CSV đã ghi xong** → GY-2 |
| `main(--warmup -90 --n-frames 100)` | 🟡 **trả 0, ghi tệp 10 dòng nhưng meta khai 100** → CẦN SỬA-1 |
| `main(--models a/x.onnx b/x.onnx)` | 🟡 **CSV 200 dòng nhưng `tom_tat` chỉ 1 mục** → CẦN SỬA-2 |
| `main(--threads 1 1 2)` | 🟡 cùng gốc với CẦN SỬA-2: CSV 300 dòng, `tom_tat` 2 mục |
| `main(--seed -1)`, `--warmup 0` | ✅ chạy bình thường |
| `--threads 100` (> `SO_LUONG_TOI_DA`) | ✅ `LoiCauHinh` bị bắt, trả `1` |

---

## Lỗi phải sửa

### 🔴 CHẶN-B-1 — `test_dong30` chết trên container ARM64 (CB-6, vi phạm §8 đặc tả)

**Vị trí**: `tests/test_benchmark_detect.py:462–469`

```python
def test_dong30_git_commit_khop_kho_that():
    ket_qua = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert bd._lay_git_commit_hash() == ket_qua.stdout.strip()
```

**Vì sao**: container ARM64 của dự án **không có `git`** và **không có thư mục `.git`**:

- `deploy/Dockerfile.arm64` cài đúng `libgl1` và `libglib2.0-0` trên `python:3.11-slim-bookworm`
  — không có gói `git`.
- `.dockerignore` dòng 1 là `.git/` — thư mục `.git` **không được COPY** vào image.

Hàm sản phẩm `_lay_git_commit_hash()` xử lý đúng (bắt `OSError`/`CalledProcessError`, trả
`"khong-xac-dinh"`, `benchmark_detect.py:297–299`). Nhưng **ca test tự gọi `subprocess.run` với
`check=True` mà không bọc** → ngoại lệ lọt thẳng ra.

Chứng minh trên host bằng cách xoá `git` khỏi `PATH` (mô phỏng đúng môi trường container):

```
hàm sản phẩm trả về: khong-xac-dinh          ← đúng, có xử lý
FAILED tests/test_benchmark_detect.py::test_dong30_git_commit_khop_kho_that
E   FileNotFoundError: [WinError 2] The system cannot find the file specified
1 failed in 0.71s
```

Hai đường độc lập cùng làm đỏ ca này trong container: (1) không có nhị phân `git`, (2) kể cả có
`git` thì `/app` không phải kho git → `CalledProcessError`. Đây đúng mẫu lỗi đã gặp ở
`P2-01` CHẶN-B-1 (`import onnx` làm chết bộ test trên ARM64) — §8 đặc tả đòi `pytest` xanh **cả
trên container**, mà ở đó nó đỏ.

**Sửa**: bỏ qua có thông báo khi môi trường không có kho git, đúng tinh thần §10 ("ca cần … phải
`pytest.skip` có thông báo"):

```python
import shutil

def test_dong30_git_commit_khop_kho_that():
    goc_kho = Path(bd.__file__).resolve().parents[1]
    if shutil.which("git") is None or not (goc_kho / ".git").exists():
        pytest.skip("Môi trường không có git hoặc không có .git/ (container ARM64) — bỏ qua")
    ket_qua = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True, cwd=goc_kho
    )
    assert bd._lay_git_commit_hash() == ket_qua.stdout.strip()
```

Thêm `cwd=goc_kho` để ca test đối chiếu **cùng thư mục** mà hàm sản phẩm dùng — hiện tại ca test
dùng cwd của pytest, hàm dùng gốc kho; hai bên chỉ tình cờ trùng nhau.

---

### 🟡 CẦN SỬA-1 — `--warmup` âm vô hiệu hoá chốt R9, meta khai sai số khung (CB-1)

**Vị trí**: `scripts/benchmark_detect.py:344–346` (không kiểm `--warmup`), `:417`, `:516`

```python
    parser.add_argument(
        "--warmup", type=int, default=10, help="Số khung hình làm nóng, không tính vào kết quả"
    )
...
    so_can = args.n_frames + args.warmup            # dòng 417
...
        "n_frames_moi_cau_hinh": args.n_frames,     # dòng 516 — khai theo cờ, không theo số đo thật
```

`--warmup` âm làm `tong_can = so_lam_nong + so_luong` co lại, và phép cắt lát
`anh_da_nap[so_lam_nong:tong_can]` với `so_lam_nong` âm đếm ngược từ cuối. Chạy thật:

```
--n-frames 100 --warmup -90  →  mã trả về 0, ghi tệp bình thường
   CSV: 10 dòng          tom_tat n_frames = 10
   meta dataset.n_frames_moi_cau_hinh = 100      ← KHAI SAI
   meta warmup_frames = -90
```

**Vì sao**: một tệp trong `results/` là nguồn sự thật của báo cáo (R6). Ở đây nó tự mâu thuẫn —
khai đo 100 khung nhưng chỉ có 10 dòng dữ liệu — và **lách qua** đúng cái guard `--n-frames >= 100`
được dựng lên để thi hành R9. Nếu con số đó vào Chương 4, độ lệch chuẩn và p95 được tính trên
10 mẫu sẽ bị đọc như tính trên 100.

**Sửa**: hai thay đổi nhỏ, cùng chỗ với guard `--n-frames` đã có (dòng 378–384):

```python
    if args.warmup < 0:
        logger.error("--warmup=%d không được âm", args.warmup)
        print(f"--warmup phải >= 0, nhận được {args.warmup}.")
        return 1
```

và đổi dòng 516 để khai theo **số bản ghi thật** thay vì theo cờ:

```python
        "n_frames_moi_cau_hinh": len(toan_bo_ban_ghi) // max(len(tom_tat), 1),
```

Bổ sung một ca test cạnh dòng 39: `main([..., "--warmup", "-1"]) == 1`.

---

### 🟡 CẦN SỬA-2 — `tom_tat` mất ô khi hai mô hình trùng `stem` hoặc `--threads` trùng (CB-1, vi phạm dòng 40)

**Vị trí**: `scripts/benchmark_detect.py:459` và `:473`, dùng lại ở `:550`

```python
            imgsz_theo_mo_hinh[m.stem] = imgsz
...
                tom_tat[f"{m.stem}_t{t}"] = tong_hop(ban_ghi)
```

Khoá tổng hợp chỉ gồm **tên tệp không đuôi**. Chạy thật với hai mô hình khác thư mục nhưng trùng tên:

```
--models  <tmp>/v1/yolov8n-face-320.onnx  <tmp>/v2/yolov8n-face-320.onnx  --threads 1
   mã trả về 0
   CSV: 200 dòng  (đúng 2 ô)
   tom_tat: 1 mục ['yolov8n-face-320_t1']      ← ô thứ nhất bị ô thứ hai ĐÈ MẤT
```

Tương tự với `--threads 1 1 2`: CSV 300 dòng, `tom_tat` 2 mục.

**Vì sao**: dòng 40 của bảng §7 quy định bất biến "ma trận đúng số ô ⇒ `tom_tat` đúng số mục".
Bất biến đó vỡ với đầu vào hợp lệ. Nặng hơn: bảng tổng kết ở dòng 548–556 tra `tom_tat` theo cùng
khoá đó, nên **hai dòng bảng in ra số liệu y hệt nhau** cho hai mô hình khác nhau. Đúng kịch bản
bước 2.6 sẽ dùng khi so hai bản export cùng độ phân giải (opset khác, quantize khác) — số vào
Chương 4 sẽ sai mà không ai nhận ra vì cột "Cấu hình" in `m.name` cũng trùng.

**Sửa**: khoá theo chỉ số ô, giữ đường dẫn đầy đủ để phân biệt:

```python
        for i, m in enumerate(models):
            ...
            imgsz_theo_mo_hinh[i] = imgsz
            for t in threads_list:
                ...
                tom_tat[f"{i:02d}_{m.stem}_t{t}"] = tong_hop(ban_ghi)
```

và sửa vòng in bảng ở dòng 548 dùng cùng khoá. Bổ sung một ca test: 2 mô hình trùng `stem`
× 1 mức luồng ⇒ `len(tom_tat) == 2`.

---

### 🟡 CẦN SỬA-3 — Ca dòng 37, 39, 42 không cô lập thư mục kết quả (CB-6)

**Vị trí**: `tests/test_benchmark_detect.py:573`, `:589`, `:635`

```python
def test_dong39_n_frames_duoi_nguong(capsys):
    ma = bd.main(["--device-name", "PC test", "--n-frames", "50"])
```

Ba ca này gọi `main()` mà **không** `monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)`,
khác với các ca 34–36, 38, 40, 41, 43 vốn có. Chúng chỉ an toàn nhờ `main()` trả `1` trước khi ghi.

**Vì sao**: bằng chứng thực tế từ ĐB6 của chính lượt review này — khi guard bị gỡ, `test_dong39`
chạy benchmark thật 6 ô trên mô hình thật và **ghi hai cặp tệp vào `results/` thật**, mỗi tệp chỉ
50 khung/ô (vi phạm R9). Tôi đã phải xoá thủ công. Một ca test **không được** có khả năng ghi vào
nguồn sự thật của báo cáo, kể cả khi code sai. Ca dòng 42 (`--config` hỏng) và 37 (thiếu
`--device-name`) cùng rủi ro.

**Sửa**: thêm `tmp_path, monkeypatch` vào ba ca đó và đặt dòng đầu tiên:

```python
def test_dong39_n_frames_duoi_nguong(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    ...
```

---

## 🔵 Góp ý (không chặn — người dùng quyết định)

**GY-1 — Thứ tự ma trận cố định tạo sai lệch hệ thống; gửi `spec-writer`.**
Đo được ở §1.3: cùng cấu hình 640, máy nguội 135 ms, máy nóng 200–230 ms — chênh 50 %. Ô chạy sớm
luôn được lợi. Pi 5 throttling ở 80–85 °C nên vấn đề nặng hơn. Ba mức khắc phục, chi phí tăng dần:
(a) ghi `cpu_temp` đầu/cuối **từng ô** vào `tom_tat` (hiện chỉ có `cpu_temp_start_c`/`cpu_temp_max_c`
toàn cục) — rẻ nhất, cho phép hậu kiểm; (b) thêm cờ `--nghi-giua-o <giây>`; (c) chạy ma trận theo
thứ tự ngẫu nhiên hoá theo `--seed` và lặp lại nhiều vòng. Đây là sửa **đặc tả**, không phải lỗi
người cài đặt.

**GY-2 — `ghi_ket_qua` ghi CSV trước, meta sau, không nguyên tử.**
`benchmark_detect.py:273–280`. Nếu `json.dump` ném giữa chừng (đo được với meta chứa object không
JSON-hoá được), `results/` còn lại CSV hợp lệ cạnh một `meta.json` cụt — số liệu mất ngữ cảnh
truy vết (R17). Đường vào thực tế: `config_snapshot` lấy nguyên từ YAML, mà PyYAML biến
`2026-08-19` thành `datetime.date` không JSON-hoá được — chỉ cần ai đó thêm một khoá ngày vào
`configs/detect.yaml`. Sửa rẻ: `json.dumps(meta, ...)` ra chuỗi **trước** khi mở tệp nào.

**GY-3 — Đầu vào sai kiểu ném ngoại lệ thô thay vì `LoiCauHinh`.**
`chon_anh` với `so_luong` âm/chuỗi/float, `tong_hop` thiếu khoá hoặc `latency_ms = 0`,
`ghi_ket_qua` với `ban_ghi = None` — xem bảng §8. Đặc tả §5 chỉ liệt kê một số điều kiện phải
thành `LoiCauHinh`, nên **không tính là vi phạm**. Đây là hàm nội bộ do chính `main()` gọi, rủi ro
thực tế thấp. Ghi nhận để cân nhắc khi P3 tái dùng bộ khung này.

**GY-4 — `chon_anh(d, 0, seed)` trả `[]` im lặng.** Không tới được từ CLI vì guard `--n-frames >= 100`.

**GY-5 — `tong_hop` không kiểm `latency_ms > 0`.** `ZeroDivisionError` nếu latency đúng 0.
Không tới được với `perf_counter` (phân giải ~100 ns) trên tải ≥ 1 ms. Ghi nhận cho đủ.

**GY-6 — `cpu_temp_c` ghi mỗi khung nhưng chưa dùng.** Trên Pi 5 sẽ có 600 giá trị nhiệt độ trong
CSV; bước 2.7 (throttling 10 phút) có thể dùng lại cột này thay vì đo riêng — tiết kiệm một mã việc.

---

## Việc tiếp theo

Bốn mục phải sửa, cả bốn đều nhỏ và độc lập nhau (≈ 25 dòng tổng cộng):

| Mã | Tệp | Ước lượng |
|---|---|---|
| CHẶN-B-1 | `tests/test_benchmark_detect.py:462` | ~5 dòng |
| CẦN SỬA-1 | `scripts/benchmark_detect.py:344, 378, 516` + 1 ca test | ~10 dòng |
| CẦN SỬA-2 | `scripts/benchmark_detect.py:459, 473, 550` + 1 ca test | ~8 dòng |
| CẦN SỬA-3 | `tests/test_benchmark_detect.py:573, 589, 635` | ~6 dòng |

Sau khi sửa, người cài đặt chạy lại **bốn lệnh §8 trên host và trên container ARM64** (lần này
container là bắt buộc — CHẶN-B-1 chỉ lộ ra ở đó), dán kết quả, **không commit**.

**Không cần chạy lại benchmark thật**: `results/bench_detect_20260819_1453.*` đã được kiểm là
trung thực và không mục nào ở trên làm sai lệch số đo đã có. Giữ nguyên cặp tệp đó.

Khi đạt, commit message đề xuất (R29):

```
feat(scripts): script đo hiệu năng khối phát hiện khuôn mặt trên ma trận độ phân giải × số luồng
```

---
---

# Review P2-03-benchmark-detect — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-03-benchmark-detect.md` (§3 đã cập nhật: mốc là **số máy nguội**) |
| **Nhánh** | `feat/p2-03-benchmark-detect` (chưa commit, cây làm việc để nguyên) |
| **HEAD khi review** | `86df4fc` |
| **Ngày** | 2026-08-19 |
| **Phán quyết** | ✅ **ĐẠT** — hết 🔴 và 🟡; còn 3 mục 🔵 không chặn |

> Cả bốn mục vòng 1 đã đóng, **và cả bốn đều được chứng minh bằng phép đột biến riêng** chứ không
> chỉ bằng test xanh. Phần đo không bị đụng tới một dòng nào. `results/` sạch sau toàn bộ 10 phép
> đột biến — kể cả ĐB6, phép đã làm lộ lỗi ở vòng 1.

---

## 1. Phạm vi thay đổi

`diff` giữa bản vòng 1 và bản vòng 2 của `scripts/benchmark_detect.py`: **19 thêm, 8 bớt**,
toàn bộ nằm trong `main()` và vùng argparse. Hai tệp đúng danh sách trắng §2, không chạm
`src/`, `configs/`, `docs/`, `.claude/`.

| Tệp | sha256 vòng 2 |
|---|---|
| `scripts/benchmark_detect.py` | `21508785effab432e30f7197a96ec822ef4ff5f8f10c1439f5ce0df8ffea26a6` |
| `tests/test_benchmark_detect.py` | `2ff53da91caaac60495c681444923471756170d1a076e50a0a056ca30f086deb` |
| `results/bench_detect_20260819_1453.csv` | `e29a56a9...c95262` — **không đổi**, mtime vẫn 14:53 |

---

## 2. Kết quả kiểm máy

### 2.1. Trên host (Windows 11, Python 3.12.5)

| Lệnh | Kết quả |
|---|---|
| `black --line-length 100 --check` (hai tệp) | ✅ 2 files unchanged |
| `ruff check` (hai tệp) | ✅ All checks passed |
| `pytest tests/test_benchmark_detect.py -q` | ✅ **47 passed** (45 + 2 ca mới) |
| `black --check src tests scripts` | ✅ 29 files unchanged |
| `ruff check src tests scripts` | ✅ All checks passed |
| `pytest -q` (toàn kho) | ✅ **290 passed** (vòng 1: 288, +2) |
| `git status --short --untracked-files=all` | ✅ đúng phạm vi, `results/` không sinh tệp mới |

### 2.2. Mô phỏng container ARM64 — ❌ **VẪN CHƯA CHẠY ĐƯỢC TRÊN CONTAINER THẬT**

Docker daemon vẫn hỏng (`500 Internal Server Error` trên npipe, cả context `desktop-linux` lẫn
`default`). **Ghi lại để sau này chạy lại**: bốn lệnh §8 trên `deploy/Dockerfile.arm64` là việc
còn nợ của mã việc này, không phải việc đã làm.

Thay thế gần nhất — chạy **toàn bộ** tệp test với `PATH` không có `git` (đúng tình trạng container:
image không cài `git`, `.dockerignore` loại `.git/`):

```
46 passed, 1 skipped in 3.59s
SKIPPED [1] tests/test_benchmark_detect.py:468: Môi trường không có git hoặc không có .git/ (container ARM64) — bỏ qua
```

Không ca nào khác phụ thuộc `git`. Quét toàn bộ hai tệp cho `git` / `.git` / `docs/` / `models/` /
`data/` / `results/`: mọi chỗ còn lại đều là chuỗi mặc định argparse hoặc đã bọc `try/except`.

### 2.3. Bốn lệnh `grep` §8 — không đổi so với vòng 1

Lệnh 1 ra đúng 4 dòng đã giải trình ở vòng 1 (hai hằng số có tên kèm chú thích dẫn nguồn, hai giá
trị mặc định CLI). Ba lệnh còn lại **rỗng**. Quét rubric §2 (`except:` trần, log dùng f-string,
đường dẫn tuyệt đối, secret, `assert True`, `time.time`) — **rỗng toàn bộ**.

### 2.4. Quét AST — 47 hàm ↔ 45 dòng bảng §7 + 2 ca mới

```
số hàm test: 47 · thiếu: [] · thừa: [] · trùng: [] · đúng thứ tự: True
```

Hai ca mới đặt đúng chỗ trong dãy: `test_dong39b_warmup_am_tra_ve_1` và
`test_dong40b_ma_tran_hai_mo_hinh_trung_ten_khac_thu_muc`.

---

## 3. Bốn mục vòng 1 — đối chiếu từng mục

### 3.1. CHẶN-B-1 — gọi `git` — ✅ ĐÓNG

`tests/test_benchmark_detect.py:463-477`. Kiểm **cả hai chiều**, đúng yêu cầu "không được skip
luôn cho tiện":

| Môi trường | Kết quả | |
|---|---|---|
| **Không** có `git` trên `PATH` | `1 skipped` — thông báo nêu rõ lý do và container ARM64 | ✅ |
| **Có** `git` (host bình thường) | `1 passed` — chạy thật, assert thật | ✅ |

Và phép đột biến **ĐB7** (bịa `_lay_git_commit_hash` trả 40 số 0) làm **đỏ đúng
`test_dong30`** → ca test vẫn còn răng, việc sửa không làm mất phép kiểm.

Thêm `cwd=goc_kho` như đề xuất: ca test nay đối chiếu cùng thư mục mà hàm sản phẩm dùng.

### 3.2. CẦN SỬA-1 — `--warmup` âm — ✅ ĐÓNG

`scripts/benchmark_detect.py:386-390`, đặt ngay sau chốt `--n-frames`, **trước** khi nạp cấu hình.

| Đầu vào | Mã trả về | Tệp sinh ra | Thông báo |
|---|---|---|---|
| `--n-frames 100 --warmup -90` *(ca lỗi vòng 1)* | **1** | **0** | `--warmup phải >= 0, nhận được -90.` |
| `--warmup -1` (biên) | **1** | 0 | `--warmup phải >= 0, nhận được -1.` |
| `--warmup 0` (biên hợp lệ) | 0 | 2 | CSV 300 dòng, meta khai **100** — khớp |
| `--warmup 10000` (> số ảnh) | **1** | 0 | `Không đủ ảnh ...: có 160, cần 10100` |
| `--warmup abc` (sai kiểu) | **2** | 0 | argparse: `invalid int value: 'abc'` |

Ca lỗi vòng 1 **không còn tái hiện**: không còn CSV 10 dòng kèm meta khai 100.
`dataset.n_frames_moi_cau_hinh` nay tính từ **số bản ghi thật** (dòng 521-527), không từ cờ.
ĐB8 (gỡ chốt `--warmup < 0`) làm đỏ đúng `test_dong39b` → chốt có ca test canh.

### 3.3. CẦN SỬA-2 — `tom_tat` trùng khoá — ✅ ĐÓNG

Khoá nay gồm chỉ số ô (dòng 481), vòng in bảng dùng cùng khoá (dòng 559-566).

Hai mô hình **trùng tên tệp, khác thư mục** (`v1/gia.onnx`, `v2/gia.onnx`) × 3 mức luồng:

```
số mục tom_tat = 6   khoá: ['00_gia_t1','00_gia_t2','00_gia_t4','01_gia_t1','01_gia_t2','01_gia_t4']
fps từng ô     : 106303.8 · 316957.1 · 332005.4 · 33290.1 · 15166.0 · 32448.6   <- sáu giá trị KHÁC nhau
hai dòng bảng giống hệt nhau? False
meta khai n_frames_moi_cau_hinh = 100
```

Vòng 1 chỗ này cho **1 mục** và bảng in số trùng lặp. ĐB9 (trả khoá về `m.stem`) làm đỏ đúng
`test_dong40b`. Dòng 40 gốc vẫn xanh — ca mới không nuốt ca cũ.

### 3.4. CẦN SỬA-3 — ca test ghi vào `results/` — ✅ ĐÓNG

Ba ca 37, 39, 42 nay đều `monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)`
(dòng 581-582, 598-599, 686-687); hai ca mới 39b, 40b cũng có.

Phép kiểm quyết định — chạy **cả 10 phép đột biến** (gồm ĐB6, thủ phạm vòng 1) rồi soi lại:

```
git status  ->  không sinh tệp nào
results/    ->  đúng 2 cặp tệp cũ, mtime 14:53 và 15:12, không đổi
```

Vòng 1 cùng thao tác này để lại `bench_detect_20260819_{1553,1555}.*` phải xoá tay. Nay **sạch**.

---

## 4. Hồi quy — phần đo không bị đụng

| Kiểm | Kết quả |
|---|---|
| `do_mot_cau_hinh` và `tong_hop` | **giống hệt vòng 1 từng ký tự** (`diff` không có hunk nào trong khoảng dòng 150-245) |
| `InferenceSession` mỗi ô | đếm lại trên mã mới: **3 phiên** cho 1 mô hình × 2 mức luồng (1 đọc imgsz + 2 ô), 660 lần `detect` |
| `doc_nhiet_do_cpu()` so với đồng hồ | dòng 192 `bat_dau` · 193 `detect` · 194 `ket_thuc` · **205** `doc_nhiet_do_cpu()` — vẫn sau khi dừng đồng hồ 11 dòng |
| `imread` trong cửa sổ đo | chỉ xuất hiện ở dòng **432**, trong `main`, trước vòng ma trận; ĐB5 vẫn làm đỏ dòng 16 |
| Tệp kết quả thật | `sha256` và mtime **không đổi** — không bị ghi đè |

Kết luận vòng 1 về tính sạch của phép đo **vẫn còn hiệu lực nguyên vẹn**; không cần đo lại.

---

## 5. Mười phép đột biến

`sha256` trước: script `21508785...ea26a6`, test `2ff53da9...86deb`. Ghi/đọc bằng `open(..., newline="")`.

| # | Phép đột biến | Đòi đỏ | Thực tế đỏ | |
|---|---|---|---|---|
| ĐB1 | tính cả khung làm nóng | 11 | `test_dong11` | ✅ |
| **ĐB2** | **`>=` thành `>` ở `dat_chi_tieu`** | **22** | **`test_dong22`, một mình nó** | ✅ |
| ĐB3 | bỏ chốt chặn container | 34, 35 | `test_dong34`, `test_dong35` | ✅ |
| ĐB4a | `np.mean` thành `np.std` ở `latency_tb` | 17 | `test_dong17` (+20, 21, 22, 23 kéo theo) | ✅ |
| ĐB4b | `np.std` thành `np.mean` ở `latency_do_lech` | 18 | `test_dong18` | ✅ |
| ĐB5 | `imread` trong vòng đo | 16 | `test_dong16` | ✅ |
| ĐB6 | bỏ kiểm `--n-frames >= 100` | 39 | `test_dong39` — **và không rác `results/`** | ✅ |
| ĐB7 *(mới)* | `_lay_git_commit_hash` trả số bịa | 30 | `test_dong30` | ✅ |
| ĐB8 *(mới)* | bỏ kiểm `--warmup < 0` | 39b | `test_dong39b` | ✅ |
| ĐB9 *(mới)* | khoá `tom_tat` quay lại `m.stem` | 40b | `test_dong40b` | ✅ |

ĐB2 vẫn đỏ **đúng dòng 22 và chỉ dòng 22** — dòng 20 (20 FPS) và 21 (5 FPS) xanh.
`sha256` sau khôi phục: **KHỚP cả hai tệp**.

---

## 6. 🔵 Góp ý (không chặn — người dùng quyết định)

**GY-7 — `--threads` trùng giá trị vẫn gộp ô; lỗi kê đơn của chính vòng 1.**
Khoá mới gồm chỉ số **mô hình** nhưng không gồm chỉ số **mức luồng**, nên `--threads 1 1 2` cho:

```
CSV 300 dòng (3 ô)  ·  tom_tat 2 mục  ·  meta khai n_frames_moi_cau_hinh = 150   <- sai, thật ra 100
```

Vòng 1 tôi có nêu ca `--threads 1 1 2` nhưng **đoạn "Sửa" chỉ đánh chỉ số cho `models`** — người
cài đặt làm đúng đơn thuốc, thiếu sót thuộc về biên bản vòng 1. Không chặn vì: chỉ kích hoạt khi gõ
trùng giá trị, người chạy nhìn thấy ngay hai dòng cùng mức luồng trong bảng tổng kết của chính mình,
và CSV thô vẫn giữ đủ 300 dòng để tính lại. Sửa một dòng khi tiện:

```python
threads_list: list[int] = list(dict.fromkeys(args.threads))   # bỏ trùng, giữ thứ tự
```

**GY-8 — `ghi_ket_qua` vẫn ghi CSV trước, meta sau** (GY-2 vòng 1, chưa yêu cầu sửa nên chưa sửa —
đúng quy trình). Giữ nguyên đề xuất: `json.dumps(...)` ra chuỗi trước khi mở tệp nào.

**GY-9 — Còn nợ phép kiểm trên container ARM64 thật.** Docker hỏng suốt cả hai vòng. Khi daemon
lên lại, chạy bốn lệnh §8 trong `deploy/Dockerfile.arm64` và ghi kết quả vào nhật ký tuần. Rủi ro
còn lại thấp: đã mô phỏng đúng hai đặc trưng khác biệt của container (thiếu `git`, thiếu `.git/`)
và toàn bộ 47 ca đều qua.

*(GY-1, GY-3 đến GY-6 của vòng 1 giữ nguyên, không mục nào chặn.)*

---

## 7. Tổng kết hai vòng

| | Vòng 1 | Vòng 2 |
|---|---|---|
| 🔴 CHẶN | 1 (CB-1: test chết trên ARM64) | 0 |
| 🟡 CẦN SỬA | 3 | 0 |
| 🔵 GÓP Ý | 6 | 3 (1 mới, 2 mang sang) |
| Ca test | 45 | 47 |
| Phép đột biến | 7 | 10 |
| Phán quyết | 🔴 TRẢ LẠI | ✅ **ĐẠT** |

### Bài học chính — **số đo máy nguội** (vào nhật ký tuần và Chương 3)

Vòng 1 mở ra với một nghi vấn nghiêm trọng: script cho 47,6 ms ở 320 và 198,3 ms ở 640, chậm hơn
mốc tự đo 20 % và 45 %. Nếu kết luận vội là "script có chi phí ẩn", sẽ mất một vòng sửa **một lỗi
không tồn tại**. Bốn phép chạy độc lập cho thấy:

- Chạy **chính script**, **một ô duy nhất**, máy nghỉ 90-120 s trước: 320/4 luồng = **31,8 ms**
  (mốc 39,4), 640/2 luồng = **132,3 ms** (mốc 136,9) — tái lập mốc trong 3 %.
- Chạy **xen kẽ** `num_threads` 4 và 0 ở 640 khi máy đã nóng: hai mức **hội tụ** về 200-230 ms.
  Con số 135 ms không bao giờ quay lại.
- **Kiểm toán ngân sách thời gian**: tổng `latency_ms` 84,3 s + warm-up 8,4 s = 92,7 s so với
  `duration_s` 93,1 s → **dư 0,43 %** cho toàn bộ chi phí ngoài inference. Không còn chỗ cho lỗi.

**Ba hệ quả cho cách đọc mọi số hiệu năng của đồ án về sau:**

1. **Một con số hiệu năng không có trạng thái nhiệt kèm theo là một con số chưa đủ nghĩa.**
   Cùng máy, cùng mã, cùng ảnh, chỉ khác nguội/nóng: chênh **50 %** ở 640. Lớn hơn khoảng cách
   giữa nhiều lựa chọn thiết kế mà đồ án định so sánh.
2. **Ô chạy trước trong một ma trận luôn được lợi.** So sánh ONNX với NCNN, hay 320 với 640, bằng
   cách chạy tuần tự trên máy nóng dần là so sánh **không công bằng** — sai lệch có hướng, không
   phải nhiễu ngẫu nhiên. Pi 5 throttling ở 80-85 °C nên vấn đề nặng hơn máy để bàn (xem GY-1).
3. **Ngân sách thời gian là phép kiểm rẻ nhất để phân biệt "đo sai" với "máy chậm".**
   Cộng `latency` đo được, cộng warm-up, so với `duration_s`. Phần dư lớn thì có chi phí ẩn; phần
   dư nhỏ thì vấn đề nằm ở phần cứng hoặc điều kiện đo. Nên áp dụng cho mọi `bench_*` của
   Phase 3, 4, 7.

Đặc tả §3 đã được `spec-writer` sửa theo phát hiện này (mốc ghi rõ là số máy nguội, chỉ dùng để
bắt sai lệch hàng chục lần). Con số trong `results/bench_detect_20260819_1453.*` **vẫn dùng được**:
nó là số máy nóng, đúng ngữ cảnh đã ghi trong meta, và `tom_tat` tính lại được từ CSV thô tới 1e-9.

---

## 8. Việc tiếp theo

Được commit. Đề xuất (R29):

```
feat(scripts): thêm script đo hiệu năng khối phát hiện khuôn mặt theo ma trận cấu hình
```

Cặp tệp `results/bench_detect_20260819_1453.*` commit kèm — số máy phát triển, dùng để kiểm tính
đúng đắn, **không** phải số Cổng C. Cổng C của Phase 2 vẫn chờ Raspberry Pi 5 thật.

Còn nợ, ghi vào nhật ký tuần: **bốn lệnh §8 trên container ARM64** (GY-9) khi Docker chạy lại.

---
---

# Review P2-03-benchmark-detect — bổ sung kiểm container ARM64

| | |
|---|---|
| **Ngày** | 2026-08-19 |
| **Lý do** | Trả nợ GY-9 của vòng 2 — Docker hỏng suốt hai vòng trước, nay chạy lại được |
| **Phán quyết vòng 2** | ✅ **ĐẠT — GIỮ NGUYÊN**, không thay đổi |
| **Khoản nợ container** | ✅ **ĐÃ TRẢ XONG** |

> Kết luận ngắn: khoản nợ đã trả. `EXE002` là chuyện **toàn kho**, không thuộc `P2-03`.
> Lỗi chặn của vòng 1 nay được xác nhận đã sửa **trên container thật**, không còn phải mô phỏng.
> Phát hiện thêm một khoản nợ container của **`P2-01`** — ghi lại để mở mã việc riêng.

---

## 1. Cách đưa mã vào container — tự build, không dùng ảnh có sẵn

Ảnh `faceid-arm64-test:p2-03-kiem-lai` trong máy **không phải do tôi tạo**, nên không dùng để kết
luận. Tôi tự dựng ảnh riêng từ `deploy/Dockerfile.arm64` nguyên bản:

```
docker build --platform linux/arm64 -f deploy/Dockerfile.arm64 -t faceid-arm64-review:p2-03 .
```

Chạy **hai biến thể** vì hai cách cho môi trường khác nhau:

| | **A — build vào ảnh** *(chính)* | **B — gắn thư mục** `-v "${PWD}:/app"` |
|---|---|---|
| `uname -m` | `aarch64` | `aarch64` |
| `.git/` | **không có** (`.dockerignore`) | **có** |
| `models/`, `data/` | **không có** | **có** |
| nhị phân `git` | **không có** | **không có** |
| quyền tệp `.py` | `-rwxr-xr-x` (0755) | `-rwxrwxrwx` (0777) |

Biến thể **A** là thứ phản ánh đúng artifact triển khai, nên mọi con số dưới đây lấy từ A trừ khi
ghi rõ. Môi trường: Python 3.11.16 · ruff 0.16.1 · black 24.4.2 · pytest 9.1.1 · Docker 29.6.2.

*(Ghi chú vận hành: chạy `docker` từ PowerShell; **không** dùng cờ `--platform` ở `docker run`.)*

---

## 2. Bốn lệnh §8 trong container — nguyên văn

```
###### LENH 1: black --line-length 100 --check (hai tep) ######
All done! ✨ 🍰 ✨
2 files would be left unchanged.
RC=0

###### LENH 2: ruff check (hai tep) ######
EXE002 The file is executable but no shebang is present
--> scripts/benchmark_detect.py:1:1

EXE002 The file is executable but no shebang is present
--> tests/test_benchmark_detect.py:1:1

Found 2 errors.
RC=1

###### LENH 3: pytest tests/test_benchmark_detect.py ######
...............................s...............                          [100%]
SKIPPED [1] tests/test_benchmark_detect.py:468: Môi trường không có git hoặc không có .git/ (container ARM64) — bỏ qua
46 passed, 1 skipped in 10.61s
RC=0

###### LENH 4: git status --short --untracked-files=all ######
KHONG CO nhi phan git trong container (RC=127) — lenh 4 chi co nghia tren host
```

| Lệnh | Kết quả | |
|---|---|---|
| 1 · `black --check` | RC=0, sạch | ✅ |
| 2 · `ruff check` | RC=1, **đúng 2 lỗi, cả hai là `EXE002`** — xem §4 | 🔵 ngoài phạm vi |
| 3 · `pytest` tệp P2-03 | **46 passed, 1 skipped**, RC=0 | ✅ |
| 4 · `git status` | không áp dụng trong container (không có `git`) | — |

---

## 3. Ca test cần `git` — ✅ SKIP SẠCH, KHÔNG ERROR

Đây là **lỗi chặn CHẶN-B-1 của vòng 1**, hai vòng trước chỉ mô phỏng được bằng cách gỡ `git` khỏi
`PATH`. Nay kiểm trên container thật, và kiểm **cả hai nhánh** của điều kiện bảo vệ:

| Biến thể | `.git/` | nhị phân `git` | Nhánh guard được kích hoạt | Kết quả |
|---|---|---|---|---|
| **A** build vào ảnh | không | không | cả hai vế | `1 skipped` ✅ |
| **B** gắn thư mục | **có** | không | chỉ `shutil.which("git") is None` | `1 skipped` ✅ |

```
SKIPPED [1] tests/test_benchmark_detect.py:468: Môi trường không có git hoặc không có .git/ (container ARM64) — bỏ qua
```

**`skipped`, không phải `error`, ở cả hai biến thể.** Biến thể B đặc biệt có giá trị: nó chứng minh
vế `shutil.which("git")` tự nó đủ để chặn, chứ không phải guard chỉ tình cờ đúng nhờ thiếu `.git/`.

Trước khi sửa, ca này ném `FileNotFoundError` không bọc và làm **đỏ** bộ test trên container.
Khoản nợ kiểm chứng của vòng 1 đến đây đóng lại bằng bằng chứng thật.

---

## 4. Kết luận về `EXE002` — chuyện toàn kho, KHÔNG thuộc `P2-03`

### 4.1. Số liệu

```
$ python -m ruff check . --statistics
29    EXE002    shebang-missing-executable-file
Found 29 errors.

$ python -m ruff check . --ignore EXE002
All checks passed!
```

| Đại lượng | Giá trị |
|---|---|
| Tổng số lỗi `ruff check .` trong container | **29** |
| Trong đó là `EXE002` | **29 / 29 — 100 %** |
| Lỗi thuộc mã khác `EXE002` | **0** |
| Số **tệp** dính `EXE002` | **29** |
| Tổng số tệp `.py` trong kho | **29** |

**29/29 tệp — tức là mọi tệp `.py` của kho, không sót tệp nào.** Danh sách gồm cả những tệp đã qua
review và gộp từ lâu, không liên quan gì tới `P2-03`:

```
src/common/config.py · src/common/exceptions.py · src/common/logging.py · src/common/types.py
src/capture/{base,factory,mock_camera,opencv_camera}.py · src/detector/yolo_face.py
src/preprocess/align.py · scripts/{collect_faces,download_lfw,export_detector}.py
tests/{test_align,test_capture,test_collect_faces,test_common,test_download_lfw,...}.py
```

### 4.2. Nguyên nhân — quyền thực thi, không phải mã nguồn

```
-rwxr-xr-x 1 root root 22596 /app/scripts/benchmark_detect.py
-rwxr-xr-x 1 root root  3866 /app/src/common/config.py      <- tệp P0-01, gộp từ 07/08
```

Windows **không có bit thực thi POSIX**. Khi `COPY . .` đưa mã vào ảnh Linux, Docker gán 0755;
khi gắn thư mục thì lớp mount gán 0777. Cả hai đều khiến mọi `.py` "là tệp thực thi", và `ruff`
báo `EXE002` vì không tệp nào có dòng `#!`. Trên host Windows `ruff` không thấy bit đó nên sạch.

**Đây là hiện tượng của nền tảng, không phải khuyết tật của mã.**

### 4.3. Bác bỏ giả thuyết lệch phiên bản `ruff` (R18)

| | Host | Container |
|---|---|---|
| `ruff --version` | **0.16.1** | **0.16.1** |
| `black --version` | 24.4.2 | 24.4.2 |
| `pytest --version` | 9.1.1 | 9.1.1 |

`requirements-dev.txt` ghim cứng cả ba, đúng R18:

```
pytest==9.1.1
black==24.4.2
ruff==0.16.1
```

Vậy **không có chuyện mỗi máy chạy một phiên bản lint khác nhau**. Hai bên cùng `ruff 0.16.1`,
cùng mã nguồn, khác nhau **chỉ ở quyền tệp**. Mối lo tái lập nêu ra là **không có cơ sở** — R18
đang được tuân thủ.

### 4.4. Phân loại

🔵 **GY-10 — `EXE002` toàn kho: mở mã việc riêng, không tính vào `P2-03`.**
Trải đều 29/29 tệp `.py`, gồm tệp của `P0-01`, `P1-02`, `P1-03`, `P1-04`, `P2-01`, `P2-02`.
Nếu tính vào `P2-03` thì phải trả lại cả sáu mã việc đã gộp — vô lý. Ba hướng xử lý, chọn một:

| Hướng | Việc | Đánh giá |
|---|---|---|
| (a) Tắt luật | thêm `EXE002` vào `lint.ignore` trong `pyproject.toml` | rẻ nhất, đúng bản chất: kho này không dùng bit thực thi để phân biệt script |
| (b) Sửa quyền khi build | `RUN chmod -R a-x $(find /app -name '*.py')` trong Dockerfile | sửa đúng gốc nhưng thêm một lớp ảnh |
| (c) Thêm shebang | thêm `#!/usr/bin/env python3` cho 29 tệp | sai hướng — phần lớn là module, không phải script chạy trực tiếp |

Khuyến nghị (a) hoặc (b), thuộc mã việc hạ tầng, **không** thuộc `P2-03`.

---

## 5. `pytest -q` toàn kho trong container — trả nợ cho cả ba mã việc gần đây

```
8 failed, 256 passed, 24 skipped, 8 warnings, 2 errors in 33.08s
```

Bảng theo từng tệp:

| Tệp test | Mã việc | Kết quả trong container | |
|---|---|---|---|
| `test_common.py` | P0-01 | 26 passed | ✅ |
| `test_capture.py` | P0-0x | 26 passed | ✅ |
| `test_collect_faces.py` | P1-02 | 34 passed | ✅ |
| `test_download_lfw.py` | P1-03 | 32 passed | ✅ |
| `test_align.py` | P1-04 | 37 passed | ✅ |
| `test_export_detector.py` | **P2-01** | **8 failed, 35 passed, 2 errors** | ❌ |
| `test_yolo_face.py` | P2-02 | 20 passed, 23 skipped | ✅ |
| **`test_benchmark_detect.py`** | **P2-03** | **46 passed, 1 skipped** | ✅ |

**Số ca hỏng thuộc `P2-03`: 0.** Đếm trực tiếp:

```
$ pytest -q | grep -E '^(FAILED|ERROR)' | grep -c 'test_benchmark_detect'
0
```

Toàn bộ 10 ca hỏng (8 failed + 2 errors) nằm trong **`tests/test_export_detector.py` — mã việc
`P2-01`**. `P2-03` không làm đổ mã việc nào khác.

### 5.1. 🔵 GY-11 — `P2-01` chưa chạy được trên container: mở mã việc riêng

Nguyên nhân, lấy từ trace:

```
E   src.common.exceptions.LoiMoHinh: Không tìm thấy trọng số nguồn: models/yolov8n-face.pt
```

`.dockerignore` loại `models/` khỏi build context, và ảnh cũng không cài `ultralytics`
(`Dockerfile.arm64` chỉ lấy `pytest|black|ruff` từ `requirements-dev.txt`). Tám ca của `P2-01`
gọi thẳng `export_mot_kich_thuoc(...)` mà **không có chốt bỏ qua** khi thiếu trọng số.

Đối chiếu cách `P2-02` làm — cùng hoàn cảnh thiếu `models/` nhưng **skip sạch có thông báo**:

```
SKIPPED [23] tests/test_yolo_face.py: chưa có models/yolov8n-face-320.onnx, chạy scripts/export_detector.py trước
```

`P2-03` cũng theo mẫu này (skip ca cần `git`). Vậy `P2-01` là mã việc **duy nhất** còn thiếu chốt.
Cách sửa gợi ý cho mã việc mới, một dòng đầu mỗi ca hoặc một fixture chung:

```python
if not _DUONG_DAN_WEIGHTS_THAT.exists():
    pytest.skip("chưa có models/yolov8n-face.pt — bỏ qua trên container/máy chưa tải trọng số")
```

Kèm theo: `pytest.mark.slow` chưa được đăng ký (`PytestUnknownMarkWarning` × 5 trong tệp `P2-01`),
nên thêm `markers = ["slow: ..."]` vào `pyproject.toml` — gộp chung vào mã việc đó.

---

## 6. Phán quyết

**Vòng 2 ✅ ĐẠT — GIỮ NGUYÊN.** Không có gì trong đợt kiểm container làm lung lay phán quyết đó:

| Điều kiện | Trạng thái |
|---|---|
| `black --check` trong container | ✅ sạch |
| `ruff check` hai tệp `P2-03` | chỉ `EXE002`, dính **mọi** tệp `.py` của kho → ngoài phạm vi |
| `pytest` tệp `P2-03` trong container | ✅ 46 passed, 1 skipped |
| Ca cần `git` | ✅ **skip sạch**, không `error`, ở cả hai biến thể môi trường |
| `pytest -q` toàn kho | 0 ca hỏng thuộc `P2-03` |
| Cây làm việc | ✅ không tệp nào bị sửa; `sha256` hai tệp mã và cặp tệp `results/` giữ nguyên |

**Khoản nợ container (GY-9) đã trả xong. Mã việc sẵn sàng commit.**

Commit message giữ như vòng 2 (R29):

```
feat(scripts): thêm script đo hiệu năng khối phát hiện khuôn mặt theo ma trận cấu hình
```

Hai mục 🔵 mới sinh ra từ đợt này — **cả hai đều là mã việc riêng, không chặn `P2-03`**:

- **GY-10** — `EXE002` toàn kho (29/29 tệp): tắt luật trong `pyproject.toml` hoặc `chmod` khi build.
- **GY-11** — `P2-01` chưa chạy được trên container: thêm chốt `pytest.skip` khi thiếu
  `models/yolov8n-face.pt`, và đăng ký mark `slow`.

Đề nghị đưa cả hai vào nhật ký tuần cùng ghi chú vận hành Docker ở §1 (PowerShell, không dùng
`--platform` khi `docker run`) để lần sau khỏi mò lại.
