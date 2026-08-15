"""Normalization of raw Excel values into canonical, DB-ready data.

Covers (EXM-2):
- decimal comma -> dot (Colombian locale "9,5" -> Decimal("9.5"));
- quantity+unit regex ("9,5 mts" -> Decimal 9.5 + unit mts);
- canonical unit conversion by category (Telas -> m, Herrajes -> un o cm2,
  Empaques -> un, peso kg/g keep);
- area expressions ("50 x 280 cm" -> 1.4 m2);
- width-from-name regex ("(\\d+)\\s*cm") with a 100cm default + WARN;
- uninterpretable values (#DIV/0!, ...) stop the row and are reported, never
  inferred (EXM-2 error scenario).

Date policy (design D5): empty dates are inherited from the contiguous previous
row with the same insumo; a row without a previous match is left None so the
phase can decide (omit + WARN). never now().
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from migrate.report import Report

# --- Decimal normalization -------------------------------------------------

_DECIMAL_COMMA_RE = re.compile(r"^\s*([+-]?)(\d{1,3}(?:\.\d{3})*)([.,])(\d+)\s*$")


def normalizar_decimal(valor: object) -> Decimal | None:
    """Convert a raw Excel cell to Decimal (no rounding). None if uninterpretable.

    Handles "9,5" (comma decimal) and "1.234,56" (Colombian thousands).
    """
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, (int, float)):
        try:
            return Decimal(str(valor))
        except InvalidOperation:
            return None
    texto = str(valor).strip()
    if not texto:
        return None
    # Excel error strings like #DIV/0! are not numbers -> not inferred (EXM-2).
    if texto.startswith("#"):
        return None
    # "1.234,56" -> 1234.56 ; "9,5" -> 9.5
    m = _DECIMAL_COMMA_RE.match(texto)
    if m:
        signo, miles, sep, dec = m.group(1), m.group(2), m.group(3), m.group(4)
        miles_normal = miles.replace(".", "")
        if sep == "." and len(dec) == 3:  # thousands separator, not decimal
            texto_num = f"{signo}{miles_normal}{dec}"
        else:
            texto_num = f"{signo}{miles_normal}.{dec}"
    else:
        texto_num = texto.replace(",", ".").replace(" ", "")
    try:
        return Decimal(texto_num)
    except (InvalidOperation, ValueError):
        return None


# --- Quantity+unit -----------------------------------------------------------

# canonical unit -> (family, display label). Family length ("mza") converts to m
# for Telas; "un", "cm2", "peso" stay as-is.
_UNIDADES_REGISTRO: dict[str, tuple[str, str]] = {
    "m": ("long", "m"),
    "cm": ("long", "cm"),
    "un": ("un", "un"),
    "cm2": ("cm2", "cm2"),
    "kg": ("peso", "kg"),
    "g": ("peso", "g"),
}

_SINONIMOS: dict[str, str] = {
    "mt": "m",
    "mts": "m",
    "metros": "m",
    "metro": "m",
    "metr": "m",
    "cms": "cm",
    "centimetro": "cm",
    "centimetros": "cm",
    "unidades": "un",
    "unid": "un",
    "und": "un",
    "unidad": "un",
    "gms": "g",
    "gramos": "g",
}

_CANT_UNIDAD_RE = re.compile(r"^\s*([+-]?\d+(?:[.,]\d+)?)\s*([A-Za-zº²]+)\s*$")

_FACTOR_M_CM: dict[str, Decimal] = {"m": Decimal("1"), "cm": Decimal("0.01")}


@dataclass(frozen=True)
class CantidadUnidad:
    cantidad: Decimal
    unidad: str  # raw unit token as it appeared


def parsear_cantidad_unidad(celda: object) -> CantidadUnidad | None:
    """Parse '9,5 mts' -> CantidadUnidad(cantidad=Decimal('9.5'), unidad='mts')."""
    if celda is None:
        return None
    if isinstance(celda, (int, float, Decimal)):
        cant = normalizar_decimal(celda)
        return CantidadUnidad(cantidad=cant, unidad="un") if cant is not None else None
    m = _CANT_UNIDAD_RE.match(str(celda).strip())
    if not m:
        return None
    cantidad = normalizar_decimal(m.group(1))
    if cantidad is None:
        return None
    return CantidadUnidad(cantidad=cantidad, unidad=m.group(2).lower())


def unidad_canonica(unidad_raw: str) -> str:
    """Map a raw unit token to its canonical key (m, cm, un, cm2, kg, g)."""
    clave = unidad_raw.strip().lower()
    if clave in _SINONIMOS:
        return _SINONIMOS[clave]
    if clave in _UNIDADES_REGISTRO:
        return clave
    return clave  # unknown stays raw -> caller decides (stop + report)


def convertir_cantidad(
    cant: Decimal, unidad_raw: str, categoria: str
) -> tuple[Decimal, str] | None:
    """Convert (cantidad, unidad) to the canonical unit for the category.

    Returns (cantidad_canonica, unidad_canonica) or None when uninterpretable
    for that category (caller reports and stops the row).
    """
    u = unidad_canonica(unidad_raw)
    if u not in _UNIDADES_REGISTRO:
        return None
    familia, etiqueta = _UNIDADES_REGISTRO[u]
    if familia == "long":
        # Length quantities convert to canonical meters (design D4: Telas -> m);
        # 100 cm = 1 m, so the label is "m" when cm was the raw unit.
        factor = _FACTOR_M_CM[u]
        return (cant * factor, "m")
    return (cant, etiqueta)


# --- Area expressions ---------------------------------------------------------

_AREA_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)\s*(?:cms?)?\s*$")


def normalizar_area_m2(celda: object) -> Decimal | None:
    """Parse '50 x 280 cm' -> area in m2 (50*280/10000 = 1.4). None si no aplica."""
    texto = str(celda).strip() if celda is not None else ""
    m = _AREA_RE.match(texto)
    if not m:
        return None
    a = normalizar_decimal(m.group(1))
    b = normalizar_decimal(m.group(2))
    if a is None or b is None:
        return None
    return a * b / Decimal("10000")


# --- Width from insumo name ----------------------------------------------------

_ANCHO_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*cm", re.IGNORECASE)
ANCHO_DEFAULT = Decimal("100")


def ancho_desde_nombre(
    nombre: str,
    report: Report | None = None,
    hoja: str = "",
    fila: int | None = None,
) -> Decimal:
    """Extract width in cm from the insumo name; default 100cm + WARN (design D4)."""
    m = _ANCHO_RE.search(str(nombre))
    if m:
        ancho = normalizar_decimal(m.group(1))
        if ancho is not None:
            return ancho
    if report is not None:
        report.warn(
            hoja, fila, None, f"ancho no informado en {nombre!r} -> default {ANCHO_DEFAULT}cm"
        )
    return ANCHO_DEFAULT


# --- Dates: contiguous inheritance policy (D5 — never now()) -------------------


@dataclass(frozen=True)
class ClaveFecha:
    insumo: object


def fecha_para_fila(
    fecha_actual: object | None,
    clave: ClaveFecha,
    ultima_por_clave: dict[ClaveFecha, object],
) -> object | None:
    """Effective date for a row under policy D5.

    Own date wins (and seeds the cache). Empty inherits from the contiguous
    previous row with the SAME insumo. No match -> None (caller omits + WARN).
    Never now().
    """
    if fecha_actual is not None:
        ultima_por_clave[clave] = fecha_actual
        return fecha_actual
    return ultima_por_clave.get(clave)


def es_aware(dt: object) -> bool:
    """True if dt is a timezone-aware datetime (TIMESTAMPTZ storage)."""
    if isinstance(dt, datetime):
        return dt.tzinfo is not None and dt.utcoffset() is not None
    return False


def coerce_aware(dt: object, tz=None) -> object:
    """Make an Excel naive datetime timezone-aware (server tz) so no ambiguity
    is persisted (spec 'compras-insumos' borde scenario)."""
    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=tz or UTC)
    return dt
