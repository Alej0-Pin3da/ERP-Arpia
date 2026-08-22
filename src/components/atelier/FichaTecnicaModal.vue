<script setup lang="ts">
import { ref } from 'vue'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import type { RecetaBOM } from '@/stores/atelier'
import { showToast } from '@/utils/toast'

defineProps<{
  visible: boolean
  receta: RecetaBOM | null
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
}>()

const activeTab = ref<'ficha' | 'matriz'>('ficha')

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function imprimir() {
  window.print()
}

function exportarMatriz() {
  showToast('info', 'Matriz Google Sheet', 'Exportando escandallo y matriz de corte a formato de hoja de cálculo.')
}
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :style="{ width: '92vw', maxWidth: '980px' }"
    :header="receta ? `${receta.nombre} (${receta.codigo})` : 'Ficha Técnica'"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <div v-if="receta" class="space-y-5 pt-1">
      <!-- Subheader with category & view toggle buttons -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-800 pb-3">
        <div class="flex items-center gap-2">
          <Tag severity="warning" class="font-bold tracking-wider text-xs uppercase">{{ receta.linea }}</Tag>
          <span class="text-xs text-stone-400 font-medium">Ficha Técnica Oficial de Taller • Arpía Atelier</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="inline-flex bg-stone-900 rounded-lg p-0.5 border border-stone-800">
            <button
              type="button"
              class="px-3 py-1.5 rounded-md text-xs font-semibold transition"
              :class="activeTab === 'ficha' ? 'bg-amber-500 text-stone-950 shadow' : 'text-stone-400 hover:text-stone-200'"
              @click="activeTab = 'ficha'"
            >
              📋 Ficha Técnica
            </button>
            <button
              type="button"
              class="px-3 py-1.5 rounded-md text-xs font-semibold transition"
              :class="activeTab === 'matriz' ? 'bg-amber-500 text-stone-950 shadow' : 'text-stone-400 hover:text-stone-200'"
              @click="activeTab = 'matriz'"
            >
              📊 Matriz Google Sheet
            </button>
          </div>
          <Button
            label="Imprimir"
            icon="pi pi-print"
            severity="secondary"
            size="small"
            outlined
            @click="imprimir"
          />
        </div>
      </div>

      <!-- TAB 1: FICHA TÉCNICA -->
      <div v-if="activeTab === 'ficha'" class="space-y-5 animate-fade-in">
        <!-- Metadata Overview Strip -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-stone-900/90 border border-stone-800 rounded-xl p-3.5 text-center">
          <div>
            <div class="text-[11px] uppercase font-bold text-stone-400">Código Referencia</div>
            <div class="text-sm font-mono font-bold text-amber-400 mt-0.5">{{ receta.codigo }}</div>
          </div>
          <div>
            <div class="text-[11px] uppercase font-bold text-stone-400">Línea / Categoría</div>
            <div class="text-sm font-semibold text-stone-200 mt-0.5">{{ receta.categoria }}</div>
          </div>
          <div>
            <div class="text-[11px] uppercase font-bold text-stone-400">Tiempo Estimado</div>
            <div class="text-sm font-semibold text-stone-200 mt-0.5">{{ receta.tiempo_confeccion_min }} min</div>
          </div>
          <div>
            <div class="text-[11px] uppercase font-bold text-stone-400">Costo Unitario</div>
            <div class="text-sm font-bold text-emerald-400 mt-0.5">{{ formatCOP(receta.costo_total_unitario) }}</div>
          </div>
        </div>

        <!-- Description -->
        <div class="bg-stone-900/40 border border-stone-800/80 rounded-xl p-3 text-xs text-stone-300 leading-relaxed">
          <strong class="text-amber-300">Descripción del Modelo:</strong> {{ receta.descripcion }}
        </div>

        <!-- BOM Items Table -->
        <div class="border border-stone-800 rounded-xl overflow-hidden bg-stone-900/50">
          <div class="p-3 bg-stone-900/80 border-b border-stone-800 flex items-center justify-between">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0">Lista de Insumos & Escandallo (BOM)</h4>
            <span class="text-xs text-stone-400">{{ receta.items.length }} materiales directos e indirectos</span>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left text-xs border-collapse">
              <thead>
                <tr class="border-b border-stone-800 text-stone-400 bg-stone-950/40">
                  <th class="py-2.5 px-3 font-semibold">Insumo / Material</th>
                  <th class="py-2.5 px-3 font-semibold">Tipo</th>
                  <th class="py-2.5 px-3 font-semibold text-right">Consumo Unit.</th>
                  <th class="py-2.5 px-3 font-semibold text-right">Merma %</th>
                  <th class="py-2.5 px-3 font-semibold text-right">Costo Unit.</th>
                  <th class="py-2.5 px-3 font-semibold text-right">Subtotal</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-stone-800/50 text-stone-200">
                <tr v-for="it in receta.items" :key="it.id" class="hover:bg-stone-800/30">
                  <td class="py-2.5 px-3 font-medium text-stone-100">{{ it.nombre }}</td>
                  <td class="py-2.5 px-3">
                    <span
                      class="px-2 py-0.5 rounded text-[10px] font-bold"
                      :class="it.tipo === 'Directo' ? 'bg-amber-950/60 text-amber-300 border border-amber-500/30' : 'bg-stone-800 text-stone-400'"
                    >
                      {{ it.tipo }}
                    </span>
                  </td>
                  <td class="py-2.5 px-3 text-right font-mono">{{ it.consumo_unitario }} {{ it.unidad }}</td>
                  <td class="py-2.5 px-3 text-right font-mono text-stone-400">{{ it.merma_pct }}%</td>
                  <td class="py-2.5 px-3 text-right font-mono">{{ formatCOP(it.costo_unitario) }}</td>
                  <td class="py-2.5 px-3 text-right font-mono font-bold text-amber-300">{{ formatCOP(it.subtotal) }}</td>
                </tr>
              </tbody>
              <tfoot>
                <tr class="bg-stone-950/70 border-t border-stone-800 font-bold">
                  <td colspan="5" class="py-2.5 px-3 text-stone-300 text-right uppercase text-[11px]">Total Insumos y Materiales:</td>
                  <td class="py-2.5 px-3 text-right font-mono text-amber-400">{{ formatCOP(receta.costo_insumos) }}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        <!-- 2 Columns: Phases vs Costing Breakdown -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Left: Production Phases -->
          <div class="border border-stone-800 rounded-xl p-4 bg-stone-900/50 space-y-3">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0 flex items-center gap-2">
              <i class="pi pi-cog" /> Fases de Producción en Taller
            </h4>
            <div class="space-y-2.5">
              <div
                v-for="(fase, idx) in receta.fases"
                :key="idx"
                class="bg-stone-950/50 border border-stone-800/80 rounded-lg p-2.5 text-xs flex items-start justify-between gap-2"
              >
                <div>
                  <div class="font-bold text-stone-200">{{ fase.nombre }}</div>
                  <div class="text-stone-400 text-[11px] mt-0.5">{{ fase.descripcion }}</div>
                </div>
                <div class="px-2 py-0.5 rounded bg-amber-950/50 text-amber-300 border border-amber-500/20 font-mono text-[11px] font-bold whitespace-nowrap">
                  {{ fase.minutos }} min
                </div>
              </div>
            </div>
          </div>

          <!-- Right: Costing & Pricing Calculation -->
          <div class="border border-stone-800 rounded-xl p-4 bg-stone-900/50 space-y-3">
            <h4 class="text-xs font-bold uppercase tracking-wider text-amber-400 m-0 flex items-center gap-2">
              <i class="pi pi-dollar" /> Costeo & Fijación de Precio Sugerido
            </h4>

            <div class="space-y-2 text-xs divide-y divide-stone-800/60">
              <div class="flex justify-between py-1 text-stone-300">
                <span>(+) Costo Insumos Directos / Indirectos</span>
                <span class="font-mono font-semibold">{{ formatCOP(receta.costo_insumos) }}</span>
              </div>
              <div class="flex justify-between py-1 text-stone-300">
                <span>(+) Mano de Obra ({{ receta.tiempo_confeccion_min }} min)</span>
                <span class="font-mono font-semibold">{{ formatCOP(receta.mano_obra) }}</span>
              </div>
              <div class="flex justify-between py-1 text-stone-300">
                <span>(+) Costos CIF / Energía Eléctrica</span>
                <span class="font-mono font-semibold">{{ formatCOP(receta.cif_energia) }}</span>
              </div>
              <div class="flex justify-between py-1.5 font-bold text-stone-100 bg-stone-950/40 px-2 rounded">
                <span>(=) Costo Unitario de Confección</span>
                <span class="font-mono text-emerald-400">{{ formatCOP(receta.costo_total_unitario) }}</span>
              </div>
              <div class="flex justify-between py-2 items-center">
                <div>
                  <div class="font-bold text-amber-400 text-sm">PRECIO VENTA SUGERIDO</div>
                  <div class="text-[10px] text-stone-400">Margen comercial: {{ receta.markup_pct }}%</div>
                </div>
                <div class="font-mono text-lg font-extrabold text-amber-300">
                  {{ formatCOP(receta.precio_venta) }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Recommendations Banner -->
        <div class="bg-amber-950/20 border border-amber-500/30 rounded-xl p-3 text-xs text-amber-200/90 flex items-start gap-2.5">
          <i class="pi pi-info-circle text-amber-400 text-base flex-shrink-0 mt-0.5" />
          <div>
            <strong class="text-amber-300 block mb-0.5">Recomendaciones del Taller para Confección:</strong>
            {{ receta.recomendaciones_taller }}
          </div>
        </div>
      </div>

      <!-- TAB 2: MATRIZ GOOGLE SHEET -->
      <div v-else class="space-y-4 animate-fade-in">
        <div class="bg-stone-900/80 border border-stone-800 rounded-xl p-3 flex items-center justify-between text-xs">
          <div class="text-stone-300">
            <strong class="text-amber-400">Matriz de Dimensiones & Consumo Textil</strong> • Escandallo tipo planilla de cálculo
          </div>
          <Button
            label="Exportar Planilla"
            icon="pi pi-file-excel"
            size="small"
            severity="warning"
            outlined
            @click="exportarMatriz"
          />
        </div>

        <div class="border border-stone-800 rounded-xl overflow-hidden bg-stone-950/80">
          <table class="w-full text-left text-xs border-collapse font-mono">
            <thead>
              <tr class="bg-stone-900 border-b border-stone-800 text-stone-400 font-sans">
                <th class="py-2.5 px-3">Componente</th>
                <th class="py-2.5 px-3 text-right">Ancho (m)</th>
                <th class="py-2.5 px-3 text-right">Alto (m)</th>
                <th class="py-2.5 px-3 text-right">Cant. Cms</th>
                <th class="py-2.5 px-3 text-right">Valor Metro</th>
                <th class="py-2.5 px-3 text-right text-amber-400">Valor Total</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/50 text-stone-200">
              <tr v-for="it in receta.items" :key="it.id" class="hover:bg-stone-900/40 font-mono">
                <td class="py-2 px-3 font-sans text-stone-100">{{ it.nombre }}</td>
                <td class="py-2 px-3 text-right text-stone-400">{{ (it.ancho || 0.24).toFixed(2) }}</td>
                <td class="py-2 px-3 text-right text-stone-400">{{ (it.alto || 0.85).toFixed(2) }}</td>
                <td class="py-2 px-3 text-right text-stone-300">{{ Math.round((it.consumo_unitario || 1) * 100) }} cm</td>
                <td class="py-2 px-3 text-right">{{ formatCOP(it.costo_unitario) }}</td>
                <td class="py-2 px-3 text-right font-bold text-amber-300">{{ formatCOP(it.subtotal) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Profitability Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="bg-stone-900/90 border border-stone-800 rounded-xl p-3 text-center">
            <div class="text-[11px] uppercase font-bold text-stone-400">Costo Total Confección</div>
            <div class="text-base font-mono font-bold text-stone-200 mt-1">{{ formatCOP(receta.costo_total_unitario) }}</div>
          </div>
          <div class="bg-stone-900/90 border border-amber-500/30 rounded-xl p-3 text-center">
            <div class="text-[11px] uppercase font-bold text-amber-400">Venta Sugerida Atelier</div>
            <div class="text-base font-mono font-bold text-amber-300 mt-1">{{ formatCOP(receta.precio_venta) }}</div>
          </div>
          <div class="bg-stone-900/90 border border-emerald-500/30 rounded-xl p-3 text-center">
            <div class="text-[11px] uppercase font-bold text-emerald-400">Ganancia Neta Estimada</div>
            <div class="text-base font-mono font-bold text-emerald-300 mt-1">
              {{ formatCOP(receta.precio_venta - receta.costo_total_unitario) }} ({{ receta.markup_pct }}%)
            </div>
          </div>
        </div>
      </div>
    </div>
  </Dialog>
</template>
