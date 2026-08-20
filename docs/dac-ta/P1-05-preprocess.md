# P1-05-preprocess — Mẻ tiền xử lý: detect → lọc → căn chỉnh → 112×112

> Mã việc: `P1-05-preprocess` · Bước **1.9** trong `CLAUDE.md` §5 Phase 1
> Nhánh: `feat/p1-05-preprocess` · Đặc tả viết ngày 19/08/2026
> Phụ thuộc: `P1-04` (`src/preprocess/align.py`) và `P2-02` (`src/detector/yolo_face.py`), đều đã gộp

---

## 1. Mục tiêu

Viết `scripts/preprocess.py` — chạy một mẻ qua cả thư mục ảnh, với mỗi ảnh: phát hiện khuôn mặt,
lọc bỏ trường hợp không tin cậy, căn chỉnh về **112×112**, ghi ra `data/processed/` giữ nguyên
cấu trúc và tên tệp nguồn, kèm `manifest.csv` ghi lại số phận từng ảnh.

Áp dụng **đồng nhất** cho cả bốn nguồn dữ liệu (gallery, LFW gốc, LFW đã domain-adapt, in-domain).
Dùng chung một quy trình là điều kiện để phép kiểm chứng domain adaptation ở Phase 3 có giá trị —
xem cảnh báo trong `configs/data.yaml`.

Hiện chỉ có **LFW gốc** (1 680 danh tính, 9 164 ảnh) là chạy được. Ba nguồn kia chờ camera.

---

## 2. Phạm vi file — danh sách trắng

| File | Trạng thái | Vai trò |
|---|---|---|
| `scripts/preprocess.py` | tạo mới | Script CLI |
| `tests/test_preprocess.py` | tạo mới | Bộ kiểm thử |

**Không sửa**: `src/**`, `configs/**`, `requirements.txt`, `docs/**`, `.claude/**`.
Thiếu tham số trong `configs/preprocess.yaml` → **dừng và báo**, không tự thêm key.

---

## 3. ⚠️ RÀNG BUỘC QUAN TRỌNG NHẤT — phân biệt hai loại lỗi

Đây là điều kiện tiên quyết của mã việc này. Làm sai chỗ này thì mọi thứ khác vô nghĩa.

| Loại lỗi | Ném từ đâu | Nghĩa là gì | Mẻ phải làm gì |
|---|---|---|---|
| `ValueError` | `align.can_chinh`, `detector.detect` | **Một ảnh** hỏng: sai hình dạng, sai kiểu, ảnh rỗng | **Bỏ qua ảnh đó**, ghi lý do vào manifest, **chạy tiếp** |
| `LoiCauHinh` | `align`, `detector`, hàm đọc config | **Cấu hình sai** — áp cho MỌI ảnh | **Dừng cả mẻ ngay**, trả về `1` |
| `LoiMoHinh` | `YoloFaceDetector.__init__` | Không nạp được mô hình | **Dừng cả mẻ ngay**, trả về `1` |

**TUYỆT ĐỐI KHÔNG bắt `except Exception` bao trùm.** Bắt gộp sẽ biến một lỗi cấu hình thành
"bỏ qua ảnh này" và mẻ vẫn chạy hết 9 164 ảnh, ghi ra 9 164 dòng `bo_qua` — **trôi im lặng cả
mẻ mà không có dấu hiệu nào báo**. Người dùng chỉ phát hiện khi mở `data/processed/` thấy rỗng.

Ba vòng review của `P1-04` dựng riêng 50 cấu hình hỏng để bảo đảm mọi lỗi cấu hình đều ném
`LoiCauHinh` chứ không phải `ValueError`. Bắt gộp ở đây sẽ xoá sạch công sức đó.

---

## 4. Dữ kiện đã kiểm chứng — dùng luôn, đừng đoán lại

| Dữ kiện | Giá trị | Đo ngày |
|---|---|---|
| Thứ tự 5 điểm mốc của detector | mắt trái · mắt phải · mũi · khoé miệng trái · khoé miệng phải | 17/08 |
| Thứ tự này so với `configs/preprocess.yaml` | **trùng khớp** — nối thẳng, **không hoán vị** | 17/08 |
| Tỉ lệ phát hiện trên LFW | 60/60 ảnh ngẫu nhiên | 17/08 |
| Bốn bất biến hình học điểm mốc | đúng 60/60 | 17/08 |
| `align.can_chinh` với điểm mốc **thẳng hàng phân biệt** | **KHÔNG báo lỗi** — vẫn trả ảnh 112×112 | 18/08 |
| `align.can_chinh` với 5 điểm mốc **trùng nhau** | ném `LoiCauHinh` | 18/08 |
| Tốc độ detect trên PC, imgsz 320 | ~32–48 ms mỗi ảnh tuỳ nhiệt độ máy | 18–19/08 |

Dòng thứ năm là lý do §5 cần bộ lọc hình học: **`align.py` không tự bảo vệ được**.
9 164 ảnh × ~40 ms ≈ **7 phút** cho một mẻ LFW đầy đủ.

---

## 5. Giao diện dòng lệnh

```
python scripts/preprocess.py --vao VAO --ra RA [--model MODEL]
                             [--config-preprocess CFG1] [--config-detect CFG2]
                             [--gioi-han N] [--seed SEED] [--tiep-tuc] [--dry-run]
```

| Cờ | Mặc định | Ý nghĩa |
|---|---|---|
| `--vao` | *(bắt buộc)* | Thư mục ảnh nguồn, ví dụ `data/impostor/lfw_original` |
| `--ra` | *(bắt buộc)* | Thư mục đích, ví dụ `data/processed/lfw_original` |
| `--model` | `models/yolov8n-face-320.onnx` | Tệp ONNX dùng để phát hiện |
| `--config-preprocess` | `configs/preprocess.yaml` | Cấu hình căn chỉnh và lọc |
| `--config-detect` | `configs/detect.yaml` | Cấu hình bộ phát hiện |
| `--gioi-han` | `0` (không giới hạn) | Chỉ xử lý N ảnh đầu — để chạy thử nhanh |
| `--seed` | `42` | Seed khi `--gioi-han` chọn mẫu (R15) |
| `--tiep-tuc` | tắt | Bỏ qua ảnh đã có trong thư mục đích, chạy tiếp mẻ dở |
| `--dry-run` | tắt | Chỉ in kế hoạch, **không ghi tệp nào** |

`--tiep-tuc` cần thiết vì một mẻ LFW mất khoảng 7 phút; đứt giữa chừng mà phải làm lại từ đầu
là lãng phí.

---

## 6. Giao diện hàm

```python
def liet_ke_anh(thu_muc: Path) -> list[Path]:
    """Liệt kê mọi ảnh trong thư mục, đệ quy, sắp xếp ổn định.

    Nhận các đuôi .jpg, .jpeg, .png (không phân biệt hoa thường).

    Raises:
        LoiCauHinh: thư mục không tồn tại, hoặc không có ảnh nào.
    """

def kiem_hinh_hoc_diem_moc(diem_moc: np.ndarray, min_ti_le_lech_mui: float) -> bool:
    """Kiểm NĂM điều kiện hình học của 5 điểm mốc.

    Bốn bất biến thứ tự, xem §4:
      1. diem_moc[0][0] < diem_moc[1][0]        (mắt trái bên trái mắt phải)
      2. max(mắt trái y, mắt phải y) < mũi y     (hai mắt trên mũi)
      3. mũi y < min(miệng trái y, miệng phải y) (mũi trên miệng)
      4. diem_moc[3][0] < diem_moc[4][0]        (khoé miệng trái bên trái khoé phải)

    Điều kiện thứ NĂM — chống suy biến:
      5. khoảng cách vuông góc từ mũi tới đường nối hai mắt, chia cho khoảng cách
         giữa hai mắt, phải `>= min_ti_le_lech_mui`.

    ⚠️ Bốn điều đầu là ĐIỀU KIỆN CẦN nhưng KHÔNG ĐỦ. Đã kiểm 19/08/2026: bộ điểm thẳng
    hàng theo đường chéo `[[0,0],[1,1],[2,2],[3,3],[4,4]]` **thoả cả bốn**. Chỉ điều kiện
    thứ năm bắt được nó (tỉ số 0,0000 so với 0,5715 của mặt chuẩn).

    Returns:
        True nếu thoả cả năm, False nếu vi phạm bất kỳ điều nào.

    Raises:
        ValueError: diem_moc sai hình dạng (phải là (5, 2)); hoặc hai mắt trùng nhau
            khiến mẫu số bằng 0.
    """

def xu_ly_mot_anh(
    duong_dan: Path, detector, cfg_preprocess: dict,
) -> tuple[np.ndarray | None, str, dict]:
    """Xử lý MỘT ảnh: đọc, phát hiện, lọc, căn chỉnh.

    Returns:
        (ảnh_đã_căn_chỉnh, lý_do, thông_tin).
        `ảnh_đã_căn_chỉnh` là None khi ảnh bị bỏ qua.
        `lý_do` là một trong sáu chuỗi ở §7.
        `thông_tin` gồm `n_faces`, `conf`, `bbox_w`, `bbox_h` (rỗng khi không áp dụng).

    KHÔNG ném ngoại lệ cho lỗi dữ liệu của một ảnh — trả về lý do.
    Ngoại lệ cấu hình (`LoiCauHinh`) thì để nó lan lên trên, KHÔNG bắt.
    """

def ghi_manifest(duong_dan: Path, ban_ghi: list[dict]) -> None:
    """Ghi manifest.csv.

    Raises:
        LoiCauHinh: bản ghi thiếu khoá bắt buộc.
    """

def main(argv: list[str] | None = None) -> int:
    """Điểm vào CLI. Trả về 0 thành công, 1 thất bại."""
```

---

## 7. Sáu lý do — bảng chốt, không được thêm bớt

Cột `ly_do` trong manifest chỉ nhận **đúng sáu** giá trị:

| Giá trị | Khi nào | Ảnh có được ghi ra không |
|---|---|---|
| `ok` | Xử lý thành công | **có** |
| `khong_doc_duoc_anh` | `cv2.imread` trả `None` — tệp hỏng hoặc không phải ảnh | không |
| `khong_thay_mat` | `detect` trả danh sách rỗng | không |
| `mat_qua_nho` | Cạnh nhỏ nhất của khung bao < `min_bbox_px` | không |
| `do_tin_cay_thap` | `confidence` < `min_confidence` | không |
| `diem_moc_bat_thuong` | `kiem_hinh_hoc_diem_moc` trả `False` | không |

Khi có **nhiều khuôn mặt**: lấy khuôn mặt có **diện tích khung bao lớn nhất**
(`chieu_rong × chieu_cao`). Bằng nhau thì lấy khuôn mặt có độ tin cậy cao hơn.
Ghi số lượng thật vào cột `n_faces`. Không bỏ qua ảnh chỉ vì có nhiều mặt.

> ⚠️ **Bản đặc tả đầu ghi "lấy độ tin cậy cao nhất" — SAI, đã sửa 20/08/2026.**
> Review vòng 1 đo trên mẻ thật: luật đó chọn **nhầm người ở 5/198 ảnh**. Một khuôn mặt hậu cảnh
> bị mép ảnh cắt cụt thắng khuôn mặt chính **lớn gấp 2–3 lần**, chênh độ tin cậy chỉ
> **0,001–0,036**. Trong 198 ảnh thành công có **47 ảnh nhiều mặt** — gần một phần tư, nên đây
> không phải trường hợp hiếm.
>
> Nguyên nhân: **độ tin cậy đo chất lượng phát hiện, không đo mức quan trọng của đối tượng.**
> Một khuôn mặt nhỏ, rõ nét, ở hậu cảnh hoàn toàn có thể đạt độ tin cậy ngang khuôn mặt chính.
>
> Diện tích thì phân tách rõ: mặt chính lớn gấp 2–3 lần theo cạnh, tức **4–9 lần theo diện tích**.
> Luật này cũng đúng với ảnh camera của hệ thống — người đứng trước camera luôn gần nhất, nên
> khuôn mặt lớn nhất.
>
> Hậu quả nếu không sửa: `data/processed/` là đầu vào sinh embedding ở Phase 3. Ghi nhầm mặt
> người lạ vào thư mục của một danh tính làm hỏng chính con số FAR mà đồ án lấy làm trọng tâm.

**Thứ tự kiểm là đúng thứ tự các dòng trong bảng trên**, từ trên xuống. Ảnh vi phạm nhiều điều
kiện thì nhận lý do của điều kiện **kiểm trước nhất**. Quy định thứ tự để bảng lý do xác định
được, không phụ thuộc cách cài đặt — nếu không thì cùng một ảnh có thể nhận hai lý do khác nhau
ở hai lần chạy, và thống kê ở bước 1.10 mất ý nghĩa.

---

## 8. Đầu ra

### Ảnh

`<ra>/<danh_tinh>/<ten_tep_goc>.png` — **phản chiếu đúng cấu trúc và tên** thư mục nguồn,
nhưng **đuôi luôn là `.png`** kể cả khi nguồn là `.jpg`.

Lý do dùng PNG: `docs/quy-uoc-du-lieu.md` §6 — ảnh đã nén một lần rồi nén tiếp sẽ chồng nhiễu,
làm hỏng phép đo độ nét ở bước 1.7 và che dấu vết tấn công của bộ spoof.

Mọi ảnh ra **đúng `output_size` trong config**, mặc định 112×112.

### `<ra>/manifest.csv`

```csv
file_vao,file_ra,ly_do,n_faces,conf,bbox_w,bbox_h
```

- `file_vao`, `file_ra` — đường dẫn **tương đối** so với `--vao` và `--ra`, dùng dấu `/`
  (dùng `Path.as_posix()`) để manifest giống nhau trên Windows và Linux.
- `file_ra` rỗng khi ảnh bị bỏ qua.
- Mỗi ảnh trong `--vao` có **đúng một** dòng, kể cả ảnh bị bỏ qua.

### Bảng tổng kết in ra màn hình

Đếm theo từng lý do, kèm tỉ lệ thành công. Đây là thứ người dùng nhìn để biết mẻ có ổn không.

---

## 9. Bảng tiêu chí nghiệm thu

Mỗi dòng là một ca test tên `test_dong<nn>` trong `tests/test_preprocess.py`.

### 9.1. Liệt kê ảnh

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Liệt kê đệ quy, tìm ảnh trong thư mục con | Cây 2 thư mục × 3 ảnh ⇒ `len(liet_ke_anh(d)) == 6` |
| 02 | Nhận cả `.jpg`, `.jpeg`, `.png` | Ba tệp ba đuôi ⇒ `len(...) == 3` |
| 03 | Không phân biệt hoa thường ở đuôi | `a.JPG`, `b.PNG` ⇒ `len(...) == 2` |
| 04 | Bỏ qua tệp không phải ảnh | Thêm `manifest.csv`, `note.txt` ⇒ số lượng không đổi |
| 05 | Thứ tự **ổn định** giữa hai lần gọi | `liet_ke_anh(d) == liet_ke_anh(d)` |
| 06 | Thư mục không tồn tại → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` |
| 07 | Thư mục rỗng → `LoiCauHinh`, thông báo **khác** dòng 06 | Thông báo chứa `không có ảnh` |

### 9.2. Kiểm hình học điểm mốc

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 08 | Điểm mốc khuôn mặt thật → `True` | Dùng `reference_landmarks` của `configs/preprocess.yaml` ⇒ `True` |
| 09 | Vi phạm bất biến 1 (mắt trái sang phải mắt phải) → `False` | Hoán vị x của hai mắt ⇒ `False` |
| 10 | Vi phạm bất biến 2 (mắt dưới mũi) → `False` | Đẩy y hai mắt xuống dưới mũi ⇒ `False` |
| 11 | Vi phạm bất biến 3 (mũi dưới miệng) → `False` | Đẩy y mũi xuống dưới miệng ⇒ `False` |
| 12 | Vi phạm bất biến 4 (khoé miệng đảo) → `False` | Hoán vị x hai khoé miệng ⇒ `False` |
| 13 | **Điểm mốc thẳng hàng theo đường chéo** → `False` | `np.array([[float(i), float(i)] for i in range(5)])` ⇒ `False`. ⚠️ Bộ này **thoả cả bốn bất biến thứ tự** — chỉ điều kiện thứ năm bắt được. `align.py` cũng **không** bắt được nó (§4), nên đây là lớp bảo vệ **duy nhất** |
| 13b | Tỉ lệ lệch mũi tính đúng trên mẫu chuẩn | Với `reference_landmarks`, tỉ số `== pytest.approx(0.5715, abs=1e-3)` |
| 13c | **Ngưỡng thật sự được dùng** | Dùng bộ dựng sẵn ở §9.2b (tỉ số đúng 0,2000): `min_ti_le_lech_mui=0.15` ⇒ `True`; `min_ti_le_lech_mui=0.25` ⇒ `False`. Cùng dữ liệu, đổi ngưỡng phải đổi kết quả — bảo đảm tham số không bị bỏ qua |
| 13d | Hai mắt trùng nhau → `ValueError`, **không** chia cho 0 | `diem_moc[0] == diem_moc[1]` ⇒ `pytest.raises(ValueError)` |
| 14 | Sai hình dạng → `ValueError` | Mảng `(4, 2)` ⇒ `pytest.raises(ValueError)` |

### 9.2b. Ba bộ điểm mốc dựng sẵn — dùng nguyên, đã kiểm bằng số 19/08/2026

```python
# Mặt chuẩn — reference_landmarks của configs/preprocess.yaml. Tỉ lệ lệch mũi = 0,5715
MAT_CHUAN = np.array([[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366],
                      [41.5493, 92.3655], [70.7299, 92.2041]])

# Tỉ lệ lệch mũi ĐÚNG 0,2000 — thoả cả bốn bất biến thứ tự. Dùng cho dòng 13c.
TI_LE_020 = np.array([[0.0, 0.0], [100.0, 0.0], [50.0, 20.0], [10.0, 60.0], [90.0, 60.0]])

# Thẳng hàng theo đường chéo. Tỉ lệ lệch mũi = 0,0000.
# ⚠️ Bộ này THOẢ CẢ BỐN bất biến thứ tự — chỉ điều kiện thứ năm bắt được. Dùng cho dòng 13.
THANG_HANG = np.array([[float(i), float(i)] for i in range(5)])
```

Công thức tỉ lệ lệch mũi, để cài đặt và ca test tính giống nhau:

```
ab = mắt_phải − mắt_trái
khoảng_cách = |ab.x·(mũi.y − mắt_trái.y) − ab.y·(mũi.x − mắt_trái.x)| / ‖ab‖
tỉ_lệ       = khoảng_cách / ‖ab‖
```

### 9.3. Xử lý một ảnh

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 15 | Ảnh không đọc được → `khong_doc_duoc_anh`, ảnh ra là `None` | Tệp `.png` chứa byte rác; assert cả hai |
| 16 | Không thấy mặt → `khong_thay_mat` | Detector giả trả `[]` |
| 17 | Mặt nhỏ hơn ngưỡng → `mat_qua_nho` | `FaceBox` cạnh 20 px với `min_bbox_px: 40` |
| 18 | Độ tin cậy thấp → `do_tin_cay_thap` | `confidence=0.5` với `min_confidence: 0.7` |
| 19 | Điểm mốc bất thường → `diem_moc_bat_thuong` | Điểm mốc thẳng hàng, khung bao và conf đều đạt |
| 20 | Đường thành công → `ok`, ảnh ra đúng kích thước | `ra.shape == (112, 112, 3)` và `ly_do == "ok"` |
| 21 | **Thứ tự lọc đúng**: mặt nhỏ **và** conf thấp → báo `mat_qua_nho` | Dựng cả hai vi phạm; assert lý do là lý do kiểm trước. Bảo đảm bảng lý do xác định, không phụ thuộc thứ tự cài đặt |
| 22 | Nhiều mặt → lấy mặt **diện tích lớn nhất**, `n_faces` ghi số thật | Detector giả trả 3 mặt; assert `thong_tin["n_faces"] == 3` và `bbox_w × bbox_h` khớp mặt **lớn nhất** |
| 22b | **Diện tích thắng độ tin cậy** — ca chặn lỗi đã xảy ra thật | Detector giả trả 2 mặt: mặt A `40×70` với `conf=0.870`, mặt B `120×160` với `conf=0.850`. Danh sách đã sắp theo conf giảm dần nên A đứng trước. Assert chọn **B**: `thong_tin["bbox_w"] == 120`. ⚠️ Đây đúng tình huống đã ghi nhầm người ở 5/198 ảnh mẻ thật |
| 22c | Diện tích bằng nhau → lấy mặt tin cậy cao hơn | Hai mặt cùng `100×100`, conf `0.9` và `0.8`; assert chọn mặt `conf=0.9` |
| 23 | `LoiCauHinh` từ `align` **lan lên trên**, không bị nuốt | `align.can_chinh` giả ném `LoiCauHinh`; `pytest.raises(LoiCauHinh)` — **không** được trả về lý do |
| 24 | `ValueError` từ `align` **không** làm hỏng cả mẻ | `align.can_chinh` giả ném `ValueError`; assert trả về lý do, không ném |

### 9.4. Manifest và đầu ra

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 25 | Manifest có **đúng bảy** cột, đúng thứ tự §8 | So dòng tiêu đề với danh sách nguyên văn |
| 26 | Mỗi ảnh nguồn có **đúng một** dòng, kể cả ảnh bỏ qua | 5 ảnh trong đó 2 bị bỏ ⇒ 5 dòng |
| 27 | `file_ra` rỗng với ảnh bị bỏ qua | Ô tương ứng là chuỗi rỗng, **không** phải `"None"` |
| 28 | Đường dẫn dùng `/`, không dùng `\` | `"\\" not in dong["file_vao"]` |
| 29 | Cấu trúc thư mục con được giữ nguyên | Ảnh `A/x.jpg` ⇒ tệp ra `A/x.png` |
| 30 | Đuôi ra luôn `.png` kể cả nguồn `.jpg` | `ra_path.suffix == ".png"` |
| 31 | Bản ghi thiếu khoá → `LoiCauHinh` | `pytest.raises(LoiCauHinh)` với `[{}]` |
| 32 | Bản ghi đủ khoá → ghi thành công | Cặp đối chứng của dòng 31 |

### 9.5. Luồng chính

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 33 | `--dry-run` **không ghi tệp nào** | Chụp `rglob("*")` thư mục ra trước và sau; bằng nhau; `main(...) == 0` |
| 34 | Thiếu `--vao` hoặc `--ra` → trả về `1` | Gọi thiếu từng cờ; assert cả hai trả `1` |
| 35 | Mô hình không tồn tại → trả về `1`, **không** để ngoại lệ lọt | `main([..., "--model", "khong/co.onnx"]) == 1` |
| 36 | Cấu hình hỏng → trả về `1` | `main([..., "--config-preprocess", cfg_hong]) == 1` |
| 37 | **Cấu hình hỏng dừng NGAY, không xử lý ảnh nào** | Thư mục 10 ảnh, cấu hình hỏng; assert thư mục ra rỗng **và** không có `manifest.csv`. ⚠️ Đây là ca chặn lỗi bắt gộp `except Exception` |
| 38 | `--gioi-han N` xử lý đúng N ảnh | 20 ảnh, `--gioi-han 5` ⇒ manifest 5 dòng |
| 39 | Cùng `--seed` chọn cùng tập khi có `--gioi-han` | Hai lần chạy cho cùng danh sách `file_vao` |
| 40 | `--tiep-tuc` bỏ qua ảnh đã có ở đích | Chạy hai lần; lần hai không ghi đè, `mtime` tệp cũ không đổi |
| 41 | Không có `--tiep-tuc` thì xử lý lại từ đầu | Cặp đối chứng của dòng 40 |
| 42 | Bảng tổng kết in đủ **sáu** lý do | `capsys`: đầu ra chứa cả sáu chuỗi ở §7 |
| 43 | Mã trả về `0` khi có ảnh bị bỏ qua | Bỏ qua **không phải** lỗi mẻ; assert `main(...) == 0` |

---

## 10. Lệnh kiểm bắt buộc

```bash
black --line-length 100 --check scripts/preprocess.py tests/test_preprocess.py
```

```bash
ruff check scripts/preprocess.py tests/test_preprocess.py
```

```bash
python -m pytest tests/test_preprocess.py -v
```

```bash
git status --short --untracked-files=all
```

Lệnh cuối: **đúng hai** tệp mã nguồn mới. Ba tệp `.docx` trong `docs/bao-cao-tuan/` là của
sinh viên — bỏ qua. Tệp sinh ra trong `data/` không hiện vì `data/*` đã gitignore.

### Quét mẫu vi phạm — cả bốn phải rỗng

```bash
grep -n "except Exception" scripts/preprocess.py
```

```bash
grep -nE "\b(112|40|0\.7|0\.15)\b" scripts/preprocess.py
```

```bash
grep -rn "ultralytics\|import torch" scripts/preprocess.py
```

```bash
grep -n "print(" scripts/preprocess.py
```

Lệnh đầu là **quan trọng nhất** — xem §3. Không có ngoại lệ nào được chấp nhận cho lệnh này.
Lệnh hai bắt số hardcode: bốn giá trị đó phải đến từ `configs/preprocess.yaml`, không được viết
thẳng vào mã. Số `5` (số điểm mốc) là **đặc tính cố hữu của mô hình**, không phải tham số điều
chỉnh được — đặt thành hằng số có tên kèm chú thích, không tính là vi phạm.
Lệnh bốn: `print()` chỉ cho bảng tổng kết CLI, giải trình từng dòng.

### Kiểm đột biến bắt buộc

| # | Phép đột biến | Ca test **phải** đỏ |
|---|---|---|
| ĐB1 | Đổi `except ValueError` thành `except Exception` trong vòng lặp mẻ | dòng **37** |
| ĐB2 | Bỏ `kiem_hinh_hoc_diem_moc`, cho mọi điểm mốc đi qua | dòng 19 |
| ĐB3 | Trong `kiem_hinh_hoc_diem_moc`, bỏ **riêng** bất biến 2 (mắt trên mũi) | dòng 10, **không** được làm đỏ dòng 13 |
| ĐB3b | Bỏ **riêng** điều kiện thứ năm (tỉ lệ lệch mũi), giữ nguyên bốn bất biến | dòng **13**, **13c** |
| ĐB4 | Ghi đuôi `.jpg` thay vì `.png` | dòng 30 |
| ĐB5 | Bỏ ghi dòng manifest cho ảnh bị bỏ qua | dòng 26 |
| ĐB6 | Lấy khuôn mặt **cuối** danh sách thay vì mặt lớn nhất | dòng 22 |
| **ĐB6b** | Chọn theo **độ tin cậy cao nhất** thay vì diện tích lớn nhất — tức khôi phục đúng luật sai của bản đặc tả đầu | dòng **22b** |
| **ĐB7** | Thay `kiem_hinh_hoc_diem_moc` bằng một hàm **luôn trả `True` trừ khi điểm mốc trùng nhau hoàn toàn** — tức một bộ lọc *có vẻ hợp lý* nhưng để lọt đúng trường hợp `align.py` cũng không bắt được | dòng **13** |

**ĐB1 là phép quan trọng nhất.** Nếu dòng 37 không đỏ thì ca test đó chưa kiểm đúng: nó phải
chứng minh mẻ **dừng ngay**, thư mục ra rỗng và **không có** `manifest.csv`. Một mẻ bắt gộp
`except Exception` sẽ chạy hết 10 ảnh rồi ghi manifest đủ 10 dòng `bo_qua` — trông như "xử lý
xong, tiếc là ảnh nào cũng hỏng".

**ĐB7 là phép tự nhất quán** — kiểu cài đặt sai mà mọi ca test hiển nhiên đều xanh. Nó tồn tại
vì bài học từ `P2-02`: phải nghĩ ra bản sai *tự nhất quán*, không chỉ bản sai lộ liễu.

Mỗi phép: sửa → chạy → ghi ca đỏ → khôi phục → đối chiếu `sha256`. Dùng `newline=""`.

---

## 11. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` 100, `ruff` sạch. Type hints, docstring tiếng Việt kiểu Google.
- Chỉ `numpy`, `cv2`, `onnxruntime` và `src/**` của dự án. **Không** `ultralytics`, **không**
  `torch` — script này phải chạy được trên Pi 5.
- Dùng `logging` qua `src.common.logging.lay_logger`; `print()` chỉ cho bảng tổng kết.
- Đọc cấu hình qua `src.common.config.nap_cau_hinh` / `lay_gia_tri`.
- ⚠️ **Container ARM64 KHÔNG có** `models/`, `data/`, `docs/`, `.git/`, nhị phân `git`, và các gói
  `ultralytics`/`torch`/`onnx` (xem `.dockerignore` và `deploy/Dockerfile.arm64`).
  Mọi ca test chạm tới chúng phải `pytest.skip` **có thông báo nêu rõ thiếu gì**.
  Đây là bài học từ `P2-01` — mã việc đó để lọt 10 ca hỏng trong container vì thiếu chốt skip.
  Kiểm bắt buộc: `python -m pytest tests/test_preprocess.py -v` trong container phải
  **không có `error`, không có `failed`**, chỉ `passed` và `skipped`.
- Phần lớn ca test phải dùng **detector giả** (đối tượng có phương thức `detect`), không nạp mô
  hình thật — như vậy bộ test chạy nhanh và không phụ thuộc `models/`.

---

## 12. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **Chia tập `enroll/val/test`** — bước 1.11, mã việc riêng.
- **Loại ảnh trùng lặp** — bước 1.10. Ở đây chỉ lọc theo chất lượng phát hiện.
- **Domain adaptation** — bước 1.8, cần số đo của bước 1.7, cần camera.
- **Sinh embedding** — Phase 3.
- Đo hiệu năng của chính mẻ xử lý — không phải mục tiêu; tốc độ ở đây không phải chỉ tiêu cam kết.

---

## 13. Báo cáo khi xong

1. Kết quả bốn lệnh máy §10, trên host **và** container ARM64.
2. Kết quả bốn lệnh `grep`, giải trình từng dòng không rỗng.
3. Kết quả **bảy** phép đột biến, kèm `sha256` khôi phục.
4. **Một lần chạy thật** trên LFW với `--gioi-han 200`: dán bảng tổng kết, nêu tỉ lệ từng lý do.
   Đối chiếu với dữ kiện §4 (60/60 ảnh LFW phát hiện được) xem tỉ lệ `khong_thay_mat` có hợp lý
   không — cao bất thường là dấu hiệu sai.
5. Vướng mắc.

**Không commit.** Để nguyên cây làm việc cho người review.
