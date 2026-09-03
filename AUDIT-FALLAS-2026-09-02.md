# Auditoría UX & Técnica — ERP Arpía — 2026-09-02

> Revisión a fondo post-sprint de precio/BOM/margen. Clasificado por severidad. Cada ítem con causa, riesgo y fix propuesto. Este archivo es la fuente para los próximos 2 sprints.

---

## 🔴 Crítico — Rompe dato real

### 1. Modelo de costo partido en 4 columnas + `costos_operativos_fijos` polimórfico
- **Dónde:** `Productos` (`costos_operativos_fijos` NOT NULL) + `costo_insumos/mano_obra/cif_energia` (nullable, migración 0020) + `BOM_Insumos`
- **Síntoma:** `ProductosView` mostraba `Costo Insumos: $0` y `Mano: $0` con `Total $31k` (ahora parcheado a `—` y derivado `total - mano - cif`); `Ficha` guarda `costos_operativos_fijos = mano + cif + totalInsumosReal` ($43.050) pero deja `costo_insumos = null`; `GET /productos/{id}/costo` hace `costos_operativos_fijos + SUM(BOM)` → doble conteo si `costos_operativos_fijos` ya es el total.
- **Riesgo:** Editar solo `mano` sin tocar BOM deja `total` desfasado; `Bralete` ($0) vs `PRD-15` ($41k) son el mismo bug con distinto dato.
- **Fix propuesto:**
  1. Migración backfill: `UPDATE Productos SET costo_insumos = GREATEST(costos_operativos_fijos - COALESCE(mano_obra,0) - COALESCE(cif_energia,0), 0) WHERE costo_insumos IS NULL AND costos_operativos_fijos > 0`
  2. En `FichaTecnicaModal.guardarEdicion` ya se persiste `costo_insumos = totalInsumosReal` (hecho 2026-09-02), mantenerlo
  3. A futuro: deprecar `costos_operativos_fijos` como `total` y usarlo solo como `CIF fijo`, o renombrarlo a `costo_total_cache`

### 2. `precio_versions` nunca se puebla → Historial siempre vacío
- **Dónde:** `precio_versions` / `costo_versions` (migración 0019) + `GET /audit-fiscal/precio-versions?producto_id=X` + tab `Historial` en `Ficha` (removido temporalmente por build roto)
- **Síntoma:** `PUT /productos/{id}` actualiza `precio_venta_sugerido` pero no inserta en `precio_versions`; `Historial` muestra `Sin cambios registrados` para siempre.
- **Riesgo:** Sin trazabilidad de quién/cuándo pisó un precio (crítico en slow fashion con 15 modelos y 2 socias).
- **Fix propuesto:** En `backend/app/api/routes/productos.py:update_producto`, si `precio_venta_sugerido` cambió, insertar `PrecioVersion(producto_id, precio, fecha_desde=date.today())` y `CostoVersion` si `costos_operativos_fijos` cambió. Re-agregar tab `Historial` en `FichaTecnicaModal` (código ya estaba, solo re-activar con `v-if` correcto).

---

## 🟠 Alto — UX que miente

### 3. N+1 en grilla de Productos para `BOM count` y `BOM costo`
- **Dónde:** `ProductosView.cargarProductosReales` ahora hace `Promise.all(15 x GET /productos/{id}/bom/insumos)` para `bomCounts`
- **Síntoma:** Con 15 va, con 100+ productos saturás `db` y `rate limit`; además solo trae `count`, no `costo`.
- **Fix:** Nuevo endpoint `GET /productos?include_bom=1` que devuelva `bom_count` y `bom_costo_total` con `LEFT JOIN BOM_Insumos + Insumos` y `GROUP BY` en una sola query. Frontend deja de hacer 15 fetches.

### 4. `60 min` hardcodeado en 3 lugares
- **Dónde:** `NuevaRecetaModal` (`tiempoConfeccion=120`, `costoInsumos=25000`), `ProductosView` (`tiempo ?? 60` — ya parcheado a `—`), `Ficha` (`editTiempo` default 60)
- **Síntoma:** Crear `Blusa` sin tocar tiempo queda en `120` aunque el taller la haga en `60`.
- **Fix:** `NuevaRecetaModal` arranque en `null` y valide `tiempo > 0` obligatorio, o lea `maestros_parametros_costeo.costo_minuto_costura` para estimar `tiempo * costo_minuto`.

### 5. `margenColor` y barra con thresholds fijos `35/60`
- **Dónde:** `ProductosView.margenColor()` y `Ficha.semaforo` usan `35` y `60` hardcode, pero `margen_meta_global` es `35` y puede cambiar a `40` desde `Maestros`.
- **Síntoma:** Cambiás `Maestros → Parámetros → Margen meta 40%` y la barra sigue pintando `En meta` con `35`.
- **Fix:** `margenColor(m, meta)` y `semaforo` con `meta ±10` y `meta+20` dinámico; leer `margenMetaGlobal` también en `ProductosView` (hoy solo en `Ficha`).

---

## 🟡 Medio — Pulido

### 6. `as any` + `any[]` en `Ficha` y `Cotizador`
- **Dónde:** `Ficha.displayItems` con `(it as any).nombre`, `historial = ref<any[]>`, `Cotizador` con `productosRealCot: any[]`
- **Síntoma:** Si cambia `BomInsumoRead.costo_unitario` de `number` a `string`, no te avisa en build.
- **Fix:** Tipar `DisplayItem` y `PrecioVersionRead` y usarlos; ya tenés `BomInsumoRead` y `PrecioVersion` en `audit_fiscal`.

### 7. `Cotizador` con 2 fuentes de costo sin puente
- **Dónde:** `CotizadorView` muestra `Costo manual $X` (metros * precio) y `Costo real BOM $Y` (de `GET /productos/{id}/costo`) con `▲ Diferencia`, pero no hay acción `Usar costo real`.
- **Síntoma:** Usuario ve `Diferencia $38k` y no sabe qué hacer.
- **Fix:** Botón `Usar costo real → rellenar metros/costo` o al menos `precioMetroTela = costoReal / metros`.

### 8. `Insumos` stock con `toLocaleString` sin `minimumFractionDigits`
- **Dónde:** `Ficha` dropdown `Stock 21,2 m` con `maximumFractionDigits: 2` (ya corregido de `21.2000`), pero `21,2` vs `21,20` es inconsistente con `costo $1.635` (3 decimales).
- **Síntoma:** `21,2 m` vs `21,20 m` según si es `21.2` o `21.20`.
- **Fix:** Definir si querés `2` fijos (`minimumFractionDigits: 2`) o `2` máx; hoy es máx, documentarlo.

---

## 🟢 Bajo — Deuda

### 9. `check:mock-leak` pasa, pero `NuevaRecetaModal` aún tiene rama `isMock` con `atelier.crearReceta`
- No rompe en `REAL`, pero si alguien corre `VITE_USE_MOCK=true` en prod por error, vuelve a escribir en memoria.

### 10. `favicon.ico 404` y `chunk 553k`
- `public/favicon.ico` no existe → 404 en cada nav. `index-Ctf__OV-.js 553k` ya te lo marca Vite — con `Productos` + `Ficha` + `Cotizador` todo en `index` es pesado para 3G en taller.
- **Fix:** Agregar `favicon.ico` y `build.rollupOptions.output.manualChunks`.

---

## Plan — Próximos 2 sprints (1 y 2 primero)

| Sprint | Ítems | Estimación |
|--------|-------|------------|
| **1** | **1. Backfill `costo_insumos` + 2. Trigger `precio_versions` en `PUT /productos`** | 1 día (1 migración + 20 líneas en `productos.py` + re-activar tab Historial) |
| **2** | **3. Endpoint `include_bom` + 5. `margenColor` dinámico** | 1 día |

¿Arrancamos con Sprint 1 (1 y 2)?
