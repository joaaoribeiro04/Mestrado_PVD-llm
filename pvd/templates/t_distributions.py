import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)
d = utils.municipio_year(df, 2024)
d["kwh_freguesia"] = d.consumo * 1000 / d.n_freguesias
top = d.groupby("regiao").consumo.sum().nlargest(6).index
shown = d[d.regiao.isin(top)]

fig, (a, b) = plt.subplots(1, 2, figsize=(12, 4.8))
sns.histplot(d, x="kwh_freguesia", bins=35, stat="density", color="#9bb7d4", edgecolor="white", ax=a)
sns.kdeplot(d, x="kwh_freguesia", color="#1f3b63", lw=2, ax=a)
a.set_xlabel("Energia anual media por freguesia (kWh)"); a.set_ylabel("Densidade")
a.set_title("A. Distribuicao entre concelhos")
sns.kdeplot(shown, x="kwh_freguesia", hue="regiao", palette="colorblind", common_norm=False,
            fill=False, lw=1.6, ax=b)
b.set_xlabel("Energia anual media por freguesia (kWh)"); b.set_ylabel("")
b.set_title("B. Densidades nos seis distritos com maior consumo")
sns.move_legend(b, "upper left", bbox_to_anchor=(1.01, 1), title="Distrito", frameon=False)
fig.tight_layout(); utils.save(fig, OUT_PATH)
