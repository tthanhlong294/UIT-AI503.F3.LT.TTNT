# P2-01-export-detector — Export YOLOv8n-face sang ONNX và kiểm chứng tương đương

> Mã việc: `P2-01-export-detector` · Bước **2.2** trong `CLAUDE.md` §5 Phase 2
> Nhánh: `feat/p2-01-export-detector` · Đặc tả viết ngày 17/08/2026

---

## 1. Mục tiêu

Chuyển trọng số `models/yolov8n-face.pt` (định dạng PyTorch) sang **ONNX** ở hai độ phân giải
320 và 640, rồi **chứng minh bằng số đo** rằng bản ONNX cho kết quả tương đương bản gốc trên
ảnh thật.

Vì sao cần bước này: Raspberry Pi 5 chỉ cài `onnxruntime`, **không có `torch` và `ultralytics`**
(xem `requirements.txt` — chỉ pin `onnxruntime==1.20.1`). Toàn bộ hệ thống chạy trên Pi phải
dùng ONNX. Bước export chạy **trên PC phát triển**, không chạy trên Pi.

Vì sao phải kiểm chứng tương đương: export là phép biến đổi có thể làm sai lệch âm thầm — sai
opset, sai chuẩn hoá đầu vào, hoặc mất nhánh xử lý điểm mốc đều cho ra một tệp `.onnx` **chạy
được** nhưng kết quả lệch. Không có phép so sánh định lượng thì lỗi này chỉ lộ ra ở Phase 3
dưới dạng độ chính xác thấp không rõ nguyên nhân.

---

## 2. Phạm vi file — danh sách trắng

Chỉ được tạo hoặc sửa **đúng ba** file:

| File | Trạng thái | Vai trò |
|---|---|---|
| `scripts/export_detector.py` | tạo mới | Script CLI |
| `tests/test_export_detector.py` | tạo mới | Bộ kiểm thử |
| `scripts/__init__.py` | đã có | Không cần sửa, chỉ để import chạy được |

**Tuyệt đối không sửa**: `configs/**`, `src/**`, `requirements.txt`, `CLAUDE.md`, `docs/**`,
bất kỳ file nào trong `.claude/**`.

Nếu thấy `configs/detect.yaml` thiếu tham số cần thiết → **dừng lại và báo trong phần Vướng mắc**,
không tự thêm key. Cấu hình do người viết đặc tả giữ (`CLAUDE.md` §2.9).

---

## 3. Dữ kiện đã kiểm chứng — dùng, đừng kiểm lại

Đo ngày 17/08/2026 trên máy phát triển. Đây là **tiền đề**, không phải thứ cần xác minh lại:

| Dữ kiện | Giá trị |
|---|---|
| `YOLO('models/yolov8n-face.pt').task` | `pose` |
| `.names` | `{0: 'face'}` — một lớp duy nhất |
| `kpt_shape` | `[5, 3]` — 5 điểm mốc, mỗi điểm `(x, y, visibility)` |
| `r.keypoints.xy` | hình dạng `(N, 5, 2)` |
| Thứ tự 5 điểm mốc | mắt trái · mắt phải · mũi · khoé miệng trái · khoé miệng phải |
| Tỉ lệ phát hiện trên LFW | 60/60 ảnh ngẫu nhiên (seed 42) |
| Phiên bản | `ultralytics 8.4.39`, `onnx 1.19.1`, `onnxruntime 1.20.1`, `torch 2.5.1` |

Thứ tự điểm mốc **trùng khớp** `reference_landmarks` trong `configs/preprocess.yaml`, nên
không cần hoán vị khi nối sang `align.can_chinh()`.

---

## 4. Tham số — đọc từ `configs/detect.yaml`, không hardcode (R16)

| Khoá | Kiểu | Dùng để |
|---|---|---|
| `export.weights_pt` | chuỗi | Đường dẫn trọng số nguồn |
| `export.kich_thuoc` | danh sách số nguyên | Các độ phân giải cần export |
| `export.opset` | số nguyên | Phiên bản opset ONNX |
| `export.batch` | số nguyên | Kích thước lô cố định |
| `export.simplify` | luận lý | Có chạy onnx-simplifier không |
| `export.out_dir` | chuỗi | Thư mục ghi tệp `.onnx` |
| `inference.conf_threshold` | số thực | Ngưỡng lọc khi so sánh |
| `inference.iou_threshold` | số thực | Ngưỡng NMS khi so sánh |

**Quy ước tên tệp ra**: `<out_dir>/yolov8n-face-<imgsz>.onnx`, ví dụ `models/yolov8n-face-320.onnx`.

---

## 5. Giao diện hàm

Chữ ký dưới đây là **bắt buộc** — bộ kiểm thử gọi trực tiếp vào từng hàm.

```python
def doc_cau_hinh(cfg: dict) -> dict:
    """Kiểm tra và trích các tham số export từ cấu hình.

    Raises:
        LoiCauHinh: thiếu key bắt buộc, hoặc giá trị sai kiểu / ngoài miền hợp lệ.
    """

def export_mot_kich_thuoc(
    weights: Path, imgsz: int, opset: int, batch: int,
    simplify: bool, out_dir: Path, dry_run: bool = False,
) -> Path:
    """Export trọng số .pt sang .onnx ở một độ phân giải.

    Returns:
        Đường dẫn tệp .onnx đã tạo. Với dry_run trả về đường dẫn dự kiến, không tạo tệp.

    Raises:
        LoiMoHinh: không tìm thấy trọng số nguồn, hoặc export thất bại.
    """

def so_sanh_mot_anh(
    khung_pt: np.ndarray, diem_pt: np.ndarray,
    khung_onnx: np.ndarray, diem_onnx: np.ndarray,
    iou_toi_thieu: float, sai_so_diem_moc_toi_da: float,
) -> dict:
    """So sánh kết quả của hai mô hình trên CÙNG một ảnh.

    Nhận mảng NumPy thuần, KHÔNG nhận đối tượng `Results` của ultralytics — nhờ vậy
    ca kiểm thử dựng được đầu vào mà không cần nạp mô hình thật.

    Args:
        khung_pt: Khung bao từ bản .pt, hình dạng (N, 4), thứ tự (x1, y1, x2, y2),
            đã sắp xếp theo độ tin cậy giảm dần.
        diem_pt: Điểm mốc từ bản .pt, hình dạng (N, 5, 2).
        khung_onnx: Khung bao từ bản .onnx, hình dạng (M, 4).
        diem_onnx: Điểm mốc từ bản .onnx, hình dạng (M, 5, 2).
        iou_toi_thieu: Ngưỡng IoU tối thiểu để một cặp khung được coi là khớp.
        sai_so_diem_moc_toi_da: Ngưỡng sai số điểm mốc, đơn vị pixel.

    Returns:
        Từ điển gồm các khoá `so_mat_pt`, `so_mat_onnx`, `khop_so_mat`,
        `iou_min`, `sai_so_diem_moc_max`, `dat`.
        Khi lệch số mặt, `iou_min` và `sai_so_diem_moc_max` nhận giá trị `None`.

        `dat` là `True` khi và chỉ khi cả ba điều kiện cùng đúng:
        `khop_so_mat`, `iou_min >= iou_toi_thieu`, và
        `sai_so_diem_moc_max <= sai_so_diem_moc_toi_da`.
        Trường hợp cả hai bên đều không có mặt nào: `dat` là `True`.

    Raises:
        ValueError: mảng sai hình dạng, hoặc số khung không khớp số bộ điểm mốc.
    """

def kiem_chung_tuong_duong(
    weights_pt: Path, onnx_path: Path, danh_sach_anh: list[Path],
    imgsz: int, conf: float, iou: float, sai_so_diem_moc_toi_da: float,
) -> dict:
    """Chạy cả hai mô hình trên cùng tập ảnh và tổng hợp số đo.

    Returns:
        Từ điển tổng hợp, tối thiểu gồm: `n_anh`, `n_khop_so_mat`, `iou_trung_binh`,
        `iou_nho_nhat`, `sai_so_diem_moc_trung_binh`, `sai_so_diem_moc_lon_nhat`, `dat`.
    """

def ghi_ket_qua(duong_dan: Path, ban_ghi: dict) -> None:
    """Ghi số đo ra tệp JSON kèm tệp .meta.json theo R17.

    Raises:
        LoiCauHinh: `ban_ghi` thiếu khoá bắt buộc.
    """

def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 nếu thành công, 1 nếu thất bại."""
```

**Ngoại lệ dùng đúng loại** — `src/common/exceptions.py` đã có sẵn:
`LoiCauHinh` cho lỗi **cấu hình**, `LoiMoHinh` cho lỗi **mô hình / trọng số**.
Không ném `Exception` trần, không ném `TypeError` cho lỗi cấu hình.

---

## 6. Giao diện dòng lệnh

```
python scripts/export_detector.py [--config CONFIG] [--anh-dir ANH_DIR]
                                  [--so-anh SO_ANH] [--seed SEED] [--dry-run]
```

| Cờ | Mặc định | Ý nghĩa |
|---|---|---|
| `--config` | `configs/detect.yaml` | Đường dẫn cấu hình |
| `--anh-dir` | `data/impostor/lfw_original` | Thư mục ảnh dùng để kiểm chứng |
| `--so-anh` | `50` | Số ảnh lấy mẫu để so sánh |
| `--seed` | `42` | Seed chọn mẫu ảnh, để tái lập (R15) |
| `--dry-run` | tắt | Chỉ in kế hoạch, **không ghi tệp nào** |

---

## 7. Cách kiểm chứng tương đương — thiết kế bắt buộc

**Dùng `ultralytics` để chạy CẢ HAI mô hình.** `YOLO('duong/dan.onnx')` nạp và chạy được tệp
ONNX với cùng API. Nhờ vậy script **không phải tự cài đặt phần giải mã tensor** — phần đó
thuộc mã việc sau (`P2-02`, module `src/detector/yolo_face.py` chạy `onnxruntime` thuần).

Viết lại phần giải mã ở đây sẽ trùng lặp với `P2-02` và tạo hai bản cài đặt có thể lệch nhau.

**So sánh công bằng về độ phân giải**: bản ONNX xuất ở `imgsz=320` phải được đối chiếu với bản
`.pt` chạy **cũng ở `imgsz=320`**, không phải mặc định 640. So lệch độ phân giải sẽ đo ra khác
biệt của độ phân giải chứ không phải khác biệt của phép export.

**Ba đại lượng đo**:

1. **Khớp số mặt** — hai mô hình phát hiện cùng số khuôn mặt trên cùng ảnh.
2. **IoU khung bao** — ghép từng khung theo thứ tự độ tin cậy giảm dần, tính IoU từng cặp.
3. **Sai số điểm mốc** — khoảng cách Euclid (pixel) giữa các điểm mốc tương ứng.

**Ngưỡng đạt** (áp cho từng độ phân giải):

| Đại lượng | Ngưỡng |
|---|---|
| Tỉ lệ ảnh khớp số mặt | ≥ 95 % |
| IoU trung bình | ≥ 0,90 |
| Sai số điểm mốc trung bình | ≤ 5,0 px |

Ngưỡng đặt lỏng có chủ ý: mục tiêu là **bắt lỗi export hỏng**, không phải đòi khớp từng bit.
Sai khác nhỏ do thứ tự phép toán dấu phẩy động là bình thường. Nếu số đo thực tế tốt hơn
nhiều thì **báo cáo số thật**, không sửa ngưỡng (R7).

**Ghi số đo ra tệp** (R17) — bắt buộc, không chỉ in ra màn hình:

```
results/export_detector_<YYYYMMDD_HHMM>.json
results/export_detector_<YYYYMMDD_HHMM>.meta.json
```

Tệp `.meta.json` chứa: commit hash, nội dung cấu hình đã dùng, phiên bản `ultralytics` /
`onnx` / `onnxruntime` / `torch`, tên máy và hệ điều hành, thời điểm chạy, seed.

---

## 8. Bảng tiêu chí nghiệm thu

Mỗi dòng là **một ca kiểm thử** trong `tests/test_export_detector.py`, đặt tên `test_dong<nn>`.
Cột "Assert tối thiểu" là **biểu thức chạy được**, không phải mô tả.

### 8.1. Đọc và kiểm tra cấu hình

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Cấu hình hợp lệ đọc được đủ 8 khoá | `set(doc_cau_hinh(cfg_hop_le)) >= {"weights_pt","kich_thuoc","opset","batch","simplify","out_dir","conf_threshold","iou_threshold"}` |
| 02 | Thiếu `export` → `LoiCauHinh` | `pytest.raises(LoiCauHinh, match="export")` với `cfg` bỏ hẳn khoá `export` |
| 03 | Thiếu `export.weights_pt` → `LoiCauHinh` | `pytest.raises(LoiCauHinh, match="weights_pt")` |
| 04 | Thiếu `export.kich_thuoc` → `LoiCauHinh` | `pytest.raises(LoiCauHinh, match="kich_thuoc")` |
| 05 | Thiếu `export.opset` → `LoiCauHinh` | `pytest.raises(LoiCauHinh, match="opset")` |
| 06 | Thiếu `inference.conf_threshold` → `LoiCauHinh` | `pytest.raises(LoiCauHinh, match="conf_threshold")` |
| 07 | `kich_thuoc` rỗng → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` với `kich_thuoc: []` |
| 08 | `kich_thuoc` chứa phần tử không phải số nguyên dương → `LoiCauHinh` | Duyệt **đích danh bốn biến thể**: `[320, "abc"]`, `[320, -1]`, `[320, 0]`, `[320, 1.5]` — mỗi biến thể ném `LoiCauHinh` và thông báo chứa `kich_thuoc` |
| 09 | `opset` sai kiểu hoặc ngoài miền → `LoiCauHinh` | Duyệt **đích danh ba biến thể**: `"12"`, `-1`, `0` |
| 10 | `conf_threshold` ngoài `[0, 1]` → `LoiCauHinh` | Duyệt **đích danh ba biến thể**: `-0.1`, `1.5`, `"0.5"` |
| 11 | `iou_threshold` ngoài `[0, 1]` → `LoiCauHinh` | Duyệt **đích danh ba biến thể**: `-0.1`, `1.5`, `"0.45"` |
| 12 | **Mọi lỗi cấu hình đều là `LoiCauHinh`, không phải `ValueError`/`TypeError`** | Gom danh sách cấu hình hỏng phủ đủ **năm khoá**: `weights_pt`, `kich_thuoc`, `opset`, `conf_threshold`, `iou_threshold` — mỗi khoá ≥ 2 biến thể; assert `pytest.raises(LoiCauHinh)` cho từng trường hợp, và thông báo lỗi in ra giá trị gây lỗi |

### 8.2. Export

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 13 | Trọng số nguồn không tồn tại → `LoiMoHinh` | `pytest.raises(LoiMoHinh, match="")` với `weights=Path("khong/ton/tai.pt")` |
| 14 | Tên tệp ra đúng quy ước | `export_mot_kich_thuoc(..., imgsz=320, dry_run=True).name == "yolov8n-face-320.onnx"` |
| 15 | `dry_run=True` **không tạo tệp nào** | Chụp `set(out_dir.rglob("*"))` trước và sau; assert hai tập bằng nhau |
| 16 | Export thật tạo ra tệp `.onnx` đọc được | `onnx.load(str(p))` không ném lỗi; `p.stat().st_size > 0` |
| 17 | Tệp ONNX có đúng **một** đầu vào, hình dạng `(batch, 3, imgsz, imgsz)` | Nạp bằng `onnxruntime.InferenceSession`; assert `len(sess.get_inputs()) == 1` và `sess.get_inputs()[0].shape[1:] == [3, imgsz, imgsz]` |
| 18 | Export ở 320 và 640 cho **hai tệp khác nhau**, đều tồn tại | `p320 != p640 and p320.exists() and p640.exists()` |
| 19 | Export lần hai **ghi đè** tệp cũ, không ném lỗi | Gọi hai lần liên tiếp; lần hai trả về cùng đường dẫn và không ném ngoại lệ |

> Dòng 16–19 cần chạy export thật (chậm). Đánh dấu `@pytest.mark.slow` và bảo đảm
> `pytest -m "not slow"` vẫn chạy được toàn bộ phần còn lại.

### 8.3. So sánh kết quả

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 20 | Hai kết quả **giống hệt** → `iou_min == 1.0`, sai số điểm mốc `== 0.0`, `dat is True` | Truyền cùng một mảng cho cả hai phía; assert cả ba giá trị |
| 21 | Lệch số mặt → `khop_so_mat is False`, `dat is False`, và hai số đo là `None` | `khung_pt` có 1 hàng, `khung_onnx` có 2 hàng; assert thêm `kq["iou_min"] is None` |
| 22 | Khung bao lệch nhẹ vẫn đạt | `(0,0,100,100)` và `(2,2,102,102)` → IoU = 9604/10396 ≈ 0,9238; với `iou_toi_thieu=0.90` assert `dat is True` |
| 23 | Khung bao lệch nhiều → không đạt | `(0,0,10,10)` và `(50,50,60,60)`, IoU = 0; với `iou_toi_thieu=0.90` assert `dat is False` |
| 23b | **Cùng dữ liệu, ngưỡng IoU khác nhau cho kết quả khác nhau** | Dùng lại cặp khung của dòng 22: `iou_toi_thieu=0.90` ⇒ `dat is True`; `iou_toi_thieu=0.95` ⇒ `dat is False`. Bảo đảm ngưỡng thật sự được dùng chứ không bị bỏ qua |
| 24 | Điểm mốc lệch quá ngưỡng → không đạt | Khung bao giống hệt nhau, dời **một** điểm mốc đi 20 px, `sai_so_diem_moc_toi_da=5.0`; assert `dat is False` và `kq["sai_so_diem_moc_max"] == pytest.approx(20.0)` |
| 25 | Cả hai bên **không phát hiện mặt nào** → coi là khớp | Hai mảng rỗng hình dạng `(0, 4)`; assert `khop_so_mat is True` và `dat is True` |
| 25b | Số khung không khớp số bộ điểm mốc → `ValueError` | `khung_pt` 2 hàng nhưng `diem_pt` chỉ 1 bộ; `pytest.raises(ValueError)` |
| 26 | IoU tính đúng trên trường hợp biết trước | Hai khung `(0,0,10,10)` và `(5,5,15,15)`: giao 25, hợp 175 ⇒ `abs(iou - 25/175) < 1e-9` |
| 27 | `kiem_chung_tuong_duong` tổng hợp đúng số ảnh | `kq["n_anh"] == len(danh_sach_anh)` |
| 28 | Tổng hợp có đủ **bảy** khoá bắt buộc | `set(kq) >= {"n_anh","n_khop_so_mat","iou_trung_binh","iou_nho_nhat","sai_so_diem_moc_trung_binh","sai_so_diem_moc_lon_nhat","dat"}` |
| 29 | Danh sách ảnh rỗng → `LoiCauHinh`, **không** chia cho 0 | `pytest.raises(LoiCauHinh)` với `danh_sach_anh=[]` |

### 8.4. Ghi kết quả

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 30 | `ghi_ket_qua` tạo **cả hai** tệp `.json` và `.meta.json` | `p.exists() and p.with_suffix(".meta.json").exists()` |
| 31 | Tệp JSON đọc lại được và giữ nguyên số liệu | `json.loads(p.read_text(encoding="utf-8"))["iou_trung_binh"] == ban_ghi["iou_trung_binh"]` |
| 32 | `.meta.json` chứa đủ **năm** trường bắt buộc | `set(meta) >= {"commit","cau_hinh","phien_ban","thiet_bi","thoi_diem"}` |
| 33 | `ban_ghi` thiếu khoá bắt buộc → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` với `ban_ghi={}` |
| 34 | `ban_ghi` **đủ khoá** → ghi thành công, không ném lỗi | Cặp đối chứng của dòng 33 — bảo đảm hàm không phải lúc nào cũng ném lỗi |
| 35 | Tên tệp đúng khuôn `export_detector_<YYYYMMDD_HHMM>` | `re.fullmatch(r"export_detector_\d{8}_\d{4}\.json", p.name)` |

### 8.5. Luồng chính

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 36 | `--dry-run` **không ghi bất kỳ tệp nào** vào `models/` lẫn `results/` | Chụp `rglob("*")` của cả hai thư mục trước và sau; assert bằng nhau; `main([...,"--dry-run"]) == 0` |
| 37 | Thư mục ảnh **không tồn tại** → trả về `1`, thông báo nhắc chạy `download_lfw.py` | `main(["--anh-dir","khong/ton/tai"]) == 1` **và** `"download_lfw" in capsys.readouterr().out` |
| 38 | Thư mục ảnh **tồn tại nhưng rỗng** → trả về `1`, thông báo **khác** dòng 37 | Dựng thư mục rỗng bằng `tmp_path`; `main([...]) == 1` **và** thông báo chứa từ `rỗng` hoặc `không có ảnh`. Hai dòng 37/38 phải phân biệt được qua thông báo, nếu không thì một nhánh lỗi chung cũng qua được cả hai |
| 39 | Cùng `--seed` chọn **cùng** tập ảnh | Gọi hàm chọn mẫu hai lần với seed 42; assert hai danh sách bằng nhau |
| 40 | Khác `--seed` chọn **khác** tập ảnh | Seed 42 và seed 7 trên tập ≥ 100 ảnh; assert hai danh sách khác nhau |
| 41 | Cấu hình hỏng → `main` trả về `1`, **không** để ngoại lệ lọt ra ngoài | `main(["--config", duong_dan_cfg_hong]) == 1` — không dùng `pytest.raises` |
| 42 | Không tìm thấy tệp cấu hình → trả về `1` | `main(["--config","khong/ton/tai.yaml"]) == 1` |

---

## 9. Lệnh kiểm tra bắt buộc — chạy đủ trước khi báo xong

```bash
black --line-length 100 --check scripts/export_detector.py tests/test_export_detector.py
```

```bash
ruff check scripts/export_detector.py tests/test_export_detector.py
```

```bash
python -m pytest tests/test_export_detector.py -v
```

```bash
git status --short --untracked-files=all
```

Lệnh cuối phải cho thấy **đúng hai** tệp mã nguồn mới: `scripts/export_detector.py` và
`tests/test_export_detector.py`.

Ngoài ra được phép xuất hiện **các tệp kết quả** `results/export_detector_*.json` và
`results/export_detector_*.meta.json` do chính lần chạy thật sinh ra. Chúng **không** bị
gitignore — `.gitignore` chỉ chặn ảnh và video trong `results/`, còn JSON thì giữ lại, vì R6
đòi mọi con số trong báo cáo phải truy được về một tệp trong `results/`. Các tệp này sẽ được
commit cùng mã việc.

Tệp `.onnx` sinh ra trong `models/` thì **không** xuất hiện ở đây vì `models/*` đã bị gitignore.

Bất kỳ tệp nào khác hai nhóm trên là vi phạm phạm vi.

> Nếu chạy thật nhiều lần và sinh ra nhiều bộ tệp kết quả trùng nội dung, **giữ lại một bộ**
> và xoá phần dư — mỗi lần chạy có ý nghĩa mới một tệp, không phải mỗi lần bấm chạy.

### Quét mẫu vi phạm — cả bốn lệnh phải cho kết quả rỗng

```bash
grep -n "print(" scripts/export_detector.py
```

```bash
grep -nE "0\.5|0\.45|320|640|\b12\b" scripts/export_detector.py
```

```bash
grep -n "except Exception" scripts/export_detector.py
```

```bash
grep -nE "raise (ValueError|TypeError)" scripts/export_detector.py
```

Ghi chú cho lệnh thứ nhất: `print()` **được phép** trong hàm in bảng kết quả ra màn hình cho
người dùng — đó là giao diện CLI, không phải log. Nếu có `print()` hợp lệ, hãy nêu rõ dòng nào
và vì sao trong báo cáo; phần còn lại dùng `logging` (R23).

Ghi chú cho lệnh thứ hai: mục đích là bắt **giá trị hardcode**. Số xuất hiện trong chuỗi tài
liệu, tên tệp mẫu, hoặc **trong ca kiểm thử** thì không tính. Nếu lệnh có kết quả, giải trình
từng dòng.

### Kiểm đột biến bắt buộc

Chạy **ba** phép, mỗi phép: sửa → chạy `pytest` → ghi lại ca nào đỏ → khôi phục → đối chiếu
`sha256` để chắc chắn tệp về nguyên trạng. Dùng `newline=""` khi đọc và ghi tệp để tránh
lệch CRLF/LF.

| # | Phép đột biến | Ca test **phải** đỏ |
|---|---|---|
| ĐB1 | Bỏ toàn bộ khối kiểm `conf_threshold` trong `doc_cau_hinh` | dòng 10 **và** dòng 12 |
| ĐB2 | Trong `so_sanh_mot_anh`, luôn gán `dat = True` | dòng 21, 23, 23b, 24 |
| ĐB3 | Trong `kiem_chung_tuong_duong`, bỏ nhánh chặn danh sách ảnh rỗng | dòng 29 |
| ĐB4 | Trong `so_sanh_mot_anh`, bỏ qua tham số `iou_toi_thieu` (coi như luôn đạt phần IoU) | dòng 23 **và** dòng 23b |

Nếu ĐB1 **không** làm đỏ dòng 12, nghĩa là dòng 12 chưa thật sự phủ đủ năm khoá — **sửa ca
test dòng 12 trước**, đừng báo xong.

---

## 10. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` dài dòng 100, `ruff` sạch (R19).
- Type hints cho mọi hàm public; docstring tiếng Việt kiểu Google (R20).
- Dùng `logging` qua `src.common.logging.lay_logger`, không `print()` trừ phần in bảng CLI (R23).
- Đọc cấu hình qua `src.common.config.nap_cau_hinh` và `lay_gia_tri` — **không** tự mở YAML.
  Ràng buộc này áp cho **mã trong `scripts/`**. Ca kiểm thử vẫn được phép ghi tệp YAML tạm
  vào `tmp_path` để dựng cấu hình hỏng cho các dòng 41–42 — đó là dữ liệu thử, không phải
  đường đọc cấu hình của sản phẩm.
- `doc_cau_hinh(cfg)` nhận **từ điển Python**, không nhận đường dẫn. Nhờ vậy phần lớn ca kiểm
  thử cấu hình (dòng 01–12) dựng đầu vào trực tiếp bằng `dict`, không cần chạm tới đĩa.
- Không thêm phụ thuộc mới vào `requirements.txt`. `ultralytics`, `onnx`, `torch` **đã có sẵn**
  trên máy phát triển nhưng **cố ý không nằm** trong `requirements.txt` vì Pi 5 không cần chúng.
  Script này chỉ chạy trên PC — hãy ghi rõ điều đó trong docstring đầu file.
- Bộ kiểm thử **không được** đòi hỏi mạng. Ca cần mô hình thật thì đánh dấu `@pytest.mark.slow`.
- Mọi ca test phải chạy được trên Windows (đường dẫn dùng `pathlib`, không nối chuỗi bằng `/`).

---

## 11. Báo cáo khi xong

Ghi theo mẫu §12 của [`docs/quy-tac-cai-dat.md`](../quy-tac-cai-dat.md), tối thiểu gồm:

1. Kết quả bốn lệnh máy ở §9 (dán nguyên văn dòng tổng kết).
2. Kết quả bốn lệnh `grep`, giải trình nếu có dòng nào không rỗng.
3. Kết quả ba phép đột biến: ca nào đỏ, `sha256` trước/sau có khớp không.
4. **Số đo tương đương thực tế** cho cả 320 và 640: tỉ lệ khớp số mặt, IoU trung bình và nhỏ
   nhất, sai số điểm mốc trung bình và lớn nhất. Kèm đường dẫn tệp trong `results/`.
5. Vướng mắc: chỗ nào trong đặc tả này mơ hồ, thiếu, hoặc mâu thuẫn.

**Không commit.** Để nguyên cây làm việc cho người review.
