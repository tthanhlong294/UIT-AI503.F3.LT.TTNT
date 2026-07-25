---
applyTo: "report/**, docs/**/*.md"
description: Chuẩn viết văn bản học thuật tiếng Việt cho báo cáo khoá luận — văn phong, thuật ngữ, định dạng số liệu, cấu trúc bảng-hình, trích dẫn IEEE và quy tắc trung thực dữ liệu. Áp dụng cho mọi nội dung trong report/ và docs/.
---

# Instructions: Viết văn bản học thuật

Áp dụng cho **mọi file** trong `report/` và `docs/**/*.md`.
Chi tiết mở rộng xem skill `report-drafting` (soạn thảo) và `academic-editing` (rà soát).

---

## 1. Quy tắc số một — trung thực dữ liệu

Trước khi viết bất kỳ con số nào: **tìm nguồn trong `results/`, đọc file, lấy đúng giá trị**.

- Không có nguồn → viết `[CHƯA ĐO — cần chạy <script>]` và báo cho người dùng.
- ❌ Không điền số minh hoạ, số "ví dụ", số ước lượng.
- ❌ Không lấy số từ paper khác rồi trình bày như kết quả của đồ án.
- Số liệu từ công trình khác **luôn kèm trích dẫn** và nói rõ đó là kết quả của họ.
- Mỗi bảng/hình có ghi chú nguồn: `Nguồn: results/bench_recognize_20260812_1430.csv`.

---

## 2. Văn phong

### Ngôi kể — ngôi thứ ba, luôn luôn

| ❌ | ✅ |
|---|---|
| Em đã xây dựng hệ thống… | Hệ thống được xây dựng… |
| Tôi chọn ArcFace vì… | Nghiên cứu này lựa chọn ArcFace do… |
| Chúng ta thấy rằng… | Kết quả cho thấy… |
| Mình nhận thấy… | Có thể nhận thấy… |

### Định lượng thay cho cảm tính

| ❌ | ✅ |
|---|---|
| rất nhanh | 18,4 ms mỗi khuôn mặt |
| tốt hơn nhiều | cao hơn 2,7 điểm phần trăm |
| khá chính xác | đạt độ chính xác 96,8 % |
| ổn định | độ lệch chuẩn FPS 0,4 trong 2 giờ chạy |
| nhiều nghiên cứu chỉ ra | các nghiên cứu [3], [7], [12] chỉ ra |

### Cấu trúc

- Câu > 40 từ → tách. Đoạn > 8 câu → tách. Đoạn < 2 câu → gộp.
- ❌ Câu hỏi tu từ, dấu chấm than, biểu tượng cảm xúc trong thân báo cáo.
- ❌ Không dùng gạch đầu dòng thay cho đoạn văn phân tích (bullet chỉ để liệt kê thuần).
- Mỗi đoạn một ý, có câu chủ đề.

---

## 3. Thuật ngữ — bảng chuẩn

Lần đầu xuất hiện: `tiếng Việt (tiếng Anh)`. Từ lần 2: dùng **một dạng nhất quán** toàn báo cáo.

| Dùng | Không dùng |
|---|---|
| phát hiện khuôn mặt | dò tìm khuôn mặt |
| nhận diện khuôn mặt | nhận dạng / nhận biết khuôn mặt |
| vector đặc trưng (embedding) | vector nhúng |
| chống giả mạo khuôn mặt (anti-spoofing) | chống gian lận |
| phát hiện sự sống (liveness detection) | kiểm tra sống |
| ngưỡng | mức chặn |
| độ trễ | thời gian delay |
| suy luận | chạy mô hình |
| đăng ký khuôn mặt | ghi danh |
| AI biên (edge AI) | AI cạnh |
| pipeline, relay | (giữ nguyên tiếng Anh) |

Tên riêng viết đúng: `Raspberry Pi 5`, `YOLOv8n-face`, `MobileFaceNet`, `ArcFace`, `MiniFASNet`, `dlib`, `ONNX`, `NCNN`.

Viết tắt định nghĩa ở lần đầu: *"tỉ lệ chấp nhận sai (False Acceptance Rate — FAR)"*,
và phải có trong **Danh mục từ viết tắt** đầu báo cáo.

---

## 4. Định dạng số và đơn vị (chuẩn tiếng Việt)

| ❌ | ✅ |
|---|---|
| `96.8%` | `96,8 %` |
| `18.4ms` | `18,4 ms` |
| `11.4 fps` | `11,4 FPS` |
| `2s` | `2 s` |
| `112x112` | `112 × 112` |
| `0.5-2m` | `0,5 – 2 m` |
| `1000000` | `1 000 000` |

- **Dấu thập phân là dấu phẩy.**
- **Có khoảng trắng giữa số và đơn vị**, kể cả trước `%`.
- Làm tròn nhất quán: độ chính xác / FAR / FRR 1 chữ số thập phân; latency 1 chữ số; FPS 1 chữ số.
- Kèm độ lệch chuẩn khi có: `11,4 ± 0,6 FPS`.
- Trong LaTeX: `\sisetup{output-decimal-marker={,}}` và dùng cột `S` của `siunitx`.

---

## 5. Bảng và hình

### Bảng
- Tiêu đề **phía trên**, đánh số theo chương: `Bảng 4.3. <mô tả>`
- Chân bảng: **nguồn + điều kiện đo**
- Dùng `booktabs` (`\toprule`, `\midrule`, `\bottomrule`), **không đường kẻ dọc**
- Đơn vị đặt ở tiêu đề cột, không lặp trong từng ô
- Cột số căn theo dấu thập phân

### Hình
- Tiêu đề **phía dưới**: `Hình 4.7. <mô tả>`
- Nhãn trục: tên đại lượng + đơn vị, tiếng Việt
- Định dạng vector `.pdf`, cỡ chữ ≥ 8 pt sau khi thu nhỏ, đọc được khi in đen trắng
- **Hình số liệu phải sinh từ script** đọc `results/` (xem skill `latex-visualization`)

### Quy tắc chung
**Mọi bảng/hình phải được dẫn trong thân bài trước khi xuất hiện.**
> "Bảng 4.3 trình bày kết quả so sánh hai phương án nhận diện."

Không để bảng/hình đứng trơ trọi không có câu dẫn và câu nhận xét.

---

## 6. Trích dẫn — IEEE

- Trong bài: `[1]`, `[2]`, `[3]–[5]`; đánh số theo thứ tự xuất hiện lần đầu.
- Lưu trong `report/refs.bib`.
- **≥ 20 tài liệu**, ≥ 60 % từ 2020 trở lại đây.
- Bắt buộc có **paper gốc** của: YOLO, ArcFace, MobileFaceNet, Silent Face Anti-Spoofing.
- ❌ Không Wikipedia, blog cá nhân, nội dung do AI sinh ra.
- ❌ Không có tài liệu **mồ côi** (trong `.bib` mà không được dẫn).
- ❌ Không có trích dẫn **treo** (`[n]` trong bài mà không có trong `.bib`).
- Mọi phát biểu về công trình khác, mọi công thức lấy từ paper: đều phải trích dẫn.

```
[1] J. Deng, J. Guo, N. Xue, and S. Zafeiriou, "ArcFace: Additive Angular Margin Loss for
    Deep Face Recognition," in Proc. IEEE/CVF CVPR, 2019, pp. 4690–4699.
```

---

## 7. Cấu trúc & đánh số

- Chương: `Chương 1`, `Chương 2`… Mục: `1.1`, `1.1.1` (tối đa 3 cấp).
- Không có mục con đơn độc: có `3.2.1` thì phải có `3.2.2`.
- Công thức đánh số theo chương: `(2.3)`, và phải được dẫn trong thân bài.
- Mỗi chương có đoạn dẫn nhập ở đầu và đoạn chuyển tiếp ở cuối.
- Không lặp nội dung giữa các chương: Ch.2 (lý thuyết) ≠ Ch.3 (thiết kế) ≠ Ch.4 (kết quả).

---

## 8. Đạo đức nghiên cứu — mục bắt buộc

Báo cáo **phải có** mục nêu:
- **Gallery** chỉ gồm sinh viên thực hiện và thành viên gia đình (**2–3 người**); **tập impostor
  in-domain** gồm **5–7 người quen đã được thông báo mục đích và đồng ý**. Danh sách người tham gia
  ghi nhận ở `docs/nguoi-tham-gia.md`. Đây là lựa chọn có chủ ý nhằm hạn chế thu thập dữ liệu
  sinh trắc học.
- Tập người lạ gồm: **LFW** (công khai, có trích dẫn công trình gốc và nêu giấy phép; xử lý cục bộ,
  **không phát hành lại** ảnh kèm mã nguồn) và **5–7 người quen đã đồng ý tham gia**, dùng mã ẩn danh.
- ❌ Nghiên cứu **không sử dụng hình ảnh của người không được thông báo và không đồng ý** —
  không trích ảnh từ camera an ninh, không lấy ảnh từ mạng xã hội. Nêu rõ điều này trong báo cáo.
- Dữ liệu **xử lý hoàn toàn cục bộ**, không truyền lên cloud — đây vừa là lựa chọn kỹ thuật
  (edge AI) vừa là cam kết quyền riêng tư.
- Dữ liệu ảnh **không được công bố** kèm mã nguồn, chỉ mô tả thống kê.
- Không sử dụng ảnh của người khác khi chưa được phép.

---

## 9. Nhật ký tuần — `docs/nhat-ky/tuan-XX.md`

Viết **cuối mỗi tuần**, không dồn. Mẫu:

```markdown
# Tuần <n> — <dd/mm> đến <dd/mm>/2026

## Phase & cổng
Phase <n> — <tên> · Cổng đã qua: <A/B/C/D>

## Đã làm
- <việc> → <kết quả cụ thể, có số liệu nếu có>

## Kết quả đo được
| Chỉ số | Giá trị | Nguồn |
|---|---|---|

## Vướng mắc
- <vấn đề> → <cách xử lý / còn tồn đọng>

## Kế hoạch tuần sau
- <việc cụ thể>

## Cần hỏi GVHD
- <câu hỏi>
```

Nhật ký tuần là **nguyên liệu thô** để viết Chương 4 — ghi càng chi tiết, viết báo cáo càng nhanh.

---

## 10. Checklist mỗi lần viết xong một mục

- [ ] Mọi số có nguồn `results/` được ghi chú
- [ ] Không còn `[CHƯA ĐO]` / `TBD` chưa báo cáo
- [ ] Không dùng ngôi thứ nhất
- [ ] Thuật ngữ nhất quán theo §3
- [ ] Định dạng số theo §4 (dấu phẩy thập phân, khoảng trắng đơn vị)
- [ ] Bảng/hình có số, tiêu đề, nguồn, và được dẫn trong bài
- [ ] Trích dẫn `[n]` đều có trong `refs.bib`
- [ ] Không có từ cảm tính không đo được
- [ ] Nội dung không vượt ngoài phạm vi đề cương
- [ ] Độ dài trong ngân sách trang của chương
