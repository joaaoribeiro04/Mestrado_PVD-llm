"""Isolated execution of generated figure code with a time limit."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from pvd.config import EXEC_TIMEOUT, FIG, ROOT

HEADER = (
    "import matplotlib\nmatplotlib.use('Agg')\n"
    "from pathlib import Path\n"
    "import sys\n"
    "ROOT = Path.cwd()\n"
    "sys.path.insert(0, str(ROOT))\n"
    "DATA_PATH = str(ROOT / 'data' / 'processed' / 'consumo.csv')\n"
    "OUT_PATH = str(ROOT / 'figures' / {filename!r})\n"
    "PARAMS = {params!r}\nMETA = {meta!r}\n"
)


def build_script(code: str, spec: dict, out_path: Path) -> str:
    return HEADER.format(filename=out_path.name, params=spec.get("params", {}),
                         meta=spec.get("meta", {})) + "\n" + code


def execute(code: str, spec: dict, out_path: Path) -> tuple[bool, str]:
    """Return (success, error message); never raise execution exceptions."""
    script = build_script(code, spec, out_path)
    if out_path.exists():
        out_path.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "fig.py"
        f.write_text(script, encoding="utf-8")
        env = {**os.environ, "MPLBACKEND": "Agg", "PYTHONPATH": str(ROOT)}
        try:
            result = subprocess.run([sys.executable, str(f)], capture_output=True, text=True,
                                    timeout=EXEC_TIMEOUT, cwd=ROOT, env=env)
        except subprocess.TimeoutExpired:
            return False, f"Timeout ({EXEC_TIMEOUT}s) while executing generated code."
    if result.returncode != 0:
        return False, result.stderr[-1500:]
    if not out_path.exists():
        return False, "Script exited without saving a figure to OUT_PATH."
    (FIG / "code" / f"{out_path.stem}.py").write_text(script, encoding="utf-8")
    return True, ""
