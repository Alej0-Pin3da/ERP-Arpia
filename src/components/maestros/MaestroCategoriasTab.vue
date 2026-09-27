<script setup lang="ts">
import { ref } from 'vue'
import InputNumber from 'primevue/inputnumber'
import type { CategoriaRead } from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'

defineProps<{
  categorias: CategoriaRead[]
}>()

const emit = defineEmits<{
  (e: 'actualizado'): void
  (e: 'solicitar-eliminar', payload: { tipo: string; id: number; nombre: string }): void
}>()

const maestros = useMaestros()

const modalCategoria = ref(false)
const modoEdicionCategoria = ref(false)
const catForm = ref<Partial<CategoriaRead>>({
  nombre: '',
  tipo_talla: 'CON_TALLAS_ESTANDAR',
  descripcion: '',
  margen_meta_pct: 65,
  total_modelos: 0,
  activo: true,
})

function abrirNuevaCategoria() {
  modoEdicionCategoria.value = false
  catForm.value = {
    nombre: '',
    tipo_talla: 'CON_TALLAS_ESTANDAR',
    descripcion: '',
    margen_meta_pct: 65,
    total_modelos: 0,
    activo: true,
  }
  modalCategoria.value = true
}

function abrirEditarCategoria(c: CategoriaRead) {
  modoEdicionCategoria.value = true
  catForm.value = { ...c }
  modalCategoria.value = true
}

async function guardarCategoria() {
  if (!catForm.value.nombre) return
  if (modoEdicionCategoria.value && catForm.value.id) {
    await maestros.updateCategoria(catForm.value.id, catForm.value as Record<string, unknown>)
  } else {
    await maestros.createCategoria(catForm.value as Record<string, unknown>)
  }
  emit('actualizado')
  modalCategoria.value = false
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
      <div>
        <h2 class="text-lg font-serif font-bold text-stone-100">Familias & Categorías de Colección</h2>
        <p class="text-xs text-stone-400 font-mono">Líneas de producto, márgenes objetivo de rentabilidad y segmentación por tipo de talla.</p>
      </div>

      <button
        id="btn-nueva-categoria"
        @click="abrirNuevaCategoria"
        class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
      >
        <span>+</span> Nueva Familia de Colección
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="cat in categorias"
        :key="cat.id"
        :id="`card-cat-${cat.id}`"
        class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
      >
        <div>
          <div class="flex items-center justify-between">
            <span
              class="text-[10px] font-mono px-2 py-0.5 rounded font-bold"
              :class="cat.tipo_talla === 'CON_TALLAS_ESTANDAR'
                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                : 'bg-indigo-950 text-indigo-300 border border-indigo-800'"
            >
              {{ cat.tipo_talla === 'CON_TALLAS_ESTANDAR' ? 'Tallas XXS-XL' : 'Sin Talla / Merch' }}
            </span>

            <span class="text-xs font-mono text-emerald-400 font-bold">
              Margen Meta: {{ cat.margen_meta_pct }}%
            </span>
          </div>

          <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
            {{ cat.nombre }}
          </h3>
          <p class="text-xs text-stone-400 mt-1">
            {{ cat.descripcion }}
          </p>
        </div>

        <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-between text-xs font-mono">
          <span class="text-stone-500">Modelos en Ficha BOM: <strong class="text-stone-300">{{ cat.total_modelos }}</strong></span>

          <div class="flex items-center gap-2">
            <button
              :id="`btn-editar-cat-${cat.id}`"
              @click="abrirEditarCategoria(cat)"
              class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
            >
              Editar
            </button>
            <button
              :id="`btn-eliminar-cat-${cat.id}`"
              @click="emit('solicitar-eliminar', { tipo: 'categoria', id: cat.id, nombre: cat.nombre })"
              class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
              title="Eliminar Categoría"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL 6: FAMILIA / CATEGORÍA COLECCIÓN -->
    <div
      v-if="modalCategoria"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionCategoria ? 'Editar Familia de Colección' : 'Nueva Familia de Colección' }}
          </h3>
          <button @click="modalCategoria = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarCategoria" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre de la Familia:</label>
            <input
              id="input-cat-nombre"
              v-model="catForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Corsetería Overbust de Gala"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Tipo de Talla:</label>
              <select
                id="input-cat-tipo-talla"
                v-model="catForm.tipo_talla"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="CON_TALLAS_ESTANDAR">Con Tallas (XXS-XL)</option>
                <option value="SIN_TALLA_MERCH">Sin Talla / Merch</option>
                <option value="TALLA_UNICA">Talla Única</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Margen Meta (%):</label>
              <InputNumber
                v-model="catForm.margen_meta_pct"
                inputId="input-cat-margen"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :max="100"
                :step="0.5"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" %"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-emerald-400 font-bold focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Descripción:</label>
            <textarea
              id="input-cat-desc"
              v-model="catForm.descripcion"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Detalles sobre patrones, insumos clave y características..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalCategoria = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Familia
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
