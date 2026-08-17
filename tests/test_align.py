"""Bộ kiểm thử cho khối căn chỉnh khuôn mặt `src/preprocess/align.py`.

Không ca nào cần mô hình, tệp ảnh thật hay mạng — ảnh và điểm mốc dựng bằng numpy tại chỗ.
Tên các hàm test tham chiếu số dòng trong bảng §5 của `docs/dac-ta/P1-04-align.md`.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from src.common.config import nap_cau_hinh
from src.common.exceptions import LoiCauHinh
from src.preprocess.align import can_chinh, kiem_diem_moc, uoc_luong_bien_doi

DUONG_DAN_CONFIG_THAT = Path(__file__).resolve().parents[1] / "configs" / "preprocess.yaml"


# -----------------------------------------------------------------------------
# Tiện ích dựng dữ liệu tổng hợp — không đọc file, không cần mạng, không cần mô hình
# -----------------------------------------------------------------------------


def _diem_moc_hop_le() -> np.ndarray:
    """5 điểm mốc hợp lệ bất kỳ, dùng cho các ca không đòi hỏi hình học chính xác."""
    return np.array(
        [[38.0, 51.0], [73.0, 51.0], [56.0, 71.0], [41.0, 92.0], [70.0, 92.0]],
        dtype=np.float64,
    )


def _diem_chuan_test() -> np.ndarray:
    """5 điểm chuẩn dùng riêng cho test — KHÔNG lấy từ `configs/preprocess.yaml`."""
    return np.array(
        [[30.0, 35.0], [70.0, 35.0], [50.0, 55.0], [35.0, 75.0], [65.0, 75.0]],
        dtype=np.float64,
    )


def _cfg_toi_thieu(
    output_size: tuple[int, int] = (100, 100),
    diem_chuan: np.ndarray | None = None,
) -> dict:
    """Cấu hình tối thiểu hợp lệ cho `can_chinh`, dùng riêng cho test."""
    if diem_chuan is None:
        diem_chuan = _diem_chuan_test()
    return {
        "output_size": list(output_size),
        "reference_landmarks": np.asarray(diem_chuan).tolist(),
        "interpolation": "bilinear",
        "border_value": [0, 0, 0],
    }


def _mau_tong_hop(x: np.ndarray, y: np.ndarray, kich_thuoc: int) -> np.ndarray:
    """Hàm màu mượt (2 dốc tuyến tính + 1 đốm Gauss) — không tuần hoàn, không có cạnh sắc.

    Dùng để các ca kiểm bất biến hình học (dòng 13, 14, 15) đo đúng sai số hình học,
    không lẫn với nhiễu do nội suy trên hoạ tiết tần số cao.
    """
    tam_x, tam_y, sigma = 170.0, 160.0, 60.0
    kenh_b = 255.0 * x / kich_thuoc
    kenh_g = 255.0 * y / kich_thuoc
    kenh_r = 255.0 * np.exp(-((x - tam_x) ** 2 + (y - tam_y) ** 2) / (2 * sigma**2))
    anh = np.stack([kenh_b, kenh_g, kenh_r], axis=-1)
    return np.clip(anh, 0, 255).astype(np.uint8)


def _anh_tong_hop(kich_thuoc: int = 320) -> np.ndarray:
    """Ảnh tổng hợp mượt kích thước (kich_thuoc, kich_thuoc, 3), kiểu uint8."""
    ys, xs = np.mgrid[0:kich_thuoc, 0:kich_thuoc].astype(np.float64)
    return _mau_tong_hop(xs, ys, kich_thuoc)


def _diem_moc_bat_bien() -> np.ndarray:
    """5 điểm mốc là biến đổi TƯƠNG TỰ chính xác của `_diem_chuan_test()` (dư dôi = 0).

    Bắt buộc dư dôi bằng 0: nếu điểm mốc chỉ "gần đúng" biến đổi tương tự, phép làm khớp
    bình phương tối thiểu bên trong `cv2.estimateAffinePartial2D` (dùng RANSAC) có thể chọn
    tập hợp điểm nội biên khác nhau khi điểm mốc bị co giãn theo tỉ lệ khác nhau — gây sai
    khác giả tạo, không phản ánh đúng tính bất biến hình học cần kiểm ở dòng 13, 14, 15.
    """
    diem_chuan = _diem_chuan_test()
    goc = np.deg2rad(-8.0)
    ty_le = 1.4
    tam = np.array([50.0, 55.0])
    tinh_tien = np.array([120.0, 110.0])
    xoay = np.array([[np.cos(goc), -np.sin(goc)], [np.sin(goc), np.cos(goc)]])
    return (diem_chuan - tam) @ xoay.T * ty_le + tam + tinh_tien


def _do_sai_khac_xam(anh_a: np.ndarray, anh_b: np.ndarray) -> float:
    """Sai khác trung bình mức xám giữa hai ảnh BGR cùng kích thước."""
    xam_a = cv2.cvtColor(anh_a, cv2.COLOR_BGR2GRAY).astype(np.float64)
    xam_b = cv2.cvtColor(anh_b, cv2.COLOR_BGR2GRAY).astype(np.float64)
    return float(np.mean(np.abs(xam_a - xam_b)))


def _anh_cham_sang_tai_moc(diem_moc: np.ndarray, kich_thuoc: int) -> np.ndarray:
    """Ảnh nền đen, có chấm sáng 255 tại đúng 5 vị trí `diem_moc`.

    Dùng cho phép đo dòng 13/13a/14/15: đo trực tiếp trên ảnh ra xem điểm mốc có bị
    `can_chinh` đưa đúng về vị trí điểm chuẩn hay không — khác với so sánh mức xám trung
    bình giữa hai ảnh (cách đo cũ, không phân biệt được căn chỉnh thật với cắt ảnh theo
    khung bao, xem ghi chú cuối bảng §5 của đặc tả).
    """
    anh = np.zeros((kich_thuoc, kich_thuoc, 3), dtype=np.uint8)
    for x, y in diem_moc:
        cv2.circle(anh, (round(x), round(y)), 4, (255, 255, 255), -1)
    return anh


def _gia_tri_tai_diem_chuan(anh_can_chinh: np.ndarray, diem_chuan: np.ndarray) -> list[int]:
    """Mức xám của `anh_can_chinh` lấy mẫu tại 5 toạ độ `diem_chuan` (làm tròn)."""
    xam = cv2.cvtColor(anh_can_chinh, cv2.COLOR_BGR2GRAY)
    return [int(xam[round(y), round(x)]) for x, y in diem_chuan]


def _kiem_diem_moc_ve_dung_vi_tri_chuan(anh: np.ndarray, diem_moc: np.ndarray, cfg: dict) -> None:
    """Căn chỉnh `anh`/`diem_moc` theo `cfg`, đòi cả 5 điểm chuẩn trong ảnh ra `>= 250`."""
    diem_chuan = np.asarray(cfg["reference_landmarks"], dtype=np.float64)
    kq = can_chinh(anh, diem_moc, cfg)
    gia_tri = _gia_tri_tai_diem_chuan(kq, diem_chuan)
    assert all(v >= 250 for v in gia_tri), gia_tri


# -----------------------------------------------------------------------------
# kiem_diem_moc — dòng 1-5
# -----------------------------------------------------------------------------


def test_dong01_kiem_diem_moc_hop_le_khong_nem() -> None:
    """Dòng 1: mảng (5, 2) số thực hữu hạn — đường thành công, không ném ngoại lệ."""
    kiem_diem_moc(_diem_moc_hop_le())


def test_dong02_kiem_diem_moc_sai_so_diem() -> None:
    """Dòng 2: hình dạng (4, 2) phải bị từ chối, thông báo chứa '(5, 2)'."""
    diem = np.zeros((4, 2), dtype=np.float64)
    with pytest.raises(ValueError, match=r"\(5, 2\)"):
        kiem_diem_moc(diem)


def test_dong03_kiem_diem_moc_sai_so_chieu() -> None:
    """Dòng 3: hình dạng (5, 3) phải bị từ chối, thông báo chứa '(5, 2)'."""
    diem = np.zeros((5, 3), dtype=np.float64)
    with pytest.raises(ValueError, match=r"\(5, 2\)"):
        kiem_diem_moc(diem)


def test_dong04_kiem_diem_moc_nan() -> None:
    """Dòng 4: chứa NaN phải bị từ chối, thông báo nói về giá trị không hữu hạn."""
    diem = _diem_moc_hop_le()
    diem[0, 0] = np.nan
    with pytest.raises(ValueError, match="hữu hạn"):
        kiem_diem_moc(diem)


def test_dong05_kiem_diem_moc_inf() -> None:
    """Dòng 5: chứa vô cực phải bị từ chối, cùng loại thông báo như dòng 4."""
    diem = _diem_moc_hop_le()
    diem[2, 1] = np.inf
    with pytest.raises(ValueError, match="hữu hạn"):
        kiem_diem_moc(diem)


# -----------------------------------------------------------------------------
# uoc_luong_bien_doi — dòng 6-9
# -----------------------------------------------------------------------------


def test_dong06_uoc_luong_bien_doi_trung_diem_chuan_ra_ma_tran_don_vi() -> None:
    """Dòng 6: diem_moc trùng đúng diem_chuan → ma trận gần đơn vị."""
    diem = _diem_chuan_test()
    ma_tran = uoc_luong_bien_doi(diem, diem)
    assert np.allclose(ma_tran, [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], atol=1e-6)


def test_dong07_uoc_luong_bien_doi_diem_suy_bien_rai_loi_cau_hinh() -> None:
    """Dòng 7: 5 điểm trùng nhau hoàn toàn (suy biến) → LoiCauHinh nói về điểm suy biến.

    Thông báo phải phân biệt được với LoiCauHinh do thiếu key cấu hình (xem dòng 20, 21):
    không được chứa chữ 'key' hay tên tham số cấu hình nào.
    """
    diem_suy_bien = np.full((5, 2), 10.0, dtype=np.float64)
    with pytest.raises(LoiCauHinh, match="suy biến") as loi:
        uoc_luong_bien_doi(diem_suy_bien, _diem_chuan_test())
    assert "key" not in str(loi.value)


def test_dong08_uoc_luong_bien_doi_hinh_dang_ma_tran() -> None:
    """Dòng 8: ma trận trả về có hình dạng (2, 3), dùng được cho `cv2.warpAffine`."""
    ma_tran = uoc_luong_bien_doi(_diem_moc_hop_le(), _diem_chuan_test())
    assert ma_tran.shape == (2, 3)


def test_dong09_uoc_luong_bien_doi_la_tuong_tu_khong_phai_affine_day_du() -> None:
    """Dòng 9: điểm mốc bị kéo giãn theo một trục vẫn phải cho biến đổi TƯƠNG TỰ.

    Hai vectơ hàng của ma trận phải cùng độ dài (phóng đại đều theo mọi hướng). Nếu lỡ
    dùng `cv2.estimateAffine2D` (affine đầy đủ, có cắt xiên) thay vì
    `cv2.estimateAffinePartial2D`, thuộc tính này bị phá vỡ vì affine đầy đủ khớp chính
    xác cả phần kéo giãn khác nhau theo hai trục.
    """
    diem_chuan = np.array(
        [[0.0, 0.0], [10.0, 0.0], [5.0, 5.0], [2.0, 10.0], [8.0, 10.0]], dtype=np.float64
    )
    diem_moc = diem_chuan * np.array([3.0, 1.0])  # kéo giãn riêng theo trục x
    ma_tran = uoc_luong_bien_doi(diem_moc, diem_chuan)
    do_dai_hang_0 = float(np.hypot(ma_tran[0, 0], ma_tran[0, 1]))
    do_dai_hang_1 = float(np.hypot(ma_tran[1, 0], ma_tran[1, 1]))
    assert abs(do_dai_hang_0 - do_dai_hang_1) < 1e-6


# -----------------------------------------------------------------------------
# can_chinh — dòng 10-25
# -----------------------------------------------------------------------------


def test_dong10_can_chinh_dung_kich_thuoc_config() -> None:
    """Dòng 10: kết quả đúng kích thước cfg['output_size'] = [112, 112]."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(output_size=(112, 112), diem_chuan=_diem_chuan_test() + [60, 60])
    kq = can_chinh(anh, diem_moc, cfg)
    assert kq.shape == (112, 112, 3)


def test_dong11_can_chinh_doc_kich_thuoc_tu_config_khong_viet_cung() -> None:
    """Dòng 11: đổi output_size sang [64, 64] phải đổi hình dạng kết quả tương ứng."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(output_size=(64, 64), diem_chuan=_diem_chuan_test() + [60, 60])
    kq = can_chinh(anh, diem_moc, cfg)
    assert kq.shape == (64, 64, 3)


def test_dong12_can_chinh_kieu_du_lieu_uint8() -> None:
    """Dòng 12: kết quả luôn có kiểu uint8."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    kq = can_chinh(anh, diem_moc, cfg)
    assert kq.dtype == np.uint8


def test_dong13_can_chinh_diem_moc_roi_dung_vi_tri_chuan_trong_anh_ra() -> None:
    """Dòng 13: chấm sáng đặt tại điểm mốc phải rơi đúng vị trí điểm chuẩn trong ảnh ra.

    Đo trực tiếp trên ảnh ra (không phải mức xám trung bình) — phân biệt được `can_chinh`
    thật với một hàm chỉ cắt ảnh theo khung bao 5 điểm mốc rồi resize (xem ghi chú cuối
    bảng §5 của đặc tả: bản đúng cho `[255]*5`, bản cắt khung bao cho `[0, 0, 0, 0, 5]`).
    """
    kich_thuoc = 320
    diem_moc = _diem_moc_bat_bien()
    cfg = _cfg_toi_thieu()

    anh = _anh_cham_sang_tai_moc(diem_moc, kich_thuoc)
    _kiem_diem_moc_ve_dung_vi_tri_chuan(anh, diem_moc, cfg)


def test_dong13a_can_chinh_dung_sau_khi_tinh_tien() -> None:
    """Dòng 13a: dịch cả ảnh lẫn điểm mốc (+30, +20) — dòng 13 vẫn phải đúng."""
    kich_thuoc = 320
    diem_moc = _diem_moc_bat_bien() + np.array([30.0, 20.0])
    cfg = _cfg_toi_thieu()

    anh = _anh_cham_sang_tai_moc(diem_moc, kich_thuoc)
    _kiem_diem_moc_ve_dung_vi_tri_chuan(anh, diem_moc, cfg)


def test_dong14_can_chinh_dung_sau_khi_phong_dai() -> None:
    """Dòng 14: phóng ảnh và điểm mốc lên 2 lần quanh tâm — dòng 13 vẫn phải đúng."""
    kich_thuoc = 320
    diem_moc_goc = _diem_moc_bat_bien()
    tam = diem_moc_goc.mean(axis=0)
    diem_moc = (diem_moc_goc - tam) * 2.0 + tam
    cfg = _cfg_toi_thieu()

    anh = _anh_cham_sang_tai_moc(diem_moc, kich_thuoc)
    _kiem_diem_moc_ve_dung_vi_tri_chuan(anh, diem_moc, cfg)


def test_dong15_can_chinh_dung_sau_khi_xoay() -> None:
    """Dòng 15: xoay ảnh và điểm mốc 20 độ quanh tâm — dòng 13 vẫn phải đúng."""
    kich_thuoc = 320
    diem_moc_goc = _diem_moc_bat_bien()
    tam = diem_moc_goc.mean(axis=0)
    goc = np.deg2rad(20.0)
    cos_g, sin_g = np.cos(goc), np.sin(goc)
    dx, dy = diem_moc_goc[:, 0] - tam[0], diem_moc_goc[:, 1] - tam[1]
    diem_moc = np.stack(
        [cos_g * dx - sin_g * dy + tam[0], sin_g * dx + cos_g * dy + tam[1]], axis=-1
    )
    cfg = _cfg_toi_thieu()

    anh = _anh_cham_sang_tai_moc(diem_moc, kich_thuoc)
    _kiem_diem_moc_ve_dung_vi_tri_chuan(anh, diem_moc, cfg)


def test_dong16_can_chinh_diem_moc_dua_dung_ve_diem_chuan() -> None:
    """Dòng 16: áp ma trận M lên diem_moc phải cho kết quả sát diem_chuan (< 1.0 pixel)."""
    diem_chuan = _diem_chuan_test()
    diem_moc = _diem_moc_bat_bien()
    ma_tran = uoc_luong_bien_doi(diem_moc, diem_chuan)

    toa_do_dong_nhat = np.hstack([diem_moc, np.ones((5, 1))])
    diem_bien_doi = toa_do_dong_nhat @ ma_tran.T

    sai_khac = np.abs(diem_bien_doi - diem_chuan)
    assert np.all(sai_khac < 1.0)


def test_dong17_can_chinh_giu_thu_tu_kenh_bgr() -> None:
    """Dòng 17: ảnh vào toàn xanh lam BGR [255, 0, 0] → vùng giữa ảnh ra vẫn kênh 0 lớn nhất."""
    anh = np.zeros((200, 200, 3), dtype=np.uint8)
    anh[:, :, 0] = 255  # kênh B (thứ tự BGR) toàn 255, G và R bằng 0
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])

    kq = can_chinh(anh, diem_moc, cfg)
    cao, rong = kq.shape[:2]
    pixel_giua = kq[cao // 2, rong // 2]

    assert int(pixel_giua[0]) > int(pixel_giua[1])
    assert int(pixel_giua[0]) > int(pixel_giua[2])


def test_dong18_can_chinh_anh_khong_du_ba_kenh() -> None:
    """Dòng 18: ảnh (H, W) không phải 3 kênh → ValueError."""
    anh_xam = np.zeros((100, 100), dtype=np.uint8)
    with pytest.raises(ValueError):
        can_chinh(anh_xam, _diem_moc_hop_le(), _cfg_toi_thieu())


def test_dong19_can_chinh_anh_khong_phai_uint8() -> None:
    """Dòng 19: ảnh kiểu float32 → ValueError."""
    anh_float = np.zeros((100, 100, 3), dtype=np.float32)
    with pytest.raises(ValueError):
        can_chinh(anh_float, _diem_moc_hop_le(), _cfg_toi_thieu())


def test_dong20_can_chinh_thieu_reference_landmarks() -> None:
    """Dòng 20: cfg thiếu 'reference_landmarks' → LoiCauHinh nêu tên key."""
    cfg = _cfg_toi_thieu()
    del cfg["reference_landmarks"]
    anh = _anh_tong_hop(200)
    with pytest.raises(LoiCauHinh, match="reference_landmarks"):
        can_chinh(anh, _diem_moc_hop_le() + np.array([60.0, 60.0]), cfg)


def test_dong21_can_chinh_thieu_output_size() -> None:
    """Dòng 21: cfg thiếu 'output_size' → LoiCauHinh nêu tên key."""
    cfg = _cfg_toi_thieu()
    del cfg["output_size"]
    anh = _anh_tong_hop(200)
    with pytest.raises(LoiCauHinh, match="output_size"):
        can_chinh(anh, _diem_moc_hop_le() + np.array([60.0, 60.0]), cfg)


def test_dong22_can_chinh_du_key_chay_thanh_cong() -> None:
    """Dòng 22: cfg đủ key bắt buộc — đường thành công, không ném, đúng kích thước."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    kq = can_chinh(anh, diem_moc, cfg)
    assert kq.shape == (100, 100, 3)


def test_dong23_can_chinh_diem_chuan_lay_tu_config_khong_viet_cung() -> None:
    """Dòng 23: đổi 'reference_landmarks' sang bộ khác hẳn phải làm ảnh ra khác đi."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg_goc = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])

    diem_chuan_khac = np.array(
        [[10.0, 90.0], [90.0, 90.0], [50.0, 50.0], [20.0, 15.0], [80.0, 15.0]]
    )
    cfg_khac = _cfg_toi_thieu(diem_chuan=diem_chuan_khac)

    kq_goc = can_chinh(anh, diem_moc, cfg_goc)
    kq_khac = can_chinh(anh, diem_moc, cfg_khac)

    assert _do_sai_khac_xam(kq_goc, kq_khac) > 10.0


def test_dong24_can_chinh_vien_ngoai_dien_bang_border_value() -> None:
    """Dòng 24: vùng nằm ngoài ảnh gốc sau biến đổi được điền đúng border_value."""
    anh = np.full((60, 60, 3), 200, dtype=np.uint8)
    diem_chuan = _diem_chuan_test()  # trải rộng tới (70, 75), vượt khỏi ảnh nguồn 60x60
    diem_moc = diem_chuan.copy()  # trùng diem_chuan => M gần đơn vị (xem dòng 6)
    cfg = _cfg_toi_thieu(output_size=(100, 100), diem_chuan=diem_chuan)
    cfg["border_value"] = [9, 9, 9]

    kq = can_chinh(anh, diem_moc, cfg)

    assert [int(v) for v in kq[99, 99]] == [9, 9, 9]


def test_dong25_can_chinh_nap_config_that_cua_du_an() -> None:
    """Dòng 25: nạp đúng `configs/preprocess.yaml` thật và chạy `can_chinh` thành công."""
    cfg = nap_cau_hinh(str(DUONG_DAN_CONFIG_THAT))
    diem_chuan = np.array(cfg["reference_landmarks"], dtype=np.float64)
    diem_moc = diem_chuan + np.array([40.0, 40.0])
    anh = _anh_tong_hop(250)

    kq = can_chinh(anh, diem_moc, cfg)

    assert kq.shape == (112, 112, 3)


# -----------------------------------------------------------------------------
# can_chinh — cấu hình hỏng, dòng 26-31 (vòng review 2)
# -----------------------------------------------------------------------------


def test_dong26_can_chinh_output_size_bang_khong_rai_loi_cau_hinh() -> None:
    """Dòng 26: output_size = [0, 0] phải ném LoiCauHinh, KHÔNG được trả về ảnh gốc."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    cfg["output_size"] = [0, 0]
    with pytest.raises(LoiCauHinh, match="output_size"):
        can_chinh(anh, diem_moc, cfg)


def test_dong27_can_chinh_output_size_am_rai_loi_cau_hinh() -> None:
    """Dòng 27: output_size chứa số âm phải ném LoiCauHinh."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    cfg["output_size"] = [-5, 100]
    with pytest.raises(LoiCauHinh):
        can_chinh(anh, diem_moc, cfg)


def test_dong28_can_chinh_reference_landmarks_sai_so_diem_rai_loi_cau_hinh() -> None:
    """Dòng 28: reference_landmarks chỉ có 4 điểm (thay vì 5) phải ném LoiCauHinh nêu tên key."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    cfg["reference_landmarks"] = cfg["reference_landmarks"][:4]
    with pytest.raises(LoiCauHinh, match="reference_landmarks"):
        can_chinh(anh, diem_moc, cfg)


def test_dong29_can_chinh_reference_landmarks_khong_phai_so_rai_loi_cau_hinh() -> None:
    """Dòng 29: reference_landmarks chứa giá trị không phải số → LoiCauHinh, KHÔNG phải
    ValueError hay TypeError (nếu là ValueError/TypeError thô, `pytest.raises(LoiCauHinh)`
    dưới đây sẽ để ngoại lệ đó thoát ra và làm ca test này đỏ)."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    cfg["reference_landmarks"] = [["a", "b"], [1, 2], [3, 4], [5, 6], [7, 8]]
    with pytest.raises(LoiCauHinh):
        can_chinh(anh, diem_moc, cfg)


def test_dong30_moi_loi_cau_hinh_deu_la_loi_cau_hinh() -> None:
    """Dòng 30 (kiểm gộp §7): mọi cấu hình hỏng phải ném LoiCauHinh, không lẫn với
    ValueError/TypeError — tầng gọi (`P1-05`) phải phân biệt được "ảnh này bỏ qua"
    (ValueError) với "cấu hình hỏng, dừng cả mẻ" (LoiCauHinh).

    Phủ đủ BỐN key ở §4 (`output_size`, `reference_landmarks`, `interpolation`,
    `border_value`), mỗi key ít nhất 2 biến thể hỏng.
    """
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    diem_chuan_hop_le = (_diem_chuan_test() + [60, 60]).tolist()

    cau_hinh_hong = [
        # output_size — 4 biến thể
        {**_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le), "output_size": [0, 0]},
        {**_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le), "output_size": [-5, 100]},
        {**_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le), "output_size": [100]},
        {**_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le), "output_size": "khong_hop_le"},
        # reference_landmarks — 3 biến thể
        {
            **_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le),
            "reference_landmarks": diem_chuan_hop_le[:4],
        },
        {
            **_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le),
            "reference_landmarks": [[p[0], p[1], 0.0] for p in diem_chuan_hop_le],
        },
        {**_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le), "reference_landmarks": "khong_hop_le"},
        # interpolation — 2 biến thể
        {**_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le), "interpolation": "xyz"},
        {**_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le), "interpolation": 42},
        # border_value — 2 biến thể
        {**_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le), "border_value": 0},
        {**_cfg_toi_thieu(diem_chuan=diem_chuan_hop_le), "border_value": [0, 0]},
    ]

    for cfg in cau_hinh_hong:
        try:
            can_chinh(anh, diem_moc, cfg)
        except LoiCauHinh:
            continue
        except (ValueError, TypeError) as e:
            pytest.fail(f"Cấu hình hỏng {cfg!r} ném {type(e).__name__} thay vì LoiCauHinh: {e}")
        else:
            pytest.fail(f"Cấu hình hỏng {cfg!r} không ném ngoại lệ nào")


def test_dong32_can_chinh_border_value_sai_kieu_rai_loi_cau_hinh() -> None:
    """Dòng 32: border_value là số nguyên (không phải danh sách) → LoiCauHinh nêu tên key."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    cfg["border_value"] = 0
    with pytest.raises(LoiCauHinh, match="border_value"):
        can_chinh(anh, diem_moc, cfg)


def test_dong33_can_chinh_border_value_sai_so_phan_tu_rai_loi_cau_hinh() -> None:
    """Dòng 33: border_value chỉ có 2 phần tử (thay vì 3) → LoiCauHinh, KHÔNG được im lặng
    bỏ qua (nếu im lặng, `cv2.warpAffine` sẽ nhận Scalar 2 phần tử mà không báo gì)."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    cfg["border_value"] = [0, 0]
    with pytest.raises(LoiCauHinh, match="border_value"):
        can_chinh(anh, diem_moc, cfg)


def test_dong34_can_chinh_border_value_khong_phai_so_rai_loi_cau_hinh() -> None:
    """Dòng 34: border_value chứa giá trị không phải số → LoiCauHinh, KHÔNG phải ValueError."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    cfg["border_value"] = ["den", "den", "den"]
    with pytest.raises(LoiCauHinh):
        can_chinh(anh, diem_moc, cfg)


def test_dong35_can_chinh_interpolation_khong_hop_le_rai_loi_cau_hinh() -> None:
    """Dòng 35: interpolation = 'xyz' → LoiCauHinh nêu tên key và các giá trị hợp lệ."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    cfg["interpolation"] = "xyz"
    with pytest.raises(LoiCauHinh, match="interpolation"):
        can_chinh(anh, diem_moc, cfg)


def test_dong36_can_chinh_border_value_hop_le_thanh_cong() -> None:
    """Dòng 36: border_value hợp lệ [0, 0, 0] — đường thành công, không ném, đúng kích thước."""
    anh = _anh_tong_hop(200)
    diem_moc = _diem_moc_hop_le() + np.array([60.0, 60.0])
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    cfg["border_value"] = [0, 0, 0]
    kq = can_chinh(anh, diem_moc, cfg)
    assert kq.shape == (100, 100, 3)


def test_dong31_moi_loi_du_lieu_vao_deu_la_value_error() -> None:
    """Dòng 31 (kiểm gộp §7, chiều ngược lại): mọi lỗi dữ liệu đầu vào phải ném ValueError,
    không lẫn với LoiCauHinh.
    """
    cfg = _cfg_toi_thieu(diem_chuan=_diem_chuan_test() + [60, 60])
    anh_hop_le = _anh_tong_hop(200)
    diem_moc_hop_le = _diem_moc_hop_le() + np.array([60.0, 60.0])

    diem_moc_nan = diem_moc_hop_le.copy()
    diem_moc_nan[0, 0] = np.nan
    diem_moc_inf = diem_moc_hop_le.copy()
    diem_moc_inf[1, 1] = np.inf

    ca_hong: list[tuple[np.ndarray, np.ndarray]] = [
        (np.zeros((100, 100), dtype=np.uint8), diem_moc_hop_le),  # ảnh thiếu kênh màu
        (np.zeros((100, 100, 3), dtype=np.float32), diem_moc_hop_le),  # ảnh sai kiểu
        (anh_hop_le, np.zeros((4, 2), dtype=np.float64)),  # điểm mốc thiếu điểm
        (anh_hop_le, np.zeros((5, 3), dtype=np.float64)),  # điểm mốc sai số chiều
        (anh_hop_le, diem_moc_nan),  # điểm mốc chứa NaN
        (anh_hop_le, diem_moc_inf),  # điểm mốc chứa vô cực
    ]

    for anh, diem_moc in ca_hong:
        try:
            can_chinh(anh, diem_moc, cfg)
        except ValueError:
            continue
        except LoiCauHinh as e:
            pytest.fail(f"Dữ liệu vào hỏng ném LoiCauHinh thay vì ValueError: {e}")
        else:
            pytest.fail("Dữ liệu vào hỏng không ném ngoại lệ nào")
