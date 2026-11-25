from pvd import cvd, utils
import matplotlib.pyplot as plt
from pathlib import Path
import json, csv
# Teste de conformidade CVD: (1) paletas usadas no projeto (+ contra-exemplos) e (2) figuras finais simuladas.
utils.apply_style()
pals = PARAMS["palettes"]
rows, res = [], []
fig, axs = plt.subplots(len(pals), len(cvd.MODES), figsize=(11, 0.95 * len(pals) + 1.2))
for i, (name, kind) in enumerate(pals):
    r = cvd.check_categorical(name, 5) if kind == "categorical" else cvd.check_continuous(name, kind == "diverging")
    cols = cvd.palette_colors(name, 5 if kind == "categorical" else 64)
    for j, m in enumerate(cvd.MODES):
        ax = axs[i, j]
        ax.imshow(cvd.simulate(cols, m)[None], aspect="auto"); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_visible(False)
        if i == 0: ax.set_title(m, fontsize=10)
        if j == 0: ax.set_ylabel(f"{name}\n{'OK' if r['pass'] else 'FALHA'}", rotation=0, ha="right", va="center", fontsize=9,
                                  color="#1a7f37" if r["pass"] else "#b42318")
    rows.append({"palette": name, "kind": kind, "pass": r["pass"], **{k: round(v, 1) for k, v in (r.get("min_dE") or r["ends_dE"]).items()}})
fig.suptitle("Teste de daltonismo das paletas (ΔE mínimo entre cores / extremos)", fontsize=12, fontweight="bold")
fig.tight_layout(); utils.save(fig, OUT_PATH)
out = Path(OUT_PATH).parent
with open(out / "cvd_report.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
for img in PARAMS.get("images", []):
    p = out / img
    if p.exists():
        cvd.image_triptych(p, out / f"{p.stem}_cvd.png")
