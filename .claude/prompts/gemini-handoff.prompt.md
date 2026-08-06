# Prompt: Bàn giao công việc cho Gemini

Dùng ở **Nhịp 2** (sinh mã) và **Nhịp 4** (sửa theo review) của quy trình 5 nhịp — xem `CLAUDE.md` §2.9.

Tham số cần điền:
- `<MÃ>` — mã việc, ví dụ `P0-01-nen-tang`
- `<mã>` — mã việc viết thường, dùng cho tên nhánh

---

## 0. Chuẩn bị nhánh (làm một lần cho mỗi mã việc)

Gemini làm việc **ngay trong thư mục dự án**, trên một nhánh `feat/` riêng. Bảo vệ đến từ git:
mọi thứ đã commit đều khôi phục được, nên **điều kiện bắt buộc là cây làm việc phải sạch trước khi
gọi Gemini**.

Đồng bộ `dev`, rồi tạo nhánh **tách từ `dev`** (R30 — `feat/*` luôn phân nhánh từ `dev`,
không phải từ `main`):

```bash
git checkout dev && git pull
```

```bash
git checkout -b feat/<mã>
```

> ⚠️ **Hai điều kiện, kiểm trước khi chạy Gemini:**
> ```bash
> git status --short && git log --oneline -1 -- docs/dac-ta/<MÃ>.md
> ```
> Lệnh đầu **không được in gì** — còn việc chưa commit thì commit hoặc `git stash` trước.
> Lệnh sau phải in ra commit chứa đặc tả; chưa commit đặc tả thì Gemini vẫn đọc được file trên đĩa,
> nhưng lịch sử sẽ mất dấu vết bàn giao.

> 💡 **Khi nào vẫn nên dùng worktree**: chỉ khi bạn muốn làm việc khác song song trong lúc Gemini
> chạy lâu (ví dụ build Docker vài chục phút). Khi đó:
> `git worktree add ../wt-<mã> -b feat/<mã> dev` — nhưng nhớ rằng đặc tả sửa giữa chừng sẽ **không**
> tự có trong worktree, phải `git checkout dev -- docs/dac-ta/<MÃ>.md` hoặc trỏ reviewer sang repo chính.

---

## 1. Nhịp 2 — Sinh mã

Chạy trong thư mục dự án, trên nhánh `feat/<mã>`:

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
- [ ] Đang đứng đúng nhánh: `git branch --show-current` → `feat/<mã>`
- [ ] **Cây làm việc sạch**: `git status --short` không in gì — đây là lớp bảo vệ duy nhất khi
      Gemini chạy `--approval-mode auto_edit` ngay trong thư mục dự án

---

## 4. Sau khi Gemini báo xong

```bash
git status --short      # đối chiếu danh sách trắng
git diff --stat
```

Rồi gọi review — **luôn dùng agent, không tự đọc lướt**:

> Dùng agent `code-reviewer` review `<MÃ>` trên nhánh `feat/<mã>`, đối chiếu `docs/dac-ta/<MÃ>.md`.

Phán quyết:

| Phán quyết | Làm gì |
|---|---|
| 🔴 TRẢ LẠI | Chạy lệnh Nhịp 4 ở §2. Tối đa **2 vòng** rồi dừng, xem lại đặc tả |
| 🟡 ĐẠT CÓ ĐIỀU KIỆN | Được commit; góp ý chuyển thành mã việc mới nếu bạn đồng ý |
| ✅ ĐẠT | Commit + gộp nhánh (§5) |

---

## 5. Gộp về sau khi ĐẠT

Commit trên nhánh `feat/<mã>` (bạn commit, không phải Gemini). Dùng `-A` để lấy cả biên bản
review — nó là bằng chứng quy trình, phải đi cùng commit mã nguồn:

```bash
git add -A && git commit -m "feat(<phạm vi>): <mô tả> — <MÃ>"
```

Gộp **vào `dev`** (không phải `main`) rồi xoá nhánh:

```bash
git checkout dev && git merge --no-ff feat/<mã> && git branch -d feat/<mã>
```

Commit message theo `CLAUDE.md` R29, **luôn kèm mã việc ở cuối** để truy vết được sang
`docs/dac-ta/`, `docs/review/` và nhật ký tuần.

> `main` **chỉ nhận từ `dev`** khi một Phase đã qua đủ 4 cổng A→B→C→D, kèm tag `phase-<n>-done` (R32):
> ```bash
> git checkout main && git merge --no-ff dev && git tag phase-<n>-done && git push --follow-tags
> ```
> Nếu làm qua Pull Request: PR của mã việc để `--base dev`; chỉ PR cuối Phase mới `--base main`.
> `gh pr create` mặc định lấy nhánh mặc định của repo (`main`) — **phải ghi rõ `--base dev`**.

---

## 6. Xử lý sự cố

| Tình huống | Xử lý |
|---|---|
| Gemini sửa file ngoài danh sách trắng | `git checkout -- <file>` khôi phục file đó (file mới thì `rm`), ghi CHẶN-A vào biên bản, nêu rõ trong lệnh Nhịp 4 |
| Gemini làm hỏng nhiều thứ, muốn quay về mốc sạch | `git reset --hard` đưa cây làm việc về commit gần nhất. **Chỉ an toàn nếu đã commit trước khi chạy** — đó là lý do checklist §3 bắt cây làm việc sạch |
| Gemini lỡ `git commit` | Không hoảng: `git reset --soft HEAD~1` giữ nguyên nội dung. Nhắc lại lệnh cấm ở lượt sau |
| Gemini đòi thêm dependency | Không cho tự thêm. `spec-writer` cập nhật đặc tả trước, rồi chạy lại |
| Gemini hỏi lại vì đặc tả mơ hồ | **Dấu hiệu tốt.** Sửa đặc tả (`spec-writer`), commit, rồi chạy lại — đừng trả lời trực tiếp trong hội thoại Gemini vì câu trả lời đó không lưu lại được |
| Cần chạy nhiều mã việc song song | Lúc này mới dùng worktree: mỗi mã việc một thư mục riêng. Không chạy 2 Gemini trên cùng thư mục |
| `git worktree remove` báo `Permission denied` | Có chương trình đang mở thư mục đó. Đóng editor/terminal rồi xoá tay bằng `rm -rf`. Git đã bỏ đăng ký worktree nên `git branch -d` vẫn chạy được |
| Việc quá nhỏ (< 10 dòng, sửa lỗi chính tả) | Claude được sửa trực tiếp, **nhưng phải ghi một dòng vào biên bản review** để không mất dấu vết |
