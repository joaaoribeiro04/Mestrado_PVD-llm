import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)
t = utils.municipio_year(df, 2024)
t["kwh_freguesia"] = t.consumo * 1000 / t.n_freguesias
mediana = t.kwh_freguesia.median()
t["desvio_pct"] = (t.kwh_freguesia / mediana - 1) * 100

fig, (a, b) = plt.subplots(1, 2, figsize=(13, 6), gridspec_kw={"width_ratios": [1.1, 1]})
sc = a.scatter(t.n_freguesias, t.kwh_freguesia, c=t.kwh_freguesia, cmap="viridis", s=55,
               edgecolor="white", linewidth=0.4)
a.set_xscale("log")
a.set_xlabel("Freguesias identificadas por concelho (escala log)")
a.set_ylabel("Energia anual media por freguesia (kWh)")
a.set_title("A. Escala sequencial: magnitude")
fig.colorbar(sc, ax=a, label="kWh por freguesia")

ext = pd.concat([t.nsmallest(7, "desvio_pct"), t.nlargest(7, "desvio_pct")]).sort_values("desvio_pct")
m = max(abs(ext.desvio_pct.min()), abs(ext.desvio_pct.max()))
norm = mpl.colors.TwoSlopeNorm(vcenter=0, vmin=-m, vmax=m)
b.barh(ext.municipio, ext.desvio_pct, color=plt.get_cmap("coolwarm")(norm(ext.desvio_pct)), edgecolor="white")
b.axvline(0, color="#333", lw=0.8)
b.set_xlabel(f"Desvio face a mediana ({mediana:,.0f} kWh/freguesia), %")
b.set_title("B. Escala divergente: desvio a mediana")
b.grid(axis="y", visible=False)
utils.add_caption(fig, "Sequencial para magnitude continua; divergente centrada em zero para desvios com ponto de referencia explicito. "
                       "Energia por freguesia e um indicador territorial aproximado, nao consumo per capita.", y=-0.01)
fig.tight_layout(); utils.save(fig, OUT_PATH)
