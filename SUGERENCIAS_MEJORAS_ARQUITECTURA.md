# Informe de Análisis Arquitectónico y Propuestas de Mejora — ERP/MRP ARPIA

**Fecha:** 2026-08-13  
**Proyecto:** ERP/MRP ARPIA (FastAPI + SQLAlchemy + PostgreSQL + Vue 3 + Vite + TypeScript + Pinia)  
**Objetivo:** Diagnóstico técnico, evaluación de arquitectura y hoja de ruta con mejoras priorizadas (Seguridad, Rendimiento, Base de Datos, Frontend, Backend y DevOps).

---

## 1. Diagnóstico General del Proyecto

### 1.1 Fortalezas Destacadas
1. **Precisión Financiera e Inventario:** Uso estricto de `NUMERIC(15,4)` y tipos `Decimal` en todo el flujo de costos, WAC y ventas, evitando problemas de redondeo binario de punto flotante.
2. **Concurrencia y Consistencia:** Implementación de bloqueos pesimistas (`SELECT ... FOR UPDATE` ordenado por ID) y `populate_existing=True` en deducción y reposición de inventario (`backend/app/services/inventory.py`), mitigando eficazmente *race conditions* y *deadlocks*.
3. **Manejo de Autenticación y Refresh Tokens:** Rotación de refresh tokens con detección de reuso (revocación en cadena ante posible compromiso de credenciales).
4. **Separación de Responsabilidades:** Monolito modular bien delimitado con esquemas Pydantic v2, servicios de dominio y modelos SQLAlchemy 2.0.
5. **Suite de Pruebas Extensa:** Más de 490 tests unitarios y de integración para migraciones, BOM, WAC, costos, devoluciones y ventas.

---

## 2. Hallazgos y Sugerencias de Mejora

---

### 2.1 Base de Datos & Rendimiento (Backend)

#### 🔴 Prioridad Alta: Índices en Llaves Foráneas y Filtros Frecuentes
> **Estado:** ✅ HECHO — `index=True` en modelos + migración `0007_add_indexes_fk_and_filters.py` (incluye también Devoluciones, Variantes_Producto y BOM_Productos)
- **Problema:** En PostgreSQL, las restricciones de llave foránea (`ForeignKey`) **no crean índices automáticamente** en la columna hija. Tablas de alto crecimiento como `Detalle_Ventas`, `Ventas`, `Compras_Insumos`, `Items_Devolucion` y `BOM_Insumos` realizarán *Sequential Scans* al hacer `JOIN` o filtrar por fecha/estado/canal.
- **Acción Recomendada:**
  - Agregar `index=True` en modelos SQLAlchemy y generar una migración de Alembic:
    - `Ventas.cliente_id`, `Ventas.fecha`, `Ventas.canal_venta`, `Ventas.estado`
    - `Detalle_Ventas.venta_id`, `Detalle_Ventas.producto_id`, `Detalle_Ventas.variante_id`
    - `Compras_Insumos.insumo_id`, `Compras_Insumos.proveedor_id`, `Compras_Insumos.fecha_compra`
    - `BOM_Insumos.insumo_id`, `BOM_Insumos.producto_id`
    - `Insumos.categoria_id`
    - `Items_Devolucion.devolucion_id`, `Items_Devolucion.producto_id`

```python
# Ejemplo en app/models/ventas.py
class Venta(Base):
    # ...
    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    cliente_id: Mapped[int | None] = mapped_column(
        ForeignKey("Clientes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    canal_venta: Mapped[str] = mapped_column(
        String(16), nullable=False, server_default="feria", default="feria", index=True
    )
```

---

#### 🟡 Prioridad Media: Configuración Explícita del Pool de Conexiones
> **Estado:** ✅ HECHO — `pool_size=10, max_overflow=20, pool_recycle=1800, pool_timeout=30, pool_pre_ping=True` en `app/db/session.py`
- **Problema:** En `app/db/session.py`, `create_engine` utiliza valores por defecto del pool de SQLAlchemy sin controlar `pool_size`, `max_overflow`, `pool_recycle` ni `pool_timeout`.
- **Acción Recomendada:**
  Configurar el pool según la carga esperada y el hosting (especialmente en cPanel/Passenger donde cada worker puede abrir conexiones):

```python
# app/db/session.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,  # Reciclar conexiones cada 30 min para evitar timeouts del servidor
    pool_timeout=30,
)
```

---

#### 🟡 Prioridad Media: Tarea de Limpieza (Pruning) de Refresh Tokens
> **Estado:** ✅ HECHO — script `backend/scripts/prune_tokens.py` (`--days N`, `--dry-run`) con instrucciones de cron
- **Problema:** La tabla `RefreshTokens` almacena tokens expirados y revocados indefinidamente, creciendo con cada inicio de sesión y renovación.
- **Acción Recomendada:**
  - Agregar un script o tarea programada (cron job/FastAPI background task) para purgar tokens revocados o expirados con más de $N$ días:
    ```sql
    DELETE FROM "RefreshTokens" WHERE expira_en < NOW() - INTERVAL '30 days';
    ```

---

### 2.2 Seguridad & Robustez

#### 🔴 Prioridad Alta: Validación Obligatoria de `JWT_SECRET_KEY` en Producción
> **Estado:** ✅ HECHO — `@model_validator` en `app/core/config.py` bloquea la clave por defecto en production/staging + `test_config.py`
- **Problema:** `config.py` tiene `"dev_secret_change_me"` como valor por defecto. Si en un despliegue se omite la variable de entorno, el sistema iniciará vulnerable.
- **Acción Recomendada:**
  Agregar un validador en Pydantic `Settings` que impida iniciar en entornos de staging/production si la clave es la por defecto:

```python
# app/core/config.py
from pydantic import model_validator

class Settings(BaseSettings):
    # ...
    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT in ("production", "staging") and self.JWT_SECRET_KEY == "dev_secret_change_me":
            raise ValueError("JWT_SECRET_KEY must be configured with a secure secret in production!")
        return self
```

---

#### 🟡 Prioridad Media: Rate Limiting en Endpoints Críticos de Autenticación
> **Estado:** ✅ HECHO — `slowapi` en `/auth/login` (10/min) y `/auth/refresh` (20/min) + handler de `RateLimitExceeded` en `main.py`
- **Problema:** `/auth/login` y `/auth/refresh` no tienen limitador de tasa de peticiones (*rate limiter*), permitiendo ataques de fuerza bruta o saturación.
- **Acción Recomendada:**
  Integrar `slowapi` (basado en `limits`) para limitar intentos por IP en rutas de autenticación:

```python
# Ejemplo de protección en /auth/login
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    ...
```

---

#### 🟢 Prioridad Baja: Manejador Global de Excepciones Sanitizado
> **Estado:** ✅ HECHO — handler de `Exception` en `app/main.py`; en production/staging devuelve respuesta sanitizada sin trazas
- **Problema:** Excepciones no controladas pueden revelar trazas internas o detalles de base de datos en respuestas 500 al cliente.
- **Acción Recomendada:**
  Registrar un manejador global de `Exception` en `app/main.py` que registre el error en logs y devuelva una respuesta estandarizada:
  ```json
  {
    "detail": "Error interno del servidor. Contacte al administrador.",
    "code": "INTERNAL_SERVER_ERROR"
  }
  ```

---

### 2.3 Frontend & Experiencia de Usuario (Vue 3 + Vite)

#### 🔴 Prioridad Alta: Lazy Loading (Code Splitting) en Rutas
> **Estado:** ✅ HECHO — `() => import(...)` en `frontend/src/router/index.ts` (import estático solo en modo test para no romper jsdom)
- **Problema:** En `frontend/src/router/index.ts`, todas las vistas (`DashboardView`, `ProductosView`, `FinanzasView`, `InventarioView`, etc.) se importan estáticamente (`import ... from '@/views/...'`). Esto obliga al navegador a descargar todo el bundle del ERP en la carga inicial.
- **Acción Recomendada:**
  Cambiar a imports dinámicos por función:

```typescript
// frontend/src/router/index.ts
const routes: RouteRecordRaw[] = [
  { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { public: true } },
  {
    path: '/',
    component: AppLayout,
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'dashboard', component: () => import('@/views/DashboardView.vue'), meta: { roles: ALL_ROLES } },
      { path: 'analisis', name: 'analisis', component: () => import('@/views/AnalisisView.vue'), meta: { roles: ALL_ROLES } },
      { path: 'ventas', name: 'ventas', component: () => import('@/views/VentasView.vue'), meta: { roles: ALL_ROLES } },
      { path: 'devoluciones', name: 'devoluciones', component: () => import('@/views/DevolucionesView.vue'), meta: { roles: ALL_ROLES } },
      { path: 'finanzas', name: 'finanzas', component: () => import('@/views/FinanzasView.vue'), meta: { roles: ALL_ROLES } },
      { path: 'inventario', name: 'inventario', component: () => import('@/views/InventarioView.vue'), meta: { roles: ALL_ROLES } },
      { path: 'productos', name: 'productos', component: () => import('@/views/ProductosView.vue'), meta: { roles: ALL_ROLES } },
      { path: 'maestros', name: 'maestros', component: () => import('@/views/MaestrosView.vue'), meta: { roles: ALL_ROLES } },
      { path: 'omisiones', name: 'omisiones', component: () => import('@/views/OmisionesView.vue'), meta: { roles: ALL_ROLES } },
      { path: 'usuarios', name: 'usuarios', component: () => import('@/views/UsuariosView.vue'), meta: { roles: ['admin'] } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]
```

---

#### 🟡 Prioridad Media: Desacoplamiento de Componentes Grandes
> **Estado:** ⚠️ PARCIAL — `ProductosView.vue` extraído (−507 líneas) a composables `useProductosCatalog/Bom/Costo` + `utils/api.ts`; `FinanzasView` e `InventarioView` pendientes
- **Problema:** Vistas como `ProductosView.vue` (30 KB), `FinanzasView.vue` (18 KB) e `InventarioView.vue` (16 KB) concentran modales, tablas, formularios y lógica de estado en un solo archivo.
- **Acción Recomendada:**
  Extraer subcomponentes atómicos/presentacionales bajo carpetas dedicadas (ej. `src/components/productos/ProductModal.vue`, `src/components/productos/BomEditor.vue`, `src/components/finanzas/KpiSummary.vue`), facilitando tests unitarios de interfaz y mantenimiento.

---

### 2.4 Arquitectura de Código & Servicios (Backend)

#### 🟡 Prioridad Media: Desacoplar Excepciones HTTP de la Capa de Servicios
> **Estado:** ✅ HECHO — `app/core/exceptions.py` (`InsufficientStockError`, `BomCycleDetectedError`, `EntityNotFoundError`, `DomainValidationError`) + refactor de `inventory.py`/`costos.py` + handler en `main.py` + `test_domain_exceptions.py`
- **Problema:** En `app/services/inventory.py` y `app/services/costos.py`, se lanza `HTTPException(status_code=409, detail=...)` directamente dentro de funciones de dominio.
- **Impacto:** Si estos servicios son invocados desde CLI de migración (`backend/migrate/`), scripts de background o workers, se acoplan innecesariamente a conceptos web de FastAPI.
- **Acción Recomendada:**
  Definir excepciones de dominio propias (ej. `InsufficientStockError`, `BomCycleDetectedError`, `EntityNotFoundError`) y mapearlas en los routers o mediante un exception handler centralizado.

```python
# app/core/exceptions.py
class DomainError(Exception):
    """Base domain exception."""

class InsufficientStockError(DomainError):
    def __init__(self, insumo_nombre: str):
        self.insumo_nombre = insumo_nombre
        super().__init__(f"Stock insuficiente para insumo '{insumo_nombre}'")

class BomCycleDetectedError(DomainError):
    def __init__(self, path: list[int]):
        self.path = path
        super().__init__(f"Cycle detected in BOM explosion: {' -> '.join(map(str, path))}")
```

---

### 2.5 DevOps, CI/CD y Observabilidad

#### 🟡 Prioridad Media: Pipeline de CI/CD (GitHub Actions)
> **Estado:** ✅ HECHO — `.github/workflows/ci.yml` con jobs backend (ruff check/format + pytest con Postgres 16 container) y frontend (lint + test + build)
- **Problema:** No se observa configuración de `.github/workflows` para automatizar validaciones antes de mergear PRs.
- **Acción Recomendada:**
  Crear workflow para ejecutar automáticamente:
  1. **Backend:** `ruff check`, `ruff format --check`, `pytest` con base de datos de pruebas en contenedor postgres.
  2. **Frontend:** `npm run lint`, `npm run build`, `npm run test`.

---

#### 🟢 Prioridad Baja: Logging Estructurado (JSON Logging)
> **Estado:** ✅ HECHO — middleware `RequestContextMiddleware` (`X-Request-ID` en logs y respuesta) + `JsonFormatter` (JSON en prod/staging, texto en dev), sin dependencias externas
- **Problema:** El sistema depende del logging por defecto de Uvicorn/FastAPI.
- **Acción Recomendada:**
  Configurar logs estructurados con identificador de petición (`X-Request-ID`) para trazabilidad de ventas, devoluciones y compras en producción.

---

## 3. Matriz de Priorización e Impacto

| # | Propuesta | Área | Impacto | Esfuerzo | Prioridad |
|---|---|---|---|---|---|
| 1 | Índices en Foreign Keys y columnas de filtrado | Base de Datos | 🚀 Alto | 🟢 Bajo (Alembic) | **Inmediata** |
| 2 | Lazy loading en rutas de Vue Router | Frontend | 🚀 Alto | 🟢 Bajo | **Inmediata** |
| 3 | Validación estricta de `JWT_SECRET_KEY` en producción | Seguridad | 🔒 Alto | 🟢 Bajo | **Inmediata** |
| 4 | Rate limiting en `/auth/login` y `/auth/refresh` | Seguridad | 🔒 Alto | 🟡 Medio | **Alta** |
| 5 | Configuración explícita del pool de SQLAlchemy | Rendimiento | ⚡ Medio | 🟢 Bajo | **Alta** |
| 6 | Modularización de vistas monolíticas (`ProductosView`, `FinanzasView`) | Frontend | 🛠️ Medio | 🟡 Medio | **Media** |
| 7 | Separación de excepciones de dominio de `HTTPException` | Arquitectura | 🛠️ Medio | 🟡 Medio | **Media** |
| 8 | Automatización de CI con GitHub Actions | DevOps | 🔄 Alto | 🟡 Medio | **Media** |
| 9 | Limpieza periódica de `RefreshTokens` antiguos | Base de Datos | 🧹 Bajo | 🟢 Bajo | **Baja** |

---

## 4. Roadmap de Implementación Paso a Paso

Un plan estructurado en 4 fases secuenciales para llevar el proyecto a un nivel de excelencia en producción, minimizando riesgos y asegurando la estabilidad operativa:

```mermaid
graph LR
    F1[Fase 1: Quick Wins & Hardening] --> F2[Fase 2: Seguridad & Dominio]
    F2 --> F3[Fase 3: Refactor UI & Frontend]
    F3 --> F4[Fase 4: CI/CD & Observabilidad]
```

---

### 🔹 Fase 1: Quick Wins & Rendimiento Inmediato (Esfuerzo: 1 - 2 días)
> **Estado:** ✅ COMPLETA — índices, code-splitting, validación de secretos y pool configurados
> **Objetivo:** Resolver cuellos de botella de base de datos y optimizar la carga inicial sin alterar la lógica de negocio.

1. **Migración de Índices en Base de Datos:**
   - Modificar modelos SQLAlchemy en `app/models/` (`Venta`, `DetalleVenta`, `Insumo`, `CompraInsumo`, `BomInsumo`, `DevolucionItem`).
   - Generar y ejecutar migración con Alembic:
     ```bash
     alembic revision --autogenerate -m "add_indexes_fk_and_filter_columns"
     alembic upgrade head
     ```
2. **Code-Splitting en Frontend:**
   - Convertir los imports de `frontend/src/router/index.ts` a `() => import(...)`.
   - Validar que el build de Vite genere chunks independientes por vista (`npm run build`).
3. **Validación de Secretos en Configuración:**
   - Agregar el `@model_validator` en `backend/app/core/config.py` para bloquear `JWT_SECRET_KEY` por defecto en entornos productivos.
4. **Optimización del Pool de Conexiones:**
   - Configurar `pool_size`, `max_overflow` y `pool_recycle` en `backend/app/db/session.py`.

---

### 🔹 Fase 2: Seguridad, Robustez y Dominio (Esfuerzo: 2 - 3 días)
> **Estado:** ✅ COMPLETA — rate limiting, jerarquía de excepciones de dominio y manejador global de errores
> **Objetivo:** Blindar endpoints contra abusos y desacoplar la lógica de negocio del framework web.

1. **Rate Limiting en Autenticación:**
   - Instalar y configurar `slowapi` en `backend/app/api/routes/auth.py` para `/auth/login` y `/auth/refresh`.
2. **Creación de Jerarquía de Excepciones de Dominio:**
   - Crear `backend/app/core/exceptions.py` con excepciones tipadas (`InsufficientStockError`, `BomCycleDetectedError`, etc.).
   - Refactorizar `app/services/inventory.py` y `app/services/costos.py` para levantar estas excepciones en lugar de `HTTPException`.
   - Registrar exception handlers en `app/main.py` para mapear automáticamente errores de dominio a códigos HTTP (409, 404, 400).
3. **Manejador Global de Errores Sanitizado:**
   - Implementar middleware o handler global para capturar errores 500 no controlados sin exponer trazas de base de datos al cliente.

---

### 🔹 Fase 3: Arquitectura Frontend y Modularización (Esfuerzo: 3 - 4 días)
> **Estado:** ⚠️ PARCIAL — `ProductosView` descompuesto (vía composables); faltan `FinanzasView`, `InventarioView` y el tipado estricto de stores
> **Objetivo:** Mejorar la mantenibilidad del código UI y facilitar testing de componentes.

1. **Descomposición de Vistas Monolíticas:**
   - Extraer subcomponentes de `ProductosView.vue`:
     - `components/productos/ProductTable.vue`
     - `components/productos/ProductFormDialog.vue`
     - `components/productos/BomRecipeEditor.vue`
     - `components/productos/VariantManager.vue`
   - Extraer subcomponentes de `FinanzasView.vue` e `InventarioView.vue`.
2. **Tipado Estricto y Validación de Esquemas:**
   - Ejecutar `npm run gen:api` para sincronizar los tipos de OpenAPI con el backend.
   - Reemplazar tipos genéricos (`any`) en stores de Pinia por tipos estrictos generados.

---

### 🔹 Fase 4: CI/CD, Mantenimiento y Observabilidad (Esfuerzo: 2 días)
> **Estado:** ✅ COMPLETA — CI (GitHub Actions), pruning de tokens (`scripts/prune_tokens.py`) y logging estructurado con `X-Request-ID`
> **Objetivo:** Asegurar la calidad continua y el ciclo de vida de los datos en producción.

1. **Pipeline de Integración Continua (GitHub Actions):**
   - Configurar `.github/workflows/ci.yml`:
     - Job Backend: Setup Python, Postgres service container, `ruff check`, `pytest`.
     - Job Frontend: Setup Node, `npm run lint`, `npm run test`, `npm run build`.
2. **Depuración Automática de Tokens (Pruning):**
   - Crear script de mantenimiento `scripts/prune_tokens.py` o tarea periódica para eliminar refresh tokens revocados/expirados con más de 30 días de antigüedad.
3. **Logging Estructurado y Trazabilidad:**
   - Incorporar middleware de correlación (`X-Request-ID`) en FastAPI para trazabilidad de peticiones de ventas e inventario.

---

## 5. Conclusión

El proyecto posee una **base técnica sólida**, con excelentes decisiones de ingeniería en el manejo de consistencia transaccional, cálculos WAC y prevención de ciclos en BOM. Siguiendo este **Roadmap de 4 fases**, el sistema alcanzará niveles óptimos de escalabilidad, seguridad bancaria en transacciones y una experiencia de desarrollo limpia y mantenible a largo plazo.

