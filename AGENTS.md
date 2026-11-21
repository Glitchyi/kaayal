# AGENTS.md — Kaayal (കായൽ) workspace

The working app + product guardrails live in `starter/` — **read `starter/AGENTS.md` first**; its scope rules (no unapproved Phase 2 features, no secrets in code, honest reporting) still apply.

## Installed design skills (project scope, `.devin/skills/`)

| Skill | Source | Commit | Use for |
| --- | --- | --- | --- |
| `ui-ux-pro-max` | github.com/nextlevelbuilder/ui-ux-pro-max-skill | `f76d165` | Design-system research: palettes, typography, stack guidance (`data/*.csv`, `references/`) |
| `frontend-design` | github.com/anthropics/skills | `e4bb5d9` | Distinctive anti-generic visual direction |
| `web-design-guidelines` | github.com/vercel-labs/agent-skills | `5a37a63` | Accessibility/interaction review (`references/command.md`) |

These are invocable skills (`/ui-ux-pro-max`, `/frontend-design`, `/web-design-guidelines`) and plain reference files — **supporting input only**. The final authority is `starter/docs/design/KAAYAL_DESIGN_SYSTEM.md`.

## Design workflow (mandatory before/after any UI work)

Before implementing UI:
1. Read `starter/docs/design/KAAYAL_DESIGN_SYSTEM.md` + `COMPONENT_INVENTORY.md`.
2. Consult `ui-ux-pro-max` for layout/design-system guidance.
3. Apply `frontend-design` principles — no generic AI SaaS look.
4. Follow `web-design-guidelines` (`references/command.md`) for interaction/accessibility.
5. Reuse tokens/classes in `starter/app/ui.py`; never invent new ones ad hoc.

After implementing UI:
1. `cd starter && uv run pytest -q` — all green.
2. Reload the server and inspect the page in a real browser (desktop + ~375px mobile).
3. Check Malayalam rendering (Noto Sans Malayalam), contrast, keyboard nav, focus states, empty/loading states.
4. Run the list in `starter/docs/design/UI_REVIEW_CHECKLIST.md`.
5. Report remaining issues honestly — never declare polish unverified.

## Anti-slop (binding)
No generic gradients, glassmorphism, identical rounded card grids, glowing orbs, decorative motion, emoji icons, fake testimonials/inventory, or arbitrary colors/spacing. Identity = Backwater Editorial; see the design system doc.

## Scope gates (unchanged)
- Phase 1 telephony is live — do not break it (`POST /api/voice/reply`, `/health`).
- Phase 2 surfaces (portal/admin/landing/catalog/requests) are owner-approved scope.
- WhatsApp (openwa), payments, outbound calls, customer web booking = deferred; ask first.
