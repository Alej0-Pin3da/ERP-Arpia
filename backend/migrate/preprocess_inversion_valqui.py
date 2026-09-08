"""Standalone CSV preprocessor: INVERSION VALQUI -> stockable vs non-stockable.

Parses the `ARPIA - INVERSION VALQUI (1).csv` export (left purchase block
A:G + right price block H:L) and separates rows into:

- stockable candidates -> Insumos + Compras_Insumos (WAC), LOT total / qty;
- movement candidates -> Movimientos_Financieros (Inversion/Gasto, tipo
  case-sensitive per CHECK ck_movimientos_tipo).

Modeled on `backfill_precios_costos.py` (F8-style): Report from
migrate.report + catalog helpers, --dry-run default, JSON audit, exit 1 on
ERROR. --apply still performs ZERO DB writes (no session is wired here);
it only requires explicit --yes and marks the plan as owner-validated.

Hard rules (never violated):
- column D/C/J carry LOT totals: unit cost = total / canonical qty, the
  D value is NEVER stored as a unit price;
- header rows (L2/L97), the L137 total row and empty rows never become data;
- missing qty / supplier / date / cost -> WARN + skip (EXM-2/D5), NEVER
  inferred and never now();
- Direccion has no DB column -> kept as a dropped-nota in the JSON only.

The 7 owner decisions (every WARN is tagged [DEC-n] and grouped):
- DEC-1: stockable (BOM universe + aliases) vs non-stockable (finanzas);
- DEC-2: LOT total -> unitario (D / cantidad);
- DEC-3: combined / Kilotelas-block qty (A-or-C fallback) -> canonical unit;
- DEC-4: missing data -> omit + WARN, never infer;
- DEC-5: right sub-table unique-source vs discarded duplicate;
- DEC-6: supplier normalize + dedup (Gerrajes and Herrajes stay DISTINCT);
- DEC-7: exact duplicates, 2026 post-cut date risk, checksum vs L137 total.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from migrate.catalog import (
    _es_material_valido,
    clasificar_material,
    clave_normalizada,
    normalizar_nombre,
)
from migrate.finanzas import clasificar_tipo
from migrate.normalize import (
    ClaveFecha,
    fecha_para_fila,
    normalizar_area_m2,
    normalizar_decimal,
    parsear_cantidad_unidad,
    unidad_canonica,
)
from migrate.purchases import (
    ALIASES_COMPRA_A_CATALOGO,
    normalizar_cantidad_compra,
)
from migrate.report import LEVEL_ERROR, Report

ESCALA = Decimal("0.0001")
EXPECTED_TOTAL = Decimal("13548941")  # L137 checksum, excluded from data.
WAC_CUTOFF = datetime(2025, 10, 31)  # post-OCT25 purchases flag date risk.
SOCIO_VALQUI = "Valqui"  # source file attribution (finanzas SOCIO_POR_HOJA).

DECISIONES = (
    ("DEC-1", "Clasificacion stockable (BOM) vs no-stockable (finanzas)"),
    ("DEC-2", "Costo de lote -> unitario (total / cantidad, nunca D directo)"),
    ("DEC-3", "Cantidad combinada / bloque Kilotelas (A-or-C) -> canonica"),
    ("DEC-4", "Dato faltante (cantidad/proveedor/fecha/costo) -> omitir, nunca inferir"),
    ("DEC-5", "Sub-tabla derecha: fuente unica vs duplicada descartada"),
    ("DEC-6", "Proveedores: normalizar + dedup (Gerrajes != Herrajes)"),
    ("DEC-7", "Duplicados exactos + riesgo fecha 2026 post-corte + checksum"),
)

# Normalized-key substrings that force the finanzas route even when the name
# looks like material. "maquina" covers the 3 SINGER rows; "aguja
# fileteadora" stays stockable on purpose (consumable notion, no keyword hit).
NON_STOCKABLE_KEYWORDS: tuple[str, ...] = (
    "termofijadora",
    "maquina",
    "miquina",
    "singer",
    "hosting",
    "dominio",
    "madera",
    "patron",
    "curso",
    "maniqui",
    "stand",
    "fotografia",
    "video",
    "brazo estampar",
    "lampara",
    "tijera",
    "regleta",
    "papelera",
    "extension",
    "modisteria",
    "teflon",
    "cinta termica",
    "envio",
    "prestamo",
)

# Normalized supplier key -> canonical display. Gerrajes (Cl 15 #7-46 notions
# store) and Herrajes (2026 tote hardware) are DIFFERENT businesses: they are
# kept distinct and their similarity is flagged for the owner (DEC-6).
SUPPLIER_ALIASES: dict[str, str] = {
    "gerrajes": "Gerrajes",
    "herrajes": "Herrajes",
    "kilotelas": "Kilotelas",
    "corseteria": "Corseteria",
    "la corseteria": "Corseteria",
    "mercado libre": "MercadoLibre",
    "mercadolibre": "MercadoLibre",
    "las 3bbb premium": "Las 3BBB",
    "las 3bbb": "Las 3BBB",
    "hilos y suministros ltda": "Hilos y Suministros",
    "hilos y suministros": "Hilos y Suministros",
    "singer pereira": "SINGER Pereira",
    "colombiahosting": "ColombiaHosting",
    "atenea bordados y encajes": "Atenea Bordados",
    "boutique de los empaques": "Boutique de los Empaques",
    "gamma impresos y marquillas": "GAMMA Marquillas",
    "santa rosa": "Santa Rosa",
    "mil adornos": "Mil Adornos",
    "gato bandido": "Gato Bandido",
    "casatextil": "CasaTextil",
    "textiles f y m": "Textiles F y M",
    "the lingerie formula": "The Lingerie Formula",
    "almacen de la 6ta": "Almacen de la 6ta",
    "la sesta": "La Sesta",
    "tienda pequena misma cuadra herrajes": "Tienda Herrajes (cuadra)",
}

PLACEHOLDERS = frozenset({"", "-", "--", "n/a", "na", "s/n", "nn", "ninguno", "no aplica"})
_HEADER_TOKENS = frozenset({"cantidad", "producto", "costo", "total"})

_TOKEN_RE = re.compile(r"([+-]?\d+(?:[.,]\d+)?)\s*([A-Za-z\xba\xb2]+)")
_NUMERO_RE = re.compile(r"^[+-]?\d+(?:[.,]\d+)?$")
_DEC_TAG_RE = re.compile(r"^\[(DEC-\d)\]")


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(ESCALA, rounding=ROUND_HALF_UP)


def parse_money(valor: object) -> Decimal | None:
    """Colombian money text ($960.000 / "$66,00" / $2.367.000) -> Decimal.

    Strips currency symbols/quotes, then delegates to normalizar_decimal
    (thousands `.` vs comma-decimal); #DIV/0! and junk -> None. Never float().
    """
    if isinstance(valor, (int, float, Decimal)):
        try:
            return Decimal(str(valor))
        except InvalidOperation:
            return None
    texto = str(valor or "").strip().strip("\"'").replace("$", "").replace(" ", "")
    if not texto or texto.startswith("#"):
        return None
    return normalizar_decimal(texto)


def parse_fecha(valor: object) -> datetime | None:
    """DD/MM/YYYY export dates -> naive datetime; None when empty/illegible."""
    if isinstance(valor, datetime):
        return valor
    texto = str(valor or "").strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%d/%m/%Y")
    except ValueError:
        return None


def _unidad_objetivo(nombre: str) -> str:
    """Canonical purchase unit for an insumo name (same classifier as F1)."""
    try:
        return clasificar_material(nombre)[1]
    except Exception:
        return "un"


def parse_cantidad(texto: object, unidad_obj: str) -> tuple[Decimal | None, str | None]:
    """Quantity cell -> (canonical qty, canonical unit).

    Pipeline-faithful first (bare numbers + `normalizar_cantidad_compra`);
    multi-token fallback ("4 mts + 90 cms") sums length tokens into `unidad_obj`
    and keeps peso tokens in their own unit; mixed families -> (None, None).
    """
    if texto is None:
        return None, None
    crudo = str(texto).strip()
    if not crudo or crudo.startswith("#"):
        return None, None
    if _NUMERO_RE.match(crudo):  # CSV bare numbers arrive as strings.
        numero = normalizar_decimal(crudo)
        if numero is not None and numero > 0:
            return numero, unidad_canonica(unidad_obj)
        return None, None
    directo = normalizar_cantidad_compra(crudo, unidad_obj)
    if directo is not None:
        return directo, unidad_canonica(unidad_obj)
    tokens = _TOKEN_RE.findall(crudo)
    if len(tokens) < 2:
        # Single peso token under a length default (e.g. "100 gms" Hilaza):
        # honor the cell unit instead of dropping the row silently.
        if len(tokens) == 1:
            cantidad = normalizar_decimal(tokens[0][0])
            unidad = unidad_canonica(tokens[0][1])
            if cantidad is not None and cantidad > 0 and unidad in ("g", "kg", "un"):
                return cantidad, unidad
        return None, None
    total, unidad_final = Decimal("0"), None
    for numero_txt, unidad_txt in tokens:
        cantidad = normalizar_decimal(numero_txt)
        unidad = unidad_canonica(unidad_txt)
        if cantidad is None or cantidad <= 0:
            return None, None
        if unidad == "cm":
            cantidad, unidad = cantidad * Decimal("0.01"), "m"
        if unidad_final is None:
            unidad_final = unidad
        elif unidad != unidad_final:
            return None, None  # mixed families need an owner call.
        total += cantidad
    if total <= 0 or unidad_final is None:
        return None, None
    return total, unidad_final


@dataclass(frozen=True)
class StockCandidate:
    linea: int
    producto: str
    cantidad: str
    unidad: str
    costo_lote: str
    costo_unitario: str
    fecha: str
    fecha_heredada: bool
    proveedor: str
    fuente: str  # 'izquierda' | 'derecha-unica'
    duplicado: bool = False
    post_corte: bool = False
    revision_dueno: bool = False


@dataclass(frozen=True)
class MovementCandidate:
    linea: int
    descripcion: str
    monto: str
    tipo: str  # 'Inversion' | 'Gasto' (case-sensitive CHECK).
    fecha: str
    socio: str
    proveedor_nota: str = ""


@dataclass(frozen=True)
class RightDecision:
    linea: int
    producto: str
    decision: str  # 'unica' | 'descartada-duplicada' | 'omitida'
    detalle: str


@dataclass
class SupplierMap:
    canonicos: dict[str, dict] = field(default_factory=dict)

    def registrar(self, crudo: object, linea: int) -> str | None:
        nombre = normalizar_nombre(crudo)
        if nombre.casefold() in PLACEHOLDERS:
            return None
        clave = clave_normalizada(nombre)
        display = SUPPLIER_ALIASES.get(clave, nombre)
        entrada = self.canonicos.setdefault(
            display, {"variantes": set(), "lineas": [], "conteo": 0}
        )
        entrada["variantes"].add(nombre)
        entrada["lineas"].append(linea)
        entrada["conteo"] += 1
        return display


def _cargar_universo(report: Report) -> tuple[dict[str, str], str]:
    """BOM universe like F2 (_universo_bom + ALIASES); keyword fallback first.

    Non-stockable keywords always win (equipment/services are never WAC even
    if a word collides with the BOM universe); rows outside the universe are
    kept as stockable candidates flagged revision_dueno (DEC-1) instead of
    being silently dropped.
    """
    universo: dict[str, str] = {}
    origen = "fallback-keywords"
    root = Path(__file__).resolve().parents[2]
    workbook = root / "ARPIA.xlsx"
    if workbook.exists():
        try:
            from migrate.loaders import LibroMigracion
            from migrate.purchases import _universo_bom

            with LibroMigracion(workbook) as libro:
                universo = _universo_bom(libro, report)
            origen = "ARPIA.xlsx"
        except Exception as exc:  # standalone must never die on the workbook.
            report.warn("UNIVERSO", None, None, f"[DEC-1] workbook ilegible ({exc}); fallback")
    for clave, canonico in ALIASES_COMPRA_A_CATALOGO.items():
        universo.setdefault(clave, canonico)
    return universo, origen


def _es_no_stockable(nombre: str) -> str | None:
    clave = clave_normalizada(nombre)
    for keyword in NON_STOCKABLE_KEYWORDS:
        if keyword in clave:
            return keyword
    return None


def _leer_csv(path: Path, report: Report) -> tuple[list[list[str]], dict[str, int] | None]:
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            filas = list(csv.reader(fh))
    except OSError as exc:
        report.error("CSV", None, None, f"no se pudo leer {path}: {exc}")
        return [], None
    derecha: dict[str, int] | None = None
    for fila in filas:
        for idx, celda in enumerate(fila):
            if "largo" in str(celda or "").casefold() and idx >= 1:
                # idx points at 'Largo CMS'; Producto is one column left.
                derecha = {"nombre": idx - 1, "largo": idx, "ancho": idx + 1,
                           "valor": idx + 2, "unitario": idx + 3}
                break
        if derecha is not None:
            break
    if derecha is None:
        report.warn("CSV", None, None, "[DEC-5] cabecera derecha (Largo CMS) no hallada")
    return filas, derecha


def plan_izquierda(
    filas: list[list[str]],
    universo: dict[str, str],
    report: Report,
    proveedores: SupplierMap,
    ultima_fecha: dict | None = None,
) -> tuple[list[StockCandidate], list[MovementCandidate], dict]:
    """Left block A:G -> stock vs movement candidates (pure planner)."""
    stocks, movimientos = [], []
    vistos: set[tuple] = set()
    if ultima_fecha is None:
        ultima_fecha = {}
    stats = {"omitidas": 0, "duplicadas": 0, "post_corte": 0, "lote_suma": Decimal("0")}
    for linea, fila in enumerate(filas, start=1):
        cols = list(fila) + [""] * 8
        cant_raw, nombre_raw, costo_raw = cols[0].strip(), cols[1].strip(), cols[3].strip()
        fecha_raw, prov_raw, direcc = cols[4].strip(), cols[5].strip(), cols[6].strip()
        if not any(c.strip() for c in fila):
            continue
        if clave_normalizada(cant_raw) == "cantidad" or not nombre_raw:
            continue  # L1 vacia / cabeceras L2 y L97.
        if clave_normalizada(nombre_raw) in _HEADER_TOKENS and not costo_raw:
            continue
        if clave_normalizada(nombre_raw) == "total":
            continue  # L137 checksum, nunca producto.
        nombre = normalizar_nombre(nombre_raw)
        if not _es_material_valido(nombre):
            continue
        monto = parse_money(costo_raw)
        if monto is None or monto <= 0:
            stats["omitidas"] += 1
            report.warn("VALQUI", linea, "D",
                        f"[DEC-4] {nombre!r}: costo {costo_raw!r} vacio/ilegible; fila omitida")
            continue
        stats["lote_suma"] += monto
        # DEC-7 early duplicate scan: exact (nombre + monto + fecha cruda)
        # repeat is flagged even when the row is later skipped (Cajas L83-84,
        # Hilaza L75-76): the owner confirms whether they are two real buys.
        dup_key = (clave_normalizada(nombre), str(monto), fecha_raw)
        duplicado = dup_key in vistos
        if duplicado:
            stats["duplicadas"] += 1
            report.warn("VALQUI", linea, None,
                        f"[DEC-7] {nombre!r}: duplicado exacto (nombre+monto+fecha); "
                        f"el dueno confirma si son dos compras reales")
        vistos.add(dup_key)
        keyword = _es_no_stockable(nombre)
        if keyword is not None:
            fecha = parse_fecha(fecha_raw)
            if fecha is None:
                stats["omitidas"] += 1
                report.warn("VALQUI", linea, "E",
                            f"[DEC-4] {nombre!r}: movimiento sin fecha; omitido (D5, nunca now())")
                continue
            movimientos.append(MovementCandidate(
                linea=linea, descripcion=nombre, monto=str(monto),
                tipo=clasificar_tipo(nombre), fecha=fecha.date().isoformat(),
                socio=SOCIO_VALQUI,
                proveedor_nota=normalizar_nombre(prov_raw) or "(sin proveedor)"))
            if fecha > WAC_CUTOFF:
                stats["post_corte"] += 1
                report.warn("VALQUI", linea, "E",
                            f"[DEC-7] {nombre!r} {fecha.date()}: posterior al corte "
                            f"WAC OCT25; el dueno confirma imputacion")
            continue
        # Stockable path: A-or-C fallback (bloque Kilotelas trae cantidad en C).
        qty_raw = cant_raw if cant_raw else cols[2].strip()
        unidad_obj = _unidad_objetivo(
            universo.get(clave_normalizada(nombre), nombre))
        cantidad, unidad = parse_cantidad(qty_raw, unidad_obj)
        if cantidad is None:
            stats["omitidas"] += 1
            report.warn("VALQUI", linea, "A",
                        f"[DEC-4] {nombre!r}: cantidad {qty_raw!r} no interpretable; "
                        f"fila excluida (EXM-2, nunca inferida)")
            continue
        if "," in (qty_raw or "") and parse_cantidad(qty_raw, unidad_obj)[0] is not None \
                and len(_TOKEN_RE.findall(qty_raw)) > 1:
            report.warn("VALQUI", linea, "A",
                        f"[DEC-3] {nombre!r}: cantidad combinada {qty_raw!r} sumada "
                        f"-> {cantidad} {unidad}; el dueno confirma")
        display = proveedores.registrar(prov_raw, linea)
        if display is None:
            stats["omitidas"] += 1
            hint = f" (col Direccion trae {direcc!r}, no se infiere)" if direcc else ""
            report.warn("VALQUI", linea, "F",
                        f"[DEC-4] {nombre!r}: sin proveedor{hint}; fila omitida, nunca inferido")
            continue
        clave_fecha = ClaveFecha(clave_normalizada(nombre))
        fecha = parse_fecha(fecha_raw)
        heredada = False
        if fecha is None:
            heredada_dt = fecha_para_fila(None, clave_fecha, ultima_fecha)
            if isinstance(heredada_dt, datetime):
                fecha = heredada_dt
                heredada = True
        else:
            ultima_fecha[clave_fecha] = fecha
        if fecha is None:
            stats["omitidas"] += 1
            report.warn("VALQUI", linea, "E",
                        f"[DEC-4] {nombre!r}: fecha vacia sin contigua heredable; "
                        f"omitida (D5, nunca now())")
            continue
        if heredada:
            report.warn("VALQUI", linea, "E",
                        f"[DEC-4] {nombre!r}: fecha heredada de fila contigua "
                        f"({fecha.date()}); el dueno confirma")
        unitario = _q(monto / cantidad)  # D es TOTAL de lote, nunca unitario (DEC-2).
        post_corte = fecha > WAC_CUTOFF
        if post_corte:
            stats["post_corte"] += 1
            report.warn("VALQUI", linea, "E",
                        f"[DEC-7] {nombre!r} {fecha.date()}: lote 2026 posterior al "
                        f"corte WAC OCT25; riesgo cronologico, el dueno confirma")
        en_universo = clave_normalizada(nombre) in universo
        if not en_universo:
            report.warn("VALQUI", linea, "B",
                        f"[DEC-1] {nombre!r}: fuera del universo BOM; se propone como "
                        f"stockable con revision del dueno (alternativa: movimiento)")
        stocks.append(StockCandidate(
            linea=linea, producto=universo.get(clave_normalizada(nombre), nombre),
            cantidad=str(cantidad), unidad=str(unidad or unidad_obj),
            costo_lote=str(monto), costo_unitario=str(unitario),
            fecha=fecha.date().isoformat(), fecha_heredada=heredada,
            proveedor=display, fuente="izquierda", duplicado=duplicado,
            post_corte=post_corte, revision_dueno=not en_universo))
    return stocks, movimientos, stats


def plan_derecha(
    filas: list[list[str]],
    cols: dict[str, int] | None,
    universo: dict[str, str],
    report: Report,
    ultima_fecha: dict,
) -> tuple[list[StockCandidate], list[RightDecision], Decimal]:
    """Right block H:L -> unique-source only (pure planner, DEC-5).

    Unique = nombre ausente en todo el bloque izquierdo (criterio
    _procesar_subtabla_derecha simplificado: el CSV derecho no trae fechas
    propias). Valor es TOTAL de lote; Unitario solo corrobora.
    """
    stocks, decisiones = [], []
    suma_valor = Decimal("0")
    if cols is None:
        return stocks, decisiones, suma_valor
    izquierda = set()
    for fila in filas:
        full = list(fila) + [""] * 8
        if len(full) > 1 and full[1].strip():
            izquierda.add(clave_normalizada(full[1]))
    for linea, fila in enumerate(filas, start=1):
        full = list(fila) + [""] * (max(cols.values()) + 2 - len(fila))
        nombre_raw = full[cols["nombre"]].strip() if cols["nombre"] < len(full) else ""
        if not nombre_raw or "producto" in nombre_raw.casefold():
            continue
        nombre = normalizar_nombre(nombre_raw)
        if not _es_material_valido(nombre):
            continue
        valor = parse_money(full[cols["valor"]])
        if valor is None or valor <= 0:
            continue  # #DIV/0! L70-76 y celdas vacias: se excluyen.
        suma_valor += valor
        clave = clave_normalizada(nombre)
        if clave in izquierda:
            decisiones.append(RightDecision(linea, nombre, "descartada-duplicada",
                                            "duplica el bloque izquierdo; no genera compra"))
            continue
        display = universo.get(clave, nombre)
        unidad_obj = _unidad_objetivo(display)
        largo = normalizar_decimal(full[cols["largo"]])
        ancho = normalizar_decimal(full[cols["ancho"]])
        cantidad = None
        if largo is not None and largo > 0:
            if unidad_canonica(unidad_obj) == "m":
                cantidad = largo * Decimal("0.01")  # K en cm -> metros.
            elif unidad_canonica(unidad_obj) == "cm2":
                cantidad = largo * (ancho if ancho and ancho > 0 else Decimal("1"))
            else:
                cantidad = largo
        if cantidad is None or cantidad <= 0:
            decisiones.append(RightDecision(linea, nombre, "omitida",
                                            f"[DEC-5] largo {full[cols['largo']]!r} no "
                                            f"interpretable; excluida (EXM-2)"))
            report.warn("VALQUI-DER", linea, "I",
                        f"[DEC-5] {nombre!r}: largo no interpretable; excluida")
            continue
        unitario = _q(valor / cantidad)
        listado = parse_money(full[cols["unitario"]])
        if listado is not None and abs(unitario - listado) > Decimal("0.01"):
            report.warn("VALQUI-DER", linea, "L",
                        f"[DEC-2] {nombre!r}: unitario calculado {unitario} vs listado "
                        f"{listado}; el lote manda (Valor/cantidad)")
        clave_fecha = ClaveFecha(clave)
        heredada_dt = fecha_para_fila(None, clave_fecha, ultima_fecha)
        if not isinstance(heredada_dt, datetime):
            decisiones.append(RightDecision(linea, nombre, "omitida",
                                            "[DEC-5] fuente unica pero sin fecha "
                                            "heredable; omitida (D5)"))
            report.warn("VALQUI-DER", linea, None,
                        f"[DEC-5] {nombre!r}: fuente unica sin fecha heredable; "
                        f"omitida (D5, nunca now())")
            continue
        fecha = heredada_dt
        stocks.append(StockCandidate(
            linea=linea, producto=display, cantidad=str(cantidad),
            unidad=unidad_canonica(unidad_obj), costo_lote=str(valor),
            costo_unitario=str(unitario), fecha=fecha.date().isoformat(),
            fecha_heredada=True, proveedor="(sub-tabla: sin proveedor; FK NULL)",
            fuente="derecha-unica", revision_dueno=clave not in universo))
        decisiones.append(RightDecision(linea, nombre, "unica",
                                        f"{cantidad} {unidad_canonica(unidad_obj)} @ "
                                        f"{unitario} fecha {fecha.date()}"))
        report.warn("VALQUI-DER", linea, None,
                    f"[DEC-5] {nombre!r}: fuente unica sin proveedor (FK NULL); "
                    f"el dueno confirma")
    return stocks, decisiones, suma_valor


def _sha(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "missing"


def _tabla(titulo: str, filas: Sequence[Sequence[str]]) -> list[str]:
    lineas = [titulo]
    if not filas:
        return lineas + ["  (sin filas)"]
    celdas = [[str(c) for c in fila] for fila in filas]
    anchos = [max(len(r[i]) for r in celdas) for i in range(len(celdas[0]))]
    for fila in celdas:
        lineas.append("  " + " | ".join(c.ljust(anchos[i]) for i, c in enumerate(fila)))
    return lineas


def ejecutar(*, modo: str = "dry-run", csv_path: Path | None = None,
             reports_dir: Path | str | None = None) -> int:
    root = Path(__file__).resolve().parents[2]
    csv_path = csv_path or root / "ARPIA - INVERSION VALQUI (1).csv"
    report = Report(fase="PREPROCESS-INVERSION-VALQUI", modo=modo)
    proveedores = SupplierMap()

    filas, cols_der = _leer_csv(csv_path, report)
    universo, origen_universo = _cargar_universo(report)
    ultima_fecha: dict = {}  # D5 cache shared: left pass seeds, right pass inherits.
    report.info("CSV", None, None,
                f"fuente {csv_path.name} sha {_sha(csv_path)[:12]} | "
                f"universo BOM: {origen_universo} ({len(universo)} claves) | "
                f"{len(filas)} lineas leidas")

    stocks_izq, movimientos, stats = plan_izquierda(
        filas, universo, report, proveedores, ultima_fecha)
    stocks_der, decisiones_der, suma_der = plan_derecha(
        filas, cols_der, universo, report, ultima_fecha)
    stocks = stocks_izq + stocks_der

    # Checksum L137: suma de lotes izquierdos parseados vs total declarado.
    esperado = EXPECTED_TOTAL
    hallado: Decimal | None = None
    for fila_total in filas:
        celdas = list(fila_total) + ["", ""]
        if len(celdas) > 1 and clave_normalizada(celdas[1]) == "total":
            hallado = parse_money(celdas[3])
            break
    if hallado is not None and hallado != esperado:
        report.warn("CSV", None, "D",
                    f"[DEC-7] total declarado {hallado} difiere del esperado {esperado}")
    if stats["lote_suma"] != esperado:
        report.warn("CSV", None, "D",
                    f"[DEC-7] checksum: suma de lotes parseados {stats['lote_suma']} vs "
                    f"L137 {esperado}; diferencia {stats['lote_suma'] - esperado} "
                    f"(revise omitidas/duplicadas)")
    else:
        report.info("CSV", None, "D", f"checksum OK: {stats['lote_suma']} == L137")

    # DEC-6: Gerrajes vs Herrajes deben seguir distintos.
    if "Gerrajes" in proveedores.canonicos and "Herrajes" in proveedores.canonicos:
        report.warn("PROVEEDORES", None, None,
                    "[DEC-6] 'Gerrajes' y 'Herrajes' son negocios distintos "
                    "(no fusionar): Gerrajes Cl 15 #7-46 vs Herrajes tote-hardware 2026")
    for display, info in sorted(proveedores.canonicos.items()):
        if len(info["variantes"]) > 1:
            report.warn("PROVEEDORES", None, None,
                        f"[DEC-6] {display}: variantes fusionadas "
                        f"{sorted(info['variantes'])}; el dueno confirma")

    # ---- stdout tables (Spanish, owner-facing) ----
    print(f"=== Preproceso INVERSION VALQUI [{modo}] ({csv_path.name}) ===")
    for linea in _tabla("STOCKABLES (Insumos + Compras_Insumos WAC):",
                        [["L", "Producto", "Cant", "U", "Unitario", "Fecha", "Proveedor"]
                         ] + [[f"L{s.linea}", s.producto[:38], s.cantidad,
                                s.unidad, s.costo_unitario, s.fecha,
                                s.proveedor[:22]] for s in stocks]):
        print(linea)
    for linea in _tabla("MOVIMIENTOS (Movimientos_Financieros):",
                        [["L", "Descripcion", "Monto", "Tipo", "Fecha"]
                         ] + [[f"L{m.linea}", m.descripcion[:38], m.monto, m.tipo,
                                m.fecha] for m in movimientos]):
        print(linea)
    for linea in _tabla("SUB-TABLA DERECHA (unicas vs descartadas):",
                        [["L", "Producto", "Decision", "Detalle"]
                         ] + [[f"L{d.linea}", d.producto[:30], d.decision, d.detalle[:60]]
                              for d in decisiones_der]):
        print(linea)
    print("WARN POR DECISION (las 7 decisiones del dueno):")
    grupos: dict[str, list] = {}
    for entrada in report.entradas:
        if entrada.nivel != "WARN":
            continue
        tag = _DEC_TAG_RE.match(entrada.mensaje)
        grupos.setdefault(tag.group(1) if tag else "SIN-TAG", []).append(entrada)
    for codigo, titulo in DECISIONES:
        items = grupos.get(codigo, [])
        print(f"  {codigo} {titulo}: {len(items)}")
        for entrada in items[:25]:
            loc = f"L{entrada.fila}" if entrada.fila else "--"
            print(f"    [{loc}] {entrada.mensaje}")
    print("MAPA PROVEEDORES (dedup):")
    for display, info in sorted(proveedores.canonicos.items(),
                                key=lambda kv: kv[0].casefold()):
        print(f"  {display} x{info['conteo']}: {sorted(info['variantes'])}")
    print(f"CHECKSUM lotes={stats['lote_suma']} vs L137={esperado} | "
          f"valor-derecha={suma_der} (no suma al checksum) | "
          f"omitidas={stats['omitidas']} duplicadas={stats['duplicadas']} "
          f"post-corte={stats['post_corte']}")

    if modo == "apply":
        print("APPLY: plan validado por el dueno (--yes). Sin sesion DB cableada: "
              "0 escrituras; el JSON es el entregable para la carga F2/F6.")

    audit = {"generated": datetime.now().isoformat(timespec="seconds"), "mode": modo,
             "source": {"csv": str(csv_path), "sha": _sha(csv_path),
                        "universo_origen": origen_universo},
             "decisiones": [{"codigo": c, "titulo": t} for c, t in DECISIONES],
             "stockables": [asdict(s) for s in stocks],
             "movimientos": [asdict(m) for m in movimientos],
             "derecha": [asdict(d) for d in decisiones_der],
             "proveedores": {k: {"variantes": sorted(v["variantes"]),
                                 "lineas": v["lineas"], "conteo": v["conteo"]}
                             for k, v in proveedores.canonicos.items()},
             "checksum": {"lotes_izquierda": str(stats["lote_suma"]),
                          "valor_derecha": str(suma_der),
                          "l137": str(esperado)},
             "notas_direccion": "col Direccion sin columna DB: descartada (ver lineas en JSON)",
             "direcciones_vistas": sorted({(list(f) + [""] * 8)[6].strip()
                                           for f in filas
                                           if len(f) > 6 and (list(f) + [""])[6].strip()}),
             "snapshot": [], "changes": [],
             "warnings": [{"hoja": e.hoja, "fila": e.fila, "celda": e.celda,
                           "nivel": e.nivel, "mensaje": e.mensaje}
                          for e in report.entradas],
             "summary": {"stockables": len(stocks),
                         "movimientos": len(movimientos),
                         "derecha_unicas": sum(1 for d in decisiones_der
                                               if d.decision == "unica"),
                         "derecha_descartadas": sum(1 for d in decisiones_der
                                                   if d.decision != "unica"),
                         "warnings": report.count("WARN"),
                         "errors": report.count(LEVEL_ERROR)}}
    target = Path(reports_dir) if reports_dir else Path(__file__).resolve().parent / "reports"
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"preprocess_inversion_valqui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    for linea in report.resumen_lineas():
        print(linea)
    print(f"Audit: {path} [{modo}]")
    return 1 if report.count(LEVEL_ERROR) else 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preproceso standalone INVERSION VALQUI")
    parser.add_argument("--dry-run", action="store_const", const="dry-run", dest="modo")
    parser.add_argument("--apply", action="store_const", const="apply", dest="modo")
    parser.add_argument("--yes", action="store_true",
                        help="Explicit owner confirmation (required with --apply).")
    parser.add_argument("--csv", dest="csv_path", type=Path, default=None)
    parser.add_argument("--reports-dir", type=Path, default=None)
    parser.add_argument("--cwd", type=Path, default=None)
    parser.set_defaults(modo="dry-run")
    return parser


def main() -> None:
    args = _parser().parse_args()
    if args.cwd:
        import os
        os.chdir(args.cwd)
    if args.modo == "apply" and not args.yes:
        raise SystemExit("--apply exige --yes explicito del dueno (sin escrituras DB).")
    raise SystemExit(ejecutar(modo=args.modo, csv_path=args.csv_path,
                              reports_dir=args.reports_dir))


if __name__ == "__main__":
    main()
