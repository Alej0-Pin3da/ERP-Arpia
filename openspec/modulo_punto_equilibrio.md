# ESPECIFICACIÓN TÉCNICA: MÓDULO DE PUNTO DE EQUILIBRIO Y RENTABILIDAD MENSUAL

## 1. Contexto y Objetivo
Necesitamos implementar un "Termómetro de Rentabilidad" en el dashboard de Arpía ERP. El objetivo es que el sistema calcule automáticamente cuánto necesitamos facturar en el mes actual para cubrir nuestros costos fijos operativos (arriendo, servicios, etc.), basándose en el margen de contribución real de las ventas realizadas.

---

## 2. Base de Datos y Modelos (SQLAlchemy & Alembic)
1. **Actualización de Parámetros:** Localiza la tabla de configuración global (la misma que guarda `margen_meta_global_pct` en el esquema de Maestros).
2. **Nueva Columna:** Agrega una columna `costos_fijos_mensuales` (tipo `Numeric`, por defecto `0`).
3. **Migración:** Genera la migración con Alembic (`alembic revision --autogenerate -m "add_costos_fijos_mensuales"`).
4. **Validación:** Actualiza los schemas de Pydantic correspondientes para permitir la lectura y edición de este nuevo campo.

---

## 3. Backend: Endpoint de Análisis Financiero (FastAPI)
Crea un endpoint estadístico ligero para calcular la métrica en tiempo real.

*   **Ruta:** `GET /api/v1/finanzas/punto-equilibrio`
*   **Lógica Requerida:**
    1. Filtrar las **Ventas** realizadas únicamente durante el mes en curso.
    2. Sumar el ingreso total (`Total Ventas`) y el costo operativo total (`Total Costos`) de esas ventas.
    3. Calcular el **Margen de Contribución Promedio (MC%)**: 
       `MC% = (Total Ventas - Total Costos) / Total Ventas`. 
       *(Asegurar manejo de división por cero si no hay ventas).*
    4. Consultar el valor de `costos_fijos_mensuales` configurado en los parámetros.
    5. Calcular la **Meta de Ventas (Punto de Equilibrio)**: 
       `Meta = Costos Fijos / MC%`.
    6. Calcular el `monto_faltante` y el `porcentaje_avance`.
*   **Payload de Salida (JSON):**
    Retornar todos los valores calculados listos para ser consumidos por el frontend.

---

## 4. Frontend: Termómetro de Rentabilidad (Vue 3 + PrimeVue)
Integra el indicador visual en el panel principal (`DashboardView.vue` o `AnalisisView.vue`).

1. **Componente Visual:** Utiliza el componente `<ProgressBar>` de PrimeVue para graficar el `porcentaje_avance` del mes.
2. **Estados UI/UX Condicionales:**
   - **Bajo la meta (< 100%):** Mostrar la barra de progreso en tono ámbar/naranja con un mensaje claro: *"Faltan $X para cubrir los costos operativos del mes"*.
   - **Meta superada (>= 100%):** Mostrar la barra en verde esmeralda con un indicador de éxito: *"¡Punto de Equilibrio superado! Toda venta adicional es utilidad neta"*.
3. **Edición de Costos Fijos:** Asegúrate de que en la vista de **Maestros** (donde se configura el margen global) exista un campo `InputNumber` (modo currency) para editar los "Costos Fijos Mensuales" de manera ágil.

---

## 5. Instrucciones de Ejecución para OpenCode
Actúa como un Ingeniero de Software Senior. Debes implementar este módulo paso a paso:
1. Comienza por modificar el modelo en SQLAlchemy y genera la migración de Alembic. Revisa el script generado antes de hacer el upgrade.
2. Implementa la lógica matemática en el router de FastAPI asegurando el uso estricto de `Decimal` para evitar errores de coma flotante.
3. Finalmente, construye el componente visual en Vue 3 integrando el endpoint.
4. Avísame al terminar cada capa (DB, Backend, Frontend) para llevar el control del avance.