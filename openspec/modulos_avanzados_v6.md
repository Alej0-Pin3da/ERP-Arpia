# ESPECIFICACIÓN TÉCNICA Y DE ARQUITECTURA: MÓDULOS DE EXPANSIÓN Y PURGA (ARPÍA ERP - V6)

## 1. Contexto y Visión Global
Este documento define la estrategia completa para la versión V6 de Arpía ERP. Antes de desarrollar nuevas capacidades, se ejecutará una purga estricta de deuda técnica (Fase 0). Posteriormente, se implementarán 5 módulos avanzados orientados a la automatización de procesos financieros, sincronización de e-commerce, kits promocionales y análisis predictivo de inventario.

---

## 2. FASE 0: PURGA DE DEUDA TÉCNICA Y LIMPIEZA PREVIA (OBLIGATORIA)
Antes de construir los nuevos módulos, OpenCode debe eliminar los componentes legacy y la dependencia de datos falsos:

1. **Eliminación Total de Mock Data (`atelier.ts`):**
   - Buscar y eliminar todas las importaciones y llamadas a `useAtelierStore` en las vistas principales (`DashboardView.vue`, `AnalisisView.vue`, `AppLayout.vue`) y modales.
   - Forzar el uso exclusivo de los servicios reales (`useClientes`, `useVentas`, `useInsumos`, etc.) respetando el switch de la aplicación.

2. **Limpieza del Modelo Estático en el Cotizador:**
   - Eliminar las columnas estáticas obsoletas de la base de datos y del modelo SQLAlchemy (`metros_tela`, `precio_metro_tela`, `metros_forro`, `precio_metro_forro`).
   - Reemplazar en `CotizadorView.vue` la antigua "Sección 1: Telas y Forros Directos" por la nueva estructura dinámica basada en un arreglo de materiales (BOM dinámico).

3. **Desacoplamiento de Lógica en Modales Financieros y de Inventario:**
   - Remover cálculos matemáticos locales de liquidación de socias en modales (`NuevaLiquidacionModal.vue`), preparando el terreno para que el backend maneje el nuevo modelo financiero.
   - Limpiar la lógica de cliente que calcula alertas de stock crítico, dejando que el backend devuelva dichos estados directamente desde la base de datos.

---

## 3. MÓDULO 1: Gestión de "Cajas", Kits y Descuentos Dinámicos
Permitir la agrupación de múltiples prendas (BOMs) bajo un solo SKU comercial para campañas promocionales.

*   **Modelo de Datos (SQLAlchemy):** 
    *   Crear tabla `Kits` (`id`, `nombre`, `precio_promocional`, `activo`).
    *   Crear tabla pivote `Kit_Productos` (`kit_id`, `producto_id`, `cantidad`).
*   **Lógica de Negocio (Backend):** 
    *   Al cotizar o vender un Kit, el sistema debe sumar el `costo_total` de los productos que lo componen.
    *   Verificar automáticamente si `precio_promocional - suma(costos)` respeta el margen de seguridad de Arpía (al menos 5% de utilidad). Si no, retornar una alerta visual.
*   **Frontend (Vue 3):**
    *   Crear `NuevoKitModal.vue` donde el usuario seleccione productos existentes y asigne un precio final de "Caja".

---

## 4. MÓDULO 2: Automatización de Liquidación y Reinversión
Automatizar la división de ganancias (Arpía, Valqui, Margarita, Fondos de Reinversión) que actualmente se hace manualmente.

*   **Modelo de Datos (SQLAlchemy):**
    *   Crear tabla `Reglas_Liquidacion` (`id`, `cuenta_destino`, `porcentaje`). Ejemplo: Valqui=33.3%, Margarita=33.3%, Reinversión=33.3%.
    *   Crear tabla `Saldos_Socias` para llevar el acumulado por cuenta.
*   **Lógica de Negocio (Backend):**
    *   En el endpoint de venta completada (`POST /api/v1/ventas`), interceptar la `ganancia_neta` calculada por el Módulo de Costeo.
    *   Ejecutar un servicio interno que divida esa `ganancia_neta` multiplicándola por los porcentajes de `Reglas_Liquidacion` y sume los montos a `Saldos_Socias`.
*   **Frontend (Vue 3):**
    *   Actualizar `FinanzasView.vue` para mostrar el saldo en tiempo real de cada socia sin necesidad de cargar un Excel.

---

## 5. MÓDULO 3: Sincronización Bidireccional con WooCommerce
Evitar quiebres de stock sincronizando el inventario del ERP con la tienda web.

*   **API y Endpoints (FastAPI):**
    *   Crear router `webhooks.py` con un endpoint `POST /api/v1/webhooks/woo/order-created`.
*   **Lógica de Negocio (Backend):**
    *   Validar la firma secreta del webhook de WooCommerce.
    *   Extraer los SKUs de los productos vendidos.
    *   Localizar el `producto_id` en la BD y descontar 1 unidad del inventario final. 
    *   Si el producto se hace "Bajo Pedido", descontar directamente el metraje de la tela en la tabla `Insumos` usando el detalle del campo `insumos_detalle` (BOM) del producto.

---

## 6. MÓDULO 4: Análisis Predictivo de Inventario (Reservas)
Proteger el inventario de insumos cuando hay pedidos en curso para que no se asuma que hay tela disponible cuando ya está comprometida.

*   **Modelo de Datos (SQLAlchemy):**
    *   Añadir columna `stock_reservado` (Numeric) a la tabla `Insumos`.
*   **Lógica de Negocio (Backend):**
    *   Al crear una **Orden de Producción** (estado = `en_proceso`), leer el BOM de la prenda, calcular el consumo total de tela y sumarlo a `stock_reservado`.
    *   Cuando la Orden de Producción cambie a `terminada`, restar ese monto de `stock_reservado` y también restarlo de `stock_actual`.
*   **Frontend (Vue 3):**
    *   En `InventarioView.vue`, mostrar `Stock Disponible = (stock_actual - stock_reservado)`.
    *   Si `Stock Disponible < stock_minimo`, pintar la fila de rojo y activar la alerta de insumos críticos.

---

## 7. MÓDULO 5: Generación de Copy Comercial con IA Local
Estandarizar las descripciones de los productos en la tienda web utilizando un LLM.

*   **Integración (FastAPI):**
    *   Crear endpoint `POST /api/v1/ai/generar-copy`.
    *   Utilizar la librería `httpx` o `requests` para conectar con el puerto local de Ollama o llama.cpp (ej. `http://localhost:11434/api/generate`).
*   **Lógica de Prompting:**
    *   Al recibir un `producto_id`, el backend lee su `insumos_detalle` (BOM).
    *   Inyecta los datos en este prompt interno: *"Actúa como un experto en marketing de moda alternativa. Escribe una descripción de producto de 2 párrafos para [Nombre de Prenda]. Menciona que está fabricada con materiales de alta calidad, incluyendo: [Lista de Insumos del BOM]. Tono: Oscuro, elegante, alternativo."*
*   **Frontend (Vue 3):**
    *   En el detalle del producto, añadir un botón "Generar Descripción con IA".

---

## 8. Instrucciones de Ejecución para OpenCode

Actúa como un Ingeniero de Software Senior. Debes implementar esta versión V6 de manera estrictamente secuencial:
1. **Paso Obligatorio Inicial (Fase 0):** Ejecuta la purga de deuda técnica, eliminando las dependencias de `atelier.ts` y refactorizando el cotizador para usar BOM dinámico sin columnas estáticas.
2. **Desarrollo de Módulos (1 al 5):** Para cada módulo subsiguiente:
   - Comienza **siempre** por el Modelo de Datos (SQLAlchemy) y genera la migración correspondiente con Alembic (`alembic revision --autogenerate`). Revisa el código SQL generado antes de aplicarlo.
   - Implementa los Schemas de Pydantic asegurando el uso de `Decimal` para cualquier valor monetario o fraccional.
   - Escribe la lógica en los routers de FastAPI dentro de transacciones atómicas seguras.
   - Actualiza el código en Vue 3 (`.vue` y stores/composables), conectando los nuevos endpoints.
3. Pregunta al usuario o avísale al concluir cada fase antes de continuar con la siguiente.