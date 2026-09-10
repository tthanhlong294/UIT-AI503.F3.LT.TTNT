# Review P2-08 — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-08-camera-fourcc-fps.md` |
| **Nhánh** | `feat/p2-08-camera-fourcc-fps` |
| **Ngày** | 2026-09-10 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — không còn 🔴/🟡, chỉ còn 🔵 góp ý; được commit và gộp `dev` |

Phạm vi mã việc: `CameraOpenCV.mo()` đặt `CAP_PROP_FOURCC` sang MJPG, áp `CAP_PROP_FPS`, phơi thông
số webcam thực tế qua property `thong_so_thuc_te`.

---

## 1. Kết quả kiểm máy

**Người dùng chạy ngày 2026-09-10.** Lệnh chép nguyên văn; mọi con số dưới đây đến từ lượt chạy của
người dùng, không từ bảng `coder` dán về (R42, `code-review.instructions` §1).

### 1.1. Phạm vi thay đổi

| # | Lệnh | Kết quả |
|---|---|---|
| [1/28] | `git status --short --untracked-files=all` | ` M src/capture/opencv_camera.py`, ` M tests/test_capture.py`, cộng 2 tệp `.docx` untracked trong `docs/bao-cao-tuan/` có từ trước ✅ |
| [2/28] | `git diff --stat dev` | `src/capture/opencv_camera.py │ 158 +`, `tests/test_capture.py │ 679 +`, tổng `834 insertions(+), 3 deletions(-)` ✅ |
| [3/28] | `git diff --name-only dev` | đúng hai tệp trong danh sách trắng §2 ✅ |
| [4/28] | `git diff --name-only dev -- src/capture/` | **đúng một dòng** `src/capture/opencv_camera.py` — chốt **B3** đạt ✅ |
| [5/28] | `git diff dev -- tests/test_capture.py \| Select-String '^-[^-]'` | **rỗng hoàn toàn**, 0 dòng xoá — chốt **B1** đạt ✅ |
| [6/28] | `git diff dev -- configs/capture.yaml` | **rỗng** — `coder` không chạm tệp của `spec-writer` ✅ |
| [7/28] | `git diff --name-only dev -- docs results report scripts notebooks .claude CLAUDE.md requirements.txt tests/test_benchmark_detect.py` | **rỗng** ✅ |
| [8/28] | `git log --oneline dev..HEAD` | **rỗng** — không commit nào, đúng §13 ✅ |
| [9/28] | `Get-ChildItem src\capture\*.py` | đúng 5 tệp `base.py`, `factory.py`, `mock_camera.py`, `opencv_camera.py`, `__init__.py` — không tệp mới (§11) ✅ |
| [10/28] | lọc `\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$` trên `git status` | rỗng ✅ |

Không có tệp nào ngoài danh sách trắng bị chạm. Hai tệp `.docx` untracked có từ trước mã việc này,
đúng như §9.2 đã dự liệu.

### 1.2. Mốc THẬT trước khi sửa (đo bằng `git stash`)

| Môi trường | Kết quả nguyên văn |
|---|---|
| host `pc_x86`, `pytest -q`, không lọc marker | `789 passed, 15 warnings in 172.95s` |
| container `faceid:arm64`, `-m "not slow"` | `756 passed, 1 skipped, 32 deselected, 1 warning in 656.81s` |

⭐ Con số `756` mà `coder` báo về là **suy diễn** (`837 − 81`, do Docker Desktop chưa chạy lúc nó lấy
mốc). Lượt này đo thật và trùng khớp — nhưng phép trùng khớp đó chỉ biết được **sau khi** đo, nên việc
dựng lại mốc là bắt buộc chứ không thừa. `git stash pop` thành công, `git diff --stat dev` sau đó vẫn
`+834/−3`.

### 1.3. Ba lệnh nền, container, phép đếm

| # | Lệnh | Kết quả |
|---|---|---|
| [11/28] | `python -m black --check --line-length 100 src tests` | `All done! 41 files would be left unchanged.` ✅ |
| [12/28] | `python -m ruff check src tests` | `All checks passed!` ✅ |
| [13/28] | `python -m pytest -q` (host) | `870 passed, 15 warnings in 138.64s` — **+81** so với mốc, 0 failed, 0 skipped ✅ |
| [14/28] | `python -m pytest tests/test_capture.py -q` | `107 passed in 0.52s`, 0 skipped ✅ |
| [15/28] | container `faceid:arm64`, `python3 -m pytest -q -m "not slow"` | `837 passed, 1 skipped, 32 deselected, 1 warning in 627.81s` — **+81**, **0 failed** ✅ |
| [16/28] | container, `--collect-only -q tests/test_capture.py` | `107 tests collected in 3.07s`, không lỗi import ✅ |
| [17/28] | đếm `::test_[0-9]` | **26** — chốt **B1** đạt ✅ |
| [18/28] | đếm `::test_fourcc_dong` | **81** — đủ mỗi dòng §8 một ca ✅ |

Host và container tăng **đúng cùng một lượng 81**: không ca mới nào phụ thuộc thứ container không có
(§3.5). `26 + 81 = 107` khớp lệnh [14/28].

Dùng đúng image `faceid:arm64`, không dựng image mới (R43).

### 1.4. Bảy lệnh quét mẫu §9.4 + quét bổ sung theo `code-review.instructions` §2

| # | Lệnh | Kết quả |
|---|---|---|
| [19/28] | `grep -nE "1280\|720\|30" src/capture/opencv_camera.py` | **rỗng** — bẫy lớn nhất §3.4 vượt qua ✅ |
| [20/28] | `grep -n "except Exception" src/capture/opencv_camera.py` | **đúng một dòng** `:222`, chính là dòng có sẵn trong `dong()` từ `P1-01` ✅ |
| [21/28] | `grep -nE "raise (ValueError\|TypeError\|Exception)\(" …` | rỗng ✅ |
| [22/28] | `grep -n "get(cv2.CAP_PROP_FRAME" …` | **rỗng** — chốt **C1** §4.3 đạt ✅ |
| [23/28] | `grep -nE "print\(\|VideoWriter" …` | rỗng — R23 và §4.2 đạt ✅ |
| [24/28] | `grep -nE "cv2\.VideoCapture" tests/test_capture.py` (đã lọc `monkeypatch\|patch\|VideoCaptureGia`) | rỗng — không ca nào mở camera thật ✅ |
| [25/28] | `grep -n "pytest.mark.slow" tests/test_capture.py` | rỗng ✅ |
| [26/28] | `grep -nE "logger\.\w+\(f\"" src/capture/*.py` | rỗng — lazy formatting, không dính CS-5 ✅ |
| [27/28] | `grep -n "logger.warning(" src/capture/opencv_camera.py` | **đúng 5 dòng**: `:133` warmup · `:161` không lấy được khung thử · `:188` Camera từ chối · `:207` retry đọc · `:223` lỗi release ✅ |
| [28/28] | `assert True`, đường dẫn tuyệt đối máy cá nhân, secret | rỗng ✅ |

Phép đếm `levelno == logging.WARNING` trong tests cho **5 dòng**: `:668`, `:725`, `:739`, `:752`
(bốn dòng lọc `"Camera từ chối"`) và `:841` (lọc `"Không lấy được khung thử"`). Cả năm nằm trong vùng
81 ca mới; không dòng nào chạm 26 ca cũ — thêm một bằng chứng độc lập cho chốt B1.

### 1.5. Hai mươi phép đột biến

Mỗi phép: sao lưu ra ngoài repo → sửa → `pytest tests/test_capture.py -q` → khôi phục. Sau cả hai mươi
lượt, `git diff --stat dev` vẫn `834 insertions(+), 3 deletions(-)` và `pytest -q` vẫn `870 passed` —
không phép nào để lại vết trong cây làm việc.

ĐB1–ĐB18 dựng lại từ §10 đặc tả; **ĐB19 và ĐB20 do lượt review này thêm** để trả lời hai câu hỏi treo.

| # | Phá gì | Đặc tả đòi đỏ | Dòng §8 đỏ thật sự | Tổng kết |
|---|---|---|---|---|
| ĐB1 | bỏ `set(CAP_PROP_FOURCC)` | 24,26,38,39,40 | 24,25,26,28,38,39,40,41,50,52,54,56,58,62,67,68,70,73 | `18 failed, 89 passed` |
| **ĐB2** ★★ | FOURCC xuống sau HEIGHT | 24,26 | **24,25,26** | `3 failed, 104 passed` |
| ĐB3 ★ | FPS lên trước WIDTH | 24,27 | 24,27 | `2 failed, 105 passed` |
| ĐB4 | bỏ `set(CAP_PROP_FPS)` | 24,29,39 | 24,27,29,38,39,40,42,44,47,68,70 | `11 failed, 96 passed` |
| **ĐB5** ★★ | đọc độ phân giải bằng `cap.get` | 55,56 | **55,56** | `2 failed, 105 passed` |
| ĐB6 | hoán vị `shape[0]/[1]` | 43 | 38,39,40,43,44,47,50,52,53,55,62,68,70 | `13 failed, 94 passed` |
| ĐB7 | `"little"` → `"big"` | 31,32,33 | 28,31,32,33,34,37,46,49 | `8 failed, 99 passed` |
| ĐB8 | bỏ `math.isfinite` | 17,**18** | **17,19** | `2 failed, 105 passed` |
| ĐB9 | bỏ loại `bool` | 22 | 22 | `1 failed, 106 passed` |
| ĐB10 | nhận `fourcc` dài ≠ 4 | 04,05 | 03,04,05,12 | `4 failed, 103 passed` |
| ĐB11 | `khop` gán cứng `True` | 45 | 45 | `1 failed, 106 passed` |
| ĐB12 | mọi `logger.warning` → `info` | 47 | 47,48,49,60 | `4 failed, 103 passed` |
| ĐB13 | trả thẳng danh sách nội bộ | 70 | 70 | `1 failed, 106 passed` |
| ĐB14 | `dong()` xoá `*_thuc_te` | 67 | 67 | `1 failed, 106 passed` |
| ĐB15 | `mo()` ném khi đọc thử hỏng | 59 | 57,58,59,60 | `4 failed, 103 passed` |
| ĐB16 | bỏ lần đọc thử | 71 | 38,39,43,44,50,52,53,54,55,56,61,62,68,70,71,72 | `16 failed, 91 passed` |
| ĐB17 | `FOURCC_MAC_DINH = "YUYV"` | 01 | 01 | `1 failed, 106 passed` |
| ĐB18 | so `fps` bằng `!=` | 52 | 52 | `1 failed, 106 passed` |
| **ĐB19** ★ *(review thêm)* | luôn báo lệch fourcc | — | **38,39,40**,50,52,54,56,58,62,68,70 | `11 failed, 96 passed` |
| **ĐB20** ★ *(review thêm)* | bỏ mệnh đề `<= 0` | — | **15,16,23** | `3 failed, 104 passed` |

**Đọc kết quả:**

- **ĐB2 và ĐB5 — hai phép chịu lực — đỏ ĐÚNG và CHỈ đỏ** những dòng đặc tả chỉ định (`24,25,26` và
  `55,56`). Cả hai đều là cài đặt **tự nhất quán**: mọi lệnh `set` vẫn gọi đủ, `canh_bao` vẫn rỗng,
  `khop` vẫn `True`, mọi kịch bản webcam tuân thủ vẫn xanh. Việc chúng đỏ chứng minh bộ ca test canh
  **đúng chỗ** chứ không canh vào một đại lượng không nhạy với khuyết tật. Đây là bằng chứng mạnh
  nhất của cả lượt review.
- ĐB1, ĐB4, ĐB6, ĐB7, ĐB16 đỏ lan rộng hơn dự đoán. Đây là **bao hàm**, không phải sai: dự đoán trong
  §10 là tập tối thiểu, và mỗi phép đều đỏ trọn tập đó. Không có phép nào đỏ **thiếu** so với dự
  đoán, trừ ĐB8 (xử lý ở §4 dưới).
- Không phép nào **vẫn xanh**. Nghĩa là không guard nào của mã việc này nằm ngoài tầm với của bộ ca
  test.
- Thông báo lỗi khớp ngữ nghĩa: ĐB8 và ĐB20 đều báo `Failed: DID NOT RAISE LoiCauHinh`, đỏ đúng các
  ca `..._dong17_fps_inf_raise`/`..._dong19_fps_nan_raise` (ĐB8) và
  `..._dong15_fps_0_raise`/`..._dong16_fps_am_raise`/`..._dong23_thong_bao_chua_ten_khoa_fps` (ĐB20).

---

## 2. Đối chiếu đặc tả

| Mục đặc tả | Kết luận |
|---|---|
| §2 Danh sách trắng | ✅ đúng hai tệp; `configs/capture.yaml` không bị chạm; không tệp mới trong `src/capture/` |
| §3.4 Bẫy `test_02` | ✅ `grep "1280\|720\|30"` rỗng; `test_02` vẫn xanh |
| §4.1 Thứ tự `set` | ✅ `src/capture/opencv_camera.py:123-127` đúng FOURCC → WIDTH → HEIGHT → FPS; `if self._fps is not None` bao lời gọi FPS |
| §4.2 Hai hàm FOURCC | ✅ `:18-42` chép đúng, little-endian, `& 0xFFFFFFFF`, byte ngoài `0x20`–`0x7E` thành `"?"` |
| §4.3 C1 (`.shape`) | ✅ `:158` `(khung.shape[1], khung.shape[0])`; không có `cap.get(CAP_PROP_FRAME…)` ở đâu trong tệp |
| §4.3 C2 (`cap.get`) | ✅ `:163-164` |
| §4.3 C3 (WARNING nêu cả hai giá trị) | ✅ `:180-188`, khuôn dạng đúng §5.5, lazy formatting |
| §4.3 C4 (cảnh báo, không chặn) | ✅ không ném, không đặt `dang_mo = False`; ca dòng 59 và ĐB15 xác nhận |
| §5.1 Hằng số | ✅ `:14-15` `FOURCC_MAC_DINH = "MJPG"`, `DUNG_SAI_FPS = 0.5` |
| §5.2 Kiểm `fourcc` | ✅ `:71-80`; thông báo chứa `opencv.fourcc` và giá trị đã nhận |
| §5.2 Kiểm `fps` | ✅ `:82-94`; loại `bool` **trước** `isinstance`, `math.isfinite`, `> 0`; vắng khoá ⇒ `None` |
| §5.3 Trình tự `mo()` | ✅ 8 bước đúng thứ tự; bước 3–6 nằm trong `try … except cv2.error` (`:115-138`) |
| §5.4 Thứ tự `canh_bao` | ✅ `:166-178`; mục 2/2' loại trừ nhau; `fps is None` ⇒ không so |
| §5.5 Khuôn dạng WARNING | ✅ `"khong_lay_duoc_khung"` không lọt vào khuôn `"Camera từ chối"` (`:186` lọc bằng `if muc in yeu_cau_theo_muc`) |
| §5.6 `VideoCaptureGia` | ✅ `tests/test_capture.py:346-414` khớp hợp đồng từng dòng — xem §3 dưới |
| §6 Bốn chốt chịu lực | ✅ B1 lệnh [5/28]+[17/28] · B2 ca dòng 78 + lệnh [4/28] · B3 lệnh [4/28] · B4 chữ ký giữ nguyên, ca dòng 76–77 |
| §7 Giao diện | ✅ tên/kiểu khớp từng ký tự; `thong_so_thuc_te` đúng 8 khoá (ca dòng 69), trả bản sao (`:251` `list(...)`, ĐB13 đỏ đúng dòng 70) |
| §8 Bảng 81 ca | ✅ **81/81** dòng có ca tương ứng, một dòng một hàm, tên `test_fourcc_dong<NN>_…` |
| §11 Ràng buộc kỹ thuật | ✅ chỉ thêm `math` (thư viện chuẩn); ngoại lệ chỉ `LoiCamera`/`LoiCauHinh`; không `VideoWriter_fourcc`; type hints + docstring tiếng Việt Google |
| §12 Ngoài phạm vi | ✅ không làm gì trong danh sách cấm — xem 🔵-2 về hệ quả |

**Kiểm riêng hai điểm sống còn:**

- **Trung thực số liệu (R5)**: không có giá trị mặc định nào trông như kết quả đo, không có số ví dụ
  trong docstring có thể bị chép nhầm vào báo cáo. `DUNG_SAI_FPS = 0.5` là dung sai của **phép so**,
  đã được §5.1 chốt là không thuộc `configs/` kèm lý do — không phải magic number thực nghiệm (CA-1).
  Các con số `1280`/`720`/`30` nằm **duy nhất** trong `configs/capture.yaml`.
- **Fail-safe phần cứng (R24)**: webcam từ chối cấu hình ⇒ WARNING, hệ thống vẫn chạy được trên
  phần cứng khác (C4). Đọc khung thử thất bại ⇒ ghi WARNING, `dang_mo` vẫn `True`, không sập. `dong()`
  vẫn `release()` trong `try/finally`. Không có nhánh nào mới có thể làm sập vòng lặp chính.

---

## 3. Bảy chỗ `coder` khai tự diễn giải — đã soi từng chỗ

| Chỗ | Phán |
|---|---|
| Nhóm E dùng `fps=25`, riêng dòng 42 dùng `fps: 30` | ✅ đúng. Đặc tả chỉ chốt `fps: 30` cho dòng 42 và 50–52; các dòng còn lại chỉ cần "cfg có `fps`". Dùng `25` ở nơi khác **tăng** sức phân biệt vì nó khác `fps_ban_dau=10.0` lẫn dung sai |
| Dòng 53–58, 62 bỏ khoá `fps`; dòng 61 có `fps: 30` | ✅ đúng và tốt hơn: bỏ `fps` cô lập biến, để `canh_bao == ["do_phan_giai"]` là phép so `==` chặt chứ không phải phép so tập hợp lỏng. Dòng 61 giữ `fps` vì nó cần đủ ba mục lệch |
| Điều kiện ném viết `gia_tri_fps <= 0` thay vì `not (> 0)` | ✅ tương đương với số hữu hạn (đã lọc `nan`/`inf` bằng `isfinite` **trước** đó, `:90` đứng trước `:91`). ĐB20 chứng minh mệnh đề này có hiệu lực thật (đỏ 15,16,23) |
| Ba hàm trợ giúp `_gan`, `_gan_chuoi`, `_cfg` | ✅ đã đọc mã xác nhận, không chỉ dựa vào ĐB5. `VideoCaptureGia.get()` (`tests/test_capture.py:393-401`) trả **trạng thái nội bộ** `self._fourcc`/`self._fps`/`self._rong`/`self._cao`, và `set()` (`:377-391`) **không** cập nhật trạng thái khi tên nằm trong `tu_choi`. `read()` (`:403-411`) lấy kích thước từ `_kich_thuoc_khung` **nếu khác `None`**, ngược lại mới theo kích thước báo cáo — tức `kich_thuoc_khung` **tách rời** `kich_thuoc_ban_dau` đúng §5.6 |
| Hai hàm mã hoá FOURCC chép nguyên văn §4.2 | ✅ `:27` và `:41-42` khớp từng ký tự |
| Bỏ lại việc sửa `benchmark_detect.py` | ✅ đúng §12 — nhưng để lại một khoảng trống quy trình, ghi ở 🔵-2 |
| `_do_thong_so_thuc_te` là phương thức mới (không có trong §7) | ✅ hàm private, không đổi giao diện công khai; §7 chỉ khoá chữ ký các thành viên công khai |

---

## 4. Bốn câu hỏi treo — phán từng câu

**4.1. G1 bị bác — phép sửa của `coder` là siết, không nới.**
`coder` thêm `and r.levelno == logging.WARNING` vào bộ lọc `caplog` ở các ca dòng 40, 47, 48, 49, 60
(`tests/test_capture.py:668, 725, 739, 752, 841`). Nghi vấn đặt ra ở lượt trước: liệu điều kiện thêm
này có làm ca dòng 40 mất khả năng bắt lỗi không. **ĐB19** trả lời dứt điểm: khi mã sản phẩm bị sửa
để **luôn** báo lệch fourcc, dòng 40 **đỏ**. Nghĩa là bộ lọc vẫn bắt được một bản ghi `"Camera từ
chối"` thừa trên đường thành công. Kết luận này đến từ một phép đột biến của lượt review, **không**
từ lời khai của `coder`.

**4.2. G2 xác nhận — dòng 18 được canh hai lớp, đặc tả §10 dự đoán sai.**
Cặp ĐB8 + ĐB20 khép kín lập luận:

| Phép | `-inf` bị chặn bởi | Dòng 18 |
|---|---|---|
| ĐB8 — bỏ `isfinite` | mệnh đề `<= 0` (vì `-inf <= 0` là `True`) | **xanh** |
| ĐB20 — bỏ `<= 0` | `math.isfinite(-inf)` là `False` | **xanh** |

Nên dòng 18 (`fps: float("-inf")`) về nguyên tắc **không nhạy riêng** với phép nào — nó là ca biên
được hai guard cùng phủ. Mã cài đặt **đúng**; thứ sai là **bảng ĐB8 trong đặc tả §10**, vốn liệt kê
dòng 18 vào tập "phải đỏ". Đây là lỗi tài liệu của `spec-writer`, không phải lỗi người cài đặt — ghi
ở 🔵-1.

**4.3. G8 — flake, không phải hồi quy.**
Lượt container [15/28] chạy **sạch hoàn toàn** (`0 failed`); ca
`tests/test_benchmark_detect.py::test_camera_dong26` mà `coder` gặp đỏ lần trước nay **xanh** trong
cùng điều kiện, cùng image `faceid:arm64`, cùng bộ lọc marker. Đủ kết luận là jitter QEMU. Ngưỡng
tuyệt đối vẫn mong manh — ghi ở 🔵-3.

**4.4. G6 và G7 — mã có sẵn từ `P1-01`, ngoài phạm vi mã việc này.**
Diff xác nhận cả hai đều là **dòng ngữ cảnh**, không phải dòng thêm:
`self._warmup_frames = self.cfg.get("warmup_frames", 0)` (`:68`, mặc định `0` có từ `P1-01`, không bị
mã việc này đổi) và hai chỗ `self._cap = None` không kèm `release()` (`:118`, `:137`). Ghi nhận ở
🔵-4, không tính là lỗi của `P2-08`.

---

## 5. Lỗi phải sửa

**Không có mục 🔴 CHẶN-A, 🔴 CHẶN-B, hay 🟡 CẦN SỬA nào.**

Đã rà đủ bảng mẫu vi phạm `code-review.instructions` §2 (lệnh [19/28]–[28/28]), đủ bốn mức của thang
§3, và đủ từng mục của đặc tả (§2 bảng trên). Không có: hardcode tham số thực nghiệm, `print()`,
`except` trần mới, rò rỉ tài nguyên **mới**, nạp model trong vòng lặp, test giả, log f-string, thiếu
type hint/docstring, thiếu ca test so với bảng §8, hay dependency ngoài đặc tả.

---

## 6. 🔵 Góp ý (không chặn — người dùng quyết định)

### 🔵-1 — Sửa bảng ĐB8 trong đặc tả để lần sau không báo động giả
**Vị trí**: `docs/dac-ta/P2-08-camera-fourcc-fps.md:773`
```
| ĐB8 | Bỏ `math.isfinite` khi kiểm `fps` | 17, 18 |
```
**Vì sao**: dòng 18 (`-inf`) được `isfinite` và `<= 0` cùng phủ, nên không phép đột biến đơn lẻ nào
làm nó đỏ (chứng minh ở §4.2). Một người cài đặt sau đọc bảng này sẽ tưởng mã của mình sai và đi sửa
một chỗ vốn đúng, tốn một vòng bàn giao.
**Sửa**: đổi cột "Dòng §8 phải đỏ" của ĐB8 thành `17, 19`, và thêm một dòng ghi chú: *"dòng 18 được
hai guard cùng phủ nên cố ý không xuất hiện ở ĐB8 lẫn ĐB20"*. Cân nhắc đưa **ĐB20** (bỏ mệnh đề
`<= 0`, phải đỏ `15, 16, 23`) thành phép đột biến chính thức — nó canh guard `> 0` mà bảng §10 hiện
bỏ trống. Chi phí: sửa 2 dòng tài liệu. Lợi: bảng đột biến trở nên tự nhất quán.

### 🔵-2 — `.meta.json` của lượt đo Pi 5 chưa mang được thông số thật vừa phơi ra
**Vị trí**: `scripts/benchmark_detect.py:485-499` (dict meta hiện có 8 khoá:
`backend_thu_hinh`, `do_phan_giai_yeu_cau`, `do_phan_giai_that`, `khop_do_phan_giai`, …) — **không**
có `fourcc_thuc_te` hay `fps_thuc_te`.
**Vì sao**: mục đích của cả mã việc là để lượt đo trên Pi 5 **tự nói ra** webcam đang chạy ở định
dạng nào. Hiện `thong_so_thuc_te` mới chỉ **tồn tại**; nơi tiêu thụ chưa nối. Hệ quả cụ thể: ba tệp
`results/bench_detect_camera_*` sinh ra ở §12b sẽ **không** truy được về định dạng thật, và bằng
chứng duy nhất là dòng `Pixel Format` dán tay từ §12a — dán tay thì không tự động khớp với tệp kết
quả nào, ngược với tinh thần R6/R17.
**Phán**: **không** phải lỗi của `P2-08` — §12 đặc tả cấm rõ ràng, `coder` làm đúng. Đây là khoảng
trống **quy trình**, thuộc quyền quyết định của người dùng.
**Đề xuất**: mở mã việc `P2-09` (sửa `benchmark_detect.py` gọi `cam.thong_so_thuc_te` và `update` vào
meta) **trước** khi chạy §12b, để bộ số đo đầu-cuối tự mang bằng chứng định dạng. Chi phí: một mã
việc nhỏ (~1 tệp mã, ~1 tệp test), lùi lượt đo khoảng một nhịp. Nếu người dùng muốn đo ngay, phương
án thay thế là chạy §12b trước rồi **đo lại** sau khi có `P2-09` — nhưng đo lại tốn công hơn viết mã.

### 🔵-3 — Ngưỡng thời gian tuyệt đối trong ca 26 vẫn mong manh trên QEMU
**Vị trí**: `tests/test_benchmark_detect.py:1775`
```python
assert all(r["latency_ms"] < 20 for r in bg)
```
**Vì sao**: ca này ngủ 2 ms giả lập suy luận rồi khẳng định tổng dưới 20 ms **theo đồng hồ tường**.
Trong `faceid:arm64` qua QEMU, chi phí lập lịch có lúc vượt 18 ms và ca đỏ mà mã hoàn toàn không đổi
— đúng thứ vừa xảy ra với `coder`. Một ca đỏ ngẫu nhiên làm mất niềm tin vào **toàn bộ** bảng kết
quả và tốn một lượt chạy 10 phút để phân biệt flake với hồi quy.
**Phán**: lượt này ca 26 xanh, không chặn. `P2-07` đã ghi một mục 🔵 cùng loại cho ca 97.
**Đề xuất**: gộp cả hai vào **một** mã việc dọn dẹp: đổi phép khẳng định từ ngưỡng tuyệt đối sang
**quan hệ** (`latency_ms` phải nhỏ hơn `latency_tong_ms`, hoặc nhỏ hơn `k` lần thời gian ngủ đã đặt),
là đại lượng bất biến trước tốc độ máy. Không nên gắn `@pytest.mark.slow` — điều đó chỉ giấu ca đi
chứ không sửa phép đo.

### 🔵-4 — Hai chỗ `self._cap = None` không kèm `release()` (di sản `P1-01`)
**Vị trí**: `src/capture/opencv_camera.py:118` và `:137`
```python
self._cap = None
raise LoiCamera(...)
```
**Vì sao**: khi `isOpened()` sai hoặc `cv2.error` bật ra giữa chừng, đối tượng `VideoCapture` bị bỏ
mà không `release()`. Trên Pi 5 với webcam USB, thiết bị có thể bị giữ cho tới khi tiến trình thoát,
làm lần `mo()` sau thất bại vì lý do khác hẳn — một lỗi rất tốn công chẩn đoán. Cùng nhóm: gọi `mo()`
hai lần liên tiếp không `dong()` cũng ghi đè `self._cap` mà không giải phóng.
**Phán**: **ngoài phạm vi `P2-08`** — cả hai dòng là ngữ cảnh của diff, có từ `P1-01`, mã việc này
không làm xấu đi. Tuy nhiên `P2-08` có **tăng nhẹ mức phơi nhiễm**: nay có thêm một lời gọi `read()`
trong `_do_thong_so_thuc_te` nằm trong cùng khối `try`.
**Đề xuất**: gộp vào cùng mã việc dọn dẹp với 🔵-3 — thêm `self._cap.release()` trước mỗi lần gán
`None` trên đường lỗi, và một ca test khẳng định `cam_gia.da_release is True` sau khi `mo()` ném.

### 🔵-5 — `fps_thuc_te` bằng `nan` sẽ lọt qua phép so mà không cảnh báo
**Vị trí**: `src/capture/opencv_camera.py:174`
```python
if self._fps is not None and abs(self._fps_thuc_te - self._fps) > DUNG_SAI_FPS:
```
**Vì sao**: `abs(nan - 30) > 0.5` cho `False`, nên một driver trả `nan` sẽ được coi là **khớp** —
đúng chế độ hỏng im lặng mà mã việc này sinh ra để chống. Xác suất thấp (OpenCV thường trả `0.0` cho
thuộc tính không hỗ trợ, và `0.0` bị bắt đúng), nên không chặn.
**Đề xuất**: nếu có mã việc chạm lại tệp này, đổi thành
`not math.isfinite(self._fps_thuc_te) or abs(...) > DUNG_SAI_FPS`, kèm một ca test cho
`fps_ban_dau=float("nan")`. Chi phí: 1 dòng mã + 1 ca test.

---

## 7. Việc tiếp theo

1. **Được commit và gộp `dev`.** Gợi ý commit message (R29):
   `feat(capture): P2-08 đặt FOURCC MJPG, áp CAP_PROP_FPS và phơi thông số thật của camera`
2. Sau khi gộp, chạy **§12a** (kiểm rẻ trên Pi 5, đối chiếu `v4l2-ctl --get-fmt-video`). Nếu
   `Pixel Format` vẫn là `'YUYV'` thì **dừng, không đo**, và mở lại review với dict
   `thong_so_thuc_te` in ra ở terminal thứ nhất.
3. Quyết định 🔵-2 **trước** khi chạy §12b: mở `P2-09` để `.meta.json` tự mang `fourcc_thuc_te`, hay
   chấp nhận dán tay bằng chứng §12a cho lượt đo này.
4. Ba lượt đo **§12b** do người dùng chạy, commit đủ 6 tệp `results/` + `.meta.json`, dán nhiệt độ và
   `throttled` trước/sau phiên vào mục "vòng 2" của biên bản này.
5. 🔵-1 gửi `spec-writer`; 🔵-3 + 🔵-4 + 🔵-5 gom thành một mã việc dọn dẹp nếu người dùng đồng ý.
