<script setup lang="ts">
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'

withDefaults(
  defineProps<{
    visible: boolean
    titulo: string
    mensaje: string
    detalle?: string | null
    loading?: boolean
    confirmarLabel?: string
  }>(),
  { detalle: null, loading: false, confirmarLabel: 'Eliminar' },
)

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'confirmar'): void
}>()
</script>

<template>
  <Dialog
    :visible="visible"
    modal
    :header="titulo"
    :style="{ width: '90vw', maxWidth: '420px' }"
    @update:visible="(v) => emit('update:visible', v)"
  >
    <p class="text-xs text-stone-300 pt-2">
      {{ mensaje }}
      <strong v-if="detalle" class="text-amber-300">{{ detalle }}</strong>
    </p>
    <template #footer>
      <div class="flex items-center justify-end gap-2 pt-3 border-t border-stone-800">
        <Button
          label="Cancelar"
          icon="pi pi-times"
          size="small"
          class="p-button-text p-button-secondary text-xs"
          :disabled="loading"
          @click="emit('update:visible', false)"
        />
        <Button
          :label="confirmarLabel"
          icon="pi pi-trash"
          size="small"
          severity="danger"
          class="text-xs font-semibold"
          :loading="loading"
          @click="emit('confirmar')"
        />
      </div>
    </template>
  </Dialog>
</template>
