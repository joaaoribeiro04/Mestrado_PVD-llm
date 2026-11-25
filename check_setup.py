#!/usr/bin/env python
"""Diagnóstico do ambiente: python -m pip install -r requirements.txt && python check_setup.py"""
import argparse
import importlib
import json
import os
import sys
import urllib.request

from pvd import config  # noqa: F401  (carrega o .env)

OK, KO = "[ OK ]", "[FALHA]"
bad = 0
parser = argparse.ArgumentParser()
parser.add_argument("--vision", action="store_true",
                    help="testa o modelo multimodal com uma figura existente")
args = parser.parse_args()


def report(ok, msg):
    global bad
    bad += (not ok)
    print(f"{OK if ok else KO} {msg}")


print(f"Python {sys.version.split()[0]}")
for mod, pkg in [("pandas", "pandas"), ("numpy", "numpy"), ("scipy", "scipy"), ("matplotlib", "matplotlib"),
                 ("seaborn", "seaborn"), ("PIL", "pillow"), ("langgraph.graph", "langgraph"),
                 ("langchain_core", "langchain-core"), ("langchain_ollama", "langchain-ollama")]:
    try:
        importlib.import_module(mod)
        report(True, f"import {mod}")
    except Exception as e:
        report(False, f"import {mod}  ->  pip install {pkg}   ({type(e).__name__}: {e})")

prov = os.getenv("LLM_PROVIDER", "none").lower()
print(f"\nLLM_PROVIDER={prov}  LLM_MODEL={os.getenv('LLM_MODEL')}  LLM_VISION_MODEL={os.getenv('LLM_VISION_MODEL')}")
if prov == "ollama":
    base = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    try:
        tags = json.load(urllib.request.urlopen(f"{base}/api/tags", timeout=5))
        names = [m["name"] for m in tags.get("models", [])]
        report(True, f"servidor Ollama a responder em {base}; modelos: {names}")
        for var in ("LLM_MODEL", "LLM_VISION_MODEL"):
            m = os.getenv(var, "")
            if m and m.lower() != "none":
                found = any(n == m or n.split(":")[0] == m.split(":")[0] and ":" not in m for n in names)
                report(found, f"{var}={m} instalado" + ("" if found else f"  ->  ollama pull {m}"))
    except Exception as e:
        report(False, f"Ollama inacessível em {base}: abrir a aplicação Ollama ou correr `ollama serve` ({e})")
    else:
        try:
            from pvd.llm import ask, get_llm
            out = ask(get_llm(), "Responde em português, numa palavra.", "Diz apenas: pronto")
            report(True, f"chamada de teste ao LLM devolveu: {out.strip()[:60]!r}")
        except Exception as e:
            report(False, f"chamada de teste ao LLM falhou: {e}")
        if args.vision and os.getenv("LLM_VISION_MODEL", "none").lower() != "none":
            try:
                from pvd.llm import ask, get_llm
                image = config.FIG / "p2f2_bar_zero.png"
                out = ask(get_llm(vision=True),
                          "Analisa graficos. Devolve JSON com approved (boolean) e feedback (texto).",
                          "Verifica legibilidade e se o eixo quantitativo da figura comeca em zero.",
                          image_path=str(image))
                report(True, f"resposta do critico visual: {out.strip()[:100]!r}")
            except Exception as e:
                report(False, f"chamada de teste visual falhou: {e}")

print("\nTudo pronto: python run_all.py --only p2f2_bar_zero" if not bad else f"\n{bad} problema(s) a resolver acima.")
sys.exit(1 if bad else 0)
