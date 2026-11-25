import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)

# VERSÃO INGÉNUA (usada só para demonstrar o ciclo de rejeição): eixo truncado exagera diferenças.
s = utils.category_table(df, "regiao", "consumo_mwh", "sum", "ano == 2024 and setor == 'Total'")
fig, ax = plt.subplots(figsize=(9, 5.2))
ax.bar(s.index, s.values, color="#4c72b0", edgecolor="white")
ax.set_ylim(s.min() * 0.97, s.max() * 1.02)
ax.set_ylabel("Energia ativa total (MWh)"); ax.set_title("Energia ativa por distrito, 2024")
ax.tick_params(axis="x", rotation=15)
utils.save(fig, OUT_PATH)
