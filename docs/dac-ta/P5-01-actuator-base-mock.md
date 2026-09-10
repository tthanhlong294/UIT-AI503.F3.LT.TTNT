# P5-01 — Khối chấp hành: interface trừu tượng, backend `mock`, factory

| | |
|---|---|
| **Phase** | 5 — Điều khiển thiết bị & Cảnh báo |
| **Bước pipeline** | `docs/pipeline/phase-5.md`, bước **5.1** (và chỉ 5.1) |
| **Nhánh** | `feat/p5-01-actuator-base-mock` |
| **Phụ thuộc** | đỉnh `dev` = `5a873d7`. Không phụ thuộc mã việc nào chưa gộp |
| **Ước lượng** | 4 tệp mã nguồn (~360 dòng) + 1 tệp kiểm thử (~600 dòng) |

---

## 1. Mục tiêu

Dựng lớp trừu tượng hoá phần cứng cho khối chấp hành (R22) cùng backend `mock` và factory, sao cho
toàn bộ logic điều khiển thiết bị chạy và kiểm thử được trên PC/Docker **mà không bao giờ có thể
nhầm giả lập với thật**.

---

## 2. DANH SÁCH TRẮNG — chỉ được tạo/sửa các tệp sau

| Tệp | Thao tác |
|---|---|
| `src/actuator/__init__.py` | tạo mới |
| `src/actuator/base.py` | tạo mới |
| `src/actuator/mock_actuator.py` | tạo mới |
| `src/actuator/factory.py` | tạo mới |
| `tests/test_actuator.py` | tạo mới |

> Mọi tệp khác: **cấm chạm**. Sửa tệp ngoài danh sách = lỗi CHẶN-A khi review.
>
> ⛔ **`configs/actuator.yaml` đã được người viết đặc tả tạo sẵn và đã commit.** Nó nằm trong vùng
> ghi của `spec-writer` (CLAUDE.md §2.9), **bạn chỉ đọc, không sửa một ký tự nào** — kể cả khoảng
> trắng cuối dòng. Thấy nội dung của nó mâu thuẫn với đặc tả thì **dừng và báo**, đừng tự sửa.
>
> ⛔ **Cấm chạm `requirements.txt` và `deploy/Dockerfile.arm64`.** Mã việc này chạy trọn bằng thư
> viện chuẩn; thêm phụ thuộc buộc phải dựng lại `faceid:arm64` (R43), việc đó thuộc `P5-03`.
>
> ⛔ **Cấm chạm `src/common/exceptions.py`.** Hai lớp cần dùng — `LoiCauHinh` và `LoiPhanCung` —
> **đã có sẵn**, `LoiPhanCung` được viết ra đúng cho việc này ("Lỗi phần cứng chấp hành: GPIO,
> relay, module phát IR"). Không định nghĩa lớp lỗi mới.

---

## 3. Dữ kiện đã kiểm — 10/09/2026

### 3.1. Thư mục `src/actuator/` **chưa tồn tại**

Toàn bộ gói là mới. `src/` dùng gói tường minh — mỗi thư mục con có `__init__.py`
(`src/__init__.py`, `src/common/__init__.py`, `src/capture/__init__.py`, …). Gói mới phải theo
đúng khuôn đó.

### 3.2. `Command` đã có sẵn trong `src/common/types.py` — KHÔNG định nghĩa lại

```python
@dataclass(frozen=True)
class Command:
    thiet_bi: str
    hanh_dong: str      # "bat" hoặc "tat"
    nguon: str | None   # ID người dùng đã kích hoạt; None nếu hệ thống tự phát
    thoi_diem: float    # dấu thời gian Unix, đơn vị giây
```

Lớp `frozen=True` nên có `__eq__` và không sửa được sau khi tạo — đây là lý do nó được chọn làm
đơn vị của lịch sử lệnh ở §4.4: hai `Command` so sánh được bằng `==`, và người gọi không thể sửa
bản ghi lịch sử sau lưng.

### 3.3. `src/common/exceptions.py` — bốn lớp đã có

`LoiHeThong` (gốc) → `LoiCauHinh`, `LoiCamera`, `LoiPhanCung`, `LoiMoHinh`.

### 3.4. Khuôn mẫu bám theo: khối thu hình `src/capture/`

Đã đọc `base.py`, `mock_camera.py`, `factory.py`, `__init__.py`, `configs/capture.yaml` và 26 ca
kiểm thử đầu của `tests/test_capture.py`. Những điểm **giữ nguyên** để hai khối đọc giống nhau:

| Điểm | Khối thu hình | Khối chấp hành (mã việc này) |
|---|---|---|
| Tên vòng đời | `mo()` / `dong()` / `dang_mo` | **y hệt** |
| Context manager | `__enter__` gọi `mo()`, `__exit__` gọi `dong()` | **y hệt** |
| Factory | `tao_bo_thu_hinh(cfg)` nhận **toàn bộ** dict YAML | `tao_bo_chap_hanh(cfg)`, **y hệt** |
| Thiếu khoá | `raise LoiCauHinh("Thiếu key bắt buộc: <key>")` | **y hệt khuôn thông báo** |
| Gọi khi chưa mở | `raise LoiCamera(...)` | `raise LoiPhanCung(...)` |
| `dong()` gọi nhiều lần | an toàn, không ném | **y hệt** |
| `__init__.py` | chỉ xuất ABC + factory | **y hệt** |
| Ca kiểm thử số 01 | khoá cứng tập tên tệp `.py` trong thư mục | **y hệt**, xem dòng 01 §6 |

Ba điểm **cố ý khác**, đều có lý do ở §4:

1. **Không có backend `auto`** (§4.1).
2. **`base.py` không phải ABC thuần mà là lớp cơ sở có cài đặt** (Template Method, §4.2).
3. **Backend nhận toàn bộ dict cấu hình**, không nhận riêng nhánh con — vì nó cần cả `devices`
   (mức trên cùng) lẫn `mock` (§4.7).

### 3.5. Container `faceid:arm64` — thứ KHÔNG có

Bộ kiểm thử phải xanh khi thiếu tất cả những thứ sau:

| Thứ thiếu | Vì sao |
|---|---|
| nhị phân `git` | `deploy/Dockerfile.arm64` chỉ cài `libgl1`, `libglib2.0-0` |
| `.git/`, và nội dung `docs/`, `models/`, `data/`, `results/`, `report/` trong **ảnh** | `.dockerignore` loại chúng khỏi ngữ cảnh dựng ảnh |
| `ultralytics`, `torch`, `onnx` | không có trong `requirements.txt` |
| **mọi phần cứng GPIO, mọi module `RPi.GPIO` / `gpiozero` / `pigpio`** | chưa cài, và chưa mua |

⚠️ Lệnh chạy ở §9.3 gắn cả kho vào `/app` bằng `-v`, nên `configs/` **có mặt** trong container dù
`.dockerignore` nói gì — phép gắn thư mục xảy ra lúc chạy, không lúc dựng ảnh. Thứ **không** phục
hồi được bằng phép gắn là nhị phân `git` và các gói Python thiếu.

Hệ quả bắt buộc: **không** `subprocess.run(["git", ...])`, **không** import gói phần cứng ở bất kỳ
đâu, **không** `@pytest.mark.slow`, **không** chạm mạng. Tệp duy nhất trong kho mà ca kiểm thử được
đọc là `configs/actuator.yaml`, qua đường dẫn dựng từ `Path(__file__).resolve().parents[1]` (khuôn
đã dùng ở `tests/test_capture.py::test_01`). Mọi tệp ca kiểm thử tự tạo phải nằm trong `tmp_path`.

### 3.6. Bộ kiểm thử — mốc để đối chiếu

Đo ngày 10/09/2026 trên `5a873d7` (chính là commit ở dòng "Phụ thuộc"):

| Môi trường | Lệnh | Kết quả |
|---|---|---|
| `pc_x86`, Python 3.12.5 | `pytest -q`, không lọc marker | `875 passed, 3 skipped` (878 thu thập) |
| `docker_arm64`, Python 3.11.16 | `pytest -q -m "not slow"` | `845 passed, 1 skipped, 32 deselected` (878 thu thập) |
| `pi5` | — | **[CHƯA ĐO Ở MỐC NÀY]** |

Ba ca `skipped` trên `pc_x86` là ca 49, 50, 51 của `P0-05`, gác theo nền tảng vì bit quyền chỉ có
nghĩa trên POSIX. **Con số bạn tự đo ở §9.0 mới là mốc thật**; ba con số trên chỉ để đối chiếu.

### 3.7. Cấu hình đã được sửa sẵn — bạn chỉ ĐỌC

`configs/actuator.yaml` đã tồn tại với đúng nội dung sau (rút gọn phần chú thích):

```yaml
backend: mock
devices:
  den_phong_khach:
    loai: relay
    mo_ta: "..."
    gpio: { pin: TBD, active_low: true }
  tivi_phong_khach:
    loai: ir
    mo_ta: "..."
    ir: { pin: TBD, tan_so_hz: 38000, ma_bat: TBD, ma_tat: TBD }
mock:
  do_tre_gia_lap_giay: 0.0
decision:
  n_frame_xac_nhan: 3
  cooldown_giay: 10
  timeout_vang_mat_giay: 30
```

Ba điều rút ra và phải cài đúng:

- `pin: TBD` nạp thành **chuỗi** `"TBD"`. Mã việc này **không** kiểm nhánh `gpio:`/`ir:` — nếu bạn
  kiểm, tệp cấu hình thật sẽ đỏ ngay. Xem dòng 42, 43 §6.
- Nhánh `decision:` **thuộc `P5-02`**. Mã việc này phải **bỏ qua** mọi khoá mức trên cùng mà nó
  không sở hữu. Xem dòng 44 §6.
- Chỉ có đúng hai thiết bị, đại diện đúng hai nhóm mà đề cương MT5 chốt: đèn (relay/GPIO) và tivi
  (IR).

---

## 4. Bảy quyết định thiết kế — chốt và lý do

### 4.1. ★★ CẤM giá trị `auto` — và đây không phải chuyện cẩn thận thái quá

`src/capture/factory.py` có nhánh `auto`: mở thử camera thật, hỏng thì rơi về `mock` kèm một dòng
`logger.warning`. Ở `benchmark_detect.py` nhánh đó sinh ra một tệp `results/` đầy đủ, mang nhãn
"Raspberry Pi 5", mà số bên trong là nhiễu tổng hợp — `P2-07` §4.3 phải cấm hẳn để chặn.

Với khối chấp hành, chế độ hỏng đó **tệ hơn một bậc**: hệ thống ghi log "đã bật đèn cho `u01`",
dashboard hiện đèn sáng, biên bản đo độ trễ bước 5.6 cho ra một con số đẹp — trong khi **không có
dòng điện nào qua relay**. Ảnh benchmark còn mở ra xem lại được; ở đây không còn gì để xem lại.

Nhưng lý do quyết định không phải mức độ hậu quả, mà là: **ở khối này `auto` không thể đúng về
nguyên tắc.** Mở một chân GPIO thành công trên **mọi** Raspberry Pi, kể cả khi không có sợi dây
nào cắm vào chân đó. Không tồn tại phép dò nào phân biệt "relay đã đấu" với "relay chưa đấu". Nên
`auto` chỉ có thể rơi về giả lập trong im lặng — nó không phải một phép tự dò, nó là một cái bẫy.

**Chốt:** `backend` chỉ nhận `"mock"` (cài đặt ở mã việc này) và `"gpio"` (`P5-03`). Giá trị
`"auto"` bị **từ chối bằng một thông báo riêng**, không rơi chung nhánh "backend không hợp lệ" —
để người đọc thông báo hiểu ngay đây là quyết định cố ý chứ không phải lỗi đánh máy.

### 4.2. ★★ `base.py` là lớp cơ sở CÓ CÀI ĐẶT (Template Method), không phải ABC thuần

`src/capture/base.py` là ABC thuần vì `CameraGiaLap` và `CameraOpenCV` gần như không chia sẻ gì.
Ở khối chấp hành thì ngược lại: `mock` và `gpio` chia sẻ **tất cả** — bảng thiết bị, bộ nhớ trạng
thái, lịch sử lệnh, phép kiểm hợp lệ, ghi log, trình tự fail-safe — và khác nhau **đúng một việc**:
ghi mức điện lên chân.

**Chốt:** `BoChapHanh` cài đặt sẵn toàn bộ phần chung. Backend chỉ phải khai hai hằng lớp và cài
**một** phương thức trừu tượng duy nhất:

```python
@abstractmethod
def _tac_dong_phan_cung(self, ten_thiet_bi: str, bat_len: bool) -> None: ...
```

Lý do quyết định: nó khiến `P5-03` **không thể quên** fail-safe, lịch sử và log — không phải vì
`P5-03` được nhắc, mà vì không có chỗ nào để quên. `gpio_backend.py` sẽ dài khoảng 40 dòng.

### 4.3. ★★ Tên backend đến từ LỚP, không đến từ cấu hình

Mọi đối tượng chấp hành phải phơi ra tên backend **thật đang chạy**, để `main.py` và khối ghi log
lấy được mà không phải đoán. Nếu thuộc tính đó đọc từ `cfg["backend"]` thì nó **không chứng minh
được gì** — một cấu hình ghi `backend: gpio` chạy nhầm bằng giả lập vẫn tự khai là `gpio`.

**Chốt:** mỗi lớp con khai hai **hằng lớp** với giá trị chữ (literal):

```python
class ChapHanhGiaLap(BoChapHanh):
    TEN_BACKEND = "mock"
    LA_GIA_LAP = True
```

`ten_backend` trả `type(self).TEN_BACKEND`, `la_gia_lap` trả `type(self).LA_GIA_LAP`. **Cấm đọc
`cfg` trong hai thuộc tính này.** Ca kiểm thử canh đúng chỗ đó bằng cách dựng `ChapHanhGiaLap` với
một cấu hình **nói dối** (`backend: "gpio"`) rồi đòi `.ten_backend == "mock"` — dòng 23, 24 §6.

Kèm theo, `BoChapHanh.__init_subclass__` **từ chối định nghĩa lớp con** nếu lớp đó không tự khai
`TEN_BACKEND` và `LA_GIA_LAP` trong `cls.__dict__`, hoặc `TEN_BACKEND` rỗng. Đây chính là quy tắc
"lệnh kiểm không được tự cấp thứ mà mã nguồn phải tự khai báo", cài thẳng vào ngôn ngữ: quên khai
thì không import được, không phải chờ một ca test nhớ ra.

`LA_GIA_LAP` mặc định về phía an toàn: lớp quên khai thì lỗi, chứ **không** âm thầm nhận `False`.
Nói dối theo chiều "tôi là thật" là chiều nguy hiểm.

### 4.4. ★ Lịch sử lệnh là `list[Command]`, và nó thuộc lớp cơ sở

Hình dạng lịch sử phải chốt **ngay bây giờ** vì `P5-02` (chống nhiễu, cooldown) và ca kiểm thử của
`main.py` sẽ đối chiếu với nó; đổi sau kéo theo sửa ca test ở nhiều mã việc.

**Chốt:**

- `lich_su -> list[Command]` — **bản sao**, người gọi sửa không ảnh hưởng trạng thái trong.
- `lich_su_rut_gon -> list[tuple[str, str]]` — dãy `(thiet_bi, hanh_dong)`, để khẳng định bằng
  `==` mà không vướng dấu thời gian. Đây là dạng mà ca kiểm thử của `P5-02` nên dùng.
- Lịch sử nằm ở **lớp cơ sở**, không riêng `mock` — backend GPIO cũng cần vết kiểm toán cho phép
  đo độ trễ bước 5.6 và cho trang lịch sử ở Phase 6.
- Ghi **mọi lệnh được chấp nhận**, kể cả lệnh lặp không đổi trạng thái (§4.5), **trừ** các lời ép
  tắt lúc `mo()` (§4.6).
- Ghi **sau khi** lời ghi phần cứng thành công. Lệnh ném ngoại lệ **không** để lại bản ghi — lịch
  sử là vết của việc đã làm, không phải của ý định.

### 4.5. ★ Bật thiết bị đang bật là phép LUỸ ĐẲNG, không phải lỗi

`P5-02` mới là nơi chịu trách nhiệm dập lệnh lặp (N khung xác nhận, cooldown). Nếu khối chấp hành
ném ngoại lệ khi gặp lệnh lặp thì vòng lặp chính phải bọc `try` quanh **mọi** lời gọi, và một lần
lặp vô hại sẽ có nguy cơ làm sập hệ thống — trái R24.

**Chốt, ba vế tách bạch:**

| Vế | Hành vi |
|---|---|
| Ngoại lệ | **Không.** `bat` một thiết bị đang bật trả về `None` bình thường |
| Lịch sử | **Có ghi.** Nếu nuốt luôn, `P5-02` không cách nào kiểm chứng cooldown của chính nó có chạy không |
| Ghi phần cứng | **Bỏ qua.** Không gọi `_tac_dong_phan_cung`, chỉ `logger.debug` |

Vế thứ ba là ràng buộc cho `P5-03`, không phải trang trí: relay đóng/ngắt liên tục là mối nguy phần
cứng (`hardware-safety` §4). Ở `mock` nó vẫn quan sát được — dòng 95, 97 §6 đếm số lời gọi.

### 4.6. ★ Trạng thái là trạng thái GIẢ ĐỊNH, đọc từ bộ nhớ, và luôn khởi tạo bằng TẮT

Câu hỏi "đọc trạng thái từ bộ nhớ hay hỏi lại phần cứng" phải chốt ở đây vì nó ràng buộc `P5-03`.
Chân GPIO output đọc ngược lại được, nhưng **IR là một chiều** — hệ thống không bao giờ biết tivi
đã bật hay chưa (`hardware-safety` §5). Một hợp đồng thống nhất cho cả hai nhóm thiết bị chỉ có thể
là "trạng thái giả định".

**Chốt:**

- `trang_thai(ten)` và `trang_thai_tat_ca()` đọc bộ nhớ trong của lớp cơ sở. Docstring **phải** có
  chữ "giả định" — Phase 6 sẽ hiển thị con số này lên dashboard và báo cáo phải nói rõ đó là giả
  định, không phải đo được.
- Cả hai **ném `LoiPhanCung` khi chưa `mo()` hoặc đã `dong()`**. Trả trạng thái cũ sau khi đã đóng
  là cách chắc chắn để dashboard hiển thị một cái đèn "đang sáng" mà chương trình đã thoát từ lâu.
- `mo()` đặt **mọi** thiết bị đã khai về `False`, **và ghi mức TẮT xuống phần cứng cho từng thiết
  bị** (`hardware-safety` §3: "Khởi tạo GPIO ở trạng thái TẮT, không để trạng thái không xác định
  lúc boot"). Các lời ép tắt này **không** vào lịch sử — nếu vào, mọi ca kiểm thử của `P5-02` phải
  bỏ qua N bản ghi đầu.

  ⚠️ Chỉ đặt dict về `False` mà **không** ghi xuống phần cứng là một bản sai *tự nhất quán*: mọi
  phép đọc trạng thái đều đúng, chỉ có chân GPIO là còn nguyên mức từ lần chạy trước. Dòng 63 §6
  đếm lời gọi `_tac_dong_phan_cung` để bắt đúng chỗ này; ĐB5 §10 dựng lại bản sai đó.
- `mo()` **xoá** lịch sử (mở lại là một phiên mới), giống `CameraGiaLap.mo()` đặt lại RNG.
- `dong()` tắt mọi thiết bị **đang bật** — và **chỉ** những cái đang bật — rồi ghi mỗi lần tắt đó
  vào lịch sử với `nguon = NGUON_HE_THONG`. Đây là bằng chứng fail-safe: log phải cho thấy hệ thống
  đã chủ động tắt lúc thoát, chứ không im lặng bỏ đó.

### 4.7. ★ Ranh giới ngoại lệ — hai câu, không có trường hợp thứ ba

| Loại | Ngoại lệ | Cách đọc |
|---|---|---|
| Cấu hình sai/thiếu khoá, backend không hợp lệ, **thiết bị chưa khai trong `devices`** | `LoiCauHinh` | "đi sửa tệp YAML" |
| Gọi khi chưa `mo()` / đã `dong()`, và lỗi phần cứng thật (`P5-03`) | `LoiPhanCung` | "kiểm dây, kiểm vòng đời" |
| **Đối số sai kiểu/sai miền** truyền vào một hàm public (`hanh_dong` lạ, `lenh` không phải `Command`) | `ValueError` | "đi sửa mã gọi" |

Vế thứ ba theo đúng tiền lệ đã có trong kho: `src/recognizer/base.py::trich_dac_trung` ném
`ValueError` cho ảnh sai hình dạng, còn lỗi hệ thống mới dùng lớp con của `LoiHeThong`. Nêu ra đây
để người review không báo nhầm là vi phạm quy ước.

Kèm theo, **hai khoá phân chia trách nhiệm nạp cấu hình**:

- `factory.py` kiểm **`backend`**, và chỉ `backend`.
- `BoChapHanh.__init__` kiểm **`devices`**, và chỉ `devices`.
- `ChapHanhGiaLap.__init__` kiểm **`mock`**, và chỉ `mock`.
- Mọi khoá mức trên cùng khác (`decision`, và bất cứ gì `P5-02`/`P5-03` thêm sau) — **bỏ qua**.

Vì thế `ChapHanhGiaLap` nhận **toàn bộ** dict cấu hình, không nhận riêng nhánh `mock` như
`CameraGiaLap`. Nó cần `devices` ở mức trên cùng.

---

## 5. Thiết kế chi tiết

### 5.1. Hằng mức module trong `src/actuator/base.py`

Bốn hằng dưới đây phải có **đúng tên này** vì ca kiểm thử và các mã việc sau import chúng:

```python
NGUON_HE_THONG = "he_thong"
HANH_DONG_HOP_LE: tuple[str, ...] = ("bat", "tat")
LOAI_THIET_BI_HOP_LE: tuple[str, ...] = ("relay", "ir")
PHUONG_THUC_KHOA: tuple[str, ...] = ("mo", "dong", "bat", "tat", "thuc_thi")
CANH_BAO_GIA_LAP = (
    "KHỐI CHẤP HÀNH ĐANG CHẠY BACKEND GIẢ LẬP — "
    "KHÔNG CÓ DÒNG ĐIỆN NÀO ĐI QUA RELAY VÀ KHÔNG CÓ LỆNH IR NÀO ĐƯỢC PHÁT"
)
```

`CANH_BAO_GIA_LAP` là bản sao vai trò của khoá `canh_bao_nguon_gia_lap` trong `.meta.json` ở
`P2-07`: một chuỗi không thể đọc lướt qua mà không hiểu.

### 5.2. `__init_subclass__` — ba phép từ chối

Chạy khi **định nghĩa** một lớp con của `BoChapHanh`, ném `TypeError` nếu:

1. `"TEN_BACKEND" not in cls.__dict__` hoặc giá trị rỗng → thông báo **chứa** `TEN_BACKEND`.
2. `"LA_GIA_LAP" not in cls.__dict__` → thông báo **chứa** `LA_GIA_LAP`.
3. Lớp con định nghĩa lại bất kỳ tên nào trong `PHUONG_THUC_KHOA` → thông báo **chứa tên phương
   thức bị ghi đè**. Vòng đời và trình tự fail-safe là phần chịu lực, không backend nào được đổi.

### 5.3. `BoChapHanh.__init__(cfg: dict)` — nạp `devices`

Không chạm phần cứng, không gọi `mo()`. Sau khi chạy: `dang_mo` là `False`, lịch sử rỗng.

Phép kiểm, theo thứ tự, mỗi phép ném `LoiCauHinh`:

| # | Điều kiện | Khuôn thông báo (bắt buộc chứa) |
|---|---|---|
| 1 | thiếu khoá `devices` | `Thiếu key bắt buộc: devices` |
| 2 | `devices` không phải `dict`, hoặc rỗng | `devices` |
| 3 | tên thiết bị không phải `str`, hoặc rỗng sau `.strip()` | `Tên thiết bị` |
| 4 | giá trị của một thiết bị không phải `dict` | tên thiết bị đó |
| 5 | thiếu `loai` | `Thiếu key bắt buộc: devices.<ten>.loai` |
| 6 | `loai` ngoài `LOAI_THIET_BI_HOP_LE` | `loai` **và** tên thiết bị đó |

Không kiểm gì thêm — nhánh `gpio:`/`ir:` thuộc `P5-03` (§3.7).

Lưu lại: `self._thiet_bi: dict[str, str]` ánh xạ **tên → loại**.

### 5.4. Trình tự `mo()` — viết đúng thứ tự này

```
nếu đã mở: trả về ngay (luỹ đẳng, không ghi phần cứng lần hai)
đặt _trang_thai = {ten: False cho mọi ten}
đặt _lich_su = []
gọi _mo_phan_cung()
với mỗi ten trong danh_sach_thiet_bi:   # đã sắp xếp
    gọi _tac_dong_phan_cung(ten, False)  # ép TẮT vật lý — §4.6
đặt _dang_mo = True                      # SAU vòng lặp, không trước
logger.info(...)
```

`_dang_mo` bật lên **sau** vòng lặp là cố ý: nếu một lời ghi phần cứng ném ngoại lệ, ngoại lệ đó
lan ra ngoài và đối tượng ở lại trạng thái **chưa mở**. Không bảo đảm được TẮT lúc khởi động thì
từ chối khởi động — đó là nghĩa của fail-safe, không phải "cứ chạy tiếp rồi log một dòng".
Dòng 84, 85 §6 canh chỗ này.

### 5.5. Trình tự `dong()` — viết đúng thứ tự này

```
nếu chưa mở: trả về ngay (gọi nhiều lần phải an toàn)
với mỗi ten trong danh_sach_thiet_bi:
    nếu _trang_thai[ten] là True:
        thử: _tac_dong_phan_cung(ten, False)
        bắt Exception: logger.error("Không tắt được %s: %s", ten, e)   # cố tắt cho bằng hết
        _trang_thai[ten] = False
        _lich_su.append(Command(ten, "tat", NGUON_HE_THONG, time.time()))
thử: _dong_phan_cung()
bắt Exception: logger.error(...)
đặt _dang_mo = False
logger.info(...)
```

Ba điểm phải cài đúng, không suy diễn lại:

- **`dong()` không bao giờ ném.** R24: mất phần cứng thì log lỗi, giữ thiết bị ở trạng thái an
  toàn, không làm sập hệ thống. `dong()` được gọi trong khối `finally` của vòng lặp chính; nó mà
  ném thì nuốt luôn ngoại lệ gốc.
- **Ghi lịch sử và đặt `False` kể cả khi lời ghi phần cứng ném.** Trạng thái là *giả định* (§4.6):
  sau khi đã ra lệnh tắt, giả định an toàn là đã tắt; sai lệch được ghi bằng dòng `ERROR`.
- Đây là **hai** chỗ duy nhất trong cả gói được dùng `except Exception`, và cả hai đều ghi log chứ
  không `pass` (G5, và đúng khuôn `hardware-safety` §3). §9.4 đếm đúng bằng 2.

### 5.6. Trình tự nội bộ khi bật/tắt — dùng chung cho `bat`, `tat`, `thuc_thi`

```
nếu không _dang_mo: raise LoiPhanCung("... chưa mở hoặc đã đóng ...")   # KIỂM TRƯỚC
nếu ten không có trong _thiet_bi: raise LoiCauHinh("Thiết bị chưa khai báo trong cấu hình: <ten>")
nếu _trang_thai[ten] khác đích:
    _tac_dong_phan_cung(ten, đích)      # ném thì lan ra ngoài, KHÔNG ghi gì
    _trang_thai[ten] = đích
    logger.info("Đặt thiết bị %s sang %s (nguồn: %s)", ...)
ngược lại:
    logger.debug(...)                   # luỹ đẳng, không chạm phần cứng
_lich_su.append(lenh)                   # ghi SAU cùng, cả hai nhánh
```

**Thứ tự hai phép kiểm đầu là một quyết định, không phải ngẫu nhiên**: `dang_mo` kiểm trước
`ten`. Nghĩa là gọi `bat("thiet_bi_khong_ton_tai")` khi chưa mở phải ném `LoiPhanCung`, **không**
phải `LoiCauHinh`. Dòng 69 và 70 §6 là cặp canh đúng thứ tự này; ĐB14 §10 đảo nó lại.

Ngoại lệ từ `_tac_dong_phan_cung` trong `bat`/`tat` **lan ra ngoài, không nuốt** — trái với
`dong()`. Lý do: nuốt ở đây tái tạo đúng chế độ hỏng mà cả mã việc này sinh ra để chặn (hệ thống
báo đã bật đèn trong khi không có gì xảy ra). Người gọi ở vòng lặp chính đã có `finally: dong()`.

### 5.7. `thuc_thi(lenh: Command)` — cụ thể ở lớp cơ sở, backend KHÔNG được ghi đè

```
nếu không isinstance(lenh, Command): raise ValueError("thuc_thi cần một Command, nhận được ...")
nếu lenh.hanh_dong không thuộc HANH_DONG_HOP_LE: raise ValueError("Hành động không hợp lệ: <giá trị>")
gọi trình tự §5.6 với ten = lenh.thiet_bi, đích = (hanh_dong == "bat"), và ghi CHÍNH `lenh` vào lịch sử
```

Hai điểm chốt:

- **Ghi chính đối tượng `lenh`**, giữ nguyên `nguon` và `thoi_diem` của nó — **không** đóng mốc
  thời gian lại bằng `time.time()`. Dấu thời gian do khối quyết định gán là thứ phép đo độ trễ
  đầu-cuối ở bước 5.6 sẽ trừ; đóng mốc lại là xoá đúng đại lượng cần đo. Dòng 106 §6, ĐB15 §10.
- **Không chuẩn hoá chữ hoa/thường.** `"BAT"` là lỗi, không phải `"bat"`. Hai đường vào cho cùng
  một hành động là hai chỗ để lệch nhau về sau. Dòng 113 §6.

Ngược lại, `bat(ten, nguon=None)` và `tat(ten, nguon=None)` — cũng cụ thể ở lớp cơ sở — tự dựng
`Command(ten, "bat"/"tat", nguon, time.time())` rồi đi vào cùng trình tự.

### 5.8. `src/actuator/mock_actuator.py` — `ChapHanhGiaLap`

```python
class ChapHanhGiaLap(BoChapHanh):
    TEN_BACKEND = "mock"
    LA_GIA_LAP = True

    def __init__(self, cfg: dict) -> None: ...
    def _mo_phan_cung(self) -> None: ...
    def _tac_dong_phan_cung(self, ten_thiet_bi: str, bat_len: bool) -> None: ...
```

- `__init__` gọi `super().__init__(cfg)` trước, rồi đọc nhánh `mock` (§5.9).
- `_mo_phan_cung` phát **đúng một** dòng `logger.warning` mang nguyên văn `CANH_BAO_GIA_LAP`. Viết
  bằng lazy formatting: `logger.warning("%s", CANH_BAO_GIA_LAP)`.
- `_tac_dong_phan_cung` không chạm phần cứng; nếu độ trễ mô phỏng > 0 thì gọi **đúng dòng này**:

  ```python
  time.sleep(self._do_tre)
  ```

  ⚠️ Bắt buộc `import time` ở đầu tệp rồi gọi `time.sleep(...)`. Viết `from time import sleep` thì
  `monkeypatch.setattr(time, "sleep", ...)` **không** chặn được, và ca kiểm thử dòng 48 §6 sẽ ngủ
  thật. ĐB23 §10 dựng lại đúng bản sai này.

### 5.9. Kiểm `mock.do_tre_gia_lap_giay` — bốn phép, đúng thứ tự

| # | Điều kiện | Ném | Thông báo chứa |
|---|---|---|---|
| 1 | `cfg["mock"]` tồn tại nhưng không phải `dict` (và không phải `None`) | `LoiCauHinh` | `mock` |
| 2 | giá trị là `bool`, hoặc không phải `int`/`float` | `LoiCauHinh` | `do_tre_gia_lap_giay` |
| 3 | `not math.isfinite(gia_tri)` | `LoiCauHinh` | `hữu hạn` |
| 4 | `gia_tri < 0` | `LoiCauHinh` | `âm` |

Thiếu nhánh `mock`, hoặc `mock: None`, hoặc thiếu khoá → mặc định `0.0`, dựng bình thường.

Phép 2 phải loại `bool` **trước** vì `isinstance(True, int)` là `True` trong Python. Phép 3 là phép
dễ quên nhất và cũng là phép chịu lực: `inf`, `-inf`, `nan` lọt qua mọi phép kiểm kiểu và qua cả
phép so `< 0` (`nan < 0` là `False`), rồi `time.sleep(inf)` treo cứng tiến trình còn
`time.sleep(nan)` ném `ValueError` ở tận trong thư viện chuẩn — cả hai đều là hỏng ở nơi không ai
đi tìm. Dòng 54, 55, 56 §6 và ĐB17 §10.

### 5.10. `src/actuator/factory.py`

Hai hằng mức module, ca kiểm thử import trực tiếp:

```python
THONG_BAO_CAM_AUTO = (
    "backend='auto' bị CẤM ở khối chấp hành: không có phép dò nào phân biệt được relay đã "
    "đấu dây với relay chưa đấu dây, nên 'auto' chỉ có thể rơi về giả lập trong im lặng. "
    "Khai báo tường minh backend='mock' hoặc backend='gpio'."
)
THONG_BAO_CHUA_CO_GPIO = (
    "backend='gpio' chưa được cài đặt — thuộc mã việc P5-03. Dùng backend='mock' cho tới khi "
    "có module relay và hardware/gpio-pinout.md."
)
```

`tao_bo_chap_hanh(cfg)`:

| Trường hợp | Kết quả |
|---|---|
| thiếu khoá `backend` | `LoiCauHinh("Thiếu key bắt buộc: backend")` |
| `"mock"` | trả `ChapHanhGiaLap(cfg)` — import **bên trong nhánh** (G7) |
| `"auto"` | `LoiCauHinh(THONG_BAO_CAM_AUTO)` |
| `"gpio"` | `LoiCauHinh(THONG_BAO_CHUA_CO_GPIO)` |
| còn lại (kể cả không phải chuỗi) | `LoiCauHinh(f"Backend không hợp lệ: {backend}. Giá trị cho phép: mock, gpio")` |

**Factory không gọi `mo()`.** Khác `tao_bo_thu_hinh` — ở đó nhánh `auto` phải mở thử; ở đây không
có `auto` nên cũng không có lý do gì để chạm phần cứng lúc dựng đối tượng. Dòng 13 §6.

### 5.11. `src/actuator/__init__.py`

```python
from .base import BoChapHanh
from .factory import tao_bo_chap_hanh

__all__ = ["BoChapHanh", "tao_bo_chap_hanh"]
```

### 5.12. Ba lớp phụ trợ trong `tests/test_actuator.py`

Nhiều dòng §6 chỉ khẳng định được thông qua ba lớp con dựng riêng cho kiểm thử. Đặt **đúng tên
này** để bảng đột biến §10 trỏ tới được:

```python
class ChapHanhDem(BoChapHanh):
    """Đếm mọi lời ghi phần cứng."""
    TEN_BACKEND = "dem"
    LA_GIA_LAP = True
    # __init__ gọi super() rồi khởi tạo self.ghi_nhan: list[tuple[str, bool]] = []
    # _tac_dong_phan_cung nối (ten_thiet_bi, bat_len) vào self.ghi_nhan

class ChapHanhNem(BoChapHanh):
    """Lời ghi phần cứng ném RuntimeError khi công tắc đang bật."""
    TEN_BACKEND = "nem"
    LA_GIA_LAP = True
    # self.bat_dau_nem: bool — _tac_dong_phan_cung ném RuntimeError khi cờ này True
    # __init__ nhận cờ ban đầu để dựng được CẢ HAI kịch bản:
    #   ném ngay từ mo()          -> dòng 88, 89
    #   mo() trót lọt rồi mới ném -> dòng 85, 86, 87, 90, 91, 92

class ChapHanhGiaVoThat(ChapHanhDem):
    """Lớp tự khai là phần cứng thật — dùng cho các dòng CẶP của phần cảnh báo giả lập."""
    TEN_BACKEND = "gia_vo_that"
    LA_GIA_LAP = False
```

⚠️ `ChapHanhNem` cần công tắc vì `mo()` cũng gọi `_tac_dong_phan_cung`: không có công tắc thì
không dựng được kịch bản "mở thành công rồi hỏng giữa chừng" cho các dòng 81–83, 86–88.

---

## 6. Bảng ca kiểm thử — mỗi dòng đúng MỘT điều kiện

Ký hiệu dùng chung: `CFG2` là cấu hình tối thiểu hai thiết bị
`{"backend": "mock", "devices": {"den": {"loai": "relay"}, "tivi": {"loai": "ir"}}}`;
`CFG1` là bản chỉ có `den`. `act` là đối tượng đã `mo()` trừ khi dòng nói khác.

### Nhóm A — cấu trúc gói và ba phép từ chối của `__init_subclass__` (§5.2)

| # | Đầu vào / tình huống | Assert tối thiểu |
|---|---|---|
| 01 | tập tệp `.py` trong `src/actuator/` | `{p.name for p in (Path(__file__).resolve().parents[1] / "src" / "actuator").glob("*.py")} == {"__init__.py", "base.py", "mock_actuator.py", "factory.py"}` |
| 02 | định nghĩa lớp con **không** khai `TEN_BACKEND` | `pytest.raises(TypeError, match="TEN_BACKEND")` |
| 03 | định nghĩa lớp con khai `TEN_BACKEND = ""` | `pytest.raises(TypeError, match="TEN_BACKEND")` |
| 04 | định nghĩa lớp con **không** khai `LA_GIA_LAP` | `pytest.raises(TypeError, match="LA_GIA_LAP")` |
| 05 | lớp con ghi đè `thuc_thi` | `pytest.raises(TypeError, match="thuc_thi")` |
| 06 | lớp con ghi đè `bat` | `pytest.raises(TypeError, match="bat")` |
| 07 | lớp con ghi đè `dong` | `pytest.raises(TypeError, match="dong")` |
| 08 | **đường cặp**: lớp con khai đủ hai hằng, không ghi đè gì | `ChapHanhDem.TEN_BACKEND == "dem"` |
| 09 | `ChapHanhGiaLap` không ghi đè `thuc_thi` | `ChapHanhGiaLap.thuc_thi is BoChapHanh.thuc_thi` |
| 10 | khởi tạo thẳng lớp cơ sở: `BoChapHanh(CFG2)` | `pytest.raises(TypeError)` |

### Nhóm B — factory và phép cấm `auto` (§4.1, §5.10)

| # | Đầu vào / tình huống | Assert tối thiểu |
|---|---|---|
| 11 | `cfg` không có khoá `backend` | `pytest.raises(LoiCauHinh, match="Thiếu key bắt buộc: backend")` |
| 12 | `CFG2` với `backend: "mock"` | `isinstance(tao_bo_chap_hanh(CFG2), ChapHanhGiaLap)` |
| 13 | factory **không** tự mở | `tao_bo_chap_hanh(CFG2).dang_mo is False` |
| 14 | `backend: "auto"` | `pytest.raises(LoiCauHinh)` |
| 15 | thông báo của `auto` nêu đích danh giá trị | `"auto" in str(e.value)` |
| 16 | thông báo của `auto` nêu rõ đây là phép cấm cố ý | `"CẤM" in str(e.value)` |
| 17 | `backend: "gpio"` | `pytest.raises(LoiCauHinh)` |
| 18 | thông báo của `gpio` trỏ sang mã việc kế tiếp | `"P5-03" in str(e.value)` |
| 19 | `auto` **không** rơi chung nhánh với `gpio` | `THONG_BAO_CAM_AUTO != THONG_BAO_CHUA_CO_GPIO` |
| 20 | `backend: "khong_co_that"` | `pytest.raises(LoiCauHinh, match="Backend không hợp lệ")` |
| 21 | `auto` **không** rơi chung nhánh mặc định | `str(e_auto.value) != str(e_khong_co.value)` |
| 22 | `backend: 123` (không phải chuỗi) | `pytest.raises(LoiCauHinh, match="Backend không hợp lệ")` |

### Nhóm C — ★★ phơi ra nguồn thật (§4.3)

| # | Đầu vào / tình huống | Assert tối thiểu |
|---|---|---|
| 23 | dựng qua factory với `backend: "mock"` | `tao_bo_chap_hanh(CFG2).ten_backend == "mock"` |
| 24 | ★ dựng **thẳng** `ChapHanhGiaLap({**CFG2, "backend": "gpio"})` — cấu hình nói dối | `.ten_backend == "mock"` |
| 25 | ★ cùng đối tượng nói dối ở dòng 24 | `.la_gia_lap is True` |
| 26 | tập khoá của `mo_ta_nguon()` | `set(act.mo_ta_nguon()) == {"backend", "la_gia_lap", "canh_bao_nguon_gia_lap"}` |
| 27 | `mo_ta_nguon()` khoá `backend` | `act.mo_ta_nguon()["backend"] == "mock"` |
| 28 | `mo_ta_nguon()` khoá `la_gia_lap` | `act.mo_ta_nguon()["la_gia_lap"] is True` |
| 29 | `mo_ta_nguon()` khoá cảnh báo | `act.mo_ta_nguon()["canh_bao_nguon_gia_lap"] == CANH_BAO_GIA_LAP` |
| 30 | **đường cặp**: `ChapHanhGiaVoThat(CFG2).mo_ta_nguon()` | `...["canh_bao_nguon_gia_lap"] is None` |
| 31 | **đường cặp**: cùng đối tượng dòng 30 | `ChapHanhGiaVoThat(CFG2).la_gia_lap is False` |
| 32 | ★ `mo()` của `mock` phát nguyên văn cảnh báo | với `caplog.at_level(logging.WARNING)`: `CANH_BAO_GIA_LAP in caplog.text` |
| 33 | ★ cảnh báo đó ở mức WARNING trở lên, không phải INFO | `any(r.levelno >= logging.WARNING for r in caplog.records)` |
| 34 | **đường cặp**: `ChapHanhGiaVoThat(CFG2).mo()` không phát cảnh báo nào | `[r for r in caplog.records if r.levelno >= logging.WARNING] == []` |

### Nhóm D — nạp `devices` (§5.3)

| # | Đầu vào / tình huống | Assert tối thiểu |
|---|---|---|
| 35 | `cfg` không có `devices` | `pytest.raises(LoiCauHinh, match="Thiếu key bắt buộc: devices")` |
| 36 | `devices: {}` | `pytest.raises(LoiCauHinh, match="devices")` |
| 37 | `devices: []` | `pytest.raises(LoiCauHinh, match="devices")` |
| 38 | `devices: "den"` | `pytest.raises(LoiCauHinh, match="devices")` |
| 39 | `devices: {"den": "khong_phai_dict"}` | `pytest.raises(LoiCauHinh, match="den")` |
| 40 | `devices: {"den": {}}` — thiếu `loai` | `pytest.raises(LoiCauHinh, match="loai")` |
| 41 | `devices: {"den": {"loai": "bong_den"}}` — `loai` ngoài tập | `pytest.raises(LoiCauHinh, match="loai")` |
| 42 | `devices: {"": {"loai": "relay"}}` — tên rỗng | `pytest.raises(LoiCauHinh, match="Tên thiết bị")` |
| 43 | `devices: {"   ": {"loai": "relay"}}` — tên toàn khoảng trắng | `pytest.raises(LoiCauHinh, match="Tên thiết bị")` |
| 44 | `devices: {123: {"loai": "relay"}}` — tên không phải chuỗi | `pytest.raises(LoiCauHinh, match="Tên thiết bị")` |
| 45 | **đường cặp**: `loai: "relay"` **không** kèm khối `gpio` vẫn dựng được | `ChapHanhGiaLap(CFG1).loai_thiet_bi("den") == "relay"` |
| 46 | **đường cặp**: `loai: "ir"` **không** kèm khối `ir` vẫn dựng được | `ChapHanhGiaLap(CFG2).loai_thiet_bi("tivi") == "ir"` |
| 47 | cấu hình có khoá lạ mức trên cùng: `{**CFG2, "decision": {"n_frame_xac_nhan": 3}}` | `ChapHanhGiaLap(...).danh_sach_thiet_bi == ("den", "tivi")` |
| 48 | ★ `danh_sach_thiet_bi` sắp theo bảng chữ cái dù YAML khai ngược: `devices` khai `{"zzz": ..., "aaa": ...}` | `.danh_sach_thiet_bi == ("aaa", "zzz")` |
| 49 | `loai_thiet_bi` với tên lạ | `pytest.raises(LoiCauHinh, match="khong_co")` |

### Nhóm E — tham số số `mock.do_tre_gia_lap_giay` (§5.9)

Ở các dòng đếm `time.sleep`, đặt `monkeypatch.setattr(time, "sleep", ghi_nhan.append)` rồi
**xoá sạch `ghi_nhan` sau khi `mo()` xong** — `mo()` cũng đi qua `_tac_dong_phan_cung`.

| # | Đầu vào / tình huống | Assert tối thiểu |
|---|---|---|
| 50 | cfg **không có** nhánh `mock`, gọi `act.bat("den")` | `ghi_nhan == []` |
| 51 | `mock: None`, dựng bình thường | `ChapHanhGiaLap({**CFG1, "mock": None}).danh_sach_thiet_bi == ("den",)` |
| 52 | `mock: "khong_phai_dict"` | `pytest.raises(LoiCauHinh, match="mock")` |
| 53 | `do_tre_gia_lap_giay: 0` → không ngủ | `ghi_nhan == []` |
| 54 | ★ **đường thành công**: `do_tre_gia_lap_giay: 0.05`, gọi `act.bat("den")` | `ghi_nhan == [0.05]` |
| 55 | `do_tre_gia_lap_giay: -0.1` | `pytest.raises(LoiCauHinh, match="âm")` |
| 56 | `do_tre_gia_lap_giay: "0.1"` | `pytest.raises(LoiCauHinh, match="do_tre_gia_lap_giay")` |
| 57 | `do_tre_gia_lap_giay: True` | `pytest.raises(LoiCauHinh, match="do_tre_gia_lap_giay")` |
| 58 | `do_tre_gia_lap_giay: None` | `pytest.raises(LoiCauHinh, match="do_tre_gia_lap_giay")` |
| 59 | ★ `do_tre_gia_lap_giay: float("inf")` | `pytest.raises(LoiCauHinh, match="hữu hạn")` |
| 60 | ★ `do_tre_gia_lap_giay: float("-inf")` | `pytest.raises(LoiCauHinh, match="hữu hạn")` |
| 61 | ★ `do_tre_gia_lap_giay: float("nan")` | `pytest.raises(LoiCauHinh, match="hữu hạn")` |

### Nhóm F — vòng đời và fail-safe R24 (§5.4, §5.5)

⚠️ **Tiền đề cho dòng 85, 86, 87** — không có tiền đề này thì `dong()` chẳng có gì để tắt và ba
dòng sẽ xanh mà không đi qua nhánh cần kiểm: dùng `ChapHanhNem` với công tắc **tắt**, gọi `mo()`
rồi `bat("den")` cho thành công, **sau đó** mới bật công tắc ném, rồi mới gọi `dong()`.

⚠️ **Tiền đề cho dòng 90, 91, 92**: y hệt, nhưng bật công tắc ngay sau `mo()` — trước lời gọi
`bat("den")` đầu tiên.

| # | Đầu vào / tình huống | Assert tối thiểu |
|---|---|---|
| 62 | ngay sau khi dựng, chưa `mo()` | `tao_bo_chap_hanh(CFG2).dang_mo is False` |
| 63 | sau `mo()` | `act.dang_mo is True` |
| 64 | sau `mo()`, mọi thiết bị TẮT | `act.trang_thai_tat_ca() == {"den": False, "tivi": False}` |
| 65 | sau `mo()`, lịch sử rỗng (lời ép tắt không vào lịch sử) | `act.lich_su == []` |
| 66 | ★★ `mo()` **ghi mức TẮT xuống phần cứng** đúng một lần mỗi thiết bị (dùng `ChapHanhDem`) | `act.ghi_nhan == [("den", False), ("tivi", False)]` |
| 67 | `mo()` gọi hai lần liên tiếp không ghi phần cứng lần hai | `len(act.ghi_nhan) == 2` sau lời gọi `mo()` thứ hai |
| 68 | `bat` khi chưa `mo()` | `pytest.raises(LoiPhanCung, match="chưa mở")` |
| 69 | `tat` khi chưa `mo()` | `pytest.raises(LoiPhanCung, match="chưa mở")` |
| 70 | `thuc_thi` khi chưa `mo()` | `pytest.raises(LoiPhanCung, match="chưa mở")` |
| 71 | `trang_thai("den")` khi chưa `mo()` | `pytest.raises(LoiPhanCung, match="chưa mở")` |
| 72 | `trang_thai_tat_ca()` sau khi `dong()` | `pytest.raises(LoiPhanCung, match="chưa mở")` |
| 73 | `bat` sau khi `dong()` | `pytest.raises(LoiPhanCung, match="chưa mở")` |
| 74 | ★ thứ tự kiểm: `bat("khong_co")` **khi chưa mở** | `pytest.raises(LoiPhanCung)` |
| 75 | ★ **đường cặp**: `bat("khong_co")` khi **đã mở** | `pytest.raises(LoiCauHinh, match="chưa khai báo")` |
| 76 | `dong()` gọi hai lần không ném | `act.dong()` lần hai chạy hết mà không có ngoại lệ |
| 77 | `dong()` lần hai không thêm bản ghi | sau `bat("den"); dong(); n = len(act.lich_su); dong()` → `len(act.lich_su) == n` |
| 78 | `mo()` sau `dong()` xoá lịch sử | sau `bat("den"); dong(); mo()` → `act.lich_su == []` |
| 79 | `mo()` sau `dong()` đặt lại trạng thái TẮT | sau chuỗi ở dòng 78 → `act.trang_thai("den") is False` |
| 80 | context manager mở đúng | `with act: assert act.dang_mo is True` |
| 81 | context manager đóng đúng | sau khối `with` → `act.dang_mo is False` |
| 82 | ★★ **R24**: ngoại lệ trong khối `with` vẫn tắt hết và để lại vết | với `pytest.raises(ValueError)` bọc `with act:` có `act.bat("den")` rồi `raise ValueError("x")` → `act.lich_su_rut_gon == [("den", "bat"), ("den", "tat")]` |
| 83 | nguồn của bản ghi tự-tắt | sau dòng 82 → `act.lich_su[-1].nguon == NGUON_HE_THONG` |
| 84 | `dong()` **không** tắt lại thiết bị vốn đang tắt | `mo(); dong()` → `act.lich_su == []` |
| 85 | `dong()` không ném dù lời ghi phần cứng hỏng (`ChapHanhNem`) | `act.dong()` chạy hết mà không có ngoại lệ |
| 86 | và ghi lại lỗi ở mức ERROR | `any(r.levelno == logging.ERROR for r in caplog.records)` |
| 87 | và vẫn đóng được | `act.dang_mo is False` |
| 88 | ★ lời ghi phần cứng hỏng trong `mo()` → ngoại lệ lan ra | `pytest.raises(RuntimeError)` khi gọi `mo()` |
| 89 | ★ và đối tượng ở lại trạng thái **chưa mở** | `act.dang_mo is False` |
| 90 | ★ lời ghi phần cứng hỏng trong `bat()` → ngoại lệ lan ra, **không nuốt** | `pytest.raises(RuntimeError)` khi gọi `bat("den")` |
| 91 | ★ và **không** ghi lịch sử cho lệnh chưa thực hiện | `act.lich_su == []` |
| 92 | ★ và trạng thái không đổi | `act.trang_thai("den") is False` |

### Nhóm G — bật/tắt, luỹ đẳng, lịch sử (§4.4, §4.5, §5.6)

| # | Đầu vào / tình huống | Assert tối thiểu |
|---|---|---|
| 93 | **đường thành công**: `bat("den")` | `act.trang_thai("den") is True` |
| 94 | **đường thành công**: `tat("den")` sau khi đã bật | `act.trang_thai("den") is False` |
| 95 | `bat("den")` không đụng thiết bị khác | `act.trang_thai("tivi") is False` |
| 96 | `bat("den")` ghi đúng một bản ghi | `act.lich_su_rut_gon == [("den", "bat")]` |
| 97 | `bat` hai lần **không ném** (luỹ đẳng) | lời gọi `act.bat("den")` thứ hai chạy hết mà không có ngoại lệ |
| 98 | ★ `bat` hai lần vẫn ghi **cả hai** vào lịch sử | `act.lich_su_rut_gon == [("den", "bat"), ("den", "bat")]` |
| 99 | ★ `bat` hai lần chỉ ghi phần cứng **một** lần (`ChapHanhDem`, xoá `ghi_nhan` sau `mo()`) | `act.ghi_nhan == [("den", True)]` |
| 100 | `tat` thiết bị vốn đang tắt vẫn vào lịch sử | `act.lich_su_rut_gon == [("den", "tat")]` |
| 101 | `tat` thiết bị vốn đang tắt không ghi phần cứng | `act.ghi_nhan == []` |
| 102 | `bat("den", nguon="u01")` ghi đúng nguồn | `act.lich_su[-1].nguon == "u01"` |
| 103 | `bat("den")` không truyền nguồn | `act.lich_su[-1].nguon is None` |
| 104 | ★ `lich_su` trả **bản sao** | sau `act.bat("den"); ls = act.lich_su; ls.clear()` → `len(act.lich_su) == 1` |
| 105 | ★ `trang_thai_tat_ca()` trả **bản sao** | sau `d = act.trang_thai_tat_ca(); d["den"] = True` → `act.trang_thai("den") is False` |
| 106 | `trang_thai("khong_co")` khi đã mở | `pytest.raises(LoiCauHinh, match="chưa khai báo")` |

### Nhóm H — `thuc_thi(Command)` (§5.7)

| # | Đầu vào / tình huống | Assert tối thiểu |
|---|---|---|
| 107 | **đường thành công**: `thuc_thi(Command("den", "bat", "u01", 123.0))` | `act.trang_thai("den") is True` |
| 108 | giữ nguyên `nguon` của lệnh | `act.lich_su[-1].nguon == "u01"` |
| 109 | ★★ giữ nguyên `thoi_diem` của lệnh, **không** đóng mốc lại | `act.lich_su[-1].thoi_diem == 123.0` |
| 110 | ghi **chính** đối tượng lệnh vào lịch sử | `act.lich_su == [Command("den", "bat", "u01", 123.0)]` |
| 111 | **đường thành công**: `thuc_thi(Command("den", "tat", None, 1.0))` sau khi đã bật | `act.trang_thai("den") is False` |
| 112 | `hanh_dong` lạ: `Command("den", "nhap_nhay", None, 1.0)` | `pytest.raises(ValueError, match="nhap_nhay")` |
| 113 | `hanh_dong` lạ **không** vào lịch sử | `act.lich_su == []` |
| 114 | `hanh_dong` lạ **không** đổi trạng thái | `act.trang_thai("den") is False` |
| 115 | ★ `hanh_dong` viết hoa: `Command("den", "BAT", None, 1.0)` — không tự chuẩn hoá | `pytest.raises(ValueError, match="BAT")` |
| 116 | đối số không phải `Command`: truyền một `dict` | `pytest.raises(ValueError, match="Command")` |
| 117 | `thuc_thi` với thiết bị lạ khi đã mở | `pytest.raises(LoiCauHinh, match="chưa khai báo")` |

### Nhóm I — tệp `configs/actuator.yaml` thật (§3.7)

Nạp bằng `nap_cau_hinh(Path(__file__).resolve().parents[1] / "configs" / "actuator.yaml")`.

| # | Đầu vào / tình huống | Assert tối thiểu |
|---|---|---|
| 118 | nạp được | `isinstance(cfg, dict)` |
| 119 | backend khai tường minh là `mock` | `cfg["backend"] == "mock"` |
| 120 | dựng được qua factory | `isinstance(tao_bo_chap_hanh(cfg), ChapHanhGiaLap)` |
| 121 | đúng hai thiết bị đại diện của MT5 | `act.danh_sach_thiet_bi == ("den_phong_khach", "tivi_phong_khach")` |
| 122 | nhóm đèn là relay | `act.loai_thiet_bi("den_phong_khach") == "relay"` |
| 123 | nhóm tivi là IR | `act.loai_thiet_bi("tivi_phong_khach") == "ir"` |
| 124 | nhánh `decision` của `P5-02` có mặt trong tệp | `"decision" in cfg` |
| 125 | và **không** làm hỏng phép nạp của mã việc này | `with tao_bo_chap_hanh(cfg) as a: assert a.lich_su == []` |
| 126 | tệp thật đi qua đủ vòng đời bật/tắt | với `with tao_bo_chap_hanh(cfg) as a: a.bat("den_phong_khach")` → sau khối, `a.lich_su_rut_gon == [("den_phong_khach", "bat"), ("den_phong_khach", "tat")]` |

---

## 7. Tham số → config

| Tham số | Tệp config | Key | Mặc định | Bắt buộc? |
|---|---|---|---|---|
| Backend chấp hành | `configs/actuator.yaml` | `backend` | — | **có** |
| Bảng thiết bị | `configs/actuator.yaml` | `devices` | — | **có** |
| Loại từng thiết bị | `configs/actuator.yaml` | `devices.<ten>.loai` | — | **có** |
| Độ trễ mô phỏng (giây) | `configs/actuator.yaml` | `mock.do_tre_gia_lap_giay` | `0.0` | không |
| Chân GPIO, `active_low` | `configs/actuator.yaml` | `devices.<ten>.gpio.*` | `TBD` | **P5-03 đọc, P5-01 bỏ qua** |
| Chân IR, tần số, mã lệnh | `configs/actuator.yaml` | `devices.<ten>.ir.*` | `TBD` | **P5-03 đọc, P5-01 bỏ qua** |
| Chống nhiễu, cooldown | `configs/actuator.yaml` | `decision.*` | tạm | **P5-02 đọc, P5-01 bỏ qua** |

> Không hardcode. Thiếu khoá bắt buộc → `LoiCauHinh` nêu đích danh khoá thiếu (§5.3, §5.10).

---

## 8. Giao diện bắt buộc — giữ nguyên tên và kiểu

```python
# src/actuator/base.py
NGUON_HE_THONG: str
HANH_DONG_HOP_LE: tuple[str, ...]
LOAI_THIET_BI_HOP_LE: tuple[str, ...]
PHUONG_THUC_KHOA: tuple[str, ...]
CANH_BAO_GIA_LAP: str


class BoChapHanh(ABC):
    """Lớp cơ sở cho mọi backend chấp hành. Phần chung đã cài sẵn — xem §4.2."""

    TEN_BACKEND: str
    LA_GIA_LAP: bool

    def __init_subclass__(cls, **kwargs: object) -> None: ...
    def __init__(self, cfg: dict) -> None: ...

    # --- phơi ra nguồn thật (§4.3) ---
    @property
    def ten_backend(self) -> str: ...
    @property
    def la_gia_lap(self) -> bool: ...
    def mo_ta_nguon(self) -> dict[str, object]: ...

    # --- vòng đời ---
    def mo(self) -> None: ...
    def dong(self) -> None: ...
    @property
    def dang_mo(self) -> bool: ...
    def __enter__(self) -> "BoChapHanh": ...
    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None: ...

    # --- tác động ---
    def bat(self, ten_thiet_bi: str, nguon: str | None = None) -> None: ...
    def tat(self, ten_thiet_bi: str, nguon: str | None = None) -> None: ...
    def thuc_thi(self, lenh: Command) -> None: ...

    # --- đọc ---
    @property
    def danh_sach_thiet_bi(self) -> tuple[str, ...]: ...
    def loai_thiet_bi(self, ten_thiet_bi: str) -> str: ...
    def trang_thai(self, ten_thiet_bi: str) -> bool: ...
    def trang_thai_tat_ca(self) -> dict[str, bool]: ...
    @property
    def lich_su(self) -> list[Command]: ...
    @property
    def lich_su_rut_gon(self) -> list[tuple[str, str]]: ...

    # --- điểm nối cho backend ---
    @abstractmethod
    def _tac_dong_phan_cung(self, ten_thiet_bi: str, bat_len: bool) -> None: ...
    def _mo_phan_cung(self) -> None: ...    # mặc định không làm gì
    def _dong_phan_cung(self) -> None: ...  # mặc định không làm gì


# src/actuator/mock_actuator.py
class ChapHanhGiaLap(BoChapHanh):
    TEN_BACKEND = "mock"
    LA_GIA_LAP = True

    def __init__(self, cfg: dict) -> None: ...
    def _mo_phan_cung(self) -> None: ...
    def _tac_dong_phan_cung(self, ten_thiet_bi: str, bat_len: bool) -> None: ...


# src/actuator/factory.py
THONG_BAO_CAM_AUTO: str
THONG_BAO_CHUA_CO_GPIO: str


def tao_bo_chap_hanh(cfg: dict) -> BoChapHanh: ...
```

Docstring tiếng Việt kiểu Google cho mọi hàm/thuộc tính public — người cài đặt viết đầy đủ, kể cả
mục `Raises:`. Docstring của `trang_thai` và `trang_thai_tat_ca` **bắt buộc** chứa chữ "giả định"
(§4.6).

---

## 9. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

### 9.0. Lấy mốc TRƯỚC khi tạo tệp nào

```bash
git rev-parse --short HEAD
```

```bash
python -m pytest -q
```

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

Mốc để tham chiếu (§3.6): `875 passed, 3 skipped` và `845 passed, 1 skipped, 32 deselected`.
**Con số bạn thu được chính là mốc thật** — ghi lại kèm commit đang đứng, rồi mọi con số về sau
phát biểu bằng **phép trừ** so với mốc này, không phát biểu bằng số tuyệt đối.

### 9.1. Định dạng và ca kiểm thử của riêng khối

```bash
python -m black --check --line-length 100 src/actuator tests/test_actuator.py
```

```bash
python -m ruff check src/actuator tests/test_actuator.py
```

```bash
python -m pytest tests/test_actuator.py -q
```

Kỳ vọng: **mọi ca xanh, 0 skipped, 0 failed**. Một ca `skipped` nghĩa là ca đó đang phụ thuộc thứ
mà §3.5 nói không có — sửa ca test, không thêm `skipif`.

### 9.2. Chốt phạm vi

```bash
python -m pytest tests/test_actuator.py --collect-only -q | grep -c "::test_"
```

Kỳ vọng: **≥ 126** — mỗi dòng §6 ít nhất một ca.

```bash
git status --short --untracked-files=all
```

Kỳ vọng — đúng hai nhóm dòng, không có nhóm thứ ba:

| Dòng | Ai tạo ra |
|---|---|
| `?? src/actuator/__init__.py`, `?? src/actuator/base.py`, `?? src/actuator/mock_actuator.py`, `?? src/actuator/factory.py`, `?? tests/test_actuator.py` | **bạn** |
| các tệp `.docx` trong `docs/bao-cao-tuan/` nếu có | có từ trước mã việc này |

⚠️ `configs/actuator.yaml` và `docs/dac-ta/P5-01-actuator-base-mock.md` **không được** xuất hiện —
chúng đã commit trước khi bạn nhận việc. Thấy chúng ở dạng ` M` là bạn đã sửa nhầm.

Cờ `--untracked-files=all` là bắt buộc: thiếu nó, git gộp cả thư mục `src/actuator/` mới thành
**một** dòng và phép đếm sai (đúng lỗi đã xảy ra ở `P1-01`, trả `3` trong khi thực tế `7`).

```bash
git diff --name-only dev
```

Kỳ vọng: **rỗng hoàn toàn** — mã việc này chỉ thêm tệp mới, không sửa tệp đã có.

### 9.3. Chạy toàn bộ, hai môi trường

```bash
python -m pytest -q
```

Kỳ vọng: `passed` = mốc §9.0 **cộng** số ca mới; `0 failed`; số `skipped` **không đổi** so với mốc.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

Kỳ vọng: số `passed` tăng **đúng bằng** mức tăng trên host, và `deselected` **không đổi** (`32`).
Lệch nghĩa là có ca phụ thuộc thứ container không có, hoặc bạn đã lỡ gắn `slow`.

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest --collect-only -q tests/test_actuator.py
```

Kỳ vọng: thu thập **đủ** số ca, **không** lỗi import. Lệnh này bắt riêng chế độ hỏng "import ở mức
module một thứ container không có" — đã làm đổ cả bộ kiểm thử ở `P2-01` và `P2-03`.

### 9.4. Quét mẫu vi phạm

```bash
grep -rnE "print\(" src/actuator/
```

Phải **rỗng** — R23, G2.

```bash
grep -rnE "logger\.(debug|info|warning|error|critical)\(f[\"']" src/actuator/
```

Phải **rỗng** — G3, log dùng lazy formatting.

```bash
grep -rn "except Exception" src/actuator/base.py
```

Kỳ vọng: **đúng hai dòng**, cả hai nằm trong `dong()` (§5.5), cả hai đều có `logger.error` ngay
sau. Không hơn, không kém.

```bash
grep -rn "except Exception" src/actuator/mock_actuator.py src/actuator/factory.py src/actuator/__init__.py
```

Phải **rỗng**.

```bash
grep -rnE "except\s*:" src/actuator/ tests/test_actuator.py
```

Phải **rỗng** — G5, không `except:` trần.

```bash
grep -rnE "^\s*(import|from)\s+(RPi|gpiozero|pigpio|serial|lirc)" src/actuator/ tests/test_actuator.py
```

Phải **rỗng** — không phụ thuộc phần cứng ở mã việc này (§3.5).

```bash
grep -rnE "\b(17|18|27|22|38000)\b" src/actuator/
```

Phải **rỗng** — G1. Số chân GPIO và tần số sóng mang chỉ được nằm trong `configs/actuator.yaml`.

```bash
grep -rn "from time import" src/actuator/
```

Phải **rỗng** — §5.8 bắt buộc `import time` rồi gọi `time.sleep(...)`.

```bash
grep -rn "time.sleep" src/actuator/
```

Kỳ vọng: **đúng một dòng**, trong `mock_actuator.py`.

```bash
grep -n "pytest.mark.slow" tests/test_actuator.py
```

Phải **rỗng** (§3.5).

```bash
grep -nE "subprocess|urlopen|requests\.|socket" tests/test_actuator.py | grep -v "monkeypatch\|mock\|patch("
```

Phải **rỗng** — không ca nào gọi tiến trình ngoài hay chạm mạng. Vế loại trừ ở sau là **cố ý**:
vá bằng `monkeypatch` là cách phòng thủ đúng đắn, cấm luôn cả nó thì lệnh kiểm tự phá biện pháp
mạnh nhất.

### 9.5. Nhìn tận mắt dòng cảnh báo giả lập

```bash
python -c "import logging,sys; logging.basicConfig(level=logging.INFO); sys.path.insert(0,'.'); from src.common.config import nap_cau_hinh; from src.actuator import tao_bo_chap_hanh; a=tao_bo_chap_hanh(nap_cau_hinh('configs/actuator.yaml')); print(a.mo_ta_nguon()); a.mo(); a.bat('den_phong_khach', 'u01'); print(a.lich_su_rut_gon); a.dong(); print(a.lich_su_rut_gon)"
```

Kỳ vọng, dán nguyên văn về:

1. Dòng dict đầu tiên có `'backend': 'mock'`, `'la_gia_lap': True`, và khoá
   `'canh_bao_nguon_gia_lap'` mang chuỗi cảnh báo — **không** phải `None`.
2. Một dòng log mức `WARNING` mang nguyên văn `CANH_BAO_GIA_LAP`.
3. `[('den_phong_khach', 'bat')]` rồi `[('den_phong_khach', 'bat'), ('den_phong_khach', 'tat')]`.

Lệnh này không ghi gì ra đĩa nên bạn được chạy (R42). Người review sẽ chạy lại.

---

## 10. Phép đột biến bắt buộc

Mỗi phép: sao lưu tệp **ra ngoài repo** → sửa → chạy `python -m pytest tests/test_actuator.py -q` →
ghi ca đỏ → khôi phục → đối chiếu `sha256`. Tuyệt đối **không** `git checkout -- <tệp>`.

| # | Phép đột biến | Dòng §6 **phải** đỏ |
|---|---|---|
| ĐB1 | ★★ Đổi `ChapHanhGiaLap` thành `TEN_BACKEND = "gpio"`, `LA_GIA_LAP = False` | 23, 24, 25, 27, 28, 29 |
| ĐB2 | ★★ `_mo_phan_cung` của `mock` dùng `logger.info` thay `logger.warning` | 32, 33 |
| ĐB3 | ★★ `ten_backend` trả `self.cfg.get("backend", "")` | 24 (dòng 23 vẫn xanh) |
| ĐB4 | `mo_ta_nguon` luôn trả `canh_bao_nguon_gia_lap = None` | 29 |
| ĐB5 | ★★ Bỏ vòng ép TẮT phần cứng trong `mo()` | 66 (dòng 64 vẫn xanh) |
| ĐB6 | `mo()` không xoá `_lich_su` | 78 |
| ĐB7 | `dong()` không ghi bản ghi tự-tắt vào lịch sử | 82, 83 |
| ĐB8 | `dong()` ghi `nguon=None` thay vì `NGUON_HE_THONG` | 83 |
| ĐB9 | `dong()` tắt cả thiết bị vốn đang tắt | 84 |
| ĐB10 | Bỏ `try/except` quanh lời ghi phần cứng trong `dong()` | 85, 87 |
| ĐB11 | `mo()` đặt `_dang_mo = True` **trước** vòng ép TẮT | 89 |
| ĐB12 | `bat` ghi lịch sử **trước** khi gọi phần cứng | 91 |
| ĐB13 | `bat` nuốt ngoại lệ của `_tac_dong_phan_cung` và chỉ log | 90 |
| ĐB14 | ★ Đảo thứ tự: kiểm tên thiết bị **trước** `dang_mo` | 74 |
| ĐB15 | `bat` bỏ qua ghi lịch sử khi trạng thái không đổi | 98, 100 |
| ĐB16 | `bat` vẫn ghi phần cứng khi trạng thái không đổi | 99, 101 |
| ĐB17 | ★★ `thuc_thi` dựng `Command` mới với `time.time()` thay vì giữ `lenh` | 109, 110 |
| ĐB18 | `thuc_thi` chuẩn hoá `lenh.hanh_dong.lower()` | 115 |
| ĐB19 | Bỏ `math.isfinite` khi kiểm `do_tre_gia_lap_giay` | 59, 60, 61 |
| ĐB20 | Bỏ phép loại `bool` khi kiểm `do_tre_gia_lap_giay` | 57 |
| ĐB21 | `lich_su` trả thẳng danh sách nội bộ | 104 |
| ĐB22 | `trang_thai_tat_ca` trả thẳng dict nội bộ | 105 |
| ĐB23 | ★ Bỏ nhánh `auto` trong factory, để rơi vào nhánh mặc định | 16, 21 |
| ĐB24 | `danh_sach_thiet_bi` trả theo thứ tự khai báo, không sắp xếp | 48 |
| ĐB25 | Bỏ phép kiểm ghi đè `PHUONG_THUC_KHOA` trong `__init_subclass__` | 05, 06, 07 |
| ĐB26 | `mock_actuator.py` dùng `from time import sleep` rồi gọi `sleep(...)` | 54 |
| ĐB27 | `trang_thai_tat_ca` trả trạng thái cũ thay vì ném khi đã đóng | 72 |

**Bốn phép ★★ là những phép quan trọng nhất — cả bốn đều dựng lại một cài đặt *tự nhất quán*:**

- **ĐB1** — đây chính là chế độ hỏng mà cả mã việc sinh ra để chặn: giả lập chạy trong khi mọi thứ
  khác trông như thật. Lịch sử vẫn đúng, trạng thái vẫn đúng, mọi dòng §6 khác vẫn xanh; chỉ bốn
  chốt phơi-nguồn phân biệt được. **Nếu ĐB1 không làm sáu dòng kia đỏ thì bộ ca test đang canh sai
  chỗ — sửa ca test, đừng sửa mã sản phẩm.**
- **ĐB2** — hệ thống hoạt động hoàn hảo, chỉ có dòng cảnh báo tụt xuống mức INFO, nghĩa là nó biến
  mất khỏi log vận hành mặc định. Không có ca nào canh mức log thì khuyết tật này không tồn tại
  với bộ kiểm thử.
- **ĐB5** — dict trạng thái vẫn khởi tạo `False`, mọi phép **đọc** trạng thái vẫn đúng, dòng 64 vẫn
  xanh. Khác biệt duy nhất là chân GPIO còn nguyên mức từ lần chạy trước. Chỉ dòng 66 — đếm lời gọi
  phần cứng — phân biệt được.
- **ĐB17** — `Command` mới có đủ `thiet_bi`, `hanh_dong`, `nguon`; `lich_su_rut_gon` không đổi một
  phần tử nào. Chỉ `thoi_diem` lệch, mà đó đúng là đại lượng phép đo độ trễ bước 5.6 sẽ trừ.

---

## 11. Ràng buộc kỹ thuật

- **Python ≥ 3.11, và không dùng gì chỉ có từ 3.12.** Pi OS đóng gói **3.11.2**; container đóng gói
  3.11.16. Bảy ca test đã từng xanh trong container mà đỏ trên Pi vì lệch đúng mốc 3.11.4 — đừng
  lặp lại. Không `type` statement kiểu 3.12, không `itertools.batched`.
- `black --line-length 100` sạch, `ruff check` sạch. Type hints cho mọi hàm public, docstring tiếng
  Việt kiểu Google có mục `Raises:`.
- **Thư viện được phép dùng: CHỈ thư viện chuẩn** — `abc`, `math`, `time`, `logging` (qua
  `src.common.logging.lay_logger`). Trong `tests/`: thêm `pytest` và `pathlib`, cộng
  `src.common.config.nap_cau_hinh` cho Nhóm I. **Không** `numpy`, **không** `yaml` trực tiếp,
  **không** `cv2`, **không** phụ thuộc mới.
- Ngoại lệ chỉ dùng `LoiCauHinh` / `LoiPhanCung` từ `src/common/exceptions.py`, cộng `ValueError` và
  `TypeError` đúng ba chỗ đã nêu ở §4.7 và §5.2. **Không** `raise Exception`, **không**
  `raise RuntimeError` trong `src/`.
- Không `print()`; log lazy formatting; không `except:` trần; `except Exception` đúng hai chỗ ở
  `base.py::dong()`.
- Mọi ca kiểm thử chạy được khi thiếu `git`, `.git/`, `models/`, `data/`, `results/`, và mọi phần
  cứng GPIO. Không ca nào mang `@pytest.mark.slow`. Tệp tạm chỉ ghi vào `tmp_path`.
- Ca kiểm thử **không được ngủ thật**: mọi dòng đụng `do_tre_gia_lap_giay > 0` phải
  `monkeypatch.setattr(time, "sleep", ...)`.
- **Không tạo tệp mới trong `src/actuator/` ngoài bốn tệp §2** — dòng 01 §6 khoá cứng tập tên tệp.

---

## 12. Ngoài phạm vi — KHÔNG làm ở mã việc này

| Việc | Thuộc về | Vì sao không làm bây giờ |
|---|---|---|
| `src/actuator/gpio_backend.py` — relay/LED qua GPIO | **P5-03**, bước 5.2 | Chưa có module relay, chưa có LED, chưa có `hardware/gpio-pinout.md` (`hardware/` mới chỉ có `.gitkeep`). Thêm `gpiozero`/`RPi.GPIO` còn buộc dựng lại `faceid:arm64` (R43) |
| `src/actuator/ir_backend.py` — phát IR cho tivi | **P5-03**, bước 5.3 | Chưa có LED phát hồng ngoại, chưa ghi được mã NEC của remote thật bằng VS1838B/`irrecord` |
| `hardware/gpio-pinout.md`, sơ đồ đấu nối | **P5-03** | Chỉ viết được sau khi đấu dây thật |
| `src/decision/policy.py` — phân quyền `user_id → {devices, actions}` | **P5-02**, bước 5.4 | Mã việc riêng; nó sẽ đọc nhánh `decision:` trong `configs/actuator.yaml` mà P5-01 cố ý bỏ qua |
| N khung xác nhận, cooldown, timeout vắng mặt | **P5-02**, bước 5.5 | Ba tham số đã đặt sẵn trong config nhưng **P5-01 không đọc**. §4.5 chốt: khối chấp hành luỹ đẳng, việc dập lệnh lặp là của P5-02 |
| Đo độ trễ đầu-cuối, `results/bench_latency_*.csv` | Cổng C Phase 5, bước 5.6 | Cần phần cứng thật; mã việc này không ghi gì vào `results/` |
| Cảnh báo người lạ, Telegram, rate-limit | bước 5.7, 5.8 | Khối giám sát, không phải khối chấp hành |
| `mqtt_backend.py` | **mở rộng**, R12 | Chỉ làm sau khi Phase 6 đã đạt |
| Nối khối chấp hành vào `src/main.py` | Phase 6, bước 6.5 | `src/main.py` không có trong danh sách trắng |
| Đăng ký handler `SIGTERM`/`SIGINT` | Phase 6, bước 6.6 | Thuộc điểm vào của ứng dụng, không thuộc thư viện chấp hành |
| Thêm khoá `thong_so_thuc_te` hay ghi `.meta.json` | — | Mã việc này chỉ **tạo ra** `mo_ta_nguon()` để bên khác dùng |
| Cập nhật Chương 3 §Thiết kế khối chấp hành, vẽ hình, viết notebook | Cổng D | Sau khi mã đạt |

---

## 13. Ghi chú để `P5-03` không phải suy lại

Bốn ràng buộc dưới đây do mã việc này chốt, `P5-03` chỉ việc tuân theo — không cần thiết kế lại:

1. `gpio_backend.py` chỉ cài **một** phương thức `_tac_dong_phan_cung(ten, bat_len)` cộng hai hằng
   lớp `TEN_BACKEND = "gpio"`, `LA_GIA_LAP = False`, cộng (tuỳ chọn) `_mo_phan_cung` để
   `GPIO.setmode` và `_dong_phan_cung` để `GPIO.cleanup()`. Không được ghi đè `mo`, `dong`, `bat`,
   `tat`, `thuc_thi` — `__init_subclass__` sẽ từ chối.
2. `_tac_dong_phan_cung` **chỉ ghi mức điện**. Không kiểm hợp lệ, không ghi lịch sử, không đổi bộ
   nhớ trạng thái — lớp cơ sở làm hết rồi.
3. Lệnh lặp **không** được đi tới chân GPIO (§4.5) — lớp cơ sở đã chặn, `P5-03` không cần chặn lại,
   và cũng **không được** tự chặn thêm ở tầng dưới vì như thế sẽ vô hiệu hoá dòng 99, 101 §6.
4. `active_low` xử lý **bên trong** `_tac_dong_phan_cung`: `bat_len=True` nghĩa là "thiết bị BẬT",
   không phải "chân ở mức HIGH". Mọi tầng trên chỉ biết bật/tắt logic, không biết mức điện.

---

## 14. Báo cáo khi xong

Theo mẫu §12 của `docs/quy-tac-cai-dat.md`. Bắt buộc có:

- Mốc §9.0: commit đang đứng và hai con số nguyên văn.
- Mức tăng số ca ở §9.3, phát biểu bằng **phép trừ** so với mốc §9.0, cho **cả hai** môi trường.
- Bảng đột biến §10: 27 dòng, mỗi dòng ghi **ca nào thật sự đỏ** và có khớp cột "phải đỏ" không.
  Phép nào đỏ **khác** dự đoán thì nói rõ — đó là thông tin có giá trị nhất trong cả báo cáo.
- Đầu ra nguyên văn của §9.5.
