# PHASE 5 — Điều khiển thiết bị & Cảnh báo

**Tuần 5–7 (12/08–01/09/2026)**

> Tệp này là **kế hoạch** của Phase 5, tách ra từ `CLAUDE.md` §5.
> Bộ quy tắc R1–R43 và cấu trúc 4 cổng nằm ở `CLAUDE.md`, **luôn áp dụng**, không lặp lại ở đây.
> Hai quy tắc chi phối nặng nhất Phase này: **R22** (mọi truy cập GPIO/IR qua lớp abstraction có
> backend `mock`) và **R24** (lỗi phần cứng phải fail-safe, đưa thiết bị về trạng thái tắt).
> **Trạng thái thực tế** (ngoại vi đã có chưa) ở [`docs/trang-thai.md`](../trang-thai.md).

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 5.1 | `src/actuator/base.py` — interface trừu tượng + **backend `mock`** (R22) chạy được trên PC | Abstraction layer |
| 5.2 | `gpio_backend.py` — relay/LED qua GPIO. Đấu nối theo `hardware/gpio-pinout.md` | Điều khiển đèn |
| 5.3 | `ir_backend.py` — phát lệnh IR cho tivi (LIRC hoặc `pigpio`); ghi lại mã IR của remote thật | Điều khiển tivi |
| 5.4 | `src/decision/policy.py` — **phân quyền theo danh tính**: bảng `user_id → {devices, actions}` trong `configs/actuator.yaml` | Khối quyết định |
| 5.5 | Logic chống nhiễu: cần **N frame liên tiếp** cùng danh tính mới kích hoạt; **cooldown** tránh bật/tắt liên tục | Ổn định hoá |
| 5.6 | **Đo độ trễ end-to-end**: từ frame có mặt → thiết bị đổi trạng thái, ≥ 30 lần lặp | `results/bench_latency_*.csv` |
| 5.7 | Cảnh báo người lạ: chụp ảnh → lưu `results/alerts/` → ghi log DB → gửi **Telegram bot** | Module cảnh báo |
| 5.8 | Rate-limit cảnh báo (không spam khi người lạ đứng lâu trước camera) | Chống spam |

**Cổng C — chỉ tiêu chặn: độ trễ điều khiển < 2 s.** Điều khiển đúng theo phân quyền.
**Cổng D:** Chương 3 §Thiết kế khối chấp hành + Chương 4 §Kết quả điều khiển thiết bị.
**Công cụ:** `hardware-safety.instructions.md` · `python-embedded.instructions.md`
