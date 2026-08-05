# Review P0-02-dependency — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P0-02-dependency.md` |
| **Nhánh** | `feat/p0-02-dependency` |
| **Worktree** | `D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/wt-p0-02-dependency` |
| **Ngày** | 2026-08-05 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — 1 lỗi CHẶN-A |

---

## 1. Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short` | **4 file** — thừa `versions.txt` ngoài danh sách trắng ❌ |
| `git diff --stat` | rỗng (không sửa file đã theo dõi) ✅ |
| `git status --short \| grep -Ei '\.(jpg\|png\|npy\|onnx\|pt\|env\|db)$'` | rỗng ✅ |
| `black --check --line-length 100 src tests` | `7 files would be left unchanged` ✅ |
| `ruff check src tests` | `All checks passed!` ✅ |
| `pytest -q` | `26 passed in 0.42s` ✅ (không phá `P0-01`) |
| `pip install -r requirements-dev.txt` | thoát mã **0** ✅ |

Nội dung `git status --short`:

```
?? .env.example
?? requirements-dev.txt
?? requirements.txt
?? versions.txt        ← NGOÀI DANH SÁCH TRẮNG §2
```

---

## 2. Bảng §5 — chạy từng lệnh, kết quả thật

| # | Điều kiện | Lệnh kiểm | Kỳ vọng | Kết quả thật | |
|---|---|---|---|---|---|
| 1 | Pin cứng toàn bộ | `grep -E "^[a-zA-Z]" requirements.txt \| grep -v "=="` | rỗng | rỗng (exit 1) | ✅ |
| 2 | Đúng 6 gói runtime | `grep -cE "^[a-zA-Z].*==" requirements.txt` | `6` | `6` | ✅ |
| 3 | Không có torch/ultralytics | `grep -iE "torch\|ultralytics" requirements.txt` | rỗng | rỗng (exit 1) | ✅ |
| 4 | Dòng đầu `requirements-dev.txt` | `head -1 requirements-dev.txt` | `-r requirements.txt` | `# File này dùng cho Python >= 3.11` — chuỗi `-r requirements.txt` nằm ở **dòng 8** | ⚠️ xem §4 |
| 5 | Đúng 4 gói dev | `grep -cE "^[a-zA-Z].*==" requirements-dev.txt` | `4` | `4` | ✅ |
| 6 | Không có secret thật | `grep -iE "[0-9]{8,}:[A-Za-z0-9_-]{30,}" .env.example` | rỗng | rỗng (exit 1) | ✅ |
| 7 | Đủ 4 biến môi trường | `grep -cE "^[A-Z_]+=" .env.example` | `4` | `4` | ✅ |
| 8 | Cài lại được, không xung đột | `pip install -r requirements-dev.txt` | exit 0 | exit **0** | ✅ |
| 9 | Không phá `P0-01` | `pytest -q` | 26 passed | **26 passed** | ✅ |

**8/9 đạt.** Dòng 4 không đạt theo chữ, nhưng nguyên nhân là **đặc tả tự mâu thuẫn** — xem §4,
không tính là lỗi của bên cài đặt.

---

## 3. Kiểm số phiên bản có thật hay bịa (§3.4 — rủi ro chính của mã việc)

Đối chiếu **từng dòng** hai file requirements với `python -m pip freeze` chạy thật trong môi trường
(Python 3.12.5, Windows x86-64):

| Gói | Ghi trong file | `pip freeze` trả về | Khớp |
|---|---|---|---|
| `onnxruntime` | `1.20.1` | `onnxruntime==1.20.1` | ✅ |
| `opencv-python` | `4.13.0.92` | `opencv-python==4.13.0.92` | ✅ |
| `numpy` | `2.2.0` | `numpy==2.2.0` | ✅ |
| `pyyaml` | `6.0.2` | `PyYAML==6.0.2` | ✅ (tên chuẩn hoá, pip không phân biệt hoa thường) |
| `flask` | `3.1.3` | `Flask==3.1.3` | ✅ |
| `python-telegram-bot` | `21.11.1` | `python-telegram-bot==21.11.1` | ✅ |
| `ultralytics` | `8.4.39` | `ultralytics==8.4.39` | ✅ |
| `pytest` | `9.1.1` | `pytest==9.1.1` | ✅ |
| `black` | `24.4.2` | `black==24.4.2` | ✅ |
| `ruff` | `0.16.1` | `ruff==0.16.1` | ✅ |

**Kết luận: 10/10 phiên bản khớp tuyệt đối với môi trường thật. Không có số bịa.**
Không phát hiện vi phạm CA-7. Đây là điểm quan trọng nhất của mã việc và nó đạt.

---

## 4. Đối chiếu các mục còn lại của đặc tả

| Mục | Kết luận |
|---|---|
| §2 Danh sách trắng | ❌ thừa `versions.txt` — **CHẶN-A-1** |
| §3.2 Đúng 6 gói runtime, không `-headless` | ✅ đủ 6, đúng tên, `opencv-python` bản đầy đủ |
| §3.3 Đúng 4 gói dev + dòng tham chiếu | ✅ đủ 4, có `-r requirements.txt` |
| §3.4 Phiên bản lấy từ `pip freeze` | ✅ khớp 10/10 |
| §3.5 Khối chú thích đầu file | ✅ cả hai file, đủ 4 ý (Python ≥ 3.11 · nền tảng pin = Windows x86-64 · cảnh báo ARM64 Linux + hoãn sang `P0-03` · lệnh cài) |
| §3.6 `.env.example` | ✅ đủ 4 biến, giá trị rỗng, mỗi biến có chú thích tiếng Việt, có dòng nhắc cuối file |
| §4 Tham số → config | không áp dụng |
| §5 Ca biên | 8/9 (xem §2) |
| §6 Nghiệm thu | 5/6 — trượt mục "không có file ngoài danh sách trắng" |
| §7 G8 (`torch` không vào runtime) | ✅ |
| §7 G10 (không token thật) | ✅ |
| §8 Ngoài phạm vi | ✅ không tạo `models/README.md`, không sửa `pyproject.toml`, không đụng `src/`, `tests/`, `deploy/`, không thêm gói ngoài 10 gói |

---

## 5. Lỗi phải sửa

### 🔴 CHẶN-A-1 — File `versions.txt` ngoài danh sách trắng, sẽ lọt vào git (CA-5)

**Vị trí**: `versions.txt` (toàn bộ file, 318 dòng, 12 352 byte, mã hoá UTF-16 LE có BOM `ff fe`)

```
?? versions.txt          ← git status: untracked, KHÔNG bị .gitignore chặn
```

Trích dòng 1 và các dòng đáng chú ý (đã bỏ ký tự NUL của UTF-16):

```
absl-py==2.3.1
...
tensorflow==2.21.0
torch==2.5.1
torchvision==0.20.1
transformers==4.55.1
```

**Xác minh**: `git check-ignore -v versions.txt` → exit 1, tức là **không có luật `.gitignore` nào
chặn file này**. Chỉ cần một lệnh `git add .` là nó vào lịch sử repo vĩnh viễn.

**Vì sao**: ba hậu quả cụ thể, xếp theo mức nghiêm trọng.

1. **Đây là ảnh chụp toàn bộ site-packages của máy cá nhân**, không phải của dự án — chứa
   `tensorflow`, `jupyterlab`, `selenium`, `gspread`, `kaggle`, `google-genai`, `mysql-connector-python`…
   Nó tiết lộ môi trường làm việc riêng của sinh viên và không liên quan gì tới đồ án.
2. **Nó chứa `torch==2.5.1` và `ultralytics==8.4.39` ở cùng thư mục gốc với `requirements.txt`.**
   Toàn bộ lý do tồn tại của mã việc này là tách `torch` ra khỏi đường cài của Pi 5 (§3.1, G8).
   Một file tên `versions.txt` nằm cạnh `requirements.txt` là **cái bẫy**: người dựng lại hệ thống
   ở Phase 8 rất dễ tưởng đây là bản pin đầy đủ và chạy `pip install -r versions.txt` trên Pi,
   kéo về 2 GB `torch` + `tensorflow` — đúng thứ mà cả mã việc này cố tránh.
3. **Mã hoá UTF-16 LE với BOM** xác nhận đây là file trung gian sinh bởi
   `pip freeze > versions.txt` trong PowerShell. Nó là **giàn giáo**, đã hoàn thành nhiệm vụ khi
   10 phiên bản được chép sang hai file requirements. Giàn giáo không đi kèm công trình.

**Sửa**: xoá file, không tạo lại.

```bash
rm "versions.txt"
```

Kiểm lại phải thấy đúng 3 file:

```bash
git status --short
# ?? .env.example
# ?? requirements-dev.txt
# ?? requirements.txt
```

**Không** thêm `versions.txt` vào `.gitignore` để "cho qua" — `.gitignore` nằm ngoài danh sách
trắng §2, sửa nó là thêm một vi phạm CA-5 nữa. Lần sau cần `pip freeze`, ghi ra thư mục tạm ngoài
repo, ví dụ `%TEMP%\versions.txt`.

---

## 6. Lỗi của ĐẶC TẢ, không phải của bên cài đặt — cần `spec-writer` xử lý

### ⚠️ Mâu thuẫn nội tại giữa §3.3/§5-dòng-4 và §3.5

Hai yêu cầu **không thể cùng thoả**:

| Mục | Yêu cầu |
|---|---|
| §3.3 dòng 62 | *"Dòng đầu tiên **bắt buộc** là `-r requirements.txt`"* |
| §5 dòng 123 | *"Dòng đầu tiên đúng bằng `-r requirements.txt`"* |
| §3.5 dòng 84 | *"**Cả hai file** requirements phải **mở đầu** bằng khối chú thích…"* |

Bên cài đặt đã chọn cách giải quyết hợp lý: khối chú thích ở dòng 1–7, `-r requirements.txt` ở
dòng 8 — vị trí đầu tiên trong phần nội dung thực thi. Cách này **đúng về mặt kỹ thuật**:
`pip install -r requirements-dev.txt` thoát mã 0, và log pip xác nhận đã kéo đúng
`requirements.txt` (`… ->-r D:\...\requirements.txt (line 8)`). `pip` không quan tâm `-r` nằm ở
dòng nào.

**Vì vậy đây không phải lỗi trả lại.** Theo `code-review.instructions.md` §5, thiết kế đã chốt
trong đặc tả không phải việc của bên cài đặt sửa.

**Đề xuất sửa đặc tả** (dành cho `spec-writer`, không dành cho vòng 2 của mã việc này):

- §3.3 → *"Sau khối chú thích §3.5, dòng nội dung đầu tiên bắt buộc là `-r requirements.txt`."*
- §5 dòng 4 → đổi lệnh kiểm thành lệnh chạy được, thay vì mô tả bằng lời:
  ```bash
  grep -vE '^\s*(#|$)' requirements-dev.txt | head -1
  # kỳ vọng: -r requirements.txt
  ```

---

## 7. 🔵 Góp ý (không chặn — người dùng quyết định)

1. **Nguồn của các phiên bản là site-packages toàn cục dùng chung.**
   `pip freeze` chạy trong môi trường chứa `tensorflow`, `jupyterlab`, `insightface`, `mediapipe`…
   Nghĩa là `numpy==2.2.0` là con số **đã bị các dự án khác ghim sẵn**, không phải kết quả `pip`
   giải phụ thuộc riêng cho đồ án này. `pip install` vẫn thoát mã 0 nên hiện chưa có xung đột.
   Chi phí để làm sạch: tạo venv trống, cài 10 gói, `pip freeze` lại (~10 phút, tải ~2,5 GB).
   Lợi ích: số pin phản ánh đúng nhu cầu của dự án. **Đề xuất gộp vào `P0-03`** khi dựng container
   ARM64 — lúc đó dù sao cũng phải giải lại phụ thuộc từ đầu trên nền tảng khác, làm hai lần là phí.

2. **`FACEID_LOG_LEVEL=` để trống trong khi §3.6 ghi "mặc định `INFO`".**
   Đúng đặc tả (§3.6 cho phép "giá trị mẫu rỗng"), và `src/common/logging.py` của `P0-01` đã có
   giá trị mặc định. Nhưng viết `FACEID_LOG_LEVEL=INFO` sẽ tự tài liệu hoá tốt hơn cho người
   dựng lại hệ thống ở Phase 8. Chi phí: 1 ký tự. Không đáng mở một vòng review.

3. **Chưa có gì neo phiên bản Python.** File chỉ ghi "Python >= 3.11" trong chú thích, còn môi
   trường pin thực tế là **3.12.5**. Ràng buộc này chỉ được kiểm bằng mắt. Có thể cân nhắc đưa
   `requires-python` vào `pyproject.toml` ở một mã việc sau — nhưng `pyproject.toml` nằm ngoài
   phạm vi mã việc này (§8), nên chỉ ghi nhận.

---

## 8. Hai điểm sống còn — soi riêng

| Điểm | Kết luận |
|---|---|
| **Trung thực số liệu** (R5 / CA-7) | ✅ **Sạch.** 10/10 phiên bản đối chiếu trực tiếp với `pip freeze` thật, không có số phỏng đoán. Khối chú thích còn chủ động ghi rõ đây là "bản nháp đầu tiên" chờ kiểm chứng ở `P0-03` — đúng tinh thần R5, không tuyên bố mạnh hơn bằng chứng đang có. |
| **An toàn phần cứng** | Không áp dụng — mã việc không sinh mã điều khiển thiết bị. |
| **Rò rỉ secret** (R25 / R26 / G10) | ✅ `.env.example` chỉ có tên biến và giá trị rỗng. `.gitignore:255-257` chặn `.env`, `.env.*` nhưng mở ngoại lệ `!.env.example` — đúng ý đồ. Không có file `.env`/`.jpg`/`.onnx`/`.db` nào trong `git status`. |

---

## 9. Việc tiếp theo

Đúng **một** thao tác, không đụng gì khác:

```bash
cd "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/wt-p0-02-dependency"
rm versions.txt
git status --short     # phải thấy đúng 3 dòng
```

Sau đó review vòng 2 (dự kiến rất ngắn — chỉ xác nhận lại phạm vi file, phần nội dung đã đạt toàn bộ).

Khi ĐẠT, commit gợi ý:

```
chore(deps): tach requirements runtime va dev, pin cung phien ban — P0-02-dependency
```

**Không commit `versions.txt`.**

---
---

# Review P0-02-dependency — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P0-02-dependency.md` — **bản đã sửa sau vòng 1**, đọc tại repo chính `UIT-AI503.F3.LT.TTNT/docs/dac-ta/` (bản trong worktree đã lỗi thời) |
| **Nhánh** | `feat/p0-02-dependency` |
| **Worktree** | `D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/wt-p0-02-dependency` |
| **Ngày** | 2026-08-05 |
| **Phán quyết** | ✅ **ĐẠT** — hết 🔴 và 🟡, 11/11 dòng bảng §5 xanh |

---

## 1. Xác minh lỗi CHẶN-A-1 của vòng 1 đã được sửa

Yêu cầu vòng 1 gồm **hai vế**, kiểm riêng từng vế:

| Vế | Lệnh | Kết quả | |
|---|---|---|---|
| `versions.txt` không còn | `ls -la versions.txt` | `No such file or directory` | ✅ |
| **Không** lách bằng cách thêm vào `.gitignore` | `git diff --stat .gitignore` | rỗng — file không bị sửa | ✅ |
| — (kiểm chéo) | `grep -n "versions" .gitignore` | không khớp (exit 1) | ✅ |

Đây là điểm cần soi kỹ nhất của vòng 2: cách sửa "rẻ tiền" là thêm một dòng `versions.txt` vào
`.gitignore` để `git status` sạch mà vẫn giữ file. Cách đó sẽ **là một vi phạm CA-5 mới** vì
`.gitignore` nằm ngoài danh sách trắng §2. **Bên cài đặt đã không làm vậy** — file bị xoá thật,
`.gitignore` nguyên vẹn. Sửa đúng bản chất, không sửa triệu chứng.

Kiểm thêm bằng `--untracked-files=all` (soi cả file ẩn trong thư mục con), vẫn đúng 3 file:

```
?? .env.example
?? requirements-dev.txt
?? requirements.txt
```

---

## 2. Bảng §5 bản mới — **11 dòng**, chạy từng lệnh

| # | Điều kiện | Kỳ vọng | Kết quả thật | |
|---|---|---|---|---|
| 1 | **[MỚI]** Không có file ngoài danh sách trắng | `3` | `3` | ✅ |
| 2 | **[MỚI]** Mọi phiên bản lấy từ môi trường thật | không in gì | không in gì | ✅ |
| 3 | Mọi dòng gói `requirements.txt` pin cứng | rỗng | rỗng (exit 1) | ✅ |
| 4 | `requirements.txt` đúng 6 gói | `6` | `6` | ✅ |
| 5 | `requirements.txt` không chứa torch/ultralytics | rỗng | rỗng (exit 1) | ✅ |
| 6 | **[SỬA]** Dòng lệnh đầu `requirements-dev.txt` | `-r requirements.txt` | `-r requirements.txt` | ✅ |
| 7 | `requirements-dev.txt` đúng 4 gói | `4` | `4` | ✅ |
| 8 | `.env.example` không chứa secret thật | rỗng | rỗng (exit 1) | ✅ |
| 9 | `.env.example` đủ 4 biến | `4` | `4` | ✅ |
| 10 | Cài lại từ file sạch được | exit 0 | exit **0** | ✅ |
| 11 | Mã nguồn hiện có vẫn chạy | 26 passed | **26 passed** | ✅ |

**11/11 đạt.**

### Ghi chú cách kiểm dòng 1 — loại trừ `docs/review/`

Lệnh nguyên văn của đặc tả là `git status --short | wc -l` trả `3`. Chạy trần sẽ ra `4`, vì trong
worktree có thêm `docs/review/P0-02-dependency.review.md` — **chính biên bản này**, do người review
ghi ở vòng 1. Theo `CLAUDE.md` §2.9, `docs/review/` là vùng ghi của vai `code-reviewer`, không phải
của bên cài đặt, nên nó **không tính là vi phạm danh sách trắng**.

Cách loại trừ đã dùng, ghi lại để tái lập được:

```bash
git status --short | grep -v "docs/review/" | wc -l
# → 3
```

Danh sách sau khi loại trừ đúng bằng 3 file của §2, không thừa không thiếu.

> ⚠️ Đây là **khiếm khuyết của lệnh kiểm**, không phải của code — xem góp ý §5.1.

### Ghi chú dòng 6 — mâu thuẫn đặc tả vòng 1 đã được gỡ

Vòng 1 đây là dòng duy nhất trượt, do §3.3 và §3.5 đòi hai thứ loại trừ nhau. Bản đặc tả mới §3.3
đã định nghĩa lại là **"dòng lệnh đầu tiên"** (dòng đầu không phải chú thích, không rỗng) và đổi ô
kiểm sang lệnh chạy được:

```bash
grep -vE "^\s*(#|$)" requirements-dev.txt | head -1
# → -r requirements.txt
```

File **không bị sửa** giữa hai vòng — `-r requirements.txt` vẫn ở `requirements-dev.txt:8`, ngay
sau khối chú thích 7 dòng. Cách cài đặt vốn đã đúng; thứ được sửa là đặc tả. Xác nhận lại nhận định
vòng 1: đây là lỗi `spec-writer`, không phải lỗi bên cài đặt.

---

## 3. Kiểm hồi quy — không phá `P0-01`

| Lệnh | Kết quả | |
|---|---|---|
| `pytest -q` | `26 passed in 0.56s` | ✅ |
| `black --check --line-length 100 src tests` | `7 files would be left unchanged` | ✅ |
| `ruff check src tests` | `All checks passed!` | ✅ |
| `pip install -r requirements-dev.txt` | exit `0` | ✅ |

Đủ 26 ca test của `P0-01` vẫn xanh. `git diff --stat` rỗng — không file nào đã theo dõi bị đụng vào.

---

## 4. Kiểm lại số phiên bản bịa (lần hai)

Bên cài đặt **không sửa** hai file requirements ở vòng này (thao tác duy nhất là xoá `versions.txt`),
nhưng vẫn đối chiếu lại toàn bộ để chắc chắn — đây là rủi ro chính của mã việc nên không tin vào
"chắc là không đổi".

Lệnh ở dòng §5-2 đối chiếu **tự động** từng dòng `ten==phienban` của cả hai file với `pip freeze`
(so khớp chính xác, không phân biệt hoa thường bằng `grep -qix`):

```bash
for p in $(grep -hoE "^[a-zA-Z0-9_-]+==[^ ]+" requirements*.txt); do
  pip freeze | grep -qix "$p" || echo "KHONG KHOP: $p"
done
# → không in gì
```

Không dòng `KHONG KHOP` nào. Đối chiếu tay lần nữa cho đủ 10 gói:

| Gói | File | `pip freeze` | |
|---|---|---|---|
| `onnxruntime` | `1.20.1` | `1.20.1` | ✅ |
| `opencv-python` | `4.13.0.92` | `4.13.0.92` | ✅ |
| `numpy` | `2.2.0` | `2.2.0` | ✅ |
| `pyyaml` | `6.0.2` | `PyYAML==6.0.2` | ✅ |
| `flask` | `3.1.3` | `Flask==3.1.3` | ✅ |
| `python-telegram-bot` | `21.11.1` | `21.11.1` | ✅ |
| `ultralytics` | `8.4.39` | `8.4.39` | ✅ |
| `pytest` | `9.1.1` | `9.1.1` | ✅ |
| `black` | `24.4.2` | `24.4.2` | ✅ |
| `ruff` | `0.16.1` | `0.16.1` | ✅ |

**10/10 khớp. Không có số bịa (R5 / CA-7 sạch).**

---

## 5. 🔵 Góp ý

### 5.1. Lệnh kiểm phạm vi file (§5 dòng 1) sẽ báo động giả ở mọi mã việc sau

`git status --short | wc -l` trả `3` chỉ đúng khi **chưa có biên bản review**. Nhưng biên bản
luôn được ghi vào worktree trước khi phán quyết, nên từ vòng 2 trở đi lệnh này **luôn lệch 1**.
Mã việc sau sẽ gặp lại đúng chuyện này.

Đề xuất `spec-writer` đổi ô kiểm thành dạng miễn nhiễm, dùng được cho mọi mã việc:

```bash
git status --short | grep -v "^?? docs/review/" | wc -l
```

Chi phí: sửa một ô trong mẫu đặc tả. Lợi ích: người review không phải giải thích thủ công cách
loại trừ ở từng biên bản, và không có nguy cơ ai đó nhìn số `4` rồi kết luận nhầm là vi phạm.

### 5.2. Ba góp ý của vòng 1 — giữ nguyên, không cái nào chặn

| # | Nội dung | Đề xuất xử lý |
|---|---|---|
| 1 | Phiên bản pin từ site-packages toàn cục dùng chung, không phải venv sạch của dự án | **Gộp vào `P0-03`** — khi dựng container ARM64 phải giải lại phụ thuộc từ đầu, làm hai lần là phí |
| 2 | `FACEID_LOG_LEVEL=` để trống thay vì `INFO` | Đúng đặc tả §3.6. Không đáng mở vòng review. Sửa kèm khi nào động vào file vì lý do khác |
| 3 | Chưa có `requires-python` neo Python ≥ 3.11 bằng máy | `pyproject.toml` ngoài phạm vi §8. Ghi nhận cho mã việc sau |

---

## 6. Hai điểm sống còn — soi lại

| Điểm | Kết luận |
|---|---|
| **Trung thực số liệu** (R5 / CA-7) | ✅ Sạch. 10/10 phiên bản khớp `pip freeze` thật, kiểm cả bằng lệnh tự động lẫn đối chiếu tay. Khối chú thích tự khai báo đây là "bản nháp đầu tiên" chờ kiểm chứng ở `P0-03` — không tuyên bố mạnh hơn bằng chứng. |
| **An toàn phần cứng** | Không áp dụng — mã việc không sinh mã điều khiển thiết bị. |
| **Rò rỉ secret** (R25 / R26 / G10) | ✅ `.env.example` chỉ có tên biến, giá trị rỗng, không token thật. `.gitignore` chặn `.env`, `.env.*`, mở ngoại lệ `!.env.example`. Không file `.env`/`.jpg`/`.onnx`/`.db` nào trong `git status`. **`versions.txt` — thứ duy nhất từng làm lộ môi trường máy cá nhân — đã bị xoá.** |

---

## 7. Đối chiếu tiêu chí nghiệm thu §6

| Tiêu chí | |
|---|---|
| Mỗi dòng bảng §5 có lệnh kiểm đã chạy, kết quả đúng — dán vào báo cáo | ✅ 11/11, kết quả ở §2 |
| `pip install -r requirements-dev.txt` chạy sạch | ✅ exit 0 |
| `pytest -q` vẫn 26 passed | ✅ |
| `black --check` và `ruff check` vẫn sạch | ✅ |
| Cả hai file requirements có khối chú thích §3.5, nêu rõ nền tảng pin | ✅ đủ 4 ý, ghi rõ Windows x86-64 |
| `git status --short` không có file ngoài danh sách trắng §2 | ✅ đúng 3 file (loại trừ `docs/review/`, xem §2) |

**6/6 tiêu chí thoả.**

---

## 8. Việc tiếp theo

**Đã ĐẠT — được commit.** Commit đúng 3 file, tuyệt đối không `git add .` (sẽ kéo theo biên bản
review — file này thuộc vai `code-reviewer`, commit riêng):

```bash
cd "D:/hoc tap/lop CNTT dai hoc/ky 4/DO AN/wt-p0-02-dependency"
git add requirements.txt requirements-dev.txt .env.example
git commit -m "chore(deps): tach requirements runtime va dev, pin cung phien ban — P0-02-dependency"
```

Sau đó gộp `feat/p0-02-dependency` vào `dev`, rồi chuyển sang mã việc `P0-03`
(`deploy/Dockerfile.arm64` + `docker-compose.yml`).

**Mang sang `P0-03`**: kiểm chứng lại 6 phiên bản runtime trên nền ARM64 Linux — khối chú thích của
cả hai file đã hẹn sẵn việc này, và góp ý §5.2-1 (dựng venv sạch) nên làm luôn ở đó.
