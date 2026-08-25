"""Interface chung cho khối nhận diện danh tính khuôn mặt (KHỐI 1d).

Định nghĩa hợp đồng `BoNhanDien` mà mọi backend nhận diện (ArcFace và các backend bổ sung sau
này) phải tuân theo, và hàm độ tương đồng cosin dùng chung giữa các backend. Module này KHÔNG
phụ thuộc bất kỳ backend cụ thể nào — mỗi backend (ví dụ `arcface_backend.py`) chỉ import từ
đây, không ngược lại.
"""

from abc import ABC, abstractmethod

import numpy as np


class BoNhanDien(ABC):
    """Interface chung cho mọi backend nhận diện."""

    @property
    @abstractmethod
    def so_chieu(self) -> int:
        """Số chiều vectơ đặc trưng, đọc từ mô hình chứ không từ cấu hình."""

    @abstractmethod
    def trich_dac_trung(self, anh: np.ndarray) -> np.ndarray:
        """Trích vectơ đặc trưng từ MỘT ảnh khuôn mặt đã căn chỉnh.

        Args:
            anh: Ảnh BGR uint8, hình dạng (112, 112, 3).

        Returns:
            Vectơ đặc trưng hình dạng (so_chieu,), kiểu float32,
            **đã chuẩn hoá L2** — độ dài bằng 1.

        Raises:
            ValueError: ảnh sai hình dạng, sai kiểu, hoặc rỗng.
        """

    @abstractmethod
    def enroll(self, danh_sach_anh: list[np.ndarray], cfg: dict) -> np.ndarray:
        """Đăng ký một người từ nhiều ảnh.

        Chuẩn hoá L2 TỪNG vectơ trước, rồi lấy trung bình, rồi chuẩn hoá L2 lần nữa.
        Không chuẩn hoá trước khi trung bình thì ảnh có vectơ dài sẽ lấn át phần còn lại,
        trong khi độ dài không mang thông tin về danh tính.

        Args:
            danh_sach_anh: Danh sách ảnh khuôn mặt đã căn chỉnh của cùng một người.
            cfg: Cấu hình đăng ký (mục "enroll" của configs/recognize.yaml),
                chứa khoá `min_images_per_user`.

        Returns:
            Vectơ đặc trưng đại diện cho người đó, hình dạng (so_chieu,), đã chuẩn hoá L2.

        Raises:
            ValueError: danh sách rỗng, hoặc ít hơn `enroll.min_images_per_user`.
        """

    @abstractmethod
    def identify(
        self, anh: np.ndarray, gallery: dict[str, np.ndarray], nguong: float
    ) -> tuple[str | None, float]:
        """So khớp một khuôn mặt với danh sách đã đăng ký.

        Args:
            anh: Ảnh khuôn mặt đã căn chỉnh cần nhận diện.
            gallery: Ánh xạ mã người dùng sang vectơ đặc trưng đã đăng ký.
            nguong: Ngưỡng độ tương đồng cosin để chấp nhận một danh tính.

        Returns:
            (mã_người_dùng, độ_tương_đồng). Trả về (None, độ_tương_đồng_cao_nhất)
            khi không ai vượt ngưỡng — người lạ.
            Với gallery rỗng, trả về (None, 0.0).
        """


def do_tuong_dong(a: np.ndarray, b: np.ndarray) -> float:
    """Độ tương đồng cosin giữa hai vectơ.

    Args:
        a: Vectơ thứ nhất.
        b: Vectơ thứ hai.

    Returns:
        Độ tương đồng cosin, giá trị trong khoảng [-1, 1].

    Raises:
        ValueError: hai vectơ khác số chiều, hoặc có vectơ độ dài bằng 0.
    """
    if a.shape != b.shape:
        raise ValueError(f"Hai vectơ khác số chiều: {a.shape} và {b.shape}")

    do_dai_a = float(np.linalg.norm(a))
    do_dai_b = float(np.linalg.norm(b))
    if do_dai_a == 0.0 or do_dai_b == 0.0:
        raise ValueError("Không thể tính độ tương đồng cosin với vectơ có độ dài bằng 0")

    return float(np.dot(a, b) / (do_dai_a * do_dai_b))
