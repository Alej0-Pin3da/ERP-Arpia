/**
 * useProductos — adapter that selects Pinia mock or real API based on useMode.
 *
 * When isMock is true, operations run against src/stores/atelier.ts (in-memory
 * `recetas`). Otherwise they delegate to src/services/api/productos.ts
 * (FastAPI + Postgres). The interface is promise-based in both paths so
 * callers can await uniformly.
 */
import { useAtelierStore, type RecetaBOM } from '@/stores/atelier'
import { useMode } from './useMode'
import * as api from '@/services/api/productos'

export interface UseProductosReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListProductosParams) => Promise<api.Paginated<api.ProductoRead> | api.Paginated<RecetaBOM>>
  get: (id: number) => Promise<api.ProductoRead | RecetaBOM | null>
  create: (payload: api.ProductoCreate) => Promise<api.ProductoRead | RecetaBOM>
  update: (id: number, payload: api.ProductoUpdate) => Promise<api.ProductoRead | RecetaBOM | null>
  remove: (id: number) => Promise<void>
}

function toPaginatedRecetas(list: RecetaBOM[], params: api.ListProductosParams = {}): api.Paginated<RecetaBOM> {
  let filtered = [...list]
  if (params.q) {
    const q = params.q.toLowerCase()
    filtered = filtered.filter(
      (r) =>
        r.nombre.toLowerCase().includes(q) ||
        (r.codigo && r.codigo.toLowerCase().includes(q)) ||
        (r.descripcion && r.descripcion.toLowerCase().includes(q)),
    )
  }
  if (params.tipo_producto_id != null) {
    filtered = filtered.filter(
      (r) => (r as unknown as { tipo_producto_id?: number }).tipo_producto_id === params.tipo_producto_id,
    )
  }
  const total = filtered.length
  const offset = params.offset ?? 0
  const limit = params.limit ?? 50
  const items = filtered.slice(offset, offset + limit)
  return { items, total }
}

export function useProductos(): UseProductosReturn {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  async function list(params: api.ListProductosParams = {}) {
    if (isMock.value) {
      return toPaginatedRecetas(atelier.recetas as unknown as RecetaBOM[], params)
    }
    return api.listProductos(params)
  }

  async function get(id: number) {
    if (isMock.value) {
      return (atelier.recetas.find((r) => r.id === id) as unknown as RecetaBOM) ?? null
    }
    return api.getProducto(id)
  }

  async function create(payload: api.ProductoCreate) {
    if (isMock.value) {
      const recetas = atelier.recetas as unknown as RecetaBOM[]
      const nextId = Math.max(0, ...recetas.map((r) => r.id)) + 1
      const nuevo: RecetaBOM = {
        id: nextId,
        codigo: payload.codigo ?? `PRD-${nextId}`,
        nombre: payload.nombre,
        categoria: payload.categoria ?? 'General',
        linea: payload.linea ?? 'General',
        descripcion: payload.descripcion ?? payload.nombre,
        tiempo_confeccion_min: payload.tiempo_confeccion_min ?? 60,
        insumos_count: 0,
        costo_insumos: Number(payload.costo_insumos ?? 0),
        mano_obra: Number(payload.mano_obra ?? 0),
        cif_energia: Number(payload.cif_energia ?? 0),
        costo_total_unitario: Number(payload.costos_operativos_fijos ?? 0),
        precio_venta: Number(payload.precio_venta_sugerido ?? 0),
        markup_pct: Number(payload.markup_pct ?? 0),
        recomendaciones_taller: payload.recomendaciones_taller ?? '',
        items: [],
        fases: [],
      }
      recetas.unshift(nuevo)
      return nuevo
    }
    return api.createProducto(payload)
  }

  async function update(id: number, payload: api.ProductoUpdate) {
    if (isMock.value) {
      const recetas = atelier.recetas as unknown as RecetaBOM[]
      const idx = recetas.findIndex((r) => r.id === id)
      if (idx === -1) return null
      const current = recetas[idx] as unknown as Record<string, unknown>
      if (payload.nombre !== undefined) current.nombre = payload.nombre
      if (payload.codigo !== undefined) current.codigo = payload.codigo
      if (payload.categoria !== undefined) current.categoria = payload.categoria
      if (payload.linea !== undefined) current.linea = payload.linea
      if (payload.descripcion !== undefined) current.descripcion = payload.descripcion
      if (payload.precio_venta_sugerido !== undefined) current.precio_venta = Number(payload.precio_venta_sugerido)
      Object.assign(current, payload)
      return current as unknown as RecetaBOM
    }
    return api.updateProducto(id, payload)
  }

  async function remove(id: number): Promise<void> {
    if (isMock.value) {
      const recetas = atelier.recetas as unknown as RecetaBOM[]
      const idx = recetas.findIndex((r) => r.id === id)
      if (idx !== -1) recetas.splice(idx, 1)
      return
    }
    return api.deleteProducto(id)
  }

  return { isMock, mode, list, get, create, update, remove }
}
