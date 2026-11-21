"""Public site — Backwater Editorial single-page site.

Honesty contract (prototype): listings are owner-reviewed but Paayal never
confirms bookings or prices; demo-seeded inventory carries a DEMO badge;
WhatsApp onboarding is a demo path; nothing here is a confirmed booking.
"""

import json
import re
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session

from app.catalog import listed_boats
from app.db import Boat, Operator
from app.ui import esc as _esc, page as _page

router = APIRouter()

_CONTOURS = """
<svg class="contours" aria-hidden="true" viewBox="0 0 720 120" width="100%" height="120"
     preserveAspectRatio="none" style="display:block;margin:1.5rem 0 0;opacity:.9">
  <g fill="none" stroke="#267A73" stroke-width="1.4">
    <path d="M0,95 C120,75 200,110 340,90 S560,70 720,92"/>
    <path d="M0,80 C140,60 240,100 360,80 S580,55 720,78" opacity=".85"/>
    <path d="M0,65 C160,45 280,88 400,66 S600,42 720,64" opacity=".68"/>
    <path d="M0,50 C180,32 320,76 440,54 S620,30 720,50" opacity=".52"/>
    <path d="M0,35 C200,20 360,62 480,42 S640,20 720,38" opacity=".38"/>
  </g>
</svg>
"""

# Hand-drawn kettuvallam scene: sun, birds, palms, a houseboat drifting on
# animated waterlines. Stroked elements draw themselves in via motion.dev.
_SCENE = """
<svg class="scene" aria-hidden="true" viewBox="0 0 720 230" width="100%"
     style="display:block;margin:2rem 0 .25rem;overflow:visible">
  <circle cx="585" cy="48" r="24" fill="#C68E55" opacity=".28"/>
  <g class="birds" fill="none" stroke="#123F3C" stroke-width="1.4"
     stroke-linecap="round" opacity=".55">
    <path d="M600,44 q6,-6 12,0 q6,-6 12,0"/>
    <path d="M634,62 q5,-5 10,0 q5,-5 10,0"/>
  </g>
  <path d="M0,128 C110,118 240,130 380,122 S640,112 720,122"
        fill="none" stroke="#123F3C" stroke-width="1" opacity=".25"/>
  <g fill="none" stroke="#123F3C" stroke-width="1.6" stroke-linecap="round" opacity=".7">
    <path d="M82,128 C78,108 82,86 92,66"/>
    <path d="M92,66 C76,60 62,64 52,76"/>
    <path d="M92,66 C78,54 62,52 50,56"/>
    <path d="M92,66 C102,50 118,44 132,48"/>
    <path d="M92,66 C106,56 122,56 134,64"/>
    <path d="M656,126 C654,112 658,98 664,86"/>
    <path d="M664,86 C654,82 644,84 636,92"/>
    <path d="M664,86 C656,78 646,76 638,78"/>
    <path d="M664,86 C672,76 682,74 690,76"/>
    <path d="M664,86 C674,80 684,82 692,88"/>
  </g>
  <g class="boat">
    <path d="M168,164 C200,182 300,190 380,186 C460,182 512,170 540,160
             L528,174 C480,190 360,200 260,194 C220,191 186,182 168,164 Z"
          fill="#123F3C"/>
    <path d="M208,158 C214,116 268,88 348,86 C428,84 492,116 506,158"
          fill="none" stroke="#123F3C" stroke-width="3"/>
    <path d="M238,158 C242,124 288,102 348,100 C408,98 458,124 478,158"
          fill="none" stroke="#267A73" stroke-width="1.2" opacity=".55"/>
    <path d="M270,158 C274,132 306,116 348,114 C390,112 430,132 450,158"
          fill="none" stroke="#267A73" stroke-width="1" opacity=".4"/>
    <path d="M208,158 L506,158" stroke="#123F3C" stroke-width="2"/>
    <path d="M538,158 L552,116" stroke="#123F3C" stroke-width="2.4" stroke-linecap="round"/>
    <circle cx="552" cy="112" r="3.5" fill="#123F3C"/>
  </g>
  <g fill="none" stroke="#267A73" stroke-width="1.2">
    <ellipse class="rip" cx="350" cy="196" rx="70" ry="5"/>
    <ellipse class="rip rip2" cx="350" cy="196" rx="70" ry="5"/>
  </g>
  <g class="waves" fill="none" stroke="#267A73" stroke-width="1.4">
    <path d="M0,206 C120,192 240,214 360,200 S620,186 720,202" opacity=".85"/>
    <path d="M0,214 C140,202 280,222 400,210 S600,198 720,212" opacity=".6"/>
    <path d="M0,222 C160,212 320,228 460,218 S640,210 720,220" opacity=".4"/>
  </g>
</svg>
"""


# --- shared chrome ----------------------------------------------------------

def _nav(request: Request) -> str:
    phone = request.app.state.settings.kaayal_phone_number
    cta = ""
    if phone:
        digits = re.sub(r"\D", "", phone)
        cta = f'<a class="btn navcall" href="tel:+{_esc(digits)}">Call {_esc(phone)}</a>'
    return (
        '<nav class="topnav" aria-label="Main">'
        '<a class="wordmark" href="/">Kaayal <span class="ml" lang="ml">കായൽ</span></a>'
        '<a class="navlink" href="#paayal">Meet Paayal</a>'
        '<a class="navlink" href="#boats">Houseboats</a>'
        '<a class="navlink" href="#explore">Explore</a>'
        '<a class="navlink" href="#before-you-book">Before You Book</a>'
        '<a class="navlink" href="#faq">FAQ</a>'
        f"{cta}</nav>"
    )


def _footer(request: Request) -> str:
    s = request.app.state.settings
    nums = []
    if s.kaayal_phone_number:
        d = re.sub(r"\D", "", s.kaayal_phone_number)
        nums.append(f'Call <a href="tel:+{_esc(d)}">{_esc(s.kaayal_phone_number)}</a>')
    if s.kaayal_whatsapp_number:
        d = re.sub(r"\D", "", s.kaayal_whatsapp_number)
        nums.append(
            f'WhatsApp <a href="https://wa.me/{_esc(d)}" rel="noopener">'
            f'{_esc(s.kaayal_whatsapp_number)}</a>')
    nums_html = f"<p>{' · '.join(nums)}</p>" if nums else ""
    return (
        '<footer class="site-footer">'
        "<p>Kaayal is a working prototype: inbound calling and booking inquiries "
        "are live, and the callback system is real — but Paayal’s return calls "
        "are simulated, so no real outbound call is placed. Nothing on this "
        "site is a confirmed booking; the operator always confirms. WhatsApp "
        "messaging runs on WhatsApp Web automation (open-wa) under a "
        "closed-demo exemption from the open-wa team; the production path is "
        "the official WhatsApp Business API.</p>"
        '<p><a href="#privacy">Privacy &amp; consent</a> · '
        '<a href="#before-you-book">Before you book</a> · '
        '<a href="#dtpc">DTPC counter</a> · '
        '<a href="#faq">FAQ</a> · '
        '<a href="https://glitchyi.github.io/kaayal/" '
        'rel="noopener">Docs &amp; runbooks</a></p>'
        f"{nums_html}</footer>"
    )


_ORG_JSONLD = (
    '<script type="application/ld+json">'
    '{"@context":"https://schema.org","@type":"Organization",'
    '"name":"Kaayal","alternateName":"കായൽ",'
    '"description":"Malayalam-first phone tourism service for Alappuzha, Kerala. '
    'Paayal is Kaayal\'s AI voice assistant."}'
    "</script>"
)


def _base_url(request: Request) -> str:
    s = request.app.state.settings
    return (getattr(s, "kaayal_public_base_url", "") or str(request.base_url)).rstrip("/")


def _public(request: Request, title: str, body: str, description: str = "",
            head_extra: str = "") -> HTMLResponse:
    base = _base_url(request)
    return HTMLResponse(_page(
        title, body, description=description,
        nav=_nav(request), footer=_footer(request),
        canonical_url=base + request.url.path,
        head_extra=_ORG_JSONLD + head_extra,
        og_image=base + "/static/paayal.png",
    ))


def _tel_digits(request: Request) -> str:
    phone = request.app.state.settings.kaayal_phone_number or ""
    return re.sub(r"\D", "", phone)


def _call_cta(request: Request, sonar: bool = True) -> str:
    phone = request.app.state.settings.kaayal_phone_number
    if not phone:
        return '<p class="muted" style="margin-top:1.25rem">Call the Kaayal number to talk to Paayal.</p>'
    digits = re.sub(r"\D", "", phone)
    cls = "btn sonar" if sonar else "btn"
    return (
        f'<p class="call_line" style="margin-top:1.25rem"><a class="{cls}" href="tel:+{_esc(digits)}" '
        f'style="text-decoration:none">Call {_esc(phone)}</a></p>'
    )


def _boat_card(b: Boat, op: Operator) -> str:
    demo = ' <span class="badge wait">DEMO</span>' if b.source == "demo-seed" else ""
    avail = (
        '<span class="badge ok">available</span>'
        if b.available
        else '<span class="badge wait">unavailable</span>'
    )
    meta = f"with {_esc(op.name)}"
    if b.capacity:
        meta += f" · up to {_esc(b.capacity)} guests"
    if b.embarkation_point:
        meta += f" · from {_esc(b.embarkation_point)}"
    price = (
        f'<p style="margin:.35rem 0 0;color:var(--lagoon)"><b>{_esc(b.price_display)}</b>'
        ' <span class="muted small">— set by the operator, confirmed on the callback</span></p>'
        if b.price_display else ""
    )
    chips = "".join(f'<span class="chip">{_esc(a)}</span>' for a in (b.amenities or []))
    chips_html = f'<p style="margin:.5rem 0 0">{chips}</p>' if chips else ""
    reach = (
        '<p class="muted small" style="margin:.5rem 0 0">This operator can’t be reached '
        'right now — Paayal can arrange a callback when they return.</p>'
        if not op.reachable else
        '<p class="muted small" style="margin:.5rem 0 0">The operator is reachable — '
        'your inquiry goes straight to them.</p>'
    )
    return (
        f'<div class="card"><h3>{_esc(b.name)}{demo}</h3>'
        f'<p class="muted" style="margin:.15rem 0">{meta}</p>'
        f'<p style="margin:.4rem 0 0">{avail}</p>{price}{chips_html}{reach}</div>'
    )


_FAQ = [
    ("Can I book a houseboat through Kaayal?",
     "Not directly. Paayal takes a booking inquiry — your name, number, date "
     "and group size go to the operator with your consent — and the operator "
     "calls you back to confirm. Nothing is booked until they say yes."),
    ("Does Kaayal show prices?",
     "Operators can publish a price note on their listing, but Paayal never "
     "guarantees prices. She explains what affects price — boat, season, "
     "what’s included — and the operator confirms the figure on the call."),
    ("Is a boat available on my dates?",
     "Paayal can tell you what operators have listed as available, but the "
     "operator always confirms on the call back. If nothing fits, she can "
     "arrange a callback when something frees up."),
    ("Which languages does Paayal speak?",
     "Malayalam and English, including mixing both in the same call."),
    ("Do I need an app?",
     "No. Just call the Kaayal number and talk."),
    ("Is Kaayal government-approved or operator-verified?",
     "No. Kaayal is an independent service and does not rank or endorse boats. "
     "Listings are reviewed and switched on by the Kaayal owner — a human "
     "approval step, not a government or safety certification. To check a "
     "boat yourself, ask for its registration and Kerala Tourism "
     "classification."),
    ("What happens to my name and number?",
     "They go only to the operator you inquire about, after you consent on "
     "the call — that is the whole point of the inquiry. The Kaayal owner can "
     "see inquiries in the admin dashboard. Details are anonymized after 90 "
     "days. See the privacy section below for the full picture."),
    ("Can I cancel a booking inquiry?",
     "There is nothing to cancel — an inquiry is not a booking. If you "
     "changed your mind, tell the operator when they call, or call Paayal "
     "and ask her to withdraw your inquiry."),
    ("Can I stop Paayal calling me back?",
     "Yes — tell her “don’t call me” at any point, on any call. Callbacks "
     "only ever happen between 09:00 and 18:00 IST, at most twice per "
     "request, and only about the inquiry you consented to."),
    ("Are the callbacks real?",
     "The callback system is real — consent, queueing and availability "
     "triggers all work. In this prototype Paayal’s return call is simulated "
     "and no real outbound phone call is placed."),
]


# --- the page -----------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def landing(request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        rows = sorted(listed_boats(session), key=lambda row: row[0].name)

    call_line = _call_cta(request)
    wa = request.app.state.settings.kaayal_whatsapp_number
    wa_digits = re.sub(r"\D", "", wa or "")
    operator_cta = (
        f'<p style="margin-top:.75rem"><a class=btn target="_blank" rel="noopener" '
        f'href="https://wa.me/{_esc(wa_digits)}?text='
        f'{quote("Hi Kaayal, I run a boat in Alappuzha and want to join as an operator.")}" '
        f'style="text-decoration:none">WhatsApp {_esc(wa)} to start onboarding</a></p>'
        if wa
        else '<p class="muted small">Operator onboarding is by WhatsApp — '
             'message the Kaayal onboarding number to start.</p>'
    )

    boats = "".join(_boat_card(b, op) for b, op in rows) or (
        '<div class=card><h3>No boats on the list yet</h3>'
        '<p class=muted>Operators are being onboarded. Call Paayal — she can '
        'take a booking inquiry anyway, and with your consent she can call you '
        'back when a boat that fits is listed.</p></div>'
    )

    faq_items = "".join(
        f'<h3 class="faq-q">{_esc(q)}</h3><p class=muted>{_esc(a)}</p>'
        for q, a in _FAQ
    )
    faq_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in _FAQ
        ],
    })
    faq_jsonld = f'<script type="application/ld+json">{faq_ld}</script>'

    body = f"""
<h1 style="font-size:2.6rem">The backwaters,<br>a phone call away.</h1>
<p class=lead>
  Paayal is Kaayal’s voice assistant. Call and ask — in <b>Malayalam</b> or <b>English</b> —
  about boat operators in Alappuzha, and leave a booking inquiry. The operator calls you
  back to confirm. No app, no forms, no account.</p>
{call_line}
<p class=muted small>Prefer to scroll? <a href="#boats">See the boats</a>
Paayal can tell you about.</p>
{_SCENE}

<section id="how">
<p class=kick>How it works</p>
<ol style="padding-left:1.25rem">
  <li style="margin-bottom:.6rem"><b>Call</b> — Paayal answers in your language and can tell
      you about reviewed boats: capacity, embarkation point, the operator behind each one.</li>
  <li style="margin-bottom:.6rem"><b>Inquire</b> — leave your name, number, date, and group size.
      With your permission, the inquiry goes to the operator.</li>
  <li style="margin-bottom:.6rem"><b>Not available now?</b> — if a boat is unavailable or its
      operator can’t be reached, Paayal can call <i>you</i> back when that changes —
      only if you say yes, and she never calls for anything else.</li>
  <li><b>Confirm</b> — the operator calls you directly to confirm the trip and the price.
      Nothing is booked until they say yes.</li>
</ol>
</section>

<section id="paayal">
<p class=kick>Meet Paayal · <span class="ml" lang="ml">പായൽ</span></p>
<h2>The voice on the other end</h2>
<img src="/static/paayal.png" alt="Paayal — Kaayal’s voice assistant"
     width="140" height="140" style="border-radius:50%;margin:.25rem 0 1rem;
     border:2px solid var(--line);float:right;margin-left:1rem">
<p>Paayal is Kaayal’s voice assistant — a <b>Malayalam-first</b> voice on the other
end of the Kaayal phone line. She also speaks English. You talk, she answers;
there is nothing to install and nothing to type.</p>
<h3>What Paayal does</h3>
<ul style="padding-left:1.25rem">
  <li style="margin-bottom:.5rem">Answers questions about boat trips out of Alappuzha,
      in Malayalam or English.</li>
  <li style="margin-bottom:.5rem">Describes <b>reviewed</b> boats — capacity, embarkation
      point, amenities, and the operator behind each listing.</li>
  <li style="margin-bottom:.5rem">Takes booking inquiries: your name, number, preferred
      date, and group size go to the operator <b>only with your consent</b>.</li>
  <li>Arranges consented callbacks — if a boat or operator can’t be reached now,
      she can call you back when they can. <span class="muted small">In this
      prototype the return call is simulated; the consent, queue, and
      availability triggers are real.</span></li>
</ul>
<h3>What Paayal never does</h3>
<ul style="padding-left:1.25rem">
  <li style="margin-bottom:.5rem"><b>Confirms bookings.</b> Only the operator confirms,
      by calling you back. Until then nothing is booked.</li>
  <li style="margin-bottom:.5rem"><b>Confirms prices.</b> Quoted prices come from the
      operator; Paayal repeats them, she doesn’t guarantee them.</li>
  <li><b>Takes payments.</b> There is no checkout, no wallet, no card on file —
      you settle directly with the operator.</li>
</ul>
<h3>Things you can ask her</h3>
<ul style="padding-left:1.25rem">
  <li style="margin-bottom:.5rem">“What boats go out of Alappuzha this weekend?”</li>
  <li style="margin-bottom:.5rem">“Is anything available for six people on Saturday?”</li>
  <li style="margin-bottom:.5rem">“What should I check before I book a houseboat?”</li>
  <li>“Call me back when that boat is free.”</li>
</ul>
<p class=muted small>Paayal shares your name and number with an operator only after
you say yes on the call. Say no, and nothing is shared.
<a href="#privacy">How your details are handled →</a></p>
</section>

<section id="boats">
<p class=kick>Houseboats</p>
<h2>Boats on the Kaayal list</h2>
<p class=muted>Boats the Kaayal owner has reviewed and switched on, operating out
of Alappuzha. Availability and prices come from the operators themselves —
the operator confirms both on the call back.</p>
{boats}
<p class="muted small">Every listing here is reviewed by the Kaayal owner —
a person, not a government or safety certification.
<b>Paayal never confirms bookings</b> — after you inquire, the operator calls you
back and confirms the trip and the price themselves. Prefer an official counter?
See <a href="#dtpc">the DTPC pre-paid counter</a>.</p>
<p><a class=btn href="tel:+{_tel_digits(request)}" style="text-decoration:none">Call to send a booking inquiry</a></p>
</section>

{_CONTOURS}

<section id="explore">
<p class=kick>Explore Alappuzha</p>
<h2>The backwaters</h2>
<p>Alappuzha — older maps say Alleppey — is a canal town on the edge of Vembanad,
Kerala’s largest lake. Behind the town, lakes, lagoons, and narrow canals link
together into the waterways people call the backwaters.</p>
<h3>Trips from town</h3>
<p>Most local trips cast off from the <b>Finishing Point</b> and <b>Punnamada</b>
jetties near the town centre. From there, operators run small motor boats and
shikaras for an hour or two through the canals, as well as the larger
kettuvallam houseboats that cruise Vembanad — some for a day, some overnight.</p>
<p>What you see depends on the route: paddy fields below the waterline, village
jetties, toddy shops, and long open stretches of lake. Morning and late-afternoon
light are the kindest.</p>
<h3>Before you go</h3>
<p>Trip length, route, and price vary by boat and by season, and they are the
operator’s call — not ours. We don’t publish timings or tariffs here. Paayal can
describe boats on the list by phone, and the operator confirms the details
when they call you back.</p>
<p><a href="#before-you-book">What to ask before you book →</a></p>
</section>

<section id="before-you-book">
<p class=kick>Before you book</p>
<h2>Five questions worth asking</h2>
<p class=muted>Before you pay a deposit — the operator’s answers are theirs to give.</p>
<ol style="padding-left:1.25rem">
  <li style="margin-bottom:.75rem"><b>Is the boat registered?</b> Ask for the
      boat’s registration before you pay anything.</li>
  <li style="margin-bottom:.75rem"><b>What is its Kerala Tourism
      classification?</b> Houseboats are classified Silver, Gold, or Diamond —
      ask which yours is and what it means for that boat.
      <a href="https://www.keralatourism.org/cls/houseboats/Houseboat.htm"
         target="_blank" rel="noopener">Kerala Tourism’s classification page</a>
      explains the grades.</li>
  <li style="margin-bottom:.75rem"><b>What exactly is included?</b> Meals,
      air-conditioning hours, and cruise timings differ by operator — get them
      spelled out, not assumed.</li>
  <li style="margin-bottom:.75rem"><b>What is the price based on?</b> Weekday
      or peak dates, taxes, and the cancellation terms — ask before, not after.</li>
  <li><b>Which boat will you actually get?</b> Ask for photos of the actual
      boat, not a brochure boat.</li>
</ol>
<h3>What moves the price</h3>
<p class=muted>Quotes vary with the boat itself — size and bedrooms, A/C hours,
season and weekday versus peak dates, what’s included (meals, cruise time),
taxes, and the cancellation terms. Comparing two boats? Compare what’s
included, not just the number.</p>
<p class="muted small">Further reading:
<a href="https://www.onmanorama.com/travel/travel-news/2026/01/21/kerala-houseboats-defy-guidelines.html"
   target="_blank" rel="noopener">Onmanorama: Kerala houseboats defy guidelines</a>.</p>
</section>

<section id="dtpc">
<p class=kick>The official route</p>
<h2>The DTPC houseboat counter</h2>
<p>If you’d rather book through an official channel, the District Tourism
Promotion Council (DTPC) runs a <b>pre-paid houseboat counter</b> in
Alappuzha. You pay at the counter and are allotted a boat — useful if you
want a fixed, government-run option rather than calling operators yourself.</p>
<p>Kerala Tourism’s houseboat page lists an advance payment of
<b>₹2,500</b> for booking through this route.
<a href="https://www.keralatourism.org/houseboat/" target="_blank"
   rel="noopener">See Kerala Tourism’s houseboat page</a>.</p>
<p class=muted>Counter details — timings, rates, and how the allotment works —
change over time. <b>Confirm current details with DTPC</b> before you travel;
we don’t keep their timings here.</p>
</section>

{_CONTOURS}

<section id="faq">
<p class=kick>FAQ</p>
<h2>Straight answers</h2>
<p class=muted>What Kaayal does, what it doesn’t, and how your call is handled.</p>
{faq_items}
</section>

<section id="privacy">
<p class=kick>Privacy</p>
<h2>Privacy &amp; consent</h2>
<p class=muted>What Kaayal does with your details — based on what the system
actually does today, not promises.</p>
<h3>What we collect</h3>
<p>Only what a booking inquiry or callback needs: your <b>name</b>, <b>phone
number</b>, preferred date, and group size. Paayal asks for your permission on
the call before saving any of it — say no and nothing is stored.</p>
<h3>What it’s for</h3>
<p>So the operator can call you back and confirm the trip. That is the entire
purpose — there is no marketing list, no resale, no advertising.</p>
<h3>Who sees it</h3>
<p>The operator you inquire about sees your contact details when they confirm
your inquiry. The Kaayal owner can view inquiries in the admin dashboard.
Nobody else.</p>
<h3>Callbacks</h3>
<p>A callback is only queued after you agree on the call. Calls are attempted
only between <b>09:00 and 18:00 IST</b>, at most twice per request, and expire
after about a week. Say “don’t call me” to Paayal at any time — on any call —
and all pending callbacks for your number stop. In this prototype the return
call itself is simulated; the consent and queue rules described here are real.</p>
<h3>How long we keep it</h3>
<p>Your name, phone number, and notes are <b>anonymized after 90 days</b>. The
inquiry keeps only its reference number and status afterwards.</p>
<h3>Calls, recordings, transcripts</h3>
<p>Kaayal does not store call recordings or transcripts of your inbound calls
in its own database. Simulated demo callbacks keep a script of what Paayal
would have said — clearly marked as simulation, not a real conversation. Calls
are carried by Sarvam’s voice platform; whether they retain call audio is
governed by Sarvam’s policies and the account’s settings — that part is outside
Kaayal’s own systems and we are not able to state it here.</p>
<h3>This website</h3>
<p>No cookies, no analytics, no trackers, no forms that collect your details.
Just links to call or message us.</p>
<p class=muted small>Questions about your details? Call the Kaayal number and ask.</p>
</section>

<hr class=rule>
<p class=muted small><b>For operators.</b> Run a boat out of Alappuzha? Message us on
WhatsApp — a human reviews you, then you list your boats once, get booking
inquiries, and confirm by a call back.</p>
{operator_cta}
<p class=muted small>Every listing is reviewed and switched on by the Kaayal owner before
callers hear about it — that means a person approved it, not a government or
safety certification. Kaayal never confirms prices, availability, or bookings
on its own — the operator always does.</p>
"""
    return _public(request,
        "Kaayal | Alappuzha boats by phone",
        body,
        description="Call Kaayal and talk to Paayal in Malayalam or English about Alappuzha boats: send a booking inquiry, the operator calls back to confirm.",
        head_extra=faq_jsonld,
    )


# --- redirects from the old multi-page URLs -------------------------------------

_OLD = {
    "/paayal": "#paayal",
    "/boats": "#boats",
    "/explore": "#explore",
    "/before-you-book": "#before-you-book",
    "/dtpc-houseboat-counter": "#dtpc",
    "/faq": "#faq",
    "/privacy": "#privacy",
}

for _path, _frag in _OLD.items():
    async def _redirect(request: Request, frag=_frag):
        return RedirectResponse(str(request.base_url).rstrip("/") + "/" + frag,
                                status_code=301)
    router.add_api_route(_path, _redirect, methods=["GET"])


# --- robots + sitemap ---------------------------------------------------------

@router.get("/robots.txt")
def robots(request: Request):
    base = _base_url(request)
    return Response(
        f"User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /portal\n"
        f"Disallow: /api\n\nSitemap: {base}/sitemap.xml\n",
        media_type="text/plain",
    )


@router.get("/sitemap.xml")
def sitemap(request: Request):
    base = _base_url(request)
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{base}/</loc></url>\n</urlset>\n",
        media_type="application/xml",
    )
