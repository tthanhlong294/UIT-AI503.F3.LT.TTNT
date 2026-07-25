---
name: eda
description: Prompt mẫu cho phân tích khám phá dữ liệu (EDA) — dùng ở Phase 1 để phân tích cơ sở dữ liệu khuôn mặt, và ở Phase 3/6/7 để phân tích kết quả benchmark. Mọi biểu đồ sinh ra phải dùng được luôn cho báo cáo.
phase: 1, 3, 6, 7
---

# Prompt: Phân tích khám phá dữ liệu (EDA)

> Dùng skill `latex-visualization` cho mọi biểu đồ — hình sinh ra ở đây phải dùng được **trực tiếp**
> trong báo cáo, không vẽ lại.
> Notebook lưu ở `notebooks/`, hình xuất ra `report/figures/`.

---

## PHẦN A — EDA cơ sở dữ liệu khuôn mặt (Phase 1)

### YÊU CẦU

```
Tạo notebook `notebooks/01_eda_khuon_mat.ipynb` phân tích bộ dữ liệu khuôn mặt trong
data/processed/ và data/splits/. Mọi nhận xét viết bằng tiếng Việt, đủ chất lượng để
đưa thẳng vào Chương 4 §4.2 của báo cáo.

## A1. Thống kê mô tả
- Bảng: user_id | tổng ảnh | số ảnh mỗi góc (5 cột) | số ảnh mỗi mức sáng (2 cột)
- Tổng số người, tổng số ảnh, trung bình ± std ảnh/người
- Cảnh báo mất cân bằng: người nào lệch > 30 % so với trung bình

## A2. Biểu đồ phân bố  → report/figures/fig_dataset_dist.pdf
- Cột chồng: số ảnh mỗi người, chia theo góc nhìn
- Cột nhóm: số ảnh theo (góc × mức sáng)

## A3. Chất lượng ảnh  → report/figures/fig_dataset_quality.pdf
- Histogram độ sáng trung bình, tách theo nhãn bright/dim
  (kiểm chứng nhãn điều kiện có đúng không — nếu 2 phân bố chồng nhau thì việc dán nhãn có vấn đề)
- Histogram độ nét (Laplacian variance)
- Boxplot kích thước bbox gốc theo người

## A4. Kiểm chứng domain adaptation  ⭐⭐ (mục mới, quan trọng)
Từ results/domain_stats_*.json, so sánh BA miền dữ liệu: LFW gốc / LFW adapted / in-domain.
- Bảng: kích thước bbox, Laplacian variance, độ sáng, độ tương phản, nhiệt độ màu, mức nhiễu
  → mỗi dòng một miền, mỗi cột một đặc trưng (trung vị + IQR)
- Hình 3 phân bố chồng nhau cho từng đặc trưng → report/figures/fig_domain_adaptation.pdf
- Định lượng khoảng cách bằng Wasserstein distance hoặc KS test:
  d(LFW_gốc, in-domain) phải LỚN HƠN d(LFW_adapted, in-domain) — nếu không thì adaptation vô ích.
- Kết luận rõ ràng: adaptation đã kéo LFW về gần miền thật bao nhiêu phần trăm? Còn lệch ở đâu?
Mục này viết thẳng vào Chương 4 §4.2.

## A5. Phân tích không gian embedding  ⭐ (phần có giá trị khoa học nhất)
Với CẢ HAI backend (dlib và arcface), tính embedding cho data/processed (người nhà) và cả
ba tập impostor:
- Giảm chiều bằng t-SNE và PCA (2D) → scatter: 2–3 người nhà tô màu riêng, in-domain tô màu
  thứ hai, LFW adapted tô xám nhạt làm nền → report/figures/fig_embedding_tsne.pdf
  Hình này trả lời: cụm người nhà có TÁCH BIỆT khỏi đám mây impostor không? Người in-domain
  có nằm lẫn trong đám mây LFW adapted không (nếu có → adaptation tốt)?
- Ma trận similarity trung bình giữa các người nhà (heatmap). Với 2–3 người thì ma trận nhỏ,
  nhưng nếu là người thân ruột thịt có nét giống nhau thì similarity cao là phát hiện đáng ghi nhận.
- NĂM phân bố similarity trên cùng một histogram:
  (1) genuine — cùng người nhà
  (2) impostor nội bộ — giữa 2–3 người nhà
  (3) impostor LFW gốc
  (4) impostor LFW adapted        ← quyết định ngưỡng
  (5) impostor in-domain          ← kiểm chứng (4)
  Tính độ chồng lấn của (1) với từng nhóm (3)(4)(5).
  Kỳ vọng: (4) và (5) chồng lấn nhau; (3) lệch về phía similarity thấp hơn (dễ phân biệt hơn).
- Nhận xét: khoảng cách giữa genuine và (4) có đủ rộng để đặt ngưỡng an toàn không?

## A6. Kiểm tra tập chia
- Xác nhận cả 2–3 người nhà có mặt ở enroll, val VÀ test
- ⛔ Xác nhận KHÔNG danh tính LFW nào và KHÔNG pid in-domain nào lọt vào enroll
- Xác nhận mọi cặp *_val / *_test không trùng danh tính
- Xác nhận lfw_original và lfw_adapted chia cùng danh tính về cùng phía
- Kiểm tra phân tầng: tỉ lệ góc/ánh sáng ở các tập có tương đồng không

## A7. Kết luận EDA
Viết 5–7 gạch đầu dòng, mỗi ý là một phát hiện CÓ SỐ LIỆU kèm hàm ý cho các Phase sau.
Ví dụ: "Similarity nội bộ trung bình của người `mai` chỉ đạt 0,68 (thấp nhất trong 3 người),
nguyên nhân có thể do ảnh chụp ở góc `up` bị che một phần trán → cần thu bổ sung."

BẮT BUỘC có một gạch đầu dòng đánh giá HẠN CHẾ CỠ MẪU:
gallery chỉ 2–3 người nên bài toán phân biệt danh tính đơn giản hơn đáng kể so với hệ thống
thực tế; do đó accuracy KHÔNG phải chỉ số đại diện, phải dựa vào FAR đo trên tập impostor LFW.
Câu này dùng thẳng cho Chương 4 §4.2 và Chương 5.
```

---

## PHẦN B — Phân tích kết quả benchmark nhận diện (Phase 3)

### YÊU CẦU

```
Tạo notebook `notebooks/02_phan_tich_nhan_dien.ipynb` phân tích results/bench_recognize_*.csv.
Đầu ra phải đủ để viết Chương 4 §4.6 — mục quan trọng nhất của báo cáo.

## B1. Bảng so sánh chính  ⭐
Bảng đầy đủ cho 2 backend: Accuracy, Precision, Recall, F1, FAR, FRR, EER,
FPS (mean ± std), latency p50/p95, số chiều embedding, dung lượng model.
Thêm dòng "Chỉ tiêu đề cương" để đối chiếu. Xuất sẵn dạng LaTeX booktabs.

BẮT BUỘC tách FAR thành 4 cột riêng, KHÔNG gộp:
- FAR_noibo     — nhầm lẫn giữa 2–3 người nhà với nhau
- FAR_lfw       — LFW gốc (baseline, so sánh được với tài liệu)
- FAR_adapt     — LFW domain-adapted   ← CHỈ SỐ ĐẠI DIỆN, dùng chốt ngưỡng
- FAR_indomain  — 5–7 người quen thật  ← kiểm chứng FAR_adapt, kèm khoảng tin cậy 95%
Ghi chú dưới bảng: với gallery 2–3 người, accuracy cao là điều dự kiến;
FAR_adapt mới phản ánh năng lực an ninh thật của hệ thống.

## B1b. Kiểm chứng domain adaptation  ⭐
- Đặt FAR_adapt và FAR_indomain cạnh nhau tại CÙNG ngưỡng đã chốt
- Tính khoảng tin cậy 95% cho FAR_indomain bằng Clopper–Pearson, n = SỐ DANH TÍNH (5–7),
  không phải số ảnh
- Kết luận: FAR_adapt có nằm trong khoảng đó không?
  + Có  → adaptation hợp lệ, FAR_adapt là số báo cáo chính
  + Không → nêu trung thực khoảng chênh, phân tích nguyên nhân
- Nêu rõ: với n = 5–7 danh tính, khoảng tin cậy rất rộng, nên đây là phép KIỂM CHỨNG
  chứ không phải phép đo chính xác. Câu này bắt buộc có trong báo cáo.

## B2. Đường cong ROC / DET  → report/figures/fig_roc_recognize.pdf
- ROC 2 backend trên cùng hệ trục, ghi AUC và đánh dấu điểm EER
- Đường FAR/FRR theo ngưỡng, đánh dấu điểm cắt → report/figures/fig_far_frr.pdf
- Hình riêng: với BACKEND ĐÃ CHỌN, vẽ 3 đường ROC ứng với 3 tập impostor
  (lfw gốc / lfw adapted / in-domain) trên cùng hệ trục
  → report/figures/fig_roc_domain.pdf
  Khoảng cách giữa đường "lfw gốc" và "lfw adapted" chính là TÁC ĐỘNG ĐỊNH LƯỢNG của domain gap.
  Đây là một trong những hình có giá trị nhất của báo cáo — cho thấy nếu chỉ đánh giá trên LFW gốc
  thì kết quả sẽ lạc quan hơn thực tế bao nhiêu.

## B3. Ma trận nhầm lẫn  → report/figures/fig_confusion.pdf
Heatmap cho backend được chọn, gồm 2–3 người nhà + một lớp gộp "người lạ (LFW)".
Ma trận nhỏ (3×3 hoặc 4×4) nên trình bày đầy đủ số đếm tuyệt đối, không chỉ tỉ lệ.
Phân tích: lỗi chủ yếu là nhầm người-nhà-với-người-nhà hay nhận-người-lạ-thành-người-nhà?
Loại lỗi thứ hai nguy hiểm hơn nhiều với hệ thống điều khiển thiết bị.

## B4. Phân tích theo điều kiện
Độ chính xác phân theo: góc nhìn / mức sáng / khoảng cách.
→ Điều kiện nào hệ thống yếu nhất? Đây là nội dung bàn luận quan trọng.

## B5. Đánh đổi tốc độ – độ chính xác
Scatter: trục x = latency (ms), trục y = accuracy (%), mỗi điểm là một cấu hình.
Vẽ đường Pareto. Đánh dấu vùng thoả mãn CẢ HAI chỉ tiêu (≥95 % và ≥5 FPS).

## B6. Kiểm định thống kê
Chênh lệch giữa 2 backend có ý nghĩa thống kê không?
- Accuracy: McNemar test trên cùng tập test
- Latency: Mann–Whitney U test (không giả định phân phối chuẩn)
Báo cáo p-value. Nếu p ≥ 0,05 → phải viết trong báo cáo là "chênh lệch chưa có ý nghĩa thống kê",
không được kết luận backend này tốt hơn.

## B7. Kết luận chọn phương án
Viết đoạn kết luận theo mẫu: chọn <backend> vì <lý do định lượng 1>, <lý do định lượng 2>,
chấp nhận đánh đổi <nhược điểm>. Đoạn này dùng thẳng cho báo cáo.
```

---

## PHẦN C — Phân tích anti-spoofing (Phase 4)

### YÊU CẦU

```
Tạo notebook `notebooks/03_phan_tich_antispoof.ipynb` từ results/bench_antispoof_*.csv.

## C1. Bảng kết quả tách theo loại tấn công
| Loại tấn công | Số mẫu | APCER (%) | Ghi chú |
| Ảnh in — giấy thường | | | |
| Ảnh in — giấy ảnh | | | |
| Màn hình — thiết bị 1 | | | |
| Màn hình — thiết bị 2 | | | |
| **Tổng hợp** | | | so với chỉ tiêu ≥ 90 % phát hiện |
Kèm BPCER trên tập live và ACER tổng.

## C2. Đường cong APCER/BPCER theo ngưỡng  → report/figures/fig_antispoof_threshold.pdf
Đánh dấu ngưỡng đã chọn, giải thích vì sao ưu tiên giảm APCER.

## C3. Phân tích mẫu lọt (false negative)
Liệt kê các mẫu tấn công KHÔNG bị phát hiện, tìm đặc điểm chung
(khoảng cách? độ sáng? chất liệu?). Đây là nội dung bàn luận có giá trị.

## C4. Chi phí hiệu năng
So sánh FPS pipeline có/không anti-spoofing → report/figures/fig_antispoof_cost.pdf
```

---

## PHẦN D — Phân tích hiệu năng hệ thống (Phase 6–7)

### YÊU CẦU

```
Tạo notebook `notebooks/04_phan_tich_he_thong.ipynb`.

## D1. Phân rã độ trễ theo khâu  → report/figures/fig_latency_breakdown.pdf
Cột chồng: capture / detect / antispoof / recognize / decision / actuate.
Chỉ ra nút thắt. Đối chiếu tổng với chỉ tiêu < 2 s.

## D2. Ổn định theo thời gian  → report/figures/fig_stability.pdf
Từ results/stability_*.csv (chạy 2 giờ liên tục):
- FPS theo thời gian (trục y trái) + nhiệt độ CPU (trục y phải)
- Đánh dấu thời điểm throttling nếu có
- RAM sử dụng theo thời gian → phát hiện rò rỉ bộ nhớ

## D3. Kết quả 3 kịch bản kiểm thử
Bảng: kịch bản × điều kiện ánh sáng × khoảng cách → tỉ lệ thành công.
Heatmap trực quan hoá → report/figures/fig_scenario_matrix.pdf

## D4. Bảng đối chiếu 5 chỉ tiêu cam kết  ⭐
| Chỉ tiêu | Ngưỡng | Đạt được | Kết luận | File nguồn |
Dùng thẳng cho Chương 5.
```

---

## Nguyên tắc chung khi làm EDA

1. **Mỗi biểu đồ phải trả lời một câu hỏi cụ thể.** Không vẽ vì "cho đẹp".
2. **Mỗi ô notebook có markdown giải thích** đang phân tích gì và phát hiện được gì.
3. **Không kết luận vượt quá dữ liệu.** Gallery chỉ **2–3 người** → mọi nhận định về độ chính xác
   phải kèm cảnh báo về khả năng khái quát hoá, và phải đối chiếu với FAR đo trên tập impostor LFW.
4. **Ghi rõ file nguồn** ở đầu mỗi phần: `Dữ liệu: results/bench_recognize_20260812_1430.csv`.
5. **Notebook phải chạy lại được từ đầu** (Restart & Run All) — không phụ thuộc trạng thái ô đã chạy trước.
6. **Xuất hình bằng `plot_style.luu()`** để định dạng đồng nhất với báo cáo.
7. **Kết quả bất ngờ thì điều tra**, đừng bỏ qua — đó thường là nội dung bàn luận hay nhất.
