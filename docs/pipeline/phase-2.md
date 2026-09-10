# PHASE 2 — Phát hiện khuôn mặt (YOLOv8n-face)

**Tuần 2–3 (22/07–04/08/2026)**

> Tệp này là **kế hoạch** của Phase 2, tách ra từ `CLAUDE.md` §5.
> Bộ quy tắc R1–R43 và cấu trúc 4 cổng nằm ở `CLAUDE.md`, **luôn áp dụng**, không lặp lại ở đây.
> **Trạng thái thực tế** (số đo đã có, việc còn nợ) ở [`docs/trang-thai.md`](../trang-thai.md).

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 2.1 | Tải `yolov8n-face.pt`, chạy thử trên PC, xác nhận chất lượng detect | Baseline PC |
| 2.2 | Export **ONNX** (`imgsz=320` và `640`, `opset=12`) và **NCNN**; ghi lại kích thước file | `models/*.onnx`, `*.ncnn` |
| 2.3 | Viết `src/detector/yolo_face.py` — interface `detect(frame) -> List[FaceBox]` (bbox, conf, landmarks) | Module detector |
| 2.4 | Test trên Docker ARM64 với video mẫu; `pytest tests/test_detector.py` | Test xanh |
| 2.5 | Deploy lên **Pi 5 thật**, đo FPS realtime từ camera | Số đo FPS |
| 2.6 | **Benchmark ma trận**: {ONNX, NCNN} × {320, 640} × {1, 2, 4 thread} → chọn cấu hình tối ưu | `results/bench_detect_*.csv` |
| 2.7 | Ghi nhận nhiệt độ CPU + throttling trong 10 phút chạy liên tục | Log nhiệt độ |

**Cổng C — chỉ tiêu chặn: ≥ 10 FPS trên Pi 5.** Chưa đạt → giảm `imgsz`, đổi sang NCNN, bật quantization.
**Cổng D:** Chương 2 §YOLOv8n-face + Chương 4 §Kết quả phát hiện khuôn mặt.
**Công cụ:** `training.agent.md` · `experiment-protocol.instructions.md`
