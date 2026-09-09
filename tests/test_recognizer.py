"""Kiểm thử cho src/recognizer/base.py và src/recognizer/arcface_backend.py.

Ba nhóm ca theo mức phụ thuộc:

- §6.1–§6.3 (dòng 01–26): phần lớn chỉ cần cấu hình/vectơ dựng tay. Các ca gọi thẳng
  `ArcFaceBackend(...)`/`trich_dac_trung(...)` với mô hình thật tự BỎ QUA CÓ THÔNG BÁO nếu
  `models/mobilefacenet.onnx` chưa có.
- §6.4 (dòng 27–28): cần dữ liệu LFW thật trong `data/processed/lfw_original/`, tự BỎ QUA CÓ
  THÔNG BÁO nếu thư mục chưa có — xem `_bo_qua_neu_thieu_lfw`.
- §6.5 (dòng 29–38, enroll/identify): dùng một `ArcFaceBackend` GIẢ — dựng bằng
  `object.__new__`, bỏ qua `__init__`, thay `trich_dac_trung` bằng hàm trả sẵn vectơ đã biết
  trước (xem `_backend_gia`). Mục đích của nhóm này là kiểm logic quyết định của
  `enroll()`/`identify()` (chuẩn hoá trước khi trung bình, chọn điểm cao nhất, ngưỡng...),
  tách biệt khỏi suy luận ONNX thật — suy luận đã được kiểm ở §6.2–§6.3. Nhờ vậy nhóm này
  không cần mô hình lẫn dữ liệu, chạy được cả trong container ARM64.
- §6.6–§6.9 (dòng 39–47, P3-01b): vá ba lỗ hổng G5/G6/G7 ghi ở
  `docs/dac-ta/P3-01b-chan-gia-tri-hong.md`. Dòng 39–43 chặn `mean`/`scale` không hữu hạn qua
  `ArcFaceBackend.__init__`/`chuan_bi_dau_vao`. Dòng 44–45 chặn `NaN` lan vào độ dài vectơ —
  dòng 44 dùng `_backend_gia_voi_session` (thay `_session` giả, GIỮ NGUYÊN `trich_dac_trung`
  thật) để chạm đúng nhánh mã cần kiểm, khác với `_backend_gia` vốn thay hẳn hàm đó. Dòng 46
  đối chiếu `input_size` với đồ thị ONNX, cần mô hình thật. Dòng 47 nạp
  `configs/recognize.yaml` THẬT — không cần mô hình, chạy được cả trong container ARM64.
"""

from pathlib import Path

import cv2
import numpy as np
import pytest

from src.common.config import lay_gia_tri, nap_cau_hinh
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.recognizer.arcface_backend import ArcFaceBackend, chuan_bi_dau_vao
from src.recognizer.base import do_tuong_dong

_MODEL_PATH = Path("models/mobilefacenet.onnx")
_LFW_DIR = Path("data/processed/lfw_original")


def _cfg_hop_le() -> dict:
    """Cấu hình ArcFace hợp lệ tối giản — khớp mục "arcface" của configs/recognize.yaml."""
    return {
        "model_path": str(_MODEL_PATH),
        "embedding_dim": 512,
        "input_size": [112, 112],
        "channel_order": "rgb",
        "mean": 127.5,
        "scale": 128.0,
    }


def _cfg_chuan_hoa_hop_le() -> dict:
    """Cấu hình chuẩn hoá tối giản dùng riêng cho các ca kiểm `chuan_bi_dau_vao`."""
    return {"channel_order": "rgb", "mean": 127.5, "scale": 128.0}


def _anh_bgr_10_20_30() -> np.ndarray:
    """Ảnh 112x112, mọi điểm ảnh bằng [10, 20, 30] theo thứ tự kênh BGR của OpenCV."""
    anh = np.zeros((112, 112, 3), dtype=np.uint8)
    anh[:, :, 0] = 10
    anh[:, :, 1] = 20
    anh[:, :, 2] = 30
    return anh


def _bo_qua_neu_thieu(duong_dan: Path) -> None:
    if not duong_dan.exists():
        pytest.skip(f"chưa có {duong_dan}, xem models/README.md để tải mô hình")


def _bo_qua_neu_thieu_lfw() -> None:
    if not _LFW_DIR.exists():
        pytest.skip(f"chưa có {_LFW_DIR}, chạy scripts/preprocess.py trước")


def _backend_gia(vectors_theo_thu_tu_goi: list[np.ndarray]) -> ArcFaceBackend:
    """Dựng một `ArcFaceBackend` GIẢ, không cần mô hình ONNX thật.

    `__init__` bị bỏ qua bằng `object.__new__`. `trich_dac_trung` được thay bằng một hàm trả
    lần lượt các vectơ trong `vectors_theo_thu_tu_goi` theo đúng thứ tự gọi — dùng để kiểm logic
    của `enroll()`/`identify()` độc lập với suy luận ONNX thật (xem docstring đầu module).
    """
    backend = object.__new__(ArcFaceBackend)
    trang_thai = {"i": 0}

    def _tra_vector_gia(_anh: np.ndarray) -> np.ndarray:
        v = vectors_theo_thu_tu_goi[trang_thai["i"]]
        trang_thai["i"] += 1
        return v

    backend.trich_dac_trung = _tra_vector_gia
    return backend


class _SessionGia:
    """Session ONNX GIẢ — `run()` trả sẵn một vectơ đặc trưng, không cần mô hình thật.

    Khác với `_backend_gia()` (thay hẳn `trich_dac_trung`), lớp này chỉ giả phần suy luận
    ONNX bên trong, để `trich_dac_trung()` THẬT vẫn chạy — cần thiết để kiểm chốt độ dài NaN
    (§6.7, dòng 44 của `docs/dac-ta/P3-01b-chan-gia-tri-hong.md`) đúng đoạn mã sản phẩm.
    """

    def __init__(self, vec: np.ndarray) -> None:
        self._vec = vec

    def run(self, _ten_dau_ra: object, _dau_vao: object) -> list[np.ndarray]:
        return [np.array([self._vec], dtype=np.float32)]


def _backend_gia_voi_session(vec_dau_ra: np.ndarray) -> ArcFaceBackend:
    """Dựng `ArcFaceBackend` GIẢ với `_session` giả — `trich_dac_trung()` thật vẫn chạy."""
    backend = object.__new__(ArcFaceBackend)
    backend._session = _SessionGia(vec_dau_ra)
    backend._ten_dau_vao = "input"
    backend._kich_thuoc_vao = (112, 112)
    backend._cfg_chuan_hoa = {"channel_order": "rgb", "mean": 127.5, "scale": 128.0}
    return backend


@pytest.fixture(scope="module")
def backend_that() -> ArcFaceBackend:
    _bo_qua_neu_thieu(_MODEL_PATH)
    return ArcFaceBackend(_cfg_hop_le())


@pytest.fixture(scope="module")
def embeddings_lfw(backend_that: ArcFaceBackend) -> dict[str, list[np.ndarray]]:
    """Embedding của tối thiểu 10 danh tính LFW có ≥2 ảnh (tối đa 20 danh tính, 2 ảnh/người)."""
    _bo_qua_neu_thieu_lfw()
    thu_muc_con = sorted(p for p in _LFW_DIR.iterdir() if p.is_dir())

    ket_qua: dict[str, list[np.ndarray]] = {}
    for tm in thu_muc_con:
        anh_files = sorted(tm.glob("*.png"))
        if len(anh_files) < 2:
            continue
        vecs = []
        for f in anh_files[:2]:
            anh = cv2.imread(str(f))
            assert anh is not None
            vecs.append(backend_that.trich_dac_trung(anh))
        ket_qua[tm.name] = vecs
        if len(ket_qua) >= 20:
            break

    if len(ket_qua) < 10:
        pytest.skip(f"không đủ 10 danh tính có ≥2 ảnh trong {_LFW_DIR} (chỉ có {len(ket_qua)})")
    return ket_qua


# ============================================================================
# §6.1 — Cấu hình và khởi tạo (dòng 01-08)
# ============================================================================


def test_dong01_nap_cau_hinh_hop_le_thanh_cong():
    _bo_qua_neu_thieu(_MODEL_PATH)
    ArcFaceBackend(_cfg_hop_le())  # không ném lỗi


def test_dong02_so_chieu_doc_tu_onnx_bang_512(backend_that: ArcFaceBackend):
    assert backend_that.so_chieu == 512


def test_dong03_tep_khong_ton_tai_nem_loimohinh():
    cfg = _cfg_hop_le()
    cfg["model_path"] = "khong/ton/tai.onnx"
    with pytest.raises(LoiMoHinh):
        ArcFaceBackend(cfg)


def test_dong04_tep_khong_phai_onnx_nem_loimohinh(tmp_path):
    tep_rac = tmp_path / "x.onnx"
    tep_rac.write_bytes(b"day khong phai onnx that")
    cfg = _cfg_hop_le()
    cfg["model_path"] = str(tep_rac)
    with pytest.raises(LoiMoHinh):
        ArcFaceBackend(cfg)


def test_dong05_embedding_dim_lech_nem_loicauhinh_neu_ca_hai_so():
    _bo_qua_neu_thieu(_MODEL_PATH)
    cfg = _cfg_hop_le()
    cfg["embedding_dim"] = 128
    with pytest.raises(LoiCauHinh) as exc_info:
        ArcFaceBackend(cfg)
    thong_bao = str(exc_info.value)
    assert "128" in thong_bao
    assert "512" in thong_bao


def test_dong06_thieu_key_bat_buoc_nem_loi():
    for khoa in ("model_path", "embedding_dim", "input_size", "channel_order", "mean", "scale"):
        cfg = _cfg_hop_le()
        del cfg[khoa]
        with pytest.raises(LoiCauHinh, match=khoa):
            ArcFaceBackend(cfg)


def test_dong07_gia_tri_ngoai_mien_nem_loicauhinh():
    bien_the = [
        ("channel_order", "xyz"),
        ("scale", 0),
        ("scale", -1),
        ("mean", "abc"),
        ("input_size", [112]),
    ]
    for khoa, gia_tri in bien_the:
        cfg = _cfg_hop_le()
        cfg[khoa] = gia_tri
        with pytest.raises(LoiCauHinh):
            ArcFaceBackend(cfg)


def test_dong08_moi_loi_cau_hinh_la_loicauhinh_khong_valueerror_typeerror():
    bien_the = [
        ("model_path", ""),
        ("model_path", 123),
        ("embedding_dim", -1),
        ("embedding_dim", "512"),
        ("input_size", [112]),
        ("input_size", "112,112"),
        ("channel_order", "xyz"),
        ("channel_order", 5),
        ("mean", "abc"),
        ("mean", None),
        ("scale", 0),
        ("scale", -1),
    ]
    for khoa, gia_tri in bien_the:
        cfg = _cfg_hop_le()
        cfg[khoa] = gia_tri
        with pytest.raises(LoiCauHinh) as exc_info:
            ArcFaceBackend(cfg)
        assert not isinstance(exc_info.value, (ValueError, TypeError))


# ============================================================================
# §6.2 — chuan_bi_dau_vao: kiểm trực tiếp chuẩn hoá (dòng 09-16)
# ============================================================================


def test_dong09_hinh_dang_ra_dung():
    anh = np.zeros((112, 112, 3), dtype=np.uint8)
    ra = chuan_bi_dau_vao(anh, _cfg_chuan_hoa_hop_le())
    assert ra.shape == (1, 3, 112, 112)


def test_dong10_kieu_ra_la_float32():
    anh = np.zeros((112, 112, 3), dtype=np.uint8)
    ra = chuan_bi_dau_vao(anh, _cfg_chuan_hoa_hop_le())
    assert ra.dtype == np.float32


def test_dong11_dao_kenh_bgr_sang_rgb():
    """Ca chặn lỗi thứ tự kênh — xem §4.2 của đặc tả. do_tuong_dong KHÔNG bắt được lỗi này."""
    anh = _anh_bgr_10_20_30()
    cfg = _cfg_chuan_hoa_hop_le()
    ra = chuan_bi_dau_vao(anh, cfg)

    ky_vong_30 = (30 - cfg["mean"]) / cfg["scale"]
    ky_vong_10 = (10 - cfg["mean"]) / cfg["scale"]
    assert ra[0, 0, 0, 0] == pytest.approx(ky_vong_30)  # kênh 0 (R) ứng với giá trị B gốc = 30...
    assert ra[0, 2, 0, 0] == pytest.approx(ky_vong_10)  # kênh 2 (B) ứng với giá trị B gốc = 10


def test_dong12_cong_thuc_chuan_hoa_dung():
    anh = _anh_bgr_10_20_30()
    cfg = _cfg_chuan_hoa_hop_le()
    ra = chuan_bi_dau_vao(anh, cfg)
    assert ra[0, 0, 0, 0] == pytest.approx((30 - 127.5) / 128)


def test_dong13_tham_so_khong_bi_viet_cung():
    anh = _anh_bgr_10_20_30()
    ra_scale_goc = chuan_bi_dau_vao(anh, _cfg_chuan_hoa_hop_le())

    cfg_scale_moi = _cfg_chuan_hoa_hop_le()
    cfg_scale_moi["scale"] = 64.0
    ra_scale_moi = chuan_bi_dau_vao(anh, cfg_scale_moi)

    assert ra_scale_moi[0, 0, 0, 0] == pytest.approx(ra_scale_goc[0, 0, 0, 0] * 2)


def test_dong14_channel_order_bgr_khong_dao():
    anh = _anh_bgr_10_20_30()
    cfg = _cfg_chuan_hoa_hop_le()
    cfg["channel_order"] = "bgr"
    ra = chuan_bi_dau_vao(anh, cfg)
    assert ra[0, 0, 0, 0] == pytest.approx((10 - cfg["mean"]) / cfg["scale"])


def test_dong15_anh_sai_hinh_dang_nem_valueerror():
    anh = np.zeros((112, 112), dtype=np.uint8)
    with pytest.raises(ValueError):
        chuan_bi_dau_vao(anh, _cfg_chuan_hoa_hop_le())


def test_dong16_anh_sai_kieu_nem_valueerror():
    anh = np.zeros((112, 112, 3), dtype=np.float32)
    with pytest.raises(ValueError):
        chuan_bi_dau_vao(anh, _cfg_chuan_hoa_hop_le())


# ============================================================================
# §6.3 — trich_dac_trung và do_tuong_dong (dòng 17-26)
# ============================================================================


def test_dong17_trich_dac_trung_hinh_dang_va_kieu_dung(backend_that: ArcFaceBackend):
    anh = np.zeros((112, 112, 3), dtype=np.uint8)
    vec = backend_that.trich_dac_trung(anh)
    assert vec.shape == (512,)
    assert vec.dtype == np.float32


def test_dong18_vector_da_chuan_hoa_l2(backend_that: ArcFaceBackend):
    anh = np.zeros((112, 112, 3), dtype=np.uint8)
    vec = backend_that.trich_dac_trung(anh)
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-5


def test_dong19_cung_anh_cho_cung_vector(backend_that: ArcFaceBackend):
    anh = np.zeros((112, 112, 3), dtype=np.uint8)
    v1 = backend_that.trich_dac_trung(anh)
    v2 = backend_that.trich_dac_trung(anh)
    assert np.allclose(v1, v2)


def test_dong20_anh_sai_hinh_dang_nem_valueerror(backend_that: ArcFaceBackend):
    anh = np.zeros((64, 64, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        backend_that.trich_dac_trung(anh)


def test_dong21_anh_rong_nem_valueerror(backend_that: ArcFaceBackend):
    anh = np.zeros((0, 0, 3), dtype=np.uint8)
    with pytest.raises(ValueError):
        backend_that.trich_dac_trung(anh)


def test_dong22_do_tuong_dong_chinh_no_bang_1():
    v = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert do_tuong_dong(v, v) == pytest.approx(1.0, abs=1e-6)


def test_dong23_hai_vector_vuong_goc_bang_0():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert do_tuong_dong(a, b) == pytest.approx(0.0, abs=1e-6)


def test_dong24_hai_vector_nguoc_huong_bang_am1():
    a = np.array([1.0, 0.0])
    b = np.array([-1.0, 0.0])
    assert do_tuong_dong(a, b) == pytest.approx(-1.0, abs=1e-6)


def test_dong25_khac_so_chieu_nem_valueerror():
    a = np.zeros(512, dtype=np.float32)
    b = np.zeros(128, dtype=np.float32)
    with pytest.raises(ValueError):
        do_tuong_dong(a, b)


def test_dong26_vector_do_dai_0_nem_valueerror_khong_chia_cho_0():
    a = np.zeros(512, dtype=np.float32)
    b = np.ones(512, dtype=np.float32)
    with pytest.raises(ValueError):
        do_tuong_dong(a, b)


# ============================================================================
# §6.4 — Năng lực phân biệt trên dữ liệu thật (dòng 27-28) — nhóm quan trọng nhất
# ============================================================================


def test_dong27_cung_nguoi_giong_hon_khac_nguoi(embeddings_lfw: dict[str, list[np.ndarray]]):
    """Mốc đo được ở §4.2 của đặc tả: cùng người 0,6088 / khác người 0,0079 / hiệu 0,6010."""
    danh_tinh = list(embeddings_lfw.keys())

    cung_nguoi = [do_tuong_dong(*embeddings_lfw[ten]) for ten in danh_tinh]

    khac_nguoi = []
    for i in range(len(danh_tinh)):
        for j in range(i + 1, len(danh_tinh)):
            v_i = embeddings_lfw[danh_tinh[i]][0]
            v_j = embeddings_lfw[danh_tinh[j]][0]
            khac_nguoi.append(do_tuong_dong(v_i, v_j))

    tb_cung_nguoi = float(np.mean(cung_nguoi))
    tb_khac_nguoi = float(np.mean(khac_nguoi))

    assert tb_cung_nguoi > 0.40
    assert tb_khac_nguoi < 0.20
    assert (tb_cung_nguoi - tb_khac_nguoi) > 0.30


def test_dong28_anh_cung_nguoi_luon_xep_tren(embeddings_lfw: dict[str, list[np.ndarray]]):
    danh_tinh = list(embeddings_lfw.keys())

    so_dat = 0
    for i, ten in enumerate(danh_tinh):
        v0, v1 = embeddings_lfw[ten]
        diem_cung_nguoi = do_tuong_dong(v0, v1)

        diem_khac_nguoi = [
            do_tuong_dong(v0, v_khac)
            for j, ten_khac in enumerate(danh_tinh)
            if j != i
            for v_khac in embeddings_lfw[ten_khac]
        ]
        if diem_cung_nguoi > max(diem_khac_nguoi):
            so_dat += 1

    ti_le = so_dat / len(danh_tinh)
    assert ti_le > 0.90


# ============================================================================
# §6.5 — enroll và identify, dùng ArcFaceBackend GIẢ (dòng 29-38)
# ============================================================================


def test_dong29_vector_dang_ky_da_chuan_hoa_l2():
    vecs = [np.arange(8, dtype=np.float32) + i + 1 for i in range(10)]
    backend = _backend_gia(vecs)
    ket_qua = backend.enroll(
        [np.zeros((1, 1, 3), dtype=np.uint8)] * 10, {"min_images_per_user": 10}
    )
    assert abs(np.linalg.norm(ket_qua) - 1.0) < 1e-5


def test_dong30_chuan_hoa_tung_vector_truoc_khi_trung_binh():
    """Ca chặn lỗi ĐB4 — xem §7 của đặc tả.

    Hai vectơ giả CÓ HƯỚNG KHÁC NHAU (trục x và trục y) nhưng độ dài khác nhau (1 và 100).
    Nếu enroll() chuẩn hoá TỪNG vectơ trước khi trung bình (đúng): kết quả nằm đúng giữa hai
    hướng — hai thành phần bằng nhau. Nếu trung bình thô rồi mới chuẩn hoá một lần (ĐB4, sai):
    vectơ dài lấn át, kết quả lệch hẳn về hướng của nó.
    """
    vecs_gia = [
        np.array([1.0, 0.0], dtype=np.float32),
        np.array([0.0, 100.0], dtype=np.float32),
    ]
    backend = _backend_gia(vecs_gia)

    ket_qua = backend.enroll(
        [np.zeros((1, 1, 3), dtype=np.uint8), np.zeros((1, 1, 3), dtype=np.uint8)],
        {"min_images_per_user": 2},
    )

    assert ket_qua[0] == pytest.approx(ket_qua[1], abs=1e-4)
    assert np.linalg.norm(ket_qua) == pytest.approx(1.0, abs=1e-5)


def test_dong31_danh_sach_rong_nem_valueerror():
    backend = _backend_gia([])
    with pytest.raises(ValueError):
        backend.enroll([], {"min_images_per_user": 10})


def test_dong32_it_hon_so_toi_thieu_nem_loi_neu_ca_hai_so():
    backend = _backend_gia([np.array([1.0, 0.0], dtype=np.float32)] * 3)
    with pytest.raises(ValueError) as exc_info:
        backend.enroll([np.zeros((1, 1, 3), dtype=np.uint8)] * 3, {"min_images_per_user": 10})
    thong_bao = str(exc_info.value)
    assert "3" in thong_bao
    assert "10" in thong_bao


def test_dong33_du_so_anh_thanh_cong():
    backend = _backend_gia([np.array([1.0, 0.0], dtype=np.float32)] * 10)
    ket_qua = backend.enroll(
        [np.zeros((1, 1, 3), dtype=np.uint8)] * 10, {"min_images_per_user": 10}
    )
    assert ket_qua.shape == (2,)
    assert abs(np.linalg.norm(ket_qua) - 1.0) < 1e-5


def test_dong34_identify_tra_dung_nguoi_khi_vuot_nguong():
    vec_truy_van = np.array([1.0, 0.0], dtype=np.float32)
    backend = _backend_gia([vec_truy_van])
    gallery = {
        "nguoi_a": np.array([1.0, 0.0], dtype=np.float32),
        "nguoi_b": np.array([0.0, 1.0], dtype=np.float32),
    }

    ma, _diem = backend.identify(np.zeros((1, 1, 3), dtype=np.uint8), gallery, nguong=0.3)
    assert ma == "nguoi_a"


def test_dong35_khong_ai_vuot_nguong_tra_none_va_diem_cao_nhat():
    vec_truy_van = np.array([1.0, 0.0], dtype=np.float32)
    backend = _backend_gia([vec_truy_van])
    goc = np.deg2rad(30)
    gallery = {
        "nguoi_a": np.array([np.cos(goc), np.sin(goc)], dtype=np.float32),
        "nguoi_b": np.array([0.0, 1.0], dtype=np.float32),
    }

    ma, diem = backend.identify(np.zeros((1, 1, 3), dtype=np.uint8), gallery, nguong=0.99)
    assert ma is None
    assert diem != 0.0


def test_dong36_gallery_rong_tra_none_0_khong_nem_loi():
    backend = _backend_gia([])
    anh = np.zeros((112, 112, 3), dtype=np.uint8)
    ma, diem = backend.identify(anh, {}, nguong=0.5)
    assert ma is None
    assert diem == 0.0


def test_dong37_nguong_that_su_duoc_dung():
    goc = np.deg2rad(30)
    gallery = {"nguoi_a": np.array([np.cos(goc), np.sin(goc)], dtype=np.float32)}

    backend_thap = _backend_gia([np.array([1.0, 0.0], dtype=np.float32)])
    ma_thap, _diem_thap = backend_thap.identify(
        np.zeros((1, 1, 3), dtype=np.uint8), gallery, nguong=0.3
    )

    backend_cao = _backend_gia([np.array([1.0, 0.0], dtype=np.float32)])
    ma_cao, _diem_cao = backend_cao.identify(
        np.zeros((1, 1, 3), dtype=np.uint8), gallery, nguong=0.95
    )

    assert ma_thap == "nguoi_a"
    assert ma_cao is None


def test_dong38_chon_diem_cao_nhat_khong_phai_nguoi_dau():
    """Ca chặn lỗi ĐB6 — xem §7 của đặc tả.

    Ba người, tất cả đều vượt ngưỡng 0,9, nhưng người điểm cao nhất (nguoi_dung) được đặt CUỐI
    dict. Cài đặt "trả người đầu tiên vượt ngưỡng" sẽ sai vì nguoi_dau đứng trước và cũng vượt
    ngưỡng — chỉ cài đặt "quét hết, giữ điểm cao nhất" mới trả đúng nguoi_dung.
    """
    vec_truy_van = np.array([1.0, 0.0], dtype=np.float32)
    backend = _backend_gia([vec_truy_van])

    goc_nho = np.deg2rad(10)
    goc_vua = np.deg2rad(5)
    gallery = {
        "nguoi_dau": np.array([np.cos(goc_nho), np.sin(goc_nho)], dtype=np.float32),
        "nguoi_giua": np.array([np.cos(goc_vua), np.sin(goc_vua)], dtype=np.float32),
        "nguoi_dung": np.array([1.0, 0.0], dtype=np.float32),
    }

    ma, diem = backend.identify(np.zeros((1, 1, 3), dtype=np.uint8), gallery, nguong=0.9)
    assert ma == "nguoi_dung"
    assert diem == pytest.approx(1.0, abs=1e-6)


# ============================================================================
# §6.6 — chặn 'mean'/'scale' không hữu hạn ở ArcFaceBackend.__init__ (dòng 39-43, P3-01b)
# ============================================================================


def test_dong39_scale_inf_nem_loicauhinh():
    """Chốt G5 — dòng 39 của đặc tả P3-01b.

    KHÔNG cần `_bo_qua_neu_thieu(_MODEL_PATH)`: mọi tham số cấu hình được xác thực TRƯỚC khi
    `__init__` chạm tới hệ thống tệp/ONNX (xem thứ tự gọi trong `ArcFaceBackend.__init__`) —
    cùng cách test_dong06/07/08 cũ đã khai thác. Nhờ vậy ca này chạy được cả khi chưa có
    `models/mobilefacenet.onnx`, kể cả trong container ARM64.
    """
    cfg = _cfg_hop_le()
    cfg["scale"] = float("inf")
    with pytest.raises(LoiCauHinh) as exc_info:
        ArcFaceBackend(cfg)
    assert "scale" in str(exc_info.value)


def test_dong40_scale_nan_nem_loicauhinh():
    """Chốt G5 — dòng 40 của đặc tả P3-01b. Không cần mô hình thật, xem lý do ở test_dong39."""
    cfg = _cfg_hop_le()
    cfg["scale"] = float("nan")
    with pytest.raises(LoiCauHinh) as exc_info:
        ArcFaceBackend(cfg)
    assert "scale" in str(exc_info.value)


def test_dong41_mean_inf_nem_loicauhinh():
    """Chốt G6 — dòng 41 của đặc tả P3-01b. Không cần mô hình thật, xem lý do ở test_dong39."""
    cfg = _cfg_hop_le()
    cfg["mean"] = float("inf")
    with pytest.raises(LoiCauHinh) as exc_info:
        ArcFaceBackend(cfg)
    assert "mean" in str(exc_info.value)


def test_dong42_mean_am_vo_cung_va_nan_nem_loicauhinh():
    """Chốt G6 — dòng 42 của đặc tả P3-01b, hai giá trị `mean = -inf` và `mean = nan`.

    Không cần mô hình thật, xem lý do ở test_dong39.
    """
    for gia_tri in (float("-inf"), float("nan")):
        cfg = _cfg_hop_le()
        cfg["mean"] = gia_tri
        with pytest.raises(LoiCauHinh) as exc_info:
            ArcFaceBackend(cfg)
        assert "mean" in str(exc_info.value)


def test_dong43_mean_0_va_am127_5_duoc_chap_nhan():
    """Ca chống vá quá tay — dòng 43 của đặc tả P3-01b, xem §6.1.

    `mean` chỉ cần hữu hạn, KHÔNG cần dương: `mean = 0` (phương án x/255, §4.2 đặc tả P3-01)
    và `mean = -127,5` đều hợp lệ. Chốt `math.isfinite` không được chặn nhầm hai giá trị này —
    nếu chặn nhầm thì đây là dấu hiệu vá quá tay (xem §10 đặc tả P3-01b).
    """
    anh = _anh_bgr_10_20_30()

    cfg_0 = _cfg_chuan_hoa_hop_le()
    cfg_0["mean"] = 0.0
    ra_0 = chuan_bi_dau_vao(anh, cfg_0)  # không ném lỗi

    cfg_am = _cfg_chuan_hoa_hop_le()
    cfg_am["mean"] = -127.5
    ra_am = chuan_bi_dau_vao(anh, cfg_am)  # không ném lỗi

    assert not np.allclose(ra_0, ra_am)


# ============================================================================
# §6.7 — chốt NaN cho độ dài vectơ, G6 (dòng 44-45, P3-01b)
# ============================================================================


def test_dong44_trich_dac_trung_do_dai_nan_nem_loi_khong_tra_ve_nan():
    """Chốt G6 — dòng 44 của đặc tả P3-01b.

    `trich_dac_trung()` THẬT (không bị thay thế) phải ném lỗi khi độ dài vectơ là NaN. Nếu vì lý
    do gì đó không ném lỗi, phép assert dưới đây vẫn phải chặn được mọi mảng NaN lọt ra ngoài.
    """
    vec_nan = np.full(512, np.nan, dtype=np.float32)
    backend = _backend_gia_voi_session(vec_nan)
    anh = np.zeros((112, 112, 3), dtype=np.uint8)

    try:
        vec = backend.trich_dac_trung(anh)
    except ValueError:
        pass
    else:
        assert not np.any(np.isnan(vec)), "trich_dac_trung không được trả vectơ chứa NaN"
        pytest.fail("trich_dac_trung phải ném ValueError khi độ dài vectơ đặc trưng là NaN")


def test_dong45_enroll_mot_anh_cho_vector_nan_nem_loi_khong_dang_ky():
    """Chốt G6 — dòng 45 của đặc tả P3-01b.

    Một ảnh trong danh sách cho vectơ NaN → không đăng ký.
    """
    vecs = [
        np.array([1.0, 0.0], dtype=np.float32),
        np.full(2, np.nan, dtype=np.float32),
    ]
    backend = _backend_gia(vecs)

    with pytest.raises(ValueError):
        backend.enroll(
            [np.zeros((1, 1, 3), dtype=np.uint8), np.zeros((1, 1, 3), dtype=np.uint8)],
            {"min_images_per_user": 2},
        )


# ============================================================================
# §6.8 — đối chiếu input_size với đồ thị ONNX, G7 (dòng 46, P3-01b)
# ============================================================================


def test_dong46_input_size_lech_do_thi_onnx_nem_loicauhinh():
    """Chốt G7 — dòng 46 của đặc tả P3-01b. Thông báo phải nêu CẢ HAI con số 64 và 112."""
    _bo_qua_neu_thieu(_MODEL_PATH)
    cfg = _cfg_hop_le()
    cfg["input_size"] = [64, 64]
    with pytest.raises(LoiCauHinh) as exc_info:
        ArcFaceBackend(cfg)
    thong_bao = str(exc_info.value)
    assert "64" in thong_bao
    assert "112" in thong_bao


# ============================================================================
# §6.9 — tệp cấu hình thật, G1 (dòng 47, P3-01b) — ca quan trọng nhất của mã việc này
# ============================================================================


def test_dong47_nap_configs_recognize_yaml_that_khop_moc_da_do():
    """Chốt G1 — dòng 47 của đặc tả P3-01b.

    Nạp `configs/recognize.yaml` THẬT (không phải `_cfg_hop_le()` viết tay) và đối chiếu bốn
    giá trị chuẩn hoá đã chốt bằng thực nghiệm (models/README.md §3.3, tách biệt 0,6010). Không
    cần mô hình ONNX, chỉ đọc YAML — không được skip, phải chạy cả trong container ARM64.
    """
    cfg_toan_bo = nap_cau_hinh("configs/recognize.yaml")
    cfg_arcface = lay_gia_tri(cfg_toan_bo, "arcface")

    assert cfg_arcface["channel_order"] == "rgb"
    assert cfg_arcface["mean"] == 127.5
    assert cfg_arcface["scale"] == 128.0
    assert cfg_arcface["embedding_dim"] == 512
    assert cfg_arcface["input_size"] == [112, 112]
