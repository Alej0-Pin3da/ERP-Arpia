"""F8 backfill: hydrate zero-valued money fields + supplier master (standalone).

csv/ARPIA - VENTAS.csv is the canonical price source; CAJAS triplets + VENTAS
G/H corroborate only; DESCUENTOS is validation-only; Set Celeno stays 75000
(MIG-2). Costs come from recipe-sheet E + CAJAS costo via direct column write
+ provenance flag (Compras_Insumos never seeded). Suppliers are insert-only
INVERSION Provedor names. EXM-2/D5: #/discount/dateless cells -> WARN+skip,
never inferred, never now(). --dry-run (default) writes nothing; exit 1 on ERROR.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from migrate.catalog import clave_normalizada, normalizar_nombre
from migrate.loaders import HojaInexistenteError, LibroMigracion
from migrate.normalize import normalizar_decimal
from migrate.report import LEVEL_ERROR, Report
ESCALA = Decimal("0.0001")
ORIGEN_BACKFILL = "backfill"
CELENO_PRECIO = Decimal("75000")
RECIPE_SHEETS = ("SET AELO", "SET OCIPETE", "Corset Garras", "CORSET ARTEMISIA",
                 "FALDA EMILY", "Corset Hypatia", "BLUSAS", "TOTEBAG")
INVERSION_SHEETS = ("INVERSION VALQUI", "INVERSION MARGARA")
# csv Producto -> catalog Producto (seven known; anything else warns + skips).
PRICE_ALIASES = {"CAJA SACA LAS GARRAS": "Caja Saca Las Garras", "SET AELO": "Set Aelo",
                 "SET OCIPETE": "Set Ocipete", "BLUSA ARPIA MANGA LARGA": "Blusa Manga Larga",
                 "TOTEBAG": "Tote Bag Arpia", "CORSET GARRAS": "Corset Garras",
                 "FALDA EMILY": "Falda Emily"}
CAJAS_JUNK = {"TOTAL", "VENTA", "GANANCIA"}
PLACEHOLDERS = frozenset({"", "-", "--", "n/a", "na", "s/n", "nn", "ninguno",
                          "no aplica", "...", "???", "provedor", "proveedor"})
def parse_money(valor: object) -> Decimal | None:
    """Colombian money text ($295.000 / $1.633.750,00) -> Decimal. None if junk."""
    if isinstance(valor, (int, float, Decimal)):
        try:
            return Decimal(str(valor))
        except InvalidOperation:
            return None
    texto = re.sub(r"[^\d.,-]", "", str(valor or "").strip())
    if not texto or texto.startswith("#"):
        return None
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+", texto):
        texto = texto.replace(".", "")
    try:
        return Decimal(texto)
    except InvalidOperation:
        return None
def _q(v: Decimal) -> Decimal:
    return v.quantize(ESCALA, rounding=ROUND_HALF_UP)
@dataclass(frozen=True)
class PriceUpdate:
    nombre: str
    precio: Decimal
    fuente: str
@dataclass(frozen=True)
class CostUpdate:
    clave: str
    nombre: str
    costo: Decimal
    fuente: str
@dataclass
class SupplierPlan:
    nombres: list[str] = field(default_factory=list)
def _alias(nombre: str, universo: dict[str, str]) -> str | None:
    clave = clave_normalizada(nombre)
    return next((v for k, v in universo.items() if clave_normalizada(k) == clave), None)
def plan_precios(csv_rows: list[dict], corroborar: dict[str, list[tuple[str, Decimal]]],
                 report: Report | None = None) -> list[PriceUpdate]:
    """Pure planner: canonical csv price per aliased product. Never writes."""
    candidatas: dict[str, list[Decimal]] = {}
    for i, row in enumerate(csv_rows, start=2):
        crudo = normalizar_nombre(row.get("Producto") or "")
        if not crudo:
            continue  # empty/total rows are not data
        alias = _alias(crudo, PRICE_ALIASES)
        if alias is None:
            if report:
                report.warn("CSV-VENTAS", i, "A", f"{crudo!r}: no catalog alias; skipped")
            continue
        if str(row.get("Precio Venta") or "").strip().startswith("#") \
                or parse_money(row.get("Precio Venta")) is None:
            if report:
                report.warn("CSV-VENTAS", i, "G",
                            f"{crudo!r}: uninterpretable price; skipped (EXM-2)")
            continue
        if "desc" in normalizar_nombre(row.get("Columna 2") or "").casefold():
            if report:
                report.warn("CSV-VENTAS", i, "G",
                            f"{crudo!r}: discount-marked price; skipped, never list price")
            continue
        if not str(row.get("Fecha") or "").strip():
            if report:
                report.warn("CSV-VENTAS", i, "M", f"{crudo!r}: dateless row; skipped (D5)")
            continue
        candidatas.setdefault(alias, []).append(_q(parse_money(row.get("Precio Venta"))))  # type: ignore[arg-type]
    planes: list[PriceUpdate] = []
    for nombre, vals in candidatas.items():
        if clave_normalizada(nombre) == "set celeno":
            continue  # MIG-2 lock: Celeno never hydrated
        moda = max(set(vals), key=vals.count)
        if len(set(vals)) > 1 and report:
            report.warn("CSV-VENTAS", None, None,
                        f"{nombre!r}: intra-csv divergence "
                        f"{sorted({str(v) for v in vals})}; canonical {moda}")
        for fuente, ref in corroborar.get(nombre, []):
            if ref != moda and report:
                report.warn("CORROBORAR", None, None,
                            f"{nombre!r}: csv {moda} vs {fuente} {ref}; csv wins")
        planes.append(PriceUpdate(nombre=nombre, precio=moda, fuente="csv/ARPIA - VENTAS.csv"))
    return sorted(planes, key=lambda p: p.nombre)
def plan_costos(recetas: list[tuple[str, int, str, object]],
                cajas: list[tuple[str, Decimal, str]],
                report: Report | None = None) -> list[CostUpdate]:
    """Pure planner: unit cost per normalized material name. First wins."""
    costos: dict[str, CostUpdate] = {}
    for hoja, fila, nombre, e_val in recetas:
        clave = clave_normalizada(nombre)
        if not clave:
            continue
        costo = normalizar_decimal(e_val)
        if costo is None or costo <= 0:
            if report:
                report.warn(hoja, fila, "E",
                            f"{normalizar_nombre(nombre)!r}: uninterpretable cost; skipped (EXM-2)")
            continue
        if clave in costos:
            if costos[clave].costo != _q(costo) and report:
                report.warn(hoja, fila, "E",
                            f"{normalizar_nombre(nombre)!r}: divergent cost; first wins")
            continue
        costos[clave] = CostUpdate(clave=clave, nombre=normalizar_nombre(nombre),
                                   costo=_q(costo), fuente=f"{hoja}!E{fila}")
    for nombre, costo, fuente in cajas:
        clave = clave_normalizada(nombre)
        if clave and clave not in costos and costo > 0:
            costos[clave] = CostUpdate(clave=clave, nombre=normalizar_nombre(nombre),
                                       costo=_q(costo), fuente=fuente)
    return sorted(costos.values(), key=lambda c: c.nombre.casefold())
def plan_proveedores(filas: list[tuple[str, int, object]],
                     report: Report | None = None) -> SupplierPlan:
    """Pure planner: distinct normalized supplier names, insert-only."""
    plan, vistos = SupplierPlan(), set()
    for hoja, fila, crudo in filas:
        nombre = normalizar_nombre(crudo)
        if nombre.casefold() in PLACEHOLDERS:
            if str(crudo or "").strip() and report:
                report.warn(hoja, fila, None,
                            f"supplier {str(crudo).strip()!r}: blank/placeholder; skipped")
            continue
        if (clave := clave_normalizada(nombre)) in vistos:
            continue
        vistos.add(clave)
        plan.nombres.append(nombre)
    return plan
def _aplicar_money(db, cached: dict, planes: list, *, entidad: str, campo: str,
                   origen_campo: str, modo: str, report: Report) -> dict:
    """Shared hydrate: zeros + own backfills only; Celeno lock; idempotent."""
    cambios, snap, hechos = [], [], 0
    for plan in planes:
        clave = plan.nombre if entidad == "Productos" else plan.clave
        valor = plan.precio if entidad == "Productos" else plan.costo
        obj = cached.get(clave)
        if obj is None:
            report.warn(entidad, None, None, f"{plan.nombre!r}: no match; skipped")
            continue
        if entidad == "Productos" and clave_normalizada(obj.nombre) == "set celeno":
            report.warn(entidad, obj.id, None, "Set Celeno locked at 75000; skipped")
            continue
        snap += [{"entity": obj.__tablename__, "id": obj.id, "field": campo,
                  "before": str(getattr(obj, campo))}]
        if getattr(obj, campo) == valor and getattr(obj, origen_campo) == ORIGEN_BACKFILL:
            continue  # idempotent re-run: zero diff
        if getattr(obj, campo) != 0 and getattr(obj, origen_campo) != ORIGEN_BACKFILL:
            report.warn(entidad, obj.id, None,
                        f"{obj.nombre!r}: non-zero pipeline value preserved")
            continue
        if modo == "apply":
            setattr(obj, campo, valor)
            setattr(obj, origen_campo, ORIGEN_BACKFILL)
        cambios.append({"entity": obj.__tablename__, "id": obj.id, "nombre": obj.nombre,
                        "field": campo, "before": snap[-1]["before"],
                        "after": str(valor), "source": plan.fuente})
        hechos += 1
    return {"cambios": cambios, "snapshot": snap, "updated": hechos}
def aplicar_precios(db, planes: list[PriceUpdate], *, modo: str, report: Report) -> dict:
    from app.models import Producto
    cached = {p.nombre: p for p in db.query(Producto).all()}
    return _aplicar_money(db, cached, planes, entidad="Productos",
                          campo="precio_venta_sugerido", origen_campo="origen_precio",
                          modo=modo, report=report)
def aplicar_costos(db, planes: list[CostUpdate], *, modo: str, report: Report) -> dict:
    from app.models import Insumo
    cached = {clave_normalizada(i.nombre): i for i in db.query(Insumo).all()}
    return _aplicar_money(db, cached, planes, entidad="Insumos",
                          campo="costo_promedio_actual", origen_campo="origen_costo",
                          modo=modo, report=report)
def aplicar_proveedores(db, plan: SupplierPlan, *, modo: str, report: Report) -> dict:
    from app.models import ProveedorMaestro
    existentes = {clave_normalizada(p.nombre) for p in db.query(ProveedorMaestro).all()}
    cambios, hechos = [], 0
    for nombre in plan.nombres:
        if (clave := clave_normalizada(nombre)) in existentes:
            continue  # insert-only idempotency
        if modo == "apply":
            db.add(ProveedorMaestro(nombre=nombre, categoria="Insumos",
                                    notas="backfill hidratacion-datos-faltantes"))
            db.flush()
        existentes.add(clave)
        cambios.append({"entity": "maestros_proveedores", "nombre": nombre})
        hechos += 1
    return {"cambios": cambios, "snapshot": [], "updated": hechos}
# Thin loaders (read-only; loaders.py untouched).
def _leer_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))
def _leer_cajas(libro: LibroMigracion, report: Report) -> tuple[dict, list]:
    """CAJAS triplets once: (price corroboration, packaging unit costs)."""
    corroborar: dict[str, list[tuple[str, Decimal]]] = {}
    costos: list[tuple[str, Decimal, str]] = []
    try:
        lec = libro.leer_hoja("CAJAS", report=report)
    except HojaInexistenteError:
        report.warn("CAJAS", None, None, "sheet missing; corroboration skipped")
        return corroborar, costos
    for i, f in enumerate(lec.filas, start=4):
        for kp, kc, kv, tag in (("B", "C", "D", "CAJAS-C1"), ("F", "G", "H", "CAJAS-C2"),
                                ("J", "K", "L", "CAJAS-C3")):
            if not (n := normalizar_nombre(f.get(kp))) or n in CAJAS_JUNK:
                continue
            v, alias = parse_money(f.get(kv)), _alias(n, {a: a for a in PRICE_ALIASES.values()})
            if v is not None and v > 0 and alias:
                corroborar.setdefault(alias, []).append((f"{tag}!{i}", _q(v)))
            c = normalizar_decimal(f.get(kc))
            if c is not None and c > 0:
                costos.append((n, _q(c), f"{tag}!{i}"))
    return corroborar, costos


def _leer_corroborar(libro: LibroMigracion, report: Report) -> dict[str, list[tuple[str, Decimal]]]:
    """VENTAS G/H + DESCUENTOS validation map (CAJAS comes from _leer_cajas)."""
    out: dict[str, list[tuple[str, Decimal]]] = {}
    for hoja, col_n, col_v, ini, tag in (("VENTAS", "A", "G", 2, "VENTAS!G"),
                                         ("DESCUENTOS", "B", "C", 3, "DESCUENTOS!C")):
        try:
            lec = libro.leer_hoja(hoja, report=report)
        except HojaInexistenteError:
            report.warn(hoja, None, None, "sheet missing; corroboration skipped")
            continue
        for i, f in enumerate(lec.filas, start=ini):
            if not normalizar_nombre(f.get(col_n)):
                continue
            v = parse_money(f.get(col_v))
            alias = _alias(str(f.get(col_n)), {a: a for a in PRICE_ALIASES.values()})
            if v is not None and v > 0 and alias:
                extra = " (validation-only)" if hoja == "DESCUENTOS" else ""
                out.setdefault(alias, []).append((f"{tag}{i}{extra}", _q(v)))
    return out
def _leer_recetas(libro: LibroMigracion, report: Report) -> list[tuple[str, int, str, object]]:
    filas: list[tuple[str, int, str, object]] = []
    for hoja in RECIPE_SHEETS:
        try:
            lec = libro.leer_hoja(hoja, report=report)
        except HojaInexistenteError:
            report.warn(hoja, None, None, "sheet missing in this workbook; skipped")
            continue
        for i, f in enumerate(lec.filas, start=3):
            if normalizar_nombre(f.get("A")):
                filas.append((hoja, i, str(f.get("A")), f.get("E")))
    return filas
def _leer_proveedores(libro: LibroMigracion, report: Report) -> list[tuple[str, int, object]]:
    from openpyxl.utils import get_column_letter
    filas: list[tuple[str, int, object]] = []
    sin_proveedor = 0
    for hoja in INVERSION_SHEETS:
        try:
            ws = libro.obtener_worksheet(hoja)
            lec = libro.leer_hoja(hoja, report=report)
        except HojaInexistenteError:
            report.warn(hoja, None, None, "sheet missing in this workbook; skipped")
            continue
        col = next((get_column_letter(i) for i, c in enumerate(list(ws[2]), start=1)
                    if c.value and "provedor" in str(c.value).strip().casefold()), None)
        if col is None:
            report.warn(hoja, 2, None, "Provedor column not found; skipped")
            continue
        for i, f in enumerate(lec.filas, start=3):
            if f.get(col) is None:
                sin_proveedor += 1
            else:
                filas.append((hoja, i, f.get(col)))
    report.info("INVERSION", None, None, f"{sin_proveedor} purchase rows without provider "
                                        "(no master row; history untouched)")
    return filas
def _sha(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return "missing"
def ejecutar(*, modo: str = "dry-run", workbook: Path | None = None,
             csv_path: Path | None = None, reports_dir: Path | str | None = None) -> int:
    from app.db.session import SessionLocal
    root = Path(__file__).resolve().parents[2]
    workbook = workbook or root / "ARPIA.xlsx"
    csv_path = csv_path or root / "csv" / "ARPIA - VENTAS.csv"
    report = Report(fase="BACKFILL-PRECIOS-COSTOS", modo=modo)
    libro = LibroMigracion(workbook)
    libro.abrir()
    try:
        corroborar, cajas_costos = _leer_cajas(libro, report)
        for alias, refs in _leer_corroborar(libro, report).items():
            corroborar.setdefault(alias, []).extend(refs)
        planes_p = plan_precios(_leer_csv(csv_path), corroborar, report)
        planes_c = plan_costos(_leer_recetas(libro, report), cajas_costos, report)
        plan_s = plan_proveedores(_leer_proveedores(libro, report), report)
    finally:
        libro.cerrar()
    audit = {"generated": datetime.now().isoformat(timespec="seconds"), "mode": modo,
             "sources": {"workbook_sha": _sha(workbook), "csv_sha": _sha(csv_path)},
             "snapshot": [], "changes": [], "warnings": [], "summary": {}}
    db = SessionLocal()
    try:
        thunks = (("productos", lambda: aplicar_precios(db, planes_p, modo=modo, report=report)),
                  ("insumos", lambda: aplicar_costos(db, planes_c, modo=modo, report=report)),
                  ("proveedores",
                   lambda: aplicar_proveedores(db, plan_s, modo=modo, report=report)))
        for nombre, thunk in thunks:
            antes = report.count(LEVEL_ERROR)
            res = thunk()
            audit["snapshot"] += res["snapshot"]
            audit["changes"] += res["cambios"]
            audit["summary"][nombre] = res["updated"]
            if modo == "apply" and report.count(LEVEL_ERROR) == antes:
                db.commit()
            else:
                db.rollback()  # dry-run always rolls back; errored entity commits nothing
    finally:
        db.close()
    audit["warnings"] = [{"hoja": e.hoja, "fila": e.fila, "celda": e.celda,
                          "nivel": e.nivel, "mensaje": e.mensaje} for e in report.entradas]
    audit["summary"].update({"warnings": report.count("WARN"),
                             "errors": report.count(LEVEL_ERROR)})
    target = Path(reports_dir) if reports_dir else Path(__file__).resolve().parent / "reports"
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"backfill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")
    for line in report.resumen_lineas():
        print(line)
    print(f"Audit: {path} [{modo}]")
    return 1 if report.count(LEVEL_ERROR) else 0
def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="F8 backfill precios/costos/proveedores")
    parser.add_argument("--dry-run", action="store_const", const="dry-run", dest="modo")
    parser.add_argument("--apply", action="store_const", const="apply", dest="modo")
    parser.add_argument("--workbook", type=Path, default=None)
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
    raise SystemExit(ejecutar(modo=args.modo, workbook=args.workbook,
                              csv_path=args.csv_path, reports_dir=args.reports_dir))
if __name__ == "__main__":
    main()
