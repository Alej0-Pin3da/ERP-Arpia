<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Dialog from 'primevue/dialog'
import Slider from 'primevue/slider'
import NuevaLiquidacionModal from '@/components/atelier/NuevaLiquidacionModal.vue'
import DetalleLiquidacionModal from '@/components/atelier/DetalleLiquidacionModal.vue'
import GestionSociasModal from '@/components/atelier/GestionSociasModal.vue'
import NuevoAnticipoModal from '@/components/atelier/NuevoAnticipoModal.vue'
import { showToast } from '@/utils/toast'
import { useSocios } from '@/composables/useSocios'
import { useFinanzas } from '@/composables/useFinanzas'
import * as movimientosApi from '@/services/api/movimientos'

/** REAL display shapes: backend payloads normalized for this view. */
interface SociaDisplay {
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
interface DistribucionDisplay {
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
interface LiquidacionDisplay {
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
interface AnticipoDisplay {
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

const sociosApi = useSocios()
const finanzasApi = useFinanzas()

// REAL state (populated via API)
const sociasList = ref<SociaDisplay[]>([])
const liquidacionesList = ref<LiquidacionDisplay[]>([])
const anticiposList = ref<AnticipoDisplay[]>([])
const movimientosList = ref<movimientosApi.MovimientoRead[]>([])
const cargando = ref(false)

function normalizeSocia(raw: Record<string, unknown>): SociaDisplay {
  return {
    id: raw.id as number,
    nombre: raw.nombre as string,
    rol: (raw.rol as string) ?? 'Socia Atelier',
    porcentaje: Number(raw.porcentaje_participacion ?? raw.porcentaje ?? 0),
    es_fondo_taller: Boolean(raw.es_fondo_taller),
    telefono: raw.telefono as string | undefined,
    email: raw.email as string | undefined,
    banco: raw.banco as string | undefined,
    tipo_cuenta: raw.tipo_cuenta as string | undefined,
    numero_cuenta: raw.numero_cuenta as string | undefined,
    titular_cuenta: raw.titular_cuenta as string | undefined,
    activo: raw.activo !== false,
    notas: raw.notas as string | undefined,
  }
}

function normalizeLiquidacion(raw: Record<string, unknown>): LiquidacionDisplay {
  const dist = (raw.distribucion as unknown[] | undefined) ?? []
  return {
    id: raw.id as number,
    codigo: (raw.codigo as string) ?? '',
    periodo: (raw.periodo as string) ?? '',
    fecha_cierre: raw.fecha_cierre as string,
    total_ventas_brutas: Number(raw.total_ventas_brutas ?? 0),
    costo_taller_insumos: Number(raw.costo_taller_insumos ?? 0),
    gastos_operativos: Number(raw.gastos_operativos ?? 0),
    utilidad_neta_total: Number(raw.utilidad_neta_total ?? 0),
    fondo_reinversion_monto: Number(raw.fondo_reinversion_monto ?? 0),
    utilidad_repartible: Number(raw.utilidad_repartible ?? 0),
    estado: raw.estado as string,
    distribucion: dist.map((d: unknown) => {
      const dd = d as Record<string, unknown>
      return {
        socia_id: dd.socia_id as number,
        nombre_socia: (dd.socia_nombre as string) ?? (dd.nombre_socia as string) ?? '',
        rol_socia: (dd.rol_socia as string) ?? '',
        porcentaje: Number(dd.porcentaje ?? 0),
        monto_bruto: Number(dd.monto_bruto ?? 0),
        deduccion_anticipos: Number(dd.deduccion_anticipos ?? 0),
        monto_neto_pagar: Number((dd as Record<string, unknown>).monto_neto ?? dd.monto_neto_pagar ?? 0),
        estado_pago: (dd.estado_pago as string) ?? 'PENDIENTE',
        fecha_pago: dd.fecha_pago as string | undefined,
        comprobante_transferencia: dd.comprobante_transferencia as string | undefined,
        banco_destino: dd.banco_destino as string | undefined,
      }
    }),
    observaciones: raw.observaciones as string | undefined,
    created_at: (raw.created_at as string) ?? (raw.creado_en as string) ?? new Date().toISOString(),
  }
}

function normalizeAnticipo(raw: Record<string, unknown>): AnticipoDisplay {
  return {
    id: raw.id as number,
    socia_id: raw.socia_id as number,
    nombre_socia: (raw.socia_nombre as string) ?? (raw.nombre_socia as string) ?? '',
    fecha: raw.fecha as string,
    monto: Number(raw.monto ?? 0),
    concepto: (raw.concepto as string) ?? 'Adelanto',
    metodo_desembolso: (raw.metodo_desembolso as string) ?? 'Transferencia Bancaria',
    estado: raw.estado as string,
    liquidacion_id: (raw.liquidacion_id as number | null) ?? null,
    comprobante: raw.comprobante as string | undefined,
    observaciones: raw.observaciones as string | undefined,
  }
}

async function cargarDatos() {
  cargando.value = true
  try {
    const [socRes, liqRes, antRes, movRes] = await Promise.all([
      sociosApi.list({ limit: 100, offset: 0 }),
      finanzasApi.listLiquidaciones({ limit: 100, offset: 0 }),
      finanzasApi.listAnticipos({ limit: 100, offset: 0 }),
      movimientosApi.listMovimientos({ limit: 100, offset: 0 }).catch(() => ({ items: [], total: 0 })),
    ])
    sociasList.value = (socRes.items as unknown as Record<string, unknown>[]).map(normalizeSocia)
    liquidacionesList.value = (liqRes.items as unknown as Record<string, unknown>[]).map(normalizeLiquidacion)
    anticiposList.value = (antRes.items as unknown as Record<string, unknown>[]).map(normalizeAnticipo)
    movimientosList.value = (movRes.items as unknown as movimientosApi.MovimientoRead[]) ?? []
  } catch {
    // keep previous state on error
  } finally {
    cargando.value = false
  }
}

onMounted(() => {
  void cargarDatos()
})

// Unified lists — REAL API only

// Subtabs
type TabType = 'liquidaciones' | 'socias' | 'anticipos' | 'movimientos' | 'simulador'
const activeTab = ref<TabType>('liquidaciones')

// Search and Filter states
const searchLiquidaciones = ref('')
const filterEstadoLiquidacion = ref('TODOS')
const searchAnticipos = ref('')
const filterMovTipo = ref('TODOS')
const filterMovEstado = ref('TODOS')

// Modals state
const showNuevaLiqModal = ref(false)
const showDetalleLiqModal = ref(false)
const showGestionSociaModal = ref(false)
const showNuevoAnticipoModal = ref(false)

const liquidacionSeleccionadaEditar = ref<LiquidacionDisplay | null>(null)
const liquidacionSeleccionadaDetalle = ref<LiquidacionDisplay | null>(null)
const sociaSeleccionadaEditar = ref<SociaDisplay | null>(null)
const anticipoSeleccionadoEditar = ref<AnticipoDisplay | null>(null)

// Deletion confirmation modals
const showDeleteLiqModal = ref(false)
const liquidacionAEliminar = ref<LiquidacionDisplay | null>(null)

const showDeleteSociaModal = ref(false)
const sociaAEliminar = ref<SociaDisplay | null>(null)

const showDeleteAnticipoModal = ref(false)
const anticipoAEliminar = ref<AnticipoDisplay | null>(null)
const descontandoAnticipoId = ref<number | null>(null)

// Break-even simulator parameters
const precioPromedioCorse = ref(450000)
const costoInsumosPromedio = ref(130000)
const horasManoObraPromedio = ref(6)
const costoHoraTaller = ref(15000)
const gastosOperativosSimulator = ref(2100000)
const prendasMetaSimuladas = ref(15)

const margenContribucionUnitario = computed(() => {
  const costoTotalUnitario = costoInsumosPromedio.value + horasManoObraPromedio.value * costoHoraTaller.value
  return Math.max(1, precioPromedioCorse.value - costoTotalUnitario)
})

const puntoEquilibrioUnidades = computed(() => {
  return Math.ceil(gastosOperativosSimulator.value / margenContribucionUnitario.value)
})

const utilidadSimulada = computed(() => {
  const ingresoSim = prendasMetaSimuladas.value * margenContribucionUnitario.value
  return Math.max(0, ingresoSim - gastosOperativosSimulator.value)
})

function formatCOP(val: number): string {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

// Filtered liquidaciones
const liquidacionesFiltradas = computed(() => {
  let list = [...liquidacionesList.value]

  if (searchLiquidaciones.value.trim()) {
    const q = searchLiquidaciones.value.trim().toLowerCase()
    list = list.filter(
      (l) =>
        (l.codigo ?? '').toLowerCase().includes(q) ||
        (l.periodo ?? '').toLowerCase().includes(q) ||
        (l.observaciones ?? '').toLowerCase().includes(q) ||
        (l.distribucion ?? []).some((d) => (d.nombre_socia ?? '').toLowerCase().includes(q)),
    )
  }

  if (filterEstadoLiquidacion.value !== 'TODOS') {
    list = list.filter((l) => l.estado === filterEstadoLiquidacion.value)
  }

  return list
})

// Filtered anticipos
const anticiposFiltrados = computed(() => {
  let list = [...anticiposList.value]

  if (searchAnticipos.value.trim()) {
    const q = searchAnticipos.value.trim().toLowerCase()
    list = list.filter(
      (a) =>
        a.nombre_socia.toLowerCase().includes(q) ||
        a.concepto.toLowerCase().includes(q) ||
        (a.comprobante || '').toLowerCase().includes(q),
    )
  }

  return list
})

// Movimientos — solo-lectura; el backend soporta filtros tipo/estado (sin rango de fechas)
const movimientosFiltrados = computed(() => {
  let list = [...movimientosList.value]
  if (filterMovTipo.value !== 'TODOS') {
    list = list.filter((m) => m.tipo === filterMovTipo.value)
  }
  if (filterMovEstado.value !== 'TODOS') {
    list = list.filter((m) => m.estado === filterMovEstado.value)
  }
  return list
})

async function recargarMovimientos() {
  try {
    const r = await movimientosApi.listMovimientos({
      limit: 100,
      offset: 0,
      ...(filterMovTipo.value !== 'TODOS' ? { tipo: filterMovTipo.value as 'Gasto' | 'Inversion' | 'Retiro' } : {}),
      ...(filterMovEstado.value !== 'TODOS' ? { estado: filterMovEstado.value as 'draft' | 'confirmed' | 'cancelled' | 'reversed' } : {}),
    })
    movimientosList.value = r.items ?? []
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al cargar movimientos'
    showToast('error', 'Error', msg)
  }
}

// Total % of active socias
const sumaPorcentajesSocias = computed(() => {
  return sociasList.value.filter((s) => s.activo).reduce((acc, s) => acc + s.porcentaje, 0)
})

// KPI aggregates over the active data source
const totalHistoricoFacturado = computed(() => liquidacionesList.value.reduce((a, l) => a + l.total_ventas_brutas, 0))
const totalHistoricoFondo = computed(() => liquidacionesList.value.reduce((a, l) => a + l.fondo_reinversion_monto, 0))
// Socias de reparto dinámicas (primeras 2 activas no-fondo): en REAL los ids
// no son 2/3 ni los nombres Margara/Valqui, así que nada puede hardcodearlos.
const sociasReparto = computed(() =>
  (sociasList.value as any[]).filter((s) => !s.es_fondo_taller && s.activo !== false).slice(0, 2),
)
function totalRepartidoSocia(sociaId: number | undefined): number {
  if (sociaId == null) return 0
  return liquidacionesList.value.reduce((a, l) => {
    const item = l.distribucion.find((d) => d.socia_id === sociaId)
    return a + (item ? item.monto_neto_pagar : 0)
  }, 0)
}
const totalRepartidoMargara = computed(() => totalRepartidoSocia((sociasReparto.value[0] as any)?.id))
const totalRepartidoValqui = computed(() => totalRepartidoSocia((sociasReparto.value[1] as any)?.id))
function nombreSociaReparto(i: number, fallback: string): string {
  return ((sociasReparto.value[i] as any)?.nombre as string) ?? fallback
}
function porcentajeSociaReparto(i: number, fallback: number): number {
  const s = sociasReparto.value[i] as any
  return Number(s?.porcentaje ?? s?.porcentaje_participacion ?? fallback) || fallback
}
function itemDistribucion(l: LiquidacionDisplay, sociaId: number | undefined) {
  if (sociaId == null) return undefined
  return l.distribucion.find((d) => d.socia_id === sociaId)
}
const totalAnticiposPendientes = computed(() =>
  anticiposList.value.filter((a) => a.estado === 'PENDIENTE_DESCUENTO').reduce((a, x) => a + x.monto, 0),
)

// Historical income per socia
function getIngresoHistoricoSocia(sociaId: number): number {
  return liquidacionesList.value.reduce((acc, l) => {
    const item = l.distribucion.find((d) => d.socia_id === sociaId)
    return acc + (item ? item.monto_neto_pagar : 0)
  }, 0)
}

function getAnticiposPendientesSocia(sociaId: number): number {
  return anticiposList.value
    .filter((a) => a.socia_id === sociaId && a.estado === 'PENDIENTE_DESCUENTO')
    .reduce((acc, a) => acc + a.monto, 0)
}

// Liquidaciones actions
function abrirNuevaLiquidacion() {
  liquidacionSeleccionadaEditar.value = null
  showNuevaLiqModal.value = true
}

function abrirEditarLiquidacion(liq: LiquidacionDisplay) {
  liquidacionSeleccionadaEditar.value = liq
  showNuevaLiqModal.value = true
}

function abrirDetalleLiquidacion(liq: LiquidacionDisplay) {
  liquidacionSeleccionadaDetalle.value = liq
  showDetalleLiqModal.value = true
}

function solicitarEliminarLiquidacion(liq: LiquidacionDisplay) {
  liquidacionAEliminar.value = liq
  showDeleteLiqModal.value = true
}

async function confirmarEliminarLiquidacion() {
  if (liquidacionAEliminar.value) {
    const cod = liquidacionAEliminar.value.codigo
    const id = liquidacionAEliminar.value.id
    try {
      await finanzasApi.removeLiquidacion(id)
      await cargarDatos()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error al eliminar liquidación'
      showToast('error', 'Error', msg)
      return
    }
    showToast('info', 'Liquidación Eliminada', `La liquidación ${cod} ha sido eliminada del historial.`)
    liquidacionAEliminar.value = null
    showDeleteLiqModal.value = false
  }
}

async function cambiarEstadoLiq(liq: LiquidacionDisplay, nuevoEstado: 'BORRADOR' | 'APROBADA' | 'PAGADA') {
  try {
    await finanzasApi.transitionLiquidacion(liq.id, { estado: nuevoEstado })
    // Siempre refetch: el parcheo optimista quedaba stale si el shape deriva.
    await cargarDatos()
    showToast('success', 'Estado Actualizado', `Liquidación ${liq.codigo} marcada como ${nuevoEstado}.`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Transición no permitida'
    showToast('error', 'Error', msg)
  }
}

// Socias actions
function abrirNuevaSocia() {
  sociaSeleccionadaEditar.value = null
  showGestionSociaModal.value = true
}

function abrirEditarSocia(soc: SociaDisplay) {
  sociaSeleccionadaEditar.value = soc
  showGestionSociaModal.value = true
}

function solicitarEliminarSocia(soc: SociaDisplay) {
  sociaAEliminar.value = soc
  showDeleteSociaModal.value = true
}

async function confirmarEliminarSocia() {
  if (sociaAEliminar.value) {
    const nom = sociaAEliminar.value.nombre
    const id = sociaAEliminar.value.id
    try {
      await sociosApi.remove(id)
      await cargarDatos()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error al eliminar socia'
      showToast('error', 'Error', msg)
      return
    }
    showToast('info', 'Socia Eliminada', `El registro de ${nom} ha sido removido.`)
    sociaAEliminar.value = null
    showDeleteSociaModal.value = false
  }
}

async function toggleActivoSocia(s: SociaDisplay) {
  try {
    await sociosApi.update(s.id, { activo: !s.activo })
    await cargarDatos()
    showToast('success', 'Socia Actualizada', `${s.nombre} ${!s.activo ? 'activada' : 'desactivada'}.`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al actualizar socia'
    showToast('error', 'Error', msg)
  }
}

// Anticipos actions
function abrirNuevoAnticipo() {
  anticipoSeleccionadoEditar.value = null
  showNuevoAnticipoModal.value = true
}

function abrirEditarAnticipo(ant: AnticipoDisplay) {
  anticipoSeleccionadoEditar.value = ant
  showNuevoAnticipoModal.value = true
}

async function marcarAnticipoDescontado(ant: AnticipoDisplay) {
  if (descontandoAnticipoId.value === ant.id) return
  // Camino único: PATCH /anticipos/{id}/descuento exige liquidacion_id.
  // Sin liquidación no hay a qué imputar el descuento — se avisa y no se
  // llama a ningún endpoint (el fallback a transitionAnticipo hacía doble
  // escritura potencial: descontar + transición suelta sin vínculo).
  if (!ant.liquidacion_id) {
    showToast('warn', 'Falta liquidación', 'Seleccioná una liquidación para descontar el anticipo.')
    return
  }
  descontandoAnticipoId.value = ant.id
  try {
    await finanzasApi.descontarAnticipo(ant.id, ant.liquidacion_id)
    await cargarDatos()
    showToast('success', 'Anticipo Actualizado', `Anticipo marcado como DESCONTADO.`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al descontar anticipo'
    showToast('error', 'Error', msg)
  } finally {
    descontandoAnticipoId.value = null
  }
}

function solicitarEliminarAnticipo(ant: AnticipoDisplay) {
  anticipoAEliminar.value = ant
  showDeleteAnticipoModal.value = true
}

async function confirmarEliminarAnticipo() {
  if (anticipoAEliminar.value) {
    const id = anticipoAEliminar.value.id
    try {
      await finanzasApi.removeAnticipo(id)
      await cargarDatos()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error al eliminar anticipo'
      showToast('error', 'Error', msg)
      return
    }
    showToast('info', 'Anticipo Eliminado', `El anticipo ha sido eliminado.`)
    anticipoAEliminar.value = null
    showDeleteAnticipoModal.value = false
  }
}

function imprimirBalance() {
  showToast('info', 'Balance Preparado', 'Generando balance financiero oficial de Atelier Arpía.')
  if (typeof window !== 'undefined') {
    window.print()
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-stone-800 pb-4">
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide m-0">
            Reparto de Socias & Finanzas Atelier
          </h1>
          <span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-mono text-[10px] font-bold">
            Reparto según socias registradas
          </span>
        </div>
        <p class="text-xs text-stone-400 mt-1 font-mono m-0">
          Módulo integral para gestión de liquidaciones de utilidades, deducción de insumos, fondo de taller, anticipos y perfiles de socias.
        </p>
      </div>

      <!-- Main Quick Actions -->
      <div class="flex flex-wrap items-center gap-2">
        <Button
          label="Imprimir Balance"
          icon="pi pi-print"
          size="small"
          severity="secondary"
          outlined
          class="text-xs"
          @click="imprimirBalance"
        />
        <Button
          label="Nuevo Anticipo"
          icon="pi pi-dollar"
          size="small"
          class="p-button-outlined p-button-warning text-xs font-semibold"
          @click="abrirNuevoAnticipo"
        />
        <Button
          label="Nueva Liquidación"
          icon="pi pi-plus"
          size="small"
          class="p-button-warning text-xs font-semibold px-3"
          @click="abrirNuevaLiquidacion"
        />
      </div>
    </div>

    <!-- Financial KPI Summary Cards (4 Columns) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 font-mono">
      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-3.5 flex flex-col justify-between">
        <div>
          <div class="text-[10px] text-stone-400 uppercase tracking-wider">Ventas Totales Facturadas</div>
          <div class="text-lg font-serif font-bold text-emerald-400 mt-1">
            {{ formatCOP(totalHistoricoFacturado) }}
          </div>
        </div>
        <div class="text-[10px] text-stone-500 mt-2 border-t border-stone-800/80 pt-1.5 flex justify-between">
          <span>Liquidaciones:</span>
          <span class="text-stone-300 font-bold">{{ liquidacionesList.length }} periodos</span>
        </div>
      </div>

      <div class="rounded-xl border border-amber-500/30 bg-amber-950/20 p-3.5 flex flex-col justify-between">
        <div>
          <div class="text-[10px] text-amber-300/90 uppercase tracking-wider font-bold">🏛️ Fondo Taller (40%)</div>
          <div class="text-lg font-serif font-bold text-amber-300 mt-1">
            {{ formatCOP(totalHistoricoFondo) }}
          </div>
        </div>
        <div class="text-[10px] text-amber-400/70 mt-2 border-t border-amber-500/20 pt-1.5 flex justify-between">
          <span>Reserva Textil & Maquinaria</span>
        </div>
      </div>

      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-3.5 flex flex-col justify-between">
        <div>
          <div class="text-[10px] text-stone-400 uppercase tracking-wider">🪡 {{ nombreSociaReparto(0, '—') }} ({{ porcentajeSociaReparto(0, 0) }}%)</div>
          <div class="text-lg font-serif font-bold text-stone-100 mt-1">
            {{ formatCOP(totalRepartidoMargara) }}
          </div>
        </div>
        <div class="text-[10px] text-stone-500 mt-2 border-t border-stone-800/80 pt-1.5 flex justify-between">
          <span>Confección & Taller</span>
        </div>
      </div>

      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-3.5 flex flex-col justify-between">
        <div>
          <div class="text-[10px] text-stone-400 uppercase tracking-wider">🎨 {{ nombreSociaReparto(1, '—') }} ({{ porcentajeSociaReparto(1, 0) }}%)</div>
          <div class="text-lg font-serif font-bold text-stone-100 mt-1">
            {{ formatCOP(totalRepartidoValqui) }}
          </div>
        </div>
        <div class="text-[10px] text-stone-500 mt-2 border-t border-stone-800/80 pt-1.5 flex justify-between">
          <span>Diseño & Dirección</span>
        </div>
      </div>

      <div class="rounded-xl border border-stone-800 bg-stone-900/60 p-3.5 flex flex-col justify-between">
        <div>
          <div class="text-[10px] text-stone-400 uppercase tracking-wider">Anticipos Pendientes</div>
          <div class="text-lg font-serif font-bold text-rose-400 mt-1">
            {{ formatCOP(totalAnticiposPendientes) }}
          </div>
        </div>
        <div class="text-[10px] text-stone-500 mt-2 border-t border-stone-800/80 pt-1.5 flex justify-between">
          <span>Por descontar en cierre</span>
        </div>
      </div>
    </div>

    <!-- Navigation Subtabs -->
    <div class="flex items-center gap-2 border-b border-stone-800 overflow-x-auto pb-1 text-xs font-mono">
      <button
        class="px-4 py-2 rounded-t-lg transition-all flex items-center gap-2 font-bold cursor-pointer"
        :class="activeTab === 'liquidaciones' ? 'bg-amber-500/10 text-amber-300 border-b-2 border-amber-400' : 'text-stone-400 hover:text-stone-200'"
        @click="activeTab = 'liquidaciones'"
      >
        <i class="pi pi-list" />
        Liquidaciones & Cierres ({{ liquidacionesList.length }})
      </button>

      <button
        class="px-4 py-2 rounded-t-lg transition-all flex items-center gap-2 font-bold cursor-pointer"
        :class="activeTab === 'socias' ? 'bg-amber-500/10 text-amber-300 border-b-2 border-amber-400' : 'text-stone-400 hover:text-stone-200'"
        @click="activeTab = 'socias'"
      >
        <i class="pi pi-users" />
        Perfiles de Socias & Cuentas ({{ sociasList.length }})
      </button>

      <button
        class="px-4 py-2 rounded-t-lg transition-all flex items-center gap-2 font-bold cursor-pointer"
        :class="activeTab === 'anticipos' ? 'bg-amber-500/10 text-amber-300 border-b-2 border-amber-400' : 'text-stone-400 hover:text-stone-200'"
        @click="activeTab = 'anticipos'"
      >
        <i class="pi pi-dollar" />
        Anticipos & Retiros ({{ anticiposList.length }})
      </button>

      <button
        class="px-4 py-2 rounded-t-lg transition-all flex items-center gap-2 font-bold cursor-pointer"
        :class="activeTab === 'movimientos' ? 'bg-amber-500/10 text-amber-300 border-b-2 border-amber-400' : 'text-stone-400 hover:text-stone-200'"
        @click="activeTab = 'movimientos'"
      >
        <i class="pi pi-wallet" />
        Movimientos ({{ movimientosList.length }})
      </button>

      <button
        class="px-4 py-2 rounded-t-lg transition-all flex items-center gap-2 font-bold cursor-pointer"
        :class="activeTab === 'simulador' ? 'bg-amber-500/10 text-amber-300 border-b-2 border-amber-400' : 'text-stone-400 hover:text-stone-200'"
        @click="activeTab = 'simulador'"
      >
        <i class="pi pi-chart-line" />
        Simulador Punto Equilibrio Textil
      </button>
    </div>

    <!-- TAB 1: LIQUIDACIONES DE PERIODO (CRUD) -->
    <div v-if="activeTab === 'liquidaciones'" class="space-y-4">
      <!-- Search & Filters -->
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800 text-xs">
        <div class="w-full sm:w-72 relative">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-stone-500 text-xs" />
          <InputText
            v-model="searchLiquidaciones"
            placeholder="Buscar por código, periodo, socia..."
            class="w-full pl-8 text-xs"
          />
        </div>

        <div class="flex items-center gap-2 w-full sm:w-auto">
          <span class="text-stone-400 text-xs font-mono">Estado:</span>
          <Dropdown
            v-model="filterEstadoLiquidacion"
            :options="[
              { label: 'Todos los Estados', value: 'TODOS' },
              { label: 'Totalmente Pagadas', value: 'PAGADA' },
              { label: 'Aprobadas', value: 'APROBADA' },
              { label: 'En Borrador', value: 'BORRADOR' },
            ]"
            option-label="label"
            option-value="value"
            class="text-xs w-44"
          />
          <Button
            label="Nueva Liquidación"
            icon="pi pi-plus"
            size="small"
            class="p-button-warning text-xs font-semibold whitespace-nowrap"
            @click="abrirNuevaLiquidacion"
          />
        </div>
      </div>

      <!-- Liquidaciones Table (desktop) + Cards (mobile) -->
      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden">
        <div class="hidden overflow-x-auto md:block">
          <table class="w-full min-w-[900px] text-xs text-left border-collapse">
            <thead>
              <tr class="bg-stone-950/90 border-b border-stone-800 text-[10px] font-mono uppercase text-stone-400">
                <th class="py-3 px-4 sticky left-0 z-10 bg-stone-950/95">Código & Periodo</th>
                <th class="py-3 px-3 text-right whitespace-nowrap">Ventas Brutas</th>
                <th class="py-3 px-3 text-right whitespace-nowrap">Costos / Gastos</th>
                <th class="py-3 px-3 text-right whitespace-nowrap">Utilidad Neta</th>
                <th class="py-3 px-3 text-center whitespace-nowrap">Fondo Taller (40%)</th>
                <th v-for="(s, i) in sociasReparto" :key="(s as any).id" class="py-3 px-3 text-center whitespace-nowrap">{{ (s as any).nombre }} ({{ porcentajeSociaReparto(i, 30) }}%)</th>
                <th class="py-3 px-3 text-center whitespace-nowrap">Estado</th>
                <th class="py-3 px-4 text-center whitespace-nowrap">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60 font-mono">
              <tr
                v-for="l in liquidacionesFiltradas"
                :key="l.id"
                class="hover:bg-stone-800/30 transition-colors"
              >
                <td class="py-3.5 px-4 sticky left-0 z-10 bg-stone-900/95">
                  <div class="font-bold text-amber-300 font-serif text-sm">{{ l.codigo }}</div>
                  <div class="text-stone-200 text-xs font-sans mt-0.5">{{ l.periodo }}</div>
                  <div class="text-[10px] text-stone-500">Cierre: {{ l.fecha_cierre }}</div>
                </td>

                <td class="py-3.5 px-3 text-right font-bold text-stone-100 whitespace-nowrap">
                  {{ formatCOP(l.total_ventas_brutas) }}
                </td>

                <td class="py-3.5 px-3 text-right text-stone-400 text-[11px] whitespace-nowrap">
                  <div>-{{ formatCOP(l.costo_taller_insumos) }} ins.</div>
                  <div>-{{ formatCOP(l.gastos_operativos) }} gast.</div>
                </td>

                <td class="py-3.5 px-3 text-right font-bold text-emerald-400 text-sm whitespace-nowrap">
                  {{ formatCOP(l.utilidad_neta_total) }}
                </td>

                <td class="py-3.5 px-3 text-center">
                  <span class="text-amber-300 font-bold text-xs">{{ formatCOP(l.fondo_reinversion_monto) }}</span>
                </td>

                <td v-for="(s, i) in sociasReparto" :key="(s as any).id" class="py-3.5 px-3 text-center">
                  <div class="text-stone-200 font-semibold text-xs">
                    {{ formatCOP(itemDistribucion(l, (s as any).id)?.monto_neto_pagar || 0) }}
                  </div>
                  <span
                    class="text-[9px] px-1.5 py-0.2 rounded"
                    :class="itemDistribucion(l, (s as any).id)?.estado_pago === 'PAGADO' ? 'bg-emerald-950 text-emerald-400' : 'bg-stone-800 text-amber-400'"
                  >
                    {{ itemDistribucion(l, (s as any).id)?.estado_pago || 'PENDIENTE' }}
                  </span>
                </td>

                <td class="py-3.5 px-3 text-center">
                  <button
                    class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider cursor-pointer hover:opacity-80 transition-opacity"
                    :class="{
                      'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': l.estado === 'PAGADA',
                      'bg-amber-500/20 text-amber-300 border border-amber-500/30': l.estado === 'APROBADA',
                      'bg-stone-800 text-stone-400 border border-stone-700': l.estado === 'BORRADOR',
                    }"
                    :title="'Click para cambiar estado (actual: ' + l.estado + ')'"
                    @click="cambiarEstadoLiq(l, l.estado === 'PAGADA' ? 'BORRADOR' : l.estado === 'BORRADOR' ? 'APROBADA' : 'PAGADA')"
                  >
                    {{ l.estado }}
                  </button>
                </td>

                <td class="py-3.5 px-4 text-center">
                  <div class="flex items-center justify-center gap-1.5">
                    <Button
                      icon="pi pi-eye"
                      size="small"
                      text
                      rounded
                      class="p-button-secondary text-amber-300 hover:bg-stone-800"
                      title="Ver Acta Oficial & Transferencias"
                      @click="abrirDetalleLiquidacion(l)"
                    />
                    <Button
                      icon="pi pi-trash"
                      size="small"
                      text
                      rounded
                      class="p-button-danger text-rose-400 hover:bg-rose-950/40"
                      title="Eliminar Liquidación"
                      @click="solicitarEliminarLiquidacion(l)"
                    />
                  </div>
                </td>
              </tr>

              <tr v-if="liquidacionesFiltradas.length === 0">
                <td colspan="9" class="py-8 text-center text-stone-500">
                  <i class="pi pi-inbox text-2xl mb-2 block" />
                  No se encontraron liquidaciones de socias con los filtros actuales.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Mobile cards: same liquidacionesFiltradas. No horizontal scroll. -->
        <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
          <div v-if="liquidacionesFiltradas.length === 0" class="text-center py-8 text-sm text-stone-500">No se encontraron liquidaciones de socias con los filtros actuales.</div>
          <div v-for="l in liquidacionesFiltradas" :key="l.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
            <div class="flex items-start justify-between gap-2 min-w-0">
              <div class="min-w-0">
                <div class="font-bold text-sm text-amber-300">{{ l.codigo }}</div>
                <div class="text-sm text-stone-200">{{ l.periodo }}</div>
                <div class="text-xs text-stone-500">Cierre: {{ l.fecha_cierre }}</div>
              </div>
              <button type="button" class="px-2 py-1 rounded-full text-xs font-bold uppercase tracking-wider shrink-0 min-h-[40px]" :class="{ 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': l.estado === 'PAGADA', 'bg-amber-500/20 text-amber-300 border border-amber-500/30': l.estado === 'APROBADA', 'bg-stone-800 text-stone-400 border border-stone-700': l.estado === 'BORRADOR' }" @click="cambiarEstadoLiq(l, l.estado === 'PAGADA' ? 'BORRADOR' : l.estado === 'BORRADOR' ? 'APROBADA' : 'PAGADA')">{{ l.estado }}</button>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Ventas brutas</span>
              <span class="font-mono font-bold text-stone-100">{{ formatCOP(l.total_ventas_brutas) }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Costos / gastos</span>
              <span class="font-mono text-stone-400">−{{ formatCOP(l.costo_taller_insumos) }} / −{{ formatCOP(l.gastos_operativos) }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Utilidad neta</span>
              <span class="font-mono font-bold text-emerald-400">{{ formatCOP(l.utilidad_neta_total) }}</span>
            </div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Fondo taller (40%)</span>
              <span class="font-mono font-bold text-amber-300">{{ formatCOP(l.fondo_reinversion_monto) }}</span>
            </div>
            <div class="space-y-1 border-t border-stone-800 pt-2">
              <div v-for="(s, i) in sociasReparto" :key="(s as any).id" class="flex items-center justify-between text-sm">
                <span class="text-stone-300">{{ (s as any).nombre }} ({{ porcentajeSociaReparto(i, 30) }}%)</span>
                <span class="font-mono font-semibold text-stone-100">{{ formatCOP(itemDistribucion(l, (s as any).id)?.monto_neto_pagar || 0) }}</span>
              </div>
            </div>
            <div class="flex gap-2 pt-1">
              <button type="button" class="flex-1 min-h-[40px] rounded-lg bg-stone-800 text-amber-300 text-sm font-semibold" @click="abrirDetalleLiquidacion(l)">Ver acta</button>
              <button type="button" class="min-w-[44px] min-h-[40px] px-3 rounded-lg border border-rose-800 text-rose-400" title="Eliminar Liquidación" @click="solicitarEliminarLiquidacion(l)"><i class="pi pi-trash text-xs" /></button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 2: PERFILES DE SOCIAS & CUENTAS (CRUD) -->
    <div v-if="activeTab === 'socias'" class="space-y-4">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800">
        <div>
          <div class="text-xs font-bold text-amber-300 uppercase font-mono">
            Estructura de Socias & Porcentajes de Participación
          </div>
          <div class="text-[11px] text-stone-400 font-mono mt-0.5">
            Suma total activa: <strong class="text-emerald-400">{{ sumaPorcentajesSocias }}%</strong>
            (Según porcentajes registrados de socias activas)
          </div>
        </div>

        <Button
          label="Añadir Nueva Socia"
          icon="pi pi-user-plus"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="abrirNuevaSocia"
        />
      </div>

      <!-- Socias Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          v-for="s in sociasList"
          :key="s.id"
          class="rounded-2xl border bg-stone-900/60 p-5 relative overflow-hidden flex flex-col justify-between transition-all"
          :class="s.activo ? 'border-stone-800 hover:border-amber-500/40' : 'border-stone-800/40 opacity-60'"
        >
          <div>
            <div class="flex items-center justify-between">
              <span class="px-2.5 py-1 rounded-full text-xs font-mono font-bold text-amber-300 bg-amber-500/20 border border-amber-500/30">
                {{ s.porcentaje }}% Participación
              </span>
              <span
                class="text-[10px] px-2 py-0.5 rounded font-mono font-bold"
                :class="s.activo ? 'bg-emerald-950 text-emerald-400' : 'bg-stone-800 text-stone-400'"
              >
                {{ s.activo ? 'Activa' : 'Inactiva' }}
              </span>
            </div>

            <div class="font-serif font-bold text-stone-100 text-base mt-3">{{ s.nombre }}</div>
            <div class="text-xs text-stone-400 font-mono mt-0.5">{{ s.rol }}</div>

            <div class="mt-4 pt-3 border-t border-stone-800/80 space-y-2 text-xs font-mono text-stone-300">
              <div class="flex items-center justify-between text-[11px]">
                <span class="text-stone-500">Banco / Plataforma:</span>
                <span class="font-bold text-stone-200">{{ s.banco || 'N/A' }}</span>
              </div>
              <div class="flex items-center justify-between text-[11px]">
                <span class="text-stone-500">N° Cuenta:</span>
                <span class="text-stone-300">{{ s.numero_cuenta || 'N/A' }} ({{ s.tipo_cuenta || 'Ahorros' }})</span>
              </div>
              <div v-if="s.telefono" class="flex items-center justify-between text-[11px]">
                <span class="text-stone-500">Teléfono:</span>
                <span class="text-stone-300">{{ s.telefono }}</span>
              </div>
              <div v-if="s.email" class="flex items-center justify-between text-[11px]">
                <span class="text-stone-500">Email:</span>
                <span class="text-stone-300 truncate max-w-[150px]">{{ s.email }}</span>
              </div>
            </div>

            <!-- Historical Financials -->
            <div class="mt-4 p-3 rounded-xl bg-stone-950/80 border border-stone-800/80 font-mono space-y-1.5">
              <div class="flex items-center justify-between text-[11px]">
                <span class="text-stone-400">Total Liquidado Histórico:</span>
                <span class="text-emerald-400 font-bold">{{ formatCOP(getIngresoHistoricoSocia(s.id)) }}</span>
              </div>
              <div class="flex items-center justify-between text-[11px]">
                <span class="text-stone-400">Anticipos Pendientes:</span>
                <span class="text-rose-400 font-bold">{{ formatCOP(getAnticiposPendientesSocia(s.id)) }}</span>
              </div>
            </div>

            <p v-if="s.notas" class="text-[11px] text-stone-400 italic mt-3 line-clamp-2">
              "{{ s.notas }}"
            </p>
          </div>

          <div class="mt-5 pt-3 border-t border-stone-800 flex items-center justify-between">
            <Button
              :label="s.activo ? 'Desactivar' : 'Activar'"
              size="small"
              text
              class="text-[11px] p-0 text-stone-400 hover:text-stone-200"
              @click="toggleActivoSocia(s)"
            />

            <div class="flex items-center gap-1">
              <Button
                icon="pi pi-pencil"
                size="small"
                text
                rounded
                class="p-button-secondary text-amber-300 hover:bg-stone-800"
                @click="abrirEditarSocia(s)"
              />
              <Button
                v-if="!s.es_fondo_taller"
                icon="pi pi-trash"
                size="small"
                text
                rounded
                class="p-button-danger text-rose-400 hover:bg-rose-950/40"
                @click="solicitarEliminarSocia(s)"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 3: ANTICIPOS & RETIROS DE SOCIAS (CRUD) -->
    <div v-if="activeTab === 'anticipos'" class="space-y-4">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800 text-xs font-mono">
        <div class="w-full sm:w-72 relative">
          <i class="pi pi-search absolute left-3 top-1/2 -translate-y-1/2 text-stone-500 text-xs" />
          <InputText
            v-model="searchAnticipos"
            placeholder="Buscar por socia, concepto, recibo..."
            class="w-full pl-8 text-xs font-sans"
          />
        </div>

        <Button
          label="Registrar Nuevo Anticipo"
          icon="pi pi-plus"
          size="small"
          class="p-button-warning text-xs font-semibold whitespace-nowrap"
          @click="abrirNuevoAnticipo"
        />
      </div>

      <!-- Anticipos Table (desktop) + Cards (mobile) -->
      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden">
        <div class="hidden overflow-x-auto md:block">
          <table class="w-full min-w-[760px] text-xs text-left border-collapse font-mono">
            <thead>
              <tr class="bg-stone-950/90 border-b border-stone-800 text-[10px] uppercase text-stone-400">
                <th class="py-3 px-4 sticky left-0 z-10 bg-stone-950/95">Fecha & Socia</th>
                <th class="py-3 px-4 min-w-[180px]">Concepto / Motivo</th>
                <th class="py-3 px-3 text-right whitespace-nowrap">Monto Anticipo</th>
                <th class="py-3 px-3 whitespace-nowrap">Método & Comprobante</th>
                <th class="py-3 px-3 text-center whitespace-nowrap">Estado</th>
                <th class="py-3 px-4 text-center whitespace-nowrap">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60">
              <tr v-for="a in anticiposFiltrados" :key="a.id" class="hover:bg-stone-800/30">
                <td class="py-3.5 px-4 sticky left-0 z-10 bg-stone-900/95">
                  <div class="font-serif font-bold text-stone-100 text-xs">{{ a.nombre_socia }}</div>
                  <div class="text-[10px] text-stone-400">Fecha: {{ a.fecha }}</div>
                </td>

                <td class="py-3.5 px-4 font-sans text-stone-300 min-w-[180px]">
                  <div>{{ a.concepto }}</div>
                  <div v-if="a.observaciones" class="text-[10px] text-stone-500 italic mt-0.5">
                    {{ a.observaciones }}
                  </div>
                </td>

                <td class="py-3.5 px-3 text-right font-bold text-rose-400 text-sm whitespace-nowrap">
                  {{ formatCOP(a.monto) }}
                </td>

                <td class="py-3.5 px-3 text-stone-300 text-[11px]">
                  <div>{{ a.metodo_desembolso }}</div>
                  <div v-if="a.comprobante" class="text-amber-400/90 font-mono text-[10px]">
                    Ref: {{ a.comprobante }}
                  </div>
                </td>

                <td class="py-3.5 px-3 text-center whitespace-nowrap">
                  <span
                    class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider"
                    :class="{
                      'bg-amber-500/20 text-amber-300 border border-amber-500/30': a.estado === 'PENDIENTE_DESCUENTO',
                      'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': a.estado === 'DESCONTADO',
                      'bg-rose-950 text-rose-400 border border-rose-800': a.estado === 'ANULADO',
                    }"
                  >
                    {{ a.estado === 'PENDIENTE_DESCUENTO' ? '⏳ Pendiente Descuento' : (a.estado === 'DESCONTADO' ? '✅ Descontado' : 'Anulado') }}
                  </span>
                </td>

                <td class="py-3.5 px-4 text-center whitespace-nowrap">
                  <div class="flex items-center justify-center gap-1">
                    <Button
                      v-if="a.estado === 'PENDIENTE_DESCUENTO'"
                      icon="pi pi-check"
                      size="small"
                      text
                      rounded
                      class="p-button-success text-emerald-400 hover:bg-emerald-950/40"
                      title="Marcar como Descontado"
                      :loading="descontandoAnticipoId === a.id"
                      @click="marcarAnticipoDescontado(a)"
                    />
                    <Button
                      icon="pi pi-pencil"
                      size="small"
                      text
                      rounded
                      class="p-button-secondary text-stone-300 hover:bg-stone-800"
                      title="Editar Anticipo"
                      @click="abrirEditarAnticipo(a)"
                    />
                    <Button
                      icon="pi pi-trash"
                      size="small"
                      text
                      rounded
                      class="p-button-danger text-rose-400 hover:bg-rose-950/40"
                      title="Eliminar Anticipo"
                      @click="solicitarEliminarAnticipo(a)"
                    />
                  </div>
                </td>
              </tr>

              <tr v-if="anticiposFiltrados.length === 0">
                <td colspan="6" class="py-8 text-center text-stone-500">
                  <i class="pi pi-inbox text-2xl mb-2 block" />
                  No hay registros de anticipos que coincidan.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Mobile cards: same anticiposFiltrados. No horizontal scroll. -->
        <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
          <div v-if="anticiposFiltrados.length === 0" class="text-center py-8 text-sm text-stone-500">No hay registros de anticipos que coincidan.</div>
          <div v-for="a in anticiposFiltrados" :key="a.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
            <div class="flex items-start justify-between gap-2 min-w-0">
              <div class="font-bold text-sm text-stone-100 min-w-0">{{ a.nombre_socia }}</div>
              <span class="text-xs text-stone-500 shrink-0">{{ a.fecha }}</span>
            </div>
            <div class="text-sm text-stone-300">{{ a.concepto }}</div>
            <div v-if="a.observaciones" class="text-sm text-stone-500 italic">{{ a.observaciones }}</div>
            <div class="flex items-center justify-between text-sm">
              <span class="text-xs uppercase tracking-wider text-stone-400">Monto</span>
              <span class="font-mono font-bold text-rose-400">{{ formatCOP(a.monto) }}</span>
            </div>
            <div class="text-sm text-stone-300">{{ a.metodo_desembolso }}<span v-if="a.comprobante" class="ml-1 font-mono text-xs text-amber-400/90">Ref: {{ a.comprobante }}</span></div>
            <span class="inline-block px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider" :class="{ 'bg-amber-500/20 text-amber-300 border border-amber-500/30': a.estado === 'PENDIENTE_DESCUENTO', 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30': a.estado === 'DESCONTADO', 'bg-rose-950 text-rose-400 border border-rose-800': a.estado === 'ANULADO' }">{{ a.estado === 'PENDIENTE_DESCUENTO' ? '⏳ Pendiente Descuento' : (a.estado === 'DESCONTADO' ? '✅ Descontado' : 'Anulado') }}</span>
            <div class="flex gap-2 pt-1">
              <button v-if="a.estado === 'PENDIENTE_DESCUENTO'" type="button" class="flex-1 min-h-[40px] rounded-lg bg-emerald-950 text-emerald-300 border border-emerald-800 text-sm font-semibold" @click="marcarAnticipoDescontado(a)">Marcar descontado</button>
              <button type="button" class="flex-1 min-h-[40px] rounded-lg bg-stone-800 text-stone-200 text-sm font-semibold" @click="abrirEditarAnticipo(a)">Editar</button>
              <button type="button" class="min-w-[44px] min-h-[40px] px-3 rounded-lg border border-rose-800 text-rose-400" title="Eliminar Anticipo" @click="solicitarEliminarAnticipo(a)"><i class="pi pi-trash text-xs" /></button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 4: MOVIMIENTOS FINANCIEROS (solo-lectura) -->
    <div v-if="activeTab === 'movimientos'" class="space-y-4">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-stone-900/60 p-3.5 rounded-xl border border-stone-800 text-xs font-mono">
        <div class="flex items-center gap-2 w-full sm:w-auto">
          <span class="text-stone-400 text-xs font-mono">Tipo:</span>
          <Dropdown
            v-model="filterMovTipo"
            :options="[
              { label: 'Todos', value: 'TODOS' },
              { label: 'Gasto', value: 'Gasto' },
              { label: 'Inversión', value: 'Inversion' },
              { label: 'Retiro', value: 'Retiro' },
            ]"
            option-label="label"
            option-value="value"
            class="text-xs w-36"
            @change="recargarMovimientos"
          />
          <span class="text-stone-400 text-xs font-mono">Estado:</span>
          <Dropdown
            v-model="filterMovEstado"
            :options="[
              { label: 'Todos', value: 'TODOS' },
              { label: 'Borrador', value: 'draft' },
              { label: 'Confirmado', value: 'confirmed' },
              { label: 'Anulado', value: 'cancelled' },
              { label: 'Revertido', value: 'reversed' },
            ]"
            option-label="label"
            option-value="value"
            class="text-xs w-36"
            @change="recargarMovimientos"
          />
        </div>
        <Button
          label="Recargar"
          icon="pi pi-refresh"
          size="small"
          severity="secondary"
          outlined
          class="text-xs"
          @click="recargarMovimientos"
        />
      </div>

      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden">
        <div class="hidden overflow-x-auto md:block">
          <table class="w-full min-w-[640px] text-xs text-left border-collapse font-mono">
            <thead>
              <tr class="bg-stone-950/90 border-b border-stone-800 text-[10px] uppercase text-stone-400">
                <th class="py-3 px-4 sticky left-0 z-10 bg-stone-950/95 whitespace-nowrap">Fecha</th>
                <th class="py-3 px-4 whitespace-nowrap">Tipo</th>
                <th class="py-3 px-4 min-w-[180px]">Descripción</th>
                <th class="py-3 px-3 text-right whitespace-nowrap">Monto</th>
                <th class="py-3 px-3 text-center whitespace-nowrap">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60">
              <tr v-for="m in movimientosFiltrados" :key="m.id" class="hover:bg-stone-800/30">
                <td class="py-3 px-4 text-stone-300 sticky left-0 z-10 bg-stone-900/95 whitespace-nowrap">{{ m.fecha }}</td>
                <td class="py-3 px-4 text-amber-300 font-bold whitespace-nowrap">{{ m.tipo }}</td>
                <td class="py-3 px-4 text-stone-300 min-w-[180px]">{{ m.descripcion }}</td>
                <td class="py-3 px-3 text-right font-bold text-stone-100 whitespace-nowrap">{{ formatCOP(Number(m.monto ?? 0)) }}</td>
                <td class="py-3 px-3 text-center whitespace-nowrap">
                  <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border"
                    :class="m.estado === 'confirmed' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : m.estado === 'draft' ? 'bg-stone-800 text-stone-400 border-stone-700' : 'bg-rose-950 text-rose-400 border-rose-800'">
                    {{ m.estado }}
                  </span>
                </td>
              </tr>
              <tr v-if="!movimientosFiltrados.length">
                <td colspan="5" class="py-8 text-center text-stone-500">
                  <i class="pi pi-inbox text-2xl mb-2 block" />
                  Sin movimientos con los filtros actuales.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Mobile cards: same movimientosFiltrados. No horizontal scroll. -->
        <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
          <div v-if="!movimientosFiltrados.length" class="text-center py-8 text-sm text-stone-500">Sin movimientos con los filtros actuales.</div>
          <div v-for="m in movimientosFiltrados" :key="m.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
            <div class="flex items-start justify-between gap-2 min-w-0">
              <div class="font-bold text-sm text-amber-300 min-w-0">{{ m.tipo }}</div>
              <span class="text-xs text-stone-500 shrink-0">{{ m.fecha }}</span>
            </div>
            <div class="text-sm text-stone-300">{{ m.descripcion }}</div>
            <div class="flex items-center justify-between text-sm">
              <span class="px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider border" :class="m.estado === 'confirmed' ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : m.estado === 'draft' ? 'bg-stone-800 text-stone-400 border-stone-700' : 'bg-rose-950 text-rose-400 border-rose-800'">{{ m.estado }}</span>
              <span class="font-mono font-bold text-stone-100">{{ formatCOP(Number(m.monto ?? 0)) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 5: SIMULADOR DE PUNTO DE EQUILIBRIO TEXTIL -->
    <div v-if="activeTab === 'simulador'" class="rounded-2xl border border-amber-500/20 bg-stone-900/60 p-6 space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-800 pb-3">
        <div>
          <h2 class="text-base font-serif font-semibold text-stone-100 flex items-center gap-2 m-0">
            <i class="pi pi-chart-line text-amber-400" />
            Simulador de Rentabilidad & Punto de Equilibrio Textil
          </h2>
          <p class="text-xs text-stone-400 mt-0.5 m-0 font-mono">
            Proyección de unidades mínimas para cubrir costos fijos del taller y rentabilidad esperada por socias.
          </p>
        </div>
        <div class="px-3 py-1 rounded-lg bg-stone-950 border border-amber-500/30 text-amber-300 font-mono text-xs font-bold">
          Punto de Equilibrio: {{ puntoEquilibrioUnidades }} Corsets / Mes
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
        <div class="space-y-1">
          <label class="text-stone-400 block text-[11px]">PVP Promedio Corset</label>
          <InputNumber
            v-model="precioPromedioCorse"
            mode="currency"
            currency="COP"
            locale="es-CO"
            class="w-full text-xs"
          />
        </div>

        <div class="space-y-1">
          <label class="text-stone-400 block text-[11px]">Costo Insumos Promedio</label>
          <InputNumber
            v-model="costoInsumosPromedio"
            mode="currency"
            currency="COP"
            locale="es-CO"
            class="w-full text-xs"
          />
        </div>

        <div class="space-y-1">
          <label class="text-stone-400 block text-[11px]">Horas Confección Promedio</label>
          <InputNumber
            v-model="horasManoObraPromedio"
            :min="1"
            :max="30"
            suffix=" horas"
            class="w-full text-xs"
          />
        </div>

        <div class="space-y-1">
          <label class="text-stone-400 block text-[11px]">Costo Hora Taller</label>
          <InputNumber
            v-model="costoHoraTaller"
            mode="currency"
            currency="COP"
            locale="es-CO"
            class="w-full text-xs"
          />
        </div>
      </div>

      <!-- Interactive Goal Slider & Projected Profit -->
      <div class="p-4 rounded-xl bg-stone-950/80 border border-stone-800 space-y-3">
        <div class="flex items-center justify-between text-xs font-mono">
          <span class="text-stone-300">Meta Mensual de Confección Simulada:</span>
          <span class="text-amber-300 font-bold text-sm">{{ prendasMetaSimuladas }} prendas</span>
        </div>
        <Slider v-model="prendasMetaSimuladas" :min="1" :max="50" class="w-full" />

        <div class="grid grid-cols-1 sm:grid-cols-4 gap-3 pt-2 font-mono text-xs">
          <div class="p-2.5 rounded-lg bg-stone-900/60 border border-stone-800">
            <span class="text-stone-400 block text-[10px]">Margen Unitario:</span>
            <span class="text-emerald-400 font-bold text-sm">{{ formatCOP(margenContribucionUnitario) }}</span>
          </div>
          <div class="p-2.5 rounded-lg bg-stone-900/60 border border-stone-800">
            <span class="text-stone-400 block text-[10px]">Costos Fijos Taller:</span>
            <span class="text-stone-200 font-bold text-sm">{{ formatCOP(gastosOperativosSimulator) }}</span>
          </div>
          <div class="p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/30">
            <span class="text-amber-300 block text-[10px]">Fondo Taller (estimado):</span>
            <span class="text-amber-300 font-bold text-sm">{{ formatCOP(Math.round(utilidadSimulada * 0.4)) }}</span>
          </div>
          <div class="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30">
            <span class="text-emerald-300 block text-[10px]">Cuota por socia (estimado):</span>
            <span class="text-emerald-300 font-bold text-sm">{{ formatCOP(Math.round(utilidadSimulada * 0.3)) }} c/u</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <NuevaLiquidacionModal
      v-model:visible="showNuevaLiqModal"
      :liquidacion-editar="liquidacionSeleccionadaEditar"
      @guardada="() => { void cargarDatos() }"
    />

    <DetalleLiquidacionModal
      v-model:visible="showDetalleLiqModal"
      :liquidacion="liquidacionSeleccionadaDetalle"
      @editar="(l) => { showDetalleLiqModal = false; abrirEditarLiquidacion(l); }"
    />

    <GestionSociasModal
      v-model:visible="showGestionSociaModal"
      :socia-editar="sociaSeleccionadaEditar"
      @guardada="() => { void cargarDatos() }"
    />

    <NuevoAnticipoModal
      v-model:visible="showNuevoAnticipoModal"
      :anticipo-editar="anticipoSeleccionadoEditar"
      @guardado="() => { void cargarDatos() }"
    />

    <!-- Delete Liquidacion Dialog -->
    <Dialog
      v-model:visible="showDeleteLiqModal"
      modal
      header="⚠️ Confirmar Eliminación de Liquidación"
      :style="{ width: '90vw', maxWidth: '420px' }"
    >
      <div class="space-y-3 pt-1 text-xs text-stone-200">
        <p>
          ¿Está seguro de que desea eliminar la liquidación
          <strong class="text-amber-300">{{ liquidacionAEliminar?.codigo }}</strong> ({{ liquidacionAEliminar?.periodo }})?
        </p>
        <p class="text-stone-400 text-[11px]">
          Esta acción no se puede deshacer.
        </p>
      </div>
      <template #footer>
        <div class="flex items-center justify-end gap-2 pt-2 border-t border-stone-800">
          <Button
            label="Cancelar"
            icon="pi pi-times"
            size="small"
            class="p-button-text p-button-secondary text-xs"
            @click="showDeleteLiqModal = false"
          />
          <Button
            label="Eliminar"
            icon="pi pi-trash"
            size="small"
            class="p-button-danger text-xs font-semibold"
            @click="confirmarEliminarLiquidacion"
          />
        </div>
      </template>
    </Dialog>

    <!-- Delete Socia Dialog -->
    <Dialog
      v-model:visible="showDeleteSociaModal"
      modal
      header="⚠️ Confirmar Eliminación de Socia"
      :style="{ width: '90vw', maxWidth: '420px' }"
    >
      <div class="space-y-3 pt-1 text-xs text-stone-200">
        <p>
          ¿Está seguro de eliminar el registro de
          <strong class="text-amber-300">{{ sociaAEliminar?.nombre }}</strong>?
        </p>
      </div>
      <template #footer>
        <div class="flex items-center justify-end gap-2 pt-2 border-t border-stone-800">
          <Button
            label="Cancelar"
            icon="pi pi-times"
            size="small"
            class="p-button-text p-button-secondary text-xs"
            @click="showDeleteSociaModal = false"
          />
          <Button
            label="Eliminar"
            icon="pi pi-trash"
            size="small"
            class="p-button-danger text-xs font-semibold"
            @click="confirmarEliminarSocia"
          />
        </div>
      </template>
    </Dialog>

    <!-- Delete Anticipo Dialog -->
    <Dialog
      v-model:visible="showDeleteAnticipoModal"
      modal
      header="⚠️ Confirmar Eliminación de Anticipo"
      :style="{ width: '90vw', maxWidth: '420px' }"
    >
      <div class="space-y-3 pt-1 text-xs text-stone-200">
        <p>
          ¿Desea eliminar el anticipo de
          <strong class="text-rose-400">{{ formatCOP(anticipoAEliminar?.monto || 0) }}</strong> para
          <strong class="text-amber-300">{{ anticipoAEliminar?.nombre_socia }}</strong>?
        </p>
      </div>
      <template #footer>
        <div class="flex items-center justify-end gap-2 pt-2 border-t border-stone-800">
          <Button
            label="Cancelar"
            icon="pi pi-times"
            size="small"
            class="p-button-text p-button-secondary text-xs"
            @click="showDeleteAnticipoModal = false"
          />
          <Button
            label="Eliminar"
            icon="pi pi-trash"
            size="small"
            class="p-button-danger text-xs font-semibold"
            @click="confirmarEliminarAnticipo"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>
