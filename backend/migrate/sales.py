"""F5 sales phase: INSERT directo Venta + Detalle_Ventas + destock batch.

Scope of slice 6 (PR#6): ONLY phase 5 (tasks #424 T8; design #423 sales.py +
D2 + D7; spec VTA-1..VTA-4, EXM-2/3/4, NFR-1/2).

What this module does
---------------------
F5 builds a plan of the historical sales from the bounded VENTAS sheet and, in
commit mode, inserts them inside a single ``session_scope`` (EXM-4) WITHOUT
going through ``registrar_venta`` (design D2): that service forces now() and
recalculates cost with the current WAC; the Excel has the real date (col M),
the real discounted price (col G) and the real full cost (col H) per row, so
the snapshot must be exact.

Layout VENTAS (verified against ARPIA.xlsx, 2026-08-08):
    A  = producto (hoja de venta; nombre a mapear al catalogo)
    B-F= tallas/variantes de la fila (primera columna no vacia)
    G  = Precio Venta (YA descontado, VTA-2 -> tal-cual, nunca re-descontar)
    H  = Costo FULL (snapshot costa_unitario_aplicado, sin recalcular WAC)
    I  = Ganancia; J = Reinversion 40%; K = Margarita 30%; L = Valqui 30%
    M  = Fecha real (TIMESTAMPTZ via coerce_aware; nunca now())
    N  = color; O = nota (e.g. 'DESC 25%' -> informativa, NO se re-aplica);
    P  = cliente (texto libre, D7) -> upsert Cliente por nombre normalizado
La hoja VENTAS recalculada (2026-08) tiene #VALUE! en J/K/L en cada fila con
datos -> NO es usable: la fuente real de las ventas historicas es
csv/ARPIA - VENTAS.csv (ver ``_leer_ventas_csv``), usada cuando existe junto al
source. Con la hoja legacy (libros mini/contrato) se respeta su layout; las 3
filas R12..R14 sin columna A son SCOPE OUT (VTA-4): se reportan y no se cargan.

Destock (VTA-3): tras insertar TODAS las ventas se computa una unica
explosion agregada por producto/variante via ``explosion_materiales`` y se
aplica ``descontar_stock`` en lote (SELECT ... FOR UPDATE, consistente con
inventory.descarto_stock). Stock insuficiente -> DomainError propagada
(InsufficientStockError 409) -> la envoltura ``session_scope`` hace rollback de
fase (EXM-4): cero ventas residuales, causa reportada.

Idempotencia (NFR-1/EXM-3): la fase es re-ejecutable sin duplicar.  La
columna P del Excel contiene texto libre que puede repetirse (e.g.
'TOTEBAG' vendido 2x a 'Maira *Comic' la misma fecha con el mismo precio y
costo) -> la clave natural usa FILA_DATA (fecha, cliente, producto,
variante, cantidad, precio, costo) con un guard CUANTITATIVO: si la DB ya
contiene >= al numero de filas del plan para esa clave, la fila se salta; si
una corrida anterior inserto parcialmente, se completan las restantes. Esto
distingue dos ventas reales identicas entre si de un re-run.

El runner F5 se registra en ``migrate/__init__.py`` (FASES_IMPLEMENTADAS+F5).
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from sqlalchemy import func, select

from app.core.exceptions import EntityNotFoundError
from app.models import (
    CategoriaInsumo,
    Cliente,
    DetalleVenta,
    Insumo,
    Producto,
    VarianteProducto,
    Venta,
)
from app.services.inventory import descontar_stock, explosion_materiales
from migrate.catalog import clave_normalizada, normalizar_nombre
from migrate.context import MigrationContext, session_scope
from migrate.loaders import SHEET_BOUNDS, HojaInexistenteError, LibroMigracion
from migrate.normalize import coerce_aware, normalizar_decimal

# Columnas reales de la hoja VENTAS (verificadas contra ARPIA.xlsx 2026-08-08).
COL_PRODUCTO = "A"
COLS_VARIANTE = ("B", "C", "D", "E", "F")
COL_PRECIO = "G"
COL_COSTO = "H"
COL_FECHA = "M"
COL_NOTA = "O"
COL_CLIENTE = "P"

HOJA_VENTAS = "VENTAS"

# Nombres del Excel que NO matchean 1:1 con el catalogo F1 (key normalizada ->
# nombre de catalogo); el resto se busca directamente por clave normalizada.
ALIASES_VENTAS_A_CATALOGO: dict[str, str] = {
    "totebag": "Tote Bag Arpia",
    "blusa arpia manga larga": "Blusa Manga Larga",
}

# --- VENTAS from CSV (source of truth for the recalculated workbook) ---------
# The recalculated 16-sheet workbook's VENTAS sheet has #VALUE! on J/K/L in
# every data row, so historical sales come from csv/ARPIA - VENTAS.csv (next to
# the workbook). Its columns A..P match the VENTAS sheet positionally; header
# is file line 0, real data lines 1..21 (0-indexed after the header) and junk
# ($0 / TOTAL ARPIA / empty) from line 22 on.
NOMBRE_CSV_VENTAS = "ARPIA - VENTAS.csv"
FILAS_CSV_VENTAS = 21
_COLS_CSV_VENTAS = "ABCDEFGHIJKLMNOP"


def _resolver_csv_ventas(source: Path) -> Path | None:
    """csv/ARPIA - VENTAS.csv next to the workbook, when it exists."""
    ruta = source.parent / "csv" / NOMBRE_CSV_VENTAS
    return ruta if ruta.exists() else None


def _leer_ventas_csv(ruta: Path) -> list[dict[str, object]]:
    """Parse the VENTAS CSV into loader-shaped rows (col-letter keys A..P).

    Precio/costo '$295.000' -> Decimal('295000') (strip '$' and spaces; the
    Excel thousands dots are handled by normalizar_decimal); fecha '13/12/2025'
    (dd/mm/yyyy) -> naive datetime; tallas/nota/cliente stay as text. Only
    lines 1..21 (0-indexed after the header) are real; the rest is ignored.
    """
    filas: list[dict[str, object]] = []
    with ruta.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        next(reader, None)  # header line 0
        for idx, cells in enumerate(reader, start=1):
            if idx > FILAS_CSV_VENTAS:
                break
            fila: dict[str, object] = {}
            for col, valor in zip(_COLS_CSV_VENTAS, cells, strict=False):
                if valor is None or valor == "":
                    continue
                if col in (COL_PRECIO, COL_COSTO):
                    fila[col] = normalizar_decimal(valor.strip().lstrip("$").replace(" ", ""))
                elif col == COL_FECHA:
                    try:
                        fila[col] = datetime.strptime(valor.strip(), "%d/%m/%Y")
                    except ValueError:
                        fila[col] = None  # plan_ventas reports it as sin_fecha (D5)
                else:
                    fila[col] = valor.strip()
            filas.append(fila)
    return filas


def resolver_nombre_producto(excel: object) -> str:
    """Nombre de la venta -> nombre catalogado (alias o normalizado)."""
    nombre = normalizar_nombre(excel)
    return ALIASES_VENTAS_A_CATALOGO.get(clave_normalizada(nombre), nombre)


@dataclass(frozen=True)
class VentaPlanLinea:
    """Una venta planificada (precio tal-cual, costo FULL, fecha real)."""

    producto_nombre: str
    variante_nombre: str | None
    cantidad: Decimal
    precio: Decimal
    costo: Decimal
    fecha: datetime
    cliente_nombre: str | None
    hoja: str
    fila: int
    nota: str | None = None


@dataclass
class VentasPlan:
    """Plan (dry-run) of the historical sales F5 would insert."""

    ventas: list[VentaPlanLinea] = field(default_factory=list)
    scope_out: int = 0  # filas sin producto (VTA-4): reportadas, no cargan
    sin_fecha: int = 0  # D5: fila sin fecha -> nunca now()
    sin_precio: int = 0  # EXM-2: precio/costo no interpretable

    @property
    def conteo_ventas(self) -> int:
        return len(self.ventas)


def _variante_de_fila(fila: dict[str, object]) -> str | None:
    """Primera columna B..F con valor (talla/variante) de la fila."""
    for col in COLS_VARIANTE:
        valor = fila.get(col)
        if isinstance(valor, str) and valor.strip():
            return normalizar_nombre(valor)
    return None


def plan_ventas(libro, report=None, ruta_csv: Path | None = None) -> VentasPlan:
    """Armar el plan (puro) desde la hoja VENTAS o, cuando existe, desde
    csv/ARPIA - VENTAS.csv (la hoja recalculada tiene #VALUE! y no es usable).

    Ambos orígenes devuelven filas con claves de letra de columna (A..P), asi
    que el flujo de parseo es identico; el contrato de VentaPlanLinea se
    mantiene (hoja='VENTAS', fila = indice real 1-based del origen)."""
    plan = VentasPlan()
    if ruta_csv is not None and ruta_csv.exists():
        # CSV is the source of truth for the historical sales.
        filas = _leer_ventas_csv(ruta_csv)
        inicio = 1  # fila 1-based del CSV (header = fila 0)
    else:
        if HOJA_VENTAS not in SHEET_BOUNDS:
            return plan
        try:
            lectura = libro.leer_hoja(HOJA_VENTAS, report=report)
        except HojaInexistenteError:
            if report:
                report.warn(
                    HOJA_VENTAS, None, None, "hoja ausente en este workbook; omitida (0 ventas)"
                )
            return plan
        filas = lectura.filas
        inicio = SHEET_BOUNDS[HOJA_VENTAS][0]
    for fila_idx, fila in enumerate(filas, start=inicio):
        producto_excel = fila.get(COL_PRODUCTO)
        if not isinstance(producto_excel, str) or not producto_excel.strip():
            # VTA-4: sin producto -> SCOPE OUT
            plan.scope_out += 1
            if report:
                report.warn(
                    HOJA_VENTAS,
                    fila_idx,
                    COL_PRODUCTO,
                    "venta sin producto (col A) -> SCOPE OUT, no migra",
                )
            continue
        producto = resolver_nombre_producto(producto_excel)
        fecha_raw = fila.get(COL_FECHA)
        if fecha_raw is None:
            plan.sin_fecha += 1
            if report:
                report.warn(
                    HOJA_VENTAS,
                    fila_idx,
                    COL_FECHA,
                    f"{producto}: fecha vacia -> sin venta (D5, nunca now())",
                )
            continue
        fecha = coerce_aware(fecha_raw)
        precio = normalizar_decimal(fila.get(COL_PRECIO))
        if precio is None or precio <= 0:
            plan.sin_precio += 1
            if report:
                report.warn(
                    HOJA_VENTAS,
                    fila_idx,
                    COL_PRECIO,
                    f"{producto}: precio {fila.get(COL_PRECIO)!r} no "
                    f"interpretable -> fila excluida (EXM-2)",
                )
            continue
        costo = normalizar_decimal(fila.get(COL_COSTO))
        if costo is None or costo <= 0:
            plan.sin_precio += 1
            if report:
                report.warn(
                    HOJA_VENTAS,
                    fila_idx,
                    COL_COSTO,
                    f"{producto}: costo {fila.get(COL_COSTO)!r} no "
                    f"interpretable -> fila excluida (EXM-2)",
                )
            continue
        cliente_raw = fila.get(COL_CLIENTE)
        cliente = (
            normalizar_nombre(cliente_raw)
            if isinstance(cliente_raw, str) and cliente_raw.strip()
            else None
        )
        nota = fila.get(COL_NOTA)
        nota_txt = normalizar_nombre(nota) if isinstance(nota, str) else None
        if nota_txt:
            if report:
                report.info(
                    HOJA_VENTAS,
                    fila_idx,
                    COL_NOTA,
                    f"{producto}: nota {nota_txt!r} (precio YA descontado, "
                    f"VTA-2: descuento no re-aplicado)",
                )
        plan.ventas.append(
            VentaPlanLinea(
                producto_nombre=producto,
                variante_nombre=_variante_de_fila(fila),
                cantidad=Decimal("1"),
                precio=precio,
                costo=costo,
                fecha=fecha,
                cliente_nombre=cliente,
                hoja=HOJA_VENTAS,
                fila=fila_idx,
                nota=nota_txt,
            )
        )
    return plan


# ------------------------------------------------------------------------- #
# DB apply (clave natural cuantitativa + destock batch con rollback)
# ------------------------------------------------------------------------- #


def _fecha_key(fecha) -> str:
    """Key estable de la fecha (ISO en UTC) para el guard de idempotencia."""
    return fecha.isoformat()


def _moneda(valor: Decimal) -> Decimal:
    """Redondea a la escala NUMERIC(15,4) real de las columnas (PostgreSQL
    redondea el excedente al persistir; el redondeo debe ser identico en la
    clave de idempotencia, o un re-run nunca matchea lo guardado)."""
    return valor.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _upsert_cliente(db, nombre: str | None) -> int | None:
    """get-or-create Cliente por nombre normalizado (upsert, dedup manual)."""
    if not nombre:
        return None
    limpio = normalizar_nombre(nombre)
    cli = db.scalar(select(Cliente).where(Cliente.nombre == limpio))
    if cli is None:
        cli = Cliente(nombre=limpio)
        db.add(cli)
        db.flush()
    return cli.id


def _clave_venta(
    venta: VentaPlanLinea, producto_id: int, variante_id: int | None, cliente_id: int | None
) -> tuple:
    """Clave natural: fecha + cliente + producto + variante + cant + precio + costo.

    Precio/costo se redondean a la escala NUMERIC(15,4) (``_moneda``): es
    EXACTAMENTE lo que PostgreSQL persiste, asi el re-run matchea.
    """
    return (
        _fecha_key(venta.fecha),
        cliente_id,
        producto_id,
        variante_id,
        venta.cantidad,
        _moneda(venta.precio),
        _moneda(venta.costo),
    )


def _contar_existentes(db, clave) -> int:
    """Ventas ya persistentes con esta clave natural (idempotencia)."""
    fecha_key, cliente_id, producto_id, variante_id, cantidad, precio, costo = clave
    stmt = (
        select(func.count(Venta.id))
        .join(DetalleVenta, DetalleVenta.venta_id == Venta.id)
        .where(Venta.fecha == datetime.fromisoformat(fecha_key))
    )
    if cliente_id is None:
        stmt = stmt.where(Venta.cliente_id.is_(None))
    else:
        stmt = stmt.where(Venta.cliente_id == cliente_id)
    stmt = stmt.where(
        DetalleVenta.producto_id == producto_id,
        DetalleVenta.cantidad == cantidad,
        DetalleVenta.precio_unitario_aplicado == precio,
        DetalleVenta.costo_unitario_aplicado == costo,
    )
    if variante_id is None:
        stmt = stmt.where(DetalleVenta.variante_id.is_(None))
    else:
        stmt = stmt.where(DetalleVenta.variante_id == variante_id)
    return db.scalar(stmt) or 0


def _producto_por_nombre(db, nombre: str) -> Producto | None:
    """Producto del catalogo por clave normalizada (dedup manual, == F1)."""
    clave = clave_normalizada(nombre)
    for p in db.scalars(select(Producto)).all():
        if clave_normalizada(p.nombre) == clave:
            return p
    return None


def _variante_por_nombre(db, producto_id: int, nombre: str | None) -> int | None:
    """Variante del producto por nombre normalizado; None si no existe."""
    if not nombre:
        return None
    limpio = normalizar_nombre(nombre)
    var = db.scalar(
        select(VarianteProducto).where(
            VarianteProducto.producto_id == producto_id,
            VarianteProducto.nombre_variante == limpio,
        )
    )
    return var.id if var is not None else None


def _es_empaque_consumible(db, insumo_id: int) -> bool:
    """Empaques de combo (Caja/Vela/Papel/Envio/...) son consumibles SIN
    inventario rastreable: no estan en OCT25 ni tienen compras WAC. F5 los
    excluye del destock (VTA-3); de lo contrario la venta de un combo falla
    con InsufficientStockError aun con stock real de los materiales."""
    insumo = db.get(Insumo, insumo_id)
    if insumo is None or insumo.categoria_id is None:
        return False
    cat = db.get(CategoriaInsumo, insumo.categoria_id)
    return cat is not None and cat.nombre == "Empaques"


def _descontar_stock_tolerante(db, explosiones: dict[int, Decimal], report=None) -> None:
    """Destock de la migracion historica que PERMITE stock negativo.

    Decision de negocio (2026-08): el workbook no registra compras suficientes
    para toda la produccion vendida (el negocio vendio de stock previo no
    registrado). Igual que ``inventory.descontar_stock`` bloquea con FOR UPDATE,
    pero en vez de lanzar 409 descuenta y reporta WARN por insumo deficitario.
    Nunca se usa en el runtime de la app: solo en F5 con permitir_deficit=True.
    """

    for insumo_id in sorted(explosiones):
        cantidad = explosiones[insumo_id]
        insumo = db.get(Insumo, insumo_id, with_for_update=True, populate_existing=True)
        if insumo is None:
            raise EntityNotFoundError("Insumo", insumo_id)
        if insumo.stock_actual < cantidad and report:
            report.warn(
                "F5",
                None,
                None,
                f"stock insuficiente para '{insumo.nombre}': disponible "
                f"{insumo.stock_actual}, requerido {cantidad}; stock quedara "
                f"negativo (deficit historico permitido)",
            )
        insumo.stock_actual -= cantidad


def aplicar_ventas(
    db, plan: VentasPlan, report=None, canal_venta: str = "feria", permitir_deficit: bool = False
) -> dict[str, int]:
    """INSERT directo Venta + Detalle_Ventas (fecha real, canal='feria', costo
    snapshot = H del Excel) + destock en lote al final (VTA-3).

    Idempotente (NFR-1/EXM-3): clave natural (fecha, cliente, producto,
    variante, cantidad, precio, costo) con guard CUANTITATIVO por corrida; el
    caller (session_scope) controla el commit unico y ante 409 de destock la
    fase completa revierte (EXM-4): cero ventas residuales.

    ``permitir_deficit`` (decision de negocio 2026-08): el historico de ventas
    supera el inventario comprado (Lino vertigo 4.8m vs 1.8m, Satin elastico
    4.8 vs 2, Tela a cuadros 1.8 vs 1) -- el negocio vendio de stock previo no
    registrado. Con True, el destock tolerante descuenta dejando stock NEGATIVO
    y reporta WARN por insumo deficitario, SIN rollback. El servicio runtime
    inventory.descontar_stock NO cambia (sigue protegiendo ventas en vivo).
    """
    res: dict[str, int] = {"insertadas": 0, "ya_presentes": 0, "omitidas": 0, "destock": 0}

    # 1) Resolver cada linea del plan a ids de catalogo (upsert cliente) y
    #    contar cuantas veces aparece cada clave natural (guard cuantitativo).
    esperadas: Counter = Counter()
    resueltas: list[tuple[VentaPlanLinea, int, int | None, int | None]] = []
    for venta in plan.ventas:
        producto = _producto_por_nombre(db, venta.producto_nombre)
        if producto is None:
            res["omitidas"] += 1
            if report:
                report.error(
                    venta.hoja,
                    venta.fila,
                    COL_PRODUCTO,
                    f"{venta.producto_nombre}: producto ausente en catalogo; "
                    f"venta no aplicada (correr F1 antes)",
                )
            continue
        cliente_id = _upsert_cliente(db, venta.cliente_nombre)
        variante_id = _variante_por_nombre(db, producto.id, venta.variante_nombre)
        esperadas[_clave_venta(venta, producto.id, variante_id, cliente_id)] += 1
        resueltas.append((venta, producto.id, variante_id, cliente_id))

    # 2) Ventas ya persistidas con esa clave (una sola COUNT por clave).
    ya_existentes: dict[tuple, int] = {}
    for clave in esperadas:
        ya_existentes[clave] = _contar_existentes(db, clave)

    # 3) Insertar solo las lineas que faltan para completar el esperado de su
    #    clave; agregar la explosion SOLO de las lineas insertadas (las ya
    #    existentes ya consumieron stock en su corrida anterior).
    explosiones: dict[int, Decimal] = {}
    insertadas_por_clave: Counter = Counter()
    for venta, producto_id, variante_id, cliente_id in resueltas:
        clave = _clave_venta(venta, producto_id, variante_id, cliente_id)
        if ya_existentes[clave] + insertadas_por_clave[clave] >= esperadas[clave]:
            insertadas_por_clave[clave] += 1
            res["ya_presentes"] += 1
            continue
        nueva = Venta(
            fecha=venta.fecha,
            cliente_id=cliente_id,
            canal_venta=canal_venta,  # decision producto: 'feria' (default modelo)
            descuento_porcentaje=Decimal("0"),  # VTA-2: precio ya descontado
            estado="completada",
            total_venta=venta.cantidad * venta.precio,
        )
        db.add(nueva)
        db.flush()
        db.add(
            DetalleVenta(
                venta_id=nueva.id,
                producto_id=producto_id,
                variante_id=variante_id,
                cantidad=venta.cantidad,
                precio_unitario_aplicado=venta.precio,
                costo_unitario_aplicado=venta.costo,  # snapshot FULL H del Excel
            )
        )
        for insumo_id, qty in explosion_materiales(
            db, producto_id, variante_id, venta.cantidad
        ).items():
            if _es_empaque_consumible(db, insumo_id):
                continue  # empaques de combo sin inventario rastreable
            explosiones[insumo_id] = explosiones.get(insumo_id, Decimal("0")) + qty
        insertadas_por_clave[clave] += 1
        res["insertadas"] += 1
        if report:
            report.info(
                venta.hoja,
                venta.fila,
                None,
                f"venta {venta.producto_nombre} {venta.variante_nombre or ''} "
                f"cant {venta.cantidad} @ {venta.precio} costo {venta.costo} "
                f"fecha {venta.fecha.date()} canal {canal_venta}",
            )

    # 4) Destock en lote (VTA-3): 409 -> sube -> rollback de fase (EXM-4).
    if explosiones:
        if permitir_deficit:
            _descontar_stock_tolerante(db, explosiones, report)
        else:
            descontar_stock(db, explosiones)
        res["destock"] = len(explosiones)
        if report:
            report.info(
                "F5",
                None,
                None,
                f"destock batch: {len(explosiones)} insumos consumidos "
                f"(stock FOR UPDATE, unica transaccion"
                f"{', deficit permitido' if permitir_deficit else ''})",
            )

    if report:
        report.info(
            "F5",
            None,
            None,
            f"ventas aplicadas: {res['insertadas']} insertadas, "
            f"{res['ya_presentes']} ya-presentes, {res['omitidas']} omitidas",
        )
    return res


# ------------------------------------------------------------------------- #
# Phase entry point (F5 runner registered in migrate/__init__.py)
# ------------------------------------------------------------------------- #


def cargar_ventas(ctx: MigrationContext) -> VentasPlan:
    """F5 runner: planifica las ventas historias y, en commit, las inserta en
    una sola transaccion (EXM-4), con descuento directo + destock en lote; es
    idempotente (NFR-1). En dry-run 0 escrituras (NFR-2). El canal por defecto
    es 'feria' (decision de producto); --canal del CLI lo sobrescribe."""
    report = ctx.report
    canal = ctx.options.canal_venta or "feria"
    ruta_csv = _resolver_csv_ventas(ctx.options.source)
    if ruta_csv is not None:
        report.info(
            "F5",
            None,
            None,
            f"ventas leidas desde {ruta_csv.name} (la hoja VENTAS del xlsx "
            f"tiene #VALUE! y no es usable)",
        )
    with LibroMigracion(ctx.options.source) as libro:
        plan = plan_ventas(libro, report, ruta_csv=ruta_csv)

    report.info(
        "F5",
        None,
        None,
        f"plan ventas: {plan.conteo_ventas} ventas | scope out "
        f"{plan.scope_out} | sin fecha {plan.sin_fecha} | sin precio/costo "
        f"{plan.sin_precio}",
    )
    if ctx.options.modo == "commit" and ctx.session is not None:
        with session_scope(ctx, ctx.session) as db:
            # permitir_deficit=True: decision de negocio 2026-08 (el historico
            # supera el inventario comprado; se registra todo con alerta WARN).
            aplicar_ventas(db, plan, report, canal_venta=canal, permitir_deficit=True)
    return plan


__all__ = [
    "VentaPlanLinea",
    "VentasPlan",
    "plan_ventas",
    "aplicar_ventas",
    "cargar_ventas",
]
