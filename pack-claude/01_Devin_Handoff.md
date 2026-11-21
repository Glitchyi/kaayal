> **UPDATE 21 Nov 2026 (read first).** Written before the live site (https://kaayal.glitchy.systems) was found. Where this document differs, the live site and `Kaayal_Marketing_Actions.md` win:
> - **Brand:** *Kaayal* is the company; *Paayal* is its AI voice assistant.
> - **Headline:** the site says "The backwaters, a phone call away." Our earlier tagline "Alappuzha, in your own language." is not on the site.
> - **Site facts [S67]:** a published phone number; Paayal answers in Malayalam or English; the operator, not Kaayal, confirms price, availability and booking.
> - **Callbacks** (consent-based, availability-triggered) are a **planned** capability, not deployed. Check the site's present-tense "request" wording.
> - **Retired:** "no fees, no commitment" operator messaging (not on the site) and "no website found / provisional tokens". Design system: Fraunces, Satoshi, Noto Sans Malayalam with the approved palette.
> - **Campaigns:** the three in `Kaayal_Marketing_Actions.md` supersede the eight listed in the earlier strategy.

> **Kaayal (കായൽ)** | Research, Product Strategy & Marketing | Research date: 2026-11-21
> Status: working draft for owner review. Research only; no live inventory, prices or availability.
> Evidence IDs like [S01] resolve to tab `10_Research_Sources` in `Kaayal_Market_Competitor_Research.xlsx`.

# Devin Handoff

## Do this now (Phase 1 website work)

1. Build the landing site per `Kaayal_Website_Content_SEO_Spec.md` (backlog B01-B04). Copy is verbatim from workbook tab `09_Website_Content`.
2. Prototype notice above the fold. Call button = `tel:` link to the demo number (owner supplies; Q01).
3. SEO metadata, schema and hreflang as specified. No review/rating schema.
4. Apply provisional brand tokens (Deep Lagoon #123F3C, Teal #267A73, Warm Ivory #F7F5EE, Mist #D9E6DE, Sand #C68E55). Tell us if a real design system exists.
5. Hold Malayalam pages until native review (B05).

## Do not do

- No listings, prices, availability, ratings, testimonials, booking or callback forms, dashboards, WhatsApp, payments, Aadhaar eKYC, subscriptions, promotions.
- No invented market data or claims. If a number is not in the workbook, ask us.
- No "first", "only", "best", "verified" or "instant booking" language.
- Do not state that calls are recorded or not recorded until Q02 is answered.

## Positioning in one paragraph

Kaayal is a Malayalam-first, English-ready voice assistant for Alappuzha visitors, reached by phone. It explains what to ask before booking a houseboat and answers place questions. It does not book, quote prices or check availability. Status: prototype.

## Phase 1 engineering notes (already under way; for consistency only)

- Flow: provisioned Sarvam number -> hosted voice agent -> protected FastAPI HTTPS tool -> OpenAI Responses API -> spoken reply. No database.
- Sarvam API tool: bearer/api-key/basic auth; max wait up to 30 s; allowlist Sarvam IPs if firewalled; response size limits not documented [S42].
- Kaayal supplies a tool; it does not replace Sarvam's hosted reasoning model.
- Caller number and transcript can be passed to the tool. Do not forward them to OpenAI until Q02 is decided [S42].
- Prompt guardrails (content, not code): never state a live price or availability; say what to ask an operator; recommend confirming with the operator or DTPC.
- Read live OpenAI and Sarvam docs when implementing; model names and limits change.

## Content hierarchy and metadata

See spec sections 1 and 3. Titles and meta descriptions are length-checked in the workbook (`en_char_count`).

## Imagery

Original contour artwork in the deck only. No licensed photos fetched. Use team photography or Kerala Tourism media with written permission (Q14).

## Open questions that block you

- **Q01** (Phase 1): Which phone number and Sarvam number model (provisioned vs own telephony) should the website show? *Default:* Use the provisioned demo number only, labelled 'prototype'.
- **Q02** (Phase 1): Will calls be recorded or transcribed, for how long, and who sees them? *Default:* No retention beyond the demo; do not send caller number to OpenAI.
- **Q03** (Phase 1): Who will review Malayalam copy? *Default:* Appoint one native reviewer; sign-off before publish.
- **Q05** (Phase 2): What is the minimum proof an operator must show to be listed (registration, survey, insurance, classification)? *Default:* Require a Kerala Tourism classification or equivalent document, checked by a human.
- **Q06** (Phase 2): Which sources are 'approved' for operator facts (DTPC list, Kerala Tourism, operator documents)? *Default:* Operator-supplied documents + human check against Kerala Tourism listing.
- **Q07** (Phase 2): May Kaayal ever state a price or availability, and if so, how is it labelled and refreshed? *Default:* No live prices; operator-approved 'indicative' tariffs with dates, only after approval.
- **Q08** (Phase 2): Who is liable if a caller books through a Kaayal introduction and the stay goes wrong? *Default:* Kaayal never takes payment or confirms bookings; operator is the contracting party; legal review first.
- **Q09** (Phase 2): Is Kaayal neutral (no ranking) or may operators pay for placement later? *Default:* Neutral. No ranking or paid placement in MVP.
- **Q10** (Phase 2): Do we collect names/numbers for callbacks, and under what consent notice? *Default:* Do not collect until a notice and retention policy exist.

## Evidence map (workbook tabs to backend ideas, Phase 2 only, not approved)

| Tab | IDs | Possible entity (later) |
|---|---|---|
| `04_Tourism_Operators` | O01-O09 | operator |
| `03_Houseboat_Pricing` | P01-P20 | published_tariff_example (dated, never live) |
| `11_Attractions_Experiences` | A01-A08, E01-E04 | place, experience |
| `10_Research_Sources` | S01-S66 | source (required on every fact) |
| `13_Devin_Backlog` | B01-B14 | work item |

Every fact shown to a caller in Phase 2 would need a source ID, a verified date and an owner-approved status. This is a design note, not a request to build.

## Contradictions to respect

- **Kerala DTV growth 2025:** Computed value from the same counts = 12.64%. Use 12.64%.
- **Alappuzha 2025 visits:** Unresolved (likely different counting basis). Deck uses the district table and says so in notes.
- **Sarvam language count:** Malayalam and English appear in both. Claim only Malayalam + English.
- **Sarvam telephony numbers:** Owner reports a provisioned number; confirm model (Q01).
- **Number of houseboats:** No reliable current count. Do not publish a fleet size.
- **State tourist count in S33:** Do not reuse S33's state figure; its Alappuzha ~6.5 lakh is also unverified.
- **Blue Lotus 1-bedroom tariff:** Show as 'published tariff varies'; not used in deck.
- **Boats N Beds price bands:** Treated as low-confidence; not used in deck.
- **Diamond 'first/only' claims:** Do not repeat exclusivity claims.