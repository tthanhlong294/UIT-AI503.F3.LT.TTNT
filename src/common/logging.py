"""Module thiết lập và cung cấp hệ thống ghi log toàn ứng dụng."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.common.exceptions import LoiCauHinh

KICH_THUOC_TOI_DA_FILE_LOG = 10 * 1024 * 1024
SO_FILE_LOG_XOAY_VONG = 3
DINH_DANG_LOG = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"


def thiet_lap_log(muc: str = "INFO", file_log: str | Path | None = None) -> None:
    """Thiết lập logging toàn hệ thống. Gọi một lần khi khởi động.

    Args:
        muc: Mức ghi log ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL").
        file_log: Đường dẫn file lưu log (tuỳ chọn).

    Raises:
        LoiCauHinh: Nếu mức log không hợp lệ.
    """
    muc_str = muc.upper()
    if muc_str not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
        raise LoiCauHinh(f"Mức log không hợp lệ: '{muc}'")

    cap_do = getattr(logging, muc_str)
    root_logger = logging.getLogger()
    root_logger.setLevel(cap_do)

    # Đóng và xoá các handler cũ để tránh nhân đôi handler khi gọi nhiều lần
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    formatter = logging.Formatter(DINH_DANG_LOG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    if file_log is not None:
        file_log_path = Path(file_log)
        file_log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            file_log_path,
            maxBytes=KICH_THUOC_TOI_DA_FILE_LOG,
            backupCount=SO_FILE_LOG_XOAY_VONG,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)


def lay_logger(ten: str) -> logging.Logger:
    """Trả về logger con theo tên module, thường truyền __name__.

    Args:
        ten: Tên đại diện cho logger.

    Returns:
        Đối tượng logging.Logger tương ứng.
    """
    return logging.getLogger(ten)
