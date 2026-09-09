# Review P1-05-preprocess — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-05-preprocess.md` |
| **Nhánh** | `feat/p1-05-preprocess` (chưa commit) |
| **Ngày** | 2026-08-20 |
| **Sản phẩm** | `scripts/preprocess.py` (434 dòng) · `tests/test_preprocess.py` (864 dòng) · mẻ thật `data/processed/lfw_original/` (200 ảnh) |
| **Phán quyết** | 🔴 **TRẢ LẠI** — 0 lỗi 🔴 CHẶN-A, 0 lỗi 🔴 CHẶN-B, **3 lỗi 🟡 CẦN SỬA**, 6 góp ý 🔵 |

> **Ghi nhận trước**: ràng buộc quan trọng nhất của mã việc này (§3 — phân biệt hai loại lỗi)
> **đã cài đặt đúng và đã được bộ test bảo vệ có hiệu lực**. Xem §1 và §3 bên dưới.
> Ba lỗi 🟡 đều nhỏ, khu trú, sửa ước chừng 15–20 dòng, không đụng tới kiến trúc.

---

## 1. ƯU TIÊN SỐ MỘT — phân biệt hai loại lỗi: **ĐẠT**

### 1.1. Quét AST toàn bộ `ExceptHandler`

Không dùng `grep`, quét bằng `ast.walk` để bắt cả `except:` trần, `except BaseException`,
và `except (A, B)` có gộp lớp cha:

| Dòng | Bắt gì | Nằm ở đâu | Đúng ý đồ? |
|---|---|---|---|
| 178 | `except ValueError` | `xu_ly_mot_anh` — bọc `detector.detect` | ✅ |
| 201 | `except ValueError` | `xu_ly_mot_anh` — bọc `kiem_hinh_hoc_diem_moc` | ✅ |
| 209 | `except ValueError` | `xu_ly_mot_anh` — bọc `can_chinh` | ✅ |
| 321 | `except LoiCauHinh` | `main` — nạp cấu hình | ✅ |
| 328 | `except LoiCauHinh` | `main` — liệt kê ảnh | ✅ |
| 348 | `except LoiMoHinh` | `main` — khởi tạo detector | ✅ |
| 352 | `except LoiCauHinh` | `main` — khởi tạo detector | ✅ |
| 412 | `except LoiCauHinh` | `main` — **bọc cả vòng lặp mẻ** | ✅ |

**Không có** `except:` trần, **không có** `except BaseException`, **không có** tuple gộp lớp cha,
**không có** `except Exception`. Tám handler, tất cả đều nêu đích danh lớp ngoại lệ hẹp nhất.

Đối chiếu ngược: `align.py` và `yolo_face.py` chỉ ném `ValueError` cho lỗi **dữ liệu một ảnh**
và `LoiCauHinh`/`LoiMoHinh` cho lỗi **cấu hình/mô hình**. `detect()` không bao giờ ném `LoiMoHinh`
(chỉ `__init__` ném, và đã bắt ở dòng 348). Nên vòng lặp mẻ chỉ cần bắt `LoiCauHinh` là đủ phủ.

### 1.2. ĐB1 — chạy thật, **dòng 37 ĐỎ**

Chạy hai biến thể để chắc chắn không phải ăn may:

| Phép | Thay đổi | Ca đỏ | Kết luận |
|---|---|---|---|
| ĐB1 | cả ba `except ValueError` → `except Exception` | **37**, 23 | ✅ dòng 37 đỏ |
| ĐB1b | **chỉ** chỗ bọc `can_chinh` (dòng 209) | **37**, 23 | ✅ dòng 37 đỏ |

`sha256` sau khôi phục khớp bản gốc ở cả hai lần.

Ca `test_dong37` được dựng đúng ý đồ: cấu hình **đúng cú pháp YAML nhưng thiếu `output_size`** —
lỗi chỉ lộ ra khi `can_chinh()` thực sự chạy cho ảnh đầu tiên, tức là **bên trong** vòng lặp mẻ.
Đây khác hẳn dòng 36 (lỗi cú pháp, lộ ngay lúc `nap_cau_hinh`). Ba assert của nó:

```python
assert ma == 1
assert not (ra / "manifest.csv").exists()
assert not ra.exists() or list(ra.iterdir()) == []
```

đúng ba điều đặc tả đòi: **dừng ngay · thư mục ra rỗng · không có manifest**.

### 1.3. Dựng cấu hình hỏng thật, chạy `main()` trên thư mục 30 ảnh LFW thật

Không dùng test, dựng **12 cấu hình hỏng** khác nhau rồi gọi thẳng `main()`:

| Cấu hình hỏng | Mã trả về | Có manifest? | Số ảnh ghi ra |
|---|---|---|---|
| thiếu `output_size` | `1` | không | 0 |
| thiếu `reference_landmarks` | `1` | không | 0 |
| `output_size: "112x112"` | `1` | không | 0 |
| `reference_landmarks` chỉ 4 điểm | `1` | không | 0 |
| `interpolation: khong_ton_tai` | `1` | không | 0 |
| thiếu `loc_chat_luong.min_bbox_px` | `1` | không | 0 |
| thiếu `loc_chat_luong.min_ti_le_lech_mui` | `1` | không | 0 |
| thiếu cả khối `loc_chat_luong` | `1` | không | 0 |
| `border_value: [0, 0]` | `1` | không | 0 |
| `min_bbox_px: "bon_muoi"` | **ngoại lệ lọt** | không | 0 |
| `min_confidence: null` | **ngoại lệ lọt** | không | 0 |
| `min_ti_le_lech_mui: "0.15"` | **ngoại lệ lọt** | không | 0 |

**9/12 đúng hoàn toàn.** 3 ca cuối vẫn **dừng mẻ ngay, thư mục ra rỗng, không có manifest** —
tức là **tính chất sống còn "không trôi im lặng" vẫn được giữ** — nhưng `main()` **ném ra ngoài**
thay vì trả `1`. Đây là 🟡 CẦN SỬA-1 bên dưới, không phải lỗi bắt gộp.

### 1.4. Kết luận ưu tiên số một

**Không có dấu vết bắt gộp nào.** Việc phân biệt hai loại lỗi được cài đặt đúng, và — quan trọng
hơn — **được bộ test bảo vệ có hiệu lực**, chứng minh bằng ĐB1/ĐB1b chứ không bằng việc đọc code.
Công sức ba vòng review của `P1-04` không bị xoá.

---

## 2. ƯU TIÊN SỐ HAI — bộ lọc điểm mốc: **ĐẠT, đủ cả năm điều kiện**

### 2.1. Đọc cài đặt

`scripts/preprocess.py:121-136` — bốn bất biến thứ tự (dòng 121, 123, 125, 127) **cộng** điều kiện
thứ năm (dòng 130-136). Công thức tỉ lệ lệch mũi khớp nguyên văn §9.2b đặc tả:

```python
khoang_cach_vuong_goc = (
    abs(vecto_hai_mat[0] * (mui[1] - mat_trai[1]) - vecto_hai_mat[1] * (mui[0] - mat_trai[0]))
    / do_dai_hai_mat
)
ti_le_lech_mui = khoang_cach_vuong_goc / do_dai_hai_mat
```

Mẫu số `do_dai_hai_mat` được kiểm `== 0.0` **trước** cả bốn bất biến (dòng 118-119) → hai mắt trùng
nhau luôn ném `ValueError`, không bao giờ chia cho 0. Đúng dòng 13d.

### 2.2. Tự kiểm công thức bằng số

| Bộ điểm | Tỉ lệ lệch mũi đo được | Đặc tả nói | Khớp |
|---|---|---|---|
| `MAT_CHUAN` | 0,5715 | 0,5715 | ✅ |
| `TI_LE_020` | 0,2000 | 0,2000 | ✅ |
| `THANG_HANG` | 0,0000 | 0,0000 | ✅ |

`TI_LE_020` thoả cả bốn bất biến thứ tự và cho tỉ số đúng 0,2000 → dùng được làm cặp đối chứng
ngưỡng như đặc tả thiết kế.

### 2.3. ĐB3b và ĐB7 — chạy thật

| Phép | Ca đỏ | Đặc tả đòi | Kết luận |
|---|---|---|---|
| **ĐB3b** — bỏ **riêng** điều kiện thứ năm | **13**, **13c**, 19 | 13, 13c | ✅ đỏ đủ, dòng 19 đỏ thêm là hợp lý (dòng 19 dựa vào chính điều kiện 5) |
| **ĐB7** — bộ lọc luôn `True` trừ khi 5 điểm trùng nhau hoàn toàn | 09, 10, 11, 12, **13**, 13c, 19 | 13 | ✅ đỏ đủ |
| **ĐB3** — bỏ **riêng** bất biến 2 | **10** — và **KHÔNG** đỏ dòng 13 | 10, không đỏ 13 | ✅ đúng y hệt |
| **ĐB2** — bỏ hẳn `kiem_hinh_hoc_diem_moc` | **19** | 19 | ✅ |

ĐB3 là phép tinh tế nhất và nó cho kết quả **chính xác như đặc tả tiên đoán**: bỏ bất biến 2 làm
đỏ dòng 10 nhưng dòng 13 vẫn xanh, chứng minh dòng 13 thật sự bị bắt bởi **điều kiện thứ năm**
chứ không phải vô tình bị bắt bởi một bất biến thứ tự nào đó.

ĐB7 — bản sai *tự nhất quán* — cũng bị bắt. Lớp bảo vệ duy nhất trước `data/processed/` là thật.

---

## 3. Kết quả kiểm máy

### 3.1. Trên host (Windows, Python 3.12)

| Lệnh | Kết quả |
|---|---|
| `black --line-length 100 --check scripts/preprocess.py tests/test_preprocess.py` | **sạch** ✅ |
| `ruff check scripts/preprocess.py tests/test_preprocess.py` | **All checks passed** ✅ |
| `python -m pytest tests/test_preprocess.py -v` | **47 passed** ✅ |
| `python -m pytest -q` (toàn repo) | **337 passed** ✅ — không hồi quy mã việc cũ |
| `git status --short --untracked-files=all` | đúng **2** tệp mã nguồn mới ✅ |

`git status` cho đúng `scripts/preprocess.py` + `tests/test_preprocess.py`, cộng 3 tệp `.docx` trong
`docs/bao-cao-tuan/` của sinh viên (bỏ qua theo §10 đặc tả). `git diff --stat` **rỗng** — không sửa
tệp nào đã theo dõi. Không có tệp `.jpg/.png/.npy/.onnx/.env/.db` nào lọt vào git.
**Danh sách trắng §2 đặc tả: tuân thủ tuyệt đối.**

### 3.2. Trong container ARM64

Ảnh dựng lại từ cây làm việc hiện tại (`docker build -f deploy/Dockerfile.arm64`), **không** dùng
cờ `--platform` khi `docker run`. Môi trường xác nhận đúng như §11 đặc tả mô tả:

```
aarch64 · Python 3.11.16
/app/models /app/data /app/docs : No such file or directory
git : KHÔNG CÓ
ultralytics KHÔNG CÓ · torch KHÔNG CÓ · onnx KHÔNG CÓ
cv2 CÓ · numpy CÓ · onnxruntime CÓ · yaml CÓ
```

| Lệnh | Kết quả |
|---|---|
| `black --check` | **sạch** ✅ |
| `ruff check` | 2 lỗi `EXE002` ⚠️ — **không phải lỗi của mã việc này**, xem 🔵 GÓP Ý-4 |
| `pytest tests/test_preprocess.py -v` | **47 passed** — **0 error, 0 failed, 0 skipped** ✅ |

Đây là điểm mạnh đáng ghi nhận: bộ test **không cần một `pytest.skip` nào** vì nó vốn không chạm
tới `models/`, `data/`, `docs/`, `.git/`. Detector thật chỉ được dùng ở dòng 35 và 36, và cả hai
đều thất bại **trước** khi nạp ONNX (không tìm thấy tệp mô hình → `LoiMoHinh`), nên chạy được
trong container không có `models/`. Bài học `P2-01` (10 ca hỏng vì thiếu chốt skip) đã được xử lý
theo cách tốt hơn cả yêu cầu: **thiết kế để không cần skip**, thay vì vá bằng skip.

### 3.3. Bốn lệnh `grep` §10

| Lệnh | Kết quả |
|---|---|
| `grep -n "except Exception" scripts/preprocess.py` | **rỗng** ✅ (đã kiểm chéo bằng AST, §1.1) |
| `grep -nE "\b(112\|40\|0\.7\|0\.15)\b" scripts/preprocess.py` | **rỗng** ✅ — bốn tham số đều đọc từ config |
| `grep -rn "ultralytics\|import torch" scripts/preprocess.py` | **rỗng** ✅ |
| `grep -n "print(" scripts/preprocess.py` | 18 dòng — **giải trình đầy đủ** bên dưới |

Giải trình 18 dòng `print()`, tất cả nằm trong `main()` (điểm vào CLI, không phải `src/`):

- **312, 323, 330, 350, 354, 414** — sáu thông báo lỗi ra màn hình cho người chạy lệnh, **mỗi dòng
  đều đi kèm một `logger.error(...)` tương ứng** (311, 322, 329, 349, 353, 413). Không thay thế
  logging, mà bổ sung cho nó. Hợp lệ.
- **337–343** — bảng kế hoạch `--dry-run`, đúng yêu cầu §5 "chỉ in kế hoạch".
- **421–428** — bảng tổng kết, đúng §8. Đây là mục đích được cho phép tường minh.

Không có `print()` nào trong `src/`. **Không vi phạm CA-2/R23.**

### 3.4. Quét mẫu vi phạm — rubric §2

| Vi phạm | Kết quả |
|---|---|
| `except:` trần / nuốt lỗi | rỗng ✅ (AST xác nhận) |
| Log dùng f-string | rỗng ✅ — cả 11 lời gọi `logger` đều dùng lazy `%s`/`%d` |
| Số magic float trong so sánh (`[<>]=?\s*0\.\d`) | rỗng ✅ |
| Đường dẫn tuyệt đối máy cá nhân | rỗng ✅ |
| Secret trong code | rỗng ✅ |
| Test giả (`assert True`, `pass` trần) | rỗng ✅ |
| Nạp model trong vòng lặp | `YoloFaceDetector(...)` chỉ ở **dòng 347**, vòng lặp bắt đầu **dòng 361** → **ngoài vòng lặp** ✅ |
| Đo hiệu năng (ngoài phạm vi §12) | không có `time`/`perf_counter` ✅ |
| Số liệu bịa trong docstring | rỗng ✅ |

---

## 4. Kết quả tám phép đột biến §10 (+ 4 phép bổ sung)

`sha256` gốc trước khi động vào:
`bca1d4ef3a835fd3c772214621a9b57ac56f612bd1d4541ba93d414d97039b95`

Mỗi phép: sửa → chạy → ghi ca đỏ → khôi phục → đối chiếu `sha256`. Đọc/ghi bằng `newline=""`.

| # | Phép | Ca đỏ thật | Đặc tả đòi | Kết luận |
|---|---|---|---|---|
| ĐB1 | `except ValueError` → `except Exception` | **37**, 23 | 37 | ✅ |
| ĐB1b | *(bổ sung)* chỉ chỗ bọc `can_chinh` | **37**, 23 | — | ✅ |
| ĐB2 | bỏ `kiem_hinh_hoc_diem_moc` | **19** | 19 | ✅ |
| ĐB3 | bỏ riêng bất biến 2 | **10** (13 vẫn xanh) | 10, không đỏ 13 | ✅ |
| ĐB3b | bỏ riêng điều kiện thứ năm | **13**, **13c**, 19 | 13, 13c | ✅ |
| ĐB4 | ghi đuôi `.jpg` | **30**, 29, 40, 41 | 30 | ✅ |
| ĐB5 | bỏ ghi dòng manifest cho ảnh bỏ qua | **26**, 43 | 26 | ✅ |
| ĐB6 | lấy khuôn mặt **cuối** danh sách | **22** | 22 | ✅ |
| ĐB7 | bộ lọc luôn `True` trừ khi 5 điểm trùng nhau | **13**, 09–12, 13c, 19 | 13 | ✅ |
| BS1 | *(bổ sung)* đảo thứ tự lọc: conf trước bbox | **21** | — | ✅ thứ tự §7 được bảo vệ |
| BS2 | *(bổ sung)* `file_ra` ghi `"None"` thay vì `""` | **KHÔNG CA NÀO ĐỎ** | — | ❌ **lỗ hổng — xem CẦN SỬA-2** |
| BS3 | *(bổ sung)* bỏ `as_posix()`, dùng `str()` | **28**, 29 | — | ✅ |

`sha256` sau toàn bộ 12 phép: **khớp bản gốc**. Không để lại thay đổi nào trong mã sản phẩm.

**Tám phép bắt buộc: 8/8 ĐẠT.** Phép bổ sung BS2 tìm ra một ca test không chạm tới code nó tuyên bố
bảo vệ — đúng kiểu lỗ hổng mà rubric §2b sinh ra để bắt.

---

## 5. ƯU TIÊN SỐ BA — kết luận về hai ảnh `mat_qua_nho`: **phán quyết ĐÚNG**

### 5.1. Hai ảnh nào

| `file_vao` | `n_faces` | `conf` | `bbox_w` | `bbox_h` |
|---|---|---|---|---|
| `Dalai_Lama/Dalai_Lama_0001.jpg` | 2 | 0,8468 | **37** | 98 |
| `Mary-Kate_Olsen/Mary-Kate_Olsen_0001.jpg` | 2 | 0,8436 | **33** | 96 |

Tỉ lệ `w/h` ≈ 0,38 và 0,34 — lệch hẳn so với trung vị 0,73 của 198 ảnh còn lại. Đáng ngờ, nên đã
chạy detector thật trên hai ảnh này và xem tận mắt hai ảnh gốc.

### 5.2. Chạy detector thật

```
Dalai_Lama_0001.jpg  (250, 250, 3)
  [0] conf=0.8468  x1=0    y1=32  x2=37   y2=130   w=37  h=98
  [1] conf=0.8252  x1=83   y1=34  x2=188  y2=191   w=105 h=157
Mary-Kate_Olsen_0001.jpg  (250, 250, 3)
  [0] conf=0.8436  x1=217  y1=0   x2=250  y2=96    w=33  h=96
  [1] conf=0.8403  x1=79   y1=67  x2=170  y2=184   w=91  h=117
```

Xem ảnh gốc: **cả hai đều có người thứ hai bị khung ảnh cắt cụt ở mép** — một người ở mép trái ảnh
Dalai Lama, một phụ nữ ở mép phải ảnh Mary-Kate Olsen. Khung bao của họ **hẹp vì bị cắt**, cao vì
chiều dọc còn nguyên. Đó chính là hai khung `[0]`.

### 5.3. Loại trừ ba giả thuyết cài đặt sai

| Giả thuyết | Bằng chứng bác bỏ |
|---|---|
| Đo `bbox` trên ảnh đã **letterbox** thay vì ảnh gốc | `x2 = 250` **đúng bằng chiều rộng ảnh gốc**, và `x1 = 0` chạm mép trái. Toạ độ nằm trong hệ ảnh gốc 250×250, không phải hệ 320×320 |
| Lấy **nhầm** khuôn mặt trong danh sách | ĐB6 chứng minh code lấy `khuon_mat[0]`; detector trả về đã sắp giảm dần theo `conf`; `conf[0]=0.8468 > conf[1]=0.8252` — đúng phần tử đầu |
| Ngưỡng `min_bbox_px` đọc sai | 37 < 40 và 33 < 40, đọc từ `configs/preprocess.yaml` (grep số hardcode rỗng) |

**Kết luận: đây là phán quyết ĐÚNG, không phải dấu hiệu cài đặt sai.** Cạnh nhỏ nhất của khung bao
có độ tin cậy cao nhất thật sự nhỏ hơn `min_bbox_px: 40`. Cài đặt làm đúng §7 đặc tả.

Tỉ lệ `khong_thay_mat` = **0,00 %** (0/200), hoàn toàn nhất quán với dữ kiện §4 đặc tả (60/60 ảnh
LFW phát hiện được). Không có dấu hiệu bất thường.

### 5.4. Nhưng phát hiện thêm một điều đáng lo — xem 🔵 GÓP Ý-1

Chính cơ chế "lấy khuôn mặt tin cậy cao nhất" đã khiến **5 ảnh khác bị ghi NHẦM NGƯỜI** vào
`data/processed/`. Chi tiết ở GÓP Ý-1. Đây là **khiếm khuyết của đặc tả §7**, không phải lỗi cài đặt.

---

## 6. Kiểm tệp đầu ra thật `data/processed/lfw_original/`

Đọc thật **toàn bộ 198 tệp** bằng `cv2.imread`, không tin manifest:

| Kiểm | Kết quả |
|---|---|
| Kích thước mọi ảnh `.png` | **198/198 đúng `(112, 112, 3)`** ✅ |
| Số tệp `.png` vs số dòng `ly_do == ok` | 198 = 198 ✅ |
| `file_ra` khai báo nhưng tệp không tồn tại | 0 ✅ |
| Tệp `.png` tồn tại nhưng không có trong manifest | 0 ✅ |
| Tệp lạ ngoài `.png` và `manifest.csv` | 0 ✅ |
| Cấu trúc thư mục con phản chiếu nguồn, tên giữ nguyên chỉ đổi đuôi | **198/198 khớp** ✅ |
| Manifest: số dòng | **200** ✅ |
| Manifest: số cột và thứ tự | 7 cột, đúng §8 ✅ |
| Manifest: đường dẫn dùng `/`, không có `\` | 0 dấu `\` ✅ |
| `file_ra` rỗng đúng ở 2 dòng bị bỏ qua | 2/2 ✅ |
| `file_vao` trỏ tới tệp nguồn có thật | 200/200 ✅ |

**Bảng tổng kết mẻ thật** (chạy lại và đối chiếu):

| Lý do | Số lượng | Tỉ lệ |
|---|---|---|
| `ok` | 198 | 99,00 % |
| `khong_doc_duoc_anh` | 0 | 0,00 % |
| `khong_thay_mat` | 0 | 0,00 % |
| `mat_qua_nho` | 2 | 1,00 % |
| `do_tin_cay_thap` | 0 | 0,00 % |
| `diem_moc_bat_thuong` | 0 | 0,00 % |

### 6.1. `--tiep-tuc` — kiểm thật, không qua test

Sao chép nguyên `data/processed/lfw_original/` ra thư mục tạm, chạy lại `main()` với `--tiep-tuc`
trên đúng 200 ảnh đó:

| Kiểm | Kết quả |
|---|---|
| Số tệp đổi `mtime` | **0 / 198** ✅ |
| Số tệp đổi nội dung (`sha256`) | **0 / 198** ✅ |
| Tệp sinh thêm ngoài dự kiến | 0 ✅ |
| Mã trả về | `0` ✅ |
| Cùng `--seed 42 --gioi-han 200` chọn đúng cùng 200 ảnh như manifest đã có | **True** ✅ |

`--tiep-tuc` **thật sự không ghi đè**, và việc lấy mẫu **tái lập được chính xác** (R15).

---

## 7. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §2 Danh sách trắng file | ✅ đúng 2 tệp, `git diff --stat` rỗng |
| §3 **Phân biệt hai loại lỗi** | ✅ **ĐẠT** (§1 biên bản) — trừ 3 ca sai kiểu ở CẦN SỬA-1 |
| §5 Giao diện dòng lệnh | ✅ đủ 9 cờ, mặc định khớp từng giá trị |
| §6 Giao diện hàm | ✅ 5 chữ ký khớp **từng ký tự**, kể cả `-> tuple[np.ndarray \| None, str, dict]` |
| §7 Sáu lý do + thứ tự kiểm | ✅ đúng sáu, không thêm bớt; thứ tự đúng (BS1 xác nhận) |
| §8 Đầu ra (ảnh, manifest, bảng tổng kết) | ✅ kiểm trên 198 tệp thật (§6 biên bản) |
| §9 Bảng tiêu chí (46 dòng) | ✅ **46/46 có mặt**, đủ `13b/13c/13d`, không trùng, dư 1 ca `15b` hợp lý — nhưng dòng 27 không chạm code (CẦN SỬA-2) |
| §10 Bốn lệnh máy + 4 grep + 8 đột biến | ✅ trên host và container; 8/8 đột biến đạt |
| §11 Ràng buộc kỹ thuật | ✅ không `ultralytics`/`torch`; `lay_logger`; `nap_cau_hinh`/`lay_gia_tri`; detector giả; container sạch |
| §12 Ngoài phạm vi | ✅ không chia tập, không lọc trùng, không domain adaptation, không embedding, không đo hiệu năng |
| R15 seed ghi vào output | ❌ **CẦN SỬA-3** |
| R16 không hardcode tham số | ✅ grep rỗng |
| R23 không `print()` trong `src/` | ✅ |

**Kiểm đếm ca test bằng AST**: 47 hàm `test_*`, ánh xạ 1–1 với 46 dòng bảng §9 (01–43 + 13b/13c/13d),
không thiếu dòng nào, không trùng dòng nào, dư đúng một ca `test_dong15b` (detect ném `ValueError`
→ trả lý do, không ném) — ca dư này **có ích và đúng tinh thần §3**, không phải ca thừa.

---

## 8. Lỗi phải sửa

### 🟡 CẦN SỬA-1 — Giá trị cấu hình **sai kiểu** làm ngoại lệ lọt ra ngoài `main()` thay vì trả `1`

**Vị trí**: `scripts/preprocess.py:136`, `scripts/preprocess.py:192`, `scripts/preprocess.py:195`
(gốc là bốn lời gọi `lay_gia_tri` ở `scripts/preprocess.py:171-174`)

```python
# 171-174 — đọc config, KHÔNG kiểm kiểu
min_bbox_px = lay_gia_tri(cfg_preprocess, "loc_chat_luong.min_bbox_px")
min_confidence = lay_gia_tri(cfg_preprocess, "loc_chat_luong.min_confidence")
bat_kiem_hinh_hoc = lay_gia_tri(cfg_preprocess, "loc_chat_luong.kiem_hinh_hoc_diem_moc")
min_ti_le_lech_mui = lay_gia_tri(cfg_preprocess, "loc_chat_luong.min_ti_le_lech_mui")
...
# 192
if min(mat.chieu_rong, mat.chieu_cao) < min_bbox_px:      # TypeError nếu là chuỗi
# 195
if mat.confidence < min_confidence:                        # TypeError nếu là None
# 136
return bool(ti_le_lech_mui >= min_ti_le_lech_mui)          # UFuncTypeError nếu là chuỗi
```

`lay_gia_tri` chỉ bảo đảm **khoá tồn tại**, không bảo đảm **kiểu**. Dựng thật ba cấu hình hỏng và
chạy `main()` trên 30 ảnh LFW thật:

| Cấu hình | Kết quả thật |
|---|---|
| `min_bbox_px: "bon_muoi"` | `TypeError: '<' not supported between instances of 'int' and 'str'` |
| `min_confidence: null` | `TypeError: '<' not supported between instances of 'float' and 'NoneType'` |
| `min_ti_le_lech_mui: "0.15"` | `numpy.UFuncTypeError: ufunc 'greater_equal' ...` |

**Vì sao**: `min_ti_le_lech_mui: "0.15"` — bỏ nhầm dấu nháy quanh một số trong YAML — là lỗi gõ
phổ biến nhất khi sửa file cấu hình. Khi đó người chạy mẻ nhận về một `UFuncTypeError` của numpy
giữa màn hình thay vì câu tiếng Việt "cấu hình hỏng ở khoá nào", và `main()` **không trả `1`** —
phá vỡ hợp đồng `main() -> int` ở §6 và tiêu chí dòng 36 "cấu hình hỏng → trả về `1`". Đáng chú ý:
`align.py` và `yolo_face.py` **đều đã kiểm kiểu** cho tham số của chúng và ném `LoiCauHinh`
(xem `align.py:143`, `yolo_face.py:137`) — chỉ bốn tham số của riêng `preprocess.py` là chưa.
Đây là chỗ duy nhất trong chuỗi phá vỡ quy ước mà `P1-04` đã dựng bằng 50 cấu hình hỏng.

*Giảm nhẹ*: mẻ **vẫn dừng ngay**, thư mục ra **vẫn rỗng**, **vẫn không có** manifest. Tính chất
sống còn "không trôi im lặng" không bị ảnh hưởng. Vì vậy đây là 🟡 chứ không phải 🔴.

**Sửa**: kiểm kiểu ngay sau khi đọc, ném `LoiCauHinh` — sẽ được `main():412` bắt và trả `1`:

```python
def _lay_so(cfg: dict, khoa: str) -> float:
    """Đọc một tham số số thực từ cấu hình, ném LoiCauHinh nếu sai kiểu."""
    gia_tri = lay_gia_tri(cfg, khoa)
    if isinstance(gia_tri, bool) or not isinstance(gia_tri, (int, float)):
        raise LoiCauHinh(f"Cấu hình '{khoa}' phải là số, nhận {gia_tri!r}")
    return float(gia_tri)
```

rồi dùng `_lay_so(...)` cho `min_bbox_px`, `min_confidence`, `min_ti_le_lech_mui`; với
`kiem_hinh_hoc_diem_moc` kiểm `isinstance(..., bool)`.
Bổ sung một ca test (đề xuất `test_dong36b`) dựng cấu hình `min_ti_le_lech_mui: "0.15"` và assert
`main(...) == 1` — hiện chưa ca nào phủ nhánh này.

---

### 🟡 CẦN SỬA-2 — `test_dong27` không chạm tới đoạn code nó tuyên bố bảo vệ

**Vị trí**: `tests/test_preprocess.py:515-520`

```python
def test_dong27_file_ra_rong_khong_phai_none(tmp_path):
    pp.ghi_manifest(tmp_path / "manifest.csv", [_ban_ghi_bo_qua("c.jpg")])
    ...
    assert rows[0]["file_ra"] == ""
    assert rows[0]["file_ra"] != "None"
```

`_ban_ghi_bo_qua()` (dòng 194-203) **đã tự chứa sẵn** `"file_ra": ""`. Ca test này chỉ chứng minh
`csv.writer` ghi lại được một chuỗi rỗng — điều luôn đúng. Nó **không** chạy qua
`scripts/preprocess.py:388`, tức là chỗ `main()` thật sự **quyết định** đặt gì vào `file_ra` khi
một ảnh bị bỏ qua.

**Bằng chứng bằng đột biến (BS2)**: sửa `scripts/preprocess.py:388` từ `"file_ra": ""` thành
`"file_ra": "None"` → **cả 47 ca vẫn XANH**. Đúng ô mà rubric §2b gọi là *"Vẫn xanh → chỗ đó
không ca test nào chạm tới — ghi lỗi, dù bảng đối chiếu báo 'có test'"*.

**Vì sao**: yêu cầu dòng 27 của đặc tả nói về **hành vi của mẻ với ảnh bị bỏ qua**, và cạm bẫy nó
nhắm tới là `str(None)` → `"None"` rò ra từ `main()`. Ở dạng hiện tại, nếu ai đó sau này refactor
khối ghi bản ghi ở dòng 385-395 và vô tình để `None` lọt vào, bộ test sẽ không báo gì, và cột
`file_ra` của manifest 9 164 dòng sẽ chứa chuỗi `"None"` — thứ mà bước 1.10/1.11 sẽ đọc như một
đường dẫn hợp lệ. Mã hiện tại **đang đúng** (mẻ thật cho 2 ô rỗng thật sự), nhưng không được canh giữ.

**Sửa**: cho dòng 27 đi qua `main()` như dòng 26/28/29/30 đã làm — dùng lại fixture kiểu
`_main_cau_truc_con`, với detector giả trả `[]` để ảnh bị bỏ qua, rồi assert trên manifest sinh ra:

```python
assert rows[0]["ly_do"] == "khong_thay_mat"
assert rows[0]["file_ra"] == ""
assert rows[0]["file_ra"] != "None"
```

Giữ nguyên ca hiện tại cũng được (nó vẫn kiểm `ghi_manifest` ở mức đơn vị), nhưng phải có thêm ca
đi qua `main()`. Nghiệm thu: sau khi sửa, phép đột biến BS2 phải làm **dòng 27 đỏ**.

---

### 🟡 CẦN SỬA-3 — Seed không được ghi vào bất kỳ đầu ra nào (vi phạm R15)

**Vị trí**: `scripts/preprocess.py:421-428` (khối bảng tổng kết)

```python
print("\n### BẢNG TỔNG KẾT TIỀN XỬ LÝ")
print("| Lý do | Số lượng | Tỉ lệ |")
...
print(f"\nTổng số ảnh xét: `{tong}` — manifest: `{duong_dan_manifest}`\n")
```

`--seed` và `--gioi-han` chỉ được in trong nhánh `--dry-run` (dòng 340-343). Ở lần chạy **thật**,
không đầu ra nào — không bảng tổng kết, không manifest — ghi lại seed hay giới hạn đã dùng.

**Vì sao**: `data/processed/lfw_original/manifest.csv` hiện có 200 dòng trong khi nguồn có 9 164 ảnh.
Nhìn vào tệp đó **không có cách nào biết** đây là mẻ thử lấy mẫu ngẫu nhiên với `--gioi-han 200
--seed 42` hay một mẻ đầy đủ trên một thư mục nguồn nhỏ. Bước 1.7 (đo phân bố kích thước bbox) và
bước 1.13 (EDA) sẽ đọc chính manifest này; nếu ai đó — kể cả chính tác giả sau sáu tuần — tưởng nhầm
đó là mẻ đầy đủ thì con số thống kê đưa vào báo cáo sẽ sai mà không có dấu hiệu nào báo.
R15 tồn tại đúng để chặn tình huống này, và §5 đặc tả đã tự trích dẫn "(R15)" ngay ở dòng `--seed`.

**Sửa**: thêm hai dòng vào khối tổng kết (không đụng 7 cột manifest, vốn bị §8 chốt cứng):

```python
print(f"\nTổng số ảnh xét: `{tong}` — manifest: `{duong_dan_manifest}`")
print(f"Seed: `{args.seed}` — giới hạn: `{args.gioi_han or 'không giới hạn'}`\n")
```

Nếu người dùng muốn seed nằm trong tệp chứ không chỉ trên màn hình, đó là thay đổi §8 đặc tả và
phải do `spec-writer` quyết định — xem GÓP Ý-2.

---

## 9. 🔵 Góp ý (không chặn — người dùng quyết định)

### GÓP Ý-1 ⚠️ — Luật "lấy khuôn mặt tin cậy cao nhất" (§7 đặc tả) đã ghi **nhầm người** vào `data/processed/`

**Đây là khiếm khuyết của đặc tả, không phải lỗi cài đặt** — `scripts/preprocess.py:186`
(`mat = khuon_mat[0]`) làm đúng nguyên văn §7. Nêu ở đây vì hậu quả chạm tới tính trung thực dữ liệu.

Chạy detector thật trên 49 ảnh có `n_faces > 1` trong mẻ 200: **5 ảnh đã được ghi ra
`data/processed/` với khuôn mặt của người ở hậu cảnh**, trong khi khuôn mặt chính (lớn hơn > 1,5 lần)
bị bỏ. Cả 5 khung được chọn đều **chạm mép ảnh**, tức là mặt bị khung hình cắt cụt:

| Tệp | Khung được chọn | Khung lớn nhất (bị bỏ) |
|---|---|---|
| `Angela_Bassett/Angela_Bassett_0006.jpg` | 61×127, conf 0,858 | 101×123, conf 0,837 |
| `George_W_Bush/George_W_Bush_0060.jpg` | 45×76, conf 0,838 | 92×120, conf 0,831 |
| `Gerry_Adams/Gerry_Adams_0005.jpg` | 68×133, conf 0,864 | 104×141, conf 0,828 |
| `Marc_Grossman/Marc_Grossman_0001.jpg` | 57×98, conf 0,868 | 86×115, conf 0,867 |
| `Shaul_Mofaz/Shaul_Mofaz_0002.jpg` | 60×121, conf 0,860 | 100×144, conf 0,849 |

Chênh lệch `conf` giữa hai khung chỉ 0,001–0,036 — quá nhỏ để làm tiêu chí chọn, trong khi chênh lệch
diện tích tới 2–3 lần. Tỉ lệ **5/198 ≈ 2,5 %**; ngoại suy lên 9 164 ảnh là khoảng **230 ảnh sai nhãn
danh tính**.

Với vai trò impostor LFW thì một người lạ vẫn là người lạ, nên `FAR_lfw` chưa hỏng ngay. Nhưng:
(1) số danh tính thực tế không còn đúng như khai báo — ảnh hưởng lập luận "≥ 100 danh tính" ở §1
`CLAUDE.md`; (2) bước 1.7 đo phân bố kích thước bbox sẽ lẫn các khung bị cắt cụt, làm lệch chính
tham số dùng để domain-adapt LFW ở bước 1.8; (3) nếu áp dụng nguyên quy trình này cho **gallery
2–3 người nhà** như §1 đặc tả yêu cầu ("áp dụng đồng nhất cho cả bốn nguồn"), thì embedding của một
danh tính sẽ bị trộn mặt người khác — đúng kịch bản mà `configs/preprocess.yaml` dòng 38-42 cảnh báo.

**Đề xuất cho `spec-writer`** (chi phí ~5 dòng code, lợi ích: bỏ hẳn một nguồn nhiễm dữ liệu):
sửa §7 để chọn khuôn mặt theo **diện tích lớn nhất** thay vì `conf` cao nhất — hoặc theo `conf`
nhưng chỉ trong số các khung **không chạm mép ảnh**. Với ảnh chân dung một chủ thể (đúng định vị
đề tài, R11 cấm nhận diện đám đông), "mặt lớn nhất" là tiêu chí đúng hơn hẳn. Nếu chốt đổi thì
**phải chạy lại mẻ** và bỏ `data/processed/lfw_original/` hiện có.

### GÓP Ý-2 — `--tiep-tuc` làm rỗng bốn cột đo của manifest

Kiểm thật: chạy lại mẻ 200 ảnh với `--tiep-tuc`, manifest kết quả có **198/198 dòng `ok` với
`n_faces`, `conf`, `bbox_w`, `bbox_h` đều rỗng** (do `scripts/preprocess.py:366-379` ghi bản ghi
rút gọn cho ảnh đã có ở đích).

Cài đặt **đúng đặc tả** — §8 chỉ đòi "mỗi ảnh đúng một dòng", không quy định giá trị bốn cột đo
trong trường hợp này. Nhưng hậu quả: một mẻ LFW 9 164 ảnh (≈ 7 phút) bị đứt giữa chừng rồi chạy
tiếp sẽ cho manifest **trống cột `bbox_w`/`bbox_h` ở phần đã xử lý trước** — mà đó chính là dữ liệu
đầu vào của bước 1.7 "phân bố kích thước bbox (px)". Phân bố sẽ được tính trên một tập con thiên
lệch, im lặng.

Đề xuất: hoặc §5 ghi rõ "manifest của mẻ chạy tiếp không dùng được cho bước 1.7", hoặc `--tiep-tuc`
đọc lại manifest cũ để hợp nhất bốn cột đo. Người dùng quyết định.

### GÓP Ý-3 — `test_dong13b` kiểm hàm trợ giúp của test, không kiểm cài đặt

`tests/test_preprocess.py:316-317` gọi `_ti_le_lech_mui(MAT_CHUAN)` — một bản cài lại công thức
**bên trong tệp test** (dòng 173-179) — chứ không gọi `pp.kiem_hinh_hoc_diem_moc`. Nó chứng minh
công thức §9.2b cho ra 0,5715, nhưng không chứng minh **`preprocess.py` dùng đúng công thức đó**.
Đây là lý do ĐB3b không làm đỏ dòng 13b.

Không chặn: dòng 13c **có** kiểm ngưỡng đi qua cài đặt thật và ĐB3b làm nó đỏ, nên điều kiện thứ năm
vẫn được canh giữ. Muốn chặt hơn thì tách tỉ lệ lệch mũi thành một hàm public nhỏ trong
`preprocess.py` rồi cho 13b gọi thẳng vào đó — nhưng việc này đổi §6 đặc tả, phải qua `spec-writer`.

### GÓP Ý-4 — `ruff` báo `EXE002` trong container: vấn đề môi trường, **không phải của mã việc này**

`ruff check` trong container báo `EXE002 The file is executable but no shebang is present` cho
`scripts/preprocess.py` và `tests/test_preprocess.py`. Đã kiểm chéo: chạy `ruff check src tests scripts`
trong container cho **31 lỗi EXE002 trên toàn repo**, gồm cả các tệp đã gộp từ lâu
(`tests/test_align.py`, `scripts/benchmark_detect.py`, `scripts/collect_faces.py`...). Nguyên nhân:
`COPY . .` từ máy Windows đặt mọi tệp thành mode `0755` trong ảnh Linux.

Trên host, `ruff check` **sạch tuyệt đối**. Đây là nhiễu công cụ, không phải khiếm khuyết mã nguồn,
và không thuộc trách nhiệm `P1-05`. Đề xuất xử lý bằng một commit riêng `chore(quy-trinh)`:
thêm `COPY --chmod=644 . .` trong `deploy/Dockerfile.arm64`, hoặc thêm `EXE002` vào `lint.ignore`
của `pyproject.toml`. Nếu không xử lý, mọi mã việc sau đều sẽ vấp lại đúng điểm này.

### GÓP Ý-5 — `liet_ke_anh("")` quét toàn bộ thư mục làm việc

`Path("")` bằng `Path(".")`, nên `--vao ""` không bị `main():310` chặn (chỉ kiểm `is None`) và
`liet_ke_anh` sẽ `rglob` toàn bộ repo — thử nghiệm cho thấy nó nhặt cả `data/.cache/lfw/...`.
Hậu quả là một mẻ khổng lồ ngoài ý muốn chứ không phải hỏng dữ liệu. Sửa rẻ: đổi
`if args.vao is None or args.ra is None` thành `if not args.vao or not args.ra`.

### GÓP Ý-6 — `ghi_manifest` ở `main():418` nằm ngoài khối `try`

`scripts/preprocess.py:418` gọi `ghi_manifest` sau khi khối `try/except LoiCauHinh` (360-415) đã
đóng. Nếu `ghi_manifest` ném `LoiCauHinh` (bản ghi thiếu khoá) thì ngoại lệ lọt ra khỏi `main()`
thay vì trả `1`. Hiện **không thể xảy ra** vì cả ba nhánh dựng bản ghi (368, 386, 402) đều ghi đủ
bảy khoá — nên chỉ là góp ý phòng thủ, gộp được vào lần sửa CẦN SỬA-1.

*(Ghi nhận điểm tốt: `ghi_manifest` kiểm đủ khoá cho **toàn bộ** danh sách **trước** khi mở tệp
(dòng 229-232). Kiểm thật với `[ok, ok, {}, ok]` → ném `LoiCauHinh` và **không tạo tệp dở dang**.
Đúng như docstring của chính nó cam kết.)*

---

## 10. Hai điểm sống còn — soi riêng

**Trung thực số liệu**: ✅ không có giá trị mặc định giả, không có số ví dụ trong docstring trông
như kết quả đo, không có test dùng số bịa. Ba bộ điểm mốc dựng sẵn được chép nguyên từ §9.2b đặc tả
và **đã tự kiểm lại bằng số** (0,5715 / 0,2000 / 0,0000 — khớp cả ba). Bảng tổng kết in ra là số
đếm thật, không phải số cứng. Manifest của mẻ thật khớp 100 % với 198 tệp đọc lại từ đĩa.
Hai điểm cần người dùng lưu tâm khi dùng số này về sau: GÓP Ý-1 (2,5 % ảnh sai nhãn) và
CẦN SỬA-3 (không truy được seed của mẻ).

**An toàn phần cứng**: không áp dụng — mã việc này không chạm GPIO/relay/camera.
Về "fail-safe" ở nghĩa dữ liệu: khi cấu hình hỏng, mẻ dừng ngay và **không để lại tệp nào**
(kiểm thật 12/12 cấu hình hỏng đều cho thư mục ra rỗng, không manifest). Trạng thái an toàn được giữ.

---

## 11. Việc tiếp theo

Ba lỗi 🟡 đều khu trú, tổng cộng khoảng 15–20 dòng, không đụng kiến trúc. Giao lại cho người cài đặt:

> Sửa theo `docs/review/P1-05-preprocess.review.md` §8, đúng ba mục CẦN SỬA-1, CẦN SỬA-2, CẦN SỬA-3.
> Chỉ được sửa `scripts/preprocess.py` và `tests/test_preprocess.py`.
> Nghiệm thu bổ sung: (a) cấu hình `min_ti_le_lech_mui: "0.15"` phải làm `main()` trả `1`;
> (b) phép đột biến đổi `"file_ra": ""` thành `"file_ra": "None"` ở `main()` phải làm **dòng 27 đỏ**;
> (c) bảng tổng kết in ra seed và giới hạn.
> Chạy lại đủ bốn lệnh §10 trên host **và** container ARM64, kèm tám phép đột biến. **Không commit.**

**Không cần chạy lại mẻ thật** cho ba lỗi này — cả ba đều không đổi kết quả xử lý của 200 ảnh hiện có.
Nhưng **nếu người dùng chấp nhận GÓP Ý-1** (đổi luật chọn khuôn mặt) thì phải xoá
`data/processed/lfw_original/` và chạy lại, vì 5 ảnh trong đó đang mang mặt của người khác.

Khi đã ĐẠT, commit theo R29:

```
feat(scripts): thêm mẻ tiền xử lý ảnh khuôn mặt về 112x112
```

---
---

# Review P1-05-preprocess — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-05-preprocess.md` (cập nhật 20/08: §7 đổi luật chọn, §9 thêm dòng 22/22b/22c, §10 thêm ĐB6b) |
| **Nhánh** | `feat/p1-05-preprocess` (chưa commit) |
| **Ngày** | 2026-08-20 |
| **Phán quyết** | ✅ **ĐẠT** — 0 lỗi 🔴, 0 lỗi 🟡, 4 góp ý 🔵 |

Cả bốn mục vòng 1 đã sửa xong và **được kiểm bằng đột biến**, không chỉ bằng "test xanh".
`sha256` mã sản phẩm sau toàn bộ 12 phép đột biến khớp bản gốc — không để lại thay đổi nào.

---

## 1. ĐB6b — phép quyết định: **ĐẠT**

Luật chọn mới ở `scripts/preprocess.py:233`:

```python
mat = max(khuon_mat, key=lambda m: (m.dien_tich, m.confidence))
```

Đúng §7 mới: diện tích lớn nhất, bằng nhau thì độ tin cậy cao hơn. Kèm chú thích 5 dòng (228-232)
ghi lại **vì sao** luật cũ sai và cảnh báo "danh sách chỉ sắp theo conf — KHÔNG được giả định đã
sắp theo diện tích". Đây là loại chú thích ngăn lỗi tái phát khi người khác đọc lại.

Chạy bốn phép quanh luật chọn để phân biệt được từng nhánh:

| Phép | Thay bằng | Ca đỏ thật | Đặc tả đòi | Kết luận |
|---|---|---|---|---|
| **ĐB6b** | `max(..., key=lambda m: m.confidence)` — **khôi phục đúng luật sai cũ** | **22b**, 22 | 22b | ✅ **ĐẠT** |
| ĐB6 | `khuon_mat[-1]` | 22, 22c | 22 | ✅ |
| ĐB6c *(bổ sung)* | `khuon_mat[0]` — tương đương luật cũ vì `detect` sắp theo conf | **22b**, 22 | — | ✅ bắt được |
| ĐB6d *(bổ sung)* | bỏ tiêu chí phụ `conf` khi diện tích bằng nhau | **22c** | — | ✅ bắt được |

**ĐB6b làm đỏ dòng 22b — đúng ca chặn.** Dòng 22 đỏ kèm là **liên quan trực tiếp**, không phải đỏ
lan man: dòng 22 assert `bbox_w × bbox_h` khớp mặt **lớn nhất**, nên đổi luật chọn tất nhiên làm nó
đỏ. Không ca nào ngoài nhóm chọn khuôn mặt bị đỏ.

Ca `test_dong22b` (`tests/test_preprocess.py:424-437`) dựng **đúng tình huống thật** đo được ở vòng
1: mặt A `40×70` conf `0.870` đứng **trước** trong danh sách (đã sắp theo conf giảm dần), mặt B
`120×160` conf `0.850` đứng sau; assert `thong_tin["bbox_w"] == 120`. Chênh conf 0,020 nằm đúng
trong khoảng 0,001–0,036 đo được trên mẻ thật. Ca test không phải phỏng đoán — nó tái dựng số liệu thật.

Bốn phép này cho thấy ba cài đặt sai **khác nhau** đều bị bắt bởi **ba ca test khác nhau** (22, 22b,
22c), tức bảng §9 mới phân giải được lỗi chứ không chỉ báo có lỗi.

---

## 2. Năm ảnh từng ghi nhầm người — **ĐÃ SỬA THẬT, 7/7**

Chạy detector thật trên đúng năm ảnh vòng 1 tìm ra, đối chiếu với manifest mẻ mới:

| Tệp | Vòng 1 chọn (SAI) | Vòng 2 chọn | Là mặt lớn nhất? | Chạm mép? |
|---|---|---|---|---|
| `Angela_Bassett/Angela_Bassett_0006.jpg` | 61×127 conf 0,858 | **101×123** conf 0,837 | ✅ | không |
| `George_W_Bush/George_W_Bush_0060.jpg` | 45×76 conf 0,838 | **92×120** conf 0,831 | ✅ | không |
| `Gerry_Adams/Gerry_Adams_0005.jpg` | 68×133 conf 0,864 | **104×141** conf 0,828 | ✅ | không |
| `Marc_Grossman/Marc_Grossman_0001.jpg` | 57×98 conf 0,868 | **86×115** conf 0,867 | ✅ | không |
| `Shaul_Mofaz/Shaul_Mofaz_0002.jpg` | 60×121 conf 0,860 | **100×144** conf 0,849 | ✅ | không |

**Cả năm nay chọn đúng khuôn mặt chính**, không khung nào chạm mép ảnh nữa.

### 2.1. Hai ảnh trước bị `mat_qua_nho` — nay `ok` và **hợp lý**

| Tệp | Vòng 1 | Vòng 2 | Nhận xét |
|---|---|---|---|
| `Dalai_Lama/Dalai_Lama_0001.jpg` | 37×98 → `mat_qua_nho` | **105×157** conf 0,825 → `ok` | đúng khung `[1]` mà vòng 1 đã xác định là mặt chính |
| `Mary-Kate_Olsen/Mary-Kate_Olsen_0001.jpg` | 33×96 → `mat_qua_nho` | **91×117** conf 0,840 → `ok` | đúng khung `[1]` |

Hai ảnh này **không** "vừa qua ngưỡng" — chúng chuyển từ khung bị mép ảnh cắt cụt sang khung mặt
chính, lớn gấp gần 3 lần theo cạnh. Đó là lý do đúng để chúng thành `ok`, không phải do nới lỏng
điều kiện nào.

### 2.2. Bằng chứng trực tiếp nhất — xem ảnh đầu ra

Mở thật hai tệp `.png` trong `data/processed/lfw_original/`:

- `Dalai_Lama/Dalai_Lama_0001.png` → **đúng Đức Đạt-lai Lạt-ma**, không phải người bị cắt cụt ở mép trái.
- `Angela_Bassett/Angela_Bassett_0006.png` → **đúng Angela Bassett**, không phải người ở mép ảnh.

Cả hai căn chỉnh đúng tư thế chính diện, 112×112. Bằng chứng này mạnh hơn mọi ca test.

### 2.3. Quét lại toàn mẻ 200 ảnh

| Kiểm | Kết quả |
|---|---|
| Ảnh nhiều mặt | **49 / 200** (24,5 % — đúng như đặc tả cảnh báo, không phải ca hiếm) |
| Ảnh chọn **sai** (không phải mặt lớn nhất) | **0 / 200** ✅ |
| Ảnh mà khuôn mặt được chọn **chạm mép** | **0 / 200** ✅ |
| Cạnh nhỏ nhất của khung được chọn | **72 px** (vòng 1: 45 px) — xa ngưỡng `min_bbox_px: 40` |
| Số tệp `.png`, đọc thật bằng `cv2.imread` | **200/200 đúng `(112, 112, 3)`** ✅ |
| Manifest | 200 dòng, 7 cột đúng thứ tự, không có dấu gạch chéo ngược, không tệp lạ ✅ |
| Phân bố lý do | `ok` 200 (100 %), năm lý do còn lại đều 0 |

Tỉ lệ `khong_thay_mat` = 0 % vẫn nhất quán với dữ kiện §4 (60/60 ảnh LFW phát hiện được).
**Nguồn nhiễm dữ liệu 2,5 % phát hiện ở vòng 1 đã bị loại bỏ hoàn toàn.**

---

## 3. Mục 4 vòng 1 (ghi `seed` và `gioi_han`) — **ĐÃ LÀM**, ở `scripts/preprocess.py:476`

> Ghi chú cho người điều phối: mục này **có làm**, nằm ở bảng tổng kết CLI chứ không phải tệp,
> nên tìm bằng `.meta.json` hoặc cột manifest sẽ không thấy.

```python
# scripts/preprocess.py:475-476
print(f"\nTổng số ảnh xét: `{tong}` — manifest: `{duong_dan_manifest}`")
print(f"Seed: `{args.seed}` — giới hạn: `{args.gioi_han or 'không giới hạn'}`\n")
```

Chạy thật `--gioi-han 7 --seed 123` trên 30 ảnh LFW, bảng tổng kết in ra hai dòng cuối:

```
Tổng số ảnh xét: `7` — manifest: `...\ra_seed\manifest.csv`
Seed: `123` — giới hạn: `7`
```

Đúng **nguyên văn** cách sửa mà CẦN SỬA-3 vòng 1 kê ra. Vòng 1 đã nêu rõ lý do không đưa seed vào
tệp: §8 đặc tả chốt cứng manifest **đúng bảy cột**, và thêm `.meta.json` là mở rộng §8 — thuộc thẩm
quyền `spec-writer`, không phải việc người cài đặt tự quyết (R38). Người cài đặt làm đúng phạm vi
được giao.

Có ca test riêng `test_dong43b` dùng `capsys` assert chuỗi seed và chuỗi giới hạn xuất hiện trong
đầu ra của lần chạy **thật** (không phải `--dry-run`).

**Hạn chế còn lại** — seed chỉ có trên màn hình, nên tệp `data/processed/lfw_original/manifest.csv`
vẫn **không tự mô tả** được nó là mẻ lấy mẫu 200/9 164. Đây là vấn đề của §8 đặc tả, không phải lỗi
cài đặt → chuyển thành 🔵 GÓP Ý-1 bên dưới.

---

## 4. Kiểm kiểu bốn tham số — **19/19 ĐẠT**

Chạy lại đủ 12 cấu hình hỏng của vòng 1, cộng 11 biến thể mới, trên 30 ảnh LFW thật:

| Cấu hình hỏng | Vòng 1 | Vòng 2 |
|---|---|---|
| `min_bbox_px: "bon_muoi"` | ❌ `TypeError` lọt | ✅ `1` — *"phải là số, nhận 'bon_muoi'"* |
| `min_confidence: null` | ❌ `TypeError` lọt | ✅ `1` — *"phải là số, nhận None"* |
| `min_ti_le_lech_mui: "0.15"` | ❌ `UFuncTypeError` lọt | ✅ `1` — *"phải là số, nhận '0.15'"* |
| `min_bbox_px: True` | *(chưa thử)* | ✅ `1` — **bool bị chặn** dù `isinstance(True, int)` là `True` |
| `min_confidence: False` | *(chưa thử)* | ✅ `1` |
| `min_bbox_px: [40]` | *(chưa thử)* | ✅ `1` |
| `min_confidence: {a: 1}` | *(chưa thử)* | ✅ `1` |
| `min_ti_le_lech_mui: null` | *(chưa thử)* | ✅ `1` |
| `kiem_hinh_hoc_diem_moc: "true"` (chuỗi) | *(chưa thử)* | ✅ `1` — *"phải là true/false"* |
| `kiem_hinh_hoc_diem_moc: 1` (số) | *(chưa thử)* | ✅ `1` |
| 9 ca thiếu khoá / sai kiểu thuộc `align` | ✅ `1` | ✅ `1` (không hồi quy) |

**Cả 19 ca sai kiểu hoặc thiếu khoá đều trả `1`, thư mục ra rỗng, không có manifest, không ngoại lệ
nào lọt.** Thông báo lỗi tiếng Việt nêu đích danh khoá sai và giá trị nhận được.

Cài đặt ở `scripts/preprocess.py:139-179` — hai hàm `_lay_so_thuc` và `_lay_bool`. Điểm đáng ghi
nhận: `_lay_so_thuc:158` loại `bool` **trước** khi kiểm `isinstance(..., (int, float))`, kèm docstring
giải thích vì sao (bool là subclass của int). Đây đúng cái bẫy mà một bản sửa vội sẽ để lọt —
`min_bbox_px: true` trong YAML sẽ thành ngưỡng 1 px và mọi ảnh đều qua.

### 4.1. Bốn giá trị **hợp lệ về kiểu** — hành vi đúng, không phải lỗi

| Cấu hình | Mã trả về | Hành vi | Nhận xét |
|---|---|---|---|
| `min_bbox_px: 40.0` (float) | `0`, 30 ảnh ra | chấp nhận | ✅ đúng — float là kiểu số hợp lệ |
| `min_bbox_px: -40` | `0`, 30 ảnh ra | không lọc gì | ngưỡng âm = tắt lọc; hợp lệ về kiểu, §7 không định nghĩa miền giá trị |
| `min_confidence: inf` | `0`, 0 ảnh ra | mọi ảnh → `do_tin_cay_thap` | mẻ hoàn tất, bảng tổng kết hiện 100 % `do_tin_cay_thap` — người dùng thấy ngay |
| `min_ti_le_lech_mui: nan` | `0`, 0 ảnh ra | mọi ảnh → `diem_moc_bat_thuong` | `x >= nan` luôn `False`; bảng tổng kết hiện 100 % `diem_moc_bat_thuong` |

Ba ca sau là **giá trị vô lý nhưng đúng kiểu**. Mẻ vẫn chạy hết và trả `0`, nhưng bảng tổng kết hiển
thị 100 % ở một lý do bỏ qua — đúng chức năng mà §8 giao cho bảng tổng kết ("thứ người dùng nhìn để
biết mẻ có ổn không"). Không phải lỗi. Ghi thành 🔵 GÓP Ý-2.

---

## 5. Dòng 27 nay đã chạm `main()` — **lỗ hổng vòng 1 đã đóng**

| Phép BS2 (đổi dòng ghi `file_ra` thành `"None"`) | Kết quả |
|---|---|
| Vòng 1 | **KHÔNG ca nào đỏ** — 47 passed ❌ |
| **Vòng 2** | **dòng 27 ĐỎ** — 1 failed, 50 passed ✅ |

Xác nhận thêm bằng ĐB5 (bỏ ghi dòng manifest cho ảnh bị bỏ qua): vòng 1 đỏ `26, 43`; vòng 2 đỏ
`26, 27, 43` — dòng 27 nay **cũng** phản ứng với thay đổi ở nhánh ghi bản ghi của ảnh bị bỏ qua.
Hai phép độc lập cùng chỉ ra dòng 27 đã thật sự đi qua `main()`.

---

## 6. Hồi quy — không phép nào suy giảm

Vòng này đụng vào luồng chọn khuôn mặt và luồng đọc cấu hình, nên chạy lại **toàn bộ** bảng đột biến:

| # | Phép | Ca đỏ vòng 2 | Đặc tả đòi | Vòng 1 | Kết luận |
|---|---|---|---|---|---|
| ĐB1 | `except ValueError` → `except Exception` | **37**, 23 | 37 | 37, 23 | ✅ không đổi |
| ĐB2 | bỏ `kiem_hinh_hoc_diem_moc` | **19** | 19 | 19 | ✅ |
| ĐB3 | bỏ riêng bất biến 2 | **10** — **13 vẫn XANH** | 10, không đỏ 13 | như cũ | ✅ |
| ĐB3b | bỏ riêng điều kiện thứ năm | **13**, **13c**, 19 | 13, 13c | như cũ | ✅ |
| ĐB4 | đuôi `.jpg` | **30**, 29, 40, 41 | 30 | như cũ | ✅ |
| ĐB5 | bỏ dòng manifest ảnh bỏ qua | **26**, 27, 43 | 26 | 26, 43 | ✅ mạnh hơn |
| ĐB6 | lấy khuôn mặt cuối | **22**, 22c | 22 | 22 | ✅ |
| **ĐB6b** | khôi phục luật chọn theo conf | **22b**, 22 | 22b | *(mới)* | ✅ |
| ĐB7 | bộ lọc luôn `True` trừ khi 5 điểm trùng | **13**, 09–12, 13c, 19 | 13 | như cũ | ✅ |
| BS2 | `file_ra` ghi `"None"` | **27** | — | *không ai đỏ* | ✅ đã đóng |
| ĐB6c / ĐB6d | *(bổ sung, xem §1)* | 22b / 22c | — | *(mới)* | ✅ |

**10/10 phép bắt buộc đạt, 12/12 kể cả phép bổ sung.**
`sha256` `scripts/preprocess.py` sau toàn bộ:
`d6f50eae9a52d07d085646b99e8c0047a0569eb69fcedc911c86a8fca3e80c73` — **khớp bản gốc**.
Đọc/ghi bằng `newline=""` ở mọi phép.

Ba điểm sống còn của mã việc **không suy giảm sau khi sửa**: ĐB1 vẫn đỏ dòng 37 (phân biệt hai loại
lỗi), ĐB3b/ĐB7 vẫn đỏ dòng 13 (điều kiện thứ năm), ĐB3 vẫn **không** đỏ dòng 13 (bốn bất biến và
điều kiện thứ năm vẫn phân giải riêng rẽ được).

---

## 7. Kiểm máy, quét vi phạm, phạm vi

### 7.1. Host (Windows, Python 3.12)

| Lệnh | Kết quả |
|---|---|
| `black --line-length 100 --check` | **sạch** ✅ |
| `ruff check` | **All checks passed** ✅ |
| `pytest tests/test_preprocess.py -v` | **51 passed** ✅ (vòng 1: 47) |
| `pytest -q` (toàn repo) | **341 passed** ✅ (vòng 1: 337 — đúng +4 ca mới, không hồi quy) |
| `git status --short --untracked-files=all` | đúng **2** tệp mã nguồn ✅ |

`git diff --stat` **rỗng** — không sửa tệp đã theo dõi nào. Không có tệp
`.jpg/.png/.npy/.onnx/.env/.db` lọt vào git. **Danh sách trắng §2: tuân thủ.**

### 7.2. Container ARM64

Dựng lại ảnh từ cây làm việc hiện tại, `docker run` **không** cờ `--platform`, chạy từ PowerShell.
Môi trường xác nhận đúng §11: `aarch64`, không `models/`, không `data/`, không `docs/`, không nhị
phân `git`.

| Lệnh | Kết quả |
|---|---|
| `black --check` | **sạch** ✅ |
| `pytest tests/test_preprocess.py -v` | **51 passed — 0 error, 0 failed, 0 skipped** ✅ |

Cả bốn ca mới (`22b`, `22c`, `36b`, `43b`) đều `PASSED` trong container. Bộ test vẫn **không cần một
`pytest.skip` nào** — giữ được thiết kế "không phụ thuộc `models/`" sau khi thêm 4 ca.

`ruff` trong container vẫn báo `EXE002` như vòng 1 — đã xác định là nhiễu môi trường toàn repo
(31 tệp, gồm cả tệp đã gộp từ lâu), không phải khiếm khuyết của mã việc này. Xem 🔵 GÓP Ý-4.

### 7.3. Bốn lệnh `grep` §10

| Lệnh | Kết quả |
|---|---|
| `grep -n "except Exception" scripts/preprocess.py` | **RỖNG TUYỆT ĐỐI** ✅ |
| `grep -nE "\b(112|40|0\.7|0\.15)\b" scripts/preprocess.py` | **rỗng** ✅ |
| `grep -rn "ultralytics\|import torch" scripts/preprocess.py` | **rỗng** ✅ |
| `grep -n "print(" scripts/preprocess.py` | 19 dòng — **tất cả nằm trong `main()`**, xác minh bằng AST |

Quét AST toàn bộ `ExceptHandler`: **8 handler**, tất cả nêu đích danh lớp hẹp (`ValueError` ×3 ở
dòng 221/248/256, `LoiCauHinh` ×4, `LoiMoHinh` ×1). Không `except:` trần, không `BaseException`,
không tuple gộp lớp cha. **Ràng buộc §3 nguyên vẹn sau khi sửa.**

Rubric §2: `except:` trần `0` · log f-string `0` · `assert True` `0` · `InferenceSession` `0` ·
số magic float `0` · đường dẫn tuyệt đối `0` · secret `0`. Model khởi tạo một lần, ngoài vòng lặp.

### 7.4. Đối chiếu bảng §9 bằng AST

**51 hàm test.** Bảng §9 nay có **48 dòng** (01–43 + `13b`/`13c`/`13d` + `22b`/`22c`):
**thiếu 0, trùng 0**. Ba ca dư — `15b` (detect ném `ValueError` → trả lý do), `36b` (giá trị sai kiểu
→ trả `1`, sinh từ CẦN SỬA-1), `43b` (in seed và giới hạn, sinh từ CẦN SỬA-3) — đều **có ích và đúng
tinh thần đặc tả**, không phải ca thừa.

---

## 8. Trạng thái ba lỗi vòng 1

| Lỗi vòng 1 | Trạng thái | Bằng chứng |
|---|---|---|
| 🟡 CẦN SỬA-1 — giá trị cấu hình sai kiểu làm ngoại lệ lọt | ✅ **ĐÃ SỬA** | 19/19 cấu hình hỏng trả `1`; `_lay_so_thuc`/`_lay_bool`; ca `36b` |
| 🟡 CẦN SỬA-2 — dòng 27 không chạm `main()` | ✅ **ĐÃ SỬA** | BS2 nay làm **dòng 27 đỏ**; ĐB5 cũng đỏ 27 |
| 🟡 CẦN SỬA-3 — seed không ghi vào đầu ra | ✅ **ĐÃ SỬA** | `preprocess.py:476`; ca `43b`; chạy thật in seed và giới hạn |
| 🔵 GÓP Ý-1 — luật chọn khuôn mặt sai | ✅ **ĐÃ NÂNG THÀNH LỖI VÀ SỬA** | §7 đặc tả sửa; ĐB6b đỏ 22b; 0/200 ảnh chọn sai |

**Không phát sinh lỗi mới.** Không còn 🔴 hay 🟡.

---

## 9. 🔵 Góp ý (không chặn — người dùng quyết định)

### GÓP Ý-1 — Mẻ đã chạy vẫn không tự mô tả được từ tệp

Seed nay in ra màn hình (CẦN SỬA-3 đã xong), nhưng đầu ra để lại trên đĩa —
`data/processed/lfw_original/manifest.csv` 200 dòng — vẫn không cho biết đó là **mẻ lấy mẫu
`--gioi-han 200 --seed 42`** hay mẻ đầy đủ trên một nguồn nhỏ. Sáu tuần nữa, khi bước 1.13 (EDA)
đọc tệp này, thông tin trên terminal đã mất.

Đây là giới hạn của §8 đặc tả (manifest chốt cứng bảy cột), **không phải lỗi cài đặt**.
Đề xuất cho `spec-writer`: cho phép ghi thêm `<ra>/manifest.meta.json` chứa `seed`, `gioi_han`,
commit hash, đường dẫn config, thời điểm chạy — đúng tinh thần R17 vốn đã áp cho `results/`.
Chi phí khoảng 10 dòng, lợi ích: mọi mẻ tự truy vết được. Nếu chốt, đây là một mã việc nhỏ riêng.

### GÓP Ý-2 — Ngưỡng vô lý nhưng đúng kiểu vẫn cho mẻ "thành công"

`min_confidence: inf` hoặc `min_ti_le_lech_mui: nan` làm **mọi ảnh** bị bỏ qua nhưng mẻ vẫn trả `0`.
Bảng tổng kết có hiện 100 % ở một lý do bỏ qua nên người dùng thấy được, và dòng 43 đặc tả nói rõ
"bỏ qua không phải lỗi mẻ" — nên hành vi hiện tại **đúng đặc tả**.

Nếu muốn chặt hơn: cảnh báo `logger.warning` khi tỉ lệ `ok` bằng 0 trên một mẻ có từ N ảnh trở lên.
Rẻ và bắt được cả lỗi cấu hình lẫn lỗi mô hình. Người dùng quyết định.

### GÓP Ý-3 — `--tiep-tuc` vẫn làm rỗng bốn cột đo (giữ nguyên từ vòng 1)

`scripts/preprocess.py:413-426` ghi bản ghi rút gọn cho ảnh đã có ở đích, nên manifest của một mẻ
chạy tiếp sẽ trống `n_faces`/`conf`/`bbox_w`/`bbox_h` ở phần đã xử lý trước. Đúng đặc tả (§8 không
quy định), nhưng bước 1.7 dùng chính cột `bbox_w`/`bbox_h` để đo phân bố kích thước khuôn mặt.
Với mẻ LFW đầy đủ khoảng 7 phút, khả năng đứt giữa chừng là có thật.

Xử lý gọn: gộp chung với GÓP Ý-1 — `--tiep-tuc` đọc lại manifest cũ để hợp nhất bốn cột đo.

### GÓP Ý-4 — `ruff` báo `EXE002` trong container (nhiễu môi trường, toàn repo)

Không đổi so với vòng 1: `COPY . .` từ máy Windows đặt mọi tệp thành mode `0755` trong ảnh Linux,
làm `ruff` báo 31 lỗi `EXE002` cho **toàn bộ** repo kể cả tệp đã gộp từ lâu. Trên host `ruff` sạch.
Đề xuất một commit riêng `chore(quy-trinh)`: dùng `COPY --chmod=644 . .` trong
`deploy/Dockerfile.arm64`, hoặc thêm `EXE002` vào `lint.ignore` của `pyproject.toml`.
Không xử lý thì mọi mã việc sau đều vấp lại đúng điểm này.

---

## 10. Hai điểm sống còn

**Trung thực số liệu**: ✅ Nguồn nhiễm dữ liệu nghiêm trọng nhất — 5/198 ảnh mang mặt người khác —
**đã bị loại bỏ, xác nhận bằng cả số đo (0/200 chọn sai) lẫn mắt thường (mở hai tệp `.png` đầu ra)**.
Không có giá trị mặc định giả, không có số ví dụ trong docstring trông như kết quả đo, không có test
dùng số bịa. Ca `22b` dùng đúng số đo thật của mẻ vòng 1 (chênh conf 0,020 trong khoảng 0,001–0,036).
Bảng tổng kết in số đếm thật. Manifest khớp 100 % với 200 tệp đọc lại từ đĩa.

**An toàn phần cứng**: không áp dụng (mã việc không chạm GPIO/relay/camera). Ở nghĩa dữ liệu, tính
fail-safe **được tăng cường** so với vòng 1: 19/19 cấu hình hỏng nay dừng mẻ và trả `1`, thư mục ra
rỗng, không manifest, không ngoại lệ lọt.

---

## 11. Tổng kết hai vòng và bài học

### 11.1. Diễn biến

| | Vòng 1 | Vòng 2 |
|---|---|---|
| Ca test | 47 | **51** |
| Phép đột biến chạy | 12 (8 bắt buộc) | **12 (10 bắt buộc)** |
| Lỗi 🔴 / 🟡 | 0 / **3** | **0 / 0** |
| Ảnh ghi nhầm người trong mẻ thật | **5 / 198** | **0 / 200** |
| Cấu hình hỏng làm ngoại lệ lọt | **3 / 12** | **0 / 19** |
| Phép BS2 (`file_ra` = `"None"`) | không ca nào đỏ | **dòng 27 đỏ** |
| Container ARM64 | 47 passed, 0 error/failed/skipped | **51 passed, 0 error/failed/skipped** |

### 11.2. Bài học: luật chọn khuôn mặt — lỗi đặc tả đầu tiên gây **hỏng dữ liệu**

Các lỗi đặc tả trước đây trong dự án chỉ làm **hỏng test** hoặc **tốn một vòng bàn giao**. Lần này
khác về bản chất: mã nguồn **làm đúng đặc tả từng chữ**, `black`/`ruff` sạch, 47/47 test xanh,
container xanh — mà **dữ liệu ra vẫn bẩn**. 2,5 % ảnh trong `data/processed/` mang khuôn mặt của
người khác, và không một cơ chế tự động nào trong quy trình báo được điều đó.

**Nguyên nhân gốc**: đặc tả dùng **độ tin cậy** làm tiêu chí chọn đối tượng. Nhưng độ tin cậy đo
*chất lượng phát hiện*, **không** đo *mức quan trọng của đối tượng*. Một khuôn mặt nhỏ, rõ nét, ở
hậu cảnh hoàn toàn có thể đạt độ tin cậy ngang — thực tế là **cao hơn** — khuôn mặt chính. Diện tích
thì phân tách rõ: mặt chính lớn gấp 2–3 lần theo cạnh, tức **4–9 lần theo diện tích**.

**Vì sao không cơ chế nào bắt được**: cả bốn lớp kiểm đều mù với lỗi này. Lint và định dạng không
nhìn ngữ nghĩa. Bộ test dùng detector giả, mà detector giả được dựng theo đúng cách hiểu của đặc tả
— nên nó **tự nhất quán** với chính cái sai. Ca `22` cũ assert "conf khớp mặt đầu" — chính là assert
cái sai. Chỉ có một thứ bắt được: **mở mẻ thật ra, đối chiếu từng con số đáng ngờ với ảnh gốc bằng
mắt.** Hai ảnh `mat_qua_nho` có tỉ lệ `w/h` lệch khỏi trung vị là sợi chỉ duy nhất, và kéo nó ra mới
lộ 5 ảnh sai khác.

**Ba điều rút ra cho quy trình:**

1. **Chạy thật rồi soi số bất thường là bắt buộc, không phải tuỳ chọn.** Mọi mã việc sinh dữ liệu
   phải kèm một lần chạy thật, và review phải mở dữ liệu đó ra xem — không chỉ đọc bảng tổng kết.
   Ở đây, "198/200 ok" trông hoàn hảo; lỗi nằm trong 198 ảnh **thành công**.
2. **Ca test dùng đối tượng giả chỉ mạnh bằng hiểu biết đã có khi viết đặc tả.** Nó không phát hiện
   được sai lầm về *bản chất bài toán*. Vì thế bảng §9 nay có dòng `22b` **tái dựng số liệu thật**,
   không phải số phỏng đoán — và ĐB6b bảo đảm nó không mục theo thời gian.
3. **Khi chọn một đại lượng làm tiêu chí, phải hỏi: đại lượng này đo cái gì?** Ghi vào checklist
   `spec-writer`: *độ tin cậy đo chất lượng phát hiện, không đo mức quan trọng của đối tượng.*

Bài học này nên vào `docs/nhat-ky/tuan-05.md` và phần bàn về quy trình ở Chương 3 — nó là ví dụ cụ
thể, có số liệu, cho luận điểm "kiểm định nhiều lớp" của đồ án.

---

## 12. Việc tiếp theo

**✅ ĐẠT — được commit.** Theo R29:

```
feat(scripts): thêm mẻ tiền xử lý ảnh khuôn mặt về 112x112
```

Đặc tả `docs/dac-ta/P1-05-preprocess.md` đã sửa ở vòng này (§7, §9, §10) — nếu chưa commit thì đi
**commit riêng** trước, để truy được thay đổi đặc tả nào sinh ra thay đổi mã nào:

```
docs(dac-ta): chọn khuôn mặt theo diện tích thay vì độ tin cậy
```

Sau khi commit: gộp `feat/p1-05-preprocess` vào `dev`. Bước **1.9** của Phase 1 hoàn tất phần chạy
được — ba nguồn dữ liệu còn lại (gallery, LFW adapted, in-domain) chờ camera.

Cân nhắc chạy **mẻ LFW đầy đủ 9 164 ảnh** (khoảng 7 phút) để có `data/processed/lfw_original/` hoàn
chỉnh cho bước 1.10 và 1.13 — mẻ 200 ảnh hiện tại chỉ là mẻ thử. Nếu chạy, nhớ **xoá thư mục cũ
trước** hoặc dùng thư mục đích mới, tránh trộn kết quả của mẻ lấy mẫu với mẻ đầy đủ.
