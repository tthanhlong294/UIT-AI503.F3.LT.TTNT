"""Kiểm thử cho scripts/export_detector_ncnn.py (mã việc P2-04, dọn chú thích ở P0-05 §9).

Ca cần export NCNN thật (`models/yolov8n-face.pt` + `ultralytics`/`torch`/`ncnn`) được đánh
dấu `@pytest.mark.slow`; fixture của chúng gọi `pytest.importorskip` cho `ultralytics` và
`ncnn` (kéo theo `torch`). Chúng ghi thư mục NCNN tạm vào `tmp_path`, KHÔNG ghi vào `models/`
hay `results/` thật.

Tình trạng ba gói:
- `ncnn` CÓ trong `requirements.txt` (dòng 9) — phụ thuộc CHẠY, cần trên cả Pi lẫn máy dev.
- `ultralytics` chỉ có trong `requirements-dev.txt`; `torch` không được ghim ở tệp nào, nó
  đến kèm theo `ultralytics`.

⚠️ Dù `ncnn` đã được ghim, cả ba gói `ncnn`/`ultralytics`/`torch` VẪN KHÔNG BAO GIỜ được
import ở mức module (xem §7.2, §8 đặc tả P2-04): `ultralytics`/`torch` không có trên thiết bị
đích, và ca kiểm thử không được giả định môi trường đã cài đúng bản `ncnn` đã ghim. Import ở
mức module làm `pytest` chết ngay khâu thu thập, kéo đổ cả bộ test — nên `pytest.importorskip`
giữ nguyên và `pytest -m "not slow" --collect-only` chạy được kể cả khi máy không có chúng.

Các ca không-slow giả lập `ultralytics.YOLO` bằng cách monkeypatch
`scripts.export_detector_ncnn._tao_mo_hinh_yolo` — hàm chỉ dẫn ở mức module đặt riêng
cho mục đích này.
"""

import datetime
import json
import re
import shutil
from pathlib import Path

import numpy as np
import pytest

from scripts.export_detector import ghi_ket_qua
from scripts.export_detector_ncnn import (
    _in_bang_ket_qua,
    _ten_tep_ket_qua_ncnn,
    export_ncnn_mot_kich_thuoc,
    kiem_chung_tuong_duong_ncnn,
    kiem_tra_thu_muc_ncnn,
    main,
    thu_thap_metadata_ncnn,
    xac_dinh_moi_truong,
)
from src.common.exceptions import LoiCauHinh, LoiMoHinh

_WEIGHTS_THAT = Path("models/yolov8n-face.pt")


# ============================================================================
# Tiện ích chung
# ============================================================================


def _sao_chep_weights_tam(thu_muc: Path) -> Path:
    """Sao chép trọng số .pt thật vào thư mục tạm — export không ghi vào models/ thật."""
    dich = thu_muc / "yolov8n-face.pt"
    shutil.copy2(_WEIGHTS_THAT, dich)
    return dich


def _ban_ghi_hop_le() -> dict:
    """Bản ghi đủ tám khoá bắt buộc của `ghi_ket_qua` (dùng chung với P2-01)."""
    return {
        "n_anh": 50,
        "n_khop_so_mat": 49,
        "iou_trung_binh": 0.94,
        "iou_nho_nhat": 0.88,
        "sai_so_diem_moc_trung_binh": 1.7,
        "sai_so_diem_moc_lon_nhat": 4.9,
        "dat": True,
        "meta": {
            "commit": "abc123",
            "cau_hinh": {"export": {}},
            "phien_ban": {"ncnn": "1.0.20260526"},
            "thiet_bi": {"hostname": "may-test"},
            "thoi_diem": "2026-08-27T00:00:00+07:00",
            "seed": 42,
        },
    }


# --- Giả lập tối thiểu đối tượng `Results` của ultralytics ---


class _FakeTensor:
    def __init__(self, arr):
        self._arr = np.asarray(arr, dtype=np.float64)

    def cpu(self):
        return self

    def numpy(self):
        return self._arr

    def __len__(self):
        return len(self._arr)


class _FakeBoxes:
    def __init__(self, xyxy, conf=None):
        arr = np.asarray(xyxy, dtype=np.float64).reshape(-1, 4)
        self.xyxy = _FakeTensor(arr)
        self.conf = _FakeTensor(np.ones(len(arr)) if conf is None else np.asarray(conf))

    def __len__(self):
        return len(self.xyxy)


class _FakeKeypoints:
    def __init__(self, xy):
        self.xy = _FakeTensor(np.asarray(xy, dtype=np.float64))


class _FakeResults:
    def __init__(self, boxes=None, keypoints=None):
        self.boxes = boxes
        self.keypoints = keypoints


class _FakeModel:
    """Trả cùng một `_FakeResults` cho mọi ảnh, hoặc tra theo `str(source)` nếu là dict."""

    def __init__(self, ket_qua):
        self._ket_qua = ket_qua

    def predict(self, source, **kwargs):
        if isinstance(self._ket_qua, dict):
            return [self._ket_qua[str(source)]]
        return [self._ket_qua]


def _patch_yolo(monkeypatch, kq_pt, kq_ncnn) -> None:
    """Thay `_tao_mo_hinh_yolo`: đường dẫn .pt -> model PT, còn lại -> model NCNN."""

    def gia_lap(duong_dan, task="pose"):
        if str(duong_dan).endswith(".pt"):
            return _FakeModel(kq_pt)
        return _FakeModel(kq_ncnn)

    monkeypatch.setattr("scripts.export_detector_ncnn._tao_mo_hinh_yolo", gia_lap)


def _ket_qua_mot_mat() -> _FakeResults:
    return _FakeResults(
        _FakeBoxes([[10.0, 10.0, 60.0, 60.0]]),
        _FakeKeypoints([[[20.0, 20.0], [40.0, 20.0], [30.0, 35.0], [22.0, 50.0], [38.0, 50.0]]]),
    )


def _ket_qua_rong() -> _FakeResults:
    return _FakeResults(_FakeBoxes(np.zeros((0, 4))), _FakeKeypoints(np.zeros((0, 5, 2))))


# ============================================================================
# §8.1 — Export (dòng 01-06)
# ============================================================================


def test_dong01_trong_so_khong_ton_tai_nem_loi(tmp_path):
    with pytest.raises(LoiMoHinh):
        export_ncnn_mot_kich_thuoc(Path("khong/ton/tai.pt"), 320, 1, tmp_path)


def test_dong02_ten_thu_muc_ra_dung_quy_uoc(tmp_path):
    p = export_ncnn_mot_kich_thuoc(_WEIGHTS_THAT, 320, 1, tmp_path, dry_run=True)
    assert p.name == "yolov8n-face-320_ncnn_model"


def test_dong03_dry_run_khong_tao_gi(tmp_path):
    out_dir = tmp_path / "ra"
    out_dir.mkdir()
    truoc = set(out_dir.rglob("*"))

    export_ncnn_mot_kich_thuoc(_WEIGHTS_THAT, 320, 1, out_dir, dry_run=True)

    assert set(out_dir.rglob("*")) == truoc


def test_dong04_320_va_640_hai_thu_muc_khac_nhau(tmp_path):
    p320 = export_ncnn_mot_kich_thuoc(_WEIGHTS_THAT, 320, 1, tmp_path, dry_run=True)
    p640 = export_ncnn_mot_kich_thuoc(_WEIGHTS_THAT, 640, 1, tmp_path, dry_run=True)
    assert p320 != p640


@pytest.fixture(scope="module")
def _ncnn_320(tmp_path_factory):
    """Export NCNN thật một lần ở imgsz=320, dùng chung cho dòng 05 và 06."""
    pytest.importorskip("ultralytics")
    pytest.importorskip("ncnn")
    thu_muc = tmp_path_factory.mktemp("ncnn_320")
    weights = _sao_chep_weights_tam(thu_muc)
    duong_dan = export_ncnn_mot_kich_thuoc(weights, 320, 1, thu_muc)
    return weights, thu_muc, duong_dan


@pytest.mark.slow
def test_dong05_export_that_du_ba_tep(_ncnn_320):
    _, _, duong_dan = _ncnn_320
    kq = kiem_tra_thu_muc_ncnn(duong_dan)  # không ném lỗi
    assert kq["tong_kich_thuoc_byte"] > 0


@pytest.mark.slow
def test_dong06_export_lai_ghi_de_khong_nem_loi(_ncnn_320):
    weights, thu_muc, p1 = _ncnn_320
    p2 = export_ncnn_mot_kich_thuoc(weights, 320, 1, thu_muc)
    assert p1 == p2
    assert p2.is_dir()


# ============================================================================
# §8.2 — kiem_tra_thu_muc_ncnn (dòng 07-12)
# ============================================================================


def test_dong07_thu_muc_khong_ton_tai_nem_loi(tmp_path):
    with pytest.raises(LoiMoHinh):
        kiem_tra_thu_muc_ncnn(tmp_path / "khong-co")


def _dung_thu_muc_ncnn_gia(thu_muc: Path, co: tuple[str, ...]) -> Path:
    thu_muc.mkdir(parents=True, exist_ok=True)
    for ten in co:
        (thu_muc / ten).write_text("noi-dung", encoding="utf-8")
    return thu_muc


def test_dong08_thieu_param_nem_loi_neu_ten_tep(tmp_path):
    d = _dung_thu_muc_ncnn_gia(tmp_path / "m", ("model.ncnn.bin", "metadata.yaml"))
    with pytest.raises(LoiMoHinh, match="param"):
        kiem_tra_thu_muc_ncnn(d)


def test_dong09_thieu_bin_nem_loi_neu_ten_tep(tmp_path):
    d = _dung_thu_muc_ncnn_gia(tmp_path / "m", ("model.ncnn.param", "metadata.yaml"))
    with pytest.raises(LoiMoHinh, match="bin"):
        kiem_tra_thu_muc_ncnn(d)


def test_dong08b_thieu_model_ncnn_py_van_hop_le(tmp_path):
    # Chỉ ba tệp bắt buộc, KHÔNG có model_ncnn.py — script mẫu của PNNX, không nằm trên
    # đường nạp lại của ultralytics (§3). Hàm phải coi thư mục là hợp lệ.
    d = _dung_thu_muc_ncnn_gia(
        tmp_path / "m", ("model.ncnn.param", "model.ncnn.bin", "metadata.yaml")
    )
    assert not (d / "model_ncnn.py").exists()
    kq = kiem_tra_thu_muc_ncnn(d)  # không ném lỗi
    assert set(kq) >= {"param", "bin", "metadata", "tong_kich_thuoc_byte"}


def test_dong10_thieu_metadata_nem_loi_neu_ten_tep(tmp_path):
    d = _dung_thu_muc_ncnn_gia(tmp_path / "m", ("model.ncnn.param", "model.ncnn.bin"))
    with pytest.raises(LoiMoHinh, match="metadata"):
        kiem_tra_thu_muc_ncnn(d)


def test_dong11_mot_tep_rong_nem_loi(tmp_path):
    d = _dung_thu_muc_ncnn_gia(
        tmp_path / "m", ("model.ncnn.param", "model.ncnn.bin", "metadata.yaml")
    )
    (d / "model.ncnn.bin").write_bytes(b"")
    with pytest.raises(LoiMoHinh):
        kiem_tra_thu_muc_ncnn(d)


def test_dong12_du_ba_tep_khong_rong_tra_ve_bon_khoa(tmp_path):
    d = _dung_thu_muc_ncnn_gia(
        tmp_path / "m", ("model.ncnn.param", "model.ncnn.bin", "metadata.yaml")
    )
    kq = kiem_tra_thu_muc_ncnn(d)
    assert set(kq) >= {"param", "bin", "metadata", "tong_kich_thuoc_byte"}
    assert kq["tong_kich_thuoc_byte"] > 0


# ============================================================================
# §8.3 — kiem_chung_tuong_duong_ncnn (dòng 13-18)
# ============================================================================


def test_dong13_danh_sach_anh_rong_nem_loicauhinh():
    with pytest.raises(LoiCauHinh):
        kiem_chung_tuong_duong_ncnn(Path("x.pt"), Path("x_ncnn_model"), [], 320, 0.5, 0.45, 5.0)


def test_dong14_ncnn_co_khung_khong_diem_moc_nem_loimohinh(tmp_path, monkeypatch):
    kq_pt = _ket_qua_mot_mat()
    kq_ncnn = _FakeResults(_FakeBoxes([[10.0, 10.0, 60.0, 60.0]]), keypoints=None)
    _patch_yolo(monkeypatch, kq_pt, kq_ncnn)

    with pytest.raises(LoiMoHinh) as exc_info:
        kiem_chung_tuong_duong_ncnn(
            Path("w.pt"), tmp_path / "ncnn_model", [tmp_path / "a.jpg"], 320, 0.5, 0.45, 5.0
        )
    assert "điểm mốc" in str(exc_info.value)


def test_dong15_ca_hai_khong_co_mat_khong_nem_loi(tmp_path, monkeypatch):
    rong = _ket_qua_rong()
    _patch_yolo(monkeypatch, rong, rong)

    kq = kiem_chung_tuong_duong_ncnn(
        Path("w.pt"), tmp_path / "ncnn_model", [tmp_path / "a.jpg"], 320, 0.5, 0.45, 5.0
    )
    assert kq["n_anh"] == 1


def test_dong16_tong_hop_du_tam_khoa(tmp_path, monkeypatch):
    same = _ket_qua_mot_mat()
    _patch_yolo(monkeypatch, same, same)

    kq = kiem_chung_tuong_duong_ncnn(
        Path("w.pt"), tmp_path / "ncnn_model", [tmp_path / "a.jpg"], 320, 0.5, 0.45, 5.0
    )
    assert set(kq) >= {
        "n_anh",
        "n_khop_so_mat",
        "iou_trung_binh",
        "iou_nho_nhat",
        "sai_so_diem_moc_trung_binh",
        "sai_so_diem_moc_lon_nhat",
        "dat",
        "thu_muc_ncnn",
    }


def test_dong17_hai_mo_hinh_giong_het_thi_dat(tmp_path, monkeypatch):
    same = _ket_qua_mot_mat()
    _patch_yolo(monkeypatch, same, same)

    kq = kiem_chung_tuong_duong_ncnn(
        Path("w.pt"), tmp_path / "ncnn_model", [tmp_path / "a.jpg"], 320, 0.5, 0.45, 5.0
    )
    assert kq["dat"] is True
    assert kq["iou_nho_nhat"] == 1.0


def test_dong18_lech_so_mat_qua_5_phan_tram_thi_khong_dat(tmp_path, monkeypatch):
    anh = [tmp_path / f"{i}.jpg" for i in range(10)]
    mot_mat = _ket_qua_mot_mat()
    hai_mat = _FakeResults(
        _FakeBoxes([[10.0, 10.0, 60.0, 60.0], [70.0, 70.0, 90.0, 90.0]]),
        _FakeKeypoints(np.zeros((2, 5, 2))),
    )
    map_pt = {str(p): mot_mat for p in anh}
    map_ncnn = {str(p): mot_mat for p in anh}
    map_ncnn[str(anh[0])] = hai_mat
    map_ncnn[str(anh[1])] = hai_mat
    _patch_yolo(monkeypatch, map_pt, map_ncnn)

    kq = kiem_chung_tuong_duong_ncnn(
        Path("w.pt"), tmp_path / "ncnn_model", anh, 320, 0.5, 0.45, 5.0
    )
    assert kq["dat"] is False


# ============================================================================
# §8.4 — Metadata và ghi kết quả (dòng 19-22, kèm 20b/20c/20d)
# ============================================================================


def test_dong19_thu_thap_metadata_du_bay_truong():
    meta = thu_thap_metadata_ncnn({"export": {}}, 42)
    assert set(meta) >= {
        "commit",
        "cau_hinh",
        "phien_ban",
        "thiet_bi",
        "thoi_diem",
        "seed",
        "moi_truong",
    }


def test_dong20_phien_ban_co_khoa_ncnn():
    meta = thu_thap_metadata_ncnn({"export": {}}, 42)
    assert "ncnn" in meta["phien_ban"]


def test_dong20b_moi_truong_nhan_dung_mot_trong_ba_ma():
    assert xac_dinh_moi_truong() in {"pc_x86", "docker_arm64", "pi5"}


def test_dong20c_co_dockerenv_thi_docker_arm64_bat_ke_kien_truc(monkeypatch):
    monkeypatch.setattr("scripts.export_detector_ncnn.Path.exists", lambda self: True)
    monkeypatch.setattr("scripts.export_detector_ncnn.platform.machine", lambda: "x86_64")
    assert xac_dinh_moi_truong() == "docker_arm64"


def test_dong20d_khong_dockerenv_may_aarch64_thi_pi5(monkeypatch):
    monkeypatch.setattr("scripts.export_detector_ncnn.Path.exists", lambda self: False)
    monkeypatch.setattr("scripts.export_detector_ncnn.platform.machine", lambda: "aarch64")
    assert xac_dinh_moi_truong() == "pi5"


def test_dong21_ten_tep_ket_qua_dung_khuon():
    ten = _ten_tep_ket_qua_ncnn(
        datetime.datetime(2026, 8, 27, 19, 50, tzinfo=datetime.timezone.utc)
    )
    assert re.fullmatch(r"export_ncnn_\d{8}_\d{4}\.json", ten)


def test_dong22_ghi_ra_ca_hai_tep_doc_lai_giu_nguyen(tmp_path):
    p = tmp_path / "export_ncnn_20260827_1950.json"
    ban_ghi = _ban_ghi_hop_le()
    ghi_ket_qua(p, ban_ghi)

    assert p.exists() and p.with_suffix(".meta.json").exists()
    noi_dung = json.loads(p.read_text(encoding="utf-8"))
    assert noi_dung["iou_trung_binh"] == ban_ghi["iou_trung_binh"]


# ============================================================================
# §8.5 — Luồng chính (dòng 23-27)
# ============================================================================


def test_dong23_dry_run_khong_ghi_tep_nao():
    models_dir = Path("models")
    results_dir = Path("results")
    truoc_models = set(models_dir.rglob("*"))
    truoc_results = set(results_dir.rglob("*"))

    assert main(["--dry-run"]) == 0

    assert set(models_dir.rglob("*")) == truoc_models
    assert set(results_dir.rglob("*")) == truoc_results


def test_dong24_anh_dir_khong_ton_tai_tra_ve_1(capsys):
    assert main(["--anh-dir", "khong/ton/tai"]) == 1
    assert "download_lfw" in capsys.readouterr().out


def test_dong25_anh_dir_rong_tra_ve_1_thong_bao_khac(tmp_path, capsys):
    thu_muc_rong = tmp_path / "rong"
    thu_muc_rong.mkdir()

    assert main(["--anh-dir", str(thu_muc_rong)]) == 1

    ra = capsys.readouterr().out
    assert "rỗng" in ra or "không có ảnh" in ra
    assert "download_lfw" not in ra


def test_dong26_cau_hinh_hong_tra_ve_1(tmp_path):
    cfg_hong = tmp_path / "detect_hong.yaml"
    cfg_hong.write_text("export:\n  weights_pt: models/yolov8n-face.pt\n", encoding="utf-8")
    assert main(["--config", str(cfg_hong)]) == 1


def test_dong27_khong_tim_thay_config_tra_ve_1(tmp_path):
    assert main(["--config", str(tmp_path / "khong_ton_tai.yaml")]) == 1


# ============================================================================
# Ghim định dạng bảng CLI — ngoài §8 đặc tả
# ============================================================================


def test_dong28_bang_cli_dung_ky_hieu_khoa_hoc(capsys):
    """Xuất xứ: CẦN SỬA-1, docs/review/P2-04-export-ncnn.review.md. Chưa có dòng tương
    ứng trong §8 đặc tả.

    `_in_bang_ket_qua` phải giữ đúng bậc độ lớn của số đo: sai số 2,33e-05 px không
    được làm tròn thành "0.00", nếu không bảng — thứ người đọc chép thẳng vào báo cáo —
    sẽ tuyên bố "khớp tuyệt đối" mạnh hơn hẳn thứ đã đo (R5).
    """
    ket_qua = {
        "320": {
            "n_anh": 50,
            "n_khop_so_mat": 50,
            "iou_trung_binh": 0.9999996,
            "iou_nho_nhat": 0.9999971,
            "sai_so_diem_moc_trung_binh": 2.33e-05,
            "sai_so_diem_moc_lon_nhat": 5.50e-05,
            "dat": True,
        }
    }

    _in_bang_ket_qua(ket_qua)
    ra = capsys.readouterr().out

    dong_320 = [d for d in ra.splitlines() if d.startswith("| 320 |")]
    assert len(dong_320) == 1
    o = [c.strip() for c in dong_320[0].split("|")]
    ss_tb, ss_max = o[6], o[7]

    assert "0.00" not in ss_tb
    assert "0.00" not in ss_max
    assert "e-05" in ss_tb
    assert "e-05" in ss_max
