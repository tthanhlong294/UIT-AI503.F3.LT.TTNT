# Review P2-06c — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P2-06c-git-dirty-dung-pham-vi.md` (commit `85a12ed`) |
| **Nhánh** | `feat/p2-06c-git-dirty` (mã **chưa commit** lúc review) |
| **Ngày** | 2026-09-04 |
| **Phán quyết** | 🟡 **ĐẠT CÓ ĐIỀU KIỆN** — 0 lỗi 🔴 CHẶN-A, 0 lỗi 🔴 CHẶN-B, 0 lỗi 🟡 CẦN SỬA, 6 mục 🔵 GÓP Ý. **Được commit ngay**, không có việc nào phải sửa. |

**Nguồn số liệu**: toàn bộ con số trong biên bản này đến từ **lượt chạy của người dùng ngày 04/09/2026**,
gồm 42 lệnh `K01`–`K42` do người review soạn. Không con số nào lấy từ bảng tự kiểm của người cài đặt
(R5, R6, `code-review.instructions.md` §0 và §2b). Mỗi dữ kiện dưới đây dẫn mã lệnh `[Kxx]` đã sinh ra
nó; lệnh được chép nguyên văn để chạy lại được mà không cần tệp kịch bản.

Môi trường lượt chạy: `pc_x86` — Windows, PowerShell 5.1; container `faceid:arm64` qua Docker Desktop
bind-mount, **không dựng image mới** (R43).

**Vì sao mã việc này đáng soi kỹ hơn mức bình thường**: đoạn mã được chấm chính là đoạn quyết định cờ
`git_dirty` của **mọi lượt đo sau**, kể cả các lượt trên Raspberry Pi 5 kết luận sáu chỉ tiêu cam kết ở
CLAUDE.md §1. Sai theo hướng **quá chặt** chỉ gây phiền; sai theo hướng **quá lỏng** thì số liệu không
truy vết được vẫn lọt vào báo cáo mà không ai biết — vi phạm R17 và R6 một cách âm thầm. Lượt kiểm định
này vì vậy ưu tiên soi hướng lỏng, và đó là lý do có thêm nhóm lệnh D (git thật) và phép đột biến ĐB2b
ngoài §7 đặc tả.

---

## 1. Kết quả kiểm máy

### A. Ba lệnh nền trên host

| # | Lệnh | Kết quả |
|---|---|---|
| [K01] | `python -m black --check --line-length 100 scripts/benchmark_detect.py tests/test_benchmark_detect.py` | `2 files would be left unchanged.` ✅ |
| [K02] | `python -m ruff check scripts/benchmark_detect.py tests/test_benchmark_detect.py` | `All checks passed!` ✅ |
| [K03] | `python -m pytest tests/test_benchmark_detect.py -v -m "not slow"` | **72 passed**, 0 failed, 5,61 s ✅ — khớp đúng dự kiến (63 ca theo mốc `P2-06b` + 9 ca mới). **Đây là mốc so sánh của cả bốn phép đột biến.** |
| [K04] | `python -m pytest -q -m "not slow"` | **462 passed, 14 deselected**, 0 failed, 11,86 s ✅ — khớp mốc `P2-06b` (453) + 9 |
| [K05] | `python -m pytest -q` | **476 passed**, 0 failed, 59,44 s ✅ — khớp mốc `P2-06b` (467) + 9 |

Chín ca mới xanh và mang đúng tên `test_dong59` … `test_dong67` `[K03]`, đúng quy ước đánh số nối tiếp
của §6 đặc tả:

```
test_dong59_chi_tep_moi_trong_results_thi_co_khong_bat
test_dong60_lenh_git_co_kem_pham_vi_duong_dan
test_dong61_sua_doi_trong_src_lam_co_bat
test_dong62_tep_moi_chua_theo_doi_trong_src_lam_co_bat
test_dong63_sua_doi_requirements_lam_co_bat
test_dong64_khong_chay_duoc_git_thi_gia_dinh_xau_nhat
test_dong65_toan_cay_goi_lenh_khong_kem_pham_vi
test_dong66_meta_co_ca_hai_khoa
test_dong67_hai_khoa_doc_lap_nhau
```

Ba con số `72`, `462`, `476` tự nhất quán với nhau và với mốc `P2-06b`: `476 − 462 = 14` ca `slow`,
và cả ba đều tăng đúng `+9` so với mốc — không có ca cũ nào bị xoá hay bị sửa để đi qua (CB-6 không
thành lập).

### B. Ba lệnh nền trong container `faceid:arm64` (R43 — không dựng image mới)

| # | Lệnh | Kết quả |
|---|---|---|
| [K06] | `docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m black --check --line-length 100 <2 tệp>` | `2 files would be left unchanged.` ✅ |
| [K07] | `docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m ruff check <2 tệp>` | `Found 2 errors.` — **cả hai là `EXE002 The file is executable but no shebang is present`**, ở `scripts/benchmark_detect.py:1:1` và `tests/test_benchmark_detect.py:1:1`, **không mã lỗi nào khác** ⚠️ artifact môi trường, **không tính lỗi của mã việc** — xem §1.1 |
| [K08] | `docker run --rm -v "D:/…/UIT-AI503.F3.LT.TTNT:/app" -w /app faceid:arm64 python3 -m pytest -q -m "not slow"` | **461 passed, 1 skipped, 14 deselected**, 0 failed, 875,57 s ✅ — khớp mốc `P2-06b` (452/1/14) + 9 ca mới. Ca skip là `test_dong30` (container không có `git` và không có `.git/`) |

#### 1.1. `EXE002` — vấn đề đã phân định dứt điểm, không mở lại

Biên bản `P2-06b` mục §1.1 và 🔵-1 đã kết luận bằng ba dữ kiện độc lập: git index để cả bốn tệp ở mode
`100644`; rule này đánh cả những tệp `.py` **ngoài** mã việc; `ruff 0.16.1` và `pyproject.toml` giống hệt
nhau ở hai bên. Biến duy nhất khác nhau là quyền tệp do Docker Desktop gắn ổ Windows với mode 0755.
Lượt này chỉ xác nhận triệu chứng tái diễn đúng như dự báo — **hai** lỗi cho **hai** tệp, không lỗi lạ nào
`[K07]`. Không điều tra lại; giữ nguyên ở mức 🔵 kế thừa (§4 mục 🔵-5).

#### 1.2. Chín ca mới xanh **cả trong container không có `git`** — một dữ kiện có ý nghĩa

`[K08]` cho 461 passed trong môi trường không có nhị phân `git`. Nếu ca nào trong chín ca mới lỡ gọi
`git` thật, nó đã phải skip hoặc đỏ ở đó. Xanh hết nghĩa là chúng thật sự giả lập `subprocess.run` và
không phụ thuộc môi trường — đúng ràng buộc §8 đặc tả ("script chạy trên Pi 5 không màn hình; không
import gì chỉ có trên máy phát triển") và đúng tinh thần `docs/quy-tac-cai-dat.md` về test chạy được
bằng backend giả. Mặt trái của chính dữ kiện này là §1.4 dưới đây.

### C. Phạm vi tệp và quét mẫu vi phạm

| # | Lệnh | Kết quả |
|---|---|---|
| [K09] | `git branch --show-current` | `feat/p2-06c-git-dirty` ✅ — đúng quy ước tên nhánh của mã việc (R30, §2.9) |
| [K10] | `git --no-pager log --oneline -5` | `85a12ed (HEAD -> feat/p2-06c-git-dirty, dev) docs(dac-ta): P2-06c…` · `56a3bd1 exp(detect): ma trận 12 ô ONNX vs NCNN, ba lượt trên máy phát triển` · `743640b Merge … P2-06b … into dev` · `c50789f feat(benchmark): … — P2-06b` · `64c8e8f docs(dac-ta): P2-06b…` — **`P2-06b` đã gộp**, nên K11 ra đúng 2 tệp là hợp lệ, không có dư âm mã việc trước |
| [K11] | `git status --short --untracked-files=all` | **đúng 2 dòng `M`**: `scripts/benchmark_detect.py`, `tests/test_benchmark_detect.py`. Không dòng `??` nào ✅ — khớp tuyệt đối danh sách trắng §3, **CA-5 không thành lập** |
| [K12] | `git --no-pager diff --stat` | `2 files changed, 224 insertions(+), 3 deletions(-)` — `benchmark_detect.py` 61 · `test_benchmark_detect.py` 166. Không có `configs/`, `src/`, `requirements*.txt`, `models/`, `notebooks/`, `.claude/` ✅ |
| [K13] | `git status --short --untracked-files=all \| Select-String -Pattern '\.(jpg\|jpeg\|png\|npy\|npz\|onnx\|pt\|pth\|env\|db\|sqlite3?)$'` | không in gì ✅ — **CA-4 không thành lập** |
| [K14] | `Select-String -Path 'scripts\benchmark_detect.py' -Pattern 'untracked-files'` | **không in gì** ✅ — lệnh quét bắt buộc của §7 đặc tả: mã sản phẩm không dùng cờ bỏ tệp chưa theo dõi. §5.1 xác nhận **bằng dữ kiện**, không bằng lời hứa |
| [K15] | `Select-String -Path <2 tệp> -Pattern 'except\s*:\|except Exception:\s*pass\|assert True\|import torch\|[A-Z]:\\\|/home/\|/Users/'` | không in gì ✅ — CB-4, CB-6, CA-9, đường dẫn tuyệt đối máy cá nhân: đều không thành lập |
| [K16] | `Select-String -Path 'scripts\benchmark_detect.py' -Pattern 'porcelain\|_chay_git_status\|pham_vi\|timeout='` | 7 dòng: `:359` `:360` `:367` `:372` `:373` `:374` `:400` `:414` — **không dòng nào chứa `timeout=`** (căn cứ của 🔵-3) |
| [K42] | `git status --short --untracked-files=all` (chạy lại sau cả bốn phép đột biến) | đúng 2 dòng `M`, không tệp `??` nào ✅ — cây làm việc trở về đúng bản người cài đặt bàn giao, không sót tệp đột biến, tệp thăm dò hay tệp sao lưu nào trong repo |

Chỉ số dòng dùng trong toàn biên bản lấy từ `[K16]`:

```
359 def _chay_git_status(pham_vi: tuple[str, ...]) -> bool:
372     lenh = ["git", "status", "--porcelain"]
373     if pham_vi:
374         lenh = lenh + ["--", *pham_vi]
400     return _chay_git_status(_DUONG_DAN_ANH_HUONG_PHEP_DO)
414     return _chay_git_status(())
```

### D. Hành vi `git` THẬT — nhóm lệnh quan trọng nhất của lượt này

| # | Lệnh | Kết quả |
|---|---|---|
| [K17] | `git status --porcelain -- src scripts configs requirements.txt requirements-dev.txt` | đúng **một dòng** ` M scripts/benchmark_detect.py`. **Không** có `tests/test_benchmark_detect.py` dù tệp đó đang sửa ✅ — pathspec thật sự lọc, và git chấp nhận pathspec nhiều đường dẫn sau `--` mà không báo lỗi |
| [K18] | `git status --porcelain -- duong_dan_khong_ton_tai_p2_06c; "exit=$LASTEXITCODE"` | đầu ra **rỗng**, `exit=0` ⚠️ — git **không** báo lỗi với pathspec không khớp gì. Căn cứ của 🔵-1 |
| [K19] | `New-Item -ItemType File -Path 'src\_probe_p2_06c_xoa_ngay.py' \| Out-Null` | không in gì (tệp thăm dò, xoá ở K21) |
| [K20] | `git status --porcelain -- src scripts configs requirements.txt requirements-dev.txt` | **hai dòng**: ` M scripts/benchmark_detect.py` **và** `?? src/_probe_p2_06c_xoa_ngay.py` ✅ — tiền đề của §5.1 đứng vững trước git thật |
| [K21] | `Remove-Item 'src\_probe_p2_06c_xoa_ngay.py' -Force` | không in gì |
| [K22] | `git status --short --untracked-files=all` | đúng 2 dòng `M` ✅ — tệp thăm dò đã sạch, không lọt vào repo |

Phân tích riêng của nhóm này ở §3.

### E–I. Bốn phép đột biến

`sha256` bản gốc `scripts/benchmark_detect.py` `[K25]`:
`51283C9FA37421E6DBF3F0214EFFD6E2253013D32BDBB9EFEB1DA71DB28EBA26`

Mã **chưa commit**, nên khôi phục dùng **bản sao lưu ngoài repo** `$env:TEMP\p2-06c-backup\` `[K23]` `[K24]`,
**không** dùng `git checkout`/`git restore`. Tệp đột biến ghi bằng
`[System.IO.File]::WriteAllText($p, $noiDung, (New-Object System.Text.UTF8Encoding($false)))` — không BOM,
tránh làm ca `ast.parse` đỏ giả như sự cố `P2-05`. Mỗi phép đều đủ bốn bước *sao lưu → sửa → xác nhận
đột biến đã ăn → chạy → khôi phục và đối chiếu `sha256`*, và mỗi chuỗi thay thế đều được đếm để chắc
chắn **khớp duy nhất một chỗ** (`so_lan_khop=1`), tránh đột biến lan ra ngoài ý định.

| Phép | Nội dung | Xác nhận đã ăn | Kết quả `pytest` | Ca đỏ | Khôi phục |
|---|---|---|---|---|---|
| **ĐB1** | `:400` → `_chay_git_status(())` — bỏ phạm vi, hỏi toàn cây `[K26]` `so_lan_khop=1` | `[K27]` hai dòng `400`, `414` cùng mang `_chay_git_status(())` | `[K28]` **6 failed, 66 passed** | `test_dong59` `test_dong60` `test_dong61` `test_dong62` `test_dong63` `test_dong67` | `[K29]` sha256 **trùng khít** ✅ |
| **ĐB2** | `:372` → `["git","status","--porcelain","--untracked-files=no"]; pham_vi = ()` `[K30]` `so_lan_khop=1` | `[K31]` dòng `372` mang cờ và `pham_vi = ()` | `[K32]` **6 failed, 66 passed** | cùng sáu ca, **có `test_dong62`** | `[K33]` sha256 **trùng khít** ✅ |
| **ĐB2b** ⭐ | `:374` → `["--untracked-files=no", "--", *pham_vi]` — giữ pathspec, **chỉ** thêm cờ `[K34]` `so_lan_khop=1` | `[K35]` dòng `374` mang cờ trước `--` | `[K36]` **1 failed, 71 passed** | **duy nhất `test_dong62`** | `[K37]` sha256 **trùng khít** ✅ |
| **ĐB3** | `:414` → `return _kiem_tra_git_dirty()` `[K38]` `so_lan_khop=1` | `[K39]` dòng `414` | `[K40]` **2 failed, 70 passed** | `test_dong65` và `test_dong67` | `[K41]` sha256 **trùng khít** ✅ |

Đối chiếu với bảng §7 đặc tả: ĐB1 yêu cầu **dòng 01, 02** đỏ → `test_dong59`, `test_dong60` đều đỏ ✅.
ĐB2 yêu cầu **dòng 04** đỏ → `test_dong62` đỏ ✅. ĐB3 yêu cầu **dòng 09** đỏ → `test_dong67` đỏ ✅.
Cả bốn lần khôi phục cho cùng một hash với `[K25]`, và `[K42]` xác nhận cây làm việc không còn dấu vết
nào của lượt kiểm định — đúng ràng buộc "người review không sửa code" (R41,
`code-review.instructions.md` §2b).

---

## 2. Đối chiếu đặc tả

### 2.1. Bảng tiêu chí nghiệm thu §6 — từng dòng, kèm lệnh đã chứng minh

| # | Yêu cầu §6 | Ca | Xanh | Đột biến chứng minh ca **nhắm đúng chỗ** | Kết luận |
|---|---|---|---|---|---|
| 01 | Chỉ tệp mới trong `results/` → `git_dirty` là `False` | `test_dong59` | `[K03]` | `[K28]` ĐB1 làm đỏ (`assert True is False`) | ✅ Đạt |
| 02 | Lệnh git được gọi **có kèm phạm vi** đường dẫn | `test_dong60` | `[K03]` | `[K28]` ĐB1 đỏ tại `assert '--' in ['git','status','--porcelain']`; `[K32]` ĐB2 đỏ tại `assert '--' in [...,'--untracked-files=no']` | ✅ Đạt |
| 03 | Sửa đổi trong `src/` → `True` | `test_dong61` | `[K03]` | `[K28]` ĐB1 đỏ (`assert False is True`) | ✅ Đạt |
| 04 | **Tệp mới chưa theo dõi trong `src/` → `True`** — ca canh §5.1 | `test_dong62` | `[K03]` | ⭐ `[K36]` ĐB2b làm đỏ **đúng một ca này, đúng một assert** — xem §3 | ✅ Đạt, bằng chứng sắc nhất của lượt |
| 05 | Sửa `requirements.txt` → `True` | `test_dong63` | `[K03]` | `[K28]` ĐB1 đỏ | ✅ Đạt |
| 06 | Không chạy được git → `True` | `test_dong64` | `[K03]` | — (đặc tả §7 không yêu cầu đột biến cho nhánh này) | ✅ Đạt |
| 07 | Hàm toàn cây gọi lệnh **không kèm** phạm vi | `test_dong65` | `[K03]` | `[K40]` ĐB3 đỏ (`assert False is True`) | ✅ Đạt |
| 08 | Meta có **cả hai** khoá | `test_dong66` | `[K03]` | — | ✅ Đạt; đọc mã: `:626-627` ghi vào dict `meta`, `:104-105` đưa cả hai vào `_KHOA_META_BAT_BUOC` nên `ghi_ket_qua` ném `LoiCauHinh` nếu thiếu |
| 09 | **Hai khoá độc lập nhau** — ca chốt | `test_dong67` | `[K03]` | ⭐ `[K40]` ĐB3 đỏ tại `assert meta["git_dirty_toan_cay"] is True` (dòng 1238) **sau khi** `assert meta["git_dirty"] is False` (dòng 1237) đã xanh | ✅ Đạt — ca kiểm được **cả hai vế** của tính độc lập, không chỉ một |
| 10 | Mọi ca cũ vẫn xanh | — | `[K03]` 72 = 63 + 9 · `[K05]` 476 = 467 + 9 | — | ✅ Đạt, không ca cũ nào bị sửa |

### 2.2. Bốn ràng buộc thiết kế §5 và giao diện §4

| Mục | Bằng chứng đọc mã (số dòng từ `[K16]`) | Bằng chứng chạy được | Kết luận |
|---|---|---|---|
| **§5.1** — giới hạn theo **đường dẫn**, KHÔNG bỏ tệp chưa theo dõi | `:372` dựng đúng ba tham số `["git", "status", "--porcelain"]` — không cờ nào lẩn vào; `:373-374` chỉ nối `["--", *pham_vi]`, tức pathspec **nằm sau `--`** nên git không hiểu `src` là tên nhánh; phạm vi lấy từ tuple `:66-72`; điểm gọi `:400` | `[K14]` không có `untracked-files` trong mã sản phẩm · `[K17]` pathspec thật sự lọc (`tests/` bị sửa nhưng không hiện) · `[K20]` tệp `??` trong `src/` **có** làm cờ bật trên git thật · `[K36]` ca dòng 04 bắt được cờ nếu ai đó thêm vào | ✅ **Đạt** |
| **§5.2** — không chạy được git thì trả `True` | `:384` bắt `(subprocess.CalledProcessError, OSError)`, `:385` log `warning` lazy formatting, `:386 return True`. `FileNotFoundError` (không có nhị phân `git`) là lớp con của `OSError` ✅; `check=True` `:380` biến mọi mã thoát khác 0 thành `CalledProcessError` ✅ — cả hai ngả về phía an toàn, đúng "nghi ngờ thì báo bẩn" | `[K03]` `test_dong64` xanh với `OSError` · `[K08]` container **không có `git`** mà 9 ca mới vẫn xanh, gián tiếp xác nhận nhánh fail-safe không làm sập gì | ✅ **Đạt**. `subprocess.TimeoutExpired` **không** nằm trong bộ ngoại lệ, nhưng mã cũng **không** truyền `timeout=` (`[K16]`) nên ngoại lệ đó không thể phát sinh — không phải lỗi sống, chuyển thành 🔵-3 |
| **§5.3** — **hai** lệnh git riêng, không tự phân tích chuỗi | `:400` và `:414` là hai lần gọi độc lập vào `_chay_git_status`; `:383` chỉ dùng `bool(ket_qua.stdout.strip())` — **không** tách dòng, không đọc ký tự trạng thái, không so tên tệp. Chỗ dễ sai lặng lẽ mà §5.3 cảnh báo (tên tệp có dấu cách, tệp đổi tên, Unicode bị git thoát) đã bị loại bỏ tận gốc | `[K40]` ĐB3 (ép hai hàm dùng chung một kết quả) làm đỏ 2 ca — chứng minh sự tách đôi này được bộ test canh, không phải tách cho đẹp | ✅ **Đạt** |
| **Dòng 09** — hai khoá độc lập, đều vào `.meta.json` | `git_dirty_toan_cay` **thật sự được ghi**, không phải tính rồi bỏ: `:627` đặt vào dict `meta`; `:104-105` đưa cả hai khoá vào `_KHOA_META_BAT_BUOC`, nên `ghi_ket_qua:320-322` ném `LoiCauHinh` nếu thiếu — không có đường nào ghi ra tệp mà thiếu khoá | `[K03]` `test_dong66`, `test_dong67` xanh · `[K40]` ĐB3 làm đỏ đúng ca chốt, tại đúng assert vế thứ hai | ✅ **Đạt** |
| **§4 Giao diện** | Tên và chữ ký khớp từng ký tự: `_DUONG_DAN_ANH_HUONG_PHEP_DO` là tuple 5 mục đúng thứ tự đặc tả `:66-72`; `_kiem_tra_git_dirty() -> bool` `:389`; `_kiem_tra_git_dirty_toan_cay() -> bool` `:403`. Docstring tiếng Việt kiểu Google, có `Returns:`. Hàm phụ `_chay_git_status(pham_vi: tuple[str, ...]) -> bool` `:359` **không có** trong §4 nhưng là chi tiết cài đặt nội bộ (tiền tố `_`), và chính nó là thứ hiện thực hoá §5.3 — không tính là lệch giao diện | `[K02]` `[K06]` lint sạch | ✅ **Đạt** |
| **§8 Ràng buộc** | Chỉ dùng `subprocess` thư viện chuẩn, không thêm gói `[K12]` không đụng `requirements*.txt`; không import gì chỉ có trên máy phát triển | `[K08]` chạy được trong container ARM64 | ✅ **Đạt** |
| **§9 Ngoài phạm vi** | Không sửa `experiment-protocol.instructions.md`, không chạy lại ba lượt đo, không đụng 🔵-4/🔵-6 của mã việc trước | `[K11]` `[K12]` đúng 2 tệp | ✅ **Đạt** — người cài đặt không làm thêm việc bị cấm |

---

## 3. ⭐ ĐB2b — phép đột biến ngoài §7, và vì sao nó cần thiết

**Phép này không có trong §7 đặc tả.** Người review tự thêm sau khi đọc mã, vì §7 chỉ yêu cầu "ĐB2 →
dòng 04 phải đỏ", mà kết quả của ĐB2 **không đủ để kết luận điều đó**.

**Vấn đề của ĐB2 một mình.** ĐB2 thay cả cụm phạm vi bằng cờ, nên nó đồng thời đổi **hai** thứ: lệnh git
mất pathspec, **và** lệnh git mọc thêm cờ. Trong bộ test, hàm giả `_gia_lap_git_status`
(`tests/test_benchmark_detect.py:1105-1114`) chọn đầu ra theo tiêu chí `"--" in lenh`. Mất pathspec nghĩa
là mọi ca đều nhận nhầm luồng đầu ra — nên `[K32]` cho **6 ca đỏ lẫn lộn**. Trong sáu ca đó, `test_dong62`
có đỏ, nhưng **không cách nào biết nó đỏ vì lý do gì**: vì nó bắt được cờ `--untracked-files`, hay đơn
giản vì đầu ra giả bị đổi luồng như năm ca kia. Nếu là lý do thứ hai thì ca dòng 04 **không** canh §5.1,
và một người sau này thêm cờ `--untracked-files=no` mà vẫn giữ pathspec sẽ đi lọt qua bộ test.

**ĐB2b tách bạch được.** Nó giữ nguyên pathspec và **chỉ** thêm cờ — tức là mô phỏng đúng người sửa sai
theo kiểu tinh vi nhất, thay vì thô bạo nhất:

```python
# :374 sau đột biến
        lenh = lenh + ["--untracked-files=no", "--", *pham_vi]
```

Kết quả `[K36]`: **1 failed, 71 passed**. Ca đỏ duy nhất là `test_dong62`, và nó đỏ tại **đúng assert
tham số**, không phải tại assert giá trị trả về:

```
tests\test_benchmark_detect.py:1169
    assert not any(
        tham_so.startswith("--untracked-files") or tham_so in {"-u", "-uno", "-unormal"}
        for tham_so in lenh
    )
E   assert not True
```

Ba điều rút ra, và cả ba đều là kết luận **không thể có** nếu chỉ chạy ĐB2:

1. Assert `bd._kiem_tra_git_dirty() is True` ở ngay phía trên **vẫn xanh** dưới ĐB2b — nghĩa là vế giá trị
   trả về không hề bắt được cách sửa sai này. Nếu ca dòng 04 chỉ có vế đó thì §5.1 sẽ không có ai canh.
2. Cái bắt được là **vế kiểm tham số** ở `tests/…:1169-1173`. Đây mới là nơi §5.1 được thi hành.
3. Assert đó còn phủ cả các dạng viết tắt `-u`, `-uno`, `-unormal`, tức là chặn cả đường vòng đặt cờ ngắn —
   một chi tiết vượt mức tối thiểu mà §6 dòng 04 đòi hỏi.

Nói cách khác: bộ test hỏi đúng câu hỏi mà mã việc này sinh ra để hỏi. Điều đó **không** suy ra được từ
việc suite xanh, cũng không suy ra được từ ĐB2 của đặc tả; nó chỉ được chứng minh bởi `[K36]`.

Ghi nhận cho `spec-writer`: **bảng §7 của các đặc tả sau nên ưu tiên phép đột biến phẫu thuật** — đổi
đúng một biến, kỳ vọng đúng một ca đỏ. Phép đột biến làm đỏ sáu ca cùng lúc chứng minh "có ai đó phản
ứng", chứ không chứng minh "đúng người phản ứng".

---

## 4. K17–K20 — chỗ duy nhất trong cả lượt kiểm định chạm vào `git` thật

**Khoảng trống cần lấp.** Cả chín ca mới đều giả lập `subprocess.run` (`tests/…:1116`). Đó là lựa chọn
đúng — nhờ vậy chúng chạy được trong container không có `git` `[K08]` — nhưng nó khiến bộ test **không thể**
kiểm chứng bất cứ điều gì về hành vi của git thật. Toàn bộ thiết kế §5.1 lại đứng trên hai giả định về
git thật, mà nếu sai thì cách sửa này thủng bất kể suite xanh bao nhiêu:

| Giả định của §5.1 | Nếu sai thì sao | Lệnh kiểm | Kết quả |
|---|---|---|---|
| `git status --porcelain -- <nhiều đường dẫn>` chạy được, lọc đúng, không báo lỗi | Cờ luôn `True` (quá chặt) hoặc script hỏng giữa lượt đo | `[K17]` | ✅ đúng một dòng ` M scripts/benchmark_detect.py`; `tests/test_benchmark_detect.py` **đang sửa nhưng không hiện** — lọc đúng |
| Tệp `.py` **mới chưa `git add`** trong `src/` **vẫn** làm cờ bật khi giới hạn bằng pathspec | Toàn bộ lập luận §5.1 sai: cách sửa này bỏ sót đúng tình huống mà nó tuyên bố bắt được, mà bộ test không biết | `[K19]`–`[K20]` | ✅ đầu ra có `?? src/_probe_p2_06c_xoa_ngay.py` bên cạnh dòng ` M` |

**Giả định thứ hai là điểm tựa của cả mã việc.** Đặc tả §5.1 bác cách sửa `--untracked-files=no` với lý do
"giới hạn theo đường dẫn vẫn bắt được tệp mới, vì tệp đó nằm trong `src/`". Câu đó là một **khẳng định
về hành vi của git**, không phải về mã Python — và trước `[K20]` nó chưa từng được kiểm chứng ở đâu, kể
cả trong lượt tự kiểm của người cài đặt. Nay đã có bằng chứng.

`[K18]` là lệnh dò theo chiều ngược lại và là lệnh duy nhất **tìm ra** một điều chưa ai biết — xem 🔵-1.

Tệp thăm dò được xoá ngay `[K21]` và cây làm việc xác nhận sạch hai lần `[K22]` `[K42]`; không lệnh nào
trong nhóm này ghi vào `results/`, `models/` hay `data/`.

---

## 5. Lỗi phải sửa

**Không có.** Không lỗi 🔴 CHẶN-A, không lỗi 🔴 CHẶN-B, không lỗi 🟡 CẦN SỬA.

Hai điểm sống còn mà `code-review.instructions.md` §6 buộc soi riêng:

- **Trung thực số liệu (R5, R17)** — mã việc này *tăng* độ trung thực chứ không giảm: nó gỡ một cờ báo
  động giả từng khiến hai trong ba lượt đo ngày 03/09 bị đánh dấu sai, đồng thời **không vứt bỏ thông tin**
  — trạng thái toàn cây được giữ nguyên ở khoá `git_dirty_toan_cay` `:627`. Không có giá trị mặc định giả,
  không có số ví dụ nào trong docstring có thể bị chép nhầm vào báo cáo.
- **An toàn phần cứng** — mã việc không đụng tới `src/actuator/**` hay bất kỳ đường chạy phần cứng nào
  `[K12]`. Không áp dụng.

---

## 6. 🔵 Góp ý (không chặn — người dùng quyết định)

### 🔵-1 — Pathspec sai chính tả thì git im lặng, không có tín hiệu nào

**Vị trí**: `scripts/benchmark_detect.py:66-72` (tuple) và `:372-374` (nơi dùng)
**Dữ kiện** `[K18]`:

```
git status --porcelain -- duong_dan_khong_ton_tai_p2_06c
exit=0
```

Đầu ra rỗng, mã thoát 0. `check=True` ở `:380` **không cứu được** vì git coi đây là trường hợp hợp lệ.
Hệ quả: nếu một mục trong `_DUONG_DAN_ANH_HUONG_PHEP_DO` bị gõ sai, hoặc thư mục bị đổi tên/di chuyển
trong một Phase sau, `_kiem_tra_git_dirty` sẽ trả **`False` — báo sạch** — mà không ngoại lệ, không log,
không cảnh báo. Đây đúng dạng hỏng nguy hiểm nhất với mã việc này: **lỏng và âm thầm**.

**Vì sao xếp 🔵 chứ không 🟡** — ba lý do, xếp theo trọng số:

1. **Không phải lỗi sống.** Cả năm đường dẫn hiện đều tồn tại trên đĩa; `[K17]` và `[K20]` cho thấy phạm vi
   đang hoạt động đúng. Không có `file:dòng` nào đang sai, mà quy tắc cứng của vai review là *không chỉ
   được dòng nào thì không phải lỗi*.
2. **Đặc tả §4 chốt cứng tuple này và §5 không yêu cầu kiểm tồn tại.** Người cài đặt làm **đúng** đặc tả.
   Trả lại mã ở Nhịp 3 vì một yêu cầu mà đặc tả không nêu là mở rộng đặc tả khi review — lấn sang vai
   `spec-writer`, và nếu đặc tả thiếu thì đó là lỗi của `spec-writer`, không phải của người cài đặt.
3. Rủi ro chỉ hiện thực hoá khi **ai đó sửa tuple trong tương lai** — tức là ở một mã việc sau, nơi việc
   bổ sung phòng vệ này thuộc về đúng phạm vi của nó.

Ghi nhận ngược lại, để người dùng cân: mã này quyết định cờ truy vết của **mọi lượt đo sau** (R17, R6),
và cái giá bịt lỗ rất rẻ. Vì vậy **đề nghị mở một mã việc riêng**, không để chìm:

> **`P2-06d` (đề xuất)** — bổ sung một ca test khẳng định mọi mục của `_DUONG_DAN_ANH_HUONG_PHEP_DO` tồn
> tại trên đĩa, hình dạng khoảng năm dòng, chạy được ở cả host lẫn container:
>
> ```python
> def test_moi_duong_dan_trong_pham_vi_deu_ton_tai():
>     goc = Path(bd.__file__).resolve().parents[1]
>     thieu = [p for p in bd._DUONG_DAN_ANH_HUONG_PHEP_DO if not (goc / p).exists()]
>     assert thieu == [], f"pathspec không khớp gì sẽ im lặng trả 'sạch': {thieu}"
> ```
>
> Ca này biến một khuyết tật âm thầm thành một ca test đỏ ngay khi cây thư mục lệch khỏi tuple. Cân nhắc
> gộp cùng 🔵-2 và 🔵-3 dưới đây thành một mã việc dọn dẹp nhỏ.

### 🔵-2 — Phạm vi không gồm `deploy/Dockerfile.arm64` và `pyproject.toml`

**Vị trí**: `scripts/benchmark_detect.py:66-72`
Đánh giá đã cân: `pyproject.toml` chỉ chứa cấu hình `black`/`ruff`/`pytest` — **không** ảnh hưởng số đo;
`models/` bị gitignore nên git không bao giờ báo được, đưa vào cũng vô nghĩa; `deploy/Dockerfile.arm64`
chỉ ảnh hưởng môi trường `docker_arm64`, vốn đã bị khai là **số tham khảo** không dùng kết luận chỉ tiêu,
còn số kết luận đo trên Pi 5 chạy bằng venv của host. Kết luận: **không thấy lỗ lỏng đủ mức chặn**, và
tuple hiện tại là lựa chọn hợp lý. Ghi lại để nếu sau này có lượt đo chính thức chạy **trong** container
thì xem lại `deploy/`.

### 🔵-3 — Không có `timeout=` cho lệnh `git`

**Vị trí**: `scripts/benchmark_detect.py:376-382` (và `_lay_git_commit_hash:346-352`, hành vi cũ)
`[K16]` xác nhận không dòng nào chứa `timeout=`. Hệ quả **không phải** cờ sai mà là **treo**: nếu `git` chờ
khoá `index.lock` hoặc chờ nhập thông tin xác thực, lượt đo trên Pi 5 không màn hình sẽ đứng vô hạn, và
người chạy chỉ thấy tiến trình im lặng giữa một phép đo hai phút. Kèm theo một cái bẫy cho người sửa sau:
`subprocess.TimeoutExpired` **không** thuộc `(CalledProcessError, OSError)` ở `:384`, nên ai thêm `timeout=`
mà quên mở rộng `except` sẽ biến nhánh fail-safe thành crash — ngược hẳn ý §5.2.
Không chặn: §5.2 không yêu cầu, và mã **giữ nguyên hành vi cũ** đúng như §8 đòi hỏi.
Nếu làm: thêm `timeout=10` và đổi thành `except (subprocess.SubprocessError, OSError)` — `SubprocessError`
phủ cả `CalledProcessError` lẫn `TimeoutExpired`.

### 🔵-4 — `monkeypatch.setattr(bd.subprocess, "run", …)` vá module dùng chung

**Vị trí**: `tests/test_benchmark_detect.py:1116`
`bd.subprocess` chính là module `subprocess` toàn cục, nên trong thời gian ca chạy, `subprocess.run` của
**cả tiến trình** bị thay, không riêng lời gọi của `benchmark_detect`. `monkeypatch` có hoàn tác nên không
rò rỉ giữa các ca, và `[K03]`–`[K05]` không cho thấy tác dụng phụ nào. Ghi nhận vì phạm vi vá rộng hơn cần
thiết; nếu sau này thêm ca chạy song song hoặc ca gọi tiến trình con thật, đây là chỗ đầu tiên nên nghi.

### 🔵-5 — `EXE002` trong container (kế thừa từ `P2-06b` 🔵-1)

Tái diễn đúng như dự báo `[K07]`. Đã phân định là artifact bind-mount Windows→Linux, không phải khuyết tật
mã. Sẽ tiếp tục tái diễn ở **mọi** mã việc sau cho tới khi người dùng chọn một trong hai hướng xử lý đã
nêu ở biên bản `P2-06b`. Mỗi lượt review sau lại tốn một dòng giải thích — đó là chi phí của việc chưa
quyết.

### 🔵-6 — Marker `slow` chưa đăng ký trong `pyproject.toml` (kế thừa)

`[K04]` `[K08]` đều kèm `15 warnings`, `[K05]` `27 warnings`. Đăng ký `markers = ["slow: …"]` trong
`[tool.pytest.ini_options]` là việc một dòng, đã nằm ở §9 đặc tả như mã việc dọn dẹp về sau — nhắc lại để
không quên.

---

## 7. Việc tiếp theo

Mã việc **không còn việc nào phải sửa**. Các bước sau thuộc **người dùng** — người duy nhất được
`git commit`/`push` (§2.9):

1. **Commit** hai tệp trong danh sách trắng `[K11]`:

   ```
   fix(benchmark): git_dirty chỉ xét mã nguồn ảnh hưởng phép đo, thêm git_dirty_toan_cay — P2-06c
   ```

2. **Gộp** `feat/p2-06c-git-dirty` vào `dev`.

3. ⭐ **Chạy §10b đặc tả với cây làm việc sạch** — đây mới là lúc khiếm khuyết gốc được chứng minh đã hết.
   Hai lượt liên tiếp, lượt B chạy khi thư mục đã có tệp kết quả của lượt A:

   ```bash
   python scripts/benchmark_detect.py --device-name "PC phát triển" --n-frames 100 --ghi-chu "kiểm P2-06c lượt A"
   ```

   ```bash
   python scripts/benchmark_detect.py --device-name "PC phát triển" --n-frames 100 --ghi-chu "kiểm P2-06c lượt B"
   ```

   Kết quả mong đợi: **cả hai** `.meta.json` có `git_dirty: false`, và riêng lượt B có
   `git_dirty_toan_cay: true` — đúng tình huống đã làm hỏng ba lượt đo ngày 03/09/2026. Hai lệnh này ghi
   vào `results/` nên **người dùng chạy**, không phải người review, không phải `coder` (§2.9).

4. Sau khi gộp: Claude cập nhật `experiment-protocol.instructions.md` §9 cho nói rõ điều kiện căn theo
   `git_dirty` phạm vi hẹp, đi **commit riêng** loại `chore(quy-trinh)` như §9 đặc tả đã định.

5. Quyết định về 🔵-1: mở `P2-06d` hay bỏ qua. Nếu mở, gộp luôn 🔵-3 và 🔵-6 vào cùng một mã việc dọn dẹp.
