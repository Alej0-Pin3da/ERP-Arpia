/**
 * Redirect helpers for the API layer. Kept in a tiny module so refresh/client
 * never import the router directly (the router arrives in PR3).
 */

/** Navigate to the login screen. The router guard (PR3) re-applies any
 * `redirect` query param. Safe under SSR-less jsdom tests. */
export function redirectToLogin(path = '/login'): void {
  if (typeof window !== 'undefined' && window.location.pathname !== path) {
    window.location.assign(path)
  }
}
