"""Declarative portfolio based on the E-REDES open tariff-period dataset."""

CVD_PALETTES = [("colorblind", "categorical"), ("viridis", "continuous"), ("cividis", "continuous"),
                ("coolwarm", "diverging"), ("Set2", "categorical"), ("jet", "continuous")]

FIGURES = [
    # Part I, phase 1
    dict(id="p1f1_aesthetics", part=1, phase=1, template="t_aesthetics",
         desc="Consumo anual por concelho: periodos de vazio vs ponta; tamanho=numero de freguesias; cor+forma=periodo predominante."),
    dict(id="p1f1_color_scales", part=1, phase=1, template="t_color_scales",
         desc="Escala sequencial para energia anual media por freguesia e divergente para desvios a mediana."),
    # Part I, phase 2
    dict(id="p1f2_cat_setor", part=1, phase=2, selector=True,
         desc="Energia anual por periodo tarifario em 2024.",
         params=dict(category="setor", measure="consumo_mwh", agg="sum",
                     query="ano == 2024 and setor != 'Total'", scale=1000,
                     xlabel="Energia ativa em 2024 (GWh)", title="Consumo por periodo tarifario, 2024")),
    dict(id="p1f2_cat_norte", part=1, phase=2, selector=True,
         desc="Consumo total por concelho no distrito do Porto em 2024.",
         params=dict(category="municipio", measure="consumo_mwh", agg="sum",
                     query="regiao == 'Porto' and ano == 2024 and setor == 'Total'",
                     xlabel="Energia ativa em 2024 (MWh)", title="Concelhos do distrito do Porto, 2024")),
    dict(id="p1f2_cat_heatmap", part=1, phase=2, selector=True,
         desc="Consumo anual total por concelho e ano.",
         params=dict(category="municipio", second_dim="ano", measure="consumo_mwh", agg="sum",
                     query="setor == 'Total'", cbar="Energia ativa (MWh)",
                     title="Consumo anual por concelho, 2023-2025")),
    dict(id="p1f2_distributions", part=1, phase=2, template="t_distributions",
         desc="Distribuicao da energia anual por freguesia e densidades por distrito."),
    dict(id="p1f2_multivariate", part=1, phase=2, template="t_multivariate",
         desc="Violin plots por periodo tarifario e ridgeline por distritos com maior consumo."),
    dict(id="p1f2_treemap", part=1, phase=2, template="t_treemap",
         desc="Treemap aninhado: periodo tarifario > distrito; area=energia ativa em 2024."),
    # Part II, phase 1
    dict(id="p2f1_correlation", part=2, phase=1, template="t_scatter_corr", chain="corr",
         desc="Associacao entre numero de freguesias e energia anual por concelho, com OLS, IC bootstrap e correlacao."),
    dict(id="p2f1_timeseries", part=2, phase=1, template="t_timeseries", chain="ts",
         desc="Serie mensal nacional da energia ativa total com media movel de 12 meses e LOWESS."),
    # Part II, phase 2
    dict(id="p2f2_bar_zero", part=2, phase=2, template="t_bar_zero", naive_template="t_bar_zero_naive",
         desc="Barras do consumo anual total por distrito; eixo quantitativo comeca em zero."),
    dict(id="p2f2_cvd", part=2, phase=2, template="t_cvd",
         desc="Teste CVD de paletas e simulacoes das figuras finais.",
         params=dict(palettes=CVD_PALETTES,
                     images=["p1f1_aesthetics.png", "p1f1_color_scales.png", "p1f2_treemap.png", "p2f1_correlation.png"])),
]
