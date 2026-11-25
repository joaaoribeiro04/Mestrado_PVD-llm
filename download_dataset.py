#!/usr/bin/env python
"""Download the E-REDES public tariff-period consumption dataset (CC BY 4.0)."""
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "raw" / "consumos_faturados_por_periodo_tarifario.csv"
URL = (
    "https://e-redes.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
    "consumos-faturados-por-periodo-tarifario/exports/csv"
    "?delimiter=%3B&with_bom=false"
)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUT.with_suffix(OUT.suffix + ".part")
    req = Request(URL, headers={"User-Agent": "MEI-PVD-educational-project/1.0"})
    try:
        with urlopen(req, timeout=90) as response, temp.open("wb") as dst:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status} ao obter o CSV")
            while chunk := response.read(1024 * 1024):
                dst.write(chunk)
        if temp.stat().st_size < 1000:
            raise RuntimeError("A resposta do portal nao parece ser um CSV completo")
        temp.replace(OUT)
    except Exception:
        temp.unlink(missing_ok=True)
        raise
    print(f"CSV guardado: {OUT} ({OUT.stat().st_size:,} bytes)")
    print("Fonte: E-REDES Open Data Portal; licenca CC BY 4.0.")


if __name__ == "__main__":
    main()
