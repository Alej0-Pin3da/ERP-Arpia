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
Movimientos_Financieros in a later phase (F6).

Sub-tablas derechas (P1 fix de remediacion): ya NO se descartan todas. La
sub-tabla derecha de VALQUI (J..N: Producto/Largo CMS/Ancho CMS/Valor) y la de
MARGARA (H..L: Cantidad/Producto/Costo/Fecha/Provedor) son fuentes de compra
SOLO cuando el item de la derecha NO aparece en el bloque izquierdo de la
MISMA hoja (es fuente unica, no duplicado). Cuando la derecha duplica algo ya
comprado a la izquierda (mismo item en la misma hoja) se descarta como antes
(duplicado). Cantidad derecha VALQUI: K es 'Largo CMS' -> en la unidad
canonica del insumo (Herrajes 'un' -> K piezas; Telas 'm' -> K cm / 100;
'cm2' -> K x L). Precio unitario = M / cantidad. Fecha/proveedor: los del
bloque izquierdo de la misma fila (VALQUI) o propios K/L (MARGARA).
Caso real: 'Argolla 10 mm' R18 (J18) es fuente unica -> compra 100 un @ 72;
'Ref 100 24 cm tul bordado negro' R34 duplica la compra izquierda B80 -> se
descarta.

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
from migrate.catalog import (
    _es_material_valido,
    _leer_materiales,
    clave_normalizada,
    normalizar_nombre,
)
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

# Right-hand sub-tables (P1 fix). Layout real verificado en ARPIA.xlsx:
# - VALQUI J..N: J=Producto, K=Largo CMS, L=Ancho CMS, M=Valor (N=Unitario).
#   La cantidad K es 'Largo CMS': conteo (Herrajes 'un'), cm -> m (Telas) o
#   K x L cm2. Fecha/proveedor = los del bloque izquierdo de la misma fila.
# - MARGARA H..L ('INVERSION MARZO/OCTUBRE MARGARA'): H=Cantidad (con o sin
#   unidad), I=Producto, J=Costo, K=Fecha, L=Provedor (fechas propias).
_COLS_DERECHA: dict[str, dict[str, str]] = {
    "INVERSION VALQUI": {
        "nombre": "J", "cantidad": "K", "ancho": "L", "costo": "M",
        "fecha": "E", "proveedor": "F",
    },
    "INVERSION MARGARA": {
        "nombre": "I", "cantidad": "H", "ancho": None, "costo": "J",
        "fecha": "K", "proveedor": "L",
    },
}


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
    derecha: int = 0         # sub-tabla derecha descartada (dup / no-BOM)
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


def _cantidad_subtabla_derecha(
    celda: object, ancho: object, unidad_objetivo: str
) -> Decimal | None:
    """Cantidad de la sub-tabla derecha en la unidad canonica del insumo.

    VALQUI: K = 'Largo CMS'. Herrajes 'un' -> K es el conteo (100 un);
    Telas 'm' -> K cm / 100 (1000 cm = 10 m); 'cm2' -> K x L (L default 1).
    MARGARA: H ya trae cantidad+unidad ('10 mts' / 200) -> parser normal.
    """
    if celda is None:
        return None
    if isinstance(celda, str):
        # MARGARA / VALQUI con cantidad textual: parser de cantidad+unidad.
        return normalizar_cantidad_compra(celda, unidad_objetivo)
    valor = normalizar_decimal(celda)
    if valor is None or valor <= 0:
        return None
    u = unidad_canonica(unidad_objetivo)
    if u == "m":
        return valor * Decimal("0.01")  # K en cm -> metros
    if u == "cm2":
        ancho_dec = normalizar_decimal(ancho) if ancho is not None else None
        return valor * (ancho_dec if ancho_dec and ancho_dec > 0 else Decimal("1"))
    return valor  # 'un' (o kg/g): K es el conteo


def _procesar_subtabla_derecha(
    plan: ComprasPlan,
    fila: dict[str, object],
    indx: int,
    hoja: str,
    universo: dict[str, str],
    nombres_izquierda: set[str],
    ultima_fecha: dict[ClaveFecha, object],
    report,
) -> bool:
    """Procesa la celda derecha de la fila (P1 fix).

    Criterio documentado: la derecha genera compra SOLO cuando su item es un
    insumo BOM y NO aparece en el bloque izquierdo de la MISMA hoja (fuente
    unica). Si duplica un item de la izquierda -> se descarta (duplicado,
    como antes) y cuenta en ``conteos.derecha``. Devuelve True si la fila
    tenia contenido derecho (para el contador).
    """
    config = _COLS_DERECHA.get(hoja)
    if config is None:
        return False
    nombre_raw = fila.get(config["nombre"])
    if not isinstance(nombre_raw, str) or not nombre_raw.strip():
        return False
    nombre = normalizar_nombre(nombre_raw)
    if not _es_material_valido(nombre):
        return False  # headers 'Producto'/'Herrajes' o filas junk
    conteos = plan.conteos
    if nombre in nombres_izquierda:
        conteos.derecha += 1  # duplica el bloque izquierdo de la misma hoja
        return True
    clave_ins = clave_normalizada(nombre)
    if clave_ins not in universo:
        conteos.derecha += 1  # lista de precios sin compra asociada (no-BOM)
        return True
    nombre_display = universo[clave_ins]
    unidad_obj = _unidad_de_insumo(nombre_display)
    cantidad = _cantidad_subtabla_derecha(
        fila.get(config["cantidad"]), fila.get(config["ancho"]), unidad_obj
    )
    if cantidad is None:
        conteos.sin_cantidad += 1
        if report:
            report.warn(
                hoja, indx, config["cantidad"],
                f"{nombre_display} (sub-tabla derecha): cantidad "
                f"{fila.get(config['cantidad'])!r} no interpretable; "
                f"fila excluida (EXM-2)",
            )
        return True
    costo_total = normalizar_decimal(fila.get(config["costo"]))
    if costo_total is None or costo_total <= 0:
        conteos.sin_cantidad += 1
        if report:
            report.warn(
                hoja, indx, config["costo"],
                f"{nombre_display} (sub-tabla derecha): costo no interpretable; "
                f"fila excluida",
            )
        return True
    precio_unitario = costo_total / cantidad

    proveedor_raw = fila.get(config["proveedor"])
    proveedor_nombre = (
        normalizar_nombre(proveedor_raw)
        if proveedor_raw is not None
        else None
    )
    fecha_raw = fila.get(config["fecha"])
    clave_f = ClaveFecha(clave_ins, proveedor_nombre or "<sin-proveedor>")
    fecha = fecha_para_fila(fecha_raw, clave_f, ultima_fecha)
    if fecha is None:
        conteos.sin_fecha += 1
        if report:
            report.warn(
                hoja, indx, config["fecha"],
                f"{nombre_display} (sub-tabla derecha): fecha vacia y sin fila "
                f"contigua del mismo insumo+proveedor; omitida (D5, nunca now())",
            )
        return True
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
    if report:
        report.info(
            hoja, indx, config["nombre"],
            f"sub-tabla derecha (fuente unica): {nombre_display} "
            f"{cantidad} @ {precio_unitario:.2f} fecha "
            f"{fecha.date() if fecha else '?'}"
            f"{' (fecha heredada)' if fecha_raw is None else ''}",
        )
    return True


def _universo_bom(libro, report) -> dict[str, str]:
    """clave normalizada -> nombre display (el mismo universo que cataloga F1:
    recetas BOM + OCT25 + CAJAS)."""
    return {
        clave_normalizada(v): v for v in _leer_materiales(libro, report).values()
    }


def _nombres_izquierda_hoja(filas: list[dict[str, object]], col_nom: str) -> set[str]:
    """Nombres (display) del bloque izquierdo de la hoja: la derecha que
    repita uno de estos se considera duplicado y se descarta."""
    nombres: set[str] = set()
    for fila in filas:
        valor = fila.get(col_nom)
        if isinstance(valor, str) and valor.strip():
            nombres.add(normalizar_nombre(valor))
    return nombres


def plan_compras(libro, report=None) -> ComprasPlan:
    """Build the purchase plan from the bounded workbook (read-only).

    Bloque izquierdo + sub-tabla derecha (P1 fix): la derecha se procesa solo
    cuando el item NO aparece en el bloque izquierdo de la misma hoja (fuente
    unica); cada fila se filtra por el universo BOM; fechas bajo politica D5;
    never now().
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
        nombres_izquierda = _nombres_izquierda_hoja(filas, col_nom)
        ultima_fecha: dict[ClaveFecha, object] = {}
        for indx, fila in enumerate(filas, start=SHEET_BOUNDS[hoja][0]):
            cantidad_raw = fila.get(col_cant)
            if cantidad_raw is None and hoja == "INVERSION VALQUI":
                # Bloque Kilotelas (R56-78): la cantidad va en C cuando A esta vacia.
                cantidad_raw = fila.get("C")
            nombre = fila.get(col_nom)
            if isinstance(nombre, str):
                _procesar_fila_izquierda(
                    plan, fila, indx, hoja, col_cant, col_costo, col_fecha,
                    col_prov, cantidad_raw, nombre, universo, ultima_fecha,
                    report,
                )
            _procesar_subtabla_derecha(
                plan, fila, indx, hoja, universo, nombres_izquierda,
                ultima_fecha, report,
            )
    return plan


def _procesar_fila_izquierda(
    plan: ComprasPlan,
    fila: dict[str, object],
    indx: int,
    hoja: str,
    col_cant: str,
    col_costo: str,
    col_fecha: str,
    col_prov: str,
    cantidad_raw: object,
    nombre: str,
    universo: dict[str, str],
    ultima_fecha: dict[ClaveFecha, object],
    report,
) -> None:
    """Procesa una fila del bloque izquierdo (compra WAC BOM-only)."""
    conteos = plan.conteos
    clave_ins = clave_normalizada(nombre)
    if clave_ins not in universo:
        conteos.no_bom += 1
        return
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
        return
    costo_total = normalizar_decimal(fila.get(col_costo))
    if costo_total is None or costo_total <= 0:
        conteos.sin_cantidad += 1
        if report:
            report.warn(
                hoja, indx, col_costo,
                f"{nombre_display}: costo no interpretable; fila excluida",
            )
        return
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
        return
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