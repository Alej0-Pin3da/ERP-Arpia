import { afterEach } from 'vitest'
import { enableAutoUnmount } from '@vue/test-utils'

// Element Plus el-table measures its wrapper with ResizeObserver, which jsdom
// does not implement — without it tables never render their body (or empty
// slot). No-op polyfill keeps table layout code running in tests.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
if (!('ResizeObserver' in globalThis)) {
  ;(globalThis as unknown as { ResizeObserver: unknown }).ResizeObserver = ResizeObserverStub
}

// PrimeVue Select binds an orientation media query listener on mount; jsdom
// does not implement matchMedia. No-op polyfill keeps Select (used inside
// DataTable column filter funnels) from crashing in tests.
if (typeof globalThis.matchMedia !== 'function') {
  ;(globalThis as unknown as { matchMedia: unknown }).matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => undefined,
    removeListener: () => undefined,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    dispatchEvent: () => false,
  })
}

// Unmount every mounted component after each test to avoid leaks between specs.
enableAutoUnmount(afterEach)
