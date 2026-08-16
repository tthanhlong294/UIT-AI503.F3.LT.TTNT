# P1-03-download-lfw — Script tải và chọn lọc bộ dữ liệu LFW

| | |
|---|---|
| **Phase** | 1 — Dữ liệu khuôn mặt |
| **Bước CLAUDE.md** | §5 Phase 1, bước 1.5 |
| **Nhánh** | `feat/p1-03-download-lfw` |
| **Phụ thuộc** | `P0-01-nen-tang` (dùng `LoiCauHinh`, `nap_cau_hinh`, `lay_logger`) |
| **Quy ước dữ liệu** | `docs/quy-uoc-du-lieu.md` §4 — **đọc trước khi cài đặt** |
| **Ước lượng** | 2 file, ~300 dòng |

---

## 1. Mục tiêu

Tải bộ dữ liệu LFW, chọn ra **≥ 100 danh tính một cách tái lập được**, đặt vào
`data/impostor/lfw_original/` kèm manifest — làm tập impostor quy mô lớn để đo `FAR_lfw`.

---

## 2. DANH SÁCH TRẮNG

| File | Thao tác |
|---|---|
| `scripts/download_lfw.py` | tạo mới |
| `tests/test_download_lfw.py` | tạo mới |

> **Cấm chạm** mọi file khác. `configs/data.yaml` **đã có mục `lfw`**, chỉ đọc, không sửa.
> `scripts/__init__.py` đã tồn tại từ `P1-02`.

---

## 3. Interface bắt buộc

```python
def tai_ve(url: str, dich: Path, dry_run: bool = False) -> Path:
    """Tải tệp về đích. Bỏ qua nếu tệp đã tồn tại. Raises LoiCauHinh nếu tải thất bại."""


def tinh_sha256(duong_dan: Path) -> str:
    """Tính mã băm SHA256 của tệp, đọc theo khối để không nạp cả tệp vào bộ nhớ."""


def giai_nen(archive: Path, dich: Path) -> Path:
    """Giải nén tệp .tgz vào thư mục đích, trả về thư mục gốc vừa giải nén.

    Raises LoiCauHinh với **thông báo phân biệt được hai nguyên nhân** — xem §3.1.
    """


def liet_ke_danh_tinh(thu_muc_lfw: Path) -> dict[str, list[Path]]:
    """Quét thư mục LFW, trả về {tên_danh_tính: [danh sách đường dẫn ảnh]}.

    Bỏ qua tệp không phải ảnh. Thư mục không tồn tại → trả về dict rỗng.
    """


def chon_danh_tinh(
    danh_tinh: dict[str, list[Path]], so_luong: int, toi_thieu_anh: int, seed: int
) -> list[str]:
    """Chọn ngẫu nhiên có tái lập ra `so_luong` danh tính có ít nhất `toi_thieu_anh` ảnh.

    Trả về danh sách tên đã sắp xếp. Raises LoiCauHinh nếu không đủ danh tính thoả điều kiện.
    """


def sao_chep(
    danh_tinh: dict[str, list[Path]], da_chon: list[str], thu_muc_ra: Path, dry_run: bool = False
) -> list[dict]:
    """Sao chép ảnh của các danh tính đã chọn sang thư mục ra, giữ nguyên cấu trúc và tên file.

    Trả về danh sách bản ghi manifest. Không ghi đè tệp đã có.
    """


def ghi_manifest(duong_dan: Path, ban_ghi: list[dict]) -> None:
    """Ghi manifest CSV kèm dòng tiêu đề (ghi đè, không ghi nối — xem §4.1).

    Raises LoiCauHinh nếu bất kỳ bản ghi nào thiếu một trong sáu khoá bắt buộc ở §4.1.
    """


def main() -> int:
    """Điểm vào CLI. Trả về 0 nếu thành công, 1 nếu lỗi.

    TRƯỚC KHI TẢI, nếu `out_dir` đã có manifest cũ với `selected_seed` khác seed đang dùng,
    hoặc manifest cũ không đọc được, thì raise LoiCauHinh — xem §4.2.
    """
```

### 3.1. `giai_nen` — hai nguyên nhân lỗi phải có thông báo KHÁC NHAU

`tarfile.ReadError` và `tarfile.FilterError` đều là lớp con của `TarError`. Bắt chung một `except`
sẽ cho cùng một thông báo cho hai tình huống **đòi hỏi phản ứng ngược nhau**:

| Ngoại lệ gốc | Nghĩa là gì | Người dùng phải làm gì |
|---|---|---|
| `tarfile.ReadError` | Tệp tải về **hỏng** — lành tính | **Tải lại** |
| `tarfile.FilterError` | Tệp nén chứa **đường dẫn vượt ra ngoài** — dấu hiệu tệp độc hại | **Dừng, điều tra nguồn tải** |

Thông báo gộp đẩy người dùng về phản ứng phổ biến là "tải lại" — phản ứng **sai nhất** cho tình
huống an ninh. Bắt **hai `except` riêng**, `FilterError` đặt **trước** `TarError` vì nó là lớp con:

- `FilterError` → thông báo nêu rõ **đường dẫn không an toàn**
- `TarError` → thông báo nêu rõ **tệp nén hỏng**

`tarfile.FilterError` có sẵn ở cả Python 3.11.15 (container) và 3.12.5 (máy phát triển).

---

## 4. Tham số → config

Đọc từ mục `lfw` của `configs/data.yaml`. **Không hardcode giá trị nào.**

| Tham số | Key | Ghi chú |
|---|---|---|
| Đường dẫn tải | `lfw.url` | Bản **gốc chưa căn chỉnh** |
| Tên tệp lưu | `lfw.archive_name` | |
| Thư mục tạm | `lfw.cache_dir` | Nơi giữ tệp nén và bản giải nén |
| Thư mục ra | `lfw.out_dir` | |
| Số danh tính | `lfw.min_identities` | |
| Số ảnh tối thiểu mỗi danh tính | `lfw.min_images_per_identity` | |
| Seed | `lfw.seed` | |
| Trích dẫn | `lfw.citation` | In ra cuối phiên chạy |

### 4.1. Manifest — cột và nguồn giá trị

| Cột | Nguồn |
|---|---|
| `file` | Đường dẫn tương đối tính từ `out_dir` |
| `identity` | Tên thư mục danh tính của LFW, giữ nguyên |
| `n_images` | Tổng số ảnh của danh tính đó **có mặt trong `out_dir`** sau khi chạy |
| `source_sha256` | SHA256 của **tệp nén** đã tải, giống nhau ở mọi dòng |
| `selected_seed` | Giá trị seed đã dùng để chọn |
| `timestamp` | Thời điểm chạy, ISO 8601 có múi giờ |

> `source_sha256` và `selected_seed` là hai cột làm cho tập dữ liệu **tái lập được**: ai đó chạy lại
> với cùng tệp nén và cùng seed phải nhận đúng 100 danh tính ấy.

**Khoá nào do hàm nào sinh** — `sao_chep` không nhận seed lẫn mã băm trong chữ ký, nên:

| Khoá | Do hàm nào điền |
|---|---|
| `file`, `identity`, `n_images` | `sao_chep` |
| `source_sha256`, `selected_seed`, `timestamp` | `main()` bổ sung vào từng bản ghi **trước khi** gọi `ghi_manifest` |

⛔ **`ghi_manifest` phải từ chối bản ghi thiếu khoá.** `csv.DictWriter` mặc định điền chuỗi rỗng cho
khoá thiếu — không lỗi, không cảnh báo. Nếu `source_sha256` và `selected_seed` rỗng thì manifest mất
đúng hai cột làm nên tính tái lập, mà không ai biết. Kiểm ở đầu hàm, thiếu → `LoiCauHinh` nêu tên khoá.

### 4.2. Chạy lại với seed khác — phải dừng, không được trộn

`sao_chep` bỏ qua tệp đã tồn tại, còn `ghi_manifest` ghi đè. Hệ quả nếu chạy lần hai với seed khác:
ảnh của 100 danh tính **cũ** vẫn nằm trong `out_dir`, nhưng manifest chỉ liệt kê 100 danh tính **mới**.

Tập impostor lặng lẽ phình lên 200 danh tính trong khi manifest nói 100 — và `FAR_lfw` đo trên tập đó
sẽ sai mà không có dấu hiệu gì.

**Yêu cầu**: `main()` đọc `selected_seed` của manifest cũ nếu có. Lệch seed đang dùng → **dừng ngay**,
raise `LoiCauHinh` nêu cả hai giá trị seed và yêu cầu dọn `out_dir` trước. Không thêm cờ ghi đè —
dọn thư mục là thao tác có ý thức, đúng tinh thần "hỏng ồn ào còn hơn hỏng âm thầm".

**Vị trí kiểm: TRƯỚC khi tải và giải nén**, không phải trước khi sao chép. Đặt sau thì mỗi lần chạy
nhầm seed vẫn tốn công đọc tệp nén vài trăm MB và bung hơn mười ba nghìn tệp rồi mới báo lỗi.

**Manifest cũ không đọc được** (hỏng, thiếu cột `selected_seed`, giá trị không phải số) → cũng
**dừng** với `LoiCauHinh` yêu cầu dọn `out_dir`. Không được để ngoại lệ thô lọt ra ngoài `main()`,
và không được âm thầm coi như "chưa có manifest" — vì khi đó dữ liệu cũ vẫn nằm đó và sẽ bị trộn.

### Tham số dòng lệnh

| Cờ | Bắt buộc | Ý nghĩa |
|---|---|---|
| `--config` | không | mặc định `configs/data.yaml` |
| `--out` | không | ghi đè `lfw.out_dir` |
| `--seed` | không | ghi đè `lfw.seed` |
| `--expect-sha256` | không | So mã băm tệp nén với giá trị này; lệch → thoát mã 1 |
| `--dry-run` | không | In kế hoạch, **không tải, không ghi file nào** |

---

## 5. Hành vi & ca biên

> **Bảng này chỉ chứa ca kiểm thử pytest.** Lệnh shell nằm ở §6.
> ⛔ **Không ca test nào được truy cập mạng.** Mọi ca dùng `tmp_path` và tệp `.tgz` tự dựng tại chỗ.

| # | Điều kiện | Kỳ vọng | Assert tối thiểu |
|---|---|---|---|
| 1 | `tinh_sha256` trên tệp đã biết nội dung | khớp giá trị tính bằng `hashlib` | `tinh_sha256(p) == hashlib.sha256(p.read_bytes()).hexdigest()` |
| 2 | `tinh_sha256` trên tệp lớn hơn kích thước khối | vẫn đúng, không nạp cả tệp | Tạo tệp 5 MB, so với `hashlib` |
| 3 | `giai_nen` tệp `.tgz` hợp lệ — **đường thành công** | giải ra đúng cây thư mục | Dựng `.tgz` chứa `lfw/A/a_0001.jpg`, sau khi gọi: tệp đó tồn tại |
| 4 | `giai_nen` tệp hỏng | raise `LoiCauHinh` **vì không mở được tệp nén** | `pytest.raises(LoiCauHinh)` với tệp chứa byte ngẫu nhiên, **và** thông báo nói **tệp nén hỏng**, **và** thông báo **không** chứa cụm nói về đường dẫn không an toàn — xem §3.1 |
| 5 | **`giai_nen` chặn đường dẫn vượt ra ngoài** | không ghi ra ngoài thư mục đích, thông báo nói về **đường dẫn không an toàn** | Dựng `.tgz` chứa mục `../../thoat.txt`; tệp đó **không tồn tại** bên ngoài `tmp_path`, **và** thông báo **không** chứa cụm nói tệp nén hỏng — hai thông báo phải phân biệt được (§3.1) |
| 6 | `liet_ke_danh_tinh` trên cây thư mục mẫu | đếm đúng | 3 thư mục lần lượt 1, 2, 5 ảnh → `len(kq) == 3` và `len(kq["B"]) == 2` |
| 7 | `liet_ke_danh_tinh` bỏ qua tệp không phải ảnh | không đếm nhầm | Thêm `README.txt` vào một thư mục, số ảnh không đổi |
| 8 | `liet_ke_danh_tinh` trên thư mục không tồn tại | dict rỗng, không ném | `== {}` |
| 9 | `chon_danh_tinh` **cùng seed** hai lần | tái lập được (R15) | `chon_danh_tinh(d,10,2,42) == chon_danh_tinh(d,10,2,42)` |
| 10 | `chon_danh_tinh` **khác seed** | kết quả khác | `chon_danh_tinh(d,10,2,42) != chon_danh_tinh(d,10,2,7)` |
| 11 | `chon_danh_tinh` loại danh tính thiếu ảnh | không chọn nhầm | Với `toi_thieu_anh=3`, danh tính có 2 ảnh **không** có trong kết quả |
| 12 | `chon_danh_tinh` trả **đúng số lượng** và **đã sắp xếp** | | `len(kq) == so_luong` **và** `kq == sorted(kq)` |
| 13 | `chon_danh_tinh` khi **không đủ** danh tính thoả điều kiện | raise `LoiCauHinh`, thông báo nêu số tìm được và số cần | `pytest.raises(LoiCauHinh)` **và** thông báo chứa **cả hai** con số — phân biệt với `LoiCauHinh` do nguyên nhân khác |
| 14 | `sao_chep` — **đường thành công** | chép đúng số ảnh, giữ nguyên tên | Số tệp trong `out_dir` `==` tổng ảnh của các danh tính đã chọn |
| 15 | `sao_chep` giữ **cấu trúc thư mục theo danh tính** | truy ngược được về nguồn | Tồn tại `out_dir/<tên danh tính>/<tên ảnh gốc>` |
| 16 | `sao_chep` **không ghi đè** tệp đã có | dữ liệu cũ nguyên vẹn | Ghi nội dung đã biết vào một tệp đích, sau khi gọi nội dung **không đổi** |
| 17 | `sao_chep` với `dry_run=True` | không ghi gì | `list(out_dir.rglob("*"))` không đổi trước và sau |
| 18 | `sao_chep` trả bản ghi khớp số danh tính | | `len({r["identity"] for r in ban_ghi}) == len(da_chon)` |
| 19 | `ghi_manifest` tạo tệp có dòng tiêu đề | | Dòng đầu chứa `file`, `identity`, `n_images`, `source_sha256`, `selected_seed` |
| 20 | Số dòng dữ liệu manifest khớp số ảnh đã chép | | `so_dong == len(list(out_dir.rglob("*.jpg")))` |
| 21 | `tai_ve` khi tệp **đã tồn tại** | bỏ qua, không tải lại, trả đúng đường dẫn | Tạo sẵn tệp đích với nội dung đã biết, gọi `tai_ve` với url giả `"http://khong-ton-tai.invalid/x.tgz"` → **không ném**, trả đường dẫn đó, **và nội dung tệp không đổi** (chứng minh không tải đè) |
| 22 | `tai_ve` với `dry_run=True` | không tạo tệp nào | `not dich.exists()` sau khi gọi |
| 23 | `main --dry-run` | thoát `0`, **có in kế hoạch**, không ghi file | `main() == 0`, `data/` không phát sinh tệp, **và** `capsys` bắt được số danh tính dự kiến chọn — chứng minh thân hàm đã chạy chứ không thoát sớm |
| 24 | `main` với `--expect-sha256` **lệch** — ⚠️ **tiền đề: tệp nén mồi phải là tar HỢP LỆ** | thoát `1` **vì so mã băm**, không phải vì lỗi khác | `main() == 1` **và** thông báo chứa **cả hai** chuỗi mã băm. ⚠️ Mồi bằng tệp không phải tar sẽ khiến `main()` trả `1` từ bước giải nén — ca test xanh mà nhánh mã băm **không hề chạy** |
| 24a | `main` với `--expect-sha256` **khớp** — đường thành công của cùng nhánh | thoát `0`, đi qua được bước so mã băm | `main() == 0` với cùng tệp nén hợp lệ ở dòng 24 và mã băm đúng |
| 25 | `ghi_manifest` với bản ghi **thiếu khoá** bắt buộc | raise `LoiCauHinh` nêu tên khoá thiếu | `pytest.raises(LoiCauHinh)` khi bản ghi không có `source_sha256`, **và** thông báo chứa chuỗi `source_sha256` — chứng minh đúng nhánh kiểm khoá |
| 26 | `ghi_manifest` với bản ghi **đủ sáu khoá** — đường thành công | ghi bình thường | Tệp tạo ra, dòng dữ liệu có đủ giá trị ở cả sáu cột, **không cột nào rỗng** |
| 27 | `main` chạy lần hai với **seed khác** trên `out_dir` đã có manifest cũ | thoát `1` **vì lệch seed**, không trộn dữ liệu | `main() == 1` **và** thông báo chứa **cả hai** giá trị seed ở dạng có dấu nháy (`'42'`, `'7'`) — dạng trần dễ khớp nhầm chữ số trong đường dẫn `tmp_path` |
| 27a | Sau dòng 27, dữ liệu cũ **nguyên vẹn** | không trộn hai tập impostor | Số thư mục danh tính trong `out_dir` **không đổi**, và manifest cũ **không bị ghi đè** |
| 27b | `main` khi manifest cũ có `selected_seed` **không phải số** | thoát `1`, thông báo nhắc dọn `out_dir` | `main() == 1`, **không** ném `ValueError` ra ngoài, thông báo chứa `out_dir` |
| 27c | `main` khi manifest cũ **thiếu hẳn cột** `selected_seed` | thoát `1` — **không** được âm thầm coi như chưa có manifest | `main() == 1`, **không** ném ra ngoài, thông báo chứa `selected_seed`. ⚠️ `dict.get()` trả `None` chứ không ném, nên nhánh này phải kiểm tường minh |
| 28 | `main` chạy lần hai với **cùng seed** — đường thành công | chạy lại được, không lỗi | `main() == 0`, số thư mục danh tính **không đổi** |

---

## 6. Tiêu chí nghiệm thu

- [ ] **Mỗi dòng bảng §5 có ít nhất một ca test, mỗi ca có assert thật** — hàm rỗng là CHẶN-B
- [ ] **Không ca test nào truy cập mạng**:
      `grep -nE "urlopen|urlretrieve|requests\.|socket" tests/test_download_lfw.py` không có kết quả
- [ ] **Không ca test nào gọi `subprocess`**
- [ ] **Không ca test nào ghi ra ngoài `tmp_path`** — sau khi chạy `pytest`,
      `git status --short --untracked-files=all` không có tệp mới, `data/` không phát sinh gì
- [ ] `pytest -q` xanh toàn bộ — **86 ca cũ vẫn đạt**, cộng ca mới (bảng §5 nay có **30 dòng**)
- [ ] `pytest -q` **xanh trong container ARM64**:
      `MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q`
- [ ] `black --check --line-length 100 src tests scripts` và `ruff check src tests scripts` sạch
- [ ] **Kiểm phạm vi file**:
      `git status --short --untracked-files=all | grep -v "docs/review/" | wc -l` trả `2`
- [ ] **Không thư viện ngoài `requirements.txt`**:
      `grep -nE "^\s*(import|from) (requests|PIL|imageio|skimage|pandas|tqdm)" scripts/download_lfw.py`
      không có kết quả
- [ ] `python scripts/download_lfw.py --help` chạy được, mô tả tiếng Việt
- [ ] `python scripts/download_lfw.py --dry-run` thoát `0`, in kế hoạch, **không tạo tệp nào**

---

## 7. Quy tắc áp dụng

| Mã | Vì sao |
|---|---|
| **G1** | Mọi tham số từ `configs/data.yaml` mục `lfw` |
| **G2, G3** | `lay_logger(__name__)` cho tiến trình; `print` chỉ cho bảng tóm tắt và trích dẫn cuối |
| **G4** | Type hints + docstring tiếng Việt |
| **G5** | Lỗi mạng, lỗi giải nén bọc thành `LoiCauHinh` bằng `raise ... from e` |
| **R15** | `--seed` mặc định lấy từ config; cùng seed phải chọn ra cùng tập danh tính |
| **R28c** | In trích dẫn LFW và địa chỉ trang chủ ở cuối phiên chạy; **không phát hành lại** ảnh LFW |

**Thư viện được phép**: chỉ **thư viện chuẩn** — `urllib.request`, `tarfile`, `hashlib`, `random`,
`shutil`, `pathlib`, `csv`, `argparse`, `datetime`. **Không dùng `requests`, `tqdm`, `pandas`.**
Thiếu thư viện → **dừng và báo**, không tự cài.

### Hai điểm an toàn bắt buộc

**Giải nén phải chặn đường dẫn vượt ra ngoài.** Dùng `tarfile.extractall(..., filter="data")` —
có từ Python 3.11.4, môi trường dự án là 3.11.15 và 3.12.5 nên dùng được. Không có bộ lọc này, một
tệp nén độc hại chứa mục `../../` sẽ ghi đè tệp bất kỳ trên máy.

**Tính mã băm phải đọc theo khối.** Tệp LFW cỡ hàng trăm MB; `hashlib.sha256(p.read_bytes())` nạp
toàn bộ vào RAM. Đọc từng khối 1 MB.

---

## 8. Ngoài phạm vi — KHÔNG làm

- **Hiệu chỉnh miền dữ liệu** (`lfw_adapted`) → bước 1.8, mã việc riêng
- Phát hiện khuôn mặt, cắt, căn chỉnh 112×112 → bước 1.9
- Chia tập `val`/`test` → bước 1.11
- Tải bản `funneled` hoặc `deep-funneled` — **cố ý dùng bản gốc chưa căn chỉnh**, xem chú thích trong
  `configs/data.yaml`
- Thanh tiến trình, tải song song nhiều luồng, tải tiếp khi đứt mạng
- Sửa `configs/data.yaml`
- **Cố ý không phủ bằng test**: nhánh "tệp nén có nhiều thư mục gốc" của `giai_nen`. `lfw.tgz` thật
  chỉ có một thư mục `lfw/`, và nếu rơi vào nhánh này thì `chon_danh_tinh` sẽ ném `LoiCauHinh` —
  hỏng ồn ào chứ không hỏng âm thầm, nên chấp nhận được
