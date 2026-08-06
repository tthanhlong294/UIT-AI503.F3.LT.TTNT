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
| A1 | `yolov8n-face.pt` | Phát hiện khuôn mặt | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |
| A2 | `dlib/shape_predictor_68_face_landmarks.dat` | Nhận diện — phương án A | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |
| A3 | `dlib/dlib_face_recognition_resnet_model_v1.dat` | Nhận diện — phương án A | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |
| A4 | `mobilefacenet.onnx` | Nhận diện — phương án B | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |
| A5 | `minifasnet.pth` *(hoặc định dạng gốc)* | Chống giả mạo | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |

### Bảng B — File sinh tại chỗ

| # | File | Sinh từ | Lệnh và tham số | Phiên bản công cụ | Kích thước | SHA256 | Ngày sinh |
|---|---|---|---|---|---|---|---|
| B1 | `yolov8n-face-320.onnx` | A1 | `yolo export model=... format=onnx imgsz=320 opset=12 simplify=True` | ultralytics `[…]` | `[…]` | `[…]` | `[…]` |
| B2 | `yolov8n-face-640.onnx` | A1 | như trên, `imgsz=640` | ultralytics `[…]` | `[…]` | `[…]` | `[…]` |
| B3 | `yolov8n-face-320.ncnn.param` + `.bin` | A1 | `yolo export model=... format=ncnn imgsz=320` | ultralytics `[…]` | `[…]` | `[…]` | `[…]` |
| B4 | `minifasnet.onnx` | A5 | `[…]` — ghi script hoặc lệnh chuyển đổi | `[…]` | `[…]` | `[…]` | `[…]` |

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
├── minifasnet.pth                   ← A5, tải về
├── minifasnet.onnx                  ← B4, sinh tại chỗ
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

Thường phát hành ở định dạng PyTorch `.pth`, **phải tự chuyển sang ONNX**. Ghi lại:

- Script hoặc lệnh đã dùng để chuyển đổi
- Kích thước ảnh đầu vào và tỉ lệ mở rộng khung bao khuôn mặt mà mô hình mong đợi — MiniFASNet nhạy
  với việc cắt ảnh, cắt sai tỉ lệ thì kết quả sai lệch nhiều

---

## 4. Giấy phép — bắt buộc ghi

Một số mô hình nhận diện khuôn mặt phát hành kèm điều khoản **chỉ dùng cho nghiên cứu, phi thương mại**.
Đồ án tốt nghiệp thuộc phạm vi nghiên cứu nên thường hợp lệ, nhưng **báo cáo phải nêu rõ giấy phép của
từng mô hình**, tương tự yêu cầu đã đặt ra với bộ dữ liệu LFW (`CLAUDE.md` R28c).

Khi tải mỗi mô hình, mở file `LICENSE` trong kho nguồn, ghi vào cột "Giấy phép" của bảng §1, và trích
dẫn công trình gốc trong `report/refs.bib`. Làm lúc tải mất hai phút; để đến lúc viết báo cáo thì phải
lần lại từ đầu và dễ ghi sai.

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
