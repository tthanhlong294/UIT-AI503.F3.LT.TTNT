# Review P0-03-docker-arm64 — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P0-03-docker-arm64.md` |
| **Nhánh** | `feat/p0-03-docker-arm64` (worktree `wt-p0-03-docker`) |
| **Ngày** | 2026-08-07 |
| **Phán quyết** | 🔴 TRẢ LẠI — 0 lỗi 🔴, **1 lỗi 🟡**, 3 góp ý 🔵 |

Mã việc gần đạt. Toàn bộ 13 dòng kiểm của §5 đều xanh, kể cả Cổng C của Phase 0. Chỉ còn **một
dòng thiếu trong `Dockerfile.arm64`** — sửa xong là ĐẠT.

---

## 1. Kết quả kiểm máy

### 1.1. Ba lệnh bắt buộc (chạy trên máy thật)

| Lệnh | Kết quả |
|---|---|
| `black --check --line-length 100 src tests` | `7 files would be left unchanged` ✅ |
| `ruff check src tests` | `All checks passed!` ✅ |
| `pytest -q` | `26 passed in 2.25s` ✅ — không hồi quy `P0-01` |

### 1.2. Phạm vi file

```
$ git status --short
A  .dockerignore
A  deploy/Dockerfile.arm64
A  deploy/docker-compose.yml
```

- **3 file, đúng và đủ DANH SÁCH TRẮNG §2.** Không có file nào ngoài danh sách. ✅
- `git log --oneline dev..HEAD` → **rỗng**: chưa có commit nào. ✅
- `git status --short | grep -Ei '\.(jpg|png|npy|npz|onnx|pt|pth|env|db|sqlite3?)$'` → không kết quả. ✅
- **Về việc Gemini dùng `git add`** (file ở trạng thái `A ` thay vì `??`): **không phải vi phạm.**
  `GEMINI.md:195` cấm đích danh `git commit / push / reset / checkout / merge / đổi nhánh` —
  `git add` **không** nằm trong danh sách. Checklist `GEMINI.md:246` "Chưa commit gì cả" cũng thoả
  (0 commit). Việc stage không làm mất khả năng review, không đổi nội dung file, và lệnh kiểm
  §5 dòng 1 vẫn trả `3`. Ghi nhận là chi tiết, **không tính lỗi**.
- Lưu ý cho người commit: nhánh này đang **đứng sau `dev` 9 commit** (`ae41382` vs `1a79221`).
  Vì vậy `git diff dev --name-only` có liệt kê `CLAUDE.md`, `models/README.md`,
  `report/chapters/*` — đó là **các commit của `dev` mà nhánh chưa có**, không phải file Gemini sửa.
  Đã đối chiếu: cây làm việc chỉ khác HEAD đúng 3 file mới.

### 1.3. §2b — điều kiện sửa hai file requirements: **KHÔNG kích hoạt** ✅

```
$ git diff dev -- requirements.txt requirements-dev.txt
(rỗng)
```

Hai file requirements **nguyên vẹn**, không sửa một ký tự. Đây là kết quả đúng: build sạch
(`--no-cache`) đã cài toàn bộ 6 gói của `requirements.txt` trên `linux/arm64` **không một lỗi pip**:

```
Successfully installed ... flask-3.1.3 numpy-2.2.0 onnxruntime-1.20.1
opencv-python-4.13.0.92 python-telegram-bot-21.11.1 pyyaml-6.0.2 ...
```

→ Kết luận có giá trị cho báo cáo: **các phiên bản pin ở `P0-02` đã được kiểm chứng là cài được
trên ARM64 Linux/Python 3.11.** Không có gì để nghi ngờ về §2b.

---

## 2. Đối chiếu 13 dòng bảng §5 — kết quả thật

| # | Dòng kiểm §5 | Kết quả thật | KL |
|---|---|---|---|
| 1 | Không có file ngoài danh sách trắng | `git status --short \| grep -v docs/review/ \| wc -l` → `3` | ✅ |
| 2 | Phiên bản requirements khớp gói thật trong container | Vòng lặp so `pip freeze` với 6 dòng `requirements.txt` → **không in gì** | ✅ |
| 3 | Build thành công | `docker build --platform linux/arm64 ...` → `EXIT=0` (cả bản có cache lẫn `--no-cache`) | ✅ |
| 4 | Image đúng kiến trúc | `docker image inspect --format {{.Architecture}}` → **`arm64`** (os `linux`) | ✅ |
| 5 | Python 3.11 | `python -V` → **`Python 3.11.15`** (khớp Pi OS Bookworm, không phải 3.12 của máy dev) | ✅ |
| 6 | **Cổng C Phase 0** | `python -c "import cv2, onnxruntime; print('ok')"` → **`ok 4.13.0 1.20.1`** | ✅ |
| 7 | Không lỗi `libGL.so.1` | Không có `ImportError` ở dòng 6 → `libgl1` + `libglib2.0-0` đã đủ | ✅ |
| 8 | `pytest` trong container ARM64 | **`26 passed in 16.21s`** | ✅ |
| 9 | Không có `ultralytics`/`torch` | `pip list \| grep -iE "ultralytics\|torch"` → **không kết quả** | ✅ |
| 10 | Có `pytest`, `black`, `ruff` | `grep -cE "^(pytest\|black\|ruff) "` → **`3`** (pytest 9.1.1, black 24.4.2, ruff 0.16.1) | ✅ |
| 11 | `docker compose config` hợp lệ | `EXIT=0`; context resolve về gốc repo, `platform: linux/arm64` | ✅ |
| 12 | `.dockerignore` chặn đủ thư mục nhạy cảm | Vòng lặp `.git data models results report .env` → **không in `THIEU:`** | ✅ |
| 13 | (dòng 7 gộp với 6 theo đặc tả) | — | — |

**Kiểm thêm ngoài bảng — chứng minh `.dockerignore` có hiệu lực thật, không chỉ có mặt trên giấy:**

```
$ docker run --rm --platform linux/arm64 faceid:arm64 sh -c 'ls -a /app'
.claude  .dockerignore  .env.example  .gitignore  .pytest_cache  .ruff_cache
CLAUDE.md  GEMINI.md  README.md  deploy  pyproject.toml
requirements-dev.txt  requirements.txt  src  tests
```

`.git`, `models/`, `docs/`, `report/` **tồn tại trên host nhưng không có trong image** → xác nhận
loại trừ hoạt động (R25/R27). `data/`, `results/`, `.venv/` chưa tồn tại trên host nên chỉ kiểm
được bằng mẫu trong `.dockerignore`, chưa kiểm được bằng thực nghiệm — **ghi rõ để khỏi hiểu nhầm**.

### 2.1. Số liệu cho Chương 3 §Môi trường triển khai (đặc tả §6)

Không tìm thấy hai số này trong repo (Gemini không để lại file báo cáo nào — bàn giao qua chat).
**Người review tự đo lại**, số dưới đây dùng được cho báo cáo:

| Chỉ số | Giá trị đo | Ngữ cảnh (R8) |
|---|---|---|
| Thời gian build sạch (`--no-cache`) | **1053 s ≈ 17 phút 33 s** | Docker 29.6.2 / Docker Desktop, giả lập QEMU `linux/arm64` trên PC Windows x86-64 |
| — trong đó lớp `pip install -r requirements.txt` | **526 s** | Chiếm ~50 % thời gian build |
| Thời gian build lại (có cache, chỉ đổi mã nguồn) | **7 s** | Chỉ lớp `COPY . .` chạy lại |
| Dung lượng image (content size) | **251 663 863 B ≈ 252 MB** | `docker image inspect --format {{.Size}}` |
| Dung lượng đĩa Docker Desktop báo | 1,05 GB | Gồm cả lớp nền dùng chung + attestation manifest; **không phải** cỡ image truyền đi |

> Chênh lệch 252 MB / 1,05 GB là điểm dễ ghi nhầm vào báo cáo. **Số nên dùng là 252 MB.**
> Tỉ số 1053 s → 7 s cũng là bằng chứng định lượng cho việc xếp lớp đúng thứ tự (§3.1) — đáng đưa
> vào Chương 3 để giải thích vì sao phải tách `COPY requirements*.txt` khỏi `COPY . .`.

---

## 3. Đối chiếu nội dung bắt buộc §3

| Mục | Yêu cầu | Thực tế | KL |
|---|---|---|---|
| §3.1 | Ảnh nền `python:3.11-slim-bookworm` | `Dockerfile.arm64:1` | ✅ |
| §3.1 | **Khai báo nền tảng `linux/arm64` trong Dockerfile** | **thiếu** | ❌ **CẦN SỬA-1** |
| §3.1 | `WORKDIR /app` | dòng 3 | ✅ |
| §3.1 | `libgl1`, `libglib2.0-0` | dòng 6 | ✅ |
| §3.1 | `rm -rf /var/lib/apt/lists/*` cùng lớp `RUN` | dòng 5–7, cùng một `RUN` | ✅ |
| §3.1 | `pip install --no-cache-dir -r requirements.txt` | dòng 10 | ✅ |
| §3.1 | Thứ tự lớp: requirements trước mã nguồn | dòng 9–15 trước dòng 17 `COPY . .` | ✅ |
| §3.2 | Lấy `pytest/black/ruff` bằng `grep` từ `requirements-dev.txt`, không chép tay số phiên bản | dòng 13–15 đúng nguyên văn mẫu; **không có số phiên bản nào viết tay** | ✅ |
| §3.2 | Không cài `ultralytics` | `grep` chỉ khớp 3 gói, đã kiểm bằng `pip list` | ✅ |
| §3.3 | service `faceid-dev`, context gốc repo, `dockerfile:`, `platform:`, `volumes`, `working_dir`, `command` | `docker-compose.yml:1–10` đủ 7 mục | ✅ |
| §3.3 | Không khai báo `devices:`, có chú thích camera | dòng 11 có chú thích, không có `devices` | ✅ |
| §3.4 | Chặn đủ 12 mục | `.dockerignore:1–12` đủ cả 12, không thiếu mục nào | ✅ |
| §8 | Không làm việc ngoài phạm vi | Không có `systemd`, không multi-stage, không ánh xạ camera, không đụng `src/`,`tests/`,`configs/`,`docs/` | ✅ |

**§3.2 xin ghi nhận riêng**: đây là mục dễ làm ẩu nhất và Gemini làm đúng — dòng 13 `grep` thật từ
`requirements-dev.txt` chứ không chép `pytest==9.1.1` vào Dockerfile. Nhờ vậy chỉ còn một nguồn sự
thật về phiên bản công cụ kiểm thử. Đã kiểm chứng: 3 phiên bản trong image trùng khít file gốc.

---

## 4. Lỗi phải sửa

### 🟡 CẦN SỬA-1 — `Dockerfile.arm64` không tự khai báo nền tảng ARM64 (thiếu mục bắt buộc §3.1)

**Vị trí**: `deploy/Dockerfile.arm64:1`

```dockerfile
FROM python:3.11-slim-bookworm
```

**Vì sao**: đặc tả §3.1 có một dòng bắt buộc — *"Nền tảng | `linux/arm64` | Khai báo
`--platform=$TARGETPLATFORM` hoặc cố định `linux/arm64`"*. Dòng 1 không làm cả hai cách, nên
kiến trúc image **hoàn toàn phụ thuộc vào việc người gõ lệnh có nhớ thêm cờ `--platform` hay không**.

Đây không phải lo xa — đã kiểm chứng bằng thực nghiệm trong lượt review này:

```
$ docker build -t platformtest:noflag .        # Dockerfile chỉ có FROM python:3.11-slim-bookworm
$ docker image inspect platformtest:noflag --format "Architecture={{.Architecture}}"
Architecture=amd64
```

Hậu quả cụ thể: ai đó chạy `docker build -f deploy/Dockerfile.arm64 -t faceid:arm64 .` (thiếu cờ)
sẽ nhận **một image x86-64 mang cái tên `arm64`**, và nó vẫn chạy được, vẫn `26 passed`, vẫn
`import cv2` bình thường — **không có dấu hiệu nào báo sai**. Mọi số đo FPS/latency lấy từ image đó
ở Phase 2–7 sẽ là số của x86-64 chạy native, nhanh hơn ARM64 giả lập nhiều lần, và sẽ lọt vào
`results/` như một con số ARM64 (vi phạm R5/R8 ở khâu sau). Tên file `Dockerfile.arm64` càng làm
người dùng tin nhầm rằng kiến trúc đã được bảo đảm.

**Sửa**: sửa dòng 1 thành

```dockerfile
FROM --platform=linux/arm64 python:3.11-slim-bookworm
```

Sau đó build lại **không kèm cờ** và xác nhận vẫn ra `arm64`:

```bash
docker build -f deploy/Dockerfile.arm64 -t faceid:arm64 .
docker image inspect faceid:arm64 --format "{{.Architecture}}"   # phải in: arm64
```

Không cần sửa `docker-compose.yml` (đã có `platform: linux/arm64`) và cũng không cần sửa các lệnh
kiểm ở §5 — chúng vẫn đúng, chỉ là từ nay không còn phụ thuộc vào cờ nữa.

---

## 5. 🔵 Góp ý — không chặn, người dùng quyết định

- **GY-1 — `.pytest_cache/` và `.ruff_cache/` lọt vào image** (thấy trong `ls -a /app`).
  Vô hại về bảo mật, chỉ là rác. Đặc tả §3.4 không yêu cầu nên **không tính lỗi**. Nếu muốn dọn:
  thêm 2 dòng vào `.dockerignore`. Lợi ích nhỏ, chi phí gần bằng 0.
- **GY-2 — chú thích đầu `requirements.txt` / `requirements-dev.txt` nay đã lỗi thời.**
  Hai file vẫn ghi *"sẽ được kiểm chứng lại khi dựng container ARM64 ở mã việc P0-03"* — trong khi
  P0-03 vừa kiểm chứng xong và kết quả là **không phải đổi gì**. Gemini **làm đúng** khi không sửa:
  §2b chỉ cho phép sửa hai file này khi build **thất bại**. Đây là kẽ hở của đặc tả, không phải lỗi
  cài đặt. Đề nghị người dùng (hoặc `spec-writer`) tự cập nhật một dòng chú thích thành *"đã kiểm
  chứng cài được trên linux/arm64 + Python 3.11.15 ngày 07/08/2026 (P0-03)"* — thông tin này có giá
  trị cho Chương 3 và cho người dựng lại repo.
- **GY-3 — tên project của compose đang là `deploy`** (lấy theo tên thư mục chứa file compose), nên
  container/network sẽ mang tiền tố `deploy_`. Không sai, không thuộc đặc tả. Nếu muốn dễ đọc thì
  thêm `name: faceid` vào compose. Ngoài phạm vi mã việc này.

---

## 6. Hai điểm sống còn — soi riêng

- **Trung thực số liệu (R5)**: không có con số nào bị bịa trong 3 file cấu hình. Hai số duy nhất
  đáng đưa vào báo cáo (thời gian build, dung lượng image) người review đã **tự đo lại** thay vì
  chép theo lời báo cáo — xem §2.1. Rủi ro số liệu thật sự của mã việc này **không nằm trong code
  mà nằm ở CẦN SỬA-1**: một image sai kiến trúc sẽ âm thầm sinh ra số đo sai ở Phase 2–7.
- **An toàn phần cứng**: không áp dụng — mã việc không sinh mã Python, không đụng GPIO/relay/camera.
  Đã xác nhận compose **không** khai báo `devices:` đúng như §3.3 và §8 yêu cầu.

---

## 7. Việc tiếp theo

Sửa đúng **1 dòng**, không đụng file nào khác:

```
Sửa deploy/Dockerfile.arm64 dòng 1 thành:
FROM --platform=linux/arm64 python:3.11-slim-bookworm

Rồi chạy lại 2 lệnh kiểm và dán kết quả thật:
  docker build -f deploy/Dockerfile.arm64 -t faceid:arm64 .        (CO Y KHONG kem --platform)
  docker image inspect faceid:arm64 --format "{{.Architecture}}"   (phai in: arm64)

KHONG sua requirements.txt / requirements-dev.txt. KHONG commit.
```

Sau khi Gemini báo xong → review vòng 2, ghi nối tiếp vào **chính file này**.
Nếu vòng 2 sạch, commit đề xuất:

```
feat(deploy): moi truong gia lap ARM64 bang Docker (P0-03)
```

---

## 8. Nhận xét về chất lượng đặc tả (gửi `spec-writer`)

Đặc tả `P0-03` là bản tốt nhất trong ba mã việc đầu, nên ghi lại điều gì làm nó tốt để tái dùng:

1. **Bảng §5 gồm 13 dòng, mỗi dòng một lệnh chạy được, dán vào shell là ra kết quả.** Nhờ vậy vòng
   review này gần như không phải phán đoán — chỉ chạy và ghi. Mẫu này nên bắt buộc cho mọi mã việc sau.
2. **§2b "sửa có điều kiện" là thiết kế đúng**: cho phép đúng thứ cần cho phép, kèm 3 điều kiện và
   yêu cầu bằng chứng nguyên văn. Kết quả: Gemini không đụng vào requirements, và bản thân việc
   *không đụng* đã trở thành một kết luận kiểm chứng có giá trị.
3. **§3.2 nêu thẳng lý do "một nguồn sự thật" kèm đoạn `grep` mẫu** — chỗ dễ làm ẩu nhất lại là chỗ
   làm đúng nhất. Xu hướng rõ: yêu cầu nào có **kèm đoạn mã mẫu** thì được thực hiện chính xác.

**Điểm cần rút kinh nghiệm** — và nó chính là nguyên nhân của lỗi 🟡 duy nhất:

4. Yêu cầu "Nền tảng `linux/arm64`" nằm ở **một ô trong bảng §3.1**, diễn đạt bằng hai lựa chọn
   (`--platform=$TARGETPLATFORM` *hoặc* cố định) và **không có dòng `FROM` mẫu**, trong khi các mục
   khác của cùng bảng đều có giá trị cụ thể. Đây đúng là kiểu "yêu cầu bị chôn" trong bảng chẩn đoán
   của quy trình. Quan trọng hơn: **§5 không có dòng nào bắt được lỗi này** — cả 13 lệnh kiểm đều
   tự truyền `--platform`, nên Dockerfile thiếu khai báo vẫn qua sạch 13/13.
   → Bài học cho đặc tả sau: **mỗi mục bắt buộc ở §3 phải có ít nhất một dòng ở §5 kiểm được nó
   khi KHÔNG có sự trợ giúp của cờ dòng lệnh.** Cụ thể ở đây, §5 nên có thêm dòng:
   *"`docker build` **không kèm** `--platform` vẫn ra image `arm64`"*.
5. §6 yêu cầu "báo cáo ghi rõ thời gian build và dung lượng image" nhưng **không nói ghi vào đâu**.
   Vì bàn giao Gemini→Claude đi qua file chứ không qua hội thoại (R39), số liệu này đã thất lạc và
   người review phải đo lại (mất ~18 phút build). → Đặc tả sau nên chỉ đích danh nơi ghi, ví dụ
   *"ghi vào phần cuối biên bản bàn giao"* hoặc cấp cho Gemini quyền tạo một file
   `docs/dac-ta/<mã>.ketqua.md` nằm trong danh sách trắng.

---
---

# Review P0-03-docker-arm64 — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P0-03-docker-arm64.md` |
| **Nhánh** | `feat/p0-03-docker-arm64` (worktree `wt-p0-03-docker`) |
| **Ngày** | 2026-08-07 |
| **Phán quyết** | ✅ **ĐẠT** — 0 lỗi 🔴, 0 lỗi 🟡 |

Lỗi 🟡 duy nhất của vòng 1 đã được sửa đúng, sửa gọn, và **đã kiểm chứng bằng đúng phép thử mà
vòng 1 chỉ ra là còn thiếu**. Không phát sinh lỗi mới. Mã việc đủ điều kiện commit.

---

## 1. Xác minh bản sửa

### 1.1. Nội dung sửa — đúng 1 dòng, đúng chỗ

```
$ git diff
-FROM python:3.11-slim-bookworm
+FROM --platform=linux/arm64 python:3.11-slim-bookworm
```

`deploy/Dockerfile.arm64:1` nay là:

```dockerfile
FROM --platform=linux/arm64 python:3.11-slim-bookworm
```

Đây đúng là chỉ dẫn ở mục "Sửa" của CẦN SỬA-1 vòng 1, không thừa không thiếu. 16 dòng còn lại của
Dockerfile giữ nguyên — đã đối chiếu từng dòng với bảng §3 ở vòng 1, mọi mục vẫn ✅.

### 1.2. Phạm vi — lệnh N4 chỉ cho phép sửa `deploy/Dockerfile.arm64`

```
$ git status --short
A  .dockerignore
AM deploy/Dockerfile.arm64
A  deploy/docker-compose.yml
?? docs/review/P0-03-docker-arm64.review.md
```

| Kiểm | Kết quả |
|---|---|
| Chỉ `Dockerfile.arm64` có phần `M` (đã sửa) | ✅ — `.dockerignore` và `docker-compose.yml` vẫn là `A ` thuần, **không đổi** |
| `git diff` (chưa stage) chỉ động tới 1 file, 1 dòng | ✅ — xem 1.1 |
| `git diff dev -- requirements.txt requirements-dev.txt` | **rỗng** ✅ — hai file requirements vẫn nguyên vẹn qua cả 2 vòng |
| `git log --oneline dev..HEAD` | **rỗng** ✅ — Gemini vẫn chưa commit gì, đúng `GEMINI.md:195` |
| File `??` duy nhất | là biên bản review này, do người review tạo — nằm ngoài diện kiểm §5 |

Không có file nào ngoài DANH SÁCH TRẮNG. Không có file dữ liệu/secret nào lọt vào git.

---

## 2. Phép thử mấu chốt — build **KHÔNG** kèm cờ `--platform`

Đây chính là lỗ hổng của bảng §5 vòng 1: cả 13 lệnh kiểm đều tự truyền `--platform`, nên không
lệnh nào phát hiện được Dockerfile thiếu khai báo nền tảng. Vòng 2 kiểm bằng phép thử đó.

**Không tin image `faceid:arm64check` có sẵn** (không có cách nào biết nó được build bằng lệnh gì),
người review **tự build lại** bằng một tag riêng:

```
$ docker build -f deploy/Dockerfile.arm64 -t faceid:reviewv2 .     <- CỐ Ý KHÔNG có --platform
EXIT=0

$ docker image inspect faceid:reviewv2 --format "Architecture={{.Architecture}} Os={{.Os}}"
Architecture=arm64 Os=linux
```

✅ **Đạt.** Kiến trúc ARM64 nay do chính Dockerfile bảo đảm, không còn phụ thuộc người gõ lệnh.

### 2.1. Xác nhận sâu hơn — image thật sự chạy mã ARM64, không phải chỉ dán nhãn

Nhãn `Architecture` trong metadata về nguyên tắc có thể lệch với nội dung thật, nên kiểm thêm ở ba
tầng độc lập:

```
$ docker run --rm faceid:reviewv2 uname -m
aarch64

$ docker run --rm faceid:reviewv2 python -c "import platform,sysconfig; ..."
machine= aarch64
platform= linux-aarch64

$ head -c 20 /usr/local/bin/python3.11 | od -An -tx1        <- ELF header của interpreter
 7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00
 03 00 b7 00
```

Trường `e_machine` của ELF = **`0xb7` = 183 = EM_AARCH64** (nếu là x86-64 sẽ là `0x3e`). Bản thân
Docker cũng cảnh báo `The requested image's platform (linux/arm64) does not match the detected host
platform (linux/amd64/v4)` — tức nó đang chạy qua QEMU. Ba bằng chứng độc lập cùng kết luận:
**image là ARM64 thật.**

### 2.2. Đối chứng — vì sao phương án còn lại của đặc tả sẽ KHÔNG sửa được lỗi ⚠️

Đặc tả §3.1 cho hai lựa chọn: *"Khai báo `--platform=$TARGETPLATFORM` **hoặc** cố định
`linux/arm64`"*. Gemini chọn vế sau. Người review đã thử vế trước bằng một Dockerfile tối giản:

```
FROM --platform=$TARGETPLATFORM python:3.11-slim-bookworm
```
```
$ docker build -t tgtplat:noflag .          <- không kèm --platform
$ docker image inspect tgtplat:noflag --format "Architecture={{.Architecture}}"
Architecture=amd64
```

→ **`$TARGETPLATFORM` mặc định bằng nền tảng của máy build**, nên nếu Gemini chọn vế đầu thì lỗi
vòng 1 vẫn còn nguyên. **Gemini đã chọn đúng vế duy nhất giải quyết được vấn đề.** Xem thêm §6.

### 2.3. Cảnh báo lint của BuildKit — đã xem xét, **không phải lỗi**

Bản build in ra:

```
1 warning found:
 - FromPlatformFlagConstDisallowed: FROM --platform flag should not use constant
   value "linux/arm64" (line 1)
```

BuildKit khuyến nghị dùng biến thay vì hằng, vì Dockerfile "chuẩn" phải build được cho nhiều kiến
trúc. **Với đồ án này khuyến nghị đó không áp dụng**: đích triển khai chỉ có một là Raspberry Pi 5
(ARM64), và mục tiêu của mã việc là **cố định** kiến trúc để không thể build nhầm — đúng như §2.2
vừa chứng minh. Đặc tả §3.1 cũng cho phép tường minh cách viết này. Ghi nhận để người viết báo cáo
biết cảnh báo này là **có chủ đích**, không phải sơ suất; không cần sửa.

---

## 3. Hồi quy — các dòng có thể bị ảnh hưởng bởi việc đổi `FROM`

Chạy trên chính image vừa tự build từ Dockerfile đã sửa (`faceid:reviewv2`), không dùng image cũ:

| # | Dòng kiểm §5 | Kết quả vòng 2 | KL |
|---|---|---|---|
| 5 | Python trong image là 3.11 | `Python 3.11.15` | ✅ |
| 6 | **Cổng C Phase 0** — `import cv2, onnxruntime` | `ok 4.13.0 1.20.1` | ✅ |
| 7 | Không lỗi `libGL.so.1` | không có `ImportError` → `libgl1`/`libglib2.0-0` vẫn đủ | ✅ |
| 8 | `pytest` trong container ARM64 | **`26 passed`** (chạy 2 lần: 2,22 s và 2,75 s) | ✅ |
| 9 | Không có `ultralytics`/`torch` | `pip list | grep -iE "ultralytics|torch"` → không kết quả | ✅ |
| 10 | Có `pytest`, `black`, `ruff` | đếm được `3` | ✅ |
| 3 | Build thành công | `EXIT=0` | ✅ |
| 4 | Image đúng kiến trúc | `arm64` — **kể cả khi không truyền cờ** | ✅ |

Các dòng §5 còn lại (1, 2, 11, 12) không thể bị ảnh hưởng bởi việc đổi dòng `FROM` và đã kiểm đủ ở
vòng 1; không chạy lại, đúng phạm vi vòng 2.

> ⚠️ **Một điểm về số liệu, ghi lại để không ai dùng nhầm sau này.**
> `pytest` trong container ARM64 đo được **16,21 s ở vòng 1** nhưng **2,22 s và 2,75 s ở vòng 2** —
> cùng một bộ 26 test, cùng kiến trúc. Chênh lệch đến từ độ "ấm" của QEMU/binfmt và cache hệ thống
> tệp, **không** phải từ kiến trúc. Do đó **tuyệt đối không dùng thời gian chạy trong container giả
> lập làm số đo hiệu năng trong báo cáo** (trái R8/R9: không ổn định, không kiểm soát được ngữ cảnh).
> Mọi số FPS/latency phải đo trên **Pi 5 thật** từ bước 0.4 trở đi. Container chỉ dùng để kiểm tính
> đúng đắn, không dùng để đo tốc độ.

---

## 4. Số liệu cho Chương 3 §Môi trường triển khai

Bảng dưới đây là **nguồn duy nhất** cho các con số về môi trường Docker trong báo cáo.

### 4.1. Thời gian build và dung lượng

| Chỉ số | Giá trị | Ghi chú ngữ cảnh (R8) |
|---|---|---|
| Thời gian build **sạch** (`--no-cache`) | **1053 s ≈ 17 phút 33 s** | Docker 29.6.2 / Docker Desktop, giả lập QEMU `linux/arm64` trên PC Windows x86-64 |
| — riêng lớp `pip install -r requirements.txt` | **526 s** (~50 % tổng) | Cài 24 gói (6 gói trực tiếp + phụ thuộc) |
| Thời gian build **lại có cache** (chỉ đổi mã nguồn) | **3–7 s** | Chỉ lớp `COPY . .` chạy lại |
| **Dung lượng image — CONTENT SIZE** | **251 663 874 B ≈ 252 MB** | ⭐ **Đây là con số phải dùng trong báo cáo** |
| Dung lượng "disk usage" Docker Desktop hiển thị | 1,05 GB | ❌ **KHÔNG dùng con số này** |

> ⭐ **Phân biệt hai con số — chỗ dễ ghi nhầm nhất.**
> `docker images` trên Docker Desktop bản mới hiển thị **hai cột khác nhau**:
> - **CONTENT SIZE = 252 MB** — tổng dung lượng thật của các lớp thuộc image, là con số có ý nghĩa
>   khi nói "image nặng bao nhiêu"; lấy bằng `docker image inspect faceid:arm64 --format "{{.Size}}"`.
> - **DISK USAGE = 1,05 GB** — dung lượng chiếm trên đĩa của builder, **bao gồm cả các lớp nền dùng
>   chung với image khác, cache build và attestation manifest**. Con số này thay đổi theo trạng thái
>   máy, không tái lập được, và sẽ khiến người đọc tưởng image nặng gấp 4 lần thực tế.
>
> **Trong báo cáo ghi: "image ARM64 dung lượng ~252 MB".** Nguồn: `docker image inspect`, đo ngày
> 07/08/2026. Nếu cần một câu giải thích: *"số liệu là content size của image, không bao gồm lớp nền
> dùng chung và cache build"*.

Tỉ số **1053 s → 3–7 s** giữa build sạch và build lại là bằng chứng định lượng cho quyết định xếp
lớp ở §3.1 (cài thư viện trước, sao chép mã nguồn sau). Đáng đưa vào Chương 3 để giải thích thiết kế
Dockerfile, vì dưới giả lập QEMU đây là khác biệt giữa "sửa code chờ 3 giây" và "chờ 18 phút".

### 4.2. Phiên bản thành phần trong container (đo trực tiếp, không chép từ file)

| Thành phần | Phiên bản | Cách lấy |
|---|---|---|
| Ảnh nền | `python:3.11-slim-bookworm` | Debian 12 Bookworm — **cùng nền Raspberry Pi OS 64-bit** |
| Kiến trúc | `arm64` / `aarch64` (`linux-aarch64`) | `docker image inspect`, `uname -m`, ELF `e_machine=0xb7` |
| Python | **3.11.15** | `python -V` — khớp Python 3.11 của Pi OS Bookworm, **không** phải 3.12 của máy dev |
| OpenCV | **4.13.0** (gói `opencv-python==4.13.0.92`) | `cv2.__version__` |
| ONNX Runtime | **1.20.1** | `onnxruntime.__version__` |
| NumPy | 2.2.0 | `pip freeze` |
| Flask | 3.1.3 | `pip freeze` |
| python-telegram-bot | 21.11.1 | `pip freeze` |
| PyYAML | 6.0.2 | `pip freeze` |
| pytest / black / ruff | 9.1.1 / 24.4.2 / 0.16.1 | `pip list` — lấy từ `requirements-dev.txt` bằng `grep`, không chép tay |
| Thư viện hệ thống thêm | `libgl1`, `libglib2.0-0` | Bắt buộc cho `import cv2` |

### 4.3. Kết luận kiểm chứng `requirements.txt` trên ARM64 ⭐

**Toàn bộ 6 gói pin cứng ở `P0-02` cài được trên `linux/arm64` + Python 3.11, không một lỗi pip,
không phải đổi một phiên bản nào.** Bằng chứng: lần build sạch `--no-cache` kết thúc `EXIT=0` với

```
Successfully installed anyio-4.14.2 blinker-1.9.0 certifi-2026.7.22 click-8.4.2
coloredlogs-15.0.1 flask-3.1.3 flatbuffers-25.12.19 h11-0.16.0 httpcore-1.0.9
httpx-0.28.1 humanfriendly-10.0 idna-3.18 itsdangerous-2.2.0 jinja2-3.1.6
markupsafe-3.0.3 mpmath-1.3.0 numpy-2.2.0 onnxruntime-1.20.1
opencv-python-4.13.0.92 protobuf-7.35.1 python-telegram-bot-21.11.1 pyyaml-6.0.2
sympy-1.14.0 typing_extensions-4.16.0 werkzeug-3.1.8
```

và vòng lặp đối chiếu `pip freeze` với từng dòng `requirements.txt` **không in ra dòng lệch nào**.

→ Điều kiện §2b **không kích hoạt**, đúng như thiết kế. Cảnh báo *"phiên bản pin từ Windows x86-64,
sẽ kiểm chứng lại ở P0-03"* ghi ở đầu hai file requirements **nay đã được giải toả**. Câu dùng được
cho báo cáo: *"Các phiên bản thư viện được pin cứng trên môi trường phát triển Windows x86-64 đã
được kiểm chứng lại trên container ARM64/Python 3.11 và cài đặt thành công mà không cần điều chỉnh."*

---

## 5. Hai điểm sống còn — soi lại ở vòng 2

- **Trung thực số liệu (R5)**: không có số bịa. Mọi con số ở §4 đều do người review tự đo, không chép
  theo báo cáo của Gemini. Đã chủ động chặn trước **hai cái bẫy** sẽ dẫn tới số sai trong Chương 3:
  (1) nhầm `disk usage` 1,05 GB với `content size` 252 MB — xem §4.1; (2) dùng thời gian `pytest`
  trong container giả lập làm số đo hiệu năng — xem cảnh báo cuối §3. Bản thân lỗi vòng 1 cũng thuộc
  nhóm này: một image sai kiến trúc sẽ âm thầm sinh ra số FPS sai.
- **An toàn phần cứng**: không áp dụng (không sinh mã Python, không đụng GPIO/relay/camera). Đã xác
  nhận lại `docker-compose.yml` **không** khai báo `devices:`, đúng §3.3 và §8.

---

## 6. Nhận xét bổ sung về đặc tả (gửi `spec-writer`) — phát hiện mới ở vòng 2

Vòng 1 đã ghi 5 nhận xét. Vòng 2 bổ sung một phát hiện **quan trọng hơn cả năm nhận xét kia**:

6. **Đặc tả §3.1 đưa ra hai phương án như thể tương đương, nhưng một trong hai KHÔNG giải quyết được
   vấn đề.** Nguyên văn: *"Khai báo `--platform=$TARGETPLATFORM` hoặc cố định `linux/arm64`"*. Thực
   nghiệm ở §2.2 cho thấy `$TARGETPLATFORM` mặc định bằng nền tảng máy build → build không kèm cờ vẫn
   ra **amd64**, tức lỗi vòng 1 vẫn còn. Gemini chọn đúng vế thứ hai, nhưng đó là **may, không phải
   do đặc tả dẫn dắt**.
   → Bài học: khi đặc tả viết chữ "**hoặc**", người viết đặc tả có nghĩa vụ đã **tự kiểm chứng cả hai
   nhánh**. Nếu chưa kiểm được thì chốt một phương án duy nhất, đừng đẩy lựa chọn sang người viết
   code — họ không có ngữ cảnh để biết nhánh nào an toàn.
   Với mã việc này, câu đúng phải là: *"Dòng `FROM` **bắt buộc** ghi `--platform=linux/arm64` (giá
   trị hằng). Không dùng `$TARGETPLATFORM` vì biến này mặc định bằng nền tảng máy build."*

Nhắc lại nhận xét số 4 của vòng 1 vì vòng 2 đã chứng minh nó bằng số liệu: **mỗi mục bắt buộc ở §3
phải có ít nhất một dòng ở §5 kiểm được nó khi KHÔNG có cờ dòng lệnh trợ giúp.** Bảng §5 vòng 1 có
13 dòng, đạt 13/13, mà vẫn để lọt lỗi — vì mọi lệnh kiểm đều "giúp" Dockerfile bằng cách tự truyền
`--platform`. Dòng cần thêm vào §5:

| Điều kiện | Kỳ vọng | Assert / lệnh kiểm |
|---|---|---|
| Dockerfile tự bảo đảm kiến trúc | Không phụ thuộc người gõ lệnh | `docker build -f deploy/Dockerfile.arm64 -t faceid:chk .` (**không** `--platform`) rồi `docker image inspect faceid:chk --format "{{.Architecture}}"` trả `arm64` |

---

## 7. Việc tiếp theo

**Không còn việc cho Gemini.** Mã việc ĐẠT, đủ điều kiện commit và gộp vào `dev`.

### 7.1. Commit đề xuất (R29)

Ba file đang ở trạng thái `A`/`AM`, cần `git add` lại `deploy/Dockerfile.arm64` để đưa phần sửa
vòng 2 vào vùng stage:

```bash
git add deploy/Dockerfile.arm64
git commit -m "feat(deploy): moi truong gia lap ARM64 bang Docker (P0-03-docker-arm64)"
```

Biên bản review commit riêng theo thông lệ:

```bash
git add docs/review/P0-03-docker-arm64.review.md
git commit -m "docs(review): bien ban P0-03-docker-arm64 — 2 vong, phan quyet DAT"
```

> Lưu ý khi gộp: nhánh `feat/p0-03-docker-arm64` đang **đứng sau `dev` 9 commit**. Nên `git rebase dev`
> (hoặc merge `dev` vào trước) rồi mới gộp ngược lại, để biên bản review không nằm lệch dòng thời gian.

### 7.2. Dọn image tạm

Người review đã tự xoá hai image mình tạo ra để kiểm chứng ở vòng 2: `faceid:reviewv2`,
`tgtplat:noflag` (và ở vòng 1: `faceid:coldbuild`, `platformtest:noflag`).

Còn lại hai image, **cần dọn `faceid:arm64check`**:

```bash
docker rmi faceid:arm64check      # image tạm của lượt sửa vòng 2, không còn dùng
```

`faceid:arm64` giữ lại làm image làm việc. Image này được build từ **Dockerfile bản cũ** (trước khi
sửa dòng 1) nên nên build lại một lần cho khớp mã nguồn sẽ commit — nội dung không đổi, nhưng để
image và Dockerfile là một:

```bash
docker build -f deploy/Dockerfile.arm64 -t faceid:arm64 .
```

### 7.3. Trạng thái Phase 0 sau mã việc này

Bước 0.3 **hoàn tất**. Phase 0 chỉ còn **bước 0.4 (Pi 5 thật)** đang bị chặn vì chưa có phần cứng —
đúng tình huống R36. Cổng C của Phase 0 (`import cv2, onnxruntime` chạy được trong container ARM64)
đã **đạt**; phần còn lại của Cổng C ("Pi 5 mở được camera") phải chờ thiết bị.
