<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Dropdown from 'primevue/dropdown'
import Dialog from 'primevue/dialog'
import Slider from 'primevue/slider'
import {
  useAtelierStore,
  type LiquidacionSocias,
  type SociaAtelier,
  type AnticipoSocia,
} from '@/stores/atelier'
import NuevaLiquidacionModal from '@/components/atelier/NuevaLiquidacionModal.vue'
import DetalleLiquidacionModal from '@/components/atelier/DetalleLiquidacionModal.vue'
import GestionSociasModal from '@/components/atelier/GestionSociasModal.vue'
import NuevoAnticipoModal from '@/components/atelier/NuevoAnticipoModal.vue'
import { showToast } from '@/utils/toast'
import { useMode } from '@/composables/useMode'
import { useSocios } from '@/composables/useSocios'
import { useFinanzas } from '@/composables/useFinanzas'
import * as movimientosApi from '@/services/api/movimientos'

const atelier = useAtelierStore()
const { isMock } = useMode()
const sociosApi = useSocios()
const finanzasApi = useFinanzas()

// Real-mode state (populated via API when !isMock)
const sociasReal = ref<SociaAtelier[]>([])
const liquidacionesReal = ref<LiquidacionSocias[]>([])
const anticiposReal = ref<AnticipoSocia[]>([])
const movimientosReal = ref<movimientosApi.MovimientoRead[]>([])
const cargandoReal = ref(false)

function normalizeSocia(raw: Record<string, unknown>): SociaAtelier {
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

function normalizeLiquidacion(raw: Record<string, unknown>): LiquidacionSocias {
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
    estado: raw.estado as LiquidacionSocias['estado'],
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
        estado_pago: (dd.estado_pago as LiquidacionSocias['distribucion'][number]['estado_pago']) ?? 'PENDIENTE',
        fecha_pago: dd.fecha_pago as string | undefined,
        comprobante_transferencia: dd.comprobante_transferencia as string | undefined,
        banco_destino: dd.banco_destino as string | undefined,
      }
    }),
    observaciones: raw.observaciones as string | undefined,
    created_at: (raw.created_at as string) ?? (raw.creado_en as string) ?? new Date().toISOString(),
  }
}

function normalizeAnticipo(raw: Record<string, unknown>): AnticipoSocia {
  return {
    id: raw.id as number,
    socia_id: raw.socia_id as number,
    nombre_socia: (raw.socia_nombre as string) ?? (raw.nombre_socia as string) ?? '',
    fecha: raw.fecha as string,
    monto: Number(raw.monto ?? 0),
    concepto: (raw.concepto as string) ?? 'Adelanto',
    metodo_desembolso: (raw.metodo_desembolso as string) ?? 'Transferencia Bancaria',
    estado: raw.estado as AnticipoSocia['estado'],
    liquidacion_id: (raw.liquidacion_id as number | null) ?? null,
    comprobante: raw.comprobante as string | undefined,
    observaciones: raw.observaciones as string | undefined,
  }
}

async function cargarDatosReales() {
  if (isMock.value) return
  cargandoReal.value = true
  try {
    const [socRes, liqRes, antRes, movRes] = await Promise.all([
      sociosApi.list({ limit: 100, offset: 0 }),
      finanzasApi.listLiquidaciones({ limit: 100, offset: 0 }),
      finanzasApi.listAnticipos({ limit: 100, offset: 0 }),
      movimientosApi.listMovimientos({ limit: 100, offset: 0 }).catch(() => ({ items: [], total: 0 })),
    ])
    sociasReal.value = (socRes.items as unknown as Record<string, unknown>[]).map(normalizeSocia)
    liquidacionesReal.value = (liqRes.items as unknown as Record<string, unknown>[]).map(normalizeLiquidacion)
    anticiposReal.value = (antRes.items as unknown as Record<string, unknown>[]).map(normalizeAnticipo)
    movimientosReal.value = (movRes.items as unknown as movimientosApi.MovimientoRead[]) ?? []
  } catch {
    // keep atelier fallback on error
  } finally {
    cargandoReal.value = false
  }
}

onMounted(() => {
  void cargarDatosReales()
})

watch(isMock, () => {
  void cargarDatosReales()
})

// Unified lists — isMock ? atelier : real API
const sociasList = computed<SociaAtelier[]>(() => (isMock.value ? (atelier.socias as unknown as SociaAtelier[]) : sociasReal.value))
const liquidacionesList = computed<LiquidacionSocias[]>(() => (isMock.value ? (atelier.liquidaciones as unknown as LiquidacionSocias[]) : liquidacionesReal.value))
const anticiposList = computed<AnticipoSocia[]>(() => (isMock.value ? (atelier.anticipos as unknown as AnticipoSocia[]) : anticiposReal.value))
const movimientosList = computed<movimientosApi.MovimientoRead[]>(() => (isMock.value ? [] : movimientosReal.value))

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

const liquidacionSeleccionadaEditar = ref<LiquidacionSocias | null>(null)
const liquidacionSeleccionadaDetalle = ref<LiquidacionSocias | null>(null)
const sociaSeleccionadaEditar = ref<SociaAtelier | null>(null)
const anticipoSeleccionadoEditar = ref<AnticipoSocia | null>(null)

// Deletion confirmation modals
const showDeleteLiqModal = ref(false)
const liquidacionAEliminar = ref<LiquidacionSocias | null>(null)

const showDeleteSociaModal = ref(false)
const sociaAEliminar = ref<SociaAtelier | null>(null)

const showDeleteAnticipoModal = ref(false)
const anticipoAEliminar = ref<AnticipoSocia | null>(null)

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

// Filtered liquidaciones (source switches via isMock)
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

// Filtered anticipos (source switches via isMock)
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
  if (isMock.value) return
  try {
    const r = await movimientosApi.listMovimientos({
      limit: 100,
      offset: 0,
      ...(filterMovTipo.value !== 'TODOS' ? { tipo: filterMovTipo.value as 'Gasto' | 'Inversion' | 'Retiro' } : {}),
      ...(filterMovEstado.value !== 'TODOS' ? { estado: filterMovEstado.value as 'draft' | 'confirmed' | 'cancelled' | 'reversed' } : {}),
    })
    movimientosReal.value = r.items ?? []
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al cargar movimientos'
    showToast('error', 'Error', msg)
  }
}

// Total % of active socias (real or mock)
const sumaPorcentajesSocias = computed(() => {
  return sociasList.value.filter((s) => s.activo).reduce((acc, s) => acc + s.porcentaje, 0)
})

// KPI aggregates — mirror atelier getters but over the active data source
const totalHistoricoFacturado = computed(() => liquidacionesList.value.reduce((a, l) => a + l.total_ventas_brutas, 0))
const totalHistoricoFondo = computed(() => liquidacionesList.value.reduce((a, l) => a + l.fondo_reinversion_monto, 0))
const totalRepartidoMargara = computed(() =>
  liquidacionesList.value.reduce((a, l) => {
    const item = l.distribucion.find((d) => d.socia_id === 2 || d.nombre_socia.toLowerCase().includes('marg'))
    return a + (item ? item.monto_neto_pagar : 0)
  }, 0),
)
const totalRepartidoValqui = computed(() =>
  liquidacionesList.value.reduce((a, l) => {
    const item = l.distribucion.find((d) => d.socia_id === 3 || d.nombre_socia.toLowerCase().includes('valq'))
    return a + (item ? item.monto_neto_pagar : 0)
  }, 0),
)
const totalAnticiposPendientes = computed(() =>
  anticiposList.value.filter((a) => a.estado === 'PENDIENTE_DESCUENTO').reduce((a, x) => a + x.monto, 0),
)

// Historical income per socia (real or mock)
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

function abrirEditarLiquidacion(liq: LiquidacionSocias) {
  liquidacionSeleccionadaEditar.value = liq
  showNuevaLiqModal.value = true
}

function abrirDetalleLiquidacion(liq: LiquidacionSocias) {
  liquidacionSeleccionadaDetalle.value = liq
  showDetalleLiqModal.value = true
}

function solicitarEliminarLiquidacion(liq: LiquidacionSocias) {
  liquidacionAEliminar.value = liq
  showDeleteLiqModal.value = true
}

async function confirmarEliminarLiquidacion() {
  if (liquidacionAEliminar.value) {
    const cod = liquidacionAEliminar.value.codigo
    const id = liquidacionAEliminar.value.id
    if (isMock.value) {
      atelier.eliminarLiquidacion(id)
    } else {
      try {
        await finanzasApi.removeLiquidacion(id)
        await cargarDatosReales()
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Error al eliminar liquidación'
        showToast('error', 'Error', msg)
        return
      }
    }
    showToast('info', 'Liquidación Eliminada', `La liquidación ${cod} ha sido eliminada del historial.`)
    liquidacionAEliminar.value = null
    showDeleteLiqModal.value = false
  }
}

async function cambiarEstadoLiq(liq: LiquidacionSocias, nuevoEstado: LiquidacionSocias['estado']) {
  if (isMock.value) {
    atelier.cambiarEstadoLiquidacion(liq.id, nuevoEstado)
    showToast('success', 'Estado Actualizado', `Liquidación ${liq.codigo} marcada como ${nuevoEstado}.`)
    return
  }
  try {
    const updated = await finanzasApi.transitionLiquidacion(liq.id, { estado: nuevoEstado })
    // patch local real list optimistically
    const idx = liquidacionesReal.value.findIndex((l) => l.id === liq.id)
    if (idx !== -1 && updated) liquidacionesReal.value[idx] = normalizeLiquidacion(updated as unknown as Record<string, unknown>)
    else await cargarDatosReales()
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

function abrirEditarSocia(soc: SociaAtelier) {
  sociaSeleccionadaEditar.value = soc
  showGestionSociaModal.value = true
}

function solicitarEliminarSocia(soc: SociaAtelier) {
  sociaAEliminar.value = soc
  showDeleteSociaModal.value = true
}

async function confirmarEliminarSocia() {
  if (sociaAEliminar.value) {
    const nom = sociaAEliminar.value.nombre
    const id = sociaAEliminar.value.id
    if (isMock.value) {
      atelier.eliminarSocia(id)
    } else {
      try {
        await sociosApi.remove(id)
        await cargarDatosReales()
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Error al eliminar socia'
        showToast('error', 'Error', msg)
        return
      }
    }
    showToast('info', 'Socia Eliminada', `El registro de ${nom} ha sido removido.`)
    sociaAEliminar.value = null
    showDeleteSociaModal.value = false
  }
}

async function toggleActivoSocia(s: SociaAtelier) {
  if (isMock.value) {
    atelier.toggleActivoSocia(s.id)
    return
  }
  try {
    await sociosApi.update(s.id, { activo: !s.activo })
    await cargarDatosReales()
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

function abrirEditarAnticipo(ant: AnticipoSocia) {
  anticipoSeleccionadoEditar.value = ant
  showNuevoAnticipoModal.value = true
}

async function marcarAnticipoDescontado(ant: AnticipoSocia) {
  if (isMock.value) {
    atelier.cambiarEstadoAnticipo(ant.id, 'DESCONTADO')
    showToast('success', 'Anticipo Actualizado', `Anticipo marcado como DESCONTADO.`)
    return
  }
  // Camino único: PATCH /anticipos/{id}/descuento exige liquidacion_id.
  // Sin liquidación no hay a qué imputar el descuento — se avisa y no se
  // llama a ningún endpoint (el fallback a transitionAnticipo hacía doble
  // escritura potencial: descontar + transición suelta sin vínculo).
  if (!ant.liquidacion_id) {
    showToast('warn', 'Falta liquidación', 'Seleccioná una liquidación para descontar el anticipo.')
    return
  }
  try {
    await finanzasApi.descontarAnticipo(ant.id, ant.liquidacion_id)
    await cargarDatosReales()
    showToast('success', 'Anticipo Actualizado', `Anticipo marcado como DESCONTADO.`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al descontar anticipo'
    showToast('error', 'Error', msg)
  }
}

function solicitarEliminarAnticipo(ant: AnticipoSocia) {
  anticipoAEliminar.value = ant
  showDeleteAnticipoModal.value = true
}

async function confirmarEliminarAnticipo() {
  if (anticipoAEliminar.value) {
    const id = anticipoAEliminar.value.id
    if (isMock.value) {
      atelier.eliminarAnticipo(id)
    } else {
      try {
        await finanzasApi.removeAnticipo(id)
        await cargarDatosReales()
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Error al eliminar anticipo'
        showToast('error', 'Error', msg)
        return
      }
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
            Fórmula 40 / 30 / 30
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
          <div class="text-[10px] text-stone-400 uppercase tracking-wider">🪡 Margara Restrepo (30%)</div>
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
          <div class="text-[10px] text-stone-400 uppercase tracking-wider">🎨 Valeria Quintero (30%)</div>
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

      <!-- Liquidaciones Table -->
      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left border-collapse">
            <thead>
              <tr class="bg-stone-950/90 border-b border-stone-800 text-[10px] font-mono uppercase text-stone-400">
                <th class="py-3 px-4">Código & Periodo</th>
                <th class="py-3 px-3 text-right">Ventas Brutas</th>
                <th class="py-3 px-3 text-right">Costos / Gastos</th>
                <th class="py-3 px-3 text-right">Utilidad Neta</th>
                <th class="py-3 px-3 text-center">Fondo Taller (40%)</th>
                <th class="py-3 px-3 text-center">Margara (30%)</th>
                <th class="py-3 px-3 text-center">Valqui (30%)</th>
                <th class="py-3 px-3 text-center">Estado</th>
                <th class="py-3 px-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60 font-mono">
              <tr
                v-for="l in liquidacionesFiltradas"
                :key="l.id"
                class="hover:bg-stone-800/30 transition-colors"
              >
                <td class="py-3.5 px-4">
                  <div class="font-bold text-amber-300 font-serif text-sm">{{ l.codigo }}</div>
                  <div class="text-stone-200 text-xs font-sans mt-0.5">{{ l.periodo }}</div>
                  <div class="text-[10px] text-stone-500">Cierre: {{ l.fecha_cierre }}</div>
                </td>

                <td class="py-3.5 px-3 text-right font-bold text-stone-100">
                  {{ formatCOP(l.total_ventas_brutas) }}
                </td>

                <td class="py-3.5 px-3 text-right text-stone-400 text-[11px]">
                  <div>-{{ formatCOP(l.costo_taller_insumos) }} ins.</div>
                  <div>-{{ formatCOP(l.gastos_operativos) }} gast.</div>
                </td>

                <td class="py-3.5 px-3 text-right font-bold text-emerald-400 text-sm">
                  {{ formatCOP(l.utilidad_neta_total) }}
                </td>

                <td class="py-3.5 px-3 text-center">
                  <span class="text-amber-300 font-bold text-xs">{{ formatCOP(l.fondo_reinversion_monto) }}</span>
                </td>

                <td class="py-3.5 px-3 text-center">
                  <div class="text-stone-200 font-semibold text-xs">
                    {{ formatCOP(l.distribucion.find((d) => d.socia_id === 2)?.monto_neto_pagar || 0) }}
                  </div>
                  <span
                    class="text-[9px] px-1.5 py-0.2 rounded"
                    :class="l.distribucion.find((d) => d.socia_id === 2)?.estado_pago === 'PAGADO' ? 'bg-emerald-950 text-emerald-400' : 'bg-stone-800 text-amber-400'"
                  >
                    {{ l.distribucion.find((d) => d.socia_id === 2)?.estado_pago || 'PENDIENTE' }}
                  </span>
                </td>

                <td class="py-3.5 px-3 text-center">
                  <div class="text-stone-200 font-semibold text-xs">
                    {{ formatCOP(l.distribucion.find((d) => d.socia_id === 3)?.monto_neto_pagar || 0) }}
                  </div>
                  <span
                    class="text-[9px] px-1.5 py-0.2 rounded"
                    :class="l.distribucion.find((d) => d.socia_id === 3)?.estado_pago === 'PAGADO' ? 'bg-emerald-950 text-emerald-400' : 'bg-stone-800 text-amber-400'"
                  >
                    {{ l.distribucion.find((d) => d.socia_id === 3)?.estado_pago || 'PENDIENTE' }}
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
                      v-if="isMock"
                      icon="pi pi-pencil"
                      size="small"
                      text
                      rounded
                      class="p-button-secondary text-stone-300 hover:bg-stone-800"
                      title="Editar Liquidación (solo MOCK: la API solo permite transición de estado)"
                      @click="abrirEditarLiquidacion(l)"
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
            (Regla estatutaria de Atelier Arpía: 40% Taller / 30% Confección / 30% Dirección)
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

      <!-- Anticipos Table -->
      <div class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left border-collapse font-mono">
            <thead>
              <tr class="bg-stone-950/90 border-b border-stone-800 text-[10px] uppercase text-stone-400">
                <th class="py-3 px-4">Fecha & Socia</th>
                <th class="py-3 px-4">Concepto / Motivo</th>
                <th class="py-3 px-3 text-right">Monto Anticipo</th>
                <th class="py-3 px-3">Método & Comprobante</th>
                <th class="py-3 px-3 text-center">Estado</th>
                <th class="py-3 px-4 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60">
              <tr v-for="a in anticiposFiltrados" :key="a.id" class="hover:bg-stone-800/30">
                <td class="py-3.5 px-4">
                  <div class="font-serif font-bold text-stone-100 text-xs">{{ a.nombre_socia }}</div>
                  <div class="text-[10px] text-stone-400">Fecha: {{ a.fecha }}</div>
                </td>

                <td class="py-3.5 px-4 font-sans text-stone-300">
                  <div>{{ a.concepto }}</div>
                  <div v-if="a.observaciones" class="text-[10px] text-stone-500 italic mt-0.5">
                    {{ a.observaciones }}
                  </div>
                </td>

                <td class="py-3.5 px-3 text-right font-bold text-rose-400 text-sm">
                  {{ formatCOP(a.monto) }}
                </td>

                <td class="py-3.5 px-3 text-stone-300 text-[11px]">
                  <div>{{ a.metodo_desembolso }}</div>
                  <div v-if="a.comprobante" class="text-amber-400/90 font-mono text-[10px]">
                    Ref: {{ a.comprobante }}
                  </div>
                </td>

                <td class="py-3.5 px-3 text-center">
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

                <td class="py-3.5 px-4 text-center">
                  <div class="flex items-center justify-center gap-1">
                    <Button
                      v-if="a.estado === 'PENDIENTE_DESCUENTO'"
                      icon="pi pi-check"
                      size="small"
                      text
                      rounded
                      class="p-button-success text-emerald-400 hover:bg-emerald-950/40"
                      title="Marcar como Descontado"
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

      <div v-if="isMock" class="rounded-2xl border border-stone-800 bg-stone-900/40 p-8 text-center">
        <i class="pi pi-inbox text-2xl mb-2 block text-stone-500" />
        <p class="text-sm font-bold text-stone-300">Sin movimientos en modo MOCK</p>
        <p class="text-xs text-stone-400 mt-1">Los movimientos financieros viven en <code>GET /api/v1/finanzas/movimientos</code> (Postgres).</p>
      </div>

      <div v-else class="rounded-2xl border border-stone-800 bg-stone-900/40 backdrop-blur-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-xs text-left border-collapse font-mono">
            <thead>
              <tr class="bg-stone-950/90 border-b border-stone-800 text-[10px] uppercase text-stone-400">
                <th class="py-3 px-4">Fecha</th>
                <th class="py-3 px-4">Tipo</th>
                <th class="py-3 px-4">Descripción</th>
                <th class="py-3 px-3 text-right">Monto</th>
                <th class="py-3 px-3 text-center">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60">
              <tr v-for="m in movimientosFiltrados" :key="m.id" class="hover:bg-stone-800/30">
                <td class="py-3 px-4 text-stone-300">{{ m.fecha }}</td>
                <td class="py-3 px-4 text-amber-300 font-bold">{{ m.tipo }}</td>
                <td class="py-3 px-4 text-stone-300">{{ m.descripcion }}</td>
                <td class="py-3 px-3 text-right font-bold text-stone-100">{{ formatCOP(Number(m.monto ?? 0)) }}</td>
                <td class="py-3 px-3 text-center">
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
            <span class="text-amber-300 block text-[10px]">Fondo Taller (40%):</span>
            <span class="text-amber-300 font-bold text-sm">{{ formatCOP(Math.round(utilidadSimulada * 0.4)) }}</span>
          </div>
          <div class="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-500/30">
            <span class="text-emerald-300 block text-[10px]">Cuota Socias (Margara 30% / Valqui 30%):</span>
            <span class="text-emerald-300 font-bold text-sm">{{ formatCOP(Math.round(utilidadSimulada * 0.3)) }} c/u</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <NuevaLiquidacionModal
      v-model:visible="showNuevaLiqModal"
      :liquidacion-editar="liquidacionSeleccionadaEditar"
      @guardada="() => { if (!isMock) void cargarDatosReales() }"
    />

    <DetalleLiquidacionModal
      v-model:visible="showDetalleLiqModal"
      :liquidacion="liquidacionSeleccionadaDetalle"
      @editar="(l) => { showDetalleLiqModal = false; abrirEditarLiquidacion(l); }"
    />

    <GestionSociasModal
      v-model:visible="showGestionSociaModal"
      :socia-editar="sociaSeleccionadaEditar"
      @guardada="() => { if (!isMock) void cargarDatosReales() }"
    />

    <NuevoAnticipoModal
      v-model:visible="showNuevoAnticipoModal"
      :anticipo-editar="anticipoSeleccionadoEditar"
      @guardado="() => { if (!isMock) void cargarDatosReales() }"
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
