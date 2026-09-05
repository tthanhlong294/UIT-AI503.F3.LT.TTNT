"""Kiểm thử cho scripts/enroll.py (mã việc P3-03).

Ca cần trọng số thật (dlib + mobilefacenet.onnx) đánh dấu `@pytest.mark.slow` — đúng dòng 07, 08,
17, 18, 25 của bảng §7 đặc tả. Các ca còn lại dùng một `BoNhanDien` GIẢ, gắn qua
`monkeypatch.setattr(se, "tao_bo_nhan_dien", ...)`, để chạy được trong container không có
`models/`.

Không ca nào ghi vào `data/` hay `results/` — mọi đường dẫn `--vao`/`--ra`/`--config` đều nằm
trong `tmp_path` của pytest (trừ các ca `slow` dùng `configs/recognize.yaml` THẬT chỉ để ĐỌC, và
luôn ghi `--ra` vào `tmp_path`). Tên hàm test tham chiếu số dòng trong bảng §7 của
docs/dac-ta/P3-03-enroll.md.

⚠️ Dòng 26 là ca canh §6.1 và là ca quan trọng nhất tệp này (xem đặc tả ĐB1): `_BackendDemGoi`
đếm số lần `enroll()` được gọi. Nếu script tự tính trung bình thay vì gọi `backend.enroll()`,
bộ đếm này không tăng, và dòng 26 phải đỏ.

⚠️ `test_dong09b_...` và `test_dong09c_...` canh CHẶN-B-1 (biên bản review vòng 1): dùng
`_BackendLoiMoHinhGia`, có `enroll()` LUÔN ném `ValueError` bất kể số ảnh. Ca 09b đủ ảnh — phải
thành `LoiMoHinh`, mã trả về 1, không ghi `.npy`. Ca 09c thiếu ảnh thật — vẫn phải là `thieu_anh`,
mã trả về 0. Hai ca này chứng minh bản vá phân biệt bằng SỐ ẢNH THẬT SỰ, không bằng nội dung
`ValueError`.
"""

import csv
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from scripts import enroll as se
from src.common.exceptions import LoiMoHinh
from src.recognizer.base import BoNhanDien

_MODEL_DLIB = Path("models/dlib/dlib_face_recognition_resnet_model_v1.dat")
_SHAPE_DLIB = Path("models/dlib/shape_predictor_68_face_landmarks.dat")
_MODEL_ARCFACE = Path("models/mobilefacenet.onnx")
_CONFIG_THAT = Path("configs/recognize.yaml")

_TEN_BA_NGUOI = ("nguoi_a", "nguoi_b", "nguoi_c")


class _BackendLoiMoHinhGia(BoNhanDien):
    """`BoNhanDien` GIẢ: `enroll()` LUÔN ném `ValueError`, bất kể số ảnh nhận được.

    Dùng để canh CHẶN-B-1 (biên bản review vòng 1 P3-03-enroll): `ValueError` không phải lúc
    nào cũng là "thiếu ảnh" — nó còn là lỗi mô hình (vd: vectơ đặc trưng có độ dài 0) hoặc dữ
    liệu vào chưa qua tiền xử lý. Backend này mô phỏng đúng nhóm lỗi đó: nó không hề xét số
    lượng ảnh trước khi ném lỗi, khác hẳn `_BackendDemGoi` ở trên.
    """

    def __init__(self, so_chieu: int = 4) -> None:
        self._so_chieu = so_chieu

    @property
    def so_chieu(self) -> int:
        return self._so_chieu

    def trich_dac_trung(self, anh: np.ndarray) -> np.ndarray:
        raise AssertionError("trich_dac_trung() không được scripts/enroll.py gọi trực tiếp")

    def enroll(self, danh_sach_anh: list[np.ndarray], cfg: dict) -> np.ndarray:
        raise ValueError("Vectơ đặc trưng có độ dài 0")

    def identify(
        self, anh: np.ndarray, gallery: dict[str, np.ndarray], nguong: float
    ) -> tuple[str | None, float]:
        raise AssertionError("identify() không được scripts/enroll.py dùng tới")


class _BackendDemGoi(BoNhanDien):
    """`BoNhanDien` GIẢ: không cần trọng số, đếm số lần `enroll()` được gọi.

    `trich_dac_trung`/`identify` KHÔNG được `scripts/enroll.py` dùng tới — ném lỗi nếu bị gọi
    nhầm, để lộ ngay nếu script đổi cách gọi backend.
    """

    def __init__(self, so_chieu: int = 4, seed: int = 0) -> None:
        self._so_chieu = so_chieu
        self._rng = np.random.default_rng(seed)
        self.so_lan_goi = 0

    @property
    def so_chieu(self) -> int:
        return self._so_chieu

    def trich_dac_trung(self, anh: np.ndarray) -> np.ndarray:
        raise AssertionError("trich_dac_trung() không được scripts/enroll.py gọi trực tiếp")

    def enroll(self, danh_sach_anh: list[np.ndarray], cfg: dict) -> np.ndarray:
        self.so_lan_goi += 1
        so_toi_thieu = cfg["min_images_per_user"]
        if len(danh_sach_anh) < so_toi_thieu:
            raise ValueError(
                f"Cần tối thiểu {so_toi_thieu} ảnh để đăng ký một người, "
                f"chỉ nhận được {len(danh_sach_anh)}"
            )
        vec = self._rng.standard_normal(self._so_chieu).astype(np.float32)
        return (vec / np.linalg.norm(vec)).astype(np.float32)

    def identify(
        self, anh: np.ndarray, gallery: dict[str, np.ndarray], nguong: float
    ) -> tuple[str | None, float]:
        raise AssertionError("identify() không được scripts/enroll.py dùng tới")


def _dung_backend_gia(monkeypatch, so_chieu: int = 4, seed: int = 0) -> _BackendDemGoi:
    """Gắn một `_BackendDemGoi` vào `scripts.enroll.tao_bo_nhan_dien`, bỏ qua trọng số thật."""
    backend = _BackendDemGoi(so_chieu=so_chieu, seed=seed)
    monkeypatch.setattr(se, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    return backend


class _BackendHongLanThu(BoNhanDien):
    """`BoNhanDien` GIẢ: `enroll()` thành công `so_lan_thanh_cong` lần đầu, sau đó LUÔN ném
    `ValueError` — mô phỏng lỗi mô hình xảy ra GIỮA một lượt đăng ký nhiều người, bất kể số ảnh
    của người gặp lỗi có đủ hay không (dùng cho các ca canh §4.1-4.4 đặc tả P3-04, ghi gallery
    nguyên khối)."""

    def __init__(self, so_chieu: int = 4, seed: int = 0, so_lan_thanh_cong: int = 1) -> None:
        self._so_chieu = so_chieu
        self._rng = np.random.default_rng(seed)
        self._so_lan_thanh_cong = so_lan_thanh_cong
        self.so_lan_goi = 0

    @property
    def so_chieu(self) -> int:
        return self._so_chieu

    def trich_dac_trung(self, anh: np.ndarray) -> np.ndarray:
        raise AssertionError("trich_dac_trung() không được scripts/enroll.py gọi trực tiếp")

    def enroll(self, danh_sach_anh: list[np.ndarray], cfg: dict) -> np.ndarray:
        self.so_lan_goi += 1
        if self.so_lan_goi > self._so_lan_thanh_cong:
            raise ValueError(f"Lỗi mô hình giả lập ở lần gọi thứ {self.so_lan_goi}")
        vec = self._rng.standard_normal(self._so_chieu).astype(np.float32)
        return (vec / np.linalg.norm(vec)).astype(np.float32)

    def identify(
        self, anh: np.ndarray, gallery: dict[str, np.ndarray], nguong: float
    ) -> tuple[str | None, float]:
        raise AssertionError("identify() không được scripts/enroll.py dùng tới")


def _ghi_cfg(
    tmp_path: Path,
    backend: str = "dlib",
    gallery_dir: str | None = None,
    min_images: int = 3,
) -> Path:
    """Ghi một `configs/recognize.yaml` tối giản — đủ khoá `scripts/enroll.py` tự đọc trực
    tiếp (`backend`, `enroll.*`). Backend GIẢ không đọc mục "dlib"/"arcface"."""
    gallery_dir_thuc = (
        gallery_dir if gallery_dir is not None else str(tmp_path / "gallery_mac_dinh")
    )
    dong = [
        f"backend: {backend}",
        "enroll:",
        f"  gallery_dir: {gallery_dir_thuc}",
        f"  min_images_per_user: {min_images}",
    ]
    duong_dan = tmp_path / "recognize_test.yaml"
    duong_dan.write_text("\n".join(dong) + "\n", encoding="utf-8")
    return duong_dan


def _anh_gia(duong_dan: Path, seed: int = 0) -> None:
    """Ghi một ảnh PNG 2x2 GIẢI MÃ ĐƯỢC bằng cv2.imread — nội dung không quan trọng với backend
    giả, chỉ cần đọc được."""
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    anh = rng.integers(0, 256, size=(2, 2, 3), dtype=np.uint8)
    cv2.imwrite(str(duong_dan), anh)


def _ghi_nguoi(thu_muc_vao: Path, user_id: str, so_anh: int, seed: int = 0) -> None:
    """Ghi `so_anh` ảnh giả vào `<thu_muc_vao>/<user_id>/`."""
    for i in range(so_anh):
        _anh_gia(thu_muc_vao / user_id / f"anh_{i:02d}.png", seed=seed * 100 + i)


def _anh_ngau_nhien_that(duong_dan: Path, seed: int = 0) -> None:
    """Ảnh 112x112 BGR ngẫu nhiên — dùng cho ca cần backend THẬT.

    dlib chạy shape_predictor trên TOÀN khung ảnh, không tự dò khuôn mặt (xem docstring
    src/recognizer/dlib_backend.py) nên không cần nội dung là khuôn mặt thật — cùng cách
    tests/test_dlib_backend.py `_anh_bgr_ngau_nhien` đã dùng.
    """
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    anh = rng.integers(0, 256, size=(112, 112, 3), dtype=np.uint8)
    cv2.imwrite(str(duong_dan), anh)


def _bo_qua_neu_thieu_dlib() -> None:
    pytest.importorskip("dlib")
    if not _MODEL_DLIB.exists() or not _SHAPE_DLIB.exists():
        pytest.skip("chưa có trọng số dlib, xem models/README.md để tải mô hình")


def _bo_qua_neu_thieu_arcface() -> None:
    if not _MODEL_ARCFACE.exists():
        pytest.skip("chưa có models/mobilefacenet.onnx, xem models/README.md để tải mô hình")


def _sha256(duong_dan: Path) -> str:
    return hashlib.sha256(duong_dan.read_bytes()).hexdigest()


def _doc_manifest(duong_dan: Path) -> list[dict]:
    with open(duong_dan, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ============================================================================
# §7 — scripts/enroll.py (dòng 07-26)
# ============================================================================


@pytest.mark.slow
def test_dong07_ba_nguoi_du_anh_ghi_du_ba_tep(tmp_path):
    _bo_qua_neu_thieu_dlib()
    vao = tmp_path / "vao"
    for idx, ten in enumerate(_TEN_BA_NGUOI):
        for i in range(3):
            _anh_ngau_nhien_that(vao / ten / f"anh_{i}.png", seed=idx * 10 + i)
    ra = tmp_path / "ra"

    ma = se.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--config",
            str(_CONFIG_THAT),
            "--backend",
            "dlib",
            "--toi-thieu",
            "3",
        ]
    )
    assert ma == 0
    for ten in _TEN_BA_NGUOI:
        vec = np.load(ra / "dlib" / f"{ten}.npy")
        assert vec.shape == (128,)
        assert vec.dtype == np.float32


@pytest.mark.slow
def test_dong08_vector_ghi_ra_co_do_dai_l2_bang_1(tmp_path):
    _bo_qua_neu_thieu_dlib()
    vao = tmp_path / "vao"
    for i in range(3):
        _anh_ngau_nhien_that(vao / "nguoi_a" / f"anh_{i}.png", seed=i)
    ra = tmp_path / "ra"

    ma = se.main(
        [
            "--vao",
            str(vao),
            "--ra",
            str(ra),
            "--config",
            str(_CONFIG_THAT),
            "--backend",
            "dlib",
            "--toi-thieu",
            "3",
        ]
    )
    assert ma == 0
    vec = np.load(ra / "dlib" / "nguoi_a.npy")
    assert abs(np.linalg.norm(vec) - 1.0) < 1e-5


def test_dong09_it_anh_hon_nguong_khong_ghi_npy(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_it", so_anh=2)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0
    assert not (ra / "dlib" / "nguoi_it.npy").exists()

    rows = _doc_manifest(ra / "dlib" / "manifest.csv")
    assert rows[0]["trang_thai"] == "thieu_anh"


def test_dong09b_loi_mo_hinh_du_anh_khong_bi_ghi_thieu_anh(tmp_path, monkeypatch):
    """Ca canh CHẶN-B-1 (biên bản review vòng 1): đủ ảnh mà `enroll()` vẫn ném `ValueError` là
    lỗi mô hình, KHÔNG phải thiếu ảnh — phải nổi lên thành `LoiMoHinh`, dừng cả lượt chạy.

    Trước bản vá, khối `except ValueError` bắt mọi trường hợp và ghi nhầm `thieu_anh` dù người
    này có tới 5 ảnh với ngưỡng 3.
    """
    backend = _BackendLoiMoHinhGia()
    monkeypatch.setattr(se, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=5)  # đủ ảnh so với ngưỡng 3 — không phải thiếu ảnh
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 1
    assert not (ra / "dlib" / "nguoi_a.npy").exists()

    manifest = ra / "dlib" / "manifest.csv"
    # Sau §4.2 (ghi gallery nguyên khối), thư mục đích không hề được tạo khi lượt chạy dừng giữa
    # chừng vì LoiMoHinh — manifest chưa từng được ghi vào đó. Trước bản vá này, khối `if` bên
    # dưới không bao giờ chạy (nhánh chết) vì lý do tương tự nhưng không có gì khẳng định điều
    # đó — review vòng 2 chỉ ra đây là một chốt tưởng có mà không có (§4.5 điều 2 đặc tả P3-04).
    assert not manifest.exists()


def test_dong09c_loi_mo_hinh_nhung_thieu_anh_that_van_la_thieu_anh(tmp_path, monkeypatch):
    """Ca đối chứng của test_dong09b: cùng backend LUÔN ném `ValueError`, nhưng lần này người
    thật sự thiếu ảnh — phải vẫn được phân loại `thieu_anh`, mã trả về 0 (giữ nguyên §6.2).

    Chứng minh bản vá phân biệt bằng SỐ ẢNH THẬT SỰ (`so_anh_tim_thay` so với
    `min_images_per_user`), không phải bằng nội dung thông điệp `ValueError`.
    """
    backend = _BackendLoiMoHinhGia()
    monkeypatch.setattr(se, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_it", so_anh=2)  # thiếu ảnh thật so với ngưỡng 3
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0
    assert not (ra / "dlib" / "nguoi_it.npy").exists()

    rows = _doc_manifest(ra / "dlib" / "manifest.csv")
    assert rows[0]["trang_thai"] == "thieu_anh"


def test_dong10_manifest_du_sau_cot_dung_thu_tu(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0

    with open(ra / "dlib" / "manifest.csv", newline="", encoding="utf-8") as f:
        tieu_de = next(csv.reader(f))
    assert tieu_de == [
        "user_id",
        "so_anh_tim_thay",
        "so_anh_dung",
        "trang_thai",
        "so_chieu",
        "tep_ra",
    ]


def test_dong11_manifest_co_dong_cho_nguoi_bo_qua(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_du", so_anh=3)
    _ghi_nguoi(vao, "nguoi_thieu", so_anh=1)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0
    rows = _doc_manifest(ra / "dlib" / "manifest.csv")
    assert len(rows) == 2
    trang_thai_theo_ten = {r["user_id"]: r["trang_thai"] for r in rows}
    assert trang_thai_theo_ten == {"nguoi_du": "da_dang_ky", "nguoi_thieu": "thieu_anh"}


def test_dong12_meta_du_khoa_bat_buoc(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0

    meta = json.loads((ra / "dlib" / "gallery.meta.json").read_text(encoding="utf-8"))
    khoa_bat_buoc = (
        "backend",
        "so_chieu",
        "duong_dan_vao",
        "so_nguoi_da_dang_ky",
        "so_nguoi_bo_qua",
        "min_images_per_user_da_dung",
        "min_images_per_user_trong_cau_hinh",
        "seed",
        "thoi_gian",
        "commit",
        "git_dirty",
        "moi_truong",
        "software",
    )
    for khoa in khoa_bat_buoc:
        assert khoa in meta, f"thiếu khoá '{khoa}' trong gallery.meta.json"


def test_dong13_moi_truong_hop_le(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0
    meta = json.loads((ra / "dlib" / "gallery.meta.json").read_text(encoding="utf-8"))
    assert meta["moi_truong"] in ("pc_x86", "docker_arm64", "pi5")


def test_dong14_toi_thieu_khac_cau_hinh_ghi_ca_hai_con_so(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=2)
    cfg = _ghi_cfg(tmp_path, min_images=5)  # cấu hình đòi 5, --toi-thieu ghi đè xuống 2
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg), "--toi-thieu", "2"])
    assert ma == 0
    meta = json.loads((ra / "dlib" / "gallery.meta.json").read_text(encoding="utf-8"))
    assert meta["min_images_per_user_da_dung"] == 2
    assert meta["min_images_per_user_trong_cau_hinh"] == 5
    assert meta["min_images_per_user_da_dung"] != meta["min_images_per_user_trong_cau_hinh"]


def test_dong15_toi_thieu_khac_cau_hinh_co_canh_bao_warning(tmp_path, monkeypatch, caplog):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=2)
    cfg = _ghi_cfg(tmp_path, min_images=5)
    ra = tmp_path / "ra"

    with caplog.at_level("WARNING"):
        ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg), "--toi-thieu", "2"])
    assert ma == 0
    assert any(
        rec.levelname == "WARNING" and "2" in rec.getMessage() and "5" in rec.getMessage()
        for rec in caplog.records
    )


@pytest.mark.parametrize("gia_tri", ["-1", "abc", "1.5"])
def test_dong16_toi_thieu_am_hoac_khong_phai_so_nguyen(tmp_path, monkeypatch, gia_tri):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg), "--toi-thieu", gia_tri])
    assert ma == 1
    assert not ra.exists()


@pytest.mark.slow
def test_dong17_hai_backend_ghi_hai_thu_muc_khac_nhau(tmp_path):
    _bo_qua_neu_thieu_dlib()
    _bo_qua_neu_thieu_arcface()
    vao = tmp_path / "vao"
    for i in range(3):
        _anh_ngau_nhien_that(vao / "nguoi_a" / f"anh_{i}.png", seed=i)
    ra = tmp_path / "ra"

    for backend in ("dlib", "arcface"):
        ma = se.main(
            [
                "--vao",
                str(vao),
                "--ra",
                str(ra),
                "--config",
                str(_CONFIG_THAT),
                "--backend",
                backend,
                "--toi-thieu",
                "3",
            ]
        )
        assert ma == 0

    assert (ra / "dlib" / "nguoi_a.npy").exists()
    assert (ra / "arcface" / "nguoi_a.npy").exists()
    assert not (ra / "nguoi_a.npy").exists()


@pytest.mark.slow
def test_dong18_so_chieu_dung_theo_backend_tren_cung_thu_muc_anh(tmp_path):
    _bo_qua_neu_thieu_dlib()
    _bo_qua_neu_thieu_arcface()
    vao = tmp_path / "vao"
    for i in range(3):
        _anh_ngau_nhien_that(vao / "nguoi_a" / f"anh_{i}.png", seed=i)
    ra = tmp_path / "ra"

    for backend, so_chieu_ky_vong in (("dlib", 128), ("arcface", 512)):
        ma = se.main(
            [
                "--vao",
                str(vao),
                "--ra",
                str(ra),
                "--config",
                str(_CONFIG_THAT),
                "--backend",
                backend,
                "--toi-thieu",
                "3",
            ]
        )
        assert ma == 0
        vec = np.load(ra / backend / "nguoi_a.npy")
        assert vec.shape == (so_chieu_ky_vong,)


def test_dong19_dry_run_khong_ghi_gi(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg), "--dry-run"])
    assert ma == 0
    assert not ra.exists()


def test_dong20_loc_theo_nguoi_chi_dang_ky_ten_yeu_cau(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "A", so_anh=3)
    _ghi_nguoi(vao, "B", so_anh=3)
    _ghi_nguoi(vao, "C", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg), "--nguoi", "A,B"])
    assert ma == 0
    tep = sorted(p.name for p in (ra / "dlib").glob("*.npy"))
    assert tep == ["A.npy", "B.npy"]


def test_dong21_nguoi_khong_ton_tai_tra_ve_1_va_neu_ten_sai(tmp_path, monkeypatch, capsys):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "A", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(
        ["--vao", str(vao), "--ra", str(ra), "--config", str(cfg), "--nguoi", "A,khong_co"]
    )
    assert ma == 1
    out = capsys.readouterr().out
    assert "khong_co" in out


def test_dong22_thu_muc_con_rong_bo_qua_khong_vao_manifest(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    (vao / "nguoi_rong").mkdir(parents=True)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0
    rows = _doc_manifest(ra / "dlib" / "manifest.csv")
    ten_trong_manifest = {r["user_id"] for r in rows}
    assert ten_trong_manifest == {"nguoi_a"}


def test_dong23_vao_khong_ton_tai_tra_ve_1_khong_nem_ngoai_le(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    cfg = _ghi_cfg(tmp_path, min_images=3)

    ma = se.main(
        [
            "--vao",
            str(tmp_path / "khong_ton_tai"),
            "--ra",
            str(tmp_path / "ra"),
            "--config",
            str(cfg),
        ]
    )
    assert ma == 1


def test_dong24_anh_hong_khong_lam_hong_nguoi_khac(tmp_path, monkeypatch):
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_tot", so_anh=3)
    thu_muc_hong = vao / "nguoi_hong"
    thu_muc_hong.mkdir(parents=True)
    for i in range(3):
        (thu_muc_hong / f"anh_{i:02d}.png").write_bytes(b"")  # 0 byte, không giải mã được
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0

    rows = {r["user_id"]: r for r in _doc_manifest(ra / "dlib" / "manifest.csv")}
    assert rows["nguoi_hong"]["trang_thai"] == "loi_doc_anh"
    assert rows["nguoi_tot"]["trang_thai"] == "da_dang_ky"
    assert (ra / "dlib" / "nguoi_tot.npy").exists()
    assert not (ra / "dlib" / "nguoi_hong.npy").exists()


@pytest.mark.slow
def test_dong25_chay_lai_lan_hai_cho_vecto_giong_het(tmp_path):
    _bo_qua_neu_thieu_dlib()
    vao = tmp_path / "vao"
    for i in range(3):
        _anh_ngau_nhien_that(vao / "nguoi_a" / f"anh_{i}.png", seed=i)

    ra1 = tmp_path / "ra1"
    ra2 = tmp_path / "ra2"
    for ra in (ra1, ra2):
        ma = se.main(
            [
                "--vao",
                str(vao),
                "--ra",
                str(ra),
                "--config",
                str(_CONFIG_THAT),
                "--backend",
                "dlib",
                "--toi-thieu",
                "3",
            ]
        )
        assert ma == 0

    assert _sha256(ra1 / "dlib" / "nguoi_a.npy") == _sha256(ra2 / "dlib" / "nguoi_a.npy")


def test_dong26_enroll_duoc_goi_dung_mot_lan_moi_nguoi(tmp_path, monkeypatch):
    """Ca canh §6.1 — xem ĐB1 của đặc tả. QUAN TRỌNG NHẤT tệp này.

    Nếu script tự tính vectơ trung bình thay vì gọi `backend.enroll()`, `so_lan_goi` không tăng
    và phép so sánh dưới đây thất bại.
    """
    backend = _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    _ghi_nguoi(vao, "nguoi_b", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0
    assert backend.so_lan_goi == 2


# ============================================================================
# §5 docs/dac-ta/P3-04-enroll-ghi-nguyen-khoi.md — scripts/enroll.py (dòng 27-36)
# ============================================================================


def test_dong27_hong_giua_chung_khong_de_lai_thu_muc_dich(tmp_path, monkeypatch):
    """Ca canh §4.1-4.2: lượt chạy dừng giữa chừng (người thứ hai làm backend ném lỗi mô hình,
    người thứ nhất đã đủ ảnh và đã đăng ký thành công) không được để lại `<ra>/<backend>/`.
    Xem ĐB1, ĐB3 của đặc tả — hai phép đó phải làm ca này đỏ.
    """
    backend = _BackendHongLanThu(so_lan_thanh_cong=1)
    monkeypatch.setattr(se, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    _ghi_nguoi(vao, "nguoi_b", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 1
    assert not (ra / "dlib").exists()


def test_dong28_hong_giua_chung_khong_sot_thu_muc_tam(tmp_path, monkeypatch):
    """Cùng tình huống ca 27: không thư mục tạm nào (`.dlib.dang-ghi`, `.dlib.cu`) sót lại
    trong thư mục ra. Xem ĐB2 của đặc tả."""
    backend = _BackendHongLanThu(so_lan_thanh_cong=1)
    monkeypatch.setattr(se, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    _ghi_nguoi(vao, "nguoi_b", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 1
    if ra.exists():
        ten_con = [p.name for p in ra.iterdir()]
        assert not any(ten.startswith(".") for ten in ten_con)


def test_dong29_thanh_cong_ghi_du_ba_loai_tep_khong_sot_thu_muc_tam(tmp_path, monkeypatch):
    """Lượt chạy thành công: thư mục đích có đủ `.npy` + `manifest.csv` + `gallery.meta.json`,
    và không thư mục tạm nào sót lại cạnh nó."""
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0
    assert (ra / "dlib" / "nguoi_a.npy").exists()
    assert (ra / "dlib" / "manifest.csv").exists()
    assert (ra / "dlib" / "gallery.meta.json").exists()
    ten_con = [p.name for p in ra.iterdir()]
    assert not any(ten.startswith(".") for ten in ten_con)


def test_dong30_khong_ai_du_anh_van_ghi_manifest_va_meta(tmp_path, monkeypatch):
    """Lượt chạy hợp lệ nhưng không ai đủ ảnh: đây là ngoại lệ nêu ở §4.1 — thư mục đích vẫn
    phải có `manifest.csv` và `gallery.meta.json` (bằng chứng vì sao không có ai), chỉ là
    không có `.npy` nào."""
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_it", so_anh=1)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0
    assert (ra / "dlib" / "manifest.csv").exists()
    assert (ra / "dlib" / "gallery.meta.json").exists()
    assert not list((ra / "dlib").glob("*.npy"))


def test_dong31_gallery_cu_con_nguyen_ven_khi_lot_moi_hong(tmp_path, monkeypatch):
    """Ca quan trọng nhất của §4.1-4.4 (xem §5 đặc tả): đã có gallery cũ, lượt mới hỏng giữa
    chừng — gallery cũ phải còn NGUYÊN VẸN, so `sha256` từng tệp trước và sau. Xem ĐB4 của đặc
    tả — phép đó phải làm ca này đỏ."""
    vao1 = tmp_path / "vao1"
    _ghi_nguoi(vao1, "nguoi_cu", so_anh=3)
    cfg1 = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    _dung_backend_gia(monkeypatch)
    ma = se.main(["--vao", str(vao1), "--ra", str(ra), "--config", str(cfg1)])
    assert ma == 0

    sha_truoc = {p.name: _sha256(p) for p in (ra / "dlib").iterdir() if p.is_file()}

    backend_hong = _BackendHongLanThu(so_lan_thanh_cong=1)
    monkeypatch.setattr(se, "tao_bo_nhan_dien", lambda cfg, ten: backend_hong)
    vao2 = tmp_path / "vao2"
    _ghi_nguoi(vao2, "nguoi_moi_1", so_anh=3)
    _ghi_nguoi(vao2, "nguoi_moi_2", so_anh=3)
    cfg2 = _ghi_cfg(tmp_path, min_images=3)

    ma2 = se.main(["--vao", str(vao2), "--ra", str(ra), "--config", str(cfg2)])
    assert ma2 == 1

    sha_sau = {p.name: _sha256(p) for p in (ra / "dlib").iterdir() if p.is_file()}
    assert sha_sau == sha_truoc


def test_dong32_gallery_moi_thay_the_hoan_toan_gallery_cu(tmp_path, monkeypatch):
    """Đã có gallery cũ, lượt mới THÀNH CÔNG với danh sách người khác: thư mục đích chỉ chứa
    người của lượt mới, không sót `.npy` của lượt cũ."""
    vao1 = tmp_path / "vao1"
    _ghi_nguoi(vao1, "nguoi_cu", so_anh=3)
    cfg1 = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    _dung_backend_gia(monkeypatch)
    ma = se.main(["--vao", str(vao1), "--ra", str(ra), "--config", str(cfg1)])
    assert ma == 0
    assert (ra / "dlib" / "nguoi_cu.npy").exists()

    _dung_backend_gia(monkeypatch)
    vao2 = tmp_path / "vao2"
    _ghi_nguoi(vao2, "nguoi_moi", so_anh=3)
    cfg2 = _ghi_cfg(tmp_path, min_images=3)

    ma2 = se.main(["--vao", str(vao2), "--ra", str(ra), "--config", str(cfg2)])
    assert ma2 == 0

    tep_npy = sorted(p.name for p in (ra / "dlib").glob("*.npy"))
    assert tep_npy == ["nguoi_moi.npy"]
    assert not (ra / "dlib" / "nguoi_cu.npy").exists()


def test_dong33_thu_muc_tam_sot_lai_bi_don_truoc_khi_ghi(tmp_path, monkeypatch):
    """Thư mục tạm còn sót từ lượt trước (tạo sẵn, có một tệp rác): lượt mới vẫn chạy trót lọt,
    tệp rác biến mất, mã trả về 0 (§4.2 điều 1: xoá sạch thư mục tạm cũ rồi tạo lại)."""
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    thu_muc_tam = ra / ".dlib.dang-ghi"
    thu_muc_tam.mkdir(parents=True)
    (thu_muc_tam / "rac.txt").write_text("rac", encoding="utf-8")

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 0
    assert not (ra / "dlib" / "rac.txt").exists()
    assert not thu_muc_tam.exists()
    assert (ra / "dlib" / "nguoi_a.npy").exists()


def test_dong34_dry_run_khong_tao_thu_muc_tam(tmp_path, monkeypatch):
    """`--dry-run` không được tạo thư mục nào, kể cả thư mục tạm `.dlib.dang-ghi`."""
    _dung_backend_gia(monkeypatch)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg), "--dry-run"])
    assert ma == 0
    assert not ra.exists()
    assert not (ra / ".dlib.dang-ghi").exists()


def test_dong35_xu_ly_mot_nguoi_du_anh_loi_mo_hinh_nem_dung_lop(tmp_path):
    """Ca canh §4.5 điều 1 (§12.2 biên bản review vòng 2): gọi THẲNG `xu_ly_mot_nguoi`, đủ ảnh,
    backend giả LUÔN ném `ValueError` — phải nổi lên thành đúng `LoiMoHinh`, không phải
    `LoiCauHinh`. Đây là chốt DUY NHẤT phân biệt được hai lớp ngoại lệ đó khi gọi trực tiếp,
    không đi qua `main()`. Xem ĐB5 của đặc tả — phép đó phải làm ca này đỏ."""
    backend = _BackendLoiMoHinhGia()
    thu_muc_nguoi = tmp_path / "nguoi_a"
    danh_sach_anh = []
    for i in range(5):  # đủ ảnh so với ngưỡng 3 — không phải thiếu ảnh
        duong_dan = thu_muc_nguoi / f"anh_{i:02d}.png"
        _anh_gia(duong_dan, seed=i)
        danh_sach_anh.append(duong_dan)
    cfg_enroll = {"min_images_per_user": 3}

    with pytest.raises(LoiMoHinh):
        se.xu_ly_mot_nguoi(thu_muc_nguoi, danh_sach_anh, backend, cfg_enroll)


def test_dong36_so_anh_bang_dung_nguong_van_la_loi_mo_hinh(tmp_path, monkeypatch):
    """Ca canh §4.6 (§12.3 biên bản review vòng 2): biên `so_anh_tim_thay == min_images_per_user`
    phải có người gác trong đúng phép so sánh `so_anh_tim_thay < cfg_enroll["min_images_per_user"]`
    (`scripts/enroll.py`, khối `except ValueError` của `xu_ly_mot_nguoi`) — không phải `<=`.

    Dùng `_BackendLoiMoHinhGia` (cùng backend của ca 09b/09c) để `enroll()` LUÔN ném `ValueError`
    bất kể số ảnh, và đặt `so_anh` ĐÚNG BẰNG ngưỡng (không lớn hơn, khác ca 09b dùng 5/3). Với mã
    đúng, `3 < 3` là `False` nên KHÔNG bị coi là thiếu ảnh — lỗi phải nổi lên thành `LoiMoHinh`,
    dừng cả lượt chạy, không ghi gallery nào (§4.1). Nếu toán tử bị đổi thành `<=` (ĐB6), `3 <=
    3` thành `True`, lỗi bị nuốt thành `thieu_anh` một cách im lặng và lượt chạy vẫn ghi gallery
    thành công — đúng chế độ hỏng mà §4.6 mô tả: người đủ ảnh bị mất khỏi gallery không một
    tiếng động. Xem ĐB6 của đặc tả — phép đó phải làm ca này đỏ.
    """
    backend = _BackendLoiMoHinhGia()
    monkeypatch.setattr(se, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    vao = tmp_path / "vao"
    _ghi_nguoi(vao, "nguoi_a", so_anh=3)  # đúng bằng ngưỡng, không phải lớn hơn (khác ca 09b)
    cfg = _ghi_cfg(tmp_path, min_images=3)
    ra = tmp_path / "ra"

    ma = se.main(["--vao", str(vao), "--ra", str(ra), "--config", str(cfg)])
    assert ma == 1
    assert not (ra / "dlib").exists()
