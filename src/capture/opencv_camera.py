"""Bộ thu hình thực tế dùng OpenCV."""

import cv2
import numpy as np

from src.capture.base import BoThuHinh
from src.common.exceptions import LoiCamera, LoiCauHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)


class CameraOpenCV(BoThuHinh):
    """Bộ thu hình sử dụng OpenCV."""

    def __init__(self, cfg: dict) -> None:
        """Khởi tạo camera OpenCV với cấu hình.

        Args:
            cfg (dict): Nhánh `opencv` của cấu hình.
        """
        self.cfg = cfg
        if "device_index" not in self.cfg:
            raise LoiCauHinh("Thiếu key bắt buộc: opencv.device_index")
        if "width" not in self.cfg:
            raise LoiCauHinh("Thiếu key bắt buộc: opencv.width")
        if "height" not in self.cfg:
            raise LoiCauHinh("Thiếu key bắt buộc: opencv.height")

        self._device_index = self.cfg["device_index"]
        self._width = self.cfg["width"]
        self._height = self.cfg["height"]
        self._warmup_frames = self.cfg.get("warmup_frames", 0)
        self._max_retry = self.cfg.get("max_retry", 3)

        self._cap = None
        self._dang_mo = False

    def mo(self) -> None:
        """Mở thiết bị camera."""
        try:
            self._cap = cv2.VideoCapture(self._device_index)
            if not self._cap.isOpened():
                self._cap = None
                raise LoiCamera(f"Không thể mở camera OpenCV với device_index={self._device_index}")

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)

            # Đọc bỏ một số khung hình ban đầu
            for _ in range(self._warmup_frames):
                ret, _ = self._cap.read()
                if not ret:
                    logger.warning("Đọc khung hình warmup thất bại")
        except cv2.error as e:
            self._cap = None
            raise LoiCamera(f"Lỗi OpenCV khi mở device_index={self._device_index}") from e

        self._dang_mo = True
        logger.info("Đã mở camera OpenCV (device_index=%s)", self._device_index)

    def doc_frame(self) -> np.ndarray:
        """Đọc một khung hình từ camera.

        Returns:
            np.ndarray: khung hình `(height, width, 3)`, `dtype=uint8`, thứ tự kênh **BGR**.

        Raises:
            LoiCamera: khi chưa gọi `mo()` hoặc đọc thất bại.
        """
        if not self._dang_mo or self._cap is None:
            raise LoiCamera("Camera OpenCV chưa mở hoặc đã đóng")

        for thutu in range(self._max_retry):
            try:
                ret, frame = self._cap.read()
                if ret and frame is not None:
                    return frame
                logger.warning("Lỗi đọc khung hình, thử lại lần %d", thutu + 1)
            except cv2.error as e:
                raise LoiCamera("Lỗi OpenCV khi đọc khung hình") from e

        raise LoiCamera("Không thể đọc khung hình từ camera sau nhiều lần thử")

    def dong(self) -> None:
        """Giải phóng camera. An toàn khi gọi nhiều lần và khi release() lỗi."""
        try:
            if self._cap is not None:
                self._cap.release()
        except Exception as e:  # noqa: BLE001
            logger.warning("Lỗi khi giải phóng camera: %s", e)
        finally:
            self._cap = None
            if self._dang_mo:
                self._dang_mo = False
                logger.info("Đã đóng camera OpenCV")

    @property
    def dang_mo(self) -> bool:
        """Trạng thái camera."""
        return self._dang_mo
