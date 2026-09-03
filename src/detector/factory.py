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

TEN_BACKEND_ONNX = "onnx"
TEN_BACKEND_NCNN = "ncnn"


def tra_ten_backend(duong_dan: Path | str) -> str:
    """Suy tên backend từ DẠNG đường dẫn, KHÔNG khởi tạo mô hình.

    Dùng đúng bộ quy tắc của `tao_bo_phat_hien`, để hai hàm không bao giờ bất đồng
    (P2-06b §5.2): tệp `.onnx` -> ONNX, thư mục chứa `model.ncnn.param` -> NCNN.

    Args:
        duong_dan: Đường dẫn tệp `.onnx` hoặc thư mục `*_ncnn_model`.

    Returns:
        `TEN_BACKEND_ONNX` hoặc `TEN_BACKEND_NCNN`.

    Raises:
        LoiCauHinh: đường dẫn không khớp dạng nào — cùng thông báo mà `tao_bo_phat_hien`
            vẫn ném, không viết lại chuỗi khác.
    """
    p = Path(duong_dan)

    if p.suffix == _DUOI_ONNX:
        return TEN_BACKEND_ONNX

    if p.is_dir() and (p / _TEP_NHAN_DANG_NCNN).is_file():
        return TEN_BACKEND_NCNN

    raise LoiCauHinh(
        f"Không nhận dạng được backend từ đường dẫn: '{p}' (đuôi {p.suffix!r}, "
        f"là thư mục: {p.is_dir()}). "
        f"Cần tệp đuôi '{_DUOI_ONNX}' hoặc thư mục chứa '{_TEP_NHAN_DANG_NCNN}'."
    )


def tao_bo_phat_hien(duong_dan: Path | str, cfg: dict) -> YoloFaceDetector | NcnnFaceDetector:
    """Chọn và khởi tạo backend phát hiện khuôn mặt theo dạng đường dẫn mô hình.

    Gọi lại `tra_ten_backend` để nhận dạng, rồi mới khởi tạo lớp tương ứng — chỉ một bộ
    quy tắc nhận dạng cho cả hai hàm (P2-06b §5.2), tránh viết điều kiện hai lần rồi trôi
    khỏi nhau.

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
    ten_backend = tra_ten_backend(p)

    if ten_backend == TEN_BACKEND_ONNX:
        logger.info("Factory chọn backend ONNX cho %s", p)
        return YoloFaceDetector(p, cfg)

    logger.info("Factory chọn backend NCNN cho %s", p)
    return NcnnFaceDetector(p, cfg)
