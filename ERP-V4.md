# ERP Arpía — Estado V4: Migración a Datos Reales (Postgres)

> **Fecha:** 2026-08-24  
> **Versión:** V4 — Fuente de verdad  
> **Propósito:** Documentar el estado actual del ERP Atelier Arpía, qué parte ya opera con datos reales de Postgres, qué parte sigue en mock de frontend, y el plan para migrar **TODO el frontend a datos reales manteniendo la UI actual intacta**.  
> **Principio rector:** `Misma UI, datos reales` — Ninguna vista `*.vue` cambia de layout/flujo; solo cambia la fuente de datos (de Pinia hardcodeado a API + Postgres).

---

## 1. Resumen Ejecutivo

El ERP Atelier Arpía tiene un backend sólido con ~78 handlers y 17 tablas activas en Postgres que ya cubren el núcleo de insumos, productos, variantes, BOM, costeo, ventas, finanzas y analíticos. El frontend, en cambio, está 100% desacoplado de ese backend: `src/stores/atelier.ts` (3403 líneas, 17 entidades + 8 maestros, 35 funciones CRUD locales) es la única fuente de datos y **ninguna vista hace fetch real**. V4 consiste en cerrar esa brecha sin reescribir UI: extender el modelo de datos donde hay gaps, completar endpoints y hacer que el frontend consuma la API mediante un adapter conmutable (`USE_MOCK=false`), deprecando progresivamente el Pinia mock.

---

## 2. Qué está BIEN — Ya opera con datos reales

Estas áreas **no requieren cambios de esquema ni de UI** para operar en modo real. El backend ya persiste y expone datos; el frontend solo necesita conmutar la fuente.

| Dominio | Tablas Postgres | Endpoints existentes | Estado | Acción V4 |
|---|---|---|---|---|
| **Insumos básicos** | `Insumos`, `Categorias_Insumos`, `Compras_Insumos` | `insumos`, `categorias-insumos` (CRUD + stock) | ✅ Listo | Conmutar frontend a API |
| **Productos + Variantes + BOM + Costo** | `Productos`, `Tipos_Producto`, `Variantes_Producto`, `BOM_Insumos`, `BOM_Productos` | `productos`, `variantes`, `BOM`, `costo` (cálculo real) | ✅ Listo | Conmutar frontend a API |
| **Ventas (core)** | `Ventas`, `Detalle_Ventas` | `ventas` (CRUD + detalle) | ✅ Listo (core) | Ampliar solo `canal_venta` + `metodo_pago` (ver §5.2) |
| **Finanzas — Movimientos** | `Movimientos_Financieros` | `finanzas/movimientos`, `finanzas/socios` | ✅ Listo | Conmutar; ampliar Socios en Fase 2 |
| **Finanzas — Socios (básico)** | `Socios_Configuracion` (campos base) | `finanzas/socios`, `finanzas/liquidaciones` (simulado) | ⚠️ Parcial | Ver gaps §5.3 |
| **Analíticos / Dashboard** | Vistas sobre ventas, movimientos, productos | 7 endpoints `analiticos` | ✅ Listo | Conmutar DashboardView a API |
| **Clientes (básico)** | `Clientes` (4 campos: nombres, teléfono, email, etc.) | `clientes` (CRUD básico) | ⚠️ Parcial | Extender a CRM completo en Fase 1 |
| **Transversales** | `Usuarios`, `AuditLog`, `RefreshToken`, `Migracion_Omisiones` | `auth`, `usuarios`, `audit`, `omisiones` | ✅ Listo | Sin cambios |

> **Nota Proveedores:** La tabla `Proveedores` fue **eliminada en la migración `0008`** por decisión de dominio (Atelier Arpía no gestiona proveedores como entidad propia; las compras se registran directo en `Compras_Insumos`). No se debe recrear. El maestro `ProveedorMaestro` que aparece como gap en §5.4 es un catálogo liviano de referencia para formularios, no la tabla histórica eliminada — si se necesita, se creará como `maestros_proveedores` con alcance acotado.

---

## 3. Qué está MAL — Matriz central de gaps

> Fuente única frontend: `src/stores/atelier.ts` — 3403 líneas, 100% Pinia `ref()` hardcodeado, 35 funciones CRUD locales. **Ninguna vista hace fetch real.** Todas las vistas listadas consumen solo ese store.

| # | Entidad Frontend (atelier.ts) | Vistas que la consumen | Tabla Backend actual | Gap | Severidad |
|---|---|---|---|---|---|
| 1 | `ClienteCRM` | `ClientesView` | `Clientes` (4 cols) | Faltan **10 columnas**: `ciudad`, `direccion`, `tipo`, `talla_habitual`, `talla_superior`, `talla_inferior`, `categoria_preferida`, `tipo_producto_frecuente`, `notas`, `medidas JSONB`. Endpoint incompleto. | 🔴 CRÍTICO |
| 2 | `Venta` (`canal_venta`) | `VentasView` | `Ventas.canal_venta` (enum) | **Mismatch de enum**: frontend usa `web / whatsapp / instagram / feria`; DB usa `Showroom Pereira` etc. Valores no coinciden → validación falla. | 🔴 CRÍTICO |
| 3 | `Venta` (`metodo_pago`) | `VentasView` | `Ventas` | **Falta columna** `metodo_pago` en DB y en schema/endpoint. | 🔴 CRÍTICO |
| 4 | `Socia` | `FinanzasView` | `Socios_Configuracion` | Faltan **8 columnas**: `rol`, `banco` (+ 6 adicionales a relevar: datos bancarios, porcentaje, estado, etc.). | 🔴 CRÍTICO |
| 5 | `Liquidacion` | `FinanzasView` | — (sin tabla) | **Sin tabla propia.** Hoy se simula con `Movimientos_Financieros`. Requiere `liquidaciones` + relación a socia y período. | 🔴 CRÍTICO |
| 6 | `Anticipo` | `FinanzasView` | — (sin tabla) | **Sin tabla propia.** Simulado con `Movimientos_Financieros`. Requiere `anticipos` + relación a socia. | 🟠 ALTO |
| 7 | `ProveedorMaestro` | `MaestrosView` (pestaña Proveedores) | — (sin tabla) | **Falta tabla completa.** Catálogo de referencia para formularios. | 🟠 ALTO |
| 8 | `CanalVenta` (maestro) | `MaestrosView` (pestaña Canales) | — (sin tabla) | **Falta tabla completa.** Debe unificar enum de `Ventas.canal_venta`. | 🟠 ALTO |
| 9 | `MetodoPago` (maestro) | `MaestrosView` (pestaña Métodos de Pago) | — (sin tabla) | **Falta tabla completa.** Catálogo para `Ventas.metodo_pago`. | 🟠 ALTO |
| 10 | `UbicacionTaller` | `MaestrosView` (pestaña Ubicaciones) | — (sin tabla) | **Falta tabla completa.** | 🟡 MEDIO |
| 11 | `TallaEstandar` | `MaestrosView` (pestaña Tallas) | — (sin tabla) | **Falta tabla completa.** | 🟡 MEDIO |
| 12 | `ProductoSinTalla` | `MaestrosView` (pestaña Productos sin talla) | — (sin tabla) | **Falta tabla completa.** | 🟡 MEDIO |
| 13 | `ParametrosCosteo` | `MaestrosView` (pestaña Parámetros) | — (sin tabla) | **Falta tabla completa.** Parámetros de cálculo de costo/markup. | 🟠 ALTO |
| 14 | `InsumoAtelier` (campos ext.) | `InsumosView` | `Insumos` (básico) | Faltan **4 columnas**: `codigo`, `descripcion`, `tipo`, `ubicacion`. | 🟠 ALTO |
| 15 | `RecetaBOM` (campos ext.) | `ProductosView`, `ProduccionView` | `BOM_Insumos` / `BOM_Productos` | Faltan **3 campos**: `fases`, `tiempo_estimado`, `markup` a nivel receta. | 🟠 ALTO |
| 16 | `PrendaConfeccionada` | `PrendasListasView` | — (sin tabla) | **Falta DB total.** Sin tabla, sin endpoints, sin persistencia. | 🔴 CRÍTICO |
| 17 | `PedidoProduccion` | `ProduccionView` | — (sin tabla) | **Falta DB total.** Sin tabla, sin endpoints, sin persistencia. | 🔴 CRÍTICO |

**Leyenda severidad:** 🔴 CRÍTICO = bloquea operación real / pérdida de datos · 🟠 ALTO = flujo incompleto pero hay workaround · 🟡 MEDIO = catálogo/maestro no bloqueante.

---

## 4. Gaps Detallados por Dominio

### 4.1 Clientes CRM

- **Actual:** `Clientes` con solo 4 campos (nombre, teléfono, email + uno adicional base). Suficiente para registrar una venta, insuficiente para CRM de atelier (medidas, preferencias, historial).
- **Faltan 10 columnas:**
  - `ciudad` — para segmentación y logística.
  - `direccion` — entrega / showroom.
  - `tipo` — ej. `frecuente / nuevo / mayorista` (definir enum en spec).
  - `talla_habitual`, `talla_superior`, `talla_inferior` — base para recomendaciones.
  - `categoria_preferida`, `tipo_producto_frecuente` — personalización.
  - `notas` — texto libre de atelier.
  - `medidas` — `JSONB` (busto, cintura, cadera, largo, etc. — esquema flexible por producto).
- **Endpoint:** `clientes` existe pero expone solo campos base; falta ampliar schema de creación/actualización y filtros por `tipo`/`ciudad`/`talla`.

### 4.2 Ventas

- **Enum `canal_venta` desalineado:**
  - Frontend (atelier.ts): `web | whatsapp | instagram | feria`
  - Backend (`Ventas.canal_venta`): valores tipo `Showroom Pereira` etc.
  - **Impacto:** cualquier venta creada desde UI falla validación o se persiste con valor no esperado.
  - **Solución:** unificar en tabla maestra `maestros_canales_venta` (ver §4.4) y migrar enum a FK o enum alineado. Decisión a tomar en Fase 1 (recomendado: FK a maestro para permitir agregar canales sin migración).
- **Falta `metodo_pago`:**
  - No existe columna en `Ventas`. Frontend la gestiona en memoria.
  - Requiere `metodo_pago VARCHAR(50)` (o FK a `maestros_metodos_pago`) + validación en schema.

### 4.3 Finanzas — Socias / Liquidaciones / Anticipos

- **Socia (`Socios_Configuracion`):** faltan 8 columnas. Confirmadas por análisis: `rol`, `banco` + 6 adicionales a relevar en spec (candidatas: `tipo_cuenta`, `numero_cuenta`, `titular_cuenta`, `porcentaje_participacion`, `fecha_alta`, `estado`). No inventar valores finales hasta spec; la migración debe dejar placeholders documentados.
- **Liquidaciones:** hoy no hay tabla `liquidaciones`. El endpoint `finanzas/liquidaciones` simula a partir de `Movimientos_Financieros`. Se requiere tabla propia con `socia_id`, `periodo_desde`, `periodo_hasta`, `monto_total`, `estado`, `movimientos_ids` (o tabla puente).
- **Anticipos:** idem — sin tabla `anticipos`. Simulado con movimientos. Requiere `anticipos` con `socia_id`, `monto`, `fecha`, `estado`, `liquidacion_id` (nullable, para descuento en liquidación).

### 4.4 Maestros — 7 pestañas de `MaestrosView`

Todas las pestañas de `MaestrosView` leen/escriben solo en `atelier.ts`. **Faltan 7 tablas completas:**

| Pestaña | Tabla propuesta | Propósito |
|---|---|---|
| Proveedores | `maestros_proveedores` | Catálogo liviano de referencia (nombre, contacto, rubro). No es la tabla histórica eliminada en 0008. |
| Canales de Venta | `maestros_canales_venta` | Unifica `Ventas.canal_venta`. Semilla con valores actuales de ambos lados y deja abierto a nuevos. |
| Métodos de Pago | `maestros_metodos_pago` | Catálogo para `Ventas.metodo_pago`. |
| Ubicaciones Taller | `maestros_ubicaciones_taller` | Ubicaciones físicas (ej. `Taller Pereira`, `Depósito`). |
| Tallas Estándar | `maestros_tallas_estandar` | Talle → medidas base. |
| Productos sin Talla | `maestros_productos_sin_talla` | Flag/catálogo de productos que no requieren talle. |
| Parámetros de Costeo | `maestros_parametros_costeo` | Parámetros globales de cálculo (margen, overhead, moneda). |

> Cada maestro requiere CRUD completo (ver §8). Semillas iniciales deben reflejar los valores hoy hardcodeados en `atelier.ts`.

### 4.5 Inventario / Recetas / Prendas / Pedidos

- **InsumoAtelier:** a `Insumos` le faltan `codigo` (SKU interno), `descripcion`, `tipo` (ej. `tela / avío / packaging`), `ubicacion` (FK o texto a `maestros_ubicaciones_taller`).
- **RecetaBOM:** a `BOM_Insumos` / `BOM_Productos` les faltan `fases` (JSONB o tabla `bom_fases`), `tiempo_estimado_minutos`, `markup_porcentual` a nivel receta. Afecta cálculo de costo real.
- **PrendaConfeccionada:** sin tabla. Entidad de stock de producto terminado listo para venta (distinto de `Variantes_Producto` que es definición). Requiere `prendas_confeccionadas` con `variante_id`, `talla`, `estado`, `ubicacion`, `costo_real`, `fecha_confeccion`.
- **PedidoProduccion:** sin tabla. Requiere `pedidos_produccion` con `producto_id`, `variante_id`, `cantidad`, `estado`, `prioridad`, `fecha_pedido`, `fecha_entrega_estimada`, `prendas_ids`.

### 4.6 Parámetros

- `ParametrosCosteo` sin tabla — ver `maestros_parametros_costeo` en §4.4. Debe ser singleton o versionado (una fila activa). Incluye al menos: `margen_default`, `costo_hora_taller`, `moneda`, `iva_porcentual`.

---

## 5. Roadmap por Fases

> Ordenado por **impacto operativo** y **dependencias**. Cada fase cierra con frontend conmutado a API real para su dominio.

### Fase 1 — Clientes extendido + Ventas canal/método de pago
**Objetivo:** el CRM y el flujo de ventas operan 100% en Postgres.

- [ ] Migración Alembic: extender `Clientes` con 10 columnas (§7.1)
- [ ] Migración Alembic: corregir `Ventas.canal_venta` + agregar `Ventas.metodo_pago` (§7.2)
- [ ] Seed de `maestros_canales_venta` y `maestros_metodos_pago` mínimos para que ventas no quede bloqueada (puede adelantarse de Fase 3)
- [ ] Backend: ampliar `schemas.ClienteCreate/Update` + filtros
- [ ] Backend: ampliar `schemas.VentaCreate` + validación canal/método
- [ ] Frontend: `services/api/clientes.ts` + `services/api/ventas.ts` + adapter `USE_MOCK` (§9)
- [ ] Verificación: crear cliente con medidas JSONB y venta con canal+medio de pago desde UI, persistencia en `psql`

| Estimación Fase 1 | Cantidad |
|---|---|
| Tablas nuevas | 0 (solo ALTER) — 2 maestros opcionales adelantados |
| Migraciones Alembic | 2 |
| Endpoints nuevos/ampliados | 2 ampliados (`clientes`, `ventas`) |
| Services frontend | 2 |

### Fase 2 — Socios ampliado + Liquidaciones / Anticipos
**Objetivo:** finanzas de socias sin simulación.

- [ ] Migración: ampliar `Socios_Configuracion` con 8 columnas (§7.3)
- [ ] Migración: crear `liquidaciones` (§7.4)
- [ ] Migración: crear `anticipos` (§7.5)
- [ ] Backend: CRUD `finanzas/liquidaciones` real (cálculo por período + movimientos asociados)
- [ ] Backend: CRUD `finanzas/anticipos` + descuento en liquidación
- [ ] Frontend: `services/api/socios.ts`, `services/api/liquidaciones.ts`, `services/api/anticipos.ts`
- [ ] Verificación: generar liquidación de un período y verificar que anticipos se descuentan

| Estimación Fase 2 | Cantidad |
|---|---|
| Tablas nuevas | 2 (`liquidaciones`, `anticipos`) |
| Migraciones Alembic | 3 |
| Endpoints nuevos/ampliados | 3 (1 ampliado + 2 nuevos) |
| Services frontend | 3 |

### Fase 3 — 6 maestros faltantes (catálogos)
**Objetivo:** `MaestrosView` deja de ser mock. Desbloquea selects de todo el ERP.

- [ ] Migración: crear 6 tablas `maestros_*` restantes (§7.6) — si canales/métodos ya se crearon en Fase 1, quedan 5 aquí
- [ ] Backend: 6× CRUD `maestros/*` (o 5 si aplica) + seeds con valores de `atelier.ts`
- [ ] Frontend: `services/api/maestros.ts` (un service con sub-recursos o uno por maestro)
- [ ] Verificación: cada pestaña de `MaestrosView` lista/crea/edita/borra contra DB y persiste recargando

| Estimación Fase 3 | Cantidad |
|---|---|
| Tablas nuevas | 6 (o 5 si 2 ya en Fase 1) |
| Migraciones Alembic | 1–2 (pueden agruparse) |
| Endpoints nuevos | 6 (o 5) |
| Services frontend | 1 agrupado |

### Fase 4 — Insumos / Recetas / Prendas / Pedidos
**Objetivo:** inventario y producción con persistencia real.

- [ ] Migración: ampliar `Insumos` con 4 columnas (§7.7)
- [ ] Migración: ampliar `BOM_Insumos`/`BOM_Productos` con `fases`, `tiempo_estimado`, `markup` (§7.8)
- [ ] Migración: crear `prendas_confeccionadas` (§7.9)
- [ ] Migración: crear `pedidos_produccion` (§7.10)
- [ ] Backend: ampliar `insumos`, `BOM/costo`; crear `prendas-confeccionadas`, `pedidos-produccion`
- [ ] Frontend: `services/api/insumos.ts` (ampliar), `services/api/prendas.ts`, `services/api/pedidos-produccion.ts`
- [ ] Verificación: crear insumo con código/ubicación, receta con fases/tiempo, prenda y pedido asociados

| Estimación Fase 4 | Cantidad |
|---|---|
| Tablas nuevas | 2 (`prendas_confeccionadas`, `pedidos_produccion`) |
| Migraciones Alembic | 4 |
| Endpoints nuevos/ampliados | 4 (2 ampliados + 2 nuevos) |
| Services frontend | 3 |

### Fase 5 — Switch frontend a API real y deprecación de Pinia mock
**Objetivo:** toda la UI consume Postgres. `atelier.ts` queda como fallback solo para tests.

- [ ] Introducir flag global `USE_MOCK` (env `VITE_USE_MOCK=false` por defecto en prod) y `services/api/__mode.ts`
- [ ] Adapter por dominio: cada store/composable elige `api.*` si `USE_MOCK=false`, o `atelier.ts` si `true`
- [ ] Mantener `*.vue` intactos — solo cambia el `import` de datos (via adapter, no edición masiva de vistas)
- [ ] Agregar badge de modo en layout + endpoint `GET /api/__mode` (§10)
- [ ] Deprecar funciones CRUD locales de `atelier.ts` (marcar `@deprecated`, no borrar hasta V4.1)
- [ ] Smoke test E2E: navegar Clientes → Ventas → Finanzas → Maestros → Insumos → Productos → Prendas → Producción → Dashboard sin datos mock
- [ ] Documentar en `CambiosV3.md` el corte V4

| Estimación Fase 5 | Cantidad |
|---|---|
| Tablas/migraciones | 0 |
| Endpoints nuevos | 1 (`/__mode`) |
| Cambios frontend | Adapter + flag + badge |

**Totales estimados V4 completo:** ~10 tablas nuevas, ~10–12 migraciones Alembic, ~16–18 endpoints nuevos/ampliados, ~9–10 services frontend.

---

## 6. Cambios DB Propuestos (Migraciones Alembic)

> Nombres de revisiones sugeridos. Tipos Postgres. Ajustar `nullable`/`default` en spec fina. Todas las migraciones deben ser reversibles (`downgrade`).

### 6.1 `0009_extend_clientes_crm.py` — `Clientes` +10 columnas
```python
op.add_column('clientes', sa.Column('ciudad', sa.String(100), nullable=True))
op.add_column('clientes', sa.Column('direccion', sa.String(255), nullable=True))
op.add_column('clientes', sa.Column('tipo', sa.String(50), nullable=True))  # ej. frecuente/nuevo/mayorista
op.add_column('clientes', sa.Column('talla_habitual', sa.String(20), nullable=True))
op.add_column('clientes', sa.Column('talla_superior', sa.String(20), nullable=True))
op.add_column('clientes', sa.Column('talla_inferior', sa.String(20), nullable=True))
op.add_column('clientes', sa.Column('categoria_preferida', sa.String(100), nullable=True))
op.add_column('clientes', sa.Column('tipo_producto_frecuente', sa.String(100), nullable=True))
op.add_column('clientes', sa.Column('notas', sa.Text(), nullable=True))
op.add_column('clientes', sa.Column('medidas', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
# Índices útiles
op.create_index('ix_clientes_tipo', 'clientes', ['tipo'])
op.create_index('ix_clientes_ciudad', 'clientes', ['ciudad'])
```

### 6.2 `0010_fix_ventas_canal_y_metodo_pago.py` — `Ventas`
```python
# Opción A (recomendada): canal_venta como FK a maestros_canales_venta
# 1) Crear maestros_canales_venta si no existe (o adelantar de 0011)
# 2) Migrar datos existentes de canal_venta a IDs del maestro
# 3) Cambiar columna a FK o alinear enum

# Mínimo viable si se mantiene VARCHAR:
op.add_column('ventas', sa.Column('metodo_pago', sa.String(50), nullable=True))
# Si se usa FK:
# op.add_column('ventas', sa.Column('metodo_pago_id', sa.Integer(), sa.ForeignKey('maestros_metodos_pago.id'), nullable=True))
# op.add_column('ventas', sa.Column('canal_venta_id', sa.Integer(), sa.ForeignKey('maestros_canales_venta.id'), nullable=True))

# Si se mantiene enum, alinear valores:
# op.alter_column('ventas', 'canal_venta', type_=sa.String(50), nullable=False)
# + seed de valores canónicos: web, whatsapp, instagram, feria, showroom_pereira, etc.
```

### 6.3 `0011_extend_socios_configuracion.py` — `Socios_Configuracion` +8 columnas
```python
op.add_column('socios_configuracion', sa.Column('rol', sa.String(50), nullable=True))
op.add_column('socios_configuracion', sa.Column('banco', sa.String(100), nullable=True))
op.add_column('socios_configuracion', sa.Column('tipo_cuenta', sa.String(50), nullable=True))
op.add_column('socios_configuracion', sa.Column('numero_cuenta', sa.String(50), nullable=True))
op.add_column('socios_configuracion', sa.Column('titular_cuenta', sa.String(150), nullable=True))
op.add_column('socios_configuracion', sa.Column('porcentaje_participacion', sa.Numeric(5,2), nullable=True))
op.add_column('socios_configuracion', sa.Column('fecha_alta', sa.Date(), nullable=True))
op.add_column('socios_configuracion', sa.Column('estado', sa.String(20), nullable=True, server_default='activo'))
# Nota: los 6 últimos son candidatos a confirmar en spec; no fijar sin validar con dominio.
```

### 6.4 `0012_create_liquidaciones.py`
```python
op.create_table('liquidaciones',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('socia_id', sa.Integer(), sa.ForeignKey('socios_configuracion.id', ondelete='CASCADE'), nullable=False),
    sa.Column('periodo_desde', sa.Date(), nullable=False),
    sa.Column('periodo_hasta', sa.Date(), nullable=False),
    sa.Column('monto_total', sa.Numeric(12,2), nullable=False, server_default='0'),
    sa.Column('monto_anticipos_descontados', sa.Numeric(12,2), nullable=False, server_default='0'),
    sa.Column('estado', sa.String(20), nullable=False, server_default='pendiente'),  # pendiente/pagada/anulada
    sa.Column('observaciones', sa.Text(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
)
op.create_index('ix_liquidaciones_socia_periodo', 'liquidaciones', ['socia_id', 'periodo_desde', 'periodo_hasta'])
```

### 6.5 `0013_create_anticipos.py`
```python
op.create_table('anticipos',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('socia_id', sa.Integer(), sa.ForeignKey('socios_configuracion.id', ondelete='CASCADE'), nullable=False),
    sa.Column('liquidacion_id', sa.Integer(), sa.ForeignKey('liquidaciones.id', ondelete='SET NULL'), nullable=True),
    sa.Column('monto', sa.Numeric(12,2), nullable=False),
    sa.Column('fecha', sa.Date(), nullable=False, server_default=sa.func.current_date()),
    sa.Column('estado', sa.String(20), nullable=False, server_default='pendiente'),  # pendiente/descontado/anulado
    sa.Column('concepto', sa.String(255), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.func.now(), nullable=False),
)
op.create_index('ix_anticipos_socia_fecha', 'anticipos', ['socia_id', 'fecha'])
```

### 6.6 `0014_create_maestros_catalogos.py` — 6–7 tablas de catálogo
```python
# Patrón por cada maestro (ejemplo: canales)
op.create_table('maestros_canales_venta',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('nombre', sa.String(100), nullable=False, unique=True),
    sa.Column('codigo', sa.String(50), nullable=True, unique=True),  # ej. web, whatsapp, showroom_pereira
    sa.Column('activo', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('orden', sa.Integer(), nullable=False, server_default='0'),
)
# Repetir para:
# maestros_metodos_pago (nombre, codigo, activo, orden)
# maestros_proveedores (nombre, contacto, telefono, email, rubro, activo)
# maestros_ubicaciones_taller (nombre, direccion, activo)
# maestros_tallas_estandar (codigo, nombre, medidas_base JSONB, activo)
# maestros_productos_sin_talla (producto_id FK nullable o nombre, motivo)
# maestros_parametros_costeo (clave, valor JSONB, descripcion) — o tabla singleton con columnas tipadas

# Seeds con valores de atelier.ts:
# op.bulk_insert('maestros_canales_venta', [
#   {'nombre': 'Web', 'codigo': 'web'}, {'nombre': 'WhatsApp', 'codigo': 'whatsapp'},
#   {'nombre': 'Instagram', 'codigo': 'instagram'}, {'nombre': 'Feria', 'codigo': 'feria'},
#   {'nombre': 'Showroom Pereira', 'codigo': 'showroom_pereira'},
# ])
```

### 6.7 `0015_extend_insumos_atelier.py` — `Insumos` +4 columnas
```python
op.add_column('insumos', sa.Column('codigo', sa.String(50), nullable=True))
op.add_column('insumos', sa.Column('descripcion', sa.Text(), nullable=True))
op.add_column('insumos', sa.Column('tipo', sa.String(50), nullable=True))  # tela/avío/packaging/etc.
op.add_column('insumos', sa.Column('ubicacion', sa.String(100), nullable=True))  # o FK a maestros_ubicaciones_taller
op.create_index('ix_insumos_codigo', 'insumos', ['codigo'], unique=True)
op.create_index('ix_insumos_tipo', 'insumos', ['tipo'])
```

### 6.8 `0016_extend_bom_receta.py` — `BOM_Insumos` / `BOM_Productos`
```python
# BOM_Insumos
op.add_column('bom_insumos', sa.Column('fases', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
op.add_column('bom_insumos', sa.Column('tiempo_estimado_minutos', sa.Integer(), nullable=True))
op.add_column('bom_insumos', sa.Column('markup_porcentual', sa.Numeric(5,2), nullable=True))
# BOM_Productos (si aplica igual)
op.add_column('bom_productos', sa.Column('fases', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
op.add_column('bom_productos', sa.Column('tiempo_estimado_minutos', sa.Integer(), nullable=True))
op.add_column('bom_productos', sa.Column('markup_porcentual', sa.Numeric(5,2), nullable=True))
# Alternativa normalizada: tabla bom_fases (bom_id, orden, nombre, minutos, costo)
```

### 6.9 `0017_create_prendas_confeccionadas.py`
```python
op.create_table('prendas_confeccionadas',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('variante_id', sa.Integer(), sa.ForeignKey('variantes_producto.id', ondelete='CASCADE'), nullable=False),
    sa.Column('talla', sa.String(20), nullable=True),
    sa.Column('estado', sa.String(30), nullable=False, server_default='disponible'),  # disponible/reservada/vendida/defectuosa
    sa.Column('ubicacion', sa.String(100), nullable=True),
    sa.Column('costo_real', sa.Numeric(12,2), nullable=True),
    sa.Column('precio_venta', sa.Numeric(12,2), nullable=True),
    sa.Column('fecha_confeccion', sa.Date(), nullable=True),
    sa.Column('pedido_id', sa.Integer(), sa.ForeignKey('pedidos_produccion.id', ondelete='SET NULL'), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.func.now(), nullable=False),
)
op.create_index('ix_prendas_variante_estado', 'prendas_confeccionadas', ['variante_id', 'estado'])
```

### 6.10 `0018_create_pedidos_produccion.py`
```python
op.create_table('pedidos_produccion',
    sa.Column('id', sa.Integer(), primary_key=True),
    sa.Column('producto_id', sa.Integer(), sa.ForeignKey('productos.id', ondelete='CASCADE'), nullable=False),
    sa.Column('variante_id', sa.Integer(), sa.ForeignKey('variantes_producto.id', ondelete='SET NULL'), nullable=True),
    sa.Column('cantidad', sa.Integer(), nullable=False),
    sa.Column('cantidad_producida', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('estado', sa.String(30), nullable=False, server_default='pendiente'),  # pendiente/en_produccion/completado/cancelado
    sa.Column('prioridad', sa.String(20), nullable=False, server_default='normal'),  # baja/normal/alta/urgente
    sa.Column('fecha_pedido', sa.Date(), nullable=False, server_default=sa.func.current_date()),
    sa.Column('fecha_entrega_estimada', sa.Date(), nullable=True),
    sa.Column('observaciones', sa.Text(), nullable=True),
    sa.Column('creado_en', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    sa.Column('actualizado_en', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
)
op.create_index('ix_pedidos_estado_prioridad', 'pedidos_produccion', ['estado', 'prioridad'])
```

---

## 7. Cambios Backend Propuestos (Endpoints y Schemas)

> Base existente: ~78 handlers. Todos los nuevos endpoints siguen el patrón actual (FastAPI + Pydantic + SQLAlchemy + audit).

### 7.1 Ampliar existentes

| Endpoint | Cambios de schema | Cambios de handler |
|---|---|---|
| `clientes` | `ClienteCreate/Update`: +10 campos (§6.1). `ClienteResponse`: idem. Filtros `?tipo=&ciudad=&q=` | `GET /clientes` con filtros, `POST/PATCH` validando `medidas` JSONB |
| `ventas` | `VentaCreate`: `canal_venta` alineado (enum o FK), `metodo_pago` nuevo. `VentaResponse` idem | Validar canal contra `maestros_canales_venta` si es FK; idem método de pago |
| `socios` (`Socios_Configuracion`) | `SocioCreate/Update`: +8 campos (§6.3) | `GET/POST/PATCH /finanzas/socios` |
| `insumos` | `InsumoCreate/Update`: +4 campos (§6.7) | `GET/POST/PATCH /insumos` |
| `BOM` / `costo` | `BOMCreate`: `fases`, `tiempo_estimado_minutos`, `markup_porcentual` | `POST /bom`, `GET /costo/{producto_id}` recalculando con nuevos campos |

### 7.2 Crear nuevos

| Endpoint | Método | Descripción |
|---|---|---|
| `finanzas/liquidaciones` | `GET /finanzas/liquidaciones?socia_id=&periodo=` `POST /finanzas/liquidaciones` `GET /finanzas/liquidaciones/{id}` `PATCH /finanzas/liquidaciones/{id}` | CRUD real (reemplaza simulación). `POST` calcula `monto_total` desde movimientos del período menos anticipos. |
| `finanzas/anticipos` | `GET /finanzas/anticipos?socia_id=&estado=` `POST /finanzas/anticipos` `PATCH /finanzas/anticipos/{id}` | CRUD anticipos. `PATCH` para asociar a liquidación. |
| `maestros/canales-venta` | `GET/POST/PATCH/DELETE` | CRUD catálogo canales |
| `maestros/metodos-pago` | `GET/POST/PATCH/DELETE` | CRUD catálogo métodos de pago |
| `maestros/proveedores` | `GET/POST/PATCH/DELETE` | CRUD catálogo proveedores (liviano) |
| `maestros/ubicaciones-taller` | `GET/POST/PATCH/DELETE` | CRUD ubicaciones |
| `maestros/tallas-estandar` | `GET/POST/PATCH/DELETE` | CRUD tallas |
| `maestros/productos-sin-talla` | `GET/POST/PATCH/DELETE` | CRUD productos sin talla |
| `maestros/parametros-costeo` | `GET /maestros/parametros-costeo` `PATCH /maestros/parametros-costeo` | Singleton/versionado |
| `prendas-confeccionadas` | `GET/POST/PATCH/DELETE` | CRUD prendas listas |
| `pedidos-produccion` | `GET/POST/PATCH/DELETE` | CRUD pedidos de producción |
| `__mode` | `GET /api/__mode` | Retorna `{ mode: "mock"|"real", db_connected: bool, version: "V4" }` para badge y diagnóstico |

**Schemas Pydantic:** cada nuevo endpoint requiere `Create`, `Update`, `Response` + validadores (ej. `medidas` como `dict` libre, `fases` como `list[dict]`).

---

## 8. Cambios Frontend Propuestos

> **Regla de oro:** `*.vue` **no se reescribe**. Se mantiene layout, estilos y flujos. Solo cambia de dónde vienen los datos.

### 8.1 Patrón Adapter + `USE_MOCK`

```
src/
  stores/atelier.ts          # ← queda como está, marcado @deprecated, solo para USE_MOCK=true y tests
  services/api/
    client.ts                # axios/fetch base (baseURL, auth header, interceptors)
    __mode.ts                # GET /api/__mode → { mode, db_connected }
    clientes.ts              # list/get/create/update/remove → /clientes
    ventas.ts                # idem → /ventas
    socios.ts                # → /finanzas/socios
    liquidaciones.ts         # → /finanzas/liquidaciones
    anticipos.ts             # → /finanzas/anticipos
    maestros.ts              # sub-recursos → /maestros/*
    insumos.ts               # → /insumos
    prendas.ts               # → /prendas-confeccionadas
    pedidos-produccion.ts    # → /pedidos-produccion
    analiticos.ts            # → /analiticos/* (ya existe, solo conmutar)
  composables/
    useMode.ts               # computed isMock = import.meta.env.VITE_USE_MOCK === 'true'
    useClientes.ts           # ejemplo: if (isMock) return atelierStore.clientes; else return api.clientes.list()
```

**Flag de entorno:**

```env
# .env / .env.production
VITE_USE_MOCK=false   # prod y dev real → API
# VITE_USE_MOCK=true  # solo para demo/offline o tests
```

**Adapter por vista (ejemplo `ClientesView.vue`):**

```ts
// composables/useClientes.ts
import { useAtelierStore } from '@/stores/atelier'
import * as apiClientes from '@/services/api/clientes'
import { useMode } from '@/composables/useMode'

export function useClientes() {
  const { isMock } = useMode()
  const atelier = useAtelierStore()
  return {
    async list(params?: any) {
      return isMock.value ? atelier.clientes : await apiClientes.list(params)
    },
    // create/update/remove igual
  }
}
```

Las vistas siguen haciendo `const { list } = useClientes()` sin saber si es mock o real.

### 8.2 Qué NO se toca

- Ningún `*.vue` cambia de template, estilos, rutas ni navegación.
- `atelier.ts` no se borra en V4 — se depreca. Se borra en V4.1 cuando el smoke E2E esté verde.
- Los 35 CRUD locales de `atelier.ts` quedan como fallback documentado.

---

## 9. Cómo Verificar que se Usa DB Real

Checklist para cualquier persona (dev, QA, dueña del atelier) para confirmar que **no se está viendo mock**.

| # | Verificación | Cómo hacerlo | Qué se espera en modo REAL |
|---|---|---|---|
| 1 | **Badge de modo en UI** | Mirar header/sidebar del ERP | Badge `● REAL — Postgres` (verde). En mock: `● MOCK — Pinia` (amarillo) |
| 2 | **Endpoint `GET /api/__mode`** | `curl http://localhost:8000/api/__mode` o DevTools → Network | `{ "mode": "real", "db_connected": true, "version": "V4" }` |
| 3 | **Network (DevTools)** | Abrir DevTools → Network → navegar Clientes/Ventas/Finanzas | Requests a `/api/clientes`, `/api/ventas`, `/api/finanzas/*`, `/api/maestros/*` con `200` y payload real. En mock no hay requests. |
| 4 | **`psql` directo** | `psql $DATABASE_URL -c "SELECT count(*) FROM clientes; SELECT * FROM ventas ORDER BY id DESC LIMIT 5;"` | Los datos creados en la UI aparecen en Postgres |
| 5 | **Persistencia tras recarga** | Crear un cliente/venta/prenda en la UI → `F5` | El dato sigue ahí. En mock con `atelier.ts` se resetea al hardcodeado al recargar (si no hay localStorage). |
| 6 | **Logs de backend** | `tail -f backend.log` o `docker logs` | `GET /api/clientes 200`, `POST /api/ventas 201` con SQL en modo debug |
| 7 | **Variable de entorno** | `echo $VITE_USE_MOCK` / `.env` | `VITE_USE_MOCK=false` (o no definida, default real) |

> **Criterio de aceptación V4:** las 7 verificaciones pasan en `main` con `VITE_USE_MOCK=false` y sin datos hardcodeados visibles en ninguna vista tras `hard refresh`.

---

## 10. Estado de Avance y Próximos Pasos

### Avance actual (2026-08-27)

- [x] Análisis completo de `atelier.ts` vs Postgres (17 entidades + 8 maestros relevados)
- [x] Inventario de 17 tablas activas + 78 handlers
- [x] Matriz de gaps con severidad (17 filas)
- [x] Documento fuente de verdad `ERP-V4.md` (este archivo)
- [x] Fase 1 — Clientes + Ventas — **HECHO** (2026-08-24, rama `feat/v4-fase1-clientes-ventas`, migraciones `0009_extend_clientes_crm` + `0010_ventas_canal_pago`, archive [`openspec/changes/archive/2026-08-24-v4-fase1-clientes-ventas`](openspec/changes/archive/2026-08-24-v4-fase1-clientes-ventas), `CambiosV3.md` V3.3.0)
- [x] Fase 2 — Socios + Liquidaciones + Anticipos — **HECHO** (2026-08-25, rama `feat/v4-fase2-socios-liquidaciones-anticipos`, migraciones `0011_extend_socios_configuracion` + `0012_create_liquidaciones` + `0013_create_anticipos`, archive [`openspec/changes/archive/2026-08-26-v4-fase2-socios-liquidaciones-anticipos`](openspec/changes/archive/2026-08-26-v4-fase2-socios-liquidaciones-anticipos), `CambiosV3.md` V3.4.0)
- [x] Fase 3 — Maestros (8 catálogos + singleton) — **HECHO** (2026-08-26, rama `feat/v4-fase3-maestros`, migraciones `0014_maestros_core` + `0015_maestros_tallas`, archive [`openspec/changes/archive/2026-08-26-v4-fase3-maestros`](openspec/changes/archive/2026-08-26-v4-fase3-maestros), `CambiosV3.md` V3.5.0)
- [x] Fase 4 — Insumos / Recetas / Prendas / Pedidos — **HECHO** (2026-08-27, migraciones `0016_insumos_bom` + `0017_pedidos_produccion` + `0018_prendas_listas`, `CambiosV3.md` V3.6.0)
- [x] Fase 5 — Switch global + badge + deprecación mock — **HECHO** (2026-08-27, `GET /api/v1/__mode` + `src/services/api/__mode.ts` + wiring `InventarioView`, `PrendasListasView`, `ProduccionView`, `CambiosV3.md` V3.7.0)

### §10.1 Checklist operativo V4 (viva)

> Regla: cada entrega marca su fila aquí y en §11 en el mismo PR/commit. Esta tabla es la fuente de verdad del estado vivo.

| Item | Estado | Dueño | Evidencia |
|---|---|---|---|
| Fase 1 — Clientes extendido + Ventas canal/método pago | ✅ Hecho — 2026-08-24 | — | Migraciones `0009`–`0010`, archive `2026-08-24-v4-fase1-clientes-ventas`, `CambiosV3.md` V3.3.0, verify 18/18 PASS |
| Fase 2 — Socios ampliado + Liquidaciones/Anticipos | ✅ Hecho — 2026-08-25 | — | Migraciones `0011`–`0013`, archive `2026-08-26-v4-fase2-socios-liquidaciones-anticipos`, `CambiosV3.md` V3.4.0, verify 27/27 PASS |
| Fase 3 — Maestros 8 catálogos + singleton + ventas extend | ✅ Hecho — 2026-08-26 | — | Migraciones `0014`–`0015`, archive `2026-08-26-v4-fase3-maestros`, `CambiosV3.md` V3.5.0, verify 16/16 PASS (40/40 scenarios) |
| Bug `/ventas` — backend no serializa `cliente_nombre` ni campos descriptivos del detalle (`nombre_prenda`, `talla`, `color`) | ✅ Hecho — 2026-08-27 | — | Fix `Venta`/`DetalleVenta` `@property` (`cliente_nombre`, `codigo`, `nombre_prenda`, `talla`, `subtotal`...) + `VentaRead`/`DetalleVentaRead` enriquecidos + `src/services/api/ventas.ts` + `VentasView` fallback `nombre_variante`; `py_compile` + `npm run build` 378 módulos OK |
| Fase 4 — Insumos / Recetas / Prendas / Pedidos | ✅ Hecho — 2026-08-27 | — | Migraciones `0016`–`0018`, endpoints `/prendas-confeccionadas` + `/pedidos-produccion` + `/insumos` extend + `/productos/{id}/bom/insumos`, composables `useInsumos`/`usePrendas`/`useProduccion`, `pytest` 5/5 + `vitest` 70/70 PASS |
| Fase 5 — Switch frontend a API real y deprecación `atelier.ts` | ✅ Hecho — 2026-08-27 | — | `ApiModeBadge` + `useMode` + `GET /api/__mode` OK; wiring `InventarioView`, `PrendasListasView`, `ProduccionView`; 67/67 pytest + 70/70 Vitest PASS |

### Próximos pasos inmediatos

1. ~~**Fase 5 — Switch global**~~ — ✅ Hecho 2026-08-27. Toda la aplicación ERP Atelier Arpía opera contra Postgres manteniéndose la UI intacta.

---

## 11. Registro de Avance

> Esta sección se actualiza a medida que se completan fases. Cada entrada debe referenciar rama, migraciones y verificación. Ver también §10.1 checklist vivo.

| Fecha | Fase / Hito | Rama | Migraciones | Verificación | Responsable |
|---|---|---|---|---|---|
| 2026-08-24 | Doc V4 creado | — | — | `ERP-V4.md` en repo | — |
| 2026-08-24 | Fase 1 — Clientes extendido + Ventas canal/método pago | `feat/v4-fase1-clientes-ventas` | `0009_extend_clientes_crm`, `0010_ventas_canal_pago` | 18/18 PASS (spec delta sync → `openspec/specs/`), `pytest` + `vitest` + `alembic upgrade head` reversible | — |
| 2026-08-25 | Fase 2 — Socios ampliado + Liquidaciones/Anticipos | `feat/v4-fase2-socios-liquidaciones-anticipos` | `0011_extend_socios_configuracion`, `0012_create_liquidaciones`, `0013_create_anticipos` | 27/27 PASS (3 specs sync), `pytest backend/tests/test_finanzas_*.py` 53 + `test_finanzas` 48 = 103 GREEN | — |
| 2026-08-26 | Fase 3 — Maestros 8 catálogos + singleton + ventas extend | `feat/v4-fase3-maestros` | `0014_maestros_core`, `0015_maestros_tallas` | 16/16 PASS (40/40 scenarios, 6 specs sync), `pytest` 62 + `vitest` 58 + `alembic HEAD 0015` reversible | — |
| 2026-08-27 | Bug `/ventas` — `cliente_nombre` + detalle descriptivo no serializado | — | — | ✅ Fix `Venta`/`DetalleVenta` props + `VentaRead` enriquecido, `src/services/api/ventas.ts` + `VentasView` fallback; `py_compile` + `npm run build` OK | — |
| 2026-08-27 | Fase 4 — Insumos / Recetas / Prendas / Pedidos | `main` | `0016_insumos_bom`, `0017_pedidos_produccion`, `0018_prendas_listas` | 5/5 pytest PASS, 70/70 Vitest PASS, build 378 módulos OK | — |
| 2026-08-27 | Fase 5 — Switch global + probe `/api/__mode` + wiring final | `main` | — | 67/67 pytest PASS, 70/70 Vitest PASS, build 378 módulos OK, V4 100% completado | — |

---

## Anexo — Inventario de Referencia

### Tablas activas (17 + transversales)
`Usuarios`, `Categorias_Insumos`, `Insumos`, `Compras_Insumos`, `Clientes`, `Tipos_Producto`, `Productos`, `Variantes_Producto`, `BOM_Insumos`, `BOM_Productos`, `Ventas`, `Detalle_Ventas`, `Devoluciones`, `Items_Devolucion`, `Socios_Configuracion`, `Movimientos_Financieros`, `Migracion_Omisiones`, `AuditLog`, `RefreshToken` — `Proveedores` eliminada en `0008`.

### Endpoints reales (~78 handlers)
`auth`, `insumos`, `categorias-insumos`, `clientes`, `productos`, `variantes`, `BOM`, `costo`, `ventas`, `devoluciones`, `finanzas/movimientos`, `finanzas/socios`, `finanzas/liquidaciones` (simulado), `analiticos` (7), `omisiones`, `usuarios`, `audit`.

### Vistas frontend (todas en mock hoy)
`ClientesView`, `VentasView`, `FinanzasView`, `MaestrosView`, `InsumosView`, `ProductosView`, `PrendasListasView`, `ProduccionView`, `DashboardView` (+ otras que consumen `atelier.ts`).

---

*Fin del documento V4. Mantener actualizado en cada fase. Registrar todo cambio V3+ también en `CambiosV3.md` según regla del proyecto.*

> **Regla V4:** cada entrega marca su fila en §10.1 y §11 en el mismo PR/commit.
