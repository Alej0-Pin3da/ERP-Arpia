# ERP Arpia — Manual Testing Checklist (Phase 1 + Phase 2)

Scope: verify everything built in **Phase 1** (backend scaffold, auth, CRUD base entities, users)
and **Phase 2** (WAC purchase engine + compras-insumos routes).

Test against the local backend (Docker Postgres on port **5433**). API base: **`http://localhost:8000/api/v1`**
Interactive docs (Swagger): `http://localhost:8000/api/v1/docs` or `/redoc`.

---

## 0. Prerequisites

- [ ] Backend running: from `backend/`, run the FastAPI app (venv active)
- [ ] DB up: `docker compose up -d db` (Postgres on `localhost:5433`, healthy)
- [ ] Migrations applied (Alembic) — tables exist
- [ ] Seed admin present: **admin@arpia.com / Admin123!** (rol `admin`)
- [ ] You can reach `GET /api/v1/auth/me` flow described below (proves app is up)

### Roles used in this guide

| Rol | Can do |
|---|---|
| `admin` | everything (CRUD + create purchases) |
| `operador` | read + create purchases (NOT admin-only writes like create user) |
| `consulta` | read-only (GET), NO POST purchases |

---

## 1. Auth (Phase 1)

### 1.1 Login
`POST /auth/login`
```json
{ "email": "admin@arpia.com", "password": "Admin123!" }
```
- [ ] Returns `200` with `access_token`, `refresh_token`, `token_type: "bearer"`, `rol: "admin"`
- [ ] Wrong password / unknown email returns `401` (detail `Incorrect email or password`)

### 1.2 Get current user
`GET /auth/me` — Header: `Authorization: Bearer <access_token>`
- [ ] Returns `200` with your user (`id`, `nombre`, `email`, `rol`)
- [ ] No token / invalid token returns `401`

### 1.3 Refresh token (rotation)
`POST /auth/refresh`
```json
{ "refresh_token": "<refresh_token from login>" }
```
- [ ] Returns `200` with a NEW pair (access + refresh)
- [ ] Reusing the SAME refresh token again returns `401` (`Refresh token already revoked`)
- [ ] Bonus security check: after reuse, other active refresh tokens for that user are also revoked (rotation contains compromise)

### 1.4 Logout
`POST /auth/logout` with a refresh token body
- [ ] Returns `204`; using that refresh token afterwards returns `401`

---

## 2. Proveedores (Phase 1) — ELIMINADO (2026-08)

> ⚠️ **Entidad eliminada** (decisión de negocio 2026-08): el endpoint `/proveedores` ya no existe
> en la API y la tabla `Proveedores` fue removida del esquema. Los casos CRUD de esta sección
> (`POST/GET/PUT/DELETE /proveedores`) quedaron **obsoletos** — no probar.

## 3. Categorías de Insumos (Phase 1)

Same role pattern as the other base entities.

- [ ] `POST /categorias-insumos` (admin) → `201`
```json
{ "nombre": "Telas" }
```
- [ ] `GET /categorias-insumos` → `200` (list)
- [ ] `GET /categorias-insumos/{id}` → `200`; unknown → `404`
- [ ] `PUT /categorias-insumos/{id}` → `200`
- [ ] `DELETE /categorias-insumos/{id}` → `204`
- [ ] `POST` as `consulta` → `403`

## 4. Insumos (Phase 1)

Create a category first (keep its `id`; example uses `1`).

- [ ] `POST /insumos` (admin) → `201`
```json
{
  "categoria_id": 1,
  "nombre": "Tela Algodón",
  "unidad_medida": "m",
  "stock_actual": 0,
  "stock_minimo": 5,
  "costo_promedio_actual": 0
}
```
- [ ] Response includes `nombre_categoria` (e.g. `"Telas"`) and all Decimal fields
- [ ] `POST /insumos` with a **nonexistent** `categoria_id` → `400` (`Categoria does not exist`)
- [ ] `GET /insumos` → `200` list; `GET /insumos/{id}` → `200`; unknown → `404`
- [ ] `PUT /insumos/{id}` → `200` (change `nombre`/`stock_minimo`)
- [ ] `DELETE /insumos/{id}` → `204`
- [ ] `POST` as `consulta` → `403`

## 5. Clientes (Phase 1)

- [ ] `POST /clientes` (admin) → `201`
```json
{ "nombre": "Cliente A", "documento_identidad": "30111222", "email": "a@mail.com", "telefono": "11-5555" }
```
- [ ] `GET /clientes` → `200` (list, includes `created_at`)
- [ ] `GET /clientes/{id}` → `200`; unknown → `404`
- [ ] `PUT /clientes/{id}` → `200`
- [ ] `DELETE /clientes/{id}` → `204`
- [ ] `POST` as `consulta` → `403`

## 6. Usuarios (Phase 1 — admin only)

- [ ] `GET /usuarios` (admin) → `200` list
- [ ] `POST /usuarios` (admin) → `201`
```json
{ "nombre": "Operador Uno", "email": "operador@arpia.com", "password": "Operador123!", "rol": "operador" }
```
- [ ] Duplicate email → `400` (`Email already registered`)
- [ ] Invalid rol (e.g. `"superadmin"`) → `422` (validation)
- [ ] `PATCH /usuarios/{id}` (admin) → `200` (change `nombre`, `password`, `rol`)
- [ ] Trying to change **your own** rol away from `admin` → `400` (`Cannot change your own role away from admin`)
- [ ] `DELETE /usuarios/{id}` → `204`; deleting your own user → `400`
- [ ] Non-admin (`operador`/`consulta`) on any `/usuarios` → `403`

---

## 7. Compras de Insumos + WAC (Phase 2)

**WAC formula**: `nuevo_costo = (stock_actual * costo_actual + cantidad * precio_unitario) / (stock_actual + cantidad)`
Computed in Decimal **without rounding**; stored in `NUMERIC(15,4)`.

Permissions:
- `POST /compras-insumos` → `admin` OR `operador` (`consulta` → **403**)
- `GET /compras-insumos` → any authenticated role

### 7.1 Create a purchase (WAC happy path)
Setup: insumo with `stock_actual=0`, `costo_promedio_actual=0`, id `1` (or your created one).

1. `POST /compras-insumos` (admin) → `201`
```json
{ "insumo_id": 1, "cantidad_comprada": 10, "precio_unitario_compra": 5 }
```
- [ ] Returns `201` with `id`, `insumo_id`, `fecha_compra`, `cantidad_comprada`, `precio_unitario_compra`
- [ ] After: `GET /insumos/1` shows `stock_actual: 10`, `costo_promedio_actual: 5`

2. `POST /compras-insumos` again, price 7:
```json
{ "insumo_id": 1, "cantidad_comprada": 10, "precio_unitario_compra": 7 }
```
- [ ] New cost = `(10*5 + 10*7)/(10+10) = 120/20 = 6` → `GET /insumos/1` shows `costo_promedio_actual: 6`, `stock_actual: 20`

3. `POST` third lot, price 8, qty 20:
- [ ] New cost = `(20*6 + 20*8)/(20+20) = 280/40 = 7` → `costo_promedio_actual: 7`, `stock_actual: 40`

### 7.2 Purchase without proveedor — OBSOLETO (2026-08)
> ⚠️ El campo `proveedor_id` fue **eliminado en 2026-08** junto con la entidad `Proveedores`;
> las compras ya no lo aceptan ni lo devuelven. Este caso de prueba quedó obsoleto.

### 7.3 Error cases
- [ ] `insumo_id` nonexistent → `404` (`Insumo not found`)
- [ ] `cantidad_comprada: 0` or negative → `422` (validation)
- [ ] `precio_unitario_compra: -1` → `422`
- [ ] No token → `401`
- [ ] As `consulta` → `403`

### 7.4 List / pagination / filter
- [ ] `GET /compras-insumos` → `200` list ordered by `id` ascending
- [ ] `GET /compras-insumos?limit=2&offset=2` → `200`, returns the 3rd and 4th records (2 at a time)
- [ ] `GET /compras-insumos?insumo_id=1` → `200`, only records of that insumo
- [ ] `GET /compras-insumos` as `consulta` → `200` (read allowed)

### 7.5 Concurrency (advanced)
- [ ] Optional: fire two purchases for the **same** insumo at the same time (e.g. two curl/PowerShell jobs).
  Because `SELECT ... FOR UPDATE` serializes on the row lock, the final `stock_actual` must equal
  the sum of both quantities and the final `costo_promedio_actual` must match the formula on the combined
  state (no lost update).

---

## 8. Test suite (automated)

- [ ] From repo root: `python -m pytest backend/tests -q` → expect **53 passed**
- [ ] Run it a second time → stable 53

---

## Summary of what's covered

| Area | Phase | Status |
|---|---|---|
| Auth (login/me/refresh/logout) | 1 | ✅ built |
| Categorías insumos CRUD | 1 | ✅ built |
| Insumos CRUD | 1 | ✅ built |
| Clientes CRUD | 1 | ✅ built |
| Usuarios CRUD (admin) | 1 | ✅ built |
| Compras insumos + WAC | 2 | ✅ built (PR #1/#2) |
| Automated suite | 1+2 | ✅ 53 passed |
