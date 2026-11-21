# Kaayal docs — index

Start at the **HTML wiki** for a guided tour of how the system works:

- `wiki/index.html` — open in a browser (or `python3 -m http.server` inside `wiki/`).

Everything below is the canonical Markdown source the wiki links back to. Paths
are referenced from `AGENTS.md`, `STATUS.md` and `specs/` — do not rename files
without updating those references.

## Concepts

- `how-sarvam-and-openai-fit.md` — who does what: Sarvam-hosted Paayal vs the
  FastAPI tool backend vs OpenAI. The short version of the architecture.

## Runbooks

- `run-local-and-tunnel.md` — `uv sync`, `.env`, run uvicorn, expose a public
  HTTPS tunnel, smoke test.
- `sarvam-dashboard-setup.md` — exact Sarvam dashboard steps: the five API
  tools, the Paayal prompt, inbound deployment, verification.
- `operator-onboarding.md` — owner steps to onboard an operator: admin → portal
  link → verify boats → requests.
- `demo-runbook.md` — end-to-end demo script: seed demo data, tourist/callback/
  opt-out scenarios, what's real vs simulated.
- `wa-demo.md` — WhatsApp operator-onboarding demo via the open-wa sidecar
  (unofficial API — demo only).

## Design

- `design/KAAYAL_DESIGN_SYSTEM.md` — **the design authority.** Backwater
  Editorial tokens, type, expressions.
- `design/BRAND_GUIDELINES.md` — brand voice and usage.
- `design/COMPONENT_INVENTORY.md` — implemented components and their classes.
- `design/UI_REVIEW_CHECKLIST.md` — the post-UI-work review list.

## Governance / decisions

- `REVIEW_DECISIONS.md` — settled owner decisions and pre-live-call checks.
- `PHASE2_CLARIFICATIONS.md` — questions that must be answered before any
  Phase 2 expansion. Blocked until owner approval.
