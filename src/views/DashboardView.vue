<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import { useAtelierStore } from '@/stores/atelier'
import { useMode } from '@/composables/useMode'
import { useInsumos } from '@/composables/useInsumos'
import { useProduccion } from '@/composables/useProduccion'
import { useVentas } from '@/composables/useVentas'
import AsistenteIaModal from '@/components/atelier/AsistenteIaModal.vue'
import NuevoPedidoModal from '@/components/atelier/NuevoPedidoModal.vue'
import SugerirOrdenModal from '@/components/atelier/SugerirOrdenModal.vue'

const router = useRouter()
const atelier = useAtelierStore()
const { isMock } = useMode()
const { insumos: insumosReal } = useInsumos()
const { pedidos: pedidosReal } = useProduccion()
const { ventas: ventasReal } = useVentas()

const insumosCriticosReal = computed(() => (insumosReal.value as any[]).filter((i: any) => (i.stock_actual ?? i.stock ?? 0) <= (i.stock_minimo ?? 0)))
const insumosCriticosDisplay = computed(() => isMock.value ? insumosCriticosDisplay : insumosCriticosReal.value)
const pedidosDisplay = computed(() => isMock.value ? pedidosDisplay : (pedidosReal.value as any[]))
const ventasDisplay = computed(() => isMock.value ? atelier.ventas : (ventasReal.value as any[]))

onMounted(() => { if (!isMock.value) { /* composables auto-fetch via watch(isMock) */ } })

const showIaModal = ref(false)
const showNuevoPedidoModal = ref(false)
const showSugerirModal = ref(false)

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function getEstadoBadgeClass(estado: string) {
  switch (estado) {
    case 'ENTREGADO':
      return 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
    case 'COSTURA':
      return 'bg-amber-950/60 text-amber-300 border border-amber-500/30'
    case 'CORTE':
      return 'bg-blue-950/60 text-blue-300 border border-blue-500/30'
    case 'LISTO':
      return 'bg-purple-950/60 text-purple-300 border border-purple-500/30'
    default:
      return 'bg-stone-800 text-stone-300 border border-stone-700'
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Top Banner: Panel General de Operaciones -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl relative overflow-hidden">
      <div class="absolute -right-12 -top-12 w-48 h-48 bg-amber-500/5 rounded-full blur-3xl pointer-events-none" />

      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 relative z-10">
        <div class="space-y-1.5">
          <div class="flex items-center gap-2.5 flex-wrap">
            <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
              Panel General de Operaciones
            </h1>
            <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
              Operación Activa
            </span>
          </div>
          <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
            Resumen de rentabilidad, balance de insumos textiles y flujo de confección en tiempo real.
          </p>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <Button
            label="Crear Receta con IA"
            icon="pi pi-sparkles"
            size="small"
            class="p-button-warning text-xs font-semibold"
            @click="showIaModal = true"
          />
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
    </div>

    <!-- 4 Main KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <!-- 1. Rentabilidad Mes -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 sm:p-5 flex flex-col justify-between shadow-md hover:border-amber-500/30 transition">
        <div>
          <div class="flex items-center justify-between text-xs text-stone-400 font-bold uppercase tracking-wider">
            <span>Rentabilidad Mes</span>
            <span class="text-emerald-400 font-semibold text-[11px]">+2.4%</span>
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-stone-100 mt-2 font-mono">
            {{ atelier.rentabilidadPromedio }}%
          </div>
          <!-- Progress bar -->
          <div class="w-full bg-stone-800 h-1.5 rounded-full overflow-hidden mt-3">
            <div class="bg-gradient-to-r from-amber-500 to-emerald-400 h-full rounded-full" :style="{ width: `${atelier.rentabilidadPromedio}%` }" />
          </div>
        </div>
        <div class="text-xs text-stone-400 mt-3 pt-2 border-t border-stone-800/80 flex items-center justify-between">
          <span>Utilidad neta:</span>
          <strong class="text-emerald-400 font-mono font-bold">{{ formatCOP(atelier.totalUtilidad) }}</strong>
        </div>
      </div>

      <!-- 2. Pedidos Activos -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 sm:p-5 flex flex-col justify-between shadow-md hover:border-amber-500/30 transition">
        <div>
          <div class="flex items-center justify-between text-xs text-stone-400 font-bold uppercase tracking-wider">
            <span>Pedidos Activos</span>
            <i class="pi pi-clock text-amber-400" />
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-stone-100 mt-2 font-mono">
            {{ pedidosDisplayActivos }}
          </div>
        </div>
        <div class="text-xs text-stone-400 mt-3 pt-2 border-t border-stone-800/80 flex items-center justify-between">
          <span>En confección:</span>
          <span class="text-amber-300 font-semibold">{{ pedidosDisplayActivos }} prenda(s) en taller</span>
        </div>
      </div>

      <!-- 3. Ventas Totales -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 sm:p-5 flex flex-col justify-between shadow-md hover:border-amber-500/30 transition">
        <div>
          <div class="flex items-center justify-between text-xs text-stone-400 font-bold uppercase tracking-wider">
            <span>Ventas Totales</span>
            <i class="pi pi-chart-line text-emerald-400" />
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-stone-100 mt-2 font-mono">
            {{ formatCOP(atelier.totalVentas) }}
          </div>
        </div>
        <div class="text-xs text-stone-400 mt-3 pt-2 border-t border-stone-800/80 flex items-center justify-between">
          <span>Total órdenes:</span>
          <span class="text-stone-200 font-semibold">{{ pedidosDisplay.length }} pedidos registrados</span>
        </div>
      </div>

      <!-- 4. Insumos Críticos -->
      <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-4 sm:p-5 flex flex-col justify-between shadow-md hover:border-red-500/30 transition">
        <div>
          <div class="flex items-center justify-between text-xs text-stone-400 font-bold uppercase tracking-wider">
            <span>Insumos Críticos</span>
            <i class="pi pi-exclamation-circle text-red-400" />
          </div>
          <div class="text-2xl sm:text-3xl font-extrabold text-red-400 mt-2 font-mono">
            {{ insumosCriticosDisplay.length }}
          </div>
        </div>
        <div class="text-xs text-stone-400 mt-3 pt-2 border-t border-stone-800/80">
          <button
            type="button"
            class="text-amber-400 hover:underline font-semibold flex items-center gap-1"
            @click="router.push('/insumos')"
          >
            <span>Ver inventario de insumos</span>
            <i class="pi pi-arrow-right text-[10px]" />
          </button>
        </div>
      </div>
    </div>

    <!-- Flujo de Producción Personalizada (Kanban Summary Bar) -->
    <div class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg space-y-3">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0 flex items-center gap-2">
          <i class="pi pi-sliders-h" /> Flujo de Producción Personalizada
        </h3>
        <button
          type="button"
          class="text-xs text-amber-400 hover:underline font-semibold flex items-center gap-1"
          @click="router.push('/produccion')"
        >
          <span>Ver Tablero Kanban Completo</span>
          <i class="pi pi-arrow-right text-[10px]" />
        </button>
      </div>

      <!-- 8-Stage Pipeline Strip -->
      <div class="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">1. Cotizado</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ atelier.pipelineCounts.COTIZADO }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">2. Reservado</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ atelier.pipelineCounts.RESERVADO }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">3. Corte</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ atelier.pipelineCounts.CORTE }}</div>
        </div>
        <div class="bg-amber-950/40 border border-amber-500/40 rounded-xl p-2.5 text-center shadow-inner">
          <div class="text-[11px] text-amber-300 font-bold truncate">4. Costura</div>
          <div class="text-base font-bold font-mono text-amber-400 mt-0.5">{{ atelier.pipelineCounts.COSTURA }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">5. Acabados</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ atelier.pipelineCounts.ACABADOS }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">6. Calidad</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ atelier.pipelineCounts.CALIDAD }}</div>
        </div>
        <div class="bg-stone-950/60 border border-stone-800 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-stone-400 font-medium truncate">7. Listo</div>
          <div class="text-base font-bold font-mono text-stone-300 mt-0.5">{{ atelier.pipelineCounts.LISTO }}</div>
        </div>
        <div class="bg-emerald-950/30 border border-emerald-500/30 rounded-xl p-2.5 text-center">
          <div class="text-[11px] text-emerald-300 font-bold truncate">8. Entregado</div>
          <div class="text-base font-bold font-mono text-emerald-400 mt-0.5">{{ atelier.pipelineCounts.ENTREGADO }}</div>
        </div>
      </div>
    </div>

    <!-- Liquidación & Reparto de Utilidades Atelier Arpía (Fórmula de Socias) -->
    <div class="bg-gradient-to-br from-stone-900 via-stone-950 to-amber-950/30 border border-amber-500/30 rounded-2xl p-5 shadow-xl space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-stone-800/80 pb-3">
        <div class="flex items-center gap-2 flex-wrap">
          <h3 class="text-sm font-bold uppercase tracking-wider text-amber-300 m-0 flex items-center gap-2">
            <i class="pi pi-wallet" /> Liquidación & Reparto de Utilidades Atelier Arpía
          </h3>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Fórmula de Socias Activa
          </span>
        </div>
        <div class="text-xs text-stone-300">
          Total Utilidad Taller: <strong class="text-emerald-400 font-mono text-sm">{{ formatCOP(atelier.distribucionSocias.total) }}</strong>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- 40% Fondo Reinversión Taller -->
        <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-4 space-y-2 hover:border-amber-500/30 transition">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-stone-300">Fondo Reinversión Taller</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-stone-800 text-stone-300">40%</span>
          </div>
          <div class="text-xl font-bold font-mono text-amber-400">
            {{ formatCOP(atelier.distribucionSocias.reversion40) }}
          </div>
          <p class="text-[11px] text-stone-400 m-0 leading-tight">
            Destinado a compra de insumos, telas Atenea, agujas y mantenimiento de máquinas Singer.
          </p>
        </div>

        <!-- 30% Ganancia Margara -->
        <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-4 space-y-2 hover:border-amber-500/30 transition">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-stone-300">Ganancia Margara</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-stone-800 text-stone-300">30%</span>
          </div>
          <div class="text-xl font-bold font-mono text-emerald-400">
            {{ formatCOP(atelier.distribucionSocias.margara30) }}
          </div>
          <p class="text-[11px] text-stone-400 m-0 leading-tight">
            Liquidación de utilidades por confección y corte directo de corsetería.
          </p>
        </div>

        <!-- 30% Ganancia Valqui -->
        <div class="bg-stone-950/70 border border-stone-800 rounded-xl p-4 space-y-2 hover:border-amber-500/30 transition">
          <div class="flex justify-between items-center">
            <span class="text-xs font-bold text-stone-300">Ganancia Valqui</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-stone-800 text-stone-300">30%</span>
          </div>
          <div class="text-xl font-bold font-mono text-emerald-400">
            {{ formatCOP(atelier.distribucionSocias.valqui30) }}
          </div>
          <p class="text-[11px] text-stone-400 m-0 leading-tight">
            Liquidación de utilidades por patronaje, diseño y gestión del atelier.
          </p>
        </div>
      </div>
    </div>

    <!-- Bottom Row: Seguimiento de Producción & Rentabilidad Table + Alerts Panel -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Left (2 Cols): Orders Table -->
      <div class="lg:col-span-2 bg-stone-900/80 border border-stone-800 rounded-2xl overflow-hidden shadow-lg flex flex-col justify-between">
        <div>
          <div class="p-4 bg-stone-900 border-b border-stone-800 flex items-center justify-between">
            <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0 flex items-center gap-2">
              <i class="pi pi-list" /> Seguimiento de Producción & Rentabilidad
            </h3>
            <span class="text-xs text-stone-400">{{ pedidosDisplay.length }} órdenes</span>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="border-b border-stone-800 text-stone-400 bg-stone-950/40">
                  <th class="py-2.5 px-3">Código / Cliente</th>
                  <th class="py-2.5 px-3">Prenda Solicitada</th>
                  <th class="py-2.5 px-3 text-center">Estado</th>
                  <th class="py-2.5 px-3 text-right">Venta</th>
                  <th class="py-2.5 px-3 text-right">Utilidad</th>
                  <th class="py-2.5 px-3 text-right">Margen</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-stone-800/50 text-stone-200">
                <tr v-for="p in pedidosDisplay.slice(0, 6)" :key="p.id" class="hover:bg-stone-800/30">
                  <td class="py-2.5 px-3">
                    <div class="font-mono font-bold text-amber-300">{{ p.codigo }}</div>
                    <div class="text-[11px] text-stone-400 truncate max-w-[130px]">{{ p.cliente_nombre }}</div>
                  </td>
                  <td class="py-2.5 px-3 font-medium text-stone-100 max-w-[180px] truncate">
                    {{ p.prenda_nombre }}
                  </td>
                  <td class="py-2.5 px-3 text-center">
                    <span :class="['px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider', getEstadoBadgeClass(p.estado)]">
                      {{ p.estado }}
                    </span>
                  </td>
                  <td class="py-2.5 px-3 text-right font-mono">{{ formatCOP(p.precio_venta) }}</td>
                  <td class="py-2.5 px-3 text-right font-mono font-bold text-emerald-400">{{ formatCOP(p.utilidad_neta) }}</td>
                  <td class="py-2.5 px-3 text-right font-mono text-stone-300">{{ p.margen_pct }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="p-3 bg-stone-950/60 border-t border-stone-800 flex justify-end">
          <button
            type="button"
            class="text-xs text-amber-400 hover:underline font-semibold flex items-center gap-1"
            @click="router.push('/produccion')"
          >
            <span>Ver historial completo de pedidos</span>
            <i class="pi pi-arrow-right text-[10px]" />
          </button>
        </div>
      </div>

      <!-- Right (1 Col): Critical Insumos & Tip Card -->
      <div class="space-y-4">
        <!-- Stock Bajo Crítico -->
        <div class="bg-stone-900/80 border border-red-500/30 rounded-2xl p-4 shadow-lg space-y-3">
          <div class="flex items-center justify-between">
            <h4 class="text-xs font-bold uppercase tracking-wider text-red-400 m-0 flex items-center gap-2">
              <i class="pi pi-exclamation-triangle" /> Stock Bajo Crítico ({{ insumosCriticosDisplay.length }} alertas)
            </h4>
          </div>

          <div v-for="it in insumosCriticosDisplay" :key="it.id" class="bg-stone-950/70 border border-stone-800 rounded-xl p-3 space-y-2">
            <div class="flex justify-between items-start">
              <div>
                <div class="font-bold text-stone-200 text-xs">{{ it.nombre }}</div>
                <div class="text-[11px] text-stone-400">{{ it.proveedor }}</div>
              </div>
              <span class="text-xs font-mono font-bold text-red-400">{{ it.stock_actual }} {{ it.unidad_medida }}</span>
            </div>
            <div class="text-[11px] text-stone-400 flex justify-between">
              <span>Mínimo requerido: {{ it.stock_minimo }} {{ it.unidad_medida }}</span>
              <span class="text-amber-400 font-semibold">Faltante: {{ (it.stock_minimo - it.stock_actual).toFixed(1) }} {{ it.unidad_medida }}</span>
            </div>
            <Button
              label="Generar Orden de Compra"
              icon="pi pi-shopping-cart"
              size="small"
              class="w-full p-button-warning text-xs font-semibold mt-1"
              @click="showSugerirModal = true"
            />
          </div>
        </div>

        <!-- Tip de Rentabilidad Textil -->
        <div class="bg-gradient-to-br from-stone-900 to-amber-950/20 border border-amber-500/30 rounded-2xl p-4 shadow-lg space-y-2.5">
          <div class="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider">
            <i class="pi pi-lightbulb" /> Tip de Rentabilidad Textil
          </div>
          <p class="text-xs text-stone-300 leading-relaxed m-0">
            "Optimizar el corte de tela en trazos al hilo intercalados ahorra hasta un 8% de merma en rollos de 1.50m."
          </p>
          <div class="flex items-center justify-between pt-1">
            <span class="text-[11px] text-stone-400">AtelierPro Advisor</span>
            <button
              type="button"
              class="text-xs text-amber-400 hover:underline font-bold"
              @click="router.push('/optimizador')"
            >
              Abrir Optimizador →
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <AsistenteIaModal v-model:visible="showIaModal" />
    <NuevoPedidoModal v-model:visible="showNuevoPedidoModal" />
    <SugerirOrdenModal v-model:visible="showSugerirModal" />
  </div>
</template>
