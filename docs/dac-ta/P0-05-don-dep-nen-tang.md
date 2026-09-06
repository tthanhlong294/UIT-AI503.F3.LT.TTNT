# P0-05 — Dọn dẹp nền tảng sau `P0-04`

| | |
|---|---|
| **Nguồn** | Bốn mục 🔵 của `docs/review/P0-04-tuong-thich-pi-os.review.md` và mục §14 đặc tả `P0-04` |
| **Phase / bước** | Phase 0, bước 0.2 và 0.4 (phần dọn dẹp còn lại) |
| **Nhánh** | `feat/p0-05-don-dep-nen-tang` |
| **Phụ thuộc** | `dev` **sau khi `P0-04` gộp** — cây mã = `bfc9026` + nhánh `feat/p0-04-tuong-thich-pi-os`. Hash commit gộp chưa tồn tại lúc viết đặc tả; người cài đặt rẽ nhánh từ đỉnh `dev` và ghi hash thật vào báo cáo tự kiểm |
| **Chặn** | Không chặn mã việc nào. Nên đóng trước khi Phase 0 được tổng kết lại ở Cổng D |
| **Ước lượng** | 6 tệp, ~120 dòng (trong đó ~5 dòng mã sản phẩm) |

---

## 1. Mục tiêu

Đóng bốn khoản nợ kỹ thuật mà lượt kiểm định `P0-04` ghi nhận nhưng cố ý không sửa trong vòng đó,
tất cả nằm chung một vùng tệp: `scripts/download_lfw.py`, ba tệp kiểm thử và `pyproject.toml`.

| Việc | Nguồn | Nội dung một dòng |
|---|---|---|
| 1 | 🔵-1 | Nhánh dự phòng của `giai_nen` làm sạch bit quyền như bộ lọc `data` |
| 2 | 🔵-2 phần mã | Thêm **ca 37** chốt tường minh hành vi nhánh A với thành viên tên tuyệt đối |
| 3 | 🔵-3 | Thông báo `skip` của hàm gác trọng số `.pt` đang chỉ sai đường |
| 4 | 🔵-4 | Thêm `--strict-config` vào `addopts` |
| 5 | §14 `P0-04` | Sửa chú thích lỗi thời ở `tests/test_export_detector_ncnn.py:7-10` |

**Không** có việc nào trong mã việc này đổi kết quả một ca kiểm thử đang có. Mọi thay đổi hoặc là
thêm ca mới, hoặc là đổi chuỗi thông báo, hoặc là siết chặt thêm một bậc theo chiều an toàn.

### 1.1. Hai quyết định thiết kế đã chốt (🔵-1 và 🔵-4 để mở cho `spec-writer` quyết)

| Mục | Hai phương án biên bản nêu | **Chốt** | Lý do |
|---|---|---|---|
| 🔵-1 | (a) chỉ ghi chú thích nêu ranh giới là chủ ý · (b) cài đặt phần làm sạch bit quyền | **(b), có giới hạn** — làm sạch **bit quyền**, **không** đụng `uid`/`gid`, và ghi chú thích cho phần không làm | xem §5.1 |
| 🔵-4 | có thêm `--strict-config` hay không | **Có làm** | xem §8.1 |

---

## 2. Phạm vi tệp — danh sách trắng

| # | Tệp | Thao tác |
|---|---|---|
| 1 | `scripts/download_lfw.py` | sửa — **chỉ** nhánh B của `giai_nen`, một hằng số mức module, và chú thích `:148-149` |
| 2 | `tests/test_download_lfw.py` | sửa — **chỉ cộng** ca 37, 49, 50, 51 và một hàm dựng tệp nén; không xoá, không đổi ca 01–36 |
| 3 | `tests/test_export_detector.py` | sửa — **chỉ** hàm gác `:42-45` và dòng gọi `:78`; **cộng** ca 55. Docstring đầu tệp giữ nguyên (§7 điều 5) |
| 4 | `tests/test_cau_hinh_pytest.py` | sửa — helper `_chay_pytest_con`, docstring đầu tệp; **cộng** ca 52, 53, 54 |
| 5 | `pyproject.toml` | sửa — **chỉ** khoá `addopts` |
| 6 | `tests/test_export_detector_ncnn.py` | sửa — **chỉ** docstring `:1-15`, không đụng một dòng mã nào |

**Tệp cấm chạm, kèm lý do:**

| Tệp | Vì sao không sửa |
|---|---|
| `requirements.txt` | Không có gói nào phải thêm hay bớt. Sửa tệp này, dù chỉ một dòng chú thích, buộc dựng lại `faceid:arm64` theo R43 (~18 phút) mà không đổi một gói nào |
| `deploy/Dockerfile.arm64` | như trên — sửa là buộc dựng lại image |
| `configs/**` | Mã việc này không sinh tham số cấu hình nào (§4) |
| `src/**` | Cả năm việc nằm ở `scripts/`, ở tệp kiểm thử và ở cấu hình `pytest` |
| `tests/test_yolo_face.py` | Cùng một lớp khuyết tật với Việc 3 nhưng **ba** biến thể lời khuyên — xem §15 |
| `docs/dac-ta/P0-04-*.md` | Phần sửa câu chữ của 🔵-2 **đã làm xong** ngày 06/09/2026, không thuộc mã việc này |

> Sửa tệp ngoài danh sách trắng = lỗi CHẶN-A khi review.

---

## 3. Dữ kiện — mốc, số ca và môi trường

### 3.1. Mốc kho

Theo quy ước mới ở 🔵-5 biên bản `P0-04`, mọi con số ca dưới đây ghi kèm mốc, môi trường và bộ lọc.

> **555 ca thu thập** trên **`dev` sau commit gộp `P0-04`** (cây mã = `bfc9026` + nhánh
> `feat/p0-04-tuong-thich-pi-os`), môi trường **`pc_x86`**, lệnh `pytest -q` **không lọc marker**.

Ba lượt chạy khác trên **cùng mốc đó**, đã đo ngày 06/09/2026:

| Môi trường | Python | Lệnh | Kết quả |
|---|---|---|---|
| `pc_x86` (Windows) | 3.12.5 | `pytest -q` | `555 passed` |
| `pc_x86` (Windows) | 3.12.5 | `pytest -q -m "not slow"` | `523 passed, 32 deselected` |
| `docker_arm64` (`faceid:arm64`) | 3.11.16 | `pytest -q -m "not slow"` | `522 passed, 1 skipped, 32 deselected` |
| `pi5` | 3.11.2 | `pytest -q -m "not slow"` | `518 passed, 5 skipped, 32 deselected` |

Ba con số tổng đều bằng **555**; khác nhau ở cách phân bổ `passed`/`skipped` vì các người gác
`skip` phụ thuộc nền tảng. Đây là mốc để đối chiếu, **không** phải con số phải đạt lại.

### 3.2. Một số hiệu = một hàm test

Cách đọc đã được biên bản `P0-04` §5.2 chốt và giữ nguyên ở đây: **một số hiệu ca = một hàm
test**; các dòng `37a`, `37b`… trong bảng §10 là **assert bên trong cùng một hàm**, không phải hàm
riêng. Mã việc này thêm **8 hàm test** mang tám số hiệu: 37, 49, 50, 51, 52, 53, 54, 55.

Số hiệu 38–48 đã dùng ở `P0-04` (39, 40, 41, 43, 44 ở `test_export_detector.py`; 45–48 ở
`test_cau_hinh_pytest.py`), nên ca mới của mã việc này nhảy lên 49 sau ca 37 — cố ý, để số hiệu
không bao giờ trùng giữa các tệp.

### 3.3. Số ca mong đợi sau mã việc

**555 + 8 = 563 ca thu thập** trên mốc §3.1 cộng nhánh này. Phân bổ dự đoán cho từng môi trường ở
§11, bảng [4]–[7].

⚠️ Nếu người cài đặt đo ra con số khác, **không được tự chỉnh cho khớp**: báo lại nguyên văn con
số đo được kèm mốc và lệnh đã chạy. Hai mã việc trước đều lệch ở đúng chỗ này.

---

## 4. Tham số → config

**Không có.** Mã việc này không đưa ra tham số vận hành nào. Hằng số kỹ thuật duy nhất sinh ra ở
đây đặt trong tệp dùng nó, có tên rõ ràng:

| Hằng số | Đặt ở | Giá trị | Vì sao không vào `configs/` |
|---|---|---|---|
| `_MASK_QUYEN_AN_TOAN` | `scripts/download_lfw.py` | `0o755` | Hằng an toàn của thư viện chuẩn (§5.2), không phải tham số điều chỉnh được. Đổi nó là đổi chính sách an ninh, phải qua review, không phải qua tệp YAML |

---

## 5. Việc 1 — nhánh dự phòng làm sạch bit quyền

### 5.1. Quyết định: cài đặt, nhưng chỉ phần bit quyền

Biên bản 🔵-1 để mở hai phương án. **Chốt phương án (b) có giới hạn**: cài đặt phần làm sạch **bit
quyền**, **không** đụng `uid`/`gid`, và ghi chú thích cho đúng phần không làm.

Ba lý do:

1. **Nhánh B là nhánh chạy trên thiết bị đích.** Host và container đều có `tarfile.data_filter` nên
   không bao giờ vào nhánh B trong điều kiện tự nhiên (bảng §5.4 biên bản). Chỗ duy nhất trong dự án
   ghi tệp ra đĩa từ dữ liệu tải về Internet lại chạy nhánh yếu hơn ở đúng máy thật — đó là hình
   dạng ngược với mong muốn.
2. **Chi phí đúng một dòng, và làm cho phát biểu "nhánh B chặt hơn nhánh A" trở thành đúng
   không điều kiện.** Hiện nhánh B chặt hơn ở liên kết, tệp thiết bị và tên tuyệt đối, nhưng **yếu
   hơn** ở bit quyền. Một quan hệ "chặt hơn trừ một chỗ" là thứ người đọc sau sẽ nhớ sai.
3. **`uid`/`gid` thì không đụng** vì chi phí/rủi ro đảo chiều: `TarFile.chown` chỉ chạy khi
   `os.geteuid() == 0`, còn việc gán `tv.uid`/`tv.gid` sang giá trị khác kéo theo API không có trên
   Windows (`os.getuid`) và chạm vào đường mã mà không ca nào của dự án chạy qua ở chế độ `root`.
   Đổi lấy một dòng chú thích trung thực thì tốt hơn.

### 5.2. Cài đặt

Thêm hằng số mức module, đặt cạnh ba hằng thông báo hiện có (`:92-99`):

```python
# Mặt nạ quyền của nhánh dự phòng — xoá setuid/setgid/sticky và bit ghi của nhóm/khác,
# đúng những gì bộ lọc "data" của thư viện chuẩn làm (tài liệu tarfile, mục Extraction filters).
_MASK_QUYEN_AN_TOAN = 0o755
```

Trong **nhánh B**, ở đúng vòng lặp đã có (`:151-154`), sau phép kiểm chứa-trong-đích, thêm **một
dòng** áp mặt nạ lên `tv.mode`.

Ràng buộc:

| # | Ràng buộc | Vì sao |
|---|---|---|
| 1 | Dòng mới nằm **trong nhánh B**, không nằm ở vòng quét chung `:135-137` | Nhánh A đã được bộ lọc `data` làm việc này; áp hai lần là thừa và làm ca 50 mất ý nghĩa đối chứng |
| 2 | Đặt **trước** `tf.extractall(dich)` | Sau khi giải nén thì đã muộn |
| 3 | **Không** thêm `import` nào | `scripts/download_lfw.py` chỉ dùng thư viện chuẩn (§5.7 `P0-04`), và phép `&` không cần gói nào |
| 4 | **Giữ nguyên** lời gọi `tf.extractall(dich)`, không thêm tham số `members=` | `getmembers()` trả về danh sách đã cache trong `tf.members`, nên các đối tượng `TarInfo` bị sửa ở vòng lặp **chính là** các đối tượng `extractall` sẽ dùng. Ca 49 là bằng chứng máy cho giả định này: giả định sai thì ca 49 đỏ ngay, không âm thầm |
| 5 | Chữ ký `giai_nen(archive: Path, dich: Path) -> Path` **không đổi**, ba hằng thông báo **không đổi** | Ca 01–36 phải xanh nguyên vẹn |

### 5.3. Chú thích phải sửa

Đoạn chú thích `:148-149` hiện mô tả nhánh B như bản thay thế của bộ lọc `data` mà không nêu chỗ
không tương đương. Viết lại để nêu đủ ba ý, mỗi ý một mệnh đề kiểm được bằng mắt trong 10 giây:

1. Nhánh B kiểm chứa-trong-đích **và** áp mặt nạ quyền `_MASK_QUYEN_AN_TOAN`.
2. Nhánh B **không** xử lý `uid`/`gid`; `extractall` áp chủ sở hữu ghi trong tệp nén khi tiến trình
   chạy bằng `root`. Đây là chủ ý, xem §5.1 đặc tả `P0-05`.
3. Do đó **không chạy `scripts/download_lfw.py` bằng `sudo`** — không cần, và là cách rẻ nhất để
   khác biệt còn lại ở ý 2 không bao giờ có tác dụng.

---

## 6. Việc 2 — ca 37 chốt hành vi nhánh A với tên tuyệt đối

Hiện **không ca nào** chốt hành vi của nhánh A khi tệp nén chứa thành viên mang tên tuyệt đối. Dữ
kiện đo ở §1.6 biên bản `P0-04`: bộ lọc `data` **không ném lỗi**, nó cắt ký tự `/` rồi giải nén vào
**trong** thư mục đích; còn nhánh B ném `LoiCauHinh` (ca 32). Khác biệt ấy đang nằm trong biên bản
chứ không nằm trong bộ kiểm thử — ai "dọn dẹp" nhánh B sau này sẽ không có ca nào cản, và nếu thư
viện chuẩn đổi cách xử lý ở một phiên bản sau thì cũng không gì báo.

Ca 37 dùng lại `_tao_tgz` có sẵn với thành viên `"/tmp/thoat.txt"` — **đúng chuỗi ca 32 dùng**, để
biến duy nhất đổi giữa hai ca là nhánh chạy. Người gác: `if not hasattr(tarfile, "data_filter"):
pytest.skip(...)`, cùng khuôn ca 34/35/36 — trên `pi5` ca này skip vì không có nhánh A để kiểm.

---

## 7. Việc 3 — hàm gác trọng số `.pt`

`tests/test_export_detector.py:42-45` khuyên *"chạy `scripts/export_detector.py` trước"*, nhưng
đường dẫn duy nhất nó gác là `_DUONG_DAN_WEIGHTS_THAT = models/yolov8n-face.pt` (`:33`, gọi ở
`:78`) — tệp `.pt` là **đầu vào** của script đó, không phải đầu ra. Người đọc thông báo mất một
vòng thử.

**Cách sửa: đổi tên hàm, không tách hàm.** Trong tệp này hàm chỉ có **một** lời gọi (`:78`) và lời
gọi đó gác đúng trọng số `.pt`, nên tách thành hai hàm sẽ để lại một hàm chết.

| # | Yêu cầu | Kiểm bằng |
|---|---|---|
| 1 | Hàm đổi tên thành `_bo_qua_neu_thieu_weights_pt`, giữ nguyên chữ ký `(duong_dan: Path) -> None` và hành vi `pytest.skip` | ca 55, §12 [G2] |
| 2 | Thông báo nêu **đường đi đúng**: chứa chuỗi `models/README.md` | ca 55a |
| 3 | Thông báo **không** còn nhắc `export_detector.py` | ca 55b, §12 [G1] |
| 4 | Lời gọi `:78` đổi theo tên mới; **không** thêm hay bớt lời gọi nào | §12 [G3] |
| 5 | Docstring đầu tệp (`:1-12`) hiện **không** nhắc tên hàm gác — giữ nguyên như vậy, không thêm tên hàm và không thêm chuỗi `models/README.md` vào đó | §12 [G2], [G3] đếm được đúng số dòng |

Không đổi điều kiện skip (`not duong_dan.exists()`), nên **không ca nào đổi trạng thái** giữa
`passed` và `skipped` vì việc này.

---

## 8. Việc 4 — `--strict-config`

### 8.1. Quyết định: có làm

**Chốt: thêm `--strict-config`.** Ba lý do, và một lý do phản đối đã cân:

| | |
|---|---|
| Được | Cùng **một lớp lỗi im lặng** với `--strict-markers`: một lần gõ nhầm `testpath` thay vì `testpaths` sẽ làm `pytest` quét cả kho thay vì `tests/`, chạy lâu hơn và có thể thu thập nhầm — mà không một dòng cảnh báo nào đủ nổi để ai đó dừng lại đọc |
| Chi phí hôm nay | **Bằng không.** `[tool.pytest.ini_options]` hiện có đúng bốn khoá `testpaths`, `pythonpath`, `markers`, `addopts` — cả bốn đều là khoá hợp lệ của `pytest 9.1.1` |
| Chi phí sau này | Chỉ phát sinh khi ai đó thêm khoá sai — đúng thứ cần bị chặn |
| Phản đối đã cân | Cờ này áp cho **mọi** lượt `pytest` đọc `pyproject.toml`, kể cả tiến trình con ở ca 47/48/53/54. Một khoá hỏng sẽ làm **cả lượt chạy** dừng với mã thoát `4`, không phải vài ca đỏ. Chấp nhận: đó chính là hành vi mong muốn, và ĐB5 (§13) dựng lại đúng tình huống ấy để nó không bao giờ là bất ngờ |

### 8.2. Cài đặt

`pyproject.toml`, **chỉ** khoá `addopts`: thêm `"--strict-config"` bên cạnh `"--strict-markers"`.
Không đụng `testpaths`, `pythonpath`, `markers`. Không thêm khoá mới nào — `filterwarnings` và
`-W error` vẫn bị cấm (§5.8 `P0-04`).

### 8.3. Ba ca canh, và vì sao cần cả ba

| Ca | Canh điều gì | Nếu thiếu ca này thì… |
|---|---|---|
| 52 | `addopts` của **kho** thật sự có cờ | Ca 53/54 dùng cấu hình tạm nên vẫn xanh dù kho không bật cờ — không ai biết |
| 53 | Cờ **thật sự cắn**: khoá sai làm `pytest` con thoát khác `0` và nêu đích danh tên khoá | Ca 52 chỉ chứng minh chuỗi có mặt trong tệp TOML, không chứng minh `pytest` xử lý nó |
| 54 | **Cặp đối chứng** của 53: cùng cách dựng cấu hình tạm, khoá viết đúng → thoát `0` | Một cấu hình tạm hỏng vì lý do vô can (sai cú pháp TOML, thiếu mục) cũng làm ca 53 xanh |

Ca 53/54 dựng tệp cấu hình tạm **tự chứa** trong `tmp_path`, đặt tên đúng `pyproject.toml` (pytest
đọc mục `[tool.pytest.ini_options]` theo tên tệp), nội dung tối giản: một mục `markers`, một mục
`addopts` chứa `--strict-config`, và một khoá `testpath` (sai) hoặc `testpaths` (đúng). Bộ ca kiểm
thử con là tệp `.py` tối giản như ca 47/48 đã làm.

Helper `_chay_pytest_con` hiện chốt cứng `-c pyproject.toml` với `cwd=_GOC_KHO`. Mở rộng bằng một
tham số **tuỳ chọn** `cau_hinh: Path | None = None`; mặc định giữ nguyên hành vi cũ, nên ca 47/48
**không đổi một ký tự nào**. Giữ nguyên `cwd=_GOC_KHO`, `-p no:cacheprovider`, và cách truyền
đường dẫn tệp test trên dòng lệnh.

Hai chi tiết phải chốt để ca 53/54 không xanh vì lý do vô can:

| # | Chốt | Vì sao |
|---|---|---|
| 1 | Tệp cấu hình tạm đặt tên đúng `pyproject.toml` trong `tmp_path`, mục `[tool.pytest.ini_options]` | `pytest` chỉ đọc mục này ở tệp mang tên đó |
| 2 | Tệp test con được truyền **tường minh** trên dòng lệnh; giá trị của `testpath`/`testpaths` trong cấu hình tạm không ảnh hưởng việc thu thập | Biến duy nhất đổi giữa ca 53 và 54 là **tên khoá**, không phải tập ca được thu thập |

---

## 9. Việc 5 — chú thích `ncnn` lỗi thời

`tests/test_export_detector_ncnn.py:7-10` viết rằng `ncnn`/`ultralytics`/`torch` "không có trong
`requirements.txt`/container ARM64". Câu này **sai với `ncnn`** kể từ khi gói được ghim ở
`requirements.txt:9`.

Viết lại docstring cho đúng bốn dữ kiện, mỗi dữ kiện kiểm được bằng một lệnh `grep`:

| # | Dữ kiện phải nêu | Nguồn kiểm |
|---|---|---|
| 1 | `ncnn` **có** trong `requirements.txt` (dòng 9) — là phụ thuộc **chạy**, cần trên cả Pi lẫn máy dev | `grep -n ncnn requirements.txt` |
| 2 | `ultralytics` chỉ có trong `requirements-dev.txt`; `torch` không được ghim ở tệp nào, nó đến theo `ultralytics` | `grep -n "ultralytics\|torch" requirements*.txt` |
| 3 | Ràng buộc **cấm import ba gói ở mức module vẫn giữ nguyên** — vì `ultralytics`/`torch` không có trên thiết bị đích, và vì ca kiểm thử không được giả định môi trường đã cài đúng bản `ncnn` đã ghim | đọc mã: không dòng `import` nào của ba gói ở mức module |
| 4 | `pytest.importorskip` cho cả ba gói giữ nguyên | `grep -n importorskip tests/test_export_detector_ncnn.py` |

⚠️ **Chỉ sửa docstring.** Không đụng một dòng mã nào trong tệp; số ca của tệp này **không đổi**.

---

## 10. Ca kiểm thử mới — mỗi dòng một điều kiện

Ký hiệu: `giai_nen` nhập từ `scripts.download_lfw`, `LoiCauHinh` từ `src.common.exceptions` — đã có
sẵn ở đầu `tests/test_download_lfw.py`.

### 10.1. `tests/test_download_lfw.py` — ca 37, 49, 50, 51

| Ca | Tiền đề | Điều kiện kiểm | Assert tối thiểu |
|---|---|---|---|
| 37a | Có `tarfile.data_filter` (không thì `pytest.skip`). `_tao_tgz(tmp_path/"a.tgz", {"/tmp/thoat.txt": b"x"})`, `dich = tmp_path/"dest"`, gọi `giai_nen` **không** bọc `pytest.raises` | Nhánh A không ném lỗi và giải nén vào trong đích | `assert (dich / "tmp" / "thoat.txt").exists()` |
| 37b | như 37a, cùng một lượt gọi | Không tệp nào rơi ra ngoài `dich` | `assert not [p for p in tmp_path.rglob("thoat.txt") if not p.is_relative_to(dich)]` |
| 49 | POSIX (Windows → `pytest.skip`). `monkeypatch.delattr(tarfile, "data_filter", raising=False)`. Tệp nén dựng bằng `_tao_tgz_voi_quyen(..., ten="lfw/a.jpg", mode=0o4755)` | Nhánh B xoá bit `setuid` | `assert (dich / "lfw" / "a.jpg").stat().st_mode & 0o7000 == 0` |
| 50 | POSIX. Có `tarfile.data_filter` (không thì `pytest.skip`). **Cùng tệp nén** như ca 49, **không** `delattr` | Nhánh A cũng cho bit cao sạch — cặp đối chứng chứng minh hai nhánh nay **đồng ý** về quyền | `assert (dich / "lfw" / "a.jpg").stat().st_mode & 0o7000 == 0` |
| 51 | POSIX. `delattr` như ca 49. Tệp nén dựng với `mode=0o644` | Mặt nạ **không** phá quyền đọc của tệp thường — cặp đối chứng theo chiều ngược của ca 49 | `assert (dich / "lfw" / "a.jpg").stat().st_mode & 0o400 != 0` |

Hàm dựng tệp nén mới, đặt cạnh `_tao_tgz_voi_lien_ket` (`:600`):

```python
def _tao_tgz_voi_quyen(duong_dan: Path, ten: str, noi_dung: bytes, mode: int) -> Path:
    """Dựng tệp .tgz chứa đúng một tệp thường mang giá trị `mode` chỉ định."""
```

Ràng buộc của ba ca quyền:

| # | Ràng buộc | Vì sao |
|---|---|---|
| 1 | Người gác POSIX viết theo `sys.platform`, thông báo `skip` nêu rõ "bit quyền chỉ có ý nghĩa trên POSIX" | Trên Windows `os.chmod` chỉ hiểu bit chỉ-đọc; ca sẽ xanh vì lý do vô can |
| 2 | Dùng bit **`setuid`** (`0o4755`), **không** dùng `setgid` | Hạt nhân có thể tự bỏ `setgid` khi người chạy không thuộc nhóm của tệp — ca sẽ xanh mà không chứng minh được gì |
| 3 | Ghi vào `tmp_path`, không ghi vào thư mục gắn từ host | `tmp_path` nằm trong hệ tệp của chính container/máy chạy, giữ được bit quyền |
| 4 | Ca 50 dùng **cùng một hàm dựng** và **cùng tham số** như ca 49 | Biến duy nhất đổi giữa hai ca là nhánh chạy |

### 10.2. `tests/test_cau_hinh_pytest.py` — ca 52, 53, 54

| Ca | Tiền đề | Điều kiện kiểm | Assert tối thiểu |
|---|---|---|---|
| 52 | `_doc_cau_hinh_pytest()` | `addopts` của kho có `--strict-config` | `assert "--strict-config" in cfg["addopts"]` |
| 53a | `tmp_path/"pyproject.toml"` tự chứa, `addopts` có `--strict-config`, có khoá sai `testpath`; một tệp test tối giản; chạy `_chay_pytest_con(tep_test, cau_hinh=cfg_sai)` | Khoá sai làm tiến trình con thoát khác `0` | `assert kq.returncode != 0` |
| 53b | như 53a, cùng lượt chạy | Thông báo nêu **đích danh** khoá sai, không phải lỗi chung chung | `assert "testpath" in kq.stdout + kq.stderr` |
| 54 | **Cùng cách dựng** như 53 nhưng khoá viết đúng `testpaths` | Cấu hình tạm hợp lệ vẫn thoát `0` | `assert kq.returncode == 0` |
| 47, 48 | không đổi | Gọi `_chay_pytest_con` **không** truyền `cau_hinh` | (ca cũ, phải vẫn xanh) |

### 10.3. `tests/test_export_detector.py` — ca 55

| Ca | Tiền đề | Điều kiện kiểm | Assert tối thiểu |
|---|---|---|---|
| 55a | `with pytest.raises(pytest.skip.Exception) as e: _bo_qua_neu_thieu_weights_pt(tmp_path / "khong_co.pt")` | Thông báo chỉ đúng đường lấy trọng số | `assert "models/README.md" in str(e.value)` |
| 55b | như 55a, cùng lượt gọi | Thông báo **không** còn chỉ sai đường | `assert "export_detector.py" not in str(e.value)` |

> `pytest.skip.Exception` là lớp `Skipped`, kế thừa `BaseException`; `pytest.raises` bắt được vì
> lớp được truyền tường minh. Ca này **không** mang dấu `slow` và **không** cần tệp trọng số thật —
> nó gọi hàm gác với một đường dẫn chắc chắn không tồn tại trong `tmp_path`.

### 10.4. Không ca nào đổi trạng thái

Ca 01–48 giữ nguyên số lượng và giữ nguyên phân bổ `passed`/`skipped`/`deselected` ở cả ba môi
trường. Nếu một ca cũ đổi trạng thái, đó là dấu hiệu đã đụng nhầm chỗ — dừng lại, báo cáo.

---

## 11. Lệnh tự kiểm — `coder` chạy trong phiên của mình

Mỗi khối đúng một lệnh. Chạy lại toàn bộ sau **mỗi** lần sửa. Không lệnh nào commit, dựng image
hay `pip install`.

```bash
black --check --line-length 100 src tests scripts
```
[1] Mong đợi: `All done!`, không tệp nào phải định dạng lại.

```bash
ruff check src tests scripts
```
[2] Mong đợi: `All checks passed!`

```bash
python -VV
```
[3] Ghi lại nguyên văn — mọi con số ca dưới đây chỉ đọc được cùng với dòng này.

```bash
pytest -q
```
[4] `pc_x86`, không lọc marker. Mong đợi: **563 ca thu thập** = `560 passed, 3 skipped`.
Ba ca skip là 49, 50, 51 (người gác POSIX). Mốc cũ: `555 passed`.

```bash
pytest -q -m "not slow"
```
[5] `pc_x86`, lọc marker. Mong đợi: `528 passed, 3 skipped, 32 deselected` — tổng **563**.
Mốc cũ: `523 passed, 32 deselected`.

```bash
pytest tests/test_download_lfw.py tests/test_export_detector.py tests/test_cau_hinh_pytest.py -q
```
[6] Ba tệp bị đụng, chạy riêng. Mong đợi tổng **99** ca thu thập = `44 + 48 + 7`, trong đó
`96 passed, 3 skipped` trên `pc_x86`. Mốc cũ: `91` = `40 + 47 + 4`.

```bash
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q -m "not slow"
```
[7] `docker_arm64`, Python 3.11.16. Mong đợi: `530 passed, 1 skipped, 32 deselected` — tổng
**563**. Ba ca quyền **chạy** ở đây (Linux), ca 37 và 50 cũng chạy (có `data_filter`). Ca skip duy
nhất vẫn là ca 43 như mốc cũ.
⚠️ **Không dựng lại image.** Mã việc không đụng `requirements.txt` lẫn `deploy/Dockerfile.arm64`
(§2), nên theo R43 image hiện có là đúng image. Nếu người cài đặt thấy một lý do bắt buộc phải sửa
hai tệp đó → **dừng lại, báo cáo**, không tự quyết.

```bash
git status --short --untracked-files=all
```
[8] Mong đợi: đúng **6** dòng, đúng sáu tệp của §2. Không dòng thứ bảy.

```bash
git diff --numstat dev...HEAD
```
[9] Mong đợi: sáu tệp; cột "bớt" của `tests/test_download_lfw.py` phải bằng **0** (chỉ cộng ca
mới), cột "bớt" của `tests/test_export_detector_ncnn.py` chỉ gồm dòng docstring cũ.

---

## 12. Quét mẫu bằng `grep` — `coder` chạy, dán nguyên văn kết quả

```bash
grep -n "export_detector.py trước" tests/test_export_detector.py
```
[G1] Mong đợi: **không dòng nào**.

```bash
grep -n "models/README.md" tests/test_export_detector.py
```
[G2] Mong đợi: đúng **một** dòng, nằm trong thân `_bo_qua_neu_thieu_weights_pt`.

```bash
grep -n "_bo_qua_neu_thieu" tests/test_export_detector.py
```
[G3] Mong đợi: đúng **hai** dòng — định nghĩa và một lời gọi ở `:78`; cả hai mang tên mới
`_bo_qua_neu_thieu_weights_pt`, không còn tên cũ đứng một mình.

```bash
grep -n "0o755\|_MASK_QUYEN_AN_TOAN\|mode &=" scripts/download_lfw.py
```
[G4] Mong đợi: đúng **hai** dòng — khai báo hằng ở mức module, và một lời áp mặt nạ nằm **trong
nhánh B** (số dòng lớn hơn dòng `else:` của `giai_nen`).

```bash
grep -n "^import\|^from" scripts/download_lfw.py
```
[G5] Mong đợi: danh sách `import` **không đổi** một dòng nào so với mốc §3.1 — chỉ thư viện chuẩn
và `src.common.exceptions`.

```bash
grep -n "strict-markers\|strict-config" pyproject.toml
```
[G6] Mong đợi: đúng **một** dòng `addopts` chứa cả hai cờ.

```bash
grep -n "requirements.txt\|ncnn\|ultralytics\|torch" tests/test_export_detector_ncnn.py
```
[G7] Mong đợi: mọi dòng khớp đều nằm trong docstring `:1-20` hoặc trong lời gọi
`pytest.importorskip`; **không** dòng nào nói `ncnn` vắng mặt ở `requirements.txt`.

```bash
grep -rn "sudo" scripts/download_lfw.py
```
[G8] Mong đợi: đúng **một** dòng — câu chú thích ý 3 của §5.3.

---

## 13. Phép đột biến — bốn bước bắt buộc cho mỗi phép

Bốn bước, không được bỏ bước nào:

1. **Sao lưu ra ngoài kho** (không để bản sao trong cây làm việc):
   `cp <tệp> "$TMPDIR/<tệp>.bak"` — Windows: `Copy-Item <tệp> $env:TEMP\<tệp>.bak`
2. **Sửa** đúng một chỗ theo bảng dưới.
3. **Chạy** lệnh ghi ở cột "Chạy ở đâu", dán nguyên văn danh sách ca đỏ.
4. **Khôi phục** từ bản sao lưu, rồi **đối chiếu `sha256`** của tệp trước và sau; dán cả hai giá
   trị. Lệch một ký tự = còn sót mã đột biến, phải xử lý trước khi báo cáo.

| # | Phép sửa | Ca **phải đỏ** | Ca **phải vẫn xanh** | Chạy ở đâu |
|---|---|---|---|---|
| ĐB1 | Xoá dòng áp mặt nạ quyền ở nhánh B | **49** | 50, 51 — chúng không canh dòng này | `docker_arm64` (ca 49 skip trên Windows) |
| ĐB2 | Đổi mặt nạ thành `0o000` (siết quá tay) | **51** | 49 — bit cao vẫn sạch | `docker_arm64` |
| ĐB3 | Ép `giai_nen` luôn đi nhánh B (thay `hasattr(...)` bằng `False`) | **37** | 50 — nhánh B cũng cho bit sạch | `pc_x86` |
| ĐB4 | Xoá `--strict-config` khỏi `addopts` | **52** | 53, 54 — chúng dùng cấu hình tạm, không dùng của kho | `pc_x86` |
| ĐB5 | Đổi `testpaths` thành `testpath` trong `pyproject.toml` | **cả lượt chạy dừng**: `pytest` thoát mã `4`, in `Unknown config option: testpath`, không thu thập ca nào | — | `pc_x86` |
| ĐB6 | Đổi thông báo của `_bo_qua_neu_thieu_weights_pt` về câu cũ | **55** | mọi ca còn lại | `pc_x86` |
| ĐB7 | Trong nhánh B, áp mặt nạ **sau** `tf.extractall(dich)` | **49** | 50, 51 | `docker_arm64` |

ĐB5 là phép quan trọng nhất của Việc 4: nó cho thấy hình dạng thật của lỗi mà `--strict-config`
chặn — **cả lượt chạy dừng ngay**, chứ không phải vài ca đỏ. Dán nguyên văn dòng lỗi và mã thoát.

ĐB7 là phép quan trọng nhất của Việc 1: nó dựng lại đúng cách cài đặt sai **tự nhất quán** — mã
trông hợp lý, mặt nạ có mặt, tên hằng đúng, nhưng áp sai thời điểm nên không có tác dụng gì.

---

## 14. Ràng buộc kỹ thuật

- Mã chạy được trên **Python 3.11.2** trở lên. Không dùng cú pháp hay API chỉ có từ 3.12.
- `scripts/download_lfw.py` **chỉ** thư viện chuẩn — không thêm `import` nào (§5.2 ràng buộc 3).
- `black` line-length 100, `ruff` sạch.
- Không `except Exception` trần; ngoại lệ dùng lớp trong `src/common/exceptions.py`.
- Ca test chỉ ghi vào `tmp_path`; không ghi vào `data/`, `models/`, `results/`, `report/`.
- **Không ca test nào chạm mạng.** Ca 37/49/50/51 dựng tệp nén tại chỗ bằng `tarfile`.
- Không `git commit`, không dựng image, không `pip install` (R42, R43).

**Container `faceid:arm64` KHÔNG có những thứ sau** — mọi ca mới phải chạy được khi thiếu chúng:

| Thứ thiếu | Vì sao |
|---|---|
| `git` (nhị phân) và thư mục `.git/` | Dockerfile không cài `git`; `.dockerignore` loại `.git/` |
| `docs/`, `models/`, `data/`, `results/`, `report/` | `.dockerignore` |
| `ultralytics`, `torch`, `onnx` | không có trong `requirements.txt` |

Không ca nào của mã việc này được gọi `subprocess` tới `git`, đọc `models/` hay `data/`. Ca
53/54 gọi `subprocess` tới **chính `sys.executable` -m pytest**, không tới nhị phân ngoài.

### 14b. Lượt của người dùng — sau khi §11, §12, §13 xanh

Chạy trên **Raspberry Pi 5** (Python 3.11.2 — môi trường duy nhất chạy nhánh B tự nhiên):

```bash
python3 -m pytest -q -m "not slow"
```
Mong đợi: `524 passed, 7 skipped, 32 deselected` — tổng **563**. Bảy ca skip = năm ca của mốc cũ
cộng ca 37 và ca 50 (Pi không có `data_filter`, không có nhánh A để kiểm).

```bash
python3 -m pytest tests/test_download_lfw.py -q
```
Mong đợi: **44** ca thu thập, `39 passed, 5 skipped` — ca skip là 34, 35, 36, 37, 50.
⭐ Ca **49** và **51** phải **passed** ở đây: đây là lượt duy nhất chứng minh mặt nạ quyền chạy trên
nhánh B **trong điều kiện tự nhiên**, không phải nhờ `monkeypatch`.

```bash
python3 -m pytest -q -m "not slow" 2>&1 | grep -i "PytestUnknownMark\|Unknown config option"
```
Mong đợi: **không dòng nào**.

---

## 15. Ngoài phạm vi — KHÔNG làm ở mã việc này

- **`tests/test_yolo_face.py:49-51`** — cùng một lớp khuyết tật với Việc 3, nhưng hàm gác ở đó phục
  vụ **ba** loại đường dẫn với ba lời khuyên khác nhau: mô hình `.onnx` do `export_detector.py`
  sinh (lời khuyên hiện tại **đúng**), ảnh LFW (phải khuyên `download_lfw.py`), và trọng số `.pt`
  ở `:464` (phải khuyên `models/README.md`). Sửa đúng cần ba hàm gác trong một tệp 40+ ca — đủ lớn
  để là mã việc riêng, và trộn vào đây sẽ làm bảng §10 khó review. **Ghi lại để không quên.**
- Xử lý `uid`/`gid` ở nhánh B — đã cân và loại ở §5.1 lý do 3.
- Nới `giai_nen` để chấp nhận liên kết mềm trỏ vào bên trong thư mục đích — chặt hơn là chủ ý
  (§5.4 `P0-04`).
- Thêm `filterwarnings` hay `-W error` vào `pyproject.toml` — cấm ở §5.8 `P0-04`, vẫn cấm.
- Tạo `requirements-pi.txt` — đã cân và loại ở §7.1 `P0-04`.
- Sửa câu chữ đặc tả `P0-04` (phần 🔵-2 không thuộc mã) — **đã làm xong** ngày 06/09/2026.
- Cập nhật `CLAUDE.md` §8, `docs/dieu-chinh-pham-vi.md`, hay Chương 4 §4.1 — việc của phiên chính
  và của `paper-writer` ở Cổng D.
- Đo hiệu năng trên Pi 5 — thuộc Cổng C của Phase 2.

---

## 16. Quy tắc áp dụng

`docs/quy-tac-cai-dat.md` — mã liên quan và lý do một dòng:

- **R15/R16** — hằng `_MASK_QUYEN_AN_TOAN` là hằng an toàn có tên, không phải số magic và không
  phải tham số vận hành (§4).
- **R18** — không đụng tệp phụ thuộc nào, mọi ghim `==` giữ nguyên.
- **R19** — `black` 100 ký tự, `ruff` sạch.
- **R20** — hàm mới và hàm đổi tên vẫn phải có type hints và docstring tiếng Việt kiểu Google.
- **R23** — không thêm `print()` vào `scripts/download_lfw.py`.
- **R33** — đọc `:126-159` của `giai_nen` trước khi sửa; một dòng thêm sai chỗ (ĐB7) là vô hiệu.
- **R38/R40** — `coder` viết mã, không commit; phải có biên bản review ĐẠT mới gộp `dev`.
- **R42** — `coder` chỉ chạy §11, §12, §13; §14b là lượt của người dùng.
- **R43** — một image duy nhất `faceid:arm64`, và mã việc này cố ý không tạo lý do dựng lại nó.
