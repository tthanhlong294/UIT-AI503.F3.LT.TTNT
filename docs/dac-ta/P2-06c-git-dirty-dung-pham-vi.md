# P2-06c — `git_dirty` phải hỏi đúng câu hỏi

> Mã việc: `P2-06c-git-dirty-dung-pham-vi` · Sửa một khiếm khuyết chặn Cổng C
> Nhánh: `feat/p2-06c-git-dirty` · Đặc tả viết ngày 03/09/2026
> Phát hiện từ: `notebooks/02_phan_tich_hieu_nang_detect.ipynb` mục 1, lượt chạy 03/09/2026

---

## 1. Vấn đề

`_kiem_tra_git_dirty` (`scripts/benchmark_detect.py:347-360`) chạy `git status --porcelain` trên
**toàn bộ thư mục dự án**. Lệnh này liệt kê cả tệp chưa được git theo dõi, nên **chính tệp kết quả
mà lượt đo vừa sinh ra cũng bị tính là "có thay đổi chưa lưu"**.

Ba lượt đo ngày 03/09/2026 cho thấy hậu quả:

| Lượt | Giờ | `git_commit` | `git_dirty` | Thư mục lúc đó |
|---|---|---|---|---|
| 1 | 20:22 | `743640b` | `false` | sạch |
| 2 | 20:40 | `743640b` | **`true`** | có 2 tệp kết quả của lượt 1 |
| 3 | 20:44 | `743640b` | **`true`** | có 4 tệp kết quả của lượt 1 và 2 |

**Mã nguồn không đổi một dòng nào** — cả ba cùng một commit, không có commit nào xen giữa. Cờ bật
lên chỉ vì phép đo trước để lại kết quả trong thư mục.

## 2. Vì sao phải sửa trước Cổng C

Checklist §9 của `experiment-protocol.instructions.md` đặt `git_dirty = false` làm điều kiện đưa số
liệu vào báo cáo. Kết hợp với yêu cầu đo **nhiều lượt** — thứ mà chính ba lượt này chứng minh là cần
thiết, vì một lượt đơn lẻ dao động tới 168 % — ta được một mâu thuẫn:

> Đo một lượt thì không đủ căn cứ kết luận. Đo nhiều lượt thì mọi lượt từ thứ hai trở đi đều bị đánh
> dấu là không đủ điều kiện.

Trên Raspberry Pi 5 ở Cổng C, đây là số liệu kết luận sáu chỉ tiêu cam kết. Không thể để một cờ sai
làm người đọc nghi ngờ toàn bộ, hoặc tệ hơn, buộc phải commit tệp kết quả xen giữa các lượt đo chỉ
để lách điều kiện.

Câu hỏi mà trường này cần trả lời là **"mã sinh ra số đo có nguyên vẹn không"**, không phải
**"thư mục có tệp mới nào không"**.

---

## 3. Phạm vi file — danh sách trắng

| File | Trạng thái | Vai trò |
|---|---|---|
| `scripts/benchmark_detect.py` | sửa | `_kiem_tra_git_dirty` đổi phạm vi; thêm trường meta phụ |
| `tests/test_benchmark_detect.py` | sửa | Ca cho phạm vi mới |

**Không sửa**: `src/**`, `configs/**`, `scripts/export_detector*.py`, `notebooks/**`,
`.claude/**`. Không thêm gói. Không `docker build`.

> `scripts/export_detector_ncnn.py` cũng ghi metadata nhưng **không** có trường `git_dirty`, nên
> không nằm trong mã việc này.

---

## 4. Giao diện

```python
# Đường dẫn ảnh hưởng tới kết quả đo — thay đổi ở đây làm số đo khác đi.
# `results/` KHÔNG nằm trong danh sách: tệp kết quả là sản phẩm của phép đo,
# không phải đầu vào của nó (P2-06c §2).
_DUONG_DAN_ANH_HUONG_PHEP_DO = (
    "src",
    "scripts",
    "configs",
    "requirements.txt",
    "requirements-dev.txt",
)


def _kiem_tra_git_dirty() -> bool:
    """Kiểm mã nguồn sinh ra số đo có thay đổi nào chưa commit hay không.

    Chỉ xét các đường dẫn ở `_DUONG_DAN_ANH_HUONG_PHEP_DO`. Tệp mới trong `results/`,
    `notebooks/` hay `docs/` không làm cờ này bật, vì chúng không đổi kết quả của
    phép đo đang chạy.

    Returns:
        True nếu có thay đổi chưa commit trong phạm vi trên, hoặc nếu không chạy
        được git (giả định xấu nhất, giữ nguyên hành vi cũ).
    """


def _kiem_tra_git_dirty_toan_cay() -> bool:
    """Kiểm toàn bộ thư mục dự án, kể cả tệp chưa được theo dõi.

    Giá trị này ghi vào meta dưới khoá `git_dirty_toan_cay` để không mất thông tin:
    người đọc sau này vẫn biết lúc đo thư mục có gì khác thường hay không, nhưng
    điều kiện của checklist §9 thì căn theo `git_dirty` ở trên.
    """
```

Meta thêm khoá **`git_dirty_toan_cay`** bên cạnh `git_dirty` đã có. Cả hai vào
`_KHOA_META_BAT_BUOC`.

---

## 5. Thiết kế bắt buộc

### 5.1. Vì sao giới hạn theo đường dẫn, không phải bỏ tệp chưa theo dõi

Một cách sửa ngắn hơn là thêm `--untracked-files=no`. **Không dùng cách đó.**

Nó bỏ sót một tình huống thật: người cài đặt tạo tệp `src/detector/backend_moi.py` chưa `git add`,
rồi chạy đo. Mã đó **có** ảnh hưởng kết quả nhưng không nằm trong lịch sử — đúng thứ `git_dirty`
sinh ra để bắt. Giới hạn theo đường dẫn vẫn bắt được, vì tệp mới đó nằm trong `src/`.

Nói cách khác: vấn đề không nằm ở chỗ tệp *đã theo dõi hay chưa*, mà ở chỗ nó *có ảnh hưởng phép đo
hay không*.

### 5.2. Không chạy được git thì giả định xấu nhất

Giữ nguyên hành vi hiện có: `subprocess` lỗi → trả `True`. Một cờ báo động nhầm còn hơn một cờ im
lặng cho qua số liệu không truy vết được.

### 5.3. Hai lệnh git, không phải một

`_kiem_tra_git_dirty` và `_kiem_tra_git_dirty_toan_cay` chạy hai lệnh riêng. Không tối ưu bằng cách
chạy một lệnh rồi tự lọc chuỗi đầu ra: phân tích đầu ra `--porcelain` bằng tay là chỗ dễ sai lặng lẽ
(tên tệp có dấu cách, tệp đổi tên, ký tự Unicode bị git thoát), và cái giá phải trả chỉ là vài chục
mili-giây mỗi lượt đo dài hai phút.

---

## 6. Bảng tiêu chí nghiệm thu

Ca mới đặt tên `test_dong<nn>` nối tiếp số hiện có.

| # | Yêu cầu | Assert tối thiểu |
|---|---|---|
| 01 | Chỉ có tệp mới trong `results/` → `git_dirty` là `False` | monkeypatch `subprocess.run` trả đầu ra rỗng cho lệnh giới hạn phạm vi; assert `is False` |
| 02 | Lệnh git được gọi **có kèm phạm vi** đường dẫn | bắt tham số `subprocess.run` nhận được; assert chứa `"src"`, `"scripts"`, `"configs"` và dấu `--` |
| 03 | Có sửa đổi trong `src/` → `git_dirty` là `True` | đầu ra giả ` M src/detector/yolo_face.py`; assert `is True` |
| 04 | **Tệp mới chưa theo dõi trong `src/` → `True`** | đầu ra giả `?? src/detector/backend_moi.py`; assert `is True` — ca này canh §5.1 |
| 05 | Sửa đổi trong `requirements.txt` → `True` | đầu ra giả ` M requirements.txt` |
| 06 | Không chạy được git → `True` | monkeypatch ném `OSError`; assert `is True` |
| 07 | `_kiem_tra_git_dirty_toan_cay` gọi lệnh **không kèm** phạm vi | assert tham số không chứa `"src"` |
| 08 | Meta có **cả hai** khoá | `{"git_dirty", "git_dirty_toan_cay"} <= set(meta)` |
| 09 | Hai khoá độc lập nhau | dựng tình huống phạm vi sạch nhưng toàn cây bẩn; assert `meta["git_dirty"] is False and meta["git_dirty_toan_cay"] is True` |
| 10 | Mọi ca cũ vẫn xanh | không sửa ca cũ |

Dòng 09 là ca chốt: nó tái dựng đúng tình huống của ba lượt đo ngày 03/09/2026, và là lý do mã việc
này tồn tại.

---

## 7. Lệnh tự kiểm — bạn chạy, dán nguyên văn kết quả về

```bash
python -m black --check --line-length 100 scripts/benchmark_detect.py tests/test_benchmark_detect.py
```

```bash
python -m ruff check scripts/benchmark_detect.py tests/test_benchmark_detect.py
```

```bash
python -m pytest tests/test_benchmark_detect.py -v -m "not slow"
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

Phải cho thấy đúng hai tệp của §3.

### Quét mẫu vi phạm

```bash
grep -n "untracked-files" scripts/benchmark_detect.py
```

Phải rỗng — xem §5.1.

### Kiểm đột biến bắt buộc

Ghi tệp bằng `[System.IO.File]::WriteAllText` với `UTF8Encoding($false)`, **không**
`Set-Content -Encoding utf8`.

| # | Phép đột biến | Ca **phải** đỏ |
|---|---|---|
| ĐB1 | Bỏ phạm vi đường dẫn, trả về `git status --porcelain` toàn cây | dòng 01, 02 |
| ĐB2 | Thay phạm vi bằng cờ `--untracked-files=no` | **dòng 04** |
| ĐB3 | Cho `_kiem_tra_git_dirty_toan_cay` trả cùng giá trị với `_kiem_tra_git_dirty` | dòng 09 |

ĐB2 quan trọng nhất: nó là cách sửa sai mà §5.1 cảnh báo, và bộ kiểm thử phải bắt được.

---

## 8. Ràng buộc kỹ thuật

- Python ≥ 3.11, `black` 100, `ruff` sạch. Type hints, docstring tiếng Việt kiểu Google.
- Chỉ dùng `subprocess` của thư viện chuẩn — không thêm gói git nào.
- Giữ nguyên mọi hành vi khác của script: cỡ mẫu, warm-up, lược đồ CSV, cách tính tổng hợp,
  cách chọn backend.
- Script chạy trên Pi 5 không màn hình; không import gì chỉ có trên máy phát triển.

---

## 9. Ngoài phạm vi

- **Sửa `experiment-protocol.instructions.md`** để checklist §9 nói rõ căn theo `git_dirty` phạm vi
  hẹp — Claude cập nhật sau khi mã việc này gộp, đi commit riêng loại `chore(quy-trinh)`.
- **Chạy lại ba lượt đo** — không cần: ba lượt hiện có đã chứng minh cùng `git_commit`, và notebook
  mục 1 đã ghi lập luận đó. Lượt đo tiếp theo trên Pi 5 sẽ có cờ đúng.
- 🔵-4 CSV thiếu cột định danh mô hình · 🔵-6 marker `pytest` — mã việc dọn dẹp về sau.
- Ba mục 🔵 của `P2-05` — `P2-05b` nếu người dùng đồng ý.

---

## 10. Báo cáo khi xong

Theo mẫu §12 của [`docs/quy-tac-cai-dat.md`](../quy-tac-cai-dat.md):

1. Kết quả các lệnh §7, dán nguyên văn dòng tổng kết.
2. Kết quả lệnh `grep`.
3. Bảng ba phép đột biến — đặc biệt **ĐB2**.
4. Vướng mắc.

**Không commit.**

## 10b. Lượt của người dùng — sau khi §7 xanh

Sau khi mã việc qua review và gộp vào `dev`, kiểm bằng chính tình huống đã gây ra lỗi:

```bash
python scripts/benchmark_detect.py --device-name "PC phát triển" --n-frames 100 --ghi-chu "kiểm P2-06c lượt A"
```

```bash
python scripts/benchmark_detect.py --device-name "PC phát triển" --n-frames 100 --ghi-chu "kiểm P2-06c lượt B"
```

Kết quả mong đợi: **cả hai** tệp meta có `git_dirty: false` — dù lượt B chạy khi thư mục đã có tệp
kết quả của lượt A. Trường `git_dirty_toan_cay` của lượt B sẽ là `true`, và đó là điều đúng: thư mục
có tệp mới, nhưng mã nguồn thì không đổi.

Hai tệp này chỉ để kiểm chứng, không thay thế ba lượt đo đã dùng cho notebook.
