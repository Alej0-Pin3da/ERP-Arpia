<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useProduccion } from '@/composables/useProduccion'
import NuevoPedidoModal from '@/components/atelier/NuevoPedidoModal.vue'
import DetallePedidoTallerModal from '@/components/atelier/DetallePedidoTallerModal.vue'
import { showToast } from '@/utils/toast'

const router = useRouter()
const produccionService = useProduccion()

/** REAL display shape: backend PedidoProduccionRead normalized for this view. */
interface PedidoDisplay {
  id: number
  codigo: string
  cliente_id: number
  cliente_nombre: string
  prenda_nombre: string
  // Display: etapas del kanban. estadoReal guarda el enum del backend
  // (pendiente/en_produccion/completado/cancelado) para las transiciones.
  estado: string
  estadoReal?: string
  precio_venta: number
  costo_produccion: number
  utilidad_neta: number
  margen_pct: number
  fecha: string
  observaciones?: string
}

const search = ref('')
const viewMode = ref<'kanban' | 'tabla'>('kanban')
const showNuevoPedidoModal = ref(false)
const showDetallePedidoModal = ref(false)
const pedidoSeleccionado = ref<PedidoDisplay | null>(null)
const pedidos = ref<PedidoDisplay[]>([])

async function cargarPedidos() {
  try {
    const res = await produccionService.list({ limit: 100 })
    pedidos.value = res.items.map((p: any) => ({
      id: p.id,
      codigo: `ORD-${p.id}`,
      cliente_id: p.cliente_id ?? 0,
      cliente_nombre: p.cliente_nombre || p.nombre_variante || p.nombre_producto || 'Taller Arpía',
      prenda_nombre: p.nombre_producto || `Producto #${p.producto_id}`,
      estado: p.estado === 'pendiente' ? 'CORTE' : p.estado === 'en_produccion' ? 'COSTURA' : p.estado === 'completado' ? 'LISTO' : 'COTIZADO',
      estadoReal: p.estado,
      // PedidoProduccionRead no trae montos (sin join a productos, fuera de alcance);
      // se mantienen en 0 y el template los oculta para no mostrar $0 mentiroso.
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

onMounted(() => {
  cargarPedidos()
})

// Anti doble-submit por fila: un doble clic en "Siguiente" saltaba etapas
// (pendiente→en_produccion→completado de una). Terminal = sin transiciones.
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
  return p.estado
}

function abrirFichaTaller(p: PedidoDisplay) {
  pedidoSeleccionado.value = p
  showDetallePedidoModal.value = true
}

const estados: string[] = [
  'COTIZADO',
  'RESERVADO',
  'CORTE',
  'COSTURA',
  'ACABADOS',
  'CALIDAD',
  'LISTO',
  'ENTREGADO',
]
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

// Transiciones dentro del enum del backend (CHECK ck_pedidos_produccion_estado):
// pendiente -> en_produccion -> completado. Cancelado es terminal.
const AVANZAR_REAL: Record<string, string> = { pendiente: 'en_produccion', en_produccion: 'completado' }
const RETROCEDER_REAL: Record<string, string> = { en_produccion: 'pendiente', completado: 'en_produccion' }
const ETAPA_DISPLAY: Record<string, string> = { pendiente: 'CORTE', en_produccion: 'COSTURA', completado: 'LISTO', cancelado: 'CANCELADO' }

async function avanzarEstado(pedido: PedidoDisplay) {
  if (transicionandoId.value === pedido.id) return
  const raw = estadoRealDe(pedido)
  const next = raw ? AVANZAR_REAL[raw] : undefined
  if (!next) {
    showToast('info', 'Sin transición', raw === 'cancelado' ? `La orden ${pedido.codigo} está cancelada.` : `La orden ${pedido.codigo} ya está en su etapa final.`)
    return
  }
  transicionandoId.value = pedido.id
  try {
    await produccionService.update(pedido.id, { estado: next } as unknown as Record<string, unknown> as never)
    await cargarPedidos()
    showToast('success', 'Etapa Actualizada', `Orden ${pedido.codigo} avanzada a ${ETAPA_DISPLAY[next] ?? next}.`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al avanzar estado'
    showToast('error', 'Error', String(msg))
  } finally {
    transicionandoId.value = null
  }
}

async function retrocederEstado(pedido: PedidoDisplay) {
  if (transicionandoId.value === pedido.id) return
  const raw = estadoRealDe(pedido)
  const prev = raw ? RETROCEDER_REAL[raw] : undefined
  if (!prev) {
    showToast('info', 'Sin transición', `La orden ${pedido.codigo} no puede retroceder desde ${ETAPA_DISPLAY[raw ?? ''] ?? raw ?? 'su estado'}.`)
    return
  }
  transicionandoId.value = pedido.id
  try {
    await produccionService.update(pedido.id, { estado: prev } as unknown as Record<string, unknown> as never)
    await cargarPedidos()
    showToast('info', 'Etapa Actualizada', `Orden ${pedido.codigo} movida a ${ETAPA_DISPLAY[prev] ?? prev}.`)
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Error al retroceder estado'
    showToast('error', 'Error', String(msg))
  } finally {
    transicionandoId.value = null
  }
}

function abrirWhatsApp(p: PedidoDisplay) {
  const msg = encodeURIComponent(`¡Hola ${p.cliente_nombre}! Te escribimos de Atelier Arpía sobre tu pedido *${p.codigo}* (${p.prenda_nombre}). Estado actual: *${p.estado}*. ✨`)
  window.open(`https://wa.me/573124567890?text=${msg}`, '_blank')
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
          Tablero visual por etapas de confección: Cotizado, Reservado, Corte, Costura, Acabados, Calidad, Listo y Entregado.
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

    <!-- Kanban Board View -->
    <div v-if="viewMode === 'kanban'" class="overflow-x-auto pb-4">
      <div class="flex gap-4 min-w-[1400px]">
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

                <!-- Price & Profit: la API no trae montos, no se muestran -->

                <!-- Stage Movement Buttons -->
                <div class="flex justify-between items-center pt-2 border-t border-stone-800/60">
                  <button
                    type="button"
                    class="text-[11px] text-stone-400 hover:text-stone-200 transition disabled:opacity-30 disabled:cursor-not-allowed"
                    :disabled="estados.indexOf(p.estado) === 0 || transicionandoId === p.id || esTerminal(p)"
                    @click="retrocederEstado(p)"
                  >
                    ← Anterior
                  </button>
                  <button
                    type="button"
                    class="text-[11px] text-amber-400 hover:text-amber-300 font-bold transition disabled:opacity-30 disabled:cursor-not-allowed"
                    :disabled="estados.indexOf(p.estado) === estados.length - 1 || transicionandoId === p.id || esTerminal(p)"
                    @click="avanzarEstado(p)"
                  >
                    Siguiente →
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
              </td>
              <td class="py-3 px-4 text-right whitespace-nowrap">
                <div class="flex items-center justify-end gap-2">
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
    />
  </div>
</template>
