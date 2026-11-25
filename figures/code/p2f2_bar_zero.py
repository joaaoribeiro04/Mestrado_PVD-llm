import matplotlib
matplotlib.use('Agg')
from pathlib import Path
import sys
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
DATA_PATH = str(ROOT / 'data' / 'processed' / 'consumo.csv')
OUT_PATH = str(ROOT / 'figures' / 'p2f2_bar_zero.png')
PARAMS = {}
META = {}

import matplotlib.pyplot as plt
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)
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
