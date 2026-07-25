# Prompt: Bàn giao công việc cho Gemini

Dùng ở **Nhịp 2** (sinh mã) và **Nhịp 4** (sửa theo review) của quy trình 5 nhịp — xem `CLAUDE.md` §2.9.

Tham số cần điền:
- `<MÃ>` — mã việc, ví dụ `P0-01-nen-tang`
- `<mã>` — mã việc viết thường, dùng cho tên nhánh/worktree

---

## 0. Chuẩn bị worktree (làm một lần cho mỗi mã việc)

Gemini làm việc trong **git worktree riêng** để không đụng được vào nhánh đang mở của bạn.

```bash
git worktree add ../wt-<mã> -b feat/<mã>
```

Thư mục `../wt-<mã>` là một bản sao làm việc độc lập, **cùng repo, khác nhánh**.
`GEMINI.md` và `docs/dac-ta/` có sẵn trong đó vì đã được commit.

> ⚠️ Đặc tả phải **đã commit** trước khi tạo worktree, nếu không Gemini sẽ không thấy file.
> Kiểm nhanh: `git status --short docs/dac-ta/`

---

## 1. Nhịp 2 — Sinh mã

Chạy trong thư mục worktree:

```bash
gemini --approval-mode auto_edit -p "Đọc GEMINI.md, sau đó đọc docs/dac-ta/<MÃ>.md. Cài đặt ĐÚNG đặc tả đó. Chỉ được tạo/sửa các file trong DANH SÁCH TRẮNG mục 2 của đặc tả. Giữ nguyên chữ ký hàm ở mục 3, không đổi tên và không đổi kiểu trả về. Chạy black, ruff, pytest cho tới khi sạch và xanh. TUYỆT ĐỐI KHÔNG git commit. Kết thúc bằng báo cáo theo mẫu mục 12 của GEMINI.md."
```

## 2. Nhịp 4 — Sửa theo biên bản review

```bash
gemini --approval-mode auto_edit -p "Đọc GEMINI.md, docs/dac-ta/<MÃ>.md và docs/review/<MÃ>.review.md. Sửa ĐÚNG các mục 🔴 CHẶN và 🟡 CẦN SỬA trong biên bản review, theo đúng chỉ dẫn ở phần 'Sửa' của từng mục. KHÔNG làm thêm việc khác, KHÔNG sửa các mục 🔵 GÓP Ý. Chạy lại black, ruff, pytest. TUYỆT ĐỐI KHÔNG git commit. Báo cáo từng mục lỗi đã xử lý thế nào."
```

---

## 3. Checklist trước khi bấm chạy

- [ ] File `docs/dac-ta/<MÃ>.md` đã tồn tại **và đã commit**
- [ ] Đặc tả có đủ 8 mục theo khung của `spec-writer`
- [ ] Mục 2 (danh sách trắng) liệt kê đủ file, **có cả file test**
- [ ] File `configs/*.yaml` mà đặc tả tham chiếu đã tồn tại
- [ ] Đang đứng trong worktree đúng nhánh: `git branch --show-current` → `feat/<mã>`
- [ ] Cây làm việc sạch: `git status --short` không có gì

---

## 4. Sau khi Gemini báo xong

```bash
git status --short      # đối chiếu danh sách trắng
git diff --stat
```

Rồi gọi review — **luôn dùng agent, không tự đọc lướt**:

> Dùng agent `code-reviewer` review `<MÃ>` trong worktree `../wt-<mã>`, đối chiếu `docs/dac-ta/<MÃ>.md`.

Phán quyết:

| Phán quyết | Làm gì |
|---|---|
| 🔴 TRẢ LẠI | Chạy lệnh Nhịp 4 ở §2. Tối đa **2 vòng** rồi dừng, xem lại đặc tả |
| 🟡 ĐẠT CÓ ĐIỀU KIỆN | Được commit; góp ý chuyển thành mã việc mới nếu bạn đồng ý |
| ✅ ĐẠT | Commit + gộp nhánh (§5) |

---

## 5. Gộp về sau khi ĐẠT

Commit ngay trong worktree (bạn commit, không phải Gemini):

```bash
git add -A && git commit -m "feat(<phạm vi>): <mô tả> — <MÃ>"
```

Về repo chính rồi gộp và dọn worktree:

```bash
git merge --no-ff feat/<mã>
git worktree remove ../wt-<mã>
```

Commit message theo `CLAUDE.md` R29, **luôn kèm mã việc ở cuối** để truy vết được sang
`docs/dac-ta/`, `docs/review/` và nhật ký tuần.

---

## 6. Xử lý sự cố

| Tình huống | Xử lý |
|---|---|
| Gemini sửa file ngoài danh sách trắng | `git checkout -- <file>` khôi phục file đó, ghi CHẶN-A vào biên bản, nêu rõ trong lệnh Nhịp 4 |
| Gemini lỡ `git commit` | Không hoảng: `git reset --soft HEAD~1` giữ nguyên nội dung. Nhắc lại lệnh cấm ở lượt sau |
| Gemini đòi thêm dependency | Không cho tự thêm. `spec-writer` cập nhật đặc tả trước, rồi chạy lại |
| Gemini hỏi lại vì đặc tả mơ hồ | **Dấu hiệu tốt.** Sửa đặc tả (`spec-writer`), commit, rồi chạy lại — đừng trả lời trực tiếp trong hội thoại Gemini vì câu trả lời đó không lưu lại được |
| Cần chạy nhiều mã việc song song | Mỗi mã việc một worktree riêng. Không chạy 2 Gemini trên cùng thư mục |
| Việc quá nhỏ (< 10 dòng, sửa lỗi chính tả) | Claude được sửa trực tiếp, **nhưng phải ghi một dòng vào biên bản review** để không mất dấu vết |
