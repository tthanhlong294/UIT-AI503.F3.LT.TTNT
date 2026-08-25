# Prompt: Bàn giao công việc cho người cài đặt

Dùng ở **Nhịp 2** (sinh mã) và **Nhịp 5** (sửa theo review) của quy trình 6 nhịp — xem `CLAUDE.md` §2.9.

⚠️ **Người cài đặt không chạy gì** (R42). Nó viết mã **và** viết một kịch bản kiểm, rồi dừng.
Bạn — người dùng — chạy kịch bản đó và dán kết quả về. Đó là **Nhịp 3**, nằm giữa hai nhịp dưới đây.

Người cài đặt là agent **`coder`** (`.claude/agents/coder.agent.md`). Hiến pháp của nó là
`docs/quy-tac-cai-dat.md` — tài liệu trung lập, không gắn với một công cụ cụ thể.

Tham số cần điền:
- `<MÃ>` — mã việc, ví dụ `P1-03-preprocess`
- `<mã>` — mã việc viết thường, dùng cho tên nhánh

---

## 0. Chuẩn bị nhánh (một lần cho mỗi mã việc)

Người cài đặt làm việc **ngay trong thư mục dự án**, trên một nhánh `feat/` riêng. Lớp bảo vệ đến từ
git: mọi thứ đã commit đều khôi phục được, nên **điều kiện bắt buộc là cây làm việc phải sạch trước
khi giao việc**.

```bash
git checkout dev && git pull
```

```bash
git checkout -b feat/<mã>
```

> ⚠️ **Hai điều kiện, kiểm trước khi giao:**
> ```bash
> git status --short && git log --oneline -1 -- docs/dac-ta/<MÃ>.md
> ```
> Lệnh đầu **không được in gì** — còn việc chưa commit thì commit hoặc `git stash` trước.
> Lệnh sau phải in ra commit chứa đặc tả (R39: bàn giao qua file đã commit).

---

## 1. Nhịp 2 — Sinh mã

Gọi agent `coder` với nội dung sau, thay `<MÃ>` bằng mã việc thật:

> Đọc `docs/quy-tac-cai-dat.md`, sau đó đọc `docs/dac-ta/<MÃ>.md`. Cài đặt **đúng** đặc tả đó.
> Chỉ được tạo/sửa các file trong DANH SÁCH TRẮNG §2. Giữ nguyên chữ ký hàm ở §3 — không đổi tên,
> không đổi kiểu trả về. Thư viện chỉ được dùng những gì §7 cho phép; thiếu → **dừng và báo**.
> Mỗi dòng trong bảng §5 phải có ít nhất một ca test **có assert thật**, và ca test phải **thực sự đi
> qua** đoạn mã cần kiểm.
> Bạn **không được chạy bất cứ lệnh nào**. Thay vào đó, viết `docs/kiem-may/<MÃ>.coder.ps1` theo khung
> ở `docs/kiem-may/README.md`: `black`, `ruff`, `pytest` trên host, `pytest` trong `faceid:arm64`,
> `git status`, và một phép đột biến cho mỗi guard quan trọng kèm dự đoán ca nào phải đỏ.
> **TUYỆT ĐỐI KHÔNG `git commit`.** Kết thúc bằng báo cáo theo mẫu §12 của quy tắc cài đặt, nêu rõ
> lệnh tôi cần chạy, rồi **dừng lại chờ tôi dán kết quả về**. Không đoán trước kết quả.

## 2. Nhịp 3 — Người dùng chạy

```bash
powershell -ExecutionPolicy Bypass -File docs/kiem-may/<MÃ>.coder.ps1
```

Dán **toàn bộ** đầu ra về cho `coder`. Có đoạn đỏ → nó sửa rồi bạn chạy lại. Tất cả xanh → sang Nhịp 4.

Dòng khôi phục báo `KHONG KHOP` → **dừng**, không chạy tiếp, báo lại. Nghĩa là một phép đột biến đã
không trả mã nguồn về nguyên trạng, và cây làm việc đang bẩn.

## 3. Nhịp 5 — Sửa theo biên bản review

> Đọc `docs/quy-tac-cai-dat.md`, `docs/dac-ta/<MÃ>.md` và `docs/review/<MÃ>.review.md`.
> Sửa **đúng** các mục 🔴 CHẶN và 🟡 CẦN SỬA trong biên bản, theo chỉ dẫn ở phần "Sửa" của từng mục.
> **Không** làm thêm việc khác, **không** sửa các mục 🔵 GÓP Ý.
> Nếu đặc tả đã được cập nhật sau biên bản đó, **đọc lại đặc tả từ đầu** — nêu rõ trong lời giao.
> Cập nhật `docs/kiem-may/<MÃ>.coder.ps1` nếu cần thêm đoạn kiểm cho chỗ vừa sửa.
> **KHÔNG chạy gì, KHÔNG `git commit`.** Báo cáo từng mục lỗi đã xử lý thế nào rồi dừng chờ tôi chạy lại.

> 💡 Khi giao Nhịp 5, **liệt kê thẳng các việc cần sửa** trong lời giao thay vì chỉ trỏ tới biên bản.
> Kinh nghiệm từ `P1-01` và `P1-02`: chỉ dẫn càng cụ thể thì càng ít vòng lặp.

---

## 3. Checklist trước khi giao

- [ ] File `docs/dac-ta/<MÃ>.md` đã tồn tại **và đã commit**
- [ ] Đặc tả có đủ 8 mục theo khung của `spec-writer`
- [ ] §2 danh sách trắng liệt kê đủ file, **có cả file test**
- [ ] §5 chỉ chứa assert pytest; lệnh shell nằm ở §6
- [ ] **Không ô "Assert tối thiểu" nào gộp từ hai điều kiện trở lên**
- [ ] §7 nêu rõ **thư viện được phép dùng**
- [ ] Các ràng buộc §2, §3, §5, §7 **thoả mãn được đồng thời** — tồn tại ít nhất một cách cài đặt hợp lệ
- [ ] File `configs/*.yaml` mà đặc tả tham chiếu đã tồn tại
- [ ] Đang đúng nhánh: `git branch --show-current` → `feat/<mã>`
- [ ] **Cây làm việc sạch**: `git status --short` không in gì

---

## 4. Nhịp 4 — Review

Sau khi kịch bản `.coder.ps1` đã xanh hết, gọi review — **luôn dùng agent, không tự đọc lướt**:

> Dùng agent `code-reviewer` review `<MÃ>` trên nhánh `feat/<mã>`, đối chiếu `docs/dac-ta/<MÃ>.md`.
> Viết `docs/kiem-may/<MÃ>.review.ps1` rồi dừng chờ tôi chạy. Dựng lại **tất cả** phép đột biến từ
> đầu, kể cả những phép người cài đặt nói đã làm rồi.

Nó sẽ dừng và đưa lệnh. Bạn chạy, dán kết quả, nó mới viết biên bản:

```bash
powershell -ExecutionPolicy Bypass -File docs/kiem-may/<MÃ>.review.ps1
```

| Phán quyết | Làm gì |
|---|---|
| ⏳ CHƯA KẾT LUẬN | Nó còn thiếu số liệu — chạy tiếp đoạn nó xin, đừng ép nó kết luận sớm |
| 🔴 TRẢ LẠI | Giao lại Nhịp 5 (§3). Trần **2 vòng**, sau đó dừng và **xem lại đặc tả** |
| 🟡 ĐẠT CÓ ĐIỀU KIỆN | Được commit; góp ý chuyển thành mã việc mới nếu người dùng đồng ý |
| ✅ ĐẠT | Commit + gộp nhánh (§5) |

⚠️ Biên bản nào có bảng kết quả máy toàn ✅ mà bạn **chưa hề chạy lượt nào** thì đó là số liệu bịa —
trả lại và bắt viết kịch bản. Đây là chế độ hỏng nguy hiểm nhất của mô hình mới.

> **Reviewer phải chạy phiên riêng, ngữ cảnh sạch** — không được thấy quá trình viết đặc tả hay viết
> mã. Đây là phần chịu lực của toàn bộ quy trình: người viết và người kiểm phải độc lập.

---

## 5. Gộp về sau khi ĐẠT

Dùng `-A` để lấy cả biên bản review — nó là bằng chứng quy trình, phải đi cùng commit mã nguồn:

```bash
git add -A && git commit -m "feat(<phạm vi>): <mô tả> — <MÃ>"
```

```bash
git checkout dev && git merge --no-ff feat/<mã> && git branch -d feat/<mã>
```

Commit message theo `CLAUDE.md` R29, **luôn kèm mã việc ở cuối** để truy vết sang `docs/dac-ta/`,
`docs/review/` và nhật ký tuần.

> `main` **chỉ nhận từ `dev`** khi một Phase đã qua đủ 4 cổng, kèm tag `phase-<n>-done` (R32):
> ```bash
> git checkout main && git merge --no-ff dev && git tag phase-<n>-done && git push --follow-tags
> ```
> Nếu làm qua Pull Request: PR của mã việc để `--base dev`; chỉ PR cuối Phase mới `--base main`.

---

## 6. Xử lý sự cố

| Tình huống | Xử lý |
|---|---|
| Sửa file ngoài danh sách trắng | `git checkout -- <file>` khôi phục (file mới thì `rm`), ghi CHẶN-A vào biên bản, nêu rõ ở Nhịp 5 |
| Làm hỏng nhiều thứ, muốn về mốc sạch | `git reset --hard` — **chỉ an toàn nếu đã commit trước**, đó là lý do checklist §3 bắt cây làm việc sạch |
| Lỡ `git commit` | `git reset --soft HEAD~1` giữ nguyên nội dung; nhắc lại lệnh cấm ở lượt sau |
| Đòi thêm thư viện | Không cho tự thêm. `spec-writer` cập nhật §7 của đặc tả trước, commit, rồi giao lại |
| Báo đặc tả mâu thuẫn hoặc bế tắc | **Dấu hiệu tốt.** Sửa đặc tả, commit, rồi giao lại — đây chính là điều đặc tả tự yêu cầu ở `docs/quy-tac-cai-dat.md` |
| Test xanh nhưng nghi chưa phủ | Chạy phép thử đột biến — xem `code-review.instructions.md` §2b |
| Cần chạy nhiều mã việc song song | Lúc này mới dùng worktree, mỗi mã việc một thư mục riêng |
| Việc quá nhỏ (< 10 dòng) | Claude được sửa trực tiếp, **nhưng phải ghi một dòng vào biên bản review** để không mất dấu vết |
