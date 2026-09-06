"""Quét ngưỡng cosine similarity và đo tốc độ khối nhận diện danh tính — bước 3.5 CLAUDE.md.

Xem docs/dac-ta/P3-05-benchmark-recognize.md. Script này CHỈ ĐO và GHI SỐ, không vẽ gì cả — ROC/DET
thuộc notebooks/06_nguong_va_roc.ipynb (CLAUDE.md §2.9 tách đo, vẽ và minh hoạ thành ba việc).

Sinh ra hai tập điểm số (genuine, impostor) cho MỘT backend nhận diện, quét ngưỡng trên lưới đều,
và ghi số liệu thô cùng bảng quét ra results/ để bước 3.7c chốt ngưỡng và bước 3.8 lập bảng so sánh
hai phương án.

⚠️ Điểm chịu lực nhất (§4.1 đặc tả): ảnh đã dùng để đăng ký một người TUYỆT ĐỐI không được làm probe
của chính người đó — nếu không, điểm số sẽ cao giả tạo một cách không ai phát hiện được. Việc loại
trừ dựa trên MÃ BĂM NỘI DUNG tệp, không dựa trên đường dẫn: một ảnh bị chép sang thư mục khác vẫn
phải bị loại.

⚠️ Bài toán là open-set: một probe của người lạ phải bị TỪ CHỐI theo ngưỡng, không phải gán cho
người gần nhất trong gallery. Vì vậy script không tính "accuracy kiểu phân loại" — mọi chỉ số đều
là hàm của ngưỡng quét được.
"""

import sys
from pathlib import Path

# Thêm gốc dự án vào sys.path để cho phép chạy trực tiếp kịch bản
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import csv
import datetime
import hashlib
import importlib.metadata
import json
import math
import platform
import random
import subprocess
import time

import cv2
import numpy as np
import onnxruntime as ort

from scripts.benchmark_detect import doc_nhiet_do_cpu
from scripts.export_detector_ncnn import xac_dinh_moi_truong
from src.common.config import lay_gia_tri, nap_cau_hinh
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger
from src.recognizer.base import BoNhanDien, do_tuong_dong
from src.recognizer.factory import tao_bo_nhan_dien

logger = lay_logger(__name__)

# R9 (experiment-protocol.instructions.md §6): mỗi lần đo tối thiểu 100 mẫu.
SO_MAU_TOI_THIEU = 100

# Mã môi trường của phần cứng đích (experiment-protocol.instructions.md §2). Chỉ số đo ở môi
# trường này mới dùng để kết luận chỉ tiêu độ chính xác nhận diện.
_MOI_TRUONG_PHAN_CUNG_DICH = "pi5"

# Đuôi tệp được coi là ảnh khi quét thư mục theo người.
_DINH_DANG_ANH_HOP_LE = {".jpg", ".jpeg", ".png"}

# Trạng thái "đã đăng ký" trong manifest.csv của gallery — quy ước chốt ở scripts/enroll.py.
_TRANG_THAI_DA_DANG_KY = "da_dang_ky"

# Thư mục ghi kết quả mặc định — hằng số module để ca kiểm thử monkeypatch ra tmp_path,
# không ghi vào results/ thật khi chạy pytest (cùng cách benchmark_detect.py:61 làm).
_THU_MUC_KET_QUA_MAC_DINH = Path("results")

# Đường dẫn ảnh hưởng tới số đo — cùng quy ước phạm vi git_dirty của benchmark_detect.py /
# scripts/enroll.py.
_DUONG_DAN_ANH_HUONG_PHEP_DO = (
    "src",
    "scripts",
    "configs",
    "requirements.txt",
    "requirements-dev.txt",
)

# 14 cột CSV thô — đúng thứ tự chốt ở §7.4 đặc tả.
_COT_CSV_THO = [
    "run_id",
    "backend",
    "tap",
    "user_id_that",
    "nhan",
    "anh_bam",
    "top1_user",
    "top1_score",
    "diem_dung_nguoi",
    "so_chieu",
    "latency_trich_ms",
    "latency_so_khop_ms",
    "latency_identify_ms",
    "cpu_temp_c",
]

# 17 cột CSV bảng quét ngưỡng — đúng thứ tự chốt ở §7.4 đặc tả.
_COT_CSV_NGUONG = [
    "run_id",
    "backend",
    "tap",
    "nguong",
    "so_genuine",
    "so_impostor",
    "tp",
    "fp_impostor",
    "fp_nham_nguoi",
    "fn",
    "tn",
    "far",
    "frr",
    "ti_le_gan_nham",
    "accuracy",
    "precision",
    "recall",
]

# 23 khoá bắt buộc của .meta.json — liệt kê đích danh (§7.4 đặc tả).
_KHOA_META_BAT_BUOC = (
    "run_id",
    "timestamp",
    "git_commit",
    "git_dirty",
    "git_dirty_toan_cay",
    "script",
    "command",
    "device",
    "moi_truong",
    "software",
    "config_file",
    "config_snapshot",
    "backend",
    "tap",
    "dataset",
    "seed",
    "warmup_probes",
    "cpu_temp_start_c",
    "cpu_temp_max_c",
    "duration_s",
    "notes",
    "tep_ket_qua",
    "tom_tat",
)


def bam_noi_dung(duong_dan: Path) -> str:
    """Mã băm sha256 nội dung một tệp, dạng hex.

    Args:
        duong_dan: Đường dẫn tệp cần băm.

    Returns:
        Chuỗi hex 64 ký tự của mã băm sha256 nội dung tệp.
    """
    bam = hashlib.sha256()
    with open(duong_dan, "rb") as f:
        while True:
            khoi = f.read(65536)
            if not khoi:
                break
            bam.update(khoi)
    return bam.hexdigest()


def bam_danh_sach_tep(danh_sach: list[Path], goc: Path) -> str:
    """Mã băm của cả tập tệp, theo công thức chốt ở §4.5 đặc tả.

    Với mỗi tệp dựng dòng "<đường_dẫn_tương_đối_POSIX>:<sha256_nội_dung>", sắp xếp toàn bộ
    dòng, nối bằng "\\n", mã hoá UTF-8, rồi sha256 chuỗi đó. Băm cả nội dung lẫn đường dẫn
    tương đối: đổi nội dung một ảnh mà giữ nguyên tên, hoặc đổi tên mà giữ nguyên nội dung,
    đều làm mã băm đổi.

    Args:
        danh_sach: Danh sách đường dẫn tệp cần băm.
        goc: Thư mục gốc dùng để tính đường dẫn tương đối.

    Returns:
        Chuỗi hex của mã băm tổng hợp. Bất biến với thứ tự truyền vào `danh_sach`.
    """
    goc_tuyet_doi = Path(goc).resolve()
    dong: list[str] = []
    for p in danh_sach:
        duong_dan_tuong_doi = Path(p).resolve().relative_to(goc_tuyet_doi).as_posix()
        dong.append(f"{duong_dan_tuong_doi}:{bam_noi_dung(p)}")
    dong.sort()
    chuoi = "\n".join(dong)
    return hashlib.sha256(chuoi.encode("utf-8")).hexdigest()


def liet_ke_anh_theo_nguoi(thu_muc: Path) -> dict[str, list[Path]]:
    """Liệt kê ảnh theo user_id, cấu trúc <thu_muc>/<user_id>/*.{jpg,jpeg,png}, không đệ quy.

    Args:
        thu_muc: Thư mục gốc, mỗi thư mục con là một người.

    Returns:
        Ánh xạ user_id sang danh sách đường dẫn ảnh đã sắp xếp.

    Raises:
        LoiCauHinh: thư mục không tồn tại, hoặc không có thư mục con nào.
    """
    thu_muc = Path(thu_muc)
    if not thu_muc.exists() or not thu_muc.is_dir():
        raise LoiCauHinh(f"Thư mục ảnh không tồn tại hoặc không phải thư mục: '{thu_muc}'")

    thu_muc_con = sorted(p for p in thu_muc.iterdir() if p.is_dir())
    if not thu_muc_con:
        raise LoiCauHinh(f"Thư mục ảnh '{thu_muc}' rỗng, không có thư mục người dùng nào")

    ket_qua: dict[str, list[Path]] = {}
    for tm in thu_muc_con:
        ket_qua[tm.name] = sorted(
            p for p in tm.iterdir() if p.is_file() and p.suffix.lower() in _DINH_DANG_ANH_HOP_LE
        )
    return ket_qua


def doc_danh_sach_danh_tinh(duong_dan: Path) -> list[str]:
    """Đọc tệp danh sách user_id; bỏ dòng rỗng và dòng bắt đầu bằng '#'.

    Args:
        duong_dan: Đường dẫn tệp danh sách, mỗi dòng một user_id.

    Returns:
        Danh sách user_id, theo đúng thứ tự trong tệp.

    Raises:
        LoiCauHinh: tệp không tồn tại, hoặc tệp không còn dòng hợp lệ nào.
    """
    duong_dan = Path(duong_dan)
    if not duong_dan.exists() or not duong_dan.is_file():
        raise LoiCauHinh(f"Tệp danh sách impostor không tồn tại: '{duong_dan}'")

    ket_qua: list[str] = []
    for dong in duong_dan.read_text(encoding="utf-8").splitlines():
        dong = dong.strip()
        if not dong or dong.startswith("#"):
            continue
        ket_qua.append(dong)

    if not ket_qua:
        raise LoiCauHinh(f"Tệp danh sách impostor '{duong_dan}' không còn dòng hợp lệ nào")
    return ket_qua


def nap_gallery_tu_dia(thu_muc: Path) -> tuple[dict[str, np.ndarray], dict, list[dict]]:
    """Nạp gallery đã dựng sẵn — xem §4.4 chế độ 'tep' đặc tả, các bước 1 đến 4.

    Args:
        thu_muc: Thư mục gallery, chứa các tệp .npy, manifest.csv và gallery.meta.json.

    Returns:
        (gallery, nội_dung_gallery_meta_json, bản_ghi_manifest).

    Raises:
        LoiCauHinh: thiếu thư mục, thiếu manifest.csv, thiếu gallery.meta.json,
            hoặc vectơ lệch số chiều.
    """
    thu_muc = Path(thu_muc)
    if not thu_muc.exists() or not thu_muc.is_dir():
        cha = thu_muc.parent
        co_san: list[str] = []
        if cha.exists() and cha.is_dir():
            co_san = sorted(
                p.name for p in cha.iterdir() if p.is_dir() and not p.name.startswith(".")
            )
        raise LoiCauHinh(
            f"Thư mục gallery không tồn tại: '{thu_muc}'. Các backend có sẵn trong '{cha}': "
            f"{', '.join(co_san) if co_san else 'không có'}"
        )

    duong_dan_manifest = thu_muc / "manifest.csv"
    duong_dan_meta = thu_muc / "gallery.meta.json"
    if not duong_dan_manifest.exists():
        raise LoiCauHinh(f"Thiếu manifest.csv trong thư mục gallery '{thu_muc}'")
    if not duong_dan_meta.exists():
        raise LoiCauHinh(f"Thiếu gallery.meta.json trong thư mục gallery '{thu_muc}'")

    with open(duong_dan_meta, "r", encoding="utf-8") as f:
        meta_gallery = json.load(f)

    with open(duong_dan_manifest, "r", newline="", encoding="utf-8") as f:
        ban_ghi_manifest = list(csv.DictReader(f))

    so_chieu_khai_bao = meta_gallery.get("so_chieu")
    gallery: dict[str, np.ndarray] = {}
    for p in sorted(thu_muc.iterdir()):
        if not (p.is_file() and p.suffix == ".npy"):
            continue
        vec = np.load(p)
        if so_chieu_khai_bao is not None and vec.shape != (so_chieu_khai_bao,):
            raise LoiCauHinh(
                f"Vectơ '{p.name}' có hình dạng {vec.shape}, kỳ vọng ({so_chieu_khai_bao},) "
                f"theo gallery.meta.json"
            )
        gallery[p.stem] = vec

    return gallery, meta_gallery, ban_ghi_manifest


def suy_tap_anh_da_dang_ky(
    meta_gallery: dict, ban_ghi_manifest: list[dict], goc_ghi_de: Path | None
) -> list[Path]:
    """Suy ra tập ảnh đã dùng để đăng ký — xem §4.4 chế độ 'tep' đặc tả, các bước 6 và 7.

    Args:
        meta_gallery: Nội dung gallery.meta.json, chứa khoá `duong_dan_vao`.
        ban_ghi_manifest: Bản ghi manifest.csv, mỗi dòng một người.
        goc_ghi_de: Thư mục ghi đè `duong_dan_vao`, dùng khi thư mục nguồn đã dời chỗ.
            `None` nghĩa là dùng nguyên `duong_dan_vao` trong meta.

    Returns:
        Danh sách đường dẫn ảnh đã dùng đăng ký, của mọi người có trang_thai = da_dang_ky.

    Raises:
        LoiCauHinh: thư mục nguồn của một người không tồn tại, hoặc số ảnh tìm được lệch
            `so_anh_dung` trong manifest.
    """
    if goc_ghi_de is not None:
        goc = Path(goc_ghi_de)
    else:
        duong_dan_vao_tho = str(meta_gallery.get("duong_dan_vao", ""))
        goc = Path(duong_dan_vao_tho.replace("\\", "/"))

    ket_qua: list[Path] = []
    for ban in ban_ghi_manifest:
        if ban.get("trang_thai") != _TRANG_THAI_DA_DANG_KY:
            continue

        user_id = ban["user_id"]
        thu_muc_nguoi = goc / user_id
        if not thu_muc_nguoi.exists() or not thu_muc_nguoi.is_dir():
            raise LoiCauHinh(
                f"Thư mục ảnh đã đăng ký của '{user_id}' không tồn tại: '{thu_muc_nguoi}' "
                "(thư mục nguồn có thể đã dời chỗ kể từ lượt đăng ký — dùng --anh-da-dang-ky "
                "để ghi đè)"
            )

        anh = sorted(
            p
            for p in thu_muc_nguoi.iterdir()
            if p.is_file() and p.suffix.lower() in _DINH_DANG_ANH_HOP_LE
        )
        so_anh_dung = int(ban["so_anh_dung"])
        if len(anh) != so_anh_dung:
            raise LoiCauHinh(
                f"Số ảnh tìm được của '{user_id}' ({len(anh)}) khác so_anh_dung trong "
                f"manifest ({so_anh_dung})"
            )
        ket_qua.extend(anh)

    return ket_qua


def chia_enroll_probe(
    anh_theo_nguoi: dict[str, list[Path]], so_anh_enroll: int, seed: int
) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    """Chia enroll/probe theo từng người — xem §4.4 chế độ 'chia' đặc tả, các bước 2 đến 4.

    Mỗi người dùng một bộ sinh ngẫu nhiên RIÊNG (seed theo từng người), để thêm hay bớt một
    danh tính không làm đổi phép chia của những người còn lại.

    Args:
        anh_theo_nguoi: Ánh xạ user_id sang danh sách ảnh của người đó.
        so_anh_enroll: Số ảnh dùng đăng ký mỗi người (K).
        seed: Seed gốc (R15), kết hợp với user_id để dựng bộ sinh ngẫu nhiên riêng.

    Returns:
        (ảnh_enroll_theo_người, ảnh_probe_theo_người). Người có <= K ảnh không có mặt trong
        từ điển thứ nhất; toàn bộ ảnh của họ nằm ở từ điển thứ hai.

    Raises:
        LoiCauHinh: `so_anh_enroll` < 1.
    """
    if so_anh_enroll < 1:
        raise LoiCauHinh(f"so_anh_enroll phải >= 1, nhận {so_anh_enroll}")

    enroll: dict[str, list[Path]] = {}
    probe: dict[str, list[Path]] = {}
    for user_id, danh_sach in anh_theo_nguoi.items():
        danh_sach_sap_xep = sorted(danh_sach)
        if len(danh_sach_sap_xep) <= so_anh_enroll:
            probe[user_id] = list(danh_sach_sap_xep)
            continue

        rng = random.Random(f"{seed}:{user_id}")
        chi_so_enroll = set(rng.sample(range(len(danh_sach_sap_xep)), so_anh_enroll))
        enroll[user_id] = [danh_sach_sap_xep[i] for i in sorted(chi_so_enroll)]
        probe[user_id] = [
            danh_sach_sap_xep[i] for i in range(len(danh_sach_sap_xep)) if i not in chi_so_enroll
        ]

    return enroll, probe


def dung_gallery_trong_bo_nho(
    anh_enroll: dict[str, list[Path]], backend: BoNhanDien, so_anh_enroll: int
) -> dict[str, np.ndarray]:
    """Dựng gallery bằng cách gọi enroll của backend — xem §4.4 chế độ 'chia' đặc tả, bước 5.

    Gọi phương thức enroll của backend ĐÚNG MỘT LẦN cho mỗi người. KHÔNG tự tính vectơ trung
    bình ở đây — cùng lý do đã chốt ở scripts/enroll.py: chuẩn hoá L2 trước khi trung bình là
    quyết định phương pháp đã chốt và đã có ca kiểm thử ở cả hai backend.

    Args:
        anh_enroll: Ánh xạ user_id sang danh sách ảnh dùng đăng ký người đó.
        backend: Backend nhận diện đã khởi tạo.
        so_anh_enroll: Số ảnh tối thiểu để đăng ký, truyền vào cfg của backend.

    Returns:
        Ánh xạ user_id sang vectơ đặc trưng đại diện.

    Raises:
        LoiMoHinh: enroll của backend ném ValueError dù người đó đủ ảnh.
    """
    gallery: dict[str, np.ndarray] = {}
    for user_id, danh_sach_anh in anh_enroll.items():
        anh_da_doc: list[np.ndarray] = []
        for p in danh_sach_anh:
            anh = cv2.imread(str(p))
            if anh is None:
                raise LoiMoHinh(f"Không đọc được ảnh dùng để đăng ký '{user_id}': {p}")
            anh_da_doc.append(anh)

        try:
            vec = backend.enroll(anh_da_doc, {"min_images_per_user": so_anh_enroll})
        except ValueError as e:
            raise LoiMoHinh(f"Đăng ký thất bại với '{user_id}' dù đủ ảnh: {e}") from e
        gallery[user_id] = vec

    return gallery


def do_diem_probe(
    danh_sach_probe: list[tuple[str, Path]],
    gallery: dict[str, np.ndarray],
    backend: BoNhanDien,
    so_lam_nong: int,
) -> tuple[list[dict], list[Path]]:
    """Trích đặc trưng từng probe và so với toàn bộ gallery — xem §7.1 đặc tả.

    Làm nóng bằng `so_lam_nong` probe đầu tiên trước, không loại chúng khỏi vòng đo sau đó.

    Args:
        danh_sach_probe: Danh sách (user_id_thật, đường_dẫn_ảnh).
        gallery: Ánh xạ user_id sang vectơ đặc trưng đã đăng ký.
        backend: Backend nhận diện đã khởi tạo.
        so_lam_nong: Số probe chạy làm nóng, không tính vào latency.

    Returns:
        (bản_ghi, ảnh_bị_bỏ_qua). Mỗi bản ghi gồm đủ các khoá của `_COT_CSV_THO` trừ `run_id`,
        `backend` và `tap` — nơi gọi điền ba khoá đó.

    Raises:
        LoiCauHinh: gallery rỗng.
    """
    if not gallery:
        raise LoiCauHinh("Gallery rỗng, không thể đo probe")

    for _, duong_dan in danh_sach_probe[:so_lam_nong]:
        anh = cv2.imread(str(duong_dan))
        if anh is None:
            continue
        try:
            backend.trich_dac_trung(anh)
        except ValueError as e:
            logger.debug("Làm nóng thất bại trên một ảnh, bỏ qua: %s", e)

    ban_ghi: list[dict] = []
    anh_bo_qua: list[Path] = []
    for user_id_that, duong_dan in danh_sach_probe:
        anh = cv2.imread(str(duong_dan))
        if anh is None:
            logger.warning("Không đọc được ảnh probe, bỏ qua ảnh này")
            anh_bo_qua.append(duong_dan)
            continue

        t0 = time.perf_counter()
        try:
            vec = backend.trich_dac_trung(anh)
        except ValueError as e:
            logger.warning("Không trích được đặc trưng, bỏ qua ảnh probe: %s", e)
            anh_bo_qua.append(duong_dan)
            continue
        t1 = time.perf_counter()

        top1_user: str | None = None
        top1_score = float("-inf")
        for user_id_gallery in sorted(gallery):
            diem = do_tuong_dong(vec, gallery[user_id_gallery])
            if diem > top1_score:
                top1_score = diem
                top1_user = user_id_gallery
        t2 = time.perf_counter()

        diem_dung_nguoi: float | str = ""
        if user_id_that in gallery:
            diem_dung_nguoi = do_tuong_dong(vec, gallery[user_id_that])

        latency_trich_ms = (t1 - t0) * 1000.0
        latency_so_khop_ms = (t2 - t1) * 1000.0

        ban_ghi.append(
            {
                "user_id_that": user_id_that,
                "nhan": "genuine" if user_id_that in gallery else "impostor",
                "anh_bam": bam_noi_dung(duong_dan)[:12],
                "top1_user": top1_user,
                "top1_score": top1_score,
                "diem_dung_nguoi": diem_dung_nguoi,
                "so_chieu": backend.so_chieu,
                "latency_trich_ms": latency_trich_ms,
                "latency_so_khop_ms": latency_so_khop_ms,
                "latency_identify_ms": latency_trich_ms + latency_so_khop_ms,
                "cpu_temp_c": doc_nhiet_do_cpu(),
            }
        )

    return ban_ghi, anh_bo_qua


def quet_nguong(ban_ghi: list[dict], so_buoc: int) -> list[dict]:
    """Quét ngưỡng trên lưới đều — xem §7.2 đặc tả.

    Args:
        ban_ghi: Danh sách bản ghi trả về bởi `do_diem_probe`.
        so_buoc: Số điểm chia đều trên lưới ngưỡng.

    Returns:
        Danh sách `so_buoc` dòng, đúng 17 cột của `_COT_CSV_NGUONG` (trừ `run_id`, `backend`,
        `tap` — nơi gọi điền thêm). Ngưỡng đầu bằng điểm nhỏ nhất, ngưỡng cuối bằng điểm lớn
        nhất trong `ban_ghi`.

    Raises:
        LoiCauHinh: `ban_ghi` rỗng, hoặc `so_buoc` < 2.
    """
    if not ban_ghi:
        raise LoiCauHinh("Danh sách bản ghi rỗng, không thể quét ngưỡng")
    if so_buoc < 2:
        raise LoiCauHinh(f"so_buoc phải >= 2, nhận {so_buoc}")

    diem = [r["top1_score"] for r in ban_ghi]
    diem_min = min(diem)
    diem_max = max(diem)

    genuine = [r for r in ban_ghi if r["nhan"] == "genuine"]
    impostor = [r for r in ban_ghi if r["nhan"] == "impostor"]
    so_genuine = len(genuine)
    so_impostor = len(impostor)

    bang: list[dict] = []
    for i in range(so_buoc):
        t = diem_min + (diem_max - diem_min) * i / (so_buoc - 1)

        tp = sum(1 for r in genuine if r["top1_score"] >= t and r["top1_user"] == r["user_id_that"])
        fp_nham_nguoi = sum(
            1 for r in genuine if r["top1_score"] >= t and r["top1_user"] != r["user_id_that"]
        )
        fn = sum(1 for r in genuine if r["top1_score"] < t)
        fp_impostor = sum(1 for r in impostor if r["top1_score"] >= t)
        tn = sum(1 for r in impostor if r["top1_score"] < t)

        far: float | str = (fp_impostor / so_impostor) if so_impostor > 0 else ""
        frr: float | str = (fn / so_genuine) if so_genuine > 0 else ""
        ti_le_gan_nham: float | str = (fp_nham_nguoi / so_genuine) if so_genuine > 0 else ""
        tong = so_genuine + so_impostor
        accuracy: float | str = ((tp + tn) / tong) if tong > 0 else ""
        mau_precision = tp + fp_impostor + fp_nham_nguoi
        precision: float | str = (tp / mau_precision) if mau_precision > 0 else ""
        recall: float | str = (tp / so_genuine) if so_genuine > 0 else ""

        bang.append(
            {
                "nguong": t,
                "so_genuine": so_genuine,
                "so_impostor": so_impostor,
                "tp": tp,
                "fp_impostor": fp_impostor,
                "fp_nham_nguoi": fp_nham_nguoi,
                "fn": fn,
                "tn": tn,
                "far": far,
                "frr": frr,
                "ti_le_gan_nham": ti_le_gan_nham,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
            }
        )

    return bang


def chot_diem_can_bang(bang_nguong: list[dict], far_muc_tieu: float) -> dict:
    """Chốt EER và ngưỡng tại chỉ tiêu FAR — xem §7.3 đặc tả.

    EER chỉ để SO SÁNH hai phương án, không dùng chốt ngưỡng triển khai — cách chốt chính thức
    là ấn định FAR <= `far_muc_tieu` rồi đọc FRR tương ứng.

    Args:
        bang_nguong: Bảng quét ngưỡng, trả về bởi `quet_nguong`.
        far_muc_tieu: Chỉ tiêu FAR để chốt ngưỡng, số thực trong (0, 1].

    Returns:
        Từ điển gồm `nguong_eer`, `eer`, `far_tai_eer`, `frr_tai_eer`, `nguong_far_muc_tieu`,
        `far_tai_nguong_chot`, `frr_tai_nguong_chot`, `accuracy_tai_nguong_chot`. Khi không có
        ngưỡng nào đạt, các khoá liên quan mang giá trị `None`.

    Raises:
        LoiCauHinh: `far_muc_tieu` không hữu hạn hoặc ngoài khoảng (0, 1].
    """
    if not math.isfinite(far_muc_tieu) or not (0 < far_muc_tieu <= 1):
        raise LoiCauHinh(f"far_muc_tieu phải là số hữu hạn trong (0, 1], nhận {far_muc_tieu!r}")

    ung_vien_eer = [d for d in bang_nguong if d["far"] != "" and d["frr"] != ""]
    if ung_vien_eer:
        do_lech_nho_nhat = min(abs(d["far"] - d["frr"]) for d in ung_vien_eer)
        hoa = [
            d
            for d in ung_vien_eer
            if math.isclose(abs(d["far"] - d["frr"]), do_lech_nho_nhat, abs_tol=1e-12)
        ]
        dong_eer = min(hoa, key=lambda d: d["nguong"])
        nguong_eer = dong_eer["nguong"]
        eer = (dong_eer["far"] + dong_eer["frr"]) / 2
        far_tai_eer = dong_eer["far"]
        frr_tai_eer = dong_eer["frr"]
    else:
        nguong_eer = eer = far_tai_eer = frr_tai_eer = None

    ung_vien_far = [d for d in bang_nguong if d["far"] != "" and d["far"] <= far_muc_tieu]
    if ung_vien_far:
        dong_chot = min(ung_vien_far, key=lambda d: d["nguong"])
        nguong_far_muc_tieu = dong_chot["nguong"]
        far_tai_nguong_chot = dong_chot["far"]
        frr_tai_nguong_chot = dong_chot["frr"]
        accuracy_tai_nguong_chot = dong_chot["accuracy"]
    else:
        nguong_far_muc_tieu = None
        far_tai_nguong_chot = None
        frr_tai_nguong_chot = None
        accuracy_tai_nguong_chot = None

    return {
        "nguong_eer": nguong_eer,
        "eer": eer,
        "far_tai_eer": far_tai_eer,
        "frr_tai_eer": frr_tai_eer,
        "nguong_far_muc_tieu": nguong_far_muc_tieu,
        "far_tai_nguong_chot": far_tai_nguong_chot,
        "frr_tai_nguong_chot": frr_tai_nguong_chot,
        "accuracy_tai_nguong_chot": accuracy_tai_nguong_chot,
    }


def tong_hop_toc_do(ban_ghi: list[dict]) -> dict:
    """Tổng hợp latency — xem §7.3 đặc tả.

    Args:
        ban_ghi: Danh sách bản ghi trả về bởi `do_diem_probe`.

    Returns:
        Từ điển gồm `latency_tb_ms`, `latency_do_lech_ms`, `latency_p50_ms`, `latency_p95_ms`,
        `fps_suy_ra` (tính trên cột `latency_identify_ms`).

    Raises:
        LoiCauHinh: danh sách bản ghi rỗng.
    """
    if not ban_ghi:
        raise LoiCauHinh("Danh sách bản ghi rỗng, không thể tổng hợp tốc độ")

    latency = np.array([r["latency_identify_ms"] for r in ban_ghi], dtype=np.float64)
    latency_tb = float(np.mean(latency))

    return {
        "latency_tb_ms": latency_tb,
        "latency_do_lech_ms": float(np.std(latency)),
        "latency_p50_ms": float(np.percentile(latency, 50)),
        "latency_p95_ms": float(np.percentile(latency, 95)),
        "fps_suy_ra": 1000.0 / latency_tb,
    }


def _ten_tep_ket_qua(run_id: str) -> tuple[str, str, str]:
    """Suy ba tên tệp kết quả từ run_id — dùng chung giữa `meta` và `ghi_ket_qua`."""
    return f"{run_id}.csv", f"{run_id}.nguong.csv", f"{run_id}.meta.json"


def ghi_ket_qua(
    thu_muc: Path, run_id: str, ban_ghi: list[dict], bang_nguong: list[dict], meta: dict
) -> tuple[Path, Path, Path]:
    """Ghi ĐÚNG BA tệp — xem §7.4 đặc tả.

    Args:
        thu_muc: Thư mục đích (thường là `results/`).
        run_id: Định danh lần chạy — dùng để suy tên cả ba tệp.
        ban_ghi: Bản ghi thô, mỗi phần tử một dòng của `_COT_CSV_THO`.
        bang_nguong: Bảng quét ngưỡng, mỗi phần tử một dòng của `_COT_CSV_NGUONG`.
        meta: Ngữ cảnh của lần chạy — xem `_KHOA_META_BAT_BUOC`.

    Returns:
        Tuple `(đường_dẫn_csv_thô, đường_dẫn_csv_ngưỡng, đường_dẫn_meta)`.

    Raises:
        LoiCauHinh: meta thiếu khoá bắt buộc, hoặc một trong ba tệp đích đã tồn tại.
    """
    thieu = [khoa for khoa in _KHOA_META_BAT_BUOC if khoa not in meta]
    if thieu:
        raise LoiCauHinh(f"Bản ghi meta thiếu khoá bắt buộc: {', '.join(thieu)}")

    thu_muc = Path(thu_muc)
    ten_tho, ten_nguong, ten_meta = _ten_tep_ket_qua(run_id)
    duong_dan_tho = thu_muc / ten_tho
    duong_dan_nguong = thu_muc / ten_nguong
    duong_dan_meta = thu_muc / ten_meta

    for p in (duong_dan_tho, duong_dan_nguong, duong_dan_meta):
        if p.exists():
            raise LoiCauHinh(f"Tệp kết quả đã tồn tại, từ chối ghi đè: '{p}'")

    thu_muc.mkdir(parents=True, exist_ok=True)

    with open(duong_dan_tho, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_COT_CSV_THO)
        for r in ban_ghi:
            writer.writerow([r.get(cot) for cot in _COT_CSV_THO])

    with open(duong_dan_nguong, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_COT_CSV_NGUONG)
        for r in bang_nguong:
            writer.writerow([r.get(cot) for cot in _COT_CSV_NGUONG])

    with open(duong_dan_meta, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    logger.info("Đã ghi kết quả: %s, %s, %s", duong_dan_tho, duong_dan_nguong, duong_dan_meta)
    return duong_dan_tho, duong_dan_nguong, duong_dan_meta


def _doc_so_buoc_nguong(cfg: dict) -> int:
    """Đọc `benchmark.so_buoc_nguong` — số nguyên >= 2 (§5.2 đặc tả)."""
    gia_tri = lay_gia_tri(cfg, "benchmark.so_buoc_nguong")
    hop_le = (
        isinstance(gia_tri, int)
        and not isinstance(gia_tri, bool)
        and math.isfinite(gia_tri)
        and gia_tri >= 2
    )
    if not hop_le:
        raise LoiCauHinh(
            f"Cấu hình 'benchmark.so_buoc_nguong' phải là số nguyên >= 2, nhận {gia_tri!r}"
        )
    return gia_tri


def _doc_far_muc_tieu(cfg: dict) -> float:
    """Đọc `benchmark.far_muc_tieu` — số thực hữu hạn trong (0, 1] (§5.2 đặc tả)."""
    gia_tri = lay_gia_tri(cfg, "benchmark.far_muc_tieu")
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, (int, float)):
        raise LoiCauHinh(f"Cấu hình 'benchmark.far_muc_tieu' phải là số, nhận {gia_tri!r}")
    gia_tri_float = float(gia_tri)
    if not math.isfinite(gia_tri_float) or not (0 < gia_tri_float <= 1):
        raise LoiCauHinh(
            f"Cấu hình 'benchmark.far_muc_tieu' phải là số hữu hạn trong (0, 1], "
            f"nhận {gia_tri!r}"
        )
    return gia_tri_float


def _lay_git_commit_hash() -> str:
    """Lấy commit hash hiện tại của repo, dùng cho .meta.json (R17)."""
    try:
        ket_qua = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        return ket_qua.stdout.strip()
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning("Không lấy được commit hash git: %s", e)
        return "khong-xac-dinh"


def _chay_git_status(pham_vi: tuple[str, ...]) -> bool:
    """Chạy `git status --porcelain` giới hạn theo pathspec, trả về cây có bẩn hay không."""
    lenh = ["git", "status", "--porcelain"]
    if pham_vi:
        lenh = lenh + ["--", *pham_vi]
    try:
        ket_qua = subprocess.run(
            lenh,
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        return bool(ket_qua.stdout.strip())
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning("Không kiểm tra được trạng thái git: %s", e)
        return True


def _kiem_tra_git_dirty() -> bool:
    """Kiểm mã nguồn sinh ra số đo có thay đổi nào chưa commit hay không (R17)."""
    return _chay_git_status(_DUONG_DAN_ANH_HUONG_PHEP_DO)


def _kiem_tra_git_dirty_toan_cay() -> bool:
    """Kiểm toàn bộ thư mục dự án, kể cả tệp chưa được theo dõi."""
    return _chay_git_status(())


def _xay_dung_parser() -> argparse.ArgumentParser:
    """Dựng argparse cho script, theo đúng giao diện dòng lệnh ở §5.1 đặc tả."""
    parser = argparse.ArgumentParser(
        description=(
            "Quét ngưỡng cosine similarity và đo tốc độ khối nhận diện danh tính — sinh hai "
            "tập điểm số (genuine, impostor) và bảng quét ngưỡng cho bước 3.7c/3.8 (xem "
            "docs/dac-ta/P3-05-benchmark-recognize.md)."
        )
    )
    parser.add_argument(
        "--vao", required=True, help="Thư mục ảnh probe, cấu trúc <vao>/<user_id>/*.{jpg,png}"
    )
    parser.add_argument(
        "--backend", required=True, choices=["dlib", "arcface"], help="Backend nhận diện cần đo"
    )
    parser.add_argument(
        "--tap",
        required=True,
        choices=["val", "test", "kiem-chuc-nang"],
        help="Tập đang đo — val/test bắt buộc kèm --danh-sach-impostor",
    )
    parser.add_argument("--device-name", default=None, help="Tên thiết bị đo (R8, bắt buộc)")
    parser.add_argument(
        "--che-do-gallery",
        default="tep",
        choices=["tep", "chia"],
        help="'tep': nạp gallery đã dựng sẵn; 'chia': tự chia enroll/probe từ --vao",
    )
    parser.add_argument(
        "--gallery-dir", default=None, help="Thư mục gallery (chỉ dùng ở chế độ 'tep')"
    )
    parser.add_argument(
        "--anh-da-dang-ky",
        default=None,
        help="Ghi đè thư mục ảnh đã dùng đăng ký (chỉ dùng ở chế độ 'tep')",
    )
    parser.add_argument(
        "--enroll-moi-nguoi",
        type=int,
        default=None,
        help="Số ảnh dùng đăng ký mỗi người (chỉ dùng ở chế độ 'chia')",
    )
    parser.add_argument(
        "--danh-sach-impostor",
        default=None,
        help="Tệp danh sách user_id impostor của tập đang đo",
    )
    parser.add_argument(
        "--config", default="configs/recognize.yaml", help="Đường dẫn cấu hình khối nhận diện"
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
        help="Số probe làm nóng trước vòng đo, không loại khỏi kết quả",
    )
    parser.add_argument("--seed", type=int, default=42, help="Seed phép chia enroll/probe (R15)")
    parser.add_argument("--ghi-chu", default="", help="Ghi chú tự do, vào notes của meta")
    parser.add_argument(
        "--dry-run", action="store_true", help="In kế hoạch; không dựng backend, không ghi tệp"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 thành công, 1 thất bại."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = _xay_dung_parser().parse_args(argv)

    if args.device_name is None:
        logger.error("Thiếu tham số bắt buộc --device-name")
        print("Thiếu tham số bắt buộc --device-name (R8: mọi số đo phải kèm ngữ cảnh thiết bị).")
        return 1

    try:
        cfg = nap_cau_hinh(args.config)
    except LoiCauHinh as e:
        logger.error("Không đọc được cấu hình: %s", e)
        print(f"Không đọc được cấu hình '{args.config}': {e}")
        return 1

    try:
        so_buoc_nguong = _doc_so_buoc_nguong(cfg)
        far_muc_tieu = _doc_far_muc_tieu(cfg)
    except LoiCauHinh as e:
        logger.error("Cấu hình quét ngưỡng không hợp lệ: %s", e)
        print(f"Cấu hình quét ngưỡng không hợp lệ: {e}")
        return 1

    if args.tap in ("val", "test") and not args.danh_sach_impostor:
        logger.error("Thiếu --danh-sach-impostor khi --tap=%s", args.tap)
        print(
            f"Thiếu tham số bắt buộc --danh-sach-impostor khi --tap={args.tap} (chọn ngưỡng "
            "trên tập val/test phải biết rõ danh tính impostor thuộc tập đó)."
        )
        return 1

    vao_dir = Path(args.vao)
    che_do_gallery = args.che_do_gallery

    gallery_dir: Path | None = None
    so_anh_enroll_moi_nguoi: int | None = None

    if che_do_gallery == "tep":
        if args.gallery_dir:
            gallery_dir = Path(args.gallery_dir)
        else:
            try:
                gallery_dir = Path(lay_gia_tri(cfg, "enroll.gallery_dir")) / args.backend
            except LoiCauHinh as e:
                logger.error("Không xác định được thư mục gallery mặc định: %s", e)
                print(f"Không xác định được thư mục gallery mặc định: {e}")
                return 1
    else:
        if args.enroll_moi_nguoi is not None:
            so_anh_enroll_moi_nguoi = args.enroll_moi_nguoi
        else:
            try:
                so_anh_enroll_moi_nguoi = lay_gia_tri(cfg, "enroll.min_images_per_user")
            except LoiCauHinh as e:
                logger.error("Không xác định được --enroll-moi-nguoi mặc định: %s", e)
                print(f"Không xác định được --enroll-moi-nguoi mặc định: {e}")
                return 1

    if args.dry_run:
        print("\n### BẢNG KẾ HOẠCH BENCHMARK RECOGNIZE (DRY-RUN)")
        print(f"- Thư mục vào (probe) : `{vao_dir}`")
        print(f"- Backend             : `{args.backend}`")
        print(f"- Tập                 : `{args.tap}`")
        print(f"- Chế độ gallery      : `{che_do_gallery}`")
        if che_do_gallery == "tep":
            print(f"- Thư mục gallery     : `{gallery_dir}`")
        else:
            print(f"- Số ảnh enroll/người : `{so_anh_enroll_moi_nguoi}`")
        print(f"- Danh sách impostor  : `{args.danh_sach_impostor}`")
        print(f"- Seed                : `{args.seed}`")
        print(f"- Warmup              : `{args.warmup}`\n")
        return 0

    try:
        backend = tao_bo_nhan_dien(cfg, args.backend)
    except (LoiCauHinh, LoiMoHinh) as e:
        logger.error("Không dựng được backend nhận diện: %s", e)
        print(f"Không dựng được backend nhận diện: {e}")
        return 1

    meta_gallery: dict = {}
    if che_do_gallery == "tep":
        try:
            gallery, meta_gallery, ban_ghi_manifest = nap_gallery_tu_dia(gallery_dir)
        except LoiCauHinh as e:
            logger.error("Không nạp được gallery: %s", e)
            print(f"Không nạp được gallery: {e}")
            return 1

        goc_ghi_de = Path(args.anh_da_dang_ky) if args.anh_da_dang_ky else None
        try:
            anh_da_dang_ky = suy_tap_anh_da_dang_ky(meta_gallery, ban_ghi_manifest, goc_ghi_de)
        except LoiCauHinh as e:
            logger.error("Không suy được tập ảnh đã đăng ký: %s", e)
            print(f"Không suy được tập ảnh đã đăng ký: {e}")
            return 1

        goc_dang_ky = (
            goc_ghi_de
            if goc_ghi_de is not None
            else Path(str(meta_gallery.get("duong_dan_vao", "")).replace("\\", "/"))
        )

        try:
            anh_theo_nguoi_probe = liet_ke_anh_theo_nguoi(vao_dir)
        except LoiCauHinh as e:
            logger.error("Không liệt kê được ảnh probe: %s", e)
            print(f"Không liệt kê được ảnh probe: {e}")
            return 1
    else:
        try:
            anh_theo_nguoi_nguon = liet_ke_anh_theo_nguoi(vao_dir)
        except LoiCauHinh as e:
            logger.error("Không liệt kê được ảnh nguồn: %s", e)
            print(f"Không liệt kê được ảnh nguồn: {e}")
            return 1

        anh_enroll, anh_theo_nguoi_probe = chia_enroll_probe(
            anh_theo_nguoi_nguon, so_anh_enroll_moi_nguoi, args.seed
        )
        try:
            gallery = dung_gallery_trong_bo_nho(anh_enroll, backend, so_anh_enroll_moi_nguoi)
        except LoiMoHinh as e:
            logger.error("Không dựng được gallery trong bộ nhớ: %s", e)
            print(f"Không dựng được gallery trong bộ nhớ: {e}")
            return 1

        anh_da_dang_ky = [p for ds in anh_enroll.values() for p in ds]
        goc_dang_ky = vao_dir

    danh_sach_probe_ung_vien: list[tuple[str, Path]] = [
        (uid, p) for uid, ds in anh_theo_nguoi_probe.items() for p in ds
    ]

    danh_sach_impostor: list[str] | None = None
    if args.danh_sach_impostor:
        try:
            danh_sach_impostor = doc_danh_sach_danh_tinh(Path(args.danh_sach_impostor))
        except LoiCauHinh as e:
            logger.error("Không đọc được --danh-sach-impostor: %s", e)
            print(f"Không đọc được --danh-sach-impostor: {e}")
            return 1

        trung_gallery = sorted(u for u in danh_sach_impostor if u in gallery)
        if trung_gallery:
            msg = "Danh tính impostor sau đây đang có trong gallery, không hợp lệ: " + ", ".join(
                trung_gallery
            )
            logger.error(msg)
            print(msg)
            return 1

        tap_impostor_cho_phep = set(danh_sach_impostor)
        danh_sach_probe_ung_vien = [
            (uid, p)
            for uid, p in danh_sach_probe_ung_vien
            if uid in gallery or uid in tap_impostor_cho_phep
        ]

    # ★ Điểm chịu lực (§4.1 đặc tả): loại theo MÃ BĂM NỘI DUNG, không theo đường dẫn.
    tap_bam_da_dang_ky = {bam_noi_dung(p) for p in anh_da_dang_ky}
    danh_sach_probe_sau_loc = [
        (uid, p) for uid, p in danh_sach_probe_ung_vien if bam_noi_dung(p) not in tap_bam_da_dang_ky
    ]

    so_genuine_con_lai = sum(1 for uid, _ in danh_sach_probe_sau_loc if uid in gallery)
    if so_genuine_con_lai == 0:
        msg = (
            "Không còn probe genuine nào sau khi loại ảnh đã dùng đăng ký (hoặc lọc theo "
            "--danh-sach-impostor). Kiểm lại thư mục --vao và cấu hình gallery."
        )
        logger.error(msg)
        print(msg)
        return 1

    thoi_diem_bat_dau_do = time.perf_counter()
    nhiet_do_bat_dau = doc_nhiet_do_cpu()

    try:
        ban_ghi, anh_bo_qua = do_diem_probe(danh_sach_probe_sau_loc, gallery, backend, args.warmup)
    except LoiCauHinh as e:
        logger.error("Không đo được điểm số probe: %s", e)
        print(f"Không đo được điểm số probe: {e}")
        return 1

    thoi_gian_chay = time.perf_counter() - thoi_diem_bat_dau_do

    tap_bo_qua = set(anh_bo_qua)
    anh_do_duoc = [p for _, p in danh_sach_probe_sau_loc if p not in tap_bo_qua]
    bam_danh_sach_anh_probe = bam_danh_sach_tep(anh_do_duoc, vao_dir) if anh_do_duoc else ""
    bam_danh_sach_anh_da_dang_ky = (
        bam_danh_sach_tep(anh_da_dang_ky, goc_dang_ky) if anh_da_dang_ky else ""
    )

    thoi_diem = datetime.datetime.now().astimezone()
    run_id = f"bench_recognize_{args.backend}_{thoi_diem.strftime('%Y%m%d_%H%M')}"
    for r in ban_ghi:
        r["run_id"] = run_id
        r["backend"] = args.backend
        r["tap"] = args.tap

    so_probe_genuine = sum(1 for r in ban_ghi if r["nhan"] == "genuine")
    so_probe_impostor = len(ban_ghi) - so_probe_genuine
    so_danh_tinh_impostor = len({r["user_id_that"] for r in ban_ghi if r["nhan"] == "impostor"})

    canh_bao: dict[str, str] = {}
    ghi_chu_bo_sung: list[str] = []

    moi_truong = xac_dinh_moi_truong()
    if moi_truong != _MOI_TRUONG_PHAN_CUNG_DICH:
        thong_bao = (
            f"CẢNH BÁO: phép đo chạy ở môi trường '{moi_truong}', không phải môi trường đích "
            f"'{_MOI_TRUONG_PHAN_CUNG_DICH}' (Raspberry Pi 5 thật). Số liệu này KHÔNG dùng kết "
            "luận chỉ tiêu độ chính xác nhận diện của Cổng C Phase 3."
        )
        canh_bao["canh_bao_hieu_nang"] = thong_bao
        ghi_chu_bo_sung.append(thong_bao)

    if len(ban_ghi) < SO_MAU_TOI_THIEU or so_probe_genuine < SO_MAU_TOI_THIEU:
        thong_bao = (
            f"Cỡ mẫu nhỏ: tổng {len(ban_ghi)} probe (genuine {so_probe_genuine}), dưới mức "
            f"tối thiểu {SO_MAU_TOI_THIEU} mẫu (R9). Số liệu chỉ dùng kiểm chức năng."
        )
        canh_bao["canh_bao_co_mau"] = thong_bao
        ghi_chu_bo_sung.append(thong_bao)

    if anh_bo_qua:
        thong_bao = (
            f"{len(anh_bo_qua)} ảnh probe bị bỏ qua vì không đọc được hoặc trích đặc trưng "
            "thất bại."
        )
        canh_bao["canh_bao_anh_bo_qua"] = thong_bao
        ghi_chu_bo_sung.append(thong_bao)

    if args.tap == "kiem-chuc-nang":
        thong_bao = (
            "CẢNH BÁO: --tap=kiem-chuc-nang — lượt đo này KHÔNG dùng danh sách impostor tách "
            "theo val/test, chỉ phục vụ kiểm chức năng, không dùng số liệu này chốt ngưỡng "
            "chính thức."
        )
        canh_bao["canh_bao_chia_tap"] = thong_bao
        ghi_chu_bo_sung.append(thong_bao)

    if args.ghi_chu:
        ghi_chu_bo_sung.append(args.ghi_chu)

    notes = " ".join(ghi_chu_bo_sung)

    try:
        bang_nguong_tho = quet_nguong(ban_ghi, so_buoc_nguong)
    except LoiCauHinh as e:
        logger.error("Không quét được ngưỡng: %s", e)
        print(f"Không quét được ngưỡng: {e}")
        return 1

    for r in bang_nguong_tho:
        r["run_id"] = run_id
        r["backend"] = args.backend
        r["tap"] = args.tap

    ket_qua_can_bang = chot_diem_can_bang(bang_nguong_tho, far_muc_tieu)
    ket_qua_toc_do = tong_hop_toc_do(ban_ghi)

    cac_nhiet_do = [r["cpu_temp_c"] for r in ban_ghi if r["cpu_temp_c"] is not None]
    if nhiet_do_bat_dau is not None:
        cac_nhiet_do.append(nhiet_do_bat_dau)
    nhiet_do_max = max(cac_nhiet_do) if cac_nhiet_do else None

    try:
        phien_ban_dlib_bin = importlib.metadata.version("dlib-bin")
    except importlib.metadata.PackageNotFoundError as e:
        logger.warning("Không tra được phiên bản gói 'dlib-bin': %s", e)
        phien_ban_dlib_bin = "khong-xac-dinh"

    meta_dataset = {
        "che_do_gallery": che_do_gallery,
        "gallery_dir": str(gallery_dir) if che_do_gallery == "tep" else None,
        "gallery_commit": meta_gallery.get("commit") if che_do_gallery == "tep" else None,
        "gallery_git_dirty": meta_gallery.get("git_dirty") if che_do_gallery == "tep" else None,
        "gallery_so_nguoi_da_dang_ky": (
            meta_gallery.get("so_nguoi_da_dang_ky") if che_do_gallery == "tep" else None
        ),
        "gallery_min_images_per_user_da_dung": (
            meta_gallery.get("min_images_per_user_da_dung") if che_do_gallery == "tep" else None
        ),
        "so_anh_enroll_moi_nguoi": so_anh_enroll_moi_nguoi if che_do_gallery == "chia" else None,
        "anh_dir": str(vao_dir),
        "tep_danh_sach_impostor": args.danh_sach_impostor,
        "so_nguoi_gallery": len(gallery),
        "so_anh_da_dang_ky": len(anh_da_dang_ky),
        "bam_danh_sach_anh_da_dang_ky": bam_danh_sach_anh_da_dang_ky,
        "so_anh_probe": len(ban_ghi),
        "so_anh_bo_qua": len(anh_bo_qua),
        "so_danh_tinh_impostor": so_danh_tinh_impostor,
        "bam_danh_sach_anh_probe": bam_danh_sach_anh_probe,
    }

    tom_tat = {
        **ket_qua_can_bang,
        **ket_qua_toc_do,
        "so_nguoi_gallery": len(gallery),
        "so_probe_genuine": so_probe_genuine,
        "so_probe_impostor": so_probe_impostor,
        "far_muc_tieu": far_muc_tieu,
    }

    argv_hien_thi = argv if argv is not None else sys.argv[1:]
    ten_tho, ten_nguong, ten_meta = _ten_tep_ket_qua(run_id)

    meta: dict = {
        "run_id": run_id,
        "timestamp": thoi_diem.isoformat(),
        "git_commit": _lay_git_commit_hash(),
        "git_dirty": _kiem_tra_git_dirty(),
        "git_dirty_toan_cay": _kiem_tra_git_dirty_toan_cay(),
        "script": "scripts/benchmark_recognize.py",
        "command": "python scripts/benchmark_recognize.py " + " ".join(argv_hien_thi),
        "device": {
            "name": args.device_name,
            "os": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "moi_truong": moi_truong,
        "software": {
            "python": platform.python_version(),
            "onnxruntime": ort.__version__,
            "opencv-python": cv2.__version__,
            "numpy": np.__version__,
            "dlib-bin": phien_ban_dlib_bin,
        },
        "config_file": args.config,
        "config_snapshot": cfg,
        "backend": args.backend,
        "tap": args.tap,
        "dataset": meta_dataset,
        "seed": args.seed,
        "warmup_probes": args.warmup,
        "cpu_temp_start_c": nhiet_do_bat_dau,
        "cpu_temp_max_c": nhiet_do_max,
        "duration_s": thoi_gian_chay,
        "notes": notes,
        "tep_ket_qua": {"tho": ten_tho, "nguong": ten_nguong, "meta": ten_meta},
        "tom_tat": tom_tat,
    }
    meta.update(canh_bao)

    try:
        duong_dan_tho, duong_dan_nguong, duong_dan_meta = ghi_ket_qua(
            _THU_MUC_KET_QUA_MAC_DINH, run_id, ban_ghi, bang_nguong_tho, meta
        )
    except LoiCauHinh as e:
        logger.error("Không ghi được kết quả: %s", e)
        print(f"Không ghi được kết quả: {e}")
        return 1

    print("\n### BẢNG TỔNG KẾT BENCHMARK RECOGNIZE")
    print(f"- Backend             : `{args.backend}` — tập `{args.tap}`")
    print(f"- Số người gallery    : `{len(gallery)}`")
    print(f"- Probe genuine       : `{so_probe_genuine}` — impostor: `{so_probe_impostor}`")

    nguong_eer = ket_qua_can_bang["nguong_eer"]
    if nguong_eer is not None:
        print(f"- Ngưỡng EER          : `{nguong_eer:.4f}` (EER = `{ket_qua_can_bang['eer']:.4f}`)")
    else:
        print("- Ngưỡng EER          : không xác định được trên tập này")
    print(
        "  ⚠️ EER chỉ để so sánh hai phương án, KHÔNG dùng chốt ngưỡng triển khai "
        "(configs/recognize.yaml đã chốt cách chọn ngưỡng theo FAR)."
    )

    nguong_far = ket_qua_can_bang["nguong_far_muc_tieu"]
    if nguong_far is not None:
        print(
            f"- Ngưỡng theo FAR<={far_muc_tieu:.2%}: `{nguong_far:.4f}` "
            f"(FAR=`{ket_qua_can_bang['far_tai_nguong_chot']:.4f}`, "
            f"FRR=`{ket_qua_can_bang['frr_tai_nguong_chot']:.4f}`, "
            f"accuracy=`{ket_qua_can_bang['accuracy_tai_nguong_chot']:.4f}`)"
        )
    else:
        print(f"- Không có ngưỡng nào đạt FAR <= {far_muc_tieu:.2%} trên tập này")

    print(
        f"- Latency p50/p95 (ms): `{ket_qua_toc_do['latency_p50_ms']:.2f}` / "
        f"`{ket_qua_toc_do['latency_p95_ms']:.2f}` — FPS suy ra: `{ket_qua_toc_do['fps_suy_ra']:.2f}`"
    )
    print(f"- Tệp kết quả         : `{duong_dan_tho}`, `{duong_dan_nguong}`, `{duong_dan_meta}`")
    print(
        "\n⚠️ Kết luận chỉ tiêu độ chính xác nhận diện chỉ có giá trị với gallery người nhà đo "
        "trên Raspberry Pi 5 thật — xem docs/dac-ta/P3-05-benchmark-recognize.md §1.\n"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
