import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)

# Barras: poucas categorias (<= 8). Eixo a começar em 0 (comprimento = valor).
s = utils.category_table(df, PARAMS["category"], PARAMS.get("measure", "consumo_mwh"), PARAMS.get("agg", "sum"),
                         PARAMS.get("query"), PARAMS.get("per_capita", False)) / PARAMS.get("scale", 1)
fig, ax = plt.subplots(figsize=(9, 0.7 * len(s) + 2))
ax.barh(s.index, s.values, color="#4c72b0", edgecolor="white")
for y, v in enumerate(s.values):
    ax.text(v, y, f" {v:,.1f}", va="center", fontsize=9)
ax.set_xlim(0, s.max() * 1.15)
ax.set_xlabel(PARAMS.get("xlabel", "")); ax.set_title(PARAMS.get("title", ""))
ax.grid(axis="y", visible=False)
utils.save(fig, OUT_PATH)
