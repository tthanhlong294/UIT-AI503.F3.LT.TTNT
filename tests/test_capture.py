"""Kiểm thử cho khối thu hình."""

import logging
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from src.capture.factory import tao_bo_thu_hinh
from src.capture.mock_camera import CameraGiaLap
from src.capture.opencv_camera import CameraOpenCV, _giai_ma_fourcc, _ma_hoa_fourcc
from src.common.exceptions import LoiCamera, LoiCauHinh


def test_01_danh_sach_file_trang():
    """Đúng các file trong danh sách trắng §2, không thừa file nào trong src/capture."""
    goc = Path(__file__).resolve().parents[1]
    assert {p.name for p in (goc / "src" / "capture").glob("*.py")} == {
        "__init__.py",
        "base.py",
        "opencv_camera.py",
        "mock_camera.py",
        "factory.py",
    }


def test_02_khong_hardcode_tham_so():
    """Kiểm tra không hardcode kích thước hoặc thông số."""
    src_dir = os.path.join(os.path.dirname(__file__), "..", "src", "capture")
    for file_name in os.listdir(src_dir):
        if file_name.endswith(".py"):
            file_path = os.path.join(src_dir, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                # Kiểm tra một vài số như 1280, 720, 30 không xuất hiện như hằng số trong code
                # Dùng một kiểm tra cơ bản.
                assert "1280" not in content, f"Tìm thấy số hardcode trong {file_name}"
                assert "720" not in content, f"Tìm thấy số hardcode trong {file_name}"
                assert "30" not in content, f"Tìm thấy số hardcode trong {file_name}"


def test_03_mock_tra_ve_dung_dinh_dang():
    """Kiểm tra định dạng frame của mock."""
    cfg = {"backend": "mock", "mock": {"width": 640, "height": 480}}
    with tao_bo_thu_hinh(cfg) as cam:
        frame = cam.doc_frame()
        assert frame.shape == (480, 640, 3)
        assert frame.dtype == np.uint8


def test_04_mock_cung_seed():
    """Cùng seed trả về khung hình giống nhau."""
    cfg1 = {"backend": "mock", "mock": {"width": 100, "height": 100, "seed": 42}}
    cfg2 = {"backend": "mock", "mock": {"width": 100, "height": 100, "seed": 42}}
    with tao_bo_thu_hinh(cfg1) as cam1, tao_bo_thu_hinh(cfg2) as cam2:
        frame1 = cam1.doc_frame()
        frame2 = cam2.doc_frame()
        assert np.array_equal(frame1, frame2)


def test_04b_mock_mo_lai_cung_seed():
    """Mở lại camera giả lập phải trả lại chuỗi giống nhau (đặt lại seed)."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10, "seed": 42}}
    cam = tao_bo_thu_hinh(cfg)
    cam.mo()
    frame1 = cam.doc_frame()
    cam.dong()
    cam.mo()
    frame2 = cam.doc_frame()
    assert np.array_equal(frame1, frame2)


@patch("cv2.VideoCapture")
def test_03b_opencv_bgr(mock_video_capture):
    """OpenCV camera không hoán vị kênh màu (giữ BGR)."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    pixel = np.array([[[1, 2, 3]]], dtype=np.uint8)
    mock_cap.read.return_value = (True, pixel)
    mock_video_capture.return_value = mock_cap

    cfg = {"backend": "opencv", "opencv": {"device_index": 0, "width": 1, "height": 1}}
    with tao_bo_thu_hinh(cfg) as cam:
        frame = cam.doc_frame()
        assert frame[0, 0].tolist() == [1, 2, 3]


def test_05_mock_khac_seed():
    """Khác seed trả về khung hình khác nhau."""
    cfg1 = {"backend": "mock", "mock": {"width": 100, "height": 100, "seed": 42}}
    cfg2 = {"backend": "mock", "mock": {"width": 100, "height": 100, "seed": 99}}
    with tao_bo_thu_hinh(cfg1) as cam1, tao_bo_thu_hinh(cfg2) as cam2:
        frame1 = cam1.doc_frame()
        frame2 = cam2.doc_frame()
        assert not np.array_equal(frame1, frame2)


def test_06_mock_khung_hinh_lien_tiep_khac_nhau():
    """Hai khung hình liên tiếp khác nhau."""
    cfg = {"backend": "mock", "mock": {"width": 100, "height": 100}}
    with tao_bo_thu_hinh(cfg) as cam:
        frame1 = cam.doc_frame()
        frame2 = cam.doc_frame()
        assert not np.array_equal(frame1, frame2)


def test_07_doc_chua_mo_raise_loi():
    """Đọc khi chưa mở."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10}}
    cam = tao_bo_thu_hinh(cfg)
    with pytest.raises(LoiCamera):
        cam.doc_frame()


def test_08_doc_sau_khi_dong_raise_loi():
    """Đọc sau khi đóng."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10}}
    with tao_bo_thu_hinh(cfg) as cam:
        pass
    with pytest.raises(LoiCamera):
        cam.doc_frame()


def test_09_dong_hai_lan_an_toan():
    """Đóng hai lần an toàn."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10}}
    cam = tao_bo_thu_hinh(cfg)
    cam.mo()
    cam.dong()
    cam.dong()  # Không lỗi


def test_10_trang_thai_dang_mo():
    """Kiểm tra dang_mo."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10}}
    cam = tao_bo_thu_hinh(cfg)
    assert not cam.dang_mo
    cam.mo()
    assert cam.dang_mo
    cam.dong()
    assert not cam.dang_mo


def test_11_context_manager():
    """Kiểm tra with statement."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10}}
    cam = tao_bo_thu_hinh(cfg)
    with cam:
        assert cam.dang_mo
    assert not cam.dang_mo


def test_12_ngoai_le_trong_context():
    """Ngoại lệ trong block thì vẫn đóng."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10}}
    cam = tao_bo_thu_hinh(cfg)
    with pytest.raises(ValueError), cam:
        raise ValueError("Test error")
    assert not cam.dang_mo


def test_13_max_frames_loop_false():
    """max_frames = N, loop=False, đọc quá N raise LoiCamera."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10, "max_frames": 2, "loop": False}}
    with tao_bo_thu_hinh(cfg) as cam:
        cam.doc_frame()
        cam.doc_frame()
        with pytest.raises(LoiCamera):
            cam.doc_frame()


def test_14_max_frames_loop_true():
    """max_frames = N, loop=True, quay vòng."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10, "max_frames": 2, "loop": True}}
    with tao_bo_thu_hinh(cfg) as cam:
        cam.doc_frame()
        cam.doc_frame()
        cam.doc_frame()  # N+1 không lỗi
        cam.doc_frame()


def test_15_mock_source_directory_khong_ton_tai(tmp_path):
    """mock.source = directory rỗng/không tồn tại raise LoiCauHinh."""
    cfg = {
        "backend": "mock",
        "mock": {
            "width": 10,
            "height": 10,
            "source": "directory",
            "source_dir": str(tmp_path / "fake"),
        },
    }
    with pytest.raises(LoiCauHinh):
        tao_bo_thu_hinh(cfg)


def test_15a_mock_source_directory_hop_le(tmp_path):
    """mock.source = directory đọc đúng ảnh."""
    import cv2

    dir_path = tmp_path / "images"
    dir_path.mkdir()
    anh1 = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
    anh2 = np.random.randint(0, 256, (10, 10, 3), dtype=np.uint8)
    cv2.imwrite(str(dir_path / "1.png"), anh1)
    cv2.imwrite(str(dir_path / "2.png"), anh2)

    cfg = {
        "backend": "mock",
        "mock": {
            "width": 10,
            "height": 10,
            "source": "directory",
            "source_dir": str(dir_path),
        },
    }
    with tao_bo_thu_hinh(cfg) as cam:
        f1 = cam.doc_frame()
        f2 = cam.doc_frame()
        assert np.array_equal(f1, anh1)
        assert np.array_equal(f2, anh2)


def test_15b_directory_va_synthetic_khac_nhau(tmp_path):
    """Hai chế độ directory và synthetic phải khác nhau."""
    import cv2

    dir_path = tmp_path / "images"
    dir_path.mkdir()
    cv2.imwrite(str(dir_path / "1.png"), np.zeros((10, 10, 3), dtype=np.uint8))

    cfg_dir = {
        "backend": "mock",
        "mock": {
            "width": 10,
            "height": 10,
            "source": "directory",
            "source_dir": str(dir_path),
            "seed": 42,
        },
    }
    cfg_syn = {
        "backend": "mock",
        "mock": {"width": 10, "height": 10, "source": "synthetic", "seed": 42},
    }
    with tao_bo_thu_hinh(cfg_dir) as cam_dir, tao_bo_thu_hinh(cfg_syn) as cam_syn:
        f_dir = cam_dir.doc_frame()
        f_syn = cam_syn.doc_frame()
        assert not np.array_equal(f_dir, f_syn)


def test_15c_mock_source_directory_thu_muc_rong(tmp_path):
    """Thư mục tồn tại nhưng không có ảnh hợp lệ."""
    dir_path = tmp_path / "empty"
    dir_path.mkdir()
    cfg = {
        "backend": "mock",
        "mock": {"width": 10, "height": 10, "source": "directory", "source_dir": str(dir_path)},
    }
    with pytest.raises(LoiCauHinh):
        tao_bo_thu_hinh(cfg)


def test_16_backend_mock():
    """backend = mock trả về CameraGiaLap."""
    cfg = {"backend": "mock", "mock": {"width": 10, "height": 10}}
    cam = tao_bo_thu_hinh(cfg)
    assert isinstance(cam, CameraGiaLap)


def test_17_backend_khong_hop_le():
    """backend không hợp lệ."""
    cfg = {"backend": "xyz"}
    with pytest.raises(LoiCauHinh):
        tao_bo_thu_hinh(cfg)


def test_18_thieu_key_mock_width():
    """Thiếu mock.width."""
    cfg = {"backend": "mock", "mock": {"height": 10}}
    with pytest.raises(LoiCauHinh):
        tao_bo_thu_hinh(cfg)


@patch("cv2.VideoCapture")
def test_19_backend_auto_roi_ve_mock(mock_video_capture):
    """backend = auto không có camera rơi về mock."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_video_capture.return_value = mock_cap

    cfg = {
        "backend": "auto",
        "opencv": {"device_index": 0, "width": 640, "height": 480},
        "mock": {"width": 10, "height": 10},
    }
    cam = tao_bo_thu_hinh(cfg)
    assert isinstance(cam, CameraGiaLap)


@patch("cv2.VideoCapture")
def test_20_backend_opencv_that_bai(mock_video_capture):
    """backend = opencv thất bại mở raise LoiCamera."""
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_video_capture.return_value = mock_cap

    cfg = {"backend": "opencv", "opencv": {"device_index": 0, "width": 640, "height": 480}}
    cam = tao_bo_thu_hinh(cfg)
    with pytest.raises(LoiCamera):
        cam.mo()

    # Test raise cv2.error
    import cv2

    mock_video_capture.side_effect = cv2.error("hong")
    cam2 = tao_bo_thu_hinh(cfg)
    with pytest.raises(LoiCamera):
        cam2.mo()


@patch("cv2.VideoCapture", side_effect=AssertionError("Không được chạm camera thật"))
def test_21_chay_duoc_khong_can_camera(_mvc):
    """Toàn bộ luồng mock chạy được mà không đụng tới thiết bị thật."""
    cfg = {"backend": "mock", "mock": {"width": 16, "height": 16, "seed": 1}}
    with tao_bo_thu_hinh(cfg) as cam:
        assert cam.doc_frame().shape == (16, 16, 3)


# ---------------------------------------------------------------------------
# P2-08 — công cụ đo: camera giả ghi lại THỨ TỰ lời gọi set() và mô phỏng việc
# webcam từ chối cấu hình một cách im lặng (docs/dac-ta/P2-08-camera-fourcc-fps.md §5.6).
# ---------------------------------------------------------------------------

_TEN_THUOC_TINH = {
    cv2.CAP_PROP_FOURCC: "FOURCC",
    cv2.CAP_PROP_FRAME_WIDTH: "FRAME_WIDTH",
    cv2.CAP_PROP_FRAME_HEIGHT: "FRAME_HEIGHT",
    cv2.CAP_PROP_FPS: "FPS",
}


class VideoCaptureGia:
    """Camera giả: ghi lại THỨ TỰ các lời gọi set() và mô phỏng việc từ chối im lặng."""

    def __init__(
        self,
        chi_so,
        *,
        tu_choi=(),
        fourcc_ban_dau="YUYV",
        fps_ban_dau=10.0,
        kich_thuoc_ban_dau=(1280, 720),
        kich_thuoc_khung=None,
        mo_duoc=True,
        doc_duoc=True,
    ):
        self.chi_so = chi_so
        self.tu_choi = tuple(tu_choi)
        self._fourcc = fourcc_ban_dau
        self._fps = fps_ban_dau
        self._rong, self._cao = kich_thuoc_ban_dau
        self._kich_thuoc_khung = kich_thuoc_khung
        self.mo_duoc = mo_duoc
        self.doc_duoc = doc_duoc
        self.thu_tu_set = []
        self.gia_tri_set = []
        self.so_lan_read = 0
        self.da_release = False

    def isOpened(self):
        return self.mo_duoc

    def set(self, prop, gia_tri):
        ten = _TEN_THUOC_TINH[prop]
        self.thu_tu_set.append(ten)
        self.gia_tri_set.append((ten, gia_tri))
        if ten in self.tu_choi:
            return False
        if ten == "FOURCC":
            self._fourcc = _giai_ma_fourcc(gia_tri)
        elif ten == "FRAME_WIDTH":
            self._rong = int(gia_tri)
        elif ten == "FRAME_HEIGHT":
            self._cao = int(gia_tri)
        elif ten == "FPS":
            self._fps = float(gia_tri)
        return True

    def get(self, prop):
        ten = _TEN_THUOC_TINH[prop]
        if ten == "FOURCC":
            return float(_ma_hoa_fourcc(self._fourcc))
        if ten == "FPS":
            return self._fps
        if ten == "FRAME_WIDTH":
            return float(self._rong)
        return float(self._cao)

    def read(self):
        self.so_lan_read += 1
        if not self.doc_duoc:
            return (False, None)
        if self._kich_thuoc_khung is not None:
            rong, cao = self._kich_thuoc_khung
        else:
            rong, cao = self._rong, self._cao
        return (True, np.zeros((cao, rong, 3), np.uint8))

    def release(self):
        self.da_release = True


def _cfg(**kw):
    """Dựng nhánh `opencv` của cấu hình với ba khoá bắt buộc mặc định."""
    d = {"device_index": 0, "width": 1280, "height": 720}
    d.update(kw)
    return d


def _gan(monkeypatch, **kwargs):
    """Vá cv2.VideoCapture bằng một VideoCaptureGia duy nhất; trả về đối tượng giả đó."""
    cam = VideoCaptureGia(0, **kwargs)

    def _tao(chi_so):
        cam.chi_so = chi_so
        return cam

    monkeypatch.setattr(cv2, "VideoCapture", _tao)
    return cam


def _gan_chuoi(monkeypatch, *cameras):
    """Vá cv2.VideoCapture để trả lần lượt từng VideoCaptureGia trong `cameras`."""
    it = iter(cameras)

    def _tao(chi_so):
        cam = next(it)
        cam.chi_so = chi_so
        return cam

    monkeypatch.setattr(cv2, "VideoCapture", _tao)


# --- Nhóm A — khoá `fourcc` trong cấu hình -------------------------------------


def test_fourcc_dong01_thieu_khoa_fourcc_dung_mac_dinh():
    assert CameraOpenCV(_cfg()).thong_so_thuc_te["fourcc_yeu_cau"] == "MJPG"


def test_fourcc_dong02_fourcc_yuyv():
    assert CameraOpenCV(_cfg(fourcc="YUYV")).thong_so_thuc_te["fourcc_yeu_cau"] == "YUYV"


def test_fourcc_dong03_fourcc_rong_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fourcc=""))


def test_fourcc_dong04_fourcc_ba_ky_tu_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fourcc="MJP"))


def test_fourcc_dong05_fourcc_nam_ky_tu_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fourcc="MJPGX"))


def test_fourcc_dong06_fourcc_kieu_int_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fourcc=1234))


def test_fourcc_dong07_fourcc_none_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fourcc=None))


def test_fourcc_dong08_fourcc_list_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fourcc=["M", "J", "P", "G"]))


def test_fourcc_dong09_fourcc_ky_tu_dieu_khien_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fourcc="MJP\n"))


def test_fourcc_dong10_fourcc_ngoai_ascii_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fourcc="MJPé"))


def test_fourcc_dong11_fourcc_khoang_trang_cuoi_hop_le():
    assert CameraOpenCV(_cfg(fourcc="MJP ")).thong_so_thuc_te["fourcc_yeu_cau"] == "MJP "


def test_fourcc_dong12_thong_bao_chua_ten_khoa_fourcc():
    with pytest.raises(LoiCauHinh) as exc_info:
        CameraOpenCV(_cfg(fourcc=""))
    assert "opencv.fourcc" in str(exc_info.value)


# --- Nhóm B — khoá `fps` trong cấu hình --------------------------------------


def test_fourcc_dong13_thieu_khoa_fps_la_none():
    assert CameraOpenCV(_cfg()).thong_so_thuc_te["fps_yeu_cau"] is None


def test_fourcc_dong14_fps_30():
    assert CameraOpenCV(_cfg(fps=30)).thong_so_thuc_te["fps_yeu_cau"] == 30.0


def test_fourcc_dong15_fps_0_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fps=0))


def test_fourcc_dong16_fps_am_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fps=-1))


def test_fourcc_dong17_fps_inf_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fps=float("inf")))


def test_fourcc_dong18_fps_am_inf_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fps=float("-inf")))


def test_fourcc_dong19_fps_nan_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fps=float("nan")))


def test_fourcc_dong20_fps_chuoi_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fps="abc"))


def test_fourcc_dong21_fps_none_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fps=None))


def test_fourcc_dong22_fps_bool_raise():
    with pytest.raises(LoiCauHinh):
        CameraOpenCV(_cfg(fps=True))


def test_fourcc_dong23_thong_bao_chua_ten_khoa_fps():
    with pytest.raises(LoiCauHinh) as exc_info:
        CameraOpenCV(_cfg(fps=0))
    assert "opencv.fps" in str(exc_info.value)


# --- Nhóm C — THỨ TỰ lời gọi set() ------------------------------------------


def test_fourcc_dong24_thu_tu_set_day_du(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG", fps=25)).mo()
    assert cam_gia.thu_tu_set == ["FOURCC", "FRAME_WIDTH", "FRAME_HEIGHT", "FPS"]


def test_fourcc_dong25_thu_tu_set_khong_fps(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG")).mo()
    assert cam_gia.thu_tu_set == ["FOURCC", "FRAME_WIDTH", "FRAME_HEIGHT"]


def test_fourcc_dong26_fourcc_truoc_width(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG", fps=25)).mo()
    assert cam_gia.thu_tu_set.index("FOURCC") < cam_gia.thu_tu_set.index("FRAME_WIDTH")


def test_fourcc_dong27_fps_sau_height(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG", fps=25)).mo()
    assert cam_gia.thu_tu_set.index("FPS") > cam_gia.thu_tu_set.index("FRAME_HEIGHT")


def test_fourcc_dong28_gia_tri_fourcc_ma_hoa(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG", fps=25)).mo()
    assert int(dict(cam_gia.gia_tri_set)["FOURCC"]) == 0x47504A4D


def test_fourcc_dong29_gia_tri_fps(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG", fps=25)).mo()
    assert dict(cam_gia.gia_tri_set)["FPS"] == 25.0


def test_fourcc_dong30_gia_tri_width(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG", fps=25, width=800, height=600)).mo()
    assert dict(cam_gia.gia_tri_set)["FRAME_WIDTH"] == 800


# --- Nhóm D — hai hàm trợ giúp FOURCC --------------------------------------


def test_fourcc_dong31_ma_hoa_mjpg():
    assert _ma_hoa_fourcc("MJPG") == 0x47504A4D


def test_fourcc_dong32_ma_hoa_yuyv():
    assert _ma_hoa_fourcc("YUYV") == 0x56595559


def test_fourcc_dong33_khep_kin_mjpg():
    assert _giai_ma_fourcc(_ma_hoa_fourcc("MJPG")) == "MJPG"


def test_fourcc_dong34_khep_kin_nv12():
    assert _giai_ma_fourcc(_ma_hoa_fourcc("NV12")) == "NV12"


def test_fourcc_dong35_giai_ma_khong():
    assert _giai_ma_fourcc(0) == "????"


def test_fourcc_dong36_giai_ma_am_mot():
    assert _giai_ma_fourcc(-1.0) == "????"


def test_fourcc_dong37_giai_ma_tu_float():
    assert _giai_ma_fourcc(float(_ma_hoa_fourcc("YUYV"))) == "YUYV"


# --- Nhóm E — dò thông số thực tế và cảnh báo ------------------------------


def test_fourcc_dong38_webcam_tuan_thu_khop_true(monkeypatch):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["khop"] is True


def test_fourcc_dong39_webcam_tuan_thu_khong_canh_bao(monkeypatch):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == []


def test_fourcc_dong40_webcam_tuan_thu_khong_log_tu_choi(monkeypatch, caplog):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    with caplog.at_level(logging.WARNING):
        cam.mo()
    assert (
        sum(
            1
            for r in caplog.records
            if "Camera từ chối" in r.getMessage() and r.levelno == logging.WARNING
        )
        == 0
    )


def test_fourcc_dong41_fourcc_thuc_te_mjpg(monkeypatch):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["fourcc_thuc_te"] == "MJPG"


def test_fourcc_dong42_fps_thuc_te_30(monkeypatch):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=30, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["fps_thuc_te"] == 30.0


def test_fourcc_dong43_do_phan_giai_thuc_te(monkeypatch):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["do_phan_giai_thuc_te"] == (1280, 720)


def test_fourcc_dong44_tu_choi_fourcc_canh_bao(monkeypatch):
    _gan(monkeypatch, tu_choi=("FOURCC",), fourcc_ban_dau="YUYV")
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == ["fourcc"]


def test_fourcc_dong45_tu_choi_fourcc_khop_false(monkeypatch):
    _gan(monkeypatch, tu_choi=("FOURCC",), fourcc_ban_dau="YUYV")
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["khop"] is False


def test_fourcc_dong46_tu_choi_fourcc_thuc_te_yuyv(monkeypatch):
    _gan(monkeypatch, tu_choi=("FOURCC",), fourcc_ban_dau="YUYV")
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["fourcc_thuc_te"] == "YUYV"


def test_fourcc_dong47_tu_choi_fourcc_dung_mot_log(monkeypatch, caplog):
    _gan(monkeypatch, tu_choi=("FOURCC",), fourcc_ban_dau="YUYV")
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    with caplog.at_level(logging.WARNING):
        cam.mo()
    assert (
        sum(
            1
            for r in caplog.records
            if "Camera từ chối" in r.getMessage() and r.levelno == logging.WARNING
        )
        == 1
    )


def test_fourcc_dong48_log_neu_ro_gia_tri_yeu_cau(monkeypatch, caplog):
    _gan(monkeypatch, tu_choi=("FOURCC",), fourcc_ban_dau="YUYV")
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    with caplog.at_level(logging.WARNING):
        cam.mo()
    ban_ghi = [
        r
        for r in caplog.records
        if "Camera từ chối" in r.getMessage() and r.levelno == logging.WARNING
    ]
    assert "MJPG" in ban_ghi[0].getMessage()


def test_fourcc_dong49_log_neu_ro_gia_tri_thuc_te(monkeypatch, caplog):
    _gan(monkeypatch, tu_choi=("FOURCC",), fourcc_ban_dau="YUYV")
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    with caplog.at_level(logging.WARNING):
        cam.mo()
    ban_ghi = [
        r
        for r in caplog.records
        if "Camera từ chối" in r.getMessage() and r.levelno == logging.WARNING
    ]
    assert "YUYV" in ban_ghi[0].getMessage()


def test_fourcc_dong50_tu_choi_fps_canh_bao(monkeypatch):
    _gan(monkeypatch, tu_choi=("FPS",), fps_ban_dau=10.0)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=30, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == ["fps"]


def test_fourcc_dong51_tu_choi_fps_thuc_te_giu_nguyen(monkeypatch):
    _gan(monkeypatch, tu_choi=("FPS",), fps_ban_dau=10.0)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=30, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["fps_thuc_te"] == 10.0


def test_fourcc_dong52_fps_lech_trong_dung_sai_khong_canh_bao(monkeypatch):
    _gan(monkeypatch, tu_choi=("FPS",), fps_ban_dau=29.97)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=30, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == []


def test_fourcc_dong53_tu_choi_kich_thuoc_do_phan_giai_thuc_te(monkeypatch):
    _gan(
        monkeypatch,
        tu_choi=("FRAME_WIDTH", "FRAME_HEIGHT"),
        kich_thuoc_ban_dau=(640, 480),
    )
    cam = CameraOpenCV(_cfg(fourcc="MJPG", width=1280, height=720, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["do_phan_giai_thuc_te"] == (640, 480)


def test_fourcc_dong54_tu_choi_kich_thuoc_canh_bao(monkeypatch):
    _gan(
        monkeypatch,
        tu_choi=("FRAME_WIDTH", "FRAME_HEIGHT"),
        kich_thuoc_ban_dau=(640, 480),
    )
    cam = CameraOpenCV(_cfg(fourcc="MJPG", width=1280, height=720, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == ["do_phan_giai"]


def test_fourcc_dong55_driver_noi_khac_khung_ve_khac(monkeypatch):
    _gan(monkeypatch, kich_thuoc_khung=(640, 480))
    cam = CameraOpenCV(_cfg(fourcc="MJPG", warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["do_phan_giai_thuc_te"] == (640, 480)


def test_fourcc_dong56_driver_noi_khac_sinh_canh_bao(monkeypatch):
    _gan(monkeypatch, kich_thuoc_khung=(640, 480))
    cam = CameraOpenCV(_cfg(fourcc="MJPG", warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == ["do_phan_giai"]


def test_fourcc_dong57_khong_doc_duoc_khung_do_phan_giai_none(monkeypatch):
    _gan(monkeypatch, doc_duoc=False)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["do_phan_giai_thuc_te"] is None


def test_fourcc_dong58_khong_doc_duoc_khung_canh_bao_rieng(monkeypatch):
    _gan(monkeypatch, doc_duoc=False)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == ["khong_lay_duoc_khung"]


def test_fourcc_dong59_khong_doc_duoc_khung_van_mo(monkeypatch):
    _gan(monkeypatch, doc_duoc=False)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", warmup_frames=0))
    cam.mo()
    assert cam.dang_mo is True


def test_fourcc_dong60_khong_doc_duoc_khung_co_log(monkeypatch, caplog):
    _gan(monkeypatch, doc_duoc=False)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", warmup_frames=0))
    with caplog.at_level(logging.WARNING):
        cam.mo()
    assert any(
        "Không lấy được khung thử" in r.getMessage() and r.levelno == logging.WARNING
        for r in caplog.records
    )


def test_fourcc_dong61_moi_thu_lech_thu_tu_canh_bao(monkeypatch):
    _gan(
        monkeypatch,
        tu_choi=("FOURCC", "FRAME_WIDTH", "FRAME_HEIGHT", "FPS"),
        fourcc_ban_dau="YUYV",
        fps_ban_dau=10.0,
        kich_thuoc_ban_dau=(640, 480),
    )
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=30, width=1280, height=720, warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == ["fourcc", "do_phan_giai", "fps"]


def test_fourcc_dong62_thieu_fps_khong_so_khong_canh_bao(monkeypatch):
    _gan(monkeypatch, fps_ban_dau=10.0)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", warmup_frames=0))
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == []


# --- Nhóm F — vòng đời và hình dạng dict -----------------------------------


def test_fourcc_dong63_truoc_mo_khop_none():
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25))
    assert cam.thong_so_thuc_te["khop"] is None


def test_fourcc_dong64_truoc_mo_fourcc_thuc_te_none():
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25))
    assert cam.thong_so_thuc_te["fourcc_thuc_te"] is None


def test_fourcc_dong65_truoc_mo_do_phan_giai_thuc_te_none():
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25))
    assert cam.thong_so_thuc_te["do_phan_giai_thuc_te"] is None


def test_fourcc_dong66_truoc_mo_canh_bao_rong():
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25))
    assert cam.thong_so_thuc_te["canh_bao"] == []


def test_fourcc_dong67_giu_nguyen_sau_khi_dong(monkeypatch):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    cam.dong()
    assert cam.thong_so_thuc_te["fourcc_thuc_te"] == "MJPG"


def test_fourcc_dong68_mo_lai_do_lai_ghi_de(monkeypatch):
    cam_a = VideoCaptureGia(0, tu_choi=("FOURCC",), fourcc_ban_dau="YUYV")
    cam_b = VideoCaptureGia(0)
    _gan_chuoi(monkeypatch, cam_a, cam_b)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    cam.dong()
    cam.mo()
    assert cam.thong_so_thuc_te["canh_bao"] == []


def test_fourcc_dong69_dung_tam_khoa(monkeypatch):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert set(cam.thong_so_thuc_te) == {
        "fourcc_yeu_cau",
        "fourcc_thuc_te",
        "fps_yeu_cau",
        "fps_thuc_te",
        "do_phan_giai_yeu_cau",
        "do_phan_giai_thuc_te",
        "canh_bao",
        "khop",
    }


def test_fourcc_dong70_tra_ban_sao_canh_bao(monkeypatch):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    cam.thong_so_thuc_te["canh_bao"].append("bay")
    assert cam.thong_so_thuc_te["canh_bao"] == []


def test_fourcc_dong71_dung_mot_lan_doc_thu(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0)).mo()
    assert cam_gia.so_lan_read == 1


def test_fourcc_dong72_warmup_hai_cong_doc_thu(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=2)).mo()
    assert cam_gia.so_lan_read == 3


def test_fourcc_dong73_log_info_co_fourcc(monkeypatch, caplog):
    _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    with caplog.at_level(logging.INFO):
        cam.mo()
    assert any("MJPG" in r.getMessage() for r in caplog.records if r.levelno == logging.INFO)


# --- Nhóm G — không hồi quy ------------------------------------------------


def test_fourcc_dong74_doc_frame_dung_shape(monkeypatch):
    _gan(monkeypatch, kich_thuoc_khung=(64, 48))
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert cam.doc_frame().shape == (48, 64, 3)


def test_fourcc_dong75_doc_frame_dung_dtype(monkeypatch):
    _gan(monkeypatch, kich_thuoc_khung=(64, 48))
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    assert cam.doc_frame().dtype == np.uint8


def test_fourcc_dong76_mo_that_bai_raise(monkeypatch):
    _gan(monkeypatch, mo_duoc=False)
    cam = CameraOpenCV(_cfg(fourcc="MJPG"))
    with pytest.raises(LoiCamera):
        cam.mo()


def test_fourcc_dong77_mo_that_bai_khong_set_gi(monkeypatch):
    cam_gia = _gan(monkeypatch, mo_duoc=False)
    cam = CameraOpenCV(_cfg(fourcc="MJPG"))
    with pytest.raises(LoiCamera):
        cam.mo()
    assert cam_gia.thu_tu_set == []


def test_fourcc_dong78_mock_khong_bi_them_thong_so():
    cam_mock = CameraGiaLap({"width": 10, "height": 10})
    assert not hasattr(cam_mock, "thong_so_thuc_te")


def test_fourcc_dong79_ke_thua_bo_thu_hinh():
    from src.capture.base import BoThuHinh

    assert issubclass(CameraOpenCV, BoThuHinh)


def test_fourcc_dong80_chi_so_thiet_bi(monkeypatch):
    cam_gia = _gan(monkeypatch)
    CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0, device_index=0)).mo()
    assert cam_gia.chi_so == 0


def test_fourcc_dong81_dong_goi_release(monkeypatch):
    cam_gia = _gan(monkeypatch)
    cam = CameraOpenCV(_cfg(fourcc="MJPG", fps=25, warmup_frames=0))
    cam.mo()
    cam.dong()
    assert cam_gia.da_release is True
