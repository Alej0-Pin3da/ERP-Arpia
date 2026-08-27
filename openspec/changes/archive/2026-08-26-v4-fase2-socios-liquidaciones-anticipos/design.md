# Design: v4-fase2-socios-liquidaciones-anticipos

## Technical Approach

Three reversible Alembics after 0010: 0011 socios +10 nullable cols, 0012 liquidaciones header+distribucion, 0013 anticipos. SQLAlchemy models + Pydantic Literals + FastAPI CRUD enforce invariants; services handle sum-to-100 incl fondo, payload-as-source drift warning, double-discount lock. Frontend adds 3 `services/api/*` + 2 composables toggling via `useMode`/`client.ts`; `*.vue` intact.

## Architecture Decisions

| Decision | Options | Trade-off | Choice |
|----------|---------|-----------|--------|
| Socios cols | A 8 cols (ERP-V4 §6.3) B 10 (SociaAtelier) | A breaks UI mapping; B nullable additive | **B 10 nullable** `rol,banco,es_fondo_taller,telefono,email,tipo_cuenta,numero_cuenta,titular_cuenta,activo,notas` |
| Liquidaciones shape | A JSONB B header+child | A no FK/unique; B relational + CASCADE | **B** `liquidacion_distribucion` + `UNIQUE(liquidacion_id,socia_id)` |
| Estado enums | A reuse DocumentState B per-domain StrEnum | A leaks states; B isolated map | **B** `LiquidacionEstado`/`AnticipoEstado` |
| Double-discount | A app check B partial idx + FOR UPDATE | A races; B 409 on concurrency | **B** `UNIQUE WHERE liquidacion_id IS NOT NULL` + `SELECT FOR UPDATE` |
| Drift >5% | A reject B warn+persist | A blocks manual fix; B audits | **B** payload source, `warnings[]` |
| Fondo | A separate table B boolean on Socios | A extra join; B same sum-to-100 | **B** `es_fondo_taller`, activo sum includes fondo (40+30+30) |
| Migrations | A 1 combined B 3 isolated | A large rollback; B fits 400-line budget | **B** 0011/12/13 idempotent |

## Data Flow

```
Postgres Socios(+10) ─┬─> liquidaciones (codigo LIQ-YYYY-NN UNIQUE, 6×NUMERIC(12,2), CHECK BORRADOR|APROBADA|PAGADA)
                      ├─> liquidacion_distribucion (FK CASCADE, UNIQUE pair, monto_bruto/deduccion/neto)
                      └─> anticipos (socia FK CASCADE, liquidacion FK SET NULL, CHECK estado, partial UNIQUE)
FastAPI /finanzas ─ schemas(Literal) ─ services(sum-to-100, fondo, drift, FOR UPDATE) ─ Paginated+warnings
Adapter services/api/{socios,liquidaciones,anticipos} ─ composables/useSocios|useFinanzas ─ useMode ? atelier : client ─ *.vue
```

Create liquidacion: validate `ventas-costos=utilidad_neta` else 422 → fetch `activo=true` incl fondo → `bruto=repartible*%/100`, `deduccion=sum PENDIENTE`, `neto=bruto-deduccion` → insert header+rows + UPDATE anticipos→DESCONTADO in one tx with locks.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/alembic/versions/0011_extend_socios_configuracion.py` | Create | 10 cols + 2 indexes + guards |
| `backend/alembic/versions/0012_create_liquidaciones.py` | Create | header + child + CHECKs + FKs + indexes |
| `backend/alembic/versions/0013_create_anticipos.py` | Create | table + CHECK + `ix_anticipos_socia_fecha` + partial unique |
| `backend/app/models/finanzas.py` | Modify | Extend Socios + 3 models + 2 enums |
| `backend/app/schemas/finanzas.py` | Modify | Create/Update/Read Literals + validators |
| `backend/app/api/routes/finanzas.py` | Modify | CRUD + PATCH /state + descuento |
| `backend/app/services/finanzas.py` | Modify | sum-to-100, fondo, drift, lock |
| `src/services/api/socios.ts` | Create | CRUD via client.ts |
| `src/services/api/liquidaciones.ts` | Create | CRUD + transition |
| `src/services/api/anticipos.ts` | Create | CRUD + descuento |
| `src/composables/useSocios.ts` | Create | isMock toggle |
| `src/composables/useFinanzas.ts` | Create | isMock toggle |
| `src/stores/atelier.ts` | Modify | @deprecated header only |

## Interfaces / Contracts

```python
# models
class LiquidacionEstado(StrEnum): BORRADOR, APROBADA, PAGADA
class AnticipoEstado(StrEnum): PENDIENTE_DESCUENTO, DESCONTADO, ANULADO
class Liquidacion(Base): codigo VARCHAR(12) UNIQUE; periodo VARCHAR(20); fecha_cierre DATE
  6×NUMERIC(12,2) totals; estado CHECK DEFAULT BORRADOR; timestamps
class LiquidacionDistribucion(Base): liquidacion_id FK CASCADE; socia_id FK CASCADE
  porcentaje NUMERIC(5,2); monto_bruto/deduccion/monto_neto NUMERIC(12,2); estado_pago CHECK
  __table_args__=(UniqueConstraint(liquidacion_id,socia_id),)
class Anticipo(Base): socia_id FK CASCADE NOT NULL; liquidacion_id FK SET NULL
  monto NUMERIC(12,2) CHECK>0; estado CHECK; Index(socia_id,fecha); partial UNIQUE WHERE liquidacion_id IS NOT NULL
# schemas
class SociaCreate(BaseModel): nombre:str[1,150]; porcentaje:Decimal>0; rol:str|None≤50; email:EmailStr|None
  tipo_cuenta:Literal["AHORROS","CORRIENTE","OTRA"]|None; es_fondo_taller:bool=False; activo:bool=True
class LiquidacionCreate(BaseModel): periodo:str; fecha_cierre:date; totals:6×Decimal; obs:str|None
class LiquidacionRead(BaseModel): codigo:str; estado:Literal[...]; distribucion:list[DistRead]; warnings:list[str]
```

```typescript
listSocios(p:{activo?,es_fondo_taller?,rol?,q?,limit?,offset?}):Paginated<SociaRead>
createLiquidacion(p):LiquidacionRead // server LIQ-YYYY-NN
transitionLiquidacion(id,{estado}):LiquidacionRead // BORRADOR→APROBADA→PAGADA only else 422
descontarAnticipo(id,{liquidacion_id}):AnticipoRead // PENDIENTE→DESCONTADO atomically else 409
useSocios():{list,get,create,update,remove,isMock}
useFinanzas():{liquidaciones,anticipos,isMock}
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | email/tipo_cuenta validators, Literals, 10→8 drift | pytest schemas |
| Integration | sum 40+30+30→105=422, second fondo 422, inactive excluded, filters composable; liq 3 rows LIQ-YYYY-NN, dup 409, FSM 422 terminal, drift warn persists, anticipo net; anticipo >0 422, socia 404, double-discount 409, SET NULL, FOR UPDATE 1×201/1×409 | Postgres docker pytest |
| Frontend | isMock→atelier vs /api/v1, badge __mode | Vitest jsdom |
| E2E | FinanzasView BORRADOR→PAGADA + descuentos, F5 persists | manual |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR or executable boundary. Pure DB + typed HTTP via `client.ts`.

## Migration / Rollout

Upgrade: 0010→0011 nullable adds →0012 header+child `codigo` UNIQUE →0013 `ix_anticipos_socia_fecha`+partial unique; guards `_has_column/_has_table/_has_index`; downgrade reverse; `downgrade -1` atomic. Rollback `VITE_USE_MOCK=true` instant; no data loss.

## Open Questions

- [ ] `rol` free VARCHAR(50) vs enum Fase 3?
- [ ] LIQ-YYYY-NN MAX+1 vs advisory lock concurrency?
- [ ] `tipo_cuenta` SHOULD-only validation confirmed?
