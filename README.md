# Kaayal (കായൽ)

Malayalam-first, voice-first tourism assistant for Alappuzha. **Paayal** — Kaayal's AI voice assistant — answers calls on a Sarvam-hosted number, describes verified boat operators, takes consented booking *inquiries* (never confirmations), and calls customers back when operators or boats become available.

**Live prototype:** `https://kaayal.glitchy.systems` (Cloudflare tunnel → local FastAPI). `STATUS.md` tracks what's live and pending.

## Architecture

```
Caller → Sarvam number → Paayal (Sarvam voice agent: STT→LLM→TTS)
   ├─ tool:voice_reply        → FastAPI → OpenAI Responses API (free-form answers only)
   ├─ tool:list_boats/get_boat → FastAPI → SQLite (verified catalog)
   ├─ tool:create_booking_request → FastAPI → inquiry row → operator portal
   └─ tool:create_callback_request → FastAPI → callback queue → event engine
        → outbound provider (simulator today; Sarvam adapter stubbed, off by default)
```

- `starter/app/` — FastAPI + SQLModel/SQLite: catalog, requests, callbacks engine, portal, admin, site, wa-onboard, pii
- `starter/wa-bot/` — open-wa WhatsApp onboarding demo (unofficial, demo only)
- `starter/docs/` — Sarvam setup, demo runbook, operator onboarding, design system
- `starter/specs/` — historical phase specs (superseded; kept for traceability)
- `.devin/skills/` — UI/design skills; `AGENTS.md` files carry the working rules

## Run

```bash
cd starter && uv sync          # or .venv exists already
.venv/bin/python -m pytest -q  # tests
.venv/bin/python -m uvicorn app.main:app --port 8000
```

Env in `starter/.env` (never committed — see `.env.example`): OpenAI key, `SARVAM_TOOL_SHARED_SECRET`, `ADMIN_TOKEN`, `KAAYAL_PUBLIC_BASE_URL`, phone/WhatsApp numbers, callback engine flags.

## Demonstrate

`starter/docs/demo-runbook.md` — seed demo data from `/admin`, then walk the full tourist→callback→operator journey.

**Honesty rules:** booking requests are inquiries confirmed by the operator by phone; demo data is labeled DEMO; the outbound dialer is simulated; WhatsApp onboarding is an unofficial-API demo. No payments, eKYC, or real outbound calls without owner approval.
