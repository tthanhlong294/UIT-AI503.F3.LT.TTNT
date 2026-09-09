# UIT-AI503.F3.LT.TTNT
Đồ án tốt nghiệp ngành TTNT. với đề tài Nghiên cứu và triển khai hệ thống nhận diện khuôn mặt trên Raspberry Pi 5 ứng dụng điều khiển thiết bị trong nhà thông minh

## Cài đặt trên Raspberry Pi 5

Raspberry Pi OS Bookworm (64-bit) đóng gói **Python 3.11.2**; dự án yêu cầu Python ≥ 3.11 nên
phiên bản này tương thích.

Cài đặt phụ thuộc CHẠY (không kéo theo `ultralytics`/`torch`):

```bash
pip install -r requirements.txt
```

Cài thêm bộ công cụ để chạy được `pytest`/`black`/`ruff` trên chính thiết bị, ghim đúng phiên
bản đang dùng để kiểm thử (xem `requirements-dev.txt`):

```bash
pip install pytest==9.1.1 black==24.4.2 ruff==0.16.1
```

⚠️ **Không** chạy `pip install -r requirements-dev.txt` trên Raspberry Pi 5: tệp này kéo theo
`ultralytics` → `torch` bản đầy đủ cùng khoảng **2,5 GB** thư viện CUDA của NVIDIA (bao gồm
`nvidia-cudnn-cu13`, `nvidia-cublas`, `triton`, ...) — vô dụng trên thiết bị không có GPU
NVIDIA. Tệp `requirements-dev.txt` chỉ dùng trên máy phát triển để export mô hình.

Việc export mô hình (`scripts/export_detector.py`, `scripts/export_detector_ncnn.py`) thực
hiện trên máy phát triển, sau đó **chép tệp kết quả** (`models/*.onnx`, `models/*.ncnn`) sang
Raspberry Pi 5 — thiết bị đích chỉ nạp mô hình đã export sẵn, không tự export.
