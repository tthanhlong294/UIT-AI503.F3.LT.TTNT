"""Đo hiệu năng khối phát hiện khuôn mặt YOLOv8n-face (ONNX) — bước 2.6 của CLAUDE.md.

Xem docs/dac-ta/P2-03-benchmark-detect.md. Script này là CÔNG CỤ, không phải phép đo: chỉ khi
chạy trên Raspberry Pi 5 thật thì số đo mới có giá trị đưa vào Cổng C của Phase 2 (xem chốt
chặn container ở dưới và experiment-protocol.instructions.md §2).

Ma trận đo: {tệp .onnx được liệt kê ở --models} × {số luồng ở --threads}. Cùng một tập ảnh đã
nạp sẵn được dùng lại cho MỌI ô của ma trận để bảo đảm so sánh công bằng (chỉ đổi đúng một biến
mỗi lần — xem experiment-protocol.instructions.md §2 "Quy tắc so sánh công bằng").
"""

import sys
from pathlib import Path

# Thêm gốc dự án vào sys.path để cho phép chạy trực tiếp kịch bản
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import csv
import datetime
import json
import platform
import random
import subprocess
import time

import cv2
import numpy as np
import onnxruntime as ort

from src.common.config import nap_cau_hinh
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger
from src.detector import YoloFaceDetector

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

_KHOA_META_BAT_BUOC = (
    "run_id",
    "timestamp",
    "git_commit",
    "git_dirty",
    "script",
    "command",
    "device",
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
    duong_dan_onnx: Path,
    cfg: dict,
    so_luong: int,
    anh_da_nap: list[np.ndarray],
    so_lam_nong: int,
) -> list[dict]:
    """Đo một ô của ma trận benchmark (một tệp .onnx tại một mức số luồng).

    Ảnh phải được truyền vào ĐÃ NẠP SẴN vào bộ nhớ — thời gian đọc tệp không được tính vào
    phép đo (§3 đặc tả). Vùng đo thời gian chỉ bọc lệnh gọi `detector.detect`.

    Args:
        duong_dan_onnx: Đường dẫn tệp .onnx cần đo.
        cfg: Cấu hình truyền cho YoloFaceDetector (đã đặt sẵn inference.num_threads).
        so_luong: Số khung hình cần đo (không tính khung làm nóng).
        anh_da_nap: Ảnh đã nạp sẵn vào bộ nhớ, độ dài tối thiểu `so_lam_nong + so_luong`.
            `so_lam_nong` ảnh đầu dùng để làm nóng, phần còn lại dùng để đo.
        so_lam_nong: Số khung hình chạy làm nóng trước, không tính vào kết quả.

    Returns:
        Danh sách bản ghi, mỗi khung hình đo một bản ghi, gồm các khoá `sample_idx`,
        `latency_ms`, `fps_instant`, `n_faces`, `conf_top`, `cpu_temp_c`.

    Raises:
        LoiMoHinh: không nạp được mô hình.
        LoiCauHinh: cấu hình sai, hoặc không đủ ảnh đã nạp sẵn cho warm-up + đo.
    """
    tong_can = so_lam_nong + so_luong
    if len(anh_da_nap) < tong_can:
        raise LoiCauHinh(
            f"Cần ít nhất {tong_can} ảnh đã nạp sẵn (làm nóng {so_lam_nong} + đo {so_luong}), "
            f"chỉ có {len(anh_da_nap)}"
        )

    detector = YoloFaceDetector(duong_dan_onnx, cfg)

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
                "sample_idx": idx,
                "latency_ms": latency_ms,
                "fps_instant": 1000.0 / latency_ms,
                "n_faces": len(khuon_mat),
                "conf_top": khuon_mat[0].confidence if khuon_mat else None,
                "cpu_temp_c": doc_nhiet_do_cpu(),
            }
        )

    return ban_ghi


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


def ghi_ket_qua(thu_muc: Path, run_id: str, ban_ghi: list[dict], meta: dict) -> tuple[Path, Path]:
    """Ghi ĐÚNG HAI tệp kết quả: dữ liệu thô .csv và ngữ cảnh .meta.json.

    Args:
        thu_muc: Thư mục đích (thường là `results/`).
        run_id: Định danh lần chạy, dùng làm tên tệp: `<run_id>.csv`, `<run_id>.meta.json`.
        ban_ghi: Danh sách bản ghi thô, mỗi phần tử là một dòng CSV — đã có đủ mười khoá
            liệt kê ở `_COT_CSV`.
        meta: Ngữ cảnh của lần chạy — xem `_KHOA_META_BAT_BUOC`.

    Returns:
        Tuple `(đường_dẫn_csv, đường_dẫn_meta)`.

    Raises:
        LoiCauHinh: meta thiếu khoá bắt buộc.
    """
    thieu = [khoa for khoa in _KHOA_META_BAT_BUOC if khoa not in meta]
    if thieu:
        raise LoiCauHinh(f"Bản ghi meta thiếu khoá bắt buộc: {', '.join(thieu)}")

    thu_muc = Path(thu_muc)
    thu_muc.mkdir(parents=True, exist_ok=True)

    duong_dan_csv = thu_muc / f"{run_id}.csv"
    duong_dan_meta = thu_muc / f"{run_id}.meta.json"

    with open(duong_dan_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_COT_CSV)
        for r in ban_ghi:
            writer.writerow([r.get(cot) for cot in _COT_CSV])

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


def _kiem_tra_git_dirty() -> bool:
    """Kiểm tra cây làm việc có thay đổi chưa commit hay không, dùng cho .meta.json (R17)."""
    try:
        ket_qua = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(__file__).resolve().parents[1],
        )
        return bool(ket_qua.stdout.strip())
    except (subprocess.CalledProcessError, OSError) as e:
        logger.warning("Không kiểm tra được trạng thái git: %s", e)
        return True


def _xay_dung_parser() -> argparse.ArgumentParser:
    """Dựng argparse cho script, theo đúng giao diện dòng lệnh ở §4 đặc tả."""
    parser = argparse.ArgumentParser(
        description=(
            "Đo hiệu năng khối phát hiện khuôn mặt YOLOv8n-face (ONNX) trên ma trận "
            "{độ phân giải} x {số luồng} (xem docs/dac-ta/P2-03-benchmark-detect.md)."
        )
    )
    parser.add_argument(
        "--config", default="configs/detect.yaml", help="Đường dẫn file cấu hình phát hiện"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["models/yolov8n-face-320.onnx", "models/yolov8n-face-640.onnx"],
        help="Danh sách tệp .onnx cần đo",
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
    parser.add_argument("--anh-dir", default="data/impostor/lfw_original", help="Thư mục ảnh nguồn")
    parser.add_argument("--seed", type=int, default=42, help="Seed chọn mẫu ảnh, để tái lập (R15)")
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
        print("| Mô hình | Số luồng |")
        print("|---|---|")
        for m in models:
            for t in threads_list:
                print(f"| `{m}` | {t} |")
        print(
            f"\nẢnh nguồn : `{args.anh_dir}` (n_frames={args.n_frames}, "
            f"warmup={args.warmup}, seed={args.seed})"
        )
        print(f"Thiết bị  : `{args.device_name}`\n")
        return 0

    for m in models:
        if not m.exists() or not m.is_file():
            logger.error("Không tìm thấy tệp mô hình: %s", m)
            print(f"Không tìm thấy tệp mô hình: '{m}'. Chạy scripts/export_detector.py trước.")
            return 1

    anh_dir = Path(args.anh_dir)
    so_can = args.n_frames + args.warmup
    try:
        duong_dan_anh = chon_anh(anh_dir, so_can, args.seed)
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
            detector_do_kich_thuoc = YoloFaceDetector(m, cfg)
            imgsz = detector_do_kich_thuoc.kich_thuoc_vao
            del detector_do_kich_thuoc
            imgsz_theo_mo_hinh[i] = imgsz

            for t in threads_list:
                cfg_combo = dict(cfg)
                cfg_combo["inference"] = dict(cfg.get("inference", {}))
                cfg_combo["inference"]["num_threads"] = t

                ban_ghi = do_mot_cau_hinh(m, cfg_combo, args.n_frames, anh_da_nap, args.warmup)
                for r in ban_ghi:
                    r["run_id"] = ""  # điền lại bên dưới sau khi biết run_id
                    r["backend"] = "onnx"
                    r["imgsz"] = imgsz
                    r["threads"] = t

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

    argv_hien_thi = argv if argv is not None else sys.argv[1:]
    meta: dict = {
        "run_id": run_id,
        "timestamp": thoi_diem.isoformat(),
        "git_commit": _lay_git_commit_hash(),
        "git_dirty": _kiem_tra_git_dirty(),
        "script": "scripts/benchmark_detect.py",
        "command": "python scripts/benchmark_detect.py " + " ".join(argv_hien_thi),
        "device": {
            "name": args.device_name,
            "os": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
        },
        "software": {
            "python": platform.python_version(),
            "onnxruntime": ort.__version__,
            "opencv-python": cv2.__version__,
            "numpy": np.__version__,
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
        "seed": args.seed,
        "warmup_frames": args.warmup,
        "cpu_temp_start_c": nhiet_do_bat_dau,
        "cpu_temp_max_c": nhiet_do_max,
        "duration_s": thoi_gian_chay,
        "notes": args.ghi_chu,
        "tom_tat": tom_tat,
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
