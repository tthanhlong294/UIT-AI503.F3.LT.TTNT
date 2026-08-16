# Review P1-03-download-lfw — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-03-download-lfw.md` |
| **Nhánh** | `feat/p1-03-download-lfw` |
| **Ngày** | 2026-08-15 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — 1 lỗi CHẶN-B |

Tổng: **🔴 CHẶN-A: 0 · 🔴 CHẶN-B: 1 · 🟡 CẦN SỬA: 0 · 🔵 GÓP Ý: 5**

Mã nguồn sản phẩm gần như sạch: interface khớp từng ký tự, không hardcode, an toàn giải nén đúng,
tái lập được qua tiến trình. **Lỗi duy nhất nằm ở tệp test**, không nằm ở `scripts/download_lfw.py`.

---

## Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | đúng **2** file, cả hai trong danh sách trắng §2 ✅ |
| `git diff dev -- configs/ src/` | rỗng — không chạm `configs/data.yaml` ✅ |
| `black --check --line-length 100 src tests scripts` | 19 files unchanged ✅ |
| `ruff check src tests scripts` | All checks passed ✅ |
| `pytest -q` | **110 passed** (86 cũ + 24 mới) ✅ |
| `docker run ... faceid:arm64 pytest -q` | **110 passed in 7.56s** ✅ |
| `python scripts/download_lfw.py --help` | chạy được, mô tả tiếng Việt ✅ |
| `python scripts/download_lfw.py --dry-run` | thoát `0`, in kế hoạch, `data/` vẫn rỗng ✅ |
| `git status` sau `pytest` | không phát sinh tệp mới ✅ |

### Quét mẫu vi phạm §2 — sạch toàn bộ

`except:` trần · log f-string · đường dẫn tuyệt đối · secret · `assert True`/`pass` ·
float trần trong so sánh · `import torch`/RPi · file cấm lọt git — **không kết quả nào**.

### Ràng buộc §6 — tự chạy lại, không tin báo cáo

| Lệnh | Kết quả |
|---|---|
| `grep -nE "urlopen\|urlretrieve\|requests\.\|socket" tests/test_download_lfw.py` | rỗng ✅ |
| `grep -n "subprocess" tests/test_download_lfw.py` | rỗng ✅ |
| `grep -nE "^\s*(import\|from) (requests\|PIL\|imageio\|skimage\|pandas\|tqdm)" scripts/download_lfw.py` | rỗng ✅ |

Chỉ dùng thư viện chuẩn: `argparse csv datetime hashlib random shutil tarfile urllib`.

---

## Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §3 Interface (8 hàm) | ✅ khớp từng ký tự, kể cả giá trị mặc định `dry_run: bool = False` |
| §4 Config | ✅ 8/8 key đọc từ `configs/data.yaml`, không hardcode. `homepage` cũng đọc từ config (có sẵn trong file) dù bảng §4 không liệt kê |
| §4.1 Manifest 6 cột | ✅ đủ 6 cột, đúng nguồn giá trị |
| §4 CLI 5 cờ | ✅ đủ `--config --out --seed --expect-sha256 --dry-run` |
| §5 Ca biên 24 dòng | ⚠️ 24 ca, ánh xạ 1:1, mọi ca có assert thật — nhưng **dòng 24 không đi qua đường code cần kiểm** |
| §6 Nghiệm thu 11 mục | 10/11 ✅ (mục "mỗi ca có assert thật" đạt hình thức, hỏng thực chất ở ca 24) |
| §7 Quy tắc G1–G5, R15, R28c | ✅ `raise ... from e` ở 3 chỗ · `lay_logger` cho tiến trình · `print` chỉ cho bảng tóm tắt và trích dẫn · seed từ config |
| §8 Ngoài phạm vi | ✅ không lấn — không adapt miền, không detect/crop, không chia tập, không thanh tiến trình/đa luồng, dùng đúng bản `lfw.tgz` gốc |

### Quét AST — không có ca test rỗng

24/24 hàm `test_*` đều có `assert` hoặc `pytest.raises`. Không ca nào là vỏ rỗng.

---

## Kiểm bằng đột biến (§2b) — tự chạy, 9 phép

`sha256` gốc: `scripts/download_lfw.py` = `2a75fcde…4799`.
**Đã khôi phục và đối chiếu sha256 sau mỗi phép — khớp tuyệt đối.**

| # | Đột biến | Kỳ vọng | Kết quả thực tế |
|---|---|---|---|
| M1 | `filter="data"` → `filter="fully_trusted"` | đỏ dòng 5 | ✅ đỏ **đúng** `test_05`, 23 ca khác xanh |
| M2 | xoá khối `if dich.exists(): continue` trong `sao_chep` | đỏ dòng 16 | ✅ đỏ **đúng** `test_16` (`assert b'anh-id00-0' == b'DU_LIEU_CU'`) |
| M3 | `random.Random(seed)` → `random` toàn cục | đỏ dòng 9/10 | ✅ đỏ **đúng** `test_09`, **lặp 3 lần đều đỏ** (không phải may rủi) |
| M4 | vô hiệu hoá điều kiện `--expect-sha256` | đỏ dòng 24 | ❌ **VẪN XANH 24/24** → xem CHẶN-B-1 |
| M5 | xoá `if dry_run: continue` trong `sao_chep` | đỏ dòng 17 | ✅ đỏ đúng `test_17` |
| M6 | `return sorted(da_chon)` → `return da_chon` | — | ⚠️ vẫn xanh (xem GÓP Ý-1) |
| M7 | `len(anh) >= toi_thieu_anh` → `>` | đỏ dòng 11 | ✅ đỏ đúng `test_11` — biên `>=` **có** được kiểm |
| M8 | xoá guard "tệp đã tồn tại" trong `tai_ve` | đỏ dòng 21 | ✅ đỏ đúng `test_21` |
| M9 | vô hiệu hoá nhánh `--dry-run` của `main()` | đỏ dòng 23 | ✅ đỏ đúng `test_23` |

**8/9 phép định vị chính xác.** Bộ test có chất lượng cao — chỉ một lỗ thủng duy nhất, ở M4.

---

## Kiểm tính đúng đắn phần chọn danh tính (ảnh hưởng trực tiếp `FAR_lfw`)

Dựng phân bố mô phỏng LFW thật (5749 danh tính, lệch mạnh: 4069 người 1 ảnh, 1131 người 2 ảnh,
549 người 3–60 ảnh → 1680 danh tính hợp lệ khi `min_images_per_identity = 2`).

**1. Cùng seed → cùng tập danh tính, kể cả qua tiến trình khác nhau.**
Chạy 3 tiến trình riêng biệt với `PYTHONHASHSEED` = 0, 1, 12345 → hash kết quả **giống hệt**
(`abb8a8a9eec222af`). `sorted()` ở dòng 160 trước khi `sample` là thứ bảo đảm điều này: kết quả
không phụ thuộc thứ tự quét thư mục của hệ tệp. Đây là điểm cài đặt **đúng và quan trọng** —
R15 được thoả thực chất, không chỉ trên giấy.

**2. Loại đúng danh tính thiếu ảnh.** 100/100 danh tính được chọn đều có ≥ 2 ảnh, không trùng lặp,
đã sắp xếp. Biên `>=` được M7 chứng minh là có test.

**3. Không thiên lệch chọn.** Đây là rủi ro thật: nếu thuật toán ưu tiên danh tính nhiều ảnh
(như George_W_Bush với 530 ảnh trong LFW gốc) thì tập impostor bị lệch và `FAR_lfw` mất ý nghĩa.

| Phép đo | Kết quả |
|---|---|
| Số ảnh TB của nhóm hợp lệ (chuẩn) | 11.921 |
| Số ảnh TB qua 200 seed khác nhau | 12.021 (độ lệch chuẩn 1.659) |
| Chênh lệch | +0.100 = **+0.85 sai số chuẩn** → nhiễu lấy mẫu, không phải thiên lệch |
| Qua 2000 lần chọn: số danh tính từng được chọn | **1680/1680** — mọi danh tính hợp lệ đều có cơ hội |
| Tần suất xuất hiện | min 87, max 162, kỳ vọng 119 — phù hợp nhiễu nhị thức |

**Kết luận: `rng.sample` cho lấy mẫu đều, không thiên lệch. Phần sinh tập impostor đủ tin cậy để
làm nền cho `FAR_lfw` ở Phase 3.**

---

## Lỗi phải sửa

### 🔴 CHẶN-B-1 — `test_24` báo xanh nhưng không hề chạy qua nhánh `--expect-sha256` (CB-6)

**Vị trí**: `tests/test_download_lfw.py:347-358`, cụ thể dòng 352.

```python
def test_24_main_expect_sha256_lech(tmp_path):
    """main() với --expect-sha256 lệch thoát 1 (không cần mạng vì tệp nén đã có sẵn)."""
    cfg_path = _ghi_config_lfw(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    (cache_dir / "lfw.tgz").write_bytes(b"noi dung tep nen da co san")   # ← không phải tar hợp lệ
    ...
        assert main() == 1
```

**Vì sao**: chuỗi `b"noi dung tep nen da co san"` **không phải tệp tar hợp lệ**. `main()` đi tiếp
tới `giai_nen()` (`scripts/download_lfw.py:294`), hàm này ném `LoiCauHinh("Tệp nén hỏng…")`, bị bắt
ở dòng 315 và trả về `1`. Nghĩa là ca test xanh vì **tệp nén hỏng**, hoàn toàn không liên quan
đến mã băm.

Đã chứng minh bằng ba cách độc lập:

1. **Đột biến M4** — thay `if args.expect_sha256 and args.expect_sha256 != sha256_thuc_te:`
   (dòng 286) thành `if False:`, tức xoá sạch tính năng: **24/24 ca vẫn xanh.**
2. Chạy lại đúng kịch bản test **mà không truyền `--expect-sha256`** → `main()` vẫn trả `1`.
3. Chạy với `--expect-sha256` bằng **đúng mã băm thật** của tệp → `main()` **vẫn trả `1`**.
   Một ca test đúng phải trả `0` ở tình huống này.

Hậu quả: cờ `--expect-sha256` là chốt chặn duy nhất bảo đảm tệp `lfw.tgz` tải về đúng là bản
đã công bố. Cột `source_sha256` trong manifest — theo §4.1 là một trong hai cột làm tập dữ liệu
**tái lập được** — dựa vào chốt chặn này. Hiện tại nó có thể hỏng bất cứ lúc nào mà bộ test
vẫn báo xanh. Ngoài ra ca này còn thiếu assert cho yêu cầu "thông báo nêu cả hai giá trị" ở §5 dòng 24.

**Lưu ý quan trọng: mã sản phẩm KHÔNG sai.** `scripts/download_lfw.py:286-292` cài đặt đúng, log
đủ cả hai giá trị. **Chỉ sửa tệp test, không đụng vào `scripts/download_lfw.py`.**

**Sửa**: dựng tệp `.tgz` **hợp lệ** bằng chính helper `_tao_tgz` đã có sẵn (dòng 29), rồi khẳng định
cả hai chiều để chứng minh ca test đi đúng nhánh:

```python
def test_24_main_expect_sha256_lech(tmp_path, caplog):
    """main() với --expect-sha256 lệch thoát 1; khớp thì thoát 0 — chứng minh đi đúng nhánh."""
    cfg_path = _ghi_config_lfw(tmp_path)
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    archive = _tao_tgz(
        cache_dir / "lfw.tgz",
        {"lfw/A/a_0001.jpg": b"anh 1", "lfw/A/a_0002.jpg": b"anh 2"},
    )
    sha_that = hashlib.sha256(archive.read_bytes()).hexdigest()

    # Chiều 1 — mã băm lệch: thoát 1, thông báo nêu CẢ HAI giá trị (§5 dòng 24)
    with caplog.at_level(logging.ERROR):
        with patch(
            "sys.argv",
            ["download_lfw.py", "--config", str(cfg_path), "--expect-sha256", "0" * 64],
        ):
            assert main() == 1
    assert "0" * 64 in caplog.text and sha_that in caplog.text

    # Chiều 2 — mã băm khớp: thoát 0. Thiếu vế này thì ca test không phân biệt được
    # "lệch mã băm" với "tệp nén hỏng".
    with patch(
        "sys.argv",
        ["download_lfw.py", "--config", str(cfg_path), "--expect-sha256", sha_that],
    ):
        assert main() == 0
```

Thêm `import logging` vào đầu tệp test. `_ghi_config_lfw` đã đặt `min_identities=1` và
`min_images_per_identity=1` nên tệp nén 2 ảnh ở trên chạy lọt tới cuối.

**Đã kiểm chứng cách sửa này chạy đúng** trước khi viết vào biên bản: chiều lệch → `1` kèm log
`"Mã băm không khớp — kỳ vọng '000…' , thực tế '2b1c93bf…'"`; chiều khớp → `0`.

**Nghiệm thu lại**: sau khi sửa, chạy lại đột biến M4 (`if False:` ở dòng 286) — `test_24` **phải đỏ**.

---

## 🔵 Góp ý (không chặn — người dùng quyết định)

### GÓP Ý-1 — Yêu cầu "trả về danh sách đã sắp xếp" chưa có test

Đột biến M6 (`return sorted(da_chon)` → `return da_chon`, `scripts/download_lfw.py:170`) **vẫn xanh**.
Mã nguồn làm đúng, chỉ là không ai canh. Ảnh hưởng thấp: chỉ đổi thứ tự dòng manifest, không đổi
tập danh tính. Bảng §5 không có dòng nào cho yêu cầu này nên **không tính là thiếu test theo đặc tả**.
Chi phí bổ sung: một dòng `assert kq == sorted(kq)` ghép vào `test_12`.

### GÓP Ý-2 — `ghi_manifest` ghi âm thầm cột rỗng khi bản ghi thiếu khoá

`scripts/download_lfw.py:220` dùng `csv.DictWriter`, mặc định `restval=""`. Gọi
`ghi_manifest(p, sao_chep(...))` trực tiếp (bỏ bước bổ sung khoá ở `main()`) cho ra:

```
file,identity,n_images,source_sha256,selected_seed,timestamp
A/a.jpg,A,1,,,
```

Không lỗi, không cảnh báo — mà `source_sha256` và `selected_seed` chính là hai cột §4.1 gọi là
"làm cho tập dữ liệu tái lập được". Đề xuất: thêm một dòng kiểm ở đầu `ghi_manifest`, thiếu khoá
thì ném `LoiCauHinh`. Chi phí 3 dòng, đổi lấy việc không bao giờ sinh ra manifest mất dấu vết.

### GÓP Ý-3 — Chạy lại với `--seed` khác làm manifest lệch pha với thư mục

`sao_chep` bỏ qua tệp đã tồn tại (dòng 200) còn `ghi_manifest` ghi đè (dòng 219). Chạy lần hai với
seed khác: ảnh của 100 danh tính **cũ** vẫn nằm trong `out_dir`, nhưng manifest chỉ còn liệt kê 100
danh tính **mới**. Bất biến "1 dòng = 1 ảnh trong `out_dir`" (§5 dòng 20) gãy, và tập impostor
`FAR_lfw` lặng lẽ phình lên 200 danh tính. Đề xuất: `main()` đọc `selected_seed` của manifest cũ,
lệch seed thì dừng và yêu cầu `--force` hoặc dọn `out_dir`. Đây là việc **ngoài đặc tả hiện tại** —
nên mở mã việc riêng nếu người dùng thấy cần trước Phase 3.

### GÓP Ý-4 — `giai_nen` chưa phủ nhánh "nhiều thư mục gốc"

`scripts/download_lfw.py:113-116` trả về `dich` khi tệp nén có nhiều mục cấp một. `test_03` chỉ phủ
nhánh một gốc. Nhánh dự phòng này hỏng cũng không ai biết. Rủi ro thấp vì `lfw.tgz` thật chỉ có
một thư mục `lfw/`, và nếu rơi vào nhánh này thì `chon_danh_tinh` sẽ ném `LoiCauHinh` — **hỏng ồn
ào chứ không hỏng âm thầm**, đó là hành vi đúng.

### GÓP Ý-5 — `manifest.csv` nằm trong `out_dir` mà `n_images` đếm theo nguồn

`sao_chep` gán `n_images = len(anh_list)` (dòng 191) tức đếm ảnh **nguồn**, trong khi §4.1 ghi
"số ảnh… **đã sao chép**". Hai con số chỉ lệch nhau khi có tệp đích trùng tên bị bỏ qua — trường hợp
đó tệp vẫn nằm trong `out_dir` nên con số vẫn mô tả đúng thư mục. **Không phải lỗi**, chỉ nêu để
đặc tả sau dùng từ chính xác hơn.

---

## Đánh giá bốn chỗ người cài đặt phải suy diễn (đặc tả không nói rõ)

| Chỗ | Diễn giải của người cài đặt | Đánh giá | Đặc tả có cần sửa? |
|---|---|---|---|
| `giai_nen` trả thư mục gốc | Gom thành phần đường dẫn cấp một của mọi mục; **đúng một** giá trị phân biệt → trả `dich/<đó>`, ngược lại trả `dich` | ✅ **Hợp lý và cài đặt phòng thủ tốt.** Điều kiện lọc `if Path(tv.name).parts` xử lý đúng mục `./` mà tar hay chèn. Không có hậu quả xấu: rơi vào nhánh dự phòng thì `chon_danh_tinh` ném lỗi ồn ào | **Có** — §3 nên ghi thẳng quy tắc này thành một câu, kèm một dòng vào bảng §5 |
| `sao_chep` trả 3 khoá, `main()` bổ sung 3 | Tách theo thông tin sẵn có: `sao_chep` không nhận `seed` lẫn mã băm trong chữ ký | ✅ **Buộc phải thế** — chính chữ ký ở §3 quy định. Diễn giải duy nhất khả thi. Hậu quả duy nhất là bẫy cột rỗng ở GÓP Ý-2 | **Có** — §4.1 nên ghi rõ khoá nào do hàm nào sinh |
| `ghi_manifest` ghi đè (`w`) ≠ `P1-02` ghi nối (`a`) | Ghi đè một lần ở cuối phiên | ✅ **Hợp lý theo ngữ cảnh, KHÔNG phải thiếu nhất quán cần thống nhất.** Xem phân tích bên dưới | **Có** — nhưng chỉ để ghi lại *lý do*, không phải để đổi hành vi |
| Kiểm `--expect-sha256` không chạm mạng | Đặt sẵn tệp nén trong `cache_dir` để `tai_ve` thoát sớm ở nhánh "tệp đã tồn tại" | ⚠️ **Ý tưởng đúng, thực thi sai** — tệp mồi không phải tar hợp lệ nên `main()` chết trước khi tới nhánh cần kiểm → CHẶN-B-1 | **Có** — §5 dòng 24 nên nêu rõ tệp mồi phải là `.tgz` hợp lệ và phải khẳng định cả chiều khớp |

### Vì sao hai hành vi manifest khác nhau là hợp lý, không phải thiếu nhất quán

Hai script có **mô hình phiên chạy khác hẳn nhau**:

- `collect_faces.py` (P1-02) thu thập **tăng dần, nhiều phiên**: chốt sổ sau mỗi tư thế
  (`scripts/collect_faces.py:290`) và ghi nốt phần dở khi gặp ngoại lệ hoặc Ctrl+C (dòng 304).
  Mất dữ liệu đã chụp là mất công người ngồi trước camera → **bắt buộc ghi nối**.
- `download_lfw.py` (P1-03) sinh toàn bộ đầu ra trong **một lượt tất định**, từ một tệp nén cố định
  và một seed cố định. Nếu ghi nối, chạy lại lần hai sẽ **nhân đôi mọi dòng**, phá vỡ bất biến
  "số dòng dữ liệu = số ảnh trong `out_dir`" mà chính §5 dòng 20 dùng làm tiêu chí nghiệm thu.

Tức là ghi đè ở đây **được đặc tả gián tiếp yêu cầu**. Ép hai script dùng chung một hành vi sẽ làm
hỏng một trong hai. Khuyến nghị: **giữ nguyên**, chỉ bổ sung một câu vào docstring `ghi_manifest`
của cả hai script nêu rõ chế độ ghi và lý do, để mã việc sau không copy nhầm.

---

## Nhận xét chất lượng đặc tả

Đặc tả P1-03 **tốt trên mức trung bình của dự án**: bảng §5 24 dòng ánh xạ 1:1 ra 24 ca test, §6
đưa hẳn lệnh `grep` kiểm được bằng máy, §7 nêu thẳng hai điểm an toàn kèm lý do kỹ thuật
(`filter="data"`, đọc theo khối) — cả hai đều được cài đúng ngay vòng 1.

Điểm yếu duy nhất, và nó chính là nguyên nhân của lỗi CHẶN-B: **§5 mô tả *kết quả* mong đợi mà
không mô tả *tiền đề* của ca test**. Dòng 24 chỉ ghi `main() == 1`, mà `main()` có tới hai đường
dẫn tới giá trị `1` (mã băm lệch, và bất kỳ `LoiCauHinh` nào). Đặc tả chỉ chốt giá trị trả về thì
người cài đặt không có cách nào biết mình đang đo nhầm đường.

**Đề xuất cho `spec-writer`, áp dụng từ mã việc sau**: với mọi ca test mà hàm có nhiều đường dẫn
dẫn tới cùng một giá trị trả về, bảng §5 phải thêm một cột **"Tiền đề"** và yêu cầu **assert
phân biệt** — thường là khẳng định thêm chiều ngược lại (đầu vào hợp lệ → trả `0`). Bốn dòng §5
của mã việc này đáng lẽ phải có cột đó: dòng 13, 21, 23, 24.

---

## Việc tiếp theo

🔴 **TRẢ LẠI** — giao lại cho người cài đặt, phạm vi sửa **chỉ một tệp**:

> Sửa `tests/test_download_lfw.py:347-358` theo mục CHẶN-B-1 của
> `docs/review/P1-03-download-lfw.review.md`. **Không sửa `scripts/download_lfw.py`** — mã sản phẩm
> đã đúng. Thêm `import logging` vào đầu tệp test. Tự kiểm bằng đột biến: đổi dòng 286 của
> `scripts/download_lfw.py` thành `if False:`, `test_24` **phải đỏ**, sau đó khôi phục và đối chiếu
> `sha256` = `2a75fcde2b42e82b2c64b2f867262a366c689197d8fe2adf8a8753999bff4799`.
> Chạy lại: `black --check --line-length 100 src tests scripts`, `ruff check src tests scripts`,
> `pytest -q` (phải 110 passed).

Sau khi ĐẠT, commit gợi ý:

```
feat(scripts): P1-03 tai va chon loc bo du lieu LFW lam tap impostor
```

---
---

# Review P1-03-download-lfw — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-03-download-lfw.md` (đã sửa — §5 nay **30 dòng**, thêm §4.1 bảng khoá, §4.2 mới) |
| **Nhánh** | `feat/p1-03-download-lfw` |
| **Ngày** | 2026-08-16 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — còn **1 lỗi 🟡**, không còn lỗi 🔴 |

Tổng: **🔴 CHẶN-A: 0 · 🔴 CHẶN-B: 0 · 🟡 CẦN SỬA: 1 · 🔵 GÓP Ý: 4**

> Lỗi 🟡 duy nhất còn lại **không phải lỗi cũ tái diễn** — nó là yêu cầu **mới siết vào ở §5 dòng 4**
> của bản đặc tả vòng 2, và nó **không thể sửa bằng test**: mã sản phẩm phải đổi trước. Xem mục
> "Phán quyết về điểm mở".

---

## Trạng thái lỗi vòng 1

| Lỗi vòng 1 | Trạng thái |
|---|---|
| 🔴 CHẶN-B-1 — `test_24` không chạy qua nhánh `--expect-sha256` | ✅ **ĐÃ SỬA, đã xác minh lại bằng đột biến** |
| 🔵 GÓP Ý-1 — thiếu assert "đã sắp xếp" | ✅ đã nhận, gộp vào `test_12` (`kq == sorted(kq)`) |
| 🔵 GÓP Ý-2 — `ghi_manifest` sinh cột rỗng âm thầm | ✅ đã nhận, thành §4.1 + dòng 25/26 |
| 🔵 GÓP Ý-3 — chạy lại lệch seed làm phình tập impostor | ✅ đã nhận, thành §4.2 + dòng 27/27a/28 |
| 🔵 GÓP Ý-4 — nhánh "nhiều thư mục gốc" chưa phủ | ✅ đã nhận, ghi vào §8 là **cố ý không phủ** |
| 🔵 GÓP Ý-5 — chữ "đã sao chép" của `n_images` | ✅ §4.1 đã sửa thành "**có mặt trong `out_dir`** sau khi chạy" |

---

## Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | đúng **2** file mã nguồn (+ biên bản review) ✅ |
| `git diff dev -- configs/ src/` | rỗng ✅ |
| `black --check --line-length 100 src tests scripts` | 19 files unchanged ✅ |
| `ruff check src tests scripts` | All checks passed ✅ |
| `pytest -q` (host) | **116 passed** (86 cũ + 30 mới) ✅ |
| `docker run … faceid:arm64 pytest -q` | **116 passed in 9.67s** ✅ |
| `python scripts/download_lfw.py --dry-run` | thoát `0`, `data/` vẫn rỗng ✅ |
| Quét AST | **30/30** hàm `test_*` có assert thật, không hàm rỗng ✅ |
| Quét mẫu vi phạm §2 | sạch toàn bộ (except trần, log f-string, đường dẫn tuyệt đối, secret, `assert True`, float trần) ✅ |
| Ràng buộc §6 (mạng / `subprocess` / thư viện ngoài) | cả ba lệnh `grep` đều rỗng ✅ |

Số ca test **30 khớp đúng 30 dòng** bảng §5, ánh xạ 1:1 theo tên hàm.

---

## Kiểm bằng đột biến — 3 phép bắt buộc, tự chạy

`sha256` gốc `scripts/download_lfw.py` = `e85173ea13806233…6658`.
**Khôi phục và đối chiếu sau mỗi phép — khớp cả 3 lần.**

| Phép | Đột biến | Kỳ vọng | Kết quả thực tế |
|---|---|---|---|
| **MA** | `if args.expect_sha256 and … != sha256_thuc_te:` → `if False:` (dòng 318) | đỏ dòng 24 | ✅ **đỏ đúng `test_24`**, 29 ca khác xanh |
| **MB** | xoá khối kiểm khoá thiếu trong `ghi_manifest` (dòng 223-226) | đỏ dòng 25 | ✅ **đỏ đúng `test_25`**, 29 ca khác xanh |
| **MC** | xoá khối chặn lệch seed trong `main()` (dòng 330-337) | đỏ dòng 27 | ✅ **đỏ đúng `test_27` và `test_27a`**, 28 ca khác xanh |

**MA là phép quyết định của vòng này**: vòng 1 phép này **vẫn xanh** (lỗ hổng), vòng 2 **đỏ đúng chỗ**.
Lỗi CHẶN-B-1 đã được sửa thực chất, không phải sửa hình thức.

MC đỏ **hai** ca là đúng chứ không phải "lan man": dòng 27 kiểm mã thoát và thông báo, dòng 27a kiểm
dữ liệu cũ nguyên vẹn — cả hai đều thuộc chính cơ chế bị phá.

---

## Hai cơ chế mới có thực sự đóng được lỗ hổng không (không chỉ có test)

Chạy trực tiếp, không qua bộ test:

**① `ghi_manifest` với bản ghi chỉ có 3 khoá**

```
Đã ném LoiCauHinh: Bản ghi manifest thiếu khoá bắt buộc: source_sha256, selected_seed, timestamp
Tệp manifest có được tạo không? False
```

Nêu đủ **cả ba** khoá thiếu, và **không sinh tệp** — không còn manifest cột rỗng. Kiểm khoá đặt
**trước** khi mở tệp (dòng 223 trước dòng 229) nên không để lại tệp nửa vời. Lỗ hổng đã đóng ✅

**② `out_dir` có manifest seed cũ, chạy `main()` với seed khác**

Dựng tệp nén 3 danh tính A/B/C, `min_identities=2`:

```
Lần 1 seed=42 -> main()=0; danh tính: ['A', 'C']
Lần 2 seed=7  -> main()=1; danh tính: ['A', 'C']
Số thư mục không tăng? True | manifest không bị ghi đè? True
```

Thông báo nêu **cả hai seed** và chỉ rõ cách xử lý ("Dọn thư mục … trước khi chạy lại với seed khác").
Tập impostor **không** phình từ 2 lên 3 danh tính. Lỗ hổng đã đóng ✅
(Chi tiết đáng ghi nhận: seed 42 chọn `['A','C']` chứ không phải toàn bộ — chứng minh phép chọn thật
sự phụ thuộc seed, kịch bản kiểm có hiệu lực.)

---

## 🔎 Phán quyết về điểm mở — thông báo lỗi gộp của `giai_nen`

### Xác minh hiện trạng

Lời khai của người cài đặt là **chính xác**. Đã kiểm bằng máy:

```
MRO OutsideDestinationError: ['OutsideDestinationError', 'FilterError', 'TarError', 'Exception']
ReadError là con của TarError?  True
```

Chạy thật cả hai ca qua `giai_nen`:

```
DÒNG 4 (tệp hỏng)           : Tệp nén hỏng hoặc chứa đường dẫn không an toàn: …/hong.tgz
   nguyên nhân gốc: ReadError
DÒNG 5 (đường dẫn độc hại)  : Tệp nén hỏng hoặc chứa đường dẫn không an toàn: …/doc.tgz
   nguyên nhân gốc: OutsideDestinationError

Assert của test_04 ("hỏng" in msg) có đúng cho cả DÒNG 5 không?  True
```

⇒ Assert ở `tests/test_download_lfw.py:124` **không phân biệt được gì**, đúng như người cài đặt nêu.

### Ba câu hỏi — trả lời dứt khoát

**1. Lỗi cài đặt, lỗi đặc tả, hay chấp nhận được?**
→ **Lỗi cài đặt** (mức 🟡), **không phải** lỗi đặc tả. Yêu cầu ở §5 dòng 4 là **chính đáng và khả thi**:
Python cho sẵn `tarfile.FilterError` làm lớp cha riêng cho nhóm lỗi bộ lọc an toàn, tách bạch hẳn với
`ReadError`. Mã hiện tại gộp cả hai vào một `except tarfile.TarError` là **bỏ mất thông tin mà thư viện
chuẩn đã phân loại sẵn**. Đặc tả không đòi hỏi gì quá đáng.

**2. Có nên tách `except` thành hai nhánh không?**
→ **Có, dứt khoát nên tách** — và lý do vận hành mạnh hơn lý do hình thức:

| Tình huống | Bản chất | Phản ứng đúng |
|---|---|---|
| `ReadError` — tệp nén hỏng | Tải dở dang, đứt mạng, đĩa lỗi. **Lành tính, hay gặp** | Xoá tệp cache, tải lại |
| `FilterError` — mục `../../` | Tệp nén **độc hại** hoặc mirror bị chiếm. **Sự cố an ninh** | **Dừng hẳn**, không tải lại, kiểm nguồn tải và đối chiếu `sha256` công bố |

Thông báo hiện tại — *"Tệp nén hỏng hoặc chứa đường dẫn không an toàn"* — đẩy người vận hành vào chỗ
phải đoán. Và người ta sẽ đoán theo hướng phổ biến nhất: "chắc tải hỏng, tải lại phát nữa". Đó **đúng
là phản ứng sai nhất** cho trường hợp thứ hai. Gộp một sự kiện an ninh vào một lỗi lành tính là làm
mất tác dụng chẩn đoán của chính lớp phòng thủ `filter="data"` mà §7 đặc tả coi là điểm an toàn bắt buộc.

**3. Sửa mã sản phẩm hay hạ yêu cầu ở đặc tả?**
→ **Sửa mã sản phẩm. Không hạ đặc tả.** Chi phí 5 dòng, không thêm phụ thuộc, không đổi chữ ký hàm,
và `tarfile.FilterError` **có sẵn ở cả hai môi trường của dự án** — đã kiểm:

```
Host      : Python 3.12.5   FilterError: True
Container : Python 3.11.15  FilterError: True   (faceid:arm64)
```

**Đã thử bản vá và xác minh trước khi khuyến nghị** (sau đó khôi phục, `sha256` khớp gốc):

```
DÒNG 4: Tệp nén hỏng, không mở được
DÒNG 5: Tệp nén chứa đường dẫn vượt ra ngoài thư mục đích, đã chặn giải nén
Phân biệt được? True        Assert 'hỏng' còn dính nhầm dòng 5? False
pytest: 30 passed
```

Bản vá **giữ nguyên 30/30 ca xanh** và làm assert sẵn có của `test_04` trở nên có hiệu lực.

---

## Lỗi phải sửa

### 🟡 CẦN SỬA-1 — `giai_nen` gộp lỗi an ninh vào lỗi tệp hỏng, assert §5 dòng 4 vô hiệu (CS-4)

**Vị trí**: `scripts/download_lfw.py:108-109` và `tests/test_download_lfw.py:124`

```python
    except tarfile.TarError as e:
        raise LoiCauHinh(f"Tệp nén hỏng hoặc chứa đường dẫn không an toàn: {archive}") from e
```

**Vì sao**: `OutsideDestinationError` (mục `../../` — tệp nén độc hại) và `ReadError` (tải dở dang —
lành tính) đều là con của `TarError` nên rơi chung một nhánh, sinh **một chuỗi thông báo giống hệt
nhau**. Người vận hành gặp lỗi không biết nên tải lại hay dừng điều tra, và sẽ chọn tải lại — phản ứng
sai cho ca độc hại. Kéo theo: assert `"hỏng" in str(exc_info.value)` ở `test_04` cũng đúng với ngoại lệ
của dòng 5 (đã kiểm: `True`), nên **cột "Assert tối thiểu" của §5 dòng 4 chưa đạt**.

**Sửa** — hai phần, phải làm cả hai:

*(a)* `scripts/download_lfw.py`, thay khối `except tarfile.TarError` bằng hai nhánh, **`FilterError`
đặt trước** vì nó là lớp con:

```python
    except tarfile.FilterError as e:
        raise LoiCauHinh(
            f"Tệp nén chứa đường dẫn vượt ra ngoài thư mục đích, đã chặn giải nén: {archive}"
        ) from e
    except tarfile.TarError as e:
        raise LoiCauHinh(f"Tệp nén hỏng, không mở được: {archive}") from e
```

Giữ nguyên `except OSError` phía sau. Cập nhật mục `Raises:` của docstring cho khớp hai thông báo.

*(b)* `tests/test_download_lfw.py`, siết assert của **cả hai** ca để chúng loại trừ lẫn nhau:

```python
# test_04 — thêm vế phủ định để chứng minh không dính nhánh an ninh
assert "hỏng" in str(exc_info.value)
assert "vượt ra ngoài" not in str(exc_info.value)

# test_05 — hiện chỉ pytest.raises(LoiCauHinh); bổ sung:
assert "vượt ra ngoài" in str(exc_info.value)
```

**Nghiệm thu lại**: đổi `except tarfile.FilterError` thành `except tarfile.ExtractError` (lớp không
bắt được `OutsideDestinationError`) — `test_05` **phải đỏ**. Sau đó khôi phục, đối chiếu `sha256`.

---

## 🔵 Góp ý (không chặn — người dùng quyết định)

### GÓP Ý-1 — `_doc_seed_manifest_cu` làm `main()` thoát bằng ngoại lệ không bắt khi manifest hỏng

**Vị trí**: `scripts/download_lfw.py:249` — `return int(gia_tri)`

Ghi một manifest có `selected_seed` không phải số rồi chạy `main()`:

```
!!! THOÁT BẰNG NGOẠI LỆ KHÔNG BẮT: ValueError: invalid literal for int() with base 10: 'KHONG_PHAI_SO'
```

`main()` chỉ bắt `LoiCauHinh` (dòng 357) nên `ValueError` (và `OSError` nếu tệp không đọc được) lọt ra
ngoài, in traceback thay vì trả `1` như §3 công bố. **Không phải lỗi chặn**: §5 không có dòng nào cho
ca manifest hỏng, và hậu quả là *hỏng ồn ào* trước khi ghi gì — đúng tinh thần §4.2, dữ liệu vẫn an
toàn. Nhưng chính `_doc_seed_manifest_cu` là hàm đọc lại trạng thái **không đáng tin** từ đĩa, mà kịch
bản §4.2 nhắm tới lại đúng là "`out_dir` đang lộn xộn". Đề xuất: bọc thân hàm trong
`try/except (ValueError, OSError, csv.Error)` → `raise LoiCauHinh(...)`, và thêm một dòng vào §5.

### GÓP Ý-2 — Chặn lệch seed đặt sau khi đã tải và giải nén (điểm người cài đặt nêu)

**Vị trí**: `scripts/download_lfw.py:330`, nằm sau `tai_ve` → `tinh_sha256` → `giai_nen` → `chon_danh_tinh`.

**Đánh giá: đúng đặc tả, nhưng đáng chuyển lên sớm.** §3 chỉ yêu cầu "trước khi sao chép" và §4.2 nói
"dừng ngay" — vị trí hiện tại **thoả cả hai**, nên đây không phải lỗi.

Chi phí thật: lần chạy lại có `lfw.tgz` trong cache nên `tai_ve` thoát sớm, nhưng `tinh_sha256` vẫn
đọc hết ~180 MB và `giai_nen` vẫn bung lại ~13 000 tệp — hàng chục giây đến vài phút bị vứt đi trước
khi báo một lỗi đã biết chắc từ đầu. Cả `out_dir` lẫn `seed` đều đã có ngay sau khi đọc config
(dòng 293), nên khối chặn có thể đặt ngay trước `tai_ve` mà không cần thêm gì.

Đổi lại có một điểm cần cân nhắc: chuyển lên sớm thì lỗi lệch seed sẽ **che** lỗi `--expect-sha256`
khi cả hai cùng sai. Không nghiêm trọng, chỉ là thứ tự ưu tiên chẩn đoán. Người dùng quyết định.

### GÓP Ý-3 — Assert của `test_27` có thể khớp nhầm chữ số trong đường dẫn

**Vị trí**: `tests/test_download_lfw.py:470` — `assert "42" in caplog.text and "7" in caplog.text`

`caplog.text` chứa cả đường dẫn `tmp_path`, mà đường dẫn tạm thường có chữ số — `"7"` gần như chắc chắn
khớp kể cả khi thông báo không nêu seed. Ca test hiện vẫn có hiệu lực (đã chứng minh bằng đột biến MC),
nhưng để chắc chắn về lâu dài nên so cả dấu nháy như mã sản phẩm đang in:
`assert "'42'" in caplog.text and "'7'" in caplog.text`. Chi phí: 1 dòng.

### GÓP Ý-4 — `_doc_seed_manifest_cu` không nằm trong §3 (điểm người cài đặt nêu)

**Đánh giá: không có vấn đề gì.** §3 tên là "Interface **bắt buộc**" — sàn tối thiểu, không phải trần.
Hàm có tiền tố `_` (riêng tư), có type hint `Path -> int | None`, có docstring tiếng Việt kiểu Google
đúng G4, và chỉ được gọi từ `main()`. Đã có **tiền lệ trong chính dự án**: `scripts/collect_faces.py:155`
có `_lay_max_idx_da_co` cũng không nằm trong §3 của đặc tả P1-02, và đã qua review ĐẠT.

Tách hàm này ra là **quyết định đúng**: nó làm khối chặn lệch seed trong `main()` đọc được thành ba
dòng thay vì mười. Không cần đổi gì. Nếu muốn chặt chẽ hơn cho các mã việc sau, `spec-writer` có thể
thêm một câu vào mẫu đặc tả: *"§3 là sàn tối thiểu; hàm riêng tư `_ten` được phép thêm nếu có docstring
và được gọi từ hàm trong §3."*

---

## Trần 2 vòng — chẩn đoán

Hết vòng 2 **không còn lỗi 🔴**, nên trần 2 vòng **chưa bị chạm** (điều kiện dừng là còn 🔴).
Vẫn ghi nhận chẩn đoán để tránh hiểu nhầm là người cài đặt đang lặp:

| Quan sát | Chẩn đoán |
|---|---|
| Lỗi 🔴 vòng 1 đã sửa đúng, đột biến MA xác nhận | Không phải "sửa đúng chỗ nhưng sinh lỗi mới" |
| 5/5 góp ý vòng 1 được tiếp thu, không bỏ sót | Không phải "bỏ qua yêu cầu" |
| 🟡 còn lại sinh từ **yêu cầu mới** của bản đặc tả vòng 2 (§5 dòng 4 được siết) | **Không phải lỗi lặp.** Đây là vòng đầu tiên yêu cầu đó tồn tại |
| Người cài đặt **tự nêu** đúng điểm mở này thay vì giấu | Chất lượng bàn giao tốt — nên duy trì |

Nếu tính theo yêu cầu, `CẦN SỬA-1` mới đang ở **vòng 1 của chính nó**. Giao lại là hợp lý.

---

## Việc tiếp theo — gom đủ cho **đúng một vòng sửa**

Giao lại người cài đặt. **Bắt buộc** mục ①; các mục ②–④ là 🔵, **chỉ làm nếu người dùng đồng ý** —
nếu đồng ý thì làm **cùng lượt này** để không phát sinh vòng thứ tư.

| # | Mức | Việc | File |
|---|---|---|---|
| ① | 🟡 **bắt buộc** | Tách `except tarfile.FilterError` khỏi `except tarfile.TarError`, hai thông báo khác nhau; siết assert `test_04` (thêm vế phủ định) và `test_05` (thêm vế khẳng định) | `scripts/download_lfw.py:108`, `tests/test_download_lfw.py:118-135` |
| ② | 🔵 tuỳ chọn | Bọc `_doc_seed_manifest_cu` trong `try/except (ValueError, OSError, csv.Error)` → `LoiCauHinh` | `scripts/download_lfw.py:245-250` |
| ③ | 🔵 tuỳ chọn | Chuyển khối chặn lệch seed lên trước `tai_ve` | `scripts/download_lfw.py:330` |
| ④ | 🔵 tuỳ chọn | Đổi assert `test_27` thành `"'42'"` / `"'7'"` | `tests/test_download_lfw.py:470` |

**Tự kiểm trước khi bàn giao** (bắt buộc với mục ①):

```bash
# 1. Ghi sha256 gốc
sha256sum scripts/download_lfw.py
# 2. Đột biến: except tarfile.FilterError  ->  except tarfile.ExtractError
# 3. pytest -q tests/test_download_lfw.py   ->  test_05 PHẢI ĐỎ
# 4. Khôi phục, đối chiếu sha256
black --check --line-length 100 src tests scripts
ruff check src tests scripts
pytest -q                    # phải 116 passed
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)":/app -w /app faceid:arm64 pytest -q
```

Nếu chỉ làm mục ① thì §5 vẫn đủ 30 dòng, số ca test **không đổi (116)**.
Nếu làm thêm mục ②, cần `spec-writer` bổ sung một dòng vào §5 cho ca manifest hỏng **trước khi** cài đặt.

Sau khi ĐẠT, commit gợi ý (R29):

```
feat(scripts): P1-03 tai va chon loc bo du lieu LFW lam tap impostor
```

---
---

# Review P1-03-download-lfw — vòng 3

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-03-download-lfw.md` (§3.1 mới, §4.2 siết vị trí kiểm, §5 nay **32 dòng**) |
| **Nhánh** | `feat/p1-03-download-lfw` |
| **Ngày** | 2026-08-16 |
| **Phán quyết** | ✅ **ĐẠT** |

Tổng: **🔴 CHẶN-A: 0 · 🔴 CHẶN-B: 0 · 🟡 CẦN SỬA: 0 · 🔵 GÓP Ý: 3**

Không còn lỗi 🔴 lẫn 🟡. Ba lệnh máy sạch, container ARM64 xanh, mọi tiêu chí §6 thoả.
**Được commit.**

---

## Năm việc vòng 2 — xác minh từng việc bằng đột biến, không tin báo cáo

`sha256` gốc `scripts/download_lfw.py` = `26b5289d360c9f50…1940`.
**Khôi phục và đối chiếu sau mỗi phép — khớp toàn bộ 10 lần.**

| # | Việc | Đột biến kiểm chứng | Kết quả |
|---|---|---|---|
| 1 | Tách `except FilterError` / `TarError` | **MD** — gộp lại một `except` với thông báo cũ | ✅ **đỏ đúng `test_05`**, 31 ca khác xanh |
| 1b | `FilterError` đặt **trước** `TarError` | **MD2** — đảo thứ tự (làm `FilterError` không bao giờ tới) | ✅ **đỏ đúng `test_05`** |
| 2 | Chốt chặn seed chuyển lên trước `tai_ve` | đo trực tiếp số lần gọi `urlopen` | ✅ **0 lần gọi** — xem bên dưới |
| 3 | Bọc lỗi trong `_doc_seed_manifest_cu` | **ME** — đổi `except (ValueError, OSError, csv.Error)` thành `except RuntimeError` | ✅ **đỏ đúng `test_27b`** |
| 4 | `test_27` dùng dạng có dấu nháy | đọc mã: `assert "'42'" in caplog.text and "'7'" in caplog.text` | ✅ đã sửa |
| 5 | Tách 27b/27c, kiểm tường minh cột thiếu | **MF** — xoá khối kiểm `"selected_seed" not in reader.fieldnames` | ✅ **đỏ đúng `test_27c`** |

**Kiểm chức năng trực tiếp** (chạy ngoài bộ test):

```
1. giai_nen — hai thông báo phân biệt, đúng nguyên nhân gốc
   tệp hỏng : "Tệp nén hỏng, không mở được"                              gốc: ReadError
   độc hại  : "Tệp nén chứa đường dẫn vượt ra ngoài thư mục đích…"       gốc: OutsideDestinationError

2. Chốt chặn seed đặt TRƯỚC tai_ve — lệch seed, KHÔNG có tệp nén trong cache:
   main()=1  ·  số lần gọi urlopen = 0     ← chứng minh chưa hề chạm bước tải

3. 27b  selected_seed không phải số   -> main()=1, không ngoại lệ nào lọt ra ngoài
   27c  thiếu hẳn cột selected_seed   -> main()=1, thông báo nêu đúng tên cột
```

Mục 2 là điểm đáng ghi nhận: §4.2 yêu cầu "kiểm TRƯỚC khi tải", và điều đó **đo được** chứ không phải
suy từ vị trí dòng mã — đếm số lần `urlopen` được gọi cho ra đúng `0`.

Về cách bọc lỗi ở `_doc_seed_manifest_cu`: `LoiCauHinh` kế thừa `LoiHeThong → Exception`, **không**
phải con của `ValueError` hay `OSError` (đã kiểm bằng `issubclass`). Nên lệnh `raise LoiCauHinh` cho
ca thiếu cột — nằm *bên trong* khối `try` — không bị chính `except (ValueError, OSError, csv.Error)`
bắt lại và bọc chồng. Chi tiết dễ sai này đã được cài đúng.

---

## Hồi quy — cơ chế đã đạt ở vòng 1 và 2 có còn nguyên không

Vòng 3 động vào `giai_nen` và `main()`, tức chạm đúng hai chỗ nhạy cảm nhất. Chạy lại 5 phép đột biến
của các vòng trước:

| Phép hồi quy | Cơ chế | Kết quả |
|---|---|---|
| `filter="data"` → `"fully_trusted"` | chặn đường dẫn vượt ra ngoài (dòng 5) | ✅ **đỏ đúng `test_05`** |
| xoá nhánh `--expect-sha256` | so mã băm (dòng 24) | ✅ **đỏ đúng `test_24`** |
| xoá guard không-ghi-đè của `sao_chep` | dòng 16 | ✅ **đỏ đúng `test_16`** |
| `random.Random(seed)` → `random` toàn cục | tái lập R15 (dòng 9) | ✅ **đỏ đúng `test_09`** |
| xoá kiểm khoá thiếu của `ghi_manifest` | dòng 25 | ✅ **đỏ đúng `test_25`** |

**Không có hồi quy.** Hai cơ chế bị động vào ở vòng này (`filter="data"` nằm trong khối `try` vừa sửa;
`--expect-sha256` nằm sau chốt chặn vừa dời) đều vẫn được canh đúng.

---

## Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | đúng **2** file mã nguồn (+ biên bản review) ✅ |
| `git diff dev -- configs/ src/` | rỗng ✅ |
| `black --check --line-length 100 src tests scripts` | 19 files unchanged ✅ |
| `ruff check src tests scripts` | All checks passed ✅ |
| `pytest -q` (host) | **118 passed** (86 cũ + 32 mới) ✅ |
| `docker run … faceid:arm64 pytest -q` | **118 passed in 9.64s** ✅ |
| `python scripts/download_lfw.py --help` | thoát `0`, mô tả tiếng Việt ✅ |
| `python scripts/download_lfw.py --dry-run` | thoát `0`, `data/` vẫn rỗng (0 mục) ✅ |
| Quét AST | **32/32** hàm `test_*` có assert thật ✅ |
| §6: `grep` mạng / `subprocess` / thư viện ngoài | cả ba rỗng ✅ |
| §2: except trần, log f-string, đường dẫn tuyệt đối, secret, `assert True`, float trần | sạch ✅ |

**32 ca test khớp đúng 32 dòng bảng §5**, ánh xạ 1:1 theo tên hàm.

---

## 🔎 Phán quyết điểm mới — `test_27c` không được cách ly mạng về cấu trúc

### Xác minh: đúng, nhưng phạm vi hẹp hơn báo cáo

Đã tái hiện bằng đột biến MF, và đã **đo chính xác ca nào chạm mạng** bằng cách xoá hẳn chốt chặn seed
rồi chạy riêng từng ca `main()`:

| Ca | Sau khi xoá chốt chặn | Vì sao |
|---|---|---|
| `test_23` (dry-run) | an toàn | thoát ở nhánh `--dry-run`, chưa tới `tai_ve` |
| `test_24`, `test_24a` | an toàn | **có dựng `.tgz` mồi** → `tai_ve` thoát sớm ở `dich.exists()` |
| `test_27`, `test_27a`, `test_28` | **an toàn** | **có dựng `.tgz` mồi** |
| `test_27b`, `test_27c` | ❗ **chạm DNS** | **không dựng `.tgz` mồi** |

⇒ Trả lời câu hỏi "các ca 27, 27a, 28 có cùng đặc điểm này không": **KHÔNG**. Chỉ **27b và 27c**.
Sáu ca `main()` còn lại được cách ly **bằng cấu trúc**, không nhờ may mắn.

### Đính chính một chi tiết quan trọng trong mô tả sự việc

Nhận định *"ca test này sẽ thử tải thật vài trăm MB"* là **không đúng**. URL trong cấu hình test là
`http://khong-ton-tai.invalid/lfw.tgz`. Đuôi `.invalid` là **TLD dành riêng theo RFC 2606**, được bảo
đảm **không bao giờ phân giải được**. Đã kiểm:

```
khong-ton-tai.invalid -> KHÔNG PHÂN GIẢI ĐƯỢC: gaierror [Errno 11001] getaddrinfo failed
```

Tình huống xấu nhất là **một truy vấn DNS thất bại**, không phải một lượt tải vài trăm MB. Không có
cấu hình test nào trong tệp trỏ tới máy chủ thật, nên **không ca test nào có khả năng tải dữ liệu thật**.

### Kết luận: 🔵 chấp nhận được, nên siết — không phải lỗi chặn

**Lý do không tính là lỗi:**
1. Tiêu chí §6 *"không ca test nào truy cập mạng"* **hiện đang thoả** — không chỉ theo `grep` mà theo
   **đo thực tế**: ở trạng thái nguyên vẹn, số lần gọi `urlopen` trong toàn bộ 32 ca là **0**.
2. Hậu quả tối đa là một truy vấn DNS hỏng, không phải tải dữ liệu, không phải mất/hỏng dữ liệu.
3. Kịch bản rủi ro là **giả định về một lần refactor tương lai**. Theo nguyên tắc không mở rộng đặc tả
   khi review, "nên phòng thêm cho tương lai" là góp ý, không phải căn cứ trả lại.

**Vì sao vẫn nên siết** (chi phí rất thấp): độ an toàn của hai ca này đang **phụ thuộc thứ tự các bước
trong `main()`** — một quan hệ ngầm giữa mã sản phẩm và tệp test, không ai nhìn thấy khi đọc riêng ca
test. Vòng 2 chính tôi đề xuất dời chốt chặn lên trước; nếu vòng nào đó có lý do dời xuống, hai ca này
âm thầm mất tính hermetic.

**Cách sửa đề xuất (đã kiểm chứng)**: thêm `.tgz` mồi vào `test_27b` và `test_27c` đúng như 5 ca
`main()` còn lại — 2 dòng mỗi ca, dùng lại helper `_tao_tgz` có sẵn:

```python
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True)
    _tao_tgz(cache_dir / "lfw.tgz", {"lfw/A/a_0001.jpg": b"anh 1", "lfw/A/a_0002.jpg": b"anh 2"})
```

Đã chạy thử: thêm tệp mồi **không đổi kết quả** — cả hai ca vẫn `main() == 1` với đúng thông báo cũ,
vì chốt chặn vẫn bắn trước. Tức đây là thay đổi **trung tính về hành vi**, chỉ thêm lớp bảo hiểm.

### ⚠️ Mâu thuẫn trong chính đặc tả — việc của `spec-writer`, không phải người cài đặt

Cách chặn mạng mạnh nhất là một fixture `autouse` vá `urlopen` để mọi truy cập mạng **không thể xảy ra**
và báo lỗi rõ ràng. **Nhưng làm thế sẽ vi phạm chính tiêu chí §6**:

```
grep -nE "urlopen|urlretrieve|requests\.|socket" tests/test_download_lfw.py  # phải không có kết quả
```

Tiêu chí này dùng `grep` làm **đại diện** cho "không chạm mạng", nhưng nó lại **cấm luôn cơ chế duy nhất
bảo đảm được điều đó**. Đề xuất cho `spec-writer` ở các mã việc sau: đổi tiêu chí thành *"không ca test
nào **gọi** mạng"*, cho phép nhắc `urlopen` **trong fixture chặn**, hoặc chuyển hẳn fixture đó vào
`tests/conftest.py` dùng chung cho mọi mã việc — vừa mạnh hơn `grep`, vừa áp dụng một lần cho cả dự án.

---

## 🔵 Góp ý (không chặn — người dùng quyết định)

### GÓP Ý-1 — Cách ly mạng cho `test_27b`/`test_27c`
Như phân tích trên: thêm `.tgz` mồi, 2 dòng mỗi ca, trung tính về hành vi. Hoặc giải quyết triệt để
bằng fixture chặn `urlopen` trong `tests/conftest.py` — nhưng phải sửa tiêu chí §6 trước.

### GÓP Ý-2 — Vế phủ định của `test_04` bám vào câu chữ, không bám vào ngữ nghĩa
**Vị trí**: `tests/test_download_lfw.py` — `assert "vượt ra ngoài" not in thong_bao`

Khi chạy đột biến MD (gộp lại hai `except`, thông báo cũ *"Tệp nén hỏng **hoặc chứa đường dẫn không an
toàn**"*), `test_04` **vẫn xanh** vì chuỗi cũ dùng chữ "không an toàn" chứ không phải "vượt ra ngoài".
Chỉ `test_05` bắt được. Cặp assert vẫn **đủ hiệu lực** — mọi cách gộp hai thông báo làm một đều làm đỏ
ít nhất một trong hai ca (đã suy xét đủ bốn khả năng gộp) — nên **không phải lỗi**. Chỉ lưu ý rằng lớp
canh thực sự đang nằm ở `test_05`, không phải ở cả hai như tên gọi "bắt chéo" gợi ý.

### GÓP Ý-3 — §6 đặc tả còn ghi "bảng §5 nay có **30 dòng**"
**Vị trí**: `docs/dac-ta/P1-03-download-lfw.md` §6, gạch đầu dòng thứ 5. Bảng §5 đã là **32 dòng**.
Lỗi sót của `spec-writer` khi thêm 27b/27c, **không phải lỗi người cài đặt** và không ảnh hưởng mã
nguồn. Nên sửa để các mã việc sau không lấy nhầm con số làm mốc.

---

## 📊 Tổng kết ba vòng — P1-03-download-lfw

### Diễn biến

| | Vòng 1 | Vòng 2 | Vòng 3 |
|---|---|---|---|
| Dòng bảng §5 đặc tả | 24 | 30 | **32** |
| Số ca test của mã việc | 24 | 30 | **32** |
| Tổng ca test toàn dự án | 110 | 116 | **118** |
| 🔴 CHẶN-A / CHẶN-B | 0 / **1** | 0 / 0 | 0 / 0 |
| 🟡 CẦN SỬA | 0 | **1** | 0 |
| 🔵 GÓP Ý | 5 | 4 | 3 |
| Phép đột biến người review tự chạy | 9 | 3 | **10** |
| Đột biến **sống sót** (lỗ hổng) | **1** | 0 | 0 |
| Phán quyết | 🔴 TRẢ LẠI | 🔴 TRẢ LẠI | ✅ **ĐẠT** |

Tổng cộng **22 phép đột biến** trong ba vòng, mọi phép đều khôi phục và đối chiếu `sha256`.
Mã sản phẩm **chưa từng bị người review sửa** (R41).

### Đối chiếu với các mã việc trước

| Mã việc | Số vòng | Phán quyết cuối |
|---|---|---|
| P0-01-nen-tang | 2 | ✅ ĐẠT |
| P0-02-dependency | 2 | ✅ ĐẠT |
| P0-03-docker-arm64 | 2 | ✅ ĐẠT |
| P1-01-capture | 3 | 🟡 ĐẠT CÓ ĐIỀU KIỆN |
| P1-02-collect-faces | 3 | ✅ ĐẠT |
| **P1-03-download-lfw** | **3** | ✅ **ĐẠT** |

P1-03 đi đúng quỹ đạo của P1-02 (🔴 → 🟡 → ✅) và **tốt hơn P1-01** (mã việc duy nhất phải chốt ở mức
"đạt có điều kiện"). Ba mã việc Phase 0 cần 2 vòng vì phạm vi hẹp hơn hẳn; các mã việc Phase 1 có
`main()` và nhiều nhánh lỗi nên 3 vòng là mức bình thường, không phải dấu hiệu xấu.

### Bốn bài học rút ra

**1. Bộ test xanh không chứng minh điều gì về chất lượng test.**
Vòng 1: `black` sạch, `ruff` sạch, **110 ca xanh**, 24/24 ca có assert thật, ánh xạ 1:1 với bảng đặc
tả — vậy mà nhánh `--expect-sha256` **hoàn toàn không được ca nào chạm tới**. Xoá sạch tính năng đó,
110 ca vẫn xanh. Chỉ phép đột biến mới lộ ra. Đây là lần thứ ba trong dự án đột biến bắt được thứ mà
lint và test xanh bỏ sót (trước đó: P1-01, P1-02).

**2. Đặc tả chốt *kết quả* mà không chốt *tiền đề* thì sinh ra test giả.**
Nguyên nhân gốc của lỗi 🔴 vòng 1: bảng §5 dòng 24 chỉ ghi `main() == 1`, trong khi `main()` có nhiều
đường dẫn tới giá trị `1`. Người cài đặt mồi bằng một tệp không phải tar, `main()` trả `1` từ bước giải
nén — ca test xanh, nhánh cần kiểm không chạy. **Không phải lỗi cẩu thả mà là lỗ hổng của đặc tả.**
Cách chữa đã áp dụng từ vòng 2 và nên thành chuẩn: với mọi ca mà hàm có nhiều đường tới cùng một giá
trị trả về, bảng §5 phải nêu **tiền đề** và bắt buộc **assert phân biệt** — thường là thêm ca đường
thành công đối xứng (24 ↔ 24a, 27 ↔ 28, 25 ↔ 26).

**3. Góp ý 🔵 của vòng trước nên trở thành dòng đặc tả của vòng sau.**
5 góp ý 🔵 vòng 1 → §4.1, §4.2 và 6 dòng ca biên mới ở vòng 2. 1 góp ý vòng 2 → §3.1 và 2 dòng mới ở
vòng 3. Bảng §5 lớn từ 24 lên 32 dòng, tức **đặc tả ban đầu thiếu khoảng 25 % số ca biên thật sự cần**.
Vòng lặp review–đặc tả đang làm đúng việc của nó: biến quan sát rời rạc thành yêu cầu kiểm được.

**4. Người cài đặt tự nêu điểm mở là chỉ dấu chất lượng đáng tin nhất.**
Hai vòng liên tiếp, người cài đặt chủ động báo cáo chỗ mình phải suy diễn hoặc chỗ mình thấy chưa chắc
(thông báo lỗi gộp ở vòng 2; chạm mạng khi chạy đột biến ở vòng 3) — thay vì để review tự tìm. Cả hai
lần đều là vấn đề thật và dẫn tới cải thiện. Riêng lần thứ hai, người cài đặt còn **tự chạy đột biến
rồi báo lại hiện tượng quan sát được**, đúng tinh thần §2b. Nên duy trì yêu cầu này trong
`coder-handoff.prompt.md`.

> Ghi chú cho Chương 3 (bàn về quy trình phát triển): số liệu ở đây minh hoạ được luận điểm
> "kiểm thử đột biến phát hiện lỗ hổng mà độ phủ và lint không thấy" bằng **dữ liệu của chính đồ án**
> — 22 phép đột biến, 1 lỗ hổng nghiêm trọng bị bắt ở vòng 1, 0 hồi quy ở vòng 3.

---

## Việc tiếp theo

✅ **ĐẠT — được commit.** Ba góp ý 🔵 không chặn; GÓP Ý-3 thuộc về `spec-writer`.

```
feat(scripts): P1-03 tai va chon loc bo du lieu LFW lam tap impostor
```

Sau khi commit và gộp vào `dev`:
1. Nếu người dùng đồng ý GÓP Ý-1, mở mã việc nhỏ **hoặc** gộp vào mã việc kế tiếp — nên xử lý ở tầng
   `tests/conftest.py` cho cả dự án thay vì vá riêng một tệp test.
2. `spec-writer` sửa con số "30 dòng" ở §6 (GÓP Ý-3).
3. Bước 1.5 của Phase 1 **chưa xong về dữ liệu**: script đã sẵn sàng nhưng chưa chạy tải thật.
   Cổng C của Phase 1 yêu cầu `data/impostor/lfw_original/` có ≥ 100 danh tính — cần chạy
   `python scripts/download_lfw.py` với mạng thật, rồi ghi nhận `source_sha256` của `lfw.tgz` vào
   nhật ký tuần để về sau tái lập được.
