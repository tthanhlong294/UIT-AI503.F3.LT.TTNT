# Review P1-02-collect-faces — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-02-collect-faces.md` |
| **Quy ước tham chiếu** | `docs/quy-uoc-du-lieu.md` |
| **Nhánh** | `feat/p1-02-collect-faces` |
| **Ngày** | 2026-08-13 |
| **Phán quyết** | 🔴 **TRẢ LẠI** |

Tổng hợp: **2 lỗi 🔴 CHẶN-A · 3 lỗi 🔴 CHẶN-B · 3 lỗi 🟡 CẦN SỬA · 5 🔵 góp ý**.

Điểm tích cực cần ghi nhận trước: bốn hành vi dễ làm hỏng dữ liệu âm thầm (đánh số tiếp tục, không
ghi đè, manifest ghi nối, không gọi hàm hiển thị) đều đã được **cài đặt đúng** — đã kiểm chứng độc
lập, không tin theo tên hàm test. Các lỗi bên dưới nằm ở chỗ khác: nguồn gốc khung hình ghi vào
manifest, hành vi khi `--no-preview`, mất manifest khi lỗi giữa chừng, và hai ca test rỗng ruột.

---

## 1. Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | đúng **3 file**, đều trong danh sách trắng ✅ |
| `git diff dev -- configs/ src/` | **rỗng** — `configs/data.yaml`, `configs/capture.yaml`, `src/` không bị chạm ✅ |
| `black --check --line-length 100 src tests scripts` | `17 files would be left unchanged` ✅ |
| `ruff check src tests scripts` | `All checks passed!` ✅ |
| `pytest -q` (host) | **77 passed** (52 ca cũ + 25 ca mới) ✅ |
| `pytest -q` (container ARM64) | **77 passed in 47.82s**, `platform.machine() == aarch64` ✅ |
| `git status` sau khi chạy `pytest` | vẫn đúng 3 file, `data/` không phát sinh gì ✅ |

**Ghi chú về lệnh container**: lệnh nguyên văn ở §6 đặc tả
(`docker run --rm --platform linux/arm64 -v "$(pwd)":/app -w /app faceid:arm64 pytest -q`)
**không chạy được trên máy này**, vì hai lý do độc lập với mã nguồn:
Git Bash đổi `/app` thành `C:/Program Files/Git/app`, và cờ `--platform` khiến Docker Desktop bỏ qua
ảnh cục bộ rồi đi kéo từ registry. Lệnh đã dùng thay thế (cùng tác dụng, đã xác nhận `aarch64` bên trong):

```bash
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 \
  sh -c "python -c 'import platform;print(platform.machine())' && pytest -q"
```

## 2. Quét mẫu vi phạm

| Mẫu | Kết quả |
|---|---|
| Thư viện ngoài `cv2`/`numpy`/chuẩn (`PIL,imageio,skimage,scipy,matplotlib,torch,pandas`) | không có ✅ |
| `subprocess` / `shutil.which` trong test | không có ✅ |
| Log dùng f-string | không có ✅ |
| Đường dẫn tuyệt đối máy cá nhân, secret | không có ✅ |
| Số magic là tham số thực nghiệm | có — xem CHẶN-A-1 ❌ |
| Nuốt lỗi im lặng | 1 chỗ, `scripts/collect_faces.py:286-287` — xem góp ý |
| Test không assert | 1 ca — xem CẦN SỬA-2 ❌ |

## 3. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §2 Danh sách trắng | ✅ đúng 3 file, không chạm `configs/`, `src/`, `docs/`, `data/` |
| §3 Interface | ✅ 7 hàm public khớp **từng ký tự** về tên, thứ tự tham số, kiểu trả về |
| §4 Tham số → config | ❌ đọc đúng key nhưng **kèm giá trị mặc định hardcode** (CHẶN-A-1) |
| §4 Tham số dòng lệnh | ✅ đủ 7 cờ, đúng tên, đúng mặc định |
| §5 Ca biên | ⚠️ **25/25 dòng có hàm test**, nhưng **23/25 có kiểm chứng thực chất** (dòng 12 rỗng ruột, dòng 25 không assert, dòng 22 thiếu 2/3 mã sai) |
| §6 Nghiệm thu | 9/11 (hai mục "mỗi ca có assert thật" và "52 ca cũ + ca mới" — mục sau đạt, mục trước không) |
| §7 Quy tắc | ❌ G1 (CHẶN-A-1), G2 (hướng dẫn tư thế dùng `logger` và bị tắt theo `hien_thi`, CHẶN-B-1); ✅ G4, G5, G6 (context manager đóng camera), R15 |
| §8 Ngoài phạm vi | ✅ không làm gì ngoài phạm vi |
| Quy ước dữ liệu §3 (tên file) | ✅ `u01_frontal_bright_007.png` đúng mẫu |
| Quy ước dữ liệu §5 (manifest) | ⚠️ đủ 10 cột nhưng cột `camera` và `note` ghi giá trị **không phản ánh sự thật** (CHẶN-A-2, CẦN SỬA-1) |
| Quy ước dữ liệu §6 (PNG) | ✅ lấy từ `image_format`, không hardcode đuôi trong tên hàm |

### Kết quả bốn điểm soi kỹ (kiểm chứng độc lập, không dựa vào test của Gemini)

| Điểm | Phép kiểm đã chạy | Kết quả |
|---|---|---|
| Dòng 11 — đánh số tiếp tục | có sẵn `..._007.png`, `min_per_combo=3` | sinh `008`, `009` — **không quay về 001** ✅ |
| Dòng 12 — không ghi đè | ghi `b"OLD_DATA_KHONG_DUOC_DOI"` vào `..._001.png`, `min_per_combo=3` → chụp thêm 2 ảnh | nội dung cũ **không đổi**, ảnh mới là `002`, `003` ✅ |
| Dòng 17 — manifest ghi nối | chạy `thu_thap` **hai lần** liên tiếp cùng thư mục | 5 dòng / 4 ảnh, **đúng 1 dòng tiêu đề** ✅ |
| Dòng 25 — `hien_thi=False` | vá `imshow`, `waitKey`, `namedWindow`, `destroyAllWindows`, `startWindowThread` thành hàm ném lỗi | **không ném** ✅ |

Bốn hành vi này đúng. Nhưng phép kiểm dòng 12 cũng cho thấy **ca test tương ứng của Gemini không hề
chạm tới đường code đang cần bảo vệ** — xem CHẶN-B-3.

---

## 4. Lỗi phải sửa

### 🔴 CHẶN-A-1 — Hardcode giá trị mặc định cho mọi tham số config (vi phạm G1 / R16)

**Vị trí**: `scripts/collect_faces.py:210-215`, `:322`, `:327`, `:338`, `:340`, `:347-348`

```python
poses = cfg_data.get("poses", ["frontal", "left", "right", "up", "down"])
min_per_combo = cfg_data.get("min_per_combo", 10)
image_format = cfg_data.get("image_format", "png")
manifest_name = cfg_data.get("manifest_name", "manifest.csv")
capture_interval_s = cfg_data.get("capture_interval_s", 0.5)
pose_switch_delay_s = cfg_data.get("pose_switch_delay_s", 3.0)
```

```python
id_pattern = cfg_data.get("id_pattern", "^[ux][0-9]{2}$")      # dòng 322
lights = cfg_data.get("lights", ["bright", "dim"])              # dòng 327
out_base = cfg_data.get("out_dir_gallery", "data/raw")          # dòng 338
```

**Vì sao**: §4 đặc tả ghi rõ *"Không hardcode giá trị nào"*. Mỗi giá trị mặc định ở đây là một **bản
sao thứ hai** của `configs/data.yaml` nằm trong code. Hậu quả cụ thể: đổi tên hoặc gõ sai một key
trong YAML (`min_per_combo` → `min_moi_to_hop`) thì script **không báo lỗi**, nó lặng lẽ thu 10
ảnh/tổ hợp theo con số chôn trong code. Người thu thập tưởng đang chạy theo cấu hình mới, kết quả là
một bộ dữ liệu không tái lập được và không ai biết. Riêng `capture_interval_s=0.5` và
`pose_switch_delay_s=3.0` là **tham số thực nghiệm** — chúng quyết định độ đa dạng của 100 ảnh/người.

**Sửa**: dự án **đã có sẵn** hàm đúng cho việc này — `lay_gia_tri` trong `src/common/config.py`, nó
ném `LoiCauHinh` khi thiếu key nếu không truyền mặc định. Thay toàn bộ `.get(key, <mặc định>)` bằng:

```python
from src.common.config import lay_gia_tri, nap_cau_hinh

poses = lay_gia_tri(cfg_data, "poses")
min_per_combo = lay_gia_tri(cfg_data, "min_per_combo")
image_format = lay_gia_tri(cfg_data, "image_format")
manifest_name = lay_gia_tri(cfg_data, "manifest_name")
capture_interval_s = lay_gia_tri(cfg_data, "capture_interval_s")
pose_switch_delay_s = lay_gia_tri(cfg_data, "pose_switch_delay_s")
```

Áp dụng cho cả `id_pattern`, `lights`, `out_dir_gallery`, `out_dir_indomain` trong `main()`. Trong
`main()`, bọc phần đọc key vào khối `try/except LoiCauHinh` đã có sẵn ở dòng 315-320 để thiếu key thì
`main()` trả `1` kèm thông báo, thay vì chạy tiếp bằng giá trị giả.
Fixture `cfg_data` trong test đã có đủ mọi key nên **không ca test nào phải sửa** vì thay đổi này.

---

### 🔴 CHẶN-A-2 — Manifest ghi sai nguồn khung hình: không phân biệt được ảnh thật và ảnh giả lập (vi phạm R5 / CA-7)

**Vị trí**: `scripts/collect_faces.py:256`

```python
camera_info = str(cfg_capture.get("backend", "unknown"))
```

**Vì sao**: `configs/capture.yaml` đặt `backend: auto`. Đây là **bộ chọn**, không phải thiết bị đã
dùng. `src/capture/factory.py` khi ở chế độ `auto` mà không mở được camera thật sẽ **âm thầm quay về
`CameraGiaLap`** — nguồn ảnh tổng hợp theo seed. Chạy thật trên máy dev hoặc trong container (đúng
tình huống Phase 1 hiện tại: chưa có camera của hệ thống), câu lệnh
`python scripts/collect_faces.py --id u01 --light bright` sẽ ghi **100 ảnh tổng hợp vào
`data/raw/u01/`**, và manifest ghi `camera=auto` cho cả 100 dòng. Đã kiểm chứng: với
`backend="auto"` và `opencv.device_index=99`, cột `camera` trong manifest ra đúng chuỗi `'auto'`.

Không có cách nào phân biệt các ảnh đó với ảnh chụp thật về sau. Toàn bộ Phase 1.7 (đo đặc trưng
miền), Phase 3 (`FAR_indomain`) và mọi con số trong báo cáo đều dựa trên thư mục này. Đây đúng là
loại lỗi mà R5 và checklist "không có số liệu bịa" nhắm tới — dữ liệu giả trông y hệt dữ liệu thật.
Cảnh báo trong `factory.py` chỉ là một dòng log trôi qua giữa hàng trăm dòng khác.

**Sửa**: ghi **backend đã được phân giải thật sự**, lấy từ chính đối tượng camera đang mở. Sửa vòng
lặp trong `thu_thap` (dòng 220 và 256):

```python
with tao_bo_thu_hinh(cfg_capture) as cam:
    ten_backend = type(cam).__name__  # "CameraOpenCV" hoặc "CameraGiaLap"
    if ten_backend == "CameraGiaLap":
        logger.warning(
            "Đang thu bằng camera GIẢ LẬP — ảnh sinh ra KHÔNG phải dữ liệu thật, "
            "chỉ dùng để kiểm thử. Thư mục: %s",
            thu_muc_ra,
        )
    ...
    camera_info = ten_backend   # thay dòng 256
```

Bổ sung một ca test vào `tests/test_collect_faces.py`: gọi `thu_thap` với
`cfg_capture = {"backend": "mock", ...}` rồi assert
`ban_ghi[0]["camera"] == "CameraGiaLap"` — để về sau không ai lặng lẽ đổi lại.

---

### 🔴 CHẶN-B-1 — `--no-preview` tắt luôn hướng dẫn tư thế và nhịp chụp (vi phạm §1, §3, G2 / CB-1)

**Vị trí**: `scripts/collect_faces.py:229-237` và `:272-279`

```python
            if hien_thi:
                logger.info(
                    "Tư thế %s (%s): cần chụp thêm %d ảnh. Chờ %.1fs...", ...
                )
                time.sleep(pose_switch_delay_s)
```

```python
                if hien_thi:
                    cv2.imshow("Collect Faces Preview", frame)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord("q"):
                        ...
                    if capture_interval_s > 0:
                        time.sleep(capture_interval_s)
```

**Vì sao**: §3 đặc tả nói rõ phạm vi của cờ này — *"`hien_thi=False` phải bỏ qua hoàn toàn mọi lời
gọi **hiển thị cửa sổ**"*. Gemini đã gói thêm hai thứ không phải hiển thị cửa sổ vào cùng một `if`:
**hướng dẫn tư thế** và **toàn bộ nhịp chụp**. Đã kiểm chứng: `thu_thap(hien_thi=False)` với
`pose_switch_delay_s=1.0`, `capture_interval_s=0.5`, 2 tư thế × 2 ảnh chạy hết **0.12 giây** (đúng
theo cấu hình phải là 4.0 giây) và phát ra **0 dòng hướng dẫn tư thế**.

Hậu quả trên Pi 5, nơi việc thu thập thường chạy qua SSH nên `--no-preview` là chế độ mặc định trên
thực tế: người ngồi trước camera **không được báo phải quay mặt sang hướng nào**, mà 10 ảnh của một
tổ hợp bị chụp xong trong vài mili-giây. Kết quả là 10 khung hình gần như trùng khít nhau, được gán
nhãn `left`, `right`, `up`, `down` trong khi người đó vẫn ngồi yên nhìn thẳng. Bộ dữ liệu **sai nhãn
và không đa dạng** — đúng thứ mà quy ước §2 cảnh báo (*"Thu đều tay quan trọng hơn thu nhiều"*), và
không ai phát hiện ra cho tới khi Phase 3 cho số liệu vô nghĩa.

Kèm theo là vi phạm G2: §7 ghi *"`print` **chỉ** cho hướng dẫn tư thế và bảng tóm tắt cuối"* — tức
hướng dẫn tư thế phải là `print`, không phải `logger.info` (log có thể bị đặt mức `WARNING` là người
chụp không thấy gì).

**Sửa**: tách ba mối quan tâm ra, chỉ `imshow`/`waitKey`/`destroyAllWindows` mới phụ thuộc `hien_thi`.

```python
        for pose in poses:
            ...
            # Hướng dẫn tư thế: LUÔN hiện, dùng print theo G2
            print(f"\n>>> Tư thế: {pose} ({light}) — cần chụp thêm {needed} ảnh.")
            print(f"    Giữ nguyên tư thế, bắt đầu sau {pose_switch_delay_s:.1f}s...")
            time.sleep(pose_switch_delay_s)

            for _ in range(needed):
                ...
                if hien_thi:
                    cv2.imshow("Collect Faces Preview", frame)
                    if (cv2.waitKey(1) & 0xFF) == ord("q"):
                        logger.info("Người dùng bấm 'q' để ngắt thu thập.")
                        break
                # Nhịp chụp: LUÔN áp dụng, không phụ thuộc hien_thi
                if capture_interval_s > 0:
                    time.sleep(capture_interval_s)
```

Fixture `cfg_data` trong test đã đặt `capture_interval_s = 0.0` và `pose_switch_delay_s = 0.0` nên
test vẫn chạy nhanh và **không ca nào phải sửa**. Bổ sung một ca mới:

```python
def test_26_hien_thi_false_van_ap_dung_nhip_chup(tmp_path, cfg_data, cfg_capture):
    """hien_thi=False vẫn phải tôn trọng nhịp chụp trong cấu hình."""
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 2
    cfg_data["capture_interval_s"] = 0.2
    cfg_data["pose_switch_delay_s"] = 0.2
    t0 = time.monotonic()
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert time.monotonic() - t0 >= 0.5
```

---

### 🔴 CHẶN-B-2 — Lỗi camera hoặc `Ctrl+C` giữa chừng làm mất toàn bộ manifest của buổi chụp (vi phạm R24 / CB-2)

**Vị trí**: `scripts/collect_faces.py:289-293` (ghi manifest **sau khi** vòng lặp kết thúc trọn vẹn)

```python
    if ban_ghi_list:
        manifest_path = thu_muc_ra / manifest_name
        ghi_manifest(manifest_path, ban_ghi_list)

    return ban_ghi_list
```

**Vì sao**: ảnh được ghi ra đĩa ngay trong vòng lặp (dòng 250), nhưng bản ghi manifest chỉ được ghi
**một lần duy nhất, sau khi mọi tư thế đã chụp xong**. Bất kỳ lối thoát bất thường nào cũng làm mất
sạch phần metadata của các ảnh đã nằm trên đĩa. Đã kiểm chứng: cho `doc_frame()` ném `LoiCamera` ở
lần đọc thứ ba → **2 ảnh trên đĩa, `manifest.csv` không tồn tại**.

Đây không phải tình huống hiếm. Một buổi chụp 100 ảnh kéo dài vài phút; `Ctrl+C` để dừng giữa chừng
là thao tác hoàn toàn bình thường (chính §7 G6 của đặc tả đã lường trước `Ctrl+C`), và `Ctrl+C` cũng
đi qua đúng đường code này. Hậu quả: thư mục có ảnh nhưng không có manifest, phá vỡ bất biến ở dòng
18 bảng §5 và làm hỏng bước 1.11 (quy ước §7 nói chia tập gallery **dựa vào cột `timestamp` của
manifest**). Ảnh vẫn được `dem_da_co` đếm ở lần chạy sau nên **không ai nhận ra thiếu metadata**.

**Sửa**: ghi manifest ngay sau mỗi tư thế hoàn tất, và bọc `try/finally` để phần đã chụp luôn được
ghi lại. `ghi_manifest` vốn đã ghi nối nên gọi nhiều lần là an toàn:

```python
    ban_ghi_list: list[dict] = []
    manifest_path = thu_muc_ra / manifest_name
    chua_ghi: list[dict] = []
    try:
        with tao_bo_thu_hinh(cfg_capture) as cam:
            for pose in poses:
                ...
                for _ in range(needed):
                    ...
                    chua_ghi.append(rec)
                    ban_ghi_list.append(rec)
                # Chốt sổ sau mỗi tư thế
                ghi_manifest(manifest_path, chua_ghi)
                chua_ghi = []
    finally:
        # Mất camera hoặc Ctrl+C: phần đã chụp vẫn phải có metadata
        ghi_manifest(manifest_path, chua_ghi)

    return ban_ghi_list
```

Bổ sung ca test: giả lập `doc_frame` ném `LoiCamera` giữa chừng, assert số dòng dữ liệu trong
`manifest.csv` **bằng** số file `*.png` trên đĩa.

---

### 🔴 CHẶN-B-3 — Ca test dòng 12 không chạm tới đường code cần bảo vệ (test giả / CB-6)

**Vị trí**: `tests/test_collect_faces.py:135-142`

```python
def test_12_khong_ghi_de_anh_da_co(tmp_path, cfg_data, cfg_capture):
    """Tuyệt đối không ghi đè dữ liệu ảnh đã có."""
    old_file = tmp_path / "u01_frontal_bright_001.png"
    old_file.write_bytes(b"OLD_DATA")
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 1          # ← đã có 1 ảnh, nên cần chụp thêm = 0
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert old_file.read_bytes() == b"OLD_DATA"
```

**Vì sao**: đặt `min_per_combo = 1` trong khi thư mục **đã có đúng 1 ảnh** khiến
`needed = 1 - 1 = 0`, nhánh `if needed <= 0: continue` ở dòng 224 nhảy qua, và `thu_thap` **không
chụp ảnh nào**. Đã kiểm chứng bằng chính kịch bản của test: `thu_thap` trả về **0 bản ghi**. Nghĩa là
câu `assert` chỉ đang xác nhận rằng "một hàm không làm gì thì không sửa file" — luôn đúng, kể cả nếu
mai này ai đó thay `cv2.imwrite` bằng phiên bản ghi đè vô điều kiện. Dòng 12 là một trong hai dòng
quan trọng nhất của bảng §5 (mất ảnh cũ là mất dữ liệu không lấy lại được), mà nó lại đang được canh
gác bằng một ca test rỗng ruột.

Lưu ý: **hành vi của code là đúng** — đã kiểm chứng riêng, đặt `min_per_combo = 3` thì ảnh cũ giữ
nguyên byte và ảnh mới đánh số `002`, `003`. Chỉ ca test cần sửa, không cần sửa `collect_faces.py`.

**Sửa**: nâng `min_per_combo` để thật sự có ảnh được chụp, và assert thêm rằng ảnh mới đã ra đời:

```python
    cfg_data["min_per_combo"] = 3          # đã có 1 → phải chụp thêm 2
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert old_file.read_bytes() == b"OLD_DATA"
    assert (tmp_path / "u01_frontal_bright_002.png").exists()
    assert (tmp_path / "u01_frontal_bright_003.png").exists()
```

---

### 🟡 CẦN SỬA-1 — Cột `note` điền giá trị bịa (vi phạm quy ước dữ liệu §5)

**Vị trí**: `scripts/collect_faces.py:268`

```python
                    "note": f"{light} light",
```

**Vì sao**: quy ước §5 định nghĩa cột `note` là *"mô tả **thật** của buổi chụp — 'đèn trần + rèm mở',
'chỉ đèn bàn'"*, và nói rõ *"chính cột này giúp giải thích các bất thường phát hiện ở bước kiểm chất
lượng"*. Chuỗi `"bright light"` được suy ra máy móc từ cột `light` ngay bên cạnh: nó không mang thêm
một chút thông tin nào, nhưng lại **trông như một ghi chú đã được ghi**. Ở bước 1.10, không còn cách
nào phân biệt "buổi chụp này chưa ai ghi chú" với "buổi chụp này được ghi chú là bright light".

**Sửa**: để trống, đúng như các ca test đang mong đợi (`"note": ""` ở `tests/test_collect_faces.py:187`):

```python
                    "note": "",
```

**Nguyên nhân gốc một phần ở đặc tả**: §4 không định nghĩa cờ `--note`, nên hiện không có đường nào
để người chụp nhập mô tả thật. Gemini **không được tự thêm cờ này** (ngoài §3/§4). Đã ghi vào mục góp
ý để người dùng quyết định mở một mã việc nhỏ bổ sung `--note` cho quy ước §5 dùng được đúng ý.

---

### 🟡 CẦN SỬA-2 — Ca test dòng 25 không có câu `assert` nào (vi phạm §6)

**Vị trí**: `tests/test_collect_faces.py:311-320`

```python
def test_25_hien_thi_false_khong_goi_imshow(tmp_path, cfg_data, cfg_capture, monkeypatch):
    """hien_thi=False không gọi bất kỳ hàm cv2.imshow nào."""
    ...
    monkeypatch.setattr(cv2, "imshow", throw_err)
    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 1
    thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
```

**Vì sao**: quét bằng AST toàn bộ file test, đây là hàm test duy nhất **không có `assert` và không có
`pytest.raises`**. §6 đặc tả liệt kê đây là mục nghiệm thu riêng. Rủi ro cụ thể: nếu `thu_thap` vì lý
do nào đó trả về sớm mà không chụp gì (đúng loại lỗi vừa gặp ở CHẶN-B-3), ca test này **vẫn xanh** vì
không có gì để gọi `imshow` cả. Nó chỉ chứng minh được điều mình tuyên bố khi thật sự có ảnh được chụp.

**Sửa**: thêm một dòng khẳng định vòng lặp đã chạy thật:

```python
    ban_ghi = thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert len(ban_ghi) == 1
    assert (tmp_path / "u01_frontal_bright_001.png").exists()
```

---

### 🟡 CẦN SỬA-3 — Ca test dòng 22 chỉ kiểm 1 trong 3 mã sai đặc tả liệt kê (CS-4)

**Vị trí**: `tests/test_collect_faces.py:290-293`

```python
def test_22_main_id_sai_mau():
    with patch("sys.argv", ["collect_faces.py", "--id", "abc", "--light", "bright"]):
        assert main() == 1
```

**Vì sao**: dòng 22 bảng §5 ghi ba mã: `"abc"`, `"u1"`, `"y01"`. Ba mã này không thừa, mỗi mã bắt một
lỗi khác nhau của biểu thức chính quy: `"abc"` bắt lỗi thiếu chữ số, `"u1"` bắt lỗi thiếu neo `{2}`
(mã một chữ số), `"y01"` bắt lỗi sai lớp ký tự tiền tố. Chỉ kiểm `"abc"` thì một mẫu lỏng như
`^[a-z]+` vẫn qua được test — trong khi `x`/`u` là ranh giới sống còn giữa gallery và impostor
(quy ước §1: *"Tiền tố `x` không bao giờ được đưa vào gallery"*).

**Sửa**: chuyển thành test tham số hoá:

```python
@pytest.mark.parametrize("ma_sai", ["abc", "u1", "y01"])
def test_22_main_id_sai_mau(ma_sai):
    """main() trả về 1 với mọi mã --id không hợp lệ."""
    with patch("sys.argv", ["collect_faces.py", "--id", ma_sai, "--light", "bright"]):
        assert main() == 1
```

---

## 5. 🔵 Góp ý — không chặn, người dùng quyết định

1. **Bổ sung cờ `--note` cho manifest** (liên quan CẦN SỬA-1). Quy ước §5 đòi mô tả thật của buổi
   chụp, nhưng §4 đặc tả không có đường nhập. Chi phí: thêm 1 cờ argparse + 1 tham số `thu_thap`.
   Lợi: bước 1.10 giải thích được bất thường; bước 1.11 chia tập theo buổi chụp dễ hơn.
   Cần **sửa đặc tả trước**, không để Gemini tự thêm.
2. **Chặn hẳn việc thu dữ liệu thật bằng camera giả lập.** Ngoài việc ghi đúng backend (CHẶN-A-2),
   nên cho `thu_thap` từ chối ghi vào `data/` khi backend phân giải ra `CameraGiaLap`, trừ khi có cờ
   `--allow-mock`. Đây là hàng rào cuối chống việc ảnh tổng hợp lọt vào bộ dữ liệu của đồ án.
   Cần sửa đặc tả trước.
3. **Phím `q` chỉ thoát tư thế hiện tại** (`scripts/collect_faces.py:277`): `break` nằm trong vòng
   lặp ảnh nên script nhảy sang tư thế kế tiếp thay vì dừng buổi chụp. Người dùng bấm `q` thường muốn
   dừng hẳn. Nên dùng một cờ `dung_hen` để thoát cả hai vòng lặp.
4. **Nuốt lỗi im lặng** (`scripts/collect_faces.py:286-287`): `except cv2.error: pass`. Vô hại ở đây
   (dọn cửa sổ), nhưng nên `logger.debug("Không đóng được cửa sổ hiển thị: %s", e)` để giữ dấu vết.
   Tương tự, `logger.error` ở dòng 382 nên đổi thành `logger.exception` để giữ traceback khi lỗi
   phần cứng — chẩn đoán trên Pi sẽ đỡ mò.
5. **`sys.stdout.reconfigure` chạy khi import** (`scripts/collect_faces.py:10-13`): đây là tác dụng
   phụ toàn cục, ảnh hưởng cả tiến trình `pytest` khi test import module. Nên chuyển vào trong
   `main()`. Ba ca test 22–24 cũng đang phụ thuộc `configs/*.yaml` thật và thư mục làm việc; nếu chạy
   `pytest` từ thư mục khác thì 22–23 vẫn xanh **vì lý do sai** (nạp config thất bại cũng trả `1`).
   Nên trỏ `--config-data` vào file YAML tạm trong `tmp_path`.

## 6. Nhận xét chất lượng đặc tả

Đặc tả này tốt hơn hẳn `P1-01`: bốn bài học đều đã áp dụng và **có hiệu quả đo được** — §5 thuần
assert nên 25/25 dòng đều có hàm test tương ứng; lệnh đếm phạm vi có `--untracked-files=all` nên
kiểm phạm vi mất đúng một lệnh; §7 liệt kê thư viện được phép nên lỗi phụ thuộc không khai báo của
vòng 2 `P1-01` không tái diễn.

Ba chỗ đặc tả còn hở, đều dẫn thẳng tới lỗi ở trên:

- **§5 không ràng buộc "ca test phải thật sự đi qua đường code đang kiểm"**. Dòng 12 ghi *"Ghi nội
  dung đã biết vào `..._001.png`, chạy `thu_thap`, đọc lại **không đổi**"* — làm đúng từng chữ vẫn ra
  một test rỗng ruột nếu chọn `min_per_combo` sai. Lần sau nên ghi thẳng số liệu vào ô kỳ vọng:
  *"đã có 1 ảnh, `min_per_combo=3` → phải chụp thêm 2 ảnh; ảnh cũ không đổi"*.
- **§3 định nghĩa `hien_thi` bằng câu văn xuôi** (*"bỏ qua mọi lời gọi hiển thị cửa sổ"*) nhưng
  không nói **cái gì KHÔNG được tắt theo**. Bảng §5 cũng không có dòng nào kiểm nhịp chụp. Nên thêm
  một dòng ca biên dạng *"`hien_thi=False` vẫn phải in hướng dẫn tư thế và tôn trọng
  `capture_interval_s`"*.
- **§4 và quy ước §5 lệch nhau về manifest**: quy ước định nghĩa 10 cột (kèm `camera`, `note`), §4 và
  §5 đặc tả chỉ nhắc 6 cột, và không mục nào nói cột `camera` phải ghi **backend đã phân giải**.
  Khoảng trống này chính là chỗ CHẶN-A-2 chui qua. Đặc tả nên có một bảng ánh xạ từng cột manifest →
  nguồn giá trị.
- Nhỏ hơn: dòng 20 §5 tự mâu thuẫn — *"vẫn trả về kế hoạch để in ra"* nhưng assert `== []`.
  Gemini theo assert (đúng), nhưng câu chữ nên sửa thành *"trả về danh sách rỗng"*.

Ba lỗi 🔴 còn lại (CHẶN-A-1, CHẶN-B-1, CHẶN-B-2) **là lỗi cài đặt**, không đổ cho đặc tả được:
§4 đã ghi "Không hardcode giá trị nào", §7 G2 đã ghi hướng dẫn tư thế dùng `print`, §7 G6 và R24 đã
đòi an toàn khi `Ctrl+C`.

---

## 7. Việc tiếp theo

🔴 **TRẢ LẠI cho Gemini — vòng 2.** Thứ tự sửa đề nghị (từ rủi ro dữ liệu cao nhất xuống):

1. CHẶN-A-2 — ghi đúng backend vào cột `camera` + cảnh báo khi dùng camera giả lập
2. CHẶN-B-2 — ghi manifest theo từng tư thế, bọc `try/finally`
3. CHẶN-B-1 — tách hướng dẫn tư thế và nhịp chụp khỏi cờ `hien_thi`, đổi sang `print` theo G2
4. CHẶN-A-1 — thay mọi `.get(key, <mặc định>)` bằng `lay_gia_tri(cfg, key)`
5. CHẶN-B-3, CẦN SỬA-2, CẦN SỬA-3 — sửa ba ca test; thêm 3 ca mới (nhịp chụp, cột `camera`,
   manifest còn nguyên khi lỗi giữa chừng)

**Phạm vi file cho vòng 2 vẫn đúng 3 file** của §2 — không mở rộng. Không sửa `configs/`, không sửa
`src/`, không thêm thư viện.

Sau khi sửa, chạy lại đủ bộ trước khi báo xong:

```bash
black --check --line-length 100 src tests scripts
ruff check src tests scripts
pytest -q                      # phải ≥ 80 ca, không ca nào đỏ
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q
git status --short --untracked-files=all | grep -v "docs/review/" | wc -l   # phải trả 3
```

Chưa có phán quyết ĐẠT thì **không commit** (R40).

---
---

# Review P1-02-collect-faces — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-02-collect-faces.md` (bản đã cập nhật, commit `470cc05`) |
| **Nhánh** | `feat/p1-02-collect-faces` |
| **Ngày** | 2026-08-14 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — chỉ còn **1 lỗi 🟡, sửa 3 dòng trong file test**, không phải sửa mã sản phẩm |

Tổng hợp: **0 🔴 CHẶN-A · 0 🔴 CHẶN-B · 1 🟡 CẦN SỬA · 4 🔵 góp ý**.

**Cả 5 lỗi chặn của vòng 1 đã được sửa đúng, đã kiểm chứng độc lập bằng phép đo chứ không đọc mắt.**
Ba ca test rỗng ruột cũng đã vá đúng chỗ. Lỗi còn lại duy nhất: ca test dòng 25 vá thiếu 3 trong 4
hàm mà bảng §5 liệt kê — vẫn để hở một nhánh code có thật.

---

## 1. Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | 3 file danh sách trắng + biên bản review ✅ |
| `... | grep -v "docs/review/" | wc -l` | trả đúng **`3`** ✅ |
| `git diff dev -- configs/ src/` | **rỗng** ✅ |
| `black --check --line-length 100 src tests scripts` | `17 files would be left unchanged` ✅ |
| `ruff check src tests scripts` | `All checks passed!` ✅ |
| `pytest -q` (host) | **84 passed in 2.69s** ✅ đúng con số điều phối báo |
| `pytest -q` (container ARM64, lệnh §6 đã sửa) | **84 passed in 15.41s**, `platform.machine()` = `aarch64` ✅ |
| `git status` sau `pytest` | không file mới, `data/` rỗng ✅ |
| `python scripts/collect_faces.py --help` | mã thoát 0, mô tả tiếng Việt ✅ |
| `--id u01 --light bright --dry-run --no-preview` | mã thoát **0**, `find data -type f` **rỗng** ✅ |

Lệnh container ở §6 nay **chạy đúng nguyên văn** — không phải mò lại như vòng 1.

### Quét mẫu vi phạm

| Mẫu | Kết quả |
|---|---|
| Thư viện ngoài `cv2`/`numpy`/chuẩn | không có ✅ |
| `subprocess` / `shutil.which` trong test | không có ✅ |
| `except` trần, `pass` nuốt lỗi | không còn — dòng 296-297 đã đổi thành `logger.debug` ✅ |
| Log dùng f-string | không có ✅ |
| **`cfg_data.get(` / `cfg_capture.get(` còn sót** | **không còn dòng nào** ✅ |
| Số magic là tham số thực nghiệm | không có ✅ |

---

## 2. Xác minh từng lỗi vòng 1 — bằng phép đo độc lập

Mọi kết quả dưới đây do người review tự dựng kịch bản chạy, **không dùng lại test của Gemini**.

| Lỗi vòng 1 | Phép kiểm đã chạy | Kết quả |
|---|---|---|
| 🔴 CHẶN-A-1 hardcode config | quét toàn file tìm `cfg_data.get`/`cfg_capture.get` | **0 dòng**; 12 tham số đều qua `lay_gia_tri` — `scripts/collect_faces.py:202-207`, `:338-343` ✅ **ĐÃ SỬA** |
| 🔴 CHẶN-A-2 cột `camera` ghi `"auto"` | `thu_thap` với `backend="auto"`, `opencv.device_index=99` trên máy không camera, 3 ảnh | `set(camera)` = `{'CameraGiaLap'}`; chuỗi `,auto,` **không xuất hiện** trong `manifest.csv` ✅ **ĐÃ SỬA** |
| — kèm theo | `width`/`height` từ khung hình thật: mock `640×480` | manifest ghi `640×480`, `cv2.imread` ảnh trên đĩa cũng `640×480` — **khớp nhau** ✅ |
| 🔴 CHẶN-B-1 `--no-preview` tắt nhịp chờ | 4 ảnh, `capture_interval_s=0.2`, `pose_switch_delay_s=0` | **0.91 s** (ngưỡng ≥ 0.6) — vòng 1 là 0.12 s ✅ **ĐÃ SỬA** |
| 🔴 CHẶN-B-1 tắt hướng dẫn tư thế | bắt `stdout` khi `hien_thi=False`, poses `["left","up"]` | stdout chứa cả `left` lẫn `up`; dòng đầu: `>>> Tư thế: left (bright) — cần chụp thêm 1 ảnh.` ✅ **ĐÃ SỬA** |
| 🔴 CHẶN-B-2 mất manifest khi lỗi | `doc_frame` ném `LoiCamera` ở lần thứ 3, `min_per_combo=6` | **2 ảnh trên đĩa / 2 dòng dữ liệu manifest — khớp**; vòng 1 là 2 ảnh / không có file ✅ **ĐÃ SỬA** |
| 🔴 CHẶN-B-2 (kiểm thêm) `Ctrl+C` | `doc_frame` ném `KeyboardInterrupt` ở lần thứ 3 | **2 ảnh / 2 dòng manifest**, ngoại lệ vẫn lan ra ngoài đúng cách ✅ — khối `finally` `:301-304` phủ luôn G6 |
| 🔴 CHẶN-B-3 `test_12` rỗng ruột | đọc `tests/test_collect_faces.py:137-146` + chạy lại kịch bản | `min_per_combo=3`, có assert `..._002.png` và `..._003.png` tồn tại — **đi qua đúng đường không-ghi-đè** ✅ **ĐÃ SỬA** |
| 🟡 CẦN SỬA-1 cột `note` bịa | đọc `scripts/collect_faces.py:269` | `"note": ""` ✅ **ĐÃ SỬA** |
| 🟡 CẦN SỬA-2 `test_25` không assert | quét AST toàn file test | **30 hàm test, 0 hàm không có assert** ✅ **ĐÃ SỬA** (còn dư một điểm — xem §4) |
| 🟡 CẦN SỬA-3 `test_22` thiếu mã sai | đọc `tests/test_collect_faces.py:368-372` | `@pytest.mark.parametrize("ma_sai", ["abc", "u1", "y01"])` — đủ **cả ba** ✅ **ĐÃ SỬA** |

### Bốn điểm soi kỹ của vòng 1 — chạy lại để chắc không có hồi quy

| Điểm | Kết quả |
|---|---|
| Dòng 11 — đánh số tiếp tục | có sẵn `_007`, `min_per_combo=3` → sinh `008`, `009` ✅ |
| Dòng 12 — không ghi đè | byte cũ nguyên vẹn, ảnh mới `002`, `003` ✅ |
| Dòng 17 — manifest ghi nối | 2 lần chạy → 5 dòng / 4 ảnh / **đúng 1 dòng tiêu đề** ✅ |
| Dòng 25 — `hien_thi=False` | vá **6** hàm `cv2` (`imshow`, `waitKey`, `namedWindow`, `destroyAllWindows`, `destroyWindow`, `startWindowThread`) → **không ném**, trả về 2 bản ghi ✅ |

---

## 3. Đối chiếu đặc tả (bản cập nhật)

| Mục | Kết luận |
|---|---|
| §2 Danh sách trắng | ✅ đúng 3 file |
| §3 Interface | ✅ khớp từng ký tự |
| **§3.1 phạm vi `hien_thi`** | ✅ **đúng cả 4 dòng bảng**: chỉ `imshow`/`waitKey`/`destroyAllWindows` nằm trong `if hien_thi` (`:274-276`, `:293-297`); hướng dẫn tư thế (`:233-234`), `pose_switch_delay_s` (`:235-236`), `capture_interval_s` (`:281-283`) và ghi manifest (`:290`) đều **ngoài** guard |
| §4 Tham số → config | ✅ 12/12 key qua `lay_gia_tri`, không mặc định hardcode |
| **§4.1 Cột manifest → nguồn** | ✅ **9/9 cột đúng nguồn**: `camera` = `type(cam).__name__` (`:216`, `:266`), `width`/`height` = `frame.shape[:2]` (`:256`), `note` = `""` |
| §4 Tham số dòng lệnh | ✅ đủ 7 cờ |
| §5 Ca biên | ⚠️ **30/30 dòng có ca test, 29/30 đi qua đúng đường code cần kiểm** — dòng 25 còn hở, xem §4 |
| §6 Nghiệm thu | ✅ 11/11 mục chạy được và đạt |
| §7 Quy tắc | ✅ G1, G2 (hướng dẫn tư thế dùng `print`), G4, G5, G6 (`try/finally` + context manager), R15 |
| §8 Ngoài phạm vi | ✅ không làm gì thêm |
| Quy ước dữ liệu §3, §5, §6 | ✅ tên file, 10 cột manifest, PNG lấy từ `image_format` |

### Rà 30 dòng bảng §5

Dòng 1-11, 12, 12a, 12b, 12c, 12d, 12e, 13-24: **đều có ca test đi qua đúng đường code**, đã đối
chiếu từng ca với thân hàm tương ứng trong `scripts/collect_faces.py`. Dòng 25: có ca test, có
assert, nhưng **vá thiếu 3 trong 4 hàm** đặc tả liệt kê — mục lỗi duy nhất bên dưới.

Một ghi nhận để khỏi hiểu nhầm là bỏ sót: ca `test_12d` dùng **2 ảnh và ngưỡng 0.5 s** thay vì
"4 ảnh, ≥ 0.6 s" như ô assert của đặc tả. Đây **không** tính là lỗi, vì nhịp chờ nằm trong vòng lặp
từng ảnh nên 2 vòng lặp đã đi qua đúng đường code đó, và ngưỡng vẫn phân biệt được: nếu
`capture_interval_s` bị bỏ qua thì thời gian trôi chỉ còn 0.2 s < 0.5 s và ca test đỏ. Khác hẳn dòng
25, nơi có một **nhánh code không được ca test nào chạm tới**.

---

## 4. Lỗi phải sửa

### 🟡 CẦN SỬA-1 — Ca test dòng 25 vá thiếu 3/4 hàm hiển thị, để hở nhánh `destroyAllWindows` (CS-4)

**Vị trí**: `tests/test_collect_faces.py:390-401`

```python
def test_25_hien_thi_false_khong_goi_imshow(tmp_path, cfg_data, cfg_capture, monkeypatch):
    def throw_err(*args, **kwargs):
        raise AssertionError("Không được gọi cv2.imshow khi hien_thi=False")

    monkeypatch.setattr(cv2, "imshow", throw_err)      # ← chỉ vá 1 hàm
```

Dòng 25 bảng §5 ghi rõ ở ô "Assert tối thiểu": *"Vá `cv2.imshow`, `cv2.waitKey`, `cv2.namedWindow`,
`cv2.destroyAllWindows` bằng hàm ném `AssertionError`"*. Quét AST xác nhận thân hàm test chỉ nhắc
tên `imshow`; ba tên còn lại **không xuất hiện**.

**Vì sao đây không phải chuyện câu chữ**: mã nguồn có **hai** khối `if hien_thi:` riêng biệt, không
phải một:

- `scripts/collect_faces.py:274-276` — `imshow` + `waitKey` (ca test hiện tại có phủ)
- `scripts/collect_faces.py:293-297` — `destroyAllWindows` (**ca test hiện tại không phủ chút nào**)

Khối thứ hai nằm ở cuối mỗi tư thế và trông y như mã dọn dẹp vô hại. Người sửa sau này hoàn toàn có
thể nghĩ "dọn cửa sổ thì lúc nào chẳng nên chạy" rồi bỏ guard đi — `pytest` vẫn xanh 84 ca, `ruff`
vẫn sạch, mà script thì gãy trên Pi chạy headless qua SSH, đúng môi trường thu thập thật. Đây chính
là loại hồi quy mà dòng 25 sinh ra để chặn.

**Sửa**: vá cả bốn hàm bằng cùng một hàm giả, giữ nguyên phần assert đã có. Cách này đã được kiểm
chứng là **chạy qua** với mã nguồn hiện tại (người review thử với 6 hàm vẫn qua), nên **không phải
sửa `collect_faces.py`**:

```python
def test_25_hien_thi_false_khong_goi_ham_hien_thi(tmp_path, cfg_data, cfg_capture, monkeypatch):
    """hien_thi=False không gọi bất kỳ hàm hiển thị cửa sổ nào của cv2."""

    def throw_err(*args, **kwargs):
        raise AssertionError("Không được gọi hàm hiển thị khi hien_thi=False")

    for ten_ham in ("imshow", "waitKey", "namedWindow", "destroyAllWindows"):
        monkeypatch.setattr(cv2, ten_ham, throw_err)

    cfg_data["poses"] = ["frontal"]
    cfg_data["min_per_combo"] = 2
    ban_ghi = thu_thap(cfg_data, cfg_capture, "u01", "bright", tmp_path, hien_thi=False)
    assert len(ban_ghi) == 2
    assert (tmp_path / "u01_frontal_bright_002.png").exists()
```

Đây là **thay đổi duy nhất** cần cho vòng 3.

---

## 5. 🔵 Góp ý — không chặn

1. **`thu_thap` gãy vì `UnicodeEncodeError` khi được gọi ngoài `main()` trên console Windows cp1252.**
   Đây là hệ quả trực tiếp của góp ý số 5 vòng 1 (dời `sys.stdout.reconfigure` vào `main()`) — người
   review nhận phần trách nhiệm. Tái hiện được:

   ```
   File "scripts/collect_faces.py", line 233, in thu_thap
       print(f"\n>>> Tư thế: {pose} ...")
   UnicodeEncodeError: 'charmap' codec can't encode character 'ư'
   ```

   **Đường CLI hoàn toàn an toàn** vì `main()` gọi `reconfigure` trước (`:311-315`), container dùng
   UTF-8, và `pytest` cũng không dính. Chỉ gãy khi import `thu_thap` như thư viện từ script khác trên
   Windows — kịch bản có thể xuất hiện ở bước 1.6. Nếu muốn chắc: tách hàm `_bat_utf8()` gọi ở đầu cả
   `main()` lẫn `thu_thap()`. Cần sửa đặc tả trước vì §3 không định nghĩa hàm này.

2. **Mất docstring cấp module** ở `scripts/collect_faces.py:1` — vòng 1 có, nay file mở đầu thẳng
   bằng `import sys`. G4 chỉ đòi docstring cho **hàm** public nên không phải lỗi, nhưng mọi file
   trong `src/` và cả `tests/test_collect_faces.py:1` đều có; nên trả lại cho đồng bộ.

3. **`except Exception` ở `:403` vẫn dùng `logger.error`** thay vì `logger.exception`, nên mất
   traceback. Giữ nguyên góp ý vòng 1: khi lỗi camera xảy ra trên Pi, có traceback đỡ mò rất nhiều.

4. **Ba ca test 22-24 vẫn đọc `configs/*.yaml` thật** và phụ thuộc thư mục làm việc. Chạy `pytest` từ
   thư mục khác thì 22-23 vẫn xanh **vì lý do sai** (nạp config thất bại cũng trả `1`). Nên trỏ
   `--config-data` vào file YAML tạm trong `tmp_path`.

---

## 6. Nhận xét chất lượng đặc tả sau lần sửa

Bốn thay đổi đều **trúng đích và hiệu quả đo được**:

- **§3.1** là kiểu mục nên có ở mọi cờ boolean: bảng hai cột "tắt cái gì / KHÔNG được tắt cái gì" xoá
  sạch khoảng diễn giải mà CHẶN-B-1 vòng 1 đã chui qua. Đoạn giải thích *"chụp 4 ảnh trong 0,12 giây
  thì cả bốn ảnh đều cùng một tư thế nhưng vẫn được gắn nhãn `left`, `up`, `down`"* đưa **hậu quả**
  vào đặc tả chứ không chỉ đưa quy tắc — người cài đặt hiểu vì sao thì khó làm sai.
- **§4.1** đóng đúng lỗ hổng của CHẶN-A-2. Ô cấm `"auto"` viết ở thể phủ định tuyệt đối
  (*"tuyệt đối không được ghi"*) là cách diễn đạt tốt nhất cho ràng buộc kiểu này.
- **Dòng 12 sửa thành `min_per_combo=3` kèm cảnh báo *"nếu số ảnh cần chụp bằng 0 thì đường
  không-ghi-đè không hề chạy — ca test rỗng ruột"*** là thay đổi có giá trị nhất: nó dạy nguyên tắc
  "ca test phải đi qua đường code", không chỉ vá một ca cụ thể. Năm dòng 12a-12e đều được cài đúng
  ngay lần đầu.
- **§6** sửa lệnh container thành đúng biến thể chạy được, tiết kiệm nguyên một vòng mò lệnh.

Hai chỗ còn có thể siết thêm cho các mã việc sau:

- **Ô "Assert tối thiểu" cần được đọc như danh sách kiểm, không phải gợi ý.** Dòng 25 liệt kê bốn hàm,
  Gemini vá một, và không có gì trong quy trình bắt được chuyện đó ngoài mắt người review. Khi ô
  assert liệt kê nhiều mục thì nên tách thành nhiều dòng bảng (25a, 25b…) hoặc ghi rõ *"vá **cả bốn**
  hàm trong cùng một ca"*. Cách đánh số 12a-12e ở lần sửa này đã chứng minh là hiệu quả — mỗi dòng
  một ca, không dòng nào bị làm nửa vời.
- **§4.1 nhắc `--note`** (*"`--note` nếu có, mặc định rỗng"*) nhưng bảng cờ dòng lệnh §4 **không có**
  `--note`. Gemini xử lý đúng (ghi `""`), nhưng câu chữ vẫn để hở. Nên bỏ cụm "`--note` nếu có" cho
  tới khi thật sự mở mã việc thêm cờ đó.

Một ghi nhận về mức độ tuân thủ: **12/12 điểm sửa được yêu cầu đều làm đúng ngay vòng đầu**, kể cả
những điểm chỉ nêu trong phần "cách sửa" của biên bản (dùng `lay_gia_tri`, khối `try/finally`, cảnh
báo khi gặp `CameraGiaLap`, `logger.debug` thay `pass`). Khối `finally` còn phủ luôn `Ctrl+C` — điều
biên bản không yêu cầu tường minh nhưng G6 có đòi. Đây là dấu hiệu đặc tả và biên bản đang đủ cụ thể
để thực thi mà không cần đối thoại.

---

## 7. Việc tiếp theo

🔴 **TRẢ LẠI — vòng 3, phạm vi một file, một hàm.**

Chỉ sửa `tests/test_collect_faces.py:390-401` theo mục CẦN SỬA-1 ở trên. **Không đụng
`scripts/collect_faces.py`** — mã sản phẩm đã đạt.

Trần 2 vòng của quy trình **không bị chạm**: không còn lỗi 🔴 nào, nên đây không phải tình huống bế
tắc (mã việc quá to / đặc tả mơ hồ / yêu cầu bất khả thi) mà chỉ là một lượt vá cuối. Nếu người dùng
thấy không đáng thêm một vòng, đây là lỗi 🟡 duy nhất và người dùng có quyền **miễn trừ** để commit
ngay — nhưng khi đó cần ghi nhận rằng nhánh `destroyAllWindows` đang không có ca test nào canh.

Sau khi sửa, chạy lại:

```bash
black --check --line-length 100 src tests scripts
ruff check src tests scripts
pytest -q                     # phải vẫn 84 passed
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q
git status --short --untracked-files=all | grep -v "docs/review/" | wc -l   # phải trả 3
```

Khi ca test dòng 25 đã vá đủ bốn hàm, mã việc **ĐẠT** và commit được với:

```
feat(scripts): P1-02 script thu thap anh khuon mat co huong dan tu the
```

Nội dung mô tả gợi ý: đếm theo tổ hợp `(pose, light)`, đánh số tiếp tục qua nhiều buổi chụp, không
ghi đè ảnh cũ, manifest ghi nối theo từng tư thế và giữ nguyên khi lỗi giữa chừng, cột `camera` ghi
backend đã phân giải để phân biệt ảnh thật với ảnh giả lập.

---
---

# Review P1-02-collect-faces — vòng 3

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-02-collect-faces.md` (bản có §5 dòng 25a/25b/25c và cờ `--note`) |
| **Nhánh** | `feat/p1-02-collect-faces` |
| **Ngày** | 2026-08-14 |
| **Phán quyết** | ✅ **ĐẠT** |

Tổng hợp: **0 🔴 · 0 🟡 · 3 🔵 góp ý.** Lỗi 🟡 duy nhất của vòng 2 đã được sửa, và lần này **không
kết luận bằng đọc mã hay đếm chuỗi** — đã chứng minh bằng **kiểm thử đột biến** (mutation testing).

---

## 1. Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | 3 file danh sách trắng + biên bản review ✅ |
| `... \| grep -v "docs/review/" \| wc -l` | trả đúng **`3`** ✅ |
| `git diff dev -- configs/ src/` | **rỗng** ✅ |
| `black --check --line-length 100 src tests scripts` | `17 files would be left unchanged` ✅ |
| `ruff check src tests scripts` | `All checks passed!` ✅ |
| `pytest -q` (host) | **86 passed in 1.76s** ✅ (vòng 2: 84 — thêm đúng 2 ca do tách 25a/b/c) |
| `pytest -q` (container ARM64, lệnh §6) | **86 passed in 7.46s** ✅ |
| `python scripts/collect_faces.py --help` | mã thoát 0, mô tả tiếng Việt ✅ |
| `--id u01 --light bright --dry-run --no-preview` | mã thoát 0, `data/` có **0 file** ✅ |

**Xác nhận phạm vi N4 (chỉ được sửa file test)**: `scripts/collect_faces.py` **không đổi** so với
vòng 2 — vẫn đúng **409 dòng**, và 13 dòng mốc đã đối chiếu ở vòng 2 (`:202`, `:216`, `:266`, `:269`,
`:274`, `:290`, `:293`, `:301-304`, `:311-315`) trùng khớp từng ký tự. `tests/test_collect_faces.py`
tăng từ 402 lên 432 dòng. Đúng phạm vi được phép.

Quét mẫu vi phạm: thư viện ngoài, `subprocess` trong test, `cfg_data.get`/`cfg_capture.get` còn sót —
**cả ba đều không có kết quả** ✅

---

## 2. Kiểm chốt cho dòng 25c — kiểm thử đột biến

Vòng 2 chỉ ra: mã có **hai** khối `if hien_thi:` riêng biệt, và khối thứ hai
(`scripts/collect_faces.py:293`, gọi `destroyAllWindows`) **không ca test nào chạm tới**. Đếm số lần
xuất hiện chuỗi `destroyAllWindows` trong file test **không chứng minh được** điều ngược lại — một ca
test có thể nhắc tên hàm mà vẫn không chạy qua nhánh đó. Nên phép kiểm dùng ở đây là **đột biến**:
cố tình làm hỏng mã sản phẩm, rồi xem bộ test có bắt được không.

**Cách làm**: sao lưu nguyên văn `scripts/collect_faces.py`, đổi `if hien_thi:` thành `if True:`
(tức bỏ guard), chạy lại `pytest tests/test_collect_faces.py`, rồi **khôi phục và đối chiếu
`sha256`**. Toàn bộ nằm trong `try/finally` để không bao giờ để lại thay đổi.

| Đột biến | Kết quả | Đọc kết quả |
|---|---|---|
| **A — bỏ guard quanh `destroyAllWindows`** (`:293`) | `3 failed, 31 passed` — đỏ đúng **`test_25a`, `test_25b`, `test_25c`** | ✅ khối dọn dẹp **đã được phủ**. Ba ca chết đúng ba ca sinh ra để canh nó, không ca nào khác — chứng tỏ phép kiểm **nhắm trúng đích**, không phải đỏ vì hiệu ứng phụ |
| **B — bỏ guard quanh `imshow`/`waitKey`** (`:274`) | `15 failed, 19 passed`, trong đó có `test_25a`, `test_25b`, `test_25c` | ✅ khối vòng lặp chụp cũng được phủ, và còn được 12 ca khác canh gián tiếp |

Đối chiếu trực tiếp với vòng 2: khi đó `test_25` chỉ vá `cv2.imshow`, nên đột biến A sẽ **không làm
đỏ ca nào** — đúng lỗ hổng biên bản vòng 2 đã nêu. Nay lỗ hổng đã bịt.

**Khôi phục nguyên trạng**: `sha256` của `scripts/collect_faces.py` trước và sau khi thử đều là
`f2ed834b6852ad4179a0a2cb94d87fb5a72193e5b2eb1657ffcbb48cdabfffb5` — **giống hệt**. Chạy lại bộ test
trên bản gốc: `34 passed`. Cây làm việc sạch, `git status` vẫn đúng 3 file.

---

## 3. Đối chiếu ba dòng 25a/25b/25c

| Dòng | Ca test | Kết luận |
|---|---|---|
| **25a** — vá **cả bốn** hàm, `thu_thap(hien_thi=False)` không ném | `tests/test_collect_faces.py:390-401` | ✅ quét AST xác nhận thân hàm vá đủ `imshow`, `waitKey`, `namedWindow`, `destroyAllWindows` |
| **25b** — cùng ca đó `assert len(ban_ghi) == so_anh_mong_doi` | `:404-418` | ✅ vá đủ bốn hàm, `assert len(ban_ghi) == 2` + hai ảnh `001`, `002` tồn tại |
| **25c** — khối dọn dẹp cuối hàm cũng trong guard và được chạy qua | `:421-432` | ✅ vá `destroyAllWindows`, 2 tư thế × 1 ảnh, `assert len(ban_ghi) == 2`; **đột biến A chứng minh ca này thật sự canh khối `:293`** |

### Quét AST toàn bộ file test

**32 hàm test, 1 hàm không có câu `assert`: `test_25a` (`:390`).**

Đây **không** phải lỗi, và khác hẳn tình huống vòng 1. Lý do:

- Đặc tả **cố ý** tách 25a (kiểm "không ném") khỏi 25b (kiểm "chạy hết thân hàm"). Cơ chế kiểm của
  25a là hàm vá ném `AssertionError`, nên câu `assert` tường minh không có chỗ đứng tự nhiên.
- Vòng 1, ca test dòng 25 không assert **và** không có ca anh em nào bù — một cài đặt thoát sớm vẫn
  qua được. Nay `test_25b` chốt đúng lỗ đó bằng `assert len(ban_ghi) == 2` với **cùng bộ vá**.
- Quan trọng nhất: **đột biến A làm `test_25a` đỏ**. Một ca test giết được đột biến thì theo định
  nghĩa là ca test có hiệu lực, dù không chứa từ khoá `assert`.

Nếu muốn con số AST tuyệt đối sạch cho các lần quét tự động về sau, thêm
`assert len(ban_ghi) == 2` vào cuối `test_25a` là đủ — nhưng đó là chuyện thẩm mỹ của phép quét, không
phải chuyện đúng sai của phép kiểm. Ghi ở mục góp ý, **không chặn**.

---

## 4. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §2 Danh sách trắng | ✅ đúng 3 file; N4 chỉ cho sửa file test và đã tuân thủ |
| §3 Interface | ✅ khớp từng ký tự |
| §3.1 Phạm vi `hien_thi` | ✅ đúng cả 4 dòng bảng, nay **có kiểm thử đột biến làm chứng** |
| §4 Tham số → config | ✅ 12/12 key qua `lay_gia_tri` |
| §4.1 Cột manifest → nguồn | ✅ 9/9 cột đúng nguồn |
| §4 Tham số dòng lệnh | ⚠️ 7/8 — cờ `--note` mới thêm vào đặc tả **chưa được cài** (xem §5 dưới đây) |
| §5 Ca biên | ✅ **32/32 dòng có ca test đi qua đúng đường code cần kiểm** |
| §6 Tiêu chí nghiệm thu | ✅ **11/11 đạt** |
| §7 Quy tắc | ✅ G1, G2, G4, G5, G6, R15 |
| §8 Ngoài phạm vi | ✅ không làm gì thêm |
| Quy ước dữ liệu §3, §5, §6 | ✅ tên file, 10 cột manifest, PNG từ `image_format` |

---

## 5. Một khoản nợ quy trình cần ghi nhận — cờ `--note`

**Không tính là lỗi của mã nguồn, nhưng phải ghi lại để khỏi rơi mất.**

Bản đặc tả vòng 3 bổ sung cờ `--note` vào bảng §4 (dòng 155) cho khớp với §4.1 (dòng 135, *"`note` ←
`--note` nếu có"*). Nhưng lệnh bàn giao N4 của vòng 3 **chỉ cho phép sửa `tests/test_collect_faces.py`**.
Kết quả: `python scripts/collect_faces.py --help` hiện **không có** `--note`, và cột `note` trong
manifest luôn rỗng.

Vì sao **không** trả lại vì việc này:

- Gemini làm **đúng** chỉ thị được giao; sửa `scripts/` ở vòng 3 mới là vi phạm phạm vi.
- §5 **chưa có dòng ca biên nào** cho `--note`, §6 **chưa có tiêu chí nghiệm thu nào** cho nó. Cài đặt
  bây giờ sẽ là mã không có test canh — đúng thứ ba vòng vừa rồi mất công dẹp.
- Hệ quả hiện tại là **vô hại và trung thực**: cột `note` rỗng nghĩa là "chưa ai ghi chú", không phải
  một giá trị bịa. Khác hẳn `"bright light"` của vòng 1.

**Đề nghị**: mở mã việc nhỏ **`P1-02b-note-manifest`** làm trước bước 1.3 (thu ảnh thật), gồm ba
việc: thêm dòng ca biên vào §5 (`--note "den tran"` → cột `note` trong manifest bằng `den tran`;
không truyền `--note` → cột rỗng), thêm cờ vào `argparse` và tham số `note: str = ""` cho `thu_thap`,
thêm hai ca test. Ước lượng: 2 file, ~25 dòng. Nếu người dùng thấy chưa cần thì **gỡ cụm "`--note`
nếu có" khỏi §4.1 và bỏ dòng 155** để đặc tả và mã nguồn không lệch nhau.

---

## 6. 🔵 Góp ý — không chặn

1. **`test_25a` không có câu `assert` tường minh** (`tests/test_collect_faces.py:390`). Đã chứng minh
   là có hiệu lực bằng đột biến A, nhưng mọi phép quét AST tự động về sau sẽ báo nó. Thêm
   `assert len(ban_ghi) == 2` vào cuối là xong.
2. **Ba góp ý của vòng 2 vẫn còn nguyên**, đều nằm ngoài phạm vi N4 nên chưa xử lý:
   `UnicodeEncodeError` khi gọi `thu_thap` ngoài `main()` trên console Windows cp1252 (đường CLI và
   container vẫn an toàn); thiếu docstring cấp module ở `scripts/collect_faces.py:1`;
   `except Exception` ở `:403` nên dùng `logger.exception` để giữ traceback.
3. **Ba ca test 22-24 vẫn đọc `configs/*.yaml` thật** và phụ thuộc thư mục làm việc — chạy `pytest`
   từ thư mục khác thì 22-23 vẫn xanh vì lý do sai. Nên trỏ `--config-data` vào YAML tạm trong
   `tmp_path`.

Cả ba đều là việc nhỏ, gộp được vào `P1-02b` nếu mở mã việc đó.

---

## 7. Tổng kết ba vòng

### Số liệu

| | Vòng 1 | Vòng 2 | Vòng 3 |
|---|---|---|---|
| Phán quyết | 🔴 TRẢ LẠI | 🔴 TRẢ LẠI | ✅ **ĐẠT** |
| 🔴 CHẶN-A | 2 | 0 | 0 |
| 🔴 CHẶN-B | 3 | 0 | 0 |
| 🟡 CẦN SỬA | 3 | 1 | 0 |
| 🔵 Góp ý | 5 | 4 | 3 |
| `pytest -q` (host) | 77 passed | 84 passed | **86 passed** |
| Container ARM64 | 77 passed | 84 passed | **86 passed** |
| Dòng bảng §5 | 25 (23 có hiệu lực) | 30 (29 có hiệu lực) | **32 (32 có hiệu lực)** |
| Số dòng đặc tả | 209 | 256 | 262 |
| Phạm vi file | 3/3 đúng | 3/3 đúng | 3/3 đúng |

Không vòng nào có vi phạm phạm vi file, không vòng nào có ảnh/model/secret lọt git, không vòng nào
`data/` bị chạm.

### Năm lỗi chặn của vòng 1 và nguồn gốc

| Lỗi | Nguồn gốc | Bằng chứng |
|---|---|---|
| Hardcode mặc định cho 12 tham số config | **Cài đặt** | §4 đã ghi rõ *"Không hardcode giá trị nào"*, và `src/common/config.py` đã có sẵn `lay_gia_tri` |
| Cột `camera` ghi `"auto"` thay vì backend đã phân giải | **Đặc tả** | §4 cũ không có bảng cột manifest → nguồn giá trị; đã sửa thành §4.1 |
| `--no-preview` tắt luôn hướng dẫn tư thế và nhịp chờ | **Đặc tả** (một phần cài đặt) | §3 cũ mô tả bằng văn xuôi, không nói cái gì **không** được tắt; đã sửa thành bảng §3.1. Riêng phần dùng `logger` thay `print` là sai G2 đã ghi rõ |
| Mất toàn bộ manifest khi lỗi camera hoặc `Ctrl+C` | **Cài đặt** | G6 và R24 đã đòi an toàn khi ngắt giữa chừng |
| Ba ca test rỗng ruột (`test_12`, `test_25`, `test_22`) | **Đặc tả** | Ô "Assert tối thiểu" mô tả thao tác mà không chốt số liệu; làm đúng từng chữ vẫn ra ca test không đi qua đường code |

**Ba trong năm lỗi chặn có gốc ở đặc tả.** Con số này khớp với kinh nghiệm ghi trong quy trình review:
phần lớn vòng lặp thất bại là lỗi đặc tả, không phải lỗi người viết mã.

### Ba bài học dùng được cho các mã việc sau

1. **Ô "Assert tối thiểu" phải chốt số liệu, không mô tả thao tác.** Vòng 1 ghi *"ghi nội dung đã biết
   vào `..._001.png`, chạy `thu_thap`, đọc lại không đổi"* → Gemini chọn `min_per_combo=1`, số ảnh cần
   chụp thành 0, ca test không đi qua đường nào. Vòng 2 ghi thẳng `min_per_combo=3` kèm cảnh báo
   *"nếu số ảnh cần chụp bằng 0 thì đường không-ghi-đè không hề chạy"* → cài đúng ngay lần đầu.
   **Một dòng bảng = một khẳng định.** Dòng nào liệt kê nhiều thứ trong cùng một ô thì tách thành
   `12a`–`12e`, `25a`–`25c`: cả 8 dòng tách theo cách này đều đúng ngay lần đầu, còn dòng 25 gộp bốn
   hàm vào một ô thì bị làm nửa vời.
2. **Cờ boolean phải có bảng "tắt cái gì / KHÔNG được tắt cái gì".** `hien_thi=False` mô tả bằng văn
   xuôi đã kéo theo việc tắt luôn hướng dẫn tư thế và nhịp chụp — hỏng nhãn tư thế của toàn bộ dataset
   mà `pytest` vẫn xanh.
3. **Mọi cột dữ liệu ghi ra đĩa phải có bảng "cột → nguồn giá trị".** Không có bảng đó thì giá trị cấu
   hình thô (`"auto"`) lọt vào manifest, và ảnh tổng hợp của `CameraGiaLap` trở nên không phân biệt
   được với ảnh chụp thật.

### Điều đáng ghi cho phần bàn về quy trình (Chương 3)

Ở vòng 2, bộ test **84 ca xanh, `black` và `ruff` sạch** vẫn cùng tồn tại với một nhánh mã **không ca
test nào chạm tới**. Ba lệnh máy không phát hiện được, và đọc mã cũng chỉ cho một nghi ngờ. Thứ biến
nghi ngờ thành kết luận là **kiểm thử đột biến**: bỏ guard, chạy lại, xem có ca nào đỏ không.
Đây là bằng chứng cụ thể cho luận điểm *"số ca test xanh không đo được chất lượng bộ test"* — dùng
được trực tiếp trong phần bàn về phương pháp phát triển của báo cáo.

---

## 8. Việc tiếp theo

✅ **ĐẠT — được commit.**

```
feat(scripts): P1-02 script thu thap anh khuon mat co huong dan tu the
```

Nội dung mô tả commit đề nghị:

```
- Dem anh da co theo tung to hop (pose, light), chi chup phan con thieu
- Danh so tiep tuc qua nhieu buoi chup, tuyet doi khong ghi de anh cu
- Manifest ghi noi theo tung tu the; loi camera hay Ctrl+C giua chung
  van giu du metadata cua phan da chup (khong de anh mo coi)
- Cot camera ghi backend DA PHAN GIAI (CameraOpenCV / CameraGiaLap) de
  phan biet anh that voi anh gia lap; width/height lay tu frame.shape
- --no-preview chi tat cua so hien thi, khong tat huong dan tu the va
  nhip chup
- 32 ca test, chay xanh tren host va container ARM64
- Bien ban review: docs/review/P1-02-collect-faces.review.md (3 vong)
```

Sau khi commit và gộp vào `dev`:

1. **Mở `P1-02b-note-manifest`** (§5 biên bản này) hoặc gỡ `--note` khỏi đặc tả — chọn một, đừng để
   đặc tả và mã nguồn lệch nhau.
2. Bước 1.2 của Phase 1 khép lại. Bước 1.3 (thu ảnh thật, 2-3 người × ≥ 100 ảnh) **chờ camera của hệ
   thống** — vẫn nằm trong phần đã ghi ở `docs/dieu-chinh-pham-vi.md`.
3. Việc làm được ngay mà không cần phần cứng: bước 1.5 (tải LFW ≥ 100 danh tính).
4. Ghi mã việc `P1-02-collect-faces` vào `docs/nhat-ky/tuan-04.md` kèm bảng ba vòng ở §7 trên.
