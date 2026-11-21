"""Public site — Backwater Editorial pages.

Honesty contract (prototype): listings are owner-verified but Paayal never
confirms bookings or prices; demo-seeded inventory carries a DEMO badge;
WhatsApp onboarding is a demo path; nothing here is a confirmed booking.
"""

import re
from urllib.parse import quote

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.db import Boat, BookingRequest, Operator
from app.portal import hash_token, new_token
from app.requests_api import _next_public_id
from app.ui import esc as _esc, page as _page, status_badge as _status_badge

router = APIRouter()

# Same rule as the voice tool (app/requests_api.py).
_PHONE_RE = re.compile(r"^[+0-9][0-9 ()-]{5,24}$")

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
        '<a class="navlink" href="/join">For operators</a>'
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
        "nothing on this site is a confirmed booking.</p>"
        f"{nums_html}</footer>"
    )


def _public(request: Request, title: str, body: str, description: str = "") -> HTMLResponse:
    return HTMLResponse(_page(title, body, description=description,
                              nav=_nav(request), footer=_footer(request)))


def _call_cta(request: Request) -> str:
    phone = request.app.state.settings.kaayal_phone_number
    if not phone:
        return '<p class="muted" style="margin-top:1.25rem">Call the Kaayal number to talk to Paayal.</p>'
    digits = re.sub(r"\D", "", phone)
    return (
        f'<p style="margin-top:1.25rem"><a class=btn href="tel:+{_esc(digits)}" '
        f'style="text-decoration:none">Call {_esc(phone)}</a></p>'
    )


def _callback_hint(request: Request) -> str:
    """The honest line shown when a boat/operator can't take a request now."""
    phone = request.app.state.settings.kaayal_phone_number
    if phone:
        return f"call {_esc(phone)} and Paayal can arrange a callback"
    return "call Kaayal and Paayal can arrange a callback"


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
        f'<p class="muted small">No WhatsApp? <a href="/join">Sign up on the web instead</a>.</p>'
        if wa
        else '<p style="margin-top:.75rem"><a class=btn href="/join" '
             'style="text-decoration:none">Join as an operator</a></p>'
    )

    boats = "".join(
        f'<div class=card><h3>{_esc(b.name)}</h3>'
        f'<p class=muted style="margin:.15rem 0">with {_esc(op)}'
        f'{f" · up to {_esc(b.capacity)} guests" if b.capacity else ""}'
        f'{f" · from {_esc(b.embarkation_point)}" if b.embarkation_point else ""}</p></div>'
        for b, op in rows
    ) or (
        '<p class=muted>Verified boat listings are being added. '
        'Call Paayal and she’ll tell you what’s available today.</p>'
    )

    body = f"""
<h1 style="font-size:2.6rem">The backwaters,<br>a phone call away.</h1>
<p style="font-size:1.15rem;max-width:34rem">
  Paayal is Kaayal’s voice assistant. Call and ask — in <b>Malayalam</b> or <b>English</b> —
  about boat operators in Alappuzha, and leave a booking request. The operator calls you
  back to confirm. No app, no forms, no account.</p>
{call_line}
<p class=muted small>Prefer the web? <a href="/boats">Browse verified boats</a> or
<a href="/inquire">send a booking inquiry</a>.</p>
{_CONTOURS}

<h2>How it works</h2>
<ol style="padding-left:1.25rem">
  <li style="margin-bottom:.6rem"><b>Call</b> — Paayal answers in your language and can tell
      you about verified boats: capacity, embarkation point, the operator behind each one.</li>
  <li style="margin-bottom:.6rem"><b>Request</b> — leave your name, number, date, and group size.
      With your permission, the request goes to the operator.</li>
  <li><b>Confirm</b> — the operator calls you directly to confirm the trip and the price.
      Nothing is booked until they say yes.</li>
</ol>

<h2>Verified boats</h2>
{boats}
<p class=muted small><a href="/boats">See the full list with prices and amenities →</a></p>

<hr class=rule>
<p class=muted small><b>For operators.</b> Run a boat out of Alappuzha? Message us on WhatsApp
or sign up here — you list your boats once, get booking requests, and confirm by a call back.</p>
{operator_cta}
<p class=muted small>Every listing is verified by the Kaayal owner before callers hear about it.
Kaayal never confirms prices, availability, or bookings on its own — the operator always does.</p>
"""
    return _public(request,
        "Kaayal — Alappuzha boats by phone",
        body,
        description="Call Kaayal and talk to Paayal in Malayalam or English: verified Alappuzha boat operators, booking requests, and a call back to confirm.",
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
<p><a class=btn href="/inquire" style="text-decoration:none">Send a booking inquiry</a></p>
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
      she can call you back when they can.</li>
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


# --- /inquire ---------------------------------------------------------------

def _inquire_boats(session: Session) -> list[tuple[Boat, str]]:
    """Boats a guest may pick in the form: verified + available, operator active."""
    return session.exec(
        select(Boat, Operator.name)
        .join(Operator, Boat.operator_id == Operator.id)
        .where(Boat.active, Boat.verified_at.is_not(None), Operator.active, Boat.available)
        .order_by(Boat.name)
    ).all()


def _inquire_form(request: Request, error: str = "", values: dict | None = None) -> HTMLResponse:
    v = values or {}
    engine = request.app.state.engine
    with Session(engine) as session:
        options = ['<option value="">No preference — general inquiry</option>']
        for b, op_name in _inquire_boats(session):
            sel = ' selected' if str(b.id) == str(v.get("boat_id", "")) else ""
            options.append(f'<option value="{b.id}"{sel}>{_esc(b.name)} — {_esc(op_name)}</option>')
    select_html = "".join(options)

    err = f'<div class="error-box" role="alert">{error}</div>' if error else ""
    checked = " checked" if v.get("consent") else ""
    body = f"""
<h1>Send a booking inquiry</h1>
<p class=muted>The same request Paayal takes over the phone, as a form. The
operator calls you back to confirm — <b>nothing is booked by submitting this</b>.</p>
{err}
<form method="post" action="/inquire">
  <label for="inq-name">Your name</label>
  <input id="inq-name" name="name" required maxlength="120" autocomplete="name"
         value="{_esc(v.get('name', ''))}">
  <label for="inq-phone">Phone number (with country code)</label>
  <input id="inq-phone" name="phone" type="tel" required maxlength="25" autocomplete="tel"
         placeholder="+91 …" value="{_esc(v.get('phone', ''))}">
  <label for="inq-boat">Boat</label>
  <select id="inq-boat" name="boat_id">{select_html}</select>
  <label for="inq-date">Preferred date or time <span class=muted>(optional)</span></label>
  <input id="inq-date" name="preferred_date" maxlength="40"
         placeholder="e.g. next Saturday morning" value="{_esc(v.get('preferred_date', ''))}">
  <label for="inq-group">Group size <span class=muted>(1–200, optional)</span></label>
  <input id="inq-group" name="group_size" inputmode="numeric" maxlength="4"
         value="{_esc(v.get('group_size', ''))}">
  <label for="inq-consent" style="margin-top:1.1rem">
    <input id="inq-consent" type="checkbox" name="consent" value="yes"
           style="width:auto;margin-right:.4rem"{checked}>
    I agree to share my name and number with the operator so they can call me back</label>
  <div style="margin-top:1.25rem"><button type="submit">Send inquiry</button></div>
</form>
<p class="muted small">We only pass your details to the operator you inquire about.
No marketing, no resale — they call you, that’s it.</p>
"""
    return _public(request, "Booking inquiry — Kaayal", body,
                   description="Send a booking inquiry to a verified Alappuzha boat operator. They call you back to confirm — nothing is booked yet.")


def _inquire_reject(request: Request, message: str) -> HTMLResponse:
    body = f"""
<h1>We couldn’t send that inquiry</h1>
<div class="error-box" role="alert">{message}</div>
<p class=muted>Your details were not saved or shared.</p>
<p><a href="/inquire">← Back to the inquiry form</a> · <a href="/boats">Browse boats</a></p>
"""
    return _public(request, "Inquiry not sent — Kaayal", body)


@router.get("/inquire", response_class=HTMLResponse)
def inquire_get(request: Request):
    return _inquire_form(request)


@router.post("/inquire", response_class=HTMLResponse)
def inquire_post(
    request: Request,
    name: str = Form(max_length=120),
    phone: str = Form(max_length=25),
    boat_id: str | None = Form(default=None),
    preferred_date: str | None = Form(default=None, max_length=40),
    group_size: str | None = Form(default=None),
    consent: str | None = Form(default=None),
):
    values = {
        "name": name, "phone": phone, "boat_id": boat_id or "",
        "preferred_date": preferred_date or "", "group_size": group_size or "",
        "consent": bool(consent),
    }
    # Mirror the voice flow (app/requests_api.py): consent first, then the
    # phone check, then boat availability/reachability — no row on rejection.
    if not consent:
        return _inquire_form(
            request,
            error="Please tick the consent box — we can’t pass your details to an operator without it.",
            values=values,
        )
    if not _PHONE_RE.match(phone.strip()):
        return _inquire_form(
            request,
            error="That phone number doesn’t look right — include the country code, e.g. +91 …",
            values=values,
        )
    gs = None
    if group_size and group_size.strip():
        try:
            gs = int(group_size.strip())
        except ValueError:
            gs = -1
        if not 1 <= gs <= 200:
            return _inquire_form(
                request,
                error="Group size should be a number between 1 and 200.",
                values=values,
            )
    bid = None
    if boat_id and boat_id.strip():
        try:
            bid = int(boat_id.strip())
        except ValueError:
            bid = -1

    engine = request.app.state.engine
    with Session(engine) as session:
        if bid is not None:
            boat = session.get(Boat, bid)
            if not boat or not boat.active or boat.verified_at is None:
                return _inquire_reject(
                    request,
                    "That boat isn’t listed right now — send a general inquiry instead, "
                    "or pick another boat.",
                )
            op = session.get(Operator, boat.operator_id)
            if not boat.available or (op and not op.reachable):
                return _inquire_reject(
                    request,
                    f"{_esc(boat.name)} is not available right now — "
                    f"{_callback_hint(request)}.",
                )
        req = BookingRequest(
            public_id=_next_public_id(session),
            boat_id=bid,
            customer_name=name.strip(),
            customer_phone=phone.strip(),
            consent_given=True,
            preferred_date=(preferred_date or "").strip() or None,
            group_size=gs,
            source="web",
        )
        session.add(req)
        session.commit()
        public_id = req.public_id

    body = f"""
<h1>Inquiry sent</h1>
<p style="font-size:1.15rem">Your reference is <b>{_esc(public_id)}</b> {_status_badge('pending')}</p>
<p>The operator will call you to confirm the trip and the price —
<b>nothing is booked yet</b>. If they can’t reach you, nothing happens.</p>
<p class=muted small>Keep the reference handy if you call us back. Kaayal never
confirms bookings itself; only the operator does, on the call.</p>
<p><a href="/boats">← Back to boats</a></p>
"""
    return _public(request, "Inquiry sent — Kaayal", body)


# --- /join ------------------------------------------------------------------

def _join_form(request: Request, error: str = "", values: dict | None = None) -> HTMLResponse:
    v = values or {}
    err = f'<div class="error-box" role="alert">{error}</div>' if error else ""
    body = f"""
<h1>Join Kaayal as an operator</h1>
<p class=muted>Run a boat out of Alappuzha? Leave your name and number. The Kaayal
team verifies operators by phone before listings go live — after approval we share
your private portal link, where you add boats and answer booking requests.</p>
{err}
<form method="post" action="/join">
  <label for="join-name">Your name or business name</label>
  <input id="join-name" name="name" required maxlength="120" autocomplete="organization"
         value="{_esc(v.get('name', ''))}">
  <label for="join-phone">Phone number (with country code)</label>
  <input id="join-phone" name="phone" type="tel" required maxlength="25" autocomplete="tel"
         placeholder="+91 …" value="{_esc(v.get('phone', ''))}">
  <div style="margin-top:1.25rem"><button type="submit">Request to join</button></div>
</form>
<p class="muted small">This is the web signup — the WhatsApp onboarding you may have
heard about is a demo. Either way, a human approves every operator.</p>
"""
    return _public(request, "For operators — Kaayal", body,
                   description="Alappuzha boat operators: join Kaayal. Verified by phone, then a private portal link for listings and booking requests.")


@router.get("/join", response_class=HTMLResponse)
def join_get(request: Request):
    return _join_form(request)


@router.post("/join", response_class=HTMLResponse)
def join_post(
    request: Request,
    name: str = Form(max_length=120),
    phone: str = Form(max_length=25),
):
    values = {"name": name, "phone": phone}
    if not _PHONE_RE.match(phone.strip()):
        return _join_form(
            request,
            error="That phone number doesn’t look right — include the country code, e.g. +91 …",
            values=values,
        )
    want_digits = re.sub(r"\D", "", phone)

    engine = request.app.state.engine
    with Session(engine) as session:
        # Match by normalized digits so "+91 94003 54625" == "919400354625".
        existing = next(
            (o for o in session.exec(select(Operator)).all()
             if re.sub(r"\D", "", o.phone) == want_digits),
            None,
        )
        if existing is not None:
            hint = _callback_hint(request)
            body = f"""
<h1>Already registered</h1>
<p>That number is already on the Kaayal operator list — {hint}
and we’ll re-issue your portal link.</p>
<p class=muted small>For safety we never send a portal link twice or to a new
number without checking it’s really you.</p>
<p><a href="/">← Back to Kaayal</a></p>
"""
            return _public(request, "Already registered — Kaayal", body)
        op = Operator(
            name=name.strip(),
            phone=f"+{want_digits}",
            token_hash=hash_token(new_token()),
            approved_at=None,
            source="web-signup",
        )
        session.add(op)
        session.commit()

    body = """
<h1>Request received</h1>
<p>Your signup is <b>pending verification</b> — the Kaayal team will call to check
the details, then share your portal link after approval.</p>
<p class=muted small>Your portal link is private and unguessable; keep it safe
when it arrives. It’s the only way into your dashboard.</p>
<p><a href="/">← Back to Kaayal</a></p>
"""
    return _public(request, "Pending verification — Kaayal", body)
