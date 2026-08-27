# Proposal: v4-fase3-maestros

## Intent
Replace 8 mocked maestros (`atelier.ts` + stub) with Postgres. `MaestrosView.vue` 7 tabs (tallas merges 2 entities) needs 8 catalogs + singleton `ParametrosCosteo` 40/30/30. Via `useMaestros`/`isMock`, view intact.

## Scope

### In Scope
- 8 tables: 6 new (`maestros_proveedores`, `categoria_coleccion`, `ubicacion_taller`, `tallas_estandar`, `producto_sin_talla`, `parametros_costeo` singleton) + extend 0010 stubs (`canales_venta`/`metodos_pago` via `ALTER`)
- Paginated CRUD `GET /maestros/*` (`limit/offset/q/tipo/activo/sort_by/order`), `POST 201`/`PATCH`/`DELETE`, singleton `GET/PATCH /parametros-costeo`
- `Talla` flat (`talla`+`orden` UNIQUE, free strings); `Parametros` sum 40/30/30 + `FOR UPDATE`
- `maestros.ts` 8 clients + `useMaestros.ts` + `seeder.py` seeds

### Out of Scope
- `*.vue` rewrites, WAC/BOM, `atelier.ts` deletion (Fase5), re-creating 0008 `Proveedores`, FKs from `Ventas`/`Insumo`

## Capabilities

### New Capabilities
- `maestros-proveedores`: free `categoria`, `calificacion 0-5`
- `maestros-categorias-coleccion`: `tipo_talla` enum 3 values
- `maestros-ubicaciones-taller`: `codigo UB-* UNIQUE`, `tipo` 4 values
- `maestros-tallas-estandar`: flat, `orden UNIQUE`
- `maestros-productos-sin-talla`: `precio_sugerido NUMERIC(15,4)`
- `maestros-parametros-costeo`: singleton 40/30/30

### Modified Capabilities
- `ventas-channel-payment`: extend 0010 stubs (`tipo/comision_pct/costo_fijo/activo/descripcion`) nullable `ALTER`, keep CK

## Approach
Sliced > monolithic (660 lines >400). **0014 core** (proveedores, categorias, ubicaciones, extend 2 stubs, parametros singleton) + **0015 tallas** (tallas + sin-talla). Each <400, `_has_*` guards, `CHECK` enums / free `VARCHAR` categorias, `NUMERIC(15,4)`/`TIMESTAMPTZ`, reuse `Paginated`/`aplicar_orden`/`useMode`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/alembic/versions/0014_*.py` | New | Core 4 + extend 2 |
| `backend/alembic/versions/0015_*.py` | New | Tallas + sin-talla |
| `backend/app/models/maestros.py` | New | 8 models, CHECK/UNIQUE |
| `backend/app/schemas/maestros.py` | New | Create/Update/Read |
| `backend/app/services/maestros.py` | New | Sum guard + `FOR UPDATE` |
| `backend/app/api/routes/maestros.py` | New | CRUD + singleton |
| `src/services/api/maestros.ts` | Modified | Stub → 8 clients |
| `src/composables/useMaestros.ts` | New | `isMock ? atelier : api` |
| `src/stores/atelier.ts` | — | `@deprecated` fallback kept |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 0010 collision | High | `_has_column`, nullable, drops cols only |
| Proveedor vs 0008 | Med | `maestros_proveedores` decoupled |
| Talla dup | Med | `UNIQUE` both, `MAX(orden)+1`, 409 |
| Singleton race | Med | `FOR UPDATE`, 422 if sum!=100 |
| Budget exceed | Med | Sliced ~350+310 |

## Rollback Plan
`downgrade -1` per slice (drops cols not table). `VITE_USE_MOCK=true` fallback. No data loss.

## Dependencies
Head `0013`; stack from `feat/v4-fase2-pr3-integration`. FastAPI 0.115.6, Postgres 16.

## Success Criteria
- [ ] 8 tables CHECK/UNIQUE/Index; stubs extended
- [ ] `GET /maestros/*` Paginated; `POST` 201; dup →409; bad `tipo` →422
- [ ] `PATCH /parametros-costeo` 40/30/30 sum=100 else 422
- [ ] `MaestrosView.vue` 7 tabs CRUD + `F5` OK, no layout change
- [ ] `pytest` + `vitest` green

## Proposal question round
Confirm decoupled proveedores, Talla strings, Parametros overwrite, sliced 0014/0015.
