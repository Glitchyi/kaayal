# AGENTS.md — Kaayal (കായൽ), Devin CLI guardrails

Single integrated prototype — phase gates were lifted by the owner. Historical specs in `specs/001-*` and `specs/002-*` are kept for traceability but their phase boundaries are **superseded**; the live backlog is `STATUS.md` at the repo root.

## Scope

- Full prototype: inbound Paayal voice calls (Sarvam) → tool-authed FastAPI → OpenAI for free-form answers; verified boat catalog; booking *inquiries* (never confirmations); operator portal; owner admin; event-driven simulated callbacks; demo WhatsApp onboarding.
- Still out: payments, Aadhaar/eKYC, subscriptions, paid promotion, P2P, real outbound calls without owner approval.
- Sarvam owns the call and hosted conversation. OpenAI is invoked only through the `voice_reply` HTTP tool; never misrepresent it as replacing Sarvam's runtime. Catalog/booking/callback data never passes through a language model.
- Demo data must be clearly labeled (DEMO badge / `source` fields). Never present simulated inventory or the simulated outbound dialer as live telephony.
- Do not place real outbound calls, trigger paid services, or contact real operators/customers without explicit permission. The Sarvam outbound adapter stays a stub until the owner approves real calls.

## Security + correctness

- Never expose `OPENAI_API_KEY`, Sarvam credentials, admin/portal tokens, or raw DB contents in code, browser, logs, or git; `.env.example` has placeholders only. Portal tokens are stored SHA-256-hashed; raw tokens are shown to the owner exactly once.
- Tool endpoints keep validated payloads (extra fields forbidden), bounded input size, tight timeouts, and safe fallbacks. **DEMO DECISION (owner, 2026-11-22): tool-token auth is intentionally OFF** — `require_tool_auth` in `app/main.py` early-returns so `/api/*` endpoints answer with no `X-Kaayal-Tool-Token`. Do NOT re-enable it, do NOT write tests expecting 401/503 on tool endpoints; tests must assert the open demo behavior. Re-enable only on explicit owner request.
- Do not log raw phone numbers, transcripts, API keys, or tool secrets. Use public IDs (`REQ-…`, `CB-…`) and trace IDs.
- Customer PII is consent-gated, masked until operator confirmation, and anonymized after 90 days (`app/pii.py`). Callbacks honor opt-outs, IST calling hours, retry caps, and expiry — don't bypass these except via the documented `DEMO_IGNORE_CALL_WINDOW` flag.
- Respond in the caller's language, briefly. Never invent prices, operators, availability, or successful actions.

## Workflow

- Tests: `cd starter && .venv/bin/python -m pytest -q` — keep everything green.
- Wiki freshness guard: `.githooks/pre-commit` (enabled via `core.hooksPath=.githooks`) blocks commits that change routes/settings in `starter/app` without a `starter/docs/wiki` file staged. Bypass code-only commits with `SKIP_WIKI_CHECK=1 git commit ...`.
- New boat/operator state changes that affect availability must fire the callbacks engine (`fire_boat_available`, `fire_operator_reachable`).
- At each milestone report: what worked, actual evidence, what is untested, and the next manual action. No false success reports.
