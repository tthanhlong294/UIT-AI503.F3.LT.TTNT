# Tuần 7 — 26/08 đến 01/09/2026

**Phase**: 2 — Phát hiện khuôn mặt, chuyển sang backend NCNN · Phase 3 vẫn mở song song

---

## Mục tiêu tuần

Đóng nốt phần backend NCNN cho khối phát hiện (export mô hình rồi tích hợp vào khối `src/detector/`),
và ổn định lại quy trình làm việc sau khi mã việc `P3-01b` cuối tuần trước cho thấy kịch bản kiểm gộp
gây nhiều vấn đề hơn nó giải quyết.

## Đã thực hiện

### 1. Gộp `P3-01b` vào `dev`, đóng băng `docs/kiem-may/` (27/08, 16:35–16:41)

Mã việc `P3-01b` (vá ba lỗ hổng cấu hình của khối nhận diện) đã được tường thuật đầy đủ ở
`docs/nhat-ky/tuan-06.md` §11 — đạt có điều kiện ngay vòng đầu, chín phép đột biến, ba bài học vận
hành. Tuần này chỉ ghi phần nối tiếp:

- `e445c6f`: sửa kịch bản kiểm bắt buộc tắt trình phân trang của git — bài học thứ nhất của biên bản
  `P3-01b` được vá ngay trong ngày, trước khi merge.
- `f8aa44a` → `baf86ec`: gộp nhánh `feat/p3-01b-chan-gia-tri-hong` vào `dev`.
- `ee42d80`: lưu ba kịch bản `.ps1` của `P3-01b` vào `docs/kiem-may/` trước khi đóng thư mục — các
  kịch bản này là **di tích**, biên bản `P3-01b` trỏ tới chúng nên không xoá được mà không làm biên
  bản mất khả năng tái lập.

### 2. Đổi quy trình lần hai: bỏ kịch bản kiểm gộp, quay lại lệnh rời (27–28/08)

Ba ngày sau khi chuyển sang kịch bản gộp (tuần 6), quy trình bị đổi lại. `docs/kiem-may/README.md`
ghi rõ ba vấn đề phát sinh:

| Vấn đề | Biểu hiện |
|---|---|
| Vòng lặp sửa mã dài ra | Mỗi lần `coder` sửa một dòng, người dùng lại phải chạy toàn bộ kịch bản và dán về; nhịp chờ nằm giữa mọi bước |
| Kịch bản trở thành phần mềm thứ hai phải bảo trì | Đã có lỗi thật: kịch bản treo ở trình phân trang vì quên tắt |
| Đầu ra gộp khó đọc | Lỗi thật nằm lẫn giữa hàng trăm dòng của các đoạn xanh |

Từ 27/08/2026 (`cd5cb5b`, `ff711a2`), ranh giới đặt lại theo **ai chạy cái gì**, không theo **đóng
gói thế nào**: `coder` tự chạy phần tự kiểm (`black`, `ruff`, `pytest` hai môi trường, đột biến) trong
phiên riêng của nó; `code-reviewer` và `training` đưa lệnh rời từng khối, người dùng chạy và dán kết
quả nguyên văn về. Thư mục `docs/kiem-may/` đóng băng, không nhận thêm kịch bản `.ps1` nào.

Cùng đợt sửa quy trình này, hai quy ước mới được ghi vào `CLAUDE.md`: bảng ba môi trường đo
(`pc_x86` / `docker_arm64` / `pi5`) kèm vai trò và giới hạn của từng môi trường, và quy ước xem
notebook là **phương tiện trình bày chính thức** của đồ án — commit kèm đầu ra, không phải bản nháp.

### 3. Mã việc `P2-04` — export YOLOv8n-face sang NCNN và kiểm chứng (27–28/08)

| Nhịp | Kết quả |
|---|---|
| Review vòng 1 | 🔴 Trả lại — 1 lỗi cần sửa |
| Review vòng 2 (28/08) | 🟡 Đạt có điều kiện — 2 điều kiện trước khi gộp |

Xuất mô hình phát hiện sang định dạng NCNN (`model.ncnn.param` + `model.ncnn.bin`) và kiểm chứng độ
khớp với bản gốc trên cùng tập ảnh — kết quả kiểm chứng này về sau được trích dẫn trong Chương 4 §4.3.1
(độ chồng khớp khung bao 0,9999996, sai lệch điểm mốc ở mức 10⁻⁵ pixel).

Kiểm định: toàn kho `-m "not slow"` tăng từ 410 lên 411 ca sau vòng 2; container `faceid:arm64` tăng
từ 409 lên 410 ca (1 skip). Tệp mới `tests/test_export_detector_ncnn.py` có 30 ca không đánh dấu
`slow` cộng 2 ca `slow` chạy export thật vào thư mục tạm. Ba phép đột biến đều đỏ đúng ca được chỉ
định (bỏ kiểm tồn tại tệp `.ncnn.param`, vô hiệu guard thiếu điểm mốc, giả lập môi trường sai).

Merge vào `dev`: `8ff1063`.

### 4. Mã việc `P2-05` — backend NCNN cho khối phát hiện (28–30/08, merge 01/09)

| Nhịp | Kết quả |
|---|---|
| Đặc tả | `c7c6273` (28/08) |
| Đặc tả vòng 2 | `29d76a6` (30/08) — đổi ngưỡng IoU |
| Review | 🟡 Đạt có điều kiện — 0 lỗi 🔴, 0 lỗi 🟡, 5 mục 🔵 |

Bọc mô hình NCNN đã export ở `P2-04` thành một backend cùng giao diện với backend ONNX đã có, để
`src/detector/factory.py` chọn được giữa hai bộ suy luận qua cấu hình.

Kiểm định: toàn kho `446 passed` (26 warnings); riêng ba tệp mới của khối phát hiện `69 passed`, 0
skip; container `faceid:arm64` `432 passed, 1 skipped, 13 deselected`. Người review tự dựng thêm một
phán quyết về "số đo rò rỉ bộ nhớ" ở hai ca kiểm và kết luận **không phải rò rỉ ở mức chặn** — ghi lại
trong biên bản để không lặp lại lo ngại này ở mã việc sau.

Feat: `cfbb6a1` (01/09, 14:17). Merge: `121968a` (01/09, 15:18).

### 5. Mở đặc tả `P2-06` — benchmark hợp nhất ONNX và NCNN trong một ma trận (01/09, 15:27)

`4b37c97`: đặc tả cho `scripts/benchmark_detect.py` đo được cả hai bộ suy luận trong cùng một ma trận
12 ô, thay vì hai script tách rời như bản `P2-03`. Phần viết mã và kiểm định rơi sang tuần 8.

### 6. Báo cáo

Không có mục báo cáo mới hoàn thành trong tuần này — trọng tâm dồn vào khối phát hiện NCNN và ổn định
lại quy trình làm việc. Chương 2 và Chương 3 giữ nguyên trạng thái đã ghi ở tuần 6.

## Số liệu

| Hạng mục | Giá trị | Nguồn |
|---|---|---|
| Mã việc đóng trong tuần | 2 (`P2-04`, `P2-05`) | `docs/review/` |
| Mã việc mở đặc tả cuối tuần | 1 (`P2-06`) | `docs/dac-ta/P2-06-benchmark-ncnn.md` |
| Ca kiểm thử toàn kho, cuối tuần | 446 passed | biên bản `P2-05-detector-ncnn.review.md` |
| Ca kiểm thử container `faceid:arm64`, cuối tuần | 432 passed, 1 skipped, 13 deselected | biên bản `P2-05-detector-ncnn.review.md` |
| Độ khớp NCNN với bản gốc (bbox) | 0,9999996 | `results/export_ncnn_20260827_2144.json` |
| Số lần đổi quy trình làm việc kể từ đầu đồ án | 2 (tuần 6: gộp thành kịch bản; tuần 7: quay lại lệnh rời) | `docs/kiem-may/README.md` |

## Vướng mắc

- **Vẫn chưa có Raspberry Pi 5 và camera.** Sang tuần thứ tư kể từ khi vướng mắc này được ghi lần
  đầu. Cổng C của Phase 2 vẫn mở vì mọi số đo đang có đều của máy phát triển (`pc_x86`).
- **Ba Phase vẫn mở song song** (Phase 1, 2, 3) — cùng lý do đã ghi ở tuần 6: mọi thứ chặn đều chặn ở
  cùng một chỗ là phần cứng.
- **Còn ba tuần tới hạn nộp 23–24/09.** Phase 4, 5, 6, 7 chưa bắt đầu.

## Kế hoạch tuần sau

- Viết mã và kiểm định cho `P2-06` (ma trận đo hợp nhất), sau đó dùng nó để chạy mẻ đo ba lượt trên
  máy phát triển nhằm chuẩn bị sẵn quy trình cho khi có Pi 5.
- Bắt đầu phương án A của khối nhận diện (`dlib`/`face_recognition`) song song với việc chốt cấu hình
  phát hiện, vì hai việc không phụ thuộc lẫn nhau.
- Tiếp tục theo dõi tiến độ mua phần cứng — đây vẫn là rủi ro tiến độ lớn nhất.

---

*Nguồn: lịch sử git từ `e445c6f` đến `4b37c97`; biên bản `docs/review/P2-04-export-ncnn.review.md` và
`docs/review/P2-05-detector-ncnn.review.md`; `docs/kiem-may/README.md`; `results/export_ncnn_20260827_2144.json`.*
