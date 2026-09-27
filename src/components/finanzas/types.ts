export interface SociaDisplay {
  id: number
  nombre: string
  rol: string
  porcentaje: number
  es_fondo_taller: boolean
  telefono?: string
  email?: string
  banco?: string
  tipo_cuenta?: string
  numero_cuenta?: string
  titular_cuenta?: string
  activo: boolean
  notas?: string
}

export interface DistribucionDisplay {
  socia_id: number
  nombre_socia: string
  rol_socia: string
  porcentaje: number
  monto_bruto: number
  deduccion_anticipos: number
  monto_neto_pagar: number
  estado_pago: string
  fecha_pago?: string
  comprobante_transferencia?: string
  banco_destino?: string
}

export interface LiquidacionDisplay {
  id: number
  codigo: string
  periodo: string
  fecha_cierre: string
  total_ventas_brutas: number
  costo_taller_insumos: number
  gastos_operativos: number
  utilidad_neta_total: number
  fondo_reinversion_monto: number
  utilidad_repartible: number
  estado: string
  distribucion: DistribucionDisplay[]
  observaciones?: string
  created_at: string
}

export interface AnticipoDisplay {
  id: number
  socia_id: number
  nombre_socia: string
  fecha: string
  monto: number
  concepto: string
  metodo_desembolso: string
  estado: string
  liquidacion_id: number | null
  comprobante?: string
  observaciones?: string
}

export function formatCOP(val: number): string {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}
