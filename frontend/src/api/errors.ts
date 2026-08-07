/**
 * API error classification helpers.
 *
 * The axios layer rejects with AxiosError instances, but tests and mocks may
 * hand back structurally identical plain errors — so these helpers inspect
 * the shape (`response.status`), not the constructor.
 */

/** True when the error is an HTTP 401 (unauthenticated / expired token). */
export function isUnauthorized(err: unknown): boolean {
  return (
    typeof err === 'object' &&
    err !== null &&
    'response' in err &&
    typeof (err as { response?: { status?: number } }).response?.status === 'number' &&
    (err as { response: { status: number } }).response.status === 401
  )
}
