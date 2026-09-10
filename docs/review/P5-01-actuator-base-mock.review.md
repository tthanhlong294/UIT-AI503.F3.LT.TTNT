# Review P5-01-actuator-base-mock — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P5-01-actuator-base-mock.md` |
| **Nhánh** | `feat/p5-01-actuator-base-mock` (đỉnh `e18caee`) |
| **Ngày** | 2026-09-10 |
| **Mã nguồn xét** | `src/actuator/{__init__,base,mock_actuator,factory}.py`, `tests/test_actuator.py` — cả năm còn ở dạng tệp chưa theo dõi |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — không còn 🔴 và 🟡, còn 3 mục 🔵. Được commit ngay, không phải sửa gì trước khi commit |

---

## 1. Kết quả kiểm máy

**Người dùng chạy ngày 10/09/2026**, đủ **49/49 khối**. Lệnh chép nguyên văn dưới đây; mọi con số
trong biên bản này truy được về đúng một dòng trong bảng.

### 1.1. Phạm vi thay đổi

| # | Lệnh | Kết quả |
|---|---|---|
| [1/49] | `git status --short --untracked-files=all` | đúng 5 dòng `??`, trùng khít danh sách trắng §2 ✅ |
| [2/49] | `git diff --name-only dev` | rỗng — không sửa tệp đã có ✅ |
| [3/49] | `git status --short --untracked-files=all` lọc `\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$` | rỗng — không dữ liệu cấm ✅ |

`configs/actuator.yaml` và `docs/dac-ta/P5-01-actuator-base-mock.md` **không** xuất hiện ở [1/49] —
đúng cảnh báo §9.2 đặc tả, người cài đặt không chạm tệp của `spec-writer`.

### 1.2. Ba lệnh nền và hai lượt container

| # | Lệnh | Kết quả |
|---|---|---|
| [4/49] | `python -m black --check --line-length 100 src tests` | `All done! 46 files would be left unchanged.` ✅ |
| [5/49] | `python -m ruff check src tests` | `All checks passed!` ✅ |
| [6/49] | `python -m ruff check --select RUF100 src/actuator tests/test_actuator.py` | **`Found 4 errors.`** — bốn `# noqa` vô dụng ⚠️ (xem §4, 🔵 GY-1) |
| [7/49] | `python -m pytest -q` (host `pc_x86`) | `1001 passed, 3 skipped, 15 warnings in 173.72s` ✅ |
| [8/49] | `python -m pytest tests/test_actuator.py -q` | `126 passed in 0.47s`, 0 skipped, 0 failed ✅ |
| [9/49] | `python -m pytest tests/test_actuator.py --collect-only -q` (đếm `::test_`) | `126` ✅ (§9.2 đòi ≥ 126) |
| [10/49] | `docker run --rm -v "<kho>:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"` | `1 failed, 970 passed, 1 skipped, 32 deselected in 664.34s` ⚠️ — xem §5 |
| [11/49] | `docker run --rm -v "<kho>:/app" -w /app faceid:arm64 python3 -m pytest --collect-only -q tests/test_actuator.py` | `126 tests collected in 2.84s`, không lỗi import ✅ |

Đúng image `faceid:arm64` (R43), không dựng image mới.

**Phép trừ so với mốc §3.6 đặc tả** — đây mới là cách phát biểu hợp lệ, không dùng số tuyệt đối:

| Môi trường | Mốc `5a873d7` | Sau P5-01 | Mức tăng |
|---|---|---|---|
| `pc_x86` | `875 passed, 3 skipped` | `1001 passed, 3 skipped` | **+126**, `skipped` không đổi ✅ |
| `docker_arm64` | `845 passed, 1 skipped, 32 deselected` | `970 passed + 1 failed`, `1 skipped`, `32 deselected` | `970 + 1 = 971 = 845 + 126` ✅, `deselected` không đổi ✅ |

Hai mức tăng bằng nhau và bằng đúng số ca mới → không ca nào phụ thuộc thứ container thiếu, không ca
nào bị gắn `slow`.

### 1.3. Quét mẫu vi phạm (rubric §2 + §9.4 đặc tả)

| # | Lệnh | Kết quả |
|---|---|---|
| [12/49] | `grep -rnE "print\(" src/actuator/` | rỗng ✅ (R23 / CA-2) |
| [13/49] | `grep -rnE "logger\.(debug\|info\|warning\|error\|critical)\(f[\"']" src/actuator/` | rỗng ✅ (CS-5) |
| [14/49] | `grep -rn "except Exception" src/actuator/` | **đúng 2 dòng**, cả hai ở `base.py:219` và `:225`, cả hai kèm `logger.error` ngay sau ✅ (§5.5) |
| [15/49] | `grep -rnE "except\s*:" src/actuator/ tests/test_actuator.py` | rỗng ✅ (CB-4) |
| [16/49] | `grep -rnE "^\s*(import\|from)\s+(RPi\|gpiozero\|pigpio\|serial\|lirc)" src/actuator/ tests/test_actuator.py` | rỗng ✅ (§3.5) |
| [17/49] | `grep -rnE "\b(17\|18\|27\|22\|38000)\b" src/actuator/` | rỗng ✅ (G1 / R16 — chân GPIO và tần số chỉ ở YAML) |
| [18/49] | `grep -rn "time.sleep\|from time import" src/actuator/` | đúng một dòng `mock_actuator.py:98: time.sleep(self._do_tre)`, không có `from time import` ✅ (§5.8) |
| [19/49] | `grep -nE "pytest.mark.slow\|assert True\|^\s*pass\s*$" tests/test_actuator.py` | một dòng `668: pass` — **hợp lệ** (xem dưới) ✅ |
| [20/49] | `grep -nE "subprocess\|urlopen\|requests\.\|socket" tests/test_actuator.py` (loại `monkeypatch\|mock\|patch(`) | rỗng ✅ |
| [21/49] | `grep -rnE "[A-Z]:\\\\\|/home/\|/Users/\|token\s*=\s*[\"']" src/actuator/ tests/test_actuator.py` | rỗng ✅ (CA-4, R26) |

Về [19/49]: `tests/test_actuator.py:668` nằm trong thân `with act:` của
`test_dong81_context_manager_dong_dung`, đúng nghĩa "vào rồi ra khối `with` mà không làm gì", và
dòng 669 ngay sau là `assert act.dang_mo is False`. **Không phải test giả** (CB-6 không áp dụng).

### 1.4. Chạy thật khối sản phẩm

| # | Lệnh | Kết quả |
|---|---|---|
| [22/49] | lệnh §9.5 đặc tả (`python -c "... tao_bo_chap_hanh(nap_cau_hinh('configs/actuator.yaml')) ..."`) | cả ba kỳ vọng đạt ✅ |

Ba kỳ vọng §9.5, đối chiếu với đầu ra nguyên văn người dùng dán về:

1. `{'backend': 'mock', 'la_gia_lap': True, 'canh_bao_nguon_gia_lap': 'KHỐI CHẤP HÀNH ĐANG CHẠY
   BACKEND GIẢ LẬP — …'}` — khoá cảnh báo **không** phải `None` ✅
2. Một dòng `WARNING:src.actuator.mock_actuator:` mang **nguyên văn** `CANH_BAO_GIA_LAP` ✅
3. `[('den_phong_khach', 'bat')]` rồi `[('den_phong_khach', 'bat'), ('den_phong_khach', 'tat')]` ✅

Quan sát thêm, có giá trị: hai dòng `MOCK: đặt thiết bị … sang OFF` xuất hiện cho **cả hai** thiết bị
ngay sau khi `mo()` — vòng ép TẮT vật lý của §4.6 quan sát được ở lượt chạy thật, không chỉ trong test.

---

## 2. Đối chiếu đặc tả — từng mục

| Mục đặc tả | Kết luận |
|---|---|
| **§2 Danh sách trắng** | ✅ đúng 5 tệp, không hơn; [1/49] + [2/49]. `configs/actuator.yaml` nguyên vẹn |
| **§5.1 Hằng module** | ✅ `NGUON_HE_THONG`, `HANH_DONG_HOP_LE`, `LOAI_THIET_BI_HOP_LE`, `PHUONG_THUC_KHOA`, `CANH_BAO_GIA_LAP` đúng tên, đúng giá trị chữ (`base.py:20–27`) |
| **§5.2 `__init_subclass__`** | ✅ ba phép từ chối, thông báo chứa `TEN_BACKEND` / `LA_GIA_LAP` / tên phương thức bị ghi đè (`base.py:58–74`) |
| **§5.3 Nạp `devices`** | ✅ sáu phép kiểm **đúng thứ tự bảng**, khuôn thông báo khớp từng dòng (`base.py:108–131`) |
| **§5.4 Trình tự `mo()`** | ✅ khớp từng dòng giả mã, kể cả `_dang_mo = True` đặt **sau** vòng ép TẮT (`base.py:190–202`) |
| **§5.5 Trình tự `dong()`** | ✅ khớp từng dòng: chỉ tắt thiết bị đang bật, ghi `NGUON_HE_THONG`, đặt `False` và ghi lịch sử **kể cả** khi phần cứng ném, không bao giờ ném ra ngoài (`base.py:213–228`) |
| **§5.6 Trình tự bật/tắt** | ✅ `dang_mo` kiểm **trước** tên thiết bị; ghi lịch sử sau cùng ở cả hai nhánh; ngoại lệ phần cứng lan ra, không ghi gì (`base.py:312–329`) |
| **§5.7 `thuc_thi`** | ✅ ghi **chính** đối tượng `lenh`, không đóng mốc `time.time()` lại; không chuẩn hoá chữ thường (`base.py:288–293`) |
| **§5.8 `ChapHanhGiaLap`** | ✅ `logger.warning("%s", CANH_BAO_GIA_LAP)`; `import time` rồi `time.sleep(self._do_tre)` — [18/49] xác nhận |
| **§5.9 Kiểm `do_tre_gia_lap_giay`** | ✅ bốn phép **đúng thứ tự**: loại `bool` trước kiểm số, `math.isfinite` trước so `< 0` (`mock_actuator.py:63–79`) |
| **§5.10 Factory** | ✅ năm nhánh đúng bảng; `auto` và `gpio` có thông báo riêng; import `ChapHanhGiaLap` **bên trong nhánh** (`factory.py:44–55`); không gọi `mo()` |
| **§5.11 `__init__.py`** | ✅ đúng ba dòng theo mẫu |
| **§5.12 Ba lớp phụ trợ** | ✅ `ChapHanhDem`, `ChapHanhNem` (có công tắc `bat_dau_nem`), `ChapHanhGiaVoThat` — đúng tên §5.12 |
| **§6 Bảng 126 dòng** | ✅ **126/126**, mỗi dòng đúng một hàm `test_dongNN_*`, không dòng nào bị gộp hay bỏ. [8/49] `126 passed`, [9/49] đếm `126` |
| **§7 Tham số → config** | ✅ `backend` đọc ở factory, `devices` ở lớp cơ sở, `mock.do_tre_gia_lap_giay` ở `mock`; `gpio.*`, `ir.*`, `decision.*` **bỏ qua** đúng như bảng. Không hardcode — [17/49] rỗng |
| **§8 Giao diện** | ✅ khớp **từng ký tự**: tên, thứ tự tham số, kiểu trả về, `@property` đúng chỗ, `_tac_dong_phan_cung` là abstractmethod duy nhất. Docstring Google tiếng Việt có mục `Raises:`; `trang_thai` (`base.py:359`) và `trang_thai_tat_ca` (`base.py:382`) đều chứa chữ "giả định" |
| **§9 Lệnh nghiệm thu** | ✅ toàn bộ §9.1–§9.5 dựng lại độc lập ở [4/49]–[22/49], không chép lời khai của `coder` |
| **§10 Đột biến** | ✅ **27/27** phép dựng lại từ đầu, không phép nào để lọt — xem §3 |
| **§11 Ràng buộc kỹ thuật** | ✅ chỉ thư viện chuẩn (`abc`, `math`, `time`, `logging` qua `lay_logger`); không cú pháp riêng 3.12; `except Exception` đúng hai chỗ; không `raise RuntimeError` trong `src/`; không `@pytest.mark.slow`; không ca nào ngủ thật (dòng 54 vá `time.sleep`) |
| **§12 Ngoài phạm vi** | ✅ không `gpio_backend.py`/`ir_backend.py`, không đọc nhánh `decision`, không chạm `src/main.py`, không ghi gì vào `results/`, không thêm phụ thuộc, không đăng ký handler tín hiệu |

### Hai điểm sống còn — soi riêng

**Trung thực số liệu (R5, R6).** Mã việc không ghi tệp nào vào `results/`, không có giá trị mặc định
nào trông như kết quả đo, không có con số ví dụ trong docstring có thể bị chép nhầm vào báo cáo.
Giá trị `0.05` duy nhất nằm trong `tests/test_actuator.py:479` là dữ liệu dựng ca test, không phải
số đo. `mo_ta_nguon()` đi đúng hướng ngược lại: nó **bơm** vào hệ thống một khoá cảnh báo khiến mọi
lượt chạy giả lập tự tố cáo mình. ✅

**Fail-safe phần cứng (R24, `hardware-safety`).** Bốn chốt đều có và đều được đột biến chứng minh là
sống: ép TẮT vật lý lúc `mo()` (ĐB5), `_dang_mo` bật sau vòng ép TẮT (ĐB11), `dong()` không bao giờ
ném (ĐB10), `dong()` tắt hết và để lại vết kiểm toán (ĐB7, ĐB9). `__exit__` gọi `dong()` nên ngoại lệ
giữa khối `with` vẫn đưa thiết bị về TẮT — dòng 82 §6 khẳng định đúng dãy `[bat, tat]`. ✅

---

## 3. Bảng 27 phép đột biến

Mỗi phép: sao lưu tệp **ra ngoài kho** → sửa → `[k/49]` `python -m pytest tests/test_actuator.py -q`
→ ghi ca đỏ → khôi phục. **Mọi khối đều in `KHOI PHUC OK: True`**; sau khối [49/49],
`git status --short --untracked-files=all` trở lại đúng 5 dòng như [1/49] — không sót thay đổi nào
trong mã sản phẩm.

| # | Khối | Phá gì | Dòng §6 dự đoán đỏ | Dòng §6 thực tế đỏ | Tổng kết |
|---|---|---|---|---|---|
| ĐB1 ★★ | [23/49] | mock khai `TEN_BACKEND="gpio"`, `LA_GIA_LAP=False` | 23,24,25,27,28,29 | 23,24,25,27,28,29 | 6 failed, 120 passed |
| ĐB2 ★★ | [24/49] | cảnh báo giả lập `warning`→`info` | 32,33 | 32,33 | 2 failed, 124 passed |
| ĐB3 ★★ | [25/49] | `ten_backend` đọc `cfg.get("backend","")` | 24 | 24 | 1 failed, 125 passed |
| ĐB4 | [26/49] | `canh_bao_nguon_gia_lap` luôn `None` | 29 | 29 | 1 failed, 125 passed |
| ĐB5 ★★ | [27/49] | bỏ vòng ép TẮT trong `mo()` | 66 | 66, **88, 89** | 3 failed, 123 passed |
| ĐB6 | [28/49] | `mo()` không xoá lịch sử | 78 | 78 | 1 failed, 125 passed |
| ĐB7 | [29/49] | `dong()` không ghi bản ghi tự-tắt | 82,83 | 82, 83, **85, 126** | 4 failed, 122 passed |
| ĐB8 | [30/49] | bản ghi tự-tắt mang `nguon=None` | 83 | 83 | 1 failed, 125 passed |
| ĐB9 | [31/49] | `dong()` tắt cả thiết bị đang tắt | 84 | **82**, 84, **126** | 3 failed, 123 passed |
| ĐB10 | [32/49] | `dong()` để ngoại lệ phần cứng lan ra | 85,87 | 85, **86**, 87 | 3 failed, 123 passed |
| ĐB11 | [33/49] | `mo()` bật `_dang_mo` trước vòng ép TẮT | 89 | 89 | 1 failed, 125 passed |
| ĐB12 | [34/49] | ghi lịch sử trước khi gọi phần cứng | 91 | 91 | 1 failed, 125 passed |
| ĐB13 | [35/49] | `bat` nuốt ngoại lệ, chỉ log | 90 | 90, **91, 92** | 3 failed, 123 passed |
| ĐB14 ★ | [36/49] | kiểm tên thiết bị trước `dang_mo` | 74 | 74 | 1 failed, 125 passed |
| ĐB15 | [37/49] | bỏ ghi lịch sử khi trạng thái không đổi | 98,100 | 98, 100 | 2 failed, 124 passed |
| ĐB16 | [38/49] | vẫn ghi phần cứng khi trạng thái không đổi | 99,101 | 99, 101 | 2 failed, 124 passed |
| ĐB17 ★★ | [39/49] | `thuc_thi` đóng mốc thời gian lại | 109,110 | 109, 110 | 2 failed, 124 passed |
| ĐB18 | [40/49] | `thuc_thi` tự chuẩn hoá chữ thường | 115 | 115 | 1 failed, 125 passed |
| ĐB19 | [41/49] | bỏ `math.isfinite` | 59,60,61 | 59, 60, 61 | 3 failed, 123 passed |
| ĐB20 | [42/49] | bỏ phép loại `bool` | 57 | 57 | 1 failed, 125 passed |
| ĐB21 | [43/49] | `lich_su` trả danh sách nội bộ | 104 | 104 (`assert 0 == 1`) | 1 failed, 125 passed |
| ĐB22 | [44/49] | `trang_thai_tat_ca` trả dict nội bộ | 105 | 105 | 1 failed, 125 passed |
| ĐB23 ★ | [45/49] | bỏ nhánh `auto` trong factory | 16,21 | 16, 21 | 2 failed, 124 passed |
| ĐB24 | [46/49] | `danh_sach_thiet_bi` không sắp xếp | 48 | 48 | 1 failed, 125 passed |
| ĐB25 | [47/49] | bỏ kiểm ghi đè `PHUONG_THUC_KHOA` | 05,06,07 | 05, 06, 07 | 3 failed, 123 passed |
| ĐB26 | [48/49] | `from time import sleep` | 54 | 54 | 1 failed, 125 passed |
| ĐB27 | [49/49] | `trang_thai_tat_ca` không ném sau khi đóng | 72 | 72 | 1 failed, 125 passed |

**Kết luận: 27/27 phép đều làm ít nhất một ca đỏ, và mọi dòng §6 dự đoán đều thực sự đỏ.** Không có
guard nào của mã việc này nằm ngoài tầm với của bộ kiểm thử.

### 3.1. Năm phép đỏ rộng hơn dự đoán — giải thích được bằng cơ chế

Rubric §2b cảnh báo "đỏ lan man nhiều ca không liên quan → ca test quá rộng". Ở đây **không** phải
vậy: cả năm trường hợp chỉ lan thêm 1–3 ca, và mọi ca lan thêm đều nằm đúng vùng guard bị phá.

| Phép | Ca đỏ thêm | Cơ chế |
|---|---|---|
| **ĐB5** | 88, 89 | Vòng ép TẮT là **lời ghi phần cứng duy nhất** trong `mo()`. Bỏ nó đi thì `ChapHanhNem(bat_dau_nem=True).mo()` không còn chỗ nào để ném → `pytest.raises(RuntimeError)` của dòng 88 và 89 hỏng ngay. Hai dòng này canh trình tự `mo()`, cùng vùng với dòng 66 |
| **ĐB7** | 85, 126 | Người cài đặt viết dòng 85 **mạnh hơn** mức tối thiểu §6 ("chạy hết không ném") thành `lich_su_rut_gon == [("den","bat"),("den","tat")]`, nên nó cũng phụ thuộc bản ghi tự-tắt; dòng 126 khẳng định đúng dãy đó trên cấu hình thật. Assert mạnh hơn đặc tả là được phép và có lợi |
| **ĐB9** | 82, 126 | Cả hai dòng so lịch sử bằng `==` trên cấu hình **hai thiết bị**; tắt lại `tivi` vốn đang tắt thì thêm một phần tử `("tivi","tat")` vào dãy → lệch |
| **ĐB10** | 86 | Bỏ `try/except` thì mất luôn `logger.error` — dòng 86 canh đúng sự tồn tại của bản ghi ERROR đó, ngoài việc ngoại lệ lan ra làm 85, 87 đỏ |
| **ĐB13** | 91, 92 | Nuốt ngoại lệ trong `bat` thì luồng chạy tiếp: trạng thái bị đặt `True` và lệnh vào lịch sử. Dòng 91 (`lich_su == []`) và 92 (`trang_thai is False`) chính là hai chốt bắt đúng chế độ hỏng "hệ thống báo đã bật đèn trong khi không có gì xảy ra" mà §5.6 sinh ra để chặn |

Đây là **bộ ca canh chồng lấn**, không phải khuyết tật: mỗi guard được nhiều hơn một dòng §6 canh,
nên xoá nhầm một dòng test trong tương lai vẫn còn dòng khác đỡ. Không có trường hợp nào không giải
thích được.

---

## 4. Phân loại lỗi

### 🔴 CHẶN-A — **không có**

Đã soi đủ CA-1…CA-9: không hardcode tham số ([17/49]), không `print()` ([12/49]), truy cập phần cứng
đi qua đúng interface có backend `mock` (CA-3 ngược lại: mã việc này **chính là** lớp abstraction đó),
không dữ liệu cấm lọt git ([3/49]), không sửa tệp ngoài danh sách trắng ([1/49], [2/49]), không làm
việc ngoài phạm vi (§12 đặc tả), không số liệu bịa, không gọi API ngoài, không `import torch`.

### 🔴 CHẶN-B — **không có**

CB-1 logic khớp §5/§6 từng dòng; CB-2 fail-safe đủ bốn chốt và đã chứng minh bằng ĐB5/ĐB7/ĐB9/ĐB10/
ĐB11; CB-3 có context manager, `dong()` luỹ đẳng và không ném; CB-4 không `except:` trần, hai
`except Exception` đều ghi `logger.error` ([14/49]); CB-5, CB-7 không áp dụng; CB-6 dòng `pass` duy
nhất đã kiểm tận mắt là hợp lệ.

### 🟡 CẦN SỬA — **không có**

CS-1 type hints và docstring Google tiếng Việt đủ cho mọi thành viên public, có `Raises:`; CS-2 gói
`actuator` chỉ import `src.common.*`, không import chéo tầng; CS-3 dùng lại `Command` của
`src/common/types.py`, không định nghĩa lại; CS-4 đủ 126/126 dòng §6; CS-5 log lazy formatting
([13/49]); CS-6 lỗi phần cứng ghi ERROR, cảnh báo giả lập ghi WARNING (ĐB2 canh đúng mức này);
CS-7 không log dữ liệu nhạy cảm; CS-8 không áp dụng (không có script CLI); CS-9 không thêm phụ thuộc.

### 🔵 GÓP Ý — không chặn, người dùng quyết định

#### 🔵 GY-1 — Bốn chỉ thị `# noqa` không vô hiệu hoá quy tắc nào đang bật

**Vị trí**: `src/actuator/base.py:219`, `:225`, `:230`, `:290`

```python
except Exception as e:  # noqa: BLE001          # 219, 225
def __enter__(self) -> "BoChapHanh":  # noqa: PYI034   # 230
raise ValueError(thong_bao_sai_kieu)  # noqa: TRY004   # 290
```

**Có vi phạm dòng nào của đặc tả không: KHÔNG.** §11 đòi `ruff check` sạch — [5/49] cho
`All checks passed!`. `BLE001`, `PYI034`, `TRY004` đều **không** nằm trong bộ quy tắc mặc định đang
bật, nên bốn chỉ thị này không che giấu cảnh báo nào, và cũng không dòng nào của đặc tả cấm chúng.
Khuyết tật chỉ hiện ra dưới `--select RUF100` ([6/49]) — tức nó **vô hình dưới đúng lệnh lint mà đặc
tả yêu cầu**. Vì vậy nó không thể là lý do trả lại người cài đặt: yêu cầu chưa từng được viết ra.

**Vì sao vẫn nêu**: `# noqa` là lời khẳng định "chỗ này có cảnh báo và tôi cố ý bỏ qua". Khi lời
khẳng định đó sai, người đọc sau sẽ tưởng `dong()` đang phải chống lại một cảnh báo mà thật ra không
có, và bốn dòng nhiễu này sẽ được sao chép sang `gpio_backend.py` ở P5-03 theo quán tính. Cùng lớp
với ba `# noqa` thừa đã dọn ở `a89927d`. Ghi chú kèm: biến trung gian `thong_bao_sai_kieu`
(`base.py:289`) cũng chỉ tồn tại để chiều một quy tắc không bật, bỏ được cùng lượt.

**Nếu người dùng đồng ý sửa**: xoá bốn chú thích `# noqa` (chỉ chạm `base.py`, vẫn trong danh sách
trắng), giữ lại lý do bằng một câu trong docstring `dong()` — nó đã có sẵn: "Lỗi phần cứng lúc tắt
chỉ được ghi ở mức `ERROR`". Với `:290`, `ValueError` là quyết định của §4.7 đặc tả, đã ghi trong
docstring `Raises:`, không cần `# noqa` để bảo vệ. **Không** bật `RUF100` trong cấu hình ở mã việc
này — `pyproject.toml` nằm ngoài danh sách trắng §2; nếu muốn bật vĩnh viễn thì mở một mã việc
`chore(cong-cu)` riêng.

#### 🔵 GY-2 — `logger` mức module trong `factory.py:13` không được dùng dòng nào

**Vị trí**: `src/actuator/factory.py:13`

```python
logger = lay_logger(__name__)
```

**Đã xác minh bằng cách đọc trọn tệp (56 dòng): không có bất kỳ lời gọi `logger.*` nào trong
`factory.py`.** Đây là hệ quả trực tiếp của §4.1 đặc tả — factory của khối thu hình cần `logger`
cho dòng `warning` của nhánh `auto`, còn ở đây nhánh `auto` bị cấm hẳn nên không còn gì để log; mọi
đường ra của `tao_bo_chap_hanh` đều là `raise LoiCauHinh`, và người bắt ngoại lệ mới là người quyết
định ghi log.

`lay_logger` chỉ gọi `logging.getLogger(ten)` (`src/common/logging.py:67`), không tạo handler, không
có tác dụng phụ lúc import — nên đây là **binding chết vô hại**, không phải rủi ro. `ruff` không bắt
được vì F841 chỉ xét biến cục bộ.

**Người dùng chọn một trong hai**, cả hai đều chấp nhận được:
- **Xoá** dòng 13 và dòng `from src.common.logging import lay_logger` (dòng 11) — tệp gọn đúng bằng
  những gì nó dùng;
- **Giữ** để mọi module trong `src/actuator/` cùng một khuôn mở đầu, và vì P5-03 thêm nhánh `gpio`
  có thể sẽ cần log. Nếu giữ, nên ghi một dòng chú thích để lần đọc sau không tưởng là sót.

#### 🔵 GY-3 — Ba điểm nhỏ trong chính đặc tả, gửi `spec-writer` (không phải lỗi của người cài đặt)

1. **Tham chiếu chéo lệch số** trong đặc tả: §5.7 viết "Dòng 106 §6, ĐB15 §10" nhưng bảng §6 đánh số
   dòng 109/110 và §10 đánh số ĐB17; §5.8 viết "dòng 48 §6 … ĐB23" trong khi thực tế là dòng 54 và
   ĐB26; §5.9 viết "Dòng 54, 55, 56 §6 và ĐB17 §10" trong khi thực tế là 59, 60, 61 và ĐB19. Bảng §6
   và §10 mới là bản đúng và người cài đặt đã bám đúng chúng, nhưng ở mã việc sau các tham chiếu lệch
   này có thể dẫn người đọc tới nhầm dòng.
2. **§11 liệt kê thư viện cho `tests/` chưa đủ**: chỉ nêu `pytest`, `pathlib`, `nap_cau_hinh`, trong
   khi dòng 32–34 và 86 §6 **buộc** phải dùng `logging`, và cách viết sạch nhất cho dòng 91/92 là
   `contextlib.suppress`. Người cài đặt dùng cả hai — đúng tinh thần "chỉ thư viện chuẩn, không thêm
   phụ thuộc" ở đầu gạch đầu dòng, nên **không tính là lỗi**. Đề nghị sửa câu đó thành "thư viện
   chuẩn bất kỳ, cộng `pytest`".
3. **Thuộc tính công khai `self.cfg`** (`base.py:89`) không có trong danh sách §8 và hiện không được
   dòng nào trong `src/` đọc. Giữ nó là hợp lý vì P5-03 cần `cfg` để lấy chân GPIO, nhưng nó cũng mở
   một đường vòng: `act.cfg["backend"]` trên cấu hình nói dối ở dòng 24 §6 vẫn trả `"gpio"`, đúng thứ
   §4.3 muốn chặn ở `ten_backend`. Đề nghị P5-03 (hoặc một dòng bổ sung vào §8) đổi thành `_cfg` và
   ghi rõ "chỉ backend được đọc, tầng trên dùng `mo_ta_nguon()`".

---

## 5. Ca đỏ trong container — **không thuộc P5-01**

Khối [10/49] có **một** ca đỏ:

```
tests/test_benchmark_detect.py::test_camera_dong26_vung_suy_luan_do_dung_phan_suy_luan
tests/test_benchmark_detect.py:1775
assert all(r["latency_ms"] < 20 for r in bg)
  với _do_camera_truc_tiep(monkeypatch, tmp_path, 0.040, 0.002)
```

Ba lý do khẳng định ca này **không** tính vào phán quyết của mã việc này:

1. Tệp `tests/test_benchmark_detect.py` **không** nằm trong danh sách trắng §2 và **không** bị mã
   việc này chạm — [1/49] chỉ có 5 dòng `??`, [2/49] rỗng.
2. Ca thuộc `P2-07`, kiểm khối phát hiện; nó không import và không đi qua bất kỳ dòng nào của
   `src/actuator/`.
3. Phép trừ khớp chính xác: `970 passed + 1 failed = 971 = 845 + 126`. Nếu ca đỏ này do P5-01 gây ra
   thì phép trừ đã lệch.

Nguyên nhân: ngưỡng **tuyệt đối** `latency_ms < 20` dưới QEMU, trong một lượt chạy kéo 11 phút
(`664.34s`) — đúng rủi ro mà biên bản `P2-07` và `P2-08` đã treo sẵn một mục 🔵. Ghi nhận lần đỏ này
làm **bằng chứng thực nghiệm đầu tiên** cho mục đó: ngưỡng tuyệt đối tính bằng mili-giây không tái
lập được trên môi trường giả lập, nên hoặc đổi sang khẳng định **tỉ lệ** giữa hai đại lượng cùng đo,
hoặc gác ca theo môi trường. Việc xử lý thuộc một mã việc riêng, không thuộc P5-01.

⚠️ Vì môi trường `docker_arm64` là số **tham khảo** (CLAUDE.md §2.9), lần đỏ này không ảnh hưởng đến
bất kỳ chỉ tiêu §1 nào.

---

## 6. Phán quyết

🟡 **ĐẠT CÓ ĐIỀU KIỆN**

| Mức | Số lỗi |
|---|---|
| 🔴 CHẶN-A | **0** |
| 🔴 CHẶN-B | **0** |
| 🟡 CẦN SỬA | **0** |
| 🔵 GÓP Ý | **3** (GY-1 `# noqa` thừa · GY-2 `logger` chết · GY-3 ba điểm gửi `spec-writer`) |

Ba lệnh nền sạch/xanh ([4/49], [5/49], [7/49]); 126/126 dòng §6 có ca tương ứng và đều xanh; 27/27
phép đột biến đều bắt được. **Không có gì phải sửa trước khi commit** — ba mục 🔵 là quyết định của
người dùng, chuyển thành mã việc sau nếu đồng ý.

---

## 7. Việc tiếp theo

1. **Commit ngay** năm tệp trên nhánh `feat/p5-01-actuator-base-mock`, message đề xuất (R29):

   ```
   feat(actuator): interface trừu tượng, backend mock và factory khối chấp hành — P5-01
   ```

   Chỉ `git add` đúng năm tệp trong danh sách trắng §2; `configs/actuator.yaml` đã commit ở `22c58e4`.
2. **Gộp vào `dev`** sau khi commit.
3. **Quyết định về GY-1 và GY-2**: nếu muốn dọn, gộp chung một commit `chore(actuator)` nhỏ **sau**
   khi P5-01 đã gộp, để lịch sử của mã việc giữ nguyên hình dạng đã được review.
4. **GY-3 gửi `spec-writer`** trước khi viết đặc tả `P5-02`, để ba điểm đó không lặp lại.
5. Ca đỏ `P2-07` trong container: gom vào mục 🔵 đang treo của `P2-07`/`P2-08`, xử lý ở một mã việc
   riêng — **không** chặn Phase 5.
