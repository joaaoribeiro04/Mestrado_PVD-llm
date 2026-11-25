import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)
t = utils.municipio_year(df, 2024)
t["consumo_gwh"] = t.consumo / 1000
x, y = np.log10(t.n_freguesias.values), t.consumo_gwh.values
xs = np.linspace(x.min(), x.max(), 100)
rng = np.random.default_rng(0)
boot = []
for _ in range(500):
    i = rng.integers(0, len(x), len(x))
    boot.append(np.polyval(np.polyfit(x[i], y[i], 1), xs))
lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
fig, ax = plt.subplots(figsize=(9.5, 6))
ax.fill_between(10 ** xs, lo, hi, color="#4c72b0", alpha=0.18, lw=0, label="IC 95% (bootstrap)")
ax.plot(10 ** xs, np.polyval(np.polyfit(x, y, 1), xs), color="#1f3b63", lw=2, label="Ajuste linear em log10(x)")
sns.scatterplot(data=t, x="n_freguesias", y="consumo_gwh", color="#35618f",
                s=46, edgecolor="white", linewidth=0.3, ax=ax)
ax.set_xscale("log")
ax.set_xlabel("Numero de freguesias identificadas (escala log)"); ax.set_ylabel("Energia ativa total em 2024 (GWh)")
ax.set_title(META.get("title", "Numero de freguesias e consumo total por concelho"), loc="left")
ax.legend(frameon=False, loc="upper left", fontsize=8)
utils.add_caption(fig, META.get("caption", "Associacao descritiva; nao implica causalidade."), y=-0.01)
utils.save(fig, OUT_PATH)
