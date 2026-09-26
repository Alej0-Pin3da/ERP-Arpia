"""Backfill F2/F6: filas omitidas por D5 sin fecha, con fecha autorizada.

El usuario autorizó fecha 2025-03 para las filas que la migración omitió por
falta de fecha real (66 WARN en INVERSION MARGARA + 4 gastos GASTOS ARPIA sin
columna de fecha). El script construye el plan base y el plan con fallback,
aplica SOLO la diferencia (clave hoja+fila) vía los appliers idempotentes
(aplicar_compras / aplicar_finanzas, doble guarda por clave natural en DB).

--dry-run (default) no escribe; --apply persiste en una transacción.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from migrate.finanzas import FinanzasPlan, aplicar_finanzas, plan_finanzas
from migrate.loaders import LibroMigracion
from migrate.normalize import UTC
from migrate.purchases import ComprasPlan, aplicar_compras, plan_compras
from migrate.report import LEVEL_ERROR, Report

FASE = "BACKFILL-SIN-FECHA"

# Filas de totales del Excel: nunca son gasto real (verificado: la DB no tiene
# ninguna; el fallback las rescataría como "Gasto total" millonario).
_JUNK_EXACTO = frozenset({"total", "totales", "subtotal", "total inversion", "total inversiones"})


def _es_basura(descripcion: str) -> bool:
    from migrate.catalog import clave_normalizada

    return clave_normalizada(descripcion) in _JUNK_EXACTO


def _parse_fecha(texto: str) -> datetime:
    try:
        anio, mes = texto.split("-")
        fecha = datetime(int(anio), int(mes), 1, tzinfo=UTC)
    except (ValueError, AttributeError) as exc:
        raise SystemExit(f"--fecha debe ser YYYY-MM (ej. 2025-03): {texto!r}") from exc
    return fecha


def _diff_compras(base: ComprasPlan, full: ComprasPlan):
    vistas = {(c.hoja, c.fila) for c in base.compras}
    return [c for c in full.compras if (c.hoja, c.fila) not in vistas]


def _diff_movimientos(base, full):
    vistos = {(m.hoja, m.fila) for m in base.movimientos}
    return [m for m in full.movimientos if (m.hoja, m.fila) not in vistos]


def ejecutar(
    *,
    modo: str = "dry-run",
    workbook: Path | None = None,
    fecha: str = "2025-03",
    reports_dir: Path | str | None = None,
) -> int:
    from app.db.session import SessionLocal

    root = Path(__file__).resolve().parents[2]
    workbook = workbook or root / "ARPIA.xlsx"
    fallback = _parse_fecha(fecha)
    report = Report(fase=FASE, modo=modo)
    libro = LibroMigracion(workbook)
    libro.abrir()
    try:
        base_c = plan_compras(libro, report)
        full_c = plan_compras(libro, report, fecha_fallback=fallback)
        base_f = plan_finanzas(libro, report)
        full_f = plan_finanzas(libro, report, fecha_fallback=fallback)
    finally:
        libro.cerrar()
    nuevas_compras = _diff_compras(base_c, full_c)
    nuevos_movs = [m for m in _diff_movimientos(base_f, full_f) if not _es_basura(m.descripcion)]
    report.info(
        FASE, None, None,
        f"backfill {fecha}: {len(nuevas_compras)} compras + {len(nuevos_movs)} "
        f"movimientos recuperados (base {base_c.conteo_compras}/{base_f.conteo_movimientos})",
    )
    for c in nuevas_compras:
        report.info(
            c.hoja, c.fila, None,
            f"backfill compra {c.insumo_nombre}: {c.cantidad} @ {c.precio_unitario:.2f} "
            f"fecha {fallback.date()} (autorizada)",
        )
    for m in nuevos_movs:
        report.info(
            m.hoja, m.fila, None,
            f"backfill {m.tipo} {m.descripcion}: {m.monto} fecha {fallback.date()} "
            f"socio {m.socio_nombre or 'NULL'} (autorizada)",
        )
    audit = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "mode": modo,
        "fecha_autorizada": fallback.date().isoformat(),
        "compras_nuevas": [
            {"hoja": c.hoja, "fila": c.fila, "insumo": c.insumo_nombre,
             "cantidad": str(c.cantidad), "precio": str(c.precio_unitario)}
            for c in nuevas_compras
        ],
        "movimientos_nuevos": [
            {"hoja": m.hoja, "fila": m.fila, "descripcion": m.descripcion,
             "monto": str(m.monto), "tipo": m.tipo, "socio": m.socio_nombre}
            for m in nuevos_movs
        ],
    }
    db = SessionLocal()
    try:
        antes = report.count(LEVEL_ERROR)
        res_c = aplicar_compras(db, ComprasPlan(compras=nuevas_compras), report)
        res_f = aplicar_finanzas(db, FinanzasPlan(movimientos=nuevos_movs), report)
        audit["apply"] = {"compras": res_c, "finanzas": res_f}
        if modo == "apply" and report.count(LEVEL_ERROR) == antes:
            db.commit()
        else:
            db.rollback()  # dry-run siempre revierte; con ERROR no persiste nada
    finally:
        db.close()
    audit["warnings"] = [
        {"hoja": e.hoja, "fila": e.fila, "celda": e.celda,
         "nivel": e.nivel, "mensaje": e.mensaje}
        for e in report.entradas
    ]
    audit["summary"] = {"warnings": report.count("WARN"), "errors": report.count(LEVEL_ERROR)}
    target = Path(reports_dir) if reports_dir else Path(__file__).resolve().parent / "reports"
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"backfill_sin_fecha_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    for line in report.resumen_lineas():
        print(line)
    print(f"Audit: {path} [{modo}]")
    return 1 if report.count(LEVEL_ERROR) else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill filas sin fecha (F2/F6) con fecha autorizada")
    parser.add_argument("--dry-run", action="store_const", const="dry-run", dest="modo")
    parser.add_argument("--apply", action="store_const", const="apply", dest="modo")
    parser.add_argument("--workbook", type=Path, default=None)
    parser.add_argument("--fecha", default="2025-03", help="YYYY-MM autorizado (default 2025-03)")
    parser.add_argument("--reports-dir", type=Path, default=None)
    parser.add_argument("--cwd", type=Path, default=None)
    parser.set_defaults(modo="dry-run")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.cwd:
        import os

        os.chdir(args.cwd)
    raise SystemExit(
        ejecutar(modo=args.modo, workbook=args.workbook, fecha=args.fecha, reports_dir=args.reports_dir)
    )


if __name__ == "__main__":
    main()
