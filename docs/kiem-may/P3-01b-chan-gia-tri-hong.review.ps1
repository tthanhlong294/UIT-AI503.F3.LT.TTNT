# docs/kiem-may/P3-01b-chan-gia-tri-hong.review.ps1
# Sinh boi: code-reviewer . Ma viec: P3-01b-chan-gia-tri-hong . Vong: 1
# Chay: powershell -ExecutionPolicy Bypass -File "docs/kiem-may/P3-01b-chan-gia-tri-hong.review.ps1"
#
# KIEM DINH DOC LAP - dung lai tu dau moi phep kiem, KHONG tin ket qua cua kich ban .coder.
# 26 doan. Khong commit, khong push, khong dung image Docker moi (R43), khong ghi vao data/ hay results/.
# Moi phep dot bien deu: sao luu ra %TEMP% -> sua -> chay -> khoi phuc -> doi chieu sha256.
#
# Luu y khi doc ket qua: "ma thoat" chi co y nghia voi lenh ngoai (python, docker, git).
# Voi Select-String / logic PowerShell thi doc phan ket luan in ra trong doan.

$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }

# Tat trinh phan trang cua git. Khong co dong nay thi `git diff` va `git log` day dau ra qua `less`,
# man hinh dung o dau ":" cho bam phim - kich ban treo giua chung, trai quy uoc "chay bang mot lenh".
$env:GIT_PAGER = "cat"

$goc = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $goc

$TEP_MA   = "src/recognizer/arcface_backend.py"
$TEP_TEST = "tests/test_recognizer.py"
$TEP_CFG  = "configs/recognize.yaml"

function Doan($so, $ten, $khoi) {
    Write-Output ""
    Write-Output "===== [$so] $ten ====="
    & $khoi
    Write-Output "===== HET [$so] - ma thoat = $LASTEXITCODE ====="
}

# Dot bien bang regex: in ra SO LAN MAU KHOP truoc khi sua.
# Neu so lan khop khac mong doi thi phep dot bien vo nghia - phai bao lai, khong duoc ket luan.
function DotBien($so, $ten, $tep, $mau, $thay, $soLanMongDoi, $caDoMongDoi) {
    $luu = Join-Path $env:TEMP ("kiem_" + [IO.Path]::GetRandomFileName())
    Copy-Item $tep $luu
    $truoc = (Get-FileHash $tep -Algorithm SHA256).Hash
    Write-Output ""
    Write-Output "===== [$so] DOT BIEN: $ten ====="
    Write-Output "Tep              : $tep"
    Write-Output "Ca PHAI do       : $caDoMongDoi"
    Write-Output "sha256 truoc     : $truoc"
    try {
        $noiDung = [IO.File]::ReadAllText($tep)
        $soKhop = ([regex]::Matches($noiDung, $mau)).Count
        Write-Output "So lan mau khop  : $soKhop (mong doi $soLanMongDoi)"
        if ($soKhop -ne $soLanMongDoi) {
            Write-Output "*** MAU KHONG KHOP DUNG SO LAN -> PHEP DOT BIEN NAY VO NGHIA, BAO LAI CHO AGENT ***"
        }
        $moi = [regex]::Replace($noiDung, $mau, $thay)
        [IO.File]::WriteAllText($tep, $moi, (New-Object System.Text.UTF8Encoding($false)))
        python -m pytest tests/test_recognizer.py -q -rf --tb=no 2>&1 | Select-Object -Last 30
    } finally {
        Copy-Item $luu $tep -Force
        Remove-Item $luu -Force
        $sau = (Get-FileHash $tep -Algorithm SHA256).Hash
        Write-Output "sha256 sau       : $sau"
        if ($truoc -eq $sau) { Write-Output "KHOI PHUC: KHOP" }
        else { Write-Output "KHOI PHUC: *** KHONG KHOP - DUNG LAI, KIEM TAY ***" }
    }
    Write-Output "===== HET [$so] ====="
}

# ============================================================================
# A. BOI CANH VA PHAM VI TEP
# ============================================================================

Doan "1/26" "Boi canh: nhanh, commit, python, image faceid:arm64" {
    git rev-parse --abbrev-ref HEAD
    git log -1 --oneline
    python --version
    Write-Output "--- image faceid:arm64 (Id / ngay dung) ---"
    docker image inspect faceid:arm64 --format "{{.Id}} | tao luc {{.Created}}"
}

Doan "2/26" "Pham vi tep tho: git status + git diff --stat" {
    git status --short --untracked-files=all
    Write-Output "--- git diff --stat ---"
    git diff --stat
}

Doan "3/26" "Doi chieu DANH SACH TRANG §3 dac ta (dung 3 tep) - KET LUAN tu dong" {
    $trang = @(
        "src/recognizer/arcface_backend.py",
        "tests/test_recognizer.py",
        "docs/kiem-may/P3-01b-chan-gia-tri-hong.coder.ps1",
        "docs/kiem-may/P3-01b-chan-gia-tri-hong.review.ps1"
    )
    $viPham = 0
    foreach ($d in (git status --short --untracked-files=all)) {
        if (-not $d) { continue }
        $p = $d.Substring(3).Trim().Trim('"') -replace '\\', '/'
        if ($trang -contains $p) {
            Write-Output "OK   (danh sach trang)                  : $p"
        }
        elseif ($p -like 'docs/bao-cao-tuan*') {
            Write-Output "OK   (.docx bao cao tuan cua SV, co san) : $p"
        }
        else {
            Write-Output "*** NGOAI DANH SACH TRANG ***           : $p"
            $viPham++
        }
    }
    Write-Output "KET LUAN doan 3: so tep ngoai danh sach trang = $viPham (phai bang 0)"
}

Doan "4/26" "Du lieu cam lot git (jpg/png/npy/npz/onnx/pt/pth/env/db/sqlite) - mong doi RONG" {
    $kq = git status --short --untracked-files=all |
        Select-String -Pattern '\.(jpg|jpeg|png|npy|npz|onnx|pt|pth|env|db|sqlite3?)$'
    if ($kq) { $kq; Write-Output "*** CO TEP CAM ***" }
    else { Write-Output "RONG - khong co tep cam" }
}

Doan "5/26" "Vung CAM CHAM (§3 dac ta): configs/, src/recognizer/base.py, results/, report/, CLAUDE.md, docs/ ngoai kiem-may" {
    $cam = git status --short --untracked-files=all | Select-String -Pattern `
        '(configs/|src/recognizer/base\.py|results/|report/|CLAUDE\.md|models/)'
    if ($cam) { $cam; Write-Output "*** DA CHAM VUNG CAM ***" }
    else { Write-Output "RONG - khong cham vung cam" }
    Write-Output "--- moi thay doi trong docs/ (chi duoc phep docs/kiem-may/*.ps1) ---"
    $tailieu = git status --short --untracked-files=all | Select-String -Pattern 'docs/'
    if ($tailieu) { $tailieu } else { Write-Output "(khong co)" }
}

Doan "6/26" "Toan bo diff cua src/recognizer/arcface_backend.py (doc bang mat)" {
    git diff -- $TEP_MA
}

Doan "7/26" "38 ca cu co bi sua khong: cac dong BI XOA trong tests/test_recognizer.py + dem so ca" {
    Write-Output "--- cac dong bi xoa (chi duoc phep nam trong docstring dau module) ---"
    $xoa = git diff -U0 -- $TEP_TEST | Select-String -Pattern '^-[^-]'
    if ($xoa) { $xoa } else { Write-Output "(khong xoa dong nao)" }
    Write-Output "--- so ham test trong tep (mong doi 47) ---"
    $ham = Select-String -Path $TEP_TEST -Pattern '^def test_dong(\d+)'
    Write-Output ("So ham test_dong* : " + $ham.Count)
    Write-Output "--- danh sach ten ham ---"
    $ham | ForEach-Object { $_.Line }
}

# ============================================================================
# B. BA LENH NEN TREN HOST
# ============================================================================

Doan "8/26" "black --check --line-length 100 src tests (mong doi ma thoat 0)" {
    python -m black --check --line-length 100 src tests
}

Doan "9/26" "ruff check src tests (mong doi All checks passed!)" {
    python -m ruff check src tests
}

Doan "10/26" "pytest -q toan kho tren host (dac ta §7.1 mong doi 388 passed)" {
    python -m pytest -q -rf --tb=line 2>&1 | Select-Object -Last 40
}

Doan "11/26" "pytest tests/test_recognizer.py -rs tren host (mong doi 47 passed, 0 skipped)" {
    python -m pytest tests/test_recognizer.py -q -rs -rf --tb=short 2>&1 | Select-Object -Last 40
}

# ============================================================================
# C. CONTAINER faceid:arm64 - dung dung image nay, KHONG dung image moi (R43)
# ============================================================================

Doan "12/26" "Container CO gan thu muc: kien truc + pytest toan kho" {
    docker run --rm -v "${goc}:/app" -w /app faceid:arm64 python3 -c "import platform,sys;print('machine =',platform.machine());print('python  =',sys.version.split()[0])"
    docker run --rm -v "${goc}:/app" -w /app faceid:arm64 python3 -m pytest -q -rf --tb=no 2>&1 | Select-Object -Last 25
}

Doan "13/26" "Container CO gan thu muc: pytest tests/test_recognizer.py -rs (mong doi 47 passed, 0 skipped)" {
    docker run --rm -v "${goc}:/app" -w /app faceid:arm64 python3 -m pytest tests/test_recognizer.py -q -rs -rf --tb=short 2>&1 | Select-Object -Last 40
}

Doan "14/26" "Container CO gan thu muc NHUNG CHE KHUAT models/ va data/ - kiem duong SKIP (§8 dac ta P3-01)" {
    Write-Output "MONG DOI: 0 failed, 0 error. Cac ca can models/ hoac LFW phai SKIP CO THONG BAO."
    Write-Output "MONG DOI: dong 39,40,41,42,43,44,45,47 van CHAY THAT (khong skip); chi dong 46 duoc skip."
    Write-Output "--- xac nhan models/ va data/ that su rong trong container ---"
    docker run --rm -v "${goc}:/app" --tmpfs /app/models --tmpfs /app/data -w /app faceid:arm64 `
        python3 -c "import os;print('models:',os.listdir('/app/models'));print('data:',os.listdir('/app/data'));print('configs co:',os.path.exists('/app/configs/recognize.yaml'))"
    Write-Output "--- pytest voi -rs (in ly do skip) ---"
    docker run --rm -v "${goc}:/app" --tmpfs /app/models --tmpfs /app/data -w /app faceid:arm64 `
        python3 -m pytest tests/test_recognizer.py -q -rs -rf --tb=short 2>&1 | Select-Object -Last 45
}

Doan "15/26" "Container KHONG gan thu muc (ma nguon nuong trong image) + do do MOI cua ma trong image" {
    Write-Output "Doan nay chi de doi chieu. Neu ma trong image CU (chua co P3-01b) thi ket qua pytest ben duoi"
    Write-Output "KHONG noi len dieu gi ve ma viec nay - doan 14 moi la doan co gia tri."
    docker run --rm faceid:arm64 python3 -c "import inspect, src.recognizer.arcface_backend as m; s=inspect.getsource(m); print('ma trong image CO chot isfinite:', 'math.isfinite' in s)"
    docker run --rm faceid:arm64 python3 -m pytest tests/test_recognizer.py -q -rs --tb=no 2>&1 | Select-Object -Last 25
}

# ============================================================================
# D. QUET MAU VI PHAM (code-review.instructions.md §2)
# ============================================================================

Doan "16/26" "Quet mau vi pham chuan - moi muc mong doi RONG" {
    function Quet($nhan, $mau, $duong) {
        Write-Output "--- $nhan ---"
        $r = Select-String -Path $duong -Pattern $mau -ErrorAction SilentlyContinue
        if ($r) { $r | ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" } }
        else { Write-Output "(rong)" }
    }
    Quet "print() trong src/"            '\bprint\('                       "src/**/*.py"
    Quet "except tran / nuot loi"        'except\s*:|except Exception:\s*pass' "src/**/*.py"
    Quet "import phan cung dau tep"      '^import RPi|^import pigpio|^from RPi' "src/**/*.py"
    Quet "import torch"                  'import torch'                     "src/**/*.py"
    Quet "log dung f-string"             'logger\.\w+\(f"'                  "src/**/*.py"
    Quet "duong dan tuyet doi may ca nhan" '[A-Z]:\\\\|/home/|/Users/'      "src/**/*.py"
    Quet "secret trong code"             'token\s*=\s*["'']|api_key\s*=\s*["'']|password\s*=\s*["'']' "src/**/*.py"
    Quet "nap model trong vong lap (kiem tay ngu canh)" 'InferenceSession'  "src/**/*.py"
    Quet "test gia: assert True"         'assert True'                      "tests/**/*.py"
    Quet "so magic float trong 2 tep sua doi (ra tay)" '[<>]=?\s*0\.\d'     @($TEP_MA, $TEP_TEST)
}

Doan "17/26" "Quet chuyen biet cho P3-01b" {
    Write-Output "--- 7.1/6: moi chot '== 0.0' trong src/recognizer/ (moi cho o arcface_backend PHAI co isfinite ke ben) ---"
    Select-String -Path "src/recognizer/*.py" -Pattern '== 0\.0' |
        ForEach-Object { "$($_.Filename):$($_.LineNumber): $($_.Line.Trim())" }
    Write-Output "--- 7.1/7: so viet cung 127.5|128|512|112 trong arcface_backend.py (mong doi RONG) ---"
    $s = Select-String -Path $TEP_MA -Pattern '\b(127\.5|128|512|112)\b'
    if ($s) { $s | ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } } else { Write-Output "(rong)" }
    Write-Output "--- vi tri cac chot math.isfinite trong arcface_backend.py ---"
    Select-String -Path $TEP_MA -Pattern 'math\.isfinite' |
        ForEach-Object { "dong $($_.LineNumber): $($_.Line.Trim())" }
    Write-Output "--- 'import math' co dung nhom thu vien chuan khong ---"
    Select-String -Path $TEP_MA -Pattern '^import |^from ' | Select-Object -First 6 |
        ForEach-Object { "dong $($_.LineNumber): $($_.Line.Trim())" }
}

# ============================================================================
# E. DOT BIEN - dung lai tu dau ca ba phep §7.2 cua dac ta, cong bon phep rieng cua nguoi review
# ============================================================================

DotBien "18/26" "DB8 (§7.2 dac ta) - vo hieu hoa chot math.isfinite trong _doc_so_thuc" `
    $TEP_MA `
    '(?m)^    if not math\.isfinite\(gia_tri_float\):' `
    '    if False:  # DOT BIEN DB8' `
    1 `
    "CHI test_dong39, 40, 41, 42 do. test_dong43 KHONG DUOC do (neu do 43 -> va qua tay)."

DotBien "19/26" "DB11 (nguoi review tu dung) - VA QUA TAY: chot them 'gia_tri <= 0' cho ca mean" `
    $TEP_MA `
    'if not math\.isfinite\(gia_tri_float\):' `
    'if not math.isfinite(gia_tri_float) or gia_tri_float <= 0:  # DOT BIEN DB11' `
    1 `
    "CHI test_dong43 do. Neu 43 KHONG do thi dong 43 la ca chet, khong canh duoc viec va qua tay."

DotBien "20/26" "DB9a - vo hieu hoa CHI chot NaN trong trich_dac_trung (dong 282)" `
    $TEP_MA `
    '(?m)^        if not math\.isfinite\(do_dai\) or do_dai == 0\.0:' `
    '        if do_dai == 0.0:  # DOT BIEN DB9a' `
    1 `
    "test_dong44 do. test_dong45 du bao van xanh (enroll con chot rieng)."

DotBien "21/26" "DB9b - vo hieu hoa CHI chot NaN trong vong lap cua enroll (dong 318)" `
    $TEP_MA `
    '(?m)^            if not math\.isfinite\(do_dai\) or do_dai == 0\.0:' `
    '            if do_dai == 0.0:  # DOT BIEN DB9b' `
    1 `
    "Du bao: KHONG ca nao do (chot vecto trung binh van bat duoc). Doan nay do do THUA cua ba chot."

DotBien "22/26" "DB9c - vo hieu hoa CHI chot NaN cua vecto trung binh trong enroll (dong 324)" `
    $TEP_MA `
    'if not math\.isfinite\(do_dai_trung_binh\) or do_dai_trung_binh == 0\.0:' `
    'if do_dai_trung_binh == 0.0:  # DOT BIEN DB9c' `
    1 `
    "Du bao: KHONG ca nao do (chot trong vong lap van bat duoc)."

DotBien "23/26" "DB9 day du (§7.2 dac ta) - vo hieu hoa CA BA chot NaN do dai" `
    $TEP_MA `
    'not math\.isfinite\(do_dai(_trung_binh)?\) or ' `
    '' `
    3 `
    "test_dong44 va test_dong45 do."

DotBien "24/26" "DB10 (§7.2 dac ta) - vo hieu hoa chot doi chieu input_size voi do thi ONNX" `
    $TEP_MA `
    'if la_kich_thuoc_tinh and kich_thuoc_dau_vao_onnx != kich_thuoc_vao:' `
    'if False:  # DOT BIEN DB10' `
    1 `
    "CHI test_dong46 do."

DotBien "25/26" "DB2 chay lai tu P3-01 - bo (x-mean)/scale, dua tho 0-255 vao mo hinh" `
    $TEP_MA `
    'tensor = \(anh_dung_kenh\.astype\(np\.float32\) - do_lech\) / ty_le' `
    'tensor = anh_dung_kenh.astype(np.float32)  # DOT BIEN DB2' `
    1 `
    "TOI THIEU test_dong12 va test_dong27 do (27 skip neu may khong co du lieu LFW). La chan cu con nguyen?"

DotBien "26/26" "DB12 (nguoi review tu dung) - doi scale trong configs/recognize.yaml THAT tu 128.0 sang 64.0" `
    $TEP_CFG `
    '(?m)^  scale: 128\.0' `
    '  scale: 64.0  # DOT BIEN DB12' `
    1 `
    "CHI test_dong47 do. Neu 47 KHONG do thi no khong thuc su doc tep cau hinh that."

# ============================================================================
# F. BO CAU HINH THU DICH TU DUNG - do lo hong NGOAI danh sach dac ta liet ke
#    (chi DOC; script python nam ngoai repo, xoa sau khi chay)
# ============================================================================

$tepDo = Join-Path $env:TEMP ("do_cauhinh_" + [IO.Path]::GetRandomFileName() + ".py")
$maDo = @'
"""Do lo hong cau hinh khoi nhan dien - do code-reviewer viet, CHI DOC, khong ghi gi."""

import os
import sys

sys.path.insert(0, os.getcwd())
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from pathlib import Path

import numpy as np

from src.common.exceptions import LoiCauHinh, LoiMoHinh
from src.recognizer.arcface_backend import ArcFaceBackend

MODEL = Path("models/mobilefacenet.onnx")


def cfg_goc():
    return {
        "model_path": str(MODEL),
        "embedding_dim": 512,
        "input_size": [112, 112],
        "channel_order": "rgb",
        "mean": 127.5,
        "scale": 128.0,
    }


BIEN_THE = [
    ("scale", float("inf"), "inf"),
    ("scale", float("nan"), "nan"),
    ("scale", 0, "0"),
    ("scale", -1, "-1"),
    ("scale", 1e308, "1e308"),
    ("scale", 1e-320, "1e-320 (dac ta KHONG yeu cau chan)"),
    ("scale", 5e-324, "5e-324 nho nhat"),
    ("scale", 10**400, "int qua lon, khong lot float"),
    ("mean", float("inf"), "inf"),
    ("mean", float("-inf"), "-inf"),
    ("mean", float("nan"), "nan"),
    ("mean", 1e308, "1e308"),
    ("mean", -1e308, "-1e308"),
    ("mean", 10**400, "int qua lon, khong lot float"),
    ("mean", 0, "0 (PHAI duoc chap nhan)"),
    ("mean", -127.5, "-127.5 (PHAI duoc chap nhan)"),
    ("embedding_dim", 10**400, "int qua lon"),
    ("input_size", [64, 64], "64x64 lech do thi"),
    ("input_size", [112, 113], "lech mot chieu"),
    ("input_size", [10**400, 10**400], "int qua lon"),
    ("input_size", (112, 112), "tuple (PHAI duoc chap nhan)"),
    ("channel_order", "RGB", "hoa (PHAI duoc chap nhan)"),
]

print("=== Phan 1: ArcFaceBackend(cfg) voi tung bien the ===")
print("(RO = ngoai le KHONG phai LoiCauHinh/LoiMoHinh ro ra ngoai -> lo hong)")
for khoa, gia_tri, nhan in BIEN_THE:
    cfg = cfg_goc()
    cfg[khoa] = gia_tri
    try:
        ArcFaceBackend(cfg)
        ket = "CHAP NHAN (khong nem loi)"
    except LoiCauHinh as e:
        ket = "LoiCauHinh : " + str(e)[:64]
    except LoiMoHinh as e:
        ket = "LoiMoHinh  : " + str(e)[:64]
    except Exception as e:  # noqa: BLE001
        ket = "*** RO " + type(e).__name__ + " : " + str(e)[:56]
    print("  %-14s %-34s -> %s" % (khoa, nhan, ket))

print()
print("=== Phan 2: hanh vi dau cuoi voi cau hinh bien (can models/mobilefacenet.onnx) ===")
if not MODEL.exists():
    print("  BO QUA: khong co", MODEL)
    sys.exit(0)

rng = np.random.default_rng(42)  # R15: seed 42
ba_anh = [rng.integers(0, 256, (112, 112, 3), dtype=np.uint8) for _ in range(3)]

from src.recognizer.base import do_tuong_dong  # noqa: E402

TRUONG_HOP = [
    ("doi chung: scale=128, mean=127.5", {}),
    ("scale = 1e-320", {"scale": 1e-320}),
    ("mean  = 1e308", {"mean": 1e308}),
    ("mean  = -1e308", {"mean": -1e308}),
]
for nhan, sua in TRUONG_HOP:
    cfg = cfg_goc()
    cfg.update(sua)
    try:
        be = ArcFaceBackend(cfg)
        vecs = [be.trich_dac_trung(a) for a in ba_anh]
        huu_han = all(bool(np.isfinite(v).all()) for v in vecs)
        sims = [
            round(do_tuong_dong(vecs[i], vecs[j]), 4)
            for i in range(3)
            for j in range(i + 1, 3)
        ]
        print("  %-34s -> vec huu han=%s ; tuong dong giua 3 ANH KHAC NHAU=%s" % (nhan, huu_han, sims))
    except Exception as e:  # noqa: BLE001
        print("  %-34s -> nem %s: %s" % (nhan, type(e).__name__, str(e)[:60]))

print()
print("=== Phan 3: gallery chua vecto NaN di vao identify (hop dong §5 P3-01) ===")
cfg = cfg_goc()
try:
    be = ArcFaceBackend(cfg)
    gallery = {"nguoi_a": np.full(512, np.nan, dtype=np.float32)}
    print("  identify voi gallery NaN ->", be.identify(ba_anh[0], gallery, 0.5))
except Exception as e:  # noqa: BLE001
    print("  nem", type(e).__name__, ":", str(e)[:70])
'@

Write-Output ""
Write-Output "===== [BO SUNG] BO CAU HINH THU DICH TU DUNG (22 bien the + 4 kich ban dau cuoi) ====="
Write-Output "Tep tam (ngoai repo): $tepDo"
try {
    [IO.File]::WriteAllText($tepDo, $maDo, (New-Object System.Text.UTF8Encoding($false)))
    python $tepDo 2>&1
    Write-Output "ma thoat = $LASTEXITCODE"
} finally {
    Remove-Item $tepDo -Force -ErrorAction SilentlyContinue
}
Write-Output "===== HET [BO SUNG] ====="

# ============================================================================
# G. TRANG THAI CUOI - kich ban co lam ban cay lam viec khong
# ============================================================================

Write-Output ""
Write-Output "===== [CUOI] git status --short --untracked-files=all (phai giong het doan 2) ====="
git status --short --untracked-files=all
Write-Output "--- sha256 hien tai cua ba tep bi dot bien ---"
Get-FileHash $TEP_MA, $TEP_TEST, $TEP_CFG -Algorithm SHA256 |
    ForEach-Object { "$($_.Hash)  $($_.Path)" }
Write-Output "===== HET [CUOI] ====="

Write-Output ""
Write-Output "===== XONG - dan TOAN BO dau ra tren ve cho agent code-reviewer ====="
