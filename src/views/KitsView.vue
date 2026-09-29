<script setup lang="ts">
import { ref, onMounted } from 'vue'
import MaestroKitsTab from '@/components/maestros/MaestroKitsTab.vue'
import ConfirmActionDialog from '@/components/ConfirmActionDialog.vue'
import { listKits, deleteKit, type KitRead } from '@/services/api/kits'
import { showToast } from '@/utils/toast'

const kitsList = ref<KitRead[]>([])

async function cargarKits() {
  try {
    const r = await listKits({ limit: 100 })
    kitsList.value = r.items ?? []
  } catch {
    // keep previous state on error
  }
}

onMounted(() => {
  void cargarKits()
})

const showEliminarDialog = ref(false)
const eliminarTarget = ref<{ tipo: string; id: number; nombre: string } | null>(null)
const eliminarEnCurso = ref(false)

function solicitarEliminar(target: { tipo: string; id: number; nombre: string }) {
  eliminarTarget.value = target
  showEliminarDialog.value = true
}

async function confirmarEliminar() {
  const t = eliminarTarget.value
  if (!t) return
  eliminarEnCurso.value = true
  try {
    await deleteKit(t.id)
    await cargarKits()
    showToast('info', 'Eliminado', `${t.nombre} eliminado del catálogo.`)
  } catch (e: unknown) {
    const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
    showToast('error', 'No se pudo eliminar', typeof detail === 'string' ? detail : 'Es posible que tenga registros asociados.')
  } finally {
    eliminarEnCurso.value = false
    showEliminarDialog.value = false
    eliminarTarget.value = null
  }
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 class="text-xl font-bold text-stone-100">Kits &amp; Cajas</h1>
        <p class="text-xs text-stone-400">Cajas promocionales con costeo en vivo. También disponible en Maestros.</p>
      </div>
      <div class="bg-stone-900 border border-stone-800 rounded-lg px-3 py-1.5 text-xs font-mono text-stone-300">
        Kits: <strong class="text-amber-300">{{ kitsList.length }}</strong>
      </div>
    </div>

    <MaestroKitsTab
      :kits="kitsList"
      @actualizado="cargarKits()"
      @solicitar-eliminar="solicitarEliminar"
    />

    <ConfirmActionDialog
      :visible="showEliminarDialog"
      title="Confirmar Eliminación de Catálogo"
      :message="`¿Estás seguro de que deseás eliminar '${eliminarTarget?.nombre}'? Esta acción no se puede deshacer.`"
      confirm-label="Eliminar Definitivamente"
      :loading="eliminarEnCurso"
      @confirm="confirmarEliminar"
      @cancel="showEliminarDialog = false"
    />
  </div>
</template>
