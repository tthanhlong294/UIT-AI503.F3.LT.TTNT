"""Khối căn chỉnh khuôn mặt về kích thước chuẩn bằng biến đổi tương tự từ 5 điểm mốc.

Phần toán thuần tuý, không phụ thuộc mô hình phát hiện khuôn mặt — dùng chung cho cả tiền xử lý
dữ liệu (Phase 1) lẫn suy luận thời gian thực (Phase 3). Xem `docs/dac-ta/P1-04-align.md` §3.1 để
biết vì sao dùng biến đổi tương tự (4 bậc tự do) thay vì affine đầy đủ (6 bậc tự do).
"""

import cv2
import numpy as np

from src.common.exceptions import LoiCauHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)

# Ánh xạ tên kiểu nội suy trong config sang hằng số OpenCV.
_KIEU_NOI_SUY = {
    "nearest": cv2.INTER_NEAREST,
    "bilinear": cv2.INTER_LINEAR,
    "cubic": cv2.INTER_CUBIC,
    "lanczos4": cv2.INTER_LANCZOS4,
}

_HINH_DANG_DIEM_MOC = (5, 2)


def kiem_diem_moc(diem_moc: np.ndarray) -> None:
    """Kiểm tính hợp lệ của mảng điểm mốc.

    Hợp lệ: mảng số thực hình dạng (5, 2), không chứa NaN hoặc vô cực.

    Args:
        diem_moc: Mảng điểm mốc cần kiểm.

    Raises:
        ValueError: nếu sai hình dạng, sai kiểu, hoặc chứa giá trị không hữu hạn.
    """
    if not isinstance(diem_moc, np.ndarray):
        # ValueError (không phải TypeError) vì đây là lỗi dữ liệu đầu vào theo hợp đồng của
        # đặc tả (docs/dac-ta/P1-04-align.md §3, §7): "sai kiểu" gộp chung với "sai hình dạng".
        raise ValueError(  # noqa: TRY004
            f"diem_moc phải là numpy.ndarray, nhận kiểu {type(diem_moc).__name__}"
        )

    if diem_moc.shape != _HINH_DANG_DIEM_MOC:
        raise ValueError(
            f"diem_moc phải có hình dạng {_HINH_DANG_DIEM_MOC}, nhận hình dạng {diem_moc.shape}"
        )

    try:
        deu_huu_han = bool(np.all(np.isfinite(diem_moc)))
    except TypeError as e:
        raise ValueError(
            f"diem_moc phải chứa giá trị số thực, kiểu dữ liệu không hợp lệ: {diem_moc.dtype}"
        ) from e

    if not deu_huu_han:
        raise ValueError("diem_moc chứa giá trị không hữu hạn (NaN hoặc vô cực)")


def uoc_luong_bien_doi(diem_moc: np.ndarray, diem_chuan: np.ndarray) -> np.ndarray:
    """Ước lượng ma trận biến đổi tương tự 2×3 đưa `diem_moc` về `diem_chuan`.

    Biến đổi tương tự gồm xoay, phóng đại đều và tịnh tiến — KHÔNG có cắt xiên
    và KHÔNG phóng đại khác nhau theo hai trục (xem `docs/dac-ta/P1-04-align.md` §3.1).

    Args:
        diem_moc: 5 điểm mốc nguồn, hình dạng (5, 2).
        diem_chuan: 5 điểm mốc đích (điểm chuẩn), hình dạng (5, 2).

    Returns:
        Ma trận biến đổi tương tự, hình dạng (2, 3), dùng trực tiếp cho `cv2.warpAffine`.

    Raises:
        ValueError: nếu `diem_moc` hoặc `diem_chuan` không hợp lệ (xem `kiem_diem_moc`).
        LoiCauHinh: nếu không ước lượng được (điểm suy biến, ví dụ 5 điểm trùng nhau).
    """
    kiem_diem_moc(diem_moc)
    kiem_diem_moc(diem_chuan)

    nguon = diem_moc.astype(np.float32)
    dich = diem_chuan.astype(np.float32)

    try:
        ma_tran, _inliers = cv2.estimateAffinePartial2D(nguon, dich)
    except cv2.error as e:
        raise LoiCauHinh(f"Lỗi OpenCV khi ước lượng biến đổi tương tự: {e}") from e

    if ma_tran is None:
        raise LoiCauHinh(
            "Không ước lượng được biến đổi tương tự: điểm mốc suy biến "
            "(ví dụ 5 điểm trùng nhau hoặc thẳng hàng)"
        )

    return ma_tran


def can_chinh(
    anh: np.ndarray,
    diem_moc: np.ndarray,
    cfg: dict,
) -> np.ndarray:
    """Căn chỉnh khuôn mặt về kích thước chuẩn.

    Args:
        anh: Ảnh BGR, hình dạng (H, W, 3), kiểu uint8.
        diem_moc: 5 điểm mốc trên `anh`, hình dạng (5, 2), thứ tự theo
            `docs/dac-ta/P1-04-align.md` §3.2 (mắt trái, mắt phải, mũi, khoé miệng trái,
            khoé miệng phải).
        cfg: Toàn bộ nội dung `configs/preprocess.yaml`.

    Returns:
        Ảnh BGR đã căn chỉnh, đúng kích thước `cfg["output_size"]`, kiểu uint8.

    Raises:
        ValueError: nếu `anh` sai hình dạng hoặc sai kiểu; nếu `diem_moc` không hợp lệ.
        LoiCauHinh: nếu thiếu key bắt buộc trong `cfg`, hoặc điểm mốc suy biến.
    """
    if not isinstance(anh, np.ndarray):
        # ValueError (không phải TypeError) vì đây là lỗi dữ liệu đầu vào theo hợp đồng của
        # đặc tả (docs/dac-ta/P1-04-align.md §3, §7): "sai kiểu" gộp chung với "sai hình dạng".
        raise ValueError(  # noqa: TRY004
            f"anh phải là numpy.ndarray, nhận kiểu {type(anh).__name__}"
        )

    if anh.ndim != 3 or anh.shape[2] != 3:
        raise ValueError(f"anh phải có hình dạng (H, W, 3), nhận hình dạng {anh.shape}")

    if anh.dtype != np.uint8:
        raise ValueError(f"anh phải có kiểu uint8, nhận kiểu {anh.dtype}")

    kiem_diem_moc(diem_moc)

    if "output_size" not in cfg:
        raise LoiCauHinh("Thiếu key bắt buộc trong cấu hình: 'output_size'")

    if "reference_landmarks" not in cfg:
        raise LoiCauHinh("Thiếu key bắt buộc trong cấu hình: 'reference_landmarks'")

    try:
        rong, cao = (int(v) for v in cfg["output_size"])
    except (TypeError, ValueError) as e:
        raise LoiCauHinh(f"Cấu hình 'output_size' không hợp lệ: {cfg['output_size']!r}") from e

    if rong <= 0 or cao <= 0:
        raise LoiCauHinh(
            f"Cấu hình 'output_size' phải là hai số dương, nhận {cfg['output_size']!r}"
        )

    try:
        diem_chuan = np.asarray(cfg["reference_landmarks"], dtype=np.float64)
        kiem_diem_moc(diem_chuan)
    except (TypeError, ValueError) as e:
        raise LoiCauHinh(f"Cấu hình 'reference_landmarks' không hợp lệ: {e}") from e

    ten_noi_suy = cfg.get("interpolation", "bilinear")
    if ten_noi_suy not in _KIEU_NOI_SUY:
        raise LoiCauHinh(
            f"Cấu hình 'interpolation' không hợp lệ: {ten_noi_suy!r}. "
            f"Các giá trị hợp lệ: {sorted(_KIEU_NOI_SUY)}"
        )
    co_noi_suy = _KIEU_NOI_SUY[ten_noi_suy]

    mau_vien_raw = cfg.get("border_value", [0, 0, 0])
    if not isinstance(mau_vien_raw, (list, tuple)):
        raise LoiCauHinh(
            f"Cấu hình 'border_value' phải là danh sách 3 số (B, G, R), nhận {mau_vien_raw!r}"
        )
    if len(mau_vien_raw) != 3:
        raise LoiCauHinh(
            f"Cấu hình 'border_value' phải có đúng 3 phần tử (B, G, R), nhận {mau_vien_raw!r}"
        )
    try:
        mau_vien = tuple(float(v) for v in mau_vien_raw)
    except (TypeError, ValueError) as e:
        raise LoiCauHinh(f"Cấu hình 'border_value' không hợp lệ: {mau_vien_raw!r}") from e

    ma_tran = uoc_luong_bien_doi(diem_moc, diem_chuan)

    anh_can_chinh = cv2.warpAffine(
        anh,
        ma_tran,
        (rong, cao),
        flags=co_noi_suy,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=mau_vien,
    )

    logger.debug("Đã căn chỉnh khuôn mặt về kích thước (%d, %d)", cao, rong)

    return anh_can_chinh.astype(np.uint8)
