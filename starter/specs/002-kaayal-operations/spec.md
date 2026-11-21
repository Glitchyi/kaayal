> **SUPERSEDED — phase boundaries lifted.** Historical record only; the live backlog is `/STATUS.md`.

# Feature spec: Kaayal Phase 2 — Operator Catalog + Portal + Booking Requests

**Status:** DRAFT for owner review — implementation authorized for catalog slice only after owner sign-off.
**Agreed via owner Q&A on 2026-11-21.**

## Naming
- **Kaayal** = the product/service.
- **Paayal** = the voice agent persona (the name callers hear).

## Goal
Kaayal becomes a lightweight marketplace for Alappuzha boat operators: Paayal answers catalog questions from verified data and takes booking requests **by phone (customers only)**; operators manage their boats and confirm requests via a **browser portal** (WhatsApp integration deferred to a later slice); a public landing page lives on `kaayal.glitchy.systems`.

## Channel map (corrected by owner)
| Actor | Channel |
| --- | --- |
| Caller/customer | **Phone call only** (Paayal) |
| Boat operator | **Browser portal** now; **WhatsApp (openwa)** later |
| Owner/admin | Browser admin view |

## Functional requirements

### Catalog
- FR-01: Boat listings contain **basics only**: boat name, operator name, operator contact, capacity, embarkation point, photos. Trip details/policies optional later.
- FR-02: Every listing carries `verified_at` and `source` (owner-entered / operator-submitted / govt registry reference). Unverified listings are flagged, never presented as confirmed.
- FR-03: Catalog is Paayal's Q&A source alongside official govt sources (KTDC/DTPC). When data is absent or stale, Paayal says so honestly and offers to take a request — never invented price/availability.

### Operator portal (browser, primary interface)
- FR-04: Owner creates an operator account and shares a unique portal URL (no self-serve public signup in v1 — owner vets operators first).
- FR-05: Operator can add/edit their own boat listings; new/edited listings start `unverified` until owner marks verified.
- FR-06: Operator sees incoming booking requests for their boats and can **confirm** or **block** each request.
- FR-07: On confirm, the portal reveals the customer's name + callback number so the operator calls them directly. (Interim flow until WhatsApp exists — replaces the earlier "WhatsApp message to customer" idea; flag for owner if wrong.)
- FR-08: **No login in v1** (owner decision): the operator's unique unguessable URL IS the access — no password/OTP step. Upgrade path: WhatsApp OTP later.

### Booking requests (voice, customers only)
- FR-09: Paayal collects: name, callback number (with explicit spoken consent), preferred date, group size. Stored as a booking request tied to a boat/operator when identifiable.
- FR-10: Requests are **request → operator confirms → confirmed**. Paayal never confirms availability, price, or reservation itself.
- FR-11: Customers may change details (date/venue) via Paayal, which updates the request and notifies the operator in-portal.

### WhatsApp slice — DEFERRED (build after portal works)
- FR-12: (Later) Operators also onboard/notify/confirm via WhatsApp (openwa), behind a swappable adapter so it can become the official Business API.
- FR-13: (Later) Customer receives a WhatsApp message with the operator's number on confirm.
- FR-14: (Later) Periodic WhatsApp nudges ask operators to confirm listing accuracy; non-responsive → stale flag.

### Web presence
- FR-15: Landing page on `kaayal.glitchy.systems` explaining Kaayal, showing verified listings, directing to the phone line.
- FR-16: Routing: `/api/*` + `/health` → Phase 1 voice service; everything else → site/portal (same app, separate routes — simplest).

### Admin (owner view)
- FR-17: Owner-only view over the same datastore: manage operators, verify listings, see all requests.

## Non-goals — deferred to Phase 3+
- Customer-facing online booking on the website.
- Payments, commissions, subscriptions (free for now).
- Real-time availability calendars.
- Outbound voice calls (customer contact is operator-initiated).
- WhatsApp integration itself (its own slice).

## Privacy & consent
- PII now exists: customer name + phone number; operator contact details.
- Spoken consent on the call before collecting customer contact info; consent flag stored with the request.
- Retention rule needed: default proposal — request PII kept 90 days then anonymized; deletion on request.
- Operator numbers shared with customers only after operator confirms (interim: operator sees customer number on confirm).

## Risks
- Operator portal auth is minimal (token links) — acceptable for v1, upgrade before scale.
- Catalog staleness — `verified_at` flags + honest agent speech; WhatsApp nudges later.
- Scope creep — build thin slices in order; WhatsApp stays out until portal proves the flow.

## User story and acceptance
A caller asks "what houseboats run from Alappuzha?" → Paayal answers from verified catalog → caller leaves name/number/date with consent → request appears in the operator's portal → operator confirms → portal shows the customer's number → operator calls them back. Owner can verify listings and see everything.

## Definition of done
- Live demo: real call → request → portal notification → operator confirms → operator calls customer.
- Catalog in SQLite with `verified_at`/source fields.
- Landing page reachable on `kaayal.glitchy.systems` alongside the working voice API.
- Mocked tests cover request lifecycle, consent gating, and portal auth.
