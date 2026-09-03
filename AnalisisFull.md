# Análisis Full ERP-Arpia — fecha 2026-09-03

> Estado global: backend REAL cubre ~95% del DDL; frontend REAL cubre ~70% del backend. Brecha principal: auditoría, movimientos financieros, devoluciones e historial de versiones sin UI dedicada. Fuente de verdad del esquema: `DDL.sql` (1210 líneas, 36 tablas incl. `alembic_version`).

## 1. Resumen ejecutivo (estado global, % aproximado por capa)

| Capa | Cobertura aproximada | Veredicto |
|------|----------------------|-----------|
| Base de datos (`DDL.sql`) | 100% (referencia) — 35 tablas de negocio + `alembic_version` | Fuente de verdad. Esquema coherente, con 2 FK faltantes y 2 CHECK desincronizados (ver §6). |
| Backend (`backend/app`) | ~95% — 12 archivos de modelos cubren las 35 tablas; 22 routers registrados en `backend/app/api/router.py`; schemas para todos los dominios | Completo salvo matices: `liquidacion_distribucion` sin endpoint directo (embebida), `Detalle_Ventas` / `Items_Devolucion` solo anidados, `compras-insumos` sin update/delete, `devoluciones` sin PUT/DELETE. |
| Frontend (`src/`) | ~70% REAL — 16 vistas, 16 servicios API, 9 composables; 10 vistas con switch MOCK/REAL funcional, 6 con REAL parcial o solo lectura | Cableado REAL sólido en clientes, ventas, insumos, productos/BOM, producción, prendas, finanzas (liquidaciones/anticipos/socios), maestros, omisiones. Faltan: auditoría, movimientos financieros, usuarios CRUD, devoluciones create, historial de versiones (tab removido), cierres. |
| Dual MOCK/REAL | Activo vía `src/composables/useMode.ts` + `src/services/api/__mode.ts` (`GET /api/v1/__mode`) + `src/stores/atelier.ts` (deprecated, solo fallback) | Funciona, pero ~10 vistas aún importan `useAtelierStore` como fallback. Purga mock V5.1–V5.3 pendiente de completar. |

Qué revisar primero: §5 (matriz) para el mapa completo, §6 P0 para lo que bloquea operación real.

## 2. Base de datos (DDL.sql) — inventario de tablas por dominio + observaciones

Total: 35 tablas de negocio + `alembic_version`. Convención mixta preservada del legacy: `"PascalCase_Con_Guion"` (núcleo original) + `snake_case` (V4/V5).

### 2.1 Identidad y seguridad (3)

| Tabla | Columnas clave | Observaciones |
|-------|---------------|---------------|
| `"Usuarios"` | `id, nombre, email UNIQUE, password_hash, rol CHECK(admin/operador/consulta)` | Sin `created_at`. Rol `gerente` usado en `audit_fiscal.py` (`require_roles("admin","gerente")`) NO existe en el CHECK → 403 garantizado para ese rol. |
| `"RefreshTokens"` | `usuario_id FK CASCADE, token_hash UNIQUE, expira_en, revocado_en` | Correcta. Solo backend, sin UI (correcto por seguridad). |
| `"AuditLog"` | `usuario_id FK SET NULL, entidad, entity_id, accion, valores_old/new jsonb, request_id, ip, user_agent, timestamp` | Índices compuestos `ix_auditlog_*`. Sin UI (gap P0). |

### 2.2 Catálogos base (2)

| Tabla | Observaciones |
|-------|---------------|
| `"Tipos_Producto"` (`id, nombre UNIQUE`) | Catálogo simple. CRUD completo en backend + frontend (`productos.ts` → `GET /tipos-producto`). |
| `"Categorias_Insumos"` (`id, nombre UNIQUE`) | Idem. Router propio `categorias_insumos.py` (`/categorias-insumos`, CRUD completo). |

### 2.3 Insumos y compras (3)

| Tabla | Observaciones |
|-------|---------------|
| `"Insumos"` | `categoria_id FK RESTRICT, codigo, tipo, ubicacion (varchar libre, no FK a maestros_ubicaciones_taller), stock_actual/minimo, costo_promedio_actual numeric(15,4)` |
| `"Compras_Insumos"` | `insumo_id FK RESTRICT, cantidad_comprada, precio_unitario_compra, proveedor_id INT SIN FK (índice `ix_Compras_Insumos_proveedor_id` pero sin constraint)`, `factura, costo_unitario_aplicado`. Migración `20260821_compras_wac_ux.py` implementa promedio ponderado (WAC). |
| `"BOM_Insumos"` | `producto_id FK CASCADE, insumo_id FK RESTRICT, variante_id FK CASCADE NULL, cantidad_requerida, porcentaje_desperdicio, fases jsonb, tiempo_estimado_minutos, markup_porcentual`, UNIQUE `(producto_id, insumo_id, variante_id)` |

### 2.4 Productos, variantes y combos (4)

| Tabla | Observaciones |
|-------|---------------|
| `"Productos"` | Cabecera V4 (`0020_productos_cabecera.py`): `tipo_producto_id FK RESTRICT, codigo UNIQUE NULL, categoria/linea, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido, tiempo_confeccion_min, costo_insumos (backfill `0021_backfill_costo_insumos.py`), mano_obra, cif_energia, markup_pct, recomendaciones_taller, fases jsonb`. Ficha Técnica unificada lee/escribe aquí. |
| `"Variantes_Producto"` | `producto_id FK CASCADE, nombre_variante, precio_venta NULL`, UNIQUE `(producto_id, nombre_variante)` |
| `"BOM_Productos"` | Combos: `combo_id FK CASCADE → Productos, producto_incluido_id FK RESTRICT → Productos`, UNIQUE `(combo_id, producto_incluido_id)` |
| `precio_versions` / `costo_versions` | Versionado fiscal (`0019_audit_fiscal_versioning.py` + `0021`): `producto_id FK CASCADE (+ variante_id en precio), costo/precio numeric(15,4), fecha_desde, creado_por`. Solo lectura inline en `FichaTecnicaModal.vue`; tab Historial removido para no bloquear build. |

### 2.5 Producción e inventario de prendas (2)

| Tabla | Observaciones |
|-------|---------------|
| `pedidos_produccion` | `producto_id FK CASCADE, variante_id FK SET NULL, cantidad, cantidad_producida DEFAULT 0, estado DEFAULT 'pendiente', prioridad DEFAULT 'normal', fecha_pedido DEFAULT CURRENT_DATE, fecha_entrega_estimada NULL`. Sin CHECK de estado/prioridad (los enums viven solo en `backend/app/models/produccion.py`). |
| `prendas_confeccionadas` | `variante_id FK CASCADE (NOT NULL, sin prenda genérica por producto), talla NULL, estado DEFAULT 'disponible', ubicacion varchar libre, costo_real/precio_venta NULL, pedido_id FK SET NULL`. |

### 2.6 Clientes y ventas (4)

| Tabla | Observaciones |
|-------|---------------|
| `"Clientes"` | CRM extendido (`0009_extend_clientes_crm.py`): `documento_identidad UNIQUE NULL, ciudad/direccion/tipo, talla_habitual/superior/inferior, categoria_preferida, tipo_producto_frecuente, notas, medidas jsonb`. Índices `ix_clientes_ciudad/tipo`. |
| `"Ventas"` | `cliente_id FK SET NULL, descuento_porcentaje, estado CHECK(completada/anulada), canal_venta CHECK(web/whatsapp/instagram/feria/showroom_pereira) DEFAULT 'feria', metodo_pago varchar(50) LIBRE (sin FK ni CHECK), es_regalo bool (migración `27d5c5b6fd80`), reversed_* (migración `98bda77bcd4d`)`. CHECK de canal NO incluye canales de `maestros_canales_venta` (desincronización P1). |
| `"Detalle_Ventas"` | `venta_id FK CASCADE, producto_id FK RESTRICT, variante_id FK SET NULL, cantidad/precio_unitario_aplicado/costo_unitario_aplicado numeric(15,4)`. Sin endpoint directo (anidado en `POST /ventas`). |
| `"Devoluciones"` + `"Items_Devolucion"` | Cabecera: `venta_id FK CASCADE, motivo, monto_reembolsado, tipo CHECK(parcial/total), estado CHECK(draft/confirmed/cancelled/reversed), usuario_id`. Ítems: `devolucion_id FK CASCADE, producto_id FK RESTRICT, variante_id FK SET NULL, cantidad/precio_unitario/subtotal`. |

### 2.7 Finanzas, socios y liquidaciones (5)

| Tabla | Observaciones |
|-------|---------------|
| `"Socios_Configuracion"` | `nombre UNIQUE, porcentaje_participacion CHECK>0, rol/banco/es_fondo_taller/telefono/email/tipo_cuenta/numero_cuenta/titular_cuenta/activo/notas` (`0011_extend_socios_configuracion.py`). |
| `"Movimientos_Financieros"` | `tipo CHECK(Gasto/Inversion/Retiro), estado CHECK(draft/confirmed/cancelled/reversed), socio_id FK SET NULL, liquidacion_id varchar(12) UNIQUE PARCIAL (WHERE NOT NULL, sin FK a liquidaciones.id integer), reversed_*`. `liquidacion_id` varchar vs `liquidaciones.id` integer → join imposible (P1). |
| `liquidaciones` | `codigo varchar(12) UNIQUE, periodo, fecha_cierre, total_ventas_brutas, costo_taller_insumos, gastos_operativos, utilidad_neta_total, fondo_reinversion_monto, utilidad_repartible, estado CHECK(BORRADOR/APROBADA/PAGADA)` (`0012_create_liquidaciones.py`). |
| `liquidacion_distribucion` | `liquidacion_id FK CASCADE, socia_id FK CASCADE, porcentaje, monto_bruto, deduccion_anticipos DEFAULT 0, monto_neto, estado_pago CHECK(PENDIENTE/PAGADO/RETENIDO)`, UNIQUE `(liquidacion_id, socia_id)`. Sin endpoint directo (calculada en `_liquidacion_response`). |
| `anticipos` | `socia_id FK CASCADE, liquidacion_id FK SET NULL, monto CHECK>0, fecha DEFAULT CURRENT_DATE, estado CHECK(PENDIENTE_DESCUENTO/DESCONTADO/ANULADO)` (`0013_create_anticipos.py`). |

### 2.8 Maestros V4 (8)

`maestros_proveedores`, `maestros_categorias_coleccion` (`tipo_talla` CHECK 3 valores, `margen_meta_pct`, `total_modelos`), `maestros_ubicaciones_taller` (`codigo LIKE 'UB-%'`, `tipo` CHECK 4 valores), `maestros_canales_venta` (`codigo UNIQUE, tipo CHECK FISICO/DIGITAL/EVENTO, comision_pct, costo_fijo_mensual`), `maestros_metodos_pago` (`codigo UNIQUE, tipo CHECK TRANSFERENCIA/BILLETERA_DIGITAL/EFECTIVO/PASARELA_DATAFONO, comision_pct`), `maestros_tallas_estandar` (`talla/orden UNIQUE`), `maestros_productos_sin_talla`, `maestros_parametros_costeo` (singleton: `costo_minuto_costura, costo_hora_patronaje, margen_meta_global_pct, desperdicio_textil_default_pct, iva_regimen_pct, distribucion_reinversion_pct DEFAULT 40, reparto_margara/valqui_pct DEFAULT 30`). Migraciones `0014_maestros_core.py`, `0015_maestros_tallas.py`.

### 2.9 Migración y control (2)

| Tabla | Observaciones |
|-------|---------------|
| `"Migracion_Omisiones"` | `corrida_id, fase, hoja, fila, celda, nivel CHECK(WARN/ERROR), mensaje, resuelta DEFAULT false` (`0005_migracion_omisiones.py`). UI `OmisionesView.vue` REAL. |
| `cierres_mensuales` | `periodo varchar(7) UNIQUE, estado DEFAULT 'cerrado', cerrado_por`. Backend `audit_fiscal.py` (`GET/POST /audit-fiscal/cierres`). Sin UI. |

## 3. Backend — cobertura modelo/schema/route/migración por dominio + faltantes

Router central: `backend/app/api/router.py` (22 routers). Prefijo global `/api/v1` (`backend/app/main.py`).

| Dominio | Modelo (`models/`) | Schema (`schemas/`) | Route (prefijo + verbos) | Migración | Faltantes |
|---------|-------------------|---------------------|--------------------------|-----------|-----------|
| Auth | `usuarios.py:Usuario`, `refresh_token.py:RefreshToken` | `auth.py`, `usuario.py` | `auth.py` `/auth`: POST login/refresh/logout, GET me | `0001`, `0002_refresh_tokens` | Rol `gerente` referenciado en `audit_fiscal.py` sin existir en CHECK de `Usuarios` |
| Usuarios | `usuarios.py` | `usuario.py` | `usuarios.py` `/usuarios`: GET list/get, POST, PATCH, DELETE, PATCH `/{id}/password` | `0001` | Sin UI (ver §4). Sin schema/endpoint para `RefreshTokens` (solo interno, OK). |
| Auditoría | `audit.py:AuditLog` | `audit.py` | `audit.py` `/auditoria`: GET list/entidades/acciones/`{id}` (solo lectura, correcto) | `0001` + `0007` índices | Sin UI, sin servicio frontend, sin composable. |
| Audit-fiscal | `audit_fiscal.py` (3 clases) | — (respuestas ad-hoc) | `audit_fiscal.py` `/audit-fiscal`: GET+POST precio-versions/costo-versions/cierres | `0019_audit_fiscal_versioning` | POST exige rol `gerente` inexistente. Sin UI dedicada; solo lectura inline de precio en Ficha Técnica. |
| Clientes | `clientes.py` | `cliente.py` | `clientes.py` `/clientes`: CRUD completo (GET×2, POST, PUT, DELETE) | `0001`, `0009_extend_clientes_crm` | Ninguno en backend. |
| Insumos | `insumos.py:CategoriaInsumo/Insumo/CompraInsumo` | `categoria_insumo.py`, `insumo.py`, `compra_insumo.py` | `categorias_insumos.py` `/categorias-insumos` CRUD; `insumos.py` `/insumos` CRUD + PATCH; `compras_insumos.py` `/compras-insumos` POST + GET (list) | `0001`, `0016_insumos_bom`, `20260821_compras_wac_ux` | `compras-insumos` sin PUT/PATCH/DELETE (ajuste de compra imposible). `proveedor_id` sin FK. |
| Productos | `productos.py:TipoProducto/Producto/VarianteProducto/BomInsumo/BomProducto` | `producto.py`, `bom.py`, `costo.py` | `tipos_productos.py` `/tipos-producto` CRUD; `productos.py` `/productos` CRUD + variantes CRUD; `bom.py` `/productos/{id}/bom/insumos\|productos` CRUD; `costos.py` `GET /productos/{id}/costo` | `0001`, `0016`, `0020_productos_cabecera`, `0021_backfill_costo_insumos` | Ninguno crítico. `BOM_Productos` sin servicio frontend (ver §4). |
| Producción | `produccion.py:PedidoProduccion/PrendaConfeccionada` | `produccion.py` | `produccion.py` `/pedidos-produccion` y `/prendas-confeccionadas`: GET×2, POST, PATCH, PUT, DELETE c/u | `0017_pedidos_produccion`, `0018_prendas_listas` | PUT y PATCH duplicados (misma función con dos verbos, mantener uno). Enums de estado solo en Python, sin CHECK en DDL. |
| Ventas | `ventas.py:Venta/DetalleVenta/Devolucion/DevolucionItem` | `venta.py`, `devoluciones.py` | `ventas.py` `/ventas`: POST, GET, PATCH, PUT, DELETE, PATCH `/{id}/state`; `devoluciones.py` `/devoluciones`: POST, GET, PATCH `/{id}/state` | `0001`, `0003_ventas_canal_variante`, `0004_devolucion_finanzas_extension`, `0010_ventas_canal_pago`, `27d5c5b6fd80_es_regalo`, `98bda77bcd4d_reversal` | `Detalle_Ventas` y `Items_Devolucion` sin endpoint directo (diseño anidado, OK). `devoluciones` sin PUT/DELETE/GET-by-id. `metodo_pago` libre vs `maestros_metodos_pago`. |
| Finanzas | `finanzas.py` (5 clases) | `finanzas.py` | `finanzas.py` `/finanzas`: movimientos (POST×2, GET, DELETE, PATCH×2 incl. `/state`), socios CRUD, `POST /liquidaciones/crear` + GET×2 + PATCH estado + DELETE, anticipos GET/POST/PATCH×2/DELETE | `0004`, `0011`, `0012`, `0013` | `liquidacion_distribucion` sin CRUD directo (OK si siempre derivada). `liquidacion_id` varchar en movimientos rompe FK. Endpoint crear es `/finanzas/liquidaciones/crear` (no REST puro, pero consistente con `liquidaciones.ts`). |
| Maestros (8) | `maestros.py` (8 clases) | `maestros.py` | `maestros.py` `/maestros`: 7 recursos CRUD + `GET/PATCH /parametros-costeo` (singleton) | `0014`, `0015` | Ninguno. Mejor cobertura del backend. |
| Analíticos | — (agregaciones) | `analiticos.py` | `analiticos.py` `/analiticos`: resumen, ventas-mensuales, insumos-bajo-stock, margen-por-producto, top-productos, top-insumos, finanzas-mensuales | — | `resumen`, `margen-por-producto`, `top-insumos` sin consumidor frontend (ver §4). |
| Omisiones | `migracion.py` | `migracion.py` | `omisiones.py` `/omisiones`: GET filtrado, PATCH `/{id}` (solo admin) | `0005_migracion_omisiones` | Ninguno. |
| Observability | — | — | `observability.py` `/observability`: summary/metrics/alerts | — | Sin UI. Solo diagnóstico interno (OK). |

## 4. Frontend — cobertura vista/servicio/composable por dominio (MOCK vs REAL) + faltantes

Servicios (`src/services/api/`, 16 archivos) usan `client` de `src/api/client.ts` con `baseURL /api/v1`. Composables (`src/composables/`, 9 archivos). Router: `src/router/` monta 16 vistas (alias: `/insumos`→Inventario, `/recetas`→Productos, `/prendas`→PrendasListas, `/socias`→Finanzas).

| Dominio | Vista | Servicio | Composable | Estado REAL | Faltantes |
|---------|-------|----------|------------|-------------|-----------|
| Dashboard | `DashboardView.vue` | `analiticos.ts` (importado pero marcado `eslint-disable no-unused-vars`, sin llamada) | `useInsumos/useProduccion/useVentas` | REAL parcial (listas vía composables; analíticos del backend no consumidos) | Conectar `GET /analiticos/*` al dashboard; hoy los KPIs se calculan en cliente. |
| Clientes | `ClientesView.vue` | `clientes.ts` (CRUD) | `useClientes.ts` | REAL completo (switch `isMock`, modales `NuevoClienteModal`, `FichaTallasClienteModal`) | Ninguno. |
| Inventario/Insumos | `InventarioView.vue` | `insumos.ts` (CRUD+PATCH), `compras-insumos.ts` (create+list) | `useInsumos.ts` | REAL completo (modales `NuevoInsumoModal`, `CompraInsumoModal`, `SugerirOrdenModal`, `OrdenCompraProveedorModal`) | Editar/eliminar compra sin endpoint (coherente con backend). `ubicacion` libre vs `maestros_ubicaciones_taller`. |
| Productos/Ficha | `ProductosView.vue` + `FichaTecnicaModal.vue` | `productos.ts` (CRUD + tipos), `bom.ts` (BOM insumos + `getCostoProduccion`) | — (llamada directa al servicio) | REAL completo salvo historial: precio sugerido auto + semáforo + BOM inline OK | Tab Historial removido (pendiente conocido). `BOM_Productos` (combos) sin servicio/UI. `costo_versions` sin lectura UI (solo precio). |
| Producción | `ProduccionView.vue` | `pedidos-produccion.ts` (CRUD) | `useProduccion.ts` | REAL completo (modales `NuevoPedidoModal`, `DetallePedidoTallerModal`) | Ninguno. |
| Prendas | `PrendasListasView.vue` | `prendas.ts` (CRUD) | `usePrendas.ts` | REAL completo (`EtiquetaPrendaModal`) | `variante_id NOT NULL` impide prenda genérica; sin UI de variantes sueltas. |
| Ventas | `VentasView.vue` | `ventas.ts` (CRUD + anular) | `useVentas.ts` | REAL completo (modales `NuevaVentaModal`, `DetalleVentaModal`) | `metodo_pago` y `canal_venta` son strings libres en el payload, no selectores de maestros. |
| Devoluciones | `DevolucionesView.vue` | `devoluciones.ts` (SOLO `listDevoluciones`) | — | REAL parcial (lectura; create/PATCH state del backend sin consumidor) | P0: crear devolución y cambiar estado sin UI. `Items_Devolucion` sin UI. Vista mezcla constante mock (`'Ajuste a Medida (Garantía Atelier)'`). |
| Finanzas | `FinanzasView.vue` (tabs liquidaciones/socias/anticipos/simulador) | `socios.ts`, `liquidaciones.ts`, `anticipos.ts` | `useSocios.ts`, `useFinanzas.ts` | REAL completo en liquidaciones/anticipos/socios (modales `NuevaLiquidacionModal`, `DetalleLiquidacionModal`, `GestionSociasModal`, `NuevoAnticipoModal`) | Movimientos (`GET/PATCH/DELETE /finanzas/movimientos`) sin tab ni servicio frontend. `liquidacion_distribucion` visible solo vía detalle. `marcarAnticipoDescontado` con fallback confuso cuando `liquidacion_id` es null. |
| Maestros | `MaestrosView.vue` | `maestros.ts` (7 recursos + parámetros) | `useMaestros.ts` | REAL completo (única vista que ya pagina/sortea contra REAL) | `listCanales` con fallback estático `CANALES_VENTA` enmascara errores del backend. |
| Cotizador | `CotizadorView.vue` | `productos.ts`, `bom.ts` | — | REAL parcial (lista productos REAL + `costo real BOM` con botón "Usar costo real"; cálculo manual local) | Cálculo 100% local; no persiste cotización. Sección "Avíos, Cierres & Empaque" es texto, no `cierres_mensuales`. |
| Optimizador | `OptimizadorView.vue` | `insumos.ts` vía `useInsumos` | `useInsumos.ts` | REAL parcial (lista insumos REAL, optimización local) | Sin persistencia; sin llamada a analíticos. |
| Análisis | `AnalisisView.vue` | `useInsumos/useProduccion/usePrendas` + `productos.ts` | varios | REAL parcial (lee insumos/pedidos/prendas/productos REAL; todo el análisis es cómputo local) | Endpoints `/analiticos/margen-por-producto`, `/top-*` sin consumidor. |
| Omisiones | `OmisionesView.vue` | `omisiones.ts` (GET + PATCH implícito) | — | REAL completo (muestra `GET /api/v1/omisiones`) | PATCH resuelta exige admin; verificar que la UI lo exponga solo a admin. |
| Usuarios | `UsuariosView.vue` | — (ninguno; solo `useAuthStore`) | — | MOCK-only / estático (sin llamadas a `/usuarios`) | P1: CRUD de usuarios del backend sin UI. Ruta restringida a `admin` en router, pero sin contenido REAL. |
| Login | `LoginView.vue` | `useAuthStore` (`/auth/login`) | — | REAL (único flujo sin modo mock) | Ninguno. |
| Auditoría | — (no existe) | — | — | Inexistente | P0: `GET /auditoria` + `/audit-fiscal/*` + `/observability/*` sin vista, sin servicio, sin composable. |

## 5. Matriz DDL × Backend × Frontend (tabla: dominio/tabla | DDL | modelo | API | UI REAL | estado)

Leyenda: ✅ completo · ⚠️ parcial · ❌ faltante.

| Dominio / tabla | DDL | Modelo | API | UI REAL | Estado |
|-----------------|-----|--------|-----|---------|--------|
| `Usuarios` | ✅ | ✅ `models/usuarios.py` | ✅ `/usuarios` CRUD + password | ❌ `UsuariosView.vue` sin servicio | ⚠️ backend listo, UI pendiente |
| `RefreshTokens` | ✅ | ✅ `models/refresh_token.py` | ✅ interno `/auth/*` | — (no aplica) | ✅ correcto sin UI |
| `AuditLog` | ✅ | ✅ `models/audit.py` | ✅ `GET /auditoria` + filtros | ❌ sin vista/servicio | ❌ gap P0 |
| `Tipos_Producto` | ✅ | ✅ `models/productos.py` | ✅ `/tipos-producto` CRUD | ✅ `productos.ts` en ProductosView | ✅ |
| `Categorias_Insumos` | ✅ | ✅ `models/insumos.py` | ✅ `/categorias-insumos` CRUD | ⚠️ sin servicio dedicado (usa maestros/insumos) | ⚠️ wiring incompleto |
| `Insumos` | ✅ | ✅ | ✅ `/insumos` CRUD+PATCH | ✅ InventarioView + `useInsumos` | ✅ |
| `Compras_Insumos` | ✅ | ✅ | ⚠️ POST+GET (sin PUT/DELETE) | ✅ create+list vía `CompraInsumoModal` | ⚠️ sin editar/eliminar |
| `Productos` | ✅ | ✅ | ✅ `/productos` CRUD | ✅ ProductosView + Ficha Técnica | ✅ (menos historial) |
| `Variantes_Producto` | ✅ | ✅ | ✅ nested `/productos/{id}/variantes` | ✅ vía Ficha Técnica | ✅ |
| `BOM_Insumos` | ✅ | ✅ | ✅ `/productos/{id}/bom/insumos` CRUD | ✅ BOM inline en Ficha + `bom.ts` | ✅ |
| `BOM_Productos` | ✅ | ✅ | ✅ `/productos/{id}/bom/productos` CRUD | ❌ sin servicio ni UI | ❌ gap P1 (combos inoperables) |
| `precio_versions` | ✅ | ✅ `models/audit_fiscal.py` | ✅ `GET /audit-fiscal/precio-versions` | ⚠️ lectura inline en Ficha (`cargarHistorial`), tab removido | ⚠️ pendiente conocido |
| `costo_versions` | ✅ | ✅ | ✅ `GET /audit-fiscal/costo-versions` | ❌ sin lectura UI | ❌ gap P1 |
| `cierres_mensuales` | ✅ | ✅ | ✅ `GET+POST /audit-fiscal/cierres` | ❌ sin UI | ❌ gap P1 |
| `pedidos_produccion` | ✅ | ✅ | ✅ `/pedidos-produccion` full | ✅ ProduccionView + `useProduccion` | ✅ |
| `prendas_confeccionadas` | ✅ | ✅ | ✅ `/prendas-confeccionadas` full | ✅ PrendasListasView + `usePrendas` | ✅ |
| `Clientes` | ✅ | ✅ | ✅ `/clientes` CRUD | ✅ ClientesView + `useClientes` | ✅ |
| `Ventas` | ✅ | ✅ | ✅ `/ventas` + `/state` | ✅ VentasView + `useVentas` | ✅ (selectores libres, P2) |
| `Detalle_Ventas` | ✅ | ✅ | ✅ anidado en `POST /ventas` | ✅ vía `NuevaVentaModal`/`DetalleVentaModal` | ✅ por diseño |
| `Devoluciones` | ✅ | ✅ | ✅ POST+GET+PATCH state | ⚠️ solo list en `devoluciones.ts` | ⚠️ gap P0 (sin crear) |
| `Items_Devolucion` | ✅ | ✅ | ✅ anidado en POST | ❌ sin UI | ❌ gap P1 |
| `Movimientos_Financieros` | ✅ | ✅ | ✅ `/finanzas/movimientos` CRUD+state | ❌ sin tab/servicio | ❌ gap P1 |
| `Socios_Configuracion` | ✅ | ✅ | ✅ `/finanzas/socios` CRUD | ✅ tab Socias + `useSocios` | ✅ |
| `liquidaciones` | ✅ | ✅ | ✅ `/finanzas/liquidaciones[/crear]` | ✅ tab Liquidaciones + `useFinanzas` | ✅ |
| `liquidacion_distribucion` | ✅ | ✅ | ⚠️ embebida en `_liquidacion_response` | ✅ vía `DetalleLiquidacionModal` | ✅ por diseño |
| `anticipos` | ✅ | ✅ | ✅ `/finanzas/anticipos` + descuento/estado | ✅ tab Anticipos | ✅ |
| `maestros_proveedores` | ✅ | ✅ | ✅ `/maestros/proveedores` | ✅ MaestrosView | ✅ |
| `maestros_categorias_coleccion` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `maestros_ubicaciones_taller` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `maestros_canales_venta` | ✅ | ✅ | ✅ | ⚠️ con fallback estático | ⚠️ enmascara errores |
| `maestros_metodos_pago` | ✅ | ✅ | ✅ | ✅ | ✅ (desconectado de Ventas) |
| `maestros_tallas_estandar` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `maestros_productos_sin_talla` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `maestros_parametros_costeo` | ✅ | ✅ | ✅ GET+PATCH singleton | ✅ | ✅ |
| `Migracion_Omisiones` | ✅ | ✅ | ✅ `GET /omisiones` + PATCH | ✅ OmisionesView | ✅ |
| Analíticos (sin tabla) | — | — | ✅ 7 endpoints `/analiticos/*` | ⚠️ 2/7 consumidos (`ventas-mensuales`, `insumos-bajo-stock`, `finanzas-mensuales`; `resumen` parcial) | ⚠️ dashboard calcula local |
| Observability (sin tabla) | — | — | ✅ `/observability/*` | ❌ sin UI | ✅ aceptable (interno) |

## 6. Gaps y riesgos priorizados (P0 crítico / P1 importante / P2 mejora, con evidencia de archivo)

### P0 — Crítico (bloquea operación real o integridad)

- **P0-1. Devoluciones sin crear en frontend.** Backend `backend/app/api/routes/devoluciones.py` (POST + PATCH state) sin consumidor: `src/services/api/devoluciones.ts` solo exporta `listDevoluciones`. `DevolucionesView.vue` solo lee. Evidencia: `devoluciones.ts:1-14`, `DevolucionesView.vue` (`cargarDevolucionesReales`, `devolucionesDisplay`).
- **P0-2. Auditoría sin UI.** `GET /auditoria` (`backend/app/api/routes/audit.py`: list/entidades/acciones/`{id}`) no tiene servicio, composable ni vista. Sin trazabilidad visible, `AuditLog` es escritura ciega. Evidencia: grep `auditoria|AuditLog` en `src/**` sin resultados (solo "cierres" textiles en Cotizador).
- **P0-3. Rol `gerente` inexistente bloquea POST fiscal.** `backend/app/api/routes/audit_fiscal.py` exige `require_roles("admin","gerente")`, pero `DDL.sql:443` (`ck_usuarios_rol`) y `models/usuarios.py` solo permiten `admin/operador/consulta`. Todo `POST /audit-fiscal/*` devuelve 403 siempre.

### P1 — Importante (función degradada o dato inconsistente)

- **P1-1. `BOM_Productos` (combos) inoperable en UI.** Backend completo (`bom.py`, 4 endpoints `bom/productos`), modelo `BomProducto`, schema `bom.py`. Sin servicio en `src/services/api/bom.ts` (solo BOM insumos + costo) ni UI en `ProductosView.vue`. Los combos existen en DB pero no se pueden armar.
- **P1-2. Movimientos financieros sin UI.** `finanzas.py` expone `GET/PATCH/DELETE /finanzas/movimientos` (+ `/state`), pero `FinanzasView.vue` solo tiene tabs liquidaciones/socias/anticipos/simulador y `useFinanzas.ts` no lista movimientos. Gastos/inversiones/retiros fuera de liquidaciones quedan invisibles.
- **P1-3. Historial de versiones incompleto (pendiente conocido).** `FichaTecnicaModal.vue: cargarHistorial()` lee `GET /audit-fiscal/precio-versions?producto_id=` inline, pero el tab Historial está removido y `costo_versions` + `cierres` no se leen en ningún lado. Riesgo de regresión: reponer el tab sin paginación rompe el build (motivo original de la remoción).
- **P1-4. `Movimientos_Financieros.liquidacion_id` varchar sin FK.** `DDL.sql:792` (`liquidacion_id varchar(12)`) vs `liquidaciones.id integer`: el UNIQUE parcial `uq_liquidacion` no sustituye la FK. Conciliación movimiento↔liquidación solo por `codigo` a mano.
- **P1-5. `Compras_Insumos.proveedor_id` sin FK.** `DDL.sql:1122` + índice `ix_Compras_Insumos_proveedor_id` pero sin `REFERENCES maestros_proveedores(id)`. Compras huérfanas posibles; `OrdenCompraProveedorModal.vue` no tiene garantía referencial.
- **P1-6. `Ventas.canal_venta` / `metodo_pago` desconectados de maestros.** CHECK `ck_ventas_canal_venta` (`DDL.sql:902`: 5 valores fijos) vs `maestros_canales_venta` (CRUD independiente); `metodo_pago varchar(50)` libre vs `maestros_metodos_pago`. Crear un canal/método en Maestros no lo habilita en Ventas.
- **P1-7. `UsuariosView.vue` sin cableado REAL.** Solo `useAuthStore`, cero llamadas a `/usuarios` (`backend/app/api/routes/usuarios.py` CRUD + password). Gestión de usuarios admin inoperante pese a ruta protegida `roles:['admin']`.
- **P1-8. `Items_Devolucion` sin UI y `devoluciones` sin PUT/DELETE/GET-by-id.** El detalle de qué prenda/talla vuelve no se registra en UI; correcciones solo vía DB.
- **P1-9. ` liquidaciones.ts` usa `POST /finanzas/liquidaciones/crear` (no REST) + `descontarAnticipo` frágil.** El crear es correcto contra el backend (`finanzas.py: "/liquidaciones/crear"`), pero `FinanzasView.vue: marcarAnticipoDescontado` llama `descontarAnticipo(id, liquidacion_id ?? 0)` y si es null hace fallback a `transitionAnticipo` — doble escritura potencial.

### P2 — Mejora (deuda técnica, UX, robustez)

- **P2-1. Analíticos a medio consumir.** `src/services/api/analiticos.ts` llama 5 endpoints, pero `DashboardView.vue` lo importa como unused (`eslint-disable`) y `AnalisisView/Optimizador/Cotizador` computan local. `resumen`, `margen-por-producto`, `top-*` sin consumidor.
- **P2-2. Fallback `CANALES_VENTA` enmascara caídas.** `maestros.ts:205-211 listCanales` (`tryFetch` con fallback estático) devuelve datos falsos ante error de red; resto de maestros propaga el error. Unificar criterio.
- **P2-3. PUT+PATCH duplicados en producción.** `produccion.py` registra ambos verbos para el mismo update en prendas y pedidos. Elegir PATCH (parcial) y deprecar PUT.
- **P2-4. Enums de producción/prendas solo en Python.** `pedidos_produccion.estado/prioridad`, `prendas.estado` sin CHECK en DDL → estados inválidos entran por SQL directo.
- **P2-5. `Insumos.ubicacion` y `prendas.ubicacion` varchar libre.** No referencian `maestros_ubicaciones_taller(codigo LIKE 'UB-%')`; el maestro de ubicaciones es decorativo.
- **P2-6. Cotizador/Optimizador sin persistencia.** `CotizadorView.vue` ("Usar costo real" ajusta CIF local), `OptimizadorView.vue` y `AnalisisView.vue` (cómputo local sobre listas REAL) no guardan resultados. Aceptable como herramienta, documentarlo.
- **P2-7. `prendas_confeccionadas.variante_id NOT NULL`.** Impide stock de prenda genérica o sin talla (`maestros_productos_sin_talla` queda como catálogo aislado sin puente a `Productos`/`prendas`).
- **P2-8. Composables faltantes por dominio.** Sin `useProductos/useBom/useDevoluciones/useOmisiones/useAnaliticos`: `ProductosView`, `DevolucionesView`, `OmisionesView`, `CotizadorView` llaman servicios directamente, patrón inconsistente con clientes/ventas/insumos/socios/finanzas.

## 7. Roadmap sugerido (próximos 3-5 pasos concretos)

1. **Cerrar P0-3 + P0-1 (1–2 días).** Agregar `CHECK (rol IN ('admin','operador','consulta','gerente'))` o cambiar `audit_fiscal.py` a `require_roles("admin")` (migración `0022`). Implementar `createDevolucion + transitionDevolucion` en `src/services/api/devoluciones.ts` y botón "Nueva devolución" en `DevolucionesView.vue` contra `POST /devoluciones`.
2. **Auditoría mínima visible (2–3 días).** Crear `src/services/api/auditoria.ts` (`GET /auditoria`, `/entidades`, `/acciones`), `AuditoriaView.vue` solo-lectura con filtros entidad/acción/fechas (reutilizar patrón `OmisionesView.vue`), ruta `/auditoria` rol `admin|operador`. Desbloquea P0-2 sin abrir escritura.
3. **Reponer Historial fiscal paginado (2 días).** Reintroducir tab Historial en `FichaTecnicaModal.vue` con paginación (`limit/offset`) y dos subtabs (precio/costo) contra `/audit-fiscal/precio-versions` y `/costo-versions`; no cargar sin `recetaId`. Cierra P1-3 y el pendiente conocido del build.
4. **Integridad referencial + Ventas↔Maestros (3–4 días).** Migración `0023`: FK `Compras_Insumos.proveedor_id → maestros_proveedores(id)`, columna `Ventas.canal_venta_id → maestros_canales_venta(id)` + `metodo_pago_id → maestros_metodos_pago(id)` (mantener strings legacy como fallback), FK o vista de conciliación para `Movimientos.liquidacion_id`. Cambiar `VentasView.vue` a selectores de maestros. Cierra P1-4/5/6.
5. **Movimientos + Usuarios + Combos (3–5 días).** Tab Movimientos en `FinanzasView.vue` (servicio `finanzas/movimientos`), CRUD en `UsuariosView.vue` contra `/usuarios` (solo admin), servicio `bomProductos` en `bom.ts` + sección Combos en `ProductosView.vue`. Cierra P1-1/2/7 y deja el frontend en ~90% REAL.

---
*Generado 2026-09-03 desde `DDL.sql`, `backend/app/{models,schemas,api/routes}`, `backend/alembic/versions/`, `src/{views,services/api,composables}`, `src/router/` y `git log (b3df143)`. Sin consultas a memoria previa (contexto provisto por el orquestador). Skill aplicada: `cognitive-doc-design` (respuesta primero, tablas sobre prosa, secciones señalizadas).*

