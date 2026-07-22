"""
CLI de procesamiento por lotes. Automatiza el caso de uso real: apuntar a una
carpeta con muchos comprobantes y obtener, de una, qué se auto-aprueba, qué
necesita revisión humana y qué hay que reprocesar — más un JSON con el detalle.

Uso:
    python -m factura_ai.cli data/samples
    python -m factura_ai.cli data/samples --json salida.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .domain.models import Decision
from .pipeline import procesar_archivos

_ETIQUETA = {
    Decision.AUTO_APROBAR: "AUTO-APROBADA",
    Decision.REVISAR: "A REVISION",
    Decision.RECHAZAR: "RECHAZADA",
}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="factura-ai",
        description="Procesa comprobantes en lote y decide su destino.",
    )
    p.add_argument("carpeta", help="Carpeta con archivos .txt de comprobantes.")
    p.add_argument("--json", metavar="RUTA", dest="json_path",
                   help="Guarda el detalle de resultados en un JSON.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    carpeta = Path(args.carpeta)
    if not carpeta.is_dir():
        print(f"Error: '{carpeta}' no es una carpeta", file=sys.stderr)
        return 1

    rutas = sorted(carpeta.glob("*.txt"))
    if not rutas:
        print(f"No se encontraron archivos .txt en '{carpeta}'", file=sys.stderr)
        return 1

    resultados = procesar_archivos(rutas)

    print(f"\n== Procesadas {len(resultados)} facturas ==\n")
    conteo = {d: 0 for d in Decision}
    for r in resultados:
        conteo[r.decision] += 1
        print(f"  [{_ETIQUETA[r.decision]:>13}]  {r.fuente:<32} "
              f"confianza {r.confianza:5.1f}  ({r.extractor})")
        for issue in r.issues:
            print(f"        - {issue.severidad.value}: {issue.mensaje}")

    print("\n  Resumen:")
    print(f"    Auto-aprobadas : {conteo[Decision.AUTO_APROBAR]}")
    print(f"    A revision     : {conteo[Decision.REVISAR]}")
    print(f"    Rechazadas     : {conteo[Decision.RECHAZAR]}")
    tasa = 100 * conteo[Decision.AUTO_APROBAR] / len(resultados)
    print(f"    Automatizacion : {tasa:.0f}% sin intervencion humana\n")

    if args.json_path:
        payload = [r.model_dump(mode="json") for r in resultados]
        Path(args.json_path).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"  Detalle guardado en: {args.json_path}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
