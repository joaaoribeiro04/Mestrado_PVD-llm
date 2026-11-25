import matplotlib.pyplot as plt
import seaborn as sns
from pvd import utils

utils.apply_style()
df = utils.load(DATA_PATH)
t = utils.municipio_year_tariff(df, 2024)
t["vazio_mwh"] = t.get("Vazio", 0) + t.get("Super vazio", 0)
t["ponta_mwh"] = t.get("Ponta", 0) + t.get("Cheias", 0)
fig, ax = plt.subplots(figsize=(11, 6.5))
sns.scatterplot(data=t, x="vazio_mwh", y="ponta_mwh", size="n_freguesias", sizes=(20, 500),
                hue="periodo_predominante", style="periodo_predominante", palette="colorblind",
                alpha=0.8, edgecolor="white", linewidth=0.5, ax=ax)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Energia anual em vazio + super vazio (MWh, escala log)")
ax.set_ylabel("Energia anual em ponta + cheias (MWh, escala log)")
ax.set_title("Consumo por concelho e regime tarifario, 2024")
ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False, title="Periodo predominante / nº freguesias")
utils.add_caption(fig, "Posicao: energia anual nos periodos de vazio e de ponta. Tamanho: numero de freguesias com codigo oficial. "
                       "Matiz e forma: periodo tarifario com maior consumo. A escala log compara concelhos com ordens de grandeza distintas.", y=-0.02)
utils.save(fig, OUT_PATH)
