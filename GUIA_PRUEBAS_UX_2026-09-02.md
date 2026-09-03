# Guía de Pruebas UX — ERP Arpía — 2026-09-02

> Todos los cambios de UX del sprint. Probalos en `REAL` (`VITE_USE_MOCK=false`, `npm run start:all`).

---

## 1. Ficha Técnica — Precio sugerido auto + override (ya probado)
- **Dónde:** `ProductosView` → `Ver Ficha Técnica` → bloque `Costeo & Fijación`
- **Qué:** `PRECIO VENTA $83.000` grande (precio guardado), `Sugerido (35%): $48.106`, `Margen real: 62% | Meta: 35%`
- **Probar:** Abrir `PRD-2 Corset Artemisia` → ver grande `$83k` + sugerido. Editar → input arranca en `$83k`, tipeá `$60k` → margen live cambia → `↺ auto` vuelve a `$48k` → `Guardar` → sin cerrar ves `$60k` actualizado.

## 2. Ficha — Semáforo de margen + sin guardar
- **Dónde:** Header de la ficha
- **Qué:** Badge `En meta +73%` verde / `Por debajo` ámbar / `Pérdida` rojo / `Alto` celeste + `• sin guardar` ámbar pulsante al tocar cualquier campo. Cerrar sin guardar → `confirm("¿Descartar cambios?")`.
- **Probar:** Editar nombre o precio → aparece `• sin guardar` + semáforo cambia. Intentar cerrar con X → confirm. Guardar → desaparece.

## 3. Ficha — BOM con stock/costo visible
- **Dónde:** Ficha → `Agregar insumo al BOM`
- **Qué:** Dropdown `Nombre (COD) — $2.700/m — Stock 42 ⚠️` si `stock <= min`. Debajo: `$2.700/m | Stock 42` badge + warning `Stock crítico` o `Necesitás 10.5m, stock 5`. Al agregar con stock bajo → toast `Stock bajo`.
- **Probar:** Seleccionar insumo con stock bajo, pedir cantidad mayor al stock → ver badge rojo + toast al agregar.

## 4. Productos — Tarjeta densidad + margen real
- **Dónde:** `ProductosView` grilla de tarjetas
- **Qué:** `Costo $31.269 → Precio $83.000 | Margen 62%` con barra de margen (verde/ámbar/rojo). Chip `BOM: 3 insumos` verde si tiene BOM, gris `Sin BOM`. Ordenar por margen (mayor margen primero) opcional.
- **Probar:** Ver `PRD-2` ahora muestra `62%` (antes `0%`). `Bralete` sin BOM muestra `Sin BOM`. Cambiar filtro categoría → margen se mantiene.

## 5. Ficha — Costeo transparente desglosado
- **Dónde:** Ficha → `Costeo & Fijación`
- **Qué:** Desglose `Insumos (BOM) $48.000 + Mano $0 + CIF $31.269 = Costo base $31.269 + BOM $48.000 = Total $79.269` con tooltip `¿Qué es CIF?`. Separado visualmente de `Precio venta / sugerido`.
- **Probar:** Producto con BOM vs sin BOM → ver desglose correcto. Editar `Mano` a `$5.000` → `Total` y `Sugerido` suben live.

## 6. Ficha — Historial de precio (nuevo tab)
- **Dónde:** Ficha → tab `Historial` (al lado de `Ficha Técnica` / `Matriz`)
- **Qué:** Timeline de `precio_versions`: `02/09 $60k 48% (vos) ← 12/08 $83k 62%`. Si no hay historial, `Sin cambios registrados`.
- **Probar:** Guardar nuevo precio → abrir `Historial` → ver entrada nueva arriba. En producto sin historial → mensaje vacío.

## 7. Productos — Filtros y búsqueda mejorados
- **Dónde:** `ProductosView` header
- **Qué:** Búsqueda por `nombre/código/descripción` + filtro categoría + filtro `Con/Sin BOM` + filtro `Margen <0 / <35% / >60%` + ordenar por `Margen / Precio / Costo`.
- **Probar:** Buscar `Corset` → solo corsets. Filtrar `Sin BOM` → solo `Bralete` etc. Ordenar por `Margen` → mayor margen arriba.

## 8. Producción — Kanban por fase
- **Dónde:** `ProduccionView`
- **Qué:** Toggle `Lista / Kanban`. Kanban columnas `Corte | Confección | Acabado | Control` con cards de pedidos. Cada card muestra `Modelo | Cliente | Tiempo | Costo`. Drag & drop cambia fase (si backend lo permite, sino solo visual).
- **Probar:** Cambiar a `Kanban` → ver pedidos agrupados. Mover card de `Corte` a `Confección` → toast.

## 9. Cotizador — Conectado a BOM real
- **Dónde:** `CotizadorView`
- **Qué:** Al seleccionar modelo, trae `BOM real + costo real + sugerido` del backend, no valores fijos. Muestra `Costo $69k → Sugerido $106k → Precio final $120k` con IVA y comisión canal.
- **Probar:** Seleccionar `Accesorio TEST` → ver costo `69k` (no `31k` fijo). Cambiar canal `Web 5%` → precio final ajusta.

## 10. Mobile — Ficha compacta
- **Dónde:** Ficha en `sm` (<640px)
- **Qué:** En móvil, `Costo` y `Precio` en 2 columnas, BOM colapsable, inputs más grandes para dedos.
- **Probar:** Achicar viewport a móvil → ver layout 2 cols, BOM colapsado con `Ver 3 insumos`.

---

## Cómo probar todo de golpe (5 min)

1. `npm run start:all` (o `docker compose up -d` + `npm run dev`)
2. Login admin
3. `Productos` → verificar tarjetas con `62%`, `Sin BOM`, barra
4. Abrir `Corset Artemisia` → verificar `PRECIO VENTA $83k` + `Sugerido $48k` + `Margen 62% | Meta 35%` + semáforo `En meta`
5. `Editar` → cambiar precio a `$60k` → ver `• sin guardar` + semáforo live → `Guardar` → ver `$60k` sin cerrar
6. `Agregar insumo al BOM` → dropdown con `— $X/m — Stock N` → seleccionar stock bajo → ver warning → `Agregar`
7. Cambiar `Mano` a `$5000` → ver `Costo total` y `Sugerido` subir live
8. Tab `Historial` → ver timeline
9. Volver a `Productos` → `Filtros` → probar `Sin BOM`, `Margen <35%`, `Ordenar por Margen`
10. `Producción` → toggle `Kanban` → ver columnas
11. `Cotizador` → seleccionar modelo → ver costo real
12. Achicar a móvil → verificar ficha compacta

---

## Notas
- Todos los cálculos usan `margen_meta_global_pct` de `Maestros → Parámetros` (hoy `35%`). Cambialo ahí y el `Sugerido` se recalcula.
- `Stock` viene de `Insumos.stock_actual` vs `stock_minimo`.
- Historial lee `precio_versions`/`costo_versions` si el backend las expone; si no, muestra `Sin historial`.
