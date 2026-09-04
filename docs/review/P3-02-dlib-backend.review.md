# Review P3-02-dlib-backend — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-02-dlib-backend.md` (commit `fc86902`) |
| **Nhánh** | `feat/p3-02-dlib-backend` — mã **chưa commit**, nằm ở cây làm việc |
| **Ảnh chụp mã được kiểm** | `src/recognizer/dlib_backend.py` · sha256 `D9606004CCE369A468F1FE8A8C884F6F30A1069D3510E31B65FEC41BDC85E866` |
| **Ngày** | 2026-09-04 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — một mục CHẶN-B. Sửa nằm **trọn trong `tests/test_dlib_backend.py`**; `src/recognizer/dlib_backend.py` **không cần đổi một dòng nào** |

Kiểm định độc lập: cả bốn phép đột biến được dựng lại từ đầu, không dùng lại kết quả người cài đặt
báo về. Mã chưa commit nên khôi phục bằng bản sao lưu ngoài repo, đối chiếu `sha256` sau mỗi phép —
cả bốn lần đều `KHOP` đúng chuỗi gốc, và lượt cuối xác nhận không còn dấu vết `DOT BIEN` nào.

---

## 1. Kết quả kiểm máy

### 1.1. Phạm vi tệp và dữ liệu cấm

| Kiểm | Kết quả |
|---|---|
| Danh sách trắng §2 — đúng bốn tệp | `M requirements.txt` · `M src/recognizer/__init__.py` · `?? src/recognizer/dlib_backend.py` · `?? tests/test_dlib_backend.py` ✅ |
| `git diff --stat` | `requirements.txt` **1 +** · `__init__.py` **4 +** — tổng 5 insertions, **0 deletions** ✅ |
| `requirements.txt` thêm đúng một dòng | `+dlib-bin==20.0.1`, không dòng xoá, không gói nào khác ✅ |
| `__init__.py` có xoá export cũ không | Bản `HEAD` **không export gì** (chỉ docstring). Thay đổi là thuần cộng thêm, **không có hồi quy** với `P3-01` ✅ |
| Dữ liệu cấm lọt git (R25) | rỗng ✅ |

### 1.2. Ba lệnh nền trên host

| Lệnh | Kết quả |
|---|---|
| `black --check --line-length 100 src tests` | `All done!`, 36 tệp không đổi ✅ |
| `ruff check src tests` | `All checks passed!` ✅ |
| `pytest -q` toàn kho | **1 failed, 500 passed** — 🔴 xem §2 |
| `pytest tests/test_dlib_backend.py -v` | **1 failed, 24 passed**, 0 skipped — 🔴 xem §2 |
| `python -c "import dlib"` | `20.0.1` — gói thật có mặt, nhóm đột biến có hiệu lực ✅ |

### 1.3. Container `faceid:arm64`

| Kiểm | Kết quả |
|---|---|
| Đúng một image, không dựng lại (R43) | `faceid:arm64` `caeca57e97d9` · **4 days ago** · 1.07GB — một dòng duy nhất ✅ |
| Image chưa có `dlib-bin` (§11b chưa chạy) | `ModuleNotFoundError: No module named 'dlib'` ✅ đúng kỳ vọng |
| `black` trong container | `All done!` ✅ |
| `ruff` trong container | **36 lỗi `EXE002`** — 🔵 xem §3.2, không thuộc mã việc này |
| `pytest tests/test_dlib_backend.py -m "not slow"` | **15 passed, 2 skipped, 8 deselected**. `test_dong02` và `test_dong03` **SKIPPED** đúng như thiết kế, không đỏ ✅ |
| `pytest -q -m "not slow"` toàn kho | **476 passed, 3 skipped, 22 deselected**, 0 failed ✅ |

Cơ chế skip đặt **đúng chỗ**: hai ca cần gói thật lùi về `SKIPPED` chứ không đổ, khâu thu thập không
sinh `ImportError` nào. Ràng buộc §9 "container không có `models/`, ca cần trọng số phải skip" đạt.

### 1.4. Quét mẫu vi phạm (§8 đặc tả + `code-review.instructions.md` §2)

| Mẫu | Kết quả |
|---|---|
| `^import dlib` / `^from dlib` ở mức module | rỗng ✅ |
| Số viết cứng `150` / `128` / `112` / `127.5` | rỗng ✅ — **không có `150`**, tức không tự phóng ảnh |
| `except Exception` | rỗng ✅ |
| `print(` trong `src/recognizer/` | rỗng ✅ |
| `logger.*(f"` | rỗng ✅ |
| Đường dẫn máy cá nhân · secret · `assert True` | rỗng ✅ |
| Nạp mô hình ngoài `__init__` | Đúng hai kết quả, cả hai ở dòng 210–211 trong `__init__` ✅ |

### 1.5. Bốn phép đột biến

| # | Phép | Ca đặc tả yêu cầu đỏ | Thực tế | Kết luận |
|---|---|---|---|---|
| ĐB1 | Bỏ đổi BGR sang RGB | dòng 16 | `1 failed, 24 passed` — **y hệt lượt chưa đột biến**, cùng ca, cùng con số `0.9955222010612488` | ❌ **không phân biệt được** |
| ĐB2 | Bỏ chuẩn hoá L2 | dòng 14 | `test_dong14` FAILED, `norm = 1.3635` ≠ 1 | ✅ có hiệu lực |
| ĐB3 | Bỏ đối chiếu `embedding_dim` | dòng 07 | `test_dong07` FAILED, `DID NOT RAISE LoiMoHinh`; dòng 08 vẫn xanh | ✅ có hiệu lực, không lan man |
| ĐB4 | Bỏ kiểm `min_images_per_user` | dòng 18 | `test_dong18` FAILED | ✅ có hiệu lực — 🔵 xem §3.1 về đường đỏ |

---

## 2. Mục lỗi

### 🔴 CHẶN-B-1 — Ca canh §6.1 đỏ sẵn và không phân biệt được ĐB1 (CB-6)

**Vị trí**: `tests/test_dlib_backend.py:302` (và ngưỡng dùng chung ở dòng 264)

```python
_NGUONG_TRUNG_KHOP = 0.99
...
    diem_trung = do_tuong_dong(vec_backend, vec_tham_chieu)
    assert diem_trung > _NGUONG_TRUNG_KHOP, (...)          # dòng 296 — mốc tuyệt đối

    vec_dao_kenh = backend_that.trich_dac_trung(anh_bgr[:, :, ::-1].copy())
    assert do_tuong_dong(vec_backend, vec_dao_kenh) < _NGUONG_TRUNG_KHOP   # dòng 302
```

**Vì sao**: hai hậu quả, cùng một gốc.

1. **Bộ kiểm thử đỏ ngay trên mã chưa đột biến.** `pytest tests/test_dlib_backend.py -v` cho
   `1 failed, 24 passed`: `assert 0.9955222010612488 < 0.99`. Lệnh này nằm trong §8 đặc tả, nên
   trạng thái bàn giao **chưa đạt §8**. (Ca 16 mang `@pytest.mark.slow` và chỉ chạy khi có đủ trọng
   số dlib lẫn ảnh `data/processed/lfw_original/` — nhiều khả năng lượt tự kiểm đã bỏ qua nó.)

2. **Nghiêm trọng hơn: ĐB1 không làm đổi bất cứ điều gì.** Lượt đột biến cho **đúng cùng một dòng
   đỏ, đúng cùng con số** `0.9955222010612488` như lượt gốc. Ca dòng 16 vì thế mang **zero thông tin**
   về §6.1 — chính chỗ đặc tả gọi là "quan trọng nhất", chính chế độ lỗi im lặng mà `P3-01` đã vấp
   với chuẩn hoá đầu vào ArcFace. Nếu ai đó gỡ `cvtColor` ở lần sửa sau, không phép kiểm nào kêu.

   Nguyên nhân là một **giả định thực nghiệm sai**: vectơ 128-D của dlib **gần như bất biến** với
   phép hoán đổi kênh R↔B trên ảnh khuôn mặt — độ tương đồng đo được là **0,9955**. Ngưỡng `0.99`
   được dùng cho **cả hai** khẳng định với hai chiều ngược nhau, nên nó phải vừa đủ lỏng để chấp
   nhận "cùng một ảnh" vừa đủ chặt để bác "đã đảo kênh". Với con số thật 0,9955 thì không ngưỡng đơn
   nào làm được cả hai việc. Bằng chứng: khẳng định dòng 296 **đi qua trong cả hai lượt** — gốc lẫn
   ĐB1 — nên mốc tuyệt đối cũng không cứu được.

   Đối chiếu mảng xác nhận cơ chế: ở lượt gốc `vec_backend` bắt đầu bằng `-4.2458e-02`, ở lượt ĐB1
   bắt đầu bằng `-0.03066187` — đúng bằng `vec_dao_kenh` của lượt gốc. Hai đầu vào chỉ **hoán vai**,
   đúng như docstring của chính ca này đã cảnh báo về phép so đối xứng.

**Sửa** — chỉ động vào tệp test:

1. **Xoá hẳn khẳng định dòng 302.** Phép so đối xứng này không bao giờ phân biệt được, giữ lại chỉ
   tạo cảm giác an toàn giả.
2. **Siết khẳng định dòng 296 thành so khớp gần-đúng-tuyệt-đối.** Khi mã đúng, `vec_backend` và mốc
   tham chiếu được tính trên **đúng cùng một mảng pixel RGB**, nên phải trùng tới sai số dấu phẩy
   động; khi bỏ `cvtColor` thì tụt xuống 0,9955 và bị bắt ngay. Nhớ chuẩn hoá mốc trước, vì backend
   có chuẩn hoá L2 còn `compute_face_descriptor` thì không:

```python
    vec_tham_chieu = vec_tham_chieu / float(np.linalg.norm(vec_tham_chieu))
    vec_backend = backend_that.trich_dac_trung(anh_bgr)
    assert np.allclose(vec_backend, vec_tham_chieu, atol=1e-5), (
        "backend không khớp mốc RGB tham chiếu; dấu hiệu thiếu bước đổi BGR sang RGB"
    )
```

3. Chạy lại ĐB1 và **chứng minh** ca 16 đỏ khi đột biến, xanh khi khôi phục. Đây là điều kiện
   nghiệm thu của vòng 2 — không nhận lại "đã sửa" mà không kèm cặp kết quả đó.

`num_jitters` bằng `0` ở cả `configs/recognize.yaml:56` lẫn cấu hình test, nên đường chạy tất định
và `np.allclose` là hợp lệ. Nếu về sau bật jitter, ca này phải ép `num_jitters = 0` tại chỗ.

---

## 3. Ghi nhận không chặn

### 3.1. 🔵 ĐB4 đỏ qua `AttributeError`, không qua `ValueError`

`tests/test_dlib_backend.py:318` dùng `_backend_gia()` — thể hiện dựng vòng qua `__init__` nên không
có `_dlib`. Bỏ guard `min_images_per_user` thì luồng chạy tiếp vào `_chay_mo_hinh` và đổ ở
`AttributeError: 'DlibFaceRecognizer' object has no attribute '_dlib'`, thay vì `pytest.raises` bắt
được một `ValueError` khác. Phép đột biến **vẫn phân biệt được** nên không chặn, nhưng tín hiệu là
gián tiếp: nó chứng minh "guard biến mất", không chứng minh "guard nằm đúng chỗ".

### 3.2. 🔵 `ruff` trong container báo 36 lỗi `EXE002` — không thuộc mã việc này

`The file is executable but no shebang is present` nổ trên **cả 36 tệp** `src/**` và `tests/**`, kể
cả những tệp đã gộp từ `P1`/`P2`. Trên host `ruff` sạch. Nguyên nhân là bind-mount từ Windows khiến
mọi tệp hiện ra với quyền thực thi bên trong container. Hệ quả cần biết: **cổng "ruff trong
container" hiện không thể xanh trên máy này** với bất kỳ mã việc nào. Xử lý bằng một mã việc dọn dẹp
riêng (bỏ qua `EXE002` trong cấu hình `ruff`, hoặc chỉnh cách gắn thư mục) — không phải việc của
`P3-02`.

### 3.3. 🔵 Marker `slow` chưa đăng ký

`PytestUnknownMarkWarning: Unknown pytest.mark.slow` xuất hiện ở `test_dlib_backend.py` và năm tệp
test cũ. `pyproject.toml` không có mục `markers`. Việc lọc `-m "not slow"` vẫn hoạt động, nên đây
chỉ là nhiễu log — nhưng nó **che mất** một chuyện: ca `slow` bị deselect im lặng, và đó có lẽ là lý
do CHẶN-B-1 lọt qua lượt tự kiểm. Đăng ký marker trong `pyproject.toml` nên đi cùng mã việc dọn dẹp
ở §3.2.

### 3.4. 🔵 `dlib.rectangle(0, 0, rong, cao)` lệch một pixel

`src/recognizer/dlib_backend.py:258` — `rectangle` nhận `(left, top, right, bottom)` **bao gồm cả
biên**, nên `(0, 0, 112, 112)` mô tả vùng 113×113 trên ảnh 112×112. Nhất quán giữa mã và ca test nên
không ca nào đỏ. Sửa gần như miễn phí (`rong - 1, cao - 1`), lợi ích là khung dò khớp đúng ảnh khi
đo ở Cổng C. **Ghi chú**: nếu sửa chỗ này thì mốc tham chiếu ở ca 16 phải sửa theo cho khớp.

### 3.5. 🔵 Bất đối xứng giữa hai backend — việc của `spec-writer`, không phải người cài đặt

| | Phương án A (`P3-02`) | Phương án B (`P3-01`) |
|---|---|---|
| Tên lớp | `DlibFaceRecognizer` | `ArcFaceBackend` |
| `__init__` nhận | **toàn bộ** `recognize.yaml`, đọc khoá `dlib.model_path` | **riêng nhánh** `arcface`, đọc khoá `model_path` |
| Xuất ở mức gói | có, trong `__all__` | không |
| Kiểm kích thước ảnh ở `trich_dac_trung` | không (dlib tự căn chỉnh) | có |

Mã làm **đúng** đặc tả ở cả bốn dòng — tên lớp do §5 đặc tả chốt, hình dạng `cfg` do §5 chốt. Nhưng
ở Cổng C, script đo hai phương án sẽ phải dựng cấu hình theo hai kiểu và import theo hai kiểu, đúng
thứ mà dòng 24 (chữ ký ba phương thức) được đặt ra để tránh. Nên chuẩn hoá bằng một mã việc riêng
**trước** khi viết đặc tả script đo, không trả lại `P3-02`.

---

## 4. Đối chiếu đặc tả

| Mục | Kết quả |
|---|---|
| §6.1 tiền xử lý — BGR→RGB, dò 68 điểm mốc, truyền cả ảnh lẫn kết quả dò | ✅ mã đi đúng đường (`dlib_backend.py:257-261`, `:284`). Không `resize`, không hằng `150`. **Nhưng chưa có phép kiểm nào canh giữ** — CHẶN-B-1 |
| §6.4 `dlib` chỉ import trong thân hàm | ✅ `dlib_backend.py:201`, duy nhất một chỗ |
| §6.5 hai mô hình nạp một lần trong `__init__` | ✅ `dlib_backend.py:210-211`; không lệnh nạp nào trong `trich_dac_trung`/`enroll`/`identify` |
| §4 `so_chieu` đọc từ mô hình, `embedding_dim` chỉ kiểm chéo | ✅ `_do_so_chieu_that()` đo thật rồi so; lệch → `LoiMoHinh`. ĐB3 xác nhận guard sống |
| Dòng 24 ba phương thức cùng chữ ký `ArcFaceRecognizer` | ✅ `test_dong24` PASSED, so cả `Signature` đầy đủ |
| Dòng 25 hai backend cùng nhận ra một người | ✅ PASSED |
| §9 ngoại lệ đúng loại, không `print`, không `torch`/`onnxruntime` | ✅ |
| §9 ca cần trọng số phải skip trong container | ✅ dòng 02, 03 `SKIPPED` |
| §10 ngoài phạm vi (`scripts/enroll.py`) | ✅ không đụng |
| **R5 trung thực số liệu** | ✅ không hằng số nào trông như kết quả đo; `configs/recognize.yaml:64` vẫn `threshold: TBD` |
| Fail-safe phần cứng | không áp dụng — mã việc không chạm GPIO/camera |
| §8 lệnh tự kiểm | 🔴 `pytest tests/test_dlib_backend.py -v` đỏ; ĐB1 không đạt yêu cầu "dòng 16 phải đỏ" |

---

## 5. Phán quyết

🔴 **TRẢ LẠI** — vòng 1. Một mục CHẶN-B.

`src/recognizer/dlib_backend.py` được đánh giá là **đúng**: bốn ràng buộc trọng yếu đều đạt, ba trên
bốn phép đột biến chứng minh guard sống, và chế độ hỏng im lặng mà đặc tả cảnh báo không xuất hiện.
Sửa nằm trọn trong `tests/test_dlib_backend.py`.

**Điều kiện nghiệm thu vòng 2** — thiếu một là chưa nhận:

1. `pytest tests/test_dlib_backend.py -v` cho **25 passed, 0 failed, 0 skipped** trên host.
2. Chạy ĐB1 và dán về **cặp** kết quả: đỏ khi đột biến (nêu rõ ca 16 và thông báo), xanh sau khôi phục.
3. `sha256` sau khôi phục trùng chuỗi trước khi đột biến.
4. `black` và `ruff` trên host vẫn sạch; container `-m "not slow"` vẫn 15 passed / 2 skipped.

Bốn mục 🔵 ở §3 **không** thuộc vòng sửa này: §3.2 và §3.3 là việc dọn dẹp toàn kho, §3.5 là việc
của `spec-writer` trước Cổng C, §3.1 và §3.4 để người dùng quyết định.

---
---

# Review P3-02-dlib-backend — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-02-dlib-backend.md` (commit `fc86902`) |
| **Nhánh** | `feat/p3-02-dlib-backend` — mã **chưa commit**, nằm ở cây làm việc |
| **Ảnh chụp mã được kiểm** | `src/recognizer/dlib_backend.py` · sha256 `D9606004CCE369A468F1FE8A8C884F6F30A1069D3510E31B65FEC41BDC85E866` — **trùng chuỗi vòng 1** (KĐ-1) |
| **Ngày** | 2026-09-04 |
| **Phán quyết** | ✅ **ĐẠT** — CHẶN-B-1 đã gỡ, không phát sinh mục 🔴 hay 🟡 mới |

Phạm vi vòng 2 đúng như §5 vòng 1 đã chốt: sửa nằm **trọn trong `tests/test_dlib_backend.py`**.
Mã sản phẩm không đổi một byte — KĐ-1 cho sha256 trùng đúng chuỗi ghi ở đầu vòng 1, nên mọi kết luận
vòng 1 về `src/recognizer/dlib_backend.py` vẫn còn hiệu lực và không phải kiểm lại.

Toàn bộ mười một khối lệnh do người dùng chạy. Bốn phép kiểm bằng đọc mã ở §7 do bên kiểm định thực
hiện trên tệp thật, không dùng lại lời báo của người cài đặt.

---

## 6. Kết quả kiểm máy — vòng 2

**Môi trường host** `pc_x86`: Windows 11, Python 3.12.5, pytest 9.1.1, pluggy 1.6.0.
**Container** `faceid:arm64`: cảnh báo `linux/arm64` chạy trên host `linux/amd64/v4` — tức qua QEMU,
đúng mã môi trường `docker_arm64`, số thời gian **không** dùng để kết luận chỉ tiêu.

| KĐ | Lệnh | Kết quả |
|---|---|---|
| KĐ-1 | `Get-FileHash -Algorithm SHA256 src\recognizer\dlib_backend.py` | `D9606004CCE369A468F1FE8A8C884F6F30A1069D3510E31B65FEC41BDC85E866` — **khớp** chuỗi vòng 1 ✅ |
| KĐ-2 | `git status --short --untracked-files=all` | Đúng 5 dòng: `M requirements.txt` · `M src/recognizer/__init__.py` · `?? docs/review/P3-02-dlib-backend.review.md` · `?? src/recognizer/dlib_backend.py` · `?? tests/test_dlib_backend.py` — trong danh sách trắng §2 đặc tả (dòng thứ ba là chính biên bản này), **không tệp lạ** ✅ |
| KĐ-3 | `python -m pytest tests/test_dlib_backend.py -v` | **25 passed**, 0 failed, 0 skipped, 8 warnings, 14.08s ✅ |
| KĐ-4 | `python -m black --check --line-length 100 src tests` | `All done!` — **36 files would be left unchanged**, 0 reformatted ✅ |
| KĐ-5 | `python -m ruff check src tests` | `All checks passed!` ✅ |
| KĐ-6 | `python -m pytest -q` (toàn kho) | **501 passed**, 0 failed, 35 warnings, 67.37s — vòng 1 là 1 failed / 500 passed trên **cùng 501 ca**, tức không ca nào bị xoá để lấy màu xanh ✅ |
| KĐ-7 | `docker run --rm -v "${PWD}:/app" -w /app faceid:arm64 pytest tests/test_dlib_backend.py -m "not slow" -q` | **15 passed, 2 skipped, 8 deselected**, 0 failed/error, 3.47s. Dấu tiến trình `.ss..............` xác định hai ca skip là `test_dong02` và `test_dong03` — lùi về SKIP chứ không đỏ, đúng kỳ vọng vì image chưa có `dlib-bin` (§11b là lượt sau khi ĐẠT) ✅ |
| KĐ-8 | Sao lưu ra `%TEMP%` rồi băm bản sao | `C:\Users\THANHL~1\AppData\Local\Temp\P3-02_dlib_backend_goc.py` · Hash `D9606004…866` — bản sao đặt **ngoài** cây repo ✅ |
| KĐ-9 | ĐB1: dòng 284 `anh_rgb = cv2.cvtColor(anh, cv2.COLOR_BGR2RGB)` → `anh_rgb = anh  # DOT BIEN DB1`, ghi UTF-8 không BOM | `Select-String` khớp **đúng một dòng** tại `src\recognizer\dlib_backend.py:284`; sha256 đổi thành `CAA648E54FD9CC16BD335D63586C7D70BCEDA4FA592ACC6A46CF0A9FEACDBEAF` ✅ đột biến đã vào đúng chỗ |
| KĐ-10 | `python -m pytest tests/test_dlib_backend.py -v` **dưới đột biến** | **1 failed, 24 passed**, 12.29s. Ca đỏ đúng là `test_dong16_doi_kenh_mau_lam_doi_ket_qua`, thông báo `AssertionError: backend không khớp mốc RGB tham chiếu; dấu hiệu thiếu bước đổi BGR sang RGB` tại `tests\test_dlib_backend.py:298`. **Không ca nào khác đỏ** ✅ |
| KĐ-11 | Khôi phục từ bản sao rồi đối chiếu | sha256 về `D9606004…866` — **trùng lại chuỗi gốc**; `Select-String "DOT BIEN"` **không dòng nào** khớp; `pytest tests/test_dlib_backend.py -v` cho **25 passed**, trùng KĐ-3 ✅ |

### 6.1. Biên độ của tín hiệu đỏ ở KĐ-10

Hai vectơ lệch ngay ở **chữ số thập phân thứ hai**: phần tử đầu của vectơ backend là `-0.03066187`,
của mốc tham chiếu là `-0.04245894`. Khoảng cách này vượt `atol=1e-5` khoảng ba bậc độ lớn, nên
đường đỏ đến từ **khác biệt về ngữ nghĩa** (ảnh còn ở hệ BGR), không phải từ sai số dấu phẩy động.
Đây là điểm mà ngưỡng `0.99` của vòng 1 không có: khi đó cả lượt gốc lẫn lượt đột biến đều cho đúng
một con số `0.9955222010612488`.

Ngoài ra, đột biến **không lan** ra ngoài phạm vi ca 16: 24 ca còn lại vẫn xanh dưới đột biến, tức
ca 16 là phép kiểm **duy nhất** canh bước `cvtColor`, và nó thật sự canh được.

### 6.2. Bài học quy trình — lỗi của bên ra lệnh kiểm, không tính vào phán quyết

Khối KĐ-7 lần chạy đầu thất bại vì **lỗi cú pháp shell**: lệnh viết theo cú pháp Bash
(`MSYS_NO_PATHCONV=1 … "$(pwd)"`) được dán vào PowerShell, sinh `CommandNotFoundException`, rồi
`docker: invalid reference format` do đường dẫn dự án có khoảng trắng không được bọc nguyên. Chạy
lại bằng bản PowerShell `-v "${PWD}:/app"` thì đạt.

Đây là **lỗi của bên ra lệnh kiểm**, không phải lỗi mã nguồn: danh sách lệnh phải được viết đúng
shell mà người dùng đang dùng (PowerShell trên máy này), và đường dẫn dự án có khoảng trắng nên mọi
tham số `-v` phải bọc nguyên chuỗi. Ghi lại để lượt kiểm sau không lặp.

---

## 7. Kiểm bằng đọc mã — bốn cách hỏng đã biết

Vòng 1 hỏng vì phép kiểm **trông như** canh giữ mà thật ra không. Bốn phép đọc dưới đây nhắm đúng
bốn cách mà bản sửa có thể lặp lại cùng chế độ hỏng đó. **Cả bốn đều đạt.**

| # | Cách hỏng cần loại | Kết luận |
|---|---|---|
| A.1 | Mốc tham chiếu lại đi qua chính hàm cần kiểm ⟹ đột biến làm đổi **cả hai** vế | ✅ đã loại |
| A.2 | Mốc và backend chạy với `num_jitters` khác nhau ⟹ đường chạy không tất định | ✅ đã loại |
| A.3 | Khung dò của mốc lệch tham số so với mã sản phẩm ⟹ đỏ giả | ✅ đã loại |
| A.4 | Khẳng định đối xứng cũ vẫn còn, chỉ được nới ngưỡng | ✅ đã xoá hẳn |

**A.1 — Mốc tham chiếu dựng độc lập.** `test_dong16_doi_kenh_mau_lam_doi_ket_qua`
(`tests/test_dlib_backend.py:262`) dựng mốc ở dòng 280–293 bằng cách gọi **thẳng** vào thư viện:
`dlib.load_rgb_image` (dòng 286), `dlib.shape_predictor` (287), `dlib.face_recognition_model_v1`
(288), `compute_face_descriptor` (291–293). `trich_dac_trung` xuất hiện **đúng một lần** trong cả
thân ca, ở vế cần kiểm (dòng 297). Đột biến ở `dlib_backend.py:284` vì vậy chỉ tác động lên vế
backend, mốc đứng yên — chế độ hỏng vòng 1 (đột biến làm đổi cả hai vế, chỉ hoán vai trò hai đầu
vào) **không tái diễn**. KĐ-10 xác nhận điều này bằng số: chỉ một vế dịch chuyển.

**A.2 — Ép `num_jitters = 0` tại chỗ.** Dòng 292 truyền hằng `0` viết thẳng cho mốc. Vế backend lấy
`"num_jitters": 0` từ `_cfg_hop_le()` (dòng 51–61, khoá ở dòng 58), **không** đọc
`configs/recognize.yaml`. Hai vế do đó khoá cùng một giá trị ngay trong tệp test: người nào bật
jitter ở `configs/recognize.yaml:56` về sau cũng không chạm được ca này. Đúng cảnh báo cuối
CHẶN-B-1 vòng 1.

**A.3 — Khung dò khớp mã sản phẩm từng tham số.** Mốc dựng khung ở dòng 289–290
(`cao, rong = anh_rgb.shape[:2]` rồi `dlib.rectangle(0, 0, rong, cao)`), khớp từng tham số với mã
sản phẩm ở `src/recognizer/dlib_backend.py:257-258`. Không còn nguồn false positive nào đến từ lệch
tham số khung dò. (Ghi chú §3.4 vòng 1 vẫn treo: nếu sau này sửa `rong - 1, cao - 1` thì phải sửa cả
hai chỗ cùng lúc.)

**A.4 — Khẳng định đối xứng cũ đã xoá hẳn, không phải nới ngưỡng.** Hằng `_NGUONG_TRUNG_KHOP = 0.99`
và vế `backend_that.trich_dac_trung(anh_bgr[:, :, ::-1].copy())` **không còn tồn tại** dưới bất kỳ
dạng nào trong tệp. Ngưỡng duy nhất còn lại là `_NGUONG_CUNG_NGUOI = 0.4` (dòng 391), thuộc
`test_dong25`, không liên quan tới ca 16. Thân ca 16 chỉ còn **một** khẳng định, ở dòng 298–300.
Phân biệt này quan trọng: nới ngưỡng sẽ để lại một phép kiểm vô hiệu nhưng trông có vẻ chặt, còn xoá
hẳn thì không để lại cảm giác an toàn giả nào.

**Ghi nhận cấu trúc tệp**: 25 hàm `test_dong01`…`test_dong25`, trong đó 8 ca mang `slow` và 17 ca
không — cộng lại đúng con số 25 passed của KĐ-3 và 15 passed + 2 skipped + 8 deselected của KĐ-7.
`import dlib` nằm trong **thân hàm** (dòng 280), không ở mức module, nên ràng buộc thu thập §7 đặc
tả ("`pytest --collect-only -m "not slow"` chạy trót lọt kể cả khi chưa cài `dlib`") giữ nguyên.

### 7.1. Một điểm phương pháp — rủi ro đã nêu và đã bị loại bằng số liệu

Mốc tham chiếu **không** dùng `cv2.cvtColor` mà đọc lại tệp bằng `dlib.load_rgb_image`. Đây là lựa
chọn đúng về mặt độc lập (A.1), nhưng nó kéo theo một rủi ro: hai vế đi qua **hai bộ giải mã PNG
khác nhau** (OpenCV và dlib). Nếu hai bộ giải mã lệch nhau dù chỉ một mức xám ở một pixel, vectơ đầu
ra sẽ lệch và `np.allclose(atol=1e-5)` sẽ cho **đỏ giả** trên mã đúng.

Rủi ro này **đã bị loại bằng số liệu**, không bằng lập luận: KĐ-3 và KĐ-11 đều cho 25 passed với
đúng `atol=1e-5`, chứng minh hai bộ giải mã trả về **cùng một mảng pixel** trên tập ảnh đang dùng.
Ghi lại đây như một điểm phương pháp cần biết — không phải lỗi — vì nếu về sau đổi định dạng ảnh
đầu vào (chẳng hạn sang JPEG có nén mất mát) thì giả định này phải được đo lại.

---

## 8. Đối chiếu năm điều kiện nghiệm thu §5 vòng 1

| # | Điều kiện | Kết luận | Bằng chứng |
|---|---|---|---|
| 1 | `pytest tests/test_dlib_backend.py -v` cho 25 passed / 0 failed / 0 skipped trên host | ✅ Đạt | KĐ-3 (25 passed, 14.08s) · KĐ-11 (25 passed sau khôi phục) |
| 2 | ĐB1 do **bên kiểm định** dựng lại: đỏ ở ca 16 khi đột biến, xanh sau khôi phục | ✅ Đạt | KĐ-9 (đột biến vào đúng dòng 284) · KĐ-10 (1 failed, đúng `test_dong16`) · KĐ-11 (25 passed) |
| 3 | `sha256` sau khôi phục trùng chuỗi trước khi đột biến | ✅ Đạt | KĐ-1 = KĐ-8 = KĐ-11 → `D9606004…866`; KĐ-9 xác nhận chuỗi đã thật sự đổi ở giữa |
| 4 | `black` và `ruff` trên host vẫn sạch | ✅ Đạt | KĐ-4 (36 files unchanged) · KĐ-5 (`All checks passed!`) |
| 5 | Container `faceid:arm64` `-m "not slow"` vẫn 15 passed / 2 skipped, hai ca đó SKIP không đỏ | ✅ Đạt | KĐ-7 (15 passed, 2 skipped, 8 deselected; `test_dong02`, `test_dong03` SKIP) |
| + | Không hồi quy trên toàn kho | ✅ Đạt | KĐ-6 (501 passed, so với 1 failed / 500 passed vòng 1 trên cùng 501 ca) |

Không điều kiện nào thiếu bằng chứng máy. Không con số nào trong bảng trên đến từ lời báo của người
cài đặt.

---

## 9. Phán quyết vòng 2

✅ **ĐẠT.**

CHẶN-B-1 đã được gỡ. Cặp KĐ-10 (đỏ dưới đột biến, đúng ca 16, biên độ lệch ở chữ số thập phân thứ
hai) và KĐ-11 (xanh sau khôi phục, sha256 trùng gốc) chứng minh ca `test_dong16` thật sự canh giữ
bước `cv2.cvtColor` ở `src/recognizer/dlib_backend.py:284` — đúng điều §6.1 đặc tả gọi là quan trọng
nhất. Bốn phép đọc mã ở §7 loại trừ bốn cách hỏng đã biết, nên kết luận không dựa vào một lượt chạy
may mắn.

Mã sản phẩm **không đổi một byte** trong suốt vòng 2 (KĐ-1). Sửa nằm trọn trong
`tests/test_dlib_backend.py`, đúng phạm vi §5 vòng 1 đã chốt. Không phát sinh mục 🔴 hay 🟡 mới.

**Việc tiếp theo** — mã việc đã đủ điều kiện để người dùng đưa qua N5:

1. Commit và gộp nhánh `feat/p3-02-dlib-backend`.
2. Chạy §11b của đặc tả: dựng lại image `faceid:arm64` (bắt buộc vì `requirements.txt` đã thêm
   `dlib-bin==20.0.1`, R43), rồi xác nhận wheel `aarch64` cài được và chạy lại bộ kiểm thử trong
   container.
3. Chạy `python -m pytest -m slow -v` để đóng nốt hai ca trọng yếu dòng 16 và dòng 25.

⚠️ **Chỉ người dùng** được `git commit` / `git push` và `docker build`. Biên bản này không đề xuất
lệnh nào để chạy hộ.

---

## 10. Mục còn treo — không thuộc phạm vi vòng 2, không kiểm lại

Năm mục 🔵 ở §3 vòng 1 vẫn nguyên trạng:

- **§3.1** — ĐB4 đỏ qua `AttributeError` chứ không qua `ValueError`; tín hiệu gián tiếp, không chặn.
- **§3.2** — `ruff` trong container báo 36 lỗi `EXE002` do bind-mount từ Windows; việc dọn dẹp toàn kho.
- **§3.3** — marker `slow` chưa đăng ký trong `pyproject.toml`; nay đã có số liệu, xem §10.1.
- **§3.4** — `dlib.rectangle(0, 0, rong, cao)` lệch một pixel; sửa thì phải sửa kèm mốc ở ca 16 (§7 A.3).
- **§3.5** — bất đối xứng giữa hai backend; việc của `spec-writer` **trước** khi viết đặc tả script đo ở Cổng C.

### 10.1. Số liệu bổ sung cho §3.3

Vòng 2 cho phép định lượng mục này. Marker `slow` **chưa đăng ký** trong `pyproject.toml`, hệ quả đo
được:

| Phạm vi | Số cảnh báo `PytestUnknownMarkWarning` | Nguồn |
|---|---|---|
| Riêng `tests/test_dlib_backend.py` | 8 | KĐ-3 |
| Toàn kho, trên 6 tệp test | 22 | KĐ-6 |
| Trong container `faceid:arm64` | 8 | KĐ-7 |

Sáu tệp phát sinh cảnh báo: `test_detector_factory.py`, `test_dlib_backend.py`,
`test_export_detector.py`, `test_export_detector_ncnn.py`, `test_ncnn_backend.py`,
`test_yolo_face.py`.

Cơ chế lọc **vẫn hoạt động đúng** — KĐ-7 cho 8 deselected, khớp đúng 8 ca mang `slow` đếm được trong
tệp — nên mục này **không chặn**. Ghi con số vào đây để mã việc dọn dẹp sau xử lý dứt điểm bằng một
dòng `markers` trong `pyproject.toml`.
