# Kaayal — status (updated 2026-11-21)

## Live
- `https://kaayal.glitchy.systems` — FastAPI via Cloudflare named tunnel `kaayal` (ID `9af85681-71d7-4370-a455-11f14d293d1b`) → `localhost:8000`
- Public repo: https://github.com/Glitchyi/kaayal (SSH `git@github.com:Glitchyi/kaayal.git`)
- Integrated prototype: voice tools (Sarvam → `voice_reply`/catalog/request/callback), SQLite catalog + portal + admin, event-driven callback engine (simulated dialer), WhatsApp demo onboarding (open-wa sidecar)
- Public site: `/` `/boats` `/paayal` `/explore` `/before-you-book` `/dtpc-houseboat-counter` `/faq` + `robots.txt` `sitemap.xml`. `/inquire` and `/join` were **removed** (no data-storing public forms — inquiries voice-only, onboarding WhatsApp/admin-only)
- Tests: 113 pass (`cd starter && .venv/bin/python -m pytest -q`)
- Lighthouse (mobile, home): perf 97, a11y 95
- Env: `starter/.env` (gitignored): OPENAI_API_KEY, SARVAM_TOOL_SHARED_SECRET, ADMIN_TOKEN, KAAYAL_PHONE_NUMBER (+91 7965861153), KAAYAL_WHATSAPP_NUMBER (+91 9400354625), KAAYAL_PUBLIC_BASE_URL
- Processes: uvicorn + cloudflared run unsupervised — die on reboot/logout. wa-bot needs `npm start` + paired phone

## Pending — USER (blocking the live product)
1. Sarvam dashboard → `starter/docs/sarvam-dashboard-setup.md`: register all 5 tools (incl. `create_callback_request`), paste Paayal checklist prompt, test each
2. `/admin?t=<ADMIN_TOKEN>` → approve/verify operators + boats
3. Live inbound calls in Malayalam + English (general Q, availability Q, inquiry, callback consent)
4. wa-bot: `cd starter/wa-bot && npm start` + QR scan on the 9400354625 phone
5. Answer Claude-pack questions: Q02 call recording/retention policy; Q03 Malayalam native reviewer; analytics tool choice (cookieless proposal needed — e.g. Plausible ≈₹800/mo or self-hosted Umami free)

## Done since last update
- Website upgrade per Claude pack: 3 new content pages, SEO (canonical/hreflang/JSON-LD/sitemap/robots), 44px tap targets, honest-split wording (inquiries live, callback dialer simulated), /inquire + /join removed
- Public repo created + pushed (commit `d742b2a` onward)
- Full callback engine: durable queue, IST window, retries, expiry, opt-outs, triggers, simulator (`SIM_CALLBACK_OUTCOME`)
- Portal: reachability/availability/price/amenities; admin: approvals, callback monitor, demo seed/clear
- PII 90-day anonymization; portal token reissue; operator deactivate/reactivate

## Deferred (explicit)
- Real outbound Sarvam calls (adapter stub ready — owner approval + charges required)
- WhatsApp Business API adapter (open-wa is demo-only; migration path in `docs/wa-demo.md`)
- Malayalam pages (`/ml/`) — hreflang plumbing ready, DRAFT copy pending native review
- No payments, Aadhaar/eKYC, paid promotion, subscriptions, P2P

## Key docs
- Demo walkthrough: `starter/docs/demo-runbook.md`
- Claude content pack: `pack-claude/` (Phase-1-era; live truth wins where they differ)
- Sarvam portal steps: `starter/docs/sarvam-dashboard-setup.md`
- Wiki: `starter/docs/wiki/index.html` · Specs (superseded phases): `starter/specs/`
