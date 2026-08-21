# Arpia Design Tokens

Source of truth: `src/styles/main.css` (`:root --arpia-*`) + `src/styles/arpia-preset.ts` (PrimeVue Aura → ArpiaPreset). The preset does not invent colors — every PrimeVue semantic token references a `--arpia-*` var.

## How to extend the preset (Aura → ArpiaPreset)

```ts
import Aura from '@primeuix/themes/aura'
import { definePreset } from '@primeuix/themes'

export const ArpiaPreset = definePreset(Aura, {
  semantic: {
    colorScheme: { dark: { primary: { color: 'var(--arpia-primary)' }, ... } },
    // ...
  },
  components: { card: { ... }, datatable: { ... } },
})
// main.ts:
// app.use(PrimeVue, { theme: { preset: ArpiaPreset, options: { darkModeSelector: 'html' } } })
```

- Keep the app always-dark: the light scheme stays at Aura defaults; dark mode is forced via `darkModeSelector: 'html'` (a class selector is required — a bare `html` type selector loses the cascade to Aura's `:root,:host` light vars).
- Add new components under `components` with `var(--arpia-*)` refs, not hard-coded hex.
- Gold editorial accents (eyebrows, rules, gold text) are page typography in `main.css`, not component tokens.

---

## Brand / Primary

| Token | Value | Usage |
|---|---|---|
| `--arpia-primary` | `#8c6ca1` | Primary actions, focus borders, links |
| `--arpia-primary-hover` | `#7a5c8e` | Hover/active of primary |
| `--arpia-primary-deep` | `#7a5d8e` | Tint base for translucent lavender washes (`color-mix` 12–25%) |
| `--arpia-primary-soft` | `#d7cafd` | Selected text, active nav |
| `--arpia-primary-rgb` | `140,108,161` | RGB for `rgba()` needs |
| `--arpia-on-primary` | `#ffffff` | Text/icon on primary paint |
| `--arpia-secondary` | `#2997aa` | Gradient companion (`--arpia-brand-gradient`) |
| `--arpia-gold` | `#c8a96b` | Eyebrows, rules, editorial accents |
| `--arpia-accent` | `#e9f8f9` | Light accent |
| `--arpia-mint` | `#cae6e8` | Mint accent |

## Surfaces (dark editorial)

| Token | Value | Usage |
|---|---|---|
| `--arpia-dark-bg` | `#11131a` | Page background (`--arpia-bg-gradient`) |
| `--arpia-dark` | `#181823` | Surface 400 |
| `--arpia-dark-elevated` | `#171924` | Elevated surface (form fields, card) |
| `--arpia-card` | `#1a1c26` | Card / table header / overlay |
| `--arpia-fill-extra-light` | `#191b24` | Fill scale |
| `--arpia-fill-light` | `#1d1f29` | Fill / skeleton |
| `--arpia-fill-dark` | `#20222d` | Fill |
| `--arpia-fill-darker` | `#232633` | Fill |

Preset maps these to `semantic.surface.{0,50,100,200,300,400,500...}` (Aura surface ramp).

## Text on dark

| Token | Value | Usage |
|---|---|---|
| `--arpia-text-primary` | `rgba(255,255,255,0.9)` | Body, headings |
| `--arpia-text-regular` | `rgba(255,255,255,0.75)` | Secondary body |
| `--arpia-text-muted` | `rgba(255,255,255,0.6)` | Muted, table headers |
| `--arpia-text-faint` | `rgba(255,255,255,0.4)` | Placeholder, empty icons |
| `--arpia-text-disabled` | `rgba(255,255,255,0.3)` | Disabled |

## Semantic (status)

| Token | Value | Aliases |
|---|---|---|
| `--arpia-success` | `#4ade80` | `--arpia-stock-ok` |
| `--arpia-success-dark` | `#16a34a` |  |
| `--arpia-warning` | `#e6a23c` |  |
| `--arpia-warning-dark` | `#b88230` |  |
| `--arpia-danger` | `#f87171` | `--arpia-error`, `--arpia-stock-low` |
| `--arpia-danger-dark` | `#dc2626` |  |
| `--arpia-info` | `#a3adc1` |  |
| `--arpia-info-dark` | `#73767a` |  |
| `--arpia-whatsapp` | `#25d366` | Hover: `--arpia-whatsapp-hover` |

Used in `semantic.highlight`, `message`, `tag`, `formField.invalidBorderColor`.

## Borders

| Token | Value |
|---|---|
| `--arpia-border` | `rgba(255,255,255,0.08)` |
| `--arpia-border-strong` | `rgba(255,255,255,0.12)` |
| `--arpia-border-subtle` | `rgba(255,255,255,0.06)` |
| `--arpia-border-faint` | `rgba(255,255,255,0.04)` |
| `--arpia-border-dark` | `rgba(255,255,255,0.22)` |
| `--arpia-border-darker` | `rgba(255,255,255,0.3)` |
| `--arpia-border-hover` | `rgba(255,255,255,0.4)` |

## Radius & Shadows

| Token | Value | Usage |
|---|---|---|
| `--arpia-radius` | `4px` | Form fields, dialogs, tags, messages |
| `--arpia-radius-lg` | `8px` | Cards |
| `--arpia-shadow-card` | `0 2px 10px rgba(0,0,0,0.25)` | Cards |
| `--arpia-shadow-pop` | `0 0 12px rgba(0,0,0,0.5)` | Select/popover |
| `--arpia-shadow-overlay` | `0 12px 32px 4px rgba(0,0,0,0.45), 0 8px 20px rgba(0,0,0,0.5)` | Modal |
| `--arpia-shadow-deep` | `0 16px 48px 16px rgba(0,0,0,0.6), 0 12px 32px rgba(0,0,0,0.5)` | Deep |
| `--arpia-shadow-glow` | `0 0 6px rgba(0,0,0,0.5)` | Glow |

## Typography

| Role | Token / Stack | Notes |
|---|---|---|
| Body | `--arpia-font-body`: `'Lora', Georgia, serif` | Global `body`, 16px / 1.65 |
| Headings | `--arpia-font-heading`: `'Nunito Sans', system-ui` | `h1–h6`, weight 600 |
| Buttons | `--arpia-font-button`: `'Montserrat', system-ui` | `.p-button` uppercase, 600, 0.05em tracking |

Editorial utilities in `main.css`: `.arpia-eyebrow` (gold uppercase), `.arpia-display`, `.arpia-gold-text` (gradient), `.arpia-rule`.

## Spacing scale

Base 4px (`--arpia-radius`). Common gaps: `0.5rem` (8px), `0.75rem` (12px), `1rem` (16px), `1.5rem` (24px). Table wrap uses `1rem` header margin, `0.75rem` toolbar gap; mobile collapses to column with `0.5rem`.

## Overlays

`--arpia-overlay: rgba(0,0,0,0.6)` (mask), `--arpia-overlay-light: 0.55`, `--arpia-overlay-lighter: 0.45`.

## Gradients

- `--arpia-bg-gradient: linear-gradient(180deg, #11131a 0%, #171924 100%)` — page
- `--arpia-brand-gradient: linear-gradient(135deg, #8c6ca1 0%, #2997aa 100%)`
- `--arpia-rule-gradient` and `--arpia-gold-text` for editorial dividers
