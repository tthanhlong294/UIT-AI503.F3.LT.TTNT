"""Kiểm thử cho src/detector/factory.py (mã việc P2-05, mở rộng ở P2-06b).

Số hàng 23-27 trong bảng §7.3 của đặc tả P2-05 ánh xạ 1-1 sang các hàm `test_dong<nn>` dưới
đây. Số hàng 01-05 trong bảng §6.1 của đặc tả P2-06b bổ sung ca cho `tra_ten_backend`.

Ca cần mô hình thật (`.onnx` hoặc thư mục NCNN) đánh dấu `@pytest.mark.slow`; ca dựng
`NcnnFaceDetector` thật còn `pytest.importorskip("ncnn")`. `pytest --collect-only
-m "not slow"` vì thế chạy được kể cả khi máy không có `ncnn`.
"""

from pathlib import Path

import pytest

from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.detector.factory import tao_bo_phat_hien, tra_ten_backend
from src.detector.ncnn_backend import NcnnFaceDetector
from src.detector.yolo_face import YoloFaceDetector

_ONNX_320 = Path("models/yolov8n-face-320.onnx")
_NCNN_320 = Path("models/yolov8n-face-320_ncnn_model")


def _cfg_hop_le() -> dict:
    return {
        "inference": {
            "conf_threshold": 0.5,
            "iou_threshold": 0.45,
            "max_faces": 10,
            "num_threads": 0,
        }
    }


def _bo_qua_neu_thieu(duong_dan: Path) -> None:
    if not duong_dan.exists():
        pytest.skip(f"chưa có {duong_dan}")


@pytest.mark.slow
def test_dong23_duong_dan_onnx_tra_ve_yoloface():
    _bo_qua_neu_thieu(_ONNX_320)
    bo = tao_bo_phat_hien(_ONNX_320, _cfg_hop_le())
    assert isinstance(bo, YoloFaceDetector)


@pytest.mark.slow
def test_dong24_thu_muc_ncnn_tra_ve_ncnnface():
    pytest.importorskip("ncnn")
    _bo_qua_neu_thieu(_NCNN_320)
    bo = tao_bo_phat_hien(_NCNN_320, _cfg_hop_le())
    assert isinstance(bo, NcnnFaceDetector)


def test_dong25_thu_muc_khong_co_param_nem_loicauhinh(tmp_path):
    thu_muc_rong = tmp_path / "rong_ncnn_model"
    thu_muc_rong.mkdir()
    with pytest.raises(LoiCauHinh):
        tao_bo_phat_hien(thu_muc_rong, _cfg_hop_le())


def test_dong26_duoi_la_nem_loicauhinh_neu_da_nhan_gi(tmp_path):
    tep_pt = tmp_path / "mo_hinh.pt"
    tep_pt.write_bytes(b"x")
    tep_bin = tmp_path / "mo_hinh.bin"
    tep_bin.write_bytes(b"x")
    khong_duoi = tmp_path / "mo_hinh"
    khong_duoi.write_bytes(b"x")

    for duong_dan in (tep_pt, tep_bin, khong_duoi):
        with pytest.raises(LoiCauHinh) as exc_info:
            tao_bo_phat_hien(duong_dan, _cfg_hop_le())
        assert str(duong_dan) in str(exc_info.value)


def test_dong27_duong_dan_khong_ton_tai_khong_nem_filenotfounderror_tran():
    with pytest.raises((LoiCauHinh, LoiMoHinh)):
        tao_bo_phat_hien(Path("khong/ton/tai/mo_hinh.onnx"), _cfg_hop_le())


# ============================================================================
# P2-06b §6.1 — tra_ten_backend (dòng 01-05)
# ============================================================================


def test_dong01_tep_onnx_tra_ve_onnx_khong_nap_mo_hinh(tmp_path):
    tep = tmp_path / "a.onnx"
    tep.write_bytes(b"")
    assert tra_ten_backend(tep) == "onnx"


def test_dong02_thu_muc_co_param_tra_ve_ncnn(tmp_path):
    thu_muc = tmp_path / "gia_ncnn_model"
    thu_muc.mkdir()
    (thu_muc / "model.ncnn.param").write_bytes(b"")
    (thu_muc / "model.ncnn.bin").write_bytes(b"")
    (thu_muc / "metadata.yaml").write_bytes(b"")
    assert tra_ten_backend(thu_muc) == "ncnn"


def test_dong03_duong_dan_la_nem_loicauhinh(tmp_path):
    tep_pt = tmp_path / "mo_hinh.pt"
    tep_pt.write_bytes(b"x")
    khong_duoi = tmp_path / "mo_hinh"
    khong_duoi.write_bytes(b"x")
    thu_muc_rong = tmp_path / "rong_ncnn_model"
    thu_muc_rong.mkdir()

    for duong_dan in (tep_pt, khong_duoi, thu_muc_rong):
        with pytest.raises(LoiCauHinh):
            tra_ten_backend(duong_dan)


def test_dong04_thong_bao_loi_giong_het_tao_bo_phat_hien(tmp_path):
    duong_dan_la = tmp_path / "mo_hinh.pt"
    duong_dan_la.write_bytes(b"x")

    with pytest.raises(LoiCauHinh) as e1:
        tra_ten_backend(duong_dan_la)
    with pytest.raises(LoiCauHinh) as e2:
        tao_bo_phat_hien(duong_dan_la, _cfg_hop_le())

    assert str(e1.value) == str(e2.value)


@pytest.mark.slow
def test_dong05_hai_nguon_dong_thuan_tren_mo_hinh_that():
    _bo_qua_neu_thieu(_ONNX_320)
    assert tra_ten_backend(_ONNX_320) == tao_bo_phat_hien(_ONNX_320, _cfg_hop_le()).ten_backend

    pytest.importorskip("ncnn")
    _bo_qua_neu_thieu(_NCNN_320)
    assert tra_ten_backend(_NCNN_320) == tao_bo_phat_hien(_NCNN_320, _cfg_hop_le()).ten_backend
