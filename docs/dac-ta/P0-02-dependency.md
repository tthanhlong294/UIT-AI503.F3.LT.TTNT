# P0-02-dependency — Khai báo phụ thuộc và mẫu biến môi trường

| | |
|---|---|
| **Phase** | 0 — Khởi tạo & Môi trường |
| **Bước CLAUDE.md** | §5 Phase 0, bước 0.2 và một phần bước 0.6 |
| **Nhánh** | `feat/p0-02-dependency` |
| **Phụ thuộc** | `P0-01-nen-tang` (đã ĐẠT và gộp vào `dev`) |
| **Ước lượng** | 3 file, ~90 dòng |

---

## 1. Mục tiêu

Khai báo phụ thuộc của dự án thành hai tập tách biệt — **runtime chạy trên Raspberry Pi 5** và
**công cụ phát triển chạy trên PC** — với phiên bản pin cứng bằng `==`, cùng file mẫu biến môi trường.

---

## 2. DANH SÁCH TRẮNG — chỉ được tạo/sửa các file sau

| File | Thao tác |
|---|---|
| `requirements.txt` | tạo mới |
| `requirements-dev.txt` | tạo mới |
| `.env.example` | tạo mới |

> Mọi file khác: **cấm chạm**. Đặc biệt **không tạo** `models/README.md`, không sửa `pyproject.toml`,
> không đụng `src/` hay `tests/` — mã việc này không thay đổi mã nguồn.

---

## 3. Nội dung bắt buộc

### 3.1. Vì sao tách hai file — đọc trước khi làm

`ultralytics` kéo theo `torch` (khoảng 2 GB). Gói này **chỉ cần khi export model YOLOv8n-face sang
ONNX/NCNN ở Phase 2, thực hiện trên PC**. Raspberry Pi 5 chỉ chạy suy luận bằng `onnxruntime`, không
bao giờ nạp `torch`. Gộp chung một file sẽ buộc Pi cài `torch` vô ích và trái quy tắc G8.

```
requirements.txt         → cài trên CẢ Pi 5 lẫn PC (runtime)
requirements-dev.txt     → chỉ cài trên PC (export model, kiểm thử, định dạng mã)
                           dòng đầu tiên là:  -r requirements.txt
```

### 3.2. `requirements.txt` — runtime

Đúng sáu gói sau, không thêm không bớt:

| Gói | Dùng cho | Ghi chú |
|---|---|---|
| `onnxruntime` | Suy luận ONNX trên ARM64 | Không dùng `onnxruntime-gpu` |
| `opencv-python` | Đọc camera, xử lý ảnh, hiển thị cửa sổ hướng dẫn khi thu thập dữ liệu | Bản đầy đủ, **không** dùng `-headless` vì `scripts/collect_faces.py` ở Phase 1 cần `imshow` |
| `numpy` | Mảng số, tính cosine similarity | |
| `pyyaml` | Nạp `configs/*.yaml` — đã dùng ở `src/common/config.py` | |
| `flask` | Web giám sát, Phase 6 | |
| `python-telegram-bot` | Cảnh báo người lạ, Phase 5 | |

### 3.3. `requirements-dev.txt` — công cụ phát triển

Thứ tự trong file: **khối chú thích §3.5 trước**, rồi `-r requirements.txt` là **dòng lệnh đầu tiên**
(dòng đầu tiên không phải chú thích và không rỗng), sau đó bốn gói:

| Gói | Dùng cho |
|---|---|
| `ultralytics` | Export YOLOv8n-face sang ONNX/NCNN, Phase 2 |
| `pytest` | Kiểm thử |
| `black` | Định dạng mã |
| `ruff` | Lint |

### 3.4. Cách lấy số phiên bản — KHÔNG được bịa

**Tuyệt đối không tự nghĩ ra số phiên bản.** Quy trình bắt buộc:

1. Cài thật: `pip install onnxruntime opencv-python numpy pyyaml flask python-telegram-bot`
2. Lấy phiên bản thực tế `pip` đã giải: `pip freeze`
3. Ghi vào file đúng phiên bản đó, dạng `ten-goi==X.Y.Z`
4. Lặp lại cho nhóm dev

Nếu một gói không cài được, **dừng lại và báo**, không ghi phiên bản phỏng đoán.

### 3.5. Phần đầu mỗi file — cảnh báo đa nền tảng

Cả hai file requirements phải mở đầu bằng khối chú thích nêu rõ:

- File này dùng cho Python ≥ 3.11
- Phiên bản được pin từ môi trường phát triển (ghi rõ hệ điều hành và kiến trúc đã dùng để pin)
- **Cảnh báo**: máy phát triển là Windows x86-64, còn đích triển khai là ARM64 Linux. Một số gói
  có tập phiên bản wheel khác nhau giữa hai nền tảng. Các phiên bản ở đây là **bản nháp đầu tiên**,
  sẽ được kiểm chứng lại khi dựng container ARM64 ở mã việc `P0-03`; nếu có xung đột thì điều chỉnh
  ở mã việc đó.
- Lệnh cài: `pip install -r requirements.txt` (và `-r requirements-dev.txt` cho máy phát triển)

### 3.6. `.env.example`

Chứa **tên biến và giá trị mẫu rỗng hoặc giả**, tuyệt đối không chứa giá trị thật.
Mỗi biến có một dòng chú thích tiếng Việt nêu công dụng và cách lấy giá trị.

| Biến | Công dụng |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token bot Telegram gửi cảnh báo người lạ |
| `TELEGRAM_CHAT_ID` | Định danh cuộc trò chuyện nhận cảnh báo |
| `FACEID_LOG_LEVEL` | Mức log toàn hệ thống — `DEBUG`/`INFO`/`WARNING`/`ERROR`, mặc định `INFO` |
| `FACEID_LOG_FILE` | Đường dẫn file log, để trống thì chỉ ghi ra console |

Cuối file thêm một dòng nhắc: sao chép thành `.env` rồi điền giá trị thật; `.env` đã bị `.gitignore` chặn.

---

## 4. Tham số → config

Không áp dụng. Mã việc này không sinh mã và không đọc `configs/`.

---

## 5. Hành vi & ca biên

| Điều kiện | Kỳ vọng | Assert / lệnh kiểm |
|---|---|---|
| **Không có file ngoài danh sách trắng** | Đúng 3 file | `git status --short \| wc -l` trả `3` |
| **Mọi phiên bản đều lấy từ môi trường thật** | Không có số bịa | `for p in $(grep -hoE "^[a-zA-Z0-9_-]+==[^ ]+" requirements*.txt); do pip freeze \| grep -qix "$p" \|\| echo "KHONG KHOP: $p"; done` không in gì |
| Mọi dòng gói trong `requirements.txt` đều pin cứng | Không có `>=`, `~=`, hoặc gói trần | `grep -E "^[a-zA-Z]" requirements.txt \| grep -v "==" ` không có kết quả |
| `requirements.txt` đúng 6 gói | Không thừa không thiếu | `grep -cE "^[a-zA-Z].*==" requirements.txt` trả `6` |
| `requirements.txt` **không** chứa torch/ultralytics | Runtime của Pi không kéo theo torch | `grep -iE "torch\|ultralytics" requirements.txt` không có kết quả |
| `requirements-dev.txt` tham chiếu file runtime | Cài dev là có đủ runtime | `grep -vE "^\s*(#\|$)" requirements-dev.txt \| head -1` trả đúng `-r requirements.txt` |
| `requirements-dev.txt` đúng 4 gói ngoài dòng tham chiếu | | `grep -cE "^[a-zA-Z].*==" requirements-dev.txt` trả `4` |
| `.env.example` không chứa secret thật | | `grep -iE "[0-9]{8,}:[A-Za-z0-9_-]{30,}" .env.example` không có kết quả |
| `.env.example` có đủ 4 biến | | `grep -cE "^[A-Z_]+=" .env.example` trả `4` |
| Cài lại từ file sạch được | Không xung đột phiên bản | `pip install -r requirements-dev.txt` thoát mã 0 |
| Mã nguồn hiện có vẫn chạy | Không phá `P0-01` | `pytest -q` vẫn 26 passed |

---

## 6. Tiêu chí nghiệm thu — phải kiểm được bằng máy

- [ ] **Mỗi dòng bảng §5 có một lệnh kiểm đã chạy và cho kết quả đúng** — dán kết quả vào báo cáo
- [ ] `pip install -r requirements-dev.txt` chạy sạch trong môi trường hiện tại
- [ ] `pytest -q` vẫn **26 passed** (không phá `P0-01`)
- [ ] `black --check --line-length 100 src tests` và `ruff check src tests` vẫn sạch
- [ ] Cả hai file requirements có khối chú thích đầu file theo §3.5, nêu rõ nền tảng đã dùng để pin
- [ ] `git status --short` không có file ngoài danh sách trắng §2

---

## 7. Quy tắc áp dụng

| Mã | Vì sao liên quan |
|---|---|
| **G8** | `torch` không được xuất hiện trong `requirements.txt` — đây là lý do tồn tại của việc tách hai file |
| **G10** | `.env.example` là file mẫu, **không chứa token thật**. Token thật chỉ nằm trong `.env` đã bị gitignore |
| **R18** | Pin cứng bằng `==`, không dùng `>=` |
| **R5** | Không bịa số phiên bản — phải lấy từ `pip freeze` sau khi cài thật |

---

## 8. Ngoài phạm vi — KHÔNG làm ở mã việc này

- `models/README.md` — cần đường dẫn tải weights đã được **người thực hiện xác minh**;
  ghi link chưa kiểm chứng là vi phạm R5. Xử lý riêng, không giao cho mã việc này.
- `deploy/Dockerfile.arm64`, `docker-compose.yml` → mã việc `P0-03`
- Tạo môi trường ảo, viết script cài đặt tự động, thêm `Makefile` → ngoài đề cương
- Sửa `pyproject.toml` để chuyển sang khai báo phụ thuộc kiểu PEP 621 → dự án dùng `requirements.txt`
  theo đề cương, không đổi
- Thêm bất kỳ gói nào ngoài 10 gói đã liệt kê ở §3.2 và §3.3. Thấy thiếu gói → **dừng và báo**,
  không tự thêm
