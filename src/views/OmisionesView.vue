<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMode } from '@/composables/useMode'
import { useOmisiones, type MockOmision } from '@/composables/useOmisiones'

const { isMock } = useMode()
const omisionesApi = useOmisiones()
const omisiones = ref<MockOmision[]>([
  {
    id: 1,
    fecha: '2026-08-20 14:30',
    usuario: 'Camila Modista',
    evento: 'Descuento manual de merma en encaje Chantilly por falla de estiramiento',
    impacto: '-0.35m Tela',
  },
  {
    id: 2,
    fecha: '2026-08-18 10:15',
    usuario: 'Valeria Arpía',
    evento: 'Ajuste de precio de cotización especial para clienta VIP',
    impacto: 'Descuento $40.000 COP',
  },
])

const omisionesReal = ref<any[]>([])
async function cargarOmisionesReales() {
  if (isMock.value) return
  try {
    const r = await omisionesApi.list({ limit: 100 })
    omisionesReal.value = (r as any).items ?? []
  } catch { omisionesReal.value = [] }
}
onMounted(() => { void cargarOmisionesReales() })
watch(isMock, () => { void cargarOmisionesReales() })
const omisionesDisplay = computed(() => isMock.value ? omisiones.value : (omisionesReal.value.length ? omisionesReal.value.map((o: any) => ({
  id: o.id,
  fecha: o.creado_en || '',
  usuario: o.hoja || 'Sistema',
  evento: o.mensaje || o.fase || 'Omisión',
  impacto: o.nivel || '',
})) : []))
</script>

<template>
  <div class="space-y-6">
    <div class="border-b border-stone-800 pb-4">
      <h1 class="text-2xl font-serif font-bold text-amber-300 tracking-wide">
        Bitácora de Omisiones & Ajustes Especiales
      </h1>
      <p class="text-xs text-stone-400 mt-1 font-mono">
        Registro auditable de modificaciones de merma, excepciones en precios y cambios de patrón.
      </p>
    </div>

    <div class="rounded-2xl border border-stone-800 bg-stone-900/40 p-6 space-y-4">
      <table class="w-full text-xs text-left border-collapse">
        <thead>
          <tr class="border-b border-stone-800 text-stone-400 font-mono">
            <th class="py-2.5 px-3">Fecha</th>
            <th class="py-2.5 px-3">Responsable</th>
            <th class="py-2.5 px-3">Detalle del Evento</th>
            <th class="py-2.5 px-3 text-right">Impacto</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-stone-800/60 font-mono">
          <tr v-if="!omisionesDisplay.length">
                <td colspan="4" class="py-8 text-center text-stone-500">
                  <i class="pi pi-inbox text-2xl mb-2 block" />
                  Sin omisiones registradas en modo {{ isMock ? 'MOCK' : 'REAL' }}.
                  <span v-if="!isMock" class="block text-[11px] mt-1">Los datos vienen de <code>GET /api/v1/omisiones</code>.</span>
                </td>
              </tr>
          <tr v-for="o in omisionesDisplay" :key="o.id">
            <td class="py-3 px-3 text-stone-400">{{ o.fecha }}</td>
            <td class="py-3 px-3 text-amber-300 font-bold">{{ o.usuario }}</td>
            <td class="py-3 px-3 text-stone-300">{{ o.evento }}</td>
            <td class="py-3 px-3 text-right text-stone-400 font-semibold">{{ o.impacto }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
