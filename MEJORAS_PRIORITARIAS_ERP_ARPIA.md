# Mejoras prioritarias para ERP Arpia

> **Progreso — 20-08-2026:** Sprint 1 (Seguridad + Auditoría foundation) ✅ completado. Ver detalle por sección abajo. `Leyenda: ✅ hecho | ⏳ pendiente | 🔄 parcial`

## Resumen ejecutivo

El proyecto tiene una base sólida: arquitectura clara, dominio bien definido, stack moderno y documentación muy buena en el README. Sin embargo, el siguiente salto de calidad no es más funcionalidad, sino robustez operativa, seguridad, trazabilidad y madurez para producción.

La mayor parte de las mejoras recomendadas se enfocan en tres áreas:

- seguridad y control de acceso
- integridad financiera e inventario
- observabilidad y operación en producción

## 1. Seguridad y hardening — ✅ Sprint 1 completado

### Qué mejorar

- ✅ Usar refresh tokens con rotación y expiración controlada. — SHA-256, reuse detection revoca todos los tokens del usuario, 7 días expiración, 15 min access token
- ✅ Añadir limitación de tasa (rate limiting) por usuario, IP y endpoint. — slowapi + políticas por entorno (auth 10/min, write 100/min/user, read 300/min/user)
- 🔄 Mejorar la gestión de secretos con entorno real de producción. — validación en config.py + sin defaults en docker-compose.yml; pendiente: Vault/AWS Secrets Manager externo
- ✅ Separar variables por entorno: desarrollo, pruebas y producción. — ENVIRONMENT dev/test/staging/production con validaciones
- ✅ Revisar headers de seguridad y políticas CORS. — SecurityHeadersMiddleware (CSP, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, X-Frame-Options) + CORS estricto por entorno
- ✅ Proteger endpoints sensibles con auditoría y trazabilidad. — AuditLog + audit helpers en ventas/devoluciones/compras/finanzas + request_id correlation
- ✅ Añadir validación estricta de entrada y evitación de abuso de payloads. — Idempotency-Key middleware en POST críticos + validación pydantic + rate limiting

### Objetivo

Reducir exposición de datos, evitar abuso del sistema y que la API sea segura para operar en entorno real con varios usuarios.

### Acciones concretas

- ⏳ Usar un gestor de secretos (Vault, AWS Secrets Manager, Azure Key Vault, etc.). — pendiente integración externa (actual: validación + sin secretos en repo)
- ✅ No dejar secretos por defecto en Docker Compose ni en archivos versionados. — `docker-compose.yml` usa `${VAR}` sin defaults sensibles; validado por tests
- ✅ Definir políticas de contraseña más fuertes. — 12+ chars, mayúscula/minúscula/dígito/especial, sin secuencias, TOTP MFA opcional
- ✅ Añadir logs de eventos de autenticación: login, logout, intentos fallidos, cambios de permisos. — audit logs + LoginAttemptTracker con logging estructurado
- ✅ Añadir bloqueo temporal para usuarios con varios intentos fallidos. — 5 intentos → 15 min lockout, reset en login exitoso

**Extras Sprint 1:**
- ✅ Estados de documento con transiciones válidas: `draft → confirmed → cancelled → reversed` + motivo/usuario en reversa (Venta/Devolucion/MovimientoFinanciero) + endpoints `PATCH .../state`
- ✅ Idempotency-Key header en POST críticos (ventas, devoluciones, compras, finanzas, ajustes stock) — middleware con cache Redis (fallback memoria) + 10 tests

---

## 2. Testing más serio y más realista — ⏳ Sprint 2 (siguiente)

### Qué mejorar

- ⏳ Añadir pruebas de integración con PostgreSQL real.
- ⏳ Cubrir transacciones complejas y condiciones de carrera.
- ⏳ Mejorar test coverage en módulos críticos: inventario, ventas, WAC, devoluciones, finanzas.
- ⏳ Probar casos de borde y errores de negocio, no solo flujos felices.

### Casos críticos a cubrir

- ⏳ stock negativo después de una venta
- ⏳ compras concurrentes sobre el mismo insumo
- ⏳ devoluciones parciales
- ⏳ venta con descuento y costo aplicado
- ⏳ producto compuesto con BOM recursivo
- ⏳ ventas donde el costo cambia entre fecha y cálculo final
- ⏳ reversiones de transacción con rollback correcto
- ⏳ rollover de inventario por ventas anuladas o devoluciones

### Objetivo

Garantizar que la lógica de negocio sea correcta y no se rompa al escalar el volumen de operaciones.

### Recomendación

Hacer una suite de pruebas para cada motor central del ERP:

- WAC (Weighted Average Cost)
- explosión del inventario por BOM
- cálculo de margen
- devoluciones
- distribución de ganancias por socios
- movimientos financieros

---

## 3. Observabilidad y trazabilidad — ⏳ Sprint 3

### Qué mejorar

- ✅ Logs estructurados con request_id, user_id, entidad y operación. — RequestContextMiddleware + JSON logs ya existen
- 🔄 Trazabilidad de cada venta, compra y ajuste de inventario. — AuditLog cubre ventas/devoluciones/compras/finanzas/stock; pendiente: compra insumo/BOM con triggers DB
- ⏳ Métricas por endpoint, duración y errores.
- ⏳ Alertas para stock crítico, pérdidas, amortización de inventario y margen anormal.
- 🔄 Health checks más completos: base de datos, worker jobs, dependencias externas. — `/health/live` + `/health/ready` (DB); pendiente: Redis, worker queue, APIs externas

### Objetivo

Que cada operación del sistema pueda explicarse en producción y que el equipo pueda diagnosticar fallos rápidamente.

### Indicadores clave

- tiempo promedio de respuesta por endpoint
- tasa de errores por módulo
- ventas por día y por canal
- margen bruto por producto
- stock crítico por insumo
- compras con precio atípico
- devoluciones y anulaciones por motivo

---

## 4. Mejoras de arquitectura interna — ⏳ Sprint 3-4

### Qué mejorar

- 🔄 Separar responsabilidades más claramente:
  - ✅ API
  - 🔄 domain — pendiente capa explícita `app/domain/` con entities/value objects/events
  - ✅ services
  - 🔄 repositories — pendiente patrón Repository formalizado
  - ✅ schemas
  - ✅ validators
- ✅ Centralizar la lógica de negocio en servicios y no en endpoints. — ya aplicado (inventory, wac, devoluciones, finanzas, etc.)
- 🔄 Usar un patrón más claro de transacciones y unit of work. — pendiente UnitOfWork context manager
- ⏳ Reducción de duplicación de lógica entre ventas, devoluciones y reportes.
- 🔄 Definir DTOs contractuales para respuestas y requests. — pendiente versionado `schemas/v1`, `schemas/v2`

### Objetivo

Hacer el sistema más mantenible y menos frágil a medida que aumenta la cantidad de módulos y reglas.

### Recomendación

Crear módulos con ownership claro:

- usuarios y seguridad
- inventario
- compras
- producción/BOM
- ventas
- devoluciones
- finanzas
- analítica

Cada módulo debe tener su servicio responsable y su conjunto de validaciones.

---

## 5. Rendimiento y escalabilidad — ⏳ Sprint 3

### Qué mejorar

- ✅ Añadir índices críticos en tablas grandes y consultas frecuentes. — migración 0007 + índices de AuditLog
- ⏳ Revisar reportes analíticos con agregaciones pesadas.
- ✅ Aplicar paginación y filtros consistentes en todos los listados. — server-side pagination + filtros en todos los listados
- ⏳ Cachear resultados que se consultan frecuentemente. — pendiente Redis cache layer
- ⏳ Separar tareas pesadas de la API HTTP. — pendiente Celery + Redis
- ⏳ Optimizar queries de dashboards y reportes de finanzas.

### Objetivo

Mantener tiempos de respuesta estables incluso cuando crezca el volumen de ventas, inventario y datos históricos.

### Casos clave

- reportes de ventas mensuales
- margen por producto
- stock crítico
- movimientos financieros
- trazabilidad de producción por BOM

---

## 6. Mejoras de UX en frontend — ⏳ Sprint 4

### Qué mejorar

- ⏳ Diseñar un sistema visual consistente con un design system.
- ⏳ Uniformar validaciones de errores y feedback de acción.
- ⏳ Mejorar la gestión de caché y estado global.
- ⏳ Manejar mejor todos los estados de carga, vacío y error.
- ⏳ Añadir paginación, búsqueda y filtros a tablas grandes.
- ⏳ Añadir pruebas E2E para flujos críticos.

### Flujos más importantes a cubrir

- login y permisos
- carga de inventario
- creación de ventas
- devoluciones
- cálculo de margen
- dashboards y reportes
- gestión de finanzas

### Objetivo

Que el sistema no solo funcione, sino que sea claro y fiable para usuarios operativos.

---

## 7. Auditoría y control fiscal — ✅ Sprint 1 (parcial) → continúa Sprint 2-3

### Qué mejorar

- ✅ Historial completo de cambios por entidad. — tabla `AuditLog` + índices + AuditService + API `/auditoria`
- ✅ Registro de quién hizo cada cambio, cuándo y desde qué usuario. — `usuario_id`, `usuario_rol`, `request_id`, `ip`, `user_agent`, `timestamp`
- ⏳ Añadir versión de precios y costos por fecha. — pendiente tablas `precio_versions` / `costo_versions`
- ⏳ Tener un esquema de cierres mensuales o de operación. — pendiente tabla `cierres_mensuales`
- ✅ Registrar anulaciones, ajustes y correcciones con motivo. — `reversed_motivo`/`reversed_by`/`reversed_at` + transiciones `cancelled → reversed` requieren motivo

### Objetivo

Que el negocio pueda auditar decisiones, operaciones y cambios en costos y stock sin ambigüedad.

### Recomendación

Introducir tablas de auditoría o eventos de negocio para:

- ✅ ventas creadas
- ✅ ventas anuladas (transición `cancelled`/`reversed`)
- ✅ devoluciones
- ⏳ cambios de precio
- ✅ ajustes de stock
- ⏳ cambios de BOM
- ✅ movimientos financieros

---

## 8. CI/CD, despliegue y operación — ⏳ Sprint 3

### Qué mejorar

- ✅ Pipeline CI con lint, tests y build. — ruff + pytest (real PG) + frontend lint/test/build ya en CI
- ⏳ Deploy automático por entorno.
- ⏳ Revisión de migraciones antes del despliegue.
- ⏳ Backups automáticos de PostgreSQL.
- ⏳ Rollback plan para releases.
- ⏳ Monitoreo de salud del sistema y alertas.
- ⏳ Documentación de procedimientos de incidentes.

### Objetivo

Reducir riesgo operativo y que cada release sea más segura y más fácil de controlar.

---

## Prioridades recomendadas

### Prioridad alta

1. ✅ Seguridad y hardening de la API — **hecho Sprint 1**
2. ⏳ Tests de negocio críticos — **siguiente (Sprint 2)**
3. 🔄 Auditoría y trazabilidad — **base hecha Sprint 1, falta versionado precios/cierres (Sprint 2-3)**
4. ⏳ Observabilidad en producción — **Sprint 3**
5. ⏳ Backups y despliegue seguro — **Sprint 3**

### Prioridad media

6. ⏳ Mejoras de arquitectura interna — **Sprint 3-4**
7. ⏳ Optimización de queries y reportes — **Sprint 3**
8. ⏳ Revisión de UX en frontend — **Sprint 4**

### Prioridad baja, pero valiosa

9. ⏳ refactors de limpieza y normalización del código
10. ⏳ preparación para crecimiento de volumen y operación multisalida

---

## Conclusión

El proyecto ya tiene una base muy buena y una visión sólida de negocio. El siguiente nivel no consiste en “hacer más módulos”, sino en hacer que el sistema sea más seguro, más verificable, más auditable y más confiable en producción.

La parte más importante es que el ERP no solo funcione bien en un entorno controlado, sino que soporte cambios reales del negocio sin romper inventario, costos, finanzas o trazabilidad.

En otras palabras: la próxima etapa ideal es pasar de un ERP funcional a un ERP de operación profesional.

---

## Siguiente paso recomendado

Crear un roadmap de 90 días con estas mejoras priorizadas en entregas concretas:

- ✅ Sprint 1: seguridad + auditoría — **completado 20-08-2026** (TASK-001 a TASK-012: hardening, estados de documento, idempotencia)
- ⏳ Sprint 2: tests + validación de negocio — **siguiente recomendado**
- ⏳ Sprint 3: observabilidad + performance + despliegue
- ⏳ Sprint 4: refinamiento de frontend y UX

Esto permite implementar mejoras sin bloquear la operación diaria del negocio.
