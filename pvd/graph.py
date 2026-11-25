"""Sistema multiagente em LangGraph com tres papeis explicitos:
planeamento visual -> escrita de codigo -> critica visual.

 START -> chart_design_agent -> code_agent -> validate -> execute -> visual_critic_agent -> finish
                                      ^                         |
                                      +----- feedback/retry -----+

The validator and executor are deterministic support nodes, not LLM agents.
The categorical selector supplies a specialized geometry decision to the chart-design role.
"""
import json
from typing import TypedDict

from langgraph.graph import END, StateGraph

from pvd import llm as L
from pvd.config import FIG, LOGS, MAX_ITER, TEMPLATES
from pvd.executor import execute
from pvd.validators import run_validators

GEN_SYSTEM = """És um engenheiro de visualização de dados. Escreves scripts Python (pandas, matplotlib, seaborn) que seguem
Fundamentals of Data Visualization (Wilke). Regras do ambiente: as variáveis DATA_PATH, OUT_PATH, PARAMS e META já estão
definidas; usa `from pvd import utils` (utils.load, utils.save, ...); guarda SEMPRE a figura com utils.save(fig, OUT_PATH).
Regras visuais obrigatórias: paleta qualitativa só para categorias (ex.: 'colorblind'), sequencial ('viridis') ou divergente
('coolwarm' com TwoSlopeNorm) para contínuos, nunca arco-íris; barras com eixo métrico a começar em 0; sem escala log em barras;
títulos e eixos com unidades. Responde APENAS com o script completo num único bloco ```python."""

DESIGN_SYSTEM = """Es um agente de planeamento de visualizacao (Wilke). Propoe um plano curto para a figura, sem escrever codigo.
Nao alteres as medidas, filtros, categorias ou objetivo fornecidos. Responde APENAS com JSON:
{"chart_type":"...", "encodings":"...", "scale":"...", "palette":"...", "rationale":"..."}.
O tipo de grafico deve ser compativel com o template fornecido. Usa escala linear salvo se a comparacao de ordens de grandeza justificar log.
Usa paleta qualitativa para categorias, sequencial para magnitude e divergente centrada em zero para diferencas.
"""

CRIT_SYSTEM = """Es um agente critico de visualizacao de dados (Wilke). Avalias a imagem recebida: legibilidade de rotulos, sobreposicao,
escalas e eixos, adequação da cor, título/unidades, proporcionalidade. Responde APENAS com JSON:
{"approved": true|false, "feedback": "correções concretas e curtas"}. Só rejeites por problemas reais."""


class State(TypedDict, total=False):
    spec: dict
    design_plan: dict
    code: str
    issues: list
    error: str
    image: str
    critique: str
    approved: bool
    iteration: int
    status: str
    history: list


def read_template(name: str) -> str:
    return (TEMPLATES / f"{name}.py").read_text(encoding="utf-8")


def _log(state, **kw):
    return (state.get("history") or []) + [{"iteration": state.get("iteration", 0), **kw}]


def build_graph(llm=None, vision_llm=None):
    # ---------------- nós ----------------
    def chart_design_agent(state: State):
        spec = state["spec"]
        plan = {
            "chart_type": spec.get("template", "template deterministico"),
            "encodings": spec.get("desc", ""),
            "scale": "linear por omissao; justificar escala log ou divergente",
            "palette": "adequada ao tipo de variavel; evitar arco-iris",
            "rationale": "plano inicial baseado na especificacao e no template do projeto",
            "source": "rule",
        }
        if llm is not None:
            prompt = (f"Especificacao da figura: {spec.get('desc', '')}\n"
                      f"Template/geometria ja escolhido: {spec.get('template', '')}\n"
                      f"Parametros (nao alterar): {spec.get('params', {})}\n"
                      f"Plano atual: {json.dumps(plan, ensure_ascii=False)}\n"
                      "Refina tipo, codificacao, escala e paleta, sem mudar medidas nem filtros.")
            try:
                proposed = L.extract_json(L.ask(llm, DESIGN_SYSTEM, prompt))
                required = {"chart_type", "encodings", "scale", "palette", "rationale"}
                if proposed and required <= proposed.keys():
                    # A geometria definida pelo seletor/template e vinculativa.
                    proposed["chart_type"] = plan["chart_type"]
                    plan = {**proposed, "source": "ollama"}
            except Exception as e:
                plan["rationale"] += f"; agente de planeamento indisponivel: {e}"
        return {"design_plan": plan, "history": _log(state, node="chart_design_agent", plan=plan)}

    def code_agent(state: State):
        spec, it = state["spec"], state.get("iteration", 0)
        code_source, generation_note = "template", ""
        if llm is None:  # modo offline determinístico
            naive = spec.get("naive_template")
            code = read_template(naive if (naive and it == 0) else spec["template"])
        else:
            base = state.get("code") or read_template(spec["template"])
            feedback = []
            if state.get("issues"):
                feedback.append("PROBLEMAS DETETADOS PELO VALIDADOR (corrigir todos):\n- " + "\n- ".join(state["issues"]))
            if state.get("error"):
                feedback.append("ERRO DE EXECUÇÃO:\n" + state["error"])
            if state.get("critique"):
                feedback.append("CRÍTICA VISUAL:\n" + state["critique"])
            user = (f"Objetivo da figura: {spec['desc']}\n"
                    f"PLANO DO AGENTE DE VISUALIZACAO={json.dumps(state.get('design_plan', {}), ensure_ascii=False)}\n"
                    f"PARAMS={spec.get('params', {})}\nMETA keys={list(spec.get('meta', {}))}\n"
                    f"Código base:\n```python\n{base}\n```\n" + "\n\n".join(feedback) +
                    "\nDevolve o script completo (corrigido, se houver feedback).")
            try:
                candidate = L.extract_code(L.ask(llm, GEN_SYSTEM, user))
                if candidate:
                    code, code_source = candidate, "ollama"
                else:
                    code, code_source = base, "template_fallback"
                    generation_note = "Ollama nao devolveu um bloco de codigo interpretavel."
            except Exception as e:  # falha de rede/quota: mantém-se o código base e regista o fallback
                code = base
                code_source = "template_fallback"
                generation_note = f"Falha do agente de codigo: {e}"
        return {"code": code, "iteration": it + 1, "issues": [], "error": "", "critique": "", "approved": False,
                "history": _log(state, node="code_agent", source=code_source, note=generation_note)}

    def validate(state: State):
        issues = run_validators(state["code"])
        return {"issues": issues, "history": _log(state, node="validate", issues=issues)}

    def run(state: State):
        out = FIG / f"{state['spec']['id']}.png"
        ok, err = execute(state["code"], state["spec"], out)
        return {"error": err, "image": str(out) if ok else "", "history": _log(state, node="execute", ok=ok, error=err[-300:])}

    def visual_critic_agent(state: State):
        approved, fb = True, ""
        img = state["image"]
        mode = "heuristic"
        if vision_llm is not None:
            mode = "vision"
            try:
                out = L.ask(vision_llm, CRIT_SYSTEM, f"Figura pretendida: {state['spec']['desc']}", image_path=img)
                j = L.extract_json(out)
                if j is None or "approved" not in j:
                    approved, fb = False, "Resposta do agente visual sem JSON valido; pedir nova revisao."
                else:
                    approved, fb = bool(j["approved"]), str(j.get("feedback", ""))
            except Exception as e:
                mode = "heuristic_fallback"
                fb = f"Agente visual indisponivel; aplicada verificacao heuristica ({e})."
        if mode in {"heuristic", "heuristic_fallback"}:
            import numpy as np
            from PIL import Image
            a = np.asarray(Image.open(img).convert("L"), float)
            if min(a.shape) < 600:
                approved, fb = False, "Resolução demasiado baixa (<600 px)."
            elif a.std() < 5 and not fb:
                approved, fb = False, "Figura praticamente em branco."
        return {"approved": approved, "critique": fb,
                "history": _log(state, node="visual_critic_agent",
                                mode=mode,
                                approved=approved, feedback=fb)}

    def finish_ok(state: State):
        return {"status": "ok"}

    def finish_fail(state: State):
        return {"status": "max_iterations" if state.get("image") else "failed"}

    # ---------------- arestas condicionais ----------------
    def exhausted(state):
        return state.get("iteration", 0) >= MAX_ITER

    def after_validate(state):
        if state["issues"]:
            return "fail" if exhausted(state) else "retry"
        return "execute"

    def after_execute(state):
        if state["error"]:
            return "fail" if exhausted(state) else "retry"
        return "critique"

    def after_critique(state):
        if state["approved"]:
            return "ok"
        return "fail" if exhausted(state) else "retry"

    g = StateGraph(State)
    for name, fn in [("chart_design_agent", chart_design_agent), ("code_agent", code_agent), ("validate", validate),
                     ("execute", run), ("visual_critic_agent", visual_critic_agent),
                     ("finish_ok", finish_ok), ("finish_fail", finish_fail)]:
        g.add_node(name, fn)
    g.set_entry_point("chart_design_agent")
    g.add_edge("chart_design_agent", "code_agent")
    g.add_edge("code_agent", "validate")
    g.add_conditional_edges("validate", after_validate, {"retry": "code_agent", "execute": "execute", "fail": "finish_fail"})
    g.add_conditional_edges("execute", after_execute, {"retry": "code_agent", "critique": "visual_critic_agent", "fail": "finish_fail"})
    g.add_conditional_edges("visual_critic_agent", after_critique,
                            {"retry": "code_agent", "ok": "finish_ok", "fail": "finish_fail"})
    g.add_edge("finish_ok", END)
    g.add_edge("finish_fail", END)
    return g.compile()


def run_figure(spec: dict, llm=None, vision_llm=None) -> dict:
    """Corre o grafo para uma figura e guarda o histórico em logs/<id>.json."""
    final = build_graph(llm, vision_llm).invoke({"spec": spec, "iteration": 0, "history": [],
                                                  "design_plan": {}},
                                                {"recursion_limit": 8 * MAX_ITER + 10})
    (LOGS / f"{spec['id']}.json").write_text(json.dumps(
        {"id": spec["id"], "status": final.get("status"), "iterations": final.get("iteration"),
         "history": final.get("history"), "final_issues": final.get("issues")}, indent=2, ensure_ascii=False))
    return final
