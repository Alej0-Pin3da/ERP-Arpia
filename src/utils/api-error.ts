/**
 * Shared FastAPI error-detail extractor (typed, no `any`).
 *
 * Backend `detail` may be a string or a validation-error array — both are
 * surfaced verbatim. Falls back to the Error message, then to `fallback`.
 */

interface ValidationIssue {
  msg?: unknown
}

interface ApiErrorShape {
  response?: { data?: unknown } | null
  message?: unknown
}

function rawDetail(e: unknown): unknown {
  const shape = e as ApiErrorShape | null | undefined
  const data = shape?.response?.data
  if (data != null && typeof data === 'object' && 'detail' in data) {
    return (data as { detail?: unknown }).detail
  }
  return undefined
}

export function getApiErrorDetail(e: unknown, fallback: string, separator = '; '): string {
  const detail = rawDetail(e)
  if (typeof detail === 'string' && detail.trim()) return detail
  if (Array.isArray(detail)) {
    const parts = detail.map((d: unknown) => {
      if (typeof d === 'string') return d
      if (typeof d === 'object' && d !== null && 'msg' in d) {
        const m = (d as ValidationIssue).msg
        return m == null ? JSON.stringify(d) : String(m)
      }
      return JSON.stringify(d)
    })
    if (parts.length) return parts.join(separator)
  }
  if (e instanceof Error && e.message) return e.message
  return fallback
}
