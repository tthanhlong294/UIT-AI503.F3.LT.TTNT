"""Chọn backend cho khối phát hiện khuôn mặt theo dạng đường dẫn mô hình.

Suy backend ra từ đường dẫn thay vì bắt khai báo trong config: bước 2.6 quét một danh
sách mô hình trộn cả hai định dạng trong cùng một lần chạy, nên backend là thuộc tính
của từng mô hình chứ không phải của cả phiên đo — xem
`docs/dac-ta/P2-05-detector-ncnn.md` §5.3.
"""

from pathlib import Path

from src.common.exceptions import LoiCauHinh
from src.common.logging import lay_logger
from src.detector.ncnn_backend import NcnnFaceDetector
from src.detector.yolo_face import YoloFaceDetector

logger = lay_logger(__name__)

_DUOI_ONNX = ".onnx"
_TEP_NHAN_DANG_NCNN = "model.ncnn.param"


def tao_bo_phat_hien(duong_dan: Path | str, cfg: dict) -> YoloFaceDetector | NcnnFaceDetector:
    """Chọn và khởi tạo backend phát hiện khuôn mặt theo dạng đường dẫn mô hình.

    Quy tắc, theo đúng thứ tự:
      * tệp có đuôi ``.onnx``                -> YoloFaceDetector
      * thư mục chứa ``model.ncnn.param``    -> NcnnFaceDetector
      * còn lại                              -> LoiCauHinh nêu rõ đã nhận gì

    Args:
        duong_dan: Đường dẫn tệp ``.onnx`` hoặc thư mục ``*_ncnn_model``.
        cfg: Toàn bộ nội dung configs/detect.yaml.

    Returns:
        Bộ phát hiện đã khởi tạo, dùng chung giao diện ``detect(khung_hinh) -> list[FaceBox]``.

    Raises:
        LoiCauHinh: đường dẫn không khớp dạng nào ở trên.
        LoiMoHinh: đường dẫn khớp dạng nhưng mô hình không nạp được (do backend ném ra).
    """
    p = Path(duong_dan)

    if p.suffix == _DUOI_ONNX:
        logger.info("Factory chọn backend ONNX cho %s", p)
        return YoloFaceDetector(p, cfg)

    if p.is_dir() and (p / _TEP_NHAN_DANG_NCNN).is_file():
        logger.info("Factory chọn backend NCNN cho %s", p)
        return NcnnFaceDetector(p, cfg)

    raise LoiCauHinh(
        f"Không nhận dạng được backend từ đường dẫn: '{p}' (đuôi {p.suffix!r}, "
        f"là thư mục: {p.is_dir()}). "
        f"Cần tệp đuôi '{_DUOI_ONNX}' hoặc thư mục chứa '{_TEP_NHAN_DANG_NCNN}'."
    )
