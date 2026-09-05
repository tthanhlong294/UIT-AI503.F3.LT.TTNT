# P3-04 — `enroll.py` ghi gallery nguyên khối, và siết hai chốt kiểm thử

| | |
|---|---|
| **Nguồn** | §12.1, §12.2, §12.3 biên bản `docs/review/P3-03-enroll.review.md` (vòng 2, cả ba mức 🔵) |
| **Nhánh** | `feat/p3-04-enroll-ghi-nguyen-khoi` |
| **Phụ thuộc** | `P3-03` đã gộp `dev` (commit gộp `7065c98`) |
| **Chặn** | bước 3.5 — script quét ngưỡng sẽ nạp thẳng `data/embeddings/` |

---

## 1. Mục tiêu

`scripts/enroll.py` hiện ghi từng tệp `.npy` **trong** vòng lặp, còn `manifest.csv` và
`gallery.meta.json` chỉ ghi **sau** khi vòng lặp kết thúc. Lượt chạy dừng giữa chừng vì thế để lại
một thư mục có `.npy` mà không có hai tệp kia.

Mã việc này làm cho thư mục gallery chỉ tồn tại ở **hai** trạng thái: hoặc chưa có, hoặc có đủ.
Không có trạng thái thứ ba.

Kèm theo, siết hai chốt kiểm thử mà lượt review vòng 2 chứng minh là **không canh được gì** — cả
hai đều nằm trong `tests/test_enroll.py`, cùng tệp mà phần trên dù sao cũng phải mở ra. Mã sản phẩm
ở hai chỗ đó **đúng**; thiếu sót nằm ở tập test.

### Vì sao đáng làm ngay, trước bước 3.5

Một thư mục chỉ có `.npy` vẫn **đủ hình dạng** để bước 3.5 nạp bằng `rglob("*.npy")`. Nó thiếu
`gallery.meta.json`, tức mất `commit`, `git_dirty`, `moi_truong` và `min_images_per_user_da_dung` —
toàn bộ dấu vết mà R17 yêu cầu. Số FAR tính từ một gallery như vậy không truy về đâu được (R6), và
không có gì trong pipeline hiện tại phát hiện ra điều đó.

Đường dẫn tới trạng thái này mới xuất hiện sau bản vá `P3-03` vòng 2: `LoiMoHinh` từ nhánh phân biệt
thiếu-ảnh nay có thật, và biên bản đã đo được đúng trạng thái đó trên máy — thư mục đích còn lại
`['nguoi_a.npy']`, không manifest, không meta.

---

## 2. Phạm vi file — danh sách trắng

| Tệp | Trạng thái |
|---|---|
| `scripts/enroll.py` | sửa |
| `tests/test_enroll.py` | sửa — **chỉ cộng thêm ca mới**, không xoá ca nào |

Không tệp nào khác. Không đụng `src/`, không đụng `configs/`.

---

## 3. Dữ kiện — đã kiểm ngày 05/09/2026

| Dữ kiện | Giá trị |
|---|---|
| Ghi `.npy` | `scripts/enroll.py:491-494`, trong vòng lặp |
| Ghi `manifest.csv` | `:502`, ngoài khối `try` |
| Ghi `gallery.meta.json` | `:530`, ngoài khối `try` |
| Nhánh thoát sớm | `:497-500`, `except (LoiCauHinh, LoiMoHinh)` → `return 1` |
| Gallery hiện có | `data/embeddings/{dlib,arcface}/`, mỗi thư mục 8 tệp `.npy` + `manifest.csv` + `gallery.meta.json` |
| Số test `tests/test_enroll.py` hiện tại | 19 ca |

---

## 4. Thiết kế bắt buộc

### 4.1. Bất biến phải giữ

> Thư mục `<ra>/<backend>/` hoặc **không tồn tại**, hoặc chứa **đủ cả ba** loại tệp:
> ít nhất một `.npy`, `manifest.csv`, và `gallery.meta.json`.

Ngoại lệ duy nhất: lượt chạy hợp lệ mà **không ai** đủ điều kiện đăng ký. Khi đó thư mục vẫn phải có
`manifest.csv` và `gallery.meta.json` (chúng chính là bằng chứng giải thích vì sao không có ai),
nhưng không có `.npy` nào. Đây là kết quả đúng, không phải trạng thái dở dang.

### 4.2. Ghi qua thư mục tạm rồi đổi tên

1. Chọn thư mục tạm `<ra>/.<backend>.dang-ghi`. Nếu nó đã tồn tại (tàn dư của lượt hỏng trước đó),
   **xoá sạch** rồi tạo lại.
2. Ghi toàn bộ `.npy`, `manifest.csv`, `gallery.meta.json` vào thư mục tạm.
3. Chỉ khi cả ba đã ghi xong mới chuyển sang vị trí thật:
   - nếu `<ra>/<backend>/` đã tồn tại, đổi tên nó thành `<ra>/.<backend>.cu`;
   - đổi tên thư mục tạm thành `<ra>/<backend>/`;
   - xoá `<ra>/.<backend>.cu`.
4. Ở **mọi** nhánh thoát sớm — `except`, và cả lỗi phát sinh giữa bước 3 — xoá thư mục tạm trước khi
   `return 1`.

Không dùng `os.replace` thẳng lên một thư mục đích đang tồn tại và không rỗng: hành vi khác nhau
giữa Windows và Linux, mà đề tài chạy trên cả hai.

### 4.3. Vì sao không chọn phương án "xoá các `.npy` vừa ghi"

Biên bản §12.1 nêu hai phương án. Phương án xoá bị loại vì nó phải theo dõi chính xác tệp nào thuộc
lượt này, và một sai sót trong danh sách đó sẽ xoá nhầm gallery của lượt trước — biến một lỗi có
thông báo rõ ràng thành mất dữ liệu. Ghi qua thư mục tạm không đụng tới gallery cũ cho tới khi lượt
mới chắc chắn thành công.

Hệ quả phụ đáng giá: gallery cũ được thay **nguyên khối**. Chạy lại `enroll.py` mà hỏng giữa chừng
thì gallery cũ vẫn còn nguyên và vẫn dùng được, thay vì bị trộn nửa cũ nửa mới.

### 4.4. Quy ước tên: thư mục con bắt đầu bằng dấu chấm không phải gallery

Nếu tiến trình bị giết cứng (Ctrl+C, mất điện) thì nhánh dọn dẹp ở 4.2 điều 4 không chạy, và thư mục
tạm còn lại. Vì vậy tên nó phải phân biệt được với gallery thật.

Ghi quy ước này thành hằng số có tên trong `enroll.py`, kèm comment nêu rõ bước 3.5 phải bỏ qua mọi
thư mục con có tên bắt đầu bằng `.`. Bản thân bước 3.5 nằm ngoài phạm vi mã việc này, nhưng quy ước
phải được đặt ra ở đây — nơi sinh ra thư mục đó.

### 4.5. Ca `test_dong09b` phải phân biệt lớp ngoại lệ (§12.2)

**Bằng chứng review**: đổi `raise LoiMoHinh(` thành `raise LoiCauHinh(` tại `scripts/enroll.py:208`
cho **19 passed, 0 failed** — không ca nào đỏ.

Nguyên nhân: `main()` bắt **cả hai** lớp `(LoiCauHinh, LoiMoHinh)` rồi cùng trả về `1`, nên chốt
`ma == 1` mù trước việc phân loại. Mà lớp ngoại lệ chính là thứ phân biệt "cấu hình sai" với "mô
hình hỏng" ở mọi chỗ gọi `xu_ly_mot_nguoi` từ ngoài `main()`.

Hai việc:

1. Thêm ca gọi **thẳng** `xu_ly_mot_nguoi` (không qua `main`) và dùng `pytest.raises(LoiMoHinh)`.
   Đây là chốt duy nhất phân biệt được hai lớp.
2. Trong ca `test_dong09b` hiện có, đổi `if manifest.exists():` (`tests/test_enroll.py:281`) thành
   `assert not manifest.exists()`. Review chứng minh manifest chưa từng được ghi khi lượt chạy dừng,
   nên khối bên trong `if` là **nhánh chết** — nó không bao giờ chạy, và một ca test có nhánh không
   bao giờ chạy là một chốt tưởng có mà không có.

Sau §4.2, khẳng định này còn mạnh hơn trước: thư mục đích không tồn tại thì manifest đương nhiên
cũng không.

### 4.6. Biên `so_anh == ngưỡng` phải có người gác (§12.3)

**Bằng chứng review**: đổi `<` thành `<=` tại `scripts/enroll.py:204` cho **19 passed, 0 failed**.
Ba ca liên quan dùng 2/3, 5/3 và 2/3 — không ca nào đặt số ảnh **bằng đúng** ngưỡng.

Mã hiện tại đúng: `so_anh = 3` với ngưỡng 3 đi nhánh `raise`, khớp với `<` ở `dlib_backend.py:308`
và `arcface_backend.py:305`. Nhưng không có người gác, nên một lần đổi toán tử trong tương lai sẽ
lọt — và hậu quả là người có **đúng** số ảnh tối thiểu bị ghi `thieu_anh` thay vì được đăng ký, tức
mất người khỏi gallery một cách im lặng. Đúng loại lỗi mà CHẶN-B-1 của `P3-03` tồn tại để chặn.

Thêm một ca đặt `so_anh == min_images_per_user`, dùng backend giả trả vectơ hợp lệ → mã trả về `0`,
`trang_thai == da_dang_ky`.

### 4.7. Không đổi hành vi nào khác

Bảng tổng kết in ra stdout, nội dung manifest, nội dung meta, mã trả về, thứ tự xử lý người — giữ
nguyên. Mã việc này chỉ đổi **chỗ** tệp được ghi và **thời điểm** chúng xuất hiện ở vị trí cuối.

Đặc biệt: `--dry-run` vẫn không được tạo thư mục nào, kể cả thư mục tạm.

---

## 5. Bảng tiêu chí nghiệm thu

Ca mới, đặt tên `test_dongNN_<mô tả>` tiếp số từ 26.

| # | Ca | Kỳ vọng |
|---|---|---|
| 27 | Lượt chạy dừng giữa chừng (backend giả ném `ValueError` ở người thứ hai, người thứ nhất đủ ảnh) | `<ra>/<backend>/` **không tồn tại**; mã trả về `1` |
| 28 | Cùng tình huống 27 | **không** thư mục tạm nào sót lại trong `<ra>` |
| 29 | Lượt chạy thành công | `<ra>/<backend>/` có đủ `.npy` + `manifest.csv` + `gallery.meta.json`; không thư mục tạm |
| 30 | Lượt chạy hợp lệ nhưng **không ai** đủ ảnh | thư mục có `manifest.csv` và `gallery.meta.json`, không `.npy`, mã trả về `0` |
| 31 | Đã có gallery cũ, lượt mới **hỏng** giữa chừng | gallery cũ còn **nguyên vẹn** — so `sha256` từng tệp trước và sau |
| 32 | Đã có gallery cũ, lượt mới **thành công** với danh sách người khác | thư mục đích chỉ chứa người của lượt mới, không sót `.npy` của lượt cũ |
| 33 | Thư mục tạm còn sót từ lượt trước (tạo sẵn, có một tệp rác) | lượt mới chạy trót lọt, tệp rác biến mất, mã trả về `0` |
| 34 | `--dry-run` | không thư mục nào được tạo, kể cả thư mục tạm |
| 35 | Gọi **thẳng** `xu_ly_mot_nguoi`, đủ ảnh, backend giả ném `ValueError` | `pytest.raises(LoiMoHinh)` — đúng lớp, không phải `LoiCauHinh` |
| 36 | `so_anh` **bằng đúng** `min_images_per_user`, backend giả trả vectơ hợp lệ | mã trả về `0`, `trang_thai == da_dang_ky`, có tệp `.npy` |

Ngoài ra sửa **trong** ca `test_dong09b` hiện có: `if manifest.exists():` → `assert not
manifest.exists()` (§4.5 điều 2). Đây là sửa ca cũ, không phải thêm ca mới.

Ca 31 là ca quan trọng nhất của phần §12.1: nó canh chính lý lẽ chọn phương án ở §4.3.
Ca 35 và 36 là hai chốt mà review chứng minh đang thiếu bằng đột biến đo được trên máy.

Mọi ca dùng backend giả, chạy được trong container không có `models/`. Không ca nào cần
`@pytest.mark.slow`.

---

## 6. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

```bash
python -m black --check --line-length 100 src tests scripts
```

```bash
python -m ruff check src tests scripts
```

```bash
python -m pytest tests/test_enroll.py -v
```

Kết quả mong đợi: **29 passed** (19 ca cũ + 10 ca mới, số 27–36), 0 failed.

```bash
python -m pytest -q
```

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

```bash
git status --short --untracked-files=all
```

Đúng hai dòng của §2, không tệp lạ, **không tệp nào trong `data/`**.

### 6.1. Quét mẫu vi phạm

```bash
grep -rn "shutil.rmtree\|os.remove\|unlink" scripts/enroll.py
```

Mọi lời gọi xoá phải nằm trong nhánh dọn thư mục **tạm** hoặc bước xoá `.<backend>.cu` sau khi đổi
tên thành công. Không được có lời gọi nào xoá thẳng `<ra>/<backend>/`.

### 6.2. Phép đột biến

| # | Phép | Ca phải đỏ |
|---|---|---|
| ĐB1 | Ghi `.npy` thẳng vào `<ra>/<backend>/` như trước, giữ nguyên phần còn lại | 27 |
| ĐB2 | Bỏ bước xoá thư mục tạm ở nhánh `except` | 28 |
| ĐB3 | Đổi tên thư mục tạm **trước** khi ghi `gallery.meta.json` | 27 hoặc 29 |
| ĐB4 | Xoá `<ra>/<backend>/` ngay đầu lượt chạy thay vì sau khi ghi xong | 31 |
| ĐB5 | Đổi `raise LoiMoHinh(` thành `raise LoiCauHinh(` tại `enroll.py:208` | 35 |
| ĐB6 | Đổi `<` thành `<=` tại `enroll.py:204` | 36 |

ĐB4 quan trọng nhất của phần §12.1: nó dựng lại đúng chế độ hỏng mà §4.3 loại bỏ — mất gallery cũ
vì một lượt chạy mới hỏng giữa chừng.

ĐB5 và ĐB6 là hai phép mà review vòng 2 đã chạy và **không ca nào đỏ**. Chúng phải đỏ sau mã việc
này; nếu vẫn xanh thì ca 35 hoặc ca 36 chưa canh đúng chỗ — sửa ca test, đừng sửa mã sản phẩm.

---

## 7. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` line-length 100, `ruff` sạch.
- Không `except Exception` trần; ngoại lệ dùng lớp trong `src/common/exceptions.py`.
- Ca test dùng `tmp_path`, **không** ghi vào `data/`.
- Không commit, không dựng image, không `pip install`.
- Không chạy `scripts/enroll.py` ở chế độ ghi thật vào `data/` — đó là lượt của người dùng ở §9.

---

## 8. Ngoài phạm vi

- §12.4 biên bản `P3-03` (thông báo lỗi in hai lần) — dư thừa, không sai.
- Ca 26 so danh tính byte thay vì đếm lời gọi (§4.2 biên bản vòng 1).
- Chuyển import hai backend vào thân `tao_bo_nhan_dien` (§4.1 biên bản vòng 1).
- Bước 3.5 và việc bước đó bỏ qua thư mục con bắt đầu bằng dấu chấm — mã việc này chỉ **đặt ra**
  quy ước ở §4.4, không thi hành nó ở phía đọc.
- Mọi mục 🔵 khác treo từ `P3-02` và `P3-03` vòng 1.

---

## 9. Lượt của người dùng — sau khi §6 xanh

```bash
Remove-Item -Recurse -Force data/embeddings
```

```bash
python -m scripts.enroll --vao data/processed/lfw_original --backend dlib --toi-thieu 3
```

```bash
python -m scripts.enroll --vao data/processed/lfw_original --backend arcface --toi-thieu 3
```

```bash
Get-ChildItem -Recurse data/embeddings | Select-Object -ExpandProperty FullName
```

Lệnh cuối phải cho đúng hai thư mục `dlib` và `arcface`, mỗi thư mục 8 tệp `.npy` cộng
`manifest.csv` và `gallery.meta.json`. **Không thư mục nào có tên bắt đầu bằng dấu chấm.**
