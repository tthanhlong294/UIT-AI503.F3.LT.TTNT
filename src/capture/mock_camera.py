"""Bộ thu hình giả lập."""

import os

import numpy as np

from src.capture.base import BoThuHinh
from src.common.exceptions import LoiCamera, LoiCauHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)


class CameraGiaLap(BoThuHinh):
    """Bộ thu hình giả lập, sinh ảnh ngẫu nhiên hoặc đọc từ thư mục."""

    def __init__(self, cfg: dict) -> None:
        """Khởi tạo camera giả lập.

        Args:
            cfg: Nhánh mock của cấu hình capture.
        """
        self.cfg = cfg
        if "width" not in self.cfg:
            raise LoiCauHinh("Thiếu key bắt buộc: mock.width")
        if "height" not in self.cfg:
            raise LoiCauHinh("Thiếu key bắt buộc: mock.height")

        self._width = self.cfg["width"]
        self._height = self.cfg["height"]

        self._source = self.cfg.get("source", "synthetic")
        if self._source == "directory":
            source_dir = self.cfg.get("source_dir", "")
            if not source_dir or not os.path.isdir(source_dir):
                raise LoiCauHinh(f"Thư mục source_dir không tồn tại hoặc rỗng: {source_dir}")

            self._image_files = sorted(
                [
                    os.path.join(source_dir, f)
                    for f in os.listdir(source_dir)
                    if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))
                ]
            )
            if not self._image_files:
                raise LoiCauHinh(f"Thư mục source_dir không có ảnh hợp lệ: {source_dir}")

        self._seed = self.cfg.get("seed", 42)
        self._loop = self.cfg.get("loop", True)
        self._max_frames = self.cfg.get("max_frames", 0)

        self._dang_mo = False
        self._rng = np.random.default_rng(self._seed)
        self._frames_read = 0

    def mo(self) -> None:
        """Mở camera giả lập, đặt lại luồng sinh số để bảo đảm tái lập (R15)."""
        self._rng = np.random.default_rng(self._seed)
        self._frames_read = 0
        self._dang_mo = True
        logger.info("Đã mở camera giả lập (độ phân giải %dx%d)", self._width, self._height)

    def doc_frame(self) -> np.ndarray:
        """Đọc một khung hình.

        Returns:
            np.ndarray: khung hình `(height, width, 3)`, `dtype=uint8`, thứ tự kênh **BGR**.

        Raises:
            LoiCamera: khi chưa gọi `mo()` hoặc đọc thất bại.
        """
        if not self._dang_mo:
            raise LoiCamera("Camera giả lập chưa mở hoặc đã đóng")

        # Kiểm tra giới hạn max_frames
        if self._max_frames > 0 and self._frames_read >= self._max_frames:
            if not self._loop:
                raise LoiCamera("Đã đạt giới hạn max_frames và không lặp")
            # Nếu lặp và đạt bội số của max_frames, đặt lại RNG cho synthetic
            if self._source == "synthetic" and self._frames_read % self._max_frames == 0:
                self._rng = np.random.default_rng(self._seed)

        if self._source == "directory":
            idx = self._frames_read
            if self._loop:
                idx = idx % len(self._image_files)
            elif idx >= len(self._image_files):
                raise LoiCamera("Đã đọc hết ảnh trong thư mục và không lặp")

            file_path = self._image_files[idx]
            try:
                import cv2

                img = cv2.imread(file_path)
                if img is None:
                    raise LoiCamera(f"Không thể đọc ảnh {file_path}")
                frame = cv2.resize(img, (self._width, self._height))
                frame = np.ascontiguousarray(frame)
            except ImportError as e:
                raise LoiCauHinh("Cần cài đặt OpenCV để đọc ảnh từ thư mục") from e
            except cv2.error as e:
                raise LoiCamera(f"Lỗi OpenCV khi đọc ảnh {file_path}") from e
        else:
            frame = self._rng.integers(0, 256, (self._height, self._width, 3), dtype=np.uint8)

        self._frames_read += 1
        return frame

    def dong(self) -> None:
        """Đóng camera giả lập."""
        if self._dang_mo:
            self._dang_mo = False
            logger.info("Đã đóng camera giả lập")

    @property
    def dang_mo(self) -> bool:
        """Trạng thái mở của camera giả lập."""
        return self._dang_mo
