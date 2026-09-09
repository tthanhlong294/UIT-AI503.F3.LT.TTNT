"""Đo hiệu năng khối phát hiện khuôn mặt YOLOv8n-face — bước 2.6 của CLAUDE.md.

Xem docs/dac-ta/P2-03-benchmark-detect.md và docs/dac-ta/P2-06-benchmark-ncnn.md. Script này là
CÔNG CỤ, không phải phép đo: chỉ khi chạy trên Raspberry Pi 5 thật thì số đo mới có giá trị đưa
vào Cổng C của Phase 2 (xem chốt chặn container ở dưới và experiment-protocol.instructions.md §2).

Ma trận đo: {mô hình được liệt kê ở --models} × {số luồng ở --threads}. Mỗi mô hình là một tệp
.onnx hoặc một thư mục mô hình NCNN; việc đường dẫn nào đi với bộ suy luận nào do
src/detector/factory.py quyết định — script này KHÔNG tự đoán lại. Cùng một tập ảnh đã nạp sẵn
được dùng lại cho MỌI ô của ma trận để bảo đảm so sánh công bằng (chỉ đổi đúng một biến mỗi lần
— xem experiment-protocol.instructions.md §2 "Quy tắc so sánh công bằng").
"""

import sys
from pathlib import Path

# Thêm gốc dự án vào sys.path để cho phép chạy trực tiếp kịch bản
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import csv
import datetime
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

from scripts.export_detector_ncnn import xac_dinh_moi_truong
from src.capture import BoThuHinh, tao_bo_thu_hinh
from src.common.config import nap_cau_hinh
from src.common.exceptions import LoiCamera, LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger
from src.detector import factory as detector_factory
from src.detector import tao_bo_phat_hien

logger = lay_logger(__name__)

# --- Ngưỡng chỉ tiêu — KHÔNG phải số tự chọn, dẫn nguồn tường minh ---
# Chỉ tiêu chặn Cổng C của Phase 2 (CLAUDE.md §1: "FPS riêng module detect >= 10 FPS").
NGUONG_FPS_TOI_THIEU = 10.0

# R9 (.claude/instructions/experiment-protocol.instructions.md §6): mỗi lần đo FPS/latency
# tối thiểu 100 khung hình sau warm-up.
SO_FRAME_TOI_THIEU = 100

# Đuôi tệp được coi là ảnh khi quét thư mục nguồn.
_DINH_DANG_ANH_HOP_LE = {".jpg", ".jpeg", ".png"}

# Đường dẫn cảm biến nhiệt độ / cờ container — đặt thành hằng số module để ca kiểm thử
# monkeypatch được, không phải gọi thẳng đường dẫn tuyệt đối trong thân hàm.
_DUONG_DAN_NHIET_DO_CPU = Path("/sys/class/thermal/thermal_zone0/temp")
_DUONG_DAN_DOCKERENV = Path("/.dockerenv")

# Thư mục ghi kết quả mặc định — hằng số module để ca kiểm thử monkeypatch ra tmp_path,
# không ghi vào results/ thật khi chạy pytest.
_THU_MUC_KET_QUA_MAC_DINH = Path("results")

# Giá trị mặc định của --anh-dir và --seed (chỉ chế độ dia). Đặt thành hằng số module vì
# `default` của hai cờ này phải là None để phân biệt "người dùng gõ" với "argparse điền hộ"
# (P2-07 §5.1); main() phân giải None về đúng hai giá trị dưới đây trước khi dùng.
_ANH_DIR_MAC_DINH = "data/impostor/lfw_original"
_SEED_MAC_DINH = 42

# Ngưỡng nghi ngờ bộ đệm khung của lớp thu hình (P2-07 §4.1, §5.6): một khung lấy về dưới
# một mili-giây không thể đến từ cảm biến webcam thật; nếu đồng thời thời gian suy luận lớn
# hơn thời gian lấy khung nhiều lần thì khung trả về có thể là khung cũ trong bộ đệm.
_NGUONG_NGHI_NGO_DEM_KHUNG_MS = 1.0
_HE_SO_NGHI_NGO_DEM_KHUNG = 10.0

# Đường dẫn ảnh hưởng tới kết quả đo — thay đổi ở đây làm số đo khác đi.
# `results/` KHÔNG nằm trong danh sách: tệp kết quả là sản phẩm của phép đo,
# không phải đầu vào của nó (P2-06c §2).
_DUONG_DAN_ANH_HUONG_PHEP_DO = (
    "src",
    "scripts",
    "configs",
    "requirements.txt",
    "requirements-dev.txt",
)

# Mã môi trường của phần cứng đích (xem experiment-protocol.instructions.md §2). Chỉ số đo sinh
# ra ở môi trường này mới dùng để kết luận chỉ tiêu FPS của Cổng C Phase 2.
_MOI_TRUONG_PHAN_CUNG_DICH = "pi5"

# Câu cảnh báo ghi kèm vào notes của .meta.json khi phép đo KHÔNG chạy trên phần cứng đích.
# Cảnh báo in ra màn hình biến mất khi đóng cửa sổ; câu này đi cùng số liệu suốt đời tệp đó
# (P2-06 §6.3). Chỗ {} điền mã môi trường thật đã đo.
_CANH_BAO_NGOAI_PHAN_CUNG_DICH = (
    "CẢNH BÁO: phép đo chạy ở môi trường '{}', KHÔNG phải Raspberry Pi 5 thật. Số liệu này "
    "chỉ dùng để kiểm quy trình đo và so sánh tương đối giữa các cấu hình, KHÔNG dùng kết "
    f"luận chỉ tiêu >= {NGUONG_FPS_TOI_THIEU:.0f} FPS của Cổng C Phase 2."
)

_COT_CSV = [
    "run_id",
    "backend",
    "imgsz",
    "threads",
    "sample_idx",
    "latency_ms",
    "fps_instant",
    "n_faces",
    "conf_top",
    "cpu_temp_c",
]

# Lược đồ CSV của chế độ camera — 13 cột (P2-07 §7). KHÁC _COT_CSV: thêm ba cột thời gian
# `latency_lay_khung_ms`, `latency_tong_ms`, `fps_tong_instant`. Số cột khác nhau (13 so với
# 10) là hàng rào thứ ba chống trộn nhầm hai loại số bước 2.5 và 2.6 (P2-07 §7).
_COT_CSV_CAMERA = [
    "run_id",
    "backend",
    "imgsz",
    "threads",
    "sample_idx",
    "latency_lay_khung_ms",
    "latency_ms",
    "latency_tong_ms",
    "fps_instant",
    "fps_tong_instant",
    "n_faces",
    "conf_top",
    "cpu_temp_c",
]

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
    "dataset",
    "seed",
    "warmup_frames",
    "cpu_temp_start_c",
    "cpu_temp_max_c",
    "duration_s",
    "notes",
    "tom_tat",
)

# Danh sách khoá bắt buộc riêng cho chế độ camera — 24 khoá (P2-07 §5.5). KHÔNG thêm khoá
# vào _KHOA_META_BAT_BUOC: tám ca kiểm thử hiện có dựng meta bằng tay cho chế độ dia, thêm
# khoá vào danh sách gốc là đổi hành vi chế độ dia (P2-07 §6, chốt B3).
_KHOA_META_BAT_BUOC_CAMERA = _KHOA_META_BAT_BUOC + (
    "nguon",
    "conditions",
    "config_file_capture",
    "config_snapshot_capture",
)


def doc_nhiet_do_cpu() -> float | None:
    """Đọc nhiệt độ CPU hiện tại, đơn vị độ C.

    Trên Linux/Raspberry Pi đọc từ /sys/class/thermal/thermal_zone0/temp (milli-độ C).

    Returns:
        Nhiệt độ theo độ C, hoặc None trên máy không có cảm biến (Windows, macOS) —
        KHÔNG ném ngoại lệ trong trường hợp đó.
    """
    try:
        noi_dung = _DUONG_DAN_NHIET_DO_CPU.read_text(encoding="utf-8").strip()
        return float(noi_dung) / 1000.0
    except (OSError, ValueError) as e:
        logger.debug("Không đọc được nhiệt độ CPU: %s", e)
        return None


def dang_trong_container() -> bool:
    """Nhận biết đang chạy trong container hay không.

    Returns:
        True nếu tệp /.dockerenv tồn tại (dấu hiệu chuẩn của container Docker).
    """
    return _DUONG_DAN_DOCKERENV.exists()


def chon_anh(thu_muc: Path, so_luong: int, seed: int) -> list[Path]:
    """Chọn ngẫu nhiên có tái lập một tập ảnh từ thư mục nguồn.

    Args:
        thu_muc: Thư mục gốc chứa ảnh (quét đệ quy).
        so_luong: Số ảnh cần chọn.
        seed: Seed cho bộ sinh ngẫu nhiên cục bộ, đảm bảo tái lập được (R15).

    Returns:
        Danh sách đường dẫn ảnh đã chọn, đã sắp xếp.

    Raises:
        LoiCauHinh: thư mục không tồn tại, rỗng, hoặc không đủ ảnh.
    """
    thu_muc = Path(thu_muc)
    if not thu_muc.exists() or not thu_muc.is_dir():
        raise LoiCauHinh(f"Thư mục ảnh không tồn tại: '{thu_muc}'")

    danh_sach = sorted(
        p for p in thu_muc.rglob("*") if p.is_file() and p.suffix.lower() in _DINH_DANG_ANH_HOP_LE
    )
    if not danh_sach:
        raise LoiCauHinh(f"Thư mục ảnh '{thu_muc}' rỗng, không có ảnh hợp lệ nào")

    if len(danh_sach) < so_luong:
        raise LoiCauHinh(f"Không đủ ảnh trong '{thu_muc}': có {len(danh_sach)}, cần {so_luong}")

    rng = random.Random(seed)
    return sorted(rng.sample(danh_sach, so_luong))


def do_mot_cau_hinh(
    duong_dan_mo_hinh: Path,
    cfg: dict,
    so_luong: int,
    anh_da_nap: list[np.ndarray],
    so_lam_nong: int,
) -> list[dict]:
    """Đo một ô của ma trận benchmark (một mô hình tại một mức số luồng).

    Ảnh phải được truyền vào ĐÃ NẠP SẴN vào bộ nhớ — thời gian đọc tệp không được tính vào
    phép đo (§3 đặc tả P2-03). Vùng đo thời gian chỉ bọc lệnh gọi `detector.detect`.

    Mô hình được nạp ĐÚNG MỘT LẦN cho mỗi ô, tại đây và chỉ tại đây (P2-06 §6.2).

    Mỗi bản ghi trả về có thêm hai khoá so với trước: `backend` và `imgsz`, lấy từ chính đối
    tượng phát hiện — KHÔNG suy từ tên tệp, và không để hàm gọi gán sau (P2-06 §6.1).

    Args:
        duong_dan_mo_hinh: Đường dẫn mô hình cần đo. Dạng nào đi với bộ suy luận nào là việc
            của `tao_bo_phat_hien`, hàm này không xét đến.
        cfg: Cấu hình truyền cho bộ phát hiện (đã đặt sẵn inference.num_threads).
        so_luong: Số khung hình cần đo (không tính khung làm nóng).
        anh_da_nap: Ảnh đã nạp sẵn vào bộ nhớ, độ dài tối thiểu `so_lam_nong + so_luong`.
            `so_lam_nong` ảnh đầu dùng để làm nóng, phần còn lại dùng để đo.
        so_lam_nong: Số khung hình chạy làm nóng trước, không tính vào kết quả.

    Returns:
        Danh sách bản ghi, mỗi khung hình đo một bản ghi, gồm các khoá `backend`, `imgsz`,
        `sample_idx`, `latency_ms`, `fps_instant`, `n_faces`, `conf_top`, `cpu_temp_c`.

    Raises:
        LoiMoHinh: không nạp được mô hình.
        LoiCauHinh: cấu hình sai, đường dẫn không khớp bộ suy luận nào, hoặc không đủ ảnh đã
            nạp sẵn cho warm-up + đo.
    """
    tong_can = so_lam_nong + so_luong
    if len(anh_da_nap) < tong_can:
        raise LoiCauHinh(
            f"Cần ít nhất {tong_can} ảnh đã nạp sẵn (làm nóng {so_lam_nong} + đo {so_luong}), "
            f"chỉ có {len(anh_da_nap)}"
        )

    detector = tao_bo_phat_hien(duong_dan_mo_hinh, cfg)
    ten_backend = detector.ten_backend
    imgsz = detector.kich_thuoc_vao

    for anh in anh_da_nap[:so_lam_nong]:
        detector.detect(anh)

    ban_ghi: list[dict] = []
    for idx, anh in enumerate(anh_da_nap[so_lam_nong:tong_can]):
        bat_dau = time.perf_counter()
        khuon_mat = detector.detect(anh)
        ket_thuc = time.perf_counter()

        latency_ms = (ket_thuc - bat_dau) * 1000.0
        # Đọc nhiệt độ SAU khi kết thúc phép đo — không để chi phí đọc /sys lọt vào latency.
        ban_ghi.append(
            {
                "backend": ten_backend,
                "imgsz": imgsz,
                "sample_idx": idx,
                "latency_ms": latency_ms,
                "fps_instant": 1000.0 / latency_ms,
                "n_faces": len(khuon_mat),
                "conf_top": khuon_mat[0].confidence if khuon_mat else None,
                "cpu_temp_c": doc_nhiet_do_cpu(),
            }
        )

    return ban_ghi


def _lay_phien_ban_ncnn() -> str:
    """Tra phiên bản gói `ncnn` đã cài, dùng cho khối `software` của `.meta.json`.

    Không tự bắt lỗi ở đây — nơi gọi (`main`) chịu trách nhiệm không để một lượt đo dài
    hỏng chỉ vì thiếu một dòng metadata (P2-06b §4.2).

    Returns:
        Chuỗi phiên bản gói `ncnn`.

    Raises:
        importlib.metadata.PackageNotFoundError: gói `ncnn` chưa được cài trên máy này.
    """
    return importlib.metadata.version("ncnn")


def tong_hop(ban_ghi: list[dict]) -> dict:
    """Tổng hợp số đo của một ô của ma trận.

    Args:
        ban_ghi: Danh sách bản ghi trả về bởi `do_mot_cau_hinh`.

    Returns:
        Từ điển gồm `n_frames`, `latency_tb`, `latency_do_lech`, `latency_p50`,
        `latency_p95`, `fps_tb`, `ti_le_phat_hien`, `dat_chi_tieu`.
        `dat_chi_tieu` là True khi `fps_tb >= NGUONG_FPS_TOI_THIEU`.

    Raises:
        LoiCauHinh: danh sách bản ghi rỗng.
    """
    if not ban_ghi:
        raise LoiCauHinh("Danh sách bản ghi rỗng, không thể tổng hợp")

    do_tre = np.array([r["latency_ms"] for r in ban_ghi], dtype=np.float64)
    n_frames = len(ban_ghi)
    latency_tb = float(np.mean(do_tre))
    fps_tb = 1000.0 / latency_tb
    so_phat_hien = sum(1 for r in ban_ghi if r["n_faces"] >= 1)

    return {
        "n_frames": n_frames,
        "latency_tb": latency_tb,
        "latency_do_lech": float(np.std(do_tre)),
        "latency_p50": float(np.percentile(do_tre, 50)),
        "latency_p95": float(np.percentile(do_tre, 95)),
        "fps_tb": fps_tb,
        "ti_le_phat_hien": so_phat_hien / n_frames,
        "dat_chi_tieu": fps_tb >= NGUONG_FPS_TOI_THIEU,
    }


def do_mot_cau_hinh_camera(
    duong_dan_mo_hinh: Path,
    cfg: dict,
    bo_thu_hinh: BoThuHinh,
    so_luong: int,
    so_lam_nong: int,
) -> list[dict]:
    """Đo một cấu hình với khung hình lấy trực tiếp từ bộ thu hình ĐÃ MỞ.

    Args:
        duong_dan_mo_hinh: Đường dẫn mô hình cần đo.
        cfg: Cấu hình phát hiện (đã đặt sẵn inference.num_threads).
        bo_thu_hinh: Bộ thu hình **đã gọi `mo()`**. Hàm này KHÔNG mở và KHÔNG đóng nó.
        so_luong: Số khung hình cần đo (không tính khung làm nóng).
        so_lam_nong: Số khung chạy làm nóng trước, không ghi bản ghi.

    Returns:
        Danh sách bản ghi, mỗi khung một bản ghi, gồm các khoá `backend`, `imgsz`,
        `sample_idx`, `latency_lay_khung_ms`, `latency_ms`, `latency_tong_ms`,
        `fps_instant`, `fps_tong_instant`, `n_faces`, `conf_top`, `cpu_temp_c`.

    Raises:
        LoiMoHinh: không nạp được mô hình.
        LoiCauHinh: cấu hình sai, hoặc `so_luong` < 1.
        LoiCamera: bộ thu hình chưa mở, hoặc đọc khung thất bại — KHÔNG bắt tại đây.
    """
    if so_luong < 1:
        raise LoiCauHinh(f"so_luong phải >= 1, nhận được {so_luong}")

    detector = tao_bo_phat_hien(duong_dan_mo_hinh, cfg)
    ten_backend = detector.ten_backend
    imgsz = detector.kich_thuoc_vao

    for _ in range(so_lam_nong):
        khung_hinh = bo_thu_hinh.doc_frame()
        detector.detect(khung_hinh)

    ban_ghi: list[dict] = []
    for idx in range(so_luong):
        # Hai vùng bấm giờ TÁCH RỜI (P2-07 §4.1): t0->t1 ôm đúng lấy khung, t1->t2 ôm đúng
        # suy luận. latency_tong_ms là phép CỘNG số học, không phải cặp perf_counter thứ ba.
        t0 = time.perf_counter()
        khung_hinh = bo_thu_hinh.doc_frame()
        t1 = time.perf_counter()
        khuon_mat = detector.detect(khung_hinh)
        t2 = time.perf_counter()

        latency_lay_khung_ms = (t1 - t0) * 1000.0
        latency_ms = (t2 - t1) * 1000.0
        latency_tong_ms = latency_lay_khung_ms + latency_ms
        # Đọc nhiệt độ SAU khi kết thúc cả hai vùng bấm giờ — giữ đúng tiền lệ chế độ dia.
        ban_ghi.append(
            {
                "backend": ten_backend,
                "imgsz": imgsz,
                "sample_idx": idx,
                "latency_lay_khung_ms": latency_lay_khung_ms,
                "latency_ms": latency_ms,
                "latency_tong_ms": latency_tong_ms,
                "fps_instant": 1000.0 / latency_ms,
                "fps_tong_instant": 1000.0 / latency_tong_ms,
                "n_faces": len(khuon_mat),
                "conf_top": khuon_mat[0].confidence if khuon_mat else None,
                "cpu_temp_c": doc_nhiet_do_cpu(),
            }
        )

    return ban_ghi


def tong_hop_camera(ban_ghi: list[dict]) -> dict:
    """Tổng hợp phần số liệu riêng của chế độ camera.

    Args:
        ban_ghi: Danh sách bản ghi trả về bởi `do_mot_cau_hinh_camera`.

    Returns:
        Từ điển gồm `lay_khung_tb`, `lay_khung_do_lech`, `lay_khung_p50`, `lay_khung_p95`,
        `tong_tb`, `tong_do_lech`, `tong_p50`, `tong_p95`, `fps_tong_tb`,
        `dat_chi_tieu_tong`. Không khoá nào trùng với `tong_hop`.

    Raises:
        LoiCauHinh: danh sách bản ghi rỗng.
    """
    if not ban_ghi:
        raise LoiCauHinh("Danh sách bản ghi rỗng, không thể tổng hợp")

    lay_khung = np.array([r["latency_lay_khung_ms"] for r in ban_ghi], dtype=np.float64)
    tong = np.array([r["latency_tong_ms"] for r in ban_ghi], dtype=np.float64)
    tong_tb = float(np.mean(tong))
    fps_tong_tb = 1000.0 / tong_tb

    return {
        "lay_khung_tb": float(np.mean(lay_khung)),
        "lay_khung_do_lech": float(np.std(lay_khung)),
        "lay_khung_p50": float(np.percentile(lay_khung, 50)),
        "lay_khung_p95": float(np.percentile(lay_khung, 95)),
        "tong_tb": tong_tb,
        "tong_do_lech": float(np.std(tong)),
        "tong_p50": float(np.percentile(tong, 50)),
        "tong_p95": float(np.percentile(tong, 95)),
        "fps_tong_tb": fps_tong_tb,
        "dat_chi_tieu_tong": fps_tong_tb >= NGUONG_FPS_TOI_THIEU,
    }


def mo_ta_nguon_camera(cfg_capture: dict, backend_thu_hinh: str, khung_mau: np.ndarray) -> dict:
    """Dựng khối `meta.dataset` cho chế độ camera — xem P2-07 §5.4, đủ tám khoá.

    Args:
        cfg_capture: Cấu hình thu hình đã nạp, đã ghi đè khoá `backend`.
        backend_thu_hinh: Giá trị `--capture-backend`, một trong `{"opencv", "mock"}`.
        khung_mau: Một khung hình thật đã lấy về — độ phân giải thật đọc từ `.shape` của
            khung này, TUYỆT ĐỐI không từ cấu hình (webcam có thể từ chối `cap.set()` im lặng).

    Returns:
        Từ điển tám khoá: `backend_thu_hinh`, `do_phan_giai_yeu_cau`, `do_phan_giai_that`,
        `khop_do_phan_giai`, `fps_khai_bao_trong_cau_hinh`, `warmup_frames_thu_hinh`,
        `n_frame_do`, `n_frame_lam_nong`. Hai khoá cuối trả về `None`, nơi gọi điền lại
        bằng số dòng CSV thật và giá trị `--warmup`.

    Raises:
        LoiCauHinh: `backend_thu_hinh` không thuộc {"opencv", "mock"}, hoặc thiếu nhánh
            cấu hình tương ứng.
    """
    if backend_thu_hinh not in ("opencv", "mock"):
        raise LoiCauHinh(
            f"backend_thu_hinh phải là 'opencv' hoặc 'mock', nhận được {backend_thu_hinh!r}"
        )

    nhanh = cfg_capture.get(backend_thu_hinh)
    if not isinstance(nhanh, dict):
        raise LoiCauHinh(
            f"Cấu hình thu hình thiếu nhánh '{backend_thu_hinh}' (cần dict, "
            f"nhận {type(nhanh).__name__})"
        )

    do_phan_giai_yeu_cau = f"{nhanh.get('width')}x{nhanh.get('height')}"
    do_phan_giai_that = f"{khung_mau.shape[1]}x{khung_mau.shape[0]}"

    if backend_thu_hinh == "opencv":
        fps_khai_bao = nhanh.get("fps")
        warmup_thu_hinh = nhanh.get("warmup_frames")
    else:
        # backend mock không có tốc độ khung hay warmup của camera thật.
        fps_khai_bao = None
        warmup_thu_hinh = None

    return {
        "backend_thu_hinh": backend_thu_hinh,
        "do_phan_giai_yeu_cau": do_phan_giai_yeu_cau,
        "do_phan_giai_that": do_phan_giai_that,
        "khop_do_phan_giai": do_phan_giai_yeu_cau == do_phan_giai_that,
        "fps_khai_bao_trong_cau_hinh": fps_khai_bao,
        "warmup_frames_thu_hinh": warmup_thu_hinh,
        "n_frame_do": None,
        "n_frame_lam_nong": None,
    }


def ghi_ket_qua(
    thu_muc: Path,
    run_id: str,
    ban_ghi: list[dict],
    meta: dict,
    cot: list[str] | None = None,
    khoa_bat_buoc: tuple[str, ...] | None = None,
) -> tuple[Path, Path]:
    """Ghi ĐÚNG HAI tệp kết quả: dữ liệu thô .csv và ngữ cảnh .meta.json.

    Args:
        thu_muc: Thư mục đích (thường là `results/`).
        run_id: Định danh lần chạy, dùng làm tên tệp: `<run_id>.csv`, `<run_id>.meta.json`.
        ban_ghi: Danh sách bản ghi thô, mỗi phần tử là một dòng CSV.
        meta: Ngữ cảnh của lần chạy.
        cot: Danh sách cột CSV. `None` ⇒ `_COT_CSV` (mười cột, chế độ dia).
        khoa_bat_buoc: Danh sách khoá meta bắt buộc. `None` ⇒ `_KHOA_META_BAT_BUOC` (20 khoá).

    Returns:
        Tuple `(đường_dẫn_csv, đường_dẫn_meta)`.

    Raises:
        LoiCauHinh: meta thiếu khoá bắt buộc.
    """
    cot = cot if cot is not None else _COT_CSV
    khoa_bat_buoc = khoa_bat_buoc if khoa_bat_buoc is not None else _KHOA_META_BAT_BUOC

    thieu = [khoa for khoa in khoa_bat_buoc if khoa not in meta]
    if thieu:
        raise LoiCauHinh(f"Bản ghi meta thiếu khoá bắt buộc: {', '.join(thieu)}")

    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)

    duong_dan_csv = thu_muc / f"{run_id}.csv"
    duong_dan_meta = thu_muc / f"{run_id}.meta.json"

    with open(duong_dan_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cot)
        for r in ban_ghi:
            writer.writerow([r.get(c) for c in cot])

    with open(duong_dan_meta, "w", newline="", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    logger.info("Đã ghi kết quả: %s (kèm %s)", duong_dan_csv, duong_dan_meta)
    return duong_dan_csv, duong_dan_meta


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
    """Chạy `git status --porcelain` giới hạn theo pathspec, trả về cây có bẩn hay không.

    Phạm vi được giới hạn bằng pathspec chứ KHÔNG bằng cách bỏ tệp chưa được git theo dõi:
    một tệp .py mới chưa `git add` trong `src/` vẫn phải làm cờ bật, vì mã đó có ảnh hưởng
    kết quả đo (P2-06c §5.1).

    Args:
        pham_vi: Danh sách đường dẫn giới hạn phép kiểm. Rỗng nghĩa là toàn bộ cây.

    Returns:
        True nếu git in ra bất kỳ dòng nào, hoặc nếu không chạy được git (P2-06c §5.2).
    """
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
    """Kiểm mã nguồn sinh ra số đo có thay đổi nào chưa commit hay không (R17).

    Chỉ xét các đường dẫn ở `_DUONG_DAN_ANH_HUONG_PHEP_DO`. Tệp mới trong `results/`,
    `notebooks/` hay `docs/` không làm cờ này bật, vì chúng không đổi kết quả của
    phép đo đang chạy.

    Returns:
        True nếu có thay đổi chưa commit trong phạm vi trên, hoặc nếu không chạy
        được git (giả định xấu nhất, giữ nguyên hành vi cũ).
    """
    return _chay_git_status(_DUONG_DAN_ANH_HUONG_PHEP_DO)


def _kiem_tra_git_dirty_toan_cay() -> bool:
    """Kiểm toàn bộ thư mục dự án, kể cả tệp chưa được theo dõi.

    Giá trị này ghi vào meta dưới khoá `git_dirty_toan_cay` để không mất thông tin:
    người đọc sau này vẫn biết lúc đo thư mục có gì khác thường hay không, nhưng
    điều kiện của checklist §9 thì căn theo `git_dirty` ở trên.

    Returns:
        True nếu cây làm việc có bất kỳ thay đổi chưa commit nào, hoặc nếu không
        chạy được git.
    """
    return _chay_git_status(())


def _xay_dung_parser() -> argparse.ArgumentParser:
    """Dựng argparse cho script, theo đúng giao diện dòng lệnh ở §4 đặc tả."""
    parser = argparse.ArgumentParser(
        description=(
            "Đo hiệu năng khối phát hiện khuôn mặt YOLOv8n-face trên ma trận "
            "{mô hình} x {số luồng} — mỗi mô hình mang sẵn bộ suy luận và độ phân giải của nó "
            "(xem docs/dac-ta/P2-03-benchmark-detect.md và P2-06-benchmark-ncnn.md)."
        )
    )
    parser.add_argument(
        "--config", default="configs/detect.yaml", help="Đường dẫn file cấu hình phát hiện"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=[
            "models/yolov8n-face-320.onnx",
            "models/yolov8n-face-640.onnx",
            "models/yolov8n-face-320_ncnn_model",
            "models/yolov8n-face-640_ncnn_model",
        ],
        help="Danh sách mô hình cần đo — tệp .onnx hoặc thư mục *_ncnn_model",
    )
    parser.add_argument(
        "--threads", nargs="+", type=int, default=[1, 2, 4], help="Các mức số luồng cần quét"
    )
    parser.add_argument(
        "--n-frames",
        type=int,
        default=SO_FRAME_TOI_THIEU,
        help=f"Số khung hình đo mỗi cấu hình, tối thiểu {SO_FRAME_TOI_THIEU} (R9)",
    )
    parser.add_argument(
        "--warmup", type=int, default=10, help="Số khung hình làm nóng, không tính vào kết quả"
    )
    parser.add_argument(
        "--nguon",
        choices=["dia", "camera"],
        default="dia",
        help="Nguồn khung hình: 'dia' = ảnh nạp sẵn (bước 2.6), 'camera' = lấy trực tiếp "
        "từ khối thu hình (bước 2.5)",
    )
    parser.add_argument(
        "--anh-dir",
        default=None,
        help=f"[chế độ dia] Thư mục ảnh nguồn (mặc định {_ANH_DIR_MAC_DINH})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help=f"[chế độ dia] Seed chọn mẫu ảnh, để tái lập — R15 (mặc định {_SEED_MAC_DINH})",
    )
    parser.add_argument(
        "--capture-config",
        default=None,
        help="[chế độ camera] Đường dẫn cấu hình thu hình (mặc định configs/capture.yaml)",
    )
    parser.add_argument(
        "--capture-backend",
        default=None,
        choices=["opencv", "mock"],
        help="[chế độ camera] BẮT BUỘC. Backend thu hình, ghi đè khoá 'backend' của cấu "
        "hình. Giá trị 'auto' bị cấm ở đây: nó âm thầm rơi về mock khi không mở được "
        "camera, sinh ra tệp kết quả trông hợp lệ nhưng chứa nhiễu tổng hợp (P2-07 §4.3).",
    )
    parser.add_argument(
        "--anh-sang",
        default=None,
        help="[chế độ camera] BẮT BUỘC. Mô tả điều kiện ánh sáng, ví dụ 'trong nhà, đèn LED trần'",
    )
    parser.add_argument(
        "--khoang-cach-m",
        type=float,
        default=None,
        help="[chế độ camera] BẮT BUỘC. Khoảng cách từ mặt tới camera, đơn vị mét (hữu hạn, > 0)",
    )
    parser.add_argument(
        "--noi-dung-khung",
        default=None,
        choices=["co-nguoi", "khong-nguoi"],
        help="[chế độ camera] BẮT BUỘC. Trong khung có người hay không",
    )
    parser.add_argument(
        "--device-name",
        default=None,
        help='Tên thiết bị đo, ví dụ "Raspberry Pi 5 8GB" hoặc "PC phát triển" (bắt buộc)',
    )
    parser.add_argument("--ghi-chu", default="", help="Ghi chú tự do, vào notes của meta")
    parser.add_argument(
        "--dry-run", action="store_true", help="In kế hoạch, không đo, không ghi tệp"
    )
    return parser


def _kiem_co_sai_che_do(args: argparse.Namespace) -> str | None:
    """Kiểm một cờ có bị dùng ở chế độ không thuộc về nó không (P2-07 §5.2).

    Báo lỗi thay vì bỏ qua kèm cảnh báo: cảnh báo in ra màn hình biến mất khi đóng cửa
    sổ, còn `.meta.json` thì sống mãi — một meta lượt đo camera mang `"seed": 42` là lời
    khẳng định sai về tính tái lập.

    Args:
        args: Namespace đã phân giải từ argparse.

    Returns:
        Câu thông báo lỗi (nêu tên cờ và tên chế độ đang chạy) nếu có vi phạm, ngược lại None.
    """
    if args.nguon == "camera":
        co_cam = {
            "--anh-dir": args.anh_dir is not None,
            "--seed": args.seed is not None,
        }
    else:
        co_cam = {
            "--capture-config": args.capture_config is not None,
            "--capture-backend": args.capture_backend is not None,
            "--anh-sang": args.anh_sang is not None,
            "--khoang-cach-m": args.khoang_cach_m is not None,
            "--noi-dung-khung": args.noi_dung_khung is not None,
        }

    vi_pham = [ten for ten, da_dung in co_cam.items() if da_dung]
    if vi_pham:
        return (
            f"Cờ {', '.join(vi_pham)} không dùng được ở chế độ '{args.nguon}'. "
            "Bỏ cờ này hoặc đổi --nguon (P2-07 §5.2)."
        )
    return None


def _kiem_co_bat_buoc_camera(args: argparse.Namespace) -> list[str]:
    """Trả về danh sách cờ BẮT BUỘC của chế độ camera còn thiếu (P2-07 §5.1)."""
    thieu: list[str] = []
    if args.capture_backend is None:
        thieu.append("--capture-backend")
    if args.anh_sang is None:
        thieu.append("--anh-sang")
    if args.khoang_cach_m is None:
        thieu.append("--khoang-cach-m")
    if args.noi_dung_khung is None:
        thieu.append("--noi-dung-khung")
    return thieu


def _in_bang_camera(tom_tat_o: dict, tong_hop_suy_luan: dict) -> None:
    """In bảng tóm tắt Markdown cuối cùng cho chế độ camera (P2-07 §7)."""
    print("\n### BẢNG TỔNG KẾT BENCHMARK DETECT — CHẾ ĐỘ CAMERA")
    print(
        "| FPS suy luận (fps_tb) | FPS đầu-cuối (fps_tong_tb) | Lấy khung p50/p95 (ms) | "
        f"Suy luận p50/p95 (ms) | Tỉ lệ phát hiện | Đạt >= {NGUONG_FPS_TOI_THIEU:.0f} FPS |"
    )
    print("|---|---|---|---|---|---|")
    print(
        f"| {tom_tat_o['fps_tb']:.2f} | {tom_tat_o['fps_tong_tb']:.2f} | "
        f"{tom_tat_o['lay_khung_p50']:.1f} / {tom_tat_o['lay_khung_p95']:.1f} | "
        f"{tong_hop_suy_luan['latency_p50']:.1f} / {tong_hop_suy_luan['latency_p95']:.1f} | "
        f"{tom_tat_o['ti_le_phat_hien']:.2%} | "
        f"{'Đạt' if tom_tat_o['dat_chi_tieu'] else 'KHÔNG ĐẠT'} |"
    )
    print(
        "\n⚠️ Trần tốc độ khung: latency_lay_khung_ms có sàn bằng nghịch đảo tốc độ khung "
        "của webcam, nên fps_tong_tb bị chặn quanh tốc độ khung và KHÔNG thể vượt nó dù "
        "khối phát hiện nhanh hơn — đây là trần của thiết kế, không phải khuyết điểm. Chỉ "
        "tiêu §1 'FPS riêng module detect >= 10' đọc ở cột fps_tb (dat_chi_tieu), KHÔNG "
        "phải fps_tong_tb."
    )
    print("⚠️ Kết luận Đạt/Không đạt CHÍNH THỨC chỉ có giá trị khi đo trên Raspberry Pi 5 thật.")


def _chay_camera(args: argparse.Namespace, argv_hien_thi: list[str]) -> int:
    """Nhánh chế độ camera của main() — xem P2-07 §5.3.

    Camera được mở ĐÚNG MỘT LẦN ở đây; `do_mot_cau_hinh_camera` nhận bộ thu hình đã mở và
    không tự mở/đóng. Mất camera giữa chừng ⇒ đóng camera (fail-safe R24), không ghi tệp
    nào, trả 1.
    """
    thieu = _kiem_co_bat_buoc_camera(args)
    if thieu:
        logger.error("Chế độ camera thiếu cờ bắt buộc: %s", ", ".join(thieu))
        print(f"Chế độ camera thiếu cờ bắt buộc: {', '.join(thieu)}.")
        return 1

    # Hai phép kiểm TÁCH RỜI với hai thông báo khác nhau (P2-07 §5.2, ĐB8): argparse với
    # type=float nhận inf/-inf/nan im lặng; nan lọt qua mọi phép so sánh miền thông thường.
    if not math.isfinite(args.khoang_cach_m):
        logger.error("--khoang-cach-m không hữu hạn: %s", args.khoang_cach_m)
        print(
            f"--khoang-cach-m phải là số hữu hạn, nhận được {args.khoang_cach_m}. "
            "argparse chấp nhận inf/-inf/nan cho type=float nên phải kiểm ở đây."
        )
        return 1
    if args.khoang_cach_m <= 0:
        logger.error("--khoang-cach-m không dương: %s", args.khoang_cach_m)
        print(f"--khoang-cach-m phải lớn hơn 0, nhận được {args.khoang_cach_m}.")
        return 1

    if len(args.models) != 1 or len(args.threads) != 1:
        logger.error(
            "Chế độ camera cần đúng một cấu hình: --models có %d phần tử, --threads có %d mức",
            len(args.models),
            len(args.threads),
        )
        print(
            "Chế độ camera đo ĐÚNG MỘT cấu hình (P2-07 §4.2): --models cần đúng 1 phần tử "
            f"(nhận {len(args.models)}), --threads cần đúng 1 mức (nhận {len(args.threads)})."
        )
        return 1

    if args.dry_run:
        print("\n### BẢNG KẾ HOẠCH BENCHMARK DETECT — CHẾ ĐỘ CAMERA (DRY-RUN)")
        print("| Mô hình | Backend thu hình | Số luồng | n_frames | warmup |")
        print("|---|---|---|---|---|")
        print(
            f"| `{args.models[0]}` | {args.capture_backend} | {args.threads[0]} | "
            f"{args.n_frames} | {args.warmup} |"
        )
        print("Camera KHÔNG được mở ở chế độ dry-run.\n")
        return 0

    try:
        cfg = nap_cau_hinh(args.config)
    except LoiCauHinh as e:
        logger.error("Không đọc được cấu hình phát hiện: %s", e)
        print(f"Không đọc được cấu hình '{args.config}': {e}")
        return 1

    duong_dan_capture_cfg = args.capture_config or "configs/capture.yaml"
    try:
        cfg_capture = nap_cau_hinh(duong_dan_capture_cfg)
    except LoiCauHinh as e:
        logger.error("Không đọc được cấu hình thu hình: %s", e)
        print(f"Không đọc được cấu hình thu hình '{duong_dan_capture_cfg}': {e}")
        return 1

    # Ghi đè khoá backend TRƯỚC khi gọi tao_bo_thu_hinh (P2-07 §4.3): script benchmark chỉ
    # nhận backend tường minh, không nhận backend tự-dò của pipeline sản phẩm.
    cfg_capture = dict(cfg_capture)
    cfg_capture["backend"] = args.capture_backend

    mo_hinh = Path(args.models[0])
    if not mo_hinh.exists():
        logger.error("Không tìm thấy mô hình: %s", mo_hinh)
        print(f"Không tìm thấy mô hình: '{mo_hinh}'.")
        return 1

    so_luong_luong = args.threads[0]
    cfg_combo = dict(cfg)
    cfg_combo["inference"] = dict(cfg.get("inference", {}))
    cfg_combo["inference"]["num_threads"] = so_luong_luong

    thoi_diem_bat_dau_do = time.perf_counter()
    nhiet_do_bat_dau = doc_nhiet_do_cpu()

    try:
        bo_thu_hinh = tao_bo_thu_hinh(cfg_capture)
    except LoiCauHinh as e:
        logger.error("Không tạo được bộ thu hình: %s", e)
        print(f"Không tạo được bộ thu hình (camera): {e}")
        return 1

    ban_ghi: list[dict] = []
    khung_mau = None
    try:
        bo_thu_hinh.mo()
        ban_ghi = do_mot_cau_hinh_camera(
            mo_hinh, cfg_combo, bo_thu_hinh, args.n_frames, args.warmup
        )
        # Một khung mẫu để đọc độ phân giải THẬT — sau cả hai vùng bấm giờ (P2-07 §5.4).
        khung_mau = bo_thu_hinh.doc_frame()
    except (LoiCamera, LoiMoHinh, LoiCauHinh) as e:
        logger.error("Benchmark camera thất bại: %s", e)
        print(f"Benchmark camera thất bại (lỗi camera hoặc mô hình): {e}")
        return 1
    finally:
        bo_thu_hinh.dong()

    thoi_gian_chay = time.perf_counter() - thoi_diem_bat_dau_do

    tong_hop_suy_luan = tong_hop(ban_ghi)
    tong_hop_cam = tong_hop_camera(ban_ghi)

    # Nghi ngờ bộ đệm khung (P2-07 §4.1): lấy khung p50 dưới ngưỡng VÀ suy luận chậm hơn
    # lấy khung ít nhất _HE_SO_NGHI_NGO_DEM_KHUNG lần.
    lay_khung_p50 = tong_hop_cam["lay_khung_p50"]
    suy_luan_p50 = tong_hop_suy_luan["latency_p50"]
    nghi_dem_khung = (
        lay_khung_p50 < _NGUONG_NGHI_NGO_DEM_KHUNG_MS
        and suy_luan_p50 >= lay_khung_p50 * _HE_SO_NGHI_NGO_DEM_KHUNG
    )

    dataset = mo_ta_nguon_camera(cfg_capture, args.capture_backend, khung_mau)
    dataset["n_frame_do"] = len(ban_ghi)
    dataset["n_frame_lam_nong"] = args.warmup

    thoi_diem = datetime.datetime.now().astimezone()
    run_id = f"bench_detect_camera_{thoi_diem.strftime('%Y%m%d_%H%M')}"
    for r in ban_ghi:
        r["run_id"] = run_id
        r["threads"] = so_luong_luong

    cac_nhiet_do = [r["cpu_temp_c"] for r in ban_ghi if r["cpu_temp_c"] is not None]
    if nhiet_do_bat_dau is not None:
        cac_nhiet_do.append(nhiet_do_bat_dau)
    nhiet_do_max = max(cac_nhiet_do) if cac_nhiet_do else None

    moi_truong = xac_dinh_moi_truong()
    try:
        phien_ban_ncnn = _lay_phien_ban_ncnn()
    except importlib.metadata.PackageNotFoundError as e:
        logger.warning("Không tra được phiên bản gói ncnn: %s", e)
        phien_ban_ncnn = "khong-xac-dinh"

    khoa_o = f"00_{mo_hinh.stem}_t{so_luong_luong}"
    tom_tat = {khoa_o: {**tong_hop_suy_luan, **tong_hop_cam}}

    canh_bao: dict[str, str] = {}
    cac_cau_canh_bao: list[str] = []
    if moi_truong != _MOI_TRUONG_PHAN_CUNG_DICH:
        cau = _CANH_BAO_NGOAI_PHAN_CUNG_DICH.format(moi_truong)
        canh_bao["canh_bao_hieu_nang"] = cau
        cac_cau_canh_bao.append(cau)
    if args.capture_backend == "mock":
        cau = (
            "CẢNH BÁO: nguồn khung hình là backend giả lập (mock), KHÔNG phải camera thật "
            "— số liệu chỉ để kiểm chức năng, không đưa vào kết luận Cổng C."
        )
        canh_bao["canh_bao_nguon_gia_lap"] = cau
        cac_cau_canh_bao.append(cau)
    if dataset["khop_do_phan_giai"] is False:
        cau = (
            f"CẢNH BÁO: độ phân giải thật {dataset['do_phan_giai_that']} khác giá trị yêu "
            f"cầu {dataset['do_phan_giai_yeu_cau']} trong cấu hình — webcam từ chối "
            "cap.set() im lặng, cần sửa nhãn cấu hình (phép đo vẫn hợp lệ)."
        )
        canh_bao["canh_bao_do_phan_giai"] = cau
        cac_cau_canh_bao.append(cau)
    if nghi_dem_khung:
        cau = (
            "CẢNH BÁO: nghi ngờ bộ đệm khung của lớp thu hình — thời gian lấy khung p50 "
            f"({lay_khung_p50:.3f} ms) dưới ngưỡng {_NGUONG_NGHI_NGO_DEM_KHUNG_MS:.1f} ms "
            "và nhỏ hơn nhiều lần thời gian suy luận; khung hình có thể đã cũ."
        )
        canh_bao["canh_bao_dem_khung"] = cau
        cac_cau_canh_bao.append(cau)

    ghi_chu = args.ghi_chu
    if cac_cau_canh_bao:
        ghi_chu = f"{ghi_chu} {' '.join(cac_cau_canh_bao)}".strip()

    meta: dict = {
        "run_id": run_id,
        "timestamp": thoi_diem.isoformat(),
        "git_commit": _lay_git_commit_hash(),
        "git_dirty": _kiem_tra_git_dirty(),
        "git_dirty_toan_cay": _kiem_tra_git_dirty_toan_cay(),
        "script": "scripts/benchmark_detect.py",
        "command": "python scripts/benchmark_detect.py " + " ".join(argv_hien_thi),
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
            detector_factory.TEN_BACKEND_NCNN: phien_ban_ncnn,
        },
        "config_file": args.config,
        "config_snapshot": cfg,
        "dataset": dataset,
        "seed": None,
        "warmup_frames": args.warmup,
        "cpu_temp_start_c": nhiet_do_bat_dau,
        "cpu_temp_max_c": nhiet_do_max,
        "duration_s": thoi_gian_chay,
        "notes": ghi_chu,
        "tom_tat": tom_tat,
        "nguon": "camera",
        "conditions": {
            "anh_sang": args.anh_sang,
            "khoang_cach_m": args.khoang_cach_m,
            "noi_dung_khung": args.noi_dung_khung,
        },
        "config_file_capture": duong_dan_capture_cfg,
        "config_snapshot_capture": cfg_capture,
    }
    meta.update(canh_bao)

    try:
        duong_dan_csv, duong_dan_meta = ghi_ket_qua(
            _THU_MUC_KET_QUA_MAC_DINH,
            run_id,
            ban_ghi,
            meta,
            cot=_COT_CSV_CAMERA,
            khoa_bat_buoc=_KHOA_META_BAT_BUOC_CAMERA,
        )
    except LoiCauHinh as e:
        logger.error("Không ghi được kết quả: %s", e)
        print(f"Không ghi được kết quả: {e}")
        return 1

    _in_bang_camera(tom_tat[khoa_o], tong_hop_suy_luan)
    print(f"\nKết quả đầy đủ: `{duong_dan_csv}` (kèm `{duong_dan_meta}`)\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 thành công, 1 thất bại."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    args = _xay_dung_parser().parse_args(argv)

    if args.device_name is None:
        logger.error("Thiếu tham số bắt buộc --device-name")
        print(
            'Thiếu tham số bắt buộc --device-name. Ví dụ: --device-name "Raspberry Pi 5 8GB" '
            "(R8: mọi số đo phải kèm ngữ cảnh thiết bị)."
        )
        return 1

    if args.n_frames < SO_FRAME_TOI_THIEU:
        logger.error("--n-frames=%d nhỏ hơn mức tối thiểu %d", args.n_frames, SO_FRAME_TOI_THIEU)
        print(
            f"--n-frames phải >= {SO_FRAME_TOI_THIEU} (R9: mỗi lần đo tối thiểu "
            f"{SO_FRAME_TOI_THIEU} khung hình), nhận được {args.n_frames}."
        )
        return 1

    if args.warmup < 0:
        logger.error("--warmup=%d không được âm", args.warmup)
        print(f"--warmup phải >= 0, nhận được {args.warmup}.")
        return 1

    loi_che_do = _kiem_co_sai_che_do(args)
    if loi_che_do is not None:
        logger.error("Cờ sai chế độ: %s", loi_che_do)
        print(loi_che_do)
        return 1

    argv_hien_thi = argv if argv is not None else sys.argv[1:]

    if args.nguon == "camera":
        return _chay_camera(args, argv_hien_thi)

    # ---- Chế độ dia — hành vi bước 2.6, KHÔNG đổi (P2-07 §6) ----
    # Phân giải None về đúng hai giá trị cũ TRƯỚC khi dùng, kể cả trong nhánh --dry-run.
    anh_dir_da_phan_giai = args.anh_dir if args.anh_dir is not None else _ANH_DIR_MAC_DINH
    seed_da_phan_giai = args.seed if args.seed is not None else _SEED_MAC_DINH

    try:
        cfg = nap_cau_hinh(args.config)
    except LoiCauHinh as e:
        logger.error("Không đọc được cấu hình: %s", e)
        print(f"Không đọc được cấu hình '{args.config}': {e}")
        return 1

    models = [Path(m) for m in args.models]
    threads_list: list[int] = args.threads

    if args.dry_run:
        print("\n### BẢNG KẾ HOẠCH BENCHMARK DETECT (DRY-RUN)")
        print("| Mô hình | backend | Số luồng |")
        print("|---|---|---|")
        for m in models:
            # Tra một lần cho mỗi mô hình, dùng lại cho mọi mức luồng của nó — CHỈ suy từ
            # dạng đường dẫn, không khởi tạo mô hình nào (P2-06b §5.1, §6.2 dòng 09).
            ten_backend = detector_factory.tra_ten_backend(m)
            for t in threads_list:
                print(f"| `{m}` | {ten_backend} | {t} |")
        print(
            f"\nẢnh nguồn : `{anh_dir_da_phan_giai}` (n_frames={args.n_frames}, "
            f"warmup={args.warmup}, seed={seed_da_phan_giai})"
        )
        print(f"Thiết bị  : `{args.device_name}`\n")
        return 0

    for m in models:
        # Chỉ kiểm TỒN TẠI, không kiểm là tệp hay thư mục: mô hình NCNN là một thư mục.
        # Đường dẫn có hợp lệ hay không do tao_bo_phat_hien phán, và LoiCauHinh nó ném ra
        # đã được bắt ở vòng đo bên dưới.
        if not m.exists():
            logger.error("Không tìm thấy mô hình: %s", m)
            print(
                f"Không tìm thấy mô hình: '{m}'. Chạy scripts/export_detector.py hoặc "
                "scripts/export_detector_ncnn.py trước."
            )
            return 1

    anh_dir = Path(anh_dir_da_phan_giai)
    so_can = args.n_frames + args.warmup
    try:
        duong_dan_anh = chon_anh(anh_dir, so_can, seed_da_phan_giai)
    except LoiCauHinh as e:
        logger.error("Không chọn được ảnh nguồn: %s", e)
        print(str(e))
        return 1

    anh_da_nap: list[np.ndarray] = []
    for p in duong_dan_anh:
        anh = cv2.imread(str(p))
        if anh is None:
            logger.warning("Không đọc được ảnh, bỏ qua: %s", p)
            continue
        anh_da_nap.append(anh)

    if len(anh_da_nap) < so_can:
        logger.error("Không nạp đủ ảnh hợp lệ: cần %d, đọc được %d", so_can, len(anh_da_nap))
        print(f"Không nạp đủ ảnh hợp lệ: cần {so_can}, đọc được {len(anh_da_nap)}.")
        return 1

    trong_container = dang_trong_container()
    if trong_container:
        print(
            "CẢNH BÁO: đang chạy trong container ARM64 (QEMU) — số đo thời gian KHÔNG quy "
            "đổi được sang phần cứng thật, KHÔNG dùng số này làm số hiệu năng chính thức. "
            "Xem experiment-protocol.instructions.md §2."
        )
        logger.warning("Đang chạy trong container — số đo hiệu năng không dùng được (QEMU)")

    thoi_diem_bat_dau_do = time.perf_counter()
    nhiet_do_bat_dau = doc_nhiet_do_cpu()

    toan_bo_ban_ghi: list[dict] = []
    tom_tat: dict[str, dict] = {}
    imgsz_theo_mo_hinh: dict[int, int] = {}

    try:
        # Khoá theo CHỈ SỐ ô (i), không theo m.stem: hai mô hình khác thư mục nhưng trùng tên
        # tệp (vd. so hai bản export cùng độ phân giải, opset khác) sẽ đè mất tổng hợp của
        # nhau nếu chỉ dùng m.stem — vỡ bất biến "số ô ma trận = số mô hình x số mức luồng".
        for i, m in enumerate(models):
            for t in threads_list:
                cfg_combo = dict(cfg)
                cfg_combo["inference"] = dict(cfg.get("inference", {}))
                cfg_combo["inference"]["num_threads"] = t

                ban_ghi = do_mot_cau_hinh(m, cfg_combo, args.n_frames, anh_da_nap, args.warmup)
                for r in ban_ghi:
                    r["run_id"] = ""  # điền lại bên dưới sau khi biết run_id
                    r["threads"] = t

                # `backend` và `imgsz` do do_mot_cau_hinh đọc từ chính đối tượng phát hiện
                # (P2-06 §6.1). Lấy lại imgsz ở đây chỉ để in bảng tổng kết cuối.
                imgsz_theo_mo_hinh[i] = ban_ghi[0]["imgsz"]
                tom_tat[f"{i:02d}_{m.stem}_t{t}"] = tong_hop(ban_ghi)
                toan_bo_ban_ghi.extend(ban_ghi)
    except (LoiMoHinh, LoiCauHinh) as e:
        logger.error("Benchmark thất bại: %s", e)
        print(f"Benchmark thất bại: {e}")
        return 1

    thoi_diem = datetime.datetime.now().astimezone()
    run_id = f"bench_detect_{thoi_diem.strftime('%Y%m%d_%H%M')}"
    for r in toan_bo_ban_ghi:
        r["run_id"] = run_id

    thoi_gian_chay = time.perf_counter() - thoi_diem_bat_dau_do
    cac_nhiet_do = [r["cpu_temp_c"] for r in toan_bo_ban_ghi if r["cpu_temp_c"] is not None]
    if nhiet_do_bat_dau is not None:
        cac_nhiet_do.append(nhiet_do_bat_dau)
    nhiet_do_max = max(cac_nhiet_do) if cac_nhiet_do else None

    moi_truong = xac_dinh_moi_truong()
    ghi_chu = args.ghi_chu
    if moi_truong != _MOI_TRUONG_PHAN_CUNG_DICH:
        canh_bao_moi_truong = _CANH_BAO_NGOAI_PHAN_CUNG_DICH.format(moi_truong)
        ghi_chu = f"{ghi_chu} {canh_bao_moi_truong}".strip()

    try:
        phien_ban_ncnn = _lay_phien_ban_ncnn()
    except importlib.metadata.PackageNotFoundError as e:
        logger.warning("Không tra được phiên bản gói ncnn: %s", e)
        phien_ban_ncnn = "khong-xac-dinh"

    meta: dict = {
        "run_id": run_id,
        "timestamp": thoi_diem.isoformat(),
        "git_commit": _lay_git_commit_hash(),
        "git_dirty": _kiem_tra_git_dirty(),
        "git_dirty_toan_cay": _kiem_tra_git_dirty_toan_cay(),
        "script": "scripts/benchmark_detect.py",
        "command": "python scripts/benchmark_detect.py " + " ".join(argv_hien_thi),
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
            detector_factory.TEN_BACKEND_NCNN: phien_ban_ncnn,
        },
        "config_file": args.config,
        "config_snapshot": cfg,
        "dataset": {
            "anh_dir": str(anh_dir),
            "n_anh_tong": len(anh_da_nap),
            # Khai theo SỐ BẢN GHI THẬT đã ghi ra CSV, không theo cờ --n-frames — --warmup âm
            # (đã chặn ở trên, nhưng giữ đúng ý nghĩa nếu logic đo thay đổi sau này) có thể làm
            # số dòng thật lệch khỏi giá trị cờ; tệp meta phải khai đúng cỡ mẫu thật (R6).
            "n_frames_moi_cau_hinh": len(toan_bo_ban_ghi) // max(len(tom_tat), 1),
        },
        "seed": seed_da_phan_giai,
        "warmup_frames": args.warmup,
        "cpu_temp_start_c": nhiet_do_bat_dau,
        "cpu_temp_max_c": nhiet_do_max,
        "duration_s": thoi_gian_chay,
        "notes": ghi_chu,
        "tom_tat": tom_tat,
        # Ghi ở CẢ HAI chế độ; chỉ danh sách bắt buộc của chế độ camera mới đòi khoá này
        # (P2-07 §5.5). Tệp meta cũ thiếu khoá ⇒ quy ước đọc là "dia".
        "nguon": "dia",
    }
    if trong_container:
        meta["canh_bao_hieu_nang"] = (
            "Đo trong container ARM64 giả lập qua QEMU — thời gian KHÔNG quy đổi được sang "
            "Raspberry Pi 5 thật, KHÔNG dùng số này làm số hiệu năng chính thức trong báo cáo. "
            "Chỉ dùng để kiểm tính đúng đắn. Xem experiment-protocol.instructions.md §2."
        )

    try:
        duong_dan_csv, duong_dan_meta = ghi_ket_qua(
            _THU_MUC_KET_QUA_MAC_DINH, run_id, toan_bo_ban_ghi, meta
        )
    except LoiCauHinh as e:
        logger.error("Không ghi được kết quả: %s", e)
        print(f"Không ghi được kết quả: {e}")
        return 1

    print("\n### BẢNG TỔNG KẾT BENCHMARK DETECT")
    print(
        "| Cấu hình | imgsz | Luồng | FPS TB | Latency p50 (ms) | Latency p95 (ms) | "
        f"Tỉ lệ phát hiện | Đạt >= {NGUONG_FPS_TOI_THIEU:.0f} FPS |"
    )
    print("|---|---|---|---|---|---|---|---|")
    for i, m in enumerate(models):
        for t in threads_list:
            kq = tom_tat[f"{i:02d}_{m.stem}_t{t}"]
            print(
                f"| {m.name} | {imgsz_theo_mo_hinh[i]} | {t} | {kq['fps_tb']:.2f} | "
                f"{kq['latency_p50']:.1f} | {kq['latency_p95']:.1f} | "
                f"{kq['ti_le_phat_hien']:.2%} | "
                f"{'Đạt' if kq['dat_chi_tieu'] else 'KHÔNG ĐẠT'} |"
            )
    print(
        "\n⚠️ Kết luận Đạt/Không đạt CHÍNH THỨC chỉ có giá trị khi đo trên Raspberry Pi 5 "
        "thật (Cổng C của Phase 2) — xem docs/dac-ta/P2-03-benchmark-detect.md §9."
    )
    print(f"\nKết quả đầy đủ: `{duong_dan_csv}` (kèm `{duong_dan_meta}`)\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
