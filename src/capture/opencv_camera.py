"""Bộ thu hình thực tế dùng OpenCV."""

import math

import cv2
import numpy as np

from src.capture.base import BoThuHinh
from src.common.exceptions import LoiCamera, LoiCauHinh
from src.common.logging import lay_logger

logger = lay_logger(__name__)

FOURCC_MAC_DINH: str = "MJPG"
DUNG_SAI_FPS: float = 0.5


def _ma_hoa_fourcc(ma: str) -> int:
    """Đổi chuỗi FOURCC 4 ký tự thành mã số nguyên theo thứ tự byte little-endian.

    Args:
        ma: Chuỗi FOURCC đúng 4 ký tự ASCII.

    Returns:
        Mã số nguyên dùng cho `cv2.CAP_PROP_FOURCC`.
    """
    return int.from_bytes(ma.encode("ascii"), "little")


def _giai_ma_fourcc(gia_tri: float) -> str:
    """Đổi mã FOURCC do OpenCV trả về thành chuỗi 4 ký tự.

    Args:
        gia_tri: Giá trị `cap.get(cv2.CAP_PROP_FOURCC)`; có thể là `0.0`, số âm hay
            giá trị vô nghĩa.

    Returns:
        Chuỗi 4 ký tự; byte không nằm trong khoảng in được thành ``"?"`` để chuỗi log
        luôn an toàn.
    """
    bon_byte = (int(gia_tri) & 0xFFFFFFFF).to_bytes(4, "little")
    return "".join(chr(b) if 0x20 <= b <= 0x7E else "?" for b in bon_byte)


class CameraOpenCV(BoThuHinh):
    """Bộ thu hình sử dụng OpenCV."""

    def __init__(self, cfg: dict) -> None:
        """Khởi tạo camera OpenCV với cấu hình.

        Args:
            cfg (dict): Nhánh `opencv` của cấu hình.

        Raises:
            LoiCauHinh: khi thiếu key bắt buộc, hoặc `fourcc`/`fps` sai định dạng.
        """
        self.cfg = cfg
        if "device_index" not in self.cfg:
            raise LoiCauHinh("Thiếu key bắt buộc: opencv.device_index")
        if "width" not in self.cfg:
            raise LoiCauHinh("Thiếu key bắt buộc: opencv.width")
        if "height" not in self.cfg:
            raise LoiCauHinh("Thiếu key bắt buộc: opencv.height")

        self._device_index = self.cfg["device_index"]
        self._width = self.cfg["width"]
        self._height = self.cfg["height"]
        self._warmup_frames = self.cfg.get("warmup_frames", 0)
        self._max_retry = self.cfg.get("max_retry", 3)

        self._fourcc = self.cfg.get("fourcc", FOURCC_MAC_DINH)
        if (
            not isinstance(self._fourcc, str)
            or len(self._fourcc) != 4
            or not all(0x20 <= ord(ky_tu) <= 0x7E for ky_tu in self._fourcc)
        ):
            raise LoiCauHinh(
                "opencv.fourcc phải là chuỗi đúng 4 ký tự ASCII in được, "
                f"đã nhận: {self._fourcc!r}"
            )

        self._fps: float | None
        if "fps" not in self.cfg:
            self._fps = None
        else:
            gia_tri_fps = self.cfg["fps"]
            if (
                isinstance(gia_tri_fps, bool)
                or not isinstance(gia_tri_fps, (int, float))
                or not math.isfinite(gia_tri_fps)
                or gia_tri_fps <= 0
            ):
                raise LoiCauHinh(f"opencv.fps phải là số hữu hạn dương, đã nhận: {gia_tri_fps!r}")
            self._fps = float(gia_tri_fps)

        self._cap = None
        self._dang_mo = False

        self._fourcc_thuc_te: str | None = None
        self._fps_thuc_te: float | None = None
        self._do_phan_giai_thuc_te: tuple[int, int] | None = None
        self._canh_bao: list[str] = []
        self._khop: bool | None = None

    def mo(self) -> None:
        """Mở thiết bị camera và áp đặt định dạng, độ phân giải, tốc độ khung yêu cầu.

        Sau khi mở, hàm dò lại thông số webcam thực sự trả về và ghi log WARNING cho
        từng thông số bị webcam từ chối im lặng. Việc bị từ chối **không** làm hàm ném
        ngoại lệ (xem `thong_so_thuc_te`).

        Raises:
            LoiCamera: khi không mở được thiết bị hoặc OpenCV ném lỗi.
        """
        try:
            self._cap = cv2.VideoCapture(self._device_index)
            if not self._cap.isOpened():
                self._cap = None
                raise LoiCamera(f"Không thể mở camera OpenCV với device_index={self._device_index}")

            # Thứ tự bốn lời gọi set là phần chịu lực: FOURCC phải chốt trước width/height;
            # FPS đặt sau vì tập tốc độ khung hợp lệ phụ thuộc cả định dạng lẫn độ phân giải.
            self._cap.set(cv2.CAP_PROP_FOURCC, _ma_hoa_fourcc(self._fourcc))
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
            if self._fps is not None:
                self._cap.set(cv2.CAP_PROP_FPS, self._fps)

            # Đọc bỏ một số khung hình ban đầu
            for _ in range(self._warmup_frames):
                ret, _ = self._cap.read()
                if not ret:
                    logger.warning("Đọc khung hình warmup thất bại")

            self._do_thong_so_thuc_te()
        except cv2.error as e:
            self._cap = None
            raise LoiCamera(f"Lỗi OpenCV khi mở device_index={self._device_index}") from e

        self._dang_mo = True
        logger.info(
            "Đã mở camera OpenCV (device_index=%s, fourcc=%s, do_phan_giai=%s, fps=%s)",
            self._device_index,
            self._fourcc_thuc_te,
            self._do_phan_giai_thuc_te,
            self._fps_thuc_te,
        )

    def _do_thong_so_thuc_te(self) -> None:
        """Đọc một khung thử, dò thông số webcam thực tế và dựng danh sách cảnh báo lệch.

        Độ phân giải thực tế đọc từ `.shape` của khung đã lấy về — **không** dùng
        `cap.get(CAP_PROP_FRAME_WIDTH/HEIGHT)`, vì `cap.get` trả lại thứ driver khai
        báo còn `.shape` trả lại thứ thật sự đến tay ứng dụng.
        """
        ret, khung = self._cap.read()
        if ret and khung is not None:
            self._do_phan_giai_thuc_te = (khung.shape[1], khung.shape[0])
        else:
            self._do_phan_giai_thuc_te = None
            logger.warning("Không lấy được khung thử sau warmup, bỏ qua bước dò độ phân giải")

        self._fourcc_thuc_te = _giai_ma_fourcc(self._cap.get(cv2.CAP_PROP_FOURCC))
        self._fps_thuc_te = float(self._cap.get(cv2.CAP_PROP_FPS))

        canh_bao: list[str] = []
        if self._fourcc_thuc_te != self._fourcc:
            canh_bao.append("fourcc")
        if self._do_phan_giai_thuc_te is not None:
            if self._do_phan_giai_thuc_te != (self._width, self._height):
                canh_bao.append("do_phan_giai")
        else:
            canh_bao.append("khong_lay_duoc_khung")
        if self._fps is not None and abs(self._fps_thuc_te - self._fps) > DUNG_SAI_FPS:
            canh_bao.append("fps")

        self._canh_bao = canh_bao
        self._khop = len(canh_bao) == 0

        yeu_cau_theo_muc = {
            "fourcc": (self._fourcc, self._fourcc_thuc_te),
            "do_phan_giai": ((self._width, self._height), self._do_phan_giai_thuc_te),
            "fps": (self._fps, self._fps_thuc_te),
        }
        for muc in canh_bao:
            if muc in yeu_cau_theo_muc:
                yeu_cau, thuc_te = yeu_cau_theo_muc[muc]
                logger.warning("Camera từ chối %s — yêu cầu %s, thực tế %s", muc, yeu_cau, thuc_te)

    def doc_frame(self) -> np.ndarray:
        """Đọc một khung hình từ camera.

        Returns:
            np.ndarray: khung hình `(height, width, 3)`, `dtype=uint8`, thứ tự kênh **BGR**.

        Raises:
            LoiCamera: khi chưa gọi `mo()` hoặc đọc thất bại.
        """
        if not self._dang_mo or self._cap is None:
            raise LoiCamera("Camera OpenCV chưa mở hoặc đã đóng")

        for thutu in range(self._max_retry):
            try:
                ret, frame = self._cap.read()
                if ret and frame is not None:
                    return frame
                logger.warning("Lỗi đọc khung hình, thử lại lần %d", thutu + 1)
            except cv2.error as e:
                raise LoiCamera("Lỗi OpenCV khi đọc khung hình") from e

        raise LoiCamera("Không thể đọc khung hình từ camera sau nhiều lần thử")

    def dong(self) -> None:
        """Giải phóng camera. An toàn khi gọi nhiều lần và khi release() lỗi.

        Các thông số đã dò trong `mo()` được **giữ nguyên** sau khi đóng để người gọi
        ghi vào `.meta.json`; lần `mo()` sau sẽ dò lại và ghi đè.
        """
        try:
            if self._cap is not None:
                self._cap.release()
        except Exception as e:  # noqa: BLE001
            logger.warning("Lỗi khi giải phóng camera: %s", e)
        finally:
            self._cap = None
            if self._dang_mo:
                self._dang_mo = False
                logger.info("Đã đóng camera OpenCV")

    @property
    def dang_mo(self) -> bool:
        """Trạng thái camera."""
        return self._dang_mo

    @property
    def thong_so_thuc_te(self) -> dict:
        """Thông số yêu cầu và thông số webcam thực sự trả về.

        Returns:
            dict: bản sao gồm đúng 8 khoá — `fourcc_yeu_cau`, `fourcc_thuc_te`,
            `fps_yeu_cau`, `fps_thuc_te`, `do_phan_giai_yeu_cau`, `do_phan_giai_thuc_te`,
            `canh_bao`, `khop`. Trả **bản sao**, không phải dict nội bộ.
        """
        return {
            "fourcc_yeu_cau": self._fourcc,
            "fourcc_thuc_te": self._fourcc_thuc_te,
            "fps_yeu_cau": self._fps,
            "fps_thuc_te": self._fps_thuc_te,
            "do_phan_giai_yeu_cau": (self._width, self._height),
            "do_phan_giai_thuc_te": self._do_phan_giai_thuc_te,
            "canh_bao": list(self._canh_bao),
            "khop": self._khop,
        }
