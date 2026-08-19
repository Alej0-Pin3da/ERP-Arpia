/**
 * ArpiaPreset dark token inventory contract (task S4-T6, design D2/D3, spec BEH-4).
 *
 * The preset is the PrimeVue side of the theme mapping: every `--p-*` token
 * must be driven by the `--arpia-*` brand vars from main.css (single source of
 * truth). This spec pins the FULL inventory so the skeleton (slice 0) cannot
 * silently regress to Aura defaults: surfaces, text, borders, form fields,
 * overlays, highlights and the component-level EP-era density (4px inputs /
 * buttons, 8px cards, dark table headers, lavender hover).
 */
import { describe, expect, it } from 'vitest'

import { ArpiaPreset } from '@/styles/arpia-preset'

const dark = ArpiaPreset.semantic.colorScheme.dark

describe('ArpiaPreset — dark token inventory (S4-T6)', () => {
  it('defines the dark scheme driven by --arpia-* brand vars', () => {
    expect(dark).toBeDefined()
    expect(dark.primary.color).toBe('var(--arpia-primary)')
    expect(dark.primary.hoverColor).toBe('var(--arpia-primary-hover)')
    expect(dark.primary.activeColor).toBe('var(--arpia-primary-hover)')
    expect(dark.primary.contrastColor).toBe('var(--arpia-on-primary)')
  })

  it('maps the full 0..950 surface scale onto --arpia-* surfaces', () => {
    for (const step of [0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]) {
      expect(dark.surface[step]).toMatch(/^var\(--arpia-/)
    }
    expect(dark.surface[0]).toBe('var(--arpia-card)')
    expect(dark.surface[950]).toBe('var(--arpia-dark-bg)')
  })

  it('maps the text hierarchy to --arpia-text-* tokens', () => {
    expect(dark.text.color).toBe('var(--arpia-text-primary)')
    expect(dark.text.hoverColor).toBe('var(--arpia-text-primary)')
    expect(dark.text.mutedColor).toBe('var(--arpia-text-muted)')
    expect(dark.text.hoverMutedColor).toBe('var(--arpia-text-muted)')
  })

  it('maps content surfaces and borders to the editorial chrome', () => {
    expect(dark.content.background).toBe('var(--arpia-card)')
    expect(dark.content.hoverBackground).toBe('var(--arpia-dark-elevated)')
    expect(dark.content.borderColor).toBe('var(--arpia-border)')
    expect(dark.content.color).toBe('var(--arpia-text-primary)')
  })

  it('maps form fields (inputs/selects/datepickers) to EP-era dark surfaces', () => {
    expect(dark.formField.background).toBe('var(--arpia-dark-elevated)')
    expect(dark.formField.borderColor).toBe('var(--arpia-border)')
    expect(dark.formField.hoverBorderColor).toBe('var(--arpia-border-hover)')
    expect(dark.formField.focusBorderColor).toBe('var(--arpia-primary)')
    expect(dark.formField.invalidBorderColor).toBe('var(--arpia-danger)')
    expect(dark.formField.placeholderColor).toBe('var(--arpia-text-faint)')
    expect(dark.formField.disabledColor).toBe('var(--arpia-text-disabled)')
    expect(dark.formField.borderRadius).toBe('var(--arpia-radius)')
  })

  it('maps overlay surfaces (select/popover/modal) onto the card surface', () => {
    for (const kind of ['select', 'popover', 'modal']) {
      expect(dark.overlay[kind].background).toBe('var(--arpia-card)')
      expect(dark.overlay[kind].borderColor).toBe('var(--arpia-border)')
    }
  })

  it('maps the mask to the --arpia-* overlay token', () => {
    expect(dark.mask.background).toBe('var(--arpia-overlay)')
  })

  it('maps highlights and list selection to translucent lavender', () => {
    expect(dark.highlight.background).toContain('color-mix(in srgb, var(--arpia-primary-deep)')
    expect(dark.list.option.focusBackground).toBe('var(--arpia-dark-elevated)')
    expect(dark.list.option.selectedBackground).toContain('color-mix(in srgb, var(--arpia-primary-deep)')
    expect(dark.list.option.selectedColor).toBe('var(--arpia-primary-soft)')
  })

  it('keeps cards at the EP 8px radius and shadow on the editorial surface', () => {
    expect(ArpiaPreset.components.card.root.borderRadius).toBe('var(--arpia-radius-lg)')
    expect(ArpiaPreset.components.card.root.background).toBe('var(--arpia-dark-elevated)')
    expect(ArpiaPreset.components.card.root.shadow).toBe('var(--arpia-shadow-card)')
  })

  it('keeps buttons, dialogs, tags and toasts at the EP 4px density', () => {
    expect(ArpiaPreset.components.button.root.label.fontWeight).toBe('600')
    expect(ArpiaPreset.components.dialog.root.borderRadius).toBe('var(--arpia-radius)')
    expect(ArpiaPreset.components.tag.root.borderRadius).toBe('var(--arpia-radius)')
    expect(ArpiaPreset.components.toast.root.borderRadius).toBe('var(--arpia-radius)')
    expect(ArpiaPreset.components.message.root.borderRadius).toBe('var(--arpia-radius)')
  })

  it('styles the datatable header like the EP table header', () => {
    expect(ArpiaPreset.components.datatable.header.background).toBe('var(--arpia-card)')
    expect(ArpiaPreset.components.datatable.header.color).toBe('var(--arpia-text-muted)')
    expect(ArpiaPreset.components.datatable.row.background).toBe('transparent')
    expect(ArpiaPreset.components.datatable.row.hoverBackground).toContain(
      'color-mix(in srgb, var(--arpia-primary-deep)',
    )
  })

  it('maps toast and message severities onto the --arpia-* semantic colors', () => {
    const toastSuccess = ArpiaPreset.components.toast.colorScheme.dark.success
    expect(toastSuccess.background).toContain('var(--arpia-success)')
    expect(toastSuccess.detailColor).toBe('var(--arpia-text-primary)')
    const toastError = ArpiaPreset.components.toast.colorScheme.dark.error
    expect(toastError.background).toContain('var(--arpia-danger)')
    const messageWarn = ArpiaPreset.components.message.colorScheme.dark.warn
    expect(messageWarn.background).toContain('var(--arpia-warning)')
  })
})