# P2-04-export-ncnn — Export YOLOv8n-face sang NCNN và kiểm chứng tương đương

> Mã việc: `P2-04-export-ncnn` · Phần còn lại của bước **2.2** trong `CLAUDE.md` §5 Phase 2
> Nhánh: `feat/p2-04-export-ncnn` · Đặc tả viết ngày 27/08/2026 · **sửa đổi vòng 2, cùng ngày**

---

## 0. Vòng 2 — GIAO LẠI, đọc mục này trước

Bản đặc tả commit `9816027` đã được cài đặt xong: `scripts/export_detector_ncnn.py`,
`tests/test_export_detector_ncnn.py`, `requirements-dev.txt`, và lượt chạy thật đã sinh
`results/export_ncnn_20260827_2027.{json,meta.json}`. **Không viết lại từ đầu.**

Vòng này chỉ **bổ sung** đúng bốn thay đổi, phát sinh từ chuẩn mới ở
`.claude/instructions/experiment-protocol.instructions.md` §2 — được chốt sau khi bạn đã nộp mã:

| # | Việc | Chỗ sửa |
|---|---|---|
| 1 | Thêm hàm `xac_dinh_moi_truong()` | `scripts/export_detector_ncnn.py`, xem §5.2 |
| 2 | `thu_thap_metadata_ncnn` trả thêm khoá `moi_truong` | cùng tệp |
| 3 | Thêm ba ca kiểm thử 20b, 20c, 20d | `tests/test_export_detector_ncnn.py`, xem §8.4 |
| 4 | Chạy lại lượt sinh kết quả để `.meta.json` có trường mới | lượt của **người dùng**, §12b |

Lý do thay đổi giữa chừng, nói thẳng để bạn không phải đoán: chuẩn `moi_truong` ra đời sau khi đặc
tả vòng 1 đã commit. Đây là **khiếm khuyết của đặc tả**, không phải của bạn. Mọi thứ bạn đã làm ở
vòng 1 vẫn đúng hợp đồng lúc đó và **giữ nguyên**.

Bảng dữ kiện §3 giờ đã có số thật từ lượt chạy của bạn — đọc lại, vì một dòng trong đó (fp16) hoá ra
sai và §7.3 đã sửa theo.

---

## 1. Mục tiêu

Chuyển `models/yolov8n-face.pt` sang định dạng **NCNN** ở hai độ phân giải 320 và 640, rồi
**chứng minh bằng số đo** rằng bản NCNN cho kết quả tương đương bản gốc trên ảnh thật — đúng ba
đại lượng và đúng phương pháp đã dùng cho bản ONNX ở `P2-01`.

Vì sao cần: bước 2.6 quy định ma trận đo `{ONNX, NCNN} × {320, 640} × {1, 2, 4 luồng}`. Hiện chỉ có
nửa ONNX. Thiếu nửa NCNN thì không kết luận được bộ suy luận nào phù hợp với Raspberry Pi 5, và
Chương 2 §2.6.3 của báo cáo còn treo dòng `[CHƯA VIẾT — CHẶN VÌ CHƯA ĐO]`.

Vì sao phải kiểm chứng thay vì export xong là tin: đường NCNN đi qua **hai** phép biến đổi liên tiếp
(PyTorch → PNNX → NCNN), nhiều hơn đường ONNX một chặng.
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
| Cấu trúc thư mục `ultralytics` sinh ra khi `format="ncnn"` | thư mục `<stem>_ncnn_model/` gồm **bốn** tệp: `model.ncnn.param`, `model.ncnn.bin`, `metadata.yaml`, `model_ncnn.py` | **đã kiểm** — lượt chạy 27/08/2026 20:26 |
| Kích thước `model.ncnn.bin` | 12 354 804 B (imgsz 320) · 12 480 804 B (imgsz 640) | **đã kiểm** |
| Kích thước `model.ncnn.param` | 19 257 B (320) · 19 260 B (640) | **đã kiểm** |
| `metadata.yaml` | có, 449 B, ghi `task: pose`, `batch: 1`, `imgsz: [320, 320]`, `names: {0: face}`, `kpt_shape`, **`half: false`** | **đã kiểm** |
| `YOLO(<thư mục ncnn>, task="pose")` có trả về `keypoints` | **có** — guard `_bao_dam_ncnn_co_diem_moc` không kích hoạt trong lượt chạy 50 ảnh × 2 độ phân giải | **đã kiểm** |
| Độ khớp NCNN so với `.pt` | khớp số mặt 100/100 · IoU TB 0,9999996 · sai số điểm mốc TB 2,3 × 10⁻⁵ px | **đã kiểm** — `results/export_ncnn_20260827_2027.json` |

⚠️ **`half: false` — bản NCNN là fp32, không phải fp16.** Bản đặc tả vòng 1 đoán sai điều này và
suy ra rằng sai số sẽ lớn hơn ONNX. Thực tế ngược lại: sai số ở mức làm tròn float32 (10⁻⁵ px), tức
phép chuyển đổi gần như không mất mát. §7.3 đã sửa theo dữ kiện này.

`model_ncnn.py` là script mẫu do PNNX sinh kèm, **không cần** cho đường nạp lại của `ultralytics`.
Nó bị import khi thư mục được nạp nên sinh ra `__pycache__/` bên trong — hiện tượng bình thường,
`models/*` đã gitignore.

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

def xac_dinh_moi_truong() -> str:
    """Trả về mã môi trường chạy: 'pc_x86' | 'docker_arm64' | 'pi5'.

    Quy tắc (experiment-protocol.instructions.md §2): có `/.dockerenv` → `docker_arm64`;
    kiến trúc máy là aarch64/arm64 → `pi5`; còn lại → `pc_x86`. Script tự suy ra, KHÔNG
    nhận từ tham số dòng lệnh — người gõ tay thì sớm muộn cũng gõ nhầm, mà nhầm ở đây
    không có gì báo lỗi và làm mất nguyên một cột trong bảng so sánh môi trường.
    """

def thu_thap_metadata_ncnn(cfg_tho: dict, seed: int) -> dict:
    """Gom metadata theo R17: commit, cấu hình, phiên bản thư viện, thiết bị, thời điểm, seed.

    Hai điểm khác `_thu_thap_metadata` của P2-01: phần `phien_ban` phải có `ncnn` và không
    cần `onnx`/`onnxruntime`; bản ghi phải có thêm khoá `moi_truong` lấy từ
    `xac_dinh_moi_truong()`.
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

### 7.1. Bước xác minh — đã do người dùng chạy, bạn KHÔNG chạy lại

Ba dòng `CHƯA KIỂM` ở §3 được trả lời bằng notebook
[`notebooks/03_xac_minh_export_ncnn.ipynb`](../../notebooks/03_xac_minh_export_ncnn.ipynb), do người
dùng chạy **trước khi** đặc tả này được commit. Notebook giữ nguyên đầu ra trong tệp, nên bạn **đọc
được** cây tệp thật, nội dung `metadata.yaml` và bảng đối chiếu ở đó — hãy đọc nó trước khi viết mã.

Bạn **không** export thử, **không** chạy `ultralytics` để thăm dò. Cứ tin bảng §3 — nếu mã bạn viết
xong lại hành xử khác bảng đó, **dừng và báo**, đừng tự sửa bảng cũng đừng tự xoay xở: sai lệch ở
đây là lỗi đặc tả, và phải sửa đặc tả rồi giao lại (R39).

Notebook đó **không thay thế** script bạn sắp viết: nó không ghi `.meta.json`, không quét đủ cỡ mẫu,
và không chạy được bằng dòng lệnh trên máy không màn hình. Nó trả lời câu hỏi *"chuyển đổi có mất
mát gì không"*; script trả lời câu hỏi *"số liệu nào đi vào báo cáo"*.

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

⚠️ Nếu không đạt ngưỡng: **báo cáo đúng số thật và dừng** (R7). Tuyệt đối không nới ngưỡng, không
đổi sang so sánh lỏng hơn, không lặng lẽ đổi tham số export rồi báo đạt — mọi thay đổi tham số đều
phải qua sửa đặc tả. Một kết quả "không đạt" có số liệu kèm theo là **kết quả hợp lệ** của mã việc.

⚠️ **Kết quả vòng 1 đạt ở mức đáng ngờ — điểm này sẽ bị soi khi review.** Sai số 2,3 × 10⁻⁵ px là
mức làm tròn float32. Với `half: false` thì con số đó **hợp lý**, nhưng nó cũng là dấu hiệu của một
chế độ hỏng nghiêm trọng khác: hai phía của phép so sánh vô tình nạp **cùng một mô hình**. Hai giả
thuyết này cho ra số liệu giống hệt nhau, nên số liệu không phân biệt được chúng.

Cách phân biệt, và bạn **phải** trả lời trong báo cáo vòng này: chỉ ra bằng `file:dòng` nơi hai
đường nạp tách nhau, và nêu bằng chứng rằng đường NCNN thật sự chạy qua `ncnn` — ví dụ gỡ tạm thư
mục NCNN rồi xác nhận lượt chạy hỏng, chứ không âm thầm rơi về bản `.pt`.

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
`thiet_bi`, `thoi_diem`, `seed`, và **`moi_truong`**.

`moi_truong` nhận đúng một trong ba giá trị `pc_x86` · `docker_arm64` · `pi5`
(`experiment-protocol.instructions.md` §2). Đây là khoá để notebook `04_so_sanh_moi_truong.ipynb`
gộp kết quả từ nhiều máy về một bảng — thứ mà báo cáo cần để trình bày **tính khả chuyển**: cùng
đầu vào, cùng seed, cùng kết quả trên cả máy phát triển, container ARM64 và Pi 5.

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

> Hai dòng 05–06 phải export thật nên đánh dấu `@pytest.mark.slow`. **Bạn viết chúng nhưng không
> chạy chúng** — chúng thuộc lượt của người dùng ở §12b. Lượt của bạn dùng `-m "not slow"`.
> Hệ quả bắt buộc: mọi ca **không** đánh dấu `slow` phải chạy được ở nơi thiếu `ncnn`,
> `ultralytics`, `torch`; ca nào cần ba gói đó thì hoặc đánh dấu `slow`, hoặc giả lập bằng
> `monkeypatch`.

### 8.2. Kiểm tra thư mục NCNN

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 07 | Thư mục không tồn tại → `LoiMoHinh` | `pytest.raises(LoiMoHinh)` với `tmp_path / "khong-co"` |
| 08 | Thiếu `model.ncnn.param` → `LoiMoHinh`, thông báo **nêu tên tệp thiếu** | Dựng thư mục giả trong `tmp_path` chỉ có `.bin` + `metadata.yaml`; `pytest.raises(LoiMoHinh, match="param")` |
| 08b | Có đủ ba tệp bắt buộc nhưng **thiếu** `model_ncnn.py` → vẫn hợp lệ | Cùng cách dựng thư mục giả, không tạo `model_ncnn.py`; `kiem_tra_thu_muc_ncnn` không ném lỗi. Tệp này là script mẫu của PNNX, không nằm trên đường nạp lại (§3) |
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
| 19 | `thu_thap_metadata_ncnn` có đủ **bảy** trường | `set(meta) >= {"commit","cau_hinh","phien_ban","thiet_bi","thoi_diem","seed","moi_truong"}` |
| 20 | Phần `phien_ban` **có khoá `ncnn`** | `"ncnn" in meta["phien_ban"]` |
| 20b | `moi_truong` nhận đúng một trong ba mã hợp lệ | `xac_dinh_moi_truong() in {"pc_x86","docker_arm64","pi5"}` |
| 20c | Có `/.dockerenv` → `docker_arm64`, bất kể kiến trúc | Monkeypatch `Path.exists` cho `/.dockerenv` trả `True`; assert `== "docker_arm64"` |
| 20d | Không có `/.dockerenv`, máy `aarch64` → `pi5` | Monkeypatch `platform.machine` trả `"aarch64"`; assert `== "pi5"` |
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

> ⚠️ **Hai thứ KHÔNG thuộc phần này**, cả hai đều là lượt của người dùng (§12b):
> lượt chạy thật `python scripts/export_detector_ncnn.py` — thứ sinh ra thư mục NCNN trong `models/`
> và tệp `results/export_ncnn_*.json` — và các ca `@pytest.mark.slow` phải export thật.
> Lý do: số liệu đi vào báo cáo phải qua mắt người ít nhất một lần (R5, R6) và `.meta.json` phải
> ghi đúng máy đã chạy (R17). Lượt của bạn chỉ gồm phần dưới đây.

```bash
python -m black --check --line-length 100 scripts/export_detector_ncnn.py tests/test_export_detector_ncnn.py
```

```bash
python -m ruff check scripts/export_detector_ncnn.py tests/test_export_detector_ncnn.py
```

```bash
python -m pytest tests/test_export_detector_ncnn.py -v -m "not slow"
```

```bash
python -m pytest tests/test_export_detector_ncnn.py --collect-only -m "not slow"
```

Lệnh trên canh ràng buộc thu thập ở cuối §8: không gói nặng nào được import ở mức module.

```bash
python -m pytest -q -m "not slow"
```

Lệnh trên là **toàn bộ** bộ kiểm thử của repo — mã việc này import từ `scripts/export_detector.py`
nên phải chắc không làm hỏng ca nào của `P2-01`.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

Image đã có sẵn — **không** `docker build` (R43). Container không có `ncnn`/`ultralytics`/`torch`,
nên lệnh này cũng là phép kiểm rằng bạn đã import ba gói đó đúng chỗ.

```bash
git status --short --untracked-files=all
```

Ở lượt của bạn, lệnh này phải cho thấy **đúng ba tệp** của §2 — không hơn. Các tệp
`results/export_ncnn_*.json` chỉ xuất hiện sau lượt chạy của người dùng ở §12b; thư mục NCNN trong
`models/` không bao giờ xuất hiện vì `models/*` đã gitignore. Bất kỳ tệp nào khác là vi phạm phạm vi.

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
| ĐB5 | Trong `xac_dinh_moi_truong`, luôn trả `'pc_x86'` bất kể môi trường | dòng 20c **và** 20d |

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

1. **Bốn việc ở §0** đã xử lý thế nào, mỗi việc một dòng.
2. **Trả lời nghi vấn ở §7.3**: `file:dòng` nơi hai đường nạp `.pt` và NCNN tách nhau, kèm bằng
   chứng rằng đường NCNN thật sự đi qua `ncnn` chứ không rơi về bản `.pt`.
3. Kết quả các lệnh §9, dán nguyên văn dòng tổng kết.
3. Kết quả bốn lệnh `grep`, giải trình dòng nào không rỗng.
4. Bảng bốn phép đột biến: ca dự đoán đỏ · ca thật sự đỏ · `sha256` khôi phục có khớp không.
5. **Lệnh người dùng cần chạy** ở §12b, viết sẵn đầy đủ để chép thẳng. Ô số đo tương đương để
   `[CHƯA CHẠY — chờ lượt của người dùng]`, **không đoán trước**.
6. Vướng mắc: chỗ nào trong đặc tả này mơ hồ, thiếu, hoặc mâu thuẫn.

**Không commit.** Để nguyên cây làm việc cho người review.

---

## 12b. Lượt chạy thật — người dùng chạy, không phải người cài đặt

Sau khi §9 xanh hết, người dùng chạy:

```bash
python -m pytest tests/test_export_detector_ncnn.py -v -m slow
```

Kết quả mong đợi: hai ca 05–06 xanh. Đây là lần export thật đầu tiên, có thể mất vài phút.

```bash
python scripts/export_detector_ncnn.py --dry-run
```

Kết quả mong đợi: in bảng kế hoạch hai độ phân giải, mã thoát `0`, và **không tạo tệp nào**.

```bash
python scripts/export_detector_ncnn.py
```

Kết quả mong đợi: sinh hai thư mục `models/yolov8n-face-{320,640}_ncnn_model/`, một cặp tệp
`results/export_ncnn_<YYYYMMDD_HHMM>.{json,meta.json}`, và in bảng số đo tương đương. Mã thoát `0`
nghĩa là cả hai độ phân giải đạt cả ba ngưỡng §7.3; mã thoát `1` nghĩa là **có độ phân giải không
đạt** — đó là kết quả hợp lệ, dán về nguyên văn, không chạy lại cho tới khi ra số đẹp.

Lần chạy đầu có thể mất vài phút vì `ultralytics` tải công cụ PNNX về; máy không ra được mạng thì
lệnh này hỏng ở đó — dán nguyên văn lỗi về.

```bash
ls -la models/yolov8n-face-320_ncnn_model models/yolov8n-face-640_ncnn_model
```

Dùng để điền kích thước tệp vào bảng B3 của `models/README.md`.

Số đo từ lượt chạy này là **nguồn duy nhất** cho mọi con số NCNN trong biên bản review và trong
báo cáo (R6). Kết quả `coder` mô tả không thay thế được nó.

### Xử lý bộ kết quả của vòng 1

`results/export_ncnn_20260827_2027.{json,meta.json}` sinh ra trước khi chuẩn `moi_truong` ra đời,
nên `.meta.json` của nó thiếu trường đó. Sau khi lượt chạy vòng 2 xong và cho số liệu tương đương,
**xoá bộ cũ** — mỗi lần chạy có ý nghĩa mới giữ một tệp, không phải mỗi lần bấm chạy (P2-01 §9):

```bash
rm results/export_ncnn_20260827_2027.json results/export_ncnn_20260827_2027.meta.json
```

Chỉ xoá **sau khi** đã có bộ mới và đã đối chiếu thấy số trùng khớp. Nếu số vòng 2 **khác** vòng 1
thì giữ cả hai và báo lại — hai lượt chạy cùng seed, cùng mã, cùng máy mà ra số khác nhau là dấu
hiệu có gì đó không tất định, phải truy ra trước khi commit.
