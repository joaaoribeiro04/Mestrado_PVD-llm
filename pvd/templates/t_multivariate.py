import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import gaussian_kde
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)
d = (df[(df.ano == 2024) & (df.setor != "Total")]
     .groupby(["municipio", "regiao", "setor"], as_index=False).consumo_mwh.sum())
d = d[d.consumo_mwh > 0]
tot = utils.municipio_year(df, 2024)
top = tot.groupby("regiao").consumo.sum().nlargest(6).index
ridge = tot[tot.regiao.isin(top)].copy()
ridge["kwh_freguesia"] = ridge.consumo * 1000 / ridge.n_freguesias
ridge = ridge[ridge.kwh_freguesia > 0]
regs = ridge.groupby("regiao").kwh_freguesia.median().sort_values().index
lo, hi = ridge.kwh_freguesia.quantile([0.01, 0.99])
xs = np.linspace(lo, hi, 300)

fig, (a, b) = plt.subplots(1, 2, figsize=(13, 5.8), gridspec_kw={"width_ratios": [1.1, 1]})
sns.violinplot(data=d, x="setor", y="consumo_mwh", hue="setor", palette="colorblind", legend=False,
               inner="box", cut=0, linewidth=0.8, ax=a)
a.set_yscale("log"); a.set_xlabel(""); a.set_ylabel("Energia anual por concelho (MWh, escala log)")
a.set_title("A. Distribuicoes por periodo tarifario"); a.tick_params(axis="x", rotation=18)
for i, regiao in enumerate(regs):
    vals = ridge.loc[ridge.regiao == regiao, "kwh_freguesia"].to_numpy()
    if len(vals) < 2 or np.std(vals) == 0: continue
    density = gaussian_kde(vals)(xs)
    density = density / density.max() * 0.8
    b.fill_between(xs, i, i + density, color="#4c72b0", alpha=0.75, edgecolor="white", lw=0.8)
b.set_yticks(range(len(regs))); b.set_yticklabels(regs)
b.set_xlabel("Energia anual media por freguesia (kWh)")
b.set_title("B. Distribuicoes nos seis distritos com maior consumo")
b.grid(axis="y", visible=False)
fig.tight_layout(); utils.save(fig, OUT_PATH)
