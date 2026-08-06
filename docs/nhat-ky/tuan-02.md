# Tuần 2 — 22/07 đến 28/07/2026

**Phase**: 0 — Khởi tạo & Môi trường

---

## Mục tiêu tuần

Khởi tạo kho mã nguồn, chốt phạm vi đề tài và thiết lập quy trình làm việc trước khi viết dòng mã đầu tiên.

## Đã thực hiện

### 1. Khởi tạo kho mã nguồn (24–25/07)

- Tạo kho `UIT-AI503.F3.LT.TTNT`, đưa các tài liệu gốc của đề tài vào `docs/`
  (`269e988`, `7fb80e9` — 18 file, 3.851 dòng).
- Soạn `CLAUDE.md` — tài liệu quy tắc của dự án: bối cảnh đề tài, 6 chỉ tiêu cam kết,
  bộ quy tắc R1–R37, cấu trúc thư mục chuẩn, pipeline 8 Phase với 4 cổng A→B→C→D.
- Soạn `.gitignore` chặn dữ liệu sinh trắc học, model weights và secret theo quy tắc R25.

### 2. Chốt phạm vi và thiết kế đánh giá

- **Điều chỉnh quy mô gallery** từ 5–7 người xuống **2–3 người** (sinh viên + gia đình), định vị lại
  đề tài là ứng dụng cá nhân trong hộ gia đình nhằm hạn chế thu thập dữ liệu sinh trắc học của người ngoài.
- Do gallery nhỏ nên **không thể trích một phần cơ sở dữ liệu làm tập người lạ**. Thiết kế bổ sung
  **ba tập impostor độc lập**: LFW gốc, LFW đã hiệu chỉnh miền dữ liệu, và tập in-domain 5–7 người quen
  có đồng ý. Kèm quy trình kiểm chứng hiệu chỉnh miền bằng cách đối chiếu `FAR_adapt` với `FAR_indomain`.
- Bổ sung chỉ tiêu `FAR_adapt` ≤ 1 % bên cạnh 5 chỉ tiêu gốc.

Toàn bộ điều chỉnh ghi vào `docs/dieu-chinh-pham-vi.md`.

### 3. Thiết lập quy trình phát triển (25/07)

Thiết lập quy trình 5 nhịp phân vai giữa hai công cụ hỗ trợ: một công cụ viết mã, công cụ còn lại
viết đặc tả và kiểm định (`7c042ed` — 10 file, 1.282 dòng).

```
N1 đặc tả → N2 sinh mã → N3 review → N4 sửa → N5 nghiệm thu
```

Sản phẩm:
- `GEMINI.md` — quy tắc cài đặt mã nguồn, gồm 10 quy tắc cứng và danh sách cấm
- `.claude/agents/spec-writer.agent.md`, `.claude/agents/code-reviewer.agent.md`
- `.claude/instructions/code-review.instructions.md` — thang phân loại lỗi 4 mức
- `docs/dac-ta/`, `docs/review/` — hai thư mục bàn giao, được commit để làm bằng chứng quy trình
- Bổ sung quy tắc R38–R41 vào `CLAUDE.md` §2.9

Nguyên tắc then chốt: **người review không được sửa mã nguồn** — nếu sửa thì không còn ai kiểm định
bản sửa đó.

### 4. Thiết lập nhánh theo R30 (25/07)

- Lập nhánh `dev` tách từ `main`; quy ước `feat/<mã việc>` tách từ `dev`, gộp về `dev`;
  `main` chỉ nhận từ `dev` khi một Phase đã qua đủ 4 cổng, kèm tag `phase-<n>-done`.
- Sửa lệnh tạo worktree thiếu điểm xuất phát nhánh (`e7e75ed`) — thiếu tham số này thì nhánh mới
  mọc từ HEAD hiện tại và lần gộp sau sẽ kéo theo commit lạ.
- Hai pull request đã gộp: `#1` (khởi tạo quy trình), `#2` (sửa lệnh worktree).

## Số liệu

Chưa có. Tuần này chưa phát sinh thực nghiệm.

## Vướng mắc

- Chưa có phần cứng Raspberry Pi 5.
- `CLAUDE.md` §8 ghi vị trí hiện tại là Phase 1, không khớp thực tế (Phase 0 chưa xong).

## Kế hoạch tuần sau

- Chạy thử trọn một vòng 5 nhịp với mã việc đầu tiên `P0-01-nen-tang` để hiệu chỉnh khung đặc tả
- Bắt đầu Chương 1 của báo cáo — phần khảo sát công trình liên quan không phụ thuộc kết quả thực nghiệm

---

*Nguồn: lịch sử git từ `269e988` đến `e7e75ed`.*
