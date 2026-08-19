/**
 * Finanzas module mappers (PR8, spec MOD-3).
 *
 * Pure functions over the finanzas module:
 *  - `buildMovimientoRows`: MovimientoRead rows carry only socio_id — the
 *    partner name is joined client-side (GET /finanzas/socios) with an em
 *    dash fallback ('—') for null/missing socios; rows render newest first
 *    (the backend lists id ASC — a ledger reads better top-down).
 *  - `buildMovimientoPayload`: form model -> MovimientoCreate POST body.
 *    `socio_id` is OMITTED (not null) when unset. NOTE: the backend does NOT
 *    require socio_id for Retiro (backend app/schemas/finanzas.py default
 *    None; the service only 400s on a nonexistent id) — so the client keeps
 *    it optional for every tipo, with no per-tipo required rule.
 *  - `buildLiquidacionPayload`: settlement form -> LiquidacionCreate body
 *    (notas omitted when empty; liquidacion_id left to the server, which
 *    generates a fresh key).
 *  - `buildLiquidacionRows`: the POST /finanzas/liquidaciones result
 *    (list[MovimientoRead], one Retiro per socio) -> {socio, monto} rows.
 *  - `sumaParticipacion` + `buildSocioPayload`/`buildSocioUpdatePayload`:
 *    socios CRUD — the sum-to-100 progress display and the create/update
 *    bodies (PATCH only carries porcentaje_participacion per the backend
 *    SocioConfiguracionUpdate schema; nombre is not updatable).
 */
import type { components } from '@/types/api.d'
import { parseDecimal } from './format'

type MovimientoRead = components['schemas']['MovimientoRead']
type SocioConfiguracionRead = components['schemas']['SocioConfiguracionRead']
export type MovimientoCreate = components['schemas']['MovimientoCreate']
export type MovimientoUpdate = components['schemas']['MovimientoUpdate']
export type LiquidacionCreate = components['schemas']['LiquidacionCreate']
export type SocioConfiguracionCreate = components['schemas']['SocioConfiguracionCreate']
export type SocioConfiguracionUpdate = components['schemas']['SocioConfiguracionUpdate']

export type MovimientoTipo = 'Gasto' | 'Inversion' | 'Retiro'

/** Selectable movement types (MovimientoCreate.tipo enum). */
export const TIPO_MOVIMIENTO: readonly MovimientoTipo[] = ['Gasto', 'Inversion', 'Retiro']

const TIPO_LABELS: Record<string, string> = {
  Gasto: 'Gasto',
  Inversion: 'Inversión',
  Retiro: 'Retiro',
}

/** es-CO label for a movement type; unknown values pass through. */
export function tipoMovimientoLabel(tipo: string): string {
  return TIPO_LABELS[tipo] ?? tipo
}

/**
 * PrimeVue Tag severity per movement type: Gasto danger (money out),
 * Inversion primary (capital in), Retiro warn (partner payout).
 */
export function tipoMovimientoTagType(tipo: string): 'success' | 'warn' | 'danger' | 'info' | 'primary' {
  if (tipo === 'Gasto') return 'danger'
  if (tipo === 'Inversion') return 'primary'
  if (tipo === 'Retiro') return 'warn'
  return 'info'
}

/** A list-row movimiento with its joined socio label (MOD-3). */
export interface MovimientoRow {
  id: number
  /** Raw ISO datetime (formatted at render time). */
  fecha: string
  tipo: string
  descripcion: string
  /** Partner name, or an em dash when no socio is linked. */
  socio: string
  /** Raw Decimal-as-string amount (formatted at render time). */
  monto: string
  /** Settlement key when the row came from a liquidacion. */
  liquidacion_id: string | null
}

/** Map of socio id -> SocioConfiguracionRead for O(1) client-side joins. */
export function buildSociosById(socios: SocioConfiguracionRead[]): Map<number, SocioConfiguracionRead> {
  return new Map(socios.map((s) => [s.id, s]))
}

/** Partner display name for a join; null/missing socio degrades to '—'. */
export function socioNombre(
  sociosById: Map<number, SocioConfiguracionRead>,
  socioId: number | null,
): string {
  if (socioId === null) return '—'
  return sociosById.get(socioId)?.nombre ?? '—'
}

/**
 * MOD-3: join movimientos with socio names, degrading to '—' when the socio
 * is null or gone. Renders newest first (the backend lists id ASC).
 */
export function buildMovimientoRows(
  movimientos: MovimientoRead[],
  socios: SocioConfiguracionRead[],
): MovimientoRow[] {
  const sociosById = buildSociosById(socios)

  return [...movimientos]
    .sort((a, b) => b.id - a.id)
    .map((m) => ({
      id: m.id,
      fecha: m.fecha,
      tipo: m.tipo,
      descripcion: m.descripcion,
      socio: socioNombre(sociosById, m.socio_id),
      monto: m.monto,
      liquidacion_id: m.liquidacion_id,
    }))
}

/** The create form model (maps to MovimientoCreate via buildMovimientoPayload). */
export interface MovimientoPayloadInput {
  tipo: MovimientoTipo
  descripcion: string
  /** Money amount > 0 (el-input-number value). */
  monto: number
  /** Optional partner; omitted from the payload when null (backend-optional). */
  socio_id: number | null
}

/**
 * MOD-3: map the create form to the MovimientoCreate POST body. `socio_id` is
 * omitted (not null) when unset; the backend does not require it for any tipo.
 */
export function buildMovimientoPayload(form: MovimientoPayloadInput): MovimientoCreate {
  return {
    tipo: form.tipo,
    descripcion: form.descripcion.trim(),
    monto: form.monto,
    ...(form.socio_id !== null ? { socio_id: form.socio_id } : {}),
  }
}

/** The edit form model (maps to MovimientoUpdate via buildMovimientoUpdatePayload). */
export interface MovimientoUpdatePayloadInput {
  /** ISO datetime as picked; omitted from the payload when empty. */
  fecha: string | null
  tipo: MovimientoTipo
  descripcion: string
  /** Money amount; omitted when null (should only happen for frozen rows). */
  monto: number | null
  /** Optional partner; omitted from the payload when null. */
  socio_id: number | null
  /** True for liquidacion-born rows: monto/socio are frozen server-side
   *  (FIN-2 -> 422), so they are NEVER sent in the PATCH body. */
  frozenMontoSocio?: boolean
}

/**
 * T9: map the edit form to the MovimientoUpdate PATCH body. Only the fields
 * the backend accepts for a movement are included: fecha/tipo/descripcion
 * always (when present), monto/socio_id ONLY when the row is not a
 * liquidacion-born one (FIN-2 — sending them would 422 server-side).
 */
export function buildMovimientoUpdatePayload(
  form: MovimientoUpdatePayloadInput,
): MovimientoUpdate {
  const payload: MovimientoUpdate = {}
  if (form.fecha !== null && form.fecha !== '') {
    payload.fecha = form.fecha
  }
  payload.tipo = form.tipo
  payload.descripcion = form.descripcion.trim()
  if (form.frozenMontoSocio !== true) {
    if (form.monto !== null) {
      payload.monto = form.monto
    }
    if (form.socio_id !== null) {
      payload.socio_id = form.socio_id
    }
  }
  return payload
}

/** The settlement form model (maps to LiquidacionCreate). */
export interface LiquidacionPayloadInput {
  /** Money amount to distribute across socios (> 0). */
  monto: number
  notas: string
}

/** MOD-3: settlement form -> LiquidacionCreate body; empty notas omitted. */
export function buildLiquidacionPayload(form: LiquidacionPayloadInput): LiquidacionCreate {
  const payload: LiquidacionCreate = { monto: form.monto }
  const notas = form.notas.trim()
  if (notas !== '') {
    payload.notas = notas
  }
  return payload
}

/** A settlement result row: one partner share (MOD-3). */
export interface LiquidacionRow {
  /** Partner name, or '—' when the row has no linked socio. */
  socio: string
  /** Raw Decimal-as-string share (formatted at render time). */
  monto: string
}

/**
 * MOD-3: map the POST /finanzas/liquidaciones result (list[MovimientoRead],
 * one Retiro per socio) to {socio, monto} rows for the result table.
 */
export function buildLiquidacionRows(
  movimientos: MovimientoRead[],
  socios: SocioConfiguracionRead[],
): LiquidacionRow[] {
  const sociosById = buildSociosById(socios)
  return movimientos.map((m) => ({
    socio: socioNombre(sociosById, m.socio_id),
    monto: m.monto,
  }))
}

/**
 * MOD-3: sum of partner participations (Decimal-as-string aware) for the
 * sum-to-100 progress display ("current sum vs 100").
 */
export function sumaParticipacion(socios: SocioConfiguracionRead[]): number {
  return socios.reduce((sum, s) => sum + (parseDecimal(s.porcentaje_participacion) ?? 0), 0)
}

/** The socio create form model (maps to SocioConfiguracionCreate). */
export interface SocioPayloadInput {
  nombre: string
  /** Share percentage > 0 (el-input-number value). */
  porcentaje_participacion: number
}

/** MOD-3: socio create form -> SocioConfiguracionCreate body. */
export function buildSocioPayload(form: SocioPayloadInput): SocioConfiguracionCreate {
  return {
    nombre: form.nombre.trim(),
    porcentaje_participacion: form.porcentaje_participacion,
  }
}

/** MOD-3: socio edit form -> SocioConfiguracionUpdate body (percentage only). */
export function buildSocioUpdatePayload(porcentaje: number): SocioConfiguracionUpdate {
  return { porcentaje_participacion: porcentaje }
}
