"""Ajuste manual de stock inicial (fix2) — capa de datos separada del pipeline.

Decision del usuario (vinculante): STOCK INICIAL MANUAL. El pipeline F0..F7
NO se modifica para interpretar cadenas/cremalleras/tapavarilla/satines (eso
roza EXM-2 'never infer' y la clasificacion por nombre). En su lugar, este
modulo es un script de ajuste de negocio que se ejecuta DESPUES de la recarga
completa (F1..F4) y ANTES de F5, fijando stock_actual para los 10 insumos
residuales que el F5 real rechazaria con 409 (stock insuficiente).

Que hace
--------
1. ``CONSUMOS_BOM``: mapa nombre (display exacto del catalogo) -> consumo BOM
   exacto de las 13 ventas historicas. Valores verificados con la explosion
   real (``explosion_materiales`` sobre ARPIA.xlsx, 2026-08-09); coinciden con
   el hallazgo residual del apply-progress #425 (318 / 288 / 240 / 379 / 2.802
   / 3 / 0.0396 / 0.045 / 0.325 / 30).
2. Margen de negocio documentado: ``stock_final = consumo + margen`` con
   ``margen = max(1, ceil(consumo * 10%))`` — nunca por debajo de +1 unidad,
   cuantizado a la escala NUMERIC(15,4) del modelo (0.0001).
3. Idempotencia por DOBLE mecanismo (documentado):
   a. Verificacion por delta: ``stock_ajuste = max(0, objetivo - stock_actual)``.
      Re-ejecutar con el stock ya en el objetivo devuelve 0 -> no suma nada.
   b. Marca de ajuste: registro JSON en ``reports/adjust_stock_registry.json``
      (gitignored) con clave = nombre del insumo y valor = {fecha, consumo,
      margen, stock_anterior, stock_ajuste, stock_final}. Un insumo ya
      registrado se omite (``--force`` lo re-aplica tras una recarga limpia).
4. dry-run (default): lee la DB y reporta que haria por insumo (insumo, stock
   anterior, ajuste, stock final, consumo cubierto); 0 escrituras y NO crea el
   registro (NFR-2). commit: aplica los deltas y escribe el registro.
5. Insumo inexistente: WARN claro en dry-run (exit 0, no bloquea); ERROR en
   commit con ROLLBACK ATOMICO (si falta 1, no se aplica ninguno, exit 1).

Uso (desde backend/):
    python -m migrate.adjust_stock --dry-run          # reporta que haria
    python -m migrate.adjust_stock --commit           # aplica + registra
    python -m migrate.adjust_stock --commit --force   # re-aplica tras recarga
    python -m migrate.adjust_stock --fase-final 4     # hook documentado (F4)

Integracion en la recarga (orden documentado):
    migracion completa (F1..F4) -> adjust_stock --commit -> F5..F7
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Insumo
from migrate.catalog import clave_normalizada, normalizar_nombre
from migrate.report import LEVEL_ERROR, Report

# Escala NUMERIC(15,4) real del modelo (mismo redondeo que PostgreSQL).
_ESCALA = Decimal("0.0001")

# Registro de ajustes (gitignored via backend/migrate/reports/).
REGISTRO_DEFAULT = Path(__file__).resolve().parent / "reports" / "adjust_stock_registry.json"

# Consumo BOM exacto de las 13 ventas historicas (verificado 2026-08-09 contra
# explosion_materiales real; coincide con el hallazgo residual de #425).
CONSUMOS_BOM: dict[str, Decimal] = {
    "Cadena gris delgada totebag": Decimal("318"),
    "Cadena plateada gruesa totebag": Decimal("288"),
    "Cremallera num 3": Decimal("240"),
    "Tapavarilla negro 10 mts": Decimal("379"),
    "Sublimacion para las totebag": Decimal("2.802"),
    "Super Brioni": Decimal("3"),
    "Satin elastico negro": Decimal("0.0396"),
    "Satin elastico rosa": Decimal("0.045"),
    "Sesgo elastico negro 2cm brillante": Decimal("0.325"),
    "Sesgo rigido para ojales corset": Decimal("30"),
}


# --------------------------------------------------------------------------- #
# Pure: margen + objetivo + delta (regla de negocio documentada)
# --------------------------------------------------------------------------- #


def margen_seguridad(consumo: Decimal) -> Decimal:
    """Margen de negocio: max(1, ceil(consumo * 10%)) en la unidad canonica.

    10% redondeado hacia ARRIBA (ceil) para nunca quedar por debajo del 10%,
    con minimo 1 unidad (un consumo chico o fraccional siempre recibe >= 1).
    """
    diez_por_ciento = (consumo * Decimal("0.10")).to_integral_value(rounding=ROUND_CEILING)
    return max(Decimal("1"), diez_por_ciento)


def stock_final_objetivo(consumo: Decimal) -> Decimal:
    """Stock final objetivo = consumo BOM + margen, escala NUMERIC(15,4)."""
    return (consumo + margen_seguridad(consumo)).quantize(_ESCALA, rounding=ROUND_HALF_UP)


def stock_ajuste_para(consumo: Decimal, stock_actual: Decimal) -> Decimal:
    """Delta a sumar: max(0, objetivo - stock_actual).

    Nunca resta; con el stock ya en el objetivo devuelve 0 (idempotencia por
    verificacion — re-ejecutar no suma doble).
    """
    delta = stock_final_objetivo(consumo) - stock_actual
    return max(Decimal("0"), delta).quantize(_ESCALA, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------- #
# Registro JSON (marca de ajuste documentada, gitignored)
# --------------------------------------------------------------------------- #


def _cargar_registro(ruta: Path) -> dict:
    """Lee el registro de ajustes ya aplicados ({nombre: {fecha, ...}})."""
    if not ruta.exists():
        return {}
    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
        return data.get("ajustes", {}) if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}  # registro corrupto/ausente -> se ignora (la verificacion por
        # delta sigue protegiendo: no se suma doble)


def _guardar_registro(ruta: Path, ajustes: dict, fase_final: int) -> None:
    """Persiste el registro con la marca de ajuste (fecha + valores)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "generado": datetime.now().isoformat(timespec="seconds"),
        "fase_final": fase_final,
        "ajustes": ajustes,
    }
    ruta.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- #
# DB helpers
# --------------------------------------------------------------------------- #


def _insumo_por_nombre(db, nombre: str) -> Insumo | None:
    """Insumo del catalogo: display exacto primero, luego clave normalizada."""
    limpio = normalizar_nombre(nombre)
    ins = db.scalar(select(Insumo).where(Insumo.nombre == limpio))
    if ins is not None:
        return ins
    clave = clave_normalizada(nombre)
    for ins in db.scalars(select(Insumo)).all():
        if clave_normalizada(ins.nombre) == clave:
            return ins
    return None


def _entrada_registro(
    nombre: str, consumo: Decimal, anterior: Decimal, ajuste: Decimal, final: Decimal
) -> dict:
    """Marca de ajuste: fecha + consumos/margen + valores de stock."""
    return {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "consumo": str(consumo),
        "margen": str(margen_seguridad(consumo)),
        "stock_anterior": str(anterior),
        "stock_ajuste": str(ajuste),
        "stock_final": str(final),
    }


# --------------------------------------------------------------------------- #
# Core: resolver + aplicar (dry-run: simula; commit: muta + registra)
# --------------------------------------------------------------------------- #


def aplicar_ajustes(
    db,
    consumos: dict[str, Decimal],
    report: Report,
    modo: str,
    fuerza: bool = False,
    registro: dict | None = None,
) -> dict[str, int]:
    """Resuelve cada insumo del mapa y aplica (o simula) el delta.

    - Faltante: WARN en dry-run; en commit se reporta ERROR y NADA se aplica
      (rollback atomico — el caller no commitea).
    - Registro: un insumo ya marcado se omite salvo ``fuerza``.
    - Delta <= 0: sin ajuste (el stock ya cubre el objetivo).
    - Delta > 0: en commit suma a stock_actual; en dry-run solo reporta.
    Devuelve resumen {ajustados, ya_en_registro, sin_delta, omitidos}.
    """
    res = {"ajustados": 0, "ya_en_registro": 0, "sin_delta": 0, "omitidos": 0}
    registro = {} if registro is None else registro

    # 1) Pre-check atomico: resolver TODOS antes de mutar nada.
    faltantes: list[str] = []
    for nombre in consumos:
        if _insumo_por_nombre(db, nombre) is None:
            faltantes.append(nombre)
    for nombre in faltantes:
        res["omitidos"] += 1
        mensaje = (
            f"{nombre}: insumo inexistente en el catalogo; ajuste NO aplicado (correr F1 antes)"
        )
        if modo == "commit":
            report.error("AJUSTE", None, None, mensaje)
        else:
            report.warn("AJUSTE", None, None, mensaje)
    if faltantes and modo == "commit":
        return res  # rollback atomico: el caller no commitea nada

    # 2) Aplicar (o simular) por insumo.
    for nombre, consumo in consumos.items():
        if nombre in registro and not fuerza:
            res["ya_en_registro"] += 1
            report.info(
                "AJUSTE",
                None,
                None,
                f"{nombre}: ya ajustado en {registro[nombre].get('fecha')}; "
                f"omitido (--force para re-aplicar tras recarga)",
            )
            continue
        insumo = _insumo_por_nombre(db, nombre)
        if insumo is None:
            continue  # ya reportado en el pre-check
        anterior = insumo.stock_actual
        delta = stock_ajuste_para(consumo, anterior)
        objetivo = stock_final_objetivo(consumo)
        if delta <= 0:
            res["sin_delta"] += 1
            report.info(
                "AJUSTE",
                None,
                None,
                f"{nombre}: stock {anterior} ya cubre objetivo {objetivo}; sin ajuste",
            )
            registro[nombre] = _entrada_registro(nombre, consumo, anterior, Decimal("0"), anterior)
            continue
        final = (anterior + delta).quantize(_ESCALA, rounding=ROUND_HALF_UP)
        if modo == "commit":
            insumo.stock_actual = final
        res["ajustados"] += 1
        registro[nombre] = _entrada_registro(nombre, consumo, anterior, delta, final)
        report.info(
            "AJUSTE",
            None,
            None,
            f"{nombre}: stock {anterior} + {delta} -> {final} "
            f"(consumo {consumo} cubierto, objetivo {objetivo})",
        )
    return res


def _emitir_entradas(report: Report) -> None:
    """Imprime las entradas del reporte en stdout (NFR-2, ASCII plano)."""
    for entry in report.entradas:
        ubicacion = entry.hoja or ""
        if entry.fila is not None:
            ubicacion = f"{ubicacion}:{entry.fila}"
        prefix = f"[{entry.nivel}]" + (f" [{ubicacion}]" if ubicacion else "")
        print(prefix, entry.mensaje)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="migrate.adjust_stock",
        description=(
            "Ajuste manual de stock inicial (fix2) para los 10 insumos "
            "residuales de F5. Correr tras F1..F4 y antes de F5. "
            "dry-run por defecto: 0 escrituras."
        ),
    )
    parser.add_argument(
        "--modo",
        choices=["dry-run", "commit"],
        default="dry-run",
        help="dry-run (default): reporta que haria. commit: aplica + registra.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_const",
        const="dry-run",
        dest="modo",
        help="Modo dry-run (default): reporte sin escrituras.",
    )
    parser.add_argument(
        "--commit",
        action="store_const",
        const="commit",
        dest="modo",
        help="Aplicar los ajustes y escribir el registro.",
    )
    parser.add_argument(
        "--fase-final",
        type=int,
        default=4,
        help="Fase tras la que corre el ajuste (hook documentado; default 4 = F4).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-aplicar aunque el insumo ya este registrado (tras recarga limpia).",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="Ruta del registro JSON (default: migrate/reports/adjust_stock_registry.json).",
    )
    parser.add_argument(
        "--cwd",
        type=Path,
        default=None,
        help="Cambiar de directorio antes de ejecutar (conveniencia CLI).",
    )
    return parser


def ejecutar(
    modo: str = "dry-run",
    consumos: dict[str, Decimal] | None = None,
    registry_path: Path | str | None = None,
    fase_final: int = 4,
    fuerza: bool = False,
) -> int:
    """Ejecuta el ajuste. Exit 0 sin ERRORes; 1 si commit falla (faltante)."""
    consumos = CONSUMOS_BOM if consumos is None else consumos
    ruta_registro = Path(registry_path) if registry_path else REGISTRO_DEFAULT
    report = Report(fase="AJUSTE-STOCK", modo=modo)

    db = SessionLocal()
    try:
        registro = {} if fuerza else _cargar_registro(ruta_registro)
        aplicar_ajustes(db, consumos, report, modo, fuerza=fuerza, registro=registro)
        # Commit + registro SOLO si no hubo ERRORes (rollback atomico en commit:
        # un insumo faltante deja la DB intacta y no marca el registro).
        if modo == "commit" and not report.tiene_errores:
            db.commit()
            _guardar_registro(ruta_registro, registro, fase_final)
        else:
            db.rollback()
    finally:
        db.close()

    _emitir_entradas(report)
    errores = report.count(LEVEL_ERROR)
    print(
        f"Resumen: {len(report.entradas)} entradas, {errores} errores "
        f"[{modo}] (fase-final F{fase_final})"
    )
    return 1 if errores else 0


def main() -> None:
    args = construir_parser().parse_args()
    if args.cwd is not None:
        os.chdir(args.cwd)
    sys.exit(
        ejecutar(
            modo=args.modo,
            registry_path=args.registry,
            fase_final=args.fase_final,
            fuerza=args.force,
        )
    )


__all__ = [
    "CONSUMOS_BOM",
    "REGISTRO_DEFAULT",
    "margen_seguridad",
    "stock_final_objetivo",
    "stock_ajuste_para",
    "aplicar_ajustes",
    "ejecutar",
    "construir_parser",
    "main",
]


if __name__ == "__main__":
    main()
