"""Kiểm thử cho src/detector/ncnn_backend.py (mã việc P2-05).

Ràng buộc thu thập (§7.3 đặc tả): `pytest --collect-only -m "not slow"` phải chạy trót
lọt kể cả khi máy KHÔNG có gói `ncnn`. Vì vậy:
  * `ncnn` không bao giờ được import ở mức module;
  * ca cần gói `ncnn` thật đánh dấu `@pytest.mark.slow` và `pytest.importorskip("ncnn")`;
  * ca kiểm hành vi khởi tạo/validate dùng một `ncnn` giả cắm qua `monkeypatch`.

Số hàng 10-22 trong bảng §7.2 của đặc tả ánh xạ 1-1 sang các hàm `test_dong<nn>` dưới đây.
"""

import sys
import types
from pathlib import Path

import numpy as np
import pytest

from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.detector.ncnn_backend import NcnnFaceDetector
from src.detector.yolo_face import YoloFaceDetector

_NCNN_320 = Path("models/yolov8n-face-320_ncnn_model")
_ONNX_320 = Path("models/yolov8n-face-320.onnx")
_LFW_ANH = [
    Path("data/impostor/lfw_original/Aaron_Peirsol/Aaron_Peirsol_0001.jpg"),
    Path("data/impostor/lfw_original/George_HW_Bush/George_HW_Bush_0001.jpg"),
    Path("data/impostor/lfw_original/Nelson_Mandela/Nelson_Mandela_0001.jpg"),
]


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


def _dung_thu_muc_ncnn(
    goc: Path,
    ten: str = "yolov8n-face-320_ncnn_model",
    co_tep: tuple[str, ...] = ("model.ncnn.param", "model.ncnn.bin", "metadata.yaml"),
    imgsz: object = (320, 320),
) -> Path:
    """Dựng thư mục NCNN giả trong `goc`; `metadata.yaml` mang khoá `imgsz` đã cho."""
    thu_muc = goc / ten
    thu_muc.mkdir(parents=True, exist_ok=True)
    for tep in co_tep:
        if tep == "metadata.yaml":
            if imgsz is None:
                (thu_muc / tep).write_text("task: pose\n", encoding="utf-8")
            else:
                dong = ", ".join(repr(x) for x in imgsz)
                (thu_muc / tep).write_text(f"imgsz: [{dong}]\n", encoding="utf-8")
        else:
            (thu_muc / tep).write_bytes(b"noi-dung-gia")
    return thu_muc


class _FakeExtractor:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def input(self, *args):
        pass

    def extract(self, ten):
        return 0, np.zeros((20, 2100), dtype=np.float32)


class _FakeNet:
    def __init__(self):
        self.opt = types.SimpleNamespace(num_threads=0)

    def load_param(self, duong_dan):
        pass

    def load_model(self, duong_dan):
        pass

    def create_extractor(self):
        return _FakeExtractor()

    def clear(self):
        pass


@pytest.fixture
def ncnn_gia(monkeypatch):
    """Cắm một module `ncnn` giả vào `sys.modules` để `__init__` chạy không cần gói thật."""
    mod = types.ModuleType("ncnn")
    mod.Net = _FakeNet
    mod.Mat = lambda arr: types.SimpleNamespace(clone=lambda: arr)
    monkeypatch.setitem(sys.modules, "ncnn", mod)
    return mod


# ============================================================================
# §7.2 — Khởi tạo và validate (dòng 10-19)
# ============================================================================


def test_dong10_thu_muc_khong_ton_tai_nem_loimohinh(tmp_path):
    with pytest.raises(LoiMoHinh):
        NcnnFaceDetector(tmp_path / "khong-co", _cfg_hop_le())


def test_dong11_thieu_param_nem_loimohinh_neu_ten_tep(tmp_path):
    d = _dung_thu_muc_ncnn(tmp_path, co_tep=("model.ncnn.bin", "metadata.yaml"))
    with pytest.raises(LoiMoHinh, match="param"):
        NcnnFaceDetector(d, _cfg_hop_le())


def test_dong12_thieu_bin_nem_loimohinh_neu_ten_tep(tmp_path):
    d = _dung_thu_muc_ncnn(tmp_path, co_tep=("model.ncnn.param", "metadata.yaml"))
    with pytest.raises(LoiMoHinh, match="bin"):
        NcnnFaceDetector(d, _cfg_hop_le())


def test_dong13_thieu_metadata_nem_loimohinh(tmp_path):
    d = _dung_thu_muc_ncnn(tmp_path, co_tep=("model.ncnn.param", "model.ncnn.bin"))
    with pytest.raises(LoiMoHinh, match="metadata"):
        NcnnFaceDetector(d, _cfg_hop_le())


def test_dong14_metadata_thieu_khoa_imgsz_nem_loimohinh(tmp_path):
    d = _dung_thu_muc_ncnn(tmp_path, imgsz=None)
    with pytest.raises(LoiMoHinh, match="imgsz"):
        NcnnFaceDetector(d, _cfg_hop_le())


def test_dong15_imgsz_khong_phai_so_nguyen_duong_nem_loimohinh(tmp_path):
    for xau in [(0, 0), ("a", "a")]:
        d = _dung_thu_muc_ncnn(tmp_path, ten=f"m_{xau[0]}_ncnn_model", imgsz=xau)
        with pytest.raises(LoiMoHinh):
            NcnnFaceDetector(d, _cfg_hop_le())


def test_dong16_imgsz_hai_phan_tu_khac_nhau_nem_loimohinh(tmp_path):
    d = _dung_thu_muc_ncnn(tmp_path, imgsz=(320, 640))
    with pytest.raises(LoiMoHinh):
        NcnnFaceDetector(d, _cfg_hop_le())


def test_dong17_kich_thuoc_vao_doc_tu_metadata_khong_tu_ten_thu_muc(tmp_path, ncnn_gia):
    d = _dung_thu_muc_ncnn(tmp_path, ten="mo-hinh-999_ncnn_model", imgsz=(320, 320))
    det = NcnnFaceDetector(d, _cfg_hop_le())
    assert det.kich_thuoc_vao == 320


def test_dong18_ten_backend_la_ncnn(tmp_path, ncnn_gia):
    d = _dung_thu_muc_ncnn(tmp_path)
    det = NcnnFaceDetector(d, _cfg_hop_le())
    assert det.ten_backend == "ncnn"


def test_dong19_num_threads_ngoai_mien_nem_loicauhinh(tmp_path):
    d = _dung_thu_muc_ncnn(tmp_path)
    for gia_tri in (-1, 999):
        cfg = _cfg_hop_le()
        cfg["inference"]["num_threads"] = gia_tri
        with pytest.raises(LoiCauHinh):
            NcnnFaceDetector(d, cfg)


def test_dong20_detect_dau_vao_sai_nem_valueerror(tmp_path, ncnn_gia):
    d = _dung_thu_muc_ncnn(tmp_path)
    det = NcnnFaceDetector(d, _cfg_hop_le())
    with pytest.raises(ValueError):
        det.detect("khong-phai-mang")
    with pytest.raises(ValueError):
        det.detect(np.zeros((10, 10), dtype=np.uint8))
    with pytest.raises(ValueError):
        det.detect(np.zeros((0, 0, 3), dtype=np.uint8))


# ============================================================================
# §7.2 — Chạy mô hình thật (dòng 21-22) — cần gói `ncnn` + thư mục NCNN thật
# ============================================================================


@pytest.mark.slow
def test_dong21_nap_mo_hinh_that_va_chay_tren_anh_lfw():
    pytest.importorskip("ncnn")
    _bo_qua_neu_thieu(_NCNN_320)
    _bo_qua_neu_thieu(_LFW_ANH[0])
    import cv2

    det = NcnnFaceDetector(_NCNN_320, _cfg_hop_le())
    anh = cv2.imread(str(_LFW_ANH[0]))
    assert anh is not None

    kq = det.detect(anh)
    assert isinstance(kq, list)
    assert kq and all(hasattr(f, "confidence") for f in kq)


# Dung sai giữa hai backend, tính bằng PIXEL trên từng cạnh và từng toạ độ điểm mốc.
# KHÔNG dùng ngưỡng IoU: IoU phụ thuộc kích thước khuôn mặt trong ảnh nên đo sai thứ cần đo
# (xem docs/dac-ta/P2-05-detector-ncnn.md §6.4). 2 px là biên an toàn cho việc round() toạ độ
# về int lệch một đơn vị giữa host x86 và container ARM64; lỗi thật lệch hàng chục px.
_DUNG_SAI_PX = 2.0
_TEN_CANH = ("x1", "y1", "x2", "y2")


@pytest.mark.slow
def test_dong22_hai_backend_cho_cung_ket_qua_tren_cung_anh():
    # dòng 22b — importorskip để ca SKIP (không đỏ) ở nơi thiếu gói ncnn.
    pytest.importorskip("ncnn")
    _bo_qua_neu_thieu(_NCNN_320)
    _bo_qua_neu_thieu(_ONNX_320)
    for p in _LFW_ANH:
        _bo_qua_neu_thieu(p)
    import cv2

    d_ncnn = NcnnFaceDetector(_NCNN_320, _cfg_hop_le())
    d_onnx = YoloFaceDetector(_ONNX_320, _cfg_hop_le())

    for p in _LFW_ANH:
        anh = cv2.imread(str(p))
        assert anh is not None
        kq_n = d_ncnn.detect(anh)
        kq_o = d_onnx.detect(anh)

        assert len(kq_n) == len(kq_o), f"{p.name}: lệch số mặt — NCNN {len(kq_n)}, ONNX {len(kq_o)}"

        for idx, (fn, fo) in enumerate(zip(kq_n, kq_o)):
            for ten, gn, go in zip(
                _TEN_CANH,
                (fn.x1, fn.y1, fn.x2, fn.y2),
                (fo.x1, fo.y1, fo.x2, fo.y2),
            ):
                lech = abs(gn - go)
                assert lech <= _DUNG_SAI_PX, (
                    f"{p.name} mặt #{idx}: cạnh {ten} lệch {lech} px "
                    f"(NCNN {gn}, ONNX {go}); dung sai {_DUNG_SAI_PX:g} px"
                )

            lm_n = np.asarray(fn.landmarks, dtype=np.float64)
            lm_o = np.asarray(fo.landmarks, dtype=np.float64)
            for k in range(lm_n.shape[0]):
                for truc, j in (("x", 0), ("y", 1)):
                    lech = abs(float(lm_n[k, j] - lm_o[k, j]))
                    assert lech <= _DUNG_SAI_PX, (
                        f"{p.name} mặt #{idx}: điểm mốc {k} toạ độ {truc} lệch "
                        f"{lech:.3f} px (NCNN {lm_n[k, j]:.3f}, ONNX {lm_o[k, j]:.3f}); "
                        f"dung sai {_DUNG_SAI_PX:g} px"
                    )
