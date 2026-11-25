import matplotlib
matplotlib.use('Agg')
DATA_PATH = 'C:\\Users\\JPMR0\\Documents\\Codex\\2026-11-19\\referenced-chatgpt-conversation-this-is-an\\work\\my_langgraph_project\\data\\processed\\consumo.csv'
OUT_PATH = 'C:\\Users\\JPMR0\\Documents\\Codex\\2026-11-19\\referenced-chatgpt-conversation-this-is-an\\work\\my_langgraph_project\\figures\\p1f2_treemap.png'
PARAMS = {}
META = {}

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)
d = (df[(df.ano == 2024) & (df.setor != "Total")]
     .groupby(["setor", "regiao"]).consumo_mwh.sum().reset_index())
tot = d.groupby("setor").consumo_mwh.sum().sort_values(ascending=False)
cores = dict(zip(tot.index, sns.color_palette("colorblind", len(tot))))
fig, ax = plt.subplots(figsize=(11, 7))
for (periodo, value), (x, y, w, h) in zip(tot.items(), utils.squarify(list(tot.values), 0, 0, 1, 1)):
    sub = d[(d.setor == periodo) & (d.consumo_mwh > 0)].sort_values("consumo_mwh", ascending=False)
    if sub.empty: continue
    rects = utils.squarify(list(sub.consumo_mwh), x, y, w, h)
    for (_, row), (sx, sy, sw, sh) in zip(sub.iterrows(), rects):
        ax.add_patch(mpl.patches.Rectangle((sx, sy), sw, sh, facecolor=cores[periodo], edgecolor="white", lw=0.8, alpha=0.9))
        if sw * sh > 0.012:
            ax.text(sx + sw / 2, sy + sh / 2, row.regiao.replace(" e Vale do Tejo", "\ne VT"),
                    ha="center", va="center", fontsize=7, color="white", fontweight="bold")
    ax.add_patch(mpl.patches.Rectangle((x, y), w, h, fill=False, edgecolor="black", lw=1.5))
    if w * h > 0.03:
        ax.text(x + 0.006, y + 0.012, f"{periodo}  {value / tot.sum():.0%}", ha="left", va="top",
                fontsize=9, fontweight="bold", color="black", bbox=dict(facecolor="white", alpha=0.8, pad=1.5, lw=0))
ax.set_xlim(0, 1); ax.set_ylim(1, 0); ax.axis("off")
ax.set_title("Quota da energia ativa em 2024: periodo tarifario e distrito")
utils.save(fig, OUT_PATH)
