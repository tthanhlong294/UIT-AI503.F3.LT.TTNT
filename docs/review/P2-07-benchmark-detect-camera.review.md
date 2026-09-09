# Review P2-07 — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-07-benchmark-detect-camera.md` (941 dòng) |
| **Mã việc** | `P2-07` — đường vào từ camera cho `benchmark_detect.py`, bước 2.5 |
| **Nhánh** | đặc tả §2 chỉ định `feat/p2-07-benchmark-detect-camera`; ảnh chụp git đầu phiên review cho thấy cây làm việc đang ở `dev` với hai tệp `M` chưa commit (xem *Việc tiếp theo*) |
| **Ngày** | 2026-09-08 |
| **Người chạy lệnh kiểm định** | người dùng — 71 khối lệnh, kết quả dán về nguyên văn |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — không còn 🔴 và không còn 🟡; **được commit ngay**. Ba mục 🔵 dưới đây là quyết định của người dùng, **không sửa trong mã việc này** |

---

## 0. Cách đọc bảng kết quả máy

Người review **không chạy lệnh nào** (R42). Mọi con số dưới đây đến từ lượt chạy của người dùng
ngày 08/09/2026. Lệnh được **chép nguyên văn** nên bảng này tự nó là thứ giữ tính tái lập: chép
dòng lệnh ra chạy lại là ra đúng con số đã dùng để kết luận. Số hiệu đánh lại theo **nhóm**
(A = phạm vi, B = ba lệnh nền + container, C = quét mẫu, D = mốc bấm giờ, E = đột biến) vì 71 khối
được phát theo nhóm; không ô nào trong bảng thiếu lệnh sinh ra nó.

---

## 1. Kết quả kiểm máy

### A. Phạm vi thay đổi và dữ liệu cấm

| # | Lệnh | Kết quả |
|---|---|---|
| A1 | `git status --short --untracked-files=all` | đúng hai dòng: `M scripts/benchmark_detect.py`, `M tests/test_benchmark_detect.py` — khớp danh sách trắng §2 ✅ |
| A2 | `git diff --stat dev` | `scripts/benchmark_detect.py \| 627 +`, `tests/test_benchmark_detect.py \| 1121 +`, tổng `1731 insertions(+), 17 deletions(-)` ✅ |
| A3 | lọc `\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$` trên `git status` | **rỗng** — không ảnh, không weights, không secret lọt git (R25) ✅ |
| A4 | `git diff dev -- tests/test_benchmark_detect.py \| Select-String '^-[^-]'` | **đúng một dòng**: `-from src.common.exceptions import LoiCauHinh` (đổi thành `import LoiCamera, LoiCauHinh`) — chốt **B1** §6 đạt ✅ |

**Không có tệp nào ngoài danh sách trắng.** `docs/`, `results/`, `report/`, `configs/`, `CLAUDE.md`,
`src/**` đều không bị đụng — đúng §2 và §12 của đặc tả.

**Diff nhánh `dia`** (người dùng liệt kê từng hunk): chỉ gồm `default=None` cho `--anh-dir`/`--seed`,
hai dòng phân giải `anh_dir_da_phan_giai`/`seed_da_phan_giai`, ba chỗ dùng biến đã phân giải, khoá
`"seed": seed_da_phan_giai`, khoá mới `"nguon": "dia"`, và `ghi_ket_qua` thêm hai tham số có mặc định.
Thân `do_mot_cau_hinh` và `tong_hop` **không có hunk nào** — đúng ràng buộc chịu lực §6.

### B. Ba lệnh nền và container

| # | Lệnh | Kết quả |
|---|---|---|
| B1 | `python -m black --check --line-length 100 src tests scripts` | `All done! 50 files would be left unchanged.` ✅ |
| B2 | `python -m ruff check src tests scripts` | `All checks passed!` ✅ |
| B3 | `python -m pytest -q` (host `pc_x86`, toàn kho) | `789 passed, 15 warnings in 169.42s` ✅ |
| B4 | `python -m pytest tests/test_benchmark_detect.py -q` | `172 passed in 18.08s`, **0 skipped** ✅ |
| B5 | `docker run … faceid:arm64 python3 -m pytest -q -m "not slow"` | `756 passed, 1 skipped, 32 deselected, 1 warning in 714.68s` ✅ |
| B6 | `docker run … faceid:arm64 python3 -m pytest --collect-only -q tests/test_benchmark_detect.py` | `172 tests collected in 4.75s`, không lỗi import ✅ |

Mốc trên `dev` trước khi sửa: host `689 passed`, container `656 passed, 1 skipped, 32 deselected`.
**Cả hai nơi tăng đúng 100** — không ca nào phụ thuộc `models/`, `data/` hay camera thật (§3.5), và
không ca nào mang `@pytest.mark.slow`. Đúng image `faceid:arm64`, không dựng image mới (R43).

### C. Đếm ca và quét mẫu vi phạm

| # | Lệnh | Kết quả |
|---|---|---|
| C1 | đếm `::test_dong` | **72** — chốt **B1** §6 đạt, 72 ca cũ còn nguyên tên ✅ |
| C2 | đếm `::test_camera_dong` | **100** — đủ mỗi dòng §8 một ca ✅ |
| C3 | `grep -n "except Exception" scripts/benchmark_detect.py` | rỗng ✅ |
| C4 | `grep -nE "raise (ValueError\|TypeError\|Exception)" scripts/benchmark_detect.py` | rỗng ✅ |
| C5 | `grep -nE "CAP_PROP\|VideoCapture" scripts/benchmark_detect.py` | rỗng — mọi truy cập camera đi qua `src.capture` (R22) ✅ |
| C6 | `grep -nE "\bauto\b" scripts/benchmark_detect.py` | **một dòng**, `:694` — chuỗi trợ giúp `--capture-backend` giải thích vì sao `auto` bị cấm. Đọc lại `:689-696`: `choices=["opencv", "mock"]`, `auto` **không** có trong `choices` ✅ |
| C7 | `grep -nE "\b(30\|33\|1280\|720\|640\|480)\b" scripts/benchmark_detect.py` | **một dòng**, `:648` — `"models/yolov8n-face-640.onnx"`, mặc định CLI có từ trước, §9.2 nói không tính ✅ |
| C8 | `grep -nE "^_COT_CSV = \|^_KHOA_META_BAT_BUOC = " -A 2` | `_COT_CSV` ở `:101`, `_KHOA_META_BAT_BUOC` ở `:133`, nguyên tên và nguyên vị trí — chốt **B3** ✅ |
| C9 | quét `assert True\|^\s*pass$` trong tệp test | rỗng — không có test giả (CB-6) ✅ |
| C10 | quét đường dẫn tuyệt đối / secret | **hai dòng dương tính giả**: `tests\test_benchmark_detect.py:1358: "opencv:\n"` và `:1365: "mock:\n"`. Đã đọc lại hai dòng đó trong `_tao_capture_yaml` — là chuỗi YAML dựng cấu hình thu hình; `Select-String` không phân biệt hoa thường nên `[A-Z]:\\` khớp `v:\`. **Không phải** đường dẫn máy cá nhân ✅ |

### D. Mốc "Đúng" của §8.2 — ranh giới bấm giờ

Bộ thu hình giả `sleep` 40 ms, bộ phát hiện giả `sleep` 2 ms, gọi thẳng `do_mot_cau_hinh_camera`:

```
lay_khung_ms: [40.97, 40.53, 40.67, 40.4, 40.93]
latency_ms  : [4.09, 4.3, 4.21, 4.21, 4.0]
```

Nằm đúng nhóm **"Đúng"** của bảng §8.2 (≈ 40–43 và ≈ 2–5), tách xa hai nhóm sai. Đây là bằng chứng
trực tiếp rằng `latency_ms` ở chế độ `camera` **giữ nguyên nghĩa "chỉ suy luận"**, tức cây cầu đặt
số bước 2.5 cạnh số bước 2.6 (§4.1) là có thật.

### E. Mười lăm phép đột biến

`sha256` gốc `F6B1AF7A2243961A51A1689BCB6768324712C46A1176D43445D7B8E67567AA9C`, **khớp đúng ở cả 15
lần khôi phục**; khôi phục bằng bản sao lưu ở `$env:TEMP`, không dùng `git checkout`. Khối dọn cuối:
`172 passed`, `git status` về đúng hai dòng `M` — **không còn dấu vết đột biến nào trong cây làm việc**.

| # | Phép đột biến | Ca §10 đòi đỏ | Ca thật sự đỏ | Tổng |
|---|---|---|---|---|
| E1 | hai vùng ôm trọn vòng lặp | 26 | `dong26`, `dong97` | `2 failed, 170 passed` ✅ |
| E2 | ★★ hoán đổi hai cột | 25, 26 | `dong25`, `dong26`, `dong97`, `dong98` | `4 failed, 168 passed` ✅ |
| E3 | `perf_counter` thứ ba bao ngoài | 27 | `dong27` | `1 failed, 171 passed` ✅ |
| E4 | gọi `mo()` trong vòng đo | 35, 36 | `dong35` (`assert 101 == 1`), `dong36` (`assert ['mo'] == []`) | `2 failed, 170 passed` ✅ |
| E5 | `finally`→`else` ở đường lỗi | 39 | `dong39` (`assert 0 >= 1`) | `1 failed, 171 passed` ✅ |
| E6 | bỏ chốt một cấu hình | 46, 48 | `dong46`–`dong49` | `4 failed, 168 passed` ✅ |
| E7 | bỏ chốt cờ sai chế độ | 06, 10 | `dong06`–`dong12` | `7 failed, 165 passed` ✅ |
| E8 | bỏ `math.isfinite` | 19, 20, 21 | `dong19`, `dong20`, `dong21` | `3 failed, 169 passed` ✅ |
| E9 | ★ `do_phan_giai_that` lấy từ cấu hình | 69 | `dong69` (`assert '1280x720' == '640x480'`), `dong71`, `dong72` | `3 failed, 169 passed` ✅ |
| E10 | bỏ khoá `nguon` khỏi meta | 01, 64 | `dong01` (`KeyError: 'nguon'`), `dong64`, + 33 ca camera | `35 failed, 137 passed` ✅ |
| E11 | dùng `_COT_CSV` cho camera | 62 | `dong62` | `1 failed, 171 passed` ✅ |
| E12 | thêm `nguon` vào `_KHOA_META_BAT_BUOC` | 53 + ≥1 ca cũ | `camera_dong53`, `camera_dong57`, `camera_dong58`, **và 9 ca cũ** `test_dong25`–`test_dong33` | `12 failed, 160 passed` ✅ |
| E13 | bỏ ghi đè `backend` | 78 | `dong78` (`assert 'auto' == 'mock'`) | `1 failed, 171 passed` ✅ |
| E14 | bỏ chốt nghi bộ đệm khung | 97 | `dong97` (`KeyError`) | `1 failed, 171 passed` ✅ |
| E15 | `--anh-dir` về `default` cũ | 06 | `dong06` + 42 ca camera, gồm `dong22`, `dong42`, `dong50` | `43 failed, 129 passed` ✅ |

**15/15 phép đột biến đều bị bắt, và bắt đúng ca mà §10 chỉ định.** Không có phép nào "vẫn xanh" —
tức không có guard nào của §7 đặc tả nằm ngoài tầm với của bộ kiểm thử.

**Ba đọc quan trọng, ghi lại để không phải suy lại về sau:**

1. **E2 là phép quyết định.** Số đo thật của hai cột dưới E2:
   ```
   lay_khung_ms: [4.67, 3.86, 4.2, 4.19, 4.28]
   latency_ms  : [40.86, 40.38, 40.49, 40.84, 43.46]
   ```
   Đảo ngược sạch so với mốc D, trong khi ca 27/28/29/62 **vẫn xanh**. Đúng như §10 dự đoán: cài đặt
   hoán đổi là tự nhất quán về cấu trúc, **chỉ độ lớn phân biệt được** — và dòng 25–26 canh đúng chỗ đó.
2. **E8 cho biết assert thứ hai của ca 19–21 là bắt buộc.** Thông báo của `dong20`:
   `assert 'hữu hạn' in '--khoang-cach-m phải lớn hơn 0, nhận được -inf.'` — nghĩa là `-inf` vẫn bị
   nhánh `<= 0` chặn và `main()` vẫn trả `1`; **chỉ** assert về chữ "hữu hạn" mới bắt được việc bỏ
   `math.isfinite`. Nếu sau này ai đó rút gọn ba ca này về một assert, phép kiểm sẽ mất hiệu lực im lặng.
3. **E10 và E15 đỏ lan rộng (35 và 43 ca) là do thiết kế, không phải ca test quá rộng.** Cả hai phá
   một chốt nằm ở **bước ghi tệp** (`_KHOA_META_BAT_BUOC_CAMERA`) hoặc ở **bước phân giải cờ**, nên
   mọi ca đi qua `main()` chế độ camera đều đổ theo. Ca mà §10 chỉ định (01, 64, 06) đều nằm trong
   tập đỏ. Không cần thu hẹp ca test.

---

## 2. Đối chiếu đặc tả

| Mục đặc tả | Kết luận |
|---|---|
| §2 Danh sách trắng | ✅ đúng hai tệp (A1), không đụng `src/**`, `configs/**`, `docs/**` |
| §4.1 Ranh giới bấm giờ, ba cột | ✅ `scripts/benchmark_detect.py:388-396` — hai cặp `perf_counter` tách rời, `latency_tong_ms` là phép **cộng** (`:396`), không có cặp thứ ba. Mốc D và E1–E3 xác nhận bằng số |
| §4.2 Đúng một cấu hình | ✅ `:828-838` chặn `len(models) != 1 or len(threads) != 1`, thông báo nêu **cả hai** tên cờ và số phần tử nhận được. E6 xác nhận |
| §4.3 Cấm `auto` | ✅ `:692` `choices=["opencv", "mock"]`; `:868-869` ghi đè `cfg_capture["backend"]` **trước** `tao_bo_thu_hinh`. C6 và E13 xác nhận |
| §5.1 Giao diện CLI | ✅ đủ 8 cờ mới/đổi, đúng tên, đúng `choices`, `--anh-dir`/`--seed` về `default=None`, hai hằng số `_ANH_DIR_MAC_DINH`/`_SEED_MAC_DINH` ở `:68-69` |
| §5.2 Một cờ thuộc đúng một chế độ | ✅ `_kiem_co_sai_che_do` `:726-759`, chạy **trước** khi rẽ nhánh (`:1073`); `meta["seed"] = None` (`:1006`), `meta["dataset"]` không có `anh_dir` (`:922`, ca 68). Kiểm `math.isfinite` **tách rời** kiểm `> 0` (`:816-826`) |
| §5.3 Vòng lặp đo, fail-safe | ✅ camera mở đúng một lần ở `:895`, `do_mot_cau_hinh_camera` không mở/đóng (ca 36 quét AST), `finally: bo_thu_hinh.dong()` `:905-906`, đường lỗi trả `1` và **không ghi tệp nào** (ca 38–41). Đã đọc `src/capture/opencv_camera.py:85-96`: `dong()` an toàn cả khi `mo()` chưa từng thành công ⇒ khối `finally` không sinh ngoại lệ thứ hai (R24) |
| §5.4 `meta.dataset` tám khoá | ✅ `mo_ta_nguon_camera` `:453-504`; `do_phan_giai_that` lấy từ `khung_mau.shape` (`:485`), E9 xác nhận đây là chỗ duy nhất |
| §5.5 Bốn khoá meta mới, 24 khoá bắt buộc | ✅ `:159-164`, `:1013-1020`; `_KHOA_META_BAT_BUOC` giữ nguyên 20 khoá. E12 chứng minh bất đối xứng này là **cần thiết**: thêm `nguon` vào danh sách gốc làm 9 ca cũ đỏ, tức đổi hành vi chế độ `dia` |
| §5.6 Bốn khoá cảnh báo | ✅ `:947-975`, cả bốn tình huống có nhánh riêng, câu cảnh báo vào **cả** meta lẫn `notes` (`:977-979`). Xem 🔵-2 về một bất đối xứng còn lại |
| §5.7 Bộ thu hình giả | ✅ `_CameraGia` kế thừa `BoThuHinh` (`tests/…:1252-1290`), đếm `mo`/`dong`/`doc`, `sleep` cấu hình được, ném `LoiCamera` ở khung thứ `k`. Không ca nào dùng `--capture-backend opencv` hay `auto` |
| **§6 Chốt chịu lực — `dia` không đổi** | ✅ **B1** 72 ca (C1) và đúng một dòng `-` là dòng `import` (A4) · **B2** ca 57 · **B3** ca 52–53 + C8 · **B4** ca 58. Hai hàm `do_mot_cau_hinh` (`:224-294`) và `tong_hop` (`:312-344`) không có hunk. Đọc lại `:275-277`: vùng bấm giờ chế độ `dia` vẫn ôm **đúng một** lệnh `detector.detect(anh)` |
| §7 Giao diện hàm | ✅ ba hàm mới khớp **từng ký tự** chữ ký đặc tả (`:347-353`, `:417`, `:453`); `dat_chi_tieu_tong` dùng lại `NGUONG_FPS_TOI_THIEU`, không thêm ngưỡng mới; `run_id` = `bench_detect_camera_<YYYYMMDD_HHMM>` (`:927`); CSV 13 cột đúng thứ tự (`:117-131`, ca 62); docstring tiếng Việt kiểu Google đủ `Args`/`Returns`/`Raises` |
| §8 Bảng nghiệm thu 100 dòng | ✅ 100 ca `test_camera_dong01`–`dong100`, đủ mọi dòng, không dòng nào bị gộp. Ba sai lệch nhỏ so với câu chữ, đã kiểm là **vô hại**: dòng 30–33 dùng `sleep 0` (bốn assert đó không phụ thuộc thời gian); dòng 44 dùng `not kq.exists()` thay cho `rglob("*") == []` (mạnh hơn); dòng 06 có thêm một dòng đối chứng (xem 🔵-3) |
| §11 Ràng buộc kỹ thuật | ✅ không thêm phụ thuộc; `time.perf_counter` (không `time.time`); log **lazy formatting** — quét `logger.\w+\(f"` cho kết quả rỗng; ngoại lệ chỉ dùng `LoiCamera`/`LoiCauHinh`/`LoiMoHinh` (C3, C4); `newline=""` và `encoding="utf-8"` giữ nguyên; mọi ca ghi tệp đều `monkeypatch` `_THU_MUC_KET_QUA_MAC_DINH` |
| §12 Ngoài phạm vi | ✅ không sửa `src/capture/**`, không đa luồng, không frame skipping, không đo RAM/`get_throttled`, không đụng `ghi_ket_qua` theo hướng từ chối ghi đè, không viết notebook/Chương 4 |

### Hai điểm sống còn — soi riêng

**Trung thực số liệu (R5, R6).** Không tìm thấy giá trị mặc định giả nào trông như kết quả đo.
`mo_ta_nguon_camera` trả `n_frame_do = None` và `n_frame_lam_nong = None` rồi để nơi gọi điền —
đã kiểm bằng grep: hàm có **đúng một** đường gọi (`:922`), và hai dòng điền lại (`:923-924`) đứng
ngay sau, trước mọi lối ghi tệp; `ghi_ket_qua` chỉ được gọi một lần ở `:1025`. Không tồn tại đường
nào ghi tệp với hai khoá còn `None`. `n_frame_do` là `len(ban_ghi)` — **số dòng CSV thật**, không
phải cờ `--n-frames` (ca 74). Backend `mock` luôn kèm `canh_bao_nguon_gia_lap` (ca 76–77), nên một
tệp kiểm chức năng không thể bị đọc nhầm thành số báo cáo. Tên tệp `bench_detect_camera_*` +
khoá `nguon` + 13 cột là ba hàng rào độc lập chống trộn với số bước 2.6 — hàng rào thứ ba làm phép
trộn nhầm hỏng to tiếng thay vì sai im lặng, đúng ý §7.

**An toàn phần cứng (R24).** Camera là thiết bị duy nhất mã việc này chạm tới. Mở đúng một lần,
đóng trong `finally` ở **mọi** đường ra kể cả khi `mo()` ném (E5 chứng minh chốt này có hiệu lực),
và `CameraOpenCV.dong()` chịu được lời gọi trên đối tượng chưa mở. Đường lỗi **không ghi tệp**, nên
không có phép đo khuyết nào lọt vào `results/`.

---

## 3. Lỗi phải sửa

**Không có 🔴 CHẶN-A, không có 🔴 CHẶN-B, không có 🟡 CẦN SỬA.**

Bảy giả thuyết nêu ở lượt kiểm định đã được phán hết; ba trong số đó thành 🔵, bốn còn lại là
**không phải lỗi** và được ghi lại dưới đây để vòng sau không phải điều tra lại:

| Giả thuyết | Phán |
|---|---|
| **G1** — dòng `argv_hien_thi = argv if argv is not None else sys.argv[1:]` bị xoá ở `@@ -621` và xuất hiện lại ở `@@ +1073` (nay là `:1079`) | **Không vi phạm §6.** Dòng này chỉ dịch lên **trước** chỗ rẽ nhánh vì nhánh camera cũng cần nó để dựng `meta["command"]`. Biểu thức giữ nguyên từng ký tự, vẫn đứng sau `_kiem_co_sai_che_do` và trước mọi lối dùng, nên `meta["command"]` của chế độ `dia` không đổi một ký tự. Bốn bất biến B1–B4 không liên quan tới dòng này. Ghi nhận: người cài đặt **không khai** dòng này trong báo cáo mục 7 — lần sau khai đủ để người review không phải tự dựng lại lập luận |
| **G3** — `mo_ta_nguon_camera` trả hai khoá `None` | **Không phải lỗi**, xem mục "Trung thực số liệu" ở trên: đúng một đường gọi, điền lại ngay, không đường ghi tệp nào bỏ qua bước điền |
| **G6** — ca 06 và ca 19–21 | **Đã phân định bằng máy**: assert thứ hai của ca 19–21 là **bắt buộc** (E8); dòng đối chứng của ca 06 là **thừa** nhưng vô hại (E15 vẫn bị `dong22`, `dong42`, `dong50` bắt) ⇒ 🔵-3, không phải lỗi |
| **G7** — bảng in ra né chữ số `30`/`33` | **Không phải lỗi.** Câu hiện tại — *"latency_lay_khung_ms có sàn bằng nghịch đảo tốc độ khung của webcam"* (`:792-793`) — còn nguyên nghĩa và **tổng quát hơn** bản có số: sàn 33 ms chỉ đúng cho webcam 30 khung/s, mà tốc độ khung thật chưa đo (§3.4: `opencv.fps` là giá trị khai báo, không phải giá trị được áp). Ở đây ràng buộc của lệnh kiểm và cách viết đúng trùng nhau, nên không có chuyện "uốn mã theo lệnh kiểm" |

---

## 4. 🔵 Góp ý — không chặn, người dùng quyết định

### 🔵-1 — Một khung đọc thêm ngoài vòng đo có thể vứt bỏ trọn lượt đo đã hoàn tất

**Vị trí**: `scripts/benchmark_detect.py:894-906` (dòng quyết định: `:900`)

```python
        ban_ghi = do_mot_cau_hinh_camera(...)
        # Một khung mẫu để đọc độ phân giải THẬT — sau cả hai vùng bấm giờ (P2-07 §5.4).
        khung_mau = bo_thu_hinh.doc_frame()
    except (LoiCamera, LoiMoHinh, LoiCauHinh) as e:
        ...
        return 1
```

**Vì sao**: khung phụ này nằm **trong** cùng khối `try` và chạy **sau** khi vòng đo đã xong. Nếu
webcam hỏng đúng ở lời gọi cuối cùng này thì 300 bản ghi đã đo xong bị vứt, `main()` trả `1`, không
tệp nào được ghi. Trên Pi 5 lượt đo mất ~10 s nên cái giá là chạy lại một lượt — **không** phải rủi
ro số liệu sai, và fail-safe vẫn đúng (camera vẫn đóng, không ghi tệp khuyết). Đó là lý do đây là
🔵 chứ không phải CB-3.

Kèm theo: đường này **chưa ca nào chạm tới**. Ca 31 đếm `so_lan_doc == 6` nhưng gọi **thẳng**
`do_mot_cau_hinh_camera`, không qua `main()`; ca 38–41 đặt lỗi ở khung thứ 12, tức giữa vòng đo.
Đặc tả §8 không có dòng nào cho tình huống này nên **không tính là CS-4**.

**Nếu người dùng muốn xử lý** (mã việc riêng, không sửa ở đây): bọc riêng khung mẫu trong `try` của
chính nó và khi hỏng thì ghi `do_phan_giai_that: null` + `khop_do_phan_giai: null` kèm một khoá cảnh
báo, thay vì huỷ cả lượt. Đổi này cần đặc tả bổ sung vì nó thêm một trạng thái `null` mới vào
`meta.dataset` mà §5.4 đang đòi tám khoá có giá trị.

### 🔵-2 — `canh_bao_hieu_nang` mang hai nghĩa khác nhau ở hai chế độ

**Vị trí**: `scripts/benchmark_detect.py:949` (camera) so với `:1257` (dia)

```python
    if moi_truong != _MOI_TRUONG_PHAN_CUNG_DICH:      # :949  — chế độ camera
        canh_bao["canh_bao_hieu_nang"] = cau
...
    if trong_container:                                # :1257 — chế độ dia, KHÔNG đổi
        meta["canh_bao_hieu_nang"] = (...)
```

**Vì sao**: cùng một khoá meta, hai điều kiện khác nhau. Một lượt `dia` trên `pc_x86` **không** có
khoá này (chỉ có câu cảnh báo trong `notes`), còn lượt `camera` trên `pc_x86` **có**. Notebook
`04_so_sanh_moi_truong.ipynb` nếu nhóm theo sự **có mặt** của khoá sẽ đọc sai một trong hai nhóm.
Chiều nguy hiểm thì không xảy ra: chế độ `camera` **chặt hơn** chế độ `dia`, nên không có lượt đo
nào bị **thiếu** cảnh báo.

**Đây là lỗi của đặc tả, không phải của người cài đặt.** §5.6 ghi *"`moi_truong != "pi5"` →
`canh_bao_hieu_nang` — **hành vi cũ, giữ nguyên**"*, trong khi hành vi cũ của khoá meta là
`dang_trong_container()`. Người cài đặt làm đúng bảng §5.6 và không đụng nhánh `dia` — đúng thứ §6
đòi. Sửa cho khớp nhau **bắt buộc** phải đổi nhánh `dia`, tức việc §6 cấm ở mã việc này.

**Đề xuất**: nếu người dùng đồng ý, mở một mã việc nhỏ (`P2-08` hoặc gộp vào `P0-05`) thống nhất
khoá này về `moi_truong != "pi5"` cho cả hai chế độ, kèm quy ước đọc tệp cũ như §5.5 đã làm với
khoá `nguon`. Chi phí: một hàm nhỏ + 2–3 ca test; lợi ích: notebook Cổng D nhóm được bằng một tiêu chí.

### 🔵-3 — Ba điểm nhỏ trong bộ kiểm thử, không đáng một vòng bàn giao

| Điểm | Vị trí | Nhận xét |
|---|---|---|
| Dòng đối chứng thừa ở ca 06 | `tests/test_benchmark_detect.py:1585` | E15 cho thấy `dong22`, `dong42`, `dong50` đã bắt được chế độ hỏng ấy. Giữ lại thì khi hỏng, thông báo lỗi của một ca tên *"camera_tu_choi_anh_dir"* lại là `assert 1 == 0` ở dòng đối chứng — dễ đọc nhầm hướng |
| Ngưỡng tuyệt đối 1 ms của ca 97 | `tests/test_benchmark_detect.py:2332-2337` | Ca đã chạy xanh trong container lượt này (B5). Rủi ro chập chờn về sau đã được người cài đặt tự giảm bằng khung `48×64` thay vì `480×640`, nên `doc_frame` chỉ còn vài chục micro-giây — nhận xét này ghi để lần sau ai sửa kích thước khung thì biết vì sao nó nhỏ |
| Ca 100 gần như hằng đúng | `tests/test_benchmark_detect.py:2354-2357` | `_setup_camera_ok` `monkeypatch` chính `xac_dinh_moi_truong` thành `"pc_x86"`, nên ca chỉ chứng minh `main()` chép giá trị đó vào meta. Đúng câu chữ dòng 100 §8, nhưng nếu bỏ `monkeypatch` riêng cho ca này thì nó canh được cả hàm suy ra môi trường thật |

---

## 5. Việc tiếp theo

1. **Được commit.** Gợi ý message (R29):
   `feat(benchmark): thêm cờ --nguon camera cho benchmark_detect — bước 2.5, P2-07`
   Nếu cây làm việc đang ở `dev` (ảnh chụp git đầu phiên cho thấy vậy) thì cân nhắc tạo
   `feat/p2-07-benchmark-detect-camera` rồi gộp, cho khớp §2 đặc tả và R30 — chuỗi truy vết
   *đặc tả → nhánh → biên bản → commit → nhật ký* mới liền mạch.
2. **§12a**: commit **trước** khi đo, để `.meta.json` ghi `git_dirty: false`.
3. **§12b — lượt chạy thật, người dùng chạy** (không phải người review, không phải `coder`):
   lệnh 1 và 2 trên máy phát triển; lệnh 3, 4, 5 trên Pi 5 với webcam thật, cùng vị trí camera,
   nghỉ ~2 phút giữa các lượt. Ghi `vcgencmd measure_temp` và `vcgencmd get_throttled` trước và
   sau phiên. Commit **cả 8 tệp** `results/`.
4. **Sau đó mới đóng Cổng C Phase 2**: số kết luận bước 2.5 lấy từ lượt 3 (`fps_tb` cho chỉ tiêu §1,
   `fps_tong_tb` cho con số đầu-cuối). Trước khi có 8 tệp đó, Bảng 4.7 §4.6 vẫn phải ghi
   `[CHƯA ĐO]` cho dòng tương ứng.
5. **Ba mục 🔵 ở trên**: người dùng quyết định có mở mã việc riêng hay không. 🔵-2 là mục duy nhất
   có hệ quả tới báo cáo (notebook `04_so_sanh_moi_truong`), nên nếu chỉ chọn một thì chọn nó.
