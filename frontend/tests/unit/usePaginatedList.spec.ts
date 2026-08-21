/**
 * usePaginatedList unit tests (UX slice 1, TASK-038).
 *
 * Covers loading/error/pagination/filters/sort and q debounce.
 */
import { flushPromises } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import { usePaginatedList } from '@/composables/usePaginatedList'

describe('usePaginatedList', () => {
  it('loads items and total via fetcher with default limit/offset', async () => {
    const fetcher = vi.fn().mockResolvedValue({ items: [{ id: 1 }], total: 1 })
    const list = usePaginatedList(fetcher, { pageSize: 20, debounceMs: 0 })
    await list.load()
    expect(fetcher).toHaveBeenCalledWith({ limit: 20, offset: 0 })
    expect(list.items.value).toEqual([{ id: 1 }])
    expect(list.total.value).toBe(1)
    expect(list.loading.value).toBe(false)
    expect(list.error.value).toBeNull()
  })

  it('sets loading true during fetch and handles error', async () => {
    const fetcher = vi.fn().mockRejectedValue(new Error('fail'))
    const list = usePaginatedList(fetcher, { debounceMs: 0 })
    const p = list.load()
    expect(list.loading.value).toBe(true)
    await p
    expect(list.loading.value).toBe(false)
    expect(list.error.value).toBeTruthy()
  })

  it('onPage recomputes page and calls fetcher with new offset', async () => {
    const fetcher = vi.fn().mockResolvedValue({ items: [], total: 0 })
    const list = usePaginatedList(fetcher, { pageSize: 20, debounceMs: 0 })
    await list.load()
    fetcher.mockClear()
    list.onPage({ first: 20, rows: 20 })
    await flushPromises()
    expect(list.page.value).toBe(2)
    expect(fetcher).toHaveBeenCalledWith(expect.objectContaining({ limit: 20, offset: 20 }))
  })

  it('onFilterChange merges filters, resets to page 1 and reloads', async () => {
    const fetcher = vi.fn().mockResolvedValue({ items: [], total: 0 })
    const list = usePaginatedList(fetcher, { pageSize: 20, debounceMs: 0, initialFilters: { categoria_id: null } })
    list.page.value = 3
    list.onFilterChange({ categoria_id: 5 })
    await flushPromises()
    expect(list.page.value).toBe(1)
    expect(list.filters.value.categoria_id).toBe(5)
    expect(fetcher).toHaveBeenCalledWith(expect.objectContaining({ categoria_id: 5, limit: 20, offset: 0 }))
  })

  it('onSort sets sortBy/sortOrder, resets page and reloads', async () => {
    const fetcher = vi.fn().mockResolvedValue({ items: [], total: 0 })
    const list = usePaginatedList(fetcher, { debounceMs: 0 })
    list.onSort({ prop: 'stock_actual', order: 'desc' })
    await flushPromises()
    expect(list.sortBy.value).toBe('stock_actual')
    expect(list.sortOrder.value).toBe('desc')
    expect(list.page.value).toBe(1)
    expect(fetcher).toHaveBeenCalledWith(expect.objectContaining({ sort_by: 'stock_actual', order: 'desc' }))
  })

  it('onSort with null order clears sort', async () => {
    const fetcher = vi.fn().mockResolvedValue({ items: [], total: 0 })
    const list = usePaginatedList(fetcher, { debounceMs: 0 })
    list.sortBy.value = 'fecha'
    list.sortOrder.value = 'asc'
    list.onSort({ prop: 'fecha', order: null })
    await flushPromises()
    expect(list.sortBy.value).toBeNull()
    expect(list.sortOrder.value).toBeNull()
  })

  it('onSort accepts PrimeVue shape {sortField, sortOrder}', async () => {
    const fetcher = vi.fn().mockResolvedValue({ items: [], total: 0 })
    const list = usePaginatedList(fetcher, { debounceMs: 0 })
    list.onSort({ sortField: 'fecha', sortOrder: -1 })
    await flushPromises()
    expect(list.sortBy.value).toBe('fecha')
    expect(list.sortOrder.value).toBe('desc')
  })

  it('debounces q changes (300ms default)', async () => {
    vi.useFakeTimers()
    const fetcher = vi.fn().mockResolvedValue({ items: [], total: 0 })
    const list = usePaginatedList(fetcher) // default 300ms
    list.q.value = 'harina'
    expect(fetcher).not.toHaveBeenCalled()
    // watch flush is async (next tick) before the debounce timer starts
    await Promise.resolve()
    vi.advanceTimersByTime(300)
    await flushPromises()
    expect(fetcher).toHaveBeenCalledWith(expect.objectContaining({ q: 'harina' }))
    vi.useRealTimers()
  })

  it('onSearch sets q and with debounceMs 0 loads immediately', async () => {
    const fetcher = vi.fn().mockResolvedValue({ items: [], total: 0 })
    const list = usePaginatedList(fetcher, { debounceMs: 0 })
    list.onSearch('aceite')
    await flushPromises()
    expect(list.q.value).toBe('aceite')
    expect(fetcher).toHaveBeenCalledWith(expect.objectContaining({ q: 'aceite' }))
  })

  it('onPrimeVueFilter normalizes and delegates to onFilterChange', async () => {
    const fetcher = vi.fn().mockResolvedValue({ items: [], total: 0 })
    const list = usePaginatedList(fetcher, { debounceMs: 0 })
    list.onPrimeVueFilter({ filters: { categoria: { value: 2, matchMode: 'equals' } } as unknown as Record<string, unknown> }, { categoria: 'categoria_id' })
    await flushPromises()
    expect(list.filters.value.categoria_id).toBe(2)
  })
})
