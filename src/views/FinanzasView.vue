<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import NuevaLiquidacionModal from '@/components/atelier/NuevaLiquidacionModal.vue'
import DetalleLiquidacionModal from '@/components/atelier/DetalleLiquidacionModal.vue'
import GestionSociasModal from '@/components/atelier/GestionSociasModal.vue'
import NuevoAnticipoModal from '@/components/atelier/NuevoAnticipoModal.vue'
import FinanzasLiquidacionesTab from '@/components/finanzas/FinanzasLiquidacionesTab.vue'
import FinanzasSociasTab from '@/components/finanzas/FinanzasSociasTab.vue'
import FinanzasAnticiposTab from '@/components/finanzas/FinanzasAnticiposTab.vue'
import FinanzasMovimientosTab from '@/components/finanzas/FinanzasMovimientosTab.vue'
import FinanzasSimuladorTab from '@/components/finanzas/FinanzasSimuladorTab.vue'
import type {
  SociaDisplay,
  LiquidacionDisplay,
  AnticipoDisplay,
} from '@/components/finanzas/types'
import { formatCOP } from '@/components/finanzas/types'
import { showToast } from '@/utils/toast'
import { useSocios } from '@/composables/useSocios'
import { useFinanzas } from '@/composables/useFinanzas'
import * as movimientosApi from '@/services/api/movimientos'

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
    rol: (raw.rol as string) ?? 'Socia',
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

// Subtabs
type TabType = 'liquidaciones' | 'socias' | 'anticipos' | 'movimientos' | 'simulador'
const activeTab = ref<TabType>('liquidaciones')

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

// KPI aggregates over the active data source
const totalHistoricoFacturado = computed(() => liquidacionesList.value.reduce((a, l) => a + l.total_ventas_brutas, 0))
const totalHistoricoFondo = computed(() => liquidacionesList.value.reduce((a, l) => a + l.fondo_reinversion_monto, 0))
const sociasReparto = computed(() =>
  sociasList.value.filter((s) => !s.es_fondo_taller && s.activo !== false).slice(0, 2),
)

function totalRepartidoSocia(sociaId: number | undefined): number {
  if (sociaId == null) return 0
  return liquidacionesList.value.reduce((a, l) => {
    const item = l.distribucion.find((d) => d.socia_id === sociaId)
    return a + (item ? item.monto_neto_pagar : 0)
  }, 0)
}

const totalRepartidoMargara = computed(() => totalRepartidoSocia(sociasReparto.value[0]?.id))
const totalRepartidoValqui = computed(() => totalRepartidoSocia(sociasReparto.value[1]?.id))

function nombreSociaReparto(i: number, fallback: string): string {
  return sociasReparto.value[i]?.nombre ?? fallback
}

function porcentajeSociaReparto(i: number, fallback: number): number {
  const s = sociasReparto.value[i] as (SociaDisplay & { porcentaje_participacion?: number }) | undefined
  return Number(s?.porcentaje ?? s?.porcentaje_participacion ?? fallback) || fallback
}

const totalAnticiposPendientes = computed(() =>
  anticiposList.value.filter((a) => a.estado === 'PENDIENTE_DESCUENTO').reduce((a, x) => a + x.monto, 0),
)

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

async function cambiarEstadoLiq(payload: { liquidacion: LiquidacionDisplay; nuevoEstado: 'BORRADOR' | 'APROBADA' | 'PAGADA' }) {
  const { liquidacion: liq, nuevoEstado } = payload
  try {
    await finanzasApi.transitionLiquidacion(liq.id, { estado: nuevoEstado })
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

async function recargarMovimientos(filters?: { tipo?: string; estado?: string }) {
  try {
    const r = await movimientosApi.listMovimientos({
      limit: 100,
      offset: 0,
      ...(filters?.tipo ? { tipo: filters.tipo as 'Gasto' | 'Inversion' | 'Retiro' } : {}),
      ...(filters?.estado ? { estado: filters.estado as 'draft' | 'confirmed' | 'cancelled' | 'reversed' } : {}),
    })
    movimientosList.value = r.items ?? []
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al cargar movimientos'
    showToast('error', 'Error', msg)
  }
}
</script>

<template>
  <div id="print-balance" class="space-y-6">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-stone-800 pb-4">
      <div>
        <div class="flex items-center gap-2">
          <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide m-0">
            Reparto de Socias & Finanzas
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

    <!-- Financial KPI Summary Cards (5 Columns) -->
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

    <!-- TAB 1: LIQUIDACIONES -->
    <FinanzasLiquidacionesTab
      v-if="activeTab === 'liquidaciones'"
      :liquidaciones="liquidacionesList"
      :socias-reparto="sociasReparto"
      @nueva="abrirNuevaLiquidacion"
      @detalle="abrirDetalleLiquidacion"
      @eliminar="solicitarEliminarLiquidacion"
      @cambiar-estado="cambiarEstadoLiq"
    />

    <!-- TAB 2: SOCIAS -->
    <FinanzasSociasTab
      v-if="activeTab === 'socias'"
      :socias-list="sociasList"
      :liquidaciones-list="liquidacionesList"
      :anticipos-list="anticiposList"
      @nueva="abrirNuevaSocia"
      @editar="abrirEditarSocia"
      @eliminar="solicitarEliminarSocia"
      @toggle-activo="toggleActivoSocia"
    />

    <!-- TAB 3: ANTICIPOS -->
    <FinanzasAnticiposTab
      v-if="activeTab === 'anticipos'"
      :anticipos-list="anticiposList"
      :descontando-anticipo-id="descontandoAnticipoId"
      @nuevo="abrirNuevoAnticipo"
      @editar="abrirEditarAnticipo"
      @eliminar="solicitarEliminarAnticipo"
      @marcar-descontado="marcarAnticipoDescontado"
    />

    <!-- TAB 4: MOVIMIENTOS -->
    <FinanzasMovimientosTab
      v-if="activeTab === 'movimientos'"
      :movimientos-list="movimientosList"
      @recargar="recargarMovimientos"
    />

    <!-- TAB 5: SIMULADOR -->
    <FinanzasSimuladorTab
      v-if="activeTab === 'simulador'"
    />

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
