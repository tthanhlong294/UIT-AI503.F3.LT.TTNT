# P2-04-export-ncnn — Export YOLOv8n-face sang NCNN và kiểm chứng tương đương

> Mã việc: `P2-04-export-ncnn` · Phần còn lại của bước **2.2** trong `CLAUDE.md` §5 Phase 2
> Nhánh: `feat/p2-04-export-ncnn` · Đặc tả viết ngày 27/08/2026

---

## 1. Mục tiêu

Chuyển `models/yolov8n-face.pt` sang định dạng **NCNN** ở hai độ phân giải 320 và 640, rồi
**chứng minh bằng số đo** rằng bản NCNN cho kết quả tương đương bản gốc trên ảnh thật — đúng ba
đại lượng và đúng phương pháp đã dùng cho bản ONNX ở `P2-01`.

Vì sao cần: bước 2.6 quy định ma trận đo `{ONNX, NCNN} × {320, 640} × {1, 2, 4 luồng}`. Hiện chỉ có
nửa ONNX. Thiếu nửa NCNN thì không kết luận được bộ suy luận nào phù hợp với Raspberry Pi 5, và
Chương 2 §2.6.3 của báo cáo còn treo dòng `[CHƯA VIẾT — CHẶN VÌ CHƯA ĐO]`.

Vì sao phải kiểm chứng thay vì export xong là tin: đường NCNN đi qua **hai** phép biến đổi liên tiếp
(PyTorch → PNNX → NCNN), nhiều hơn đường ONNX một chặng, và NCNN lưu trọng số ở fp16 theo mặc định.
Mỗi chặng là một chỗ có thể mất nhánh xử lý điểm mốc hoặc lệch chuẩn hoá đầu vào mà vẫn cho ra tệp
**chạy được**. Không đo thì sai lệch chỉ lộ ra ở Phase 3 dưới dạng độ chính xác thấp không rõ nguyên nhân.

**Mã việc này không sinh ra con số hiệu năng nào.** FPS của NCNN thuộc bước 2.6, đo trên Pi 5 thật.

---

## 2. Phạm vi file — danh sách trắng

Chỉ được tạo hoặc sửa **đúng ba** file:

| File | Trạng thái | Vai trò |
|---|---|---|
| `scripts/export_detector_ncnn.py` | tạo mới | Script CLI |
| `tests/test_export_detector_ncnn.py` | tạo mới | Bộ kiểm thử |
| `requirements-dev.txt` | sửa — **thêm đúng một dòng** | `ncnn==1.0.20260526` |

Dòng thêm vào `requirements-dev.txt` đặt ngay sau `ultralytics==8.4.39`, giữ nguyên mọi dòng khác.
Phiên bản này là bản đã cài trên máy phát triển ngày 27/08/2026 — **không** đổi sang `>=`, không
nâng, không thêm gói nào khác (R18).

> `deploy/Dockerfile.arm64:13` chỉ kéo `pytest|black|ruff` từ `requirements-dev.txt`, nên thay đổi
> này **không** làm image `faceid:arm64` khác đi. Không dựng lại image (R43).

**Tuyệt đối không sửa**: `configs/**`, `src/**`, `scripts/export_detector.py`, `requirements.txt`,
`models/README.md`, `CLAUDE.md`, `docs/**`, `.claude/**`.

Mã việc này **không** thêm khoá cấu hình nào: toàn bộ tham số đã có sẵn trong `configs/detect.yaml`
(xem §4). Nếu thấy thiếu tham số → **dừng và báo ở phần Vướng mắc**, không tự thêm key (R16).

---

## 3. Dữ kiện — mức độ chắc chắn khác nhau, đọc kỹ cột cuối

| Dữ kiện | Giá trị | Mức |
|---|---|---|
| `ncnn` trên máy phát triển | `1.0.20260526` | **đã kiểm** (`pip show ncnn`, 27/08/2026) |
| `ultralytics` | `8.4.39` | **đã kiểm** (`P2-01` §3) |
| `YOLO('models/yolov8n-face.pt').task` | `pose`, 1 lớp `face`, `kpt_shape=[5,3]` | **đã kiểm** (`P2-01` §3) |
| Thứ tự 5 điểm mốc | mắt trái · mắt phải · mũi · khoé miệng trái · khoé miệng phải | **đã kiểm** trên 60 ảnh LFW |
| Cấu trúc thư mục `ultralytics` sinh ra khi `format="ncnn"` | thư mục `<stem>_ncnn_model/` gồm `model.ncnn.param`, `model.ncnn.bin`, `metadata.yaml` | **CHƯA KIỂM — xác minh ở bước 1** |
| `YOLO(<thư mục ncnn>, task="pose")` có trả về `keypoints` | chưa rõ | **CHƯA KIỂM — xác minh ở bước 1** |
| `ultralytics` tải công cụ PNNX từ mạng ở lần export đầu | nhiều khả năng có | **CHƯA KIỂM** |

⚠️ Ba dòng cuối chưa ai kiểm chứng. **Bước đầu tiên của bạn là xác minh chúng** (§7.1), trước khi
viết dòng mã sản phẩm nào. Nếu thực tế khác bảng này — tên tệp khác, thiếu `metadata.yaml`, hoặc
bản NCNN **không trả về điểm mốc** — thì **dừng lại và báo**, đừng tự xoay xở. Trường hợp cuối làm
đổ toàn bộ thiết kế kiểm chứng ở §7.3 và cần sửa đặc tả, không phải sửa mã.

---

## 4. Tham số — đọc từ `configs/detect.yaml`, không hardcode (R16)

Dùng lại nguyên các khoá `P2-01` đã dùng. **Không thêm khoá mới.**

| Khoá | Dùng để |
|---|---|
| `export.weights_pt` | Đường dẫn trọng số nguồn |
| `export.kich_thuoc` | Các độ phân giải cần export — `[320, 640]` |
| `export.batch` | Kích thước lô cố định |
| `export.out_dir` | Thư mục ghi kết quả export |
| `inference.conf_threshold` | Ngưỡng độ tin cậy khi chạy suy luận để so sánh |
| `inference.iou_threshold` | Ngưỡng NMS khi chạy suy luận để so sánh |

`export.opset` và `export.simplify` **không áp dụng** cho NCNN — `doc_cau_hinh` vẫn đọc và kiểm
chúng (vì dùng chung hàm), nhưng script này không truyền chúng đi đâu. Ghi một dòng comment nêu rõ
điều đó tại chỗ gọi, để người đọc sau không tưởng là bỏ sót.

**Quy ước tên thư mục ra**: `<out_dir>/yolov8n-face-<imgsz>_ncnn_model/`
ví dụ `models/yolov8n-face-320_ncnn_model/`.

Giữ **nguyên vẹn** tên các tệp bên trong thư mục do `ultralytics` sinh ra — `ultralytics` đọc lại
`metadata.yaml` để biết `task` và `imgsz`, đổi tên tệp bên trong là làm hỏng đường nạp lại. Chỉ đổi
tên **thư mục**.

---

## 5. Giao diện hàm

Chữ ký dưới đây là **bắt buộc** — bộ kiểm thử gọi trực tiếp vào từng hàm.

### 5.1. Tái dùng từ `scripts/export_detector.py` — KHÔNG viết lại

Hai module cùng nằm trong gói `scripts/` (đã có `__init__.py`), import trực tiếp:

```python
from scripts.export_detector import (
    NGUONG_IOU_TOI_THIEU,
    NGUONG_SAI_SO_DIEM_MOC_TOI_DA_PX,
    NGUONG_TI_LE_KHOP_SO_MAT,
    _chon_mau_anh,
    _lay_git_commit_hash,
    _trich_khung_diem_moc,
    doc_cau_hinh,
    ghi_ket_qua,
    so_sanh_mot_anh,
)
```

Cấm viết lại bất kỳ hàm nào trong danh sách trên. `P2-01` §7 đã nêu lý do và lý do đó vẫn đúng ở
đây: hai bản cài đặt của cùng một phép so sánh sẽ lệch nhau, và khi lệch thì không ai biết bản nào
đúng. Ba hằng số ngưỡng cũng lấy nguyên — **cùng phép đo thì cùng thước đo**, có vậy bảng ONNX và
bảng NCNN mới đặt cạnh nhau được.

`ghi_ket_qua` đòi bản ghi có đủ tám khoá `n_anh`, `n_khop_so_mat`, `iou_trung_binh`, `iou_nho_nhat`,
`sai_so_diem_moc_trung_binh`, `sai_so_diem_moc_lon_nhat`, `dat`, `meta` — bản ghi của bạn phải có đủ.

### 5.2. Hàm mới

```python
def export_ncnn_mot_kich_thuoc(
    weights: Path, imgsz: int, batch: int, out_dir: Path, dry_run: bool = False,
) -> Path:
    """Export trọng số .pt sang NCNN ở một độ phân giải.

    Returns:
        Đường dẫn THƯ MỤC `<out_dir>/yolov8n-face-<imgsz>_ncnn_model`. Với dry_run trả về
        đường dẫn dự kiến, không tạo gì.

    Raises:
        LoiMoHinh: không tìm thấy trọng số nguồn, chưa cài gói `ncnn`, hoặc export thất bại.
    """

def kiem_tra_thu_muc_ncnn(thu_muc: Path) -> dict:
    """Kiểm thư mục NCNN có đủ ba tệp bắt buộc và không tệp nào rỗng.

    Returns:
        Từ điển gồm `param`, `bin`, `metadata` (đường dẫn từng tệp) và `tong_kich_thuoc_byte`.

    Raises:
        LoiMoHinh: thư mục không tồn tại, thiếu tệp bắt buộc, hoặc có tệp kích thước 0.
    """

def kiem_chung_tuong_duong_ncnn(
    weights_pt: Path, thu_muc_ncnn: Path, danh_sach_anh: list[Path],
    imgsz: int, conf: float, iou: float, sai_so_diem_moc_toi_da: float,
) -> dict:
    """Chạy bản .pt và bản NCNN trên cùng tập ảnh, tổng hợp số đo.

    Nạp bản NCNN BẮT BUỘC chỉ định `task="pose"` — cùng lý do đã ghi ở
    `kiem_chung_tuong_duong` của P2-01: đồ thị không mang theo tên lớp và `kpt_shape`,
    thiếu `task` thì ultralytics đoán thành 'detect' và bỏ hậu xử lý pose.

    Returns:
        Từ điển gồm bảy khoá như `kiem_chung_tuong_duong` của P2-01, cộng `thu_muc_ncnn`.

    Raises:
        LoiCauHinh: `danh_sach_anh` rỗng.
        LoiMoHinh: bản NCNN phát hiện được khuôn mặt nhưng KHÔNG trả về điểm mốc.
    """

def thu_thap_metadata_ncnn(cfg_tho: dict, seed: int) -> dict:
    """Gom metadata theo R17: commit, cấu hình, phiên bản thư viện, thiết bị, thời điểm, seed.

    Khác `_thu_thap_metadata` của P2-01 ở chỗ phần `phien_ban` phải có `ncnn`, và không
    cần `onnx`/`onnxruntime`.
    """

def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 nếu thành công, 1 nếu thất bại."""
```

**Ngoại lệ dùng đúng loại**: `LoiCauHinh` cho lỗi cấu hình, `LoiMoHinh` cho lỗi mô hình/trọng số
(`src/common/exceptions.py`). Không ném `Exception` trần, không ném `TypeError` cho lỗi cấu hình.

---

## 6. Giao diện dòng lệnh

```
python scripts/export_detector_ncnn.py [--config CONFIG] [--anh-dir ANH_DIR]
                                       [--so-anh SO_ANH] [--seed SEED] [--dry-run]
```

Giống hệt `P2-01` về tên cờ, giá trị mặc định và ý nghĩa: `--config configs/detect.yaml` ·
`--anh-dir data/impostor/lfw_original` · `--so-anh 50` · `--seed 42` · `--dry-run` tắt.

Giữ y nguyên để hai lượt export gọi được bằng cùng một thói quen, và để so sánh ONNX với NCNN
không lẫn khác biệt do lấy mẫu ảnh khác nhau — **cùng seed thì cùng tập ảnh** (`_chon_mau_anh`).

---

## 7. Thiết kế bắt buộc

### 7.1. Bước xác minh trước khi viết mã

Chạy đúng một lần, trong thư mục tạm **ngoài repo**, và **báo kết quả vào phần Vướng mắc**:

1. Chép `models/yolov8n-face.pt` sang thư mục tạm, gọi `YOLO(...).export(format="ncnn", imgsz=320)`
   ở đó — để lần chạy thăm dò không làm bẩn `models/`.
2. In cây tệp sinh ra kèm kích thước từng tệp, và nội dung `metadata.yaml`.
3. Nạp lại bằng `YOLO(<thư mục>, task="pose")`, chạy trên 3 ảnh LFW, in `boxes.xyxy` và
   `keypoints.xy` cạnh kết quả của bản `.pt`.

Ba dòng "CHƯA KIỂM" ở §3 phải được trả lời bằng đầu ra thật của bước này. **Khác bảng §3 → dừng, báo.**

### 7.2. Export

Dùng `ultralytics` để export, không gọi `pnnx` trực tiếp — cùng lý do với `P2-01` §7: phần chuyển
đổi và phần hậu xử lý phải đến từ một nguồn.

`ultralytics` đặt kết quả cạnh trọng số nguồn với tên `<stem>_ncnn_model`. Sau khi export xong,
**đổi tên thư mục** về đúng quy ước §4. Export lần hai phải ghi đè được thư mục cũ, không ném lỗi.

Gói `ncnn` chỉ được import **bên trong thân hàm**, không bao giờ ở mức module — cùng ràng buộc đã
áp cho `ultralytics`/`torch` ở `P2-01`: gói này không có trong `requirements.txt` nên **không tồn
tại trong container ARM64**, một dòng import ở đầu tệp làm `pytest` chết ngay khâu thu thập và kéo
đổ toàn bộ bộ kiểm thử của cả repo.

Thiếu gói `ncnn` → `LoiMoHinh` với thông báo nêu đúng lệnh khắc phục `pip install ncnn`.

### 7.3. Kiểm chứng tương đương

Ba đại lượng và ba ngưỡng **giống hệt** `P2-01` §7, lấy từ hằng số import về:

| Đại lượng | Ngưỡng |
|---|---|
| Tỉ lệ ảnh khớp số mặt | ≥ 95 % |
| IoU trung bình | ≥ 0,90 |
| Sai số điểm mốc trung bình | ≤ 5,0 px |

So sánh công bằng về độ phân giải: bản NCNN xuất ở `imgsz=320` phải đối chiếu với bản `.pt` chạy
**cũng ở 320**.

⚠️ **NCNN lưu trọng số ở fp16 theo mặc định, nên sai số dự kiến lớn hơn ONNX.** Nếu không đạt
ngưỡng: **báo cáo đúng số thật và dừng** (R7). Tuyệt đối không nới ngưỡng, không đổi sang so sánh
lỏng hơn, không lặng lẽ bật `half=False` rồi báo đạt — mọi thay đổi tham số export đều phải qua
sửa đặc tả. Một kết quả "không đạt" có số liệu kèm theo là **kết quả hợp lệ** của mã việc này.

⚠️ **Guard quan trọng nhất — thiếu điểm mốc phải làm hỏng phép đo, không được làm ngơ.**
Nếu bản NCNN phát hiện được khuôn mặt nhưng `keypoints` là `None` (hoặc mảng rỗng), `LoiMoHinh`
phải được ném ra. Không được thay bằng mảng 0 rồi tính tiếp: sai số điểm mốc khi đó sẽ là một con
số lớn trông như lỗi độ chính xác, che mất nguyên nhân thật là **đường NCNN không mang theo nhánh
pose**. Đây là chỗ hỏng đắt nhất của cả mã việc, vì `preprocess.py` và `align.py` đều ăn năm điểm
mốc từ khối phát hiện.

### 7.4. Ghi số đo ra tệp (R17)

```
results/export_ncnn_<YYYYMMDD_HHMM>.json
results/export_ncnn_<YYYYMMDD_HHMM>.meta.json
```

`.meta.json` chứa: `commit`, `cau_hinh`, `phien_ban` (có `ultralytics`, `torch`, `ncnn`, `numpy`),
`thiet_bi`, `thoi_diem`, `seed`.

---

## 8. Bảng tiêu chí nghiệm thu

Mỗi dòng là **một ca kiểm thử** trong `tests/test_export_detector_ncnn.py`, đặt tên `test_dong<nn>`.
Cột "Assert tối thiểu" là **biểu thức chạy được**.

### 8.1. Export

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Trọng số nguồn không tồn tại → `LoiMoHinh` | `pytest.raises(LoiMoHinh)` với `weights=Path("khong/ton/tai.pt")` |
| 02 | Tên thư mục ra đúng quy ước | `export_ncnn_mot_kich_thuoc(..., imgsz=320, dry_run=True).name == "yolov8n-face-320_ncnn_model"` |
| 03 | `dry_run=True` **không tạo gì** | Chụp `set(out_dir.rglob("*"))` trước và sau; assert hai tập bằng nhau |
| 04 | 320 và 640 cho **hai thư mục khác nhau** | `p320 != p640` (dùng `dry_run=True`, không cần export thật) |
| 05 | Export thật tạo thư mục có đủ ba tệp | `@pytest.mark.slow`; `kiem_tra_thu_muc_ncnn(p)` không ném lỗi |
| 06 | Export lần hai **ghi đè**, không ném lỗi | `@pytest.mark.slow`; gọi hai lần, lần hai trả về cùng đường dẫn |

### 8.2. Kiểm tra thư mục NCNN

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 07 | Thư mục không tồn tại → `LoiMoHinh` | `pytest.raises(LoiMoHinh)` với `tmp_path / "khong-co"` |
| 08 | Thiếu `model.ncnn.param` → `LoiMoHinh`, thông báo **nêu tên tệp thiếu** | Dựng thư mục giả trong `tmp_path` chỉ có `.bin` + `metadata.yaml`; `pytest.raises(LoiMoHinh, match="param")` |
| 09 | Thiếu `model.ncnn.bin` → `LoiMoHinh`, thông báo nêu tên tệp | `pytest.raises(LoiMoHinh, match="bin")` |
| 10 | Thiếu `metadata.yaml` → `LoiMoHinh`, thông báo nêu tên tệp | `pytest.raises(LoiMoHinh, match="metadata")` |
| 11 | Có đủ ba tệp nhưng **một tệp rỗng** → `LoiMoHinh` | Ghi `.bin` rỗng 0 byte; `pytest.raises(LoiMoHinh)` |
| 12 | Đủ ba tệp, không tệp nào rỗng → trả về đủ bốn khoá | Cặp đối chứng của dòng 08–11: `set(kq) >= {"param","bin","metadata","tong_kich_thuoc_byte"}` và `kq["tong_kich_thuoc_byte"] > 0` |

> Dòng 12 là **cặp đối chứng bắt buộc**: không có nó thì một hàm luôn ném `LoiMoHinh` cũng qua được
> cả bốn dòng trên.

### 8.3. Kiểm chứng tương đương

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 13 | Danh sách ảnh rỗng → `LoiCauHinh`, **không** chia cho 0 | `pytest.raises(LoiCauHinh)` với `danh_sach_anh=[]` |
| 14 | **Bản NCNN có khung bao nhưng không có điểm mốc → `LoiMoHinh`** | Giả lập `YOLO` bằng monkeypatch: kết quả NCNN có `boxes` 1 hàng, `keypoints is None`; `pytest.raises(LoiMoHinh)`, thông báo chứa `điểm mốc` |
| 15 | Cả hai bên đều không phát hiện mặt nào → **không** ném lỗi | Cùng cách giả lập, cả hai phía `boxes` rỗng; hàm chạy trót lọt, `kq["n_anh"] == 1` |
| 16 | Tổng hợp có đủ **tám** khoá | `set(kq) >= {"n_anh","n_khop_so_mat","iou_trung_binh","iou_nho_nhat","sai_so_diem_moc_trung_binh","sai_so_diem_moc_lon_nhat","dat","thu_muc_ncnn"}` |
| 17 | Hai mô hình cho kết quả **giống hệt** → `dat is True` | Giả lập cả hai phía trả cùng một mảng; assert `kq["dat"] is True` và `kq["iou_nho_nhat"] == 1.0` |
| 18 | Lệch số mặt trên **quá 5 % số ảnh** → `dat is False` | Giả lập 10 ảnh, 2 ảnh lệch số mặt; assert `kq["dat"] is False` |

### 8.4. Metadata và ghi kết quả

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 19 | `thu_thap_metadata_ncnn` có đủ **sáu** trường | `set(meta) >= {"commit","cau_hinh","phien_ban","thiet_bi","thoi_diem","seed"}` |
| 20 | Phần `phien_ban` **có khoá `ncnn`** | `"ncnn" in meta["phien_ban"]` |
| 21 | Tên tệp kết quả đúng khuôn | `re.fullmatch(r"export_ncnn_\d{8}_\d{4}\.json", p.name)` |
| 22 | Ghi ra **cả hai** tệp, đọc lại giữ nguyên số liệu | `p.exists() and p.with_suffix(".meta.json").exists()`; `json.loads(...)["iou_trung_binh"] == ban_ghi["iou_trung_binh"]` |

### 8.5. Luồng chính

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 23 | `--dry-run` **không ghi tệp nào** vào `models/` lẫn `results/` | Chụp `rglob("*")` cả hai thư mục trước/sau; assert bằng nhau; `main([...,"--dry-run"]) == 0` |
| 24 | Thư mục ảnh không tồn tại → trả về `1`, thông báo nhắc `download_lfw.py` | `main(["--anh-dir","khong/ton/tai"]) == 1` và `"download_lfw" in capsys.readouterr().out` |
| 25 | Thư mục ảnh tồn tại nhưng rỗng → trả về `1`, thông báo **khác** dòng 24 | Thông báo chứa `rỗng` hoặc `không có ảnh` |
| 26 | Cấu hình hỏng → `main` trả về `1`, không để ngoại lệ lọt ra | `main(["--config", cfg_hong]) == 1` — không dùng `pytest.raises` |
| 27 | Không tìm thấy tệp cấu hình → trả về `1` | `main(["--config","khong/ton/tai.yaml"]) == 1` |

⚠️ **Ràng buộc thu thập**: `python -m pytest tests/test_export_detector_ncnn.py -m "not slow"
--collect-only` phải chạy trót lọt **kể cả khi máy không có `ncnn`, `ultralytics`, `torch`**.
Import ba gói này chỉ được nằm trong thân hàm test cần chúng.

---

## 9. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

```bash
python -m black --check --line-length 100 scripts/export_detector_ncnn.py tests/test_export_detector_ncnn.py
```

```bash
python -m ruff check scripts/export_detector_ncnn.py tests/test_export_detector_ncnn.py
```

```bash
python -m pytest tests/test_export_detector_ncnn.py -v
```

```bash
python -m pytest -q
```

Lệnh trên là **toàn bộ** bộ kiểm thử của repo — mã việc này import từ `scripts/export_detector.py`
nên phải chắc không làm hỏng ca nào của `P2-01`.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q
```

Image đã có sẵn — **không** `docker build` (R43).

```bash
git status --short --untracked-files=all
```

Phải cho thấy đúng ba tệp của §2, cộng các tệp `results/export_ncnn_*.json` và `.meta.json` do
chính lần chạy thật sinh ra. Thư mục NCNN trong `models/` không xuất hiện vì `models/*` đã gitignore.
Bất kỳ tệp nào khác là vi phạm phạm vi.

### Quét mẫu vi phạm — cả bốn lệnh phải rỗng

```bash
grep -nE "^import ncnn|^import torch|^from ultralytics" scripts/export_detector_ncnn.py tests/test_export_detector_ncnn.py
```

```bash
grep -nE "0\.5|0\.45|320|640|0\.90|0\.95|5\.0" scripts/export_detector_ncnn.py
```

```bash
grep -n "except Exception" scripts/export_detector_ncnn.py
```

```bash
grep -nE "raise (ValueError|TypeError)" scripts/export_detector_ncnn.py
```

Lệnh thứ nhất bắt import ở mức module — có kết quả là lỗi chặn, xem §7.2.
Lệnh thứ hai bắt giá trị hardcode; số trong chuỗi tài liệu, tên tệp mẫu hoặc trong ca kiểm thử không
tính, nhưng phải giải trình từng dòng.

### Kiểm đột biến bắt buộc

Bốn phép. Mỗi phép: sao lưu ra `$env:TEMP` → sửa → `pytest` → khôi phục → đối chiếu `sha256`.
**Không dùng `git checkout` để khôi phục** — mã của bạn chưa commit, lệnh đó xoá sạch.

| # | Phép đột biến | Ca **phải** đỏ |
|---|---|---|
| ĐB1 | Trong `kiem_tra_thu_muc_ncnn`, bỏ kiểm sự tồn tại của `model.ncnn.param` | dòng 08 |
| ĐB2 | Trong `kiem_tra_thu_muc_ncnn`, bỏ kiểm tệp rỗng | dòng 11 |
| ĐB3 | Trong `kiem_chung_tuong_duong_ncnn`, thay nhánh thiếu điểm mốc bằng mảng 0 thay vì ném `LoiMoHinh` | dòng 14 |
| ĐB4 | Trong `kiem_chung_tuong_duong_ncnn`, luôn gán `dat = True` | dòng 18 |

ĐB3 là phép quan trọng nhất — nó canh đúng chỗ hỏng đắt nhất ở §7.3.

Phép nào **không** làm đỏ ca đã chỉ định → ca đó chưa thật sự canh chỗ cần canh. Sửa ca kiểm thử
trước, đừng báo xong. Ghi kết quả thật vào bảng báo cáo kể cả khi nó bác bỏ dự đoán.

---

## 10. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` dài dòng 100, `ruff` sạch (R19).
- Type hints cho mọi hàm public; docstring tiếng Việt kiểu Google (R20).
- `logging` qua `src.common.logging.lay_logger`; `print()` **chỉ** cho phần in bảng kết quả CLI (R23).
- Đọc cấu hình qua `src.common.config.nap_cau_hinh`, không tự mở YAML. Ca kiểm thử vẫn được ghi YAML
  tạm vào `tmp_path` để dựng cấu hình hỏng cho dòng 26–27.
- Thư viện được phép: thư viện chuẩn, `numpy`, `ultralytics`, `ncnn`, `torch`, và `src/**`,
  `scripts/export_detector.py` của dự án. **Không thêm gói nào khác.**
- Ba gói `ncnn`, `ultralytics`, `torch` chỉ import trong thân hàm (§7.2).
- Bộ kiểm thử **không được** đòi hỏi mạng. Ca cần export thật đánh dấu `@pytest.mark.slow`.
- Mọi ca test chạy được trên Windows — đường dẫn dùng `pathlib`.
- Script này chỉ chạy trên **PC phát triển**, không chạy trên Pi 5. Ghi rõ trong docstring đầu tệp.

---

## 11. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Backend NCNN trong `src/detector/`** — mã việc `P2-05`, và nó mới là thứ đưa `ncnn` vào
  `requirements.txt` bản chạy, kéo theo dựng lại image.
- **Đo hiệu năng NCNN** (FPS, độ trễ) — bước 2.6, cần Pi 5 thật.
- **Chốt cấu hình tối ưu cho `configs/detect.yaml`** — thuộc Cổng C Phase 2.
- **Cập nhật `models/README.md` bảng B3** — Claude làm sau khi có `sha256` và kích thước thật từ
  lượt chạy của bạn.
- Sửa `scripts/export_detector.py` dưới bất kỳ hình thức nào.

---

## 12. Báo cáo khi xong

Theo mẫu §12 của [`docs/quy-tac-cai-dat.md`](../quy-tac-cai-dat.md), tối thiểu gồm:

1. **Kết quả bước xác minh §7.1** — cây tệp thật, nội dung `metadata.yaml`, và câu trả lời dứt khoát
   cho câu hỏi *bản NCNN có trả về điểm mốc không*.
2. Kết quả sáu lệnh §9, dán nguyên văn dòng tổng kết.
3. Kết quả bốn lệnh `grep`, giải trình dòng nào không rỗng.
4. Bảng bốn phép đột biến: ca dự đoán đỏ · ca thật sự đỏ · `sha256` khôi phục có khớp không.
5. **Số đo tương đương thật** cho cả 320 và 640: tỉ lệ khớp số mặt, IoU trung bình và nhỏ nhất, sai
   số điểm mốc trung bình và lớn nhất, kết luận đạt/không đạt từng độ phân giải. Kèm đường dẫn tệp
   trong `results/` và **kích thước thư mục NCNN** từng độ phân giải.
6. Vướng mắc: chỗ nào trong đặc tả này mơ hồ, thiếu, hoặc mâu thuẫn.

**Không commit.** Để nguyên cây làm việc cho người review.
