"""Migration CLI for the historical ARPIA.xlsx -> ERP Arpia pipeline.

Usage (from ``backend/``):

    python -m migrate.cli --fase 1 --dry-run
    python -m migrate.cli --fase 1 --commit
    python -m migrate.cli --all --dry-run

Flags (design #423 / tasks #424):
    --source PATH   excel path (default: resolver ../ARPIA.xlsx desde backend/)
    --dry-run       default: plan + reporte, 0 escrituras
    --commit        persistir (fases implementadas)
    --fase N        correr una sola fase F0..F7
    --all           correr todas las fases en orden estricto
    --force         permitir re-run (reservado)
    --canal STR     canal_venta por defecto para la fase F5 (reservado)

Exit code: 0 si no hubo ERRORes, 1 en caso contrario.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from migrate import FASES, FASE_RUNNERS, get_fase
from migrate.context import FaseOptions, MigrationContext
from migrate.loaders import HojaInexistenteError, LibroMigracion, SHEET_BOUNDS
from migrate.report import Report

_DEFAULT_SOURCE = Path(__file__).resolve().parents[2] / "ARPIA.xlsx"


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="migrate.cli",
        description="Pipeline migracion historica ARPIA.xlsx -> ERP Arpia (dry-run por defecto).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=_DEFAULT_SOURCE,
        help="Ruta del workbook (default: ../ARPIA.xlsx desde backend/).",
    )
    parser.add_argument(
        "--modo",
        choices=["dry-run", "commit"],
        default="dry-run",
        help="dry-run (default): plan + reporte, 0 escrituras. commit: persiste.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_const",
        const="dry-run",
        dest="modo",
        help="Modo dry-run (default): plan y reporte sin escrituras.",
    )
    parser.add_argument(
        "--commit",
        action="store_const",
        const="commit",
        dest="modo",
        help="Persistir las escrituras de la fase (requiere DB reachable).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Repetir la fase aunque exista marker (reservado).",
    )
    parser.add_argument(
        "--canal",
        dest="canal",
        help="Canal de venta por defecto para la fase ventas (reservado).",
    )
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument(
        "--fase",
        type=str,
        help="Ejecutar una sola fase (F0..F7).",
    )
    grupo.add_argument(
        "--all",
        dest="todas",
        action="store_true",
        help="Ejecutar todas las fases en orden estricto.",
    )
    return parser


def _normalizar_fase(value: str) -> str:
    """Acepta '0' o 'F0' (cualquier case) -> canonical F0..F7."""
    value = value.strip().upper()
    if value.isdigit():
        return f"F{int(value)}"
    return value


def _fases_a_correr(args) -> list[str]:
    if getattr(args, "todas", False):
        return [f.id for f in FASES]
    if getattr(args, "fase", None):
        return [_normalizar_fase(args.fase)]
    return [f.id for f in FASES]


def _emitir(report: Report) -> int:
    """Print the report entries + summary; 0 if no ERROR, else 1."""
    for entry in report.entradas:
        ubicacion = entry.hoja or ""
        if entry.fila is not None:
            ubicacion = f"{ubicacion}:{entry.fila}"
        prefix = f"[{entry.nivel}]" + (f" [{ubicacion}]" if ubicacion else "")
        print(prefix, entry.mensaje)
    errores = sum(1 for e in report.entradas if e.nivel == "ERROR")
    print(f"\nResumen: {len(report.entradas)} entradas, {errores} errores")
    return 1 if errores else 0


def main() -> None:
    args = construir_parser().parse_args()
    options = FaseOptions(
        source=args.source,
        modo=args.modo,
        fuerza=getattr(args, "force", False),
        canal_venta=getattr(args, "canal", None),
    )
    fases = _fases_a_correr(args)
    report = Report(fase="+".join(fases), modo=args.modo)

    # Infra: bounded read of every registered sheet (report WARN/INFO).
    try:
        with LibroMigracion(options.source) as libro:
            for hoja in SHEET_BOUNDS:
                try:
                    libro.leer_hoja(hoja, report=report)
                except HojaInexistenteError:
                    report.warn(hoja, None, None, "hoja no presente en el workbook; omitida")
    except FileNotFoundError as exc:
        report.error("source", None, None, f"workbook no encontrado: {exc}")
    except Exception as exc:
        report.error("source", None, None, f"error abriendo workbook: {exc}")

    # Phases.
    for fase_id in fases:
        fase = get_fase(fase_id)
        runner = FASE_RUNNERS.get(fase_id)
        if runner is None:
            report.info(fase_id, None, None, f"{fase.nombre}: pendiente de implementacion")
            continue
        report.info(fase_id, None, None, f"{fase.nombre}: iniciando ({options.modo})")
        try:
            if options.modo == "commit":
                from app.db.session import SessionLocal  # lazy: solo en commit

                db = SessionLocal()
                try:
                    runner(MigrationContext.para_fase(options, fase_id).con_session(db))
                finally:
                    db.close()
            else:
                runner(MigrationContext.para_fase(options, fase_id))
            report.info(fase_id, None, None, f"{fase.nombre}: OK ({options.modo})")
        except Exception as exc:
            report.error(fase_id, None, None, f"{fase.nombre}: {type(exc).__name__}: {exc}")

    sys.exit(_emitir(report))


if __name__ == "__main__":
    main()