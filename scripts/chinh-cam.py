"""Xem trực tiếp khung hình camera, kèm khung bao khuôn mặt, để căn góc trước khi đo.

Công cụ chạy tay, KHÔNG thuộc mã việc nào và KHÔNG sinh số cho báo cáo. Vì vậy nó gọi
`cv2.VideoCapture` thẳng thay vì đi qua `src.capture` — ranh giới R22 áp cho mã sản phẩm,
không áp cho công cụ căn khung. Cũng vì thế script dùng `print` thay cho `logging`.

⚠️ Đây KHÔNG phải phép đo. Vẽ khung bao mỗi frame làm hình giật hơn hẳn lúc chạy
`benchmark_detect.py`; đừng đọc cảm giác mượt ở đây thành kết luận về hiệu năng.

Phải chạy trên desktop của Pi hoặc trong phiên VNC, vì `cv2.imshow` cần cửa sổ hiển thị.
Qua SSH thì đặt trước:
    export DISPLAY=:0 XDG_RUNTIME_DIR=/run/user/$(id -u) QT_QPA_PLATFORM=xcb

Dùng:
    python3 scripts/chinh-cam.py                      # có khung bao, /dev/video0
    python3 scripts/chinh-cam.py --thiet-bi 1         # webcam ở /dev/video1
    python3 scripts/chinh-cam.py --khong-detect       # chỉ video thô, nhẹ và mượt

Bấm `q` trong cửa sổ để thoát — phím bấm trên bàn phím cắm vào Pi, không phải trong
terminal SSH; ở terminal thì dùng Ctrl+C. Tắt hẳn script trước khi chạy benchmark, nếu
không nó vẫn giữ camera và lượt đo sẽ hỏng ngay ở bước mở thiết bị.
"""

import argparse
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.common.config import nap_cau_hinh  # noqa: E402
from src.common.exceptions import LoiCauHinh, LoiMoHinh  # noqa: E402
from src.detector import tao_bo_phat_hien  # noqa: E402

RONG_YEU_CAU = 1280
CAO_YEU_CAU = 720

MO_HINH_MAC_DINH = "models/yolov8n-face-320_ncnn_model"
CONFIG_MAC_DINH = "configs/detect.yaml"

_XANH_LA = (0, 255, 0)
_DO = (0, 0, 255)
_VANG = (0, 255, 255)


def _xay_dung_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Xem khung hình camera để căn góc trước khi đo")
    parser.add_argument("--thiet-bi", type=int, default=0, help="Chỉ số /dev/videoN (mặc định 0)")
    parser.add_argument("--mo-hinh", default=MO_HINH_MAC_DINH, help="Đường dẫn mô hình phát hiện")
    parser.add_argument("--config", default=CONFIG_MAC_DINH, help="Cấu hình khối phát hiện")
    parser.add_argument(
        "--khong-detect",
        action="store_true",
        help="Chỉ hiện video thô, không nạp mô hình — nhẹ và mượt hơn",
    )
    return parser


def _nap_bo_phat_hien(duong_dan_mo_hinh: str, duong_dan_config: str):
    """Nạp bộ phát hiện; trả về `None` nếu không nạp được.

    Không nạp được thì KHÔNG dừng chương trình: phần việc chính của script là căn hình
    học của khung, việc đó vẫn làm được bằng video thô.
    """
    try:
        cfg = nap_cau_hinh(duong_dan_config)
        bo_phat_hien = tao_bo_phat_hien(Path(duong_dan_mo_hinh), cfg)
    except (LoiCauHinh, LoiMoHinh, FileNotFoundError) as e:
        print(f"Không nạp được mô hình phát hiện: {e}")
        print("Chạy tiếp ở chế độ video thô — vẫn căn được góc và khoảng cách.")
        return None

    print(f"Đã nạp mô hình: {duong_dan_mo_hinh}")
    return bo_phat_hien


def _ve_khuon_mat(khung, khuon_mat) -> None:
    """Vẽ khung bao, độ tin cậy, chiều cao khung và điểm mốc lên ảnh, tại chỗ.

    Nhãn viết KHÔNG DẤU vì phông chữ dựng sẵn của OpenCV không có ký tự tiếng Việt —
    vẽ có dấu sẽ ra ô vuông.
    """
    for mat in khuon_mat:
        cv2.rectangle(khung, (mat.x1, mat.y1), (mat.x2, mat.y2), _XANH_LA, 2)
        nhan = f"conf {mat.confidence:.2f} | cao {mat.chieu_cao}px"
        cv2.putText(
            khung, nhan, (mat.x1, max(mat.y1 - 8, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, _XANH_LA, 1
        )
        if mat.landmarks is not None:
            for x, y in mat.landmarks[:, :2].astype(int):
                cv2.circle(khung, (int(x), int(y)), 2, _DO, -1)


def _ve_tom_tat(khung, khuon_mat) -> None:
    """Vẽ dòng tóm tắt ở góc trên trái — số mặt và chiều cao khung mặt lớn nhất."""
    if khuon_mat:
        cao_nhat = max(m.chieu_cao for m in khuon_mat)
        dong = f"mat: {len(khuon_mat)} | khung mat cao nhat: {cao_nhat}px"
        mau = _XANH_LA
    else:
        dong = "mat: 0 - khong phat hien duoc khuon mat nao"
        mau = _VANG
    cv2.putText(khung, dong, (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, mau, 2)


def main(argv: list[str] | None = None) -> int:
    """Mở camera, hiển thị khung hình liên tục cho tới khi người dùng bấm `q`.

    Returns:
        `0` nếu thoát bình thường, `1` nếu không mở được camera hoặc mất khung giữa chừng.
    """
    args = _xay_dung_parser().parse_args(argv)

    cap = cv2.VideoCapture(args.thiet_bi)
    if not cap.isOpened():
        print(f"Không mở được camera /dev/video{args.thiet_bi}.")
        print("Kiểm hai thứ:")
        print("  1. Thiết bị có tồn tại không   ->  ls -l /dev/video*")
        print("  2. Có tiến trình nào đang giữ  ->  đóng benchmark hoặc script khác rồi thử lại")
        print("Webcam USB đôi khi để ảnh thật ở video1, thử: --thiet-bi 1")
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RONG_YEU_CAU)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAO_YEU_CAU)

    bo_phat_hien = None if args.khong_detect else _nap_bo_phat_hien(args.mo_hinh, args.config)

    # In một lần độ phân giải THẬT đọc từ khung, không từ giá trị vừa đặt: webcam có thể
    # từ chối cap.set() mà không báo lỗi — cùng chế độ hỏng mà P2-07 §5.4 phải canh bằng
    # khoá `khop_do_phan_giai`.
    da_in_kich_thuoc = False

    print(f"Đang mở /dev/video{args.thiet_bi}. Bấm q trong cửa sổ để thoát.")
    try:
        while True:
            ok, khung = cap.read()
            if not ok:
                print("Mất khung hình từ camera, dừng.")
                return 1

            if not da_in_kich_thuoc:
                cao, rong = khung.shape[:2]
                print(f"Yêu cầu {RONG_YEU_CAU}x{CAO_YEU_CAU} — camera trả về {rong}x{cao}")
                if (rong, cao) != (RONG_YEU_CAU, CAO_YEU_CAU):
                    print("  ⚠️ Camera từ chối độ phân giải yêu cầu. Không sai, nhưng phải nhớ")
                    print("     con số thật này khi đọc kết quả đo.")
                da_in_kich_thuoc = True

            if bo_phat_hien is not None:
                khuon_mat = bo_phat_hien.detect(khung)
                _ve_khuon_mat(khung, khuon_mat)
                _ve_tom_tat(khung, khuon_mat)

            cv2.imshow("can khung", khung)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
