"""Backend chấp hành giả lập — không chạm phần cứng, không thể nhầm với thật.

:class:`ChapHanhGiaLap` là backend chạy trên PC/Docker và trong kiểm thử. Nó khai
``LA_GIA_LAP = True`` và phát một dòng ``WARNING`` mang nguyên văn
:data:`~src.actuator.base.CANH_BAO_GIA_LAP` mỗi khi mở, để không lượt vận hành nào
tưởng nhầm giả lập là phần cứng thật (đặc tả P5-01 §4.1, §4.3).
"""

import math
import time

from src.actuator.base import CANH_BAO_GIA_LAP, BoChapHanh
from src.common.exceptions import LoiCauHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)


class ChapHanhGiaLap(BoChapHanh):
    """Backend chấp hành giả lập: ghi log đầy đủ, không có tác động điện thật.

    Attributes:
        TEN_BACKEND: Luôn là ``"mock"``.
        LA_GIA_LAP: Luôn là ``True``.
    """

    TEN_BACKEND = "mock"
    LA_GIA_LAP = True

    def __init__(self, cfg: dict) -> None:
        """Khởi tạo backend giả lập.

        Args:
            cfg: Toàn bộ dict cấu hình — cần cả nhánh ``devices`` (lớp cơ sở đọc) lẫn
                nhánh ``mock`` (lớp này đọc).

        Raises:
            LoiCauHinh: Lỗi nhánh ``devices`` (xem :meth:`~src.actuator.base.BoChapHanh.__init__`);
                hoặc ``mock`` không phải dict/None; hoặc ``mock.do_tre_gia_lap_giay`` là
                ``bool``, không phải số, không hữu hạn, hoặc âm.
        """
        super().__init__(cfg)
        self._do_tre = self._nap_do_tre(cfg)

    @staticmethod
    def _nap_do_tre(cfg: dict) -> float:
        """Kiểm và trích ``mock.do_tre_gia_lap_giay`` (giây), mặc định ``0.0``.

        Thứ tự bốn phép kiểm là cố ý (P5-01 §5.9): loại ``bool`` trước khi kiểm kiểu số
        (vì ``isinstance(True, int)`` là ``True``); kiểm ``math.isfinite`` trước khi so
        ``< 0`` (vì ``nan < 0`` là ``False``, còn chờ vô hạn giây thì treo tiến trình).

        Args:
            cfg: Toàn bộ dict cấu hình.

        Returns:
            Độ trễ mô phỏng, số thực không âm hữu hạn.

        Raises:
            LoiCauHinh: Khi ``mock`` không phải dict/None, hoặc giá trị độ trễ là ``bool``,
                không phải ``int``/``float``, không hữu hạn, hoặc âm.
        """
        nhanh_mock = cfg.get("mock")
        if nhanh_mock is None:
            return 0.0
        if not isinstance(nhanh_mock, dict):
            raise LoiCauHinh("Khoá 'mock' phải là dict hoặc None")
        if "do_tre_gia_lap_giay" not in nhanh_mock:
            return 0.0
        gia_tri = nhanh_mock["do_tre_gia_lap_giay"]
        if isinstance(gia_tri, bool) or not isinstance(gia_tri, (int, float)):
            raise LoiCauHinh(
                f"mock.do_tre_gia_lap_giay phải là số int/float, nhận được: {gia_tri!r}"
            )
        if not math.isfinite(gia_tri):
            raise LoiCauHinh("mock.do_tre_gia_lap_giay phải là số hữu hạn")
        if gia_tri < 0:
            raise LoiCauHinh("mock.do_tre_gia_lap_giay không được âm")
        return float(gia_tri)

    def _mo_phan_cung(self) -> None:
        """Phát đúng một dòng ``WARNING`` mang nguyên văn cảnh báo giả lập."""
        logger.warning("%s", CANH_BAO_GIA_LAP)

    def _tac_dong_phan_cung(self, ten_thiet_bi: str, bat_len: bool) -> None:
        """Ghi log hành động giả lập; ngủ ``do_tre_gia_lap_giay`` giây nếu > 0.

        Args:
            ten_thiet_bi: Tên thiết bị.
            bat_len: ``True`` là bật thiết bị, ``False`` là tắt.
        """
        logger.info(
            "MOCK: đặt thiết bị %s sang %s — không có dòng điện, không có lệnh IR",
            ten_thiet_bi,
            "ON" if bat_len else "OFF",
        )
        if self._do_tre > 0:
            time.sleep(self._do_tre)
