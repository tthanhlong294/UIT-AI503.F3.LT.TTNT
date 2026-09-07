# Review P3-05-benchmark-recognize — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-05-benchmark-recognize.md` |
| **Nhánh** | `feat/p3-05-benchmark-recognize`, commit `d65cf27`, điểm rẽ nhánh `dev` tại `bf6d870` |
| **Mã được kiểm** | hai tệp, **+3073 / −0** (bảng §1.2) |
| **Ngày** | 2026-09-07 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — **0 mục 🔴**, **2 mục 🟡** (cả hai nằm trong tệp kiểm thử, mã sản phẩm không phải sửa dòng nào). Kèm 5 mục 🔵 và **ba khuyết tật của đặc tả** |

Toàn bộ số liệu dưới đây đến từ **lượt chạy của người dùng**. Bảng tự kiểm mà người cài đặt dán về
**không** được chép lại; mười hai phép đột biến được dựng lại từ đầu, mọi lượt khôi phục cho `sha256`
**KHỚP**, hai mã băm cuối trùng khít mốc đầu, `git status` và `git diff --stat` sau cùng đều rỗng.

Ba điều đáng ghi của lượt kiểm này:

1. **Hai phép đột biến không làm ca nào đỏ** (M7, M8). Đây là kết quả chính: bộ 134 ca xanh toàn
   phần vẫn để lọt hai chốt, và không lệnh `black`/`ruff`/`pytest` nào phát hiện được.
2. **Mã sản phẩm đúng ở cả hai chỗ đó.** Khuyết tật nằm ở tệp kiểm thử — và ở hai trong ba trường
   hợp, gốc rễ nằm ở **ô "Assert tối thiểu" của chính đặc tả**.
3. Ba điểm chịu lực nặng nhất — loại ảnh đã đăng ký theo mã băm nội dung, tính open-set, từ chối
   ghi đè — đều **đứng vững** trước đột biến, và cặp ca 34/35 phân biệt đúng hai cài đặt gần giống
   nhau như §8.4 đặc tả dự đoán.

---

## 1. Kết quả kiểm máy

**Người dùng chạy ngày 2026-09-07.** Lệnh chép theo đúng khuôn §9–§10 đặc tả; mỗi ô trong bảng truy
được về một đoạn kết quả người dùng dán về. Ô nào chưa có lượt chạy được ghi rõ `[CHƯA DỰNG LẠI]`.

### 1.1. Ba lệnh nền và bộ kiểm thử — host `pc_x86`, Windows, Python 3.12.5, **có** `models/` và `data/`

| # | Lệnh | Kết quả |
|---|---|---|
| [1/20] | `python -m black --check --line-length 100 scripts/benchmark_recognize.py tests/test_benchmark_recognize.py` | `2 files would be left unchanged` ✅ |
| [2/20] | `python -m ruff check scripts/benchmark_recognize.py tests/test_benchmark_recognize.py` | `All checks passed!` ✅ |
| [3/20] | `python -m pytest -q` (không lọc marker) | **689 passed**, 0 failed, 0 skipped, 283 s ✅ |
| [4/20] | `python -m pytest -q tests/test_benchmark_recognize.py` | **134 passed**, 0 skipped, 22,76 s ✅ |
| [5/20] | `python -m pytest -q --ignore=tests/test_benchmark_recognize.py` | **555 passed** ✅ |

Số học khép kín: 689 − 134 = **555**, đúng bằng mốc của `dev` tại `bf6d870` (`pc_x86`, không lọc
marker). Tệp mới **không** tác động lên một ca cũ nào — [5/20] là phép đo trực tiếp điều đó, không
phải suy luận từ tổng.

### 1.2. Phạm vi tệp

| # | Lệnh | Kết quả |
|---|---|---|
| [6/20] | `git diff --stat dev...HEAD` | đúng **hai** tệp, **3073 thêm, 0 xoá** ✅ |
| [7/20] | `git diff --name-status dev...HEAD` | hai dòng `A` (tệp mới) ✅ |
| [8/20] | lọc đuôi tệp cấm `\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$` | **rỗng** ✅ |

| Tệp | Thêm | Bớt |
|---|---|---|
| `scripts/benchmark_recognize.py` | 1284 | 0 (tệp mới) |
| `tests/test_benchmark_recognize.py` | 1789 | 0 (tệp mới) |

Đúng hai tệp của danh sách trắng §2 đặc tả, không tệp thứ ba. `src/`, `configs/`, `docs/`,
`results/`, `report/`, `requirements.txt`, `.gitignore`, `.claude/**`, `CLAUDE.md` **không bị đụng**
→ không có lý do dựng lại `faceid:arm64` (R43), lượt container [9/20]–[11/20] chạy trên đúng image
đang có. **CA-5 loại trừ. R25 sạch.**

Cột "Bớt = 0" ở cả hai tệp có ý nghĩa riêng: không dòng nào của kho bị xoá, nên **không ca test cũ
nào bị sửa để đi qua** — CB-6 bị loại trừ bằng số học, cộng thêm [5/20] xác nhận bằng lượt chạy.

### 1.3. Container `faceid:arm64`, Python 3.11.16 — phép kiểm người cài đặt không tự chạy được

| # | Lệnh | Kết quả |
|---|---|---|
| [9/20] | `pytest -q -m "not slow"` toàn kho, trong `faceid:arm64` | **656 passed, 1 skipped, 32 deselected**, 0 failed, 702 s ✅ |
| [10/20] | `pytest -q -m "not slow" tests/test_benchmark_recognize.py` trong `faceid:arm64` | **134 passed**, 0 skipped, 0 deselected ✅ |
| [11/20] | `pytest --collect-only -q tests/test_benchmark_recognize.py` trong `faceid:arm64` | **134 tests collected**, không lỗi import ✅ |

Ba phép đối chiếu, cả ba đều khớp:

- 656 + 1 + 32 = **689** = tổng thu thập trên host. Ba môi trường cùng một tập ca.
- 656 − 522 = **134**: số ca `passed` trong container tăng **đúng bằng** số ca mới trên host. Không
  ca nào phụ thuộc thứ container thiếu (`models/`, `data/`, `docs/`, `.git/`, `ultralytics`, `torch`).
- `deselected` giữ nguyên **32**, `skipped` giữ nguyên **1** → **không ca mới nào mang
  `@pytest.mark.slow`**, không ca mới nào có người gác `skip`. Đúng ràng buộc §3.4 và câu chốt cuối
  §8 đặc tả, và kiểm được bằng số chứ không bằng đọc mắt.

[11/20] bắt riêng chế độ hỏng "import ở mức module một thứ container không có" — chế độ đã giết
`P2-01` và `P2-03`. Sạch.

### 1.4. Quét mẫu vi phạm

| # | Lệnh | Kết quả |
|---|---|---|
| [12/20] | `grep -nE "\bthreshold\b" scripts/benchmark_recognize.py` | **rỗng** ✅ |
| [13/20] | `grep -n "except Exception" scripts/benchmark_recognize.py` | **rỗng** ✅ |
| [14/20] | `grep -rnE "ultralytics\|import torch\|matplotlib\|seaborn\|plotly\|scipy\|sklearn\|pandas" scripts/benchmark_recognize.py` | **rỗng** ✅ |
| [15/20] | `grep -nE "\b(100\|200\|0\.01\|112\|128\|512)\b" scripts/benchmark_recognize.py` | **đúng hai dòng**, cùng một hằng số ✅ |
| [16/20] | `grep -n "\.enroll(\|np\.mean\|np\.average\|linalg\.norm" scripts/benchmark_recognize.py` | **hai dòng** — giải trình dưới đây ✅ |
| [17/20] | `grep -n "assert True\|pytest\.mark\.slow\|/home/\|/Users/" hai tệp` | **rỗng** ✅ |
| [18/20] | `git status --short --untracked-files=all results configs data` sau toàn bộ lượt pytest | **rỗng** ✅ |

Giải trình từng dòng không rỗng, theo yêu cầu §9.2 đặc tả:

- **[15/20]** — `scripts/benchmark_recognize.py:52` là chú thích dẫn R9 và
  `experiment-protocol.instructions.md` §6; `:53` là `SO_MAU_TOI_THIEU = 100`. Đúng ngoại lệ hợp lệ
  mà §5.3 đặc tả liệt kê. **`200` và `0.01` không xuất hiện** — hai giá trị đó đi qua
  `benchmark.so_buoc_nguong` và `benchmark.far_muc_tieu` của `configs/recognize.yaml` như §5.2 chốt.
  **CA-1 loại trừ.**
- **[12/20] rỗng** là mục quan trọng nhất trong bảng này: khoá `threshold` của `configs/recognize.yaml`
  đang mang chuỗi `TBD`, script không đọc nó, nên không có đường nào để một ngưỡng chưa chốt lọt vào
  phép đo. **CA-7 loại trừ.**
- **[16/20] dòng `:426`** — `vec = backend.enroll(anh_da_doc, {"min_images_per_user": so_anh_enroll})`,
  nằm trong `dung_gallery_trong_bo_nho`. Đúng **một** dòng mã thi hành như §9.2 kỳ vọng: script
  **không** tự tính vectơ trung bình, phép chuẩn hoá L2 trước khi trung bình vẫn chỉ có một bản cài
  đặt duy nhất trong kho.
- **[16/20] dòng `:673`** — `latency_tb = float(np.mean(latency))`, trong `tong_hop_toc_do`.
  **Đã đọc mã quanh dòng này để xác nhận, không tin phán đoán sẵn**: `latency` được dựng ở dòng 672
  từ cột `latency_identify_ms` của các bản ghi (`np.array([r["latency_identify_ms"] for r in ban_ghi])`),
  là một mảng **một chiều các số mili-giây**, không phải tập vectơ đặc trưng. Giá trị trả về đi vào
  `latency_tb_ms` và `fps_suy_ra` — đúng thứ §7.3 đặc tả yêu cầu tính. **Dương tính giả, không phải
  vi phạm.** Vùng cấm ở đây là `dung_gallery_trong_bo_nho`, và [16/20] cho thấy trong hàm đó không có
  `np.mean` nào.
- **[18/20]** — chốt rằng không ca test nào ghi vào `results/`, `configs/` hay `data/` thật. Mọi ca
  ghi tệp dùng `tmp_path` qua `monkeypatch` hằng số `_THU_MUC_KET_QUA_MAC_DINH`. Đây là điều kiện
  cần để tin mọi con số trong `results/` về sau đến từ lượt chạy có chủ đích của người dùng.

### 1.5. Mười hai phép đột biến

Lượt đối chứng chưa đột biến: **134 passed**, 0 ca đỏ. Mọi phép đi đủ bốn bước *sao lưu ra ngoài repo
→ sửa → chạy → khôi phục và đối chiếu `sha256`*; **mọi lượt khôi phục KHỚP**.

| # | Mã | Phép đột biến | Ánh xạ §10 | Kết quả | Ca đỏ | Kết luận |
|---|---|---|---|---|---|---|
| [19/20] | M1 | loại theo đường dẫn tương đối thay vì mã băm nội dung | **ĐB2** | 1 failed, 133 passed | `test_dong35`, **ca 34 vẫn xanh** | ✅ đúng dự đoán |
| | M2 | bỏ hẳn phép loại ảnh đã đăng ký | ĐB1 | 4 failed, 130 passed | 34, 35, 36a, 37 | ✅ |
| | M3 | một `random.Random(seed)` dùng chung | ĐB11 | 1 failed, 133 passed | `test_dong16` | ✅ |
| | M3b | M3 + ca 16 quay về **dạng chữ trong đặc tả** | ĐB11 | **134 passed** | không ca nào | ⚠️ khuyết tật đặc tả |
| | K1 | chỉ đổi ca 16 về dạng chữ đặc tả, mã sản phẩm nguyên vẹn | — | **134 passed** | không ca nào | ✅ đối chứng |
| | M4 | bỏ tính open-set, impostor luôn được chấp nhận | ngoài §10 | 2 failed, 132 passed | `test_dong55`, `test_dong58` | ✅ |
| | M5 | băm trên danh sách ứng viên thay vì ảnh đo được | ĐB14 | 1 failed, 133 passed | `test_dong98` | ✅ |
| | M6 | bỏ chốt từ chối ghi đè | ĐB12 | 2 failed, 132 passed | `test_dong104`, `test_dong105` | ✅ |
| | **M7** | nới `so_buoc_nguong >= 2` thành `>= -10` | ngoài §10 | **134 passed** | **không ca nào** | 🟡 **CẦN SỬA-1** |
| | **M8** | đổi tên cột `top1_score` trong `_COT_CSV_THO` | ngoài §10 | **134 passed** | **không ca nào** | 🟡 **CẦN SỬA-2** |
| | M9 | bỏ `math.isfinite` ở `chot_diem_can_bang` | ĐB13 | 134 passed | không ca nào | ⚠️ khuyết tật đặc tả |
| | M9b | bỏ `math.isfinite` ở `_doc_far_muc_tieu` | ĐB13 | 134 passed | không ca nào | ⚠️ khuyết tật đặc tả |
| [20/20] | | bảng kiểm biểu thức cho `inf`, `-inf`, `nan`, `0.0`, `1.5`, `0.01` | — | **cả sáu giá trị `GIONG NHAU`** | — | xem §4.3 |

**M1 là phép quan trọng nhất và nó cho đúng kết quả đặc tả dự đoán**: một cài đặt **tự nhất quán**
(loại theo đường dẫn) trông hoàn toàn hợp lý, đi qua ca 34, và **chỉ** trượt ca 35. Cặp ca 34/35 vì
vậy có hiệu lực phân biệt thật, không phải hai ca trùng nhau. Đây là chốt chịu lực nhất của cả mã
việc (§4.1) và nó đứng vững.

⚠️ **Phạm vi hiệu lực của lượt kiểm này — ghi rõ để không ai đọc nhầm.** Bảy trên mười bốn phép của
§10 đã được dựng lại độc lập: ĐB1, ĐB2, ĐB11, ĐB12, ĐB13, ĐB14 và một phần ĐB7 (qua M2). **ĐB3, ĐB4,
ĐB5, ĐB6, ĐB8, ĐB9, ĐB10 `[CHƯA DỰNG LẠI]`** trong vòng này. Kết luận về bảy phép đó hiện **chỉ dựa
trên đọc mã** (§2.2 dưới đây), tức là ở mức lời khai của người cài đặt cộng phép đọc của người
review, **chưa phải bằng chứng máy**. Vòng 2 nên dựng lại đủ bảy phép còn thiếu cùng với hai bản sửa.

---

## 2. Đối chiếu đặc tả

### 2.1. Theo mục

| Mục | Kết luận |
|---|---|
| §2 Danh sách trắng | ✅ đúng hai tệp, không tệp thứ ba — [6/20], [7/20] |
| §4.1 Loại ảnh đã đăng ký theo mã băm nội dung | ✅ `benchmark_recognize.py:1047-1050`, chứng minh bằng M1 + M2 |
| §4.2 Bài toán open-set | ✅ mọi chỉ số là hàm của ngưỡng; không có chỉ số nào tính "một lần"; chứng minh bằng M4 |
| §4.3 Tách val/test | ✅ `--tap` bắt buộc, không mặc định (`:832-837`); ba nhánh đúng bảng |
| §4.4 Hai chế độ gallery | ✅ đủ 7 bước chế độ `tep`, 6 bước chế độ `chia` — đọc từng bước, §2.2 |
| §4.5 Hai mã băm dấu vết | ✅ công thức đúng nguyên văn (`:180-187`); M5 chứng minh băm trên ảnh **đo được** |
| §4.6 Backend giả | ✅ `_BackendGia` tất định theo nội dung ảnh, đếm `so_lan_enroll`, không cần `models/` — [10/20] |
| §4.7 Bốn cảnh báo không chặn | ✅ đủ bốn khoá, đều nối vào `notes` (`:1092-1133`) |
| §5.1 Giao diện dòng lệnh | ✅ đủ 14 cờ, đúng mặc định, đúng phân vai argparse ↔ `main()` |
| §5.2 Hai khoá cấu hình mới | ✅ đọc từ config, không hardcode — [15/20]; **nhưng năm ca canh nó vô hiệu**, xem 🟡 CẦN SỬA-1 |
| §5.3 Hằng số có tên | ✅ `SO_MAU_TOI_THIEU`, `_MOI_TRUONG_PHAN_CUNG_DICH` đúng giá trị, có chú thích dẫn nguồn |
| §6 Chữ ký hàm | ✅ **khớp từng ký tự** cả 14 hàm public: tên, thứ tự tham số, kiểu trả về, mục `Raises` |
| §7.1 Xử lý một probe | ✅ đủ 6 bước; hoà điểm lấy `user_id` nhỏ nhất nhờ `sorted(gallery)` + so sánh `>` chặt (`:489-493`) |
| §7.2 Định nghĩa 11 chỉ số | ✅ đúng công thức chốt cứng; `>=` ở cả hai chỗ chấp nhận (`:555`, `:560`) |
| §7.3 Chốt cân bằng và tốc độ | ✅ EER lấy `\|far−frr\|` nhỏ nhất, hoà lấy ngưỡng nhỏ nhất; `nguong_far_muc_tieu` lấy ngưỡng nhỏ nhất |
| §7.4 Ba tệp kết quả | ✅ 14/17 cột đúng thứ tự, 23 khoá meta, 16 khoá `dataset`, `run_id` mang tên backend, từ chối ghi đè (M6); **nhưng ba ca canh cột vô hiệu**, xem 🟡 CẦN SỬA-2 |
| §7.5 Bảng in ra cuối | ✅ đủ mục, có câu nhắc EER không dùng chốt ngưỡng và câu nhắc Pi 5 |
| §8 Bảng nghiệm thu | ⚠️ 134/134 ca có mặt và xanh, **nhưng 8 ca không có hiệu lực phân biệt** (111–115, 87, 88, 91) |
| §11 Ràng buộc kỹ thuật | ✅ chỉ thư viện được phép — [14/20]; `time.perf_counter()`; `newline=""`; `encoding="utf-8"`; ngoại lệ dùng `LoiCauHinh`/`LoiMoHinh` |
| §12 Ngoài phạm vi | ✅ không vẽ hình, không ghi ngưỡng vào `configs/`, không tạo `data/splits/`, không sửa `enroll.py`, không chạy §12b — [6/20] và [18/20] là bằng chứng |

### 2.2. Bốn điểm chịu lực — đọc mã đối chiếu, không dựa vào bộ test

1. **Bỏ qua thư mục dấu chấm và từ chối gallery dở dang** — `:260-277`. Danh sách backend gợi ý lọc
   `not p.name.startswith(".")`, đúng quy ước `P3-04` §4.4: `.dlib.dang-ghi` là trạng thái trung
   gian, gợi ý nó cho người dùng sẽ dẫn họ vào một gallery đang ghi dở. Thiếu `manifest.csv` **hoặc**
   thiếu `gallery.meta.json` đều ném `LoiCauHinh` **trước khi** nạp bất kỳ `.npy` nào — thư mục chỉ
   có `.npy` không bao giờ được coi là gallery, nên không có đường nào để một lượt đo mất dấu vết
   R17 mà vẫn chạy. ✅
2. **Loại ảnh đã đăng ký theo mã băm nội dung** — `:1046-1050`. Tập băm dựng **một lần** trước vòng
   lọc, không băm lại trong vòng lặp. Phép lọc đặt **sau** phép lọc theo `--danh-sach-impostor`, nên
   thứ tự không tạo kẽ hở. Chốt "không còn probe genuine" (`:1052-1060`) đặt **trước** mọi phép ghi
   tệp, và ca 37 xác nhận không tệp nào được ghi khi nó kích hoạt. ✅
3. **Tính open-set** — `:546-570`. `far` chia cho `so_impostor`, `frr` chia cho `so_genuine`, mẫu số
   `0` trả ô rỗng chứ không chia cho 0. Ba loại lỗi của probe genuine tách rời đúng §7.2: `tp`,
   `fp_nham_nguoi`, `fn`. `precision` tính **cả** `fp_nham_nguoi` vào mẫu số (`:568`) — đây là chỗ
   dễ sai nhất trong cả bảng chỉ số và nó đúng, ca 59 canh trực tiếp. ✅
4. **CSV thô lưu mã băm chứ không lưu đường dẫn** — `:507`, `anh_bam` là 12 ký tự đầu của
   `bam_noi_dung`. `results/*.csv` **nằm trong git** (§3.5 đặc tả), nên đây là điều kiện cần để R25
   không bị vi phạm khi gallery người nhà thay LFW. Đã kiểm thêm: `user_id_that` đi vào CSV là mã
   giả danh theo `docs/quy-uoc-du-lieu.md` §1 (`u01`, `u02`…), không phải tên thật — nên cột danh
   tính cũng an toàn khi commit. `meta.dataset.anh_dir` chỉ lưu **thư mục**, không lưu đường dẫn
   từng ảnh khuôn mặt. ✅

Ngoài bảng đặc tả, đã soi riêng các rủi ro mà đặc tả không phủ:

- **Rò rỉ tài nguyên (CB-3)**: mọi lượt mở tệp đều qua `with`; không có handle camera/GPIO. Sạch.
- **Nạp mô hình trong vòng lặp (CB-5)**: `tao_bo_nhan_dien` gọi **một lần** ở `:961`, ngoài mọi vòng
  lặp. Sạch.
- **Nuốt lỗi (CB-4)**: không `except:` trần, không `except Exception` — [13/20]. Các `except` đều bắt
  loại hẹp (`LoiCauHinh`, `LoiMoHinh`, `ValueError`, `CalledProcessError/OSError`,
  `PackageNotFoundError`) và đều **có** thân xử lý, không `pass`. Sạch.
- **An toàn phần cứng (CB-2)**: mã việc này không chạm GPIO/relay/camera — không áp dụng.
- **Trung thực số liệu (CA-7)**: không giá trị mặc định nào trông như kết quả đo; không con số ví dụ
  nào trong docstring có thể bị chép nhầm vào báo cáo; không đọc `threshold`. Sạch.

---

## 3. Lỗi phải sửa

### 🟡 CẦN SỬA-1 — Năm ca 111–115 trả `1` vì lý do khác, không vì `so_buoc_nguong` sai (CS-4)

**Vị trí**: `tests/test_benchmark_recognize.py:409-426` (hàm trợ giúp `_main_voi_so_buoc`), dùng bởi
`:1652`, `:1656`, `:1660`, `:1664`, `:1668`.

```python
def _main_voi_so_buoc(tmp_path: Path, gia_tri: str) -> int:
    cfg_text = f"benchmark:\n  so_buoc_nguong: {gia_tri}\n  far_muc_tieu: 0.5\n"
    p = tmp_path / "cfg.yaml"
    p.write_text(cfg_text, encoding="utf-8")
    return br.main([..., "--vao", str(tmp_path), "--config", str(p)])
```

**Vì sao**: tệp cấu hình dựng ở đây **chỉ có khối `benchmark`**, không có `enroll.gallery_dir`. Chế
độ gallery mặc định là `tep`, nên `main()` đi tới `benchmark_recognize.py:929`
(`lay_gia_tri(cfg, "enroll.gallery_dir")`), ném `LoiCauHinh`, và trả `1` **bất kể**
`so_buoc_nguong` mang giá trị gì. Năm ca chỉ khẳng định `main() == 1`, nên chúng xanh cả khi phép
kiểm mà chúng tồn tại để canh đã bị gỡ bỏ — M7 chứng minh bằng máy: nới `>= 2` thành `>= -10` mà
**không ca nào đỏ**.

Hậu quả thật, không phải chuyện hình thức: `so_buoc_nguong` quyết định độ mịn của lưới quét ngưỡng,
và ngưỡng chốt ở bước 3.7c đọc thẳng từ lưới đó. Một ngày nào đó ai đó sửa điều kiện kiểm — hoặc
`configs/recognize.yaml` bị đặt `so_buoc_nguong: 2` — thì bảng ROC/DET rút xuống hai điểm, con số
`nguong_far_muc_tieu` trong `results/` sai hoàn toàn, mà toàn bộ 134 ca vẫn xanh và `ruff` vẫn sạch.
Đây đúng là chế độ hỏng "số liệu sai lặng lẽ" mà cả quy trình dựng ra để chặn.

**Sửa** — hai việc, đều trong tệp test, mã sản phẩm giữ nguyên:

1. Xoá `_main_voi_so_buoc`, cho năm ca đi qua `_dung_va_chay_co_ban` (đã dựng sẵn gallery + probe
   đầy đủ, và ca 116 đã chứng minh cùng bộ dựng đó trả `0` khi `so_buoc_nguong` hợp lệ). `_cfg_yaml`
   dùng `yaml.safe_dump` nên nhận thẳng `float("inf")`, `float("nan")`, `"abc"`, `2.5`, `1` mà không
   cần sửa hàm trợ giúp:

```python
def test_dong111_so_buoc_nguong_1(tmp_path, monkeypatch):
    kq = _dung_va_chay_co_ban(tmp_path, monkeypatch, so_buoc_nguong=1)
    assert kq["ma"] == 1
```

   và tương tự với `2.5`, `"abc"`, `float("inf")`, `float("nan")`.

2. Thêm **bằng chứng phân biệt** cho từng ca — một `capsys` khẳng định thông báo nêu đích danh khoá,
   theo đúng khuôn cặp `109a`/`109b` đã có sẵn trong tệp:

```python
    out = capsys.readouterr().out
    assert "so_buoc_nguong" in out
```

**Kiểm bản sửa**: chạy lại M7 (nới `>= 2` thành `>= -10`). Năm ca 111–115 **phải đỏ**. Chưa đỏ thì
bản sửa chưa đạt.

---

### 🟡 CẦN SỬA-2 — Ba ca 87/88/91 đối chiếu tệp kết quả với hằng số của chính module (CS-4)

**Vị trí**: `tests/test_benchmark_recognize.py:1378`, `:1387`, `:1406`.

```python
    assert header == br._COT_CSV_THO        # dòng 1378
    assert header == br._COT_CSV_NGUONG     # dòng 1387
    assert set(meta) >= set(br._KHOA_META_BAT_BUOC)   # dòng 1406
```

**Vì sao**: ba khẳng định này lấy kỳ vọng từ **chính đối tượng đang bị kiểm**, nên chúng đúng theo
định nghĩa. Đổi tên bất kỳ cột nào trong `_COT_CSV_THO` thì tệp CSV đổi header **và** kỳ vọng cũng
đổi theo — M8 chứng minh: đổi tên cột `top1_score` mà **không ca nào đỏ**.

Đây là mục nặng hơn CẦN SỬA-1, vì `results/*.csv` là **hợp đồng đọc** chứ không phải chi tiết nội
bộ: `notebooks/06_nguong_va_roc.ipynb` (bước 3.5) sẽ đọc cột `top1_score` để vẽ ROC/DET, Chương 4
§4.4 sẽ trích từ `.nguong.csv`, và bước 3.8 lập bảng so sánh hai backend từ cùng khuôn cột đó. Đổi
tên một cột làm hỏng mọi thứ đọc tệp — mà lỗi chỉ lộ ra khi notebook chạy, tức là ở Cổng D, sau khi
số đã vào báo cáo. Ba ca này tồn tại đúng để chặn điều đó và hiện không chặn được gì.

Ngoài ra đây là **lệch khỏi đặc tả**, không phải khoảng trống của đặc tả: §8 dòng 87 ghi *"So
`next(csv.reader(f))` với danh sách 14 tên **nguyên văn** §7.4"*, dòng 88 ghi tương tự cho 17 cột,
dòng 91 viết thẳng tập 23 khoá vào ô assert. Các ca 92–95 kề bên **đã** làm đúng cách đó (liệt kê
tập khoá nguyên văn), nên trong cùng một tệp đang tồn tại hai lối viết.

**Sửa**: thay ba khẳng định bằng danh sách/tập **nguyên văn**, chép từ §7.4 đặc tả — cùng lối viết
mà ca 92–95 đang dùng:

```python
    assert header == [
        "run_id", "backend", "tap", "user_id_that", "nhan", "anh_bam", "top1_user",
        "top1_score", "diem_dung_nguoi", "so_chieu", "latency_trich_ms",
        "latency_so_khop_ms", "latency_identify_ms", "cpu_temp_c",
    ]
```

tương tự 17 tên cho ca 88 và 23 khoá cho ca 91.

**Kiểm bản sửa**: chạy lại M8 (đổi tên `top1_score` trong `_COT_CSV_THO`). Ca 87 **phải đỏ**. Kèm
theo, đổi một tên trong `_COT_CSV_NGUONG` → ca 88 phải đỏ; bỏ một khoá khỏi `_KHOA_META_BAT_BUOC` →
ca 91 phải đỏ.

---

## 4. Khuyết tật của ĐẶC TẢ — không phải lỗi người cài đặt

Ba mục dưới đây **không** trả về cho người cài đặt. Chúng là việc của `spec-writer`.

### 4.1. §8 dòng 16 — ô assert không bắt được phép đột biến mà nó tồn tại để bắt

Đặc tả viết `chia_enroll_probe({"u1": ds}, 2, 42)[0]["u1"] == chia_enroll_probe({"u1": ds, "u9": ds9}, 2, 42)[0]["u1"]`
— đặt `"u1"` **trước** trong cả hai lượt gọi. Với một cài đặt dùng `random.Random(seed)` **chung**
cho cả lượt, `"u1"` vẫn luôn là người đầu tiên tiêu thụ trạng thái ngẫu nhiên, nên hai vế bằng nhau
và ô assert xanh.

Ba lượt chạy chốt điều này dứt điểm: **M3** (dùng chung seed, ca 16 dạng của người cài đặt) → ca 16
**đỏ**. **M3b** (dùng chung seed, ca 16 quay về dạng chữ đặc tả) → **134 passed**, không ca nào đỏ.
**K1** (mã sản phẩm nguyên vẹn, ca 16 dạng đặc tả) → **134 passed**.

Đọc ba lượt cùng nhau: dạng chữ trong đặc tả **không** có hiệu lực phân biệt, dạng của người cài đặt
**có**, và K1 chứng minh bản sửa **không làm mất** phép kiểm nào (nếu nó siết quá tay, K1 đã đỏ).
Đây là **siết chốt**, đúng hướng. Người cài đặt còn ghi 5 dòng chú thích tại `:556-560` giải thích
chính xác vì sao phải đảo thứ tự — hành vi khai báo minh bạch, ghi nhận.

**Việc cho `spec-writer`**: sửa §8 dòng 16 thành dạng đảo thứ tự đã được kiểm chứng.

### 4.2. §8 dòng 111–115 — assert chỉ vào giá trị trả về của `main()`

Gốc rễ của 🟡 CẦN SỬA-1 nằm ở đây. Cả năm ô "Assert tối thiểu" chỉ ghi `main([...]) == 1`, trong khi
`main()` trả `1` từ **chín** chỗ khác nhau. Đây đúng là mục mà checklist của `spec-writer` đã cấm —
`.claude/agents/spec-writer.agent.md:285-287`:

> *Mỗi dòng có kết quả đến được bằng nhiều đường (`main()` trả cùng mã lỗi…) đã ghi rõ **tiền đề** và
> assert vào **bằng chứng phân biệt**, không chỉ vào giá trị trả về.*

Các dòng 107a/b, 109a/b, 110a/b, 41a/b, 42a/b, 46a/b **đã** làm đúng (mỗi ca "a" kèm một ca "b" soi
thông báo). Riêng 111–115 bị bỏ sót. **Việc cho `spec-writer`**: bổ sung ô "tiền đề" (cấu hình phải
hợp lệ ở mọi khoá khác) và thêm dòng `111b`–`115b` soi thông báo.

⚠️ Nhận xét quy trình: 4.1 và 4.2 là **cùng một hình dạng lỗi** — ô assert được viết ra mà không thử
xem một cài đặt sai có trượt nó không. Nó đã tái phạm ở `P1-01` và `P1-02` (checklist dòng 288–291
ghi lại), nay tái phạm lần thứ ba dưới dạng khác. Đề xuất bổ sung một dòng vào checklist
`spec-writer`: *với mỗi phép đột biến ở §10, chỉ đích danh ô assert nào sẽ đỏ, và tự hỏi ô đó có thể
xanh vì lý do khác không.*

### 4.3. §10 ĐB13 — phép đột biến không quan sát được về mặt toán học

Đặc tả §5.2 yêu cầu kiểm hữu hạn **bằng `math.isfinite`**, và §10 ĐB13 khẳng định bỏ nó đi thì ca
70/71/72 phải đỏ. Máy nói khác: **M9** (bỏ ở `chot_diem_can_bang:612`) và **M9b** (bỏ ở
`_doc_far_muc_tieu:764`) đều cho **134 passed**, và bảng biểu thức [20/20] cho **cả sáu** giá trị
`inf`, `-inf`, `nan`, `0.0`, `1.5`, `0.01` đều `GIONG NHAU`.

Lý do là số học chứ không phải lỗi test: phép kiểm miền `not (0 < x <= 1)` đã **bao trùm** cả ba giá
trị không hữu hạn — `0 < inf` đúng nhưng `inf <= 1` sai; `0 < -inf` sai; mọi phép so sánh với `nan`
đều sai. Nên ĐB13 **không thể** làm ca nào đỏ với bất kỳ bộ test nào, chừng nào phép kiểm miền còn
được viết như hiện tại.

**Phán quyết về mã: GIỮ NGUYÊN, không sửa.** Ba lý do:

1. §5.2 đặc tả **yêu cầu đích danh** `math.isfinite`; gỡ đi là lệch đặc tả.
2. Nó là phòng thủ theo tầng, không phải mã chết: ngày nào đó ai đó nới phép kiểm miền (bỏ cận trên
   `<= 1`, chẳng hạn khi có người muốn thử `far_muc_tieu` lớn hơn), `inf` sẽ lọt ngay nếu không còn
   `isfinite`. Chi phí giữ lại bằng không.
3. Nó tài liệu hoá **ý định** — và ý định ấy có lịch sử: `P3-01` đã từng liệt kê đủ `0`, số âm,
   chuỗi mà quên ba giá trị không hữu hạn.

**Việc cho `spec-writer`**: sửa §10 ĐB13 thành một phép quan sát được — ví dụ *"đổi `not (0 < x <= 1)`
thành `not (0 < x)`"*, phép này sẽ làm ca 70 và 74 đỏ và mới thật sự kiểm được người gác. Ghi kèm
một dòng cảnh báo cho các đặc tả sau: **trước khi viết một phép đột biến, kiểm xem nó có bị một phép
kiểm khác bao trùm không.**

---

## 5. Bốn quyết định người cài đặt tự chốt — phán định

### 5.1. Mốc tính `so_danh_tinh_impostor` — ✅ chấp nhận

`benchmark_recognize.py:1090` đếm trên `ban_ghi`, tức các probe **thật sự đo được**, sau cả phép lọc
theo `--danh-sach-impostor` lẫn phép bỏ ảnh hỏng. Đặc tả §7.4 liệt kê khoá này nhưng không định mốc.

Chấp nhận, vì nó **nhất quán với `bam_danh_sach_anh_probe`** (cũng tính trên ảnh đo được, §4.5) và
vì nó là con số người đọc cần để diễn giải FAR: mẫu số của FAR là số probe impostor đo được, nên số
danh tính đi kèm phải cùng một mốc. Lấy mốc "số dòng trong tệp danh sách" sẽ tạo ra một cặp số lệch
nhau trong cùng một `.meta.json` mà không ai giải thích được.

🔵 kèm theo: meta **không** ghi số danh tính được **yêu cầu** trong `--danh-sach-impostor`. Nếu toàn
bộ ảnh của một danh tính impostor hỏng, danh tính đó biến mất khỏi phép đo và dấu hiệu duy nhất là
`so_anh_bo_qua`. Đề xuất thêm khoá `so_danh_tinh_impostor_yeu_cau` ở mã việc sau — **không chặn**.

### 5.2. Dạng lưu `tep_ket_qua` — ✅ chấp nhận, kèm một góp ý

`:1229` lưu ba **tên tệp trần** (`<run_id>.csv`, `.nguong.csv`, `.meta.json`), không kèm tiền tố
`results/`. §7.4 chỉ ghi *"đường dẫn tương đối của ba tệp"* mà không nói tương đối với cái gì — ô
này của đặc tả mơ hồ, nên diễn giải của người cài đặt là hợp lệ.

Chấp nhận vì nó **tự nhất quán**: cả ba tệp nằm cùng thư mục với `.meta.json`, nên tên trần là đường
dẫn tương đối đúng nghĩa và không phụ thuộc chỗ đặt `results/`. Cách này cũng sống sót khi
`_THU_MUC_KET_QUA_MAC_DINH` bị `monkeypatch` — điều mà tiền tố cứng `results/` sẽ làm sai.

🔵 Góp ý: khi Chương 4 trích nguồn theo R6, dạng `results/bench_recognize_dlib_....csv` tiện hơn.
Nên chốt dứt khoát trong đặc tả sau, chọn một trong hai và ghi rõ "tương đối với gốc kho" hay "tương
đối với chính tệp meta". **Không chặn.**

### 5.3. Dùng cả `logger.error` lẫn `print` — ✅ **chấp nhận tiền lệ, và chốt thành quy tắc toàn dự án**

Đã đối chiếu hai script đã qua review: `scripts/enroll.py:479-480, 488-489, 495-496, 513-514,
527-528, 544-545, 616-617, 621-622` và `scripts/benchmark_detect.py:476-477, 484-485, 492-493,
499-500, 528-529, 540-541, 553-554, 594-595, 674-675` — cả hai đều ghép cặp `logger.error(...)` +
`print(...)` ở **mọi** nhánh thoát lỗi của `main()`. `P3-05` theo đúng khuôn đó.

**Phán quyết cho toàn dự án — chốt tại đây, các mã việc sau chiếu theo:**

| Nơi | `print` | `logger` |
|---|---|---|
| `src/**` | ❌ **cấm tuyệt đối** (G2 / R23 / CA-2) | ✅ bắt buộc, lazy formatting |
| `scripts/**` — nhánh thoát lỗi của `main()` | ✅ **bắt buộc** | ✅ **bắt buộc**, mức `error` |
| `scripts/**` — bảng tóm tắt / kế hoạch `--dry-run` | ✅ bắt buộc | không cần |

Lý do giữ cả hai, chứ không phải "cho tiện": `print` là **giao diện của công cụ dòng lệnh** — người
dùng chạy `scripts/*.py` phải thấy lý do hỏng ngay trên terminal, không phải đi tìm tệp log; và
chính đặc tả §8 buộc phải như vậy, vì bảy ô assert (36b, 41b, 42b, 46b, 107b, 109b, 110b) soi
`capsys.readouterr().out`. Còn `logger.error` để lại vết cho lượt chạy không có người ngồi xem —
đúng thứ cần khi `results/` sinh ra lúc nửa đêm trên Pi 5. Bỏ một trong hai là mất một trong hai
công dụng. **Không siết lại.**

### 5.4. Dựng ca 34/35 bằng hai thư mục vật lý — ✅ chấp nhận, và đây là lựa chọn đúng

`tests/test_benchmark_recognize.py:814-894` dựng `<gốc>/enroll/<uid>/` và `<gốc>/probe/<uid>/` tách
biệt, rồi `shutil.copyfile` một ảnh sang thư mục probe — ca 34 **giữ nguyên tên**, ca 35 **đổi tên**.

Chấp nhận, vì hai lý do:

1. Nó **mô hình hoá đúng tình huống thật** mà §4.1 mô tả: khi có gallery người nhà, thư mục enroll
   và thư mục test là hai thư mục khác nhau. Dựng cả hai trong một thư mục sẽ kiểm một bài toán
   khác.
2. Nó **có hiệu lực phân biệt, đã chứng minh bằng máy**: M1 (loại theo đường dẫn tương đối) làm
   **đúng** ca 35 đỏ và để ca 34 xanh — khớp từng chữ với dự đoán ở §8.4 và §10 ĐB2 của đặc tả. Cặp
   ca này là thứ đắt giá nhất trong cả 134 ca.

---

## 6. Kích thước mã việc — bài học quy trình

| | |
|---|---|
| Mốc quy ước | **400 dòng** — `.claude/agents/spec-writer.agent.md:38`: *"Quá 400 dòng code dự kiến → tách thành 2 mã việc"* |
| Đặc tả ước lượng | ~600 (script) + ~750 (test) = **1350** |
| Thực tế | 1284 + 1789 = **3073** — gấp **2,28 lần** ước tính của chính đặc tả, gấp **7,7 lần** mốc quy ước |

`spec-writer` đã cân nhắc và chọn **không tách**, lý do ghi ở §2 đặc tả: *"tách đôi sẽ cắt ngang một
luồng dữ liệu duy nhất (ảnh → điểm số → bảng ngưỡng → tệp kết quả) và sinh ra một interface trung
gian chỉ dùng một lần"*.

**Quyết định đó đứng vững một nửa, và số liệu chỉ rõ nửa nào.**

Nửa đứng vững: mọi chốt thuộc **luồng dữ liệu chính** đều sống sót đột biến — M1, M2 (loại theo mã
băm nội dung), M3 (seed theo từng người), M4 (open-set), M5 (băm trên ảnh đo được), M6 (từ chối ghi
đè). Sáu trên sáu. Nếu tách ngang luồng này, mỗi mảnh sẽ phải dựng lại một nửa ngữ cảnh và cặp ca
34/35 — phép kiểm giá trị nhất của cả mã việc — sẽ **không dựng được** ở mảnh nào cả. Lập luận của
`spec-writer` đúng **trên trục pipeline**.

Nửa không đứng vững: **cả hai khuyết tật tìm được đều nằm ở rìa**, không ở lõi — M7 ở tầng đọc và
kiểm cấu hình CLI, M8 ở tầng ghi tệp và siêu dữ liệu. Đó không phải trùng hợp. Hai tầng ấy có 46
trên 134 ca (§8.9 dòng 83–106 và §8.10 dòng 107–128), nằm ở cuối một tệp test 1789 dòng, và là nơi
sự chú ý mỏng nhất khi cả người viết lẫn người đọc đã đi qua 1300 dòng trước đó.

**Chỗ đáng lẽ nên tách — theo trục tầng, không theo trục pipeline:**

| Mã việc giả định | Nội dung | Ca |
|---|---|---|
| `P3-05a` — đo và quét | §4.1–§4.5, §7.1–§7.3, §8.1–§8.8 | dòng 01–82 |
| `P3-05b` — ghi kết quả và CLI | §5.1–§5.2, §7.4–§7.5, §8.9–§8.10 | dòng 83–128 |

Phép tách này **không** cắt ngang luồng dữ liệu và **không** sinh interface dùng một lần: mặt cắt
chính là `ghi_ket_qua(thu_muc, run_id, ban_ghi, bang_nguong, meta)` — một chữ ký **đã có sẵn** trong
§6 đặc tả, đã được thiết kế như một ranh giới, và có bộ ca riêng biệt hoàn toàn. Nói cách khác:
`spec-writer` lập luận đúng về phương án tách mà mình xét, nhưng **chỉ xét một phương án**.

**Bài học ghi cho các mã việc sau**: khi một đặc tả vượt mốc 400 dòng và định viện lý do "không tách
được", phải nêu rõ **đã xét những mặt cắt nào**. Mặt cắt theo *tầng* (đo ↔ ghi ↔ CLI) hầu như luôn
tồn tại và thường rẻ hơn mặt cắt theo *pipeline*. Dấu hiệu nhận biết: nếu §6 đã có một hàm nhận trọn
kết quả của phần trước và không trả gì về, đó chính là mặt cắt.

---

## 7. 🔵 Góp ý — không chặn, người dùng quyết định

- **`--enroll-moi-nguoi 0` cho traceback thay vì thông báo.** `:1004` gọi `chia_enroll_probe` **không
  bọc `try`**, trong khi hàm này ném `LoiCauHinh` khi `so_anh_enroll < 1` (`:375-376`). Ngoại lệ
  thoát khỏi `main()`, người dùng thấy stack trace thay vì một câu tiếng Việt, và hợp đồng "trả 0
  hoặc 1" của §6 bị phá. Đường này **có thật** vì §12b dùng `--enroll-moi-nguoi 2`, gõ nhầm thành `0`
  là chuyện thường. Đặc tả §8 không có dòng nào cho ca này nên **không trả lại**; đề xuất bọc `try`
  cùng khuôn 9 nhánh còn lại ở mã việc sau. Chi phí: 5 dòng.
- **Thông báo có thể chỉ sai chỗ khi chế độ `chia` không ai đủ ảnh.** Nếu mọi người có ≤ K ảnh,
  gallery rỗng, và `main()` dừng ở chốt `:1053` với câu *"Không còn probe genuine nào sau khi loại
  ảnh đã dùng đăng ký"* — đúng về mặt kết quả nhưng chỉ sai nguyên nhân (thật ra là không ai đủ ảnh
  để đăng ký). Không nguy hiểm, chỉ tốn thời gian chẩn đoán. Chi phí sửa: một nhánh kiểm `if not
  gallery` riêng.
- **Ca 36b (`"genuine" in out`) yếu hơn vẻ ngoài.** Bảng tóm tắt lúc chạy **thành công** cũng chứa
  chữ `genuine` (dòng `Probe genuine       :`), nên ô assert này xanh ở cả hai kết cục; nó chỉ có
  hiệu lực nhờ đi cặp với 36a. Nhận định này rút ra từ **đọc mã**, `[CHƯA DỰNG LẠI]` bằng đột biến —
  vòng 2 nên chạy ĐB7 (bỏ riêng chốt `:1052-1060`, giữ nguyên phần còn lại) để chốt dứt điểm ca nào
  thật sự canh nó.
- **`so_danh_tinh_impostor_yeu_cau`** — xem §5.1.
- **Dạng `tep_ket_qua`** — xem §5.2.

---

## 8. Việc tiếp theo

**Phán quyết: 🔴 TRẢ LẠI — vòng 1.** Không mục 🔴. Hai mục 🟡, **cả hai nằm trong
`tests/test_benchmark_recognize.py`**; `scripts/benchmark_recognize.py` **không phải sửa dòng nào**.
Ước lượng khối lượng sửa: khoảng 40 dòng test, không đụng mã sản phẩm, không đụng `configs/`.

Bàn giao cho `coder` (Nhịp 4, cùng nhánh `feat/p3-05-benchmark-recognize`, **không commit**):

1. Sửa **🟡 CẦN SỬA-1** theo §3 — bỏ `_main_voi_so_buoc`, đưa ca 111–115 qua `_dung_va_chay_co_ban`,
   thêm khẳng định `capsys` nêu đích danh `so_buoc_nguong`.
2. Sửa **🟡 CẦN SỬA-2** theo §3 — thay ba khẳng định tự tham chiếu ở `:1378`, `:1387`, `:1406` bằng
   danh sách tên nguyên văn chép từ §7.4 đặc tả.
3. Chạy lại §9 đặc tả trên host **và** trong `faceid:arm64`. Kỳ vọng: **134 passed** ở tệp mới,
   **689 passed** toàn kho trên `pc_x86` không lọc marker, **656 passed / 1 skipped / 32 deselected**
   trong container với `-m "not slow"`. Số ca **không được đổi** — hai bản sửa chỉ siết assert, không
   thêm không bớt ca.
4. **Chạy lại M7 và M8 và dán kết quả về**: M7 phải làm ca 111–115 đỏ; M8 phải làm ca 87 đỏ. Đây là
   tiêu chí nghiệm thu của chính bản sửa — bản sửa nào không làm hai phép này đỏ thì chưa đạt.
5. Không sửa `scripts/benchmark_recognize.py`. Không sửa `docs/`, `configs/`.

Việc song song cho `spec-writer` (commit riêng, loại `docs(dac-ta)`, **không** trộn vào commit của
mã việc): sửa ba khuyết tật đặc tả ở §4 — dòng 16, dòng 111–115, và ĐB13; kèm bổ sung một dòng vào
checklist theo đề xuất cuối §4.2.

Vòng 2 sẽ kiểm: hai bản sửa, hai phép đột biến nghiệm thu, và **bảy phép đột biến `[CHƯA DỰNG LẠI]`**
của §1.5 (ĐB3, ĐB4, ĐB5, ĐB6, ĐB7, ĐB8, ĐB9, ĐB10).

---
---

# Review P3-05-benchmark-recognize — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-05-benchmark-recognize.md` (nội dung **không đổi** so với vòng 1) |
| **Nhánh** | `feat/p3-05-benchmark-recognize`, đỉnh `2571ea9` (commit biên bản vòng 1), điểm rẽ nhánh `dev` tại `bf6d870` |
| **Mã được kiểm** | bản sửa **chưa commit** trên cây làm việc: `tests/test_benchmark_recognize.py`, **+88 / −33**. `scripts/benchmark_recognize.py` **không đụng dòng nào** |
| **Ngày** | 2026-09-08 |
| **Phán quyết** | ✅ **ĐẠT** — **0 mục 🔴**, **0 mục 🟡**. Hai mục 🟡 của vòng 1 đã đóng, có bằng chứng máy đích danh. Còn 5 mục 🔵 và ba khuyết tật đặc tả — chuyển thành mã việc riêng, không chặn commit |

Người dùng đã chốt **vòng 2 là vòng cuối**. Biên bản này vì vậy phân định dứt khoát từng mục tồn
đọng: mục nào đã đóng, mục nào chuyển đi đâu, và **phạm vi hiệu lực** của bằng chứng đến đâu.

Ba điều đáng ghi của vòng này:

1. **Hai phép đột biến từng câm ở vòng 1 nay cắn đích danh** — M7 làm `test_dong111` đỏ, M8 làm
   `test_dong87` đỏ. Đây là tiêu chí nghiệm thu của chính bản sửa, và nó đạt.
2. **Không phép kiểm nào bị mất trong lúc sửa.** Mười hai phép đột biến của vòng 1 được dựng lại
   nguyên vẹn, không phép nào chuyển từ đỏ sang xanh; số ca giữ đúng 134 ở cả hai môi trường.
3. **Một bài học phương pháp mới, có đối chứng**: phép đột biến M8c0 cho `134 passed` **không** phải
   vì chốt hỏng mà vì phép đột biến ấy **không quan sát được theo thiết kế**. Cách phân biệt hai
   trường hợp là dựng phép đối chứng — xem §2.4.3.

---

## 1. Kết quả kiểm máy — vòng 2

**Người dùng chạy ngày 2026-09-08.** Đánh số nối tiếp vòng 1: `[21/38]`–`[38/38]`. Mỗi ô truy được
về một đoạn trong khối kết quả người dùng dán về. Ô nào chưa có lượt chạy ghi rõ `[CHƯA DỰNG LẠI]`.

### 1.1. Phạm vi tệp

| # | Lệnh | Kết quả |
|---|---|---|
| [21/38] | `git status --short --untracked-files=all` | **bốn dòng** — một trong danh sách trắng, ba ngoài mã việc (giải trình dưới) ⚠️ |
| [22/38] | `git diff --stat` | `1 file changed, 88 insertions(+), 33 deletions(-)` ✅ |
| [23/38] | `git diff --stat dev...HEAD` | **ba tệp**, 3624 thêm, **0 xoá** ✅ |
| [24/38] | lọc `\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$` trên danh sách tệp thay đổi | **rỗng** ✅ |

[22/38] chốt điều quan trọng nhất về phạm vi: **đúng một tệp** trên cây làm việc bị sửa, và nó nằm
trong danh sách trắng §2 đặc tả. `scripts/benchmark_recognize.py` không đổi — xem [26/38].

[23/38] so với `dev`: ba tệp = hai tệp mã việc (script 1283, test 1790) + biên bản vòng 1 (551), đúng
bằng `docs/review/` mà vai review được phép ghi. **0 xoá** trên toàn nhánh → không dòng nào của kho
bị gỡ, CB-6 tiếp tục bị loại trừ bằng số học.

⚠️ **Ba dòng ngoài mã việc trong [21/38]** — ghi nhận, **không tính vào phán quyết**:

| Tệp | Bản chất | Xử lý |
|---|---|---|
| `docs/dac-ta/P2-07-benchmark-detect-camera.md` | đặc tả của **mã việc khác** (bước 2.5, đường vào từ camera) | commit riêng theo mã việc đó |
| `results/bench_detect_20260907_2203.csv` | một lượt đo `pc_x86` rời | người dùng sẽ xoá |
| `results/bench_detect_20260907_2203.meta.json` | meta của lượt đo trên | người dùng sẽ xoá |

Đã đọc tệp meta để chắc rằng nếu người dùng đổi ý mà giữ lại thì nó **không** làm hỏng tính trung
thực số liệu: `moi_truong: "pc_x86"` (dòng 15), `git_dirty: false` (dòng 5), và `notes` (dòng 60)
mang sẵn câu cảnh báo *"phép đo chạy ở môi trường 'pc_x86', KHÔNG phải Raspberry Pi 5 thật… KHÔNG
dùng kết luận chỉ tiêu >= 10 FPS"*. Đúng chuẩn R8/R17. Nhưng nó thuộc mã việc đo khác, nên **không
được trộn vào commit của `P3-05`** (R29, quy tắc một commit một mã việc).

Hai tệp `results/` này **không** mâu thuẫn với [18/20] của vòng 1 (bộ test không ghi vào `results/`):
dấu thời gian `20260907_2203` là một lượt chạy có chủ đích của người dùng, không phải sản phẩm của
`pytest`.

### 1.2. Mã sản phẩm nguyên vẹn qua toàn bộ bộ đột biến

| # | Lệnh | Kết quả |
|---|---|---|
| [26/38] | `Get-FileHash -Algorithm SHA256 scripts/benchmark_recognize.py` — **trước** và **sau** mười tám phép đột biến | hai lần cùng cho `54d76293a61e7d465437ae515eecfae4d5368760ca103419495273aa76b0afde` ✅ |

Mọi phép đột biến đi đủ bốn bước *sao lưu ra ngoài repo → sửa → chạy → khôi phục và đối chiếu
`sha256`*; **mọi lượt khôi phục KHỚP**, và hai mã băm ở hai đầu bộ đột biến trùng khít. Không có
đường nào để một phép sửa lọt lại trong mã sản phẩm.

### 1.3. Bằng chứng: không ca kiểm thử nào bị mất trong vòng sửa

| # | Lệnh | Kết quả |
|---|---|---|
| [25/38] | `git diff \| Select-String "^[+-]def test_"` | **đúng mười dòng** — năm cặp `-`/`+` cùng tên `test_dong111`…`test_dong115` ✅ |

Mười dòng chia thành năm cặp, mỗi cặp cùng tên ca, chỉ khác danh sách tham số (thêm `monkeypatch`,
`capsys`). **Không tên ca nào chỉ xuất hiện ở dòng `-`** → không ca nào bị xoá, không ca nào bị đổi
tên để tránh né. Ba ca 87/88/91 không xuất hiện trong kết quả này vì chữ ký của chúng không đổi —
chỉ thân hàm đổi.

33 dòng bị xoá đã được đối chiếu với trích đoạn ở §3 vòng 1: đó là **toàn bộ thân hàm trợ giúp
`_main_voi_so_buoc`** (dòng 409–426 của bản cũ) cộng thân năm ca cũ. Hàm bị xoá chỉ dựng chuỗi YAML
và gọi `br.main(...)`, **không mang khẳng định nào** — xoá nó không làm mất phép kiểm.

### 1.4. Ba lệnh nền và bốn lượt kiểm thử

Mọi con số dưới đây ghi kèm **mốc, môi trường và bộ lọc marker**, theo quy ước ở
`.claude/agents/spec-writer.agent.md`.

| # | Lệnh | Môi trường · bộ lọc | Kết quả |
|---|---|---|---|
| [27/38] | `python -m black --check --line-length 100 scripts/benchmark_recognize.py tests/test_benchmark_recognize.py` | `pc_x86` | `2 files would be left unchanged` ✅ |
| [28/38] | `python -m ruff check scripts/benchmark_recognize.py tests/test_benchmark_recognize.py` | `pc_x86` | `All checks passed!` ✅ |
| [29/38] | `python -m pytest -q tests/test_benchmark_recognize.py` | `pc_x86` · không lọc marker | **134 passed**, 0 skipped ✅ |
| [30/38] | `python -m pytest -q` | `pc_x86` · không lọc marker | **689 passed**, 0 failed, 0 skipped ✅ |
| [31/38] | `python -m pytest -q --ignore=tests/test_benchmark_recognize.py` | `pc_x86` · không lọc marker | **555 passed** ✅ |
| [32/38] | `python3 -m pytest -q -m "not slow"` trong `faceid:arm64` | `docker_arm64`, Python 3.11.16 · `-m "not slow"` | **656 passed, 1 skipped, 32 deselected** ✅ |
| [33/38] | `python3 -m pytest -q -m "not slow" tests/test_benchmark_recognize.py` trong `faceid:arm64` | `docker_arm64` · `-m "not slow"` | **134 passed**, 0 skipped, 0 deselected ✅ |
| [34/38] | `python3 -m pytest --collect-only -q tests/test_benchmark_recognize.py` trong `faceid:arm64` | `docker_arm64` | **134 tests collected**, không lỗi import ✅ |

Bốn phép đối chiếu số học, cả bốn đều khép kín:

- 689 − 134 = **555** = mốc của `dev` tại `bf6d870` (`pc_x86`, không lọc marker). [31/38] đo trực
  tiếp con số đó, không suy từ tổng → bản sửa **không** chạm ca cũ nào.
- 656 + 1 + 32 = **689** = tổng thu thập trên host. Hai môi trường cùng một tập ca.
- 656 − 522 = **134** = số ca mới, đúng bằng số trên host (mốc `dev` `docker_arm64` với
  `-m "not slow"` là **522 passed, 1 skipped, 32 deselected**).
- `deselected` giữ **32**, `skipped` giữ **1** → **không ca mới nào mang `@pytest.mark.slow`**,
  không ca mới nào có người gác `skip`. Đúng §3.4 và câu chốt cuối §8 đặc tả.

134 giữ nguyên so với vòng 1 ở **cả ba** phép đếm ([29/38], [33/38], [34/38]): hai bản sửa chỉ siết
khẳng định, **không thêm không bớt ca** — đúng yêu cầu 3 của §8 vòng 1.

⚠️ **`pi5` `[CHƯA CHẠY]`** cho mã việc này. Không phải khuyết tật: đặc tả §9 không yêu cầu, và §3.4
đã chốt rằng không ca nào cần `models/`/`data/`. Ghi ra để bảng ba môi trường của
`04_so_sanh_moi_truong.ipynb` không bị hiểu nhầm là đã có cột `pi5` cho tệp test này.

### 1.5. Hai phép quét chốt

| # | Lệnh | Kết quả |
|---|---|---|
| [35/38] | `Select-String "br\._COT_CSV_THO\|br\._COT_CSV_NGUONG\|br\._KHOA_META_BAT_BUOC\|_main_voi_so_buoc" tests/test_benchmark_recognize.py` | **rỗng** ✅ |
| [36/38] | `Select-String "assert True\|pytest\.mark\.slow\|xfail\|skipif" tests/test_benchmark_recognize.py` | **rỗng** ✅ |

[35/38] là chốt của 🟡 CẦN SỬA-2: không còn khẳng định tự tham chiếu nào, và hàm trợ giúp hỏng đã
biến mất hoàn toàn khỏi tệp.

**Người review kiểm thêm bằng một phép quét rộng hơn, đọc trực tiếp trên cây làm việc**: mẫu
`br\.[_A-Z]` trên `tests/test_benchmark_recognize.py` cho **không kết quả nào**. Nghĩa là tệp test
**không tham chiếu bất kỳ hằng số nào** của module đang bị kiểm — mạnh hơn [35/38] vốn chỉ soi ba
tên cụ thể. Chế độ hỏng "kỳ vọng lấy từ chính đối tượng bị kiểm" bị loại trừ trên toàn tệp, không
chỉ ở ba dòng đã sửa.

[36/38] chốt rằng không ca nào bị vô hiệu hoá bằng `xfail`/`skipif` để đi qua — chế độ hỏng CB-6
biến tướng.

### 1.6. Mười tám phép đột biến

| # | Lệnh chạy cho **mỗi** phép | |
|---|---|---|
| [37/38] | `python -m pytest -q tests/test_benchmark_recognize.py` sau khi sửa, rồi khôi phục và đối chiếu `sha256` | môi trường `pc_x86`, không lọc marker |

Lượt đối chứng chưa đột biến: **134 passed**, 0 ca đỏ.

| Mã | Phép đột biến | Ánh xạ §10 | Kết quả | Ca đỏ | Vòng 1 | Kết luận |
|---|---|---|---|---|---|---|
| M1 | loại theo đường dẫn tương đối thay vì mã băm nội dung | **ĐB2** | 1 failed | `test_dong35` — **ca 34 vẫn xanh** | như cũ | ✅ |
| M2 | bỏ hẳn phép loại ảnh đã đăng ký | ĐB1 | 4 failed | 34, 35, 36a, 37 | như cũ | ✅ |
| M3 | một `random.Random(seed)` dùng chung | ĐB11 | 1 failed | `test_dong16` | như cũ | ✅ |
| M3b | M3 + ca 16 quay về dạng chữ đặc tả | ĐB11 | 134 passed | — | như cũ | ⚠️ khuyết tật đặc tả §4.1 vòng 1 |
| K1 | chỉ đổi ca 16 về dạng chữ đặc tả, mã sản phẩm nguyên vẹn | — | 134 passed | — | như cũ | ✅ đối chứng |
| M4 | bỏ tính open-set, impostor luôn được chấp nhận | ngoài §10 | 2 failed | 55, 58 | như cũ | ✅ |
| M5 | băm trên danh sách ứng viên thay vì ảnh đo được | ĐB14 | 1 failed | `test_dong98` | như cũ | ✅ |
| M6 | bỏ chốt từ chối ghi đè | ĐB12 | 2 failed | 104, 105 | như cũ | ✅ |
| **M7** | nới `so_buoc_nguong >= 2` thành `>= -10` | ngoài §10 | **1 failed** | **`test_dong111`** | **134 passed** | ✅ **CẦN SỬA-1 đã đóng** |
| **M7b** | nới **cả hai** người gác của `_doc_so_buoc_nguong` | ngoài §10 | **5 failed** | **111, 112, 113, 114, 115** | — (mới) | ✅ |
| **M8** | đổi tên cột `top1_score` trong `_COT_CSV_THO` | ngoài §10 | **1 failed** | **`test_dong87`** | **134 passed** | ✅ **CẦN SỬA-2 đã đóng** |
| **M8b** | đổi một tên cột trong `_COT_CSV_NGUONG` | ngoài §10 | **1 failed** | **`test_dong88`** | — (mới) | ✅ |
| **M8c** | một khoá bắt buộc **vắng mặt** trong meta được ghi ra | ngoài §10 | **1 failed** | **`test_dong91`** | — (mới) | ✅ |
| **M8c0** | chỉ bỏ khoá khỏi hằng số `_KHOA_META_BAT_BUOC` | ngoài §10 | **134 passed** | — | — (mới) | ✅ đối chứng — xem §2.4.3 |
| **M8d** | hoán vị hai cột trong `_COT_CSV_THO` | ngoài §10 | **1 failed** | **`test_dong87`** | — (mới) | ✅ canh cả thứ tự |
| **M10** | đổi điều kiện chấp nhận `top1_score >= t` | **ĐB4** | **7 failed** | 55, 56, 57, 59, 60, **61a**, **61b** | `[CHƯA DỰNG LẠI]` | ✅ đã kiểm |
| M9 | bỏ `math.isfinite` ở `chot_diem_can_bang` | ĐB13 | 134 passed | — | như cũ | ⚠️ khuyết tật đặc tả §4.3 vòng 1 |
| M9b | bỏ `math.isfinite` ở `_doc_far_muc_tieu` | ĐB13 | 134 passed | — | như cũ | ⚠️ khuyết tật đặc tả §4.3 vòng 1 |

| # | Lệnh | Kết quả |
|---|---|---|
| [38/38] | bảng kiểm biểu thức `not (0 < x <= 1)` có/không `math.isfinite`, với `inf`, `-inf`, `nan`, `0.0`, `1.5`, `0.01` | **cả sáu in `GIONG NHAU`** ✅ |

---

## 2. Năm việc phán định

### 2.1. Hai lỗi 🟡 của vòng 1 — **ĐÃ ĐÓNG**

**🟡 CẦN SỬA-1 → đóng.** Ba bằng chứng độc lập:

1. **Máy**: M7 chuyển từ `134 passed` (vòng 1) sang `1 failed` — `test_dong111` đỏ. Tiêu chí nghiệm
   thu ở §8 vòng 1 điểm 4 đạt.
2. **Đọc mã**: `tests/test_benchmark_recognize.py:1692-1724`, năm ca nay đi qua
   `_dung_va_chay_co_ban` — bộ dựng đầy đủ gallery + probe, cùng bộ mà ca 116 dùng để chứng minh
   `main()` trả `0` khi `so_buoc_nguong` hợp lệ. Tiền đề "cấu hình hợp lệ ở mọi khoá khác" nay có
   thật: `_cfg_yaml` (`:181-189`) ghi đủ `backend`, `enroll.gallery_dir`, `enroll.min_images_per_user`,
   nên đường thoát `1` qua `lay_gia_tri(cfg, "enroll.gallery_dir")` ở `benchmark_recognize.py:929`
   **không còn tồn tại** cho năm ca này.
3. **Bằng chứng phân biệt**: mỗi ca thêm `assert "so_buoc_nguong" in out` trên `capsys`, đúng khuôn
   cặp `109a`/`109b`. Đây mới là thứ làm ca đỏ dưới M7 — xem §2.4.1.

**🟡 CẦN SỬA-2 → đóng.** Ba bằng chứng:

1. **Máy**: M8 chuyển từ `134 passed` sang `1 failed` (`test_dong87`); M8b làm ca 88 đỏ; M8c làm ca
   91 đỏ. Đủ ba phép kiểm bản sửa mà §3 vòng 1 đòi.
2. **Đọc mã**: `:1352-1374` (14 tên), `:1377-1402` (17 tên), `:1418-1446` (23 khoá) nay là **danh
   sách và tập nguyên văn**, chép từ §7.4 đặc tả, mỗi chỗ kèm một dòng chú thích nêu rõ *"không tham
   chiếu hằng số của module đang bị kiểm"*. Lối viết nay thống nhất với ca 92–95 kề bên.
3. **Quét**: [35/38] rỗng, và phép quét rộng `br\.[_A-Z]` của người review cũng rỗng trên toàn tệp.

Hợp đồng đọc của `results/*.csv` — thứ mà `notebooks/06_nguong_va_roc.ipynb` và Chương 4 §4.4 sẽ dựa
vào — nay **thật sự** được canh.

### 2.2. Bản sửa có làm mất phép kiểm nào không — **KHÔNG**

Ba lớp bằng chứng, đọc cùng nhau:

- **Mười hai phép đột biến của vòng 1 được dựng lại nguyên vẹn** (M1–M6, M3b, K1, M9, M9b + M7, M8).
  **Không phép nào chuyển từ đỏ sang xanh**; ca đỏ của từng phép trùng khít vòng 1, kể cả chi tiết
  "M1 làm ca 35 đỏ nhưng ca 34 vẫn xanh". Chốt chịu lực nhất của mã việc (§4.1 đặc tả) vẫn đứng.
- **[25/38]**: mười dòng `def test_`, năm cặp cùng tên, không tên nào chỉ có ở phía `-`.
- **[29/38] / [33/38] / [34/38]**: 134 ca, không đổi, ở cả hai môi trường; [31/38] cho 555 ca cũ
  không suy suyển.

Kết luận dứt khoát: bản sửa là **siết chốt thuần tuý**, không nới chỗ nào.

### 2.3. Kích thước và tính tự nhất quán của bản sửa

`git diff --stat` cho +88/−33 trên đúng một tệp, khớp với khối lượng dự trù ở §8 vòng 1 (*"khoảng 40
dòng test"* — thực tế lớn hơn vì ba danh sách nguyên văn 14 + 17 + 23 tên chiếm phần lớn số dòng
thêm). Không có thay đổi nào ngoài hai mục được yêu cầu: `scripts/benchmark_recognize.py` bất biến
theo `sha256` ([26/38]), `docs/` và `configs/` không bị đụng ([22/38]).

### 2.4. Ba giả thuyết nêu đầu vòng 2 — cả ba **được xác nhận bằng máy**, và cả ba đã được đối chiếu lại bằng đọc mã

#### 2.4.1. A1 — M7 chỉ nới **một** trong hai người gác, và ca 111 đỏ nhờ `capsys`

**Máy**: M7 → 1 ca đỏ (111). M7b → 5 ca đỏ (111–115).

**Đọc mã xác nhận cơ chế**, `scripts/benchmark_recognize.py:742-755`:

```python
    hop_le = (
        isinstance(gia_tri, int)
        and not isinstance(gia_tri, bool)
        and math.isfinite(gia_tri)
        and gia_tri >= 2
    )
```

Hai người gác độc lập. Bốn giá trị `2.5`, `"abc"`, `inf`, `nan` bị chặn ngay ở `isinstance(int)`,
nên nới `>= 2` **không thể** chạm tới ca 112–115. Chỉ `so_buoc_nguong = 1` (ca 111) đi qua được
người gác thứ nhất. Vì vậy **M7 làm đúng một ca đỏ là kết quả đúng**, không phải dấu hiệu bốn ca kia
còn yếu — và M7b, nới cả hai người gác, chứng minh điều đó bằng cách làm cả năm ca đỏ.

**Điểm tinh tế, và là lý do khẳng định `capsys` không phải trang trí**: dưới M7, `so_buoc_nguong = 1`
đi tiếp tới `quet_nguong` (`:539-540`), ném `LoiCauHinh("so_buoc phải >= 2, nhận 1")`, `main()` bắt ở
`:1137-1140` và **vẫn trả `1`**. Nghĩa là khẳng định `kq["ma"] == 1` của ca 111 **vẫn xanh dưới M7**.
Chuỗi in ra là `"Không quét được ngưỡng: so_buoc phải >= 2, nhận 1"` — **không chứa** `so_buoc_nguong`.
Thứ làm ca 111 đỏ là đúng dòng `assert "so_buoc_nguong" in out`.

Đây là minh hoạ sạch nhất cho quy tắc mà §4.2 vòng 1 trích từ checklist `spec-writer`: khi `main()`
trả cùng một mã lỗi từ nhiều đường, chỉ khẳng định vào **bằng chứng phân biệt** mới có hiệu lực.

#### 2.4.2. A3 — ca 87 canh cả **thứ tự cột**, không chỉ tập tên

**Máy**: M8d (hoán vị hai cột) → `test_dong87` đỏ.

**Đọc mã xác nhận**: `ghi_ket_qua` (`:723-727`) ghi header **thẳng từ** `_COT_CSV_THO`; ca 87
(`:1359-1374`) so bằng `assert header == [...]`, tức phép so **danh sách** — nhạy với thứ tự, khác
hẳn phép so tập hợp. Hoán vị hai cột đổi header và làm ca đỏ.

Điều này quan trọng vì §7.4 đặc tả chốt *"đúng thứ tự"*: một notebook đọc CSV theo chỉ số cột sẽ hỏng
im lặng nếu thứ tự trôi, và đó lại là kiểu hỏng chỉ lộ ra ở Cổng D.

#### 2.4.3. A2 — "bỏ khoá khỏi hằng số" là phép đột biến **không quan sát được theo thiết kế**

**Máy**: M8c0 (chỉ bỏ khoá khỏi hằng số `_KHOA_META_BAT_BUOC`) → **134 passed**. M8c (khoá thật sự
vắng mặt trong meta được ghi ra) → `test_dong91` **đỏ**.

**Đọc mã giải thích vì sao hai kết quả này không mâu thuẫn**: `_KHOA_META_BAT_BUOC` (`:119-143`) chỉ
được dùng ở **một** chỗ duy nhất trong cả tệp — `ghi_ket_qua:707`, để **kiểm** từ điển meta mà nơi
gọi truyền vào. Từ điển meta thật được dựng **bằng chữ** trong `main()` (`:~1195-1231`), không đọc
hằng số đó. Vậy nên gỡ một khoá khỏi hằng số **không thể** làm đổi nội dung tệp `.meta.json` được
ghi ra, và một ca test canh **tệp được ghi ra** — đúng thứ ca 91 nên canh — sẽ không bao giờ thấy
phép đột biến ấy.

⭐ **Bài học phương pháp, ghi lại để các vòng review sau dùng**: một phép đột biến **không cắn**
không đồng nghĩa với chốt hỏng. Có hai nguyên nhân khác nhau hẳn:

| Nguyên nhân | Dấu hiệu | Xử lý |
|---|---|---|
| Chốt hỏng | phép đột biến đổi **hành vi quan sát được** mà không ca nào đỏ | 🟡 sửa ca test — đúng M7, M8 của vòng 1 |
| Phép đột biến không quan sát được | phép đột biến **không** đổi hành vi quan sát được nào | không phải lỗi — sửa **phép đột biến**, đúng ĐB13 |

Cách phân biệt: **dựng phép đối chứng** đổi thẳng thứ mà hợp đồng nói tới (M8c), rồi so với phép chỉ
đụng vào cấu trúc nội bộ (M8c0). Vòng 1 đã dùng đúng kỹ thuật này cho ĐB13 qua bảng biểu thức
[20/20]; vòng 2 dùng lại cho meta. Đề nghị đưa cặp M8c/M8c0 làm ví dụ mẫu trong
`.claude/instructions/code-review.instructions.md` — **🔵, người dùng quyết định.**

Hệ quả nhỏ còn lại, ghi thành 🔵 chứ không phải lỗi: hằng số `_KHOA_META_BAT_BUOC` hiện chỉ được canh
gián tiếp qua ca 102 (`meta={}` → `LoiCauHinh`). Nếu ai đó gỡ đúng một khoá khỏi hằng số, người gác
của `ghi_ket_qua` yếu đi mà không ca nào báo. Đây là **mất phòng thủ theo tầng**, không phải vỡ hợp
đồng đọc — tệp ghi ra vẫn đủ 23 khoá và ca 91 vẫn canh điều đó. Chi phí bịt: một ca dựng meta thiếu
**đúng một** khoá và đòi `LoiCauHinh`. §8 đặc tả không có dòng này nên **không trả lại**.

### 2.5. M10 = ĐB4 — chuyển từ `[CHƯA DỰNG LẠI]` sang **đã kiểm**

M10 đổi điều kiện chấp nhận `top1_score >= t` và làm **bảy** ca đỏ: 55, 56, 57, 59, 60, **61a**,
**61b**. §10 ĐB4 chỉ đòi ca 61 đỏ; kết quả thực tế là **tập cha** của yêu cầu đó, nên ĐB4 đạt.

Hai ca 61a/61b là phần đắt nhất trong nhóm: chúng canh đúng chỗ "điểm **bằng đúng** ngưỡng được tính
vào `tp`, **không** vào `fn`" — quy ước dấu bằng mà §7.2 chốt cứng. Đọc mã xác nhận cài đặt khớp:
`quet_nguong:555-561` dùng `>=` ở cả `tp` lẫn `fp_impostor`, `<` ở `fn` và `tn`.

⚠️ **Bảy phép còn lại vẫn `[CHƯA DỰNG LẠI]` — không ngụy trang thành đã phủ hết.**

| Trạng thái | Phép |
|---|---|
| Đã dựng lại độc lập (vòng 1 + vòng 2) | ĐB1 (M2) · ĐB2 (M1) · **ĐB4 (M10)** · ĐB11 (M3, M3b, K1) · ĐB12 (M6) · ĐB13 (M9, M9b, [38/38]) · ĐB14 (M5) — **7/14** |
| `[CHƯA DỰNG LẠI]` | **ĐB3 · ĐB5 · ĐB6 · ĐB7 · ĐB8 · ĐB9 · ĐB10** — **7/14** |
| Ngoài §10, do người review tự thiết kế | M4 · M7 · M7b · M8 · M8b · M8c · M8c0 · M8d — 8 phép |

Ghi chú về hai phép trong nhóm chưa dựng:

- **ĐB7** (bỏ riêng chốt "không còn probe genuine") mới chỉ được chạm **gián tiếp** qua M2 — M2 bỏ
  hẳn phép loại ảnh nên làm cả 34, 35, 36a, 37 đỏ cùng lúc, không tách được đóng góp của riêng chốt
  đó. Nghi vấn về ca 36b nêu ở §7 vòng 1 vì vậy **chưa được chốt dứt điểm**.
- **ĐB10** (tự tính vectơ trung bình thay vì gọi `backend.enroll` → ca 20) hiện chỉ có bằng chứng
  **tĩnh**: [16/20] vòng 1 cho đúng một dòng `.enroll(` thi hành trong `dung_gallery_trong_bo_nho`.
  Bằng chứng tĩnh không thay được phép đột biến.

Kết luận về phạm vi hiệu lực: bảy phép trên hiện **chỉ có lời khai của người cài đặt** (§13 điểm 3
đặc tả) cộng phép đọc mã của người review. Người dùng đã chốt không mở vòng 3, nên chúng **không**
chặn phán quyết — nhưng phải được ghi lại đúng như vậy để không ai đọc biên bản này rồi tưởng
`P3-05` đã qua đủ mười bốn phép đột biến độc lập.

### 2.6. Trạng thái từng mục 🔵 và ba khuyết tật đặc tả của vòng 1

**Ba khuyết tật đặc tả — vẫn MỞ.** Đã đọc `docs/dac-ta/P3-05-benchmark-recognize.md` trên cây làm
việc: §8 dòng 16 (`:586`) vẫn ở dạng đặt `"u1"` trước trong cả hai lượt gọi; §8 dòng 111–115
(`:734-738`) vẫn chỉ có ô `main([...]) == 1`, chưa có tiền đề và chưa có dòng `111b`–`115b`; §10
ĐB13 (`:869`) vẫn giữ nguyên văn cũ. [21/38] cũng xác nhận tệp đặc tả **không** nằm trong danh sách
tệp thay đổi.

Đây là việc của `spec-writer`, **không** chặn commit mã việc (R38 tách rõ hai vai). Ba mục chuyển
thành một commit riêng loại `docs(dac-ta)`, **không** trộn vào commit `P3-05`.

⭐ Riêng **ĐB13, chốt lại lần cuối**: **giữ nguyên mã, không sửa `math.isfinite`.** [38/38] tái xác
nhận cả sáu giá trị cho `GIONG NHAU`, nên ĐB13 là **phép đột biến thiết kế sai** — không quan sát
được về mặt toán học — chứ **không phải chốt hỏng. Ba lý do giữ mã đã ghi ở §4.3 vòng 1 vẫn nguyên
giá trị.** Nay cùng loại với M8c0 theo phân loại ở §2.4.3.

Ghi thêm một dữ kiện mới, để `spec-writer` sửa ĐB13 cho trọn: `math.isfinite` còn xuất hiện lần thứ
ba ở `_doc_so_buoc_nguong:748`, và ở đó nó **cũng** không quan sát được — vì đứng sau
`isinstance(gia_tri, int)`, mà số nguyên Python thì luôn hữu hạn. Cùng lập luận: giữ mã (đặc tả §5.2
yêu cầu đích danh, phòng thủ theo tầng, chi phí bằng không), sửa phép đột biến.

**Năm mục 🔵 của vòng 1 — trạng thái:**

| Mục 🔵 | Trạng thái sau vòng 2 | Đề xuất |
|---|---|---|
| `--enroll-moi-nguoi 0` cho traceback (`benchmark_recognize.py:1004` không bọc `try`) | **còn nguyên** — đã đọc lại mã, `chia_enroll_probe` vẫn gọi trần | mã việc dọn dẹp, ~5 dòng |
| Thông báo chỉ sai chỗ khi chế độ `chia` không ai đủ ảnh | **còn nguyên** | cùng mã việc trên, một nhánh `if not gallery` |
| Ca 36b yếu hơn vẻ ngoài | **chưa chốt** — ĐB7 dạng độc lập `[CHƯA DỰNG LẠI]`, xem §2.5 | dựng ĐB7 ở lượt kiểm sau |
| `so_danh_tinh_impostor_yeu_cau` thiếu trong meta | **còn nguyên** | mã việc sau, khi có tệp `data/splits/` thật |
| Dạng lưu `tep_ket_qua` (tên trần hay có tiền tố `results/`) | **còn nguyên** | chốt trong đặc tả kế tiếp có đụng `results/` |

Không mục nào trong năm mục này đổi trạng thái, vì chúng đều nằm trong `scripts/benchmark_recognize.py`
— tệp mà vòng 2 **cố ý không cho sửa**, và `sha256` [26/38] xác nhận đã không sửa.

---

## 3. Đối chiếu đặc tả — phần đổi so với vòng 1

Chỉ ghi những mục có thay đổi kết luận. Mọi mục khác giữ nguyên bảng §2.1 vòng 1.

| Mục | Vòng 1 | Vòng 2 |
|---|---|---|
| §5.2 Hai khoá cấu hình mới | ✅ mã đúng, **nhưng năm ca canh nó vô hiệu** | ✅ **đủ cả hai vế** — M7 và M7b làm 111–115 đỏ đích danh |
| §7.4 Ba tệp kết quả | ✅ mã đúng, **nhưng ba ca canh cột vô hiệu** | ✅ **đủ cả hai vế** — M8, M8b, M8c, M8d làm 87/88/91 đỏ đích danh |
| §8 Bảng nghiệm thu | ⚠️ 134/134 ca xanh, **8 ca không có hiệu lực phân biệt** | ✅ **134/134 ca xanh và 8 ca kia nay có hiệu lực**, chứng minh bằng sáu phép đột biến |
| §2 Danh sách trắng | ✅ hai tệp | ✅ vẫn hai tệp mã việc; ba tệp lạ trong `git status` thuộc mã việc khác, xem §1.1 |

Rủi ro ngoài đặc tả, soi lại trên bản sửa:

- **Trung thực số liệu (CA-7)**: bản sửa **tăng** mức bảo vệ — hợp đồng cột CSV và tập khoá meta nay
  được canh bằng danh sách nguyên văn, nên một lần đổi tên cột sẽ bị chặn **trước** khi số liệu đi
  vào notebook và Chương 4. Không có giá trị mặc định nào trông như kết quả đo được thêm vào.
- **An toàn phần cứng (CB-2)**: mã việc không chạm GPIO/relay/camera — không áp dụng, như vòng 1.
- **Test giả (CS-4)**: [36/38] rỗng; phép quét `br\.[_A-Z]` rỗng; không ca nào bị `xfail`/`skipif`.

🔵 nhỏ, ghi cho đủ, **không chặn**: chú thích kiểu của hai hàm trợ giúp test — `_cfg_yaml(...,
so_buoc_nguong: int = 10, ...)` (`:181`) và `_dung_va_chay_co_ban(..., so_buoc_nguong: int = 10,
...)` (`:202`) — khai `int` nhưng ca 112–115 truyền `2.5`, `"abc"`, `inf`, `nan`. Đây là hàm trợ giúp
riêng tư trong tệp test, `ruff` sạch, và việc truyền giá trị sai kiểu **chính là** mục đích của năm
ca đó. Nếu muốn chính xác, đổi thành `object`. Chi phí: hai dòng.

---

## 4. Phán quyết và việc tiếp theo

**Phán quyết: ✅ ĐẠT — vòng 2.**

| Điều kiện của ✅ ĐẠT | Kết quả |
|---|---|
| Không còn 🔴 | ✅ chưa từng có mục 🔴 nào ở cả hai vòng |
| Không còn 🟡 | ✅ hai mục của vòng 1 đã đóng, mỗi mục có phép đột biến nghiệm thu đích danh |
| Ba lệnh máy sạch/xanh | ✅ [27/38] `black` sạch · [28/38] `ruff` sạch · [30/38] **689 passed** trên `pc_x86`, [32/38] **656 passed / 1 skipped / 32 deselected** trong `faceid:arm64` |
| Mọi tiêu chí nghiệm thu §8 thoả | ✅ 134/134 ca có mặt và xanh ở cả hai môi trường, và tám ca từng vô hiệu nay có hiệu lực phân biệt |

**Phạm vi hiệu lực của phán quyết — đọc kèm, không tách rời:**

1. Bảy trên mười bốn phép đột biến §10 (ĐB3, ĐB5, ĐB6, ĐB7, ĐB8, ĐB9, ĐB10) **`[CHƯA DỰNG LẠI]`**
   độc lập; chúng dựa trên lời khai của người cài đặt cộng phép đọc mã. Xem §2.5.
2. Mã việc **chưa** chạy trên `pi5`; đặc tả không yêu cầu.
3. Con số do script này sinh ra vẫn là **số kiểm chức năng trên LFW**, không phải số báo cáo — §12b
   và §3.2 đặc tả đã chốt. Ngưỡng của bước 3.7c chỉ được chốt từ gallery người nhà đo trên Pi 5 thật.

**Việc tiếp theo cho người dùng, theo thứ tự:**

1. Xoá hai tệp `results/bench_detect_20260907_2203.*` như đã định, hoặc tách sang commit của mã việc
   đo tương ứng. Đưa `docs/dac-ta/P2-07-benchmark-detect-camera.md` sang commit riêng của mã việc đó.
2. Commit mã việc này — chỉ hai tệp `scripts/benchmark_recognize.py` và
   `tests/test_benchmark_recognize.py`, cộng `docs/review/P3-05-benchmark-recognize.review.md`:

   ```
   test(recognize): siết năm ca kiểm số bước quét ngưỡng và ba ca kiểm khuôn tệp kết quả — P3-05
   ```

   (Biên bản vòng 1 đã nằm trong `2571ea9`; commit này mang phần vòng 2.)
3. Chạy **§12b đặc tả** — bốn lệnh chạy thật, do người dùng chạy, sinh ba tệp
   `results/bench_recognize_{dlib,arcface}_*`. Nhắc lại kỳ vọng đã chốt: hai lệnh đầu trả `0`;
   lệnh thứ ba **phải hỏng** với mã `1` và không ghi tệp nào; lệnh `--dry-run` trả `0` và không ghi
   tệp nào.
4. Gộp `feat/p3-05-benchmark-recognize` vào `dev`. Mốc mới sau khi gộp: **689 ca** trên `pc_x86`
   không lọc marker; **656 passed / 1 skipped / 32 deselected** trên `docker_arm64` với
   `-m "not slow"`. Cập nhật §8 `CLAUDE.md`.

**Việc cho `spec-writer`** (commit riêng `docs(dac-ta)`, không trộn): ba khuyết tật đặc tả ở §4 vòng
1 vẫn mở — §8 dòng 16, §8 dòng 111–115, §10 ĐB13 (kèm dữ kiện mới về `_doc_so_buoc_nguong:748` ở
§2.6), và một dòng bổ sung cho checklist theo đề xuất cuối §4.2 vòng 1.

**Đề xuất một mã việc dọn dẹp** — gộp năm mục 🔵 còn tồn đọng, người dùng quyết định có làm hay
không, và làm ngay hay để sau bước 3.6:

| Nội dung | Chi phí ước tính |
|---|---|
| Bọc `try` cho `chia_enroll_probe` (`:1004`), thông báo tiếng Việt thay traceback | ~5 dòng |
| Nhánh `if not gallery` riêng để thông báo đúng nguyên nhân ở chế độ `chia` | ~5 dòng |
| Thêm khoá `so_danh_tinh_impostor_yeu_cau` vào `meta.dataset` | ~5 dòng + 1 ca |
| Chốt dạng lưu `tep_ket_qua` (tên trần hay tiền tố `results/`) | quyết định đặc tả |
| Một ca canh `_KHOA_META_BAT_BUOC` bằng meta thiếu đúng một khoá (§2.4.3) | ~8 dòng test |
| Dựng ĐB7 dạng độc lập để chốt dứt điểm ca 36b | phép đột biến, không sửa mã |

Mọi mục trên đều là 🔵 — **không mục nào chặn commit hay chặn bước 3.6**.
