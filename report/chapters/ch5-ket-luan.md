# Chương 5 — Kết luận và Hướng phát triển

> **Khung làm việc.** Viết ở Phase 8 (bước 8.2). Ngân sách ~3 trang.
> §5.1 và §5.2 cần số liệu thật từ `results/`; §5.3 tích luỹ dần trong suốt quá trình làm.

---

## 5.1. Kết quả đạt được

`[CHƯA VIẾT]` — cần số liệu Phase 7

Bảng đối chiếu **bắt buộc** có, điền bằng số thật, có ghi nguồn file trong `results/`:

| Chỉ tiêu cam kết | Ngưỡng | Đạt được | Kết luận |
|---|---|---|---|
| Độ chính xác nhận diện người đã đăng ký | ≥ 95 % | `[CHƯA ĐO]` | |
| *(bổ sung)* `FAR_adapt` — LFW đã hiệu chỉnh miền | ≤ 1 % | `[CHƯA ĐO]` | |
| FPS toàn pipeline | ≥ 5 FPS | `[CHƯA ĐO]` | |
| FPS riêng module phát hiện | ≥ 10 FPS | `[CHƯA ĐO]` | |
| Độ trễ điều khiển thiết bị | < 2 s | `[CHƯA ĐO]` | |
| Tỉ lệ phát hiện tấn công giả mạo | ≥ 90 % | `[CHƯA ĐO]` | |

Chỉ tiêu không đạt → phân tích nguyên nhân trung thực, không sửa số, không hạ ngưỡng (R7).

---

## 5.2. Hạn chế

`[CHƯA VIẾT]` — nêu thẳng, không né tránh

Các hạn chế đã biết trước, phải có mặt:

1. **Quy mô gallery nhỏ (2–3 người).** Kết quả độ chính xác không khái quát hoá được cho hệ thống
   nhiều người dùng; chưa đánh giá được mức suy giảm khi số danh tính đăng ký tăng.
2. **Tập impostor in-domain chỉ 5–7 danh tính** → khoảng tin cậy rộng, chỉ đủ vai trò kiểm chứng
   chứ không phải phép đo chính xác.
3. `[BỔ SUNG SAU]` — các hạn chế phát sinh từ kết quả thực nghiệm.

---

## 5.3. Hướng phát triển

Mục này tích luỹ dần. Mỗi ý **phải nêu được căn cứ**, tốt nhất là số đo từ `results/`, để phân biệt
với ý tưởng chung chung.

### 5.3.1. Huấn luyện tinh chỉnh trên dữ liệu khuôn mặt người Việt Nam

**Nội dung**: tinh chỉnh (fine-tune) mô hình phát hiện và mô hình trích xuất đặc trưng trên bộ dữ liệu
khuôn mặt người Việt Nam quy mô lớn, nhằm giảm khác biệt miền dữ liệu giữa tập huấn luyện quốc tế và
điều kiện sử dụng thực tế trong nước.

**Căn cứ dẫn vào**: dẫn lại chỉ số recall của mô hình phát hiện đo ở Chương 4 trên dữ liệu thu bằng
chính camera hệ thống. `[CHƯA ĐO]`

**Vì sao không thực hiện trong phạm vi nghiên cứu này** — cần nêu rõ, vì đây là câu hỏi phản biện
nhiều khả năng xuất hiện:

- Khác biệt theo nhóm nhân khẩu được ghi nhận chủ yếu ở **khối trích xuất đặc trưng**, không phải khối
  phát hiện; trong khi khối trích xuất đặc trưng thuộc phạm vi bị loại trừ (không huấn luyện lại mô hình).
- Việc tinh chỉnh đòi hỏi bộ dữ liệu có nhãn khung bao và điểm mốc ở quy mô hàng nghìn ảnh. Nghiên cứu
  này giới hạn thu thập dữ liệu ở những người đã được thông báo và đồng ý, nên **không có nguồn dữ liệu
  hợp lệ** ở quy mô đó.
- Tinh chỉnh trên tập nhỏ có nguy cơ quá khớp và suy giảm khả năng khái quát hoá, làm kết quả kém hơn
  mô hình gốc.

**Điều kiện để thực hiện được**: xây dựng bộ dữ liệu khuôn mặt người Việt Nam có sự đồng ý hợp lệ và
có nhãn đầy đủ — bản thân việc này là một hướng nghiên cứu độc lập.

> Nghiên cứu này đã xử lý một phần vấn đề khác biệt miền dữ liệu bằng con đường khác, không cần huấn
> luyện: hiệu chỉnh miền (domain adaptation) tập LFW cho khớp đặc trưng camera thực tế, và kiểm chứng
> bằng tập in-domain thu tại chỗ. Xem Chương 4 §4.2b.

### 5.3.2. Mở rộng giao thức và giao diện

- **MQTT** cho khối chấp hành, thay cho điều khiển GPIO trực tiếp — cho phép tích hợp với các nền tảng
  nhà thông minh sẵn có.
- **ReactJS** cho giao diện giám sát, thay cho Flask + Jinja2.

### 5.3.3. Mở rộng năng lực nhận diện

- Nhận diện **nhiều người đồng thời** trong khung hình và ở khoảng cách xa hơn.
- **Camera hồng ngoại** hoặc cảm biến chiều sâu để cải thiện chống giả mạo và hoạt động trong bóng tối.
- Đánh giá mức **suy giảm độ chính xác khi quy mô gallery tăng** — trực tiếp giải quyết hạn chế §5.2.1.

### 5.3.4. Tăng tốc phần cứng

Raspberry Pi 5 không tích hợp bộ xử lý thần kinh chuyên dụng, nhưng có cổng PCIe 2.0 x1 cho phép gắn
bộ tăng tốc suy luận rời. Hướng này đáng xem xét nếu cần nâng số khung hình xử lý hoặc chạy đồng thời
nhiều mô hình. Dẫn lại số FPS đo được ở Chương 4 làm căn cứ. `[CHƯA ĐO]`

### 5.3.5. Hoàn thiện kỹ thuật

Các cải tiến nhỏ đã được ghi nhận trong quá trình thực hiện nhưng để ngoài phạm vi:

- Nạp lại cấu hình khi đang chạy, cấu hình theo môi trường (phát triển / triển khai)
- Tối ưu ảnh container: dựng nhiều tầng, chạy bằng người dùng không phải `root`
- Đóng gói và phát hành ảnh container để triển khai lại nhanh

---

## Checklist hoàn thành Chương 5

- [ ] Bảng §5.1 điền đủ 6 dòng bằng số thật, mỗi số ghi nguồn file trong `results/`
- [ ] Mỗi chỉ tiêu có kết luận Đạt / Không đạt rõ ràng
- [ ] Chỉ tiêu không đạt có phân tích nguyên nhân, không có chỗ nào sửa ngưỡng cho vừa kết quả
- [ ] §5.2 nêu thẳng hạn chế gallery 2–3 người và hệ quả của nó
- [ ] Mỗi mục §5.3 có căn cứ, không có ý tưởng chung chung thiếu dẫn chứng
- [ ] §5.3.1 giải thích được **vì sao không làm trong phạm vi này**, không chỉ nói "sẽ làm sau"
- [ ] Không dùng ngôi thứ nhất
- [ ] Không còn `[CHƯA VIẾT]` hay `[CHƯA ĐO]` sót lại
