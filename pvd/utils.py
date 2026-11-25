"""Utilitários partilhados pelos templates gráficos."""
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns


def apply_style():
    sns.set_theme(style="whitegrid", context="notebook")
    mpl.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 110,
                         "axes.titleweight": "bold", "axes.titlesize": 13, "axes.labelsize": 11,
                         "grid.alpha": 0.35, "font.family": "DejaVu Sans"})


def load(path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["data"], dtype={"codigo_freguesia": "string"}, low_memory=False)


def add_caption(fig, text, y=-0.01):
    fig.text(0.01, y, text, ha="left", va="top", fontsize=8.5, color="#444", wrap=True)


def save(fig, path):
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white")


# ---------- agregações ----------
def municipio_year(df, year):
    d = df[(df.ano == year) & (df.setor == "Total")]
    return (d.groupby(["municipio", "regiao"])
            .agg(consumo=("consumo_mwh", "sum"), n_freguesias=("n_freguesias", "first"))
            .reset_index())


def municipio_domestic(df, year):
    """Backward-compatible alias: the official source has no domestic-sector field."""
    return municipio_year(df, year).rename(columns={"consumo": "mwh"})


def municipio_year_tariff(df, year):
    d = df[(df.ano == year) & (df.setor != "Total")]
    wide = d.pivot_table(index=["municipio", "regiao"], columns="setor", values="consumo_mwh",
                         aggfunc="sum", fill_value=0).reset_index()
    total = municipio_year(df, year).set_index("municipio")
    wide = wide.join(total["n_freguesias"], on="municipio")
    wide["periodo_predominante"] = wide[[c for c in wide.columns if c not in {"municipio", "regiao", "n_freguesias"}]].idxmax(axis=1)
    return wide


def monthly_series(df, setor="Total"):
    s = df[df.setor == setor].groupby("data")["consumo_mwh"].sum() / 1000  # GWh
    return s.sort_index()


def category_table(df, category, measure="consumo_mwh", agg="sum", query=None, per_capita=False):
    d = df.query(query) if query else df
    s = d.groupby(category)[measure].agg(agg)
    if per_capita:
        raise ValueError("O dataset E-REDES nao inclui populacao; nao e possivel calcular consumo per capita.")
    return s.sort_values()


# ---------- LOWESS (local linear, tricubo) ----------
def lowess(x, y, frac=0.4):
    x, y = np.asarray(x, float), np.asarray(y, float)
    n = len(x)
    k = max(int(np.ceil(frac * n)), 3)
    out = np.empty(n)
    for i in range(n):
        d = np.abs(x - x[i])
        idx = np.argsort(d)[:k]
        h = d[idx].max() or 1.0
        w = np.sqrt((1 - (d[idx] / h) ** 3) ** 3)
        X = np.c_[np.ones(k), x[idx] - x[i]]
        out[i] = np.linalg.lstsq(X * w[:, None], y[idx] * w, rcond=None)[0][0]
    return out


# ---------- treemap (squarified, Bruls et al. 2000) ----------
def squarify(values, x, y, w, h):
    total = float(sum(values))
    order = sorted(range(len(values)), key=lambda i: -values[i])
    areas = [values[i] * w * h / total for i in order]
    res = {}

    def worst(row, side):
        s = sum(row)
        return max(side * side * max(row) / (s * s), s * s / (side * side * min(row)))

    i = 0
    while i < len(areas):
        side = min(w, h)
        row, j = [areas[i]], i + 1
        while j < len(areas) and worst(row + [areas[j]], side) <= worst(row, side):
            row.append(areas[j]); j += 1
        s = sum(row)
        if w >= h:
            cw, cy = s / h, y
            for k, a in enumerate(row):
                res[order[i + k]] = (x, cy, cw, a / cw); cy += a / cw
            x += cw; w -= cw
        else:
            rh, cx = s / w, x
            for k, a in enumerate(row):
                res[order[i + k]] = (cx, y, a / rh, rh); cx += a / rh
            y += rh; h -= rh
        i = j
    return [res[k] for k in range(len(values))]
