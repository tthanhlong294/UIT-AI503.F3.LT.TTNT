# docs/kiem-may/P3-01b-chan-gia-tri-hong.coder.ps1
# Sinh boi: coder . Ma viec: P3-01b-chan-gia-tri-hong . Vong: 1
# Chay: powershell -ExecutionPolicy Bypass -File docs/kiem-may/P3-01b-chan-gia-tri-hong.coder.ps1
#
# Va 3 lo hong G5/G6/G7 o src/recognizer/arcface_backend.py va them 9 ca test moi
# (dong 39-47) vao tests/test_recognizer.py. Kich ban gom 12 doan:
#   1-2  black + ruff
#   3-4  pytest toan kho + pytest rieng test_recognizer.py (host)
#   5    pytest trong container faceid:arm64
#   6-7  quet "== 0.0" va quet so viet cung
#   8-11 bon phep dot bien (DB8, DB9, DB10, va chay lai DB2 cua P3-01)
#   12   git status (pham vi tep)

$ErrorActionPreference = "Continue"
$goc = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $goc

function Doan($so, $ten, $khoi) {
    Write-Output ""
    Write-Output "===== [$so] $ten ====="
    & $khoi
    Write-Output "===== HET [$so] - ma thoat = $LASTEXITCODE ====="
}

function DotBien($so, $ten, $tep, $tim, $thay, $caDoMongDoi) {
    $luu = Join-Path $env:TEMP ("kiem_" + [IO.Path]::GetRandomFileName())
    Copy-Item $tep $luu
    $truoc = (Get-FileHash $tep -Algorithm SHA256).Hash
    Write-Output ""
    Write-Output "===== [$so] DOT BIEN: $ten ====="
    Write-Output "Tep            : $tep"
    Write-Output "Ca do mong doi phai do : $caDoMongDoi"
    Write-Output "sha256 truoc   : $truoc"
    try {
        (Get-Content $tep -Raw).Replace($tim, $thay) |
            Set-Content $tep -NoNewline -Encoding utf8
        python -m pytest -q tests/test_recognizer.py -v 2>&1
    } finally {
        Copy-Item $luu $tep -Force
        Remove-Item $luu -Force
        $sau = (Get-FileHash $tep -Algorithm SHA256).Hash
        Write-Output "sha256 sau     : $sau"
        if ($truoc -eq $sau) { Write-Output "KHOI PHUC: KHOP" }
        else { Write-Output "KHOI PHUC: *** KHONG KHOP - DUNG LAI, KIEM TAY ***" }
    }
    Write-Output "===== HET [$so] ====="
}

# ============================================================================
# 1-2: dinh dang va lint
# ============================================================================

Doan "1/12" "black --check --line-length 100 src tests" {
    python -m black --check --line-length 100 src tests
}

Doan "2/12" "ruff check src tests" {
    python -m ruff check src tests
}

# ============================================================================
# 3-5: pytest tren host va trong container faceid:arm64
# ============================================================================

Doan "3/12" "pytest -q toan kho (mong doi 388 passed: 379 cu + 9 moi)" {
    python -m pytest -q
}

Doan "4/12" "pytest tests/test_recognizer.py -v (mong doi 47 passed)" {
    python -m pytest -q tests/test_recognizer.py -v
}

Doan "5/12" "pytest tests/test_recognizer.py trong faceid:arm64 (KHONG dung image moi, R43)" {
    docker run --rm -v "${goc}:/app" -w /app faceid:arm64 python3 -m pytest -q tests/test_recognizer.py -v
}

# ============================================================================
# 6-7: quet chuan bang mat - khong so viet cung, khong con chot "== 0.0" don doc
# ============================================================================

Doan "6/12" 'Quet "== 0.0" trong arcface_backend.py (moi dong phai co math.isfinite ke ben)' {
    Select-String -Path "src/recognizer/arcface_backend.py" -Pattern "== 0\.0"
}

Doan "7/12" 'Quet so viet cung 127.5|128|512|112 trong arcface_backend.py (mong doi RONG)' {
    Select-String -Path "src/recognizer/arcface_backend.py" -Pattern "\b(127\.5|128|512|112)\b"
}

# ============================================================================
# 8: DB8 - bo chot math.isfinite trong _doc_so_thuc
# Du doan: dong 39, 40, 41, 42 do. Dong 43 KHONG duoc do (khong duoc va qua tay).
# ============================================================================

DotBien "8/12" "DB8 - bo chot isfinite trong _doc_so_thuc, tra thang float(gia_tri)" `
    "src/recognizer/arcface_backend.py" `
    "if not math.isfinite(gia_tri_float):" `
    "if False:  # DOT BIEN DB8 - da vo hieu hoa chot isfinite" `
    "test_dong39, test_dong40, test_dong41, test_dong42 phai DO. test_dong43 KHONG duoc do."

# ============================================================================
# 9: DB9 - bo chot NaN cho do dai vecto (ca trich_dac_trung LAN enroll)
# Hai phep thay the trong cung mot chu ky sao luu/khoi phuc de vo hieu hoa CA BA cho chot
# (dong 260 va 296 dung chung mot doan van ban, dong 302 dung ten bien khac).
# Du doan: dong 44, 45 do.
# ============================================================================

$tep9 = "src/recognizer/arcface_backend.py"
$luu9 = Join-Path $env:TEMP ("kiem_" + [IO.Path]::GetRandomFileName())
Copy-Item $tep9 $luu9
$truoc9 = (Get-FileHash $tep9 -Algorithm SHA256).Hash
Write-Output ""
Write-Output "===== [9/12] DOT BIEN: DB9 - bo chot NaN do_dai (trich_dac_trung + enroll) ====="
Write-Output "Tep            : $tep9"
Write-Output "Ca do mong doi phai do : test_dong44, test_dong45"
Write-Output "sha256 truoc   : $truoc9"
try {
    $noiDung9 = Get-Content $tep9 -Raw
    # Dong 260 va 296 dung chung mot cau chu (bien do_dai) -> mot lan .Replace() la du ca hai.
    $noiDung9 = $noiDung9.Replace(
        "if not math.isfinite(do_dai) or do_dai == 0.0:",
        "if do_dai == 0.0:  # DOT BIEN DB9"
    )
    # Dong 302 dung ten bien rieng (do_dai_trung_binh) -> can mot lan .Replace() nua.
    $noiDung9 = $noiDung9.Replace(
        "if not math.isfinite(do_dai_trung_binh) or do_dai_trung_binh == 0.0:",
        "if do_dai_trung_binh == 0.0:  # DOT BIEN DB9"
    )
    Set-Content $tep9 -Value $noiDung9 -NoNewline -Encoding utf8
    python -m pytest -q tests/test_recognizer.py -v 2>&1
} finally {
    Copy-Item $luu9 $tep9 -Force
    Remove-Item $luu9 -Force
    $sau9 = (Get-FileHash $tep9 -Algorithm SHA256).Hash
    Write-Output "sha256 sau     : $sau9"
    if ($truoc9 -eq $sau9) { Write-Output "KHOI PHUC: KHOP" }
    else { Write-Output "KHOI PHUC: *** KHONG KHOP - DUNG LAI, KIEM TAY ***" }
}
Write-Output "===== HET [9/12] ====="

# ============================================================================
# 10: DB10 - thay choi doi chieu input_size bang if False:
# Du doan: chi dong 46 do.
# ============================================================================

DotBien "10/12" "DB10 - vo hieu hoa chot doi chieu input_size voi do thi ONNX" `
    "src/recognizer/arcface_backend.py" `
    "if la_kich_thuoc_tinh and kich_thuoc_dau_vao_onnx != kich_thuoc_vao:" `
    "if False:  # DOT BIEN DB10 - da vo hieu hoa chot input_size" `
    "CHI test_dong46 phai do."

# ============================================================================
# 11: chay lai DB2 cua P3-01 (bo chuan hoa, dua thang 0-255 vao mo hinh)
# Chung minh ma viec nay KHONG lam hong la chan cu. Du doan: dong 12 va 27 van do nhu truoc.
# Dong 27 can data/processed/lfw_original/ that - neu may nay chua co du lieu, ca do se SKIP
# thay vi do; ghi ro trang thai nay khi doc ket qua.
# ============================================================================

DotBien "11/12" "DB2 (chay lai tu P3-01) - bo (x-mean)/scale, dua tho 0-255 vao mo hinh" `
    "src/recognizer/arcface_backend.py" `
    "tensor = (anh_dung_kenh.astype(np.float32) - do_lech) / ty_le" `
    "tensor = anh_dung_kenh.astype(np.float32)  # DOT BIEN DB2 lai" `
    "test_dong12 phai do. test_dong27 phai do NEU co du lieu LFW that (neu khong co thi SKIP)."

# ============================================================================
# 12: pham vi tep da sua - phai dung 3 tep trong danh sach trang (+ file .docx cua sinh vien)
# ============================================================================

Doan "12/12" "git status --short --untracked-files=all (pham vi tep)" {
    git status --short --untracked-files=all
}

Write-Output ""
Write-Output "===== XONG - dan toan bo dau ra tren ve cho agent ====="
