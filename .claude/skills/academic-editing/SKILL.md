---
name: academic-editing
description: Rà soát và biên tập văn bản học thuật tiếng Việt cho báo cáo khoá luận — sửa văn phong, thống nhất thuật ngữ, chuẩn hoá định dạng số liệu và đơn vị, kiểm tra trích dẫn IEEE, phát hiện số liệu không có nguồn. Dùng trước khi nộp bất kỳ chương nào cho GVHD hoặc trước hạn nộp cuối.
---

# Skill: Biên tập học thuật (Academic Editing)

Rà soát văn bản **đã viết** trong `report/` và `docs/`. Không viết nội dung mới —
việc đó thuộc skill `report-drafting`.

---

## Quy trình rà soát 6 lớp (làm theo đúng thứ tự)

```
Lớp 1: Tính trung thực số liệu   ← quan trọng nhất, làm trước
Lớp 2: Cấu trúc & logic
Lớp 3: Văn phong học thuật
Lớp 4: Thuật ngữ & nhất quán
Lớp 5: Định dạng số, đơn vị, bảng, hình
Lớp 6: Trích dẫn & tài liệu tham khảo
```

---

## LỚP 1 — Tính trung thực số liệu ⛔

Quét mọi con số trong văn bản. Với **từng con số**:

| Kiểm tra | Hành động khi sai |
|---|---|
| Có ghi chú nguồn `results/...` không? | Đánh dấu `⚠️ THIẾU NGUỒN` |
| File nguồn có tồn tại thật không? | `Glob results/` xác minh — không có → `⛔ NGUỒN KHÔNG TỒN TẠI` |
| Giá trị trong văn bản có khớp file không? | Đọc file, đối chiếu → lệch thì báo cả 2 giá trị |
| Số liệu từ tài liệu khác có trích dẫn `[n]` không? | Thiếu → `⛔ ĐẠO VĂN SỐ LIỆU` |
| Còn `[CHƯA ĐO]`, `TBD`, `XX`, `...` sót lại không? | Liệt kê đầy đủ vị trí |

**Dấu hiệu số liệu đáng ngờ cần chất vấn:**
- Số quá tròn: `95.0%`, `10 FPS`, `2.0s` — đo thật hiếm khi tròn thế
- Kết quả khớp chỉ tiêu một cách hoàn hảo ở mọi chỉ số
- Không có độ lệch chuẩn / khoảng tin cậy
- Không nêu số lần lặp hoặc điều kiện đo

**Kiểm tra riêng cho đồ án này — gallery 2–3 người, ba tập impostor:**
- [ ] Mỗi lần nêu **accuracy** có kèm **câu cảnh báo cỡ mẫu** không? Thiếu → `⛔`
- [ ] Có báo cáo **đủ 4 con số FAR** (`FAR_noibo`, `FAR_lfw`, `FAR_adapt`, `FAR_indomain`)
      hay gộp thành một cột "FAR"? Gộp → `⛔`
- [ ] Có nêu rõ **`FAR_adapt` là số báo cáo chính** không, hay lẫn lộn các con số?
- [ ] Có **kết luận kiểm chứng** `FAR_adapt` vs `FAR_indomain` kèm khoảng tin cậy không? Thiếu → `⛔`
- [ ] Có nêu **giới hạn thống kê của tập in-domain** (5–7 danh tính → khoảng tin cậy rộng,
      là kiểm chứng chứ không phải phép đo) không?
- [ ] §4.2b có mô tả **quy trình domain adaptation** đủ chi tiết để tái lập không?
- [ ] Chương 4 §4.2 có nêu **lý do điều chỉnh phạm vi** không?
- [ ] Chương 5 mục Hạn chế có nêu **quy mô gallery nhỏ** không?
- [ ] Có so sánh trực tiếp accuracy với công trình dùng gallery lớn mà không nêu điều kiện khác nhau? → `⚠️`
- [ ] Bộ dữ liệu **LFW đã được trích dẫn**, nêu giấy phép, và nêu **bias đã biết** của LFW chưa?
- [ ] Phần đạo đức có khẳng định **chỉ thu ảnh của người đã đồng ý** không?

Báo cáo lớp này **riêng, ở đầu output**, vì đây là rủi ro nghiêm trọng nhất khi bảo vệ.

---

## LỚP 2 — Cấu trúc & logic

- [ ] Mỗi chương có đoạn dẫn nhập và đoạn kết chuyển tiếp
- [ ] Đánh số mục liên tục, không nhảy cóc (3.1 → 3.2 → 3.3)
- [ ] Không có mục con đơn độc (có 3.2.1 thì phải có 3.2.2)
- [ ] Mọi bảng/hình được **dẫn trong thân bài trước khi xuất hiện**
- [ ] Không lặp nội dung giữa các chương (Ch.2 lý thuyết ≠ Ch.3 thiết kế ≠ Ch.4 kết quả)
- [ ] Chương 4 có mô tả **điều kiện đo** trước khi trình bày kết quả
- [ ] Chương 5 đối chiếu **đủ 5 chỉ tiêu** cam kết
- [ ] Nội dung không vượt ngoài phạm vi đề cương (§4.4 — không đám đông, không train from scratch)
- [ ] Độ dài mỗi chương nằm trong ngân sách trang (±20 %)

---

## LỚP 3 — Văn phong học thuật

### Ngôi kể

| ❌ Sai | ✅ Đúng |
|---|---|
| Em đã xây dựng… | Hệ thống được xây dựng… |
| Tôi nhận thấy… | Kết quả cho thấy… |
| Chúng ta có thể thấy… | Có thể nhận thấy… / Số liệu Bảng 4.3 chỉ ra… |
| Mình chọn ArcFace vì… | Nghiên cứu này lựa chọn ArcFace do… |

### Từ ngữ cảm tính → định lượng

| ❌ Mơ hồ | ✅ Cụ thể |
|---|---|
| rất nhanh, cực nhanh | 18,4 ms mỗi khuôn mặt |
| tốt hơn nhiều, vượt trội | cao hơn 2,7 điểm phần trăm |
| khá chính xác | đạt độ chính xác 96,8 % |
| gần như hoàn hảo | APCER 3,2 % |
| ổn định | độ lệch chuẩn FPS 0,4 trong 2 giờ chạy liên tục |
| nhiều nghiên cứu cho thấy | các nghiên cứu [3], [7], [12] cho thấy |

### Cấu trúc câu

- Câu dài > 40 từ → tách.
- Đoạn > 8 câu → tách.
- Đoạn < 2 câu → gộp hoặc mở rộng.
- ❌ Câu hỏi tu từ: "Vậy làm sao để tăng tốc độ?" → "Để tăng tốc độ xử lý, nghiên cứu áp dụng…"
- ❌ Dấu chấm than trong thân báo cáo.
- ❌ Gạch đầu dòng thay cho đoạn văn phân tích (bullet chỉ dùng cho liệt kê thuần).

---

## LỚP 4 — Thuật ngữ & nhất quán

### Bảng thuật ngữ chuẩn của đồ án

| Khái niệm | Dùng thống nhất | Không dùng |
|---|---|---|
| face detection | **phát hiện khuôn mặt** | dò tìm, nhận dạng khuôn mặt |
| face recognition | **nhận diện khuôn mặt** | nhận dạng, nhận biết |
| embedding | **vector đặc trưng (embedding)** | vector nhúng, mã hoá đặc trưng |
| anti-spoofing | **chống giả mạo khuôn mặt (anti-spoofing)** | chống gian lận, phát hiện giả |
| liveness detection | **phát hiện sự sống (liveness detection)** | kiểm tra sống |
| threshold | **ngưỡng** | mức chặn, giá trị chặn |
| latency | **độ trễ** | thời gian trễ, delay |
| inference | **suy luận** | dự đoán, chạy mô hình |
| enroll | **đăng ký khuôn mặt** | ghi danh, thêm người dùng |
| gallery | **tập khuôn mặt đã đăng ký** | thư viện, kho |
| pipeline | **pipeline** (giữ nguyên) | dây chuyền, luồng ống |
| relay | **relay** (giữ nguyên) | rơ-le, công tắc điện tử |
| edge AI | **AI biên (edge AI)** | AI cạnh, trí tuệ biên |
| pre-trained | **mô hình đã huấn luyện sẵn (pre-trained)** | mô hình sẵn có |

**Quy tắc**: thuật ngữ tiếng Anh xuất hiện **lần đầu** ghi dạng `tiếng Việt (tiếng Anh)`,
từ lần 2 dùng thống nhất **một** dạng trong toàn báo cáo.

### Kiểm tra nhất quán khác

- [ ] Tên mô hình viết đúng, thống nhất: `YOLOv8n-face`, `MobileFaceNet`, `ArcFace`, `MiniFASNet`, `dlib`
- [ ] `Raspberry Pi 5` — không viết `RPi5`, `Pi5`, `raspberry pi`
- [ ] Viết tắt định nghĩa ở lần đầu: "tỉ lệ chấp nhận sai (False Acceptance Rate — FAR)"
- [ ] Danh mục từ viết tắt đầu báo cáo khớp với thực tế dùng trong bài
- [ ] Cách gọi 2 phương án nhất quán xuyên suốt (đặt tên rõ ở Ch.3, dùng lại y hệt ở Ch.4)

---

## LỚP 5 — Định dạng số, đơn vị, bảng, hình

### Số và đơn vị (chuẩn tiếng Việt)

| ❌ | ✅ |
|---|---|
| `96.8%` | `96,8 %` |
| `18.4ms` | `18,4 ms` |
| `11.4fps` / `11.4 fps` | `11,4 FPS` |
| `2s` | `2 s` |
| `1000000` | `1 000 000` |
| `0.5-2m` | `0,5 – 2 m` |
| `112x112` | `112 × 112` |

- Làm tròn nhất quán: độ chính xác/FAR/FRR 1 chữ số thập phân; latency 1 chữ số; FPS 1 chữ số.
- Có khoảng trắng giữa số và đơn vị (kể cả `%`).
- Số đo hiệu năng nên kèm ± độ lệch chuẩn khi có: `11,4 ± 0,6 FPS`.

### Bảng

- [ ] Tiêu đề **phía trên**, đánh số theo chương: `Bảng 4.3.`
- [ ] Chân bảng ghi **nguồn + điều kiện đo**
- [ ] Dùng `booktabs`, không đường kẻ dọc
- [ ] Cột số căn theo dấu thập phân (`siunitx`)
- [ ] Đơn vị đặt ở tiêu đề cột, không lặp trong từng ô

### Hình

- [ ] Tiêu đề **phía dưới**: `Hình 4.7.`
- [ ] Nhãn trục có tên đại lượng + đơn vị, tiếng Việt
- [ ] Cỡ chữ trong hình ≥ 8 pt sau khi thu nhỏ
- [ ] Định dạng vector (`.pdf`), đọc được khi in đen trắng
- [ ] Hình số liệu sinh từ script (kiểm `scripts/plot_*.py` có tồn tại)

---

## LỚP 6 — Trích dẫn & tài liệu tham khảo

- [ ] Định dạng **IEEE**: `[1]`, `[2]`, `[3]–[5]`, đánh số theo thứ tự xuất hiện lần đầu
- [ ] **Không có tài liệu mồ côi** — mọi mục trong `refs.bib` được dẫn ≥ 1 lần
- [ ] **Không có trích dẫn treo** — mọi `[n]` trong bài có mục trong `refs.bib`
- [ ] ≥ 20 tài liệu tham khảo
- [ ] Có đủ **paper gốc** của các mô hình dùng: YOLO, ArcFace, MobileFaceNet, Silent Face Anti-Spoofing
- [ ] ≥ 60 % tài liệu từ 2020 trở lại đây
- [ ] ❌ Không có Wikipedia, blog cá nhân, nội dung do AI sinh
- [ ] Mọi câu phát biểu về công trình khác đều có trích dẫn
- [ ] Mọi công thức lấy từ paper đều ghi nguồn: `... theo [8]`

**Kiểm nhanh bằng lệnh:**
```bash
# Trích dẫn treo: khoá dùng trong .tex nhưng không có trong .bib
grep -oh '\\cite{[^}]*}' report/chapters/*.tex | sed 's/.*{//;s/}//' | tr ',' '\n' | sort -u > /tmp/da_dung.txt
grep -oh '^@[a-z]*{[^,]*' report/refs.bib | sed 's/.*{//' | sort -u > /tmp/co_trong_bib.txt
comm -23 /tmp/da_dung.txt /tmp/co_trong_bib.txt   # trích dẫn treo
comm -13 /tmp/da_dung.txt /tmp/co_trong_bib.txt   # tài liệu mồ côi
```

---

## Định dạng báo cáo kết quả rà soát

```markdown
## 📝 KẾT QUẢ RÀ SOÁT — <tên file/chương>

### ⛔ NGHIÊM TRỌNG — phải sửa trước khi nộp
1. **[Lớp 1]** Dòng 142: độ chính xác "96,8 %" không có nguồn trong `results/`.
   → Bổ sung ghi chú nguồn hoặc chạy lại benchmark.
2. ...

### ⚠️ CẦN SỬA
1. **[Lớp 3]** Dòng 87: "Em đã cài đặt…" → "Hệ thống được cài đặt…"
2. **[Lớp 4]** Dòng 203: dùng "nhận dạng khuôn mặt", các chỗ khác dùng "nhận diện" → thống nhất "nhận diện".
3. ...

### 💡 NÊN CẢI THIỆN
1. **[Lớp 2]** Mục 4.6 dài 4,5 trang so với ngân sách 3 trang → cân nhắc rút gọn phần mô tả cài đặt.

### 📊 Tổng kết
| Lớp | Số vấn đề | Nghiêm trọng |
|---|---|---|
| 1 — Số liệu | 3 | 2 |
| 2 — Cấu trúc | 1 | 0 |
| ... | | |

**Kết luận**: <Sẵn sàng nộp / Cần sửa X vấn đề nghiêm trọng trước khi nộp>
```

---

## Checklist cuối cùng trước khi nộp (23–24/09/2026)

- [ ] Mọi số liệu truy được về `results/`
- [ ] Không còn `[CHƯA ĐO]` / `TBD` / placeholder
- [ ] Bảng đối chiếu 5 chỉ tiêu ở Chương 5 đã điền đủ
- [ ] Không dùng ngôi thứ nhất ở bất kỳ đâu trong thân báo cáo
- [ ] Thuật ngữ nhất quán theo bảng Lớp 4
- [ ] Mọi bảng/hình có số, tiêu đề, nguồn, và được dẫn trong bài
- [ ] Trích dẫn IEEE đầy đủ, không treo, không mồ côi
- [ ] Mục lục / danh mục hình / danh mục bảng / danh mục viết tắt đã cập nhật
- [ ] Tổng số trang ≈ 50 (±5)
- [ ] Thông tin bìa đúng: tên đề tài VI/EN, SV Trần Thanh Long – 25410088, GVHD ThS. Phan Đình Duy
- [ ] Có mục nêu **đạo đức nghiên cứu** (chỉ thu ảnh của người đã được thông báo và đồng ý)
- [ ] Đã nêu **điều chỉnh phạm vi** kèm lý do và cách bù đắp
- [ ] Đã báo cáo **đủ 4 con số FAR** + kết luận kiểm chứng domain adaptation
- [ ] Đã trích dẫn nguồn LFW và nêu giấy phép
- [ ] File PDF xuất ra không lỗi font tiếng Việt
