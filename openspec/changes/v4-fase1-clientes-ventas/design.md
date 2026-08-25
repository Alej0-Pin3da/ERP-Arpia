# Design: v4-fase1-clientes-ventas

## Technical Approach

Two reversible Alembics (`0009` clientes, `0010` ventas+seeds) extend Postgres, Pydantic schemas enforce canonical enums/dict validation, routes add filters. Frontend adapter (`services/api/*` + `composables/use*` + `useMode`) toggles `VITE_USE_MOCK` between `stores/atelier.ts` and real API, reusing `client.ts` and `GET /api/__mode`. Ships `VARCHAR(50)` whitelist; FK deferred. `*.vue` intact per ERP-V4 §8.

## Architecture Decisions

| Decision | Options | Trade-off | Choice |
|----------|---------|-----------|--------|
| Ventas validation | A VARCHAR(50)+whitelist B FK to maestros | A ships now, no blocking; B strong guarantee but seeds ordering risk | **A** — whitelist + seeds as source for dropdowns, FK in Fase 3 |
| Migration split | A 1 migration B 2 | A fewer files, big rollback; B isolated revert + 400-line budget fit | **B: 0009 clientes, 0010 ventas+seeds**, nullable + downgrade |
| medidas | A JSONB dict B columns | A flexible, zero churn; B rigid, typed | **A JSONB dict**, 422 on non-object, NULL if absent |
| Frontend boundary | A rewrite *.vue B adapter composables | A large diff, breaks contract; B ≤100 lines, toggle-safe | **B adapter** |
| Seeds | A Alembic bulk_insert B seeder.py only | A runs on upgrade, zero manual; B needs manual run | **A in 0010 + mirror in seeder.py**, idempotent |

## Data Flow

```
Postgres (Clientes +10 JSONB, Ventas metodo_pago + canal VARCHAR(50))
  │
  ▼
FastAPI /api/v1 — schemas (Cliente/Venta) — routes (clientes/ventas)
  │  Literal enums + ILIKE filters → Paginated
  ▼
Adapter: services/api/{clientes,ventas,maestros}.ts → composables/{useClientes,useVentas,useMode}.ts
  │  VITE_USE_MOCK ? atelier.ts : client.ts (/api/v1)
  ▼
*.vue intact — ApiModeBadge ← GET /api/__mode (real|mock)
```

`GET /clientes?tipo=&ciudad=&q=` → exact `tipo/ciudad` + `ilike(nombre|ciudad|direccion)`. `POST /ventas {canal_venta,metodo_pago}` → Literal check + optional masters whitelist → persist.

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/alembic/versions/0009_extend_clientes_crm.py` | Create | 10 nullable cols + ix_clientes_tipo/ciudad + legacy canal map |
| `backend/alembic/versions/0010_fix_ventas_canal_y_metodo_pago.py` | Create | metodo_pago VARCHAR(50) NULL, canal VARCHAR(50) + CK 5 valores + 5+4 seeds |
| `backend/app/models/clientes.py` | Modify | 10 cols + medidas JSONB + indices |
| `backend/app/models/ventas.py` | Modify | metodo_pago, canal String(50), CK showroom_pereira, legacy mapper |
| `backend/app/schemas/cliente.py` | Modify | +10 fields, medidas dict validator |
| `backend/app/schemas/venta.py` | Modify | canal Literal 5, metodo_pago Literal\|None |
| `backend/app/api/routes/clientes.py` | Modify | tipo/ciudad/q filters (ILIKЕ) |
| `backend/app/api/routes/ventas.py` | Modify | canal/metodo_pago validation |
| `backend/app/seeder.py` | Modify | idempotent channel/payment seeds |
| `src/services/api/clientes.ts` | Create | CRUD via client.ts |
| `src/services/api/ventas.ts` | Create | CRUD |
| `src/services/api/maestros.ts` | Create | listCanales/listMetodosPago |
| `src/composables/useMode.ts` | Create | isMock + /api/__mode probe |
| `src/composables/useClientes.ts` | Create | mock↔api switch |
| `src/composables/useVentas.ts` | Create | mock↔api switch |
| `src/stores/atelier.ts` | Modify | @deprecated header only |

## Interfaces / Contracts

```python
# schemas/cliente.py — 10 new fields
class ClienteCreate(ClienteBase):
    ciudad: str | None = Field(max_length=80, default=None)
    direccion: str | None = Field(max_length=200, default=None)
    tipo: str | None = Field(max_length=30, default=None)
    talla_habitual: str | None = Field(max_length=10, default=None)
    talla_superior: str | None = Field(max_length=10, default=None)
    talla_inferior: str | None = Field(max_length=10, default=None)
    categoria_preferida: str | None = Field(max_length=50, default=None)
    tipo_producto_frecuente: str | None = Field(max_length=50, default=None)
    notas: str | None = None
    medidas: dict | None = None  # 422 if not dict

# schemas/venta.py
CANAL = Literal["web","whatsapp","instagram","feria","showroom_pereira"]
METODO = Literal["efectivo","transferencia","tarjeta","contraentrega"]
class VentaCreate(BaseModel):
    canal_venta: CANAL
    metodo_pago: METODO | None = None
```

```typescript
// services/api/clientes.ts + composables/useClientes.ts
listClientes(p:{q?,tipo?,ciudad?,limit?,offset?}):Promise<Paginated<ClienteRead>>
useClientes(): { list,get,create,update,remove, isMock } // atelier if mock else api
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | medidas non-dict 422, canal/metodo 422 | pytest schemas |
| Integration | POST/GET clientes round-trip, ?tipo+ciudad+q combinable, ventas 201/422, upgrade/downgrade reversible | real Postgres docker |
| Frontend | VITE_USE_MOCK true→atelier, false→/api/v1; badge via /api/__mode | Vitest jsdom, mock client.ts |
| E2E manual | create cliente+venta, F5 persists, 200 | proposal success criteria |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, or executable classification. Pure DB + typed HTTP via existing client.ts.

## Migration / Rollout

- `alembic upgrade head`: 0009 nullable cols (zero downtime) → 0010 widen canal + add metodo_pago + seeds (SELECT-before-insert). Legacy map: `Feria Showroom`→`feria`, `WhatsApp / DM`→`whatsapp`, `Showroom Pereira`→`showroom_pereira`.
- `downgrade -2` restores CK `web|whatsapp|instagram|feria`, drops cols/indices/seeds. Nullable → no data loss. Frontend fallback `VITE_USE_MOCK=true` instant. `seeder.py` mirrors seeds for fresh DBs.

## Open Questions

- [ ] Final clave `showroom_pereira` vs `showroom` — confirm with business.
- [ ] `tipo` free VARCHAR(30) vs closed enum in Fase 3?
- [ ] FK hardening Fase 3 or keep VARCHAR whitelist long-term?
