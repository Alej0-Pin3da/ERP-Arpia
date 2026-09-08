"""SAFE wiring: validated INVERSION VALQUI plan -> F2 (Compras_Insumos WAC)
+ F6 (Movimientos_Financieros).

Delegated direct route (NOT SDD): this module imports the pure planners
``plan_izquierda`` / ``plan_derecha`` from ``preprocess_inversion_valqui``
and books them through the existing phase writers ``aplicar_compras`` (F2)
and ``aplicar_finanzas`` (F6). No pipeline logic is duplicated here; the
only new logic is the OWNER SAFETY GATE below.

Safety gate (never violated):
- ``OWNER_ALLOWLIST`` is EMPTY by default. Every row the preprocess flagged
  for an owner decision (``revision_dueno`` DEC-1, ``duplicado`` DEC-7,
  ``post_corte`` DEC-7, right-table unique source with NULL supplier FK
  DEC-5) stays SKIPPED until the owner confirms its CSV line number in the
  allowlist. Nothing is ever inferred.
- 2026 post-OCT25 rows (``ALLOW_POST_CUTOFF_2026``) default to SKIP: booking
  them into WAC would silently rewrite historical costs. The owner either
  confirms per-line in the allowlist or flips the cut-off flag explicitly
  (separate ledger decision, never silent).
- Direccion has no DB column -> dropped nota only, never persisted.
- Movimientos ``tipo`` is validated against the case-sensitive CHECK
  (``ck_movimientos_tipo``): only 'Gasto' / 'Inversion' / 'Retiro' book.
- Right-only new items (not in the F1 catalog) ERROR at apply time via
  ``aplicar_compras`` (``Insumo.categoria_id`` + ``unidad_medida`` are NOT
  NULL, so they need F1 catalog first) instead of inventing catalog rows.

Usage (from ``backend/``):
    python -m migrate.inversion_valqui_loader --dry-run   # default, 0 writes
    python -m migrate.inversion_valqui_loader --apply --yes   # books allowlisted only

Exit code: 0 when no ERROR, 1 otherwise. --apply requires --yes.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from migrate.finanzas import (
    FinanzasPlan,
    MovimientoPlan,
    aplicar_finanzas,
    clasificar_tipo,
)
from migrate.normalize import coerce_aware
from migrate.preprocess_inversion_valqui import (
    WAC_CUTOFF,
    MovementCandidate,
    StockCandidate,
    SupplierMap,
    _cargar_universo,
    _leer_csv,
    parse_fecha,
    plan_derecha,
    plan_izquierda,
)
from migrate.purchases import CompraPlan, ComprasPlan, aplicar_compras
from migrate.report import LEVEL_ERROR, Report

# --------------------------------------------------------------------------- #
# Owner safety gate: EMPTY by default. The owner confirms CSV line numbers
# after reviewing the dry-run on screen. Documented examples (DO NOT enable
# without the owner's explicit per-row confirmation):
# - "dec1_stock": DEC-1 stockables outside the BOM universe flagged
#   revision_dueno, e.g. {57} if the owner confirms L57 as stockable
#   (alternative: movement).
# - "dec4_supplier": DEC-4 rows skipped for missing supplier, e.g. {"L56"}
#   once the owner supplies the real supplier (never inferred from
#   Direccion).
# - "dec7_duplicates": DEC-7 exact duplicates needing confirmation that
#   they are two real buys, e.g. {83, 75, 24, 25} for Cajas L83-84,
#   Hilaza L75-76, Hilo L24/L26 + L25/L27.
# - "dec7_post_cutoff": DEC-7 2026 post-cut rows confirmed for booking,
#   e.g. {96} for a 2026 tote-hardware lot the owner imputes explicitly.
# - "dec5_right_unique": DEC-5 right-table unique sources (supplier FK
#   NULL), e.g. {18} once the owner confirms the source lot.
# --------------------------------------------------------------------------- #
OWNER_ALLOWLIST: dict[str, set] = {
    "dec1_stock": set(),
    "dec4_supplier": set(),
    "dec7_duplicates": set(),
    "dec7_post_cutoff": set(),
    "dec5_right_unique": set(),
}

# 2026 batch post-OCT25 WAC cut: default SKIP (never silently rewrite WAC).
# The owner flips this only as an explicit separate-ledger decision.
ALLOW_POST_CUTOFF_2026 = False

# Case-sensitive CHECK ck_movimientos_tipo.
TIPOS_VALIDOS = frozenset({"Gasto", "Inversion", "Retiro"})


def _parse_fecha_plan(fecha_iso: str) -> datetime | None:
    """ISO date from the plan (YYYY-MM-DD) -> naive datetime; None if bad."""
    try:
        return datetime.fromisoformat(fecha_iso)
    except ValueError:
        return parse_fecha(fecha_iso)


def _es_post_corte(fecha_iso: str) -> bool:
    fecha = _parse_fecha_plan(fecha_iso)
    if fecha is None:
        return False
    return fecha > WAC_CUTOFF


def _stock_bookable(c: StockCandidate, report: Report) -> bool:
    """True only when every owner decision on this row is confirmed."""
    if c.revision_dueno and c.linea not in OWNER_ALLOWLIST["dec1_stock"]:
        report.warn(
            "VALQUI-SAFE", c.linea, None,
            f"[DEC-1] {c.producto!r}: fuera del universo BOM, sin confirmacion "
            f"del dueno; omitida (nunca inferida)",
        )
        return False
    if c.duplicado and c.linea not in OWNER_ALLOWLIST["dec7_duplicates"]:
        report.warn(
            "VALQUI-SAFE", c.linea, None,
            f"[DEC-7] {c.producto!r}: duplicado exacto sin confirmacion; "
            f"omitida (el dueno confirma si son dos compras reales)",
        )
        return False
    if c.post_corte and not (
        ALLOW_POST_CUTOFF_2026 or c.linea in OWNER_ALLOWLIST["dec7_post_cutoff"]
    ):
        report.warn(
            "VALQUI-SAFE", c.linea, None,
            f"[DEC-7] {c.producto!r} {c.fecha}: posterior al corte WAC OCT25; "
            f"omitida (nunca reescribe WAC en silencio)",
        )
        return False
    if c.fuente == "derecha-unica" and c.linea not in OWNER_ALLOWLIST["dec5_right_unique"]:
        report.warn(
            "VALQUI-SAFE", c.linea, None,
            f"[DEC-5] {c.producto!r}: fuente unica sin proveedor (FK NULL) ni "
            f"confirmacion; omitida",
        )
        return False
    return True


def _movement_bookable(m: MovementCandidate, report: Report) -> bool:
    if m.tipo not in TIPOS_VALIDOS:
        report.error(
            "VALQUI-SAFE", m.linea, None,
            f"{m.descripcion!r}: tipo {m.tipo!r} viola CHECK case-sensitive; omitido",
        )
        return False
    if _es_post_corte(m.fecha) and not (
        ALLOW_POST_CUTOFF_2026 or m.linea in OWNER_ALLOWLIST["dec7_post_cutoff"]
    ):
        report.warn(
            "VALQUI-SAFE", m.linea, None,
            f"[DEC-7] {m.descripcion!r} {m.fecha}: posterior al corte WAC OCT25; "
            f"omitido (el dueno confirma imputacion)",
        )
        return False
    return True


def _a_compra_plan(c: StockCandidate, report: Report) -> CompraPlan | None:
    try:
        cantidad = Decimal(c.cantidad)
        precio = Decimal(c.costo_unitario)
    except (InvalidOperation, ValueError):
        report.error(
            "VALQUI-SAFE", c.linea, None,
            f"{c.producto!r}: cantidad/precio no numericos; omitida",
        )
        return None
    fecha = coerce_aware(_parse_fecha_plan(c.fecha))
    if not isinstance(fecha, datetime):
        report.error(
            "VALQUI-SAFE", c.linea, None,
            f"{c.producto!r}: fecha {c.fecha!r} ilegible; omitida (D5, nunca now())",
        )
        return None
    return CompraPlan(
        insumo_nombre=c.producto,
        cantidad=cantidad,
        precio_unitario=precio,
        fecha=fecha,
        hoja="INVERSION VALQUI",
        fila=c.linea,
        fecha_heredada=c.fecha_heredada,
    )


def _a_movimiento_plan(m: MovementCandidate, report: Report) -> MovimientoPlan | None:
    try:
        monto = Decimal(m.monto)
    except (InvalidOperation, ValueError):
        report.error(
            "VALQUI-SAFE", m.linea, None,
            f"{m.descripcion!r}: monto no numerico; omitido",
        )
        return None
    fecha = coerce_aware(_parse_fecha_plan(m.fecha))
    if not isinstance(fecha, datetime):
        report.error(
            "VALQUI-SAFE", m.linea, None,
            f"{m.descripcion!r}: fecha {m.fecha!r} ilegible; omitido (D5, nunca now())",
        )
        return None
    tipo = m.tipo if m.tipo in TIPOS_VALIDOS else clasificar_tipo(m.descripcion)
    if tipo not in TIPOS_VALIDOS:  # clasificar_tipo default is safe ('Gasto').
        report.error(
            "VALQUI-SAFE", m.linea, None,
            f"{m.descripcion!r}: tipo {tipo!r} viola CHECK; omitido",
        )
        return None
    return MovimientoPlan(
        descripcion=m.descripcion,
        monto=monto,
        tipo=tipo,
        fecha=fecha,
        socio_nombre=m.socio,
        hoja="INVERSION VALQUI",
        fila=m.linea,
    )


def build_safe_plan(
    csv_path: Path | None = None,
    report: Report | None = None,
) -> tuple[ComprasPlan, FinanzasPlan, dict]:
    """Run the preprocess planners and keep ONLY owner-confirmed rows.

    Returns (safe F2 plan, safe F6 plan, skip stats). Pure: never writes.
    """
    report = report or Report(fase="INVERSION-VALQUI-SAFE", modo="dry-run")
    root = Path(__file__).resolve().parents[2]
    csv_path = csv_path or root / "ARPIA - INVERSION VALQUI (1).csv"
    filas, cols_der = _leer_csv(csv_path, report)
    universo, _origen = _cargar_universo(report)
    proveedores = SupplierMap()
    ultima_fecha: dict = {}
    stocks_izq, movimientos, _stats = plan_izquierda(
        filas, universo, report, proveedores, ultima_fecha
    )
    stocks_der, _decisiones, _suma = plan_derecha(
        filas, cols_der, universo, report, ultima_fecha
    )
    plan_c = ComprasPlan()
    plan_f = FinanzasPlan()
    skips = {"stock_held": 0, "stock_kept": 0, "mov_held": 0, "mov_kept": 0}
    for c in stocks_izq + stocks_der:
        if not _stock_bookable(c, report):
            skips["stock_held"] += 1
            continue
        compra = _a_compra_plan(c, report)
        if compra is None:
            skips["stock_held"] += 1
            continue
        plan_c.compras.append(compra)
        plan_c.conteos.planificadas += 1
        skips["stock_kept"] += 1
    for m in movimientos:
        if not _movement_bookable(m, report):
            skips["mov_held"] += 1
            continue
        mov = _a_movimiento_plan(m, report)
        if mov is None:
            skips["mov_held"] += 1
            continue
        plan_f.movimientos.append(mov)
        plan_f.conteos.planificadas += 1
        skips["mov_kept"] += 1
    return plan_c, plan_f, skips


def ejecutar(
    *,
    modo: str = "dry-run",
    csv_path: Path | None = None,
    reports_dir: Path | str | None = None,
) -> int:
    report = Report(fase="INVERSION-VALQUI-LOADER", modo=modo)
    plan_c, plan_f, skips = build_safe_plan(csv_path, report)

    # ---- stdout (Spanish, owner-facing) ----
    print(f"=== INVERSION VALQUI loader [{modo}] (allowlist SAFE) ===")
    print("WOULD BOOK -> Compras_Insumos (F2 WAC):")
    if not plan_c.compras:
        print("  (sin filas: todo lo no confirmado queda retenido)")
    for compra in plan_c.compras:
        fecha = compra.fecha.date() if isinstance(compra.fecha, datetime) else "?"
        print(
            f"  L{compra.fila} {compra.insumo_nombre[:38]} "
            f"{compra.cantidad} @ {compra.precio_unitario} fecha {fecha}"
        )
    print("WOULD BOOK -> Movimientos_Financieros (F6):")
    if not plan_f.movimientos:
        print("  (sin filas: todo lo no confirmado queda retenido)")
    for mov in plan_f.movimientos:
        fecha = mov.fecha.date() if isinstance(mov.fecha, datetime) else "?"
        print(
            f"  L{mov.fila} {mov.descripcion[:38]} {mov.monto} "
            f"{mov.tipo} fecha {fecha} socio {mov.socio_nombre}"
        )
    print(
        f"RETENIDAS sin confirmacion: stock {skips['stock_held']} / "
        f"movimientos {skips['mov_held']} | confirmadas: stock "
        f"{skips['stock_kept']} / movimientos {skips['mov_kept']}"
    )

    aplicadas: dict = {}
    if modo == "apply":
        from app.db.session import SessionLocal  # lazy: solo en apply

        db = SessionLocal()
        try:
            res_c = aplicar_compras(db, plan_c, report)
            res_f = aplicar_finanzas(db, plan_f, report)
            aplicadas = {"compras": res_c, "finanzas": res_f}
            if report.count(LEVEL_ERROR):
                db.rollback()
                print("APPLY: errores -> rollback total, 0 escrituras.")
            else:
                db.commit()
                print(
                    f"APPLY: {res_c['insertadas']} compras + "
                    f"{res_f['movimientos']} movimientos confirmados por el dueno."
                )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    else:
        print("DRY-RUN: 0 escrituras DB (use --apply --yes para confirmar).")

    audit = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "mode": modo,
        "allowlist": {k: sorted(v) for k, v in OWNER_ALLOWLIST.items()},
        "allow_post_cutoff_2026": ALLOW_POST_CUTOFF_2026,
        "safe_compras": [asdict(c) for c in plan_c.compras],
        "safe_movimientos": [asdict(m) for m in plan_f.movimientos],
        "skips": skips,
        "aplicadas": aplicadas,
        "warnings": [
            {"hoja": e.hoja, "fila": e.fila, "nivel": e.nivel, "mensaje": e.mensaje}
            for e in report.entradas
        ],
        "summary": {
            "compras": len(plan_c.compras),
            "movimientos": len(plan_f.movimientos),
            "warnings": report.count("WARN"),
            "errors": report.count(LEVEL_ERROR),
        },
    }
    target = Path(reports_dir) if reports_dir else Path(__file__).resolve().parent / "reports"
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"inversion_valqui_loader_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(audit, indent=2, ensure_ascii=False, default=str),
                    encoding="utf-8")
    for linea in report.resumen_lineas():
        print(linea)
    print(f"Audit: {path} [{modo}]")
    return 1 if report.count(LEVEL_ERROR) else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="SAFE wiring INVERSION VALQUI -> F2/F6 (allowlist del dueno)."
    )
    parser.add_argument("--dry-run", action="store_const", const="dry-run", dest="modo")
    parser.add_argument("--apply", action="store_const", const="apply", dest="modo")
    parser.add_argument("--yes", action="store_true",
                        help="Explicit owner confirmation (required with --apply).")
    parser.add_argument("--csv", dest="csv_path", type=Path, default=None)
    parser.add_argument("--reports-dir", type=Path, default=None)
    parser.add_argument("--cwd", type=Path, default=None)
    parser.set_defaults(modo="dry-run")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.cwd:
        import os

        os.chdir(args.cwd)
    if args.modo == "apply" and not args.yes:
        raise SystemExit("--apply exige --yes explicito del dueno.")
    raise SystemExit(ejecutar(modo=args.modo, csv_path=args.csv_path,
                              reports_dir=args.reports_dir))


if __name__ == "__main__":
    main()


__all__ = [
    "OWNER_ALLOWLIST",
    "ALLOW_POST_CUTOFF_2026",
    "build_safe_plan",
    "ejecutar",
    "main",
]
