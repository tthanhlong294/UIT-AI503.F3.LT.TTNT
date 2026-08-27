# Kịch bản kiểm máy — thư mục đã đóng băng

> **Trạng thái: ĐÓNG BĂNG từ 27/08/2026.** Không viết thêm tệp `.ps1` nào vào đây.
> Ba tệp còn lại là **di tích** của mã việc `P3-01b` — biên bản
> `docs/review/P3-01b-chan-gia-tri-hong.review.md` trỏ tới chúng, nên xoá đi thì biên bản đó
> không tái lập được nữa.

---

## Thư mục này từng dùng để làm gì

Từ 25/08 đến 27/08/2026, quy trình 6 nhịp cấm mọi tác tử chạy lệnh (R42 bản cũ). Hệ quả: mỗi lượt
tự kiểm và mỗi lượt kiểm định đều phải gói thành một kịch bản PowerShell để người dùng chạy bằng
đúng một lệnh, rồi dán nguyên khối kết quả về.

## Vì sao bỏ

Kịch bản gộp giải quyết đúng một vấn đề — người dùng chỉ phải gõ một lệnh — nhưng tạo ra ba vấn đề
lớn hơn:

| Vấn đề | Biểu hiện |
|---|---|
| Vòng lặp sửa mã dài ra | Mỗi lần `coder` sửa một dòng, người dùng lại phải chạy toàn bộ kịch bản và dán về; nhịp chờ nằm giữa mọi bước |
| Kịch bản trở thành một phần mềm thứ hai phải bảo trì | Đã có lỗi thật: kịch bản treo ở `less` vì quên `$env:GIT_PAGER = "cat"` |
| Đầu ra gộp khó đọc | Lỗi thật nằm lẫn giữa hàng trăm dòng của các đoạn xanh |

Từ 27/08/2026, ranh giới đặt lại theo **ai chạy cái gì**, không theo **đóng gói thế nào**:

| Việc | Ai chạy | Lệnh nằm ở đâu |
|---|---|---|
| **Tự kiểm** — `black`, `ruff`, `pytest` host, `pytest` trong `faceid:arm64`, đột biến | `coder`, trong phiên riêng của nó | §9 của đặc tả `docs/dac-ta/<mã>.md` |
| **Kiểm định** — dựng lại độc lập mọi phép kiểm | **người dùng** | `code-reviewer` đưa từng lệnh rời trong hội thoại; biên bản chép lại nguyên văn |
| **Đo hiệu năng** | **người dùng**, trên máy đo | `training` đưa từng lệnh rời; `results/*.meta.json` giữ lại lệnh đã chạy |

Nguyên tắc không đổi: **người viết mã không được là người chấm mã.** `coder` chạy lệnh trên mã của
chính nó là tự kiểm, không phải kiểm định. Mọi con số đi vào biên bản review vẫn phải đến từ lượt
chạy của người dùng.

---

## Quy ước cho lệnh rời

Áp dụng cho `code-reviewer` và `training` — hai vai không được chạy gì (R42).

1. **Mỗi khối mã đúng một lệnh.** Người dùng bấm chạy từng khối, dán kết quả theo thứ tự.
2. **Nêu kết quả mong đợi trước mỗi lệnh** — một dòng. Không có mốc kỳ vọng thì kết quả dán về
   không phân định được đạt hay không.
3. **Tắt trình phân trang của git** ở lệnh git nào in thẳng ra màn hình:
   `git --no-pager log …`. Thiếu thì màn hình đứng ở dấu `:` chờ bấm phím.
4. **Kết thúc bằng** `git status --short --untracked-files=all` để lộ ngay nếu cây làm việc bẩn.
5. **Không bao giờ**: `git commit`, `git push`, `git checkout`, dựng image Docker mới,
   `pip install`, xoá tệp trong `data/` hay `results/`.
6. **Docker chỉ dùng `faceid:arm64`** (R43). Không `docker build -t <tên khác>`, không giữ image tạm.

### Phép đột biến bằng lệnh rời — bốn bước, không rút gọn

Đây là phần dễ làm hỏng cây làm việc nhất. Mã của `coder` **chưa commit**, nên tuyệt đối không
khôi phục bằng `git checkout -- <tệp>` — lệnh đó xoá luôn phần mã chưa commit. Phải sao lưu ra
**ngoài repo** rồi chép ngược lại.

```powershell
Copy-Item src/recognizer/arcface_backend.py "$env:TEMP\db.bak"; (Get-FileHash src/recognizer/arcface_backend.py -Algorithm SHA256).Hash
```

```powershell
(Get-Content src/recognizer/arcface_backend.py -Raw).Replace('<chuỗi gốc>', '<chuỗi đột biến>') | Set-Content src/recognizer/arcface_backend.py -NoNewline -Encoding utf8
```

```bash
python -m pytest -q
```

```powershell
Copy-Item "$env:TEMP\db.bak" src/recognizer/arcface_backend.py -Force; Remove-Item "$env:TEMP\db.bak"; (Get-FileHash src/recognizer/arcface_backend.py -Algorithm SHA256).Hash
```

Hai giá trị `sha256` ở bước 1 và bước 4 **phải khớp**. Không khớp → dừng, báo lại, không chạy tiếp.

Đọc kết quả: phép đột biến **phải làm đỏ đúng ca mà đặc tả chỉ định**, không thừa không thiếu. Phá mã
mà bộ kiểm thử vẫn xanh nghĩa là chỗ đó chưa có ca nào canh — lỗi của bộ kiểm thử, không phải của
phép đột biến.

---

## Người dùng cần làm gì

1. Chạy từng lệnh mà tác tử đưa, theo đúng thứ tự
2. Dán **toàn bộ** đầu ra về, kể cả phần trông như rác — dòng lỗi thường nằm ở chỗ không ngờ
3. Nếu bước khôi phục báo `sha256` lệch: dừng, báo lại, **không chạy tiếp**

Không cần đọc hiểu đầu ra. Việc đọc là của tác tử.
