"""Khối phát hiện khuôn mặt dùng YOLOv8n-face định dạng ONNX.

Chỉ dùng `onnxruntime`, `numpy`, `cv2` — đây là khối chạy thật trên Raspberry Pi 5, không được
kéo theo `ultralytics`/`torch` (quá nặng, không có trong `requirements.txt`).

Các hằng số bố cục đầu ra và tham số letterbox dưới đây là **dữ kiện đã đo thực tế** trên chính
hai tệp `models/yolov8n-face-{320,640}.onnx`, xem `docs/dac-ta/P2-02-detector.md` §3.
"""

from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

from src.common.config import lay_gia_tri
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger
from src.common.types import FaceBox

logger = lay_logger(__name__)

# --- Hằng số cố hữu của kiến trúc YOLOv8n-face — xem docs/dac-ta/P2-02-detector.md §3 ---

# §3.3: màu nền xám chèn vào phần viền khi letterbox, không phải tham số điều chỉnh được.
MAU_NEN_LETTERBOX = 114

# §3.2: bố cục 20 kênh của output0 — 4 (cx,cy,w,h) + 1 (conf) + 5*3 (điểm mốc x,y,visibility).
SO_KENH_DAU_RA = 20

# §3.2: chỉ số kênh chứa độ tin cậy (đã ở thang [0, 1], không cần sigmoid).
CHI_SO_KENH_CONF = 4

# §3.2: điểm mốc thứ i (đếm từ 0) nằm ở kênh CHI_SO_BAT_DAU_DIEM_MOC + i*SO_GIA_TRI_MOI_DIEM_MOC.
CHI_SO_BAT_DAU_DIEM_MOC = 5
SO_GIA_TRI_MOI_DIEM_MOC = 3
SO_DIEM_MOC = 5

# Trần số luồng cho onnxruntime — Pi 5 có 4 lõi; giá trị lớn hơn chắc chắn là lỗi cấu hình,
# và làm onnxruntime ném ngoại lệ thô (bad_alloc / TypeError) thay vì LoiCauHinh.
SO_LUONG_TOI_DA = 64


def letterbox(anh: np.ndarray, kich_thuoc: int) -> tuple[np.ndarray, float, int, int]:
    """Thu ảnh về hình vuông, giữ nguyên tỉ lệ, chèn nền xám.

    BẮT BUỘC dùng cách này thay vì kéo giãn thẳng (`cv2.resize` không giữ tỉ lệ) — kéo giãn
    làm lệch khung bao khi ảnh không vuông, xem `docs/dac-ta/P2-02-detector.md` §3.3.

    Args:
        anh: Ảnh BGR, hình dạng (H, W, 3), kiểu uint8.
        kich_thuoc: Cạnh của ảnh vuông đích (kích thước đầu vào mô hình).

    Returns:
        Tuple `(ảnh_đã_letterbox, tỉ_lệ_r, dx, dy)` — `r` là tỉ lệ thu/phóng đã áp dụng,
        `dx`/`dy` là độ lệch (pixel) của vùng ảnh thật so với góc trên-trái của ảnh vuông.
    """
    chieu_cao, chieu_rong = anh.shape[:2]
    r = min(kich_thuoc / chieu_cao, kich_thuoc / chieu_rong)
    rong_moi = round(chieu_rong * r)
    cao_moi = round(chieu_cao * r)

    anh_thu_phong = cv2.resize(anh, (rong_moi, cao_moi), interpolation=cv2.INTER_LINEAR)

    nen = np.full((kich_thuoc, kich_thuoc, 3), MAU_NEN_LETTERBOX, dtype=np.uint8)
    dx = (kich_thuoc - rong_moi) // 2
    dy = (kich_thuoc - cao_moi) // 2
    nen[dy : dy + cao_moi, dx : dx + rong_moi] = anh_thu_phong

    return nen, r, dx, dy


def nms(khung: np.ndarray, diem_tin_cay: np.ndarray, nguong_iou: float) -> list[int]:
    """Gộp khung chồng lấn, giữ khung có độ tin cậy cao nhất.

    Args:
        khung: hình dạng (N, 4), thứ tự (x1, y1, x2, y2).
        diem_tin_cay: hình dạng (N,).
        nguong_iou: Ngưỡng IoU — khung có IoU với khung đang xét lớn hơn ngưỡng này bị loại.

    Returns:
        Danh sách chỉ số được giữ lại, theo thứ tự độ tin cậy giảm dần.
    """
    if khung.shape[0] == 0:
        return []

    x1, y1, x2, y2 = khung[:, 0], khung[:, 1], khung[:, 2], khung[:, 3]
    dien_tich = (x2 - x1) * (y2 - y1)

    thu_tu = np.argsort(-diem_tin_cay)
    giu_lai: list[int] = []

    while thu_tu.size > 0:
        i = int(thu_tu[0])
        giu_lai.append(i)

        if thu_tu.size == 1:
            break

        con_lai = thu_tu[1:]
        xx1 = np.maximum(x1[i], x1[con_lai])
        yy1 = np.maximum(y1[i], y1[con_lai])
        xx2 = np.minimum(x2[i], x2[con_lai])
        yy2 = np.minimum(y2[i], y2[con_lai])

        rong_giao = np.maximum(0.0, xx2 - xx1)
        cao_giao = np.maximum(0.0, yy2 - yy1)
        dien_tich_giao = rong_giao * cao_giao

        iou = dien_tich_giao / (dien_tich[i] + dien_tich[con_lai] - dien_tich_giao)
        thu_tu = con_lai[iou <= nguong_iou]

    return giu_lai


def _tien_xu_ly(anh_letterbox: np.ndarray) -> np.ndarray:
    """Chuyển ảnh BGR đã letterbox thành tensor NCHW float32 RGB thang [0, 1]."""
    anh_rgb = cv2.cvtColor(anh_letterbox, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    tensor = np.transpose(anh_rgb, (2, 0, 1))
    return np.expand_dims(tensor, axis=0)


def _lay_so_trong_khoang(
    cfg: dict, duong_dan_key: str, kieu: type, thap: float, cao: float, mac_dinh=None
) -> float:
    """Đọc một tham số số thực/nguyên trong `cfg`, kiểm kiểu và miền giá trị."""
    if mac_dinh is None:
        gia_tri = lay_gia_tri(cfg, duong_dan_key)
    else:
        gia_tri = lay_gia_tri(cfg, duong_dan_key, mac_dinh)

    # bool là subclass của int trong Python — loại trừ tường minh để không lọt True/False.
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, kieu):
        ten_kieu = (
            kieu.__name__ if isinstance(kieu, type) else " hoặc ".join(k.__name__ for k in kieu)
        )
        raise LoiCauHinh(f"Cấu hình '{duong_dan_key}' phải có kiểu {ten_kieu}, nhận {gia_tri!r}")
    if not (thap <= gia_tri <= cao):
        raise LoiCauHinh(
            f"Cấu hình '{duong_dan_key}' phải trong khoảng [{thap}, {cao}], nhận {gia_tri!r}"
        )
    return gia_tri


class YoloFaceDetector:
    """Khối phát hiện khuôn mặt dùng YOLOv8n-face định dạng ONNX."""

    def __init__(self, duong_dan_onnx: Path | str, cfg: dict) -> None:
        """Nạp mô hình ONNX và chốt tham số suy luận.

        Args:
            duong_dan_onnx: Đường dẫn tệp .onnx.
            cfg: Toàn bộ nội dung configs/detect.yaml.

        Raises:
            LoiMoHinh: tệp không tồn tại, hoặc không nạp được bằng onnxruntime.
            LoiCauHinh: thiếu key bắt buộc trong cfg, hoặc giá trị ngoài miền hợp lệ.
        """
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

        duong_dan = Path(duong_dan_onnx)
        if not duong_dan.exists() or not duong_dan.is_file():
            raise LoiMoHinh(f"Không tìm thấy tệp mô hình ONNX: {duong_dan}")

        tuy_chon = ort.SessionOptions()
        if self._num_threads > 0:
            tuy_chon.intra_op_num_threads = self._num_threads

        try:
            self._session = ort.InferenceSession(
                str(duong_dan), sess_options=tuy_chon, providers=["CPUExecutionProvider"]
            )
        except Exception as e:
            raise LoiMoHinh(f"Không nạp được mô hình ONNX từ {duong_dan}: {e}") from e

        dau_vao = self._session.get_inputs()[0]
        dau_ra = self._session.get_outputs()[0]

        so_kenh_thuc_te = dau_ra.shape[1]
        if so_kenh_thuc_te != SO_KENH_DAU_RA:
            raise LoiMoHinh(
                f"Số kênh đầu ra của {duong_dan} không đúng: kỳ vọng {SO_KENH_DAU_RA}, "
                f"nhận {so_kenh_thuc_te}"
            )

        self._ten_dau_vao = dau_vao.name
        self._kich_thuoc_vao = int(dau_vao.shape[2])

        logger.info(
            "Đã nạp mô hình detector %s (kích thước vào %d, %d luồng)",
            duong_dan,
            self._kich_thuoc_vao,
            self._num_threads,
        )

    @property
    def kich_thuoc_vao(self) -> int:
        """Cạnh ảnh đầu vào của mô hình, đọc từ đồ thị ONNX chứ không từ cfg."""
        return self._kich_thuoc_vao

    def detect(self, khung_hinh: np.ndarray) -> list[FaceBox]:
        """Phát hiện mọi khuôn mặt trong một khung hình.

        Args:
            khung_hinh: Ảnh BGR, hình dạng (H, W, 3), kiểu uint8.

        Returns:
            Danh sách FaceBox sắp xếp theo độ tin cậy GIẢM DẦN, tối đa `max_faces` phần tử.
            Toạ độ đã quy về hệ của ảnh gốc và ép về kiểu int.
            Trả về danh sách RỖNG khi không thấy khuôn mặt nào — không ném ngoại lệ.

        Raises:
            ValueError: khung_hinh sai hình dạng, sai kiểu, hoặc rỗng.
        """
        if not isinstance(khung_hinh, np.ndarray):
            # ValueError (không phải TypeError) vì đây là lỗi dữ liệu đầu vào theo hợp đồng của
            # đặc tả (docs/dac-ta/P2-02-detector.md §5, §6.5): "sai kiểu" gộp chung với
            # "sai hình dạng" — cùng mẫu với src/preprocess/align.py.
            raise ValueError(  # noqa: TRY004
                f"khung_hinh phải là numpy.ndarray, nhận kiểu {type(khung_hinh).__name__}"
            )
        if khung_hinh.ndim != 3 or khung_hinh.shape[2] != 3:
            raise ValueError(
                f"khung_hinh phải có hình dạng (H, W, 3), nhận hình dạng {khung_hinh.shape}"
            )
        if khung_hinh.dtype != np.uint8:
            raise ValueError(f"khung_hinh phải có kiểu uint8, nhận kiểu {khung_hinh.dtype}")
        if khung_hinh.shape[0] == 0 or khung_hinh.shape[1] == 0:
            raise ValueError(f"khung_hinh không được rỗng, nhận hình dạng {khung_hinh.shape}")

        cao_goc, rong_goc = khung_hinh.shape[:2]
        anh_letterbox, r, dx, dy = letterbox(khung_hinh, self._kich_thuoc_vao)
        tensor_vao = _tien_xu_ly(anh_letterbox)

        dau_ra = self._session.run(None, {self._ten_dau_vao: tensor_vao})[0]
        mang = dau_ra[0].T  # (N, SO_KENH_DAU_RA)

        diem_tin_cay = mang[:, CHI_SO_KENH_CONF]
        mat_na = diem_tin_cay >= self._conf_threshold
        mang = mang[mat_na]
        diem_tin_cay = diem_tin_cay[mat_na]

        if mang.shape[0] == 0:
            return []

        cx, cy, w, h = mang[:, 0], mang[:, 1], mang[:, 2], mang[:, 3]
        khung = np.stack(
            [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
            axis=1,
        )

        chi_so_giu = nms(khung, diem_tin_cay, self._iou_threshold)
        if not chi_so_giu:
            return []

        chi_so_giu = chi_so_giu[: self._max_faces]

        ket_qua: list[FaceBox] = []
        for i in chi_so_giu:
            x1 = round(float(np.clip((khung[i, 0] - dx) / r, 0, rong_goc)))
            y1 = round(float(np.clip((khung[i, 1] - dy) / r, 0, cao_goc)))
            x2 = round(float(np.clip((khung[i, 2] - dx) / r, 0, rong_goc)))
            y2 = round(float(np.clip((khung[i, 3] - dy) / r, 0, cao_goc)))

            diem_moc = np.empty((SO_DIEM_MOC, 2), dtype=np.float64)
            for k in range(SO_DIEM_MOC):
                cot_x = CHI_SO_BAT_DAU_DIEM_MOC + k * SO_GIA_TRI_MOI_DIEM_MOC
                diem_moc[k, 0] = (mang[i, cot_x] - dx) / r
                diem_moc[k, 1] = (mang[i, cot_x + 1] - dy) / r

            ket_qua.append(
                FaceBox(
                    x1=x1,
                    y1=y1,
                    x2=x2,
                    y2=y2,
                    confidence=float(diem_tin_cay[i]),
                    landmarks=diem_moc,
                )
            )

        logger.debug("Phát hiện %d khuôn mặt trong khung hình", len(ket_qua))
        return ket_qua
