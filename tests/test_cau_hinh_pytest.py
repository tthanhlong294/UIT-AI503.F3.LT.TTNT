"""Kiểm thử cấu hình pytest khai báo trong pyproject.toml (mã việc P0-04 §8.3, P0-05 §8 đặc tả).

Đọc `[tool.pytest.ini_options]` bằng `tomllib` của thư viện chuẩn (không cần gói ngoài
`requirements.txt`). Ca 47/48 gọi một tiến trình pytest CON trên một bộ ca kiểm thử tối giản
dựng trong `tmp_path`, để kiểm chứng `--strict-markers` thực sự chặn dấu sai chính tả mà
KHÔNG chặn nhầm dấu đúng; ca 53/54 làm điều tương ứng cho `--strict-config` bằng một tệp
`pyproject.toml` tạm tự chứa trong `tmp_path` — không ca nào ở đây chạm mạng hay cần `git`.
"""

import subprocess
import sys
from pathlib import Path

import tomllib

_GOC_KHO = Path(__file__).resolve().parents[1]


def _doc_cau_hinh_pytest() -> dict:
    """Đọc mục `[tool.pytest.ini_options]` từ `pyproject.toml` ở gốc kho.

    Returns:
        Dict nội dung của mục `[tool.pytest.ini_options]`.
    """
    with open(_GOC_KHO / "pyproject.toml", "rb") as f:
        toml = tomllib.load(f)
    return toml["tool"]["pytest"]["ini_options"]


def _chay_pytest_con(tep_test: Path, cau_hinh: Path | None = None) -> subprocess.CompletedProcess:
    """Chạy một tiến trình pytest con trên đúng một tệp test.

    Args:
        tep_test: Đường dẫn tệp test cần chạy.
        cau_hinh: Tệp cấu hình truyền qua `-c`. Mặc định `None` giữ nguyên hành vi cũ —
            dùng `pyproject.toml` của kho (đường dẫn tương đối, hợp với `cwd=_GOC_KHO`).

    Returns:
        Kết quả tiến trình con (mã thoát, stdout, stderr).
    """
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "pyproject.toml" if cau_hinh is None else str(cau_hinh),
            "-p",
            "no:cacheprovider",
            str(tep_test),
        ],
        cwd=_GOC_KHO,
        capture_output=True,
        text=True,
        check=False,
    )


def test_45_markers_khai_bao_slow():
    """Mục `markers` phải khai báo dấu tuỳ biến `slow` (§6 đặc tả P0-04)."""
    cfg = _doc_cau_hinh_pytest()
    assert any(m.startswith("slow:") for m in cfg["markers"])


def test_46_addopts_bat_strict_markers():
    """Mục `addopts` phải bật `--strict-markers` — dấu sai chính tả bị chặn ngay lượt đầu."""
    cfg = _doc_cau_hinh_pytest()
    assert "--strict-markers" in cfg["addopts"]


def test_47_dau_sai_chinh_ta_bi_chan(tmp_path):
    """Một dấu tuỳ biến sai chính tả (chưa khai báo) làm pytest con thoát khác 0, và thông báo
    lỗi nêu đúng tên dấu sai — không phải lỗi chung chung không xác định được.

    Ghép chuỗi `dau_sai` từ hai mảnh thay vì viết liền một chuỗi ký tự đầy đủ của dấu mô phỏng:
    tránh để phép quét bằng grep theo mẫu decorator pytest (§10 đặc tả P0-04) bắt nhầm dấu MÔ
    PHỎNG trong nội dung tệp .py con này thành một dấu tuỳ biến thật của chính kho — dấu này chỉ
    tồn tại trong tệp tạm sinh ra lúc chạy, không phải trong mã nguồn.
    """
    dau_sai = "slow" + "ww"
    tep_test = tmp_path / "test_mau_sai_dau.py"
    tep_test.write_text(
        f"import pytest\n\n\n@pytest.mark.{dau_sai}\ndef test_mau():\n    assert True\n",
        encoding="utf-8",
    )

    kq = _chay_pytest_con(tep_test)

    assert kq.returncode != 0
    assert dau_sai in kq.stdout


def test_48_dau_dung_van_chay_duoc(tmp_path):
    """Cùng bộ ca kiểm thử nhưng dùng dấu `slow` (đã khai báo ở `markers`): pytest con thoát 0.

    Dòng cặp đường thành công của ca 47: thiếu ca này, một cấu hình chặn MỌI dấu — kể cả dấu
    `slow` hợp lệ — vẫn qua được ca 47.
    """
    tep_test = tmp_path / "test_mau_dau_dung.py"
    tep_test.write_text(
        "import pytest\n\n\n@pytest.mark.slow\ndef test_mau():\n    assert True\n",
        encoding="utf-8",
    )

    kq = _chay_pytest_con(tep_test)

    assert kq.returncode == 0


# ---------- P0-05 §8: --strict-config ----------


def _viet_pyproject_tam(tmp_path: Path, khoa_duong_dan: str) -> Path:
    """Ghi một `pyproject.toml` tạm tự chứa trong `tmp_path` để chạy pytest con với `-c`.

    Nội dung tối giản: một mục `markers`, một mục `addopts` bật `--strict-config`, và đúng
    một khoá đường dẫn mang tên `khoa_duong_dan` — 'testpath' (sai) hoặc 'testpaths' (đúng).
    Đây là biến DUY NHẤT đổi giữa ca 53 và ca 54.
    """
    cfg = tmp_path / "pyproject.toml"
    cfg.write_text(
        "[tool.pytest.ini_options]\n"
        'markers = ["cham: vi du"]\n'
        'addopts = ["--strict-config"]\n'
        f'{khoa_duong_dan} = ["tests"]\n',
        encoding="utf-8",
    )
    return cfg


def _viet_tep_test_toi_gian(tmp_path: Path) -> Path:
    """Một tệp test tối giản, truyền tường minh trên dòng lệnh nên `testpath(s)` không ảnh
    hưởng việc thu thập."""
    tep_test = tmp_path / "test_toi_gian_strict_config.py"
    tep_test.write_text("def test_mau():\n    assert True\n", encoding="utf-8")
    return tep_test


def test_52_addopts_bat_strict_config():
    """Mục `addopts` của KHO thật sự có `--strict-config`.

    Thiếu ca này, ca 53/54 dùng cấu hình tạm nên vẫn xanh dù kho không bật cờ — không ai biết.
    """
    cfg = _doc_cau_hinh_pytest()
    assert "--strict-config" in cfg["addopts"]


def test_53_khoa_cau_hinh_sai_lam_pytest_con_dung_va_neu_dich_danh(tmp_path):
    """`--strict-config` cắn thật: một khoá sai chính tả (`testpath`) làm pytest con thoát
    khác 0 và thông báo nêu ĐÍCH DANH tên khoá sai, không phải lỗi chung chung."""
    cfg_sai = _viet_pyproject_tam(tmp_path, "testpath")
    tep_test = _viet_tep_test_toi_gian(tmp_path)

    kq = _chay_pytest_con(tep_test, cau_hinh=cfg_sai)

    assert kq.returncode != 0  # 53a
    assert "testpath" in kq.stdout + kq.stderr  # 53b


def test_54_khoa_cau_hinh_dung_thi_pytest_con_thoat_0(tmp_path):
    """Cặp đối chứng ca 53: CÙNG cách dựng cấu hình tạm, khoá viết đúng `testpaths` → thoát 0.

    Thiếu ca này, một cấu hình tạm hỏng vì lý do vô can (sai cú pháp TOML, thiếu mục) cũng
    làm ca 53 xanh.
    """
    cfg_dung = _viet_pyproject_tam(tmp_path, "testpaths")
    tep_test = _viet_tep_test_toi_gian(tmp_path)

    kq = _chay_pytest_con(tep_test, cau_hinh=cfg_dung)

    assert kq.returncode == 0
