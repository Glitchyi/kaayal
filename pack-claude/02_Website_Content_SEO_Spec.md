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

# Kaayal Website Content & SEO Specification (for Devin)

**Authoritative copy lives in `Kaayal_Market_Competitor_Research.xlsx`, tab `09_Website_Content`. This document mirrors it; if they differ, the workbook wins and this file is regenerated.**

## 0. Rules

1. Phase 1 only. No listings, no booking forms, no prices, no availability, no ratings, no testimonials.
2. Use copy verbatim. Do not invent statistics, claims or imagery.
3. Malayalam is DRAFT until a native reviewer signs off (backlog B05). Do not publish Malayalam pages before then.
4. The prototype notice must appear above the fold on Home.
5. Anything marked OWNER DECISION stays a visible placeholder in staging and out of production.

## 1. Sitemap and content hierarchy

| Priority | Page | Purpose | Primary CTA |
|---|---|---|---|
| P0 | Home | What Kaayal is; call the demo line | Call the Kaayal demo line |
| P0 | How it works | 4 steps; what Kaayal can and cannot do | Call |
| P0 | FAQ | Honest answers | Call |
| P1 | Houseboat guide: what to ask before you book | SEO + trust | Call |
| P1 | Official route (DTPC) explainer | Trust | Call |
| P1 | For operators | Listening, no fees, no commitment | Email us |
| P2 | Contact | mailto + phone | Email |

**Home section order:** Hero (headline, subheadline, prototype notice, call button) -> 3 value points -> How it works (4 steps) -> "What Kaayal does not do" strip -> Houseboat experiences (3 short blocks) -> FAQ preview -> Operators strip -> Footer.

## 2. Copy

**`home.headline`** (Home / hero)
- EN: Alappuzha, in your own language.
- ML (DRAFT, needs native review): ആലപ്പുഴ, നിങ്ങളുടെ ഭാഷയിൽ.
- Note: H1. Brand line used on slide 1 and slide 12.

**`home.subheadline`** (Home / hero)
- EN: Call Kaayal and ask about backwater cruises and places in Alappuzha - in Malayalam or English.
- ML (DRAFT, needs native review): കായലിനെ വിളിച്ച് ആലപ്പുഴയിലെ കായൽ യാത്രകളെയും കാഴ്ചകളെയും കുറിച്ച് മലയാളത്തിലോ ഇംഗ്ലീഷിലോ ചോദിക്കാം.
- Note: Max 2 lines.

**`home.prototype_notice`** (Home / hero)
- EN: Prototype. Kaayal answers questions. It does not take bookings or quote live prices.
- ML (DRAFT, needs native review): ഇത് ഒരു പരീക്ഷണ പതിപ്പാണ്. കായൽ ചോദ്യങ്ങൾക്ക് ഉത്തരം നൽകും. ബുക്കിംഗോ തത്സമയ നിരക്കോ ഇപ്പോൾ ഇല്ല.
- Note: MUST appear above the fold. Do not remove.

**`home.value_prop_1`** (Home / value proposition)
- EN: Speaks your language. Ask in Malayalam, English, or a mix.
- ML (DRAFT, needs native review): നിങ്ങളുടെ ഭാഷയിൽ സംസാരിക്കാം. മലയാളത്തിലോ ഇംഗ്ലീഷിലോ കലർത്തിയോ ചോദിക്കാം.
- Note: Code-mixed speech is supported by the voice platform (S41).

**`home.value_prop_2`** (Home / value proposition)
- EN: Straight answers. We explain what to ask before you book, and we never invent prices or availability.
- ML (DRAFT, needs native review): വ്യക്തമായ ഉത്തരം. ബുക്ക് ചെയ്യുംമുൻപ് എന്ത് ചോദിക്കണമെന്ന് പറയാം. നിരക്കോ ലഭ്യതയോ ഞങ്ങൾ ഊഹിച്ച് പറയില്ല.
- Note: Core trust message.

**`home.value_prop_3`** (Home / value proposition)
- EN: Just a phone call. No app to install.
- ML (DRAFT, needs native review): ഒരു ഫോൺ കോൾ മതി. ആപ്പ് വേണ്ട.
- Note: Matches Phase 1 channel.

**`home.cta_primary`** (Home / CTA)
- EN: Call the Kaayal demo line
- ML (DRAFT, needs native review): കായൽ ഡെമോ ലൈനിലേക്ക് വിളിക്കൂ
- Note: Phone number: [OWNER TO SUPPLY - the provisioned Sarvam number]. Use tel: link.

**`home.cta_secondary`** (Home / CTA)
- EN: Ask us a question
- ML (DRAFT, needs native review): ഞങ്ങളോട് ചോദിക്കൂ
- Note: Phase 1 safe version: mailto link only. A form that stores names/numbers needs owner approval and a DPDP-aligned notice (see 14_Owner_Questions).

**`how.title`** (How it works)
- EN: How Kaayal works
- ML (DRAFT, needs native review): കായൽ എങ്ങനെ പ്രവർത്തിക്കുന്നു
- Note: H2.

**`how.step1`** (How it works)
- EN: 1. Call the demo line.
- ML (DRAFT, needs native review): 1. ഡെമോ ലൈനിലേക്ക് വിളിക്കൂ.

**`how.step2`** (How it works)
- EN: 2. Ask in Malayalam or English: what to check on a houseboat, which cruise type fits, what Alappuzha offers.
- ML (DRAFT, needs native review): 2. മലയാളത്തിലോ ഇംഗ്ലീഷിലോ ചോദിക്കൂ: ഹൗസ്ബോട്ടിൽ എന്തൊക്കെ പരിശോധിക്കണം, ഏത് യാത്ര അനുയോജ്യം, ആലപ്പുഴയിൽ എന്തൊക്കെ കാണാം.

**`how.step3`** (How it works)
- EN: 3. Hear a spoken answer in the same language.
- ML (DRAFT, needs native review): 3. അതേ ഭാഷയിൽ ഉത്തരം കേൾക്കൂ.

**`how.step4`** (How it works)
- EN: 4. Confirm details and prices directly with the operator before you pay.
- ML (DRAFT, needs native review): 4. പണം നൽകുംമുൻപ് വിവരങ്ങളും നിരക്കും ഓപ്പറേറ്ററോട് നേരിട്ട് ഉറപ്പാക്കൂ.
- Note: Honesty line; keep.

**`voice.intro`** (Voice assistant intro (spoken greeting - for Phase 1 agent prompt, owner to approve))
- EN: Namaskaram, this is Kaayal. I can help you with questions about backwater cruises and places in Alappuzha, in Malayalam or English. I cannot book a boat or give live prices. How can I help?
- ML (DRAFT, needs native review): നമസ്കാരം, ഇത് കായൽ ആണ്. ആലപ്പുഴയിലെ കായൽ യാത്രകളെയും സ്ഥലങ്ങളെയും കുറിച്ച് മലയാളത്തിലോ ഇംഗ്ലീഷിലോ എനിക്ക് സഹായിക്കാം. ബോട്ട് ബുക്ക് ചെയ്യാനോ തത്സമയ നിരക്ക് പറയാനോ എനിക്ക് കഴിയില്ല. എങ്ങനെ സഹായിക്കണം?
- Note: Greeting is part of the voice agent configuration (Phase 1 engineering), listed here for brand consistency. Recording/consent line to be added per owner decision.

**`exp.overnight`** (Houseboat experience descriptions)
- EN: Overnight houseboat cruise: operators typically offer a private boat with meals, a daytime cruise on the backwaters, and a night moored on the lake. Timings, inclusions and A/C hours differ by operator. One operator publishes check-in at 11:30 am and check-out at 9:00 am.
- ML (DRAFT, needs native review): രാത്രി താമസം ഉൾപ്പെടെയുള്ള ഹൗസ്ബോട്ട് യാത്ര: സാധാരണയായി ഭക്ഷണം ഉൾപ്പെടുന്ന സ്വകാര്യ ബോട്ടിൽ പകൽ കായൽ യാത്രയും രാത്രി കായലിൽ നങ്കൂരമിട്ടുള്ള താമസവും. സമയവും സൗകര്യങ്ങളും എ.സി. സമയവും ഓപ്പറേറ്റർ അനുസരിച്ച് മാറും.
- Note: Facts: S13 (operator timings), S54 (DTPC packages). No prices. Native review required.

**`exp.day`** (Houseboat experience descriptions)
- EN: Day cruise: a daytime backwater trip without an overnight stay. The district tourism council's day cruise lists check-in at 11:30 am and check-out at 5:00 pm.
- ML (DRAFT, needs native review): പകൽ യാത്ര: രാത്രി താമസമില്ലാതെ പകൽ സമയത്തെ കായൽ യാത്ര. ജില്ലാ ടൂറിസം പ്രമോഷൻ കൗൺസിലിന്റെ പകൽ യാത്രയിൽ രാവിലെ 11.30-ന് ചെക്ക്-ഇനും വൈകിട്ട് 5-ന് ചെക്ക്-ഔട്ടും നൽകിയിരിക്കുന്നു.
- Note: Source S54. Confirm current DTPC timings before publishing.

**`exp.village`** (Houseboat experience descriptions)
- EN: Village and canoe tours: small country boats can reach narrow canals that big houseboats cannot, so visitors see paddy fields and village life in Kuttanad, known as the Rice Bowl of Kerala.
- ML (DRAFT, needs native review): ഗ്രാമയാത്ര: ചെറിയ വള്ളങ്ങൾ വലിയ ഹൗസ്ബോട്ടുകൾക്ക് എത്താൻ കഴിയാത്ത ഇടുങ്ങിയ തോടുകളിൽ എത്തും. കേരളത്തിന്റെ നെല്ലറ എന്നറിയപ്പെടുന്ന കുട്ടനാട്ടിലെ പാടങ്ങളും ഗ്രാമജീവിതവും കാണാം.
- Note: Sources S52, S59 (listing describes a country boat with a retractable roof).

**`op.headline`** (Operator partnership messaging)
- EN: We are listening before we build.
- ML (DRAFT, needs native review): നിർമ്മിക്കുംമുൻപ് ഞങ്ങൾ കേൾക്കുകയാണ്.
- Note: Operator page H1.

**`op.body`** (Operator partnership messaging)
- EN: Kaayal is a Malayalam-first voice assistant for Alappuzha visitors. We are speaking with houseboat operators about how enquiries reach you today and what would help. No fees, no commitments, and nothing is listed without your approval.
- ML (DRAFT, needs native review): കായൽ ആലപ്പുഴയിലെ സന്ദർശകർക്കുള്ള മലയാളം-ആദ്യ ശബ്ദ സഹായിയാണ്. ഇന്ന് അന്വേഷണങ്ങൾ നിങ്ങളിലേക്ക് എങ്ങനെ എത്തുന്നു എന്നും എന്താണ് സഹായകമാകുക എന്നും ഹൗസ്ബോട്ട് ഓപ്പറേറ്റർമാരോട് ഞങ്ങൾ സംസാരിക്കുന്നു. ഫീസില്ല, ബാധ്യതയില്ല, നിങ്ങളുടെ അനുമതിയില്ലാതെ ഒന്നും ലിസ്റ്റ് ചെയ്യില്ല.
- Note: 'No fees' is a brand promise for the research phase only. Revisit if the owner later approves paid features (Future).

**`op.cta`** (Operator partnership messaging)
- EN: Tell us how you take enquiries today
- ML (DRAFT, needs native review): ഇന്ന് നിങ്ങൾ അന്വേഷണങ്ങൾ എങ്ങനെ സ്വീകരിക്കുന്നു എന്ന് പറയൂ
- Note: Phase 1 safe: mailto or phone only.

**`faq.1`** (FAQ)
- EN: Can I book a houseboat through Kaayal? - Not yet. Kaayal is a prototype that answers questions. You would book directly with an operator or through the official DTPC counter.
- Note: Phase 1 truth.

**`faq.2`** (FAQ)
- EN: Does Kaayal show prices? - No live prices. It explains what affects price (bedrooms, A/C hours, season, taxes) and what to ask an operator.

**`faq.3`** (FAQ)
- EN: Is a boat available on my dates? - Kaayal cannot check availability. Confirm with the operator.

**`faq.4`** (FAQ)
- EN: Which languages does Kaayal speak? - Malayalam and English, including a mix of both. Other Indian languages are listed by the voice platform but have not been tested by us.
- Note: Platform lists 10-11 Indian languages (S41, S43); we only claim what we test.

**`faq.5`** (FAQ)
- EN: Do I need an app? - No. Just call the demo line.

**`faq.6`** (FAQ)
- EN: Is my call recorded? - [OWNER DECISION NEEDED: recording, transcript retention, and consent wording. Do not publish a claim until decided.]
- Note: Sarvam exposes caller number and transcript to the tool call (S42); DPDP notice duties from 13 May 2027 (S47).

**`faq.7`** (FAQ)
- EN: Is Kaayal government-approved or operator-verified? - No. Kaayal is independent and does not rank or endorse boats. To check a boat, ask for its registration and Kerala Tourism classification.
- Note: Avoid 'verified' language.

**`faq.8`** (FAQ)
- EN: Who is Kaayal for? - Visitors and families planning an Alappuzha trip, and later, local operators who want to understand visitor questions.

## 3. SEO metadata

| Page | Title (max 60) | Meta description (max 155) |
|---|---|---|
| Home | Kaayal: Alappuzha travel help in Malayalam and English (54) | Call Kaayal, a Malayalam-first voice assistant, with questions about Alappuzha backwater cruises and places. Prototype: no bookings or live prices. (147) |
| How it works | How Kaayal works: a phone call, not an app (42) | Call, ask in Malayalam or English, and hear a spoken answer. See what Kaayal can and cannot do before you call. (111) |
| Houseboat guide | Alappuzha houseboat guide: what to ask before you book (54) | Classification, registration, what is included, why prices differ. A plain-language checklist for booking an Alleppey houseboat. (128) |
| Official route (DTPC) | Alappuzha DTPC houseboat counter: how it works (46) | How the district tourism council's pre-paid houseboat counter works, and when to use it. Check current details with DTPC. (121) |
| For operators | Houseboat operators: help shape Kaayal, no fees (47) | We are talking to Alappuzha houseboat operators about visitor enquiries and a Malayalam voice assistant. No commitment. (119) |
| FAQ | Kaayal FAQ: bookings, prices, languages, calls (46) | Straight answers on what Kaayal does, what it does not do, and how your call is handled. (88) |
| Contact | Contact Kaayal (14) | Questions about Kaayal or the Alappuzha demo line? Email us or call the demo line. (82) |

**Technical SEO checklist**
- One H1 per page; URL slugs in English (`/how-it-works`, `/houseboat-guide`, `/for-operators`, `/faq`); Malayalam pages under `/ml/` with `hreflang` en/ml once reviewed.
- `Organization` schema (name Kaayal, no fabricated address or rating). `FAQPage` schema only for approved FAQs. No `Review`/`AggregateRating` schema.
- Canonical tags, sitemap.xml, robots.txt; page speed budget for mobile 4G.
- Malayalam web font must load with `font-display: swap`; verify conjunct rendering on Android and iOS.

## 4. Keyword targets (volumes NOT measured)

| Keyword | Language | Intent | Page | Priority |
|---|---|---|---|---|
| alleppey houseboat booking | English | Transactional | Houseboat guide (informational angle) | High |
| alappuzha houseboat price | English | Commercial | Houseboat guide: what drives price | High |
| alleppey houseboat rates 2026 | English | Commercial | Houseboat guide: price factors | Medium |
| how to choose a houseboat in alleppey | English | Informational | What to ask before you book | High |
| alleppey houseboat classification diamond gold silver | English | Informational | What to ask before you book | Medium |
| DTPC houseboat counter alappuzha | English | Navigational | Official route explainer | Medium |
| best time to visit alleppey houseboat | English | Informational | Houseboat guide: seasons | Medium |
| nehru trophy boat race houseboat stay | English | Informational | Events page | Low |
| alleppey day cruise vs overnight houseboat | English | Informational | Houseboat guide | Medium |
| malayalam voice assistant tourism kerala | English | Informational | Home | Low |
| ആലപ്പുഴ ഹൗസ്ബോട്ട് | Malayalam | Informational/Commercial | Malayalam home + guide | High |
| ആലപ്പുഴ പുരവഞ്ചി ബുക്കിംഗ് | Malayalam | Transactional | Malayalam guide | High |
| പുരവഞ്ചി നിരക്ക് | Malayalam | Commercial | Malayalam price-factors guide | Medium |
| ആലപ്പുഴ കായൽ യാത്ര | Malayalam | Informational | Malayalam day-cruise guide | Medium |
| ഹൗസ്ബോട്ട് ബുക്ക് ചെയ്യുമ്പോൾ ശ്രദ്ധിക്കേണ്ടത് | Malayalam | Informational | Malayalam 'what to ask' guide | High |
| alappuzha tourist places | English | Informational | Places guide | Low |

Run Google Keyword Planner and Search Console before committing to any volume claim.

## 5. Design references (Backwater Editorial)

| Token | Hex | Use |
|---|---|---|
| Deep Lagoon | #123F3C | Primary dark, headings, hero background |
| Teal | #267A73 | Links, accents, charts |
| Warm Ivory | #F7F5EE | Page background |
| Mist | #D9E6DE | Panels, dividers |
| Sand | #C68E55 | Sparing highlight, quotes |

- Typography: Satoshi-style geometric sans (Satoshi if licensed; otherwise a close free alternative agreed with Devin) with a legible Malayalam companion (e.g., Noto Sans Malayalam). Generous whitespace, strong headings.
- Motif: subtle contour lines / water ripples as background detail; the deck uses concentric contour ellipses. Restrained effects only.
- Avoid: generic SaaS templates, decorative AI imagery, heavy glassmorphism, gratuitous gradients, repetitive card grids.
- Voice interfaces use "Lagoon Glass"; operator dashboards use "Coastal Utility" (Phase 2, not now).
- No Kaayal website or design system was accessible to the research team. **Devin: confirm or replace these provisional tokens and tell us so the deck can be matched.**

## 6. Imagery suggestions

No licensed photos could be fetched from the research environment, so the deck uses original contour artwork. For the website:
- Preferred: photography commissioned or taken by the team; Kerala Tourism media with written permission.
- Subjects: early-morning Vembanad light, a country boat in a narrow canal, paddy fields in Kuttanad, hands holding a phone with the call screen. Authentic Alappuzha, people-forward, no stock "tropical" cliches.
- Every image needs alt text and a licence line in the repo. Do not use OTA or operator photos.

## 7. Contact and callback CTAs

- Phase 1 safe: `tel:` link to the demo number [OWNER TO SUPPLY] and `mailto:` link.
- A form that stores names or numbers is **blocked** until the owner approves consent text and retention (Q02, Q10). Do not build it.

## 8. Accessibility and performance

- WCAG 2.1 AA contrast: Ivory on Deep Lagoon passes; check Sand on Ivory before using it for text.
- Tap targets 44 px minimum; call button sticky on mobile.
- All pages usable without JavaScript for text content.

## 9. Do not build (Phase 2 / Future)

Operator onboarding, catalogue, itineraries, availability, request-to-book, dashboards, WhatsApp messages, payments, Aadhaar eKYC, subscriptions, paid promotions, P2P or sync. All are `BLOCKED_PENDING_OWNER_CLARIFICATION` in tab `13_Devin_Backlog`.
