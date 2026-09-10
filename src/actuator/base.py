"""Lớp cơ sở cho khối chấp hành (KHỐI 3).

Module này định nghĩa :class:`BoChapHanh` — lớp cơ sở **có cài đặt** (Template Method,
xem đặc tả P5-01 §4.2) cho mọi backend điều khiển thiết bị. Toàn bộ phần dùng chung giữa
backend giả lập và backend GPIO thật đã cài sẵn ở đây: bảng thiết bị, bộ nhớ trạng thái
giả định, lịch sử lệnh, các phép kiểm hợp lệ, ghi log và trình tự fail-safe (R24). Backend
chỉ phải khai hai hằng lớp ``TEN_BACKEND`` / ``LA_GIA_LAP`` và cài một phương thức trừu
tượng duy nhất :meth:`BoChapHanh._tac_dong_phan_cung`.
"""

import time
from abc import ABC, abstractmethod

from src.common.exceptions import LoiCauHinh, LoiPhanCung
from src.common.logging import lay_logger
from src.common.types import Command

logger = lay_logger(__name__)

NGUON_HE_THONG = "he_thong"
HANH_DONG_HOP_LE: tuple[str, ...] = ("bat", "tat")
LOAI_THIET_BI_HOP_LE: tuple[str, ...] = ("relay", "ir")
PHUONG_THUC_KHOA: tuple[str, ...] = ("mo", "dong", "bat", "tat", "thuc_thi")
CANH_BAO_GIA_LAP = (
    "KHỐI CHẤP HÀNH ĐANG CHẠY BACKEND GIẢ LẬP — "
    "KHÔNG CÓ DÒNG ĐIỆN NÀO ĐI QUA RELAY VÀ KHÔNG CÓ LỆNH IR NÀO ĐƯỢC PHÁT"
)


class BoChapHanh(ABC):
    """Lớp cơ sở cho mọi backend chấp hành. Phần chung đã cài sẵn (đặc tả P5-01 §4.2).

    Lớp con **bắt buộc** khai hai hằng lớp ``TEN_BACKEND`` (chuỗi không rỗng) và
    ``LA_GIA_LAP`` (bool) ngay trong thân lớp, và **không được** ghi đè bất kỳ phương
    thức nào trong :data:`PHUONG_THUC_KHOA`. :meth:`__init_subclass__` từ chối định nghĩa
    lớp vi phạm ngay lúc import.

    Attributes:
        TEN_BACKEND: Tên backend thật đang chạy — literal khai ở lớp con, không đọc từ cấu hình.
        LA_GIA_LAP: ``True`` nếu đây là backend giả lập, không chạm phần cứng thật.
    """

    TEN_BACKEND: str
    LA_GIA_LAP: bool

    def __init_subclass__(cls, **kwargs: object) -> None:
        """Từ chối lớp con không tự khai nguồn thật hoặc ghi đè phần chịu lực.

        Args:
            cls: Lớp con vừa được định nghĩa.
            **kwargs: Tham số lớp truyền tiếp cho lớp cha.

        Raises:
            TypeError: Khi lớp con không khai ``TEN_BACKEND`` (hoặc khai rỗng), không khai
                ``LA_GIA_LAP``, hoặc ghi đè một phương thức trong :data:`PHUONG_THUC_KHOA`.
        """
        super().__init_subclass__(**kwargs)
        if "TEN_BACKEND" not in cls.__dict__ or not cls.__dict__["TEN_BACKEND"]:
            raise TypeError(
                f"Lớp con {cls.__name__} phải tự khai hằng lớp TEN_BACKEND (chuỗi không rỗng) "
                "trong thân lớp — tên backend đến từ lớp, không đến từ cấu hình (P5-01 §4.3)."
            )
        if "LA_GIA_LAP" not in cls.__dict__:
            raise TypeError(
                f"Lớp con {cls.__name__} phải tự khai hằng lớp LA_GIA_LAP trong thân lớp — "
                "quên khai là lỗi, không âm thầm nhận False (P5-01 §4.3)."
            )
        for ten_phuong_thuc in PHUONG_THUC_KHOA:
            if ten_phuong_thuc in cls.__dict__:
                raise TypeError(
                    f"Lớp con {cls.__name__} không được ghi đè phương thức khoá "
                    f"{ten_phuong_thuc!r}: vòng đời và trình tự fail-safe là phần chịu lực "
                    "chung, backend chỉ cài _tac_dong_phan_cung (P5-01 §5.2)."
                )

    def __init__(self, cfg: dict) -> None:
        """Nạp bảng thiết bị từ nhánh ``devices``. Không chạm phần cứng, không gọi :meth:`mo`.

        Sau khi khởi tạo: :attr:`dang_mo` là ``False`` và lịch sử rỗng.

        Args:
            cfg: Toàn bộ dict cấu hình đã nạp từ ``configs/actuator.yaml``.

        Raises:
            LoiCauHinh: Khi thiếu khoá ``devices``; ``devices`` không phải dict hoặc rỗng;
                tên thiết bị không phải chuỗi hoặc rỗng; giá trị thiết bị không phải dict;
                thiếu khoá ``loai``; hoặc ``loai`` ngoài :data:`LOAI_THIET_BI_HOP_LE`.
        """
        self.cfg = cfg
        self._thiet_bi: dict[str, str] = self._nap_devices(cfg)
        self._trang_thai: dict[str, bool] = {}
        self._lich_su: list[Command] = []
        self._dang_mo = False

    @staticmethod
    def _nap_devices(cfg: dict) -> dict[str, str]:
        """Kiểm và trích nhánh ``devices`` thành ánh xạ tên → loại.

        Args:
            cfg: Toàn bộ dict cấu hình.

        Returns:
            Ánh xạ ``{ten_thiet_bi: loai}`` theo đúng thứ tự khai trong cấu hình.

        Raises:
            LoiCauHinh: Xem :meth:`__init__`.
        """
        if "devices" not in cfg:
            raise LoiCauHinh("Thiếu key bắt buộc: devices")
        devices = cfg["devices"]
        if not isinstance(devices, dict) or not devices:
            raise LoiCauHinh("Khoá 'devices' phải là dict không rỗng, khai ít nhất một thiết bị")
        ket_qua: dict[str, str] = {}
        for ten, thong_tin in devices.items():
            if not isinstance(ten, str) or not ten.strip():
                raise LoiCauHinh(f"Tên thiết bị phải là chuỗi không rỗng, nhận được: {ten!r}")
            if not isinstance(thong_tin, dict):
                raise LoiCauHinh(
                    f"Cấu hình thiết bị {ten!r} phải là dict, "
                    f"nhận được: {type(thong_tin).__name__}"
                )
            if "loai" not in thong_tin:
                raise LoiCauHinh(f"Thiếu key bắt buộc: devices.{ten}.loai")
            loai = thong_tin["loai"]
            if loai not in LOAI_THIET_BI_HOP_LE:
                raise LoiCauHinh(
                    f"Thiết bị {ten!r} có loai không hợp lệ: {loai!r}. "
                    f"Giá trị cho phép: {', '.join(LOAI_THIET_BI_HOP_LE)}"
                )
            ket_qua[ten] = loai
        return ket_qua

    # --- phơi ra nguồn thật (P5-01 §4.3) ---

    @property
    def ten_backend(self) -> str:
        """Tên backend **thật đang chạy**, lấy từ hằng lớp, không đọc cấu hình.

        Returns:
            Giá trị ``TEN_BACKEND`` của lớp cụ thể.
        """
        return type(self).TEN_BACKEND

    @property
    def la_gia_lap(self) -> bool:
        """Cho biết đối tượng này có phải backend giả lập hay không, lấy từ hằng lớp.

        Returns:
            Giá trị ``LA_GIA_LAP`` của lớp cụ thể.
        """
        return type(self).LA_GIA_LAP

    def mo_ta_nguon(self) -> dict[str, object]:
        """Mô tả nguồn thật của khối chấp hành để ``main.py`` và khối ghi log dùng.

        Returns:
            Dict ba khoá: ``backend`` (tên backend thật), ``la_gia_lap`` (bool), và
            ``canh_bao_nguon_gia_lap`` — chuỗi :data:`CANH_BAO_GIA_LAP` nếu đang giả lập,
            ``None`` nếu là phần cứng thật.
        """
        return {
            "backend": self.ten_backend,
            "la_gia_lap": self.la_gia_lap,
            "canh_bao_nguon_gia_lap": CANH_BAO_GIA_LAP if self.la_gia_lap else None,
        }

    # --- vòng đời ---

    @property
    def dang_mo(self) -> bool:
        """Trạng thái đóng/mở của khối chấp hành.

        Returns:
            ``True`` khi đang giữa :meth:`mo` và :meth:`dong`.
        """
        return self._dang_mo

    def mo(self) -> None:
        """Khởi động khối chấp hành và ép mọi thiết bị về TẮT ở cả bộ nhớ lẫn phần cứng.

        Gọi lại khi đã mở là luỹ đẳng — trả về ngay, không ghi phần cứng lần hai.
        ``dang_mo`` chỉ bật lên **sau** khi mọi lời ép TẮT thành công: không bảo đảm
        được trạng thái an toàn lúc khởi động thì từ chối khởi động (fail-safe, R24).

        Raises:
            Exception: Ngoại lệ bất kỳ do :meth:`_mo_phan_cung` hoặc
                :meth:`_tac_dong_phan_cung` ném ra được để lan ra ngoài; khi đó đối tượng
                ở lại trạng thái **chưa mở**.
        """
        if self._dang_mo:
            return
        self._trang_thai = {ten: False for ten in self._thiet_bi}
        self._lich_su = []
        self._mo_phan_cung()
        for ten in self.danh_sach_thiet_bi:
            self._tac_dong_phan_cung(ten, False)
        self._dang_mo = True
        logger.info(
            "Đã mở khối chấp hành (backend %s, %d thiết bị)",
            self.ten_backend,
            len(self._thiet_bi),
        )

    def dong(self) -> None:
        """Tắt mọi thiết bị đang bật rồi giải phóng phần cứng. **Không bao giờ ném.**

        Gọi khi chưa mở, hoặc gọi nhiều lần, đều an toàn. Mỗi lần tắt do :meth:`dong`
        thực hiện được ghi vào lịch sử với ``nguon = NGUON_HE_THONG`` — đây là bằng chứng
        fail-safe cho biên bản đo độ trễ và trang lịch sử ở Phase 6. Lỗi phần cứng lúc
        tắt chỉ được ghi ở mức ``ERROR``; trạng thái giả định vẫn coi là đã tắt (P5-01
        §4.6, §5.5).
        """
        if not self._dang_mo:
            return
        for ten in self.danh_sach_thiet_bi:
            if self._trang_thai.get(ten):
                try:
                    self._tac_dong_phan_cung(ten, False)
                except Exception as e:  # noqa: BLE001
                    logger.error("Không tắt được %s khi đóng: %s", ten, e)
                self._trang_thai[ten] = False
                self._lich_su.append(Command(ten, "tat", NGUON_HE_THONG, time.time()))
        try:
            self._dong_phan_cung()
        except Exception as e:  # noqa: BLE001
            logger.error("Lỗi khi giải phóng phần cứng khối chấp hành: %s", e)
        self._dang_mo = False
        logger.info("Đã đóng khối chấp hành")

    def __enter__(self) -> "BoChapHanh":  # noqa: PYI034
        """Vào khối ``with``: gọi :meth:`mo`.

        Returns:
            Chính đối tượng này.
        """
        self.mo()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Ra khỏi khối ``with``: gọi :meth:`dong` (chạy cả khi có ngoại lệ)."""
        self.dong()

    # --- tác động ---

    def bat(self, ten_thiet_bi: str, nguon: str | None = None) -> None:
        """Bật một thiết bị. Bật thiết bị đang bật là luỹ đẳng, không phải lỗi (P5-01 §4.5).

        Args:
            ten_thiet_bi: Tên thiết bị đã khai trong ``devices``.
            nguon: ID người dùng kích hoạt; ``None`` nếu hệ thống tự phát.

        Raises:
            LoiPhanCung: Khi chưa :meth:`mo` hoặc đã :meth:`dong`.
            LoiCauHinh: Khi ``ten_thiet_bi`` chưa khai trong cấu hình.
        """
        self._dat_trang_thai(ten_thiet_bi, True, Command(ten_thiet_bi, "bat", nguon, time.time()))

    def tat(self, ten_thiet_bi: str, nguon: str | None = None) -> None:
        """Tắt một thiết bị. Tắt thiết bị đang tắt là luỹ đẳng, không phải lỗi (P5-01 §4.5).

        Args:
            ten_thiet_bi: Tên thiết bị đã khai trong ``devices``.
            nguon: ID người dùng kích hoạt; ``None`` nếu hệ thống tự phát.

        Raises:
            LoiPhanCung: Khi chưa :meth:`mo` hoặc đã :meth:`dong`.
            LoiCauHinh: Khi ``ten_thiet_bi`` chưa khai trong cấu hình.
        """
        self._dat_trang_thai(ten_thiet_bi, False, Command(ten_thiet_bi, "tat", nguon, time.time()))

    def thuc_thi(self, lenh: Command) -> None:
        """Thi hành một :class:`Command` do khối quyết định sinh ra, giữ nguyên dấu thời gian.

        Bản ghi vào lịch sử là **chính** đối tượng ``lenh`` — ``nguon`` và ``thoi_diem``
        không bị đóng mốc lại, vì phép đo độ trễ đầu-cuối (bước 5.6) sẽ trừ đúng
        ``thoi_diem`` do khối quyết định gán. Không chuẩn hoá chữ hoa/thường của
        ``hanh_dong``.

        Args:
            lenh: Lệnh cần thi hành.

        Raises:
            ValueError: Khi ``lenh`` không phải :class:`Command`, hoặc ``lenh.hanh_dong``
                ngoài :data:`HANH_DONG_HOP_LE`.
            LoiPhanCung: Khi chưa :meth:`mo` hoặc đã :meth:`dong`.
            LoiCauHinh: Khi ``lenh.thiet_bi`` chưa khai trong cấu hình.
        """
        if not isinstance(lenh, Command):
            thong_bao_sai_kieu = f"thuc_thi cần một Command, nhận được: {type(lenh).__name__}"
            raise ValueError(thong_bao_sai_kieu)  # noqa: TRY004
        if lenh.hanh_dong not in HANH_DONG_HOP_LE:
            raise ValueError(f"Hành động không hợp lệ: {lenh.hanh_dong!r}")
        self._dat_trang_thai(lenh.thiet_bi, lenh.hanh_dong == "bat", lenh)

    def _dat_trang_thai(self, ten: str, dich: bool, lenh: Command) -> None:
        """Trình tự nội bộ dùng chung cho :meth:`bat`, :meth:`tat`, :meth:`thuc_thi`.

        Kiểm ``dang_mo`` **trước** kiểm tên thiết bị (P5-01 §5.6): gọi thiết bị lạ khi
        chưa mở phải là :class:`LoiPhanCung`, không phải :class:`LoiCauHinh`. Ghi lịch
        sử **sau cùng**, ở cả hai nhánh (đổi trạng thái và luỹ đẳng). Ngoại lệ từ
        :meth:`_tac_dong_phan_cung` lan ra ngoài và **không** để lại bản ghi.

        Args:
            ten: Tên thiết bị.
            dich: Trạng thái đích — ``True`` là bật, ``False`` là tắt.
            lenh: Bản ghi lệnh sẽ nối vào lịch sử.

        Raises:
            LoiPhanCung: Khi chưa :meth:`mo` hoặc đã :meth:`dong`.
            LoiCauHinh: Khi ``ten`` chưa khai trong cấu hình.
        """
        if not self._dang_mo:
            raise LoiPhanCung(
                "Khối chấp hành chưa mở hoặc đã đóng — gọi mo() trước khi tác động thiết bị"
            )
        if ten not in self._thiet_bi:
            raise LoiCauHinh(f"Thiết bị chưa khai báo trong cấu hình: {ten}")
        if self._trang_thai[ten] != dich:
            self._tac_dong_phan_cung(ten, dich)
            self._trang_thai[ten] = dich
            logger.info(
                "Đặt thiết bị %s sang %s (nguồn: %s)",
                ten,
                "BẬT" if dich else "TẮT",
                lenh.nguon,
            )
        else:
            logger.debug("Thiết bị %s đã ở trạng thái đích, bỏ qua tác động phần cứng", ten)
        self._lich_su.append(lenh)

    # --- đọc ---

    @property
    def danh_sach_thiet_bi(self) -> tuple[str, ...]:
        """Tên mọi thiết bị đã khai, **sắp theo bảng chữ cái** bất kể thứ tự trong YAML.

        Returns:
            Tuple tên thiết bị đã sắp xếp.
        """
        return tuple(sorted(self._thiet_bi))

    def loai_thiet_bi(self, ten_thiet_bi: str) -> str:
        """Trả về loại (``relay`` hoặc ``ir``) của một thiết bị.

        Args:
            ten_thiet_bi: Tên thiết bị đã khai trong ``devices``.

        Returns:
            Chuỗi loại thiết bị.

        Raises:
            LoiCauHinh: Khi ``ten_thiet_bi`` chưa khai trong cấu hình.
        """
        if ten_thiet_bi not in self._thiet_bi:
            raise LoiCauHinh(f"Thiết bị chưa khai báo trong cấu hình: {ten_thiet_bi}")
        return self._thiet_bi[ten_thiet_bi]

    def trang_thai(self, ten_thiet_bi: str) -> bool:
        """Trạng thái **giả định** của một thiết bị, đọc từ bộ nhớ trong.

        Đây là trạng thái *giả định*: hệ thống ghi lại lệnh đã phát, không đo lại phần
        cứng (IR là một chiều, không có phản hồi — P5-01 §4.6). Phase 6 hiển thị con số
        này lên dashboard và báo cáo phải nói rõ đó là giả định.

        Args:
            ten_thiet_bi: Tên thiết bị đã khai trong ``devices``.

        Returns:
            ``True`` nếu thiết bị được giả định là đang bật.

        Raises:
            LoiPhanCung: Khi chưa :meth:`mo` hoặc đã :meth:`dong`.
            LoiCauHinh: Khi ``ten_thiet_bi`` chưa khai trong cấu hình.
        """
        if not self._dang_mo:
            raise LoiPhanCung("Khối chấp hành chưa mở hoặc đã đóng")
        if ten_thiet_bi not in self._thiet_bi:
            raise LoiCauHinh(f"Thiết bị chưa khai báo trong cấu hình: {ten_thiet_bi}")
        return self._trang_thai[ten_thiet_bi]

    def trang_thai_tat_ca(self) -> dict[str, bool]:
        """Trạng thái **giả định** của mọi thiết bị, dưới dạng bản sao.

        Trạng thái *giả định* — xem :meth:`trang_thai`. Bản trả về là bản sao: người gọi
        sửa nó không ảnh hưởng trạng thái trong.

        Returns:
            Dict ``{ten_thiet_bi: bool}`` mới, độc lập với bộ nhớ trong.

        Raises:
            LoiPhanCung: Khi chưa :meth:`mo` hoặc đã :meth:`dong`.
        """
        if not self._dang_mo:
            raise LoiPhanCung("Khối chấp hành chưa mở hoặc đã đóng")
        return dict(self._trang_thai)

    @property
    def lich_su(self) -> list[Command]:
        """Lịch sử mọi lệnh đã được chấp nhận, dưới dạng bản sao.

        Ghi cả lệnh luỹ đẳng không đổi trạng thái, **trừ** các lời ép tắt lúc :meth:`mo`.
        Lệnh ném ngoại lệ không để lại bản ghi.

        Returns:
            Danh sách :class:`Command` mới; sửa nó không ảnh hưởng trạng thái trong.
        """
        return list(self._lich_su)

    @property
    def lich_su_rut_gon(self) -> list[tuple[str, str]]:
        """Lịch sử rút gọn thành dãy ``(thiet_bi, hanh_dong)`` để khẳng định bằng ``==``.

        Returns:
            Danh sách cặp ``(thiet_bi, hanh_dong)`` theo đúng thứ tự lịch sử.
        """
        return [(c.thiet_bi, c.hanh_dong) for c in self._lich_su]

    # --- điểm nối cho backend ---

    @abstractmethod
    def _tac_dong_phan_cung(self, ten_thiet_bi: str, bat_len: bool) -> None:
        """Ghi mức tác động lên phần cứng. **Phương thức trừu tượng duy nhất.**

        Lớp con chỉ ghi mức điện / phát lệnh IR. Không kiểm hợp lệ, không ghi lịch sử,
        không đổi bộ nhớ trạng thái — lớp cơ sở làm hết.

        Args:
            ten_thiet_bi: Tên thiết bị.
            bat_len: ``True`` nghĩa là "thiết bị BẬT", không phải "chân ở mức HIGH".
        """

    def _mo_phan_cung(self) -> None:
        """Mở tài nguyên phần cứng. Mặc định không làm gì."""

    def _dong_phan_cung(self) -> None:
        """Giải phóng tài nguyên phần cứng. Mặc định không làm gì."""
