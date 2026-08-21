/**
 * usePaginatedList — unified pagination composable (UX slice 1, TASK-038).
 *
 * Centralizes the duplicated logic from VentasView (455L), InventarioView
 * (540L) and FinanzasView (601L):
 * - page/pageSize -> limit/offset via buildListParams
 * - filters + q + sortBy/sortOrder -> query params
 * - parsePrimeVueFilters / parsePrimeVueSort adapters
 * - debounce for q (300ms)
 * - optional URL sync (?page=&q=&sort_by=&order=)
 * - loading / error / total / items state
 *
 * ### Usage
 * ```ts
 * const list = usePaginatedList<InsumoRead>(
 *   (params) => insumosApi.list(params),
 *   { pageSize: 20, initialFilters: { categoria_id: null } }
 * )
 * // in template: :rows="list.items" :loading="list.loading"
 * //             <Paginator :total-records="list.total" @page="list.onPage" />
 * //             @filter-change="list.onFilterChange" @sort-change="list.onSort"
 * ```
 *
 * ### Migration guide (one view at a time)
 * 1. Replace per-view refs (page, pageSize, filtros, q, sortBy, sortOrder,
 *    loading, error, items, total) with a single `usePaginatedList` call.
 * 2. Wire the fetcher: `(params) => yourApi.list(params)` already expects the
 *    shape `buildListParams` produces.
 * 3. Replace manual `load()` that did `Promise.all([paginated, lookups])` with
 *    `list.load()` for the table + keep lookup fetches separate (lookups use
 *    `src/api/lookups.ts`).
 * 4. Replace `@filter-change` / `@sort-change` / `@page` / search handlers
 *    with `list.onFilterChange` / `list.onSort` / `list.onPage` / `list.onSearch`.
 *    For PrimeVue DataTable raw events use `list.onPrimeVueFilter` / `onPrimeVueSort`
 *    or pass through `parsePrimeVueFilters` manually — `onFilterChange` already
 *    handles the normalized `{ field: value }` shape.
 * 5. Replace ad-hoc `<Message>` / `#empty` with `<ErrorState>` / `<EmptyState>`
 *    / `<LoadingSkeleton>` driven by `list.error` / `list.items.length === 0`.
 *
 * InventarioView (Insumos tab) is the reference migrated example.
 */
import { onUnmounted, ref, watch } from 'vue'

import { buildListParams } from '@/utils/pagination'
import { parseColumnFilter, parsePrimeVueFilters, parsePrimeVueSort } from '@/utils/table-filters'

export interface Paginated<T> {
  items: T[]
  total: number
}

export interface UsePaginatedListOptions {
  /** Rows per page (default 20). */
  pageSize?: number
  /** Initial 1-based page (default 1). */
  page?: number
  /** Initial filter bag (e.g. { categoria_id: null }). */
  initialFilters?: Record<string, unknown>
  /** Initial global search term. */
  initialQ?: string
  /** Debounce for q in ms (default 300; 0 disables). */
  debounceMs?: number
  /** Sync page/q/sort to URL query string (default false). */
  syncUrl?: boolean
  /** Initial sort field. */
  initialSortBy?: string | null
  /** Initial sort direction. */
  initialSortOrder?: 'asc' | 'desc' | null
}

export function usePaginatedList<T>(
  fetcher: (params: Record<string, unknown>) => Promise<Paginated<T>>,
  options: UsePaginatedListOptions = {},
) {
  const page = ref(options.page ?? 1)
  const pageSize = ref(options.pageSize ?? 20)
  const filters = ref<Record<string, unknown>>({ ...(options.initialFilters ?? {}) })
  const q = ref(options.initialQ ?? '')
  const sortBy = ref<string | null>(options.initialSortBy ?? null)
  const sortOrder = ref<'asc' | 'desc' | null>(options.initialSortOrder ?? null)

  const items = ref<T[]>([]) as import('vue').Ref<T[]>
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)

  let debounceTimer: ReturnType<typeof setTimeout> | null = null
  const debounceMs = options.debounceMs ?? 300

  function buildParams(): Record<string, unknown> {
    // Strip null/undefined filters so buildListParams doesn't forward them as
    // explicit query keys — mirrors the per-view filtering already done.
    const cleanFilters: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(filters.value)) {
      if (v !== null && v !== undefined && v !== '') cleanFilters[k] = v
    }
    return buildListParams({
      page: page.value,
      pageSize: pageSize.value,
      filtros: cleanFilters,
      q: q.value,
      sortBy: sortBy.value ?? undefined,
      sortOrder: sortOrder.value ?? undefined,
    })
  }

  function syncToUrl(): void {
    if (!options.syncUrl || typeof window === 'undefined') return
    const url = new URL(window.location.href)
    url.searchParams.set('page', String(page.value))
    if (q.value) url.searchParams.set('q', q.value)
    else url.searchParams.delete('q')
    if (sortBy.value && sortOrder.value) {
      url.searchParams.set('sort_by', sortBy.value)
      url.searchParams.set('order', sortOrder.value)
    } else {
      url.searchParams.delete('sort_by')
      url.searchParams.delete('order')
    }
    for (const [k, v] of Object.entries(filters.value)) {
      if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, String(v))
      else url.searchParams.delete(k)
    }
    window.history.replaceState(null, '', url.toString())
  }

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const params = buildParams()
      const result = await fetcher(params)
      items.value = result.items
      total.value = result.total
      syncToUrl()
    } catch {
      error.value = 'No se pudo cargar la información. Verifica la conexión con el servidor.'
    } finally {
      loading.value = false
    }
  }

  function onFilterChange(newFilters: Record<string, unknown>): void {
    // Merge incoming filters; explicit null clears the key.
    for (const [k, v] of Object.entries(newFilters)) {
      if (v === null || v === undefined || v === '') {
        // Keep key as null so next buildParams strips it — preserves shape.
        filters.value[k] = null as unknown as string
      } else {
        filters.value[k] = v
      }
    }
    page.value = 1
    void load()
  }

  /**
   * Adapter for PrimeVue DataTable @filter payload.
   * Normalizes `Record<field, {value, matchMode}>` -> single-value bag and
   * delegates to onFilterChange (resets to page 1).
   */
  function onPrimeVueFilter(
    e: { filters: Record<string, unknown> },
    fieldMap?: Record<string, string>,
  ): void {
    // e.filters is PrimeVue's shape; cast for parse helper.
    const normalized = parsePrimeVueFilters(
      e.filters as Record<string, import('@/utils/table-filters').PrimeVueFilterConstraint | import('@/utils/table-filters').PrimeVueFilterConstraint[]>,
    )
    const bag: Record<string, unknown> = {}
    for (const [field, values] of Object.entries(normalized)) {
      const mapped = fieldMap?.[field] ?? field
      bag[mapped] = parseColumnFilter(values)
    }
    onFilterChange(bag)
  }

  function onSearch(value: string): void {
    q.value = value
    page.value = 1
    // Debounce is handled by the watcher below; if debounceMs is 0 load now.
    if (debounceMs === 0) void load()
  }

  // Debounced q watcher — mirrors the UX expectation (typeahead 300ms).
  if (debounceMs > 0) {
    watch(q, () => {
      if (debounceTimer) clearTimeout(debounceTimer)
      debounceTimer = setTimeout(() => {
        page.value = 1
        void load()
      }, debounceMs)
    })
    onUnmounted(() => {
      if (debounceTimer) clearTimeout(debounceTimer)
    })
  }

  function onSort(sort: { prop: string; order: 'asc' | 'desc' | null } | { sortField?: string; sortOrder?: number }): void {
    let prop: string
    let order: 'asc' | 'desc' | null
    if ('prop' in sort) {
      prop = sort.prop
      order = sort.order
    } else {
      const parsed = parsePrimeVueSort(sort)
      prop = parsed.prop
      order = parsed.order
    }
    sortBy.value = order === null ? null : prop
    sortOrder.value = order
    page.value = 1
    void load()
  }

  /** PrimeVue Paginator @page adapter: 0-based first -> 1-based page. */
  function onPage(e: { first: number; rows: number }): void {
    page.value = Math.floor(e.first / e.rows) + 1
    pageSize.value = e.rows
    void load()
  }

  return {
    items,
    total,
    loading,
    error,
    page,
    pageSize,
    filters,
    q,
    sortBy,
    sortOrder,
    load,
    onFilterChange,
    onPrimeVueFilter,
    onSearch,
    onSort,
    onPage,
  }
}
