---
applyTo: "src/**/*.py, tests/**/*.py, scripts/**/*.py, docs/review/**"
description: Chuẩn review mã nguồn — lệnh kiểm bắt buộc, danh sách mẫu vi phạm quét được bằng grep, thang phân loại lỗi 4 mức và cách viết một mục lỗi. Áp dụng cho mọi lượt review code do Gemini sinh ra.
---

# Instructions: Chuẩn review mã nguồn

Áp dụng cho mọi lượt review trong quy trình 5 nhịp (xem `CLAUDE.md` §2.9).
Nguyên tắc bao trùm: **máy kiểm trước, người đọc sau**. Con người chỉ nên tốn sức vào thứ máy không bắt được.

---

## 1. Ba lệnh kiểm bắt buộc

```bash
black --check --line-length 100 src tests
ruff check src tests
pytest -q
```

Không chạy đủ ba lệnh → **biên bản review không hợp lệ**. Không được suy đoán kết quả.

Kèm theo, luôn kiểm phạm vi thay đổi:

```bash
git status --short
git diff --stat
```

---

## 2. Quét mẫu vi phạm — chạy trước khi đọc code

| Vi phạm | Lệnh quét | Mức |
|---|---|---|
| `print()` trong `src/` | `Grep "\bprint\(" --glob "src/**/*.py"` | 🔴 CHẶN-A |
| `except:` trần / nuốt lỗi | `Grep "except\s*:" hoặc "except Exception:\s*pass"` | 🔴 CHẶN-B |
| Import phần cứng ở đầu file | `Grep "^import RPi\|^import pigpio\|^from RPi" --glob "src/**/*.py"` | 🔴 CHẶN-A |
| `import torch` | `Grep "import torch"` | 🔴 CHẶN-A |
| Log dùng f-string | `Grep "logger\.\w+\(f\""` | 🟡 CẦN SỬA |
| Số magic (float trần trong so sánh) | `Grep "[<>]=?\s*0\.\d"` — rà thủ công kết quả | 🔴 CHẶN-A nếu là tham số thực nghiệm |
| Đường dẫn tuyệt đối máy cá nhân | `Grep "[A-Z]:\\\\\|/home/\|/Users/"` | 🔴 CHẶN-A |
| Secret trong code | `Grep -i "token\s*=\s*[\"']\|api_key\s*=\s*[\"']\|password\s*=\s*[\"']"` | 🔴 CHẶN-A |
| Test giả | `Grep "assert True\|^\s*pass$" --glob "tests/**/*.py"` | 🔴 CHẶN-B |
| Nạp model trong vòng lặp | `Grep -B5 "InferenceSession\|cv2.dnn.read"` — kiểm xem có nằm trong `for`/`while` | 🔴 CHẶN-B |
| File cấm lọt git | `git status --short \| grep -Ei '\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$'` | 🔴 CHẶN-A |

> Lưu ý về **số magic**: không phải mọi số trong code đều là vi phạm.
> `112` cho kích thước ảnh align, `0` `1` `2` cho chỉ số mảng là bình thường.
> Vi phạm là khi **giá trị đó ảnh hưởng đến kết quả thực nghiệm** (ngưỡng, conf, IoU, số frame xác nhận,
> cooldown) — những thứ sẽ phải đổi khi đo lại và phải ghi được vào báo cáo.

---

## 3. Thang phân loại 4 mức

### 🔴 CHẶN-A — Vi phạm quy tắc cứng của dự án

Trả lại ngay, không cần xét thêm. Đây là những thứ làm hỏng **tính khoa học** hoặc **tính pháp lý**
của đồ án, không phải chuyện thẩm mỹ.

| Mã | Vi phạm | Quy tắc |
|---|---|---|
| CA-1 | Hardcode tham số thực nghiệm thay vì đọc `configs/` | G1 / R16 |
| CA-2 | `print()` trong `src/` | G2 / R23 |
| CA-3 | Truy cập phần cứng không qua interface có backend `mock` | G7 / R22 |
| CA-4 | Ảnh khuôn mặt, `.npy/.npz`, model weights, `.env`, token lọt vào git | R25 / R26 |
| CA-5 | Sửa file **ngoài DANH SÁCH TRẮNG** của đặc tả | quy trình |
| CA-6 | Làm việc **ngoài phạm vi đề cương** (huấn luyện lại model, nhận diện đám đông, MQTT/ReactJS sớm) | R10–R14 |
| CA-7 | Số liệu bịa: giá trị mặc định giả trông như kết quả đo, số ví dụ trong docstring dễ bị chép vào báo cáo | R5 |
| CA-8 | Gửi dữ liệu khuôn mặt ra API/cloud ngoài | R27 |
| CA-9 | `import torch` hoặc thư viện nặng khác trên đường chạy của Pi | G8 |

### 🔴 CHẶN-B — Sai tính đúng đắn hoặc mất an toàn

| Mã | Vi phạm |
|---|---|
| CB-1 | Logic sai so với bảng ca biên §5 của đặc tả |
| CB-2 | **Không fail-safe**: lỗi phần cứng làm sập hệ thống, hoặc relay/LED không được đưa về trạng thái tắt |
| CB-3 | Rò rỉ tài nguyên: camera/file/GPIO không đóng, thiếu `try/finally` hay context manager |
| CB-4 | `except:` trần hoặc nuốt lỗi im lặng |
| CB-5 | Nạp model / cấp phát lớn bên trong vòng lặp xử lý frame |
| CB-6 | Test giả (không assert, `assert True`), hoặc test được sửa để đi qua thay vì sửa code |
| CB-7 | Tranh chấp dữ liệu giữa thread capture và thread xử lý (thiếu queue/khoá) |

### 🟡 CẦN SỬA — Phải sửa trước khi commit, nhưng không nguy hiểm

| Mã | Vi phạm |
|---|---|
| CS-1 | Thiếu type hints hoặc docstring tiếng Việt ở hàm public |
| CS-2 | Import chéo sai tầng kiến trúc (`detector` gọi `actuator`…) |
| CS-3 | Định nghĩa lại kiểu dữ liệu đã có trong `src/common/types.py` |
| CS-4 | Thiếu ca test mà bảng §5 đặc tả đã liệt kê |
| CS-5 | Log dùng f-string thay vì lazy formatting |
| CS-6 | Log sai mức (lỗi phần cứng ghi ở `INFO`, người lạ không ghi `WARNING`) |
| CS-7 | Log dữ liệu nhạy cảm (embedding thô, đường dẫn ảnh khuôn mặt ở mức `INFO`) |
| CS-8 | Thiếu tham số CLI bắt buộc của script (`--config`, `--dry-run`, `--seed`) |
| CS-9 | Thêm dependency không có trong đặc tả |

### 🔵 GÓP Ý — Ghi nhận, không chặn

Hiệu năng có thể cải thiện, đặt tên chưa hay, cấu trúc có phương án gọn hơn, ý tưởng cho Phase sau.
**Người dùng quyết định**, không tự chuyển thành yêu cầu sửa.

---

## 4. Cách viết một mục lỗi

Bốn thành phần, thiếu một là mục lỗi không dùng được:

```markdown
### 🔴 CHẶN-A-1 — <nhãn ngắn> (vi phạm <mã quy tắc>)
**Vị trí**: `src/detector/yolo_face.py:47`      ← phải có số dòng
```python
<trích đúng đoạn code sai>                       ← phải trích, không mô tả suông
```
**Vì sao**: <hậu quả cụ thể, 1–2 câu — không phải "vi phạm quy tắc" mà là chuyện gì sẽ hỏng>
**Sửa**: <chỉ dẫn thao tác được, kèm đoạn code thay thế nếu ngắn>
```

Quy tắc viết:
- Nói về **code**, không nói về người viết code.
- "Vì sao" phải nêu **hậu quả thật**, không nhắc lại tên quy tắc. So sánh:
  ❌ *"Vi phạm R16"* · ✅ *"Khi Phase 3 chốt lại ngưỡng từ ROC, giá trị này sẽ bị bỏ sót,
  số trong báo cáo và số trong code lệch nhau."*
- "Sửa" phải đủ cụ thể để làm theo **mà không cần đọc lại toàn bộ đặc tả**.

---

## 5. Những gì KHÔNG review

| Không review | Vì sao |
|---|---|
| Khoảng trắng, xuống dòng, thứ tự import, độ dài dòng | `black` và `ruff` đã lo |
| Sở thích cá nhân về đặt tên khi tên hiện tại đã rõ nghĩa | Tranh cãi vô ích, tốn vòng lặp |
| Việc mà đặc tả **cố ý** để lại cho mã việc sau | Xem §8 "Ngoài phạm vi" của đặc tả |
| Thiết kế kiến trúc đã được chốt trong đặc tả | Muốn đổi → góp ý cho `spec-writer`, không trả lại Gemini |

Mỗi mục lỗi thừa làm loãng các mục lỗi thật và tốn thêm một vòng bàn giao.
**Một biên bản 4 lỗi đúng chỗ mạnh hơn một biên bản 20 mục.**

---

## 6. Checklist trước khi ra phán quyết

- [ ] Đã chạy đủ **ba lệnh máy** và ghi kết quả thật vào biên bản
- [ ] Đã kiểm `git status --short` đối chiếu danh sách trắng
- [ ] Đã quét đủ bảng mẫu vi phạm §2
- [ ] Đã đối chiếu **từng mục** của đặc tả (§3 interface, §4 config, §5 ca biên, §6 nghiệm thu, §8 phạm vi)
- [ ] Mọi lỗi đều có `file:dòng` + trích code + hậu quả + cách sửa
- [ ] Đã soi riêng hai điểm sống còn: **trung thực số liệu** và **fail-safe phần cứng**
- [ ] Không có mục lỗi nào thuộc nhóm "không review" §5
- [ ] Phán quyết dứt khoát: ✅ ĐẠT / 🟡 ĐẠT CÓ ĐIỀU KIỆN / 🔴 TRẢ LẠI
- [ ] Biên bản đã ghi vào `docs/review/<mã việc>.review.md`
- [ ] Nếu là vòng ≥ 2: đã ghi nối tiếp vào cùng file, không tạo file mới
- [ ] Nếu hết vòng 2 vẫn 🔴: đã dừng và chẩn đoán nguyên nhân gốc thay vì giao lại Gemini
