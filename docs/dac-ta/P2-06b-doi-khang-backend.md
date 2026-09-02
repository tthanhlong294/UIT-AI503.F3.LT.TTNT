# P2-06b — Ca đối kháng cho `backend`, dry-run khô, và phiên bản NCNN trong meta

> Mã việc: `P2-06b-doi-khang-backend` · Ba mục 🔵 của biên bản `P2-06`
> Nhánh: `feat/p2-06b-doi-khang-backend` · Đặc tả viết ngày 02/09/2026
> Tiền đề: `P2-06` đã gộp vào `dev` (`2ae8ec2`)

---

## 1. Mục tiêu

Ba việc nhỏ, cùng một lý do làm ngay: **cả ba đắt hơn nhiều nếu để sau khi đã đo trên Pi 5**, vì lúc
đó phải đo lại toàn bộ Cổng C.

| Mục | Vấn đề | Nguồn |
|---|---|---|
| A | Yêu cầu trung tâm §6.1 của `P2-06` **không có ca kiểm thử nào canh** | 🔵-1 |
| B | `--dry-run` khởi tạo mô hình thật, đắt đúng ở nơi nó có ích nhất | 🔵-2 |
| C | `.meta.json` không ghi phiên bản `ncnn`, dù 6/12 ô số đo do NCNN sinh ra | 🔵-3 |

Mục A là nghiêm trọng nhất và có bằng chứng máy: phép đột biến ĐB5 của lượt review thay
`detector.ten_backend` bằng phép đoán theo đuôi đường dẫn, **59/59 ca vẫn xanh**. Ràng buộc mà đặc
tả `P2-06` gọi là trung tâm hiện chỉ được canh bằng `grep` — dụng cụ không chạy tự động ở bất kỳ
vòng nào sau này. Đây là **khiếm khuyết của đặc tả `P2-06`**, không phải của người cài đặt.

Mục C tuy nhỏ nhất nhưng chặn lượt đo: bảng so sánh ở Chương 4 sẽ nói "NCNN nhanh hơn x %" mà không
chỗ nào ghi **bản NCNN nào đã chạy**, trong khi phía đối chứng `onnxruntime` thì ghi đủ. Bất đối
xứng nằm đúng trên trục biến thiên của phép so sánh.

---

## 2. Phạm vi file — danh sách trắng

| File | Trạng thái | Vai trò |
|---|---|---|
| `src/detector/factory.py` | sửa | Thêm `tra_ten_backend`; `tao_bo_phat_hien` gọi lại nó |
| `scripts/benchmark_detect.py` | sửa | Dry-run dùng `tra_ten_backend`; bỏ `_ten_backend_du_kien`; thêm `ncnn` vào `software` của meta |
| `tests/test_detector_factory.py` | sửa | Ca cho `tra_ten_backend` |
| `tests/test_benchmark_detect.py` | sửa | Ca đối kháng `backend`, ca meta, ca dry-run không nạp mô hình |

**Không sửa**: `src/detector/yolo_face.py`, `ncnn_backend.py`, `configs/**`, `requirements*.txt`,
`models/**`. Không thêm gói. **Không** `docker build`.

---

## 3. Dữ kiện — đã kiểm

| Dữ kiện | Giá trị |
|---|---|
| Quy tắc nhận dạng hiện có | `factory.py:44-53` — đuôi `.onnx` → ONNX; thư mục chứa `model.ncnn.param` → NCNN; còn lại `LoiCauHinh` |
| Hằng số đã có | `factory.py:18-19` — `_DUOI_ONNX = ".onnx"`, `_TEP_NHAN_DANG_NCNN = "model.ncnn.param"` |
| Thuộc tính của hai lớp | `.ten_backend` trả `"onnx"` / `"ncnn"` |
| Hàm cần bỏ | `benchmark_detect.py:244-272` — `_ten_backend_du_kien`, khởi tạo thật rồi hỏi `ten_backend` |
| Chi phí đo được của dry-run hiện tại | 0,265 s cho 4 mô hình trên `pc_x86` (biên bản `P2-06` 🔵-2) |
| Khối `software` của meta | `benchmark_detect.py:593-598` — có `python`, `onnxruntime`, `opencv-python`, `numpy`; **thiếu `ncnn`** |

---

## 4. Giao diện

### 4.1. `src/detector/factory.py`

```python
TEN_BACKEND_ONNX = "onnx"
TEN_BACKEND_NCNN = "ncnn"


def tra_ten_backend(duong_dan: Path | str) -> str:
    """Suy tên backend từ DẠNG đường dẫn, KHÔNG khởi tạo mô hình.

    Dùng đúng bộ quy tắc của `tao_bo_phat_hien`, để hai hàm không bao giờ bất đồng.

    Args:
        duong_dan: Đường dẫn tệp `.onnx` hoặc thư mục `*_ncnn_model`.

    Returns:
        `TEN_BACKEND_ONNX` hoặc `TEN_BACKEND_NCNN`.

    Raises:
        LoiCauHinh: đường dẫn không khớp dạng nào — cùng thông báo mà
            `tao_bo_phat_hien` vẫn ném, không viết lại chuỗi khác.
    """
```

`tao_bo_phat_hien` sửa lại để **gọi `tra_ten_backend`** rồi mới khởi tạo lớp tương ứng. Hai hàm chia
nhau đúng một bộ quy tắc; không được viết điều kiện nhận dạng hai lần.

Hai hằng số mới thay cho chuỗi viết cứng trong `factory.py`.

### 4.2. `scripts/benchmark_detect.py`

- **Xoá** `_ten_backend_du_kien` (`:244-272`). Nhánh dry-run gọi thẳng `tra_ten_backend(m)`.
- Chuỗi trợ giúp của `--dry-run` giữ nguyên nghĩa "không đo, không ghi tệp" — sau mã việc này nó
  đúng trở lại, vì dry-run không còn nạp mô hình.
- Khối `software` của meta thêm khoá `"ncnn"`, lấy phiên bản bằng đúng cơ chế đang dùng cho các gói
  khác. Gói vắng mặt → ghi giá trị báo vắng (ví dụ `"khong-xac-dinh"`), **không** ném ngoại lệ:
  một lượt đo dài không được hỏng chỉ vì thiếu một dòng metadata.

---

## 5. Ràng buộc chịu lực — đọc kỹ, đây là toàn bộ lý do mã việc tồn tại

### 5.1. `tra_ten_backend` KHÔNG được dùng trong đường ghi số đo

Sau khi có hàm này, cám dỗ tự nhiên là dùng nó trong `do_mot_cau_hinh` cho gọn. **Cấm.**

| Nơi dùng | Nguồn của `backend` |
|---|---|
| `do_mot_cau_hinh` — dòng số đo đi vào CSV | **`detector.ten_backend`** — đối tượng thật sự vừa chạy phép đo |
| Nhánh `--dry-run` — chưa có đối tượng nào | `tra_ten_backend(duong_dan)` |

Lý do: `tra_ten_backend` trả lời *"đường dẫn này trông như backend nào"*, còn cột `backend` của CSV
phải trả lời *"cái gì đã thật sự sinh ra con số bên cạnh"*. Hai câu hỏi trùng đáp án trong mọi
trường hợp bình thường, và **khác nhau đúng vào lúc có lỗi** — khi đó cột CSV phải nói sự thật về
phép đo, không nói phỏng đoán về tên tệp. Dry-run được phép dùng phỏng đoán vì nó không sinh số đo
nào.

### 5.2. Một bộ quy tắc, hai hàm

`tao_bo_phat_hien` và `tra_ten_backend` phải chia nhau đúng một bộ điều kiện nhận dạng. Nếu viết hai
lần, chúng sẽ trôi khỏi nhau, và khi trôi thì bảng dry-run hứa một đằng còn lượt đo cho một nẻo —
sai lệch chỉ lộ ra sau khi đã chạy xong một lượt dài.

---

## 6. Bảng tiêu chí nghiệm thu

### 6.1. `tests/test_detector_factory.py`

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Tệp `.onnx` → `"onnx"`, không nạp mô hình | `tra_ten_backend(tmp_path / "a.onnx") == "onnx"` với tệp rỗng — không cần mô hình thật |
| 02 | Thư mục có `model.ncnn.param` → `"ncnn"` | dựng thư mục giả với ba tệp rỗng |
| 03 | Đường dẫn lạ → `LoiCauHinh` | ba ca: `.pt`, không đuôi, thư mục rỗng |
| 04 | Thông báo lỗi **giống hệt** của `tao_bo_phat_hien` | bắt cả hai ngoại lệ trên cùng đầu vào, assert `str(e1) == str(e2)` |
| 05 | **Hai nguồn đồng thuận trên mô hình thật** | `@pytest.mark.slow`; với cả `models/yolov8n-face-320.onnx` và `models/yolov8n-face-320_ncnn_model`: `tra_ten_backend(p) == tao_bo_phat_hien(p, cfg).ten_backend` |

Dòng 05 là ca chốt của §5.2: nó buộc hằng số trong `factory.py` phải khớp với thuộc tính mà hai lớp
backend thật sự trả về. Đổi một bên mà quên bên kia thì ca này đỏ.

### 6.2. `tests/test_benchmark_detect.py`

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 06 | **Bản ghi lấy `backend` từ đối tượng, không từ tên đường dẫn** | monkeypatch factory trả detector giả có `ten_backend="ncnn"`; gọi `do_mot_cau_hinh(tmp_path / "gia.onnx", ...)`; assert `{r["backend"] for r in bg} == {"ncnn"}` |
| 07 | Meta có `software["ncnn"]` | `"ncnn" in meta["software"]` |
| 08 | Thiếu gói `ncnn` → meta vẫn ghi được, lượt đo không hỏng | monkeypatch hàm lấy phiên bản để ném; assert `main(...) == 0` và `meta["software"]["ncnn"]` là chuỗi |
| 09 | **`--dry-run` không khởi tạo mô hình nào** | đếm số lần `tao_bo_phat_hien` được gọi qua monkeypatch; assert `== 0` |
| 10 | `--dry-run` vẫn in đúng cột backend cho cả bốn mô hình | assert `stdout` chứa cả `onnx` lẫn `ncnn` |
| 11 | Mọi ca cũ vẫn xanh | không sửa ca cũ |

Dòng 06 là ca mà biên bản `P2-06` 🔵-1 chỉ ra là đang thiếu. Nó đúng bằng phép mà dòng 03 của `P2-06`
đã làm cho `imgsz` (đối tượng nói 999, tên tệp nói 320), chỉ chuyển sang trục `backend`.

Dòng 09 là thứ biến mục B từ lời hứa thành ràng buộc kiểm được.

---

## 7. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

```bash
python -m black --check --line-length 100 src/detector/factory.py scripts/benchmark_detect.py tests/test_detector_factory.py tests/test_benchmark_detect.py
```

```bash
python -m ruff check src/detector/factory.py scripts/benchmark_detect.py tests/test_detector_factory.py tests/test_benchmark_detect.py
```

```bash
python -m pytest tests/test_detector_factory.py tests/test_benchmark_detect.py -v -m "not slow"
```

```bash
python -m pytest -q -m "not slow"
```

```bash
docker run --rm -v "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"
```

```bash
git status --short --untracked-files=all
```

Phải cho thấy đúng bốn tệp của §2.

### Quét mẫu vi phạm

```bash
grep -n "tra_ten_backend" scripts/benchmark_detect.py
```

Chỉ được xuất hiện trong **nhánh dry-run**. Xuất hiện trong `do_mot_cau_hinh` là vi phạm §5.1.

```bash
grep -nE "\"onnx\"|'onnx'|\"ncnn\"|'ncnn'" src/detector/factory.py scripts/benchmark_detect.py
```

Trong `factory.py` chỉ được là **hai dòng định nghĩa hằng số** `TEN_BACKEND_*`. Trong
`benchmark_detect.py` phải rỗng (đường dẫn mặc định chứa `_ncnn_model` là tên thư mục, không phải
tên backend — nếu lệnh bắt được dòng đó thì giải trình).

### Kiểm đột biến bắt buộc

Ba phép. Sao lưu ra `$env:TEMP` → sửa → `pytest` → khôi phục → đối chiếu `sha256`.
Ghi tệp bằng `[System.IO.File]::WriteAllText` với `UTF8Encoding($false)` — **không**
`Set-Content -Encoding utf8`, nó ghi BOM và làm ca `ast.parse` đỏ giả.

| # | Phép đột biến | Ca **phải** đỏ |
|---|---|---|
| ĐB1 | Trong `do_mot_cau_hinh`, thay `detector.ten_backend` bằng `tra_ten_backend(duong_dan_mo_hinh)` | **dòng 06** |
| ĐB2 | Trong `factory.py`, cho `tra_ten_backend` luôn trả `TEN_BACKEND_ONNX` | dòng 02, 05, 10 |
| ĐB3 | Bỏ khoá `"ncnn"` khỏi khối `software` | dòng 07 |

ĐB1 là phép quan trọng nhất của cả mã việc: nó tái dựng đúng ĐB5 của lượt review `P2-06`, phép mà
trước đây **59/59 ca vẫn xanh**. Sau mã việc này nó phải đỏ. Nếu vẫn xanh thì dòng 06 chưa canh
đúng chỗ, và mục A coi như chưa làm.

---

## 8. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` 100, `ruff` sạch. Type hints, docstring tiếng Việt kiểu Google.
- Không thêm gói. `importlib.metadata` thuộc thư viện chuẩn.
- `factory.py` **không** được import `ncnn` hay `onnxruntime` ở mức module — nó vốn không import, giữ nguyên.
- Giữ nguyên mọi hành vi khác của `benchmark_detect.py`: cỡ mẫu, warm-up, lược đồ CSV, cách tính tổng hợp.

---

## 9. Ngoài phạm vi

- 🔵-4 CSV thiếu cột định danh mô hình — đổi lược đồ CSV, cần mã việc riêng có cân nhắc.
- 🔵-6 `PytestUnknownMarkWarning` — mã việc dọn dẹp marker.
- Ba mục 🔵 của `P2-05` (guard `load_param`, kiểm số kênh, `close()`) — `P2-05b` nếu người dùng đồng ý.
- Chạy ma trận và phân tích số liệu — bước 3 của trình tự, lượt của người dùng.

---

## 10. Báo cáo khi xong

Theo mẫu §12 của [`docs/quy-tac-cai-dat.md`](../quy-tac-cai-dat.md). Bắt buộc nêu:

1. Kết quả các lệnh §7, dán nguyên văn dòng tổng kết.
2. Kết quả hai lệnh `grep`.
3. Bảng ba phép đột biến — **đặc biệt ĐB1**: ca nào đỏ, và đối chiếu với ghi nhận "59/59 xanh" của
   lượt review `P2-06`.
4. Vướng mắc.

**Không commit.**

## 10b. Lượt của người dùng — sau khi §7 xanh

Sau khi mã việc này qua review và gộp vào `dev`, chạy **ba lượt** đo, cách nhau ít nhất 10 phút để
máy trở lại trạng thái nhiệt tương đương:

```bash
python scripts/benchmark_detect.py --device-name "PC phát triển" --ghi-chu "lượt 1/3"
```

Lý do ba lượt thay vì một: hai lượt đo ngày 02/09/2026 trên cùng máy, cùng seed, cùng mã cho kết
quả lệch tới **49 %** ở ô `ONNX 320 / 4 luồng`, và **đảo ngược thứ tự** giữa hai backend ở ô đó.
Với mức nhiễu như vậy, một lượt đo không xếp hạng được gì; ba lượt cho phép báo cáo trung bình kèm
độ phân tán giữa các lượt, đúng tinh thần R9.

Kiểm trước khi chạy: `git status --short` **không in gì** — số đo phải truy được về đúng một commit
(`git_dirty: false`), điều mà hai lượt trước chưa đạt.
