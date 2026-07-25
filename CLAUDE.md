# CLAUDE.md — Bộ quy tắc & Pipeline làm việc

> **Đồ án tốt nghiệp**: Nghiên cứu và triển khai hệ thống nhận diện khuôn mặt trên Raspberry Pi 5
> ứng dụng điều khiển thiết bị trong nhà thông minh.
> **SV**: Trần Thanh Long – 25410088 · **GVHD**: ThS. Phan Đình Duy · **Lớp**: AI503.F3.LT.TTNT
>
> File này là **hiến pháp** của repo. Claude Code đọc file này đầu mỗi phiên.
> Phạm vi và chỉ tiêu lấy từ [`docs/DE-CUONG-CHI-TIET.md`](docs/DE-CUONG-CHI-TIET.md) — **không được tự ý mở rộng**.

---

## 0. TL;DR — Đọc 30 giây

1. **Trả lời bằng tiếng Việt.** Thuật ngữ kỹ thuật giữ nguyên tiếng Anh (embedding, anti-spoofing, FPS...).
2. **Không bịa số liệu.** Mọi con số trong báo cáo phải truy được về một file trong `results/`.
3. **Giả lập trước, phần cứng sau.** Code chạy được trên Docker ARM64 rồi mới deploy lên Pi 5.
4. **Không tự mở rộng phạm vi.** Ngoài đề cương = không làm (xem §2.3).
5. **Mỗi Phase có 4 cổng A→B→C→D.** Chưa qua cổng D (tài liệu) thì Phase chưa xong.
6. Cần làm gì → tra bảng **§6 Bản đồ nhanh** để biết dùng agent/skill/prompt nào.
7. **Gemini viết code, Claude thiết kế – kiểm định – viết báo cáo.** Bàn giao qua file, không qua
   hội thoại: đặc tả → code → biên bản review → commit (xem §2.9).

---

## 1. Bối cảnh đề tài (Claude cần nhớ)

| Hạng mục | Giá trị chốt |
|---|---|
| Phần cứng đích | **Raspberry Pi 5, 8 GB RAM** (ARM64), Camera Module / USB Webcam |
| Ngoại vi | Module relay + LED (đèn), LED phát IR (tivi), GPIO |
| Detect | **YOLOv8n-face** (Ultralytics) → export **ONNX / NCNN** |
| Recognize | **So sánh 2 phương án**: (A) `face_recognition`/dlib · (B) **MobileFaceNet/ArcFace ONNX** |
| Anti-spoofing | **MiniFASNet** (Silent Face Anti-Spoofing) |
| Backend/Web | **Python + Flask** (ReactJS = mở rộng) |
| Cảnh báo | **Telegram Bot** + log CSDL |
| Môi trường dev | **Docker ARM64** trên máy cá nhân → Pi 5 thật |
| Gallery (người đăng ký) | **2–3 người** (bản thân + gia đình), **≥ 100 ảnh/người**, nhiều góc/ánh sáng |
| Impostor (đo FAR) | **3 nguồn**: ① LFW gốc ≥ 100 danh tính · ② LFW domain-adapted · ③ **in-domain 5–7 người quen có đồng ý**, ≥ 20 ảnh/người, chụp bằng chính camera hệ thống |
| Anti-spoofing data | ≥ 30 print + ≥ 30 screen + ≥ 30 live |
| Định vị đề tài | **Ứng dụng cá nhân trong hộ gia đình** — chỉ thu thập ảnh của người **đã được thông báo và đồng ý** |
| Thời gian | 15/07/2026 → 23/09/2026 (10 tuần) · Nộp 23–24/09 · Bảo vệ ~10/10/2026 |

### Chỉ tiêu cam kết (KHÔNG được hạ thấp trong báo cáo)

| Chỉ tiêu | Ngưỡng |
|---|---|
| Độ chính xác nhận diện người đã đăng ký | **≥ 95 %** |
| FPS toàn pipeline | **≥ 5 FPS** |
| FPS riêng module detect | **≥ 10 FPS** |
| Độ trễ điều khiển thiết bị | **< 2 giây** |
| Tỉ lệ phát hiện tấn công giả mạo | **≥ 90 %** |

> ⚠️ **Cảnh báo phương pháp — gallery nhỏ (2–3 người)**
> Với gallery chỉ 2–3 người, đạt độ chính xác ≥ 95 % là **dễ một cách giả tạo** — bài toán phân biệt
> 3 danh tính đơn giản hơn nhiều so với 50 danh tính. Do đó:
> 1. **Bắt buộc báo cáo FAR**, không chỉ accuracy trên 3 người nhà.
>    FAR mới là chỉ số phản ánh năng lực thật của hệ thống an ninh.
> 2. **Không so sánh trực tiếp** con số accuracy của đồ án với các công trình dùng gallery lớn.
> 3. **Nêu rõ hạn chế này** ở Chương 4 §4.2 và Chương 5 — hội đồng chắc chắn sẽ hỏi.

### Ba nguồn impostor và vai trò từng nguồn

| Nguồn | Ký hiệu | Cỡ mẫu | Vai trò |
|---|---|---|---|
| LFW gốc | `FAR_lfw` | ≥ 100 danh tính | **Đủ mẫu để đo FAR ở mức 1 %**; so sánh được với tài liệu |
| LFW domain-adapted | `FAR_adapt` | cùng danh tính, đã xử lý cho khớp camera thật | **Ước lượng sát thực tế nhất** — dùng để chốt ngưỡng |
| In-domain (5–7 người quen có đồng ý) | `FAR_indomain` | 5–7 danh tính, ≥ 20 ảnh/người | **Kiểm chứng** rằng domain adaptation là hợp lệ |

**Logic của thiết kế này**: nếu `FAR_adapt ≈ FAR_indomain` thì bước domain adaptation được **kiểm chứng**,
và ta có quyền tin con số `FAR_adapt` đo trên 100+ danh tính. Nếu lệch xa → adaptation chưa đủ tốt,
phải điều chỉnh lại tham số hoặc báo cáo trung thực khoảng chênh lệch.

⚠️ **In-domain KHÔNG thay thế được LFW.** Với 5–7 danh tính, theo quy tắc số 3, nếu không có mẫu nào
bị chấp nhận sai thì cận trên khoảng tin cậy 95 % của FAR vẫn ~3/7 ≈ 43 %. Tức là in-domain chỉ
**bắt được lỗi nghiêm trọng**, không đo được mức 1 %. Sức mạnh thống kê đến từ LFW.

⚠️ **5–7 người in-domain TUYỆT ĐỐI KHÔNG được đưa vào gallery** — họ là người lạ về mặt hệ thống.

---

## 2. BỘ QUY TẮC

### 2.1. Ngôn ngữ & giao tiếp

- **R1.** Mọi phản hồi, comment code, docstring, commit message, tài liệu: **tiếng Việt**.
- **R2.** Giữ nguyên thuật ngữ kỹ thuật tiếng Anh; **không dịch** các từ: embedding, anti-spoofing,
  liveness, threshold, pipeline, FPS, latency, relay, GPIO, inference, ONNX.
- **R3.** Khi viết vào báo cáo: văn phong học thuật, ngôi thứ ba ("hệ thống", "nghiên cứu này"),
  **không dùng "em/tôi/mình"** trong thân báo cáo.
- **R4.** Trả lời ngắn gọn, đi thẳng vấn đề. Không tán dương, không lặp lại câu hỏi.

### 2.2. Tính trung thực của số liệu — QUY TẮC CỨNG

- **R5.** **TUYỆT ĐỐI KHÔNG bịa số liệu thực nghiệm.** Không có số đo → ghi `TBD` hoặc `[CHƯA ĐO]`.
- **R6.** Mọi số trong báo cáo phải **truy vết được** về một file cụ thể trong `results/`.
  Bảng/biểu đồ phải ghi chú nguồn: `Nguồn: results/bench_recognize_20260812.csv`.
- **R7.** Nếu kết quả **không đạt chỉ tiêu §1** → **báo cáo đúng sự thật**, phân tích nguyên nhân,
  đề xuất khắc phục. Không được sửa số, không được đổi ngưỡng để "cho đạt".
- **R8.** Đo hiệu năng phải ghi kèm **ngữ cảnh**: thiết bị (Pi 5 / Docker), độ phân giải input,
  nhiệt độ CPU, có tản nhiệt hay không, số lần lặp, điều kiện ánh sáng.
- **R9.** Mỗi lần đo **≥ 100 frame** (hoặc ≥ 30 s liên tục), báo cáo **trung bình + độ lệch chuẩn**,
  không báo cáo giá trị đơn lẻ tốt nhất.

### 2.3. Phạm vi — cái gì KHÔNG làm

- **R10.** ❌ Không huấn luyện mô hình nhận diện từ đầu. Chỉ dùng **pre-trained + đăng ký bằng embedding**.
- **R11.** ❌ Không làm nhận diện nhiều người trong đám đông / camera tầm xa.
- **R12.** ⚠️ **MQTT là mở rộng** — chỉ làm sau khi Phase 5 (Web & Tích hợp) đã đạt.
- **R13.** ⚠️ **ReactJS là mở rộng** — mặc định web dùng Flask + Jinja2 + HTML/CSS thuần.
- **R14.** Khi Claude thấy một ý tưởng hay nhưng **ngoài đề cương** → **nêu ở mục "Hướng phát triển"**,
  không tự ý implement.

### 2.4. Tái lập (reproducibility)

- **R15.** Mọi script thực nghiệm nhận `--seed` (mặc định `42`) và ghi seed vào output.
- **R16.** Mọi tham số (ngưỡng cosine similarity, conf threshold, IoU, kích thước input...)
  đặt trong `configs/*.yaml`, **không hardcode** trong code.
- **R17.** Mỗi lần chạy benchmark ghi ra `results/<tên>_<YYYYMMDD_HHMM>.{csv,json}` kèm
  file `.meta.json` chứa: commit hash, config đã dùng, thông tin thiết bị, thời gian chạy.
- **R18.** Pin phiên bản thư viện trong `requirements.txt` (`==`, không dùng `>=`).

### 2.5. Code

- **R19.** Python **≥ 3.11**, format bằng **`black`** (line length 100), lint bằng **`ruff`**.
- **R20.** Type hints cho mọi hàm public. Docstring **tiếng Việt** kiểu Google.
- **R21.** Kiến trúc **4 khối** phản ánh trực tiếp vào cây thư mục `src/` (xem §3).
  Mỗi khối là một module độc lập, giao tiếp qua **interface rõ ràng**, không import chéo lung tung.
- **R22.** **Trừu tượng hoá phần cứng**: mọi truy cập GPIO/IR/camera đi qua lớp abstraction có
  **backend `mock`** để chạy được trên Docker/PC không có Pi.
  → `src/actuator/base.py` định nghĩa interface, `gpio_real.py` và `gpio_mock.py` implement.
- **R23.** Không `print()` trong code sản phẩm — dùng `logging` với level phù hợp.
- **R24.** Xử lý lỗi phần cứng phải **fail-safe**: mất camera / lỗi GPIO → log lỗi, giữ thiết bị ở
  trạng thái an toàn (tắt), không crash toàn hệ thống.

### 2.6. Dữ liệu & bảo mật

- **R25.** ❌ **Không commit** vào git: ảnh khuôn mặt, file `.npy` embedding, DB có dữ liệu thật,
  token Telegram, WiFi credentials, model weights > 50 MB.
  → Đã liệt kê trong `.gitignore`. Kiểm tra trước mỗi commit.
- **R26.** Secrets đọc từ **biến môi trường** hoặc `.env` (đã gitignore). Code chỉ đọc `os.environ`.
- **R27.** Dữ liệu khuôn mặt **xử lý cục bộ** — không gửi lên cloud/API bên ngoài. Đây là
  luận điểm khoa học của đề tài (edge AI, quyền riêng tư), phải nhất quán trong code và báo cáo.
- **R28.** Chỉ thu thập ảnh khuôn mặt của người **đã được thông báo rõ mục đích và đồng ý**:
  ① 2–3 thành viên gia đình (gallery), ② 5–7 người quen (tập impostor in-domain).
  Ghi nhận danh sách người tham gia + ngày đồng ý vào `docs/nguoi-tham-gia.md` (dạng bảng đơn giản,
  không cần biểu mẫu phức tạp), nêu trong phần Đạo đức nghiên cứu của báo cáo.
- **R28b.** ❌ **CẤM thu thập hình ảnh khuôn mặt của người không được thông báo và không đồng ý** —
  hàng xóm, người qua đường, ảnh trích từ camera an ninh, ảnh lấy từ mạng xã hội.
  Lý do: (1) trái Nghị định 13/2023/NĐ-CP — ảnh khuôn mặt là dữ liệu cá nhân nhạy cảm;
  (2) mâu thuẫn với luận điểm quyền riêng tư của chính đề tài;
  (3) **vô dụng về kỹ thuật** — không có nhãn danh tính thì không tính được FAR.
- **R28c.** Tập impostor quy mô lớn lấy từ **bộ dữ liệu công khai LFW**, tải về xử lý **cục bộ**.
  Trích dẫn công trình gốc và nêu giấy phép trong báo cáo. **Không phát hành lại** ảnh LFW kèm mã nguồn.

### 2.7. Git

- **R29.** Commit message tiếng Việt, dạng: `<loại>(<phạm vi>): <mô tả>`
  Loại: `feat` `fix` `docs` `exp` `refactor` `chore` `data`
  Ví dụ: `exp(recognize): benchmark dlib vs ArcFace trên Pi 5 — 100 frame`
- **R30.** Nhánh: `main` (ổn định) · `dev` (tích hợp) · `feat/<tên>` · `exp/<tên-thí-nghiệm>`.
- **R31.** **Chỉ commit/push khi được yêu cầu rõ ràng.** Không tự động push.
- **R32.** Mỗi Phase kết thúc → tạo tag `phase-<n>-done`.

### 2.8. Cách Claude làm việc

- **R33.** Trước khi sửa code: đọc file liên quan, **không đoán**.
- **R34.** Thay đổi > 3 file hoặc động vào kiến trúc → **trình bày kế hoạch, chờ duyệt**.
- **R35.** Không chạy lệnh phá huỷ (`rm -rf`, `git reset --hard`, ghi đè `data/`) khi chưa hỏi.
- **R36.** Khi bị chặn bởi thiếu phần cứng → **làm hết phần không phụ thuộc phần cứng**,
  ghi rõ phần nào cần Pi 5 thật, rồi báo cáo.
- **R37.** Không tự ý gọi subagent hoặc workflow trừ khi người dùng yêu cầu.

### 2.9. Phân vai Claude ↔ Gemini — quy trình 5 nhịp

**Gemini viết code. Claude thiết kế, kiểm định và viết báo cáo.**
Hai công cụ **không chia sẻ ngữ cảnh hội thoại**, nên mọi bàn giao đi qua **file trong repo**.

- **R38.** Claude **không viết code sản phẩm** vào `src/`, `tests/`, `scripts/`.
  Claude viết **đặc tả** (`docs/dac-ta/`) và **biên bản review** (`docs/review/`).
  *Ngoại lệ*: sửa vặt < 10 dòng — vẫn phải ghi một dòng vào biên bản review để không mất dấu vết.
- **R39.** Mọi bàn giao qua file, **không qua hội thoại**. Câu trả lời trong phiên chat của Gemini
  không lưu lại được → đặc tả mơ hồ thì **sửa đặc tả rồi commit**, không giải thích miệng.
- **R40.** Code **chưa có biên bản review phán quyết ĐẠT** thì không được commit vào `dev`/`main`.
- **R41.** Người review **không được tự sửa code** — nếu sửa thì không còn ai review bản sửa đó.
  Agent `code-reviewer` cố ý **không có tool `Edit`**.

```
N1 ĐẶC TẢ (Claude/spec-writer) ──▶ docs/dac-ta/P<n>-<nn>-<slug>.md
        ▼
N2 SINH MÃ (Gemini, git worktree riêng, không commit)
        ▼
N3 REVIEW (Claude/code-reviewer) ──▶ docs/review/<mã>.review.md
        ├── 🔴 TRẢ LẠI ──▶ N4 Gemini sửa ──▶ quay lại N3   (trần 2 vòng)
        ▼
N5 ✅ ĐẠT ──▶ commit + gộp nhánh ──▶ Cổng C (đo) ──▶ Cổng D (báo cáo)
```

**Ranh giới ghi file — kiểm được bằng `git diff --name-only`:**

| Vai | Được ghi vào |
|---|---|
| Gemini (cài đặt) | `src/`, `tests/`, `scripts/` |
| Claude · `spec-writer` | `docs/dac-ta/`, `configs/` |
| Claude · `code-reviewer` | `docs/review/` — **chỉ đọc** code |
| Claude · `training` | `results/` |
| Claude · `paper-writer` | `report/`, `docs/nhat-ky/` |

`configs/*.yaml` do Claude giữ vì mọi ngưỡng phải chốt từ `results/` (R7, R16) — không để AI tự chọn.

**Mã việc** `P<Phase>-<nn>-<slug>` xuất hiện nguyên vẹn ở 5 chỗ, tạo chuỗi truy vết:
đặc tả → tên nhánh → biên bản review → commit message → nhật ký tuần.

Ánh xạ vào 4 cổng: **Cổng A** = N1 · **Cổng B** = N2–N5 · **Cổng C** = `training` đo · **Cổng D** = `paper-writer`.

---

## 3. Cấu trúc thư mục chuẩn

```
UIT-AI503.F3.LT.TTNT/
├── CLAUDE.md                        # File này — hiến pháp repo (Claude đọc)
├── GEMINI.md                        # Hiến pháp cài đặt mã nguồn (Gemini đọc) — tự chứa
├── README.md
├── requirements.txt                 # Pin cứng phiên bản (==)
├── .env.example                     # Mẫu biến môi trường (KHÔNG chứa secret thật)
│
├── .claude/
│   ├── agents/                      # Subagent chuyên trách (§4.1)
│   │   ├── onboarding-with-skills.md
│   │   ├── spec-writer.agent.md
│   │   ├── code-reviewer.agent.md
│   │   ├── paper-writer.agent.md
│   │   └── training.agent.md
│   ├── skills/                      # Kỹ năng tái sử dụng (§4.2)
│   │   ├── latex-visualization/SKILL.md
│   │   ├── report-drafting/SKILL.md
│   │   └── academic-editing/SKILL.md
│   ├── prompts/                     # Prompt mẫu tham số hoá (§4.3)
│   │   ├── data-pipeline.prompt.md
│   │   ├── eda.prompt.md
│   │   └── gemini-handoff.prompt.md # Lệnh bàn giao việc cho Gemini (§2.9)
│   └── instructions/                # Chuẩn kỹ thuật bắt buộc (§4.4)
│       ├── python-embedded.instructions.md
│       ├── experiment-protocol.instructions.md
│       ├── code-review.instructions.md
│       ├── hardware-safety.instructions.md
│       └── academic-writing.instructions.md
│
├── docs/
│   ├── DE-CUONG-CHI-TIET.md         # Nguồn sự thật về phạm vi
│   ├── DC DATN ....pdf              # Bản gốc
│   ├── Don DKDA ....docx            # Bản gốc
│   ├── nguoi-tham-gia.md            # Danh sách người tham gia + ngày đồng ý (tự ghi, dạng bảng)
│   ├── spoof-protocol.md            # Quy trình tạo bộ dữ liệu tấn công
│   ├── dac-ta/                      # Đặc tả từng mã việc — Claude viết, Gemini thực thi (§2.9)
│   │   └── P0-01-nen-tang.md
│   ├── review/                      # Biên bản review mã nguồn — Claude viết (§2.9)
│   └── nhat-ky/                     # Nhật ký tuần (tuan-01.md, tuan-02.md, ...)
│
├── configs/                         # TẤT CẢ tham số ở đây (R16)
│   ├── detect.yaml
│   ├── recognize.yaml
│   ├── antispoof.yaml
│   ├── actuator.yaml
│   └── system.yaml
│
├── data/                            # GITIGNORED
│   ├── raw/                         # Gallery: data/raw/<user_id>/*.jpg — 2–3 người nhà
│   ├── impostor/                    # Người lạ — KHÔNG BAO GIỜ vào gallery
│   │   ├── lfw_original/            #   ① LFW gốc, ≥100 danh tính
│   │   ├── lfw_adapted/             #   ② LFW sau domain adaptation
│   │   └── indomain/                #   ③ 5–7 người quen có đồng ý, chụp bằng camera hệ thống
│   ├── processed/                   # Ảnh đã crop/align 112x112 (cả gallery lẫn impostor)
│   ├── embeddings/                  # Vector đặc trưng đã đăng ký (gallery 2–3 người)
│   ├── splits/                      # enroll · val · test · impostor_{lfw,adapt,indomain}_{val,test}
│   └── spoof/                       # Bộ tấn công: print/ · screen/ · live/
│
├── models/                          # GITIGNORED (weights) — kèm models/README.md ghi link tải
│   ├── yolov8n-face.onnx
│   ├── mobilefacenet.onnx
│   └── minifasnet.onnx
│
├── src/
│   ├── capture/                     # KHỐI 1a — camera
│   ├── detector/                    # KHỐI 1b — YOLOv8n-face
│   ├── antispoof/                   # KHỐI 1c — MiniFASNet
│   ├── recognizer/                  # KHỐI 1d — dlib | arcface (2 backend so sánh)
│   ├── decision/                    # KHỐI 2 — quyết định & phân quyền
│   ├── actuator/                    # KHỐI 3 — gpio/ir/mqtt (+ backend mock, R22)
│   ├── monitor/                     # KHỐI 4 — Flask web + Telegram + log DB
│   ├── common/                      # config loader, logging, types dùng chung
│   └── main.py                      # Điểm vào — vòng lặp chính
│
├── scripts/                         # Script CLI: enroll, benchmark, export model, collect data
├── tests/                           # pytest — chạy được KHÔNG cần Pi (dùng backend mock)
│
├── notebooks/                       # EDA, phân tích kết quả
├── results/                         # Output thực nghiệm (R17) — CSV/JSON + .meta.json
│
├── report/                          # Báo cáo LaTeX/Markdown
│   ├── main.tex
│   ├── chapters/
│   ├── figures/                     # Hình sinh từ results/ (KHÔNG vẽ tay số liệu)
│   └── refs.bib
│
├── deploy/
│   ├── Dockerfile.arm64
│   ├── docker-compose.yml
│   └── systemd/faceid.service
│
└── hardware/                        # Sơ đồ đấu nối, ảnh mạch, bảng chân GPIO
```

---

## 4. Tài nguyên trong `.claude/`

### 4.1. Agents — `.claude/agents/`

| File | Gọi khi nào | Nhiệm vụ |
|---|---|---|
| `onboarding-with-skills.md` | **Đầu mỗi phiên làm việc mới**, hoặc khi mất ngữ cảnh | Quét repo, xác định đang ở Phase nào, tổng hợp việc đã/đang/sắp làm, chỉ ra skill/prompt cần dùng tiếp |
| `spec-writer.agent.md` | **Nhịp 1** (Cổng A) — trước mọi hạng mục code | Chuyển một bước trong §5 thành đặc tả có chữ ký hàm, danh sách trắng file, ánh xạ tham số → `configs/`, tiêu chí nghiệm thu chạy được |
| `code-reviewer.agent.md` | **Nhịp 3 và 5** — sau khi Gemini báo xong | Chạy `black`/`ruff`/`pytest` + quét mẫu vi phạm, đối chiếu đặc tả, phân loại lỗi 4 mức, ra phán quyết, ghi `docs/review/` |
| `training.agent.md` | Cổng C của Phase 2, 3, 4, 7 | **Thiết kế giao thức đo**, chạy benchmark, phân tích số liệu, chốt ngưỡng từ ROC, ghi kết quả đúng chuẩn `results/`. *Không tự viết script — viết đặc tả cho Gemini* |
| `paper-writer.agent.md` | Cổng D mỗi Phase & Phase 8 | Viết/cập nhật chương báo cáo từ dữ liệu thật trong `results/`, đúng văn phong học thuật, không bịa số |

> Gọi agent bằng cách nêu rõ tên trong yêu cầu, ví dụ: *"Dùng training agent chạy benchmark Phase 3"*.
>
> **Code do Gemini viết** — xem §2.9 và `.claude/prompts/gemini-handoff.prompt.md`.
> Hiến pháp của Gemini là [`GEMINI.md`](GEMINI.md) ở gốc repo (tự chứa, Gemini không đọc file này).

### 4.2. Skills — `.claude/skills/`

| Skill | Kích hoạt khi | Nội dung |
|---|---|---|
| `latex-visualization` | Cần biểu đồ/bảng/sơ đồ cho báo cáo | Chuẩn vẽ biểu đồ từ `results/`, bảng booktabs, TikZ sơ đồ kiến trúc & đấu nối, quy ước màu/font |
| `report-drafting` | Soạn thảo chương/mục báo cáo | Dàn ý chuẩn từng chương, checklist nội dung, cách chèn số liệu có trích nguồn |
| `academic-editing` | Rà soát, biên tập văn bản đã viết | Sửa văn phong học thuật tiếng Việt, thống nhất thuật ngữ, chuẩn trích dẫn IEEE, checklist trước nộp |

### 4.3. Prompts — `.claude/prompts/`

| Prompt | Dùng cho |
|---|---|
| `data-pipeline.prompt.md` | Phase 1 — thu thập, chuẩn hoá, crop/align, kiểm chất lượng, tách train/test, đăng ký embedding |
| `eda.prompt.md` | Phase 1 & 6 — phân tích thống kê CSDL khuôn mặt và phân tích kết quả benchmark |
| `gemini-handoff.prompt.md` | Mọi Phase — lệnh bàn giao Nhịp 2/Nhịp 4 cho Gemini, quy ước worktree, xử lý sự cố (§2.9) |

### 4.4. Instructions — `.claude/instructions/`

Chuẩn kỹ thuật **luôn áp dụng** khi động vào loại file tương ứng:

| File | Áp dụng cho |
|---|---|
| `python-embedded.instructions.md` | Toàn bộ `src/**/*.py`, `scripts/**/*.py` — Claude tra khi **viết đặc tả**; bản rút gọn cho Gemini nằm trong `GEMINI.md` |
| `experiment-protocol.instructions.md` | `scripts/benchmark*`, mọi thứ ghi vào `results/` |
| `code-review.instructions.md` | Mọi lượt review code — rubric 4 mức, mẫu quét vi phạm, cách viết mục lỗi |
| `hardware-safety.instructions.md` | `src/actuator/**`, `hardware/**` |
| `academic-writing.instructions.md` | `report/**`, `docs/**/*.md` |

---

## 5. PIPELINE — 8 PHASE THỰC HIỆN

### 5.0. Cấu trúc chuẩn của mọi Phase — 4 cổng A→B→C→D

Mỗi Phase **bắt buộc** đi qua 4 cổng, theo đúng thứ tự:

```
  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
  │ CỔNG A  │──▶│ CỔNG B  │──▶│ CỔNG C  │──▶│ CỔNG D  │
  │ CHUẨN BỊ│   │ THỰC THI│   │ KIỂM CHỨNG│ │ TÀI LIỆU│
  └─────────┘   └─────────┘   └─────────┘   └─────────┘
```

| Cổng | Tên | Phải làm gì | Bằng chứng hoàn thành |
|---|---|---|---|
| **A** | Chuẩn bị | Đọc mục tương ứng trong `docs/DE-CUONG-CHI-TIET.md`; liệt kê đầu vào cần có; xác nhận đủ tài nguyên (phần cứng/dữ liệu/model); viết config vào `configs/*.yaml` | Danh sách việc + config đã tạo |
| **B** | Thực thi | Code trên **Docker ARM64 trước**; test bằng backend `mock`; sau đó deploy lên Pi 5 | Code chạy được + `pytest` xanh |
| **C** | Kiểm chứng | Đo số liệu theo `experiment-protocol`; đối chiếu chỉ tiêu §1; ghi ra `results/` | File `results/*.csv` + `.meta.json` |
| **D** | Tài liệu | Cập nhật `docs/nhat-ky/tuan-XX.md`; viết/cập nhật chương báo cáo tương ứng bằng `paper-writer`; tag git `phase-<n>-done` | Chương báo cáo đã cập nhật + tag |

> **Quy tắc chặn**: chưa qua cổng D thì **không được bắt đầu Phase sau**.
> Ngoại lệ duy nhất: Phase 3 và Phase 4 có thể chồng lấn nếu phần cứng chưa về.

---

### PHASE 0 — Khởi tạo & Môi trường
**Tuần 1 (15–21/07/2026)** · Trạng thái: cần hoàn tất trước mọi việc khác

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 0.1 | Tạo cây thư mục theo §3, tạo `.gitignore` (chặn `data/`, `models/*.onnx`, `.env`, `results/*.jpg`) | Repo có cấu trúc chuẩn |
| 0.2 | `requirements.txt` pin cứng: `ultralytics`, `onnxruntime`, `opencv-python`, `numpy`, `flask`, `pyyaml`, `python-telegram-bot`, `pytest`, `black`, `ruff` | File dependency |
| 0.3 | Viết `deploy/Dockerfile.arm64` + `docker-compose.yml` — môi trường giả lập ARM64 | Container build thành công |
| 0.4 | Cài Raspberry Pi OS 64-bit + Python venv trên Pi 5; bật camera; test `libcamera-hello` | Pi 5 sẵn sàng |
| 0.5 | `src/common/config.py` (loader YAML) + `src/common/logging.py` | Module nền tảng |
| 0.6 | Viết `.env.example`, `models/README.md` (link tải weights) | Tài liệu setup |

**Cổng C:** container ARM64 chạy được `python -c "import cv2, onnxruntime"` · Pi 5 mở được camera.
**Cổng D:** `docs/nhat-ky/tuan-01.md` + Chương 3 §Môi trường triển khai (nháp).
**Công cụ:** `onboarding-with-skills` agent · `python-embedded.instructions.md`

---

### PHASE 1 — Dữ liệu khuôn mặt
**Tuần 2 (22–28/07/2026)** · ⬅️ **Đang ở đây (24/07/2026)**

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

> ⚠️ **Vì sao cần cả ba nguồn impostor**
> - Gallery chỉ 2–3 người → **không thể giữ lại người nhà nào làm "người lạ"** → bắt buộc phải có
>   dữ liệu impostor từ ngoài, nếu không thì **không đo được FAR**.
> - **LFW** cho **sức mạnh thống kê** (≥ 100 danh tính) nhưng là ảnh web — khác điều kiện camera thật.
> - **Domain adaptation** thu hẹp khoảng cách đó.
> - **In-domain 5–7 người** **kiểm chứng** rằng bước adaptation là hợp lệ. Cỡ mẫu quá nhỏ để tự nó
>   đo được FAR ở mức 1 %, nhưng đủ để phát hiện nếu adaptation sai lệch nghiêm trọng.
>
> ❌ **Không** bổ sung impostor bằng cách trích ảnh người qua đường từ camera an ninh (R28b) —
> vi phạm quy định dữ liệu cá nhân **và** không dùng được vì thiếu nhãn danh tính.

**Cổng C:** gallery 2–3 người × ≥ 100 ảnh · impostor ≥ 100 danh tính LFW (gốc + adapted) +
5–7 người in-domain × ≥ 20 ảnh · adaptation đã kiểm chứng bằng thống kê · mọi ảnh `processed/`
đúng 112×112 · bộ spoof ≥ 90 mẫu.
**Cổng D:** `docs/nhat-ky/tuan-02.md` + Chương 4 §Xây dựng cơ sở dữ liệu khuôn mặt.
**Công cụ:** `prompts/data-pipeline.prompt.md` · `prompts/eda.prompt.md`

---

### PHASE 2 — Phát hiện khuôn mặt (YOLOv8n-face)
**Tuần 2–3 (22/07–04/08/2026)**

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

---

### PHASE 3 — Nhận diện danh tính & So sánh 2 phương án ⭐
**Tuần 3–5 (29/07–18/08/2026)** · **Đây là đóng góp khoa học chính của đồ án**

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

---

### PHASE 4 — Chống giả mạo (Anti-spoofing)
**Tuần 4–5 (05–18/08/2026)** · có thể chạy song song Phase 3

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

---

### PHASE 5 — Điều khiển thiết bị & Cảnh báo
**Tuần 5–7 (12/08–01/09/2026)**

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

---

### PHASE 6 — Web giám sát & Tích hợp hệ thống
**Tuần 7–8 (26/08–08/09/2026)**

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

---

### PHASE 7 — Kiểm thử toàn hệ thống & Benchmark tổng
**Tuần 8–9 (02–15/09/2026)**

| Bước | Việc cụ thể | Đầu ra |
|---|---|---|
| 7.1 | Viết **kịch bản kiểm thử** chuẩn: 3 tình huống × 2 điều kiện ánh sáng × ≥ 3 khoảng cách (0,5 / 1 / 2 m) | `tests/scenarios.md` |
| 7.2 | **Tình huống 1 — Người hợp lệ**: mỗi người ≥ 20 lượt → tỉ lệ nhận đúng, thời gian phản hồi | Kết quả TH1 |
| 7.3 | **Tình huống 2 — Người lạ**: ≥ 20 lượt → tỉ lệ từ chối đúng + cảnh báo có gửi không | Kết quả TH2 |
| 7.4 | **Tình huống 3 — Tấn công giả mạo**: ảnh in + màn hình ĐT, ≥ 20 lượt mỗi loại | Kết quả TH3 |
| 7.5 | Chạy **ổn định 2 giờ liên tục** — theo dõi rò rỉ bộ nhớ, nhiệt độ, throttling | Log ổn định |
| 7.6 | **Lập bảng benchmark tổng hợp** — đối chiếu từng chỉ tiêu §1 với số đo thực tế: Đạt/Không đạt | Bảng benchmark ⭐ |
| 7.7 | Vẽ toàn bộ biểu đồ cho báo cáo từ `results/` | `report/figures/*` |

**Cổng C:** đủ số liệu cho **cả 5 chỉ tiêu cam kết**, mỗi chỉ tiêu có kết luận Đạt/Không đạt kèm bằng chứng.
**Cổng D:** Chương 4 hoàn chỉnh.
**Công cụ:** `training.agent.md` · `skills/latex-visualization` · `experiment-protocol.instructions.md`

---

### PHASE 8 — Báo cáo, Slide & Bảo vệ
**Tuần 9–10 (09–22/09/2026)** · Nộp **23–24/09** · Bảo vệ **~10/10**

| Bước | Việc cụ thể | Hạn |
|---|---|---|
| 8.1 | Hợp nhất các chương đã viết rải rác ở cổng D → `report/main.tex` (~50 trang) | 12/09 |
| 8.2 | Viết Mở đầu + **Chương 5 Kết luận & Hướng phát triển** (nêu MQTT, ReactJS, nhận diện đa người) | 14/09 |
| 8.3 | Rà soát bằng `academic-editing`: văn phong, thuật ngữ nhất quán, trích dẫn IEEE đầy đủ | 16/09 |
| 8.4 | Kiểm tra **mọi số liệu** trong báo cáo khớp với `results/` (R6) | 17/09 |
| 8.5 | Dọn mã nguồn, viết `README.md` hướng dẫn cài đặt, đẩy GitHub | 18/09 |
| 8.6 | Quay **video demo** (đủ 3 tình huống), làm **slide** (15–20 slide) | 20/09 |
| 8.7 | Gửi GVHD duyệt, chỉnh sửa theo góp ý | 21/09 |
| 8.8 | **Nộp báo cáo** | **23–24/09** |
| 8.9 | Luyện trình bày, chuẩn bị câu hỏi phản biện | 25/09–09/10 |

**Cổng D:** báo cáo + slide + video + repo GitHub công khai.
**Công cụ:** `paper-writer.agent.md` · `skills/report-drafting` · `skills/academic-editing` · `skills/latex-visualization`

---

## 6. Bản đồ nhanh: Việc cần làm → Tài nguyên dùng

| Tôi muốn... | Dùng |
|---|---|
| Bắt đầu phiên làm việc, không nhớ đang ở đâu | agent `onboarding-with-skills` |
| Thu thập / chuẩn hoá dữ liệu khuôn mặt | prompt `data-pipeline` |
| Phân tích thống kê dữ liệu hoặc kết quả | prompt `eda` |
| Export model, chạy benchmark, so sánh 2 phương án | agent `training` + `experiment-protocol.instructions` |
| **Bắt đầu một hạng mục code mới** | agent `spec-writer` → viết `docs/dac-ta/<mã>.md` |
| **Giao code cho Gemini viết** | prompt `gemini-handoff` |
| **Kiểm định code Gemini vừa viết** | agent `code-reviewer` + `code-review.instructions` |
| Tra chuẩn viết code Python cho `src/` | `python-embedded.instructions` (Claude tra khi viết đặc tả) |
| Đấu nối / lập trình GPIO, IR | `hardware-safety.instructions` |
| Vẽ biểu đồ, bảng, sơ đồ cho báo cáo | skill `latex-visualization` |
| Viết một chương báo cáo | agent `paper-writer` + skill `report-drafting` |
| Rà soát văn bản trước khi nộp | skill `academic-editing` |

---

## 7. Checklist trước khi nộp (kiểm 100 %)

- [ ] Mọi số liệu trong báo cáo truy được về file trong `results/`
- [ ] Bảng so sánh 2 phương án nhận diện đầy đủ (Accuracy, FAR, FRR, FPS, latency)
- [ ] Kết quả anti-spoofing tách riêng cho ảnh in và màn hình điện thoại
- [ ] Đủ 5 chỉ tiêu cam kết, mỗi chỉ tiêu có kết luận Đạt / Không đạt
- [ ] Kiểm thử trong ≥ 2 điều kiện ánh sáng
- [ ] Không có secret / ảnh khuôn mặt / weights lớn trong git history
- [ ] `README.md` cho phép người khác dựng lại hệ thống từ đầu
- [ ] Trích dẫn IEEE đầy đủ, không tài liệu tham khảo "mồ côi"
- [ ] Video demo đủ 3 tình huống
- [ ] Danh sách người tham gia + ngày đồng ý đã ghi nhận (`docs/nguoi-tham-gia.md`)
- [ ] **Đã nêu rõ hạn chế gallery 2–3 người** ở Chương 4 §4.2 và Chương 5
- [ ] **Đã báo cáo đủ 3 con số FAR** (`FAR_lfw`, `FAR_adapt`, `FAR_indomain`), không chỉ accuracy
- [ ] Đã trình bày **kết luận kiểm chứng domain adaptation**
- [ ] Đã mô tả **quy trình domain adaptation** đủ chi tiết để tái lập
- [ ] Đã trích dẫn nguồn và giấy phép bộ dữ liệu LFW
- [ ] Đã nêu điều chỉnh phạm vi so với đề cương gốc và lý do
- [ ] Không có ảnh của người chưa đồng ý trong toàn bộ dữ liệu (R28b)

---

## 8. Ghi chú vận hành

- **Vị trí hiện tại (24/07/2026)**: Phase 1 — Dữ liệu khuôn mặt (Tuần 2).
- Cập nhật mục này mỗi khi qua Phase mới.
- Nhật ký tuần lưu ở `docs/nhat-ky/tuan-XX.md`, viết vào **cuối mỗi tuần**, không dồn.
