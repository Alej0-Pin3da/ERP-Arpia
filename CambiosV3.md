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

---

### Instrucción de Mantenimiento Continuo
A partir de esta versión (V3), cada cambio, ajuste de lógica, nuevo componente o funcionalidad agregada en el proyecto será documentada en este archivo `CambiosV3.md` con su respectiva fecha, archivo modificado y resumen operativo.
