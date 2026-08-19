"""Kiểm thử cho scripts/benchmark_detect.py.

Không cần mô hình ONNX thật cho bất kỳ ca nào ở đây: `YoloFaceDetector` được thay bằng một
lớp giả lập qua `monkeypatch.setattr(bd, "YoloFaceDetector", ...)` — đúng ràng buộc §10 của
đặc tả P2-03 ("Ca test không được đòi hỏi mô hình thật trừ khi đánh dấu @pytest.mark.slow").
Không có ca nào trong tệp này được đánh dấu slow.
"""

import ast
import csv
import inspect
import json
import re
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest

from scripts import benchmark_detect as bd
from src.common.exceptions import LoiCauHinh
from src.common.types import FaceBox

# ============================================================================
# Trợ giúp dùng chung
# ============================================================================


def _lam_lop_detector_gia(kich_thuoc_vao: int = 320, so_lan_co_mat: int | None = None):
    """Sinh một lớp thay thế YoloFaceDetector, giữ đúng chữ ký constructor (đường_dẫn, cfg).

    Args:
        kich_thuoc_vao: Giá trị trả về bởi thuộc tính `kich_thuoc_vao`.
        so_lan_co_mat: Số lệnh gọi `detect` đầu tiên trả về một khuôn mặt; các lệnh gọi
            sau đó trả về danh sách rỗng. `None` nghĩa là luôn trả về một khuôn mặt.
    """

    class _DetectorGia:
        def __init__(self, duong_dan_onnx, cfg) -> None:
            self.duong_dan_onnx = Path(duong_dan_onnx)
            self.cfg = cfg
            self._so_lan_goi = 0

        @property
        def kich_thuoc_vao(self) -> int:
            return kich_thuoc_vao

        def detect(self, khung_hinh):
            self._so_lan_goi += 1
            # Việc làm giả tốn chút CPU thật để latency_ms > 0 luôn đúng trên mọi máy.
            _ = sum(int(x) for x in khung_hinh.shape)
            if so_lan_co_mat is not None and self._so_lan_goi > so_lan_co_mat:
                return []
            return [FaceBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9)]

    return _DetectorGia


def _cfg_co_ban() -> dict:
    """Cấu hình hợp lệ tối giản dùng làm nền cho các ca kiểm thử."""
    return {
        "inference": {
            "conf_threshold": 0.5,
            "iou_threshold": 0.45,
            "max_faces": 10,
            "num_threads": 0,
        }
    }


def _anh_gia(n: int) -> list[np.ndarray]:
    """Sinh `n` ảnh giả (mảng NumPy) dùng cho do_mot_cau_hinh — không cần đọc từ đĩa."""
    rng = np.random.default_rng(42)
    return [rng.integers(0, 255, size=(8, 8, 3), dtype=np.uint8) for _ in range(n)]


def _tao_thu_muc_anh_gia(tmp_path: Path, so_luong: int, ten: str = "anh") -> Path:
    """Tạo thư mục chứa `so_luong` tệp .jpg RỖNG — đủ cho chon_anh (chỉ kiểm đuôi/tồn tại)."""
    d = tmp_path / "anh_nguon"
    d.mkdir(exist_ok=True)
    for i in range(so_luong):
        (d / f"{ten}_{i:04d}.jpg").write_bytes(b"\x00")
    return d


def _tao_mo_hinh_gia(tmp_path: Path, ten: str = "gia.onnx") -> Path:
    """Tạo một tệp .onnx giả (nội dung rỗng) — chỉ cần TỒN TẠI để qua bước kiểm tra tệp."""
    p = tmp_path / ten
    p.write_bytes(b"\x00")
    return p


def _bg_tu_latency(latencies: list[float], n_faces: list[int] | None = None) -> list[dict]:
    """Dựng danh sách bản ghi hợp lệ trực tiếp từ danh sách latency, cho ca test tong_hop."""
    if n_faces is None:
        n_faces = [1] * len(latencies)
    return [
        {
            "sample_idx": i,
            "latency_ms": lat,
            "fps_instant": 1000.0 / lat,
            "n_faces": nf,
            "conf_top": 0.9 if nf else None,
            "cpu_temp_c": None,
        }
        for i, (lat, nf) in enumerate(zip(latencies, n_faces))
    ]


def _ban_ghi_csv_mau() -> list[dict]:
    return [
        {
            "run_id": "bench_detect_20260819_1200",
            "backend": "onnx",
            "imgsz": 320,
            "threads": 1,
            "sample_idx": 0,
            "latency_ms": 40.0,
            "fps_instant": 25.0,
            "n_faces": 1,
            "conf_top": 0.9,
            "cpu_temp_c": None,
        },
        {
            "run_id": "bench_detect_20260819_1200",
            "backend": "onnx",
            "imgsz": 320,
            "threads": 1,
            "sample_idx": 1,
            "latency_ms": 42.0,
            "fps_instant": 1000 / 42.0,
            "n_faces": 0,
            "conf_top": None,
            "cpu_temp_c": None,
        },
    ]


def _meta_hop_le(tom_tat: dict | None = None) -> dict:
    return {
        "run_id": "bench_detect_20260819_1200",
        "timestamp": "2026-08-19T12:00:00+07:00",
        "git_commit": "abc123",
        "git_dirty": False,
        "script": "scripts/benchmark_detect.py",
        "command": "python scripts/benchmark_detect.py --device-name test",
        "device": {"name": "test", "os": "x", "machine": "x", "processor": "x"},
        "software": {
            "python": "3.11",
            "onnxruntime": "1.0",
            "opencv-python": "4.0",
            "numpy": "2.0",
        },
        "config_file": "configs/detect.yaml",
        "config_snapshot": {},
        "dataset": {"anh_dir": "x", "n_anh_tong": 1},
        "seed": 42,
        "warmup_frames": 10,
        "cpu_temp_start_c": None,
        "cpu_temp_max_c": None,
        "duration_s": 1.0,
        "notes": "",
        "tom_tat": tom_tat or {},
    }


@pytest.fixture(scope="module")
def thu_muc_anh_that(tmp_path_factory) -> Path:
    """Thư mục ảnh .jpg THẬT (giải mã được bằng cv2.imread), dùng cho các ca chạy main()."""
    d = tmp_path_factory.mktemp("anh_that")
    rng = np.random.default_rng(0)
    for i in range(130):
        anh = rng.integers(0, 255, size=(16, 16, 3), dtype=np.uint8)
        cv2.imwrite(str(d / f"anh_{i:04d}.jpg"), anh)
    return d


# ============================================================================
# §7.1 — chon_anh, doc_nhiet_do_cpu, dang_trong_container (dòng 01-10)
# ============================================================================


def test_dong01_cung_seed_chon_cung_tap(tmp_path):
    d = _tao_thu_muc_anh_gia(tmp_path, 100)
    assert bd.chon_anh(d, 20, 42) == bd.chon_anh(d, 20, 42)


def test_dong02_khac_seed_chon_khac_tap(tmp_path):
    d = _tao_thu_muc_anh_gia(tmp_path, 100)
    assert bd.chon_anh(d, 20, 42) != bd.chon_anh(d, 20, 7)


def test_dong03_dung_so_luong(tmp_path):
    d = _tao_thu_muc_anh_gia(tmp_path, 50)
    assert len(bd.chon_anh(d, 20, 42)) == 20


def test_dong04_thu_muc_khong_ton_tai(tmp_path):
    with pytest.raises(LoiCauHinh):
        bd.chon_anh(tmp_path / "khong_ton_tai", 5, 42)


def test_dong05_thu_muc_rong(tmp_path):
    d = tmp_path / "rong"
    d.mkdir()
    with pytest.raises(LoiCauHinh, match="rỗng|không có ảnh") as exc_rong:
        bd.chon_anh(d, 5, 42)

    with pytest.raises(LoiCauHinh) as exc_khong_ton_tai:
        bd.chon_anh(tmp_path / "khong_ton_tai", 5, 42)

    # Thông báo phải khác dòng 04 (thư mục không tồn tại) — không được trùng chuỗi.
    assert str(exc_rong.value) != str(exc_khong_ton_tai.value)


def test_dong06_khong_du_anh(tmp_path):
    d = _tao_thu_muc_anh_gia(tmp_path, 5)
    with pytest.raises(LoiCauHinh) as exc_info:
        bd.chon_anh(d, 100, 42)
    assert "5" in str(exc_info.value)
    assert "100" in str(exc_info.value)


def test_dong07_khong_co_cam_bien_khong_nem_loi(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "_DUONG_DAN_NHIET_DO_CPU", tmp_path / "khong_ton_tai_temp")
    kq = bd.doc_nhiet_do_cpu()
    assert kq is None or isinstance(kq, float)


def test_dong08_doc_dung_khi_co_tep(monkeypatch, tmp_path):
    tep = tmp_path / "temp_gia"
    tep.write_text("52341", encoding="utf-8")
    monkeypatch.setattr(bd, "_DUONG_DAN_NHIET_DO_CPU", tep)
    assert bd.doc_nhiet_do_cpu() == pytest.approx(52.341)


def test_dong09_dang_trong_container_true(monkeypatch, tmp_path):
    tep = tmp_path / ".dockerenv"
    tep.touch()
    monkeypatch.setattr(bd, "_DUONG_DAN_DOCKERENV", tep)
    assert bd.dang_trong_container() is True


def test_dong10_dang_trong_container_false(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "_DUONG_DAN_DOCKERENV", tmp_path / "khong_ton_tai_dockerenv")
    assert bd.dang_trong_container() is False


# ============================================================================
# §7.2 — do_mot_cau_hinh, tong_hop (dòng 11-24)
# ============================================================================


def test_dong11_so_ban_ghi_dung_khong_tinh_lam_nong(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    anh = _anh_gia(17)
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 12, anh, 5)
    assert len(bg) == 12


def test_dong12_du_sau_khoa(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    anh = _anh_gia(15)
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 10, anh, 5)
    for r in bg:
        assert set(r) >= {
            "sample_idx",
            "latency_ms",
            "fps_instant",
            "n_faces",
            "conf_top",
            "cpu_temp_c",
        }


def test_dong13_sample_idx_lien_tuc(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    anh = _anh_gia(15)
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 10, anh, 5)
    assert [r["sample_idx"] for r in bg] == list(range(len(bg)))


def test_dong14_fps_instant_khop_nghich_dao(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    anh = _anh_gia(15)
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 10, anh, 5)
    for r in bg:
        assert abs(r["fps_instant"] - 1000.0 / r["latency_ms"]) < 1e-6


def test_dong15_latency_duong(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    anh = _anh_gia(15)
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 10, anh, 5)
    assert all(r["latency_ms"] > 0 for r in bg)


def test_dong16_khong_doc_tep_trong_vong_do():
    """Quét AST thân do_mot_cau_hinh: không gọi imread/open/read_bytes ở bất kỳ đâu."""
    nguon = inspect.getsource(bd.do_mot_cau_hinh)
    cay = ast.parse(nguon)
    ham_cam = {"imread", "open", "read_bytes"}
    vi_pham = []
    for node in ast.walk(cay):
        if isinstance(node, ast.Call):
            ten = None
            if isinstance(node.func, ast.Attribute):
                ten = node.func.attr
            elif isinstance(node.func, ast.Name):
                ten = node.func.id
            if ten in ham_cam:
                vi_pham.append(ten)
    assert vi_pham == [], f"do_mot_cau_hinh gọi hàm đọc tệp bị cấm trong vòng đo: {vi_pham}"


def test_dong17_trung_binh_dung():
    bg = _bg_tu_latency([10, 20, 30])
    kq = bd.tong_hop(bg)
    assert kq["latency_tb"] == pytest.approx(20.0)


def test_dong18_do_lech_chuan_dung():
    bg = _bg_tu_latency([10, 20, 30])
    kq = bd.tong_hop(bg)
    assert kq["latency_do_lech"] == pytest.approx(np.std([10, 20, 30]))


def test_dong19_p50_p95_dung():
    latencies = list(range(1, 101))
    bg = _bg_tu_latency(latencies)
    kq = bd.tong_hop(bg)
    assert kq["latency_p50"] == pytest.approx(np.percentile(latencies, 50))
    assert kq["latency_p95"] == pytest.approx(np.percentile(latencies, 95))


def test_dong20_dat_chi_tieu_true_tren_nguong():
    bg = _bg_tu_latency([50.0] * 10)
    kq = bd.tong_hop(bg)
    assert kq["fps_tb"] == pytest.approx(20.0)
    assert kq["dat_chi_tieu"] is True


def test_dong21_dat_chi_tieu_false_duoi_nguong():
    bg = _bg_tu_latency([200.0] * 10)
    kq = bd.tong_hop(bg)
    assert kq["fps_tb"] == pytest.approx(5.0)
    assert kq["dat_chi_tieu"] is False


def test_dong22_bien_dung_tai_10fps():
    """Ca biên: latency đều 100 ms ⇒ fps_tb == 10.0 đúng chỗ ranh giới >= (không phải >)."""
    bg = _bg_tu_latency([100.0] * 10)
    kq = bd.tong_hop(bg)
    assert kq["fps_tb"] == pytest.approx(10.0)
    assert kq["dat_chi_tieu"] is True


def test_dong23_ti_le_phat_hien_dung():
    n_faces = [1, 1, 1, 1, 1, 1, 1, 0, 0, 0]
    bg = _bg_tu_latency([50.0] * 10, n_faces=n_faces)
    kq = bd.tong_hop(bg)
    assert kq["ti_le_phat_hien"] == pytest.approx(0.7)


def test_dong24_danh_sach_rong_nem_loi():
    with pytest.raises(LoiCauHinh):
        bd.tong_hop([])


# ============================================================================
# §7.3 — ghi_ket_qua (dòng 25-33)
# ============================================================================


def test_dong25_ghi_dung_hai_tep(tmp_path):
    csv_path, meta_path = bd.ghi_ket_qua(
        tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), _meta_hop_le()
    )
    assert csv_path.exists()
    assert meta_path.exists()


def test_dong26_ten_tep_dung_khuon(tmp_path):
    csv_path, _ = bd.ghi_ket_qua(
        tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), _meta_hop_le()
    )
    assert re.fullmatch(r"bench_detect_\d{8}_\d{4}\.csv", csv_path.name)


def test_dong27_csv_dung_muoi_cot_dung_thu_tu(tmp_path):
    csv_path, _ = bd.ghi_ket_qua(
        tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), _meta_hop_le()
    )
    with open(csv_path, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == [
        "run_id",
        "backend",
        "imgsz",
        "threads",
        "sample_idx",
        "latency_ms",
        "fps_instant",
        "n_faces",
        "conf_top",
        "cpu_temp_c",
    ]


def test_dong28_so_dong_csv_dung(tmp_path):
    ban_ghi = _ban_ghi_csv_mau()
    csv_path, _ = bd.ghi_ket_qua(tmp_path, "bench_detect_20260819_1200", ban_ghi, _meta_hop_le())
    with open(csv_path, newline="", encoding="utf-8") as f:
        so_dong = len(list(csv.DictReader(f)))
    assert so_dong == len(ban_ghi)


def test_dong29_meta_du_muoi_tam_khoa(tmp_path):
    _, meta_path = bd.ghi_ket_qua(
        tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), _meta_hop_le()
    )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert set(meta) >= {
        "run_id",
        "timestamp",
        "git_commit",
        "git_dirty",
        "script",
        "command",
        "device",
        "software",
        "config_file",
        "config_snapshot",
        "dataset",
        "seed",
        "warmup_frames",
        "cpu_temp_start_c",
        "cpu_temp_max_c",
        "duration_s",
        "notes",
        "tom_tat",
    }


def test_dong29b_device_du_bon_truong(tmp_path):
    _, meta_path = bd.ghi_ket_qua(
        tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), _meta_hop_le()
    )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert set(meta["device"]) >= {"name", "os", "machine", "processor"}


def test_dong29c_software_du_bon_phien_ban(tmp_path):
    _, meta_path = bd.ghi_ket_qua(
        tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), _meta_hop_le()
    )
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert set(meta["software"]) >= {"python", "onnxruntime", "opencv-python", "numpy"}


def test_dong30_git_commit_khop_kho_that():
    """Bỏ qua trên container ARM64: không có nhị phân `git` và không có thư mục `.git/`
    (deploy/Dockerfile.arm64 không cài git; .dockerignore loại .git/ khỏi build context)."""
    goc_kho = Path(bd.__file__).resolve().parents[1]
    if shutil.which("git") is None or not (goc_kho / ".git").exists():
        pytest.skip("Môi trường không có git hoặc không có .git/ (container ARM64) — bỏ qua")

    ket_qua = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
        cwd=goc_kho,
    )
    assert bd._lay_git_commit_hash() == ket_qua.stdout.strip()


def test_dong31_meta_thieu_khoa_nem_loi(tmp_path):
    with pytest.raises(LoiCauHinh):
        bd.ghi_ket_qua(tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), {})


def test_dong32_meta_du_khoa_ghi_thanh_cong(tmp_path):
    csv_path, meta_path = bd.ghi_ket_qua(
        tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), _meta_hop_le()
    )
    assert csv_path.exists() and meta_path.exists()


def test_dong33_cpu_temp_rong_khong_phai_none(tmp_path):
    ban_ghi = _ban_ghi_csv_mau()  # cpu_temp_c là None trong mọi bản ghi mẫu
    csv_path, _ = bd.ghi_ket_qua(tmp_path, "bench_detect_20260819_1200", ban_ghi, _meta_hop_le())
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        assert row["cpu_temp_c"] == ""
        assert row["cpu_temp_c"] != "None"


# ============================================================================
# §7.4 — chốt chặn container, qua main() (dòng 34-36)
# ============================================================================


def test_dong34_container_co_canh_bao(monkeypatch, tmp_path, thu_muc_anh_that):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    monkeypatch.setattr(bd, "dang_trong_container", lambda: True)
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    ma = bd.main(
        [
            "--device-name",
            "PC test",
            "--anh-dir",
            str(thu_muc_anh_that),
            "--models",
            str(mo_hinh),
            "--threads",
            "1",
        ]
    )
    assert ma == 0
    meta_files = list(tmp_path.glob("*.meta.json"))
    assert len(meta_files) == 1
    meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
    assert meta.get("canh_bao_hieu_nang")


def test_dong35_container_in_canh_bao_ra_man_hinh(monkeypatch, tmp_path, capsys, thu_muc_anh_that):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    monkeypatch.setattr(bd, "dang_trong_container", lambda: True)
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    ma = bd.main(
        [
            "--device-name",
            "PC test",
            "--anh-dir",
            str(thu_muc_anh_that),
            "--models",
            str(mo_hinh),
            "--threads",
            "1",
        ]
    )
    assert ma == 0
    ra = capsys.readouterr()
    assert "QEMU" in ra.out or "không dùng được" in ra.out


def test_dong36_ngoai_container_khong_co_canh_bao(monkeypatch, tmp_path, thu_muc_anh_that):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    monkeypatch.setattr(bd, "dang_trong_container", lambda: False)
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    ma = bd.main(
        [
            "--device-name",
            "PC test",
            "--anh-dir",
            str(thu_muc_anh_that),
            "--models",
            str(mo_hinh),
            "--threads",
            "1",
        ]
    )
    assert ma == 0
    meta_files = list(tmp_path.glob("*.meta.json"))
    meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
    assert "canh_bao_hieu_nang" not in meta


# ============================================================================
# §7.5 — luồng chính main() (dòng 37-43)
# ============================================================================


def test_dong37_thieu_device_name(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    ma = bd.main([])
    assert ma == 1
    ra = capsys.readouterr()
    assert "device-name" in ra.out or "device-name" in ra.err


def test_dong38_dry_run_khong_ghi_tep(tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    truoc = set(tmp_path.rglob("*"))
    ma = bd.main(["--device-name", "PC test", "--dry-run"])
    sau = set(tmp_path.rglob("*"))
    assert truoc == sau
    assert ma == 0


def test_dong39_n_frames_duoi_nguong(capsys, tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    ma = bd.main(["--device-name", "PC test", "--n-frames", "50"])
    assert ma == 1
    ra = capsys.readouterr()
    assert "100" in ra.out or "100" in ra.err


def test_dong39b_warmup_am_tra_ve_1(capsys, tmp_path, monkeypatch):
    """CS-1: --warmup âm không được lách qua chốt R9 (>=100 khung) và không được ghi tệp."""
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    truoc = set(tmp_path.rglob("*"))
    ma = bd.main(["--device-name", "PC test", "--n-frames", "100", "--warmup", "-90"])
    assert ma == 1
    sau = set(tmp_path.rglob("*"))
    assert truoc == sau
    ra = capsys.readouterr()
    assert "warmup" in ra.out or "warmup" in ra.err


def test_dong40_ma_tran_dung_so_o(monkeypatch, tmp_path, thu_muc_anh_that):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    m1 = _tao_mo_hinh_gia(tmp_path, "gia1.onnx")
    m2 = _tao_mo_hinh_gia(tmp_path, "gia2.onnx")
    ma = bd.main(
        [
            "--device-name",
            "PC test",
            "--anh-dir",
            str(thu_muc_anh_that),
            "--models",
            str(m1),
            str(m2),
            "--threads",
            "1",
            "2",
            "4",
        ]
    )
    assert ma == 0
    meta_files = list(tmp_path.glob("*.meta.json"))
    meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
    assert len(meta["tom_tat"]) == 6


def test_dong40b_ma_tran_hai_mo_hinh_trung_ten_khac_thu_muc(
    monkeypatch, tmp_path, thu_muc_anh_that
):
    """CS-2: hai mô hình khác thư mục nhưng trùng tên tệp không được đè mất tổng hợp của nhau."""
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "ket_qua")
    (tmp_path / "v1").mkdir()
    (tmp_path / "v2").mkdir()
    m1 = _tao_mo_hinh_gia(tmp_path / "v1", "gia.onnx")
    m2 = _tao_mo_hinh_gia(tmp_path / "v2", "gia.onnx")
    ma = bd.main(
        [
            "--device-name",
            "PC test",
            "--anh-dir",
            str(thu_muc_anh_that),
            "--models",
            str(m1),
            str(m2),
            "--threads",
            "1",
        ]
    )
    assert ma == 0
    meta_files = list((tmp_path / "ket_qua").glob("*.meta.json"))
    meta = json.loads(meta_files[0].read_text(encoding="utf-8"))
    assert len(meta["tom_tat"]) == 2


def test_dong41_mo_hinh_khong_ton_tai(tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    ma = bd.main(
        [
            "--device-name",
            "PC test",
            "--models",
            "khong/co.onnx",
        ]
    )
    assert ma == 1


def test_dong42_cau_hinh_hong(tmp_path, monkeypatch):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "ket_qua")
    cfg_hong = tmp_path / "hong.yaml"
    cfg_hong.write_text("khoa: [1, 2\n", encoding="utf-8")  # dấu ngoặc chưa đóng ⇒ lỗi YAML
    ma = bd.main(
        [
            "--device-name",
            "PC test",
            "--config",
            str(cfg_hong),
        ]
    )
    assert ma == 1


def test_dong43_bang_tong_ket_co_cot_dat(monkeypatch, tmp_path, thu_muc_anh_that, capsys):
    monkeypatch.setattr(bd, "YoloFaceDetector", _lam_lop_detector_gia())
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    ma = bd.main(
        [
            "--device-name",
            "PC test",
            "--anh-dir",
            str(thu_muc_anh_that),
            "--models",
            str(mo_hinh),
            "--threads",
            "1",
        ]
    )
    assert ma == 0
    ra = capsys.readouterr()
    assert "10" in ra.out
    assert "Đạt" in ra.out or "KHÔNG" in ra.out
