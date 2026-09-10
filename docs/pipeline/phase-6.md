# PHASE 6 — Web giám sát & Tích hợp hệ thống

**Tuần 7–8 (26/08–08/09/2026)**

> Tệp này là **kế hoạch** của Phase 6, tách ra từ `CLAUDE.md` §5.
> Bộ quy tắc R1–R43 và cấu trúc 4 cổng nằm ở `CLAUDE.md`, **luôn áp dụng**, không lặp lại ở đây.
> **R12** (MQTT là mở rộng) và **R13** (ReactJS là mở rộng) chặn phạm vi Phase này.
> **Trạng thái thực tế** ở [`docs/trang-thai.md`](../trang-thai.md).

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 6.1 | Thiết kế CSDL SQLite: bảng `users`, `recognition_log`, `alerts`, `device_state` | Schema |
| 6.2 | Flask app `src/monitor/webapp.py`: **Dashboard** (trạng thái thiết bị, FPS hiện tại), **Lịch sử nhận diện**, **Ảnh cảnh báo**, **Quản lý người dùng đăng ký** | 4 màn hình |
| 6.3 | Đăng ký người dùng mới **qua web** (upload ảnh → enroll → sinh embedding) | Luồng enroll web |
| 6.4 | Xác thực đăng nhập cho trang quản trị (không để mở trong LAN) | Bảo mật cơ bản |
| 6.5 | **Tích hợp toàn hệ thống** `src/main.py`: vòng lặp capture → detect → antispoof → recognize → decision → actuate → log | Hệ thống hợp nhất |
| 6.6 | `deploy/systemd/faceid.service` — **tự khởi động cùng thiết bị**, auto-restart khi crash | Service |
| 6.7 | Tối ưu hiệu năng: đa luồng (capture riêng thread), frame skipping, cache embedding | FPS cải thiện |
| 6.8 | ⚠️ **Chỉ khi đã đạt 6.1–6.7**: mở rộng MQTT (`mqtt_backend.py`) | Mở rộng (tuỳ chọn) |

**Cổng C:** web truy cập được từ máy khác trong LAN · reboot Pi → hệ thống tự chạy lại · **FPS toàn pipeline ≥ 5**.
**Cổng D:** Chương 3 §Thiết kế khối giám sát + Chương 4 §Tích hợp hệ thống.
**Công cụ:** `python-embedded.instructions.md`
