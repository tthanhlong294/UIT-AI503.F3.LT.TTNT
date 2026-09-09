"""Bộ kiểm thử cho scripts/preprocess.py.

Không ca nào cần mô hình ONNX thật: `YoloFaceDetector` được thay bằng lớp giả qua
`monkeypatch.setattr(pp, "YoloFaceDetector", ...)` (trừ hai ca cố tình dùng lớp thật để kiểm
đường lỗi "mô hình/đường dẫn không tồn tại" — dòng 35, 36 — không cần tệp .onnx thật vì lỗi xảy
ra trước khi mô hình được nạp). Không ca nào đọc `data/`, `models/` hay `docs/` — an toàn chạy
trong container ARM64 (§11 đặc tả P1-05).

Tên các hàm test tham chiếu số dòng trong bảng §9 của `docs/dac-ta/P1-05-preprocess.md`.
"""

import csv
import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from scripts import preprocess as pp
from src.common.config import nap_cau_hinh
from src.common.exceptions import LoiCauHinh
from src.common.types import FaceBox

# Bộ điểm mốc dựng sẵn đã kiểm bằng số 19/08/2026 — xem §9.2b đặc tả. Dùng nguyên, không sửa.

# Mặt chuẩn — reference_landmarks của configs/preprocess.yaml. Tỉ lệ lệch mũi = 0,5715.
MAT_CHUAN = np.array(
    [
        [38.2946, 51.6963],
        [73.5318, 51.5014],
        [56.0252, 71.7366],
        [41.5493, 92.3655],
        [70.7299, 92.2041],
    ]
)

# Tỉ lệ lệch mũi ĐÚNG 0,2000 — thoả cả bốn bất biến thứ tự. Dùng cho dòng 13c.
TI_LE_020 = np.array([[0.0, 0.0], [100.0, 0.0], [50.0, 20.0], [10.0, 60.0], [90.0, 60.0]])

# Thẳng hàng theo đường chéo. Tỉ lệ lệch mũi = 0,0000.
# Thoả CẢ BỐN bất biến thứ tự — chỉ điều kiện thứ năm bắt được. Dùng cho dòng 13.
THANG_HANG = np.array([[float(i), float(i)] for i in range(5)])

_DUONG_DAN_CONFIG_THAT = Path(__file__).resolve().parents[1] / "configs" / "preprocess.yaml"


# =============================================================================
# Trợ giúp dùng chung — không đọc data/, models/, docs/
# =============================================================================


def _cfg_preprocess(
    output_size: tuple[int, int] = (112, 112),
    min_bbox_px: int = 40,
    min_confidence: float = 0.7,
    kiem_hinh_hoc: bool = True,
    min_ti_le_lech_mui: float = 0.15,
) -> dict:
    """Cấu hình preprocess hợp lệ tối giản dùng làm nền cho các ca kiểm thử."""
    return {
        "output_size": list(output_size),
        "reference_landmarks": MAT_CHUAN.tolist(),
        "interpolation": "bilinear",
        "border_value": [0, 0, 0],
        "loc_chat_luong": {
            "min_bbox_px": min_bbox_px,
            "min_confidence": min_confidence,
            "kiem_hinh_hoc_diem_moc": kiem_hinh_hoc,
            "min_ti_le_lech_mui": min_ti_le_lech_mui,
        },
    }


def _ghi_cfg_preprocess(
    tmp_path: Path,
    output_size: tuple[int, int] = (112, 112),
    min_bbox_px: int = 40,
    min_confidence: float = 0.7,
    kiem_hinh_hoc: bool = True,
    min_ti_le_lech_mui: float = 0.15,
) -> Path:
    """Ghi một `configs/preprocess.yaml` tối giản, tham số hoá, dùng riêng cho test CLI."""
    dong: list[str] = [
        f"output_size: [{output_size[0]}, {output_size[1]}]",
        "reference_landmarks:",
    ]
    dong += [f"  - [{x}, {y}]" for x, y in MAT_CHUAN.tolist()]
    dong += [
        "interpolation: bilinear",
        "border_value: [0, 0, 0]",
        "loc_chat_luong:",
        f"  min_bbox_px: {min_bbox_px}",
        f"  min_confidence: {min_confidence}",
        f"  kiem_hinh_hoc_diem_moc: {'true' if kiem_hinh_hoc else 'false'}",
        f"  min_ti_le_lech_mui: {min_ti_le_lech_mui}",
    ]
    duong_dan = tmp_path / "preprocess_test.yaml"
    duong_dan.write_text("\n".join(dong) + "\n", encoding="utf-8")
    return duong_dan


def _ghi_cfg_detect(tmp_path: Path) -> Path:
    """Ghi một `configs/detect.yaml` tối giản, hợp lệ, dùng riêng cho test CLI."""
    dong = [
        "inference:",
        "  conf_threshold: 0.5",
        "  iou_threshold: 0.45",
        "  max_faces: 10",
        "  num_threads: 0",
    ]
    duong_dan = tmp_path / "detect_test.yaml"
    duong_dan.write_text("\n".join(dong) + "\n", encoding="utf-8")
    return duong_dan


def _anh_that(duong_dan: Path, kich_thuoc: int = 32, seed: int = 0) -> None:
    """Ghi một ảnh .jpg/.png THẬT (giải mã được bằng cv2.imread) tại `duong_dan`."""
    rng = np.random.default_rng(seed)
    anh = rng.integers(0, 255, size=(kich_thuoc, kich_thuoc, 3), dtype=np.uint8)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(duong_dan), anh)


def _face_hop_le(landmarks: np.ndarray | None = None, conf: float = 0.9) -> FaceBox:
    """FaceBox hợp lệ mặc định: bbox 100x100, conf 0.9, điểm mốc mặt chuẩn."""
    if landmarks is None:
        landmarks = MAT_CHUAN.copy()
    return FaceBox(x1=0, y1=0, x2=100, y2=100, confidence=conf, landmarks=landmarks)


class _DetectorSimples:
    """Detector giả tối giản cho xu_ly_mot_anh — chỉ cần .detect(anh) -> list[FaceBox]."""

    def __init__(self, ket_qua: list[FaceBox]) -> None:
        self._ket_qua = ket_qua

    def detect(self, anh: np.ndarray) -> list[FaceBox]:
        return self._ket_qua


class _DetectorNemLoi:
    """Detector giả ném một ngoại lệ cho trước ngay khi gọi detect()."""

    def __init__(self, loi: Exception) -> None:
        self._loi = loi

    def detect(self, anh: np.ndarray) -> list[FaceBox]:
        raise self._loi


class _DetectorKhongDuocGoi:
    """Detector giả — assert nếu bị gọi (dùng cho ca ảnh không đọc được được rồi)."""

    def detect(self, anh: np.ndarray) -> list[FaceBox]:
        raise AssertionError("detect() không được gọi khi ảnh không đọc được")


def _lop_detector_gia(ham_detect) -> type:
    """Sinh lớp fake thay thế YoloFaceDetector cho main(), giữ đúng chữ ký (đường_dẫn, cfg)."""

    class _DetectorGiaChoMain:
        def __init__(self, duong_dan_onnx, cfg) -> None:
            self.duong_dan_onnx = Path(duong_dan_onnx)
            self.cfg = cfg

        def detect(self, anh: np.ndarray) -> list[FaceBox]:
            return ham_detect(anh)

    return _DetectorGiaChoMain


def _ti_le_lech_mui(diem_moc: np.ndarray) -> float:
    """Tính tỉ lệ lệch mũi độc lập với cài đặt — đúng công thức §9.2b của đặc tả."""
    mat_trai, mat_phai, mui = diem_moc[0], diem_moc[1], diem_moc[2]
    ab = mat_phai - mat_trai
    do_dai = float(np.hypot(ab[0], ab[1]))
    khoang_cach = abs(ab[0] * (mui[1] - mat_trai[1]) - ab[1] * (mui[0] - mat_trai[0])) / do_dai
    return khoang_cach / do_dai


def _ban_ghi_ok(file_vao: str = "a.jpg", file_ra: str = "a.png") -> dict:
    return {
        "file_vao": file_vao,
        "file_ra": file_ra,
        "ly_do": "ok",
        "n_faces": 1,
        "conf": 0.9,
        "bbox_w": 100,
        "bbox_h": 100,
    }


# =============================================================================
# §9.1 — liet_ke_anh (dòng 01-07)
# =============================================================================


def test_dong01_liet_ke_de_quy(tmp_path):
    d = tmp_path / "vao"
    for sub in ["A", "B"]:
        (d / sub).mkdir(parents=True)
        for i in range(3):
            (d / sub / f"anh_{i}.jpg").write_bytes(b"\x00")
    assert len(pp.liet_ke_anh(d)) == 6


def test_dong02_nhan_ca_ba_duoi(tmp_path):
    d = tmp_path / "vao"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"\x00")
    (d / "b.jpeg").write_bytes(b"\x00")
    (d / "c.png").write_bytes(b"\x00")
    assert len(pp.liet_ke_anh(d)) == 3


def test_dong03_khong_phan_biet_hoa_thuong(tmp_path):
    d = tmp_path / "vao"
    d.mkdir()
    (d / "a.JPG").write_bytes(b"\x00")
    (d / "b.PNG").write_bytes(b"\x00")
    assert len(pp.liet_ke_anh(d)) == 2


def test_dong04_bo_qua_tep_khong_phai_anh(tmp_path):
    d = tmp_path / "vao"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"\x00")
    (d / "manifest.csv").write_text("x", encoding="utf-8")
    (d / "note.txt").write_text("x", encoding="utf-8")
    assert len(pp.liet_ke_anh(d)) == 1


def test_dong05_thu_tu_on_dinh(tmp_path):
    d = tmp_path / "vao"
    d.mkdir()
    for i in range(10):
        (d / f"anh_{i:02d}.jpg").write_bytes(b"\x00")
    assert pp.liet_ke_anh(d) == pp.liet_ke_anh(d)


def test_dong06_thu_muc_khong_ton_tai(tmp_path):
    with pytest.raises(LoiCauHinh):
        pp.liet_ke_anh(tmp_path / "khong_ton_tai")


def test_dong07_thu_muc_rong(tmp_path):
    d = tmp_path / "rong"
    d.mkdir()
    with pytest.raises(LoiCauHinh, match="không có ảnh") as loi_rong:
        pp.liet_ke_anh(d)
    with pytest.raises(LoiCauHinh) as loi_khong_ton_tai:
        pp.liet_ke_anh(tmp_path / "khong_ton_tai_2")
    # Thông báo phải khác nhau — không được trùng chuỗi với dòng 06.
    assert str(loi_rong.value) != str(loi_khong_ton_tai.value)


# =============================================================================
# §9.2 — kiem_hinh_hoc_diem_moc (dòng 08-14, 13b, 13c, 13d)
# =============================================================================


def test_dong08_diem_moc_that_true():
    cfg = nap_cau_hinh(str(_DUONG_DAN_CONFIG_THAT))
    diem_chuan = np.array(cfg["reference_landmarks"], dtype=np.float64)
    min_ti_le = cfg["loc_chat_luong"]["min_ti_le_lech_mui"]
    assert pp.kiem_hinh_hoc_diem_moc(diem_chuan, min_ti_le) is True


def test_dong09_vi_pham_bat_bien_1():
    """Hoán vị x của hai mắt — mắt trái không còn bên trái mắt phải."""
    diem = MAT_CHUAN.copy()
    diem[[0, 1], 0] = diem[[1, 0], 0]
    assert pp.kiem_hinh_hoc_diem_moc(diem, 0.15) is False


def test_dong10_vi_pham_bat_bien_2():
    """Đẩy y hai mắt xuống dưới mũi — hai mắt không còn nằm trên mũi."""
    diem = MAT_CHUAN.copy()
    diem[0, 1] = diem[2, 1] + 50.0
    diem[1, 1] = diem[2, 1] + 50.0
    assert pp.kiem_hinh_hoc_diem_moc(diem, 0.15) is False


def test_dong11_vi_pham_bat_bien_3():
    """Đẩy y mũi xuống dưới miệng — mũi không còn nằm trên miệng."""
    diem = MAT_CHUAN.copy()
    diem[2, 1] = max(diem[3, 1], diem[4, 1]) + 50.0
    assert pp.kiem_hinh_hoc_diem_moc(diem, 0.15) is False


def test_dong12_vi_pham_bat_bien_4():
    """Hoán vị x hai khoé miệng — khoé trái không còn bên trái khoé phải."""
    diem = MAT_CHUAN.copy()
    diem[[3, 4], 0] = diem[[4, 3], 0]
    assert pp.kiem_hinh_hoc_diem_moc(diem, 0.15) is False


def test_dong13_thang_hang_la_false():
    """Điểm mốc thẳng hàng theo đường chéo — thoả cả bốn bất biến, chỉ điều kiện 5 bắt được."""
    assert pp.kiem_hinh_hoc_diem_moc(THANG_HANG.copy(), 0.15) is False


def test_dong13b_ti_le_lech_mui_mau_chuan():
    assert _ti_le_lech_mui(MAT_CHUAN) == pytest.approx(0.5715, abs=1e-3)


def test_dong13c_nguong_that_su_duoc_dung():
    """Cùng dữ liệu (tỉ số đúng 0,2000), đổi ngưỡng phải đổi kết quả."""
    assert pp.kiem_hinh_hoc_diem_moc(TI_LE_020.copy(), 0.15) is True
    assert pp.kiem_hinh_hoc_diem_moc(TI_LE_020.copy(), 0.25) is False


def test_dong13d_hai_mat_trung_nhau_value_error():
    diem = MAT_CHUAN.copy()
    diem[1] = diem[0]
    with pytest.raises(ValueError):
        pp.kiem_hinh_hoc_diem_moc(diem, 0.15)


def test_dong14_sai_hinh_dang_value_error():
    with pytest.raises(ValueError):
        pp.kiem_hinh_hoc_diem_moc(np.zeros((4, 2)), 0.15)


# =============================================================================
# §9.3 — xu_ly_mot_anh (dòng 15-24)
# =============================================================================


def test_dong15_khong_doc_duoc_anh(tmp_path):
    p = tmp_path / "rac.png"
    p.write_bytes(b"day khong phai anh that, chi la byte rac 123456789")
    anh_ra, ly_do, thong_tin = pp.xu_ly_mot_anh(p, _DetectorKhongDuocGoi(), _cfg_preprocess())
    assert anh_ra is None
    assert ly_do == "khong_doc_duoc_anh"
    assert thong_tin == {}


def test_dong15b_detect_nem_valueerror_tra_ve_ly_do(tmp_path):
    p = tmp_path / "anh.jpg"
    _anh_that(p)
    detector = _DetectorNemLoi(ValueError("khung hình hỏng (giả lập)"))
    anh_ra, ly_do, _thong_tin = pp.xu_ly_mot_anh(p, detector, _cfg_preprocess())
    assert anh_ra is None
    assert ly_do == "khong_doc_duoc_anh"


def test_dong16_khong_thay_mat(tmp_path):
    p = tmp_path / "anh.jpg"
    _anh_that(p)
    anh_ra, ly_do, thong_tin = pp.xu_ly_mot_anh(p, _DetectorSimples([]), _cfg_preprocess())
    assert anh_ra is None
    assert ly_do == "khong_thay_mat"
    assert thong_tin == {}


def test_dong17_mat_qua_nho(tmp_path):
    p = tmp_path / "anh.jpg"
    _anh_that(p)
    fb = FaceBox(x1=0, y1=0, x2=20, y2=20, confidence=0.9, landmarks=MAT_CHUAN.copy())
    anh_ra, ly_do, thong_tin = pp.xu_ly_mot_anh(p, _DetectorSimples([fb]), _cfg_preprocess())
    assert anh_ra is None
    assert ly_do == "mat_qua_nho"
    assert thong_tin["bbox_w"] == 20


def test_dong18_do_tin_cay_thap(tmp_path):
    p = tmp_path / "anh.jpg"
    _anh_that(p)
    fb = _face_hop_le(conf=0.5)
    anh_ra, ly_do, thong_tin = pp.xu_ly_mot_anh(p, _DetectorSimples([fb]), _cfg_preprocess())
    assert anh_ra is None
    assert ly_do == "do_tin_cay_thap"
    assert thong_tin["conf"] == pytest.approx(0.5)


def test_dong19_diem_moc_bat_thuong(tmp_path):
    p = tmp_path / "anh.jpg"
    _anh_that(p)
    fb = _face_hop_le(landmarks=THANG_HANG.copy())
    anh_ra, ly_do, _thong_tin = pp.xu_ly_mot_anh(p, _DetectorSimples([fb]), _cfg_preprocess())
    assert anh_ra is None
    assert ly_do == "diem_moc_bat_thuong"


def test_dong20_thanh_cong(tmp_path):
    p = tmp_path / "anh.jpg"
    _anh_that(p, kich_thuoc=200)
    fb = _face_hop_le()
    anh_ra, ly_do, _thong_tin = pp.xu_ly_mot_anh(p, _DetectorSimples([fb]), _cfg_preprocess())
    assert ly_do == "ok"
    assert anh_ra.shape == (112, 112, 3)


def test_dong21_thu_tu_loc_dung(tmp_path):
    """Mặt vừa nhỏ vừa conf thấp — phải báo lý do kiểm TRƯỚC (mat_qua_nho), không phải sau."""
    p = tmp_path / "anh.jpg"
    _anh_that(p)
    fb = FaceBox(x1=0, y1=0, x2=20, y2=20, confidence=0.1, landmarks=MAT_CHUAN.copy())
    anh_ra, ly_do, _thong_tin = pp.xu_ly_mot_anh(p, _DetectorSimples([fb]), _cfg_preprocess())
    assert anh_ra is None
    assert ly_do == "mat_qua_nho"


def test_dong22_nhieu_mat_lay_dien_tich_lon_nhat(tmp_path):
    """Nhiều mặt → chọn mặt diện tích khung bao lớn nhất, n_faces ghi đúng số thật (§7 đặc tả,
    sửa 20/08/2026)."""
    p = tmp_path / "anh.jpg"
    _anh_that(p, kich_thuoc=200)
    fb1 = FaceBox(x1=0, y1=0, x2=50, y2=50, confidence=0.95, landmarks=MAT_CHUAN.copy())  # 2500
    fb2 = FaceBox(x1=0, y1=0, x2=120, y2=160, confidence=0.80, landmarks=MAT_CHUAN.copy())  # 19200
    fb3 = FaceBox(x1=0, y1=0, x2=70, y2=70, confidence=0.70, landmarks=MAT_CHUAN.copy())  # 4900
    anh_ra, ly_do, thong_tin = pp.xu_ly_mot_anh(
        p, _DetectorSimples([fb1, fb2, fb3]), _cfg_preprocess()
    )
    assert ly_do == "ok"
    assert anh_ra is not None
    assert thong_tin["n_faces"] == 3
    assert thong_tin["bbox_w"] == 120
    assert thong_tin["bbox_h"] == 160


def test_dong22b_dien_tich_thang_do_tin_cay(tmp_path):
    """Ca chặn lỗi đã xảy ra thật (GÓP Ý-1 biên bản review vòng 1): mặt A nhỏ hơn nhưng độ tin
    cậy cao hơn đứng TRƯỚC trong danh sách (đã sắp theo conf giảm dần) không được thắng mặt B
    lớn hơn nhưng conf thấp hơn."""
    p = tmp_path / "anh.jpg"
    _anh_that(p, kich_thuoc=200)
    mat_a = FaceBox(x1=0, y1=0, x2=40, y2=70, confidence=0.870, landmarks=MAT_CHUAN.copy())
    mat_b = FaceBox(x1=0, y1=0, x2=120, y2=160, confidence=0.850, landmarks=MAT_CHUAN.copy())
    anh_ra, ly_do, thong_tin = pp.xu_ly_mot_anh(
        p, _DetectorSimples([mat_a, mat_b]), _cfg_preprocess()
    )
    assert ly_do == "ok"
    assert anh_ra is not None
    assert thong_tin["bbox_w"] == 120


def test_dong22c_dien_tich_bang_nhau_lay_tin_cay_cao_hon(tmp_path):
    """Diện tích bằng nhau → lấy mặt tin cậy cao hơn."""
    p = tmp_path / "anh.jpg"
    _anh_that(p, kich_thuoc=200)
    fb_cao = _face_hop_le(conf=0.9)
    fb_thap = _face_hop_le(conf=0.8)
    anh_ra, ly_do, thong_tin = pp.xu_ly_mot_anh(
        p, _DetectorSimples([fb_cao, fb_thap]), _cfg_preprocess()
    )
    assert ly_do == "ok"
    assert anh_ra is not None
    assert thong_tin["conf"] == pytest.approx(0.9)


def test_dong23_loicauhinh_tu_align_lan_len(tmp_path, monkeypatch):
    p = tmp_path / "anh.jpg"
    _anh_that(p, kich_thuoc=200)
    fb = _face_hop_le()

    def _can_chinh_gia(anh, diem_moc, cfg):
        raise LoiCauHinh("cấu hình hỏng (giả lập)")

    monkeypatch.setattr(pp, "can_chinh", _can_chinh_gia)
    with pytest.raises(LoiCauHinh):
        pp.xu_ly_mot_anh(p, _DetectorSimples([fb]), _cfg_preprocess())


def test_dong24_valueerror_tu_align_khong_hong_ca_me(tmp_path, monkeypatch):
    p = tmp_path / "anh.jpg"
    _anh_that(p, kich_thuoc=200)
    fb = _face_hop_le()

    def _can_chinh_gia(anh, diem_moc, cfg):
        raise ValueError("điểm mốc suy biến (giả lập)")

    monkeypatch.setattr(pp, "can_chinh", _can_chinh_gia)
    anh_ra, ly_do, _thong_tin = pp.xu_ly_mot_anh(p, _DetectorSimples([fb]), _cfg_preprocess())
    assert anh_ra is None
    assert ly_do == "diem_moc_bat_thuong"


# =============================================================================
# §9.4 — Manifest và đầu ra (dòng 25-32)
# =============================================================================


def test_dong25_manifest_bay_cot_dung_thu_tu(tmp_path):
    pp.ghi_manifest(tmp_path / "manifest.csv", [_ban_ghi_ok()])
    with open(tmp_path / "manifest.csv", newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == ["file_vao", "file_ra", "ly_do", "n_faces", "conf", "bbox_w", "bbox_h"]


def test_dong26_moi_anh_dung_mot_dong_ke_ca_bi_bo_qua(tmp_path, monkeypatch):
    """5 ảnh, 2 bị bỏ qua (không thấy mặt) — manifest vẫn phải có đúng 5 dòng."""
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    for i in range(5):
        _anh_that(vao / f"anh_{i:02d}.jpg", seed=i)

    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)

    dem = {"n": 0}

    def _detect_gia(anh):
        dem["n"] += 1
        if dem["n"] > 3:
            return []
        return [_face_hop_le()]

    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(_detect_gia))

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--model",
            "gia.onnx",
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
        ]
    )
    assert ma == 0
    with open(ra / "manifest.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5
    ly_do_dem = [r["ly_do"] for r in rows]
    assert ly_do_dem.count("khong_thay_mat") == 2
    assert ly_do_dem.count("ok") == 3


def test_dong27_file_ra_rong_khong_phai_none(tmp_path, monkeypatch):
    """Đi qua main() thật — chỗ quyết định đặt gì vào file_ra khi ảnh bị bỏ qua (CẦN SỬA-2
    biên bản review vòng 1). Detector giả trả [] để ảnh bị bỏ qua với lý do khong_thay_mat."""
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    _anh_that(vao / "c.jpg")
    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)
    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: []))

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--model",
            "gia.onnx",
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
        ]
    )
    assert ma == 0
    with open(ra / "manifest.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["ly_do"] == "khong_thay_mat"
    assert rows[0]["file_ra"] == ""
    assert rows[0]["file_ra"] != "None"


@pytest.fixture
def _main_cau_truc_con(tmp_path, monkeypatch):
    """Chạy main() một lần với ảnh trong thư mục con A/, trả về (ra_dir, rows)."""
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    _anh_that(vao / "A" / "x.jpg", kich_thuoc=200)

    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)
    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: [_face_hop_le()]))

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--model",
            "gia.onnx",
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
        ]
    )
    assert ma == 0
    with open(ra / "manifest.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return ra, rows


def test_dong28_duong_dan_dung_dau_gach_cheo(_main_cau_truc_con):
    _ra, rows = _main_cau_truc_con
    assert "\\" not in rows[0]["file_vao"]
    assert "\\" not in rows[0]["file_ra"]


def test_dong29_cau_truc_thu_muc_con_giu_nguyen(_main_cau_truc_con):
    _ra, rows = _main_cau_truc_con
    assert rows[0]["file_vao"] == "A/x.jpg"
    assert rows[0]["file_ra"] == "A/x.png"


def test_dong30_duoi_ra_luon_png(_main_cau_truc_con):
    ra, _rows = _main_cau_truc_con
    ra_path = ra / "A" / "x.png"
    assert ra_path.exists()
    assert ra_path.suffix == ".png"


def test_dong31_ban_ghi_thieu_khoa_nem_loi(tmp_path):
    with pytest.raises(LoiCauHinh):
        pp.ghi_manifest(tmp_path / "manifest.csv", [{}])


def test_dong32_ban_ghi_du_khoa_ghi_thanh_cong(tmp_path):
    pp.ghi_manifest(tmp_path / "manifest.csv", [_ban_ghi_ok()])
    assert (tmp_path / "manifest.csv").exists()


# =============================================================================
# §9.5 — Luồng chính main() (dòng 33-43)
# =============================================================================


def test_dong33_dry_run_khong_ghi_tep(tmp_path):
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    _anh_that(vao / "a.jpg")
    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
            "--dry-run",
        ]
    )
    assert ma == 0
    assert not ra.exists()


def test_dong34_thieu_vao_hoac_ra(tmp_path):
    assert pp.main(["--ra", str(tmp_path / "ra")]) == 1
    assert pp.main(["--vao", str(tmp_path / "vao")]) == 1


def test_dong35_mo_hinh_khong_ton_tai(tmp_path):
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    _anh_that(vao / "a.jpg")
    ma = pp.main(
        ["--vao", str(vao), "--ra", str(ra), "--model", str(tmp_path / "khong_ton_tai.onnx")]
    )
    assert ma == 1


def test_dong36_cau_hinh_hong(tmp_path):
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    _anh_that(vao / "a.jpg")
    cfg_hong = tmp_path / "hong.yaml"
    cfg_hong.write_text("khoa: [1, 2\n", encoding="utf-8")  # ngoặc chưa đóng => lỗi cú pháp YAML
    ma = pp.main(["--vao", str(vao), "--ra", str(ra), "--config-preprocess", str(cfg_hong)])
    assert ma == 1


def test_dong36b_gia_tri_sai_kieu_tra_ve_1(tmp_path, monkeypatch):
    """CẦN SỬA-1 biên bản review vòng 1: `min_ti_le_lech_mui` đọc thành chuỗi (dấu nháy bỏ nhầm
    quanh một số trong YAML) phải làm main() trả 1, không để TypeError/UFuncTypeError lọt ra
    ngoài."""
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    _anh_that(vao / "a.jpg", kich_thuoc=200)

    dong = ["output_size: [112, 112]", "reference_landmarks:"]
    dong += [f"  - [{x}, {y}]" for x, y in MAT_CHUAN.tolist()]
    dong += [
        "interpolation: bilinear",
        "border_value: [0, 0, 0]",
        "loc_chat_luong:",
        "  min_bbox_px: 40",
        "  min_confidence: 0.7",
        "  kiem_hinh_hoc_diem_moc: true",
        '  min_ti_le_lech_mui: "0.15"',
    ]
    cfg_pp = tmp_path / "preprocess_sai_kieu.yaml"
    cfg_pp.write_text("\n".join(dong) + "\n", encoding="utf-8")
    cfg_dt = _ghi_cfg_detect(tmp_path)
    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: [_face_hop_le()]))

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--model",
            "gia.onnx",
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
        ]
    )
    assert ma == 1


def test_dong37_cau_hinh_hong_dung_ngay_khong_xu_ly_anh_nao(tmp_path, monkeypatch):
    """⚠️ Ca chặn lỗi bắt gộp `except Exception` — xem ĐB1 §10 đặc tả.

    Cấu hình cú pháp YAML hợp lệ nhưng THIẾU khoá 'output_size' — lỗi này chỉ lộ ra khi
    `align.can_chinh()` thực sự được gọi cho ảnh đầu tiên bên trong `xu_ly_mot_anh` (khác với
    dòng 36: lỗi cú pháp, lộ ra ngay lúc `nap_cau_hinh()` phân tích cú pháp).
    """
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    for i in range(10):
        _anh_that(vao / f"anh_{i:02d}.jpg", seed=i)

    dong = ["reference_landmarks:"]
    dong += [f"  - [{x}, {y}]" for x, y in MAT_CHUAN.tolist()]
    dong += [
        "interpolation: bilinear",
        "border_value: [0, 0, 0]",
        "loc_chat_luong:",
        "  min_bbox_px: 40",
        "  min_confidence: 0.7",
        "  kiem_hinh_hoc_diem_moc: true",
        "  min_ti_le_lech_mui: 0.15",
    ]
    cfg_pp = tmp_path / "preprocess_thieu_output_size.yaml"
    cfg_pp.write_text("\n".join(dong) + "\n", encoding="utf-8")
    cfg_dt = _ghi_cfg_detect(tmp_path)

    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: [_face_hop_le()]))

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--model",
            "gia.onnx",
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
        ]
    )

    assert ma == 1
    assert not (ra / "manifest.csv").exists()
    assert not ra.exists() or list(ra.iterdir()) == []


def test_dong38_gioi_han_dung_so_luong(tmp_path, monkeypatch):
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    for i in range(20):
        _anh_that(vao / f"anh_{i:02d}.jpg", seed=i)
    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)
    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: [_face_hop_le()]))

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--model",
            "gia.onnx",
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
            "--gioi-han",
            "5",
        ]
    )
    assert ma == 0
    with open(ra / "manifest.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 5


def test_dong39_cung_seed_chon_cung_tap(tmp_path, monkeypatch):
    vao = tmp_path / "vao"
    for i in range(20):
        _anh_that(vao / f"anh_{i:02d}.jpg", seed=i)
    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)
    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: [_face_hop_le()]))

    args_chung = [
        "--vao",
        str(vao),
        "--model",
        "gia.onnx",
        "--config-preprocess",
        str(cfg_pp),
        "--config-detect",
        str(cfg_dt),
        "--gioi-han",
        "5",
        "--seed",
        "7",
    ]

    ra1 = tmp_path / "ra1"
    ra2 = tmp_path / "ra2"
    assert pp.main(["--ra", str(ra1)] + args_chung) == 0
    assert pp.main(["--ra", str(ra2)] + args_chung) == 0

    with open(ra1 / "manifest.csv", newline="", encoding="utf-8") as f:
        tap1 = {r["file_vao"] for r in csv.DictReader(f)}
    with open(ra2 / "manifest.csv", newline="", encoding="utf-8") as f:
        tap2 = {r["file_vao"] for r in csv.DictReader(f)}
    assert tap1 == tap2
    assert len(tap1) == 5


def _chay_lan_dau_va_backdate(tmp_path, monkeypatch):
    """Chạy main() lần đầu (3 ảnh), lùi mtime tệp ra đầu tiên về một mốc cố định."""
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    for i in range(3):
        _anh_that(vao / f"anh_{i:02d}.jpg", seed=i)
    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)
    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: [_face_hop_le()]))

    args_chung = [
        "--vao",
        str(vao),
        "--ra",
        str(ra),
        "--model",
        "gia.onnx",
        "--config-preprocess",
        str(cfg_pp),
        "--config-detect",
        str(cfg_dt),
    ]
    assert pp.main(list(args_chung)) == 0

    tep_dau = ra / "anh_00.png"
    assert tep_dau.exists()

    # Lùi mtime về mốc cố định trong quá khứ — tránh phụ thuộc độ phân giải mtime hệ điều hành,
    # kiểm chắc chắn việc ghi đè hay không thay vì so sánh thời gian thực thi (có thể trùng giây).
    moc_cu = 1_600_000_000.0
    os.utime(tep_dau, (moc_cu, moc_cu))

    return ra, args_chung, tep_dau, moc_cu


def test_dong40_tiep_tuc_khong_ghi_de(tmp_path, monkeypatch):
    _ra, args_chung, tep_dau, moc_cu = _chay_lan_dau_va_backdate(tmp_path, monkeypatch)

    ma2 = pp.main(list(args_chung) + ["--tiep-tuc"])
    assert ma2 == 0
    assert tep_dau.stat().st_mtime == pytest.approx(moc_cu)


def test_dong41_khong_tiep_tuc_xu_ly_lai_tu_dau(tmp_path, monkeypatch):
    _ra, args_chung, tep_dau, moc_cu = _chay_lan_dau_va_backdate(tmp_path, monkeypatch)

    ma2 = pp.main(list(args_chung))
    assert ma2 == 0
    assert tep_dau.stat().st_mtime != pytest.approx(moc_cu)


def test_dong42_bang_tong_ket_du_sau_ly_do(tmp_path, monkeypatch, capsys):
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    _anh_that(vao / "a.jpg")
    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)
    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: [_face_hop_le()]))

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--model",
            "gia.onnx",
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
        ]
    )
    assert ma == 0
    ra_out = capsys.readouterr().out
    for ly_do in (
        "ok",
        "khong_doc_duoc_anh",
        "khong_thay_mat",
        "mat_qua_nho",
        "do_tin_cay_thap",
        "diem_moc_bat_thuong",
    ):
        assert ly_do in ra_out


def test_dong43_tra_ve_0_khi_co_anh_bi_bo_qua(tmp_path, monkeypatch):
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    _anh_that(vao / "a.jpg")
    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)
    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: []))

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--model",
            "gia.onnx",
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
        ]
    )
    assert ma == 0
    with open(ra / "manifest.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["ly_do"] == "khong_thay_mat"


def test_dong43b_bang_tong_ket_in_seed_va_gioi_han(tmp_path, monkeypatch, capsys):
    """CẦN SỬA-3 biên bản review vòng 1 (R15): bảng tổng kết của lần chạy THẬT (không phải
    --dry-run) phải in seed và giới hạn đã dùng, để tái lập được mẻ chỉ từ nhìn đầu ra CLI."""
    vao = tmp_path / "vao"
    ra = tmp_path / "ra"
    for i in range(5):
        _anh_that(vao / f"anh_{i:02d}.jpg", seed=i)
    cfg_pp = _ghi_cfg_preprocess(tmp_path)
    cfg_dt = _ghi_cfg_detect(tmp_path)
    monkeypatch.setattr(pp, "YoloFaceDetector", _lop_detector_gia(lambda anh: [_face_hop_le()]))

    ma = pp.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--model",
            "gia.onnx",
            "--config-preprocess",
            str(cfg_pp),
            "--config-detect",
            str(cfg_dt),
            "--gioi-han",
            "3",
            "--seed",
            "99",
        ]
    )
    assert ma == 0
    ra_out = capsys.readouterr().out
    assert "Seed: `99`" in ra_out
    assert "giới hạn: `3`" in ra_out
