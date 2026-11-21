# AGENTS.md — Kaayal (കായൽ) workspace

The working app + product guardrails live in `starter/` — **read `starter/AGENTS.md` first**. Phase gates were lifted by the owner: the goal is one integrated prototype (voice, catalog, inquiries, portal, admin, simulated callbacks, demo WhatsApp onboarding). `STATUS.md` is the live backlog.

## Installed design skills (project scope, `.devin/skills/`)

| Skill | Source | Commit | Use for |
| --- | --- | --- | --- |
| `ui-ux-pro-max` | github.com/nextlevelbuilder/ui-ux-pro-max-skill | `f76d165` | Design-system research: palettes, typography, stack guidance (`data/*.csv`, `references/`) |
| `frontend-design` | github.com/anthropics/skills | `e4bb5d9` | Distinctive anti-generic visual direction |
| `web-design-guidelines` | github.com/vercel-labs/agent-skills | `5a37a63` | Accessibility/interaction review (`references/command.md`) |
| `codebase-design` | github.com/mattpocock/skills | `abeeaf9` | Deep-module vocabulary (module, interface, depth, seam, adapter) for code design/restructuring |
| `improve-codebase-architecture` | github.com/mattpocock/skills | `abeeaf9` | User-invoked architecture survey: finds deepening candidates, renders HTML report, grills chosen candidate |
| `grilling` | github.com/mattpocock/skills | `abeeaf9` | Companion to improve-codebase-architecture: stress-tests a chosen refactor decision |
| `domain-modeling` | github.com/mattpocock/skills | `abeeaf9` | Companion to improve-codebase-architecture: maintains `GLOSSARY.md` / ADRs |

These are invocable skills (`/ui-ux-pro-max`, `/frontend-design`, `/web-design-guidelines`, `/codebase-design`, `/improve-codebase-architecture`, `/grilling`, `/domain-modeling`) and plain reference files — **supporting input only**. The final authority is `starter/docs/design/KAAYAL_DESIGN_SYSTEM.md`.

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

## Scope gates (updated — phase gates lifted)
- Do not break the live voice path (`POST /api/voice/reply`, `/health`) or existing portal/admin flows.
- Still excluded without owner approval: real outbound calls/charges, real operator/customer contact, payments, eKYC, external credentials, production deploy changes, destructive ops.
- WhatsApp onboarding stays the open-wa demo path; Business API migration is documented in `starter/docs/wa-demo.md`.
