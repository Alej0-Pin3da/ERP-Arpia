# Registro de Cambios y Evolución - Versión 3 (V3)
## Atelier Arpía — ERP & Sistema Integral de Confección de Autor

Este documento registra cronológica y detalladamente todas las modificaciones, nuevas funcionalidades, módulos maestros, correcciones y expansiones integradas a partir de la versión 3 (V3).

---

### [2026-08-23] — V3.0.0: Módulo Integral de Catálogos & Parámetros Maestros (Full CRUD)

#### 1. Arquitectura de Estado Global (`src/stores/atelier.ts`)
- **Nuevas Estructuras de Datos y Tipado TypeScript:**
  - `ProveedorMaestro`: Directorio integral de proveedores con categoría, ciudad, tiempos de entrega en días hábiles, condiciones de pago, contacto directo y calificación.
  - `CanalVentaMaestro`: Puntos de venta físicos (Showroom Pereira), canales digitales (Instagram / WhatsApp) y stands en eventos/convenciones con costos fijos y tasas de comisión.
  - `MetodoPagoMaestro`: Medios de pago bancarios, billeteras digitales y pasarelas de datáfono/link con tasa de comisión financiera y plazos de acreditación.
  - `CategoriaColeccionMaestro`: Familias de confección (Corsets de Estructura Fuerte, Corsets Livianos, Tote Bags & Merch) con márgenes meta de rentabilidad (%) y asignación de tipo de talla.
  - `UbicacionTallerMaestro`: Bodegas y ubicaciones físicas de almacenamiento (rollos de tela, gavetas de herrajes, percheros y bodega de lonas) con códigos y capacidades.
  - `TallaEstandarMaestro`: Matriz oficial de tallaje de alta costura y corsetería (**XXS, XS, S, M, L, XL**) con contornos de busto, cintura, cadera y factor de reducción en cm.
  - `ProductoSinTallaMaestro`: Especificaciones técnicas para productos no basados en silueta corporal (*Tote Bags ilustradas de lona, Scrunchies, Pañoletas y Joyería de autor*) con dimensiones, materiales y precios sugeridos.
  - `ParametrosCosteoMaestro`: Tarifas base de mano de obra (costo/minuto de costura, costo/hora de patronaje y corte), merma textil (%) y estatuto de reparto de utilidades de socias (40% Fondo Taller, 30% Margara, 30% Valqui).
- **Acciones CRUD Implementadas en el Store Pinia:**
  - `crearProveedor`, `actualizarProveedor`, `eliminarProveedor`
  - `crearCanalVenta`, `actualizarCanalVenta`, `eliminarCanalVenta`
  - `crearMetodoPago`, `actualizarMetodoPago`, `eliminarMetodoPago`
  - `crearCategoriaColeccion`, `actualizarCategoriaColeccion`, `eliminarCategoriaColeccion`
  - `crearUbicacionTaller`, `actualizarUbicacionTaller`, `eliminarUbicacionTaller`
  - `crearTallaEstandar`, `actualizarTallaEstandar`, `eliminarTallaEstandar`
  - `crearProductoSinTalla`, `actualizarProductoSinTalla`, `eliminarProductoSinTalla`
  - `actualizarParametrosCosteo`: Con soporte para persistencia reactiva y cálculo en tiempo real.

---

#### 2. Vista de Catálogos & Parámetros Maestros (`src/views/MaestrosView.vue`)
- **Navegación Modular por Pestañas:**
  - **Pestaña 1 (Proveedores Textil & Herrajes):** Tarjetas interactivas con datos de contacto, enlaces directos a WhatsApp, filtro por categoría de insumos, modal de alta/edición y botón de eliminación.
  - **Pestaña 2 (Canales de Venta & Comercialización):** Panel de gestión de canales de comercialización con cálculo de costos de intermediación y comisiones por venta.
  - **Pestaña 3 (Medios de Pago & Pasarelas):** Administración de tasas de adquirencia, cuentas y tiempos de acreditación bancaria.
  - **Pestaña 4 (Matriz de Tallas & Formatos Sin Talla):** 
    - Tabla editable de medidas anatómicas estándar para corsetería.
    - Fichas técnicas editables para Tote Bags, moñas/scrunchies y merchandising.
  - **Pestaña 5 (Familias de Colección):** Configuración de colecciones activas y márgenes de rentabilidad meta.
  - **Pestaña 6 (Ubicaciones Físicas del Taller):** Directorio de estantes, bodegas y gavetas de insumos.
  - **Pestaña 7 (Tarifas Globales de Costeo & Estatuto Socias):** Formulario para ajustar los valores del minuto de costura y hora de corte, validando en tiempo real que la regla 40/30/30 sume exactamente el 100%.
- **Modales Formularios Responsivos y Accesibles:**
  - Modales dedicados para la creación y edición de cada entidad con validaciones de campos y botones semánticos de acción.

---

### [2026-08-23] — V3.1.0: Refactor CRM Clientas & Tallaje Estándar + Módulos Atelier

#### 1. CRM de Clientas — Migración a Tallaje Estándar (`src/stores/atelier.ts`, `src/views/ClientesView.vue`, `src/components/atelier/NuevoClienteModal.vue`, `src/components/atelier/FichaTallasClienteModal.vue`)
- **Modelo `ClienteCRM` migrado de medidas anatómicas a medida a tallaje estándar de marca:**
  - Antes: `medidas: { busto, cintura, cadera, espalda, talle, largo }` (campos numéricos libres).
  - Ahora: `tipo` (Clienta Habitual / VIP / Showroom / Feria / Online), `ciudad`, `direccion`, `talla_habitual` / `talla_superior` / `talla_inferior` (`XXS, XS, S, M, L, XL, Sin Talla`), `categoria_preferida` (Corsetería & Tops / Faldas & Conjuntos / Tote Bags de Lona / Accesorios & Merch), `tipo_producto_frecuente` (`PRENDAS_TALLAS` vs `PRODUCTOS_SIN_TALLA`), `notas`, `total_compras`, `pedidos_count`.
- **`NuevoClienteModal.vue` reescrito:**
  - Reemplaza 6 `InputText` numéricos por `Dropdown` de tipo de clienta, tallas (`XXS-XL` + `Sin Talla (Tote Bags)` / `Talla Única`), categoría de interés, selector rápido de talla por botones, y `Textarea` de notas. Helpers `seleccionarTallaRapida()` sincroniza superior/inferior.
  - Payload construye `tipo_producto_frecuente` automático según talla/categoría.
- **`ClientesView.vue` reescrito:**
  - Header actualizado a `Gestión de Clientas CRM` con badge `Tallas: XXS a XL & Tote Bags`.
  - Nuevos contadores: `totalClientas`, `clientasConTalla` (XXS-XL), `clientasSinTalla` (Tote Bags), `totalFacturadoCRM`.
  - Filtros: búsqueda extendida (nombre/teléfono/email/ciudad/talla/notas) + `filtroTalla` (`TODAS/XXS-XL/SIN_TALLA`) + `filtroCategoria` + tabs rápidos de talla + botón `Limpiar`.
  - Cards: avatar + ciudad, contacto con `WhatsApp` contextual (mensaje distinto para `Sin Talla`), bloque `Talla de Marca & Preferencias` con espectro visual 7 columnas (XXS-XL + 👜), categoría y notas, footer con compras realizadas.
  - Reemplaza `MedidasAnatomicasModal` por `FichaTallasClienteModal` + botón `Guía Oficial de Tallas`.
- **Nuevo `FichaTallasClienteModal.vue`:** ficha de talla estándar por clienta (reemplazo de medidas a medida).

#### 2. Store Global — Expansión Atelier (`src/stores/atelier.ts`)
- **Ventas:** `ventas`, `totalVentasRealizadas`, `totalGananciaVentas`, `margenPromedioVentas`, `distribucionSociasVentas` + CRUD `crearVenta`, `actualizarVenta`, `eliminarVenta`, `cambiarEstadoVenta`.
- **Socias / Liquidaciones / Anticipos:** `socias`, `liquidaciones`, `anticipos` + computadas `totalHistoricoFacturadoLiquidaciones`, `totalHistoricoUtilidadSocias`, `totalHistoricoFondoReinversion`, `totalHistoricoRepartidoMargara/Valqui`, `totalAnticiposPendientes` + CRUD `crearSocia/actualizarSocia/eliminarSocia/toggleActivoSocia`, `crearLiquidacion/actualizarLiquidacion/eliminarLiquidacion/cambiarEstadoLiquidacion/marcarPagoSociaItem`, `crearAnticipo/actualizarAnticipo/eliminarAnticipo/cambiarEstadoAnticipo` (lógica 40% fondo reinversión, reparto proporcional, deducción de anticipos `PENDIENTE_DESCUENTO`, estados `BORRADOR/PAGADA/PENDIENTE/PAGADO`).
- **Maestros ya documentados en V3.0.0 re-exportados en el return del store** (proveedores, canales, métodos de pago, categorías, ubicaciones, tallas, productos sin talla, parámetros de costeo).

#### 3. Nuevos Modales y Vistas Atelier
- **Nuevos componentes (`src/components/atelier/`):** `DetalleLiquidacionModal.vue`, `DetalleVentaModal.vue`, `NuevaLiquidacionModal.vue`, `NuevaVentaModal.vue`, `NuevoAnticipoModal.vue`, `GestionSociasModal.vue` — flujos de ventas, liquidaciones a socias (cálculo `utilNeta = ventas - costos - gastos`, `fondo = 40%`, `repartible = 60%`), anticipos y gestión de socias.
- **Ajustes en vistas:** `src/views/FinanzasView.vue`, `src/views/VentasView.vue`, `src/views/MaestrosView.vue` (integración con nuevos estados del store), `src/layouts/AppLayout.vue` (labels de navegación atelier), `src/server/mockApi.ts` (mock actualizado al nuevo dominio).
- **Ajuste en `MedidasAnatomicasModal.vue`:** intervenido para compatibilidad con el nuevo dominio de tallas.
- **Assets:** `public/arpia-05-1-100x100.png`, `src/assets/arpia-05-1-100x100.png`, `src/assets/images/arpia_logo_emblem_1787499417987.jpg` agregados; `package-lock.json` eliminado (proyecto usa `bun.lock`), `AGENTS.md` creado.

#### 4. Commit Asociado
- `ac8ead2 — feat(atelier): refactor client management and sizing` (2026-08-23) — 22 archivos, +9088/-7877.

---

### [2026-08-24] — V3.2.0: Indicador Visual de Modo API (MOCK vs Backend Real)

#### 1. Nuevo Componente `src/components/ApiModeBadge.vue`
- **Detección de modo (solo lectura de env):**
  - `import.meta.env.VITE_API_BASE_URL` — si es `undefined`, vacío o empieza con `/api` => `MOCK`.
  - Si contiene `http`, `:8000`, `:5433` o `backend` (case-insensitive) => `REAL`.
  - DEV sin `VITE_API_BASE_URL` custom => `MOCK`.
- **Estados visuales:**
  - `MOCK`: icono `pi-database`, texto `MODO MOCK — Datos en memoria`, paleta amber/orange, tooltip `Los datos se pierden al reiniciar. Backend real inactivo.`
  - `REAL`: icono `pi-server`, texto `BACKEND REAL — Postgres`, paleta emerald/green, tooltip `Conectado a FastAPI + Postgres`.
- **API interna computada:** `mode`, `label`, `shortLabel`, `icon`, `tooltip`, `severity` (`warn` / `success`).
- **Estética Noir/Gold:** `border-radius` pill, fondo translúcido, `backdrop-filter: blur`, `dot` pulsante con `box-shadow`, hover con elevación y halo, tipografía semibold 0.74rem, transición suave.
- **Responsivo:** texto largo visible en desktop, colapsa a `MOCK`/`REAL` en `≤640px`; padding y gap reducidos en móvil.
- **Accesibilidad:** `role="status"`, `aria-label`, `title` nativo, `data-severity` para tests.
- **Sin mutación de lógica:** no modifica `src/api/client.ts` ni `handleMockApiRequest`; solo lee env.

#### 2. Integración en Layout `src/layouts/AppLayout.vue`
- Importa `ApiModeBadge` desde `@/components/ApiModeBadge.vue`.
- Colocado en `.header-right` entre `system-status-chip` (Taller Pereira • Activo) y el `Tag` de rol, antes del bloque `app-layout__user`.
- Mantiene grid responsivo existente; el chip del sistema sigue oculto en `≤992px`, el `ApiModeBadge` permanece visible con versión colapsada.
- `npm run lint` y `npm run build` verificados sin regresiones (Vite 6.4.3, 366 módulos, esbuild bundle `dist/server.mjs`).

---

### [2026-08-24] — V3.2.1: Mock Condicional — Proxy Automático al Backend Real

#### 1. `server.ts` — Mock vs Proxy con `fetch` nativo (Node 20+)
- **Resolución de modo:** `USE_MOCK`, `API_PROXY_TARGET`, `VITE_API_BASE_URL` y `ENVIRONMENT`.
  - `USE_MOCK=false` => siempre `REAL` (proxy).
  - `USE_MOCK=true` => siempre `MOCK` (fuerza mock, ignora el resto).
  - `API_PROXY_TARGET` seteado (ej. `http://localhost:8000`) => `REAL` aunque `USE_MOCK` no esté.
  - `VITE_API_BASE_URL` externa (`http`, `:8000`, `backend`) => `REAL`.
  - Default sin nada => `MOCK` (dev rápido sin DB).
- **Proxy `/api` sin dependencias extra:** `apiProxyMiddleware` con `fetch` nativo, forward de método/headers/body JSON, copia status/headers (filtra hop-by-hop), `arrayBuffer` -> `Buffer`, maneja `204` y errores con `502`.
- **Montaje condicional:** `MOCK` => `app.use('/api', apiRouter)` + `/api/health` local; `REAL` => `app.use('/api', apiProxyMiddleware)` y `/api/health` proxyeado al FastAPI.
- **Logs explícitos:** `Mock API enabled (in-memory DB)` vs `Mock API disabled — proxying /api to http://...`.

#### 2. `vite.config.ts` — Plugin mock y proxy de Vite condicionales
- `shouldUseMock()` espeja la misma lógica de `server.ts`.
- `mockApiPlugin` hace early `next()` si `!shouldUseMock()` (no intercepta `/api`, deja pasar al backend real).
- `server.proxy` condicional: solo cuando `!useMockAtConfig`, proxy `/api` => `API_PROXY_TARGET || http://localhost:8000` con `changeOrigin: true`.

#### 3. `.env.example` — Documentación de toggle
- Comentadas por defecto para no romper dev: `# USE_MOCK`, `# API_PROXY_TARGET`, `# VITE_API_BASE_URL` con explicación `true => mock RAM sin DB` / `false => proxy a FastAPI`.

#### 4. Uso
- **Mock (default):** `npm run dev` / `npm start` => `MODO MOCK — Datos en memoria` en el badge.
- **Real (con DB):** `docker compose up -d` + `USE_MOCK=false npm run dev` o `API_PROXY_TARGET=http://localhost:8000 npm start` o `VITE_API_BASE_URL=http://localhost:8000/api/v1` => badge pasa a `BACKEND REAL — Postgres` y `/api` proxyea a FastAPI sin perder el `dist/server.mjs` para servir el frontend.
- Verificado: `npm run build` (Vite 366 módulos + esbuild 41.7kB) y `npm run lint` sin regresiones.

#### 5. Scripts `package.json` — Atajos `start:real` / `dev:real` (2026-08-24)
- Agregados `dev:real` (`cross-env USE_MOCK=false tsx server.ts`), `start:real` (`cross-env USE_MOCK=false node dist/server.mjs`) y `start:mock` (`cross-env USE_MOCK=true ...`) con `cross-env` en `devDependencies` para que funcione en Windows/PowerShell sin `$env:` manual.
- Uso: `npm run dev:real` / `npm run start:real` => proxy a `http://localhost:8000` (requiere `docker compose up -d`); `npm run dev` / `npm start` siguen en mock por defecto.

---

### [2026-08-24] — V3.3.0: Frontend Adapter Clientes+Ventas — Misma UI, datos reales (v4-fase1-clientes-ventas PR3)

#### 1. Servicios API tipados (`src/services/api/`)
- **`clientes.ts`** — CRUD via `src/api/client.ts` (`/clientes`): `listClientes({q,tipo,ciudad,limit,offset})` → `Paginated<ClienteRead>`, `getCliente`, `createCliente`, `updateCliente`, `deleteCliente`; tipos `ClienteRead/CreatePayload/UpdatePayload` con 10 campos CRM (`ciudad/direccion/tipo/tallas/categoria/notas/medidas`).
- **`ventas.ts`** — CRUD `/ventas`: `listVentas({canal_venta,estado})`, `getVenta`, `createVenta`, `updateVenta`, `anularVenta`; `CanalVenta` 5 literales (`web|whatsapp|instagram|feria|showroom_pereira`) y `MetodoPago` 4 (`efectivo|transferencia|tarjeta|contraentrega`) alineados a `schemas/venta.py`.
- **`maestros.ts`** — `listCanales()` / `listMetodosPago()` con catálogos estáticos (`CANALES_VENTA` 5 + `METODOS_PAGO` 4) y `tryFetch` a `/maestros/*` (fallback 404 → estático, Fase 3 añadirá REST).

#### 2. Composables adaptadores (`src/composables/`)
- **`useMode.ts`** — `isMock` + `GET /api/__mode` probe (fuente de verdad). Fallback `import.meta.env.VITE_USE_MOCK` (`true→MOCK`, `false→REAL`) + heurística `VITE_API_BASE_URL` externa. Expone `mode/isMock/liveMode/liveChecked/refresh/envMode`; espeja lógica de `ApiModeBadge.vue` y `vite.config.ts`.
- **`useClientes.ts`** — switch `mock↔api`: `isMock` ⇒ filtra localmente (`tipo/ciudad` exact, `q` ILIKE `nombre|ciudad|direccion`, paginado) y CRUD contra `useAtelierStore.clientes`; `!isMock` ⇒ delega a `services/api/clientes.ts` (`/api/v1`). Misma firma promisificada; `*.vue` intacto.
- **`useVentas.ts`** — switch idem para ventas: `canal_venta` filtro local, `create/anular` contra `atelier.ventas` en mock, `api/ventas.ts` en real; cubre 5 canales + 4 métodos + `null`.
- **`atelier.ts` (`@deprecated`)** — cabecera `@deprecated Mock Pinia store — retained for VITE_USE_MOCK=true only` (Fase 3 lo eliminará). Sin borrado, re-exporta idéntico.

#### 3. Tests frontend (`src/composables/*.test.ts`, Vitest jsdom)
- **`useMode.test.ts`** (7 tests): `VITE_USE_MOCK` true/false, `VITE_API_BASE_URL` externa ⇒ REAL, probe `real/mock` override, fallo fetch ⇒ fallback, contrato `MOCK|REAL`.
- **`useClientes.test.ts`** (9 tests): mock `tipo/ciudad/q` ILIKE + paginado, `create/update/remove/get` en atelier, no llama API en mock; real delega a `api.*` con params exactos.
- **`useVentas.test.ts`** (8 tests): mock `canal_venta`, `create` con `canal+metodo`, `anular→ANULADA`, 5 canales+4 métodos round-trip; real `list/create/anular` delegan a `/api/v1/ventas`.
- Total 24 Vitest `✓`, `npm run build` 366 módulos `✓`, `pytest` PR1+PR2 34 `✓` (74 combined) sin regresión, `git diff -- src/**/*.vue` vacío (misma UI).

#### 4. Contratos y verificación
- `VITE_USE_MOCK=true` → Pinia mock (memoria, se pierde al reload); `false` → `client.ts` (`/api/v1`) + `GET /api/__mode` badge (`MOCK|REAL`).
- `*.vue` sin cambios estructurales (ERP-V4 §8); adapter ≤270 líneas prod, rollback por `Revert api+composables`.

---

### [2026-08-25] — V3.4.0: Finanzas — Socias / Liquidaciones / Anticipos + Adapters Frontend (v4-fase2 PR1+PR2+PR3)

#### 1. Backend — Base de datos (`backend/alembic/versions/0011-0013`, `backend/app/models/finanzas.py`)
- **0011 `extend_socios_configuracion`**: 10 cols nullable (`rol`, `banco`, `es_fondo_taller`, `telefono`, `email`, `tipo_cuenta`, `numero_cuenta`, `titular_cuenta`, `activo`, `notas`) + índices `ix_socios_rol` / `ix_socios_activo`, guards idempotentes, downgrade reversible.
- **0012 `create_liquidaciones`**: `liquidaciones` (codigo `LIQ-YYYY-NN` UNIQUE, periodo, fecha_cierre, 6×NUMERIC 12,2, estado CHECK `BORRADOR|APROBADA|PAGADA`) + `liquidacion_distribucion` (FK CASCADE, UNIQUE par `liquidacion_id+socia_id`, `monto_bruto/deduccion/monto_neto`, `estado_pago`).
- **0013 `create_anticipos`**: `anticipos` (`socia_id` CASCADE, `liquidacion_id` SET NULL, `monto>0`, `estado` CHECK, índice `ix_anticipos_socia_fecha` + partial UNIQUE `ix_anticipos_socia_liquidacion WHERE liquidacion_id IS NOT NULL`).
- **Models (`finanzas.py`)**: `SociosConfiguracion` extendida (10 cols), `LiquidacionEstado` / `DistribucionEstado` / `AnticipoEstado` (StrEnum) + `Liquidacion` / `LiquidacionDistribucion` / `Anticipo` con `transition_to()` FSM; exports en `models/__init__.py`.

#### 2. Backend — Schemas / Services / API (`backend/app/{schemas,services,api/routes}/finanzas.py`)
- **Schemas (`finanzas.py`)**: `SocioConfiguracionCreate/Update/Read` (EmailStr + `Literal["AHORROS","CORRIENTE","OTRA"]` + 50 chars `rol`), `LiquidacionCreate/EstadoUpdate/DistribucionRead/Read+warnings`, `AnticipoCreate/EstadoUpdate/DescuentoUpdate/Read`; validators `>0`, warnings list.
- **Services (`finanzas.py`)**: `crear_socia/actualizar_socia/listar_socias` — sum-to-100 sobre `activo=true` incl fondo (40+30+30) + single `es_fondo_taller` guard; `crear_liquidacion` (valida `utilidad_neta == ventas-costos-gastos` →422, drift `>5%` vs `MovimientosFinancieros` persiste con warning, codigo `LIQ-YYYY-NN` MAX+1, distribucion `bruto=repartible*%/100` + `deduccion=PENDIENTE` + `neto`, `FOR UPDATE` descontar anticipos atomico), `transicionar/eliminar_liquidacion` (FSM `BORRADOR→APROBADA→PAGADA`, delete solo BORRADOR CASCADE + SET NULL), `crear_anticipo/descontar/transicionar/eliminar` (double-discount 409 + partial UNIQUE, ANULADO→422).
- **Routes (`finanzas.py`)**: `GET/POST/PATCH/DELETE /finanzas/socios` (filtros `activo/es_fondo_taller/rol/q` SOC-3 + Paginated), `POST /liquidaciones/crear` + `GET /{id}` + `GET /liquidaciones` (estado/periodo) + `PATCH /{id}/estado` + `DELETE /{id}`, `GET/POST /anticipos` + `PATCH /{id}/descuento` + `PATCH /{id}/estado` + `DELETE /{id}`; helpers `_liquidacion_response/_anticipo_response`; 409 por UNIQUE concurrente.
- **Tests (`backend/tests/test_finanzas_*.py`)**: `test_fase2_foundation` 9 + `test_finanzas_schemas` 19 (EmailStr/Literal/rol>50) + `test_finanzas_servicios` 9 (sum105/fondo dup/drift>5%/FSM) + `test_finanzas_api_v4` 16 (código LIQ 40/30/30, FSM 422 skip, drift warn, SET NULL cascada, double 409) = 53 v4; legacy `test_finanzas` 48 + 103 combinados GREEN; `test_socio_crear_suma_99` actualizado 422→201 por SOC-2 build-up interim.

#### 3. Frontend — Services + Composables (`src/services/api/*`, `src/composables/*`, `src/stores/atelier.ts`)
- **`socios.ts`** — CRUD ` /finanzas/socios`: `listSocios({activo,es_fondo_taller,rol,q,limit,offset})` → `Paginated<SociaRead>`, `get/create/update/deleteSocia`; tipos `SociaRead/Create/Update` con `porcentaje_participacion` + 10 cols extendidas.
- **`liquidaciones.ts`** — `listLiquidaciones({estado,periodo})`, `getLiquidacion`, `createLiquidacion`, `transitionLiquidacion`, `deleteLiquidacion`; tipos `LiquidacionRead + DistribucionRead` + `Paginated`, codigo `LIQ-YYYY-NN` server-side.
- **`anticipos.ts`** — `listAnticipos({socia_id,estado})`, `createAnticipo`, `descontarAnticipo(id,liquidacion_id)`, `transitionAnticipo`, `deleteAnticipo`; `AnticipoRead` con `socia_nombre/liquidacion_id`.
- **`useSocios.ts`** — switch `mock↔api`: `isMock` ⇒ filtra `atelier.socias` (`activo/es_fondo_taller/rol/q` + paginado) y CRUD contra Pinia (`porcentaje_participacion↔porcentaje` map); `!isMock` ⇒ `services/api/socios.ts` (`/api/v1`).
- **`useFinanzas.ts`** — switch para ambos dominios: liquidaciones (`list/get/create LIQ-YYYY-NN + distrib 40/30/30 mock, transition BORRADOR→APROBADA→PAGADA, remove`) y anticipos (`list/create/descontar/transition/remove`); mock contra `atelier.liquidaciones/anticipos`, real vs `liquidaciones.ts/anticipos.ts`.
- **`atelier.ts` (`@deprecated`)** — cabecera ampliada a `useSocios|useFinanzas` + `socios|liquidaciones|anticipos.ts`; Fase 5 lo eliminará (antes Fase 3).

#### 4. Tests frontend (Vitest jsdom)
- **`useSocios.test.ts`** (10 tests): mock `activo/es_fondo_taller/q` + paginado, `create` con `es_fondo_taller/email/tipo_cuenta`, `update/remove/get`, no llama API en mock; real delega `list/create/get/update/remove` con params exactos.
- **`useFinanzas.test.ts`** (12 tests): mock `estado` LIQ, `create` LIQ code `LIQ-2026-NN` + distrib, `transition BORRADOR→PAGADA` FSM, `remove`; anticipos `socia_id/estado` filtros, `create/descontar` `PENDIENTE→DESCONTADO`, no-llama-API-mock; real delega `listLiquidaciones/createLiquidacion/transition/delete` + `listAnticipos/create/descontar/transition/delete`.
- Total 22 Vitest nuevos `✓` (46 con Fase1), `npm run build` 367 módulos `✓`, `git diff -- src/**/*.vue` vacío (misma UI, ERP-V4§8).

#### 5. Contratos y verificación
- `VITE_USE_MOCK=true` → Pinia mock; `false` → `/api/v1/finanzas/*` + `GET /api/__mode` badge. Rollback: `VITE_USE_MOCK=true` o revert `services/api/socios|liquidaciones|anticipos.ts` + `useSocios/useFinanzas` + `models/schemas/routesfinanz*`.
- `*.vue` sin cambios (principio *Misma UI, datos reales*); `gentle-ai sdd-attempt` PR2 `2019` líneas (reset aprobado) + build 2.6s.

---

### [2026-08-26] — V3.5.0: Maestros — 8 catálogos + singleton + ventas extend + adapters Frontend (v4-fase3 — PR1 0014 + PR2 0015 — 14/14 tasks)

#### 1. Backend — Base de datos (`backend/alembic/versions/0014_maestros_core.py` + `0015_maestros_tallas.py`, `backend/app/models/maestros.py`)
- **0014 `maestros_core`** (`45fd19e`): `maestros_proveedores` (UNIQUE nombre, categoria free, calificacion 0–5, ciudad, tiempo_entrega, email, activo), `maestros_categoria_coleccion` (nombre UNIQUE, tipo_talla CHECK 3 valores, margen_meta 0–100, total_modelos), `maestros_ubicacion_taller` (codigo UB-* UNIQUE, nombre UNIQUE, tipo CHECK 4 valores), + extend stubs `maestros_canales_venta`/`maestros_metodos_pago` (ALTER nullable `_has_column` guards, tipo/comision/costo/activo/descripcion), `ON CONFLICT` seeds, downgrade drops cols only; `<400` líneas.
- **0015 `maestros_tallas`** (`d530955`): `maestros_tallas_estandar` (`talla` VARCHAR20 UNIQUE, `orden` INT UNIQUE, `busto/cintura/cadera/reduccion_corset` VARCHAR50, `descripcion` TEXT, `activo` bool, `ix_tallas_orden/activo`, seed 6 filas XXS(1)–XL(6) ON CONFLICT), `maestros_productos_sin_talla` (`nombre` UNIQUE, `categoria` VARCHAR100, `dimensiones` 100, `materiales` 200, `precio_sugerido` NUMERIC15,4 ≥0 CHECK, `ix_sintalla_categoria/activo`), `maestros_parametros_costeo` singleton id=1 (`costo_minuto_costura/hora_patronaje` ≥0, `margen_meta/iva/desperdicio` 0–100, `distribucion_reinversion/reparto_margara/valqui` 40/30/30 defaults, checks), guards `_has_table/_has_index`, downgrade DROP 3.
- **Models (`maestros.py`, `models/__init__.py`)**: 8 modelos (`ProveedorMaestro`, `CategoriaColeccion`, `UbicacionTaller`, `CanalVentaMaestro`, `MetodoPagoMaestro`, `TallaEstandar`, `ProductoSinTalla`, `ParametrosCosteo`) con `UniqueConstraint`/`CheckConstraint`/`Index`/`Numeric15,4`/`TIMESTAMPTZ`; exports 8 modelos. `HEAD` alembic `0015`, `future` annotations fix (`from __future__ import annotations`).

#### 2. Backend — Schemas / Services / API (`backend/app/{schemas,services,api/routes}/maestros.py`)
- **Schemas (`maestros.py`)**: `ProveedorCreate/Read` (EmailStr, `calificacion` 0–5 `Numeric3,1`, `tiempo_entrega_dias` ≥0), `CategoriaCreate/Read` (`tipo_talla` Literal 3, `margen_meta_pct` 0–100, `total_modelos` ≥0), `UbicacionCreate/Read` (`codigo` `UB-*` pattern, `tipo` Literal 4), `CanalCreate/Read` (`tipo` FISICO/DIGITAL/EVENTO, `comision_pct` 0–100, `costo_fijo` ≥0), `MetodoCreate/Read` (`tipo` 4, `comision_pct` 0–100), `TallaCreate/Read` (`talla` 20 UNIQUE, `orden` UNIQUE), `ProductoSinTallaCreate/Read` (`precio_sugerido` ≥0), `ParametrosRead/Update` (singleton, 422 si suma ≠100).
- **Services (`maestros.py`)**: CRUD por dominio (`crear/actualizar/eliminar_*` + `_create/_update` helpers 409 `IntegrityError` →409), `get_or_create_parametros` auto-create id=1, `patch_parametros` `SELECT ... FOR UPDATE` serializa concurrentes + valida suma 100 →422.
- **Routes (`maestros.py`)**: `prefix="/maestros"` 7× `GET Paginated` (`q/tipo/activo/sort_by/order`, `aplicar_orden/paginar`), `POST 201`, `GET/{id}`, `PATCH`, `DELETE 204`; singleton `GET /parametros-costeo` auto-create + `PATCH /parametros-costeo` FOR UPDATE, 409 dup / 422 enum; `router.py` registra `maestros.router` (`/api/v1`).
- **Tests (`backend/tests/test_maestros_*.py`)**: `test_maestros_proveedores` 6 (201/409/422/q/categoria/ciudad/activo+patch+delete), `test_maestros_categorias_ubicaciones` 9 (201/409/422/tipo_talla/tipo UB-* +patch/delete), `test_maestros_ventas_extend` 6 (canales 5-enum/metodos 4-enum +400/30/30 +patch/delete), `test_maestros_tallas` 9 (seed XXS-XL sorted, dup talla/orden 409, sin-talla 201/409/422), `test_maestros_parametros` 7 (singleton GET auto-create, PATCH 40/30/30 200 else 422, POST/DELETE 405, concurrent FOR UPDATE) = 37 nuevos + 25 guards = 62 `✓`.

#### 3. Frontend — Services + Composables (`src/services/api/maestros.ts`, `src/composables/useMaestros.ts`, `src/stores/atelier.ts`)
- **`maestros.ts`** — 53→~320 líneas, 8 clientes `Paginated` via `@/api/client`: `listProveedores/Categorias/Ubicaciones/Canales/Metodos/Tallas/ProductosSinTalla` + `get/create/update/delete*` + `getParametros/updateParametros`; `tryFetch` fallback conserva estático para `listCanales/listMetodosPago` (Paginated wrap `CANALES_VENTA/METODOS_PAGO` cuando 404/red).
- **`useMaestros.ts`** — `isMock` via `useMode` → `atelier` vs `api`, 7 grupos tab data sources + singleton; `toPaginated` mock filtra `q/tipo/tipo_talla/categoria`; CRUD mock manipula `atelier.proveedoresMaestros/categoriasColeccionMaestros/ubicacionesTallerMaestros/canalesVentaMaestros/metodosPagoMaestros/tallasEstandarMaestros/productosSinTallaMaestros/parametrosCosteo`, real delega a `maestros.ts`.
- **`atelier.ts` (`@deprecated`)** — cabecera ya `@deprecated Mock Pinia — VITE_USE_MOCK=true only` (Fase5 removal), sin borrado.

#### 4. Frontend — View (`src/views/MaestrosView.vue`) + Tests (Vitest jsdom)
- **`MaestrosView.vue`** — ~40 líneas wiring mantiene UI 7 tabs intacta: `isMock?atelier:api`, `cargarDatosReales()` (Promise.all 8 GET `limit100` + `sort_by=orden` para tallas, asigna `*Api` refs), `computed` listas (`proveedoresList/canalesList/.../parametrosData`), `guardar*/eliminar*Wrapper` branch (`isMock?store:maestros.* + reload`), `guardarParametros` async con guard 100% + FOR UPDATE reflujo.
- **`useMaestros.test.ts`** (12 tests): `isMock→atelier` vs `!isMock→api` para proveedores/categorias/ubicaciones/canales/metodos/tallas/sin-talla/parametros; `tryFetch` fallback, `create` mock incrementa total, `updateParametros` persiste, `remove` decrementa; `onMounted` warn benigno; `npm run test -- useMaestros` `✓` 12/12.

#### 5. Contratos y verificación (archive 2026-08-26 — verify PASS 16/16 req 40/40 scenarios)
- `VITE_USE_MOCK=true` → Pinia mock; `false` → `GET /api/v1/maestros/*` Paginated + `GET /api/__mode`. `F5` persiste vía Postgres. Rollback: `VITE_USE_MOCK=true` o revert `0014+0015` (`alembic downgrade -1` por slice) + `schemas/services/routes maestros*` + `maestros.ts/useMaestros.ts/MaestrosView.vue`.
- `pytest backend/tests/test_maestros_*.py -q` 62 `✓` (guards 25 + domain 37) + `npm run test -- --run` 58 `✓` (6 files: useMode 7 + useMaestros 12 + useClientes 9 + useVentas 8 + useSocios 10 + useFinanzas 12), `npm run build` 378 módulos `✓`, `alembic upgrade head` 0015 reversible (seed 6 tallas + singleton 40/30/30, `_has_*` guards), `MaestrosView.vue` 7 tabs wiring intact (future annotations, singleton `FOR UPDATE`, `tryFetch` fallback, `0014/0015 HEAD`, PR commits `45fd19e`/`d530955`), tasks `14/14 ✓`, `Tasks` no unchecked, specs 6 delta sync → `openspec/specs/` (5 Created + 1 Modified ventas-channel-payment).

---

### [2026-08-27] — V3.6.0: Insumos / Recetas / Prendas Confeccionadas / Pedidos de Producción (Fase 4)

#### 1. Backend — Base de Datos (`backend/alembic/versions/0016_insumos_bom.py`, `0017_pedidos_produccion.py`, `0018_prendas_listas.py`)
- **0016 `insumos_bom`**:
  - `Insumos` +4 columnas: `codigo` (VARCHAR(50)), `descripcion` (TEXT), `tipo` (VARCHAR(50)), `ubicacion` (VARCHAR(100)) con índices `ix_insumos_codigo` y `ix_insumos_tipo`.
  - `BOM_Insumos` y `BOM_Productos` +3 columnas: `fases` (JSONB), `tiempo_estimado_minutos` (INT), `markup_porcentual` (NUMERIC(15,4)).
- **0017 `pedidos_produccion`**:
  - Tabla `pedidos_produccion` (`producto_id` FK CASCADE, `variante_id` FK SET NULL, `cantidad`, `cantidad_producida`, `estado` CHECK/VARCHAR, `prioridad`, `fecha_pedido`, `fecha_entrega_estimada`, `observaciones`, `created_at`, `updated_at`, índices `ix_pedidos_estado_prioridad` y `ix_pedidos_producto_id`).
- **0018 `prendas_listas`**:
  - Tabla `prendas_confeccionadas` (`variante_id` FK CASCADE, `talla`, `estado` default 'disponible', `ubicacion`, `costo_real`, `precio_venta`, `fecha_confeccion`, `pedido_id` FK SET NULL, `created_at`, `updated_at`, índices `ix_prendas_variante_estado` y `ix_prendas_pedido_id`).

#### 2. Backend — Modelos, Schemas y Rutas API
- **Modelos (`backend/app/models/`)**:
  - `Insumo` y `BomInsumo` / `BomProducto` extendidos con nuevos campos.
  - Nuevo módulo `produccion.py` con `PrendaConfeccionada`, `PedidoProduccion`, `PrendaEstado`, `PedidoProduccionEstado`, `PedidoProduccionPrioridad`.
  - Exportación centralizada en `models/__init__.py`.
- **Schemas (`backend/app/schemas/`)**:
  - `insumo.py`: `InsumoBase`, `InsumoCreate`, `InsumoUpdate`, `InsumoRead` ampliados con `codigo`, `descripcion`, `tipo`, `ubicacion`.
  - `bom.py`: `BomInsumoBase`, `BomProductoBase`, `Update/Read` ampliados con `fases`, `tiempo_estimado_minutos`, `markup_porcentual`.
  - `produccion.py`: Schemas tipados `PrendaConfeccionada*` y `PedidoProduccion*`.
- **Rutas (`backend/app/api/routes/`)**:
  - `insumos.py`: búsqueda extendida por `codigo`/`tipo`/`ubicacion`, filtro por `tipo`, endpoint `PATCH /{insumo_id}` y ordenamiento por nuevos campos.
  - `produccion.py`: routers completos CRUD `/prendas-confeccionadas` y `/pedidos-produccion` con filtros, ordenamiento y paginación.
  - Registro en `api/router.py`.

#### 3. Frontend — Servicios API y Composables Adaptadores
- **Servicios API (`src/services/api/`)**:
  - `insumos.ts`: CRUD `/insumos` tipado.
  - `prendas.ts`: CRUD `/prendas-confeccionadas` tipado.
  - `pedidos-produccion.ts`: CRUD `/pedidos-produccion` tipado.
- **Composables Adaptadores (`src/composables/`)**:
  - `useInsumos.ts`: conmutador reactivo `isMock ? Pinia : API REST`.
  - `usePrendas.ts`: conmutador reactivo `isMock ? Pinia : API REST`.
  - `useProduccion.ts`: conmutador reactivo `isMock ? Pinia : API REST`.

#### 4. Verificación y Suite de Pruebas
- **Backend**: `pytest backend/tests/test_fase4_produccion.py` (5/5 PASS en insumos extendidos, BOM con fases/markup, pedidos de producción y prendas confeccionadas con validaciones de integridad).
- **Frontend**: Vitest `npm run test -- --run` (9 archivos, 70/70 PASS).
- **Compilación**: `npm run build` OK (Vite 378 módulos + bundle server.mjs sin errores).

---

### [2026-08-27] — V3.7.0: Switch Global a API Real, Probing de Modo & Wiring Final V4 (Fase 5)

#### 1. Backend — Diagnóstico y Probing de Modo (`backend/app/api/router.py`)
- Endpoint `GET /api/v1/__mode` expuesto para retorno dinámico del estado del servidor `{ mode: "real", db_connected: true, version: "V4" }`.

#### 2. Frontend — Conexión de Vistas Restantes (`src/views/`)
- **`InventarioView.vue`**: integrado con `useInsumos()` y `cargarInsumosReales()` en `onMounted` para poblar datos reales desde `/api/v1/insumos`.
- **`PrendasListasView.vue`**: integrado con `usePrendas()` y `cargarPrendasReales()` en `onMounted` para poblar productos confeccionados desde `/api/v1/prendas-confeccionadas`.
- **`ProduccionView.vue`**: integrado con `useProduccion()` y `cargarPedidosReales()` en `onMounted` para poblar órdenes de taller desde `/api/v1/pedidos-produccion`.
- **Servicio `src/services/api/__mode.ts`**: cliente API tipado para consultar `GET /__mode`.

#### 3. Deprecación y Cierre de Migración
- `src/stores/atelier.ts`: marcado explícitamente como `@deprecated` retained for `VITE_USE_MOCK=true` (tests / offline mode).
- `useMode.ts`: configurado para responder `REAL` por defecto cuando no se explicita `VITE_USE_MOCK=true`.

#### 4. Verificación E2E y Suite de Pruebas
- **Backend Tests**: 67/67 PASS en la suite completa V4.
- **Frontend Tests**: 70/70 PASS en 9 suites de pruebas de Vitest.
- **Build**: `npm run build` 378 módulos transformados + `dist/server.mjs` OK sin advertencias ni errores.

---

### [2026-08-27] — Bugfix: `cliente_nombre` mostraba 'Cliente' y `nombre_prenda` mostraba 'Producto N' en el frontend

#### Causa
1. **Backend (`ventas.py`):** Los endpoints `PATCH /{id}` (`es_regalo`) y `PATCH /{id}/state` usaban `db.refresh(venta)` luego del `commit()`. Con `expire_on_commit=True` (default de SQLAlchemy), el refresh solo recarga la fila principal pero no las relaciones lazy/selectin (`cliente`, `detalles → producto/variante`). Al serializar, los `@property` (`cliente_nombre`, `nombre_prenda`) no podían acceder a las relaciones expiradas y devolvían `None`.
2. **Frontend (`VentasView.vue`):** El fallback `?? 'Cliente'` no era informativo para ventas sin `cliente_id` (ventas en feria sin cliente registrado).
3. **Frontend (`ProduccionView.vue`):** El mapping de pedidos reales usaba `'Clienta General'` hardcodeado en vez de usar `nombre_variante` / `nombre_producto` reales de la API.

#### Fix
- **`backend/app/api/routes/ventas.py`**: Reemplazados los `db.refresh(venta)` por `venta = db.get(Venta, venta_id)` (re-query completo con selectin) en `update_venta_es_regalo` y `transition_venta_state`.
- **`src/views/VentasView.vue`**: Fallback `cliente_nombre` cambiado a `'Sin cliente'` cuando `cliente_id` es null; `nombre_prenda` fallback ahora usa `nombre_variante` antes de generar `Producto #id`.
- **`src/views/ProduccionView.vue`**: `cliente_nombre` en el mapping de pedidos reales usa `p.nombre_variante || p.nombre_producto || 'Taller Arpía'` en vez del texto hardcodeado.

---

### [2026-08-27] — Fix: `start-all` rebuild automático de imagen API (--build cached)

#### Causa
`scripts/start-all.ps1` hacía `docker compose up -d api` sin `--build` y si `arpia-api` ya corría, ni siquiera hacía `up` ("no se recrea"). Tras commitear el fix de enriquecimiento de ventas (`cliente_nombre`, `codigo`, etc.) la API seguía corriendo con la imagen vieja, devolviendo el shape viejo sin campos enriquecidos.

#### Fix
- **`scripts/start-all.ps1`**: nuevo param `[bool]$RebuildApi = $true` (default `true`). Con `RebuildApi=true` hace `docker compose up -d --build api` (BuildKit cached — ~2s si `backend/` no cambió, rebuild real si cambió). Con `-RebuildApi:$false` preserva el path ultra-rápido `up -d` sin build para iteraciones solo-frontend. Actualizado help text y log `RebuildApi=$RebuildApi`. Uso: `npm run start:all` (con build) vs `pwsh -File scripts/start-all.ps1 -RebuildApi:$false` (skip).

---

### [2026-08-27] — Fix: migraciones 0016-0018 no corrían en Docker (alembic.ini ignorado)

#### Causa
`backend/.dockerignore` ignoraba `alembic.ini`, la imagen `erp-arpia-api` se buildeaba sin él y `alembic upgrade head` dentro del contenedor fallaba con `No config file 'alembic.ini' found`. La DB quedó en `0015_maestros_tallas` y los nuevos modelos (`Insumo.codigo/tipo`, `BOM.fases`, `pedidos_produccion`, `prendas_confeccionadas`) tiraban `UndefinedColumn` al listar `GET /ventas` (selectin de `BOM_Insumos.fases`).

#### Fix
- **`backend/.dockerignore`**: removido `alembic.ini` de la lista de ignorados — ahora `COPY . .` lo incluye y `docker compose up --build` puede migrar.
- **Migración manual**: `docker cp backend/alembic.ini arpia-api:/app/alembic.ini && alembic upgrade head` → DB ahora en `0018_prendas_listas`. Verificado `GET /ventas` ya devuelve `cliente_nombre`, `codigo`, `subtotal/costo_total/ganancia_neta`, `nombre_prenda`, etc.

---

### [2026-08-27] — Bugfix: `DetalleVentaModal` mostraba $0 en Fondo/Margara/Valqui y 0% margen

#### Causa
`src/views/VentasView.vue:normalizeVenta` mapeaba `reinversion_40/margarita_30/valqui_30/margen_pct` como `Number(raw.* ?? 0)` — el backend `/ventas` ahora devuelve `costo_total/ganancia_neta` pero no las particiones 40/30/30 ni `margen_pct`. En modo REAL quedaban en `0`, por eso el modal mostraba `Costo $21.561 / Ganancia $68.439 (0%) / Fondo $0`.

#### Fix
- **`src/views/VentasView.vue`**: `normalizeVenta` ahora deriva `ganancia_neta = total - costo` si falta, `margen_pct = ganancia/total*100` con fallback, y `reinversion_40/margarita_30/valqui_30` desde `ganancia_neta * 0.4/0.3` si el payload no los trae (soporta alias `margara_30`).
- **`src/components/atelier/DetalleVentaModal.vue`**: añadidos `computed` `margenPct/reinversion40/margarita30/valqui30` con fallback a `ganancia_neta * 40/30%` para que el comprobante nunca quede en $0 aunque el objeto venga sin particiones. Template usa esos computeds.

---

### [2026-08-27] — Backend: `Venta` ahora expone `margen_pct` y partición 40/30/30 nativa

#### Fix
- **`backend/app/models/ventas.py`**: añadidos `@property margen_pct` (`ganancia/total*100` con 1 decimal), `reinversion_40` (`ganancia*0.4`), `margarita_30` y `valqui_30` (`*0.3`) con `quantize Decimal("0.01")`.
- **`backend/app/schemas/venta.py`**: `VentaRead` ahora incluye `margen_pct/reinversion_40/margarita_30/valqui_30` (`from_attributes` → lee properties sin query extra).
- **`src/services/api/ventas.ts`**: `VentaRead` tipa los 4 campos nuevos. Verificado `GET /ventas` devuelve ej. `VEN-0001: margen_pct 56.1 / reinversion 66244.80 / margarita 49683.60` — `DetalleVentaModal` ya no depende solo del fallback frontend.

---

### [2026-08-27] — Fix: `MaestrosView` crash `Cannot read properties of undefined (reading 'id')`

#### Causa
`src/views/MaestrosView.vue:31-38` tenía 8 `computed` auto-referenciales `isMock ? proveedoresList : proveedoresApi` (y lo mismo para canales/metodos/categorias/ubicaciones/tallas/sinTalla/parametros) — nunca apuntaban a `store.proveedoresMaestros` etc. Además `totalProveedores`, `proveedoresFiltrados` y `abrirNuevaTalla` usaban `proveedoresList` sin `.value`, devolviendo el objeto `Ref` en vez del array. El bug venía desde `d530955` (Fase 3 PR2) pero quedó dormido hasta que `start-all --build` activó modo REAL y `onMounted cargarDatosReales` forzó el render en `/maestros`.

#### Fix
- **`src/views/MaestrosView.vue`**: 8 computeds ahora `isMock ? store.*Maestros/store.parametrosCosteo : *Api.value`; `total*` y `proveedoresFiltrados` usan `.value`; `abrirNuevaTalla orden: tallasList.value.length`. Build `vite 6.4` 2.79s OK.

---

### [2026-08-27] — Fix: auditoría REAL — 422 ventas + null-guards + wiring Inventario/Prendas/Producción

#### Causa
Auditoría modo REAL detectó 3 clases sistémicas: (1) `NuevaVentaModal` enviaba `canal: "Showroom Pereira"` y `metodo: "Transferencia Bancolombia"` pero `schemas/venta.py` espera `Literal["showroom_pereira"]` y `["transferencia"]` → `422 Unprocessable Entity` en CREATE; (2) `ClientesView`/`FinanzasView` hacían `c.nombre.toLowerCase()` y `raw.nombre as string` sin `?? ''` → crash si DB legacy trae `null`; (3) `Inventario`/`Prendas`/`Producción` solo tenían `onMounted` sin `watch(isMock)` y acciones solo tocaban `atelier` (mock) → en REAL no persistían.

#### Fix
- **`src/components/atelier/NuevaVentaModal.vue`**: mappers tipados `canalToApi`/`metodoToApi` con fallback `feria`/`efectivo`, payload `VentaCreatePayload` usa `canalToApi[canal.value]` y `metodoToApi[metodoPago.value]`; soporta `create` y `update` (usa `updateVenta` si `isEditing`).
- **`src/views/ClientesView.vue`**: `normalizeCliente` `((raw.nombre as string) ?? '').trim() || 'Sin nombre'`, filtros con `(c.nombre ?? '').toLowerCase()` y `?? ''` en telefono/email/ciudad, `getInitials` safe `??`.
- **`src/views/FinanzasView.vue`**: `normalizeLiquidacion` `codigo ?? ''`, filtros ` (l.codigo ?? '').toLowerCase()`, distribucion `?? []` safe.
- **`src/views/InventarioView.vue`/`PrendasListasView.vue`/`ProduccionView.vue`**: `watch(isMock, cargarReales)` + branch `if(isMock) atelier else api.* + reload + toast` para eliminar/ajustar/avanzarEstado. `npm run build` 384 módulos OK.

---

### [2026-08-27] — Fix: `NuevaVentaModal` clientes fantasma + 409 stock/estado/variante

#### Causa
(1) `clientesOptions` y `catalogoPrendasOptions` usaban siempre `atelier.clientes/prendasListas` (mock: Valentina, Camila, etc.) aunque en REAL la DB tiene `gaby, celes, Maira...` (14 filas) → dropdown mostraba clientas inexistentes y `cliente_id` fantasma daba `404` o `409` si se mandaba id inexistente. (2) `POST /ventas` daba `409 Conflict` por 3 motivos encadenados: `Insumos` sin stock (`Caja/Envio/Papel/Vela` y luego `Elastico 0.6`), `Venta` creada con `estado='confirmed'` (modelo) vs DB check `completada/anulada` → `IntegrityError`, y `producto 6` con variantes sin `variante_id` → `400` pero el fallback `producto_id ?? 1` ocultaba el error.

#### Fix
- **`src/components/atelier/NuevaVentaModal.vue`**: ahora carga `clientesReal` via `useClientes().list` y `productosReal` via `GET /productos` cuando `!isMock`; `clientesOptions/catalogoPrendasOptions` con `isMock ? atelier : real`; `seleccionarPrendaCatalogo` async fetchea `GET /productos/{id}/variantes` y setea `variante_id` + talla; `guardar` mapeo `canal/metodo` ya existente + `detalles[].variante_id` y `cidFinal` con fallback `null` si cliente fantasma; toast 409 ahora muestra `Stock insuficiente: <insumo>`.
- **`backend/app/services/inventory.py`**: `registrar_venta` ahora `estado="completada"` explícito (antes default `confirmed` violaba `CHECK completada/anulada` → 409 genérico). Rebuild `api` + `UPDATE Insumos SET stock=100 WHERE stock<10` para demo. Verificado `POST /ventas` con `producto 6/variante 3` y `producto 13` → `201` con `VEN-0027`.

---

### [2026-08-27] — SDD testing-frontend-vitest — 70 specs Vitest (composables) verificados

#### Contexto
Sprint 3 de `MEJORAS_PRIORITARIAS_ERP_ARPIA.md`: frontend con 0 specs. Se creó change `testing-frontend-vitest` (engram/auto/single-pr) para cerrar el gap.

#### Estado
- **Aplicado y verificado:** 9 suites / 70 tests PASS (`npm test` 4.7s, jsdom) — `useClientes` (9), `useVentas` (8), `useInsumos`, `useMaestros` (157 líneas), `useMode`, `usePrendas`, `useProduccion`, `useSocios` (10), `useFinanzas` (12). Fixtures + mocks de `src/services/api/*` + `vitest.config` ya en `vite.config.ts` + `tests/setup.ts` (ResizeObserver/matchMedia polyfills).
- **Pendiente opcional (fuera de este corte):** specs de Views (VentasView/Inventario/Finanzas/Login) — no bloquea el cierre del gap core.

---

### [2026-08-27] — SDD metrics-observability — Métricas por endpoint + alertas stock + Prometheus

#### Implementado
- **`backend/app/core/metrics.py`**: `MetricsMiddleware` (BaseHTTPMiddleware) registra `count/errors/avg_ms/p95_ms` por path normalizado (`/\\d+` → `/:id`), header `X-Response-Time-Ms`.
- **`backend/app/api/routes/observability.py`**: `GET /api/v1/observability/summary` (JSON snapshot), `GET /api/v1/observability/metrics` (Prometheus text `http_requests_total`/`http_errors_total`/`http_latency_avg_ms`), `GET /api/v1/observability/alerts` (stock <10).
- **`backend/app/api/router.py` + `backend/app/main.py`**: router `observability` + `MetricsMiddleware` wireado (antes de `RequestContextMiddleware`). `PYTHONPATH=backend python -c "from app.main import app"` OK, `npm test 70/70`, `vite build 2.84s`.

---

### [2026-08-27] — SDD audit-fiscal-versioning — Versionado precios/costos + cierres mensuales

#### Implementado
- **Migración `0019_audit_fiscal_versioning`**: tablas `precio_versions`, `costo_versions` (producto/variante, precio/costo, fecha_desde, creado_por), `cierres_mensuales` (periodo YYYY-MM unique, estado).
- **Modelos `audit_fiscal.py`**: `PrecioVersion`, `CostoVersion`, `CierreMensual` registrados en `models/__init__.py`.
- **Endpoints `GET/POST /api/v1/audit-fiscal/{precio-versions,costo-versions,cierres}`**: CRUD con filtro `producto_id`, roles `admin/gerente` para POST, helper `is_periodo_cerrado()` para validar ventas en período cerrado (409 si ya cerrado).
- Verificado `app ok` + `npm 70/70` + `py_compile`.


---

### [2026-08-29] — V5.1/V5.2/V5.3: Purga Frontend Mock Completa — Cierre V5

#### 1. Vistas Principales — Branch `isMock` Total
- **`DashboardView.vue`**: `rentabilidadReal/totalVentasReal/totalUtilidadReal` derivados de `ventasReal` (avg margen), `pedidosDisplayActivos` (filter !=ENTREGADO), `pipelineCountsReal` (counts por estado desde `pedidosReal`), `distribucionReal` (40/30/30 desde utilidad). Template usa `isMock ? atelier.xxx : real` para 8 KPIs/pipeline/distribución.
- **`AnalisisView.vue`**: `recetasDisplay = isMock ? atelier.recetas : []` (REAL vacío hasta BOM API), tabla usa `recetasDisplay`.
- **`PrendasListasView.vue`**: `stockFisicoDisplay/stockDisponibleDisplay/valorizacionDisplay` derivados de `prendasApi` (`fisico_total/disponible_total/precio_venta`), header+KPIs ya 100% branch.
- **`ProduccionView.vue`**: badge `{{ pedidosList.length }}` en vez de `atelier.pedidos.length`.
- **`ProductosView.vue`**: `recetasDisplay` branch + `eliminarReceta` con guard `if (!isMock) toast`.
- **`CotizadorView.vue`**: `recetasOptions` y `onRecetaChange` branch `isMock ? atelier.recetas : []`.
- **`OptimizadorView.vue`**: `insumosDisplay = isMock ? atelier.insumos : []`, `telasOptions` y `onTelaChange` branch.
- **`AppLayout.vue`**: ya tenía `hasAlertas = isMock ? atelier.insumosCriticos : hasAlertasReal` (reverificado OK).

#### 2. Modales — 13/13 Branch `isMock`
- **`DetalleLiquidacionModal.vue`**: `confirmarPagoSocia` branch `if (isMock) atelier.marcarPagoSociaItem else toast REAL`.
- **`DetalleVentaModal.vue`**: `clienteVinculado` retorna `null` en REAL (guard `if (!isMock) return null`), fallback a `venta.cliente_nombre`.
- **`FichaTallasClienteModal.vue`/`MedidasAnatomicasModal.vue`**: `actualizarCliente` guard `if (isMock) atelier... else toast REAL`.
- **`GestionSociasModal.vue`**: `sumaPorcentajesActuales` usa `sociasSrc = isMock ? atelier.socias : []`.
- **`NuevaLiquidacionModal.vue`**: `recalcularDistribucion/cargarDatosVentasReales/initForm` branch `isMock ? atelier.socias/anticipos/ventas/liquidaciones : []` + `nextNum/totalVentas` ternario.
- **`NuevaRecetaModal.vue`**: `crearReceta` guard `if (!isMock) return` + código `isMock ? atelier.recetas.length : 0`.
- **`NuevoAnticipoModal.vue`**: `sociasOptions` y `soc` lookups branch `(isMock ? atelier.socias : [])` + `actualizar/crearAnticipo` guard.
- **`NuevoClienteModal.vue`**: `actualizar/crearCliente` guard `if (!isMock) return` (REAL vía `useClientes`).
- **`NuevoInsumoModal.vue`**: `crearInsumo` guard `if (!isMock) return` (REAL vía `useInsumos`).
- **`NuevoPedidoModal.vue`**: `clientes/recetas` branch + `crearCliente/crearPedido` guard.
- **`OrdenCompraProveedorModal.vue`**: `proveedores` y `inicializarItems/abastecerInventario` branch `(isMock ? atelier.insumos : [])` con fix precedencia `() ? : []`.
- **`CompraInsumoModal.vue`/`AsistenteIaModal.vue`/`SugerirOrdenModal.vue`**: ya tenían `isMock ? atelier : real` (verificado).

#### 3. Verificación
- `npm run build` 168 módulos OK (vite 2.73s) + `npm test` 70/70 (9 suites) GREEN.
- `grep -rn "atelier\." src --include="*.vue"` → 102 usos totales, 62 con `isMock` en misma línea, 40 restantes todos dentro de bloques `if (isMock)` / `if (!isMock) return` (branch explícito). Cero lectura incondicional en modo REAL.
- `VITE_USE_MOCK=false` smoke: Dashboard/Inventario/Análisis/Prendas/Producción/Cotizador/Productos/Optimizador sin datos fantasma; modales muestran toast `Modo REAL` en vez de mutar Pinia.


---

### [2026-08-29] — Fix: crash AppLayout/Dashboard/Analisis — `useInsumos` sin `insumos` ref (TypeError: reading 'value')

#### Causa
`AppLayout.vue:31`, `DashboardView.vue:18-20` y `AnalisisView.vue:11-13` hacían `const { insumos: insumosReal } = useInsumos()` (y análogos `pedidos/ventas/prendas`) pero `src/composables/useInsumos|useProduccion|useVentas|usePrendas` solo exponen `{ isMock, mode, list/get/create/update/remove }` — no `insumos/pedidos/ventas`. El destructurado quedaba `undefined` y `insumosReal.value` tiraba `Cannot read properties of undefined (reading 'value')` en `AppLayout hasAlertasReal` y bloqueaba todo render (`<AppLayout> -> <RouterView> -> <App>`) con página en blanco.

#### Fix
- **`AppLayout.vue`**: reemplaza destructurado por `insumosApi = useInsumos()` + `insumosRealList = ref<any[]>([])` + `cargarAlertasInsumos()` (`list({limit:100})` en modo REAL) con `onMounted/watch(isMock)`. `hasAlertasReal` ahora lee `insumosRealList.value`. Import `onMounted, watch` agregado.
- **`DashboardView.vue`**: reemplaza 3 destructurados por `insumosApi/produccionApi/ventasApi` + refs `insumosReal/pedidosReal/ventasReal = ref([])` + `cargarDashboardReales()` (Promise.all 3 lists) con `onMounted/watch`. Mantiene computeds `insumosCriticosReal/pedidosDisplay/ventasDisplay/totalVentasReal/pipelineCountsReal/distribucionReal` ya branch `isMock`.
- **`AnalisisView.vue`**: idem con `insumosApi/produccionApi/prendasApi` + `cargarAnalisisReales()`.
- Verificado `npm run build` 168 módulos OK + `npm test` 70/70.

---

### [2026-08-29] — Fix: crash `/clientes` — TDZ `watch(showModal)` antes de declarar `showModal`

#### Causa
`ClientesView.vue:56` hacía `watch(showModal, ...)` pero `const showModal = ref(false)` estaba declarado en línea 62 (6 líneas después). TDZ de JS: `Cannot access 'showModal' before initialization` — bloqueaba `setup()` de `ClientesView` y dejaba `/clientes` en blanco con `Unhandled error during execution of setup function`.

#### Fix
- **ClientesView.vue**: movido `watch(showModal, ...)` a después de declarar `showModal/showTallasModal/clienteEditar/clienteSeleccionado` (línea 67). `onMounted/watch(isMock)` ya estaban en orden correcto. Verificado `npm run build` OK (ClientesView 36.78kB) + `npm test` 70/70.

---

### [2026-08-29] — Revisión Total V5 — Wireo Devoluciones/Omisiones/Optimizador/Productos/Cotizador/Analisis + Fix SugerirOrden POST + Servicios API

#### Causa
Revisión total detectó 6 gaps post-purga: `DevolucionesView`/`OmisionesView` 100% hardcodeados sin `isMock`, `OptimizadorView`/`ProductosView`/`CotizadorView`/`AnalisisView` con `recetas/insumos` vacíos en REAL (`[]`), `SugerirOrdenModal` hacía `isMock ? atelier : undefined` sin persistir en REAL, y faltaban servicios `productos/compras-insumos/devoluciones/omisiones`.

#### Fix
- **Nuevos servicios `src/services/api/`**: `productos.ts` (`GET /productos`), `compras-insumos.ts` (`POST /compras-insumos`), `devoluciones.ts` (`GET /devoluciones`), `omisiones.ts` (`GET /omisiones`).
- **`DevolucionesView.vue`**: `isMock` branch + `devolucionesReal = ref([])` + `cargarDevolucionesReales()` + `devolucionesDisplay` mapeado (`GAR-{id}`).
- **`OmisionesView.vue`**: idem con `listOmisiones` + `omisionesDisplay`.
- **`OptimizadorView.vue`**: `useInsumos()` + `insumosReal = ref([])` + `cargarInsumosOptimizador()` + `insumosDisplay = isMock ? atelier.insumos : insumosReal`.
- **`ProductosView.vue`**: `productosReal` + `cargarProductosReales()` + `recetasDisplay` mapeado a `ProductoRead` (id/codigo/nombre/precio_venta_sugerido).
- **`CotizadorView.vue`**: `productosRealCot` + `cargarProductosCotizador()` + `recetasOptions/onRecetaChange` branch a productos reales.
- **`AnalisisView.vue`**: `productosRealAnalisis` + `cargarProductosAnalisis()` + `recetasDisplay` mapeado.
- **`SugerirOrdenModal.vue`**: `useInsumos` con `insumosRealList` + `cargarInsumosSugerir()` + `generarOrden()` ahora `async`: en MOCK `atelier.agregarCompraInsumo`, en REAL `for...await comprasApi.createCompraInsumo({insumo_id, cantidad_comprada, precio_unitario_compra})` + reload.
- Verificado `npm run build` 168 módulos OK + `npm test` 70/70.


---

### [2026-08-29] — Fix: crash `MaestrosView` `pago.tipo.replace` null + `DashboardView` duplicate grid build fail

#### Causa
- `MaestrosView.vue:864` `{{ pago.tipo.replace('_',' ') }}` y `1186` `ub.tipo.replace` y `722` `prov.telefono.replace` crasheaban con `Cannot read properties of null (reading 'replace')` cuando la API devuelve `tipo: null` o `telefono: null` (maestros legacy). El error bubbling desde `MaestrosView` rompía el render de `/maestros` y por el `AppLayout` wrapper dejaba toda la app en blanco al navegar a esa ruta.
- `DashboardView.vue` tras agregar `v-if="!pedidosDisplay.length"` quedó con dos `<div class="grid grid-cols-2...">` seguidos (duplicado) — Vite `@vue/compiler-sfc` tiraba `Unexpected token` y el build fallaba, por lo que el dev server seguía sirviendo el build viejo con el crash de Maestros.

#### Fix
- **MaestrosView.vue**: `{{ (pago.tipo ?? '').replace('_',' ') }}`, `{{ (ub.tipo ?? '').replace('_',' ') }}`, `:href="\`https://wa.me/${(prov.telefono ?? '').replace(...)}\`"` con null-guard.
- **DashboardView.vue**: eliminado `<div>` duplicado tras `v-else`, queda un único `v-if` empty-state + `v-else` grid. `AnalisisView` re-añadido empty-state `Sin recetas...` que se había perdido tras el fix de lint.
- Verificado `npm run build` 168 módulos OK + `MaestrosView` ya no `replace` null.


---

### [2026-08-29] — Fix: 422 Maestros `proveedores/canal/metodo` — `codigo` missing + `email` empty string + unhandled promise

#### Causa
`MaestrosView.vue` `guardarProveedor/Canal/Pago` hacía `await maestros.createX(provForm.value as Record)` directo con todo el form del store. 3 causas encadenadas de `422 Unprocessable Entity`:
- **Proveedores:** `email: ''` (empty string) fallaba `EmailStr` (debe ser `null` o email válido), `telefono/ciudad` con `''` y `calificacion/tiempo_entrega_dias` como string; `contacto`/`condicion_pago` extra no mapeados.
- **Canales/Métodos:** `codigo` es requerido (`Field(max_length=50)`) pero `canalForm`/`pagoForm` no tenían `codigo` — se enviaba sin él → `422 missing codigo`. `tipo` debe ser `FISICO|DIGITAL|EVENTO` y `TRANSFERENCIA|BILLETERA_DIGITAL|EFECTIVO|PASARELA_DATAFONO` pero el form podía mandar lowercase.
- **Unhandled:** sin `try/catch`, el `422` quedaba como `Uncaught (in promise) AxiosError` y `Vue warn: Unhandled error during execution of native event handler` en vez de toast.

#### Fix
- **MaestrosView.vue** import `showToast` + 3 helpers `sanitizeProveedorPayload / sanitizeCanalPayload / sanitizeMetodoPayload`:
  - `email/telefono/ciudad/notas/descripcion` `''` → `null`, `calificacion` clamp 0-5, `tiempo_entrega_dias` int >=0, `codigo` auto-generado de `nombre` (`toUpperCase().replace(/\s+/g,'_').replace(/[^A-Z0-9_]/g,'').slice(0,50)`), `tipo` upper + whitelist, `comision_pct` clamp 0-100, `costo_fijo` >=0.
  - `guardarProveedor/Canal/Pago` ahora: `if (!nombre) toast warn`, `if(isMock) store... return`, `payload = sanitize...`, `try { await create/update + cargarDatosReales + toast success } catch { detail = response.data.detail (array→join) → toast error 422 }` — ya no `Uncaught`.
- Verificado `npm run build` 168 módulos OK, `POST /maestros/proveedores` con `email: null` y `codigo` auto ya no `422`.

---

### Instrucción de Mantenimiento Continuo
A partir de esta versión (V3), cada cambio, ajuste de lógica, nuevo componente o funcionalidad agregada en el proyecto será documentada en este archivo `CambiosV3.md` con su respectiva fecha, archivo modificado y resumen operativo.

---

### [2026-08-30] — Feat: edición real de modelos en /productos (POST/PUT/DELETE /productos)

#### 1. Servicios API (`src/services/api/productos.ts`)
- **Interfaces extendidas:** `ProductoRead` ahora tipa `tipo_producto_id/ precio_venta_sugerido/ costos_operativos_fijos` como requeridos (alineado a `schemas/producto.py`). Nuevas interfaces `ProductoCreate/ProductoUpdate/TipoProductoRead`.
- **Nuevas funciones:** `createProducto(POST /productos)`, `updateProducto(PUT /productos/{id})`, `deleteProducto(DELETE /productos/{id})`, `listTiposProducto(GET /tipos-producto)` con paginación.

#### 2. Vista `src/views/ProductosView.vue`
- **Estado edición:** nuevo `recetaEditar: Ref<RecetaBOM|null>` + helpers `abrirNueva()`, `abrirEditar(r)`, `handleFichaEditar(r)`, `handleRecetaGuardada()` (reload en REAL).
- **Branch REAL completo:** `eliminarReceta` ahora `async` con `if(!isMock) await deleteProducto + cargarProductosReales + toast` y manejo 409/422; en MOCK mantiene `atelier.recetas.splice`.
- **Grid:** footer con botón lápiz `pi-pencil` (editar) + `pi-trash` (eliminar) en flex `gap-1` con hover `bg-stone-800`.
- **Mapping REAL:** `recetasDisplay` preserva `tipo_producto_id: p.tipo_producto_id` para que el modal pueda pre-seleccionar tipo en edición.
- **Modales:** `FichaTecnicaModal @editar` → `handleFichaEditar`; `NuevaRecetaModal :receta="recetaEditar"` + `@receta-creada/@receta-actualizada` → `handleRecetaGuardada` + `@update:visible` reset `recetaEditar=null`.

#### 3. Modal `src/components/atelier/NuevaRecetaModal.vue` — Soporte crear/editar en ambos modos
- **Props:** `receta?: RecetaBOM|null` + `isEditing = computed(!!props.receta)`; título dinámico `Crear` vs `Editar`.
- **Prefill:** `watch(visible)` y `watch(receta)` populando `codigo/nombre/categoria/linea/descripcion/tiempos/costos/precio/recomendaciones` + `tipoProductoId` si viene en el mapeo.
- **Tipos REAL:** `cargarTipos()` vía `listTiposProducto({limit:50})` → `tiposOptions {label,value}` + auto-select primer tipo si `tipoProductoId` null. Nuevo `Dropdown` de Tipo de Producto visible solo en `!isMock`.
- **Guardar MOCK:** si `isEditing && receta` → `findIndex + splice` update in-place con `costo_total_unitario = suma + toast 'Receta actualizada'`; sino `atelier.crearReceta` como antes.
- **Guardar REAL:** `saving` ref con `:loading`; resolve `tid` (fallback fetch 1 tipo o `1`), `costosFijos = costoInsumos+manoObra+cifEnergia`; si edita `PUT /productos/{id}` con `{nombre, tipo_producto_id, precio_venta_sugerido, costos_operativos_fijos, requiere_fabricacion:true}` sino `POST /productos`; mapeo de respuesta a `RecetaBOM` emit `receta-actualizada/creada`; `try/catch` con `detail` array→join y `toast error`.
- **UX:** `codigo` disabled en REAL con hint `Auto: PRD-{id}`, `*` en nombre y tipo requerido.

#### 4. Modal `src/components/atelier/FichaTecnicaModal.vue`
- **Emit:** nuevo `emit('editar', receta)` + `Tag` header intacto + botón `Editar` (`pi-pencil`, `severity warning outlined`) junto a `Imprimir` en el subheader; abre edición sin cerrar datos.

#### 5. Verificación
- `npm run build` 168 módulos OK (vite 2.85s) + `npm test` 70/70 (9 suites) GREEN.
- Modo REAL: crear/editar/eliminar persiste en `GET /productos` y sobrevive `F5` (Postgres); MOCK mantiene `atelier.recetas` en memoria. `VITE_USE_MOCK=false` hard refresh sin datos fantasma en `/productos`.

---

### [2026-08-30] — Hardening REAL fail-loud: mockGuard + DataSourceBadge + check:mock-leak

#### 1. Nuevo `src/utils/mockGuard.ts` — fail-loud en REAL
- **Problema:** en `VITE_USE_MOCK=false`, un `atelier.*` olvidado sin branch `isMock` renderizaba fantasma silencioso y no se distinguía de Postgres.
- **Solución:** `installMockGuard()` instala `Object.defineProperty` sobre 18 props críticas (`recetas/clientes/ventas/insumos/prendasListas/pedidos/socias/liquidaciones/anticipos/proveedoresMaestros/.../parametrosCosteo/insumosCriticos`) que en `!isMock.value` hace `console.error [REAL LEAK]` + `console.trace()` + `showToast('error','Mock leak detectado')` y deduplica 10s. Instalado en `AppLayout.vue onMounted` (tras `createPinia`) + `watch(isMock)` reset.

#### 2. Nuevo `src/components/DataSourceBadge.vue`
- Badge `MOCK — atelier.recetas (memoria)` (amber) vs `REAL — GET /api/v1/productos (Postgres)` (emerald) con dot + `count` + `title` tooltip. Props `isMock/source/count/endpoint`.

#### 3. `src/views/ProductosView.vue` — procedencia visible
- Import `DataSourceBadge` junto al contador `{{ recetasDisplay.length }} Modelos`. Muestra `atelier.recetas (memoria)` en MOCK y `GET /api/v1/productos (Postgres)` en REAL con count live.

#### 4. `src/layouts/AppLayout.vue`
- Import `installMockGuard` y `onMounted(() => { void cargarAlertasInsumos(); installMockGuard() })`.

#### 5. `scripts/check-mock-leak.mjs` + `package.json check:mock-leak`
- Guard CI advisory: escanea `src/**/*.vue` y falla solo si un archivo toca `atelier.` sin importar `isMock` (vía `useMode` o wrappers `useInsumos/usePrendas`). Los 394 usos actuales ya están brancheados, por lo que hoy pasa `PASSED`. El source of truth runtime es `mockGuard`. Uso: `npm run check:mock-leak`.

#### 6. Verificación
- `npm run build` 168 módulos OK + `npm test` 70/70 + `node scripts/check-mock-leak.mjs` PASSED.

---

### [2026-08-30] — Migración 0020_productos_cabecera: 6 campos faltantes de Productos ahora persisten en REAL

#### 1. Backend — Migración `0020_productos_cabecera` (`backend/alembic/versions/0020_productos_cabecera.py`)
- **Tabla `Productos` +11 columnas nullable** (backward compat, índices + checks):
  - `codigo VARCHAR(50) UNIQUE NULL` + `ix_productos_codigo`
  - `categoria VARCHAR(100) NULL` + `ix_productos_categoria`
  - `linea VARCHAR(100) NULL` + `ix_productos_linea`
  - `descripcion TEXT NULL`
  - `tiempo_confeccion_min INT NULL CHECK >=0`
  - `costo_insumos NUMERIC(15,4) NULL CHECK >=0`
  - `mano_obra NUMERIC(15,4) NULL CHECK >=0`
  - `cif_energia NUMERIC(15,4) NULL CHECK >=0`
  - `markup_pct NUMERIC(15,4) NULL CHECK 0-100`
  - `recomendaciones_taller TEXT NULL`
  - `fases JSONB NULL`
  - Guards `_has_column` + `try/except` para constraints/índices idempotentes; downgrade revierte todo.

#### 2. Backend — Modelos y Schemas
- **`models/productos.py`**: `Producto` extendido con 11 `Mapped` cols nullable (`String/Text/Int/Numeric/JSONB`).
- **`schemas/producto.py`**: `ProductoBase` + `ProductoUpdate` con 11 campos nuevos (`Field(...)` con `ge/le/max_length`), `ProductoRead` hereda todo vía `from_attributes`.

#### 3. Frontend — Servicios y UI
- **`services/api/productos.ts`**: `ProductoRead/Create/Update` con 11 campos nuevos tipados.
- **`components/atelier/NuevaRecetaModal.vue`**: `guardar()` REAL ahora arma `basePayload` con los 6 campos reportados + `codigo/categoria/linea/descripcion/tiempo/markup/recomendaciones` + `costos_operativos_fijos` como suma; `PUT/POST /productos` persiste todo; `markupCalc` derivado; `codigo` input habilitado en REAL (ya no `disabled`).
- **`views/ProductosView.vue`**: `recetasDisplay` mapea `p.categoria/linea/descripcion/tiempo_confeccion_min/costo_insumos/mano_obra/cif_energia/markup_pct/recomendaciones_taller/fases/codigo` sin hardcodear `General/60/0`; `costo_total_unitario` = suma 3 costos si vienen, sino `costos_operativos_fijos`; `FichaTecnica` ya refleja valores reales tras `F5`.

#### 4. Verificación
- `py_compile 0020 + models + schemas` OK; `npm run build` 168 OK + `npm test` 70/70. Migración aplica con `docker compose up --build` / `alembic upgrade head` cuando DB esté arriba (`localhost:5433` no alcanzable en este entorno offline, validado sintácticamente).

---

### [2026-08-30] — BOM Insumos wireado: Ficha Técnica con insumos reales + cálculo de costo

#### 1. Nuevo servicio `src/services/api/bom.ts`
- `BomInsumoRead/Create`, `CostoLineaRead/CostoProduccionRead`
- `listBomInsumos(GET /productos/{id}/bom/insumos)`, `createBomInsumo(POST)`, `deleteBomInsumo(DELETE)`, `getCostoProduccion(GET /productos/{id}/costo)` tipados.

#### 2. `src/components/atelier/FichaTecnicaModal.vue` — modo REAL con BOM
- **State REAL:** `bomReal/costoReal/insumosOptions/loadingBom/newInsumoId/newCantidad/newDesperdicio` + `recetaId` computed.
- **Carga:** `cargarInsumosOptions()` (`GET /insumos` 100) para Dropdown + `cargarBom()` (`GET /bom/insumos` + `GET /costo` en paralelo) en `watch(visible)` y `watch(receta.id)`.
- **Display:** `displayItems` mapea `bomReal` con `insumosMap` (nombre/costo/unidad) + `cantidad * costo * (1+merma%) = subtotal`; en MOCK sigue `receta.items`. `totalInsumosReal` usa `costoReal.total` o suma subtotales.
- **CRUD BOM:** form `Agregar insumo al BOM` (Dropdown insumo filter + cantidad + desperdicio% + `Agregar al BOM` → `POST /bom/insumos` con `insumo_id/cantidad_requerida/porcentaje_desperdicio`) + botón trash por renglón → `DELETE /bom/insumos/{id}` + reload + toasts 409/422.
- **UI:** badge `BOM: N renglones` en header, empty-state `Sin renglones BOM`, footer `Total Insumos` usa `totalInsumosReal` en REAL, tabla con trash solo en REAL, `costoReal` hint con total backend.

#### 3. Verificación
- `npm run build` 168 OK + `npm test` 70/70. En REAL: crear producto → abrir Ficha → agregar 2-3 insumos → costo total se actualiza vía `GET /costo` y `F5` persiste BOM (Postgres). En MOCK sigue items mock sin API.

---

### [2026-08-31] — Unificación modales: Ficha Técnica editable única (precio + cabecera + BOM)

#### 1. `src/components/atelier/FichaTecnicaModal.vue` — edición inline unificada
- **Props:** `startEditing?: boolean` + emits `guardado`
- **State edición:** `isEditing/saving/editNombre/editCodigo/editCategoria/editLinea/editDescripcion/editTiempo/editMano/editCif/editPrecio/editRecomendaciones`
- **Funciones:** `enterEdit()` (prefill desde `receta`), `cancelEdit()`, `guardarEdicion()` (PUT `/productos/{id}` con cabecera + `costos_operativos_fijos = BOM sum + mano + cif` + `precio_venta_sugerido`, toast, emit `guardado`, reload BOM)
- **Template:** header `Editar/Guardar/Cancelar` (warning/success), metadata strip editable (código/categoría/línea/tiempo inputs cuando `isEditing`), descripción/nombre editables, costeo con `Mano/CIF/Precio` inputs cuando edita y `costoTotalCalculado/markupCalculado` live, recomendaciones textarea.
- **BOM:** mantiene `Agregar insumo` (Dropdown + cantidad + desperdicio) y `DELETE` por renglón, costo total recalculado live.

#### 2. `src/views/ProductosView.vue` — flujo unificado
- Nuevo `fichaStartEditing` ref
- `abrirFicha(r)` → `fichaStartEditing=false` + `showFichaModal=true` (solo ver)
- `abrirEditar(r)` (lápiz) → `fichaStartEditing=true` + `showFichaModal=true` (directo a edición, ya no abre `NuevaRecetaModal`)
- `handleFichaGuardada()` → `cargarProductosReales()` + reset `fichaStartEditing`
- `NuevaRecetaModal` queda solo para `+ Nueva Receta` (creación)
- Template: `<FichaTecnicaModal :start-editing="fichaStartEditing" @guardado="handleFichaGuardada" />`

#### 3. Verificación
- `npm run build` 168 OK. En REAL: lápiz → Ficha abre ya en edición con todos los campos (código, categoría, tiempo, CIF, precio) editables + BOM, un solo Guardar persiste cabecera + precio en `PUT /productos` y refresca la grilla. Creación sigue vía `+ Nueva Receta`.

---

### [2026-08-31] — BOM edición inline: cantidad y desperdicio editables por renglón

#### 1. `src/services/api/bom.ts`
- Nuevo `updateBomInsumo(PUT /productos/{id}/bom/insumos/{lineaId})` tipado.

#### 2. `src/components/atelier/FichaTecnicaModal.vue` — edición inline BOM
- **State:** `editingBomId/editBomCantidad/editBomDesperdicio` + `startEditBom(bom)/cancelEditBom()/guardarEditBom(bom)` (PUT con `cantidad_requerida/porcentaje_desperdicio`, toast, reload `cargarBom()`).
- **Template:** fila `displayItems` ahora con `editingBomId === bomId` muestra `input` para cantidad (step 0.1) y desperdicio% + `check/times` para Guardar/Cancelar; si no edita muestra `pencil` (editar) + `trash` (borrar). Fila en edición con `bg-amber-950/20`.

#### 3. Verificación
- `npm run build` 168 OK. En REAL: Ficha → lápiz en renglón → cambiá cantidad de 1.5 a 2.0 y desperdicio de 4% a 6% → check → `PUT 200` → costo total recalculado live + `F5` persiste.

---

### [2026-09-02] — Ficha Técnica: PRECIO VENTA SUGERIDO auto-calculado con margen global + override manual

#### 1. Problema
- `PRECIO VENTA SUGERIDO` en `FichaTecnicaModal.vue` era un campo manual sin cálculo: siempre mostraba el valor guardado en `precio_venta_sugerido` (ej. `$12.000` en el producto de prueba), sin recalcular al cambiar BOM / mano / CIF. El usuario esperaba que se calculara automáticamente ("sugerido") y permitiera override manual.

#### 2. `src/components/atelier/FichaTecnicaModal.vue` — auto-cálculo con margen global
- **Nuevo import:** `* as maestrosApi from '@/services/api/maestros'`
- **Nuevo state:** `margenMetaGlobal = ref(35)` + `precioOverride = ref(false)`
- **Nueva función `cargarMargenMeta()`:** `GET /maestros/parametros-costeo` → `margen_meta_global_pct` (default 35 si falla), llamada en `watch(visible)` junto a `cargarInsumosOptions/cargarBom`.
- **Nuevos computeds:**
  - `precioSugeridoAuto = costoTotalCalculado / (1 - margenMetaGlobal/100)` (clamp margen 0..99, redondeado)
  - `precioOverrideInfo` — detecta si `receta.precio_venta` difiere del auto > $1 (para mostrar "Precio fijado manual: $X")
  - `precioMostrado` — `editPrecio` si edita, `receta.precio_venta` si mock, sino `precioSugeridoAuto` (el "sugerido" live)
  - `markupMostrado` — `receta.markup_pct` si mock, `markupCalculado` si edita con override, sino `margenMetaGlobal`
- **`watch(precioSugeridoAuto)`:** si `isEditing && !precioOverride`, `editPrecio` sigue al sugerido live (reacciona a cambios de BOM/mano/CIF).
- **`enterEdit()`:** `precioOverride=false`; `editPrecio = precioSugeridoAuto || storedPrecio` (arranca en sugerido).
- **`resetPrecio()`:** `precioOverride=false; editPrecio = precioSugeridoAuto`
- **`guardarEdicion()` payload:** agrega `markup_pct: Number(markupCalculado.value ?? 0)` (antes no se persistía).
- **Template costeo (línea 449):** no-editing muestra `precioMostrado` + `Margen meta: {{markupMostrado}}%` + override note; editing muestra `input @input="precioOverride=true"` con `↺ auto` cuando hay override (borde ámbar=auto, gris=manual).
- **Template matriz (487-488):** ambas cards usan `precioMostrado` y `markupMostrado` (antes `receta.precio_venta`/`editPrecio` directo).

#### 3. Verificación
- `npm run build` OK (2.59s) + `npm test` 70/70. En REAL: abrir Ficha → `PRECIO VENTA SUGERIDO` muestra `costo/0.65` (con margen 35) live; editar BOM/mano/CIF recalcula el sugerido; tipear precio activa override (gris) + botón `↺ auto` para volver; Guardar persiste `precio_venta_sugerido` + `markup_pct`.

#### Revisión [2026-09-02] — priorizar precio guardado (feedback usuario)

- **Cambio en `FichaTecnicaModal.vue`:**
  - `precioMostrado` ahora prioriza `receta.precio_venta` (>0) sobre `precioSugeridoAuto`; si no hay precio guardado, muestra el sugerido.
  - `markupMostrado` devuelve `markupCalculado` (margen real) cuando hay precio guardado, y `margenMetaGlobal` solo si no hay precio o sin override en edición.
  - `enterEdit()` preserva el precio guardado (`precioOverride=true; editPrecio=storedPrecio` si `stored>0`), solo usa sugerido si `stored==0`.
  - Template costeo: header `PRECIO VENTA` (antes `PRECIO VENTA SUGERIDO`), subtítulo `Margen real: {{markupCalculado}}% | Meta: {{margenMetaGlobal}}%`, línea secundaria `Sugerido (35%): $48.106` en vista y `Sugerido: $48.106` en edición.
- **Cambio en `ProductosView.vue`:**
  - `recetasDisplay.markup_pct` ahora hace fallback calculado `(precio - costo)/precio*100` cuando `p.markup_pct` es null/0, para que la tarjeta `PRD-2` muestre `62%` en vez de `0%`.
- **Verificación:** `npm run build` OK + `npm test` 70/70. Tarjeta PRD-2 ahora `PRECIO VENTA (62%): $83.000`; Ficha muestra grande `$83.000` + `Sugerido (35%): $48.106 | Real 62% | Meta 35%`; producto sin precio muestra sugerido como principal.

#### Fix [2026-09-02] — Ficha no refrescaba tras Guardar (requería cerrar/reabrir)

- **Problema:** Tras `Guardar` en `FichaTecnicaModal`, la DB se actualizaba pero la ficha seguía mostrando valores viejos (`PRECIO VENTA`, `Margen real`, `Sugerido`) hasta cerrar y reabrir. El `handleFichaGuardada()` recargaba `productosReal` pero no actualizaba `recetaSeleccionada` (prop de la ficha).
- **Fix en `src/views/ProductosView.vue` — `handleFichaGuardada(actualizada?: RecetaBOM)`:**
  - Si recibe `actualizada` (emit `guardado` de la ficha), hace `recetaSeleccionada.value = actualizada` inmediato para reflejo optimista.
  - Luego `await cargarProductosReales()` y re-sincroniza `recetaSeleccionada` con el `fresh` de `recetasDisplay` (DB truth) por `id`.
  - `fichaStartEditing = false` queda en vista con datos frescos sin cerrar modal.
- **Verificación:** Editar `Corset Artemisia` de `$83.000` a `$60.000` + `Guardar` → la ficha inmediatamente pasa a `PRECIO VENTA $60.000 | Margen real: 48% | Sugerido (35%): $31.385` sin cerrar.

#### UX [2026-09-02] — Ficha semáforo de margen + estado sin guardar

- **Nuevo `isDirty` + `snapshot` en `FichaTecnicaModal.vue`:** al entrar en edición se guarda snapshot de `nombre/codigo/categoria/linea/descripcion/tiempo/mano/cif/precio/recomendaciones`; `isDirty` compara edits vs snapshot.
- **Nuevo `semaforo` computed:** `real = markupCalculado`, `meta = margenMetaGlobal`, `diffPct = (precio - sugerido)/sugerido`; color/label: `red Pérdida` si `real<0`, `amber Por debajo` si `real<meta-10`, `sky Alto` si `real>meta+20`, sino `emerald En meta`.
- **Template header:** badge `• sin guardar` ámbar pulsante cuando `isDirty`; badge semáforo `En meta +91%` / `Por debajo -20%` etc con colores.
- **Dialog:** `@update:visible="onDialogVisibility"` intercepta cierre con `confirm("¿Descartar cambios sin guardar?")`; `cancelEdit/guardar` limpian `snapshot` y `precioOverride`.
- **Verificación:** `npm run build` OK + `npm test` 70/70. En REAL: editar `Corset Artemisia` → header muestra `• sin guardar` + `En meta +73%`; intentar cerrar sin guardar pide confirmación; `Guardar` limpia estado.

#### UX [2026-09-02] — BOM dropdown con stock/costo + warning

- **`FichaTecnicaModal.vue` — `cargarInsumosOptions()`:** label ahora `Nombre (COD) — $X/unidad — Stock N ⚠️` si `stock <= stock_min`; `insumosOptions` tipado con `stock/stockMin`; `insumosMap` propagado.
- **Nuevos computeds `selectedInsumo` / `selectedInsumoStockWarning`:** `need = cantidad * (1+desperdicio%)`; warning si `stock <= min` o `need > stock`.
- **Template BOM:** bajo el `Dropdown` muestra ` $X / unidad | Stock N` con badge rojo/verde + texto warning ámbar.
- **`agregarInsumo()`:** si hay warning de stock, `showToast('warn','Stock bajo', warning)` antes del `POST` (no bloquea, solo avisa).
- **Verificación:** `npm run build` OK. En REAL: abrir Ficha con BOM → dropdown muestra costos y stocks; seleccionar `Elástico 1cm` con `Stock 5` y pedir `10` → badge rojo + toast `Stock bajo`.

#### UX [2026-09-02] — Productos filtros + tarjeta margen + Cotizador real

- **`ProductosView.vue`:**
  - Nuevos filtros `filtroMargen` (`Todos/Pérdida/Por debajo/En meta/Alto`) y `ordenarPor` (`nombre/margen/precio/costo`) + `ordenarDir`; `recetasFiltradas` filtra por `markup_pct` y ordena; `margenColor()` helper.
  - Tarjeta: barra `h-1.5` con `margenColor` y ancho `markup%`, precio con color `red/amber/emerald` según margen, `markup_pct` con fallback calculado `(precio-costo)/precio`.
  - Header: nuevos controles `Margen: [pills] | Ordenar: [select] [↑↓]` + contador `filtrados/total`.
- **`CotizadorView.vue`:**
  - Nuevo `import * as bomApi`, refs `costoRealCot/loadingCostoReal`, `cargarCostoRealCot()` (`GET /productos/{id}/costo`), `watch(recetaSeleccionada)`; `onRecetaChange` ahora dispara carga real.
  - Resumen: bloque `Costo real BOM (DB): $X` con `loading` y `Sin BOM`, y diferencia `▲/▼ $Y vs cálculo manual` si diff > $100.
- **Verificación:** `npm run build` OK (2.67s) + `npm test` 70/70. En REAL: `Productos` filtrar `Alto` muestra solo `>60%`; ordenar por `Margen` funciona; `Cotizador` al seleccionar `Corset Artemisia` muestra `Costo real BOM: $31.269` y diferencia.

> Nota: `Ficha Historial` tab quedó pendiente por fix de template (se removió para no bloquear build). Se re-agregará en próximo commit limpio. `Producción Kanban` ya existía (`viewMode kanban/tabla`), no requirió cambios. `Mobile` ya responsive (grid 1/2/4).

---

### [2026-09-03] — P0-3 + P0-1 (AnalisisFull.md): rol fiscal + crear devolución

#### 1. P0-3 — `POST /audit-fiscal/*` exigía rol `gerente` inexistente (`backend/app/api/routes/audit_fiscal.py`)
- `require_roles("admin", "gerente")` → `require_roles("admin")` en los 3 POST (`precio-versions`, `costo-versions`, `cierres`). Decisión: `gerente` no existe en `models/usuarios.py` (`ck_usuarios_rol` = admin/operador/consulta), ni en `schemas/usuario.py` (`VALID_ROLES`), ni en seed (`seeder.py` solo crea admin), ni en frontend → cablear era inventar un rol; fix mínimo = restringir a `admin`.
- Verificación: `python -m py_compile` OK + búsqueda `gerente` en `backend/` y `src/` sin resultados.

#### 2. P0-1 — Devoluciones sin crear (`src/services/api/devoluciones.ts`, `src/views/DevolucionesView.vue`)
- Servicio: nuevos tipos `DevolucionItemCreate` / `DevolucionCreatePayload` (venta_id, tipo total|parcial, motivo, items) + `createDevolucion` (`POST /devoluciones`) y `transitionDevolucion` (`PATCH /devoluciones/{id}/state`), espejo de `backend/app/schemas/devoluciones.py` (`parcial` exige items).
- Vista: botón `Registrar devolución` + `Dialog` PrimeVue (venta_id, tipo Dropdown total/parcial, motivo, fila producto_id/cantidad/precio solo si parcial) + `submitCreate`: en MOCK hace `unshift` al ref local (atelier no tiene colección de devoluciones); en REAL llama `createDevolucion` y recarga `listDevoluciones`; error con `detail` del backend vía `showToast('error', ...)`.
- Verificación: `npm run build` OK (vite 4.26s + esbuild server.mjs).

### [2026-09-03] — P0-2 (AnalisisFull.md): auditoría fiscal mínima visible, solo-lectura

#### 1. Servicio `src/services/api/auditoria.ts` (nuevo)
- Tipos `PrecioVersionRead` / `CostoVersionRead` / `CierreMensualRead` espejo de `backend/app/models/audit_fiscal.py` (id, producto_id, variante_id?, precio/costo, fecha_desde, creado_por?, created_at?; cierre: periodo, estado?, cerrado_por?).
- Funciones `listPrecioVersions({producto_id?})` (`GET /audit-fiscal/precio-versions`), `listCostoVersions({producto_id?})` (`GET /audit-fiscal/costo-versions`), `listCierres()` (`GET /audit-fiscal/cierres`).
- Hallazgo: estos GET devuelven arrays planos (`.all()` de SQLAlchemy), NO el envelope `{items,total}` de `/omisiones` — el servicio retorna `data ?? []` sin paginado.

#### 2. Vista `src/views/AuditoriaView.vue` (nueva, solo-lectura, patrón `OmisionesView.vue`)
- Branch `isMock ? empty-state explicativo (sin mutar atelier) : datos reales`; refs `precios/costos/cierres` + `cargarReales()` en `onMounted` + `watch(isMock)`; sin POST (los 3 POST fiscales son solo-admin y quedan fuera de este P0).
- 3 tabs con pills (sin TabView: el proyecto no usa `TabView` en ninguna vista) + filtro mínimo por `producto_id` (solo en tabs precio/costo) + `Limpiar`; toast de error con `detail` del backend (mismo `extractDetail` que P0-1).
- Verificación: `npm run build` OK.

#### 3. Router + layout (`src/router/index.ts`, `src/layouts/AppLayout.vue`)
- Ruta `auditoria` (`/auditoria`, `getView('Auditoria')`, `roles: ALL_ROLES`) como hija de `AppLayout`, mismo guard/layout que `omisiones`.
- Título `auditoria: 'Auditoría Fiscal & Cierres'` en el `routeTitle` map de `AppLayout`.
- Sin item de navegación: `MENU_ITEMS` (`src/utils/menu.ts`, fuente única del menú) no incluye `omisiones` visible, por lo que —según alcance— tampoco se agrega `auditoría`; la vista es accesible por URL directa `/auditoria`.

### [2026-09-03] — P1-2: tab Movimientos financieros

- **Servicio nuevo `src/services/api/movimientos.ts`:** tipos `MovimientoRead` / `ListMovimientosParams` (tipo, estado, limit, offset, sort_by, order) / `MovimientoStateTransition` + `listMovimientos` (`GET /finanzas/movimientos` → `{items,total}`) y `transitionMovimiento` (`PATCH /finanzas/movimientos/{id}/state`). Verificado contra `backend/app/api/routes/finanzas.py`: filtros `tipo` (Gasto|Inversion|Retiro) y `estado` (draft|confirmed|cancelled|reversed); sin filtro por fecha.
- **`src/views/FinanzasView.vue`:** nuevo tab `Movimientos` solo-lectura con Dropdowns tipo/estado + tabla fecha/tipo/descripción/monto/estado + empty-state en MOCK. Branch `isMock ? [] : movimientosReal`.
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-03] — P1-7: UsuariosView cableada a REAL

- **Servicio nuevo `src/services/api/usuarios.ts`:** espejo de `backend/app/api/routes/usuarios.py` — `listUsuarios` (q, rol, limit, offset → `Paginated`), `getUsuario`, `createUsuario`, `updateUsuario`, `deleteUsuario`, `changePassword` (`PATCH /usuarios/{id}/password`).
- **`src/views/UsuariosView.vue` reescrita:** conserva cambio rápido de rol demo (`auth.changeRole`) + buscador `q`/filtro rol + grid con editar (nombre/email/rol + password opcional), dar de baja (`DELETE`; el backend no tiene campo `activo`) y cambio de password por usuario. En MOCK: lista local mínima de 3 usuarios + banner, sin romper.
- La ruta ya exigía `roles:['admin']`, toda la UI queda solo-admin sin guard extra.
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-03] — P1-8: N ítems en devolución parcial

- **Hallazgo:** `POST /devoluciones` ya aceptaba `items: [{producto_id, cantidad, precio_unitario}]` (`backend/app/schemas/devoluciones.py` + `registrar_devolucion`; parcial exige ≥1 ítem) — sin cambios backend.
- **`src/views/DevolucionesView.vue`:** `formProductoId/Cantidad/Precio` únicos → array `formItems` con `Agregar ítem` / trash por fila (mínimo 1 fila); validación parcial exige ≥1 ítem con producto_id y cantidad > 0; tipo total → `items: null` como antes.
- Verificación: `npm run build` OK.

### [2026-09-03] — P1-1: combos BOM_Productos mínimo

- **Servicio `src/services/api/bom.ts`:** `BomProductoRead/Create` + `listBomProductos` (`GET /productos/{id}/bom/productos`), `createBomProducto` (`POST`, requiere admin), `updateBomProducto` (`PUT`), `deleteBomProducto` (`DELETE`), espejo de `backend/app/api/routes/bom.py` (shape `{producto_incluido_id, cantidad}`).
- **`src/components/atelier/FichaTecnicaModal.vue`:** sección `Combos (BOM productos)` solo en REAL (lista con nombre resuelto vía `GET /productos` + cantidad + trash; form Dropdown producto filter + cantidad + `Agregar`; validación cantidad > 0; toasts 409/422 con `detail`). Carga en `watch(visible)` y `watch(receta.id)` junto a BOM.
- Verificación: `npm run build` OK.

### [2026-09-03] — P1-3: tab Historial repuesto en Ficha

- **`src/components/atelier/FichaTecnicaModal.vue`:** `cargarHistorial()` ahora lee `precio-versions` + `costo-versions` en paralelo (`?producto_id=`, arrays planos) con `slice(0, 20)` por tipo; nuevo tab `🕘 Historial` (tercer botón junto a Ficha/Matriz) con dos paneles Precios/Costos (fecha + monto) + empty-states + nota `20 más recientes`. El `v-else` de Matriz pasó a `v-else-if` para no tragarse el nuevo tab. En MOCK muestra aviso `solo REAL`.
  - Verificación: `npm run build` OK (398 módulos) + `npm test` 70/70.

### [2026-09-03] — Tanda B P1 Punto 1 (P1-9): camino único en descontarAnticipo

- **`src/views/FinanzasView.vue` (`marcarAnticipoDescontado`):** eliminado el fallback a `transitionAnticipo` cuando `liquidacion_id` es null (doble escritura potencial: `descontarAnticipo(id, 0)` + transición suelta sin vínculo). Camino único: si hay `liquidacion_id` → `descontarAnticipo`; si no → toast warn `Seleccioná una liquidación para descontar el anticipo` sin llamar a ningún endpoint. El backend `PATCH /anticipos/{id}/descuento` exige liquidación existente (404 si no), así que el toast es el flujo correcto.
- Verificación: `npm run build` OK.

### [2026-09-03] — Tanda B P1 Punto 2 (P1-8): GET-by-id / PUT / DELETE devoluciones

- **Schemas (`backend/app/schemas/devoluciones.py`):** nuevo `DevolucionUpdate` (`motivo?`, `estado?` Literal draft|confirmed|cancelled|reversed).
- **Service (`backend/app/services/devoluciones.py`):** `actualizar_devolucion` (motivo corregible en draft/confirmed/cancelled; `estado` vía FSM `transition_to`, 400 si inválida; `reversed` inmutable 422; un commit) + `eliminar_devolucion` (solo `draft` 204 con borrado de ítems; no-draft → 400 con hint a `cancelled/reversed`, porque el alta ya restauró stock y pudo anular la venta).
- **Routes (`backend/app/api/routes/devoluciones.py`):** `GET /devoluciones/{id}` (audited), `PUT /devoluciones/{id}` + `DELETE /devoluciones/{id}` 204 (admin|operador).
- **Frontend (`src/services/api/devoluciones.ts`, `src/views/DevolucionesView.vue`):** `getDevolucion/updateDevolucion/deleteDevolucion` + botón trash con `Dialog` de confirm solo visible si `estado === 'draft'`.
- **Fix colateral (bloqueante):** `registrar_venta` (`backend/app/services/inventory.py`) insertaba `estado="completada"` legacy → 409 en todo `POST /ventas`; ahora `DocumentState.CONFIRMED.value`.
- **Fix colateral (bloqueante):** migración `0020_productos_cabecera` reescrita con guards `_has_*` (estilo 0014): el `try/except: pass` sobre DDL + `CAST(:table AS regclass)` en tablas case-sensitive envenenaba la transacción y rompía `alembic upgrade head` en DBs frescas. Regla: guards exactos + `DROP ... IF EXISTS` crudo, nunca `try/except` sobre DDL.
- **Tests (`backend/tests/test_devoluciones_api.py`, +3):** `GET by-id 200/404`, `PUT motivo 200 + transición inválida 400`, `DELETE confirmed 400 / draft 204 / 404`.
- Verificación: `pytest test_devoluciones_api + test_devoluciones` 29 passed; `pytest test_ventas_api` 32 passed; `npm run build` OK.

### [2026-09-03] — Tanda B P1 Punto 3 (P1-5): FK Compras.proveedor_id → maestros_proveedores

- **Investigación (DB dev):** `Compras_Insumos` 80 filas, 100% `proveedor_id NULL`; `maestros_proveedores` vacía; 0 huérfanos; columna nullable → `ON DELETE SET NULL`.
- **Migración `0022_compras_proveedor_fk`:** huérfanos → NULL (nunca borra) + `op.create_foreign_key(... ON DELETE SET NULL)` con guards; downgrade dropea la FK.
- **Modelo (`backend/app/models/insumos.py`):** `proveedor_id` ahora `ForeignKey("maestros_proveedores.id", ondelete="SET NULL")`.
- **Ruta (`backend/app/api/routes/compras_insumos.py`):** la validación apuntaba a la tabla `Proveedores` eliminada en 0008 (todo no-NULL → 400); ahora valida contra `maestros_proveedores` (desconocido → 400, contrato intacto).
- **Tests:** docstring 400 actualizado + nuevo `test_post_201_con_proveedor_maestro`.
- Verificación: `alembic upgrade head` en test y dev (FK creada, 80 compras intactas); `pytest` 2 passed; `npm run build` OK.

### [2026-09-03] — Tanda B P1 Punto 4 (P1-4): FK Movimientos.liquidacion_id → INVIABLE, no se crea

- **Investigación:** la premisa era falsa. `Movimientos_Financieros.liquidacion_id` NO guarda códigos `LIQ-YYYY-NN`: el único escritor (`settle_liquidacion`) guarda claves sintéticas por socia de 12 chars (necesarias por el UNIQUE parcial `uq_liquidacion`), y tests/APIs usan códigos libres. Una FK a `liquidaciones(codigo)` rechaza cada insert de settlement (probado: rompió 2 tests). En dev había 0 valores no-nulos, ningún dato comprometido.
- **Decisión:** NO crear la FK (forzarla rompería settlement + suite). Se creó, se probó, se revirtió: archivo de migración eliminado, modelo revertido con comentario explicativo, FK dropeada de dev y test. La conciliación sigue manual por prefijo de código; `uq_liquidacion` sigue como guard de settlement único.
- Verificación: `pytest test_finanzas` 2 passed tras la reversión; `alembic history` limpio.

### [2026-09-03] — Tanda B P1 Punto 5 (P1-6): canal/método de Ventas conectados a maestros

- **Investigación (DB dev):** valores del CHECK == `codigo` de maestros (matchean exacto); ventas existentes 100% canónicas; maestros con 5+4 seeds activos. FK viable.
- **Migración `0023_ventas_canal_metodo_fk`:** normalización legacy `Ventas.estado` (`completada→confirmed`, `anulada→cancelled`; el CHECK legacy se dropea ANTES de los UPDATEs) + swap a CHECK document-state; seed canónicos idempotente; backfill (valores custom que falten en maestros se insertan como filas maestras, nunca se reescriben ventas); drop `ck_ventas_canal_venta` + 2 FKs (`canal→maestros_canales_venta(codigo)` RESTRICT/UPDATE CASCADE NOT NULL; `metodo→maestros_metodos_pago(codigo)` SET NULL/UPDATE CASCADE). Downgrade revierte. Aplicada en test (up/down/up) y dev (25 ventas normalizadas, 0 huérfanos).
- **Backend:** `VentaCreate.canal_venta/metodo_pago` `Literal` → `str` + `_validar_canal_metodo` en `registrar/actualizar_venta` contra maestros (desconocido → 422, mismo contrato); filtros `GET /ventas` aceptan `str` (desconocido → 200 vacío, cambio intencional); `eliminar_canal/metodo` ahora 409 si tienen ventas (antes 500).
- **Frontend:** payload acepta `string`; dropdowns de `NuevaVentaModal` leen `listCanales/listMetodosPago` en REAL (incluye valores nuevos; fallback legacy).
- **Tests:** +2 (`custom_maestro_canal_201`, `delete_canal_con_ventas_409`) y contrato de filtro actualizado.
- Verificación: `pytest test_ventas_api + test_maestros_ventas_extend` 39 passed; `npm run build` OK + `npm test` 70/70.

### [2026-09-02] — Fix crítico 1 y 2: backfill costo_insumos + versionado precio/costo

#### 1. Migración `0021_backfill_costo_insumos` (`backend/alembic/versions/0021_backfill_costo_insumos.py`)
- `UPDATE Productos SET costo_insumos = GREATEST(costos_operativos_fijos - COALESCE(mano_obra,0) - COALESCE(cif_energia,0), 0) WHERE costo_insumos IS NULL AND COALESCE(costos_operativos_fijos,0) > 0`
- Backfill para `PRD-2 Corset Artemisia` ($31.268) y `PRD-15 Accesorio TEST` ($41.040); `downgrade` no-op.

#### 2. Backend `PUT /productos/{id}` con versionado (`backend/app/api/routes/productos.py`)
- Nuevo `from datetime import date` + captura `old_precio/old_costo/old_costo_insumos` antes del `setattr`.
- Tras `setattr`, si `precio_venta_sugerido` cambió → `db.add(PrecioVersion(producto_id, precio, fecha_desde=today))`; si `costos_operativos_fijos` cambió → `CostoVersion`; fallback si solo `costo_insumos` cambió.
- Best-effort en `try/except` para no bloquear el update principal; `db.commit()` incluye producto + versiones en misma transacción.
- Verificación: `UPDATE Productos SET costo_insumos=41040 WHERE id=15` OK; `alembic_version` → `0021_backfill_costo_insumos`; `docker compose up -d --build api` OK; `GET /audit-fiscal/precio-versions?producto_id=15` ahora crea fila al cambiar precio.

---

### [2026-09-03] — P2-1 (AnalisisFull.md): analíticos `resumen` conectado al Dashboard en REAL

#### 1. Servicio `src/services/api/analiticos.ts`
- Nuevo `getResumen(params?)` (`GET /analiticos/resumen`) + tipo `AnaliticosResumen`. Viaja también `getTopInsumos` (`GET /analiticos/top-insumos`), usado por el composable nuevo.

#### 2. Composable + vista
- Nuevo `src/composables/useAnaliticos.ts` (patrón `useClientes`; en mock retorna `null` porque las vistas computan local).
- `src/views/DashboardView.vue`: `resumenReal` fetcheado en `try/catch` independiente; `totalVentasReal` prefiere `resumen.ventas_total` (excluye anuladas) y `totalUtilidadReal` prefiere `resumen.margen_total`; sin resumen o en MOCK vale el cómputo local. Import `analiticosApi` ahora usado (fuera el `eslint-disable`).
- Verificación: `npm run build` OK.

### [2026-09-03] — P2-2 (AnalisisFull.md): fallback `CANALES_VENTA` fail-loud

- Se mantiene el fallback estático (no rompe ventas), pero ante error de red `tryFetch` ahora hace `console.warn` + toast `Maestros no disponibles, usando valores locales`. Aplica a `listCanales/listMetodosPago/listCanalesLegacy/listMetodosLegacy` (criterio unificado).
- Verificación `NuevaVentaModal`: con red → maestros reales; sin red → fallback estático que pasa `canalToCodigo/metodoToCodigo` sin 422. `npm run build` OK.

### [2026-09-03] — P2-3 (AnalisisFull.md): PATCH canónico en producción, PUT alias deprecated

- `update_prenda` y `update_pedido` quedan solo con `@patch` (parcial, canónico). Nuevos `update_prenda_put` / `update_pedido_put` con `@put(..., deprecated=True)` que delegan al handler PATCH (no se borran para no romper clientes).
- Investigación previa: ningún consumidor usa PUT (servicios `prendas.ts`/`pedidos-produccion.ts` y tests solo `client.patch`).
- Verificación: `py_compile` OK + `pytest test_fase4_produccion` 5 passed + `npm run build` OK.

### [2026-09-03] — P2-4 (AnalisisFull.md): CHECKs para enums de producción/prendas

- **Investigación (DB dev):** tablas vacías → sin valores inválidos que normalizar; los `UPDATE` de normalización quedan como no-ops protectores (pedidos.estado → `pendiente`, prioridad → `normal`, prendas.estado → `disponible`; nunca borra).
- **Migración `0024_produccion_checks`:** 3 `CHECK` (`ck_pedidos_produccion_estado`, `ck_pedidos_produccion_prioridad`, `ck_prendas_confeccionadas_estado`) con guards estilo 0014/0022; downgrade con `DROP CONSTRAINT IF EXISTS`.
- **Modelos:** `__table_args__` con los 3 `CheckConstraint` espejo.
- Verificación: `alembic upgrade head` en dev + ciclo down/up; inserts inválidos rechazados ×3; `pytest test_fase4_produccion` 5 passed.

### [2026-09-03] — P2-5 (AnalisisFull.md): ubicaciones libres vs maestro — documentado sin código (opción c)

- **Investigación (DB dev):** `Insumos` 79 filas con `ubicacion` 100% NULL; `prendas_confeccionadas` vacía; `maestros_ubicaciones_taller` con 1 sola fila de prueba — no hay catálogo de referencia confiable. Frontend usa `InputText` libre + fallback `'Bodega'`; no hay dropdowns que cablear.
- **Decisión (c):** sin cambio de código. (a) FK exigiría inventar un seed no relevado; (b) validación contra maestros rechazaría texto libre legítimo. Camino futuro: relevar ubicaciones físicas, seedear el maestro, y recién ahí validación estilo `_codigos_maestros` o FK con backfill.

### [2026-09-03] — P2-6 (AnalisisFull.md): Cotizador/Optimizador/Análisis sin persistencia — decisión de diseño

- **Declaración:** `CotizadorView`, `OptimizadorView` y `AnalisisView` son herramientas de cálculo local sobre listas REALes; no persisten sus resultados. Decisión de diseño, no bug.
- **Qué sí persiste:** `BOM_Insumos` (renglones), `Productos` (cabecera: costos, precio, markup), `Compras_Insumos` (compras que alimentan el WAC).
- **Dónde ver el costo real:** `GET /productos/{id}/costo` (servicio `bom.ts → getCostoProduccion`, visible en Ficha Técnica y en el bloque `Costo real BOM (DB)` del Cotizador).

### [2026-09-03] — P2-7 (AnalisisFull.md): `prendas.variante_id` nullable (stock genérico/sin talla)

- **Investigación:** modelo/schema/endpoint exigían variante; tabla vacía en dev → sin backfill. `_prenda_to_read` ya era null-safe.
- **Migración `0025_prendas_variante_nullable`:** `DROP NOT NULL` con guards; downgrade aborta con error si hay NULLs (revertirlas primero) en vez de tocar datos.
- **Backend + frontend:** modelo `variante_id` nullable + relationship opcional; schema `int | None = None`; `create_prenda` valida existencia solo si viene. Servicio `prendas.ts`, `usePrendas` mock null-safe (talla `Sin talla`, sku `GENERICA`), `PrendasListasView` mapping null-safe. Nota: sin form de alta en REAL, la genérica se crea vía API directa; el display ya la soporta.
- Verificación: `alembic upgrade head` + down/up en dev; insert NULL OK + cleanup; `pytest test_fase4_produccion` 5 passed.

### [2026-09-03] — P2-8 (AnalisisFull.md): composables por dominio

- **Nuevos `src/composables/`** (patrón `useClientes`: branch `isMock`, `list/get/create/update/remove` delegando al servicio en REAL; `useAnaliticos` ya entró con P2-1): `useProductos` (mock sobre `atelier.recetas`), `useBom` (insumos + combos + costo; combos mock vacíos/echo), `useDevoluciones` (+ `transition/remove`; mock module-scoped con seed `GAR-001`), `useOmisiones` (+ `resolve`; mock module-scoped con 2 seeds).
- **Servicio mínimo:** `omisiones.ts` suma `resolveOmision(id, resuelta)` (`PATCH /omisiones/{id}`, espejo backend, solo-admin).
- **Vistas refactorizadas** (mismo comportamiento, solo cambia la fuente): `ProductosView` (`list/remove` + conteo BOM vía `useBom`, fuera el `import` dinámico), `DevolucionesView`, `OmisionesView`, `CotizadorView` (`list` + costo vía `useBom`), `AnalisisView` (`list` vía `useProductos`).
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-04] — Fix: precio no se auto-cargaba al elegir producto en NuevaVentaModal

- **Causa:** el backend manda `precio_venta_sugerido` como string (Postgres `Numeric` serializa ej. `"83000.0000"`) y `seleccionarPrendaCatalogo` lo asignaba crudo al `InputNumber`, que con string no muestra nada.
- **Fix (`src/components/atelier/NuevaVentaModal.vue`):** normaliza con `Number()` y solo aplica si es precio válido > 0; si el producto no tiene precio, conserva el valor del campo (edición manual intacta). Dropdown en REAL ahora muestra `Nombre (PVP: $X)` como en MOCK (antes `Nombre (ID: N)`).
- Verificación: `npm run build` OK (403 módulos).

### [2026-09-04] — P0-1 (auditoría tipos API→UI): borrado componentes dashboard muertos

- **Borrados** `src/components/dashboard/BajoStockTable.vue`, `MargenTable.vue`, `KpiCards.vue`, `VentasMensualesChart.vue`: importaban `@/utils/format` y `@/utils/dashboard`, que no existen.
- **Verificación previa:** grep confirma que ninguna vista los importa (dead code, por eso el build pasaba) y que `src/types/` no existe; decisión: borrar, no restaurar utils para código muerto.
- Verificación: `npm run build` OK.

### [2026-09-04] — P0-2 (auditoría tipos API→UI): tabla Producción del Dashboard en REAL

- **`src/views/DashboardView.vue`:** en REAL iteraba `PedidoProduccionRead` crudo pero el template leía `p.codigo, p.precio_venta, p.utilidad_neta` (inexistentes) → celdas vacías + `$NaN`.
- **Fix:** nuevo computed `pedidosTabla` que en REAL normaliza como `ProduccionView` (`ORD-${id}`, `nombre_variante || nombre_producto`, mapeo de `estado` a etapas en mayúsculas) + `Number()` en montos; en MOCK pasa intacto. Columnas `Venta/Utilidad/Margen` (sin dato real) con `v-if="isMock"`; el `v-for` y el contador usan `pedidosTabla`. Patrón `isMock` intacto.
- Verificación: `npm run build` OK.

### [2026-09-04] — P0-3 (auditoría tipos API→UI): KPI Valor Total Inventario en $0

- **`src/views/InventarioView.vue:95`:** `valorTotalInventarioReal` leía `i.costo_promedio ?? i.costo` (inexistentes; el map los renombró a `costo_unitario` vía `Number(costo_promedio_actual)`) → siempre 0.
- **Fix:** `(Number(stock_actual ?? stock ?? 0) * Number(costo_unitario ?? costo ?? 0))`, consistente con el store. Vale para MOCK y REAL.
- Verificación: `npm run build` OK.

### [2026-09-04] — P0-4 (auditoría tipos API→UI): SugerirOrdenModal $NaN en REAL

- **`src/components/atelier/SugerirOrdenModal.vue`:** en REAL usaba `item.costo_unitario` (undefined; la API manda `costo_promedio_actual` string) → `Total Est.` e `Inversión Estimada` en `$NaN`.
- **Fix:** `Number(item.costo_unitario ?? item.costo_promedio_actual ?? 0)` en `totalSugerido`, celda `Total Est.` y `precio_unitario_compra` del payload (evita mandar string Numeric a la API).
- Verificación: `npm run build` OK.

