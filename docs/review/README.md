# Biên bản review mã nguồn

Thư mục này chứa biên bản kiểm định của agent `code-reviewer` cho từng mã việc.

## Quy ước

- Mỗi mã việc **một file**: `<MÃ VIỆC>.review.md` — ví dụ `P0-01-nen-tang.review.md`.
- Review lại lần 2 → **ghi nối tiếp vào cùng file** dưới tiêu đề `# Review <MÃ> — vòng 2`,
  không tạo file mới. Lịch sử sửa lỗi là dữ liệu có giá trị.
- Đặc tả tương ứng nằm ở `docs/dac-ta/<MÃ VIỆC>.md`.

## Chuỗi truy vết

```
docs/dac-ta/<MÃ>.md  →  nhánh feat/<mã>  →  docs/review/<MÃ>.review.md
                                          →  commit message (kết thúc bằng — <MÃ>)
                                          →  docs/nhat-ky/tuan-XX.md
```

Mã việc xuất hiện nguyên vẹn ở cả năm chỗ, nên có thể lần ngược từ một dòng code bất kỳ
về lý do nó tồn tại.

## Phán quyết

| Ký hiệu | Nghĩa |
|---|---|
| ✅ ĐẠT | Không còn lỗi 🔴 và 🟡 — được commit |
| 🟡 ĐẠT CÓ ĐIỀU KIỆN | Chỉ còn 🔵 góp ý — được commit, góp ý để người dùng quyết |
| 🔴 TRẢ LẠI | Còn lỗi chặn — giao lại Gemini sửa, tối đa 2 vòng |

Chuẩn phân loại lỗi: [`.claude/instructions/code-review.instructions.md`](../../.claude/instructions/code-review.instructions.md)
