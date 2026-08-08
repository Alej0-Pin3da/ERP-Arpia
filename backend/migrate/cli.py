"""Migration CLI (PR#1: infra + loader + normalize).

Usage (from ``backend/``):

    python -m migrate.cli --fase 0 --dry-run
    python -m migrate.cli --all --dry-run --source ../ARPIA.xlsx

Flags (design #423 / tasks #424):
    --source PATH      excel path (default: resolver ../ARPIA.xlsx from backend/)
    --dry-run          default mode: load + parse + validate + report, 0 writes
    --commit           actually persist (PR slices later add the write logic)
    --fase N           run a single phase F0..F7
    --all              run every phase in strict order
    --force            allow re-run even when a phase marker exists
    --canal STR        default canal_venta for sales phase (configurable; None)

Exit code: 0 on success, 1 if the report accumulated ERROR entries.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from migrate import FASES, get_fase
from migrate.context import FaseOptions
from migrate.loaders import LibroMigracion, SHEET_BOUNDS
from migrate.report import Report

_DEFAULT_SOURCE = Path(__file__).resolve().parents[2] / "ARPIA.xlsx"
_EXTRA_MSG = (
    "Las fases de negocio (catalogo, compras, BOM, stock, ventas, finanzas, "
    "validacion) se implementan en slices posteriores; este slice (PR #1) "
    "solo registra la infraestructura: loader, normalizador, reporte y CLI."
)


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="migrate.cli",
        description="Pipeline de migracion historica ARPIA.xlsx -> ERP Arpia (dry-run por defecto).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=_DEFAULT_SOURCE,
        help=f"Ruta del workbook (default: {_DEFAULT_SOURCE})",
    )
    modo = parser.add_mutually_exclusive_group()
    modo.add_argument(
        "--dry-run",
        dest="modo",
        action="store_const",
        const="dry-run",
        default="dry-run",
        help="Solo leer/parsear/reportar; cero escrituras (default).",
    )
    modo.add_argument(
        "--commit",
        dest="modo",
        action="store_const",
        const="commit",
        help="Persistir en DB (requiere implementacion de fase).",
    )
    seleccion = parser.add_mutually_exclusive_group()
    seleccion.add_argument(
        "--fase", type=str, metavar="N",
        help="Fase a ejecutar: F0..F7 (ej. '0' o 'F0').",
    )
    seleccion.add_argument(
        "--all",
        dest="todas",
        action="store_true",
        help="Ejecutar las 8 fases en orden estricto.",
    )
    parser.add_argument("--force", action="store_true", help="Re-run aunque haya marker.")
    parser.add_argument("--canal", default=None, help="canal_venta para fase de ventas.")
    return parser


def _normalizar_fase(arg: str) -> str:
    return arg if arg.upper().startswith("F") else f"F{arg}"


def _fases_a_correr(args) -> list[str]:
    if args.todas:
        return [f.id for f in FASES]
    if args.fase:
        return [_normalizar_fase(args.fase)]
    # Ninguno -> default: correr todas (dry-run plan) como --all.
    return [f.id for f in FASES]


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    options = FaseOptions(
        source=args.source,
        modo=args.modo,
        fuerza=args.force,
        canal_venta=args.canal,
    )

    report = Report(fase="cli", modo=args.modo)

    if not args.source.exists():
        report.error("", None, None, f"archivo fuente no encontrado: {args.source}")
        _emitir(report)
        return 1

    # Infra step: bounded read of the workbook (dry-run only writes nothing).
    with LibroMigracion(args.source) as libro:
        report.info("", None, None, f"workbook leido: {args.source.name} ({len(libro.hojas)} hojas)")
        for hoja in libro.hojas:
            if hoja in SHEET_BOUNDS:
                lect = libro.leer_hoja(hoja, report=report)
                report.info(hoja, None, None,
                            f"{len(lect.filas)} filas de datos (descartadas={lect.descartadas}, "
                            f"omitidas={lect.omitidas})")
            else:
                report.warn(hoja, None, None, "hoja sin bounds registrados; no leida")

    fases = _fases_a_correr(args)
    for fid in fases:
        fase = get_fase(fid)
        report.info(fid, None, None, f"{fase.nombre}: pendiente de implementacion (slice posterior) - 0 escrituras")

    report.info("", None, None, _EXTRA_MSG)

    _emitir(report)
    return 1 if report.tiene_errores else 0


def _emitir(report: Report) -> None:
    for linea in report.resumen_lineas():
        print(linea)
    try:
        ruta = report.write()
        print(f"Reporte: {ruta}")
    except Exception as exc:  # pragma: no cover - filesystem edge
        print(f"AVISO: no se pudo escribir el reporte JSON: {exc}")


if __name__ == "__main__":
    sys.exit(main())