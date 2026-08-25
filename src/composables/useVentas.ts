/**
 * useVentas — adapter that selects Pinia mock or real API based on useMode.
 * Mirrors useClientes but for sales domain.
 */
import { useAtelierStore, type VentaAtelier } from '@/stores/atelier'
import { useMode } from './useMode'
import * as api from '@/services/api/ventas'

export interface UseVentasReturn {
  isMock: ReturnType<typeof useMode>['isMock']
  mode: ReturnType<typeof useMode>['mode']
  list: (params?: api.ListVentasParams) => Promise<api.Paginated<api.VentaRead> | api.Paginated<VentaAtelier>>
  get: (id: number) => Promise<api.VentaRead | VentaAtelier | null>
  create: (payload: api.VentaCreatePayload) => Promise<api.VentaRead | VentaAtelier>
  anular: (id: number) => Promise<api.VentaRead | VentaAtelier | null>
}

function toPaginatedVentas(list: VentaAtelier[], params: api.ListVentasParams = {}): api.Paginated<VentaAtelier> {
  let filtered = [...list]
  if (params.canal_venta) filtered = filtered.filter((v) => v.canal === params.canal_venta)
  if (params.estado) filtered = filtered.filter((v) => v.estado === (params.estado as string).toUpperCase())
  const total = filtered.length
  const offset = params.offset ?? 0
  const limit = params.limit ?? 50
  const items = filtered.slice(offset, offset + limit)
  return { items, total }
}

export function useVentas(): UseVentasReturn {
  const { isMock, mode } = useMode()
  const atelier = useAtelierStore()

  async function list(params: api.ListVentasParams = {}) {
    if (isMock.value) {
      return toPaginatedVentas(atelier.ventas as unknown as VentaAtelier[], params)
    }
    return api.listVentas(params)
  }

  async function get(id: number) {
    if (isMock.value) {
      return (atelier.ventas.find((v) => v.id === id) as unknown as VentaAtelier) ?? null
    }
    return api.getVenta(id)
  }

  async function create(payload: api.VentaCreatePayload) {
    if (isMock.value) {
      const nextId = Math.max(0, ...atelier.ventas.map((v) => v.id)) + 1
      const nuevo: VentaAtelier = {
        id: nextId,
        codigo: `VEN-LOC-${String(nextId).padStart(3, '0')}`,
        cliente_id: payload.cliente_id ?? null,
        cliente_nombre: 'Cliente mock',
        fecha: new Date().toISOString().split('T')[0],
        canal: payload.canal_venta,
        metodo_pago: (payload.metodo_pago as string) ?? 'efectivo',
        estado: 'COMPLETADA',
        items: (payload.detalles ?? []).map((d, idx) => ({
          id: idx + 1,
          producto_id: d.producto_id,
          nombre_prenda: `Producto ${d.producto_id}`,
          talla: 'M',
          color: '—',
          cantidad: Number(d.cantidad),
          precio_unitario: Number(d.precio_unitario),
          costo_unitario: 0,
          subtotal: Number(d.cantidad) * Number(d.precio_unitario),
          costo_subtotal: 0,
        })),
        subtotal: 0,
        descuento_porcentaje: Number(payload.descuento_porcentaje ?? 0),
        descuento_valor: 0,
        total_venta: 0,
        costo_total: 0,
        ganancia_neta: 0,
        margen_pct: 0,
        reinversion_40: 0,
        margarita_30: 0,
        valqui_30: 0,
      }
      // compute totals from detalles
      const subtotal = nuevo.items.reduce((a, it) => a + it.subtotal, 0)
      nuevo.subtotal = subtotal
      nuevo.total_venta = subtotal
      atelier.ventas.unshift(nuevo as unknown as typeof atelier.ventas[number])
      return nuevo
    }
    return api.createVenta(payload)
  }

  async function anular(id: number) {
    if (isMock.value) {
      const idx = atelier.ventas.findIndex((v) => v.id === id)
      if (idx === -1) return null
      const v = atelier.ventas[idx] as unknown as VentaAtelier
      v.estado = 'ANULADA'
      return v
    }
    return api.anularVenta(id)
  }

  return { isMock, mode, list, get, create, anular }
}
