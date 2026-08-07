---
applyTo: "scripts/benchmark*.py, scripts/eval*.py, results/**, notebooks/**"
description: Giao thức thực nghiệm bắt buộc — cách chuẩn hoá điều kiện đo, chỉ số phải thu thập, định dạng lưu kết quả và quy tắc trung thực số liệu. Mọi số liệu đưa vào báo cáo phải tuân thủ giao thức này.
---

# Instructions: Giao thức thực nghiệm

Áp dụng cho mọi thứ sinh ra số liệu đưa vào báo cáo.
Đây là phần quyết định **tính khoa học** của đồ án — hội đồng sẽ hỏi kỹ nhất ở đây.

---

## 1. Nguyên tắc bất di bất dịch

1. **Không bịa số.** Chưa đo → `[CHƯA ĐO]`. Không ước lượng, không lấy từ paper khác.
2. **Mỗi số phải tái tạo được**: cùng script + cùng config + cùng seed → kết quả tương đương.
3. **Điều kiện đo phải chuẩn hoá và được ghi lại**, nếu không thì phép so sánh vô nghĩa.
4. **Không chọn ngưỡng trên tập test.** Quét ngưỡng trên validation, báo cáo trên test.
5. **Không báo cáo giá trị tốt nhất đơn lẻ.** Luôn báo trung bình ± độ lệch chuẩn.
6. Kết quả kém → **báo cáo trung thực + phân tích nguyên nhân**, tuyệt đối không sửa số.

---

## 2. Chuẩn hoá điều kiện đo

Trước mỗi lần đo, ghi lại và giữ **cố định** trong suốt phiên đo:

| Yếu tố | Cách ghi | Ghi chú |
|---|---|---|
| Thiết bị | `Raspberry Pi 5 8GB` / `Docker ARM64 trên <CPU>` | Không trộn kết quả từ 2 nền tảng trong cùng bảng |

> ⛔ **TUYỆT ĐỐI không dùng thời gian đo trong container ARM64 giả lập làm số hiệu năng.**
>
> Container chạy qua QEMU nên thời gian **không ổn định và không quy đổi được**. Bằng chứng thực tế
> từ `P0-03`: cùng một bộ `pytest`, cùng kiến trúc, cùng image — đo được **16,21 s** ở lần chạy nguội
> và **2,22 s** ở lần chạy ấm. Chênh hơn 7 lần chỉ do trạng thái cache của máy chủ.
>
> Container dùng để kiểm **tính đúng đắn** (code chạy được trên ARM64, test xanh, thư viện nạp được).
> Mọi con số **FPS, latency, thông lượng** phải đo trên **Raspberry Pi 5 thật**. Số đo từ container
> chỉ được ghi vào `results/` khi cột `device` nói rõ là môi trường giả lập, và **không được đưa vào
> bảng đối chiếu chỉ tiêu** ở Chương 4.
| Tản nhiệt | `tản nhiệt nhôm + quạt` / `không tản nhiệt` | Ảnh hưởng lớn tới FPS do throttling |
| Nguồn điện | `27W USB-C chính hãng` | Nguồn yếu gây throttle |
| OS & kernel | `Raspberry Pi OS 64-bit, kernel 6.6` | |
| Phiên bản thư viện | dict đầy đủ | Lấy từ `pip freeze` |
| Độ phân giải camera | `1280×720 @ 30fps` | |
| Ánh sáng | `~300 lux, đèn LED trần` (đo bằng app lux hoặc mô tả rõ) | Bắt buộc ≥ 2 điều kiện |
| Khoảng cách | `0,5 / 1,0 / 2,0 m` | Đánh dấu vạch trên sàn để lặp lại được |
| Số lần lặp | `≥ 100 frame` hoặc `≥ 30 s` | |
| Warm-up | `bỏ 10 frame đầu` | Loại chi phí nạp model / JIT |
| Tải nền | `không chạy ứng dụng khác` | |
| Seed | `42` | |

**Quy tắc so sánh công bằng**: khi so 2 phương án, **chỉ được thay đổi đúng một biến**
(backend nhận diện), mọi thứ khác giữ nguyên tuyệt đối. Chạy tuần tự, không song song.

---

## 3. Chỉ số phải đo

### 3.1. Hiệu năng (mọi module)

| Chỉ số | Định nghĩa | Cách báo cáo |
|---|---|---|
| FPS | số frame xử lý xong / giây | trung bình ± std |
| Latency p50 | trung vị thời gian xử lý 1 frame | ms, 1 chữ số thập phân |
| Latency p95 | phân vị 95 | ms — **quan trọng hơn p50** cho trải nghiệm thực tế |
| RAM peak | bộ nhớ đỉnh của tiến trình | MB |
| Nhiệt độ CPU | `vcgencmd measure_temp` | °C, ghi cả max trong phiên |
| Throttling | `vcgencmd get_throttled` | ghi cờ nếu ≠ 0x0 |

### 3.2. Nhận diện (closed-set)

Accuracy, Precision, Recall, F1 (macro-average), ma trận nhầm lẫn.

### 3.3. Nhận diện (open-set) — QUAN TRỌNG cho hệ thống an ninh

| Chỉ số | Ý nghĩa | Ưu tiên |
|---|---|---|
| **`FAR_adapt`** ⭐ | Người lạ từ LFW **đã domain-adapted** bị nhận thành người nhà | **Số báo cáo chính** — chốt ngưỡng theo chỉ số này |
| `FAR_lfw` | Như trên nhưng trên LFW gốc | Baseline, so sánh được với tài liệu |
| `FAR_indomain` | 5–7 người quen có đồng ý, chụp bằng camera thật | **Kiểm chứng** `FAR_adapt` |
| `FAR_noibo` | Nhầm lẫn giữa 2–3 người trong gallery | Tham khảo, cỡ mẫu rất nhỏ |
| **FRR** (False Rejection Rate) | Người nhà bị từ chối | Gây bất tiện, chấp nhận được cao hơn |
| **EER** | Điểm FAR = FRR | Dùng để so sánh 2 phương án |
| ROC / AUC | Một đường cho mỗi tập impostor | Vẽ hình cho báo cáo |

> Báo cáo FAR/FRR **luôn kèm ngưỡng đang dùng** — nếu không thì số liệu vô nghĩa.

> ⚠️ **Bối cảnh gallery nhỏ (2–3 người) và thiết kế ba tập impostor**
> Đề tài định vị là ứng dụng cá nhân trong hộ gia đình nên gallery chỉ gồm sinh viên thực hiện và
> thành viên gia đình. Hệ quả bắt buộc phải xử lý:
> 1. **Không thể giữ lại người nhà nào làm "người lạ"** → phải có dữ liệu impostor từ ngoài.
> 2. **Accuracy KHÔNG phải chỉ số đại diện** — phân biệt 3 danh tính là bài toán dễ một cách giả tạo.
>    **FAR mới phản ánh năng lực an ninh thật.**
> 3. Mọi bảng/kết luận nêu accuracy **phải kèm câu cảnh báo cỡ mẫu**.
> 4. Chốt ngưỡng **theo `FAR_adapt` ≤ 1 %**, chấp nhận FRR cao hơn (an ninh > tiện dụng).

### Vì sao cần ba tập impostor — và giới hạn của từng tập

| Tập | Mạnh ở đâu | Yếu ở đâu |
|---|---|---|
| **LFW gốc** | ≥ 100 danh tính → đủ phân giải thống kê cho mức 1 % | Ảnh web, chất lượng cao, **khác miền** với camera thật → FAR lạc quan |
| **LFW adapted** | Giữ nguyên cỡ mẫu lớn, đã kéo về gần miền thật | Là dữ liệu **tổng hợp** — phải chứng minh adaptation hợp lệ |
| **In-domain** | Dữ liệu **thật**, đúng camera, đúng điều kiện | Chỉ 5–7 danh tính → **không đo được mức 1 %** |

**Giới hạn thống kê của tập in-domain — phải hiểu rõ:**
Theo *quy tắc số 3*, nếu quan sát 0 sự kiện trong n phép thử độc lập thì cận trên khoảng tin cậy
95 % của xác suất là ≈ 3/n. Với **n = 7 danh tính**, dù không có ai bị chấp nhận sai, ta chỉ kết
luận được **FAR < 43 %**. Đó là lý do in-domain **không thay thế được LFW** — nó là **phép kiểm
chứng**, không phải phép đo.

> Lưu ý: đếm theo **danh tính**, không theo ảnh. 7 người × 20 ảnh không cho 140 phép thử độc lập —
> các ảnh của cùng một người có tương quan cao. Cỡ mẫu hiệu dụng là số danh tính.

**Quy trình kiểm chứng domain adaptation (bắt buộc ở Phase 3):**
1. Đo `FAR_adapt` và `FAR_indomain` tại **cùng một ngưỡng**.
2. Tính khoảng tin cậy 95 % cho `FAR_indomain` (Clopper–Pearson trên số danh tính).
3. `FAR_adapt` **nằm trong** khoảng đó → adaptation **hợp lệ**, dùng `FAR_adapt` báo cáo.
4. Nằm ngoài → quay lại `configs/domain_adapt.yaml`, tinh chỉnh, đo lại.
   Vẫn lệch sau 2–3 vòng → **báo cáo trung thực cả hai con số và khoảng chênh**, phân tích nguyên nhân.
5. Ghi toàn bộ quá trình vào `results/` — quá trình tinh chỉnh này là nội dung bàn luận có giá trị.

### 3.4. Anti-spoofing — chuẩn ISO/IEC 30107-3

| Chỉ số | Công thức | Ghi chú |
|---|---|---|
| **APCER** | (số mẫu tấn công bị phân loại là thật) / (tổng mẫu tấn công) | Báo cáo **tách riêng** cho từng loại tấn công, rồi lấy max |
| **BPCER** | (số mẫu thật bị phân loại là tấn công) / (tổng mẫu thật) | |
| **ACER** | (APCER + BPCER) / 2 | |

Chỉ tiêu đề cương "phát hiện ≥ 90 % tấn công" ⇔ **APCER ≤ 10 %**.

---

## 4. Định dạng lưu kết quả (BẮT BUỘC)

Mỗi lần chạy sinh **đúng 2 file** trong `results/`:

### File 1 — dữ liệu thô `results/<ten>_<YYYYMMDD_HHMM>.csv`

Mỗi dòng là **một lần đo đơn lẻ**, không phải giá trị đã tổng hợp:

```csv
run_id,backend,imgsz,threads,sample_idx,latency_ms,fps_instant,label_true,label_pred,similarity,is_correct,cpu_temp_c
```

Lưu thô để có thể tính lại mọi chỉ số về sau mà không phải chạy lại thí nghiệm.

### File 2 — ngữ cảnh `results/<ten>_<YYYYMMDD_HHMM>.meta.json`

```json
{
  "run_id": "bench_recognize_20260812_1430",
  "timestamp": "2026-08-12T14:30:00+07:00",
  "git_commit": "a1b2c3d4",
  "git_dirty": false,
  "script": "scripts/benchmark_recognize.py",
  "command": "python scripts/benchmark_recognize.py --backend arcface --n-samples 100 --seed 42",
  "device": {
    "name": "Raspberry Pi 5 8GB",
    "cooling": "tản nhiệt nhôm + quạt 5V",
    "power": "nguồn USB-C 27W chính hãng",
    "os": "Raspberry Pi OS 64-bit (Bookworm), kernel 6.6.20"
  },
  "software": {
    "python": "3.11.2",
    "onnxruntime": "1.17.0",
    "opencv-python": "4.9.0.80",
    "numpy": "1.26.4"
  },
  "config_file": "configs/recognize.yaml",
  "config_snapshot": {"backend": "arcface", "threshold": 0.42, "...": "..."},
  "dataset": {
    "gallery": "data/embeddings/arcface/gallery.npz",
    "test_split": "data/splits/test.txt",
    "n_users": 6,
    "n_samples": 100
  },
  "conditions": {
    "lighting": "trong nhà, đèn LED trần, ~300 lux",
    "distance_m": 1.0,
    "camera_resolution": "1280x720"
  },
  "seed": 42,
  "warmup_frames": 10,
  "cpu_temp_start_c": 42.1,
  "cpu_temp_max_c": 61.3,
  "throttled_flag": "0x0",
  "duration_s": 187.4,
  "notes": "Chạy tuần tự sau khi đo backend dlib, nghỉ 5 phút để hạ nhiệt."
}
```

> `git_dirty: true` là **cảnh báo** — kết quả đo từ code chưa commit khó tái lập.
> Commit trước khi chạy benchmark chính thức.

### Đặt tên file

```
bench_detect_<YYYYMMDD_HHMM>          Phase 2
bench_recognize_<YYYYMMDD_HHMM>       Phase 3
bench_antispoof_<YYYYMMDD_HHMM>       Phase 4
bench_latency_<YYYYMMDD_HHMM>         Phase 5
stability_<YYYYMMDD_HHMM>             Phase 7 — chạy dài
scenario_<YYYYMMDD_HHMM>              Phase 7 — 3 kịch bản
```

❌ Không đặt tên `test1.csv`, `final.csv`, `ket_qua_moi.csv`, `bench_v2_final_final.csv`.
❌ **Không ghi đè** file kết quả cũ — mỗi lần chạy là một timestamp mới. Lịch sử đo là dữ liệu có giá trị.

---

## 5. Quy trình quét ngưỡng (chuẩn)

1. Tính điểm tương đồng cho **mọi cặp** trên tập **validation**, phân thành 5 nhóm:
   - **genuine** — cùng người nhà
   - **impostor nội bộ** — giữa 2–3 người nhà với nhau
   - **`impostor_lfw_val`** — người nhà vs LFW gốc
   - **`impostor_adapt_val`** — người nhà vs LFW đã domain-adapted ← **nhóm chốt ngưỡng**
   - **`impostor_indomain_val`** — người nhà vs 5–7 người quen
2. Quét ngưỡng từ min → max, **200 bước**.
3. Tại mỗi ngưỡng tính FRR và **cả 4 loại FAR**.
4. Xác định:
   - **Ngưỡng tại EER** — dùng để so sánh học thuật giữa 2 phương án
   - **Ngưỡng tại `FAR_adapt` = 1 %** — **dùng cho hệ thống triển khai thực tế**
5. **Chốt ngưỡng, ghi vào `configs/*.yaml` kèm comment nguồn.**
6. Đánh giá lại trên **tập test + toàn bộ `*_test`** với ngưỡng đã chốt → **đây mới là số liệu báo cáo**.
7. **Kiểm chứng adaptation** theo quy trình ở mục trên.

⛔ Danh tính impostor dùng ở bước quét ngưỡng (`*_val`) **không được** xuất hiện lại ở `*_test` —
nếu trùng thì FAR báo cáo sẽ lạc quan giả tạo.
⛔ `impostor_lfw` và `impostor_adapt` phải chia **cùng danh tính về cùng phía** — nếu không thì
hai con số FAR không so sánh được với nhau, và toàn bộ phân tích domain gap mất ý nghĩa.

⛔ Chọn ngưỡng trên tập test là **lỗi phương pháp nghiêm trọng** — hội đồng sẽ phát hiện.

---

## 6. Cỡ mẫu tối thiểu

| Loại đo | Tối thiểu |
|---|---|
| FPS / latency | 100 frame (sau warm-up) |
| Độ chính xác nhận diện | ≥ 100 lần so khớp, mỗi người ≥ 30 mẫu test (gallery nhỏ → tăng mẫu/người) |
| **`FAR_lfw` / `FAR_adapt`** | **≥ 100 danh tính, ≥ 300 cặp so khớp** — gallery nhỏ nên phải bù bằng nhiều impostor |
| `FAR_indomain` | 5–7 danh tính × ≥ 20 ảnh — **chỉ dùng kiểm chứng**, ghi rõ cận trên khoảng tin cậy |
| `FAR_noibo` | mọi cặp có thể giữa 2–3 người nhà (số lượng ít, ghi rõ hạn chế) |
| Anti-spoofing | ≥ 30 mẫu mỗi loại tấn công + ≥ 30 mẫu live |
| Độ trễ end-to-end | ≥ 30 lần lặp |
| Kiểm thử kịch bản | ≥ 20 lượt mỗi tổ hợp (kịch bản × ánh sáng × khoảng cách) |
| Thử nghiệm ổn định | ≥ 2 giờ liên tục |

Không đạt cỡ mẫu tối thiểu → **ghi rõ trong báo cáo** là hạn chế, không im lặng.

---

## 7. Kiểm định thống kê

Khi kết luận "phương án A tốt hơn B", phải kiểm định:

| So sánh | Phép kiểm | Ghi chú |
|---|---|---|
| Độ chính xác (cùng tập test) | **McNemar test** | Dữ liệu ghép cặp |
| Latency / FPS | **Mann–Whitney U** | Không giả định phân phối chuẩn |
| Nhiều cấu hình | Kruskal–Wallis + hiệu chỉnh Bonferroni | |

Báo cáo **p-value**. Nếu p ≥ 0,05 → viết *"chênh lệch chưa đạt ý nghĩa thống kê"*,
**không được** kết luận phương án này tốt hơn.

---

## 8. Khi kết quả không đạt chỉ tiêu

Theo đúng thứ tự, **không sửa số liệu**:

1. Ghi nhận trung thực vào `results/`.
2. **Chẩn đoán nút thắt**: đo latency phân rã từng khâu (capture/detect/antispoof/recognize/actuate).
3. Áp dụng tối ưu theo thứ tự chi phí tăng dần: giảm `imgsz` → đổi runtime (ONNX→NCNN) →
   frame skipping + tracking → anti-spoofing thưa → quantization INT8 → đa luồng.
4. **Đo lại và giữ CẢ HAI kết quả** (trước/sau tối ưu) — quá trình tối ưu là nội dung
   có giá trị khoa học cho Chương 4.
5. Vẫn không đạt → viết mục "Hạn chế và nguyên nhân" ở Chương 5, phân tích trung thực.

---

## 9. Checklist trước khi đưa số liệu vào báo cáo

- [ ] Có file `.csv` **và** `.meta.json` trong `results/`
- [ ] `git_dirty = false` trong meta (code đã commit)
- [ ] Đạt cỡ mẫu tối thiểu §6
- [ ] Có warm-up, đã loại frame đầu
- [ ] Điều kiện đo ghi đầy đủ trong meta
- [ ] Đo trong ≥ 2 điều kiện ánh sáng (yêu cầu đề cương)
- [ ] Báo cáo trung bình ± std, không phải giá trị tốt nhất
- [ ] Ngưỡng chọn trên validation, kết quả báo cáo trên test
- [ ] **Có đủ 4 con số FAR**, không chỉ accuracy trên 2–3 người nhà
- [ ] **Có kết luận kiểm chứng** `FAR_adapt` vs `FAR_indomain` kèm khoảng tin cậy
- [ ] **Có câu cảnh báo cỡ mẫu** kèm mọi con số accuracy
- [ ] `*_val` và `*_test` không trùng danh tính; `lfw` và `adapt` chia cùng danh tính cùng phía
- [ ] Tham số domain adaptation đã ghi vào `.meta.json` để tái lập
- [ ] Có kiểm định thống kê nếu so sánh 2 phương án
- [ ] Bảng/hình trong báo cáo ghi chú đúng tên file nguồn
- [ ] Đã đối chiếu với chỉ tiêu cam kết và kết luận Đạt/Không đạt
