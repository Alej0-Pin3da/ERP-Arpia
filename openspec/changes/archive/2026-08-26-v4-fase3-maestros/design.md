# Design: v4-fase3-maestros

## Technical Approach

8 mocked maestros → Postgres `GET /api/v1/maestros/*` Paginated CRUD. One `maestros.ts` + `useMaestros.ts` (`isMock ? atelier : api`) keeps `MaestrosView.vue` 7 tabs intact; only `guardar*/eliminar*` branch. Sliced 0014/0015 <400 lines each. Reuses `Paginated`/`aplicar_orden`/`paginar`/`useMode`.

## Architecture Decisions

| Decision | Options | Tradeoff | Choice |
|----------|---------|----------|--------|
| Slice | Monolithic vs 0014/0015 | Monolithic >400 | **Sliced**: 0014 3+2 ALTERs + 0015 2+singleton. <400 each, reversible. |
| Types | TEXT vs VARCHAR(n) | TEXT no guard | **VARCHAR(100)/50/20**, TEXT only for notas. |
| Enums | CHECK vs free vs PG ENUM | PG ENUM hard to migrate | **CHECK closed sets** (3/4/4/3 values). **Free VARCHAR** for open categoria. |
| Money | 15,4 vs 12,2 | 12,2 drifts | **NUMERIC(15,4)** + ge/le. |
| Talla | Flat vs JSONB | JSONB breaks sort | **Flat**: `talla+orden UNIQUE`, medida strings `VARCHAR(50)`. |
| Proveedor | Recreate vs new | Collides with 0008 | **New `maestros_proveedores`**, no FK. |
| API shape | One vs 8 files | Duplicates tryFetch | **One `maestros.ts`** 8 clients, keeps fallback. |
| Singleton | App check vs FOR UPDATE | Races | **`FOR UPDATE` id=1** sum==100 else 422. |

## Data Flow

```
Postgres 8 tables ──► FastAPI /maestros/* (Paginated+aplicar_orden/paginar+require_roles) ──► maestros.ts (8 clients)
        │ 200/201/409/422                                                               │
        └────► useMaestros.ts (isMock via useMode) ── isMock? atelier : api ──► MaestrosView.vue 7 tabs
                singleton: GET auto-creates id=1; PATCH FOR UPDATE → validate sum 100 → 200 else 422
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `backend/alembic/versions/0014_*.py` | Create | 3 CREATE + 2 ALTER with `_has_*` guards; ON CONFLICT seeds; downgrade drops cols only |
| `backend/alembic/versions/0015_*.py` | Create | `tallas_estandar`+`producto_sin_talla`+`parametros` singleton 40/30/30; downgrade DROP 3 |
| `backend/app/models/maestros.py` | Create | 8 models, CHECK/UNIQUE/Index, 15,4, TIMESTAMPTZ |
| `backend/app/models/__init__.py` | Modify | Export 8 models |
| `backend/app/schemas/maestros.py` | Create | Create/Update/Read per catalog, singleton partial |
| `backend/app/services/maestros.py` | Create | `get_or_create` + `patch FOR UPDATE` sum 100 |
| `backend/app/api/routes/maestros.py` | Create | `prefix="/maestros"` 7× list + POST/PATCH/DELETE + singleton; 409 mapping |
| `backend/app/main.py` | Modify | Register router |
| `backend/app/seeder.py` | Modify | ON CONFLICT seeds 8 tables |
| `src/services/api/maestros.ts` | Modify | 53→~250 lines, 8 clients |
| `src/composables/useMaestros.ts` | Create | `isMock?atelier:api` adapter |
| `src/views/MaestrosView.vue` | Modify | Wire guardar*/eliminar* ~40 lines |
| `backend/tests/test_maestros_*.py` | Create | pytest per table + race |
| `src/composables/useMaestros.test.ts` | Create | Vitest isMock toggle |

## Interfaces / Contracts

```python
class ProveedorMaestro(Base):  # UNIQUE(nombre), CHECK 0-5
    __tablename__ = "maestros_proveedores"
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    categoria: Mapped[str] = mapped_column(String(100))  # free
    calificacion: Mapped[Decimal | None] = mapped_column(Numeric(3,1))

class ProveedorCreate(BaseModel):
    nombre: str = Field(max_length=100); categoria: str = Field(max_length=100)
    calificacion: Decimal | None = Field(default=None, ge=0, le=5)
    email: EmailStr | None = None
# GET /maestros/proveedores → Paginated; dup 409 bad tipo 422
# GET /parametros-costeo auto-create; PATCH sum!=100 422 FOR UPDATE
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit pytest | CRUD 201, dup 409, enum 422, bounds 422, filters q/tipo/activo + sort orden + total | Real Postgres Docker, TestClient per table |
| Integration | Singleton auto-create, PATCH sum 100→200 else 422, concurrent PATCH FOR UPDATE serializes | ThreadPoolExecutor 2× PATCH, assert no lost update |
| Frontend vitest | isMock branches, tryFetch fallback, F5 persist | jsdom mock useMode, spy client.get |

## Threat Matrix

N/A — no routing/shell/subprocess/VCS. Typed HTTP JSON only. No RED tests.

## Migration / Rollout

Branch from `feat/v4-fase2-pr3-integration` head 0013. `_has_*` guards + nullable ALTER + `ON CONFLICT` seeds. Downgrade 0015 DROP 3; 0014 DROP cols + DROP 3 (stubs kept). `VITE_USE_MOCK=true` fallback. Verify: `alembic upgrade head && pytest -q -k maestros`.

## Open Questions

- [ ] `Insumo.ubicacion` FK to ubicaciones or free text? → free text for Fase 3.
- [ ] `Ventas.canal_venta` FK to canales or CK? → keep CK, FK later.
- [ ] Talla `orden` gaps after delete? → allow gaps (UNIQUE only).
- [ ] `total_modelos` manual vs BOM trigger? → manual.
