# Trọng số mô hình (model weights)

Thư mục này **không chứa file weights** — chúng bị `.gitignore` chặn vì dung lượng lớn và vì git lưu
vĩnh viễn mọi phiên bản của file nhị phân, khiến kho phình ra không thể thu lại.

File này là chỉ dẫn để **tải lại toàn bộ weights từ đầu**, đáp ứng yêu cầu "người khác dựng lại được
hệ thống" trong checklist trước khi nộp (`CLAUDE.md` §7).

> ⚠️ **Chưa điền.** Mọi ô `[…]` bên dưới phải do người thực hiện tự tải, tự kiểm chứng rồi ghi vào.
> Không chép link từ nguồn thứ cấp mà chưa bấm thử — link chết hoặc sai phiên bản sẽ khiến toàn bộ
> phần này vô dụng, và số liệu trong báo cáo mất khả năng tái lập.

---

## 1. Hai loại file — ghi nhận khác nhau

| Loại | Đặc điểm | Cần ghi gì để tái lập |
|---|---|---|
| **A — Tải về** | Do bên thứ ba phát hành | Nguồn, giấy phép, kích thước, SHA256, ngày tải |
| **B — Sinh tại chỗ** | Do chính nghiên cứu này chuyển đổi từ file loại A | Sinh từ file nào, **lệnh và tham số**, phiên bản công cụ, kích thước, SHA256, ngày sinh |

File loại B **không có "nguồn tải"**. Thứ khiến nó tái lập được là **lệnh sinh ra nó**, không phải
đường dẫn tải. Ghi kích thước của file gốc `.pt` vào dòng của file `.onnx` là sai dữ liệu.

### Bảng A — File tải về

| # | File | Khối | Nguồn tải | Giấy phép | Kích thước | SHA256 | Ngày tải |
|---|---|---|---|---|---|---|---|
| A1 | `yolov8n-face.pt` | Phát hiện khuôn mặt | `[https://github.com/akanametov/yolo-face]` | `[GPL-3.0 license]` | `[6.09 mb]` | `[D545BF1ADD5AA736A4FEBAC4F4F9245A6D596CD0FE70D5D57989FE0CB9E626CA]` | `[06/8/2026]` |
| A2 | `dlib/shape_predictor_68_face_landmarks.dat` | Nhận diện — phương án A | `[https://huggingface.co/matt3ounstable/dlib_predictor_recognition]` | `[Phi thương mại]` | `[99.7 mb]` | `[fbdc2cb80eb9aa7a758672cbfdda32ba6300efe9b6e6c7a299ff7e736b11b92f]` | `[7/8/2026]` |
| A3 | `dlib/dlib_face_recognition_resnet_model_v1.dat` | Nhận diện — phương án A | `[https://huggingface.co/matt3ounstable/dlib_predictor_recognition]` | `[Phi thương mại]` | `[22.5 mb]` | `[55533b28a95800a551ba546ba62fe69625c7e95a7061c338adffead08719da30]` | `[7/8/2026]` |
| A4 | `mobilefacenet.onnx` | Nhận diện — phương án B | `[https://github.com/deepinsight/insightface/tree/master/model_zoo]` | `[Phi thương mại]` | `[12.9 mb]` | `[9CC6E4A75F0E2BF0B1AED94578F144D15175F357BDC05E815E5C4A02B319EB4F]` | `[7/8/2026]` |
| A5 | `minifasnet.onnx` | Chống giả mạo | `[ONNX: https://github.com/yakhyo/face-anti-spoofing/releases · gốc: https://github.com/minivision-ai/Silent-Face-Anti-Spoofing]` | `[Apache-2.0 — Minivision, 2020]` | `[1.66 mb]` | `[sha256:b32929adc2d9c34b9486f8c4c7bc97c1b69bc0ea9befefc380e4faae4e463907]` | `[7/8/2026]` |

### Bảng B — File sinh tại chỗ

| # | File | Sinh từ | Lệnh và tham số | Phiên bản công cụ | Kích thước | SHA256 | Ngày sinh |
|---|---|---|---|---|---|---|---|
| B1 | `yolov8n-face-320.onnx` | A1 | `yolo export model=... format=onnx imgsz=320 opset=12 simplify=True` | ultralytics `[…]` | `[…]` | `[…]` | `[…]` |
| B2 | `yolov8n-face-640.onnx` | A1 | như trên, `imgsz=640` | ultralytics `[…]` | `[…]` | `[…]` | `[…]` |
| B3 | `yolov8n-face-320.ncnn.param` + `.bin` | A1 | `yolo export model=... format=ncnn imgsz=320` | ultralytics `[…]` | `[…]` | `[…]` | `[…]` |

> Chỉ YOLOv8n-face cần export. `mobilefacenet.onnx` (A4) và `minifasnet.onnx` (A5) đều lấy bản ONNX
> phát hành sẵn — mỗi bước chuyển đổi tự làm là một nguồn sai lệch không báo lỗi, chỉ biểu hiện thành
> độ chính xác thấp bất thường.

> Phase 2 chạy ma trận benchmark `{ONNX, NCNN} × {320, 640} × {1, 2, 4 thread}`, nên **cần cả hai
> kích thước đầu vào**. Tên file mang hậu tố kích thước để phân biệt; sau khi Phase 2 chốt cấu hình
> tối ưu, `configs/detect.yaml` trỏ tới đúng file đã chọn.

**Cây thư mục sau khi có đủ:**

```
models/
├── README.md                        ← file này (được commit)
├── yolov8n-face.pt                  ← A1, tải về
├── yolov8n-face-320.onnx            ← B1, sinh tại chỗ
├── yolov8n-face-640.onnx            ← B2
├── yolov8n-face-320.ncnn.param      ← B3
├── yolov8n-face-320.ncnn.bin        ← B3
├── mobilefacenet.onnx               ← A4, tải về
├── minifasnet.onnx                  ← A5, tải về
└── dlib/
    ├── shape_predictor_68_face_landmarks.dat        ← A2
    └── dlib_face_recognition_resnet_model_v1.dat    ← A3
```

Tên file phải **khớp đúng** giá trị `model_path` trong `configs/*.yaml`. Đổi tên file thì phải sửa
config tương ứng, không sửa đường dẫn cứng trong code (R16).

> 💡 **Điền dần, không dồn.** Bảng A điền ngay lúc tải (Phase 2 bước 2.1). Bảng B điền ngay sau khi
> chạy lệnh export (bước 2.2) — lúc đó mới có kích thước và SHA256 thật.

---

## 2. Cách lấy mã băm SHA256

Mã băm dùng để xác nhận file tải về không hỏng và không bị thay đổi. Chạy sau khi tải xong:

Git Bash:
```bash
sha256sum models/yolov8n-face.onnx
```

PowerShell:
```powershell
Get-FileHash models\yolov8n-face.onnx -Algorithm SHA256
```

Chép giá trị vào cột SHA256 của bảng trên.

---

## 3. Ghi chú cho từng mô hình

### 3.1. YOLOv8n-face

Ultralytics **không phát hành mô hình chuyên cho khuôn mặt**. Weights thường đến từ các kho cộng đồng
huấn luyện lại YOLOv8 trên tập WIDER FACE. Khi chọn nguồn, ghi lại:

- Kho nguồn và tác giả
- Tập dữ liệu huấn luyện
- Có đủ **5 điểm mốc** (landmarks) hay chỉ có khung bao? Đồ án cần landmarks để căn chỉnh
  khuôn mặt về 112×112 ở bước tiền xử lý — thiếu thì phải dùng bộ định vị điểm mốc riêng

Bản `.onnx` và `.ncnn` **tự export** ở Phase 2 từ file `.pt` gốc, không tải sẵn:

```bash
yolo export model=yolov8n-face.pt format=onnx imgsz=320 opset=12 simplify=True
yolo export model=yolov8n-face.pt format=ncnn imgsz=320
```

Ghi lại kích thước file và phiên bản `ultralytics` đã dùng để export — số liệu này vào Chương 4.

### 3.2. dlib — phương án A

Hai file `.dat` thường được tải kèm khi cài gói `face_recognition`, hoặc lấy trực tiếp từ trang chính
thức của dlib. File phát hành ở dạng nén `.bz2`, phải giải nén trước khi dùng.

### 3.3. MobileFaceNet / ArcFace — phương án B

Ghi rõ **số chiều embedding** (512) và **kích thước ảnh đầu vào** (112×112) của bản đã tải — hai
thông số này phải khớp với `configs/recognize.yaml`. Cùng tên "MobileFaceNet" nhưng các bản phát hành
có thể khác nhau về chuẩn hoá đầu vào; ghi lại cách chuẩn hoá (khoảng giá trị, thứ tự kênh màu).

### 3.4. MiniFASNet — chống giả mạo

#### Nguồn gốc — dùng để trích dẫn

**`minivision-ai/Silent-Face-Anti-Spoofing`** — <https://github.com/minivision-ai/Silent-Face-Anti-Spoofing>

Kho gốc của nhóm tác giả. Weights **được commit thẳng trong repo**, không tải rời:

```
resources/anti_spoof_models/2.7_80x80_MiniFASNetV2.pth
```

Đây là nguồn ghi vào `report/refs.bib` và cột "Giấy phép" của A5, **kể cả khi lấy file ONNX từ nơi
khác** — bản chuyển đổi của bên thứ ba chỉ đổi định dạng, không tạo ra giấy phép mới.

#### Nguồn ONNX sẵn — chọn một

| Nguồn | Nội dung | Đánh giá |
|---|---|---|
| **`yakhyo/face-anti-spoofing`** (GitHub, mục Releases) | ONNX cho **cả MiniFASNetV1SE lẫn MiniFASNetV2**, opset 11; tuyên bố weights tương đương bit với `.pth` gốc; kèm mã suy luận tối giản | **Ưu tiên** — có cả hai mô hình và mã để đối chiếu tiền xử lý |
| `garciafido/minifasnet-v2-anti-spoofing-onnx` (Hugging Face) | Chỉ MiniFASNetV2, chuyển từ `2.7_80x80_MiniFASNetV2.pth`, opset 11, ~1,7 MB | Gọn hơn nếu chỉ dùng một mô hình |
| `QingHeYang/Silent-Face-Anti-Spoofing-onnx` (GitHub) | Bản chuyển đổi kèm mã suy luận | Phương án dự phòng |

Lý do ưu tiên nguồn có **cả hai mô hình**: kho gốc chạy **tổ hợp** rồi cộng kết quả. Chỉ lấy
`MiniFASNetV2` mà bỏ `MiniFASNetV1SE` sẽ cho kết quả thấp hơn con số nhóm tác giả công bố — và rất dễ
bị hiểu nhầm thành "mô hình kém" trong khi thực ra là cài thiếu.

#### Bốn điểm phải xác minh trước khi dùng

Đây là những chỗ sai mà **không có thông báo lỗi nào**, chỉ biểu hiện thành kết quả tệ:

1. **Thứ tự kênh màu là BGR, không phải RGB.** Mô hình nhận ảnh cắt 80×80 theo thứ tự BGR — trùng mặc
   định của OpenCV. Nếu pipeline có chỗ nào chuyển sang RGB thì điểm số sai hoàn toàn.
2. **Chỉ số của lớp "thật" — đọc từ mã suy luận gốc, tuyệt đối không đoán.** Đầu ra là softmax **3 lớp**
   (thật / tấn công in / tấn công phát lại), không phải 2. Nhầm một chỉ số là hệ thống đảo ngược kết
   luận: người thật bị chặn, ảnh in được cho qua. Ghi cách ánh xạ 3 lớp → `is_live` vào
   `configs/antispoof.yaml`.
3. **Số `2.7` trong tên file là hệ số nới khung bao, không phải phiên bản.** Khung bao từ YOLO phải
   được nới đúng hệ số này trước khi cắt về 80×80. Cắt sát quá hay rộng quá đều làm điểm số lệch nhiều.
4. **Một mô hình hay hai.** Đọc mã suy luận của kho gốc xem nó cộng kết quả của mấy mô hình, rồi quyết
   định và **ghi rõ** — lựa chọn này ảnh hưởng cả độ chính xác lẫn chi phí FPS, phải nêu trong Chương 4.

#### Kết quả xác minh — ĐIỀN VÀO ĐÂY

Bảng này là nơi ghi câu trả lời cho bốn điểm trên. Điền xong thì chép thẳng sang đặc tả `P4-01`
và `configs/antispoof.yaml` ở Phase 4.

| # | Thông số | Giá trị | Xác minh bằng cách nào |
|---|---|---|---|
| 1 | Hình dạng đầu vào | `[batch, 3, 80, 80]`, kiểu `float32` | Nạp bằng `onnxruntime`, đọc `get_inputs()[0].shape` — 07/08/2026 |
| 2 | Hình dạng đầu ra | `[batch, 3]` — xác nhận **3 lớp** | Nạp bằng `onnxruntime`, đọc `get_outputs()[0].shape` — 07/08/2026 |
| 3 | **Thứ tự kênh màu** | `[…]` BGR hay RGB | `[…]` — ghi file và dòng trong mã tiền xử lý của kho nguồn |
| 4 | **Chỉ số lớp "thật"** | `[…]` 0, 1 hay 2 | `[…]` — ghi file và dòng trong mã suy luận của kho nguồn |
| 5 | Ý nghĩa hai lớp còn lại | `[…]` in / phát lại | `[…]` |
| 6 | **Hệ số nới khung bao** | `[…]` — tên file gốc `2.7_80x80` gợi ý là `2.7`, cần xác nhận | `[…]` |
| 7 | Khoảng giá trị chuẩn hoá | `[…]` `[0,1]` hay `[-1,1]` hay chia 255 | `[…]` |
| 8 | Kho gốc dùng **một hay hai** mô hình | `[…]` | `[…]` — đọc vòng lặp suy luận của kho gốc |

Cách xác minh dòng 1 và 2 — đã chạy, kết quả ghi sẵn ở trên:

```bash
python -c "import onnxruntime as ort; s=ort.InferenceSession('models/minifasnet.onnx'); print('vao:', s.get_inputs()[0].shape, '| ra:', s.get_outputs()[0].shape)"
```

Các dòng 3–8 **không đọc được từ file ONNX** — chúng nằm trong mã tiền xử lý và hậu xử lý của kho
nguồn. Mở mã suy luận của `yakhyo/face-anti-spoofing` hoặc kho gốc MiniVision, tìm đoạn cắt ảnh và
đoạn diễn giải đầu ra, rồi ghi **cả giá trị lẫn vị trí dòng mã** để sau này kiểm lại được.

> ⚠️ Dòng 4 là dòng nguy hiểm nhất. Nhầm chỉ số lớp "thật" thì hệ thống **đảo ngược hoàn toàn**:
> người thật bị chặn, ảnh in được cho qua — mà không có thông báo lỗi nào. Kiểm bằng cách chạy thử
> một ảnh mặt thật và một ảnh chụp lại màn hình, xem lớp nào có xác suất cao hơn ở từng trường hợp.

> 💡 **Biến thể đã khảo sát nhưng chưa dùng: MiniFASNetV2-SE.**
> Kho `face-antispoof-onnx` phát hành bản ONNX chỉ khoảng 600 KB, có thêm khối SE và hàm mất mát phụ
> trên miền tần số nhằm bắt vân lưới màn hình và mạng lưới in — đúng hai loại tấn công trong phạm vi
> đồ án. Có cả bản đã lượng tử hoá.
>
> **Chưa chọn**, ba lý do: (a) con số độ chính xác là **tự công bố, chưa qua bình duyệt**;
> (b) kho xuất hiện dưới nhiều tên giống hệt nhau nên cần xác định đâu là bản gốc;
> (c) thêm nó thành phương án so sánh thứ hai là mở thêm một trục so sánh ngoài kế hoạch —
> trục chính thức của đồ án là dlib ↔ ArcFace ở khối nhận diện.
>
> **Khi nào quay lại**: nếu MiniFASNetV2 đo trên bộ tấn công thật không đạt chỉ tiêu ≥ 90 %.
> Lúc đó việc thử biến thể SE là bước tối ưu có căn cứ, và quá trình đó là nội dung đáng viết
> cho Chương 4. Đã ghi vào Chương 5 §5.3 như hướng đã khảo sát.

---

## 4. Giấy phép — bắt buộc ghi

Một số mô hình nhận diện khuôn mặt phát hành kèm điều khoản **chỉ dùng cho nghiên cứu, phi thương mại**.
Đồ án tốt nghiệp thuộc phạm vi nghiên cứu nên thường hợp lệ, nhưng **báo cáo phải nêu rõ giấy phép của
từng mô hình**, tương tự yêu cầu đã đặt ra với bộ dữ liệu LFW (`CLAUDE.md` R28c).

Khi tải mỗi mô hình, mở file `LICENSE` trong kho nguồn, ghi vào cột "Giấy phép" của bảng §1, và trích
dẫn công trình gốc trong `report/refs.bib`. Làm lúc tải mất hai phút; để đến lúc viết báo cáo thì phải
lần lại từ đầu và dễ ghi sai.

> ⚠️ **Giấy phép của hệ thống bị ràng buộc bởi thành phần chặt nhất.** Các mô hình đang dùng có điều
> khoản rất khác nhau — từ Apache-2.0 (cho phép cả thương mại) tới nghiên cứu phi thương mại. Chỉ cần
> **một** thành phần giới hạn nghiên cứu là **toàn hệ thống** không thương mại hoá được.
>
> Với đồ án tốt nghiệp thì không vướng, vì đây là nghiên cứu học thuật. Nhưng cần nêu một câu trong
> phần đạo đức nghiên cứu hoặc Chương 5 §Hạn chế: hệ thống ở dạng hiện tại **chỉ dùng cho mục đích
> nghiên cứu**; muốn triển khai thương mại phải thay các thành phần có giấy phép hạn chế. Đây là loại
> chi tiết hội đồng đánh giá cao khi thấy sinh viên chủ động nêu.

---

## 5. Checklist sau khi tải đủ

- [ ] **Bảng A** không còn ô `[…]` — điền lúc tải
- [ ] **Bảng B** không còn ô `[…]` — điền sau khi export, gồm cả lệnh và phiên bản `ultralytics`
- [ ] Không lấy kích thước / SHA256 của file gốc điền cho file đã export
- [ ] Mọi file nằm đúng vị trí theo cây thư mục §1
- [ ] SHA256 đã tính và ghi cho từng file, **tính trên chính file đó**
- [ ] Giấy phép từng mô hình đã ghi, và đã thêm mục tương ứng vào `report/refs.bib`
- [ ] `git status` **không** hiện file weights nào (xác nhận `.gitignore` hoạt động đúng)
- [ ] Đường dẫn trong `configs/*.yaml` khớp tên file thật
- [ ] Nạp thử được: `python -c "import onnxruntime as ort; ort.InferenceSession('models/mobilefacenet.onnx')"`
