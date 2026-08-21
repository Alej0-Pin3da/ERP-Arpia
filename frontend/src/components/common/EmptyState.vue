<script setup lang="ts">
/**
 * EmptyState — unified empty placeholder (UX slice 1, TASK-037).
 *
 * Replaces ad-hoc `#empty` slots in each view. Uses PrimeVue Button and
 * --arpia-* tokens for consistent styling. The CTA is optional; when
 * `actionLabel` is present the component emits `action`.
 */
import Button from 'primevue/button'

withDefaults(
  defineProps<{
    icon?: string
    title: string
    description?: string
    actionLabel?: string
  }>(),
  {
    icon: 'pi pi-inbox',
    description: undefined,
    actionLabel: undefined,
  },
)

defineEmits<{
  action: []
}>()
</script>

<template>
  <div class="empty-state" data-test="empty-state">
    <i v-if="icon" :class="icon" class="empty-state-icon" data-test="empty-icon" aria-hidden="true" />
    <h3 class="empty-state-title" data-test="empty-title">{{ title }}</h3>
    <p v-if="description" class="empty-state-description" data-test="empty-description">
      {{ description }}
    </p>
    <Button
      v-if="actionLabel"
      :label="actionLabel"
      data-test="empty-action"
      @click="$emit('action')"
    />
  </div>
</template>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1.5rem;
  text-align: center;
  gap: 0.75rem;
}

.empty-state-icon {
  font-size: 2.5rem;
  color: var(--arpia-text-faint);
}

.empty-state-title {
  margin: 0;
  font-family: var(--arpia-font-heading);
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--arpia-text-primary);
}

.empty-state-description {
  margin: 0;
  max-width: 28rem;
  font-family: var(--arpia-font-body);
  color: var(--arpia-text-muted);
  font-size: 0.95rem;
  line-height: 1.5;
}
</style>
