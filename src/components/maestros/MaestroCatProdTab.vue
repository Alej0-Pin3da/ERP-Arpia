<script setup lang="ts">
import { ref } from 'vue'
import type { CategoriaProductoRead } from '@/services/api/maestros'
import { useMaestros } from '@/composables/useMaestros'
import { showToast } from '@/utils/toast'
import { getApiErrorDetail } from '@/utils/api-error'

const props = defineProps<{
  catProdList: CategoriaProductoRead[]
}>()

const emit = defineEmits<{
  (e: 'actualizado'): void
  (e: 'solicitar-eliminar', payload: { tipo: string; id: number; nombre: string }): void
}>()

const maestros = useMaestros()

const nuevoCatProd = ref<Record<string, string>>({ CATEGORIA: '', LINEA: '' })
const catProdPorTipo = (tipo: string) => props.catProdList.filter((c) => c.tipo === tipo)

async function agregarCatProd(tipo: string) {
  const nombre = (nuevoCatProd.value[tipo] ?? '').trim()
  if (!nombre) {
    showToast('warn', 'Campo requerido', 'Escribí el nombre primero.')
    return
  }
  try {
    await maestros.createCategoriaProducto({ nombre, tipo })
    nuevoCatProd.value[tipo] = ''
    emit('actualizado')
    showToast('success', 'Guardado', `${nombre} agregado a ${tipo === 'CATEGORIA' ? 'Categorías' : 'Líneas'}.`)
  } catch (e: unknown) {
    showToast('error', 'No se pudo guardar', getApiErrorDetail(e, '¿Nombre duplicado?'))
  }
}

async function toggleCatProdActivo(item: CategoriaProductoRead) {
  try {
    await maestros.updateCategoriaProducto(item.id, { activo: !item.activo })
    emit('actualizado')
  } catch {
    showToast('error', 'Error', 'No se pudo cambiar el estado.')
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-stone-900/50 p-4 rounded-xl border border-stone-800">
      <div>
        <h2 class="text-lg font-serif font-bold text-stone-100">Categorías de Producto</h2>
        <p class="text-xs text-stone-400 font-mono">Opciones del select de la Ficha BOM. Desactivar oculta sin borrar historia.</p>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="grupo in [{ tipo: 'CATEGORIA', titulo: 'Categorías' }]" :key="grupo.tipo" class="bg-stone-900/60 border border-stone-800 rounded-xl p-4">
        <h3 class="text-sm font-bold text-stone-100 mb-3">{{ grupo.titulo }}</h3>
        <div class="space-y-2">
          <div v-for="item in catProdPorTipo(grupo.tipo)" :key="item.id" class="flex items-center justify-between gap-2 bg-stone-950/60 border border-stone-800 rounded-lg px-3 py-2">
            <span class="text-sm text-stone-200" :class="{ 'line-through text-stone-500': !item.activo }">{{ item.nombre }}</span>
            <div class="flex items-center gap-2">
              <button
                :id="`btn-toggle-catprod-${item.id}`"
                @click="toggleCatProdActivo(item)"
                class="text-[11px] font-mono px-2 py-0.5 rounded border transition-colors"
                :class="item.activo ? 'text-emerald-300 border-emerald-700/60 bg-emerald-950/40' : 'text-stone-500 border-stone-700'"
                :title="item.activo ? 'Ocultar de la Ficha' : 'Mostrar en la Ficha'"
              >
                {{ item.activo ? 'Activa' : 'Oculta' }}
              </button>
              <button
                :id="`btn-eliminar-catprod-${item.id}`"
                @click="emit('solicitar-eliminar', { tipo: 'catprod', id: item.id, nombre: item.nombre })"
                class="text-xs text-stone-500 hover:text-rose-400 font-mono p-1 transition-colors"
                :title="`Eliminar ${item.nombre}`"
              >
                ✕
              </button>
            </div>
          </div>
          <div v-if="!catProdPorTipo(grupo.tipo).length" class="text-xs text-stone-500 text-center py-2">Sin valores.</div>
        </div>
        <div class="flex items-center gap-2 mt-3">
          <input
            :id="`input-nuevo-catprod-${grupo.tipo}`"
            v-model="nuevoCatProd[grupo.tipo]"
            :placeholder="`Nueva ${grupo.titulo.toLowerCase().slice(0, -1)}…`"
            class="flex-1 bg-stone-950 border border-stone-700 rounded-lg px-3 py-2 text-sm text-stone-200 placeholder:text-stone-600 focus:border-amber-400 focus:outline-none"
            @keyup.enter="agregarCatProd(grupo.tipo)"
          />
          <button
            :id="`btn-agregar-catprod-${grupo.tipo}`"
            @click="agregarCatProd(grupo.tipo)"
            class="bg-amber-400 hover:bg-amber-300 text-stone-950 font-mono text-xs font-semibold px-3.5 py-2 rounded-lg transition-colors whitespace-nowrap"
          >
            + Agregar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
