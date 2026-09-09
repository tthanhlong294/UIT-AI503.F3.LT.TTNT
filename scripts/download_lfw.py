"""Script tải bộ dữ liệu LFW và chọn ra một số danh tính tái lập được làm tập impostor.

Xem docs/dac-ta/P1-03-download-lfw.md và docs/quy-uoc-du-lieu.md §4. Chỉ dùng thư viện chuẩn:
urllib.request để tải, tarfile để giải nén, hashlib để tính mã băm.
"""

import sys
from pathlib import Path

# Thêm gốc dự án vào sys.path để cho phép chạy trực tiếp kịch bản
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import csv
import datetime
import hashlib
import random
import shutil
import tarfile
import urllib.error
import urllib.request

from src.common.config import lay_gia_tri, nap_cau_hinh
from src.common.exceptions import LoiCauHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)

# 1 MB — đọc theo khối khi tính SHA256, tránh nạp cả tệp lớn (hàng trăm MB) vào bộ nhớ
KICH_THUOC_KHOI_DOC = 1024 * 1024

# Đuôi tệp được coi là ảnh khi quét thư mục danh tính LFW
DINH_DANG_ANH_HOP_LE = {".jpg", ".jpeg", ".png", ".ppm", ".pgm", ".bmp"}


def tai_ve(url: str, dich: Path, dry_run: bool = False) -> Path:
    """Tải tệp về đích. Bỏ qua nếu tệp đã tồn tại.

    Args:
        url: Địa chỉ tải tệp.
        dich: Đường dẫn tệp đích để lưu.
        dry_run: Chỉ báo dự định tải, không thực sự tải.

    Returns:
        Đường dẫn tệp đích (đã có sẵn hoặc vừa tải xong).

    Raises:
        LoiCauHinh: Nếu tải thất bại (lỗi mạng, lỗi ghi đĩa).
    """
    if dich.exists():
        logger.info("Tệp đã tồn tại, bỏ qua tải về: %s", dich)
        return dich

    if dry_run:
        logger.info("[DRY-RUN] Sẽ tải '%s' về '%s'", url, dich)
        return dich

    dich.parent.mkdir(parents=True, exist_ok=True)
    tam = dich.with_name(dich.name + ".part")
    try:
        with urllib.request.urlopen(url) as phan_hoi, open(tam, "wb") as f:
            shutil.copyfileobj(phan_hoi, f)
        tam.replace(dich)
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        if tam.exists():
            tam.unlink(missing_ok=True)
        raise LoiCauHinh(f"Tải tệp thất bại từ '{url}': {e}") from e

    logger.info("Đã tải xong: %s", dich)
    return dich


def tinh_sha256(duong_dan: Path) -> str:
    """Tính mã băm SHA256 của tệp, đọc theo khối để không nạp cả tệp vào bộ nhớ.

    Args:
        duong_dan: Đường dẫn tệp cần tính mã băm.

    Returns:
        Chuỗi hex của mã băm SHA256.
    """
    bam = hashlib.sha256()
    with open(duong_dan, "rb") as f:
        for khoi in iter(lambda: f.read(KICH_THUOC_KHOI_DOC), b""):
            bam.update(khoi)
    return bam.hexdigest()


# Ba thông báo lỗi của giai_nen(), đặt thành hằng số mức module: nhánh A (thư viện chuẩn,
# Python >= 3.11.4) và nhánh B (dự phòng cho Python < 3.11.4, vd. Raspberry Pi OS Bookworm
# đóng gói 3.11.2) đọc chung một hằng số nên luôn nói cùng một câu — xem §5.2 đặc tả P0-04.
_MSG_VUOT_RA_NGOAI = (
    "Tệp nén chứa đường dẫn vượt ra ngoài thư mục đích, đã chặn giải nén: {archive}"
)
_MSG_HONG = "Tệp nén hỏng, không mở được: {archive}"
_MSG_KHONG_AN_TOAN = (
    "Tệp nén chứa thành viên không an toàn (liên kết mềm/cứng hoặc tệp thiết bị), "
    "đã chặn giải nén: {archive}"
)


def giai_nen(archive: Path, dich: Path) -> Path:
    """Giải nén tệp .tgz vào thư mục đích, trả về thư mục gốc vừa giải nén.

    Chọn nhánh giải nén TẠI THỜI ĐIỂM GỌI, không tại thời điểm import module: thư viện chuẩn
    có bộ lọc an toàn ``filter="data"`` (và lớp ``tarfile.FilterError``) kể từ Python 3.11.4
    trở lên. Raspberry Pi OS Bookworm đóng gói Python 3.11.2 — chưa có bộ lọc này — nên cần
    một nhánh dự phòng tự kiểm tra thủ công (§5 đặc tả P0-04).

    Args:
        archive: Đường dẫn tệp nén .tgz.
        dich: Thư mục đích để giải nén vào.

    Returns:
        Thư mục cấp một duy nhất bên trong tệp nén (ví dụ ``dich/lfw``) nếu mọi mục đều
        nằm chung một thư mục gốc; ngược lại trả về chính `dich`.

    Raises:
        LoiCauHinh: Nếu tệp nén chứa đường dẫn vượt ra ngoài thư mục đích, hoặc chứa thành
            viên không an toàn (liên kết mềm/cứng, tệp thiết bị) — cả hai là dấu hiệu tệp
            độc hại, phải dừng và điều tra nguồn tải (không tự tải lại); hoặc nếu tệp nén
            hỏng, không mở được — lành tính, có thể tải lại. Ba nguyên nhân có ba thông báo
            khác nhau, xem §3.1/§5.2 đặc tả.
    """
    dich.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(archive, "r:*") as tf:
            thanh_vien = tf.getmembers()

            # Quét CHO CẢ HAI nhánh (cố ý đặt ngoài if/else bên dưới): bộ lọc "data" của
            # thư viện chuẩn cho phép liên kết trỏ vào bên trong thư mục đích, còn nhánh dự
            # phòng không có cách nào kiểm điều đó cho rẻ. Đặt phép quét ở đây làm hai nhánh
            # xử lý liên kết/thiết bị y hệt nhau, đổi lại giai_nen chặt hơn bộ lọc "data" một
            # bậc (từ chối luôn liên kết mềm/cứng, kể cả loại trỏ vào bên trong) — xem §5.4.
            for tv in thanh_vien:
                if not (tv.isfile() or tv.isdir()):
                    raise LoiCauHinh(_MSG_KHONG_AN_TOAN.format(archive=archive))

            if hasattr(tarfile, "data_filter"):
                # Nhánh A — thư viện chuẩn có bộ lọc "data" (Python >= 3.11.4).
                try:
                    tf.extractall(dich, filter="data")
                except tarfile.FilterError as e:
                    # FilterError là lớp con của TarError (đường dẫn vượt ra ngoài thư mục
                    # đích) nên phải bắt TRƯỚC TarError, không thì không bao giờ tới nhánh này.
                    raise LoiCauHinh(_MSG_VUOT_RA_NGOAI.format(archive=archive)) from e
            else:
                # Nhánh B — dự phòng cho Python < 3.11.4. Tự kiểm từng thành viên nằm trong
                # thư mục đích trước khi giải nén thủ công (không có tham số filter=).
                dich_that = dich.resolve()
                for tv in thanh_vien:
                    duong_dan_tv = (dich / tv.name).resolve()
                    if not duong_dan_tv.is_relative_to(dich_that):
                        raise LoiCauHinh(_MSG_VUOT_RA_NGOAI.format(archive=archive))
                tf.extractall(dich)  # không có filter= — tham số này chưa tồn tại ở 3.11.2
    except tarfile.TarError as e:
        raise LoiCauHinh(_MSG_HONG.format(archive=archive)) from e
    except OSError as e:
        raise LoiCauHinh(f"Không thể giải nén tệp: {archive}") from e

    cap_mot = {Path(tv.name).parts[0] for tv in thanh_vien if Path(tv.name).parts}
    if len(cap_mot) == 1:
        return dich / next(iter(cap_mot))
    return dich


def liet_ke_danh_tinh(thu_muc_lfw: Path) -> dict[str, list[Path]]:
    """Quét thư mục LFW, trả về {tên_danh_tính: [danh sách đường dẫn ảnh]}.

    Args:
        thu_muc_lfw: Thư mục gốc chứa các thư mục con, mỗi thư mục con là một danh tính.

    Returns:
        Từ điển ánh xạ tên danh tính sang danh sách đường dẫn ảnh (đã sắp xếp). Bỏ qua tệp
        không phải ảnh. Thư mục không tồn tại trả về dict rỗng, không ném ngoại lệ.
    """
    if not thu_muc_lfw.exists() or not thu_muc_lfw.is_dir():
        return {}

    ket_qua: dict[str, list[Path]] = {}
    for muc in sorted(thu_muc_lfw.iterdir()):
        if not muc.is_dir():
            continue
        anh = sorted(
            p for p in muc.iterdir() if p.is_file() and p.suffix.lower() in DINH_DANG_ANH_HOP_LE
        )
        ket_qua[muc.name] = anh
    return ket_qua


def chon_danh_tinh(
    danh_tinh: dict[str, list[Path]], so_luong: int, toi_thieu_anh: int, seed: int
) -> list[str]:
    """Chọn ngẫu nhiên có tái lập ra `so_luong` danh tính có ít nhất `toi_thieu_anh` ảnh.

    Args:
        danh_tinh: Từ điển ánh xạ tên danh tính sang danh sách đường dẫn ảnh.
        so_luong: Số danh tính cần chọn.
        toi_thieu_anh: Số ảnh tối thiểu để một danh tính đủ điều kiện.
        seed: Seed dùng cho bộ sinh ngẫu nhiên cục bộ, đảm bảo tái lập được (R15).

    Returns:
        Danh sách tên danh tính đã chọn, đã sắp xếp.

    Raises:
        LoiCauHinh: Nếu số danh tính thoả điều kiện ít hơn `so_luong`.
    """
    hop_le = sorted(ten for ten, anh in danh_tinh.items() if len(anh) >= toi_thieu_anh)
    if len(hop_le) < so_luong:
        raise LoiCauHinh(
            f"Không đủ danh tính có ít nhất {toi_thieu_anh} ảnh: "
            f"tìm được {len(hop_le)}, cần {so_luong}"
        )

    # random.Random(seed) cục bộ — không dùng random toàn cục — để kết quả chỉ phụ thuộc seed
    rng = random.Random(seed)
    da_chon = rng.sample(hop_le, so_luong)
    return sorted(da_chon)


def sao_chep(
    danh_tinh: dict[str, list[Path]], da_chon: list[str], thu_muc_ra: Path, dry_run: bool = False
) -> list[dict]:
    """Sao chép ảnh của các danh tính đã chọn sang thư mục ra, giữ nguyên cấu trúc và tên file.

    Args:
        danh_tinh: Từ điển ánh xạ tên danh tính sang danh sách đường dẫn ảnh nguồn.
        da_chon: Danh sách tên danh tính cần sao chép.
        thu_muc_ra: Thư mục đích, mỗi danh tính là một thư mục con.
        dry_run: Chỉ tính toán bản ghi manifest, không sao chép tệp nào.

    Returns:
        Danh sách bản ghi manifest (một bản ghi cho mỗi ảnh), mỗi bản ghi gồm các khoá
        `file`, `identity`, `n_images`.
    """
    ban_ghi: list[dict] = []
    for ten in da_chon:
        anh_list = danh_tinh.get(ten, [])
        n_images = len(anh_list)
        for nguon in anh_list:
            duong_dan_tuong_doi = Path(ten, nguon.name).as_posix()
            ban_ghi.append({"file": duong_dan_tuong_doi, "identity": ten, "n_images": n_images})

            if dry_run:
                continue

            dich = thu_muc_ra / ten / nguon.name
            if dich.exists():
                logger.debug("Bỏ qua, tệp đích đã tồn tại, không ghi đè: %s", dich)
                continue

            dich.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(nguon, dich)

    return ban_ghi


def ghi_manifest(duong_dan: Path, ban_ghi: list[dict]) -> None:
    """Ghi manifest CSV kèm dòng tiêu đề (ghi đè, không ghi nối — xem §4.1).

    Args:
        duong_dan: Đường dẫn tệp manifest.csv.
        ban_ghi: Danh sách bản ghi manifest cần ghi.

    Raises:
        LoiCauHinh: Nếu bất kỳ bản ghi nào thiếu một trong sáu khoá bắt buộc ở §4.1.
            `csv.DictWriter` mặc định điền chuỗi rỗng cho khoá thiếu — không lỗi, không
            cảnh báo — nên phải kiểm tường minh để không làm mất dấu vết tái lập.
    """
    cot = ["file", "identity", "n_images", "source_sha256", "selected_seed", "timestamp"]
    for rec in ban_ghi:
        thieu = [khoa for khoa in cot if khoa not in rec]
        if thieu:
            raise LoiCauHinh(f"Bản ghi manifest thiếu khoá bắt buộc: {', '.join(thieu)}")

    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    with open(duong_dan, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cot)
        writer.writeheader()
        writer.writerows(ban_ghi)


def _doc_seed_manifest_cu(duong_dan_manifest: Path) -> int | None:
    """Đọc `selected_seed` từ manifest cũ nếu có, dùng để chặn chạy lại lệch seed (§4.2).

    Args:
        duong_dan_manifest: Đường dẫn tệp manifest.csv cần đọc.

    Returns:
        Giá trị `selected_seed` của dòng dữ liệu đầu tiên tìm được, hoặc `None` nếu
        manifest không có dòng dữ liệu nào.

    Raises:
        LoiCauHinh: Nếu manifest cũ không đọc được — tệp hỏng, thiếu cột `selected_seed`,
            hoặc giá trị của cột không phải số. **Không** được âm thầm coi như "chưa có
            manifest", vì dữ liệu cũ vẫn nằm trong `out_dir` và sẽ bị trộn nếu bỏ qua (§4.2).
    """
    try:
        with open(duong_dan_manifest, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is not None and "selected_seed" not in reader.fieldnames:
                raise LoiCauHinh(
                    f"Manifest cũ tại '{duong_dan_manifest}' thiếu cột 'selected_seed'. "
                    f"Dọn thư mục '{duong_dan_manifest.parent}' trước khi chạy lại."
                )
            for dong in reader:
                gia_tri = dong.get("selected_seed")
                if gia_tri:
                    return int(gia_tri)
        return None
    except (ValueError, OSError, csv.Error) as e:
        raise LoiCauHinh(
            f"Manifest cũ tại '{duong_dan_manifest}' không đọc được: {e}. "
            f"Dọn thư mục '{duong_dan_manifest.parent}' trước khi chạy lại."
        ) from e


def main() -> int:
    """Điểm vào CLI. Trả về 0 nếu thành công, 1 nếu lỗi.

    TRƯỚC KHI TẢI, nếu `out_dir` đã có manifest cũ với `selected_seed` khác seed đang dùng,
    hoặc manifest cũ không đọc được, thì raise LoiCauHinh — xem §4.2.
    """
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description=(
            "Tải bộ dữ liệu LFW gốc, chọn ra một số danh tính tái lập được làm tập impostor "
            "để đo FAR (xem docs/quy-uoc-du-lieu.md §4)."
        )
    )
    parser.add_argument(
        "--config", default="configs/data.yaml", help="Đường dẫn file cấu hình dữ liệu"
    )
    parser.add_argument("--out", help="Ghi đè thư mục đầu ra (mặc định lấy từ lfw.out_dir)")
    parser.add_argument(
        "--seed", type=int, help="Ghi đè seed chọn danh tính (mặc định lấy từ lfw.seed)"
    )
    parser.add_argument(
        "--expect-sha256", help="Đối chiếu mã băm SHA256 của tệp nén đã tải; lệch thì dừng"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Chỉ in kế hoạch, không tải và không ghi file nào"
    )
    args = parser.parse_args()

    try:
        cfg = nap_cau_hinh(args.config)
        url = lay_gia_tri(cfg, "lfw.url")
        archive_name = lay_gia_tri(cfg, "lfw.archive_name")
        cache_dir = Path(lay_gia_tri(cfg, "lfw.cache_dir"))
        out_dir = Path(args.out) if args.out else Path(lay_gia_tri(cfg, "lfw.out_dir"))
        min_identities = int(lay_gia_tri(cfg, "lfw.min_identities"))
        min_images_per_identity = int(lay_gia_tri(cfg, "lfw.min_images_per_identity"))
        seed = args.seed if args.seed is not None else int(lay_gia_tri(cfg, "lfw.seed"))
        citation = lay_gia_tri(cfg, "lfw.citation")
        homepage = lay_gia_tri(cfg, "lfw.homepage")
    except LoiCauHinh as e:
        logger.error("Không thể đọc cấu hình: %s", e)
        return 1

    archive_path = cache_dir / archive_name

    if args.dry_run:
        print("\n### BẢNG KẾ HOẠCH TẢI LFW (DRY-RUN)")
        print(f"- URL nguồn           : `{url}`")
        print(f"- Tệp nén lưu tại     : `{archive_path}`")
        print(f"- Thư mục ra          : `{out_dir}`")
        print(f"- Số danh tính cần    : `{min_identities}`")
        print(f"- Ảnh tối thiểu/người : `{min_images_per_identity}`")
        print(f"- Seed                : `{seed}`")
        print(f"\nNguồn dữ liệu: {citation}")
        print(f"Trang chủ    : {homepage}\n")
        return 0

    try:
        # TRƯỚC KHI TẢI (§4.2): lệch seed thì dừng ngay, tránh tốn công tải/giải nén
        # cả trăm MB rồi mới báo lỗi đã biết chắc từ đầu.
        manifest_path = out_dir / "manifest.csv"
        if manifest_path.exists():
            seed_cu = _doc_seed_manifest_cu(manifest_path)
            if seed_cu is not None and seed_cu != seed:
                raise LoiCauHinh(
                    f"'{out_dir}' đã có manifest với seed cũ '{seed_cu}', khác seed đang "
                    f"dùng '{seed}'. Dọn thư mục '{out_dir}' trước khi chạy lại với seed khác."
                )

        tai_ve(url, archive_path)
        sha256_thuc_te = tinh_sha256(archive_path)

        if args.expect_sha256 and args.expect_sha256 != sha256_thuc_te:
            logger.error(
                "Mã băm không khớp — kỳ vọng '%s', thực tế '%s'",
                args.expect_sha256,
                sha256_thuc_te,
            )
            return 1

        thu_muc_goc = giai_nen(archive_path, cache_dir)
        danh_tinh = liet_ke_danh_tinh(thu_muc_goc)
        da_chon = chon_danh_tinh(danh_tinh, min_identities, min_images_per_identity, seed)

        ban_ghi = sao_chep(danh_tinh, da_chon, out_dir)

        dau_thoi_gian = datetime.datetime.now().astimezone().isoformat()
        for rec in ban_ghi:
            rec["source_sha256"] = sha256_thuc_te
            rec["selected_seed"] = seed
            rec["timestamp"] = dau_thoi_gian

        ghi_manifest(out_dir / "manifest.csv", ban_ghi)

        print("\n### KẾT QUẢ TẢI LFW")
        print(f"- Số danh tính đã chọn : `{len(da_chon)}`")
        print(f"- Tổng số ảnh đã chép  : `{len(ban_ghi)}`")
        print(f"- Thư mục lưu trữ      : `{out_dir}`")
        print(f"- Mã băm tệp nén       : `{sha256_thuc_te}`")
        print(f"\nNguồn dữ liệu: {citation}")
        print(f"Trang chủ    : {homepage}\n")
        return 0
    except LoiCauHinh as e:
        logger.error("Lỗi khi xử lý bộ dữ liệu LFW: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
