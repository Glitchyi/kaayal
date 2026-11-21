"""Public site — Backwater Editorial pages.

Honesty contract (prototype): listings are owner-verified but Paayal never
confirms bookings or prices; demo-seeded inventory carries a DEMO badge;
WhatsApp onboarding is a demo path; nothing here is a confirmed booking.
"""

import json
import re
from urllib.parse import quote

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response
from sqlmodel import Session, select

from app.db import Boat, Operator
from app.ui import esc as _esc, page as _page

router = APIRouter()

_CONTOURS = """
<svg aria-hidden="true" viewBox="0 0 720 120" width="100%" height="120"
     preserveAspectRatio="none" style="display:block;margin:1.5rem 0 0;opacity:.55">
  <g fill="none" stroke="#267A73" stroke-width="1" opacity=".35">
    <path d="M0,95 C120,75 200,110 340,90 S560,70 720,92"/>
    <path d="M0,80 C140,60 240,100 360,80 S580,55 720,78" opacity=".7"/>
    <path d="M0,65 C160,45 280,88 400,66 S600,42 720,64" opacity=".5"/>
    <path d="M0,50 C180,32 320,76 440,54 S620,30 720,50" opacity=".35"/>
    <path d="M0,35 C200,20 360,62 480,42 S640,20 720,38" opacity=".22"/>
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
        '<a class="navlink" href="/boats">Boats</a>'
        '<a class="navlink" href="/paayal">Meet Paayal</a>'
        '<a class="navlink" href="/explore">Explore</a>'
        '<a class="navlink" href="/faq">FAQ</a>'
        f"{cta}</nav>"
    )


def _footer(request: Request) -> str:
    s = request.app.state.settings
    nums = []
    if s.kaayal_phone_number:
        d = re.sub(r"\D", "", s.kaayal_phone_number)
        nums.append(f'Call <a href="tel:+{_esc(d)}">{_esc(s.kaayal_phone_number)}</a>')
    if s.kaayal_whatsapp_number:
        nums.append(f"WhatsApp {_esc(s.kaayal_whatsapp_number)}")
    nums_html = f"<p>{' · '.join(nums)}</p>" if nums else ""
    return (
        '<footer class="site-footer">'
        "<p>Kaayal prototype: the phone line and voice assistant are live; "
        "WhatsApp onboarding is a demo; the catalog shows verified listings; "
        "booking inquiries are live, but Paayal’s return calls are simulated "
        "(no real outbound call is placed); nothing on this site is a "
        "confirmed booking.</p>"
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
    canonical = _base_url(request) + request.url.path
    return HTMLResponse(_page(
        title, body, description=description,
        nav=_nav(request), footer=_footer(request),
        canonical_url=canonical,
        head_extra=_ORG_JSONLD + head_extra,
    ))


def _tel_digits(request: Request) -> str:
    phone = request.app.state.settings.kaayal_phone_number or ""
    return re.sub(r"\D", "", phone)


def _call_cta(request: Request) -> str:
    phone = request.app.state.settings.kaayal_phone_number
    if not phone:
        return '<p class="muted" style="margin-top:1.25rem">Call the Kaayal number to talk to Paayal.</p>'
    digits = re.sub(r"\D", "", phone)
    return (
        f'<p style="margin-top:1.25rem"><a class=btn href="tel:+{_esc(digits)}" '
        f'style="text-decoration:none">Call {_esc(phone)}</a></p>'
    )


# --- landing ----------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def landing(request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        rows = session.exec(
            select(Boat, Operator.name)
            .join(Operator, Boat.operator_id == Operator.id)
            .where(Boat.active, Boat.verified_at.is_not(None), Operator.active)
            .order_by(Boat.name)
        ).all()

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

    demo_badge = " <span class='badge wait'>DEMO</span>"
    avail_ok = "<span class='badge ok'>available</span>"
    avail_off = "<span class='badge wait'>unavailable — Paayal can call you when it is</span>"
    boats = "".join(
        f'<div class=card><h3>{_esc(b.name)}'
        f'{demo_badge if b.source == "demo-seed" else ""}</h3>'
        f'<p class=muted style="margin:.15rem 0">with {_esc(op)}'
        f'{f" · up to {_esc(b.capacity)} guests" if b.capacity else ""}'
        f'{f" · from {_esc(b.embarkation_point)}" if b.embarkation_point else ""}</p>'
        f'<p style="margin:.4rem 0 0">{avail_ok if b.available else avail_off}</p></div>'
        for b, op in rows
    ) or (
        '<p class=muted>Verified boat listings are being added. '
        'Call Paayal and she’ll tell you what’s available today.</p>'
    )

    body = f"""
<h1 style="font-size:2.6rem">The backwaters,<br>a phone call away.</h1>
<p style="font-size:1.15rem;max-width:34rem">
  Paayal is Kaayal’s voice assistant. Call and ask — in <b>Malayalam</b> or <b>English</b> —
  about boat operators in Alappuzha, and leave a booking inquiry. The operator calls you
  back to confirm. No app, no forms, no account.</p>
{call_line}
<p class=muted small>Prefer the web? <a href="/boats">Browse the verified boats</a>
Paayal can tell you about.</p>
{_CONTOURS}

<h2>How it works</h2>
<ol style="padding-left:1.25rem">
  <li style="margin-bottom:.6rem"><b>Call</b> — Paayal answers in your language and can tell
      you about verified boats: capacity, embarkation point, the operator behind each one.</li>
  <li style="margin-bottom:.6rem"><b>Inquire</b> — leave your name, number, date, and group size.
      With your permission, the inquiry goes to the operator.</li>
  <li style="margin-bottom:.6rem"><b>Not available now?</b> — if a boat is unavailable or its
      operator can’t be reached, Paayal can call <i>you</i> back when that changes —
      only if you say yes, and she never calls for anything else.</li>
  <li><b>Confirm</b> — the operator calls you directly to confirm the trip and the price.
      Nothing is booked until they say yes.</li>
</ol>

<h2>Verified boats</h2>
{boats}
<p class=muted small><a href="/boats">See the full list with prices and amenities →</a></p>

<hr class=rule>
<p class=muted small><b>For operators.</b> Run a boat out of Alappuzha? Message us on
WhatsApp — a human verifies you, then you list your boats once, get booking
inquiries, and confirm by a call back.</p>
{operator_cta}
<p class=muted small>Every listing is verified by the Kaayal owner before callers hear about it.
Kaayal never confirms prices, availability, or bookings on its own — the operator always does.</p>
"""
    return _public(request,
        "Kaayal — Alappuzha boats by phone",
        body,
        description="Call Kaayal and talk to Paayal in Malayalam or English: verified Alappuzha boat operators, booking inquiries, and a call back to confirm.",
    )


# --- /boats -----------------------------------------------------------------

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


@router.get("/boats", response_class=HTMLResponse)
def boats_page(request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        rows = session.exec(
            select(Boat, Operator)
            .join(Operator, Boat.operator_id == Operator.id)
            .where(Boat.active, Boat.verified_at.is_not(None), Operator.active)
            .order_by(Boat.name)
        ).all()

    cards = "".join(_boat_card(b, op) for b, op in rows) or (
        '<p class=muted>Verified boat listings are being added. '
        'Call Paayal and she’ll tell you what’s available today.</p>'
    )
    body = f"""
<h1>Boats on the Kaayal list</h1>
<p class=muted>Owner-verified boats operating out of Alappuzha. Availability and
prices come from the operators themselves.</p>
{cards}
<hr class=rule>
<p class="muted small">Every listing here is verified by the Kaayal owner.
<b>Paayal never confirms bookings</b> — after you inquire, the operator calls you
back and confirms the trip and the price themselves.</p>
<p><a class=btn href="tel:+{_tel_digits(request)}" style="text-decoration:none">Call to send a booking inquiry</a></p>
"""
    return _public(request, "Boats — Kaayal", body,
                   description="Verified Alappuzha boat listings with prices and amenities.")


# --- /paayal ----------------------------------------------------------------

@router.get("/paayal", response_class=HTMLResponse)
def paayal_page(request: Request):
    call_line = _call_cta(request)
    body = f"""
<h1>Meet Paayal <span class="ml" lang="ml">(പായൽ)</span></h1>
<p style="font-size:1.15rem;max-width:34rem">
  Paayal is Kaayal’s voice assistant — a <b>Malayalam-first</b> voice on the other
  end of the Kaayal phone line. She also speaks English. You talk, she answers;
  there is nothing to install and nothing to type.</p>
{call_line}

<h2>What Paayal does</h2>
<ul style="padding-left:1.25rem">
  <li style="margin-bottom:.5rem">Answers questions about boat trips out of Alappuzha,
      in Malayalam or English.</li>
  <li style="margin-bottom:.5rem">Describes <b>verified</b> boats — capacity, embarkation
      point, amenities, and the operator behind each listing.</li>
  <li style="margin-bottom:.5rem">Takes booking inquiries: your name, number, preferred
      date, and group size go to the operator <b>only with your consent</b>.</li>
  <li>Arranges consented callbacks — if a boat or operator can’t be reached now,
      she can call you back when they can. <span class="muted small">In this
      prototype the return call is simulated; the consent, queue, and
      availability triggers are real.</span></li>
</ul>

<h2>What Paayal never does</h2>
<ul style="padding-left:1.25rem">
  <li style="margin-bottom:.5rem"><b>Confirms bookings.</b> Only the operator confirms,
      by calling you back. Until then nothing is booked.</li>
  <li style="margin-bottom:.5rem"><b>Confirms prices.</b> Quoted prices come from the
      operator; Paayal repeats them, she doesn’t guarantee them.</li>
  <li><b>Takes payments.</b> There is no checkout, no wallet, no card on file —
      you settle directly with the operator.</li>
</ul>

<hr class=rule>
<p class=muted small>Paayal shares your name and number with an operator only after
you say yes on the call. Say no, and nothing is shared.</p>
"""
    return _public(request, "Meet Paayal — Kaayal", body,
                   description="Paayal is Kaayal's Malayalam-first voice assistant. She answers questions and takes booking inquiries — she never confirms bookings or takes payments.")


# --- /explore ---------------------------------------------------------------

@router.get("/explore", response_class=HTMLResponse)
def explore_page(request: Request):
    body = """
<h1>Alappuzha and the backwaters</h1>
<p style="font-size:1.15rem;max-width:34rem">
  Alappuzha — older maps say Alleppey — is a canal town on the edge of Vembanad,
  Kerala’s largest lake. Behind the town, lakes, lagoons, and narrow canals link
  together into the waterways people call the backwaters.</p>

<h2>Trips from town</h2>
<p>Most local trips cast off from the <b>Finishing Point</b> and <b>Punnamada</b>
jetties near the town centre. From there, operators run small motor boats and
shikaras for an hour or two through the canals, as well as the larger
kettuvallam houseboats that cruise Vembanad — some for a day, some overnight.</p>
<p>What you see depends on the route: paddy fields below the waterline, village
jetties, toddy shops, and long open stretches of lake. Morning and late-afternoon
light are the kindest.</p>

<h2>Before you go</h2>
<p>Trip length, route, and price vary by boat and by season, and they are the
operator’s call — not ours. We don’t publish timings or tariffs here. Paayal can
describe verified boats on the phone, and the operator confirms the details
when they call you back.</p>
<p><a class=btn href="/boats" style="text-decoration:none">See verified boats</a></p>
"""
    return _public(request, "Explore Alappuzha — Kaayal", body,
                   description="The Alappuzha backwaters: trips from Finishing Point and Punnamada, and how Kaayal connects you to verified operators.")


# --- /before-you-book ---------------------------------------------------------

@router.get("/before-you-book", response_class=HTMLResponse)
def guide_page(request: Request):
    body = f"""
<h1>What to ask before you book an Alappuzha houseboat</h1>
<p class=muted>Five questions that save most of the trouble people run into
with houseboat bookings. The operator’s answers are theirs to give — these
are the things worth asking.</p>
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
<p style="margin-top:1.5rem">Not sure? Ask Paayal.
<a href="tel:+{_tel_digits(request)}">Call {_esc(request.app.state.settings.kaayal_phone_number)}</a>.</p>
<p class="muted small">Further reading:
<a href="https://www.onmanorama.com/travel/travel-news/2026/01/21/kerala-houseboats-defy-guidelines.html"
   target="_blank" rel="noopener">Onmanorama: Kerala houseboats defy guidelines</a>.</p>
"""
    return _public(
        request,
        "Alappuzha houseboat guide: what to ask before you book",
        body,
        description="Classification, registration, what is included, why prices differ. A plain-language checklist for booking an Alleppey houseboat.",
    )


# --- /dtpc-houseboat-counter --------------------------------------------------

@router.get("/dtpc-houseboat-counter", response_class=HTMLResponse)
def dtpc_page(request: Request):
    body = """
<h1>The DTPC houseboat counter — the official route</h1>
<p style="font-size:1.15rem;max-width:34rem">
  If you’d rather book through an official channel, the District Tourism
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
"""
    return _public(
        request,
        "Alappuzha DTPC houseboat counter: how it works",
        body,
        description="How the district tourism council's pre-paid houseboat counter works, and when to use it. Check current details with DTPC.",
    )


# --- /faq -------------------------------------------------------------------

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
     "Malayalam and English, including a mix of both in the same call."),
    ("Do I need an app?",
     "No. Just call the Kaayal number and talk."),
    ("Is Kaayal government-approved or operator-verified?",
     "No. Kaayal is an independent service and does not rank or endorse boats. "
     "Every listing is verified by the Kaayal owner before callers hear about "
     "it — to check a boat yourself, ask for its registration and Kerala "
     "Tourism classification."),
    ("Are the callbacks real?",
     "The callback system is real — consent, queueing and availability "
     "triggers all work. In this prototype Paayal’s return call is simulated "
     "and no real outbound phone call is placed."),
]


@router.get("/faq", response_class=HTMLResponse)
def faq_page(request: Request):
    items = "".join(
        f"<h3>{_esc(q)}</h3><p class=muted>{_esc(a)}</p>" for q, a in _FAQ
    )
    faq_ld = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in _FAQ
        ],
    }
    jsonld = f'<script type="application/ld+json">{json.dumps(faq_ld)}</script>'
    call_line = _call_cta(request)
    body = f"""
<h1>Straight answers</h1>
<p class=muted>What Kaayal does, what it doesn’t, and how your call is handled.</p>
{items}
<hr class=rule>
<p class=muted small>Still unsure? Call and ask Paayal directly — in Malayalam or English.</p>
{call_line}
"""
    return _public(
        request,
        "Kaayal FAQ: bookings, prices, languages, calls",
        body,
        description="Straight answers on what Kaayal does, what it does not do, and how your call is handled.",
        head_extra=jsonld,
    )


# --- robots + sitemap ---------------------------------------------------------

_PUBLIC_PATHS = [
    "/", "/boats", "/paayal", "/explore",
    "/before-you-book", "/dtpc-houseboat-counter", "/faq",
]


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
    urls = "".join(f"  <url><loc>{base}{p}</loc></url>\n" for p in _PUBLIC_PATHS)
    return Response(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}</urlset>\n",
        media_type="application/xml",
    )
