"""Export trọng số YOLOv8n-face (.pt) sang NCNN và kiểm chứng tương đương với bản gốc.

Xem docs/dac-ta/P2-04-export-ncnn.md. Chạy trên PC phát triển, KHÔNG chạy trên Pi 5:
Raspberry Pi 5 chỉ cài `onnxruntime` (xem requirements.txt), không có `torch`/`ultralytics`/
`ncnn`. Đường NCNN đi qua hai phép biến đổi liên tiếp (PyTorch → PNNX → NCNN), nhiều hơn
đường ONNX một chặng, nên bản NCNN phải được kiểm chứng bằng số đo trước khi tin dùng.

`ultralytics`, `torch`, `ncnn` đã có sẵn trên máy phát triển nhưng CỐ Ý không nằm trong
requirements.txt vì Pi 5 không cần chúng. Vì vậy các hàm cần những thư viện này chỉ import
chúng cục bộ trong thân hàm, không import ở đầu tệp (xem §7.2 đặc tả). Phần thu thập phiên
bản thư viện dùng `importlib.metadata` để không phải import gói nặng.

Mã việc này KHÔNG sinh ra con số hiệu năng nào — FPS của NCNN thuộc bước 2.6, đo trên Pi 5.
"""

import sys
from pathlib import Path

# Thêm gốc dự án vào sys.path để cho phép chạy trực tiếp kịch bản
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import datetime
import importlib.metadata
import importlib.util
import platform
import shutil

import numpy as np

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
from src.common.config import nap_cau_hinh
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)

# Tên ba tệp bắt buộc bên trong thư mục NCNN do ultralytics sinh ra. Giữ NGUYÊN VẸN —
# ultralytics đọc lại `metadata.yaml` để biết `task` và `imgsz` khi nạp lại (xem §4 đặc tả).
_TEP_NCNN_BAT_BUOC = ("model.ncnn.param", "model.ncnn.bin", "metadata.yaml")

# Bốn gói cần ghi phiên bản vào .meta.json (R17). Lấy qua importlib.metadata để không
# phải import gói nặng — nhờ vậy hàm chạy được cả trong container ARM64 không có chúng.
_GOI_GHI_PHIEN_BAN = ("ultralytics", "torch", "ncnn", "numpy")


def _tao_mo_hinh_yolo(duong_dan: str, task: str = "pose"):
    """Nạp một mô hình YOLO của ultralytics.

    Tách thành hàm riêng ở mức module để ca kiểm thử monkeypatch được mà KHÔNG cần
    `ultralytics`/`torch`/`ncnn` thật (§7.2 đặc tả: ba gói này không có trong container
    ARM64, import ở mức module làm `pytest` chết ngay khâu thu thập).

    Args:
        duong_dan: Đường dẫn tệp .pt hoặc thư mục NCNN.
        task: Loại bài toán, luôn là "pose" cho YOLOv8n-face.

    Returns:
        Đối tượng `ultralytics.YOLO` đã nạp.
    """
    from ultralytics import YOLO

    return YOLO(duong_dan, task=task)


def _phien_ban_goi(ten: str) -> str:
    """Lấy phiên bản một gói qua metadata, không import gói đó.

    Trả về "khong-xac-dinh" nếu gói không được cài (trường hợp container ARM64 với các
    gói chỉ dành cho máy phát triển) — khoá vẫn hiện diện trong .meta.json.
    """
    try:
        return importlib.metadata.version(ten)
    except importlib.metadata.PackageNotFoundError:
        return "khong-xac-dinh"


def _lay_phien_ban_thu_vien_ncnn() -> dict:
    """Phiên bản các thư viện dùng để export NCNN, cho .meta.json (R17).

    Khác `_lay_phien_ban_thu_vien` của P2-01: có `ncnn`, không có `onnx`/`onnxruntime`.
    """
    return {ten: _phien_ban_goi(ten) for ten in _GOI_GHI_PHIEN_BAN}


def _ten_tep_ket_qua_ncnn(thoi_diem: datetime.datetime) -> str:
    """Sinh tên tệp kết quả theo quy ước `export_ncnn_<YYYYMMDD_HHMM>.json` (§7.4)."""
    return f"export_ncnn_{thoi_diem.strftime('%Y%m%d_%H%M')}.json"


def _bao_dam_ncnn_co_diem_moc(ket_qua) -> None:
    """Ném `LoiMoHinh` nếu bản NCNN có khung bao nhưng thiếu điểm mốc (§7.3 đặc tả).

    Đây là chỗ hỏng đắt nhất của mã việc: nếu đường PyTorch→PNNX→NCNN đánh rơi nhánh
    pose, `keypoints` sẽ là `None` trong khi vẫn có `boxes`. TUYỆT ĐỐI không được thay
    bằng mảng 0 rồi tính tiếp — sai số điểm mốc khi đó thành một con số lớn trông như
    lỗi độ chính xác, che mất nguyên nhân thật. `preprocess.py` và `align.py` đều ăn
    năm điểm mốc từ khối phát hiện.

    Args:
        ket_qua: Một đối tượng `Results` của ultralytics từ bản NCNN.

    Raises:
        LoiMoHinh: có khung bao nhưng `keypoints` là `None` hoặc rỗng.
    """
    co_khung = ket_qua.boxes is not None and len(ket_qua.boxes) > 0
    if not co_khung:
        return

    kp = ket_qua.keypoints
    thieu_diem_moc = kp is None or kp.xy is None or len(kp.xy) == 0
    if thieu_diem_moc:
        raise LoiMoHinh(
            "Bản NCNN phát hiện được khuôn mặt nhưng KHÔNG trả về điểm mốc — đường "
            "chuyển đổi PyTorch→PNNX→NCNN đã đánh rơi nhánh xử lý pose. Cần sửa bước "
            "export, không được nới ngưỡng hay bỏ qua."
        )


def export_ncnn_mot_kich_thuoc(
    weights: Path,
    imgsz: int,
    batch: int,
    out_dir: Path,
    dry_run: bool = False,
) -> Path:
    """Export trọng số .pt sang NCNN ở một độ phân giải.

    `ultralytics` đặt kết quả cạnh trọng số nguồn với tên `<stem>_ncnn_model`; hàm này
    đổi tên THƯ MỤC đó về quy ước `<out_dir>/yolov8n-face-<imgsz>_ncnn_model`, giữ nguyên
    vẹn tên các tệp bên trong (§4 đặc tả). Export lần hai ghi đè được thư mục cũ.

    Không truyền `export.opset`/`export.simplify` — hai tham số đó không áp dụng cho NCNN.

    Args:
        weights: Đường dẫn trọng số nguồn (.pt).
        imgsz: Độ phân giải ảnh vuông dùng để export.
        batch: Kích thước lô cố định của đồ thị xuất ra.
        out_dir: Thư mục ghi kết quả export.
        dry_run: Chỉ tính đường dẫn dự kiến, không thực sự export.

    Returns:
        Đường dẫn THƯ MỤC `<out_dir>/yolov8n-face-<imgsz>_ncnn_model`. Với dry_run trả về
        đường dẫn dự kiến, không tạo gì.

    Raises:
        LoiMoHinh: không tìm thấy trọng số nguồn, chưa cài gói `ncnn`, hoặc export thất bại.
    """
    weights = Path(weights)
    if not weights.exists():
        raise LoiMoHinh(f"Không tìm thấy trọng số nguồn: {weights}")

    duong_dan_ra = Path(out_dir) / f"yolov8n-face-{imgsz}_ncnn_model"

    if dry_run:
        logger.info(
            "[DRY-RUN] Sẽ export '%s' (imgsz=%d) sang NCNN ra '%s'",
            weights,
            imgsz,
            duong_dan_ra,
        )
        return duong_dan_ra

    if importlib.util.find_spec("ncnn") is None:
        raise LoiMoHinh(
            "Chưa cài gói 'ncnn' — cần cho cả export lẫn kiểm chứng NCNN. "
            "Khắc phục: pip install ncnn"
        )

    mo_hinh = _tao_mo_hinh_yolo(str(weights))
    try:
        ket_qua_export = Path(mo_hinh.export(format="ncnn", imgsz=imgsz, batch=batch))
    except (RuntimeError, OSError, ValueError, TypeError, ImportError) as e:
        raise LoiMoHinh(f"Export NCNN thất bại cho imgsz={imgsz}: {e}") from e

    Path(out_dir).mkdir(parents=True, exist_ok=True)
    if ket_qua_export.resolve() != duong_dan_ra.resolve():
        if duong_dan_ra.exists():
            shutil.rmtree(duong_dan_ra)
        shutil.move(str(ket_qua_export), str(duong_dan_ra))

    logger.info("Đã export NCNN xong: %s", duong_dan_ra)
    return duong_dan_ra


def kiem_tra_thu_muc_ncnn(thu_muc: Path) -> dict:
    """Kiểm thư mục NCNN có đủ ba tệp bắt buộc và không tệp nào rỗng.

    Args:
        thu_muc: Thư mục `<...>_ncnn_model` cần kiểm.

    Returns:
        Từ điển gồm `param`, `bin`, `metadata` (đường dẫn từng tệp) và
        `tong_kich_thuoc_byte`.

    Raises:
        LoiMoHinh: thư mục không tồn tại, thiếu tệp bắt buộc, hoặc có tệp kích thước 0.
    """
    thu_muc = Path(thu_muc)
    if not thu_muc.exists() or not thu_muc.is_dir():
        raise LoiMoHinh(f"Thư mục NCNN không tồn tại hoặc không phải thư mục: {thu_muc}")

    for ten_tep in _TEP_NCNN_BAT_BUOC:
        if not (thu_muc / ten_tep).exists():
            raise LoiMoHinh(f"Thư mục NCNN thiếu tệp bắt buộc: {ten_tep}")

    for ten_tep in _TEP_NCNN_BAT_BUOC:
        if (thu_muc / ten_tep).stat().st_size == 0:
            raise LoiMoHinh(f"Tệp NCNN rỗng (0 byte): {ten_tep}")

    param = thu_muc / "model.ncnn.param"
    tep_bin = thu_muc / "model.ncnn.bin"
    metadata = thu_muc / "metadata.yaml"
    tong = sum(p.stat().st_size for p in (param, tep_bin, metadata))

    return {
        "param": param,
        "bin": tep_bin,
        "metadata": metadata,
        "tong_kich_thuoc_byte": tong,
    }


def kiem_chung_tuong_duong_ncnn(
    weights_pt: Path,
    thu_muc_ncnn: Path,
    danh_sach_anh: list[Path],
    imgsz: int,
    conf: float,
    iou: float,
    sai_so_diem_moc_toi_da: float,
) -> dict:
    """Chạy bản .pt và bản NCNN trên cùng tập ảnh, tổng hợp số đo.

    Nạp bản NCNN BẮT BUỘC chỉ định `task="pose"` — cùng lý do đã ghi ở
    `kiem_chung_tuong_duong` của P2-01: đồ thị không mang theo tên lớp và `kpt_shape`,
    thiếu `task` thì ultralytics đoán thành 'detect' và bỏ hậu xử lý pose.

    `iou` chỉ dùng làm ngưỡng NMS khi chạy suy luận (khớp `inference.iou_threshold`); ngưỡng
    IoU để ĐÁNH GIÁ độ khớp giữa hai mô hình lấy từ hằng số `NGUONG_IOU_TOI_THIEU` (§7.3).

    Args:
        weights_pt: Đường dẫn trọng số .pt gốc.
        thu_muc_ncnn: Thư mục NCNN đã export cần kiểm chứng.
        danh_sach_anh: Danh sách ảnh dùng để so sánh.
        imgsz: Độ phân giải suy luận, phải khớp độ phân giải đã export.
        conf: Ngưỡng độ tin cậy khi suy luận.
        iou: Ngưỡng NMS khi suy luận.
        sai_so_diem_moc_toi_da: Ngưỡng sai số điểm mốc tối đa, đơn vị pixel.

    Returns:
        Từ điển gồm bảy khoá như `kiem_chung_tuong_duong` của P2-01 (`n_anh`,
        `n_khop_so_mat`, `iou_trung_binh`, `iou_nho_nhat`, `sai_so_diem_moc_trung_binh`,
        `sai_so_diem_moc_lon_nhat`, `dat`), cộng `thu_muc_ncnn`.

    Raises:
        LoiCauHinh: `danh_sach_anh` rỗng.
        LoiMoHinh: bản NCNN phát hiện được khuôn mặt nhưng KHÔNG trả về điểm mốc.
    """
    if not danh_sach_anh:
        raise LoiCauHinh("Danh sách ảnh kiểm chứng rỗng, không thể tính số đo trung bình")

    mo_hinh_pt = _tao_mo_hinh_yolo(str(weights_pt))
    mo_hinh_ncnn = _tao_mo_hinh_yolo(str(thu_muc_ncnn))

    n_anh = len(danh_sach_anh)
    n_khop_so_mat = 0
    danh_sach_iou: list[float] = []
    danh_sach_sai_so: list[float] = []

    for anh in danh_sach_anh:
        kq_pt = mo_hinh_pt.predict(source=str(anh), imgsz=imgsz, conf=conf, iou=iou, verbose=False)[
            0
        ]
        kq_ncnn = mo_hinh_ncnn.predict(
            source=str(anh), imgsz=imgsz, conf=conf, iou=iou, verbose=False
        )[0]

        _bao_dam_ncnn_co_diem_moc(kq_ncnn)

        khung_pt, diem_pt = _trich_khung_diem_moc(kq_pt)
        khung_ncnn, diem_ncnn = _trich_khung_diem_moc(kq_ncnn)

        kq = so_sanh_mot_anh(
            khung_pt,
            diem_pt,
            khung_ncnn,
            diem_ncnn,
            NGUONG_IOU_TOI_THIEU,
            sai_so_diem_moc_toi_da,
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
        "thu_muc_ncnn": str(thu_muc_ncnn),
    }


def xac_dinh_moi_truong() -> str:
    """Trả về mã môi trường chạy: 'pc_x86' | 'docker_arm64' | 'pi5'.

    Quy tắc (`experiment-protocol.instructions.md` §2): có `/.dockerenv` → `docker_arm64`;
    kiến trúc máy là aarch64/arm64 → `pi5`; còn lại → `pc_x86`. Script tự suy ra, KHÔNG
    nhận từ tham số dòng lệnh — người gõ tay thì sớm muộn cũng gõ nhầm, mà nhầm ở đây
    không có gì báo lỗi và làm mất nguyên một cột trong bảng so sánh môi trường.

    Kiểm `/.dockerenv` trước kiến trúc: container ARM64 vừa có tệp đó vừa là aarch64, và
    ở ngữ cảnh mã việc này nó là môi trường giả lập, không phải Pi 5 thật.

    Returns:
        Đúng một trong ba chuỗi `"pc_x86"`, `"docker_arm64"`, `"pi5"`.
    """
    if Path("/.dockerenv").exists():
        return "docker_arm64"
    if platform.machine().lower() in ("aarch64", "arm64"):
        return "pi5"
    return "pc_x86"


def thu_thap_metadata_ncnn(cfg_tho: dict, seed: int) -> dict:
    """Gom metadata theo R17: commit, cấu hình, phiên bản thư viện, thiết bị, thời điểm, seed.

    Hai điểm khác `_thu_thap_metadata` của P2-01: phần `phien_ban` phải có `ncnn` và không
    cần `onnx`/`onnxruntime`; bản ghi phải có thêm khoá `moi_truong` lấy từ
    `xac_dinh_moi_truong()` (`experiment-protocol.instructions.md` §2).

    Args:
        cfg_tho: Cấu hình thô đã nạp từ YAML (chưa qua `doc_cau_hinh`).
        seed: Seed dùng để chọn mẫu ảnh, ghi lại để tái lập (R15).

    Returns:
        Từ điển bảy khoá: `commit`, `cau_hinh`, `phien_ban`, `thiet_bi`, `thoi_diem`, `seed`,
        `moi_truong`.
    """
    return {
        "commit": _lay_git_commit_hash(),
        "cau_hinh": cfg_tho,
        "phien_ban": _lay_phien_ban_thu_vien_ncnn(),
        "thiet_bi": {"hostname": platform.node(), "he_dieu_hanh": platform.platform()},
        "thoi_diem": datetime.datetime.now().astimezone().isoformat(),
        "seed": seed,
        "moi_truong": xac_dinh_moi_truong(),
    }


def _in_bang_ket_qua(ket_qua_theo_kich_thuoc: dict) -> None:
    """In bảng Markdown tóm tắt kết quả kiểm chứng ra stdout (G2 — phần in bảng CLI)."""
    print("\n### KẾT QUẢ KIỂM CHỨNG TƯƠNG ĐƯƠNG EXPORT NCNN")
    print(
        "| Kích thước | Số ảnh | Khớp số mặt | IoU TB | IoU min | "
        "Sai số mốc TB (px) | Sai số mốc max (px) | Đạt |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for imgsz, kq in ket_qua_theo_kich_thuoc.items():
        # Ký hiệu khoa học, không làm tròn về 0.00 / 1.0000 (CẦN SỬA-1, R5): bảng này người
        # đọc chép thẳng vào báo cáo, phải giữ đúng bậc độ lớn của thứ đã đo.
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
        print(
            f"| {imgsz} | {kq['n_anh']} | {kq['n_khop_so_mat']} | {iou_tb} | {iou_min} | "
            f"{ss_tb} | {ss_max} | {'DAT' if kq['dat'] else 'KHONG DAT'} |"
        )


def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 nếu thành công, 1 nếu thất bại."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=(
            "Export trọng số YOLOv8n-face .pt sang NCNN và kiểm chứng bằng số đo rằng bản "
            "NCNN cho kết quả tương đương bản gốc (xem docs/dac-ta/P2-04-export-ncnn.md)."
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

    # `export.opset` và `export.simplify` KHÔNG áp dụng cho NCNN (§4 đặc tả): `doc_cau_hinh`
    # vẫn đọc và kiểm chúng vì dùng chung hàm với P2-01, nhưng script này không truyền chúng
    # đi đâu. Chỉ dùng `weights_pt`, `kich_thuoc`, `batch`, `out_dir`, và hai ngưỡng suy luận.
    weights_pt = Path(cfg["weights_pt"])
    out_dir = Path(cfg["out_dir"])

    if args.dry_run:
        print("\n### BẢNG KẾ HOẠCH EXPORT NCNN (DRY-RUN)")
        print("| Kích thước | Thư mục NCNN dự kiến |")
        print("|---|---|")
        for imgsz in cfg["kich_thuoc"]:
            duong_dan = export_ncnn_mot_kich_thuoc(
                weights_pt, imgsz, cfg["batch"], out_dir, dry_run=True
            )
            print(f"| {imgsz} | `{duong_dan}` |")
        print(
            f"\nẢnh kiểm chứng : `{args.anh_dir}` " f"(lấy mẫu {args.so_anh}, seed {args.seed})\n"
        )
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
            thu_muc_ncnn = export_ncnn_mot_kich_thuoc(weights_pt, imgsz, cfg["batch"], out_dir)
            kiem_tra_thu_muc_ncnn(thu_muc_ncnn)
            kq = kiem_chung_tuong_duong_ncnn(
                weights_pt,
                thu_muc_ncnn,
                danh_sach_anh,
                imgsz,
                cfg["conf_threshold"],
                cfg["iou_threshold"],
                NGUONG_SAI_SO_DIEM_MOC_TOI_DA_PX,
            )
            ket_qua_theo_kich_thuoc[str(imgsz)] = kq
    except LoiMoHinh as e:
        logger.error("Export hoặc kiểm chứng NCNN thất bại: %s", e)
        return 1

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
    dat_tat_ca = bool(ket_qua_theo_kich_thuoc) and all(
        kq["dat"] for kq in ket_qua_theo_kich_thuoc.values()
    )

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
        "meta": thu_thap_metadata_ncnn(cfg_tho, args.seed),
    }

    duong_dan_ra = Path("results") / _ten_tep_ket_qua_ncnn(datetime.datetime.now().astimezone())

    try:
        ghi_ket_qua(duong_dan_ra, ban_ghi)
    except LoiCauHinh as e:
        logger.error("Không ghi được kết quả: %s", e)
        return 1

    _in_bang_ket_qua(ket_qua_theo_kich_thuoc)
    print(f"\nKết quả đầy đủ: `{duong_dan_ra}`\n")

    return 0 if dat_tat_ca else 1


if __name__ == "__main__":
    sys.exit(main())
