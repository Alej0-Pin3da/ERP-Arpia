<script setup lang="ts">
import { computed } from 'vue'

/**
 * ResponsiveTable — shared wrapper for the desktop <table> + mobile cards
 * pattern (pilot: InventarioView, VentasView).
 *
 * Owns the responsive visibility + scroll behavior ONCE so future column
 * changes touch one place:
 * - `#desktop` slot → horizontal-scroll wrapper, visible md and up.
 * - `#mobile` slot  → stacked cards, visible below md, never scrolls sideways.
 *
 * Stone/amber styling stays on the slotted content (views keep their outer
 * card container + inner cell classes untouched → desktop pixel-identical).
 * Shared primitives live in `src/styles/main.css`: `.table-scroll`,
 * `.th-sticky`, `.rt-mobile`, `.card-mobile`, `.card-title`.
 */
const props = withDefaults(
  defineProps<{
    /** Desktop table min-width in px. Feeds --rt-min-width (see .table-scroll). */
    minWidth?: '640' | '760' | '900'
  }>(),
  { minWidth: '900' },
)

const rootStyle = computed<Record<string, string>>(() => ({
  '--rt-min-width': `${props.minWidth}px`,
}))
</script>

<template>
  <!--
    MIGRATION PATH for the remaining 9 views + 7 modals (migrate one at a
    time, do NOT batch):
    1. Import this component:  import ResponsiveTable from '@/components/ResponsiveTable.vue'
    2. Replace `<div class="hidden overflow-x-auto md:block">` + its `<table>`
       with `<ResponsiveTable min-width="900"><template #desktop>` + the same
       `<table>` verbatim (keep its classes/handlers). Pick min-width by table
       density: '640' (≤5 cols), '760' (6-7 cols), '900' (8+ cols / sticky col).
    3. Move the mobile `<div class="... md:hidden">` block into
       `<template #mobile>` + inner `<div>` keeping every class EXCEPT md:hidden
       (e.g. keep `space-y-3 p-4 max-w-full min-w-0`). Keep text-sm on cards.
    4. Optionally replace `sticky left-0 z-10` with `.th-sticky` (position only;
       keep the bg-* class inline so sticky cells stay opaque).
    5. Keep all sorting, filters and handlers identical. No logic changes.
  -->
  <div class="rt-root" :style="rootStyle">
    <!-- Desktop: horizontal scroll wrapper, visible md and up -->
    <div class="table-scroll hidden md:block">
      <slot name="desktop" />
    </div>
    <!-- Mobile: stacked cards, no lateral scroll, readable text-sm -->
    <div class="rt-mobile md:hidden">
      <slot name="mobile" />
    </div>
  </div>
</template>
