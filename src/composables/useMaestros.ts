/**
 * useMaestros — adapter that selects Pinia mock or real API based on useMode.
 * When isMock is true, operations run against src/stores/atelier.ts.
 * Otherwise they delegate to src/services/api/maestros.ts (FastAPI + Postgres).
 * Mirrors useClientes / useSocios / useFinanzas; MaestrosView.vue stays intact.
 */
import { useAtelierStore } from '@/stores/atelier'
import { useMode } from './useMode'
import * as api from '@/services/api/maestros'

function toPaginated<T>(list: T[], params: api.ListParams = {}): api.Paginated<T> {
  let filtered = [...list] as unknown as Record<string, unknown>[]
  if (params.q) {
    const q = String(params.q).toLowerCase()
    filtered = filtered.filter((r) => JSON.stringify(r).toLowerCase().includes(q))
  }
  if (params.tipo_talla) filtered = filtered.filter((r) => r.tipo_talla === params.tipo_talla)
  if (params.tipo) filtered = filtered.filter((r) => r.tipo === params.tipo)
  if (params.categoria) filtered = filtered.filter((r) => r.categoria === params.categoria)
  const total = filtered.length
  const offset = (params.offset as number) ?? 0
  const limit = (params.limit as number) ?? 50
  const items = filtered.slice(offset, offset + limit) as unknown as T[]
  return { items, total }
}

export function useMaestros() {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  // Proveedores
  async function listProveedores(params: api.ListParams = {}) {
    if (isMock.value) return toPaginated(atelier.proveedoresMaestros as unknown as api.ProveedorRead[], params)
    return api.listProveedores(params)
  }
  async function createProveedor(payload: Record<string, unknown>) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.proveedoresMaestros.map((p) => p.id)) + 1
      const nuevo = { id: nextId, nombre: payload.nombre as string, categoria: payload.categoria as string, ciudad: payload.ciudad as string, telefono: payload.telefono as string, email: payload.email as string, activo: true, ...payload } as unknown as typeof atelier.proveedoresMaestros[number]
      atelier.proveedoresMaestros.unshift(nuevo)
      return nuevo as unknown as api.ProveedorRead
    }
    return api.createProveedor(payload)
  }
  async function updateProveedor(id: number, payload: Record<string, unknown>) {
    if (isMock.value) {
      const idx = atelier.proveedoresMaestros.findIndex((p) => p.id === id)
      if (idx === -1) return null
      Object.assign(atelier.proveedoresMaestros[idx] as unknown as Record<string, unknown>, payload)
      return atelier.proveedoresMaestros[idx] as unknown as api.ProveedorRead
    }
    return api.updateProveedor(id, payload)
  }
  async function removeProveedor(id: number) {
    if (isMock.value) {
      const idx = atelier.proveedoresMaestros.findIndex((p) => p.id === id)
      if (idx !== -1) atelier.proveedoresMaestros.splice(idx, 1)
      return
    }
    return api.deleteProveedor(id)
  }

  // Categorias
  async function listCategorias(params: api.ListParams = {}) {
    if (isMock.value) return toPaginated(atelier.categoriasColeccionMaestros as unknown as api.CategoriaRead[], params)
    return api.listCategorias(params)
  }
  async function createCategoria(payload: Record<string, unknown>) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.categoriasColeccionMaestros.map((c) => c.id)) + 1
      const nuevo = { id: nextId, ...payload, total_modelos: 0, activo: true } as unknown as typeof atelier.categoriasColeccionMaestros[number]
      atelier.categoriasColeccionMaestros.unshift(nuevo)
      return nuevo as unknown as api.CategoriaRead
    }
    return api.createCategoria(payload)
  }
  async function updateCategoria(id: number, payload: Record<string, unknown>) {
    if (isMock.value) {
      const idx = atelier.categoriasColeccionMaestros.findIndex((c) => c.id === id)
      if (idx !== -1) Object.assign(atelier.categoriasColeccionMaestros[idx] as unknown as Record<string, unknown>, payload)
      return atelier.categoriasColeccionMaestros[idx] as unknown as api.CategoriaRead
    }
    return api.updateCategoria(id, payload)
  }
  async function removeCategoria(id: number) {
    if (isMock.value) {
      const idx = atelier.categoriasColeccionMaestros.findIndex((c) => c.id === id)
      if (idx !== -1) atelier.categoriasColeccionMaestros.splice(idx, 1)
      return
    }
    return api.deleteCategoria(id)
  }

  // Ubicaciones
  async function listUbicaciones(params: api.ListParams = {}) {
    if (isMock.value) return toPaginated(atelier.ubicacionesTallerMaestros as unknown as api.UbicacionRead[], params)
    return api.listUbicaciones(params)
  }
  async function createUbicacion(payload: Record<string, unknown>) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.ubicacionesTallerMaestros.map((u) => u.id)) + 1
      const nuevo = { id: nextId, ...payload, activo: true } as unknown as typeof atelier.ubicacionesTallerMaestros[number]
      atelier.ubicacionesTallerMaestros.unshift(nuevo)
      return nuevo as unknown as api.UbicacionRead
    }
    return api.createUbicacion(payload)
  }
  async function updateUbicacion(id: number, payload: Record<string, unknown>) {
    if (isMock.value) {
      const idx = atelier.ubicacionesTallerMaestros.findIndex((u) => u.id === id)
      if (idx !== -1) Object.assign(atelier.ubicacionesTallerMaestros[idx] as unknown as Record<string, unknown>, payload)
      return atelier.ubicacionesTallerMaestros[idx] as unknown as api.UbicacionRead
    }
    return api.updateUbicacion(id, payload)
  }
  async function removeUbicacion(id: number) {
    if (isMock.value) {
      const idx = atelier.ubicacionesTallerMaestros.findIndex((u) => u.id === id)
      if (idx !== -1) atelier.ubicacionesTallerMaestros.splice(idx, 1)
      return
    }
    return api.deleteUbicacion(id)
  }

  // Canales (tryFetch preserved)
  async function listCanales(params: api.ListParams = {}) {
    if (isMock.value) return toPaginated(atelier.canalesVentaMaestros as unknown as api.CanalRead[], params)
    return api.listCanales(params)
  }
  async function createCanal(payload: Record<string, unknown>) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.canalesVentaMaestros.map((c) => c.id)) + 1
      const nuevo = { id: nextId, ...payload } as unknown as typeof atelier.canalesVentaMaestros[number]
      atelier.canalesVentaMaestros.unshift(nuevo)
      return nuevo as unknown as api.CanalRead
    }
    return api.createCanal(payload)
  }
  async function updateCanal(id: number, payload: Record<string, unknown>) {
    if (isMock.value) {
      const idx = atelier.canalesVentaMaestros.findIndex((c) => c.id === id)
      if (idx !== -1) Object.assign(atelier.canalesVentaMaestros[idx] as unknown as Record<string, unknown>, payload)
      return atelier.canalesVentaMaestros[idx] as unknown as api.CanalRead
    }
    return api.updateCanal(id, payload)
  }
  async function removeCanal(id: number) {
    if (isMock.value) {
      const idx = atelier.canalesVentaMaestros.findIndex((c) => c.id === id)
      if (idx !== -1) atelier.canalesVentaMaestros.splice(idx, 1)
      return
    }
    return api.deleteCanal(id)
  }

  // Metodos
  async function listMetodosPago(params: api.ListParams = {}) {
    if (isMock.value) return toPaginated(atelier.metodosPagoMaestros as unknown as api.MetodoRead[], params)
    return api.listMetodosPago(params)
  }
  async function createMetodo(payload: Record<string, unknown>) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.metodosPagoMaestros.map((m) => m.id)) + 1
      const nuevo = { id: nextId, ...payload } as unknown as typeof atelier.metodosPagoMaestros[number]
      atelier.metodosPagoMaestros.unshift(nuevo)
      return nuevo as unknown as api.MetodoRead
    }
    return api.createMetodo(payload)
  }
  async function updateMetodo(id: number, payload: Record<string, unknown>) {
    if (isMock.value) {
      const idx = atelier.metodosPagoMaestros.findIndex((m) => m.id === id)
      if (idx !== -1) Object.assign(atelier.metodosPagoMaestros[idx] as unknown as Record<string, unknown>, payload)
      return atelier.metodosPagoMaestros[idx] as unknown as api.MetodoRead
    }
    return api.updateMetodo(id, payload)
  }
  async function removeMetodo(id: number) {
    if (isMock.value) {
      const idx = atelier.metodosPagoMaestros.findIndex((m) => m.id === id)
      if (idx !== -1) atelier.metodosPagoMaestros.splice(idx, 1)
      return
    }
    return api.deleteMetodo(id)
  }

  // Tallas
  async function listTallas(params: api.ListParams = {}) {
    if (isMock.value) return toPaginated(atelier.tallasEstandarMaestros as unknown as api.TallaRead[], params)
    return api.listTallas(params)
  }
  async function createTalla(payload: Record<string, unknown>) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.tallasEstandarMaestros.map((t) => t.id)) + 1
      const nuevo = { id: nextId, ...payload, orden: (payload.orden as number) ?? 99 } as unknown as typeof atelier.tallasEstandarMaestros[number]
      atelier.tallasEstandarMaestros.unshift(nuevo)
      return nuevo as unknown as api.TallaRead
    }
    return api.createTalla(payload)
  }
  async function updateTalla(id: number, payload: Record<string, unknown>) {
    if (isMock.value) {
      const idx = atelier.tallasEstandarMaestros.findIndex((t) => t.id === id)
      if (idx !== -1) Object.assign(atelier.tallasEstandarMaestros[idx] as unknown as Record<string, unknown>, payload)
      return atelier.tallasEstandarMaestros[idx] as unknown as api.TallaRead
    }
    return api.updateTalla(id, payload)
  }
  async function removeTalla(id: number) {
    if (isMock.value) {
      const idx = atelier.tallasEstandarMaestros.findIndex((t) => t.id === id)
      if (idx !== -1) atelier.tallasEstandarMaestros.splice(idx, 1)
      return
    }
    return api.deleteTalla(id)
  }

  // Productos sin talla
  async function listProductosSinTalla(params: api.ListParams = {}) {
    if (isMock.value) return toPaginated(atelier.productosSinTallaMaestros as unknown as api.ProductoSinTallaRead[], params)
    return api.listProductosSinTalla(params)
  }
  async function createProductoSinTalla(payload: Record<string, unknown>) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.productosSinTallaMaestros.map((p) => p.id)) + 1
      const nuevo = { id: nextId, ...payload } as unknown as typeof atelier.productosSinTallaMaestros[number]
      atelier.productosSinTallaMaestros.unshift(nuevo)
      return nuevo as unknown as api.ProductoSinTallaRead
    }
    return api.createProductoSinTalla(payload)
  }
  async function updateProductoSinTalla(id: number, payload: Record<string, unknown>) {
    if (isMock.value) {
      const idx = atelier.productosSinTallaMaestros.findIndex((p) => p.id === id)
      if (idx !== -1) Object.assign(atelier.productosSinTallaMaestros[idx] as unknown as Record<string, unknown>, payload)
      return atelier.productosSinTallaMaestros[idx] as unknown as api.ProductoSinTallaRead
    }
    return api.updateProductoSinTalla(id, payload)
  }
  async function removeProductoSinTalla(id: number) {
    if (isMock.value) {
      const idx = atelier.productosSinTallaMaestros.findIndex((p) => p.id === id)
      if (idx !== -1) atelier.productosSinTallaMaestros.splice(idx, 1)
      return
    }
    return api.deleteProductoSinTalla(id)
  }

  // Parametros singleton
  async function getParametros() {
    if (isMock.value) return atelier.parametrosCosteo as unknown as api.ParametrosRead
    return api.getParametros()
  }
  async function updateParametros(payload: Record<string, unknown>) {
    if (isMock.value) {
      Object.assign(atelier.parametrosCosteo as unknown as Record<string, unknown>, payload)
      return atelier.parametrosCosteo as unknown as api.ParametrosRead
    }
    return api.updateParametros(payload)
  }

  return {
    isMock,
    mode,
    // proveedores
    listProveedores,
    createProveedor,
    updateProveedor,
    removeProveedor,
    // categorias
    listCategorias,
    createCategoria,
    updateCategoria,
    removeCategoria,
    // ubicaciones
    listUbicaciones,
    createUbicacion,
    updateUbicacion,
    removeUbicacion,
    // canales
    listCanales,
    createCanal,
    updateCanal,
    removeCanal,
    // metodos
    listMetodosPago,
    createMetodo,
    updateMetodo,
    removeMetodo,
    // tallas
    listTallas,
    createTalla,
    updateTalla,
    removeTalla,
    // sin talla
    listProductosSinTalla,
    createProductoSinTalla,
    updateProductoSinTalla,
    removeProductoSinTalla,
    // parametros
    getParametros,
    updateParametros,
  }
}
