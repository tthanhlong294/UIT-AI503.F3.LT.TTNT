"""Kiểm thử cho script tải và chọn lọc bộ dữ liệu LFW.

Không có ca test nào truy cập mạng: mọi tệp .tgz được dựng tại chỗ bằng `tarfile`,
mọi cấu hình dùng cho main() được ghi ra tệp YAML tạm trong `tmp_path`.
"""

import csv
import hashlib
import io
import json
import logging
import tarfile
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.download_lfw import (
    chon_danh_tinh,
    ghi_manifest,
    giai_nen,
    liet_ke_danh_tinh,
    main,
    sao_chep,
    tai_ve,
    tinh_sha256,
)
from src.common.exceptions import LoiCauHinh


def _tao_tgz(duong_dan: Path, muc: dict[str, bytes]) -> Path:
    """Dựng tệp .tgz tại chỗ với nội dung cho trước, hoàn toàn không cần mạng."""
    with tarfile.open(duong_dan, "w:gz") as tf:
        for ten, noi_dung in muc.items():
            info = tarfile.TarInfo(name=ten)
            info.size = len(noi_dung)
            tf.addfile(info, io.BytesIO(noi_dung))
    return duong_dan


def _tao_danh_tinh_that(tmp_path: Path, so_danh_tinh: int, so_anh: int) -> dict[str, list[Path]]:
    """Tạo cây thư mục danh tính thật trên đĩa để test sao_chep (cần tệp nguồn tồn tại)."""
    goc = tmp_path / "nguon"
    danh_tinh: dict[str, list[Path]] = {}
    for i in range(so_danh_tinh):
        ten = f"id{i:02d}"
        thu_muc = goc / ten
        thu_muc.mkdir(parents=True)
        anh = []
        for j in range(so_anh):
            p = thu_muc / f"{ten}_{j:04d}.jpg"
            p.write_bytes(f"anh-{ten}-{j}".encode())
            anh.append(p)
        danh_tinh[ten] = anh
    return danh_tinh


def _dict_danh_tinh_gia(so_danh_tinh: int = 20, so_anh: int = 3) -> dict[str, list[Path]]:
    """Từ điển danh tính giả (không cần tệp thật) — đủ dùng cho chon_danh_tinh."""
    ket_qua = {}
    for i in range(so_danh_tinh):
        ten = f"id{i:02d}"
        ket_qua[ten] = [Path(f"{ten}_{j}.jpg") for j in range(so_anh)]
    return ket_qua


def _ghi_config_lfw(tmp_path: Path, **ghi_de) -> Path:
    """Ghi một configs/data.yaml tối giản chỉ với mục `lfw`, dùng để test main()."""
    gia_tri = {
        "url": "http://khong-ton-tai.invalid/lfw.tgz",
        "archive_name": "lfw.tgz",
        "cache_dir": str(tmp_path / "cache"),
        "out_dir": str(tmp_path / "out"),
        "min_identities": 1,
        "min_images_per_identity": 1,
        "seed": 42,
        "citation": "Trich dan LFW",
        "homepage": "http://vis-www.cs.umass.edu/lfw/",
    }
    gia_tri.update(ghi_de)
    # json.dumps trả về cú pháp tương thích YAML (chuỗi có ngoặc kép, số không ngoặc),
    # tránh phải tự lo việc escape dấu \ trong đường dẫn Windows.
    noi_dung = "lfw:\n" + "\n".join(f"  {k}: {json.dumps(v)}" for k, v in gia_tri.items())
    cfg_path = tmp_path / "data.yaml"
    cfg_path.write_text(noi_dung, encoding="utf-8")
    return cfg_path


# ---------- Dòng 1-2: tinh_sha256 ----------


def test_01_tinh_sha256_khop_hashlib(tmp_path):
    """SHA256 tính bằng hàm khớp với hashlib tính trực tiếp trên cùng nội dung."""
    p = tmp_path / "nho.bin"
    p.write_bytes(b"noi dung tep nho")
    assert tinh_sha256(p) == hashlib.sha256(p.read_bytes()).hexdigest()


def test_02_tinh_sha256_tep_lon_doc_theo_khoi(tmp_path):
    """SHA256 vẫn đúng với tệp lớn hơn kích thước một khối đọc (5 MB)."""
    p = tmp_path / "lon.bin"
    p.write_bytes(b"x" * (5 * 1024 * 1024))
    assert tinh_sha256(p) == hashlib.sha256(p.read_bytes()).hexdigest()


# ---------- Dòng 3-5: giai_nen ----------


def test_03_giai_nen_thanh_cong(tmp_path):
    """Giải nén tệp .tgz hợp lệ ra đúng cây thư mục, trả về thư mục gốc vừa giải nén."""
    archive = _tao_tgz(tmp_path / "a.tgz", {"lfw/A/a_0001.jpg": b"noi dung anh"})
    dich = tmp_path / "dest"
    ket_qua = giai_nen(archive, dich)
    assert (dich / "lfw" / "A" / "a_0001.jpg").exists()
    assert ket_qua == dich / "lfw"


def test_04_giai_nen_tep_hong(tmp_path):
    """Tệp hỏng (không phải tar hợp lệ) ném LoiCauHinh nêu rõ tệp nén hỏng.

    Siết thêm vế phủ định: thông báo KHÔNG được lẫn cụm "vượt ra ngoài" của nhánh an ninh
    (dòng 5) — chứng minh hai thông báo thực sự phân biệt được (§3.1).
    """
    archive = tmp_path / "hong.tgz"
    archive.write_bytes(bytes(range(256)) * 20)
    with pytest.raises(LoiCauHinh) as exc_info:
        giai_nen(archive, tmp_path / "dest")
    thong_bao = str(exc_info.value)
    assert "hỏng" in thong_bao
    assert "vượt ra ngoài" not in thong_bao


def test_05_giai_nen_chan_duong_dan_vuot_ra_ngoai(tmp_path):
    """Mục '../../thoat.txt' trong tệp nén không được ghi ra ngoài thư mục đích.

    Siết thêm: thông báo phải nêu "vượt ra ngoài" và KHÔNG được lẫn cụm "hỏng" của nhánh
    tệp nén hỏng (dòng 4) — chứng minh hai thông báo thực sự phân biệt được (§3.1).
    """
    archive = _tao_tgz(tmp_path / "doc_hai.tgz", {"../../thoat.txt": b"du lieu gian lan"})
    dich = tmp_path / "trong" / "long" / "dest"

    with pytest.raises(LoiCauHinh) as exc_info:
        giai_nen(archive, dich)

    assert not any(tmp_path.rglob("thoat.txt"))
    thong_bao = str(exc_info.value)
    assert "vượt ra ngoài" in thong_bao
    assert "hỏng" not in thong_bao


# ---------- Dòng 6-8: liet_ke_danh_tinh ----------


def test_06_liet_ke_danh_tinh_dem_dung(tmp_path):
    """Đếm đúng số ảnh của từng danh tính: 3 thư mục lần lượt 1, 2, 5 ảnh."""
    goc = tmp_path / "lfw"
    (goc / "A").mkdir(parents=True)
    (goc / "A" / "a1.jpg").write_bytes(b"1")
    (goc / "B").mkdir(parents=True)
    (goc / "B" / "b1.jpg").write_bytes(b"1")
    (goc / "B" / "b2.jpg").write_bytes(b"1")
    (goc / "C").mkdir(parents=True)
    for i in range(5):
        (goc / "C" / f"c{i}.jpg").write_bytes(b"1")

    kq = liet_ke_danh_tinh(goc)
    assert len(kq) == 3
    assert len(kq["B"]) == 2


def test_07_liet_ke_danh_tinh_bo_qua_tep_khong_phai_anh(tmp_path):
    """Tệp không phải ảnh (README.txt) không được tính vào số ảnh của danh tính."""
    goc = tmp_path / "lfw"
    (goc / "A").mkdir(parents=True)
    (goc / "A" / "a1.jpg").write_bytes(b"1")
    (goc / "A" / "a2.jpg").write_bytes(b"1")
    (goc / "A" / "README.txt").write_text("khong phai anh", encoding="utf-8")

    kq = liet_ke_danh_tinh(goc)
    assert len(kq["A"]) == 2


def test_08_liet_ke_danh_tinh_thu_muc_khong_ton_tai(tmp_path):
    """Thư mục không tồn tại trả về dict rỗng, không ném ngoại lệ."""
    assert liet_ke_danh_tinh(tmp_path / "khong_ton_tai") == {}


# ---------- Dòng 9-13: chon_danh_tinh ----------


def test_09_chon_danh_tinh_cung_seed_tai_lap():
    """Cùng seed hai lần trả về đúng cùng một kết quả (R15)."""
    d = _dict_danh_tinh_gia()
    assert chon_danh_tinh(d, 10, 2, 42) == chon_danh_tinh(d, 10, 2, 42)


def test_10_chon_danh_tinh_khac_seed_ket_qua_khac():
    """Seed khác nhau cho kết quả khác nhau."""
    d = _dict_danh_tinh_gia()
    assert chon_danh_tinh(d, 10, 2, 42) != chon_danh_tinh(d, 10, 2, 7)


def test_11_chon_danh_tinh_loai_danh_tinh_thieu_anh():
    """Danh tính không đủ số ảnh tối thiểu (2 ảnh, cần 3) không được chọn."""
    d = {
        "du": [Path("a.jpg"), Path("b.jpg"), Path("c.jpg")],
        "thieu": [Path("x.jpg"), Path("y.jpg")],
    }
    kq = chon_danh_tinh(d, 1, 3, 42)
    assert "thieu" not in kq


def test_12_chon_danh_tinh_dung_so_luong_va_da_sap_xep():
    """Trả về đúng số lượng danh tính yêu cầu và kết quả đã được sắp xếp."""
    d = _dict_danh_tinh_gia()
    kq = chon_danh_tinh(d, 10, 2, 42)
    assert len(kq) == 10
    assert kq == sorted(kq)


def test_13_chon_danh_tinh_khong_du_nem_loi():
    """Không đủ danh tính thoả điều kiện ném LoiCauHinh, nêu rõ số tìm được và số cần."""
    d = _dict_danh_tinh_gia(so_danh_tinh=3, so_anh=3)
    with pytest.raises(LoiCauHinh) as exc_info:
        chon_danh_tinh(d, 10, 2, 42)
    thong_bao = str(exc_info.value)
    assert "3" in thong_bao and "10" in thong_bao


# ---------- Dòng 14-18: sao_chep ----------


def test_14_sao_chep_dung_so_anh(tmp_path):
    """Sao chép đúng tổng số ảnh của các danh tính đã chọn."""
    danh_tinh = _tao_danh_tinh_that(tmp_path, so_danh_tinh=3, so_anh=4)
    out_dir = tmp_path / "ra"
    sao_chep(danh_tinh, list(danh_tinh.keys()), out_dir)
    assert len(list(out_dir.rglob("*.jpg"))) == 12


def test_15_sao_chep_giu_cau_truc_thu_muc(tmp_path):
    """Ảnh chép ra giữ đúng cấu trúc <tên danh tính>/<tên ảnh gốc>."""
    danh_tinh = _tao_danh_tinh_that(tmp_path, so_danh_tinh=1, so_anh=1)
    ten = next(iter(danh_tinh))
    ten_anh = danh_tinh[ten][0].name
    out_dir = tmp_path / "ra"
    sao_chep(danh_tinh, [ten], out_dir)
    assert (out_dir / ten / ten_anh).exists()


def test_16_sao_chep_khong_ghi_de(tmp_path):
    """Không ghi đè tệp đích đã tồn tại — dữ liệu cũ phải nguyên vẹn."""
    danh_tinh = _tao_danh_tinh_that(tmp_path, so_danh_tinh=1, so_anh=1)
    ten = next(iter(danh_tinh))
    ten_anh = danh_tinh[ten][0].name
    out_dir = tmp_path / "ra"
    dich = out_dir / ten / ten_anh
    dich.parent.mkdir(parents=True)
    dich.write_bytes(b"DU_LIEU_CU")

    sao_chep(danh_tinh, [ten], out_dir)

    assert dich.read_bytes() == b"DU_LIEU_CU"


def test_17_sao_chep_dry_run_khong_ghi_gi(tmp_path):
    """dry_run=True không ghi bất kỳ tệp nào ra đĩa."""
    danh_tinh = _tao_danh_tinh_that(tmp_path, so_danh_tinh=2, so_anh=2)
    out_dir = tmp_path / "ra"
    out_dir.mkdir()
    truoc = list(out_dir.rglob("*"))

    sao_chep(danh_tinh, list(danh_tinh.keys()), out_dir, dry_run=True)

    sau = list(out_dir.rglob("*"))
    assert truoc == sau


def test_18_sao_chep_ban_ghi_khop_danh_tinh(tmp_path):
    """Số danh tính xuất hiện trong bản ghi manifest khớp số danh tính đã chọn."""
    danh_tinh = _tao_danh_tinh_that(tmp_path, so_danh_tinh=3, so_anh=2)
    da_chon = list(danh_tinh.keys())
    out_dir = tmp_path / "ra"
    ban_ghi = sao_chep(danh_tinh, da_chon, out_dir)
    assert len({r["identity"] for r in ban_ghi}) == len(da_chon)


# ---------- Dòng 19-20: ghi_manifest ----------


def test_19_ghi_manifest_co_dong_tieu_de(tmp_path):
    """Manifest sinh ra có dòng tiêu đề chứa đủ các cột bắt buộc."""
    m_file = tmp_path / "manifest.csv"
    ghi_manifest(
        m_file,
        [
            {
                "file": "A/a1.jpg",
                "identity": "A",
                "n_images": 1,
                "source_sha256": "abc123",
                "selected_seed": 42,
                "timestamp": "2026-08-15T00:00:00+07:00",
            }
        ],
    )
    header = m_file.read_text(encoding="utf-8").splitlines()[0]
    for cot in ("file", "identity", "n_images", "source_sha256", "selected_seed"):
        assert cot in header


def test_20_so_dong_manifest_khop_so_anh_da_chep(tmp_path):
    """Số dòng dữ liệu trong manifest khớp đúng số ảnh .jpg đã chép ra đĩa."""
    danh_tinh = _tao_danh_tinh_that(tmp_path, so_danh_tinh=2, so_anh=3)
    da_chon = list(danh_tinh.keys())
    out_dir = tmp_path / "ra"
    ban_ghi = sao_chep(danh_tinh, da_chon, out_dir)
    for rec in ban_ghi:
        rec["source_sha256"] = "abc123"
        rec["selected_seed"] = 42
        rec["timestamp"] = "2026-08-15T00:00:00+07:00"

    m_file = out_dir / "manifest.csv"
    ghi_manifest(m_file, ban_ghi)

    dong = [line for line in m_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    so_dong_du_lieu = len(dong) - 1
    assert so_dong_du_lieu == len(list(out_dir.rglob("*.jpg")))


# ---------- Dòng 21-22: tai_ve ----------


def test_21_tai_ve_tep_da_ton_tai_bo_qua(tmp_path):
    """Tệp đích đã tồn tại: bỏ qua tải lại, không ném lỗi, trả đúng đường dẫn."""
    dich = tmp_path / "x.tgz"
    dich.write_bytes(b"da co san tren dia")
    ket_qua = tai_ve("http://khong-ton-tai.invalid/x.tgz", dich)
    assert ket_qua == dich
    assert dich.read_bytes() == b"da co san tren dia"


def test_22_tai_ve_dry_run_khong_tao_tep(tmp_path):
    """dry_run=True không tạo tệp đích nào, kể cả khi tệp chưa tồn tại."""
    dich = tmp_path / "chua_co.tgz"
    tai_ve("http://khong-ton-tai.invalid/x.tgz", dich, dry_run=True)
    assert not dich.exists()


# ---------- Dòng 23-24: main ----------


def test_23_main_dry_run_khong_ghi_file(tmp_path, capsys):
    """main() --dry-run thoát 0, không ghi tệp, và in ra số danh tính dự kiến chọn.

    Dùng min_identities=7 (khác giá trị mặc định) để khẳng định số in ra đến từ việc
    main() thực sự chạy qua thân hàm, không phải trùng hợp với một hằng số khác.
    """
    cfg_path = _ghi_config_lfw(tmp_path, min_identities=7)
    truoc = set(tmp_path.rglob("*"))

    with patch("sys.argv", ["download_lfw.py", "--config", str(cfg_path), "--dry-run"]):
        assert main() == 0

    sau = set(tmp_path.rglob("*"))
    assert sau == truoc

    ra = capsys.readouterr()
    assert "7" in ra.out


def test_24_main_expect_sha256_lech(tmp_path, caplog):
    """main() với --expect-sha256 lệch thoát 1 vì so mã băm, thông báo nêu cả hai giá trị.

    ⚠️ Mồi bằng tệp nén .tgz HỢP LỆ (dựng bằng _tao_tgz), không phải byte tuỳ ý — nếu
    không, main() sẽ trả 1 từ bước giải nén và nhánh --expect-sha256 không hề được chạy.
    """
    cfg_path = _ghi_config_lfw(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    archive = _tao_tgz(
        cache_dir / "lfw.tgz",
        {"lfw/A/a_0001.jpg": b"anh 1", "lfw/A/a_0002.jpg": b"anh 2"},
    )
    sha_that = hashlib.sha256(archive.read_bytes()).hexdigest()

    with (
        caplog.at_level(logging.ERROR),
        patch(
            "sys.argv",
            ["download_lfw.py", "--config", str(cfg_path), "--expect-sha256", "0" * 64],
        ),
    ):
        assert main() == 1
    assert "0" * 64 in caplog.text and sha_that in caplog.text


def test_24a_main_expect_sha256_khop(tmp_path):
    """main() với --expect-sha256 khớp: đi qua được bước so mã băm, thoát 0.

    Đường thành công của cùng nhánh dòng 24 — thiếu vế này thì không phân biệt được
    "lệch mã băm" với "tệp nén hỏng" (cả hai đều làm main() trả 1).
    """
    cfg_path = _ghi_config_lfw(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    archive = _tao_tgz(
        cache_dir / "lfw.tgz",
        {"lfw/A/a_0001.jpg": b"anh 1", "lfw/A/a_0002.jpg": b"anh 2"},
    )
    sha_that = hashlib.sha256(archive.read_bytes()).hexdigest()

    with patch(
        "sys.argv",
        ["download_lfw.py", "--config", str(cfg_path), "--expect-sha256", sha_that],
    ):
        assert main() == 0


# ---------- Dòng 25-26: ghi_manifest từ chối bản ghi thiếu khoá (§4.1) ----------


def test_25_ghi_manifest_thieu_khoa_nem_loi(tmp_path):
    """Bản ghi thiếu khoá source_sha256: ghi_manifest ném LoiCauHinh nêu tên khoá thiếu."""
    m_file = tmp_path / "manifest.csv"
    ban_ghi = [
        {
            "file": "A/a1.jpg",
            "identity": "A",
            "n_images": 1,
            # thiếu source_sha256
            "selected_seed": 42,
            "timestamp": "2026-08-15T00:00:00+07:00",
        }
    ]
    with pytest.raises(LoiCauHinh) as exc_info:
        ghi_manifest(m_file, ban_ghi)
    assert "source_sha256" in str(exc_info.value)


def test_26_ghi_manifest_du_sau_khoa_thanh_cong(tmp_path):
    """Bản ghi đủ sáu khoá bắt buộc: ghi bình thường, không cột nào rỗng."""
    m_file = tmp_path / "manifest.csv"
    ban_ghi = [
        {
            "file": "A/a1.jpg",
            "identity": "A",
            "n_images": 1,
            "source_sha256": "abc123",
            "selected_seed": 42,
            "timestamp": "2026-08-15T00:00:00+07:00",
        }
    ]
    ghi_manifest(m_file, ban_ghi)

    with open(m_file, newline="", encoding="utf-8") as f:
        dong = next(csv.DictReader(f))
    for gia_tri in dong.values():
        assert gia_tri != ""


# ---------- Dòng 27-28: main() chặn chạy lại với seed khác (§4.2) ----------


def test_27_main_chay_lai_lech_seed_tra_ve_1(tmp_path, caplog):
    """Chạy lần hai với seed khác trên out_dir đã có manifest cũ: thoát 1, nêu cả hai seed."""
    cfg_path = _ghi_config_lfw(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    _tao_tgz(
        cache_dir / "lfw.tgz",
        {"lfw/A/a_0001.jpg": b"anh 1", "lfw/A/a_0002.jpg": b"anh 2"},
    )

    with patch("sys.argv", ["download_lfw.py", "--config", str(cfg_path), "--seed", "42"]):
        assert main() == 0

    with (
        caplog.at_level(logging.ERROR),
        patch("sys.argv", ["download_lfw.py", "--config", str(cfg_path), "--seed", "7"]),
    ):
        assert main() == 1
    # Dạng có dấu nháy — dạng trần ("42", "7") dễ khớp nhầm với chữ số nằm sẵn trong
    # đường dẫn tmp_path, không thực sự chứng minh thông báo có nêu seed hay không.
    assert "'42'" in caplog.text and "'7'" in caplog.text


def test_27a_main_lech_seed_giu_nguyen_du_lieu_cu(tmp_path):
    """Sau khi bị chặn vì lệch seed, dữ liệu cũ (thư mục + manifest) nguyên vẹn."""
    cfg_path = _ghi_config_lfw(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    _tao_tgz(
        cache_dir / "lfw.tgz",
        {"lfw/A/a_0001.jpg": b"anh 1", "lfw/A/a_0002.jpg": b"anh 2"},
    )

    with patch("sys.argv", ["download_lfw.py", "--config", str(cfg_path), "--seed", "42"]):
        assert main() == 0

    out_dir = tmp_path / "out"
    manifest_path = out_dir / "manifest.csv"
    so_thu_muc_truoc = len([p for p in out_dir.iterdir() if p.is_dir()])
    noi_dung_manifest_truoc = manifest_path.read_bytes()

    with patch("sys.argv", ["download_lfw.py", "--config", str(cfg_path), "--seed", "7"]):
        assert main() == 1

    so_thu_muc_sau = len([p for p in out_dir.iterdir() if p.is_dir()])
    assert so_thu_muc_sau == so_thu_muc_truoc
    assert manifest_path.read_bytes() == noi_dung_manifest_truoc


def test_27b_main_manifest_cu_hong_khong_lot_ngoai_le(tmp_path, caplog):
    """Manifest cũ hỏng (selected_seed không phải số): main() thoát 1, thông báo nhắc out_dir.

    Không dựng tệp .tgz mồi: chốt chặn đặt TRƯỚC KHI TẢI nên không cần tải/giải nén gì cả
    trước khi phát hiện manifest hỏng — nếu ValueError lọt ra ngoài không bị bắt, pytest sẽ
    báo lỗi (error) ở đây thay vì test đỏ có kiểm soát, tức "không ném ra ngoài" được chứng
    minh gián tiếp bởi chính việc main() trả về được giá trị.
    """
    cfg_path = _ghi_config_lfw(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    manifest_path = out_dir / "manifest.csv"
    manifest_path.write_text(
        "file,identity,n_images,source_sha256,selected_seed,timestamp\n"
        "A/a1.jpg,A,1,abc123,KHONG_PHAI_SO,2026-08-15T00:00:00+07:00\n",
        encoding="utf-8",
    )

    with (
        caplog.at_level(logging.ERROR),
        patch("sys.argv", ["download_lfw.py", "--config", str(cfg_path), "--seed", "42"]),
    ):
        ket_qua = main()

    assert ket_qua == 1
    assert str(out_dir) in caplog.text


def test_27c_main_manifest_cu_thieu_cot_seed_khong_lot_ngoai_le(tmp_path, caplog):
    """Manifest cũ thiếu hẳn cột selected_seed: main() thoát 1, không âm thầm coi như chưa có.

    dict.get("selected_seed") trả None chứ không ném — nếu không kiểm tường minh, main() sẽ
    hiểu nhầm là "chưa có manifest cũ" rồi chạy tiếp và trộn dữ liệu, đúng lỗ hổng §4.2 cảnh báo.
    Không dựng tệp .tgz mồi vì chốt chặn đặt TRƯỚC KHI TẢI.
    """
    cfg_path = _ghi_config_lfw(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir(parents=True)
    manifest_path = out_dir / "manifest.csv"
    manifest_path.write_text(
        "file,identity,n_images,source_sha256,timestamp\n"
        "A/a1.jpg,A,1,abc123,2026-08-15T00:00:00+07:00\n",
        encoding="utf-8",
    )

    with (
        caplog.at_level(logging.ERROR),
        patch("sys.argv", ["download_lfw.py", "--config", str(cfg_path), "--seed", "42"]),
    ):
        ket_qua = main()

    assert ket_qua == 1
    assert "selected_seed" in caplog.text


def test_28_main_chay_lai_cung_seed_thanh_cong(tmp_path):
    """Chạy lần hai với cùng seed: không lỗi, số thư mục danh tính không đổi."""
    cfg_path = _ghi_config_lfw(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    _tao_tgz(
        cache_dir / "lfw.tgz",
        {"lfw/A/a_0001.jpg": b"anh 1", "lfw/A/a_0002.jpg": b"anh 2"},
    )

    with patch("sys.argv", ["download_lfw.py", "--config", str(cfg_path), "--seed", "42"]):
        assert main() == 0

    out_dir = tmp_path / "out"
    so_thu_muc_truoc = len([p for p in out_dir.iterdir() if p.is_dir()])

    with patch("sys.argv", ["download_lfw.py", "--config", str(cfg_path), "--seed", "42"]):
        assert main() == 0

    so_thu_muc_sau = len([p for p in out_dir.iterdir() if p.is_dir()])
    assert so_thu_muc_sau == so_thu_muc_truoc


# ---------- Dòng 29-36: giai_nen — nhánh dự phòng cho Python < 3.11.4 (P0-04 §5, §8.1) ----------
#
# Mọi ca dựng tệp .tgz tại chỗ bằng tarfile, không chạm mạng. Ép chạy nhánh dự phòng bằng
# monkeypatch.delattr(tarfile, "data_filter", raising=False) — đây là lý do giai_nen() phải
# chọn nhánh BẰNG hasattr() ngay trong thân hàm, không phải bằng một hằng số tính sẵn lúc
# import (§5.3 đặc tả): chỉ như vậy phép ép này mới có tác dụng trên máy Python >= 3.11.4.


def _tao_tgz_voi_lien_ket(duong_dan: Path, ten_lien_ket: str, muc_tieu: str) -> Path:
    """Dựng tệp .tgz chứa một liên kết mềm (SYMTYPE) trỏ tới `muc_tieu`.

    Không dùng os.symlink: trên Windows lời gọi đó cần quyền quản trị (§8.1 đặc tả P0-04).
    """
    with tarfile.open(duong_dan, "w:gz") as tf:
        info = tarfile.TarInfo(name=ten_lien_ket)
        info.type = tarfile.SYMTYPE
        info.linkname = muc_tieu
        tf.addfile(info)
    return duong_dan


def test_29_giai_nen_nhanh_b_thanh_cong(tmp_path, monkeypatch):
    """Nhánh B (không có tarfile.data_filter) giải nén tệp hợp lệ đúng cây thư mục và trả về
    đúng thư mục gốc duy nhất bên trong tệp nén — đường thành công song song ca 03."""
    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    archive = _tao_tgz(tmp_path / "a.tgz", {"lfw/A/a_0001.jpg": b"noi dung anh"})
    dich = tmp_path / "dest"

    ket_qua = giai_nen(archive, dich)

    assert (dich / "lfw" / "A" / "a_0001.jpg").exists()
    assert ket_qua == dich / "lfw"


def test_30_giai_nen_nhanh_b_chan_duong_dan_vuot_ra_ngoai(tmp_path, monkeypatch):
    """Nhánh B chặn thành viên '../../thoat.txt' (tệp nén hợp lệ, chỉ tên thành viên độc hại):
    thông báo đúng 'vượt ra ngoài', không lẫn 'hỏng', và không ghi tệp độc hại ra đĩa."""
    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    archive = _tao_tgz(tmp_path / "doc_hai.tgz", {"../../thoat.txt": b"du lieu gian lan"})
    dich = tmp_path / "trong" / "long" / "dest"

    with pytest.raises(LoiCauHinh) as exc_info:
        giai_nen(archive, dich)

    thong_bao = str(exc_info.value)
    assert "vượt ra ngoài" in thong_bao
    assert "hỏng" not in thong_bao
    assert not any(tmp_path.rglob("thoat.txt"))


def test_31_giai_nen_nhanh_b_tep_hong(tmp_path, monkeypatch):
    """Nhánh B: tệp không phải tar hợp lệ (byte ngẫu nhiên) báo đúng 'hỏng', không lẫn
    'vượt ra ngoài' của nhánh an ninh."""
    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    archive = tmp_path / "hong.tgz"
    archive.write_bytes(bytes(range(256)) * 20)

    with pytest.raises(LoiCauHinh) as exc_info:
        giai_nen(archive, tmp_path / "dest")

    thong_bao = str(exc_info.value)
    assert "hỏng" in thong_bao
    assert "vượt ra ngoài" not in thong_bao


def test_32_giai_nen_nhanh_b_chan_duong_dan_tuyet_doi(tmp_path, monkeypatch):
    """Nhánh B chặn thành viên có tên đường dẫn tuyệt đối '/tmp/thoat.txt'.

    Đây là ca canh đúng cái bẫy nêu ở §5.6 đặc tả P0-04: trên Windows,
    ``PurePath("/tmp/x").is_absolute()`` trả về ``False`` vì thiếu ký tự ổ đĩa, nên phép kiểm
    chính không được dùng ``is_absolute()`` mà phải hợp đường dẫn rồi ``resolve()`` +
    ``is_relative_to()`` — phép đó bắt được cả hai nền tảng.
    """
    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    archive = _tao_tgz(tmp_path / "doc_hai.tgz", {"/tmp/thoat.txt": b"du lieu gian lan"})
    dich = tmp_path / "dest"

    with pytest.raises(LoiCauHinh) as exc_info:
        giai_nen(archive, dich)

    assert "vượt ra ngoài" in str(exc_info.value)


def test_33_giai_nen_nhanh_b_lien_ket_mem_ra_ngoai(tmp_path, monkeypatch):
    """Nhánh B chặn thành viên là liên kết mềm trỏ ra ngoài thư mục đích."""
    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    archive = _tao_tgz_voi_lien_ket(tmp_path / "lien_ket.tgz", "an_toan.txt", "../../ngoai.txt")
    dich = tmp_path / "dest"

    with pytest.raises(LoiCauHinh) as exc_info:
        giai_nen(archive, dich)

    assert "không an toàn" in str(exc_info.value)


def test_34_giai_nen_nhanh_a_lien_ket_mem_ra_ngoai(tmp_path):
    """Nhánh A (thư viện chuẩn) chặn CÙNG tệp nén của ca 33, với CÙNG thông báo.

    Cặp then chốt cùng ca 33: chứng minh phép quét liên kết/thiết bị (§5.4 đặc tả) áp dụng
    cho cả hai nhánh — không phải riêng nhánh B — nên hai nhánh xử lý liên kết y hệt nhau.
    Bỏ qua trên Python < 3.11.4 (không có tarfile.data_filter, không có nhánh A để kiểm).
    """
    if not hasattr(tarfile, "data_filter"):
        pytest.skip("Python hiện tại không có tarfile.data_filter (< 3.11.4)")
    archive = _tao_tgz_voi_lien_ket(tmp_path / "lien_ket.tgz", "an_toan.txt", "../../ngoai.txt")
    dich = tmp_path / "dest"

    with pytest.raises(LoiCauHinh) as exc_info:
        giai_nen(archive, dich)

    assert "không an toàn" in str(exc_info.value)


def test_35_giai_nen_hai_nhanh_cung_thong_bao_vuot_ra_ngoai(tmp_path, monkeypatch):
    """Hai nhánh xử lý CÙNG tệp nén '../../thoat.txt' phải cho CÙNG một thông báo lỗi.

    Không dựng bản sao byte-for-byte của tệp nén ở đường dẫn khác: giai_nen() chỉ MỞ ĐỌC
    archive, không ghi/sửa gì lên nó, nên gọi lại với đúng cùng đường dẫn archive ở nhánh B là
    đủ để cô lập biến duy nhất đang đổi giữa hai lượt gọi — có/không có tarfile.data_filter.
    Thông báo lỗi chứa nguyên văn đường dẫn archive (§5.2); nếu dùng hai tệp khác đường dẫn,
    phép so chuỗi ở đây sẽ luôn lệch vì một lý do vô can (đường dẫn khác nhau), không phải vì
    hai nhánh xử lý khác nhau — nên phải giữ nguyên cùng một archive cho cả hai lượt gọi.
    Bỏ qua trên Python < 3.11.4 (không có nhánh A để so sánh).
    """
    if not hasattr(tarfile, "data_filter"):
        pytest.skip("Python hiện tại không có tarfile.data_filter (< 3.11.4)")
    archive = _tao_tgz(tmp_path / "doc_hai.tgz", {"../../thoat.txt": b"du lieu gian lan"})

    with pytest.raises(LoiCauHinh) as exc_A:
        giai_nen(archive, tmp_path / "dest_a")

    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    with pytest.raises(LoiCauHinh) as exc_B:
        giai_nen(archive, tmp_path / "dest_b")

    assert str(exc_A.value) == str(exc_B.value)


def test_36_giai_nen_hai_nhanh_cung_ket_qua_thanh_cong(tmp_path, monkeypatch):
    """Hai nhánh giải nén CÙNG tệp nén hợp lệ ra hai thư mục đích khác nhau: cùng cây tương đối.

    Dòng cặp đường thành công của ca 35 — thiếu ca này, một cài đặt luôn ném lỗi ở cả hai
    nhánh (bất kể tệp nén hợp lệ hay không) vẫn qua được ca 35.
    Bỏ qua trên Python < 3.11.4 (không có nhánh A để so sánh).
    """
    if not hasattr(tarfile, "data_filter"):
        pytest.skip("Python hiện tại không có tarfile.data_filter (< 3.11.4)")
    archive = _tao_tgz(
        tmp_path / "hop_le.tgz",
        {"lfw/A/a_0001.jpg": b"anh 1", "lfw/B/b_0001.jpg": b"anh 2"},
    )
    dich_a = tmp_path / "dest_a"
    dich_b = tmp_path / "dest_b"

    giai_nen(archive, dich_a)
    monkeypatch.delattr(tarfile, "data_filter", raising=False)
    giai_nen(archive, dich_b)

    tuong_doi_a = {p.relative_to(dich_a).as_posix() for p in dich_a.rglob("*") if p.is_file()}
    tuong_doi_b = {p.relative_to(dich_b).as_posix() for p in dich_b.rglob("*") if p.is_file()}
    assert tuong_doi_a == tuong_doi_b
