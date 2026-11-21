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
from app import scenes
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

# --- shared chrome ----------------------------------------------------------

def _nav(request: Request) -> str:
    # On the landing page anchors are local; on subpages (/privacy) they
    # point back to the landing sections.
    pre = "" if request.url.path == "/" else "/"
    links = (("how", "How it works"), ("paayal", "Meet Paayal"), ("boats", "Boats"),
             ("before-you-book", "Before you book"), ("faq", "FAQ"))
    return (
        '<nav class="topnav" aria-label="Main">'
        '<a class="wordmark" href="/">Kaayal <span class="ml" lang="ml">കായൽ</span></a>'
        + "".join(f'<a class="navlink" href="{pre}#{a}">{t}</a>' for a, t in links)
        + "</nav>"
    )


# Floating call button — persistent CTA, flat teal, voicewave mark.
_FAB = (
    '<a class="fab-call" href="tel:+{digits}" aria-label="Call Paayal">'
    '<svg class="voicewave" width="18" height="14" viewBox="0 0 46 24" aria-hidden="true">'
    '<rect x="0" y="8" width="3" height="8" rx="1.5" fill="#F7F5EE"/>'
    '<rect x="7" y="4" width="3" height="16" rx="1.5" fill="#F7F5EE"/>'
    '<rect x="14" y="7" width="3" height="10" rx="1.5" fill="#F7F5EE"/>'
    '<rect x="21" y="3" width="3" height="18" rx="1.5" fill="#F7F5EE"/>'
    '<rect x="28" y="6" width="3" height="12" rx="1.5" fill="#F7F5EE"/>'
    '<rect x="35" y="5" width="3" height="14" rx="1.5" fill="#F7F5EE"/>'
    '<rect x="42" y="9" width="3" height="6" rx="1.5" fill="#F7F5EE"/>'
    '</svg><span>Call Paayal</span></a>'
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
    pre = "" if request.url.path == "/" else "/"
    return (
        '<footer class="site-footer">'
        "<p>Kaayal is a working prototype. Calls and booking inquiries are live, "
        "and consented callbacks are placed through Sarvam’s calling platform "
        "during calling hours. Nothing on this site is a confirmed booking; the "
        "operator always confirms.</p>"
        f'<p><a href="/privacy">Privacy &amp; consent</a> · '
        f'<a href="{pre}#before-you-book">Before you book</a> · '
        f'<a href="{pre}#faq">FAQ</a> · '
        '<a href="https://glitchyi.github.io/kaayal/" '
        'rel="noopener">Wiki</a></p>'
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
    digits = _tel_digits(request)
    fab = _FAB.format(digits=_esc(digits)) if digits else ""
    return HTMLResponse(_page(
        title, body + fab, description=description,
        nav=_nav(request), footer=_footer(request),
        canonical_url=base + request.url.path,
        head_extra=_ORG_JSONLD + head_extra,
        og_image=base + "/static/paayal.png",
        body_class="wide site",
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
        f'<p class="call_line" style="margin-top:1.25rem"><a class="btn" href="tel:+{_esc(digits)}" '
        f'style="text-decoration:none">Call {_esc(phone)}</a></p>'
    )


def _boat_card(b: Boat, op: Operator) -> str:
    """One ruled row of the listing — name and operator on the left, the facts
    a caller would ask about on the right. No card chrome."""
    demo = ' <span class="badge wait">DEMO</span>' if b.source == "demo-seed" else ""
    avail = (
        '<span class="badge ok">available</span>'
        if b.available
        else '<span class="badge wait">unavailable</span>'
    )
    facts = []
    if b.capacity:
        facts.append(f"Up to {_esc(b.capacity)} guests")
    if b.embarkation_point:
        facts.append(f"Boards at {_esc(b.embarkation_point)}")
    facts_html = "".join(f"<li>{f}</li>" for f in facts)
    price = (
        f'<p class="boat-price"><b>{_esc(b.price_display)}</b>'
        '<span class="muted small">set by the operator, confirmed on the call back</span></p>'
        if b.price_display else
        '<p class="boat-price muted small">Price on the call back, from the operator</p>'
    )
    chips = "".join(f'<span class="chip">{_esc(a)}</span>' for a in (b.amenities or []))
    chips_html = f'<p class="boat-chips">{chips}</p>' if chips else ""
    reach = (
        'This operator can’t be reached right now — Paayal can arrange a callback when they return.'
        if not op.reachable else
        'The operator is reachable — your inquiry goes straight to them.'
    )
    return (
        f'<article class="boat"><div class="boat-id"><h3>{_esc(b.name)}{demo}</h3>'
        f'<p class="muted">with {_esc(op.name)}</p>'
        f'{f"<ul class=boat-facts>{facts_html}</ul>" if facts_html else ""}</div>'
        f'<div class="boat-state"><p>{avail}</p>{price}{chips_html}'
        f'<p class="muted small">{reach}</p></div></article>'
    )


_FAQ = [
    ("Can I book a houseboat through Kaayal?",
     "Not directly. Paayal takes a booking inquiry and, with your consent, "
     "passes it to the operator, who calls you back to confirm the trip and the "
     "price. Nothing is booked until they say yes."),
    ("Does Kaayal show prices?",
     "Some operators add a price note to their listing, but the figure is "
     "theirs: Paayal repeats it and never guarantees it. The operator confirms "
     "the price on the call back."),
    ("Which languages does Paayal speak?",
     "Eleven: Malayalam, English, Hindi, Tamil, Telugu, Kannada, Bengali, "
     "Marathi, Gujarati, Punjabi and Odia. She answers in Malayalam first and "
     "switches to whichever you speak — mixing is fine too, like "
     "Malayalam and English in the same call."),
    ("Do I need an app?",
     "No. Just call the Kaayal number and talk."),
    ("Is Kaayal government-approved?",
     "No. Kaayal is an independent service and does not rank or endorse boats. "
     "The Kaayal owner reviews each listing before it goes live — a person, "
     "not a government or safety certification. To check a boat yourself, ask "
     "for its registration and Kerala Tourism classification."),
    ("Will Paayal call me back, and can I stop it?",
     "Only if you said yes on the call. Callbacks happen between 09:00 and "
     "18:00 IST, at most twice per request, and only about the inquiry you "
     "agreed to. Say “don’t call me” on any call and they stop."),
    ("Can I cancel a booking inquiry?",
     "There is nothing to cancel — an inquiry is not a booking. Tell the "
     "operator when they call, or call Paayal and ask her to withdraw it."),
]


# --- the page -----------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def landing(request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        rows = sorted(listed_boats(session), key=lambda row: row[0].name)

    call_line = _call_cta(request)
    digits = _tel_digits(request)
    asks = "".join(
        (f'<a class=ask href="tel:+{_esc(digits)}">{q}</a>' if digits
         else f'<p class=ask>{q}</p>')
        for q in (
            "“What boats go out of Alappuzha this weekend?”",
            "“Is anything available for six people on Saturday?”",
            "“What should I check before I book a houseboat?”",
            "“Call me back when that boat is free.”",
        )
    )
    demo_note = (
        '<p class="muted small">Boats badged <span class="badge wait">DEMO</span> '
        'are seeded walkthrough inventory — stand-ins so you can see the list, '
        'not real boats.</p>'
        if any(b.source == "demo-seed" for b, _ in rows) else ""
    )
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
        f'<details class="faq-item"><summary>{_esc(q)}</summary>'
        f'<p class=muted>{_esc(a)}</p></details>'
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
<header class="hero">
<div class="hero-copy">
<h1>The backwaters, a&nbsp;phone call away.</h1>
<p class=lead>
  Call Paayal, Kaayal’s voice assistant, and ask about boats in Alappuzha in
  <b>Malayalam</b>, <b>English</b> or nine more Indian languages. Leave an inquiry and the
  operator calls you back to confirm. No app, no forms.</p>
{call_line}
<p class="muted small">Prefer to scroll? <a href="#boats">See the boats</a>
Paayal can tell you about.</p>
</div>
<figure class="hero-art" data-plx="0.35">
  <span class="avatar-wrap"><picture><source srcset="/static/paayal.webp" type="image/webp"><img src="/static/paayal.png" alt="Paayal — Kaayal’s voice assistant" width="248" height="248"></picture></span>
  <figcaption>
    <span class="ml greeting" lang="ml">നമസ്കാരം — ഞാൻ പായൽ.</span>
    <span class="muted">Namaskaram — I’m Paayal. Malayalam first, and ten more languages.</span>
  </figcaption>
</figure>
</header>
{scenes.HOUSEBOAT}

<section id="how" class="ed">
<div class="ed-head">
<h2>Four steps, one phone call</h2>
<p class=muted>From your call to a confirmed trip.</p>
</div>
<ol class=steps>
  <li><b>Call</b><span>Paayal tells you about reviewed boats, in your language.</span></li>
  <li><b>Inquire</b><span>Leave your name, number, date and group size.</span></li>
  <li><b>Not free yet?</b><span>Paayal can call <i>you</i> back when it is — only if you ask.</span></li>
  <li><b>Confirm</b><span>The operator calls you back. Nothing is booked until they say yes.</span></li>
</ol>
</section>

<section id="paayal" class="band ed">
<div class="ed-head">
<h2>Meet Paayal, the voice on the other&nbsp;end</h2>
<p>Paayal (<span class="ml" lang="ml">പായൽ</span>) answers the Kaayal phone line —
<b>Malayalam-first</b>, and she follows you if you switch language mid-call. You talk,
she answers; there is nothing to install and nothing to type.</p>
<ul class="tongues" aria-label="Languages Paayal speaks">
  <li lang="ml" class="ml first">മലയാളം</li><li lang="en">English</li><li lang="hi">हिन्दी</li>
  <li lang="ta">தமிழ்</li><li lang="te">తెలుగు</li><li lang="kn">ಕನ್ನಡ</li><li lang="bn">বাংলা</li>
  <li lang="mr">मराठी</li><li lang="gu">ગુજરાતી</li><li lang="pa">ਪੰਜਾਬੀ</li><li lang="or">ଓଡ଼ିଆ</li>
</ul>
</div>
<div class=duo>
  <div>
    <h3>What Paayal does</h3>
    <ul class=ticks>
      <li>Describes <b>reviewed</b> boats — capacity, boarding point, amenities, and the
          operator behind each listing.</li>
      <li>Takes booking inquiries and passes them to the operator
          <b>only with your consent</b>.</li>
      <li>Calls you back when a boat or operator becomes available, if you asked her to.</li>
    </ul>
  </div>
  <div>
    <h3>What Paayal never does</h3>
    <ul class=ticks>
      <li><b>Confirms bookings.</b> Only the operator confirms, on the call back.</li>
      <li><b>Guarantees prices.</b> She repeats the operator’s figure; the operator confirms it.</li>
      <li><b>Takes payments.</b> No checkout, no card on file — you pay the operator directly.</li>
    </ul>
  </div>
</div>
<div class="asks-block">
<h3>Things you can ask her</h3>
<div class="asks">
  {asks}
</div>
<p class="muted small">Your name and number reach an operator only after you say yes on
the call. <a href="#privacy">How your details are handled →</a></p>
</div>
</section>

<section id="boats" class="ed">
<div class="ed-head">
<h2>Boats on the Kaayal list</h2>
<p class=muted>Reviewed and switched on by the Kaayal owner, operating out of
Alappuzha. Availability and prices come from the operators themselves.</p>
{call_line}
</div>
<div>
<div class="listing">
{boats}
</div>
{demo_note}
<p class="muted small">Reviewed means a person checked the listing — not a government or
safety certification. <b>Paayal never confirms bookings</b>; the operator does.</p>
</div>
</section>

{scenes.NET}

<section id="explore" class="ed">
<div class="ed-head">
<h2>Alappuzha and the backwaters</h2>
</div>
<div>
<p class=dropcap>Alappuzha — older maps say Alleppey — sits on the edge of Vembanad,
Kerala’s largest lake, where canals and lagoons knot into the backwaters. Most trips
cast off from the <b>Finishing Point</b> and <b>Punnamada</b> jetties: shikaras and small
motor boats for an hour or two, kettuvallam houseboats for a day or overnight.
<a href="https://www.keralatourism.org/districts/alappuzha/" target="_blank"
   rel="noopener">Kerala Tourism’s Alappuzha guide</a> has more.</p>
</div>
</section>

{scenes.CANOE}

<section id="before-you-book" class="band ed">
<div class="ed-head">
<h2>Five questions to ask before you book</h2>
<p class=muted>Before you pay a deposit — the operator’s answers are theirs to give.</p>
</div>
<div>
<ol class=flow>
  <li><b>Is the boat registered?</b> Ask for the
      boat’s registration before you pay anything.</li>
  <li><b>What is its Kerala Tourism
      classification?</b> Houseboats are classified Silver, Gold, or Diamond —
      <a href="https://www.keralatourism.org/cls/houseboats/Houseboat.htm"
         target="_blank" rel="noopener">Kerala Tourism’s classification page</a>
      explains the grades.</li>
  <li><b>What exactly is included?</b> Meals,
      air-conditioning hours, and cruise timings differ by operator — get them
      spelled out, not assumed.</li>
  <li><b>What is the price based on?</b> Weekday
      or peak dates, taxes, and the cancellation terms — ask before, not after.</li>
  <li><b>Which boat will you actually get?</b> Ask for photos of the actual
      boat, not a brochure boat.</li>
</ol>
<div id="dtpc">
<h3>Prefer an official route?</h3>
<p>The District Tourism Promotion Council (DTPC) runs a <b>pre-paid houseboat
counter</b> in Alappuzha: you pay at the counter and are allotted a boat. Kerala
Tourism lists an advance of <b>₹2,500</b> for this route —
<a href="https://www.keralatourism.org/houseboat/" target="_blank" rel="noopener">see
their houseboat page</a>, and confirm current timings and rates with DTPC before you travel.</p>
</div>
<p class="muted small">Further reading:
<a href="https://www.onmanorama.com/travel/travel-news/2026/01/21/kerala-houseboats-defy-guidelines.html"
   target="_blank" rel="noopener">Onmanorama: Kerala houseboats defy guidelines</a>.</p>
</div>
</section>

<section id="faq" class="ed">
<div class="ed-head">
<h2>Straight answers</h2>
<p class=muted>What Kaayal does, what it doesn’t, and how your call is handled.</p>
</div>
<div>
{faq_items}
</div>
</section>

<section id="privacy" class="band ed">
<div class="ed-head">
<h2>Your details</h2>
</div>
<div>
<p>Paayal saves your name, number, date and group size only after you agree on the
call, and only so the operator can call you back. No marketing list, no resale, no
cookies or trackers on this site. Details are <b>anonymized after 90 days</b>.
Callbacks happen only between 09:00 and 18:00 IST.</p>
<p><a href="/privacy">Read the full privacy &amp; consent page →</a></p>
</div>
</section>

<section id="closing" class="band-dark">
<div class="closing">
<div>
<h2>Talk to the backwaters.</h2>
<p class=lead>Call Paayal in Malayalam, English, or nine more Indian languages.
Leave an inquiry; the operator calls you back.</p>
{call_line}
</div>
<div class="closing-ops">
{scenes.HOUSEBOAT_MARK}
<div class="ops-copy">
<h3>For operators</h3>
<p>Run a boat out of Alappuzha? Message us on WhatsApp. We review your listing, then
callers can hear about your boats and send you inquiries to confirm.</p>
{operator_cta}
</div>
</div>
</div>
</section>
"""
    return _public(request,
        "Kaayal | Alappuzha boats by phone",
        body,
        description="Call Paayal about Alappuzha boats in Malayalam, English or nine more Indian languages. Leave a booking inquiry; the operator calls back to confirm.",
        head_extra=faq_jsonld,
    )


# --- full privacy page ---------------------------------------------------------

_PRIVACY_FACTS = """<dl class="facts">
<dt>What we collect</dt>
<dd><p>Only what a booking inquiry or callback needs: your <b>name</b>, <b>phone
number</b>, preferred date, and group size. Paayal asks for your permission on
the call before saving any of it — say no and nothing is stored.</p></dd>
<dt>What it’s for</dt>
<dd><p>So the operator can call you back and confirm the trip. That is the entire
purpose — there is no marketing list, no resale, no advertising.</p></dd>
<dt>Who sees it</dt>
<dd><p>The operator you inquire about sees your contact details when they confirm
your inquiry. The Kaayal owner can view inquiries in the admin dashboard.
Nobody else.</p></dd>
<dt>Callbacks</dt>
<dd><p>A callback is only queued after you agree on the call. Calls are attempted
only between <b>09:00 and 18:00 IST</b>, at most twice per request, and expire
after about a week. Say “don’t call me” to Paayal at any time — on any call —
and all pending callbacks for your number stop. Return calls are placed through
Sarvam’s calling platform; the consent and queue rules here govern when.</p></dd>
<dt>How long we keep it</dt>
<dd><p>Your name, phone number, and notes are <b>anonymized after 90 days</b>. The
inquiry keeps only its reference number and status afterwards.</p></dd>
<dt>Calls and recordings</dt>
<dd><p>Kaayal does not store call recordings or transcripts of your inbound calls
in its own database. Callback attempts store only their outcome (answered, no
answer, opted out), not call audio. Calls are carried by Sarvam’s voice
platform; whether they retain call audio is governed by Sarvam’s policies and
the account’s settings — that part is outside Kaayal’s own systems and we are
not able to state it here.</p></dd>
<dt>This website</dt>
<dd><p>No cookies, no analytics, no trackers, no forms that collect your details.
Just links to call or message us.</p></dd>
</dl>"""


@router.get("/privacy", response_class=HTMLResponse)
def privacy(request: Request):
    body = f"""
<section class="ed privacy-page">
<div class="ed-head">
<h1>Privacy &amp; consent</h1>
<p class=muted>What Kaayal does with your details — based on what the system
actually does today, not promises.</p>
<p><a href="/">← Back to Kaayal</a></p>
</div>
<div>
{_PRIVACY_FACTS}
<p class="muted small">Questions about your details? Call the Kaayal number and ask.</p>
</div>
</section>
"""
    return _public(request, "Privacy & consent | Kaayal", body,
                   description="What Kaayal stores from a call, who sees it, callback rules, and when details are anonymized.")


# --- redirects from the old multi-page URLs -------------------------------------

_OLD = {
    "/paayal": "#paayal",
    "/boats": "#boats",
    "/explore": "#explore",
    "/before-you-book": "#before-you-book",
    "/dtpc-houseboat-counter": "#dtpc",
    "/faq": "#faq",
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
        f"  <url><loc>{base}/</loc></url>\n  <url><loc>{base}/privacy</loc></url>\n</urlset>\n",
        media_type="application/xml",
    )
