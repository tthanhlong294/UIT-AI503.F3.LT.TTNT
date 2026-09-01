"""Kiểm thử cho src/detector/yolo_face.py.

Ca cần mô hình ONNX thật (`models/yolov8n-face-{320,640}.onnx`) hoặc dữ liệu LFW thật được
đánh dấu và tự BỎ QUA CÓ THÔNG BÁO nếu tệp chưa có — xem `_bo_qua_neu_thieu`.

⚠️ `ultralytics` chỉ được dùng để đối chiếu ở một ca `@pytest.mark.slow`, và import BÊN TRONG
thân hàm test (không ở mức module) — nó không có trong container ARM64/`requirements.txt`.
Import ở mức module làm `pytest` chết ngay khâu thu thập, kéo đổ toàn bộ bộ test còn lại
(bài học từ `P2-01`, xem `docs/dac-ta/P2-02-detector.md` §8).
"""

import ast
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.detector.yolo_face import YoloFaceDetector, giai_ma_dau_ra, letterbox, nms

_MODEL_320 = Path("models/yolov8n-face-320.onnx")
_MODEL_640 = Path("models/yolov8n-face-640.onnx")
_LFW_ANH_MAU = Path("data/impostor/lfw_original/Aaron_Peirsol/Aaron_Peirsol_0001.jpg")
_LFW_ANH_KHAC_1 = Path("data/impostor/lfw_original/George_HW_Bush/George_HW_Bush_0001.jpg")
_LFW_ANH_KHAC_2 = Path("data/impostor/lfw_original/Nelson_Mandela/Nelson_Mandela_0001.jpg")

# Bộ số đối chứng đã kiểm chứng ngày 18/08/2026 — xem docs/dac-ta/P2-02-detector.md §3.5.
_KHUNG_DOI_CHUNG = [82.81, 66.45, 169.56, 183.96]
_CONF_DOI_CHUNG = 0.8564
_DIEM0_DOI_CHUNG = [105.36, 115.41]

# Đối chứng cho ca dòng 27 (ảnh không vuông, dựng theo §6.6 của đặc tả) — đo ngày 18/08/2026.
_KHUNG_KHONG_VUONG_DOI_CHUNG = [880.68, 368.38, 972.30, 483.01]


def _cfg_hop_le() -> dict:
    """Cấu hình hợp lệ tối giản dùng làm nền cho các ca kiểm thử biến thể lỗi."""
    return {
        "inference": {
            "conf_threshold": 0.5,
            "iou_threshold": 0.45,
            "max_faces": 10,
            "num_threads": 0,
        }
    }


def _bo_qua_neu_thieu(duong_dan: Path) -> None:
    if not duong_dan.exists():
        pytest.skip(f"chưa có {duong_dan}, chạy scripts/export_detector.py trước")


@pytest.fixture(scope="module")
def d320() -> YoloFaceDetector:
    _bo_qua_neu_thieu(_MODEL_320)
    return YoloFaceDetector(_MODEL_320, _cfg_hop_le())


@pytest.fixture(scope="module")
def d640() -> YoloFaceDetector:
    _bo_qua_neu_thieu(_MODEL_640)
    return YoloFaceDetector(_MODEL_640, _cfg_hop_le())


@pytest.fixture(scope="module")
def anh_lfw() -> np.ndarray:
    _bo_qua_neu_thieu(_LFW_ANH_MAU)
    anh = cv2.imread(str(_LFW_ANH_MAU))
    assert anh is not None
    return anh


# ============================================================================
# §6.1 — Khởi tạo (dòng 01-10)
# ============================================================================


def test_dong01_nap_model_hop_le_thanh_cong():
    _bo_qua_neu_thieu(_MODEL_320)
    YoloFaceDetector(_MODEL_320, _cfg_hop_le())  # không ném lỗi


def test_dong02_tep_khong_ton_tai_nem_loimohinh():
    with pytest.raises(LoiMoHinh):
        YoloFaceDetector(Path("khong/ton/tai.onnx"), _cfg_hop_le())


def test_dong03_tep_khong_phai_onnx_nem_loimohinh(tmp_path):
    tep_rac = tmp_path / "x.onnx"
    tep_rac.write_bytes(b"day khong phai onnx that")
    with pytest.raises(LoiMoHinh):
        YoloFaceDetector(tep_rac, _cfg_hop_le())


def test_dong04_kich_thuoc_vao_dung_320(d320):
    assert d320.kich_thuoc_vao == 320


def test_dong05_kich_thuoc_vao_dung_640(d640):
    assert d640.kich_thuoc_vao == 640


def test_dong06_thieu_conf_threshold_nem_loi():
    cfg = _cfg_hop_le()
    del cfg["inference"]["conf_threshold"]
    with pytest.raises(LoiCauHinh, match="conf_threshold"):
        YoloFaceDetector(Path("khong_can_ton_tai.onnx"), cfg)


def test_dong07_thieu_iou_threshold_nem_loi():
    cfg = _cfg_hop_le()
    del cfg["inference"]["iou_threshold"]
    with pytest.raises(LoiCauHinh, match="iou_threshold"):
        YoloFaceDetector(Path("khong_can_ton_tai.onnx"), cfg)


def test_dong08_thieu_max_faces_nem_loi():
    cfg = _cfg_hop_le()
    del cfg["inference"]["max_faces"]
    with pytest.raises(LoiCauHinh, match="max_faces"):
        YoloFaceDetector(Path("khong_can_ton_tai.onnx"), cfg)


def test_dong09_gia_tri_ngoai_mien_sau_bien_the():
    bien_the = [
        ("conf_threshold", -0.1),
        ("conf_threshold", 1.5),
        ("conf_threshold", "0.5"),
        ("max_faces", 0),
        ("max_faces", -1),
        ("max_faces", "10"),
    ]
    for khoa, gia_tri in bien_the:
        cfg = _cfg_hop_le()
        cfg["inference"][khoa] = gia_tri
        with pytest.raises(LoiCauHinh):
            YoloFaceDetector(Path("khong_can_ton_tai.onnx"), cfg)


def test_dong10_moi_loi_cau_hinh_la_loicauhinh_phu_du_bon_khoa():
    bien_the = [
        ("conf_threshold", -0.1),
        ("conf_threshold", "0.5"),
        ("iou_threshold", 1.5),
        ("iou_threshold", "0.45"),
        ("max_faces", 0),
        ("max_faces", "10"),
        ("num_threads", -1),
        ("num_threads", "2"),
        ("num_threads", 10**9),
        ("num_threads", 2**40),
    ]
    for khoa, gia_tri in bien_the:
        cfg = _cfg_hop_le()
        cfg["inference"][khoa] = gia_tri
        with pytest.raises(LoiCauHinh) as exc_info:
            YoloFaceDetector(Path("khong_can_ton_tai.onnx"), cfg)
        assert not isinstance(exc_info.value, (ValueError, TypeError))


# ============================================================================
# §6.2 — letterbox (dòng 11-17)
# ============================================================================


def test_dong11_anh_ra_luon_vuong_dung_kich_thuoc():
    ra, _r, _dx, _dy = letterbox(np.zeros((720, 1280, 3), np.uint8), 320)
    assert ra.shape == (320, 320, 3)


def test_dong12_anh_ngang_r_dx_dy_dung():
    _ra, r, dx, dy = letterbox(np.zeros((720, 1280, 3), np.uint8), 320)
    assert r == pytest.approx(0.25)
    assert dx == 0
    assert dy == (320 - 180) // 2 == 70


def test_dong13_anh_doc_hoan_doi_dung():
    _ra, r, dx, dy = letterbox(np.zeros((1280, 720, 3), np.uint8), 320)
    assert r == pytest.approx(0.25)
    assert dx == 70
    assert dy == 0


def test_dong14_anh_vuong_khong_chen_vien():
    _ra, r, dx, dy = letterbox(np.zeros((250, 250, 3), np.uint8), 320)
    assert dx == 0 and dy == 0
    assert r == pytest.approx(320 / 250)


def test_dong15_vung_chen_mang_gia_tri_114():
    ra, _r, _dx, dy = letterbox(np.zeros((720, 1280, 3), np.uint8), 320)
    assert dy == 70
    assert set(np.unique(ra[0:70, :])) == {114}


def test_dong16_anh_nho_hon_van_phong_len():
    _ra, r, _dx, _dy = letterbox(np.zeros((100, 100, 3), np.uint8), 320)
    assert r == pytest.approx(3.2)


def test_dong17_giu_nguyen_ti_le_khong_meo():
    anh = np.zeros((720, 1280, 3), np.uint8)
    anh[100:200, 200:300] = 255  # ô vuông trắng 100x100 tại (200,100)

    ra, _r, _dx, _dy = letterbox(anh, 320)

    hang_trang = np.where(np.any(ra == 255, axis=(1, 2)))[0]
    cot_trang = np.where(np.any(ra == 255, axis=(0, 2)))[0]
    chieu_cao_o = hang_trang.max() - hang_trang.min() + 1
    chieu_rong_o = cot_trang.max() - cot_trang.min() + 1

    assert abs(int(chieu_cao_o) - int(chieu_rong_o)) <= 1


# ============================================================================
# §6.3 — nms (dòng 18-22)
# ============================================================================


def test_dong18_hai_khung_trung_hoan_toan_giu_1():
    khung = np.array([[0.0, 0.0, 10.0, 10.0], [0.0, 0.0, 10.0, 10.0]])
    conf = np.array([0.9, 0.8])
    assert nms(khung, conf, 0.5) == [0]


def test_dong19_hai_khung_tach_roi_giu_ca_hai():
    khung = np.array([[0.0, 0.0, 10.0, 10.0], [50.0, 50.0, 60.0, 60.0]])
    conf = np.array([0.9, 0.8])
    assert len(nms(khung, conf, 0.5)) == 2


def test_dong20_ket_qua_sap_theo_do_tin_cay_giam_dan():
    khung = np.array(
        [
            [0.0, 0.0, 10.0, 10.0],
            [50.0, 50.0, 60.0, 60.0],
            [100.0, 100.0, 110.0, 110.0],
        ]
    )
    conf = np.array([0.3, 0.9, 0.6])
    assert nms(khung, conf, 0.5) == [1, 2, 0]


def test_dong21_nguong_co_tac_dung_that():
    khung = np.array([[0.0, 0.0, 10.0, 10.0], [5.0, 5.0, 15.0, 15.0]])
    conf = np.array([0.9, 0.8])
    assert nms(khung, conf, 0.10) == [0]
    assert nms(khung, conf, 0.20) == [0, 1]


def test_dong22_mang_rong_khong_nem_loi():
    assert nms(np.zeros((0, 4)), np.zeros((0,)), 0.5) == []


# ============================================================================
# §6.4 — detect (dòng 23-33)
# ============================================================================


def test_dong23_khung_khop_doi_chung(d320, anh_lfw):
    kq = d320.detect(anh_lfw)
    assert len(kq) >= 1
    khung_thuc_te = [kq[0].x1, kq[0].y1, kq[0].x2, kq[0].y2]
    for thuc_te, doi_chung in zip(khung_thuc_te, _KHUNG_DOI_CHUNG):
        assert abs(thuc_te - doi_chung) < 1.0


def test_dong24_do_tin_cay_khop_doi_chung(d320, anh_lfw):
    kq = d320.detect(anh_lfw)
    assert abs(kq[0].confidence - _CONF_DOI_CHUNG) < 0.01


def test_dong25_diem_moc_dau_khop_doi_chung(d320, anh_lfw):
    kq = d320.detect(anh_lfw)
    assert np.abs(kq[0].landmarks[0] - np.array(_DIEM0_DOI_CHUNG)).max() < 1.0


def test_dong26_tra_ve_dung_nam_diem_moc(d320, anh_lfw):
    kq = d320.detect(anh_lfw)
    assert kq[0].landmarks.shape == (5, 2)


def test_dong27_anh_khong_vuong_cho_ket_qua_dung(d320, anh_lfw):
    """Ca chặn lỗi kéo giãn — xem §3.3, §6.6, §7 ĐB1/ĐB1b của đặc tả.

    Dựng ảnh không vuông 1280x720, chèn khuôn mặt LFW đã biết vị trí, đối chiếu **từng cạnh**
    của khung bao với số đo bằng `ultralytics` (§6.6). Kéo giãn (kể cả kéo giãn "tự nhất quán"
    với hai hệ số tỉ lệ riêng theo trục — ĐB1b) làm méo cạnh tới ~7 px trong khi gần như không
    dịch tâm khung — vì vậy tiêu chí ở đây KHÔNG được assert tâm, chỉ assert từng cạnh.
    """
    canvas = np.full((720, 1280, 3), 128, dtype=np.uint8)
    canvas[300:550, 800:1050] = anh_lfw

    kq = d320.detect(canvas)
    assert len(kq) >= 1

    khung_thuc_te = [kq[0].x1, kq[0].y1, kq[0].x2, kq[0].y2]
    for thuc_te, doi_chung in zip(khung_thuc_te, _KHUNG_KHONG_VUONG_DOI_CHUNG):
        assert abs(thuc_te - doi_chung) < 2.0


def test_dong28_khong_co_mat_tra_ve_rong(d320):
    anh_xam = np.full((480, 640, 3), 128, dtype=np.uint8)
    assert d320.detect(anh_xam) == []


def test_dong29_thu_tu_diem_moc_dung_quy_uoc(d320, anh_lfw):
    kq = d320.detect(anh_lfw)
    lm = kq[0].landmarks
    assert lm[0][0] < lm[1][0]
    assert max(lm[0][1], lm[1][1]) < lm[2][1]
    assert lm[2][1] < min(lm[3][1], lm[4][1])
    assert lm[3][0] < lm[4][0]


def test_dong30_sap_theo_do_tin_cay_giam_dan(d320):
    _bo_qua_neu_thieu(_LFW_ANH_MAU)
    _bo_qua_neu_thieu(_LFW_ANH_KHAC_1)
    a1 = cv2.imread(str(_LFW_ANH_MAU))
    a2 = cv2.imread(str(_LFW_ANH_KHAC_1))
    canvas = np.full((700, 700, 3), 200, dtype=np.uint8)
    canvas[50:300, 50:300] = a1
    canvas[400:650, 400:650] = a2

    kq = d320.detect(canvas)
    assert len(kq) >= 2
    diem_tin_cay = [f.confidence for f in kq]
    assert diem_tin_cay == sorted(diem_tin_cay, reverse=True)


def test_dong31_ton_trong_max_faces():
    _bo_qua_neu_thieu(_MODEL_320)
    _bo_qua_neu_thieu(_LFW_ANH_MAU)
    _bo_qua_neu_thieu(_LFW_ANH_KHAC_1)
    _bo_qua_neu_thieu(_LFW_ANH_KHAC_2)

    a1 = cv2.imread(str(_LFW_ANH_MAU))
    a2 = cv2.imread(str(_LFW_ANH_KHAC_1))
    a3 = cv2.imread(str(_LFW_ANH_KHAC_2))
    canvas = np.full((900, 900, 3), 200, dtype=np.uint8)
    canvas[50:300, 50:300] = a1
    canvas[350:600, 350:600] = a2
    canvas[650:900, 650:900] = a3

    cfg = _cfg_hop_le()
    cfg["inference"]["max_faces"] = 2
    d_gioi_han = YoloFaceDetector(_MODEL_320, cfg)

    kq = d_gioi_han.detect(canvas)
    assert len(kq) <= 2


def test_dong32_toa_do_nam_trong_anh_va_la_so_nguyen(d320, anh_lfw):
    kq = d320.detect(anh_lfw)
    cao, rong = anh_lfw.shape[:2]
    assert len(kq) >= 1
    for f in kq:
        assert 0 <= f.x1 < f.x2 <= rong
        assert 0 <= f.y1 < f.y2 <= cao
        assert isinstance(f.x1, int)
        assert isinstance(f.y1, int)
        assert isinstance(f.x2, int)
        assert isinstance(f.y2, int)


def test_dong33_ban_640_phat_hien_cung_khuon_mat(d320, d640, anh_lfw):
    kq320 = d320.detect(anh_lfw)
    kq640 = d640.detect(anh_lfw)
    assert len(kq320) >= 1 and len(kq640) >= 1

    tam320 = ((kq320[0].x1 + kq320[0].x2) / 2, (kq320[0].y1 + kq320[0].y2) / 2)
    tam640 = ((kq640[0].x1 + kq640[0].x2) / 2, (kq640[0].y1 + kq640[0].y2) / 2)

    assert abs(tam320[0] - tam640[0]) < 10
    assert abs(tam320[1] - tam640[1]) < 10


# ============================================================================
# §6.5 — Đầu vào sai (dòng 34-39)
# ============================================================================


def test_dong34_khong_phai_mang_numpy_nem_valueerror(d320):
    with pytest.raises(ValueError):
        d320.detect("anh.jpg")


def test_dong35_sai_so_chieu_nem_valueerror(d320):
    with pytest.raises(ValueError):
        d320.detect(np.zeros((480, 640), dtype=np.uint8))


def test_dong36_sai_so_kenh_nem_valueerror(d320):
    with pytest.raises(ValueError):
        d320.detect(np.zeros((480, 640, 4), dtype=np.uint8))


def test_dong37_sai_kieu_du_lieu_nem_valueerror(d320):
    with pytest.raises(ValueError):
        d320.detect(np.zeros((480, 640, 3), dtype=np.float32))


def test_dong38_anh_rong_nem_valueerror(d320):
    with pytest.raises(ValueError):
        d320.detect(np.zeros((0, 0, 3), dtype=np.uint8))


def test_dong39_anh_hop_le_nho_nhat_van_chay_duoc(d320):
    kq = d320.detect(np.zeros((1, 1, 3), dtype=np.uint8))
    assert isinstance(kq, list)


# ============================================================================
# §6.6 — Ràng buộc triển khai (dòng 40-42)
# ============================================================================


def test_dong40_khong_import_ultralytics_hoac_torch():
    ma_nguon = Path("src/detector/yolo_face.py").read_text(encoding="utf-8")
    cay = ast.parse(ma_nguon)
    ten_import: list[str] = []
    for node in ast.walk(cay):
        if isinstance(node, ast.Import):
            ten_import.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            ten_import.append(node.module)

    for ten in ten_import:
        assert not ten.startswith("ultralytics")
        assert not ten.startswith("torch")


def test_dong41_num_threads_0_khong_nem_loi():
    _bo_qua_neu_thieu(_MODEL_320)
    cfg = _cfg_hop_le()
    cfg["inference"]["num_threads"] = 0
    YoloFaceDetector(_MODEL_320, cfg)  # không ném lỗi


def test_dong42_num_threads_2_ap_dung_va_ket_qua_nhu_dong23(anh_lfw):
    _bo_qua_neu_thieu(_MODEL_320)
    cfg = _cfg_hop_le()
    cfg["inference"]["num_threads"] = 2
    d = YoloFaceDetector(_MODEL_320, cfg)

    kq = d.detect(anh_lfw)
    assert len(kq) >= 1
    khung_thuc_te = [kq[0].x1, kq[0].y1, kq[0].x2, kq[0].y2]
    for thuc_te, doi_chung in zip(khung_thuc_te, _KHUNG_DOI_CHUNG):
        assert abs(thuc_te - doi_chung) < 1.0


# ============================================================================
# Đối chiếu với ultralytics (tham khảo thêm, không thuộc bảng §6 nhưng củng cố dòng 23-25)
# ============================================================================


@pytest.mark.slow
def test_doi_chieu_ultralytics_tren_anh_lfw_mau(d320, anh_lfw):
    from ultralytics import YOLO  # chỉ ca slow mới cần; container ARM64 không cài (đọc §8)

    _bo_qua_neu_thieu(Path("models/yolov8n-face.pt"))
    mo_hinh = YOLO("models/yolov8n-face.pt")
    ket_qua_pt = mo_hinh.predict(anh_lfw, imgsz=320, conf=0.5, verbose=False)[0]
    assert len(ket_qua_pt.boxes) >= 1

    khung_pt = ket_qua_pt.boxes.xyxy.cpu().numpy()[0]
    kq_onnx = d320.detect(anh_lfw)
    assert len(kq_onnx) >= 1

    for thuc_te, doi_chung in zip(
        [kq_onnx[0].x1, kq_onnx[0].y1, kq_onnx[0].x2, kq_onnx[0].y2], khung_pt
    ):
        assert abs(thuc_te - doi_chung) < 2.0


# ============================================================================
# P2-05 §7.1 — hàm module-level giai_ma_dau_ra (đã trích khỏi detect, §5.1) và ten_backend
#
# Số hàng 01-08 trong bảng §7.1 của đặc tả P2-05 ánh xạ sang các ca dưới đây;
# đánh số tiếp nối dãy test_dong<nn> sẵn có trong tệp này để không trùng tên hàm:
#   §7.1 hàng 01 -> test_dong43   §7.1 hàng 05 -> test_dong47
#   §7.1 hàng 02 -> test_dong44   §7.1 hàng 06 -> test_dong48
#   §7.1 hàng 03 -> test_dong45   §7.1 hàng 07 -> test_dong49  (mục tiêu ĐB1)
#   §7.1 hàng 04 -> test_dong46   §7.1 hàng 08 -> test_dong50
#              (mục tiêu ĐB2)
# ============================================================================


def _hang_ung_vien(
    cx: float,
    cy: float,
    w: float,
    h: float,
    conf: float,
    diem_moc: list[tuple[float, float]] | None = None,
) -> np.ndarray:
    """Dựng một hàng 20 kênh của tensor thô YOLOv8n-face.

    Bố cục kênh: 0-3 (cx, cy, w, h), 4 (conf), 5+3k / 6+3k (x, y điểm mốc thứ k),
    7+3k (visibility). Không truyền `diem_moc` thì năm điểm mốc để 0.
    """
    hang = np.zeros(20, dtype=np.float64)
    hang[0:4] = (cx, cy, w, h)
    hang[4] = conf
    if diem_moc is not None:
        for k, (px, py) in enumerate(diem_moc):
            hang[5 + k * 3] = px
            hang[5 + k * 3 + 1] = py
            hang[5 + k * 3 + 2] = 1.0
    return hang


def test_dong43_mang_rong_tra_ve_rong():
    ket_qua = giai_ma_dau_ra(np.zeros((0, 20)), 1.0, 0, 0, 100, 100, 0.5, 0.45, 10)
    assert ket_qua == []


def test_dong44_moi_ung_vien_duoi_nguong_tra_ve_rong():
    mang = np.stack([_hang_ung_vien(50, 50, 20, 20, 0.1) for _ in range(3)])
    assert giai_ma_dau_ra(mang, 1.0, 0, 0, 200, 200, 0.5, 0.45, 10) == []


def test_dong45_mot_ung_vien_hop_le_toa_do_quy_ve_anh_goc():
    diem_moc = [(100, 200), (120, 200), (110, 220), (102, 240), (118, 240)]
    mang = _hang_ung_vien(60, 60, 40, 40, 0.9, diem_moc)[None, :]

    kq = giai_ma_dau_ra(mang, 0.5, 10, 20, 1000, 1000, 0.5, 0.45, 10)

    assert len(kq) == 1
    # x1 = round((60 - 40/2 - 10) / 0.5) = 60 ; y1 = round((60 - 20 - 20) / 0.5) = 40
    # x2 = round((60 + 20 - 10) / 0.5) = 140 ; y2 = round((60 + 20 - 20) / 0.5) = 120
    assert (kq[0].x1, kq[0].y1, kq[0].x2, kq[0].y2) == (60, 40, 140, 120)
    # điểm mốc 0: ((100 - 10) / 0.5, (200 - 20) / 0.5) = (180, 360)
    assert kq[0].landmarks[0] == pytest.approx([180.0, 360.0])


def test_dong46_max_faces_cat_dung_so_luong():
    mang = np.stack([_hang_ung_vien(100 + i * 300, 100, 50, 50, 0.9 - i * 0.05) for i in range(5)])
    kq = giai_ma_dau_ra(mang, 1.0, 0, 0, 2000, 2000, 0.5, 0.45, 2)
    assert len(kq) == 2


def test_dong47_ket_qua_sap_theo_do_tin_cay_giam_dan():
    confs = [0.6, 0.9, 0.7, 0.55, 0.95]
    mang = np.stack([_hang_ung_vien(100 + i * 300, 100, 50, 50, confs[i]) for i in range(5)])
    kq = giai_ma_dau_ra(mang, 1.0, 0, 0, 2000, 2000, 0.5, 0.45, 10)
    ds_conf = [f.confidence for f in kq]
    assert ds_conf == sorted(ds_conf, reverse=True)


def test_dong48_nam_diem_moc_trich_dung_vi_tri():
    diem_moc = [(10, 20), (30, 20), (20, 35), (12, 50), (28, 50)]
    mang = _hang_ung_vien(50, 50, 40, 40, 0.9, diem_moc)[None, :]

    kq = giai_ma_dau_ra(mang, 1.0, 0, 0, 500, 500, 0.5, 0.45, 10)

    assert kq[0].landmarks.shape == (5, 2)
    assert kq[0].landmarks[2] == pytest.approx([20.0, 35.0])


def test_dong49_toa_do_bi_kep_trong_bien_anh_goc():
    mang = _hang_ung_vien(0, 0, 400, 400, 0.9)[None, :]
    kq = giai_ma_dau_ra(mang, 1.0, 0, 0, 100, 100, 0.5, 0.45, 10)
    assert len(kq) == 1
    f = kq[0]
    assert 0 <= f.x1 <= f.x2 <= 100
    assert 0 <= f.y1 <= f.y2 <= 100


def test_dong50_ten_backend_la_onnx(d320):
    assert d320.ten_backend == "onnx"
