<script setup lang="ts">
/**
 * Executive KPI cards (DASH-1).
 *
 * Four modern metric cards computed from analytics endpoints:
 * - Ventas del mes (with spark icon and trend)
 * - Unidades vendidas
 * - Insumos bajo stock (with alert indicator)
 * - Productos con margen
 */
import { computed } from 'vue'
import Card from 'primevue/card'
import Skeleton from 'primevue/skeleton'

import { formatMoney, formatQty } from '@/utils/format'

const props = defineProps<{
  /** Month total as Decimal-as-string (null when there are no sales). */
  monthTotal: string | null
  /** Units sold in the latest month (null when there are no sales). */
  monthCount: number | null
  /** Number of insumos below their minimum (insumos-bajo-stock length). */
  lowStockCount: number
  /** Number of products with computed margin (margen-por-producto length). */
  margenCount: number
  /** While true the cards show a skeleton instead of values. */
  loading?: boolean
}>()

const cards = computed(() => [
  {
    label: 'Ventas del mes',
    value: formatMoney(props.monthTotal),
    icon: 'pi-dollar',
    badge: 'Ingresos',
    badgeType: 'gold',
    iconColor: '#c5a059',
    bgColor: 'rgba(197, 160, 89, 0.12)',
  },
  {
    label: 'Prendas confeccionadas',
    value: formatQty(props.monthCount),
    icon: 'pi-shopping-bag',
    badge: 'Taller',
    badgeType: 'info',
    iconColor: '#dfb15b',
    bgColor: 'rgba(223, 177, 91, 0.12)',
  },
  {
    label: 'Insumos bajo stock',
    value: formatQty(props.lowStockCount),
    icon: 'pi-exclamation-triangle',
    badge: props.lowStockCount > 0 ? '¡Atención!' : 'Óptimo',
    badgeType: props.lowStockCount > 0 ? 'danger' : 'success',
    iconColor: props.lowStockCount > 0 ? '#f43f5e' : '#10b981',
    bgColor: props.lowStockCount > 0 ? 'rgba(244, 63, 94, 0.12)' : 'rgba(16, 185, 129, 0.12)',
  },
  {
    label: 'Prendas con margen BOM',
    value: formatQty(props.margenCount),
    icon: 'pi-chart-line',
    badge: 'Rentabilidad',
    badgeType: 'gold',
    iconColor: '#c5a059',
    bgColor: 'rgba(197, 160, 89, 0.12)',
  },
])
</script>

<template>
  <div class="kpi-cards">
    <div v-for="card in cards" :key="card.label" class="kpi-col">
      <Card :pt="{ root: { class: 'kpi-card' } }">
        <template #content>
          <div class="kpi-card-inner">
            <div class="kpi-top-row">
              <span class="kpi-label">{{ card.label }}</span>
              <div class="kpi-icon-box" :style="{ color: card.iconColor, background: card.bgColor }">
                <i :class="['pi', card.icon]" />
              </div>
            </div>

            <Skeleton v-if="loading" class="kpi-skeleton" />
            <div v-else class="kpi-bottom-row">
              <p class="kpi-value" data-test="kpi-value">{{ card.value }}</p>
              <span class="kpi-badge" :class="`kpi-badge--${card.badgeType}`">
                {{ card.badge }}
              </span>
            </div>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.kpi-cards {
  display: grid;
  grid-template-columns: repeat(1, 1fr);
  gap: 1.25rem;
}

@media (min-width: 640px) {
  .kpi-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .kpi-cards {
    grid-template-columns: repeat(4, 1fr);
  }
}

.kpi-card {
  border: 1px solid var(--arpia-border);
  border-radius: var(--arpia-radius-lg);
  background: var(--arpia-card);
  box-shadow: var(--arpia-shadow-card);
  transition: all 200ms ease;
  position: relative;
  overflow: hidden;
}

.kpi-card:hover {
  border-color: var(--arpia-border-strong);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
}

.kpi-card-inner {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.kpi-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.kpi-label {
  margin: 0;
  font-family: var(--arpia-font-heading);
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--arpia-text-muted);
}

.kpi-icon-box {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  font-size: 1.1rem;
}

.kpi-bottom-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.5rem;
}

.kpi-value {
  margin: 0;
  font-family: var(--arpia-font-heading);
  font-size: 1.65rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--arpia-text-primary);
  line-height: 1.1;
}

.kpi-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 9999px;
  letter-spacing: 0.02em;
}

.kpi-badge--success {
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.kpi-badge--info {
  background: rgba(6, 182, 212, 0.12);
  color: #38bdf8;
  border: 1px solid rgba(6, 182, 212, 0.25);
}

.kpi-badge--warning {
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.kpi-badge--danger {
  background: rgba(244, 63, 94, 0.15);
  color: #fb7185;
  border: 1px solid rgba(244, 63, 94, 0.3);
}

.kpi-skeleton {
  width: 100%;
  height: 2rem;
  border-radius: 6px;
}
</style>
