"""Khối phát hiện khuôn mặt dùng YOLOv8n-face định dạng NCNN.

Backend này chia sẻ toàn bộ phần hậu xử lý với backend ONNX qua `giai_ma_dau_ra` và
`_kiem_tra_khung_hinh` trong `yolo_face.py` (xem `docs/dac-ta/P2-05-detector-ncnn.md`
§6.1). Chỉ hai chỗ khác biệt: cách nạp mô hình và cách chạy một tensor qua mô hình.

Gói `ncnn` KHÔNG được import ở mức module (§6.2): container ARM64 có thể chưa có gói, và
một dòng import ở đầu tệp làm `pytest` chết ngay khâu thu thập, kéo đổ toàn bộ bộ kiểm
thử của cả repo. Vì vậy `import ncnn` chỉ nằm trong thân hàm.
"""

from pathlib import Path

import numpy as np
import yaml

from src.common.exceptions import LoiMoHinh
from src.common.logging import lay_logger
from src.common.types import FaceBox
from src.detector.yolo_face import (
    SO_LUONG_TOI_DA,
    _kiem_tra_khung_hinh,
    _lay_so_trong_khoang,
    _tien_xu_ly,
    giai_ma_dau_ra,
    letterbox,
)

logger = lay_logger(__name__)

# Tên blob vào/ra của đồ thị NCNN — đã kiểm trên model.ncnn.param (dòng 3 và dòng cuối),
# xem docs/dac-ta/P2-05-detector-ncnn.md §3. Đặt tên ở đây một lần, không rải trong thân hàm.
BLOB_VAO = "in0"
BLOB_RA = "out0"

_TEP_PARAM = "model.ncnn.param"
_TEP_BIN = "model.ncnn.bin"
_TEP_METADATA = "metadata.yaml"


def _doc_kich_thuoc_vao(tep_metadata: Path) -> int:
    """Đọc cạnh ảnh đầu vào của mô hình từ khoá `imgsz` trong metadata.yaml.

    Lấy từ metadata.yaml — do công cụ export sinh ra cùng lúc với trọng số — chứ KHÔNG
    suy từ tên thư mục, vốn chỉ là quy ước dự án và người đổi tên được. Đoán từ tên là
    loại lỗi im lặng, xem `docs/dac-ta/P2-05-detector-ncnn.md` §6.3.

    Args:
        tep_metadata: Đường dẫn tệp metadata.yaml trong thư mục NCNN.

    Returns:
        Cạnh ảnh vuông đầu vào, một số nguyên dương.

    Raises:
        LoiMoHinh: không đọc được YAML, thiếu khoá `imgsz`, hoặc `imgsz` không phải cặp
            số nguyên dương bằng nhau.
    """
    try:
        with open(tep_metadata, "r", encoding="utf-8") as f:
            noi_dung = yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        raise LoiMoHinh(f"Không đọc được {_TEP_METADATA}: {e}") from e

    if not isinstance(noi_dung, dict) or "imgsz" not in noi_dung:
        raise LoiMoHinh(f"{_TEP_METADATA} thiếu khoá bắt buộc 'imgsz'")

    imgsz = noi_dung["imgsz"]
    if not isinstance(imgsz, list) or len(imgsz) != 2:
        raise LoiMoHinh(f"{_TEP_METADATA} khoá 'imgsz' phải là cặp số, nhận {imgsz!r}")

    cao, rong = imgsz
    hai_so_nguyen = (
        isinstance(cao, int)
        and isinstance(rong, int)
        and not isinstance(cao, bool)
        and not isinstance(rong, bool)
    )
    if not hai_so_nguyen or cao <= 0 or rong <= 0:
        raise LoiMoHinh(f"{_TEP_METADATA} khoá 'imgsz' phải là số nguyên dương, nhận {imgsz!r}")
    if cao != rong:
        raise LoiMoHinh(f"{_TEP_METADATA} khoá 'imgsz' hai phần tử phải bằng nhau, nhận {imgsz!r}")

    return int(cao)


class NcnnFaceDetector:
    """Khối phát hiện khuôn mặt dùng YOLOv8n-face định dạng NCNN."""

    def __init__(self, duong_dan_thu_muc: Path | str, cfg: dict) -> None:
        """Nạp mô hình NCNN và chốt tham số suy luận.

        Args:
            duong_dan_thu_muc: Thư mục `*_ncnn_model` gồm `model.ncnn.param`,
                `model.ncnn.bin`, `metadata.yaml`.
            cfg: Toàn bộ nội dung configs/detect.yaml.

        Raises:
            LoiMoHinh: thư mục không tồn tại, thiếu tệp bắt buộc, chưa cài gói `ncnn`,
                `metadata.yaml` không đọc được hoặc thiếu/sai khoá `imgsz`.
            LoiCauHinh: thiếu key bắt buộc trong cfg, hoặc giá trị ngoài miền hợp lệ.
        """
        self._da_dong = True
        self._conf_threshold = _lay_so_trong_khoang(
            cfg, "inference.conf_threshold", (int, float), 0.0, 1.0
        )
        self._iou_threshold = _lay_so_trong_khoang(
            cfg, "inference.iou_threshold", (int, float), 0.0, 1.0
        )
        self._max_faces = int(
            _lay_so_trong_khoang(cfg, "inference.max_faces", int, 1, float("inf"))
        )
        self._num_threads = int(
            _lay_so_trong_khoang(cfg, "inference.num_threads", int, 0, SO_LUONG_TOI_DA, mac_dinh=0)
        )

        thu_muc = Path(duong_dan_thu_muc)
        if not thu_muc.is_dir():
            raise LoiMoHinh(f"Không tìm thấy thư mục mô hình NCNN: {thu_muc}")

        tep_param = thu_muc / _TEP_PARAM
        tep_bin = thu_muc / _TEP_BIN
        tep_metadata = thu_muc / _TEP_METADATA
        if not tep_param.is_file():
            raise LoiMoHinh(f"Thư mục NCNN {thu_muc} thiếu tệp bắt buộc: {_TEP_PARAM}")
        if not tep_bin.is_file():
            raise LoiMoHinh(f"Thư mục NCNN {thu_muc} thiếu tệp bắt buộc: {_TEP_BIN}")
        if not tep_metadata.is_file():
            raise LoiMoHinh(f"Thư mục NCNN {thu_muc} thiếu tệp bắt buộc: {_TEP_METADATA}")

        self._kich_thuoc_vao = _doc_kich_thuoc_vao(tep_metadata)

        try:
            import ncnn
        except ImportError as e:
            raise LoiMoHinh("Chưa cài gói 'ncnn'. Khắc phục: pip install ncnn==1.0.20260526") from e

        self._net = ncnn.Net()
        if self._num_threads > 0:
            self._net.opt.num_threads = self._num_threads
        self._net.load_param(str(tep_param))
        self._net.load_model(str(tep_bin))
        self._da_dong = False

        logger.info(
            "Đã nạp mô hình detector NCNN %s (kích thước vào %d, %d luồng)",
            thu_muc,
            self._kich_thuoc_vao,
            self._num_threads,
        )

    @property
    def kich_thuoc_vao(self) -> int:
        """Cạnh ảnh đầu vào của mô hình, đọc từ metadata.yaml chứ không từ tên thư mục."""
        return self._kich_thuoc_vao

    @property
    def ten_backend(self) -> str:
        """Tên bộ suy luận của backend này — luôn trả 'ncnn'."""
        return "ncnn"

    def detect(self, khung_hinh: np.ndarray) -> list[FaceBox]:
        """Phát hiện mọi khuôn mặt trong một khung hình.

        Giữ nguyên hợp đồng của `YoloFaceDetector.detect` — cùng đầu vào, cùng đầu ra,
        cùng ngoại lệ.

        Args:
            khung_hinh: Ảnh BGR, hình dạng (H, W, 3), kiểu uint8.

        Returns:
            Danh sách FaceBox sắp xếp theo độ tin cậy GIẢM DẦN, tối đa `max_faces` phần
            tử. Toạ độ đã quy về hệ của ảnh gốc. Danh sách RỖNG khi không thấy khuôn mặt
            nào — không ném ngoại lệ.

        Raises:
            ValueError: khung_hinh sai hình dạng, sai kiểu, hoặc rỗng.
        """
        _kiem_tra_khung_hinh(khung_hinh)

        cao_goc, rong_goc = khung_hinh.shape[:2]
        anh_letterbox, r, dx, dy = letterbox(khung_hinh, self._kich_thuoc_vao)
        tensor_nchw = _tien_xu_ly(anh_letterbox)
        # NCNN nhận tensor CHW, KHÔNG có chiều batch (§6.2). Lấy sai chỗ này thì ncnn
        # không báo lỗi mà trả về rác.
        tensor_chw = np.ascontiguousarray(tensor_nchw[0], dtype=np.float32)

        import ncnn

        with self._net.create_extractor() as ex:
            ex.input(BLOB_VAO, ncnn.Mat(tensor_chw).clone())
            _, dau_ra = ex.extract(BLOB_RA)

        mang_tho = np.array(dau_ra).T  # (SO_KENH_DAU_RA, N) -> (N, SO_KENH_DAU_RA)

        ket_qua = giai_ma_dau_ra(
            mang_tho,
            r,
            dx,
            dy,
            rong_goc,
            cao_goc,
            self._conf_threshold,
            self._iou_threshold,
            self._max_faces,
        )
        logger.debug("Phát hiện %d khuôn mặt trong khung hình", len(ket_qua))
        return ket_qua

    def close(self) -> None:
        """Giải phóng tài nguyên gốc C++ của `ncnn.Net`.

        `ncnn.Net` giữ bộ nhớ ngoài vùng quản lý của Python; bước 2.6 tạo và huỷ hàng
        chục detector trong một lần chạy nên phải giải phóng tường minh, không phó mặc
        cho bộ thu gom rác (§6.2).
        """
        if self._da_dong:
            return
        net = getattr(self, "_net", None)
        if net is not None:
            net.clear()
        self._da_dong = True

    def __del__(self) -> None:
        """Dọn tài nguyên khi đối tượng bị thu hồi — gọi lại `close`."""
        self.close()
