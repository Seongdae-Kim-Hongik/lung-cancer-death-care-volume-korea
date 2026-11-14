# figs_lcad.py: part of the manuscript build for the analysis of lung cancer deaths relative to treated persons (see README).
import os, numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from PIL import Image
Image.MAX_IMAGE_PIXELS = None
from numbers_lcad import load, SHP, EDU, OUTC
HERE = os.path.dirname(os.path.abspath(__file__)); B = os.path.dirname(os.path.dirname(HERE)); RS = os.path.join(B, "results_std3")
FIG = os.path.join(HERE, "figs"); OUTF = os.path.join(os.path.dirname(HERE), "out", "Figures"); os.makedirs(FIG, exist_ok=True); os.makedirs(OUTF, exist_ok=True)
MM = 1 / 25.4; W = 174 * MM; DPI = 600; LW = 0.3
plt.rcParams.update({"font.family": "Arial", "font.size": 8, "legend.fontsize": 8, "legend.title_fontsize": 8, "axes.linewidth": 0.5, "pdf.fonttype": 42})
N = load()
G = gpd.read_file(SHP); G["cd"] = G.sigungu_cd.astype(str); G["sido"] = G.cd.str[:2]; SIDO = G.dissolve("sido")   # 결합은 시군구 코드(cd)로만
XL = (G.total_bounds[0], G.total_bounds[2]); YL = (G.total_bounds[1], G.total_bounds[3])
rd = lambda f: pd.read_csv(os.path.join(RS, f), encoding="utf-8-sig", dtype={"sigungu_cd": str})
PANEL_LABEL_PT = 52   # 모든 패널 같은 크기·대문자
def letter(fig, x, y, ch):
    fig.text(x, y, ch, fontsize=PANEL_LABEL_PT, fontweight="bold", va="top", ha="left")
def mapax(ax):   # 북침 = 슬림 채움 삼각형 + "N"(3배), 축척 0-50-100 km 흑백 2단
    from matplotlib.patches import Polygon, Rectangle
    SIDO.boundary.plot(ax=ax, color="#404040", linewidth=0.45); ax.set_xlim(*XL); ax.set_ylim(*YL); ax.set_axis_off(); ax.set_aspect("equal")
    x0, x1 = XL; y0, y1 = YL; W_ = x1 - x0; H_ = y1 - y0
    bx, by, bh = x0 + 0.60 * W_, y0 + 0.04 * H_, 0.010 * H_
    ax.add_patch(Rectangle((bx, by), 50000, bh, facecolor="black", edgecolor="black", lw=0.5)); ax.add_patch(Rectangle((bx + 50000, by), 50000, bh, facecolor="white", edgecolor="black", lw=0.5))
    for k, t, ha in ((0, "0", "center"), (50000, "50", "center"), (100000, " 100 km", "left")): ax.text(bx + k, by + bh + 0.008 * H_, t, ha=ha, va="bottom", fontsize=8)
    nx, ny, nw, nh = x0 + 0.95 * W_, y0 + 0.62 * H_, 0.054 * W_, 0.21 * H_
    ax.add_patch(Polygon([[nx - nw / 2, ny], [nx, ny + nh], [nx + nw / 2, ny], [nx, ny + 0.25 * nh]], closed=True, facecolor="black", edgecolor="black", lw=0.4))
    ax.text(nx, ny + nh + 0.012 * H_, "N", ha="center", va="bottom", fontsize=24, fontweight="bold")
def save(fig, k, dpi=DPI):
    p = os.path.join(FIG, f"JTO_Fig{k}.png"); fig.savefig(p, dpi=dpi, facecolor="white"); plt.close(fig)
    im = Image.open(p).convert("RGB"); im.save(p, dpi=(dpi, dpi))
    if not str(k).startswith("S"): im.save(os.path.join(OUTF, f"Figure{k}.tif"), dpi=(dpi, dpi), compression="tiff_lzw")
    return im.size

# Figure 1
S6 = rd("S6_spatial_RR.csv"); assert len(S6) == 229
Q = N["Q"]; s6r = S6.set_index("sigungu_cd")
BR = [0, 0.8, 0.9, 0.95, 1, 1.05, 1.1, 1.2, 99]; LB = ["<0.80", "0.80-0.89", "0.90-0.94", "0.95-0.99", "1.00-1.04", "1.05-1.09", "1.10-1.19", "≥1.20"]
PAL = ["#2166AC", "#4393C3", "#92C5DE", "#D1E5F0", "#FDDBC7", "#F4A582", "#D6604D", "#B2182B"]
fig = plt.figure(figsize=(W, 8.6))
AX = [fig.add_axes([0.00, 0.555, 0.48, 0.37]), fig.add_axes([0.50, 0.555, 0.48, 0.37]), fig.add_axes([0.00, 0.075, 0.48, 0.37]), fig.add_axes([0.60, 0.13, 0.28, 0.27])]
gg = G.copy(); gg["r"] = gg.cd.map(s6r.fbd_region); assert gg.r.notna().all()
gg["smr"] = gg.r.map(Q.smr); gg["care"] = gg.r.map(Q.sir_care); gg["v"] = gg.cd.map(s6r.RR); gg["c"] = gg.cd.map(s6r["class"]); assert gg[["smr", "care", "v"]].notna().all().all()
for ax, col in ((AX[0], "smr"), (AX[1], "care"), (AX[2], "v")):
    gg.plot(ax=ax, column=col, cmap=ListedColormap(PAL), norm=BoundaryNorm(BR, len(PAL)), edgecolor="#a0a0a0", linewidth=LW); mapax(ax)
gg[gg.c == "coldspot"].boundary.plot(ax=AX[2], color="#2171B5", linewidth=0.6, linestyle=(0, (2.0, 1.2))); gg[gg.c == "hotspot"].boundary.plot(ax=AX[2], color="black", linewidth=0.6)
h = [Patch(facecolor=c, edgecolor="#777777", linewidth=LW, label=l) for c, l in zip(PAL, LB)]
fig.legend(handles=h, title="Ratio (A, B) or residual rate ratio (C)", loc="center", bbox_to_anchor=(0.5, 0.515), ncol=8, frameon=False, columnspacing=0.7, handlelength=1.2)
AX[2].legend(handles=[Patch(facecolor="none", edgecolor="black", linewidth=0.8, label="Hot spot"), Patch(facecolor="none", edgecolor="#2171B5", linewidth=0.8, linestyle="--", label="Cold spot")], loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False)
yrs = sorted(N["asr"]); a1 = AX[3]; a2 = a1.twinx()
a1.plot(yrs, [N["asr"][t] for t in yrs], color="#b2182b", marker="s", ms=2.5, lw=0.9)
a2.plot(yrs, [N["ratio_y"][t] for t in yrs], color="#2166AC", marker="o", ms=2.5, lw=0.9)
assert max(N["asr"].values()) < 40 and max(N["ratio_y"].values()) < 30
a1.set_ylim(0, 40); a2.set_ylim(0, 30); a1.set_xticks([2011, 2014, 2017, 2020, 2024]); a1.set_xlabel("Year")
a1.set_ylabel("Deaths per 100,000", color="#b2182b"); a2.set_ylabel("Deaths per 100 persons treated", color="#2166AC")
a1.spines[["top"]].set_visible(False); a2.spines[["top"]].set_visible(False)
a1.legend(handles=[Line2D([0], [0], color="#b2182b", marker="s", ms=2.5, lw=0.9, label="Age-standardized death rate"), Line2D([0], [0], color="#2166AC", marker="o", ms=2.5, lw=0.9, label="Deaths per 100 treated")], frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=1)
for (x, y), ch in zip(((0.005, 0.995), (0.505, 0.995), (0.005, 0.485), (0.505, 0.485)), "ABCD"): letter(fig, x, y, ch)
s1 = save(fig, 1)

# Figure S1
EH = rd("S11_ehsa.csv")
CATS = [f"{a} {b}" for b in ("hot", "cold") for a in ("New", "Consecutive", "Intensifying", "Persistent", "Diminishing", "Sporadic", "Oscillating", "Historical")] + ["No pattern"]
EPAL = {"New hot": "#fdd0a2", "Consecutive hot": "#fdae6b", "Intensifying hot": "#a50f15", "Persistent hot": "#de2d26", "Diminishing hot": "#fc9272", "Sporadic hot": "#fee0d2", "Oscillating hot": "#d6a5c9", "Historical hot": "#bcbddc",
        "New cold": "#c6dbef", "Consecutive cold": "#9ecae1", "Intensifying cold": "#08519c", "Persistent cold": "#3182bd", "Diminishing cold": "#6baed6", "Sporadic cold": "#deebf7", "Oscillating cold": "#a1d99b", "Historical cold": "#c7e9c0", "No pattern": "#f7f7f7"}
WM = rd("S4b_window_spatialRR.csv")
nh = WM[WM["class"] == "hotspot"].groupby("sigungu_cd").size(); nc = WM[WM["class"] == "coldspot"].groupby("sigungu_cd").size()
assert int((nh == 3).sum()) == N["hot_all_windows"] and int((nc == 3).sum()) == N["cold_all_windows"]
fig, (a0, a1) = plt.subplots(1, 2, figsize=(W, 5.0)); fig.subplots_adjust(left=0.01, right=0.99, top=0.80, bottom=0.31, wspace=0.04); letter(fig, 0.01, 0.995, "A"); letter(fig, 0.51, 0.995, "B")
gg = G.copy(); gg["c"] = gg.cd.map(EH.set_index("sigungu_cd").EHSA); assert gg.c.notna().all()
gg.plot(ax=a0, color=[EPAL[c] for c in gg.c], edgecolor="#a0a0a0", linewidth=LW); mapax(a0)
cnt = EH.EHSA.value_counts(); pres = [c for c in CATS if c in cnt.index]
a0.legend(handles=[Patch(facecolor=EPAL[c], edgecolor="#777777", linewidth=LW, label=f"{c} ({cnt[c]})") for c in pres], title="Category (districts)", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, columnspacing=0.8, handlelength=1.2)
hh = gg.cd.map(nh).fillna(0).astype(int); cc = gg.cd.map(nc).fillna(0).astype(int)
gg["k"] = np.where((hh > 0) & (cc > 0), 9, hh - cc)
KP = {-3: "#2166AC", -2: "#67A9CF", -1: "#D1E5F0", 0: "#f7f7f7", 1: "#FDDBC7", 2: "#EF8A62", 3: "#B2182B", 9: "#c2a5cf"}
KL = {-3: "Cold spot in 3 windows", -2: "Cold spot in 2", -1: "Cold spot in 1", 0: "Neither", 1: "Hot spot in 1", 2: "Hot spot in 2", 3: "Hot spot in 3 windows", 9: "Hot or cold by window"}
gg.plot(ax=a1, color=[KP[k] for k in gg.k], edgecolor="#a0a0a0", linewidth=LW); mapax(a1)
kc = gg.k.value_counts()
a1.legend(handles=[Patch(facecolor=KP[k], edgecolor="#777777", linewidth=LW, label=f"{KL[k]} ({kc.get(k, 0)})") for k in (3, 2, 1, 0, -1, -2, -3, 9) if kc.get(k, 0)], title="Windows 2011-2015, 2016-2019, 2020-2024", loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=False, columnspacing=0.8, handlelength=1.2)
s2 = save(fig, "S1")

# Figure 2 — (A) 관외 외래 진료 비율 (B) 대졸 비율
SL = {"ma3": "3-year treatment ratio", "s577": "Queen graph", "s2": "Without age 80+ control", "s8": "Ten age groups"}
def rows(v):
    R = [("Principal", (N["main"][v]["IRR"], N["main"][v]["lo"], N["main"][v]["hi"]), "#000000", "o")]
    R += [(f"KH {k}", N["s43"][(f"KH_type{k}", v)][:3], "#B2182B", "D") for k in ("I", "II", "III", "IV")]
    R += [("Between districts", N["bw"][v + "__between"][:3], "#2166AC", "s"), ("Within districts", N["bw"][v + "__within"][:3], "#67A9CF", "v")]
    R += [(SL[s], N["sens_main"][s][v][:3], "#542788", "P") for s in ("ma3", "s577", "s2", "s8")]
    R += [("Mortality level", N["sens_main"]["smr"][v][:3], "#7f7f7f", "X")]
    R += [("Transport deaths (comparison)", N["nco"][("TRANS", v)][:3], "#E08214", "^"), ("Fall deaths (comparison)", N["nco"][("FALL", v)][:3], "#E08214", "<")]
    return R
fig, axs = plt.subplots(1, 2, figsize=(W, 4.8), sharey=True); fig.subplots_adjust(left=0.27, right=0.98, top=0.80, bottom=0.13, wspace=0.12)
for ax, v, xt, xlim, xl in ((axs[0], OUTC, [0.95, 1.00, 1.05], (0.94, 1.06), "Out-of-district outpatient share"), (axs[1], EDU, [0.85, 0.90, 0.95, 1.00], (0.82, 1.02), "Tertiary education")):
    R = rows(v)
    for i, (lab, (e, lo, hi), col, mk) in enumerate(R):
        ax.plot([lo, hi], [i, i], color=col, lw=0.9); ax.plot(e, i, marker=mk, color=col, ms=4, mew=0, ls="none")
    ax.axvline(1, color="#404040", lw=0.5, ls=":"); ax.set_yticks(range(len(R))); ax.set_yticklabels([r[0] for r in R])
    lo_all = min(r[1][1] for r in R); hi_all = max(r[1][2] for r in R); assert xlim[0] <= lo_all and hi_all <= xlim[1], (v, lo_all, hi_all)
    ax.set_xscale("log"); ax.set_xlim(*xlim); ax.set_xticks(xt); ax.set_xticklabels([f"{x:.2f}" for x in xt]); ax.minorticks_off()
    ax.set_title(xl, fontsize=8, fontweight="bold"); ax.set_xlabel("Rate ratio per 1 SD\n(95% credible interval, log scale)"); ax.spines[["top", "right"]].set_visible(False)
axs[0].invert_yaxis()
letter(fig, 0.005, 0.995, "A"); letter(fig, 0.62, 0.995, "B")
s3 = save(fig, 2, dpi=1200)
for k, s, dp in zip((1, "S1", 2), (s1, s2, s3), (DPI, DPI, 1200)): print(f"Fig{k}: {s[0]}x{s[1]} px = {s[0]/dp*25.4:.0f} x {s[1]/dp*25.4:.0f} mm")
