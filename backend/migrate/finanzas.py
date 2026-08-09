"""F6 finanzas phase: 3 socios (40/30/30) + Movimientos_Financieros historicos.

Scope of slice 7 (PR#7): ONLY phase 6 (tasks #424 T9; design #423 finanzas.py
+ D3; spec FIN-1..FIN-3, EXM-2/3/4, NFR-1/2; approved product decisions 1..5).

What this module does
---------------------
F6 builds an idempotent ``FinanzasPlan`` from the investment sheets of the
Excel and, in commit mode, persists it inside a single ``session_scope``
(EXM-4):

- **Socios (decision 1)**: the 3 canonical partners Valqui 40% / Margarita
  30% / ARPIA 30% are created as an atomic batch with sum == 100 guaranteed by
  the pipeline (FIN-2). It uses INSERT directo ORM (design D3) because
  ``crear_socio_configuracion`` (service) demands sum==100 PER create (finanzas
  service raises 422 with zero partners unless the batch is a single 100% row)
  — a 40/30/30 batch can never pass through it. The CHECK constraint only
  enforces positive percentages; the sum invariant is enforced here.

- Socios por hoja: every movement is attributed to the partner named in the
  sheet (Valqui -> 40%, Margarita -> 30%) except GASTOS/STICKERS equipment and
  expenses which go to the company partner ARPIA (30%), and every row whose
  normalized name contains 'prestamo' is typed Inversion with socio_id=NULL
  (approved decision 2: the Rafael loan is modelled as Inversion with no
  partner — NO Rafael socio is created).

- **Movimientos (FIN-1)**: type 'Inversion'|'Gasto' decided by keywords on the
  normalized description (see ``clasificar_tipo``): machinery/equipment/
  printers/termo/curses/stands -> Inversion (capital productive), services and
  consumables (hosting, publicidad, envio, papeleria, configuracion, ...) ->
  Gasto; the default is 'Gasto'. Amount = the row TOTAL cost (col D / C / C /
  E per sheet), Decimal NUMERIC(15,4). Fecha = the real Excel date coerced to
  aware (never now(), D5); a row without a usable fecha is OMITTED + WARN.

- **BOM-skip (hybrid, product decision 4)**: rows whose normalized name is in
  the F2 BOM universe (``_universo_bom``) were ALREADY registered as WAC
  purchases by F2 — they are counted and skipped here (no duplicated
  movements). The right-hand price sub-tables of INVERSION VALQUI (J..N,
  duplicate price lists) never become movements. The MARGARA right block
  (H..L "INVERSION MARZO"/"OCTUBRE") IS real investment data (not duplicates)
  and IS loaded as movements.

- Idempotence (NFR-1/EXM-3): partners by name (upsert, never duplicated);
  movements by natural key (fecha ISO, tipo, monto quantized to NUMERIC(15,4),
  socio_id, descripcion normalized).

The F6 runner is registered in ``migrate/__init__.py`` (FASES_IMPLEMENTADAS+F6).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select

from app.models import MovimientoFinanciero, SociosConfiguracion
from migrate.catalog import clave_normalizada, normalizar_nombre
from migrate.context import MigrationContext, session_scope
from migrate.loaders import HojaInexistenteError, LibroMigracion, SHEET_BOUNDS
from migrate.normalize import coerce_aware, normalizar_decimal

# --- Canonical partners (product decision 1): sum MUST be 100 --------------- #
SOCIOS: tuple[tuple[str, str], ...] = (
    ("Valqui", "40"),
    ("Margarita", "30"),
    ("ARPIA", "30"),
)

# Source sheet -> default socio name (company partner for company-wide rows).
SOCIO_POR_HOJA: dict[str, str] = {
    "INVERSION VALQUI": "Valqui",
    "INVERSION MARGARA": "Margarita",
    "STICKERS": "ARPIA",
    "GASTOS ARPIA": "ARPIA",
}

_INVERSION_KEYWORDS: tuple[str, ...] = (
    "prestamo", "maquin", "impresora", "impresion", "term", "cinta termica", "termo",
    "teflon", "cortador", "regla", "modisteria", "tijeras", "guillotina",
    "plancha", "patron", "patrones", "curso", "estampar", "brazo",
    "madera", "tornillo", "maniqui", "lampara", "silla", "kit",
    "accesorio", "impresion", "printer", "maquina", "miquina", "planchuela",
    "barilla", "varilla", "aro", "arco", "fly", "refrigerador", "refrigeracion",
    "wash", "cur", "resina", "filamento", "aerografo", "stand", "sello",
    "sillas", "termonegative", "configuracion tecnica", "taller",
)
_GASTO_DE_KEYWORDS: tuple[str, ...] = (
    "hosting", "dominio", "publicidad", "ads", "envio", "domicilio",
    "ayudante", "papeleria", "organizacion", "bono", "fotografia", "video",
    "revision", "fragancia", "decoracion", "feria", "materiales surtidos",
    "maneula", "mueble", "papel", "compras varias", "domicilios", "envios",
)


def clasificar_tipo(nombre: object) -> str:
    """Classify a financial row as 'Inversion' or 'Gasto' (documented rule).

    - 'Inversion': productive capital — machinery, printers, thermo/teflon,
      patterns, plots, courses (capacitacion = capital), ferias equipment.
    - 'Gasto': operating consumables/services — hosting, dominio, publicidad,
      envio/domicilio, ayudante, papelería, fotografía, bonos, ...
    - default: 'Gasto' (conservative; unclassified rows are never investments).
    """
    texto = clave_normalizada(nombre)
    for kw in _INVERSION_KEYWORDS:
        if kw in texto:
            return "Inversion"
    for kw in _GASTO_DE_KEYWORDS:
        if kw in texto:
            return "Gasto"
    return "Gasto"


def _es_prestamo(nombre: str) -> bool:
    return "prestamo" in clave_normalizada(nombre)


# --------------------------------------------------------------------------- #
# Plan model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class MovimientoPlan:
    descripcion: str
    monto: Decimal
    tipo: str
    fecha: datetime
    socio_nombre: str | None  # 'Valqui' | 'Margarita' | 'ARPIA' | None (loan)
    hoja: str
    fila: int


@dataclass
class ConteosFinanzas:
    """Counters of the phase (reporte N7a / EXM-1)."""

    bom_skip: int = 0      # fila del universo BOM (ya compra WAC F2 -> no duplicar)
    sin_fecha: int = 0     # D5: fila sin fecha -> omitida + WARN (nunca now())
    subtabla: int = 0      # sub-tabla derecha (lista de precios) ignorada
    planificadas: int = 0  # movimientos que entran al plan
    gastos_referencia: int = 0  # GASTOS ARP4 filas sin fecha (reporte INFO)


@dataclass
class FinanzasPlan:
    """Plan (dry-run) of the F6 movements + partners the phase would persist."""

    movimientos: list[MovimientoPlan] = field(default_factory=list)
    conteos: ConteosFinanzas = field(default_factory=ConteosFinanzas)

    @property
    def conteo_movimientos(self) -> int:
        return len(self.movimientos)


# --------------------------------------------------------------------------- #
# Pure: workbook -> plan
# --------------------------------------------------------------------------- #

# (hoja, col_descripcion, col_costo, col_fecha, bloque_extra)
_HOJAS_INVERSION: tuple[tuple[str, str, str, str], ...] = (
    ("INVERSION VALQUI", "B", "D", "E"),
    ("INVERSION MARGARA", "B", "C", "D"),
    ("STICKERS", "B", "C", "D"),
)

# MARGARA right block (H..L) is REAL investment data (bloques 'INVERSION
# MARZO/OCTUBRE'); H=es header. col cual: descripcion=I, costo=J, fecha=K.
_MARGARA_DERECHA_COLS = ({"desc": "I", "costo": "J", "fecha": "K"},)

# GASTOS ARPA: NOMBRE/COSTO columns but NO date column -> D5: every row is
# 'sin fecha' and is reported (never migrated with now()).
_HOJA_GASTOS = ("GASTOS ARPIA", "B", "E")


def _universo_bom(libro, report) -> dict[str, str]:
    """Reuse the F2 universe: key normalizada -> display name."""
    from migrate.purchases import _universo_bom

    return _universo_bom(libro, report)


def _coerce_fecha(celda: object) -> datetime | None:
    """Fecha del Excel -> aware (UTC); None si vacia/ilegible (never now)."""
    if celda is None:
        return None
    fecha = coerce_aware(celda)
    if not isinstance(fecha, datetime):
        return None
    return fecha


def _es_fila_izquierda(fila: dict[str, object], cols_izq: tuple[str, ...]) -> bool:
    return any(col in fila for col in cols_izq)


def plan_finanzas(libro, report=None) -> FinanzasPlan:
    """Build the plan from the bounded workbook (read-only).

    Filas del universo BOM (ya F2 WAC) -> bom_skip; sub-tabla derecha de
    VALQUI (J..N price list) -> subtabla; GASTOS ARPA sin fecha -> report INFO.
    """
    plan = FinanzasPlan()
    conteos = plan.conteos
    universo = _universo_bom(libro, report)

    for hoja, col_desc, col_costo, col_fecha in _HOJAS_INVERSION:
        if hoja not in SHEET_BOUNDS:
            continue
        try:
            lectura = libro.leer_hoja(hoja, report=report)
        except HojaInexistenteError:
            if report:
                report.warn(hoja, None, None, "hoja ausente en este workbook; omitida")
            continue
        filas = lectura.filas
        for indx, fila in enumerate(filas, start=SHEET_BOUNDS[hoja][0]):
            if hoja == "INVERSION VALQUI" and _es_subtabla_j_n(fila):
                conteos.subtabla += 1
                continue
            _agregar_fila(plan, fila, hoja, indx, col_desc, col_costo,
                          col_fecha, universo, report)

    # INVERSION MARGARA: right block H..L (real INVERSION MARZO/OCT).
    if "INVERSION MARGARA" in SHEET_BOUNDS:
        try:
            lectura = libro.leer_hoja("INVERSION MARGARA", report=report)
        except HojaInexistenteError:
            lectura = None
        if lectura is not None:
            for indx, fila in enumerate(lectura.filas, start=SHEET_BOUNDS["INVERSION MARGARA"][0]):
                nombre = fila.get("I")
                if not isinstance(nombre, str) or not nombre.strip():
                    continue
                clave_nombre = clave_normalizada(nombre)
                if clave_nombre in universo:
                    conteos.bom_skip += 1
                    continue
                costo = normalizar_decimal(fila.get("J"))
                if costo is None or costo <= 0:
                    continue
                fecha = _coerce_fecha(fila.get("K"))
                if fecha is None:
                    conteos.sin_fecha += 1
                    if report:
                        report.warn("INVERSION MARGARA", indx, "K",
                                    f"{normalizar_nombre(nombre)}: fila sin fecha "
                                    f"(D5, nunca now()) -> omitida")
                    continue
                _movimiento_a_plan(plan, normalizar_nombre(nombre), costo,
                                 fecha, hoja="INVERSION MARGARA", fila=indx,
                                 report=report)

    # GASTOS ARP4: sin columna de fecha en el Excel -> se reporta, no migra.
    if _HOJA_GASTOS[0] in SHEET_BOUNDS:
        try:
            lectura = libro.leer_hoja(_HOJA_GASTOS[0], report=report)
        except HojaInexistenteError:
            lectura = None
        if lectura is not None:
            for indx, fila in enumerate(lectura.filas, start=SHEET_BOUNDS[_HOJA_GASTOS[0]][0]):
                nombre = fila.get(_HOJA_GASTOS[1])
                if not isinstance(nombre, str) or not nombre.strip():
                    continue
                costo = normalizar_decimal(fila.get(_HOJA_GASTOS[2]))
                if costo is None:
                    continue
                conteos.gastos_referencia += 1
                if report:
                    report.warn(
                        _HOJA_GASTOS[0], indx, None,
                        f"{normalizar_nombre(nombre)}: hoja sin columna de fecha; "
                        f"gasto NO migrado (D5: fechas reales, nunca now()).",
                    )
    return plan


def _es_subtabla_j_n(fila: dict[str, object]) -> bool:
    """True si la fila solo tiene celdas J..N (price list de VALQUI)."""
    izquierda = any(col in fila for col in ("A", "B", "C", "D", "E", "F"))
    derecha = any(col in fila for col in ("J", "K", "L", "M", "N"))
    return derecha and not izquierda


def _agregar_fila(plan, fila, hoja, indx, col_desc, col_costo, col_fecha,
                  universo, report) -> None:
    nombre_raw = fila.get(col_desc)
    if not isinstance(nombre_raw, str) or not nombre_raw.strip():
        return
    clave = clave_normalizada(nombre_raw)
    if clave in universo:
        plan.conteos.bom_skip += 1
        return
    monto = normalizar_decimal(fila.get(col_costo))
    if monto is None or monto <= 0:
        return
    fecha = _coerce_fecha(fila.get(col_fecha))
    if fecha is None:
        plan.conteos.sin_fecha += 1
        if report:
            report.warn(hoja, indx, col_fecha,
                        f"{normalizar_nombre(nombre_raw)}: fecha vacia; "
                        f"no migrado (D5, nunca now())")
        return
    _movimiento_a_plan(plan, normalizar_nombre(nombre_raw), monto, fecha,
                       hoja, indx, report)


def _movimiento_a_plan(plan, descripcion, monto, fecha, hoja, fila, report) -> None:
    socio_nombre = None
    if _es_prestamo(descripcion):
        # approved decision 2: prestamo intro overcome -> socio NULL
        tipo = "Inversion"
        socio = None
        if report:
            report.info(hoja, fila, None,
                        f"{descripcion}: prestamo -> movimiento Inversion socio NULL")
    else:
        tipo = clasificar_tipo(descripcion)
        socio = SOCIO_POR_HOJA.get(hoja, "ARPIA")
    plan.movimientos.append(
        MovimientoPlan(
            descripcion=descripcion,
            monto=monto,
            tipo=tipo,
            fecha=fecha,
            socio_nombre=socio,
            hoja=hoja,
            fila=fila,
        )
    )
    plan.conteos.planificadas += 1


# --------------------------------------------------------------------------- #
# DB apply (3 partners batch + movements, idempotent)
# --------------------------------------------------------------------------- #


def _moneda(valor: Decimal) -> Decimal:
    """Escala NUMERIC(15,4) exactamente (identica a sales._moneda)."""
    return valor.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _socio_ids(db) -> dict[str, int]:
    """Partner ids by name (get-or-create, batch guaranteed sum==100)."""
    ids: dict[str, int] = {}
    for nombre, pct in SOCIOS:
        exist = db.scalar(
            select(SociosConfiguracion).where(SociosConfiguracion.nombre == nombre)
        )
        if exist is None:
            # Design D3: INSERT directo ORM, batch atomico; the pipeline
            # guarantees the global sum == 100 (FIN-2). Service rejects a batch.
            exist = SociosConfiguracion(
                nombre=nombre, porcentaje_participacion=Decimal(pct)
            )
            db.add(exist)
            db.flush()
        ids[nombre] = exist.id
    return ids


def _clave_movimiento(m: MovimientoPlan, socio_id: int | None) -> tuple:
    return (
        m.fecha.isoformat(),
        m.tipo,
        _moneda(m.monto),
        socio_id,
        normalizar_nombre(m.descripcion),
    )


def aplicar_finanzas(db, plan: FinanzasPlan, report=None) -> dict[str, int]:
    """Persist socios y movimientos en una transaccion (EXM-4); el caller
    (session_scope) hace el commit unico. Idempotente (NFR-1).

    Socios: batch atomico get-or-create por nombre (suma=100 pipeline).
    Movimientos: por clave natural; re-run nunca duplica.
    """
    res = {"socios": len(SOCIOS), "socios_nuevos": 0, "movimientos": 0,
           "ya_presentes": 0}

    # Partners (solo crea los que faltan; nunca toca porcentajes existentes).
    for nombre, pct in SOCIOS:
        exist = db.scalar(
            select(SociosConfiguracion).where(SociosConfiguracion.nombre == nombre)
        )
        if exist is None:
            exist = SociosConfiguracion(
                nombre=nombre, porcentaje_participacion=Decimal(pct)
            )
            db.add(exist)
            db.flush()
            res["socios_nuevos"] += 1

    socio_ids = {
        s.nombre: s.id
        for s in db.scalars(select(SociosConfiguracion)).all()
        if s.nombre in dict(SOCIOS)
    }

    for mv in plan.movimientos:
        socio_id = socio_ids.get(mv.socio_nombre) if mv.socio_nombre else None
        clave = _clave_movimiento(mv, socio_id)
        existe = _movimiento_existe(db, clave)
        if existe:
            res["ya_presentes"] += 1
            continue
        _insertar_movimiento(db, mv, socio_id)
        res["movimientos"] += 1
        if report:
            report.info(mv.hoja, mv.fila, None,
                        f"{mv.descripcion}: {mv.tipo} {mv.monto} fecha "
                        f"{mv.fecha.date()} socio {mv.socio_nombre or 'NULL'}")
    if report:
        report.info(
            "F6", None, None,
            f"finanzas aplicadas: {res['movimientos']} movimientos, "
            f"{res['socios_nuevos']} socios nuevos, "
            f"{res['ya_presentes']} ya-existentes",
        )
    return res


def _movimiento_existe(db, clave) -> bool:
    fecha_key, tipo, monto4, socio_id, descripcion = clave
    stmt = select(MovimientoFinanciero.id).where(
        MovimientoFinanciero.fecha == datetime.fromisoformat(fecha_key),
        MovimientoFinanciero.tipo == tipo,
        MovimientoFinanciero.monto == monto4,
        MovimientoFinanciero.descripcion == descripcion,
    )
    if socio_id is None:
        stmt = stmt.where(MovimientoFinanciero.socio_id.is_(None))
    else:
        stmt = stmt.where(MovimientoFinanciero.socio_id == socio_id)
    return db.scalar(stmt) is not None


def _insertar_movimiento(db, mv: MovimientoPlan, socio_id: int | None) -> None:
    db.add(
        MovimientoFinanciero(
            tipo=mv.tipo,
            descripcion=mv.descripcion,
            monto=mv.monto,  # Decimal NUMERIC(15,4)
            fecha=mv.fecha,   # fecha real del Excel (nunca now())
            socio_id=socio_id,
            estado="activo",
        )
    )
    db.flush()


# --------------------------------------------------------------------------- #
# Phase entry point (F6 runner registered in migrate/__init__.py)
# --------------------------------------------------------------------------- #


def cargar_finanzas(ctx: MigrationContext) -> FinanzasPlan:
    """F6 runner: planifica y en commit persiste (EXM-4) con idempotencia
    (NFR-1); dry-run = plan + reporte, 0 escrituras (NFR-2)."""
    report = ctx.report
    with LibroMigracion(ctx.options.source) as libro:
        plan = plan_finanzas(libro, report)

    report.info(
        "F6", None, None,
        f"plan finanzas: {plan.conteo_movimientos} movimientos | "
        f"bom-skip {plan.conteos.bom_skip} | sin fecha {plan.conteos.sin_fecha} "
        f"| sub-tabla {plan.conteos.subtabla} | gastos sin fecha "
        f"{plan.conteos.gastos_referencia}",
    )
    if ctx.options.modo == "commit" and ctx.session is not None:
        with session_scope(ctx, ctx.session) as db:
            aplicar_finanzas(db, plan, report)
    return plan


__all__ = [
    "SOCIOS",
    "FinanzasPlan",
    "MovimientoPlan",
    "FinanzasPlan",
    "clasificar_tipo",
    "plan_finanzas",
    "aplicar_finanzas",
    "cargar_finanzas",
]