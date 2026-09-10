# Review P0-05 — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P0-05-don-dep-nen-tang.md` |
| **Nhánh** | `feat/p0-05-don-dep-nen-tang` |
| **Mốc `dev`** | `187296d` (đỉnh `dev` lúc lấy mốc; đặc tả soạn ở `e4b7b85`) |
| **Ngày** | 2026-09-10 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — không còn 🔴 và 🟡; chỉ còn 🔵 góp ý. Được commit và gộp `dev` |

Phạm vi mã việc: năm khoản nợ kỹ thuật của `P0-04` — mặt nạ quyền ở nhánh dự phòng của `giai_nen`,
ca 37 chốt hành vi nhánh A với tên tuyệt đối, thông báo của hàm gác trọng số `.pt`, `--strict-config`,
và chú thích `ncnn` lỗi thời. Khoảng 5 dòng mã sản phẩm, 8 hàm test mới.

⚠️ **Phán quyết này KHÔNG bao gồm bằng chứng từ `pi5`** — xem §5 và §7.

---

## 1. Kết quả kiểm máy

**Người dùng chạy ngày 2026-09-10.** Lệnh chép nguyên văn dưới đây; mọi con số đều đến từ lượt chạy
của người dùng, không từ bảng `coder` dán về (R42 · `code-review.instructions.md` §1).
Người review không chạy lệnh nào.

### 1.1. Phạm vi thay đổi

| # | Lệnh | Kết quả |
|---|---|---|
| [1/30] | `git status --short --untracked-files=all` | đúng **6 dòng `M`**: `pyproject.toml`, `scripts/download_lfw.py`, `tests/test_cau_hinh_pytest.py`, `tests/test_download_lfw.py`, `tests/test_export_detector.py`, `tests/test_export_detector_ncnn.py`. Không dòng thứ bảy ✅ |
| [2/30] | `git diff --numstat dev` | 6 tệp: `1/1`, `13/2`, `72/5`, `82/0`, `24/4`, `17/10` — cột "bớt" của `tests/test_download_lfw.py` bằng **0** ✅ |
| [3/30] | `git status --short` lọc `\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$` | **rỗng** ✅ |

Không có `requirements.txt`, `deploy/Dockerfile.arm64`, `src/`, `configs/`, `docs/`, `results/`,
`report/`, `CLAUDE.md`, `scripts/chinh-cam.py` trong `numstat`. Sáu tệp là **tập con đúng bằng**
danh sách trắng §2 đặc tả → **không có CHẶN-A-5**. R43 được tôn trọng: không có lý do dựng lại
`faceid:arm64`.

### 1.2. Mốc trước khi sửa và phép trừ

| Môi trường | Lệnh | Mốc tại `187296d` | Sau mã việc | Hiệu |
|---|---|---|---|---|
| `pc_x86` | `pytest -q` | `870 passed` | `875 passed, 3 skipped` | **+8** ca thu thập (`875 + 3 = 878 = 870 + 8`) |
| `docker_arm64` | `pytest -q -m "not slow"` | `837 passed, 1 skipped, 32 deselected` | `845 passed, 1 skipped, 32 deselected` | **+8** `passed`; `skipped`/`deselected` **không đổi** |

Đúng kỳ vọng §3.3 và §11 [4]/[7] đặc tả: **phép trừ bằng 8 ở cả hai môi trường**, khớp với 8 hàm
test mới. Phân bổ trên `pc_x86`: `passed` +5 (ca 37, 52, 53, 54, 55), `skipped` +3 (ca 49, 50, 51
bị người gác POSIX chặn trên Windows) — đúng bảng §11 [4].

### 1.3. Ba lệnh nền, container, môi trường

| # | Lệnh | Kết quả |
|---|---|---|
| [4/30] | `black --check --line-length 100 src tests scripts` | `All done! 51 files would be left unchanged.` ✅ |
| [5/30] | `ruff check src tests` | `All checks passed!` ✅ |
| [6/30] | `ruff check src tests scripts` | `Found 4 errors.` — **cả bốn ở `scripts/chinh-cam.py`**, tệp **ngoài** `numstat` ⚠️ xem 🔵-2 |
| [7/30] | `python -VV` | `Python 3.12.5 (tags/v3.12.5:ff3bc82, Aug 6 2024, 20:45:27) [MSC v.1940 64 bit (AMD64)]` |
| [8/30] | `pytest -q` (host) | `875 passed, 3 skipped, 15 warnings in 208.83s` — 0 failed, 0 errors ✅ |
| [9/30] | `pytest -q -m "not slow"` (host) | `843 passed, 3 skipped, 32 deselected, 3 warnings in 61.81s` ✅ |
| [10/30] | `pytest tests/test_download_lfw.py tests/test_export_detector.py tests/test_cau_hinh_pytest.py -q -rs` | `96 passed, 3 skipped, 11 warnings in 29.60s`, kèm `SKIPPED [3] tests\test_download_lfw.py:631: bit quyền chỉ có ý nghĩa trên POSIX` ✅ |
| [11/30] | `MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q -m "not slow"` | `845 passed, 1 skipped, 32 deselected, 1 warning in 719.29s` ✅ |

Kiểm chéo §11 [5] đặc tả bằng chính hai lượt [8]/[9]: `843 + 3 + 32 = 878` bằng đúng tổng thu thập
của [8] (`875 + 3`) → bộ lọc marker chỉ đổi cách phân loại, **không** đổi tập ca; `skipped` của [9]
bằng `skipped` của [8] → không ca mới nào mang dấu `slow`. §11 [6] đòi tổng 99 ca (`44 + 48 + 7`) —
[10] cho `96 + 3 = 99` ✅.

Ba ca `skipped` trên Windows là 49, 50, 51 và mang **đúng chuỗi lý do** mà §10.1 ràng buộc 1 quy
định — điều này quan trọng: nó chứng minh ba ca đó skip vì người gác nền tảng, không phải vì một
lỗi import hay một fixture hỏng.

### 1.4. Quét mẫu

| # | Lệnh | Kết quả | Kỳ vọng đặc tả |
|---|---|---|---|
| [12/30] | `Select-String "export_detector.py trước" tests/test_export_detector.py` | **0 dòng** | [G1] = 0 ✅ |
| [13/30] | `Select-String "models/README.md" tests/test_export_detector.py` | **2 dòng** — `:49`, `:599` | [G2] = 1 ❌ *lệch — xem 🔵-1* |
| [14/30] | `Select-String "_bo_qua_neu_thieu" tests/test_export_detector.py` | **3 dòng** — `:42`, `:82`, `:598` | [G3] = 2 ❌ *lệch — xem 🔵-1* |
| [15/30] | `Select-String "0o755\|_MASK_QUYEN_AN_TOAN\|mode &=" scripts/download_lfw.py` | **2 dòng** — `:103` khai báo hằng, `:165` áp mặt nạ (sau `else:` ở `:151`) | [G4] = 2 ✅ |
| [16/30] | `Select-String "^import\|^from" scripts/download_lfw.py` | chỉ thư viện chuẩn + `src.common.{config,exceptions,logging}`; **không dòng nào được thêm** | [G5] không đổi ✅ |
| [17/30] | `Select-String "sudo" scripts/download_lfw.py` | **1 dòng** — chú thích ý 3 của §5.3 | [G8] = 1 ✅ |
| [18/30] | `Select-String "strict-markers\|strict-config" pyproject.toml` | **1 dòng** — `:13 addopts = ["--strict-markers", "--strict-config"]` | [G6] = 1, cả hai cờ ✅ |
| [19/30] | `Select-String "requirements.txt\|ncnn\|ultralytics\|torch" tests/test_export_detector_ncnn.py` | mọi dòng khớp nằm trong docstring hoặc `importorskip`; **không dòng nào nói `ncnn` vắng mặt** | [G7] ✅ |
| [20/30] | `git diff dev -- tests \| Select-String '^\+def test_', '^-def test_', '^\+.*pytest\.mark\.slow'` | **8** dòng `+def test_` (52, 53, 54, 37, 49, 50, 51, `test_dong55`); **0** dòng `-def test_` | 8 hàm mới, 0 hàm xoá ✅ |
| [21/30] | quét `assert True` / `except:` / `except Exception` trên ba tệp test | 3 dòng `assert True` **đều nằm trong chuỗi `write_text`** ghi ra tệp test **con** (`test_cau_hinh_pytest.py:83`, `:101`, `:135`); không `except:` trần | Không có CHẶN-B-6 ✅ |

⭐ Về [20/30]: dòng thứ chín khớp mẫu `slow` là một dòng **docstring** của `test_export_detector_ncnn.py`
bị hiển thị lỗi mã hoá (`dß║Ñu @pytest.mark.slow; fixture…`) — **dương tính giả của phép quét**, không
phải dấu `slow` mới. Ghi lại để lượt sau không phán nhầm.

⭐ Về [21/30]: ba dòng `assert True` là **dữ liệu đầu vào** cho tiến trình `pytest` con, không phải
assert của ca thật. Phân biệt này quyết định: nếu chúng là assert thật thì đây là CHẶN-B-6. Đã đọc
`tests/test_cau_hinh_pytest.py:82-85`, `:100-103`, `:134-135` xác nhận cả ba đều nằm trong tham số
của `Path.write_text`.

### 1.5. Bảy phép đột biến

Mỗi phép đủ bốn bước sao lưu ra ngoài kho → sửa → chạy → khôi phục; sau khôi phục `numstat` khớp
đúng dòng tương ứng ở [2/30].

| # | Phép phá | Chạy ở | Ca đặc tả đòi đỏ | Ca thật sự đỏ | Tổng kết lượt |
|---|---|---|---|---|---|
| [22/30] ĐB1 | xoá dòng áp mặt nạ ở nhánh B | `docker_arm64` | 49 | **49** — `AssertionError: assert (35309 & 3584) == 0` | `1 failed, 43 passed` ✅ |
| [23/30] ĐB2 | mặt nạ `0o000` | `docker_arm64` | 51 | **51** — `AssertionError: assert (32768 & 256) != 0` | `1 failed, 43 passed` ✅ |
| [24/30] ĐB3 | ép luôn đi nhánh B | `pc_x86` | 37 | **37** — `LoiCauHinh: Tệp nén chứa đường dẫn vượt ra ngoài thư mục đích` | `1 failed, 40 passed, 3 skipped` ✅ |
| [25/30] ĐB4 | xoá `--strict-config` khỏi `addopts` | `pc_x86` | 52 | **52** — `assert '--strict-config' in ['--strict-markers']`; ca 53, 54 **vẫn xanh** | `1 failed, 6 passed` ✅ |
| [26/30] ĐB5 | `testpaths` → `testpath` | `pc_x86` | cả lượt dừng | **cả lượt dừng** — `ERROR: Unknown config option: testpath`, `no tests ran in 6.07s`, `EXITCODE=4`, 0 ca thu thập | ✅ |
| [27/30] ĐB6 | thông báo hàm gác về câu cũ | `pc_x86` | 55 | **`test_dong55_...`** — `assert 'models/README.md' in '… chạy scripts/export_detector.py trước'` | `1 failed, 47 passed` ✅ |
| [28/30] ĐB7 | áp mặt nạ **sau** `tf.extractall(dich)` | `docker_arm64` | 49 | **49** — `st_mode=35309` tức `0o104755`, bit setuid còn nguyên trên đĩa; ca 50, 51 **vẫn xanh** | `1 failed, 43 passed` ✅ |

**Đọc kết quả — ba phép có sức nặng riêng:**

- **ĐB7** dựng lại đúng một cài đặt sai **tự nhất quán**: hằng có tên đúng, mặt nạ đúng giá trị, dòng
  nằm trong nhánh B, chỉ sai thời điểm. Nó đỏ ca 49 → giả định của §5.2 ràng buộc 4 (`getmembers()`
  trả về chính các đối tượng `TarInfo` mà `extractall` dùng) **có bằng chứng máy**, và ca 49 canh
  đúng hiệu quả trên đĩa chứ không canh sự tồn tại của một dòng mã.
- **ĐB4** chứng minh ba ca 52/53/54 canh **ba thứ khác nhau** đúng như §8.3 lập luận: bỏ cờ khỏi kho
  làm 52 đỏ trong khi 53/54 vẫn xanh vì chúng chạy trên cấu hình tạm.
- **ĐB5** cho thấy hình dạng thật của lỗi mà `--strict-config` chặn: **cả lượt chạy dừng với mã thoát
  `4`**, không phải vài ca đỏ. Đúng thứ §8.1 "phản đối đã cân" mô tả, nay không còn là bất ngờ.

**Bảy trên bảy phép đúng y dự đoán — có đáng nghi không?**
`coder-handoff.prompt.md` §2 xếp "phép đột biến nào cũng đúng y dự đoán" vào cột đáng nghi. Phán ở
đây: **không phải dấu hiệu xấu, nhưng cũng không phải bảo đảm mạnh như con số 7/7 gợi ra.** Lý lẽ:

1. Bề mặt mã sản phẩm của mã việc này là **hai dòng** (`:103` và `:165`) cộng một dòng cấu hình.
   Ba ca 49/50/51 nhắm thẳng vào hai dòng đó, ba ca 52/53/54 nhắm thẳng vào dòng cấu hình. Với bề mặt
   nhỏ như vậy, tỉ lệ trúng 7/7 là điều **nên** xảy ra, không phải điều bất thường.
2. Nhưng bảy phép này **do chính đặc tả liệt kê** (§13), và bảng ca kiểm thử (§10) cũng do chính đặc
   tả đó viết. Hai danh sách sinh ra từ một bộ óc thì phép đột biến chỉ chứng minh **ca canh đúng chỗ
   đặc tả đã nghĩ tới**, không chứng minh **không còn chỗ nào bị bỏ sót**. Đây là giới hạn của lượt
   này, ghi ra để không đọc quá con số 7/7.
3. Lượt này có bù bằng một phép **đọc mã ngoài danh sách đột biến**: §5.2 ràng buộc 1 đòi dòng áp mặt
   nạ nằm **trong nhánh B**, không nằm ở vòng quét chung `:139-141`. Ràng buộc này **không ca test nào
   bắt được** — chuyển dòng lên vòng quét chung sẽ áp mặt nạ cho cả nhánh A, mà nhánh A vốn đã làm
   sạch bit quyền nên ca 50 vẫn xanh. Đã kiểm bằng mắt thay cho máy: dòng `165` nằm sau `else:` ở
   `151` và trước `tf.extractall(dich)` ở `166`. Kết luận: ràng buộc đạt, nhưng nó là **ràng buộc vị
   trí mã**, chỉ giữ được bằng review, không giữ được bằng test — và điều đó là chấp nhận được vì
   vi phạm nó chỉ gây **thừa**, không gây sai.

---

## 2. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §2 Danh sách trắng (6 tệp) | ✅ đúng 6 tệp, không thừa một dòng — [1/30], [2/30] |
| §3.3 Số ca: **+8** mọi môi trường | ✅ host `870→878`, container `837→845` — §1.2 |
| §4 Tham số → config | ✅ không có tham số vận hành; hằng duy nhất `_MASK_QUYEN_AN_TOAN = 0o755` đặt ở `scripts/download_lfw.py:103` kèm chú thích nguồn, đúng bảng §4 |
| §5.2 ràng buộc 1 — dòng nằm trong nhánh B | ✅ `:165` sau `else:` ở `:151` (kiểm bằng mắt, xem §1.5) |
| §5.2 ràng buộc 2 — trước `extractall` | ✅ `:165` trước `:166`; ĐB7 là bằng chứng máy |
| §5.2 ràng buộc 3 — không thêm `import` | ✅ [16/30] |
| §5.2 ràng buộc 4 — không thêm `members=` | ✅ `tf.extractall(dich)` ở `:166` giữ nguyên; ca 49 canh giả định này |
| §5.2 ràng buộc 5 — chữ ký và ba hằng `_MSG_*` không đổi | ✅ `giai_nen(archive: Path, dich: Path) -> Path` ở `:106`, `_MSG_*` ở `:92-99` không đụng; ca 01–36 xanh nguyên |
| §5.3 Chú thích nhánh B nêu đủ ba ý | ✅ `:152-159` — nêu (1) kiểm chứa-trong-đích + mặt nạ, (2) không xử lý `uid`/`gid`, chủ ý, (3) không chạy bằng `sudo` |
| §6 Ca 37 | ✅ `tests/test_download_lfw.py:776-792`, dùng lại `_tao_tgz` với đúng chuỗi `"/tmp/thoat.txt"` của ca 32, người gác `hasattr(tarfile, "data_filter")` |
| §7 Việc 3 (5 yêu cầu) | ✅ đủ 5: đổi tên `_bo_qua_neu_thieu_weights_pt` giữ nguyên chữ ký; thông báo chứa `models/README.md`; không còn `export_detector.py`; **một** lời gọi ở `:82`, không thêm không bớt; docstring đầu tệp `:1-12` **giữ nguyên** |
| §8 Việc 4 | ✅ `pyproject.toml:13` chỉ đổi `addopts`; `testpaths`/`pythonpath`/`markers` không đụng; không thêm `filterwarnings` hay `-W error` |
| §8.3 Ba ca canh ba thứ khác nhau | ✅ chứng minh bằng ĐB4 |
| §9 Việc 5 (4 dữ kiện) | ✅ `tests/test_export_detector_ncnn.py:8-17` nêu đủ; `ncnn` đúng là ở `requirements.txt:9`; **chỉ sửa docstring**, `numstat` `17/10` toàn bộ nằm trong docstring |
| §10.1 Ca 37, 49, 50, 51 | ✅ đủ 4 hàm, assert khớp bảng; `_tao_tgz_voi_quyen` đúng chữ ký §10.1; ràng buộc 1–4 (gác POSIX theo `sys.platform`, dùng `setuid` chứ không `setgid`, ghi vào `tmp_path`, ca 50 cùng hàm dựng cùng tham số) đều đạt |
| §10.2 Ca 52, 53, 54 | ✅ đủ 3 hàm; `_chay_pytest_con` mở rộng bằng tham số **tuỳ chọn**, mặc định giữ nguyên hành vi → ca 47/48 không đổi một ký tự; cấu hình tạm đặt tên đúng `pyproject.toml`, tệp test truyền tường minh |
| §10.3 Ca 55 | ✅ `tests/test_export_detector.py:592-600`, đủ 55a và 55b |
| §10.4 Không ca nào đổi trạng thái | ✅ host: `skipped` từ 0 lên 3 và cả 3 là ca **mới**; container: `skipped` vẫn 1, `deselected` vẫn 32 |
| §14 Ràng buộc kỹ thuật | ✅ không cú pháp riêng 3.12 (`Path \| None` là 3.10+, `tomllib` 3.11+, `is_relative_to` 3.9+); test chỉ ghi `tmp_path`; không chạm mạng; `subprocess` chỉ gọi `sys.executable`; container xanh chứng minh không phụ thuộc `git`/`models/`/`docs/` |
| §15 Ngoài phạm vi | ✅ không đụng `tests/test_yolo_face.py`, không xử lý `uid`/`gid`, không tạo `requirements-pi.txt`, không sửa `CLAUDE.md` |
| §11 [2] `ruff check src tests scripts` sạch | ❌ `Found 4 errors` — **nguyên nhân nằm ngoài danh sách trắng**, xem 🔵-2 |
| §14b Lượt trên `pi5` | ⏳ **CHƯA CHẠY** — xem §5 |

**Hai điểm sống còn** (checklist rubric §6):

- **Trung thực số liệu (R5/R6)**: mã việc này không sinh con số nào đi vào `results/` hay báo cáo.
  Không có giá trị mặc định giả, không có số ví dụ trong docstring trông như kết quả đo. Hằng `0o755`
  là hằng an toàn của thư viện chuẩn, không phải tham số đo được. ✅
- **Fail-safe phần cứng (R22/R24)**: mã việc không chạm `src/actuator/**` lẫn `src/capture/**`.
  Không áp dụng. ✅

---

## 3. Lỗi phải sửa

**Không có 🔴 CHẶN-A, không có 🔴 CHẶN-B, không có 🟡 CẦN SỬA.**

Bốn khoản nợ của `P0-04` cộng khoản §14 đều đã đóng, mỗi khoản có ít nhất một ca kiểm thử và một
phép đột biến chứng minh ca đó nhắm đúng chỗ.

---

## 4. 🔵 Góp ý (không chặn — người dùng quyết định)

### 🔵-1 — Hai phép quét [G2]/[G3] của đặc tả đếm sai từ lúc soạn, **không phải lỗi cài đặt**

**Vị trí**: `docs/dac-ta/P0-05-don-dep-nen-tang.md:496` và `:501` (kỳ vọng 1 dòng và 2 dòng), mâu
thuẫn với chính `:354` và `:355` (§10.3) của cùng đặc tả.

Số đo: [13/30] cho **2** dòng, [14/30] cho **3** dòng.

Nguyên nhân đã truy được, và nó **không** nằm ở mã:

```python
# tests/test_export_detector.py:597-599 — do CHÍNH §10.3 đặc tả quy định từng ký tự
        _bo_qua_neu_thieu_weights_pt(tmp_path / "khong_co.pt")
    assert "models/README.md" in str(e.value)  # 55a — chỉ đúng đường
```

§10.3 bắt ca 55 gọi hàm gác (một dòng nữa khớp `[G3]`) và assert chuỗi `models/README.md` (một dòng
nữa khớp `[G2]`). Đặc tả **tự yêu cầu** hai dòng mà **chính nó cấm** ở §12. Số đúng phải là
`[G2] = 2` và `[G3] = 3`. Đây là mẫu mà checklist `spec-writer` gọi tên: *lệnh kiểm cấm một thứ thì
đừng cấm luôn cách phòng thủ trước thứ đó* — ca test canh chuỗi thì đương nhiên phải chứa chuỗi.

**Hậu quả nếu bỏ qua**: lượt kiểm sau đọc `[G2] ≠ 1` thành lỗi và trả lại một bản cài đặt đúng; hoặc
tệ hơn, người cài đặt né phép quét bằng cách viết assert vòng vo (ghép chuỗi từ hai mảnh như ca 47 đã
phải làm) làm ca kiểm thử khó đọc mà chẳng được gì.

**Sửa (cho `spec-writer`, ở mã việc sau, không phải ở đây)**: khi phép quét nhằm vào **mã sản phẩm**
mà tệp bị quét lại chứa cả ca kiểm thử, hãy loại trừ vùng ca test khỏi phép đếm thay vì hạ kỳ vọng
xuống một con số dễ sai. Ví dụ, đổi [G3] thành hai lệnh tách bạch:

```bash
grep -n "_bo_qua_neu_thieu" tests/test_export_detector.py | grep -v "^59[0-9]:"
```

hoặc đơn giản hơn và bền hơn: nêu kỳ vọng theo **vai trò** — "đúng một định nghĩa, đúng một lời gọi
trong hàm dựng, cộng các lời gọi trong ca kiểm thử mới" — rồi để người review đối chiếu bằng mắt.

### 🔵-2 — Bốn lỗi `ruff` ở `scripts/chinh-cam.py`: nợ có sẵn trên `dev`, **không chặn mã việc này**

**Vị trí**: `scripts/chinh-cam.py:1:1` (`N999 Invalid module name: 'chinh-cam'`), `:32:45`, `:33:58`,
`:34:44` (`RUF100 Unused noqa directive (non-enabled: E402)`).

Phán mức: **nợ có sẵn**, không phải lỗi của `P0-05`. Ba căn cứ:

1. Tệp **không** có trong `git diff --numstat dev` ([2/30]) — mã việc không chạm tới nó.
2. Tệp vào kho ở commit `961fa41` (`chore(cong-cu): chinh-cam vẽ khung bao…`), tức lỗi đã có trên
   `dev` trước khi nhánh này rẽ.
3. `scripts/chinh-cam.py` **ngoài danh sách trắng §2**. Nếu người cài đặt sửa nó, đó mới là lỗi —
   **CHẶN-A-5**. Đặc tả đặt người cài đặt vào thế không thể vừa đạt §11 [2] vừa giữ §2.

**Dạng lệnh nào là chuẩn**: `docs/quy-tac-cai-dat.md:254` chốt `ruff check src tests`, và
`code-review.instructions.md` §1 cũng vậy — lượt [5/30] cho `All checks passed!`, nên **ba lệnh nền
bắt buộc đều sạch**. Đặc tả `P0-05` §11 [2] tự mở rộng sang `scripts` mà không kèm cách xử lý phần
`scripts` vốn đã đỏ. Đề xuất: hoặc thống nhất mọi đặc tả về `ruff check src tests scripts` **sau khi**
`scripts/` đã sạch, hoặc giữ nguyên `src tests` như hiến pháp cài đặt và bỏ biến thể ba thư mục.
Không nên để hai dạng lệnh song song — mỗi lượt review lại phải giải thích lại chênh lệch này.

**Sửa (commit `chore` riêng, sau khi gộp `P0-05` — đúng như người dùng đã dự định)**: đổi tên tệp
thành `scripts/chinh_cam.py` (dấu gạch dưới) để tắt `N999`, và bỏ ba chỉ thị `# noqa: E402` ở `:32-34`
vì `E402` không nằm trong bộ quy tắc đang bật nên chúng vô tác dụng. Tách riêng khỏi mọi mã việc, vì
đây là công cụ chạy tay ngoài quy trình.

### 🔵-3 — Tên hàm ca 55 lệch quy ước **giữa các tệp**, nhưng đúng quy ước **trong tệp**

`tests/test_export_detector.py:592` đặt tên `test_dong55_gac_trong_so_pt_chi_dung_duong_dan`, trong
khi bảy ca mới còn lại dùng `test_37_`, `test_49_`…, `test_54_`.

Phán: **không phải lỗi.** Toàn bộ 47 hàm test có sẵn của chính tệp đó mang tiền tố `test_dong` —
từ `test_dong01_cau_hinh_hop_le_du_tam_khoa` (`:123`) tới `test_dong44_chon_mau_anh_thu_muc_rong`
(`:578`). Đặt `test_55_` vào đây mới là ca lạc lõng. Lời khai của `coder` ("đổi tên để tên hàm không
chứa chuỗi `_bo_qua_neu_thieu` mà `[G3]` quét") **không đúng với thực tế mã**: tên hàm ca 55 không hề
chứa chuỗi đó dù đặt kiểu nào, và [14/30] vẫn đếm ra 3 dòng. Kết quả cuối cùng thì đúng, chỉ có lý do
là sai — ghi lại để lượt sau không dựa vào lời khai đó.

**Góp ý cho `spec-writer`**: hai quy ước tên hàm test (`test_dongNN_` và `test_NN_`) đang cùng tồn tại
trong `tests/`. Chi phí thống nhất bây giờ là một lượt đổi tên hàng loạt trên ~800 ca — **không đáng**.
Chi phí để nguyên: mỗi đặc tả phải nói rõ "theo quy ước của tệp đang sửa". Đề xuất chọn vế thứ hai và
thêm đúng một câu đó vào `docs/quy-tac-cai-dat.md`.

### 🔵-4 — Docstring `tests/test_export_detector.py:7-11` mang **cùng lớp khuyết tật** với Việc 5

**Vị trí**: `tests/test_export_detector.py:8-9`

```
chúng (dòng 16, 17) — không bao giờ ở mức module (xem §10 đặc tả). Ba gói này không có
trong `requirements.txt`/container ARM64; import ở mức module làm `pytest` chết ngay khâu
```

Câu này sai với `onnxruntime`, vốn được ghim ở `requirements.txt:8` — đúng hình dạng của lỗi mà
Việc 5 vừa sửa cho `ncnn` ở tệp `_ncnn`. Đặc tả §7 điều 5 **cố ý** cấm chạm docstring này (để phép
đếm [G2]/[G3] chạy được), nên người cài đặt làm đúng khi để nguyên — rubric §5 xếp đây vào nhóm
"việc mà đặc tả cố ý để lại".

**Đề xuất**: gộp vào cùng mã việc với `tests/test_yolo_face.py:49-51` đã ghi ở §15 đặc tả — cả hai
đều là câu chữ lỗi thời trong tệp test, cùng một lượt sửa, một lượt review. Chi phí ~15 dòng.

### 🔵-5 — Assert 53b bắt được cả chuỗi đúng

**Vị trí**: `tests/test_cau_hinh_pytest.py:157`

```python
    assert "testpath" in kq.stdout + kq.stderr  # 53b
```

`"testpath"` là tiền tố của `"testpaths"`, nên assert này cũng xanh nếu một ngày nào đó thông báo lỗi
nhắc tới khoá **đúng**. Người cài đặt chép đúng từng ký tự assert mà §10.2 quy định, nên đây là góp ý
cho đặc tả chứ không phải lỗi. Rủi ro thực tế thấp: ĐB5 ([26/30]) đã dán nguyên văn
`ERROR: Unknown config option: testpath`, và ca 54 là cặp đối chứng.

**Sửa nếu muốn** (một dòng): `assert "Unknown config option: testpath" in kq.stdout + kq.stderr`.
Đổi lại, ca sẽ gắn với câu chữ của `pytest` và có thể vỡ khi nâng phiên bản — đó là lý do có thể chọn
**không** sửa. Người dùng quyết.

---

## 5. Điều lượt kiểm này **chưa** chứng minh

⚠️ **§14b — lượt trên Raspberry Pi 5 chưa chạy.** Đây là lượt của người dùng theo đúng phân vai
(R42), không phải thiếu sót của người cài đặt. Hệ quả cụ thể:

Mọi bằng chứng về nhánh B trong biên bản này đến từ `monkeypatch.delattr(tarfile, "data_filter")` —
tức nhánh B chạy vì bị **ép**, trên Python 3.11.16 (container) và 3.12.5 (host). `pi5` chạy Python
3.11.2, là **môi trường duy nhất trong dự án đi vào nhánh B một cách tự nhiên**. Chừng nào chưa có
lượt đó, chưa loại trừ được khả năng phép ép bằng `monkeypatch` che mất một khác biệt nào đó của
`tarfile` phiên bản 3.11.2.

Lượt còn thiếu, chép nguyên văn từ §14b đặc tả:

```bash
python3 -m pytest tests/test_download_lfw.py -q
```

Kỳ vọng: **44** ca thu thập, `39 passed, 5 skipped` — ca skip là 34, 35, 36, **37**, **50** (thiếu
`tarfile.data_filter` nên không có nhánh A để kiểm), và **ca 49, 51 phải `passed`**.

```bash
python3 -m pytest -q -m "not slow" 2>&1 | grep -i "PytestUnknownMark\|Unknown config option"
```

Kỳ vọng: **không dòng nào** — chứng minh `--strict-config` mới thêm không làm vỡ lượt chạy trên Pi.

Khi có kết quả, ghi tiếp vào **chính tệp này** dưới tiêu đề "Phụ lục — lượt `pi5`", không tạo tệp mới.

---

## 6. Ghi chú cho các đặc tả sau

- §11 [8] đặc tả dự kiến `git status` có **8 dòng** (6 `M` + 2 `??` là hai tệp `.docx` trong
  `docs/bao-cao-tuan/`). Thực tế [1/30] cho đúng **6 dòng**: hai tệp `.docx` nay đã được track.
  Không ảnh hưởng kết luận nào, nhưng đặc tả sau đừng chép lại phán đoán này — trạng thái untracked
  là thứ thay đổi theo thời gian, không nên chốt cứng vào kỳ vọng của một lệnh kiểm.
- Mốc `pc_x86` có lọc marker và mốc `pi5` vẫn là `[CHƯA ĐO]` ở `187296d`. Lượt này lách được bằng ba
  điều kiện nội tại của §11 [5] và chúng đủ dùng. Nhưng nếu mã việc sau lại cần phép trừ trên hai
  lệnh đó thì phải **đo mốc trước khi sửa**, không suy từ `870 − 32` (R5).

---

## 7. Việc tiếp theo

**Đã ĐẠT CÓ ĐIỀU KIỆN — được commit và gộp `dev`.** Đề xuất commit message:

```
feat(nen-tang): P0-05 làm sạch bit quyền nhánh dự phòng, bật --strict-config, sửa hai chú thích lỗi thời
```

Sau khi gộp, ba việc rời nhau, không việc nào chặn việc nào:

1. Chạy §14b trên Pi 5, ghi phụ lục vào chính biên bản này (§5).
2. Commit `chore(cong-cu):` riêng dọn bốn lỗi `ruff` ở `scripts/chinh-cam.py` (🔵-2).
3. Nếu người dùng đồng ý 🔵-4: một mã việc nhỏ gộp `tests/test_yolo_face.py:49-51` (§15 đặc tả) với
   docstring `tests/test_export_detector.py:7-11`.

Phase 0 sau mã việc này còn thiếu đúng **lượt `pi5`** trước khi tổng kết lại ở Cổng D.
