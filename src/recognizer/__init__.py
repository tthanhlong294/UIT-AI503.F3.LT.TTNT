"""Khối nhận diện danh tính khuôn mặt (KHỐI 1d).

Biến ảnh khuôn mặt đã căn chỉnh thành vectơ đặc trưng và so khớp với danh sách đã đăng ký.
"""

from .dlib_backend import DlibFaceRecognizer
from .factory import TEN_BACKEND_ARCFACE, TEN_BACKEND_DLIB, tao_bo_nhan_dien

__all__ = [
    "TEN_BACKEND_ARCFACE",
    "TEN_BACKEND_DLIB",
    "DlibFaceRecognizer",
    "tao_bo_nhan_dien",
]
