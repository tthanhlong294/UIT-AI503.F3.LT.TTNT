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
