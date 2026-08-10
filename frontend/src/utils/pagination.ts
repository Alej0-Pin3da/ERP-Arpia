/**
 * Server-side list param builders (design D3, spec FE-1/FE-2).
 *
 * Every table view owns its pagination state (page/pageSize/filtros/q) and
 * derives the backend query params with this helper, so page changes map to
 * limit/offset and filter changes always restart at page 1.
 */

export interface ListFilters {
  [key: string]: string | number | boolean | null | undefined
}

export interface BuildListParamsOptions {
  /** 1-based page number (defaults to 1). */
  page?: number
  /** Rows per page (defaults to 50). */
  pageSize?: number
  /** Typed per-column filters already validated by the caller. */
  filtros?: ListFilters
  /** Global search term (undefined omits `q`). */
  q?: string
  /** Server-side sort column key (backend whitelist); only sent with sortOrder. */
  sortBy?: string
  /** Server-side sort direction; only sent with sortBy. */
  sortOrder?: 'asc' | 'desc'
}

/** Build `{limit, offset, ...filtros, q?, sort_by?, order?}` from the view's state. */
export function buildListParams(options: BuildListParamsOptions = {}): Record<string, unknown> {
  const page = options.page ?? 1
  const pageSize = options.pageSize ?? 50
  const params: Record<string, unknown> = {
    limit: pageSize,
    offset: (page - 1) * pageSize,
  }
  for (const [key, value] of Object.entries(options.filtros ?? {})) {
    if (value !== undefined && value !== null && value !== '') {
      params[key] = value
    }
  }
  if (options.q !== undefined && options.q !== null && options.q !== '') {
    params.q = options.q
  }
  if (
    options.sortBy !== undefined &&
    options.sortBy !== '' &&
    options.sortOrder !== undefined &&
    options.sortOrder !== null
  ) {
    params.sort_by = options.sortBy
    params.order = options.sortOrder
  }
  return params
}
