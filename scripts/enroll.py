"""Đăng ký danh tính: gộp nhiều ảnh khuôn mặt của mỗi người thành một vectơ đại diện.

Xem docs/dac-ta/P3-03-enroll.md. Đây là mắt xích còn thiếu giữa khối nhận diện (đã xong ở P3-01,
P3-02) và phép quét ngưỡng (bước 3.5): chưa có gallery thì không có gì để so, không có đường cong
ROC, và không chốt được ngưỡng.

⚠️ Script KHÔNG tự tính vectơ trung bình (§6.1 đặc tả) — luôn gọi thẳng `backend.enroll(...)` và
ghi thẳng kết quả. Phép chuẩn hoá L2 từng vectơ trước khi lấy trung bình là một quyết định phương
pháp đã chốt và đã có ca kiểm thử ở cả hai backend; viết lại logic đó trong script tạo ra một bản
sao thứ hai trôi khỏi bản gốc theo thời gian mà không có gì phát hiện được.

⚠️ Người thiếu ảnh (backend.enroll() ném ValueError) bị BỎ QUA, không hạ ngưỡng ngầm để "chạy cho
xong" (§6.2). Hai backend ghi vào hai thư mục con khác nhau — 128 và 512 chiều không được trộn
(§6.3).
"""

import sys
from pathlib import Path

# Thêm gốc dự án vào sys.path để cho phép chạy trực tiếp kịch bản
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import csv
import datetime
import importlib.metadata
import json
import platform
import subprocess

import cv2
import numpy as np
import onnxruntime as ort

from scripts.export_detector_ncnn import xac_dinh_moi_truong
from src.common.config import lay_gia_tri, nap_cau_hinh
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger
from src.recognizer.base import BoNhanDien
from src.recognizer.factory import tao_bo_nhan_dien

logger = lay_logger(__name__)

# Đuôi tệp được coi là ảnh khi quét thư mục của một người.
_DINH_DANG_ANH_HOP_LE = {".jpg", ".jpeg", ".png"}

# Ba trạng thái chốt của một người trong manifest — xem §5.3 đặc tả. Không thêm bớt.
_TRANG_THAI_DA_DANG_KY = "da_dang_ky"
_TRANG_THAI_THIEU_ANH = "thieu_anh"
_TRANG_THAI_LOI_DOC_ANH = "loi_doc_anh"

# Sáu cột manifest, đúng thứ tự — xem §5.3 đặc tả.
_COT_MANIFEST = ["user_id", "so_anh_tim_thay", "so_anh_dung", "trang_thai", "so_chieu", "tep_ra"]

# Đường dẫn ảnh hưởng tới vectơ sinh ra — thay đổi ở đây làm gallery khác đi. Cùng cách
# scripts/benchmark_detect.py giới hạn phạm vi git_dirty (P2-06c §5.1).
_DUONG_DAN_ANH_HUONG_PHEP_CHAY = (
    "src",
    "scripts",
    "configs",
    "requirements.txt",
    "requirements-dev.txt",
)


def liet_ke_nguoi(vao_dir: Path) -> list[Path]:
    """Liệt kê thư mục con của thư mục ảnh vào — mỗi thư mục con là một người.

    Args:
        vao_dir: Thư mục gốc, cấu trúc `<vao_dir>/<user_id>/*.{jpg,jpeg,png}`.

    Returns:
        Danh sách đường dẫn thư mục con, đã sắp xếp theo tên. KỂ CẢ thư mục rỗng — người gọi
        tự quyết định có bỏ qua hay không (§6.5 đặc tả).

    Raises:
        LoiCauHinh: `vao_dir` không tồn tại hoặc không phải thư mục.
    """
    vao_dir = Path(vao_dir)
    if not vao_dir.exists() or not vao_dir.is_dir():
        raise LoiCauHinh(f"Thư mục ảnh vào không tồn tại hoặc không phải thư mục: '{vao_dir}'")
    return sorted(p for p in vao_dir.iterdir() if p.is_dir())


def liet_ke_anh_nguoi(thu_muc_nguoi: Path) -> list[Path]:
    """Liệt kê ảnh của MỘT người, không đệ quy.

    Args:
        thu_muc_nguoi: Thư mục con của một `user_id`.

    Returns:
        Danh sách đường dẫn ảnh, đã sắp xếp, nhận đuôi `.jpg`, `.jpeg`, `.png`
        (không phân biệt hoa thường).
    """
    return sorted(
        p
        for p in thu_muc_nguoi.iterdir()
        if p.is_file() and p.suffix.lower() in _DINH_DANG_ANH_HOP_LE
    )


def kiem_ten_nguoi_hop_le(ten: str) -> None:
    """Kiểm một `user_id` an toàn để dùng làm tên tệp `.npy` (§6.5 đặc tả).

    Args:
        ten: Tên thư mục con / `user_id` cần kiểm.

    Raises:
        LoiCauHinh: tên rỗng, bằng `.` hoặc `..`, hoặc chứa dấu tách đường dẫn.
    """
    if not ten:
        raise LoiCauHinh("user_id rỗng, không hợp lệ để đặt tên tệp")
    if ten in (".", ".."):
        raise LoiCauHinh(f"user_id không được là '.' hoặc '..': {ten!r}")
    if "/" in ten or "\\" in ten:
        raise LoiCauHinh(f"user_id chứa dấu tách đường dẫn, không hợp lệ: {ten!r}")


def loc_theo_yeu_cau(danh_sach_thu_muc: list[Path], ten_yeu_cau: list[str]) -> list[Path]:
    """Lọc danh sách thư mục người theo cờ `--nguoi`.

    Args:
        danh_sach_thu_muc: Toàn bộ thư mục con tìm được trong thư mục vào.
        ten_yeu_cau: Danh sách `user_id` yêu cầu qua `--nguoi`. Rỗng nghĩa là lấy tất cả.

    Returns:
        Danh sách con đã lọc, giữ nguyên thứ tự của `danh_sach_thu_muc`.

    Raises:
        LoiCauHinh: có tên trong `ten_yeu_cau` không khớp bất kỳ thư mục nào.
    """
    if not ten_yeu_cau:
        return danh_sach_thu_muc

    ten_co_san = {p.name for p in danh_sach_thu_muc}
    ten_thieu = [t for t in ten_yeu_cau if t not in ten_co_san]
    if ten_thieu:
        raise LoiCauHinh(
            f"Không tìm thấy user_id trong --nguoi: {', '.join(ten_thieu)} "
            f"(thư mục vào có: {', '.join(sorted(ten_co_san)) or 'không có ai'})"
        )

    tap_yeu_cau = set(ten_yeu_cau)
    return [p for p in danh_sach_thu_muc if p.name in tap_yeu_cau]


def xu_ly_mot_nguoi(
    thu_muc_nguoi: Path,
    danh_sach_anh: list[Path],
    backend: BoNhanDien,
    cfg_enroll: dict,
) -> dict:
    """Đăng ký MỘT người từ danh sách ảnh của họ.

    Không tự tính vectơ trung bình (§6.1) — gọi thẳng `backend.enroll(...)` và trả thẳng kết
    quả để nơi gọi ghi ra đĩa.

    Args:
        thu_muc_nguoi: Thư mục con của người này, tên thư mục là `user_id`.
        danh_sach_anh: Danh sách đường dẫn ảnh đã liệt kê sẵn, KHÔNG RỖNG — người gọi tự lọc
            thư mục rỗng trước khi gọi hàm này (§6.5 đặc tả).
        backend: Backend nhận diện đã khởi tạo.
        cfg_enroll: Cấu hình truyền thẳng cho `backend.enroll()`, chứa khoá
            `min_images_per_user`.

    Returns:
        Từ điển bảy khoá: sáu khoá khớp cột manifest (`user_id`, `so_anh_tim_thay`,
        `so_anh_dung`, `trang_thai`, `so_chieu`, `tep_ra`) cộng thêm `vec` (`np.ndarray | None`,
        `None` khi người này bị bỏ qua).

    Raises:
        LoiMoHinh: `backend.enroll()` ném `ValueError` dù người này có đủ ảnh so với
            `min_images_per_user` (lỗi mô hình hoặc dữ liệu vào chưa qua tiền xử lý, không phải
            thiếu ảnh — xem CHẶN-B-1, biên bản review vòng 1), hoặc vectơ trả về lệch số chiều
            đã khai báo (§6.3). Cả hai đều là lỗi mô hình, không phải lỗi dữ liệu của riêng
            người này, nên KHÔNG bị bắt ở đây mà lan lên trên để dừng cả lượt chạy.
    """
    user_id = thu_muc_nguoi.name
    so_anh_tim_thay = len(danh_sach_anh)

    ket_qua: dict = {
        "user_id": user_id,
        "so_anh_tim_thay": so_anh_tim_thay,
        "so_anh_dung": 0,
        "trang_thai": _TRANG_THAI_LOI_DOC_ANH,
        "so_chieu": "",
        "tep_ra": "",
        "vec": None,
    }

    anh_da_doc: list[np.ndarray] = []
    for duong_dan_anh in danh_sach_anh:
        anh = cv2.imread(str(duong_dan_anh))
        if anh is None:
            logger.warning(
                "Không đọc được ảnh của '%s', bỏ qua người này: %s", user_id, duong_dan_anh
            )
            return ket_qua
        anh_da_doc.append(anh)

    try:
        vec = backend.enroll(anh_da_doc, cfg_enroll)
    except ValueError as e:
        if so_anh_tim_thay < cfg_enroll["min_images_per_user"]:
            logger.info("Bỏ qua '%s' vì thiếu ảnh: %s", user_id, e)
            ket_qua["trang_thai"] = _TRANG_THAI_THIEU_ANH
            return ket_qua
        raise LoiMoHinh(
            f"backend.enroll() thất bại với '{user_id}' dù có {so_anh_tim_thay} ảnh "
            f"(ngưỡng {cfg_enroll['min_images_per_user']}): {e}"
        ) from e

    if vec.shape != (backend.so_chieu,):
        raise LoiMoHinh(
            f"Vectơ đăng ký của '{user_id}' có hình dạng {vec.shape}, kỳ vọng "
            f"({backend.so_chieu},) — backend.enroll() trả sai số chiều"
        )

    ket_qua["so_anh_dung"] = so_anh_tim_thay
    ket_qua["trang_thai"] = _TRANG_THAI_DA_DANG_KY
    ket_qua["so_chieu"] = backend.so_chieu
    ket_qua["vec"] = vec
    return ket_qua


def ghi_manifest(duong_dan: Path, ban_ghi: list[dict]) -> None:
    """Ghi manifest.csv, sáu cột đúng thứ tự `_COT_MANIFEST`.

    Kiểm đủ khoá cho TOÀN BỘ bản ghi trước khi mở tệp để ghi — tránh ghi một tệp dở dang khi
    một bản ghi ở giữa danh sách bị thiếu khoá (cùng cách `scripts/preprocess.py` làm).

    Args:
        duong_dan: Đường dẫn tệp manifest.csv cần ghi.
        ban_ghi: Danh sách bản ghi, mỗi phần tử là một dict đủ sáu khoá của `_COT_MANIFEST`.

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


def _phan_giai_toi_thieu(gia_tri_dong_lenh: str | None, cfg: dict) -> tuple[int, int]:
    """Phân giải ngưỡng số ảnh tối thiểu, đối chiếu với giá trị trong cấu hình (§6.4 đặc tả).

    Args:
        gia_tri_dong_lenh: Giá trị chuỗi từ cờ `--toi-thieu`, hoặc `None` nếu không truyền.
        cfg: Toàn bộ nội dung `configs/recognize.yaml`.

    Returns:
        Tuple `(đã_dùng, trong_cấu_hình)`. Hai giá trị bằng nhau khi không truyền `--toi-thieu`.

    Raises:
        LoiCauHinh: giá trị truyền vào không phải số nguyên, hoặc là số âm.
    """
    trong_cau_hinh = lay_gia_tri(cfg, "enroll.min_images_per_user")
    if gia_tri_dong_lenh is None:
        return trong_cau_hinh, trong_cau_hinh

    try:
        da_dung = int(gia_tri_dong_lenh)
    except ValueError as e:
        raise LoiCauHinh(f"--toi-thieu phải là số nguyên, nhận '{gia_tri_dong_lenh}'") from e
    if da_dung < 0:
        raise LoiCauHinh(f"--toi-thieu không được âm, nhận {da_dung}")

    return da_dung, trong_cau_hinh


def _lay_git_commit_hash() -> str:
    """Lấy commit hash hiện tại của repo, dùng cho gallery.meta.json (R17)."""
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


def _chay_git_status(pham_vi: tuple[str, ...]) -> bool:
    """Chạy `git status --porcelain` giới hạn theo pathspec, trả về cây có bẩn hay không.

    Giới hạn phạm vi bằng pathspec (KHÔNG loại tệp chưa `git add`) — cùng cách
    `scripts/benchmark_detect.py` đã dựng (P2-06c §5.1): một tệp mới trong `src/recognizer/`
    vẫn phải làm cờ bật, vì nó ảnh hưởng tới vectơ đăng ký sinh ra.

    Args:
        pham_vi: Danh sách đường dẫn giới hạn phép kiểm. Rỗng nghĩa là toàn bộ cây.

    Returns:
        True nếu git in ra bất kỳ dòng nào, hoặc nếu không chạy được git.
    """
    lenh = ["git", "status", "--porcelain"]
    if pham_vi:
        lenh = lenh + ["--", *pham_vi]
    try:
        ket_qua = subprocess.run(
            lenh,
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        return bool(ket_qua.stdout.strip())
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning("Không kiểm tra được trạng thái git: %s", e)
        return True


def _kiem_tra_git_dirty() -> bool:
    """Kiểm mã nguồn sinh ra gallery có thay đổi nào chưa commit hay không (R17).

    Chỉ xét các đường dẫn ở `_DUONG_DAN_ANH_HUONG_PHEP_CHAY` — cùng cách
    `scripts/benchmark_detect.py` giới hạn phạm vi (P2-06c).
    """
    return _chay_git_status(_DUONG_DAN_ANH_HUONG_PHEP_CHAY)


def _lay_phien_ban_goi(ten: str) -> str:
    """Tra phiên bản một gói đã cài qua metadata, không import gói đó.

    Args:
        ten: Tên phân phối (distribution name) cần tra.

    Returns:
        Chuỗi phiên bản, hoặc `"khong-xac-dinh"` nếu gói chưa cài.
    """
    try:
        return importlib.metadata.version(ten)
    except importlib.metadata.PackageNotFoundError as e:
        logger.warning("Không tra được phiên bản gói '%s': %s", ten, e)
        return "khong-xac-dinh"


def _xay_dung_parser() -> argparse.ArgumentParser:
    """Dựng argparse cho script, theo đúng giao diện dòng lệnh ở §5.2 đặc tả."""
    parser = argparse.ArgumentParser(
        description=(
            "Đăng ký danh tính: gộp nhiều ảnh khuôn mặt của mỗi người thành một vectơ đại "
            "diện, lưu vào thư mục gallery (xem docs/dac-ta/P3-03-enroll.md)."
        )
    )
    parser.add_argument(
        "--vao",
        default=None,
        help="Thư mục ảnh nguồn, cấu trúc <vao>/<user_id>/*.{jpg,png} (bắt buộc)",
    )
    parser.add_argument(
        "--ra", default=None, help="Thư mục đích, mặc định lấy từ enroll.gallery_dir trong cấu hình"
    )
    parser.add_argument(
        "--config", default="configs/recognize.yaml", help="Đường dẫn cấu hình khối nhận diện"
    )
    parser.add_argument(
        "--backend",
        default=None,
        help="Backend nhận diện: 'dlib' hoặc 'arcface', mặc định lấy từ khoá backend trong cấu hình",
    )
    parser.add_argument(
        "--toi-thieu",
        default=None,
        help="Ghi đè số ảnh tối thiểu để đăng ký một người (mặc định lấy từ cấu hình)",
    )
    parser.add_argument(
        "--nguoi",
        default="",
        help="Danh sách user_id cần đăng ký, cách nhau bằng dấu phẩy (mặc định: tất cả)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed ghi vào metadata (R15)")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in kế hoạch, không ghi tệp nào")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 thành công, 1 thất bại."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = _xay_dung_parser().parse_args(argv)

    if args.vao is None:
        logger.error("Thiếu tham số bắt buộc --vao")
        print("Thiếu tham số bắt buộc: --vao là bắt buộc.")
        return 1

    vao_dir = Path(args.vao)

    try:
        cfg = nap_cau_hinh(args.config)
    except LoiCauHinh as e:
        logger.error("Không đọc được cấu hình: %s", e)
        print(f"Không đọc được cấu hình: {e}")
        return 1

    try:
        toi_thieu_da_dung, toi_thieu_trong_cau_hinh = _phan_giai_toi_thieu(args.toi_thieu, cfg)
    except LoiCauHinh as e:
        logger.error("Tham số --toi-thieu không hợp lệ: %s", e)
        print(f"Tham số --toi-thieu không hợp lệ: {e}")
        return 1

    if toi_thieu_da_dung != toi_thieu_trong_cau_hinh:
        logger.warning(
            "Dùng --toi-thieu=%d khác giá trị trong cấu hình enroll.min_images_per_user=%d",
            toi_thieu_da_dung,
            toi_thieu_trong_cau_hinh,
        )

    ten_backend = args.backend if args.backend is not None else lay_gia_tri(cfg, "backend", None)

    try:
        ra_dir_goc = (
            Path(args.ra) if args.ra is not None else Path(lay_gia_tri(cfg, "enroll.gallery_dir"))
        )
    except LoiCauHinh as e:
        logger.error("Không xác định được thư mục ra: %s", e)
        print(f"Không xác định được thư mục ra: {e}")
        return 1

    ra_dir = ra_dir_goc / (ten_backend if ten_backend else "khong_xac_dinh_backend")

    danh_sach_nguoi_yeu_cau = (
        [t.strip() for t in args.nguoi.split(",") if t.strip()] if args.nguoi else []
    )

    try:
        tat_ca_thu_muc = liet_ke_nguoi(vao_dir)
        thu_muc_duoc_xet = loc_theo_yeu_cau(tat_ca_thu_muc, danh_sach_nguoi_yeu_cau)
    except LoiCauHinh as e:
        logger.error("Không liệt kê được người cần đăng ký: %s", e)
        print(f"Không liệt kê được người cần đăng ký: {e}")
        return 1

    if args.dry_run:
        print("\n### BẢNG KẾ HOẠCH ĐĂNG KÝ (DRY-RUN)")
        print(f"- Thư mục vào     : `{vao_dir}`")
        print(f"- Thư mục ra      : `{ra_dir}`")
        print(f"- Backend         : `{ten_backend}`")
        print(f"- Số người xét    : `{len(thu_muc_duoc_xet)}`")
        print(f"- Ngưỡng tối thiểu: `{toi_thieu_da_dung}` (cấu hình: `{toi_thieu_trong_cau_hinh}`)")
        print(f"- Seed            : `{args.seed}`\n")
        return 0

    try:
        backend = tao_bo_nhan_dien(cfg, ten_backend)
    except (LoiCauHinh, LoiMoHinh) as e:
        logger.error("Không dựng được backend nhận diện: %s", e)
        print(f"Không dựng được backend nhận diện: {e}")
        return 1

    ra_dir.mkdir(parents=True, exist_ok=True)
    cfg_enroll = {"min_images_per_user": toi_thieu_da_dung}

    ban_ghi_manifest: list[dict] = []
    dem_theo_trang_thai = dict.fromkeys(
        (_TRANG_THAI_DA_DANG_KY, _TRANG_THAI_THIEU_ANH, _TRANG_THAI_LOI_DOC_ANH), 0
    )

    try:
        for thu_muc_nguoi in thu_muc_duoc_xet:
            kiem_ten_nguoi_hop_le(thu_muc_nguoi.name)

            danh_sach_anh = liet_ke_anh_nguoi(thu_muc_nguoi)
            if not danh_sach_anh:
                continue  # thư mục rỗng — bỏ qua, không tính vào manifest (§6.5)

            ket_qua = xu_ly_mot_nguoi(thu_muc_nguoi, danh_sach_anh, backend, cfg_enroll)
            dem_theo_trang_thai[ket_qua["trang_thai"]] += 1

            if ket_qua["vec"] is not None:
                duong_dan_npy = ra_dir / f"{ket_qua['user_id']}.npy"
                np.save(duong_dan_npy, ket_qua["vec"])
                ket_qua["tep_ra"] = duong_dan_npy.name

            ban_ghi_manifest.append({cot: ket_qua[cot] for cot in _COT_MANIFEST})
    except (LoiCauHinh, LoiMoHinh) as e:
        logger.error("Đăng ký thất bại, dừng ngay: %s", e)
        print(f"Đăng ký thất bại: {e}")
        return 1

    duong_dan_manifest = ra_dir / "manifest.csv"
    ghi_manifest(duong_dan_manifest, ban_ghi_manifest)

    so_nguoi_da_dang_ky = dem_theo_trang_thai[_TRANG_THAI_DA_DANG_KY]
    so_nguoi_bo_qua = len(ban_ghi_manifest) - so_nguoi_da_dang_ky

    thoi_diem = datetime.datetime.now().astimezone()
    meta = {
        "backend": ten_backend,
        "so_chieu": backend.so_chieu,
        "duong_dan_vao": str(vao_dir),
        "so_nguoi_da_dang_ky": so_nguoi_da_dang_ky,
        "so_nguoi_bo_qua": so_nguoi_bo_qua,
        "min_images_per_user_da_dung": toi_thieu_da_dung,
        "min_images_per_user_trong_cau_hinh": toi_thieu_trong_cau_hinh,
        "seed": args.seed,
        "thoi_gian": thoi_diem.isoformat(),
        "commit": _lay_git_commit_hash(),
        "git_dirty": _kiem_tra_git_dirty(),
        "moi_truong": xac_dinh_moi_truong(),
        "software": {
            "python": platform.python_version(),
            "opencv-python": cv2.__version__,
            "numpy": np.__version__,
            "onnxruntime": ort.__version__,
            "dlib-bin": _lay_phien_ban_goi("dlib-bin"),
        },
    }
    duong_dan_meta = ra_dir / "gallery.meta.json"
    with open(duong_dan_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    logger.info("Đã ghi gallery.meta.json: %s", duong_dan_meta)

    print("\n### BẢNG TỔNG KẾT ĐĂNG KÝ")
    print("| Trạng thái | Số người |")
    print("|---|---|")
    for trang_thai in (_TRANG_THAI_DA_DANG_KY, _TRANG_THAI_THIEU_ANH, _TRANG_THAI_LOI_DOC_ANH):
        print(f"| {trang_thai} | {dem_theo_trang_thai[trang_thai]} |")
    print(f"\nBackend: `{ten_backend}` — số chiều: `{backend.so_chieu}`")
    print(
        f"Ngưỡng tối thiểu đã dùng: `{toi_thieu_da_dung}` (cấu hình: `{toi_thieu_trong_cau_hinh}`)"
    )
    print(f"Manifest: `{duong_dan_manifest}`")
    print(f"Meta    : `{duong_dan_meta}`\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
