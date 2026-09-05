"""Kiểm thử cho src/recognizer/factory.py (mã việc P3-03).

Ca 01, 02, 03, 05, 06 cần trọng số thật (dlib + mobilefacenet.onnx) → `@pytest.mark.slow`. Ca 04
không cần mô hình nào, chạy được cả trong container ARM64 không có `models/` — mọi giá trị bị
chặn ở phần đọc cấu hình, trước khi chạm tới hệ thống tệp.

Tên hàm test tham chiếu số dòng trong bảng §7 của `docs/dac-ta/P3-03-enroll.md`.
"""

from pathlib import Path

import numpy as np
import pytest

from src.common.config import nap_cau_hinh
from src.common.exceptions import LoiCauHinh
from src.recognizer.arcface_backend import ArcFaceBackend
from src.recognizer.base import BoNhanDien
from src.recognizer.dlib_backend import DlibFaceRecognizer
from src.recognizer.factory import tao_bo_nhan_dien

_CONFIG_THAT = Path("configs/recognize.yaml")
_MODEL_DLIB = Path("models/dlib/dlib_face_recognition_resnet_model_v1.dat")
_SHAPE_DLIB = Path("models/dlib/shape_predictor_68_face_landmarks.dat")
_MODEL_ARCFACE = Path("models/mobilefacenet.onnx")


def _bo_qua_neu_thieu_dlib() -> None:
    pytest.importorskip("dlib")
    if not _MODEL_DLIB.exists() or not _SHAPE_DLIB.exists():
        pytest.skip("chưa có trọng số dlib, xem models/README.md để tải mô hình")


def _bo_qua_neu_thieu_arcface() -> None:
    if not _MODEL_ARCFACE.exists():
        pytest.skip("chưa có models/mobilefacenet.onnx, xem models/README.md để tải mô hình")


def _cfg_that() -> dict:
    """Nạp configs/recognize.yaml THẬT — factory phải dựng được từ đúng tệp cấu hình thật."""
    return nap_cau_hinh(_CONFIG_THAT)


# ============================================================================
# §7 — tao_bo_nhan_dien (dòng 01-06)
# ============================================================================


@pytest.mark.slow
def test_dong01_backend_dlib_trong_cfg_tra_ve_dlibfacerecognizer():
    _bo_qua_neu_thieu_dlib()
    cfg = dict(_cfg_that())
    cfg["backend"] = "dlib"
    bo = tao_bo_nhan_dien(cfg)
    assert isinstance(bo, DlibFaceRecognizer)


@pytest.mark.slow
def test_dong02_backend_arcface_trong_cfg_tra_ve_arcfacebackend():
    _bo_qua_neu_thieu_arcface()
    cfg = dict(_cfg_that())
    cfg["backend"] = "arcface"
    bo = tao_bo_nhan_dien(cfg)
    assert isinstance(bo, ArcFaceBackend)


@pytest.mark.slow
def test_dong03_ten_backend_truyen_vao_ghi_de_khoa_backend_cua_cfg():
    _bo_qua_neu_thieu_dlib()
    cfg = dict(_cfg_that())
    cfg["backend"] = "arcface"  # cfg nói arcface...
    bo = tao_bo_nhan_dien(cfg, "dlib")  # ...nhưng tham số truyền vào ghi đè bằng dlib
    assert isinstance(bo, DlibFaceRecognizer)


def test_dong04_ten_backend_la_nem_loicauhinh_neu_ca_hai_khong_hop_le():
    with pytest.raises(LoiCauHinh) as e1:
        tao_bo_nhan_dien({"backend": "resnet"}, "resnet")
    assert "resnet" in str(e1.value)
    assert "dlib" in str(e1.value)
    assert "arcface" in str(e1.value)

    with pytest.raises(LoiCauHinh) as e2:
        tao_bo_nhan_dien({"backend": ""}, "")
    assert "dlib" in str(e2.value)
    assert "arcface" in str(e2.value)

    # ten_backend=None (mặc định) VÀ cfg cũng thiếu khoá "backend"
    with pytest.raises(LoiCauHinh) as e3:
        tao_bo_nhan_dien({})
    assert "dlib" in str(e3.value)
    assert "arcface" in str(e3.value)


@pytest.mark.slow
def test_dong05_backend_tra_ve_la_the_hien_cua_bonhandien():
    _bo_qua_neu_thieu_dlib()
    _bo_qua_neu_thieu_arcface()
    cfg = _cfg_that()

    bo_dlib = tao_bo_nhan_dien(cfg, "dlib")
    assert isinstance(bo_dlib, BoNhanDien)

    bo_arcface = tao_bo_nhan_dien(cfg, "arcface")
    assert isinstance(bo_arcface, BoNhanDien)


@pytest.mark.slow
def test_dong06_factory_chuyen_dung_nhanh_cau_hinh_cho_tung_backend():
    """dlib nhận TOÀN BỘ cfg, ArcFace nhận riêng cfg["arcface"] (§3 đặc tả).

    Kiểm bằng cách đối chiếu vectơ trích ra qua factory với vectơ trích ra bằng cách dựng
    backend TRỰC TIẾP với đúng phần cấu hình mà factory PHẢI truyền — hai vectơ khớp nhau chỉ
    khi factory truyền đúng nhánh cấu hình cho từng backend.
    """
    _bo_qua_neu_thieu_dlib()
    _bo_qua_neu_thieu_arcface()
    cfg = _cfg_that()
    anh = np.zeros((112, 112, 3), dtype=np.uint8)

    bo_dlib_qua_factory = tao_bo_nhan_dien(cfg, "dlib")
    bo_dlib_truc_tiep = DlibFaceRecognizer(cfg)
    assert np.allclose(
        bo_dlib_qua_factory.trich_dac_trung(anh), bo_dlib_truc_tiep.trich_dac_trung(anh)
    )

    bo_arcface_qua_factory = tao_bo_nhan_dien(cfg, "arcface")
    bo_arcface_truc_tiep = ArcFaceBackend(cfg["arcface"])
    assert np.allclose(
        bo_arcface_qua_factory.trich_dac_trung(anh), bo_arcface_truc_tiep.trich_dac_trung(anh)
    )
