import sys
from pathlib import Path

# Thêm gốc dự án vào sys.path để cho phép chạy trực tiếp kịch bản
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import csv
import datetime
import re
import time

import cv2

from src.capture.factory import tao_bo_thu_hinh
from src.common.config import lay_gia_tri, nap_cau_hinh
from src.common.exceptions import LoiCamera, LoiCauHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)


def tao_ten_file(ma: str, pose: str, light: str, idx: int, duoi: str) -> str:
    """Sinh tên file theo quy ước: <ma>_<pose>_<light>_<idx 3 chữ số>.<duoi>

    Args:
        ma: Mã người dùng (ví dụ: u01, x02).
        pose: Tư thế khuôn mặt (frontal, left, right, up, down).
        light: Mức sáng (bright, dim).
        idx: Chỉ số đếm của ảnh.
        duoi: Định dạng file (png, jpg).

    Returns:
        str: Tên file sinh ra theo đúng quy ước.
    """
    ext = duoi.lstrip(".")
    return f"{ma}_{pose}_{light}_{idx:03d}.{ext}"


def phan_tich_ten_file(ten: str) -> tuple[str, str, str, int]:
    """Tách tên file thành (ma, pose, light, idx). Raises ValueError nếu sai quy ước.

    Args:
        ten: Tên file hoặc đường dẫn file ảnh.

    Returns:
        tuple[str, str, str, int]: Bộ (mã người, tư thế, mức sáng, chỉ số).

    Raises:
        ValueError: Nếu tên file không đúng định dạng quy ước (cần đúng 4 phần).
    """
    file_name = Path(ten).name
    stem = Path(file_name).stem
    parts = stem.split("_")
    if len(parts) != 4:
        raise ValueError(f"Tên file không đúng định dạng quy ước (cần 4 phần): {ten}")

    ma, pose, light, idx_str = parts
    try:
        idx = int(idx_str)
    except ValueError as e:
        raise ValueError(f"Chỉ số idx trong tên file không phải số hợp lệ: {idx_str}") from e

    return ma, pose, light, idx


def dem_da_co(thu_muc: Path, ma: str) -> dict[tuple[str, str], int]:
    """Đếm số ảnh đã có của một người, theo từng tổ hợp (pose, light).

    Bỏ qua file không đúng quy ước, không ném ngoại lệ.
    Thư mục không tồn tại → trả về dict rỗng.

    Args:
        thu_muc: Thư mục chứa các ảnh đã chụp.
        ma: Mã người dùng cần đếm.

    Returns:
        dict[tuple[str, str], int]: Từ điển ánh xạ (pose, light) -> số lượng ảnh.
    """
    counts: dict[tuple[str, str], int] = {}
    if not thu_muc.exists() or not thu_muc.is_dir():
        return counts

    for item in thu_muc.glob("*"):
        if not item.is_file():
            continue
        try:
            f_ma, f_pose, f_light, _ = phan_tich_ten_file(item.name)
            if f_ma == ma:
                combo = (f_pose, f_light)
                counts[combo] = counts.get(combo, 0) + 1
        except ValueError:
            continue

    return counts


def to_hop_con_thieu(
    da_co: dict[tuple[str, str], int], poses: list[str], lights: list[str], toi_thieu: int
) -> list[tuple[str, str, int]]:
    """Trả về [(pose, light, so_anh_con_thieu)] cho các tổ hợp chưa đủ. Đủ hết → list rỗng.

    Args:
        da_co: Từ điển thống kê số lượng ảnh đã có theo (pose, light).
        poses: Danh sách các tư thế cần kiểm tra.
        lights: Danh sách các mức sáng cần kiểm tra.
        toi_thieu: Số ảnh tối thiểu cho mỗi tổ hợp.

    Returns:
        list[tuple[str, str, int]]: Danh sách các tổ hợp còn thiếu và số lượng thiếu.
    """
    result: list[tuple[str, str, int]] = []
    for pose in poses:
        for light in lights:
            count = da_co.get((pose, light), 0)
            needed = toi_thieu - count
            if needed > 0:
                result.append((pose, light, needed))
    return result


def ghi_manifest(duong_dan: Path, ban_ghi: list[dict]) -> None:
    """Ghi NỐI vào manifest CSV. Tự tạo file kèm dòng tiêu đề nếu chưa có.

    Args:
        duong_dan: Đường dẫn file manifest.csv.
        ban_ghi: Danh sách các từ điển chứa bản ghi manifest.
    """
    if not ban_ghi:
        return

    fieldnames = [
        "file",
        "id",
        "pose",
        "light",
        "idx",
        "timestamp",
        "camera",
        "width",
        "height",
        "note",
    ]

    file_exists = duong_dan.exists() and duong_dan.stat().st_size > 0
    duong_dan.parent.mkdir(parents=True, exist_ok=True)

    with open(duong_dan, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(ban_ghi)


def _lay_max_idx_da_co(thu_muc: Path, ma: str, pose: str, light: str) -> int:
    """Tìm chỉ số idx lớn nhất đã tồn tại của tổ hợp (ma, pose, light)."""
    if not thu_muc.exists() or not thu_muc.is_dir():
        return 0
    max_idx = 0
    for p in thu_muc.glob("*"):
        if not p.is_file():
            continue
        try:
            f_ma, f_pose, f_light, f_idx = phan_tich_ten_file(p.name)
            if f_ma == ma and f_pose == pose and f_light == light:
                max_idx = max(max_idx, f_idx)
        except ValueError:
            continue
    return max_idx


def thu_thap(
    cfg_data: dict,
    cfg_capture: dict,
    ma: str,
    light: str,
    thu_muc_ra: Path,
    hien_thi: bool = True,
    dry_run: bool = False,
) -> list[dict]:
    """Vòng lặp thu thập cho một người ở một mức sáng.

    Trả về danh sách bản ghi manifest của các ảnh vừa chụp (rỗng nếu dry_run).

    Args:
        cfg_data: Cấu hình dữ liệu đọc từ configs/data.yaml.
        cfg_capture: Cấu hình capture đọc từ configs/capture.yaml.
        ma: Mã định danh người dùng.
        light: Mức sáng thu thập (bright hoặc dim).
        thu_muc_ra: Đường dẫn thư mục đầu ra.
        hien_thi: Có hiển thị màn hình preview hay không.
        dry_run: Chỉ in kế hoạch mà không ghi file.

    Returns:
        list[dict]: Danh sách bản ghi manifest vừa thu thập.
    """
    if dry_run:
        return []

    thu_muc_ra.mkdir(parents=True, exist_ok=True)

    poses = lay_gia_tri(cfg_data, "poses")
    min_per_combo = lay_gia_tri(cfg_data, "min_per_combo")
    image_format = lay_gia_tri(cfg_data, "image_format")
    manifest_name = lay_gia_tri(cfg_data, "manifest_name")
    capture_interval_s = float(lay_gia_tri(cfg_data, "capture_interval_s"))
    pose_switch_delay_s = float(lay_gia_tri(cfg_data, "pose_switch_delay_s"))

    da_co = dem_da_co(thu_muc_ra, ma)
    ban_ghi_list: list[dict] = []
    chua_ghi: list[dict] = []
    manifest_path = thu_muc_ra / manifest_name

    try:
        with tao_bo_thu_hinh(cfg_capture) as cam:
            ten_backend = type(cam).__name__
            if ten_backend == "CameraGiaLap":
                logger.warning(
                    "Đang thu bằng camera GIẢ LẬP — ảnh sinh ra KHÔNG phải dữ liệu thật, "
                    "chỉ dùng để kiểm thử. Thư mục: %s",
                    thu_muc_ra,
                )

            for pose in poses:
                count_exist = da_co.get((pose, light), 0)
                needed = min_per_combo - count_exist
                if needed <= 0:
                    continue

                current_idx = _lay_max_idx_da_co(thu_muc_ra, ma, pose, light) + 1

                # Hướng dẫn tư thế: LUÔN hiện bằng print (G2), bất kể hien_thi
                print(f"\n>>> Tư thế: {pose} ({light}) — cần chụp thêm {needed} ảnh.")
                print(f"    Giữ nguyên tư thế, bắt đầu sau {pose_switch_delay_s:.1f}s...")
                if pose_switch_delay_s > 0:
                    time.sleep(pose_switch_delay_s)

                user_cancelled = False
                for _ in range(needed):
                    frame = cam.doc_frame()
                    if frame is None:
                        raise LoiCamera("Khung hình trả về từ camera bằng None")

                    file_name = tao_ten_file(ma, pose, light, current_idx, image_format)
                    out_path = thu_muc_ra / file_name

                    if out_path.exists():
                        raise FileExistsError(
                            f"File đã tồn tại, tuyệt đối không ghi đè: {out_path}"
                        )

                    success = cv2.imwrite(str(out_path), frame)
                    if not success:
                        raise LoiCamera(f"Không thể ghi ảnh ra đĩa: {out_path}")

                    h, w = frame.shape[:2]
                    ts = datetime.datetime.now().astimezone().isoformat()

                    rec = {
                        "file": file_name,
                        "id": ma,
                        "pose": pose,
                        "light": light,
                        "idx": current_idx,
                        "timestamp": ts,
                        "camera": ten_backend,
                        "width": w,
                        "height": h,
                        "note": "",
                    }
                    ban_ghi_list.append(rec)
                    chua_ghi.append(rec)

                    if hien_thi:
                        cv2.imshow("Collect Faces Preview", frame)
                        key = cv2.waitKey(1) & 0xFF
                        if key == ord("q"):
                            logger.info("Người dùng bấm 'q' để ngắt thu thập.")
                            user_cancelled = True

                    # Nhịp chụp: LUÔN áp dụng, không phụ thuộc hien_thi
                    if capture_interval_s > 0:
                        time.sleep(capture_interval_s)

                    current_idx += 1
                    if user_cancelled:
                        break

                # Ghi manifest chốt sổ theo từng tư thế
                ghi_manifest(manifest_path, chua_ghi)
                chua_ghi = []

                if hien_thi:
                    try:
                        cv2.destroyAllWindows()
                    except cv2.error as e:
                        logger.debug("Không đóng được cửa sổ hiển thị: %s", e)

                if user_cancelled:
                    break
    finally:
        # Nếu gặp ngoại lệ giữa chừng (như LoiCamera hoặc Ctrl+C), ghi nốt phần manifest chưa chốt
        if chua_ghi:
            ghi_manifest(manifest_path, chua_ghi)

    return ban_ghi_list


def main() -> int:
    """Điểm vào CLI. Trả về 0 nếu thành công, 1 nếu lỗi."""
    # Đảm bảo Windows console in tiếng Việt UTF-8 không lỗi encoding khi gọi main()
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Script thu thập ảnh khuôn mặt cho hệ thống")
    parser.add_argument("--id", required=True, help="Mã người dùng (ví dụ: u01, x01)")
    parser.add_argument("--light", required=True, help="Mức sáng chụp (bright hoặc dim)")
    parser.add_argument(
        "--config-data", default="configs/data.yaml", help="Đường dẫn file configs/data.yaml"
    )
    parser.add_argument(
        "--config-capture",
        default="configs/capture.yaml",
        help="Đường dẫn file configs/capture.yaml",
    )
    parser.add_argument("--out", help="Ghi đè thư mục đầu ra")
    parser.add_argument("--no-preview", action="store_true", help="Không mở cửa sổ xem trực tiếp")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ in kế hoạch, không ghi file")

    args = parser.parse_args()

    try:
        cfg_data = nap_cau_hinh(args.config_data)
        cfg_capture = nap_cau_hinh(args.config_capture)

        id_pattern = lay_gia_tri(cfg_data, "id_pattern")
        lights = lay_gia_tri(cfg_data, "lights")
        out_dir_gallery = lay_gia_tri(cfg_data, "out_dir_gallery")
        out_dir_indomain = lay_gia_tri(cfg_data, "out_dir_indomain")
        poses = lay_gia_tri(cfg_data, "poses")
        min_per_combo = lay_gia_tri(cfg_data, "min_per_combo")
    except (LoiCauHinh, FileNotFoundError) as e:
        logger.error("Không thể đọc cấu hình: %s", e)
        return 1

    if not re.match(id_pattern, args.id):
        logger.error("Mã người dùng '--id %s' không hợp lệ với mẫu '%s'", args.id, id_pattern)
        return 1

    if args.light not in lights:
        logger.error(
            "Mức sáng '--light %s' không nằm trong danh sách hợp lệ %s", args.light, lights
        )
        return 1

    if args.out:
        thu_muc_ra = Path(args.out)
    else:
        if args.id.startswith("u"):
            out_base = out_dir_gallery
        else:
            out_base = out_dir_indomain
        thu_muc_ra = Path(out_base) / args.id

    hien_thi = not args.no_preview

    if args.dry_run:
        da_co = dem_da_co(thu_muc_ra, args.id)
        con_thieu = to_hop_con_thieu(da_co, poses, [args.light], min_per_combo)

        print("\n### BẢNG KẾ HOẠCH THU THẬP (DRY-RUN)")
        print(f"- Mã người dùng: `{args.id}`")
        print(f"- Mức sáng     : `{args.light}`")
        print(f"- Thư mục ra   : `{thu_muc_ra}`")
        print("| Tư thế | Mức sáng | Đã có | Cần chụp |")
        print("|---|---|---|---|")
        for pose in poses:
            count_exist = da_co.get((pose, args.light), 0)
            needed = max(0, min_per_combo - count_exist)
            print(f"| {pose} | {args.light} | {count_exist} | {needed} |")
        print(f"\nTổng số tổ hợp còn thiếu: {len(con_thieu)}\n")
        return 0

    try:
        ban_ghi = thu_thap(
            cfg_data=cfg_data,
            cfg_capture=cfg_capture,
            ma=args.id,
            light=args.light,
            thu_muc_ra=thu_muc_ra,
            hien_thi=hien_thi,
            dry_run=args.dry_run,
        )

        print("\n### KẾT QUẢ THU THẬP")
        print(f"- Mã người dùng   : `{args.id}`")
        print(f"- Mức sáng       : `{args.light}`")
        print(f"- Số ảnh đã chụp  : `{len(ban_ghi)}`")
        print(f"- Thư mục lưu trữ : `{thu_muc_ra}`\n")
        return 0
    except Exception as e:  # noqa: BLE001
        logger.error("Lỗi trong quá trình thu thập: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
