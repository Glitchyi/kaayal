# Kaayal — status (updated 2026-11-21)

## Live
- `https://kaayal.glitchy.systems` — FastAPI via Cloudflare named tunnel `kaayal` (ID `9af85681-71d7-4370-a455-11f14d293d1b`) → `localhost:8000`
- Phase 1 done: `/health`, `POST /api/voice/reply` (OpenAI behind it), verified live incl. real OpenAI call
- Phase 2 core done: SQLite (operators/boats/requests), `/api/catalog/boats[/{id}]`, `POST /api/voice/request`, `/portal/<token>`, `/admin?t=<ADMIN_TOKEN>`, landing `/`
- Tests: 34/34 pass (`cd starter && pytest`)
- Design: tokens in `app/ui.py`; docs in `starter/docs/design/`; skills in `.devin/skills/` (ui-ux-pro-max, frontend-design, web-design-guidelines); workflow rules in root `AGENTS.md`
- Env: `starter/.env` (gitignored). Must have OPENAI_API_KEY, SARVAM_TOOL_SHARED_SECRET, ADMIN_TOKEN; set KAAYAL_PHONE_NUMBER for call CTA; ensure KAAYAL_PUBLIC_BASE_URL=https://kaayal.glitchy.systems
- Processes: uvicorn + cloudflared run as unsupervised background processes — die on reboot/logout

## Pending — USER (blocking the live product)
1. Sarvam dashboard → `starter/docs/sarvam-dashboard-setup.md`: create tools `list_boats`, `get_boat`, `create_booking_request` (voice_reply already done), paste Paayal checklist prompt (§3), test each tool
2. `/admin?t=<ADMIN_TOKEN>` → create operator → share portal link → verify their boat
3. Live calls in Malayalam + English: general Q, boat Q, test request → confirm in portal

## Done since last update
- Git initialized, 2 commits on `main` (latest `57e8706`)
- PII 90-day anonymization (`app/pii.py` startup sweep + `scripts/anonymize_pii.py`)
- Operator token reissue + deactivate/reactivate in /admin
- Portal wa.me "WhatsApp customer" links on confirmed requests only
- Landing: `Call +91 7965861153` CTA top + separate `WhatsApp +91 9400354625` operator CTA bottom (KAAYAL_PHONE_NUMBER / KAAYAL_WHATSAPP_NUMBER in .env)

## Pending — DEVIN (say go)
4. Process supervision: launchd for uvicorn + `sudo cloudflared service install`
5. Optional: deeper editorial pass on landing page

## Deferred (explicit)
- WhatsApp Business API adapter (full automation — needs Meta credentials; deep links done instead)
- No payments, Aadhaar/eKYC, paid promotion, subscriptions, P2P

## Key docs
- Sarvam portal steps: `starter/docs/sarvam-dashboard-setup.md`
- Sarvam vs OpenAI roles: `starter/docs/how-sarvam-and-openai-fit.md`
- Operator onboarding: `starter/docs/operator-onboarding.md`
- Specs: `starter/specs/001-kaayal-telephony/`, `starter/specs/002-kaayal-operations/`
