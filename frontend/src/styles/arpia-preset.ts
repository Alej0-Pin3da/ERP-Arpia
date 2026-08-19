/**
 * Arpia design tokens (task S0-T2 skeleton → S4-T6 full inventory; design
 * D1/D2/D3, spec BEH-4).
 *
 * Dark scheme only: the app is an always-dark editorial UI (main.css), so the
 * light scheme is left at the Aura base and the theme is forced dark via
 * `darkModeSelector: 'html'` in main.ts.
 *
 * D1 resolution: `@primeuix/themes/aura` (v2) is the 14px-calibrated preset —
 * its base formField tokens are byte-identical to v3's aura-compat — so
 * EP-era 14px density is preserved under the untouched 16px root.
 *
 * BEH-4 single source: every token below references the `--arpia-*` brand
 * vars declared in main.css, which also drive the `--el-*` alias layer. The
 * gold editorial accents (eyebrows, rules, gold text) are page typography in
 * main.css, not component tokens — nothing in the component layer consumes
 * them, so they intentionally stay out of this preset.
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
          contrastColor: 'var(--arpia-on-primary)',
          hoverColor: 'var(--arpia-primary-hover)',
          activeColor: 'var(--arpia-primary-hover)',
        },
        // Editorial dark surfaces (deep navy scale, 0 = lightest used).
        surface: {
          0: 'var(--arpia-card)',
          50: 'var(--arpia-dark-elevated)',
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
        // Panels, tables and borders.
        content: {
          background: 'var(--arpia-card)',
          hoverBackground: 'var(--arpia-dark-elevated)',
          borderColor: 'var(--arpia-border)',
          color: 'var(--arpia-text-primary)',
          hoverColor: 'var(--arpia-text-primary)',
        },
        // Selection/highlight washes — translucent lavender (EP light-7/5).
        highlight: {
          background: 'color-mix(in srgb, var(--arpia-primary-deep) 18%, transparent)',
          focusBackground: 'color-mix(in srgb, var(--arpia-primary-deep) 25%, transparent)',
          color: 'var(--arpia-text-primary)',
          focusColor: 'var(--arpia-text-primary)',
        },
        mask: {
          background: 'var(--arpia-overlay)',
          color: 'var(--arpia-text-primary)',
        },
        // Form fields (InputText/Select/InputNumber/DatePicker/Password).
        formField: {
          background: 'var(--arpia-dark-elevated)',
          disabledBackground: 'var(--arpia-card)',
          filledBackground: 'var(--arpia-card)',
          filledHoverBackground: 'var(--arpia-card)',
          filledFocusBackground: 'var(--arpia-card)',
          borderColor: 'var(--arpia-border)',
          hoverBorderColor: 'var(--arpia-border-hover)',
          focusBorderColor: 'var(--arpia-primary)',
          invalidBorderColor: 'var(--arpia-danger)',
          color: 'var(--arpia-text-primary)',
          disabledColor: 'var(--arpia-text-disabled)',
          placeholderColor: 'var(--arpia-text-faint)',
          invalidPlaceholderColor: 'var(--arpia-danger)',
          floatLabelColor: 'var(--arpia-text-faint)',
          floatLabelFocusColor: 'var(--arpia-primary)',
          floatLabelActiveColor: 'var(--arpia-text-faint)',
          floatLabelInvalidColor: 'var(--arpia-danger)',
          iconColor: 'var(--arpia-text-muted)',
          borderRadius: 'var(--arpia-radius)',
        },
        // Overlays (select dropdown, popover, dialog) sit on the card surface.
        overlay: {
          select: {
            background: 'var(--arpia-card)',
            borderColor: 'var(--arpia-border)',
            color: 'var(--arpia-text-primary)',
          },
          popover: {
            background: 'var(--arpia-card)',
            borderColor: 'var(--arpia-border)',
            color: 'var(--arpia-text-primary)',
          },
          modal: {
            background: 'var(--arpia-card)',
            borderColor: 'var(--arpia-border)',
            color: 'var(--arpia-text-primary)',
          },
        },
        list: {
          option: {
            focusBackground: 'var(--arpia-dark-elevated)',
            selectedBackground: 'color-mix(in srgb, var(--arpia-primary-deep) 15%, transparent)',
            selectedFocusBackground:
              'color-mix(in srgb, var(--arpia-primary-deep) 15%, transparent)',
            color: 'var(--arpia-text-primary)',
            focusColor: 'var(--arpia-text-primary)',
            selectedColor: 'var(--arpia-primary-soft)',
            selectedFocusColor: 'var(--arpia-primary-soft)',
            icon: {
              color: 'var(--arpia-text-muted)',
              focusColor: 'var(--arpia-text-primary)',
            },
          },
          optionGroup: {
            background: 'transparent',
            color: 'var(--arpia-text-muted)',
          },
        },
        navigation: {
          item: {
            focusBackground: 'color-mix(in srgb, var(--arpia-primary-deep) 20%, transparent)',
            activeBackground: 'color-mix(in srgb, var(--arpia-primary-deep) 20%, transparent)',
            color: 'var(--arpia-text-primary)',
            focusColor: 'var(--arpia-primary-soft)',
            activeColor: 'var(--arpia-primary-soft)',
            icon: {
              color: 'var(--arpia-text-muted)',
              focusColor: 'var(--arpia-primary-soft)',
              activeColor: 'var(--arpia-primary-soft)',
            },
          },
          submenuLabel: {
            background: 'transparent',
            color: 'var(--arpia-text-muted)',
          },
          submenuIcon: {
            color: 'var(--arpia-text-muted)',
            focusColor: 'var(--arpia-primary-soft)',
            activeColor: 'var(--arpia-primary-soft)',
          },
        },
      },
    },
    // EP-era overlay shadows (el-box-shadow family).
    overlay: {
      select: { shadow: 'var(--arpia-shadow-pop)' },
      popover: { shadow: 'var(--arpia-shadow-pop)' },
      modal: { shadow: 'var(--arpia-shadow-overlay)' },
    },
  },
  components: {
    // Cards: EP 8px radius on the elevated surface with the editorial shadow.
    card: {
      root: {
        background: 'var(--arpia-dark-elevated)',
        borderRadius: 'var(--arpia-radius-lg)',
        shadow: 'var(--arpia-shadow-card)',
      },
    },
    // DataTable: EP table header (card surface, muted heading) + lavender
    // row hover on transparent rows.
    datatable: {
      header: {
        background: 'var(--arpia-card)',
        color: 'var(--arpia-text-muted)',
      },
      headerCell: {
        background: 'var(--arpia-card)',
        color: 'var(--arpia-text-muted)',
      },
      row: {
        background: 'transparent',
        hoverBackground: 'color-mix(in srgb, var(--arpia-primary-deep) 12%, transparent)',
      },
      colorScheme: {
        dark: {
          root: { borderColor: 'var(--arpia-border)' },
          bodyCell: { selectedBorderColor: 'var(--arpia-primary)' },
        },
      },
    },
    // Buttons: EP editorial weight (the Montserrat/uppercase signature is in
    // main.css — Aura has no fontFamily/textTransform tokens). Radius follows
    // the form-field token (var(--arpia-radius)).
    button: {
      root: { label: { fontWeight: '600' } },
    },
    // EP 4px density for dialogs, tags, toasts and inline messages.
    dialog: { root: { borderRadius: 'var(--arpia-radius)' } },
    tag: {
      root: { borderRadius: 'var(--arpia-radius)' },
      colorScheme: {
        dark: {
          primary: {
            background: 'color-mix(in srgb, var(--arpia-primary-deep) 13%, transparent)',
            color: 'var(--arpia-primary)',
          },
          success: {
            background: 'color-mix(in srgb, var(--arpia-success) 11%, transparent)',
            color: 'var(--arpia-success)',
          },
          info: {
            background: 'color-mix(in srgb, var(--arpia-info) 10%, transparent)',
            color: 'var(--arpia-info)',
          },
          warn: {
            background: 'color-mix(in srgb, var(--arpia-warning) 11%, transparent)',
            color: 'var(--arpia-warning)',
          },
          danger: {
            background: 'color-mix(in srgb, var(--arpia-danger) 11%, transparent)',
            color: 'var(--arpia-danger)',
          },
        },
      },
    },
    // Toast/Message: EP message look — light-N wash background, light-8
    // border, primary text (white-ish), no glow shadow.
    toast: {
      root: { borderRadius: 'var(--arpia-radius)' },
      colorScheme: {
        dark: {
          info: {
            background: 'color-mix(in srgb, var(--arpia-info) 10%, transparent)',
            borderColor: 'color-mix(in srgb, var(--arpia-info) 11%, transparent)',
            color: 'var(--arpia-text-primary)',
            detailColor: 'var(--arpia-text-primary)',
            shadow: 'none',
            closeButton: {
              hoverBackground: 'rgba(255, 255, 255, 0.05)',
              focusRing: { color: 'var(--arpia-info)', shadow: 'none' },
            },
          },
          success: {
            background: 'color-mix(in srgb, var(--arpia-success) 11%, transparent)',
            borderColor: 'color-mix(in srgb, var(--arpia-success) 13%, transparent)',
            color: 'var(--arpia-text-primary)',
            detailColor: 'var(--arpia-text-primary)',
            shadow: 'none',
            closeButton: {
              hoverBackground: 'rgba(255, 255, 255, 0.05)',
              focusRing: { color: 'var(--arpia-success)', shadow: 'none' },
            },
          },
          warn: {
            background: 'color-mix(in srgb, var(--arpia-warning) 11%, transparent)',
            borderColor: 'color-mix(in srgb, var(--arpia-warning) 13%, transparent)',
            color: 'var(--arpia-text-primary)',
            detailColor: 'var(--arpia-text-primary)',
            shadow: 'none',
            closeButton: {
              hoverBackground: 'rgba(255, 255, 255, 0.05)',
              focusRing: { color: 'var(--arpia-warning)', shadow: 'none' },
            },
          },
          error: {
            background: 'color-mix(in srgb, var(--arpia-danger) 11%, transparent)',
            borderColor: 'color-mix(in srgb, var(--arpia-danger) 13%, transparent)',
            color: 'var(--arpia-text-primary)',
            detailColor: 'var(--arpia-text-primary)',
            shadow: 'none',
            closeButton: {
              hoverBackground: 'rgba(255, 255, 255, 0.05)',
              focusRing: { color: 'var(--arpia-danger)', shadow: 'none' },
            },
          },
        },
      },
    },
    message: {
      root: { borderRadius: 'var(--arpia-radius)' },
      colorScheme: {
        dark: {
          info: {
            background: 'color-mix(in srgb, var(--arpia-info) 10%, transparent)',
            borderColor: 'color-mix(in srgb, var(--arpia-info) 11%, transparent)',
            color: 'var(--arpia-info)',
            shadow: 'none',
            closeButton: {
              hoverBackground: 'rgba(255, 255, 255, 0.05)',
              focusRing: { color: 'var(--arpia-info)', shadow: 'none' },
            },
            outlined: { color: 'var(--arpia-info)', borderColor: 'var(--arpia-info)' },
            simple: { color: 'var(--arpia-info)' },
          },
          success: {
            background: 'color-mix(in srgb, var(--arpia-success) 11%, transparent)',
            borderColor: 'color-mix(in srgb, var(--arpia-success) 13%, transparent)',
            color: 'var(--arpia-success)',
            shadow: 'none',
            closeButton: {
              hoverBackground: 'rgba(255, 255, 255, 0.05)',
              focusRing: { color: 'var(--arpia-success)', shadow: 'none' },
            },
            outlined: { color: 'var(--arpia-success)', borderColor: 'var(--arpia-success)' },
            simple: { color: 'var(--arpia-success)' },
          },
          warn: {
            background: 'color-mix(in srgb, var(--arpia-warning) 11%, transparent)',
            borderColor: 'color-mix(in srgb, var(--arpia-warning) 13%, transparent)',
            color: 'var(--arpia-warning)',
            shadow: 'none',
            closeButton: {
              hoverBackground: 'rgba(255, 255, 255, 0.05)',
              focusRing: { color: 'var(--arpia-warning)', shadow: 'none' },
            },
            outlined: { color: 'var(--arpia-warning)', borderColor: 'var(--arpia-warning)' },
            simple: { color: 'var(--arpia-warning)' },
          },
          error: {
            background: 'color-mix(in srgb, var(--arpia-danger) 11%, transparent)',
            borderColor: 'color-mix(in srgb, var(--arpia-danger) 13%, transparent)',
            color: 'var(--arpia-danger)',
            shadow: 'none',
            closeButton: {
              hoverBackground: 'rgba(255, 255, 255, 0.05)',
              focusRing: { color: 'var(--arpia-danger)', shadow: 'none' },
            },
            outlined: { color: 'var(--arpia-danger)', borderColor: 'var(--arpia-danger)' },
            simple: { color: 'var(--arpia-danger)' },
          },
        },
      },
    },
    // Paginator sits directly under the table body — transparent surface.
    paginator: {
      root: { background: 'transparent' },
    },
  },
})