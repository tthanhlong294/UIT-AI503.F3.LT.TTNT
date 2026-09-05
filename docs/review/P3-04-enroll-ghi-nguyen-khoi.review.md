# Review P3-04-enroll-ghi-nguyen-khoi — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-04-enroll-ghi-nguyen-khoi.md` (commit `57b874c`) |
| **Nhánh** | `feat/p3-04-enroll-ghi-nguyen-khoi`, commit `e7923e3`, điểm rẽ nhánh `57b874c` |
| **Mã được kiểm** | hai tệp: `scripts/enroll.py` (+126/−32), `tests/test_enroll.py` (+246/−3) |
| **Ngày** | 2026-09-05 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — không mục 🔴, không mục 🟡. Ba mục 🔵 và hai khuyết tật của **đặc tả** (không của mã). Được commit và gộp `dev` |

Toàn bộ số liệu dưới đây đến từ **hai lượt chạy của người dùng** ngày 05/09/2026, không dùng lại bảng
tự kiểm của người cài đặt. Bảy phép đột biến được dựng lại từ đầu; cả bảy lượt khôi phục
`scripts/enroll.py` đều cho đúng
`4ED49F9702A4E570041AABBEBB51627B8CFE4B36390222AA03320A5D24FF45F6` — không sót mã đột biến nào.
Chốt cuối `git status --short --untracked-files=all` **rỗng**.

Hai điều làm lượt kiểm này khác các lượt trước: bộ kiểm thử chạy được trên **Raspberry Pi 5 thật**
(lần đầu trong dự án), và **hai phép đột biến từng chứng minh bộ test cũ mù nay đều bị bắt** — tức
§12.2 và §12.3 của biên bản `P3-03` được đóng lại bằng đo đạc, không phải đóng trên giấy (§1.5).

---

## 1. Kết quả kiểm máy

### 1.1. Lượt một — ba lệnh nền, container và phần cứng đích

| # | Lệnh | Kết quả |
|---|---|---|
| [1] | `python -m black --check --line-length 100 src tests scripts` | `All done!` — **47 tệp không đổi** ✅ |
| [2] | `python -m ruff check src tests scripts` | `All checks passed!` ✅ |
| [3] | `python -m pytest tests/test_enroll.py -v` (host, Python 3.12.5) | **34 passed**, 0 failed, 0 skipped ✅ — `0 skipped` xác nhận năm ca `slow` (dòng 07, 08, 17, 18, 25) chạy thật với trọng số thật |
| [4] | `python -m pytest -q` toàn kho (host) | **541 passed**, 0 failed ✅ — 531 → 541, đúng **+10**, khớp chính xác mười ca mới 27–36 |
| [5] | `docker run … faceid:arm64 python3 -m pytest -q -m "not slow"` | **508 passed, 1 skipped, 32 deselected**, 973 s ✅ — 498 → 508, cũng đúng **+10**. Đúng một image `faceid:arm64`, không dựng lại (R43) |
| [6] | `python -m pytest tests/test_enroll.py -q` trên **Raspberry Pi 5**, Python 3.11.2, aarch64, ext4 | **34 passed**, 11,44 s ✅ |

Ba con số `+10` khớp nhau ở ba môi trường độc lập (host chọn lọc, host toàn kho, container ARM64):
mười ca mới chạy được ở cả ba nơi và **không ca cũ nào hỏng theo**.

⭐ Ghi chú về [6] — đây là dữ kiện có giá trị riêng, vượt ra ngoài mã việc. Mã việc này đụng vào
`os.rename` và `shutil.rmtree`, tức đúng nhóm thao tác có hành vi **khác nhau giữa Windows và
Linux** mà §4.2 đặc tả nêu ra làm lý do loại `os.replace`. Bộ 34 ca xanh trên NTFS (host), trên
overlayfs qua QEMU (container) và trên **ext4 của phần cứng đích** là bằng chứng ba mặt rằng lập
luận đó được cài đặt đúng, không phải chỉ đúng trên máy phát triển. [6] là số **chức năng**, không
phải số hiệu năng, nên không vướng ràng buộc `moi_truong` của CLAUDE.md §2.9.

### 1.2. Lượt hai — phạm vi tệp và dữ liệu cấm

| # | Lệnh | Kết quả |
|---|---|---|
| [7] | `git diff --stat dev...HEAD` (phép so **ba chấm**) | đúng hai dòng `M`: `scripts/enroll.py` +126/−32 · `tests/test_enroll.py` +246/−3. **Không** dòng `D`/`A` nào ✅ đúng danh sách trắng §2 |
| [8] | `git diff dev...HEAD -- tests/test_enroll.py`, lọc dòng bắt đầu bằng `-` | đúng ba dòng, là khối `if manifest.exists():` + hai dòng thân — xem trích dưới ✅ |
| [9] | `git diff dev...HEAD -- scripts/enroll.py`, lọc dòng bắt đầu bằng `-` | 32 dòng, toàn bộ là mã **chuyển chỗ**, không mất — xem đối chiếu §2.7 ✅ |
| [21] | `git status --short --untracked-files=all` (chốt cuối lượt) | **rỗng** ✅ |

Mười hai dòng `D` xuất hiện ở lượt một là **ảo giác của phép so hai đầu mút** (`dev..HEAD` không
tính điểm rẽ nhánh) — đã loại trừ bằng [7]. Ghi lại để lượt kiểm sau không lặp lại: với nhánh
`feat/` xuất phát từ một `dev` đã đi tiếp, chỉ phép so ba chấm mới cho đúng phạm vi mã việc.

**R25 sạch** — không cần lệnh lọc riêng: [7] cho thấy toàn bộ thay đổi nằm trong đúng hai tệp `.py`,
và [21] rỗng, nên không tệp `.jpg/.png/.npy/.onnx/.env/.db` nào lọt vào vùng theo dõi của git.
Không tệp nào trong `data/`, `results/`, `report/`, `configs/`, `docs/`, `models/`, `.claude/`.

Ba dòng bị xoá ở `tests/test_enroll.py`, nguyên văn:

```
-    if manifest.exists():
-        rows = _doc_manifest(manifest)
-        assert not any(r["user_id"] == "nguoi_a" and r["trang_thai"] == "thieu_anh" for r in rows)
```

Đúng khối `if` chết mà §4.5 điều 2 yêu cầu loại bỏ, **không ca nào bị xoá** — ràng buộc "chỉ cộng
thêm ca mới" của §2 đặc tả được giữ.

### 1.3. Quét mẫu vi phạm

| # | Mẫu | Kết quả |
|---|---|---|
| [10] | `shutil.rmtree\|os.remove\|unlink\|os.rename\|os.replace` trong `scripts/enroll.py` | 9 vị trí, **không lời gọi nào xoá thẳng `ra_dir`** ✅ — bảng phân loại dưới |
| [11] | đường dẫn tuyệt đối máy cá nhân (`[A-Z]:\\`, `/home/`, `/Users/`) | rỗng ✅ |
| [12] | `assert True` · `except:` trần · `except Exception` | rỗng ✅ (§7 đặc tả, CB-4) |

Phân loại chín vị trí của [10] — đây là phép kiểm chịu lực nhất của §6.1 đặc tả, vì một lời gọi xoá
đặt nhầm chỗ sẽ biến chính bản vá này thành đường mất gallery:

| Dòng | Lời gọi | Đối tượng | Hợp lệ? |
|---|---|---|---|
| 396 | (comment) | — | — |
| 412 | `shutil.rmtree(thu_muc_cu)` | `.<backend>.cu` tàn dư | ✅ thư mục tạm |
| 416 | `os.rename(ra_dir, thu_muc_cu)` | dời gallery cũ sang chỗ tạm | ✅ không xoá |
| 420 | `os.rename(thu_muc_tam, ra_dir)` | đặt gallery mới vào chỗ | ✅ đích không tồn tại |
| 423 | `os.rename(thu_muc_cu, ra_dir)` | **hoàn tác** khi 420 hỏng | ✅ vượt yêu cầu đặc tả |
| 427 | `shutil.rmtree(thu_muc_cu)` | xoá gallery cũ **sau** khi đổi tên xong | ✅ đúng §4.2 điều 3 — xem 🔵 §5.1 |
| 553 | `shutil.rmtree(thu_muc_tam)` | tàn dư lượt hỏng trước (§4.2 điều 1) | ✅ thư mục tạm |
| 618, 623 | `shutil.rmtree(thu_muc_tam, ignore_errors=True)` | dọn ở hai nhánh `except` (§4.2 điều 4) | ✅ thư mục tạm |

Không dòng nào nhận `ra_dir` làm đối tượng xoá. Dòng 423 không có trong đặc tả: đó là nhánh hoàn
tác khi phép đổi tên thứ hai thất bại, để không bao giờ tồn tại trạng thái *mất cả gallery cũ lẫn
gallery mới*. Đây là mã đúng hướng với §4.3 và được ghi rõ trong docstring `Raises:` (`:406-409`).

### 1.4. Bảy phép đột biến

Mốc chuẩn trước đột biến [13]: **34 passed**.

| # | Phép | Vị trí | Kết quả | Ca đỏ | Dự đoán |
|---|---|---|---|---|---|
| [14] ĐB5 | `raise LoiMoHinh(` → `raise LoiCauHinh(` | `:218` | 1 failed, 33 passed | `test_dong35` | đúng |
| [15] ĐB6 | `so_anh_tim_thay <` → `<=` | `:214` | **4 failed, 30 passed** | `test_dong27`, `28`, `31`, `36` | dự đoán 1, thực tế 4 |
| [16] ĐB7 | hai `shutil.rmtree(thu_muc_tam, ignore_errors=True)` → `pass` | `:618`, `:623` | 1 failed, 33 passed | `test_dong28` | đúng, `test_dong27` vẫn xanh |
| [17] ĐB8 | `shutil.rmtree(thu_muc_tam)` → `pass` | `:553` | 1 failed, 33 passed | `test_dong33` | đúng |
| [18] ĐB9 | chèn `shutil.rmtree(ra_dir, ignore_errors=True);` trước `thu_muc_tam.mkdir` | `:554` | 1 failed, 33 passed | `test_dong31` | đúng, `test_dong32` vẫn xanh |
| [19] ĐB10 | bỏ dấu chấm khỏi tên thư mục tạm | `_duong_dan_thu_muc_tam` (`:364-375`) | 1 failed, 33 passed | `test_dong33` | đúng — §4.4 **có** người gác |
| [20] ĐB11 | `if args.dry_run:` → `if False and args.dry_run:` | `:531` | 2 failed, 32 passed | `test_dong19`, `test_dong34` | đúng |

Bảy phép phủ đủ bảy chốt chịu lực của mã việc: lớp ngoại lệ (ĐB5), biên số ảnh (ĐB6), dọn thư mục
tạm ở nhánh `except` (ĐB7), dọn tàn dư đầu lượt (ĐB8), **không đụng gallery cũ trước khi lượt mới
xong** (ĐB9 — dựng lại đúng chế độ hỏng mà §4.3 loại bỏ), quy ước tên có dấu chấm (ĐB10), và
`--dry-run` không tạo thư mục nào (ĐB11). **Không phép nào xanh.**

**ĐB6 — bốn ca đỏ, và cơ chế đọc được từ đầu ra.** Khi toán tử thành `<=`, lỗi mô hình của người có
số ảnh **bằng đúng** ngưỡng bị nuốt thành `thieu_anh`, nên `main` trả về `0` thay vì `1`; ba ca 27,
28, 31 đều khẳng định `ma == 1` nên đỏ theo. Đầu ra của `test_dong36` cho thấy đúng chế độ hỏng mà
§4.6 mô tả: bảng tổng kết in `da_dang_ky 0 / thieu_anh 1` và lượt chạy **vẫn ghi gallery thành
công** — người đủ ảnh biến mất khỏi gallery không một tiếng động, mã trả về `0`. Đây là loại lỗi
im lặng mà CHẶN-B-1 của `P3-03` tồn tại để chặn; nay nó có người gác.

**ĐB7 và ĐB9 — các ca không chồng nhau.** ĐB7 chỉ làm ca 28 đỏ trong khi ca 27 vẫn xanh: hai ca soi
hai thứ khác nhau (thư mục **đích** không được tạo · thư mục **tạm** không được sót) đúng như đặc tả
phân công, không phải hai bản sao của một chốt. ĐB9 chỉ làm ca 31 đỏ trong khi ca 32 vẫn xanh: ca 32
(thay thế gallery cũ bằng lượt mới **thành công**) không phân biệt được chế độ hỏng "xoá gallery cũ
ngay đầu lượt", và nó không cần phân biệt — ca 31 mới là ca canh chỗ đó. Bộ mười ca định vị được
lỗi, không đỏ lan man.

### 1.5. ⭐ Hai phép từng chứng minh bộ test cũ mù, nay đều bị bắt

Đây là lý do tồn tại của §4.5 và §4.6 đặc tả, nên phải đo lại đúng hai phép ấy chứ không phép nào
khác:

| Phép | `P3-03` vòng 2 (05/09, trước mã việc) | `P3-04` vòng 1 (05/09, sau mã việc) |
|---|---|---|
| `raise LoiMoHinh(` → `raise LoiCauHinh(` | ĐB8: **19 passed, 0 failed** — không ca nào đỏ ❌ | [14] ĐB5: **1 failed** — `test_dong35` ✅ |
| `so_anh_tim_thay <` → `<=` | ĐB9: **19 passed, 0 failed** — không ca nào đỏ ❌ | [15] ĐB6: **4 failed** — gồm `test_dong36` ✅ |

Hai dòng này là bằng chứng trực tiếp rằng §12.2 và §12.3 của `docs/review/P3-03-enroll.review.md`
**đã được đóng lại thật**. Ý nghĩa vượt ra ngoài mã việc: nó xác nhận vòng lặp đột biến của quy
trình có hiệu lực khép kín — một chỗ mù được đo ra ở lượt review trước, được viết thành yêu cầu
trong đặc tả, được cài đặt, và lượt review sau đo lại bằng **đúng phép cũ** thấy nó đã đóng. Không
mục 🔵 nào của `P3-03` được đóng bằng lời khai.

---

## 2. Đối chiếu đặc tả

### 2.1. Bảng tổng hợp

| Mục | Kết luận | Bằng chứng |
|---|---|---|
| §2 Danh sách trắng | ✅ đúng hai tệp, không đụng `src/`, `configs/`; `tests/` chỉ xoá đúng ba dòng §4.5 yêu cầu | [7] [8] |
| §4.1 Bất biến hai trạng thái | ✅ `ra_dir` chỉ xuất hiện qua `_doi_ten_nguyen_khoi` (`:614`), sau khi cả ba loại tệp đã ghi xong | ca 27, 29, 30 · ĐB6, ĐB9 |
| §4.2 điều 1 — dọn tàn dư rồi tạo lại | ✅ `:552-554` | ca 33 · ĐB8 |
| §4.2 điều 2 — ghi cả ba vào thư mục tạm | ✅ `.npy` `:575-576` · `manifest.csv` `:581` · `gallery.meta.json` `:608-610` | ca 29 |
| §4.2 điều 3 — đổi tên sau khi ghi xong | ✅ `:614` gọi `_doi_ten_nguyen_khoi`; ba bước `.cu` → rename → xoá `.cu` ở `:411-427` | [10] · ca 31, 32 |
| §4.2 điều 4 — dọn thư mục tạm ở mọi nhánh thoát sớm | ✅ hai nhánh `except` `:615-624`, cả lỗi phát sinh giữa bước 3 | ca 28 · ĐB7 |
| §4.2 — không `os.replace` lên đích tồn tại | ✅ không có `os.replace` trong tệp; đích của cả hai `os.rename` luôn là vị trí **không tồn tại** | [10] · docstring `:396-399` |
| §4.3 Chọn phương án thư mục tạm | ✅ gallery cũ không bị đụng tới cho tới khi lượt mới chắc chắn xong | ca 31 (so `sha256`) · ĐB9 |
| §4.4 Quy ước tên có dấu chấm | ✅ hằng số có tên `_HAU_TO_THU_MUC_DANG_GHI`, `_HAU_TO_THU_MUC_CU` (`:72-73`) kèm comment `:67-71` nêu rõ bước 3.5 phải bỏ qua thư mục con bắt đầu bằng `.` | ĐB10 |
| §4.5 điều 1 — ca gọi thẳng `xu_ly_mot_nguoi` | ✅ `test_dong35` dùng `pytest.raises(LoiMoHinh)`, không đi qua `main()` | ĐB5 |
| §4.5 điều 2 — bỏ nhánh chết | ✅ `tests/test_enroll.py:318` `assert not manifest.exists()` | [8] |
| §4.6 Biên `so_anh == ngưỡng` | ✅ **có người gác** (ĐB6 đỏ), nhưng ca cài đặt canh chiều **ngược** với câu chữ §5 dòng 36 — xem §3.2 | ĐB6 |
| §4.7 Không đổi hành vi nào khác | ✅ xem §2.7 dưới | [9] |
| §5 Bảng nghiệm thu | ✅ đủ 10/10 dòng 27–36, đặt tên `test_dongNN_*`, không ca nào `slow`, mọi ca dùng `tmp_path` | [3] [5] · đọc mã |
| §6 Lệnh tự kiểm | ✅ đủ sáu lệnh, tất cả xanh. ⚠️ con số kỳ vọng trong đặc tả sai — xem §3.1 | [1]–[5] |
| §7 Ràng buộc kỹ thuật | ✅ `black`/`ruff` sạch, không `except Exception`, ngoại lệ dùng `src/common/exceptions.py`, type hints + docstring Google tiếng Việt ở ba hàm mới (`:364-427`), không ca nào ghi vào `data/` | [1] [2] [12] · đọc mã |
| §8 Ngoài phạm vi | ✅ không đụng ca 26, không chuyển import backend vào thân `tao_bo_nhan_dien`, không sửa §12.4 (`print` + `logger.error` vẫn ở `:616-617`), không thi hành quy ước "." ở phía đọc | [7] · đọc mã |
| **R5 trung thực số liệu** | ✅ không hằng số nào trông như kết quả đo; mọi khoá meta vẫn tính từ lượt chạy | [12] · đọc mã |
| **R17 dấu vết** | ✅ khối meta 13 khoá giữ nguyên, nay chỉ đổi **chỗ** ghi | ca 12, 13, 14 vẫn xanh |
| **Fail-safe phần cứng** | không áp dụng — mã việc không chạm GPIO/camera/relay | — |

### 2.2. §4.7 — kiểm "không đổi hành vi nào khác" bằng cách đọc 32 dòng bị xoá

[9] liệt kê 32 dòng bị xoá khỏi `scripts/enroll.py`. Đối chiếu từng nhóm với mã hiện tại:

| Dòng cũ bị xoá | Đi đâu | Hệ quả hành vi |
|---|---|---|
| `ra_dir.mkdir(parents=True, exist_ok=True)` | **bỏ hẳn**, thay bằng `thu_muc_tam.mkdir(parents=True)` `:554` | đúng mục tiêu §4.1: `ra_dir` không còn được tạo sớm |
| dòng dựng `duong_dan_npy` | `:575`, đổi `ra_dir` → `thu_muc_tam` | không đổi tên tệp, không đổi `tep_ra` (vẫn `.name`) |
| `ghi_manifest(...)` | `:581`, vào **trong** khối `try`, đích là thư mục tạm | nội dung manifest không đổi |
| khối `so_nguoi_da_dang_ky` / `so_nguoi_bo_qua` | `:583-584`, vào trong `try` | công thức không đổi |
| khối dựng `meta` + ghi `gallery.meta.json` | `:586-610`, vào trong `try`, đích là thư mục tạm | 13 khoá không đổi, thứ tự không đổi |

Bảng tổng kết stdout (`:629-639`) giữ nguyên và vẫn in đường dẫn **đích cuối cùng**
(`ra_dir / "manifest.csv"`), không phải đường dẫn tạm — đúng thứ người chạy cần. Mã trả về 0/1 và
thứ tự xử lý người không đổi. Ba mươi hai dòng đều **chuyển chỗ**, không dòng nào mất.

Một thay đổi hành vi phụ, **đúng hướng và không vi phạm §4.7**: `ghi_manifest` nay nằm trong khối
`try`, nên một `LoiCauHinh` từ nó (bản ghi thiếu khoá) chuyển từ *traceback thô* thành *thông báo
tiếng Việt + dọn thư mục tạm + `return 1`*. Đây chính là thứ §4.2 điều 4 đòi hỏi ở "mọi nhánh thoát
sớm", không phải hành vi bị cấm đổi.

---

## 3. Khuyết tật của **đặc tả** — không phải của mã

Hai mục dưới đây không phải lỗi của người cài đặt: mã làm đúng, thậm chí đúng hơn câu chữ. Ghi
thành mục riêng vì đặc tả là tài liệu được đọc lại khi viết mã việc sau, và cả hai đều có thể làm
người đọc sau kết luận sai.

### 3.1. 🔵 §3 và §6 ghi sai số ca — người cài đặt có thể tưởng bộ test thiếu ca

**Vị trí**: `docs/dac-ta/P3-04-enroll-ghi-nguyen-khoi.md:58` ("Số test `tests/test_enroll.py` hiện
tại | 19 ca") và `:192` ("Kết quả mong đợi: **29 passed** (19 ca cũ + 10 ca mới)").

**Số đúng**: 24 ca cũ, **34** sau mã việc. `tests/test_enroll.py` trên `dev` có 22 hàm `test_`,
trong đó `test_dong16` mang `@pytest.mark.parametrize` ba giá trị nên thu thập **24 ca**; cộng 10 ca
mới thành 34, đúng [3] và [6].

**Nguồn gốc con số 19**: 24 − 5 ca `slow` = 19. Đó là số ca của các **lượt đột biến** ở `P3-03` vòng
2 (ĐB8, ĐB9 đều báo `19 passed`), tức số ca **không** `slow`. Đặc tả chép con số ấy vào ô "số test
hiện tại" mà mất chữ "không slow", rồi cộng 10 thành 29.

**Vì sao đáng ghi**: 29 chỉ đúng ở môi trường **không có `models/`** (năm ca `slow` tự `skip`, cho
`29 passed, 5 skipped`). Nhưng lệnh §6 dòng 189 là `pytest tests/test_enroll.py -v` **không** lọc
marker, chạy trên máy phát triển có trọng số thì phải ra 34. Người cài đặt thấy 34 ≠ 29 có hai lối
sai đối nghịch nhau: tưởng mình viết thừa ca, hoặc tưởng có ca lạ chen vào. Cả hai đều tốn một
vòng bàn giao cho một con số không liên quan gì tới mã.

**Sửa** (việc của `spec-writer`, không chặn commit): §3 ghi `24 ca (19 ca không slow + 5 ca slow)`;
§6 ghi kỳ vọng `34 passed trên máy có models/, hoặc 29 passed + 5 skipped khi thiếu models/`.

### 3.2. 🔵 §5 dòng 36 và §4.6 mô tả một ca **không thể** bắt được ĐB6 — mã đã đi đúng, đặc tả sai

**Vị trí**: đặc tả `:138-139` (§4.6) và `:165` (§5 dòng 36) — *"backend giả trả vectơ hợp lệ → mã
trả về `0`, `trang_thai == da_dang_ky`, có tệp `.npy`"*. Cài đặt: `tests/test_enroll.py:853-875`
dùng `_BackendLoiMoHinhGia` và khẳng định ngược lại — `ma == 1`, `not (ra / "dlib").exists()`.

**Vì sao cài đặt đúng còn đặc tả sai**: chốt cần canh nằm ở `scripts/enroll.py:214`, **bên trong**
khối `except ValueError`. Với một backend trả vectơ hợp lệ, `enroll()` không hề ném `ValueError`,
dòng 214 không bao giờ chạy, nên đổi `<` thành `<=` **không đổi kết quả** — ca 36 phiên bản đặc tả
sẽ xanh dưới ĐB6, tái lập đúng chỗ mù mà §4.6 sinh ra để bịt. Đặc tả tự mâu thuẫn: §5 dòng 36 mô tả
một ca mà §6.2 (*"ĐB6 … phải đỏ; nếu vẫn xanh thì ca 36 chưa canh đúng chỗ — sửa ca test, đừng sửa
mã sản phẩm"*) đòi phải đỏ.

Người cài đặt chọn đúng vế mà đặc tả nói là chịu lực, và [15] đo được kết quả: `test_dong36` đỏ
dưới ĐB6. Docstring ca 36 (`:854-864`) giải thích rành mạch lý do chệch câu chữ — chệch **có ghi
chép**, không phải chệch âm thầm.

**Không mất chốt nào**: chiều dương mà §5 dòng 36 muốn (*người có đúng ngưỡng ảnh vẫn được đăng
ký*) đã có người gác sẵn ở ba ca dùng cấu hình 3 ảnh / ngưỡng 3 — `test_dong11` (`trang_thai ==
da_dang_ky`), `test_dong29` (`.npy` tồn tại), `test_dong33` (`ma == 0` và có `.npy`). Nếu toán tử
bị đổi theo chiều ngược lại, ba ca này đỏ.

**Sửa** (việc của `spec-writer`): §4.6 và §5 dòng 36 phải mô tả backend **luôn ném `ValueError`**
với `so_anh` bằng đúng ngưỡng, kỳ vọng `ma == 1`; ghi thêm rằng chiều dương do ca 11/29/33 canh.

---

## 4. Mục lỗi

**Không có mục 🔴 CHẶN-A, không có mục 🔴 CHẶN-B, không có mục 🟡 CẦN SỬA.**

Các nhóm đã soi riêng và không tìm thấy vi phạm: hardcode tham số thực nghiệm (không hằng số mới
nào; ngưỡng vẫn đi qua `--toi-thieu`/`enroll.min_images_per_user`), `print()` trong `src/` (mã việc
không đụng `src/`), nuốt lỗi im lặng ([12] rỗng; hai nhánh `except` đều `logger.error` + `print` +
`return 1`), rò rỉ tài nguyên (`open()` dùng context manager ở `:609`), test giả ([12] rỗng; mười ca
mới đều có khẳng định thật và đều được ít nhất một phép đột biến làm đỏ), trung thực số liệu (R5),
dữ liệu cấm lọt git (R25).

---

## 5. Ghi nhận không chặn

### 5.1. 🔵 `scripts/enroll.py:427` — báo thất bại cho một lượt đã thành công

**Vị trí**: `scripts/enroll.py:426-427`

```python
    if gallery_cu_da_doi_ten:
        shutil.rmtree(thu_muc_cu)
```

**Vì sao**: tới dòng này, cả hai phép `os.rename` đã xong — gallery mới đã nằm đúng chỗ và đủ ba
loại tệp, tức **bất biến §4.1 đã thoả**. Nếu `shutil.rmtree` ném `OSError` (trên Windows: một tệp
`.npy` của gallery cũ còn bị giữ handle, thư mục đang mở trong Explorer, quét virus khoá tệp),
ngoại lệ lan lên `main`, rơi vào `except OSError` `:620-624`, in *"Đăng ký thất bại khi ghi gallery
ra đĩa"* và **trả về `1`** — trong khi kết quả thực tế đã đúng. Kèm theo, `.<backend>.cu` còn lại
trên đĩa.

**Vì sao vẫn không chặn**, ba lý do:

1. Chiều lỗi là **báo hỏng cho lượt tốt**, ngược với chiều nguy hiểm (*báo tốt cho lượt hỏng*) mà cả
   `P3-03` CHẶN-B-1 lẫn mã việc này tồn tại để chặn. Không có con số sai nào đi vào `results/` hay
   báo cáo: gallery mới vẫn mang `gallery.meta.json` đầy đủ, chuỗi truy vết R6 nguyên vẹn.
2. Tàn dư `.<backend>.cu` vô hại theo đúng quy ước §4.4 (bước 3.5 bỏ qua thư mục con bắt đầu bằng
   `.`), và bị xoá ở lượt chạy kế tiếp tại `:411-412`.
3. Đặc tả không quy định hành vi cho tình huống này, và không ca nào chạm tới nhánh — xếp mức chặn ở
   đây là **mở rộng đặc tả trong lúc review**, thứ chuẩn review §5 cấm.

**Sửa** (nếu người dùng muốn, chi phí ba dòng): bọc riêng bước dọn cuối, vì nó nằm **sau** điểm bất
biến đã thoả.

```python
    if gallery_cu_da_doi_ten:
        try:
            shutil.rmtree(thu_muc_cu)
        except OSError as e:
            logger.warning("Không xoá được gallery cũ '%s', để lại tàn dư: %s", thu_muc_cu, e)
```

**Ghi chú kề bên, cùng họ**: nếu `os.rename(thu_muc_tam, ra_dir)` `:420` hỏng **và** phép hoàn tác
`:423` cũng hỏng, gallery cũ nằm lại ở `.<backend>.cu` và sẽ bị `:411-412` của lượt sau xoá. Ở thời
điểm ấy hệ tệp đã hỏng nặng và `ra_dir` cũng không còn, nên không có phương án nào tốt hơn ngoài
chạy lại — ghi lại để người đọc sau không tưởng đây là chỗ chưa ai nghĩ tới.

### 5.2. 🔵 `tests/test_enroll.py:706` — `if ra.exists():` là đúng cái khuôn mà §4.5 vừa dọn

**Vị trí**: `tests/test_enroll.py:706-708` (ca 28)

```python
    if ra.exists():
        ten_con = [p.name for p in ra.iterdir()]
        assert not any(ten.startswith(".") for ten in ten_con)
```

**Vì sao**: `ra` **luôn** tồn tại sau một lượt hỏng — `thu_muc_tam.mkdir(parents=True)` `:554` tạo
ra nó như thư mục cha, và không nhánh nào xoá nó. [16] chứng minh khối này đang **sống**: ĐB7 làm ca
28 đỏ. Nhưng cấu trúc thì y hệt khối `if manifest.exists():` mà §4.5 điều 2 vừa yêu cầu dọn: nếu
một mã việc sau cho `enroll.py` dọn luôn `ra_dir_goc` khi lượt chạy hỏng, ca 28 sẽ **im lặng không
khẳng định gì** và vẫn xanh — mất chốt mà không ai biết.

**Sửa** (một dòng, gộp vào mã việc test kế tiếp): bỏ `if`, khẳng định thẳng, vì điều kiện đã biết
chắc là đúng.

```python
    ten_con = [p.name for p in ra.iterdir()]
    assert not any(ten.startswith(".") for ten in ten_con)
```

Ca 29 (`:725-726`) đã viết đúng dạng này — chỉ ca 28 lệch khuôn.

### 5.3. 🔵 `scripts/enroll.py:552-554` nằm ngoài khối `try` — lỗi ở bước 1 cho traceback thô

**Vị trí**: `scripts/enroll.py:552-554`

```python
    if thu_muc_tam.exists():
        shutil.rmtree(thu_muc_tam)  # tàn dư của lượt hỏng trước đó (§4.2 điều 1)
    thu_muc_tam.mkdir(parents=True)
```

**Vì sao**: khối `try` bắt đầu ở `:563`, nên `OSError` phát sinh ở ba dòng này không được xử lý.
Tình huống dựng được: `.<backend>.dang-ghi` tồn tại dưới dạng **tệp** thay vì thư mục — `exists()`
trả `True`, `shutil.rmtree` ném `NotADirectoryError`. Người chạy nhận traceback thay vì thông báo
tiếng Việt như mọi nhánh lỗi khác của script. Mã thoát vẫn khác `0` (Python trả `1` khi ngoại lệ
thoát ra ngoài), nên không có lượt hỏng nào bị báo là thành công.

Đặc tả §4.2 điều 4 chỉ nói tới nhánh `except` và lỗi phát sinh giữa bước 3, không phủ bước 1 — nên
đây là **góp ý**, không phải thiếu sót so với yêu cầu. Sửa: đưa ba dòng vào trong khối `try` hiện
có, hoặc bọc riêng bằng `except OSError` in cùng khuôn thông báo với `:620-624`.

---

## 6. Việc tiếp theo

### 6.1. Sau khi gộp — bắt buộc

| # | Việc | Ai làm |
|---|---|---|
| 1 | Commit hai tệp `scripts/enroll.py`, `tests/test_enroll.py`; gộp `feat/p3-04-enroll-ghi-nguyen-khoi` vào `dev`. Gợi ý message: `fix(enroll): ghi gallery nguyên khối qua thư mục tạm, siết hai chốt kiểm thử — P3-04` | người dùng |
| 2 | **Chạy §9 đặc tả trên mã đã gộp**: xoá `data/embeddings/`, chạy lại hai lượt `enroll` (dlib, arcface) với `--toi-thieu 3`, rồi liệt kê thư mục. Kỳ vọng: đúng hai thư mục con `dlib` và `arcface`, mỗi bên 8 tệp `.npy` + `manifest.csv` + `gallery.meta.json`, **không thư mục nào bắt đầu bằng dấu chấm**, `git_dirty: false`, `commit` trỏ vào commit gộp | người dùng |

Mục 2 là mục còn nợ từ §14.1 biên bản `P3-03` (chạy lại §11b trên mã cuối), nay gộp làm một vì mã
việc này lại đổi `scripts/enroll.py`. **Phải xong trước khi bất kỳ số nào từ `data/embeddings/` đi
vào bước 3.5.**

### 6.2. Mã việc riêng cho `spec-writer` — không chặn gộp

| Nguồn | Nội dung | Ưu tiên |
|---|---|---|
| 🔵 §3.1 + §3.2 | **Sửa chính đặc tả `P3-04`**: số ca ở §3/§6, và ca 36 ở §4.6/§5 cho khớp mã đã cài (kèm lý do). Đặc tả là tài liệu tham chiếu của mã việc sau, để sai là để lại bẫy | **cao** — chi phí gần bằng 0, làm ngay |
| 🔵 §5.1 | Bọc `try/except OSError` quanh bước dọn `.<backend>.cu` (`:426-427`) | trung bình |
| 🔵 §5.2 | Bỏ `if ra.exists():` ở ca 28, khẳng định thẳng như ca 29 | trung bình — gộp cùng mã việc test kế tiếp |
| 🔵 §5.3 | Đưa `:552-554` vào diện xử lý `OSError` | thấp |
| 🔵 §4.2 `P3-03` vòng 1 | Ca 26 so danh tính byte thay vì đếm lời gọi | trung bình — treo tiếp |
| 🔵 §4.1 `P3-03` vòng 1 | Gỡ phụ thuộc cứng `onnxruntime` khỏi `src.recognizer` | trung bình — treo tiếp |
| 🔵 §4.5, §4.7 `P3-03` vòng 1 | `kiem_ten_nguoi_hop_le` cần ca nghiệm thu khi tái dùng ở bước 6.3 · đăng ký marker `slow` trong `pyproject.toml` | thấp — treo tiếp |

Ba mục 🔵 mới (§5.1–§5.3) đều nhỏ và cùng họ "nhánh lỗi hiếm + khuôn ca test"; nên gộp thành **một**
mã việc dọn dẹp thay vì ba, và có thể xếp sau bước 3.5 — không mục nào chặn việc nạp
`data/embeddings/`.

---

## 7. Phán quyết — vòng 1

🟡 **ĐẠT CÓ ĐIỀU KIỆN**. Không mục 🔴 CHẶN-A, không 🔴 CHẶN-B, không 🟡 CẦN SỬA. Ba mục 🔵 ở §5 và
hai khuyết tật của **đặc tả** ở §3. **Được commit và gộp vào `dev`.**

Lập luận:

1. **Bảy điều của §4 đặc tả đều được cài đặt và đều có người gác đo được** (§2.1). Không guard nào
   rơi vào trạng thái "xanh vì không ca test nào chạy qua": bảy phép đột biến, bảy lần đỏ, và các ca
   không chồng lên nhau (ĐB7 tách ca 27/28, ĐB9 tách ca 31/32).
2. **Hai chỗ mù đo được ở lượt trước nay đã đóng** (§1.5) — bằng đúng hai phép đột biến đã từng cho
   `19 passed, 0 failed`, nay cho 1 và 4 ca đỏ. Đây là điều kiện nghiệm thu thực chất nhất của mã
   việc, vì §4.5 và §4.6 sinh ra chỉ để bịt hai chỗ ấy.
3. **§4.7 giữ đúng**: 32 dòng bị xoá đều truy được về vị trí mới (§2.2), bảng tổng kết, manifest,
   meta, mã trả về và thứ tự xử lý không đổi. Thay đổi duy nhất ngoài dự kiến — `ghi_manifest` vào
   trong khối `try` — đi đúng hướng §4.2 điều 4.
4. **Phạm vi sạch**: đúng hai tệp danh sách trắng, `tests/` chỉ xoá đúng ba dòng mà §4.5 điều 2 chỉ
   định, không tệp cấm nào lọt git, cây làm việc cuối lượt rỗng.
5. **Chứng cứ ba môi trường**: 34 ca xanh trên host x86-64, container ARM64 và **Raspberry Pi 5
   thật** — mã đụng `os.rename`/`shutil.rmtree` mà chạy đúng trên ba hệ tệp khác nhau là bằng chứng
   cho chính lập luận khả chuyển ở §4.2.

Điều kiện của phán quyết 🟡:

- **§6.1 mục 2 phải chạy trước bước 3.5** — gallery hiện có ở `data/embeddings/` sinh từ `6632e79`,
  tức mã trước cả `P3-03` vòng 2 lẫn mã việc này; dùng nó cho quét ngưỡng sẽ đứt chuỗi truy vết ở
  đúng chỗ R6 quan tâm.
- **§3.1 và §3.2 phải sửa vào chính đặc tả `P3-04`**. Đây là điều kiện duy nhất mang tính bắt buộc
  ngoài mục trên: hai con số sai và một ca nghiệm thu mô tả sai chiều sẽ dạy sai cho mã việc kế
  tiếp, mà mã việc kế tiếp lại đúng là bước 3.5 — nơi gallery này được nạp.

Ghi nhận về chất lượng mã việc: người cài đặt không những làm đủ bảy điều của §4 mà còn thêm nhánh
hoàn tác `:421-424` mà đặc tả không đòi, đóng nốt trạng thái *mất cả gallery cũ lẫn mới*; và khi câu
chữ §5 dòng 36 mâu thuẫn với §6.2, đã chọn vế chịu lực và **ghi rõ lý do trong docstring ca test**
thay vì im lặng đi chệch. Cả hai mục ở §3 là lỗi của khâu đặc tả, không của khâu cài đặt.
