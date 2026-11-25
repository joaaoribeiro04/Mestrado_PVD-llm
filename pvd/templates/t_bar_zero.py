import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)

# Bar charts encode magnitude by length, so the quantitative axis starts at zero.
s = utils.category_table(df, "regiao", "consumo_mwh", "sum", "ano == 2024 and setor == 'Total'")
fig, ax = plt.subplots(figsize=(10, 8))
ax.barh(s.index, s.values, color="#4c72b0", edgecolor="white")
for y, v in enumerate(s.values):
    ax.text(v, y, f" {v:,.0f}", va="center", fontsize=8)
ax.set_xlim(0, s.max() * 1.18)
ax.set_xlabel("Energia ativa total (MWh)")
ax.set_title("Energia ativa por distrito, 2024")
ax.grid(axis="y", visible=False)
utils.save(fig, OUT_PATH)
