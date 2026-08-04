"""Bộ kiểm thử cho module nền tảng src/common."""

import logging
import sys
from pathlib import Path

import numpy as np
import pytest

from src.common.config import lay_gia_tri, nap_cau_hinh
from src.common.exceptions import (
    LoiCamera,
    LoiCauHinh,
    LoiHeThong,
    LoiMoHinh,
    LoiPhanCung,
)
from src.common.logging import lay_logger, thiet_lap_log
from src.common.types import Command, FaceBox, Identity


# -----------------------------------------------------------------------------
# Test exceptions.py
# -----------------------------------------------------------------------------
def test_exceptions_inheritance() -> None:
    """Kiểm tra quan hệ kế thừa của các ngoại lệ tuỳ chỉnh."""
    assert issubclass(LoiCauHinh, LoiHeThong)
    assert issubclass(LoiCamera, LoiHeThong)
    assert issubclass(LoiPhanCung, LoiHeThong)
    assert issubclass(LoiMoHinh, LoiHeThong)
    assert issubclass(LoiHeThong, Exception)


# -----------------------------------------------------------------------------
# Test types.py
# -----------------------------------------------------------------------------
def test_facebox_properties() -> None:
    """Kiểm tra các thuộc tính chieu_rong, chieu_cao, dien_tich của FaceBox."""
    box = FaceBox(x1=10, y1=20, x2=110, y2=170, confidence=0.95)
    assert box.chieu_rong == 100
    assert box.chieu_cao == 150
    assert box.dien_tich == 15000


def test_facebox_landmarks_comparison() -> None:
    """Kiểm tra FaceBox với landmarks không gây lỗi ValueError khi so sánh equal."""
    landmarks1 = np.array([[10, 12], [20, 22]])
    landmarks2 = np.array([[10, 12], [20, 22]])

    box1 = FaceBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9, landmarks=landmarks1)
    box2 = FaceBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9, landmarks=landmarks2)

    # Do landmarks khai báo compare=False nên 2 dataclass frozen so sánh không bị ném ValueError
    assert box1 == box2


def test_identity_properties() -> None:
    """Kiểm tra thuộc tính la_nguoi_la của Identity."""
    id_nguoi_la = Identity(user_id=None, similarity=0.2, is_live=True, backend="arcface")
    assert id_nguoi_la.la_nguoi_la is True

    id_nguoi_quen = Identity(user_id="user_123", similarity=0.85, is_live=True, backend="arcface")
    assert id_nguoi_quen.la_nguoi_la is False


def test_command_fields() -> None:
    """Kiểm tra khởi tạo đối tượng Command."""
    cmd = Command(
        thiet_bi="den_phong_khach", hanh_dong="bat", nguon="user_123", thoi_diem=1700000000.0
    )
    assert cmd.thiet_bi == "den_phong_khach"
    assert cmd.hanh_dong == "bat"
    assert cmd.nguon == "user_123"
    assert cmd.thoi_diem == 1700000000.0


# -----------------------------------------------------------------------------
# Test config.py - nap_cau_hinh
# -----------------------------------------------------------------------------
def test_nap_cau_hinh_valid_yaml(tmp_path: Path) -> None:
    """Nạp file YAML hợp lệ trả về dict tương ứng."""
    file_yaml = tmp_path / "test.yaml"
    file_yaml.write_text("backend: arcface\nthreshold: 0.42\n", encoding="utf-8")

    cfg = nap_cau_hinh(file_yaml)
    assert cfg == {"backend": "arcface", "threshold": 0.42}


def test_nap_cau_hinh_file_not_found() -> None:
    """File không tồn tại ném ngoại lệ LoiCauHinh."""
    with pytest.raises(LoiCauHinh) as exc_info:
        nap_cau_hinh("duong_dan_khong_ton_tai_12345.yaml")
    assert "không tồn tại" in str(exc_info.value)


def test_nap_cau_hinh_invalid_yaml_syntax(tmp_path: Path) -> None:
    """File YAML sai cú pháp ném ngoại lệ LoiCauHinh bọc YAMLError."""
    file_yaml = tmp_path / "invalid.yaml"
    file_yaml.write_text("key: [unclosed_list\n  another_item", encoding="utf-8")

    with pytest.raises(LoiCauHinh) as exc_info:
        nap_cau_hinh(file_yaml)
    assert "Lỗi cú pháp YAML" in str(exc_info.value)


def test_nap_cau_hinh_empty_file(tmp_path: Path) -> None:
    """File rỗng trả về dict rỗng {}."""
    file_yaml = tmp_path / "empty.yaml"
    file_yaml.write_text("", encoding="utf-8")

    cfg = nap_cau_hinh(file_yaml)
    assert cfg == {}


def test_nap_cau_hinh_non_mapping_content(tmp_path: Path) -> None:
    """Nội dung YAML là list/scalar (không phải mapping) ném LoiCauHinh."""
    file_yaml = tmp_path / "list.yaml"
    file_yaml.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(LoiCauHinh) as exc_info:
        nap_cau_hinh(file_yaml)
    assert "mapping" in str(exc_info.value)


def test_nap_cau_hinh_env_var_expansion(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Thay thế biến môi trường dạng ${TEN_BIEN} khi có tồn tại trong os.environ."""
    monkeypatch.setenv("MY_TEST_TOKEN", "secret123")
    file_yaml = tmp_path / "env.yaml"
    file_yaml.write_text("token: ${MY_TEST_TOKEN}\n", encoding="utf-8")

    cfg = nap_cau_hinh(file_yaml)
    assert cfg["token"] == "secret123"


def test_nap_cau_hinh_missing_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Biến môi trường không tồn tại ném LoiCauHinh nêu đúng tên biến thiếu."""
    monkeypatch.delenv("MISSING_VAR_NAME", raising=False)
    file_yaml = tmp_path / "missing_env.yaml"
    file_yaml.write_text("var: ${MISSING_VAR_NAME}\n", encoding="utf-8")

    with pytest.raises(LoiCauHinh) as exc_info:
        nap_cau_hinh(file_yaml)
    assert "MISSING_VAR_NAME" in str(exc_info.value)


def test_nap_cau_hinh_nested_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Mở rộng biến môi trường đệ quy trong list và dict lồng nhau."""
    monkeypatch.setenv("HOST_NAME", "localhost")
    monkeypatch.setenv("PORT_NUM", "8080")

    file_yaml = tmp_path / "nested.yaml"
    file_yaml.write_text(
        "server:\n"
        "  host: ${HOST_NAME}\n"
        "  endpoints:\n"
        "    - http://${HOST_NAME}:${PORT_NUM}/v1\n",
        encoding="utf-8",
    )

    cfg = nap_cau_hinh(file_yaml)
    assert cfg["server"]["host"] == "localhost"
    assert cfg["server"]["endpoints"] == ["http://localhost:8080/v1"]


def test_nap_cau_hinh_dollar_without_braces(tmp_path: Path) -> None:
    """Chuỗi chứa $ không đúng dạng ${...} được giữ nguyên."""
    file_yaml = tmp_path / "dollar.yaml"
    file_yaml.write_text("price: $100\nvar: $FOO\n", encoding="utf-8")

    cfg = nap_cau_hinh(file_yaml)
    assert cfg["price"] == "$100"
    assert cfg["var"] == "$FOO"


def test_nap_cau_hinh_vietnamese_utf8(tmp_path: Path) -> None:
    """File chứa tiếng Việt có dấu nạp đúng nội dung UTF-8."""
    file_yaml = tmp_path / "utf8.yaml"
    file_yaml.write_text("ten: Nguyễn Văn A\nmota: Nhận diện khuôn mặt\n", encoding="utf-8")

    cfg = nap_cau_hinh(file_yaml)
    assert cfg["ten"] == "Nguyễn Văn A"
    assert cfg["mota"] == "Nhận diện khuôn mặt"


# -----------------------------------------------------------------------------
# Test config.py - lay_gia_tri
# -----------------------------------------------------------------------------
def test_lay_gia_tri_success() -> None:
    """Lấy giá trị lồng nhau theo path 'a.b'."""
    cfg = {"a": {"b": 42}}
    assert lay_gia_tri(cfg, "a.b") == 42


def test_lay_gia_tri_missing_key_with_default() -> None:
    """Key không tồn tại trả về mac_dinh khi được truyền."""
    cfg = {"a": {"b": 1}}
    assert lay_gia_tri(cfg, "a.c", mac_dinh=100) == 100


def test_lay_gia_tri_missing_key_without_default() -> None:
    """Key không tồn tại và không truyền mac_dinh ném LoiCauHinh."""
    cfg = {"a": {"b": 1}}
    with pytest.raises(LoiCauHinh) as exc_info:
        lay_gia_tri(cfg, "a.c")
    assert "a.c" in str(exc_info.value)


def test_lay_gia_tri_non_dict_step() -> None:
    """Đi xuyên qua giá trị không phải dict ném LoiCauHinh."""
    cfg = {"a": {"b": 10}}
    with pytest.raises(LoiCauHinh) as exc_info:
        lay_gia_tri(cfg, "a.b.c")
    assert "a.b.c" in str(exc_info.value)


def test_lay_gia_tri_none_value_with_default() -> None:
    """Giá trị hợp lệ là None có truyền mac_dinh vẫn trả về None."""
    cfg = {"a": {"b": None}}
    assert lay_gia_tri(cfg, "a.b", mac_dinh=999) is None


# -----------------------------------------------------------------------------
# Test logging.py
# -----------------------------------------------------------------------------
def test_thiet_lap_log_default() -> None:
    """Thiết lập log mặc định: đúng 1 handler ra stdout/stderr, mức INFO."""
    thiet_lap_log(muc="INFO")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 1
    handler = root_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream in (sys.stdout, sys.stderr)


def test_thiet_lap_log_debug_level() -> None:
    """Thiết lập log mức DEBUG."""
    thiet_lap_log(muc="DEBUG")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG


def test_thiet_lap_log_invalid_level() -> None:
    """Mức log không hợp lệ ném LoiCauHinh."""
    with pytest.raises(LoiCauHinh) as exc_info:
        thiet_lap_log(muc="INVALID_LEVEL")
    assert "INVALID_LEVEL" in str(exc_info.value)


def test_thiet_lap_log_file_handler(tmp_path: Path) -> None:
    """Thiết lập log với file_log lưu được log ra file."""
    log_file = tmp_path / "sub_dir" / "app.log"
    thiet_lap_log(muc="INFO", file_log=log_file)

    logger = lay_logger("test_module")
    logger.info("Thông điệp kiểm tra ghi file")

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Thông điệp kiểm tra ghi file" in content

    from logging.handlers import RotatingFileHandler

    from src.common.logging import KICH_THUOC_TOI_DA_FILE_LOG, SO_FILE_LOG_XOAY_VONG

    fh = [h for h in logging.getLogger().handlers if isinstance(h, RotatingFileHandler)]
    assert len(fh) == 1
    assert fh[0].maxBytes == KICH_THUOC_TOI_DA_FILE_LOG
    assert fh[0].backupCount == SO_FILE_LOG_XOAY_VONG


def test_thiet_lap_log_no_handler_duplication() -> None:
    """Gọi thiet_lap_log hai lần liên tiếp không bị nhân đôi handler."""
    thiet_lap_log(muc="INFO")
    count1 = len(logging.getLogger().handlers)

    thiet_lap_log(muc="INFO")
    count2 = len(logging.getLogger().handlers)

    assert count1 == count2 == 1


def test_lay_logger() -> None:
    """lay_logger trả về đối tượng Logger và cùng instance khi gọi cùng tên."""
    logger1 = lay_logger("module_test")
    logger2 = lay_logger("module_test")

    assert isinstance(logger1, logging.Logger)
    assert logger1 is logger2
