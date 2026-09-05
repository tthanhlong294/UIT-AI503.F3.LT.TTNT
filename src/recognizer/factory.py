"""Chọn backend cho khối nhận diện danh tính khuôn mặt theo cấu hình.

Hai backend hiện có nhận cấu hình theo hai kiểu KHÁC NHAU (xem docs/dac-ta/P3-03-enroll.md §3):
`DlibFaceRecognizer.__init__` nhận TOÀN BỘ nội dung `configs/recognize.yaml`, còn
`ArcFaceBackend.__init__` chỉ nhận mục con `cfg["arcface"]`. Factory che sự bất đối xứng này lại
để nơi gọi (script `enroll.py`, và về sau là pipeline chính) chỉ cần biết một hàm dựng duy nhất,
không cần nhớ backend nào ăn khớp cấu hình nào.
"""

from src.common.config import lay_gia_tri
from src.common.exceptions import LoiCauHinh
from src.common.logging import lay_logger
from src.recognizer.arcface_backend import ArcFaceBackend
from src.recognizer.base import BoNhanDien
from src.recognizer.dlib_backend import DlibFaceRecognizer

logger = lay_logger(__name__)

TEN_BACKEND_DLIB = "dlib"
TEN_BACKEND_ARCFACE = "arcface"

_TEN_BACKEND_HOP_LE = (TEN_BACKEND_DLIB, TEN_BACKEND_ARCFACE)


def tao_bo_nhan_dien(cfg: dict, ten_backend: str | None = None) -> BoNhanDien:
    """Chọn và khởi tạo backend nhận diện theo tên.

    Args:
        cfg: TOÀN BỘ nội dung configs/recognize.yaml.
        ten_backend: Tên backend cần dựng. None thì lấy từ khoá `backend` của cfg.

    Returns:
        Backend đã khởi tạo, dùng chung giao diện `BoNhanDien`.

    Raises:
        LoiCauHinh: tên backend không thuộc hai giá trị hợp lệ, hoặc cfg thiếu khoá.
        LoiMoHinh: tên hợp lệ nhưng mô hình không nạp được (do backend ném ra).
    """
    ten = ten_backend if ten_backend is not None else lay_gia_tri(cfg, "backend", None)

    if ten not in _TEN_BACKEND_HOP_LE:
        raise LoiCauHinh(
            f"Tên backend nhận diện không hợp lệ: {ten!r}. "
            f"Giá trị hợp lệ: {_TEN_BACKEND_HOP_LE}"
        )

    if ten == TEN_BACKEND_DLIB:
        logger.info("Factory chọn backend dlib")
        return DlibFaceRecognizer(cfg)

    logger.info("Factory chọn backend ArcFace")
    return ArcFaceBackend(lay_gia_tri(cfg, "arcface"))
