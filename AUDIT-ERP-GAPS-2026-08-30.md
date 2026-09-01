# Auditoría Full ERP — Gaps Frontend vs DB (2026-08-30)

> **Objetivo:** relevar TODO lo que el front pide/ muestra y no persiste en Postgres, para crear **1 tanda de migraciones** y cerrar de una.
> **Método:** cruce `src/stores/atelier.ts` (3.411 líneas, fuente de verdad MOCK) + `src/components/atelier/*.vue` + `src/services/api/*.ts` vs `backend/app/models/*.py` + `schemas/*.py` + `alembic/versions`.

---

## Resumen Ejecutivo

| Dominio | Estado | Gaps críticos | Acción propuesta |
|---------|--------|---------------|------------------|
| **Productos / BOM** | 🔴 Crítico | 11 campos cabecera no persisten + BOM no wireado en front | Migración `0020_productos_cabecera` + wire BOM |
| **Insumos** | 🟡 Parcial | `proveedor` fantasma, `categoria` string vs FK, `valor_total` calculado | Ajuste form + validación |
| **Clientes** | 🟢 OK | `pedidos_count/total_compras` calculados, no en DB | Sin migración, derivar de ventas |
| **Ventas** | 🟢 OK (fix previo) | `canal/metodo` ya mapeado, resto computed | Sin migración |
| **Finanzas** | 🟢 OK |  — | Sin migración |
| **Producción** | 🟢 OK | — | Sin migración |
| **Maestros** | 🟢 OK (fix 422 previo) | — | Sin migración |

**Total a migrar:** 1 migración principal (`Productos` cabecera) + opcional 1 para filtros. Resto es wiring front.

---

## 1. Productos / Recetas BOM — 🔴 11 gaps

### 1.1 Frontend (`RecetaBOM` en `atelier.ts` + `NuevaRecetaModal.vue`)
```ts
interface RecetaBOM {
  id, codigo, nombre, categoria, linea, descripcion,
  tiempo_confeccion_min, insumos_count, costo_insumos, mano_obra, cif_energia,
  costo_total_unitario, precio_venta, markup_pct, recomendaciones_taller,
  items: BomItem[], fases: FaseProduccion[]
}
interface BomItem { id, insumo_id, nombre, tipo, consumo_unitario, unidad, merma_pct, costo_unitario, subtotal, ancho, alto }
interface FaseProduccion { nombre, descripcion, minutos }
```

### 1.2 Backend (`Producto` en `models/productos.py` + `schemas/producto.py`)
```py
class Producto: id, tipo_producto_id(FK), nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido
class BomInsumo: producto_id, insumo_id, variante_id, cantidad_requerida, porcentaje_desperdicio, fases(JSONB), tiempo_estimado_minutos, markup_porcentual
class BomProducto: combo_id, producto_incluido_id, cantidad, fases, tiempo_estimado, markup
```

### 1.3 Gaps

| Campo front | En DB hoy | Estado | Plan |
|-------------|-----------|--------|------|
| `codigo` (`REC-ARP-0X`) | No columna, backend usa `PRD-{id}` derivado | Falta | Agregar `codigo VARCHAR(50) UNIQUE NULL` o derivar siempre `PRD-{id}` y quitar input |
| `categoria` (`Corsetería` etc.) | No | Falta | `categoria VARCHAR(100) NULL` o FK a `maestros_categorias_coleccion` |
| `linea` (`Corsetería/Prêt-à-Porter`) | No | Falta | `linea VARCHAR(100) NULL` |
| `descripcion` | No | Falta | `descripcion TEXT NULL` |
| `tiempo_confeccion_min` | No (solo `BomInsumo.tiempo_estimado_minutos` por renglón) | Falta | `tiempo_confeccion_min INT NULL` en `Productos` |
| `costo_insumos` (total) | No (se calcula vía BOM) | Falta / derivado | `costo_insumos NUMERIC(15,4) NULL` o calcular siempre vía `GET /productos/{id}/costo` |
| `mano_obra` | No | Falta | `mano_obra NUMERIC(15,4) NULL` |
| `cif_energia` | Colapsado en `costos_operativos_fijos` (suma) | Mapeo roto | Split en 3 cols o mantener suma: `cif_energia NUMERIC(15,4) NULL` + `costos_operativos_fijos` como suma |
| `costo_total_unitario` | Calculado (`costo_insumos+mano_obra+cif`) | Derivado | No migrar, calcular en schema `@property` |
| `markup_pct` | Solo en `BomInsumo/BomProducto.markup_porcentual` por renglón | Falta cabecera | `markup_pct NUMERIC(15,4) NULL` en `Productos` |
| `recomendaciones_taller` | No | Falta | `recomendaciones_taller TEXT NULL` |
| `items[]` (BOM renglones) | Existe `BOM_Insumos` pero front manda `items:[]` vacío | No wireado | Wirear `POST /productos/{id}/bom/insumos` en `NuevaRecetaModal`/`FichaTecnicaModal` |
| `fases[]` | Existe `BomInsumo.fases JSONB` | No wireado cabecera | Wirear o agregar `fases JSONB NULL` en `Productos` para fases globales |

**Decisión propuesta:** Migración `0020_productos_cabecera` con 9 columnas nuevas en `Productos` (todas `NULL` para no romper datos existentes) + `codigo` único opcional. BOM renglones se wirea sin migración (ya existe).

---

## 2. Insumos — 🟡 3 gaps

### Front (`InsumoAtelier`)
`id, codigo, nombre, descripcion, tipo('Directo'|'Indirecto'), categoria(string), ubicacion(string), proveedor(string), stock_actual, stock_minimo, unidad_medida, costo_unitario, valor_total(calculado)`

### DB (`Insumo` + `CategoriaInsumo`)
`id, categoria_id(FK RESTRICT), nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual, codigo, descripcion, tipo, ubicacion`

| Campo front | En DB | Estado | Plan |
|-------------|-------|--------|------|
| `proveedor` (string) | Eliminado en `0008_remove_proveedores` (col `proveedor_id` nullable sin FK) | Fantasma | Quitar del form o reintroducir `maestros_proveedores` FK si se necesita trazabilidad |
| `categoria` (string libre) | `categoria_id INT FK` + `nombre_categoria` en Read | Mapeo roto | Front debe mandar `categoria_id` (Dropdown de `GET /categorias-insumos`), no string |
| `valor_total` (`stock * costo`) | No columna, calculado | OK | No migrar, calcular en front `@property` |
| `tipo` `Directo/Indirecto` | `tipo VARCHAR(50) NULL` sin CHECK | Falta validación | Agregar `CHECK tipo IN ('Directo','Indirecto')` o dejar libre |

---

## 3. Clientes — 🟢 Sin gap migratorio

Front `ClienteCRM` ↔ DB `Clientes` 1:1. Todos los campos (`ciudad, direccion, tipo, talla_habitual/superior/inferior, categoria_preferida, tipo_producto_frecuente, notas, medidas JSONB`) existen como `NULL` en DB. `pedidos_count/total_compras` son agregados de `Ventas` — no migrar, derivar vía `GET /ventas?cliente_id`.

---

## 4. Ventas — 🟢 Sin gap migratorio (fix previo aplicado)

Front `VentaAtelier` ↔ DB `Ventas` + `Detalles_Venta`. `canal_venta`/`metodo_pago` ya mapeado a `Literal` (`NuevaVentaModal` `canalToApi/metodoToApi`). `subtotal/costo_total/ganancia_neta/margen_pct/reinversion_40/margarita_30/valqui_30` ahora son `@property` en `models/ventas.py` y vienen en `VentaRead`. `nombre_prenda/talla/color` vienen de `variante`/`producto` vía `selectin`. Sin migración.

---

## 5. Finanzas — 🟢 Sin gap

`SociosConfiguracion` 10 cols extendidas, `Liquidaciones` + `LiquidacionDistribucion` + `Anticipos` ya migrados (`0011-0013`). `MovimientosFinancieros` legacy. Sin gap.

---

## 6. Producción — 🟢 Sin gap

`PedidosProduccion` + `PrendasConfeccionadas` (`0017-0018`) alineados con `PedidoProduccion` (`cantidad, estado, prioridad, fechas`) y `PrendaConfeccionada` (`variante_id, talla, estado, ubicacion, costo_real`). Front ya wireado vía `useProduccion/usePrendas`.

---

## 7. Maestros — 🟢 Sin gap (fix 422 previo)

7 catálogos (`Proveedores, CategoriaColeccion, UbicacionTaller, CanalVenta, MetodoPago, TallaEstandar, ProductoSinTalla, ParametrosCosteo`) migrados `0014-0015`. `sanitizePayload` + `codigo` auto ya fixean `422`.

---

## Plan de Migración en Bloque (1 tanda)

### Migración `0020_productos_cabecera` (única necesaria)
```sql
ALTER TABLE "Productos" ADD COLUMN codigo VARCHAR(50) UNIQUE NULL;
ALTER TABLE "Productos" ADD COLUMN categoria VARCHAR(100) NULL;
ALTER TABLE "Productos" ADD COLUMN linea VARCHAR(100) NULL;
ALTER TABLE "Productos" ADD COLUMN descripcion TEXT NULL;
ALTER TABLE "Productos" ADD COLUMN tiempo_confeccion_min INT NULL CHECK (tiempo_confeccion_min >= 0);
ALTER TABLE "Productos" ADD COLUMN costo_insumos NUMERIC(15,4) NULL CHECK (costo_insumos >= 0);
ALTER TABLE "Productos" ADD COLUMN mano_obra NUMERIC(15,4) NULL CHECK (mano_obra >= 0);
ALTER TABLE "Productos" ADD COLUMN cif_energia NUMERIC(15,4) NULL CHECK (cif_energia >= 0);
ALTER TABLE "Productos" ADD COLUMN markup_pct NUMERIC(15,4) NULL CHECK (markup_pct >= 0 AND markup_pct <= 100);
ALTER TABLE "Productos" ADD COLUMN recomendaciones_taller TEXT NULL;
-- Opcional: fases globales si se quiere fuera de BOM renglón
ALTER TABLE "Productos" ADD COLUMN fases JSONB NULL;
CREATE INDEX ix_productos_categoria ON "Productos"(categoria);
CREATE INDEX ix_productos_linea ON "Productos"(linea);
```

### Cambios Backend (sin nueva migración)
*   `schemas/producto.py`: `ProductoCreate/Update` con 9 campos nuevos (`Field(...)`), `ProductoRead` con `@property costo_total_unitario` (suma 3 costos).
*   `models/productos.py`: 9 `mapped_column` nuevas.
*   `api/routes/productos.py`: sin cambio (ya usa `model_dump()`).
*   `api/routes/bom.py`: sin cambio, solo wirear front.

### Cambios Frontend (wiring)
*   `services/api/productos.ts`: `ProductoCreate/Update` con nuevos campos.
*   `NuevaRecetaModal.vue`: mandar payload completo (no solo `costos_operativos_fijos` sumado) + selector `categoria/linea` ya no hardcodeado si se quiere FK.
*   `ProductosView.vue`: mapear `categoria/linea/descripcion/tiempo/costo_insumos/mano_obra/cif/markup/recomendaciones` desde `ProductoRead` sin hardcodear `General/60/0`.
*   `FichaTecnicaModal.vue` / nuevo `BomEditorModal.vue`: tabla editable `items` → `POST /productos/{id}/bom/insumos` + `GET /productos/{id}/costo`.

### Verificación
*   `alembic upgrade head` → `0020` OK
*   `POST /productos` con payload completo → `GET /productos` persiste `F5`
*   `POST /productos/{id}/bom/insumos` + `GET /costo` calcula total
*   `npm run build` + `pytest` + `npm test` 70/70

---

## Recomendación

Ejecutar solo `0020_productos_cabecera` (9 cols) y el wiring front. Insumos `proveedor` y `categoria` son ajustes de form sin migración. Resto de dominios no necesitan migración.

¿Aprobás `0020` para que lo genere e implemente en bloque?
