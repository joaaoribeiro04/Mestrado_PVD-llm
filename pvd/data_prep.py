"""Prepare E-REDES tariff-period data and write a reproducible canonical table."""
import json
import unicodedata
from collections import Counter

import pandas as pd

from pvd.config import LOGS, PROC, RAW
from pvd.llm import extract_json, get_llm

SOURCE = "E-REDES Open Data Portal - Consumos por municipio por periodo tarifario"
SOURCE_URL = "https://e-redes.opendatasoft.com/explore/dataset/consumos-faturados-por-periodo-tarifario/information/"
LICENSE = "CC BY 4.0"
PERIOD_COLUMNS = {
    "Energia Ativa Simples (kWh)": "Simples",
    "Energia Ativa Vazio (kWh)": "Vazio",
    "Energia Ativa Fora de Vazio (kWh)": "Fora de vazio",
    "Energia Ativa Super Vazio (kWh)": "Super vazio",
    "Energia Ativa Ponta (kWh)": "Ponta",
    "Energia Ativa Cheias (kWh)": "Cheias",
}
TOTAL_COLUMN = "Energia Ativa Total (kWh)"


def _key(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value).strip()).encode("ascii", "ignore").decode()
    return " ".join(value.casefold().split())


def harmonize_rule(names: list[str]) -> dict[str, str]:
    """Normalize case/whitespace while preserving the most common source spelling."""
    groups: dict[str, Counter] = {}
    for name in names:
        groups.setdefault(_key(name), Counter())[name] += 1
    mapping = {}
    for variants in groups.values():
        canonical = max(variants.items(), key=lambda item: (item[1], item[0] == item[0].strip()))[0].strip()
        for variant in variants:
            mapping[variant] = canonical
    return mapping


def harmonize_llm(names: list[str], llm) -> dict[str, str] | None:
    """Use LangChain for spelling-only suggestions; reject identity-changing output."""
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    prompt = ChatPromptTemplate.from_messages([
        ("system", "Normaliza apenas maiusculas, minusculas e espacos em nomes de concelhos portugueses. "
                   "Preserva acentos e identidade. Devolve apenas JSON com todos os nomes como chaves."),
        ("human", "{names}"),
    ])
    raw = (prompt | llm | StrOutputParser()).invoke({"names": json.dumps(names, ensure_ascii=False)})
    mapping = extract_json(raw)
    if not mapping or not all(name in mapping for name in names):
        return None
    if not all(_key(mapping[name]) == _key(name) for name in names):
        return None
    return mapping


def main() -> pd.DataFrame:
    if not RAW.exists():
        raise FileNotFoundError(f"Dataset oficial nao encontrado: {RAW}. Execute python download_dataset.py.")
    raw = pd.read_csv(RAW, sep=";", encoding="utf-8-sig", low_memory=False)
    required = {"Data", "Distrito", "Concelho", "Freguesia", "Código Freguesia", TOTAL_COLUMN, *PERIOD_COLUMNS}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Colunas em falta no CSV E-REDES: {missing}")

    report = {"fonte": SOURCE, "url": SOURCE_URL, "licenca": LICENSE, "linhas_brutas": int(len(raw))}
    raw = raw.rename(columns={"Data": "data", "Distrito": "regiao", "Concelho": "municipio",
                              "Freguesia": "freguesia", "Código Freguesia": "codigo_freguesia"})
    for col in ("municipio", "regiao", "freguesia"):
        raw[col] = raw[col].astype("string").str.strip()

    # Aggregated privacy records do not identify a municipality and are excluded from municipality views.
    aggregated = raw["municipio"].str.upper().str.startswith("OUTROS ", na=False)
    report["linhas_agregadas_sem_concelho"] = int(aggregated.sum())
    raw = raw.loc[~aggregated].copy()

    names = sorted(raw["municipio"].dropna().unique().tolist())
    llm = get_llm()
    mapping, method = None, "regra"
    if llm is not None:
        try:
            mapping = harmonize_llm(names, llm)
            if mapping:
                method = "llm"
        except Exception as exc:
            report["aviso_llm"] = f"LLM indisponivel; aplicado metodo deterministico ({type(exc).__name__})"
    mapping = mapping or harmonize_rule(names)
    report["harmonizacao"] = method
    report["concelhos"] = int(len(names))
    raw["municipio"] = raw["municipio"].map(mapping)

    raw["data"] = pd.to_datetime(raw["data"], format="%Y-%m", errors="coerce")
    raw["codigo_freguesia"] = raw["codigo_freguesia"].astype("string").str.strip()
    numeric_cols = [*PERIOD_COLUMNS, TOTAL_COLUMN]
    for col in numeric_cols:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    report["datas_invalidas"] = int(raw["data"].isna().sum())
    report["nulos_por_periodo"] = {PERIOD_COLUMNS.get(c, "total"): int(raw[c].isna().sum()) for c in numeric_cols}
    report["ajustes_negativos_por_periodo"] = {
        PERIOD_COLUMNS.get(c, "total"): int((raw[c] < 0).sum()) for c in numeric_cols
    }
    report["duplicados_data_freguesia"] = int(raw.duplicated(["data", "codigo_freguesia"]).sum())

    raw = raw.dropna(subset=["data", "municipio", "regiao", TOTAL_COLUMN]).copy()
    # Null period components are treated as zero: the publisher's total equals their sum with nulls as zero.
    raw[list(PERIOD_COLUMNS)] = raw[list(PERIOD_COLUMNS)].fillna(0)
    raw["ano"], raw["mes"] = raw["data"].dt.year, raw["data"].dt.month
    parish_count = (raw[raw["codigo_freguesia"].str.fullmatch(r"\d{6}", na=False)]
                    .groupby("municipio")["codigo_freguesia"].nunique().rename("n_freguesias"))
    raw = raw.join(parish_count, on="municipio")
    raw["n_freguesias"] = raw["n_freguesias"].fillna(1).astype(int)

    id_cols = ["municipio", "regiao", "freguesia", "codigo_freguesia", "data", "ano", "mes", "n_freguesias"]
    long = raw.melt(id_vars=id_cols, value_vars=list(PERIOD_COLUMNS), var_name="periodo_origem",
                    value_name="consumo_kwh")
    long["setor"] = long.pop("periodo_origem").map(PERIOD_COLUMNS)
    totals = raw[id_cols + [TOTAL_COLUMN]].rename(columns={TOTAL_COLUMN: "consumo_kwh"}).copy()
    totals["setor"] = "Total"
    df = pd.concat([long, totals], ignore_index=True)
    df["consumo_mwh"] = df["consumo_kwh"] / 1000.0
    df = df.sort_values(["municipio", "setor", "data", "codigo_freguesia"]).reset_index(drop=True)

    report.update({
        "periodo": [df["data"].min().strftime("%Y-%m"), df["data"].max().strftime("%Y-%m")],
        "linhas_canonicas": int(len(df)),
        "concelhos_finais": int(df["municipio"].nunique()),
        "distritos": int(df["regiao"].nunique()),
        "freguesias": int(df["codigo_freguesia"].nunique()),
        "categorias_tarifarias": sorted(long["setor"].unique().tolist()),
        "nulos_periodos_preenchidos_com_zero": int(sum(report["nulos_por_periodo"].values())),
        "total_vs_soma_periodos_max_abs_kwh": round(float((raw[TOTAL_COLUMN] - raw[list(PERIOD_COLUMNS)].sum(axis=1)).abs().max()), 6),
    })
    df.to_csv(PROC, index=False, encoding="utf-8")
    (LOGS / "data_prep.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[prep]", json.dumps(report, ensure_ascii=False))
    return df


if __name__ == "__main__":
    main()
