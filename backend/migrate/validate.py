"""F7 - Validacion transversal (checks N7a-g).

The last phase cross-checks the DB against what the pipeline planned before
committing (and in commit mode right after the previous phases ran). It is
READ-ONLY: ``cargar_validate`` never writes; in ``--commit`` the phase runs the
checks against the session the CLI provides and reports ERRORs/WARNs.

Checks (spec EXM-5, NFR-1/2; design #423; slice-8 contract N7a-g):

- N7a "conteos": rows per domain (tipos, proveedores, insumos, productos,
  BOM_-insumos, compras, ventas, movimientos, socios). Identity is the plan's
  own rows (normalized names / natural identifiers); the DB is checked for
  each expected identifier: missing -> WARN (with cause), duplicated rows of
  the same identity -> ERROR (a re-run duplicated). DB rows NOT attributable
  to the plan (manual ERP data, other-source rows) are out of scope.
- N7b "stock_negativo": no Insumo with stock_actual < 0 (EXM-5).
- N7c "finanzas": scoped movements (descripcion of the plan) have monto > 0
  and the sum per tipo matches the plan; canonical partners (FIN-2) sum 100.
- N7d "cuadre": per snapshot insumo, stock_actual == snapshot + compras
  - explosion of the sales (VTA-3), tolerance 0.0005. A snapshot insumo absent
  from the catalog while the migration is partially applied -> ERROR
  (precondition broken); the whole snapshot absent (F4 not applied) -> WARN
  with cause.
- N7e "precios": every scoped DetalleVenta costo == the historical cost of the
  plan row (VTA-1/EXM-5e) and the sale total == quantity * price with
  descuento_porcentaje == 0 (no double discount, VTA-2).
- N7f "fechas": no migration row carries a fake now() date (D5).
- N7g "idempotencia": natural keys (insumo, fecha, cantidad, precio) of
  compras / (fecha, tipo, monto, socio, descripcion) of movimientos /
  (producto, insumo) of BOM with count > 1 -> ERROR; sales per natural key
  greater than the plan count -> ERROR.

The F7 runner is registered in ``migrate/__init__.py`` (FASES_IMPLEMENTADAS+F7).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from app.models import (
    BomInsumo,
    CompraInsumo,
    DetalleVenta,
    Insumo,
    MovimientoFinanciero,
    Producto,
    Proveedor,
    SociosConfiguracion,
    TipoProducto,
    Venta,
    VarianteProducto,
)
from migrate.bom import BomPlan, plan_bom
from migrate.catalog import (
    CatalogPlan,
    clave_normalizada,
    normalizar_nombre,
    plan_catalogo,
)
from migrate.context import MigrationContext
from migrate.finanzas import FinanzasPlan, SOCIOS, plan_finanzas
from migrate.loaders import LibroMigracion
from migrate.purchases import ComprasPlan, plan_compras
from migrate.sales import VentasPlan, plan_ventas
from migrate.stock import StockPlan, plan_stock

# Historical rows live ~1 year before the server; anything within 1 day of
# "now" is a fake now() date (D5).
_UMBRAL_FECHA_SEG = 86400
TOLERANCIA_CUADRE = Decimal("0.0005")
TOLERANCIA_DINERO = Decimal("0.001")


@dataclass(frozen=True)
class CheckResult:
    """One validation check: id ("N7a".."N7g"), estado (OK/WARN/ERROR), mensaje."""

    id: str
    estado: str  # "OK" | "WARN" | "ERROR"
    mensaje: str


def _peor(*estados: str) -> str:
    """Order the severities: ERROR > WARN > OK."""
    prioridad = {"OK": 0, "WARN": 1, "ERROR": 2}
    return max(estados, key=lambda e: prioridad.get(e, 0), default="OK")


def _moneda(valor: Decimal | None) -> Decimal:
    """Quantize to the NUMERIC(15,4) scale the DB stores."""
    return (Decimal(valor or 0)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------- #
# Plan model
# --------------------------------------------------------------------------- #


@dataclass
class PlanValidacion:
    """Aggregate of the six phase plans the N7 checks run against."""

    catalogo: CatalogPlan
    compras: ComprasPlan
    bom: BomPlan
    stock: StockPlan
    ventas: VentasPlan
    finanzas: FinanzasPlan

    @property
    def conteo_insumos_plan(self) -> int:
        return len(self.catalogo.insumos)

    @property
    def conteo_movimientos_plan(self) -> int:
        return len(self.finanzas.movimientos)


# --------------------------------------------------------------------------- #
# Workbook -> plan (6 sub-plans, bounded read, 0 escrituras)
# --------------------------------------------------------------------------- #


def plan_para_validacion(libro: LibroMigracion, report=None) -> PlanValidacion:
    """Run the phase plans that feed the N7 checks (read-only)."""
    return PlanValidacion(
        catalogo=plan_catalogo(libro, report),
        compras=plan_compras(libro, report),
        bom=plan_bom(libro, report),
        stock=plan_stock(libro, report),
        ventas=plan_ventas(libro, report),
        finanzas=plan_finanzas(libro, report),
    )


# --------------------------------------------------------------------------- #
# N7 checks (read-only audits over the DB + the plan)
# --------------------------------------------------------------------------- #


def _conteo_por_clave(db, col) -> dict[str, int]:
    """Rows per accent/case-insensitive key over the given name column."""
    conteos: dict[str, int] = defaultdict(int)
    for (nombre,) in db.query(col).all():
        conteos[clave_normalizada(nombre)] += 1
    return conteos


def _identidades_bom_db(db) -> dict[str, int]:
    """BOM ids 'producto|insumo' present in the DB (rows per id)."""
    conteos: dict[str, int] = defaultdict(int)
    filas = (
        db.query(BomInsumo, Producto.nombre, Insumo.nombre)
        .join(Producto, BomInsumo.producto_id == Producto.id)
        .join(Insumo, BomInsumo.insumo_id == Insumo.id)
        .all()
    )
    for _bom, producto, insumo in filas:
        conteos[
            f"{clave_normalizada(producto)}|{clave_normalizada(insumo)}"
        ] += 1
    return conteos


def _identidades_compras_db(db) -> dict[str, int]:
    """Compra ids keyed by the insumo name (the F2 natural id)."""
    conteos: dict[str, int] = defaultdict(int)
    filas = (
        db.query(Insumo.nombre)
        .join(CompraInsumo, CompraInsumo.insumo_id == Insumo.id)
        .all()
    )
    for (insumo,) in filas:
        conteos[clave_normalizada(insumo)] += 1
    return conteos


def _identidades_ventas_db(db) -> dict[str, int]:
    """Venta ids keyed by the product name (Detalle_Ventas referenced rows)."""
    conteos: dict[str, int] = defaultdict(int)
    filas = (
        db.query(Producto.nombre)
        .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
        .all()
    )
    for (producto,) in filas:
        conteos[clave_normalizada(producto)] += 1
    return conteos


def _identidades_movimientos_db(db) -> dict[str, int]:
    """Movimiento ids keyed by the normalized descripcion."""
    return _conteo_por_clave(db, MovimientoFinanciero.descripcion)


def _identidades_socios_db(db) -> dict[str, int]:
    return _conteo_por_clave(db, SociosConfiguracion.nombre)


def _productos_del_plan(plan: PlanValidacion) -> list[str]:
    """Products the workbook actually references (BOM recetas + ventas)."""
    nombres = {normalizar_nombre(l.producto_nombre) for l in plan.bom.insumos}
    nombres |= {normalizar_nombre(l.producto_nombre) for l in plan.ventas.ventas}
    return sorted(n for n in nombres if n)


def _n7a_conteos(db, plan: PlanValidacion) -> CheckResult:
    """Dominios tipificados: esperado = filas del plan; DB = filas con identidad."""
    esperados_por_dominio: list[tuple[str, list[str]]] = [
        ("proveedores", [normalizar_nombre(p.nombre) for p in plan.catalogo.proveedores]),
        ("insumos", [normalizar_nombre(i.nombre) for i in plan.catalogo.insumos]),
        ("tipos", [normalizar_nombre(t) for t in plan.catalogo.tipos]),
        ("productos", _productos_del_plan(plan)),
        ("bom_insumos", [
            f"{clave_normalizada(l.producto_nombre)}|{clave_normalizada(l.insumo_nombre)}"
            for l in plan.bom.insumos
        ]),
        ("compras", [normalizar_nombre(c.insumo_nombre) for c in plan.compras.compras]),
        ("ventas", [normalizar_nombre(v.producto_nombre) for v in plan.ventas.ventas]),
        ("movimientos", [normalizar_nombre(m.descripcion) for m in plan.finanzas.movimientos]),
        ("socios", [normalizar_nombre(n) for n, _ in SOCIOS]),
    ]
    db_claves = {
        "proveedores": _conteo_por_clave(db, Proveedor.nombre),
        "insumos": _conteo_por_clave(db, Insumo.nombre),
        "tipos": _conteo_por_clave(db, TipoProducto.nombre),
        "productos": _conteo_por_clave(db, Producto.nombre),
        "bom_insumos": _identidades_bom_db(db),
        "compras": _identidades_compras_db(db),
        "ventas": _identidades_ventas_db(db),
        "movimientos": _identidades_movimientos_db(db),
        "socios": _identidades_socios_db(db),
    }

    piezas: list[str] = []
    faltantes = 0
    duplicados = 0
    for nombre, esperados in esperados_por_dominio:
        presentes = 0
        for esperado in esperados:
            cuenta = db_claves[nombre].get(clave_normalizada(esperado), 0)
            if cuenta >= 1:
                presentes += 1
                if cuenta > 1:
                    duplicados += 1
            else:
                faltantes += 1
        piezas.append(f"{nombre} {presentes}/{len(esperados)}")

    estado = "ERROR" if duplicados else ("WARN" if faltantes else "OK")
    detalle = f"conteos: {' | '.join(piezas)} - faltantes {faltantes}, duplicados {duplicados}"
    if duplicados:
        detalle += " (re-run habria duplicado filas)"
    elif faltantes:
        detalle += " (filas del plan ausentes; fases previas no corridas)"
    return CheckResult("N7a", estado, detalle)


def _n7b_stock_negativo(db, plan: PlanValidacion) -> CheckResult:
    negativos = [
        i for i in db.query(Insumo).all()
        if i.stock_actual is not None and i.stock_actual < 0
    ]
    if negativos:
        nombres = ", ".join(sorted(i.nombre for i in negativos[:5]))
        return CheckResult(
            "N7b", "ERROR",
            f"stock_actual < 0 en {len(negativos)} insumos (ej: {nombres})",
        )
    return CheckResult("N7b", "OK", "ningun insumo con stock_actual < 0")


def _n7c_finanzas(db, plan: PlanValidacion) -> CheckResult:
    """Montos > 0 + suma por tipo + socios == 100 (FIN-2), scoped al plan."""
    errores: list[str] = []
    faltante = False

    descripciones_plan = {clave_normalizada(m.descripcion) for m in plan.finanzas.movimientos}
    if descripciones_plan:
        scoped = [
            m for m in db.query(MovimientoFinanciero).all()
            if clave_normalizada(m.descripcion) in descripciones_plan
        ]
        if not scoped:
            faltante = True  # F6 no aplicada: movimientos del plan no cargados
        else:
            if any(m.monto is not None and m.monto <= 0 for m in scoped):
                errores.append("movimiento del plan con monto <= 0")
            suma_plan: dict[str, Decimal] = defaultdict(Decimal)
            for m in plan.finanzas.movimientos:
                suma_plan[m.tipo] += m.monto if m.monto else Decimal("0")
            suma_db: dict[str, Decimal] = defaultdict(Decimal)
            for m in scoped:
                suma_db[m.tipo] += m.monto if m.monto else Decimal("0")
            for tipo in sorted(set(suma_plan) | set(suma_db)):
                if abs(suma_db[tipo] - suma_plan[tipo]) > TOLERANCIA_DINERO:
                    errores.append(
                        f"suma por tipo {tipo!r}: DB {suma_db[tipo]} != plan {suma_plan[tipo]}"
                    )

    nombres_socios = {clave_normalizada(n) for n, _ in SOCIOS}
    socios = [
        s for s in db.query(SociosConfiguracion).all()
        if clave_normalizada(s.nombre) in nombres_socios
    ]
    if socios:
        suma = sum((s.porcentaje_participacion or Decimal("0")) for s in socios)
        if abs(suma - Decimal("100")) > TOLERANCIA_DINERO:
            errores.append(f"suma de socios {suma} != 100 (FIN-2)")
    else:
        faltante = True  # socios canonicos ausentes (F6 no corrida)

    estado = _peor("ERROR" if errores else "OK", "WARN" if faltante else "OK")
    situacion = "; ".join(errores) if errores else (
        "socios ausentes (F6 no corrida)" if faltante else "finanzas coherentes con el plan"
    )
    return CheckResult("N7c", estado, f"finanzas: {situacion}")


def _n7d_cuadre(db, plan: PlanValidacion) -> CheckResult:
    """Cuadre de stock: snapshot + compras - explosion de ventas = actual (VTA-3)."""
    snapshot = plan.stock.stock
    if not snapshot:
        return CheckResult("N7d", "OK", "sin filas de snapshot OCT25 que cuadrar")

    db_insumos = {
        clave_normalizada(i.nombre): i for i in db.query(Insumo).all()
    }

    compras_total: dict[int, Decimal] = defaultdict(Decimal)
    for insumo_id, cantidad in db.query(
        CompraInsumo.insumo_id, CompraInsumo.cantidad_comprada
    ).all():
        compras_total[insumo_id] += cantidad if cantidad else Decimal("0")

    # Explosion: por cada detalle de venta, cantidad x BOM del mismo producto
    # (+ variante, si la receta la declara).
    bom_rows = db.query(BomInsumo).all()
    consumido: dict[int, Decimal] = defaultdict(Decimal)
    for detalle in db.query(DetalleVenta).all():
        for bom in bom_rows:
            if bom.producto_id != detalle.producto_id:
                continue
            if bom.variante_id is not None and bom.variante_id != detalle.variante_id:
                continue
            cantidad = detalle.cantidad if detalle.cantidad else Decimal("0")
            consumido[bom.insumo_id] += cantidad * bom.cantidad_requerida

    presentes = [
        l for l in snapshot if clave_normalizada(l.insumo_nombre) in db_insumos
    ]
    ausentes = [
        l for l in snapshot if clave_normalizada(l.insumo_nombre) not in db_insumos
    ]
    if ausentes:
        if presentes:
            return CheckResult(
                "N7d", "ERROR",
                f"{len(ausentes)} insumos del snapshot ausentes del catalogo "
                f"(precondicion rota: migracion parcial)",
            )
        return CheckResult(
            "N7d", "WARN",
            f"{len(ausentes)} insumos del snapshot ausentes del catalogo "
            f"(F4 OCT25 no aplicada)",
        )

    divergencias: list[str] = []
    for linea in snapshot:
        insumo = db_insumos[clave_normalizada(linea.insumo_nombre)]
        esperado = (
            linea.cantidad
            + compras_total.get(insumo.id, Decimal("0"))
            - consumido.get(insumo.id, Decimal("0"))
        )
        diff = abs(esperado - (insumo.stock_actual or Decimal("0")))
        if diff > TOLERANCIA_CUADRE:
            divergencias.append(
                f"{linea.insumo_nombre} actual {insumo.stock_actual} != "
                f"esperado {esperado} (dif {diff})"
            )

    if divergencias:
        return CheckResult(
            "N7d", "WARN", "cuadre divergente: " + "; ".join(divergencias[:5])
        )
    return CheckResult("N7d", "OK", f"cuadre exacto para {len(snapshot)} insumos")


def _n7e_precios(db, plan: PlanValidacion) -> CheckResult:
    """Costo historico del detalle == plan y total sin doble descuento (VTA-1/2)."""
    plan_por_clave: dict[tuple, object] = {}
    for venta in plan.ventas.ventas:
        clave = (
            venta.fecha.date(),
            clave_normalizada(venta.producto_nombre),
            clave_normalizada(venta.variante_nombre) if venta.variante_nombre else None,
            venta.cantidad,
            _moneda(venta.precio),
        )
        plan_por_clave.setdefault(clave, venta)

    errores: list[str] = []
    analizadas = 0
    for venta in db.query(Venta).all():
        for detalle in venta.detalles:
            clave = (
                venta.fecha.date(),
                clave_normalizada(detalle.producto.nombre),
                clave_normalizada(detalle.variante.nombre_variante)
                if detalle.variante else None,
                detalle.cantidad,
                _moneda(detalle.precio_unitario_aplicado),
            )
            plan_linea = plan_por_clave.get(clave)
            if plan_linea is None:
                continue  # venta no atribuible al plan: fuera de alcance
            analizadas += 1
            if _moneda(detalle.costo_unitario_aplicado) != _moneda(plan_linea.costo):
                errores.append(
                    f"{detalle.producto.nombre}: costo {detalle.costo_unitario_aplicado}"
                    f" != historico {plan_linea.costo}"
                )
            if venta.descuento_porcentaje > 0:
                errores.append(
                    f"{detalle.producto.nombre}: descuento_porcentaje > 0 (doble "
                    f"descuento, VTA-2)"
                )
            elif _moneda(venta.total_venta) != _moneda(
                detalle.cantidad * plan_linea.precio
            ):
                errores.append(
                    f"{detalle.producto.nombre}: total {venta.total_venta} != "
                    f"{detalle.cantidad} x {plan_linea.precio} (VTA-2)"
                )

    if errores:
        return CheckResult("N7e", "ERROR", "precios: " + "; ".join(errores[:5]))
    return CheckResult(
        "N7e", "OK", f"precios historicos correctos ({analizadas} ventas analizadas)"
    )


def _fecha_real_ok(fecha, ahora) -> bool:
    """True si la fecha no es un now() falso (D5)."""
    if fecha is None:
        return True  # filas sin fecha se omiten, nunca now()
    aware = fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)
    return abs((ahora - aware).total_seconds()) > _UMBRAL_FECHA_SEG


def _n7f_fechas(db, plan: PlanValidacion) -> CheckResult:
    ahora = datetime.now(timezone.utc)
    falsos: list[str] = []
    compras = db.query(CompraInsumo).all()
    for compra in compras:
        if not _fecha_real_ok(compra.fecha_compra, ahora):
            falsos.append(f"compra__{compra.id}")
    for venta in db.query(Venta).all():
        if not _fecha_real_ok(venta.fecha, ahora):
            falsos.append(f"venta__{venta.id}")
    for mov in db.query(MovimientoFinanciero).all():
        if not _fecha_real_ok(mov.fecha, ahora):
            falsos.append(f"movimiento__{mov.id}")
    if falsos:
        return CheckResult(
            "N7f", "ERROR", f"fechas falsas now() en: {', '.join(falsos[:5])}"
        )
    return CheckResult("N7f", "OK", "compras/ventas/movimientos con fechas reales")


def _clave_compra(plan) -> tuple:
    return (
        clave_normalizada(plan.insumo_nombre),
        plan.fecha.date().isoformat() if plan.fecha else "SIN-FECHA",
        _moneda(plan.cantidad),
        _moneda(plan.precio_unitario),
    )


def _n7g_idempotencia(db, plan: PlanValidacion) -> CheckResult:
    """Claves naturales con count > 1 → ERROR (un re-run habria duplicado)."""
    errores: list[str] = []

    # compras: clave natural F2 (insumo, fecha, cantidad, precio).
    plan_compras: dict[tuple, int] = defaultdict(int)
    for compra in plan.compras.compras:
        plan_compras[_clave_compra(compra)] += 1
    db_compras: dict[tuple, int] = defaultdict(int)
    filas = (
        db.query(Insumo.nombre, CompraInsumo.fecha_compra,
                 CompraInsumo.cantidad_comprada, CompraInsumo.precio_unitario_compra)
        .join(Insumo, CompraInsumo.insumo_id == Insumo.id)
        .all()
    )
    for insumo, fecha, cantidad, precio in filas:
        db_compras[(
            clave_normalizada(insumo), fecha.date().isoformat(),
            _moneda(cantidad), _moneda(precio),
        )] += 1
    for clave, esperadas in plan_compras.items():
        if db_compras.get(clave, 0) > esperadas:
            errores.append(f"compra duplicada: {clave[0]} @ {clave[1]}")

    # movimientos: clave F6 (fecha, tipo, monto, socio, descripcion).
    plan_movimientos: dict[tuple, int] = defaultdict(int)
    for mov in plan.finanzas.movimientos:
        plan_movimientos[(
            mov.fecha.date().isoformat(), mov.tipo, _moneda(mov.monto),
            clave_normalizada(mov.socio_nombre) if mov.socio_nombre else None,
            clave_normalizada(mov.descripcion),
        )] += 1
    db_movimientos: dict[tuple, int] = defaultdict(int)
    socio_por_id = {
        s.id: clave_normalizada(s.nombre)
        for s in db.query(SociosConfiguracion).all()
    }
    for m in db.query(MovimientoFinanciero).all():
        db_movimientos[(
            m.fecha.date().isoformat(), m.tipo, _moneda(m.monto),
            socio_por_id.get(m.socio_id) if m.socio_id else None,
            clave_normalizada(m.descripcion),
        )] += 1
    for clave, esperadas in plan_movimientos.items():
        if db_movimientos.get(clave, 0) > esperadas:
            errores.append(f"movimiento duplicado: {clave[4]} @ {clave[0]}")

    # bom: identidad producto|insumo con count > 1.
    plan_bom_ids = {
        f"{clave_normalizada(l.producto_nombre)}|{clave_normalizada(l.insumo_nombre)}"
        for l in plan.bom.insumos
    }
    for identidad, cuenta in _identidades_bom_db(db).items():
        if identidad in plan_bom_ids and cuenta > 1:
            errores.append(f"BOM_INSUMOS duplicado: {identidad}")

    # ventas: count por clave natural > count del plan.
    plan_ventas: dict[tuple, int] = defaultdict(int)
    for v in plan.ventas.ventas:
        plan_ventas[(
            v.fecha.date(), clave_normalizada(v.producto_nombre),
            clave_normalizada(v.variante_nombre) if v.variante_nombre else None,
            v.cantidad, _moneda(v.precio),
        )] += 1
    db_ventas: dict[tuple, int] = defaultdict(int)
    filas = (
        db.query(Venta.fecha, Producto.nombre, DetalleVenta.variante_id,
                 DetalleVenta.cantidad, DetalleVenta.precio_unitario_aplicado)
        .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
        .join(Producto, DetalleVenta.producto_id == Producto.id)
        .all()
    )
    variantes = {
        vid: clave_normalizada(name)
        for vid, name in db.query(VarianteProducto.id, VarianteProducto.nombre_variante).all()
    }
    for fecha, producto, vid, cantidad, precio in filas:
        db_ventas[(
            fecha.date(), clave_normalizada(producto),
            variantes.get(vid), cantidad, _moneda(precio),
        )] += 1
    for clave, esperadas in plan_ventas.items():
        if db_ventas.get(clave, 0) > esperadas:
            errores.append(f"venta duplicada: {clave[1]} @ {clave[0]}")

    if errores:
        return CheckResult("N7g", "ERROR", "idempotencia: " + "; ".join(errores[:5]))
    return CheckResult("N7g", "OK", "sin claves naturales duplicadas")


def checks_n7(db, plan: PlanValidacion) -> list[CheckResult]:
    """Run all seven checks in order (N7a..N7g)."""
    return [
        _n7a_conteos(db, plan),
        _n7b_stock_negativo(db, plan),
        _n7c_finanzas(db, plan),
        _n7d_cuadre(db, plan),
        _n7e_precios(db, plan),
        _n7f_fechas(db, plan),
        _n7g_idempotencia(db, plan),
    ]


# --------------------------------------------------------------------------- #
# Phase entry point (F7 runner registered in migrate/__init__.py)
# --------------------------------------------------------------------------- #


def cargar_validate(ctx: MigrationContext) -> PlanValidacion:
    """F7 runner: valida la DB contra el plan (solo lectura, NFR-2).

    En dry-run no hay sesion de DB: los checks N7 se omiten y la fase reporta
    el plan (misma NFR-2 que el resto de los runners). En commit el CLI provee
    la sesion y los 7 checks se reportan como INFO/WARN/ERROR.
    """
    report = ctx.report
    with LibroMigracion(ctx.options.source) as libro:
        plan = plan_para_validacion(libro, report)

    report.info(
        "F7", None, None,
        f"plan validacion: proveedores {len(plan.catalogo.proveedores)} | "
        f"insumos {len(plan.catalogo.insumos)} | productos {len(_productos_del_plan(plan))} "
        f"| bom {len(plan.bom.insumos)} | compras {len(plan.compras.compras)} "
        f"| ventas {len(plan.ventas.ventas)} | movimientos {len(plan.finanzas.movimientos)}",
    )

    if ctx.session is None:
        report.info(
            "F7", None, None,
            "checks N7 omitidas: dry-run sin sesion de DB (0 escrituras)",
        )
        return plan

    for check in checks_n7(ctx.session, plan):
        if check.estado == "ERROR":
            report.error("F7", None, None, f"{check.id}: {check.mensaje}")
        elif check.estado == "WARN":
            report.warn("F7", None, None, f"{check.id}: {check.mensaje}")
        else:
            report.info("F7", None, None, f"{check.id}: {check.mensaje}")
    return plan


__all__ = [
    "CheckResult",
    "PlanValidacion",
    "checks_n7",
    "plan_para_validacion",
    "cargar_validate",
]