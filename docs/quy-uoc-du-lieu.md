# Quy ước dữ liệu khuôn mặt

> Phase 1 bước 1.1. Đây là **nguồn sự thật** về cách đặt tên và tổ chức dữ liệu.
> Mọi script trong `scripts/` và mọi đặc tả từ `P1-02` trở đi đều tham chiếu về file này.
>
> ⚠️ Toàn bộ `data/` bị `.gitignore` chặn. File này mô tả **quy ước**, không chứa dữ liệu.

---

## 1. Định danh người dùng

Dùng **mã ẩn danh**, không dùng tên thật:

```
u01, u02, u03        gallery — người được đăng ký vào hệ thống
x01, x02, … x07      impostor in-domain — người quen, KHÔNG đăng ký
```

Ba lý do dùng mã thay vì tên:

1. Tên tiếng Việt có dấu gây lỗi đường dẫn trên các hệ điều hành khác nhau.
2. Tên xuất hiện trong tên file sẽ theo vào ảnh chụp màn hình, biểu đồ, phụ lục báo cáo — làm lộ danh
   tính người tham gia một cách không cần thiết.
3. Nhất quán với luận điểm quyền riêng tư của chính đề tài.

Bảng ánh xạ mã sang người thật để **ở máy cá nhân**, đặt tại `data/anh-xa-danh-tinh.txt`. Thư mục
`data/` đã bị gitignore nên nó không bao giờ lên kho mã nguồn.

> ⛔ **Tiền tố `x` không bao giờ được đưa vào gallery.** Người in-domain là *người lạ* về mặt hệ thống;
> đăng ký nhầm họ sẽ làm hỏng toàn bộ phép đo tỉ lệ chấp nhận sai.

---

## 2. Điều kiện chụp

Mỗi ảnh gallery gắn với một tổ hợp **tư thế × ánh sáng**:

| Trường | Giá trị hợp lệ |
|---|---|
| `pose` | `frontal`, `left`, `right`, `up`, `down` |
| `light` | `bright`, `dim` |

Năm tư thế nhân hai mức sáng cho **10 tổ hợp**. Chỉ tiêu tối thiểu 100 ảnh mỗi người, nên **mỗi tổ hợp
ít nhất 10 ảnh**. Thu đều tay quan trọng hơn thu nhiều: 100 ảnh chia đều 10 tổ hợp có giá trị hơn hẳn
150 ảnh mà 120 ảnh là chính diện đủ sáng.

Hai mức sáng định nghĩa theo điều kiện thật, không theo số đo lux chính xác:

- `bright` — ban ngày hoặc bật đèn trần, mặt nhìn rõ chi tiết
- `dim` — chỉ đèn ngủ hoặc ánh sáng hắt, mặt còn nhận ra được nhưng tối rõ rệt

Ghi lại mô tả thực tế của từng buổi chụp vào manifest (§5), vì bước 1.7 cần đối chiếu.

---

## 3. Quy ước tên file

```
<id>_<pose>_<light>_<idx>.png
```

Ví dụ: `u01_frontal_bright_001.png` · `u02_left_dim_007.png` · `x03_frontal_bright_012.png`

- `idx` **ba chữ số, đệm không**, bắt đầu từ `001`, đánh liên tục **trong phạm vi một tổ hợp**
  `(id, pose, light)` — không đánh liên tục toàn bộ thư mục.
- Toàn bộ chữ thường, không dấu, không khoảng trắng.
- Bốn trường ngăn bằng dấu gạch dưới, nên **tách được bằng `split("_")`** mà không cần biểu thức chính quy.

> Đề cương ghi dạng `<user_id>_<condition>_<idx>`. Quy ước này **tách `condition` thành hai trường
> riêng** `pose` và `light`. Lý do: bước 1.7 và 1.13 cần thống kê theo từng chiều độc lập — ví dụ so
> độ nét giữa `bright` và `dim` bất kể tư thế. Gộp một trường thì phải cắt chuỗi thêm một lần nữa.

---

## 4. Cây thư mục

```
data/
├── anh-xa-danh-tinh.txt         mã ↔ người thật, chỉ ở máy cá nhân
│
├── raw/                         ẢNH GỐC — gallery
│   ├── u01/  u01_frontal_bright_001.png …
│   ├── u02/
│   └── u03/
│
├── impostor/
│   ├── lfw_original/            ① LFW gốc, giữ nguyên cấu trúc và tên file của bộ dữ liệu
│   ├── lfw_adapted/             ② LFW sau hiệu chỉnh miền — GIỮ NGUYÊN tên file của ①
│   └── indomain/                ③ người quen, chụp bằng chính camera hệ thống
│       ├── x01/  x01_frontal_bright_001.png …
│       └── …
│
├── processed/                   ĐÃ CROP + ALIGN 112×112, giữ nguyên tên file nguồn
│   ├── raw/u01/…
│   ├── impostor/lfw_original/…
│   ├── impostor/lfw_adapted/…
│   └── impostor/indomain/x01/…
│
├── spoof/                       BỘ TẤN CÔNG
│   ├── live/    live_u01_001.png
│   ├── print/   print_u01_001.png
│   └── screen/  screen_u01_001.png
│
├── embeddings/                  vector đặc trưng đã đăng ký
└── splits/                      danh sách chia tập
```

**Hai quy tắc giữ tên file:**

- `lfw_adapted/` **giữ nguyên tên file** của `lfw_original/`. Nhờ vậy đối chiếu được từng ảnh trước và
  sau hiệu chỉnh, và bảo đảm hai tập chia **cùng danh tính về cùng phía** — nếu không thì hai con số
  `FAR_lfw` và `FAR_adapt` không so sánh được với nhau.
- `processed/` **phản chiếu đúng cấu trúc và tên** của nguồn. Nhìn một file trong `processed/` là truy
  ngược được về ảnh gốc mà không cần bảng tra.

---

## 5. Manifest

Mỗi thư mục dữ liệu tự thu kèm một file `manifest.csv` do `scripts/collect_faces.py` ghi:

```csv
file,id,pose,light,idx,timestamp,camera,width,height,note
u01_frontal_bright_001.png,u01,frontal,bright,1,2026-08-15T09:12:33+07:00,Logitech C270,1280,720,den tran
```

Manifest tồn tại vì ba việc sau đều cần nó và đều rất phiền nếu phải suy ngược từ tên file:

- Bước 1.7 đo đặc trưng miền dữ liệu theo từng điều kiện chụp
- Bước 1.11 chia tập mà không để cùng một buổi chụp rơi cả vào train lẫn test
- Bước 1.13 thống kê phân bố dữ liệu

Cột `note` ghi mô tả thật của buổi chụp — *"đèn trần + rèm mở"*, *"chỉ đèn bàn"*. Chính cột này giúp
giải thích các bất thường phát hiện ở bước kiểm chất lượng.

---

## 6. Định dạng ảnh

**Dùng PNG cho mọi dữ liệu tự thu.** Không dùng JPG.

Lý do không phải thẩm mỹ:

- Bước 1.7 đo **độ nét** (phương sai Laplacian) và **mức nhiễu** để hiệu chỉnh LFW. Nén JPEG làm mượt
  tần số cao và thêm nhiễu khối — tức là **làm sai lệch đúng những đại lượng đang đo**.
- Bộ dữ liệu tấn công còn nhạy hơn. Mô hình chống giả mạo nhận biết ảnh in và màn hình qua vân lưới và
  đặc trưng tần số. Nếu ảnh `live` và ảnh `print` được nén khác nhau, mô hình có thể học **dấu vết nén**
  thay vì dấu vết tấn công — cho ra kết quả cao giả tạo và sụp khi gặp dữ liệu thật.

`data/impostor/lfw_original/` là ngoại lệ: giữ nguyên định dạng gốc của bộ dữ liệu, vì không tự thu.
Sự khác biệt định dạng này chính là một phần của khoảng cách miền mà bước 1.8 phải xử lý, và **phải
được nêu trong báo cáo**.

`data/processed/` cũng dùng PNG — ảnh đã qua một lần nén rồi nén tiếp sẽ chồng nhiễu.

**Độ phân giải khi thu**: cố định theo `configs/capture.yaml`, mặc định 1280×720. Ghi vào manifest.
Không đổi độ phân giải giữa chừng; nếu buộc phải đổi thì ghi rõ mốc thời gian, vì nó tạo ra hai miền
dữ liệu khác nhau trong cùng một tập.

---

## 7. Chia tập

```
data/splits/
├── enroll.txt                  gallery — dùng sinh embedding đăng ký
├── val.txt                     gallery — quét ngưỡng
├── test.txt                    gallery — báo cáo kết quả
├── impostor_lfw_val.txt        ┐
├── impostor_lfw_test.txt       │
├── impostor_adapt_val.txt      ├─ mỗi tập impostor chia đôi
├── impostor_adapt_test.txt     │
├── impostor_indomain_val.txt   │
└── impostor_indomain_test.txt  ┘
```

Mỗi file là danh sách đường dẫn tương đối tính từ `data/`, mỗi dòng một ảnh.

**Ba quy tắc chia, vi phạm là hỏng số liệu:**

1. **Chia theo danh tính, không chia theo ảnh.** Một người chỉ được nằm ở một phía. Cùng một người
   xuất hiện ở cả `val` lẫn `test` sẽ cho kết quả lạc quan giả tạo.
2. **`lfw_val` và `adapt_val` phải chứa cùng danh tính**, tương tự cho `test`. Nếu chia khác nhau thì
   `FAR_lfw` và `FAR_adapt` đo trên hai nhóm người khác nhau, và toàn bộ phân tích khoảng cách miền
   mất ý nghĩa.
3. **Ngưỡng chốt trên `val`, kết quả báo cáo trên `test`.** Chọn ngưỡng trên tập test là lỗi phương
   pháp nghiêm trọng.

Với gallery chỉ 2–3 người thì không chia theo danh tính được — chia theo **buổi chụp**: ảnh của một
buổi chỉ nằm ở một phía. Manifest có cột `timestamp` chính là để làm việc này.

---

## 8. Bộ dữ liệu tấn công

Ba nhánh `live/`, `print/`, `screen/`, mỗi nhánh tối thiểu 30 mẫu.

```
<loai>_<id>_<idx>.png
```

Ví dụ: `live_u01_001.png` · `print_u01_001.png` · `screen_u02_003.png`

Nguyên tắc quan trọng nhất: **ba nhánh phải chụp trong cùng điều kiện**. Cùng camera, cùng khoảng cách,
cùng ánh sáng, cùng độ phân giải, cùng định dạng. Chỉ khác đúng một biến — mặt thật, ảnh in, hay màn hình.

Nếu ảnh `live` chụp ban ngày còn ảnh `print` chụp buổi tối, mô hình sẽ phân biệt được **bằng độ sáng**
chứ không bằng dấu vết tấn công. Kết quả đo sẽ đẹp và hoàn toàn vô giá trị.

Ghi vào manifest riêng của `spoof/`: loại giấy in và máy in với nhánh `print`, kiểu màn hình và mức độ
sáng màn hình với nhánh `screen`.

---

## 9. Ràng buộc bắt buộc

- ⛔ **Chỉ thu ảnh của người đã được thông báo rõ mục đích và đồng ý.** Không lấy ảnh từ mạng xã hội,
  không trích từ camera an ninh, không chụp người qua đường.
- ⛔ **Không commit bất kỳ ảnh nào.** `.gitignore` đã chặn `data/`, kiểm lại bằng `git status` trước
  mỗi lần commit.
- ⛔ **Không gửi dữ liệu khuôn mặt lên dịch vụ ngoài** — kể cả để thử nghiệm.
- ⛔ **Người in-domain (`x*`) không bao giờ vào gallery.**
- Bộ LFW: trích dẫn công trình gốc và nêu giấy phép trong báo cáo; **không phát hành lại** ảnh LFW
  kèm mã nguồn.

---

## 10. Checklist trước khi khép Phase 1

- [ ] Gallery 2–3 người, mỗi người ≥ 100 ảnh, **mỗi tổ hợp tư thế × ánh sáng ≥ 10 ảnh**
- [ ] Impostor in-domain 5–7 người, mỗi người ≥ 20 ảnh
- [ ] LFW ≥ 100 danh tính, bản gốc và bản hiệu chỉnh **cùng tên file**
- [ ] Bộ tấn công ≥ 30 mẫu mỗi nhánh, ba nhánh cùng điều kiện chụp
- [ ] Mọi ảnh trong `processed/` đúng 112×112
- [ ] Manifest đầy đủ cho mọi thư mục tự thu
- [ ] Các file trong `splits/` không có danh tính trùng giữa `val` và `test`
- [ ] `lfw_val` và `adapt_val` cùng danh tính; tương tự cho `test`
- [ ] `git status` không hiện file ảnh nào
