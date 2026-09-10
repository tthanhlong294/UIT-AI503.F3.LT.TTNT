"""Factory dựng bộ chấp hành theo khoá ``backend`` trong cấu hình.

Khác :func:`~src.capture.factory.tao_bo_thu_hinh`, factory này **không có nhánh
``auto``** và **không gọi** :meth:`~src.actuator.base.BoChapHanh.mo` (đặc tả P5-01
§4.1, §5.10): không tồn tại phép dò nào phân biệt relay đã đấu với relay chưa đấu, nên
``auto`` chỉ có thể rơi về giả lập trong im lặng — một cái bẫy, không phải phép tự dò.
"""

from src.actuator.base import BoChapHanh
from src.common.exceptions import LoiCauHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)

THONG_BAO_CAM_AUTO = (
    "backend='auto' bị CẤM ở khối chấp hành: không có phép dò nào phân biệt được relay đã "
    "đấu dây với relay chưa đấu dây, nên 'auto' chỉ có thể rơi về giả lập trong im lặng. "
    "Khai báo tường minh backend='mock' hoặc backend='gpio'."
)
THONG_BAO_CHUA_CO_GPIO = (
    "backend='gpio' chưa được cài đặt — thuộc mã việc P5-03. Dùng backend='mock' cho tới khi "
    "có module relay và hardware/gpio-pinout.md."
)


def tao_bo_chap_hanh(cfg: dict) -> BoChapHanh:
    """Dựng bộ chấp hành theo khoá ``backend``. Không mở phần cứng.

    Factory chỉ kiểm khoá ``backend``; nhánh ``devices`` do
    :meth:`~src.actuator.base.BoChapHanh.__init__` kiểm, nhánh ``mock`` do
    :class:`~src.actuator.mock_actuator.ChapHanhGiaLap` kiểm.

    Args:
        cfg: Toàn bộ dict cấu hình đã nạp từ ``configs/actuator.yaml``.

    Returns:
        Đối tượng :class:`~src.actuator.base.BoChapHanh` ở trạng thái **chưa mở**.

    Raises:
        LoiCauHinh: Khi thiếu khoá ``backend``; ``backend`` là ``"auto"`` (bị cấm cố ý);
            ``backend`` là ``"gpio"`` (chưa cài, thuộc P5-03); hoặc ``backend`` là bất kỳ
            giá trị nào khác ``"mock"``.
    """
    if "backend" not in cfg:
        raise LoiCauHinh("Thiếu key bắt buộc: backend")
    backend = cfg["backend"]
    if backend == "mock":
        from src.actuator.mock_actuator import ChapHanhGiaLap

        return ChapHanhGiaLap(cfg)
    if backend == "auto":
        raise LoiCauHinh(THONG_BAO_CAM_AUTO)
    if backend == "gpio":
        raise LoiCauHinh(THONG_BAO_CHUA_CO_GPIO)
    raise LoiCauHinh(f"Backend không hợp lệ: {backend}. Giá trị cho phép: mock, gpio")
