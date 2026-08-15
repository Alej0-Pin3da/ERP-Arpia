"""F0+F1 catalog phase: bootstrap + Tipos_Producto/Insumos/Productos.

Scope of slice 3 (PR#3): ONLY the catalog phase (design #423 > catalog.py;
tasks #424 T4; spec R-CAT / CAT-1..CAT-4, EXM-1..EXM-4, NFR-1/2).

What this module does
---------------------
F0 ``bootstrap_catalog_phase``: get-or-create the 4 base categories and the
6 ``Tipos_Producto`` (Lenceria, Corseteria, Blusa, Accesorio, Set, Combo),
idempotent (spec CAT-1). Runs inside the caller transaction (never commits).

F1 ``catalogar``: builds a ``CatalogPlan`` from the bounded Excel readers and,
in commit mode, upserts inside a single ``session_scope`` (EXM-4):

- Insumos: union of BOM recipe materials (left A / right I blocks), the
  INVENTARIO OCT25 MATERIAL+HERRAJES blocks and the CAJAS packaging items.
  unidad_medida normalizada + categoria resuelta por nombre; stock_actual,
  stock_minimo y costo_promedio_actual = 0 EXPLICITOS (CAT-3; el stock/costo
  real llega con F2 compras WAC y F4 stock OCT25).
- Productos (+ variantes): from ``PRODUCTOS_CATALOGO`` (derived from the BOM
  sheet titles/blocks + the set/combo products referenced by CAJAS and
  VENTAS), dedup por (producto_id, nombre_variante); PG UNIQUE no aplica sobre
  NULL, asi que la variante NULL (producto sin variante) se protege con dedup
  manual por nombre normalizado.

Design notes / traps (verified against ARPIA.xlsx, 2026-08-08)
- BOM sheets carry the material name in the ``Producto`` column (A) plus a
  right block (I); rows with totals/profit/tallas ("COSTO TOTAL CONJUNTO",
  "GANANCIA", "Horas trabajo", "4.0", "VENTA") are junk and never insumos.
- Name units: "Encaje Elastico 19 cm negro 10 mts" -> m; "24 cm" inside a
  material name is its WIDTH, not a purchase unit (resolver_unidad only
  accepts cm when the token ends the name).
- OCT25: A=material (+B=quantity with unit), D=herrajes (+E=count).
- Empaques of the CAJAS combos (Caja, Vela, Papel, Envio) are insumos too.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import select

from app.models import (
    CategoriaInsumo,
    Insumo,
    Producto,
    TipoProducto,
    VarianteProducto,
)
from migrate.context import MigrationContext, session_scope
from migrate.loaders import SHEET_BOUNDS, HojaInexistenteError, LibroMigracion

# --------------------------------------------------------------------------- #
# Canonical catalog content (spec CAT-1..CAT-4)
# --------------------------------------------------------------------------- #

TIPOS_CATALOGO: tuple[str, ...] = (
    "Lencería",
    "Corsetería",
    "Blusa",
    "Accesorio",
    "Set",
    "Combo",
)

# Base categories from the seeder; bootstrap keeps them idempotent.
BASE_CATEGORIAS: tuple[str, ...] = ("Telas", "Herrajes", "Empaques", "Químicos")

# BOM recipe sheets that define products; SHEET_BOUNDS keeps their ranges.
HOJAS_BOM_RECETAS: tuple[str, ...] = (
    "Braleth diseño 1",
    "Noche y Dia CACHETERO",
    "Noche y Dia",
    "CORSET",
    "CORSET DOBLE CARA",
    "CORSET ARTEMISIA",
    "FALDA EMILY",
    "Corset Hypatia",
    "BUSTIER",
    "BLUSAS",
    "TOTEBAG",
    # Recalculated 16-sheet workbook (2026-08): standard BOM recipe sheets.
    "SET AELO",
    "SET OCIPETE",
    "Corset Garras",
)

# Product universe derived from the workbook (fuente = provenance sheet).
PRODUCTOS_CATALOGO: tuple[dict[str, object], ...] = (
    {"nombre": "Bralete", "tipo": "Lencería", "fuente": "'Noche y Dia' bloque BRALETE"},
    {"nombre": "Corset Artemisia", "tipo": "Corsetería", "fuente": "hoja 'CORSET ARTEMISIA'"},
    {"nombre": "Corset Hypatia", "tipo": "Corsetería", "fuente": "hoja 'Corset Hypatia'"},
    {"nombre": "Corset Garras", "tipo": "Corsetería", "fuente": "hoja 'Corset Garras'"},
    {"nombre": "Falda Emily", "tipo": "Lencería", "fuente": "hoja 'FALDA EMILY'"},
    {"nombre": "Blusa Manga Larga", "tipo": "Blusa", "fuente": "hoja 'BLUSAS' bloque MANGA LARGA"},
    {"nombre": "Blusa Manga Corta", "tipo": "Blusa", "fuente": "hoja 'BLUSAS' bloque MANGA CORTA"},
    {"nombre": "Tote Bag Arpia", "tipo": "Accesorio", "fuente": "hoja 'TOTEBAG'"},
    {"nombre": "Set Aelo", "tipo": "Set", "fuente": "VENTAS/CAJAS sobre Corset"},
    {"nombre": "Set Ocipete", "tipo": "Set", "fuente": "VENTAS/CAJAS sobre Bustier"},
    {"nombre": "Caja Despertar", "tipo": "Combo", "fuente": "hoja 'CAJAS'"},
    {"nombre": "Caja Despertar V2", "tipo": "Combo", "fuente": "hoja 'CAJAS'"},
    {"nombre": "Caja Saca Las Garras", "tipo": "Combo", "fuente": "hoja 'CAJAS' / VENTAS"},
)

# --------------------------------------------------------------------------- #
# Pure normalization (dedup keys are accent/case-insensitive)
# --------------------------------------------------------------------------- #

# P1 fix (remediacion EXM-1): sinonimos de la palabra 'numero' como ORDINAL.
# 'Argolla numero 10 mm' significa 'argolla numero 10' (el numero 10), no un
# valor fijo: la palabra (numero/nro/num/No./Nro.) se ELIMINA cuando precede a
# un digito, unificando variantes ortograficas de un mismo material en la clave
# (compra 'Argolla numero 10 mm' == BOM 'Argolla 10 mm'). Se aplica SOLO en la
# clave de dedup (el display name conserva la grafia original del Excel).
_SINONIMOS_NUMERO_RE = re.compile(r"\b(?:numero|nro|num|no)\s*\.?\s+(?=\d)|nº\s+(?=\d)|n°\s+(?=\d)")


def normalizar_nombre(texto: object) -> str:
    """Collapse whitespace preserving accents and case (display name)."""
    if texto is None:
        return ""
    return re.sub(r"\s+", " ", str(texto).strip())


def clave_normalizada(nombre: object) -> str:
    """Accent/case-insensitive dedup key (Lenceria==Lenceria, Tela==tela).

    Tambien colapsa las variantes ortograficas del ordinal 'numero' cuando
    preceden a un digito (P1 fix): 'Argolla numero 10 mm' == 'Argolla 10 mm'.
    """
    texto = normalizar_nombre(nombre).casefold()
    texto = "".join(
        ch for ch in unicodedata.normalize("NFD", texto) if unicodedata.category(ch) != "Mn"
    )
    return _SINONIMOS_NUMERO_RE.sub("", texto)


# --------------------------------------------------------------------------- #
# Unit resolution (pure)
# --------------------------------------------------------------------------- #

_UNIDAD_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\d+(?:[.,]\d+)?\s*(?:mts?|metros?)\b"), "m"),
    (re.compile(r"\d+(?:[.,]\d+)?\s*kg\b"), "kg"),
    (re.compile(r"\d+(?:[.,]\d+)?\s*(?:cm2|cm\xb2)\b"), "cm2"),
    (re.compile(r"\d+(?:[.,]\d+)?\s*(?:unidades?|unid(?:ades)?|unds?|und)\b"), "un"),
    (re.compile(r"\d+(?:[.,]\d+)?\s*g\b"), "g"),
]
_CM_FIN_RE = re.compile(r"\d+(?:[.,]\d+)?\s*,?\s*cms?\s*$")


def resolver_unidad(nombre: object) -> str | None:
    """Purchase unit hinted by the material name.

    Only the LAST quantity+unit occurrence is meaningful: "Encaje ... 10 mts"
    -> m; "Sesgo de 2cm" (token at the END) -> cm; "24 cm tul bordado" is a
    WIDTH, not a unit -> None (caller falls back to the category default).
    """
    texto = clave_normalizada(nombre)
    if not texto:
        return None
    for patron, unidad in _UNIDAD_PATTERNS:
        if patron.search(texto):
            return unidad
    if _CM_FIN_RE.search(texto):
        return "cm"
    return None


def _unidad_de_cantidad(cantidad: object) -> str | None:
    """Unit embedded in an explicit quantity cell (OCT25 '11 mts' / count)."""
    if cantidad is None:
        return None
    if isinstance(cantidad, (int, float, Decimal)):
        return None  # bare number: unit comes from the category default
    texto = str(cantidad).strip()
    if not texto or texto.isdigit():
        return None
    return resolver_unidad(texto)


# --------------------------------------------------------------------------- #
# Category + canonical unit classification (pure, TDD-friendly)
# --------------------------------------------------------------------------- #

_CATEGORIA_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Empaques": (
        "gafete",
        "caja",
        "bolsa",
        "papel",
        "vela",
        "etiqueta",
        "sticker",
        "tarjeta",
        "empaque",
        "envoltura",
        "envio",
    ),
    "Herrajes": (
        "argolla",
        "tensor",
        "aro",
        "varilla",
        "gancho",
        "ocho",
        "zeta",
        "boton",
        "cremallera",
        "cadena",
        "cierre",
        "tapa",
        "tubo",
        "mosqueton",
        "ojal",
        "broche",
        "velcro",
        "cordon",
        "puntilla",
    ),
    "Telas": (
        "tela",
        "tul",
        "encaje",
        "satin",
        "malla",
        "gasa",
        "velo",
        "franela",
        "lycra",
        "maya",
        "poli",
        "gabardina",
        "entretela",
        "lino",
        "algodon",
        "jersey",
        "pitillo",
        "sesgo",
        "elastico",
        "contorno",
        "framilon",
        "cinta",
        "tira",
        "mallas",
    ),
    "Químicos": ("quimico", "tinte", "pegante", "silicona", "pintura"),
}

_UNIDAD_FINAL_POR_CATEGORIA: dict[str, str] = {
    "Telas": "m",
    "Herrajes": "un",
    "Empaques": "un",
    "Químicos": "kg",
}

# Continuous materials the workbook buys in METROS and consumes in cm in the
# BOM, but whose names hit a generic Herrajes keyword (cadena/cremallera/
# ojal). Key: clave_normalizada -> (categoria, unidad). Herrajes by piece
# sharing the same keyword (deslizadores cremallera, ojales metalicos,
# Terminales de cordon) are NOT overridden. Verified against ARPIA.xlsx
# 2026-08: 'Cadena plateada gruesa totebag' 1 mts / BOM 48 cm, 'Cremallera
# num 3' 10 mts / BOM 40 cm, 'Sesgo rigido para ojales corset' 10 mts / BOM
# 30 cm. Before this override the purchases were excluded (EXM-2), the
# insumo kept stock 0 and F5 failed with InsufficientStockError.
_CLASIFICACION_FORZADA: dict[str, tuple[str, str]] = {
    clave_normalizada("Cadena plateada gruesa totebag"): ("Telas", "m"),
    clave_normalizada("Cadena gris delgada totebag"): ("Telas", "m"),
    clave_normalizada("Cremallera num 3"): ("Telas", "m"),
    clave_normalizada("Sesgo rigido para ojales corset"): ("Telas", "m"),
    clave_normalizada("Tapavarilla negro 10 mts"): ("Telas", "m"),
}


def _categoria_por_nombre(nombre: str) -> str | None:
    texto = clave_normalizada(nombre)
    for categoria, palabras in _CATEGORIA_KEYWORDS.items():
        for palabra in palabras:
            if palabra in texto:
                return categoria
    return None


def clasificar_material(nombre: object, cantidad: object = None) -> tuple[str, str]:
    """(categoria, unidad_medida) for an insumo name (spec CAT-3, design D4).

    Category by name keywords; fallback keyed on the unit hint. The canonical
    unit per category wins: Telas -> m, Herrajes -> un (cm2 if explicit),
    Empaques -> un, Quimicos -> kg.
    """
    texto = normalizar_nombre(nombre)
    unidad_hint = resolver_unidad(texto) or _unidad_de_cantidad(cantidad)
    # Forzado por nombre: materiales continuos por metro que las keywords
    # genericas de Herrajes pondrian en Herrajes/un (ver _CLASIFICACION_FORZADA).
    forzada = _CLASIFICACION_FORZADA.get(clave_normalizada(texto))
    if forzada is not None:
        return forzada
    categoria = _categoria_por_nombre(texto)
    if categoria is None:
        if unidad_hint in ("m", "cm"):
            categoria = "Telas"
        elif unidad_hint in ("kg", "g"):
            categoria = "Químicos"
        elif unidad_hint == "cm2":
            categoria = "Herrajes"
        else:
            categoria = "Telas"  # default conservador: insumos BOM son telas
    if categoria == "Herrajes" and unidad_hint == "cm2":
        return categoria, "cm2"
    return categoria, _UNIDAD_FINAL_POR_CATEGORIA[categoria]


# --------------------------------------------------------------------------- #
# BOM junk-row filter (material names only)
# --------------------------------------------------------------------------- #

_JUNK_SUBCADENA = (
    "costo total",
    "ganancia",
    "precio",
    "venta",
    "total conjunto",
    "total blusa",
    "hora de trabajo",
    "horas de trabajo",
    "trabajo",
)
_JUNK_EXACTOS = frozenset(
    {
        "total",
        "ganancia",
        "venta",
        "precio",
        "costo",
        "arpia",
        "mar",
        "vlq",
        "material",
        "herrajes",
        "prendas",
        "xs",
        "s",
        "m",
        "l",
        "xl",
        "xxl",
        "xxs",
        "tipo",
        "ur",
        "requiere",
        "ubicacion",
    }
)


def filtrar_materiales_validos(filas: Iterable[dict[str, object]]) -> list[str]:
    """Filter BOM material rows (keys A and I), removing junk rows."""
    resultado: list[str] = []
    for fila in filas:
        for col in ("A", "I"):
            valor = fila.get(col)
            if not isinstance(valor, str):
                continue
            nombre = normalizar_nombre(valor)
            if not _es_material_valido(nombre):
                continue
            if nombre not in resultado:
                resultado.append(nombre)
    return resultado


def _es_material_valido(nombre: str) -> bool:
    if not nombre:
        return False
    if re.fullmatch(r"\d+(?:[.,]\d+)?", nombre):
        return False  # "4.0", "0"
    bajo = nombre.casefold()
    if bajo in _JUNK_EXACTOS:
        return False
    for parte in _JUNK_SUBCADENA:
        if parte in bajo:
            return False
    return True


# --------------------------------------------------------------------------- #
# Plan model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class InsumoPlan:
    nombre: str
    unidad: str
    categoria: str


@dataclass(frozen=True)
class ProductoPlan:
    nombre: str
    tipo: str
    variantes: tuple[str, ...] = ()


@dataclass
class CatalogPlan:
    """What the phase would upsert (dry-run plan / commit input)."""

    tipos: list[str] = field(default_factory=lambda: list(TIPOS_CATALOGO))
    insumos: list[InsumoPlan] = field(default_factory=list)
    productos: list[ProductoPlan] = field(default_factory=list)

    @property
    def conteo_tipos(self) -> int:
        return len(self.tipos)

    @property
    def conteo_insumos(self) -> int:
        return len(self.insumos)

    @property
    def conteo_productos(self) -> int:
        return len(self.productos)


# --------------------------------------------------------------------------- #
# Workbook -> plan (bounded read, pure aggregate)
# --------------------------------------------------------------------------- #

_CAJAS_EMPAQUES = frozenset({"caja", "vela", "papel", "envio", "bolsa", "etiqueta", "tarjeta"})


def _leer_materiales(libro: LibroMigracion, report) -> dict[str, str]:
    """nombre normalizado -> nombre display, union BOM + OCT25 + CAJAS."""

    def filas_de(hoja: str) -> list[dict[str, object]]:
        try:
            return libro.leer_hoja(hoja, report=report).filas
        except HojaInexistenteError:
            if report:
                report.warn(hoja, None, None, "hoja ausente en este workbook; omitida")
            return []

    nombres: dict[str, str] = {}
    for hoja in HOJAS_BOM_RECETAS:
        if hoja not in SHEET_BOUNDS:
            if report:
                report.warn(hoja, None, None, "hoja BOM sin rango registrado; no leida")
            continue
        for nombre in filtrar_materiales_validos(filas_de(hoja)):
            nombres.setdefault(clave_normalizada(nombre), nombre)
    if "INVENTARIO OCT25" in SHEET_BOUNDS:
        # Layout real (verificado contra ARPIA.xlsx, 2026-08-08): MATERIAL
        # nombre=B cantidad=D ('11 mts'); HERRAJES nombre=F cantidad=H (numero).
        # D/H son cantidades, NUNCA nombres de insumo (antes se leia A/D y la
        # cantidad '9,5 mts' de D entraba como material falso).
        for fila in filas_de("INVENTARIO OCT25"):
            for col_nombre in ("B", "F"):
                valor = fila.get(col_nombre)
                if not isinstance(valor, str):
                    continue
                nombre = normalizar_nombre(valor)
                if not _es_material_valido(nombre):
                    continue
                nombres.setdefault(clave_normalizada(nombre), nombre)
    if "CAJAS" in SHEET_BOUNDS:
        # CAJAS has no column A: combo members live in the (nombre, costo,
        # precio) name columns B/F/J (design F3, same columns bom.py reads).
        # Only the packaging items enter the F1 insumo universe; the combo
        # products (Bralete/Set Aelo/...) come from PRODUCTOS_CATALOGO.
        for fila in filas_de("CAJAS"):
            for col_nombre in ("B", "F", "J"):
                valor = fila.get(col_nombre)
                if not isinstance(valor, str):
                    continue
                nombre = normalizar_nombre(valor)
                if clave_normalizada(nombre) in _CAJAS_EMPAQUES:
                    nombres.setdefault(clave_normalizada(nombre), nombre)
    return nombres


def leer_insumos_plan(nombres: dict[str, str]) -> list[InsumoPlan]:
    plan: dict[str, InsumoPlan] = {}
    for nombre in nombres.values():
        categoria, unidad = clasificar_material(nombre)
        plan[clave_normalizada(nombre)] = InsumoPlan(
            nombre=nombre, unidad=unidad, categoria=categoria
        )
    return sorted(plan.values(), key=lambda i: i.nombre.casefold())


def plan_catalogo(libro: LibroMigracion, report=None) -> CatalogPlan:
    """Aggregate the catalog plan from the bounded workbook (read-only)."""
    materiales = _leer_materiales(libro, report)
    insumos = leer_insumos_plan(materiales)
    productos = [
        ProductoPlan(
            nombre=normalizar_nombre(entry["nombre"]),
            tipo=str(entry["tipo"]),
            variantes=tuple(v for v in entry.get("variantes", ()) if v),
        )
        for entry in PRODUCTOS_CATALOGO
    ]
    return CatalogPlan(
        insumos=insumos,
        productos=productos,
    )


# --------------------------------------------------------------------------- #
# DB upserts (idempotentes por clave natural / normalizada)
# --------------------------------------------------------------------------- #


def _get_or_create(db, model, nombre: str):
    limpio = normalizar_nombre(nombre)
    ent = db.scalar(select(model).where(model.nombre == limpio))
    if ent is None:
        ent = model(nombre=limpio)
        db.add(ent)
        db.flush()
    return ent


def bootstrap_catalogo(db, report=None) -> dict[str, int]:
    """F0 core: categorias base + Tipos_Producto, idempotente (CAT-1)."""
    for nombre_cat in BASE_CATEGORIAS:
        _get_or_create(db, CategoriaInsumo, nombre_cat)
    for nombre_tipo in TIPOS_CATALOGO:
        _get_or_create(db, TipoProducto, nombre_tipo)
    return {"categorias": len(BASE_CATEGORIAS), "tipos": len(TIPOS_CATALOGO)}


def upsert_insumo(
    db,
    nombre,
    unidad: str | None = None,
    categoria_nombre: str | None = None,
) -> Insumo:
    """get-or-create an insumo by normalized name (dedup manual).

    CAT-3: unidad normalizada; stock_actual / stock_minimo / costo_promedio_actual
    se persisten como 0 EXPLICITOS al crearlo (los valores reales llegan con
    F2 compras WAC y F4 stock OCT25). No hay UNIQUE sobre Insumos.nombre, asi
    que la dedup es manual por nombre normalizado.
    """
    nombre_limpio = normalizar_nombre(nombre)
    if categoria_nombre is None:
        categoria_nombre, _ = clasificar_material(nombre_limpio)
    if unidad is None:
        _, unidad = clasificar_material(nombre_limpio)
    cat_objeto = _get_or_create(db, CategoriaInsumo, categoria_nombre)
    insumo = db.scalar(select(Insumo).where(Insumo.nombre == nombre_limpio))
    if insumo is None:
        insumo = Insumo(
            nombre=nombre_limpio,
            categoria_id=cat_objeto.id,
            unidad_medida=unidad,
            stock_actual=Decimal("0"),
            stock_minimo=Decimal("0"),
            costo_promedio_actual=Decimal("0"),
        )
        db.add(insumo)
        db.flush()
    return insumo


def upsert_producto(
    db,
    nombre,
    tipo: str,
    variantes: Iterable[str] = (),
    precio_sugerido: Decimal | None = None,
) -> Producto:
    """get-or-create a Producto (+ Variantes) with manual dedup (CAT-4).

    Variante NULL protegida: un producto sin variantes no recibe una fila
    VarianteProducto fantasma; crearlo dos veces produce 1 fila (PG UNIQUE no
    aplica sobre NULLs). Las variantes se deduplican por (producto_id,
    nombre_variante) con guard manual antes del UNIQUE.
    """
    nombre_limpio = normalizar_nombre(nombre)
    tipo_objeto = _get_or_create(db, TipoProducto, tipo)
    producto = db.execute(
        select(Producto).where(Producto.nombre == nombre_limpio)
    ).scalar_one_or_none()
    if producto is None:
        producto = Producto(
            nombre=nombre_limpio,
            tipo_producto_id=tipo_objeto.id,
            requiere_fabricacion=True,
            costos_operativos_fijos=Decimal("0"),
            precio_venta_sugerido=(
                precio_sugerido if precio_sugerido is not None else Decimal("0")
            ),
        )
        db.add(producto)
        db.flush()
    elif producto.tipo_producto_id != tipo_objeto.id:
        producto.tipo_producto_id = tipo_objeto.id
        db.flush()

    existentes = {
        v.nombre_variante: v
        for v in db.execute(
            select(VarianteProducto).where(VarianteProducto.producto_id == producto.id)
        )
        .scalars()
        .all()
    }
    for nombre_variante in variantes:
        limpio = normalizar_nombre(nombre_variante)
        if not limpio or limpio in existentes:
            continue
        var = VarianteProducto(producto_id=producto.id, nombre_variante=limpio)
        db.add(var)
        db.flush()
        existentes[limpio] = var
    producto.variantes = list(existentes.values())
    return producto


def aplicar_plan(db, plan: CatalogPlan, report=None) -> dict[str, int]:
    """Upsert everything in the plan inside the caller transaction (EXM-4)."""
    bootstrap_catalogo(db, report)
    totales = {"insumos": 0, "productos": 0, "variantes": 0}
    for insumo in plan.insumos:
        upsert_insumo(db, insumo.nombre, unidad=insumo.unidad, categoria_nombre=insumo.categoria)
        totales["insumos"] += 1
    for producto in plan.productos:
        upsert_producto(db, producto.nombre, producto.tipo, producto.variantes)
        totales["productos"] += 1
        totales["variantes"] += len(producto.variantes)
    if report:
        report.info(
            "F1",
            None,
            None,
            f"upsert aplicados: {totales['insumos']} insumos, "
            f"{totales['productos']} productos, "
            f"{totales['variantes']} variantes",
        )
    return totales


# --------------------------------------------------------------------------- #
# Phase entry points (F0 / F1 runners, registered in migrate/__init__.py)
# --------------------------------------------------------------------------- #


def bootstrap_catalog_phase(ctx: MigrationContext) -> None:
    """F0: bootstrap (categorias + Tipos_Producto), idempotente, sin Excel."""
    if ctx.session is None:
        ctx.report.info(
            "F0",
            None,
            None,
            f"plan bootstrap: {len(BASE_CATEGORIAS)} categorias + "
            f"{len(TIPOS_CATALOGO)} Tipos_Producto (dry-run, 0 escrituras)",
        )
        return
    with session_scope(ctx, ctx.session) as db:
        bootstrap_catalogo(db)
    ctx.report.info("F0", None, None, "bootstrap aplicado (categorias + Tipos_Producto upsert)")


def catalogar(ctx: MigrationContext) -> CatalogPlan:
    """F1: catalog phase. Builds the plan from the bounded workbook; in commit
    mode applies it inside a single transaction (EXM-4) and is idempotent
    (NFR-1). In dry-run only the plan is reported (NFR-2), 0 rows written."""
    report = ctx.report
    with LibroMigracion(ctx.options.source) as libro:
        plan = plan_catalogo(libro, report)

    report.info(
        "F1",
        None,
        None,
        f"plan catalogo: {plan.conteo_insumos} insumos, "
        f"{plan.conteo_productos} productos, "
        f"{plan.conteo_tipos} tipos",
    )
    if ctx.options.modo == "commit" and ctx.session is not None:
        with session_scope(ctx, ctx.session) as db:
            aplicar_plan(db, plan, report)
    return plan


__all__ = [
    "BASE_CATEGORIAS",
    "TIPOS_CATALOGO",
    "PRODUCTOS_CATALOGO",
    "normalizar_nombre",
    "clave_normalizada",
    "resolver_unidad",
    "clasificar_material",
    "filtrar_materiales_validos",
    "InsumoPlan",
    "ProductoPlan",
    "CatalogPlan",
    "plan_catalogo",
    "bootstrap_catalogo",
    "bootstrap_catalog_phase",
    "upsert_insumo",
    "upsert_producto",
    "aplicar_plan",
    "catalogar",
]
