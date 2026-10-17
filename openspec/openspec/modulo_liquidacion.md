# ESPECIFICACIÓN TÉCNICA: MÓDULO DE LIQUIDACIÓN AUTOMÁTICA (40-30-30)

## 1. Contexto Financiero
Arpía ERP necesita automatizar la división de utilidades cada vez que se concreta una venta. La regla de negocio definida para repartir la "Ganancia Neta" (Total Venta - Costo Total Operativo) es estricta:
- **Fondo de Reinversión (Caja Taller):** 40%
- **Cuenta Valqui:** 30%
- **Cuenta Margarita:** 30%

## 2. Base de Datos (SQLAlchemy)
1. **Tabla `Saldos_Cuentas`:** Crear una tabla para llevar el acumulado de dinero disponible para cada parte.
   - `id` (PK)
   - `nombre_cuenta` (String: "Reinversión", "Valqui", "Margarita")
   - `saldo_actual` (Numeric, default 0)
2. **Tabla `Historial_Liquidaciones`:** Para auditoría.
   - `id` (PK)
   - `venta_id` (FK)
   - `cuenta_id` (FK)
   - `monto_acreditado` (Numeric)
   - `fecha` (DateTime)

## 3. Lógica del Backend (FastAPI)
- En el endpoint encargado de cerrar/completar una orden (`POST /ventas` o `PATCH /ventas/{id}/estado`), interceptar el cálculo de la `ganancia_neta` de los productos vendidos.
- Ejecutar una transacción atómica que:
  1. Calcule el 40% de la ganancia neta y lo sume al `saldo_actual` del registro "Reinversión".
  2. Calcule el 30% y lo sume al saldo de "Valqui".
  3. Calcule el 30% y lo sume al saldo de "Margarita".
  4. Inserte los 3 movimientos en `Historial_Liquidaciones`.

## 4. Interfaz Frontend (Vue 3)
- En la vista de **Finanzas** (o un nuevo tab llamado `Liquidación de Socias`), mostrar 3 tarjetas grandes con el saldo actual acumulado de Reinversión, Valqui y Margarita.
- Incluir un botón de "Retirar Fondos" en las tarjetas de las socias. Al pulsarlo, se debe abrir un modal para registrar que la socia retiró "X" cantidad de dinero, restándolo de su `saldo_actual` (para reflejar cuando efectivamente se transfieren el dinero a sus cuentas bancarias personales).
- Mostrar una tabla inferior leyendo el `Historial_Liquidaciones` para saber de qué ventas provienen esos centavos.

## 5. Instrucciones para OpenCode
Por favor, implementa este sistema completo. Genera la migración de la base de datos, construye los endpoints de liquidación y retiro, y diseña la vista de saldos en Vue 3. La prioridad es que la transacción de división de ganancias sea robusta y no permita pérdida de centavos por redondeos (utiliza el tipo `Decimal` en Python).