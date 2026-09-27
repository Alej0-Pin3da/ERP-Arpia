# E2E — V4 foundation

Golden paths (Playwright, fuera de `npm test`):

1. Producción: Pedido → fases → cierre con explosión BOM.
2. Comercial: Venta → descuento de stock → margen.
3. Cierre: Liquidación → anticipos → distribución.

Run:

```bash
npx playwright install
npm run test:e2e
```

Requires backend + frontend running (`E2E_BASE_URL`, default `http://localhost:5173`).
