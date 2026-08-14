# P1-02-collect-faces — Script thu thập ảnh khuôn mặt

| | |
|---|---|
| **Phase** | 1 — Dữ liệu khuôn mặt |
| **Bước CLAUDE.md** | §5 Phase 1, bước 1.2 |
| **Nhánh** | `feat/p1-02-collect-faces` |
| **Phụ thuộc** | `P0-01-nen-tang`, `P1-01-capture` (đã ĐẠT, đã gộp vào `dev`) |
| **Quy ước dữ liệu** | `docs/quy-uoc-du-lieu.md` — **đọc trước khi cài đặt** |
| **Ước lượng** | 3 file, ~320 dòng |

---

## 1. Mục tiêu

Script thu thập ảnh khuôn mặt **có hướng dẫn tư thế và tự đếm theo tổ hợp**, bảo đảm mọi nguồn dữ liệu
của đồ án đi qua cùng một đường ống thu nhận.

---

## 2. DANH SÁCH TRẮNG

| File | Thao tác |
|---|---|
| `scripts/__init__.py` | tạo mới (để trống — để `tests/` import được) |
| `scripts/collect_faces.py` | tạo mới |
| `tests/test_collect_faces.py` | tạo mới |

> **Cấm chạm** mọi file khác. `configs/data.yaml` và `configs/capture.yaml` **đã tồn tại**, chỉ đọc.
> Không sửa `src/`, không sửa `docs/`, không tạo dữ liệu trong `data/`.

---

## 3. Interface bắt buộc

Toàn bộ đặt trong `scripts/collect_faces.py`.

```python
def tao_ten_file(ma: str, pose: str, light: str, idx: int, duoi: str) -> str:
    """Sinh tên file theo quy ước: <ma>_<pose>_<light>_<idx 3 chữ số>.<duoi>"""


def phan_tich_ten_file(ten: str) -> tuple[str, str, str, int]:
    """Tách tên file thành (ma, pose, light, idx). Raises ValueError nếu sai quy ước."""


def dem_da_co(thu_muc: Path, ma: str) -> dict[tuple[str, str], int]:
    """Đếm số ảnh đã có của một người, theo từng tổ hợp (pose, light).

    Bỏ qua file không đúng quy ước, không ném ngoại lệ.
    Thư mục không tồn tại → trả về dict rỗng.
    """


def to_hop_con_thieu(
    da_co: dict[tuple[str, str], int], poses: list[str], lights: list[str], toi_thieu: int
) -> list[tuple[str, str, int]]:
    """Trả về [(pose, light, so_anh_con_thieu)] cho các tổ hợp chưa đủ. Đủ hết → list rỗng."""


def ghi_manifest(duong_dan: Path, ban_ghi: list[dict]) -> None:
    """Ghi NỐI vào manifest CSV. Tự tạo file kèm dòng tiêu đề nếu chưa có."""


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
    """


def main() -> int:
    """Điểm vào CLI. Trả về 0 nếu thành công, 1 nếu lỗi."""
```

### 3.1. `hien_thi` tắt cái gì và KHÔNG tắt cái gì

Đây là điều kiện để kiểm thử chạy được trong container không có màn hình. Nhưng phải chính xác về
phạm vi:

| `hien_thi=False` **tắt** | `hien_thi=False` **KHÔNG được tắt** |
|---|---|
| `cv2.imshow`, `cv2.waitKey`, `cv2.namedWindow`, `cv2.destroyAllWindows` | In hướng dẫn tư thế ra màn hình |
| | Nhịp chờ `capture_interval_s` giữa hai ảnh |
| | Nhịp chờ `pose_switch_delay_s` khi đổi tư thế |
| | Ghi manifest |

**Vì sao nhịp chờ không được tắt**: người chụp cần thời gian đổi tư thế. Chụp 4 ảnh trong 0,12 giây
thay vì 4,0 giây thì cả bốn ảnh đều là cùng một tư thế, nhưng vẫn được gắn nhãn `left`, `up`, `down`
theo kế hoạch. **Dataset sai nhãn tư thế**, và mọi phân tích theo tư thế ở bước 1.7 và 1.13 mất ý nghĩa.

Ai muốn chạy nhanh khi kiểm thử thì đặt `capture_interval_s` và `pose_switch_delay_s` về `0` **trong
config**, không phải qua cờ `--no-preview`.

---

## 4. Tham số → config

Đọc từ `configs/data.yaml` và `configs/capture.yaml`. **Không hardcode giá trị nào.**

| Tham số | File | Key |
|---|---|---|
| Danh sách tư thế | `data.yaml` | `poses` |
| Danh sách mức sáng | `data.yaml` | `lights` |
| Số ảnh tối thiểu mỗi tổ hợp | `data.yaml` | `min_per_combo` |
| Mẫu kiểm mã người | `data.yaml` | `id_pattern` |
| Thư mục ra | `data.yaml` | `out_dir_gallery` / `out_dir_indomain` |
| Tên manifest | `data.yaml` | `manifest_name` |
| Định dạng ảnh | `data.yaml` | `image_format` |
| Nhịp chụp | `data.yaml` | `capture_interval_s`, `pose_switch_delay_s` |
| Cấu hình camera | `capture.yaml` | toàn bộ, truyền cho `tao_bo_thu_hinh` |

### 4.1. Cột manifest → nguồn giá trị

Mỗi cột phải lấy từ đúng nguồn dưới đây. **Không cột nào được ghi giá trị cấu hình thô.**

| Cột | Nguồn giá trị | Ví dụ |
|---|---|---|
| `file` | Tên file vừa ghi | `u01_frontal_bright_007.png` |
| `id` | `--id` | `u01` |
| `pose` | Tổ hợp đang chụp | `frontal` |
| `light` | `--light` | `bright` |
| `idx` | Số thứ tự vừa cấp | `7` |
| `timestamp` | `datetime.now()` có múi giờ, dạng ISO 8601 | `2026-08-15T09:12:33+07:00` |
| **`camera`** | **Tên lớp backend ĐÃ PHÂN GIẢI**, lấy bằng `type(cam).__name__` | `CameraOpenCV` |
| `width`, `height` | Kích thước **thật của khung hình vừa đọc**, `frame.shape` | `1280`, `720` |
| `note` | **Để rỗng ở mã việc này.** Ghi chú buổi chụp điền tay vào manifest sau khi thu, hoặc bổ sung cờ CLI ở một mã việc riêng | *(rỗng)* |

> ⛔ **Cột `camera` tuyệt đối không được ghi `"auto"`.** `auto` là *bộ chọn*, không phải backend.
> Nếu camera không mở được, `auto` rơi về `CameraGiaLap` và script vẫn chạy êm — ảnh nhiễu tổng hợp
> được ghi vào `data/raw/` với manifest ghi `camera=auto`. Sau đó **không có cách nào phân biệt ảnh
> thật với ảnh giả** trong cùng thư mục, và toàn bộ gallery nhiễm dữ liệu rác mà không ai biết.
>
> Cùng lý do: `width`/`height` lấy từ `frame.shape` thật, không lấy từ config — camera có thể trả về
> độ phân giải khác giá trị yêu cầu.

### Tham số dòng lệnh

| Cờ | Bắt buộc | Ý nghĩa |
|---|---|---|
| `--id` | có | Mã người, ví dụ `u01` |
| `--light` | có | `bright` hoặc `dim` |
| `--config-data` | không | mặc định `configs/data.yaml` |
| `--config-capture` | không | mặc định `configs/capture.yaml` |
| `--out` | không | ghi đè thư mục ra |
| `--no-preview` | không | không mở cửa sổ xem trực tiếp |
| `--dry-run` | không | in kế hoạch, **không ghi file nào** |

---

## 5. Hành vi & ca biên

> **Bảng này chỉ chứa ca kiểm thử pytest.** Lệnh shell nằm ở §6.
> Mọi ca dùng `tmp_path`, backend camera `mock`, và `hien_thi=False`.

| # | Điều kiện | Kỳ vọng | Assert tối thiểu |
|---|---|---|---|
| 1 | `tao_ten_file("u01","frontal","bright",7,"png")` | đệm 3 chữ số | `== "u01_frontal_bright_007.png"` |
| 2 | `tao_ten_file(...)` với `idx=1000` | vẫn sinh được, không cắt cụt | `"1000" in ten` |
| 3 | `phan_tich_ten_file` là **nghịch đảo** của `tao_ten_file` | vòng tròn khép kín | `phan_tich_ten_file(tao_ten_file("u01","left","dim",12,"png")) == ("u01","left","dim",12)` |
| 4 | `phan_tich_ten_file("anh_bat_ky.png")` | raise `ValueError` | `pytest.raises(ValueError)` |
| 5 | `dem_da_co` trên thư mục **không tồn tại** | dict rỗng, không ném | `== {}` |
| 6 | `dem_da_co` trên thư mục **có 3 ảnh `frontal_bright` và 2 ảnh `left_dim`** | đếm đúng từng tổ hợp | `da_co[("frontal","bright")] == 3 and da_co[("left","dim")] == 2` |
| 7 | `dem_da_co` khi thư mục lẫn file lạ (`ghi_chu.txt`, `IMG_1234.png`) | bỏ qua, không ném, không đếm nhầm | `da_co[("frontal","bright")] == 3` như dòng 6 |
| 8 | `dem_da_co` chỉ đếm ảnh **của đúng mã người** | không lẫn `u02` vào `u01` | Ghi cả `u01_*` và `u02_*`, `dem_da_co(d,"u01")` không tính ảnh `u02` |
| 9 | `to_hop_con_thieu` khi mọi tổ hợp **đã đủ** | list rỗng | `== []` |
| 10 | `to_hop_con_thieu` khi thiếu | trả đúng tổ hợp và **số còn thiếu** | Có `("up","dim", toi_thieu - da_co)` trong kết quả |
| 11 | Đánh số **tiếp tục** khi đã có ảnh cũ | không bắt đầu lại từ 001 | Có sẵn `..._007.png`, chụp thêm 1 ảnh → tồn tại `..._008.png` |
| 12 | **Không ghi đè** ảnh đã có | dữ liệu cũ nguyên vẹn, **và có ảnh mới được chụp** | Đặt `min_per_combo=3`, để sẵn `..._001.png` nội dung đã biết → sau khi chạy: `..._001.png` **không đổi** VÀ tồn tại `..._002.png`, `..._003.png`. ⚠️ Nếu số ảnh cần chụp bằng 0 thì đường không-ghi-đè **không hề chạy** — ca test rỗng ruột |
| 12a | Cột `camera` ghi **backend đã phân giải** | không bao giờ là `"auto"` | Chạy với `backend="auto"` trên máy không camera: `ban_ghi[0]["camera"] == "CameraGiaLap"`, và `"auto" not in [r["camera"] for r in ban_ghi]` |
| 12b | `width`/`height` lấy từ **khung hình thật** | không lấy từ config | Cấu hình mock `width=640,height=480` khác giá trị mặc định: `ban_ghi[0]["width"] == 640` |
| 12c | **Lỗi camera giữa chừng** | manifest vẫn ghi phần đã chụp, không để dữ liệu mồ côi | Cho `doc_frame` ném `LoiCamera` ở lần thứ 3: số ảnh trên đĩa `== 2` **và** số dòng dữ liệu manifest `== 2` |
| 12d | `hien_thi=False` **không tắt nhịp chờ** | người chụp vẫn kịp đổi tư thế | `capture_interval_s=0.2`, chụp 4 ảnh: thời gian trôi `>= 0.6` giây |
| 12e | `hien_thi=False` **không tắt hướng dẫn tư thế** | vẫn in ra | `capsys.readouterr().out` chứa tên tư thế đang chụp |
| 13 | `thu_thap` với camera mock, `hien_thi=False` | tạo đúng số ảnh yêu cầu | `len(list(thu_muc.glob("*.png"))) == so_anh_mong_doi` |
| 14 | Ảnh ghi ra là **PNG đọc được** | không phải file rỗng hay hỏng | `cv2.imread(str(p)) is not None` và `.shape == (h, w, 3)` |
| 15 | `thu_thap` trả về bản ghi manifest khớp số ảnh | | `len(ban_ghi) == so_anh_mong_doi` |
| 16 | `ghi_manifest` lần đầu | tạo file **kèm dòng tiêu đề** | Dòng đầu chứa `file`, `id`, `pose`, `light`, `idx`, `timestamp` |
| 17 | `ghi_manifest` lần hai | **ghi nối**, không ghi đè, không lặp tiêu đề | Sau 2 lần ghi 2 bản ghi: tổng số dòng `== 5` (1 tiêu đề + 4 dữ liệu) |
| 18 | Số dòng manifest khớp số ảnh trên đĩa | | `so_dong_du_lieu == len(list(thu_muc.glob("*.png")))` |
| 19 | `dry_run=True` — **đường an toàn** | **không ghi file nào** | Trước và sau khi gọi, `list(tmp_path.rglob("*"))` không đổi |
| 20 | `dry_run=True` — **đường thành công** | vẫn trả về kế hoạch để in ra | `thu_thap(..., dry_run=True) == []` và không ném ngoại lệ |
| 21 | Thư mục ra **chưa tồn tại** | tự tạo, không ném | `thu_muc.exists()` sau khi gọi |
| 22 | `--id` sai mẫu | `main()` trả `1`, thông báo nêu mã sai | Kiểm **cả ba** mã: `"abc"`, `"u1"`, `"y01"` — mỗi mã một lần gọi, đều `main() == 1` |
| 23 | `--light` không có trong `lights` của config | `main()` trả `1` | `main() == 1` |
| 24 | `--id` và `--light` hợp lệ — **đường thành công** | `main()` trả `0` | `main() == 0` với `--dry-run` và `--no-preview` |
| 25a | `hien_thi=False` không gọi hàm hiển thị nào trong **vòng lặp chụp** | chạy được trên máy không màn hình | Vá **cả bốn** `cv2.imshow`, `cv2.waitKey`, `cv2.namedWindow`, `cv2.destroyAllWindows` thành hàm ném `AssertionError`; `thu_thap(hien_thi=False)` **không** ném |
| 25b | Ca 25a phải **chạy hết thân hàm**, không thoát sớm | guard được kiểm thật | Cùng ca 25a: `assert len(ban_ghi) == so_anh_mong_doi` |
| 25c | `hien_thi=False` cũng guard **khối dọn dẹp cuối hàm** | script không gãy ở bước đóng cửa sổ | Cùng ca 25a chạy tới khi kết thúc bình thường — mã có **hai** khối `if hien_thi:`, khối cuối gọi `destroyAllWindows` cũng phải nằm trong guard |

---

## 6. Tiêu chí nghiệm thu

- [ ] **Mỗi dòng bảng §5 có ít nhất một ca kiểm thử, mỗi ca có assert thật** — hàm test rỗng là CHẶN-B
- [ ] **Không ca test nào gọi `subprocess`**:
      `grep -n "subprocess\|shutil.which" tests/test_collect_faces.py` không có kết quả
- [ ] **Không ca test nào cần camera thật hoặc màn hình**
- [ ] **Không ca test nào ghi ra ngoài `tmp_path`** — sau khi chạy `pytest`,
      `git status --short --untracked-files=all` không có file mới
- [ ] `pytest -q` xanh toàn bộ dự án — **52 ca cũ vẫn đạt**, cộng ca mới
- [ ] `pytest -q` **xanh trong container ARM64**:
      `MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q`
      — trên Git Bash (Windows) **bắt buộc** có `MSYS_NO_PATHCONV=1`, nếu không shell sẽ biến `/app`
      thành đường dẫn Windows; bỏ cờ `--platform` vì ảnh đã tự khai báo kiến trúc từ `P0-03`
- [ ] `black --check --line-length 100 src tests scripts` và `ruff check src tests scripts` sạch
- [ ] **Kiểm phạm vi file**:
      `git status --short --untracked-files=all | grep -v "docs/review/" | wc -l` trả `3`
      — cờ `--untracked-files=all` bắt buộc, thiếu thì git gộp thư mục mới thành một dòng
- [ ] **Không thư viện ngoài `requirements.txt`**:
      `grep -nE "^\s*(import|from) (PIL|imageio|skimage|scipy|matplotlib|torch|pandas)" scripts/*.py`
      không có kết quả
- [ ] `python scripts/collect_faces.py --help` chạy được, mô tả tiếng Việt
- [ ] `python scripts/collect_faces.py --id u01 --light bright --dry-run --no-preview` thoát mã 0
      và **không tạo file nào** trong `data/`

---

## 7. Quy tắc áp dụng

| Mã | Vì sao |
|---|---|
| **G1** | Mọi tham số từ `configs/data.yaml` và `configs/capture.yaml` |
| **G2** | Dùng `lay_logger(__name__)` cho tiến trình; `print` **chỉ** cho hướng dẫn tư thế và bảng tóm tắt cuối |
| **G4** | Type hints + docstring tiếng Việt cho mọi hàm public |
| **G5** | Không `except` trần; lỗi camera bọc thành `LoiCamera` |
| **G6** | Camera phải được đóng kể cả khi người dùng ngắt bằng `Ctrl+C` — dùng `try/finally` hoặc context manager của `BoThuHinh` |
| **R15** | Không có yếu tố ngẫu nhiên trong script này; nếu thêm thì phải có `--seed` |

**Thư viện được phép**: `cv2`, `numpy`, và thư viện chuẩn (`argparse`, `pathlib`, `csv`, `datetime`,
`re`, `time`, `sys`). **Không được thêm gì khác.** Cần thư viện khác → **dừng và báo**, không tự cài.

Ghi ảnh bằng `cv2.imwrite`. Định dạng lấy từ `image_format` trong config, mặc định `png` — **không
hardcode đuôi file**.

Khung hình từ `src/capture/` theo thứ tự **BGR**, và `cv2.imwrite` cũng nhận BGR — **không chuyển đổi
màu ở giữa**.

---

## 8. Ngoài phạm vi — KHÔNG làm

- Phát hiện khuôn mặt, cắt, căn chỉnh 112×112 → `preprocess.py`, bước 1.9
- Kiểm chất lượng ảnh (loại ảnh mờ, ảnh không có mặt) → bước 1.10
- Chia tập train/val/test → bước 1.11
- Thu thập bộ dữ liệu tấn công → mã việc riêng ở bước 1.12; script này **chỉ** thu gallery và in-domain
- Giao diện đồ hoạ, đếm ngược bằng âm thanh, tự nhận biết tư thế
- Tải LFW → bước 1.5, việc khác
- Sửa `configs/*.yaml` hoặc `src/capture/`
