<script setup lang="ts">
import { ref, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import { useAtelierStore, type RecetaBOM } from '@/stores/atelier'
import FichaTecnicaModal from '@/components/atelier/FichaTecnicaModal.vue'
import NuevaRecetaModal from '@/components/atelier/NuevaRecetaModal.vue'
import AsistenteIaModal from '@/components/atelier/AsistenteIaModal.vue'
import { showToast } from '@/utils/toast'

const atelier = useAtelierStore()

const search = ref('')
const selectedCategory = ref('Todos los Modelos')

const showFichaModal = ref(false)
const showNuevaModal = ref(false)
const showIaModal = ref(false)
const recetaSeleccionada = ref<RecetaBOM | null>(null)

const categorias = [
  'Todos los Modelos',
  'Corsetería',
  'Blusas y Tops',
  'Conjuntos y Sets',
  'Vestidos',
  'Pantalones',
  'Accesorios',
  'Alta Costura',
]

const recetasFiltradas = computed(() => {
  return atelier.recetas.filter((r) => {
    const q = search.value.trim().toLowerCase()
    const matchesSearch =
      !q ||
      r.nombre.toLowerCase().includes(q) ||
      r.codigo.toLowerCase().includes(q) ||
      r.descripcion.toLowerCase().includes(q)

    const matchesCat =
      selectedCategory.value === 'Todos los Modelos' ||
      r.categoria === selectedCategory.value

    return matchesSearch && matchesCat
  })
})

function formatCOP(val: number) {
  return `$${Math.round(val).toLocaleString('es-CO')}`
}

function abrirFicha(r: RecetaBOM) {
  recetaSeleccionada.value = r
  showFichaModal.value = true
}

function eliminarReceta(r: RecetaBOM) {
  const idx = atelier.recetas.findIndex((x) => x.id === r.id)
  if (idx !== -1) {
    atelier.recetas.splice(idx, 1)
    showToast('info', 'Receta eliminada', `${r.nombre} ha sido removida del catálogo.`)
  }
}
</script>

<template>
  <div class="space-y-6">
    <!-- Header Banner -->
    <div class="bg-gradient-to-r from-stone-900 via-stone-900/90 to-stone-950 border border-amber-500/20 rounded-2xl p-5 sm:p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4">
      <div class="space-y-1.5">
        <div class="flex items-center gap-2.5 flex-wrap">
          <h1 class="text-xl sm:text-2xl font-bold font-serif tracking-wide text-stone-100 m-0">
            Recetas de Productos & Fichas Técnicas (BOM)
          </h1>
          <span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-950/80 text-amber-300 border border-amber-500/30 uppercase tracking-wider">
            {{ atelier.recetas.length }} Modelos
          </span>
        </div>
        <p class="text-xs sm:text-sm text-stone-400 m-0 max-w-2xl">
          Escandallo de costeo detallado: consumo de insumos directos/indirectos, tiempos de mano de obra y margen sugerido.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <Button
          label="Planilla Google Sheet (Matriz de Corte)"
          icon="pi pi-file-excel"
          size="small"
          severity="secondary"
          outlined
          class="text-xs font-semibold"
          @click="abrirFicha(atelier.recetas[0])"
        />
        <Button
          label="Generar con IA"
          icon="pi pi-sparkles"
          size="small"
          class="p-button-warning text-xs font-semibold"
          @click="showIaModal = true"
        />
        <Button
          label="Nueva Receta Manual"
          icon="pi pi-plus"
          size="small"
          severity="secondary"
          outlined
          class="text-xs font-semibold"
          @click="showNuevaModal = true"
        />
      </div>
    </div>

    <!-- Search & Category Filters -->
    <div class="space-y-3">
      <!-- Search Input -->
      <div class="w-full md:w-96">
        <span class="p-input-icon-left w-full">
          <InputText
            v-model="search"
            placeholder="Buscar recetas por nombre, código o material..."
            class="w-full text-xs"
          />
        </span>
      </div>

      <!-- Category Filter Pills -->
      <div class="flex flex-wrap gap-1.5 pt-1">
        <button
          v-for="cat in categorias"
          :key="cat"
          type="button"
          class="px-3 py-1.5 rounded-lg text-xs font-semibold border transition"
          :class="selectedCategory === cat ? 'bg-amber-500 text-stone-950 border-amber-500 shadow' : 'bg-stone-900 text-stone-400 border-stone-800 hover:text-stone-200 hover:border-stone-700'"
          @click="selectedCategory = cat"
        >
          {{ cat }}
        </button>
      </div>
    </div>

    <!-- Recipe Cards Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
      <div
        v-for="r in recetasFiltradas"
        :key="r.id"
        class="bg-stone-900/80 border border-stone-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between hover:border-amber-500/40 transition group"
      >
        <!-- Top: Line Badge & Code -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-amber-950/70 text-amber-300 border border-amber-500/30">
              {{ r.linea }}
            </span>
            <span class="font-mono text-xs font-bold text-stone-400">{{ r.codigo }}</span>
          </div>

          <!-- Title & Description -->
          <div>
            <h3 class="text-base font-bold text-stone-100 group-hover:text-amber-300 transition m-0">
              {{ r.nombre }}
            </h3>
            <p class="text-xs text-stone-400 mt-1.5 line-clamp-2 leading-relaxed">
              {{ r.descripcion }}
            </p>
          </div>

          <!-- Metadata Tags -->
          <div class="flex items-center gap-2 pt-1">
            <span class="px-2 py-0.5 rounded bg-stone-950 border border-stone-800 text-[11px] text-stone-300 font-mono">
              🧵 {{ r.items.length }} Insumos BOM
            </span>
            <span class="px-2 py-0.5 rounded bg-stone-950 border border-stone-800 text-[11px] text-stone-300 font-mono">
              ⏱️ {{ r.tiempo_confeccion_min }} min confección
            </span>
          </div>

          <!-- Cost Breakdown Strip -->
          <div class="bg-stone-950/70 border border-stone-800/80 rounded-xl p-3 space-y-1.5 text-xs">
            <div class="flex justify-between text-stone-400">
              <span>Costo Insumos:</span>
              <span class="font-mono text-stone-200">{{ formatCOP(r.costo_insumos) }}</span>
            </div>
            <div class="flex justify-between text-stone-400">
              <span>Mano de Obra ({{ r.tiempo_confeccion_min }}m):</span>
              <span class="font-mono text-stone-200">{{ formatCOP(r.mano_obra) }}</span>
            </div>
            <div class="flex justify-between font-bold text-stone-200 border-t border-stone-800/80 pt-1">
              <span>Costo Total Unitario:</span>
              <span class="font-mono text-emerald-400">{{ formatCOP(r.costo_total_unitario) }}</span>
            </div>
            <div class="flex justify-between items-center bg-stone-900/60 p-1.5 rounded mt-1">
              <span class="text-amber-400 font-bold text-[11px]">PRECIO VENTA ({{ r.markup_pct }}%):</span>
              <span class="font-mono text-sm font-extrabold text-amber-300">{{ formatCOP(r.precio_venta) }}</span>
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div class="flex items-center justify-between pt-4 border-t border-stone-800/80 mt-4">
          <Button
            label="Ver Ficha Técnica >"
            text
            class="text-amber-400 p-0 font-bold text-xs hover:underline"
            @click="abrirFicha(r)"
          />
          <button
            type="button"
            class="text-stone-500 hover:text-red-400 p-1 transition"
            title="Eliminar Receta"
            @click="eliminarReceta(r)"
          >
            <i class="pi pi-trash text-xs" />
          </button>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <FichaTecnicaModal v-model:visible="showFichaModal" :receta="recetaSeleccionada" />
    <NuevaRecetaModal v-model:visible="showNuevaModal" />
    <AsistenteIaModal v-model:visible="showIaModal" />
  </div>
</template>
