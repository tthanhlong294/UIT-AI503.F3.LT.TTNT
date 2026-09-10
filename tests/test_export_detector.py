"""Kiểm thử cho scripts/export_detector.py.

Ca cần mô hình thật (`models/yolov8n-face.pt`, thư viện `ultralytics`/`torch`/`onnx`/
`onnxruntime`) được đánh dấu `@pytest.mark.slow`. Các ca đó ghi tệp .onnx tạm vào
`tmp_path`, KHÔNG ghi vào `models/` hay `results/` thật.

⚠️ `onnx`/`onnxruntime` chỉ được import BÊN TRONG thân các ca `@pytest.mark.slow` cần
chúng (dòng 16, 17) — không bao giờ ở mức module (xem §10 đặc tả). Ba gói này không có
trong `requirements.txt`/container ARM64; import ở mức module làm `pytest` chết ngay khâu
thu thập, kéo đổ cả bộ test không riêng tệp này. Nhờ vậy `pytest -m "not slow"` chạy được
toàn bộ phần còn lại, không cần mạng và không cần các thư viện đó.
"""

import re
import shutil
from pathlib import Path

import numpy as np
import pytest

from scripts.export_detector import (
    _chon_mau_anh,
    _ten_tep_ket_qua,
    doc_cau_hinh,
    export_mot_kich_thuoc,
    ghi_ket_qua,
    kiem_chung_tuong_duong,
    main,
    so_sanh_mot_anh,
)
from src.common.exceptions import LoiCauHinh, LoiMoHinh

_DUONG_DAN_WEIGHTS_THAT = Path("models/yolov8n-face.pt")
_DUONG_DAN_LFW_THAT = Path("data/impostor/lfw_original")

# Ngưỡng của CA KIỂM THỬ (không phải của mã sản phẩm — xem §4 đặc tả P0-04): _chon_mau_anh trả
# nguyên danh sách khi số ảnh có sẵn <= so_anh yêu cầu, nên phải có NHIỀU HƠN 20 tệp để phép lấy
# mẫu thực sự diễn ra. Với 100 tệp, xác suất hai seed khác nhau trùng cùng 20 tệp là ~1/C(100,20).
_TOI_THIEU_ANH_LAY_MAU = 100


def _bo_qua_neu_thieu_weights_pt(duong_dan: Path) -> None:
    """Bỏ qua ca kiểm thử (có thông báo) nếu tệp trọng số `.pt` thật chưa có trên máy.

    Trọng số `.pt` là đầu vào tải thủ công, không phải đầu ra của script nào — vì vậy
    thông báo chỉ sang tài liệu nguồn tải, không chỉ sang một script.
    """
    if not duong_dan.exists():
        pytest.skip(f"chưa có {duong_dan}; xem models/README.md để tải trọng số")


def _bo_qua_neu_lfw_thieu_anh() -> None:
    """Bỏ qua ca kiểm thử nếu _DUONG_DAN_LFW_THAT có ít hơn _TOI_THIEU_ANH_LAY_MAU ảnh."""
    so_anh = len(list(_DUONG_DAN_LFW_THAT.rglob("*.jpg"))) if _DUONG_DAN_LFW_THAT.exists() else 0
    if so_anh < _TOI_THIEU_ANH_LAY_MAU:
        pytest.skip(
            f"'{_DUONG_DAN_LFW_THAT}' chỉ có {so_anh} ảnh, cần ít nhất "
            f"{_TOI_THIEU_ANH_LAY_MAU}. Chạy scripts/download_lfw.py trước."
        )


def _cfg_co_ban() -> dict:
    """Cấu hình hợp lệ tối giản dùng làm nền cho các ca kiểm thử biến thể lỗi."""
    return {
        "export": {
            "weights_pt": "models/yolov8n-face.pt",
            "kich_thuoc": [320, 640],
            "opset": 12,
            "batch": 1,
            "simplify": True,
            "out_dir": "models",
        },
        "inference": {
            "conf_threshold": 0.5,
            "iou_threshold": 0.45,
        },
    }


def _sao_chep_weights_tam(thu_muc: Path) -> Path:
    """Sao chép trọng số .pt thật vào thư mục tạm — export không ghi vào models/ thật."""
    _bo_qua_neu_thieu_weights_pt(_DUONG_DAN_WEIGHTS_THAT)
    dich = thu_muc / "yolov8n-face.pt"
    shutil.copy2(_DUONG_DAN_WEIGHTS_THAT, dich)
    return dich


def _vai_anh_lfw_that(so_luong: int) -> list[Path]:
    """Vài ảnh LFW thật đầu tiên tìm thấy, dùng cho ca kiểm thử kiem_chung_tuong_duong."""
    anh = sorted(_DUONG_DAN_LFW_THAT.rglob("*.jpg"))
    if len(anh) < so_luong:
        pytest.skip(
            f"'{_DUONG_DAN_LFW_THAT}' chỉ có {len(anh)} ảnh, cần ít nhất {so_luong}. "
            "Chạy scripts/download_lfw.py trước."
        )
    return anh[:so_luong]


def _ban_ghi_hop_le() -> dict:
    return {
        "n_anh": 50,
        "n_khop_so_mat": 49,
        "iou_trung_binh": 0.97,
        "iou_nho_nhat": 0.91,
        "sai_so_diem_moc_trung_binh": 1.2,
        "sai_so_diem_moc_lon_nhat": 4.8,
        "dat": True,
        "meta": {
            "commit": "abc123",
            "cau_hinh": {"export": {}},
            "phien_ban": {"ultralytics": "8.4.39"},
            "thiet_bi": {"hostname": "may-test"},
            "thoi_diem": "2026-08-18T00:00:00+07:00",
        },
    }


# ============================================================================
# §8.1 — doc_cau_hinh (dòng 01-12)
# ============================================================================


def test_dong01_cau_hinh_hop_le_du_tam_khoa():
    kq = doc_cau_hinh(_cfg_co_ban())
    assert set(kq) >= {
        "weights_pt",
        "kich_thuoc",
        "opset",
        "batch",
        "simplify",
        "out_dir",
        "conf_threshold",
        "iou_threshold",
    }


def test_dong02_thieu_export_nem_loi():
    cfg = _cfg_co_ban()
    del cfg["export"]
    with pytest.raises(LoiCauHinh, match="export"):
        doc_cau_hinh(cfg)


def test_dong03_thieu_weights_pt_nem_loi():
    cfg = _cfg_co_ban()
    del cfg["export"]["weights_pt"]
    with pytest.raises(LoiCauHinh, match="weights_pt"):
        doc_cau_hinh(cfg)


def test_dong04_thieu_kich_thuoc_nem_loi():
    cfg = _cfg_co_ban()
    del cfg["export"]["kich_thuoc"]
    with pytest.raises(LoiCauHinh, match="kich_thuoc"):
        doc_cau_hinh(cfg)


def test_dong05_thieu_opset_nem_loi():
    cfg = _cfg_co_ban()
    del cfg["export"]["opset"]
    with pytest.raises(LoiCauHinh, match="opset"):
        doc_cau_hinh(cfg)


def test_dong06_thieu_conf_threshold_nem_loi():
    cfg = _cfg_co_ban()
    del cfg["inference"]["conf_threshold"]
    with pytest.raises(LoiCauHinh, match="conf_threshold"):
        doc_cau_hinh(cfg)


def test_dong07_kich_thuoc_rong_nem_loi():
    cfg = _cfg_co_ban()
    cfg["export"]["kich_thuoc"] = []
    with pytest.raises(LoiCauHinh):
        doc_cau_hinh(cfg)


def test_dong08_kich_thuoc_phan_tu_khong_hop_le_nem_loi():
    for bien_the in ([320, "abc"], [320, -1], [320, 0], [320, 1.5]):
        cfg = _cfg_co_ban()
        cfg["export"]["kich_thuoc"] = bien_the
        with pytest.raises(LoiCauHinh, match="kich_thuoc"):
            doc_cau_hinh(cfg)


def test_dong09_opset_sai_kieu_hoac_ngoai_mien_nem_loi():
    for bien_the in ("12", -1, 0):
        cfg = _cfg_co_ban()
        cfg["export"]["opset"] = bien_the
        with pytest.raises(LoiCauHinh):
            doc_cau_hinh(cfg)


def test_dong10_conf_threshold_ngoai_mien_nem_loi():
    for bien_the in (-0.1, 1.5, "0.5"):
        cfg = _cfg_co_ban()
        cfg["inference"]["conf_threshold"] = bien_the
        with pytest.raises(LoiCauHinh):
            doc_cau_hinh(cfg)


def test_dong11_iou_threshold_ngoai_mien_nem_loi():
    for bien_the in (-0.1, 1.5, "0.45"):
        cfg = _cfg_co_ban()
        cfg["inference"]["iou_threshold"] = bien_the
        with pytest.raises(LoiCauHinh):
            doc_cau_hinh(cfg)


def test_dong12_moi_loi_cau_hinh_la_loicauhinh_va_neu_gia_tri_loi():
    """Phủ đủ năm khoá (mỗi khoá >= 2 biến thể); thông báo lỗi phải nêu giá trị gây lỗi.

    gia_tri_ky_vong khác gia_tri_gan cho kich_thuoc=[0]: thông báo nêu PHẦN TỬ hỏng (0),
    không phải cả danh sách ([0]) — xem nhánh kiểm tra từng phần tử trong doc_cau_hinh.
    """
    bien_the = [
        ("export", "weights_pt", None, None),
        ("export", "weights_pt", "", ""),
        ("export", "kich_thuoc", [], []),
        ("export", "kich_thuoc", [0], 0),
        ("export", "opset", -1, -1),
        ("export", "opset", "12", "12"),
        ("inference", "conf_threshold", -0.1, -0.1),
        ("inference", "conf_threshold", "0.5", "0.5"),
        ("inference", "iou_threshold", 1.5, 1.5),
        ("inference", "iou_threshold", "0.45", "0.45"),
    ]
    for nhom, khoa, gia_tri_gan, gia_tri_ky_vong in bien_the:
        cfg = _cfg_co_ban()
        cfg[nhom][khoa] = gia_tri_gan
        with pytest.raises(LoiCauHinh) as exc_info:
            doc_cau_hinh(cfg)
        assert repr(gia_tri_ky_vong) in str(exc_info.value)


# ============================================================================
# §8.2 — export_mot_kich_thuoc (dòng 13-19)
# ============================================================================


def test_dong13_export_trong_so_khong_ton_tai_nem_loi():
    with pytest.raises(LoiMoHinh, match=""):
        export_mot_kich_thuoc(
            Path("khong/ton/tai.pt"), 320, 12, 1, True, Path("khong_quan_trong"), dry_run=False
        )


def test_dong14_export_dry_run_ten_tep_dung_quy_uoc(tmp_path):
    p = export_mot_kich_thuoc(_DUONG_DAN_WEIGHTS_THAT, 320, 12, 1, True, tmp_path, dry_run=True)
    assert p.name == "yolov8n-face-320.onnx"


def test_dong15_export_dry_run_khong_tao_tep(tmp_path):
    out_dir = tmp_path / "ra"
    out_dir.mkdir()
    truoc = set(out_dir.rglob("*"))

    export_mot_kich_thuoc(_DUONG_DAN_WEIGHTS_THAT, 320, 12, 1, True, out_dir, dry_run=True)

    sau = set(out_dir.rglob("*"))
    assert truoc == sau


@pytest.mark.slow
def test_dong16_export_that_tao_tep_onnx_doc_duoc(tmp_path):
    import onnx  # chỉ ca slow mới cần; container ARM64 không cài onnx (đọc §10)

    weights = _sao_chep_weights_tam(tmp_path)
    p = export_mot_kich_thuoc(weights, 320, 12, 1, True, tmp_path)
    onnx.load(str(p))  # không ném lỗi => tệp ONNX hợp lệ
    assert p.stat().st_size > 0


@pytest.mark.slow
def test_dong17_export_dau_vao_dung_hinh_dang(tmp_path):
    import onnxruntime  # chỉ ca slow mới cần; container ARM64 không cài onnx (đọc §10)

    weights = _sao_chep_weights_tam(tmp_path)
    p = export_mot_kich_thuoc(weights, 320, 12, 1, True, tmp_path)
    sess = onnxruntime.InferenceSession(str(p))
    assert len(sess.get_inputs()) == 1
    assert sess.get_inputs()[0].shape[1:] == [3, 320, 320]


@pytest.mark.slow
def test_dong18_export_320_va_640_hai_tep_khac_nhau(tmp_path):
    weights = _sao_chep_weights_tam(tmp_path)
    p320 = export_mot_kich_thuoc(weights, 320, 12, 1, True, tmp_path)
    p640 = export_mot_kich_thuoc(weights, 640, 12, 1, True, tmp_path)
    assert p320 != p640
    assert p320.exists() and p640.exists()


@pytest.mark.slow
def test_dong19_export_lai_ghi_de_khong_nem_loi(tmp_path):
    weights = _sao_chep_weights_tam(tmp_path)
    p1 = export_mot_kich_thuoc(weights, 320, 12, 1, True, tmp_path)
    p2 = export_mot_kich_thuoc(weights, 320, 12, 1, True, tmp_path)
    assert p1 == p2
    assert p2.exists()


# ============================================================================
# §8.3 — so_sanh_mot_anh / kiem_chung_tuong_duong (dòng 20-29)
# ============================================================================


def test_dong20_so_sanh_giong_het_dat():
    khung = np.array([[10.0, 10.0, 50.0, 50.0]])
    diem = np.array([[[20.0, 20.0], [30.0, 20.0], [25.0, 30.0], [20.0, 40.0], [30.0, 40.0]]])
    kq = so_sanh_mot_anh(khung, diem, khung.copy(), diem.copy(), 0.90, 5.0)
    assert kq["iou_min"] == 1.0
    assert kq["sai_so_diem_moc_max"] == 0.0
    assert kq["dat"] is True


def test_dong21_so_sanh_lech_so_mat():
    khung_pt = np.array([[0.0, 0.0, 10.0, 10.0]])
    diem_pt = np.zeros((1, 5, 2))
    khung_onnx = np.array([[0.0, 0.0, 10.0, 10.0], [20.0, 20.0, 30.0, 30.0]])
    diem_onnx = np.zeros((2, 5, 2))
    kq = so_sanh_mot_anh(khung_pt, diem_pt, khung_onnx, diem_onnx, 0.90, 5.0)
    assert kq["khop_so_mat"] is False
    assert kq["dat"] is False
    assert kq["iou_min"] is None


def test_dong22_so_sanh_khung_lech_nhe_van_dat():
    khung_pt = np.array([[0.0, 0.0, 100.0, 100.0]])
    khung_onnx = np.array([[2.0, 2.0, 102.0, 102.0]])
    diem = np.zeros((1, 5, 2))
    kq = so_sanh_mot_anh(khung_pt, diem, khung_onnx, diem.copy(), 0.90, 5.0)
    assert kq["iou_min"] == pytest.approx(9604 / 10396)
    assert kq["dat"] is True


def test_dong23_so_sanh_khung_lech_nhieu_khong_dat():
    khung_pt = np.array([[0.0, 0.0, 10.0, 10.0]])
    khung_onnx = np.array([[50.0, 50.0, 60.0, 60.0]])
    diem = np.zeros((1, 5, 2))
    kq = so_sanh_mot_anh(khung_pt, diem, khung_onnx, diem.copy(), 0.90, 5.0)
    assert kq["dat"] is False


def test_dong23b_so_sanh_nguong_iou_khac_nhau_cho_ket_qua_khac_nhau():
    khung_pt = np.array([[0.0, 0.0, 100.0, 100.0]])
    khung_onnx = np.array([[2.0, 2.0, 102.0, 102.0]])
    diem = np.zeros((1, 5, 2))
    kq_nguong_thap = so_sanh_mot_anh(khung_pt, diem, khung_onnx, diem.copy(), 0.90, 5.0)
    kq_nguong_cao = so_sanh_mot_anh(khung_pt, diem, khung_onnx, diem.copy(), 0.95, 5.0)
    assert kq_nguong_thap["dat"] is True
    assert kq_nguong_cao["dat"] is False


def test_dong24_so_sanh_diem_moc_lech_qua_nguong():
    khung = np.array([[0.0, 0.0, 100.0, 100.0]])
    diem_pt = np.array([[[10.0, 10.0], [20.0, 10.0], [15.0, 20.0], [10.0, 30.0], [20.0, 30.0]]])
    diem_onnx = diem_pt.copy()
    diem_onnx[0, 0, 0] += 20.0

    kq = so_sanh_mot_anh(khung, diem_pt, khung.copy(), diem_onnx, 0.90, 5.0)
    assert kq["dat"] is False
    assert kq["sai_so_diem_moc_max"] == pytest.approx(20.0)


def test_dong25_so_sanh_ca_hai_khong_co_mat():
    khung = np.zeros((0, 4))
    diem = np.zeros((0, 5, 2))
    kq = so_sanh_mot_anh(khung, diem, khung.copy(), diem.copy(), 0.90, 5.0)
    assert kq["khop_so_mat"] is True
    assert kq["dat"] is True


def test_dong25b_so_sanh_so_khung_khong_khop_so_diem_moc_nem_loi():
    khung_pt = np.array([[0.0, 0.0, 10.0, 10.0], [20.0, 20.0, 30.0, 30.0]])
    diem_pt = np.zeros((1, 5, 2))  # lệch: 2 khung nhưng chỉ 1 bộ điểm mốc
    khung_onnx = np.zeros((0, 4))
    diem_onnx = np.zeros((0, 5, 2))
    with pytest.raises(ValueError):
        so_sanh_mot_anh(khung_pt, diem_pt, khung_onnx, diem_onnx, 0.90, 5.0)


def test_diem_moc_khong_du_nam_diem_nem_loi():
    """Bổ sung theo review CS-3: chiều giữa khác 5 không được NumPy broadcast âm thầm.

    Trước khi sửa, `diem_onnx` hình dạng (1, 1, 2) lọt qua kiểm hình dạng (chỉ soát
    ndim==3 và chiều cuối==2), rồi `diem_pt - diem_onnx` broadcast im lặng ra một số
    sai số trông có nghĩa thay vì báo lỗi hình dạng.
    """
    khung = np.array([[0.0, 0.0, 10.0, 10.0]])
    diem_pt = np.zeros((1, 5, 2))
    diem_onnx = np.zeros((1, 1, 2))  # chiều giữa sai — phải là 5, không phải 1
    with pytest.raises(ValueError):
        so_sanh_mot_anh(khung, diem_pt, khung.copy(), diem_onnx, 0.90, 5.0)


def test_dong26_iou_tinh_dung_tren_truong_hop_biet_truoc():
    khung1 = np.array([[0.0, 0.0, 10.0, 10.0]])
    khung2 = np.array([[5.0, 5.0, 15.0, 15.0]])
    diem = np.zeros((1, 5, 2))
    kq = so_sanh_mot_anh(khung1, diem, khung2, diem.copy(), 0.0, 999.0)
    assert abs(kq["iou_min"] - 25 / 175) < 1e-9


def test_dong29_kiem_chung_danh_sach_anh_rong_nem_loi():
    with pytest.raises(LoiCauHinh):
        kiem_chung_tuong_duong(Path("x.pt"), Path("x.onnx"), [], 320, 0.5, 0.45, 5.0)


@pytest.fixture(scope="module")
def _onnx_module_export(tmp_path_factory):
    """Một lần export dùng chung cho dòng 27/28 — tránh export lại nhiều lần (chậm)."""
    thu_muc = tmp_path_factory.mktemp("onnx_kiem_chung")
    weights = _sao_chep_weights_tam(thu_muc)
    onnx_path = export_mot_kich_thuoc(weights, 320, 12, 1, True, thu_muc)
    return weights, onnx_path


@pytest.mark.slow
def test_dong27_kiem_chung_tuong_duong_dung_so_anh(_onnx_module_export):
    weights, onnx_path = _onnx_module_export
    danh_sach_anh = _vai_anh_lfw_that(5)
    kq = kiem_chung_tuong_duong(weights, onnx_path, danh_sach_anh, 320, 0.5, 0.45, 5.0)
    assert kq["n_anh"] == len(danh_sach_anh)


@pytest.mark.slow
def test_dong28_kiem_chung_tuong_duong_du_bay_khoa(_onnx_module_export):
    weights, onnx_path = _onnx_module_export
    danh_sach_anh = _vai_anh_lfw_that(3)
    kq = kiem_chung_tuong_duong(weights, onnx_path, danh_sach_anh, 320, 0.5, 0.45, 5.0)
    assert set(kq) >= {
        "n_anh",
        "n_khop_so_mat",
        "iou_trung_binh",
        "iou_nho_nhat",
        "sai_so_diem_moc_trung_binh",
        "sai_so_diem_moc_lon_nhat",
        "dat",
    }


# ============================================================================
# §8.4 — ghi_ket_qua (dòng 30-35)
# ============================================================================


def test_dong30_ghi_ket_qua_tao_ca_hai_tep(tmp_path):
    p = tmp_path / "export_detector_20260818_1200.json"
    ghi_ket_qua(p, _ban_ghi_hop_le())
    assert p.exists() and p.with_suffix(".meta.json").exists()


def test_dong31_ghi_ket_qua_doc_lai_giu_nguyen_so_lieu(tmp_path):
    import json

    p = tmp_path / "export_detector_20260818_1200.json"
    ban_ghi = _ban_ghi_hop_le()
    ghi_ket_qua(p, ban_ghi)
    noi_dung = json.loads(p.read_text(encoding="utf-8"))
    assert noi_dung["iou_trung_binh"] == ban_ghi["iou_trung_binh"]


def test_dong32_meta_du_nam_truong_bat_buoc(tmp_path):
    import json

    p = tmp_path / "export_detector_20260818_1200.json"
    ghi_ket_qua(p, _ban_ghi_hop_le())
    meta = json.loads(p.with_suffix(".meta.json").read_text(encoding="utf-8"))
    assert set(meta) >= {"commit", "cau_hinh", "phien_ban", "thiet_bi", "thoi_diem"}


def test_dong33_ghi_ket_qua_thieu_khoa_nem_loi(tmp_path):
    with pytest.raises(LoiCauHinh):
        ghi_ket_qua(tmp_path / "x.json", {})


def test_dong34_ghi_ket_qua_du_khoa_thanh_cong(tmp_path):
    p = tmp_path / "export_detector_20260818_1200.json"
    ghi_ket_qua(p, _ban_ghi_hop_le())  # không ném lỗi
    assert p.exists()


def test_dong35_ten_tep_dung_khuon():
    import datetime

    ten = _ten_tep_ket_qua(datetime.datetime(2026, 8, 18, 12, 0, tzinfo=datetime.timezone.utc))
    assert re.fullmatch(r"export_detector_\d{8}_\d{4}\.json", ten)


# ============================================================================
# §8.5 — main (dòng 36-42)
# ============================================================================


def test_dong36_main_dry_run_khong_ghi_tep():
    models_dir = Path("models")
    results_dir = Path("results")
    truoc_models = set(models_dir.rglob("*"))
    truoc_results = set(results_dir.rglob("*"))

    assert main(["--dry-run"]) == 0

    assert set(models_dir.rglob("*")) == truoc_models
    assert set(results_dir.rglob("*")) == truoc_results


def test_dong37_main_anh_dir_khong_ton_tai(tmp_path, capsys):
    assert main(["--anh-dir", str(tmp_path / "khong_ton_tai")]) == 1
    ra = capsys.readouterr()
    assert "download_lfw" in ra.out


def test_dong38_main_anh_dir_rong(tmp_path, capsys):
    thu_muc_rong = tmp_path / "rong"
    thu_muc_rong.mkdir()

    assert main(["--anh-dir", str(thu_muc_rong)]) == 1

    ra = capsys.readouterr().out
    assert "rỗng" in ra or "không có ảnh" in ra
    # Phải phân biệt được với thông báo của dòng 37 (thư mục không tồn tại)
    assert "download_lfw" not in ra


def test_dong39_chon_mau_anh_cung_seed_tai_lap(tmp_path):
    """Cùng seed hai lần trả về đúng cùng kết quả (R15) — dùng ảnh .jpg RỖNG tự sinh trong
    tmp_path, không chạm dữ liệu LFW thật: _chon_mau_anh lọc theo đuôi tệp, không mở ảnh, nên
    ca này chưa bao giờ cần ảnh thật (§7.3 đặc tả P0-04; xác nhận không chạm _DUONG_DAN_LFW_THAT
    bằng grep ở §10 đặc tả, không bằng pytest)."""
    for i in range(_TOI_THIEU_ANH_LAY_MAU):
        (tmp_path / f"anh_{i:04d}.jpg").write_bytes(b"")

    a = _chon_mau_anh(tmp_path, 20, 42)
    b = _chon_mau_anh(tmp_path, 20, 42)
    assert a == b


def test_dong40_chon_mau_anh_khac_seed_khac_ket_qua(tmp_path):
    """Seed khác nhau cho kết quả khác nhau, và kết quả trả về luôn được sắp xếp.

    Cần NHIỀU HƠN 20 tệp để phép lấy mẫu thực sự diễn ra (xem _TOI_THIEU_ANH_LAY_MAU) — với
    đúng 21 tệp, xác suất hai seed trùng cùng 20 tệp là 1/21, ca này sẽ đỏ ngẫu nhiên.
    """
    for i in range(_TOI_THIEU_ANH_LAY_MAU):
        (tmp_path / f"anh_{i:04d}.jpg").write_bytes(b"")

    a = _chon_mau_anh(tmp_path, 20, 42)
    b = _chon_mau_anh(tmp_path, 20, 7)
    assert a != b
    assert a == sorted(a)


def test_dong41_main_cau_hinh_hong_tra_ve_1(tmp_path):
    cfg_path = tmp_path / "detect_hong.yaml"
    with open(cfg_path, "w", newline="", encoding="utf-8") as f:
        f.write("export:\n  weights_pt: models/yolov8n-face.pt\n")

    assert main(["--config", str(cfg_path)]) == 1


def test_dong42_main_khong_tim_thay_config(tmp_path):
    assert main(["--config", str(tmp_path / "khong_ton_tai.yaml")]) == 1


def test_dong43_chon_mau_anh_du_lieu_that_cung_seed_tai_lap():
    """Trên dữ liệu LFW thật, cùng seed cho cùng kết quả — và lấy đủ 20 ảnh (không xanh giả
    như khuyết tật cũ khi thư mục vắng mặt/rỗng trả về danh sách rỗng, xem ca 44)."""
    _bo_qua_neu_lfw_thieu_anh()

    a = _chon_mau_anh(_DUONG_DAN_LFW_THAT, 20, 42)
    b = _chon_mau_anh(_DUONG_DAN_LFW_THAT, 20, 42)
    assert a == b
    assert len(a) == 20


def test_dong44_chon_mau_anh_thu_muc_rong(tmp_path):
    """Thư mục rỗng: _chon_mau_anh trả về danh sách rỗng, không ném lỗi.

    Chốt tường minh chính hành vi đã sinh ra khuyết tật cũ ở ca 39/40 (thư mục LFW vắng mặt
    trả về [] khiến ca 39 xanh giả và ca 40 đỏ) — để lần sau không ai phải suy đoán lại.
    """
    assert _chon_mau_anh(tmp_path, 20, 42) == []


# ============================================================================
# §7 P0-05 — hàm gác trọng số .pt chỉ đúng đường lấy trọng số (dòng 55)
# ============================================================================


def test_dong55_gac_trong_so_pt_chi_dung_duong_dan(tmp_path):
    """Thông báo `skip` của hàm gác trọng số `.pt` chỉ sang tài liệu nguồn tải, không còn chỉ
    sang một script — tệp `.pt` là ĐẦU VÀO của script export, không phải đầu ra, nên lời khuyên
    cũ khiến người đọc mất một vòng thử.
    """
    with pytest.raises(pytest.skip.Exception) as e:
        _bo_qua_neu_thieu_weights_pt(tmp_path / "khong_co.pt")
    assert "models/README.md" in str(e.value)  # 55a — chỉ đúng đường
    assert "export_detector.py" not in str(e.value)  # 55b — không còn chỉ sai đường
