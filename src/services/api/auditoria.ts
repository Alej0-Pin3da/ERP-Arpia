import { client } from '@/api/client'

/** Mirrors `backend/app/models/audit_fiscal.py` (read-only). */
export interface PrecioVersionRead {
  id: number
  producto_id: number
  variante_id?: number | null
  precio: number | string
  fecha_desde: string
  creado_por?: number | null
  created_at?: string
}

/** Mirrors `backend/app/models/audit_fiscal.py` (read-only). */
export interface CostoVersionRead {
  id: number
  producto_id: number
  costo: number | string
  fecha_desde: string
  creado_por?: number | null
  created_at?: string
}

/** Mirrors `backend/app/models/audit_fiscal.py` (read-only). */
export interface CierreMensualRead {
  id: number
  periodo: string
  estado?: string | null
  cerrado_por?: number | null
  created_at?: string
}

/**
 * Read-only fiscal audit listings (`backend/app/api/routes/audit_fiscal.py`).
 * NOTE: unlike `/omisiones`, these GETs return plain arrays (`.all()`),
 * not a `{ items, total }` envelope.
 */
export async function listPrecioVersions(params?: { producto_id?: number }): Promise<PrecioVersionRead[]> {
  const { data } = await client.get<PrecioVersionRead[]>('/audit-fiscal/precio-versions', { params })
  return data ?? []
}

export async function listCostoVersions(params?: { producto_id?: number }): Promise<CostoVersionRead[]> {
  const { data } = await client.get<CostoVersionRead[]>('/audit-fiscal/costo-versions', { params })
  return data ?? []
}

export async function listCierres(): Promise<CierreMensualRead[]> {
  const { data } = await client.get<CierreMensualRead[]>('/audit-fiscal/cierres')
  return data ?? []
}
