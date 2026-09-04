/**
 * Maestros API — 8 catalogs via /maestros/* (Paginated) with tryFetch fallback for canales/metodos.
 * Keeps canales/metodos backward compatible by wrapping static arrays as Paginated when API unavailable.
 */
import { client } from '@/api/client'
import { showToast } from '@/utils/toast'

export interface Paginated<T> {
  items: T[]
  total: number
}

// --- Read shapes (minimal fields used by UI) ---
export interface ProveedorRead {
  id: number
  nombre: string
  categoria: string
  ciudad?: string | null
  calificacion?: number | null
  tiempo_entrega_dias?: number | null
  email?: string | null
  telefono?: string | null
  activo: boolean
  notas?: string | null
  created_at: string
  updated_at: string
}
export interface CategoriaRead {
  id: number
  nombre: string
  tipo_talla: string
  descripcion?: string | null
  margen_meta_pct?: number | null
  total_modelos: number
  activo: boolean
  created_at: string
  updated_at: string
}
export interface UbicacionRead {
  id: number
  codigo: string
  nombre: string
  tipo: string
  capacidad?: string | null
  observaciones?: string | null
  activo: boolean
  created_at: string
  updated_at: string
}
export interface CanalRead {
  id: number
  codigo: string
  nombre: string
  tipo?: string | null
  comision_pct?: number | null
  costo_fijo_mensual?: number | null
  activo?: boolean | null
  descripcion?: string | null
  created_at: string
  updated_at?: string | null
}
export interface MetodoRead {
  id: number
  codigo: string
  nombre: string
  tipo?: string | null
  comision_pct?: number | null
  tiempo_acreditacion?: string | null
  activo?: boolean | null
  datos_cuenta?: string | null
  descripcion?: string | null
  created_at: string
  updated_at?: string | null
}
export interface TallaRead {
  id: number
  talla: string
  orden: number
  busto?: string | null
  cintura?: string | null
  cadera?: string | null
  reduccion_corset?: string | null
  descripcion?: string | null
  activo: boolean
  created_at: string
  updated_at: string
}
export interface ProductoSinTallaRead {
  id: number
  nombre: string
  categoria: string
  dimensiones?: string | null
  materiales?: string | null
  descripcion?: string | null
  precio_sugerido: number
  activo: boolean
  created_at: string
  updated_at: string
}
export interface ParametrosRead {
  id: number
  costo_minuto_costura: number
  costo_hora_patronaje: number
  margen_meta_global_pct: number
  desperdicio_textil_default_pct: number
  iva_regimen_pct: number
  distribucion_reinversion_pct: number
  reparto_margara_pct: number
  reparto_valqui_pct: number
  created_at: string
  updated_at: string
}

// Backwards compat static fallbacks
export interface CanalVentaMaestro { codigo: string; nombre: string }
export interface MetodoPagoMaestro { codigo: string; nombre: string }
export const CANALES_VENTA: CanalVentaMaestro[] = [
  { codigo: 'web', nombre: 'Web' },
  { codigo: 'whatsapp', nombre: 'WhatsApp / DM' },
  { codigo: 'instagram', nombre: 'Instagram' },
  { codigo: 'feria', nombre: 'Feria / Evento' },
  { codigo: 'showroom_pereira', nombre: 'Showroom Pereira' },
]
export const METODOS_PAGO: MetodoPagoMaestro[] = [
  { codigo: 'efectivo', nombre: 'Efectivo' },
  { codigo: 'transferencia', nombre: 'Transferencia' },
  { codigo: 'tarjeta', nombre: 'Tarjeta' },
  { codigo: 'contraentrega', nombre: 'Contraentrega' },
]

// Generic param shape
export interface ListParams {
  q?: string
  limit?: number
  offset?: number
  sort_by?: string
  order?: 'asc' | 'desc'
  [key: string]: unknown
}

async function tryFetch<T>(path: string, fallback: T, params?: Record<string, unknown>): Promise<T> {
  try {
    const { data } = await client.get<T>(path, { params })
    return data
  } catch {
    // P2-2: fail-loud — el fallback estático se mantiene para no romper ventas,
    // pero se avisa en vez de enmascarar la caída del backend.
    console.warn(`[maestros] ${path} no disponible, usando valores locales`)
    try {
      showToast('warn', 'Maestros no disponibles, usando valores locales', path)
    } catch { /* toast sin suscriptores: solo el console.warn vale */ }
    return fallback
  }
}

// Proveedores
export async function listProveedores(params: ListParams = {}): Promise<Paginated<ProveedorRead>> {
  const { data } = await client.get<Paginated<ProveedorRead>>('/maestros/proveedores', { params })
  return data
}
export async function getProveedor(id: number): Promise<ProveedorRead> {
  const { data } = await client.get<ProveedorRead>(`/maestros/proveedores/${id}`)
  return data
}
export async function createProveedor(payload: Record<string, unknown>): Promise<ProveedorRead> {
  const { data } = await client.post<ProveedorRead>('/maestros/proveedores', payload)
  return data
}
export async function updateProveedor(id: number, payload: Record<string, unknown>): Promise<ProveedorRead> {
  const { data } = await client.patch<ProveedorRead>(`/maestros/proveedores/${id}`, payload)
  return data
}
export async function deleteProveedor(id: number): Promise<void> {
  await client.delete(`/maestros/proveedores/${id}`)
}

// Categorias
export async function listCategorias(params: ListParams = {}): Promise<Paginated<CategoriaRead>> {
  const { data } = await client.get<Paginated<CategoriaRead>>('/maestros/categorias-coleccion', { params })
  return data
}
export async function createCategoria(payload: Record<string, unknown>): Promise<CategoriaRead> {
  const { data } = await client.post<CategoriaRead>('/maestros/categorias-coleccion', payload)
  return data
}
export async function updateCategoria(id: number, payload: Record<string, unknown>): Promise<CategoriaRead> {
  const { data } = await client.patch<CategoriaRead>(`/maestros/categorias-coleccion/${id}`, payload)
  return data
}
export async function deleteCategoria(id: number): Promise<void> {
  await client.delete(`/maestros/categorias-coleccion/${id}`)
}

// Ubicaciones
export async function listUbicaciones(params: ListParams = {}): Promise<Paginated<UbicacionRead>> {
  const { data } = await client.get<Paginated<UbicacionRead>>('/maestros/ubicaciones-taller', { params })
  return data
}
export async function createUbicacion(payload: Record<string, unknown>): Promise<UbicacionRead> {
  const { data } = await client.post<UbicacionRead>('/maestros/ubicaciones-taller', payload)
  return data
}
export async function updateUbicacion(id: number, payload: Record<string, unknown>): Promise<UbicacionRead> {
  const { data } = await client.patch<UbicacionRead>(`/maestros/ubicaciones-taller/${id}`, payload)
  return data
}
export async function deleteUbicacion(id: number): Promise<void> {
  await client.delete(`/maestros/ubicaciones-taller/${id}`)
}

// Canales (with fallback)
export async function listCanales(params: ListParams = {}): Promise<Paginated<CanalRead>> {
  const fallback: Paginated<CanalRead> = {
    items: CANALES_VENTA.map((c, i) => ({ id: i + 1, codigo: c.codigo, nombre: c.nombre, created_at: new Date().toISOString(), updated_at: null })) as unknown as CanalRead[],
    total: CANALES_VENTA.length,
  }
  return tryFetch<Paginated<CanalRead>>('/maestros/canales-venta', fallback, params)
}
export async function createCanal(payload: Record<string, unknown>): Promise<CanalRead> {
  const { data } = await client.post<CanalRead>('/maestros/canales-venta', payload)
  return data
}
export async function updateCanal(id: number, payload: Record<string, unknown>): Promise<CanalRead> {
  const { data } = await client.patch<CanalRead>(`/maestros/canales-venta/${id}`, payload)
  return data
}
export async function deleteCanal(id: number): Promise<void> {
  await client.delete(`/maestros/canales-venta/${id}`)
}
export async function listCanalesLegacy(): Promise<CanalVentaMaestro[]> {
  return tryFetch<CanalVentaMaestro[]>('/maestros/canales-venta', CANALES_VENTA)
}

// Metodos (with fallback)
export async function listMetodosPago(params: ListParams = {}): Promise<Paginated<MetodoRead>> {
  const fallback: Paginated<MetodoRead> = {
    items: METODOS_PAGO.map((m, i) => ({ id: i + 1, codigo: m.codigo, nombre: m.nombre, created_at: new Date().toISOString(), updated_at: null })) as unknown as MetodoRead[],
    total: METODOS_PAGO.length,
  }
  return tryFetch<Paginated<MetodoRead>>('/maestros/metodos-pago', fallback, params)
}
export async function createMetodo(payload: Record<string, unknown>): Promise<MetodoRead> {
  const { data } = await client.post<MetodoRead>('/maestros/metodos-pago', payload)
  return data
}
export async function updateMetodo(id: number, payload: Record<string, unknown>): Promise<MetodoRead> {
  const { data } = await client.patch<MetodoRead>(`/maestros/metodos-pago/${id}`, payload)
  return data
}
export async function deleteMetodo(id: number): Promise<void> {
  await client.delete(`/maestros/metodos-pago/${id}`)
}
export async function listMetodosLegacy(): Promise<MetodoPagoMaestro[]> {
  return tryFetch<MetodoPagoMaestro[]>('/maestros/metodos-pago', METODOS_PAGO)
}

// Tallas
export async function listTallas(params: ListParams = {}): Promise<Paginated<TallaRead>> {
  const { data } = await client.get<Paginated<TallaRead>>('/maestros/tallas-estandar', { params })
  return data
}
export async function createTalla(payload: Record<string, unknown>): Promise<TallaRead> {
  const { data } = await client.post<TallaRead>('/maestros/tallas-estandar', payload)
  return data
}
export async function updateTalla(id: number, payload: Record<string, unknown>): Promise<TallaRead> {
  const { data } = await client.patch<TallaRead>(`/maestros/tallas-estandar/${id}`, payload)
  return data
}
export async function deleteTalla(id: number): Promise<void> {
  await client.delete(`/maestros/tallas-estandar/${id}`)
}

// Productos sin talla
export async function listProductosSinTalla(params: ListParams = {}): Promise<Paginated<ProductoSinTallaRead>> {
  const { data } = await client.get<Paginated<ProductoSinTallaRead>>('/maestros/productos-sin-talla', { params })
  return data
}
export async function createProductoSinTalla(payload: Record<string, unknown>): Promise<ProductoSinTallaRead> {
  const { data } = await client.post<ProductoSinTallaRead>('/maestros/productos-sin-talla', payload)
  return data
}
export async function updateProductoSinTalla(id: number, payload: Record<string, unknown>): Promise<ProductoSinTallaRead> {
  const { data } = await client.patch<ProductoSinTallaRead>(`/maestros/productos-sin-talla/${id}`, payload)
  return data
}
export async function deleteProductoSinTalla(id: number): Promise<void> {
  await client.delete(`/maestros/productos-sin-talla/${id}`)
}

// Parametros singleton
export async function getParametros(): Promise<ParametrosRead> {
  const { data } = await client.get<ParametrosRead>('/maestros/parametros-costeo')
  return data
}
export async function updateParametros(payload: Record<string, unknown>): Promise<ParametrosRead> {
  const { data } = await client.patch<ParametrosRead>('/maestros/parametros-costeo', payload)
  return data
}
