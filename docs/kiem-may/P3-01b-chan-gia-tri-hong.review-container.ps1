# docs/kiem-may/P3-01b-chan-gia-tri-hong.review-container.ps1
# Sinh boi: code-reviewer . Ma viec: P3-01b-chan-gia-tri-hong . Vong: 1, luot chay may thu 2
# Chay: powershell -ExecutionPolicy Bypass -File "docs/kiem-may/P3-01b-chan-gia-tri-hong.review-container.ps1"
#
# VI SAO CO TEP RIENG NAY
# Luot chay thu 1 (P3-01b-chan-gia-tri-hong.review.ps1) do bon doan container 12-15 vi Docker daemon
# chua bat. Tep .review.ps1 KHONG duoc sua nua - no phai giu nguyen dung ban da sinh ra khoi ket qua
# nguoi dung dan ve, neu khong thi khong con truy duoc so nao ra tu kich ban nao (docs/kiem-may/README.md).
# Tep nay chi chay lai PHAN CONTAINER.
#
# ⚠️ DA BO CO Y: lenh `pytest -q` TOAN KHO trong container (ban dau la nua sau cua doan C2).
# KHONG PHAI BO SOT - day la danh doi co y thuc, ghi lai de luot review sau khoi tuong la thieu:
#   . Chi phi: gia lap ARM64 chay 47 ca cua test_recognizer.py mat 268 giay. Toan kho 388 ca mat
#     hang chuc phut, nguoi dung ngoi cho truoc man hinh dung yen.
#   . Gia tri thu ve: bang 0. Bien ban P3-01-recognizer.review.md §10.3 DA do bang may lenh do:
#     `8 failed, 335 passed, 34 skipped, 2 errors`, toan bo nam o tests/test_export_detector.py cua
#     ma viec P2-02 vi thieu trong so trong image; da chung minh bang cach xoa han src/recognizer/
#     trong container roi chay lai van ra dung con so ay. Chay lai chi xac nhan mot dieu da biet,
#     va la dieu KHONG thuoc P3-01b.
#   . Thay bang: doan 10 tren host (388 passed) + phep do ban kinh anh huong TINH o C2 duoi day.
#     Khac biet host/container o day la KIEN TRUC, khong phai logic cua ma viec nay.
# Hau qua can ghi vao bien ban: sau khi bo, §8 dac ta P3-01 chi con duoc canh cho RIENG
# tests/test_recognizer.py (qua C4), khong con duoc canh cho toan bo cay test trong container.
#
# 5 doan, KHONG sua bat ky tep nao trong repo, khong dung image moi (R43), khong commit.
# Thoi gian du kien: C3 khoang 4-5 phut, C4 khoang 4-5 phut, cac doan khac gan nhu tuc thi.

$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$env:GIT_PAGER = "cat"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }

$goc = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location $goc

function Doan($so, $ten, $khoi) {
    Write-Output ""
    Write-Output "===== [$so] $ten ====="
    & $khoi
    Write-Output "===== HET [$so] - ma thoat = $LASTEXITCODE ====="
}

Doan "C1/5" "Docker con song khong + image faceid:arm64 (KHONG dung image nao khac, R43)" {
    docker version --format "client {{.Client.Version}} | server {{.Server.Version}}"
    Write-Output "--- image faceid:arm64 ---"
    docker image inspect faceid:arm64 --format "{{.Id}} | tao luc {{.Created}} | kien truc {{.Architecture}}"
    Write-Output "--- danh sach image faceid* (mong doi DUNG MOT dong faceid:arm64) ---"
    docker images --filter "reference=faceid*" --format "{{.Repository}}:{{.Tag}} {{.Size}} {{.CreatedSince}}"
    Write-Output "--- sha256 hien tai cua ba tep tung bi dot bien o luot 1 (phai y nguyen) ---"
    Get-FileHash "src/recognizer/arcface_backend.py", "tests/test_recognizer.py", "configs/recognize.yaml" `
        -Algorithm SHA256 | ForEach-Object { "$($_.Hash)  $($_.Path)" }
    Write-Output "Doi chieu voi luot 1:"
    Write-Output "  8B1F4CF340E4F5A50BAEB3009E78DB34A1CDE1625650E76000B9137F686D8EC0  arcface_backend.py"
    Write-Output "  25E6F21C668384E298A460E839170589B7FB139AE3CD2F9C1A261179CC5B4BA8  test_recognizer.py"
    Write-Output "  028924C5EBFA42F33D8F63254EB38D29724FB158A2770431FCFAD526BB36053B  recognize.yaml"
}

# ----------------------------------------------------------------------------
# C2 - Kien truc container + BAN KINH ANH HUONG do bang cach doc ma, khong chay ma.
# Thay cho lenh `pytest -q` toan kho da bo (xem ghi chu dau tep). Cau hoi can tra loi la
# "P3-01b co the lam do ma viec nao khac khong", va cau tra loi manh nhat lai la cau hoi tinh:
# ngoai tests/test_recognizer.py ra, con tep nao trong repo dung toi arcface_backend khong.
# ----------------------------------------------------------------------------

Doan "C2/5" "Kien truc container that + ban kinh anh huong cua hai tep da sua (do tinh, tuc thi)" {
    docker run --rm -v "${goc}:/app" -w /app faceid:arm64 python3 -c "import platform,sys;print('machine =',platform.machine());print('python  =',sys.version.split()[0])"
    Write-Output ""
    Write-Output "--- moi noi trong repo co nhac toi arcface_backend (mong doi: chi test_recognizer.py) ---"
    Select-String -Path "src/**/*.py", "tests/**/*.py", "scripts/**/*.py" -Pattern 'arcface_backend' -ErrorAction SilentlyContinue |
        ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" }
    Write-Output "--- moi noi co nhac toi src.recognizer (bat ca base.py) ---"
    Select-String -Path "src/**/*.py", "tests/**/*.py", "scripts/**/*.py" -Pattern 'src\.recognizer' -ErrorAction SilentlyContinue |
        ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" }
    Write-Output "Doc ket qua: neu ngoai tests/test_recognizer.py va noi bo src/recognizer/ ra khong con"
    Write-Output "tep nao khac, thi P3-01b khong the lam do ma viec khac - khong can chay toan kho de biet."
}

Doan "C3/5" "Container CO gan thu muc: pytest tests/test_recognizer.py -rs (mong doi 47 passed, 0 skipped) - ~4-5 phut" {
    docker run --rm -v "${goc}:/app" -w /app faceid:arm64 python3 -m pytest tests/test_recognizer.py -q -rs -rf --tb=short 2>&1 | Select-Object -Last 40
}

# ============================================================================
# C4 - DOAN CO GIA TRI NHAT: che khuat models/ va data/ de kiem lai duong SKIP (§8 dac ta P3-01).
# Khong chay container "khong gan thu muc" duoc vi ma nguon nuong trong image la ma CU
# (deploy/Dockerfile.arm64:17 `COPY . .`, ma R43 chi cho dung lai image khi requirements/Dockerfile doi).
# Nen: van gan -v de lay ma HIEN TAI, roi che khuat hai thu muc do bang tmpfs.
# Co duong lui sang volume an danh neu --tmpfs khong dung duoc tren may nay.
# Chay pytest DUNG MOT LAN roi in ba goc nhin tu cung mot dau ra - de khong ton them 4 phut gia lap.
# ============================================================================

Doan "C4/5" "Container CO gan thu muc NHUNG CHE KHUAT models/ va data/ - kiem duong SKIP - ~4-5 phut" {
    Write-Output "MONG DOI 1: 0 failed, 0 error."
    Write-Output "MONG DOI 2: moi ca cham models/ hoac LFW deu SKIP CO THONG BAO neu ro thieu gi."
    Write-Output "MONG DOI 3: dong 39,40,41,42,43,44,45,47 VAN CHAY THAT (khong skip). Rieng dong 47"
    Write-Output "            la ca quan trong nhat cua ma viec - dac ta §6.4 cam no skip."
    Write-Output "MONG DOI 4: dong 46 duoc phep skip (no can do thi ONNX that)."

    Write-Output ""
    Write-Output "--- thu --tmpfs ---"
    docker run --rm -v "${goc}:/app" --tmpfs /app/models --tmpfs /app/data -w /app faceid:arm64 python3 -c "print('tmpfs chay duoc')"
    $dungTmpfs = ($LASTEXITCODE -eq 0)
    if ($dungTmpfs) {
        $che = @("--tmpfs", "/app/models", "--tmpfs", "/app/data")
        Write-Output "-> dung --tmpfs"
    }
    else {
        $che = @("-v", "/app/models", "-v", "/app/data")
        Write-Output "-> --tmpfs KHONG dung duoc, chuyen sang volume an danh (--rm tu don sau khi chay)"
    }

    Write-Output ""
    Write-Output "--- xac nhan models/ va data/ that su RONG, configs/ van con, ma la ma MOI ---"
    docker run --rm -v "${goc}:/app" @che -w /app faceid:arm64 `
        python3 -c "import os;print('models:',os.listdir('/app/models'));print('data  :',os.listdir('/app/data'));print('configs/recognize.yaml co:',os.path.exists('/app/configs/recognize.yaml'));print('ma CO chot isfinite:','math.isfinite' in open('/app/src/recognizer/arcface_backend.py',encoding='utf-8').read())"

    Write-Output ""
    Write-Output "--- pytest -v -rs, chay MOT lan, in ba goc nhin ---"
    $dauRa = docker run --rm -v "${goc}:/app" @che -w /app faceid:arm64 `
        python3 -m pytest tests/test_recognizer.py -v -rs -rf --tb=short 2>&1

    Write-Output "[goc nhin 1] tong ket cuoi"
    $dauRa | Select-Object -Last 30
    Write-Output ""
    Write-Output "[goc nhin 2] trang thai tung ca dong 39-47 (PASSED hay SKIPPED)"
    $dauRa | Select-String -Pattern 'test_dong(39|4[0-7])'
    Write-Output ""
    Write-Output "[goc nhin 3] moi dong SKIPPED va ly do - §8 doi ly do phai neu ro THIEU GI"
    $dauRa | Select-String -Pattern 'SKIPPED|skipped'
}

Doan "C5/5" "Container KHONG gan thu muc - chi do do MOI cua ma nuong trong image (tuc thi)" {
    Write-Output "Neu in 'CO_ISFINITE=False' thi image dang giu ma TRUOC P3-01b. Khi do lenh pytest o day"
    Write-Output "se KHONG duoc chay: no ton 4-5 phut gia lap de kiem mot ban ma khong phai ban dang review."
    $kq = docker run --rm faceid:arm64 python3 -c "import inspect, src.recognizer.arcface_backend as m; print('CO_ISFINITE=' + str('math.isfinite' in inspect.getsource(m)))" 2>&1
    Write-Output $kq
    if ("$kq" -match 'CO_ISFINITE=True') {
        Write-Output "-> ma trong image la ma HIEN TAI, chay pytest de doi chieu voi C4"
        docker run --rm faceid:arm64 python3 -m pytest tests/test_recognizer.py -q -rs --tb=no 2>&1 | Select-Object -Last 25
    }
    else {
        Write-Output "-> ma trong image la ma CU. BO QUA lenh pytest o doan nay (co y, khong phai loi)."
        Write-Output "   C4 la doan canh duong skip; doan C5 chi con vai tro xac nhan image cu."
    }
}

Write-Output ""
Write-Output "===== [CUOI] cay lam viec sau khi chay - kich ban nay khong sua gi trong repo ====="
git status --short --untracked-files=all
Get-FileHash "src/recognizer/arcface_backend.py", "tests/test_recognizer.py", "configs/recognize.yaml" `
    -Algorithm SHA256 | ForEach-Object { "$($_.Hash)  $($_.Path)" }
Write-Output "===== HET [CUOI] ====="

Write-Output ""
Write-Output "===== XONG - dan TOAN BO dau ra tren ve cho agent code-reviewer ====="
