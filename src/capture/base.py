"""Định nghĩa giao diện trừu tượng cho bộ thu hình."""

from abc import ABC, abstractmethod

import numpy as np


class BoThuHinh(ABC):
    """Interface trừu tượng cho mọi nguồn khung hình."""

    @abstractmethod
    def mo(self) -> None:
        """Mở nguồn thu hình. Raises LoiCamera nếu không mở được."""

    @abstractmethod
    def doc_frame(self) -> np.ndarray:
        """Đọc một khung hình. Raises LoiCamera nếu chưa mở hoặc đọc thất bại."""

    @abstractmethod
    def dong(self) -> None:
        """Giải phóng tài nguyên. Gọi nhiều lần phải an toàn."""

    @property
    @abstractmethod
    def dang_mo(self) -> bool:
        """Trả về trạng thái đóng/mở của thiết bị."""
        ...

    def __enter__(self) -> "BoThuHinh":  # noqa: PYI034
        """Hỗ trợ with statement."""
        self.mo()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Giải phóng tài nguyên khi thoát khỏi with statement."""
        self.dong()
