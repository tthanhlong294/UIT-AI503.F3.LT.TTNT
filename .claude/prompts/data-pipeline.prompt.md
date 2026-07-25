---
name: data-pipeline
description: Prompt mẫu cho toàn bộ pipeline dữ liệu khuôn mặt — thu thập, chuẩn hoá, kiểm chất lượng, chia tập, đăng ký embedding và xây bộ tấn công giả mạo. Dùng ở Phase 1.
phase: 1
---

# Prompt: Pipeline dữ liệu khuôn mặt

> Sao chép phần **YÊU CẦU** bên dưới, điền tham số trong `<>`, gửi cho Claude.
> Luôn tuân thủ `CLAUDE.md` §2.6 (dữ liệu & bảo mật) và `.claude/instructions/python-embedded.instructions.md`.

---

## Bối cảnh cố định (Claude cần biết)

### Bốn nguồn dữ liệu và vai trò

| Nguồn | Thư mục | Quy mô | Vai trò |
|---|---|---|---|
| **Gallery** — bản thân + gia đình | `data/raw/` | **2–3 người**, ≥ 100 ảnh/người | Người được cấp quyền điều khiển |
| **Impostor ①** — LFW gốc | `data/impostor/lfw_original/` | ≥ 100 danh tính | Đo FAR với cỡ mẫu đủ lớn |
| **Impostor ②** — LFW domain-adapted | `data/impostor/lfw_adapted/` | cùng danh tính ① | Ước lượng FAR sát điều kiện thật |
| **Impostor ③** — in-domain | `data/impostor/indomain/` | **5–7 người quen có đồng ý**, ≥ 20 ảnh/người | Kiểm chứng bước adaptation |

- Đề tài định vị là **ứng dụng cá nhân trong hộ gia đình**.
- ⛔ **Chỉ thu ảnh của người đã được thông báo mục đích và đồng ý.** Cấm trích ảnh người qua đường
  từ camera an ninh, ảnh mạng xã hội, hoặc bất kỳ nguồn nào chủ thể không biết (R28b).
- ⛔ **5–7 người in-domain KHÔNG BAO GIỜ vào gallery** — về mặt hệ thống họ là người lạ.
- **Thư mục**: 4 nguồn trên → `data/processed/` → `data/embeddings/`; bộ tấn công ở `data/spoof/`.
- **Toàn bộ `data/` bị gitignore** — không bao giờ commit ảnh khuôn mặt (R25).
- **Ảnh chuẩn hoá**: crop theo bbox nới rộng 20 %, align theo 5 landmark, resize **112 × 112**, RGB.
- Mọi tham số đặt trong `configs/data.yaml`, không hardcode (R16).

### Quy ước đặt tên file

```
data/raw/<user_id>/<user_id>_<goc>_<sang>_<idx>.jpg

user_id : chuỗi không dấu, viết thường, ví dụ  long, mai, hung
goc     : frontal | left | right | up | down
sang    : bright | dim
idx     : số thứ tự 3 chữ số, 001..NNN

Ví dụ:  data/raw/long/long_frontal_bright_001.jpg
```

```
data/spoof/<loai>/<user_id>_<loai>_<idx>.jpg
loai : print | screen | live
```

```
data/impostor/lfw_original/<lfw_identity>/<lfw_identity>_<idx>.jpg   # giữ nguyên cấu trúc LFW
data/impostor/lfw_adapted/<lfw_identity>/<lfw_identity>_<idx>.jpg    # đối ứng 1-1 với bản gốc
data/impostor/indomain/<pid>/<pid>_<goc>_<sang>_<idx>.jpg            # pid: p01, p02, ... (ẩn danh)
```

> Người in-domain đặt mã ẩn danh `p01…p07`, **không dùng tên thật** trong đường dẫn hay metadata —
> giảm rủi ro lộ danh tính nếu dữ liệu vô tình bị chia sẻ.

---

## YÊU CẦU — Bước 1.2: Script thu thập dữ liệu

```
Viết `scripts/collect_faces.py` để thu thập ảnh khuôn mặt có hướng dẫn.

Yêu cầu:
- CLI: --user-id, --output-dir (mặc định data/raw), --camera <index|libcamera>,
       --per-condition <số ảnh mỗi điều kiện, mặc định 5>, --delay <giây giữa 2 ảnh>
- Lần lượt hướng dẫn người dùng qua 10 điều kiện (5 góc × 2 mức sáng),
  hiển thị chỉ dẫn tiếng Việt trên khung hình OpenCV, đếm ngược trước khi chụp.
- Chỉ lưu ảnh khi YOLOv8n-face phát hiện ĐÚNG 1 khuôn mặt với conf ≥ ngưỡng trong configs/data.yaml.
- Từ chối và báo lý do nếu: không có mặt / nhiều mặt / ảnh mờ (Laplacian variance < ngưỡng)
  / bbox quá nhỏ (< 100 px cạnh ngắn).
- Đặt tên file theo đúng quy ước ở trên, tự tăng idx nếu file đã tồn tại.
- Ghi `data/raw/<user_id>/metadata.json`: thời gian, camera, độ phân giải, số ảnh mỗi điều kiện.
- Chạy được cả trên Docker (đọc video file thay camera qua --source <đường dẫn>) lẫn Pi 5.
- Dùng logging, không print. Type hints + docstring tiếng Việt.
```

---

## YÊU CẦU — Bước 1.5: Tiền xử lý & chuẩn hoá

```
Viết `scripts/preprocess.py` chuẩn hoá ảnh từ data/raw sang data/processed.

Pipeline mỗi ảnh:
1. Đọc ảnh, chuyển RGB.
2. Detect bằng YOLOv8n-face → lấy bbox conf cao nhất + 5 landmark.
3. Bỏ qua ảnh không có mặt hoặc có > 1 mặt, ghi vào báo cáo loại bỏ.
4. Align: dùng similarity transform đưa 5 landmark về vị trí chuẩn ArcFace 112×112.
5. Lưu `data/processed/<user_id>/<tên gốc>.jpg`, chất lượng JPEG 95.

Yêu cầu bổ sung:
- CLI: --input, --output, --config configs/data.yaml, --workers <số tiến trình>, --dry-run
- Xuất `results/preprocess_report_<YYYYMMDD_HHMM>.csv`: file gốc, trạng thái (ok/no_face/multi_face/blurry),
  conf, kích thước bbox, độ nét (Laplacian variance).
- In bảng tóm tắt cuối: tổng ảnh, số ảnh giữ lại, số bị loại theo từng lý do, tỉ lệ % mỗi người.
- Idempotent: chạy lại không xử lý lại ảnh đã có output (trừ khi --force).
```

---

## YÊU CẦU — Bước 1.6: Kiểm chất lượng (QC)

```
Viết `scripts/qc_dataset.py` kiểm chất lượng bộ dữ liệu đã chuẩn hoá.

Kiểm tra và báo cáo:
1. Cân bằng: số ảnh mỗi người, mỗi góc, mỗi mức sáng — cảnh báo nếu lệch > 30% so với trung bình.
2. Trùng lặp: phát hiện ảnh gần giống nhau (perceptual hash hoặc cosine similarity embedding > 0,99).
3. Nhãn sai: tính embedding tất cả ảnh, với mỗi người tìm ảnh có similarity với centroid của
   chính người đó THẤP hơn similarity với centroid người khác → nghi ngờ gán nhầm nhãn.
4. Chất lượng ảnh: độ nét, độ sáng trung bình, độ tương phản — liệt kê 10 ảnh tệ nhất.
5. Kích thước bbox gốc: cảnh báo ảnh có mặt quá nhỏ.

Xuất `results/qc_report_<YYYYMMDD_HHMM>.json` + bảng tóm tắt Markdown in ra màn hình.
KHÔNG tự động xoá ảnh — chỉ liệt kê danh sách đề xuất, người dùng tự quyết định.
```

---

## YÊU CẦU — Bước 1.5: Tập impostor ① — LFW gốc

```
Viết `scripts/prepare_lfw.py` chuẩn bị tập người lạ quy mô lớn để đo FAR.

Bối cảnh: gallery chỉ có 2–3 người nên KHÔNG THỂ giữ lại người nhà nào làm "người lạ".
Không có tập impostor thì không đo được FAR — chỉ số quan trọng nhất của hệ thống an ninh.

Yêu cầu:
- Tải LFW (sklearn.datasets.fetch_lfw_people hoặc tải trực tiếp từ vis-www.cs.umass.edu/lfw),
  lưu vào data/impostor/lfw_original/. Nếu đã có sẵn thì bỏ qua bước tải.
- Lấy ≥ 100 danh tính khác nhau, mỗi danh tính 1–2 ảnh (ưu tiên danh tính có ≥ 2 ảnh).
- Chọn ngẫu nhiên có --seed 42 để tái lập được.
- Ghi nhận phân bố giới tính/độ tuổi ước lượng vào metadata (LFW lệch về nam giới da trắng —
  đây là bias đã được ghi nhận trong tài liệu, PHẢI nêu trong phần hạn chế của báo cáo).
- Ghi data/impostor/lfw_original/metadata.json: nguồn, phiên bản, URL, giấy phép,
  số danh tính, số ảnh, seed, ngày tải.

LƯU Ý PHÁP LÝ/ĐẠO ĐỨC: LFW là bộ dữ liệu công khai cho mục đích nghiên cứu.
Xử lý hoàn toàn cục bộ. Báo cáo phải trích dẫn công trình gốc và nêu giấy phép.
KHÔNG phát hành lại ảnh LFW kèm mã nguồn.
```

---

## YÊU CẦU — Bước 1.6: Tập impostor ③ — in-domain

```
Mở rộng `scripts/collect_faces.py` thêm chế độ thu thập impostor in-domain.

Bối cảnh: LFW là ảnh web (máy ảnh chuyên nghiệp, đủ mọi bối cảnh), KHÁC hẳn điều kiện camera
của hệ thống (người đứng cách 0,5–2 m, đèn LED trong nhà, webcam độ phân giải thấp).
Khoảng cách miền dữ liệu này khiến FAR đo trên LFW có thể lạc quan hơn thực tế.
Tập in-domain dùng để KIỂM CHỨNG điều đó.

Yêu cầu:
- CLI: --mode impostor --pid p01 (mã ẩn danh, KHÔNG dùng tên thật)
- Thu 5–7 người quen ĐÃ ĐỒNG Ý (bạn cùng lớp, người quen), mỗi người ≥ 20 ảnh, chỉ ~1 phút/người.
- Chụp bằng CHÍNH camera của hệ thống, ở CÙNG điều kiện với gallery:
  cùng vị trí đặt camera, cùng khoảng cách, cùng nguồn sáng, phủ được 5 góc × 2 mức sáng.
  Điều kiện phải giống nhau, nếu không thì phép so sánh mất ý nghĩa.
- Lưu vào data/impostor/indomain/<pid>/
- Ghi data/impostor/indomain/metadata.json: số người, số ảnh mỗi người, ngày thu,
  điều kiện chụp, xác nhận đã có đồng ý (true/false cho từng pid).
- Script PHẢI từ chối chạy nếu chưa đánh dấu đã có đồng ý.

⛔ KHÔNG BAO GIỜ đưa các pid này vào gallery hoặc tập enroll — về mặt hệ thống họ là người lạ.
   Script split_dataset.py phải kiểm tra và báo lỗi nếu vi phạm.
```

---

## YÊU CẦU — Bước 1.7 + 1.8: Domain adaptation cho LFW ⭐

```
Viết `scripts/measure_domain.py` và `scripts/adapt_domain.py`.

--- 1.7: measure_domain.py — đo đặc trưng miền dữ liệu thật ---
Từ data/raw/ và data/impostor/indomain/, đo và lưu results/domain_stats_<YYYYMMDD_HHMM>.json:
- Phân bố kích thước bbox khuôn mặt (px): min/p25/median/p75/max
- Độ nét: Laplacian variance — histogram + các phân vị
- Độ sáng trung bình và độ tương phản (kênh Y)
- Nhiệt độ màu ước lượng (tỉ lệ kênh R/B) — đèn LED trong nhà thường ~3000–4000K
- Mức nhiễu: độ lệch chuẩn của vùng phẳng (dùng high-pass filter)
- Nén JPEG: chất lượng ước lượng nếu ảnh từ webcam

Làm tương tự cho data/impostor/lfw_original/ để thấy KHOẢNG CÁCH giữa hai miền.
In bảng so sánh 2 cột (LFW gốc vs in-domain) — đây là hình/bảng cho báo cáo Ch.4 §4.2.

--- 1.8: adapt_domain.py — thu hẹp khoảng cách ---
Biến đổi ảnh LFW cho khớp thống kê đo được, theo thứ tự:
1. Hạ độ phân giải: resize xuống kích thước bbox median của miền thật, rồi upscale lại 112×112
   (mô phỏng mất chi tiết khi chụp xa) — bước quan trọng nhất
2. Motion blur / Gaussian blur nhẹ, cường độ chỉnh sao cho Laplacian variance khớp phân bố thật
3. Dịch nhiệt độ màu về đèn LED trong nhà
4. Điều chỉnh gamma/độ sáng cho khớp histogram độ sáng thật
5. Thêm nhiễu cảm biến (Gaussian + shot noise) khớp mức nhiễu đo được
6. Nén JPEG ở mức chất lượng tương đương webcam

Tham số của từng bước đặt trong configs/domain_adapt.yaml (R16), KHÔNG hardcode.
Mỗi bước bật/tắt được độc lập để làm ablation study.

--- KIỂM CHỨNG (bắt buộc, không được bỏ) ---
Sau khi adapt, chạy lại measure_domain.py trên data/impostor/lfw_adapted/ và kiểm tra:
- Phân bố Laplacian variance của LFW-adapted có CHỒNG LẤN với in-domain không?
- Tương tự cho độ sáng, mức nhiễu.
Định lượng bằng khoảng cách Wasserstein hoặc kiểm định Kolmogorov–Smirnov giữa 2 phân bố.
Xuất hình 3 phân bố chồng nhau (LFW gốc / LFW adapted / in-domain)
  → report/figures/fig_domain_adaptation.pdf

Nếu sau adapt mà phân bố VẪN lệch xa in-domain → tinh chỉnh tham số trong configs và chạy lại.
Ghi lại quá trình tinh chỉnh, đây là nội dung bàn luận cho báo cáo.

LƯU Ý: adaptation chỉ áp dụng cho ẢNH IMPOSTOR LFW. TUYỆT ĐỐI không adapt ảnh gallery
hay ảnh in-domain — chúng đã ở đúng miền rồi.
```

---

## YÊU CẦU — Bước 1.11: Chia tập

```
Viết `scripts/split_dataset.py` chia dữ liệu đã chuẩn hoá.

Nguyên tắc chia (QUAN TRỌNG — đây là bài toán nhận diện open-set, không phải phân loại thường):

A. GALLERY (2–3 người nhà): chia THEO ẢNH, không theo người.
   Cả 2–3 người phải xuất hiện ở CẢ ba tập.
   + enroll (60%): sinh embedding trung bình cho gallery
   + val    (10%): CHỈ dùng để quét và chốt ngưỡng
   + test   (30%): CHỈ dùng để báo cáo kết quả cuối
   + PHÂN TẦNG theo (người × góc × mức sáng)

B. IMPOSTOR — cả ba nguồn, KHÔNG BAO GIỜ vào gallery.
   Mỗi nguồn chia đôi theo DANH TÍNH (không theo ảnh), 50/50:
   + impostor_lfw_val      / impostor_lfw_test
   + impostor_adapt_val    / impostor_adapt_test
   + impostor_indomain_val / impostor_indomain_test
   Ràng buộc: lfw_adapted phải chia GIỐNG HỆT lfw_original (cùng danh tính ở cùng phía)
   — nếu không thì FAR_lfw và FAR_adapt không so sánh được với nhau.

Đầu ra: data/splits/*.txt + data/splits/split_meta.json (kèm --seed 42, R15)

Kiểm tra tự động và BÁO LỖI nếu:
- Có ảnh xuất hiện ở nhiều tập
- Có danh tính impostor xuất hiện ở cả _val và _test của cùng một nguồn
- lfw_original và lfw_adapted chia khác nhau
- Có người nhà nào vắng mặt ở enroll/val/test
- ⛔ CÓ pid IN-DOMAIN NÀO LỌT VÀO enroll — đây là lỗi nghiêm trọng nhất, phải dừng ngay
```

---

## YÊU CẦU — Bước 1.12: Bộ dữ liệu tấn công giả mạo

```
Viết `scripts/collect_spoof.py` và tài liệu `docs/spoof-protocol.md` mô tả quy trình.

Hai loại tấn công bắt buộc:
1. PRINT — in ảnh khuôn mặt ra giấy:
   - ≥ 30 mẫu, ít nhất 2 khổ giấy (A4 và ảnh 10×15), giấy thường + giấy ảnh
   - Chụp ở khoảng cách 0,5 / 1,0 m, có và không có gập/cong giấy
2. SCREEN — hiển thị ảnh/video trên màn hình điện thoại:
   - ≥ 30 mẫu, ít nhất 2 thiết bị khác nhau
   - Độ sáng màn hình: cao và trung bình
   - Cả ảnh tĩnh và video quay khuôn mặt

Script ghi metadata cho từng mẫu: loại tấn công, thiết bị/chất liệu, khoảng cách,
điều kiện ánh sáng, user_id gốc → data/spoof/metadata.csv

Đồng thời thu ≥ 30 mẫu LIVE (người thật) trong cùng điều kiện để đo BPCER.
Tài liệu spoof-protocol.md phải đủ chi tiết để người khác tái lập được bộ tấn công.

LƯU Ý: ảnh dùng để tạo mẫu tấn công CHỈ lấy từ 2–3 người trong gia đình đã đồng ý
(mô phỏng kịch bản kẻ tấn công dùng ảnh của chủ nhà lấy từ mạng xã hội).
KHÔNG in/hiển thị ảnh của người ngoài để làm mẫu tấn công.
```

---

## YÊU CẦU — Bước 3.4: Đăng ký embedding (Gallery)

```
Viết `scripts/enroll.py` sinh gallery embedding từ tập enroll.

- CLI: --backend {dlib,arcface} --splits data/splits/enroll.txt --config configs/recognize.yaml
- Với mỗi người: tính embedding từng ảnh → L2 normalize → lấy TRUNG BÌNH → L2 normalize lại.
- Lưu data/embeddings/<backend>/gallery.npz: mảng embeddings, danh sách user_id, metadata.
- Ghi kèm gallery_meta.json: backend, số người, số ảnh mỗi người, độ phân tán nội bộ
  (similarity trung bình giữa từng ảnh với centroid — cảnh báo nếu < 0,7, dấu hiệu dữ liệu bẩn).
- In ma trận similarity giữa các centroid → cặp người dễ nhầm nhất (quan trọng cho phần bàn luận Ch.4).
  Với gallery 2–3 người, nếu 2 người là thành viên gia đình có nét giống nhau, similarity centroid
  có thể cao bất thường → đây là phát hiện ĐÁNG GIÁ cho báo cáo, phải ghi nhận và phân tích.
- Cảnh báo nếu gallery < 2 người (không thể đánh giá phân biệt danh tính).
```

---

## Tiêu chí hoàn thành Phase 1 (Cổng C)

**Gallery**
- [ ] `data/raw/` có **2–3 người**, mỗi người **≥ 100 ảnh**, phủ đủ 5 góc × 2 mức sáng

**Impostor — cả ba nguồn**
- [ ] `data/impostor/lfw_original/` có **≥ 100 danh tính**
- [ ] `data/impostor/lfw_adapted/` đối ứng 1-1 với bản gốc
- [ ] `data/impostor/indomain/` có **5–7 người** (mã `p01…`), mỗi người **≥ 20 ảnh**
- [ ] In-domain chụp bằng **chính camera hệ thống**, cùng điều kiện với gallery
- [ ] ⛔ **Không pid in-domain nào lọt vào `enroll.txt`**

**Domain adaptation**
- [ ] `results/domain_stats_*.json` có bảng so sánh LFW gốc vs in-domain
- [ ] Sau adapt, phân bố độ nét/độ sáng/nhiễu của LFW-adapted **chồng lấn** với in-domain
      (có số đo Wasserstein hoặc KS test, không nói suông)
- [ ] `report/figures/fig_domain_adaptation.pdf` đã sinh
- [ ] Tham số adaptation nằm trong `configs/domain_adapt.yaml`, không hardcode

**Chung**
- [ ] `data/processed/` toàn bộ ảnh đúng 112 × 112, đã align
- [ ] Tỉ lệ ảnh bị loại ở bước preprocess < 10 %
- [ ] Báo cáo QC không còn cảnh báo mức nghiêm trọng
- [ ] `data/splits/` đủ 3 tập gallery + 6 tập impostor, không trùng lặp
- [ ] `data/spoof/` có ≥ 30 print + ≥ 30 screen + ≥ 30 live
- [ ] `docs/nguoi-tham-gia.md` ghi nhận đủ người tham gia đã đồng ý
- [ ] Metadata LFW ghi rõ nguồn, phiên bản, giấy phép
- [ ] **Không có ảnh của người chưa đồng ý** ở bất kỳ thư mục nào (R28b)
- [ ] EDA đã chạy (xem `.claude/prompts/eda.prompt.md`)
- [ ] Không có ảnh nào lọt vào git (`git ls-files | grep -E '\.(jpg|png)$'` rỗng)
