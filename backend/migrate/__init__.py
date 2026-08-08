"""Migration pipeline for ARPIA.xlsx -> ERP Arpia.

This package hosts the phase registry and the shared infrastructure of the
historical data migration: Excel loading, normalization, execution context,
reporting and the phase CLI. The catalog phase (F0/F1) is implemented in
catalog.py; the remaining phases (purchases.py, bom.py, stock.py, sales.py,
finanzas.py, validate.py) are added by later PR slices.

Artifacts live in ENGRAM only (no openspec/filesystem sync). The code on disk
serves the pipeline itself.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from migrate.context import MigrationContext


@dataclass(frozen=True)
class Fase:
    """Phase metadata (id/name/description + owning module, None while a stub)."""

    id: str
    nombre: str
    descripcion: str
    modulo: str | None = None


# Order is strict (EXM-3); F0-F7 as defined by design #423 / tasks #424.
FASES: tuple[Fase, ...] = (
    Fase("F0", "Bootstrap", "Seeder base + Tipos_Producto", "catalog"),
    Fase("F1", "Catalogo", "Proveedores, categorias, insumos, productos+variantes", "catalog"),
    Fase("F2", "Compras-WAC", "Compras historicas WAC (insumos BOM-only, fecha real)", "purchases"),
    Fase("F3", "BOM", "BOM_Insumos + BOM_Productos (combos CAJAS)", "bom"),
    Fase("F4", "Stock-OCT25", "Snapshot stock inicial INVENTARIO OCT25", "stock"),
    Fase("F5", "Ventas", "INSERT directo Venta + Detalle + destock batch", "sales"),
    Fase("F6", "Finanzas", "Socios 40/30/30 + Movimientos_Financieros", "finanzas"),
    Fase("F7", "Validacion", "Checks N7a-g + Migration_Log", "validate"),
)


# Phase runner registry: the CLI dispatches a fase id to its runner; a fase
# without a runner reports 'pendiente de implementacion' (later slices).
FASE_RUNNERS: dict[str, Callable[[MigrationContext], object]] = {}


def registrar_fase(fase_id: str, runner: Callable[[MigrationContext], object]) -> None:
    """Register a phase runner in the registry (this slice: F0/F1 from catalog)."""
    FASE_RUNNERS[fase_id] = runner


def _registrar_runners() -> None:
    from migrate.catalog import bootstrap_catalog_phase, catalogar

    registrar_fase("F0", bootstrap_catalog_phase)
    registrar_fase("F1", catalogar)


_registrar_runners()


def get_fase(fase_id: str) -> Fase:
    """Return the phase with the given id, or raise KeyError with a clear message."""
    for f in FASES:
        if f.id == fase_id:
            return f
    raise KeyError(f"Fase '{fase_id}' no existe (valores: {[f.id for f in FASES]})")


# Fases whose business logic is already implemented (status reporting).
FASES_IMPLEMENTADAS: tuple[str, ...] = ("F0", "F1")


__all__ = [
    "Fase",
    "FASES",
    "FASE_RUNNERS",
    "FASES_IMPLEMENTADAS",
    "registrar_fase",
    "get_fase",
]