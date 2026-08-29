# Spec: purge-frontend-mock

## Scenarios
1. InventarioView en REAL: "Insumos en Alerta" cuenta = insumos con stock < minimo (de API), no atelier hardcodeado
2. Dashboard en REAL: no muestra alertas fantasma; si DB vacía → "Sin alertas"
3. AppLayout badge solo muestra alertas reales en REAL
4. Todos los modales en REAL operan contra API, no atelier.crear*

## Requirements
- Cada uso de atelier en .vue debe estar guardado tras `if (isMock.value)`
- Alternativa real definida (api service o derivado de lista real)
