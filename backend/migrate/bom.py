"""F3 BOM phase: BOM_Insumos por receta + BOM_Productos combos CAJAS.

Scope of slice 5 (PR#5): ONLY phase 3 (tasks #424 T6; design #423 bom.py + D4).
Tests: backend/tests/test_migrate_bom.py (strict TDD, all written first).

What this module does
---------------------
F3 builds an idempotent ``BomPlan`` from the BOM recipe sheets and, in commit
mode, applies it inside a single ``session_scope`` (EXM-4):

- BOM_Insumos: every recipe sheet maps to a catalog Producto via the
  ``BLOQUES_BOM`` provenance table. The LEFT block (columns A..F) of each
  sheet feeds its product; sheets that define TWO products (``BLUSAS``:
  MANGA LARGA left, MANGA CORTA right) also feed the second product from the
  right block (I..L). Ghost sub-blocks (sheets whose right block is a TANGA
  duplicate, or the duplicated CACHETERO block in 'Noche y Dia') are skipped:
  the product already has its own canonical sheet.
- Combos (hoja CAJAS): each block column (B/F/J) becomes a combo product;
  its rows are BOM_Productos (productos con su propio BOM -> multinivel real)
  when the name is a product, or BOM_Insumos (empaques Caja/Vela/Papel/Envio)
  when it is packaging that touches the order (design D4 / F1 catalog).
- The quantity of a recipe row is the Excel "cantidad Cms" cell. It is
  converted to the insumo canonical unit: Telas -> metros via LINEAR cm of
  consumption per garment (metros = cm / 100; the material width does NOT
  participate); Herrajes 'un' -> piece count as-is; 'cm2' (herrajes priced by
  cm2) -> as-is. Uninterpretable amounts (None, '#DIV/0!', cero, no-numeric)
  are reported and excluded, never inferred (EXM-2).

Idempotencia (NFR-1/EXM-3): PG UNIQUE does not apply over NULLs, and the app
model has no UNIQUE over (producto, insumo, variante), so BomInsumo dedup is
MANUAL by natural key (producto_id, insumo_id, variante_id NULL) and
BomProducto by (combo_id, producto_incluido_id): re-running never duplicates.

Transactions: the caller owns the commit; the enclosing ``session_scope``
commits once at the end (EXM-4). In dry-run nothing is written (NFR-2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable

from openpyxl.utils import column_index_from_string
from sqlalchemy import select

from app.models import BomInsumo, BomProducto, Insumo, Producto
from migrate.catalog import _es_material_valido, clave_normalizada, normalizar_nombre
from migrate.context import MigrationContext, session_scope
from migrate.loaders import HojaInexistenteError, LibroMigracion, SHEET_BOUNDS
from migrate.normalize import normalizar_decimal

# Recipe sheets -> (product of the left block, product of the right block or
# None when the right block is a ghost / duplicated sub-table). Provenance
# mirrors PRODUCTOS_CATALOGO (catalog.py): 'Noche y Dia' defines Bralete; its
# right CACHETERRO block is a re-run of the dedicated 'Noche y Dia CACHETERO'
# sheet, so it is skipped to avoid dual-inventory of Cachetero.
BLOQUES_BOM: dict[str, tuple[str, str | None]] = {
      "Braleth diseño 1": ("Bralete", None),
    "Noche y Dia CACHETERO": ("Cachetero", None),
    "Noche y Dia": ("Bralete", None),
    "CORSET": ("Corset", None),
    "CORSET DOBLE CARA": ("Corset Doble Cara", None),
    "CORSET ARTEMISIA": ("Corset Artemisia", None),
    "FALDA EMILY": ("Falda Emily", None),
    "Corset Hypatia": ("Corset Hypatia", None),
    "BUSTIER": ("Bustier", None),
      "BLUSAS": ("Blusa Manga Larga", "Blusa Arpia"),
    "TOTEBAG": ("Tote Bag Arpia", None),
}

# CAJAS sheet: each combo block is a (nombre, costo, precio) column triplet.
# The block header is the combo product name ("Caja Despertar", ...); generic
# "CAJA 1/2/3" headers fall back to this positional mapping (design F3).
_COMBOS_CAJAS_POSICION: tuple[str, ...] = (
    "Caja Despertar",
    "Caja Despertar V2",
    "Caja Saca Las Garras",
)
_COLS_COMBOS: tuple[tuple[str, str, str], ...] = (
    ("B", "C", "D"),
    ("F", "G", "H"),
    ("J", "K", "L"),
)
# Packaging names inside a combo block -> BOM_Insumos of the combo product
# (catalog F1 considers them insumos too, design D4 / CAJAS sheet).
_EMPAQUES_COMBO = frozenset(
    {"caja", "vela", "papel", "envio", "bolsa", "etiqueta", "tarjeta"}
)

# Recipe-sheet material names that do NOT match the F1 catalog 1:1 (key
# normalizada -> canonical catalog name). The recipe Excel uses short or
# divergent names vs the catalog loaded from investments (e.g. "Argolla 10 mm"
# vs catalog "Argolla numero 10 mm"); everything else resolves by exact match.
# These aliases never create insumos: the orchestrator creates the missing ones
# in the real DB with the exact canonical name, so an alias line is still
# omitted until that insumo exists (intended behavior).
ALIASES_BOM_A_CATALOGO: dict[str, str] = {
    "argolla 10 mm": "Argolla numero 10 mm",
    "argolla 8 mm": "Argolla numero 8 mm",
    "tensor 8 de 10mm": "Tensor 8 numero 10",
    "zeta de 10 mm": "Zeta numero 10",
    "tira de brasier": "Tira de Brasier negro 10 mts",
    "franela lycra": "Franela lycra 1 mt (blanco y negro)",
    "tela a cuadros": "Tejido plano sim popelina (a cuadros bn)",
    "powernet negro delgado (corsets)": "Powernet negro delgado",
    "tela maya ilustrada": "Tela Maya Ilustrada",
    "sesgo elastico 10 mts": "Sesgo Elastico 10 mts",
    "aro copa brasier": "Aro Copa Brasier",
    "rosa tejida gris": "Rosa tejida gris",
}


@dataclass(frozen=True)
class BomLinea:
    """One planned BOM insumo line (producto, insumo, cantidad convertida)."""

    producto_nombre: str
    insumo_nombre: str
    cantidad: Decimal
    hoja: str
    fila: int


@dataclass(frozen=True)
class ComboLinea:
    """One BOM_Productos combo member (producto incluido en el combo)."""

    combo_nombre: str
    producto_incluido: str
    cantidad: Decimal
    hoja: str
    fila: int


@dataclass(frozen=True)
class ComboInsumoLinea:
    """One packaging insumo consumed by a combo (BOM_Insumos del combo)."""

    combo_nombre: str
    insumo_nombre: str
    cantidad: Decimal
    hoja: str
    fila: int


@dataclass
class BomPlan:
    """Plan (dry-run) of the BOM lines F3 would write."""

    insumos: list[BomLinea] = field(default_factory=list)
    combos: list[ComboLinea] = field(default_factory=list)
    combos_insumos: list[ComboInsumoLinea] = field(default_factory=list)
    sin_cantidad: int = 0   # EXM-2: amount not interpretable -> excluded

    @property
    def conteo_insumos(self) -> int:
        return len(self.insumos)

    @property
    def conteo_combos(self) -> int:
        return len(self.combos) + len(self.combos_insumos)


# --------------------------------------------------------------------------- #
# Pure quantity conversion (TDD-friendly)
# --------------------------------------------------------------------------- #


def convertir_cantidad_bom(
    cantidad_raw: object,
    nombre_insumo: object,
    unidad: str,
) -> Decimal | None:
    """Celda 'cantidad Cms' (cm lineales de consumo) -> cantidad en la unidad
    canonica del insumo.

    - numero (int/float/Decimal): parseado; 0, negativo o None -> None (cero
      no es consumo; nunca se infiere, EXM-2). Texto '#DIV/0!' -> None.
    - Telas (m): 'cantidad Cms' son CENTIMETROS LINEALES de consumo por
      prenda; metros = cm / 100. El ancho del material NO participa.
    - Herrajes 'cm2' (precio por cm2) / 'un' (conteo de piezas): as-is.
    """
    if cantidad_raw is None:
        return None
    if isinstance(cantidad_raw, str) and cantidad_raw.startswith("#"):
        return None
    numero = normalizar_decimal(cantidad_raw)
    if numero is None or numero <= 0:
        return None
    if unidad == "m":
        return numero / Decimal("100")
    return numero


# ------------------------------------------------------------------------- #
# Workbook -> plan (bounded reading, pure aggregate)
# ------------------------------------------------------------------------- #


def _unidad_de_insumo(nombre: str) -> str:
    """Unidad canonica del insumo (mismo clasificador que F1, design D4)."""
    from migrate.catalog import clasificar_material

    try:
        return clasificar_material(nombre)[1]
    except Exception:
        return "un"


def _procesar_bloque(
    plan: BomPlan,
    fila: dict[str, object],
    fila_idx: int,
    hoja: str,
    producto_nombre: str,
    col_nombre: str,
    col_cant: str,
    report=None,
) -> None:
    """One (left or right) BOM block cell: build a BomLinea or count/report."""
    valor = fila.get(col_nombre)
    if not isinstance(valor, str):
        return  # junk numeric rows ("4.0") are not material names
    nombre = normalizar_nombre(valor)
    if not _es_material_valido(nombre):
        return  # totals/profit/talla rows are junk (catalog._es_material_valido)
    unidad = _unidad_de_insumo(nombre)
    cantidad = convertir_cantidad_bom(fila.get(col_cant), nombre, unidad)
    if cantidad is None:
        plan.sin_cantidad += 1
        if report:
            report.warn(
                hoja, fila_idx, col_cant,
                f"{producto_nombre} <- {nombre}: cantidad {fila.get(col_cant)!r} " 
                f"no interpretable; linea excluida (EXM-2)",
            )
        return
    plan.insumos.append(
        BomLinea(
            producto_nombre=producto_nombre,
            insumo_nombre=nombre,
            cantidad=cantidad,
            hoja=hoja,
            fila=fila_idx,
        )
    )


def _plan_combos(libro: LibroMigracion, plan: BomPlan, report=None) -> None:
    """Hoja CAJAS -> combos (BOM_Productos + insumos de empaque)."""
    if "CAJAS" not in SHEET_BOUNDS:
        return
    try:
        (ws, filas, inicio) = (
            libro.obtener_worksheet("CAJAS"),
            libro.leer_hoja("CAJAS", report=report).filas,
            SHEET_BOUNDS["CAJAS"][0],
        )
    except HojaInexistenteError:
        if report:
            report.warn("CAJAS", None, None, "hoja ausente; combos omitidos")
        return
    for pos, (col_nombre, _col_costo, _col_precio) in enumerate(_COLS_COMBOS):
        header = ws.cell(row=2, column=column_index_from_string(col_nombre)).value
        nombre_combo = normalizar_nombre(header)
        if not nombre_combo or re.fullmatch(
            r"caja\s*[123]", clave_normalizada(nombre_combo)
        ):
            nombre_combo = _COMBOS_CAJAS_POSICION[pos]
        for fila_idx, fila in enumerate(filas, start=inicio):
            item = fila.get(col_nombre)
            if not isinstance(item, str):
                continue
            item = normalizar_nombre(item)
            if not _es_material_valido(item):
                continue  # 'PRENDAS', 'TOTAL', 'VENTA'... etc
            if clave_normalizada(item) in _EMPAQUES_COMBO:
                plan.combos_insumos.append(
                    ComboInsumoLinea(nombre_combo, item, Decimal("1"), "CAJAS", fila_idx)
                )
            else:
                plan.combos.append(
                    ComboLinea(nombre_combo, item, Decimal("1"), "CAJAS", fila_idx)
                )


def plan_bom(libro: LibroMigracion, report=None, bloques: dict[str, tuple[str, str | None]] | None = None) -> BomPlan:
    """Aggregate the BOM plan from the bounded workbook (read-only).

    ``bloques`` maps recipe sheets to their catalog product(s); it defaults to
    ``BLOQUES_BOM`` (the same provenance F1 uses). Tests / custom mini-books
    inject their own mapping; production always uses the canonical one.
    """
    if bloques is None:
        bloques = BLOQUES_BOM
    plan = BomPlan()
    for hoja, (prod_izq, prod_der) in bloques.items():
        if hoja not in SHEET_BOUNDS:
            if report:
                report.warn(hoja, None, None, "hoja BOM sin rango registrado")
            continue
        try:
            filas = libro.leer_hoja(hoja, report=report).filas
        except HojaInexistenteError:
            if report:
                report.warn(hoja, None, None, "hoja ausente en este workbook; omitida")
            continue
        inicio = SHEET_BOUNDS[hoja][0]
        for fila_idx, fila in enumerate(filas, start=inicio):
            _procesar_bloque(plan, fila, fila_idx, hoja, prod_izq, "A", "D", report)
            if prod_der is not None:
                _procesar_bloque(plan, fila, fila_idx, hoja, prod_der, "A", "L", report)
    _plan_combos(libro, plan, report)
    return plan


# ------------------------------------------------------------------------- #
# DB apply (idempotente: NFR-1 / EX-3; variante NULL -> dedup manual)
# ------------------------------------------------------------------------- #


def _bom_insumo_existente(db, producto_id: int, insumo_id: int) -> bool:
    return (
        db.scalar(
            select(BomInsumo.id).where(
                BomInsumo.producto_id == producto_id,
                BomInsumo.insumo_id == insumo_id,
                BomInsumo.variante_id.is_(None),
            )
        )
        is not None
    )


def _bom_producto_existente(db, combo_id: int, producto_incluido_id: int) -> bool:
    return (
        db.scalar(
            select(BomProducto.id).where(
                BomProducto.combo_id == combo_id,
                BomProducto.producto_incluido_id == producto_incluido_id,
            )
        )
        is not None
    )


def _producto_por_nombre(db, nombre: str):
    return db.scalar(select(Producto).where(Producto.nombre == nombre))


def _insumo_por_nombre(db, nombre: str):
    """Insumo del catalogo por nombre canonico (alias primero, luego exacto)."""
    nombre = ALIASES_BOM_A_CATALOGO.get(clave_normalizada(nombre), nombre)
    return db.scalar(select(Insumo).where(Insumo.nombre == nombre))


def aplicar_bom(db, plan: BomPlan, report=None) -> dict[str, int]:
    """Inserta BomInsumo (recetas) y BomProducto (combos) en el caller txn.

    El caller (session_scope) controla el commit unico (EXM-4). Una fila cuyo
    producto o insumo no existe aun en el catalogo se OMITE y reporta (el
    catalogo F1 corre antes; un faltante aqui es un error de datos -> report).
    Idempotente: re-ejecutar nunca duplica (dedup manual sobre variables NULL).
    """
    res = {
        "bom_insumos": 0,
        "combos": 0,
        "combos_insumos": 0,
        "ya_exist": 0,
        "omitidos": 0,
    }
    for linea in plan.insumos:
        producto = _producto_por_nombre(db, linea.producto_nombre)
        insumo = _insumo_por_nombre(db, linea.insumo_nombre)
        if producto is None or insumo is None:
            res["omitidos"] += 1
            if report:
                report.error(
                    linea.hoja, linea.fila, None,
                    f"{linea.insumo_nombre} ({linea.producto_nombre}): producto o "
                    f"insumo ausente en catalogo; linea omitida",
                )
            continue
        if _bom_insumo_existente(db, producto.id, insumo.id):
            res["ya_exist"] += 1
            continue
        db.add(
            BomInsumo(
                producto_id=producto.id,
                insumo_id=insumo.id,
                variante_id=None,
                cantidad_requerida=linea.cantidad,
                porcentaje_desperdicio=Decimal("0"),
            )
        )
        db.flush()
        res["bom_insumos"] += 1
        if report:
            report.info(
                linea.hoja, linea.fila, None,
                f"{linea.producto_nombre}: {linea.insumo_nombre} x {linea.cantidad}",
            )

    for linea in plan.combos:
        combo = _producto_por_nombre(db, linea.combo_nombre)
        incluido = _producto_por_nombre(db, linea.producto_incluido)
        if combo is None or incluido is None:
            res["omitidos"] += 1
            if report:
                report.error(
                    linea.hoja, linea.fila, None,
                    f"combo {linea.combo_nombre}: producto "
                    f"{linea.producto_incluido} ausente en el catalogo; omitido",
                )
            continue
        if _bom_producto_existente(db, combo.id, incluido.id):
            res["ya_exist"] += 1
            continue
        db.add(
            BomProducto(
                combo_id=combo.id,
                producto_incluido_id=incluido.id,
                cantidad=linea.cantidad,
            )
        )
        db.flush()
        res["combos"] += 1

    for linea in plan.combos_insumos:
        combo = _producto_por_nombre(db, linea.combo_nombre)
        insumo = _insumo_por_nombre(db, linea.insumo_nombre)
        if combo is None or insumo is None:
            res["omitidos"] += 1
            continue
        if _bom_insumo_existente(db, combo.id, insumo.id):
            res["ya_exist"] += 1
            continue
        db.add(
            BomInsumo(
                producto_id=combo.id,
                insumo_id=insumo.id,
                variante_id=None,
                cantidad_requerida=linea.cantidad,
                porcentaje_desperdicio=Decimal("0"),
            )
        )
        db.flush()
        res["combos_insumos"] += 1

    if report:
        report.info(
            "F3", None, None,
            f"BOM aplicado: {res['bom_insumos']} BOM_Insumos, "
            f"{res['combos']} BOM_Productos, {res['combos_insumos']} empaques, "
            f"{res['ya_exist']} ya-existentes, {res['omitidos']} omitidos",
        )
    return res


# ------------------------------------------------------------------------- #
# Phase entry point (F3 runner registered in migrate/__init__.py)
# ------------------------------------------------------------------------- #


def cargar_bom(ctx: MigrationContext) -> BomPlan:
    """F3 runner: builds the BOM plan and, in commit mode, applies it inside a
    single transaction (EXM-4), idempotent (NFR-1). Dry-run writes nothing."""
    report = ctx.report
    with LibroMigracion(ctx.options.source) as libro:
        plan = plan_bom(libro, report)

    report.info(
        "F3", None, None,
        f"plan BOM: {plan.conteo_insumos} lineas insumos | "
        f"{plan.conteo_combos} items de combos | sin cantidad "
        f"{plan.sin_cantidad}",
    )
    if ctx.options.modo == "commit" and ctx.session is not None:
        with session_scope(ctx, ctx.session) as db:
            aplicar_bom(db, plan, report)
    return plan


__all__ = [
    "BomLinea",
    "ComboLinea",
    "ComboInsumoLinea",
    "BomPlan",
    "convertir_cantidad_bom",
    "plan_bom",
    "aplicar_bom",
    "cargar_bom",
]