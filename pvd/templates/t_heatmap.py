import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)

# Heatmap: muitas categorias (> 40) x segunda dimensão; escala sequencial perceptual.
d = df.query(PARAMS["query"]) if PARAMS.get("query") else df
m = d.pivot_table(index=PARAMS["category"], columns=PARAMS["second_dim"], values=PARAMS.get("measure", "consumo_mwh"),
                  aggfunc=PARAMS.get("agg", "sum"))
m = m.loc[m.mean(axis=1).sort_values().index]
fig, ax = plt.subplots(figsize=(9.5, 0.2 * len(m) + 2.2))
sns.heatmap(m, cmap="viridis", ax=ax, cbar_kws={"label": PARAMS.get("cbar", "")}, linewidths=0, yticklabels=True)
ax.tick_params(axis="y", labelsize=7)
ax.set_xlabel(""); ax.set_ylabel("")
ax.set_title(PARAMS.get("title", ""))
utils.save(fig, OUT_PATH)
