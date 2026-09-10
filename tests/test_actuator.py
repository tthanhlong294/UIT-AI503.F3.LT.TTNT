"""Kiểm thử cho khối chấp hành (KHỐI 3) — đặc tả P5-01.

Mỗi hàm ``test_dongNN_*`` phủ đúng một dòng của bảng ca kiểm thử §6 trong
``docs/dac-ta/P5-01-actuator-base-mock.md``. Bộ kiểm thử chạy được khi thiếu ``git``,
``.git/``, mọi gói phần cứng GPIO và mọi thứ ``.dockerignore`` loại khỏi ảnh
``faceid:arm64`` — tệp duy nhất trong kho mà ca kiểm thử đọc là ``configs/actuator.yaml``.
"""

import contextlib
import logging
import time
from pathlib import Path

import pytest

from src.actuator.base import (
    CANH_BAO_GIA_LAP,
    NGUON_HE_THONG,
    BoChapHanh,
)
from src.actuator.factory import (
    THONG_BAO_CAM_AUTO,
    THONG_BAO_CHUA_CO_GPIO,
    tao_bo_chap_hanh,
)
from src.actuator.mock_actuator import ChapHanhGiaLap
from src.common.config import nap_cau_hinh
from src.common.exceptions import LoiCauHinh, LoiPhanCung
from src.common.types import Command

# --------------------------------------------------------------------------- #
# Tiện ích dựng cấu hình và đối tượng                                          #
# --------------------------------------------------------------------------- #


def cfg2() -> dict:
    """Cấu hình tối thiểu hai thiết bị (``CFG2`` trong §6)."""
    return {
        "backend": "mock",
        "devices": {"den": {"loai": "relay"}, "tivi": {"loai": "ir"}},
    }


def cfg1() -> dict:
    """Cấu hình chỉ có ``den`` (``CFG1`` trong §6)."""
    return {"backend": "mock", "devices": {"den": {"loai": "relay"}}}


def mo_act(cfg: dict | None = None) -> ChapHanhGiaLap:
    """Trả về một :class:`ChapHanhGiaLap` đã ``mo()``."""
    act = ChapHanhGiaLap(cfg if cfg is not None else cfg2())
    act.mo()
    return act


def _cfg_that() -> dict:
    """Nạp tệp ``configs/actuator.yaml`` thật của kho (§3.7, Nhóm I)."""
    goc = Path(__file__).resolve().parents[1]
    return nap_cau_hinh(goc / "configs" / "actuator.yaml")


def _tao_lop_con(**thanh_phan: object) -> type:
    """Dựng một lớp con của :class:`BoChapHanh` (kích hoạt ``__init_subclass__``)."""
    thanh_phan.setdefault("_tac_dong_phan_cung", lambda self, ten_thiet_bi, bat_len: None)
    return type("LopConKiemThu", (BoChapHanh,), dict(thanh_phan))


# --------------------------------------------------------------------------- #
# Ba lớp phụ trợ dựng riêng cho kiểm thử (§5.12)                               #
# --------------------------------------------------------------------------- #


class ChapHanhDem(BoChapHanh):
    """Đếm mọi lời ghi phần cứng."""

    TEN_BACKEND = "dem"
    LA_GIA_LAP = True

    def __init__(self, cfg: dict) -> None:
        super().__init__(cfg)
        self.ghi_nhan: list[tuple[str, bool]] = []

    def _tac_dong_phan_cung(self, ten_thiet_bi: str, bat_len: bool) -> None:
        self.ghi_nhan.append((ten_thiet_bi, bat_len))


class ChapHanhNem(BoChapHanh):
    """Lời ghi phần cứng ném ``RuntimeError`` khi công tắc đang bật."""

    TEN_BACKEND = "nem"
    LA_GIA_LAP = True

    def __init__(self, cfg: dict, bat_dau_nem: bool = False) -> None:
        super().__init__(cfg)
        self.bat_dau_nem = bat_dau_nem

    def _tac_dong_phan_cung(self, ten_thiet_bi: str, bat_len: bool) -> None:
        if self.bat_dau_nem:
            raise RuntimeError(f"phần cứng hỏng khi ghi {ten_thiet_bi}={bat_len}")


class ChapHanhGiaVoThat(ChapHanhDem):
    """Lớp tự khai là phần cứng thật — dùng cho các dòng CẶP của phần cảnh báo giả lập."""

    TEN_BACKEND = "gia_vo_that"
    LA_GIA_LAP = False


# --------------------------------------------------------------------------- #
# Nhóm A — cấu trúc gói và ba phép từ chối của __init_subclass__ (§5.2)        #
# --------------------------------------------------------------------------- #


def test_dong01_danh_sach_file_trang():
    """01 — đúng bốn tệp ``.py`` trong ``src/actuator/``, không thừa tệp nào."""
    goc = Path(__file__).resolve().parents[1]
    assert {p.name for p in (goc / "src" / "actuator").glob("*.py")} == {
        "__init__.py",
        "base.py",
        "mock_actuator.py",
        "factory.py",
    }


def test_dong02_thieu_ten_backend_bi_tu_choi():
    """02 — lớp con không khai ``TEN_BACKEND`` → ``TypeError``."""
    with pytest.raises(TypeError, match="TEN_BACKEND"):
        _tao_lop_con(LA_GIA_LAP=True)


def test_dong03_ten_backend_rong_bi_tu_choi():
    """03 — lớp con khai ``TEN_BACKEND = ""`` → ``TypeError``."""
    with pytest.raises(TypeError, match="TEN_BACKEND"):
        _tao_lop_con(TEN_BACKEND="", LA_GIA_LAP=True)


def test_dong04_thieu_la_gia_lap_bi_tu_choi():
    """04 — lớp con không khai ``LA_GIA_LAP`` → ``TypeError``."""
    with pytest.raises(TypeError, match="LA_GIA_LAP"):
        _tao_lop_con(TEN_BACKEND="x")


def test_dong05_ghi_de_thuc_thi_bi_tu_choi():
    """05 — lớp con ghi đè ``thuc_thi`` → ``TypeError``."""
    with pytest.raises(TypeError, match="thuc_thi"):
        _tao_lop_con(TEN_BACKEND="x", LA_GIA_LAP=True, thuc_thi=lambda self, lenh: None)


def test_dong06_ghi_de_bat_bi_tu_choi():
    """06 — lớp con ghi đè ``bat`` → ``TypeError``."""
    with pytest.raises(TypeError, match="bat"):
        _tao_lop_con(
            TEN_BACKEND="x",
            LA_GIA_LAP=True,
            bat=lambda self, ten, nguon=None: None,
        )


def test_dong07_ghi_de_dong_bi_tu_choi():
    """07 — lớp con ghi đè ``dong`` → ``TypeError``."""
    with pytest.raises(TypeError, match="dong"):
        _tao_lop_con(TEN_BACKEND="x", LA_GIA_LAP=True, dong=lambda self: None)


def test_dong08_duong_cap_lop_con_hop_le():
    """08 — đường cặp: lớp con khai đủ hai hằng, không ghi đè gì."""
    assert ChapHanhDem.TEN_BACKEND == "dem"


def test_dong09_mock_khong_ghi_de_thuc_thi():
    """09 — ``ChapHanhGiaLap`` không ghi đè ``thuc_thi``."""
    assert ChapHanhGiaLap.thuc_thi is BoChapHanh.thuc_thi


def test_dong10_khong_khoi_tao_thang_lop_co_so():
    """10 — khởi tạo thẳng lớp cơ sở → ``TypeError`` (còn phương thức trừu tượng)."""
    with pytest.raises(TypeError):
        BoChapHanh(cfg2())


# --------------------------------------------------------------------------- #
# Nhóm B — factory và phép cấm auto (§4.1, §5.10)                              #
# --------------------------------------------------------------------------- #


def test_dong11_thieu_backend():
    """11 — thiếu khoá ``backend``."""
    with pytest.raises(LoiCauHinh, match="Thiếu key bắt buộc: backend"):
        tao_bo_chap_hanh({"devices": {"den": {"loai": "relay"}}})


def test_dong12_backend_mock_tra_dung_lop():
    """12 — ``backend: "mock"`` → ``ChapHanhGiaLap``."""
    assert isinstance(tao_bo_chap_hanh(cfg2()), ChapHanhGiaLap)


def test_dong13_factory_khong_tu_mo():
    """13 — factory không tự ``mo()``."""
    assert tao_bo_chap_hanh(cfg2()).dang_mo is False


def test_dong14_auto_bi_tu_choi():
    """14 — ``backend: "auto"`` → ``LoiCauHinh``."""
    with pytest.raises(LoiCauHinh):
        tao_bo_chap_hanh({**cfg2(), "backend": "auto"})


def test_dong15_auto_neu_dich_danh_gia_tri():
    """15 — thông báo của ``auto`` nêu đích danh giá trị."""
    with pytest.raises(LoiCauHinh) as e:
        tao_bo_chap_hanh({**cfg2(), "backend": "auto"})
    assert "auto" in str(e.value)


def test_dong16_auto_neu_ro_la_phep_cam_co_y():
    """16 — thông báo của ``auto`` nêu rõ đây là phép cấm cố ý."""
    with pytest.raises(LoiCauHinh) as e:
        tao_bo_chap_hanh({**cfg2(), "backend": "auto"})
    assert "CẤM" in str(e.value)


def test_dong17_gpio_bi_tu_choi():
    """17 — ``backend: "gpio"`` → ``LoiCauHinh``."""
    with pytest.raises(LoiCauHinh):
        tao_bo_chap_hanh({**cfg2(), "backend": "gpio"})


def test_dong18_gpio_tro_sang_ma_viec_ke_tiep():
    """18 — thông báo của ``gpio`` trỏ sang mã việc kế tiếp."""
    with pytest.raises(LoiCauHinh) as e:
        tao_bo_chap_hanh({**cfg2(), "backend": "gpio"})
    assert "P5-03" in str(e.value)


def test_dong19_auto_khong_roi_chung_nhanh_voi_gpio():
    """19 — ``auto`` không rơi chung nhánh với ``gpio``."""
    assert THONG_BAO_CAM_AUTO != THONG_BAO_CHUA_CO_GPIO


def test_dong20_backend_la_bi_tu_choi():
    """20 — ``backend: "khong_co_that"`` → ``LoiCauHinh``."""
    with pytest.raises(LoiCauHinh, match="Backend không hợp lệ"):
        tao_bo_chap_hanh({**cfg2(), "backend": "khong_co_that"})


def test_dong21_auto_khong_roi_chung_nhanh_mac_dinh():
    """21 — ``auto`` không rơi chung nhánh mặc định."""
    with pytest.raises(LoiCauHinh) as e_auto:
        tao_bo_chap_hanh({**cfg2(), "backend": "auto"})
    with pytest.raises(LoiCauHinh) as e_khac:
        tao_bo_chap_hanh({**cfg2(), "backend": "khong_co_that"})
    assert str(e_auto.value) != str(e_khac.value)
    assert "Backend không hợp lệ" not in str(e_auto.value)


def test_dong22_backend_khong_phai_chuoi():
    """22 — ``backend: 123`` → ``LoiCauHinh`` nhánh mặc định."""
    with pytest.raises(LoiCauHinh, match="Backend không hợp lệ"):
        tao_bo_chap_hanh({**cfg2(), "backend": 123})


# --------------------------------------------------------------------------- #
# Nhóm C — phơi ra nguồn thật (§4.3)                                           #
# --------------------------------------------------------------------------- #


def test_dong23_ten_backend_qua_factory():
    """23 — dựng qua factory với ``backend: "mock"``."""
    assert tao_bo_chap_hanh(cfg2()).ten_backend == "mock"


def test_dong24_ten_backend_khong_doc_cau_hinh_noi_doi():
    """24 — dựng thẳng với cấu hình nói dối ``backend: "gpio"`` vẫn phơi ``"mock"``."""
    act = ChapHanhGiaLap({**cfg2(), "backend": "gpio"})
    assert act.ten_backend == "mock"


def test_dong25_la_gia_lap_khong_doc_cau_hinh_noi_doi():
    """25 — cùng đối tượng nói dối: ``la_gia_lap is True``."""
    act = ChapHanhGiaLap({**cfg2(), "backend": "gpio"})
    assert act.la_gia_lap is True


def test_dong26_mo_ta_nguon_dung_tap_khoa():
    """26 — tập khoá của ``mo_ta_nguon()``."""
    assert set(ChapHanhGiaLap(cfg2()).mo_ta_nguon()) == {
        "backend",
        "la_gia_lap",
        "canh_bao_nguon_gia_lap",
    }


def test_dong27_mo_ta_nguon_khoa_backend():
    """27 — ``mo_ta_nguon()`` khoá ``backend``."""
    assert ChapHanhGiaLap(cfg2()).mo_ta_nguon()["backend"] == "mock"


def test_dong28_mo_ta_nguon_khoa_la_gia_lap():
    """28 — ``mo_ta_nguon()`` khoá ``la_gia_lap``."""
    assert ChapHanhGiaLap(cfg2()).mo_ta_nguon()["la_gia_lap"] is True


def test_dong29_mo_ta_nguon_khoa_canh_bao():
    """29 — ``mo_ta_nguon()`` khoá cảnh báo mang nguyên văn chuỗi."""
    assert ChapHanhGiaLap(cfg2()).mo_ta_nguon()["canh_bao_nguon_gia_lap"] == CANH_BAO_GIA_LAP


def test_dong30_backend_that_canh_bao_la_none():
    """30 — đường cặp: backend tự khai là thật → cảnh báo là ``None``."""
    assert ChapHanhGiaVoThat(cfg2()).mo_ta_nguon()["canh_bao_nguon_gia_lap"] is None


def test_dong31_backend_that_la_gia_lap_false():
    """31 — đường cặp: cùng đối tượng → ``la_gia_lap is False``."""
    assert ChapHanhGiaVoThat(cfg2()).la_gia_lap is False


def test_dong32_mo_phat_nguyen_van_canh_bao(caplog):
    """32 — ``mo()`` của ``mock`` phát nguyên văn cảnh báo."""
    with caplog.at_level(logging.WARNING):
        ChapHanhGiaLap(cfg2()).mo()
    assert CANH_BAO_GIA_LAP in caplog.text


def test_dong33_canh_bao_o_muc_warning_tro_len(caplog):
    """33 — cảnh báo đó ở mức WARNING trở lên, không phải INFO."""
    with caplog.at_level(logging.WARNING):
        ChapHanhGiaLap(cfg2()).mo()
    assert any(r.levelno >= logging.WARNING for r in caplog.records)


def test_dong34_backend_that_khong_phat_canh_bao(caplog):
    """34 — đường cặp: backend thật ``mo()`` không phát cảnh báo nào."""
    with caplog.at_level(logging.WARNING):
        ChapHanhGiaVoThat(cfg2()).mo()
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []


# --------------------------------------------------------------------------- #
# Nhóm D — nạp devices (§5.3)                                                  #
# --------------------------------------------------------------------------- #


def test_dong35_thieu_devices():
    """35 — ``cfg`` không có ``devices``."""
    with pytest.raises(LoiCauHinh, match="Thiếu key bắt buộc: devices"):
        ChapHanhGiaLap({"backend": "mock"})


def test_dong36_devices_rong():
    """36 — ``devices: {}``."""
    with pytest.raises(LoiCauHinh, match="devices"):
        ChapHanhGiaLap({"backend": "mock", "devices": {}})


def test_dong37_devices_la_list():
    """37 — ``devices: []``."""
    with pytest.raises(LoiCauHinh, match="devices"):
        ChapHanhGiaLap({"backend": "mock", "devices": []})


def test_dong38_devices_la_chuoi():
    """38 — ``devices: "den"``."""
    with pytest.raises(LoiCauHinh, match="devices"):
        ChapHanhGiaLap({"backend": "mock", "devices": "den"})


def test_dong39_gia_tri_thiet_bi_khong_phai_dict():
    """39 — ``devices: {"den": "khong_phai_dict"}``."""
    with pytest.raises(LoiCauHinh, match="den"):
        ChapHanhGiaLap({"backend": "mock", "devices": {"den": "khong_phai_dict"}})


def test_dong40_thieu_loai():
    """40 — ``devices: {"den": {}}`` — thiếu ``loai``."""
    with pytest.raises(LoiCauHinh, match="loai"):
        ChapHanhGiaLap({"backend": "mock", "devices": {"den": {}}})


def test_dong41_loai_ngoai_tap():
    """41 — ``loai`` ngoài ``LOAI_THIET_BI_HOP_LE``."""
    with pytest.raises(LoiCauHinh, match="loai"):
        ChapHanhGiaLap({"backend": "mock", "devices": {"den": {"loai": "bong_den"}}})


def test_dong42_ten_rong():
    """42 — tên thiết bị rỗng."""
    with pytest.raises(LoiCauHinh, match="Tên thiết bị"):
        ChapHanhGiaLap({"backend": "mock", "devices": {"": {"loai": "relay"}}})


def test_dong43_ten_toan_khoang_trang():
    """43 — tên thiết bị toàn khoảng trắng."""
    with pytest.raises(LoiCauHinh, match="Tên thiết bị"):
        ChapHanhGiaLap({"backend": "mock", "devices": {"   ": {"loai": "relay"}}})


def test_dong44_ten_khong_phai_chuoi():
    """44 — tên thiết bị không phải chuỗi."""
    with pytest.raises(LoiCauHinh, match="Tên thiết bị"):
        ChapHanhGiaLap({"backend": "mock", "devices": {123: {"loai": "relay"}}})


def test_dong45_relay_khong_kem_gpio_van_dung_duoc():
    """45 — đường cặp: ``loai: "relay"`` không kèm khối ``gpio`` vẫn dựng được."""
    assert ChapHanhGiaLap(cfg1()).loai_thiet_bi("den") == "relay"


def test_dong46_ir_khong_kem_ir_van_dung_duoc():
    """46 — đường cặp: ``loai: "ir"`` không kèm khối ``ir`` vẫn dựng được."""
    assert ChapHanhGiaLap(cfg2()).loai_thiet_bi("tivi") == "ir"


def test_dong47_khoa_la_muc_tren_cung_bi_bo_qua():
    """47 — cấu hình có khoá lạ mức trên cùng (``decision``) vẫn nạp được."""
    act = ChapHanhGiaLap({**cfg2(), "decision": {"n_frame_xac_nhan": 3}})
    assert act.danh_sach_thiet_bi == ("den", "tivi")


def test_dong48_danh_sach_thiet_bi_sap_theo_bang_chu_cai():
    """48 — ``danh_sach_thiet_bi`` sắp theo bảng chữ cái dù YAML khai ngược."""
    act = ChapHanhGiaLap(
        {
            "backend": "mock",
            "devices": {"zzz": {"loai": "relay"}, "aaa": {"loai": "ir"}},
        }
    )
    assert act.danh_sach_thiet_bi == ("aaa", "zzz")


def test_dong49_loai_thiet_bi_ten_la():
    """49 — ``loai_thiet_bi`` với tên lạ."""
    with pytest.raises(LoiCauHinh, match="khong_co"):
        ChapHanhGiaLap(cfg2()).loai_thiet_bi("khong_co")


# --------------------------------------------------------------------------- #
# Nhóm E — tham số số mock.do_tre_gia_lap_giay (§5.9)                          #
# --------------------------------------------------------------------------- #


def test_dong50_khong_co_nhanh_mock_khong_ngu(monkeypatch):
    """50 — cfg không có nhánh ``mock``, gọi ``bat`` → không ngủ."""
    ghi_nhan: list = []
    monkeypatch.setattr(time, "sleep", ghi_nhan.append)
    act = ChapHanhGiaLap(cfg1())
    act.mo()
    ghi_nhan.clear()
    act.bat("den")
    assert ghi_nhan == []


def test_dong51_mock_none_dung_binh_thuong():
    """51 — ``mock: None``, dựng bình thường."""
    assert ChapHanhGiaLap({**cfg1(), "mock": None}).danh_sach_thiet_bi == ("den",)


def test_dong52_mock_khong_phai_dict():
    """52 — ``mock: "khong_phai_dict"``."""
    with pytest.raises(LoiCauHinh, match="mock"):
        ChapHanhGiaLap({**cfg1(), "mock": "khong_phai_dict"})


def test_dong53_do_tre_bang_khong_khong_ngu(monkeypatch):
    """53 — ``do_tre_gia_lap_giay: 0`` → không ngủ."""
    ghi_nhan: list = []
    monkeypatch.setattr(time, "sleep", ghi_nhan.append)
    act = ChapHanhGiaLap({**cfg1(), "mock": {"do_tre_gia_lap_giay": 0}})
    act.mo()
    ghi_nhan.clear()
    act.bat("den")
    assert ghi_nhan == []


def test_dong54_duong_thanh_cong_co_ngu(monkeypatch):
    """54 — đường thành công: ``do_tre_gia_lap_giay: 0.05``, gọi ``bat`` → ngủ đúng lượng."""
    ghi_nhan: list = []
    monkeypatch.setattr(time, "sleep", ghi_nhan.append)
    act = ChapHanhGiaLap({**cfg1(), "mock": {"do_tre_gia_lap_giay": 0.05}})
    act.mo()
    ghi_nhan.clear()
    act.bat("den")
    assert ghi_nhan == [0.05]


def test_dong55_do_tre_am():
    """55 — ``do_tre_gia_lap_giay: -0.1``."""
    with pytest.raises(LoiCauHinh, match="âm"):
        ChapHanhGiaLap({**cfg1(), "mock": {"do_tre_gia_lap_giay": -0.1}})


def test_dong56_do_tre_la_chuoi():
    """56 — ``do_tre_gia_lap_giay: "0.1"``."""
    with pytest.raises(LoiCauHinh, match="do_tre_gia_lap_giay"):
        ChapHanhGiaLap({**cfg1(), "mock": {"do_tre_gia_lap_giay": "0.1"}})


def test_dong57_do_tre_la_bool():
    """57 — ``do_tre_gia_lap_giay: True``."""
    with pytest.raises(LoiCauHinh, match="do_tre_gia_lap_giay"):
        ChapHanhGiaLap({**cfg1(), "mock": {"do_tre_gia_lap_giay": True}})


def test_dong58_do_tre_la_none():
    """58 — ``do_tre_gia_lap_giay: None``."""
    with pytest.raises(LoiCauHinh, match="do_tre_gia_lap_giay"):
        ChapHanhGiaLap({**cfg1(), "mock": {"do_tre_gia_lap_giay": None}})


def test_dong59_do_tre_inf():
    """59 — ``do_tre_gia_lap_giay: inf``."""
    with pytest.raises(LoiCauHinh, match="hữu hạn"):
        ChapHanhGiaLap({**cfg1(), "mock": {"do_tre_gia_lap_giay": float("inf")}})


def test_dong60_do_tre_am_inf():
    """60 — ``do_tre_gia_lap_giay: -inf``."""
    with pytest.raises(LoiCauHinh, match="hữu hạn"):
        ChapHanhGiaLap({**cfg1(), "mock": {"do_tre_gia_lap_giay": float("-inf")}})


def test_dong61_do_tre_nan():
    """61 — ``do_tre_gia_lap_giay: nan``."""
    with pytest.raises(LoiCauHinh, match="hữu hạn"):
        ChapHanhGiaLap({**cfg1(), "mock": {"do_tre_gia_lap_giay": float("nan")}})


# --------------------------------------------------------------------------- #
# Nhóm F — vòng đời và fail-safe R24 (§5.4, §5.5)                              #
# --------------------------------------------------------------------------- #


def test_dong62_chua_mo_sau_khi_dung():
    """62 — ngay sau khi dựng, chưa ``mo()``."""
    assert tao_bo_chap_hanh(cfg2()).dang_mo is False


def test_dong63_dang_mo_sau_mo():
    """63 — sau ``mo()`` → ``dang_mo is True``."""
    assert mo_act().dang_mo is True


def test_dong64_moi_thiet_bi_tat_sau_mo():
    """64 — sau ``mo()``, mọi thiết bị TẮT."""
    assert mo_act().trang_thai_tat_ca() == {"den": False, "tivi": False}


def test_dong65_lich_su_rong_sau_mo():
    """65 — sau ``mo()``, lịch sử rỗng (lời ép tắt không vào lịch sử)."""
    assert mo_act().lich_su == []


def test_dong66_mo_ghi_muc_tat_xuong_phan_cung():
    """66 — ``mo()`` ghi mức TẮT xuống phần cứng đúng một lần mỗi thiết bị."""
    act = ChapHanhDem(cfg2())
    act.mo()
    assert act.ghi_nhan == [("den", False), ("tivi", False)]


def test_dong67_mo_lan_hai_khong_ghi_phan_cung_lan_hai():
    """67 — ``mo()`` gọi hai lần liên tiếp không ghi phần cứng lần hai."""
    act = ChapHanhDem(cfg2())
    act.mo()
    n = len(act.ghi_nhan)
    act.mo()
    assert len(act.ghi_nhan) == n


def test_dong68_bat_khi_chua_mo():
    """68 — ``bat`` khi chưa ``mo()``."""
    with pytest.raises(LoiPhanCung, match="chưa mở"):
        ChapHanhGiaLap(cfg2()).bat("den")


def test_dong69_tat_khi_chua_mo():
    """69 — ``tat`` khi chưa ``mo()``."""
    with pytest.raises(LoiPhanCung, match="chưa mở"):
        ChapHanhGiaLap(cfg2()).tat("den")


def test_dong70_thuc_thi_khi_chua_mo():
    """70 — ``thuc_thi`` khi chưa ``mo()``."""
    with pytest.raises(LoiPhanCung, match="chưa mở"):
        ChapHanhGiaLap(cfg2()).thuc_thi(Command("den", "bat", None, 1.0))


def test_dong71_trang_thai_khi_chua_mo():
    """71 — ``trang_thai("den")`` khi chưa ``mo()``."""
    with pytest.raises(LoiPhanCung, match="chưa mở"):
        ChapHanhGiaLap(cfg2()).trang_thai("den")


def test_dong72_trang_thai_tat_ca_sau_khi_dong():
    """72 — ``trang_thai_tat_ca()`` sau khi ``dong()``."""
    act = mo_act()
    act.dong()
    with pytest.raises(LoiPhanCung, match="chưa mở"):
        act.trang_thai_tat_ca()


def test_dong73_bat_sau_khi_dong():
    """73 — ``bat`` sau khi ``dong()``."""
    act = mo_act()
    act.dong()
    with pytest.raises(LoiPhanCung, match="chưa mở"):
        act.bat("den")


def test_dong74_thu_tu_kiem_dang_mo_truoc_ten():
    """74 — thứ tự kiểm: ``bat("khong_co")`` khi chưa mở → ``LoiPhanCung``."""
    with pytest.raises(LoiPhanCung):
        ChapHanhGiaLap(cfg2()).bat("khong_co")


def test_dong75_duong_cap_bat_ten_la_khi_da_mo():
    """75 — đường cặp: ``bat("khong_co")`` khi đã mở → ``LoiCauHinh``."""
    with pytest.raises(LoiCauHinh, match="chưa khai báo"):
        mo_act().bat("khong_co")


def test_dong76_dong_goi_hai_lan_khong_nem():
    """76 — ``dong()`` gọi hai lần không ném."""
    act = mo_act()
    act.dong()
    act.dong()
    assert act.dang_mo is False


def test_dong77_dong_lan_hai_khong_them_ban_ghi():
    """77 — ``dong()`` lần hai không thêm bản ghi."""
    act = mo_act()
    act.bat("den")
    act.dong()
    n = len(act.lich_su)
    act.dong()
    assert len(act.lich_su) == n


def test_dong78_mo_sau_dong_xoa_lich_su():
    """78 — ``mo()`` sau ``dong()`` xoá lịch sử."""
    act = mo_act()
    act.bat("den")
    act.dong()
    act.mo()
    assert act.lich_su == []


def test_dong79_mo_sau_dong_dat_lai_trang_thai_tat():
    """79 — ``mo()`` sau ``dong()`` đặt lại trạng thái TẮT."""
    act = mo_act()
    act.bat("den")
    act.dong()
    act.mo()
    assert act.trang_thai("den") is False


def test_dong80_context_manager_mo_dung():
    """80 — context manager mở đúng."""
    act = ChapHanhGiaLap(cfg2())
    with act:
        assert act.dang_mo is True


def test_dong81_context_manager_dong_dung():
    """81 — context manager đóng đúng."""
    act = ChapHanhGiaLap(cfg2())
    with act:
        pass
    assert act.dang_mo is False


def test_dong82_r24_ngoai_le_trong_with_van_tat_het():
    """82 — R24: ngoại lệ trong khối ``with`` vẫn tắt hết và để lại vết."""
    act = ChapHanhGiaLap(cfg2())
    with pytest.raises(ValueError), act:
        act.bat("den")
        raise ValueError("x")
    assert act.lich_su_rut_gon == [("den", "bat"), ("den", "tat")]


def test_dong83_nguon_cua_ban_ghi_tu_tat():
    """83 — nguồn của bản ghi tự-tắt là ``NGUON_HE_THONG``."""
    act = ChapHanhGiaLap(cfg2())
    with pytest.raises(ValueError), act:
        act.bat("den")
        raise ValueError("x")
    assert act.lich_su[-1].nguon == NGUON_HE_THONG


def test_dong84_dong_khong_tat_lai_thiet_bi_dang_tat():
    """84 — ``dong()`` không tắt lại thiết bị vốn đang tắt."""
    act = mo_act()
    act.dong()
    assert act.lich_su == []


def test_dong85_dong_khong_nem_du_phan_cung_hong():
    """85 — ``dong()`` không ném dù lời ghi phần cứng hỏng, vẫn ghi lịch sử."""
    act = ChapHanhNem(cfg1(), bat_dau_nem=False)
    act.mo()
    act.bat("den")
    act.bat_dau_nem = True
    act.dong()
    assert act.lich_su_rut_gon == [("den", "bat"), ("den", "tat")]


def test_dong86_dong_ghi_lai_loi_muc_error(caplog):
    """86 — và ghi lại lỗi ở mức ERROR."""
    act = ChapHanhNem(cfg1(), bat_dau_nem=False)
    act.mo()
    act.bat("den")
    act.bat_dau_nem = True
    with caplog.at_level(logging.ERROR):
        act.dong()
    assert any(r.levelno == logging.ERROR for r in caplog.records)


def test_dong87_dong_van_dong_duoc_du_phan_cung_hong():
    """87 — và vẫn đóng được."""
    act = ChapHanhNem(cfg1(), bat_dau_nem=False)
    act.mo()
    act.bat("den")
    act.bat_dau_nem = True
    act.dong()
    assert act.dang_mo is False


def test_dong88_loi_phan_cung_trong_mo_lan_ra_ngoai():
    """88 — lời ghi phần cứng hỏng trong ``mo()`` → ngoại lệ lan ra."""
    act = ChapHanhNem(cfg1(), bat_dau_nem=True)
    with pytest.raises(RuntimeError):
        act.mo()


def test_dong89_mo_that_bai_thi_o_lai_chua_mo():
    """89 — và đối tượng ở lại trạng thái chưa mở."""
    act = ChapHanhNem(cfg1(), bat_dau_nem=True)
    with pytest.raises(RuntimeError):
        act.mo()
    assert act.dang_mo is False


def test_dong90_loi_phan_cung_trong_bat_lan_ra_khong_nuot():
    """90 — lời ghi phần cứng hỏng trong ``bat()`` → ngoại lệ lan ra, không nuốt."""
    act = ChapHanhNem(cfg1(), bat_dau_nem=False)
    act.mo()
    act.bat_dau_nem = True
    with pytest.raises(RuntimeError):
        act.bat("den")


def test_dong91_bat_that_bai_khong_ghi_lich_su():
    """91 — và không ghi lịch sử cho lệnh chưa thực hiện."""
    act = ChapHanhNem(cfg1(), bat_dau_nem=False)
    act.mo()
    act.bat_dau_nem = True
    with contextlib.suppress(RuntimeError):
        act.bat("den")
    assert act.lich_su == []


def test_dong92_bat_that_bai_trang_thai_khong_doi():
    """92 — và trạng thái không đổi."""
    act = ChapHanhNem(cfg1(), bat_dau_nem=False)
    act.mo()
    act.bat_dau_nem = True
    with contextlib.suppress(RuntimeError):
        act.bat("den")
    assert act.trang_thai("den") is False


# --------------------------------------------------------------------------- #
# Nhóm G — bật/tắt, luỹ đẳng, lịch sử (§4.4, §4.5, §5.6)                       #
# --------------------------------------------------------------------------- #


def test_dong93_duong_thanh_cong_bat():
    """93 — đường thành công: ``bat("den")``."""
    act = mo_act()
    act.bat("den")
    assert act.trang_thai("den") is True


def test_dong94_duong_thanh_cong_tat():
    """94 — đường thành công: ``tat("den")`` sau khi đã bật."""
    act = mo_act()
    act.bat("den")
    act.tat("den")
    assert act.trang_thai("den") is False


def test_dong95_bat_khong_dung_thiet_bi_khac():
    """95 — ``bat("den")`` không đụng thiết bị khác."""
    act = mo_act()
    act.bat("den")
    assert act.trang_thai("tivi") is False


def test_dong96_bat_ghi_dung_mot_ban_ghi():
    """96 — ``bat("den")`` ghi đúng một bản ghi."""
    act = mo_act()
    act.bat("den")
    assert act.lich_su_rut_gon == [("den", "bat")]


def test_dong97_bat_hai_lan_khong_nem():
    """97 — ``bat`` hai lần không ném (luỹ đẳng)."""
    act = mo_act()
    act.bat("den")
    act.bat("den")
    assert act.trang_thai("den") is True


def test_dong98_bat_hai_lan_ghi_ca_hai_vao_lich_su():
    """98 — ``bat`` hai lần vẫn ghi cả hai vào lịch sử."""
    act = mo_act()
    act.bat("den")
    act.bat("den")
    assert act.lich_su_rut_gon == [("den", "bat"), ("den", "bat")]


def test_dong99_bat_hai_lan_chi_ghi_phan_cung_mot_lan():
    """99 — ``bat`` hai lần chỉ ghi phần cứng một lần."""
    act = ChapHanhDem(cfg2())
    act.mo()
    act.ghi_nhan.clear()
    act.bat("den")
    act.bat("den")
    assert act.ghi_nhan == [("den", True)]


def test_dong100_tat_thiet_bi_dang_tat_van_vao_lich_su():
    """100 — ``tat`` thiết bị vốn đang tắt vẫn vào lịch sử."""
    act = mo_act()
    act.tat("den")
    assert act.lich_su_rut_gon == [("den", "tat")]


def test_dong101_tat_thiet_bi_dang_tat_khong_ghi_phan_cung():
    """101 — ``tat`` thiết bị vốn đang tắt không ghi phần cứng."""
    act = ChapHanhDem(cfg2())
    act.mo()
    act.ghi_nhan.clear()
    act.tat("den")
    assert act.ghi_nhan == []


def test_dong102_bat_ghi_dung_nguon():
    """102 — ``bat("den", nguon="u01")`` ghi đúng nguồn."""
    act = mo_act()
    act.bat("den", nguon="u01")
    assert act.lich_su[-1].nguon == "u01"


def test_dong103_bat_khong_truyen_nguon():
    """103 — ``bat("den")`` không truyền nguồn."""
    act = mo_act()
    act.bat("den")
    assert act.lich_su[-1].nguon is None


def test_dong104_lich_su_tra_ban_sao():
    """104 — ``lich_su`` trả bản sao."""
    act = mo_act()
    act.bat("den")
    ls = act.lich_su
    ls.clear()
    assert len(act.lich_su) == 1


def test_dong105_trang_thai_tat_ca_tra_ban_sao():
    """105 — ``trang_thai_tat_ca()`` trả bản sao."""
    act = mo_act()
    d = act.trang_thai_tat_ca()
    d["den"] = True
    assert act.trang_thai("den") is False


def test_dong106_trang_thai_ten_la_khi_da_mo():
    """106 — ``trang_thai("khong_co")`` khi đã mở."""
    with pytest.raises(LoiCauHinh, match="chưa khai báo"):
        mo_act().trang_thai("khong_co")


# --------------------------------------------------------------------------- #
# Nhóm H — thuc_thi(Command) (§5.7)                                            #
# --------------------------------------------------------------------------- #


def test_dong107_duong_thanh_cong_thuc_thi_bat():
    """107 — đường thành công: ``thuc_thi(Command("den", "bat", "u01", 123.0))``."""
    act = mo_act()
    act.thuc_thi(Command("den", "bat", "u01", 123.0))
    assert act.trang_thai("den") is True


def test_dong108_giu_nguyen_nguon_cua_lenh():
    """108 — giữ nguyên ``nguon`` của lệnh."""
    act = mo_act()
    act.thuc_thi(Command("den", "bat", "u01", 123.0))
    assert act.lich_su[-1].nguon == "u01"


def test_dong109_giu_nguyen_thoi_diem_khong_dong_moc_lai():
    """109 — giữ nguyên ``thoi_diem`` của lệnh, không đóng mốc lại."""
    act = mo_act()
    act.thuc_thi(Command("den", "bat", "u01", 123.0))
    assert act.lich_su[-1].thoi_diem == 123.0


def test_dong110_ghi_chinh_doi_tuong_lenh_vao_lich_su():
    """110 — ghi chính đối tượng lệnh vào lịch sử."""
    act = mo_act()
    act.thuc_thi(Command("den", "bat", "u01", 123.0))
    assert act.lich_su == [Command("den", "bat", "u01", 123.0)]


def test_dong111_duong_thanh_cong_thuc_thi_tat():
    """111 — đường thành công: ``thuc_thi(Command("den", "tat", None, 1.0))`` sau khi đã bật."""
    act = mo_act()
    act.bat("den")
    act.thuc_thi(Command("den", "tat", None, 1.0))
    assert act.trang_thai("den") is False


def test_dong112_hanh_dong_la():
    """112 — ``hanh_dong`` lạ."""
    act = mo_act()
    with pytest.raises(ValueError, match="nhap_nhay"):
        act.thuc_thi(Command("den", "nhap_nhay", None, 1.0))


def test_dong113_hanh_dong_la_khong_vao_lich_su():
    """113 — ``hanh_dong`` lạ không vào lịch sử."""
    act = mo_act()
    with pytest.raises(ValueError, match="nhap_nhay"):
        act.thuc_thi(Command("den", "nhap_nhay", None, 1.0))
    assert act.lich_su == []


def test_dong114_hanh_dong_la_khong_doi_trang_thai():
    """114 — ``hanh_dong`` lạ không đổi trạng thái."""
    act = mo_act()
    with pytest.raises(ValueError, match="nhap_nhay"):
        act.thuc_thi(Command("den", "nhap_nhay", None, 1.0))
    assert act.trang_thai("den") is False


def test_dong115_hanh_dong_viet_hoa_khong_tu_chuan_hoa():
    """115 — ``hanh_dong`` viết hoa: ``Command("den", "BAT", None, 1.0)`` — không tự chuẩn hoá."""
    act = mo_act()
    with pytest.raises(ValueError, match="BAT"):
        act.thuc_thi(Command("den", "BAT", None, 1.0))


def test_dong116_doi_so_khong_phai_command():
    """116 — đối số không phải ``Command``: truyền một ``dict``."""
    act = mo_act()
    with pytest.raises(ValueError, match="Command"):
        act.thuc_thi({"thiet_bi": "den", "hanh_dong": "bat"})


def test_dong117_thuc_thi_thiet_bi_la_khi_da_mo():
    """117 — ``thuc_thi`` với thiết bị lạ khi đã mở."""
    act = mo_act()
    with pytest.raises(LoiCauHinh, match="chưa khai báo"):
        act.thuc_thi(Command("khong_co", "bat", None, 1.0))


# --------------------------------------------------------------------------- #
# Nhóm I — tệp configs/actuator.yaml thật (§3.7)                               #
# --------------------------------------------------------------------------- #


def test_dong118_nap_duoc():
    """118 — nạp được."""
    assert isinstance(_cfg_that(), dict)


def test_dong119_backend_khai_tuong_minh_la_mock():
    """119 — backend khai tường minh là ``mock``."""
    assert _cfg_that()["backend"] == "mock"


def test_dong120_dung_duoc_qua_factory():
    """120 — dựng được qua factory."""
    assert isinstance(tao_bo_chap_hanh(_cfg_that()), ChapHanhGiaLap)


def test_dong121_dung_hai_thiet_bi_dai_dien_mt5():
    """121 — đúng hai thiết bị đại diện của MT5."""
    act = tao_bo_chap_hanh(_cfg_that())
    assert act.danh_sach_thiet_bi == ("den_phong_khach", "tivi_phong_khach")


def test_dong122_nhom_den_la_relay():
    """122 — nhóm đèn là relay."""
    act = tao_bo_chap_hanh(_cfg_that())
    assert act.loai_thiet_bi("den_phong_khach") == "relay"


def test_dong123_nhom_tivi_la_ir():
    """123 — nhóm tivi là IR."""
    act = tao_bo_chap_hanh(_cfg_that())
    assert act.loai_thiet_bi("tivi_phong_khach") == "ir"


def test_dong124_nhanh_decision_co_mat_trong_tep():
    """124 — nhánh ``decision`` của ``P5-02`` có mặt trong tệp."""
    assert "decision" in _cfg_that()


def test_dong125_khoa_la_khong_lam_hong_phep_nap():
    """125 — và không làm hỏng phép nạp của mã việc này."""
    with tao_bo_chap_hanh(_cfg_that()) as a:
        assert a.lich_su == []


def test_dong126_tep_that_di_qua_du_vong_doi_bat_tat():
    """126 — tệp thật đi qua đủ vòng đời bật/tắt."""
    a = tao_bo_chap_hanh(_cfg_that())
    with a:
        a.bat("den_phong_khach")
    assert a.lich_su_rut_gon == [
        ("den_phong_khach", "bat"),
        ("den_phong_khach", "tat"),
    ]
