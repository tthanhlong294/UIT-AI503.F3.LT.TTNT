"""Kiểm thử cho src/recognizer/dlib_backend.py (mã việc P3-02).

Ràng buộc thu thập (§7 đặc tả): `pytest --collect-only -m "not slow"` phải chạy trót lọt kể cả
khi máy CHƯA cài gói `dlib`. Vì vậy `dlib` không bao giờ được import ở mức module tệp này.

Bốn nhóm ca, phân theo mức phụ thuộc:

- §7.1 dòng 01–06: chỉ chạm phần đọc cấu hình và phần kiểm gói/tệp — không cần trọng số thật.
  Dòng 01 giả lập "chưa cài dlib" bằng cách cắm `None` vào `sys.modules`. Dòng 02–03 cần gói
  `dlib` thật (`importorskip`) vì phép kiểm tệp nằm SAU phép kiểm gói trong `__init__`.
- §7.1 dòng 07–08 và §7.2 dòng 13–16: cần cả hai tệp trọng số thật, đánh dấu `@pytest.mark.slow`.
  Container ARM64 không có thư mục `models/` nên các ca này tự BỎ QUA CÓ THÔNG BÁO ở đó.
- §7.2 dòng 09–12 và §7.3 dòng 17–22: dùng một `DlibFaceRecognizer` GIẢ dựng bằng
  `object.__new__` — bỏ qua `__init__`, không nạp mô hình. Các nhánh mã được kiểm ở đây (kiểm
  ảnh đầu vào, đếm số ảnh đăng ký, logic chọn điểm cao nhất trong `identify`) đều chạy TRƯỚC
  khi chạm tới mô hình, nên nhóm này chạy được ở mọi nơi.
- §7.4 dòng 23–25: tính thay thế được giữa hai backend. Dòng 24 so chữ ký bằng `inspect`, không
  cần mô hình; dòng 25 cần trọng số của CẢ HAI phương án nên đánh dấu `slow`.

⚠️ Dòng 16 là ca canh §6.1 và là ca phải đỏ khi bỏ bước đổi BGR sang RGB (phép đột biến ĐB1).
Xem giải trình ngay trong thân hàm vì sao chỉ so ảnh gốc với ảnh đảo kênh là KHÔNG đủ.
"""

import inspect
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.recognizer.arcface_backend import ArcFaceBackend
from src.recognizer.base import BoNhanDien, do_tuong_dong
from src.recognizer.dlib_backend import DlibFaceRecognizer

_MODEL_PATH = Path("models/dlib/dlib_face_recognition_resnet_model_v1.dat")
_SHAPE_PATH = Path("models/dlib/shape_predictor_68_face_landmarks.dat")
_ARCFACE_PATH = Path("models/mobilefacenet.onnx")
_LFW_DIR = Path("data/processed/lfw_original")

# Số chiều vectơ đặc trưng của mô hình ResNet dlib, ghi ở configs/recognize.yaml. Dùng ở dòng 08
# để đối chiếu với số chiều ĐỌC TỪ MÔ HÌNH, nên phải viết thành hằng số ở đây chứ không lấy lại
# từ chính cấu hình đang được kiểm.
_SO_CHIEU_DLIB = 128

# Số ảnh tối thiểu để đăng ký một người, khớp `enroll.min_images_per_user` của cấu hình.
_SO_ANH_TOI_THIEU = 10


def _cfg_hop_le() -> dict:
    """Cấu hình hợp lệ tối giản — khớp mục "dlib" và "enroll" của configs/recognize.yaml."""
    return {
        "dlib": {
            "model_path": str(_MODEL_PATH),
            "shape_predictor": str(_SHAPE_PATH),
            "embedding_dim": _SO_CHIEU_DLIB,
            "num_jitters": 0,
        },
        "enroll": {"min_images_per_user": _SO_ANH_TOI_THIEU},
    }


def _cfg_arcface() -> dict:
    """Cấu hình ArcFace hợp lệ — khớp mục "arcface" của configs/recognize.yaml."""
    return {
        "model_path": str(_ARCFACE_PATH),
        "embedding_dim": 512,
        "input_size": [112, 112],
        "channel_order": "rgb",
        "mean": 127.5,
        "scale": 128.0,
    }


def _bo_qua_neu_thieu(duong_dan: Path) -> None:
    if not duong_dan.exists():
        pytest.skip(f"chưa có {duong_dan}, xem models/README.md để tải mô hình")


def _bo_qua_neu_thieu_mo_hinh_dlib() -> None:
    pytest.importorskip("dlib")
    _bo_qua_neu_thieu(_MODEL_PATH)
    _bo_qua_neu_thieu(_SHAPE_PATH)


def _backend_gia() -> DlibFaceRecognizer:
    """Dựng một `DlibFaceRecognizer` GIẢ: bỏ qua `__init__`, không nạp mô hình nào.

    Dùng cho các ca chỉ chạm những nhánh mã chạy TRƯỚC khi cần tới mô hình — kiểm ảnh đầu vào,
    đếm số ảnh đăng ký, và nhánh gallery rỗng của `identify`.
    """
    return object.__new__(DlibFaceRecognizer)


def _backend_gia_tra_san(vectors_theo_thu_tu_goi: list[np.ndarray]) -> DlibFaceRecognizer:
    """Như `_backend_gia()`, nhưng `trich_dac_trung` trả sẵn các vectơ đã biết trước.

    Dùng để kiểm logic quyết định của `identify()` tách biệt khỏi suy luận thật.
    """
    backend = _backend_gia()
    trang_thai = {"i": 0}

    def _tra_vector_gia(_anh: np.ndarray) -> np.ndarray:
        v = vectors_theo_thu_tu_goi[trang_thai["i"]]
        trang_thai["i"] += 1
        return v

    backend.trich_dac_trung = _tra_vector_gia
    return backend


def _anh_bgr_ngau_nhien(so_luong: int) -> list[np.ndarray]:
    """Danh sách ảnh BGR uint8 sinh ngẫu nhiên có seed cố định, dùng cho ca đăng ký."""
    rng = np.random.default_rng(42)
    return [rng.integers(0, 256, size=(112, 112, 3), dtype=np.uint8) for _ in range(so_luong)]


@pytest.fixture(scope="module")
def cap_anh_cung_nguoi() -> list[Path]:
    """Hai ảnh LFW đã tiền xử lý của CÙNG một danh tính."""
    if not _LFW_DIR.exists():
        pytest.skip(f"chưa có {_LFW_DIR}, chạy scripts/preprocess.py trước")

    for thu_muc in sorted(p for p in _LFW_DIR.iterdir() if p.is_dir()):
        anh = sorted(thu_muc.glob("*.png"))
        if len(anh) >= 2:
            return anh[:2]

    pytest.skip(f"không có danh tính nào đủ 2 ảnh trong {_LFW_DIR}")


@pytest.fixture(scope="module")
def backend_that() -> DlibFaceRecognizer:
    _bo_qua_neu_thieu_mo_hinh_dlib()
    return DlibFaceRecognizer(_cfg_hop_le())


# ============================================================================
# §7.1 — Khởi tạo và cấu hình (dòng 01-08)
# ============================================================================


def test_dong01_thieu_goi_dlib_nem_loimohinh_neu_lenh_cai(monkeypatch):
    # Cắm None vào sys.modules làm `import dlib` ném ImportError kể cả khi máy đã cài gói.
    monkeypatch.setitem(sys.modules, "dlib", None)
    with pytest.raises(LoiMoHinh, match="dlib-bin"):
        DlibFaceRecognizer(_cfg_hop_le())


def test_dong02_tep_trong_so_khong_ton_tai_nem_loimohinh_neu_ten_tep():
    pytest.importorskip("dlib")
    cfg = _cfg_hop_le()
    cfg["dlib"]["model_path"] = "models/dlib/khong-co-tep-nay.dat"
    with pytest.raises(LoiMoHinh, match="khong-co-tep-nay"):
        DlibFaceRecognizer(cfg)


def test_dong03_tep_diem_moc_khong_ton_tai_nem_loimohinh_neu_ten_tep():
    pytest.importorskip("dlib")
    # Cần tệp trọng số THẬT: phép kiểm nó nằm trước phép kiểm bộ dò điểm mốc trong __init__,
    # nên thiếu cả hai thì thông báo lỗi sẽ nói về tệp trọng số chứ không phải tệp điểm mốc.
    _bo_qua_neu_thieu(_MODEL_PATH)
    cfg = _cfg_hop_le()
    cfg["dlib"]["shape_predictor"] = "models/dlib/khong-co-diem-moc.dat"
    with pytest.raises(LoiMoHinh, match="khong-co-diem-moc"):
        DlibFaceRecognizer(cfg)


def test_dong04_thieu_khoa_model_path_nem_loicauhinh():
    cfg = _cfg_hop_le()
    del cfg["dlib"]["model_path"]
    with pytest.raises(LoiCauHinh, match="dlib.model_path"):
        DlibFaceRecognizer(cfg)


def test_dong05_num_jitters_am_nem_loicauhinh():
    cfg = _cfg_hop_le()
    cfg["dlib"]["num_jitters"] = -1
    with pytest.raises(LoiCauHinh, match="num_jitters"):
        DlibFaceRecognizer(cfg)


def test_dong06_num_jitters_khong_phai_so_nguyen_nem_loicauhinh():
    for gia_tri in ("nhiều", 1.5, True):
        cfg = _cfg_hop_le()
        cfg["dlib"]["num_jitters"] = gia_tri
        with pytest.raises(LoiCauHinh, match="num_jitters"):
            DlibFaceRecognizer(cfg)


@pytest.mark.slow
def test_dong07_embedding_dim_lech_so_chieu_that_nem_loimohinh():
    _bo_qua_neu_thieu_mo_hinh_dlib()
    cfg = _cfg_hop_le()
    cfg["dlib"]["embedding_dim"] = 512
    with pytest.raises(LoiMoHinh, match="embedding_dim"):
        DlibFaceRecognizer(cfg)


@pytest.mark.slow
def test_dong08_so_chieu_doc_tu_mo_hinh_khong_tu_cau_hinh(backend_that: DlibFaceRecognizer):
    assert backend_that.so_chieu == _SO_CHIEU_DLIB


# ============================================================================
# §7.2 — Trích đặc trưng (dòng 09-16)
# ============================================================================


def test_dong09_anh_sai_kieu_nem_valueerror():
    with pytest.raises(ValueError, match="ndarray"):
        _backend_gia().trich_dac_trung([[1, 2, 3]])


def test_dong10_anh_sai_hinh_dang_nem_valueerror():
    with pytest.raises(ValueError, match="hình dạng"):
        _backend_gia().trich_dac_trung(np.zeros((112, 112), dtype=np.uint8))


def test_dong11_anh_sai_dtype_nem_valueerror():
    with pytest.raises(ValueError, match="uint8"):
        _backend_gia().trich_dac_trung(np.zeros((112, 112, 3), dtype=np.float32))


def test_dong12_anh_rong_nem_valueerror():
    with pytest.raises(ValueError, match="rỗng"):
        _backend_gia().trich_dac_trung(np.zeros((0, 0, 3), dtype=np.uint8))


@pytest.mark.slow
def test_dong13_anh_hop_le_cho_vecto_dung_hinh_dang_va_kieu(
    backend_that: DlibFaceRecognizer, cap_anh_cung_nguoi: list[Path]
):
    anh = cv2.imread(str(cap_anh_cung_nguoi[0]))
    assert anh is not None

    vec = backend_that.trich_dac_trung(anh)

    assert vec.shape == (_SO_CHIEU_DLIB,)
    assert vec.dtype == np.float32


@pytest.mark.slow
def test_dong14_vecto_da_chuan_hoa_l2(
    backend_that: DlibFaceRecognizer, cap_anh_cung_nguoi: list[Path]
):
    anh = cv2.imread(str(cap_anh_cung_nguoi[0]))
    vec = backend_that.trich_dac_trung(anh)
    assert abs(float(np.linalg.norm(vec)) - 1.0) < 1e-5


@pytest.mark.slow
def test_dong15_cung_anh_cho_cung_vecto(
    backend_that: DlibFaceRecognizer, cap_anh_cung_nguoi: list[Path]
):
    anh = cv2.imread(str(cap_anh_cung_nguoi[0]))
    assert np.allclose(backend_that.trich_dac_trung(anh), backend_that.trich_dac_trung(anh))


@pytest.mark.slow
def test_dong16_doi_kenh_mau_lam_doi_ket_qua(
    backend_that: DlibFaceRecognizer, cap_anh_cung_nguoi: list[Path]
):
    """Ca canh §6.1 — phải đỏ khi bỏ bước đổi BGR sang RGB (ĐB1).

    So vectơ của ảnh gốc với vectơ của ảnh đã đảo kênh là KHÔNG đủ để bắt ĐB1: vectơ 128-D của
    dlib gần như bất biến với phép hoán đổi kênh R↔B trên ảnh khuôn mặt (độ tương đồng đo được
    ~0,9955), nên không ngưỡng đơn nào vừa chấp nhận "cùng ảnh" vừa bác "đã đảo kênh" — phép so
    đối xứng đó bỏ `cvtColor` chỉ hoán vai trò hai đầu vào, cho ra đúng cùng một con số.

    Ca này neo vào một MỐC TUYỆT ĐỐI thay vì một ngưỡng tương đồng: vectơ tham chiếu tính trên
    ảnh RGB do chính `dlib.load_rgb_image` nạp — bộ nạp riêng của dlib, luôn trả về RGB — dựng
    ĐỘC LẬP với `trich_dac_trung`, dùng đúng cùng tham số mà mã sản phẩm dùng
    (`dlib.rectangle(0, 0, rong, cao)`, `num_jitters = 0`). Khi mã đúng, backend nhận ảnh BGR từ
    `cv2.imread` rồi tự đổi sang RGB nội bộ nên phải tính ra ĐÚNG CÙNG một vectơ (sai số chỉ ở
    mức dấu phẩy động) với mốc tham chiếu; bỏ `cvtColor` thì backend chạy trên ảnh vẫn ở hệ BGR,
    tụt xuống độ tương đồng ~0,9955 với mốc và bị `np.allclose` bắt ngay.
    """
    import dlib

    duong_dan = cap_anh_cung_nguoi[0]
    anh_bgr = cv2.imread(str(duong_dan))
    assert anh_bgr is not None

    anh_rgb = dlib.load_rgb_image(str(duong_dan))
    bo_do_diem_moc = dlib.shape_predictor(str(_SHAPE_PATH))
    mo_hinh = dlib.face_recognition_model_v1(str(_MODEL_PATH))
    cao, rong = anh_rgb.shape[:2]
    diem_moc = bo_do_diem_moc(anh_rgb, dlib.rectangle(0, 0, rong, cao))
    vec_tham_chieu = np.asarray(
        mo_hinh.compute_face_descriptor(anh_rgb, diem_moc, 0), dtype=np.float32
    )
    # Backend có chuẩn hoá L2, `compute_face_descriptor` thì không — chuẩn hoá mốc trước khi so.
    vec_tham_chieu = vec_tham_chieu / float(np.linalg.norm(vec_tham_chieu))

    vec_backend = backend_that.trich_dac_trung(anh_bgr)
    assert np.allclose(
        vec_backend, vec_tham_chieu, atol=1e-5
    ), "backend không khớp mốc RGB tham chiếu; dấu hiệu thiếu bước đổi BGR sang RGB"


# ============================================================================
# §7.3 — Đăng ký và so khớp (dòng 17-22)
# ============================================================================


def test_dong17_enroll_danh_sach_rong_nem_valueerror():
    with pytest.raises(ValueError, match="rỗng"):
        _backend_gia().enroll([], {"min_images_per_user": _SO_ANH_TOI_THIEU})


def test_dong18_enroll_thieu_anh_nem_valueerror_neu_so_anh():
    anh = _anh_bgr_ngau_nhien(3)
    with pytest.raises(ValueError, match=str(_SO_ANH_TOI_THIEU)):
        _backend_gia().enroll(anh, {"min_images_per_user": _SO_ANH_TOI_THIEU})


@pytest.mark.slow
def test_dong19_enroll_du_anh_cho_vecto_da_chuan_hoa(backend_that: DlibFaceRecognizer):
    vec = backend_that.enroll(
        _anh_bgr_ngau_nhien(_SO_ANH_TOI_THIEU),
        {"min_images_per_user": _SO_ANH_TOI_THIEU},
    )

    assert vec.shape == (_SO_CHIEU_DLIB,)
    assert vec.dtype == np.float32
    assert abs(float(np.linalg.norm(vec)) - 1.0) < 1e-5


def test_dong20_identify_gallery_rong_tra_none_va_0():
    anh = _anh_bgr_ngau_nhien(1)[0]
    assert _backend_gia().identify(anh, {}, 0.5) == (None, 0.0)


def test_dong21_identify_khong_ai_vuot_nguong_tra_none_kem_diem_cao_nhat():
    rng = np.random.default_rng(42)
    vec_truy_van = rng.normal(size=_SO_CHIEU_DLIB).astype(np.float32)
    gallery = {
        "nguoi_a": rng.normal(size=_SO_CHIEU_DLIB).astype(np.float32),
        "nguoi_b": rng.normal(size=_SO_CHIEU_DLIB).astype(np.float32),
    }
    diem_cao_nhat = max(do_tuong_dong(vec_truy_van, v) for v in gallery.values())

    backend = _backend_gia_tra_san([vec_truy_van])
    user_id, diem = backend.identify(_anh_bgr_ngau_nhien(1)[0], gallery, 0.99)

    assert user_id is None
    assert diem == pytest.approx(diem_cao_nhat, abs=1e-6)


def test_dong22_identify_co_nguoi_vuot_nguong_tra_dung_ma_nguoi():
    rng = np.random.default_rng(42)
    vec_truy_van = rng.normal(size=_SO_CHIEU_DLIB).astype(np.float32)
    gallery = {
        "nguoi_a": rng.normal(size=_SO_CHIEU_DLIB).astype(np.float32),
        "nguoi_b": vec_truy_van.copy(),
    }

    backend = _backend_gia_tra_san([vec_truy_van])
    user_id, diem = backend.identify(_anh_bgr_ngau_nhien(1)[0], gallery, 0.5)

    assert user_id == "nguoi_b"
    assert diem == pytest.approx(1.0, abs=1e-6)


# ============================================================================
# §7.4 — Hai backend thay thế được cho nhau (dòng 23-25)
# ============================================================================


def test_dong23_la_the_hien_cua_bonhandien():
    assert isinstance(_backend_gia(), BoNhanDien)


def test_dong24_ba_phuong_thuc_cung_chu_ky_voi_arcface():
    for ten in ("trich_dac_trung", "enroll", "identify"):
        chu_ky_dlib = inspect.signature(getattr(DlibFaceRecognizer, ten))
        chu_ky_arcface = inspect.signature(getattr(ArcFaceBackend, ten))

        assert list(chu_ky_dlib.parameters) == list(chu_ky_arcface.parameters), (
            f"phương thức {ten} lệch tên hoặc thứ tự tham số: "
            f"dlib {list(chu_ky_dlib.parameters)} / arcface {list(chu_ky_arcface.parameters)}"
        )
        assert chu_ky_dlib == chu_ky_arcface, f"phương thức {ten} lệch chú giải kiểu"


# Ngưỡng rất lỏng, chủ ý (§7.4 đặc tả): dòng 25 KHÔNG đo độ chính xác — đó là việc của Cổng C.
# Nó chỉ bắt trường hợp một backend hỏng hoàn toàn, ví dụ sai tiền xử lý khiến mọi cặp ảnh đều
# cho độ tương đồng gần bằng nhau.
_NGUONG_CUNG_NGUOI = 0.4


@pytest.mark.slow
def test_dong25_hai_backend_deu_nhan_ra_cung_mot_nguoi(cap_anh_cung_nguoi: list[Path]):
    _bo_qua_neu_thieu_mo_hinh_dlib()
    _bo_qua_neu_thieu(_ARCFACE_PATH)

    anh = [cv2.imread(str(p)) for p in cap_anh_cung_nguoi]
    assert all(a is not None for a in anh)

    cac_backend = {
        "dlib": DlibFaceRecognizer(_cfg_hop_le()),
        "arcface": ArcFaceBackend(_cfg_arcface()),
    }

    for ten, backend in cac_backend.items():
        v0 = backend.trich_dac_trung(anh[0])
        v1 = backend.trich_dac_trung(anh[1])
        diem = do_tuong_dong(v0, v1)
        assert diem > _NGUONG_CUNG_NGUOI, (
            f"backend {ten}: hai ảnh của cùng một người chỉ đạt độ tương đồng {diem:.4f}, "
            f"dưới ngưỡng lỏng {_NGUONG_CUNG_NGUOI}"
        )
