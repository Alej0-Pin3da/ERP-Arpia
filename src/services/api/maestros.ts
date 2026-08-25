/**
 * Maestros API — channels and payment methods catalogue.
 *
 * Backend tables maestros_canales_venta / maestros_metodos_pago are created
 * in Alembic 0010 and seeded idempotently. No dedicated REST endpoint exists
 * yet (planned for Fase 3). This service exposes the canonical lists as
 * static constants and tries a live fetch first, falling back to the static
 * set when the endpoint is unavailable (404).
 */
import { client } from '@/api/client'

export interface CanalVentaMaestro {
  codigo: string
  nombre: string
}

export interface MetodoPagoMaestro {
  codigo: string
  nombre: string
}

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

async function tryFetch<T>(path: string, fallback: T): Promise<T> {
  try {
    const { data } = await client.get<T>(path)
    return data
  } catch {
    return fallback
  }
}

export async function listCanales(): Promise<CanalVentaMaestro[]> {
  // Attempt live endpoint; fallback to static catalogue (Fase 3 will add REST)
  return tryFetch<CanalVentaMaestro[]>('/maestros/canales-venta', CANALES_VENTA)
}

export async function listMetodosPago(): Promise<MetodoPagoMaestro[]> {
  return tryFetch<MetodoPagoMaestro[]>('/maestros/metodos-pago', METODOS_PAGO)
}
