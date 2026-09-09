# P3-03 — `scripts/enroll.py`: sinh vectơ đại diện cho người đã đăng ký

| | |
|---|---|
| **Bước pipeline** | CLAUDE.md §5 Phase 3, bước 3.4 |
| **Nhánh** | `feat/p3-03-enroll` |
| **Phụ thuộc** | `P3-01` (backend ArcFace) và `P3-02` (backend dlib) — cả hai đã gộp `dev` |
| **Chặn** | bước 3.5 (quét ngưỡng, ROC) và `notebooks/06_nguong_va_roc.ipynb` |

---

## 1. Mục tiêu

Đăng ký một người là biến nhiều ảnh của họ thành **một** vectơ đại diện, lưu lại để về sau so khớp.
Mã việc này viết script dòng lệnh làm việc đó cho toàn bộ một thư mục ảnh, chạy được với **cả hai**
phương án nhận diện mà không đổi một dòng mã nào.

Đây là mắt xích còn thiếu giữa khối nhận diện (đã xong) và phép quét ngưỡng (bước 3.5): chưa có
gallery thì không có gì để so, không có đường cong ROC, và không chốt được ngưỡng.

---

## 2. Phạm vi file — danh sách trắng

| Tệp | Trạng thái |
|---|---|
| `src/recognizer/factory.py` | **mới** |
| `src/recognizer/__init__.py` | sửa — thêm export, **chỉ cộng thêm**, không xoá dòng nào |
| `scripts/enroll.py` | **mới** |
| `tests/test_recognizer_factory.py` | **mới** |
| `tests/test_enroll.py` | **mới** |

Không tệp nào khác. Không sửa `dlib_backend.py`, `arcface_backend.py`, `base.py`, `configs/`.

**Vì sao factory nằm cùng mã việc này thay vì tách riêng.** Script phải dựng backend từ cấu hình,
mà hai backend hiện nhận cấu hình theo hai kiểu khác nhau (§3 dưới). Factory là điều kiện cần của
script, dài chừng 40 dòng; tách nó thành một mã việc riêng chỉ thêm một nhịp chờ mà không giảm rủi
ro nào.

---

## 3. Dữ kiện — đã kiểm ngày 04/09/2026

| Dữ kiện | Giá trị | Hệ quả với thiết kế |
|---|---|---|
| `data/processed/lfw_original/` | 200 ảnh PNG, 152 danh tính | Dữ liệu duy nhất chạy thật được lúc này |
| Danh tính có ≥ 2 ảnh | 27 |  |
| Nhiều ảnh nhất | `George_W_Bush` 9 · `Colin_Powell` 9 | **Không danh tính nào đạt 10 ảnh** |
| `configs/recognize.yaml` `enroll.min_images_per_user` | `10` | Chạy nguyên cấu hình trên LFW sẽ đăng ký **0 người** — xem §6.4 |
| `data/embeddings/` | **chưa tồn tại** | Script phải tự tạo thư mục |
| `data/splits/` | **chưa tồn tại** (bước 1.11 chưa làm) | Không được phụ thuộc tệp split; nhận thư mục trực tiếp |
| `DlibFaceRecognizer.__init__` | nhận **toàn bộ** `recognize.yaml` | Factory phải bóc nhánh khác nhau cho từng backend |
| `ArcFaceBackend.__init__` | nhận **riêng** `cfg["arcface"]` |  |
| Số chiều | dlib 128 · ArcFace 512 | Vectơ hai backend **không được trộn** — xem §6.3 |
| `src/detector/factory.py` | đã có, mẫu để bám | Cùng cách đặt tên và cách ném lỗi |

---

## 4. Tham số — đọc từ `configs/recognize.yaml`

| Khoá | Giá trị hiện tại | Dùng làm gì |
|---|---|---|
| `backend` | `arcface` | Backend mặc định khi không truyền `--backend` |
| `enroll.gallery_dir` | `data/embeddings` | Thư mục đích mặc định |
| `enroll.min_images_per_user` | `10` | Số ảnh tối thiểu để đăng ký một người |
| `enroll.chuan_hoa_truoc_khi_trung_binh` | `true` | **Chỉ để đối chiếu** — phép chuẩn hoá do backend làm, script không tự làm |

Không thêm khoá mới vào `configs/`. Nếu thấy cần, dừng lại và báo về.

---

## 5. Giao diện

### 5.1. `src/recognizer/factory.py`

```python
TEN_BACKEND_DLIB = "dlib"
TEN_BACKEND_ARCFACE = "arcface"


def tao_bo_nhan_dien(cfg: dict, ten_backend: str | None = None) -> BoNhanDien:
    """Chọn và khởi tạo backend nhận diện theo tên.

    Args:
        cfg: TOÀN BỘ nội dung configs/recognize.yaml.
        ten_backend: Tên backend cần dựng. None thì lấy từ khoá `backend` của cfg.

    Returns:
        Backend đã khởi tạo, dùng chung giao diện `BoNhanDien`.

    Raises:
        LoiCauHinh: tên backend không thuộc hai giá trị hợp lệ, hoặc cfg thiếu khoá.
        LoiMoHinh: tên hợp lệ nhưng mô hình không nạp được (do backend ném ra).
    """
```

### 5.2. `scripts/enroll.py` — giao diện dòng lệnh

```
python -m scripts.enroll --vao <thư mục> [tuỳ chọn]
```

| Cờ | Mặc định | Ý nghĩa |
|---|---|---|
| `--vao` | *(bắt buộc)* | Thư mục ảnh, cấu trúc `<vao>/<user_id>/*.png` |
| `--ra` | `enroll.gallery_dir` trong cấu hình | Thư mục đích |
| `--config` | `configs/recognize.yaml` | Tệp cấu hình |
| `--backend` | khoá `backend` trong cấu hình | `dlib` hoặc `arcface` |
| `--toi-thieu` | `enroll.min_images_per_user` | Ghi đè số ảnh tối thiểu — xem §6.4 |
| `--nguoi` | *(rỗng — lấy tất cả)* | Danh sách `user_id` cần đăng ký, cách nhau bằng dấu phẩy |
| `--seed` | `42` | Ghi vào metadata (R15) |
| `--dry-run` | tắt | Chỉ in kế hoạch, **không ghi tệp nào** |

Trả về `0` khi thành công, `1` khi thất bại. Bám đúng cách `scripts/preprocess.py` xử lý mã trả về,
cách in lỗi ra stdout, và cách gọi `sys.stdout.reconfigure`.

### 5.3. Đầu ra

```
<ra>/<backend>/<user_id>.npy      — vectơ đại diện, float32, hình dạng (so_chieu,)
<ra>/<backend>/manifest.csv       — một dòng mỗi user_id ĐƯỢC XÉT, kể cả người bị bỏ qua
<ra>/<backend>/gallery.meta.json  — siêu dữ liệu của cả lượt chạy
```

`manifest.csv` — sáu cột, đúng thứ tự:

| Cột | Nội dung |
|---|---|
| `user_id` | tên thư mục con |
| `so_anh_tim_thay` | số ảnh đọc được |
| `so_anh_dung` | số ảnh thực sự đưa vào `enroll()`; `0` khi bị bỏ qua |
| `trang_thai` | `da_dang_ky` · `thieu_anh` · `loi_doc_anh` |
| `so_chieu` | số chiều vectơ ghi ra; rỗng khi bị bỏ qua |
| `tep_ra` | đường dẫn tương đối tệp `.npy`; rỗng khi bị bỏ qua |

`gallery.meta.json` — bắt buộc có: `backend`, `so_chieu`, `duong_dan_vao`, `so_nguoi_da_dang_ky`,
`so_nguoi_bo_qua`, `min_images_per_user_da_dung`, `min_images_per_user_trong_cau_hinh`, `seed`,
`thoi_gian`, `commit`, `git_dirty`, `moi_truong`, `software`.

`moi_truong` nhận đúng một trong ba giá trị `pc_x86` · `docker_arm64` · `pi5`, theo
`.claude/instructions/experiment-protocol.instructions.md`. Bám cách `scripts/benchmark_detect.py`
đã dựng khối này, kể cả cách `git_dirty` giới hạn theo đường dẫn ảnh hưởng phép chạy (`P2-06c`).

---

## 6. Thiết kế bắt buộc

### 6.1. Script KHÔNG tự tính vectơ trung bình

Gọi `backend.enroll(danh_sach_anh, cfg_enroll)` và ghi thẳng kết quả. **Cấm** script tự cộng trung
bình rồi chuẩn hoá.

Lý do: phép chuẩn hoá L2 từng vectơ *trước* khi lấy trung bình là một quyết định phương pháp đã chốt
và đã có ca kiểm thử ở cả hai backend. Viết lại nó trong script tạo ra bản sao thứ hai của cùng một
logic — hai bản sao trôi khỏi nhau theo thời gian, và không có gì phát hiện được vì cả hai đều trả
về vectơ độ dài 1 trông hợp lệ như nhau.

### 6.2. Người không đủ ảnh thì BỎ QUA, không hạ ngưỡng

`backend.enroll()` ném `ValueError` khi danh sách ngắn hơn `min_images_per_user`. Script bắt lỗi
này, ghi `trang_thai = thieu_anh` vào manifest, **không ghi tệp `.npy`**, và chạy tiếp sang người
kế. Không được bắt rồi thử lại với ngưỡng thấp hơn.

Đây là ranh giới an ninh: một người đăng ký bằng 2 ảnh có vectơ đại diện kém ổn định trước thay đổi
góc chụp và ánh sáng, làm tăng cả tỉ lệ nhận nhầm lẫn tỉ lệ từ chối oan. Hạ ngưỡng ngầm để "chạy cho
xong" là đúng thứ mà `R7` cấm.

### 6.3. Vectơ hai backend không được trộn

Thư mục đích tách theo tên backend (`<ra>/dlib/` và `<ra>/arcface/`). Trước khi ghi mỗi tệp, kiểm
`vec.shape == (backend.so_chieu,)` và ném `LoiMoHinh` nếu lệch.

Lý do: 128 và 512 chiều nằm chung một thư mục thì bước quét ngưỡng sẽ nạp nhầm và đổ ở một chỗ hoàn
toàn khác, với thông báo không liên quan gì tới nguyên nhân thật.

### 6.4. `--toi-thieu` — cờ thử nghiệm, phải để lại dấu vết

Không danh tính LFW nào đạt 10 ảnh (§3), nên chạy nguyên cấu hình sẽ đăng ký 0 người. Cờ này cho
phép hạ ngưỡng để **kiểm chức năng script**.

Ràng buộc:

1. Khi giá trị dùng khác giá trị trong cấu hình, script **phải** ghi một dòng cảnh báo mức `WARNING`
   nêu cả hai con số.
2. `gallery.meta.json` ghi **cả hai** khoá `min_images_per_user_da_dung` và
   `min_images_per_user_trong_cau_hinh`.
3. Giá trị âm hoặc không phải số nguyên → `LoiCauHinh`.

Điều 1 và 2 không phải thủ tục thừa: gallery sinh ra bằng ngưỡng hạ thấp mà không có dấu vết thì ba
tuần sau không ai phân biệt được nó với gallery thật, và một con số FAR đo trên đó sẽ đi thẳng vào
báo cáo mà không ai biết nó không hợp lệ.

### 6.5. `user_id` lấy từ tên thư mục, phải kiểm an toàn

Tên thư mục con trở thành tên tệp `.npy`. Từ chối tên rỗng, tên chứa dấu tách đường dẫn, và tên
bằng `.` hoặc `..` — ném `LoiCauHinh`. Thư mục con không chứa ảnh nào: bỏ qua, không tính vào
manifest.

### 6.6. Không `print` trong `src/`

`src/recognizer/factory.py` chỉ dùng `logging` (R23). `scripts/enroll.py` được phép in ra stdout cho
người chạy, đúng như `scripts/preprocess.py` đang làm.

---

## 7. Bảng tiêu chí nghiệm thu

Mỗi dòng là một ca kiểm thử, đặt tên `test_dongNN_<mô tả ngắn>`.

### `tests/test_recognizer_factory.py`

| # | Ca | Kỳ vọng |
|---|---|---|
| 01 | `tao_bo_nhan_dien(cfg)` với `cfg["backend"] = "dlib"` | trả về thể hiện `DlibFaceRecognizer` |
| 02 | `tao_bo_nhan_dien(cfg)` với `cfg["backend"] = "arcface"` | trả về thể hiện `ArcFaceBackend` |
| 03 | `ten_backend` truyền vào **ghi đè** khoá `backend` của cfg | dựng đúng backend được truyền |
| 04 | Tên backend lạ (`"resnet"`, `""`, `None` mà cfg cũng thiếu khoá) | `LoiCauHinh`, thông báo nêu tên đã nhận và danh sách hợp lệ |
| 05 | Backend trả về là thể hiện của `BoNhanDien` | `isinstance(bo, BoNhanDien)` cho cả hai |
| 06 | Factory chuyển đúng nhánh cấu hình cho từng backend | dlib nhận toàn bộ cfg, ArcFace nhận `cfg["arcface"]` |

Ca 01, 02, 03, 05, 06 cần trọng số thật → đánh dấu `@pytest.mark.slow`. Ca 04 không cần.

### `tests/test_enroll.py`

| # | Ca | Kỳ vọng |
|---|---|---|
| 07 | Thư mục có 3 người đủ ảnh | 3 tệp `.npy`, mỗi tệp hình dạng `(so_chieu,)`, kiểu `float32` |
| 08 | Vectơ ghi ra có độ dài L2 bằng 1 | `abs(norm - 1) < 1e-5` |
| 09 | Người có ít ảnh hơn ngưỡng | **không** có tệp `.npy`; manifest ghi `thieu_anh` |
| 10 | Manifest có đủ sáu cột, đúng thứ tự | đọc lại bằng `csv.reader`, so danh sách tiêu đề |
| 11 | Manifest có dòng cho **cả** người bị bỏ qua | số dòng bằng số thư mục con có ảnh |
| 12 | `gallery.meta.json` đủ mọi khoá bắt buộc ở §5.3 | không khoá nào thiếu |
| 13 | `moi_truong` nhận đúng một trong ba giá trị hợp lệ | thuộc tập `{pc_x86, docker_arm64, pi5}` |
| 14 | `--toi-thieu` khác cấu hình | meta ghi **cả hai** con số, khác nhau |
| 15 | `--toi-thieu` khác cấu hình | có bản ghi log mức `WARNING` (bắt bằng `caplog`) |
| 16 | `--toi-thieu` âm hoặc không phải số nguyên | mã trả về `1`, không tệp nào được ghi |
| 17 | Hai backend ghi vào **hai thư mục khác nhau** | `<ra>/dlib/` và `<ra>/arcface/` cùng tồn tại, không lẫn tệp |
| 18 | Vectơ dlib 128 chiều, ArcFace 512 chiều trên **cùng** thư mục ảnh | đọc lại hai tệp, so `shape` |
| 19 | `--dry-run` | thư mục đích **không được tạo**, không tệp nào ghi ra, mã trả về `0` |
| 20 | `--nguoi A,B` | chỉ 2 tệp `.npy`, đúng hai tên đó |
| 21 | `--nguoi` chứa tên không tồn tại | mã trả về `1`, thông báo nêu tên sai |
| 22 | Thư mục con rỗng | bỏ qua, **không** xuất hiện trong manifest |
| 23 | `--vao` không tồn tại | mã trả về `1`, không ngoại lệ nào thoát ra ngoài `main` |
| 24 | Ảnh hỏng (tệp `.png` 0 byte) | `trang_thai = loi_doc_anh`, các người khác vẫn chạy xong |
| 25 | Chạy lại lần hai trên cùng đầu vào | tệp `.npy` giống hệt lần đầu (so `sha256`) |
| 26 | Script **không** tự tính trung bình | `enroll` của backend được gọi đúng một lần cho mỗi người (dùng backend giả đếm số lần gọi) |

Ca 07, 08, 17, 18, 25 cần trọng số thật → `@pytest.mark.slow`. Các ca còn lại dùng **backend giả**
cài `BoNhanDien` bằng vectơ ngẫu nhiên có seed, để chạy được trong container không có `models/`.

Ca 26 là ca canh §6.1 và là ca quan trọng nhất tệp này.

---

## 8. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

Mỗi khối một lệnh. Đỏ thì sửa rồi chạy lại từ đầu danh sách.

```bash
python -m black --check --line-length 100 src tests scripts
```

```bash
python -m ruff check src tests scripts
```

```bash
python -m pytest tests/test_recognizer_factory.py tests/test_enroll.py -v
```

```bash
python -m pytest -q
```

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

```bash
git status --short --untracked-files=all
```

Kết quả mong đợi của lệnh cuối: đúng năm dòng của §2, không tệp lạ, không tệp nào trong `data/`.

### 8.1. Quét mẫu vi phạm

```bash
grep -rn "print(" src/recognizer/
```

```bash
grep -rn "except Exception" src/recognizer/factory.py scripts/enroll.py
```

```bash
grep -rn "np.mean\|\.mean(\|linalg.norm" scripts/enroll.py
```

Cả ba phải **rỗng**. Lệnh thứ ba canh §6.1: script không được có phép tính trung bình hay chuẩn hoá
nào của riêng nó.

### 8.2. Phép đột biến — dựng lại từng phép, khôi phục và đối chiếu `sha256`

Sao lưu tệp ra ngoài repo trước, khôi phục bằng bản sao đó, đối chiếu `sha256` sau mỗi phép.

| # | Phép | Ca phải đỏ |
|---|---|---|
| ĐB1 | Trong `enroll.py`, thay lời gọi `backend.enroll(...)` bằng trung bình tự tính rồi chuẩn hoá | dòng 26 |
| ĐB2 | Bỏ nhánh bắt `ValueError` khi thiếu ảnh, cho người thiếu ảnh vẫn được ghi `.npy` | dòng 09 |
| ĐB3 | Bỏ tên backend khỏi đường dẫn đích, ghi thẳng vào `<ra>/<user_id>.npy` | dòng 17 |
| ĐB4 | Trong `factory.py`, truyền `cfg["arcface"]` cho cả hai backend | dòng 01 hoặc 06 |

**ĐB1 quan trọng nhất.** Nó đúng loại lỗi im lặng mà §6.1 mô tả: vectơ vẫn có đủ số chiều, vẫn có độ
dài 1, mọi ca khác vẫn xanh. Chỉ ca 26 phân biệt được. Nếu ĐB1 không làm đỏ ca nào, ca 26 chưa canh
đúng chỗ — sửa ca test, đừng sửa mã sản phẩm.

---

## 9. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` line-length 100, `ruff` sạch.
- Type hints cho mọi hàm public, docstring tiếng Việt kiểu Google.
- Ngoại lệ dùng lớp trong `src/common/exceptions.py`; **không** `except Exception` trần.
- `pytest --collect-only -m "not slow"` phải chạy trót lọt kể cả khi chưa có `models/`.
- Không ghi bất cứ thứ gì vào `data/` trong lúc chạy `pytest` — dùng `tmp_path`.
- Không commit, không dựng image, không `pip install`.

---

## 10. Ngoài phạm vi — KHÔNG làm ở mã việc này

- Quét ngưỡng, ROC/DET, tính FAR (bước 3.5 và 3.7).
- Chuẩn hoá chữ ký `__init__` của hai backend cho giống nhau (§3.5 biên bản `P3-02`) — factory che
  bất đối xứng đó lại là đủ cho bước này.
- `scripts/benchmark_recognize.py`.
- Chia tập `data/splits/` (bước 1.11).

---

## 11. Báo cáo khi xong

Dán về: kết quả nguyên văn của mọi lệnh §8, bảng bốn phép đột biến với ca đỏ tương ứng, và `sha256`
trước/sau mỗi phép khôi phục. Không commit.

---

## 11b. Lượt của người dùng — sau khi §8 xanh

Chạy thật trên LFW để kiểm script làm việc ngoài đời, không chỉ trong `tmp_path`.

```bash
python -m scripts.enroll --vao data/processed/lfw_original --backend dlib --toi-thieu 3 --dry-run
```

```bash
python -m scripts.enroll --vao data/processed/lfw_original --backend dlib --toi-thieu 3
```

```bash
python -m scripts.enroll --vao data/processed/lfw_original --backend arcface --toi-thieu 3
```

```bash
python -c "import json,pathlib;[print(p, json.loads(p.read_text(encoding='utf-8'))['so_nguoi_da_dang_ky']) for p in sorted(pathlib.Path('data/embeddings').rglob('gallery.meta.json'))]"
```

Kết quả mong đợi: với ngưỡng 3 ảnh, số người đăng ký được phải **bằng nhau** ở hai backend — cùng
dữ liệu vào, cùng quy tắc lọc, chỉ khác mô hình. Lệch nghĩa là một trong hai backend đổ ở một số ảnh
mà backend kia đọc được, và đó là chuyện phải tìm hiểu trước khi đi tiếp sang bước 3.5.

Nhắc lại: gallery sinh bằng `--toi-thieu 3` **không** dùng cho bất kỳ con số nào trong báo cáo. Nó
tồn tại để kiểm chức năng script. Gallery thật dựng từ `data/raw/` với ngưỡng 10 ảnh, sau khi có
camera.
