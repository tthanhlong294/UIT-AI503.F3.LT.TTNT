# CLAUDE.md — Bộ quy tắc & Pipeline làm việc

> **Đồ án tốt nghiệp**: Nghiên cứu và triển khai hệ thống nhận diện khuôn mặt trên Raspberry Pi 5
> ứng dụng điều khiển thiết bị trong nhà thông minh.
> **SV**: Trần Thanh Long – 25410088 · **GVHD**: ThS. Phan Đình Duy · **Lớp**: AI503.F3.LT.TTNT
>
> File này là **hiến pháp** của repo. Claude Code đọc file này đầu mỗi phiên.
> Phạm vi và chỉ tiêu lấy từ [`docs/DE-CUONG-CHI-TIET.md`](docs/DE-CUONG-CHI-TIET.md) — **không được tự ý mở rộng**.

**Bản đồ tài liệu.** File này giữ thứ **hiếm khi đổi**: bối cảnh, chỉ tiêu, bộ quy tắc R1–R43,
phân vai. Thứ **đổi thường xuyên** nằm ở nơi khác, đọc khi cần chứ không nạp mặc định:

| Cần gì | Ở đâu |
|---|---|
| Kế hoạch chi tiết một Phase | [`docs/pipeline/phase-<n>.md`](docs/pipeline/) — chỉ đọc Phase đang làm |
| Đang ở đâu, số đo đã có, việc còn nợ | [`docs/trang-thai.md`](docs/trang-thai.md) |
| Checklist trước khi nộp | [`docs/checklist-nop.md`](docs/checklist-nop.md) — chỉ dùng ở Phase 8 |
| Chuẩn viết mã cho người cài đặt | [`docs/quy-tac-cai-dat.md`](docs/quy-tac-cai-dat.md) — tự chứa |

⚠️ **Đọc ít, đọc đúng.** Làm việc thuộc Phase nào thì đọc **đúng tệp Phase đó**, không đọc các Phase
khác. Vai nào không cần tiến độ thì không đọc `docs/trang-thai.md`. Danh sách đọc của từng vai ghi
ngay trong tệp agent tương ứng ở `.claude/agents/`.

---

## 0. TL;DR — Đọc 30 giây

1. **Trả lời bằng tiếng Việt.** Thuật ngữ kỹ thuật giữ nguyên tiếng Anh (embedding, anti-spoofing, FPS...).
2. **Không bịa số liệu.** Mọi con số trong báo cáo phải truy được về một file trong `results/`.
3. **Giả lập trước, phần cứng sau.** Code chạy được trên Docker ARM64 rồi mới deploy lên Pi 5.
4. **Không tự mở rộng phạm vi.** Ngoài đề cương = không làm (xem §2.3).
5. **Mỗi Phase có 4 cổng A→B→C→D.** Chưa qua cổng D (tài liệu) thì Phase chưa xong.
6. Cần làm gì → tra bảng **§6 Bản đồ nhanh** để biết dùng agent/skill/prompt nào.
7. **Một tác tử chuyên trách viết code, Claude thiết kế – kiểm định – viết báo cáo.** Bàn giao qua file, không qua
   hội thoại: đặc tả → code → biên bản review → commit (xem §2.9).
8. ⭐ **Chỉ `coder` được chạy lệnh** (R42), và chỉ trong phiên riêng của nó. Các vai còn lại —
   `code-reviewer`, `training`, `spec-writer`, `paper-writer`, phiên chính — **không chạy gì**:
   cần số liệu thì đưa **danh sách lệnh rời**, dừng lại, chờ người dùng chạy và dán kết quả về.
9. ⭐ **Đúng một image Docker cho cả dự án: `faceid:arm64`** (R43, §3.1).

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

### Ba nguồn impostor

| Nguồn | Ký hiệu | Cỡ mẫu | Vai trò |
|---|---|---|---|
| LFW gốc | `FAR_lfw` | ≥ 100 danh tính | **Đủ mẫu để đo FAR ở mức 1 %**; so sánh được với tài liệu |
| LFW domain-adapted | `FAR_adapt` | cùng danh tính, đã xử lý cho khớp camera thật | **Ước lượng sát thực tế nhất** — dùng để chốt ngưỡng |
| In-domain (5–7 người quen có đồng ý) | `FAR_indomain` | 5–7 danh tính, ≥ 20 ảnh/người | **Kiểm chứng** rằng domain adaptation là hợp lệ |

**Logic của thiết kế này**: nếu `FAR_adapt ≈ FAR_indomain` thì bước domain adaptation được **kiểm chứng**,
và ta có quyền tin con số `FAR_adapt` đo trên 100+ danh tính. Nếu lệch xa → adaptation chưa đủ tốt,
phải điều chỉnh lại tham số hoặc báo cáo trung thực khoảng chênh lệch.

⚠️ **5–7 người in-domain TUYỆT ĐỐI KHÔNG được đưa vào gallery** — họ là người lạ về mặt hệ thống.

> Lập luận đầy đủ (vì sao in-domain không thay thế được LFW, vì sao cần cả ba) nằm ở
> [`docs/pipeline/phase-1.md`](docs/pipeline/phase-1.md) — chỉ đọc khi làm Phase 1 hoặc Phase 3.

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
- **R44.** ⭐ **Mỗi vai có danh sách đọc đóng**, ghi trong tệp agent của nó ở `.claude/agents/`.
  Đọc hết danh sách đó thì **dừng**, không quét thêm cho "chắc". Đọc rộng không làm chất lượng
  tăng: nó pha loãng chú ý bằng thứ không liên quan và làm mỗi lượt đắt hơn.
  Cụ thể: **không đọc Phase khác Phase đang làm**, và không đọc `docs/trang-thai.md` nếu vai của
  mình không cần tiến độ.

### 2.9. Phân vai người cài đặt ↔ người kiểm định — quy trình 5 nhịp

**Người cài đặt viết code và tự chạy phần kiểm của mình. Claude thiết kế, kiểm định và viết báo cáo.
Khâu kiểm định do người dùng chạy.**
Ba vai **không chia sẻ ngữ cảnh làm việc**, nên mọi bàn giao đi qua **file trong repo**.

- **R38.** Claude **không viết code sản phẩm** vào `src/`, `tests/`, `scripts/`.
  Claude viết **đặc tả** (`docs/dac-ta/`) và **biên bản review** (`docs/review/`).
  *Ngoại lệ*: sửa vặt < 10 dòng — vẫn phải ghi một dòng vào biên bản review để không mất dấu vết.
- **R39.** Mọi bàn giao qua file, **không qua hội thoại**. Câu trả lời trong phiên làm việc của người cài đặt
  không lưu lại được → đặc tả mơ hồ thì **sửa đặc tả rồi commit**, không giải thích miệng.
- **R40.** Code **chưa có biên bản review phán quyết ĐẠT** thì không được commit vào `dev`/`main`.
- **R41.** Người review **không được tự sửa code** — nếu sửa thì không còn ai review bản sửa đó.
  Agent `code-reviewer` cố ý **không có tool `Edit`**.
- **R42.** ⭐ **Chỉ vai `coder` được chạy lệnh, và chỉ để tự kiểm mã của chính nó**: `black`, `ruff`,
  `pytest` trên host, `pytest` trong `faceid:arm64`, `git` chỉ-đọc, và các phép đột biến do đặc tả
  yêu cầu. `coder` chạy trong **phiên riêng** (cửa sổ VS Code khác), không dùng chung ngữ cảnh với
  phiên thiết kế — nó dán kết quả chạy về cho người dùng.
  **Mọi vai còn lại không chạy gì**: `code-reviewer`, `training`, `spec-writer`, `paper-writer` và
  phiên chính đều **đưa danh sách lệnh rời** — mỗi khối đúng một lệnh — rồi **dừng lại chờ** người
  dùng chạy và dán kết quả về. Các vai này chỉ **đọc** kết quả đó.
  *Vẫn được phép cho mọi vai*: `git` chỉ-đọc (`log`, `status`, `diff`, `show`) và các tool đọc file.
  **Không vai nào** được `git commit`/`push`, dựng image Docker mới, hay chạy `pip install`.
  ⚠️ Ranh giới chịu lực: **người viết mã không được là người chấm mã**. `coder` chạy lệnh trên mã
  của chính nó là **tự kiểm**, không phải kiểm định; số liệu vào biên bản review phải đến từ lượt
  chạy của người dùng.
- **R43.** ⭐ **Toàn dự án dùng đúng MỘT image Docker: `faceid:arm64`.**
  Cấm cờ `-t` với tên khác, cấm image tạm cho một mã việc, cấm để `docker compose` tự đặt tên.
  Chỉ dựng lại image khi `requirements.txt` hoặc `deploy/Dockerfile.arm64` đổi — mã nguồn được gắn
  vào container bằng `-v` nên sửa code **không** cần dựng lại.

```
N1 ĐẶC TẢ (Claude/spec-writer) ──▶ docs/dac-ta/P<n>-<nn>-<slug>.md
        ▼
N2 SINH MÃ (agent coder, phiên riêng, nhánh feat/<mã>, không commit)
   └─▶ tự chạy §9 đặc tả: black · ruff · pytest host · pytest faceid:arm64 · git status
       · các phép đột biến ──▶ đỏ thì sửa rồi chạy lại ──▶ dán kết quả về, DỪNG
        ▼
N3 REVIEW (Claude/code-reviewer) ──▶ đưa DANH SÁCH LỆNH RỜI rồi DỪNG
   └─▶ người dùng chạy, dán kết quả ──▶ biên bản docs/review/<mã>.review.md
        ├── 🔴 TRẢ LẠI ──▶ N4 coder sửa và chạy lại ──▶ quay lại N3   (trần 2 vòng)
        ▼
N5 ✅ ĐẠT ──▶ commit + gộp nhánh ──▶ Cổng C (đo) ──▶ Cổng D (báo cáo)
```

**Ranh giới ghi file — kiểm được bằng `git diff --name-only`:**

| Vai | Được ghi vào | Chạy lệnh |
|---|---|---|
| Claude · `coder` | `src/`, `tests/`, `scripts/` | **có** — chỉ để tự kiểm, xem R42 |
| Claude · `spec-writer` | `docs/dac-ta/`, `configs/` | không |
| Claude · `code-reviewer` | `docs/review/` — **chỉ đọc** code | không |
| Claude · `training` | `results/`, `notebooks/` | không |
| Claude · `paper-writer` | `report/`, `docs/nhat-ky/` | không |
| Claude · phiên chính | `.claude/**` — khung quy trình: định nghĩa agent, prompt, instruction; và `CLAUDE.md`, `docs/pipeline/`, `docs/trang-thai.md` | không |
| **Người dùng** | chạy khâu **kiểm định**, và là người duy nhất `git commit`/`push` | — |

`configs/*.yaml` do Claude giữ vì mọi ngưỡng phải chốt từ `results/` (R7, R16) — không để AI tự chọn.

**Vì sao mô hình có hình dạng này.** Hai chế độ hỏng cần chặn, và chúng đối nghịch nhau:

| Chế độ hỏng | Cách chặn |
|---|---|
| Tác tử vừa viết mã vừa chấm mã thì không còn ai đứng ngoài | Khâu **kiểm định** do người dùng chạy; `code-reviewer` không có `Edit`, không có `Bash` |
| Bắt người dùng chạy cả những lệnh máy vụn vặt của vòng sửa mã thì mỗi vòng lặp mất một nhịp chờ | Vòng `black`/`ruff`/`pytest` của N2 do `coder` tự chạy |

Ranh giới nằm ở chỗ: **tự kiểm** là việc của người viết mã, **kiểm định** là việc của người ngoài.
Số liệu đi vào biên bản review — và từ đó đi vào báo cáo — luôn đến từ lượt chạy của người dùng,
đúng tinh thần R5 và R6.

**Lệnh kiểm — quy ước bắt buộc:**

| | Ai đưa lệnh | Ai chạy | Khi nào |
|---|---|---|---|
| Tự kiểm của người cài đặt | đặc tả §9 | `coder`, trong phiên của nó | sau N2 và sau mỗi lần sửa |
| **Chạy thật script sản phẩm** | đặc tả §12b | **người dùng** | sau khi §9 xanh |
| Kiểm định độc lập | `code-reviewer` | **người dùng** | ở N3 |
| Đo hiệu năng | `training` | **người dùng**, trên máy đo | Cổng C |

⭐ Ranh giới giữa dòng 1 và dòng 2 nằm ở **thứ lần chạy sinh ra**, không ở việc ai gõ lệnh:
`black`/`ruff`/`pytest`/đột biến không để lại gì ngoài cây làm việc, nên `coder` chạy để rút ngắn
vòng lặp. Còn lệnh nào **ghi vào `results/`, `models/`, `data/` hay `report/`** thì người dùng chạy —
số liệu đi vào báo cáo phải qua mắt người ít nhất một lần (R5, R6) và `.meta.json` phải ghi đúng
máy đã chạy (R17). `coder` **không** chạy `scripts/export_*.py`, `scripts/benchmark_*.py`,
`scripts/collect_*.py`, `scripts/download_*.py` ở chế độ ghi thật.

Lệnh do các vai không-chạy đưa ra phải: **mỗi khối đúng một lệnh** để dán về không lẫn, nêu rõ
**kết quả mong đợi** của từng lệnh, và với phép đột biến thì kèm đủ bốn bước *sao lưu ra ngoài repo →
sửa → chạy → khôi phục và đối chiếu*. Không lệnh nào được `git commit`, dựng image mới,
hay `pip install`.

**Đo, vẽ và minh hoạ là ba việc tách rời — không được trộn:**

| | Ai chạy | Ở đâu | Ghi ra |
|---|---|---|---|
| **Đo** — `scripts/benchmark_*.py`, `scripts/export_*.py` | **người dùng**, trên máy đo (Pi 5 thật) | dòng lệnh, không giao diện | `results/*.csv` + `.meta.json` |
| **Vẽ cho báo cáo** — `scripts/plot_*.py` | **người dùng**, máy phát triển | dòng lệnh | `report/figures/*.pdf` |
| **Minh hoạ & khám phá** — `notebooks/*.ipynb` | **người dùng**, máy phát triển | Jupyter | đầu ra lưu trong chính tệp `.ipynb`, **được commit** |

Cả ba **chỉ đọc** `results/`, không tự sinh số đo. **Tuyệt đối không đo hiệu năng trong notebook**:
Pi 5 chạy không màn hình, Jupyter thêm chi phí làm sai lệch phép đo, và thứ tự chạy ô lộn xộn
khiến kết quả không tái lập được. Notebook để *cho xem*, script để *tạo* ra số.

⭐ **Notebook là phương tiện minh hoạ chính thức của đồ án, không phải bản nháp.** Đồ án này tồn tại
để trình bày trước hội đồng: một con số trong `results/*.json` không mở ra cho ai xem được, còn một
notebook có đầu ra lưu sẵn thì mở ra là thấy cả pipeline. Vì vậy:

- **Không dùng tệp tạm ngoài repo** để lấy dữ kiện. Mọi lượt chạy sinh ra thứ đi vào đặc tả hay báo
  cáo đều phải để lại vết **trong đồ án** — notebook có đầu ra, hoặc tệp trong `results/`.
- Notebook được **commit kèm đầu ra**, không xoá output trước khi commit.
- Notebook đánh số theo thứ tự trình bày, không theo thứ tự viết: `01_` dữ liệu · `02_`–`03_` khối
  phát hiện · `04_` so sánh môi trường · `05_` khối nhận diện · `06_` ngưỡng và ROC.
- Notebook **được phép** chạy pipeline thật để minh hoạ (nạp mô hình, chạy một vài ảnh, vẽ khung bao
  và điểm mốc). Ranh giới cấm chỉ là **đo thời gian**.

**Ba môi trường chạy — luôn phân biệt rõ trong mọi kết quả:**

| Mã | Môi trường | Số hiệu năng dùng được không |
|---|---|---|
| `pc_x86` | Máy phát triển Windows x86-64 | Có, nhưng **không phải phần cứng đích** |
| `docker_arm64` | Container `faceid:arm64` qua QEMU | **Không** — QEMU giả lập, thời gian không quy đổi được |
| `pi5` | Raspberry Pi 5 thật | **Có** — đây là số kết luận chỉ tiêu §1 |

Mọi `.meta.json` phải mang trường `moi_truong` nhận một trong ba giá trị trên, để notebook
`04_so_sanh_moi_truong.ipynb` nhóm được. Bảng ba môi trường trình bày được **tính khả chuyển**
(cùng đầu vào, cùng kết quả nhận diện ở cả ba nơi — một luận điểm mạnh), nhưng cột `docker_arm64`
phải ghi rõ là **số tham khảo**, không dùng kết luận chỉ tiêu. Nói trước điều này trong báo cáo là
cẩn trọng phương pháp; để hội đồng phát hiện thì thành lỗ hổng.

Notebook do Claude **viết** nhưng người dùng **chạy**. Claude đọc lại tệp `.ipynb` đã có đầu ra để
phân tích — không tự thi hành ô nào.

`.claude/**` là **khung quy trình**, không phải sản phẩm của mã việc nào. Sửa nó **nên đi commit riêng**
với loại `chore(quy-trinh)`, không trộn vào commit của một mã việc — để sau này truy được bài học nào
sinh ra từ mã việc nào. `CLAUDE.md`, `docs/pipeline/` và `docs/trang-thai.md` cũng theo quy ước này.

**Mã việc** `P<Phase>-<nn>-<slug>` xuất hiện nguyên vẹn ở 5 chỗ, tạo chuỗi truy vết:
đặc tả → tên nhánh → biên bản review → commit message → nhật ký tuần.

Ánh xạ vào 4 cổng: **Cổng A** = N1 · **Cổng B** = N2–N5 · **Cổng C** = `training` đo · **Cổng D** = `paper-writer`.

---

## 3. Cấu trúc thư mục chuẩn

```
UIT-AI503.F3.LT.TTNT/
├── CLAUDE.md              # Hiến pháp repo — bối cảnh, quy tắc, phân vai
├── requirements.txt       # Pin cứng phiên bản (==)
├── .env.example           # Mẫu biến môi trường (KHÔNG chứa secret thật)
│
├── .claude/               # Khung quy trình — agents/ skills/ prompts/ instructions/ (§4)
│
├── docs/
│   ├── DE-CUONG-CHI-TIET.md   # Nguồn sự thật về phạm vi
│   ├── pipeline/              # Kế hoạch 8 Phase — phase-0.md … phase-8.md (§5)
│   ├── trang-thai.md          # Đang ở đâu, số đo đã có, việc còn nợ
│   ├── checklist-nop.md       # Kiểm 100 % trước khi nộp (Phase 8)
│   ├── quy-tac-cai-dat.md     # Hiến pháp cài đặt mã — người cài đặt đọc, tự chứa
│   ├── quy-uoc-du-lieu.md     # Quy ước đặt tên và tổ chức dữ liệu (Phase 1)
│   ├── nguoi-tham-gia.md      # Danh sách người tham gia + ngày đồng ý
│   ├── spoof-protocol.md      # Quy trình tạo bộ dữ liệu tấn công
│   ├── dac-ta/                # Đặc tả từng mã việc — spec-writer viết, coder thực thi
│   ├── review/                # Biên bản review — code-reviewer viết
│   ├── kiem-may/              # ĐÓNG BĂNG 27/08/2026 — di tích quy trình kịch bản .ps1
│   └── nhat-ky/               # Nhật ký tuần (tuan-01.md, …)
│
├── configs/               # TẤT CẢ tham số ở đây (R16): detect · recognize · antispoof · actuator · system
│
├── data/                  # GITIGNORED
│   ├── raw/               #   Gallery: data/raw/<user_id>/*.jpg — 2–3 người nhà
│   ├── impostor/          #   Người lạ, KHÔNG BAO GIỜ vào gallery: lfw_original/ · lfw_adapted/ · indomain/
│   ├── processed/         #   Ảnh đã crop/align 112×112 (cả gallery lẫn impostor)
│   ├── embeddings/        #   Vector đặc trưng đã đăng ký
│   ├── splits/            #   enroll · val · test · impostor_{lfw,adapt,indomain}_{val,test}
│   └── spoof/             #   Bộ tấn công: print/ · screen/ · live/
│
├── models/                # GITIGNORED (weights) — kèm models/README.md ghi link tải
│
├── src/                   # Kiến trúc 4 khối (R21)
│   ├── capture/           #   KHỐI 1a — camera
│   ├── detector/          #   KHỐI 1b — YOLOv8n-face
│   ├── antispoof/         #   KHỐI 1c — MiniFASNet
│   ├── recognizer/        #   KHỐI 1d — dlib | arcface (2 backend so sánh)
│   ├── decision/          #   KHỐI 2 — quyết định & phân quyền
│   ├── actuator/          #   KHỐI 3 — gpio/ir/mqtt (+ backend mock, R22)
│   ├── monitor/           #   KHỐI 4 — Flask web + Telegram + log DB
│   ├── common/            #   config loader, logging, types dùng chung
│   └── main.py            #   Điểm vào — vòng lặp chính
│
├── scripts/               # Script CLI: enroll, benchmark, export model, collect data
├── tests/                 # pytest — chạy được KHÔNG cần Pi (dùng backend mock)
├── notebooks/             # Minh hoạ pipeline — commit KÈM đầu ra (§2.9)
├── results/               # Output thực nghiệm (R17) — CSV/JSON + .meta.json
├── report/                # Báo cáo: main.tex · chapters/ · figures/ · refs.bib
├── deploy/                # Đúng MỘT image: faceid:arm64 (R43) + systemd/faceid.service
└── hardware/              # Sơ đồ đấu nối, ảnh mạch, bảng chân GPIO
```

### 3.1. Docker — một image duy nhất (R43)

| | |
|---|---|
| Tên image | **`faceid:arm64`** — không có tên nào khác trong toàn dự án |
| Dựng lại khi nào | **Chỉ khi** `requirements.txt` hoặc `deploy/Dockerfile.arm64` đổi |
| Sửa code có phải dựng lại không | **Không.** Mã nguồn gắn vào container bằng `-v`, sửa xong chạy luôn |

```bash
docker build -f deploy/Dockerfile.arm64 -t faceid:arm64 .
```

```bash
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q
```

Cấm: đặt tag khác (`faceid:nofl`, `faceid-arm64-review:...`), để `docker compose` tự sinh tên,
giữ image tạm sau khi dùng xong. Mỗi image ARM64 nặng khoảng 250 MB — vài lượt là đầy đĩa, và
tệ hơn là **không còn biết số đo lấy từ image nào**, khiến kết quả mất tính tái lập (R17).

---

## 4. Tài nguyên trong `.claude/`

**Agents** (`.claude/agents/`) — mỗi tệp tự khai **danh sách đọc đóng** của vai đó (R44):

| Agent | Gọi khi nào | Nhiệm vụ |
|---|---|---|
| `onboarding-with-skills` | Đầu phiên mới, hoặc khi mất ngữ cảnh | Định vị Phase, tổng hợp việc đã/đang/sắp làm, chỉ ra tài nguyên cần dùng |
| `spec-writer` | **Nhịp 1** (Cổng A) | Chuyển một bước của Phase thành đặc tả có chữ ký hàm, danh sách trắng file, tiêu chí nghiệm thu chạy được |
| `coder` | **Nhịp 2 và 4**, phiên riêng | Viết code theo danh sách trắng; **tự chạy** §9 đặc tả và dán kết quả về; **không commit** |
| `code-reviewer` | **Nhịp 3** | Đưa lệnh kiểm định cho người dùng chạy, đối chiếu đặc tả, phân loại lỗi 4 mức, ghi `docs/review/` |
| `training` | Cổng C của Phase 2, 3, 4, 7 | Thiết kế giao thức đo, phân tích số liệu, chốt ngưỡng từ ROC. *Không tự viết script* |
| `paper-writer` | Cổng D mỗi Phase & Phase 8 | Viết chương báo cáo từ dữ liệu thật trong `results/`, không bịa số |

**Skills** (`.claude/skills/`): `latex-visualization` (biểu đồ, bảng booktabs, TikZ) ·
`report-drafting` (dàn ý chương, ngân sách trang) · `academic-editing` (văn phong, trích dẫn IEEE).

**Prompts** (`.claude/prompts/`): `data-pipeline` (Phase 1) · `eda` (Phase 1 & 6) ·
`coder-handoff` (lệnh bàn giao Nhịp 2/4, quy ước nhánh `feat/`, xử lý sự cố).

**Instructions** (`.claude/instructions/`) — chuẩn kỹ thuật **luôn áp dụng** khi động vào loại file
tương ứng: `python-embedded` (`src/`, `scripts/`) · `experiment-protocol` (`results/`) ·
`code-review` (rubric 4 mức) · `hardware-safety` (`src/actuator/`, `hardware/`) ·
`academic-writing` (`report/`, `docs/`).

> Gọi agent bằng cách nêu rõ tên trong yêu cầu, ví dụ: *"Dùng training agent chạy benchmark Phase 3"*.
> Hiến pháp của người cài đặt là [`docs/quy-tac-cai-dat.md`](docs/quy-tac-cai-dat.md) — tự chứa,
> trung lập với công cụ, **không phụ thuộc file này**.

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

### 5.1. Chỉ mục 8 Phase

⭐ **Bảng các bước, Cổng C, Cổng D và công cụ của từng Phase nằm trong tệp riêng.**
Làm việc thuộc Phase nào thì **đọc đúng tệp đó và chỉ tệp đó** (R44).

| Phase | Tên | Tuần | Kế hoạch chi tiết |
|---|---|---|---|
| 0 | Khởi tạo & Môi trường | 1 (15–21/07) | [`docs/pipeline/phase-0.md`](docs/pipeline/phase-0.md) |
| 1 | Dữ liệu khuôn mặt | 2 (22–28/07) | [`docs/pipeline/phase-1.md`](docs/pipeline/phase-1.md) |
| 2 | Phát hiện khuôn mặt (YOLOv8n-face) | 2–3 (22/07–04/08) | [`docs/pipeline/phase-2.md`](docs/pipeline/phase-2.md) |
| 3 | ⭐ Nhận diện & So sánh 2 phương án | 3–5 (29/07–18/08) | [`docs/pipeline/phase-3.md`](docs/pipeline/phase-3.md) |
| 4 | Chống giả mạo (Anti-spoofing) | 4–5 (05–18/08) | [`docs/pipeline/phase-4.md`](docs/pipeline/phase-4.md) |
| 5 | Điều khiển thiết bị & Cảnh báo | 5–7 (12/08–01/09) | [`docs/pipeline/phase-5.md`](docs/pipeline/phase-5.md) |
| 6 | Web giám sát & Tích hợp | 7–8 (26/08–08/09) | [`docs/pipeline/phase-6.md`](docs/pipeline/phase-6.md) |
| 7 | Kiểm thử toàn hệ thống & Benchmark tổng | 8–9 (02–15/09) | [`docs/pipeline/phase-7.md`](docs/pipeline/phase-7.md) |
| 8 | Báo cáo, Slide & Bảo vệ | 9–10 (09–22/09) | [`docs/pipeline/phase-8.md`](docs/pipeline/phase-8.md) |

Phase 3 là **đóng góp khoa học chính**. Chỉ tiêu chặn của từng Cổng C ghi trong tệp Phase tương ứng.

---

## 6. Bản đồ nhanh: Việc cần làm → Tài nguyên dùng

| Tôi muốn... | Dùng |
|---|---|
| Bắt đầu phiên làm việc, không nhớ đang ở đâu | agent `onboarding-with-skills` |
| Biết đang ở đâu, còn nợ gì | `docs/trang-thai.md` |
| Xem kế hoạch chi tiết một Phase | `docs/pipeline/phase-<n>.md` |
| Thu thập / chuẩn hoá dữ liệu khuôn mặt | prompt `data-pipeline` |
| Phân tích thống kê dữ liệu hoặc kết quả | prompt `eda` |
| Export model, chạy benchmark, so sánh 2 phương án | agent `training` + `experiment-protocol.instructions` |
| **Bắt đầu một hạng mục code mới** | agent `spec-writer` → viết `docs/dac-ta/<mã>.md` |
| **Giao code cho người cài đặt** | agent `coder` + prompt `coder-handoff` |
| **Kiểm định code vừa viết** | agent `code-reviewer` + `code-review.instructions` |
| Tra chuẩn viết code Python cho `src/` | `python-embedded.instructions` (Claude tra khi viết đặc tả) |
| Đấu nối / lập trình GPIO, IR | `hardware-safety.instructions` |
| Vẽ biểu đồ, bảng, sơ đồ cho báo cáo | skill `latex-visualization` |
| Viết một chương báo cáo | agent `paper-writer` + skill `report-drafting` |
| Rà soát văn bản trước khi nộp | skill `academic-editing` + `docs/checklist-nop.md` |

---

## 7. Checklist trước khi nộp

→ [`docs/checklist-nop.md`](docs/checklist-nop.md). Chỉ dùng ở bước 8.4 của Phase 8, nên không nằm
trong tệp mà mọi vai nạp lại ở mỗi lượt.

---

## 8. Ghi chú vận hành

→ [`docs/trang-thai.md`](docs/trang-thai.md) — vị trí hiện tại, số ca kiểm thử theo mốc, số đo đã
có, gallery hiện có và bẫy của nó, rủi ro tiến độ, trạng thái từng chương báo cáo.

Tệp đó **dài thêm sau mỗi mã việc**, nên nó nằm ngoài hiến pháp. Chỉ phiên chính,
`onboarding-with-skills`, `training` và `paper-writer` cần đọc. Cập nhật mỗi khi qua Phase mới hoặc
gộp xong một mã việc; diễn biến đã khép lại thì đẩy về `docs/nhat-ky/tuan-XX.md`.
