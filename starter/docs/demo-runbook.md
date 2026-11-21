# Kaayal prototype — end-to-end demo runbook

Everything here runs without manual DB edits. Public base URL: `https://kaayal.glitchy.systems` (tunnel → `localhost:8000`).

## Prep (once)

1. `cd starter && .venv/bin/python -m uvicorn app.main:app --port 8000` + cloudflared tunnel running (see `docs/run-local-and-tunnel.md`).
2. Admin: `https://kaayal.glitchy.systems/admin?t=<ADMIN_TOKEN>` → **Demo data → Seed demo data**. This creates:
   - *Backwater Demo Cruises (DEMO)* — reachable; boat **Demo Shikara** (verified, available, ₹2,000/hour demo price)
   - *Monsoon Houseboats (DEMO)* — **unreachable**; boat **Demo Deluxe** (verified, **unavailable**)
3. Optional for off-hours demos: set `DEMO_IGNORE_CALL_WINDOW=true` in `.env` (otherwise callbacks only attempt 09:00–18:00 IST). Simulator outcome via `SIM_CALLBACK_OUTCOME=interested|not_interested|no_answer` (default `interested`).

## Scenario A — tourist journey (the full loop)

1. **Discover**: open `/boats` — see Demo Shikara (available) and Demo Deluxe (unavailable) with DEMO badges.
2. **Inquire via web** (`/inquire`) or via Paayal on a call: pick **Demo Deluxe**.
3. Boat is unavailable → the flow offers a **callback**. Give consent → `CB-…` row queued (admin → Callbacks shows it, parked).
4. **Operator fixes availability**: log into the Monsoon portal (link from admin → Reissue/Approve) → toggle Demo Deluxe to **available**. This fires `fire_boat_available` → callback requeued (`trigger_seq` bumps).
5. **Engine runs**: during 09:00–18:00 IST the background tick attempts the call automatically — or hit **Run due callbacks** in admin for an immediate simulated attempt.
6. Simulator "calls" the customer: Paayal introduces herself, references the inquiry, asks if still interested → outcome `interested` → a **booking inquiry is auto-created** (`REQ-…`, source=`callback`, status `pending`).
7. **Operator confirms**: Monsoon portal shows the inquiry → Confirm → customer contact revealed → call/WhatsApp (wa.me link). Admin dashboard shows the full trail: callback → attempt (outcome, transcript) → booking request → confirmed.

## Scenario B — operator unreachable

1. Monsoon Houseboats is `unreachable` by default in the seed.
2. Inquire about Demo Deluxe → response `unreachable` → consent to callback (`reason=operator_unreachable`).
3. In the operator portal, flip **I'm reachable** ON → `fire_operator_reachable` → callback requeued → engine runs → same conversion flow.

## Scenario C — WhatsApp onboarding (demo)

1. `cd starter/wa-bot && npm start` → pair the +91 9400354625 phone via QR (see `docs/wa-demo.md`).
2. DM that number → bot walks name → boat → replies **pending verification**.
3. Admin → the new operator appears as **pending approval** → Approve → portal link shown once → send it back over WhatsApp (admin row has a wa.me shortcut).
4. Without WhatsApp: same flow at `/join` on the site.

## Scenario D — opt-outs and safety

- Caller says "don't call me" → `create_callback_request` with `consent_given=false` → all active callbacks for that number → `opted_out` (admin can also cancel).
- Retries: max 2 attempts per trigger, ≥61 min apart; `no_answer` is terminal per trigger.
- Expiry: 7 days, or before the travel date when a parseable date was given.
- PII: customer name/phone anonymized after 90 days (`scripts/anonymize_pii.py`).

## What's real vs simulated

| Real | Simulated |
| --- | --- |
| FastAPI app, SQLite, tunnel URL, Sarvam inbound number + tools | Outbound calls (SimulatedProvider — transcripts, no dialing) |
| Operator portal, admin, catalog, inquiries, callback engine logic | WhatsApp onboarding (open-wa, unofficial) |
| OpenAI answers via `voice_reply` | DEMO-seeded operators/boats |
