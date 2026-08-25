# Kịch bản kiểm máy — quy ước

Thư mục này chứa **kịch bản do agent viết ra và người dùng chạy**. Đây là chỗ duy nhất trong repo mà
lệnh chạy được đóng gói lại thành tệp.

Lý do tồn tại: theo **R42**, không agent nào được chạy mã của đồ án. Nhưng review mà không có số liệu
máy thì chỉ là đọc code bằng mắt — đúng thứ mà `code-review.instructions.md` cấm. Cách dung hoà:
agent viết ra **đúng một tệp**, người dùng gõ **đúng một lệnh**, rồi dán nguyên khối kết quả về.

---

## Đặt tên

```
docs/kiem-may/<mã việc>.<vai>.ps1
```

| Vai | Ai viết | Chạy khi nào |
|---|---|---|
| `.coder` | agent `coder` | Sau Nhịp 2, và sau mỗi lần sửa theo biên bản review |
| `.review` | agent `code-reviewer` | Sau khi người dùng đã dán kết quả `.coder` về |
| `.do` | agent `training` | Trên máy đo, ở Cổng C |

Ví dụ: `P3-01b-chan-vo-cung.coder.ps1`

Kịch bản **được commit** cùng mã việc. Nó là bằng chứng cho biết con số trong biên bản review sinh ra
từ đâu — không có nó thì biên bản không tái lập được.

---

## Bảy yêu cầu bắt buộc

1. **Chạy bằng một lệnh duy nhất.** Không hỏi gì giữa chừng, không cần tham số.

   ```bash
   powershell -ExecutionPolicy Bypass -File docs/kiem-may/<tên>.ps1
   ```

2. **In mốc phân đoạn rõ ràng** để người dùng dán về không lẫn, và agent đọc không đoán mò:

   ```
   ===== [1/9] black --check =====
   <đầu ra thật>
   ===== HẾT [1/9] · mã thoát = 0 =====
   ```

3. **In mã thoát của từng đoạn.** Đây là thứ agent đọc để biết đạt hay không. Không được nuốt lỗi.

4. **Tự khôi phục mọi thứ nó sửa.** Kiểm đột biến phải: sao lưu ra thư mục tạm **ngoài repo** → sửa →
   chạy → khôi phục từ bản sao lưu → in `sha256` → so với giá trị đã in trước khi sửa. In cả hai giá
   trị ra màn hình, không chỉ in "đã khôi phục".

5. **Kết thúc bằng `git status --short --untracked-files=all`.** Nếu kịch bản làm bẩn cây làm việc thì
   dòng này lộ ra ngay.

6. **Không bao giờ**: `git commit`, `git push`, `git checkout`, dựng image Docker mới, `pip install`,
   xoá tệp trong `data/` hay `results/`.

7. **Docker chỉ dùng `faceid:arm64`** (R43). Không `docker build -t <tên khác>`, không giữ image tạm.

---

## Khung mẫu

```powershell
# docs/kiem-may/<mã việc>.<vai>.ps1
# Sinh bởi: <tên agent> · Mã việc: <mã> · Vòng: <n>
# Chạy: powershell -ExecutionPolicy Bypass -File docs/kiem-may/<tên>.ps1

$ErrorActionPreference = "Continue"
$goc = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $goc

function Doan($so, $ten, $khoi) {
    Write-Output ""
    Write-Output "===== [$so] $ten ====="
    & $khoi
    Write-Output "===== HET [$so] - ma thoat = $LASTEXITCODE ====="
}

Doan "1/5" "black --check" { python -m black --check --line-length 100 src tests }
Doan "2/5" "ruff check"    { python -m ruff check src tests }
Doan "3/5" "pytest host"   { python -m pytest -q }
Doan "4/5" "pytest ARM64"  {
    docker run --rm -v "${goc}:/app" -w /app faceid:arm64 python3 -m pytest -q
}
Doan "5/5" "pham vi tep"   { git status --short --untracked-files=all }

Write-Output ""
Write-Output "===== XONG - dan toan bo doan tren ve cho agent ====="
```

---

## Mẫu một phép đột biến

Phần khó nhất và cũng là phần dễ làm hỏng repo nhất. Bản sao lưu **phải nằm ngoài repo** để `git
status` không nhìn thấy nó, và phải khôi phục kể cả khi bộ kiểm thử ném lỗi.

```powershell
function DotBien($so, $ten, $tep, $tim, $thay, $caDoMongDoi) {
    $luu = Join-Path $env:TEMP ("kiem_" + [IO.Path]::GetRandomFileName())
    Copy-Item $tep $luu
    $truoc = (Get-FileHash $tep -Algorithm SHA256).Hash
    Write-Output ""
    Write-Output "===== [$so] DOT BIEN: $ten ====="
    Write-Output "Tep      : $tep"
    Write-Output "Ca do mong doi: $caDoMongDoi"
    Write-Output "sha256 truoc  : $truoc"
    try {
        (Get-Content $tep -Raw).Replace($tim, $thay) |
            Set-Content $tep -NoNewline -Encoding utf8
        python -m pytest -q 2>&1 | Select-Object -Last 25
    } finally {
        Copy-Item $luu $tep -Force
        Remove-Item $luu -Force
        $sau = (Get-FileHash $tep -Algorithm SHA256).Hash
        Write-Output "sha256 sau    : $sau"
        if ($truoc -eq $sau) { Write-Output "KHOI PHUC: KHOP" }
        else { Write-Output "KHOI PHUC: *** KHONG KHOP - DUNG LAI, KIEM TAY ***" }
    }
    Write-Output "===== HET [$so] ====="
}
```

Đọc kết quả: phép đột biến **phải làm đỏ đúng ca mà đặc tả chỉ định**, không thừa không thiếu. Phá mã
mà bộ kiểm thử vẫn xanh nghĩa là chỗ đó chưa có ca nào canh — lỗi của bộ kiểm thử, không phải của
phép đột biến.

---

## Người dùng cần làm gì

1. Chạy đúng một lệnh mà agent đưa
2. Dán **toàn bộ** đầu ra về, kể cả phần trông như rác — dòng lỗi thường nằm ở chỗ không ngờ
3. Nếu kịch bản treo hoặc báo `KHONG KHOP` ở phần khôi phục: dừng, báo lại, **không chạy tiếp**

Không cần đọc hiểu đầu ra. Việc đọc là của agent.
