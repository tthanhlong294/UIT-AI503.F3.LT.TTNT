"""Export trọng số YOLOv8n-face (.pt) sang ONNX và kiểm chứng tương đương với bản gốc.

Xem docs/dac-ta/P2-01-export-detector.md. Chạy trên PC phát triển, KHÔNG chạy trên Pi 5:
Raspberry Pi 5 chỉ cài `onnxruntime` (xem requirements.txt), không có `torch`/`ultralytics`.

`ultralytics`, `onnx`, `torch` đã có sẵn trên máy phát triển nhưng CỐ Ý không nằm trong
requirements.txt vì Pi 5 không cần chúng — toàn hệ thống khi chạy trên Pi chỉ dùng
`onnxruntime` với các tệp .onnx do script này sinh ra trước. Vì vậy các hàm cần những
thư viện này chỉ import chúng cục bộ trong thân hàm, không import ở đầu tệp.
"""

import sys
from pathlib import Path

# Thêm gốc dự án vào sys.path để cho phép chạy trực tiếp kịch bản
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import datetime
import json
import platform
import random
import subprocess

import numpy as np

from src.common.config import lay_gia_tri, nap_cau_hinh
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)

# --- Ngưỡng kiểm chứng tương đương .pt vs .onnx — cố định theo §7 của đặc tả P2-01 ---
# KHÔNG đọc từ configs/detect.yaml: khác với inference.conf_threshold/inference.iou_threshold
# (dùng để chạy suy luận, tìm khuôn mặt trong ảnh), ba hằng số dưới đây dùng để ĐÁNH GIÁ
# độ khớp giữa bản .pt và bản .onnx trên cùng một ảnh — đây là tiêu chí đạt/không đạt của
# chính bước export, không phải tham số vận hành của hệ thống.
NGUONG_TI_LE_KHOP_SO_MAT = 0.95
NGUONG_IOU_TOI_THIEU = 0.90
NGUONG_SAI_SO_DIEM_MOC_TOI_DA_PX = 5.0

_DINH_DANG_ANH_HOP_LE = {".jpg", ".jpeg", ".png"}

_KHOA_BAT_BUOC_KET_QUA = (
    "n_anh",
    "n_khop_so_mat",
    "iou_trung_binh",
    "iou_nho_nhat",
    "sai_so_diem_moc_trung_binh",
    "sai_so_diem_moc_lon_nhat",
    "dat",
    "meta",
)


def doc_cau_hinh(cfg: dict) -> dict:
    """Kiểm tra và trích các tham số export từ cấu hình.

    Args:
        cfg: Từ điển cấu hình đã nạp từ configs/detect.yaml (qua `nap_cau_hinh`).

    Returns:
        Từ điển phẳng gồm tám khoá: `weights_pt`, `kich_thuoc`, `opset`, `batch`,
        `simplify`, `out_dir`, `conf_threshold`, `iou_threshold`.

    Raises:
        LoiCauHinh: Thiếu key bắt buộc, hoặc giá trị sai kiểu / ngoài miền hợp lệ.
    """
    weights_pt = lay_gia_tri(cfg, "export.weights_pt")
    kich_thuoc = lay_gia_tri(cfg, "export.kich_thuoc")
    opset = lay_gia_tri(cfg, "export.opset")
    batch = lay_gia_tri(cfg, "export.batch")
    simplify = lay_gia_tri(cfg, "export.simplify")
    out_dir = lay_gia_tri(cfg, "export.out_dir")
    conf_threshold = lay_gia_tri(cfg, "inference.conf_threshold")
    iou_threshold = lay_gia_tri(cfg, "inference.iou_threshold")

    if not isinstance(weights_pt, str) or not weights_pt:
        raise LoiCauHinh(
            f"'export.weights_pt' phải là chuỗi đường dẫn khác rỗng, nhận được: {weights_pt!r}"
        )

    if not isinstance(kich_thuoc, list) or len(kich_thuoc) == 0:
        raise LoiCauHinh(
            "'export.kich_thuoc' phải là danh sách số nguyên dương khác rỗng, "
            f"nhận được: {kich_thuoc!r}"
        )
    for gia_tri in kich_thuoc:
        if isinstance(gia_tri, bool) or not isinstance(gia_tri, int) or gia_tri <= 0:
            raise LoiCauHinh(
                f"'export.kich_thuoc' chứa giá trị không phải số nguyên dương: {gia_tri!r}"
            )

    if isinstance(opset, bool) or not isinstance(opset, int) or opset <= 0:
        raise LoiCauHinh(f"'export.opset' phải là số nguyên dương, nhận được: {opset!r}")

    if isinstance(batch, bool) or not isinstance(batch, int) or batch <= 0:
        raise LoiCauHinh(f"'export.batch' phải là số nguyên dương, nhận được: {batch!r}")

    if not isinstance(simplify, bool):
        raise LoiCauHinh(f"'export.simplify' phải là luận lý (bool), nhận được: {simplify!r}")

    if not isinstance(out_dir, str) or not out_dir:
        raise LoiCauHinh(
            f"'export.out_dir' phải là chuỗi đường dẫn khác rỗng, nhận được: {out_dir!r}"
        )

    if (
        isinstance(conf_threshold, bool)
        or not isinstance(conf_threshold, (int, float))
        or not (0.0 <= float(conf_threshold) <= 1.0)
    ):
        raise LoiCauHinh(
            "'inference.conf_threshold' phải trong khoảng [0, 1], " f"nhận được: {conf_threshold!r}"
        )

    if (
        isinstance(iou_threshold, bool)
        or not isinstance(iou_threshold, (int, float))
        or not (0.0 <= float(iou_threshold) <= 1.0)
    ):
        raise LoiCauHinh(
            f"'inference.iou_threshold' phải trong khoảng [0, 1], nhận được: {iou_threshold!r}"
        )

    return {
        "weights_pt": weights_pt,
        "kich_thuoc": kich_thuoc,
        "opset": opset,
        "batch": batch,
        "simplify": simplify,
        "out_dir": out_dir,
        "conf_threshold": conf_threshold,
        "iou_threshold": iou_threshold,
    }


def export_mot_kich_thuoc(
    weights: Path,
    imgsz: int,
    opset: int,
    batch: int,
    simplify: bool,
    out_dir: Path,
    dry_run: bool = False,
) -> Path:
    """Export trọng số .pt sang .onnx ở một độ phân giải.

    Args:
        weights: Đường dẫn trọng số nguồn (.pt).
        imgsz: Độ phân giải ảnh vuông dùng để export.
        opset: Phiên bản opset ONNX.
        batch: Kích thước lô cố định của đồ thị xuất ra.
        simplify: Có chạy onnx-simplifier để gộp nút thừa hay không.
        out_dir: Thư mục ghi tệp .onnx ra.
        dry_run: Chỉ tính đường dẫn dự kiến, không thực sự export.

    Returns:
        Đường dẫn tệp .onnx đã tạo. Với dry_run trả về đường dẫn dự kiến, không tạo tệp.

    Raises:
        LoiMoHinh: Không tìm thấy trọng số nguồn, hoặc export thất bại.
    """
    weights = Path(weights)
    if not weights.exists():
        raise LoiMoHinh(f"Không tìm thấy trọng số nguồn: {weights}")

    duong_dan_ra = Path(out_dir) / f"yolov8n-face-{imgsz}.onnx"

    if dry_run:
        logger.info("[DRY-RUN] Sẽ export '%s' (imgsz=%d) ra '%s'", weights, imgsz, duong_dan_ra)
        return duong_dan_ra

    # ultralytics/torch: xem docstring đầu tệp — cố ý import cục bộ, không có trên Pi 5.
    from ultralytics import YOLO

    mo_hinh = YOLO(str(weights))
    try:
        duong_dan_xuat = Path(
            mo_hinh.export(format="onnx", imgsz=imgsz, opset=opset, batch=batch, simplify=simplify)
        )
    except (RuntimeError, OSError, ValueError, TypeError, ImportError) as e:
        raise LoiMoHinh(f"Export ONNX thất bại cho imgsz={imgsz}: {e}") from e

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    if duong_dan_xuat.resolve() != duong_dan_ra.resolve():
        duong_dan_xuat.replace(duong_dan_ra)

    logger.info("Đã export xong: %s", duong_dan_ra)
    return duong_dan_ra


def _tinh_iou(hop1: np.ndarray, hop2: np.ndarray) -> float:
    """Tính IoU giữa hai khung bao dạng (x1, y1, x2, y2)."""
    x1 = max(float(hop1[0]), float(hop2[0]))
    y1 = max(float(hop1[1]), float(hop2[1]))
    x2 = min(float(hop1[2]), float(hop2[2]))
    y2 = min(float(hop1[3]), float(hop2[3]))

    giao = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    dt1 = max(0.0, float(hop1[2]) - float(hop1[0])) * max(0.0, float(hop1[3]) - float(hop1[1]))
    dt2 = max(0.0, float(hop2[2]) - float(hop2[0])) * max(0.0, float(hop2[3]) - float(hop2[1]))
    hop = dt1 + dt2 - giao

    if hop <= 0.0:
        return 0.0
    return giao / hop


def so_sanh_mot_anh(
    khung_pt: np.ndarray,
    diem_pt: np.ndarray,
    khung_onnx: np.ndarray,
    diem_onnx: np.ndarray,
    iou_toi_thieu: float,
    sai_so_diem_moc_toi_da: float,
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
    khung_pt = np.asarray(khung_pt, dtype=np.float64)
    khung_onnx = np.asarray(khung_onnx, dtype=np.float64)
    diem_pt = np.asarray(diem_pt, dtype=np.float64)
    diem_onnx = np.asarray(diem_onnx, dtype=np.float64)

    if khung_pt.ndim != 2 or khung_pt.shape[1] != 4:
        raise ValueError(f"khung_pt phải có hình dạng (N, 4), nhận được {khung_pt.shape}")
    if khung_onnx.ndim != 2 or khung_onnx.shape[1] != 4:
        raise ValueError(f"khung_onnx phải có hình dạng (M, 4), nhận được {khung_onnx.shape}")
    if diem_pt.ndim != 3 or diem_pt.shape[1:] != (5, 2):
        raise ValueError(f"diem_pt phải có hình dạng (N, 5, 2), nhận được {diem_pt.shape}")
    if diem_onnx.ndim != 3 or diem_onnx.shape[1:] != (5, 2):
        raise ValueError(f"diem_onnx phải có hình dạng (M, 5, 2), nhận được {diem_onnx.shape}")

    if diem_pt.shape[0] != khung_pt.shape[0]:
        raise ValueError(
            f"Số khung của .pt ({khung_pt.shape[0]}) không khớp số bộ điểm mốc "
            f"({diem_pt.shape[0]})"
        )
    if diem_onnx.shape[0] != khung_onnx.shape[0]:
        raise ValueError(
            f"Số khung của .onnx ({khung_onnx.shape[0]}) không khớp số bộ điểm mốc "
            f"({diem_onnx.shape[0]})"
        )

    so_mat_pt = khung_pt.shape[0]
    so_mat_onnx = khung_onnx.shape[0]
    khop_so_mat = so_mat_pt == so_mat_onnx

    if not khop_so_mat:
        return {
            "so_mat_pt": so_mat_pt,
            "so_mat_onnx": so_mat_onnx,
            "khop_so_mat": False,
            "iou_min": None,
            "sai_so_diem_moc_max": None,
            "dat": False,
        }

    if so_mat_pt == 0:
        return {
            "so_mat_pt": 0,
            "so_mat_onnx": 0,
            "khop_so_mat": True,
            "iou_min": None,
            "sai_so_diem_moc_max": None,
            "dat": True,
        }

    danh_sach_iou = [_tinh_iou(khung_pt[i], khung_onnx[i]) for i in range(so_mat_pt)]
    iou_min = min(danh_sach_iou)

    khoang_cach = np.linalg.norm(diem_pt - diem_onnx, axis=-1)
    sai_so_diem_moc_max = float(np.max(khoang_cach))

    dat = bool(iou_min >= iou_toi_thieu and sai_so_diem_moc_max <= sai_so_diem_moc_toi_da)

    return {
        "so_mat_pt": so_mat_pt,
        "so_mat_onnx": so_mat_onnx,
        "khop_so_mat": True,
        "iou_min": float(iou_min),
        "sai_so_diem_moc_max": sai_so_diem_moc_max,
        "dat": dat,
    }


def _trich_khung_diem_moc(ket_qua) -> tuple[np.ndarray, np.ndarray]:
    """Trích khung bao và điểm mốc từ một đối tượng `Results` của ultralytics.

    Sắp xếp theo độ tin cậy giảm dần để khớp quy ước đầu vào của `so_sanh_mot_anh`.
    """
    if ket_qua.boxes is None or len(ket_qua.boxes) == 0:
        return np.zeros((0, 4), dtype=np.float64), np.zeros((0, 5, 2), dtype=np.float64)

    khung = ket_qua.boxes.xyxy.cpu().numpy().astype(np.float64)
    conf = ket_qua.boxes.conf.cpu().numpy()
    diem = ket_qua.keypoints.xy.cpu().numpy().astype(np.float64)

    thu_tu = np.argsort(-conf)
    return khung[thu_tu], diem[thu_tu]


def kiem_chung_tuong_duong(
    weights_pt: Path,
    onnx_path: Path,
    danh_sach_anh: list[Path],
    imgsz: int,
    conf: float,
    iou: float,
    sai_so_diem_moc_toi_da: float,
) -> dict:
    """Chạy cả hai mô hình trên cùng tập ảnh và tổng hợp số đo.

    ⚠️ Nạp bản .onnx BẮT BUỘC chỉ định `task="pose"`. Nếu không, ultralytics đoán sai
    task thành 'detect' (đồ thị ONNX thuần không mang theo tên lớp/kpt_shape), bỏ qua
    hậu xử lý pose (NMS đúng kiểu + trích điểm mốc) và trả về hàng trăm khung thô chưa
    lọc thay vì một khung đúng. Đã kiểm chứng thủ công trên máy này ngày 17/08/2026:
    cùng ảnh, cùng tham số, chỉ khác việc truyền `task="pose"` mà kết quả lệch hẳn.

    `iou` chỉ dùng làm ngưỡng NMS khi chạy suy luận (khớp `inference.iou_threshold` của
    cấu hình) — ngưỡng IoU để ĐÁNH GIÁ độ khớp giữa hai mô hình lấy từ hằng số cố định
    `NGUONG_IOU_TOI_THIEU` (§7 đặc tả), không đọc từ tham số này.

    Args:
        weights_pt: Đường dẫn trọng số .pt gốc.
        onnx_path: Đường dẫn tệp .onnx đã export cần kiểm chứng.
        danh_sach_anh: Danh sách ảnh dùng để so sánh.
        imgsz: Độ phân giải suy luận, phải khớp độ phân giải đã export `onnx_path`.
        conf: Ngưỡng độ tin cậy khi suy luận.
        iou: Ngưỡng NMS khi suy luận.
        sai_so_diem_moc_toi_da: Ngưỡng sai số điểm mốc tối đa, đơn vị pixel.

    Returns:
        Từ điển tổng hợp, tối thiểu gồm: `n_anh`, `n_khop_so_mat`, `iou_trung_binh`,
        `iou_nho_nhat`, `sai_so_diem_moc_trung_binh`, `sai_so_diem_moc_lon_nhat`, `dat`.

    Raises:
        LoiCauHinh: `danh_sach_anh` rỗng.
    """
    if not danh_sach_anh:
        raise LoiCauHinh("Danh sách ảnh kiểm chứng rỗng, không thể tính số đo trung bình")

    from ultralytics import YOLO

    mo_hinh_pt = YOLO(str(weights_pt), task="pose")
    mo_hinh_onnx = YOLO(str(onnx_path), task="pose")

    n_anh = len(danh_sach_anh)
    n_khop_so_mat = 0
    danh_sach_iou: list[float] = []
    danh_sach_sai_so: list[float] = []

    for anh in danh_sach_anh:
        kq_pt = mo_hinh_pt.predict(source=str(anh), imgsz=imgsz, conf=conf, iou=iou, verbose=False)[
            0
        ]
        kq_onnx = mo_hinh_onnx.predict(
            source=str(anh), imgsz=imgsz, conf=conf, iou=iou, verbose=False
        )[0]

        khung_pt, diem_pt = _trich_khung_diem_moc(kq_pt)
        khung_onnx, diem_onnx = _trich_khung_diem_moc(kq_onnx)

        kq = so_sanh_mot_anh(
            khung_pt, diem_pt, khung_onnx, diem_onnx, NGUONG_IOU_TOI_THIEU, sai_so_diem_moc_toi_da
        )

        if kq["khop_so_mat"]:
            n_khop_so_mat += 1
        if kq["iou_min"] is not None:
            danh_sach_iou.append(kq["iou_min"])
        if kq["sai_so_diem_moc_max"] is not None:
            danh_sach_sai_so.append(kq["sai_so_diem_moc_max"])

    iou_trung_binh = float(np.mean(danh_sach_iou)) if danh_sach_iou else None
    iou_nho_nhat = float(np.min(danh_sach_iou)) if danh_sach_iou else None
    sai_so_tb = float(np.mean(danh_sach_sai_so)) if danh_sach_sai_so else None
    sai_so_max = float(np.max(danh_sach_sai_so)) if danh_sach_sai_so else None

    ti_le_khop = n_khop_so_mat / n_anh
    dat = (
        ti_le_khop >= NGUONG_TI_LE_KHOP_SO_MAT
        and iou_trung_binh is not None
        and iou_trung_binh >= NGUONG_IOU_TOI_THIEU
        and sai_so_tb is not None
        and sai_so_tb <= sai_so_diem_moc_toi_da
    )

    return {
        "n_anh": n_anh,
        "n_khop_so_mat": n_khop_so_mat,
        "iou_trung_binh": iou_trung_binh,
        "iou_nho_nhat": iou_nho_nhat,
        "sai_so_diem_moc_trung_binh": sai_so_tb,
        "sai_so_diem_moc_lon_nhat": sai_so_max,
        "dat": dat,
    }


def ghi_ket_qua(duong_dan: Path, ban_ghi: dict) -> None:
    """Ghi số đo ra tệp JSON kèm tệp .meta.json theo R17.

    `ban_ghi` phải chứa đủ bảy khoá tổng hợp số đo (xem `kiem_chung_tuong_duong`) và một
    khoá `meta` (từ điển) — nội dung `meta` được ghi riêng ra `<duong_dan>.meta.json`,
    phần còn lại ghi ra `duong_dan`.

    Args:
        duong_dan: Đường dẫn tệp JSON kết quả (dạng `export_detector_<YYYYMMDD_HHMM>.json`).
        ban_ghi: Từ điển kết quả cần ghi.

    Raises:
        LoiCauHinh: `ban_ghi` thiếu khoá bắt buộc.
    """
    thieu = [khoa for khoa in _KHOA_BAT_BUOC_KET_QUA if khoa not in ban_ghi]
    if thieu:
        raise LoiCauHinh(f"Bản ghi kết quả thiếu khoá bắt buộc: {', '.join(thieu)}")

    duong_dan = Path(duong_dan)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)

    noi_dung_chinh = {k: v for k, v in ban_ghi.items() if k != "meta"}
    with open(duong_dan, "w", newline="", encoding="utf-8") as f:
        json.dump(noi_dung_chinh, f, ensure_ascii=False, indent=2)

    duong_dan_meta = duong_dan.with_suffix(".meta.json")
    with open(duong_dan_meta, "w", newline="", encoding="utf-8") as f:
        json.dump(ban_ghi["meta"], f, ensure_ascii=False, indent=2)

    logger.info("Đã ghi kết quả: %s (kèm %s)", duong_dan, duong_dan_meta)


def _chon_mau_anh(thu_muc_anh: Path, so_anh: int, seed: int) -> list[Path]:
    """Chọn ngẫu nhiên có tái lập `so_anh` ảnh từ `thu_muc_anh` (R15).

    Args:
        thu_muc_anh: Thư mục gốc chứa ảnh (quét đệ quy).
        so_anh: Số ảnh cần chọn. Nếu thư mục có ít ảnh hơn, trả về toàn bộ.
        seed: Seed cho bộ sinh ngẫu nhiên cục bộ, đảm bảo tái lập được.

    Returns:
        Danh sách đường dẫn ảnh đã chọn, đã sắp xếp.
    """
    danh_sach = sorted(
        p
        for p in thu_muc_anh.rglob("*")
        if p.is_file() and p.suffix.lower() in _DINH_DANG_ANH_HOP_LE
    )
    if len(danh_sach) <= so_anh:
        return danh_sach

    rng = random.Random(seed)
    return sorted(rng.sample(danh_sach, so_anh))


def _lay_git_commit_hash() -> str:
    """Lấy commit hash hiện tại của repo, dùng cho .meta.json (R17)."""
    try:
        ket_qua = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        return ket_qua.stdout.strip()
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning("Không lấy được commit hash git: %s", e)
        return "khong-xac-dinh"


def _lay_phien_ban_thu_vien() -> dict:
    """Lấy phiên bản các thư viện dùng để export, cho .meta.json (R17)."""
    import onnx
    import onnxruntime
    import torch
    import ultralytics

    return {
        "ultralytics": ultralytics.__version__,
        "onnx": onnx.__version__,
        "onnxruntime": onnxruntime.__version__,
        "torch": torch.__version__,
    }


def _thu_thap_metadata(cfg_tho: dict, seed: int) -> dict:
    """Gom metadata bắt buộc theo R17: commit, cấu hình, phiên bản, thiết bị, thời điểm."""
    return {
        "commit": _lay_git_commit_hash(),
        "cau_hinh": cfg_tho,
        "phien_ban": _lay_phien_ban_thu_vien(),
        "thiet_bi": {"hostname": platform.node(), "he_dieu_hanh": platform.platform()},
        "thoi_diem": datetime.datetime.now().astimezone().isoformat(),
        "seed": seed,
    }


def _ten_tep_ket_qua(thoi_diem: datetime.datetime) -> str:
    """Sinh tên tệp kết quả theo quy ước `export_detector_<YYYYMMDD_HHMM>.json` (§7)."""
    return f"export_detector_{thoi_diem.strftime('%Y%m%d_%H%M')}.json"


def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 nếu thành công, 1 nếu thất bại."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=(
            "Export trọng số YOLOv8n-face .pt sang ONNX và kiểm chứng bằng số đo rằng bản "
            "ONNX cho kết quả tương đương bản gốc (xem docs/dac-ta/P2-01-export-detector.md)."
        )
    )
    parser.add_argument(
        "--config",
        default="configs/detect.yaml",
        help="Đường dẫn file cấu hình phát hiện khuôn mặt",
    )
    parser.add_argument(
        "--anh-dir",
        default="data/impostor/lfw_original",
        help="Thư mục ảnh dùng để kiểm chứng tương đương",
    )
    parser.add_argument("--so-anh", type=int, default=50, help="Số ảnh lấy mẫu để so sánh")
    parser.add_argument("--seed", type=int, default=42, help="Seed chọn mẫu ảnh, để tái lập")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in kế hoạch, không ghi tệp nào")

    args = parser.parse_args(argv)

    try:
        cfg_tho = nap_cau_hinh(args.config)
        cfg = doc_cau_hinh(cfg_tho)
    except LoiCauHinh as e:
        logger.error("Không thể đọc cấu hình: %s", e)
        return 1

    weights_pt = Path(cfg["weights_pt"])
    out_dir = Path(cfg["out_dir"])

    if args.dry_run:
        print("\n### BẢNG KẾ HOẠCH EXPORT (DRY-RUN)")
        print("| Kích thước | Tệp ONNX dự kiến |")
        print("|---|---|")
        for imgsz in cfg["kich_thuoc"]:
            duong_dan = export_mot_kich_thuoc(
                weights_pt,
                imgsz,
                cfg["opset"],
                cfg["batch"],
                cfg["simplify"],
                out_dir,
                dry_run=True,
            )
            print(f"| {imgsz} | `{duong_dan}` |")
        print(f"\nẢnh kiểm chứng : `{args.anh_dir}` (lấy mẫu {args.so_anh}, seed {args.seed})\n")
        return 0

    anh_dir = Path(args.anh_dir)
    if not anh_dir.exists() or not anh_dir.is_dir():
        logger.error("Thư mục ảnh kiểm chứng không tồn tại: '%s'", anh_dir)
        print(
            f"Thư mục ảnh kiểm chứng không tồn tại: '{anh_dir}'. "
            "Chạy 'python scripts/download_lfw.py' để tải bộ dữ liệu LFW trước."
        )
        return 1

    danh_sach_anh = _chon_mau_anh(anh_dir, args.so_anh, args.seed)
    if not danh_sach_anh:
        logger.error("Thư mục ảnh rỗng, không có ảnh hợp lệ: '%s'", anh_dir)
        print(f"Thư mục ảnh '{anh_dir}' rỗng, không có ảnh hợp lệ nào để kiểm chứng.")
        return 1

    ket_qua_theo_kich_thuoc: dict[str, dict] = {}
    try:
        for imgsz in cfg["kich_thuoc"]:
            onnx_path = export_mot_kich_thuoc(
                weights_pt, imgsz, cfg["opset"], cfg["batch"], cfg["simplify"], out_dir
            )
            kq = kiem_chung_tuong_duong(
                weights_pt,
                onnx_path,
                danh_sach_anh,
                imgsz,
                cfg["conf_threshold"],
                cfg["iou_threshold"],
                NGUONG_SAI_SO_DIEM_MOC_TOI_DA_PX,
            )
            ket_qua_theo_kich_thuoc[str(imgsz)] = kq
    except LoiMoHinh as e:
        logger.error("Export hoặc kiểm chứng thất bại: %s", e)
        return 1

    # n_anh_tong đếm mỗi ảnh MỘT LẦN CHO MỖI kích thước (vd. 50 ảnh x 2 kích thước = 100
    # phép so sánh) — không phải số ảnh phân biệt đã lấy mẫu. Tách riêng hai khái niệm để
    # tránh báo cáo nhầm "kiểm chứng trên 100 ảnh" trong khi thực tế chỉ có 50 ảnh (CS-2).
    so_anh_rieng_biet = len(danh_sach_anh)
    n_phep_so_sanh = sum(kq["n_anh"] for kq in ket_qua_theo_kich_thuoc.values())
    n_khop_tong = sum(kq["n_khop_so_mat"] for kq in ket_qua_theo_kich_thuoc.values())
    danh_sach_iou_tb = [
        kq["iou_trung_binh"]
        for kq in ket_qua_theo_kich_thuoc.values()
        if kq["iou_trung_binh"] is not None
    ]
    danh_sach_iou_min = [
        kq["iou_nho_nhat"]
        for kq in ket_qua_theo_kich_thuoc.values()
        if kq["iou_nho_nhat"] is not None
    ]
    danh_sach_sai_so_tb = [
        kq["sai_so_diem_moc_trung_binh"]
        for kq in ket_qua_theo_kich_thuoc.values()
        if kq["sai_so_diem_moc_trung_binh"] is not None
    ]
    danh_sach_sai_so_max = [
        kq["sai_so_diem_moc_lon_nhat"]
        for kq in ket_qua_theo_kich_thuoc.values()
        if kq["sai_so_diem_moc_lon_nhat"] is not None
    ]
    dat_tat_ca = all(kq["dat"] for kq in ket_qua_theo_kich_thuoc.values())

    ban_ghi = {
        "n_anh": so_anh_rieng_biet,
        "n_phep_so_sanh": n_phep_so_sanh,
        "n_khop_so_mat": n_khop_tong,
        "iou_trung_binh": float(np.mean(danh_sach_iou_tb)) if danh_sach_iou_tb else None,
        "iou_nho_nhat": float(np.min(danh_sach_iou_min)) if danh_sach_iou_min else None,
        "sai_so_diem_moc_trung_binh": (
            float(np.mean(danh_sach_sai_so_tb)) if danh_sach_sai_so_tb else None
        ),
        "sai_so_diem_moc_lon_nhat": (
            float(np.max(danh_sach_sai_so_max)) if danh_sach_sai_so_max else None
        ),
        "dat": dat_tat_ca,
        "theo_kich_thuoc": ket_qua_theo_kich_thuoc,
        "meta": _thu_thap_metadata(cfg_tho, args.seed),
    }

    duong_dan_ra = Path("results") / _ten_tep_ket_qua(datetime.datetime.now().astimezone())

    try:
        ghi_ket_qua(duong_dan_ra, ban_ghi)
    except LoiCauHinh as e:
        logger.error("Không ghi được kết quả: %s", e)
        return 1

    print("\n### KẾT QUẢ KIỂM CHỨNG TƯƠNG ĐƯƠNG XUẤT ONNX")
    print(
        "| Kích thước | Số ảnh | Khớp số mặt | IoU TB | IoU min | "
        "Sai số mốc TB (px) | Sai số mốc max (px) | Đạt |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for imgsz, kq in ket_qua_theo_kich_thuoc.items():
        print(
            f"| {imgsz} | {kq['n_anh']} | {kq['n_khop_so_mat']} | "
            f"{kq['iou_trung_binh']:.4f} | {kq['iou_nho_nhat']:.4f} | "
            f"{kq['sai_so_diem_moc_trung_binh']:.2f} | {kq['sai_so_diem_moc_lon_nhat']:.2f} | "
            f"{'DAT' if kq['dat'] else 'KHONG DAT'} |"
        )
    print(f"\nKết quả đầy đủ: `{duong_dan_ra}`\n")

    return 0 if dat_tat_ca else 1


if __name__ == "__main__":
    sys.exit(main())
