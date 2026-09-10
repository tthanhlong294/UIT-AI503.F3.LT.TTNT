# PHASE 3 — Nhận diện danh tính & So sánh 2 phương án ⭐

**Tuần 3–5 (29/07–18/08/2026)** · **Đây là đóng góp khoa học chính của đồ án**

> Tệp này là **kế hoạch** của Phase 3, tách ra từ `CLAUDE.md` §5.
> Bộ quy tắc R1–R43 và cấu trúc 4 cổng nằm ở `CLAUDE.md`, **luôn áp dụng**, không lặp lại ở đây.
> Ba nguồn impostor và lập luận đằng sau chúng: [`phase-1.md`](phase-1.md).
> **Trạng thái thực tế** (gallery hiện có, bẫy đã biết) ở [`docs/trang-thai.md`](../trang-thai.md).

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 3.1 | Định nghĩa interface chung `src/recognizer/base.py`: `enroll(images) -> Embedding`, `identify(face) -> (user_id, score)` | Interface |
| 3.2 | **Phương án A**: `src/recognizer/dlib_backend.py` dùng `face_recognition` (128-D) | Backend A |
| 3.3 | **Phương án B**: `src/recognizer/arcface_backend.py` dùng MobileFaceNet/ArcFace ONNX (512-D, cosine similarity) | Backend B |
| 3.4 | `scripts/enroll.py` — sinh embedding trung bình từ tập enroll cho từng người, lưu `data/embeddings/` | Gallery |
| 3.5 | **Quét ngưỡng**: với mỗi backend, quét threshold → vẽ ROC/DET, chọn điểm cân bằng FAR/FRR | Đường cong ROC |
| 3.6 | **Kịch bản đo thống nhất** (cùng CSDL, cùng ánh sáng, cùng phần cứng Pi 5), đo: Accuracy, Precision, Recall, **FAR** (nhận nhầm), **FRR**, FPS, latency (p50/p95) | `results/bench_recognize_*.csv` |
| 3.7 | **Đo FAR trên cả ba tập impostor** → `FAR_lfw`, `FAR_adapt`, `FAR_indomain`. **Đây là chỉ số quan trọng nhất** vì gallery chỉ 2–3 người | Số liệu open-set ⭐ |
| 3.7b | **Kiểm chứng domain adaptation**: so `FAR_adapt` với `FAR_indomain`. Khớp → adaptation hợp lệ, dùng `FAR_adapt` làm số báo cáo chính. Lệch xa → điều chỉnh tham số adaptation ở bước 1.8 rồi đo lại, hoặc báo cáo trung thực khoảng chênh lệch | Kết luận kiểm chứng ⭐ |
| 3.7c | Chốt ngưỡng **theo `FAR_adapt` ≤ 1 %**, không theo accuracy | Ngưỡng chính thức |
| 3.8 | **Lập bảng so sánh A vs B + kết luận chọn phương án chính thức** (có lý do định lượng) | Bảng benchmark ⭐ |
| 3.9 | Chốt backend, ghi vào `configs/recognize.yaml` | Config chính thức |

**Cổng C — chỉ tiêu chặn: độ chính xác ≥ 95 % với người đã đăng ký.**
**Cổng D:** Chương 2 §Trích xuất đặc trưng + **Chương 4 §Bảng so sánh thực nghiệm** (mục quan trọng nhất báo cáo).
**Công cụ:** `training.agent.md` · `skills/latex-visualization` (vẽ ROC, bảng) · `prompts/eda.prompt.md`
