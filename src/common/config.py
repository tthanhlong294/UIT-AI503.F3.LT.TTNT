"""Module xử lý nạp và truy xuất cấu hình YAML."""

import os
import re
from pathlib import Path
from typing import Any

import yaml

from src.common.exceptions import LoiCauHinh

_KHONG_CO = object()


def _thay_the_bien_moi_truong(gia_tri: str) -> str:
    pattern = re.compile(r"\$\{([^}]+)\}")

    def thay_the(match: re.Match[str]) -> str:
        ten_bien = match.group(1)
        if ten_bien in os.environ:
            return os.environ[ten_bien]
        raise LoiCauHinh(f"Thiếu biến môi trường bắt buộc: '{ten_bien}'")

    return pattern.sub(thay_the, gia_tri)


def _mo_rong_cau_hinh(du_lieu: Any) -> Any:
    if isinstance(du_lieu, str):
        return _thay_the_bien_moi_truong(du_lieu)
    elif isinstance(du_lieu, dict):
        return {k: _mo_rong_cau_hinh(v) for k, v in du_lieu.items()}
    elif isinstance(du_lieu, list):
        return [_mo_rong_cau_hinh(item) for item in du_lieu]
    elif isinstance(du_lieu, tuple):
        return tuple(_mo_rong_cau_hinh(item) for item in du_lieu)
    return du_lieu


def nap_cau_hinh(duong_dan: str | Path) -> dict[str, Any]:
    """Nạp file cấu hình YAML và mở rộng biến môi trường dạng ${TEN_BIEN}.

    Args:
        duong_dan: Đường dẫn tới file cấu hình YAML.

    Returns:
        Dict chứa dữ liệu cấu hình đã mở rộng biến môi trường.

    Raises:
        LoiCauHinh: Nếu file không tồn tại, sai cú pháp YAML, không phải mapping,
            hoặc thiếu biến môi trường được tham chiếu.
    """
    duong_dan_path = Path(duong_dan)
    if not duong_dan_path.exists() or not duong_dan_path.is_file():
        raise LoiCauHinh(f"File cấu hình không tồn tại hoặc không phải file: {duong_dan_path}")

    try:
        with open(duong_dan_path, "r", encoding="utf-8") as f:
            noi_dung = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise LoiCauHinh(f"Lỗi cú pháp YAML trong file {duong_dan_path}: {e}") from e
    except Exception as e:
        raise LoiCauHinh(f"Không thể đọc file cấu hình {duong_dan_path}: {e}") from e

    if noi_dung is None:
        return {}

    if not isinstance(noi_dung, dict):
        raise LoiCauHinh(f"Nội dung file cấu hình {duong_dan_path} không phải dạng mapping (dict)")

    return _mo_rong_cau_hinh(noi_dung)


def lay_gia_tri(cfg: dict[str, Any], duong_dan_key: str, mac_dinh: Any = _KHONG_CO) -> Any:
    """Lấy giá trị lồng nhau theo đường dẫn dạng "a.b.c".

    Args:
        cfg: Dict chứa cấu hình.
        duong_dan_key: Chuỗi đường dẫn key phân cách bởi dấu chấm.
        mac_dinh: Giá trị mặc định nếu key không tồn tại.

    Returns:
        Giá trị tương ứng với key hoặc giá trị mặc định.

    Raises:
        LoiCauHinh: Khi key không tồn tại và không có giá trị mặc định,
            hoặc khi đi qua một giá trị không phải dict.
    """
    if not duong_dan_key:
        raise LoiCauHinh("Đường dẫn key không được để rỗng")

    cac_khoa = duong_dan_key.split(".")
    hien_tai = cfg

    for i, khoa in enumerate(cac_khoa):
        if not isinstance(hien_tai, dict):
            duong_dan_truoc = ".".join(cac_khoa[:i])
            raise LoiCauHinh(
                f"Không thể truy cập key '{duong_dan_key}': "
                f"phần '{duong_dan_truoc}' có giá trị không phải dict"
            )

        if khoa not in hien_tai:
            if mac_dinh is not _KHONG_CO:
                return mac_dinh
            raise LoiCauHinh(f"Thiếu key bắt buộc trong cấu hình: '{duong_dan_key}'")

        hien_tai = hien_tai[khoa]

    return hien_tai
