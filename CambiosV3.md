# Registro de Cambios y Evolución - Versión 3 (V3)
## Atelier Arpía — ERP & Sistema Integral de Confección de Autor

Este documento registra cronológica y detalladamente todas las modificaciones, nuevas funcionalidades, módulos maestros, correcciones y expansiones integradas a partir de la versión 3 (V3).

### [2026-09-15] - Lote por cantidad slice 2 (frontend): stepper de 5 fases + stock visible (ruta directa, sin commit)

- **Alcance:** solo `src/`; backend intacto (slice 1 en 582b113). Sin endpoints nuevos, sin mocks, tipos extendidos sobre los existentes.
- **Tipos API:** `PedidoProduccionRead` suma `fase` (requerido) + `costo_unitario_snapshot?`; `CreatePayload` suma `fase?`; `ListPedidosProduccionParams` suma `fase?` (`?fase=`). Nuevo `FASES_PRODUCCION` (orden canónico corte→costura→acabados→calidad→listo, espejo del backend), `siguienteFase()` y `extractApiDetail()` (detail string o array de validación, verbatim). `ProductoRead/Update` suman `stock_actual?`.
- **ProduccionView:** kanban de 8 columnas ficticias → 5 columnas reales (CORTE/COSTURA/ACABADOS/CALIDAD/LISTO) keyed por `fase`; chips de filtro por fase (`Todas` + 5, vía `?fase=`); avance de un paso con `PATCH {fase}` (botón "Avanzar fase →", sin retroceso — el backend lo 400); tarjetas/filas/cards muestran `cantidad_producida/cantidad` + snapshot de costo solo cuando el backend lo trae; errores 400/422/409 en toast con el string del backend tal cual (incluye el detalle por-insumo del 409).
- **DetallePedidoTallerModal:** nueva sección "Fase de confección & avance de lote" con stepper 1–5, fase actual, lote `producida/cantidad`, snapshot de costo y botón Avanzar con error inline verbatim; emite `fase-avanzada` y el padre recarga. Estados vacíos honestos SOLO para lo que sigue sin endpoint (tiempos por fase, pruebas de calce, anticipos) con nota pendiente.
- **ProductosView:** badge "📦 N uds stock" por receta solo cuando `stock_actual` está presente. Mocks de `useProduccion.test.ts` acreditados con `fase`.
- **Verificación:** `npm run build` OK (vite 409 módulos + server bundle); `vitest run src/composables/useProduccion.test.ts` 2/2; eslint en 6 archivos tocados: 9 errores + 2 warnings, todos preexistentes en HEAD (el slice elimina 2: `formatCOP` sin uso y `any` en el map de pedidos). Sin commit (árbol dirty).
- **Archivos:** `src/views/ProduccionView.vue`, `src/components/atelier/DetallePedidoTallerModal.vue`, `src/views/ProductosView.vue`, `src/services/api/pedidos-produccion.ts`, `src/services/api/productos.ts`, `src/composables/useProduccion.test.ts`.

### [2026-09-14] - Lote por cantidad slice 1 (backend): fases Corte→Listo + stock por cantidad (ruta directa)

- **Decisión acordada:** stock por columna de cantidad (`Productos.stock_actual`), SIN filas por prenda. `PrendaConfeccionada` intacta.
- **Modelos + migración `0030_produccion_fase_stock`** (head sobre `0029_purge_ghost_oct25`): `Productos.stock_actual` NUMERIC(15,4) NOT NULL DEFAULT 0; `pedidos_produccion.fase` VARCHAR(20) DEFAULT 'corte' + CHECK (corte|costura|acabados|calidad|listo); `pedidos_produccion.costo_unitario_snapshot` NUMERIC(15,4) NULL. Esquemas exponen `stock_actual` (Base/Update/Read) y `fase` + `costo_unitario_snapshot` (Read).
- **Transacción de cierre** (`backend/app/services/produccion.py::completar_lote`, sin commit propio): explosión BOM × N vía `explosion_materiales`, chequeo previo con detalle por-insumo, `descontar_stock` (FOR UPDATE), `producto.stock_actual += N`, snapshot de costo unitario (`calcular_costo_produccion`) + `cantidad_producida = N`. `PATCH /pedidos-produccion/{id}` valida avance secuencial (422 fase inválida, 400 salto/retroceso), filtra/ordena por `fase`, y corre el lote UNA vez al transicionar a `listo`/`completado` (409 atómico con `{"detail": "Stock insuficiente para completar el lote: 'Tela X' (requiere A, disponible B); ..."}`).
- **Ventas** (`inventory.py::registrar_venta/actualizar_venta/anular_venta`): también mueven `Producto.stock_actual` (409 si no alcanza en venta, NULL tratado como 0; anular repone). Disciplina lock-first: se bloquean productos ANTES de mutar insumos porque un `db.get(..., populate_existing=True)` posterior refresca en cascada el chain selectin y BORRA deducciones pendientes (bug real encontrado por los tests nuevos, verificado empíricamente).
- **Tests:** nuevo `backend/tests/test_produccion_lote.py` (6 tests: defaults, secuencial+rechazos, cierre con snapshot, 409 atómico, idempotencia, venta consume/anula repone); fábricas de `test_ventas_api/inventory/devoluciones(_api)/pr2/audit` acreditadas con `stock_actual=10000` (las ventas ahora exigen stock).
- **Verificación:** `py_compile` OK; ruff sin violaciones nuevas (I001/F401/E501 restantes preexistentes, verificados contra HEAD); `configure_mappers()` OK; migración 0030 aplica vía `alembic upgrade head`; pytest: 6/6 lote + 42/42 (fase4/productos/lote/domain) + 44/44 migrate + suites ventas/inventario/devoluciones/pr2 121/123 (2 fallos por polución cruzada preexistente `.first()` sin orden en audit, reproducidos en HEAD limpio). Sin commit (árbol dirty). Sin cambios de frontend.
- **Archivos:** `backend/app/models/productos.py`, `backend/app/models/produccion.py`, `backend/app/schemas/producto.py`, `backend/app/schemas/produccion.py`, `backend/app/services/produccion.py` (nuevo), `backend/app/services/inventory.py`, `backend/app/api/routes/produccion.py`, `backend/alembic/versions/0030_produccion_fase_stock.py` (nuevo), `backend/tests/test_produccion_lote.py` (nuevo) + 6 fábricas de tests.
- **Siguiente slice:** UI frontend de lote (avance de fase + tratamientos 400/422/409).

### [2026-09-13] - Purga de datos quemados: respuestas estáticas y fallbacks reemplazados por flujo REAL (ruta directa)

- **Auditoría & Limpieza:** Reemplazados datos simulados/estáticos en 14 componentes por estados vacíos explícitos o datos reales consumidos de API.
- **DetallePedidoTallerModal:** Fases de modistería, tiempos y pruebas de calce inventadas reemplazadas por estado vacío "Sin registro de tiempos — pendiente".
- **OptimizadorView:** Esquema visual de tendido y monetización de retazos convertidos en dinámicos basados en la tela e insumos reales cargados.
- **NotificacionesModal, DashboardView, Auth, LoginView, EtiquetaPrenda:** Eliminados fallbacks ficticios y cuentas demo; todas las vistas consumen exclusivamente de FastAPI/Postgres.
- Verificación: `npm run build` OK + 36/36 tests.

### [2026-09-13] - Fix start-all.ps1: scripts mock eliminados (post-purge)

- **Causa:** el purge borró `start:real`/`dev:real` de `package.json` pero `start-all.ps1` los seguía invocando → `npm error Missing script` al final del arranque (DB + API + build OK, solo fallaba lanzar el front).
- **Fix:** `start:real`→`start`, `dev:real`→`dev`; restos `USE_MOCK=false` y menciones en comentarios eliminados. Sintaxis PS verificada, sin más referencias mock.

### [2026-09-13] - Purge total del mock: app 100% REAL-only (strangler completo)

- **Alcance:** 68 archivos, +1447/−9229. Adapters (10 composables) sin ramas `isMock`; 16 vistas + layout + 20 modales colapsados a REAL; eliminados `atelier.ts` (3411), `mockApi.ts` (970), `mockGuard.ts`, `check-mock-leak.mjs`; `server.ts` y `vite.config.ts` proxy-only; badges y `useMode` estáticos en REAL; tests reescritos a REAL-only (36/36).
- **Consecuencia:** `npm run dev` exige FastAPI + Postgres; `USE_MOCK` es no-op. Gaps REAL expuestos y documentados (sin endpoint pago-por-socia, sin montos en pedidos, stock prendas solo vía Ingresar Prenda).
- Verificación: build OK + 36/36 tests. Slices previos: b33b48c, 037c9d9.

### [2026-09-13] - Mock slice 2: useAnaliticos a REAL-only (strangler por módulos)

- **Slice 2:** 7 guards `if (isMock) return null` eliminados en los 7 getters; el path REAL ya delegaba completo a `/analiticos/*`, firmas intactas. `isMock` queda como passthrough informativo (su remoción va en slice posterior).
- Verificación: build OK + 70/70 tests.

### [2026-09-13] - Mock slice 1: Devoluciones + Omisiones a REAL-only (strangler por módulos)

- **Estrategia:** el mock es dual-path en ~50 archivos (~6500 líneas) con default mock-ON — big-bang rompería todo. Strangler por dominio, un slice por cambio.
- **Slice 1:** `useDevoluciones.ts` (121→47 líneas) y `useOmisiones.ts` (79→28) sin seeds ni ramas `isMock`; firmas intactas. `OmisionesView` ajusta import de tipo a `any[]` (sus 2 filas locales van en el slice de vista).
- Verificación: build OK + 70/70 tests. Siguiente: un dominio por slice.

### [2026-09-13] - MANUAL_USUARIO.md: manual de uso completo del ERP (ruta delegada directa)

- **Alta:** `MANUAL_USUARIO.md` (~24KB) con los 16 módulos — qué es, cómo llegar, paso a paso con nombres exactos de botones/modales, roles y tips. Español neutro, estructura por tareas (skill cognitive-doc-design).
- Puntos mock-vs-real documentados (precios ocultos en REAL, Editar solo admin, etc.).

### [2026-09-12] - Patrón compartido ResponsiveTable + CSS utilities, piloto Inventario/Ventas (ruta delegada directa)

- **Deuda:** 23 tablas duplicadas desktop + cards (cambio futuro x2). Nuevo `src/components/ResponsiveTable.vue` (slots `#desktop`/`#mobile`, prop `minWidth`) + utilidades `.table-scroll`/`.th-sticky`/`.rt-mobile` en `main.css`.
- **Piloto:** Inventario y Ventas migrados verbatim (sorting, filtros y handlers intactos). Resto (9 vistas + 7 modales) con guía de migración en el componente, uno por cambio.
- Verificación: `npm run build` OK.

### [2026-09-12] - Higiene repo: ignora .idea/, CSV VALQUI y DDL.sql (ruta directa)

- **Problema:** `git status` con ruido — `.idea/` parcialmente ignorado (lista frágil por archivo), CSV de trabajo y dump local `DDL.sql` (43KB, lo canónico es alembic) como untracked.
- **Fix:** `.gitignore` con `.idea/` completo, `ARPIA - INVERSION VALQUI (1).csv` + `*.csv`, `DDL.sql`. Status limpio.

### [2026-09-11] - Fix corte derecho global: grid blowout + header + overflow-x clip (ruta delegada directa)

- **Causa:** `grid-template-columns: 268px 1fr` (`1fr` = `minmax(auto,1fr)`) sin `min-width:0` en header/main/wrapper + header flex sin shrink + sin contención `overflow-x` a nivel página → cualquier hijo ancho estiraba el viewport a 360px en todas las vistas.
- **Fix shell:** grid a `minmax(0,1fr)`, `min-width:0`/`max-width:100%` en header/main/wrapper, `overflow-x:clip` en main/wrapper y `html/body` (preserva sticky), header con truncate/breadcrumbs ellipsis, en mobile padding `1rem`, gap `.5rem`, labels de logout/rol compactados con `aria-label`. Toast con `max-w-[calc(100vw-3rem)]`.
- Verificación: `npm run build` OK (410 módulos). Sin tocar tablas/cards ni backend.

### [2026-09-11] - Híbrido responsive: tabla desktop + cards mobile sin scroll lateral (ruta delegada directa)

- **Feedback:** el patrón scroll + sticky seguía exigiendo desplazamiento lateral y texto `xs` demasiado chico en mobile.
- **Patrón híbrido:** tabla existente en `hidden md:block` (`hidden sm:block` en modales) + cards en `md:hidden` (`sm:hidden` en modales) con mismo `v-for`/computed y mismos handlers, sin duplicar lógica. Cards `rounded-2xl p-4` con título `text-sm` bold + código ámbar mono, secundarios `text-sm`, labels `text-xs uppercase`, dinero `font-mono text-sm bold`, botones `min-h-[40px]`. Sin `overflow-x-auto` ni `min-w` en mobile.
- **Alcance:** 23 tablas en 11 vistas + 7 modales (Inventario, Ventas, Finanzas x3, Auditoría x3, Omisiones, Devoluciones, Análisis, Dashboard, Producción, Maestros, PrendasListas + DetalleVenta, DetallePedido, NuevaLiquidación, SugerirOrden, OrdenCompra, FichaTécnica BOM+matriz, FichaTallas).
- Verificación: `npm run build` OK (410 módulos). Documentado sin tocar backend.

### [2026-09-11] - Responsive tablas: scroll horizontal + sticky primera columna en 11 vistas + 5 modales (ruta delegada directa)

- **Problema:** tablas nativas `<table>` sin lógica responsive; 3 vistas + 4 modales sin wrapper `overflow-x-auto` rompían el layout a 360-640px, el resto solo scrolleaba perdiendo contexto de fila.
- **Patrón unificado:** wrapper `rounded-2xl border overflow-hidden > overflow-x-auto`, tabla con `min-w-[640px]` (≤5 col) / `min-w-[760px]` (6-7 col) / `min-w-[900px]` (8+ col, Ventas/Inventario/Finanzas), primera columna `sticky left-0 z-10` con fondo stone opaco para mantener el identificador ámbar visible, `whitespace-nowrap` solo en dinero/estado/acciones, descripciones con `min-w-[180px]`. Sin columnas ocultas ni cards duplicadas, sin migrar a DataTable, kanban intacto.
- **Archivos:** Ventas, Inventario, Finanzas (3 tablas), Auditoría (3), Análisis, Dashboard, Omisiones, Producción (solo vista tabla), Maestros, Devoluciones, PrendasListas + modales DetalleVenta, SugerirOrden, FichaTécnica (BOM+matriz), FichaTallas, OrdenCompraProveedor.
- Verificación: `npm run build` OK (410 módulos). Sin tocar backend ni lógica.

### [2026-09-08] - Fix overlap campos numéricos + scrollbar horizontal en modales de insumo (ruta delegada directa)

- **Causa raíz:** el trío numérico (`Stock Actual/Stock Inicial`, `Stock Mínimo (Alerta)`, `Costo Unitario ($)`) usaba `grid sm:grid-cols-3` sin `min-w-0` en las celdas (los grid items con `min-width: auto` no encogen y el contenido empuja), y `class="w-full"` en `<InputNumber>` solo dimensiona el wrapper `.p-inputnumber` — el `<input>` interno de PrimeVue 4.5.5 conserva su ancho intrínseco (peor con formato moneda COP `$ 18.800`). En un diálogo de 640px con padding de 1.5rem cada columna queda en ~180px y los inputs se solapan; el desborde generaba el scrollbar horizontal.
- **`src/components/atelier/EditarInsumoModal.vue` + `src/components/atelier/NuevoInsumoModal.vue` (mismo fix en ambos, layout compartido):** celdas del trío y de los grids de 2 columnas con `min-w-0`; `input-class="w-full"` en los tres `InputNumber` (prop nativo v4, pasa la clase al `<input>` interno); labels del trío con `truncate` + `title` (texto español intacto, tooltip con el nombre completo); wrapper del contenido con `min-w-0 max-w-full overflow-x-hidden`; `Dialog` con `:breakpoints="{ '640px': '95vw' }"` y `:content-style="{ overflowX: 'hidden', maxWidth: '100%' }"`. Estilo stone/amber, validación, payloads y lógica modal intactos; código/comentarios en inglés, labels UI en español.
- Verificación: `npm run build` OK (410 módulos, ~3.4s). Sin tocar backend, mapping ni lógica de modales. Sin commit/push.

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

### [2026-09-04] — P0-5 (auditoría tipos API→UI): CotizadorView inputs vacíos

- **`src/views/CotizadorView.vue:80-86`:** `onRecetaChange` asignaba `tiempo_confeccion_min` (int|null) y `cif_energia/costo_insumos/markup_pct` (Numeric|null → string) crudos a `InputNumber`/slider → inputs vacíos (mismo patrón del bug de `NuevaVentaModal`).
- **Fix:** `Number(... ?? 0)` en cada asignación (tiempo, CIF, margen vía `Math.round(Number(...))`, precios vía `Math.round(Number(costo_insumos ?? 0) * factor)`).
- Verificación: `npm run build` OK.

### [2026-09-04] — P0-6 (auditoría tipos API→UI): ProduccionView $0 mentiroso en REAL

- **`src/views/ProduccionView.vue:28-41`:** el mapping hardcodea `precio_venta/costo/utilidad/margen = 0` porque `PedidoProduccionRead` no trae montos.
- **Decisión mínima:** sin join a productos (fuera de alcance); se ocultan en REAL con `v-if="isMock"` el bloque `Venta/Utilidad` de las cards Kanban y las columnas `Precio Venta/Utilidad Neta` de la vista tabla (+ comentario en el mapping). En MOCK todo visible como antes.
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-05] — P1-1 (auditoría tipos API→UI): types `number|string` en insumos/prendas

- **`src/services/api/insumos.ts`:** `stock_actual/stock_minimo/costo_promedio_actual` ahora `number | string` (Postgres Numeric serializa string).
- **`src/services/api/prendas.ts`:** `costo_real/precio_venta` ahora `number | string | null`.
- Los consumos ya normalizaban con `Number()` (`InventarioView`, `PrendasListasView`, `FichaTecnicaModal`); el type mentía `number` puro y ocultaba el patrón.
- Verificación: `npm run build` OK.

### [2026-09-05] — P1-2 (auditoría tipos API→UI): costo ficticio $25.000 en NuevaVentaModal

- **`src/components/atelier/NuevaVentaModal.vue:seleccionarPrendaCatalogo`:** `it.costo_unitario` quedaba en el default ficticio ($25.000) porque leía solo `p.costo_unitario` (inexistente en `ProductoRead` REAL).
- **Fix:** fallback `costo_unitario ?? costos_operativos_fijos ?? costo_insumos` normalizado con `Number()`, solo si es > 0 (edición manual intacta).
- Verificación: `npm run build` OK.

### [2026-09-05] — P1-3 (auditoría tipos API→UI): mano_obra/cif crudos + thresholds fijos en ProductosView

- **`src/views/ProductosView.vue`:** `mano_obra/cif_energia` se asignaban crudos (string Numeric o null) y `costo_total_unitario/precio_venta/costo_estimado_materiales` podían quedar string.
- **Fix:** `Number()` en cada campo del mapping; `margenColor()` usa `margenMetaGlobal` (`meta` / `meta+25`) en vez de thresholds fijos `35/60` (mismo bug que `AUDIT-FALLAS` ítem 5).
- Verificación: `npm run build` OK.

### [2026-09-05] — P2-1 (auditoría tipos API→UI): markup mostraba "60.00%"

- **`src/views/ProductosView.vue`:** la tarjeta mostraba `{{ r.markup_pct }}%` crudo (string Numeric `"60.00"`).
- **Fix:** `{{ Math.round(Number(r.markup_pct ?? 0)) }}%`.
- Verificación: `npm run build` OK.

### [2026-09-05] — P2-2 (auditoría tipos API→UI): AnalisisView con costo 0 y margen 100% ficticios

- **`src/views/AnalisisView.vue`:** en REAL `costo_estimado_materiales` hardcodeado en 0 (margen siempre 100%), `precio_venta_sugerido` crudo (string), y el filtro de stock crítico comparaba strings (`"5" <= "10"` lexicográfico = falso, alertas perdidas).
- **Fix:** mapping con `Number(p.costo_insumos ?? 0)`, `Number(p.precio_venta_sugerido ?? 0)`, tiempo derivado de `tiempo_confeccion_min`; filtro con `Number()`; template con `Number()` + guard de división por cero en el margen.
- Verificación: `npm run build` OK.

### [2026-09-05] — P2-3/P2-4 (auditoría tipos API→UI): proveedor vacío + filtro string en Dashboard/Sugerir

- **`src/views/DashboardView.vue` / `src/components/atelier/SugerirOrdenModal.vue`:** columna `{{ it.proveedor }}` vacía en REAL (`InsumoRead` no trae proveedor) y filtro de críticos con comparación lexicográfica de strings.
- **Fix:** fallback `it.proveedor ?? it.nombre_categoria ?? '—'`; filtros con `Number()` en ambos archivos.
- Verificación: `npm run build` OK.

### [2026-09-05] — P2-5 (auditoría tipos API→UI): Devoluciones fecha vacía y estado crudo

- **`src/views/DevolucionesView.vue`:** el mapping leía `d.creado_en` pero `DevolucionRead` manda `fecha` → fecha siempre vacía; `estado` mostraba el enum crudo (`draft`, `confirmed`…) con fallback inventado `'Registrada'`.
- **Fix:** `fecha: d.fecha ?? d.creado_en ?? d.created_at ?? ''`; estado conserva el enum real (el botón eliminar `draft` sigue funcionando) y el template muestra etiqueta (`Borrador/Confirmada/Anulada/Revertida`).
- Verificación: `npm run build` OK.

### [2026-09-05] — P2-6 (auditoría tipos API→UI): Cotizador mostraba "(null)"

- **`src/views/CotizadorView.vue:recetasOptions`:** label `` `${r.nombre} (${r.codigo})` `` con `codigo` null → `Nombre (null)`.
- **Fix:** fallback `r.codigo ?? \`PRD-${r.id}\``.
- Verificación: `npm run build` OK.

### [2026-09-05] — P2-7 (auditoría tipos API→UI): crash en EtiquetaPrenda con sku nulo

- **`src/components/atelier/EtiquetaPrendaModal.vue`:** `props.variante.sku.slice(-4)` rompía si `sku` era null/undefined (prenda genérica P2-7).
- **Fix:** `(props.variante.sku ?? '').slice(-4) || '0000'`; `formatCOP` acepta `number | string` con `Number()`.
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-05] — Fix funcional 1: "Ingresar prenda confeccionada" era un stub

- **Síntoma (`/prendas`):** el botón solo mostraba un toast ("Selecciona el modelo...") sin forma de elegir modelo.
- **Fix:** nuevo `src/components/atelier/IngresarPrendaModal.vue` — selector de modelo (catálogo REAL vía `useProductos` / recetas en MOCK), variante/talla (variantes REAL vía `GET /productos/{id}/variantes`, tallas en MOCK), unidades, costo, precio, estado y ubicación; crea N prendas vía `usePrendas.create` (ambos modos) con `POST /prendas-confeccionadas` en REAL. `PrendasListasView` abre el modal y recarga al guardar.
- Verificación: `npm run build` OK (405 módulos) + `npm test` 70/70.

### [2026-09-05] — Fix funcional 2: NuevoPedidoModal no cargaba datos reales ni creaba en REAL

- **Síntoma (`/produccion`):** dropdowns de clientas y recetas vacíos en REAL (`[]` hardcodeado) y guardar solo mostraba "Usá POST /pedidos-produccion". Bonus: la rama REAL de "nuevo cliente" retornaba una variable en TDZ (`return c as any` → ReferenceError).
- **Fix (`src/components/atelier/NuevoPedidoModal.vue`):** branch REAL completo — productos y clientas reales, variantes por producto, cantidad, estado/prioridad con los enums del backend (`pendiente/en_produccion`, `baja/normal/alta/urgente`), fecha de entrega y `POST /pedidos-produccion` vía `useProduccion.create` con manejo de `detail` 422. Selector de clienta y precios quedan MOCK-only (el modelo `pedidos_produccion` no tiene cliente ni montos — la clienta vive en CRM/Ventas). `ProduccionView` recarga la lista al crear (`@pedido-creado`).
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-05] — Fix funcional 3: mock leak `parametrosCosteo` en MaestrosView

- **Síntoma (`/maestros` en REAL):** toast "Mock leak detectado — atelier.parametrosCosteo leído en modo REAL". Causas: fallback `parametrosApi.value ?? store.parametrosCosteo` (se evalúa en REAL antes de que resuelva la API) e inicializador `ref({ ...store.parametrosCosteo })` en setup.
- **Fix:** constante local `PARAMETROS_COSTEO_DEFAULT` (espejo del seed) usada en ambos puntos; `restaurarParametrosDefecto` reutiliza la constante para no divergir.
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-05] — Fix P0-2 (auditoría funcional): transiciones de producción daban 422 en REAL

- **`src/views/ProduccionView.vue`:** el mapping convertía el estado a etapas MOCK (`COSTURA`...) y `avanzar/retrocederEstado` mandaban esa etapa al backend, cuyo CHECK solo acepta `pendiente/en_produccion/completado/cancelado` → toda transición REAL fallaba.
- **Fix:** el mapping guarda `estadoReal` (enum crudo) además de la etapa de display; avanzar/retroceden transicionan dentro del enum (`pendiente→en_produccion→completado`, cancelado terminal con aviso honesto).
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P0-11 (auditoría funcional): contadores de Análisis siempre en 0

- **`src/views/AnalisisView.vue`:** filtraba `estado === 'entregado'` y `['corte','confeccion','prueba']`, que no existen en ningún modo (MOCK usa mayúsculas, REAL el enum del backend); `!p.vendida` contaba todo en REAL (`PrendaRead` no trae `vendida`).
- **Fix:** normalización case-insensitive (`entregado/completado/listo` vs etapas activas de ambos modos); stock REAL = `estado === 'disponible'`.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P0-3 (auditoría funcional): NuevoInsumoModal crea en REAL

- **Antes:** toast "Creación de insumos vía Inventario API" sin persistir; además la UI mandaba `categoria` string y el backend exige `categoria_id: int`.
- **Fix (`src/components/atelier/NuevoInsumoModal.vue`):** dropdown de categorías reales (`GET /categorias-insumos`), `POST /insumos` vía `useInsumos().create` con `detail` de error, proveedor MOCK-only (el modelo no lo tiene) y `:loading` anti doble-submit.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P0-4 (auditoría funcional): CompraInsumoModal persistía solo en MOCK

- **Antes:** en REAL mostraba "Compra registrada" sin guardar nada.
- **Fix:** `POST /compras-insumos` vía `createCompraInsumo`, éxito solo si persiste, evento `compra-registrada` + `:loading`.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P0-7 (auditoría funcional): OrdenCompraProveedorModal vacía y ficticia en REAL

- **Antes:** operaba sobre `[]` (tabla vacía) y el "éxito" mutaba nada.
- **Fix:** en REAL carga `useInsumos().list()` con `Number()` y fallback de proveedor a categoría; confirma con `POST /compras-insumos` por fila (reporta `ok/total` + último error) en vez de mutar el mock.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P1-2 (auditoría funcional): InventarioView recarga tras modales

- **Antes:** ningún modal tenía handler → lista REAL desactualizada hasta refresh manual.
- **Fix:** `@insumo-creado/@compra-registrada` y reload al cerrar Sugerir/OrdenProveedor (`cargarInsumosReales` ya hace early-return en MOCK).
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P0-5 (auditoría funcional): falso "Pago Registrado" en REAL

- **`src/components/atelier/DetalleLiquidacionModal.vue`:** el toast de éxito se mostraba siempre aunque en REAL no se persistía nada (la API no tiene pago por socia, solo transición de la liquidación completa).
- **Fix:** éxito solo en MOCK; en REAL aviso honesto sin fingir persistencia.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P0-6/P0-8 (auditoría funcional): ficha de tallas persiste en REAL + códigos cortos

- **Antes:** `FichaTallasClienteModal` (y el muerto `MedidasAnatomicasModal`, borrado por no usarse en ningún lado) fingían guardado en REAL; además los valores `Sin Talla (Tote Bags)`/`Talla Unica / Surtido` (21 chars) violan `max_length=10` del backend → 422.
- **Fix:** nuevo `src/utils/tallas.ts` (`toTallaCode/fromTallaCode`: `SIN_TALLA`/`UNICA`); ficha guarda vía `PUT /clientes/:id` + reload en `ClientesView` (`onFichaGuardada`); `NuevoClienteModal` persiste códigos; contador `clientasSinTalla` reconoce ambos formatos.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P0-9 (auditoría funcional): periodo de liquidación daba 422

- **`src/components/atelier/NuevaLiquidacionModal.vue`:** el default `Liquidación Periodo septiembre de 2026` (~35 chars) viola `periodo max_length=20` → todo POST en REAL daba 422.
- **Fix:** default `YYYY-MM` + validación ≤20 antes de guardar + `maxlength` y placeholder en el input.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P1-5 (auditoría funcional): venta REAL con producto fantasma

- **`src/components/atelier/NuevaVentaModal.vue:472`:** `producto_id: it.producto_id ?? 1` inventaba el producto #1 cuando la fila no tenía catálogo.
- **Fix:** validación previa que exige producto de catálogo por fila (con n° de fila y nombre en el aviso) en vez del fallback.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P1-8 (auditoría funcional): tipo_cuenta se nulificaba en silencio

- **`src/components/atelier/GestionSociasModal.vue`:** texto libre ("Nequi", "Digital"...) que no matcheaba el Literal se mandaba `null` sin aviso.
- **Fix:** Dropdown `Ahorros/Corriente/Otra` en REAL (texto libre intacto en MOCK) + normalización al cargar + red de seguridad `toTipoLiteral`.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P0-12/P1-4 (auditoría funcional): anticipos con socia fantasma + edición muda

- **`src/components/atelier/NuevoAnticipoModal.vue`:** dropdown de socias vacío en REAL con default `socia_id: 2` (404/422 o socia equivocada); al editar en REAL, monto/concepto se descartaban en silencio.
- **Fix:** socias reales vía `useSocios().list()`, default a primera no-fondo sin id fantasma (validado antes del POST); al editar en REAL los campos no-estado se deshabilitan con aviso explícito.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P1-12 (auditoría funcional): +1/-1 de prendas era un PATCH vacío

- **`src/views/PrendasListasView.vue`:** en REAL hacía `update(id, {})` + toast de éxito sin cambiar nada (no hay endpoint de delta; cada fila es 1 unidad).
- **Fix:** botones deshabilitados en REAL con tooltip explicativo; el handler informa y recarga en vez de fingir.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P1-3/P1-11 (auditoría funcional): reload en Maestros + edición de liquidación

- **`src/views/MaestrosView.vue`:** única vista sin `watch(isMock)` → catálogo desactualizado al cambiar MOCK↔REAL. Fix: watcher que recarga.
- **`src/views/FinanzasView.vue` + `DetalleLiquidacionModal.vue`:** el botón "Editar liquidación" abría un form que en REAL nunca puede guardar (la API solo permite transición). Fix: oculto en REAL con aviso en el título.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P1-6/P2-6 (auditoría funcional): estados MOCK de devoluciones normalizados

- **`src/views/DevolucionesView.vue`:** el seed usaba `'En Modificación'` y las creadas `'Registrada'` → el botón eliminar (solo `draft`) nunca aparecía y las etiquetas bypasseaban el mapa.
- **Fix:** seed `confirmed`, nuevas `draft` (eliminar visible + etiquetas del mapa).
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P1-7 (auditoría funcional): WhatsApp de venta roto en REAL

- **`src/components/atelier/DetalleVentaModal.vue`:** `clienteVinculado` retornaba `null` en REAL (con el `if` duplicado) → link `wa.me/?text=` muerto.
- **Fix:** carga el cliente vía `useClientes().get()` en REAL; el botón se oculta si no hay teléfono.
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P1-10 (auditoría funcional): PATCH /omisiones sin UI

- **`src/views/OmisionesView.vue`:** `useOmisiones().resolve()` nunca se llamaba desde el template.
- **Fix:** columna Estado con badge `Resuelta` o botón `Resolver` (PATCH + reload, `solo-admin` con mensaje de permiso).
- Verificación: `npm run build` OK.

### [2026-09-05] — Fix P1-9 (auditoría funcional): confirmación antes de eliminar

- **Antes:** deletes de un clic en Clientas, Insumos, Recetas y los 7 maestros (sin try/catch en Maestros: un 409 quedaba en silencio).
- **Fix:** nuevo `src/components/ConfirmActionDialog.vue` compartido, cableado en `ClientesView`, `InventarioView`, `ProductosView` y `MaestrosView` (genérico por tipo con manejo de 409); los deletes ahora confirman y reportan loading/error.
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-05] — Fix P2-1 (auditoría funcional): mockGuard con nombres inexistentes

- **`src/utils/mockGuard.ts`:** vigilaba `categoriasColeccion/ubicacionesTaller/tallasEstandar/productosSinTalla`, pero el store expone esos con sufijo `Maestros` → el guard los salteaba en silencio (`if (!(prop in atelier)) return`).
- **Fix:** nombres exactos + cobertura de computadas (`totalVentas/totalUtilidad/rentabilidadPromedio/valorTotalInventario/distribucionSocias/pipelineCounts`).
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-05] - Pedido con clienta: `cliente_id` end-to-end (migración 0026)

- **Motivo:** el modal de pedido en REAL no permitía elegir clienta porque `pedidos_produccion` no tenía la columna (solo el mock la modelaba).
- **Backend:** migración `0026_pedidos_cliente_fk` (`cliente_id` nullable + FK a `Clientes(id)` `ON DELETE SET NULL`, guards estilo 0022, downgrade verificado con ciclo down/up en dev); modelo + relationship `selectin`; schemas (`Create/Update/Read` + `cliente_nombre`); ruta valida `cliente_id` (desconocido → 400) y resuelve `cliente_nombre` en get/list.
- **Frontend:** servicio con los nuevos campos; `NuevoPedidoModal` muestra el selector en REAL (existente de CRM + alta rápida por nombre vía `POST /clientes`); `ProduccionView` y `DashboardView` muestran el nombre real.
- **Tests:** nuevo `test_pedido_con_cliente_y_cliente_invalido` (create con cliente, list resuelve nombre, 400 con cliente fantasma, PATCH reasigna/limpia).
- Verificación: `pytest test_fase4_produccion` 6 passed; `alembic upgrade head` + ciclo down/up en dev; `npm run build` OK + `npm test` 70/70.

### [2026-09-05] - Fix P2-3 (auditoría funcional): anti doble-submit

- **Antes:** creates y transiciones sin guard permitían doble POST con doble clic (ventas/pedidos/socias/liquidaciones/anticipos/clientas duplicados, etapas de producción salteadas).
- **Fix:** `guardando` + `:loading` en los 6 modales de alta/edición; `transicionandoId` por fila en `ProduccionView` (más badge `CANCELADO` y botones apagados en terminales); busy por fila en descontar anticipos.
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-05] - Fix auth P0 (auditoría 2): endpoints abiertos o con rol débil

- **`audit_fiscal.py`:** los 3 GETs no pedían auth → ahora `audited_user` (admin/operador/consulta); los POST validan `producto_id` (desconocido → 400) y `periodo` con formato `YYYY-MM`.
- **`observability.py`:** `/alerts` abierto y con SQL roto (columnas inexistentes, siempre `[]` por el `except` mudo) → ahora con auth y query ORM real (`stock_actual < stock_minimo`). `/summary` y `/metrics` quedan abiertos a propósito (telemetría para scrapers).
- **`ventas.py` + `finanzas.py`:** `PATCH .../state` aceptaba cualquier rol autenticado → ahora `mutation_user` (admin/operador), manteniendo `current_user` para auditoría de reversiones.
- Verificación: `py_compile` OK + suites ventas/finanzas/omisiones en verde.

### [2026-09-05] - Fix N+1 (auditoría 2): `selectinload` en listas de finanzas

- **`finanzas.py`:** `_liquidacion_response`/`_anticipo_response` disparaban una query por fila (`d.socia.nombre`).
- **Fix:** `selectinload` de distribución+socia y de socia en los listados (mismo patrón que producción).
- Verificación: suites finanzas en verde.

### [2026-09-05] - Fix omisiones (auditoría 2): filtro de fechas daba 422 + índices 0027

- **Bug real (test en rojo en main):** `GET /omisiones?fecha_desde=2026-08-01` devolvía 422 porque pydantic v2 `datetime` rechaza fechas sin hora. Fix: params como `date`.
- **Migración `0027_audit_omisiones_indexes`:** índices en `precio_versions(producto_id)`, `costo_versions(producto_id)`, `Migracion_Omisiones(resuelta/nivel)`; aplicada en dev.
- Verificación: `test_omisiones_api.py` 12 passed; `alembic upgrade head` OK.

### [2026-09-05] - Fix devoluciones (auditoría 2): cliente/prenda reales en la lista

- **Antes:** `Cliente ${venta_id}` / `Venta #id` inventados como si fueran datos.
- **Fix backend:** `DevolucionRead` suma `cliente_nombre`/`prenda_nombre` resueltos por mapper (`venta` ya venía con `selectinload`).
- **Fix frontend:** usa los nombres reales con fallback honesto (`Venta #id` / `—`).
- Verificación: suites devoluciones 29 passed; `npm run build` OK.

### [2026-09-05] - Fix finanzas (auditoría 2): socias dinámicas + reload tras transición

- **Antes:** KPIs y tabla hardcodeaban `socia_id 2/3` y nombres Margara/Valqui → con otras socias, plata mal atribuida o en 0.
- **Fix:** `sociasReparto` (primeras 2 activas no-fondo) con nombres/porcentajes/celdas dinámicos; `cambiarEstadoLiq` siempre refetchea en vez del parche optimista.
- Verificación: `npm run build` OK + `npm test` 70/70.

### [2026-09-05] - Fix optimizador (auditoría 2): eficiencia calculada

- **Antes:** el resultado mostraba `88.4%` fijo tras "optimizar".
- **Fix:** headline bindeado a `porcentajeAprovechamiento` real con etiqueta por tramo.
- Verificación: `npm run build` OK.

### [2026-09-06] - Backfill F8 hidratacion-datos-faltantes (precios/costos/proveedores)

- **Script (`backend/migrate/backfill_precios_costos.py`)**: `plan_*` puros (csv canonico, CAJAS/VENTAS corroboran, DESCUENTOS solo valida, Celeno 75000 locked) + `aplicar_*` con 1 tx por entidad, snapshot pre-run y audit JSON en `reports/backfill_*.json`; `--dry-run` default (0 escrituras, exit 1 en ERROR). EXM-2/D5: `#`/descuento/sin-fecha a WARN+skip, nunca inferir/now(). `loaders.py` intacto.
- **Migracion `0028_backfill_provenance`** (head unico, sobre `0027`): `Productos.origen_precio` / `Insumos.origen_costo` VARCHAR(20) NULL; modelos actualizados. Sin siembra de `Compras_Insumos` (WAC intacto); proveedores insert-only (`maestros_proveedores`, `proveedor_id` NULL salvo match exacto).
- **Tests (`backend/tests/test_backfill_precios_costos.py`)**: 5 passed (csv-wins, descuento/#VALUE!/sin-fecha skip, Celeno lock, normalizacion proveedores, dry-run/apply/idempotencia + FK NULL-safe). Core en verde: WAC/BOM/costos/catalogo/proveedores/productos/insumos 145 passed. `PENDIENTES_MIGRACION.md` 3.4 con drift memo (workbook 15 vs catalogo 14 vs live 15).

### [2026-09-07] - Preproceso standalone INVERSION VALQUI (stockable vs no-stockable, 7 decisiones)

- **Script (`backend/migrate/preprocess_inversion_valqui.py`)**: estilo F8 modelado en `backfill_precios_costos.py` (Report + `normalizar_nombre`/`clave_normalizada`/`clasificar_material`, `normalizar_decimal`/`unidad_canonica`/`fecha_para_fila`, `ALIASES_COMPRA_A_CATALOGO`/`normalizar_cantidad_compra`, `clasificar_tipo`; `--dry-run` default, 0 escrituras; `--apply` exige `--yes` y sigue read-only sin sesion DB; exit 1 en ERROR; audit JSON en `reports/preprocess_inversion_valqui_*.json`). Parsea `ARPIA - INVERSION VALQUI (1).csv` (bloque izquierdo A:G + sub-tabla derecha H:L) y separa **53 stockables** (lote D/Cantidad, nunca D directo: $8.000/4m=$2.000/m, 8m $149.224=$18.653/m) vs **22 movimientos** (`Inversion`/`Gasto` case-sensitive, socio Valqui). Reglas: cabeceras L2/L97 y total L137 excluidos; `#DIV/0!`/costo vacio (L115) a skip; cantidad A-or-C (bloque Kilotelas) + fallback multi-token; fechas DD/MM/YYYY con herencia contigua D5 (nunca now()); proveedor en blanco a WARN+skip nunca inferido (col Direccion solo nota descartada, sin columna DB); derecha solo fuente-unica (37 descartadas-duplicadas, 19 unicas-sin-fecha omitidas D5); `Gerrajes` != `Herrajes` (negocios distintos); duplicados exactos (Hilo L24/L26, L25/L27, Hilaza L75-76, Cajas L83-84) + 22 filas 2026 post-corte WAC OCT25 a WARN. **Checksum OK: suma de lotes 13.548.941 == L137**. Self-check `--dry-run` exit 0 (0 ERROR, 141 WARN agrupados DEC-1..DEC-7 para el dueno).
- Verificacion: sin escrituras DB, sin cambios a loaders/modelos, JSON valido (stockables/movimientos/derecha/proveedores/checksum/warnings).

### [2026-09-07] - Loader SAFE INVERSION VALQUI -> F2/F6 (ruta delegada directa, allowlist del dueno)

- **Nuevo (`backend/migrate/inversion_valqui_loader.py`)**: importa los planificadores puros `plan_izquierda`/`plan_derecha` del preproceso validado y reserva a traves de los escritores existentes `aplicar_compras` (F2 WAC) y `aplicar_finanzas` (F6), sin duplicar logica de pipeline. Puerta de seguridad: `OWNER_ALLOWLIST` vacio por defecto (claves `dec1_stock`, `dec4_supplier`, `dec7_duplicates`, `dec7_post_cutoff`, `dec5_right_unique` con ejemplos documentados: DEC-1 fuera de universo BOM, DEC-4 proveedor faltante, DEC-7 duplicados Cajas L83-84/Hilaza L75-76/Hilo L24-L27 + corte 2026, DEC-5 fuente unica FK NULL) + flag `ALLOW_POST_CUTOFF_2026 = False` (lotes 2026 nunca reescriben WAC en silencio); Direccion solo nota descartada; `tipo` validado contra CHECK case-sensitive (`ck_movimientos_tipo`); items nuevos solo-derecha fallan en `aplicar_compras` (F1 catalogo primero, `categoria_id`/`unidad_medida` NOT NULL). `--dry-run` default muestra lo que IRIA a `Compras_Insumos` vs `Movimientos_Financieros` sin escrituras; `--apply` exige `--yes` y solo reserva filas confirmadas (commit unico, rollback total en ERROR); audit JSON en `reports/inversion_valqui_loader_*.json`.
- Verificacion: `python -m migrate.preprocess_inversion_valqui --dry-run` exit 0 (0 ERROR, 141 WARN, checksum 13.548.941 OK) + `python -m migrate.inversion_valqui_loader --dry-run` exit 0 (0 ERROR; 7 stocks + 19 movimientos confirmables pre-corte, 46 stocks + 3 movimientos retenidos sin confirmacion) + `--apply` sin `--yes` rechazado. Sin escrituras DB, sin commit/push, loaders/modelos intactos.


### [2026-09-07] — Slice UI edición de insumos (EditarInsumoModal, ruta delegada directa)

- **Nuevo `src/components/atelier/EditarInsumoModal.vue`:** modal de edición con el mismo set de campos de `NuevoInsumoModal` (nombre, código, categoria_id, unidad, tipo, ubicación, stock_actual, stock_minimo, costo_promedio_actual + descripción), confirmado contra el schema `InsumoUpdate` (`backend/app/schemas/insumo.py:22-32`, todo opcional). Prefill desde la fila + refetch autoritativo `GET /insumos/{id}` para `categoria_id` en modo REAL; en MOCK sincroniza `costo_unitario/categoria` del store para que el display no quede stale. Guardar llama al `update` existente (`PATCH /insumos/{id}` vía `useInsumos`, sin cambios backend); 403 muestra hint "requiere rol admin" en vez del toast genérico. Código/comentarios en inglés, labels de usuario en español como la UI existente. Sin tocar literal Atelier ni lógica WAC.
- **`src/views/InventarioView.vue`:** botón `Editar` (pi-pencil, admin-gated vía `auth.role === 'admin'`) en la columna Acciones junto a `+Compra`/delete; abre el modal con `insumoSeleccionado` y refresca con `cargarInsumosReales` al guardar. `+Compra`, delete y ajuste ±1 intactos.
- Verificación: `npm run build` OK + grep confirma botón Editar en Acciones. Sin escrituras DB, sin commit/push.

### [2026-09-08] - Purga ghost insumos INVENTARIO OCT25 (ruta delegada directa, dueño confirmó dato irreal)

- **Alcance verificado read-only primero:** 8 fantasmas `LIKE '*%'` (ids 1-8: 2 argollas + 3 ochos + 3 gancho-G; id 1 stock 122 costo 0). Dependencias: 0 líneas `BOM_Insumos`, 2 `Compras_Insumos` (ids 79-80, insumo 3), 0 texto colgante en `Movimientos_Financieros`. Nota: `codigo 'INS-1'` no existe (código NULL; el id 1 es el match). Combos `BOM_Productos` (9) intactos.
- **Fase 1 BOM:** nada que borrar (0 líneas fantasma; el guard de la migración aborta si aparecen).
- **Fase 2 Compras — migración `0029_purge_ghost_oct25`** (head único, sobre `0028`): backup `COPY` primero (`backup_compras_ghost_oct25` 2 filas + `backup_insumos_ghost_oct25` 8 filas, con verificación backup==live y abort en mismatch), luego `DELETE` de las 2 compras (sin API DELETE existente). Downgrade reinserta desde backup. Export CSV auditoría: `csv/backup_ghost_insumos_20260908.csv` (8) + `csv/backup_ghost_compras_20260908.csv` (2).
- **Fase 3 Insumos — admin `DELETE /api/v1/insumos/{id}`** (endpoint real + JWT admin real verificado por `require_admin`; sin adivinar password para no disparar lockout): 8×204. Resultado: Insumos 79→71, Compras 83→81, fantasmas 0; BOM_Insumos 74, BOM_Productos 9, financieros 149, proveedores 41 sin cambios.
- **Fix compañero obligatorio (b) anti-resurrección:** filtro de exclusión `'*'` con WARN en `catalog.py:_leer_materiales` (universo F1) + `stock.py:plan_stock`, y eliminadas las 8 entradas `'*'` muertas de `ALIASES_STOCK_A_CATALOGO` (solo quedan alias de nombres reales). `ARPIA.xlsx` intacto.
- **Tests (solo archivos relevantes):** `test_migrate_catalog.py` — test viejo actualizado (fantasmas `'*'` ahora ausentes del universo, reales presentes) + nuevo `test_oct25_asterisco_fantasma_excluido_del_universo` sintético; `test_migrate_stock.py` — `test_aplicar_stock_alias_argollas_medianas_estrella` reescrito como `test_plan_stock_asterisco_fantasma_excluido` (plan vacío, canónico en 0, nunca crea `'*'`). Verificación: 5 passed (subset catálogo) + 14 passed (stock). Suite completa no corrida. Sin commit/push.

### [2026-09-08] - Sort single-columna estilo PrimeVue en tabla Inventario (ruta delegada directa)

- **`src/views/InventarioView.vue` (único archivo tocado):** sort liviano sobre el `<table>` existente, sin rewrite a `<DataTable>` (diff mínimo, misma UX PrimeVue Sort Single: clic en header cicla asc → desc → sin orden, una sola columna activa, indicador ▲/▼).
  - **Estado:** `SortField = 'nombre' | 'tipo' | 'ubicacion' | 'stock' | 'costo' | 'valor'` + `sortField: Ref<SortField|null>` (null = sin orden) + `sortOrder: 1 | -1`; `toggleSort(field)` implementa el ciclo asc → desc → none con semántica single-sort (cambiar de columna resetea a asc).
  - **`insumosFiltrados`:** filtra igual que antes (search/tipo/categoria/bajo-stock intactos) y luego ordena estable (índice original como tiebreak). Comparadores: `nombre` (nombre + tiebreak código, `localeCompare` es/numeric), `tipo` (tipo + tiebreak categoría, cubre header combinado "Tipo & Categoría"), `ubicacion` (ubicación + tiebreak proveedor, cubre "Ubicación / Proveedor"), `stock`/`costo`/`valor` numéricos con `Number()` (valor = stock × costo, consistente con `formatCOP`); `null` defensivo vía `?? ''` / `|| 0`.
  - **Headers accesibles:** 6 `<th scope="col" :aria-sort>` con `<button>` interno (labels/tooltips en español: "Ordenar por código / insumo", "...tipo y categoría", etc.), indicador `<span aria-hidden>` ▲/▼ ámbar solo en la columna activa. `Ajuste Rápido` y `Acciones` quedan como `<th>` planos no-ordenables.
  - Código/comentarios en inglés, UI en español como el estilo existente. Sin tocar mapping, WAC, edit modal ni backend. PrimeVue 4.5.5 ya en uso; no se necesitó consultar docs v4 (no hay componente DataTable nuevo).
- Verificación: `npm run build` OK (410 módulos, 3.4s, `InventarioView-*.js` 41.40 kB). Sin commit/push.

### [2026-09-14] - Fix FK case mismatch en audit_fiscal + auditoria global de FKs (implementacion directa)

- **`backend/app/models/audit_fiscal.py` (unico archivo tocado):** 3 strings FK en minuscula apuntaban a tablas inexistentes (Postgres con `"Productos"` entrecomillado es case-sensitive): L8 `ForeignKey("productos.id")` -> `ForeignKey("Productos.id")`, L9 `ForeignKey("variantes_producto.id")` -> `ForeignKey("Variantes_Producto.id")`, L18 `ForeignKey("productos.id")` -> `ForeignKey("Productos.id")`. Ground truth: `productos.py:27 __tablename__="Productos"`, `:66 "Variantes_Producto"`, `DDL.sql:811/870` y `backend/alembic/versions/0019_audit_fiscal_versioning.py:19-20,30`. Tablas NO renombradas, sin migracion, sin cambios DB.
- **Auditoria global:** 35 `__tablename__` en `backend/app/models/*.py` vs 38 `ForeignKey("...")` en modelos. Los otros 35 FK coinciden exacto (case-sensitive) con su tabla: `Tipos_Producto`, `Insumos`, `BOM_Insumos`, `BOM_Productos`, `pedidos_produccion`, `Ventas`, `Detalle_Ventas`, `Devoluciones`, `Items_Devolucion`, `Usuarios`, `Clientes`, `Socios_Configuracion`, `liquidaciones`, `Categorias_Insumos`, `maestros_proveedores`, etc. `DDL.sql` (32 `CREATE TABLE`) coincide con los modelos. Cero casos ambiguos (ninguna FK apunta a tabla realmente inexistente); nada mas que corregir.
- **Reproduccion `PUT /api/v1/productos/2`:** el handler crea `PrecioVersion`/`CostoVersion` en la misma transaccion (versionado desde 2026-09-02); con el FK en minuscula, `configure_mappers()` / el flush lanzaba `NoReferencedTableError: productos` y el PUT fallaba con 500. Tras el fix, `configure_mappers()` pasa y el versionado persiste.
- Verificacion: `py_compile` OK + `configure_mappers()` MAPPERS_OK (importa los 12 modulos de modelos). `pytest -k "producto or audit or version"` no corre en este entorno (requiere Postgres en 127.0.0.1:5433, caido) — fallo `OperationalError`, no relacionado al cambio. Sin commit (working tree dirty a proposito).
