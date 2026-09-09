# Review P1-04-align — vòng 1

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-04-align.md` |
| **Nhánh** | `feat/p1-04-align` |
| **Ngày** | 2026-08-17 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — 2 lỗi 🔴 CHẶN-B, 0 lỗi 🔴 CHẶN-A, 1 lỗi 🟡 CẦN SỬA |

> Tác tử viết mã bị ngắt do hết hạn mức phiên, **không có báo cáo bàn giao**. Biên bản này là lớp
> kiểm duy nhất; phần kiểm bằng đột biến được chạy đầy đủ **bảy phép** thay vì ba.

---

## 1. Kết quả kiểm máy

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | đúng **3 file**, khớp DANH SÁCH TRẮNG §2 ✅ |
| `git diff dev -- configs/ src/common/ scripts/` | **rỗng** ✅ |
| `git diff dev --name-only` | **rỗng** (không đụng file đã theo dõi) ✅ |
| File cấm lọt git (`.jpg .npy .onnx .env …`) | không có ✅ |
| `black --check --line-length 100 src tests scripts` | 22 file sạch ✅ |
| `ruff check src tests scripts` | All checks passed ✅ |
| `pytest -q` (host) | **143 passed** = 118 cũ + 25 mới ✅ |
| `pytest -q` (container `faceid:arm64`) | **143 passed** ✅ |

### Quét mẫu vi phạm §2 `code-review.instructions.md`

`print(` · `except:` trần · `except Exception: pass` · `logger.*(f"` · đường dẫn tuyệt đối ·
secret · `assert True` · `InferenceSession` trong vòng lặp · float trần trong so sánh
→ **tất cả rỗng** ✅

### Bốn lệnh nghiệm thu §6 đặc tả

| Lệnh | Kết quả |
|---|---|
| `grep -nE "\.pt\b\|\.onnx\|urlopen\|requests\.\|models/" tests/test_align.py` | rỗng ✅ |
| `grep -nE "38\.29\|51\.69\|73\.53\|56\.02" src/preprocess/align.py` | rỗng ✅ |
| `grep -nE "^\s*(import\|from) (PIL\|imageio\|skimage\|scipy\|pandas\|torch)" src/preprocess/*.py` | rỗng ✅ |
| `git status --short --untracked-files=all \| grep -v "docs/review/" \| wc -l` | `3` ✅ |

**R21**: `align.py` chỉ import `src.common.exceptions` và `src.common.logging` — không import khối khác ✅

### Quét AST — hàm test không có `assert`

25/25 hàm test tồn tại (đúng 25 dòng bảng §5). 9 hàm không có câu lệnh `assert`, nhưng 8 trong số đó
dùng `pytest.raises(...)` làm phép khẳng định; hàm còn lại là
`test_dong01_kiem_diem_moc_hop_le_khong_nem` (`test_align.py:120`) — đúng theo assert tối thiểu mà
đặc tả §5 dòng 1 quy định ("Gọi xong không có ngoại lệ"). **Không có test giả.** ✅

---

## 2. Kiểm bằng đột biến — 7 phép, mọi phép khôi phục và đối chiếu `sha256`

`sha256(src/preprocess/align.py)` gốc = `697f7e38…f2f58f`, **khớp lại sau cả 7 phép**.

| # | Phép đột biến | Ca đỏ | Kỳ vọng | KL |
|---|---|---|---|---|
| DB1 | `estimateAffinePartial2D` → `estimateAffine2D` | `dong09` | dòng 9 | ✅ đúng, chỉ 1 ca |
| DB2 | Viết cứng toạ độ điểm chuẩn thay vì đọc config | `dong23` | dòng 23 | ✅ đúng, chỉ 1 ca |
| DB3 | Bỏ phần bọc `None` → `LoiCauHinh` | `dong07` | dòng 7 | ✅ đúng, chỉ 1 ca |
| DB4 | Bỏ kiểm hình dạng `(5, 2)` trong `kiem_diem_moc` | `dong02`, `dong03` | dòng 2 và/hoặc 3 | ✅ đúng |
| **DB5** | **Thay biến đổi tương tự bằng cắt ảnh theo khung bao** | `dong23`, `dong24` | **dòng 13, 14, 15** | ❌ **HỎNG** |
| DB6 | Bỏ qua ma trận ước lượng, dùng ma trận đơn vị | `dong13,14,15,23` | 13, 14, 15 | ✅ đúng |
| DB7 | Hoán đổi kênh BGR trước khi trả về | `dong17` | dòng 17 | ✅ đúng |

**6/7 phép đúng. Phép hỏng là đúng phép mà đặc tả §5 nêu đích danh làm lý do tồn tại của ba dòng
13/14/15** — xem CHẶN-B-1.

---

## 3. Đối chiếu đặc tả

| Mục | Kết luận |
|---|---|
| §3 Interface | ✅ Ba chữ ký khớp **từng ký tự** (tên hàm, tên/thứ tự tham số, kiểu trả về) |
| §3.1 Biến đổi tương tự | ✅ `align.py:85` dùng `estimateAffinePartial2D`; DB1 chứng minh dòng 9 canh đúng chỗ |
| §3.2 Thứ tự 5 điểm mốc | ✅ Không đảo; docstring `align.py:107-109` ghi đúng thứ tự |
| §4 Tham số → config | ⚠️ Đọc đúng 4 key, **không viết cứng** (DB2 xác nhận), nhưng **không kiểm tính hợp lệ của giá trị** → CHẶN-B-2 |
| §5 Ca biên | ⚠️ Đủ 25/25 ca, nhưng **dòng 13/14/15 không đạt mục đích đặc tả nêu** → CHẶN-B-1 |
| §6 Nghiệm thu | ✅ 8/8 mục đạt |
| §7 Quy ước lỗi | ❌ Hai loại lỗi **bị lẫn** → CHẶN-B-2 |
| §8 Ngoài phạm vi | ✅ Không phát hiện mặt, không tạo `scripts/preprocess.py`, không QC ảnh, không có nhánh dự phòng cắt khung bao, không sửa `configs/preprocess.yaml` |

### Đo thực tế các ngưỡng (điều đặc tả không bắt buộc nhưng quyết định giá trị của bộ test)

| Dòng | Ngưỡng đặc tả | Sai khác **thực tế** của bản cài đặt đúng | Dùng bao nhiêu ngân sách |
|---|---|---|---|
| 13 tịnh tiến | `< 2.0` | **0.0000** | 0 % |
| 14 phóng đại | `< 3.0` | **0.5530** | 18 % |
| 15 xoay 20° | `< 5.0` | **0.2031** | 4 % |
| 16 điểm mốc về vị trí chuẩn | `< 1.0` px | **0.000005 px** | ~0 % |
| 23 đổi điểm chuẩn | `> 10.0` | **98.99** | dư dả |

Bản cài đặt **đúng về mặt toán học** — sai số căn chỉnh gần bằng không (dòng 16: 5×10⁻⁶ pixel).
Vấn đề nằm ở **sức phân biệt của ngưỡng**, không ở độ chính xác của phép biến đổi.

---

## 4. Lỗi phải sửa

### 🔴 CHẶN-B-1 — Ba ca bất biến không bắt được bản "cắt khung bao" (vi phạm CB-6, sai mục đích §5)

**Vị trí**: `tests/test_align.py:235`, `:252`, `:273` (ba hàm test) — gốc rễ ở `tests/test_align.py:57-68`

```python
def _mau_tong_hop(x: np.ndarray, y: np.ndarray, kich_thuoc: int) -> np.ndarray:
    """Hàm màu mượt (2 dốc tuyến tính + 1 đốm Gauss) — không tuần hoàn, không có cạnh sắc."""
```

**Bằng chứng đo được** (phép DB5 — thay toàn bộ `uoc_luong_bien_doi` + `warpAffine` bằng
`cv2.resize(anh[y0:y1, x0:x1], …)`):

| Dòng | Ngưỡng | Bản **đúng** | Bản **cắt khung bao** | Kết quả |
|---|---|---|---|---|
| 13 tịnh tiến | `< 2.0` | 0.000 | **0.000** | 🟢 vẫn xanh |
| 14 phóng đại | `< 3.0` | 0.553 | **0.285** | 🟢 vẫn xanh |
| 15 xoay 20° | `< 5.0` | 0.203 | **3.934** | 🟢 vẫn xanh |

Đặc tả §5 ghi: *"Không có ba dòng này thì một hàm chỉ cắt ảnh theo khung bao cũng qua được mọi dòng
còn lại."* **Có ba dòng này thì nó vẫn qua được** — DB5 chỉ làm đỏ dòng 23 và 24.

**Vì sao**: hai nguyên nhân độc lập.

1. *Ảnh thử quá mượt.* Gradient trung bình của `_anh_tong_hop(320)` chỉ **0.26 mức xám/pixel theo
   trục ngang, 0.52 theo trục dọc**. Ngưỡng `5.0` mức xám do đó dung thứ **khoảng 19 pixel** lệch
   hình học trên ảnh ra 100×100. Đó gần như không ràng buộc gì. Docstring `test_align.py:60-61` chọn
   ảnh mượt để "không lẫn với nhiễu do nội suy" — ý định đúng, nhưng tác dụng phụ là xoá luôn sức
   phân biệt. Đo với ảnh có kết cấu: bản đúng 8.999 vs bản cắt khung bao **72.446** — tách bạch rõ.
2. *Dòng 13 và 14 bất lực về mặt cấu trúc.* Phép cắt theo khung bao **vốn dĩ** bất biến với tịnh
   tiến và phóng đại (khung bao dịch/phóng cùng điểm mốc, rồi `resize` chuẩn hoá lại). Không ngưỡng
   nào và không ảnh thử nào cứu được hai dòng này — xem §6.

**Hậu quả thật**: nếu `P1-05` hoặc một lần refactor sau này thay nhầm phép căn chỉnh bằng phép cắt,
bộ test vẫn xanh 143/143. Toàn bộ `data/processed/` sẽ là ảnh cắt thô, embedding lệch hệ thống, và
`FAR_lfw`/`FAR_adapt`/`FAR_indomain` ở Phase 3 sai mà **không có lỗi nào báo** — đúng kịch bản
"hỏng âm thầm" mà §1 đặc tả nêu là lý do tách riêng mã việc này.

**Sửa** — bổ sung **một** ca test end-to-end cho `can_chinh` (đã kiểm chứng là giết được DB5):
vẽ chấm sáng tại đúng 5 điểm mốc trên ảnh nguồn, rồi khẳng định chấm sáng xuất hiện quanh **toạ độ
điểm chuẩn** trong ảnh ra.

```python
def test_can_chinh_dua_diem_moc_ve_dung_diem_chuan_tren_anh_ra() -> None:
    """`can_chinh` phải THỰC SỰ áp ma trận biến đổi, không chỉ cắt ảnh theo khung bao."""
    diem_chuan = _diem_chuan_test()
    diem_moc = _diem_moc_bat_bien()
    cfg = _cfg_toi_thieu(output_size=(100, 100), diem_chuan=diem_chuan)

    anh = np.zeros((320, 320, 3), dtype=np.uint8)
    for x, y in diem_moc:
        cv2.circle(anh, (int(round(x)), int(round(y))), 4, (255, 255, 255), -1)

    xam = cv2.cvtColor(can_chinh(anh, diem_moc, cfg), cv2.COLOR_BGR2GRAY)
    for x, y in diem_chuan:
        cx, cy = int(round(x)), int(round(y))
        vung = xam[max(0, cy - 12) : cy + 13, max(0, cx - 12) : cx + 13]
        assert vung.max() > 200, f"không thấy điểm mốc tại vị trí chuẩn ({x}, {y})"
```

Kết quả đã đo của ca này: bản đúng → `[255,255,255,255,255]` (đạt); bản cắt khung bao →
`[0,255,255,0,0]` (**đỏ**). Đây là ca **duy nhất** trong toàn bộ mã việc kiểm được rằng `can_chinh`
có dùng ma trận do `uoc_luong_bien_doi` sinh ra — dòng 16 hiện chỉ kiểm ma trận rời rạc, không chạm
tới `can_chinh`.

> Ba dòng 13/14/15 **giữ nguyên**, không phải sửa: DB6 chứng minh chúng vẫn bắt được trường hợp bỏ
> qua hẳn ma trận biến đổi. Chúng chỉ không đủ một mình.

---

### 🔴 CHẶN-B-2 — Cấu hình hỏng bị ném thành `ValueError`, lẫn hai loại lỗi (vi phạm §7)

**Vị trí**: `src/preprocess/align.py:140` và `src/preprocess/align.py:143`

```python
rong, cao = (int(v) for v in cfg["output_size"])          # dòng 140

diem_chuan = np.asarray(cfg["reference_landmarks"], dtype=np.float64)
kiem_diem_moc(diem_chuan)                                  # dòng 143
```

Dòng 143 đưa dữ liệu **lấy từ config** qua `kiem_diem_moc`, mà `kiem_diem_moc` theo hợp đồng §3
luôn ném `ValueError`. Dòng 140 để lỗi giải nén/ép kiểu của `output_size` thoát ra nguyên dạng.

**Đo được** — 12 ca cấu hình hỏng, chỉ **1** ca đúng quy ước:

| Cấu hình hỏng | Ngoại lệ thực tế | §7 yêu cầu |
|---|---|---|
| `reference_landmarks` chỉ có 4 điểm | `ValueError` | `LoiCauHinh` |
| `reference_landmarks` mỗi điểm 3 toạ độ | `ValueError` | `LoiCauHinh` |
| `reference_landmarks` chứa `null` (YAML) | `ValueError` | `LoiCauHinh` |
| `reference_landmarks` là chuỗi | `ValueError` | `LoiCauHinh` |
| `output_size` chỉ 1 phần tử | `ValueError` | `LoiCauHinh` |
| `output_size` 3 phần tử | `ValueError` | `LoiCauHinh` |
| `output_size` là chuỗi | `ValueError` | `LoiCauHinh` |
| `border_value` là số vô hướng | `TypeError` | `LoiCauHinh` |
| `interpolation` sai tên | `LoiCauHinh` | `LoiCauHinh` ✅ |

**Vì sao**: đặc tả §7 nêu chính xác hậu quả — *"tầng gọi phải phân biệt 'ảnh này bỏ qua' với 'cấu
hình hỏng, dừng cả mẻ'"*. `P1-05` sẽ duyệt hàng nghìn ảnh trong vòng lặp `try/except ValueError:
bỏ qua ảnh này`. Với `configs/preprocess.yaml` gõ sai một dấu, mẻ xử lý sẽ **chạy hết và báo thành
công với 100 % ảnh bị bỏ qua**, thay vì dừng ngay ở ảnh đầu tiên. Thông báo lỗi còn chỉ sai chỗ:
`"diem_moc phải có hình dạng (5, 2)"` khiến người đọc đi soi điểm mốc đầu vào trong khi lỗi nằm ở
file cấu hình.

**Sửa** — bọc phần đọc và kiểm giá trị config, giữ nguyên `kiem_diem_moc` cho dữ liệu đầu vào:

```python
try:
    rong, cao = (int(v) for v in cfg["output_size"])
except (TypeError, ValueError) as e:
    raise LoiCauHinh(f"Cấu hình 'output_size' không hợp lệ: {cfg['output_size']!r}") from e

try:
    diem_chuan = np.asarray(cfg["reference_landmarks"], dtype=np.float64)
    kiem_diem_moc(diem_chuan)
except (TypeError, ValueError) as e:
    raise LoiCauHinh(f"Cấu hình 'reference_landmarks' không hợp lệ: {e}") from e
```

Bổ sung hai ca test tương ứng (`reference_landmarks` sai hình dạng → `LoiCauHinh`;
`output_size` sai số phần tử → `LoiCauHinh`).

---

### 🟡 CẦN SỬA-1 — `output_size` ≤ 0 trả **ảnh gốc** thay vì báo lỗi

**Vị trí**: `src/preprocess/align.py:157-164`

```python
anh_can_chinh = cv2.warpAffine(anh, ma_tran, (rong, cao), ...)
```

**Đo được**: với `output_size: [0, 0]` hoặc `[-5, -5]`, hàm **không ném gì** và trả về ảnh
`(200, 200, 3)` — tức nguyên kích thước ảnh vào. Nguyên nhân: `cv2.warpAffine` hiểu `dsize=(0,0)`
là "giữ kích thước ảnh nguồn".

**Vì sao**: Cổng C của Phase 1 yêu cầu *"mọi ảnh `processed/` đúng 112×112"*. Với một config gõ sai,
`P1-05` sẽ ghi ra `data/processed/` hàng nghìn ảnh **sai kích thước mà không có cảnh báo nào**, và
lỗi chỉ lộ ra ở Phase 3 khi mô hình nhận đầu vào sai chiều — hoặc tệ hơn, không lộ ra vì bị resize
ngầm ở tầng sau.

**Sửa**: kiểm ngay sau khi đọc `output_size` (gộp chung với bản vá CHẶN-B-2):

```python
if rong <= 0 or cao <= 0:
    raise LoiCauHinh(f"Cấu hình 'output_size' phải là hai số dương, nhận {cfg['output_size']!r}")
```

---

## 5. 🔵 Góp ý (không chặn — người dùng quyết định)

- **`align.py:140` — quy ước thứ tự `output_size` chưa được ghi ở đâu.** Mã hiểu là
  `[rộng, cao]`; cả config lẫn hai ca test đều dùng giá trị vuông (`112`, `64`) nên thứ tự **chưa hề
  được kiểm**. Rủi ro thấp lúc này (112×112 là vuông), nhưng nếu Phase 3 đổi sang mô hình đầu vào
  chữ nhật thì đây là chỗ sai lặng lẽ. Chi phí: một dòng comment trong `configs/preprocess.yaml`
  + một ca test dùng `output_size` không vuông.
- **`reference_landmarks` gồm 5 điểm trùng nhau** cho ra ảnh một màu, không ném lỗi (đã đo). Đặc tả
  §5 dòng 7 chỉ phủ trường hợp **điểm mốc nguồn** suy biến. Cân nhắc bổ sung vào đặc tả cho đối xứng.
- `align.py:166` ghi log ở mức `DEBUG` cho mỗi lần căn chỉnh. Khi `P1-05` chạy hàng nghìn ảnh, bật
  `DEBUG` sẽ sinh log rất lớn. Cân nhắc bỏ hoặc chuyển sang đếm tổng ở tầng gọi.

---

## 6. ⚠️ Vấn đề thuộc về **đặc tả**, không phải người cài đặt

Gửi `spec-writer` — người cài đặt **không thể sửa** những điểm này:

1. **Dòng 13 và 14 của §5 bất lực về mặt cấu trúc** trước phép cắt khung bao. Đã đo: bản cắt khung
   bao cho sai khác `0.000` (dòng 13) và `0.285` (dòng 14) — *tốt hơn cả bản đúng* (`0.553` ở dòng
   14). Lý do là phép cắt theo khung bao vốn đã bất biến với tịnh tiến và phóng đại. Ghi chú của §5
   ("không có ba dòng này thì một hàm chỉ cắt ảnh theo khung bao cũng qua được mọi dòng còn lại")
   **đúng về động cơ nhưng sai về phương tiện**: chỉ dòng 15 có sức phân biệt, và cần thêm một ca
   kiểu "điểm mốc về đúng vị trí chuẩn **trên ảnh ra**".
2. **Ngưỡng `2.0 / 3.0 / 5.0` mức xám không gắn với ảnh thử nào.** §5 quy định ngưỡng nhưng để người
   cài đặt tự chọn ảnh — mà độ nhạy của phép đo phụ thuộc hoàn toàn vào kết cấu ảnh. Đo được: cùng
   một bản cài đặt đúng cho `0.203` trên ảnh mượt và `8.999` trên ảnh có kết cấu; ngưỡng `5.0` do đó
   vừa quá lỏng (ảnh mượt) vừa quá chặt (ảnh có kết cấu). Đặc tả nên **quy định luôn ảnh thử**, hoặc
   đổi sang tiêu chí không phụ thuộc kết cấu (sai số vị trí điểm mốc tính bằng pixel).
3. **§7 nêu quy ước lỗi trong văn xuôi nhưng §5 không có dòng nào kiểm nó** ngoài hai ca thiếu key
   (dòng 20, 21). Yêu cầu bị chôn trong văn xuôi thì bị bỏ sót — đúng như CHẶN-B-2 cho thấy. Nên
   thêm 2–3 dòng vào bảng §5 cho cấu hình **hỏng** (khác với **thiếu**).

---

## 7. Ghi nhận mặt được

- Phép toán căn chỉnh **đúng**: sai số đưa điểm mốc về vị trí chuẩn là **5×10⁻⁶ pixel**.
- Dùng đúng `estimateAffinePartial2D`; DB1 xác nhận dòng 9 canh đúng chỗ.
- Không viết cứng toạ độ điểm chuẩn — DB2 xác nhận bằng đột biến, không chỉ bằng `grep`.
- Quy ước BGR không bị hoán đổi; DB7 xác nhận dòng 17 có hiệu lực thật.
- `raise ... from e` dùng đúng ở `align.py:55` và `:87` (G5).
- Type hints và docstring tiếng Việt đầy đủ cho cả ba hàm public (G4).
- Hai comment `# noqa: TRY004` ở `align.py:41` và `:122` có giải thích lý do gắn với đặc tả — đúng
  cách xử lý xung đột giữa lint và hợp đồng hàm, không phải tắt lint bừa.
- Bộ test hoàn toàn tự chứa: không mô hình, không ảnh thật, không mạng; chạy xanh cả trên host lẫn
  container ARM64.

---

## 8. Việc tiếp theo

Giao lại cho người cài đặt — **một vòng sửa, ba việc**:

1. `tests/test_align.py` — thêm ca `test_can_chinh_dua_diem_moc_ve_dung_diem_chuan_tren_anh_ra`
   (mã đã cho ở CHẶN-B-1, đã kiểm chứng giết được phép cắt khung bao).
2. `src/preprocess/align.py:140-143` — bọc lỗi đọc/kiểm config thành `LoiCauHinh` (CHẶN-B-2),
   kèm kiểm `rong > 0 and cao > 0` (CẦN SỬA-1).
3. `tests/test_align.py` — thêm 3 ca: `reference_landmarks` sai hình dạng → `LoiCauHinh`;
   `output_size` sai số phần tử → `LoiCauHinh`; `output_size = [0, 0]` → `LoiCauHinh`.

Không đụng file nào khác. Sau khi sửa, chạy lại `black` / `ruff` / `pytest` (host + ARM64) và
**tự chạy lại phép DB5** để xác nhận ca mới đỏ đúng chỗ.

Song song, `spec-writer` xử lý §6 của biên bản này trước khi mã việc `P1-05` bắt đầu.

---

# Review P1-04-align — vòng 2

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-04-align.md` (đã sửa — bảng §5 từ 25 lên **32 dòng**) |
| **Nhánh** | `feat/p1-04-align` |
| **Ngày** | 2026-08-17 |
| **Phán quyết** | 🔴 **TRẢ LẠI** — 0 lỗi 🔴, **1 lỗi 🟡 CẦN SỬA** (sửa ~10 dòng) |

> **Hai lỗi 🔴 CHẶN-B của vòng 1 đều đã được sửa thật**, đã kiểm chứng bằng đột biến và bằng đo trực
> tiếp. Lỗi 🟡 còn lại là **cùng một loại** với CHẶN-B-2 nhưng trên key `border_value` — chỗ duy nhất
> chưa được bọc.

---

## 1. Kết quả kiểm máy — vòng 2

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` | đúng **3 file** code + biên bản review ✅ |
| `git diff dev -- configs/ src/common/ scripts/` | **rỗng** ✅ |
| `git diff dev --name-only` | chỉ `docs/dac-ta/P1-04-align.md` (file của `spec-writer`) ✅ |
| File cấm lọt git | không có ✅ |
| `black --check --line-length 100 src tests scripts` | 22 file sạch ✅ |
| `ruff check src tests scripts` | All checks passed ✅ |
| `pytest -q` (host) | **150 passed** = 118 cũ + 32 mới ✅ |
| `pytest -q` (container `faceid:arm64`) | **150 passed** ✅ |
| 4 lệnh `grep` §6 | cả 4 **rỗng**, lệnh đếm phạm vi trả `3` ✅ |
| Quét mẫu vi phạm §2 | `print(` · `except:` trần · `logger.*(f"` · đường dẫn tuyệt đối · `assert True` → **0** ✅ |

**Quét AST**: 32 hàm test / 32 dòng bảng §5 — khớp 1–1. Năm hàm không có `assert` trực tiếp:
`test_dong01` (đặc tả §5 dòng 1 chỉ đòi "gọi xong không có ngoại lệ") và bốn hàm
`dong13/13a/14/15` — bốn hàm này uỷ quyền cho `_kiem_diem_moc_ve_dung_vi_tri_chuan`
(`test_align.py:125`) có `assert all(v >= 250 …), gia_tri`. Đột biến DB5 chứng minh assert này có
hiệu lực thật. **Không có test giả.** ✅

---

## 2. Phép đột biến BẮT BUỘC theo §6 — kết quả quyết định

`sha256(align.py)` gốc = `08b02529…c25053`, **khớp lại sau cả 6 phép**.

### DB5 — thay toàn bộ phép căn chỉnh bằng cắt khung bao 5 điểm mốc, nới biên 35 %, `resize`

```python
le_x = (x_max - x_min) * 0.35
le_y = (y_max - y_min) * 0.35
anh_can_chinh = cv2.resize(anh[y0:y1, x0:x1], (rong, cao), interpolation=co_noi_suy)
```

| | Vòng 1 | Vòng 2 |
|---|---|---|
| Kết quả | 2 failed — **dòng 13/14/15 vẫn xanh** ❌ | **6 failed** ✅ |
| Ca đỏ | `dong23`, `dong24` | **`dong13`**, `dong13a`, `dong14`, `dong15`, `dong23`, `dong24` |

**Dòng 13 đỏ — đạt yêu cầu §6.** Lỗi CHẶN-B-1 của vòng 1 đã được khắc phục triệt để: bộ kiểm thử
nay **phân biệt được** phép căn chỉnh thật với phép cắt ảnh theo khung bao.

### Năm phép còn lại

| # | Phép đột biến | Ca đỏ | Kỳ vọng | KL |
|---|---|---|---|---|
| DB8 | Bỏ bọc lỗi cấu hình → trả về `ValueError` thô | `dong28`, `dong29`, **`dong30`** | dòng 30 | ✅ |
| DB9 | Bỏ kiểm `output_size` phải dương | **`dong26`**, `dong27`, `dong30` | dòng 26 | ✅ |
| DB1 | `estimateAffinePartial2D` → `estimateAffine2D` | `dong09` | dòng 9 | ✅ hồi quy đạt |
| DB2 | Viết cứng toạ độ điểm chuẩn | `dong23` (+28/29/30) | dòng 23 | ✅ hồi quy đạt |
| DB7 | Hoán đổi kênh BGR | `dong17` | dòng 17 | ✅ hồi quy đạt |

> DB2 làm đỏ thêm dòng 28/29/30 vì phép đột biến đặt đúng vào trong khối `try` bọc
> `reference_landmarks`, nên vô hiệu hoá luôn phần kiểm cấu hình. Đó là hệ quả vị trí đột biến,
> không phải ca test quá rộng.

---

## 3. Hai lỗi 🔴 CHẶN-B của vòng 1 — kiểm chứng đã sửa thật

### CHẶN-B-1 (ba ca bất biến bất lực) → ✅ **ĐÃ SỬA**

Cách đo cũ (sai khác mức xám trung bình) đã bị thay bằng chấm sáng tại điểm mốc / lấy mẫu tại điểm
chuẩn (`test_align.py:100-125`). DB5 xác nhận dòng 13 nay đỏ.

### CHẶN-B-2 (lẫn `ValueError` với `LoiCauHinh`) → ✅ **ĐÃ SỬA** ở `align.py:140-154`

Tự dựng **19 cấu hình hỏng** và kiểm từng cái:

| Nhóm | Số ca | Kết quả |
|---|---|---|
| `output_size` — `[0,0]`, số âm, 1 phần tử, 3 phần tử, chuỗi, `None` | 6 | **6/6 → `LoiCauHinh`** ✅ |
| `reference_landmarks` — 4 điểm, 3 toạ độ, `null`, chuỗi trong mảng, chuỗi, `None`, rỗng, `NaN` | 8 | **8/8 → `LoiCauHinh`** ✅ |
| `interpolation` sai tên | 1 | `LoiCauHinh` ✅ |
| `border_value` — vô hướng / chuỗi / 2 phần tử | 3 | **0/3** ❌ → CẦN SỬA-2 |
| `output_size` là số thực `[112.7, 112.7]` | 1 | không ném, cắt còn 112 (xem 🔵) |

**15/19 đúng quy ước §7.** Toàn bộ các ca tôi nêu đích danh ở vòng 1 nay đều đúng.

### CẦN SỬA-1 vòng 1 (`output_size: [0,0]` trả ảnh gốc) → ✅ **ĐÃ SỬA**

`align.py:145-148` nay ném `LoiCauHinh`; trước đây trả về ảnh `(200, 200, 3)` im lặng.

---

## 4. Kiểm hồi quy — những gì đã đạt ở vòng 1 vẫn đạt

| Dòng | Chỉ số | Vòng 1 | Vòng 2 | KL |
|---|---|---|---|---|
| 16 | Sai số đưa điểm mốc về vị trí chuẩn | 5,056×10⁻⁶ px | **5,056×10⁻⁶ px** | ✅ không đổi |
| 9 | Chênh độ dài hai vectơ hàng (tính tương tự) | < 1e-6 | **0,000** (chính xác) | ✅ |
| 23 | Khác biệt khi đổi `reference_landmarks` | 98,99 | **98,99** | ✅ |
| 17 | Pixel giữa ảnh ra với ảnh vào `[255,0,0]` | kênh 0 lớn nhất | **`[255, 0, 0]`** | ✅ BGR không đảo |
| 25 | Nạp `configs/preprocess.yaml` thật | `(112,112,3)` | **`(112,112,3)`** | ✅ |

Phép toán căn chỉnh **không hề bị đụng chạm** khi sửa phần cấu hình — đúng như mong muốn.

---

## 5. Đánh giá bốn quyết định người cài đặt tự nêu

### 5.1. Lấy mẫu **một pixel** tại toạ độ điểm chuẩn làm tròn — ✅ **KHÔNG quá mong manh**

Đo dung sai trong **không gian ảnh ra**: tịnh tiến ma trận biến đổi đi `d` pixel theo **8 hướng**,
tìm `d` lớn nhất mà cả 5 điểm vẫn `>= 250`.

| Ca | Hệ số phóng đại | Chấm sáng r=4 px thành | **Dung sai** |
|---|---|---|---|
| dòng 13 | 0,7143 | 2,86 px | **1,875 px** |
| dòng 13a | 0,7143 | 2,86 px | **1,875 px** |
| **dòng 14** | 0,3571 | 1,43 px | **0,875 px** ← chặt nhất |
| dòng 15 | 0,7143 | 2,86 px | **1,875 px** |

**Trả lời câu hỏi**: lệch nửa pixel **không** làm đỏ oan — ca chặt nhất (dòng 14) vẫn còn dung sai
0,875 px, gấp 1,75 lần mức nửa pixel. Biên độ hai chiều đều lành mạnh: bản cắt khung bao cho `0` tại
các điểm này nên vẫn bị bắt.

**Không có dấu hiệu bấp bênh giữa nền tảng**: chạy cùng phép đo trên host x86-64 và trong container
ARM64 cho **con số giống hệt nhau** (1,875 / 1,875 / 0,875 / 1,875), và `pytest` xanh 150/150 ở cả hai.

> Ghi chú phương pháp: phép đo đầu tiên của tôi (dịch *toạ độ lấy mẫu* rồi làm tròn) cho ra 0,25 px
> — **con số đó sai**, vì việc làm tròn về `int` tự nó gây nhảy 1 pixel. Số đúng là dịch *ma trận
> biến đổi*, giữ nguyên toạ độ lấy mẫu. Ghi lại để lần sau không đo nhầm.

### 5.2. Xoá hẳn ba hàm test kiểu cũ thay vì giữ song song — ✅ **hợp lý**

Ba ca cũ đã được chứng minh là **không phân biệt được** căn chỉnh với cắt khung bao. Giữ lại chỉ tạo
cảm giác an toàn giả và tốn thời gian chạy. Đặc tả sửa cũng đã thay hẳn dòng 13/14/15 chứ không thêm
dòng mới, nên xoá là đúng đặc tả.

### 5.3. Xoá `_render_bien_dang` và import `Callable` — ✅ **đúng**

Kiểm bằng AST: **không còn hàm trợ giúp chết nào**. `_do_sai_khac_xam` vẫn được dùng đúng 1 lần
(`test_align.py:385`, dòng 23) nên giữ lại là hợp lý; `_mau_tong_hop` vẫn được `_anh_tong_hop` gọi.

### 5.4. Dòng 30/31 dùng vòng lặp duyệt danh sách — ⚠️ **dòng 30 đạt, dòng 31 yếu hơn**

Kiểm bằng cách gây lỗi thật rồi đọc thông báo:

| Ca | Thông báo khi hỏng | Có chỉ ra trường hợp nào? |
|---|---|---|
| Dòng 30 (DB8) | `Failed: Cấu hình hỏng {'output_size': [100], 'reference_landmarks': […]} ném ValueError thay vì LoiCauHinh` | ✅ **in nguyên cấu hình gây lỗi** |
| Dòng 30 (DB9) | `Failed: Cấu hình hỏng {'output_size': [0, 0], …}` | ✅ |
| Dòng 31 (DB10) | `Failed: Dữ liệu vào hỏng ném LoiCauHinh thay vì ValueError: diem_moc chứa giá trị không hữu hạn…` | ⚠️ chỉ gián tiếp qua thông báo ngoại lệ |

Dòng 30 **định vị được ngay**. Dòng 31 chỉ định vị gián tiếp — và vì danh sách có **hai** ca cùng cho
thông báo "không hữu hạn" (`NaN` ở `test_align.py:514` và `inf` ở `:515`), thông báo thu hẹp còn hai
khả năng chứ không chỉ đúng một. Nhánh `else` (`test_align.py:526`) còn không nêu gì cả. Xem 🔵.

---

## 6. Lỗi phải sửa

### 🟡 CẦN SỬA-2 — `border_value` hỏng vẫn ném `TypeError`/`ValueError` (vi phạm §7)

**Vị trí**: `src/preprocess/align.py:164` và `src/preprocess/align.py:174`

```python
mau_vien = cfg.get("border_value", [0, 0, 0])          # dòng 164 — không kiểm
...
    borderValue=tuple(float(v) for v in mau_vien),      # dòng 174 — nổ ở đây
```

**Đo được**:

| `border_value` trong config | Ngoại lệ thực tế | §7 yêu cầu |
|---|---|---|
| `0` (số vô hướng) | `TypeError` | `LoiCauHinh` |
| `'den'` (chuỗi) | `ValueError` | `LoiCauHinh` |
| `[0, 0]` (thiếu 1 kênh) | **không ném** | `LoiCauHinh` |

**Vì sao**: đây đúng là kịch bản §7 dựng ra để phòng. `border_value: den` là lỗi gõ rất tự nhiên
(viết tên màu thay vì bộ ba số). Nó ném `ValueError`, mà `P1-05` bắt `ValueError` để **bỏ qua ảnh**
— nên cả mẻ sẽ chạy hết và báo thành công với **100 % ảnh bị bỏ**, không một dòng cảnh báo. Đây là
cùng một lỗi đã sửa cho `output_size` và `reference_landmarks`, chỉ còn sót key thứ ba.
Riêng `[0, 0]` thì tệ hơn: **không báo gì** và ghi ảnh có màu viền sai vào `data/processed/`.

**Sửa** — bọc nốt, ngay cạnh hai khối đã bọc:

```python
mau_vien = cfg.get("border_value", [0, 0, 0])
try:
    mau_vien = tuple(float(v) for v in mau_vien)
except (TypeError, ValueError) as e:
    raise LoiCauHinh(f"Cấu hình 'border_value' không hợp lệ: {cfg['border_value']!r}") from e

if len(mau_vien) != 3:
    raise LoiCauHinh(f"Cấu hình 'border_value' phải có đúng 3 kênh, nhận {cfg['border_value']!r}")
```

rồi truyền thẳng `borderValue=mau_vien` ở `align.py:174`.

**Bổ sung vào dòng 30** (`test_align.py:469-483`) ba mục vào `cau_hinh_hong`:
`{"border_value": 0}`, `{"border_value": "den"}`, `{"border_value": [0, 0]}` — danh sách lên 10 mục,
vẫn thoả "≥ 6" của đặc tả.

---

## 7. 🔵 Góp ý (không chặn — người dùng quyết định)

- **`test_align.py:509-526` — dòng 31 nên đánh số ca.** Đổi `for anh, diem_moc in ca_hong:` thành
  `for i, (anh, diem_moc) in enumerate(ca_hong):` và đưa `i` vào cả ba thông báo (kể cả nhánh `else`
  ở dòng 526, hiện không nêu gì). Chi phí: 3 dòng; lợi: hỏng ở đâu biết ngay ở đó, ngang dòng 30.
- **`test_align.py:57-61` — docstring `_mau_tong_hop` đã lạc hậu.** Vẫn ghi *"Dùng để các ca kiểm
  bất biến hình học (dòng 13, 14, 15)…"* trong khi ba ca đó nay dùng `_anh_cham_sang_tai_moc`.
  Docstring mô tả một cách đo đã bị gỡ bỏ sẽ dẫn người đọc sau này đi sai hướng.
  (`_diem_moc_bat_bien` ở dòng 77-83 cũng còn nhắc "dòng 13, 14, 15" nhưng lập luận dư dôi = 0 vẫn
  còn đúng, chỉ cần sửa câu cuối.)
- **`align.py:141` — `output_size: [112.7, 112.7]` bị cắt thành `112` không cảnh báo.** Đo được:
  không ném, trả `(112, 112, 3)`. Ép kiểu khoan dung có thể là chủ ý; nếu vậy nên ghi vào docstring.
- Ba góp ý của vòng 1 (thứ tự `[rộng, cao]` chưa được kiểm vì mọi kích thước đều vuông; điểm chuẩn
  5 điểm trùng nhau cho ảnh một màu không báo lỗi; `logger.debug` mỗi ảnh) **vẫn còn nguyên** —
  người dùng chưa quyết nên tôi không nhắc lại chi tiết.

---

## 8. Nhận xét chất lượng đặc tả sau lần sửa

Lần sửa này xử lý **đúng và đủ** cả hai khiếm khuyết ở §6 biên bản vòng 1:

- **Tiêu chí đo được thay bằng loại không phụ thuộc ảnh thử.** Chuyển từ "sai khác mức xám trung
  bình" sang "chấm sáng tại điểm mốc, lấy mẫu tại điểm chuẩn" là thay đổi đúng bản chất: nó đo
  **trực tiếp thứ cần đo**. Số đo xác nhận: dung sai 0,875–1,875 px, giống hệt trên hai kiến trúc.
- **Ghi chú dưới bảng nêu thẳng phiên bản đầu sai ở đâu, kèm số đo** (0,000 / 0,285 / 3,934 so với
  2,0 / 3,0 / 5,0). Đây là cách làm tài liệu tốt — người đọc sau hiểu vì sao cách đo hiện tại được
  chọn, nên sẽ không "đơn giản hoá" ngược trở lại.
- **§6 nâng phép đột biến thành tiêu chí nghiệm thu bắt buộc.** Đây là thay đổi có giá trị nhất:
  nó biến một phép kiểm tuỳ hứng của người review thành nghĩa vụ của người cài đặt.
- **Dòng 30/31 kéo quy ước §7 từ văn xuôi lên bảng.** Đúng chẩn đoán "yêu cầu bị chôn trong văn
  xuôi thì bị bỏ sót" — và hiệu quả thấy ngay: người cài đặt đã bọc `output_size` lẫn
  `reference_landmarks` chuẩn xác ngay vòng đầu.

Hai điểm đặc tả còn có thể chặt hơn:

1. **Dòng 30 nói "mọi lỗi cấu hình" nhưng chỉ đòi "≥ 6 cấu hình hỏng khác nhau"** — không nêu
   **key nào**. Người cài đặt chọn 7 ca thuộc đúng hai key đã được nhắc tên ở dòng 26–29, nên
   `border_value` lọt lưới (CẦN SỬA-2). Đề nghị đặc tả liệt kê **đủ bốn key của §4** trong dòng 30.
2. **Bảng §5 nay đánh số không liên tục** (…23, 24, 26, 27, 28, 29, 30, 31, **25**) — dòng 25 nằm
   sau dòng 31. Không sai gì về kỹ thuật, nhưng khi đối chiếu thủ công rất dễ tưởng thiếu dòng 25.
   Đề nghị đánh số lại liên tục ở lần sửa đặc tả kế tiếp.

---

## 9. Việc tiếp theo

Một vòng sửa nhỏ, **hai việc, ~10 dòng**:

1. `src/preprocess/align.py:164,174` — bọc `border_value` thành `LoiCauHinh` (đoạn mã ở §6).
2. `tests/test_align.py:469-483` — thêm 3 mục `border_value` vào danh sách dòng 30.

Tuỳ chọn (🔵, người dùng quyết): đánh số ca cho dòng 31, sửa docstring lạc hậu `_mau_tong_hop`.

Sau khi sửa: chạy lại `black` / `ruff` / `pytest` (host + ARM64) và **chạy lại DB5** để xác nhận
dòng 13 vẫn đỏ.

Khi đã ĐẠT, commit theo R29:

```
feat(preprocess): P1-04 khoi can chinh khuon mat ve 112x112 bang bien doi tuong tu 5 diem moc
```

> **Về trần 2 vòng**: không còn lỗi 🔴 nào, nên chưa chạm trần. Lỗi 🟡 duy nhất là loại "sót một
> key", không phải hiểu sai yêu cầu — không có dấu hiệu mã việc quá to hay đặc tả mơ hồ.
> Nếu người dùng đánh giá `border_value` là rủi ro chấp nhận được (key tuỳ chọn, giá trị trong
> `configs/preprocess.yaml` hiện đúng, và dòng 30 của đặc tả chỉ đòi "≥ 6 cấu hình"), thì hoàn toàn
> có cơ sở để hạ CẦN SỬA-2 xuống 🔵 và commit ngay. **Đó là quyết định của người dùng, không phải
> của người review** — nên tôi vẫn ghi phán quyết theo đúng thang: còn 🟡 thì là 🔴 TRẢ LẠI.

---

# Review P1-04-align — vòng 3

| | |
|---|---|
| **Đặc tả** | `docs/dac-ta/P1-04-align.md` (bảng §5 nay **37 dòng**) |
| **Nhánh** | `feat/p1-04-align` |
| **Ngày** | 2026-08-17 |
| **Phán quyết** | ✅ **ĐẠT** — 0 lỗi 🔴, 0 lỗi 🟡, 4 góp ý 🔵 |

---

## 1. Kết quả kiểm máy — vòng 3

| Lệnh | Kết quả |
|---|---|
| `git status --short --untracked-files=all` trừ `docs/review/` | **3** ✅ |
| `git diff dev -- configs/ src/common/ scripts/` | **rỗng** ✅ |
| File cấm lọt git | không có ✅ |
| `black --check --line-length 100 src tests scripts` | 22 file sạch ✅ |
| `ruff check src tests scripts` | All checks passed ✅ |
| `pytest -q` (host) | **155 passed** = 118 cũ + 37 mới ✅ |
| `pytest -q` (container `faceid:arm64`) | **155 passed** ✅ |
| 4 lệnh `grep` §6 | cả 4 **rỗng** ✅ |
| Quét mẫu vi phạm §2 | 0 kết quả ✅ |

**Quét AST**: **37 hàm test / 37 dòng bảng §5** — khớp 1–1. Năm hàm không có `assert` trực tiếp vẫn
đúng như hai vòng trước (`dong01` theo đặc tả; `dong13/13a/14/15` uỷ quyền cho
`_kiem_diem_moc_ve_dung_vi_tri_chuan`). Không có test giả.

**Toàn bộ 8 mục §6 tiêu chí nghiệm thu: đạt.**

---

## 2. Phép đột biến quyết định — dòng 30 có thực sự phủ bốn key không

`sha256(align.py)` gốc = `0cfab6f8…064521`, **khớp lại sau cả 9 phép**.

Câu hỏi cần loại trừ dứt điểm: *dòng 30 đỏ vì nó thật sự phủ `border_value`, hay chỉ được ba ca mới
32/33/34 che?* Phép đột biến trả lời trực tiếp — nếu dòng 30 chỉ ăn theo, nó sẽ **xanh**.

| # | Phép đột biến | Ca đỏ | Kỳ vọng | KL |
|---|---|---|---|---|
| **DB11** | **Bỏ toàn bộ khối kiểm `border_value`** (`align.py:164-176`) | `dong32`, `dong33`, `dong34`, **`dong30`** | 32, 33, 34 **và** 30 | ✅ **đúng hoàn toàn** |
| **DB12** | **Bỏ kiểm `interpolation`** (`align.py:156-162`) | `dong35`, **`dong30`** | 35 **và** 30 | ✅ **đúng hoàn toàn** |

**Dòng 30 đỏ trong cả hai phép.** Nó **không** ăn theo ba ca mới — nó tự phủ `border_value` và
`interpolation` bằng chính bốn mục trong danh sách của nó. Kẽ hở "≥ N trường hợp ≠ mọi trường hợp"
mà tôi nêu ở vòng 2 đã được bịt thật, không phải bịt trên giấy.

### Hồi quy bằng đột biến — mọi phép của hai vòng trước vẫn đúng đích

| # | Phép đột biến | Ca đỏ | KL |
|---|---|---|---|
| DB5 | Cắt khung bao 5 điểm mốc, nới biên 35 %, `resize` | **`dong13`**, 13a, 14, 15, 23, 24 | ✅ §6 đạt |
| DB1 | `estimateAffinePartial2D` → `estimateAffine2D` | `dong09` (duy nhất) | ✅ |
| DB2 | Viết cứng toạ độ điểm chuẩn | `dong23` + 8 ca khác | ✅ |
| DB7 | Hoán đổi kênh BGR | `dong17` (duy nhất) | ✅ |

### Ba chốt của `border_value` tách bạch hoàn toàn

| # | Bỏ chốt nào | Ca đỏ |
|---|---|---|
| DB13 | `isinstance(mau_vien_raw, (list, tuple))` — `align.py:165` | `dong32` + `dong30` |
| DB14 | `len(mau_vien_raw) != 3` — `align.py:169` | `dong33` + `dong30` |
| DB15 | `tuple(float(v) …)` — `align.py:173` | `dong34` (duy nhất) |

**Ba chốt ↔ ba dòng, ánh xạ 1–1.** Đây là bằng chứng định lượng cho mục 5.1 bên dưới.

---

## 3. Bộ cấu hình hỏng tự dựng — 50 trường hợp, cả bốn key

Tôi dựng bộ riêng, không dùng lại danh sách của người cài đặt, cố tình thêm các biến thể "lạ"
(kiểu `dict`, `bool`, `numpy.ndarray`, lồng nhau, `NaN`, chuỗi số, ngoài dải, điểm chuẩn suy biến).

| Key | Số biến thể | Ném `LoiCauHinh` |
|---|---|---|
| `output_size` | 14 | 11 |
| `reference_landmarks` | 14 | 12 |
| `interpolation` | 7 | 6 |
| `border_value` | 15 | 10 |
| **Tổng** | **50** | **39** |

### Kết quả quan trọng nhất: **chiều nguy hiểm đã đóng hoàn toàn**

**0/50 trường hợp ném `ValueError`.** Đây là con số đáng kể nhất của vòng này. Lỗi cấu hình ném
`ValueError` chính là kịch bản §7 dựng ra để chặn — `P1-05` bắt `ValueError` để bỏ qua ảnh, nên
một lỗi cấu hình rơi vào loại đó sẽ khiến cả mẻ chạy hết với 100 % ảnh bị bỏ mà không báo gì.
Vòng 2 còn 2 trường hợp như vậy (`border_value` chuỗi và vô hướng); **vòng 3 không còn trường hợp nào**.

### 11 trường hợp không ném `LoiCauHinh` — phân loại trung thực

| Nhóm | Trường hợp | Đánh giá |
|---|---|---|
| **Hợp lệ thật, không phải lỗi** | `border_value: (0,0,0)` tuple | ✅ đúng — `isinstance` chấp nhận `tuple` là chủ ý |
| **Ép kiểu khoan dung** | `border_value: ['1','2','3']`; `output_size: [112.7, 112.7]` | `float("1")`/`int(112.7)` thành công — khoan dung có chủ ý, rủi ro thấp |
| **Giá trị lọt vì hợp lệ về kiểu** | `border_value` `[999]*3`, `[-1]*3`, `[NaN]*3`; `output_size: [True, True]` → ảnh 1×1 | 🔵 xem §6 |
| **Điểm chuẩn suy biến trong config** | `reference_landmarks` 5 điểm trùng nhau / 5 điểm thẳng hàng → ảnh một màu, không báo | 🔵 — đặc tả **không có dòng nào** phủ (dòng 7 chỉ phủ điểm mốc **nguồn**) |
| **Rò rỉ kiểu thật** | `interpolation: ["bilinear"]` → **`TypeError`** | 🔵 xem §6 — hỏng **to tiếng**, không âm thầm |
| **Giới hạn tài nguyên** | `output_size: [10⁹, 10⁹]` → `cv2.error` | không phải lỗi kiểm cấu hình; `cv2.error` không bị `P1-05` nuốt |

Không có trường hợp nào trong 11 cái này thuộc chiều nguy hiểm.

---

## 4. Kiểm hồi quy — số đo ba vòng không đổi

| Dòng | Chỉ số | Vòng 1 | Vòng 2 | **Vòng 3** |
|---|---|---|---|---|
| 16 | Sai số đưa điểm mốc về vị trí chuẩn | 5,0564×10⁻⁶ px | 5,0564×10⁻⁶ px | **5,0564×10⁻⁶ px** |
| 9 | Chênh độ dài hai vectơ hàng | < 1e-6 | 0,0000 | **0,0000** |
| 23 | Khác biệt khi đổi `reference_landmarks` | 98,99 | 98,99 | **98,99** |
| 17 | Pixel giữa với ảnh vào `[255,0,0]` | kênh 0 lớn nhất | `[255,0,0]` | **`[255,0,0]`** |
| 25 | Nạp `configs/preprocess.yaml` thật | `(112,112,3)` | `(112,112,3)` | **`(112,112,3)`** |
| 13 | Dung sai không gian ảnh ra | — | 1,875 px | **1,875 px** |
| 14 | Dung sai không gian ảnh ra | — | 0,875 px | **0,875 px** |

**Không một con số nào xê dịch qua ba vòng.** Phần toán căn chỉnh chưa bao giờ bị đụng tới.

---

## 5. Đánh giá hai điểm người cài đặt tự nêu

### 5.1. Diễn giải dòng 34 thành `["den","den","den"]` — ✅ **hợp lý, và là cách đọc tối ưu**

Đặc tả dòng 34 ghi *"`border_value` chứa **giá trị không phải số** (`"den"`)"*. Cụm `"den"` trong
ngoặc **mơ hồ**: có thể hiểu là `border_value = "den"` (cả giá trị là chuỗi) hoặc phần tử bên trong
là `"den"`. Người cài đặt chọn cách thứ hai.

**Đây là cách đọc đúng, vì ba lý do đo được:**

1. Nó làm **dòng 32/33/34 nhắm vào ba chốt khác nhau** trong `align.py` — DB13/DB14/DB15 chứng minh
   ánh xạ 1–1. Cách đọc kia sẽ khiến dòng 34 trùng đường mã với dòng 32 (cùng bị `isinstance` chặn),
   mất một ca kiểm.
2. Chính chữ *"**chứa** giá trị không phải số"* trong đặc tả nghiêng về "phần tử bên trong".
3. Nó khớp cụm *"không phải `ValueError`"* ở cột kỳ vọng: chỉ đường `float("den")` mới sinh
   `ValueError` thô; đường `isinstance` sinh `TypeError`.

**Có bỏ sót biến thể nào không?** Không. Tôi kiểm riêng cách đọc còn lại — `border_value: "den"`
(chuỗi trần) — và nó **vẫn ném `LoiCauHinh`**, do chốt `isinstance` ở `align.py:165` bắt được
(chuỗi không phải `list`/`tuple`). Cả hai cách đọc đều được phủ; chỉ khác là cách đọc của người cài
đặt phủ **thêm** một đường mã. Bộ 15 biến thể `border_value` tôi tự dựng cũng không tìm ra khoảng
trống nào giữa ba dòng.

### 5.2. Sửa thông báo lỗi `interpolation` — ✅ **đúng phạm vi, và thực ra là bắt buộc**

Người cài đặt xếp việc này vào "sửa vặt < 10 dòng trong phạm vi lỗi 🟡 được giao". **Đánh giá đó
khiêm tốn quá — nó không phải sửa vặt tuỳ ý, mà là yêu cầu trực tiếp của đặc tả.**

Dòng 35 mới thêm đòi: *"raise `LoiCauHinh` **nêu các giá trị được chấp nhận**"* với assert tối thiểu
*"thông báo chứa `interpolation`"*. Thông báo cũ ở vòng 2 là:

```python
f"Kiểu nội suy không hỗ trợ: '{ten_noi_suy}'. …"
```

— **không chứa chuỗi `interpolation`**, nên `pytest.raises(LoiCauHinh, match="interpolation")` sẽ đỏ.
Muốn dòng 35 xanh chỉ có hai đường: sửa thông báo, hoặc nới assert của ca test. Sửa thông báo là
đường đúng (nới assert là "sửa test cho đi qua" — lỗi CB-6). Bản mới ở `align.py:159`:

```python
f"Cấu hình 'interpolation' không hợp lệ: {ten_noi_suy!r}. "
f"Các giá trị hợp lệ: {sorted(_KIEU_NOI_SUY)}"
```

nêu đủ tên key **và** danh sách giá trị hợp lệ — đúng cả chữ lẫn ý của dòng 35. Nằm gọn trong phạm
vi, không cần viện tới ngoại lệ "sửa vặt < 10 dòng" của R38.

---

## 6. 🔵 Góp ý (không chặn — người dùng quyết định)

- **`align.py:157` — `interpolation` kiểu không băm được cho `TypeError`.**
  `cfg["interpolation"] = ["bilinear"]` (YAML sinh ra khi gõ nhầm thành mục danh sách:
  `interpolation:` xuống dòng `- bilinear`) làm `ten_noi_suy not in _KIEU_NOI_SUY` ném
  `TypeError: unhashable type: 'list'`.
  **Vì sao chỉ là 🔵, không phải 🟡**: `TypeError` **không** bị `P1-05` nuốt (nó bắt `ValueError`),
  nên cả mẻ **dừng to tiếng** — đúng hướng an toàn mà §7 muốn. Thiệt hại chỉ là traceback khó đọc
  thay vì thông báo rõ ràng. Dòng 30 của đặc tả đòi "≥ 2 biến thể mỗi key" và người cài đặt đã có
  đủ (`"xyz"`, `42`), nên đây **không** phải vi phạm đặc tả.
  **Sửa (2 dòng)**, nếu người dùng muốn:
  ```python
  ten_noi_suy = cfg.get("interpolation", "bilinear")
  if not isinstance(ten_noi_suy, str) or ten_noi_suy not in _KIEU_NOI_SUY:
  ```
- **`reference_landmarks` suy biến trong config không bị chặn** (5 điểm trùng nhau hoặc thẳng hàng
  → ảnh ra một màu, không ngoại lệ). Đây là **khoảng trống của đặc tả**, không phải của mã: §5 dòng 7
  chỉ phủ điểm mốc **nguồn** suy biến. Đã nêu ở vòng 1 và vòng 2, vẫn còn. Nếu người dùng thấy đáng,
  đây là một dòng mới cho `spec-writer` chứ không phải việc trả lại người cài đặt.
- **`border_value` lọt giá trị ngoài dải** (`[999,999,999]`, `[-1,-1,-1]`, `[NaN]*3`) và
  **`output_size: [True, True]` cho ảnh 1×1**. Cả hai đều cần config sai một cách khá kỳ quặc; rủi ro
  thực tế thấp. Ghi lại để nếu sau này `P1-05` sinh ảnh lạ thì có chỗ tra.
- Ba góp ý cũ vẫn treo, người dùng chưa quyết: thứ tự `[rộng, cao]` chưa được kiểm (mọi kích thước
  đều vuông); dòng 31 chưa đánh số ca; docstring `_mau_tong_hop` (`test_align.py:57-61`) vẫn nhắc
  cách đo đã bị gỡ bỏ.

---

## 7. ⚠️ Ghi nhận về phạm vi ghi file (ngoài trách nhiệm người cài đặt)

`git diff dev --name-only` cho thấy nhánh này còn sửa **`.claude/agents/spec-writer.agent.md`**
(+15 dòng, commit `0cd715b`) — ghi lại đúng bài học "≥ N trường hợp ≠ mọi trường hợp" từ vòng 2.

**Nội dung hoàn toàn chính đáng và hữu ích.** Nhưng bảng phân vai ở `CLAUDE.md` §2.9 chỉ cho
`spec-writer` ghi vào `docs/dac-ta/` và `configs/` — `.claude/agents/**` không nằm trong danh sách của
bất kỳ vai nào. **Không phải lỗi người cài đặt** (3 file mã nguồn của họ đúng danh sách trắng), nên
không ảnh hưởng phán quyết. Nêu ra để người dùng biết và quyết định: hoặc bổ sung `.claude/` vào
bảng §2.9 cho một vai nào đó, hoặc tách thay đổi này thành commit riêng ngoài nhánh mã việc.

---

## 8. Tổng kết ba vòng review

### Số liệu

| | Vòng 1 | Vòng 2 | Vòng 3 |
|---|---|---|---|
| Dòng bảng §5 đặc tả | 25 | 32 | **37** |
| Hàm test | 25 | 32 | **37** |
| `pytest -q` host / ARM64 | 143 / 143 | 150 / 150 | **155 / 155** |
| Lỗi 🔴 CHẶN-A | 0 | 0 | **0** |
| Lỗi 🔴 CHẶN-B | **2** | 0 | **0** |
| Lỗi 🟡 CẦN SỬA | 1 | 1 | **0** |
| Phép đột biến đã chạy | 7 | 6 | **9** |
| Phép đột biến **sai đích** | **1** (DB5) | 0 | **0** |
| Cấu hình hỏng tự dựng | — | 19 (4 sai) | **50 (0 rò `ValueError`)** |

Tổng cộng **22 phép đột biến** và **69 cấu hình hỏng** tự dựng qua ba vòng.

### Kết luận quan trọng nhất — cho nhật ký tuần và Chương 3

> **Cả hai lỗi chặn của mã việc này đều nằm ở cách đặc tả tự kiểm chứng, không nằm ở mã nguồn.**

Bằng chứng định lượng: **sai số căn chỉnh là 5,0564×10⁻⁶ pixel ngay từ vòng 1 và không đổi qua cả ba
vòng.** Cùng với nó, tính chất "biến đổi tương tự" (chênh độ dài hai vectơ hàng = 0), thứ tự kênh BGR,
và việc đọc điểm chuẩn từ config — tất cả đều đúng ngay lần đầu. Phần **toán học chịu lực nhất của
Phase 1 chưa bao giờ sai một lần nào.**

Hai lỗi 🔴 CHẶN-B của vòng 1 là:

1. **Ba ca "bất biến" không phân biệt được căn chỉnh thật với cắt ảnh theo khung bao.** Tiêu chí đo
   (sai khác mức xám trung bình) phụ thuộc vào ảnh thử — thứ đặc tả không quy định — và hai trong ba
   ca **bất lực về mặt cấu trúc** vì phép cắt khung bao vốn đã bất biến với tịnh tiến và phóng đại.
2. **Quy ước lỗi §7 chỉ nằm trong văn xuôi, không có dòng nào trong bảng §5 kiểm nó.** Hệ quả: lỗi
   cấu hình ném `ValueError`, mà `P1-05` sẽ đọc thành "bỏ qua ảnh này" và chạy hết cả mẻ với 100 %
   ảnh bị bỏ, không một dòng cảnh báo.

Lỗi 🟡 của vòng 2 cùng một gốc: dòng 30 viết *"≥ 6 cấu hình hỏng"* thay vì liệt kê đích danh, nên
`border_value` lọt sạch.

### Ba bài học rút ra

1. **Bộ test xanh không chứng minh bộ test đúng chỗ.** Vòng 1 có 143/143 xanh, `black`/`ruff` sạch,
   25/25 dòng đặc tả có ca test — mà vẫn để lọt một bản cài đặt chỉ cắt ảnh. Chỉ phép đột biến phát
   hiện ra. Đây là lần thứ ba trong dự án phép đột biến cho kết quả quyết định (sau `P1-01`, `P1-02`).
2. **Tiêu chí nghiệm thu phải độc lập với thứ đặc tả không kiểm soát.** "Sai khác mức xám < 5,0" nghe
   định lượng nhưng vô nghĩa nếu không quy định ảnh thử: cùng một bản cài đặt đúng cho 0,203 với ảnh
   mượt và 8,999 với ảnh có kết cấu. Tiêu chí thay thế — "chấm sáng tại điểm mốc phải rơi đúng toạ độ
   điểm chuẩn" — đo thẳng thứ cần đo và có dung sai đo được (0,875–1,875 px), giống hệt trên x86-64
   lẫn ARM64.
3. **"≥ N trường hợp" không bao giờ tương đương "mọi trường hợp".** Người cài đặt sẽ chọn N trường hợp
   dễ nghĩ ra nhất — thường thuộc các mục đặc tả vừa nhắc tên — và phần còn lại lọt sạch. Phải liệt kê
   đích danh từng mục kèm số biến thể tối thiểu. Bài học này đã được ghi vào
   `.claude/agents/spec-writer.agent.md`.

### Nhận xét về mã nguồn

Chất lượng mã ổn định qua cả ba vòng: không lần nào có `print()`, `except:` trần, hardcode tham số,
thư viện ngoài danh sách, import chéo tầng, hay test giả. Mỗi vòng người cài đặt sửa **đúng phạm vi
được giao**, không phát sinh lỗi mới ở chỗ khác — không có dấu hiệu mã việc quá to. Ba quyết định tự
nêu ở vòng 2 và hai ở vòng 3 đều được kiểm chứng là hợp lý, trong đó cách diễn giải dòng 34 còn **tốt
hơn** cách đọc hiển nhiên vì tách được ba đường mã.

---

## 9. Việc tiếp theo

**Đã ĐẠT — được commit.** Theo R29:

```
feat(preprocess): P1-04 can chinh khuon mat ve 112x112 bang bien doi tuong tu 5 diem moc
```

Sau khi commit: gộp `feat/p1-04-align` vào `dev`, rồi chuyển sang mã việc **`P1-05`**
(`scripts/preprocess.py` — duyệt thư mục, gọi `can_chinh`, ghi ảnh và manifest).

⚠️ **Lưu ý bàn giao cho `P1-05`**: khối này phân biệt rạch ròi `ValueError` (bỏ qua ảnh này) với
`LoiCauHinh` (cấu hình hỏng, dừng cả mẻ) — đã kiểm chứng bằng 50 cấu hình hỏng, **0 trường hợp rò
`ValueError`**. Đặc tả `P1-05` phải bắt **đúng hai loại này riêng biệt**; bắt `Exception` chung sẽ
xoá sạch công sức ba vòng review của mã việc này.
