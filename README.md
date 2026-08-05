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
| **Entorno** | **Docker + Docker Compose** | Paridad total local/producción: base de datos, backend y frontend orquestados. |
| **Frontend** | Dashboard prototipo; migración futura a un framework reactivo (Vue.js o React). | |

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
Gestiona materia prima, empaques y componentes adquiridos a proveedores.

*   **`Proveedores`**
    *   `id` (PK), `nombre`, `ubicacion`, `url`, `contacto`
*   **`Categorias_Insumos`**
    *   `id` (PK), `nombre` (Telas, Herrajes, Empaques, Químicos)
*   **`Insumos`** (Catálogo principal)
    *   `id` (PK), `categoria_id` (FK)
    *   `nombre`, `unidad_medida` (cm, metro, unidad)
    *   `stock_actual` (NUMERIC)
    *   `stock_minimo` (NUMERIC) - *Umbral de reposición; alimenta el reporte de stock crítico.*
    *   `costo_promedio_actual` (NUMERIC) - *Se actualiza dentro de la misma transacción que registra la compra.*
*   **`Compras_Insumos`** (Historial y motor WAC)
    *   `id` (PK), `insumo_id` (FK), `proveedor_id` (FK)
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

### Fase 1: Infraestructura y Modelado (Semanas 1-2)
1.  **Inicialización:** Crear el repositorio y configurar `docker-compose.yml` con PostgreSQL y FastAPI.
2.  **Modelos ORM:** Traducir el esquema relacional a clases de SQLAlchemy (incluye `Clientes` y `Usuarios`).
3.  **Migraciones:** Configurar Alembic para manejar cambios de esquema de manera controlada.
4.  **Autenticación y permisos:** Login JWT y roles (`admin`, `operador`, `consulta`); los endpoints protegidos según rol.
5.  **CRUD Básico:** `Proveedores`, `Categorias_Insumos`, `Insumos` y `Clientes`.

### Fase 2: Lógica Central de Costos - WAC (Semana 3)
1.  **Endpoint de Compras:** Registrar `Compras_Insumos`.
2.  **Motor WAC:** Al registrar una compra, dentro de la **misma transacción**:
    ```
    nuevo_costo = (stock_actual * costo_promedio_actual + cantidad_comprada * precio_unitario_compra)
                  / (stock_actual + cantidad_comprada)
    ```
    Con `SELECT ... FOR UPDATE` sobre la fila de `Insumos` para evitar condiciones de carrera entre compras simultáneas.
3.  **Testing:** Validar que el WAC responda correctamente a fluctuaciones de precios y a compras concurrentes.

### Fase 3: Ingeniería de Producto y BOM Multinivel (Semanas 4-5)
1.  **Endpoints de Productos:** CRUD para `Productos`, `Tipos_Producto` y `Variantes_Producto`.
2.  **Gestión de Recetas:** Lógica para asignar insumos a un producto (`BOM_Insumos`, con variantes y desperdicio) y productos a un combo (`BOM_Productos`).
3.  **Cálculo Dinámico de Costos:** Servicio recursivo con memoización que recibe `producto_id` (+ variante opcional) y retorna el costo de producción al día de hoy, recorriendo el BOM, aplicando desperdicio y consultando los costos promedios actuales. Esta misma función se reutiliza en Fase 4: no duplicar la lógica.

### Fase 4: Ventas y Descarga de Inventario (Semanas 6-7)
1.  **Registro de Ventas:** Endpoint para procesar una venta nueva con su detalle.
2.  **Motor de Inventario:** Al confirmar, la aplicación ejecuta la explosión de materiales (recorre el BOM del producto vendido, considerando variante y desperdicio) y resta de `stock_actual` en `Insumos`. Todo dentro de un bloque de transacción con `FOR UPDATE`.
3.  **Cálculo de Márgenes:** Guardar `costo_unitario_aplicado` (snapshot WAC) junto a cada línea para obtener la utilidad neta real e históricamente estable.

### Fase 5: Devoluciones, Finanzas y Dashboards (Semana 8)
1.  **Devoluciones:** Endpoint que reembolsa, repone inventario (explosión inversa) y/o anula la venta.
2.  **Distribución de Utilidades:** Lógica para que las ventas liquiden porcentajes según `Socios_Configuracion`.
3.  **Gestión de Gastos:** CRUD para `Movimientos_Financieros`.
4.  **Endpoints Analíticos:** Rutas que consolidan datos para el frontend (ventas mensuales, insumos con stock crítico según `stock_minimo`, margen por producto).

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

*(Se completa al finalizar la Fase 1: comandos de `docker-compose up`, migraciones Alembic y seed inicial.)*
