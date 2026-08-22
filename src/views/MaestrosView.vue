<script setup lang="ts">
import { ref } from 'vue'

const categorias = ref([
  { id: 1, tipo: 'Categoría Insumo', nombre: 'Telas & Sedas', desc: 'Satín, encaje chantilly, tules bordados, mallas illusion' },
  { id: 2, tipo: 'Categoría Insumo', nombre: 'Estructura & Corsetería', desc: 'Varillas de acero espiralado, regilene, busks frontales' },
  { id: 3, tipo: 'Categoría Insumo', nombre: 'Herrajes & Metales', desc: 'Ojaletes inoxidables, argollas doradas, ganchos de corsé' },
  { id: 4, tipo: 'Categoría Prenda', nombre: 'Corsets Overbust & Underbust', desc: 'Prendas de alta reducción y soporte' },
  { id: 5, tipo: 'Categoría Prenda', nombre: 'Lencería de Autor', desc: 'Bralettes, bodysuits y ligueros en seda' },
])
</script>

<template>
  <div class="space-y-6">
    <div class="border-b border-stone-800 pb-4">
      <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
        Catálogos Maestros de Atelier
      </h1>
      <p class="text-xs text-stone-400 mt-1 font-mono">
        Configuración de familias de materiales, tipos de corte y clasificaciones de alta costura.
      </p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div v-for="c in categorias" :key="c.id" class="rounded-xl border border-stone-800 bg-stone-900/40 p-4">
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-800 text-amber-300">{{ c.tipo }}</span>
        </div>
        <div class="font-serif font-bold text-stone-100 text-base mt-2">{{ c.nombre }}</div>
        <div class="text-xs text-stone-400 mt-1">{{ c.desc }}</div>
      </div>
    </div>
  </div>
</template>
