# PHASE 7 — Kiểm thử toàn hệ thống & Benchmark tổng

**Tuần 8–9 (02–15/09/2026)**

> Tệp này là **kế hoạch** của Phase 7, tách ra từ `CLAUDE.md` §5.
> Bộ quy tắc R1–R43 và cấu trúc 4 cổng nằm ở `CLAUDE.md`, **luôn áp dụng**, không lặp lại ở đây.
> **R5 đến R9** chi phối toàn bộ Phase này: không bịa số, mọi số truy về `results/`, không đạt thì
> báo cáo đúng sự thật chứ không hạ ngưỡng.
> **Trạng thái thực tế** ở [`docs/trang-thai.md`](../trang-thai.md).

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 7.1 | Viết **kịch bản kiểm thử** chuẩn: 3 tình huống × 2 điều kiện ánh sáng × ≥ 3 khoảng cách (0,5 / 1 / 2 m) | `tests/scenarios.md` |
| 7.2 | **Tình huống 1 — Người hợp lệ**: mỗi người ≥ 20 lượt → tỉ lệ nhận đúng, thời gian phản hồi | Kết quả TH1 |
| 7.3 | **Tình huống 2 — Người lạ**: ≥ 20 lượt → tỉ lệ từ chối đúng + cảnh báo có gửi không | Kết quả TH2 |
| 7.4 | **Tình huống 3 — Tấn công giả mạo**: ảnh in + màn hình ĐT, ≥ 20 lượt mỗi loại | Kết quả TH3 |
| 7.5 | Chạy **ổn định 2 giờ liên tục** — theo dõi rò rỉ bộ nhớ, nhiệt độ, throttling | Log ổn định |
| 7.6 | **Lập bảng benchmark tổng hợp** — đối chiếu từng chỉ tiêu `CLAUDE.md` §1 với số đo thực tế: Đạt/Không đạt | Bảng benchmark ⭐ |
| 7.7 | Vẽ toàn bộ biểu đồ cho báo cáo từ `results/` | `report/figures/*` |

**Cổng C:** đủ số liệu cho **cả 5 chỉ tiêu cam kết**, mỗi chỉ tiêu có kết luận Đạt/Không đạt kèm bằng chứng.
**Cổng D:** Chương 4 hoàn chỉnh.
**Công cụ:** `training.agent.md` · `skills/latex-visualization` · `experiment-protocol.instructions.md`
