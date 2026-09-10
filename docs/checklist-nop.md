# Checklist trước khi nộp — kiểm 100 %

> Tách ra từ `CLAUDE.md` §7. Chỉ dùng ở **bước 8.4 của Phase 8**, nên không cần nằm trong tệp mà
> mọi vai nạp lại ở mỗi lượt. Kế hoạch Phase 8: [`pipeline/phase-8.md`](pipeline/phase-8.md).
>
> Đánh dấu từng dòng bằng bằng chứng cụ thể, không đánh dấu theo cảm giác. Dòng nào nhắc tới số
> liệu thì bằng chứng phải là **đường dẫn tệp trong `results/`** (R6).

- [ ] Mọi số liệu trong báo cáo truy được về file trong `results/`
- [ ] Bảng so sánh 2 phương án nhận diện đầy đủ (Accuracy, FAR, FRR, FPS, latency)
- [ ] Kết quả anti-spoofing tách riêng cho ảnh in và màn hình điện thoại
- [ ] Đủ 5 chỉ tiêu cam kết, mỗi chỉ tiêu có kết luận Đạt / Không đạt
- [ ] Kiểm thử trong ≥ 2 điều kiện ánh sáng
- [ ] Không có secret / ảnh khuôn mặt / weights lớn trong git history
- [ ] `README.md` cho phép người khác dựng lại hệ thống từ đầu
- [ ] Trích dẫn IEEE đầy đủ, không tài liệu tham khảo "mồ côi"
- [ ] Video demo đủ 3 tình huống
- [ ] Danh sách người tham gia + ngày đồng ý đã ghi nhận (`docs/nguoi-tham-gia.md`)
- [ ] **Đã nêu rõ hạn chế gallery 2–3 người** ở Chương 4 §4.2 và Chương 5
- [ ] **Đã báo cáo đủ 3 con số FAR** (`FAR_lfw`, `FAR_adapt`, `FAR_indomain`), không chỉ accuracy
- [ ] Đã trình bày **kết luận kiểm chứng domain adaptation**
- [ ] Đã mô tả **quy trình domain adaptation** đủ chi tiết để tái lập
- [ ] Đã trích dẫn nguồn và giấy phép bộ dữ liệu LFW
- [ ] Đã nêu điều chỉnh phạm vi so với đề cương gốc và lý do
- [ ] Không có ảnh của người chưa đồng ý trong toàn bộ dữ liệu (R28b)
