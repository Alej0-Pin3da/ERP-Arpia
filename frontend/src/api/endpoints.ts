/**
 * Typed endpoint helpers (task 1.3).
 *
 * The generated `src/types/api.d.ts` (openapi-typescript, prod OpenAPI) is the
 * single source of truth for payloads; this module is a thin, typed wrapper
 * over the shared axios instance. Paths here omit the `/api/v1` prefix because
 * the client's baseURL already carries it.
 *
 * Regenerate with: `npm run gen:api` (see package.json).
 */
import type { paths, components } from '@/types/api.d'
import type { TokenResponse } from './types'
import { client } from './client'

// --- type helpers over the generated schema --------------------------------

type HttpMethod = 'get' | 'post' | 'put' | 'patch' | 'delete'
type Op<Path extends keyof paths, Method extends HttpMethod> = paths[Path][Method]
type ReqBody<Path extends keyof paths, Method extends 'post' | 'put' | 'patch'> =
  NonNullable<NonNullable<Op<Path, Method>>['requestBody']> extends { content: { 'application/json': infer T } }
    ? T
    : never
/** 2xx success body (200 or 201; 204/absent resolves to void). */
type Res<Path extends keyof paths, Method extends HttpMethod> =
  Op<Path, Method> extends { responses: { 200: { content: { 'application/json': infer T } } } }
    ? T
    : Op<Path, Method> extends { responses: { 201: { content: { 'application/json': infer T2 } } } }
      ? T2
      : void
type Query<Path extends keyof paths, Method extends 'get'> =
  NonNullable<NonNullable<Op<Path, Method>>['parameters']> extends { query: infer T } ? T : never
type PathParams<Path extends keyof paths, Method extends HttpMethod> =
  NonNullable<NonNullable<Op<Path, Method>>['parameters']> extends { path: infer T } ? T : never

type VentasMensualesRow = components['schemas']['VentasMensualesRead']
type InsumoBajoStock = components['schemas']['InsumoBajoStockRead']
type MargenProducto = components['schemas']['MargenProductoRead']
type TopProducto = components['schemas']['TopProductoRead']
type TopInsumo = components['schemas']['TopInsumoRead']
type FinanzasMensualesRow = components['schemas']['FinanzasMensualesRead']
type CostoProduccion = components['schemas']['CostoProduccionRead']

// --- auth -------------------------------------------------------------------

export const authApi = {
  /** POST /auth/login — returns the token pair + rol. */
  login(body: ReqBody<'/api/v1/auth/login', 'post'>): Promise<TokenResponse> {
    return client.post('/auth/login', body).then((r) => r.data)
  },

  /** POST /auth/refresh — single-flight flow is owned by refresh.ts. */
  refresh(body: ReqBody<'/api/v1/auth/refresh', 'post'>): Promise<TokenResponse> {
    return client.post('/auth/refresh', body).then((r) => r.data)
  },

  /** POST /auth/logout — invalidates the refresh token (204 expected). */
  logout(body: ReqBody<'/api/v1/auth/logout', 'post'>): Promise<void> {
    return client.post('/auth/logout', body).then(() => undefined)
  },

  /** GET /auth/me — authoritative user state on reload. */
  me(): Promise<Res<'/api/v1/auth/me', 'get'>> {
    return client.get('/auth/me').then((r) => r.data)
  },
}

// --- ventas -----------------------------------------------------------------

export const ventasApi = {
  list(params?: Query<'/api/v1/ventas', 'get'>): Promise<Res<'/api/v1/ventas', 'get'>> {
    return client.get('/ventas', { params }).then((r) => r.data)
  },
  create(body: ReqBody<'/api/v1/ventas', 'post'>): Promise<Res<'/api/v1/ventas', 'post'>> {
    return client.post('/ventas', body).then((r) => r.data)
  },
  /** PATCH /ventas/{id} — mark/unmark a venta as a gift (es_regalo). */
  updateEsRegalo(
    params: PathParams<'/api/v1/ventas/{venta_id}', 'patch'>,
    body: ReqBody<'/api/v1/ventas/{venta_id}', 'patch'>,
  ): Promise<Res<'/api/v1/ventas/{venta_id}', 'patch'>> {
    return client.patch(`/ventas/${params.venta_id}`, body).then((r) => r.data)
  },
}

// --- devoluciones -----------------------------------------------------------

export const devolucionesApi = {
  list(
    params: Query<'/api/v1/devoluciones', 'get'>,
  ): Promise<Res<'/api/v1/devoluciones', 'get'>> {
    return client.get('/devoluciones', { params }).then((r) => r.data)
  },
  create(
    body: ReqBody<'/api/v1/devoluciones', 'post'>,
  ): Promise<Res<'/api/v1/devoluciones', 'post'>> {
    return client.post('/devoluciones', body).then((r) => r.data)
  },
}

// --- finanzas ---------------------------------------------------------------

export const finanzasApi = {
  listMovimientos(params?: Query<'/api/v1/finanzas/movimientos', 'get'>): Promise<Res<'/api/v1/finanzas/movimientos', 'get'>> {
    return client.get('/finanzas/movimientos', { params }).then((r) => r.data)
  },
  createMovimiento(
    body: ReqBody<'/api/v1/finanzas/movimientos', 'post'>,
  ): Promise<Res<'/api/v1/finanzas/movimientos', 'post'>> {
    return client.post('/finanzas/movimientos', body).then((r) => r.data)
  },
  /** Soft-delete — the backend answers 200 + MovimientoRead (not 204). */
  deleteMovimiento(
    params: PathParams<'/api/v1/finanzas/movimientos/{movimiento_id}', 'delete'>,
  ): Promise<Res<'/api/v1/finanzas/movimientos/{movimiento_id}', 'delete'>> {
    return client.delete(`/finanzas/movimientos/${params.movimiento_id}`).then((r) => r.data)
  },
  /** PATCH — partial update (fecha/tipo/descripcion/monto/socio_id); the
   *  backend 422s monto/socio on liquidacion-born rows (FIN-2). */
  updateMovimiento(
    params: PathParams<'/api/v1/finanzas/movimientos/{movimiento_id}', 'patch'>,
    body: ReqBody<'/api/v1/finanzas/movimientos/{movimiento_id}', 'patch'>,
  ): Promise<Res<'/api/v1/finanzas/movimientos/{movimiento_id}', 'patch'>> {
    return client.patch(`/finanzas/movimientos/${params.movimiento_id}`, body).then((r) => r.data)
  },
  listSocios(params?: Query<'/api/v1/finanzas/socios', 'get'>): Promise<Res<'/api/v1/finanzas/socios', 'get'>> {
    return client.get('/finanzas/socios', { params }).then((r) => r.data)
  },
  createSocio(
    body: ReqBody<'/api/v1/finanzas/socios', 'post'>,
  ): Promise<Res<'/api/v1/finanzas/socios', 'post'>> {
    return client.post('/finanzas/socios', body).then((r) => r.data)
  },
  updateSocio(
    params: PathParams<'/api/v1/finanzas/socios/{socio_id}', 'patch'>,
    body: ReqBody<'/api/v1/finanzas/socios/{socio_id}', 'patch'>,
  ): Promise<Res<'/api/v1/finanzas/socios/{socio_id}', 'patch'>> {
    return client.patch(`/finanzas/socios/${params.socio_id}`, body).then((r) => r.data)
  },
  deleteSocio(
    params: PathParams<'/api/v1/finanzas/socios/{socio_id}', 'delete'>,
  ): Promise<Res<'/api/v1/finanzas/socios/{socio_id}', 'delete'>> {
    return client.delete(`/finanzas/socios/${params.socio_id}`).then((r) => r.data)
  },
  createLiquidacion(
    body: ReqBody<'/api/v1/finanzas/liquidaciones', 'post'>,
  ): Promise<Res<'/api/v1/finanzas/liquidaciones', 'post'>> {
    return client.post('/finanzas/liquidaciones', body).then((r) => r.data)
  },
}

// --- analiticos -------------------------------------------------------------

export const analiticosApi = {
  ventasMensuales(): Promise<VentasMensualesRow[]> {
    return client.get('/analiticos/ventas-mensuales').then((r) => r.data)
  },
  insumosBajoStock(): Promise<InsumoBajoStock[]> {
    return client.get('/analiticos/insumos-bajo-stock').then((r) => r.data)
  },
  margenPorProducto(): Promise<MargenProducto[]> {
    return client.get('/analiticos/margen-por-producto').then((r) => r.data)
  },
  topProductos(): Promise<TopProducto[]> {
    return client.get('/analiticos/top-productos').then((r) => r.data)
  },
  topInsumos(): Promise<TopInsumo[]> {
    return client.get('/analiticos/top-insumos').then((r) => r.data)
  },
  finanzasMensuales(): Promise<FinanzasMensualesRow[]> {
    return client.get('/analiticos/finanzas-mensuales').then((r) => r.data)
  },
}

// --- insumos / compras ------------------------------------------------------

export const insumosApi = {
  /** GET /insumos — supports limit/offset (the backend defaults to limit=50). */
  list(params?: Query<'/api/v1/insumos', 'get'>): Promise<Res<'/api/v1/insumos', 'get'>> {
    return client.get('/insumos', { params }).then((r) => r.data)
  },
  get(
    params: PathParams<'/api/v1/insumos/{insumo_id}', 'get'>,
  ): Promise<Res<'/api/v1/insumos/{insumo_id}', 'get'>> {
    return client.get(`/insumos/${params.insumo_id}`).then((r) => r.data)
  },
  create(body: ReqBody<'/api/v1/insumos', 'post'>): Promise<Res<'/api/v1/insumos', 'post'>> {
    return client.post('/insumos', body).then((r) => r.data)
  },
  update(
    params: PathParams<'/api/v1/insumos/{insumo_id}', 'put'>,
    body: ReqBody<'/api/v1/insumos/{insumo_id}', 'put'>,
  ): Promise<Res<'/api/v1/insumos/{insumo_id}', 'put'>> {
    return client.put(`/insumos/${params.insumo_id}`, body).then((r) => r.data)
  },
  delete(
    params: PathParams<'/api/v1/insumos/{insumo_id}', 'delete'>,
  ): Promise<Res<'/api/v1/insumos/{insumo_id}', 'delete'>> {
    return client.delete(`/insumos/${params.insumo_id}`).then((r) => r.data)
  },
}

export const comprasApi = {
  /** GET /compras-insumos — optional insumo_id filter + limit/offset. */
  list(params?: Query<'/api/v1/compras-insumos', 'get'>): Promise<Res<'/api/v1/compras-insumos', 'get'>> {
    return client.get('/compras-insumos', { params }).then((r) => r.data)
  },
  create(
    body: ReqBody<'/api/v1/compras-insumos', 'post'>,
  ): Promise<Res<'/api/v1/compras-insumos', 'post'>> {
    return client.post('/compras-insumos', body).then((r) => r.data)
  },
}

// --- productos / variantes / BOM / costo ------------------------------------

export const productosApi = {
  list(
    params?: Query<'/api/v1/productos', 'get'>,
  ): Promise<Res<'/api/v1/productos', 'get'>> {
    return client.get('/productos', { params }).then((r) => r.data)
  },
  get(
    params: PathParams<'/api/v1/productos/{producto_id}', 'get'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}', 'get'>> {
    return client.get(`/productos/${params.producto_id}`).then((r) => r.data)
  },
  create(body: ReqBody<'/api/v1/productos', 'post'>): Promise<Res<'/api/v1/productos', 'post'>> {
    return client.post('/productos', body).then((r) => r.data)
  },
  update(
    params: PathParams<'/api/v1/productos/{producto_id}', 'put'>,
    body: ReqBody<'/api/v1/productos/{producto_id}', 'put'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}', 'put'>> {
    return client.put(`/productos/${params.producto_id}`, body).then((r) => r.data)
  },
  delete(
    params: PathParams<'/api/v1/productos/{producto_id}', 'delete'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}', 'delete'>> {
    return client.delete(`/productos/${params.producto_id}`).then((r) => r.data)
  },
  listVariantes(
    params: PathParams<'/api/v1/productos/{producto_id}/variantes', 'get'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/variantes', 'get'>> {
    return client.get(`/productos/${params.producto_id}/variantes`).then((r) => r.data)
  },
  createVariante(
    params: PathParams<'/api/v1/productos/{producto_id}/variantes', 'post'>,
    body: ReqBody<'/api/v1/productos/{producto_id}/variantes', 'post'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/variantes', 'post'>> {
    return client.post(`/productos/${params.producto_id}/variantes`, body).then((r) => r.data)
  },
  updateVariante(
    params: PathParams<'/api/v1/productos/{producto_id}/variantes/{variante_id}', 'put'>,
    body: ReqBody<'/api/v1/productos/{producto_id}/variantes/{variante_id}', 'put'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/variantes/{variante_id}', 'put'>> {
    return client.put(`/productos/${params.producto_id}/variantes/${params.variante_id}`, body).then((r) => r.data)
  },
  deleteVariante(
    params: PathParams<'/api/v1/productos/{producto_id}/variantes/{variante_id}', 'delete'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/variantes/{variante_id}', 'delete'>> {
    return client.delete(`/productos/${params.producto_id}/variantes/${params.variante_id}`).then((r) => r.data)
  },
  listBomInsumos(
    params: PathParams<'/api/v1/productos/{producto_id}/bom/insumos', 'get'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/bom/insumos', 'get'>> {
    return client.get(`/productos/${params.producto_id}/bom/insumos`).then((r) => r.data)
  },
  createBomInsumo(
    params: PathParams<'/api/v1/productos/{producto_id}/bom/insumos', 'post'>,
    body: ReqBody<'/api/v1/productos/{producto_id}/bom/insumos', 'post'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/bom/insumos', 'post'>> {
    return client.post(`/productos/${params.producto_id}/bom/insumos`, body).then((r) => r.data)
  },
  updateBomInsumo(
    params: PathParams<'/api/v1/productos/{producto_id}/bom/insumos/{linea_id}', 'put'>,
    body: ReqBody<'/api/v1/productos/{producto_id}/bom/insumos/{linea_id}', 'put'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/bom/insumos/{linea_id}', 'put'>> {
    return client.put(`/productos/${params.producto_id}/bom/insumos/${params.linea_id}`, body).then((r) => r.data)
  },
  deleteBomInsumo(
    params: PathParams<'/api/v1/productos/{producto_id}/bom/insumos/{linea_id}', 'delete'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/bom/insumos/{linea_id}', 'delete'>> {
    return client.delete(`/productos/${params.producto_id}/bom/insumos/${params.linea_id}`).then((r) => r.data)
  },
  listBomProductos(
    params: PathParams<'/api/v1/productos/{producto_id}/bom/productos', 'get'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/bom/productos', 'get'>> {
    return client.get(`/productos/${params.producto_id}/bom/productos`).then((r) => r.data)
  },
  createBomProducto(
    params: PathParams<'/api/v1/productos/{producto_id}/bom/productos', 'post'>,
    body: ReqBody<'/api/v1/productos/{producto_id}/bom/productos', 'post'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/bom/productos', 'post'>> {
    return client.post(`/productos/${params.producto_id}/bom/productos`, body).then((r) => r.data)
  },
  updateBomProducto(
    params: PathParams<'/api/v1/productos/{producto_id}/bom/productos/{linea_id}', 'put'>,
    body: ReqBody<'/api/v1/productos/{producto_id}/bom/productos/{linea_id}', 'put'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/bom/productos/{linea_id}', 'put'>> {
    return client.put(`/productos/${params.producto_id}/bom/productos/${params.linea_id}`, body).then((r) => r.data)
  },
  deleteBomProducto(
    params: PathParams<'/api/v1/productos/{producto_id}/bom/productos/{linea_id}', 'delete'>,
  ): Promise<Res<'/api/v1/productos/{producto_id}/bom/productos/{linea_id}', 'delete'>> {
    return client.delete(`/productos/${params.producto_id}/bom/productos/${params.linea_id}`).then((r) => r.data)
  },
  costo(
    params: PathParams<'/api/v1/productos/{producto_id}/costo', 'get'>,
    query?: { variante_id?: number },
  ): Promise<CostoProduccion> {
    return client.get(`/productos/${params.producto_id}/costo`, { params: query }).then((r) => r.data)
  },
}

// --- maestros ---------------------------------------------------------------

export const clientesApi = {
  /** GET /clientes — supports limit/offset (the backend defaults to limit=50). */
  list(params?: Query<'/api/v1/clientes', 'get'>): Promise<Res<'/api/v1/clientes', 'get'>> {
    return client.get('/clientes', { params }).then((r) => r.data)
  },
  create(body: ReqBody<'/api/v1/clientes', 'post'>): Promise<Res<'/api/v1/clientes', 'post'>> {
    return client.post('/clientes', body).then((r) => r.data)
  },
  update(
    params: PathParams<'/api/v1/clientes/{cliente_id}', 'put'>,
    body: ReqBody<'/api/v1/clientes/{cliente_id}', 'put'>,
  ): Promise<Res<'/api/v1/clientes/{cliente_id}', 'put'>> {
    return client.put(`/clientes/${params.cliente_id}`, body).then((r) => r.data)
  },
  delete(
    params: PathParams<'/api/v1/clientes/{cliente_id}', 'delete'>,
  ): Promise<Res<'/api/v1/clientes/{cliente_id}', 'delete'>> {
    return client.delete(`/clientes/${params.cliente_id}`).then((r) => r.data)
  },
}

export const proveedoresApi = {
  /** GET /proveedores — supports limit/offset (the backend defaults to limit=50). */
  list(params?: Query<'/api/v1/proveedores', 'get'>): Promise<Res<'/api/v1/proveedores', 'get'>> {
    return client.get('/proveedores', { params }).then((r) => r.data)
  },
  create(body: ReqBody<'/api/v1/proveedores', 'post'>): Promise<Res<'/api/v1/proveedores', 'post'>> {
    return client.post('/proveedores', body).then((r) => r.data)
  },
  update(
    params: PathParams<'/api/v1/proveedores/{proveedor_id}', 'put'>,
    body: ReqBody<'/api/v1/proveedores/{proveedor_id}', 'put'>,
  ): Promise<Res<'/api/v1/proveedores/{proveedor_id}', 'put'>> {
    return client.put(`/proveedores/${params.proveedor_id}`, body).then((r) => r.data)
  },
  delete(
    params: PathParams<'/api/v1/proveedores/{proveedor_id}', 'delete'>,
  ): Promise<Res<'/api/v1/proveedores/{proveedor_id}', 'delete'>> {
    return client.delete(`/proveedores/${params.proveedor_id}`).then((r) => r.data)
  },
}

export const tiposProductoApi = {
  /** GET /tipos-producto — supports limit/offset (the backend defaults to limit=50). */
  list(params?: Query<'/api/v1/tipos-producto', 'get'>): Promise<Res<'/api/v1/tipos-producto', 'get'>> {
    return client.get('/tipos-producto', { params }).then((r) => r.data)
  },
  create(body: ReqBody<'/api/v1/tipos-producto', 'post'>): Promise<Res<'/api/v1/tipos-producto', 'post'>> {
    return client.post('/tipos-producto', body).then((r) => r.data)
  },
  update(
    params: PathParams<'/api/v1/tipos-producto/{tipo_producto_id}', 'put'>,
    body: ReqBody<'/api/v1/tipos-producto/{tipo_producto_id}', 'put'>,
  ): Promise<Res<'/api/v1/tipos-producto/{tipo_producto_id}', 'put'>> {
    return client.put(`/tipos-producto/${params.tipo_producto_id}`, body).then((r) => r.data)
  },
  delete(
    params: PathParams<'/api/v1/tipos-producto/{tipo_producto_id}', 'delete'>,
  ): Promise<Res<'/api/v1/tipos-producto/{tipo_producto_id}', 'delete'>> {
    return client.delete(`/tipos-producto/${params.tipo_producto_id}`).then((r) => r.data)
  },
}

export const categoriasInsumosApi = {
  /** GET /categorias-insumos — supports limit/offset (backend default limit=100). */
  list(params?: Query<'/api/v1/categorias-insumos', 'get'>): Promise<Res<'/api/v1/categorias-insumos', 'get'>> {
    return client.get('/categorias-insumos', { params }).then((r) => r.data)
  },
  create(body: ReqBody<'/api/v1/categorias-insumos', 'post'>): Promise<Res<'/api/v1/categorias-insumos', 'post'>> {
    return client.post('/categorias-insumos', body).then((r) => r.data)
  },
  update(
    params: PathParams<'/api/v1/categorias-insumos/{categoria_id}', 'put'>,
    body: ReqBody<'/api/v1/categorias-insumos/{categoria_id}', 'put'>,
  ): Promise<Res<'/api/v1/categorias-insumos/{categoria_id}', 'put'>> {
    return client.put(`/categorias-insumos/${params.categoria_id}`, body).then((r) => r.data)
  },
  delete(
    params: PathParams<'/api/v1/categorias-insumos/{categoria_id}', 'delete'>,
  ): Promise<Res<'/api/v1/categorias-insumos/{categoria_id}', 'delete'>> {
    return client.delete(`/categorias-insumos/${params.categoria_id}`).then((r) => r.data)
  },
}

// --- omisiones --------------------------------------------------------------

export const omisionesApi = {
  /** GET /omisiones — paginated {items, total} + filters (fase/nivel/hoja/
   *  resuelta/fechas/q). */
  listOmisiones(
    params?: Query<'/api/v1/omisiones', 'get'>,
  ): Promise<Res<'/api/v1/omisiones', 'get'>> {
    return client.get('/omisiones', { params }).then((r) => r.data)
  },
  /** PATCH /omisiones/{id} — mark/unmark resuelta (admin-only, MIG-4). */
  updateOmision(
    params: PathParams<'/api/v1/omisiones/{omision_id}', 'patch'>,
    body: ReqBody<'/api/v1/omisiones/{omision_id}', 'patch'>,
  ): Promise<Res<'/api/v1/omisiones/{omision_id}', 'patch'>> {
    return client.patch(`/omisiones/${params.omision_id}`, body).then((r) => r.data)
  },
}

// --- usuarios ---------------------------------------------------------------

export const usuariosApi = {
  /** GET /usuarios — supports limit/offset (the backend defaults to limit=50). */
  list(params?: Query<'/api/v1/usuarios', 'get'>): Promise<Res<'/api/v1/usuarios', 'get'>> {
    return client.get('/usuarios', { params }).then((r) => r.data)
  },
  create(body: ReqBody<'/api/v1/usuarios', 'post'>): Promise<Res<'/api/v1/usuarios', 'post'>> {
    return client.post('/usuarios', body).then((r) => r.data)
  },
  update(
    params: PathParams<'/api/v1/usuarios/{usuario_id}', 'patch'>,
    body: ReqBody<'/api/v1/usuarios/{usuario_id}', 'patch'>,
  ): Promise<Res<'/api/v1/usuarios/{usuario_id}', 'patch'>> {
    return client.patch(`/usuarios/${params.usuario_id}`, body).then((r) => r.data)
  },
  delete(
    params: PathParams<'/api/v1/usuarios/{usuario_id}', 'delete'>,
  ): Promise<Res<'/api/v1/usuarios/{usuario_id}', 'delete'>> {
    return client.delete(`/usuarios/${params.usuario_id}`).then((r) => r.data)
  },
}
