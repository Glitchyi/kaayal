# Kaayal UI Review Checklist

Run this after ANY UI change, before reporting done. Skills are references; `docs/design/KAAYAL_DESIGN_SYSTEM.md` is the authority.

## Design-system conformance
- [ ] Only tokens/classes from `app/ui.py` — no inline hex outside the token set, no new fonts/shadows/gradients
- [ ] Card = sand spine + `.25rem` radius; buttons flat teal; no glassmorphism/orbs/gradients
- [ ] Status vocabulary matches spec exactly (pending ≠ confirmed visually)
- [ ] No placeholder/fake inventory, testimonials, or invented data

## Vercel Web Interface Guidelines (`.devin/skills/web-design-guidelines`)
- [ ] Every `<input>` has a `<label for>`; `autocomplete`/`inputmode`/`type` correct
- [ ] `<button>` for actions, `<a>` for navigation; no div-onclick
- [ ] `:focus-visible` styles everywhere; no `outline:none` without replacement
- [ ] `prefers-reduced-motion` honored; no `transition: all`
- [ ] `…` not `...`; placeholders end with `…` and show examples
- [ ] Images: `alt` + explicit `width`/`height`; below-fold `loading="lazy"`
- [ ] Empty states render helpfully; long text truncates safely
- [ ] `touch-action: manipulation` on inputs/buttons; tap targets ≥ ~40px
- [ ] Semantic HTML first (`<main>`, `<table>`, `<thead>`), skip-link present
- [ ] Destructive actions need confirmation or undo path (boats: soft-delete OK; block is reversible by re-request)

## Kaayal-specific
- [ ] Malayalam renders in Noto Sans Malayalam — check a real `lang="ml"` string (കായൽ), not just fallback
- [ ] Contrast: teal on ivory ≥ 4.5:1 for text; badge text vs. badge bg
- [ ] Mobile (375px): no horizontal scroll, tables readable, forms usable
- [ ] Keyboard: tab through dashboard reaches all controls; Enter activates
- [ ] Customer phone NOT visible on unconfirmed request cards (PII gate — tested)
- [ ] No secrets/tokens/phone numbers in page source beyond what's intended

## Process
1. `uv run pytest -q` — all green
2. Reload running server; inspect `/`, `/portal/<token>`, `/admin?t=…` in a real browser
3. Desktop + mobile screenshots for the record
4. Report remaining issues honestly — don't declare polished without verification
