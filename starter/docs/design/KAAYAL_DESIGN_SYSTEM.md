# Kaayal Design System — Backwater Editorial

Status: **provisional** — pending final brand assets and Claude's design research.
Authority order: this spec > skills guidance > personal taste.

## Identity
An elegant Kerala travel service powered by modern voice tech — not an AI SaaS dashboard. Three expressions, one system:

| Expression | Surface | Feel |
| --- | --- | --- |
| Backwater Editorial | Landing, tourist-facing pages | Serif display type, generous whitespace, editorial rhythm |
| Lagoon Glass | Voice/conversation UI (future) | Calm, translucent, watery states |
| Coastal Utility | Operator portal, owner admin | Quiet tables, clear status, zero decoration |

## Tokens (implemented in `app/ui.py`)
| Token | Value | Use |
| --- | --- | --- |
| `--lagoon` | `#123F3C` | Headings, primary text accents, deep brand color |
| `--teal` | `#267A73` | Interactive: links, primary buttons, focus rings |
| `--ivory` | `#F7F5EE` | Page background |
| `--mist` | `#D9E6DE` | Borders, input fills, subtle surfaces |
| `--sand` | `#C68E55` | Accent: card spine, warning-adjacent badges |
| `--ink` | `#17302E` | Body text |
| `--line` | lagoon @ 18% alpha | Hairline rules, table borders |

Derived: `card` surface `#FDFCF9`; muted text `#4A6B66`; danger `#7A2E2E`/`#F3E3E1`.

## Typography
- **Display:** Fraunces (Google Fonts, optical size) — headings, brand wordmark
- **UI/body:** Satoshi (Fontshare CDN) — interface text, labels, buttons
- **Malayalam:** Noto Sans Malayalam (Google Fonts) — always in the stack, `lang="ml"` on Malayalam spans
- Fallback: `system-ui, -apple-system, sans-serif` / `Georgia, serif`
- Rules: `text-wrap: balance` on headings; max ~44rem content column (body text measure ~38rem); no all-caps labels; no single-word italic accents
- Section kickers (`.kick`): italic Fraunces, sentence case, warm `#8A5F33` (lightened sand on dark bands) — an editorial section marker, never a tracked-caps "eyebrow chip"

## Shape & motion
- Card radius `.25rem` with a **3px sand left spine** (Kaayal signature, not generic rounded rectangles)
- Buttons `.375rem` radius, flat teal fill (no gradients, no glow)
- Transitions: `background-color`/`border-color` only, `.15s ease`; `prefers-reduced-motion` zeroes all
- Motion budget: entrance/in-view reveals, one-shot SVG draw-ins, and scroll-linked parallax only — no infinite loops, no autoplay decoration, no orbs/glow/glassmorphism
- Tables scroll horizontally in `.tablewrap`; at ≤700px the `td.actions` column is `position: sticky` on the right edge so row actions never leave the viewport

## Status vocabulary (must match product states exactly)
- `pending` → sand/wait badge — an unconfirmed request, never shown as booked
- `confirmed` → teal/ok badge — operator confirmed
- `verified` → teal/ok badge — owner-verified listing
- `unverified`/`pending verification` → sand/wait
- `blocked`/`cancelled` → muted-red/bad
- Voice states (future Lagoon Glass): idle, connecting, listening, processing, speaking, interrupted, error, disconnected — each visually distinct

## Anti-slop rules (binding)
No generic gradients, no identical 3-col feature cards, no oversized rounded rectangles, no glassmorphism, no glowing orbs, no decorative icons/emojis, no fake testimonials or invented inventory, no random font pairings, no motion for decoration, no placeholder content presented as real data.

## Imagery
Authentic Kerala photography only when owner supplies licensed assets. Until then: text-first layout, no stock photos presented as real inventory.
