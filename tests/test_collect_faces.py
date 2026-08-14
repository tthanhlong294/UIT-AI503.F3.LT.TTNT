"""Kiểm thử cho script thu thập ảnh khuôn mặt."""

import time
from unittest.mock import patch

import cv2
import pytest

from scripts.collect_faces import (
    dem_da_co,
    ghi_manifest,
    main,
    phan_tich_ten_file,
    tao_ten_file,
    thu_thap,
    to_hop_con_thieu,
)
from src.common.exceptions import LoiCamera


@pytest.fixture
def cfg_data():
    return {
        "poses": ["frontal", "left", "right", "up", "down"],
        "lights": ["bright", "dim"],
        "min_per_combo": 2,
        "min_per_user": 20,
        "id_pattern": "^[ux][0-9]{2}$",
        "out_dir_gallery": "data/raw",
        "out_dir_indomain": "data/impostor/indomain",
        "manifest_name": "manifest.csv",
        "image_format": "png",
        "capture_interval_s": 0.0,
        "pose_switch_delay_s": 0.0,
    }


@pytest.fixture
def cfg_capture():
    return {
        "backend": "mock",
        "mock": {
            "width": 16,
            "height": 16,
            "seed": 42,
            "source": "synthetic",
            "loop": True,
            "max_frames": 0,
        },
    }


def test_01_tao_ten_file_dem_3_chu_so():
    """Tạo tên file với đệm 3 chữ số."""
    assert tao_ten_file("u01", "frontal", "bright", 7, "png") == "u01_frontal_bright_007.png"


def test_02_tao_ten_file_idx_lon():
    """Tạo tên file với chỉ số lớn không bị cắt."""
    ten = tao_ten_file("u01", "frontal", "bright", 1000, "png")
    assert "1000" in ten


def test_03_phan_tich_ten_file_nghich_dao():
    """Phân tích tên file là hàm nghịch đảo của tạo tên file."""
    ten = tao_ten_file("u01", "left", "dim", 12, "png")
    assert phan_tich_ten_file(ten) == ("u01", "left", "dim", 12)


def test_04_phan_tich_ten_file_sai():
    """Tên file sai quy ước ném ValueError."""
    with pytest.raises(ValueError):
        phan_tich_ten_file("anh_bat_ky.png")


def test_05_dem_da_co_thu_muc_khong_ton_tai(tmp_path):
    """Đếm thư mục không tồn tại trả về dict rỗng."""
    dir_fake = tmp_path / "non_existent"
    assert dem_da_co(dir_fake, "u01") == {}


def test_06_dem_da_co_dung_to_hop(tmp_path):
    """Đếm đúng số lượng theo từng tổ hợp tư thế và mức sáng."""
    (tmp_path / "u01_frontal_bright_001.png").touch()
    (tmp_path / "u01_frontal_bright_002.png").touch()
    (tmp_path / "u01_frontal_bright_003.png").touch()
    (tmp_path / "u01_left_dim_001.png").touch()
    (tmp_path / "u01_left_dim_002.png").touch()

    da_co = dem_da_co(tmp_path, "u01")
    assert da_co[("frontal", "bright")] == 3 and da_co[("left", "dim")] == 2


def test_07_dem_da_co_bo_qua_file_la(tmp_path):
    """Đếm bỏ qua các file lạ không đúng quy ước."""
    (tmp_path / "u01_frontal_bright_001.png").touch()
    (tmp_path / "u01_frontal_bright_002.png").touch()
    (tmp_path / "u01_frontal_bright_003.png").touch()
    (tmp_path / "ghi_chu.txt").touch()
    (tmp_path / "IMG_1234.png").touch()

    da_co = dem_da_co(tmp_path, "u01")
    assert da_co[("frontal", "bright")] == 3


def test_08_dem_da_co_chi_dem_dung_ma(tmp_path):
    """Đếm chỉ đếm ảnh của đúng mã người dùng yêu cầu."""
    (tmp_path / "u01_frontal_bright_001.png").touch()
    (tmp_path / "u02_frontal_bright_001.png").touch()

    da_co = dem_da_co(tmp_path, "u01")
    assert da_co.get(("frontal", "bright"), 0) == 1


def test_09_to_hop_con_thieu_khi_da_du():
    """Tổ hợp còn thiếu trả về rỗng khi đã đủ chỉ tiêu."""
    da_co = {("frontal", "bright"): 10, ("left", "bright"): 10}
    assert to_hop_con_thieu(da_co, ["frontal", "left"], ["bright"], 10) == []


def test_10_to_hop_con_thieu_khi_thieu():
    """Tổ hợp còn thiếu tính đúng số ảnh cần chụp thêm."""
    da_co = {("up", "dim"): 3}
    res = to_hop_con_thieu(da_co, ["up"], ["dim"], 10)
    assert ("up", "dim", 7) in res


def test_11_danh_so_tiep_tuc(tmp_path, cfg_data, cfg_capture):
    """Đánh số chỉ số tiếp tục từ ảnh có sẵn."""
    (tmp_path / "u01_frontal_bright_007.png").touch()
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 2
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert (tmp_path / "u01_frontal_bright_008.png").exists()


def test_12_khong_ghi_de_anh_da_co(tmp_path, cfg_data, cfg_capture):
    """Tuyệt đối không ghi đè dữ liệu ảnh đã có."""
    old_file = tmp_path / "u01_frontal_bright_001.png"
    old_file.write_bytes(b"OLD_DATA")
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 3
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert old_file.read_bytes() == b"OLD_DATA"
    assert (tmp_path / "u01_frontal_bright_002.png").exists()
    assert (tmp_path / "u01_frontal_bright_003.png").exists()


def test_12a_camera_ghi_backend_da_phan_giai(tmp_path, cfg_data, cfg_capture):
    """Cột camera ghi backend đã phân giải, không bao giờ ghi auto."""
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 1
    cfg_capture_auto = {
        "backend": "auto",
        "mock": cfg_capture["mock"],
        "opencv": {"device_index": 99},
    }
    ban_ghi = thu_thap(cfg_data, cfg_capture_auto, "u01", "bright", tmp_path, hien_thi=False)
    assert ban_ghi[0]["camera"] == "CameraGiaLap"
    assert "auto" not in [r["camera"] for r in ban_ghi]


def test_12b_width_height_lay_tu_khung_hinh_that(tmp_path, cfg_data, cfg_capture):
    """width và height lấy từ khung hình thật."""
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 1
    cfg_capture["mock"]["width"] = 640
    cfg_capture["mock"]["height"] = 480
    ban_ghi = thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert ban_ghi[0]["width"] == 640
    assert ban_ghi[0]["height"] == 480


def test_12c_loi_camera_giua_chung_ghi_manifest(tmp_path, cfg_data, cfg_capture):
    """Lỗi camera giữa chừng vẫn ghi manifest cho phần đã chụp."""
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 4

    count = 0
    from src.capture.mock_camera import CameraGiaLap

    doc_frame_goc = CameraGiaLap.doc_frame

    def doc_frame_faulty(self_cam):
        nonlocal count
        count += 1
        if count == 3:
            raise LoiCamera("Camera hỏng giữa chừng")
        return doc_frame_goc(self_cam)

    with patch.object(CameraGiaLap, "doc_frame", doc_frame_faulty), pytest.raises(LoiCamera):
        thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)

    m_file = tmp_path / "manifest.csv"
    lines = [line for line in m_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    so_dong_du_lieu = len(lines) - 1
    so_file_anh = len(list(tmp_path.glob("*.png")))
    assert so_file_anh == 2
    assert so_dong_du_lieu == 2


def test_12d_hien_thi_false_khong_tat_nhip_cho(tmp_path, cfg_data, cfg_capture):
    """hien_thi=False không được tắt nhịp chờ."""
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 2
    cfg_data["capture_interval_s"] = 0.2
    cfg_data["pose_switch_delay_s"] = 0.2
    t0 = time.monotonic()
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    elapsed = time.monotonic() - t0
    assert elapsed >= 0.5


def test_12e_hien_thi_false_khong_tat_huong_dan_tu_the(tmp_path, cfg_data, cfg_capture, capsys):
    """hien_thi=False vẫn in hướng dẫn tư thế."""
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 1
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    out = capsys.readouterr().out
    assert "frontal" in out


def test_13_thu_thap_tao_dung_so_anh(tmp_path, cfg_data, cfg_capture):
    """Thu thập tạo ra đúng số lượng ảnh mong đợi."""
    cfg_data["poses"] = ["frontal", "left"]
    cfg_data["min_per_combo"] = 2
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert len(list(tmp_path.glob("*.png"))) == 4


def test_14_anh_ghi_ra_la_png_doc_duoc(tmp_path, cfg_data, cfg_capture):
    """Ảnh ghi ra đĩa là file PNG hợp lệ đọc được bởi OpenCV."""
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 1
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    p = tmp_path / "u01_frontal_bright_001.png"
    img = cv2.imread(str(p))
    assert img is not None and img.shape == (16, 16, 3)


def test_15_thu_thap_tra_ve_ban_ghi_manifest(tmp_path, cfg_data, cfg_capture):
    """Hàm thu thập trả về danh sách bản ghi manifest tương ứng."""
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 3
    ban_ghi = thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert len(ban_ghi) == 3


def test_16_ghi_manifest_lan_dau(tmp_path):
    """Ghi manifest lần đầu tạo dòng tiêu đề header."""
    m_file = tmp_path / "manifest.csv"
    ghi_manifest(
        m_file,
        [
            {
                "file": "u01_001.png",
                "id": "u01",
                "pose": "frontal",
                "light": "bright",
                "idx": 1,
                "timestamp": "2026-08-13T00:00:00",
                "camera": "mock",
                "width": 16,
                "height": 16,
                "note": "",
            }
        ],
    )
    lines = m_file.read_text(encoding="utf-8").splitlines()
    assert "file,id,pose,light,idx,timestamp" in lines[0]


def test_17_ghi_manifest_lan_hai_ghi_noi(tmp_path):
    """Ghi manifest lần hai ghi nối, không làm lặp lại header."""
    m_file = tmp_path / "manifest.csv"
    rec1 = [
        {
            "file": "f1",
            "id": "u01",
            "pose": "p",
            "light": "l",
            "idx": 1,
            "timestamp": "t",
            "camera": "c",
            "width": 1,
            "height": 1,
            "note": "",
        },
        {
            "file": "f2",
            "id": "u01",
            "pose": "p",
            "light": "l",
            "idx": 2,
            "timestamp": "t",
            "camera": "c",
            "width": 1,
            "height": 1,
            "note": "",
        },
    ]
    rec2 = [
        {
            "file": "f3",
            "id": "u01",
            "pose": "p",
            "light": "l",
            "idx": 3,
            "timestamp": "t",
            "camera": "c",
            "width": 1,
            "height": 1,
            "note": "",
        },
        {
            "file": "f4",
            "id": "u01",
            "pose": "p",
            "light": "l",
            "idx": 4,
            "timestamp": "t",
            "camera": "c",
            "width": 1,
            "height": 1,
            "note": "",
        },
    ]
    ghi_manifest(m_file, rec1)
    ghi_manifest(m_file, rec2)
    lines = m_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5  # 1 dòng tiêu đề + 4 dòng dữ liệu


def test_18_so_dong_manifest_khop_so_anh(tmp_path, cfg_data, cfg_capture):
    """Số dòng trong manifest khớp đúng số lượng ảnh trên đĩa."""
    cfg_data["poses"] = ["frontal", "left"]
    cfg_data["min_per_combo"] = 2
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    m_file = tmp_path / "manifest.csv"
    lines = [line for line in m_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    so_dong_du_lieu = len(lines) - 1
    assert so_dong_du_lieu == len(list(tmp_path.glob("*.png")))


def test_19_dry_run_khong_ghi_file(tmp_path, cfg_data, cfg_capture):
    """dry_run=True không làm thay đổi nội dung file trên đĩa."""
    truoc = list(tmp_path.rglob("*"))
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False, dry_run=True)
    sau = list(tmp_path.rglob("*"))
    assert truoc == sau


def test_20_dry_run_tra_ve_khong_loi(tmp_path, cfg_data, cfg_capture):
    """dry_run=True trả về danh sách rỗng không ném ngoại lệ."""
    res = thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False, dry_run=True)
    assert res == []


def test_21_thu_muc_ra_chua_ton_tai(tmp_path, cfg_data, cfg_capture):
    """Thư mục ra chưa tồn tại sẽ tự động tạo mới."""
    out_dir = tmp_path / "sub" / "u01"
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 1
    thu_thap(cfg_data, cfg_capture, "u01", "bright", out_dir, hien_thi=False)
    assert out_dir.exists()


@pytest.mark.parametrize("ma_sai", ["abc", "u1", "y01"])
def test_22_main_id_sai_mau(ma_sai):
    """main() trả về 1 khi truyền mã --id không hợp lệ."""
    with patch("sys.argv", ["collect_faces.py", "--id", ma_sai, "--light", "bright"]):
        assert main() == 1


def test_23_main_light_sai():
    """main() trả về 1 khi truyền --light không hợp lệ."""
    with patch("sys.argv", ["collect_faces.py", "--id", "u01", "--light", "dark"]):
        assert main() == 1


def test_24_main_thanh_cong():
    """main() trả về 0 khi tham số hợp lệ."""
    with patch(
        "sys.argv",
        ["collect_faces.py", "--id", "u01", "--light", "bright", "--dry-run", "--no-preview"],
    ):
        assert main() == 0


def test_25a_hien_thi_false_khong_goi_ham_hien_thi(tmp_path, cfg_data, cfg_capture, monkeypatch):
    """hien_thi=False không gọi bất kỳ hàm hiển thị cửa sổ nào của cv2."""

    def throw_err(*args, **kwargs):
        raise AssertionError("Không được gọi hàm hiển thị khi hien_thi=False")

    for ten_ham in ("imshow", "waitKey", "namedWindow", "destroyAllWindows"):
        monkeypatch.setattr(cv2, ten_ham, throw_err)

    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 2
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)


def test_25b_hien_thi_false_chay_het_than_ham(tmp_path, cfg_data, cfg_capture, monkeypatch):
    """hien_thi=False chạy hết thân hàm, tạo đủ số ảnh mong đợi."""

    def throw_err(*args, **kwargs):
        raise AssertionError("Không được gọi hàm hiển thị khi hien_thi=False")

    for ten_ham in ("imshow", "waitKey", "namedWindow", "destroyAllWindows"):
        monkeypatch.setattr(cv2, ten_ham, throw_err)

    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 2
    ban_ghi = thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert len(ban_ghi) == 2
    assert (tmp_path / "u01_frontal_bright_001.png").exists()
    assert (tmp_path / "u01_frontal_bright_002.png").exists()


def test_25c_hien_thi_false_guard_don_dep_cuoi_ham(tmp_path, cfg_data, cfg_capture, monkeypatch):
    """hien_thi=False guard cả khối dọn dẹp destroyAllWindows ở cuối tư thế/hàm."""

    def throw_err(*args, **kwargs):
        raise AssertionError("Không được gọi hàm hiển thị khi hien_thi=False")

    monkeypatch.setattr(cv2, "destroyAllWindows", throw_err)

    cfg_data["poses"] = ["frontal", "left"]
    cfg_data["min_per_combo"] = 1
    ban_ghi = thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert len(ban_ghi) == 2
