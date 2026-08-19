/**
 * Local API type helpers.
 *
 * `src/types/api.d.ts` (openapi-typescript, generated from the production
 * OpenAPI) is the single source of truth for endpoint payloads. A few small
 * hand-written types live here because the backend schema does not model them
 * directly (token envelopes returned by login/refresh) or because we only need
 * a narrow view (auth user). Keep this file minimal.
 */
import type { components } from '@/types/api.d'

export type UsuarioRead = components['schemas']['UsuarioRead']

/** Envelope returned by POST /auth/login and POST /auth/refresh. */
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  rol: string
}

export interface AnaliticosPeriodo {
  desde?: string
  hasta?: string
}

export interface AnaliticosResumen {
  desde: string
  hasta: string
  ventas_total: string
  cantidad_ventas: number
  unidades_vendidas: string
  ticket_promedio: string
  margen_total: string
  gastos_total: string
  resultado_neto: string
  unidades_periodo_anterior: string
  ticket_periodo_anterior: string
  ventas_periodo_anterior: string
  margen_periodo_anterior: string
  gastos_periodo_anterior: string
  resultado_periodo_anterior: string
}
