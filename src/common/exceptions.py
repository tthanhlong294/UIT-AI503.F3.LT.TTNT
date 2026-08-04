"""Định nghĩa các ngoại lệ tuỳ chỉnh cho toàn hệ thống."""


class LoiHeThong(Exception):
    """Lỗi gốc của hệ thống — mọi ngoại lệ tự định nghĩa đều kế thừa lớp này."""


class LoiCauHinh(LoiHeThong):
    """Lỗi liên quan tới file cấu hình: không tồn tại, sai cú pháp, thiếu key bắt buộc."""


class LoiCamera(LoiHeThong):
    """Lỗi thiết bị thu hình: không mở được camera, mất kết nối, frame không hợp lệ."""


class LoiPhanCung(LoiHeThong):
    """Lỗi phần cứng chấp hành: GPIO, relay, module phát IR."""


class LoiMoHinh(LoiHeThong):
    """Lỗi mô hình: không nạp được weights, sai kích thước đầu vào, inference thất bại."""
