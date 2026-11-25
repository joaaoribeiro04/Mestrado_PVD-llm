#!/usr/bin/env python
"""Reproduz o projeto de ponta a ponta: dados brutos -> limpeza -> grafos agênticos -> figuras.

Uso:  python run_all.py [--part 1|2] [--only <id>] [--regen-data]
Env:  LLM_PROVIDER=none|gemini|groq|openai|ollama (ver .env.example)
"""
import argparse
import json
import sys

from pvd import data_prep, trend_chain
from pvd.config import LOGS, PROC, RAW
from pvd.figures import FIGURES
from pvd.graph import run_figure
from pvd.llm import get_llm, provider
from pvd.selector_graph import run_selector
from pvd.utils import load


def main():
    for stream in (sys.stdout, sys.stderr):  # consolas Windows (cp1252) vs. caracteres Unicode
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", type=int, choices=[1, 2])
    ap.add_argument("--only")
    ap.add_argument("--regen-data", action="store_true", help="força novamente o tratamento do CSV oficial")
    a = ap.parse_args()

    if not RAW.exists():
        ap.error(f"CSV oficial em falta: {RAW}. Execute python download_dataset.py.")
    if not PROC.exists() or a.regen_data or RAW.stat().st_mtime > PROC.stat().st_mtime:
        data_prep.main()

    llm = get_llm()
    vision = get_llm(vision=True)
    print(f"[run] fornecedor LLM: {provider()}")
    df = load(PROC)
    summary = []
    for spec in FIGURES:
        if (a.part and spec["part"] != a.part) or (a.only and spec["id"] != a.only):
            continue
        spec = dict(spec)
        if spec.get("chain"):  # prompt chaining -> título/legenda a partir dos coeficientes
            st, meta = trend_chain.build_meta(df, spec["chain"], llm)
            spec["meta"] = meta
            (LOGS / f"{spec['id']}_stats.json").write_text(json.dumps({"stats": st, "meta": meta}, indent=2, ensure_ascii=False))
        if spec.get("selector"):
            res = run_selector(spec, llm, vision)
            final = res["result"]
            extra = f"geometria={res['choice']} ({res['rationale']})"
        else:
            final = run_figure(spec, llm, vision)
            extra = ""
        summary.append({"id": spec["id"], "status": final["status"], "iteracoes": final["iteration"], "nota": extra})
        print(f"[{final['status']:>14}] {spec['id']:<20} iter={final['iteration']} {extra}")
    (LOGS / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
