import matplotlib
matplotlib.use('Agg')
DATA_PATH = 'C:\\Users\\JPMR0\\Documents\\Codex\\2026-11-19\\referenced-chatgpt-conversation-this-is-an\\work\\my_langgraph_project\\data\\processed\\consumo.csv'
OUT_PATH = 'C:\\Users\\JPMR0\\Documents\\Codex\\2026-11-19\\referenced-chatgpt-conversation-this-is-an\\work\\my_langgraph_project\\figures\\p1f2_cat_norte.png'
PARAMS = {'category': 'municipio', 'measure': 'consumo_mwh', 'agg': 'sum', 'query': "regiao == 'Porto' and ano == 2024 and setor == 'Total'", 'xlabel': 'Energia ativa em 2024 (MWh)', 'title': 'Concelhos do distrito do Porto, 2024'}
META = {}

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)

# Dot plot de Cleveland: nº intermédio de categorias (9-40), ordenado; cor = região (qualitativa).
s = utils.category_table(df, PARAMS["category"], PARAMS.get("measure", "consumo_mwh"), PARAMS.get("agg", "sum"),
                         PARAMS.get("query"), PARAMS.get("per_capita", False)) / PARAMS.get("scale", 1)
reg = df.drop_duplicates("municipio").set_index("municipio")["regiao"]
fig, ax = plt.subplots(figsize=(8.5, 0.38 * len(s) + 2))
if PARAMS["category"] == "municipio":
    cores = dict(zip(sorted(reg.unique()), sns.color_palette("colorblind", reg.nunique())))
    for i, (k, v) in enumerate(s.items()):
        ax.hlines(i, s.min() * 0.0, v, color="#cfcfcf", lw=1, zorder=1)
        ax.scatter(v, i, s=70, color=cores[reg[k]], zorder=2)
    ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=c, label=r) for r, c in cores.items() if r in set(reg[s.index])],
              frameon=False, loc="lower right", title="Região")
else:
    ax.scatter(s.values, range(len(s)), s=70, color="#4c72b0", zorder=2)
ax.set_yticks(range(len(s))); ax.set_yticklabels(s.index)
ax.set_xlabel(PARAMS.get("xlabel", "")); ax.set_title(PARAMS.get("title", ""))
ax.grid(axis="y", alpha=0.25)
utils.save(fig, OUT_PATH)
