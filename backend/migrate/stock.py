"""F4 stock phase: snapshot inicial INVENTARIO OCT25 (stock_actual por insumo).

Scope of slice 5 (PR#5): ONLY phase 4 (tasks #424 T7; design #423 stock.py + D4).
Tests: backend/tests/test_migrate_stock.py (strict TDD, all written first).

What this module does
---------------------
F4 builds an idempotent ``StockPlan`` from the INVENTARIO OCT25 sheet and, in
commit mode, applies it inside a single ``session_scope`` (EXM-4):

- The snapshot sets ``stock_actual`` = the quantity of the OCT25 physical
  inventory at the cut, per insumo (the baseline F5 destocks against).
  MATERIAL block: B = nombre, D = cantidad; HERRAJES block: F = nombre,
  H = cantidad (layout real de ARPIA.xlsx, `_BLOQUES_OCT25`). The PRENDAS
  block (J..O) is reference only and never read.
- ``stock_minimo`` y ``costo_promedio_actual`` are NOT touched: the cost is
  the F2 WAC outcome (compras historicas); an insumo without WAC keeps 0
  (design D4: "costos derivados de WAC, sin fondo -> 0, report").
- Quantity (EXM-2): a bare number (150) is taken as-is in the canonical unit
  of the insumo; '11 mts' / '50 cm' / '2,90 mts' parse and convert to it
  (reuses ``normalizar_cantidad_compra`` from F2 so both phases share exactly
  one normalizer). Uninterpretable values (None, '#DIV/0!', cero) stop the
  row: reported and excluded, never inferred.

Idempotencia (NFR-1/EXM-3): stock_actual has no UNIQUE; re-running sets the
same snapshot value (idempotent by construction — never adds or duplicates).

Transactions: the caller owns the commit; the enclosing ``session_scope``
commits once at the end (EXM-4). In dry-run nothing is written (NFR-2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import select

from app.models import Insumo
from migrate.catalog import _es_material_valido, normalizar_nombre
from migrate.context import MigrationContext, session_scope
from migrate.loaders import HojaInexistenteError, LibroMigracion, SHEET_BOUNDS
from migrate.normalize import normalizar_decimal
from migrate.purchases import normalizar_cantidad_compra

# OCT25 blocks inside one data row (verified against ARPIA.xlsx 2026-08-08):
# MATERIAL nombre en B, cantidad en D ('11 mts'); HERRAJES nombre en F,
# cantidad en H (bare number). PRENDAS (J..O) is reference only, never read.
_BLOQUES_OCT25: tuple[tuple[str, str], ...] = (("B", "D"), ("F", "H"))


@dataclass(frozen=True)
class StockLinea:
    """One planned stock snapshot line (insumo, cantidad canonica)."""

    insumo_nombre: str
    cantidad: Decimal
    hoja: str
    fila: int


@dataclass
class StockPlan:
    """Plan (dry-run) of the stock snapshot F4 would set."""

    stock: list[StockLinea] = field(default_factory=list)
    sin_cantidad: int = 0      # EXM-2: cantidad no interpretable -> excluida

    @property
    def conteo_stock(self) -> int:
        return len(self.stock)


# --------------------------------------------------------------------------- #
# Pure quantity normalization (EXM-2, reuses the F2 normalizer)
# --------------------------------------------------------------------------- #


def normalizar_cantidad_stock(celda: object, unidad_objetivo: str) -> Decimal | None:
    """Cantidad OCT25 en la unidad canonica del insumo.

    Same semantics as ``normalizar_cantidad_compra`` (F2): bare number -> as-is;
    '11 mts' / '50 cm' / '2,90 mts' -> canonical unit (cm -> m); None,
    '#DIV/0!' or junk -> None (never inferred). One normalizer for both phases.
    A numeric STRING ('150') is a bare count: taken as-is (openpyxl often
    keeps counts as text), before delegating to the F2 parser (which needs a
    unit token).
    """
    if isinstance(celda, str):
        texto = celda.strip()
        if re.fullmatch(r"\d+(?:[.,]\d+)?", texto):
            numero = normalizar_decimal(texto)
            if numero is not None and numero > 0:
                return numero
    return normalizar_cantidad_compra(celda, unidad_objetivo)


def _unidad_de_insumo(nombre: str) -> str:
    """Unidad canonica del insumo (mismo clasificador que F1, design D4)."""
    from migrate.catalog import clasificar_material

    try:
        return clasificar_material(nombre)[1]
    except Exception:
        return "un"


# ------------------------------------------------------------------------- #
# Workbook -> plan (bounded reading, pure aggregate)
# ------------------------------------------------------------------------- #


def plan_stock(libro, report=None) -> StockPlan:
    """Aggregate the stock snapshot plan from INVENTARIO OCT25 (read-only)."""
    plan = StockPlan()
    hoja = "INVENTARIO OCT25"
    if hoja not in SHEET_BOUNDS:
        return plan
    try:
        lectura = libro.leer_hoja(hoja, report=report)
    except HojaInexistenteError:
        if report:
            report.warn(hoja, None, None, "hoja ausente en este workbook; omitida")
        return plan
    inicio = SHEET_BOUNDS[hoja][0]
    for fila_idx, fila in enumerate(lectura.filas, start=inicio):
        for col_nombre, col_cant in _BLOQUES_OCT25:
            valor = fila.get(col_nombre)
            if not isinstance(valor, str):
                continue
            nombre = normalizar_nombre(valor)
            if not _es_material_valido(nombre):
                continue  # 'GANANCIA', 'TOTAL HERR', '4.0' ... junk rows
            unidad_obj = _unidad_de_insumo(nombre)
            cantidad = normalizar_cantidad_stock(fila.get(col_cant), unidad_obj)
            if cantidad is None:
                plan.sin_cantidad += 1
                if report:
                    report.warn(
                        hoja, fila_idx, col_cant,
                        f"{nombre}: cantidad {fila.get(col_cant)!r} no interpretable; "
                        f"fila excluida (EXM-2)",
                    )
                continue
            plan.stock.append(
                StockLinea(
                    insumo_nombre=nombre,
                    cantidad=cantidad,
                    hoja=hoja,
                    fila=fila_idx,
                )
            )
    return plan


# ------------------------------------------------------------------------- #
# DB apply (snapshot idempotente: NFR-1 / EXM-3)
# ------------------------------------------------------------------------- #


def aplicar_stock(db, plan: StockPlan, report=None) -> dict[str, int]:
    """Set ``stock_actual`` del snapshot OCT25 (solo stock; costo queda WAC).

    El caller (session_scope) controla el commit unico (EXM-4). Un insumo que
    aun no esta en el catalogo (F1 debe correr antes) se OMITE y reporta.
    Re-ejecutar setea el mismo valor: no suma, no duplica (NFR-1).
    """
    res = {"seteados": 0, "ya_iguales": 0, "omitidos": 0}
    for linea in plan.stock:
        insumo = db.scalar(select(Insumo).where(Insumo.nombre == linea.insumo_nombre))
        if insumo is None:
            res["omitidos"] += 1
            if report:
                report.error(
                    linea.hoja, linea.fila, None,
                    f"{linea.insumo_nombre}: insumo ausente en catalogo; stock no "
                    f"aplicado (correr F1 antes)",
                )
            continue
        if insumo.stock_actual == linea.cantidad:
            res["ya_iguales"] += 1
            continue
        insumo.stock_actual = linea.cantidad
        res["seteados"] += 1
        if report:
            report.info(
                linea.hoja, linea.fila, None,
                f"{linea.insumo_nombre}: stock_actual -> {linea.cantidad} "
                f"(costo WAC intacto)",
            )
    if report:
        report.info(
            "F4", None, None,
            f"stock OCT25: {res['seteados']} seteados, "
            f"{res['ya_iguales']} ya-iguales, {res['omitidos']} omitidos",
        )
    return res


# ------------------------------------------------------------------------- #
# Phase entry point (F4 runner registered in migrate/__init__.py)
# ------------------------------------------------------------------------- #


def cargar_stock(ctx: MigrationContext) -> StockPlan:
    """F4 runner: builds the stock plan and, in commit mode, applies it inside a
    single transaction (EXM-3/4), idempotent (NFR-1). Dry-run writes nothing."""
    report = ctx.report
    with LibroMigracion(ctx.options.source) as libro:
        plan = plan_stock(libro, report)

    report.info(
        "F4", None, None,
        f"plan stock OCT25: {plan.conteo_stock} insumos | sin cantidad "
        f"{plan.sin_cantidad}",
    )
    if ctx.options.modo == "commit" and ctx.session is not None:
        with session_scope(ctx, ctx.session) as db:
            aplicar_stock(db, plan, report)
    return plan


__all__ = [
    "StockLinea",
    "StockPlan",
    "normalizar_cantidad_stock",
    "plan_stock",
    "aplicar_stock",
    "cargar_stock",
]