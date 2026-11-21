# Technical plan — Phase 2 (DRAFT, for owner review)

## Architecture

```
Caller ──Sarvam──> Paayal ──HTTPS tool──> FastAPI ──> OpenAI (Q&A + request intake)
                                            │
                                     SQLite (operators, boats, requests)
                                            │
Operator ──browser portal──> same FastAPI (token auth)
Owner    ──admin view──────> same FastAPI

kaayal.glitchy.systems ──/api,/health──> voice tool routes (Phase 1)
                      └── everything else ──> landing + portal + admin

(later) WhatsApp adapter (openwa sidecar) ──> notify/confirm for operators + customers
```

## Decisions made (owner Q&A, 2026-11-21)
- SQLite datastore.
- Operators use **browser portal** now; openwa WhatsApp slice comes later.
- Calls are **customers only**; operators never use the phone line.
- Interim customer contact: operator sees customer name/number on confirm → calls them directly.
- Booking = request → operator confirms → confirmed. Free for now, no payments.

## Slices (build order)
1. **Datastore + catalog** — SQLite via SQLModel/SQLAlchemy; `operators`, `boats`, `booking_requests` tables; `verified_at`, `source`, `status` fields; migration via simple `create_all` for v1.
2. **Catalog read API** — internal endpoints the voice tool calls: `GET /api/catalog/boats` (verified only), `GET /api/catalog/boats/{id}`.
3. **Voice tools v2** — new authenticated tool endpoints for Paayal: `search_boats`, `get_boat`, `create_booking_request` (consent flag required); Sarvam tool wiring documented.
4. **Operator portal** — no login step; unique unguessable URL `/portal/<token>` per operator (URL = access, owner decision); boats CRUD (own only), request list, confirm/block actions; customer contact revealed only post-confirm. WhatsApp OTP upgrade later.
5. **Admin view** — owner token (env `ADMIN_TOKEN`); operator create/token-issue, verify listings, all requests.
6. **Landing page** — server-rendered minimal page listing verified boats + phone number.
7. **WhatsApp adapter (deferred)** — `send(to,text)`/`on_reply` interface; openwa Node sidecar later; mock in tests.

## Data model (draft)
- `operators`: id, name, phone, token_hash, created_at, active
- `boats`: id, operator_id, name, capacity, embarkation_point, photo_urls(json), source, verified_at(nullable), active, created_at, updated_at
- `booking_requests`: id, boat_id(nullable→operator broadcast if general), customer_name, customer_phone, consent_given(bool), preferred_date, group_size, status(pending/confirmed/blocked/cancelled), notes, created_at, updated_at

## Open questions for plan review
1. ~~Operator login UX~~ — decided by owner: no auth step, unique URL per operator; WhatsApp OTP later.
2. Boat-less requests (caller doesn't pick a boat): broadcast to all operators or owner triage? Default: owner triage queue.
3. Non-WhatsApp interim — is operator-calls-customer acceptable to you? (spec FR-07)
4. Photo uploads v1: URL paste (simplest) vs. file upload? Default: URL paste.
5. Request ID format for operator replies: `REQ-0007`.

## Verification
- Unit tests: models, consent gating, portal auth scoping, confirm/block transitions.
- Integration: simulated Paayal tool call → request in operator portal → confirm → contact reveal.
- Live: real call once Sarvam tools are re-wired to the v2 endpoints.
