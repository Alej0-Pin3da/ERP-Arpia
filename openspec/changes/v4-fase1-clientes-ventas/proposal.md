# Proposal: v4-fase1-clientes-ventas

## Intent
Migrate Clientes and Ventas from Pinia mock (`src/stores/atelier.ts`) to Postgres, keeping `*.vue` identical. Unblocks CRM and sales.

## Scope
### In Scope
- `Clientes` +10 cols: `ciudad`, `direccion`, `tipo`, `talla_habitual`, `talla_superior`, `talla_inferior`, `categoria_preferida`, `tipo_producto_frecuente`, `notas`, `medidas JSONB` + indices `ix_clientes_tipo`, `ix_clientes_ciudad`
- `Ventas` +`metodo_pago VARCHAR(50)` (or FK) + align `canal_venta` enum; decide FK to `maestros_canales_venta` vs VARCHAR
- Minimal seeds `maestros_canales_venta` + `maestros_metodos_pago` (advanced from Fase 3)
- Expand `ClienteCreate/Update/Read`, `VentaCreate/Read`; `GET /clientes` filters `?tipo=&ciudad=&q=`, ventas validation vs masters
- Frontend `services/api/clientes.ts`, `ventas.ts` + `composables/useClientes.ts` adapter (`VITE_USE_MOCK` switch); reuse `GET /api/__mode` + badge

### Out of Scope
- Socios/Liquidaciones/Anticipos and 5 maestros (`proveedores`, `ubicaciones`, `tallas`, `productos_sin_talla`, `parametros_costeo`) — Fase 2/3
- Insumos/BOM/Prendas/Pedidos — Fase 4
- `*.vue` rewrite or deleting `atelier.ts` (mark `@deprecated` only)

## Capabilities
### New Capabilities
- `clientes-crm`: 10-field CRM, JSONB medidas, ciudad/tipo filters
- `ventas-channel-payment`: `metodo_pago` + `canal_venta` alignment/validation
- `sales-master-data`: minimal canales/metodos-pago seeds

### Modified Capabilities
- None — no existing spec covers clientes/ventas

## Approach
Two Alembics: `0009_extend_clientes_crm`, `0010_fix_ventas_canal_y_metodo_pago` (reversible, nullable). Ship VARCHAR(50); FK follow-up if needed. Expand schemas/handlers, idempotent seeds, adapter per `ERP-V4.md` §8. ~400-500 lines.

## Affected Areas
| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/clientes.py` | Modified | +10 cols, JSONB, indices |
| `backend/app/models/ventas.py` | Modified | +`metodo_pago`, fix `canal_venta` |
| `backend/alembic/versions/0009_*.py` | New | Clientes migration |
| `backend/alembic/versions/0010_*.py` | New | Ventas + seeds |
| `backend/app/schemas/cliente.py`, `venta.py` | Modified | New fields/filters |
| `backend/app/api/routes/clientes.py`, `ventas.py` | Modified | Filters + validation |
| `src/services/api/clientes.ts`, `ventas.ts` | New | API clients |
| `src/composables/useClientes.ts`, `useMode.ts` | New | Adapter |
| `src/stores/atelier.ts` | Modified | `@deprecated` |

## Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `canal_venta` FK vs VARCHAR blocks sales | Med | Ship VARCHAR(50) + canonical seeds; FK later |
| `medidas` JSONB breaks validation | Low | Accept free `dict`, type-check only |
| Migration irreversible | Low | Nullable cols, `downgrade` tested on dev |
| Adapter leaks mock to prod | Low | `isMock` from env + `__mode` badge verify |

## Rollback Plan
`alembic downgrade -2`; redeploy prior backend. Frontend: `VITE_USE_MOCK=true` restores Pinia path instantly. New cols nullable — no data loss.

## Dependencies
- `Clientes` (4 cols), `Ventas.canal_venta` constraint; Alembic + Postgres; `GET /api/__mode` exists

## Success Criteria
- [ ] `psql` shows 10 clientes cols + indices; ventas has `metodo_pago`
- [ ] `POST/PATCH /clientes` with `medidas` JSONB + filters `?tipo=&ciudad=` work
- [ ] `POST /ventas` with `canal_venta` + `metodo_pago` 201; invalid channel 422
- [ ] Seeds present; no manual setup needed
- [ ] UI `VITE_USE_MOCK=false` creates cliente+venta, survives `F5`, network 200
