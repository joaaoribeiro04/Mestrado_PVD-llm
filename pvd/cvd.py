"""Simulação de daltonismo (Machado et al., 2009, severidade 1.0) e testes de paletas.

Testa distinguibilidade com ΔE (CIE76, em Lab) entre cores sob deuteranopia,
protanopia e tritanopia — Wilke, cap. 19 (Color-vision deficiency).
"""
import numpy as np
import matplotlib as mpl
import seaborn as sns

MACHADO = {
    "deuteranopia": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
    "protanopia": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    "tritanopia": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]),
}
MODES = ["normal"] + list(MACHADO)
QUALITATIVE = {"Set1", "Set2", "Set3", "Dark2", "Paired", "Accent", "tab10", "tab20", "colorblind", "deep",
               "muted", "pastel", "bright", "dark", "Pastel1", "Pastel2"}


def _lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _gam(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def simulate(rgb, mode):
    """rgb: (..., 3) em [0,1]."""
    rgb = np.asarray(rgb, float)
    if mode == "normal":
        return rgb
    return _gam(_lin(rgb) @ MACHADO[mode].T)


def to_lab(rgb):
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    xyz = (_lin(np.asarray(rgb, float)) @ M.T) / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def palette_colors(name, n=6):
    if name in QUALITATIVE:
        return np.array(sns.color_palette(name, n))
    return np.asarray(mpl.colormaps[name](np.linspace(0, 1, n)))[:, :3]


def min_delta_e(colors, mode):
    lab = to_lab(simulate(colors, mode))
    d = np.linalg.norm(lab[:, None] - lab[None], axis=-1)
    return float(d[np.triu_indices(len(colors), 1)].min())


def check_categorical(name, n=5, threshold=12.0):
    res = {m: min_delta_e(palette_colors(name, n), m) for m in MODES}
    return {"palette": name, "n": n, "min_dE": res, "pass": all(v >= threshold for v in res.values()),
            "threshold": threshold}


def check_continuous(name, diverging=False, threshold=40.0):
    """Extremos distinguíveis sob CVD; sequenciais: luminosidade monótona."""
    c = palette_colors(name, 64)
    res, mono = {}, True
    for m in MODES:
        lab = to_lab(simulate(c, m))
        res[m] = float(np.linalg.norm(lab[0] - lab[-1]))
        if not diverging:
            dl = np.diff(lab[:, 0])
            mono &= bool((dl >= -0.5).all() or (dl <= 0.5).all())
    ok = all(v >= threshold for v in res.values()) and (diverging or mono)
    return {"palette": name, "ends_dE": res, "monotonic_lightness": mono, "pass": ok}


def image_triptych(src, out, modes=tuple(MODES)):
    """Aplica a simulação à imagem final (teste de conformidade da figura inteira)."""
    import matplotlib.pyplot as plt
    from PIL import Image
    img = np.asarray(Image.open(src).convert("RGB")) / 255.0
    fig, axs = plt.subplots(1, len(modes), figsize=(5 * len(modes), 4.2))
    for ax, m in zip(axs, modes):
        ax.imshow(simulate(img, m)); ax.set_title(m, fontsize=11); ax.axis("off")
    fig.tight_layout(); fig.savefig(out, dpi=130, facecolor="white"); plt.close(fig)
