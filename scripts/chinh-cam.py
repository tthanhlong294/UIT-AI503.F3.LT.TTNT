"""Xem trực tiếp khung hình camera để căn góc và vạch khoảng cách trước khi đo.

Công cụ chạy tay, KHÔNG thuộc mã việc nào và KHÔNG sinh số cho báo cáo. Vì vậy nó gọi
`cv2.VideoCapture` thẳng thay vì đi qua `src.capture` — ranh giới R22 áp cho mã sản phẩm,
không áp cho công cụ căn khung. Cũng vì thế script dùng `print` thay cho `logging`.

Phải chạy trên desktop của Pi hoặc trong phiên VNC, vì `cv2.imshow` cần cửa sổ hiển thị.
Qua SSH thuần thì đặt `export DISPLAY=:0` trước.

Dùng:
    python3 scripts/chinh-cam.py            # /dev/video0
    python3 scripts/chinh-cam.py 1          # /dev/video1

Bấm `q` trong cửa sổ để thoát. Tắt hẳn script trước khi chạy benchmark, nếu không nó
vẫn giữ camera và lượt đo sẽ hỏng ngay ở bước mở thiết bị.
"""

import sys

import cv2

RONG_YEU_CAU = 1280
CAO_YEU_CAU = 720


def main() -> int:
    """Mở camera, hiển thị khung hình liên tục cho tới khi người dùng bấm `q`.

    Returns:
        `0` nếu thoát bình thường, `1` nếu không mở được camera hoặc mất khung giữa chừng.
    """
    chi_so_thiet_bi = int(sys.argv[1]) if len(sys.argv) > 1 else 0

    cap = cv2.VideoCapture(chi_so_thiet_bi)
    if not cap.isOpened():
        print(f"Không mở được camera /dev/video{chi_so_thiet_bi}.")
        print("Kiểm hai thứ:")
        print("  1. Thiết bị có tồn tại không   ->  ls -l /dev/video*")
        print("  2. Có tiến trình nào đang giữ  ->  đóng benchmark hoặc script khác rồi thử lại")
        print("Webcam USB đôi khi để ảnh thật ở /dev/video1, thử: python3 scripts/chinh-cam.py 1")
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, RONG_YEU_CAU)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAO_YEU_CAU)

    # In một lần độ phân giải THẬT đọc từ khung, không từ giá trị vừa đặt: webcam có thể
    # từ chối cap.set() mà không báo lỗi — cùng chế độ hỏng mà P2-07 §5.4 phải canh bằng
    # khoá `khop_do_phan_giai`.
    da_in_kich_thuoc = False

    print(f"Đang mở /dev/video{chi_so_thiet_bi}. Bấm q trong cửa sổ để thoát.")
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

            cv2.imshow("can khung", khung)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
