# Review P3-03-enroll — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-03-enroll.md` (commit `a2023b0`) |
| **Nhánh** | `feat/p3-03-enroll` |
| **Mã được kiểm** | commit `6632e79` (04/09/2026 21:43) — 5 tệp, 1286 insertions(+), 1 deletion(-) |
| **Ngày** | 2026-09-04 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — một mục CHẶN-B. Sửa nằm trong `scripts/enroll.py` (một khối `except`) và một ca test bổ sung |

Toàn bộ số liệu dưới đây đến từ lượt chạy của **người dùng**, không dùng lại bảng tự kiểm của người
cài đặt. Sáu phép đột biến được dựng lại từ đầu — bốn phép do đặc tả §8.2 yêu cầu, thêm hai phép mà
bên kiểm định đặt ra cho hai ràng buộc dấu vết ở §6.4. Sau cả sáu phép, `git status --porcelain`
giới hạn theo tệp đều **rỗng**, hậu kiểm cuối `so_dong_git_status=0`: không sót mã đột biến nào.

---

## 1. Kết quả kiểm máy

### 1.1. Phạm vi tệp và dữ liệu cấm

| # | Lệnh | Kết quả |
|---|---|---|
| [1] | `git show --stat --name-status HEAD` | Đúng năm tệp danh sách trắng §2: `A scripts/enroll.py` · `M src/recognizer/__init__.py` · `A src/recognizer/factory.py` · `A tests/test_enroll.py` · `A tests/test_recognizer_factory.py`. Không tệp nào trong `data/`, `results/`, `report/`, `configs/`, `docs/`, `.claude/`, `models/` ✅ |
| [2] | `git status --short --untracked-files=all` | rỗng ✅ |
| [3] | lọc `\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$` trên `git show --name-only HEAD` | rỗng ✅ (R25) |
| [4] | `git show HEAD -- src/recognizer/__init__.py` | Thuần cộng thêm. `__all__` cũ `["DlibFaceRecognizer"]` → bốn phần tử **chứa đủ** phần tử cũ, không xoá dòng nào ✅ đúng ràng buộc "chỉ cộng thêm" của §2 |

### 1.2. Ba lệnh nền và container

| # | Lệnh | Kết quả |
|---|---|---|
| [5] | `python -m black --check --line-length 100 src tests scripts` | `All done!` — 47 tệp không đổi ✅ |
| [6] | `python -m ruff check src tests scripts` | `All checks passed!` ✅ |
| [8] | `python -m pytest tests/test_recognizer_factory.py tests/test_enroll.py -v` | **28 passed**, 0 failed, 0 skipped, 29.46 s ✅ (6 ca factory + 22 ca enroll, trong đó dòng 16 có 3 biến thể `parametrize`) |
| [9] | `python -m pytest -q` toàn kho | **529 passed**, 0 failed, 101.92 s ✅ — 0 skipped, tức năm ca `slow` của mã việc này (07, 08, 17, 18, 25) **chạy thật** với trọng số thật |
| [10] | `docker run … faceid:arm64 pytest -q -m "not slow"` | **496 passed, 1 skipped, 32 deselected**, 613.03 s ✅ — đúng một image `faceid:arm64`, không dựng lại (R43) |
| [11] | container + `--tmpfs /app/models`, `--collect-only -q -m "not slow"` | **497/529 tests collected (32 deselected)**, 0 error, 5.11 s ✅ |

Ghi chú về [11]: ràng buộc §9 *"`pytest --collect-only -m "not slow"` phải chạy trót lọt kể cả khi
chưa có `models/`"* **còn giữ được** dù gói `src.recognizer` nay phụ thuộc cứng `onnxruntime` — vì
gói đó nằm sẵn trong image. Xem §4.1 về vì sao điều này là rủi ro chứ chưa phải lỗi.

### 1.3. Quét mẫu vi phạm

| # | Mẫu | Kết quả |
|---|---|---|
| [12] | `print(` trong `src/recognizer/*.py` | rỗng ✅ (R23, §6.6) |
| [13] | `except Exception` · `np.mean` · `.mean(` · `linalg.norm` · hằng số thực viết cứng, trên `scripts/enroll.py` + `src/recognizer/factory.py` | **đúng 2 dòng**, cả hai là khoá metadata `enroll.py:508` `min_images_per_user_da_dung` và `:509` `min_images_per_user_trong_cau_hinh` ✅ — không phép tính trung bình hay chuẩn hoá nào của riêng script (§6.1), không `except Exception` trần (§9), không số magic |

Đường dẫn máy cá nhân, secret, `assert True`: không mẫu nào khớp trong hai tệp mã sản phẩm.

### 1.4. Sáu phép đột biến

| # | Phép | Ca đặc tả đòi đỏ | Thực tế | Kết luận |
|---|---|---|---|---|
| ĐB1 | `enroll.py`: thay `backend.enroll(...)` bằng trung bình tự tính rồi chuẩn hoá (§6.1) | dòng 26 | **10 failed, 12 passed** — có `test_dong26`, kèm dòng 10–15, 20, 22, 24 | ⚠️ đỏ, **nhưng qua cơ chế khác** — xem §4.2 |
| ĐB2 | Bắt `ValueError` rồi thử lại với `min_images_per_user=1` (§6.2) | dòng 09 | **2 failed, 20 passed** — `test_dong09` (`assert not True` trên `nguoi_it.npy`) và `test_dong11` (`'da_dang_ky' != 'thieu_anh'`) | ✅ có hiệu lực |
| ĐB3 | Bỏ tên backend khỏi đường dẫn đích (§6.3) | dòng 17 | **2 failed, 20 deselected** — `test_dong17` FAILED (không phải SKIPPED) và `test_dong18` `FileNotFoundError` trên `ra/dlib/nguoi_a.npy`; stdout cho thấy hai backend ghi đè cùng `manifest.csv` và `gallery.meta.json` | ✅ có hiệu lực, ca `slow` chạy thật |
| ĐB4 | `factory.py`: truyền `lay_gia_tri(cfg, "arcface")` cho `DlibFaceRecognizer` (§5.1) | dòng 01 hoặc 06 | **4 failed, 2 passed** — dòng 01, 03, 05, 06 đều `LoiCauHinh: Thiếu key bắt buộc trong cấu hình: 'dlib.model_path'` | ✅ có hiệu lực |
| ĐB5 | `enroll.py:416` `if toi_thieu_da_dung != toi_thieu_trong_cau_hinh:` → `if False:` (§6.4 điều 1) | — | **1 failed, 1 passed** — `test_dong15` FAILED, `test_dong14` PASSED | ✅ dấu vết `WARNING` có người gác |
| ĐB6 | `enroll.py:508-509` hai khoá meta ghi **cùng một** con số (§6.4 điều 2) | — | **1 failed, 2 passed** — `test_dong14` FAILED (`assert 2 == 5`); `test_dong12` và `test_dong15` PASSED | ✅ dấu vết metadata có người gác |

ĐB5 và ĐB6 do bên kiểm định thêm vào: §6.4 nói rõ hai ràng buộc dấu vết này tồn tại để ba tuần sau
còn phân biệt được gallery hạ ngưỡng với gallery thật. Bốn ràng buộc chịu lực của mã việc — §6.1
(không tự tính trung bình), §6.2 (không hạ ngưỡng ngầm), §6.3 (không trộn số chiều), §6.4 (dấu vết
`--toi-thieu`) — **đều có người gác thật**, không phép nào để lại chỗ "xanh vì không ai chạy qua".

---

## 2. Mục lỗi

### 🔴 CHẶN-B-1 — `except ValueError` bắt quá rộng: lỗi mô hình bị ghi vào manifest thành lỗi dữ liệu (CB-4)

**Vị trí**: `scripts/enroll.py:199-204`

```python
    try:
        vec = backend.enroll(anh_da_doc, cfg_enroll)
    except ValueError as e:
        logger.info("Bỏ qua '%s': %s", user_id, e)
        ket_qua["trang_thai"] = _TRANG_THAI_THIEU_ANH
        return ket_qua
```

**Bằng chứng runtime** (lượt thăm dò của người dùng, backend giả có đủ ảnh nhưng `enroll()` ném
`ValueError("Vecto dac trung co do dai 0 - loi mo hinh")`):

```
kq2 = xu_ly_mot_nguoi(d, sorted(d.glob("*.jpg")), BackendGia(), {"min_images_per_user": 3})
→ trang_thai: thieu_anh | so_anh_tim_thay: 5
```

Người này có **5 ảnh với ngưỡng 3** — thừa ảnh. Nguyên nhân thật là lỗi mô hình. Manifest ghi
`thieu_anh`.

**Vì sao**. `ValueError` không phải là mã lỗi riêng của tình huống thiếu ảnh; nó là loại ngoại lệ
chung mà cả hai backend dùng cho **bốn** nhóm nguyên nhân khác hẳn nhau:

| Nguồn `ValueError` | Vị trí | Nguyên nhân thật |
|---|---|---|
| Ít hơn `min_images_per_user` | `arcface_backend.py:306` · `dlib_backend.py:309` | thiếu ảnh — **đúng** thứ §6.2 muốn bắt |
| Danh sách rỗng | `arcface_backend.py:302` · `dlib_backend.py:305` | thiếu ảnh |
| Vectơ đặc trưng / vectơ trung bình dài 0 | `arcface_backend.py:319`, `:325` · `dlib_backend.py:170` | **mô hình hỏng** |
| Ảnh sai hình dạng, sai kiểu, **sai kích thước** | `arcface_backend.py:269-275` · `dlib_backend.py:149-153` | **dữ liệu vào chưa qua tiền xử lý** |

Dòng cuối bảng là kịch bản dễ xảy ra nhất và cũng tai hại nhất: `arcface_backend.py:275` ném
`ValueError` khi ảnh không đúng `112×112`. Trỏ `--vao` vào một thư mục ảnh **chưa** chạy
`scripts/preprocess.py` — chẳng hạn `data/raw/` khi có camera — thì mọi người đều đổ ở đây, script
ghi `thieu_anh` cho **tất cả**, in bảng tổng kết "0 người đăng ký", ghi
`gallery.meta.json` với `so_nguoi_da_dang_ky: 0`, và **trả về mã 0**. Người chạy đọc manifest sẽ đi
chụp thêm ảnh cho những người đã có 100 ảnh, trong khi thứ hỏng là ở bước tiền xử lý.

Điều này không phải thiếu sót thiết kế trạng thái: script **đã có** trạng thái riêng
`_TRANG_THAI_LOI_DOC_ANH` (`enroll.py:50`, dùng ở `:183` và `:193-196`) cho nhóm "không đọc được
ảnh". Đây là gộp nhầm ba nguyên nhân vào một nhãn, chứ không phải bảng trạng thái §5.3 thiếu chỗ.

Hậu quả xa hơn: manifest là dấu vết duy nhất giải thích **vì sao** một người vắng mặt trong gallery,
và gallery là đầu vào của bước 3.5 (quét ngưỡng → ROC → ngưỡng chính thức trong báo cáo). Một dòng
manifest nói sai nguyên nhân làm đứt chuỗi truy vết ở đúng mắt xích đó (R6).

**Sửa** — phân biệt bằng thông tin vốn đã có sẵn trong hàm (`so_anh_tim_thay` và
`cfg_enroll["min_images_per_user"]`), chỉ nhận `thieu_anh` khi số ảnh thật sự dưới ngưỡng; các
`ValueError` còn lại là lỗi mô hình/dữ liệu, phải nổi lên để `main` dừng lượt chạy và trả về `1`
(khối `try` ở `enroll.py:473-493` đã sẵn sàng nhận `LoiMoHinh`):

```python
    try:
        vec = backend.enroll(anh_da_doc, cfg_enroll)
    except ValueError as e:
        if so_anh_tim_thay < cfg_enroll["min_images_per_user"]:
            logger.info("Bỏ qua '%s' vì thiếu ảnh: %s", user_id, e)
            ket_qua["trang_thai"] = _TRANG_THAI_THIEU_ANH
            return ket_qua
        raise LoiMoHinh(
            f"backend.enroll() thất bại với '{user_id}' dù có {so_anh_tim_thay} ảnh "
            f"(ngưỡng {cfg_enroll['min_images_per_user']}): {e}"
        ) from e
```

Kèm hai ca test mới trong `tests/test_enroll.py`, dùng một backend giả có `enroll()` ném
`ValueError("Vectơ đặc trưng có độ dài 0")`:

1. đủ ảnh mà `enroll()` ném `ValueError` → `main` trả về `1`, **không** ghi `.npy`, và manifest
   **không** có dòng `thieu_anh` cho người đó;
2. thiếu ảnh thật → vẫn `thieu_anh`, mã trả về `0` (giữ nguyên hành vi §6.2 — ĐB2 phải tiếp tục đỏ
   đúng dòng 09 và dòng 11).

Cập nhật docstring `xu_ly_mot_nguoi` (`enroll.py:171-174`) cho khớp: `LoiMoHinh` nay còn phát sinh
từ nhánh này, không chỉ từ phép kiểm số chiều ở `:206-210`.

---

## 3. Đối chiếu đặc tả

| Mục | Kết luận | Bằng chứng |
|---|---|---|
| §2 Danh sách trắng | ✅ đúng năm tệp, `__init__.py` thuần cộng thêm | [1] [4] |
| §5.1 Giao diện `factory.py` | ✅ khớp từng ký tự: `TEN_BACKEND_DLIB`/`TEN_BACKEND_ARCFACE` (`factory.py:19-20`), `tao_bo_nhan_dien(cfg, ten_backend=None) -> BoNhanDien` (`:25`), ném `LoiCauHinh` ở `:42` | đọc mã · ĐB4 |
| §5.2 Giao diện dòng lệnh | ✅ đủ tám cờ `--vao --ra --config --backend --toi-thieu --nguoi --seed --dry-run` (`enroll.py:355-382`), mã trả về 0/1, `sys.stdout.reconfigure` ở `:388-391` | đọc mã · [8] |
| §5.3 Đầu ra ba tệp, manifest sáu cột đúng thứ tự | ✅ `_COT_MANIFEST` (`enroll.py:53`), meta đủ 13 khoá (`:502-522`) | dòng 10, 11, 12, 13 |
| §4 Tham số đọc từ `configs/recognize.yaml` | ✅ `backend` (`:423`), `enroll.gallery_dir` (`:427`), `enroll.min_images_per_user` (`:262`). Không thêm khoá mới vào `configs/` — [1] xác nhận `configs/` không bị sửa | [13] không có hằng số viết cứng |
| §6.1 Không tự tính trung bình | ✅ mã đúng (`enroll.py:200` gọi thẳng `backend.enroll`), [13] rỗng. ⚠️ hiệu lực ca canh — xem §4.2 | ĐB1 |
| §6.2 Thiếu ảnh thì bỏ qua, không hạ ngưỡng | ✅ về hành vi hạ ngưỡng. 🔴 về phân loại nguyên nhân — CHẶN-B-1 | ĐB2 |
| §6.3 Không trộn hai số chiều | ✅ `ra_dir = ra_dir_goc / ten_backend` (`:434`) + kiểm `vec.shape != (backend.so_chieu,)` → `LoiMoHinh` (`:206-210`) | ĐB3 · dòng 17, 18 |
| §6.4 Cờ `--toi-thieu` để lại dấu vết | ✅ cả ba điều: `WARNING` (`:416-421`), hai khoá meta (`:508-509`), `LoiCauHinh` khi âm/không nguyên (`:266-271`) | ĐB5 · ĐB6 · dòng 16 |
| §6.5 Kiểm `user_id` an toàn, thư mục rỗng bỏ qua | ✅ `kiem_ten_nguoi_hop_le` (`:102-116`), `continue` cho thư mục rỗng (`:478-479`). Xem 🔵 §4.5 về khả năng kích hoạt | dòng 22 |
| §6.6 Không `print` trong `src/` | ✅ | [12] |
| §7 Bảng nghiệm thu | ✅ đủ 26/26 dòng: 6 hàm `test_dong01`–`test_dong06`, 20 hàm `test_dong07`–`test_dong26`; đánh dấu `slow` đúng 10 ca đặc tả chỉ định | [8] · đọc mã |
| §9 Ràng buộc kỹ thuật | ✅ `black`/`ruff` sạch, type hints + docstring Google tiếng Việt ở mọi hàm public, không `except Exception`, `--collect-only` không cần `models/`, không ca nào ghi vào `data/` | [5] [6] [11] · §5.1 dưới |
| §10 Ngoài phạm vi | ✅ không có quét ngưỡng/ROC/FAR, không sửa chữ ký hai backend, không `benchmark_recognize.py`, không đụng `data/splits/` | [1] |
| **R5 trung thực số liệu** | ✅ không hằng số nào trông như kết quả đo; mọi con số trong meta đều tính từ lượt chạy | [13] |
| **Fail-safe phần cứng** | không áp dụng — mã việc không chạm GPIO/camera/relay | — |

---

## 4. Ghi nhận không chặn

### 4.1. 🔵 `src.recognizer` nay phụ thuộc **cứng** vào `onnxruntime`

Đo được, không suy đoán: `import src.recognizer` làm `'onnxruntime' in sys.modules` trả về `True`;
chặn `onnxruntime` bằng `sys.meta_path` trong tiến trình con cho `returncode 1` với traceback
`src/recognizer/arcface_backend.py:18 → import onnxruntime as ort`.

Chuỗi: `src/recognizer/__init__.py:7` → `factory.py:13` → `arcface_backend.py:18` (import mức
module). Hệ quả: mọi `from src.recognizer.X import …` trong kho nay kéo theo `onnxruntime` —
`tests/test_dlib_backend.py`, `tests/test_recognizer.py`, `tests/test_enroll.py`,
`tests/test_recognizer_factory.py`, `scripts/enroll.py`, `notebooks/05_khoi_nhan_dien.ipynb`.

Điều này **đảo ngược** đúng nguyên tắc mà `P3-02` cố ý dựng cho gói `dlib`
(`src/recognizer/dlib_backend.py:23-24`):

> Gói `dlib` KHÔNG được import ở mức module (§6.4): một dòng import ở đầu tệp làm `pytest` chết
> ngay khâu thu thập trên máy chưa cài gói, kéo đổ toàn bộ bộ kiểm thử của cả repo.

**Vì sao vẫn không chặn**: `onnxruntime` có trong `requirements.txt` và nằm sẵn trong image
`faceid:arm64`, nên [11] chứng minh ràng buộc §9 còn giữ được; và đặc tả P3-03 không nói gì về điểm
này. Đây là **rủi ro kiến trúc chưa phát tác**, không phải lỗi của người cài đặt. Đề xuất cho người
dùng: mở một mã việc riêng cho `spec-writer` chuyển hai lớp backend sang import trong thân hàm
`tao_bo_nhan_dien`, để dựng backend dlib không cần `onnxruntime` và ngược lại.

Cùng chủ đề, bên lề: `scripts/enroll.py:33` `import onnxruntime as ort` chỉ để lấy `ort.__version__`
ở `:519`, trong khi chính tệp đã có `_lay_phien_ban_goi()` (`:331-344`) tra phiên bản **không cần
import** và đang dùng cách đó cho `dlib-bin` ở `:520`. Đổi `:519` thành
`_lay_phien_ban_goi("onnxruntime")` bỏ được một import nặng khỏi đường chạy của backend dlib. Chi phí
một dòng.

### 4.2. 🔵 Ca dòng 26 đỏ dưới ĐB1, nhưng **không phải nhờ bộ đếm** — khe hở còn lại

ĐB1 làm đỏ 10 ca, trong đó có `test_dong26`. Nhưng mọi ca đỏ đều chết cùng một thông điệp:

```
AssertionError: trich_dac_trung() không được scripts/enroll.py gọi trực tiếp
```

— tức `tests/test_enroll.py:55`, chốt phụ trong `_BackendDemGoi.trich_dac_trung`. Traceback của ca
26 dừng ở `se.main(...)` (`tests/test_enroll.py:550`) → `scripts/enroll.py:493` → `:212` →
`_db1_tu_tinh` → `backend.trich_dac_trung(a)`. Nghĩa là khẳng định thật sự của ca 26 —
`assert backend.so_lan_goi == 2` ở `tests/test_enroll.py:552` — **không bao giờ được chạy tới** trong
lượt đột biến. Nó chỉ chạy (và qua) ở lượt sạch.

Khe hở còn lại: một bản đột biến **có gọi** `backend.enroll()` rồi **chuẩn hoá lại** kết quả sẽ không
chạm `trich_dac_trung` và vẫn để `so_lan_goi == 2`. Cả hai chốt đều mù. Đó đúng chế độ hỏng §6.1 mô
tả: bản sao thứ hai của logic chuẩn hoá trả về vectơ độ dài 1, trông hợp lệ hệt bản gốc.

**Không xếp mức chặn**, vì phép ĐB1 mà chính đặc tả §8.2 định nghĩa đã làm ca 26 đỏ, và ca 26 làm
đúng thứ bảng §7 dòng 26 yêu cầu ("`enroll` của backend được gọi đúng một lần cho mỗi người"). Đây
là giới hạn của **thiết kế ca kiểm trong đặc tả**, không phải sai sót cài đặt.

Khuyến nghị (chi phí gần bằng 0, nên làm luôn ở vòng 2 vì tệp test dù sao cũng phải mở ra): buộc ca
26 so **danh tính byte** giữa vectơ ghi ra đĩa và vectơ mà backend giả trả về, chứ không chỉ đếm lời
gọi. Cho `_BackendDemGoi.enroll` lưu lại vectơ vừa trả về, rồi:

```python
    assert backend.so_lan_goi == 2
    for user_id in ("nguoi_a", "nguoi_b"):
        ghi_ra = np.load(ra / "dlib" / f"{user_id}.npy")
        assert np.array_equal(ghi_ra, backend.vec_da_tra_ve[user_id])
```

Chốt này bắt được cả bản đột biến "gọi `enroll()` rồi chuẩn hoá lại", tức phủ kín §6.1.

### 4.3. 🔵 `--dry-run` in kế hoạch **trước** khi kiểm tên backend

`scripts/enroll.py:448-456` in bảng kế hoạch rồi `return 0`; phép kiểm tên backend chỉ xảy ra ở
`:459` khi gọi `tao_bo_nhan_dien`. Chạy `--dry-run --backend resnet` in ra đường dẫn đích chứa tên
rác và trả về `0`. Nhánh dự phòng `"khong_xac_dinh_backend"` ở `:434` cũng chỉ hiện ra trong chế độ
này. Bảng §7 không có ca nào canh, và §5.2 không quy định thứ tự. Nếu người dùng muốn: chuyển lời gọi
kiểm tên (không dựng mô hình) lên trước khối `--dry-run`.

### 4.4. 🔵 `cfg_enroll` dựng tay thay vì lấy nhánh `enroll` của cấu hình

`scripts/enroll.py:466` truyền `{"min_images_per_user": toi_thieu_da_dung}`. Hai backend chỉ đọc đúng
khoá này (`dlib_backend.py:307`, `arcface_backend.py:304`) nên **hiện không sai**, và việc dựng tay là
cần thiết để cờ `--toi-thieu` có hiệu lực. Nhưng docstring hợp đồng ở `src/recognizer/base.py:47` nói
`cfg` là "mục `enroll` của `configs/recognize.yaml`" — nếu sau này một backend đọc thêm một khoá
`enroll.*` khác thì nó sẽ nhận `KeyError` từ script này. Dạng bền hơn:
`{**lay_gia_tri(cfg, "enroll"), "min_images_per_user": toi_thieu_da_dung}`.

### 4.5. 🔵 `kiem_ten_nguoi_hop_le` gần như không thể kích hoạt — thiếu sót của đặc tả

`scripts/enroll.py:102-116` cài đúng §6.5, nhưng tên truyền vào (`:475`) luôn đến từ
`Path.iterdir()`, nên không bao giờ rỗng, không bao giờ chứa dấu tách đường dẫn, không bao giờ là
`.`/`..`. Bảng §7 cũng không có dòng nghiệm thu nào cho §6.5. Đây là **thiếu sót của đặc tả**, không
của người cài đặt: mã làm đúng thứ được yêu cầu. Ghi lại để `spec-writer` cân nhắc khi §6.5 được tái
sử dụng ở luồng enroll qua web (bước 6.3), nơi `user_id` đến từ đầu vào người dùng và phép kiểm này
mới thật sự cần.

### 4.6. 🔵 `tep_ra` ghi tên tệp trần

`scripts/enroll.py:487` ghi `duong_dan_npy.name`, §5.3 nói "đường dẫn tương đối" mà không nêu tương
đối so với gì. Tên tệp trần **là** đường dẫn tương đối so với chính thư mục chứa `manifest.csv`, nên
không mâu thuẫn. Nếu bước 3.5 muốn ghép đường dẫn từ thư mục gốc `<ra>` thì đặc tả phải nói rõ; đó là
việc của `spec-writer` khi viết mã việc quét ngưỡng, không phải lý do trả lại P3-03.

### 4.7. 🔵 Marker `slow` chưa đăng ký trong `pyproject.toml` — hiện trạng toàn kho

Mọi tệp test trong kho phát `PytestUnknownMarkWarning: Unknown pytest.mark.slow`
(`test_detector_factory`, `test_dlib_backend`, `test_export_detector`, `test_ncnn_backend`,
`test_yolo_face`…). Cơ chế lọc `-m "not slow"` vẫn đúng ([10] cho 32 deselected). Đây là mục treo từ
biên bản `P3-02` §3.3, thuộc một mã việc dọn dẹp riêng, **không tính vào phán quyết P3-03**.

---

## 5. §11b — lượt chạy thật đã diễn ra từ cây làm việc bẩn

### 5.1. Dấu vết đo được

> **Cập nhật 04/09/2026, sau khi biên bản được ghi**: người dùng đã xoá `data/embeddings/`.
> Mục 5.1 và 5.3 mô tả trạng thái tại thời điểm kiểm định; hiểm hoạ ở §5.3 nay đã được xử lý.

Tại thời điểm kiểm định, `data/embeddings/` chứa gallery thật của **cả hai** backend, mỗi bên 8 danh tính LFW
(`Colin_Powell`, `Donald_Rumsfeld`, `George_W_Bush`, `Jacques_Chirac`, `Jennifer_Capriati`,
`Jiri_Novak`, `Meryl_Streep`, `Vicente_Fox`), tệp `.npy` 640 byte (dlib 128-D) và 2176 byte
(ArcFace 512-D), kèm `manifest.csv` và `gallery.meta.json`. Trích `gallery.meta.json`:

```
"duong_dan_vao": "data\\processed\\lfw_original"
"so_nguoi_da_dang_ky": 8, "so_nguoi_bo_qua": 143
"min_images_per_user_da_dung": 3, "min_images_per_user_trong_cau_hinh": 10
"seed": 42
"thoi_gian": 2026-09-04T21:09:16 (dlib) · 21:12:34 (arcface)
"commit": "a2023b0c08570662ce488b2167387fdcb59af505"   ← commit của ĐẶC TẢ
"git_dirty": true
"moi_truong": "pc_x86"
```

Ba kết luận:

1. **`pytest` KHÔNG ghi vào `data/` — ràng buộc §9 sạch.** Hai bằng chứng độc lập: lượt thăm dò P0 in
   `ton_tai: True` **trước** khi bất kỳ lệnh `pytest` nào chạy; và tám danh tính là tên LFW thật, chứ
   không phải tên fixture (`nguoi_a`, `nguoi_du`, `nguoi_thieu`, `nguoi_it`, `nguoi_rong`,
   `nguoi_hong`, `A`, `B`, `C`). R25 cũng sạch: [2] rỗng, `.gitignore` chặn đúng.
2. **`git_dirty: true` là script làm ĐÚNG R17** — tệp meta tự khai nó sinh ra từ mã chưa commit. Đây
   là điểm tốt và là bằng chứng khối metadata hoạt động. Hệ quả bắt buộc: **gallery này không dùng
   được cho bước 3.5**, vì không khôi phục được chính xác mã đã sinh ra nó (R6). Phải chạy lại §11b
   sau khi mã gộp vào `dev`.
3. **Lượt chạy ngoài ý muốn lại xác nhận §6.3 và §6.4 trên dữ liệu thật**: hai thư mục `dlib/` và
   `arcface/` tách bạch với số chiều đúng 128/512; và `min_images_per_user_da_dung: 3` khác
   `min_images_per_user_trong_cau_hinh: 10` — hai khoá mang hai giá trị khác nhau trong một lượt chạy
   thật có dùng `--toi-thieu`. Bằng chứng bổ trợ cho ĐB3 và ĐB6.

Ngoài ra, kết quả mong đợi của §11b đạt: **8 người ở cả hai backend**, đúng ràng buộc "số người đăng
ký phải bằng nhau ở hai backend".

### 5.2. Ranh giới quy trình — ghi nhận, không quy trách nhiệm

Theo CLAUDE.md §2.9, lệnh ghi vào `data/` do **người dùng** chạy, không phải `coder`. Dấu vết cho
thấy lượt chạy diễn ra 21:08–21:12, **trước** commit 21:43, từ cây làm việc `git_dirty: true` tại
commit đặc tả — tức trong khoảng thời gian `coder` đang làm việc. Người dùng không nhớ có tự chạy hay
không, nên **không kết luận được ai đã chạy**. Điều xác định được: thời điểm, trạng thái cây làm
việc, và việc lượt chạy đã ghi vào `data/`. Điều không xác định được: người thực hiện.

Biện pháp phòng ngừa đề xuất cho lần sau (người dùng quyết định):

- Trong prompt bàn giao cho `coder`, nhắc lại rành mạch rằng §11b **không** thuộc lượt tự kiểm §8.
- Cho mọi mục §11b của đặc tả sau này một dòng mở đầu cố định: *"Khối này chỉ chạy sau khi biên bản
  review phán quyết ĐẠT và mã đã commit."*

### 5.3. ⚠️ Hiểm hoạ dữ liệu: tập impostor LFW nằm trong thư mục **gallery** — ĐÃ XỬ LÝ

Không phải lỗi mã — script làm đúng thứ được bảo, `--vao data/processed/lfw_original`. Nhưng:
`data/processed/lfw_original` là **tập impostor** (CLAUDE.md §1, bước 1.5), còn `data/embeddings/`
theo §3 là thư mục **gallery** — nơi chứa vectơ của 2–3 người nhà đã đăng ký.

Tám danh tính LFW đã nằm trong thư mục gallery. Nếu bước 3.5 trỏ vào `data/embeddings/` mà
không để ý, hệ thống sẽ coi 8 người LFW là **người đã đăng ký** và phép đo `FAR_lfw` bị lật ngược —
đúng chỉ số mà CLAUDE.md §1 gọi là quan trọng nhất của đồ án. Gallery thật chưa tồn tại (chưa có
camera) nên đây là thứ **duy nhất** trong thư mục đó, khả năng nhầm là có thật.

**Đề xuất**: dọn `data/embeddings/` rồi chạy lại §11b trên mã đã commit, ghi `--ra` vào một thư mục
riêng ngoài `data/embeddings/` (ví dụ `data/embeddings_thu_nghiem/`) cho mọi lượt kiểm chức năng
dùng `--toi-thieu`. Biên bản này **không** xoá gì — người dùng quyết định.

**Đã thực hiện 04/09/2026**: người dùng chạy `Remove-Item -Recurse -Force 'data\embeddings'`; kiểm
lại cho `Test-Path` → `False` và `git status --short --untracked-files=all` rỗng. Bất biến §9 —
*`data/embeddings/` không tồn tại trước khi §11b chạy trên mã sạch* — nay đã trở lại đúng, nên vòng
kiểm sau đọc kết quả này không còn nhập nhằng như vòng 1. Phần khuyến nghị dùng thư mục `--ra` riêng
cho các lượt kiểm chức năng vẫn còn hiệu lực.

### 5.4. §11b chạy lại trên mã đã commit — ĐẠT

Người dùng chạy lại đủ bốn lệnh §11b ngày 04/09/2026, sau khi xoá gallery cũ, trên `6632e79`:

| | dlib | arcface |
|---|---|---|
| `da_dang_ky` | 8 | 8 |
| `thieu_anh` | 143 | 143 |
| `loi_doc_anh` | 0 | 0 |
| số chiều | 128 | 512 |
| `commit` | `6632e79` | `6632e79` |
| `git_dirty` | `false` | `false` |

`--dry-run` xét 151 người và không ghi gì. Bất biến nghiệm thu của §11b — *số người đăng ký phải
bằng nhau ở hai backend* — **đạt**: 8 = 8. Và `git_dirty: false` trên cả hai: gallery lần này truy
vết được về một commit cụ thể, khác hẳn lượt `a2023b0 / dirty=true` đã bị loại ở §5.1.

**Một dữ kiện đáng ghi về CHẶN-B-1**: hai backend bỏ qua **đúng cùng 143 người**. `ArcFaceBackend`
có guard kích thước 112×112 (`arcface_backend.py:275`) mà `DlibFaceRecognizer` không có, nên nếu bất
kỳ ảnh nào trong tập này trượt guard đó thì số bỏ qua của arcface phải **lớn hơn** của dlib. Nó bằng
nhau. Vậy trên chính tập `lfw_original` này, 143 người kia là thiếu ảnh thật, và CHẶN-B-1 **không hề
phát tác**. Điều đó không làm nhẹ mục lỗi — bằng chứng runtime ở §2 đã dựng được trường hợp nhãn sai,
và guard 112×112 vẫn sẽ phát tác nếu ai đó trỏ `--vao` vào thư mục chưa qua `preprocess.py`. Nó chỉ
xác định rằng gallery hiện có **không** mang nhãn sai nào.

Lượt này là kiểm chức năng trên mã đã commit, **không** phải lượt cuối: vòng sửa CHẶN-B-1 sẽ đổi
`scripts/enroll.py`, nên §11b phải chạy lại sau khi biên bản phán quyết ĐẠT.

---

## 6. Việc phải làm trước khi gộp `dev`

| # | Việc | Ai làm |
|---|---|---|
| 1 | Sửa CHẶN-B-1 tại `scripts/enroll.py:199-204` + hai ca test mới ở §2 | `coder` |
| 2 | Dán về: `black` · `ruff` · `pytest tests/test_recognizer_factory.py tests/test_enroll.py -v` (phải ≥ 30 passed, 0 failed) · `pytest -q` toàn kho (≥ 531 passed, 0 failed) | `coder` |
| 3 | Dựng lại **ĐB2** sau khi sửa và dán cặp kết quả: đỏ đúng dòng 09 và dòng 11 khi đột biến, xanh sau khôi phục bằng `git checkout -- scripts/enroll.py`, `git status --porcelain` rỗng — chứng minh bản sửa **không** làm hỏng hành vi §6.2 | `coder` |
| 4 | ~~Quyết định về `data/embeddings/` (§5.3)~~ — **xong 04/09/2026**, đã xoá | người dùng |
| 5 | Sau khi ĐẠT và đã commit: chạy lại §11b trên mã sạch, `git_dirty` phải là `false` | người dùng |

Mục 5 đã được chạy **một lượt trước hạn** trên `6632e79` (§5.4): bất biến 8 = 8 đạt, `git_dirty:
false`. Lượt đó xác nhận script làm việc ngoài đời trên mã đã commit, nhưng **không** thay thế lượt
sau khi ĐẠT — bản sửa CHẶN-B-1 sẽ đổi `scripts/enroll.py` nên gallery phải sinh lại từ mã cuối.

Ba mục 🔵 §4.1, §4.5 và §4.7 **không** thuộc vòng sửa này: §4.1 và §4.5 là việc của `spec-writer`
(mã việc riêng), §4.7 là mục dọn dẹp toàn kho treo từ `P3-02`. Mục §4.2 là khuyến nghị — nên làm
kèm vì tệp test dù sao cũng phải mở ra, nhưng **không** là điều kiện nghiệm thu.

---

## 7. Phán quyết

🔴 **TRẢ LẠI** — vòng 1. Một mục CHẶN-B, không mục CHẶN-A, không mục CẦN SỬA.

Phần lớn mã việc `P3-03-enroll` được đánh giá là **đúng**: phạm vi tệp sạch, ba lệnh nền xanh, container
xanh, không mẫu vi phạm nào, đủ 26/26 dòng nghiệm thu, và — quan trọng nhất — **bốn ràng buộc chịu
lực của §6 đều có người gác được chứng minh bằng đột biến**, kể cả hai ràng buộc dấu vết §6.4 mà đặc
tả không yêu cầu kiểm. Khối metadata làm đúng R17 tới mức tự khai `git_dirty: true`, và chính lời khai
đó là thứ cho phép loại gallery hiện có ra khỏi bước 3.5 thay vì để nó âm thầm đi vào báo cáo.

Điều giữ lại phán quyết là mục C: `except ValueError` ở `scripts/enroll.py:201` gộp ba nhóm nguyên
nhân khác hẳn nhau vào một nhãn `thieu_anh`, và có bằng chứng runtime rằng người có 5 ảnh với ngưỡng
3 vẫn bị ghi `thieu_anh`. Với `arcface_backend.py:275`, chạy script trên ảnh chưa tiền xử lý sẽ cho
"0 người đăng ký", mã trả về `0`, và một manifest nói sai nguyên nhân — đúng loại lỗi im lặng mà
manifest tồn tại để chặn. Sửa gọn, nằm trong một khối `except`, và mọi thông tin cần để phân biệt đã
có sẵn trong hàm.

---
---

# Review P3-03-enroll — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P3-03-enroll.md` (commit `a2023b0`) |
| **Nhánh** | `feat/p3-03-enroll` |
| **Mã được kiểm** | cây làm việc trên `6632e79` + bản vá chưa commit: `M scripts/enroll.py` (+19/−6), `M tests/test_enroll.py` (+80/−0) — tổng 93 dòng thêm, 6 dòng bớt [3] |
| **Ngày** | 2026-09-05 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — CHẶN-B-1 đã được chữa và có người gác chứng minh bằng đột biến. Không còn mục 🔴 hay 🟡. Ba mục 🔵 mới chuyển thành mã việc riêng, không chặn gộp |

Số liệu ở mục này đến từ **32 lệnh do người dùng chạy ngày 05/09/2026**, không dùng lại bảng tự kiểm
của người cài đặt. Bốn phép đột biến được dựng lại từ đầu, và cả bốn lượt khôi phục ([21], [24], [27],
[30]) đều trả về đúng chuỗi `sha256` của bản sao lưu ngoài repo
`247061D24B8B78A1B522DD2B067A15B67CBFBA828B70B0F58077133561073098` — không sót mã đột biến nào.

---

## 8. Kết quả kiểm máy — vòng 2

### 8.1. Phạm vi tệp và dữ liệu cấm

| # | Lệnh | Kết quả |
|---|---|---|
| [2] | `git status --short --untracked-files=all` | đúng ba dòng: `M scripts/enroll.py`, `M tests/test_enroll.py`, `?? docs/review/P3-03-enroll.review.md` ✅ — `src/recognizer/factory.py` **không đổi**, đúng phạm vi vòng sửa mà §6 vòng 1 giao |
| [3] | `git diff --stat` | `scripts/enroll.py` +19/−6 · `tests/test_enroll.py` +80/−0 ✅ hai tệp, đều nằm trong danh sách trắng §2 đặc tả |
| [4] | lọc `\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$` trên `git status` | rỗng ✅ (R25) |

Thư mục `data/embeddings/` có tồn tại ([10]) nhưng **không** xuất hiện trong [2] — nó bị `.gitignore`
chặn đúng, không có tệp `.npy` nào lọt vào vùng theo dõi của git.

### 8.2. Ba lệnh nền và container

| # | Lệnh | Kết quả | Đối chiếu vòng 1 |
|---|---|---|---|
| [5] | `python -m black --check --line-length 100 src tests scripts` | `All done!` — **47 tệp không đổi** ✅ | như [5] vòng 1 |
| [6] | `python -m ruff check src tests scripts` | `All checks passed!` ✅ | như [6] vòng 1 |
| [7] | `python -m pytest tests/test_recognizer_factory.py tests/test_enroll.py -v` | **30 passed**, 0 failed, 29.92 s ✅ — có `test_dong09b_… PASSED` và `test_dong09c_… PASSED` | 28 → 30, đúng **+2**, khớp chính xác hai ca mới. Ngưỡng §6 mục 2 đòi ≥ 30 → **đạt** |
| [8] | `python -m pytest -q` toàn kho | **531 passed**, 0 failed, 0 skipped, 104.41 s ✅ | 529 → 531, đúng **+2**. Ngưỡng §6 mục 2 đòi ≥ 531 → **đạt** |
| [9] | `docker run --rm -v … faceid:arm64 python3 -m pytest -q -m "not slow"` | **498 passed, 1 skipped, 32 deselected**, 0 failed, 727.18 s ✅ | 496 → 498, đúng **+2**. Đúng một image `faceid:arm64`, không dựng lại (R43) |

Ba con số `+2` khớp nhau ở **ba môi trường độc lập** (host chọn lọc, host toàn kho, container ARM64):
hai ca mới chạy được ở cả ba nơi và không ca nào cũ bị hỏng theo. `0 skipped` ở [8] xác nhận năm ca
`slow` của mã việc này vẫn chạy thật với trọng số thật.

### 8.3. Quét mẫu vi phạm

| # | Mẫu | Kết quả |
|---|---|---|
| [11] | `print(` trong `src\recognizer\*.py` | rỗng ✅ (R23, §6.6) |
| [12] | `except Exception` trong `src/recognizer/factory.py`, `scripts/enroll.py` | rỗng ✅ (§9) — bản vá dùng `except ValueError` có điều kiện, không nới rộng thành `except Exception` |
| [13] | `np.mean\|\.mean(\|linalg\.norm` trong `scripts/enroll.py` | rỗng ✅ (§6.1) — bản vá không lén đưa phép chuẩn hoá nào vào script |

### 8.4. Trạng thái `data/embeddings/`

[10] `Test-Path "data\embeddings"` → **True**. Đây là gallery của lượt §11b ngày 04/09 (§5.4 vòng 1),
**không** phải thứ mới sinh ra: nội dung đúng hai thư mục con `dlib/` và `arcface/`, mỗi bên 8 tệp
`.npy` + `manifest.csv` + `gallery.meta.json`, không thư mục nào khác. Trích `gallery.meta.json` cả
hai backend: `so_nguoi_da_dang_ky: 8`, `so_nguoi_bo_qua: 143`, `min_images_per_user_da_dung: 3`,
`min_images_per_user_trong_cau_hinh: 10`, `seed: 42`, `commit: 6632e79…`, `git_dirty: false`,
`moi_truong: "pc_x86"`, khối `software` đủ 5 khoá.

Dấu thời gian `2026-09-04T22:31:51+07:00` (dlib) và `22:32:11+07:00` (arcface) là **bằng chứng bổ
sung cho ràng buộc §9**: toàn bộ lượt `pytest` ngày 05/09 ([7], [8], [9], [32]) **không ghi gì** vào
`data/` — nếu có, dấu thời gian đã đổi. Ràng buộc "không ghi vào `data/` khi chạy `pytest`" vẫn sạch.

---

## 9. Bốn phép đột biến — vòng 2

Sao lưu `scripts/enroll.py` ra ngoài repo trước mỗi phép; khôi phục và đối chiếu `sha256` sau mỗi
phép. Cả bốn lượt khôi phục cho đúng
`247061D24B8B78A1B522DD2B067A15B67CBFBA828B70B0F58077133561073098`.

| # | Phép | Mục đích | Kết quả | Kết luận |
|---|---|---|---|---|
| **ĐB2** | Bắt `ValueError` rồi thử lại với `min_images_per_user=1` (đặc tả §8.2, §6 mục 3 vòng 1) — thay 9 dòng bằng 2 | Bản vá có làm hỏng §6.2 không | **4 failed, 15 passed** — `test_dong09` (`assert not True` trên `nguoi_it.npy`), `test_dong11` (`'nguoi_thieu': 'da_dang_ky' != 'thieu_anh'`), thêm `test_dong09b` và `test_dong09c` cùng đỏ vì `ValueError` lọt ra ngoài | ✅ **đỏ đúng dòng 09 và dòng 11 như đặc tả đòi** — điều kiện §6 mục 3 vòng 1 đạt. Hai ca mới cũng đỏ theo là hệ quả đúng: chúng dùng backend luôn ném `ValueError` |
| **ĐB7** | Đảo chính bản vá — thay khối `raise LoiMoHinh` bằng `logger.info` + `trang_thai = thieu_anh` + `return`, tức quay về hành vi vòng 1; thay 9 dòng bằng 4 | Ca 09b có canh đúng chiều mới không | **1 failed, 18 passed** — **chỉ** `test_dong09b` FAILED (`assert 0 == 1`); `test_dong09` và `test_dong09c` **vẫn PASSED** | ✅ ca 09b canh đúng và **chỉ** chỗ mới; hai ca chiều `thieu_anh` không bị kéo theo — chứng minh bản vá **không** nuốt nhánh §6.2 |
| **ĐB8** | `raise LoiMoHinh(` → `raise LoiCauHinh(` tại nhánh `scripts/enroll.py:208` | Ca 09b có phân biệt lớp ngoại lệ không | **19 passed, 0 failed** | ❌ **không ai gác** — xem 🔵 §12.2 |
| **ĐB9** | `so_anh_tim_thay < …` → `so_anh_tim_thay <= …` tại `scripts/enroll.py:204` | Biên `so_anh == ngưỡng` có ca canh không | **19 passed, 0 failed** | ❌ **không ai gác** — xem 🔵 §12.3 |

ĐB2 và ĐB7 là **cặp đối xứng**, và đó là điểm chịu lực của vòng này: một phép phá chiều `thieu_anh`
làm đỏ đúng 09/11, một phép phá chiều `LoiMoHinh` làm đỏ đúng 09b. Không phép nào làm đỏ chiều kia.
Hai nhánh của bản vá được canh **độc lập**.

ĐB8 và ĐB9 do bên kiểm định thêm vào để đo **độ sắc** của ca 09b và của biên số ảnh. Cả hai xanh —
tức mã sản phẩm hiện tại đúng nhưng không có người gác cho hai chiều đó.

---

## 10. Ba thăm dò

### 10.1. [14] P1 — biên `so_anh == ngưỡng`

Backend giả **luôn** ném `ValueError`, ngưỡng 3:

```
KETQUA so_anh=2 -> ma=0 | trang_thai=thieu_anh           | npy=False
KETQUA so_anh=3 -> ma=1 | trang_thai=(KHONG CO MANIFEST) | npy=False
KETQUA so_anh=4 -> ma=1 | trang_thai=(KHONG CO MANIFEST) | npy=False
```

Với `so_anh=3` và `4`, stderr in:

```
Đăng ký thất bại, dừng ngay: backend.enroll() thất bại với 'nguoi_x' dù có 3 ảnh (ngưỡng 3):
Vecto dac trung co do dai 0
```

**Biên đúng**: số ảnh **bằng đúng** ngưỡng đi nhánh `raise`, không bị dán nhãn `thieu_anh`. Điều kiện
đối ứng nằm ở `dlib_backend.py:308` và `arcface_backend.py:305` — cùng toán tử `<`, cùng ngưỡng, nên
`scripts/enroll.py:204` không lệch một đơn vị so với backend. Thông điệp lỗi nêu đủ `user_id`, số ảnh
thật, ngưỡng và nguyên nhân gốc — đủ để người chạy phân biệt lỗi mô hình với lỗi thiếu ảnh, đúng thứ
CHẶN-B-1 đòi.

Ghi chú phụ: dòng thông báo in **hai lần** (một từ chỗ bắt trong vòng lặp, một từ `main()`), thấy ở cả
P1, P2 và P3 — dư thừa, không sai. Xem 🔵 §12.4.

### 10.2. [15] P2 — cấu hình thiếu `enroll.min_images_per_user`

```
Tham số --toi-thieu không hợp lệ: Thiếu key bắt buộc trong cấu hình: 'enroll.min_images_per_user'
KETQUA ma = 1 | co ngoai le thoat ra ngoai main: KHONG
```

Giả thuyết ban đầu — bản vá đọc `cfg_enroll["min_images_per_user"]` ở `:204`, tức **bên trong** khối
`except ValueError`, nên một cấu hình thiếu khoá có thể sinh `KeyError` chồng lên ngoại lệ đang xử lý
và trào ra thành traceback thô — **bị loại trừ**: không `KeyError`, không traceback, mã trả về 1,
thông điệp nêu đúng tên khoá thiếu. Cấu hình thiếu khoá bị chặn sớm ở `_phan_giai_toi_thieu` (`:269`)
thành `LoiCauHinh`, `main()` bắt ở `:418-421`. Đường đó không tới được qua CLI.

Khe hở duy nhất còn lại là khi gọi `xu_ly_mot_nguoi` **trực tiếp** từ ngoài với `cfg_enroll` thiếu
khoá — cùng họ với mục 🔵 §4.4 vòng 1 (hợp đồng `cfg_enroll` dựng tay), không phải mục lỗi mới.

### 10.3. [16] P3 — trạng thái thư mục đích khi lượt chạy dừng giữa chừng

Người thứ nhất thành công, người thứ hai ném `ValueError` dù đủ 3 ảnh:

```
Đăng ký thất bại, dừng ngay: backend.enroll() thất bại với 'nguoi_b' dù có 3 ảnh (ngưỡng 3): …
KETQUA ma=1 | nguoi_a.npy=True | nguoi_b.npy=False | manifest.csv=False | gallery.meta.json=False
NOI DUNG THU MUC DICH: ['nguoi_a.npy']
```

Thư mục đích còn lại **đúng một tệp `.npy` mồ côi**, không `manifest.csv`, không `gallery.meta.json`.
Xem 🔵 §12.1.

---

## 11. Kết luận về CHẶN-B-1

**Đã chữa đúng, và không nuốt nhánh nào.** Bốn bằng chứng độc lập:

| Chiều cần giữ | Bằng chứng | Kết quả |
|---|---|---|
| Đủ ảnh mà `enroll()` đổ → **không** dán nhãn `thieu_anh`, dừng lượt chạy, mã 1 | [14] dòng `so_anh=3` và `so_anh=4`; [16] | mã 1, manifest không được ghi, không `.npy` |
| Thiếu ảnh thật → **vẫn** `thieu_anh`, mã 0, chạy tiếp | [14] dòng `so_anh=2`; [7] `test_dong09c` PASSED | `trang_thai=thieu_anh`, `ma=0` |
| Hành vi §6.2 còn nguyên sau bản vá | **ĐB2** | đỏ đúng dòng 09 và dòng 11 |
| Chiều mới có người gác riêng | **ĐB7** | chỉ 09b đỏ; 09 và 09c vẫn xanh |

Mã nguồn tại `scripts/enroll.py:201-211` khớp từng dòng với đoạn sửa mà §2 vòng 1 chỉ định, kể cả
`raise … from e` giữ lại ngoại lệ gốc. Docstring `Raises:` ở `:171-176` đã được cập nhật nêu cả hai
nguồn `LoiMoHinh` (nhánh này và phép kiểm số chiều ở `:213-217`) — yêu cầu cuối của §2 vòng 1, và
R20 đạt.

Hai ca test mới đúng thứ §2 vòng 1 đặt hàng: `test_dong09b` (đủ 5 ảnh, ngưỡng 3, `enroll()` ném
`ValueError` → `ma == 1`, không `.npy`) và `test_dong09c` (đối chứng: cùng backend, 2 ảnh, ngưỡng 3
→ `ma == 0`, `trang_thai == thieu_anh`). Lớp `_BackendLoiMoHinhGia` kế thừa đúng bốn chữ ký của
`src/recognizer/base.py`, không lệch hợp đồng.

Điểm quan trọng về phương pháp: `test_dong09c` phân biệt bằng **số ảnh thật sự**, không bằng nội dung
chuỗi `ValueError` — cùng một backend, cùng một thông điệp lỗi, hai kết quả khác nhau chỉ vì số ảnh
khác nhau. Đó đúng cách phân biệt mà §2 vòng 1 yêu cầu.

**Mục CHẶN-B-1 đóng.**

---

## 12. Ghi nhận mới — vòng 2 (không chặn)

Ba mục dưới đây do lượt kiểm định vòng 2 phát hiện. **Không mục nào thuộc phạm vi vòng sửa mà §6 vòng
1 giao**, và không mục nào là vi phạm một dòng nào của đặc tả: bảng §7 đặc tả không có dòng nghiệm thu
tương ứng, và §6 đặc tả không quy định hành vi tương ứng. Theo `.claude/instructions/code-review.instructions.md`
§5 ("không review việc mà đặc tả cố ý để lại") và §3 (🔵 GÓP Ý = ghi nhận, người dùng quyết định),
cả ba xếp mức **🔵 GÓP Ý** và chuyển thành mã việc riêng cho `spec-writer`.

### 12.1. 🔵 Trạng thái ghi dở dang: `.npy` mồ côi khi lượt chạy dừng giữa chừng

**Vị trí**: `scripts/enroll.py:491-494` (ghi `.npy` trong vòng lặp) so với `:502` (`manifest.csv`) và
`:530` (`gallery.meta.json`) — hai tệp sau chỉ được ghi **ngoài** khối `try`.

```python
            if ket_qua["vec"] is not None:
                duong_dan_npy = ra_dir / f"{ket_qua['user_id']}.npy"
                np.save(duong_dan_npy, ket_qua["vec"])       # :493 — trong vòng lặp
                ket_qua["tep_ra"] = duong_dan_npy.name
            ban_ghi_manifest.append(...)
    except (LoiCauHinh, LoiMoHinh) as e:
        ...
        return 1                                             # :500 — thoát trước khi ghi manifest
    duong_dan_manifest = ra_dir / "manifest.csv"             # :502
```

**Vì sao**: khi `LoiMoHinh` nổi lên ở người thứ k, thư mục đích giữ lại `.npy` của người 1…k−1 mà
**không** `manifest.csv`, **không** `gallery.meta.json` — [16] đo được đúng trạng thái đó
(`NOI DUNG THU MUC DICH: ['nguoi_a.npy']`). Một thư mục như vậy mất toàn bộ dấu vết `commit`,
`git_dirty`, `moi_truong`, `min_images_per_user_da_dung` (R17) nhưng vẫn **đủ hình dạng** để bước 3.5
nạp vào bằng `rglob("*.npy")`. Đây đúng họ hiểm hoạ mà §5.3 vòng 1 đã nêu: gallery không truy vết
được vẫn đi tiếp vào chuỗi tính FAR.

**Vì sao vẫn không chặn**, ba lý do:

1. Đường này là **hệ quả trực tiếp của đơn thuốc vòng 1** — trước bản vá, `LoiMoHinh` từ nhánh này
   không tồn tại nên đường gần như không đi được. Đặc tả và biên bản vòng 1 đều không nói gì về việc
   dọn dẹp khi dừng; người cài đặt làm đúng thứ được yêu cầu.
2. Lỗi **không im lặng** — khác hẳn CHẶN-B-1. `main()` in `Đăng ký thất bại: …` ra stdout, ghi
   `logger.error`, và trả về `1` ([16]). Người chạy biết ngay lượt chạy đã hỏng.
3. Đặc tả §5.3 không quy định hành vi khi dừng giữa chừng, nên xếp mức chặn ở đây là **mở rộng đặc tả
   trong lúc review**.

**Đề xuất cho mã việc sau** (một trong hai, `spec-writer` chốt):
ghi `.npy` vào thư mục tạm rồi đổi tên khi cả lượt xong; hoặc ở nhánh `except`, xoá các `.npy` vừa
ghi trong lượt này trước khi `return 1`. Kèm một ca nghiệm thu: *lượt chạy dừng giữa chừng → thư mục
đích không còn `.npy` nào của lượt đó, hoặc có đủ cả `manifest.csv`*.

### 12.2. 🔵 Ca `test_dong09b` không phân biệt lớp ngoại lệ

**Vị trí**: `tests/test_enroll.py:277` (`assert ma == 1`) và `:281` (`if manifest.exists():`).

**Bằng chứng**: **ĐB8** đổi `raise LoiMoHinh(` thành `raise LoiCauHinh(` tại `scripts/enroll.py:208`
→ **19 passed, 0 failed**. Không ca nào đỏ.

**Vì sao**: `main():497-500` bắt **cả hai** lớp `(LoiCauHinh, LoiMoHinh)` và cùng trả về `1`, nên chốt
`ma == 1` mù trước việc phân loại ngoại lệ. Ba tuần sau, một bản refactor đổi nhầm lớp ngoại lệ sẽ đi
qua bộ kiểm thử mà không ai biết — và lớp ngoại lệ chính là thứ phân biệt "cấu hình sai" với "mô hình
hỏng" ở mọi chỗ gọi `xu_ly_mot_nguoi` từ ngoài `main()`.

Kèm theo, `:281` `if manifest.exists():` là **nhánh chết**: [16] chứng minh manifest chưa từng được
ghi khi lượt chạy dừng, nên khối `assert not any(…)` bên trong không bao giờ chạy. Ca test hiện chỉ
còn hai chốt sống: `ma == 1` và `not (ra/"dlib"/"nguoi_a.npy").exists()`.

**Mã sản phẩm đúng — chỗ thiếu nằm ở tập test.** Đề xuất: thêm một ca gọi thẳng `xu_ly_mot_nguoi` và
dùng `pytest.raises(LoiMoHinh)`; đổi `if manifest.exists():` thành `assert not manifest.exists()` để
nhánh chết trở thành chốt sống.

### 12.3. 🔵 Biên `so_anh == ngưỡng` không có ca canh

**Vị trí**: `scripts/enroll.py:204` `if so_anh_tim_thay < cfg_enroll["min_images_per_user"]:`.

**Bằng chứng**: **ĐB9** đổi `<` thành `<=` → **19 passed, 0 failed**. Ba ca liên quan dùng 2/3
(`test_dong09`, `test_dong09c`), 5/3 (`test_dong09b`) và 2/3 (`test_dong11`) — **không ca nào đặt số
ảnh bằng đúng ngưỡng**.

**Mã hiện tại đúng**, và [14] chứng minh trên máy: `so_anh=3` với ngưỡng 3 đi nhánh `raise`, khớp với
`<` ở `dlib_backend.py:308` và `arcface_backend.py:305`. Nhưng không có người gác, nên một lần đổi
toán tử trong tương lai sẽ lọt: khi đó người có **đúng** số ảnh tối thiểu bị ghi `thieu_anh` thay vì
được đăng ký — tức mất người khỏi gallery một cách im lặng, đúng loại lỗi CHẶN-B-1 tồn tại để chặn.

**Mã sản phẩm đúng — chỗ thiếu nằm ở tập test.** Đề xuất: một ca `so_anh == min_images_per_user` với
backend thật hoặc backend giả trả vectơ hợp lệ → `ma == 0`, `trang_thai == da_dang_ky`.

### 12.4. 🔵 Thông báo lỗi in hai lần

`scripts/enroll.py:498-499` ghi `logger.error` **và** `print` cùng một nội dung; thấy trong cả [14],
[15], [16]. Dư thừa, không sai — cùng khuôn mà `:468-469` đang dùng cho lỗi dựng backend. Không đề
xuất sửa ở mã việc này.

---

## 13. Đối chiếu điều kiện nghiệm thu §6 vòng 1

| # | Điều kiện (§6 vòng 1) | Kết luận | Bằng chứng |
|---|---|---|---|
| 1 | Sửa CHẶN-B-1 tại `scripts/enroll.py:199-204` | ✅ **đạt** — mã tại `:201-211` khớp đoạn sửa đã chỉ định, docstring `Raises:` (`:171-176`) cập nhật theo | đọc mã · [3] +19/−6 |
| 2 | Hai ca test mới đúng hai chiều §2 vòng 1 | ✅ **đạt** — `test_dong09b` (đủ ảnh → `ma == 1`, không `.npy`) và `test_dong09c` (thiếu ảnh thật → `ma == 0`, `thieu_anh`) | [7] cả hai PASSED |
| 3 | `black` và `ruff` sạch | ✅ **đạt** — `All done!` 47 tệp · `All checks passed!` | [5] [6] |
| 4 | `pytest` bộ đích ≥ 30 passed, toàn kho ≥ 531 passed, 0 failed | ✅ **đạt đúng ngưỡng** — 30 và 531, đều `+2` so với vòng 1; container 498 (+2) | [7] [8] [9] |
| 5 | Dựng lại **ĐB2**: đỏ đúng dòng 09 và dòng 11, khôi phục khớp `sha256` | ✅ **đạt** — 4 failed gồm `test_dong09` và `test_dong11`; khôi phục [21] khớp hash | ĐB2 · [21] |
| 6 | Quyết định về `data/embeddings/` (§5.3) | ✅ **đạt** — thư mục hiện chỉ chứa gallery §11b ngày 04/09 trên `6632e79`, `git_dirty: false`, không thư mục lạ; `pytest` ngày 05/09 không ghi vào `data/` (dấu thời gian không đổi) | [10] · [32] |

Mục 5 của bảng §6 vòng 1 — *chạy lại §11b trên mã sạch sau khi ĐẠT* — **chưa đến hạn** theo đúng định
nghĩa của nó: nó là việc **sau** khi gộp. Bản vá đã đổi `scripts/enroll.py`, nên gallery hiện có ở
`data/embeddings/` (sinh từ `6632e79`) **không** phải sản phẩm của mã cuối. Xem §14.

Chốt trạng thái cuối lượt kiểm: [31] `git status --short -uall` trả về y hệt [2] — đúng ba dòng, bản
sửa vòng 2 còn nguyên sau bốn phép đột biến; [32] `pytest` bộ đích **30 passed**, 92.66 s.

---

## 14. Việc còn lại

### 14.1. Sau khi gộp — bắt buộc

| # | Việc | Ai làm |
|---|---|---|
| 1 | Commit hai tệp `scripts/enroll.py` và `tests/test_enroll.py`, gộp `feat/p3-03-enroll` vào `dev` | người dùng |
| 2 | **Chạy lại §11b trên mã cuối**: xoá `data/embeddings/` cũ rồi chạy đủ bốn lệnh §11b đặc tả. Kỳ vọng: `git_dirty: false`, `commit` trỏ vào commit mới, và bất biến *số người đăng ký bằng nhau ở hai backend* (8 = 8) | người dùng |

Mục 2 là mục 5 của bảng §6 vòng 1, vẫn còn hiệu lực. Gallery hiện có mang `commit: 6632e79`, tức mã
**trước** bản vá — dùng nó cho bước 3.5 sẽ làm đứt chuỗi truy vết ở đúng chỗ R6 quan tâm.

### 14.2. Mã việc riêng cho `spec-writer` — không chặn gộp

| Nguồn | Nội dung | Ưu tiên |
|---|---|---|
| 🔵 §12.1 | Dọn dẹp hoặc ghi manifest khi lượt chạy dừng giữa chừng, kèm ca nghiệm thu | **cao** — nên đóng trước khi bước 3.5 nạp `data/embeddings/` |
| 🔵 §12.2 + §12.3 | Siết `test_dong09b` (phân biệt lớp ngoại lệ, bỏ nhánh chết `:281`) và thêm ca biên `so_anh == ngưỡng` | trung bình — gộp chung một mã việc test |
| 🔵 §4.2 vòng 1 | Ca 26 so danh tính byte thay vì chỉ đếm lời gọi | trung bình |
| 🔵 §4.1 vòng 1 | Chuyển import hai backend vào thân `tao_bo_nhan_dien` để gỡ phụ thuộc cứng `onnxruntime` | trung bình |
| 🔵 §4.5 vòng 1 | `kiem_ten_nguoi_hop_le` — cần ca nghiệm thu khi §6.5 tái sử dụng ở luồng enroll qua web (bước 6.3) | thấp |
| 🔵 §4.7 vòng 1 | Đăng ký marker `slow` trong `pyproject.toml` — mục dọn dẹp toàn kho treo từ `P3-02` | thấp |

Sáu mục trên **không** được nhét vào vòng sửa đã đóng. Vòng sửa vòng 2 nhận đúng ba việc (§6 vòng 1
mục 1–3) và hoàn thành đủ ba.

---

## 15. Phán quyết — vòng 2

🟡 **ĐẠT CÓ ĐIỀU KIỆN**. Không mục 🔴 CHẶN-A, không 🔴 CHẶN-B, không 🟡 CẦN SỬA. Bốn mục 🔵 mới
(§12.1–§12.4), chuyển thành mã việc riêng theo §14.2. **Được commit và gộp vào `dev`.**

Lập luận:

1. **Sáu điều kiện nghiệm thu §6 vòng 1 đều đạt** (§13), số test khớp `+2` ở cả ba môi trường, ba
   lệnh nền sạch, container xanh với đúng image `faceid:arm64`, phạm vi tệp đúng hai tệp trong danh
   sách trắng, không tệp cấm nào lọt vào git.
2. **CHẶN-B-1 đã đóng có bằng chứng hai chiều.** ĐB7 chứng minh ca 09b canh đúng chiều mới và **chỉ**
   chiều mới; ĐB2 chứng minh chiều `thieu_anh` của §6.2 còn nguyên. Bản vá chữa được lỗi mà không đổi
   hành vi kề bên — đúng thứ khó nhất của một vòng sửa.
3. **Ba phát hiện mới đều nằm ngoài phạm vi vòng sửa mà biên bản vòng 1 giao**, và không mục nào vi
   phạm một dòng cụ thể nào của đặc tả. §12.1 còn là hệ quả trực tiếp của chính đơn thuốc vòng 1.
   Trả lại lần nữa vì chúng là **mở rộng đặc tả trong lúc review**, thứ mà chuẩn review §5 cấm.
4. **CLAUDE.md §2.9 đặt trần 2 vòng** cho chu trình TRẢ LẠI–sửa. Đây là vòng 2. Nếu ba mục 🔵 mới bị
   xếp thành lý do trả lại thì mã việc chạm trần với một danh sách việc mà **đặc tả chưa từng yêu
   cầu** — dấu hiệu của vòng lặp hỏng do đặc tả, không do người cài đặt.
5. **Rủi ro còn lại được kiểm soát bằng thứ tự việc**: §12.1 chỉ phát tác khi có ai đó nạp thẳng
   `data/embeddings/` sau một lượt chạy hỏng, mà §14.1 mục 2 đã buộc sinh lại gallery từ mã cuối
   trước khi bước 3.5 bắt đầu. Lỗi cũng không im lặng — mã trả về `1` kèm thông báo rõ ([16]).

Điều kiện của phán quyết 🟡: **§14.1 mục 2 phải chạy trước khi bất kỳ số nào từ `data/embeddings/` đi
vào bước 3.5**; và §12.1 nên được mở thành mã việc trước khi bước đó bắt đầu.

Ghi nhận về chất lượng vòng sửa: bản vá đúng đến từng dòng so với đoạn sửa đã chỉ định, không nới rộng
phạm vi sang tệp thứ ba, không đụng `src/recognizer/factory.py`, không thêm `except Exception`, và
docstring được cập nhật cùng nhịp với mã. Ba mục 🔵 mới đều là chỗ **tập test** chưa phủ kín, không
phải chỗ mã sản phẩm sai.
