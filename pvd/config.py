"""Caminhos e constantes globais do projeto."""
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
except ImportError:  # python-dotenv é opcional
    pass

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "consumos_faturados_por_periodo_tarifario.csv"
PROC = ROOT / "data" / "processed" / "consumo.csv"
FIG = ROOT / "figures"
LOGS = ROOT / "logs"
TEMPLATES = ROOT / "pvd" / "templates"

MAX_ITER = 4         # limite de ciclos gerar -> validar -> executar -> criticar
EXEC_TIMEOUT = 180   # segundos por execução de código gerado

for _p in (RAW.parent, PROC.parent, FIG, FIG / "code", LOGS):
    _p.mkdir(parents=True, exist_ok=True)
