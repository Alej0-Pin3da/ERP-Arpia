"""F2 purchases phase: historical BOM purchases -> WAC (spec EXM-2/3/4/5, D1/D5).

Scope of slice 4 (PR#4): ONLY phase 2 (tasks #424 T5; design #423 purchases.py).

What this module does
---------------------
F2 builds an idempotent ``ComprasPlan`` from the purchase sheets of the Excel
and, in commit mode, registers the purchases through
``wac.registrar_compra(..., fecha_compra=..., commit=False)`` inside a single
``session_scope`` (EXM-4). The WAC formula lives in the service (untouched).

Filtering (design D4 / spec 'compras-insumos'): ONLY catalog (BOM) insumos
enter WAC. A row whose name is not in the F1 catalog universe (equipment,
cursos, hosting, prestamo, ...) is EXCLUDED here and goes to
Movimientos_Financieros in a later phase (F6). The right-hand sub-tables
(VALQUI J..N, MARGARA H..o) are price lists / summarized duplicates of the
left block (same insumo, same total, expressed in cm or cm2); loading them
would double-count WAC, so they are counted and never registered.

Quantity (EXM-2): the cell may be a bare number (12) -> taken as-is in the
insumo's canonical unit; or a quantity+unit string ('4 mts', '50 cm',
'2,90 mts') converted to the canonical unit of the insumo (Telas -> m,
Herrajes -> un/cm2, Empaques -> un). Uninterpretable values (None, #DIV/0!,
junk) stop the row: reported and excluded (never inferred).

Prices: the sheets carry the TOTAL cost per row (VALQUI col D / MARCARA
col C). Unit price handed to the service = total/cantidad, matching the unit
price semantics of CompraInsumo (cantidad_comprada * precio_unitario_compra).

Fechas (D5 - never now()): the real Excel date is preserved (VALQUI col E /
MARCARA col D). Empty date: inherited from the contiguous earlier row of the
same (insumo, proveedor) via normalize.fecha_para_fila; if there is no such
row the purchase is OMITTED + WARN (a purchase without a date would break the
chronological WAC cut at OCT25).

Idempotencia (NFR-1/EXM-3): natural key (insumo_id, fecha_compra, cantidad,
precio) — re-running the phase never duplicates stock/cost.

Transactions: the caller owns the commit; per-row ``savepoint`` isolates a
failing purchase so one bad row cannot roll back the whole phase, and the
enclosing ``session_scope`` commits once at the end (EXM-4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select

from app.models import CompraInsumo, Insumo, Proveedor
from app.services.wac import registrar_compra
from migrate.catalog import _leer_materiales, clave_normalizada, normalizar_nombre
from migrate.context import MigrationContext, savepoint, session_scope
from migrate.loaders import HojaInexistenteError, LibroMigracion, SHEET_BOUNDS
from migrate.normalize import (
    ClaveFecha,
    coerce_aware,
    fecha_para_fila,
    normalizar_area_m2,
    normalizar_decimal,
    parsear_cantidad_unidad,
    unidad_canonica,
)

# Purchase sheets: (hoja, col_cantidad, col_nombre, col_costo, col_fecha, col_prov).
HOJAS_COMPRAS: tuple[tuple[str, str, str, str, str, str], ...] = (
    ("INVERSION VALQUI", "A", "B", "D", "E", "F"),
    ("INVERSION MARGARA", "A", "B", "C", "D", "E"),
)

# Right-hand sub-tables (J..N in VALQUI, H..o in MARGARA): price lists that
# duplicate the left block; they never become purchases (see module docstring).
_COLS_DERECHA = frozenset("JKLMN")


@dataclass(frozen=True)
class CompraPlan:
    """One planned historical purchase (precio_unitario = costo_total / cant)."""

    insumo_nombre: str
    cantidad: Decimal
    precio_unitario: Decimal
    fecha: datetime | None
    proveedor_nombre: str | None
    hoja: str
    fila: int
    fecha_heredada: bool = False


@dataclass
class ConteosCompras:
    """Counters of the phase (reporte N7a / EXM-1)."""

    no_bom: int = 0         # no esta en el catalogo F1 -> finanzas (F6)
    derecha: int = 0         # filas de la sub-tabla derecha ignoradas
    sin_cantidad: int = 0    # cantidad/costo no interpretable (EXM-2)
    sin_fecha: int = 0       # fecha vacia sin contigua heredable (D5) -> omitida
    planificadas: int = 0    # filas que entran al plan (BOM ok)


@dataclass
class ComprasPlan:
    """Plan (dry-run) of the historical purchases F2 would register."""

    compras: list[CompraPlan] = field(default_factory=list)
    conteos: ConteosCompras = field(default_factory=ConteosCompras)

    @property
    def conteo_compras(self) -> int:
        return len(self.compras)


# --------------------------------------------------------------------------- #
# Pure quantity normalization (EXM-2)
# --------------------------------------------------------------------------- #


def normalizar_cantidad_compra(celda: object, unidad_objetivo: str) -> Decimal | None:
    """Cantidad en la unidad canonica del insumo (nunca inferida, EXM-2).

    - number (int/float/Decimal): taken as-is (asumida la unidad objetivo).
    - '4 mts' / '2,90 mts' / '50 cm': parsed, raw unit mapped via
      ``unidad_canonica``; converted when both are length (cm -> m; 100 cm = 1 m).
    - '50 x 280 cm' (expresion area en telas, EXM-2 borde / design D4): solo
      cuando la unidad objetivo es 'm', se interpreta como area -> m2
      (50*280/10000 = 1.4). Caso real: INVERSION MARGARA A7.
    - None, '#DIV/0!', o texto sin cantidad+unidad interpretable -> None.
    """
    if celda is None:
        return None
    if isinstance(celda, (int, float, Decimal)):
        valor = normalizar_decimal(celda)
        return valor if (valor is not None and valor > 0) else None
    texto = str(celda).strip()
    if not texto or texto.startswith("#"):
        return None
    objetivo = unidad_canonica(unidad_objetivo)
    # EXM-2 borde: expresion de area en telas -> m2 (regla por hoja/tipo).
    if objetivo == "m":
        area = normalizar_area_m2(texto)
        if area is not None:
            return area
    cu = parsear_cantidad_unidad(texto)
    if cu is None:
        return None
    u = unidad_canonica(cu.unidad)
    if u == objetivo:
        return cu.cantidad
    # Conversion de longitud a metro (Telas -> m); otros pares se rechazan.
    if objetivo == "m" and u == "cm":
        return cu.cantidad * Decimal("0.01")
    return None


def _unidad_de_insumo(nombre: str) -> str:
    """Unidad canonica del insumo (mismo clasificador que F1, design D4)."""
    from migrate.catalog import clasificar_material

    try:
        return clasificar_material(nombre)[1]
    except Exception:
        return "un"


# --------------------------------------------------------------------------- #
# Workbook -> plan (bounded reading, pure aggregate)
# --------------------------------------------------------------------------- #


def _es_subtabla_derecha(fila: dict[str, object]) -> bool:
    """True si la fila solo tiene celdas de la sub-tabla derecha (J..M) y no del
    bloque izquierdo (A..F): es una fila de la lista de precios duplicada."""
    izquierda = any(col in fila for col in ("A", "B", "C", "D", "E", "F"))
    derecha = any(col in _COLS_DERECHA for col in fila)
    return derecha and not izquierda


def _universo_bom(libro, report) -> dict[str, str]:
    """clave normalizada -> nombre display (el mismo universo que cataloga F1:
    recetas BOM + OCT25 + CAJAS)."""
    return {
        clave_normalizada(v): v for v in _leer_materiales(libro, report).values()
    }


def plan_compras(libro, report=None) -> ComprasPlan:
    """Build the purchase plan from the bounded workbook (read-only).

    Solo el bloque izquierdo de las hojas de compra; cada fila se filtra por el
    universo BOM; fechas bajo politica D5; never now().
    """
    plan = ComprasPlan()
    conteos = plan.conteos
    universo = _universo_bom(libro, report)

    for hoja, col_cant, col_nom, col_costo, col_fecha, col_prov in HOJAS_COMPRAS:
        if hoja not in SHEET_BOUNDS:
            continue
        try:
            lectura = libro.leer_hoja(hoja, report=report)
        except HojaInexistenteError:
            if report:
                report.warn(hoja, None, None, "hoja ausente en este workbook; omitida")
            continue
        filas = lectura.filas
        ultima_fecha: dict[ClaveFecha, object] = {}
        for indx, fila in enumerate(filas, start=SHEET_BOUNDS[hoja][0]):
            if _es_subtabla_derecha(fila):
                conteos.derecha += 1
                continue
            cantidad_raw = fila.get(col_cant)
            if cantidad_raw is None and hoja == "INVERSION VALQUI":
                # Bloque Kilotelas (R56-78): la cantidad va en C cuando A esta vacia.
                cantidad_raw = fila.get("C")
            nombre = fila.get(col_nom)
            if not isinstance(nombre, str):
                continue
            clave_ins = clave_normalizada(nombre)
            if clave_ins not in universo:
                conteos.no_bom += 1
                continue
            nombre_display = universo[clave_ins]
            unidad_obj = _unidad_de_insumo(nombre_display)
            cantidad = normalizar_cantidad_compra(cantidad_raw, unidad_obj)
            if cantidad is None:
                conteos.sin_cantidad += 1
                if report:
                    report.warn(
                        hoja, indx, col_cant,
                        f"{nombre_display}: cantidad {cantidad_raw!r} no interpretable; "
                        f"fila excluida (EXM-2)",
                    )
                continue
            costo_total = normalizar_decimal(fila.get(col_costo))
            if costo_total is None or costo_total <= 0:
                conteos.sin_cantidad += 1
                if report:
                    report.warn(
                        hoja, indx, col_costo,
                        f"{nombre_display}: costo no interpretable; fila excluida",
                    )
                continue
            precio_unitario = costo_total / cantidad

            proveedor_raw = fila.get(col_prov)
            proveedor_nombre = (
                normalizar_nombre(proveedor_raw)
                if proveedor_raw is not None
                else None
            )
            fecha_raw = fila.get(col_fecha)
            clave_f = ClaveFecha(clave_ins, proveedor_nombre or "<sin-proveedor>")
            fecha = fecha_para_fila(fecha_raw, clave_f, ultima_fecha)
            if fecha is None:
                conteos.sin_fecha += 1
                if report:
                    report.warn(
                        hoja, indx, col_fecha,
                        f"{nombre_display}: fecha vacia y sin fila contigua del mismo "
                        f"insumo+proveedor; omitida (D5, nunca now())",
                    )
                continue
            # Fecha del Excel (posible naive) -> aware (TIMESTAMPTZ, sin ambiguedad).
            fecha = coerce_aware(fecha)
            plan.compras.append(
                CompraPlan(
                    insumo_nombre=nombre_display,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    fecha=fecha,
                    proveedor_nombre=proveedor_nombre,
                    hoja=hoja,
                    fila=indx,
                    fecha_heredada=fecha_raw is None,
                )
            )
            conteos.planificadas += 1
    return plan


# ------------------------------------------------------------------------- #
# DB apply (idempotente: NFR-1 / EXM-3)
# ------------------------------------------------------------------------- #


def _clave_compra_existente(
    db, insumo_id: int, fecha, cantidad: Decimal, precio: Decimal
) -> bool:
    """Check natural key (insumo, fecha, cantidad, precio) in the DB."""
    if fecha is None:
        return False
    fila = db.scalar(
        select(CompraInsumo.id).where(
            CompraInsumo.insumo_id == insumo_id,
            CompraInsumo.fecha_compra == fecha,
            CompraInsumo.cantidad_comprada == cantidad,
            CompraInsumo.precio_unitario_compra == precio,
        )
    )
    return fila is not None


def _proveedor_id(db, nombre: str | None) -> int | None:
    """ID del proveedor catalogado (por clave normalizada); None si aun no se
    catalogo (F6 lo enriquece; aqua no se crea cat.-supplier)."""
    if not nombre:
        return None
    clave = clave_normalizada(nombre)
    for prov in db.scalars(select(Proveedor)).all():
        if clave_normalizada(prov.nombre) == clave:
            return prov.id
    return None


def aplicar_compras(db, plan: ComprasPlan, report=None) -> dict[str, int]:
    """Registra las compras a WAC por fila (commit=False, savepoint por fila).

    El caller (session_scope) controla el commit unico. Idempotente por clave
    natural. Una fila con error revierte SOLO su savepoint y se reporta ERROR.
    """
    res = {"insertadas": 0, "omitidas": 0, "ya_exist": 0}
    for compra in plan.compras:
        insumo = db.scalar(select(Insumo).where(Insumo.nombre == compra.insumo_nombre))
        if insumo is None:
            res["omitidas"] += 1
            if report:
                report.error(
                    compra.hoja, compra.fila, None,
                    f"{compra.insumo_nombre}: insumo ausente en catalogo; no registrada",
                )
            continue
        proveedor_id = _proveedor_id(db, compra.proveedor_nombre)
        if _clave_compra_existente(
            db, insumo.id, compra.fecha, compra.cantidad, compra.precio_unitario
        ):
            res["ya_exist"] += 1
            continue
        try:
            with savepoint(db):
                registrar_compra(
                    db,
                    insumo.id,
                    proveedor_id,
                    compra.cantidad,
                    compra.precio_unitario,
                    fecha_compra=compra.fecha,
                    commit=False,
                )
            res["insertadas"] += 1
            if report:
                report.info(
                    compra.hoja, compra.fila, None,
                    f"compra {compra.insumo_nombre}: {compra.cantidad} "
                    f"@ {compra.precio_unitario:.2f} fecha "
                    f"{compra.fecha.date() if compra.fecha else '?'}"
                    f"{' (fecha heredada)' if compra.fecha_heredada else ''}",
                )
        except Exception as exc:  # savepoint revierte solo esta fila
            res["omitidas"] += 1
            if report:
                report.error(
                    compra.hoja, compra.fila, None,
                    f"{compra.insumo_nombre}: {type(exc).__name__}: {exc}",
                )
    if report:
        report.info(
            "F2", None, None,
            f"compras aplicadas: {res['insertadas']} insertadas, "
            f"{res['ya_exist']} ya-existentes, {res['omitidas']} omitidas",
        )
    return res


# ------------------------------------------------------------------------- #
# Phase entry point (F2 runner registered in migrate/__init__.py)
# ------------------------------------------------------------------------- #


def cargar_compras(ctx: MigrationContext) -> ComprasPlan:
    """F2 runner: builds the purchase plan and, in commit mode, applies it in a
    single transaction (EXM-4), idempotent (NFR-1). In dry-run nothing is
    written (NFR-2)."""
    report = ctx.report
    with LibroMigracion(ctx.options.source) as libro:
        plan = plan_compras(libro, report)

    report.info(
        "F2", None, None,
        f"plan compras WAC: {plan.conteo_compras} compras BOM | "
        f"no-BOM {plan.conteos.no_bom} (-> finanzas F6) | sub-tabla derecha "
        f"{plan.conteos.derecha} | cant sin interpretar "
        f"{plan.conteos.sin_cantidad} | sin fecha {plan.conteos.sin_fecha}",
    )
    if ctx.options.modo == "commit" and ctx.session is not None:
        with session_scope(ctx, ctx.session) as db:
            aplicar_compras(db, plan, report)
    return plan


__all__ = [
    "CompraPlan",
    "ConteosCompras",
    "ComprasPlan",
    "normalizar_cantidad_compra",
    "plan_compras",
    "aplicar_compras",
    "cargar_compras",
]