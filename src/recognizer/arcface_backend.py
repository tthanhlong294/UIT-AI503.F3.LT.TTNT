"""Backend nhận diện dùng MobileFaceNet định dạng ONNX (phương án B).

Chỉ dùng `onnxruntime`, `numpy`, `cv2` — đây là khối chạy thật trên Raspberry Pi 5, không được
kéo theo các thư viện học sâu nặng khác (không có trong `requirements.txt`).

⚠️ Chuẩn hoá đầu vào là dữ kiện đã đo thực tế trên chính tệp mô hình, xem
`docs/dac-ta/P3-01-recognizer.md` §4.2 và `models/README.md` §3.3. Sai chuẩn hoá KHÔNG gây lỗi —
mô hình vẫn trả về đủ vectơ đặc trưng, nhưng mọi khuôn mặt trở nên gần như giống hệt nhau. Toàn bộ
tham số chuẩn hoá (thứ tự kênh, độ lệch, hệ số chia) đọc từ `configs/recognize.yaml`, không viết
cứng trong module này (xem `chuan_bi_dau_vao`).
"""

from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

# Lớp ngoại lệ cụ thể mà onnxruntime ném khi không nạp được đồ thị (tệp rác, đồ thị hỏng,
# thao tử không hỗ trợ...). onnxruntime không lộ một lớp cha chung nào khác ngoài `Exception`
# cho các trường hợp này, nên bắt đích danh từng lớp ở đây thay vì bắt `Exception` trần.
from onnxruntime.capi.onnxruntime_pybind11_state import (
    EPFail as _OrtEPFail,
)
from onnxruntime.capi.onnxruntime_pybind11_state import (
    Fail as _OrtFail,
)
from onnxruntime.capi.onnxruntime_pybind11_state import (
    InvalidArgument as _OrtInvalidArgument,
)
from onnxruntime.capi.onnxruntime_pybind11_state import (
    InvalidGraph as _OrtInvalidGraph,
)
from onnxruntime.capi.onnxruntime_pybind11_state import (
    InvalidProtobuf as _OrtInvalidProtobuf,
)
from onnxruntime.capi.onnxruntime_pybind11_state import (
    NoSuchFile as _OrtNoSuchFile,
)
from onnxruntime.capi.onnxruntime_pybind11_state import (
    RuntimeException as _OrtRuntimeException,
)

from src.common.config import lay_gia_tri
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger
from src.recognizer.base import BoNhanDien, do_tuong_dong

logger = lay_logger(__name__)

# Tập hợp lỗi nạp mô hình cụ thể của onnxruntime cần chuyển thành LoiMoHinh.
_LOI_NAP_MO_HINH_ONNX = (
    _OrtEPFail,
    _OrtFail,
    _OrtInvalidArgument,
    _OrtInvalidGraph,
    _OrtInvalidProtobuf,
    _OrtNoSuchFile,
    _OrtRuntimeException,
)

# Số kênh màu của ảnh đầu vào — luôn là 3 (BGR/RGB), không phải tham số cấu hình.
SO_KENH_MAU = 3

# Thứ tự kênh màu hợp lệ cho `channel_order` trong cấu hình.
_THU_TU_KENH_HOP_LE = ("rgb", "bgr")


def _doc_chuoi_khong_rong(cfg: dict, khoa: str) -> str:
    """Đọc một tham số kiểu chuỗi khác rỗng trong `cfg`, ném `LoiCauHinh` nếu sai."""
    gia_tri = lay_gia_tri(cfg, khoa)
    if not isinstance(gia_tri, str) or not gia_tri:
        raise LoiCauHinh(f"Cấu hình '{khoa}' phải là chuỗi khác rỗng, nhận {gia_tri!r}")
    return gia_tri


def _doc_so_thuc(cfg: dict, khoa: str) -> float:
    """Đọc một tham số kiểu số (int hoặc float) trong `cfg`, ném `LoiCauHinh` nếu sai."""
    gia_tri = lay_gia_tri(cfg, khoa)
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, (int, float)):
        raise LoiCauHinh(f"Cấu hình '{khoa}' phải là số, nhận {gia_tri!r}")
    return float(gia_tri)


def _doc_so_nguyen_duong(cfg: dict, khoa: str) -> int:
    """Đọc một tham số kiểu số nguyên dương trong `cfg`, ném `LoiCauHinh` nếu sai."""
    gia_tri = lay_gia_tri(cfg, khoa)
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, int) or gia_tri <= 0:
        raise LoiCauHinh(f"Cấu hình '{khoa}' phải là số nguyên dương, nhận {gia_tri!r}")
    return gia_tri


def _doc_kich_thuoc_dau_vao(cfg: dict) -> tuple[int, int]:
    """Đọc `input_size` — danh sách hai số nguyên dương [chiều_cao, chiều_rộng]."""
    gia_tri = lay_gia_tri(cfg, "input_size")
    hop_le = (
        isinstance(gia_tri, (list, tuple))
        and len(gia_tri) == 2
        and all(isinstance(v, int) and not isinstance(v, bool) and v > 0 for v in gia_tri)
    )
    if not hop_le:
        raise LoiCauHinh(
            "Cấu hình 'input_size' phải là danh sách hai số nguyên dương "
            f"[chiều_cao, chiều_rộng], nhận {gia_tri!r}"
        )
    return int(gia_tri[0]), int(gia_tri[1])


def _doc_thu_tu_kenh(cfg: dict) -> str:
    """Đọc `channel_order` — phải là "rgb" hoặc "bgr"."""
    gia_tri = lay_gia_tri(cfg, "channel_order")
    if not isinstance(gia_tri, str) or gia_tri.lower() not in _THU_TU_KENH_HOP_LE:
        raise LoiCauHinh(
            f"Cấu hình 'channel_order' phải là một trong {_THU_TU_KENH_HOP_LE}, nhận {gia_tri!r}"
        )
    return gia_tri.lower()


def _doc_ty_le(cfg: dict) -> float:
    """Đọc `scale` — phải là số thực lớn hơn 0."""
    gia_tri = _doc_so_thuc(cfg, "scale")
    if gia_tri <= 0:
        raise LoiCauHinh(f"Cấu hình 'scale' phải lớn hơn 0, nhận {gia_tri!r}")
    return gia_tri


def chuan_bi_dau_vao(anh: np.ndarray, cfg: dict) -> np.ndarray:
    """Chuyển ảnh BGR uint8 thành tensor đầu vào của mô hình.

    Thực hiện: đảo kênh theo `channel_order`, đổi sang float32,
    áp `(x − mean) / scale`, chuyển bố cục HWC sang NCHW.

    Args:
        anh: Ảnh BGR uint8, hình dạng (H, W, 3).
        cfg: Cấu hình chuẩn hoá, chứa các khoá `channel_order`, `mean`, `scale`.

    Returns:
        Mảng hình dạng (1, 3, H, W), kiểu float32.

    Raises:
        ValueError: ảnh sai hình dạng hoặc sai kiểu.
        LoiCauHinh: thiếu khoá hoặc giá trị ngoài miền hợp lệ.
    """
    if not isinstance(anh, np.ndarray):
        # ValueError (không phải TypeError) vì đây là lỗi dữ liệu đầu vào theo hợp đồng của
        # đặc tả (docs/dac-ta/P3-01-recognizer.md §5, §6.2): "sai kiểu" gộp chung với
        # "sai hình dạng" — cùng mẫu với src/detector/yolo_face.py.
        thong_bao_sai_kieu = f"anh phải là numpy.ndarray, nhận kiểu {type(anh).__name__}"
        raise ValueError(thong_bao_sai_kieu)  # noqa: TRY004
    if anh.ndim != 3 or anh.shape[2] != SO_KENH_MAU:
        raise ValueError(f"anh phải có hình dạng (H, W, {SO_KENH_MAU}), nhận hình dạng {anh.shape}")
    if anh.dtype != np.uint8:
        raise ValueError(f"anh phải có kiểu uint8, nhận kiểu {anh.dtype}")

    thu_tu_kenh = _doc_thu_tu_kenh(cfg)
    do_lech = _doc_so_thuc(cfg, "mean")
    ty_le = _doc_ty_le(cfg)

    if thu_tu_kenh == "rgb":
        # OpenCV đọc ảnh ra BGR — đảo kênh là BẮT BUỘC, xem docstring đầu module.
        anh_dung_kenh = cv2.cvtColor(anh, cv2.COLOR_BGR2RGB)
    else:
        anh_dung_kenh = anh

    tensor = (anh_dung_kenh.astype(np.float32) - do_lech) / ty_le
    tensor = np.transpose(tensor, (2, 0, 1))  # HWC -> CHW
    return np.expand_dims(tensor, axis=0).astype(np.float32)  # CHW -> NCHW


class ArcFaceBackend(BoNhanDien):
    """Backend nhận diện dùng mô hình MobileFaceNet định dạng ONNX (phương án B)."""

    def __init__(self, cfg: dict) -> None:
        """Nạp mô hình ONNX và chốt tham số.

        Args:
            cfg: Cấu hình backend ArcFace (mục "arcface" của configs/recognize.yaml), chứa
                các khoá: `model_path`, `embedding_dim`, `input_size`, `channel_order`,
                `mean`, `scale`.

        Raises:
            LoiMoHinh: không tìm thấy hoặc không nạp được mô hình.
            LoiCauHinh: thiếu khoá bắt buộc, hoặc `embedding_dim` trong cấu hình
                không khớp số chiều thật đọc từ đồ thị ONNX.
        """
        duong_dan_model = _doc_chuoi_khong_rong(cfg, "model_path")
        embedding_dim_cfg = _doc_so_nguyen_duong(cfg, "embedding_dim")
        kich_thuoc_vao = _doc_kich_thuoc_dau_vao(cfg)
        thu_tu_kenh = _doc_thu_tu_kenh(cfg)
        do_lech = _doc_so_thuc(cfg, "mean")
        ty_le = _doc_ty_le(cfg)

        duong_dan = Path(duong_dan_model)
        if not duong_dan.exists() or not duong_dan.is_file():
            raise LoiMoHinh(f"Không tìm thấy tệp mô hình ONNX: {duong_dan}")

        try:
            self._session = ort.InferenceSession(str(duong_dan), providers=["CPUExecutionProvider"])
        except _LOI_NAP_MO_HINH_ONNX as e:
            raise LoiMoHinh(f"Không nạp được mô hình ONNX từ {duong_dan}: {e}") from e

        dau_vao = self._session.get_inputs()[0]
        dau_ra = self._session.get_outputs()[0]

        so_chieu_thuc_te = int(dau_ra.shape[-1])
        if so_chieu_thuc_te != embedding_dim_cfg:
            raise LoiCauHinh(
                f"Cấu hình 'embedding_dim' ({embedding_dim_cfg}) không khớp số chiều thật "
                f"đọc từ đồ thị ONNX ({so_chieu_thuc_te})"
            )

        self._so_chieu = so_chieu_thuc_te
        self._ten_dau_vao = dau_vao.name
        self._kich_thuoc_vao = kich_thuoc_vao
        self._cfg_chuan_hoa = {
            "channel_order": thu_tu_kenh,
            "mean": do_lech,
            "scale": ty_le,
        }

        logger.info(
            "Đã nạp mô hình recognizer %s (số chiều đặc trưng %d)", duong_dan, self._so_chieu
        )

    @property
    def so_chieu(self) -> int:
        """Số chiều vectơ đặc trưng, đọc từ mô hình chứ không từ cấu hình."""
        return self._so_chieu

    def trich_dac_trung(self, anh: np.ndarray) -> np.ndarray:
        """Trích vectơ đặc trưng từ MỘT ảnh khuôn mặt đã căn chỉnh.

        Args:
            anh: Ảnh BGR uint8, đúng kích thước đã cấu hình ở `input_size`.

        Returns:
            Vectơ đặc trưng hình dạng (so_chieu,), kiểu float32, đã chuẩn hoá L2.

        Raises:
            ValueError: ảnh sai hình dạng, sai kiểu, hoặc rỗng.
        """
        if not isinstance(anh, np.ndarray):
            # ValueError (không phải TypeError) — xem giải trình ở chuan_bi_dau_vao() phía trên.
            thong_bao_sai_kieu = f"anh phải là numpy.ndarray, nhận kiểu {type(anh).__name__}"
            raise ValueError(thong_bao_sai_kieu)  # noqa: TRY004
        if anh.ndim != 3 or anh.shape[2] != SO_KENH_MAU:
            raise ValueError(
                f"anh phải có hình dạng (H, W, {SO_KENH_MAU}), nhận hình dạng {anh.shape}"
            )
        if anh.dtype != np.uint8:
            raise ValueError(f"anh phải có kiểu uint8, nhận kiểu {anh.dtype}")
        if (anh.shape[0], anh.shape[1]) != self._kich_thuoc_vao:
            raise ValueError(f"anh phải có kích thước {self._kich_thuoc_vao}, nhận {anh.shape[:2]}")

        tensor_vao = chuan_bi_dau_vao(anh, self._cfg_chuan_hoa)
        dau_ra = self._session.run(None, {self._ten_dau_vao: tensor_vao})[0]
        vec = dau_ra[0].astype(np.float32)

        do_dai = float(np.linalg.norm(vec))
        if do_dai == 0.0:
            raise ValueError("Vectơ đặc trưng có độ dài 0, không thể chuẩn hoá")

        return (vec / do_dai).astype(np.float32)

    def enroll(self, danh_sach_anh: list[np.ndarray], cfg: dict) -> np.ndarray:
        """Đăng ký một người từ nhiều ảnh.

        Args:
            danh_sach_anh: Danh sách ảnh khuôn mặt đã căn chỉnh của cùng một người.
            cfg: Cấu hình đăng ký (mục "enroll" của configs/recognize.yaml),
                chứa khoá `min_images_per_user`.

        Returns:
            Vectơ đặc trưng đại diện cho người đó, hình dạng (so_chieu,), đã chuẩn hoá L2.

        Raises:
            ValueError: danh sách rỗng, hoặc ít hơn `enroll.min_images_per_user`.
        """
        if not danh_sach_anh:
            raise ValueError("Danh sách ảnh đăng ký không được rỗng")

        so_anh_toi_thieu = lay_gia_tri(cfg, "min_images_per_user")
        if len(danh_sach_anh) < so_anh_toi_thieu:
            raise ValueError(
                f"Cần tối thiểu {so_anh_toi_thieu} ảnh để đăng ký một người, "
                f"chỉ nhận được {len(danh_sach_anh)}"
            )

        # Chuẩn hoá L2 TỪNG vectơ trước khi trung bình — không tin tưởng ngầm định rằng
        # trich_dac_trung() đã chuẩn hoá, tự làm lại tường minh tại đây (xem docstring lớp cha
        # BoNhanDien.enroll và docs/dac-ta/P3-01-recognizer.md §7 ĐB4).
        vec_da_chuan_hoa: list[np.ndarray] = []
        for anh in danh_sach_anh:
            vec = self.trich_dac_trung(anh)
            do_dai = float(np.linalg.norm(vec))
            if do_dai == 0.0:
                raise ValueError("Vectơ đặc trưng có độ dài 0, không thể chuẩn hoá")
            vec_da_chuan_hoa.append(vec / do_dai)

        trung_binh = np.mean(vec_da_chuan_hoa, axis=0)
        do_dai_trung_binh = float(np.linalg.norm(trung_binh))
        if do_dai_trung_binh == 0.0:
            raise ValueError("Vectơ trung bình có độ dài 0, không thể chuẩn hoá")

        logger.info("Đã đăng ký danh tính từ %d ảnh", len(danh_sach_anh))
        return (trung_binh / do_dai_trung_binh).astype(np.float32)

    def identify(
        self, anh: np.ndarray, gallery: dict[str, np.ndarray], nguong: float
    ) -> tuple[str | None, float]:
        """So khớp một khuôn mặt với danh sách đã đăng ký.

        Args:
            anh: Ảnh khuôn mặt đã căn chỉnh cần nhận diện.
            gallery: Ánh xạ mã người dùng sang vectơ đặc trưng đã đăng ký.
            nguong: Ngưỡng độ tương đồng cosin để chấp nhận một danh tính.

        Returns:
            (mã_người_dùng, độ_tương_đồng). Trả về (None, độ_tương_đồng_cao_nhất)
            khi không ai vượt ngưỡng. Với gallery rỗng, trả về (None, 0.0).
        """
        if not gallery:
            return None, 0.0

        vec = self.trich_dac_trung(anh)

        nguoi_tot_nhat: str | None = None
        diem_tot_nhat = float("-inf")
        for user_id, vec_gallery in gallery.items():
            diem = do_tuong_dong(vec, vec_gallery)
            if diem > diem_tot_nhat:
                diem_tot_nhat = diem
                nguoi_tot_nhat = user_id

        if diem_tot_nhat >= nguong:
            logger.info("Nhận diện thành công: %s (similarity=%.4f)", nguoi_tot_nhat, diem_tot_nhat)
            return nguoi_tot_nhat, diem_tot_nhat

        logger.warning("Người lạ: similarity cao nhất %.4f dưới ngưỡng %.4f", diem_tot_nhat, nguong)
        return None, diem_tot_nhat
