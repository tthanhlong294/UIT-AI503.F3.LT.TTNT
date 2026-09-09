# Tuần 8 — 02 đến 08/09/2026

**Phase**: 2 — khép Cổng C bằng số đo trên phần cứng đích · 3 — nhận diện danh tính, hai backend

**Sự kiện lớn nhất trong tuần**: nhận được Raspberry Pi 5 và webcam USB, dựng môi trường trên phần
cứng đích và chạy mẻ đo đầu tiên ngoài máy phát triển.

---

## Mục tiêu tuần

Khép ma trận benchmark thống nhất cho khối phát hiện, đóng phương án A của khối nhận diện (`dlib`),
mở script đăng ký (`enroll.py`) và factory chọn backend — đồng thời, ngay khi phần cứng về tay, dựng
môi trường và lấy mẻ đo đầu tiên trên Raspberry Pi 5 thật.

## Đã thực hiện

### 1. Mã việc `P2-06` — benchmark đo được cả ONNX và NCNN trong một ma trận 12 ô (02/09)

| Nhịp | Kết quả |
|---|---|
| Feat | `5cd62b3` (14:54) |
| Merge | `2ae8ec2` (14:54) |
| Review | 🟡 Đạt có điều kiện — 0 lỗi 🔴, 0 lỗi 🟡, 6 mục 🔵 |

Gộp hai script đo tách rời của `P2-03` thành một `scripts/benchmark_detect.py` duy nhất, quét được cả
bốn tổ hợp bộ suy luận × độ phân giải và ba mức số luồng trong cùng một lượt chạy, ghi ra một cặp
`.csv`/`.meta.json`.

Kiểm định: toàn kho `458 passed` (446 mốc `P2-05` + 12 ca mới); riêng `test_benchmark_detect.py`
`59 passed` (47 cũ + 12 mới); container `faceid:arm64` `444 passed, 1 skipped, 13 deselected`.

### 2. Mã việc `P2-06b` — ca đối kháng backend, dry-run không nạp mô hình (02–03/09)

| Nhịp | Kết quả |
|---|---|
| Đặc tả | `64c8e8f` (02/09) |
| Feat | `c50789f` (03/09) |
| Merge | `743640b` (03/09) |
| Review | 🟡 Đạt có điều kiện — 0 lỗi 🔴, 0 lỗi 🟡, 4 mục 🔵. Được commit ngay |

Thêm chế độ `dry-run` không nạp mô hình thật (dùng để kiểm cấu trúc lệnh CLI mà không cần trọng số),
và ca kiểm "đối kháng" — cố tình đưa backend sai để xác nhận `benchmark_detect.py` không âm thầm dùng
nhầm bộ suy luận.

Kiểm định: `70 passed, 3 deselected` (bộ đích); toàn kho `-m "not slow"` `453 passed, 14 deselected`;
bộ đích không lọc marker `73 passed, 0 skipped` — ca `slow` chạy thật, không skip; toàn kho `467
passed` (458 + 9); container `452 passed, 1 skipped, 14 deselected` (444 + 8 ca không-`slow`). Ba phép
đột biến (giả lập đoán backend từ tên tệp, ép luôn trả về ONNX, xoá khoá `ncnn` khỏi metadata phần
mềm) đều đỏ đúng ca được chỉ định.

### 3. Mẻ đo ba lượt trên máy phát triển — ma trận 12 ô, dữ liệu dùng cho Bảng 4.2/4.3 (03/09, 22:53)

`56a3bd1`: chạy `scripts/benchmark_detect.py` (bản `P2-06b`) ba lượt tại ba thời điểm khác nhau trong
đêm, sinh `results/bench_detect_20260903_{2022,2040,2044}.csv`. Đây chính là bộ dữ liệu mà Chương 4
§4.3.2–§4.3.3 dùng để lập luận: chỉ 2/6 cấu hình đủ căn cứ kết luận vì mức dao động giữa các lượt trên
máy phát triển lớn hơn khác biệt giữa hai bộ suy luận (dao động ONNX Runtime trung bình 41,4 %, NCNN
trung bình 7,7 %).

### 4. Mã việc `P2-06c` — `git_dirty` giới hạn đúng phạm vi đường dẫn ảnh hưởng phép đo (03–04/09)

| Nhịp | Kết quả |
|---|---|
| Đặc tả | `85a12ed` (03/09, 22:56) |
| Fix | `e70ffa8` (04/09, 07:37) |
| Merge | `fd002cd` (04/09, 08:10) |
| Review | 🟡 Đạt có điều kiện — 0 lỗi 🔴, 0 lỗi 🟡, 6 mục 🔵. Được commit ngay |

Trước bản vá, cờ `git_dirty` trong `.meta.json` bị bẩn bởi bất kỳ thay đổi nào trong cây làm việc, kể
cả những tệp không ảnh hưởng gì tới phép đo (ví dụ tài liệu). Bản vá giới hạn cờ này chỉ xét đúng
những đường dẫn có thể ảnh hưởng tới kết quả đo, đồng thời thêm khoá `git_dirty_toan_cay` để không
mất thông tin về tình trạng cây làm việc nói chung.

Biên bản review tự nêu lý do mã việc này đáng soi kỹ hơn mức thường: **đoạn mã này quyết định cờ
`git_dirty` của mọi lượt đo sau, kể cả các lượt trên Raspberry Pi 5 sau này dùng để kết luận các chỉ
tiêu cam kết** — sai theo hướng quá lỏng thì số liệu không truy vết được vẫn lọt vào báo cáo mà không
ai biết. Vì vậy lượt kiểm định thêm hẳn một nhóm lệnh dùng git thật và một phép đột biến ngoài đặc tả
(ĐB2b) để soi riêng hướng lỏng.

Kiểm định: `72 passed` (63 mốc `P2-06b` + 9 ca mới) — mốc so sánh của bốn phép đột biến; toàn kho
`-m "not slow"` `462 passed, 14 deselected` (453 + 9); toàn kho không lọc marker `476 passed` (467 +
9).

Tiếp nối cùng ngày: `1f59162` (04/09, 12:17) — chạy thật một lượt đo để kiểm chứng cờ `git_dirty` hoạt
động đúng sau bản vá, trên chính máy phát triển.

### 5. Cập nhật báo cáo: Chương 2 §2.6.4–2.6.6 (NCNN, PNNX) và mở Chương 4 (04/09, 11:03)

`d8c4adf`: bổ sung ba mục Chương 2 về NCNN và công cụ chuyển đổi PNNX; mở `report/chapters/
ch4-trien-khai-thuc-nghiem.md` với §4.1 (ba môi trường và quy ước đo), §4.3.1 (kiểm chứng chuyển đổi
mô hình), §4.3.2–§4.3.3 (kết quả sơ bộ trên `pc_x86` và lý do chưa kết luận được). Mọi mục cần phần
cứng đích vẫn để `[CHƯA ĐO]` tại thời điểm này — Pi 5 chưa về tay.

### 6. Mã việc `P3-02` — backend `dlib`, phương án A của khối nhận diện (04/09)

| Nhịp | Kết quả |
|---|---|
| Đặc tả | `fc86902` (11:28) |
| Feat | `b7da43b` (16:49) |
| Review vòng 1 | 🔴 Trả lại — 1 lỗi CHẶN-B, sửa **trọn trong** `tests/test_dlib_backend.py`; `src/recognizer/dlib_backend.py` không cần đổi dòng nào |
| Review vòng 2 | ✅ Đạt — CHẶN-B-1 đã gỡ, không phát sinh mục 🔴 hay 🟡 mới |
| Merge | `7baaac8` (17:25) |

Cài đặt phương án A (`face_recognition`/dlib, 128 chiều) cùng giao diện với phương án B đã có.

**Lỗ hổng ở vòng 1 nằm trong bộ kiểm thử, không nằm trong mã sản phẩm.** Người review dựng một phép
đột biến bỏ bước đổi kênh màu BGR sang RGB trước khi đưa vào mô hình — một lỗi kinh điển khi ghép
OpenCV (đọc ảnh theo BGR) với các mô hình huấn luyện trên RGB. Bộ kiểm thử vòng 1 **không phân biệt
được** hai trường hợp: có đổi kênh và không đổi kênh đều cho cùng kết quả kiểm (`1 failed, 24 passed`,
cùng một ca đỏ, cùng một con số `0,9955222010612488`, y hệt trước và sau đột biến). Nghĩa là bộ kiểm
thử đã lỡ có một ca đỏ sẵn từ trước vì lý do khác, che khuất mất việc phép đột biến không bị bắt.
Toàn kho vòng 1: `1 failed, 500 passed`.

Vòng 2 thêm ca `test_dong16` canh riêng bước đổi kênh màu. Kiểm định: `25 passed, 0 failed` (bộ đích);
toàn kho `501 passed, 0 failed` — đúng 501 ca như vòng 1 (500 + ca đỏ được sửa thành xanh), không ca
nào bị xoá để lấy màu xanh; container `faceid:arm64` `-m "not slow"` `15 passed, 2 skipped, 8
deselected` — hai ca skip đúng dự kiến vì image `faceid:arm64` chưa có gói `dlib-bin`. Phép đột biến
lặp lại ở vòng 2 cho `1 failed` đúng một mình ca `test_dong16`, và bước khôi phục cho `sha256` trùng
khớp bản gốc.

### 7. Notebook `05` — minh hoạ khối nhận diện, hai backend trên LFW (04/09, 18:43)

`46a7d62`: `notebooks/05_khoi_nhan_dien.ipynb` — đặt hai backend cạnh nhau trên ảnh LFW, minh hoạ điểm
mốc, vectơ đặc trưng và mức độ tách biệt giữa các danh tính. Notebook này **không sinh số cho báo
cáo**, thuần minh hoạ trực quan phục vụ trình bày.

### 8. Mã việc `P3-03` — script `enroll.py` và `factory` chọn backend (04–05/09)

| Nhịp | Kết quả |
|---|---|
| Đặc tả | `a2023b0` (04/09, 20:01) |
| Feat | `6632e79` (04/09, 21:43) |
| Fix vòng 2 | `5605b9e` (05/09, 07:35) |
| Review | `e7d851a` (05/09, 07:36) |
| Merge | `7065c98` (05/09, 07:36) |

`scripts/enroll.py` sinh vectơ đặc trưng trung bình từ tập ảnh enroll cho từng người, ghi ra
`data/embeddings/<backend>/`; `src/recognizer/factory.py` chọn backend theo cấu hình.

Review vòng 1: 🔴 trả lại — một lỗi CHẶN-B, backend ném `ValueError` không phân biệt được nguyên nhân
"thiếu ảnh" với "lỗi mô hình", nên script xử lý sai đường ở nhánh đó. Toàn kho vòng 1: `529 passed`.
Sáu phép đột biến được dựng để kiểm; đáng chú ý ĐB1 (thay bước gọi backend bằng tính trung bình và
chuẩn hoá tự viết) tuy có làm đỏ 10 ca nhưng **qua một cơ chế khác** với cơ chế mà đặc tả kỳ vọng —
ghi lại trong biên bản như một điểm cần diễn giải thêm, không tính là ca kiểm thất bại.

Vòng 2: 🟡 đạt có điều kiện — CHẶN-B-1 đã sửa bằng cách tách riêng lớp ngoại lệ `LoiMoHinh` cho nhánh
lỗi mô hình, khác với `LoiCauHinh`/thiếu ảnh. Kiểm định: bộ đích `30 passed` (+2 so với vòng 1); toàn
kho `531 passed` (+2); container `498 passed, 1 skipped, 32 deselected` (+2). Ba phép đột biến bổ
sung: ĐB7 xác nhận ca mới canh đúng chiều thay đổi (đảo ngược bản vá thì đúng một ca đỏ); ĐB8 và ĐB9
**không bị bắt** — hai lỗ hổng còn sót ở ranh giới giữa hai lớp ngoại lệ và ở biên số ảnh tối thiểu.
Cả hai được ghi thành góp ý 🔵 không chặn việc gộp, và tách thành mã việc riêng (`P3-04`).

### 9. Cập nhật ghi chú vận hành trong `CLAUDE.md` (05/09, 07:44)

`3c77987`: cập nhật mục "Ghi chú vận hành" sau khi `P3-03` hoàn thành — liệt kê đủ mười sáu mã việc đã
qua năm nhịp và gộp vào `dev`, ghi rõ gallery hiện có (8 người từ LFW, ngưỡng tối thiểu 3 ảnh, chỉ
dùng để kiểm chức năng chứ không dùng cho số liệu báo cáo).

### 10. Mở mã việc `P3-04` — `enroll.py` ghi gallery nguyên khối (05/09)

`57b874c`: đặc tả vá hai lỗ hổng kiểm thử còn sót ở `P3-03` vòng 2 (ĐB8, ĐB9), và đổi cách ghi gallery
sang **ghi qua thư mục tạm rồi đổi tên**, để thư mục đích chỉ tồn tại ở hai trạng thái — chưa có, hoặc
có đủ cả `.npy`, `manifest.csv`, `gallery.meta.json` — không còn trạng thái dở dang khi lượt `enroll`
dừng giữa chừng.

Nhánh `feat/p3-04-enroll-ghi-nguyen-khoi` đã có một commit mã (`e7923e3`, "ghi gallery nguyên khối qua
thư mục tạm"), nhưng **chưa có biên bản review** và **chưa gộp vào `dev`**. Trạng thái đang treo, chưa
tính là mã việc hoàn thành.

### 11. Sự kiện lớn nhất trong tuần: có Raspberry Pi 5 và webcam USB (05/09)

Phần cứng về tay sau bốn tuần chờ đợi — vướng mắc được nhắc lại liên tục từ nhật ký tuần 5. Cài đặt
Raspberry Pi OS 64-bit, tạo môi trường ảo Python, và lần đầu chạy mã của đồ án trên phần cứng đích.
Quá trình này lộ ra bốn phát hiện kỹ thuật, gộp chung thành mã việc `P0-04` (**chưa làm**):

1. **28 commit chưa được đẩy lên GitHub.** Bản clone đầu tiên trên Pi lấy về mã của khoảng bốn tuần
   trước, thiếu toàn bộ khối phát hiện NCNN và các mã việc `P2-04` đến `P3-03`. Phải đẩy lại nhánh
   `dev` lên máy chủ trước khi có thể tiếp tục trên Pi.
2. **`scripts/download_lfw.py` không chạy được trên Python của Pi OS.** Script dùng `tarfile` với
   tham số `filter` và lớp `FilterError`, hai thứ chỉ có từ Python 3.11.4 trở lên, trong khi Raspberry
   Pi OS Bookworm đóng gói Python 3.11.2. Hậu quả là bảy ca kiểm thử đỏ trên Pi. Đáng chú ý:
   **container ARM64 không phát hiện được lỗi này**, vì Python bên trong container là một bản dựng
   khác với Python của chính hệ điều hành Pi. Đây là dẫn chứng cụ thể, đo được, cho luận điểm đã nêu ở
   Chương 4 §4.1 rằng môi trường `docker_arm64` không thay thế được phép kiểm trên `pi5` thật — không
   chỉ ở tốc độ, mà ở cả tính đúng đắn.
3. **Hai ca kiểm thử phụ thuộc thư mục dữ liệu bị `.gitignore` chặn.** Trên máy sạch (Pi chưa có
   `data/`), một ca đỏ đúng như kỳ vọng, nhưng ca còn lại **xanh giả** — nó không kiểm tra được điều
   cần kiểm vì thiếu dữ liệu đầu vào khiến nhánh kiểm bị bỏ qua một cách âm thầm.
4. **`requirements-dev.txt` kéo theo khoảng 2,5 GB thư viện CUDA của NVIDIA** lên một máy không có GPU
   NVIDIA, do khai báo `ultralytics` kéo theo `torch` bản đầy đủ. Ngược lại, gói `ncnn` — vốn là phụ
   thuộc **chạy** thật sự trên Pi — lại bị xếp nhầm vào nhóm phụ thuộc chỉ dành cho máy phát triển.

Bốn việc này được gộp thành mã việc `P0-04`, **chưa bắt đầu** — cần một đặc tả riêng trước khi giao
cho `coder`.

**Bằng chứng khả chuyển đáng ghi nhận**: sau khi đồng bộ đúng mã nguồn, **490 trên 531 ca kiểm thử
chạy đúng ngay trên Python 3.11.2 ARM64 mà không phải sửa một dòng mã sản phẩm nào** — phần chênh lệch
41 ca là hệ quả trực tiếp của bốn phát hiện ở trên (bảy ca lỗi Python, một ca xanh giả, một số ca cần
mô hình/dữ liệu chưa có trên máy mới), không phải lỗi logic của khối phát hiện hay khối nhận diện.

Bước 0.4 của Phase 0 (cài Raspberry Pi OS 64-bit, venv, mở được camera) nay đã đóng — camera USB mở
được bằng chính mã của đồ án. **Phase 0 nay đủ 6/6 bước**, khép lại một mục còn treo từ tuần 1.

**Mẻ đo đầu tiên trên phần cứng đích.** Ba lượt benchmark khối phát hiện chạy trên Pi 5 (Raspberry Pi
5 8 GB, có tản nhiệt chủ động, không màn hình, qua SSH), sinh
`results/bench_detect_20260905_{1911,1914,1916}.csv` cùng ba tệp `.meta.json`. Kết quả: cả 12 cấu hình
đều giữ tỉ lệ phát hiện 100 %; 8/12 cấu hình vượt ngưỡng 10 FPS, cao nhất 60,6 FPS (NCNN, 320 px, 4
luồng), thấp nhất trong nhóm đạt là 10,58 FPS (ONNX Runtime, 320 px, 1 luồng); nhiệt độ CPU tăng từ
43,0 °C lên đỉnh 62,8 °C qua ba lượt liên tiếp (~7 phút), không ghi nhận giảm xung
(`vcgencmd get_throttled` = `0x0` cả ba lần). Chi tiết đầy đủ và phân tích đã ghi vào
`report/chapters/ch4-trien-khai-thuc-nghiem.md` §4.3.4 — **Cổng C của Phase 2 nay đã có số liệu thật
để kết luận chỉ tiêu FPS riêng module phát hiện (✅ Đạt)**.

Ba tệp `.csv` và ba tệp `.meta.json` nói trên **chưa được commit** vào git tại thời điểm ghi nhật ký
này (`git status` xác nhận cả sáu tệp còn ở trạng thái chưa theo dõi).

## Số liệu

| Hạng mục | Giá trị | Nguồn |
|---|---|---|
| Mã việc đóng trong tuần (đủ 5 nhịp, đã gộp `dev`) | 4 (`P2-06`, `P2-06b`, `P2-06c`, `P3-02`, `P3-03`) | `docs/review/` |
| Mã việc đang treo cuối tuần | 1 (`P3-04` — có mã, chưa có biên bản review) | `docs/dac-ta/P3-04-enroll-ghi-nguyen-khoi.md`, nhánh `feat/p3-04-enroll-ghi-nguyen-khoi` |
| Ca kiểm thử toàn kho, cuối tuần (host) | 531 passed | biên bản `P3-03-enroll.review.md` §7 vòng 2 |
| Ca kiểm thử chạy đúng trên Pi 5 (ARM64 thật) không sửa mã | 490/531 | quan sát trực tiếp khi dựng môi trường trên Pi, 05/09/2026 |
| FPS cao nhất đo được trên Pi 5 (NCNN, 320 px, 4 luồng) | 60,6 FPS | `results/bench_detect_20260905_{1911,1914,1916}.csv` |
| Số cấu hình đạt ngưỡng ≥ 10 FPS trên Pi 5 | 8/12 | như trên |
| Nhiệt độ CPU, khởi động → đỉnh, ba lượt liên tiếp | 43,0 °C → 62,8 °C | ba tệp `.meta.json` tương ứng |
| Bước Phase 0 hoàn thành | 6/6 (bước 0.4 vừa đóng) | quan sát trực tiếp 05/09/2026 |

## Vướng mắc

- **`P0-04` (bốn phát hiện khi dựng môi trường trên Pi) chưa có đặc tả.** Cần làm trước khi tiếp tục
  chạy `scripts/download_lfw.py` hay bất kỳ script nào phụ thuộc bản Python mới hơn 3.11.2 trên Pi.
- **`P3-04` đang treo** — có mã trên nhánh riêng nhưng chưa qua review, chặn bước 3.5 (script quét
  ngưỡng cần nạp gallery, và gallery hiện tại không có manifest đầy đủ nếu một lượt `enroll` cũ dừng
  giữa chừng).
- **Bước 2.7 (10 phút chạy liên tục để quan sát giảm xung) vẫn `[CHƯA ĐO]`** — ba lượt đo tuần này
  tổng cộng khoảng 7 phút, chưa đủ điều kiện của bước này.
- **Bước 2.5 (đo FPS thời gian thực từ camera) vẫn `[CHƯA ĐO]`** — mẻ đo tuần này đọc ảnh từ đĩa, chưa
  gồm chi phí thu hình từ webcam USB vừa nhận được.
- **Chỉ còn hai tuần rưỡi tới hạn nộp 23–24/09.** Phase 4, 5, 6, 7 chưa bắt đầu; Phase 1 vẫn còn chín
  bước treo (gallery gia đình, tập impostor in-domain, domain adaptation).

## Kế hoạch tuần sau

- Viết đặc tả và đóng mã việc `P0-04` trước khi chạy tiếp bất kỳ script thu thập dữ liệu nào trên Pi.
- Đóng `P3-04` (review, gộp `dev`), sau đó mở bước 3.5 — script quét ngưỡng và dựng ROC/DET trên LFW.
- Tận dụng camera vừa có: bắt đầu bước 1.3 (thu thập gallery gia đình) và bước 1.6 (tập impostor
  in-domain), hai bước bị chặn từ đầu Phase 1 chỉ vì thiếu camera của chính hệ thống.
- Đo bước 2.5 (FPS từ camera thật) và cân nhắc lịch cho bước 2.7 (thử nghiệm nhiệt 10 phút).

---

*Nguồn: lịch sử git từ `5cd62b3` đến `e7923e3`; biên bản `docs/review/{P2-06-benchmark-ncnn,
P2-06b-doi-khang-backend, P2-06c-git-dirty-dung-pham-vi, P3-02-dlib-backend, P3-03-enroll}.review.md`;
`docs/dac-ta/P3-04-enroll-ghi-nguyen-khoi.md`; `results/bench_detect_20260903_{2022,2040,2044}.csv`;
`results/bench_detect_20260905_{1911,1914,1916}.csv` và ba tệp `.meta.json` tương ứng; quan sát trực
tiếp khi dựng môi trường trên Raspberry Pi 5 ngày 05/09/2026; `git status --short
--untracked-files=all` chạy cùng ngày.*
