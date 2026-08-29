# Spec: testing-frontend-vitest

## Scenarios

### 1. VentasView
- Renderiza lista, crea venta, maneja error 409 stock, usa clientes reales del API

### 2. Inventario/Insumos
- Lista insumos, crea/edita, validación campos requeridos

### 3. Finanzas
- Lista movimientos y liquidaciones, estados

### 4. Auth
- Login success/failure, guarda token, redirect

### 5. Composables
- useMode respeta VITE_USE_MOCK
- useClientes/useVentas delegan a api o atelier según modo

### 6. Services API
- client baseURL, interceptors auth, error handling

## Requirements
- Vitest + @vue/test-utils + happy-dom/jsdom
- MSW o vi.mock para fetch/axios
- Coverage threshold inicial 60% sobre archivos testeados
