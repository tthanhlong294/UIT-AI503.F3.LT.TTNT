# Review P0-04-tuong-thich-pi-os — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P0-04-tuong-thich-pi-os.md` |
| **Nhánh** | `feat/p0-04-tuong-thich-pi-os`, commit `abf3207`, điểm rẽ nhánh `dev` tại `bfc9026` |
| **Mã được kiểm** | bảy tệp, +432/−26 (bảng §1.2) |
| **Ngày** | 2026-09-06 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — không mục 🔴, không mục 🟡. Bốn mục 🔵 và hai khuyết tật của **đặc tả** (không của mã). Được commit và gộp `dev` |

Toàn bộ số liệu dưới đây đến từ **lượt chạy của người dùng**, không dùng lại bảng tự kiểm của người
cài đặt. Mười hai phép đột biến được dựng lại từ đầu — nhiều hơn mười phép đặc tả §11 yêu cầu — và
mọi lượt khôi phục đều cho `sha256` **KHỚP**, không sót mã đột biến nào trong cây làm việc.

Ba điều làm lượt kiểm này khác mọi lượt trước trong dự án:

1. Đây là mã việc **đầu tiên mà lượt chạy trên Raspberry Pi 5 là bằng chứng duy nhất không thay thế
   được** — host (3.12.5) và container (3.11.16) đều có `tarfile.data_filter`, nên **không bao giờ**
   đi vào nhánh dự phòng trong điều kiện tự nhiên.
2. Ba môi trường độc lập cùng cho **555 ca thu thập** với ba cách phân bổ passed/skipped/deselected
   khác nhau — chính sự khác nhau ấy mới là thứ chứng minh các người gác `skip` hoạt động đúng.
3. Ba phép đột biến ngoài đặc tả (R10, R11, R12) trả lời dứt điểm câu hỏi "gộp ca phụ có làm mất
   chốt không" — xem §5.2.

---

## 1. Kết quả kiểm máy

### 1.1. Ba lệnh nền và bộ kiểm thử — host Windows, Python 3.12.5

| # | Lệnh | Kết quả |
|---|---|---|
| [1] | `black --check --line-length 100 src tests scripts` | `All done!` — **48 tệp không đổi** ✅ |
| [2] | `ruff check src tests scripts` | `All checks passed!` ✅ |
| [3] | `pytest -q` (không lọc marker) | **555 passed, 0 failed, 0 skipped**, 148,87 s ✅ |
| [4] | `pytest -q -m "not slow"` | **523 passed, 0 failed, 0 skipped, 32 deselected** ✅ |
| [5] | ba tệp test bị đụng, chạy riêng | **91 passed** = 40 + 47 + 4 ✅ |

[5] khớp từng tệp với dự đoán §9 đặc tả: `test_download_lfw.py` **40** (32 cũ + 8 mới 29–36),
`test_export_detector.py` **47** (45 cũ + 2 mới 43–44), `test_cau_hinh_pytest.py` **4** (45–48).
Tổng ca mới **14**, và 555 − 541 = 14 — số ca cũ không đổi một ca nào.

Mốc 541 là tổng ca của `dev` tại `bfc9026`, không phải 531 như đặc tả §9 ghi. Xem §5.1.

### 1.2. Phạm vi tệp — `git diff --numstat dev...HEAD` (phép so **ba chấm**)

| # | Tệp | Thêm | Bớt |
|---|---|---|---|
| [6] | `README.md` | 27 | 0 |
| | `pyproject.toml` | 4 | 0 |
| | `requirements-dev.txt` | 13 | 8 |
| | `scripts/download_lfw.py` | 50 | 11 |
| | `tests/test_cau_hinh_pytest.py` | 104 | 0 (tệp mới) |
| | `tests/test_download_lfw.py` | 163 | **0** |
| | `tests/test_export_detector.py` | 71 | 7 |

Đúng **bảy** tệp của danh sách trắng §2, không tệp thứ tám. `requirements.txt`, `deploy/`,
`configs/`, `src/`, `.claude/`, `CLAUDE.md` **không bị đụng** → không có lý do dựng lại
`faceid:arm64` (R43), và lượt container [7]–[8] chạy trên đúng image đang có.

⭐ Cột "Bớt = **0**" của `tests/test_download_lfw.py` là bằng chứng máy cho ràng buộc khó kiểm nhất
của §2 đặc tả — *"chỉ cộng ca mới 29–36, không xoá, không đổi ca 01–28"*. Không dòng nào bị xoá thì
không ca cũ nào bị sửa để đi qua (CB-6 loại trừ bằng số học, không bằng đọc mắt).

**R25 sạch**: toàn bộ thay đổi nằm trong bảy tệp `.py`/`.toml`/`.txt`/`.md`; không tệp nào có đuôi
`jpg|jpeg|png|npy|npz|onnx|pt|pth|env|db|sqlite3?`, không tệp nào trong `data/`, `models/`,
`results/`, `report/`, `docs/`.

### 1.3. Container `faceid:arm64`

| # | Lệnh | Kết quả |
|---|---|---|
| [7] | `python3 -VV` trong `faceid:arm64` | **Python 3.11.16** ✅ |
| [8] | `pytest -q -m "not slow"` trong `faceid:arm64` | **522 passed, 1 skipped, 32 deselected**, 642 s ✅ |

522 + 1 + 32 = **555**, khớp host. Một ca skip là ca 43 (`data/` bị `.dockerignore` loại) — đúng dự
đoán §9 đặc tả.

[7] là bằng chứng đắt giá của mã việc này, không phải một dòng thủ tục: **3.11.16 ≥ 3.11.4**, nên
container **luôn** chạy nhánh A. Ca 34–36 chạy được ở đây (không skip) xác nhận điều đó.

### 1.4. Raspberry Pi 5, Python 3.11.2, aarch64 — phần cứng đích

| # | Lệnh | Kết quả |
|---|---|---|
| [9] | `pytest tests/test_download_lfw.py -q` | **37 passed, 3 skipped, 0 failed** ✅ |
| [10] | `pytest -q -m "not slow"` | **518 passed, 5 skipped, 32 deselected, 0 failed** ✅ |
| [11] | cảnh báo `PytestUnknownMarkWarning` | **không còn dòng nào** ✅ |
| [12] | `du -sh .venv` | **420 MB** ✅ (trước khi dọn: ~2,9 GB) |

518 + 5 + 32 = **555**, khớp cả host lẫn container. **Bảy ca đỏ hai ngày liền ở §3.2 đặc tả nay
xanh** — Việc 1 nghiệm thu xong trên chính phần cứng sinh ra khuyết tật.

Ba ca skip ở [9] là ca 34, 35, 36 — đúng ba ca có người gác
`if not hasattr(tarfile, "data_filter"): pytest.skip(...)`. Đây là skip **đúng chỗ**, không phải né
việc: cả ba ca so hành vi *hai* nhánh, mà Python 3.11.2 chỉ có một nhánh để chạy. Năm ca skip ở [10]
= ba ca ấy cộng hai ca skip vốn có ở mốc `dev` (§3.1 đặc tả ghi `2 skipped`).

Ba con số 555 ở ba nơi với ba cách phân bổ khác nhau (host 555/0, container 522/1/32, Pi
518/5/32) là phép kiểm chéo mạnh hơn ba lần 555/0: nó chứng minh các nhánh `skip` **có thật sự được
đánh giá**, chứ không phải luôn rơi vào cùng một đường đi.

### 1.5. Quét mẫu vi phạm

| # | Mẫu | Kết quả |
|---|---|---|
| [13] | `def giai_nen\|data_filter\|filter=\|FilterError\|_CO_DATA_FILTER` trong `scripts/download_lfw.py` | `def giai_nen` **:102** · `hasattr(tarfile, "data_filter")` **:139** · `filter="data"` **:142** · `tarfile.FilterError` **:143** · `tf.extractall(dich)` **:155** ✅ |
| [14] | `@pytest\.mark\.[a-zA-Z_]+` toàn kho | đúng **hai** dấu: `parametrize`, `slow` ✅ |
| [15] | `ncnn`/`ultralytics` trong hai tệp requirements | `ncnn==1.0.20260526` chỉ ở `requirements.txt:9`; `ultralytics==8.4.39` chỉ ở `requirements-dev.txt:15`; hai lần nhắc `ncnn` còn lại ở `requirements-dev.txt:3,8` là chú thích ✅ |
| [16] | `assert True\|except\s*:\|except Exception\|[A-Z]:\\\|/home/\|/Users/` trên bốn tệp mã | **bốn dòng**, không dòng nào là mã thật — bảng dưới ✅ |

[13] là chốt của §5.3 đặc tả: mọi dấu vết của bộ lọc thư viện chuẩn (139, 142, 143) đều nằm **sau**
`def giai_nen` ở 102, tức trong thân hàm. Không có hằng `_CO_DATA_FILTER` mức module. Phép ép
`monkeypatch.delattr` của ca 29–33 vì thế còn tác dụng — R3 ở §1.7 xác nhận bằng máy.

Bốn dòng của [16], đã đọc lại từng dòng:

| Vị trí | Nội dung | Kết luận |
|---|---|---|
| `tests/test_download_lfw.py:83` | `noi_dung = "lfw:\n" + "\n".join(f"  {k}: {json.dumps(v)}" ...)` | chuỗi YAML ghi ra `tmp_path`, khớp mẫu vì `json.dumps` sinh đường dẫn Windows có ổ đĩa — **không** phải đường dẫn cứng trong mã |
| `tests/test_export_detector.py:554` | `f.write("export:\n  weights_pt: models/yolov8n-face.pt\n")` | nội dung tệp YAML hỏng cố ý của ca 41, đường dẫn **tương đối** |
| `tests/test_cau_hinh_pytest.py:80` | `f"...@pytest.mark.{dau_sai}\ndef test_mau():\n    assert True\n"` | thân tệp test **mô phỏng** sinh trong `tmp_path`; assert thật của ca 47 là `kq.returncode != 0` và `dau_sai in kq.stdout` |
| `tests/test_cau_hinh_pytest.py:98` | `"...@pytest.mark.slow\ndef test_mau():\n    assert True\n"` | như trên; assert thật của ca 48 là `kq.returncode == 0` |

Không dòng nào thuộc CB-6 (test giả): hai dòng `assert True` là **đầu vào** của tiến trình pytest
con, cố ý tầm thường để biến duy nhất giữa ca 47 và 48 là tên dấu. Cách ghép `"slow" + "ww"` ở
`:77` còn tránh cho chính phép quét [14] bắt nhầm dấu mô phỏng thành dấu thật của kho — một chi
tiết đúng chỗ.

### 1.6. Xác minh hành vi thư viện chuẩn — host, Python 3.12.5

| # | Dữ kiện đo được | Hệ quả |
|---|---|---|
| [17] | `co tarfile.data_filter : True` | host luôn ở nhánh A nếu không bị ép |
| | `Path("/tmp/thoat.txt").is_absolute() = False` | xác nhận cái bẫy §5.6 đặc tả nêu là **thật** trên Windows |
| | thành viên `'/tmp/thoat.txt'` qua bộ lọc `data`: `KHONG NEM LOI`, giải nén ra `['tmp/thoat.txt']`, `tep nam NGOAI dich: []` | bộ lọc `data` **cắt** ký tự `/` rồi giải nén vào **trong** đích |
| | thành viên `'../../thoat.txt'` qua bộ lọc `data`: `NEM LOI: tarfile.OutsideDestinationError` | nhánh A chặn tên tương đối vượt ra ngoài |

Ba dữ kiện này là nền để đọc R3 và để phân loại đúng khuyết tật §5.4 của đặc tả (§5.3 biên bản).

### 1.7. Mười hai phép đột biến — mọi lượt khôi phục `sha256` **KHỚP**

| # | Phép sửa | Ca đỏ thật | Dự đoán §11 đặc tả |
|---|---|---|---|
| [R1] | bỏ phép quét liên kết/thiết bị (`:135-137`) | **33, 34** | ĐB4 dự đoán 33, 34 — **đúng** |
| [R2] | bỏ phép kiểm chứa-trong-đích ở nhánh B (`:151-154`) | **30, 35** (32 bị deselect có chủ ý) | ĐB2 dự đoán 30c — **đúng**, ca 30 chứa assert 30c |
| [R3] | nâng `hasattr` lên mức module thành `_CO_DATA_FILTER` | **32**; ca 29 **vẫn xanh** | ĐB5 dự đoán 29 — **sai ca canh**, xem §5.3 |
| [R4] | nhánh B dùng `_MSG_HONG` thay `_MSG_VUOT_RA_NGOAI` | **30, 32, 35** | ĐB3 dự đoán 30, 35 — đúng, thêm 32 |
| [R5] | thay `is_relative_to` bằng `is_absolute()` | **30, 32, 35**; và `TEP THOAT NGOAI: CO` | ĐB6 dự đoán 30c (POSIX) / 32 (Windows) — **đúng** |
| [R6] | gỡ `--strict-markers` khỏi `addopts` | **46, 47** | ĐB7 — đúng |
| [R7] | vô hiệu khoá `markers` | **45, 48** | ĐB8 — đúng |
| [R8] | `rng.sample` → `danh_sach[:so_anh]` | **dong40** | ĐB9 — đúng |
| [R9] | `_DUONG_DAN_LFW_THAT` trỏ thư mục không tồn tại | **0 failed**; `dong43` chuyển SKIPPED | ĐB10 — đúng (đặc tả nói "skipped tăng 2" vì đếm 43 và 43b thành hai ca; đã gộp nên tăng 1) |
| [R10] | thông báo "vượt ra ngoài" lẫn thêm chữ "hỏng" | **05, 30** | ngoài đặc tả — canh assert phủ định |
| [R11] | `giai_nen` trả `dich` thay vì thư mục gốc | **03, 24a, 27, 27a, 28, 29** | ngoài đặc tả |
| [R12] | bỏ `sorted()` quanh `rng.sample` | **dong40** | ngoài đặc tả |

**Không phép nào xanh.** R5 là phép có giá trị cao nhất về an toàn: nó không chỉ làm ba ca đỏ mà
còn ghi được **tệp thật ra ngoài thư mục đích** (`TEP THOAT NGOAI: CO`) — tức phép kiểm ở `:153`
đang thực sự chặn một đường thoát, không phải một câu `if` trang trí.

R11 đáng chú ý ở chỗ nó làm **sáu** ca đỏ, trong đó bốn ca là ca cũ 24a/27/27a/28 của `main()`. Đó
là dấu hiệu tốt, không phải "đỏ lan man": giá trị trả về của `giai_nen` là đầu vào của luồng chính,
nên bốn ca tích hợp đỏ theo là đúng quan hệ nhân quả.

---

## 2. Đối chiếu đặc tả

| Mục đặc tả | Kết luận |
|---|---|
| §2 Danh sách trắng 7 tệp | ✅ đúng bảy, tệp cấm chạm không bị đụng ([6]) |
| §4 Tham số → config | ✅ không hằng số miền bài toán mới; ba hằng đúng chỗ (`:92`, `:95`, `:96`, `tests/test_export_detector.py:39`) |
| §5.1 Chữ ký `giai_nen` | ✅ `def giai_nen(archive: Path, dich: Path) -> Path` (`:102`) nguyên vẹn, lời gọi `:402` không đổi, ngoại lệ vẫn `LoiCauHinh` |
| §5.2 Ba hằng thông báo mức module | ✅ `:92-99`; ba chuỗi loại trừ nhau đúng bảng — xem §3.2 |
| §5.3 `hasattr` trong thân hàm | ✅ `:139` sau `def` ở `:102`; R3 xác nhận bằng máy |
| §5.4 Quét thành viên ở **cả hai** nhánh | ✅ `:135-137` đặt ngoài `if/else`; ca 33+34 và R1 chứng minh |
| §5.5 Nhánh A giữ nguyên thứ tự bắt ngoại lệ | ✅ `:141-146`, ghi chú `FilterError` trước `TarError` được giữ |
| §5.6 Nhánh B — đúng **một** phép kiểm chứa-trong-đích | ✅ `:150-154`, `resolve()` cả hai vế; R5 chứng minh không thay được bằng `is_absolute()` |
| §5.7 Chỉ thư viện chuẩn | ✅ không import mới; docstring `:3-4` vẫn đúng |
| §5.8 Không thêm `filterwarnings`/`-W error` | ✅ `pyproject.toml` chỉ có `markers` + `addopts` |
| §6 `markers` + `addopts` | ✅ `pyproject.toml:10-13`, `testpaths`/`pythonpath` giữ nguyên, không khoá thừa |
| §7.1 `requirements.txt` không sửa; `requirements-dev.txt` hai thay đổi | ✅ dòng `ncnn` trùng đã xoá, chú thích đầu tệp viết lại đủ bốn ý ([15]) |
| §7.2 Mục cài đặt README năm ý | ✅ `README.md:4-29`, đủ 1–5; cảnh báo ở `:22` đúng vế phủ định như §10 đòi |
| §7.3 Ca 39/40 dùng `tmp_path`, ngưỡng 100 | ✅ `:523-548`, `_TOI_THIEU_ANH_LAY_MAU = 100` (`:39`) |
| §7.4 Người gác cho hai hàm trợ giúp | ✅ `_bo_qua_neu_thieu` (`:42-45`) gọi ở `:78` trước `shutil.copy2`; `_vai_anh_lfw_that` skip ở `:87-91` nêu tên thư mục + số ảnh |
| §8.1 Ca 29–36 | ✅ tám hàm test, mười một dòng bảng — xem §5.2 |
| §8.2 Ca 39, 40, 43, 44 | ✅ bốn hàm; 39b kiểm bằng grep đúng như đặc tả quy định |
| §8.3 Ca 45–48 | ✅ `tomllib`, `-c pyproject.toml`, `-p no:cacheprovider`, `cwd` gốc kho — không mạng, không `git` |
| §12 Ràng buộc kỹ thuật | ✅ không API riêng 3.12, không `except` trần, ca test chỉ ghi `tmp_path`, không chạm mạng |
| §12b Lượt người dùng | ✅ [7]–[12]; image **không** phải dựng lại |
| §14 Ngoài phạm vi | ✅ không đụng `test_export_detector_ncnn.py`, không tạo `requirements-pi.txt`, không thêm `filterwarnings`, không nới `giai_nen` cho liên kết mềm, không sửa `CLAUDE.md`/Chương 4 |

Không mục nào Không đạt.

---

## 3. Đọc mã — hai điểm chịu lực

### 3.1. Nhánh dự phòng của `giai_nen` có sót loại thành viên nguy hiểm nào không

`scripts/download_lfw.py:126-159`. Phép quét chung ở `:135-137` chạy **trước** khi rẽ nhánh:

```python
for tv in thanh_vien:
    if not (tv.isfile() or tv.isdir()):
        raise LoiCauHinh(_MSG_KHONG_AN_TOAN.format(archive=archive))
```

`TarInfo.isfile()` nhận `REGTYPE`, `AREGTYPE`, `CONTTYPE`, `GNUTYPE_SPARSE`; `isdir()` nhận
`DIRTYPE`. Mọi loại còn lại bị từ chối. Đối chiếu từng loại thành viên nguy hiểm mà bộ lọc `data`
của thư viện chuẩn xử lý:

| Loại thành viên | Nhánh A (bộ lọc `data`) | Nhánh B (dự phòng) | Ca chốt |
|---|---|---|---|
| Tệp thường / thư mục hợp lệ | cho qua | cho qua | 03, 29, 36 |
| Tên tương đối vượt ra ngoài (`../../x`) | `OutsideDestinationError` → `LoiCauHinh` | `is_relative_to` chặn | 05, 30, 35, R2, R5 |
| Tên **tuyệt đối** (`/tmp/x`) | **không ném**, cắt `/` rồi giải nén trong đích | **ném** `LoiCauHinh` | 32 (chỉ nhánh B) — xem 🔵-2 |
| Liên kết mềm `SYMTYPE` | chặn bởi phép quét chung | như A | 33, 34, R1 |
| Liên kết cứng `LNKTYPE` | chặn bởi phép quét chung | như A | cùng dòng mã với 33 |
| Tệp thiết bị `CHRTYPE`/`BLKTYPE`, FIFO | chặn bởi phép quét chung | như A | cùng dòng mã với 33 |
| Bit quyền `setuid`/`setgid`/sticky | bộ lọc **xoá** | **giữ nguyên** | không ca nào — 🔵-1 |
| Chủ sở hữu `uid`/`gid` | bộ lọc bỏ qua | `extractall` áp dụng khi chạy bằng `root` | không ca nào — 🔵-1 |

**Kết luận: không sót loại thành viên nguy hiểm nào.** Bốn loại có khả năng thoát ra khỏi thư mục
đích (liên kết mềm, liên kết cứng, tên tương đối vượt ra ngoài, tên tuyệt đối) đều bị chặn ở nhánh
B, và ba trong bốn có ca đột biến chứng minh. Khác biệt duy nhất còn lại so với bộ lọc `data` là
**bit quyền và chủ sở hữu** — không phải đường thoát khỏi thư mục đích, và đặc tả §5.6 đã chốt
"đúng một phép kiểm", nên đây là 🔵 chứ không phải lỗi cài đặt.

Ba điểm cài đặt khác đã đọc và xác nhận đúng:

- `LoiCauHinh` kế thừa `LoiHeThong(Exception)` (`src/common/exceptions.py:4-9`), **không** phải
  `OSError` — nên ba lệnh `raise` bên trong khối `try` ở `:126` không bị `except tarfile.TarError`
  (`:156`) hay `except OSError` (`:158`) nuốt rồi đổi thành thông báo "hỏng". Đây là điều kiện ngầm
  mà ca 30/31 phụ thuộc; nếu lớp ngoại lệ đổi chỗ trong cây kế thừa, hai ca ấy sẽ đỏ chứ không lặng
  lẽ sai — đúng hướng.
- `resolve()` gọi trên **cả hai vế** (`:150`, `:152`) nên phép so không lệch khi thư mục tạm đi qua
  liên kết mềm; `dich.mkdir(...)` ở `:125` chạy trước nên `resolve()` không phụ thuộc thứ tự tạo.
- Không thành viên nào lọt qua bằng đường "giải nén rồi mới kiểm": cả hai vòng lặp đều đứng trước
  `extractall`.

### 3.2. Ba thông báo có thật sự loại trừ nhau không

| Hằng | Chứa | Không chứa `hỏng` | Không chứa `vượt ra ngoài` | Không chứa `không an toàn` |
|---|---|---|---|---|
| `_MSG_VUOT_RA_NGOAI` (`:92`) | `vượt ra ngoài` | ✅ | — | ✅ |
| `_MSG_HONG` (`:95`) | `hỏng` | — | ✅ | ✅ (có `không`, không có `không an toàn`) |
| `_MSG_KHONG_AN_TOAN` (`:96`) | `không an toàn` | ✅ | ✅ | — |

Đúng bảng §5.2. R4 và R10 chứng minh các assert phủ định của ca 04/05/30/31 thật sự canh điều này,
không phải chỉ chép cho đủ.

### 3.3. Đánh giá `addopts = ["--strict-markers"]`

Đây là thay đổi duy nhất trong mã việc có ảnh hưởng **toàn kho** và ảnh hưởng cả những mã việc chưa
viết, nên phải cân riêng.

| | |
|---|---|
| Được | Một dấu viết sai chính tả từ nay làm **đỏ ngay lượt chạy đầu** thay vì cảnh báo rồi trôi. Chế độ hỏng bị chặn là chế độ tệ nhất: ca mang dấu sai vẫn chạy, vẫn xanh, và **lọt qua `-m "not slow"`** — tức chạy trên máy thiếu mô hình và đỏ vì lý do vô can. [11] cho thấy 33 dòng cảnh báo trên Pi đã hết. |
| Mất | Không đáng kể ở thời điểm này: [14] xác nhận toàn kho chỉ dùng **một** dấu tuỳ biến. Chi phí chỉ phát sinh khi ai đó thêm dấu mới mà quên khai báo — và đó chính là điều cần bị chặn. |
| Rủi ro còn lại | Cờ này áp cho mọi lượt `pytest` đọc `pyproject.toml`, **kể cả tiến trình con** ở ca 47/48 — đúng chủ ý, và ca 48 là dòng cặp đường thành công bảo đảm không chặn nhầm dấu hợp lệ. R6/R7 chứng minh cả hai chiều đều có ca canh. |

**Kết luận: thay đổi đúng, đáng giữ, không có tác dụng phụ đo được.** Một gợi ý bổ sung ở 🔵-4.

---

## 4. Hai điểm sống còn

**Trung thực số liệu.** Mã việc không sinh, không sửa, không đọc tệp nào trong `results/`; không có
giá trị mặc định nào trông như kết quả đo. Con số duy nhất đi vào tài liệu là **2,5 GB**
(`requirements-dev.txt:4`, `README.md:23`) và **420 MB** (`du -sh .venv`, [12]) — cả hai truy được
về lượt đo trên Pi ở §3.5 đặc tả và [12] biên bản này, và cả hai được ghi kèm ngữ cảnh ("thiết bị
không có GPU NVIDIA"), không phải con số trần. Người cài đặt báo **555** thay vì **545** mà đặc tả
mong đợi và **không tự chỉnh cho khớp** — đúng yêu cầu "không tự ý chỉnh cho khớp" ở §9 đặc tả, và
đúng tinh thần R5. Ghi nhận rõ hành vi này.

**An toàn phần cứng.** Mã việc không đụng `src/actuator/**`, không đụng GPIO, không đụng camera.
Không có trạng thái thiết bị nào để đưa về an toàn. Mặt "an toàn" của mã việc này nằm ở chỗ khác và
đã soi ở §3.1: `giai_nen` là điểm duy nhất trong dự án ghi tệp ra đĩa từ **dữ liệu tải về từ
Internet**, và nhánh dự phòng mới viết là nhánh sẽ chạy trên **chính thiết bị đích**.

---

## 5. Bốn kết luận của lượt kiểm

### 5.1. Đặc tả §9 sai mốc kho: 531 thay vì 541 — khuyết tật của **đặc tả**

**Vị trí**: `docs/dac-ta/P0-04-tuong-thich-pi-os.md:503` — *"545 ca thu thập (531 hiện có + 14 ca
mới)"*.

Nguồn của sai lệch truy được: **531** là tổng ca của lượt chạy trên Pi ghi ở §3.1 đặc tả
(`7 failed + 490 passed + 2 skipped + 32 deselected`), tức mốc **trước** khi `P3-04` gộp vào `dev`.
Nhưng dòng "Phụ thuộc" ở đầu đặc tả trỏ `dev` tại `57b874c`, và nhánh thực tế rẽ từ `bfc9026` — cả
hai đều là `dev` **sau** `P3-04`, nơi tổng ca là **541**. Đặc tả tự mâu thuẫn giữa dòng phụ thuộc
và số ca mong đợi; phép cộng `+14` thì đúng.

**Không phải lỗi của mã.** Số ca mới đúng 14, phân bổ đúng từng tệp ([5]).

⚠️ Đây là **lần thứ hai liên tiếp** cùng một lớp khuyết tật: biên bản `P3-04` vừa phải vá đúng
chuyện đặc tả ghi số ca trần. Hai lần thì không còn là sự cố lẻ. Đề nghị nâng thành quy ước cho
`spec-writer` — xem §7.

### 5.2. Gộp ca phụ **không** làm mất chốt — đã chứng minh bằng máy

Người cài đặt gộp các dòng phụ của §8 đặc tả thành assert bên trong ca chính: 29b→29, 30b/30c→30,
31b→31, 40b→40, 43b→43, 47b→47. Câu hỏi "làm vậy có mất chốt không" nay có ba câu trả lời đo được:

| Phép | Phá **riêng** assert thứ hai của ca gộp | Kết quả |
|---|---|---|
| R10 | vế phủ định `"hỏng" not in thong_bao` của ca 30 | **05, 30 đỏ** |
| R11 | vế `ket_qua == dich / "lfw"` của ca 29 | **03, 24a, 27, 27a, 28, 29 đỏ** |
| R12 | vế `a == sorted(a)` của ca 40 | **dong40 đỏ** |

Cả ba assert bị gộp **vẫn cắn**. Độ **phủ** không mất gì.

Hơn nữa, việc gộp là thứ chính đặc tả yêu cầu chứ không phải một chệch hướng: §9 đặc tả ghi rõ
`test_download_lfw.py` phải có **40 ca** = 32 + **8**, trong khi §8.1 liệt kê **11 dòng** cho ca
29–36. Con số 8 chỉ đạt được nếu các dòng `b`/`c` là assert trong cùng một hàm test. Tương tự với
47 ca của `test_export_detector.py` và 4 ca của `test_cau_hinh_pytest.py`. Cách đọc "một dòng bảng
= một assert, một số hiệu = một hàm test" là cách đọc **duy nhất** làm §8 và §9 nhất quán.

Cái thật sự mất là **độ phân giải chẩn đoán**: khi ca 30 đỏ, phải đọc dòng assert mới biết là do
thông báo sai, do lẫn chữ "hỏng", hay do tệp bị ghi ra đĩa. Với ba assert trong một ca thì đây là
chi phí chấp nhận được. Không khuyến nghị tách ở mã việc này; nếu một ca gộp nào đó lớn dần quá bốn
assert khác nhóm nguyên nhân thì mới tách.

### 5.3. Đặc tả §11 dự đoán sai ca canh của ĐB5, và §5.4 tuyên bố quá rộng — khuyết tật của **đặc tả**

**Vị trí**: `docs/dac-ta/P0-04-tuong-thich-pi-os.md:585` (ĐB5 → ca 29) và `:251` (*"Đặt phép quét ra
ngoài làm hai nhánh xử lý liên kết y hệt nhau"*, cùng câu dẫn ĐB1 → ca 29).

R3 cho thấy khi `hasattr` bị nâng lên mức module, **ca 29 vẫn xanh**, ca **32** mới đỏ. Cơ chế đọc
được từ [17]: trên host, `_CO_DATA_FILTER` tính sẵn thành `True` nên mọi lượt gọi rơi vào nhánh A;
ca 29 chỉ kiểm *giải nén thành công*, mà nhánh A cũng giải nén thành công — nên ca 29 **không thể**
là ca canh của việc chọn nhánh. Ca 32 mới là ca canh, vì nó là ca duy nhất mà **hai nhánh cho kết
quả khác nhau**: với thành viên tên tuyệt đối `/tmp/thoat.txt`, bộ lọc `data` không ném lỗi mà cắt
ký tự `/` rồi giải nén vào trong đích (`tep nam NGOAI dich: []`), còn nhánh B ném `LoiCauHinh`.

Hệ quả sâu hơn, và nó chạm vào một câu tuyên bố của đặc tả: **hai nhánh không cho cùng mức chặn**.
Chúng giống nhau ở liên kết/thiết bị (đúng như §5.4 lập luận, và ca 33+34 chứng minh) và ở tên
tương đối vượt ra ngoài (ca 35 chứng minh), nhưng **khác nhau ở tên tuyệt đối**: nhánh B chặt hơn.
Chệch theo **chiều an toàn hơn**, nên không phải khuyết tật của mã — nhưng câu chữ §5.4 hàm ý hai
nhánh xử lý y hệt nhau là không đúng với thực tế đo được.

**Phân loại: khuyết tật của đặc tả, không của mã.** Người cài đặt cài đúng những gì §5.4 và §5.6
yêu cầu; chính bộ đột biến do đặc tả đặt ra mới là thứ chỉ sai. Việc cần làm là sửa hai chỗ chữ
trong đặc tả và bổ sung một ca chốt tường minh — xem 🔵-2.

### 5.4. Mã việc được kiểm trên đúng phần cứng đích, và đây là lần đầu điều đó **không thay thế được**

`P3-04` là mã việc đầu tiên có lượt chạy trên Pi 5 thật, nhưng lượt ấy là **kiểm chéo**: host và
container cũng chạy đủ 34 ca. `P0-04` khác về chất — lượt trên Pi là **bằng chứng duy nhất**:

| Môi trường | Python | Có `tarfile.data_filter` | Nhánh chạy tự nhiên |
|---|---|---|---|
| `pc_x86` (host) | 3.12.5 | có | **A** |
| `docker_arm64` | **3.11.16** ([7]) | có | **A** |
| `pi5` | **3.11.2** | **không** | **B** |

Container báo đúng ba chữ "Python 3.11 · ARM64 · Bookworm" trùng khớp với Pi, và vẫn bỏ lọt lỗi —
vì khoảng cách 3.11.2 → 3.11.16 chứa đúng bản backport 3.11.4. Bảy ca đỏ ở §3.2 đặc tả **chỉ đỏ
trên Pi**, và nay chỉ có thể chứng minh là đã xanh **trên Pi** ([9]).

Đây là dẫn chứng cụ thể, có số, cho luận điểm ở Chương 4 §4.1 rằng `docker_arm64` **không thay
thế** `pi5`. Trước đây luận điểm ấy chỉ nói về số đo hiệu năng (QEMU giả lập). `P0-04` bổ sung một
vế mạnh hơn hẳn: container còn không bảo đảm được **tính đúng đắn chức năng**. Cặp số **3.11.16 và
3.11.2** nên được trích thẳng vào §4.1 khi `paper-writer` viết mục đó — đặc tả §13 đã đề nghị điều
này và đặt nó ngoài phạm vi mã việc; biên bản xác nhận đề nghị đó có cơ sở đo đạc.

---

## 6. Lỗi phải sửa

**Không có mục 🔴 CHẶN-A, không có mục 🔴 CHẶN-B, không có mục 🟡 CẦN SỬA.**

Đã soi riêng và không tìm thấy: hardcode tham số thực nghiệm (§4 đặc tả không sinh tham số nào; ba
hằng đều là chuỗi thông báo hoặc ngưỡng của ca test), `print()` trong `src/` (mã việc không đụng
`src/`; sáu lệnh `print` ở `scripts/download_lfw.py:368-422` là bảng kết quả có sẵn, được §15 đặc
tả cho phép), `except` trần, test giả, đường dẫn tuyệt đối máy cá nhân, tệp cấm lọt git, dependency
thêm ngoài đặc tả, việc ngoài phạm vi §14.

---

## 7. 🔵 Góp ý (không chặn — người dùng quyết định)

### 🔵-1 — Nhánh dự phòng không làm sạch bit quyền như bộ lọc `data`

**Vị trí**: `scripts/download_lfw.py:155` — `tf.extractall(dich)`.

Bộ lọc `data` của thư viện chuẩn, ngoài việc chặn đường thoát, còn **xoá bit `setuid`/`setgid`/
sticky** và bỏ qua `uid`/`gid` ghi trong tệp nén. Nhánh dự phòng không làm hai việc đó: tệp giải
nén trên Pi giữ nguyên quyền như tệp nén khai báo, và nếu ai chạy script bằng `sudo` thì `extractall`
còn áp cả chủ sở hữu.

**Mức độ**: thấp. Thành viên đã phải qua phép quét `isfile()/isdir()` và phép kiểm chứa-trong-đích,
tệp đích nằm trong `data/impostor/` và không được hệ thống thi hành, tệp nén nguồn là LFW từ một URL
cố định có đối chiếu `sha256`. Đây **không** phải đường thoát khỏi thư mục đích.

**Vì sao vẫn ghi**: đặc tả §5.6 chốt "phép kiểm bắt buộc, **duy nhất một phép**", nên mã đang đúng
đặc tả và **không** phải sửa ở vòng này. Nhưng đoạn chú thích `:148-149` mô tả nhánh B là bản thay
thế của bộ lọc `data` mà không nêu chỗ nó không tương đương — người đọc sau dễ tin là tương đương
hoàn toàn.

**Đề xuất** (chi phí một dòng, không đổi hành vi ca test nào): hoặc thêm vào vòng lặp `:151-154`
một dòng `tv.mode &= 0o755`, hoặc — rẻ hơn và trung thực hơn — bổ sung một câu vào chú thích
`:148-149` nêu rõ nhánh B chỉ tương đương bộ lọc `data` **ở phần đường dẫn**, không ở phần quyền và
chủ sở hữu. Nếu chọn phương án thứ nhất thì phải kèm một ca chốt, vì hiện không ca nào chạm tới.

### 🔵-2 — Sửa hai câu của đặc tả và bổ sung ca 37 chốt khác biệt giữa hai nhánh

**Vị trí**: `docs/dac-ta/P0-04-tuong-thich-pi-os.md:251` và `:585`.

Theo §5.3 biên bản, hai nhánh **khác nhau** ở thành viên tên tuyệt đối, và hiện **không ca nào**
chốt hành vi của nhánh A trong tình huống đó (ca 32 chỉ chạy nhánh B). Khác biệt này không nguy
hiểm — nhánh A giải nén vào trong đích, nhánh B từ chối — nhưng nó đang là kiến thức nằm trong biên
bản chứ không nằm trong bộ kiểm thử; ai đó "dọn dẹp" nhánh B trong tương lai sẽ không có ca nào cản.

**Đề xuất** — ba việc, nên gộp vào **một mã việc dọn dẹp** cùng với 🔵-1 và mục §14 đặc tả:

1. Sửa `:585`: ca canh của ĐB5 là **32**, không phải 29, kèm một dòng lý do.
2. Sửa `:251`: thu hẹp câu "hai nhánh xử lý y hệt nhau" về đúng phạm vi **liên kết và tệp thiết bị**;
   ghi thêm rằng ở thành viên tên tuyệt đối, nhánh B chặt hơn nhánh A một bậc và đó là chủ ý.
3. Thêm ca **37**: nhánh A + thành viên `/tmp/thoat.txt` → **không** ném lỗi, tệp nằm tại
   `dich/tmp/thoat.txt`, và `not any(<ngoài dich>.rglob("thoat.txt"))`. Ca này biến khác biệt đang
   ẩn thành một dòng chốt đọc được.

### 🔵-3 — Thông báo `skip` của `_bo_qua_neu_thieu` chỉ sai đường khi thiếu trọng số `.pt`

**Vị trí**: `tests/test_export_detector.py:42-45`, dùng ở `:78`.

```python
def _bo_qua_neu_thieu(duong_dan: Path) -> None:
    if not duong_dan.exists():
        pytest.skip(f"chưa có {duong_dan}, chạy scripts/export_detector.py trước")
```

Khuôn này chép nguyên văn từ `tests/test_yolo_face.py:49-51`, nơi đường dẫn được gác là
`models/yolov8n-face.onnx` — tệp **do** `export_detector.py` sinh ra, nên lời khuyên đúng. Ở đây
đường dẫn được gác là `_DUONG_DAN_WEIGHTS_THAT = models/yolov8n-face.pt` (`:33`) — tệp `.pt` là
**đầu vào** của `export_detector.py`, chạy script đó khi thiếu `.pt` sẽ chỉ hỏng thêm một lần nữa.
Người đọc thông báo sẽ mất một vòng thử.

**Vì sao chỉ là 🔵**: §7.4 đặc tả yêu cầu "theo **đúng khuôn** đã dùng ở `tests/test_yolo_face.py:49-51`",
nên chép nguyên văn là làm đúng đặc tả; nội dung câu thông báo không được đặc tả quy định.

**Đề xuất**: đổi câu thành `f"chưa có {duong_dan}, xem models/README.md bảng A để tải"` cho tệp
trọng số, hoặc tách thành hai hàm gác với hai lời khuyên. Gộp vào mã việc dọn dẹp ở 🔵-2.

### 🔵-4 — Cân nhắc thêm `--strict-config` bên cạnh `--strict-markers`

**Vị trí**: `pyproject.toml:13`.

`--strict-markers` chặn dấu chưa khai báo; `--strict-config` chặn **khoá cấu hình** viết sai trong
`[tool.pytest.ini_options]` — cùng một lớp lỗi im lặng, cùng chi phí bằng không ở kho hiện tại (bốn
khoá, đều hợp lệ). Có nó thì một lần gõ nhầm `testpath` thay vì `testpaths` sẽ đỏ thay vì lặng lẽ
làm `pytest` quét cả kho.

**Chi phí/lợi ích**: một từ trong `addopts`, một ca test kiểu ca 46. Không cấp bách — §6 đặc tả chốt
"không thêm khoá nào khác", nên đây là việc của mã việc sau, không phải của vòng này.

### 🔵-5 — Quy ước cho `spec-writer`: số ca kiểm thử phải ghi kèm mốc, môi trường và bộ lọc

Hai mã việc liên tiếp (`P3-04`, `P0-04`) đều vấp đúng một chỗ: đặc tả ghi **một con số ca trần**,
người cài đặt đo ra số khác, và phải mất một mục biên bản để chứng minh chênh lệch là vô hại.

**Đề xuất** — từ mã việc sau, mọi con số ca trong đặc tả viết theo dạng:

> `<số> ca thu thập trên <mốc commit>, môi trường <pc_x86 | docker_arm64 | pi5>, lệnh <có/không lọc marker>`

và mốc phải là **commit ghi ở dòng "Phụ thuộc"**, không phải commit của lượt chạy được trích dẫn ở
phần dữ kiện. Đây là chỗ cả hai lần vừa rồi đều lệch. Nếu người dùng đồng ý, ghi vào
`.claude/agents/spec-writer.agent.md` bằng một commit `chore(quy-trinh)` riêng, không trộn vào mã
việc nào.

---

## 8. Việc tiếp theo

**Đã ĐẠT CÓ ĐIỀU KIỆN — được commit và gộp `dev`.** Không có việc nào giao lại cho người cài đặt ở
vòng này.

Gợi ý commit message:

```
fix(nen-tang): giai_nen chạy được trên Python 3.11.2 của Pi OS, khai báo dấu pytest và dọn phụ thuộc — P0-04
```

Sau khi gộp:

1. **Cập nhật `CLAUDE.md` §8** — Phase 0 bước 0.4 mở lại một phần: bộ kiểm thử đã xanh trên phần
   cứng đích (555 ca, ba môi trường), `.venv` trên Pi 420 MB. Đây là việc của phiên chính.
2. **Mã việc dọn dẹp `P0-05`** gộp: 🔵-1 (chú thích hoặc bit quyền), 🔵-2 (hai câu đặc tả + ca 37),
   🔵-3 (thông báo skip), 🔵-4 (`--strict-config`), và mục §14 đặc tả để lại
   (`tests/test_export_detector_ncnn.py:7-10`). Năm việc nhỏ, cùng một vùng tệp, đáng gộp một mã
   việc thay vì năm.
3. **`paper-writer`, Chương 4 §4.1** — bổ sung vế "container không bảo đảm tính đúng đắn chức năng",
   trích cặp số 3.11.16 / 3.11.2 và bảy ca ở §5.4 biên bản này. Đặc tả §13 đã đặt việc này ngoài
   phạm vi mã việc và biên bản xác nhận nó có cơ sở đo đạc.
4. Việc chặn của Phase 3 **không đổi**: mã việc dọn dẹp `data/embeddings/` theo §12.1 biên bản
   `P3-03` vẫn phải đóng trước bước 3.5.
