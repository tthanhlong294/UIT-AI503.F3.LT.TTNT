"""Định nghĩa các kiểu dữ liệu dùng chung cho toàn hệ thống."""

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class FaceBox:
    """Một khuôn mặt phát hiện được trong frame.

    Attributes:
        x1: Toạ độ x góc trên bên trái.
        y1: Toạ độ y góc trên bên trái.
        x2: Toạ độ x góc dưới bên phải.
        y2: Toạ độ y góc dưới bên phải.
        confidence: Độ tin cậy phát hiện (0.0 đến 1.0).
        landmarks: Mảng NumPy chứa điểm đặc trưng khuôn mặt (tuỳ chọn).
    """

    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    landmarks: np.ndarray | None = field(default=None, compare=False, repr=False)

    @property
    def chieu_rong(self) -> int:
        """Chiều rộng của khung chứa khuôn mặt."""
        return self.x2 - self.x1

    @property
    def chieu_cao(self) -> int:
        """Chiều cao của khung chứa khuôn mặt."""
        return self.y2 - self.y1

    @property
    def dien_tich(self) -> int:
        """Diện tích của khung chứa khuôn mặt tính bằng pixel vuông."""
        return self.chieu_rong * self.chieu_cao


@dataclass(frozen=True)
class Identity:
    """Kết quả nhận diện danh tính cho một khuôn mặt.

    Attributes:
        user_id: ID người dùng, là None nếu là người lạ.
        similarity: Độ tương đồng với mẫu đã đăng ký.
        is_live: Kết quả kiểm tra chống giả mạo (True nếu là mặt thật).
        backend: Tên backend nhận diện ("dlib" hoặc "arcface").
    """

    user_id: str | None
    similarity: float
    is_live: bool
    backend: str

    @property
    def la_nguoi_la(self) -> bool:
        """Kiểm tra xem khuôn mặt có phải là người lạ hay không."""
        return self.user_id is None


@dataclass(frozen=True)
class Command:
    """Một lệnh điều khiển thiết bị do khối quyết định sinh ra.

    Attributes:
        thiet_bi: Tên thiết bị trong configs/actuator.yaml.
        hanh_dong: Hành động cần thực hiện ("bat" hoặc "tat").
        nguon: ID người dùng đã kích hoạt; None nếu hệ thống tự phát.
        thoi_diem: Dấu thời gian Unix, đơn vị giây.
    """

    thiet_bi: str
    hanh_dong: str
    nguon: str | None
    thoi_diem: float
