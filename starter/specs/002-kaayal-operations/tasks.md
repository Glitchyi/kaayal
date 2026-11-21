# Phase 2 tasks

## Done (implemented + tested, 34/34 pytest passing)
- [x] T01 — SQLite datastore (SQLModel): `operators`, `boats`, `booking_requests` with `verified_at`/`source`/`status`/`public_id`/consent fields.
- [x] T02 — Catalog read API for Paayal (tool-token auth): `GET /api/catalog/boats`, `GET /api/catalog/boats/{id}` — verified+active only.
- [x] T03 — Voice request endpoint: `POST /api/voice/request` — consent gate, phone sanity check, unverified-boat rejection, `REQ-####-xxxx` IDs, boat-less → triage.
- [x] T04 — Operator portal: no-login unique URL `/portal/<token>`; add/remove boats (unverified until owner review); requests list; confirm/block; customer contact revealed only after confirm.
- [x] T05 — Admin view `/admin?t=<ADMIN_TOKEN>`: create operator → one-time portal link; verify boats; all requests incl. triage.
- [x] T06 — Landing page `/` on kaayal.glitchy.systems (verified listings + call-to-action).

## Next
- [ ] T07 — Owner: create first real operator via `/admin`, share portal URL, verify first real boat.
- [ ] T08 — Register new Sarvam API tools (`list_boats`, `get_boat`, `create_booking_request`) and update Paayal prompt (consent script) — see `docs/sarvam-dashboard-setup.md` §7.
- [ ] T09 — Live demo call: catalog question → request → portal confirm.
- [ ] T10 — WhatsApp adapter slice (openwa) — deferred per owner.
- [ ] T11 — Process supervision (app + cloudflared across reboots), git init + first commit.

No customer-facing online booking (Phase 3).