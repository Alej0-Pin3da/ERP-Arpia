# Sugerencias de Mejoras de Arquitectura V2 — ERP/MRP ARPIA

**Fecha:** 2026-08-18  
**Alcance:** mejoras pendientes después de las implementaciones documentadas en `SUGERENCIAS_MEJORAS_ARQUITECTURA.md`.

---

## 1. Resumen ejecutivo

El proyecto tiene una base técnica sólida: FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Vue 3, Pinia, control de roles, transacciones de inventario y una suite amplia de pruebas.

Las mejoras pendientes con mayor impacto son:

1. endurecer el despliegue y eliminar secretos por defecto;
2. proteger mejor las sesiones y credenciales;
3. hacer idempotentes las operaciones críticas del ERP;
4. incorporar auditoría funcional y trazabilidad de cambios;
5. medir cobertura, seguridad y rendimiento de forma automática;
6. completar la modularización y el code splitting del frontend;
7. formalizar backups, recuperación y observabilidad productiva.

---

## 2. Mejoras ya implementadas

Estas propuestas no deberían repetirse como trabajo pendiente salvo que se quiera revisar su calidad:

- índices para llaves foráneas y filtros frecuentes;
- configuración explícita del pool de SQLAlchemy;
- validación de `JWT_SECRET_KEY` en staging/producción;
- rate limiting en login y refresh;
- excepciones de dominio separadas de `HTTPException`;
- manejador global de errores sanitizado;
- logging estructurado y `X-Request-ID`;
- code splitting parcial en rutas de Vue;
- limpieza de refresh tokens;
- pipeline CI con Ruff, pytest, ESLint, Vitest y build de frontend.

---

## 3. Prioridad P0: producción y seguridad

### 3.1 Eliminar secretos y credenciales por defecto

**Riesgo:** [docker-compose.yml](docker-compose.yml) todavía contiene valores de desarrollo como contraseña de PostgreSQL y `dev_secret_change_me`. El [seeder.py](backend/app/seeder.py) también contiene una contraseña administrativa conocida.

**Acciones:**

- eliminar defaults de secretos en entornos `staging` y `production`;
- exigir `JWT_SECRET_KEY`, `POSTGRES_PASSWORD` y credenciales del administrador por variables de entorno;
- validar longitud y entropía mínima de secretos;
- impedir que el seeder cree un administrador con una contraseña fija;
- documentar un procedimiento de rotación de secretos;
- comprobar que `.env`, backups y logs nunca se publiquen en Git.

**Criterios de aceptación:**

- el despliegue de Passenger falla antes de reiniciar la aplicación si falta un secreto;
- no existe ninguna contraseña administrativa fija en el código;
- rotar el secreto invalida las sesiones existentes de forma controlada.

### 3.2 Endurecer tokens y sesiones

Actualmente los tokens se almacenan en `localStorage`, según [frontend/src/api/storage.ts](frontend/src/api/storage.ts). Es una decisión válida para una SPA, pero aumenta el impacto de cualquier XSS.

**Acciones:**

- reducir la duración del access token de 24 horas a 15-30 minutos;
- evaluar refresh token en cookie `HttpOnly`, `Secure` y `SameSite`;
- si se mantienen cookies, añadir protección CSRF;
- revocar sesiones por usuario desde administración;
- almacenar `last_used_at`, dispositivo y fecha de creación para cada sesión;
- limitar el número de sesiones activas por usuario;
- aplicar una política de contraseña y, si el riesgo lo justifica, MFA para administradores;
- añadir alertas ante reutilización de refresh tokens.

### 3.3 CORS, headers y superficie HTTP

En [backend/app/main.py](backend/app/main.py) se permiten todos los métodos y headers mediante CORS.

**Acciones:**

- declarar únicamente métodos y headers necesarios;
- configurar una lista de orígenes estricta por entorno;
- añadir headers de seguridad: CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy` y `Permissions-Policy`;
- limitar tamaño de payload y tiempo de espera;
- desactivar o proteger `/docs` y `/redoc` en producción si no son necesarios.

---

## 4. Prioridad P0: integridad de operaciones ERP

### 4.1 Idempotencia para escrituras críticas

Un timeout, doble clic o reintento automático puede repetir una venta, devolución, compra o movimiento financiero.

**Acciones:**

- aceptar un header `Idempotency-Key` en operaciones POST críticas;
- guardar la clave, usuario, endpoint, respuesta y estado de procesamiento;
- imponer una restricción única por usuario y operación;
- devolver la misma respuesta ante reintentos seguros;
- expirar claves antiguas mediante tarea de mantenimiento;
- añadir pruebas de concurrencia y reintento.

**Operaciones candidatas:**

- crear venta;
- crear devolución;
- registrar compra de insumos;
- crear movimiento financiero;
- ajustes manuales de stock;
- ejecución de fases de migración con `--commit`.

### 4.2 Auditoría funcional

El logging técnico no sustituye una auditoría de negocio.

**Acciones:**

Crear una tabla de auditoría con:

- usuario y rol;
- entidad y `entity_id`;
- acción (`create`, `update`, `delete`, `approve`, `reverse`);
- valores anteriores y nuevos, evitando guardar contraseñas o tokens;
- fecha UTC;
- `request_id`;
- IP y user agent, cuando corresponda.

Priorizar ventas, devoluciones, inventario, costos, finanzas, usuarios y permisos.

**Criterios de aceptación:**

- cada cambio sensible genera un registro en la misma transacción;
- la auditoría es de solo lectura para usuarios normales;
- existe una consulta filtrable por usuario, entidad, fecha y acción.

### 4.3 Estados y reversas de documentos

Revisar que ventas, devoluciones, compras y movimientos financieros no dependan únicamente de borrado físico.

**Acciones:**

- definir estados explícitos: `draft`, `confirmed`, `cancelled`, `reversed`;
- impedir modificar documentos confirmados sin una operación de reversa;
- registrar motivo y usuario de la reversa;
- proteger la integridad histórica de costos e inventario;
- añadir restricciones de transición de estados.

---

## 5. Prioridad P1: despliegue en cPanel/Passenger

La producción documentada usa un backend Python administrado por cPanel/Passenger y un frontend Vue compilado como archivos estáticos. Docker no es requisito de producción; se conserva como herramienta de desarrollo local y para ejecutar PostgreSQL/tests con un entorno reproducible.

### 5.1 Despliegue seguro del backend

El script [scripts/deploy.sh](scripts/deploy.sh) sincroniza `backend/`, ejecuta Alembic y reinicia Passenger tocando `passenger_wsgi.py`.

**Acciones:**

- mantener `.env` fuera del repositorio y configurar variables en Passenger/cPanel;
- validar secretos y `DATABASE_URL` antes de ejecutar `alembic upgrade head`;
- comprobar que `APP`, `VENV`, `CLONE` y Python coinciden con el servidor;
- añadir validación previa antes de `rsync --delete`;
- crear backup y registrar la revisión Git antes de migrar;
- no ejecutar el seeder automáticamente en producción;
- conservar rollback de código y base de datos;
- validar el reinicio con una petición a `/health/ready`, no solo con `touch passenger_wsgi.py`.

### 5.2 Despliegue seguro del frontend estático

El script [scripts/deploy-frontend.sh](scripts/deploy-frontend.sh) ejecuta `npm ci`, genera `dist/` y lo sincroniza al docroot de cPanel.

**Acciones:**

- compilar idealmente en CI y publicar un artefacto aprobado;
- si se compila en cPanel, fijar la versión de Node y verificar `npm ci`;
- mantener `.htaccess` con fallback para las rutas de Vue y headers de seguridad;
- configurar cache largo para assets con hash y `no-cache` para `index.html`;
- conservar `.well-known` durante el despliegue;
- verificar la URL raíz, una ruta interna y la conexión contra la API.

### 5.3 Tareas programadas sin workers permanentes

En cPanel/Passenger no conviene asumir Celery, un worker permanente o tareas largas de FastAPI.

**Acciones:**

- programar `backend/scripts/prune_tokens.py` mediante cron de cPanel;
- ejecutar backups y verificaciones desde cron o el proveedor de hosting;
- registrar salida y código de cada cron;
- evitar tareas largas dentro del proceso web de Passenger;
- ejecutar migraciones de datos como comandos CLI supervisados.

### 5.4 Health checks y disponibilidad

**Acciones:**

- `/health/live`: confirma que el proceso responde;
- `/health/ready`: valida la base de datos y dependencias necesarias;
- devolver HTTP 503 cuando la aplicación no esté lista;
- configurar Passenger, el proxy de cPanel y el monitoreo externo para usar readiness;
- no exponer detalles internos de conexión.

### 5.5 Base de datos, backups y recuperación

La base de datos puede ser PostgreSQL administrado por el hosting o un servicio externo; no debe asumirse que vive en un contenedor.

**Acciones:**

- documentar proveedor, host, puerto, TLS y política de conexiones;
- restringir el acceso al servidor de la aplicación cuando sea posible;
- programar backups fuera del servidor web;
- probar restauración en una instancia separada;
- documentar RPO, RTO y reconstrucción de Passenger;
- comprobar que restauración y `alembic upgrade head` producen una instalación operativa.

### 5.6 Migraciones seguras

**Acciones:**

- comprobar `alembic check` en CI;
- probar `upgrade head` sobre una base vacía;
- revisar migraciones destructivas y exigir confirmación explícita;
- evitar operaciones largas que bloqueen tablas en horario productivo;
- documentar estrategia para migraciones con datos existentes;
- validar compatibilidad entre versión de API y versión de esquema.

---

## 6. Prioridad P1: pruebas y calidad

### 6.1 Medir cobertura

Los informes históricos indican que `pytest-cov` y cobertura de Vitest no estaban instalados.

**Acciones:**

- añadir `pytest-cov` y `@vitest/coverage-v8`;
- publicar cobertura en CI;
- establecer un umbral inicial realista, por ejemplo 75%, y aumentarlo gradualmente;
- exigir cobertura específica para inventario, WAC, ventas, devoluciones y permisos;
- medir cobertura de ramas en reglas financieras.

### 6.2 Pruebas de contrato API

**Acciones:**

- generar tipos TypeScript desde OpenAPI en CI;
- detectar cambios incompatibles en schemas y respuestas;
- añadir pruebas de contrato para paginación, errores, roles y fechas;
- validar que el frontend no dependa de campos no documentados;
- considerar validación runtime en fronteras críticas con schemas generados.

### 6.3 Pruebas de concurrencia y fallos

Añadir pruebas para:

- dos ventas simultáneas consumiendo el mismo insumo;
- dos refresh simultáneos usando el mismo token;
- reintentos de una operación con la misma idempotency key;
- rollback cuando falla una parte de una operación;
- deadlocks y reintentos controlados;
- pérdida de conexión durante un commit.

### 6.4 Seguridad automatizada

Añadir al CI:

- `pip-audit`;
- `npm audit` o equivalente con política de severidad;
- escaneo de secretos;
- análisis estático de Python y TypeScript;
- revisión de imágenes Docker con Trivy o herramienta equivalente.

---

## 7. Prioridad P1: rendimiento

### 7.1 Medición de consultas

Los índices actuales deben validarse con datos representativos.

**Acciones:**

- usar `EXPLAIN ANALYZE` para dashboard, ventas, inventario y finanzas;
- revisar índices compuestos según filtros reales;
- evitar cargar relaciones innecesarias;
- revisar consultas N+1 con instrumentación de SQLAlchemy;
- establecer límites máximos de `limit` y tamaño de búsqueda;
- añadir paginación también donde aún existan listados completos.

### 7.2 Caché y agregados

Cuando el volumen crezca:

- cachear catálogos de baja variación;
- precalcular métricas pesadas del dashboard;
- definir invalidación después de ventas, compras y devoluciones;
- no cachear datos financieros sin una política clara de consistencia.

---

## 8. Prioridad P1: frontend

### 8.1 Code splitting completo

En [frontend/src/router/index.ts](frontend/src/router/index.ts) todavía existen imports estáticos de vistas junto con imports dinámicos para facilitar los tests. Esto puede reducir el beneficio real del code splitting.

**Acciones:**

- separar la tabla de rutas productiva de los dobles de test;
- eliminar imports estáticos de vistas en el bundle productivo;
- verificar chunks con `npm run build` y revisar su tamaño;
- añadir presupuesto de bundle en CI.

### 8.2 Modularización pendiente

Continuar la extracción de:

- `FinanzasView.vue`;
- `InventarioView.vue`;
- tablas y formularios de ventas;
- diálogos de devoluciones;
- componentes de filtros y paginación.

La vista debería coordinar estado, mientras los componentes presentan y emiten eventos.

### 8.3 Estado y errores coherentes

**Acciones:**

- centralizar estados `loading`, `empty`, `error` y `retry`;
- mostrar errores de validación por campo;
- cancelar requests al cambiar de vista;
- evitar respuestas antiguas sobrescribiendo datos nuevos;
- normalizar paginación, filtros y ordenamiento en un composable común;
- añadir límites y feedback para acciones duplicadas.

### 8.4 Accesibilidad y experiencia operativa

**Acciones:**

- navegación completa por teclado;
- foco correcto en diálogos;
- etiquetas y mensajes accesibles;
- contraste validado;
- estados de error anunciados por lectores de pantalla;
- confirmar claramente acciones irreversibles.

---

## 9. Prioridad P1/P2: mejoras visuales y de experiencia

El frontend ya tiene una identidad visual clara: tema oscuro editorial, tokens de diseño, PrimeVue, tipografías diferenciadas y estados de carga en varias vistas. Lo que falta es adaptar esa identidad al uso operativo diario de un ERP.

### 9.1 Shell responsive

En [frontend/src/layouts/AppLayout.vue](frontend/src/layouts/AppLayout.vue) el sidebar tiene una columna fija de `220px` y no existe un comportamiento específico para móvil.

**Acciones:**

- convertir el sidebar en drawer en pantallas pequeñas;
- añadir botón de menú visible y accesible;
- cerrar el drawer después de navegar;
- mantener el header usable con nombres largos y botones pequeños;
- respetar `100dvh`, safe areas y orientación horizontal;
- probar 320px, 375px, 768px, 1024px y escritorio amplio.

### 9.2 Navegación más escaneable

El menú de [SidebarMenu.vue](frontend/src/components/layout/SidebarMenu.vue) muestra únicamente texto y usa mayúsculas con espaciado amplio. Esto refuerza la marca, pero reduce la velocidad de reconocimiento en una aplicación con muchos módulos.

**Acciones:**

- añadir iconos consistentes de PrimeIcons;
- agrupar módulos en categorías como Operación, Catálogos, Finanzas y Administración;
- permitir modo expandido y colapsado;
- mantener tooltips cuando el menú esté colapsado;
- añadir estado `:focus-visible` claramente visible;
- marcar correctamente rutas hijas, no solo coincidencias exactas.

### 9.3 Densidad de tablas y responsive operativo

Las tablas son la superficie principal del ERP. En móvil no basta con reducir el ancho: hay que decidir qué información es prioritaria.

**Acciones:**

- definir columnas esenciales y secundarias por tabla;
- ocultar o mover columnas secundarias a un panel de detalle en móvil;
- usar expansión de filas para ventas, devoluciones y compras;
- fijar encabezados cuando el listado sea largo;
- conservar filtros y paginación visibles sin desbordamiento horizontal;
- añadir estados vacíos con una acción clara;
- unificar formato de fechas, moneda, cantidades y estados.

### 9.4 Jerarquía visual del dashboard

El dashboard tiene KPIs, gráficas, stock bajo y márgenes, pero debe guiar mejor la atención hacia excepciones operativas.

**Acciones:**

- ordenar el contenido por acción: alertas de stock, ventas del periodo y márgenes;
- destacar variaciones contra el periodo anterior, no solo valores absolutos;
- usar colores semánticos consistentes para stock, margen y estados;
- mostrar fecha de actualización y rango temporal;
- añadir filtros de periodo sin recargar toda la vista;
- evitar cargar catálogos completos con `limit: 1000` solo para resolver nombres;
- consolidar endpoints de analítica para devolver etiquetas listas para presentación.

### 9.5 Formularios y acciones

Las vistas operativas repiten patrones de formularios, diálogos, botones de actualización y mensajes. La experiencia debe sentirse uniforme.

**Acciones:**

- crear un layout común para títulos, filtros, acciones primarias y contenido;
- diferenciar visualmente acción primaria, secundaria, destructiva y de solo lectura;
- usar iconos en acciones conocidas como actualizar, editar, eliminar y cerrar;
- reservar botones con texto para acciones importantes o ambiguas;
- mostrar cambios sin guardar antes de cerrar un diálogo;
- enfocar el primer campo inválido y devolver el foco al diálogo al terminar;
- evitar que el botón de guardar cambie de tamaño al mostrar loading.

### 9.6 Contraste, tipografía y accesibilidad

La paleta oscura con lavanda, dorado y cian es distintiva, pero debe validarse contra WCAG en texto pequeño, tablas, placeholders y estados deshabilitados.

**Acciones:**

- medir contraste AA de todos los tokens semánticos;
- aumentar contraste de `muted`, `faint` y texto deshabilitado cuando sea necesario;
- no comunicar estados únicamente con color;
- revisar que la fuente serif del body no reduzca la legibilidad de tablas y formularios;
- cargar explícitamente las fuentes de marca o documentar sus sustituciones;
- comprobar navegación completa por teclado y lectores de pantalla;
- añadir `aria-live` para errores, éxitos y cambios de carga.

### 9.7 Consistencia de superficies y movimiento

El tema utiliza gradientes y un glow radial en el login. Conviene reservar estos recursos para identidad y orientación, no para competir con los datos.

**Acciones:**

- reducir efectos decorativos detrás de formularios y tablas;
- establecer una escala común de espacios, radios y sombras;
- definir transiciones breves para apertura de drawer, diálogos y estados de carga;
- respetar `prefers-reduced-motion`;
- evitar tarjetas anidadas y exceso de paneles visualmente equivalentes;
- establecer una jerarquía clara entre página, sección, panel y diálogo.

### 9.8 Pruebas visuales

**Acciones:**

- añadir pruebas de screenshot para login, shell, dashboard, ventas e inventario;
- comparar escritorio y móvil en CI;
- probar tema, loading, error, vacío, permisos y tablas largas;
- validar que no haya clipping, solapamientos ni scroll inesperado;
- revisar accesibilidad automatizada con axe o herramienta equivalente.

**Criterios de aceptación:**

- ninguna vista principal requiere zoom horizontal en móvil;
- todas las acciones importantes son accesibles por teclado;
- los estados de error, carga y vacío son visualmente distinguibles;
- las tablas conservan las columnas y acciones esenciales en pantallas pequeñas;
- el shell mantiene navegación usable desde 320px de ancho.

### 9.9 Evolución de la sección Análisis

La vista actual de [AnalisisView.vue](frontend/src/views/AnalisisView.vue) muestra productos vendidos, compras de insumos y tendencia financiera, pero todavía mezcla acumulados sin periodo seleccionado. Además, el endpoint `top-insumos` representa compras, no consumo real, porque aún no existe un ledger de producción/consumo.

**Implementado en la primera iteración:**

- mostrar el margen por producto usando el snapshot de costo histórico;
- renombrar “Insumos más usados” a “Insumos más comprados” para no inducir a error.

**Pendiente como siguiente fase analítica:**

- filtros por periodo y periodo personalizado;
- comparación contra el periodo anterior;
- KPIs de ventas, unidades, ticket promedio, margen, gastos y resultado neto;
- ventas por canal y tasa de anulaciones/devoluciones;
- ranking separado de volumen, facturación y rentabilidad;
- cobertura y rotación de inventario;
- ledger de consumo real de insumos para reemplazar la aproximación por compras.

---

## 10. Prioridad P2: arquitectura y mantenimiento

### 9.1 Separar configuración por entorno

Centralizar configuración de desarrollo, test, staging y producción sin mezclar defaults. Documentar variables obligatorias y validar valores inválidos al arrancar.

### 9.2 Tipado más estricto

- mantener `strict: true` en TypeScript;
- eliminar excepciones innecesarias de `any`;
- tipar respuestas API con OpenAPI;
- revisar `dict` genéricos en servicios Python;
- evaluar mypy o pyright para módulos financieros y de inventario.

### 9.3 Versionado y compatibilidad API

- documentar cambios de `/api/v1`;
- definir política de deprecación;
- añadir `/api/v2` solo cuando exista incompatibilidad real;
- mantener changelog técnico y funcional;
- versionar también contratos generados del frontend.

### 9.4 Limpieza del repositorio

- revisar `.gitignore` para evitar `.idea/`, `.env`, bases locales y artefactos de build;
- eliminar documentación duplicada o marcarla como histórica;
- actualizar cifras antiguas de tests y estados de roadmap;
- mantener una única fuente de verdad para el estado de las mejoras.

---

## 11. Prioridad P2: observabilidad operativa

### 10.1 Métricas

Medir como mínimo:

- latencia por endpoint;
- tasa de errores 4xx y 5xx;
- conexiones activas y saturación del pool;
- tiempo de consultas SQL;
- ventas, devoluciones y errores de stock;
- intentos de login fallidos y reutilización de tokens.

### 10.2 Alertas

Configurar alertas para:

- API no disponible;
- base de datos no lista;
- aumento de errores 5xx;
- pool agotado;
- fallos de backups;
- crecimiento anormal de tokens o logs;
- stock negativo o inconsistencias de inventario.

### 10.3 Privacidad de logs

- no registrar passwords, JWT ni refresh tokens;
- enmascarar emails e IPs cuando sea necesario;
- definir retención de logs;
- revisar permisos de acceso a logs y auditoría.

---

## 12. Roadmap recomendado

### Fase 1: bloqueo de riesgos críticos

1. secretos obligatorios y eliminación de credenciales fijas;
2. sesiones y expiración de tokens;
3. health/readiness correcto;
4. `.gitignore` y revisión de artefactos;
5. backup inicial y prueba de restauración.

### Fase 2: integridad del negocio

1. idempotencia en operaciones críticas;
2. auditoría funcional;
3. estados y reversas de documentos;
4. pruebas de concurrencia y rollback;
5. restricciones de base de datos adicionales.

### Fase 3: calidad medible

1. cobertura backend/frontend;
2. contratos OpenAPI;
3. auditoría de dependencias y secretos;
4. `alembic check` y pruebas de migración;
5. presupuestos de bundle y rendimiento.

### Fase 4: mantenibilidad y operación

1. code splitting completo;
2. modularización de Finanzas e Inventario;
3. métricas y alertas;
4. documentación de despliegue y recuperación;
5. revisión periódica de deuda técnica.

---

## 13. Resultado esperado

Al completar estas fases, ARPIA tendrá no solo una arquitectura correcta para desarrollo, sino también garantías operativas para producción:

- operaciones repetibles sin duplicados;
- historial auditable;
- recuperación probada ante fallos;
- sesiones y secretos mejor protegidos;
- cambios de esquema controlados;
- calidad medible en cada merge;
- frontend más pequeño, mantenible y accesible;
- alertas antes de que un problema afecte a usuarios o inventario.
