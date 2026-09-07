"""Kiểm thử cho scripts/benchmark_recognize.py.

Mọi ca ở đây dùng backend GIẢ (`_BackendGia`) — không ca nào cần `models/`, không ca nào chạm
mạng (§4.6 đặc tả P3-05). Backend giả trích đặc trưng TẤT ĐỊNH từ nội dung ảnh: cùng ảnh luôn cho
cùng vectơ, ảnh khác cho vectơ khác — đủ để kiểm chứng phép loại theo mã băm nội dung (§4.1) mà
không cần mô hình thật.

Quy ước dựng dữ liệu cho các ca gọi `main()` đầu-cuối: hai thư mục vật lý TÁCH BIỆT —
`<gốc>/enroll/<user_id>/...` (ảnh dùng đăng ký, dựng gallery) và `<gốc>/probe/<user_id>/...`
(ảnh probe, tham số `--vao`). Mọi ảnh được sinh với một seed DUY NHẤT trong toàn phiên kiểm thử
(bộ đếm `_SEED_COUNTER`), trừ khi bài kiểm cần TÁI LẬP giữa hai lượt gọi độc lập (ca 98) — khi đó
bộ đếm cục bộ được truyền tay để hai lượt sinh ra ảnh giống hệt nhau.

Cặp ca 34/35 phân biệt hai cách cài đặt gần giống nhau (§4.1, §8.4 đặc tả): ca 34 chép một ảnh đã
đăng ký sang thư mục probe GIỮ NGUYÊN TÊN TỆP (khớp theo đường dẫn tương đối lẫn theo nội dung);
ca 35 chép nhưng ĐỔI TÊN (chỉ khớp theo nội dung). Cài đặt loại theo đường dẫn tương đối qua được
ca 34 nhưng trượt ca 35 — đó chính là ĐB2 ở §10 đặc tả.
"""

import csv
import itertools
import json
import re
import shutil
from pathlib import Path

import cv2
import numpy as np
import pytest
import yaml

from scripts import benchmark_recognize as br
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.recognizer.base import BoNhanDien, do_tuong_dong

# ============================================================================
# Trợ giúp dùng chung
# ============================================================================

_SEED_COUNTER = itertools.count(1)


def _ghi_anh(duong_dan: Path, seed: int, kich_thuoc: int = 6) -> Path:
    """Ghi một ảnh PNG THẬT (giải mã được bằng cv2.imread), nội dung tất định theo seed."""
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    anh = rng.integers(0, 255, size=(kich_thuoc, kich_thuoc, 3), dtype=np.uint8)
    ok = cv2.imwrite(str(duong_dan), anh)
    assert ok
    return duong_dan


def _vec_tu_anh(anh: np.ndarray, so_chieu: int) -> np.ndarray:
    """Vectơ tất định từ nội dung ảnh — cùng ảnh luôn cho cùng vectơ (§4.6 đặc tả)."""
    import hashlib

    h = hashlib.sha256(np.ascontiguousarray(anh).tobytes()).digest()
    seed = int.from_bytes(h[:8], "little")
    rng = np.random.default_rng(seed)
    v = rng.normal(size=so_chieu).astype(np.float32)
    return (v / np.linalg.norm(v)).astype(np.float32)


class _BackendGia(BoNhanDien):
    """Backend giả cho ca kiểm thử — xem §4.6 đặc tả."""

    def __init__(self, so_chieu: int = 4, luon_loi_enroll: bool = False) -> None:
        self._so_chieu = so_chieu
        self._luon_loi_enroll = luon_loi_enroll
        self.so_lan_enroll = 0

    @property
    def so_chieu(self) -> int:
        return self._so_chieu

    def trich_dac_trung(self, anh: np.ndarray) -> np.ndarray:
        if not isinstance(anh, np.ndarray):
            raise ValueError("anh phải là numpy.ndarray")  # noqa: TRY004
        return _vec_tu_anh(anh, self._so_chieu)

    def enroll(self, danh_sach_anh: list[np.ndarray], cfg: dict) -> np.ndarray:
        if self._luon_loi_enroll:
            raise ValueError("lỗi enroll giả lập")
        if not danh_sach_anh:
            raise ValueError("danh sách ảnh rỗng")
        toi_thieu = cfg.get("min_images_per_user", 1)
        if len(danh_sach_anh) < toi_thieu:
            raise ValueError("thiếu ảnh")
        self.so_lan_enroll += 1
        vecs = [self.trich_dac_trung(a) for a in danh_sach_anh]
        tb = np.mean(vecs, axis=0)
        return (tb / np.linalg.norm(tb)).astype(np.float32)

    def identify(
        self, anh: np.ndarray, gallery: dict[str, np.ndarray], nguong: float
    ) -> tuple[str | None, float]:
        if not gallery:
            return None, 0.0
        vec = self.trich_dac_trung(anh)
        best_uid: str | None = None
        best = float("-inf")
        for uid, v in gallery.items():
            s = do_tuong_dong(vec, v)
            if s > best:
                best, best_uid = s, uid
        if best >= nguong:
            return best_uid, best
        return None, best


def _tao_anh_nguoi(
    goc: Path, uid: str, so_luong: int, bo_dem=None, ten_prefix: str = "anh"
) -> list[Path]:
    """Sinh `so_luong` ảnh thật cho một người dưới `<goc>/<uid>/`."""
    dem = bo_dem if bo_dem is not None else _SEED_COUNTER
    ds = [_ghi_anh(goc / uid / f"{ten_prefix}_{i:03d}.png", next(dem)) for i in range(so_luong)]
    return sorted(ds)


def _ghi_gallery(
    thu_muc_gallery: Path,
    backend: _BackendGia,
    nguoi_enroll: dict[str, list[Path]],
    duong_dan_vao: Path,
    *,
    them_thieu_anh: dict[str, int] | None = None,
    commit: str = "abc123def456",
    git_dirty: bool = False,
    min_images_per_user_da_dung: int = 3,
) -> None:
    """Dựng một thư mục gallery hợp lệ ở chế độ 'tep': .npy + manifest.csv + gallery.meta.json."""
    thu_muc_gallery.mkdir(parents=True, exist_ok=True)
    ban_ghi: list[dict] = []
    for uid, danh_sach in nguoi_enroll.items():
        anh_arrays = [cv2.imread(str(p)) for p in danh_sach]
        vec = backend.enroll(anh_arrays, {"min_images_per_user": len(danh_sach)})
        np.save(thu_muc_gallery / f"{uid}.npy", vec)
        ban_ghi.append(
            {
                "user_id": uid,
                "so_anh_tim_thay": len(danh_sach),
                "so_anh_dung": len(danh_sach),
                "trang_thai": "da_dang_ky",
                "so_chieu": backend.so_chieu,
                "tep_ra": f"{uid}.npy",
            }
        )
    for uid, n in (them_thieu_anh or {}).items():
        ban_ghi.append(
            {
                "user_id": uid,
                "so_anh_tim_thay": n,
                "so_anh_dung": 0,
                "trang_thai": "thieu_anh",
                "so_chieu": "",
                "tep_ra": "",
            }
        )

    cot = ["user_id", "so_anh_tim_thay", "so_anh_dung", "trang_thai", "so_chieu", "tep_ra"]
    with open(thu_muc_gallery / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cot)
        w.writeheader()
        w.writerows(ban_ghi)

    meta = {
        "backend": "dlib",
        "so_chieu": backend.so_chieu,
        "duong_dan_vao": str(duong_dan_vao),
        "so_nguoi_da_dang_ky": len(nguoi_enroll),
        "so_nguoi_bo_qua": len(them_thieu_anh or {}),
        "min_images_per_user_da_dung": min_images_per_user_da_dung,
        "commit": commit,
        "git_dirty": git_dirty,
        "moi_truong": "pc_x86",
    }
    with open(thu_muc_gallery / "gallery.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)


def _cfg_yaml(tmp_path: Path, so_buoc_nguong: int = 10, far_muc_tieu: float = 0.5) -> Path:
    cfg = {
        "backend": "dlib",
        "enroll": {"gallery_dir": "khong_dung_toi", "min_images_per_user": 2},
        "benchmark": {"so_buoc_nguong": so_buoc_nguong, "far_muc_tieu": far_muc_tieu},
    }
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")
    return p


def _dung_va_chay_co_ban(
    tmp_path: Path,
    monkeypatch,
    *,
    nguoi_gallery: dict[str, int] | None = None,
    nguoi_probe: dict[str, int] | None = None,
    nguoi_impostor: dict[str, int] | None = None,
    tap: str = "kiem-chuc-nang",
    danh_sach_impostor: list[str] | None = None,
    argv_bo_sung: list[str] | None = None,
    so_buoc_nguong: int = 10,
    far_muc_tieu: float = 0.5,
    luon_loi_enroll: bool = False,
    them_thieu_anh: dict[str, int] | None = None,
    xac_dinh_moi_truong_gia: str | None = None,
    bo_dem=None,
    truoc_khi_chay=None,
) -> dict:
    """Dựng môi trường tối thiểu (chế độ 'tep') và chạy `main()` một lượt.

    Trả về thông tin đủ để mọi ca test §8.4 trở đi kiểm tra kết quả.
    """
    nguoi_gallery = nguoi_gallery or {"u1": 2}
    nguoi_probe = nguoi_probe if nguoi_probe is not None else {uid: 2 for uid in nguoi_gallery}
    nguoi_impostor = nguoi_impostor or {}

    enroll_root = tmp_path / "enroll"
    probe_root = tmp_path / "probe"
    gallery_dir = tmp_path / "gallery"

    backend = _BackendGia(luon_loi_enroll=luon_loi_enroll)
    nguoi_enroll_anh = {
        uid: _tao_anh_nguoi(enroll_root, uid, n, bo_dem=bo_dem) for uid, n in nguoi_gallery.items()
    }
    if not luon_loi_enroll:
        _ghi_gallery(
            gallery_dir, backend, nguoi_enroll_anh, enroll_root, them_thieu_anh=them_thieu_anh
        )

    for uid, n in nguoi_probe.items():
        _tao_anh_nguoi(probe_root, uid, n, bo_dem=bo_dem, ten_prefix="probe")
    for uid, n in nguoi_impostor.items():
        _tao_anh_nguoi(probe_root, uid, n, bo_dem=bo_dem, ten_prefix="impostor")

    if truoc_khi_chay is not None:
        truoc_khi_chay(
            {"enroll_root": enroll_root, "probe_root": probe_root, "gallery_dir": gallery_dir}
        )

    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(br, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    monkeypatch.setattr(br, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    if xac_dinh_moi_truong_gia is not None:
        monkeypatch.setattr(br, "xac_dinh_moi_truong", lambda: xac_dinh_moi_truong_gia)

    cfg_path = _cfg_yaml(tmp_path, so_buoc_nguong=so_buoc_nguong, far_muc_tieu=far_muc_tieu)

    tep_impostor = None
    if danh_sach_impostor is not None:
        tep_impostor = tmp_path / "impostor.txt"
        tep_impostor.write_text("\n".join(danh_sach_impostor), encoding="utf-8")

    argv = [
        "--vao",
        str(probe_root),
        "--backend",
        "dlib",
        "--tap",
        tap,
        "--device-name",
        "test",
        "--gallery-dir",
        str(gallery_dir),
        "--config",
        str(cfg_path),
    ]
    if tep_impostor is not None:
        argv += ["--danh-sach-impostor", str(tep_impostor)]
    if argv_bo_sung:
        argv += argv_bo_sung

    ma = br.main(argv)
    return {
        "ma": ma,
        "thu_muc_kq": thu_muc_kq,
        "backend": backend,
        "gallery_dir": gallery_dir,
        "enroll_root": enroll_root,
        "probe_root": probe_root,
        "cfg_path": cfg_path,
    }


def _doc_csv_tho(thu_muc: Path) -> list[dict]:
    (p,) = [p for p in thu_muc.glob("*.csv") if ".nguong." not in p.name]
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _doc_csv_nguong(thu_muc: Path) -> list[dict]:
    (p,) = list(thu_muc.glob("*.nguong.csv"))
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _doc_meta(thu_muc: Path) -> dict:
    (p,) = list(thu_muc.glob("*.meta.json"))
    return json.loads(p.read_text(encoding="utf-8"))


def _bg(user_id_that: str, nhan: str, top1_user, top1_score: float) -> dict:
    """Bản ghi tối giản cho các ca §8.6 (quét ngưỡng) — dựng bằng tay, không chạy mô hình."""
    return {
        "user_id_that": user_id_that,
        "nhan": nhan,
        "top1_user": top1_user,
        "top1_score": top1_score,
    }


def _dong_nguong(nguong: float, far, frr, accuracy: float = 0.5) -> dict:
    """Một dòng bảng quét ngưỡng dựng bằng tay, cho các ca §8.7 (chốt điểm cân bằng)."""
    return {"nguong": nguong, "far": far, "frr": frr, "accuracy": accuracy}


def _bg_latency(latencies: list[float]) -> list[dict]:
    return [
        {
            "latency_trich_ms": lat / 2,
            "latency_so_khop_ms": lat / 2,
            "latency_identify_ms": lat,
        }
        for lat in latencies
    ]


def _meta_hop_le(**overrides) -> dict:
    meta = {
        "run_id": "bench_recognize_dlib_20260906_1200",
        "timestamp": "2026-09-06T12:00:00+07:00",
        "git_commit": "abc",
        "git_dirty": False,
        "git_dirty_toan_cay": False,
        "script": "scripts/benchmark_recognize.py",
        "command": "python scripts/benchmark_recognize.py --device-name test",
        "device": {"name": "test", "os": "x", "machine": "x", "processor": "x"},
        "moi_truong": "pc_x86",
        "software": {
            "python": "3.12",
            "onnxruntime": "1.0",
            "opencv-python": "4.0",
            "numpy": "2.0",
            "dlib-bin": "20.0",
        },
        "config_file": "configs/recognize.yaml",
        "config_snapshot": {},
        "backend": "dlib",
        "tap": "val",
        "dataset": {},
        "seed": 42,
        "warmup_probes": 10,
        "cpu_temp_start_c": None,
        "cpu_temp_max_c": None,
        "duration_s": 1.0,
        "notes": "",
        "tep_ket_qua": {},
        "tom_tat": {},
    }
    meta.update(overrides)
    return meta


def _ban_ghi_tho_mau() -> list[dict]:
    return [
        {
            "run_id": "r",
            "backend": "dlib",
            "tap": "val",
            "user_id_that": "u1",
            "nhan": "genuine",
            "anh_bam": "abc123456789",
            "top1_user": "u1",
            "top1_score": 0.9,
            "diem_dung_nguoi": 0.9,
            "so_chieu": 4,
            "latency_trich_ms": 1.0,
            "latency_so_khop_ms": 1.0,
            "latency_identify_ms": 2.0,
            "cpu_temp_c": None,
        }
    ]


def _bang_nguong_mau() -> list[dict]:
    return [
        {
            "run_id": "r",
            "backend": "dlib",
            "tap": "val",
            "nguong": 0.5,
            "so_genuine": 1,
            "so_impostor": 0,
            "tp": 1,
            "fp_impostor": 0,
            "fp_nham_nguoi": 0,
            "fn": 0,
            "tn": 0,
            "far": "",
            "frr": 0.0,
            "ti_le_gan_nham": 0.0,
            "accuracy": 1.0,
            "precision": 1.0,
            "recall": 1.0,
        }
    ]


# ============================================================================
# §8.1 — mã băm và dấu vết tập ảnh (dòng 01-05)
# ============================================================================


def test_dong01_cung_noi_dung_khac_ten_cung_bam(tmp_path):
    a = _ghi_anh(tmp_path / "a.png", seed=1)
    b = tmp_path / "b.png"
    shutil.copyfile(a, b)
    assert br.bam_noi_dung(a) == br.bam_noi_dung(b)


def test_dong02_lech_mot_byte_khac_bam(tmp_path):
    a = _ghi_anh(tmp_path / "a.png", seed=1)
    c = _ghi_anh(tmp_path / "c.png", seed=2)
    assert br.bam_noi_dung(a) != br.bam_noi_dung(c)


def test_dong03_bat_bien_thu_tu(tmp_path):
    a = _ghi_anh(tmp_path / "a.png", seed=1)
    b = _ghi_anh(tmp_path / "b.png", seed=2)
    assert br.bam_danh_sach_tep([a, b], tmp_path) == br.bam_danh_sach_tep([b, a], tmp_path)


def test_dong04_doi_noi_dung_giu_ten_doi_bam(tmp_path):
    a = _ghi_anh(tmp_path / "a.png", seed=1)
    b = _ghi_anh(tmp_path / "b.png", seed=2)
    bam_truoc = br.bam_danh_sach_tep([a, b], tmp_path)
    _ghi_anh(a, seed=99)
    bam_sau = br.bam_danh_sach_tep([a, b], tmp_path)
    assert bam_truoc != bam_sau


def test_dong05_doi_ten_giu_noi_dung_doi_bam(tmp_path):
    a = _ghi_anh(tmp_path / "a.png", seed=1)
    b = _ghi_anh(tmp_path / "b.png", seed=2)
    bam_truoc = br.bam_danh_sach_tep([a, b], tmp_path)
    a2 = tmp_path / "a2.png"
    shutil.copyfile(a, a2)
    bam_sau = br.bam_danh_sach_tep([a2, b], tmp_path)
    assert bam_truoc != bam_sau


# ============================================================================
# §8.2 — liệt kê ảnh và chia enroll/probe (dòng 06-20)
# ============================================================================


def test_dong06_khoa_la_ten_thu_muc_con(tmp_path):
    (tmp_path / "u1").mkdir()
    (tmp_path / "u2").mkdir()
    assert set(br.liet_ke_anh_theo_nguoi(tmp_path)) == {"u1", "u2"}


def test_dong07_bo_tep_khong_phai_anh(tmp_path):
    d = tmp_path / "u1"
    d.mkdir()
    (d / "a.jpg").write_bytes(b"x")
    (d / "ghi_chu.txt").write_bytes(b"y")
    kq = br.liet_ke_anh_theo_nguoi(tmp_path)
    assert len(kq["u1"]) == 1


def test_dong08_thu_muc_khong_ton_tai(tmp_path):
    with pytest.raises(LoiCauHinh):
        br.liet_ke_anh_theo_nguoi(tmp_path / "khong_ton_tai")


def test_dong09_khong_thu_muc_con(tmp_path):
    d = tmp_path / "rong"
    d.mkdir()
    with pytest.raises(LoiCauHinh, match="rỗng"):
        br.liet_ke_anh_theo_nguoi(d)


def test_dong10_du_k_cong_1_anh_dung_k_vao_enroll(tmp_path):
    ds = {"u1": [tmp_path / f"u1_{i}.jpg" for i in range(4)]}
    for p in ds["u1"]:
        p.write_bytes(b"x")
    enroll, _ = br.chia_enroll_probe(ds, 3, seed=42)
    assert len(enroll["u1"]) == 3


def test_dong11_enroll_probe_giao_rong(tmp_path):
    ds = {"u1": [tmp_path / f"u1_{i}.jpg" for i in range(4)]}
    for p in ds["u1"]:
        p.write_bytes(b"x")
    enroll, probe = br.chia_enroll_probe(ds, 3, seed=42)
    assert set(enroll["u1"]) & set(probe["u1"]) == set()


def test_dong12_dung_k_anh_khong_duoc_dang_ky(tmp_path):
    ds = {"u2": [tmp_path / f"u2_{i}.jpg" for i in range(3)]}
    for p in ds["u2"]:
        p.write_bytes(b"x")
    enroll, _ = br.chia_enroll_probe(ds, 3, seed=42)
    assert "u2" not in enroll


def test_dong13_dung_k_anh_toan_bo_vao_probe(tmp_path):
    ds = {"u2": [tmp_path / f"u2_{i}.jpg" for i in range(3)]}
    for p in ds["u2"]:
        p.write_bytes(b"x")
    _, probe = br.chia_enroll_probe(ds, 3, seed=42)
    assert len(probe["u2"]) == 3


def test_dong14_cung_seed_cung_phep_chia(tmp_path):
    ds = {"u1": [tmp_path / f"u1_{i}.jpg" for i in range(6)]}
    for p in ds["u1"]:
        p.write_bytes(b"x")
    assert br.chia_enroll_probe(ds, 2, 42) == br.chia_enroll_probe(ds, 2, 42)


def test_dong15_khac_seed_khac_phep_chia(tmp_path):
    ds = {"u1": [tmp_path / f"u1_{i}.jpg" for i in range(6)]}
    for p in ds["u1"]:
        p.write_bytes(b"x")
    assert br.chia_enroll_probe(ds, 2, 42) != br.chia_enroll_probe(ds, 2, 7)


def test_dong16_them_danh_tinh_khong_doi_phan_chia_cu(tmp_path):
    ds_u1 = [tmp_path / f"u1_{i}.jpg" for i in range(6)]
    ds_u9 = [tmp_path / f"u9_{i}.jpg" for i in range(6)]
    for p in ds_u1 + ds_u9:
        p.write_bytes(b"x")
    kq1 = br.chia_enroll_probe({"u1": ds_u1}, 2, 42)
    # "u9" đặt TRƯỚC "u1" trong từ điển một cách CỐ Ý: nếu cài đặt dùng một
    # random.Random(seed) DÙNG CHUNG cho cả lượt thay vì một bộ sinh riêng cho mỗi người,
    # lệnh rng.sample() xử lý "u9" trước sẽ tiêu tốn trạng thái ngẫu nhiên rồi mới tới "u1",
    # làm lệch kết quả của "u1" so với kq1. Đặt "u1" trước cả hai lệnh gọi (như bản đầu) sẽ
    # không bắt được lỗi này, vì "u1" luôn là ảnh hưởng ĐẦU TIÊN lên rng dùng chung.
    kq2 = br.chia_enroll_probe({"u9": ds_u9, "u1": ds_u1}, 2, 42)
    assert kq1[0]["u1"] == kq2[0]["u1"]


def test_dong17_so_anh_enroll_am_loi(tmp_path):
    with pytest.raises(LoiCauHinh):
        br.chia_enroll_probe({"u1": []}, 0, 42)


def test_dong18_backend_loi_enroll_nem_loi_mo_hinh(tmp_path):
    backend = _BackendGia(luon_loi_enroll=True)
    anh_enroll = {"u1": _tao_anh_nguoi(tmp_path, "u1", 3)}
    with pytest.raises(LoiMoHinh):
        br.dung_gallery_trong_bo_nho(anh_enroll, backend, 3)


def test_dong19_backend_binh_thuong_dung_du_nguoi(tmp_path):
    backend = _BackendGia()
    anh_enroll = {
        "u1": _tao_anh_nguoi(tmp_path, "u1", 3),
        "u2": _tao_anh_nguoi(tmp_path, "u2", 3),
    }
    gallery = br.dung_gallery_trong_bo_nho(anh_enroll, backend, 3)
    assert len(gallery) == 2


def test_dong20_goi_enroll_dung_mot_lan_moi_nguoi(tmp_path):
    backend = _BackendGia()
    anh_enroll = {
        "u1": _tao_anh_nguoi(tmp_path, "u1", 3),
        "u2": _tao_anh_nguoi(tmp_path, "u2", 3),
    }
    br.dung_gallery_trong_bo_nho(anh_enroll, backend, 3)
    assert backend.so_lan_enroll == 2


# ============================================================================
# §8.3 — nạp gallery từ đĩa (dòng 21-28)
# ============================================================================


def _ghi_manifest_tho(thu_muc: Path, rows: list[dict]) -> None:
    cot = ["user_id", "so_anh_tim_thay", "so_anh_dung", "trang_thai", "so_chieu", "tep_ra"]
    with open(thu_muc / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cot)
        w.writeheader()
        w.writerows(rows)


def _ghi_meta_tho(thu_muc: Path, **overrides) -> None:
    meta = {
        "so_chieu": 4,
        "duong_dan_vao": "x",
        "commit": "abc",
        "git_dirty": False,
        "min_images_per_user_da_dung": 3,
        "so_nguoi_da_dang_ky": 1,
        "so_nguoi_bo_qua": 0,
        "moi_truong": "pc_x86",
    }
    meta.update(overrides)
    with open(thu_muc / "gallery.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f)


def test_dong21_nap_du_nguoi(tmp_path):
    gd = tmp_path / "gallery"
    gd.mkdir()
    np.save(gd / "u1.npy", np.zeros(4, dtype=np.float32))
    np.save(gd / "u2.npy", np.zeros(4, dtype=np.float32))
    _ghi_manifest_tho(
        gd,
        [
            {
                "user_id": "u1",
                "so_anh_tim_thay": 3,
                "so_anh_dung": 3,
                "trang_thai": "da_dang_ky",
                "so_chieu": 4,
                "tep_ra": "u1.npy",
            },
            {
                "user_id": "u2",
                "so_anh_tim_thay": 3,
                "so_anh_dung": 3,
                "trang_thai": "da_dang_ky",
                "so_chieu": 4,
                "tep_ra": "u2.npy",
            },
        ],
    )
    _ghi_meta_tho(gd, so_chieu=4)
    gallery, _, _ = br.nap_gallery_tu_dia(gd)
    assert set(gallery) == {"u1", "u2"}


def test_dong22_khong_de_quy(tmp_path):
    gd = tmp_path / "gallery"
    gd.mkdir()
    np.save(gd / "u1.npy", np.zeros(4, dtype=np.float32))
    (gd / "con").mkdir()
    np.save(gd / "con" / "y.npy", np.zeros(4, dtype=np.float32))
    _ghi_manifest_tho(
        gd,
        [
            {
                "user_id": "u1",
                "so_anh_tim_thay": 3,
                "so_anh_dung": 3,
                "trang_thai": "da_dang_ky",
                "so_chieu": 4,
                "tep_ra": "u1.npy",
            }
        ],
    )
    _ghi_meta_tho(gd, so_chieu=4)
    gallery, _, _ = br.nap_gallery_tu_dia(gd)
    assert "y" not in gallery


def test_dong23_thieu_manifest(tmp_path):
    gd = tmp_path / "gallery"
    gd.mkdir()
    _ghi_meta_tho(gd)
    with pytest.raises(LoiCauHinh, match="manifest.csv"):
        br.nap_gallery_tu_dia(gd)


def test_dong24_thieu_meta(tmp_path):
    gd = tmp_path / "gallery"
    gd.mkdir()
    _ghi_manifest_tho(gd, [])
    with pytest.raises(LoiCauHinh, match="gallery.meta.json"):
        br.nap_gallery_tu_dia(gd)


def test_dong25_vecto_lech_so_chieu(tmp_path):
    gd = tmp_path / "gallery"
    gd.mkdir()
    np.save(gd / "u1.npy", np.zeros(8, dtype=np.float32))
    _ghi_manifest_tho(
        gd,
        [
            {
                "user_id": "u1",
                "so_anh_tim_thay": 3,
                "so_anh_dung": 3,
                "trang_thai": "da_dang_ky",
                "so_chieu": 4,
                "tep_ra": "u1.npy",
            }
        ],
    )
    _ghi_meta_tho(gd, so_chieu=4)
    with pytest.raises(LoiCauHinh, match=r"\(8,\)"):
        br.nap_gallery_tu_dia(gd)


def test_dong26_du_tep_dung_so_chieu_nap_duoc(tmp_path):
    gd = tmp_path / "gallery"
    gd.mkdir()
    np.save(gd / "u1.npy", np.zeros(4, dtype=np.float32))
    np.save(gd / "u2.npy", np.zeros(4, dtype=np.float32))
    _ghi_manifest_tho(
        gd,
        [
            {
                "user_id": "u1",
                "so_anh_tim_thay": 3,
                "so_anh_dung": 3,
                "trang_thai": "da_dang_ky",
                "so_chieu": 4,
                "tep_ra": "u1.npy",
            },
            {
                "user_id": "u2",
                "so_anh_tim_thay": 3,
                "so_anh_dung": 3,
                "trang_thai": "da_dang_ky",
                "so_chieu": 4,
                "tep_ra": "u2.npy",
            },
        ],
    )
    _ghi_meta_tho(gd, so_chieu=4)
    gallery, _, _ = br.nap_gallery_tu_dia(gd)
    assert len(gallery) == 2


def test_dong27_thu_muc_khong_ton_tai_liet_ke_backend(tmp_path):
    cha = tmp_path / "cha"
    (cha / "dlib").mkdir(parents=True)
    (cha / ".dlib.dang-ghi").mkdir(parents=True)
    with pytest.raises(LoiCauHinh, match="dlib"):
        br.nap_gallery_tu_dia(cha / "arcface")


def test_dong28_khong_liet_ke_thu_muc_dau_cham(tmp_path):
    cha = tmp_path / "cha"
    (cha / "dlib").mkdir(parents=True)
    (cha / ".dlib.dang-ghi").mkdir(parents=True)
    with pytest.raises(LoiCauHinh) as exc:
        br.nap_gallery_tu_dia(cha / "arcface")
    assert "dang-ghi" not in str(exc.value)


# ============================================================================
# §8.4 — loại ảnh đã đăng ký khỏi probe (dòng 29-40) — phần chịu lực
# ============================================================================


def test_dong29_chi_lay_nguoi_da_dang_ky(tmp_path):
    goc = tmp_path / "goc"
    _tao_anh_nguoi(goc, "u1", 3)
    meta_gallery = {"duong_dan_vao": str(goc)}
    manifest = [
        {"user_id": "u1", "so_anh_dung": "3", "trang_thai": "da_dang_ky"},
        {"user_id": "u2", "so_anh_dung": "0", "trang_thai": "thieu_anh"},
    ]
    kq = br.suy_tap_anh_da_dang_ky(meta_gallery, manifest, None)
    assert len(kq) == 3


def test_dong30_31_lech_so_anh_dung_neu_ca_hai_so(tmp_path):
    goc = tmp_path / "goc"
    _tao_anh_nguoi(goc, "u1", 2)
    meta_gallery = {"duong_dan_vao": str(goc)}
    manifest = [{"user_id": "u1", "so_anh_dung": "3", "trang_thai": "da_dang_ky"}]
    with pytest.raises(LoiCauHinh) as exc:
        br.suy_tap_anh_da_dang_ky(meta_gallery, manifest, None)
    assert "3" in str(exc.value)
    assert "2" in str(exc.value)


def test_dong32_so_khop_tra_ve_danh_sach(tmp_path):
    goc = tmp_path / "goc"
    _tao_anh_nguoi(goc, "u1", 3)
    meta_gallery = {"duong_dan_vao": str(goc)}
    manifest = [{"user_id": "u1", "so_anh_dung": "3", "trang_thai": "da_dang_ky"}]
    kq = br.suy_tap_anh_da_dang_ky(meta_gallery, manifest, None)
    assert len(kq) == 3


def test_dong33_duong_dan_vao_dau_gach_cheo_nguoc(tmp_path):
    goc = tmp_path / "a" / "b"
    _tao_anh_nguoi(goc, "u1", 2)
    duong_dan_windows = str(tmp_path / "a") + "\\b"
    meta_gallery = {"duong_dan_vao": duong_dan_windows}
    manifest = [{"user_id": "u1", "so_anh_dung": "2", "trang_thai": "da_dang_ky"}]
    kq = br.suy_tap_anh_da_dang_ky(meta_gallery, manifest, None)
    assert len(kq) == 2


def test_dong34_probe_trung_duong_dan_tuong_doi_bi_loai(tmp_path, monkeypatch):
    enroll_root = tmp_path / "enroll"
    probe_root = tmp_path / "probe"
    gallery_dir = tmp_path / "gallery"
    backend = _BackendGia()

    ds_u1 = _tao_anh_nguoi(enroll_root, "u1", 2)
    _ghi_gallery(gallery_dir, backend, {"u1": ds_u1}, enroll_root)

    ten_trung = ds_u1[0].name
    (probe_root / "u1").mkdir(parents=True)
    shutil.copyfile(ds_u1[0], probe_root / "u1" / ten_trung)
    _tao_anh_nguoi(probe_root, "u1", 1, ten_prefix="moi")

    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(br, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    monkeypatch.setattr(br, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    cfg_path = _cfg_yaml(tmp_path)

    ma = br.main(
        [
            "--vao",
            str(probe_root),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--gallery-dir",
            str(gallery_dir),
            "--config",
            str(cfg_path),
        ]
    )
    assert ma == 0

    bam_bi_loai = br.bam_noi_dung(ds_u1[0])[:12]
    rows = _doc_csv_tho(thu_muc_kq)
    assert bam_bi_loai not in {r["anh_bam"] for r in rows}


def test_dong35_probe_ban_sao_khac_ten_van_bi_loai(tmp_path, monkeypatch):
    enroll_root = tmp_path / "enroll"
    probe_root = tmp_path / "probe"
    gallery_dir = tmp_path / "gallery"
    backend = _BackendGia()

    ds_u1 = _tao_anh_nguoi(enroll_root, "u1", 2)
    _ghi_gallery(gallery_dir, backend, {"u1": ds_u1}, enroll_root)

    (probe_root / "u1").mkdir(parents=True)
    shutil.copyfile(ds_u1[0], probe_root / "u1" / "ten_khac.png")
    _tao_anh_nguoi(probe_root, "u1", 1, ten_prefix="moi")

    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(br, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    monkeypatch.setattr(br, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    cfg_path = _cfg_yaml(tmp_path)

    ma = br.main(
        [
            "--vao",
            str(probe_root),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--gallery-dir",
            str(gallery_dir),
            "--config",
            str(cfg_path),
        ]
    )
    assert ma == 0

    bam_bi_loai = br.bam_noi_dung(ds_u1[0])[:12]
    rows = _doc_csv_tho(thu_muc_kq)
    assert bam_bi_loai not in {r["anh_bam"] for r in rows}


def test_dong36a_khong_con_genuine_tra_ve_1(tmp_path, monkeypatch, capsys):
    enroll_root = tmp_path / "enroll"
    gallery_dir = tmp_path / "gallery"
    backend = _BackendGia()
    ds_u1 = _tao_anh_nguoi(enroll_root, "u1", 2)
    _ghi_gallery(gallery_dir, backend, {"u1": ds_u1}, enroll_root)

    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(br, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    monkeypatch.setattr(br, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    cfg_path = _cfg_yaml(tmp_path)

    # --vao == enroll_root: mọi probe của u1 trùng khít ảnh đã đăng ký -> không còn genuine.
    ma = br.main(
        [
            "--vao",
            str(enroll_root),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--gallery-dir",
            str(gallery_dir),
            "--config",
            str(cfg_path),
        ]
    )
    assert ma == 1
    out = capsys.readouterr().out
    assert "genuine" in out


def test_dong37_khong_ghi_tep_nao_khi_khong_con_genuine(tmp_path, monkeypatch):
    enroll_root = tmp_path / "enroll"
    gallery_dir = tmp_path / "gallery"
    backend = _BackendGia()
    ds_u1 = _tao_anh_nguoi(enroll_root, "u1", 2)
    _ghi_gallery(gallery_dir, backend, {"u1": ds_u1}, enroll_root)

    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(br, "tao_bo_nhan_dien", lambda cfg, ten: backend)
    monkeypatch.setattr(br, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    cfg_path = _cfg_yaml(tmp_path)

    br.main(
        [
            "--vao",
            str(enroll_root),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--gallery-dir",
            str(gallery_dir),
            "--config",
            str(cfg_path),
        ]
    )
    assert list(thu_muc_kq.rglob("*")) == []


def test_dong38_con_genuine_tra_ve_0(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    assert kq["ma"] == 0


def test_dong39_co_dong_genuine_trong_csv(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    rows = _doc_csv_tho(kq["thu_muc_kq"])
    assert sum(1 for r in rows if r["nhan"] == "genuine") >= 1


def test_dong40_impostor_gan_nhan_dung(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, nguoi_impostor={"u9": 2})
    rows = _doc_csv_tho(kq["thu_muc_kq"])
    assert {r["nhan"] for r in rows if r["user_id_that"] == "u9"} == {"impostor"}


# ============================================================================
# §8.5 — chia tập val/test (dòng 41-49)
# ============================================================================


def test_dong41a_val_thieu_danh_sach_impostor(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, tap="val")
    assert kq["ma"] == 1


def test_dong41b_thong_bao_neu_ten_co(tmp_path, monkeypatch, capsys):
    _dung_va_chay_co_ban(tmp_path, monkeypatch, tap="val")
    out = capsys.readouterr().out
    assert "--danh-sach-impostor" in out


def test_dong42a_test_thieu_danh_sach_impostor(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, tap="test")
    assert kq["ma"] == 1


def test_dong42b_thong_bao_neu_ten_co(tmp_path, monkeypatch, capsys):
    _dung_va_chay_co_ban(tmp_path, monkeypatch, tap="test")
    out = capsys.readouterr().out
    assert "--danh-sach-impostor" in out


def test_dong43_kiem_chuc_nang_canh_bao_khong_rong(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, tap="kiem-chuc-nang")
    meta = _doc_meta(kq["thu_muc_kq"])
    assert meta["canh_bao_chia_tap"] != ""


def test_dong44_val_khong_co_canh_bao_chia_tap(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(
        tmp_path, monkeypatch, tap="val", nguoi_impostor={"u9": 2}, danh_sach_impostor=["u9"]
    )
    meta = _doc_meta(kq["thu_muc_kq"])
    assert "canh_bao_chia_tap" not in meta


def test_dong45_danh_tinh_ngoai_tep_bi_loai(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(
        tmp_path,
        monkeypatch,
        tap="test",
        nguoi_impostor={"u8": 2, "u9": 2, "u7": 2, "u6": 2, "u5": 2},
        danh_sach_impostor=["u8", "u9"],
    )
    meta = _doc_meta(kq["thu_muc_kq"])
    assert meta["dataset"]["so_danh_tinh_impostor"] == 2


def test_dong46a_impostor_trung_gallery_tra_ve_1(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(
        tmp_path, monkeypatch, tap="test", nguoi_gallery={"u1": 2}, danh_sach_impostor=["u1"]
    )
    assert kq["ma"] == 1


def test_dong46b_thong_bao_neu_dich_danh(tmp_path, monkeypatch, capsys):
    _dung_va_chay_co_ban(
        tmp_path, monkeypatch, tap="test", nguoi_gallery={"u1": 2}, danh_sach_impostor=["u1"]
    )
    out = capsys.readouterr().out
    assert "u1" in out


def test_dong47_bo_dong_rong_va_hash(tmp_path):
    p = tmp_path / "ds.txt"
    p.write_text("a\n\n# comment\nb\n", encoding="utf-8")
    assert br.doc_danh_sach_danh_tinh(p) == ["a", "b"]


def test_dong48_khong_con_dong_hop_le(tmp_path):
    p = tmp_path / "ds.txt"
    p.write_text("\n# chỉ có comment\n", encoding="utf-8")
    with pytest.raises(LoiCauHinh):
        br.doc_danh_sach_danh_tinh(p)


def test_dong49_tap_ghi_vao_moi_dong(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(
        tmp_path, monkeypatch, tap="val", nguoi_impostor={"u9": 2}, danh_sach_impostor=["u9"]
    )
    rows = _doc_csv_tho(kq["thu_muc_kq"])
    assert {r["tap"] for r in rows} == {"val"}


# ============================================================================
# §8.6 — quét ngưỡng và chỉ số (dòng 50-64)
# ============================================================================


def test_dong50_dung_so_dong():
    bg = [_bg("u1", "genuine", "u1", 0.1), _bg("u1", "genuine", "u1", 0.9)]
    assert len(br.quet_nguong(bg, 200)) == 200


def test_dong51_nguong_dau_bang_min():
    scores = [0.1, 0.5, 0.9]
    bg = [_bg("u1", "genuine", "u1", s) for s in scores]
    bang = br.quet_nguong(bg, 10)
    assert bang[0]["nguong"] == pytest.approx(min(scores))


def test_dong52_nguong_cuoi_bang_max():
    scores = [0.1, 0.5, 0.9]
    bg = [_bg("u1", "genuine", "u1", s) for s in scores]
    bang = br.quet_nguong(bg, 10)
    assert bang[-1]["nguong"] == pytest.approx(max(scores))


def test_dong53_far_khong_tang():
    bg = [_bg("u1", "genuine", "u1", 0.9)] + [
        _bg(f"x{i}", "impostor", "u1", s) for i, s in enumerate([0.1, 0.4, 0.6, 0.8])
    ]
    bang = br.quet_nguong(bg, 20)
    assert all(bang[i]["far"] >= bang[i + 1]["far"] for i in range(len(bang) - 1))


def test_dong54_frr_khong_giam():
    bg = [_bg(f"u{i}", "genuine", f"u{i}", s) for i, s in enumerate([0.1, 0.4, 0.6, 0.8])]
    bang = br.quet_nguong(bg, 20)
    assert all(bang[i]["frr"] <= bang[i + 1]["frr"] for i in range(len(bang) - 1))


def test_dong55_far_dung_tren_vi_du_tay():
    bg = [_bg("g1", "genuine", "g1", 0.5)] + [
        _bg(f"x{i}", "impostor", "g1", s) for i, s in enumerate([0.1, 0.1, 0.1, 0.9])
    ]
    bang = br.quet_nguong(bg, 2)
    assert bang[-1]["far"] == pytest.approx(0.25)


def test_dong56_frr_dung_tren_vi_du_tay():
    bg = [_bg(f"g{i}", "genuine", f"g{i}", s) for i, s in enumerate([0.9, 0.9, 0.9, 0.1])]
    bg.append(_bg("x0", "impostor", "g0", 0.5))
    bang = br.quet_nguong(bg, 2)
    assert bang[-1]["frr"] == pytest.approx(0.25)


def test_dong57_ti_le_gan_nham_dung():
    bg = [_bg(f"g{i}", "genuine", "khac_nguoi", 0.1) for i in range(3)]
    bg.append(_bg("g3", "genuine", "nguoi_khac", 0.9))
    bg.append(_bg("x0", "impostor", "g0", 0.5))
    bang = br.quet_nguong(bg, 2)
    assert bang[-1]["ti_le_gan_nham"] == pytest.approx(0.25)


def test_dong58_accuracy_dung():
    bg = [
        _bg("g0", "genuine", "g0", 0.9),
        _bg("g1", "genuine", "g1", 0.1),
        _bg("x0", "impostor", "g0", 0.1),
        _bg("x1", "impostor", "g0", 0.9),
    ]
    bang = br.quet_nguong(bg, 2)
    assert bang[-1]["accuracy"] == pytest.approx((1 + 1) / 4)


def test_dong59_precision_tinh_ca_gan_nham():
    bg = [
        _bg("g0", "genuine", "g0", 0.9),
        _bg("g1", "genuine", "khac", 0.9),
        _bg("x0", "impostor", "g0", 0.9),
    ]
    bang = br.quet_nguong(bg, 2)
    assert bang[-1]["precision"] == pytest.approx(1 / 3)


def test_dong60_recall_dung():
    bg = [
        _bg("g0", "genuine", "g0", 0.9),
        _bg("g1", "genuine", "g1", 0.1),
        _bg("g2", "genuine", "g2", 0.1),
        _bg("x0", "impostor", "g0", 0.1),
    ]
    bang = br.quet_nguong(bg, 2)
    assert bang[-1]["recall"] == pytest.approx(1 / 3)


def test_dong61a_bang_dung_nguong_tinh_vao_tp():
    bg = [_bg("g0", "genuine", "g0", 0.9), _bg("x0", "impostor", "g0", 0.1)]
    bang = br.quet_nguong(bg, 2)
    assert bang[-1]["tp"] == 1


def test_dong61b_bang_dung_nguong_khong_vao_fn():
    bg = [_bg("g0", "genuine", "g0", 0.9), _bg("x0", "impostor", "g0", 0.1)]
    bang = br.quet_nguong(bg, 2)
    assert bang[-1]["fn"] == 0


def test_dong62_khong_impostor_far_rong():
    bg = [_bg("g0", "genuine", "g0", 0.9)]
    bang = br.quet_nguong(bg, 2)
    assert bang[0]["far"] == ""


def test_dong63_so_buoc_nho_hon_2():
    bg = [_bg("g0", "genuine", "g0", 0.9)]
    with pytest.raises(LoiCauHinh):
        br.quet_nguong(bg, 1)


def test_dong64_ban_ghi_rong():
    with pytest.raises(LoiCauHinh):
        br.quet_nguong([], 10)


# ============================================================================
# §8.7 — chốt điểm cân bằng (dòng 65-75)
# ============================================================================


def test_dong65_eer_diem_nho_nhat():
    bang = [
        _dong_nguong(0.1, 0.9, 0.1),
        _dong_nguong(0.5, 0.5, 0.5),
        _dong_nguong(0.9, 0.1, 0.9),
    ]
    kq = br.chot_diem_can_bang(bang, 0.5)
    assert kq["nguong_eer"] == 0.5


def test_dong66_hoa_eer_lay_nguong_nho_nhat():
    bang = [_dong_nguong(0.3, 0.7, 0.5), _dong_nguong(0.6, 0.5, 0.7)]
    kq = br.chot_diem_can_bang(bang, 0.5)
    assert kq["nguong_eer"] == 0.3


def test_dong67_nguong_far_muc_tieu_nho_nhat():
    bang = [
        _dong_nguong(0.4, 0.05, 0.9),
        _dong_nguong(0.6, 0.05, 0.5),
        _dong_nguong(0.8, 0.01, 0.3),
    ]
    kq = br.chot_diem_can_bang(bang, 0.1)
    assert kq["nguong_far_muc_tieu"] == 0.4


def test_dong68_khong_dat_tra_ve_none():
    bang = [_dong_nguong(0.5, 0.9, 0.1)]
    kq = br.chot_diem_can_bang(bang, 0.01)
    assert kq["nguong_far_muc_tieu"] is None


def test_dong69_main_van_tra_0_khi_khong_dat_far(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    assert kq["ma"] == 0
    meta = _doc_meta(kq["thu_muc_kq"])
    assert meta["tom_tat"]["nguong_far_muc_tieu"] is None


def test_dong70_far_muc_tieu_inf():
    bang = [_dong_nguong(0.5, 0.1, 0.1)]
    with pytest.raises(LoiCauHinh):
        br.chot_diem_can_bang(bang, float("inf"))


def test_dong71_far_muc_tieu_neg_inf():
    bang = [_dong_nguong(0.5, 0.1, 0.1)]
    with pytest.raises(LoiCauHinh):
        br.chot_diem_can_bang(bang, float("-inf"))


def test_dong72_far_muc_tieu_nan():
    bang = [_dong_nguong(0.5, 0.1, 0.1)]
    with pytest.raises(LoiCauHinh):
        br.chot_diem_can_bang(bang, float("nan"))


def test_dong73_far_muc_tieu_0():
    bang = [_dong_nguong(0.5, 0.1, 0.1)]
    with pytest.raises(LoiCauHinh):
        br.chot_diem_can_bang(bang, 0.0)


def test_dong74_far_muc_tieu_1_5():
    bang = [_dong_nguong(0.5, 0.1, 0.1)]
    with pytest.raises(LoiCauHinh):
        br.chot_diem_can_bang(bang, 1.5)


def test_dong75_far_muc_tieu_hop_le_khong_nem():
    bang = [_dong_nguong(0.5, 0.1, 0.1)]
    kq = br.chot_diem_can_bang(bang, 0.01)
    assert kq["eer"] >= 0.0


# ============================================================================
# §8.8 — tốc độ (dòng 76-82)
# ============================================================================


def test_dong76_p50_khop():
    v = list(range(1, 101))
    bg = _bg_latency(v)
    kq = br.tong_hop_toc_do(bg)
    assert kq["latency_p50_ms"] == pytest.approx(np.percentile(v, 50))


def test_dong77_p95_khop():
    v = list(range(1, 101))
    bg = _bg_latency(v)
    kq = br.tong_hop_toc_do(bg)
    assert kq["latency_p95_ms"] == pytest.approx(np.percentile(v, 95))


def test_dong78_do_lech_khop():
    v = list(range(1, 101))
    bg = _bg_latency(v)
    kq = br.tong_hop_toc_do(bg)
    assert kq["latency_do_lech_ms"] == pytest.approx(np.std(np.array(v, dtype=np.float64)))


def test_dong79_fps_suy_ra():
    bg = _bg_latency([50.0] * 10)
    kq = br.tong_hop_toc_do(bg)
    assert kq["fps_suy_ra"] == pytest.approx(20.0)


def test_dong80_identify_bang_trich_cong_so_khop(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    rows = _doc_csv_tho(kq["thu_muc_kq"])
    assert all(
        abs(
            float(r["latency_identify_ms"])
            - float(r["latency_trich_ms"])
            - float(r["latency_so_khop_ms"])
        )
        < 1e-6
        for r in rows
    )


def test_dong81_warmup_khong_hut_dong(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(
        tmp_path, monkeypatch, nguoi_probe={"u1": 10}, argv_bo_sung=["--warmup", "3"]
    )
    rows = _doc_csv_tho(kq["thu_muc_kq"])
    assert len(rows) == 10


def test_dong82_ban_ghi_rong_tong_hop_toc_do():
    with pytest.raises(LoiCauHinh):
        br.tong_hop_toc_do([])


# ============================================================================
# §8.9 — ghi tệp và metadata (dòng 83-106)
# ============================================================================


def test_dong83_ghi_dung_ba_tep(tmp_path):
    br.ghi_ket_qua(tmp_path, "r", _ban_ghi_tho_mau(), _bang_nguong_mau(), _meta_hop_le())
    assert len(list(tmp_path.iterdir())) == 3


def test_dong84_ten_csv_tho_dung_khuon(tmp_path):
    p_tho, _, _ = br.ghi_ket_qua(
        tmp_path,
        "bench_recognize_dlib_20260906_1200",
        _ban_ghi_tho_mau(),
        _bang_nguong_mau(),
        _meta_hop_le(),
    )
    assert re.fullmatch(r"bench_recognize_(dlib|arcface)_\d{8}_\d{4}\.csv", p_tho.name)


def test_dong85_ten_csv_nguong_dung_khuon(tmp_path):
    _, p_ng, _ = br.ghi_ket_qua(
        tmp_path,
        "bench_recognize_dlib_20260906_1200",
        _ban_ghi_tho_mau(),
        _bang_nguong_mau(),
        _meta_hop_le(),
    )
    assert re.fullmatch(r"bench_recognize_(dlib|arcface)_\d{8}_\d{4}\.nguong\.csv", p_ng.name)


def test_dong86_ten_meta_dung_khuon(tmp_path):
    _, _, p_meta = br.ghi_ket_qua(
        tmp_path,
        "bench_recognize_dlib_20260906_1200",
        _ban_ghi_tho_mau(),
        _bang_nguong_mau(),
        _meta_hop_le(),
    )
    assert re.fullmatch(r"bench_recognize_(dlib|arcface)_\d{8}_\d{4}\.meta\.json", p_meta.name)


def test_dong87_csv_tho_dung_14_cot(tmp_path):
    p_tho, _, _ = br.ghi_ket_qua(
        tmp_path, "r", _ban_ghi_tho_mau(), _bang_nguong_mau(), _meta_hop_le()
    )
    with open(p_tho, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    # Danh sách nguyên văn chép từ §7.4 đặc tả — không tham chiếu hằng số của module đang bị kiểm.
    assert header == [
        "run_id",
        "backend",
        "tap",
        "user_id_that",
        "nhan",
        "anh_bam",
        "top1_user",
        "top1_score",
        "diem_dung_nguoi",
        "so_chieu",
        "latency_trich_ms",
        "latency_so_khop_ms",
        "latency_identify_ms",
        "cpu_temp_c",
    ]


def test_dong88_csv_nguong_dung_17_cot(tmp_path):
    _, p_ng, _ = br.ghi_ket_qua(
        tmp_path, "r", _ban_ghi_tho_mau(), _bang_nguong_mau(), _meta_hop_le()
    )
    with open(p_ng, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    # Danh sách nguyên văn chép từ §7.4 đặc tả — không tham chiếu hằng số của module đang bị kiểm.
    assert header == [
        "run_id",
        "backend",
        "tap",
        "nguong",
        "so_genuine",
        "so_impostor",
        "tp",
        "fp_impostor",
        "fp_nham_nguoi",
        "fn",
        "tn",
        "far",
        "frr",
        "ti_le_gan_nham",
        "accuracy",
        "precision",
        "recall",
    ]


def test_dong89_so_dong_bang_so_anh_probe(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    rows = _doc_csv_tho(kq["thu_muc_kq"])
    meta = _doc_meta(kq["thu_muc_kq"])
    assert len(rows) == meta["dataset"]["so_anh_probe"]


def test_dong90_so_dong_nguong_bang_so_buoc(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, so_buoc_nguong=200)
    rows_ng = _doc_csv_nguong(kq["thu_muc_kq"])
    assert len(rows_ng) == 200


def test_dong91_meta_du_23_khoa(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    # Tập khoá nguyên văn chép từ §7.4 đặc tả — không tham chiếu hằng số của module đang bị kiểm.
    assert set(meta) >= {
        "run_id",
        "timestamp",
        "git_commit",
        "git_dirty",
        "git_dirty_toan_cay",
        "script",
        "command",
        "device",
        "moi_truong",
        "software",
        "config_file",
        "config_snapshot",
        "backend",
        "tap",
        "dataset",
        "seed",
        "warmup_probes",
        "cpu_temp_start_c",
        "cpu_temp_max_c",
        "duration_s",
        "notes",
        "tep_ket_qua",
        "tom_tat",
    }


def test_dong92_device_du_bon_truong(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert set(meta["device"]) >= {"name", "os", "machine", "processor"}


def test_dong93_software_du_nam_khoa(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert set(meta["software"]) >= {
        "python",
        "onnxruntime",
        "opencv-python",
        "numpy",
        "dlib-bin",
    }


def test_dong94_tep_ket_qua_du_ba_khoa(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert set(meta["tep_ket_qua"]) == {"tho", "nguong", "meta"}


def test_dong95_dataset_du_16_khoa(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert set(meta["dataset"]) >= {
        "che_do_gallery",
        "gallery_dir",
        "gallery_commit",
        "gallery_git_dirty",
        "gallery_so_nguoi_da_dang_ky",
        "gallery_min_images_per_user_da_dung",
        "so_anh_enroll_moi_nguoi",
        "anh_dir",
        "tep_danh_sach_impostor",
        "so_nguoi_gallery",
        "so_anh_da_dang_ky",
        "bam_danh_sach_anh_da_dang_ky",
        "so_anh_probe",
        "so_anh_bo_qua",
        "so_danh_tinh_impostor",
        "bam_danh_sach_anh_probe",
    }


def test_dong96_ghi_lai_commit_gallery(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    gallery_meta = json.loads((kq["gallery_dir"] / "gallery.meta.json").read_text(encoding="utf-8"))
    assert meta["dataset"]["gallery_commit"] == gallery_meta["commit"]


def test_dong97_ghi_lai_min_images(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert meta["dataset"]["gallery_min_images_per_user_da_dung"] == 3


def test_dong98_bam_probe_tren_anh_do_duoc(tmp_path, monkeypatch):
    bo_dem1 = itertools.count(5000)
    kq1 = _dung_va_chay_co_ban(tmp_path / "a", monkeypatch, bo_dem=bo_dem1)
    meta1 = _doc_meta(kq1["thu_muc_kq"])

    bo_dem2 = itertools.count(5000)

    def _them_anh_hong(duong_dan: dict) -> None:
        (duong_dan["probe_root"] / "u1" / "hong.png").write_bytes(b"")

    kq2 = _dung_va_chay_co_ban(
        tmp_path / "b", monkeypatch, bo_dem=bo_dem2, truoc_khi_chay=_them_anh_hong
    )
    meta2 = _doc_meta(kq2["thu_muc_kq"])

    assert (
        meta2["dataset"]["bam_danh_sach_anh_probe"] == meta1["dataset"]["bam_danh_sach_anh_probe"]
    )


def test_dong99_anh_hong_duoc_dem(tmp_path, monkeypatch):
    def _them_anh_hong(duong_dan: dict) -> None:
        (duong_dan["probe_root"] / "u1" / "hong.png").write_bytes(b"")

    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, truoc_khi_chay=_them_anh_hong)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert meta["dataset"]["so_anh_bo_qua"] == 1


def test_dong100_canh_bao_anh_bo_qua_khong_rong(tmp_path, monkeypatch):
    def _them_anh_hong(duong_dan: dict) -> None:
        (duong_dan["probe_root"] / "u1" / "hong.png").write_bytes(b"")

    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, truoc_khi_chay=_them_anh_hong)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert meta["canh_bao_anh_bo_qua"] != ""


def test_dong101_khong_anh_hong_khong_co_khoa(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert "canh_bao_anh_bo_qua" not in meta


def test_dong102_meta_thieu_khoa(tmp_path):
    with pytest.raises(LoiCauHinh):
        br.ghi_ket_qua(tmp_path, "r", _ban_ghi_tho_mau(), _bang_nguong_mau(), {})


def test_dong103_du_khoa_ghi_thanh_cong(tmp_path):
    p_tho, p_ng, p_meta = br.ghi_ket_qua(
        tmp_path, "r", _ban_ghi_tho_mau(), _bang_nguong_mau(), _meta_hop_le()
    )
    assert p_tho.exists() and p_ng.exists() and p_meta.exists()


def test_dong104_tu_choi_ghi_de(tmp_path):
    (tmp_path / "r.csv").write_text("cu", encoding="utf-8")
    with pytest.raises(LoiCauHinh):
        br.ghi_ket_qua(tmp_path, "r", _ban_ghi_tho_mau(), _bang_nguong_mau(), _meta_hop_le())


def test_dong105_noi_dung_cu_nguyen_ven(tmp_path):
    (tmp_path / "r.csv").write_text("cu", encoding="utf-8")
    with pytest.raises(LoiCauHinh):
        br.ghi_ket_qua(tmp_path, "r", _ban_ghi_tho_mau(), _bang_nguong_mau(), _meta_hop_le())
    assert (tmp_path / "r.csv").read_text(encoding="utf-8") == "cu"


def test_dong106_cpu_temp_rong_khong_phai_none(tmp_path, monkeypatch):
    monkeypatch.setattr(br, "doc_nhiet_do_cpu", lambda: None)
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    rows = _doc_csv_tho(kq["thu_muc_kq"])
    assert all(r["cpu_temp_c"] == "" for r in rows)


# ============================================================================
# §8.10 — cấu hình, CLI và cảnh báo (dòng 107-128)
# ============================================================================


def test_dong107a_thieu_device_name(tmp_path):
    ma = br.main(["--vao", str(tmp_path), "--backend", "dlib", "--tap", "kiem-chuc-nang"])
    assert ma == 1


def test_dong107b_thong_bao_neu_ten_co(tmp_path, capsys):
    br.main(["--vao", str(tmp_path), "--backend", "dlib", "--tap", "kiem-chuc-nang"])
    out = capsys.readouterr().out
    assert "device-name" in out


def test_dong108_thieu_tap_system_exit(tmp_path):
    with pytest.raises(SystemExit):
        br.main(["--vao", str(tmp_path), "--backend", "dlib", "--device-name", "test"])


def test_dong109a_thieu_so_buoc_nguong(tmp_path):
    cfg = {"benchmark": {"far_muc_tieu": 0.5}}
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    ma = br.main(
        [
            "--vao",
            str(tmp_path),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--config",
            str(p),
        ]
    )
    assert ma == 1


def test_dong109b_thong_bao_neu_dich_danh(tmp_path, capsys):
    cfg = {"benchmark": {"far_muc_tieu": 0.5}}
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    br.main(
        [
            "--vao",
            str(tmp_path),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--config",
            str(p),
        ]
    )
    out = capsys.readouterr().out
    assert "so_buoc_nguong" in out


def test_dong110a_thieu_far_muc_tieu(tmp_path):
    cfg = {"benchmark": {"so_buoc_nguong": 10}}
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    ma = br.main(
        [
            "--vao",
            str(tmp_path),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--config",
            str(p),
        ]
    )
    assert ma == 1


def test_dong110b_thong_bao_neu_dich_danh(tmp_path, capsys):
    cfg = {"benchmark": {"so_buoc_nguong": 10}}
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    br.main(
        [
            "--vao",
            str(tmp_path),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--config",
            str(p),
        ]
    )
    out = capsys.readouterr().out
    assert "far_muc_tieu" in out


def test_dong111_so_buoc_nguong_1(tmp_path, monkeypatch, capsys):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, so_buoc_nguong=1)
    assert kq["ma"] == 1
    out = capsys.readouterr().out
    assert "so_buoc_nguong" in out


def test_dong112_so_buoc_nguong_2_5(tmp_path, monkeypatch, capsys):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, so_buoc_nguong=2.5)
    assert kq["ma"] == 1
    out = capsys.readouterr().out
    assert "so_buoc_nguong" in out


def test_dong113_so_buoc_nguong_abc(tmp_path, monkeypatch, capsys):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, so_buoc_nguong="abc")
    assert kq["ma"] == 1
    out = capsys.readouterr().out
    assert "so_buoc_nguong" in out


def test_dong114_so_buoc_nguong_inf(tmp_path, monkeypatch, capsys):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, so_buoc_nguong=float("inf"))
    assert kq["ma"] == 1
    out = capsys.readouterr().out
    assert "so_buoc_nguong" in out


def test_dong115_so_buoc_nguong_nan(tmp_path, monkeypatch, capsys):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, so_buoc_nguong=float("nan"))
    assert kq["ma"] == 1
    out = capsys.readouterr().out
    assert "so_buoc_nguong" in out


def test_dong116_so_buoc_nguong_20_hop_le(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, so_buoc_nguong=20)
    assert kq["ma"] == 0


def test_dong117_dry_run_khong_ghi_tep(tmp_path, monkeypatch):
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(br, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    cfg_path = _cfg_yaml(tmp_path)
    ma = br.main(
        [
            "--vao",
            str(tmp_path / "khong_ton_tai"),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--config",
            str(cfg_path),
            "--dry-run",
        ]
    )
    assert ma == 0
    assert not thu_muc_kq.exists() or list(thu_muc_kq.rglob("*")) == []


def test_dong118_dry_run_khong_dung_backend(tmp_path, monkeypatch):
    def _khong_duoc_goi(cfg, ten):
        raise AssertionError("không được dựng backend khi --dry-run")

    monkeypatch.setattr(br, "tao_bo_nhan_dien", _khong_duoc_goi)
    cfg_path = _cfg_yaml(tmp_path)
    ma = br.main(
        [
            "--vao",
            str(tmp_path / "khong_ton_tai"),
            "--backend",
            "dlib",
            "--tap",
            "kiem-chuc-nang",
            "--device-name",
            "test",
            "--config",
            str(cfg_path),
            "--dry-run",
        ]
    )
    assert ma == 0


def test_dong119_backend_sai_system_exit(tmp_path):
    with pytest.raises(SystemExit):
        br.main(
            [
                "--vao",
                str(tmp_path),
                "--backend",
                "sai",
                "--tap",
                "kiem-chuc-nang",
                "--device-name",
                "test",
            ]
        )


def test_dong120_co_mau_nho_van_tra_0(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    assert kq["ma"] == 0


def test_dong121_canh_bao_co_mau_khong_rong(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert meta["canh_bao_co_mau"] != ""


def test_dong122_canh_bao_hieu_nang_khong_pi5(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, xac_dinh_moi_truong_gia="pc_x86")
    meta = _doc_meta(kq["thu_muc_kq"])
    assert meta["canh_bao_hieu_nang"] != ""


def test_dong123_khong_canh_bao_khi_pi5(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, xac_dinh_moi_truong_gia="pi5")
    meta = _doc_meta(kq["thu_muc_kq"])
    assert "canh_bao_hieu_nang" not in meta


def test_dong124_moi_truong_hop_le(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch)
    meta = _doc_meta(kq["thu_muc_kq"])
    assert meta["moi_truong"] in {"pc_x86", "docker_arm64", "pi5"}


def test_dong125_pi5_trong_notes(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, xac_dinh_moi_truong_gia="pc_x86")
    meta = _doc_meta(kq["thu_muc_kq"])
    assert "pi5" in meta["notes"]


def test_dong126_bang_in_neu_eer(tmp_path, monkeypatch, capsys):
    _dung_va_chay_co_ban(tmp_path, monkeypatch)
    out = capsys.readouterr().out
    assert "EER" in out


def test_dong127_bang_in_neu_far(tmp_path, monkeypatch, capsys):
    _dung_va_chay_co_ban(tmp_path, monkeypatch)
    out = capsys.readouterr().out
    assert "FAR" in out


def test_dong128_gallery_rong_loi(tmp_path):
    backend = _BackendGia()
    with pytest.raises(LoiCauHinh):
        br.do_diem_probe([], {}, backend, 0)
