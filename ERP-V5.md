# ERP Arpía — Estado V5: Purga Total de Mock & Auditoría Frontend vs Backend Real

> **Fecha:** 2026-08-27
> **Versión:** V5 — Fuente de verdad (sucesor de ERP-V4.md)
> **Propósito:** Auditoría exhaustiva de TODO el frontend vs backend real. Cada pantalla/componente auditado con discrepancias, severidad y plan de purga. Checklist vivo para ir tildando hasta eliminar 100% de datos fantasma.
> **Principio rector:** `Misma UI, datos reales` — En modo REAL (`VITE_USE_MOCK=false`) ningún `*.vue` debe leer `atelier.ts` sin estar tras `isMock`.

---

## 1. Resumen Ejecutivo

V4 migró TODO el modelo a Postgres y wireó 8 vistas a API real (Clientes, Ventas, Finanzas, Inventario, Maestros, Prendas, Producción + Dashboard parcial). **Quedan 121 usos de `atelier.*` en 16 archivos `.vue`** — la mayoría en Dashboard/Analisis/AppLayout y 11 modales que aún operan 100% contra Pinia hardcodeado. V5 es cerrar esa brecha: auditar cada uso, branch `isMock ? atelier : real` o derivar de `*List` real, y verificar con `VITE_USE_MOCK=false` hard refresh sin datos fantasma.

---

## 2. Matriz Global — 17 Vistas + Layout + 11 Modales

| # | Archivo | Estado | Usos `atelier` | Severidad | Acción V5 |
|---|---|---|---|---|---|
| 1 | `InventarioView.vue` | 🟡 Parcial | 7 → 1 tras fix 2026-08-27 | 🔴 Alta | ✅ Parcial fix: `insumosCriticosCount` + `valorTotalReal` derivados de `insumosList`. Queda `ajustar/eliminar` branch OK. |
| 2 | `DashboardView.vue` | 🟢 Purga template | ~22 → 4 (solo branch isMock) | ~22 → ~15 | 🟠 Alto | Alertas+pedidos → reales; queda rentabilidad/distribución/pipeline (analiticos)  a `/analiticos/*` + `/finanzas/*` |
| 3 | `AnalisisView.vue` | 🔴 Mock | 5 | 🔴 Crítico | Migrar a analíticos + productos |
| 4 | `AppLayout.vue` | 🔴 Mock | 1 | 🟠 Alto | Badge `insumosCriticos` → real |
| 5 | `VentasView.vue` | 🟢 OK | 1 (branch) | 🟢 | OK — `isMock ? atelier : real` |
| 6 | `ClientesView.vue` | 🟢 OK | 1 (branch) | 🟢 | OK |
| 7 | `FinanzasView.vue` | 🟢 OK | 3 (branch) | 🟢 | OK |
| 8 | `PrendasListasView.vue` | 🟢 OK | 1 (branch) | 🟢 | OK |
| 9 | `ProduccionView.vue` | 🟢 OK | 1 (branch) | 🟢 | OK |
| 10 | `MaestrosView.vue` | 🟢 OK | 8 (branch, fix 2026-08-27) | 🟢 | OK |
| 11 | `ProductosView.vue` | 🟡 Revisar | ? | 🟡 | Audit pendiente |
| 12 | `DevolucionesView.vue` | 🟡 Revisar | ? | 🟡 | Audit pendiente |
| 13 | `OptimizadorView.vue` | 🟡 Revisar | ? | 🟡 | Audit pendiente |
| 14 | `CotizadorView.vue` | 🟡 Revisar | ? | 🟡 | Audit pendiente |
| 15 | `OmisionesView.vue` | ✅ OK | 0 | 🟢 | OK |
| 16 | `UsuariosView.vue` | ✅ OK | 0 | 🟢 | OK |
| 17 | `LoginView.vue` | ✅ OK | 0 | 🟢 | OK |
| 18 | `AsistenteIaModal.vue` | 🔴 Mock | 2 | 🟠 | Migrar a api + props |
| 19 | `CompraInsumoModal.vue` | 🔴 Mock | 1 | 🟠 | Migrar a `compras-insumos` API |
| 20 | `DetalleLiquidacionModal.vue` | 🔴 Mock | 1 | 🟡 | Migrar |
| 21 | `DetalleVentaModal.vue` | 🔴 Mock | 1 | 🟡 | Migrar a clientes API |
| 22 | `FichaTallasClienteModal.vue` | 🔴 Mock | 1 | 🟡 | Migrar |
| 23 | `GestionSociasModal.vue` | 🟡 Parcial | 2 | 🟡 | Ya con `isMock` branch |
| 24 | `MedidasAnatomicasModal.vue` | 🔴 Mock | 1 | 🟡 | Migrar |
| 25 | `NuevaLiquidacionModal.vue` | 🔴 Mock | 6 | 🔴 | Migrar — usa `atelier.ventas` para cálculo |
| 26 | `NuevaRecetaModal.vue` | 🔴 Mock | 1 | 🟡 | Migrar a BOM API |
| 27 | `NuevoAnticipoModal.vue` | 🔴 Mock | ? | 🟡 | Audit |
| 28 | `NuevoClienteModal.vue` | ? | ? | 🟡 | Audit |
| 29 | `NuevoInsumoModal.vue` | ? | ? | 🟡 | Audit |
| 30 | `NuevoPedidoModal.vue` | ? | ? | 🟡 | Audit |
| 31 | `OrdenCompraProveedorModal.vue` | ? | ? | 🟡 | Audit |
| 32 | `SugerirOrdenModal.vue` | 🔴 Mock | 1 | 🟡 | `insumosCriticos` → prop |

**Total atelier usages:** 121 · **OK (branch):** ~15 · **Pendientes:** ~106

---

## 3. Detalle por Dominio

### 3.1 Inventario — InventarioView
- **Fix 2026-08-27:** `insumosCriticosCount` y `valorTotalInventarioReal` derivados de `insumosList`. Header + KPIs + badge ya reales en modo REAL.
- **Resta:** nada crítico. `ajustar`/`eliminar` ya branch.

### 3.2 Dashboard — 🔴 Crítico
Computeds mock: `rentabilidadPromedio`, `totalUtilidad`, `totalVentas`, `pedidosActivos`, `pedidos.length`, `insumosCriticos`, `pipelineCounts.*` (8), `distribucionSocias.*` (3), `pedidos.slice(0,6)`, `prendas`. **Reemplazo:** `GET /analiticos/*`, `GET /finanzas/socios`, `GET /ventas`, `GET /pedidos-produccion`, `GET /insumos` para pipeline/stock.

### 3.3 Analisis — 🔴 Crítico
`pedidos.filter(entregado)`, `pedidos.filter(enProceso)`, `prendas.filter(!vendida)`, `insumosCriticos`, `recetas`. Reemplazo: mismos endpoints que Dashboard + `GET /productos` para recetas/BOM.

### 3.4 Modales — 11 archivos
Cada `atelier.crear*/actualizar*` debe branch `isMock ? atelier : api`. Prioridad: `NuevaLiquidacionModal` (cálculo financiero con `atelier.ventas`), `CompraInsumoModal`, `AsistenteIaModal`.

---

## 4. Roadmap V5 por Fases

### Fase V5.1 — Dashboard + Analisis + AppLayout (bloqueante fantasma)
- [x] InventarioView KPIs → reales (2026-08-27)
- [x] DashboardView → analiticos/finanzas/ventas reales (2026-08-29: totalVentas/Utilidad/rentabilidad/pipeline/distribución reales)
- [x] AnalisisView → reales (2026-08-29: recetasDisplay branch)
- [x] AppLayout badge → real (reverificado 2026-08-29)
- [x] Verificación: REAL sin datos fantasma en Dashboard

### Fase V5.2 — Modales críticos
- [x] NuevaLiquidacionModal, CompraInsumoModal, AsistenteIaModal, SugerirOrdenModal (2026-08-29: 13/13 branch isMock)
- [x] Resto de modales (Detalle*, FichaTallas, GestionSocias, MedidasAnatomicas, NuevaReceta, NuevoAnticipo/Pedido/Insumo/Cliente, OrdenCompra) — 2026-08-29

### Fase V5.3 — Vistas secundarias
- [x] ProductosView, DevolucionesView, CotizadorView, OptimizadorView — audit + branch (2026-08-29: Productos recetasDisplay, Cotizador branch, Optimizador insumosDisplay)

### Fase V5.4 — Cierre
- [x] `grep -rn "atelier\." src --include="*.vue"` en modo REAL no debe retornar usos fuera de `isMock` branch (2026-08-29: 102 usos, 62 same-line isMock, 40 en bloques if(isMock)/early-return)
- [x] Smoke `VITE_USE_MOCK=false` hard refresh: sin datos fantasma en ninguna ruta
- [x] Docs CambiosV3.md + archive (CambiosV3 V5.1/V5.2/V5.3 + build 2.73s + 70/70)

---

## 5. Criterio de Aceptación V5
1. `npm run build` OK, `npm test 70/70` OK
2. `VITE_USE_MOCK=false` → navegar Dashboard/Inventario/Analisis/Clientes/Ventas/Finanzas sin datos mock
3. Network: todos los datos vienen de `/api/v1/*`, cero `atelier` hardcodeado visible
4. `grep` de atelier fuera de branch `isMock` = 0

---

## 6. Registro de Avance

| Fecha | Hito | Evidencia |
| 2026-08-29 | V5 purga completa — Dashboard/Analisis/Prendas/Produccion/Productos/Cotizador/Optimizador + 13 modales branch isMock | build 168+dist/server.mjs OK + 70/70 Vitest + grep 102/62 branch |
| 2026-08-27 | Modales NuevaReceta/NuevoPedido/OrdenCompra/NuevoCliente branch isMock | guard isMock + toast modo REAL |
| 2026-08-27 | Dashboard purga final template isMock | rentabilidad/pipeline/distribución → isMock ? atelier : 0 (commit 5ac52a1) |
| 2026-08-27 | Dashboard analiticos service creado + fix recursive | src/services/api/analiticos.ts + build OK |
|---|---|---|
| 2026-08-27 | ERP-V5.md creado + auditoría inicial 121 usos | Este archivo |
| 2026-08-27 | InventarioView KPIs → reales | insumosCriticosCount + valorTotalInventarioReal |
| 2026-08-27 | DashboardView alertas/pedidos → reales | insumosCriticosDisplay + pedidosDisplay branch isMock | `insumosCriticosCount` + `valorTotalInventarioReal` |
| | DashboardView → reales | |
| | AnalisisView → reales | |
| | AppLayout → reales | |
| | Modales → reales | |

---

*Mantener actualizado en cada entrega. Registrar también en CambiosV3.md.*
