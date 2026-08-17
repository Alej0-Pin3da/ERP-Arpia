/**
 * Finanzas module mapper tests (PR8, spec MOD-3).
 *
 * Pure functions over the finanzas module (src/utils/finanzas.ts):
 *  - movimiento display: tipo labels/tags, list join with socio names
 *    ('—' fallback for null/missing), newest-first ledger order
 *  - movimiento form -> MovimientoCreate payload (socio_id omitted when null;
 *    the backend does NOT require socio_id even for Retiro — verified in
 *    backend/app/services/finanzas.py, which only 400s on a nonexistent id)
 *  - liquidacion form -> LiquidacionCreate payload (notas omitted when empty)
 *  - liquidacion result -> per-socio rows (socio name, monto share)
 *  - socio form -> create/update payloads, and the sum-to-100 progress helper
 */
import { describe, expect, it } from 'vitest'

import {
  TIPO_MOVIMIENTO,
  buildLiquidacionPayload,
  buildLiquidacionRows,
  buildMovimientoPayload,
  buildMovimientoRows,
  buildMovimientoUpdatePayload,
  buildSocioPayload,
  buildSocioUpdatePayload,
  sumaParticipacion,
  tipoMovimientoLabel,
  tipoMovimientoTagType,
} from '@/utils/finanzas'
import type { components } from '@/types/api.d'

type MovimientoRead = components['schemas']['MovimientoRead']
type SocioConfiguracionRead = components['schemas']['SocioConfiguracionRead']

const SOCIOS: SocioConfiguracionRead[] = [
  { id: 1, nombre: 'Ana María', porcentaje_participacion: '60.00' },
  { id: 2, nombre: 'Carlos Ruiz', porcentaje_participacion: '40.00' },
]

const MOVIMIENTOS: MovimientoRead[] = [
  {
    id: 1,
    fecha: '2026-08-01T10:00:00Z',
    tipo: 'Gasto',
    descripcion: 'Compra de arepas',
    monto: '50000.00',
    socio_id: null,
    estado: 'activo',
    liquidacion_id: null,
  },
  {
    id: 2,
    fecha: '2026-08-02T12:00:00Z',
    tipo: 'Inversion',
    descripcion: 'Horno nuevo',
    monto: '1000000.00',
    socio_id: null,
    estado: 'activo',
    liquidacion_id: null,
  },
  {
    id: 3,
    fecha: '2026-08-03T15:00:00Z',
    tipo: 'Retiro',
    descripcion: 'Liquidación abc',
    monto: '30000.00',
    socio_id: 1,
    estado: 'activo',
    liquidacion_id: 'abc00',
  },
]

describe('finanzas mappers (MOD-3)', () => {
  it('exposes the three selectable movimiento types', () => {
    expect(TIPO_MOVIMIENTO).toEqual(['Gasto', 'Inversion', 'Retiro'])
  })

  it('labels and tags each movimiento tipo (accented Inversión, unknown passthrough)', () => {
    expect(tipoMovimientoLabel('Gasto')).toBe('Gasto')
    expect(tipoMovimientoLabel('Inversion')).toBe('Inversión')
    expect(tipoMovimientoLabel('Retiro')).toBe('Retiro')
    expect(tipoMovimientoLabel('Otro')).toBe('Otro')

    expect(tipoMovimientoTagType('Gasto')).toBe('danger')
    expect(tipoMovimientoTagType('Inversion')).toBe('primary')
    expect(tipoMovimientoTagType('Retiro')).toBe('warn')
    expect(tipoMovimientoTagType('Otro')).toBe('info')
  })

  it('builds list rows with joined socio names and the latest movement first', () => {
    const rows = buildMovimientoRows(MOVIMIENTOS, SOCIOS)

    expect(rows).toHaveLength(3)
    // Newest first (ledger order) — the backend lists id ASC.
    expect(rows.map((r) => r.id)).toEqual([3, 2, 1])

    const retiro = rows[0]
    expect(retiro.socio).toBe('Ana María')
    expect(retiro.tipo).toBe('Retiro')
    expect(retiro.monto).toBe('30000.00')
    expect(retiro.liquidacion_id).toBe('abc00')

    // Movements without a socio degrade to an em dash.
    expect(rows[1].socio).toBe('—')
    expect(rows[2].socio).toBe('—')
  })

  it('degrades to an em dash when a socio id has no matching row', () => {
    const rows = buildMovimientoRows(
      [{ ...MOVIMIENTOS[2], socio_id: 999 }],
      SOCIOS,
    )
    expect(rows[0].socio).toBe('—')
  })

  it('maps the create form to the MovimientoCreate payload, omitting a null socio_id', () => {
    expect(
      buildMovimientoPayload({ tipo: 'Gasto', descripcion: '  Arriendo  ', monto: 800000, socio_id: null }),
    ).toEqual({ tipo: 'Gasto', descripcion: 'Arriendo', monto: 800000 })

    expect(
      buildMovimientoPayload({ tipo: 'Retiro', descripcion: 'Retiro a socio', monto: 150000, socio_id: 1 }),
    ).toEqual({ tipo: 'Retiro', descripcion: 'Retiro a socio', monto: 150000, socio_id: 1 })
  })

  it('maps the edit form to the MovimientoUpdate payload (fecha/tipo/descripcion/monto/socio)', () => {
    expect(
      buildMovimientoUpdatePayload({
        fecha: '2026-08-01T10:00:00',
        tipo: 'Gasto',
        descripcion: '  Arriendo corregido  ',
        monto: 800000,
        socio_id: 2,
      }),
    ).toEqual({
      fecha: '2026-08-01T10:00:00',
      tipo: 'Gasto',
      descripcion: 'Arriendo corregido',
      monto: 800000,
      socio_id: 2,
    })
  })

  it('omits a null socio_id and an empty fecha from the update payload', () => {
    expect(
      buildMovimientoUpdatePayload({
        fecha: '',
        tipo: 'Inversion',
        descripcion: 'Horno nuevo',
        monto: 1000000,
        socio_id: null,
      }),
    ).toEqual({ tipo: 'Inversion', descripcion: 'Horno nuevo', monto: 1000000 })
  })

  it('freezes monto/socio_id for liquidacion rows (FIN-2) — omitted from the payload', () => {
    expect(
      buildMovimientoUpdatePayload({
        fecha: '2026-08-03T15:00:00',
        tipo: 'Retiro',
        descripcion: 'Nota corregida',
        monto: 30000,
        socio_id: 1,
        frozenMontoSocio: true,
      }),
    ).toEqual({ fecha: '2026-08-03T15:00:00', tipo: 'Retiro', descripcion: 'Nota corregida' })
  })

  it('maps the liquidacion form to the LiquidacionCreate payload, omitting empty notas', () => {
    expect(buildLiquidacionPayload({ monto: 5000000, notas: '  ' })).toEqual({ monto: 5000000 })
    expect(buildLiquidacionPayload({ monto: 5000000, notas: 'Utilidades agosto' })).toEqual({
      monto: 5000000,
      notas: 'Utilidades agosto',
    })
  })

  it('maps settlement result rows to per-socio shares', () => {
    const rows = buildLiquidacionRows(MOVIMIENTOS, SOCIOS)

    expect(rows).toHaveLength(3)
    expect(rows[0]).toEqual({ socio: '—', monto: '50000.00' })
    expect(rows[2]).toEqual({ socio: 'Ana María', monto: '30000.00' })
  })

  it('maps the socio create/update payloads', () => {
    expect(buildSocioPayload({ nombre: '  Luis Vega  ', porcentaje_participacion: 25 })).toEqual({
      nombre: 'Luis Vega',
      porcentaje_participacion: 25,
    })
    expect(buildSocioUpdatePayload(30)).toEqual({ porcentaje_participacion: 30 })
  })

  it('sums participations for the sum-to-100 progress (Decimal strings)', () => {
    expect(sumaParticipacion(SOCIOS)).toBe(100)
    expect(sumaParticipacion(SOCIOS.slice(0, 1))).toBe(60)
    expect(sumaParticipacion([])).toBe(0)
  })
})
