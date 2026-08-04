# Review P0-01-nen-tang — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P0-01-nen-tang.md` |
| **Nhánh** | `feat/p0-01-nen-tang` |
| **Worktree** | `D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/wt-p0-01-nen-tang` |
| **Ngày** | 2026-08-04 |
| **Phán quyết** | 🔴 TRẢ LẠI — 1 lỗi 🟡 CẦN SỬA (không có 🔴) |

## Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short` | đúng 8 file, khớp danh sách trắng §2 ✅ |
| `git diff --stat` | rỗng (chưa commit gì, toàn bộ là file mới) ✅ |
| `python -m black --check --line-length 100 src tests` | `7 files would be left unchanged` ✅ |
| `python -m ruff check src tests` | `All checks passed!` ✅ |
| `python -m pytest -q` | `26 passed in 0.54s` ✅ (đặc tả yêu cầu ≥ 18) |

**Phạm vi file** — `git status --short --untracked-files=all` trả về đúng 8 mục:
`pyproject.toml`, `src/__init__.py`, `src/common/__init__.py`, `src/common/config.py`,
`src/common/exceptions.py`, `src/common/logging.py`, `src/common/types.py`, `tests/test_common.py`.
Không thừa, không thiếu. `docs/`, `configs/`, `report/`, `CLAUDE.md`, `requirements.txt` — **không bị chạm** ✅
`__pycache__/`, `.pytest_cache/`, `.ruff_cache/` hiện ở trạng thái `!!` (đã bị `.gitignore` chặn) — không tính vi phạm.

**Quét dữ liệu cấm lọt git**: không có file `.jpg/.png/.npy/.npz/.onnx/.pt/.pth/.env/.db/.sqlite` ✅

## Quét mẫu vi phạm (§2 `code-review.instructions.md`)

| Vi phạm | Kết quả |
|---|---|
| `print()` trong `src/` | không có ✅ |
| `except:` trần / `except Exception: pass` | không có ✅ |
| Import phần cứng đầu file (`RPi`, `pigpio`) | không có ✅ |
| `import torch` | không có ✅ |
| Log dùng f-string | không có lệnh log nào trong `src/` ✅ |
| Số magic là tham số thực nghiệm | không có — `0.95`/`0.42` chỉ xuất hiện trong test làm dữ liệu mẫu ✅ |
| Đường dẫn tuyệt đối máy cá nhân | không có ✅ |
| Secret trong code | không có; biến môi trường đọc qua `os.environ` ✅ |
| Test giả (`assert True`, `pass`) | không có — cả 26 test đều assert thật ✅ |
| Nạp model trong vòng lặp | không áp dụng ở mã việc này ✅ |

## Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §3.1 `exceptions.py` | ✅ đủ 5 lớp, đúng cây kế thừa, đúng docstring |
| §3.2 `types.py` | ✅ khớp từng ký tự — tên trường, thứ tự, kiểu, 3 property |
| §3.3 `config.py` | ✅ chữ ký khớp, sentinel `_KHONG_CO` đúng yêu cầu |
| §3.4 `logging.py` | ✅ chữ ký khớp |
| §4 Hằng số | ✅ 3 hằng số HOA đúng giá trị (`logging.py:10-12`) |
| §5.1 `nap_cau_hinh` — 10 ca | ✅ 10/10 có test |
| §5.2 `lay_gia_tri` — 5 ca | ✅ 5/5 có test |
| §5.3 `thiet_lap_log` — 6 ca | ⚠️ 6/6 có test nhưng **ca 1 assert thiếu** (xem CẦN SỬA-1) |
| §6 Nghiệm thu | 6/7 đạt (xem bên dưới) |
| §7 Quy tắc G2–G5, G10, encoding, tầng đáy | ✅ |
| §8 Ngoài phạm vi | ✅ không làm thừa việc nào |

### Kiểm chứng chạy tay bốn điểm rủi ro đặc tả nêu rõ

Không đọc mắt — chạy thật trong worktree:

```
EQ   -> True          # FaceBox(...) == FaceBox(...) với landmarks khác nhau, KHÔNG ném ValueError
HASH -> True          # frozen dataclass vẫn hash được vì landmarks bị loại khỏi compare
REPR -> FaceBox(x1=0, y1=0, x2=10, y2=10, confidence=0.9)   # landmarks bị ẩn đúng repr=False
none+default -> None  # lay_gia_tri({'a':{'b':None}}, 'a.b', mac_dinh=999) trả None, không trả 999
HANDLERS x3 -> 1 ['StreamHandler'] [True]   # gọi thiet_lap_log 3 lần vẫn đúng 1 handler, ra sys.stdout
```

- **§3.2 `compare=False`**: đạt (`src/common/types.py:26`). Đây là bẫy đặc tả cảnh báo — Gemini né đúng.
- **§5.1 `encoding="utf-8"`**: đạt. Quét toàn repo, **mọi** lần mở file đều có `encoding="utf-8"` —
  `src/common/config.py:57`, `src/common/logging.py:52`, và cả 12 lần đọc/ghi trong `tests/test_common.py`.
- **§3.3 sentinel riêng**: đạt (`src/common/config.py:12, 73, 103`). Dùng `if khoa not in hien_tai`
  chứ không dùng `if hien_tai.get(khoa) is None` — nên giá trị `None` hợp lệ được phân biệt đúng.
- **§5.3 không nhân đôi handler**: đạt (`src/common/logging.py:34-36`).

### §6 Tiêu chí nghiệm thu

- [x] `pytest -q` xanh, 26 ca ≥ 18, phủ hết ba bảng §5 *(có một assert yếu — CẦN SỬA-1)*
- [x] `black --check --line-length 100 src tests` sạch
- [x] `ruff check src tests` sạch
- [x] `python -c "from src.common.config import nap_cau_hinh; print('ok')"` → in `ok`
- [x] Test không ghi ngoài `tmp_path` — sau `pytest`, `git status --short` vẫn đúng 8 file
- [x] Chạy được trên máy không có Raspberry Pi
- [x] `git status --short` không có file ngoài danh sách trắng

## Lỗi phải sửa

### 🟡 CẦN SỬA-1 — Test ca "mặc định" của `thiet_lap_log` assert quá yếu, không khoá được yêu cầu "handler ra stdout/stderr" (CS-4)

**Vị trí**: `tests/test_common.py:224-229`

```python
def test_thiet_lap_log_default() -> None:
    """Thiết lập log mặc định với mức INFO."""
    thiet_lap_log(muc="INFO")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) >= 1
```

Đặc tả §5.3 dòng 1 yêu cầu ba điều: **đúng 1** handler · handler **ra `stdout`/`stderr`** · mức `INFO`.
Test này chỉ khoá được mức `INFO`. Điều kiện "đúng 1" bị nới thành `>= 1`, và **không test nào trong
cả 26 ca kiểm tra handler mặc định có ghi ra console hay không**.

**Vì sao**: cài đặt hiện tại ở `src/common/logging.py:40` đúng (`StreamHandler(sys.stdout)`), nhưng
bộ test không bảo vệ được điều đó. Nếu một mã việc sau đổi thành `logging.FileHandler("app.log")`,
**cả 26 test vẫn xanh** — trong khi hệ thống mất toàn bộ log console (không debug được lúc chạy trên
Pi 5 qua SSH) và lặng lẽ đẻ file `app.log` ở thư mục gốc repo, phá luôn tiêu chí nghiệm thu
"test không ghi ra ngoài `tmp_path`". `src/common/` là tầng đáy mà mọi khối khác phụ thuộc, nên
hồi quy ở đây lan ra toàn hệ thống.

**Sửa**: siết hai assert trong `test_thiet_lap_log_default`, không cần đổi code `src/`:

```python
def test_thiet_lap_log_default() -> None:
    """Thiết lập log mặc định: đúng 1 handler ra stdout/stderr, mức INFO."""
    thiet_lap_log(muc="INFO")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 1
    handler = root_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream in (sys.stdout, sys.stderr)
```

Thêm `import sys` vào phần import của file test.

**Gợi ý kèm theo (cùng file, cùng bảng §5.3 — làm luôn cho gọn một vòng)**: ca `file_log` ở
`tests/test_common.py:246-256` mới kiểm file có tồn tại và có nội dung, chưa kiểm handler đúng loại
và đúng thông số 10 MB × 3 bản mà §5.3 dòng 4 nêu. Bổ sung vào cuối test đó:

```python
    from logging.handlers import RotatingFileHandler
    from src.common.logging import KICH_THUOC_TOI_DA_FILE_LOG, SO_FILE_LOG_XOAY_VONG

    fh = [h for h in logging.getLogger().handlers if isinstance(h, RotatingFileHandler)]
    assert len(fh) == 1
    assert fh[0].maxBytes == KICH_THUOC_TOI_DA_FILE_LOG
    assert fh[0].backupCount == SO_FILE_LOG_XOAY_VONG
```

## 🔵 Góp ý (không chặn — người dùng quyết định)

- **`thiet_lap_log` xoá mọi handler của root, kể cả handler không phải do nó tạo**
  (`src/common/logging.py:34-36`). Đã kiểm chứng bằng tay: một handler do thư viện khác gắn vào root
  sẽ bị `removeHandler` (stream không bị đóng nên không hỏng dữ liệu). Cách này thoả đúng §5.3
  "không nhân đôi handler", nên **không phải lỗi**. Nhưng từ Phase 5–6 trở đi, nếu test nào dùng
  `caplog` của pytest rồi gọi `thiet_lap_log` thì `caplog` sẽ im lặng ngừng bắt log và người viết
  test sẽ mất thời gian truy nguyên. Phương án gọn hơn: gắn thuộc tính đánh dấu
  (`handler._faceid = True`) và chỉ gỡ những handler có dấu. Chi phí ~4 dòng, lợi ích là tránh một
  lớp bug khó chẩn đoán về sau. Nếu đồng ý, nên đưa thành mã việc nhỏ chứ không sửa trong vòng này.
- **`except Exception` rộng ở `src/common/config.py:61`.** Không vi phạm G5 (không phải `except:` trần,
  không nuốt lỗi — có `raise ... from e`). Tác dụng là gom `PermissionError`, `IsADirectoryError`,
  `UnicodeDecodeError` về `LoiCauHinh`, hợp lý cho một bộ nạp cấu hình. Ghi lại để không bị hiểu nhầm
  là thiếu sót ở các vòng review sau.
- **`thiet_lap_log(muc=10)` ném `AttributeError` chứ không phải `LoiCauHinh`.** Chữ ký khai
  `muc: str` nên đây là lỗi gọi sai kiểu, đặc tả không yêu cầu xử lý. Không cần sửa.

## Nhận xét về chất lượng đặc tả (đầu vào cho `spec-writer`)

Vòng chạy thử đầu tiên của quy trình 5 nhịp cho kết quả tốt: **0 lỗi CHẶN-A, 0 lỗi CHẶN-B**.
Ba chỗ đặc tả cảnh báo trước bằng chữ đậm — `compare=False`, sentinel riêng, `encoding="utf-8"` —
Gemini làm đúng cả ba. Kết luận rút ra: **cảnh báo đặt trong ô bảng hoặc in đậm thì được thực thi;
điều kiện chôn trong văn xuôi thì dễ trôi.**

Điểm cần chỉnh cho các mã việc sau — đúng một điểm, và nó gây ra lỗi 🟡 duy nhất ở trên:

- **Bảng ca biên §5 mô tả *hành vi*, nhưng không nói rõ *phải assert gì*.** Dòng 1 của §5.3 gộp ba
  điều kiện vào một ô ("đúng 1 handler ra stdout/stderr, mức INFO"); Gemini cài đặt đúng cả ba nhưng
  chỉ assert một. Đặc tả không sai, chỉ là chưa đủ ràng buộc.
  **Đề xuất**: tách mỗi điều kiện thành một dòng riêng trong bảng §5, và thêm một cột **"Assert tối thiểu"**
  ghi thẳng biểu thức, ví dụ `len(root.handlers) == 1`. Ràng buộc theo biểu thức thì máy kiểm được,
  không phụ thuộc cách diễn giải.
- **Tiêu chí "tối thiểu 18 ca test" nên đổi thành yêu cầu phủ theo dòng bảng** ("mỗi dòng ở §5 có ít
  nhất một test, đặt tên theo dòng đó"). Đếm số ca test khuyến khích chia nhỏ test lấy số lượng thay
  vì siết chất lượng assert — ở đây có 26 ca nhưng vẫn lọt một điều kiện không được kiểm.

Ngoài hai điểm trên, khung đặc tả (danh sách trắng → interface nguyên văn → bảng ca biên → tiêu chí
nghiệm thu chạy được bằng máy) hoạt động đúng thiết kế và nên giữ nguyên cho `P0-02`.

## Việc tiếp theo

Giao lại Gemini **một việc duy nhất**, chỉ đụng `tests/test_common.py`, **không sửa file nào trong `src/`**:

> Sửa `tests/test_common.py` theo mục CẦN SỬA-1 trong `docs/review/P0-01-nen-tang.review.md`:
> siết assert của `test_thiet_lap_log_default` (đúng 1 handler, là `StreamHandler`, stream là
> `sys.stdout`/`sys.stderr`) và bổ sung kiểm `RotatingFileHandler` trong `test_thiet_lap_log_file_handler`.
> Chạy lại `black --check --line-length 100 src tests`, `ruff check src tests`, `pytest -q`.

Sau khi Gemini báo xong → review vòng 2, ghi **nối tiếp vào chính file này**.
Vòng 2 đạt → commit với message:

```
feat(common): module nen tang config, logging, types, exceptions (P0-01)
```

---

# Review P0-01-nen-tang — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P0-01-nen-tang.md` |
| **Nhánh** | `feat/p0-01-nen-tang` |
| **Ngày** | 2026-08-04 |
| **Phạm vi vòng này** | Gemini sửa lỗi 🟡 CẦN SỬA-1 của vòng 1 |
| **Phán quyết** | ✅ **ĐẠT** |

## Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short` | 8 file danh sách trắng + `docs/review/` (do reviewer ghi) ✅ |
| `git diff --stat` | rỗng — chưa track file nào, toàn bộ vẫn là file mới ✅ |
| `python -m black --check --line-length 100 src tests` | `7 files would be left unchanged` ✅ |
| `python -m ruff check src tests` | `All checks passed!` ✅ |
| `python -m pytest -q` | `26 passed in 0.45s` ✅ |

## 1. Lỗi 🟡 CẦN SỬA-1 — ĐÃ SỬA ĐÚNG

**Vị trí**: `tests/test_common.py:225-233`

```python
def test_thiet_lap_log_default() -> None:
    """Thiết lập log mặc định: đúng 1 handler ra stdout/stderr, mức INFO."""
    thiet_lap_log(muc="INFO")
    root_logger = logging.getLogger()
    assert root_logger.level == logging.INFO
    assert len(root_logger.handlers) == 1
    handler = root_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream in (sys.stdout, sys.stderr)
```

Đối chiếu ba điều kiện của đặc tả §5.3 dòng 1:

| Điều kiện §5.3 dòng 1 | Assert tương ứng | Kết luận |
|---|---|---|
| **đúng 1** handler | `len(root_logger.handlers) == 1` (dòng 230) | ✅ |
| handler **ra `stdout`/`stderr`** | `isinstance(..., StreamHandler)` + `handler.stream in (sys.stdout, sys.stderr)` (dòng 232-233) | ✅ |
| mức `INFO` | `root_logger.level == logging.INFO` (dòng 229) | ✅ |

`import sys` đã được thêm đúng chỗ (`tests/test_common.py:4`), không phải import cục bộ trong hàm.

**Gợi ý kèm theo cũng đã làm**: `tests/test_common.py:262-269` bổ sung kiểm `RotatingFileHandler`
đúng loại và đúng thông số, đối chiếu **trực tiếp với hằng số module** `KICH_THUOC_TOI_DA_FILE_LOG`
và `SO_FILE_LOG_XOAY_VONG` thay vì chép lại số `10*1024*1024`/`3` — cách này không tạo ra nguồn sự
thật thứ hai cho hằng số, tốt hơn đề xuất trong biên bản vòng 1.

### Kiểm chứng assert mới có "răng" thật (mutation check)

Không chỉ xác nhận test xanh — chạy chính khối assert mới lên sáu trạng thái root logger giả lập,
để chứng minh nó **bắt được** đúng hồi quy đã cảnh báo ở vòng 1:

```
impl DUNG  StreamHandler(sys.stdout)  -> TEST QUA (khong bat duoc)   <- đúng, phải cho qua
impl DUNG  StreamHandler(sys.stderr)  -> TEST QUA (khong bat duoc)   <- đúng, phải cho qua
impl SAI   FileHandler(app.log)       -> TEST TRUOT (bat duoc loi)   <- chính hồi quy vòng 1 cảnh báo
impl SAI   RotatingFileHandler        -> TEST TRUOT (bat duoc loi)
impl SAI   StreamHandler(StringIO)    -> TEST TRUOT (bat duoc loi)
impl SAI   nhan doi 2 handler         -> TEST TRUOT (bat duoc loi)
```

Đây là điểm mấu chốt: `RotatingFileHandler` và `FileHandler` **đều là lớp con của `StreamHandler`**,
nên riêng `isinstance` không đủ để phân biệt. Chính assert `handler.stream in (sys.stdout, sys.stderr)`
mới là cái chặn được. Bộ assert hiện tại vừa đủ chặt (loại 4/4 cài đặt sai) vừa không quá chặt
(chấp nhận cả `stdout` lẫn `stderr` đúng như đặc tả cho phép).

## 2. Gemini có làm ngoài phạm vi không? — KHÔNG

Lệnh N4 chỉ cho phép sửa `tests/test_common.py`. `git diff --stat` rỗng (chưa file nào được track),
nên kiểm bằng **dấu thời gian sửa file**:

```
2026-08-04 23:25:33  tests/test_common.py      <- duy nhất file được sửa ở vòng 2
2026-08-04 23:00:42  src/common/config.py
2026-08-04 23:00:42  src/common/logging.py
2026-08-04 23:00:42  src/common/types.py
2026-08-04 22:59:20  src/common/exceptions.py
2026-08-04 22:59:18  src/common/__init__.py
2026-08-04 22:59:16  src/__init__.py
2026-08-04 22:59:13  pyproject.toml
```

Toàn bộ `src/` và `pyproject.toml` giữ nguyên mốc 22:59–23:00 của vòng 1, cách lần sửa test 25 phút.
**Không file nào trong `src/` bị đụng vào** ✅ — đúng ranh giới: lỗi nằm ở test thì sửa test, không
nới lỏng code cho vừa test (tránh CB-6).

Số file vẫn đúng 8 mục danh sách trắng §2. File thứ 9 là `docs/review/P0-01-nen-tang.review.md` —
do `code-reviewer` ghi theo CLAUDE.md §2.9, **không tính** là Gemini vi phạm danh sách trắng.

## 3. Kiểm hồi quy — assert `== 1` có gây phụ thuộc thứ tự test không? KHÔNG

Đây là rủi ro thật khi siết `>= 1` thành `== 1`: nếu handler tích luỹ giữa các ca thì test sẽ đỏ
tuỳ thứ tự chạy. Đã loại trừ bằng năm phép chạy:

| Phép chạy | Kết quả |
|---|---|
| `pytest -q` (thứ tự khai báo) | `26 passed` ✅ |
| `pytest -q -p no:randomly` | `26 passed` ✅ (ghi chú: `pytest_randomly` **không** được cài, nên hai phép này tương đương) |
| `pytest -q tests/test_common.py::test_thiet_lap_log_default` (chạy riêng lẻ) | `1 passed` ✅ |
| Thứ tự **xấu nhất**: `test_thiet_lap_log_file_handler` ngay trước `test_thiet_lap_log_default` | `2 passed` ✅ |
| Đảo ngược toàn bộ 6 ca nhóm logging | `6 passed` ✅ |

**Lý do về mặt thiết kế** (không chỉ là quan sát may mắn): `thiet_lap_log` gỡ sạch handler cũ ở
`src/common/logging.py:34-36` **trước khi** thêm handler mới, và `test_thiet_lap_log_default` gọi
`thiet_lap_log` ở dòng đầu tiên. Nên trạng thái root logger luôn được đặt lại bất kể ca nào chạy
trước — kể cả ca vừa gắn `RotatingFileHandler`. Assert `== 1` **không tạo phụ thuộc thứ tự**.

## 4. Tiêu chí nghiệm thu §6 — 7/7 ĐẠT

- [x] `pytest -q` xanh, 26 ca ≥ 18, phủ hết ba bảng §5 — **ca §5.3 dòng 1 nay phủ đủ cả ba điều kiện**
- [x] `black --check --line-length 100 src tests` sạch
- [x] `ruff check src tests` sạch
- [x] `python -c "from src.common.config import nap_cau_hinh; print('ok')"` → in `ok`
- [x] Test không ghi ngoài `tmp_path` — chạy lại `pytest` xong, `git status --short` không sinh file mới
- [x] Chạy được trên máy không có Raspberry Pi
- [x] `git status --short` không có file ngoài danh sách trắng

## 5. Tổng kết lỗi vòng 2

| Mức | Số lượng |
|---|---|
| 🔴 CHẶN-A | **0** |
| 🔴 CHẶN-B | **0** |
| 🟡 CẦN SỬA | **0** |
| 🔵 GÓP Ý | 3 (chuyển nguyên từ vòng 1, **không chặn**) |

Không phát hiện lỗi mới nào phát sinh từ bản sửa. Ba mục 🔵 GÓP Ý của vòng 1 vẫn giữ nguyên hiệu
lực và **không phải lý do trả lại** — người dùng quyết định có chuyển thành mã việc riêng hay không.
Mục đáng cân nhắc nhất là góp ý số 1 (`thiet_lap_log` gỡ cả handler của thư viện khác), nên xử lý
trước khi Phase 5–6 bắt đầu viết test dùng `caplog`.

## 6. Ghi nhận về quy trình 5 nhịp

Chu trình đầu tiên khép kín trong **2 vòng, không chạm trần**:
đặc tả → sinh mã → review (1 lỗi 🟡) → sửa đúng phạm vi → ĐẠT.

Điều đáng ghi lại: bản sửa **chỉ động vào đúng file được chỉ định**, không "sửa lan" sang `src/` và
không nới lỏng assert để test đi qua. Đây là dấu hiệu biên bản review có đủ ba thành phần
(`file:dòng` + hậu quả + đoạn code thay thế) thì Gemini thực thi được mà không cần đối thoại thêm —
đúng giả định của R39.

Hai đề xuất chỉnh khung đặc tả nêu ở vòng 1 (thêm cột **"Assert tối thiểu"**; đổi tiêu chí đếm số
ca test thành **phủ theo dòng bảng §5**) vẫn giữ nguyên giá trị, nên áp dụng ngay từ `P0-02`.

## Việc tiếp theo

**Đã ĐẠT — được phép commit** vào `feat/p0-01-nen-tang` rồi gộp về `dev` theo R30.

Commit message gợi ý theo R29 (`<loại>(<phạm vi>): <mô tả>`):

```
feat(common): module nen tang config, logging, types, exceptions — P0-01-nen-tang
```

Nếu muốn tách biên bản review thành commit riêng cho gọn lịch sử:

```
docs(review): bien ban kiem dinh 2 vong — P0-01-nen-tang
```

Sau khi gộp `dev`: Phase 0 còn bước 0.2 (`requirements.txt`) và 0.3 (Docker ARM64) — viết đặc tả
`P0-02` bằng agent `spec-writer`, nhớ áp dụng hai điều chỉnh khung nêu ở §6.
