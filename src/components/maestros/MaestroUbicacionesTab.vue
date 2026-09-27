<script setup lang="ts">
import { ref } from 'vue'
import type { UbicacionRead } from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'

defineProps<{
  ubicaciones: UbicacionRead[]
}>()

const emit = defineEmits<{
  (e: 'actualizado'): void
  (e: 'solicitar-eliminar', payload: { tipo: string; id: number; nombre: string }): void
}>()

const maestros = useMaestros()

const modalUbicacion = ref(false)
const modoEdicionUbicacion = ref(false)
const ubForm = ref<Partial<UbicacionRead>>({
  codigo: '',
  nombre: '',
  tipo: 'ROLLOS_TELAS',
  capacidad: '',
  observaciones: '',
})

function abrirNuevaUbicacion() {
  modoEdicionUbicacion.value = false
  ubForm.value = {
    codigo: `UB-${Date.now().toString().slice(-4)}`,
    nombre: '',
    tipo: 'ROLLOS_TELAS',
    capacidad: '20 Unidades',
    observaciones: '',
  }
  modalUbicacion.value = true
}

function abrirEditarUbicacion(u: UbicacionRead) {
  modoEdicionUbicacion.value = true
  ubForm.value = { ...u }
  modalUbicacion.value = true
}

async function guardarUbicacion() {
  if (!ubForm.value.nombre) return
  if (modoEdicionUbicacion.value && ubForm.value.id) {
    await maestros.updateUbicacion(ubForm.value.id, ubForm.value as Record<string, unknown>)
  } else {
    await maestros.createUbicacion(ubForm.value as Record<string, unknown>)
  }
  emit('actualizado')
  modalUbicacion.value = false
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
      <div>
        <h2 class="text-lg font-serif font-bold text-stone-100">Ubicaciones Físicas de Almacenamiento</h2>
        <p class="text-xs text-stone-400 font-mono">Gavetas de herrajes, estantes de rollos de tela, percheros de showroom y bodegas auxiliares.</p>
      </div>

      <button
        id="btn-nueva-ubicacion"
        @click="abrirNuevaUbicacion"
        class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
      >
        <span>+</span> Nueva Ubicación
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="ub in ubicaciones"
        :key="ub.id"
        :id="`card-ub-${ub.id}`"
        class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
      >
        <div>
          <div class="flex items-center justify-between">
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-stone-300 font-bold">
              {{ ub.codigo }}
            </span>
            <span class="text-xs font-mono text-amber-400 font-medium">
              Capacidad: {{ ub.capacidad }}
            </span>
          </div>

          <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
            {{ ub.nombre }}
          </h3>
          <p class="text-xs text-stone-400 mt-1">
            {{ ub.observaciones }}
          </p>
        </div>

        <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-between text-xs font-mono">
          <span class="text-stone-500 text-[11px]">{{ (ub.tipo ?? '').replace('_', ' ') }}</span>

          <div class="flex items-center gap-2">
            <button
              :id="`btn-editar-ub-${ub.id}`"
              @click="abrirEditarUbicacion(ub)"
              class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
            >
              Editar
            </button>
            <button
              :id="`btn-eliminar-ub-${ub.id}`"
              @click="emit('solicitar-eliminar', { tipo: 'ubicacion', id: ub.id, nombre: ub.nombre || ub.codigo })"
              class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
              title="Eliminar Ubicación"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL 7: UBICACIÓN TALLER (CRUD) -->
    <div
      v-if="modalUbicacion"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionUbicacion ? 'Editar Ubicación' : 'Nueva Ubicación de Almacenamiento' }}
          </h3>
          <button @click="modalUbicacion = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarUbicacion" class="space-y-4 text-xs font-mono">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Código Ubicación:</label>
              <input
                id="input-ub-cod"
                v-model="ubForm.codigo"
                required
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-amber-300 font-bold focus:border-amber-400 focus:outline-none"
                placeholder="UB-GAV-H3"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1">Tipo:</label>
              <select
                id="input-ub-tipo"
                v-model="ubForm.tipo"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="ROLLOS_TELAS">Rollos de Tela</option>
                <option value="GAVETAS_HERRAJES">Gaveta Herrajes</option>
                <option value="PERCHERO_SHOWROOM">Perchero Showroom</option>
                <option value="ACCESORIOS_BODEGA">Bodega / Merch</option>
              </select>
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Nombre Descriptivo:</label>
            <input
              id="input-ub-nom"
              v-model="ubForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Estante Superior Telas Atenea"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Capacidad Estimada:</label>
            <input
              id="input-ub-cap"
              v-model="ubForm.capacidad"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: 30 Rollos / 50 Prendas"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Observaciones:</label>
            <textarea
              id="input-ub-obs"
              v-model="ubForm.observaciones"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Notas sobre acceso, nivel o llave..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalUbicacion = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Ubicación
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
