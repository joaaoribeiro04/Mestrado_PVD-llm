"""Regras de integridade visual aplicadas ao CÓDIGO gerado (análise estática).

 - [COR]          adequação da escala de cor à natureza dos dados  (Wilke, caps. 4 e 19; Parte I Fase 1)
 - [INTEGRIDADE]  barras com eixo métrico a começar em zero         (Wilke, cap. 17;     Parte II Fase 2)
 - [DALTONISMO]   paletas categóricas/contínuas testadas sob CVD    (Wilke, cap. 19;     Parte II Fase 2)

Cada função devolve uma lista de problemas (strings acionáveis, usadas como feedback
para o agente gerador). Lista vazia = código aceite.
"""
import ast
import re

from pvd import cvd

SEQ = {"viridis", "magma", "inferno", "plasma", "cividis", "Blues", "Greens", "Oranges", "Purples", "Reds",
       "Greys", "YlGnBu", "YlOrRd", "rocket", "mako", "crest", "flare"}
DIV = {"coolwarm", "RdBu", "PuOr", "BrBG", "RdYlBu", "Spectral", "vlag", "icefire", "PiYG", "bwr", "seismic"}
BAD = {"jet", "rainbow", "hsv", "gist_rainbow", "nipy_spectral", "prism", "flag", "gist_ncar", "turbo"}
KW_RE = re.compile(r"\b(palette|cmap|color_palette|get_cmap)\s*(?:=|\()\s*[\"'](\w+)[\"']")
# papel semântico de cada argumento -> tipos de dados aceitáveis
EXPECTED = {"palette": {"categorical"}, "color_palette": {"categorical"},
            "cmap": {"continuous", "diverging"}, "get_cmap": {"continuous", "diverging"}}


def _kind(name):
    base = name[:-2] if name.endswith("_r") else name
    if base in cvd.QUALITATIVE:
        return "categorical"
    if base in SEQ:
        return "continuous"
    if base in DIV:
        return "diverging"
    return "unknown"


def audit_color(code: str) -> list[str]:
    issues = []
    for kw, name in KW_RE.findall(code):
        base = name[:-2] if name.endswith("_r") else name
        kind = _kind(name)
        if base in BAD:
            issues.append(f"[COR] '{name}' é uma escala arco-íris/não perceptual; usar 'viridis' (contínua), "
                          f"'coolwarm' (divergente) ou 'colorblind' (categórica).")
        elif kind == "unknown":
            issues.append(f"[COR] paleta '{name}' desconhecida; não é possível validar a adequação ao tipo de dados.")
        elif kind not in EXPECTED[kw]:
            issues.append(f"[COR] '{name}' é {kind} mas é usada em '{kw}', que exige {sorted(EXPECTED[kw])}.")
    if any(_kind(n) == "diverging" for _, n in KW_RE.findall(code)) and not re.search(
            r"TwoSlopeNorm|CenteredNorm|vcenter|center\s*=", code):
        issues.append("[COR] escala divergente sem ponto médio explícito; usar TwoSlopeNorm(vcenter=0) ou center=0.")
    return issues


def _num(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) and isinstance(node.operand, ast.Constant):
        return -node.operand.value
    return None


def audit_bar_zero(code: str) -> list[str]:
    """Só avalia os EIXOS que contêm barras e apenas o eixo métrico:
    ax.bar -> y; ax.barh -> x; sns.barplot/countplot (ax=...) -> ambos (orientação não determinável)."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return [f"[INTEGRIDADE] erro de sintaxe: {e}"]
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
    fn = lambda c: c.func.attr if isinstance(c.func, ast.Attribute) else getattr(c.func, "id", "")

    def recv(c):
        if isinstance(c.func, ast.Attribute) and isinstance(c.func.value, ast.Name):
            if c.func.value.id in {"sns", "seaborn"}:  # seaborn: eixo vem em ax=...
                kw = next((k.value for k in c.keywords if k.arg == "ax"), None)
                return kw.id if isinstance(kw, ast.Name) else "plt"
            return c.func.value.id
        return "plt"

    bars = {}  # eixo -> conjunto de eixos métricos
    for c in calls:
        n = fn(c)
        if n == "bar":
            bars.setdefault(recv(c), set()).add("y")
        elif n == "barh":
            bars.setdefault(recv(c), set()).add("x")
        elif n in {"barplot", "countplot"}:
            bars.setdefault(recv(c), set()).update({"x", "y"})
    issues = []
    for c in calls:
        name, r = fn(c), recv(c)
        axis = "y" if name.endswith(("ylim", "yscale")) else "x" if name.endswith(("xlim", "xscale")) else None
        if axis is None or axis not in bars.get(r, set()):
            continue
        if "lim" in name:
            lower = c.args[0] if c.args else next((k.value for k in c.keywords
                                                   if k.arg in {"bottom", "left", "ymin", "xmin"}), None)
            v = _num(lower) if lower is not None else 0
            if v is None or v != 0:
                issues.append(f"[INTEGRIDADE] {name} com limite inferior {'não nulo' if v is not None else 'não literal'}"
                              f" num gráfico de barras: o eixo métrico tem de começar em 0 (Wilke, cap. 17). "
                              f"Usar {name}(0, <máximo>).")
        elif c.args and isinstance(c.args[0], ast.Constant) and c.args[0].value == "log":
            issues.append("[INTEGRIDADE] escala logarítmica em barras: o comprimento deixa de ser proporcional ao valor; "
                          "usar dot plot ou escala linear.")
    return issues


def audit_cvd(code: str, n_categories: int = 5) -> list[str]:
    issues = []
    for kw, name in KW_RE.findall(code):
        kind = _kind(name)
        if kind == "categorical":
            r = cvd.check_categorical(name, n_categories)
            if not r["pass"]:
                worst = min(r["min_dE"], key=r["min_dE"].get)
                issues.append(f"[DALTONISMO] paleta '{name}' falha: ΔE mínimo {r['min_dE'][worst]:.1f} < "
                              f"{r['threshold']} em {worst}. Usar 'colorblind'.")
        elif kind in {"continuous", "diverging"}:
            r = cvd.check_continuous(name, diverging=(kind == "diverging"))
            if not r["pass"]:
                issues.append(f"[DALTONISMO] escala '{name}' não passa o teste CVD; usar "
                              f"{'coolwarm' if kind == 'diverging' else 'viridis/cividis'}.")
    return issues


RULES = {"color": audit_color, "bar_zero": audit_bar_zero, "cvd": audit_cvd}


def run_validators(code: str, rules=("color", "bar_zero", "cvd")) -> list[str]:
    issues = []
    for r in rules:
        issues += RULES[r](code)
    return issues
