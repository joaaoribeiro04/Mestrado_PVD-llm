"""Parte I Fase 2: fluxo agêntico que perfila o dataset (volume e cardinalidade) e escolhe a geometria.

  profile_data -> decide -> build_spec -> render (subgrafo cíclico de pvd.graph)

Regras (Wilke cap. 6 + prática): <=8 categorias -> barras; 9-40 -> dot plot ordenado;
>40 categorias com 2.ª dimensão categórica/ordinal -> heatmap. O LLM (se existir) propõe a geometria, mas a decisão é
validada contra as regras de cardinalidade (um LLM não pode escolher barras para 51 categorias).
"""
import json
from typing import TypedDict

from langgraph.graph import END, StateGraph

from pvd import llm as L
from pvd.graph import run_figure
from pvd.utils import load
from pvd.config import PROC

TEMPLATES = {"bar": "t_bar", "dotplot": "t_dotplot", "heatmap": "t_heatmap"}


class SState(TypedDict, total=False):
    request: dict
    profile: dict
    choice: str
    rationale: str
    result: dict


def rule_choice(p: dict) -> tuple[str, str]:
    n, two = p["cardinality"], p["has_second_dim"]
    if n <= 8:
        return "bar", f"{n} categorias (<=8): barras horizontais são legíveis e o comprimento codifica o valor."
    if n <= 40:
        return "dotplot", f"{n} categorias (9-40): dot plot ordenado evita barras densas e poupa tinta."
    if two:
        return "heatmap", f"{n} categorias (>40) e uma segunda dimensão ({p['second_dim']}): heatmap em vez de barras impraticáveis."
    return "dotplot", f"{n} categorias (>40) sem segunda dimensão: dot plot alto e ordenado."


def build_selector(llm=None, vision_llm=None):
    def profile(state: SState):
        r = state["request"]
        df = load(PROC)
        d = df.query(r["params"]["query"]) if r["params"].get("query") else df
        cat = r["params"]["category"]
        prof = {"category": cat, "cardinality": int(d[cat].nunique()), "n_rows": int(len(d)),
                "second_dim": r["params"].get("second_dim"), "has_second_dim": bool(r["params"].get("second_dim")),
                "measure_is_numeric": True}
        return {"profile": prof}

    def decide(state: SState):
        p = state["profile"]
        choice, why = rule_choice(p)
        if llm is not None:
            try:
                out = L.ask(llm, "Escolhe a geometria mais adequada (bar | dotplot | heatmap) para uma variável categórica com "
                                 "o perfil dado, segundo Wilke. Responde só JSON {\"choice\": ..., \"rationale\": ...}.",
                            json.dumps(p, ensure_ascii=False))
                j = L.extract_json(out) or {}
                if j.get("choice") == choice:  # LLM concorda com as regras de cardinalidade
                    why = j.get("rationale", why)
                elif j.get("choice") in TEMPLATES:
                    why += f" (LLM sugeriu '{j['choice']}', rejeitado pela regra de cardinalidade.)"
            except Exception as e:
                why += f" (LLM indisponível: {e})"
        return {"choice": choice, "rationale": why}

    def build_spec(state: SState):
        r = state["request"]
        spec = {**r, "template": TEMPLATES[state["choice"]], "meta": {"selector_rationale": state["rationale"]}}
        return {"request": spec}

    def render(state: SState):
        return {"result": run_figure(state["request"], llm=llm, vision_llm=vision_llm)}

    g = StateGraph(SState)
    for n, f in [("profile_data", profile), ("decide", decide), ("build_spec", build_spec), ("render", render)]:
        g.add_node(n, f)
    g.set_entry_point("profile_data")
    g.add_edge("profile_data", "decide"); g.add_edge("decide", "build_spec")
    g.add_edge("build_spec", "render"); g.add_edge("render", END)
    return g.compile()


def run_selector(request: dict, llm=None, vision_llm=None):
    return build_selector(llm, vision_llm).invoke({"request": request})
