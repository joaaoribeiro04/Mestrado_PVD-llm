import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)

# Série temporal + suavização (Wilke caps. 13-14): série bruta, média móvel 12m e LOWESS; título/legenda via META.
s = utils.monthly_series(df, "Total")
t = np.arange(len(s))
fig, ax = plt.subplots(figsize=(11, 5.4))
ax.plot(s.index, s.values, color="#9bb7d4", lw=1.4, label="Mensal (bruto)")
ax.plot(s.index, s.rolling(12, center=True).mean(), color="#4c72b0", lw=1.8, ls="--", label="Média móvel 12 meses")
ax.plot(s.index, utils.lowess(t, s.values, frac=0.6), color="#1f3b63", lw=2.6, label="Tendência LOWESS")
ax.set_ylabel("Energia ativa nacional (GWh/mês)"); ax.set_xlabel("")
ax.set_title(META.get("title", "Energia ativa total mensal"), loc="left")
ax.legend(frameon=False, loc="upper right", ncol=3, fontsize=9)
utils.add_caption(fig, META.get("caption", ""), y=-0.01)
utils.save(fig, OUT_PATH)
