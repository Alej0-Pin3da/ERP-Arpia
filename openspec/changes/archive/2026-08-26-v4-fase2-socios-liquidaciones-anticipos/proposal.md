# Proposal: v4-fase2-socios-liquidaciones-anticipos

## Intent
Replace mocked socias/liquidaciones/anticipos (`atelier.ts`) with Postgres. Socios has 3 cols (needs ~8); liquidaciones/anticipos have no tables. FinanzasView expects SociaAtelier 11 fields, Liquidacion header+distribucion[], Anticipo state machines. Principle: Misma UI, datos reales. Refs: ERP-V4 §§4.3,5,6.3-6.5; explore.

## Scope

### In Scope
- Extend Socios to match SociaAtelier
- Create liquidaciones header + liquidacion_distribucion child
- Create anticipos (socia_id CASCADE, liquidacion_id SET NULL)
- Real CRUD /finanzas/liquidaciones + /finanzas/anticipos
- Adapters socios|liquidaciones|anticipos.ts + composables

### Out of Scope
- *.vue rewrites; atelier.ts deletion (Fase5)
- Maestros Fase3, insumos/recetas Fase4, USE_MOCK switch Fase5
- Re-creating Proveedores (removed 0008)

## Capabilities

### New Capabilities
- `finanzas-socios`: extended profile, es_fondo_taller, sum-to-100 incl. fondo
- `finanzas-liquidaciones`: header+items, BORRADOR|APROBADA|PAGADA
- `finanzas-anticipos`: PENDIENTE_DESCUENTO|DESCONTADO|ANULADO, discount link

### Modified Capabilities
- `finanzas-socios` modifies existing finanzas/socios (nombre+porcentaje only)

## Approach
- **3 migrations 0011-0013 > 1 combined**: atomic rollback, fits 400-line budget, idempotent guards, chain after 0010.
- **Socios (resolved)**: Spec says 8 (rol/banco+6 TBD) but atelier needs 10. Resolve 10 nullable: rol,banco,es_fondo_taller,telefono,email,tipo_cuenta,numero_cuenta,titular_cuenta,activo,notas. estado/fecha_alta deferred.
- **Liquidaciones**: header (codigo LIQ-YYYY-NN unique, periodo, fecha_cierre, 6 totals, estado CHECK) + `liquidacion_distribucion` (FKs CASCADE, monto_bruto/deduccion/monto_neto, estado_pago). No JSONB.
- **Anticipos**: socia_id CASCADE, liquidacion_id SET NULL, monto>0, estado CHECK. Partial unique index + SELECT FOR UPDATE.
- **Enums**: VARCHAR CHECK + StrEnum + transition map (DocumentState pattern).
- **monto_total**: Payload is source; warn >5% vs movimientos periodo sum.
- **Fondo**: es_fondo_taller IS a socia; sum-to-100 includes fondo (40+30+30), validate activo only.

Rejected: Socios_Detalle, single migration, M:N bridge, reuse DocumentState.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/app/models/finanzas.py` | Modified | Extend Socios, add 3 models |
| `backend/alembic/versions/0011-0013` | New | 3 migrations |
| `backend/app/{schemas,api,services}/finanzas.py` | Modified | Schemas + CRUD + invariants |
| `src/services/api/*` + `composables/*` | New | 3 services + 2 composables |
| `backend/tests/test_finanzas*.py` | Modified | New tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 10 cols vs spec 8 | Low | Nullable additive |
| monto_total drift | Med | Warn >5% |
| Double-discount race | Med | Partial index + row lock |
| Fondo sum confusion | Low | Enforce over activo incl. fondo |

## Rollback Plan
Reversible migrations (downgrade -1). Frontend VITE_USE_MOCK=true reverts to Pinia.

## Dependencies
Fase1 0010 applied; existing stack.

## Success Criteria
- [ ] Socios new nullable cols, rows intact
- [ ] liquidaciones + distribucion + anticipos with FKs/CHECKs
- [ ] POST liquidacion creates LIQ-YYYY-NN 40/30/30, anticipos deducted
- [ ] `BORRADOR→APROBADA→PAGADA` only; invalid→422
- [ ] SET NULL on delete; double-discount→409; sum-to-100→422
- [ ] FinanzasView via real API, no layout change
- [ ] pytest green
