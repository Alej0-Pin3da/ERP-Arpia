# LOG DE PENDIENTES — Migración ARPIA.xlsx → ERP Arpia
Fecha: 2026-08-09

## SUBIDO a GitHub (origin/main + ramas)
- **main** → `4c55e1d` (contiene: slices 1–9 + fix1 + fix2, **385 tests passed**)
- Ramas: `feat/migracion-excel-slice1..9`, `feat/migracion-excel-fix1`, `feat/migracion-excel-fix2` (todas pusheadas)
- `feat/migracion-excel-fix3` → WIP **SIN VERIFICAR** (commit `621328b`) — ver sección 2

---

## 1. LO QUE YA ESTÁ SUBIDO Y VERIFICADO (main)
- Pipeline completo F0–F7 en `backend/migrate/` + `wac.py` extendido (fecha_compra + commit=False)
- Ajuste manual de stock para 10 insumos residuales (`backend/migrate/adjust_stock.py`)
- 385 tests passed, 0 regresión
- **La DB local YA TIENE la migración cargada** (13 ventas, 40 compras, 104 movimientos, 9 clientes, socios 3) — esto NO se sube (es local)

---

## 2. WIP SIN VERIFICAR — `feat/migracion-excel-fix3` (commit `621328b`)
**QUÉ ES**: Corrección del check N7a para que cuente por clave natural (fecha+cantidad+precio) en vez de por nombre de entidad. El N7a actual marca "ERROR duplicados 23" que son **FALSOS POSITIVOS** (Argolla 10 mm con 2 compras legítimas, Tote Bag vendida 6 veces, etc. — no son duplicados reales; la idempotencia real la valida N7g que pasa OK).

**POR QUÉ NO SE SUBE A MAIN**: la tarea se canceló a mitad, los cambios están SIN correr la suite completa. Probablemente rompen tests (modificó conftest.py, test_productos, test_finanzas, etc. — 14 archivos, +520/−137).

**QUÉ TOCA DECIDIR**:
- Revisar `backend/migrate/validate.py` (214 líneas cambiadas): el N7a por clave natural.
- Los cambios en `backend/tests/conftest.py` y los tests (aislamiento/limpieza).
- Si lo apruebas: correr `python -m pytest backend/tests -q` (debe quedar ≥385 green), luego merge a main.

---

## 3. PENDIENTES / NO SUBIBLES (para tu revisión)

### 3.1 La carga real (solo local, no es código)
- La DB local tiene la migración **cargada y operativa**: 13 ventas, 40 compras, 104 movimientos, 9 clientes.
- F7 reporta: N7b ✓, N7c ✓ (con nota de 2 movimientos duplicados en el plan, dedup correcto), N7d WARN menor (0.18 dif en 2 tules — tolerancia decimal), N7e ✓ (7 ventas analizadas), N7f ✓, N7g ✓.
- **Único ERROR**: N7a "duplicados 23" = falso positivo del check (ver sección 2).

### 3.2 Decisiones de negocio que quedan abiertas (NO bloquean, documentadas)
1. **GASTOS ARPIA sin fecha** (4 filas: MATERIALES SURTIDOS, DOMICILIO CAJA, ENVIO TELA, AYUDANTE CORTE): la hoja no tiene columna de fecha → NO migraron (política D5 "nunca now()"). Si querés que entren, hay que darles fecha manual.
2. **~30% de compras sin fecha** en INVERSION MARGARA (sesgos, hilos, bonos, etc.): omitidas por D5 (heredan contigua o se omiten). Revisar el JSON `backend/migrate/reports/migracion_20260809_100153.json` para ver la lista completa de WARN.
3. **2 combos "Caja Despertar"** omitidos en BOM: el producto "Noche y Dia" no está en el catálogo (no aparece como producto propio en el Excel; se descartó como ghost duplicado). Si el negocio vende esas cajas, hay que crearlas.
4. **Stock manual de 10 insumos** (cadenas totebag, cremallera, tapavarilla, satines/sesgos): se fijó stock = consumo BOM + 10% margen (no viene del Excel; el Excel no registraba esas compras en formato interpretable).

### 3.3 ARPIA.xlsx
- **NO se sube** (está en `.gitignore` — son datos del negocio, correcto que no vayan al repo).

### 3.4 Backfill F8 hidratacion-datos-faltantes (2026-09-06, script + tests <= 400 lines, single PR)

- Script: `backend/migrate/backfill_precios_costos.py` (`--dry-run` default, `--apply` per-entity tx + audit JSON en `backend/migrate/reports/backfill_*.json`, gitignored). Migracion `0028_backfill_provenance` (`origen_precio`/`origen_costo` NULL=`pipeline`, `backfill`=hidratado). `loaders.py` intacto (solo lectura).
- Precios canonicos csv (`csv/ARPIA - VENTAS.csv`): Caja Saca Las Garras 295000, Set Aelo 80000, Blusa ML 90000, Totebag 45000, Corset Garras 95000 (moda; 60500/80750 divergen + WARN), Falda Emily 80000. Set Ocipete queda en 0: sus 2 filas csv son DESC 25% (precio con descuento, nunca lista) + WARN. Celeno locked 75000.
- Costos: receta E (valor metro) + CAJAS costo; `Compras_Insumos` nunca se siembra (conteo intacto, sin contaminar WAC). Proveedores: insert-only de INVERSION Provedor (~25 nombres; 86 filas sin proveedor no generan master; `proveedor_id` NULL salvo match exacto — no hay columna legacy de proveedor para wirear).
- Drift memo (verificado 2026-09-06): workbook 15 nombres distintos (VENTAS A + CAJAS prendas + DESCUENTOS B) vs catalogo 14 (`PRODUCTOS_CATALOGO`) vs live 15 (14 + `Accesorio TEST`, residuo de tests, no se toca). Genericos (`bustier`/`corset`), empaque (`caja`/`vela`/`papel`/`envio`), `noche y dia`/`despertar` son componentes/ghosts: deferred, no se resucitan. Bralete/Hypatia/Despertar x2 quedan en 0 con WARN (sin fuente canonica — EXM-2, no se infiere).
- Anomalia preexistente (no tocada): precios live no-cero mezclan origenes (ej. `Corset Artemisia` 75000 sin fuente en workbook); el script los preserva (`non-zero pipeline value preserved`).
- Cierra: 6 precios con fuente canonica hidratables, 35 insumos con costo 0 y stock > 0 identificados, `maestros_proveedores` bootstrap. Abierto/manual: Bralete, Hypatia, 2 Despertar (precio manual del negocio si aplica).

### 3.5 Backups
- Backup pre-migración: `C:\Users\AstarotH\AppData\Local\Temp\opencode\arpia_pre_migracion_20260809_084851.dump`
- Backup pre-recarga: `C:\Users\AstarotH\AppData\Local\Temp\opencode\arpia_pre_recarga_20260809_100139.dump`
- (están en temp local, no en el repo)

---

## 4. CÓMO REVISAR (sugerencia de orden)
1. **Abrí el PR de la rama `feat/migracion-excel-fix3`** en GitHub y mirá el diff de `validate.py` (lo más importante).
2. Si el N7a por clave natural te parece bien → decime y lo verifico (suite completa) y lo mergeo a main.
3. Revisá los WARN del JSON de traza (sección 3.2) para decidir fechas manuales / combos faltantes.
4. Si querés que los gastos sin fecha entren, me pasás las fechas o me decís la política (ej: "ponerles 2026-01-15" o "heredar la última fecha de la hoja").
