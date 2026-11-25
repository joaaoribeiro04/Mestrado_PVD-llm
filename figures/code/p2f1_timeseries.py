import matplotlib
matplotlib.use('Agg')
DATA_PATH = 'C:\\Users\\JPMR0\\Documents\\Codex\\2026-11-19\\referenced-chatgpt-conversation-this-is-an\\work\\my_langgraph_project\\data\\processed\\consumo.csv'
OUT_PATH = 'C:\\Users\\JPMR0\\Documents\\Codex\\2026-11-19\\referenced-chatgpt-conversation-this-is-an\\work\\my_langgraph_project\\figures\\p2f1_timeseries.png'
PARAMS = {}
META = {'title': 'A energia ativa total aumenta 2.4% ao ano (2023-2025)', 'caption': 'Regressão linear sobre totais anuais: 1120.8 GWh/ano (R² = 0.97, p = 0.11). LOWESS: +6.9% entre início e fim. Pico médio no mês 1, mínimo no mês 4 (razão 1.19x).', 'source': 'regra'}

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
