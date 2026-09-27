<script setup lang="ts">
import { ref } from 'vue'
import InputNumber from 'primevue/inputnumber'
import type { TallaRead, ProductoSinTallaRead } from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'

const props = defineProps<{
  tallas: TallaRead[]
  sinTalla: ProductoSinTallaRead[]
}>()

const emit = defineEmits<{
  (e: 'actualizado'): void
  (e: 'solicitar-eliminar', payload: { tipo: string; id: number; nombre: string }): void
}>()

const maestros = useMaestros()

// --- TALLAS ESTÁNDAR ---
const modalTalla = ref(false)
const modoEdicionTalla = ref(false)
const tallaForm = ref<Partial<TallaRead>>({
  talla: '',
  busto: '',
  cintura: '',
  cadera: '',
  reduccion_corset: '',
  descripcion: '',
  orden: 1,
  activo: true,
})

function abrirNuevaTalla() {
  modoEdicionTalla.value = false
  tallaForm.value = {
    talla: '',
    busto: '80 – 85 cm',
    cintura: '60 – 65 cm',
    cadera: '85 – 90 cm',
    reduccion_corset: '-5 cm a -7 cm',
    descripcion: 'Nueva talla estándar de confección',
    orden: props.tallas.length + 1,
    activo: true,
  }
  modalTalla.value = true
}

function abrirEditarTalla(t: TallaRead) {
  modoEdicionTalla.value = true
  tallaForm.value = { ...t }
  modalTalla.value = true
}

async function guardarTalla() {
  if (!tallaForm.value.talla) return
  if (modoEdicionTalla.value && tallaForm.value.id) {
    await maestros.updateTalla(tallaForm.value.id, tallaForm.value as Record<string, unknown>)
  } else {
    await maestros.createTalla(tallaForm.value as Record<string, unknown>)
  }
  emit('actualizado')
  modalTalla.value = false
}

// --- PRODUCTOS SIN TALLA ---
const modalSinTalla = ref(false)
const modoEdicionSinTalla = ref(false)
const sinTallaForm = ref<Partial<ProductoSinTallaRead>>({
  nombre: '',
  categoria: 'Tote Bags & Bolsos',
  dimensiones: '',
  materiales: '',
  descripcion: '',
  precio_sugerido: 45000,
  activo: true,
})

function abrirNuevoSinTalla() {
  modoEdicionSinTalla.value = false
  sinTallaForm.value = {
    nombre: '',
    categoria: 'Tote Bags & Bolsos',
    dimensiones: '',
    materiales: '',
    descripcion: '',
    precio_sugerido: 40000,
    activo: true,
  }
  modalSinTalla.value = true
}

function abrirEditarSinTalla(p: ProductoSinTallaRead) {
  modoEdicionSinTalla.value = true
  sinTallaForm.value = { ...p }
  modalSinTalla.value = true
}

async function guardarSinTalla() {
  if (!sinTallaForm.value.nombre) return
  if (modoEdicionSinTalla.value && sinTallaForm.value.id) {
    await maestros.updateProductoSinTalla(sinTallaForm.value.id, sinTallaForm.value as Record<string, unknown>)
  } else {
    await maestros.createProductoSinTalla(sinTallaForm.value as Record<string, unknown>)
  }
  emit('actualizado')
  modalSinTalla.value = false
}

function formatoCOP(val: number | string | undefined | null) {
  const n = Number(val || 0)
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(n)
}
</script>

<template>
  <div class="space-y-8">
    <!-- Section 4.1: Standard Sizes Table (CRUD) -->
    <div class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
        <div>
          <h2 class="text-lg font-serif font-bold text-stone-100">Matriz Oficial de Tallas Estándar</h2>
          <p class="text-xs text-stone-400 font-mono mt-0.5">
            Definición y escalado de medidas anatómicas estándar para la corsetería y prendas de Arpía.
          </p>
        </div>

        <button
          id="btn-nueva-talla"
          @click="abrirNuevaTalla"
          class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
        >
          <span>+</span> Nueva Talla Estándar
        </button>
      </div>

      <div class="bg-stone-900/40 border border-stone-800 rounded-xl overflow-hidden shadow-lg">
        <div class="hidden overflow-x-auto md:block">
          <table class="w-full min-w-[760px] text-left text-xs font-mono">
            <thead class="bg-stone-950/80 text-stone-400 uppercase tracking-wider border-b border-stone-800">
              <tr>
                <th class="py-3 px-4 sticky left-0 z-10 bg-stone-950/95">Talla</th>
                <th class="py-3 px-4 text-center whitespace-nowrap">Pecho</th>
                <th class="py-3 px-4 text-center whitespace-nowrap">Cintura</th>
                <th class="py-3 px-4 text-right whitespace-nowrap">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-stone-800/60 text-stone-200">
              <tr
                v-for="t in tallas"
                :key="t.id"
                class="hover:bg-stone-800/30 transition-colors"
              >
                <td class="py-3.5 px-4 font-bold text-amber-400 flex items-center gap-2 sticky left-0 z-10 bg-stone-900/95">
                  <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
                  <span>{{ t.talla }}</span>
                </td>
                <td class="py-3.5 px-4 whitespace-nowrap text-center">{{ t.busto }}</td>
                <td class="py-3.5 px-4 whitespace-nowrap text-center">{{ t.cintura }}</td>
                <td class="py-3.5 px-4 text-right whitespace-nowrap">
                  <div class="flex items-center justify-end gap-2">
                    <button
                      :id="`btn-editar-talla-${t.id}`"
                      @click="abrirEditarTalla(t)"
                      class="text-[11px] text-stone-300 hover:text-amber-300 font-mono px-2 py-1 bg-stone-800 hover:bg-stone-700 rounded border border-stone-700/70"
                    >
                      Editar
                    </button>
                    <button
                      :id="`btn-eliminar-talla-${t.id}`"
                      @click="emit('solicitar-eliminar', { tipo: 'talla', id: t.id, nombre: `Talla ${t.talla}` })"
                      class="text-[11px] text-stone-500 hover:text-rose-400 p-1"
                      title="Eliminar Talla"
                    >
                      ✕
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <!-- Mobile cards: same tallas. No horizontal scroll. -->
        <div class="space-y-3 p-4 md:hidden max-w-full min-w-0">
          <div v-for="t in tallas" :key="t.id" class="bg-stone-950/70 border border-stone-800 rounded-2xl p-4 space-y-2 min-w-0">
            <div class="flex items-center gap-2">
              <span class="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
              <div class="font-bold text-sm text-amber-400">Talla {{ t.talla }}</div>
            </div>
            <div class="grid grid-cols-2 gap-2 text-sm">
              <div><div class="text-xs uppercase tracking-wider text-stone-400">Pecho</div><div class="font-mono text-stone-100">{{ t.busto }}</div></div>
              <div><div class="text-xs uppercase tracking-wider text-stone-400">Cintura</div><div class="font-mono text-stone-100">{{ t.cintura }}</div></div>
            </div>
            <div class="flex gap-2 pt-1">
              <button type="button" class="flex-1 min-h-[40px] rounded-lg bg-stone-800 text-stone-200 text-sm font-semibold" @click="abrirEditarTalla(t)">Editar</button>
              <button type="button" class="min-w-[44px] min-h-[40px] px-3 rounded-lg border border-stone-700 text-stone-500" title="Eliminar Talla" @click="emit('solicitar-eliminar', { tipo: 'talla', id: t.id, nombre: `Talla ${t.talla}` })">✕</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Section 4.2: Products Without Size / Merch (CRUD) -->
    <div class="space-y-4">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
        <div>
          <h2 class="text-lg font-serif font-bold text-stone-100 flex items-center gap-2">
            <span>👜</span> Catálogo de Formatos Sin Talla (Tote Bags & Merch)
          </h2>
          <p class="text-xs text-stone-400 font-mono mt-0.5">
            Especificaciones de producción, dimensiones y precio base para productos sin requerimiento de calce corporal.
          </p>
        </div>

        <button
          id="btn-nuevo-sintalla"
          @click="abrirNuevoSinTalla"
          class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors flex items-center gap-1.5 shadow-sm whitespace-nowrap self-start sm:self-auto"
        >
          <span>+</span> Nuevo Producto Sin Talla
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="p in sinTalla"
          :key="p.id"
          :id="`card-sintalla-${p.id}`"
          class="bg-stone-900/60 border border-stone-800 rounded-xl p-4 flex flex-col justify-between hover:border-stone-700 transition-all"
        >
          <div>
            <div class="flex items-center justify-between">
              <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/70 text-amber-300 border border-amber-800/80 font-bold">
                {{ p.categoria }}
              </span>
              <span class="text-xs font-mono text-emerald-400 font-bold">
                PVP Sugerido: {{ formatoCOP(p.precio_sugerido) }}
              </span>
            </div>

            <h3 class="text-base font-serif font-bold text-stone-100 mt-2.5">
              {{ p.nombre }}
            </h3>
            <p class="text-xs text-stone-400 mt-1">
              {{ p.descripcion }}
            </p>

            <div class="mt-3 bg-stone-950/70 p-3 rounded-lg border border-stone-800 space-y-1.5 text-xs font-mono">
              <div class="flex flex-col sm:flex-row sm:justify-between text-stone-300 gap-0.5">
                <span class="text-stone-500">Dimensiones:</span>
                <span class="font-medium text-stone-200 text-right">{{ p.dimensiones }}</span>
              </div>
              <div class="flex flex-col sm:flex-row sm:justify-between text-stone-300 gap-0.5 pt-1 border-t border-stone-800/80">
                <span class="text-stone-500">Materiales:</span>
                <span class="font-medium text-stone-200 text-right">{{ p.materiales }}</span>
              </div>
            </div>
          </div>

          <div class="mt-4 pt-3 border-t border-stone-800 flex items-center justify-end gap-2">
            <button
              :id="`btn-editar-sintalla-${p.id}`"
              @click="abrirEditarSinTalla(p)"
              class="text-xs text-stone-400 hover:text-amber-300 font-mono px-2.5 py-1 bg-stone-800/70 hover:bg-stone-800 rounded border border-stone-700/60 transition-colors"
            >
              Editar
            </button>
            <button
              :id="`btn-eliminar-sintalla-${p.id}`"
              @click="emit('solicitar-eliminar', { tipo: 'sintalla', id: p.id, nombre: p.nombre })"
              class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
              title="Eliminar Producto Sin Talla"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL 4: TALLA ESTÁNDAR (CRUD) -->
    <div
      v-if="modalTalla"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionTalla ? 'Editar Talla Estándar' : 'Nueva Talla Estándar de Confección' }}
          </h3>
          <button @click="modalTalla = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarTalla" class="space-y-4 text-xs font-mono">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Nombre / Código Talla:</label>
              <input
                id="input-talla-nombre"
                v-model="tallaForm.talla"
                required
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-amber-300 font-bold focus:border-amber-400 focus:outline-none"
                placeholder="Ej: XXS, 38, 42"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1 text-[11px]">Orden:</label>
              <input
                id="input-talla-orden"
                v-model.number="tallaForm.orden"
                type="number"
                min="1"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-2 py-1.5 text-stone-100 focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div>
              <label class="block text-stone-300 mb-1 text-[11px]">Pecho:</label>
              <input
                id="input-talla-busto"
                v-model="tallaForm.busto"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-2 py-1.5 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="78 cm"
              />
            </div>
            <div>
              <label class="block text-stone-300 mb-1 text-[11px]">Cintura:</label>
              <input
                id="input-talla-cintura"
                v-model="tallaForm.cintura"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-2 py-1.5 text-stone-100 focus:border-amber-400 focus:outline-none"
                placeholder="60 cm"
              />
            </div>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalTalla = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Talla
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL 5: PRODUCTO SIN TALLA (CRUD) -->
    <div
      v-if="modalSinTalla"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
    >
      <div class="bg-stone-900 border border-stone-700 rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl">
        <div class="flex items-center justify-between border-b border-stone-800 pb-3">
          <h3 class="text-base font-serif font-bold text-amber-300">
            {{ modoEdicionSinTalla ? 'Editar Producto Sin Talla' : 'Nuevo Producto / Formato Sin Talla' }}
          </h3>
          <button @click="modalSinTalla = false" class="text-stone-400 hover:text-stone-200 text-lg">✕</button>
        </div>

        <form @submit.prevent="guardarSinTalla" class="space-y-4 text-xs font-mono">
          <div>
            <label class="block text-stone-300 mb-1">Nombre del Formato / Producto:</label>
            <input
              id="input-sintalla-nombre"
              v-model="sinTallaForm.nombre"
              required
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Tote Bag Ilustrada Mini"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-stone-300 mb-1">Categoría:</label>
              <select
                id="input-sintalla-cat"
                v-model="sinTallaForm.categoria"
                class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              >
                <option value="Tote Bags & Bolsos">Tote Bags & Bolsos</option>
                <option value="Accesorios Textiles">Accesorios Textiles</option>
                <option value="Pines & Joyería">Pines & Joyería</option>
                <option value="Merchandising">Merchandising</option>
              </select>
            </div>
            <div>
              <label class="block text-stone-300 mb-1">PVP Sugerido (COP):</label>
              <InputNumber
                v-model="sinTallaForm.precio_sugerido"
                inputId="input-sintalla-precio"
                mode="decimal"
                locale="es-CO"
                :min="0"
                :step="1000"
                :min-fraction-digits="0"
                :max-fraction-digits="2"
                suffix=" COP"
                class="w-full"
                inputClass="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-emerald-400 font-bold focus:border-amber-400 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Dimensiones / Medidas Técnicas:</label>
            <input
              id="input-sintalla-dim"
              v-model="sinTallaForm.dimensiones"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: 40 cm alto × 35 cm ancho × 8 cm fuelle"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Materiales & Confección:</label>
            <input
              id="input-sintalla-mat"
              v-model="sinTallaForm.materiales"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Ej: Lona cruda 100% algodón 320g"
            />
          </div>

          <div>
            <label class="block text-stone-300 mb-1">Descripción / Uso:</label>
            <textarea
              id="input-sintalla-desc"
              v-model="sinTallaForm.descripcion"
              rows="2"
              class="w-full bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-stone-100 focus:border-amber-400 focus:outline-none"
              placeholder="Descripción del formato y canal de preferencia..."
            ></textarea>
          </div>

          <div class="flex items-center justify-end gap-3 pt-3 border-t border-stone-800">
            <button
              type="button"
              @click="modalSinTalla = false"
              class="px-4 py-2 bg-stone-800 text-stone-300 hover:bg-stone-700 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 bg-amber-400 text-stone-950 font-bold hover:bg-amber-300 rounded-lg shadow"
            >
              Guardar Formato
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
