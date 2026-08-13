"""Kiểm thử cho khối thu hình."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from src.capture.factory import tao_bo_thu_hinh
from src.capture.mock_camera import CameraGiaLap
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
