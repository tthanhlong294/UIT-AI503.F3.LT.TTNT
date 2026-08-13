"""Factory tạo bộ thu hình."""

from src.capture.base import BoThuHinh
from src.common.exceptions import LoiCamera, LoiCauHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)


def tao_bo_thu_hinh(cfg: dict) -> BoThuHinh:
    """Tạo bộ thu hình theo cấu hình.

    Args:
        cfg (dict): TOÀN BỘ nội dung configs/capture.yaml.

    Returns:
        BoThuHinh: Đối tượng bộ thu hình tương ứng.
    """
    if "backend" not in cfg:
        raise LoiCauHinh("Thiếu key bắt buộc: backend")

    backend = cfg["backend"]

    if backend == "mock":
        from .mock_camera import CameraGiaLap

        return CameraGiaLap(cfg.get("mock", {}))
    elif backend == "opencv":
        try:
            from .opencv_camera import CameraOpenCV
        except ImportError as e:
            raise LoiCauHinh("backend='opencv' nhưng máy không có OpenCV") from e

        return CameraOpenCV(cfg.get("opencv", {}))
    elif backend == "auto":
        from .mock_camera import CameraGiaLap

        try:
            from .opencv_camera import CameraOpenCV

            opencv_cfg = cfg.get("opencv", {})
            cam = CameraOpenCV(opencv_cfg)
            # Thử mở camera để kiểm tra, nếu thất bại sẽ ném ngoại lệ LoiCamera
            cam.mo()
            cam.dong()
            return cam
        except (LoiCamera, LoiCauHinh, ImportError) as e:
            logger.warning(
                "Backend auto: Không dùng được OpenCV (%s), chuyển sang mock.", type(e).__name__
            )
            return CameraGiaLap(cfg.get("mock", {}))
    else:
        raise LoiCauHinh(f"Backend không hợp lệ: {backend}")
