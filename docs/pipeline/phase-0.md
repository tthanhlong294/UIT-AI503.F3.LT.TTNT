# PHASE 0 — Khởi tạo & Môi trường

**Tuần 1 (15–21/07/2026)** · Trạng thái: cần hoàn tất trước mọi việc khác

> Tệp này là **kế hoạch** của Phase 0, tách ra từ `CLAUDE.md` §5.
> Bộ quy tắc R1–R43 và cấu trúc 4 cổng nằm ở `CLAUDE.md`, **luôn áp dụng**, không lặp lại ở đây.
> **Trạng thái thực tế** (đã làm tới đâu, số đo, việc còn nợ) ở [`docs/trang-thai.md`](../trang-thai.md).

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 0.1 | Tạo cây thư mục theo `CLAUDE.md` §3, tạo `.gitignore` (chặn `data/`, `models/*.onnx`, `.env`, `results/*.jpg`) | Repo có cấu trúc chuẩn |
| 0.2 | `requirements.txt` pin cứng: `ultralytics`, `onnxruntime`, `opencv-python`, `numpy`, `flask`, `pyyaml`, `python-telegram-bot`, `pytest`, `black`, `ruff` | File dependency |
| 0.3 | Viết `deploy/Dockerfile.arm64` + `docker-compose.yml` — môi trường giả lập ARM64 | Container build thành công |
| 0.4 | Cài Raspberry Pi OS 64-bit + Python venv trên Pi 5; bật camera; test `libcamera-hello` | Pi 5 sẵn sàng |
| 0.5 | `src/common/config.py` (loader YAML) + `src/common/logging.py` | Module nền tảng |
| 0.6 | Viết `.env.example`, `models/README.md` (link tải weights) | Tài liệu setup |

**Cổng C:** container ARM64 chạy được `python -c "import cv2, onnxruntime"` · Pi 5 mở được camera.
**Cổng D:** `docs/nhat-ky/tuan-01.md` + Chương 3 §Môi trường triển khai (nháp).
**Công cụ:** `onboarding-with-skills` agent · `python-embedded.instructions.md`
