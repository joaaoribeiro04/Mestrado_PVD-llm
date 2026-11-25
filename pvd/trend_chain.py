"""Parte II Fase 1: prompt chaining (LangChain LCEL) que transforma coeficientes estatísticos em título e legenda.

  estatísticas (scipy) -> [prompt 1: descrever a tendência] -> [prompt 2: redigir título + legenda] -> META

O LLM só pode usar os números fornecidos; um verificador confirma que o título não contém números ausentes dos coeficientes.
"""
import json
import re

import numpy as np
from scipy import stats

from pvd import llm as L
from pvd import utils
from pvd.config import PROC


def corr_stats(df) -> dict:
    t = utils.municipio_year(df, 2024)
    lx, y = np.log10(t["n_freguesias"]), t.consumo / 1000.0
    pr, pp = stats.pearsonr(lx, y)
    sr, sp = stats.spearmanr(t["n_freguesias"], y)
    lr = stats.linregress(lx, y)
    return {"kind": "correlação", "n": int(len(t)), "pearson_r": round(float(pr), 2), "pearson_p": float(f"{pp:.2g}"),
            "spearman_rho": round(float(sr), 2), "slope_por_decada_freguesias": round(float(lr.slope), 2),
            "r2": round(float(lr.rvalue ** 2), 2), "x": "freguesias por concelho (log10)",
            "y": "energia ativa total (GWh/ano)"}


def ts_stats(df) -> dict:
    s = utils.monthly_series(df, "Total")
    anual = s.groupby(s.index.year).sum()
    yrs = anual.index.values
    lr = stats.linregress(yrs, anual.values)
    low = utils.lowess(np.arange(len(s)), s.values, 0.6)
    mes = s.groupby(s.index.month).mean()
    return {"kind": "série temporal", "periodo": f"{yrs[0]}-{yrs[-1]}", "slope_gwh_por_ano": round(float(lr.slope), 1),
            "variacao_anual_pct": round(float(lr.slope / anual.mean() * 100), 2), "r2": round(float(lr.rvalue ** 2), 2),
            "p": float(f"{lr.pvalue:.2g}"), "variacao_lowess_pct": round(float((low[-1] / low[0] - 1) * 100), 1),
            "mes_pico": int(mes.idxmax()), "mes_minimo": int(mes.idxmin()),
            "razao_pico_minimo": round(float(mes.max() / mes.min()), 2), "unidade": "GWh"}


def offline_text(st: dict) -> dict:
    if st["kind"] == "correlação":
        sinal = "negativa" if st["pearson_r"] < 0 else "positiva"
        forca = "forte" if abs(st["pearson_r"]) >= 0.6 else "moderada" if abs(st["pearson_r"]) >= 0.3 else "fraca"
        return {"title": f"Mais freguesias associam-se a maior consumo total (r = {st['pearson_r']})",
                "caption": f"Associação linear {sinal} {forca} (Pearson r = {st['pearson_r']}, p = {st['pearson_p']}; "
                           f"Spearman ρ = {st['spearman_rho']}; n = {st['n']} concelhos). R² = {st['r2']}: o ajuste linear "
                           f"descreve parte da variação observada. Associação não implica causalidade."}
    sentido = "diminui" if st["slope_gwh_por_ano"] < 0 else "aumenta"
    return {"title": f"A energia ativa total {sentido} {abs(st['variacao_anual_pct'])}% ao ano ({st['periodo']})",
            "caption": f"Regressão linear sobre totais anuais: {st['slope_gwh_por_ano']} GWh/ano (R² = {st['r2']}, p = {st['p']}). "
                       f"LOWESS: {st['variacao_lowess_pct']:+.1f}% entre início e fim. Pico médio no mês "
                       f"{st['mes_pico']}, mínimo no mês {st['mes_minimo']} (razão {st['razao_pico_minimo']}x)."}


def _numbers(text: str) -> set[float]:
    return {abs(float(x)) for x in re.findall(r"\d+(?:\.\d+)?", text.replace(",", "."))}


def verify(meta: dict, st: dict) -> bool:
    """Todos os números no título/legenda têm de existir nos coeficientes (ou ser n/ano)."""
    allowed = set()
    for v in st.values():
        if isinstance(v, (int, float)):
            allowed |= {abs(float(v)), round(abs(float(v))), round(abs(float(v)), 1), round(abs(float(v)), 2)}
        elif isinstance(v, str):
            allowed |= _numbers(v)
    allowed |= {abs(st["r2"] * 100), round(abs(st["r2"]) * 100)} if "r2" in st else set()
    return all(x in allowed for x in _numbers(meta["title"] + " " + meta["caption"]))


def build_meta(df, kind: str, llm=None) -> tuple[dict, dict]:
    st = corr_stats(df) if kind == "corr" else ts_stats(df)
    meta, source = None, "regra"
    if llm is not None:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.runnables import RunnablePassthrough
        p1 = ChatPromptTemplate.from_messages([
            ("system", "És analista de dados. Descreve em 2-3 frases, em português de Portugal, a tendência/associação que "
                       "estes coeficientes mostram. Usa SÓ os números fornecidos."), ("human", "{stats_json}")])
        p2 = ChatPromptTemplate.from_messages([
            ("system", "Redige o título (afirma a conclusão, <=90 caracteres) e a legenda (2-3 frases, inclui os coeficientes "
                       "principais) de um gráfico. Usa SÓ números presentes nos coeficientes. Devolve apenas JSON "
                       "{{\"title\": \"...\", \"caption\": \"...\"}}."),
            ("human", "Coeficientes: {stats_json}\nDescrição: {description}")])
        chain = RunnablePassthrough.assign(description=p1 | llm | StrOutputParser()) | p2 | llm | StrOutputParser()
        try:
            j = L.extract_json(chain.invoke({"stats_json": json.dumps(st, ensure_ascii=False)}))
            if j and {"title", "caption"} <= j.keys() and verify(j, st):
                meta, source = {"title": j["title"], "caption": j["caption"]}, "llm"
        except Exception:
            meta = None
    meta = meta or offline_text(st)
    meta["source"] = source
    return st, meta
