"""Kiểm thử cấu hình pytest khai báo trong pyproject.toml (mã việc P0-04, §8.3 đặc tả).

Đọc `[tool.pytest.ini_options]` bằng `tomllib` của thư viện chuẩn (không cần gói ngoài
`requirements.txt`). Ca 47/48 gọi một tiến trình pytest CON trên một bộ ca kiểm thử tối giản
dựng trong `tmp_path`, để kiểm chứng `--strict-markers` thực sự chặn dấu sai chính tả mà
KHÔNG chặn nhầm dấu đúng — không ca nào ở đây chạm mạng hay cần `git`.
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


def _chay_pytest_con(tep_test: Path) -> subprocess.CompletedProcess:
    """Chạy một tiến trình pytest con trên đúng một tệp test, dùng cấu hình của kho.

    Args:
        tep_test: Đường dẫn tệp test cần chạy.

    Returns:
        Kết quả tiến trình con (mã thoát, stdout, stderr).
    """
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-c",
            "pyproject.toml",
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
