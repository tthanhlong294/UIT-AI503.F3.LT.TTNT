# P0-03-docker-arm64 — Môi trường giả lập ARM64

| | |
|---|---|
| **Phase** | 0 — Khởi tạo & Môi trường |
| **Bước CLAUDE.md** | §5 Phase 0, bước 0.3 |
| **Nhánh** | `feat/p0-03-docker-arm64` |
| **Phụ thuộc** | `P0-01-nen-tang`, `P0-02-dependency` (đã ĐẠT, đã gộp vào `dev`) |
| **Ước lượng** | 3–5 file, ~120 dòng |

---

## 1. Mục tiêu

Dựng container ARM64 chạy được trên PC để phát triển và kiểm thử trước khi có Raspberry Pi 5 thật,
đồng thời **kiểm chứng các phiên bản đã pin ở `P0-02` có cài được trên nền ARM64 Linux hay không**.

---

## 2. DANH SÁCH TRẮNG

| File | Thao tác |
|---|---|
| `deploy/Dockerfile.arm64` | tạo mới |
| `deploy/docker-compose.yml` | tạo mới |
| `.dockerignore` | tạo mới |
| `requirements.txt` | **sửa có điều kiện** — xem §2b |
| `requirements-dev.txt` | **sửa có điều kiện** — xem §2b |

### 2b. Điều kiện được sửa hai file requirements

`P0-02` đã ghi trong đầu hai file rằng phiên bản là **bản nháp pin từ Windows x86-64**, sẽ kiểm chứng
lại ở mã việc này. Do đó được phép sửa, **nhưng chỉ khi thoả cả ba**:

1. Lệnh build **thất bại thật** vì phiên bản đó không có wheel cho `linux/arm64`.
2. Trong báo cáo **dán nguyên văn thông báo lỗi của pip** làm bằng chứng.
3. Chỉ đổi **đúng gói bị lỗi**, sang phiên bản gần nhất cài được, và cập nhật luôn dòng chú thích
   đầu file để ghi nhận đã kiểm chứng trên ARM64.

❌ Không đổi phiên bản vì "thấy có bản mới hơn". ❌ Không nới `==` thành `>=`.

---

## 3. Nội dung bắt buộc

### 3.1. `deploy/Dockerfile.arm64`

| Yêu cầu | Giá trị | Lý do |
|---|---|---|
| Ảnh nền | `python:3.11-slim-bookworm` | Raspberry Pi OS 64-bit (Bookworm) dùng Python 3.11. Container phải khớp môi trường đích, **không** dùng 3.12 dù máy dev đang chạy 3.12 |
| Nền tảng | `linux/arm64` | **Bắt buộc dòng đầu tiên là** `FROM --platform=linux/arm64 python:3.11-slim-bookworm` |
| Thư mục làm việc | `/app` | |
| Gói hệ thống | `libgl1`, `libglib2.0-0` | **Bắt buộc**. `opencv-python` (bản đầy đủ, đã chốt ở `P0-02`) liên kết động tới `libGL.so.1`; thiếu hai gói này thì `import cv2` sẽ ném `ImportError: libGL.so.1: cannot open shared object file` — lỗi kinh điển và tốn thời gian nhất khi đóng gói OpenCV |
| Dọn cache apt | `rm -rf /var/lib/apt/lists/*` cùng lớp `RUN` | Giảm dung lượng image |
| Cài phụ thuộc | `pip install --no-cache-dir -r requirements.txt` | |
| Công cụ kiểm thử | Xem §3.2 | |

**Thứ tự lớp**: sao chép `requirements*.txt` và cài đặt **trước** khi sao chép mã nguồn, để lớp cài
đặt được cache lại khi chỉ sửa code. Dưới giả lập QEMU, mỗi lần cài lại rất chậm nên điều này quan trọng.

### 3.2. Công cụ kiểm thử trong image — một nguồn sự thật

Container mô phỏng **runtime của Pi**, nên **không được cài `ultralytics`**: gói này kéo theo `torch`
vài GB, chỉ dùng để export model trên PC ở Phase 2, và Pi không bao giờ nạp `torch` (quy tắc G8).

Nhưng vẫn cần `pytest`, `black`, `ruff` để chạy kiểm thử trong container. **Không được chép tay lại
số phiên bản** — sẽ thành nguồn sự thật thứ hai, lệch nhau lúc nào không biết. Trích ra từ chính
`requirements-dev.txt`:

```dockerfile
RUN grep -E "^(pytest|black|ruff)==" requirements-dev.txt > /tmp/test-req.txt \
 && pip install --no-cache-dir -r /tmp/test-req.txt \
 && rm /tmp/test-req.txt
```

### 3.3. `deploy/docker-compose.yml`

- Một service tên `faceid-dev`
- `build`: context là **gốc repo**, `dockerfile: deploy/Dockerfile.arm64`
- `platform: linux/arm64`
- `volumes`: gắn gốc repo vào `/app` để sửa code trên máy thật là container thấy ngay
- `working_dir: /app`
- `command`: giữ container sống để `exec` vào (ví dụ `sleep infinity`)
- **Không** khai báo `devices: /dev/video0` — máy phát triển là Windows, không ánh xạ được camera.
  Ghi một dòng chú thích rằng phần camera sẽ bổ sung khi triển khai lên Pi 5 thật.

### 3.4. `.dockerignore`

**Bắt buộc** chặn ít nhất: `.git/`, `data/`, `models/`, `results/`, `report/`, `docs/`, `__pycache__/`,
`*.pyc`, `.venv/`, `venv/`, `wt-*/`, `.env`.

Đây không chỉ là chuyện dung lượng: `data/` chứa **ảnh khuôn mặt** và `.env` chứa token. Sao chép
chúng vào lớp image là vi phạm R25 và R27 — image có thể bị chia sẻ, và dữ liệu đã nằm trong lớp thì
không xoá được bằng cách xoá file ở lớp sau.

---

## 4. Tham số → config

Không áp dụng. Mã việc này không sinh mã Python và không đọc `configs/`.

---

## 5. Hành vi & ca biên

> Mọi lệnh chạy từ **gốc repo**. Nếu máy chưa bật giả lập ARM64 (Docker Desktop + QEMU/binfmt),
> lệnh build sẽ lỗi — khi đó **dừng lại và báo**, tuyệt đối không ghi kết quả phỏng đoán (R5).

| Điều kiện | Kỳ vọng | Assert / lệnh kiểm |
|---|---|---|
| Không có file ngoài danh sách trắng | | `git status --short \| grep -v "docs/review/" \| wc -l` trả `3`, hoặc `4`–`5` nếu §2b được kích hoạt |
| Mọi phiên bản trong requirements là thật, cài được trên ARM64 | Không có số bịa | `docker run --rm --platform linux/arm64 faceid:arm64 pip freeze > /tmp/f.txt; for p in $(grep -hoE "^[a-z0-9_-]+==[^ ]+" requirements.txt); do grep -qix "$p" /tmp/f.txt \|\| echo "KHONG KHOP: $p"; done` không in gì |
| Build thành công | | `docker build --platform linux/arm64 -f deploy/Dockerfile.arm64 -t faceid:arm64 .` thoát mã 0 |
| Image đúng kiến trúc ARM64 | Không phải x86 | `docker image inspect faceid:arm64 --format "{{.Architecture}}"` trả `arm64` |
| **Dockerfile tự khai báo nền tảng** — build KHÔNG cờ vẫn ra ARM64 | Không phụ thuộc người build nhớ truyền cờ | `docker build -f deploy/Dockerfile.arm64 -t faceid:nofl . && docker image inspect faceid:nofl --format "{{.Architecture}}"` trả `arm64` |
| Python trong image là 3.11 | Khớp Pi OS Bookworm | `docker run --rm --platform linux/arm64 faceid:arm64 python -V` khớp `Python 3.11.` |
| **Cổng C của Phase 0** | Nạp được hai thư viện cốt lõi | `docker run --rm --platform linux/arm64 faceid:arm64 python -c "import cv2, onnxruntime; print('ok')"` in `ok` |
| Không thiếu thư viện hệ thống của OpenCV | Không lỗi `libGL.so.1` | Bao gồm trong lệnh trên — nếu thiếu `libgl1` lệnh sẽ ném `ImportError` |
| Mã nguồn `P0-01` chạy được trong container | Không hồi quy | `docker run --rm --platform linux/arm64 -v "$(pwd)":/app -w /app faceid:arm64 pytest -q` trả `26 passed` |
| **Không có `ultralytics`/`torch` trong image** | Giữ image gọn, đúng G8 | `docker run --rm --platform linux/arm64 faceid:arm64 pip list \| grep -iE "ultralytics\|torch"` không có kết quả |
| Có `pytest`, `black`, `ruff` trong image | Kiểm thử được trong container | `docker run --rm --platform linux/arm64 faceid:arm64 pip list \| grep -cE "^(pytest\|black\|ruff) "` trả `3` |
| `docker-compose.yml` hợp lệ | | `docker compose -f deploy/docker-compose.yml config` thoát mã 0 |
| `.dockerignore` chặn đủ thư mục nhạy cảm | Ảnh khuôn mặt và secret không vào image | `for d in .git data models results report .env; do grep -qE "^/?$d" .dockerignore \|\| echo "THIEU: $d"; done` không in gì |

---

## 6. Tiêu chí nghiệm thu

- [ ] **Mỗi dòng bảng §5 có một lệnh đã chạy và cho kết quả đúng** — dán kết quả thật vào báo cáo
- [ ] `pytest -q` chạy **trên máy thật** vẫn 26 passed (không phá `P0-01`)
- [ ] `black --check --line-length 100 src tests` và `ruff check src tests` vẫn sạch
- [ ] Nếu §2b được kích hoạt: báo cáo có **nguyên văn lỗi pip** làm bằng chứng, và chú thích đầu file
      requirements đã cập nhật
- [ ] Báo cáo ghi rõ **thời gian build** và dung lượng image (`docker images faceid:arm64`) — số liệu
      này dùng cho Chương 3 §Môi trường triển khai

---

## 7. Quy tắc áp dụng

| Mã | Vì sao liên quan |
|---|---|
| **G8** | `torch`/`ultralytics` không được vào image ARM64 |
| **R5** | Không có Docker hoặc build lỗi → **dừng và báo**, không ghi kết quả phỏng đoán |
| **R18** | Giữ pin cứng `==`; chỉ đổi phiên bản khi có bằng chứng lỗi build |
| **R25, R27** | `.dockerignore` phải chặn `data/`, `.env` — ảnh khuôn mặt và token không được nằm trong lớp image |

---

## 8. Ngoài phạm vi — KHÔNG làm ở mã việc này

- `deploy/systemd/faceid.service` → Phase 6, bước 6.6
- Ánh xạ camera `/dev/video0`, chạy thật trên Pi 5 → bước 0.4, làm trên phần cứng thật
- Tối ưu dung lượng image bằng multi-stage build, chuyển sang `alpine`, chạy bằng user không phải
  root → hợp lý về kỹ thuật nhưng ngoài đề cương; ghi vào phần đề xuất của báo cáo bàn giao nếu muốn
- Publish image lên registry
- `models/README.md` — cần đường dẫn tải weights do người thực hiện xác minh
- Sửa bất kỳ file nào trong `src/`, `tests/`, `configs/`, `docs/`
