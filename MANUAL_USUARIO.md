# Manual de Usuario — ERP Arpía (Atelier de Confección)

Guía práctica para operar el sistema día a día: qué hace cada módulo, cómo llegar, qué botones utilizar y qué errores evitar.

## Ruta rápida

1. Iniciar sesión en `/login` con el usuario asignado.
2. Revisar el estado del día en `/dashboard` (pedidos activos, insumos críticos, ventas).
3. Operar según la tarea: pedido nuevo, compra de insumo, venta, liquidación.
4. Verificar el resultado en el módulo correspondiente (tabla, KPI o comprobante).

## Acceso y roles

| Rol | Acceso | Notas |
|-----|--------|-------|
| `admin` | Todos los módulos, incluido `/usuarios` | Único rol que puede gestionar usuarios, editar insumos y resolver omisiones. |
| `operador` | Todos los módulos excepto `/usuarios` | Puede crear y mover pedidos, registrar ventas, cargar insumos y liquidar. |
| `consulta` | Todos los módulos excepto `/usuarios` | Acceso de lectura operativa; las acciones de escritura se bloquean en la vista con avisos. |

- Ruta de ingreso: `/login` (botón **Ingresar al Atelier**). Las rutas no autenticadas redirigen a `/login?redirect=...`.
- Si un rol no autorizado intenta abrir `/usuarios`, el sistema redirige a `/dashboard`.
- Cambio rápido de rol (solo para pruebas, visible en `/usuarios`): botones **Admin**, **Operador**, **Consulta**.

## Modos MOCK vs REAL

El sistema opera en dos modos (indicador visible en cada pantalla con `DataSourceBadge`):

| Aspecto | MOCK | REAL |
|---------|------|------|
| Origen de datos | Memoria local del navegador | API `GET /api/v1/...` (Postgres) |
| Persistencia | Se pierde al recargar (excepto lo guardado en store local) | Persiste en base de datos (F5 conserva los datos) |
| Precios/utilidades en Producción | Visibles en tarjetas Kanban | Ocultos (solo flujo de taller) |
| Ajustes rápidos de stock (±1, −1) | Habilitados | Deshabilitados; el stock se mueve con los modales de ingreso/compra |

> Regla general: si un botón aparece deshabilitado en modo REAL, no es un error. Utilice el flujo oficial (ej. **Ingresar Prenda Confeccionada** en lugar de `+1`).

---

## 1. Dashboard — Panel General de Operaciones (`/dashboard`)

**Qué es.** Resumen del estado del atelier: rentabilidad, pedidos activos, ventas e insumos críticos.

**Cómo llegar.** Menú principal → Panel, o ruta `/dashboard`.

**Acciones principales.**

- **Crear Receta con IA**: abre el modal **Asistente IA**. Describa la prenda y seleccione **Guardar como Receta BOM**.
- **Cotizador Rápido**: navega a `/cotizador` para presupuestar antes de crear el pedido.
- **Nuevo Pedido**: abre **Registrar Nuevo Pedido & Confección**. Complete cliente, prenda, medidas y confirme con **Crear Pedido**.
- **Ver inventario de insumos** (enlace bajo la tarjeta de Insumos Críticos): navega a `/insumos`.
- **Generar Orden de Compra**: abre el generador de órdenes a proveedores.
- **Ver Tablero Kanban Completo**: navega a `/produccion`.

**Roles.** Todos (`admin`, `operador`, `consulta`).

**Tips / errores comunes.**

- Los KPI cambian según el modo: en MOCK verá cifras de demostración; en REAL, los valores vacíos significan que aún no hay datos en la base.
- Si la rentabilidad muestra 0 %, verifique que existan ventas en estado COMPLETADA y productos con costo cargado.

## 2. Producción / Pedidos (`/produccion`)

**Qué es.** Tablero de confección por etapas: Cotizado, Reservado, Corte, Costura, Acabados, Calidad, Listo y Entregado.

**Cómo llegar.** Menú → Producción, o ruta `/produccion`.

**Paso a paso.**

1. Pulsar **Nuevo Pedido** → modal **Registrar Nuevo Pedido & Confección** → completar cliente, prenda/modelo, talla, fecha y anticipo → **Crear Pedido**.
2. Localizar el pedido con el buscador (*código, cliente o prenda*) o cambiar entre **Tablero Kanban** y **Vista de Lista**.
3. Avanzar el pedido con **Siguiente →** (Kanban) o **Avanzar Fase** (lista). Para corregir, usar **← Anterior**.
4. Abrir la ficha de taller con el icono de reloj (**Ver Ficha de Taller & Tiempos**) para ver detalle y tiempos.
5. Contactar a la clienta con el icono **WhatsApp**.
6. Atajo: **Cotizador Rápido** lleva a `/cotizador` sin perder el contexto.

**Roles.** Todos. Las transiciones de estado en modo REAL exigen autenticación válida; los pedidos en estado terminal ya no avanzan.

**Tips / errores comunes.**

- En modo REAL las tarjetas no muestran precio ni utilidad (diseño intencional).
- Si **Avanzar Fase** aparece deshabilitado, el pedido está en estado terminal o hay una transición en curso.
- Los pedidos se recargan automáticamente después de crear uno nuevo (`pedido-creado`).

## 3. Inventario / Insumos (`/inventario`, alias `/insumos`)

**Qué es.** Control de materias primas directas (telas, forros, cierres) e indirectas (hilos, etiquetas, empaques), con alertas de stock mínimo.

**Cómo llegar.** Menú → Inventario, o rutas `/inventario` y `/insumos` (misma pantalla).

**Paso a paso.**

1. **Nuevo Insumo** → modal **Registrar Nuevo Insumo / Materia Prima** → completar nombre, categoría, Stock Inicial, Stock Mínimo (Alerta), Costo Unitario → **Guardar Insumo**.
2. **+ Compra** sobre un insumo → modal **Registrar Compra** → cantidad y costo → **Registrar Entrada**. Actualiza stock y valor promedio.
3. Ajuste rápido con botones **−** y **+** (suma/resta 1 unidad).
4. **Editar** (solo admin) → modal **Editar Insumo** → modificar Stock Actual, Stock Mínimo, Costo → **Guardar Cambios**.
5. Eliminar con el icono de papelera (confirme en el diálogo).
6. **Sugerir Orden (N)** → modal **Sugerir Orden de Compra de Insumos** para reponer los insumos bajo mínimo.
7. **Orden a Proveedores** → modal **Generador de Órdenes de Compra a Proveedores Textil** → **Confirmar Abastecimiento a Taller**.
8. Filtrar con buscador (*nombre, código o proveedor*), pestañas **Todos / Directos / Indirectos**, lista de categorías y botón **Solo Bajo Stock**. Ordenar con **Insumo / Stock / Valor**.

**Roles.** Todos para consulta y compra. **Editar** y eliminar requieren `admin` (el botón Editar solo es visible para admin).

**Tips / errores comunes.**

- Configure siempre el **Stock Mínimo (Alerta)**; sin este valor el insumo nunca entra en la lista de críticos.
- En modo REAL los botones `−1 / +1` de ajuste rápido no aplican; utilice **+ Compra**.
- El valor del inventario usa costo promedio ponderado.

## 4. Productos / Recetas / BOM (`/productos`, alias `/recetas`)

**Qué es.** Catálogo de modelos con escandallo de costeo (insumos, mano de obra, CIF) y margen sugerido. Cada receta es una ficha técnica con su BOM.

**Cómo llegar.** Menú → Productos o Recetas; rutas `/productos` y `/recetas` (misma pantalla).

**Paso a paso.**

1. **Nueva Receta Manual** → modal **Crear Nueva Receta / Ficha Técnica (BOM)** → nombre, código, categoría, tiempos, insumos del BOM → guardar.
2. **Generar con IA** → modal **Asistente IA** → describir la prenda → **Guardar como Receta BOM**.
3. **Ver Ficha Técnica >** sobre una tarjeta → modal de ficha: ver costos, BOM, tiempos y precio. Para modificar, usar el icono de lápiz (**Editar Receta**) → editar campos → **Guardar**.
4. **Planilla Google Sheet (Matriz de Corte)**: abre la ficha del primer modelo para preparar la matriz de corte.
5. Filtrar por buscador (*nombre, código o material*), categorías (Corsetería, Blusas y Tops, Conjuntos y Sets, Vestidos, Pantalones, Accesorios, Alta Costura), margen (**Pérdida / Por debajo / En meta / Alto**) y ordenar por Nombre, Margen, Precio o Costo.
6. Eliminar con el icono de papelera → confirmar en **Eliminar receta**.

**Roles.** Todos.

**Tips / errores comunes.**

- En modo REAL sin productos, la pantalla indica la fuente (`GET /api/v1/productos`): cree el producto desde el backend o vuelva a modo demostración.
- El margen se compara contra la meta global (parámetro en Maestros, por defecto 35–65 % según vista). Un margen en rojo indica pérdida o precio por debajo del costo.
- El conteo **Insumos BOM** en modo REAL se calcula por producto; puede tardar unos segundos en aparecer.

## 5. Prendas (`/prendas`)

**Qué es.** Inventario de prendas terminadas en perchero/showroom, con variantes por talla, reservas y etiquetas de autor con QR.

**Cómo llegar.** Menú → Prendas, o ruta `/prendas`.

**Paso a paso.**

1. **Ingresar Prenda Confeccionada** → modal **Ingresar Prenda Confeccionada al Perchero** → producto, talla, variante → confirmar. Cada fila equivale a 1 unidad en modo REAL.
2. Buscar con el campo (*nombre o código*).
3. Ver **Etiqueta QR** (botón o icono QR por variante) → modal **Etiqueta de Autor & Certificado de Autenticidad** con cuidados (lavado en seco, no cloro, plancha baja).
4. Ajustar stock con **−1 / +1** (solo MOCK). En REAL estos botones están deshabilitados a propósito.

**Roles.** Todos.

**Tips / errores comunes.**

- Físico vs Disponible vs Reservado: Físico es lo que hay en perchero; Reservado está apartado por pedidos con abono; Disponible es la diferencia vendible de inmediato.
- Si necesita mover stock en REAL, no busque un botón de edición: use **Ingresar Prenda Confeccionada**.

## 6. Clientes (`/clientes`)

**Qué es.** CRM de clientas con tallas estándar de marca (XXS–XL), productos sin talla (Tote Bags), historial comercial y contacto por WhatsApp.

**Cómo llegar.** Menú → Clientes, o ruta `/clientes`.

**Paso a paso.**

1. **Registrar Clienta** → modal **Registrar Nueva Clienta (CRM Atelier)** → nombre, teléfono, email, ciudad, talla habitual, categoría preferida → guardar. Para modificar, icono de lápiz (**Editar Clienta**).
2. **Ficha de Talla** (botón en cada tarjeta) → modal **Ficha de Talla & Guía de Confección** → ajustar talla y preferencias → **Guardar Talla de Clienta**.
3. **Guía Oficial de Tallas**: abre la guía general de referencia.
4. **WhatsApp** (botón verde por tarjeta): abre conversación con mensaje predefinido según talla o Tote Bag.
5. Filtrar con buscador (*nombre, teléfono, ciudad, notas*), listas de talla y categoría, pestañas rápidas de talla (**Todas, XXS–XL, Sin Talla**) y botón **Limpiar / Limpiar Filtros**.
6. Eliminar con papelera → confirmar en **Eliminar clienta**.

**Roles.** Todos.

**Tips / errores comunes.**

- Las clientas de Tote Bags y accesorios usan **Sin Talla**; no les asigne XXS–XL.
- Si el botón de WhatsApp abre un número genérico, falta el teléfono de la clienta en su ficha.

## 7. Cotizador (`/cotizador`)

**Qué es.** Calculadora de precio para presupuestar una prenda en segundos (telas, avíos, mano de obra, CIF y margen).

**Cómo llegar.** Menú → Cotizador, o ruta `/cotizador`. También se llega desde Producción y Dashboard con **Cotizador Rápido**.

**Paso a paso.**

1. Seleccionar **Cargar desde Receta BOM** o escribir el **Nombre de la Prenda** manualmente.
2. Completar sección **1. Telas y Forros Directos**: Metros Tela Principal, Precio Metro, Metros Forro, Precio Forro.
3. Completar sección **2. Avíos, Cierres & Empaque**: cierres/botones/hilo y empaque/etiquetas.
4. Completar sección **3. Mano de Obra & Costos Fijos (CIF)**: Tiempo Confección (min), Tarifa $/hora, CIF/Luz.
5. Ajustar el **Margen de Ganancia Deseado** con el deslizador (20 % mayorista, 55–65 % estándar, 80 %+ alta costura).
6. Leer el **Resumen de Cotización** y el **Precio de Venta Sugerido al Cliente**.
7. En modo REAL con receta seleccionada: comparar con el **Costo real BOM (DB)** y usar **Usar costo real** si corresponde.
8. Pulsar **Copiar Presupuesto para WhatsApp** y enviarlo a la clienta. Para producirlo, pulsar **Ir a Gestión de Pedidos**.

**Roles.** Todos.

**Tips / errores comunes.**

- Si el precio sugerido parece duplicado, revise que el margen no esté en 100 % o más.
- **Usar costo real** ajusta el CIF para igualar el cálculo manual al BOM; es reversible editando el CIF.

## 8. Optimizador (`/optimizador`)

**Qué es.** Planificador de corte: calcula cuánta tela requiere un tendido, el aprovechamiento del rollo y qué hacer con los retazos.

**Cómo llegar.** Menú → Optimizador, o ruta `/optimizador`.

**Paso a paso.**

1. En **Datos del Rollo o Corte de Tela**, seleccionar **Cargar Tela desde Inventario** (trae el stock en metros) o cargar **Ancho de Tela** y **Largo Total Disponible** manualmente.
2. En **Prendas a Cortar en la Mesa**, pulsar **+ Agregar Prenda** por cada modelo; completar nombre, **Cantidad** y **Metros c/u**. Eliminar filas con la papelera.
3. Revisar **Total Tela Requerida**, barra de **Aprovechamiento**, **Sobrante** o **Faltan** metros.
4. Pulsar **Optimizar Rendimiento & Retazos con IA** y leer el resultado: **Eficiencia de Corte en Mesa** (Alta/Media/Baja), **Esquema Visual de Tendido** y **Oportunidades de Monetización de Retazos** (scrunchies, antifaces, chokers con valores estimados).

**Roles.** Todos.

**Tips / errores comunes.**

- Si el aprovechamiento supera el 100 %, faltan metros: reduzca cantidades o consiga más tela antes de tender.
- El esquema visual es proporcional e ilustrativo, no un plano de corte a escala real.

## 9. Análisis (`/analisis`)

**Qué es.** Vista de lectura con métricas de productividad y tabla de rentabilidad por receta.

**Cómo llegar.** Menú → Análisis, o ruta `/analisis`.

**Paso a paso.**

1. Leer los 4 indicadores: **Prendas en Confección Activa**, **Pedidos de Alta Costura Entregados**, **Prendas en Showroom**, **Insumos con Stock Crítico**.
2. Revisar la tabla **Rentabilidad por Ficha Técnica / Receta BOM**: Costo Insumos, Horas Confección, Precio Sugerido y Margen Bruto (valor y %).

**Roles.** Todos (solo lectura, sin acciones de escritura).

**Tips / errores comunes.**

- Sin recetas en modo REAL, la tabla muestra el mensaje de fuente vacía; no es un error de permisos.
- Los estados de pedido se normalizan entre modos (mayúsculas MOCK vs enum REAL); los contadores ya contemplan ambas formas.

## 10. Ventas (`/ventas`)

**Qué es.** Registro de ventas realizadas, facturación por canal, recibos y base para el reparto 40/30/30.

**Cómo llegar.** Menú → Ventas, o ruta `/ventas`.

**Paso a paso.**

1. **Registrar Nueva Venta** → modal **Registrar Nueva Venta Realizada** → cliente, canal (Showroom Pereira, WhatsApp/DM, Feria/Evento NANA, Feria Gótica, Feria Showroom, Tienda Online/Instagram, Encargo Personalizado), método de pago, prendas/tallas/cantidades, descuento → guardar. Para corregir, usar el icono de lápiz (**Editar Venta**).
2. Ver el comprobante con el icono de recibo (**Ver Comprobante / Recibo**) → modal **Comprobante de Venta** (permite **Editar** desde el detalle).
3. Filtrar con buscador (*código, prenda, cliente, canal*), listas de **Canal**, **Estado** (Completada/Pendiente/Anulada) y orden (**recientes, antiguas, mayor total, mayor ganancia**). Botón **Limpiar** para restablecer.
4. **Exportar CSV**: descarga `ARPIA_VENTAS_HISTORICO_*.csv` con el histórico completo.
5. Eliminar/anular con la papelera → confirmar en **Confirmar Eliminación de Venta** con **Sí, Eliminar Venta**. En REAL la venta se anula (no se borra el rastro financiero).

**Roles.** Todos.

**Tips / errores comunes.**

- Los KPI (Total Facturado, Ganancia Neta, Margen, Fondo 40 %, Margara & Valqui 30/30) se calculan sobre ventas COMPLETADAS del filtro actual.
- Si una venta no descuenta inventario, revise el campo `descontar_inventario` en el modal.
- En REAL, anular es la vía correcta; evita eliminar ventas ya liquidadas.

## 11. Devoluciones (`/devoluciones`)

**Qué es.** Gestión de garantías y ajustes post-entrega (calce, varillas, adaptaciones de corsetería).

**Cómo llegar.** Menú → Devoluciones o Garantías, o ruta `/devoluciones`.

**Paso a paso.**

1. **Registrar devolución** → completar **ID de venta**, **Tipo** (Total: cancela la venta completa; Parcial: requiere al menos un ítem), **Motivo** → **Guardar devolución**.
2. Si es parcial, pulsar **Agregar ítem** por cada producto (Producto ID, Cantidad, Precio unit.). El precio final se recalcula desde la venta original en el backend.
3. Consultar estados: Borrador, Confirmada, Anulada, Revertida.
4. Eliminar solo borradores con la papelera (**Eliminar borrador**) → confirmar en **Eliminar devolución** con **Eliminar**. Las confirmadas se anulan por transición de estado, no se eliminan.

**Roles.** Todos para registrar y consultar; la eliminación está limitada a borradores.

**Tips / errores comunes.**

- El error más común es intentar registrar una parcial sin ítems: el sistema exige al menos un ítem válido (ID y cantidad > 0).
- Tenga a mano el ID numérico de la venta (ej. 12); el formulario lo pide como número, no como código.

## 12. Finanzas / Socias (`/finanzas`, alias `/socias`)

**Qué es.** Módulo integral de reparto con fórmula 40/30/30: liquidaciones, socias, anticipos, movimientos y simulador de punto de equilibrio.

**Cómo llegar.** Menú → Finanzas o Socias; rutas `/finanzas` y `/socias` (misma pantalla).

**Pestañas.** **Liquidaciones & Cierres** · **Perfiles de Socias & Cuentas** · **Anticipos & Retiros** · **Movimientos** · **Simulador Punto Equilibrio Textil**.

**Paso a paso.**

1. **Nueva Liquidación** → modal **Nueva Liquidación & Reparto de Socias** → período, fecha de cierre, ventas brutas, costos de insumos, gastos operativos → guardar. El sistema calcula utilidad neta, fondo 40 % y reparto 30/30.
2. Sobre cada liquidación: ver con el ojo (**Ver Acta Oficial & Transferencias**) → modal **Acta Oficial de Reparto**; cambiar estado pulsando la etiqueta (**BORRADOR → APROBADA → PAGADA**); registrar pagos con **Registrar Pago** → **Confirmar Pago**; eliminar con papelera. Nota: en modo REAL la edición directa está deshabilitada (solo transición de estado).
3. **Añadir Nueva Socia** → modal **Registrar Nueva Socia o Fondo de Reparto** → nombre, rol, porcentaje, banco, cuenta. Editar con lápiz, activar/desactivar con **Activar/Desactivar**. La suma activa debe respetar 40/30/30.
4. **Registrar Nuevo Anticipo** → modal **Registrar Nuevo Anticipo / Adelanto a Socia** → socia, monto, concepto, método, comprobante → guardar. Marcar como descontado con el icono de check (**Marcar como Descontado**; en REAL exige liquidación asociada). Editar con lápiz, eliminar con papelera.
5. **Movimientos**: vista de solo lectura con filtros por tipo (Gasto/Inversión/Retiro) y estado (draft/confirmed/cancelled/reversed).
6. **Simulador Punto Equilibrio Textil**: ajustar precio promedio, costo de insumos, horas, costo hora, gastos operativos y meta de prendas para ver margen de contribución, unidades de equilibrio y utilidad simulada.
7. **Imprimir Balance**: prepara el balance oficial para impresión.

**Roles.** Todos para operar; la gestión de socias y pagos es sensible: reservar a `admin` por política interna aunque el sistema la permita a otros roles.

**Tips / errores comunes.**

- No descontar anticipos sin liquidación: en REAL el sistema lo bloquea y pide seleccionar una liquidación.
- Si la suma de porcentajes no da 100 %, revise el fondo taller (40 %) y las dos socias de reparto (30/30).
- En REAL los nombres de socias son dinámicos (no asumir Margara/Valqui como fijos).

## 13. Maestros (`/maestros`)

**Qué es.** Catálogos base que alimentan todo el sistema: proveedores, canales, métodos de pago, tallas, ubicaciones, categorías y parámetros de costeo.

**Cómo llegar.** Menú → Maestros, o ruta `/maestros`.

**Pestañas.** Proveedores Textil & Herrajes · Canales de Venta · Métodos de Pago · Matriz de Tallas & Sin Talla · Familias de Colección · Ubicaciones Taller · Parámetros (costeo).

**Paso a paso.**

1. **Nuevo Proveedor** → completar nombre, categoría, ciudad, contacto, calificación, tiempo de entrega → **Guardar Proveedor**. Editar con **Editar Proveedor**.
2. **Nuevo Canal** → nombre, código, tipo (Físico/Digital/Evento), comisión, costo fijo → **Guardar Canal**.
3. **Nuevo Método de Pago** → nombre, código, tipo (Transferencia/Billetera/Efectivo/Pasarela), comisión → **Guardar Método**.
4. **Nueva Talla Estándar** → talla, medidas, descripción → **Guardar Talla**. **Nuevo Producto Sin Talla** → formato (ej. Tote Bag) → **Guardar Formato**.
5. **Nueva Familia de Colección** → nombre, tipo de talla (Con Tallas XXS-XL o Sin Talla/Merch) → **Guardar Familia**.
6. **Nueva Ubicación** → nombre de zona de almacenamiento → **Guardar Ubicación**.
7. **Guardar Parámetros de Costeo**: costo minuto costura, costo hora patronaje, margen meta global %, desperdicio textil %, IVA, distribución 40/30/30.

**Roles.** Todos en el sistema; por política interna reservar a `admin` (un error aquí afecta costos y reportes).

**Tips / errores comunes.**

- Los códigos de canal y método se autogeneran desde el nombre si se dejan vacíos; revíselos antes de guardar.
- Cambiar el margen meta global altera los colores y filtros de Productos y Análisis.

## 14. Omisiones (`/omisiones`)

**Qué es.** Bitácora auditable de ajustes especiales: mermas manuales, excepciones de precio, cambios de patrón.

**Cómo llegar.** Menú → Omisiones, o ruta `/omisiones`.

**Paso a paso.**

1. Revisar la tabla: Fecha, Responsable, Detalle del Evento, Impacto, Estado.
2. Marcar como tratada con **Resolver** (botón con check). Al resolverse muestra la etiqueta **Resuelta**.

**Roles.** Todos para lectura; **Resolver** requiere `admin` (si falla, el sistema indica revisar permisos).

**Tips / errores comunes.**

- En modo REAL vacía, la pantalla indica la fuente (`GET /api/v1/omisiones`); significa que no hay registros, no un error.
- No eliminar registros de esta bitácora: es evidencia de auditoría.

## 15. Auditoría (`/auditoria`)

**Qué es.** Historial fiscal de solo lectura: versiones de precio, versiones de costo y cierres mensuales por producto.

**Cómo llegar.** Menú → Auditoría, o ruta `/auditoria`.

**Paso a paso.**

1. Elegir pestaña: **Versiones de precio**, **Versiones de costo** o **Cierres mensuales**.
2. Filtrar por **producto_id** con **Filtrar**; restablecer con **Limpiar**.
3. Leer ID, Producto, Variante, Precio/Costo y Vigencia (desde), o Período y Estado en cierres.

**Roles.** Todos (solo lectura; no modifica datos).

**Tips / errores comunes.**

- En modo MOCK no hay datos por diseño: cambie a modo REAL para consultar los endpoints de auditoría fiscal.
- Para rastrear un cambio de precio necesita el ID numérico del producto, no su código.

## 16. Usuarios (`/usuarios`)

**Qué es.** Gestión de accesos y permisos por rol. Único módulo restringido.

**Cómo llegar.** Menú → Usuarios (solo visible para admin), o ruta `/usuarios`.

**Paso a paso.**

1. Buscar por nombre o email; filtrar por rol (**Admin / Operador / Consulta**).
2. **Nuevo usuario** → completar Nombre, Email, Rol (Administrador, Operador de taller, Auditor/Consulta), Contraseña (mín. 6) → **Guardar**.
3. Editar con el lápiz (**Editar usuario**); cambiar contraseña con la llave (**Cambiar contraseña** → **Actualizar**); dar de baja con la papelera (**Dar de baja** → confirmar en **Confirmar baja de usuario**).
4. Solo pruebas: **Cambio rápido de rol** (Admin/Operador/Consulta) para verificar permisos.

**Roles.** Solo `admin` (restricción en `src/router/index.ts`: `meta.roles: ['admin']`).

**Tips / errores comunes.**

- La baja es irreversible y en REAL ejecuta DELETE (no existe desactivación).
- En MOCK la lista es local y mínima (3 usuarios de ejemplo); en REAL proviene de `GET /api/v1/usuarios`.
- Para cambiar la contraseña propia se verifica la actual; para otros usuarios el admin puede indicar cualquiera.

---

## Lista de verificación del operador

- [ ] Puedo iniciar sesión y veo el Dashboard con datos coherentes.
- [ ] Puedo crear un pedido y avanzarlo de fase.
- [ ] Puedo cargar un insumo y registrar una compra.
- [ ] Puedo registrar una venta y ver su comprobante.
- [ ] Puedo crear una liquidación y entender el reparto 40/30/30.
- [ ] Sé distinguir el modo MOCK del modo REAL antes de reportar un error.

## Siguiente paso

Si un dato no aparece en modo REAL, verificar primero el modo activo y los filtros aplicados; si persiste, revisar el módulo Maestros (catálogos) y luego reportar con código, fecha y captura de pantalla.
