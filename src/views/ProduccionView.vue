<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useAtelierStore, type PedidoProduccion, type EstadoPedido } from '@/stores/atelier'
import { useProduccion } from '@/composables/useProduccion'
import NuevoPedidoModal from '@/components/atelier/NuevoPedidoModal.vue'
import DetallePedidoTallerModal from '@/components/atelier/DetallePedidoTallerModal.vue'
import { showToast } from '@/utils/toast'

const router = useRouter()
const atelier = useAtelierStore()
const { isMock, list: listPedidosApi } = useProduccion()
const produccionService = useProduccion()

const search = ref('')
const viewMode = ref<'kanban' | 'tabla'>('kanban')
const showNuevoPedidoModal = ref(false)
const showDetallePedidoModal = ref(false)
const pedidoSeleccionado = ref<PedidoProduccion | null>(null)
const pedidosApi = ref<PedidoProduccion[]>([])

async function cargarPedidosReales() {
  if (isMock.value) return
  try {
    const res = await listPedidosApi({ limit: 100 })
    pedidosApi.value = res.items.map((p: any) => ({
      id: p.id,
      codigo: `ORD-${p.id}`,
      cliente_id: 0,
      cliente_nombre: p.nombre_variante || p.nombre_producto || 'Taller Arpía',
      prenda_nombre: p.nombre_producto || `Producto #${p.producto_id}`,
      estado: p.estado === 'pendiente' ? 'CORTE' : p.estado === 'en_produccion' ? 'COSTURA' : p.estado === 'completado' ? 'LISTO' : 'COTIZADO',
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
  cargarPedidosReales()
})

watch(isMock, () => void cargarPedidosReales())

const pedidosList = computed(() => (isMock.value ? atelier.pedidos : pedidosApi.value))

function abrirFichaTaller(p: PedidoProduccion) {
  pedidoSeleccionado.value = p
  showDetallePedidoModal.value = true
}

const estados: EstadoPedido[] = [
  'COTIZADO',
  'RESERVADO',
  'CORTE',
  'COSTURA',
  'ACABADOS',
  'CALIDAD',
  'LISTO',
  'ENTREGADO',
]

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

const pedidosFiltrados = computed(() => {
  return pedidosList.value.filter((p) => {
    const q = search.value.trim().toLowerCase()
    return (
      !q ||
      (p.codigo && p.codigo.toLowerCase().includes(q)) ||
      (p.cliente_nombre && p.cliente_nombre.toLowerCase().includes(q)) ||
      (p.prenda_nombre && p.prenda_nombre.toLowerCase().includes(q))
    )
  })
})

function getPedidosPorEstado(est: EstadoPedido) {
  return pedidosFiltrados.value.filter((p) => p.estado === est)
}

async function avanzarEstado(pedido: PedidoProduccion) {
  const currentIndex = estados.indexOf(pedido.estado)
  if (currentIndex < estados.length - 1) {
    const nextState = estados[currentIndex + 1]
    if (isMock.value) {
      atelier.cambiarEstadoPedido(pedido.id, nextState)
      showToast('success', 'Etapa Actualizada', `Orden ${pedido.codigo} avanzada a ${nextState}.`)
      return
    }
    try {
      await produccionService.update(pedido.id, { estado: nextState } as unknown as Record<string, unknown> as never)
      await cargarPedidosReales()
      showToast('success', 'Etapa Actualizada', `Orden ${pedido.codigo} avanzada a ${nextState}.`)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error al avanzar estado'
      showToast('error', 'Error', String(msg))
    }
  }
}

async function retrocederEstado(pedido: PedidoProduccion) {
  const currentIndex = estados.indexOf(pedido.estado)
  if (currentIndex > 0) {
    const prevState = estados[currentIndex - 1]
    if (isMock.value) {
      atelier.cambiarEstadoPedido(pedido.id, prevState)
      showToast('info', 'Etapa Actualizada', `Orden ${pedido.codigo} movida a ${prevState}.`)
      return
    }
    try {
      await produccionService.update(pedido.id, { estado: prevState } as unknown as Record<string, unknown> as never)
      await cargarPedidosReales()
      showToast('info', 'Etapa Actualizada', `Orden ${pedido.codigo} movida a ${prevState}.`)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Error al retroceder estado'
      showToast('error', 'Error', String(msg))
    }
  }
}

function abrirWhatsApp(p: PedidoProduccion) {
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
            {{ atelier.pedidos.length }} Pedidos Registrados
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

                <!-- Price & Profit -->
                <div class="flex justify-between text-[11px] font-mono pt-1">
                  <span class="text-stone-400">Venta: {{ formatCOP(p.precio_venta) }}</span>
                  <span class="text-emerald-400 font-bold">Utilidad: {{ formatCOP(p.utilidad_neta) }}</span>
                </div>

                <!-- Stage Movement Buttons -->
                <div class="flex justify-between items-center pt-2 border-t border-stone-800/60">
                  <button
                    type="button"
                    class="text-[11px] text-stone-400 hover:text-stone-200 transition disabled:opacity-30 disabled:cursor-not-allowed"
                    :disabled="estados.indexOf(p.estado) === 0"
                    @click="retrocederEstado(p)"
                  >
                    ← Anterior
                  </button>
                  <button
                    type="button"
                    class="text-[11px] text-amber-400 hover:text-amber-300 font-bold transition disabled:opacity-30 disabled:cursor-not-allowed"
                    :disabled="estados.indexOf(p.estado) === estados.length - 1"
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

    <!-- Table View -->
    <div v-else class="bg-stone-900/80 border border-stone-800 rounded-2xl overflow-hidden shadow-xl">
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs border-collapse">
          <thead>
            <tr class="border-b border-stone-800 text-stone-400 bg-stone-950/60 uppercase tracking-wider font-semibold">
              <th class="py-3 px-4">Código / Fecha</th>
              <th class="py-3 px-4">Cliente</th>
              <th class="py-3 px-4">Prenda / Modelo</th>
              <th class="py-3 px-4 text-center">Fase de Producción</th>
              <th class="py-3 px-4 text-right">Precio Venta</th>
              <th class="py-3 px-4 text-right">Utilidad Neta</th>
              <th class="py-3 px-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-800/50 text-stone-200">
            <tr v-for="p in pedidosFiltrados" :key="p.id" class="hover:bg-stone-800/30">
              <td class="py-3 px-4">
                <div class="font-mono font-bold text-amber-300">{{ p.codigo }}</div>
                <div class="text-[11px] text-stone-400">{{ p.fecha }}</div>
              </td>
              <td class="py-3 px-4 font-medium text-stone-100">{{ p.cliente_nombre }}</td>
              <td class="py-3 px-4">{{ p.prenda_nombre }}</td>
              <td class="py-3 px-4 text-center">
                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-950/60 text-amber-300 border border-amber-500/30">
                  {{ p.estado }}
                </span>
              </td>
              <td class="py-3 px-4 text-right font-mono">{{ formatCOP(p.precio_venta) }}</td>
              <td class="py-3 px-4 text-right font-mono font-bold text-emerald-400">{{ formatCOP(p.utilidad_neta) }}</td>
              <td class="py-3 px-4 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button
                    type="button"
                    class="text-amber-400 hover:underline font-bold text-xs"
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
    </div>

    <!-- Modals -->
    <NuevoPedidoModal v-model:visible="showNuevoPedidoModal" />
    <DetallePedidoTallerModal
      v-model:visible="showDetallePedidoModal"
      :pedido="pedidoSeleccionado"
    />
  </div>
</template>
