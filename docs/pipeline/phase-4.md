# PHASE 4 — Chống giả mạo (Anti-spoofing)

**Tuần 4–5 (05–18/08/2026)** · có thể chạy song song Phase 3

> Tệp này là **kế hoạch** của Phase 4, tách ra từ `CLAUDE.md` §5.
> Bộ quy tắc R1–R43 và cấu trúc 4 cổng nằm ở `CLAUDE.md`, **luôn áp dụng**, không lặp lại ở đây.
> **Trạng thái thực tế** ở [`docs/trang-thai.md`](../trang-thai.md).
> Quy trình tạo bộ dữ liệu tấn công: [`docs/spoof-protocol.md`](../spoof-protocol.md).

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 4.1 | Tích hợp MiniFASNet ONNX → `src/antispoof/minifasnet.py`, interface `is_live(face_crop) -> (bool, score)` | Module |
| 4.2 | Đặt module **sau detect, trước recognize** trong pipeline (thứ tự này bắt buộc — tiết kiệm tài nguyên) | Pipeline đúng thứ tự |
| 4.3 | Chạy trên bộ `data/spoof/` — đo riêng cho **ảnh in** và **màn hình điện thoại** | Kết quả 2 loại tấn công |
| 4.4 | Đo **APCER** (tấn công lọt), **BPCER** (người thật bị từ chối), **ACER** | `results/bench_antispoof_*.csv` |
| 4.5 | Tinh chỉnh ngưỡng liveness — ưu tiên giảm APCER, chấp nhận BPCER cao hơn (an ninh trước tiện dụng) | Threshold đã chốt |
| 4.6 | Đo **chi phí FPS** khi bật anti-spoofing so với khi tắt | Số liệu overhead |

**Cổng C — chỉ tiêu chặn: phát hiện ≥ 90 % tấn công (cả 2 loại).**
**Cổng D:** Chương 2 §Liveness detection + Chương 4 §Kết quả chống giả mạo.
**Công cụ:** `training.agent.md` · `experiment-protocol.instructions.md`
