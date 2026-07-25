---
name: latex-visualization
description: Chuẩn tạo biểu đồ, bảng và sơ đồ cho báo cáo khoá luận bằng LaTeX/matplotlib/TikZ. Dùng khi cần vẽ biểu đồ so sánh FPS, đường ROC/DET, ma trận nhầm lẫn, bảng benchmark, sơ đồ kiến trúc 4 khối, sơ đồ đấu nối GPIO, hoặc bất kỳ hình nào đưa vào report/. Mọi hình số liệu phải sinh từ script đọc results/.
---

# Skill: Trực quan hoá cho báo cáo (LaTeX Visualization)

Áp dụng cho mọi hình/bảng trong `report/`. **Chú thích và nhãn bằng tiếng Việt.**

---

## Nguyên tắc bất di bất dịch

1. **Hình số liệu phải sinh từ script**, không vẽ tay, không chỉnh trong Photoshop.
   Script đặt tại `scripts/plot_<tên>.py`, đọc từ `results/`, xuất ra `report/figures/`.
   Dữ liệu cập nhật → chạy lại script → hình tự đúng.
2. **Mỗi hình ghi rõ nguồn** ở caption hoặc chân hình: `Nguồn: results/bench_detect_20260805_0930.csv`.
3. **Xuất vector** (`.pdf` cho LaTeX, `.svg` cho web). Chỉ dùng `.png` 300 DPI khi bắt buộc (ảnh chụp, screenshot).
4. **Không dùng biểu đồ 3D, không hiệu ứng đổ bóng, không nền màu.** Báo cáo học thuật in đen trắng vẫn phải đọc được.
5. **Phân biệt được khi in đen trắng**: dùng kèm marker/nét gạch, không chỉ dựa vào màu.

---

## Thiết lập matplotlib chuẩn dự án

Đặt trong `scripts/plot_style.py`, mọi script vẽ đều `import` file này:

```python
"""Cấu hình kiểu hình thống nhất cho báo cáo khoá luận."""
import matplotlib as mpl
import matplotlib.pyplot as plt

# Bảng màu — an toàn cho người mù màu, phân biệt được khi in xám
MAU = {
    "xanh":   "#2E5EAA",   # Phương án A / dlib
    "cam":    "#D98324",   # Phương án B / ArcFace
    "luc":    "#2E7D5B",   # Đạt chỉ tiêu
    "do":     "#B23A48",   # Không đạt / tấn công
    "xam":    "#6B7280",   # Đường tham chiếu, ngưỡng
}
NET = ["-", "--", "-.", ":"]          # kiểu nét — phân biệt khi in đen trắng
MARKER = ["o", "s", "^", "D", "v"]

def ap_dung_kieu() -> None:
    """Áp dụng kiểu hình chuẩn cho toàn bộ báo cáo."""
    mpl.rcParams.update({
        "figure.figsize": (6.0, 3.6),      # vừa 1 cột A4 lề 2,5cm
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": ":",
        "axes.spines.top": False,          # bỏ khung trên/phải
        "axes.spines.right": False,
        "legend.frameon": False,
    })

def luu(fig, ten: str) -> None:
    """Lưu hình ra report/figures/ ở cả hai định dạng."""
    for duoi in ("pdf", "png"):
        fig.savefig(f"report/figures/{ten}.{duoi}")
    plt.close(fig)
```

> **Dấu thập phân**: matplotlib mặc định dùng dấu chấm. Với hình đưa vào báo cáo tiếng Việt,
> format nhãn bằng `FuncFormatter(lambda x, _: f"{x:.1f}".replace(".", ","))`.

---

## Thư viện hình cần có cho đồ án này

| Hình | Loại biểu đồ | Nguồn dữ liệu | Tên file |
|---|---|---|---|
| So sánh FPS detect theo cấu hình | Cột nhóm (ONNX vs NCNN × 320/640) | `results/bench_detect_*.csv` | `fig_detect_fps` |
| **ROC 2 phương án nhận diện** ⭐ | Đường + điểm EER | `results/bench_recognize_*.csv` | `fig_roc_recognize` |
| **ROC theo 3 tập impostor** ⭐ | 3 đường (lfw / adapted / in-domain) | `results/bench_recognize_*.csv` | `fig_roc_domain` |
| **Kiểm chứng domain adaptation** ⭐ | 3 histogram chồng nhau × nhiều đặc trưng | `results/domain_stats_*.json` | `fig_domain_adaptation` |
| Đánh đổi FAR/FRR theo ngưỡng | 2 đường cắt nhau | `results/bench_recognize_*.csv` | `fig_far_frr` |
| **Bảng so sánh A vs B** ⭐ | Bảng booktabs | `results/bench_recognize_*.csv` | (bảng, không phải hình) |
| Ma trận nhầm lẫn | Heatmap | `results/bench_recognize_*.csv` | `fig_confusion` |
| Latency phân rã theo khâu | Cột chồng (capture/detect/antispoof/recognize) | `results/bench_latency_*.csv` | `fig_latency_breakdown` |
| Anti-spoofing: APCER theo loại tấn công | Cột nhóm | `results/bench_antispoof_*.csv` | `fig_antispoof` |
| FPS theo thời gian + nhiệt độ CPU | 2 trục y | `results/stability_*.csv` | `fig_stability` |
| Phân bố dữ liệu khuôn mặt | Cột (số ảnh/người/điều kiện) | `notebooks/01_eda_faces.ipynb` | `fig_dataset_dist` |
| **Kiến trúc 4 khối** | TikZ | Thủ công | `fig_architecture` |
| Sơ đồ đấu nối GPIO | TikZ / Fritzing | `hardware/` | `fig_wiring` |
| Luồng xử lý pipeline | TikZ flowchart | Thủ công | `fig_pipeline` |

---

## Mẫu 1 — Cột nhóm so sánh FPS

```python
"""Vẽ biểu đồ so sánh FPS phát hiện khuôn mặt theo cấu hình. Nguồn: results/bench_detect_*.csv"""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
from plot_style import ap_dung_kieu, luu, MAU

ap_dung_kieu()
df = pd.read_csv("results/bench_detect_20260805_0930.csv")
tom_tat = df.groupby(["backend", "imgsz"])["fps_instant"].agg(["mean", "std"]).reset_index()

nhan = ["320", "640"]
x = np.arange(len(nhan)); w = 0.35
fig, ax = plt.subplots()
for i, (be, mau) in enumerate([("onnx", MAU["xanh"]), ("ncnn", MAU["cam"])]):
    con = tom_tat[tom_tat.backend == be].sort_values("imgsz")
    ax.bar(x + (i - 0.5) * w, con["mean"], w, yerr=con["std"], capsize=3,
           label=be.upper(), color=mau, edgecolor="black", linewidth=0.5)

ax.axhline(10, color=MAU["xam"], ls="--", lw=1)
ax.text(len(nhan) - 0.5, 10.3, "Chỉ tiêu ≥ 10 FPS", ha="right", fontsize=8, color=MAU["xam"])
ax.set_xticks(x); ax.set_xticklabels([f"{n}×{n}" for n in nhan])
ax.set_xlabel("Kích thước ảnh đầu vào (pixel)")
ax.set_ylabel("Tốc độ xử lý (FPS)")
ax.set_title("So sánh tốc độ phát hiện khuôn mặt trên Raspberry Pi 5")
ax.legend(title="Runtime")
luu(fig, "fig_detect_fps")
```

## Mẫu 2 — Đường cong ROC 2 phương án

```python
"""Vẽ ROC so sánh dlib và ArcFace. Nguồn: results/bench_recognize_*.csv"""
from sklearn.metrics import roc_curve, auc
import pandas as pd, matplotlib.pyplot as plt
from plot_style import ap_dung_kieu, luu, MAU, NET

ap_dung_kieu()
df = pd.read_csv("results/bench_recognize_20260812_1430.csv")

fig, ax = plt.subplots(figsize=(4.6, 4.2))
for i, (be, ten, mau) in enumerate([
    ("dlib", "face_recognition (dlib), 128-D", MAU["xanh"]),
    ("arcface", "MobileFaceNet/ArcFace, 512-D", MAU["cam"]),
]):
    con = df[df.backend == be]
    fpr, tpr, _ = roc_curve(con["is_genuine"], con["similarity"])
    ax.plot(fpr, tpr, NET[i], color=mau, lw=1.6, label=f"{ten} (AUC = {auc(fpr, tpr):.3f})")

ax.plot([0, 1], [0, 1], ":", color=MAU["xam"], lw=1, label="Đoán ngẫu nhiên")
ax.set_xlabel("Tỉ lệ chấp nhận sai FAR")
ax.set_ylabel("Tỉ lệ chấp nhận đúng TAR")
ax.set_title("Đường cong ROC của hai phương án nhận diện")
ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
ax.legend(loc="lower right")
luu(fig, "fig_roc_recognize")
```

## Mẫu 3 — Kiểm chứng domain adaptation (3 phân bố chồng nhau)

```python
"""So sánh phân bố đặc trưng ảnh giữa 3 miền dữ liệu. Nguồn: results/domain_stats_*.json"""
import json, numpy as np, matplotlib.pyplot as plt
from plot_style import ap_dung_kieu, luu, MAU

ap_dung_kieu()
stats = json.load(open("results/domain_stats_20260728_1500.json"))

DAC_TRUNG = [("laplacian_var", "Độ nét (Laplacian variance)"),
             ("brightness",    "Độ sáng trung bình"),
             ("noise_std",     "Mức nhiễu (độ lệch chuẩn)")]
MIEN = [("lfw_original", "LFW gốc",      MAU["xam"]),
        ("lfw_adapted",  "LFW đã adapt", MAU["cam"]),
        ("indomain",     "In-domain (thật)", MAU["luc"])]

fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.6))
for ax, (khoa, nhan) in zip(axes, DAC_TRUNG):
    for mien, ten, mau in MIEN:
        gt = np.array(stats[mien][khoa])
        ax.hist(gt, bins=30, density=True, alpha=0.45, color=mau, label=ten)
    ax.set_xlabel(nhan)
    ax.set_ylabel("Mật độ" if ax is axes[0] else "")

axes[0].legend(loc="upper right", fontsize=7)
fig.suptitle("Kiểm chứng domain adaptation: LFW sau xử lý tiệm cận miền dữ liệu thật", y=1.02)
luu(fig, "fig_domain_adaptation")
```

> Hình này chứng minh bước adaptation có tác dụng: phân bố **cam** (LFW đã adapt) phải dịch từ
> **xám** (LFW gốc) về phía **lục** (dữ liệu thật). Ghi kèm số đo Wasserstein distance vào caption
> để định lượng, đừng để người đọc tự ước lượng bằng mắt.

## Mẫu 4 — Latency phân rã theo khâu (cột chồng)

```python
"""Phân rã độ trễ pipeline theo từng khâu. Nguồn: results/bench_latency_*.csv"""
import pandas as pd, matplotlib.pyplot as plt
from plot_style import ap_dung_kieu, luu, MAU

ap_dung_kieu()
df = pd.read_csv("results/bench_latency_20260901_1000.csv")
khau = ["capture", "detect", "antispoof", "recognize", "actuate"]
ten_vi = ["Thu ảnh", "Phát hiện", "Chống giả mạo", "Nhận diện", "Điều khiển"]
mau = [MAU["xam"], MAU["xanh"], MAU["cam"], MAU["luc"], MAU["do"]]

fig, ax = plt.subplots(figsize=(6.0, 2.6))
day = 0
for k, t, m in zip(khau, ten_vi, mau):
    gt = df[f"{k}_ms"].mean()
    ax.barh(0, gt, left=day, color=m, edgecolor="black", linewidth=0.5, label=f"{t} ({gt:.1f} ms)")
    day += gt

ax.axvline(2000, color=MAU["do"], ls="--", lw=1)
ax.text(2000, 0.45, "Chỉ tiêu < 2000 ms", fontsize=8, color=MAU["do"], ha="right")
ax.set_yticks([]); ax.set_xlabel("Độ trễ tích luỹ (ms)")
ax.set_title("Phân rã độ trễ toàn pipeline theo từng khâu xử lý")
ax.legend(ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.35))
luu(fig, "fig_latency_breakdown")
```

---

## Bảng LaTeX — chuẩn `booktabs`

Preamble cần: `\usepackage{booktabs, siunitx, multirow, caption}`

```latex
\begin{table}[htbp]
\centering
\caption{So sánh hiệu năng hai phương án nhận diện danh tính trên Raspberry Pi 5}
\label{tab:so-sanh-nhan-dien}
\begin{tabular}{l S[table-format=2.1] S[table-format=1.2] S[table-format=1.2] S[table-format=2.1] S[table-format=3.1]}
\toprule
\multirow{2}{*}{\textbf{Phương án}} & {\textbf{Độ chính xác}} & {\textbf{FAR}} & {\textbf{FRR}}
  & {\textbf{Tốc độ}} & {\textbf{Độ trễ}} \\
 & {(\%)} & {(\%)} & {(\%)} & {(FPS)} & {(ms)} \\
\midrule
face\_recognition (dlib), 128-D   & 94.1 & 2.30 & 3.60 &  6.2 & 42.7 \\
MobileFaceNet/ArcFace, 512-D      & 96.8 & 0.90 & 1.50 & 11.4 & 18.4 \\
\midrule
\textit{Chỉ tiêu đề cương}        & 95.0 & {--} & {--} & 5.0  & {--} \\
\bottomrule
\end{tabular}

\vspace{2pt}
\footnotesize\textit{Nguồn}: \texttt{results/bench\_recognize\_20260812\_1430.csv}.
\textit{Điều kiện}: Pi 5 8\,GB có tản nhiệt, ảnh 112$\times$112, 100 lần lặp,
ánh sáng trong nhà $\approx$300\,lux.
\end{table}
```

> ❌ **Không dùng** `\hline` liên tiếp và đường kẻ dọc `|`. Chỉ dùng `\toprule`, `\midrule`, `\bottomrule`.
> `siunitx` (cột `S`) căn số theo dấu thập phân — bảng đẹp và dễ so sánh hơn hẳn.
> Số trong LaTeX viết dấu chấm; cấu hình `\sisetup{output-decimal-marker={,}}` để in ra dấu phẩy.

---

## Sơ đồ TikZ — kiến trúc 4 khối

```latex
\begin{figure}[htbp]
\centering
\begin{tikzpicture}[
  node distance=0.9cm and 1.4cm,
  khoi/.style={rectangle, draw, rounded corners=2pt, minimum width=3.4cm,
               minimum height=1.0cm, align=center, font=\small},
  mui/.style={-{Latex[length=2mm]}, thick},
]
\node[khoi, fill=blue!8]  (thu)   {\textbf{KHỐI 1} — Thu nhận \& Xử lý ảnh\\
                                   \scriptsize Camera $\to$ YOLOv8n-face $\to$ MiniFASNet $\to$ Embedding};
\node[khoi, fill=orange!8, below=of thu] (qd) {\textbf{KHỐI 2} — Quyết định \& Phân quyền\\
                                   \scriptsize Danh tính $\to$ quyền điều khiển};
\node[khoi, fill=green!8, below left=1.2cm and 0.2cm of qd]  (ch)
      {\textbf{KHỐI 3} — Chấp hành\\ \scriptsize GPIO/relay · IR · MQTT};
\node[khoi, fill=red!8,  below right=1.2cm and 0.2cm of qd] (gs)
      {\textbf{KHỐI 4} — Giám sát \& Cảnh báo\\ \scriptsize Flask · Telegram · CSDL log};

\draw[mui] (thu) -- (qd);
\draw[mui] (qd) -- (ch);
\draw[mui] (qd) -- (gs);
\end{tikzpicture}
\caption{Kiến trúc tổng thể hệ thống gồm bốn khối chức năng}
\label{fig:kien-truc}
\end{figure}
```

Preamble cần: `\usepackage{tikz}` + `\usetikzlibrary{arrows.meta, positioning, shapes.geometric}`

---

## Checklist trước khi chèn hình vào báo cáo

- [ ] Hình sinh từ script trong `scripts/`, chạy lại được
- [ ] Nhãn trục có **tên đại lượng + đơn vị**, bằng tiếng Việt
- [ ] Có ghi chú nguồn `results/...`
- [ ] Có đường ngưỡng chỉ tiêu (nếu hình liên quan chỉ tiêu cam kết)
- [ ] Cỡ chữ trong hình ≥ 8 pt sau khi thu nhỏ về khổ trang
- [ ] Đọc được khi in đen trắng (thử `plt.style.use('grayscale')`)
- [ ] Xuất định dạng vector `.pdf`
- [ ] Đã được dẫn trong thân bài trước khi xuất hiện
- [ ] Cột số dùng `siunitx`, dấu thập phân là dấu phẩy khi in ra
