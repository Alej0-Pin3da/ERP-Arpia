/**
 * Arpia design tokens (task S0-T2, design D2, spec BEH-4).
 *
 * Skeleton preset — full token inventory lands in S4-T6. Dark scheme only:
 * the app is an always-dark editorial UI (main.css), so light tokens are
 * intentionally left undefined and the theme is forced dark via
 * `darkModeSelector: 'html'` in main.ts.
 *
 * IMPORTANT (D1 deviation): the design names `@primeuix/themes/aura-compat`,
 * but that entry point only exists in @primeuix/themes v3 (PrimeVue v5 era,
 * where the standard presets moved to a 16px root baseline). In the pinned
 * v2.0.3 the STANDARD `aura` preset is already the 14px-calibrated one
 * (its base formField tokens — 0.75rem/0.5rem/0.875rem — are byte-identical
 * to v3's aura-compat base). Using `@primeuix/themes/aura` therefore
 * preserves D1's intent exactly: EP-era 14px density under the untouched
 * 16px root, with zero typography disruption.
 *
 * Tokens below reference the existing --arpia-* brand vars from main.css so
 * the PrimeVue surface stays single-sourced (BEH-4); --el-* overrides are
 * mapped in S4-T6.
 */
import Aura from '@primeuix/themes/aura'
import { definePreset } from '@primeuix/themes'

export const ArpiaPreset = definePreset(Aura, {
  semantic: {
    colorScheme: {
      dark: {
        // Lavender brand primary (#8c6ca1) with its hover/soft companions.
        primary: {
          color: 'var(--arpia-primary)',
          hoverColor: 'var(--arpia-primary-hover)',
          activeColor: 'var(--arpia-primary-hover)',
          softColor: 'var(--arpia-primary-soft)',
        },
        // Editorial dark surfaces (deep navy scale).
        surface: {
          0: 'var(--arpia-dark-bg)',
          50: 'var(--arpia-dark)',
          100: 'var(--arpia-dark-elevated)',
          200: 'var(--arpia-card)',
          300: 'var(--arpia-dark-elevated)',
          400: 'var(--arpia-dark)',
          500: 'var(--arpia-dark-bg)',
          600: 'var(--arpia-dark-bg)',
          700: 'var(--arpia-dark-bg)',
          800: 'var(--arpia-dark-bg)',
          900: 'var(--arpia-dark-bg)',
          950: 'var(--arpia-dark-bg)',
        },
        // Editorial text hierarchy.
        text: {
          color: 'var(--arpia-text-primary)',
          hoverColor: 'var(--arpia-text-primary)',
          mutedColor: 'var(--arpia-text-muted)',
          hoverMutedColor: 'var(--arpia-text-muted)',
        },
        // Borders and overlays.
        content: {
          borderColor: 'var(--arpia-border)',
        },
        mask: {
          background: 'rgba(0, 0, 0, 0.6)',
        },
      },
    },
  },
})