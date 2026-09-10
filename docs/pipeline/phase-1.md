# PHASE 1 — Dữ liệu khuôn mặt

**Tuần 2 (22–28/07/2026)** · ⚠️ **Còn mở** — phần không cần camera đã xong; các bước thu dữ liệu
(1.3, 1.6, 1.7, 1.8, 1.10–1.13) chưa làm.

> Tệp này là **kế hoạch** của Phase 1, tách ra từ `CLAUDE.md` §5.
> Bộ quy tắc R1–R43 và cấu trúc 4 cổng nằm ở `CLAUDE.md`, **luôn áp dụng**, không lặp lại ở đây.
> Ràng buộc đạo đức dữ liệu **R28, R28b, R28c** chi phối toàn bộ Phase này — đọc lại trước khi thu.
> **Trạng thái thực tế** ở [`docs/trang-thai.md`](../trang-thai.md), không ghi mốc thời gian ở đây.

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 1.1 | Thiết kế quy ước dữ liệu: `data/raw/<user_id>/<user_id>_<condition>_<idx>.jpg`; `condition` ∈ {frontal, left, right, up, down} × {bright, dim} | Tài liệu quy ước |
| 1.2 | Viết `scripts/collect_faces.py` — chụp có hướng dẫn từng tư thế, đếm đủ số ảnh/điều kiện | Script thu thập |
| 1.3 | Thu thập **gallery: 2–3 người** (bản thân + gia đình), tối thiểu **100 ảnh/người**, phủ đủ 5 góc × 2 mức sáng | `data/raw/` |
| 1.4 | Ghi nhận danh sách người tham gia + ngày đồng ý vào `docs/nguoi-tham-gia.md` | Bảng ghi nhận |
| 1.5 | **Tập impostor ①**: tải LFW, lấy **≥ 100 danh tính** → `data/impostor/lfw_original/` | Impostor quy mô lớn |
| 1.6 | **Tập impostor ③**: mời **5–7 người quen** (bạn cùng lớp/người quen) đứng trước **chính camera hệ thống** ~1 phút, ≥ 20 ảnh/người, cùng điều kiện góc & ánh sáng như gallery → `data/impostor/indomain/` | Impostor in-domain |
| 1.7 | **Đo đặc trưng miền dữ liệu** của camera thật: phân bố kích thước bbox (px), độ nét (Laplacian var), độ sáng, nhiệt độ màu, mức nhiễu — từ `data/raw/` + `data/impostor/indomain/` | `results/domain_stats_*.json` |
| 1.8 | **Tập impostor ②**: viết `scripts/adapt_domain.py` — xử lý LFW cho khớp thống kê đo ở 1.7 → `data/impostor/lfw_adapted/`. **Kiểm chứng**: phân bố độ nét/độ sáng của LFW đã adapt phải chồng lấn với in-domain | LFW domain-adapted |
| 1.9 | Viết `scripts/preprocess.py` — detect → crop → align 5 điểm → resize 112×112 → `data/processed/` (áp dụng **đồng nhất** cho cả 4 nguồn dữ liệu) | Dữ liệu chuẩn hoá |
| 1.10 | Kiểm chất lượng: loại ảnh mờ, ảnh không có mặt, trùng lặp | Báo cáo QC |
| 1.11 | Chia tập: `enroll/val/test` cho gallery; mỗi tập impostor chia đôi `_val` / `_test` không trùng danh tính | `data/splits/*.txt` |
| 1.12 | Thu thập **bộ tấn công**: ≥ 30 ảnh in + ≥ 30 màn hình ĐT + ≥ 30 mẫu live → `data/spoof/` | Bộ test giả mạo |
| 1.13 | Chạy **EDA** — phân bố dữ liệu, tách biệt embedding, so sánh 3 phân bố impostor | `notebooks/01_eda_khuon_mat.ipynb` |

---

## Ba nguồn impostor — vì sao cần cả ba

Bảng tóm tắt nằm ở `CLAUDE.md` §1. Phần lập luận đầy đủ ở đây, vì nó chỉ dùng cho Phase 1 và Phase 3.

- Gallery chỉ 2–3 người → **không thể giữ lại người nhà nào làm "người lạ"** → bắt buộc phải có
  dữ liệu impostor từ ngoài, nếu không thì **không đo được FAR**.
- **LFW** cho **sức mạnh thống kê** (≥ 100 danh tính) nhưng là ảnh web, khác điều kiện camera thật.
- **Domain adaptation** thu hẹp khoảng cách đó.
- **In-domain 5–7 người** **kiểm chứng** rằng bước adaptation là hợp lệ. Cỡ mẫu quá nhỏ để tự nó
  đo được FAR ở mức 1 %, nhưng đủ để phát hiện nếu adaptation sai lệch nghiêm trọng.

⚠️ **In-domain KHÔNG thay thế được LFW.** Với 5–7 danh tính, theo quy tắc số 3, nếu không có mẫu nào
bị chấp nhận sai thì cận trên khoảng tin cậy 95 % của FAR vẫn ~3/7 ≈ 43 %. Tức là in-domain chỉ
**bắt được lỗi nghiêm trọng**, không đo được mức 1 %. Sức mạnh thống kê đến từ LFW.

⚠️ **5–7 người in-domain TUYỆT ĐỐI KHÔNG được đưa vào gallery** — họ là người lạ về mặt hệ thống.

❌ **Không** bổ sung impostor bằng cách trích ảnh người qua đường từ camera an ninh (R28b): vi phạm
quy định dữ liệu cá nhân **và** không dùng được vì thiếu nhãn danh tính.

---

**Cổng C:** gallery 2–3 người × ≥ 100 ảnh · impostor ≥ 100 danh tính LFW (gốc + adapted) +
5–7 người in-domain × ≥ 20 ảnh · adaptation đã kiểm chứng bằng thống kê · mọi ảnh `processed/`
đúng 112×112 · bộ spoof ≥ 90 mẫu.
**Cổng D:** `docs/nhat-ky/tuan-02.md` + Chương 4 §Xây dựng cơ sở dữ liệu khuôn mặt.
**Công cụ:** `prompts/data-pipeline.prompt.md` · `prompts/eda.prompt.md` · `docs/quy-uoc-du-lieu.md`
