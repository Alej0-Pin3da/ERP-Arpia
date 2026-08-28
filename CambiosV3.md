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

### Instrucción de Mantenimiento Continuo
A partir de esta versión (V3), cada cambio, ajuste de lógica, nuevo componente o funcionalidad agregada en el proyecto será documentada en este archivo `CambiosV3.md` con su respectiva fecha, archivo modificado y resumen operativo.
