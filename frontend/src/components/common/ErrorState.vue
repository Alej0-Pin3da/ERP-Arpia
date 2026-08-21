<script setup lang="ts">
/**
 * ErrorState — unified error placeholder (UX slice 1, TASK-037).
 *
 * Replaces ad-hoc <Message severity="error"> per view. Uses PrimeVue Message
 * + Button with --arpia-* semantic tokens. Emits `retry` when CTA clicked.
 */
import Button from 'primevue/button'
import Message from 'primevue/message'

defineProps<{
  message: string
}>()

defineEmits<{
  retry: []
}>()
</script>

<template>
  <div class="error-state" data-test="error-state">
    <Message severity="error" :closable="false" icon="pi pi-times-circle" data-test="error-message">
      {{ message }}
    </Message>
    <Button label="Reintentar" icon="pi pi-refresh" data-test="error-retry" @click="$emit('retry')" />
  </div>
</template>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem 0;
  align-items: flex-start;
}

.error-state :deep(.p-message) {
  width: 100%;
}
</style>
