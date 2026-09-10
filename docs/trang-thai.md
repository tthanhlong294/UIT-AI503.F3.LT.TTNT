# Trạng thái đồ án — đang ở đâu, còn nợ gì

> Tệp này tách ra từ `CLAUDE.md` §8 ngày 10/09/2026. Lý do tách: nó dài thêm sau mỗi mã việc và
> **không bao giờ ngắn lại**, trong khi `CLAUDE.md` được nạp lại ở mỗi lượt của mọi vai.
>
> **Ai đọc tệp này**: phiên chính, `onboarding-with-skills`, `training`, `paper-writer`.
> `spec-writer`, `coder` và `code-reviewer` **không cần đọc** — việc của họ được xác định bởi
> đặc tả và bộ quy tắc, không bởi tiến độ.
>
> ⚠️ **Kỷ luật giữ tệp này ngắn**: chỉ ghi **trạng thái hiện tại** và **việc còn nợ**.
> Diễn biến, bài học, chuyện đã khép lại thì đẩy về `docs/nhat-ky/tuan-XX.md` và xoá khỏi đây.
> Cập nhật mỗi khi qua Phase mới hoặc gộp xong một mã việc.

---

## Vị trí hiện tại (10/09/2026 — Tuần 9)

**Phase 0 đóng trọn**: bước 0.4 đóng ngày 05/09/2026 khi Raspberry Pi 5 và webcam USB về tới nơi;
`P0-05` gộp ngày 10/09/2026 nên **không còn mã việc nào có đặc tả mà chưa cài**.

**Phase 1, 2 và 3 đang mở song song**; lý do ghi ở `docs/dieu-chinh-pham-vi.md`.

**26 mã việc đã qua đủ 5 nhịp và gộp `dev`** — mỗi mã việc một biên bản trong `docs/review/`,
đếm số tệp ở đó là ra số chuẩn, đừng chép lại con số trong mục này mà không kiểm.
Ba mã việc gần nhất: `P2-07` (cờ `--nguon camera` cho `benchmark_detect.py`, bước 2.5) ·
`P2-08` (đặt FOURCC MJPG, áp `CAP_PROP_FPS`, phơi thông số camera thật) · `P0-05` (làm sạch
bit quyền nhánh dự phòng, thêm `--strict-config`).

`P2-06d` **đã bỏ** theo quyết định ngày 04/09/2026: khối phát hiện đã qua ba vòng kiểm, thêm
vòng thứ tư không đổi kết luận nào.

### Số ca kiểm thử

Ghi kèm mốc, môi trường và bộ lọc theo quy ước ở `.claude/agents/spec-writer.agent.md`.

| Môi trường | Bộ lọc | Kết quả | Mốc |
|---|---|---|---|
| — | — | **878 ca thu thập** | `dev` sau khi gộp `P0-05` |
| `pc_x86` | không lọc marker | `875 passed, 3 skipped` | cùng mốc |
| `docker_arm64` | `-m "not slow"` | `845 passed, 1 skipped, 32 deselected` | cùng mốc |
| `pi5` | — | **[CHƯA ĐO Ở MỐC NÀY]** | gần nhất `518 passed, 5 skipped, 32 deselected` tại `P0-04`, đã lạc hậu 323 ca |

Ba ca skip trên `pc_x86` là 49, 50, 51 của `P0-05`, gác theo nền tảng vì bit quyền chỉ có nghĩa
trên POSIX.

**Còn nợ trên `pi5`**: §14b của `P0-05` — chỉ cần chạy `pytest`, không cần camera.

---

## Chỉ tiêu đã chốt và số đo

**FPS riêng module phát hiện ≥ 10: ✅ ĐẠT.** Đo trên Pi 5 thật ngày 05/09/2026, ba lượt,
8/12 cấu hình vượt ngưỡng, cao nhất **60,6 FPS** (NCNN, 320 px, 4 luồng). Nguồn:
`results/bench_detect_20260905_{1911,1914,1916}.csv`.

Bước 2.7 cũng xong: 10,7 phút tải liên tục, `throttled=0x0`, nhiệt đỉnh 65,55 °C, hiệu năng lệch
dưới 1,4 % so với lượt ngắn (`results/bench_detect_20260905_2011.csv`).

**Bước 2.5 đã đo lần đầu ngày 09/09/2026** trên Pi 5 với camera thật, ba lượt 300 khung, NCNN
320 px 4 luồng, 1,0 m: `fps_tb` **51,2** (vượt ngưỡng 10 gấp năm lần), `fps_tong_tb` **10,02**,
lấy khung p50 **80 ms**, nhiệt 42,2 → 43,9 °C, `throttled=0x0`.

⚠️ **Ba tệp kết quả lượt đó còn nằm trên Pi, chưa vào `results/`** — phải copy về và commit,
vì chúng là đối chứng "trước FOURCC" cho lượt đo lại.

Lấy khung 80 ms là do webcam chạy YUYV: `v4l2-ctl` cho thấy ở 1280×720 định dạng này **chỉ có
10/5/1 fps**, còn MJPG có 30 fps. `P2-08` đặt FOURCC sang MJPG để nới trần; **cần đo lại ba lượt**
rồi mới chốt Cổng C. Kỳ vọng lấy khung p50 xuống ≈ 33 ms và `fps_tong_tb` lên ≈ 19; vượt 27 thì
phải nghi bộ đệm khung trả về khung cũ.

⚠️ `benchmark_detect.py` **chưa ghi `fourcc_thuc_te` vào `.meta.json`** (mục 🔵-2 biên bản
`P2-08`). Bằng chứng định dạng thật lấy từ dòng log `mo()` in ra đầu mỗi lượt, dán vào nhật ký.

---

## Notebook

| Notebook | Trạng thái |
|---|---|
| `01_eda_khuon_mat.ipynb` (bước 1.13) | **vẫn chặn** — chưa thu gallery |
| `04_so_sanh_moi_truong.ipynb` | **hết chặn** từ 05/09/2026, đã có số `pi5` đặt cạnh `pc_x86` và `docker_arm64` |
| `06_nguong_va_roc.ipynb` (bước 3.5) | **hết chặn** từ 08/09/2026 |
| `05_khoi_nhan_dien.ipynb` | viết 04/09/2026 sau khi `P3-02` đóng |

`P3-05` đã sinh `results/bench_recognize_{dlib,arcface}_20260908_0707.{csv,nguong.csv}`, nhưng đó
là mẻ **kiểm chức năng trên LFW**, không phải số báo cáo. `05_khoi_nhan_dien.ipynb` minh hoạ hai
backend trên LFW, cũng không sinh số cho báo cáo.

Notebook là phương tiện trình bày chính khi bảo vệ, không phải bản nháp — xem `CLAUDE.md` §2.9.

---

## Gallery hiện có — có bẫy

`data/embeddings/{dlib,arcface}/`, 8 người từ LFW, dựng lại ngày 06/09/2026 trên commit `bfc9026`
với `git_dirty: false`.

⚠️ Dựng bằng cờ `--toi-thieu 3` thay cho ngưỡng 10 trong cấu hình, vì không danh tính LFW nào đủ
10 ảnh. Đây là gallery **kiểm chức năng**, không dùng cho bất kỳ con số nào trong báo cáo;
`gallery.meta.json` ghi cả hai ngưỡng để không lẫn.

⚠️⚠️ **Gallery này KHÔNG còn probe genuine nào.** `enroll.py` dùng trọn ảnh của mỗi người để đăng
ký, manifest cho `so_anh_dung == so_anh_tim_thay` ở cả 8 người (38 ảnh). Lấy chính những ảnh đó làm
probe thì mỗi ảnh được so với một vectơ trung bình **có chứa chính nó**, cho điểm cao giả tạo, kéo
FRR xuống gần 0 mà không gì báo lỗi. Đặc tả `P3-05` xử lý bằng chế độ `chia` và phép loại trừ theo
mã băm nội dung; **đừng bao giờ đo trực tiếp trên thư mục này**.

---

## Rủi ro tiến độ

⚠️ **Lớn nhất: chưa thu được dữ liệu khuôn mặt.** Phần cứng đã hết là lý do — Pi 5 và webcam USB có
từ 05/09/2026, camera mở được bằng chính mã của đồ án. Nhưng **gallery 2–3 người nhà (bước 1.3) và
tập impostor in-domain (bước 1.6) vẫn chưa thu**, và **bốn trên năm chỉ tiêu cam kết đều cần
chúng**: độ chính xác nhận diện, ba con số FAR, tỉ lệ phát hiện giả mạo, độ trễ điều khiển đầu-cuối.
Đây là việc phụ thuộc lịch của người khác nên không rút ngắn được bằng cách làm nhanh hơn — phải
khởi động sớm nhất có thể.

⚠️ **Thứ hai: chưa có ngoại vi cho Phase 5.** Chưa có module relay, LED, LED phát IR. Chỉ tiêu độ
trễ điều khiển < 2 s không đo được nếu thiếu. Mua tại cửa hàng linh kiện nhanh hơn đặt online
đáng kể.

---

## Báo cáo

Chương 1 §1.1–1.3 xong · Chương 2 xong 6/7 mục (§2.7 chặn vì chưa có thiết bị), đã bổ sung
§2.6.4–2.6.6 về NCNN và PNNX · Chương 3 §3.2 và §3.3 xong · Chương 5 khung.

**Chương 4 đã mở** (`report/chapters/ch4-trien-khai-thuc-nghiem.md`): §4.1 ba môi trường, §4.3.1
kiểm chứng chuyển đổi NCNN, §4.3.2 và §4.3.3 kết quả trên `pc_x86`, **§4.3.4 kết quả trên Pi 5
thật** (Bảng 4.4 mười hai cấu hình, Bảng 4.5 tỉ lệ tăng tốc NCNN 2,07–3,35 lần, Bảng 4.6 đối chiếu
hai môi trường), và **§4.6 Bảng 4.7 đối chiếu chỉ tiêu** — dòng FPS phát hiện đã ✅ Đạt, bốn dòng
còn lại `[CHƯA ĐO]`.

Một dữ kiện dùng được cho §4.1: container `faceid:arm64` chạy Python **3.11.16**, Pi OS chạy
**3.11.2** — cùng nhánh 3.11 nhưng khác nhau đúng ở mốc 3.11.4, nơi `tarfile.FilterError` được
backport. Bảy ca test xanh trong container mà đỏ trên Pi. Đây là ca cụ thể chứng minh
`docker_arm64` không thay thế được `pi5`, kể cả ở mức tính đúng đắn chức năng chứ không chỉ tốc độ.

Nhật ký tuần 1–8 đã ghi đủ. Trọng số mô hình đã tải đủ, `models/README.md` bảng A đầy đủ, §3.3 đã
chốt cách chuẩn hoá của mô hình nhận diện bằng thực nghiệm.

Nhật ký tuần lưu ở `docs/nhat-ky/tuan-XX.md`, viết vào **cuối mỗi tuần**, không dồn.
