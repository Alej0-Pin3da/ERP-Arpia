<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useProduccion } from '@/composables/useProduccion'
import {
  FASES_PRODUCCION,
  extractApiDetail,
  siguienteFase,
} from '@/services/api/pedidos-produccion'
import NuevoPedidoModal from '@/components/atelier/NuevoPedidoModal.vue'
import DetallePedidoTallerModal from '@/components/atelier/DetallePedidoTallerModal.vue'
import { showToast } from '@/utils/toast'
import { waUrl } from '@/utils/contacto'

const router = useRouter()
const produccionService = useProduccion()

/** REAL display shape: backend PedidoProduccionRead normalized for this view. */
interface PedidoDisplay {
  id: number
  codigo: string
  cliente_id: number
  cliente_nombre: string
  prenda_nombre: string
  // Workshop phase from the backend (migración 0030):
  // corte → costura → acabados → calidad → listo. Single source of truth
  // for the kanban column; `estado` stays as the legacy enum for terminal
  // display (completado/cancelado).
  fase: string
  estado: string
  estadoReal?: string
  producto_id: number | null
  cantidad: number
  cantidad_producida: number
  costo_unitario_snapshot?: number | string | null
  mano_obra_real?: number | string | null
  energia_real?: number | string | null
  precio_venta: number
  costo_produccion: number
  utilidad_neta: number
  margen_pct: number
  fecha: string
  observaciones?: string
}

const search = ref('')
const viewMode = ref<'kanban' | 'tabla'>('kanban')
// Fase filter chip → GET /pedidos-produccion?fase=. '' = todas.
const filtroFase = ref<string>('')
const showNuevoPedidoModal = ref(false)
const showDetallePedidoModal = ref(false)
const pedidoSeleccionado = ref<PedidoDisplay | null>(null)
const pedidos = ref<PedidoDisplay[]>([])

async function cargarPedidos() {
  try {
    const params = filtroFase.value ? { limit: 100, fase: filtroFase.value } : { limit: 100 }
    const res = await produccionService.list(params)
    pedidos.value = res.items.map((p) => ({
      id: p.id,
      codigo: `ORD-${p.id}`,
      cliente_id: p.cliente_id ?? 0,
      cliente_nombre: p.cliente_nombre || p.nombre_variante || p.nombre_producto || '—',
      prenda_nombre: p.nombre_producto || (p.producto_id ? `Producto #${p.producto_id}` : '—'),
      fase: p.fase || 'corte',
      estado: (p.fase || 'corte').toUpperCase(),
      estadoReal: p.estado,
      producto_id: p.producto_id ?? null,
      cantidad: p.cantidad,
      cantidad_producida: p.cantidad_producida ?? 0,
      costo_unitario_snapshot: p.costo_unitario_snapshot ?? null,
      mano_obra_real: p.mano_obra_real ?? null,
      energia_real: p.energia_real ?? null,
      // PedidoProduccionRead no trae montos de venta (sin join a productos,
      // fuera de alcance); se mantienen en 0 y el template los oculta para
      // no mostrar $0 mentiroso.
      precio_venta: 0,
      costo_produccion: 0,
      utilidad_neta: 0,
      margen_pct: 0,
      fecha: p.fecha_pedido || new Date().toISOString().split('T')[0],
      observaciones: p.observaciones || undefined,
    }))
  } catch (e) {
    console.error('Error cargando pedidos reales:', e)
  }
}

function seleccionarFase(fase: string) {
  filtroFase.value = fase
  void cargarPedidos()
}

onMounted(() => {
  cargarPedidos()
})

// Anti doble-submit por fila: un doble clic en "Avanzar" enviaba dos PATCH.
// Terminal = sin transiciones (completado/cancelado del enum legacy).
const transicionandoId = ref<number | null>(null)
function estadoRealDe(p: PedidoDisplay): string | undefined {
  return p.estadoReal
}
function esTerminal(p: PedidoDisplay): boolean {
  const raw = estadoRealDe(p)
  return raw === 'completado' || raw === 'cancelado'
}
function etapaBadge(p: PedidoDisplay): string {
  if (estadoRealDe(p) === 'cancelado') return 'CANCELADO'
  if (estadoRealDe(p) === 'completado') return 'LISTO'
  return p.estado
}
function tieneCostoSnapshot(p: PedidoDisplay): boolean {
  return p.costo_unitario_snapshot !== null && p.costo_unitario_snapshot !== undefined
}
// Real labor/energy cost derived from TiempoFase rows — only when the backend brings it.
function tieneCostosReales(p: PedidoDisplay): boolean {
  return (
    (p.mano_obra_real !== null && p.mano_obra_real !== undefined) ||
    (p.energia_real !== null && p.energia_real !== undefined)
  )
}

function abrirFichaTaller(p: PedidoDisplay) {
  pedidoSeleccionado.value = p
  showDetallePedidoModal.value = true
}

// Kanban columns = the 5 real workshop phases (backend CHECK
// ck_pedidos_produccion_fase). Display labels in uppercase.
const estados: string[] = [...FASES_PRODUCCION.map((f) => f.toUpperCase())]
// eslint-disable-next-line @typescript-eslint/no-explicit-any

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

const pedidosFiltrados = computed(() => {
  return pedidos.value.filter((p) => {
    const q = search.value.trim().toLowerCase()
    return (
      !q ||
      (p.codigo && p.codigo.toLowerCase().includes(q)) ||
      (p.cliente_nombre && p.cliente_nombre.toLowerCase().includes(q)) ||
      (p.prenda_nombre && p.prenda_nombre.toLowerCase().includes(q))
    )
  })
})

function getPedidosPorEstado(est: string) {
  return pedidosFiltrados.value.filter((p) => p.estado === est)
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any

// Avance secuencial de fase (PATCH /pedidos-produccion/{id} {fase}):
// corte → costura → acabados → calidad → listo. El backend valida el paso
// (422 fase inválida, 400 salto adelante o salida de listo). Devolución por
// reproceso a cualquier fase anterior permitida (tiempos se editan por fila).
// Los mensajes del backend se muestran tal cual, sin reescritura.
const FASE_DISPLAY: Record<string, string> = {
  corte: 'CORTE',
  costura: 'COSTURA',
  acabados: 'ACABADOS',
  calidad: 'CALIDAD',
  listo: 'LISTO',
}

async function avanzarEstado(pedido: PedidoDisplay) {
  if (transicionandoId.value === pedido.id) return
  const next = siguienteFase(pedido.fase)
  if (!next) {
    showToast('info', 'Sin transición', `La orden ${pedido.codigo} ya está en su fase final (LISTO).`)
    return
  }
  transicionandoId.value = pedido.id
  try {
    await produccionService.update(pedido.id, { fase: next })
    await cargarPedidos()
    showToast('success', 'Fase actualizada', `Orden ${pedido.codigo} avanzada a ${FASE_DISPLAY[next] ?? next}.`)
  } catch (e: unknown) {
    // 400/422/409 del backend, verbatim (incluye el detalle por-insumo del 409).
    showToast('error', 'No se pudo avanzar', extractApiDetail(e))
  } finally {
    transicionandoId.value = null
  }
}

// Devolución por reproceso (ej: calidad → costura): cualquier fase anterior,
// nunca desde 'listo' (lote ya acreditado) ni en la primera fase.
function fasesAnteriores(fase: string | null | undefined): string[] {
  const idx = FASES_PRODUCCION.indexOf(fase ?? '')
  if (idx <= 0) return []
  return FASES_PRODUCCION.slice(0, idx)
}
function puedeDevolver(p: PedidoDisplay): boolean {
  if (esTerminal(p)) return false
  const f = (p.fase || 'corte').toLowerCase()
  return f !== 'corte' && f !== 'listo'
}
const devolverSel = ref<Record<number, string>>({})
async function devolverEstado(pedido: PedidoDisplay) {
  if (transicionandoId.value === pedido.id) return
  const previas = fasesAnteriores((pedido.fase || 'corte').toLowerCase())
  const destino = devolverSel.value[pedido.id] || previas[previas.length - 1]
  if (!destino) return
  transicionandoId.value = pedido.id
  try {
    await produccionService.update(pedido.id, { fase: destino })
    await cargarPedidos()
    showToast('success', 'Fase devuelta', `Orden ${pedido.codigo} devuelta a ${FASE_DISPLAY[destino] ?? destino} para reproceso.`)
  } catch (e: unknown) {
    showToast('error', 'No se pudo devolver', extractApiDetail(e))
  } finally {
    transicionandoId.value = null
  }
}

function abrirWhatsApp(p: PedidoDisplay) {
  const msg = encodeURIComponent(`¡Hola ${p.cliente_nombre}! Te escribimos de Arpía sobre tu pedido *${p.codigo}* (${p.prenda_nombre}). Estado actual: *${p.estado}*. ✨`)
  window.open(waUrl(null, msg), '_blank')
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div class="space-y-1.5">
        <div class="flex items-center gap-2.5 flex-wrap">
          <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
            Gestión de Pedidos & Producción en Taller
          </h1>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
            {{ pedidos.length }} Pedidos Registrados
          </span>
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Tablero por fases de confección: Corte, Costura, Acabados, Calidad y Listo. Avance de a una fase; devolución a cualquier fase anterior por reproceso (Listo no se mueve).
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Button
          label="Cotizador Rápido"
          icon="pi pi-calculator"
          size="small"
          severity="secondary"
          outlined
          class="text-xs font-semibold"
          @click="router.push('/cotizador')"
        />
        <Button
          label="Nuevo Pedido"
          icon="pi pi-plus"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="showNuevoPedidoModal = true"
        />
      </div>
    </div>

    <!-- Search & View Mode Controls -->
    <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
      <div class="w-full sm:w-80">
        <span class="p-input-icon-left w-full">
          <InputText
            v-model="search"
            placeholder="Buscar por código, cliente o prenda..."
            class="w-full text-xs"
          />
        </span>
      </div>

      <div class="inline-flex bg-stone-950 rounded-lg p-0.5 border border-stone-800 self-end sm:self-auto">
        <button
          type="button"
          class="px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5"
          :class="viewMode === 'kanban' ? 'bg-amber-500 text-stone-950 shadow' : 'text-stone-400 hover:text-stone-200'"
          @click="viewMode = 'kanban'"
        >
          <i class="pi pi-th-large text-xs" />
          <span>Tablero Kanban</span>
        </button>
        <button
          type="button"
          class="px-3 py-1.5 rounded-md text-xs font-semibold transition flex items-center gap-1.5"
          :class="viewMode === 'tabla' ? 'bg-amber-500 text-stone-950 shadow' : 'text-stone-400 hover:text-stone-200'"
          @click="viewMode = 'tabla'"
        >
          <i class="pi pi-table text-xs" />
          <span>Vista de Lista</span>
        </button>
      </div>
    </div>

    <!-- Fase filter chips → GET /pedidos-produccion?fase= -->
    <div class="flex flex-wrap gap-1.5">
      <button
        type="button"
        class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition"
        :class="filtroFase === '' ? 'bg-amber-500 text-stone-950 border-amber-500 shadow' : 'bg-stone-900 text-stone-400 border-stone-800 hover:text-stone-200 hover:border-stone-700'"
        @click="seleccionarFase('')"
      >
        Todas
      </button>
      <button
        v-for="f in FASES_PRODUCCION"
        :key="f"
        type="button"
        class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition uppercase"
        :class="filtroFase === f ? 'bg-amber-500 text-stone-950 border-amber-500 shadow' : 'bg-stone-900 text-stone-400 border-stone-800 hover:text-stone-200 hover:border-stone-700'"
        @click="seleccionarFase(f)"
      >
        {{ FASE_DISPLAY[f] ?? f }}
      </button>
    </div>

    <!-- Kanban Board View -->
    <div v-if="viewMode === 'kanban'" class="overflow-x-auto pb-4">
      <div class="flex gap-4 min-w-[1100px]">
        <div
          v-for="est in estados"
          :key="est"
          class="w-72 flex-shrink-0 bg-stone-900/60 border border-stone-800/80 rounded-2xl p-3 flex flex-col justify-between min-h-[500px]"
        >
          <!-- Column Header -->
          <div>
            <div class="flex items-center justify-between pb-2.5 border-b border-stone-800">
              <span class="text-xs font-bold uppercase tracking-wider text-amber-400">
                {{ est }}
              </span>
              <span class="w-5 h-5 rounded-full bg-stone-800 text-stone-300 text-[11px] font-mono font-bold flex items-center justify-center">
                {{ getPedidosPorEstado(est).length }}
              </span>
            </div>

            <!-- Cards Container -->
            <div class="space-y-3 pt-3">
              <div
                v-for="p in getPedidosPorEstado(est)"
                :key="p.id"
                class="bg-stone-950/90 border border-stone-800 rounded-xl p-3.5 space-y-2.5 shadow-md hover:border-amber-500/40 transition group"
              >
                <!-- Card Header -->
                <div class="flex justify-between items-start">
                  <div>
                    <span class="font-mono text-xs font-bold text-amber-300">{{ p.codigo }}</span>
                    <h4 class="text-xs font-bold text-stone-100 m-0 mt-0.5">{{ p.cliente_nombre }}</h4>
                  </div>
                  <div class="flex items-center gap-1">
                    <button
                      type="button"
                      class="text-amber-400 hover:text-amber-300 transition p-1"
                      title="Ver Ficha de Taller & Tiempos"
                      @click="abrirFichaTaller(p)"
                    >
                      <i class="pi pi-clock text-xs" />
                    </button>
                    <button
                      type="button"
                      class="text-emerald-400 hover:text-emerald-300 transition p-1"
                      title="WhatsApp"
                      @click="abrirWhatsApp(p)"
                    >
                      <i class="pi pi-whatsapp text-sm" />
                    </button>
                  </div>
                </div>

                <!-- Garment Info -->
                <div
                  class="text-xs text-stone-300 bg-stone-900/60 p-2 rounded border border-stone-800/60 leading-snug cursor-pointer hover:border-amber-500/40 transition"
                  @click="abrirFichaTaller(p)"
                >
                  {{ p.prenda_nombre }}
                </div>

                <!-- Lote: cantidad pedida vs producida + costo snapshot (solo cuando el backend lo trae) -->
                <div class="text-[11px] text-stone-400 bg-stone-900/60 p-2 rounded border border-stone-800/60 font-mono leading-snug">
                  <div class="flex justify-between">
                    <span>Cantidad:</span>
                    <span class="text-stone-200 font-bold">{{ p.cantidad_producida }}/{{ p.cantidad }} uds</span>
                  </div>
                  <div v-if="tieneCostoSnapshot(p)" class="flex justify-between pt-0.5">
                    <span>Costo unit.:</span>
                    <span class="text-emerald-400 font-bold">{{ formatCOP(Number(p.costo_unitario_snapshot)) }}</span>
                  </div>
                  <div v-if="tieneCostosReales(p)" class="flex justify-between pt-0.5">
                    <span>Mano obra real:</span>
                    <span class="text-sky-300 font-bold">{{ p.mano_obra_real !== null && p.mano_obra_real !== undefined ? formatCOP(Number(p.mano_obra_real)) : '—' }}</span>
                  </div>
                  <div v-if="tieneCostosReales(p)" class="flex justify-between pt-0.5">
                    <span>Energía real:</span>
                    <span class="text-sky-300 font-bold">{{ p.energia_real !== null && p.energia_real !== undefined ? formatCOP(Number(p.energia_real)) : '—' }}</span>
                  </div>
                </div>

                <!-- Price & Profit: la API no trae montos de venta, no se muestran -->

                <!-- Stage Movement: avance + devolución por reproceso -->
                <div class="flex justify-end items-center gap-2 pt-2 border-t border-stone-800/60">
                  <select
                    v-if="puedeDevolver(p)"
                    v-model="devolverSel[p.id]"
                    class="bg-stone-950 border border-stone-700 text-stone-300 text-[11px] rounded-lg px-2 py-1 font-mono focus:border-amber-400 focus:outline-none"
                    :title="`Devolver ${p.codigo} a una fase anterior`"
                  >
                    <option :value="undefined" disabled selected>◀ Devolver a…</option>
                    <option v-for="f in fasesAnteriores((p.fase || 'corte').toLowerCase())" :key="f" :value="f">{{ FASE_DISPLAY[f] ?? f }}</option>
                  </select>
                  <button
                    v-if="puedeDevolver(p)"
                    type="button"
                    class="text-[11px] text-sky-400 hover:text-sky-300 font-bold transition disabled:opacity-30 disabled:cursor-not-allowed"
                    :disabled="!devolverSel[p.id] || transicionandoId === p.id"
                    @click="devolverEstado(p)"
                  >
                    Devolver
                  </button>
                  <button
                    type="button"
                    class="text-[11px] text-amber-400 hover:text-amber-300 font-bold transition disabled:opacity-30 disabled:cursor-not-allowed"
                    :disabled="p.estado === 'LISTO' || transicionandoId === p.id || esTerminal(p)"
                    @click="avanzarEstado(p)"
                  >
                    Avanzar fase →
                  </button>
                </div>
              </div>

              <div
                v-if="getPedidosPorEstado(est).length === 0"
                class="py-8 text-center text-xs text-stone-500 italic"
              >
                Sin pedidos en esta fase
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Table View (desktop) + Cards (mobile) -->
    <div v-else class="bg-stone-900/80 border border-stone-800 rounded-2xl overflow-hidden shadow-xl">
      <div class="hidden overflow-x-auto md:block">
        <table class="w-full min-w-[760px] text-left text-xs border-collapse">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 bg-stone-950/60 uppercase tracking-wider font-semibold">
              <th class="py-3 px-4 sticky left-0 z-10 bg-stone-950/95">Código / Fecha</th>
              <th class="py-3 px-4">Cliente</th>
              <th class="py-3 px-4 min-w-[180px]">Prenda / Modelo</th>
              <th class="py-3 px-4 text-center whitespace-nowrap">Fase de Producción</th>
              <th class="py-3 px-4 text-right whitespace-nowrap">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/50 text-stone-200">
            <tr v-for="p in pedidosFiltrados" :key="p.id" class="hover:bg-stone-800/30">
              <td class="py-3 px-4 sticky left-0 z-10 bg-stone-900/95">
                <div class="font-mono font-bold text-amber-300">{{ p.codigo }}</div>
                <div class="text-[11px] text-stone-400">{{ p.fecha }}</div>
              </td>
              <td class="py-3 px-4 font-medium text-stone-100">{{ p.cliente_nombre }}</td>
              <td class="py-3 px-4">{{ p.prenda_nombre }}</td>
              <td class="py-3 px-4 text-center whitespace-nowrap">
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-950/60 text-amber-300 border border-amber-500/30">
                  {{ etapaBadge(p) }}
                </span>
                <div class="text-[10px] text-stone-500 font-mono mt-1">{{ p.cantidad_producida }}/{{ p.cantidad }} uds</div>
                <div v-if="tieneCostoSnapshot(p)" class="text-[10px] text-emerald-400 font-mono">{{ formatCOP(Number(p.costo_unitario_snapshot)) }}/ud</div>
                <div v-if="tieneCostosReales(p)" class="text-[10px] text-sky-300 font-mono">MO real {{ p.mano_obra_real !== null && p.mano_obra_real !== undefined ? formatCOP(Number(p.mano_obra_real)) : '—' }} · E {{ p.energia_real !== null && p.energia_real !== undefined ? formatCOP(Number(p.energia_real)) : '—' }}</div>
              </td>
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <div class="flex items-center justify-end gap-2">
                  <select
                    v-if="puedeDevolver(p)"
                    v-model="devolverSel[p.id]"
                    class="bg-stone-950 border border-stone-700 text-stone-300 text-[11px] rounded-lg px-2 py-1 font-mono focus:border-amber-400 focus:outline-none"
                    :title="`Devolver ${p.codigo} a una fase anterior`"
                  >
                    <option :value="undefined" disabled selected>◀ Devolver a…</option>
                    <option v-for="f in fasesAnteriores((p.fase || 'corte').toLowerCase())" :key="f" :value="f">{{ FASE_DISPLAY[f] ?? f }}</option>
                  </select>
                  <button
                    v-if="puedeDevolver(p)"
                    type="button"
                    class="text-sky-400 hover:underline font-bold text-xs disabled:opacity-30 disabled:cursor-not-allowed"
                    :disabled="!devolverSel[p.id] || transicionandoId === p.id"
                    @click="devolverEstado(p)"
                  >
                    Devolver
                  </button>
                  <button
                    type="button"
                    class="text-amber-400 hover:underline font-bold text-xs disabled:opacity-30 disabled:cursor-not-allowed"
                    :disabled="transicionandoId === p.id || esTerminal(p)"
                    @click="avanzarEstado(p)"
                  >
                    Avanzar Fase
                  </button>
                  <button
                    type="button"
                    class="text-emerald-400 hover:text-emerald-300 p-1"
                    title="WhatsApp"
                    @click="abrirWhatsApp(p)"
                  >
                    <i class="pi pi-whatsapp text-xs" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <!-- Mobile cards: same pedidosFiltrados. No horizontal scroll. -->
      <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
        <div v-if="!pedidosFiltrados.length" class="text-center py-8 text-sm text-stone-500">Sin pedidos con los filtros actuales.</div>
        <div v-for="p in pedidosFiltrados" :key="p.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
          <div class="flex items-start justify-between gap-2 min-w-0">
            <div class="min-w-0">
              <div class="font-mono font-bold text-sm text-amber-300">{{ p.codigo }}</div>
              <div class="text-xs text-stone-500">{{ p.fecha }}</div>
            </div>
            <span class="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-amber-950/60 text-amber-300 border border-amber-500/30 shrink-0">{{ etapaBadge(p) }}</span>
          </div>
          <div class="font-bold text-sm text-stone-100">{{ p.prenda_nombre }}</div>
          <div class="text-sm text-stone-300">{{ p.cliente_nombre }}</div>
          <div class="text-xs text-stone-500 font-mono">{{ p.cantidad_producida }}/{{ p.cantidad }} uds<span v-if="tieneCostoSnapshot(p)" class="text-emerald-400"> · {{ formatCOP(Number(p.costo_unitario_snapshot)) }}/ud</span><span v-if="tieneCostosReales(p)" class="text-sky-300"> · MO {{ p.mano_obra_real !== null && p.mano_obra_real !== undefined ? formatCOP(Number(p.mano_obra_real)) : '—' }}</span></div>
          <div v-if="puedeDevolver(p)" class="flex gap-2 pt-1">
            <select
              v-model="devolverSel[p.id]"
              class="flex-1 min-h-[40px] bg-stone-950 border border-stone-700 text-stone-300 text-sm rounded-lg px-2 font-mono focus:border-amber-400 focus:outline-none"
            >
              <option :value="undefined" disabled selected>◀ Devolver a…</option>
              <option v-for="f in fasesAnteriores((p.fase || 'corte').toLowerCase())" :key="f" :value="f">{{ FASE_DISPLAY[f] ?? f }}</option>
            </select>
            <button type="button" class="min-w-[44px] min-h-[40px] px-3 rounded-lg bg-stone-800 text-sky-400 text-sm font-bold disabled:opacity-30" :disabled="!devolverSel[p.id] || transicionandoId === p.id" @click="devolverEstado(p)">OK</button>
          </div>
          <div class="flex gap-2 pt-1">
            <button type="button" class="flex-1 min-h-[40px] rounded-lg bg-amber-500 text-stone-950 text-sm font-bold disabled:opacity-30" :disabled="transicionandoId === p.id || esTerminal(p)" @click="avanzarEstado(p)">Avanzar Fase</button>
            <button type="button" class="min-w-[44px] min-h-[40px] px-3 rounded-lg bg-stone-800 text-emerald-400" title="WhatsApp" @click="abrirWhatsApp(p)"><i class="pi pi-whatsapp text-xs" /></button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <NuevoPedidoModal v-model:visible="showNuevoPedidoModal" @pedido-creado="cargarPedidos" />
    <DetallePedidoTallerModal
      v-model:visible="showDetallePedidoModal"
      :pedido="pedidoSeleccionado"
      @fase-avanzada="cargarPedidos"
      @tiempos-actualizados="cargarPedidos"
      @costos-aplicados="cargarPedidos"
    />
  </div>
</template>
