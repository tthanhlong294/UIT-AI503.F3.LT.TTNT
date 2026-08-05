# Trọng số mô hình (model weights)

Thư mục này **không chứa file weights** — chúng bị `.gitignore` chặn vì dung lượng lớn và vì git lưu
vĩnh viễn mọi phiên bản của file nhị phân, khiến kho phình ra không thể thu lại.

File này là chỉ dẫn để **tải lại toàn bộ weights từ đầu**, đáp ứng yêu cầu "người khác dựng lại được
hệ thống" trong checklist trước khi nộp (`CLAUDE.md` §7).

> ⚠️ **Chưa điền.** Mọi ô `[…]` bên dưới phải do người thực hiện tự tải, tự kiểm chứng rồi ghi vào.
> Không chép link từ nguồn thứ cấp mà chưa bấm thử — link chết hoặc sai phiên bản sẽ khiến toàn bộ
> phần này vô dụng, và số liệu trong báo cáo mất khả năng tái lập.

---

## 1. Bảng weights

| # | File | Khối | Nguồn tải | Giấy phép | Kích thước | SHA256 | Ngày tải |
|---|---|---|---|---|---|---|---|
| 1 | `yolov8n-face.onnx` | Phát hiện khuôn mặt | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |
| 2 | `yolov8n-face.ncnn.param` + `.bin` | Phát hiện — bản NCNN | *(tự export từ #1 ở Phase 2)* | — | `[…]` | `[…]` | `[…]` |
| 3 | `dlib/shape_predictor_68_face_landmarks.dat` | Nhận diện — phương án A | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |
| 4 | `dlib/dlib_face_recognition_resnet_model_v1.dat` | Nhận diện — phương án A | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |
| 5 | `mobilefacenet.onnx` | Nhận diện — phương án B | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |
| 6 | `minifasnet.onnx` | Chống giả mạo | `[…]` | `[…]` | `[…]` | `[…]` | `[…]` |

**Cây thư mục sau khi tải đủ:**

```
models/
├── README.md                    ← file này (được commit)
├── yolov8n-face.onnx
├── yolov8n-face.ncnn.param
├── yolov8n-face.ncnn.bin
├── mobilefacenet.onnx
├── minifasnet.onnx
└── dlib/
    ├── shape_predictor_68_face_landmarks.dat
    └── dlib_face_recognition_resnet_model_v1.dat
```

Tên file phải **khớp đúng** giá trị `model_path` trong `configs/*.yaml`. Đổi tên file thì phải sửa
config tương ứng, không sửa đường dẫn cứng trong code (R16).

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

- [ ] Bảng §1 không còn ô `[…]` nào
- [ ] Mọi file nằm đúng vị trí theo cây thư mục §1
- [ ] SHA256 đã tính và ghi cho từng file
- [ ] Giấy phép từng mô hình đã ghi, và đã thêm mục tương ứng vào `report/refs.bib`
- [ ] `git status` **không** hiện file weights nào (xác nhận `.gitignore` hoạt động đúng)
- [ ] Đường dẫn trong `configs/*.yaml` khớp tên file thật
- [ ] Nạp thử được: `python -c "import onnxruntime as ort; ort.InferenceSession('models/mobilefacenet.onnx')"`
