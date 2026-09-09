"""Kiểm thử cho scripts/benchmark_detect.py.

Không cần mô hình thật cho bất kỳ ca nào ở đây: từ P2-06, `benchmark_detect` nạp mô hình qua
`tao_bo_phat_hien`, nên chỗ chèn giả lập là `monkeypatch.setattr(bd, "tao_bo_phat_hien", ...)`
— trước đó là `bd.YoloFaceDetector`. Đây là phép đổi ĐÚNG MỘT DÒNG ở mỗi ca cũ; mọi assert của
chúng giữ nguyên, vì chính chúng là lưới an toàn của phép đổi P2-06 §5.1.

Ràng buộc §10 của đặc tả P2-03 vẫn giữ ("Ca test không được đòi hỏi mô hình thật trừ khi đánh
dấu @pytest.mark.slow"). Không có ca nào trong tệp này được đánh dấu slow.

Từ P2-06b (§6.2), nhánh `--dry-run` không còn khởi tạo mô hình: nó suy `backend` thẳng từ
DẠNG đường dẫn qua `tra_ten_backend`, không còn đi qua `tao_bo_phat_hien`. Vì vậy
`test_dong53` (cột backend của bảng dry-run) đã đổi cách dựng dữ liệu — xem docstring của
chính nó — trong khi `do_mot_cau_hinh` (đường ghi số đo) vẫn đọc `backend` từ
`detector.ten_backend` như cũ, không đổi gì.
"""

import ast
import csv
import importlib.metadata
import inspect
import json
import re
import shutil
import subprocess
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from scripts import benchmark_detect as bd
from src.capture.base import BoThuHinh
from src.common.exceptions import LoiCamera, LoiCauHinh
from src.common.types import FaceBox

# ============================================================================
# Trợ giúp dùng chung
# ============================================================================


def _lam_lop_detector_gia(
    kich_thuoc_vao: int = 320,
    so_lan_co_mat: int | None = None,
    ten_backend: str = "onnx",
):
    """Sinh một lớp bộ phát hiện giả, giữ đúng chữ ký constructor (đường_dẫn, cfg).

    Args:
        kich_thuoc_vao: Giá trị trả về bởi thuộc tính `kich_thuoc_vao`.
        so_lan_co_mat: Số lệnh gọi `detect` đầu tiên trả về một khuôn mặt; các lệnh gọi
            sau đó trả về danh sách rỗng. `None` nghĩa là luôn trả về một khuôn mặt.
        ten_backend: Giá trị trả về bởi thuộc tính `ten_backend` — thứ mà benchmark_detect
            phải đọc thay vì đoán từ tên đường dẫn (P2-06 §6.1).
    """

    class _DetectorGia:
        def __init__(self, duong_dan_onnx, cfg) -> None:
            self.duong_dan_onnx = Path(duong_dan_onnx)
            self.cfg = cfg
            self._so_lan_goi = 0

        @property
        def kich_thuoc_vao(self) -> int:
            return kich_thuoc_vao

        @property
        def ten_backend(self) -> str:
            return ten_backend

        def detect(self, khung_hinh):
            self._so_lan_goi += 1
            # Việc làm giả tốn chút CPU thật để latency_ms > 0 luôn đúng trên mọi máy.
            _ = sum(int(x) for x in khung_hinh.shape)
            if so_lan_co_mat is not None and self._so_lan_goi > so_lan_co_mat:
                return []
            return [FaceBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9)]

    return _DetectorGia


def _lam_factory_gia(
    kich_thuoc_vao: int = 320,
    so_lan_co_mat: int | None = None,
    ten_backend: str = "onnx",
    bo_dem: list | None = None,
):
    """Sinh một hàm thay thế `tao_bo_phat_hien`, giữ đúng chữ ký (đường_dẫn, cfg).

    Args:
        kich_thuoc_vao: Xem `_lam_lop_detector_gia`.
        so_lan_co_mat: Xem `_lam_lop_detector_gia`.
        ten_backend: Xem `_lam_lop_detector_gia`.
        bo_dem: Nếu truyền vào, mỗi lệnh gọi factory nối thêm đường dẫn mô hình vào danh sách
            này — cách duy nhất đếm được số lần nạp mô hình của một ô (dòng 52).
    """
    lop = _lam_lop_detector_gia(kich_thuoc_vao, so_lan_co_mat, ten_backend)

    def _factory_gia(duong_dan, cfg):
        if bo_dem is not None:
            bo_dem.append(Path(duong_dan))
        return lop(duong_dan, cfg)

    return _factory_gia


def _lam_factory_gia_theo_ten(anh_xa_ten_backend: dict[str, str]):
    """Sinh factory giả trả bộ suy luận KHÁC NHAU tuỳ mô hình, cho ca trộn hai loại.

    Args:
        anh_xa_ten_backend: Ánh xạ `tên cuối của đường dẫn -> ten_backend` mà bộ phát hiện
            giả sẽ khai báo.
    """

    def _factory_gia(duong_dan, cfg):
        ten = Path(duong_dan).name
        lop = _lam_lop_detector_gia(ten_backend=anh_xa_ten_backend[ten])
        return lop(duong_dan, cfg)

    return _factory_gia


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
        "git_dirty_toan_cay": False,
        "script": "scripts/benchmark_detect.py",
        "command": "python scripts/benchmark_detect.py --device-name test",
        "device": {"name": "test", "os": "x", "machine": "x", "processor": "x"},
        "moi_truong": "pc_x86",
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
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    anh = _anh_gia(17)
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 12, anh, 5)
    assert len(bg) == 12


def test_dong12_du_sau_khoa(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
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
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    anh = _anh_gia(15)
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 10, anh, 5)
    assert [r["sample_idx"] for r in bg] == list(range(len(bg)))


def test_dong14_fps_instant_khop_nghich_dao(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    anh = _anh_gia(15)
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 10, anh, 5)
    for r in bg:
        assert abs(r["fps_instant"] - 1000.0 / r["latency_ms"]) < 1e-6


def test_dong15_latency_duong(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
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
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
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
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
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
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
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
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
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
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
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
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
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


# ============================================================================
# P2-06 §7 — hai bộ suy luận trong một ma trận (dòng 44-54)
# ============================================================================


def _tham_so_main(mo_hinh, thu_muc_anh, *them_mo_hinh) -> list[str]:
    """Dựng danh sách tham số main() tối giản cho một ô ma trận (1 mô hình x 1 mức luồng)."""
    return [
        "--device-name",
        "PC test",
        "--anh-dir",
        str(thu_muc_anh),
        "--models",
        str(mo_hinh),
        *[str(m) for m in them_mo_hinh],
        "--threads",
        "1",
    ]


def _doc_meta_duy_nhat(thu_muc: Path) -> dict:
    """Đọc tệp .meta.json duy nhất trong thư mục kết quả, khẳng định đúng một tệp."""
    tep = list(thu_muc.glob("*.meta.json"))
    assert len(tep) == 1, f"Cần đúng một tệp meta, thấy {len(tep)}"
    return json.loads(tep[0].read_text(encoding="utf-8"))


def test_dong44_duong_dan_onnx_cho_backend_onnx(monkeypatch, tmp_path):
    """Dòng 01: bản ghi lấy `backend` từ đối tượng phát hiện, trường hợp ONNX."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia(ten_backend="onnx"))
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 10, _anh_gia(15), 5)
    assert bg
    assert {r["backend"] for r in bg} == {"onnx"}


def test_dong45_thu_muc_ncnn_cho_backend_ncnn(monkeypatch, tmp_path):
    """Dòng 02: cùng hàm đó, mô hình là THƯ MỤC, backend phải là ncnn."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia(ten_backend="ncnn"))
    thu_muc = tmp_path / "gia_ncnn_model"
    thu_muc.mkdir()
    bg = bd.do_mot_cau_hinh(thu_muc, _cfg_co_ban(), 10, _anh_gia(15), 5)
    assert bg
    assert {r["backend"] for r in bg} == {"ncnn"}


def test_dong46_imgsz_lay_tu_detector_khong_tu_ten_tep(monkeypatch, tmp_path):
    """Dòng 03: tên tệp nói 320, đối tượng phát hiện nói 999 — bản ghi phải theo đối tượng."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia(kich_thuoc_vao=999))
    bg = bd.do_mot_cau_hinh(tmp_path / "yolov8n-face-320.onnx", _cfg_co_ban(), 10, _anh_gia(15), 5)
    assert bg
    assert {r["imgsz"] for r in bg} == {999}


def test_dong47_tron_hai_loai_csv_co_hai_gia_tri_backend(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 04: một lần chạy trộn cả hai loại mô hình -> cột backend của CSV có hai giá trị."""
    m_onnx = _tao_mo_hinh_gia(tmp_path, "gia.onnx")
    m_ncnn = tmp_path / "gia_ncnn_model"
    m_ncnn.mkdir()
    monkeypatch.setattr(
        bd,
        "tao_bo_phat_hien",
        _lam_factory_gia_theo_ten({"gia.onnx": "onnx", "gia_ncnn_model": "ncnn"}),
    )
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)

    ma = bd.main(_tham_so_main(m_onnx, thu_muc_anh_that, m_ncnn))

    assert ma == 0
    tep_csv = list(thu_muc_kq.glob("*.csv"))
    assert len(tep_csv) == 1
    with open(tep_csv[0], newline="", encoding="utf-8") as f:
        dong = list(csv.DictReader(f))
    assert {r["backend"] for r in dong} == {"onnx", "ncnn"}


def test_dong48_duong_dan_khong_hop_le_tra_ve_1(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 05: đuôi lạ -> main trả 1, không để ngoại lệ của factory lọt ra ngoài."""
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)

    # (a) đường dẫn không tồn tại — chặn ngay ở bước kiểm tồn tại
    assert bd.main(_tham_so_main("khong/ton/tai.txt", thu_muc_anh_that)) == 1

    # (b) tệp CÓ THẬT nhưng đuôi lạ — phải đi tới factory THẬT và bị LoiCauHinh, main bắt lấy
    tep_la = tmp_path / "mo_hinh.txt"
    tep_la.write_bytes(b"\x00")
    assert bd.main(_tham_so_main(tep_la, thu_muc_anh_that)) == 1
    assert not thu_muc_kq.exists()


def test_dong49_meta_co_khoa_moi_truong(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 06: .meta.json phải mang đủ khoá bắt buộc, trong đó có `moi_truong`."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that))

    assert ma == 0
    meta = _doc_meta_duy_nhat(thu_muc_kq)
    assert set(meta) >= set(bd._KHOA_META_BAT_BUOC)
    assert "moi_truong" in meta


def test_dong50_moi_truong_nhan_ma_hop_le(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 07: giá trị `moi_truong` phải là một trong đúng ba mã của quy ước đo."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that))

    assert ma == 0
    meta = _doc_meta_duy_nhat(thu_muc_kq)
    assert meta["moi_truong"] in {"pc_x86", "docker_arm64", "pi5"}


def test_dong51_ngoai_pi5_notes_co_canh_bao(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 08: không đo trên Pi 5 -> notes phải mang câu cấm dùng kết luận chỉ tiêu."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    monkeypatch.setattr(bd, "xac_dinh_moi_truong", lambda: "pc_x86")
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that) + ["--ghi-chu", "ghi chu cua toi"])

    assert ma == 0
    meta = _doc_meta_duy_nhat(thu_muc_kq)
    assert "KHÔNG dùng kết luận chỉ tiêu" in meta["notes"]
    assert "pc_x86" in meta["notes"]
    # Ghi chú của người đo không được câu cảnh báo nuốt mất.
    assert "ghi chu cua toi" in meta["notes"]


def test_dong51b_tren_pi5_notes_khong_co_canh_bao(monkeypatch, tmp_path, thu_muc_anh_that):
    """Ca biên của dòng 08: đo đúng trên phần cứng đích thì notes giữ nguyên ghi chú người đo."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    monkeypatch.setattr(bd, "xac_dinh_moi_truong", lambda: "pi5")
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that) + ["--ghi-chu", "ghi chu cua toi"])

    assert ma == 0
    meta = _doc_meta_duy_nhat(thu_muc_kq)
    assert meta["notes"] == "ghi chu cua toi"


def test_dong52_moi_o_nap_mo_hinh_dung_mot_lan(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 09: một mô hình x một mức luồng -> factory được gọi ĐÚNG một lần (P2-06 §6.2)."""
    bo_dem: list = []
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia(bo_dem=bo_dem))
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that))

    assert ma == 0
    assert len(bo_dem) == 1


def test_dong53_dry_run_co_cot_backend_khong_ghi_tep(monkeypatch, tmp_path, capsys):
    """Dòng 10 (P2-06b): bảng kế hoạch có cột backend suy từ DẠNG đường dẫn thật, không
    tạo ra tệp nào.

    Cập nhật so với P2-06: từ P2-06b, dry-run không còn khởi tạo mô hình (§5.1) nên
    `tao_bo_phat_hien` bị monkeypatch ở đây KHÔNG còn ảnh hưởng gì tới cột backend hiển
    thị — cố tình khai báo lệch ('onnx') để khẳng định điều đó. Dùng một thư mục NCNN có
    đủ tệp nhận dạng (không cần trọng số thật) để `tra_ten_backend` trả đúng 'ncnn'.

    Tên thư mục CỐ TÌNH không chứa chuỗi con "ncnn" (khác quy ước `*_ncnn_model` thường
    dùng) — nếu không, chuỗi "ncnn" trong stdout có thể đến từ chính đường dẫn được in ra
    (cột đầu bảng kế hoạch), khiến assert bên dưới xanh giả kể cả khi cột backend sai.
    """
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia(ten_backend="onnx"))
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "ket_qua")
    mo_hinh_ncnn = tmp_path / "kieu_thu_muc_b"
    mo_hinh_ncnn.mkdir()
    (mo_hinh_ncnn / "model.ncnn.param").write_bytes(b"")
    truoc = set(tmp_path.rglob("*"))

    ma = bd.main(
        [
            "--device-name",
            "PC test",
            "--models",
            str(mo_hinh_ncnn),
            "--threads",
            "1",
            "--dry-run",
        ]
    )

    sau = set(tmp_path.rglob("*"))
    assert ma == 0
    assert truoc == sau
    ra = capsys.readouterr()
    assert "backend" in ra.out
    assert "ncnn" in ra.out


def test_dong54_cot_csv_van_dung_muoi_khoa_dung_thu_tu(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 11: thêm bộ suy luận thứ hai không được làm xê dịch lược đồ CSV."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that))

    assert ma == 0
    tep_csv = list(thu_muc_kq.glob("*.csv"))
    assert len(tep_csv) == 1
    with open(tep_csv[0], newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == list(bd._COT_CSV)


# ============================================================================
# P2-06b §6.2 — ca đối kháng backend, meta phiên bản ncnn, dry-run khô (dòng 06-09)
# ============================================================================


def test_dong55_backend_lay_tu_doi_tuong_khong_tu_duong_dan(monkeypatch, tmp_path):
    """Dòng 06: `do_mot_cau_hinh` phải lấy `backend` từ `detector.ten_backend`, không suy từ
    dạng đường dẫn — dựng lệch cố ý (đường dẫn .onnx, đối tượng khai 'ncnn'), đúng kiểu phép
    đột biến ĐB1 (P2-06b §7) sẽ làm lộ nếu `do_mot_cau_hinh` đổi nguồn sang `tra_ten_backend`.
    Đây là ca tái dựng ĐB5 của lượt review P2-06, phép trước đây làm 59/59 ca vẫn xanh.
    """
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia(ten_backend="ncnn"))
    bg = bd.do_mot_cau_hinh(tmp_path / "gia.onnx", _cfg_co_ban(), 10, _anh_gia(15), 5)
    assert bg
    assert {r["backend"] for r in bg} == {"ncnn"}


def test_dong56_meta_software_co_khoa_ncnn(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 07: khối `software` của .meta.json phải mang khoá `ncnn`."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that))

    assert ma == 0
    meta = _doc_meta_duy_nhat(thu_muc_kq)
    assert "ncnn" in meta["software"]


def test_dong57_thieu_goi_ncnn_khong_hong_luot_do(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 08: gói `ncnn` vắng mặt trên máy đo không được làm hỏng cả lượt đo — meta vẫn ghi
    được, với giá trị báo vắng dạng chuỗi thay cho phiên bản thật."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    monkeypatch.setattr(
        bd,
        "_lay_phien_ban_ncnn",
        lambda: (_ for _ in ()).throw(importlib.metadata.PackageNotFoundError("ncnn")),
    )
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that))

    assert ma == 0
    meta = _doc_meta_duy_nhat(thu_muc_kq)
    assert isinstance(meta["software"]["ncnn"], str)


def test_dong58_dry_run_khong_khoi_tao_mo_hinh_nao(monkeypatch, tmp_path):
    """Dòng 09: `--dry-run` không được gọi `tao_bo_phat_hien` một lần nào — nó chỉ suy backend
    từ dạng đường dẫn, không được trả chi phí nạp mô hình thật (P2-06b mục B)."""
    bo_dem: list = []
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia(bo_dem=bo_dem))
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(
        ["--device-name", "PC test", "--models", str(mo_hinh), "--threads", "1", "--dry-run"]
    )

    assert ma == 0
    assert len(bo_dem) == 0


# ============================================================================
# P2-06c §6 — `git_dirty` giới hạn theo phạm vi đường dẫn (dòng 59-67)
# ============================================================================


def _gia_lap_git_status(
    monkeypatch,
    dau_ra_pham_vi: str = "",
    dau_ra_toan_cay: str = "",
    loi: type[Exception] | None = None,
) -> list[list[str]]:
    """Chèn `subprocess.run` giả cho `benchmark_detect`, trả đầu ra khác nhau theo phạm vi.

    Lệnh `git status` CÓ pathspec nhận `dau_ra_pham_vi`, lệnh KHÔNG pathspec nhận
    `dau_ra_toan_cay`. Nhờ tách hai đầu ra, phép đột biến bỏ pathspec làm ca đỏ thật: hàm sẽ
    đọc đầu ra của lệnh toàn cây thay vì đầu ra của lệnh giới hạn phạm vi. Các lệnh git khác
    (`rev-parse`) trả về chuỗi rỗng — chúng không thuộc phạm vi mã việc này.

    Args:
        monkeypatch: Fixture pytest.
        dau_ra_pham_vi: stdout giả cho lệnh có pathspec.
        dau_ra_toan_cay: stdout giả cho lệnh không có pathspec.
        loi: Nếu khác None, lệnh giả ném đúng ngoại lệ này thay vì trả kết quả.

    Returns:
        Danh sách lệnh đã bị gọi — mỗi phần tử là danh sách tham số của một lệnh.
    """
    cac_lenh: list[list[str]] = []

    def _run_gia(lenh, *args, **kwargs):
        lenh = list(lenh)
        cac_lenh.append(lenh)
        if loi is not None:
            raise loi("git gia lap khong chay duoc")
        if "status" not in lenh:
            dau_ra = ""
        else:
            dau_ra = dau_ra_pham_vi if "--" in lenh else dau_ra_toan_cay
        return subprocess.CompletedProcess(args=lenh, returncode=0, stdout=dau_ra, stderr="")

    monkeypatch.setattr(bd.subprocess, "run", _run_gia)
    return cac_lenh


def test_dong59_chi_tep_moi_trong_results_thi_co_khong_bat(monkeypatch):
    """Dòng 01: tệp kết quả của lượt đo trước không được làm cờ của lượt sau bật."""
    _gia_lap_git_status(
        monkeypatch,
        dau_ra_pham_vi="",
        dau_ra_toan_cay=(
            "?? results/bench_detect_20260903_2022.csv\n"
            "?? results/bench_detect_20260903_2022.meta.json\n"
        ),
    )

    assert bd._kiem_tra_git_dirty() is False


def test_dong60_lenh_git_co_kem_pham_vi_duong_dan(monkeypatch):
    """Dòng 02: lệnh phải mang pathspec, không hỏi toàn cây."""
    cac_lenh = _gia_lap_git_status(monkeypatch)

    bd._kiem_tra_git_dirty()

    assert len(cac_lenh) == 1
    lenh = cac_lenh[0]
    assert "--" in lenh
    for duong_dan in ("src", "scripts", "configs"):
        assert duong_dan in lenh
    # Pathspec phải nằm SAU dấu `--`, nếu không git hiểu "src" là tên nhánh.
    assert lenh.index("--") < lenh.index("src")


def test_dong61_sua_doi_trong_src_lam_co_bat(monkeypatch):
    """Dòng 03: mã nguồn đã theo dõi bị sửa -> cờ bật."""
    _gia_lap_git_status(monkeypatch, dau_ra_pham_vi=" M src/detector/yolo_face.py\n")

    assert bd._kiem_tra_git_dirty() is True


def test_dong62_tep_moi_chua_theo_doi_trong_src_lam_co_bat(monkeypatch):
    """Dòng 04 — ca canh P2-06c §5.1.

    Tệp .py mới chưa `git add` trong `src/` CÓ ảnh hưởng số đo nhưng không nằm trong lịch sử,
    đúng thứ `git_dirty` sinh ra để bắt. Vì vậy ca này khẳng định cả hai điều: đầu ra `??` làm
    cờ bật, VÀ lệnh git không được mang cờ bỏ tệp chưa theo dõi — cách sửa ngắn hơn mà §5.1
    cảnh báo, cũng chính là phép đột biến ĐB2.
    """
    cac_lenh = _gia_lap_git_status(monkeypatch, dau_ra_pham_vi="?? src/detector/backend_moi.py\n")

    assert bd._kiem_tra_git_dirty() is True

    lenh = cac_lenh[0]
    assert not any(
        tham_so.startswith("--untracked-files") or tham_so in {"-u", "-uno", "-unormal"}
        for tham_so in lenh
    )
    assert "--" in lenh and "src" in lenh


def test_dong63_sua_doi_requirements_lam_co_bat(monkeypatch):
    """Dòng 05: đổi phiên bản thư viện cũng đổi số đo, phải nằm trong phạm vi."""
    _gia_lap_git_status(monkeypatch, dau_ra_pham_vi=" M requirements.txt\n")

    assert bd._kiem_tra_git_dirty() is True


def test_dong64_khong_chay_duoc_git_thi_gia_dinh_xau_nhat(monkeypatch):
    """Dòng 06: không chạy được git -> True (P2-06c §5.2, giữ nguyên hành vi cũ)."""
    _gia_lap_git_status(monkeypatch, loi=OSError)

    assert bd._kiem_tra_git_dirty() is True


def test_dong65_toan_cay_goi_lenh_khong_kem_pham_vi(monkeypatch):
    """Dòng 07: hàm kiểm toàn cây hỏi cả thư mục, không giới hạn đường dẫn."""
    cac_lenh = _gia_lap_git_status(monkeypatch, dau_ra_toan_cay="?? results/x.csv\n")

    assert bd._kiem_tra_git_dirty_toan_cay() is True

    assert len(cac_lenh) == 1
    lenh = cac_lenh[0]
    assert "src" not in lenh
    assert "--" not in lenh


def test_dong66_meta_co_ca_hai_khoa(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 08: .meta.json phải mang cả `git_dirty` lẫn `git_dirty_toan_cay`."""
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that))

    assert ma == 0
    meta = _doc_meta_duy_nhat(thu_muc_kq)
    assert {"git_dirty", "git_dirty_toan_cay"} <= set(meta)
    assert {"git_dirty", "git_dirty_toan_cay"} <= set(bd._KHOA_META_BAT_BUOC)


def test_dong67_hai_khoa_doc_lap_nhau(monkeypatch, tmp_path, thu_muc_anh_that):
    """Dòng 09 — ca chốt của mã việc.

    Tái dựng đúng tình huống ba lượt đo ngày 03/09/2026: phạm vi mã nguồn sạch nhưng thư mục
    đã có tệp kết quả của lượt trước. Hai khoá phải mang hai giá trị khác nhau.
    """
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    thu_muc_kq = tmp_path / "ket_qua"
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", thu_muc_kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    _gia_lap_git_status(
        monkeypatch,
        dau_ra_pham_vi="",
        dau_ra_toan_cay="?? results/bench_detect_20260903_2022.csv\n",
    )

    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that))

    assert ma == 0
    meta = _doc_meta_duy_nhat(thu_muc_kq)
    assert meta["git_dirty"] is False
    assert meta["git_dirty_toan_cay"] is True


# ============================================================================
# P2-07 — đường vào từ camera cho benchmark_detect (test_camera_dong01-100)
# ============================================================================
#
# Mọi ca dưới đây: KHÔNG mô hình thật, KHÔNG camera thật, KHÔNG mạng, KHÔNG @slow.
# Bộ thu hình giả kế thừa BoThuHinh và trả mảng numpy (P2-07 §5.7); bộ phát hiện giả
# monkeypatch bd.tao_bo_phat_hien; camera giả monkeypatch bd.tao_bo_thu_hinh.


class _CameraGia(BoThuHinh):
    """Bộ thu hình giả — đếm số lần mo/dong/doc, cấu hình được hình dạng khung, độ trễ
    đọc, và tuỳ chọn ném LoiCamera ở khung thứ k (P2-07 §5.7)."""

    def __init__(
        self,
        hinh_dang: tuple[int, int, int] = (480, 640, 3),
        sleep_doc_s: float = 0.0,
        loi_o_khung: int | None = None,
        lop_loi: type[Exception] = LoiCamera,
    ) -> None:
        self._hinh_dang = hinh_dang
        self._sleep_doc_s = sleep_doc_s
        self._loi_o_khung = loi_o_khung
        self._lop_loi = lop_loi
        self.so_lan_mo = 0
        self.so_lan_dong = 0
        self.so_lan_doc = 0
        self._dang_mo = False

    def mo(self) -> None:
        self.so_lan_mo += 1
        self._dang_mo = True

    def doc_frame(self) -> np.ndarray:
        self.so_lan_doc += 1
        if self._loi_o_khung is not None and self.so_lan_doc == self._loi_o_khung:
            raise self._lop_loi(f"camera giả lỗi ở khung {self.so_lan_doc}")
        if self._sleep_doc_s:
            time.sleep(self._sleep_doc_s)
        return np.zeros(self._hinh_dang, dtype=np.uint8)

    def dong(self) -> None:
        self.so_lan_dong += 1
        self._dang_mo = False

    @property
    def dang_mo(self) -> bool:
        return self._dang_mo


def _factory_thu_hinh(cam: _CameraGia):
    """Hàm thay thế bd.tao_bo_thu_hinh — luôn trả về `cam` đã dựng sẵn."""

    def _factory(cfg):
        return cam

    return _factory


def _lam_factory_detector_camera(
    kich_thuoc_vao: int = 320,
    sleep_detect_s: float = 0.0,
    so_lan_co_mat: int | None = None,
    ten_backend: str = "onnx",
    bo_dem: list | None = None,
):
    """Sinh hàm thay thế tao_bo_phat_hien cho chế độ camera, giữ chữ ký (đường_dẫn, cfg)."""

    class _DetectorGiaCamera:
        def __init__(self, duong_dan, cfg) -> None:
            self.duong_dan = Path(duong_dan)
            self.cfg = cfg
            self._so_lan_goi = 0

        @property
        def kich_thuoc_vao(self) -> int:
            return kich_thuoc_vao

        @property
        def ten_backend(self) -> str:
            return ten_backend

        def detect(self, khung_hinh):
            self._so_lan_goi += 1
            # Đọc toàn mảng để latency_ms > 0 luôn đúng trên mọi máy (tránh chia cho 0).
            _ = int(khung_hinh.sum())
            if sleep_detect_s:
                time.sleep(sleep_detect_s)
            if so_lan_co_mat is not None and self._so_lan_goi > so_lan_co_mat:
                return []
            return [FaceBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9)]

    def _factory(duong_dan, cfg):
        if bo_dem is not None:
            bo_dem.append(Path(duong_dan))
        return _DetectorGiaCamera(duong_dan, cfg)

    return _factory


def _tao_capture_yaml(
    tmp_path: Path,
    backend: str = "auto",
    mock_w: int = 640,
    mock_h: int = 480,
    ocv_w: int = 640,
    ocv_h: int = 480,
    fps: int = 30,
    warmup: int = 5,
) -> Path:
    """Tạo tệp cấu hình thu hình tối giản, hợp lệ, với giá trị biết trước."""
    p = tmp_path / "capture_gia.yaml"
    p.write_text(
        (
            f"backend: {backend}\n"
            "opencv:\n"
            "  device_index: 0\n"
            f"  width: {ocv_w}\n"
            f"  height: {ocv_h}\n"
            f"  fps: {fps}\n"
            f"  warmup_frames: {warmup}\n"
            "  max_retry: 3\n"
            "mock:\n"
            f"  width: {mock_w}\n"
            f"  height: {mock_h}\n"
            "  source: synthetic\n"
            "  seed: 42\n"
            "  loop: true\n"
            "  max_frames: 0\n"
        ),
        encoding="utf-8",
    )
    return p


def _args_camera(
    mo_hinh=None,
    *extra,
    models: list | None = None,
    threads: tuple[str, ...] = ("1",),
    backend: str = "mock",
    khoang_cach: str = "1.0",
    noi_dung: str = "khong-nguoi",
):
    """Dựng danh sách tham số main() cho chế độ camera, đủ mọi cờ bắt buộc."""
    ms = models if models is not None else [str(mo_hinh)]
    return [
        "--nguon",
        "camera",
        "--capture-backend",
        backend,
        "--anh-sang",
        "trong nhà",
        # Dạng --opt=value để argparse không hiểu "-inf" là một cờ (P2-07 §5.2 kiểm inf/-inf/nan).
        f"--khoang-cach-m={khoang_cach}",
        "--noi-dung-khung",
        noi_dung,
        "--device-name",
        "PC test",
        "--models",
        *ms,
        "--threads",
        *threads,
        *extra,
    ]


def _setup_camera_ok(
    monkeypatch,
    tmp_path: Path,
    cam: _CameraGia | None = None,
    det=None,
    capture_yaml: Path | None = None,
    moi_truong: str = "pc_x86",
):
    """Chèn đủ bộ giả cho một lượt chạy main() chế độ camera thành công."""
    cam = cam if cam is not None else _CameraGia()
    monkeypatch.setattr(bd, "tao_bo_thu_hinh", _factory_thu_hinh(cam))
    monkeypatch.setattr(bd, "tao_bo_phat_hien", det or _lam_factory_detector_camera())
    monkeypatch.setattr(bd, "doc_nhiet_do_cpu", lambda: None)
    monkeypatch.setattr(bd, "xac_dinh_moi_truong", lambda: moi_truong)
    kq = tmp_path / "kq"
    kq.mkdir(exist_ok=True)
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", kq)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    cap = capture_yaml if capture_yaml is not None else _tao_capture_yaml(tmp_path)
    return mo_hinh, cap, kq, cam


def _bg_camera(
    lay_list: list[float], detect_list: list[float], n_faces: list[int] | None = None
) -> list[dict]:
    """Dựng danh sách bản ghi camera bằng tay, cho ca test tổng hợp/bảng in."""
    if n_faces is None:
        n_faces = [1] * len(lay_list)
    out = []
    for i, (lay, det, nf) in enumerate(zip(lay_list, detect_list, n_faces)):
        tong = lay + det
        out.append(
            {
                "backend": "onnx",
                "imgsz": 320,
                "threads": 1,
                "sample_idx": i,
                "latency_lay_khung_ms": lay,
                "latency_ms": det,
                "latency_tong_ms": tong,
                "fps_instant": 1000.0 / det,
                "fps_tong_instant": 1000.0 / tong,
                "n_faces": nf,
                "conf_top": 0.9 if nf else None,
                "cpu_temp_c": None,
            }
        )
    return out


def _meta_camera_hop_le() -> dict:
    """Meta hợp lệ đủ 24 khoá bắt buộc của chế độ camera."""
    m = _meta_hop_le()
    m["seed"] = None
    m["nguon"] = "camera"
    m["conditions"] = {
        "anh_sang": "trong nhà",
        "khoang_cach_m": 1.0,
        "noi_dung_khung": "khong-nguoi",
    }
    m["config_file_capture"] = "configs/capture.yaml"
    m["config_snapshot_capture"] = {"backend": "mock"}
    return m


_COT_CSV_CAMERA_MONG_DOI = [
    "run_id",
    "backend",
    "imgsz",
    "threads",
    "sample_idx",
    "latency_lay_khung_ms",
    "latency_ms",
    "latency_tong_ms",
    "fps_instant",
    "fps_tong_instant",
    "n_faces",
    "conf_top",
    "cpu_temp_c",
]

_KHOA_DATASET_CAMERA = {
    "backend_thu_hinh",
    "do_phan_giai_yeu_cau",
    "do_phan_giai_that",
    "khop_do_phan_giai",
    "fps_khai_bao_trong_cau_hinh",
    "warmup_frames_thu_hinh",
    "n_frame_do",
    "n_frame_lam_nong",
}


# ---------------------------------------------------------------------------
# §8.1 — Cờ, chế độ và ranh giới giữa hai chế độ (dòng 01-24)
# ---------------------------------------------------------------------------


def test_camera_dong01_khong_nguon_la_dia(monkeypatch, tmp_path, thu_muc_anh_that):
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    ma = bd.main(_tham_so_main(mo_hinh, thu_muc_anh_that))
    assert ma == 0
    meta = _doc_meta_duy_nhat(tmp_path / "kq")
    assert meta["nguon"] == "dia"


def test_camera_dong02_nguon_la_argparse_thoat():
    with pytest.raises(SystemExit):
        bd.main(["--device-name", "PC test", "--nguon", "lung-tung"])


def test_camera_dong03_camera_thieu_capture_backend_tra_1(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    ma = bd.main(
        [
            "--nguon",
            "camera",
            "--anh-sang",
            "trong nhà",
            "--khoang-cach-m",
            "1.0",
            "--noi-dung-khung",
            "khong-nguoi",
            "--device-name",
            "PC test",
        ]
    )
    assert ma == 1


def test_camera_dong04_thong_bao_neu_ten_co_capture_backend(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    bd.main(
        [
            "--nguon",
            "camera",
            "--anh-sang",
            "trong nhà",
            "--khoang-cach-m",
            "1.0",
            "--noi-dung-khung",
            "khong-nguoi",
            "--device-name",
            "PC test",
        ]
    )
    assert "--capture-backend" in capsys.readouterr().out


def test_camera_dong05_capture_backend_auto_argparse_thoat():
    with pytest.raises(SystemExit):
        bd.main(
            [
                "--nguon",
                "camera",
                "--capture-backend",
                "auto",
                "--anh-sang",
                "trong nhà",
                "--khoang-cach-m",
                "1.0",
                "--noi-dung-khung",
                "khong-nguoi",
                "--device-name",
                "PC test",
            ]
        )


def test_camera_dong06_camera_tu_choi_anh_dir(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    # Đối chứng: không có --anh-dir thì chạy được (canh ĐB15 — nếu default là chuỗi thì
    # camera luôn hỏng và dòng này đỏ).
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert (
        bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), "--anh-dir", str(tmp_path)))
        == 1
    )


def test_camera_dong07_thong_bao_neu_ten_co_anh_dir(monkeypatch, tmp_path, capsys):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), "--anh-dir", str(tmp_path)))
    assert "--anh-dir" in capsys.readouterr().out


def test_camera_dong08_camera_tu_choi_seed(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), "--seed", "7")) == 1


def test_camera_dong09_thong_bao_neu_ten_co_seed(monkeypatch, tmp_path, capsys):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), "--seed", "7"))
    assert "--seed" in capsys.readouterr().out


def test_camera_dong10_dia_tu_choi_anh_sang(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    ma = bd.main(["--device-name", "PC test", "--nguon", "dia", "--anh-sang", "sáng"])
    assert ma == 1


def test_camera_dong11_thong_bao_neu_ten_co_anh_sang(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    bd.main(["--device-name", "PC test", "--nguon", "dia", "--anh-sang", "sáng"])
    assert "--anh-sang" in capsys.readouterr().out


def test_camera_dong12_dia_tu_choi_capture_backend(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    ma = bd.main(["--device-name", "PC test", "--nguon", "dia", "--capture-backend", "mock"])
    assert ma == 1


def test_camera_dong13_camera_thieu_anh_sang_tra_1(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    ma = bd.main(
        [
            "--nguon",
            "camera",
            "--capture-backend",
            "mock",
            "--khoang-cach-m",
            "1.0",
            "--noi-dung-khung",
            "khong-nguoi",
            "--device-name",
            "PC test",
        ]
    )
    assert ma == 1


def test_camera_dong14_camera_thieu_khoang_cach_tra_1(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    ma = bd.main(
        [
            "--nguon",
            "camera",
            "--capture-backend",
            "mock",
            "--anh-sang",
            "trong nhà",
            "--noi-dung-khung",
            "khong-nguoi",
            "--device-name",
            "PC test",
        ]
    )
    assert ma == 1


def test_camera_dong15_camera_thieu_noi_dung_khung_tra_1(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    ma = bd.main(
        [
            "--nguon",
            "camera",
            "--capture-backend",
            "mock",
            "--anh-sang",
            "trong nhà",
            "--khoang-cach-m",
            "1.0",
            "--device-name",
            "PC test",
        ]
    )
    assert ma == 1


def test_camera_dong16_noi_dung_khung_la_argparse_thoat():
    with pytest.raises(SystemExit):
        bd.main(
            [
                "--nguon",
                "camera",
                "--capture-backend",
                "mock",
                "--anh-sang",
                "trong nhà",
                "--khoang-cach-m",
                "1.0",
                "--noi-dung-khung",
                "dung-dau",
                "--device-name",
                "PC test",
            ]
        )


def test_camera_dong17_khoang_cach_0_tra_1(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), khoang_cach="0")) == 1


def test_camera_dong18_khoang_cach_am_tra_1(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), khoang_cach="-1")) == 1


def test_camera_dong19_khoang_cach_inf_tra_1(monkeypatch, tmp_path, capsys):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), khoang_cach="inf")) == 1
    assert "hữu hạn" in capsys.readouterr().out


def test_camera_dong20_khoang_cach_am_inf_tra_1(monkeypatch, tmp_path, capsys):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), khoang_cach="-inf")) == 1
    assert "hữu hạn" in capsys.readouterr().out


def test_camera_dong21_khoang_cach_nan_tra_1(monkeypatch, tmp_path, capsys):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), khoang_cach="nan")) == 1
    assert "hữu hạn" in capsys.readouterr().out


def test_camera_dong22_khoang_cach_1_tra_0(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), khoang_cach="1.0")) == 0


def test_camera_dong23_khoang_cach_vao_meta(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), khoang_cach="1.0")) == 0
    meta = _doc_meta_duy_nhat(kq)
    assert meta["conditions"]["khoang_cach_m"] == pytest.approx(1.0)


def test_camera_dong24_seed_la_null(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    meta = _doc_meta_duy_nhat(kq)
    assert meta["seed"] is None


# ---------------------------------------------------------------------------
# §8.2 — Ranh giới bấm giờ (dòng 25-34)
# ---------------------------------------------------------------------------


def _do_camera_truc_tiep(
    monkeypatch, tmp_path, sleep_doc_s, sleep_detect_s, so_luong=5, so_lam_nong=1
):
    monkeypatch.setattr(
        bd, "tao_bo_phat_hien", _lam_factory_detector_camera(sleep_detect_s=sleep_detect_s)
    )
    cam = _CameraGia(sleep_doc_s=sleep_doc_s)
    cam.mo()
    bg = bd.do_mot_cau_hinh_camera(tmp_path / "gia.onnx", _cfg_co_ban(), cam, so_luong, so_lam_nong)
    return bg, cam


def test_camera_dong25_vung_lay_khung_do_dung_phan_lay_khung(monkeypatch, tmp_path):
    bg, _cam = _do_camera_truc_tiep(monkeypatch, tmp_path, 0.040, 0.002)
    assert all(r["latency_lay_khung_ms"] > 30 for r in bg)


def test_camera_dong26_vung_suy_luan_do_dung_phan_suy_luan(monkeypatch, tmp_path):
    bg, _cam = _do_camera_truc_tiep(monkeypatch, tmp_path, 0.040, 0.002)
    assert all(r["latency_ms"] < 20 for r in bg)


def test_camera_dong27_latency_tong_la_tong_so_hoc(monkeypatch, tmp_path):
    bg, _cam = _do_camera_truc_tiep(monkeypatch, tmp_path, 0.040, 0.002)
    assert all(
        abs(r["latency_tong_ms"] - r["latency_lay_khung_ms"] - r["latency_ms"]) < 1e-9 for r in bg
    )


def test_camera_dong28_fps_instant_nghich_dao_latency_ms(monkeypatch, tmp_path):
    bg, _cam = _do_camera_truc_tiep(monkeypatch, tmp_path, 0.040, 0.002)
    assert all(r["fps_instant"] == pytest.approx(1000.0 / r["latency_ms"]) for r in bg)


def test_camera_dong29_fps_tong_instant_nghich_dao_latency_tong(monkeypatch, tmp_path):
    bg, _cam = _do_camera_truc_tiep(monkeypatch, tmp_path, 0.040, 0.002)
    assert all(r["fps_tong_instant"] == pytest.approx(1000.0 / r["latency_tong_ms"]) for r in bg)


def test_camera_dong30_so_ban_ghi_dung_so_luong(monkeypatch, tmp_path):
    bg, _cam = _do_camera_truc_tiep(monkeypatch, tmp_path, 0.0, 0.0)
    assert len(bg) == 5


def test_camera_dong31_doc_du_lam_nong_cong_do(monkeypatch, tmp_path):
    _bg, cam = _do_camera_truc_tiep(monkeypatch, tmp_path, 0.0, 0.0)
    assert cam.so_lan_doc == 6


def test_camera_dong32_sample_idx_lien_tuc_tu_0(monkeypatch, tmp_path):
    bg, _cam = _do_camera_truc_tiep(monkeypatch, tmp_path, 0.0, 0.0)
    assert [r["sample_idx"] for r in bg] == [0, 1, 2, 3, 4]


def test_camera_dong33_imgsz_tu_doi_tuong_phat_hien(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_detector_camera(kich_thuoc_vao=320))
    cam = _CameraGia()
    cam.mo()
    bg = bd.do_mot_cau_hinh_camera(tmp_path / "gia.onnx", _cfg_co_ban(), cam, 3, 1)
    assert bg[0]["imgsz"] == 320


def test_camera_dong34_so_luong_duoi_1_nem_loi(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_detector_camera())
    cam = _CameraGia()
    cam.mo()
    with pytest.raises(LoiCauHinh):
        bd.do_mot_cau_hinh_camera(tmp_path / "gia.onnx", _cfg_co_ban(), cam, 0, 1)


# ---------------------------------------------------------------------------
# §8.3 — Vòng đời camera và fail-safe (dòng 35-45)
# ---------------------------------------------------------------------------


def test_camera_dong35_main_mo_camera_dung_mot_lan(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert cam.so_lan_mo == 1


def test_camera_dong36_do_mot_cau_hinh_camera_khong_goi_mo_dong():
    nguon = inspect.getsource(bd.do_mot_cau_hinh_camera)
    cay = ast.parse(nguon)
    cam_goi = {"mo", "dong"}
    vi_pham = []
    for node in ast.walk(cay):
        if isinstance(node, ast.Call):
            ten = None
            if isinstance(node.func, ast.Attribute):
                ten = node.func.attr
            elif isinstance(node.func, ast.Name):
                ten = node.func.id
            if ten in cam_goi:
                vi_pham.append(ten)
    assert vi_pham == []


def test_camera_dong37_main_dong_camera_duong_thanh_cong(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert cam.so_lan_dong >= 1


def test_camera_dong38_mat_camera_giua_chung_tra_1(monkeypatch, tmp_path):
    cam = _CameraGia(loi_o_khung=12)
    mo_hinh, cap, _kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 1


def test_camera_dong39_mat_camera_van_dong_camera(monkeypatch, tmp_path):
    cam = _CameraGia(loi_o_khung=12)
    mo_hinh, cap, _kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam)
    bd.main(_args_camera(mo_hinh, "--capture-config", str(cap)))
    assert cam.so_lan_dong >= 1


def test_camera_dong40_mat_camera_khong_ghi_tep(monkeypatch, tmp_path):
    cam = _CameraGia(loi_o_khung=12)
    mo_hinh, cap, kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam)
    bd.main(_args_camera(mo_hinh, "--capture-config", str(cap)))
    assert list(kq.rglob("*")) == []


def test_camera_dong41_mat_camera_thong_bao_neu_nguyen_nhan(monkeypatch, tmp_path, capsys):
    cam = _CameraGia(loi_o_khung=12)
    mo_hinh, cap, _kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam)
    bd.main(_args_camera(mo_hinh, "--capture-config", str(cap)))
    assert "camera" in capsys.readouterr().out


def test_camera_dong42_camera_binh_thuong_tra_0(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0


def test_camera_dong43_dry_run_khong_mo_camera(monkeypatch, tmp_path):
    def _no(cfg):
        raise AssertionError("dry-run KHÔNG được mở camera")

    monkeypatch.setattr(bd, "tao_bo_thu_hinh", _no)
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--dry-run")) == 0


def test_camera_dong44_dry_run_khong_ghi_tep(monkeypatch, tmp_path):
    monkeypatch.setattr(bd, "tao_bo_thu_hinh", _factory_thu_hinh(_CameraGia()))
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    bd.main(_args_camera(mo_hinh, "--dry-run"))
    assert not (tmp_path / "kq").exists()


def test_camera_dong45_dry_run_bang_neu_backend_thu_hinh(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    bd.main(_args_camera(mo_hinh, "--dry-run"))
    assert "mock" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# §8.4 — Một cấu hình, không ma trận (dòng 46-51)
# ---------------------------------------------------------------------------


def test_camera_dong46_hai_mo_hinh_tra_1(monkeypatch, tmp_path):
    _mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    m1 = _tao_mo_hinh_gia(tmp_path, "a.onnx")
    m2 = _tao_mo_hinh_gia(tmp_path, "b.onnx")
    ma = bd.main(
        _args_camera(models=[str(m1), str(m2)], mo_hinh=None) + ["--capture-config", str(cap)]
    )
    assert ma == 1


def test_camera_dong47_thong_bao_neu_models(monkeypatch, tmp_path, capsys):
    _mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    m1 = _tao_mo_hinh_gia(tmp_path, "a.onnx")
    m2 = _tao_mo_hinh_gia(tmp_path, "b.onnx")
    bd.main(_args_camera(models=[str(m1), str(m2)]) + ["--capture-config", str(cap)])
    assert "--models" in capsys.readouterr().out


def test_camera_dong48_hai_muc_luong_tra_1(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    ma = bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), threads=("1", "2")))
    assert ma == 1


def test_camera_dong49_thong_bao_neu_threads(monkeypatch, tmp_path, capsys):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    bd.main(_args_camera(mo_hinh, "--capture-config", str(cap), threads=("1", "2")))
    assert "--threads" in capsys.readouterr().out


def test_camera_dong50_mot_mo_hinh_mot_muc_luong_tra_0(monkeypatch, tmp_path):
    mo_hinh, cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0


def test_camera_dong51_tom_tat_dung_mot_o(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    meta = _doc_meta_duy_nhat(kq)
    assert len(meta["tom_tat"]) == 1


# ---------------------------------------------------------------------------
# §8.5 — Không hồi quy chế độ dia (dòng 52-58)
# ---------------------------------------------------------------------------


def test_camera_dong52_cot_csv_van_muoi_cot():
    assert bd._COT_CSV == [
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


def test_camera_dong53_khoa_meta_van_hai_muoi():
    assert len(bd._KHOA_META_BAT_BUOC) == 20


def test_camera_dong54_mac_dinh_anh_dir_phan_giai_dung(monkeypatch, tmp_path, thu_muc_anh_that):
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    ds = sorted(thu_muc_anh_that.glob("*.jpg"))

    def _chon_anh_gia(thu_muc, so_luong, seed):
        return ds[:so_luong]

    monkeypatch.setattr(bd, "chon_anh", _chon_anh_gia)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    ma = bd.main(["--device-name", "PC test", "--models", str(mo_hinh), "--threads", "1"])
    assert ma == 0
    meta = _doc_meta_duy_nhat(tmp_path / "kq")
    assert Path(meta["dataset"]["anh_dir"]) == Path("data/impostor/lfw_original")


def test_camera_dong55_mac_dinh_seed_phan_giai_dung(monkeypatch, tmp_path, thu_muc_anh_that):
    monkeypatch.setattr(bd, "tao_bo_phat_hien", _lam_factory_gia())
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    ds = sorted(thu_muc_anh_that.glob("*.jpg"))
    ghi = {}

    def _chon_anh_gia(thu_muc, so_luong, seed):
        ghi["seed"] = seed
        return ds[:so_luong]

    monkeypatch.setattr(bd, "chon_anh", _chon_anh_gia)
    mo_hinh = _tao_mo_hinh_gia(tmp_path)
    ma = bd.main(["--device-name", "PC test", "--models", str(mo_hinh), "--threads", "1"])
    assert ma == 0
    meta = _doc_meta_duy_nhat(tmp_path / "kq")
    assert meta["seed"] == 42
    assert ghi["seed"] == 42


def test_camera_dong56_dry_run_dia_in_thu_muc_mac_dinh(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(bd, "_THU_MUC_KET_QUA_MAC_DINH", tmp_path / "kq")
    ma = bd.main(["--device-name", "PC test", "--dry-run"])
    assert ma == 0
    assert "lfw_original" in capsys.readouterr().out


def test_camera_dong57_ghi_ket_qua_chu_ky_cu_van_muoi_cot(tmp_path):
    csv_path, _ = bd.ghi_ket_qua(
        tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), _meta_hop_le()
    )
    with open(csv_path, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == list(bd._COT_CSV)


def test_camera_dong58_tep_csv_cu_van_doc_duoc(tmp_path):
    csv_path, _ = bd.ghi_ket_qua(
        tmp_path, "bench_detect_20260819_1200", _ban_ghi_csv_mau(), _meta_hop_le()
    )
    with open(csv_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows[0]) == 10


# ---------------------------------------------------------------------------
# §8.6 — CSV và metadata chế độ camera (dòng 59-83)
# ---------------------------------------------------------------------------


def test_camera_dong59_ghi_dung_hai_tep(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert len(list(kq.iterdir())) == 2


def test_camera_dong60_ten_csv_dung_khuon(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    p_csv = next(iter(kq.glob("*.csv")))
    assert re.fullmatch(r"bench_detect_camera_\d{8}_\d{4}\.csv", p_csv.name)


def test_camera_dong61_ten_meta_dung_khuon(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    p_meta = next(iter(kq.glob("*.meta.json")))
    assert re.fullmatch(r"bench_detect_camera_\d{8}_\d{4}\.meta\.json", p_meta.name)


def test_camera_dong62_csv_camera_dung_muoi_ba_cot(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    p_csv = next(iter(kq.glob("*.csv")))
    with open(p_csv, newline="", encoding="utf-8") as f:
        header = next(csv.reader(f))
    assert header == _COT_CSV_CAMERA_MONG_DOI


def test_camera_dong63_so_dong_csv_bang_n_frames(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap)) + ["--n-frames", "100"]) == 0
    p_csv = next(iter(kq.glob("*.csv")))
    with open(p_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 100


def test_camera_dong64_nguon_la_camera(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert _doc_meta_duy_nhat(kq)["nguon"] == "camera"


def test_camera_dong65_meta_du_hai_muoi_bon_khoa(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    meta = _doc_meta_duy_nhat(kq)
    assert set(meta) >= set(bd._KHOA_META_BAT_BUOC_CAMERA)


def test_camera_dong66_conditions_du_ba_khoa_con(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    meta = _doc_meta_duy_nhat(kq)
    assert set(meta["conditions"]) == {"anh_sang", "khoang_cach_m", "noi_dung_khung"}


def test_camera_dong67_dataset_du_tam_khoa_con(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    meta = _doc_meta_duy_nhat(kq)
    assert set(meta["dataset"]) == _KHOA_DATASET_CAMERA


def test_camera_dong68_dataset_khong_co_anh_dir(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert "anh_dir" not in _doc_meta_duy_nhat(kq)["dataset"]


def test_camera_dong69_do_phan_giai_that_tu_khung(monkeypatch, tmp_path):
    cap = _tao_capture_yaml(tmp_path, mock_w=1280, mock_h=720)
    cam = _CameraGia(hinh_dang=(480, 640, 3))
    mo_hinh, cap, kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam, capture_yaml=cap)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    meta = _doc_meta_duy_nhat(kq)
    assert meta["dataset"]["do_phan_giai_that"] == "640x480"


def test_camera_dong70_do_phan_giai_yeu_cau_tu_cau_hinh(monkeypatch, tmp_path):
    cap = _tao_capture_yaml(tmp_path, mock_w=1280, mock_h=720)
    cam = _CameraGia(hinh_dang=(480, 640, 3))
    mo_hinh, cap, kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam, capture_yaml=cap)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    meta = _doc_meta_duy_nhat(kq)
    assert meta["dataset"]["do_phan_giai_yeu_cau"] == "1280x720"


def test_camera_dong71_khop_do_phan_giai_false(monkeypatch, tmp_path):
    cap = _tao_capture_yaml(tmp_path, mock_w=1280, mock_h=720)
    cam = _CameraGia(hinh_dang=(480, 640, 3))
    mo_hinh, cap, kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam, capture_yaml=cap)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert _doc_meta_duy_nhat(kq)["dataset"]["khop_do_phan_giai"] is False


def test_camera_dong72_lech_do_phan_giai_co_canh_bao(monkeypatch, tmp_path):
    cap = _tao_capture_yaml(tmp_path, mock_w=1280, mock_h=720)
    cam = _CameraGia(hinh_dang=(480, 640, 3))
    mo_hinh, cap, kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam, capture_yaml=cap)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert _doc_meta_duy_nhat(kq)["canh_bao_do_phan_giai"] != ""


def test_camera_dong73_khop_do_phan_giai_khong_co_canh_bao(monkeypatch, tmp_path):
    cap = _tao_capture_yaml(tmp_path, mock_w=640, mock_h=480)
    cam = _CameraGia(hinh_dang=(480, 640, 3))
    mo_hinh, cap, kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam, capture_yaml=cap)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert "canh_bao_do_phan_giai" not in _doc_meta_duy_nhat(kq)


def test_camera_dong74_n_frame_do_la_so_dong_that(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    p_csv = next(iter(kq.glob("*.csv")))
    with open(p_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    meta = _doc_meta_duy_nhat(kq)
    assert meta["dataset"]["n_frame_do"] == len(rows)


def test_camera_dong75_fps_khai_bao_null_voi_mock(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert _doc_meta_duy_nhat(kq)["dataset"]["fps_khai_bao_trong_cau_hinh"] is None


def test_camera_dong76_mock_sinh_canh_bao_nguon_gia_lap(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert _doc_meta_duy_nhat(kq)["canh_bao_nguon_gia_lap"] != ""


def test_camera_dong77_canh_bao_nguon_gia_lap_vao_notes(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert "giả lập" in _doc_meta_duy_nhat(kq)["notes"]


def test_camera_dong78_config_snapshot_capture_backend_da_ghi_de(monkeypatch, tmp_path):
    cap = _tao_capture_yaml(tmp_path, backend="auto")
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path, capture_yaml=cap)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert _doc_meta_duy_nhat(kq)["config_snapshot_capture"]["backend"] == "mock"


def test_camera_dong79_cau_hinh_thu_hinh_hong_tra_1(monkeypatch, tmp_path):
    mo_hinh, _cap, _kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    ma = bd.main(_args_camera(mo_hinh, "--capture-config", str(tmp_path / "khong_ton_tai.yaml")))
    assert ma == 1


def test_camera_dong80_meta_thieu_conditions_nem_loi(tmp_path):
    meta = _meta_camera_hop_le()
    del meta["conditions"]
    with pytest.raises(LoiCauHinh):
        bd.ghi_ket_qua(
            tmp_path,
            "bench_detect_camera_20260907_1200",
            _ban_ghi_csv_mau(),
            meta,
            khoa_bat_buoc=bd._KHOA_META_BAT_BUOC_CAMERA,
        )


def test_camera_dong81_meta_du_khoa_ghi_thanh_cong(tmp_path):
    csv_path, meta_path = bd.ghi_ket_qua(
        tmp_path,
        "bench_detect_camera_20260907_1200",
        _ban_ghi_csv_mau(),
        _meta_camera_hop_le(),
        cot=bd._COT_CSV_CAMERA,
        khoa_bat_buoc=bd._KHOA_META_BAT_BUOC_CAMERA,
    )
    assert csv_path.exists() and meta_path.exists()


def test_camera_dong82_mo_ta_nguon_camera_backend_la_nem_loi():
    with pytest.raises(LoiCauHinh):
        bd.mo_ta_nguon_camera(
            {"mock": {"width": 1, "height": 1}},
            "backend-la",
            np.zeros((2, 2, 3), dtype=np.uint8),
        )


def test_camera_dong83_cpu_temp_rong_khong_phai_none(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    p_csv = next(iter(kq.glob("*.csv")))
    with open(p_csv, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        assert row["cpu_temp_c"] == ""
        assert row["cpu_temp_c"] != "None"


# ---------------------------------------------------------------------------
# §8.7 — Tổng hợp và bảng in ra (dòng 84-100)
# ---------------------------------------------------------------------------


def test_camera_dong84_lay_khung_tb_khop_mean():
    lay = list(range(1, 101))
    bg = _bg_camera([float(x) for x in lay], [5.0] * 100)
    assert bd.tong_hop_camera(bg)["lay_khung_tb"] == pytest.approx(np.mean(lay))


def test_camera_dong85_lay_khung_do_lech_khop_std():
    lay = list(range(1, 101))
    bg = _bg_camera([float(x) for x in lay], [5.0] * 100)
    assert bd.tong_hop_camera(bg)["lay_khung_do_lech"] == pytest.approx(np.std(lay))


def test_camera_dong86_lay_khung_p50_khop_percentile():
    lay = list(range(1, 101))
    bg = _bg_camera([float(x) for x in lay], [5.0] * 100)
    assert bd.tong_hop_camera(bg)["lay_khung_p50"] == pytest.approx(np.percentile(lay, 50))


def test_camera_dong87_lay_khung_p95_khop_percentile():
    lay = list(range(1, 101))
    bg = _bg_camera([float(x) for x in lay], [5.0] * 100)
    assert bd.tong_hop_camera(bg)["lay_khung_p95"] == pytest.approx(np.percentile(lay, 95))


def test_camera_dong88_tong_p95_khop_percentile_tren_cot_tong():
    lay = list(range(1, 101))
    det = list(range(2, 202, 2))
    bg = _bg_camera([float(x) for x in lay], [float(x) for x in det])
    v_tong = [x + y for x, y in zip(lay, det)]
    assert bd.tong_hop_camera(bg)["tong_p95"] == pytest.approx(np.percentile(v_tong, 95))


def test_camera_dong89_fps_tong_tb_nghich_dao_tong_tb():
    bg = _bg_camera([30.0] * 10, [20.0] * 10)
    assert bd.tong_hop_camera(bg)["fps_tong_tb"] == pytest.approx(20.0)


def test_camera_dong90_dat_chi_tieu_tong_true_tren_nguong():
    bg = _bg_camera([30.0] * 10, [20.0] * 10)
    assert bd.tong_hop_camera(bg)["dat_chi_tieu_tong"] is True


def test_camera_dong91_dat_chi_tieu_tong_false_duoi_nguong():
    bg = _bg_camera([100.0] * 10, [100.0] * 10)
    assert bd.tong_hop_camera(bg)["dat_chi_tieu_tong"] is False


def test_camera_dong92_tong_hop_cu_dung_lai_duoc_tren_ban_ghi_camera():
    lat_detect = [10.0, 20.0, 30.0, 40.0, 50.0]
    bg = _bg_camera([5.0] * 5, lat_detect)
    assert bd.tong_hop(bg)["fps_tb"] == pytest.approx(1000.0 / np.mean(lat_detect))


def test_camera_dong93_hai_tu_dien_tong_hop_khong_trung_khoa():
    bg = _bg_camera([30.0] * 10, [20.0] * 10)
    assert set(bd.tong_hop(bg)) & set(bd.tong_hop_camera(bg)) == set()


def test_camera_dong94_ban_ghi_rong_nem_loi():
    with pytest.raises(LoiCauHinh):
        bd.tong_hop_camera([])


def test_camera_dong95_bang_in_co_cot_fps_dau_cuoi(capsys):
    bg = _bg_camera([30.0] * 10, [20.0] * 10)
    bd._in_bang_camera({**bd.tong_hop(bg), **bd.tong_hop_camera(bg)}, bd.tong_hop(bg))
    assert "đầu-cuối" in capsys.readouterr().out


def test_camera_dong96_bang_in_neu_tran_toc_do_khung(capsys):
    bg = _bg_camera([30.0] * 10, [20.0] * 10)
    bd._in_bang_camera({**bd.tong_hop(bg), **bd.tong_hop_camera(bg)}, bd.tong_hop(bg))
    assert "trần" in capsys.readouterr().out


def test_camera_dong97_nghi_dem_khung_co_canh_bao(monkeypatch, tmp_path):
    cam = _CameraGia(hinh_dang=(48, 64, 3), sleep_doc_s=0.0)
    det = _lam_factory_detector_camera(sleep_detect_s=0.010)
    mo_hinh, cap, kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam, det=det)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert _doc_meta_duy_nhat(kq)["canh_bao_dem_khung"] != ""


def test_camera_dong98_lay_khung_cham_hon_khong_co_canh_bao(monkeypatch, tmp_path):
    cam = _CameraGia(hinh_dang=(48, 64, 3), sleep_doc_s=0.010)
    det = _lam_factory_detector_camera(sleep_detect_s=0.0)
    mo_hinh, cap, kq, cam = _setup_camera_ok(monkeypatch, tmp_path, cam=cam, det=det)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert "canh_bao_dem_khung" not in _doc_meta_duy_nhat(kq)


def test_camera_dong99_ngoai_pi5_co_canh_bao_hieu_nang(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path, moi_truong="pc_x86")
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert _doc_meta_duy_nhat(kq)["canh_bao_hieu_nang"] != ""


def test_camera_dong100_moi_truong_thuoc_ba_ma_hop_le(monkeypatch, tmp_path):
    mo_hinh, cap, kq, _cam = _setup_camera_ok(monkeypatch, tmp_path)
    assert bd.main(_args_camera(mo_hinh, "--capture-config", str(cap))) == 0
    assert _doc_meta_duy_nhat(kq)["moi_truong"] in {"pc_x86", "docker_arm64", "pi5"}
