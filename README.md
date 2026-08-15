# ERP/MRP ARPIA

Aplicación web de gestión de inventarios, producción y ventas para **ARPIA**. Este documento define la arquitectura, el modelo de datos y la hoja de ruta del proyecto.

---

## 1. Stack Tecnológico

| Capa | Tecnología | Justificación |
| --- | --- | --- |
| **Backend & API** | **Python + FastAPI** | Alto rendimiento, ideal para un monolito modular con dominios bien delimitados (inventario, ventas, finanzas). |
| **ORM** | **SQLAlchemy** | Mapeo de modelos a tablas y manejo de transacciones complejas. |
| **Base de datos** | **PostgreSQL** | Precisión nativa con `NUMERIC`/`DECIMAL`, vital para cálculos financieros y WAC. |
| **Migraciones** | **Alembic** | Cambios de esquema versionados y controlados. |
| **Entorno local** | **Docker + Docker Compose** | Base de datos, backend y frontend orquestados con paridad con producción. |
| **Producción** | **cPanel (hosting compartido)** | API como app Python en `api.arpia.com.co` y frontend estático en `app.arpia.com.co`; despliegue vía `scripts/deploy.sh` y `scripts/deploy-frontend.sh`. |
| **Frontend** | **Vue 3 + Vite + TypeScript + Pinia + Element Plus + ECharts** | SPA completa (auth, dashboard y módulos operativos) desplegada en producción. |

**Decisión de arquitectura: monolito modular, no microservicios.** Para un equipo pequeño, una sola aplicación con dominios separados (carpetas/módulos de inventario, ventas, finanzas) y una sola base de datos es la opción correcta. La separación en microservicios solo se evalúa si el volumen o el equipo lo justifican, y en ese caso cada servicio debería tener su propio esquema, no una base compartida.

---

## 2. Arquitectura de Base de Datos (Modelo Entidad-Relación)

La base de datos usa un modelo **BOM Multinivel** (Bill of Materials) y el método **WAC (Costo Promedio Ponderado)** para la valoración de inventario.

**Convenciones de tipos:**
- Todo valor monetario y de cantidad: `NUMERIC(15,4)` (precisión interna) y redondeo a 2 decimales **solo al momento de mostrar o facturar**. Nunca `FLOAT`/`REAL` para dinero.
- Cantidades de insumos en `NUMERIC` (permiten fracciones como 0.5 unidad).
- Todos los timestamps en `TIMESTAMPTZ`.

### Módulo de Usuarios y Seguridad
*   **`Usuarios`**
    *   `id` (PK), `nombre`, `email` (único), `password_hash`
    *   `rol` (`admin`, `operador`, `consulta`)

### Módulo de Clientes
*   **`Clientes`**
    *   `id` (PK), `nombre`
    *   `documento_identidad` (único, nullable), `email`, `telefono`
    *   `created_at` (Timestamp)

### Módulo de Inventario y Suministros
Gestiona materia prima, empaques y componentes.

*   **`Categorias_Insumos`**
    *   `id` (PK), `nombre` (Telas, Herrajes, Empaques, Químicos)
*   **`Insumos`** (Catálogo principal)
    *   `id` (PK), `categoria_id` (FK)
    *   `nombre`, `unidad_medida` (cm, metro, unidad)
    *   `stock_actual` (NUMERIC)
    *   `stock_minimo` (NUMERIC) - *Umbral de reposición; alimenta el reporte de stock crítico.*
    *   `costo_promedio_actual` (NUMERIC) - *Se actualiza dentro de la misma transacción que registra la compra.*
*   **`Compras_Insumos`** (Historial y motor WAC)
    *   `id` (PK), `insumo_id` (FK)
    *   `fecha_compra` (DateTime)
    *   `cantidad_comprada` (NUMERIC)
    *   `precio_unitario_compra` (NUMERIC)

### Módulo de Ingeniería de Producto (BOM Multinivel)
Define los productos terminados (fabricados o revendidos), los combos y sus variantes.

*   **`Tipos_Producto`**
    *   `id` (PK), `nombre` (Prenda, Accesorio, Kit/Combo, Empaque Premium)
*   **`Productos`**
    *   `id` (PK), `tipo_producto_id` (FK)
    *   `nombre` (Ej. Corset Artemisia, Vela Vainilla, Caja Saca las Garras)
    *   `requiere_fabricacion` (Boolean) - Diferencia manufactura propia de reventa.
    *   `costos_operativos_fijos` (NUMERIC) - Costos de confección, corte, etc.
    *   `precio_venta_sugerido` (NUMERIC)
*   **`Variantes_Producto`** (Tallas, colores, etc.)
    *   `id` (PK), `producto_id` (FK)
    *   `nombre_variante` (Ej. "Talla S", "Negro")
    *   `precio_venta` (NUMERIC) - *Anula el sugerido cuando corresponde.*
*   **`BOM_Insumos`** (Receta base y por variante)
    *   `id` (PK), `producto_id` (FK), `insumo_id` (FK)
    *   `variante_id` (FK -> Variantes_Producto, Nullable) - *`NULL` = receta base para todas las variantes; si una variante consume distinto (ej. corset XL), se define su propia fila.*
    *   `cantidad_requerida` (NUMERIC) - Ej. 4800 cm de tela.
    *   `porcentaje_desperdicio` (NUMERIC, default 0) - *Merma de corte/empaque; el costo real usa `cantidad_requerida * (1 + porcentaje_desperdicio/100)`.*
*   **`BOM_Productos`** (Receta de Combos)
    *   `id` (PK), `combo_id` (FK -> Productos), `producto_incluido_id` (FK -> Productos)
    *   `cantidad` (NUMERIC) - *Permite fracciones (ej. 0.5 producto por combo).*

### Módulo de Ventas y Finanzas
Controla las salidas, calcula márgenes y distribuye utilidades.

*   **`Ventas`**
    *   `id` (PK), `fecha` (DateTime)
    *   `cliente_id` (FK -> Clientes, Nullable) - *Ventas sin cliente registrado quedan permitidas (ej. ferias), pero con trazabilidad.*
    *   `canal_venta` (`web`, `whatsapp`, `instagram`, `feria`) - *Origen de la venta; la persona que figura en el registro es el cliente, no un vendedor.*
    *   `descuento_porcentaje` (NUMERIC)
    *   `estado` (`completada`, `anulada`) - *Las anulaciones pasan por el módulo de devoluciones, nunca borran filas.*
    *   `total_venta` (NUMERIC)
*   **`Detalle_Ventas`**
    *   `id` (PK), `venta_id` (FK), `producto_id` (FK)
    *   `cantidad` (NUMERIC), `precio_unitario_aplicado` (NUMERIC)
    *   `costo_unitario_aplicado` (NUMERIC) - **Snapshot del WAC al momento de vender.** El margen se calcula contra este valor, no contra el costo promedio de hoy; así los reportes históricos no cambian solos.
*   **`Devoluciones`** (Reembolsos y reposición de inventario)
    *   `id` (PK), `venta_id` (FK), `fecha` (DateTime)
    *   `motivo`, `monto_reembolsado` (NUMERIC)
    *   Al confirmar, se repone stock siguiendo el BOM (o se anula el `estado` de la venta si es total).
*   **`Socios_Configuracion`**
    *   `id` (PK), `nombre` (Margara, Valqui, Reinversión), `porcentaje_participacion` (NUMERIC)
    *   *Validar que la suma de porcentajes = 100.*
*   **`Movimientos_Financieros`** (Gastos y Retiros)
    *   `id` (PK), `fecha` (DateTime), `tipo` (Gasto, Inversión, Retiro)
    *   `descripcion` (String), `monto` (NUMERIC), `socio_id` (FK, Nullable)

---

## 3. Hoja de Ruta de Desarrollo (Roadmap)

> **Estado: Fases 1–6 COMPLETADAS e implementadas en producción** (verificado agosto 2026). API en `api.arpia.com.co`, frontend en `app.arpia.com.co`.

### Fase 1: Infraestructura y Modelado (Semanas 1-2) — ✅ COMPLETADA
1.  **Inicialización:** Crear el repositorio y configurar `docker-compose.yml` con PostgreSQL y FastAPI.
2.  **Modelos ORM:** Traducir el esquema relacional a clases de SQLAlchemy (incluye `Clientes` y `Usuarios`).
3.  **Migraciones:** Configurar Alembic para manejar cambios de esquema de manera controlada.
4.  **Autenticación y permisos:** Login JWT y roles (`admin`, `operador`, `consulta`); los endpoints protegidos según rol.
5.  **CRUD Básico:** `Categorias_Insumos`, `Insumos` y `Clientes`.

### Fase 2: Lógica Central de Costos - WAC (Semana 3) — ✅ COMPLETADA
1.  **Endpoint de Compras:** Registrar `Compras_Insumos`.
2.  **Motor WAC:** Al registrar una compra, dentro de la **misma transacción**:
    ```
    nuevo_costo = (stock_actual * costo_promedio_actual + cantidad_comprada * precio_unitario_compra)
                  / (stock_actual + cantidad_comprada)
    ```
    Con `SELECT ... FOR UPDATE` sobre la fila de `Insumos` para evitar condiciones de carrera entre compras simultáneas.
3.  **Testing:** Validar que el WAC responda correctamente a fluctuaciones de precios y a compras concurrentes.

### Fase 3: Ingeniería de Producto y BOM Multinivel (Semanas 4-5) — ✅ COMPLETADA
1.  **Endpoints de Productos:** CRUD para `Productos`, `Tipos_Producto` y `Variantes_Producto`.
2.  **Gestión de Recetas:** Lógica para asignar insumos a un producto (`BOM_Insumos`, con variantes y desperdicio) y productos a un combo (`BOM_Productos`).
3.  **Cálculo Dinámico de Costos:** Servicio recursivo con memoización que recibe `producto_id` (+ variante opcional) y retorna el costo de producción al día de hoy, recorriendo el BOM, aplicando desperdicio y consultando los costos promedios actuales. Esta misma función se reutiliza en Fase 4: no duplicar la lógica.

### Fase 4: Ventas y Descarga de Inventario (Semanas 6-7) — ✅ COMPLETADA
1.  **Registro de Ventas:** Endpoint para procesar una venta nueva con su detalle.
2.  **Motor de Inventario:** Al confirmar, la aplicación ejecuta la explosión de materiales (recorre el BOM del producto vendido, considerando variante y desperdicio) y resta de `stock_actual` en `Insumos`. Todo dentro de un bloque de transacción con `FOR UPDATE`.
3.  **Cálculo de Márgenes:** Guardar `costo_unitario_aplicado` (snapshot WAC) junto a cada línea para obtener la utilidad neta real e históricamente estable.

### Fase 5: Devoluciones, Finanzas y Dashboards (Semana 8) — ✅ COMPLETADA
1.  **Devoluciones:** Endpoint que reembolsa, repone inventario (explosión inversa) y/o anula la venta.
2.  **Distribución de Utilidades:** Lógica para que las ventas liquiden porcentajes según `Socios_Configuracion`.
3.  **Gestión de Gastos:** CRUD para `Movimientos_Financieros`.
4.  **Endpoints Analíticos:** Rutas que consolidan datos para el frontend (ventas mensuales, insumos con stock crítico según `stock_minimo`, margen por producto).

### Fase 6: Frontend y Dashboard (Semana 9) — ✅ COMPLETADA
1.  **Stack frontend:** Aplicación web (Vue o React) que consume la API `/api/v1`.
2.  **Autenticación:** Login JWT con roles (`admin`, `operador`, `consulta`), sesión y guard de rutas.
3.  **Dashboard analítico:** Paneles con ventas mensuales, insumos con stock crítico y margen por producto (consume los endpoints de Fase 5).
4.  **Pantallas operativas:** Gestión de ventas, devoluciones, finanzas (movimientos y socios) e inventario.
5.  **Despliegue:** Build estático servido desde cPanel / subdominio, apuntando a `api.arpia.com.co`.

---

## 4. Notas Clave para el Desarrollo

*   **Transacciones atómicas:** Al procesar ventas o compras, la actualización de inventario y costos ocurre dentro de un bloque de transacción SQL (`db.commit()` al final, `db.rollback()` si algo falla). Sin transacción, no hay operación.
*   **Concurrencia:** Toda lectura-modificación-escritura sobre `Insumos` (WAC, explosión de inventario) usa `SELECT ... FOR UPDATE`. El stock es un recurso compartido: dos ventas simultáneas no pueden corromperlo.
*   **Snapshot de costos:** El margen histórico se calcula con `costo_unitario_aplicado` guardado en la venta, nunca con el costo promedio actual.
*   **Precisión monetaria:** `NUMERIC(15,4)` en el modelo; redondeo a 2 decimales solo en la capa de presentación. Prohibido `FLOAT` para dinero.
*   **BOM centralizado:** Una única función de costo/explosión reutilizada por ventas, devoluciones y reportes. Cualquier cambio de regla se hace en un solo lugar.
*   **Versionado de API:** Prefijo `/api/v1/` en los endpoints para evolucionar sin romper clientes.
*   **Testing:** Cada fase entrega tests del motor central (WAC, explosión de inventario, márgenes) antes de seguir. Sin test de la lógica de costos no se considera cerrada la fase.
*   **Entorno:** Secretos (passwords de DB, JWT) por variables de entorno / archivo `.env`, nunca versionados.

---

## 5. Cómo ejecutar el proyecto

### Requisitos
* Docker + Docker Compose (para la base de datos PostgreSQL y la API).
* Python 3.11+ (solo para desarrollo local fuera de Docker).

### Arranque completo con Docker (API + base de datos)

```bash
# 1. Configurar variables (copiar y ajustar si hace falta)
cp .env.example .env

# 2. Levantar la base de datos y la API
docker compose up --build -d

# 3. Aplicar migraciones y sembrar datos iniciales
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seeder
```

La API queda disponible en `http://localhost:8000` (documentación interactiva en `/docs`) y PostgreSQL en `localhost:5432`.

> **Nota Windows/WAMP:** si el puerto 5432 está ocupado por un PostgreSQL local, define `DB_PORT=5433` en `.env` (el contenedor sigue exponiendo su 5432 interno).

### Desarrollo local con venv (sin contenedor de API)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows; en Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # asegúrate de que DATABASE_URL use localhost:5433 si DB_PORT=5433
alembic upgrade head
python -m app.seeder
uvicorn app.main:app --reload
```

### Credenciales iniciales (seed)

| Rol | Email | Contraseña |
| --- | --- | --- |
| admin | `admin@arpia.com` | `Admin123!` |

> **Seguridad:** cambia `JWT_SECRET_KEY` y las contraseñas del seed antes de cualquier despliegue. Los secretos viven en `.env` (ignorado por git), nunca versionados.

### Frontend (Vue 3 + Vite)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173 con proxy a la API local :8000
npm run build      # dist/ estático (lo que se despliega en cPanel)
npm test           # Vitest
```

### Tests

```bash
cd backend
.venv\Scripts\activate
pytest             # 212 tests: health, JWT login, roles, CRUD, WAC, BOM,
                   # explosión de inventario, costos, ventas, devoluciones,
                   # finanzas y analíticos, contra PostgreSQL real vía Docker.
```

Los tests cubren health, login JWT, roles (401/403/201) y CRUD de insumos contra PostgreSQL real vía Docker. La configuración resuelve `.env` de forma absoluta respecto al backend, por lo que los comandos funcionan desde cualquier directorio.

El frontend agrega **372 tests Vitest** (`frontend/tests/`, `npm test`): guards de rutas y auth, mappers, tablas, formularios y vistas de todos los módulos.

### Despliegue a cPanel (producción)

La producción corre en hosting cPanel, no Docker. Ver detalles en `frontend/README.md` (despliegue del SPA) y los scripts:

```bash
scripts/deploy.sh           # API: clone + rsync backend/, pip install en el venv
                            # cPanel (/home/<user>/virtualenv/...), alembic upgrade head, restart
scripts/deploy-frontend.sh  # build del SPA (detección del npm del server) + rsync
                            # a app.arpia.com.co, protege .well-known, SPA htaccess
```

---

## 6. Anexo: Modelo real desde `ARPIA.xlsx`

Este anexo documenta cómo se almacenan actualmente los datos de ARPIA en el archivo de trabajo `ARPIA.xlsx`, y qué confirma o ajusta sobre el modelo relacional de este documento. Es la fuente de verdad del negocio y guía la implementación.

### Cómo se organiza hoy el archivo

| Hoja | Qué contiene |
| --- | --- |
| `VENTAS` | Ventas por fila: producto, talla, precio venta, costo, ganancias, reparto (Reinversión / Margara / Valqui), fecha, canal y cliente. |
| `INVENTARIO OCT25` | Stock separado en **MATERIAL** (telas/empaques), **HERRAJES** (argolla, varillas, ganchos) y **PRENDAS** (terminadas con talla): `INICIAL / VENTAS / FINAL`. |
| ~~`Proveedores`~~ | Hoja eliminada (2026-08): el workbook recalculado ya no la tiene; la entidad fue removida del ERP. |
| `DESCUENTOS` | Descuento en $ y %, venta neta, ganancia y reparto por socio. |
| `GASTOS ARPIA` | Gastos, retiros y distribución por socio. |
| Hojas de producto (`CORSET`, `BUSTIER`, `Braleth`, etc.) | **Receta BOM real**: por cada insumo (tela, varilla, fijaciones), dimensión (ancho x alto), `cantidad Cms`, `valor metro` y `valor total`. |

### Qué confirma el archivo sobre el modelo

*   **Costo snapshot en ventas:** cada fila de `VENTAS` conserva el costo histórico (ej. `Costo 129388`) junto al precio, tal como modelamos con `Detalle_Ventas.costo_unitario_aplicado`. El margen se calcula contra ese valor, no contra el costo actual.
*   **Reparto por socios:** el archivo reparte `Ganancias` en **Reinversión 40% / Margarita 30% / Veki 30%**. Coincide con `Socios_Configuracion`.
*   **Variantes:** tallas (`S`, `M`, `L`, `XS`) y colores/referencias (`vino`, `blanco`) → valida `Variantes_Producto` y `BOM_Insumos.variante_id`.
*   **Descuentos:** `DESC %` y `DESC $` por operación → valida `Ventas.descuento_porcentaje`.
*   **Clientes y canales de venta:** la persona que figura en cada venta (ej. `gaby`, `celeste`, `Maira`) es el **cliente**, no un vendedor. Las ventas pueden originarse por **web, WhatsApp, Instagram o feria** → justifica el campo `Ventas.canal_venta`.

### Ajustes que el archivo impone sobre el modelo

1. **Unidades y conversión en el BOM (crítico).** En la realidad, los insumos de tela se cotizan en **metros** (`valor`) y se consumen en la receta en **centímetros** (`cantidad Cms`, ej. 4800 cms). Para que la explosión de inventario y el costo dinámico no se descalibren:
   - `Insumos.unidad_medida` y `BOM_Insumos.cantidad_requerida` deben estar en la **misma unidad**, o fijar una **unidad maestra + factor de conversión** (se recomienda metros como unidad maestra para textil).
   - El costo se calcula `cantidad_requerida * unitario` con el unitario en la unidad maestra.
2. **Materiales vs Herrajes.** El archivo separa `MATERIALES` (telas, empaques, químicos) de `HERRAJES` (argollas, varillas, oches, ganchos) porque se compran y valoran distinto (por metro vs por unidad). Ambos viven en `Insumos` con `unidad_medida` distinta, pero conviene mantener la separación visible en UI/compras.
3. **Stock por prenda terminada.** `PRENDAS` lleva talla y contador `INICIAL / VENTAS / FINAL`, separado del stock de materia prima. Reafirma la necesidad de inventario de acabado por **producto + variante**, además del inventario de insumos del BOM.
