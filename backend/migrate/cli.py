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
    --reports-dir   directorio de la traza JSON (EXM-6; default migrate/reports)

Exit code: 0 si no hubo ERRORes, 1 en caso contrario.

Traceability (EXM-6): every run persists a JSON trace under reports/ with the
executed phases, counts per phase, all INFO/ERROR/WARN entries, a timestamp
and a content hash (drift/re-run detection). Per-phase runner reports are
integrated into the run report and printed to stdout (NFR-2).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from migrate import FASE_RUNNERS, FASES, get_fase
from migrate.context import FaseOptions, MigrationContext
from migrate.loaders import SHEET_BOUNDS, HojaInexistenteError, LibroMigracion
from migrate.report import LEVEL_ERROR, NIVELES, Report

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
    parser.add_argument(
        "--reports-dir",
        type=Path,
        default=None,
        help="Directorio de la traza JSON (default: backend/migrate/reports).",
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


def _emitir_entradas(entradas) -> None:
    """Print INFO/ERROR/WARN entries to stdout, plain ASCII (NFR-2)."""
    for entry in entradas:
        ubicacion = entry.hoja or ""
        if entry.fila is not None:
            ubicacion = f"{ubicacion}:{entry.fila}"
        prefix = f"[{entry.nivel}]" + (f" [{ubicacion}]" if ubicacion else "")
        print(prefix, entry.mensaje)


def ejecutar(
    options: FaseOptions,
    fases: list[str],
    reports_dir: Path | str | None = None,
) -> int:
    """Run infra + phases, integrating each runner's internal report (NFR-2)
    and persisting a run-level traceability JSON (EXM-6). Returns exit code
    (1 if any ERROR was reported)."""

    run_report = Report(fase="+".join(fases), modo=options.modo)
    run_report.fases = list(fases)

    # Infra: bounded read of every registered sheet (report WARN/INFO).
    try:
        with LibroMigracion(options.source) as libro:
            for hoja in SHEET_BOUNDS:
                try:
                    libro.leer_hoja(hoja, report=run_report)
                except HojaInexistenteError:
                    run_report.warn(hoja, None, None, "hoja no presente en el workbook; omitida")
    except FileNotFoundError as exc:
        run_report.error("source", None, None, f"workbook no encontrado: {exc}")
    except Exception as exc:
        run_report.error("source", None, None, f"error abriendo workbook: {exc}")
    # Infra entries (missing sheets, workbook errors) to stdout.
    _emitir_entradas(run_report.entradas)

    # Phases.
    for fase_id in fases:
        fase = get_fase(fase_id)
        runner = FASE_RUNNERS.get(fase_id)
        if runner is None:
            run_report.info(fase_id, None, None, f"{fase.nombre}: pendiente de implementacion")
            continue
        print(f"\n--- {fase.nombre} ({fase_id}) [{options.modo}] ---")
        run_report.info(fase_id, None, None, f"{fase.nombre}: iniciando ({options.modo})")
        ctx = MigrationContext.para_fase(options, fase_id)
        try:
            if options.modo == "commit":
                from app.db.session import SessionLocal  # lazy: solo en commit

                db = SessionLocal()
                try:
                    runner(ctx.con_session(db))
                finally:
                    db.close()
            else:
                runner(ctx)
            run_report.info(fase_id, None, None, f"{fase.nombre}: OK ({options.modo})")
        except Exception as exc:
            run_report.error(fase_id, None, None, f"{fase.nombre}: {type(exc).__name__}: {exc}")
        # NFR-2: el report interno del runner (conteos por fase) se pinta en stdout.
        _emitir_entradas(ctx.report.entradas)
        # EXM-6: conteos por fase + entradas del runner en la traza de la corrida.
        run_report.conteos_por_fase[fase_id] = {nivel: ctx.report.count(nivel) for nivel in NIVELES}
        run_report.entradas.extend(ctx.report.entradas)

    # EXM-6: persistir la traza JSON (reports/migracion_YYYYMMDD_HHMMSS.json)
    # y listar los archivos escritos en stdout.
    ruta = run_report.write(reports_dir)
    print(f"\nTrazabilidad: {ruta}")
    # MIG-2 (design D7): en modo commit, cada entrada WARN/ERROR de la corrida
    # se persiste en Migracion_Omisiones con corrida = nombre de la traza. El
    # fallo de persistencia es NO-fatal: WARN al reporte interno, exit code y
    # JSON de la traza intactos (la traza ya fue escrita).
    if options.modo == "commit":
        try:
            from app.db.session import SessionLocal  # lazy: solo en commit
            from migrate.omisiones import persistir_omisiones

            db = SessionLocal()
            try:
                persistir_omisiones(db, run_report, corrida_id=ruta.stem)
            finally:
                db.close()
        except Exception as exc:
            run_report.warn(
                "omisiones",
                None,
                None,
                f"no se persistieron las omisiones de la corrida: {type(exc).__name__}: {exc}",
            )
    print(f"Archivos escritos: {ruta.name}")
    errores = run_report.count(LEVEL_ERROR)
    print(f"Resumen: {len(run_report.entradas)} entradas, {errores} errores")
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
    reports_dir = getattr(args, "reports_dir", None)
    sys.exit(ejecutar(options, fases, reports_dir))


if __name__ == "__main__":
    main()
