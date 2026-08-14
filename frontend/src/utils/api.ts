/**
 * Extracts the `detail` string from an API error response body.
 *
 * Covers FastAPI's standard `{ detail: string }` shape returned by HTTP 4xx/5xx
 * responses. Returns null when the error does not carry a parseable detail so
 * callers can fall back to their own message.
 */
export function serverDetail(err: unknown): string | null {
  if (typeof err === 'object' && err !== null && 'response' in err) {
    const data = (err as { response?: { data?: unknown } }).response?.data
    if (
      typeof data === 'object' &&
      data !== null &&
      'detail' in data &&
      typeof (data as { detail: unknown }).detail === 'string'
    ) {
      return (data as { detail: string }).detail
    }
  }
  return null
}
