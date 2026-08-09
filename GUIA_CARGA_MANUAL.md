# GUÍA DE CARGA MANUAL — ERP Arpia

**Fecha**: 2026-08-09 · **Estado**: Base de datos vacía (solo esquema + usuario admin) · **Método**: cargar desde la app lo que se pueda y desde DBeaver lo que no.

---

## RESUMEN EN 30 SEGUNDOS

**Desde la app** (mantienen consistencia automática): Tipos de producto, Categorías de insumos, Proveedores, Clientes, Socios, Insumos (con stock y costo inicial), Productos, Variantes, BOM, Compras (fecha de hoy), Ventas (actuales), Movimientos de finanzas (y editar la fecha después), Devoluciones, Usuarios.

**Solo desde DBeaver** (la app NO permite): compras con fecha histórica, ventas con fecha histórica, editar/eliminar compras, editar/eliminar ventas, editar/eliminar devoluciones. ⚠️ Al insertar compras/ventas directo en DBeaver hay que **ajustar el stock/costo del insumo a mano** (la app lo hace sola; DBeaver no).

**Dato clave**: los movimientos de finanzas se crean desde la app y la fecha se **edita después con el botón Editar** — no hace falta DBeaver para el histórico de finanzas.

---

## 0. CÓMO CONECTAR DESDE DBEAVER

1. Abrir DBeaver → Nueva conexión → **PostgreSQL**.
2. Datos de conexión:

| Campo | Valor |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `arpia` |
| Username | `arpia` |
| Password | `arpia_secret` |

3. Test Connection → OK → Finish.

**IMPORTANTE en DBeaver**: los nombres de las tablas están entre comillas y con mayúsculas (`"Insumos"`, `"Ventas"`, `"BOM_Insumos"`, etc.). En las consultas SQL SIEMPRE van con comillas dobles: `SELECT * FROM "Insumos";`.

**Login de la app**: `admin@arpia.com` / `Admin123!` (usuario admin ya creado).

---

## 1. ORDEN OBLIGATORIO DE CARGA

Por las claves foráneas, este orden es obligatorio:

```
1. Tipos_Producto          (sin dependencias)
2. Categorias_Insumos      (sin dependencias)
3. Socios_Configuracion    (sin dependencias — pero la suma de % debe ser 100)
4. Proveedores             (sin dependencias)
5. Clientes                (sin dependencias)
6. Usuarios                (sin dependencias — opcional, ya hay admin)
7. Insumos                 (depende de Categorias_Insumos)
8. Productos               (depende de Tipos_Producto)
9. Variantes_Producto      (depende de Productos)
10. BOM_Insumos            (depende de Productos + Insumos + Variantes)
11. BOM_Productos          (depende de Productos — combos)
12. Compras_Insumos        (depende de Insumos + Proveedores)
13. Ventas + Detalle_Ventas (depende de Clientes + Productos + Variantes)
14. Movimientos_Financieros (depende de Socios_Configuracion)
15. Devoluciones + Items   (depende de Ventas + Productos)
```

---

## 2. QUÉ SE PUEDE HACER DESDE LA APP vs DBeaver

### RESUMEN RÁPIDO

| Entidad | Crear | Editar | Eliminar | Fecha manual |
|---|---|---|---|---|
| Tipos de producto | ✅ App | ✅ App | ✅ App | — |
| Categorías de insumos | ✅ App | ✅ App | ✅ App | — |
| Socios | ✅ App | ✅ App (solo %) | ✅ App | — |
| Proveedores | ✅ App | ✅ App | ✅ App | — |
| Clientes | ✅ App | ✅ App | ✅ App | — |
| Usuarios | ✅ App | ✅ App | ✅ App | — |
| Insumos (incl. stock/costo) | ✅ App | ✅ App | ✅ App | — |
| Productos | ✅ App | ✅ App | ✅ App | — |
| Variantes | ✅ App | ✅ App | ✅ App | — |
| BOM insumos / combos | ✅ App | ✅ App | ✅ App | — |
| Compras | ✅ App | ❌ NO editar | ❌ NO eliminar | ❌ **siempre now()** |
| Ventas | ✅ App | ❌ NO editar | ❌ NO eliminar | ❌ **siempre now()** |
| Movimientos financieros | ✅ App | ✅ App (PATCH) | ✅ App (soft) | ⚠️ crear now(), **editar después sí** |
| Devoluciones | ✅ App | ❌ NO editar | ❌ NO eliminar | ❌ siempre now() |

---

### 2.1 DESDE LA APP (pantallas)

| Pantalla | Qué permite |
|---|---|
| **Maestros** | CRUD completo de Clientes, Proveedores, Tipos de producto, Categorías de insumos |
| **Inventario** | CRUD de Insumos (incluye `stock_actual`, `stock_minimo`, `costo_promedio_actual` al crear/editar) + registrar compras |
| **Productos** | CRUD de Productos, Variantes, BOM de insumos y BOM de combos |
| **Ventas** | Registrar venta (elige cliente, canal, detalles) |
| **Devoluciones** | Registrar devolución (parcial o total) |
| **Finanzas** | CRUD de movimientos (crear, **editar**, eliminar) + socios + liquidaciones |
| **Usuarios** | CRUD de usuarios |
| **Omisiones** | Ver log de omisiones de migración, marcar resuelta |
| **Dashboard** | Analíticos (ventas mensuales, bajo stock, márgenes) |

### 2.2 SOLO DESDE DBeaver (lo que la app NO permite)

1. **Compras con fecha histórica** — la app sella `fecha_compra = now()` al crear; no hay forma de setear una fecha vieja desde la UI. Si querés registrar compras del pasado, INSERT directo en DBeaver con la fecha que corresponda.
2. **Ventas con fecha histórica** — la app sella `fecha = now()` al registrar; el `costo_unitario_aplicado` lo calcula el sistema con el costo actual. Para ventas pasadas con costo histórico, INSERT directo en `Ventas` + `Detalle_Ventas`.
3. **Editar/eliminar compras** — la app solo crea y lista. Correcciones → DBeaver.
4. **Editar/eliminar ventas** — la app solo crea y lista (anular = devolución). Correcciones → DBeaver.
5. **Editar/eliminar devoluciones** — la app solo crea y lista. Correcciones → DBeaver.
6. **Stock/costo inicial masivo** — se puede desde la app insumo por insumo (campo stock/costo en el form), pero para cargar muchos es más rápido un UPDATE en DBeaver.
7. **Migracion_Omisiones** — solo la puebla el proceso de migración; la app solo la lee y marca resuelta. No insertar a mano salvo necesidad puntual.

---

## 3. ESTRUCTURA DE CADA TABLA (para INSERT manual)

> Las columnas marcadas **NO** son obligatorias. Los `id` los genera la secuencia: **NO los pongas** en el INSERT (dejá que se auto-generen).

### Tipos_Producto
```sql
INSERT INTO "Tipos_Producto" (nombre) VALUES ('Lencería');
-- columnas: id (auto), nombre (único, obligatorio)
```

### Categorias_Insumos
```sql
INSERT INTO "Categorias_Insumos" (nombre) VALUES ('Telas');
-- columnas: id (auto), nombre (único, obligatorio)
```

### Socios_Configuracion
```sql
INSERT INTO "Socios_Configuracion" (nombre, porcentaje_participacion)
VALUES ('Valqui', 40.0);
-- columnas: id (auto), nombre (único), porcentaje_participacion > 0
-- ⚠️ LA SUMA DE TODOS LOS SOCIOS DEBE DAR EXACTAMENTE 100 (la app lo valida)
```

### Proveedores
```sql
INSERT INTO "Proveedores" (nombre, ubicacion, url, contacto)
VALUES ('Bexxhamel', 'Cali', 'https://...', 'Ana');
-- columnas: id (auto), nombre (obligatorio); ubicacion/url/contacto opcionales
```

### Clientes
```sql
INSERT INTO "Clientes" (nombre, documento_identidad, email, telefono)
VALUES ('María Pérez', '1002003001', 'maria@mail.com', '3001234567');
-- columnas: id (auto), nombre (obligatorio); documento/email/telefono opcionales
-- created_at / updated_at se auto-generan
```

### Usuarios
```sql
-- ⚠️ password_hash es un hash bcrypt: NO se puede inventar a mano fácil.
-- Mejor crear usuarios desde la app (pantalla Usuarios).
-- roles permitidos: 'admin' | 'operador' | 'consulta'
```

### Insumos
```sql
INSERT INTO "Insumos" (categoria_id, nombre, unidad_medida, stock_actual, stock_minimo, costo_promedio_actual)
VALUES (1, 'Tela maya negra', 'm', 50.0, 10.0, 12000.0);
-- columnas: id (auto), categoria_id (FK), nombre, unidad_medida,
--           stock_actual, stock_minimo, costo_promedio_actual (todos obligatorios)
-- unidades típicas: 'm', 'cm', 'un', 'kg', 'cm2'
-- ⚠️ los valores de dinero/stock van SIN comillas como números decimales
```

### Productos
```sql
INSERT INTO "Productos" (tipo_producto_id, nombre, requiere_fabricacion, costos_operativos_fijos, precio_venta_sugerido)
VALUES (1, 'Corset Lazo', true, 5000.0, 95000.0);
-- columnas: id (auto), tipo_producto_id (FK), nombre,
--           requiere_fabricacion (true/false), costos_operativos_fijos, precio_venta_sugerido
```

### Variantes_Producto
```sql
INSERT INTO "Variantes_Producto" (producto_id, nombre_variante, precio_venta)
VALUES (1, 'Negro - M', 95000.0);
-- columnas: id (auto), producto_id (FK), nombre_variante, precio_venta (opcional)
```

### BOM_Insumos (receta: qué insumos consume un producto)
```sql
INSERT INTO "BOM_Insumos" (producto_id, insumo_id, variante_id, cantidad_requerida, porcentaje_desperdicio)
VALUES (1, 3, NULL, 0.5, 5.0);
-- columnas: producto_id (FK), insumo_id (FK), cantidad_requerida, porcentaje_desperdicio
--           variante_id opcional (NULL = aplica a todas las variantes)
-- ⚠️ si variante_id es NULL, NO crear dos filas con el mismo (producto, insumo, NULL):
--    el sistema no puede distinguirlas (la app evita duplicados)
```

### BOM_Productos (combos: qué productos incluye un combo)
```sql
INSERT INTO "BOM_Productos" (combo_id, producto_incluido_id, cantidad)
VALUES (5, 2, 1.0);
-- columnas: combo_id (FK al producto combo), producto_incluido_id (FK), cantidad
```

### Compras_Insumos (solo DBeaver si querés fecha histórica)
```sql
INSERT INTO "Compras_Insumos" (insumo_id, proveedor_id, fecha_compra, cantidad_comprada, precio_unitario_compra)
VALUES (3, 1, '2025-10-25 10:00:00+00', 40.0, 12500.0);
-- columnas: insumo_id (FK), fecha_compra (obligatoria — TIMESTAMPTZ),
--           cantidad_comprada, precio_unitario_compra; proveedor_id opcional
-- ⚠️ la app NO permite editar/eliminar compras ni setear fecha; todo esto es DBeaver
-- ⚠️ al INSERTAR directo NO se actualiza automáticamente el stock/costo del insumo:
--    hay que ajustar "Insumos".stock_actual y costo_promedio_actual a mano
```

### Ventas + Detalle_Ventas (solo DBeaver si querés ventas históricas)
```sql
-- 1) La venta:
INSERT INTO "Ventas" (fecha, cliente_id, descuento_porcentaje, estado, total_venta, canal_venta)
VALUES ('2025-12-13 15:00:00+00', 1, 0.0, 'completada', 95000.0, 'whatsapp');
-- 2) Los detalles (una fila por producto vendido):
INSERT INTO "Detalle_Ventas" (venta_id, producto_id, variante_id, cantidad, precio_unitario_aplicado, costo_unitario_aplicado)
VALUES (1, 1, NULL, 1.0, 95000.0, 42000.0);
-- estados permitidos: 'completada' | 'anulada'
-- canales permitidos: 'web' | 'whatsapp' | 'instagram' | 'feria'
-- ⚠️ la app NO permite editar/eliminar ventas; correcciones → DBeaver
-- ⚠️ al INSERTAR directo NO se descuenta el stock: hay que ajustar "Insumos".stock_actual a mano
```

### Movimientos_Financieros
```sql
-- Desde la app: crear (fecha = hoy) → después editar la fecha con el botón Editar.
-- Desde DBeaver directo (para histórico):
INSERT INTO "Movimientos_Financieros" (fecha, tipo, descripcion, monto, socio_id, estado)
VALUES ('2024-02-17 00:00:00+00', 'Inversion', 'Compra máquina', 2500000.0, 1, 'activo');
-- tipos permitidos: 'Gasto' | 'Inversion' | 'Retiro'
-- estado: 'activo' (visible) | 'inactivo' (borrado lógico)
-- socio_id opcional (NULL = sin socio)
-- liquidacion_id: NO tocarlo (lo genera el sistema de liquidaciones)
```

### Devoluciones + Items_Devolucion (solo DBeaver para correcciones)
```sql
-- La app las crea (parcial o total) y descontar/restaurar stock automáticamente.
-- Para correcciones manuales:
INSERT INTO "Devoluciones" (venta_id, fecha, motivo, monto_reembolsado, tipo, usuario_id)
VALUES (1, '2026-01-05 10:00:00+00', 'Cambio de talla', 95000.0, 'total', 1);
-- tipos permitidos: 'parcial' | 'total'
```

---

## 4. VALORES PERMITIDOS (CHECK constraints)

| Columna | Valores permitidos |
|---|---|
| `Usuarios.rol` | `admin`, `operador`, `consulta` |
| `Ventas.estado` | `completada`, `anulada` |
| `Ventas.canal_venta` | `web`, `whatsapp`, `instagram`, `feria` |
| `Devoluciones.tipo` | `parcial`, `total` |
| `Movimientos_Financieros.tipo` | `Gasto`, `Inversion`, `Retiro` |
| `Socios_Configuracion.porcentaje_participacion` | > 0 (y la suma de todos = 100) |

---

## 5. TRUCOS Y ADVERTENCIAS

1. **Nombres con comillas**: en DBeaver siempre `"NombreTabla"` con comillas dobles.
2. **No pongas el `id`** en los INSERT — la secuencia lo genera. Si necesitás el id recién creado: en DBeaver tras el INSERT mirá la fila, o usá `RETURNING id;`.
3. **Montos y stock**: NUMERIC(15,4) — usar punto decimal (`12500.5`), no coma.
4. **Fechas**: siempre con `+00` al final (zona UTC) o el formato `'2025-10-25 00:00:00+00'`.
5. **INSERT directo de compras/ventas NO actualiza stock/costo** — ajustá `Insumos.stock_actual` / `costo_promedio_actual` a mano después.
6. **Socios**: si insertás desde DBeaver y la suma no da 100, la app va a rechazar la próxima creación de socio — respetá la invariante.
7. **Variantes NULL en BOM**: no dupliques `(producto_id, insumo_id, NULL)`.
8. **Migracion_Omisiones**: es solo lectura desde la app (log de la migración). No es para cargar datos.
9. **Reiniciar secuencias si borraste filas**: si insertás con id manual y después dejás que la secuencia avance, podés pisar ids. Mejor: siempre dejar que los id se auto-generen.

---

## 6. PLAN SUGERIDO DE TRABAJO (desde la app primero)

1. **App → Maestros**: cargar Tipos de producto, Categorías, Proveedores, Clientes.
2. **App → Finanzas → Socios**: cargar los 3 socios (la suma debe dar 100).
3. **App → Inventario**: cargar insumos con su stock y costo inicial.
4. **App → Productos**: cargar productos, variantes y BOM (recetas/combos).
5. **App → Compras**: registrar compras (fecha de hoy o aceptar now()). Para histórico → DBeaver + ajustar stock/costo.
6. **App → Ventas**: registrar ventas actuales. Para histórico → DBeaver + ajustar stock.
7. **App → Finanzas → Movimientos**: cargar gastos/inversiones; usar Editar para fijar fechas pasadas.
8. **App → Omisiones**: revisar si quedó algo del proceso de migración.

**Regla de oro**: todo lo actual se carga desde la app (que mantiene stock/costo/estados consistentes); lo histórico (fechas pasadas) se carga en DBeaver y se ajusta el stock/costo manualmente.
