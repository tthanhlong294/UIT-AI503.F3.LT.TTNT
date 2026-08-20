"""Mẻ tiền xử lý ảnh khuôn mặt: phát hiện → lọc chất lượng → căn chỉnh → ghi manifest.

Xem docs/dac-ta/P1-05-preprocess.md. Áp dụng đồng nhất cho cả bốn nguồn dữ liệu (gallery, LFW gốc,
LFW đã domain-adapt, in-domain) — dùng chung một quy trình là điều kiện để phép kiểm chứng domain
adaptation ở Phase 3 có giá trị.

⚠️ Phân biệt HAI loại lỗi trong vòng lặp mẻ (§3 của đặc tả) — đây là điều kiện tiên quyết:
  - `ValueError` (từ `align.can_chinh`, `detector.detect`, `kiem_hinh_hoc_diem_moc`): MỘT ảnh
    hỏng — bỏ qua ảnh đó, ghi lý do vào manifest, chạy tiếp.
  - `LoiCauHinh` / `LoiMoHinh`: lỗi áp dụng cho MỌI ảnh — dừng cả mẻ ngay, trả về 1.
TUYỆT ĐỐI KHÔNG được bắt gộp mọi ngoại lệ (không chỉ định đích danh `ValueError`) trong vòng lặp
mẻ: bắt gộp sẽ biến một lỗi cấu hình thành "bỏ qua ảnh này" và mẻ trôi im lặng qua toàn bộ dữ liệu.
"""

import sys
from pathlib import Path

# Thêm gốc dự án vào sys.path để cho phép chạy trực tiếp kịch bản
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import csv
import random

import cv2
import numpy as np

from src.common.config import lay_gia_tri, nap_cau_hinh
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger
from src.detector import YoloFaceDetector
from src.preprocess.align import can_chinh

logger = lay_logger(__name__)

# Đuôi tệp được coi là ảnh khi quét thư mục nguồn.
_DINH_DANG_ANH_HOP_LE = {".jpg", ".jpeg", ".png"}

# Bảy cột manifest, đúng thứ tự — xem §8 đặc tả.
_COT_MANIFEST = ["file_vao", "file_ra", "ly_do", "n_faces", "conf", "bbox_w", "bbox_h"]

# Sáu lý do chốt, đúng thứ tự kiểm — xem §7 đặc tả. Không được thêm bớt.
_DANH_SACH_LY_DO: tuple[str, ...] = (
    "ok",
    "khong_doc_duoc_anh",
    "khong_thay_mat",
    "mat_qua_nho",
    "do_tin_cay_thap",
    "diem_moc_bat_thuong",
)

# Đuôi tệp ảnh ra — luôn cố định, không phụ thuộc đuôi ảnh nguồn (§8 đặc tả).
_DUOI_ANH_RA = ".png"


def liet_ke_anh(thu_muc: Path) -> list[Path]:
    """Liệt kê mọi ảnh trong thư mục, đệ quy, sắp xếp ổn định.

    Nhận các đuôi `.jpg`, `.jpeg`, `.png` (không phân biệt hoa thường).

    Args:
        thu_muc: Thư mục gốc chứa ảnh, quét đệ quy.

    Returns:
        Danh sách đường dẫn ảnh, đã sắp xếp, thứ tự ổn định giữa các lần gọi.

    Raises:
        LoiCauHinh: thư mục không tồn tại, hoặc không có ảnh nào hợp lệ bên trong.
    """
    thu_muc = Path(thu_muc)
    if not thu_muc.exists() or not thu_muc.is_dir():
        raise LoiCauHinh(f"Thư mục ảnh nguồn không tồn tại hoặc không phải thư mục: '{thu_muc}'")

    danh_sach = sorted(
        p for p in thu_muc.rglob("*") if p.is_file() and p.suffix.lower() in _DINH_DANG_ANH_HOP_LE
    )
    if not danh_sach:
        raise LoiCauHinh(f"Thư mục ảnh nguồn '{thu_muc}' không có ảnh nào hợp lệ")

    return danh_sach


def kiem_hinh_hoc_diem_moc(diem_moc: np.ndarray, min_ti_le_lech_mui: float) -> bool:
    """Kiểm năm điều kiện hình học của 5 điểm mốc khuôn mặt.

    Bốn bất biến thứ tự (điều kiện CẦN, không ĐỦ — xem §6 đặc tả):
      1. mắt trái có x nhỏ hơn mắt phải.
      2. hai mắt nằm trên mũi (y nhỏ hơn).
      3. mũi nằm trên miệng (y nhỏ hơn).
      4. khoé miệng trái có x nhỏ hơn khoé miệng phải.

    Điều kiện thứ năm — chống suy biến, lớp bảo vệ DUY NHẤT vì `align.can_chinh` không tự phát
    hiện được điểm mốc thẳng hàng: khoảng cách vuông góc từ mũi tới đường nối hai mắt, chia cho
    khoảng cách giữa hai mắt, phải lớn hơn hoặc bằng `min_ti_le_lech_mui`.

    Args:
        diem_moc: Mảng 5 điểm mốc, hình dạng (5, 2), thứ tự mắt trái, mắt phải, mũi, khoé miệng
            trái, khoé miệng phải.
        min_ti_le_lech_mui: Ngưỡng tối thiểu cho tỉ lệ lệch mũi (điều kiện thứ năm).

    Returns:
        True nếu thoả cả năm điều kiện, False nếu vi phạm bất kỳ điều nào.

    Raises:
        ValueError: `diem_moc` sai hình dạng (phải là (5, 2)); hoặc hai mắt trùng nhau khiến
            mẫu số của tỉ lệ lệch mũi bằng 0.
    """
    if not isinstance(diem_moc, np.ndarray) or diem_moc.shape != (5, 2):
        raise ValueError(
            f"diem_moc phải là numpy.ndarray hình dạng (5, 2), "
            f"nhận {getattr(diem_moc, 'shape', type(diem_moc))}"
        )

    mat_trai, mat_phai, mui, mieng_trai, mieng_phai = diem_moc

    vecto_hai_mat = mat_phai - mat_trai
    do_dai_hai_mat = float(np.hypot(vecto_hai_mat[0], vecto_hai_mat[1]))
    if do_dai_hai_mat == 0.0:
        raise ValueError("Hai mắt trùng nhau, không tính được tỉ lệ lệch mũi (mẫu số bằng 0)")

    if not (mat_trai[0] < mat_phai[0]):
        return False
    if not (max(mat_trai[1], mat_phai[1]) < mui[1]):
        return False
    if not (mui[1] < min(mieng_trai[1], mieng_phai[1])):
        return False
    if not (mieng_trai[0] < mieng_phai[0]):
        return False

    khoang_cach_vuong_goc = (
        abs(vecto_hai_mat[0] * (mui[1] - mat_trai[1]) - vecto_hai_mat[1] * (mui[0] - mat_trai[0]))
        / do_dai_hai_mat
    )
    ti_le_lech_mui = khoang_cach_vuong_goc / do_dai_hai_mat

    return bool(ti_le_lech_mui >= min_ti_le_lech_mui)


def _lay_so_thuc(cfg: dict, khoa: str) -> float:
    """Đọc một tham số số thực từ cấu hình tiền xử lý, kiểm kiểu nghiêm ngặt.

    `lay_gia_tri` chỉ bảo đảm khoá tồn tại, không bảo đảm kiểu — hàm này bổ sung phần đó,
    để một cấu hình sai kiểu (chuỗi, `null`, ...) ném `LoiCauHinh` thay vì để `TypeError`/
    `UFuncTypeError` của Python/NumPy lọt ra ngoài `main()`.

    Args:
        cfg: Toàn bộ nội dung `configs/preprocess.yaml` đã nạp.
        khoa: Đường dẫn khoá dạng `"a.b.c"`, truyền thẳng cho `lay_gia_tri`.

    Returns:
        Giá trị đã ép về `float`.

    Raises:
        LoiCauHinh: giá trị không phải kiểu số (loại trừ `bool`, vì `bool` là subclass của `int`
            trong Python nên `isinstance(True, int)` là `True`).
    """
    gia_tri = lay_gia_tri(cfg, khoa)
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, (int, float)):
        raise LoiCauHinh(f"Cấu hình '{khoa}' phải là số, nhận {gia_tri!r}")
    return float(gia_tri)


def _lay_bool(cfg: dict, khoa: str) -> bool:
    """Đọc một tham số kiểu bool từ cấu hình tiền xử lý, kiểm kiểu nghiêm ngặt.

    Args:
        cfg: Toàn bộ nội dung `configs/preprocess.yaml` đã nạp.
        khoa: Đường dẫn khoá dạng `"a.b.c"`, truyền thẳng cho `lay_gia_tri`.

    Returns:
        Giá trị `bool`.

    Raises:
        LoiCauHinh: giá trị không phải kiểu `bool`.
    """
    gia_tri = lay_gia_tri(cfg, khoa)
    if not isinstance(gia_tri, bool):
        raise LoiCauHinh(f"Cấu hình '{khoa}' phải là true/false, nhận {gia_tri!r}")
    return gia_tri


def xu_ly_mot_anh(
    duong_dan: Path,
    detector,
    cfg_preprocess: dict,
) -> tuple[np.ndarray | None, str, dict]:
    """Xử lý MỘT ảnh: đọc, phát hiện, lọc, căn chỉnh.

    Thứ tự kiểm đúng thứ tự bảng lý do ở §7 đặc tả: đọc ảnh → phát hiện → cỡ khung bao → độ
    tin cậy → hình học điểm mốc → căn chỉnh. Ảnh vi phạm nhiều điều kiện nhận lý do của điều
    kiện kiểm trước nhất.

    Args:
        duong_dan: Đường dẫn ảnh nguồn.
        detector: Đối tượng có phương thức `detect(anh) -> list[FaceBox]`.
        cfg_preprocess: Toàn bộ nội dung `configs/preprocess.yaml`.

    Returns:
        Tuple `(ảnh_đã_căn_chỉnh, lý_do, thông_tin)`. `ảnh_đã_căn_chỉnh` là `None` khi ảnh bị
        bỏ qua. `lý_do` là một trong sáu chuỗi ở `_DANH_SACH_LY_DO`. `thông_tin` gồm `n_faces`,
        `conf`, `bbox_w`, `bbox_h` — rỗng khi chưa xác định được (đọc ảnh lỗi, phát hiện lỗi).

    Raises:
        LoiCauHinh: cấu hình sai — áp dụng cho MỌI ảnh, để lan lên trên, KHÔNG bắt ở đây.

    Không ném `ValueError` cho lỗi dữ liệu của một ảnh — luôn trả về lý do thay vào đó.
    """
    thong_tin: dict = {}

    anh = cv2.imread(str(duong_dan))
    if anh is None:
        return None, "khong_doc_duoc_anh", thong_tin

    min_bbox_px = _lay_so_thuc(cfg_preprocess, "loc_chat_luong.min_bbox_px")
    min_confidence = _lay_so_thuc(cfg_preprocess, "loc_chat_luong.min_confidence")
    bat_kiem_hinh_hoc = _lay_bool(cfg_preprocess, "loc_chat_luong.kiem_hinh_hoc_diem_moc")
    min_ti_le_lech_mui = _lay_so_thuc(cfg_preprocess, "loc_chat_luong.min_ti_le_lech_mui")

    try:
        khuon_mat = detector.detect(anh)
    except ValueError as e:
        logger.warning("Ảnh không dùng được cho khối phát hiện, bỏ qua: %s (%s)", duong_dan, e)
        return None, "khong_doc_duoc_anh", thong_tin

    if not khuon_mat:
        return None, "khong_thay_mat", thong_tin

    # Nhiều khuôn mặt: chọn khuôn mặt có DIỆN TÍCH khung bao lớn nhất; diện tích bằng nhau thì
    # chọn khuôn mặt có độ tin cậy cao hơn (§7 đặc tả, sửa 20/08/2026 — luật cũ "tin cậy cao
    # nhất" đã ghi nhầm người ở 5/198 ảnh mẻ thật vì độ tin cậy không đo mức quan trọng của đối
    # tượng). Danh sách từ detector chỉ được sắp theo confidence giảm dần — KHÔNG được giả định
    # đã sắp theo diện tích.
    mat = max(khuon_mat, key=lambda m: (m.dien_tich, m.confidence))
    thong_tin["n_faces"] = len(khuon_mat)
    thong_tin["conf"] = mat.confidence
    thong_tin["bbox_w"] = mat.chieu_rong
    thong_tin["bbox_h"] = mat.chieu_cao

    if min(mat.chieu_rong, mat.chieu_cao) < min_bbox_px:
        return None, "mat_qua_nho", thong_tin

    if mat.confidence < min_confidence:
        return None, "do_tin_cay_thap", thong_tin

    if bat_kiem_hinh_hoc:
        try:
            hinh_hoc_hop_le = kiem_hinh_hoc_diem_moc(mat.landmarks, min_ti_le_lech_mui)
        except ValueError as e:
            logger.warning("Điểm mốc bất thường, bỏ qua ảnh: %s (%s)", duong_dan, e)
            return None, "diem_moc_bat_thuong", thong_tin
        if not hinh_hoc_hop_le:
            return None, "diem_moc_bat_thuong", thong_tin

    try:
        anh_can_chinh = can_chinh(anh, mat.landmarks, cfg_preprocess)
    except ValueError as e:
        logger.warning("Điểm mốc không căn chỉnh được, bỏ qua ảnh: %s (%s)", duong_dan, e)
        return None, "diem_moc_bat_thuong", thong_tin

    return anh_can_chinh, "ok", thong_tin


def ghi_manifest(duong_dan: Path, ban_ghi: list[dict]) -> None:
    """Ghi manifest.csv, bảy cột đúng thứ tự `_COT_MANIFEST`.

    Kiểm đủ khoá cho TOÀN BỘ bản ghi trước khi mở tệp để ghi — tránh ghi một tệp dở dang khi
    một bản ghi ở giữa danh sách bị thiếu khoá.

    Args:
        duong_dan: Đường dẫn tệp manifest.csv cần ghi.
        ban_ghi: Danh sách bản ghi, mỗi phần tử là một dict đủ bảy khoá của `_COT_MANIFEST`.

    Raises:
        LoiCauHinh: một bản ghi bất kỳ thiếu khoá bắt buộc.
    """
    for i, ban in enumerate(ban_ghi):
        thieu = [cot for cot in _COT_MANIFEST if cot not in ban]
        if thieu:
            raise LoiCauHinh(f"Bản ghi manifest thứ {i} thiếu khoá bắt buộc: {', '.join(thieu)}")

    duong_dan = Path(duong_dan)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)

    with open(duong_dan, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_COT_MANIFEST)
        for ban in ban_ghi:
            writer.writerow([ban[cot] for cot in _COT_MANIFEST])

    logger.info("Đã ghi manifest: %s (%d dòng)", duong_dan, len(ban_ghi))


def _chon_gioi_han(danh_sach: list[Path], gioi_han: int, seed: int) -> list[Path]:
    """Chọn ngẫu nhiên có tái lập `gioi_han` ảnh từ `danh_sach` (R15).

    Args:
        danh_sach: Danh sách đường dẫn ảnh đầy đủ.
        gioi_han: Số ảnh cần chọn.
        seed: Seed cho bộ sinh ngẫu nhiên cục bộ, đảm bảo tái lập được.

    Returns:
        Danh sách con đã chọn, đã sắp xếp lại để đầu ra ổn định.
    """
    rng = random.Random(seed)
    so_luong = min(gioi_han, len(danh_sach))
    return sorted(rng.sample(danh_sach, so_luong))


def _xay_dung_parser() -> argparse.ArgumentParser:
    """Dựng argparse cho script, theo đúng giao diện dòng lệnh ở §5 đặc tả."""
    parser = argparse.ArgumentParser(
        description=(
            "Tiền xử lý một mẻ ảnh khuôn mặt: phát hiện, lọc chất lượng, căn chỉnh về kích "
            "thước chuẩn, ghi manifest.csv (xem docs/dac-ta/P1-05-preprocess.md)."
        )
    )
    parser.add_argument("--vao", default=None, help="Thư mục ảnh nguồn (bắt buộc)")
    parser.add_argument("--ra", default=None, help="Thư mục ảnh đích (bắt buộc)")
    parser.add_argument(
        "--model", default="models/yolov8n-face-320.onnx", help="Tệp ONNX dùng để phát hiện"
    )
    parser.add_argument(
        "--config-preprocess",
        default="configs/preprocess.yaml",
        help="Đường dẫn cấu hình căn chỉnh và lọc chất lượng",
    )
    parser.add_argument(
        "--config-detect",
        default="configs/detect.yaml",
        help="Đường dẫn cấu hình bộ phát hiện khuôn mặt",
    )
    parser.add_argument(
        "--gioi-han",
        type=int,
        default=0,
        help="Chỉ xử lý N ảnh (0 = không giới hạn), chọn ngẫu nhiên có seed để chạy thử nhanh",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed khi --gioi-han chọn mẫu (R15)")
    parser.add_argument(
        "--tiep-tuc",
        action="store_true",
        help="Bỏ qua ảnh đã có sẵn ở đích, chạy tiếp một mẻ dang dở",
    )
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in kế hoạch, không ghi tệp nào")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 thành công, 1 thất bại."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = _xay_dung_parser().parse_args(argv)

    if args.vao is None or args.ra is None:
        logger.error("Thiếu tham số bắt buộc --vao và/hoặc --ra")
        print("Thiếu tham số bắt buộc: --vao và --ra đều là bắt buộc.")
        return 1

    vao_dir = Path(args.vao)
    ra_dir = Path(args.ra)

    try:
        cfg_preprocess = nap_cau_hinh(args.config_preprocess)
        cfg_detect = nap_cau_hinh(args.config_detect)
    except LoiCauHinh as e:
        logger.error("Không đọc được cấu hình: %s", e)
        print(f"Không đọc được cấu hình: {e}")
        return 1

    try:
        danh_sach_anh = liet_ke_anh(vao_dir)
    except LoiCauHinh as e:
        logger.error("Không liệt kê được ảnh nguồn: %s", e)
        print(str(e))
        return 1

    if args.gioi_han > 0:
        danh_sach_anh = _chon_gioi_han(danh_sach_anh, args.gioi_han, args.seed)

    if args.dry_run:
        print("\n### BẢNG KẾ HOẠCH TIỀN XỬ LÝ (DRY-RUN)")
        print(f"- Thư mục vào : `{vao_dir}`")
        print(f"- Thư mục ra  : `{ra_dir}`")
        print(f"- Số ảnh      : `{len(danh_sach_anh)}`")
        print(f"- Mô hình     : `{args.model}`")
        print(f"- Tiếp tục mẻ dở : `{args.tiep_tuc}`")
        print(f"- Seed        : `{args.seed}`\n")
        return 0

    try:
        detector = YoloFaceDetector(args.model, cfg_detect)
    except LoiMoHinh as e:
        logger.error("Không nạp được mô hình phát hiện: %s", e)
        print(f"Không nạp được mô hình '{args.model}': {e}")
        return 1
    except LoiCauHinh as e:
        logger.error("Cấu hình phát hiện hỏng: %s", e)
        print(f"Cấu hình phát hiện '{args.config_detect}' hỏng: {e}")
        return 1

    ban_ghi: list[dict] = []
    dem_theo_ly_do = dict.fromkeys(_DANH_SACH_LY_DO, 0)

    try:
        for duong_dan in danh_sach_anh:
            duong_dan_vao_rel = duong_dan.relative_to(vao_dir)
            duong_dan_ra_rel = duong_dan_vao_rel.with_suffix(_DUOI_ANH_RA)
            duong_dan_ra_abs = ra_dir / duong_dan_ra_rel

            if args.tiep_tuc and duong_dan_ra_abs.exists():
                dem_theo_ly_do["ok"] += 1
                ban_ghi.append(
                    {
                        "file_vao": duong_dan_vao_rel.as_posix(),
                        "file_ra": duong_dan_ra_rel.as_posix(),
                        "ly_do": "ok",
                        "n_faces": "",
                        "conf": "",
                        "bbox_w": "",
                        "bbox_h": "",
                    }
                )
                continue

            anh_ra, ly_do, thong_tin = xu_ly_mot_anh(duong_dan, detector, cfg_preprocess)
            dem_theo_ly_do[ly_do] += 1

            if anh_ra is None:
                ban_ghi.append(
                    {
                        "file_vao": duong_dan_vao_rel.as_posix(),
                        "file_ra": "",
                        "ly_do": ly_do,
                        "n_faces": thong_tin.get("n_faces", ""),
                        "conf": thong_tin.get("conf", ""),
                        "bbox_w": thong_tin.get("bbox_w", ""),
                        "bbox_h": thong_tin.get("bbox_h", ""),
                    }
                )
                continue

            duong_dan_ra_abs.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(duong_dan_ra_abs), anh_ra)

            ban_ghi.append(
                {
                    "file_vao": duong_dan_vao_rel.as_posix(),
                    "file_ra": duong_dan_ra_rel.as_posix(),
                    "ly_do": "ok",
                    "n_faces": thong_tin.get("n_faces", ""),
                    "conf": thong_tin.get("conf", ""),
                    "bbox_w": thong_tin.get("bbox_w", ""),
                    "bbox_h": thong_tin.get("bbox_h", ""),
                }
            )

        duong_dan_manifest = ra_dir / "manifest.csv"
        ghi_manifest(duong_dan_manifest, ban_ghi)
    except LoiCauHinh as e:
        logger.error("Cấu hình hỏng giữa mẻ — dừng ngay, không ghi manifest: %s", e)
        print(f"Cấu hình hỏng, dừng mẻ ngay: {e}")
        return 1

    tong = len(ban_ghi)
    print("\n### BẢNG TỔNG KẾT TIỀN XỬ LÝ")
    print("| Lý do | Số lượng | Tỉ lệ |")
    print("|---|---|---|")
    for ly_do in _DANH_SACH_LY_DO:
        so_luong = dem_theo_ly_do[ly_do]
        ti_le = so_luong / tong if tong else 0.0
        print(f"| {ly_do} | {so_luong} | {ti_le:.2%} |")
    print(f"\nTổng số ảnh xét: `{tong}` — manifest: `{duong_dan_manifest}`")
    print(f"Seed: `{args.seed}` — giới hạn: `{args.gioi_han or 'không giới hạn'}`\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
