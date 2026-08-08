"""Migration pipeline for ARPIA.xlsx -> ERP Arpia.

This package hosts the phase registry and the shared infrastructure of the
historical data migration: Excel loading, normalization, execution context,
reporting and the phase CLI. Business phases F0-F7 are registered here as
empty skeletons; their load logic lives in dedicated modules (catalog.py,
purchases.py, bom.py, stock.py, sales.py, finanzas.py, validate.py) added by
later PR slices.

Artifacts live in ENGRAM only (no openspec/filesystem sync). The code on disk
serves the pipeline itself.
"""

from __future__ import annotations

from dataclasses import dataclass


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


def get_fase(fase_id: str) -> Fase:
    """Return the phase with the given id, or raise KeyError with a clear message."""
    for f in FASES:
        if f.id == fase_id:
            return f
    raise KeyError(
        f"Fase desconocida: {fase_id!r}. Valores posibles: {', '.join(f.id for f in FASES)}"
    )


__all__ = ["Fase", "FASES", "get_fase"]