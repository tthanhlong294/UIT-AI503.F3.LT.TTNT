"""Backend nhận diện danh tính dùng mô hình ResNet của thư viện dlib — phương án A.

Đề tài so sánh định lượng hai phương án nhận diện. Module này là phương án A, đặt sau đúng
giao diện `BoNhanDien` mà phương án B (`arcface_backend.py`) đang tuân theo, để hai backend
thay thế được cho nhau ở mọi chỗ gọi.

⚠️ Tiền xử lý của hai phương án KHÁC NHAU, và đó là đặc tính chứ không phải sai lệch: mỗi mô
hình được huấn luyện với một quy ước riêng. Mô hình của dlib chờ ảnh RGB kèm kết quả dò 68 điểm
mốc, rồi TỰ căn chỉnh nội bộ theo quy ước của nó. Vì vậy module này chạy bộ dò điểm mốc trên
toàn bộ khung ảnh đã căn chỉnh do khối phát hiện cắt ra, rồi truyền cả ảnh lẫn kết quả dò cho
hàm trích đặc trưng của dlib. Tuyệt đối KHÔNG tự phóng ảnh lên kích thước riêng của dlib rồi
truyền thẳng: cách đó bỏ qua bước căn chỉnh mà mô hình được huấn luyện cùng, và hậu quả là vectơ
đặc trưng lệch có hệ thống — mô hình vẫn trả về đủ số chiều, không ngoại lệ nào được ném ra, chỉ
có độ chính xác thấp mà không rõ nguyên nhân. Xem `docs/dac-ta/P3-02-dlib-backend.md` §6.1.

Đổi kênh màu BGR sang RGB cũng là BẮT BUỘC: OpenCV đọc ảnh ra BGR, dlib chờ RGB.

Bộ dò điểm mốc chạy trên TOÀN BỘ khung ảnh, không dò lại vị trí khuôn mặt — ảnh vào đây vốn đã
là ảnh khuôn mặt do khối phát hiện cắt ra. Vì vậy nó luôn trả về đủ điểm mốc, kể cả với ảnh không
phải khuôn mặt; quyết định "có phải khuôn mặt không" thuộc khối phát hiện, không thuộc khối này
(§6.3).

Gói `dlib` KHÔNG được import ở mức module (§6.4): một dòng import ở đầu tệp làm `pytest` chết
ngay khâu thu thập trên máy chưa cài gói, kéo đổ toàn bộ bộ kiểm thử của cả repo.
"""

import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from src.common.config import lay_gia_tri
from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.common.logging import lay_logger
from src.recognizer.base import BoNhanDien, do_tuong_dong

logger = lay_logger(__name__)

# Số kênh màu của ảnh đầu vào — luôn là 3 (BGR/RGB), không phải tham số cấu hình.
SO_KENH_MAU = 3

# Cạnh của ảnh thăm dò dùng MỘT LẦN trong `__init__` để đọc số chiều thật mà mô hình trả về.
# Đây KHÔNG phải tham số nghiệp vụ: dlib tự căn chỉnh nội bộ nên số chiều đầu ra không phụ thuộc
# kích thước ảnh đưa vào. Thư viện không lộ siêu dữ liệu nào về số chiều, nên chạy thử một lần là
# cách duy nhất để `so_chieu` đến từ mô hình chứ không từ cấu hình (§5).
CANH_ANH_THAM_DO = 64

# Ngoại lệ dlib ném ra khi không nạp hoặc không chạy được mô hình (tệp rác, tệp cắt dở, sai định
# dạng). dlib không lộ lớp ngoại lệ riêng nào, nên bắt đích danh hai lớp này thay vì bắt trần.
_LOI_MO_HINH_DLIB = (RuntimeError, OSError)


def _doc_chuoi_khong_rong(cfg: dict, khoa: str) -> str:
    """Đọc một tham số kiểu chuỗi khác rỗng trong `cfg`.

    Args:
        cfg: Cấu hình cần đọc.
        khoa: Đường dẫn khoá dạng "a.b".

    Returns:
        Giá trị chuỗi đã đọc.

    Raises:
        LoiCauHinh: thiếu khoá, hoặc giá trị không phải chuỗi khác rỗng.
    """
    gia_tri = lay_gia_tri(cfg, khoa)
    if not isinstance(gia_tri, str) or not gia_tri:
        raise LoiCauHinh(f"Cấu hình '{khoa}' phải là chuỗi khác rỗng, nhận {gia_tri!r}")
    return gia_tri


def _doc_so_nguyen_duong(cfg: dict, khoa: str) -> int:
    """Đọc một tham số kiểu số nguyên dương trong `cfg`.

    Args:
        cfg: Cấu hình cần đọc.
        khoa: Đường dẫn khoá dạng "a.b".

    Returns:
        Giá trị số nguyên đã đọc.

    Raises:
        LoiCauHinh: thiếu khoá, hoặc giá trị không phải số nguyên dương.
    """
    gia_tri = lay_gia_tri(cfg, khoa)
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, int) or gia_tri <= 0:
        raise LoiCauHinh(f"Cấu hình '{khoa}' phải là số nguyên dương, nhận {gia_tri!r}")
    return gia_tri


def _doc_so_nguyen_khong_am(cfg: dict, khoa: str) -> int:
    """Đọc một tham số kiểu số nguyên không âm trong `cfg`.

    `bool` bị từ chối tường minh: trong Python `True` cũng là một `int`, nên không chặn thì
    `num_jitters: true` lọt qua phép kiểm kiểu rồi âm thầm biến thành 1.

    Args:
        cfg: Cấu hình cần đọc.
        khoa: Đường dẫn khoá dạng "a.b".

    Returns:
        Giá trị số nguyên đã đọc.

    Raises:
        LoiCauHinh: thiếu khoá, hoặc giá trị không phải số nguyên không âm.
    """
    gia_tri = lay_gia_tri(cfg, khoa)
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, int) or gia_tri < 0:
        raise LoiCauHinh(f"Cấu hình '{khoa}' phải là số nguyên không âm, nhận {gia_tri!r}")
    return gia_tri


def _kiem_tra_tep(duong_dan: str, mo_ta: str) -> Path:
    """Kiểm tra một tệp trọng số có tồn tại không.

    Args:
        duong_dan: Đường dẫn tệp cần kiểm tra.
        mo_ta: Tên gọi của tệp, dùng trong thông báo lỗi.

    Returns:
        Đường dẫn đã kiểm tra.

    Raises:
        LoiMoHinh: tệp không tồn tại hoặc không phải tệp thường.
    """
    duong_dan_path = Path(duong_dan)
    if not duong_dan_path.exists() or not duong_dan_path.is_file():
        raise LoiMoHinh(f"Không tìm thấy {mo_ta}: {duong_dan_path}")
    return duong_dan_path


def _kiem_tra_anh(anh: Any) -> None:
    """Kiểm tra ảnh đầu vào theo đúng hợp đồng của `BoNhanDien.trich_dac_trung`.

    Args:
        anh: Đối tượng cần kiểm tra, kỳ vọng là ảnh BGR uint8 hình dạng (H, W, 3).

    Raises:
        ValueError: sai kiểu, sai hình dạng, sai dtype, hoặc ảnh rỗng.
    """
    if not isinstance(anh, np.ndarray):
        # ValueError (không phải TypeError) để giữ nguyên hợp đồng của base.py và của
        # arcface_backend.py: "sai kiểu" gộp chung với "sai hình dạng".
        thong_bao_sai_kieu = f"anh phải là numpy.ndarray, nhận kiểu {type(anh).__name__}"
        raise ValueError(thong_bao_sai_kieu)  # noqa: TRY004
    if anh.ndim != 3 or anh.shape[2] != SO_KENH_MAU:
        raise ValueError(f"anh phải có hình dạng (H, W, {SO_KENH_MAU}), nhận hình dạng {anh.shape}")
    if anh.dtype != np.uint8:
        raise ValueError(f"anh phải có kiểu uint8, nhận kiểu {anh.dtype}")
    if anh.size == 0:
        raise ValueError(f"anh rỗng, hình dạng {anh.shape}")


def _chuan_hoa_l2(vec: np.ndarray) -> np.ndarray:
    """Chuẩn hoá L2 một vectơ đặc trưng.

    Args:
        vec: Vectơ cần chuẩn hoá.

    Returns:
        Vectơ cùng hướng, độ dài bằng 1, kiểu float32.

    Raises:
        ValueError: vectơ có độ dài bằng 0 hoặc không hữu hạn.
    """
    do_dai = float(np.linalg.norm(vec))
    if not math.isfinite(do_dai) or do_dai == 0.0:
        raise ValueError("Vectơ đặc trưng có độ dài 0, không thể chuẩn hoá")
    return (vec / do_dai).astype(np.float32)


class DlibFaceRecognizer(BoNhanDien):
    """Khối nhận diện danh tính dùng mô hình ResNet của dlib — phương án A."""

    def __init__(self, cfg: dict) -> None:
        """Nạp hai mô hình dlib và chốt tham số.

        Cả hai mô hình được nạp ĐÚNG MỘT LẦN tại đây (§6.5): bộ dò điểm mốc nặng gần 100 MB,
        nạp lại trong mỗi lần trích đặc trưng sẽ biến phép đo tốc độ ở Cổng C thành phép đo
        thời gian đọc đĩa chứ không phải thời gian inference.

        Args:
            cfg: Toàn bộ nội dung configs/recognize.yaml.

        Raises:
            LoiMoHinh: chưa cài gói `dlib`, tệp trọng số không tồn tại, không nạp được,
                hoặc số chiều thật của mô hình lệch `dlib.embedding_dim` trong cấu hình.
            LoiCauHinh: thiếu khoá bắt buộc, hoặc giá trị ngoài miền hợp lệ.
        """
        duong_dan_model = _doc_chuoi_khong_rong(cfg, "dlib.model_path")
        duong_dan_shape = _doc_chuoi_khong_rong(cfg, "dlib.shape_predictor")
        so_chieu_cau_hinh = _doc_so_nguyen_duong(cfg, "dlib.embedding_dim")
        self._num_jitters = _doc_so_nguyen_khong_am(cfg, "dlib.num_jitters")

        # Import nằm trong thân hàm (§6.4). Phép kiểm gói đặt TRƯỚC phép kiểm tệp để các ca
        # kiểm thử không cần trọng số thật vẫn chạy được trong container ARM64 — nơi có gói
        # dlib nhưng không có thư mục models/.
        try:
            import dlib
        except ImportError as e:
            raise LoiMoHinh("Chưa cài gói 'dlib'. Khắc phục: pip install dlib-bin==20.0.1") from e

        tep_model = _kiem_tra_tep(duong_dan_model, "tệp trọng số mô hình nhận diện dlib")
        tep_shape = _kiem_tra_tep(duong_dan_shape, "tệp bộ dò điểm mốc dlib")

        self._dlib = dlib
        try:
            self._bo_do_diem_moc = dlib.shape_predictor(str(tep_shape))
            self._mo_hinh = dlib.face_recognition_model_v1(str(tep_model))
        except _LOI_MO_HINH_DLIB as e:
            raise LoiMoHinh(f"Không nạp được mô hình dlib từ {tep_model} / {tep_shape}: {e}") from e

        so_chieu_thuc_te = self._do_so_chieu_that()
        if so_chieu_thuc_te != so_chieu_cau_hinh:
            raise LoiMoHinh(
                f"Cấu hình 'dlib.embedding_dim' ({so_chieu_cau_hinh}) không khớp số chiều thật "
                f"mà mô hình trả về ({so_chieu_thuc_te})"
            )

        self._so_chieu = so_chieu_thuc_te
        logger.info(
            "Đã nạp mô hình recognizer dlib %s (số chiều đặc trưng %d, num_jitters %d)",
            tep_model,
            self._so_chieu,
            self._num_jitters,
        )

    def _do_so_chieu_that(self) -> int:
        """Chạy mô hình một lần trên ảnh thăm dò để đọc số chiều thật của vectơ đặc trưng.

        Returns:
            Số chiều vectơ đặc trưng mà mô hình thật sự trả về.

        Raises:
            LoiMoHinh: mô hình đã nạp nhưng không chạy được.
        """
        anh_tham_do = np.zeros((CANH_ANH_THAM_DO, CANH_ANH_THAM_DO, SO_KENH_MAU), dtype=np.uint8)
        try:
            return int(self._chay_mo_hinh(anh_tham_do).shape[0])
        except _LOI_MO_HINH_DLIB as e:
            raise LoiMoHinh(f"Mô hình dlib đã nạp nhưng không chạy được: {e}") from e

    def _chay_mo_hinh(self, anh_rgb: np.ndarray) -> np.ndarray:
        """Chạy bộ dò điểm mốc rồi trích vectơ đặc trưng THÔ, chưa chuẩn hoá.

        Bộ dò điểm mốc chạy trên toàn bộ khung ảnh; dlib nhận cả ảnh lẫn kết quả dò rồi TỰ căn
        chỉnh nội bộ theo quy ước của nó (§6.1).

        Args:
            anh_rgb: Ảnh RGB uint8, hình dạng (H, W, 3).

        Returns:
            Vectơ đặc trưng thô, kiểu float32, chưa chuẩn hoá L2.
        """
        cao, rong = anh_rgb.shape[:2]
        vung_khuon_mat = self._dlib.rectangle(0, 0, rong, cao)
        diem_moc = self._bo_do_diem_moc(anh_rgb, vung_khuon_mat)
        mo_ta = self._mo_hinh.compute_face_descriptor(anh_rgb, diem_moc, self._num_jitters)
        return np.asarray(mo_ta, dtype=np.float32)

    @property
    def so_chieu(self) -> int:
        """Số chiều vectơ đặc trưng, đọc từ mô hình chứ không từ cấu hình."""
        return self._so_chieu

    def trich_dac_trung(self, anh: np.ndarray) -> np.ndarray:
        """Trích vectơ đặc trưng từ MỘT ảnh khuôn mặt đã căn chỉnh.

        Args:
            anh: Ảnh BGR uint8, hình dạng (H, W, 3).

        Returns:
            Vectơ đặc trưng hình dạng (so_chieu,), kiểu float32,
            **đã chuẩn hoá L2** — độ dài bằng 1.

        Raises:
            ValueError: ảnh sai hình dạng, sai kiểu, hoặc rỗng.
        """
        _kiem_tra_anh(anh)

        # Đảo kênh là BẮT BUỘC: OpenCV đọc ảnh ra BGR, dlib chờ RGB (§6.1).
        anh_rgb = cv2.cvtColor(anh, cv2.COLOR_BGR2RGB)

        return _chuan_hoa_l2(self._chay_mo_hinh(anh_rgb))

    def enroll(self, danh_sach_anh: list[np.ndarray], cfg: dict) -> np.ndarray:
        """Đăng ký một người từ nhiều ảnh.

        Chuẩn hoá L2 TỪNG vectơ trước, rồi lấy trung bình, rồi chuẩn hoá L2 lần nữa.

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
        # BoNhanDien.enroll). Giữ đúng cách làm của arcface_backend.py để hai phương án so
        # sánh được công bằng ở Cổng C.
        vec_da_chuan_hoa = [_chuan_hoa_l2(self.trich_dac_trung(anh)) for anh in danh_sach_anh]

        trung_binh = np.mean(vec_da_chuan_hoa, axis=0)
        logger.info("Đã đăng ký danh tính từ %d ảnh", len(danh_sach_anh))
        return _chuan_hoa_l2(trung_binh)

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
            khi không ai vượt ngưỡng — người lạ.
            Với gallery rỗng, trả về (None, 0.0).
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
