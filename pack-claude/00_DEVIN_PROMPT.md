# Prompt for Devin: Kaayal website upgrade (content, SEO, accessibility)

*Paste everything below the line into Devin. Attach the rest of this zip.*

---

You are upgrading the live Kaayal website (https://kaayal.glitchy.systems). Kaayal (കായൽ) is the company. **Paayal is Kaayal's AI voice assistant.** Kaayal is a Malayalam-first tourism service for Alappuzha, Kerala, reached by phone. The Research, Product Strategy and Marketing department (Claude) supplied the content and research in this pack. You are the engineering team.

## 1. Non-negotiable constraints

1. **Do not change the approved design system.** Fraunces (headlines), Satoshi (body), Noto Sans Malayalam (Malayalam). Palette: Deep Lagoon #123F3C, Teal #267A73, Warm Ivory #F7F5EE, Mist #D9E6DE, Sand #C68E55. "Backwater Editorial" style: single column, hairline rules, numbered steps, restrained contour/ripple detail. No heavy glassmorphism, no unnecessary gradients, no generic SaaS templates, no decorative AI imagery. Reuse the existing components and tokens; add pages by extending them.
2. **Do not invent content or claims.** Use only copy in this pack or already on the site. No statistics, prices, availability, ratings, testimonials, "first / only / best", or "verified / government approved" wording beyond the site's existing owner-stated process ("every listing is verified by the Kaayal owner before callers hear about it").
3. **Callbacks are PLANNED, not deployed.** Consent-based, availability-triggered callbacks must never read as a live service. See section 3 for what to do about the existing site wording.
4. **Do not build Phase 2 or unapproved features:** operator onboarding flows, fleets or packages, trip planning, dashboards, request-to-book, callback or lead forms that store personal data, WhatsApp automation, payments, Aadhaar eKYC, subscriptions, paid promotions, P2P or sync. Every such item is `BLOCKED_PENDING_OWNER_CLARIFICATION` (workbook tab `13_Devin_Backlog`).
5. **Phase 1 stays as is:** caller dials the provisioned Sarvam number, Sarvam hosted Voice Agent, protected FastAPI tool, OpenAI Responses API. Do not touch the voice backend in this task.
6. **Malayalam:** use only reviewed Malayalam. All Malayalam in this pack is DRAFT. Build the Malayalam templates and `hreflang` plumbing, but do not publish Malayalam pages until the owner confirms native review.
7. **Photography:** none is supplied. Do not use stock, OTA, operator, or AI-generated images. Leave clean, optional image slots (with alt text and a licence line field in the content file) and ship without photos.
8. **No data collection.** No forms that store names or numbers, no cookies or trackers added without owner approval. Call and WhatsApp links only.

## 2. Ask the owner BEFORE changing these (reply with questions, then wait)

- **Q16:** Is any of the request-and-callback flow described on the site live today? Until answered, do not edit the hero or the "How it works" step wording, and add no new claims.
- **Q02:** Are calls recorded or transcribed, and for how long? Until answered, publish no statement about recording. Use the FAQ placeholder `[OWNER DECISION NEEDED]` in staging only; keep it out of production.
- **Q03:** Who is the native Malayalam reviewer, and when is sign-off?
- **Analytics:** propose one cookieless, privacy-friendly tool (and its cost, in rupees) and wait for approval.

## 3. Tasks, in priority order

Work on a branch. Open a pull request with a preview URL. Do not merge or deploy to production without owner review.

**P0 - Wording safety (after Q16 is answered).**
- If callbacks are not live, change present-tense request wording to planned wording. Suggested line: "Callbacks are planned. With your consent, Paayal will be able to tell you when a boat frees up. The operator always confirms price and availability."
- Keep: "Nothing is booked until an operator says yes." and "Kaayal never confirms prices, availability, or bookings on its own; the operator always does."
- Use the brand relationship consistently: "Kaayal" for the company, "Paayal" only for the voice a caller hears.

**P0 - Guide page `/before-you-book` (English).** Title: "What to ask before you book an Alappuzha houseboat" (H1). Five numbered items, each one or two sentences:
1. Boat registration.
2. Kerala Tourism classification (Silver, Gold or Diamond) - link https://www.keralatourism.org/cls/houseboats/Houseboat.htm
3. What is included (meals, A/C hours, cruise timings).
4. Price basis (weekday or peak dates, taxes, cancellation).
5. Photos of the actual boat you will get.
Closing line: "Not sure? Ask Paayal. Call +91 79658 61153." Source note linking https://www.onmanorama.com/travel/travel-news/2026/01/21/kerala-houseboats-defy-guidelines.html . Verify every legal or safety wording against official pages before publishing; flag anything you cannot verify.

**P1 - Official-route page `/dtpc-houseboat-counter`.** Explain, in plain language, that the district tourism council (DTPC) runs a pre-paid houseboat counter and that Kerala Tourism's page lists an advance of Rs 2,500 (https://www.keralatourism.org/houseboat/). Add "Confirm current details with DTPC." Do not state timings or rates you cannot see on an official page.

**P1 - FAQ page `/faq`** with these answers only (EN): Can I book through Kaayal? Not yet; Kaayal answers questions and the operator confirms. Does Kaayal show prices? No; it explains what affects price. Is a boat available on my dates? Kaayal cannot check; confirm with the operator. Which languages? Malayalam and English, including a mix. Do I need an app? No. Is Kaayal government-approved or operator-verified? No; Kaayal is independent and does not rank boats. Recording question: placeholder only (Q02).

**P1 - SEO foundations.**
- One H1 per page; titles up to 60 characters, meta descriptions up to 155 (workbook tab `09_Website_Content`, rows `seo.*`); canonical tags; `sitemap.xml`; `robots.txt`.
- Structured data: `Organization` (name Kaayal; no invented address or rating) and `FAQPage` for approved FAQs only. No `Review` or `AggregateRating`.
- Keep the existing page title; set per-page titles for new pages.
- `hreflang` en/ml wired for future `/ml/` pages; do not publish ml pages yet.

**P2 - Experiments support (see `Kaayal_Marketing_Actions.md` section 2).** Make the three experiment pages measurable: stable URLs, clean headings, and call-button tap events once analytics is approved. Do not run A/B code or tracking before approval.

**P2 - Accessibility and performance.** WCAG 2.1 AA contrast (check Sand on Ivory before using it for text), 44 px tap targets, visible focus states, a "skip to content" link (keep), usable without JavaScript for text, Malayalam web font with `font-display: swap`, check conjunct rendering on Android and iOS, Lighthouse mobile performance and accessibility at 90 or above (report actual numbers).

## 4. Acceptance criteria

- [ ] No change to fonts, palette or component styling.
- [ ] No text claims a callback, listing or booking service is live unless the owner confirmed it.
- [ ] Every new factual statement traces to the pack or a cited official page; list the sources in the PR.
- [ ] No Malayalam published without owner confirmation.
- [ ] No forms, trackers, cookies, photos or Phase 2 features added.
- [ ] `sitemap.xml`, `robots.txt`, canonical, per-page title and meta present; structured data validates.
- [ ] Lighthouse results and any deviations reported in the PR.

## 5. How to report

Return: the PR link, preview URL, a short list of what changed, the open questions that blocked you, and any claim you were unable to verify. If anything in this prompt conflicts with the site, stop and ask the owner. Do not resolve conflicts by inventing content.

## 6. Pack contents

`01_Devin_Handoff.md` (priorities, Phase boundary), `02_Website_Content_SEO_Spec.md` (copy and SEO detail), `03_Marketing_Actions.md` (campaigns and experiments), `04_Research_Workbook.xlsx` (tabs `09_Website_Content`, `13_Devin_Backlog`, `14_Owner_Questions`, `10_Research_Sources`), `05_Design_Reference_Deck.pdf` (visual reference only). **Precedence:** where the older spec or handoff differs from this prompt or from the live site, the live site and this prompt win (each older file carries an update note).
