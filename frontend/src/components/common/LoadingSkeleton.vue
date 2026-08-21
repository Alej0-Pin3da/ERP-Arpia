<script setup lang="ts">
/**
 * LoadingSkeleton — table skeleton placeholder (UX slice 1, TASK-037).
 *
 * Replaces ad-hoc loading spinners. Renders `rows * columns` PrimeVue
 * Skeleton cells with --arpia-* surface tokens.
 */
import Skeleton from 'primevue/skeleton'

withDefaults(
  defineProps<{
    rows?: number
    columns?: number
  }>(),
  {
    rows: 5,
    columns: 4,
  },
)
</script>

<template>
  <div class="loading-skeleton" data-test="loading-skeleton">
    <div
      v-for="r in rows"
      :key="r"
      class="loading-skeleton-row"
      data-test="skeleton-row"
    >
      <Skeleton
        v-for="c in columns"
        :key="c"
        height="1.25rem"
        class="loading-skeleton-cell"
        data-test="skeleton-cell"
      />
    </div>
  </div>
</template>

<style scoped>
.loading-skeleton {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 1rem 0;
}

.loading-skeleton-row {
  display: flex;
  gap: 0.75rem;
}

.loading-skeleton-cell {
  flex: 1;
  background: var(--arpia-fill-light) !important;
}
</style>
