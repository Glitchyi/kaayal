"""Public landing page — Backwater Editorial product page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.db import Boat, Operator
from app.ui import DISPLAY_FONT, esc as _esc, page as _page

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

    phone = request.app.state.settings.kaayal_phone_number
    call_line = (
        f'<p style="margin-top:1.25rem"><a class=btn href="tel:{_esc(phone)}" '
        f'style="text-decoration:none">Call {_esc(phone)}</a></p>'
        if phone
        else '<p class="muted" style="margin-top:1.25rem">Call the Kaayal number to talk to Paayal.</p>'
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
<p style="font-family:{DISPLAY_FONT};font-size:1.15rem;color:var(--teal);margin:0 0 .5rem">
  Kaayal <span class="ml" lang="ml">(കായൽ)</span></p>
<h1 style="font-size:2.6rem">The backwaters,<br>a phone call away.</h1>
<p style="font-size:1.15rem;max-width:34rem">
  Paayal is Kaayal’s voice assistant. Call and ask — in <b>Malayalam</b> or <b>English</b> —
  about boat operators in Alappuzha, and leave a booking request. The operator calls you
  back to confirm. No app, no forms, no account.</p>
{call_line}
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

<hr class=rule>
<p class=muted small><b>For operators.</b> Run a boat out of Alappuzha? Ask the Kaayal team for
your portal link — you list your boats once, get booking requests, and confirm by a call back.</p>
<p class=muted small>Every listing is verified by the Kaayal owner before callers hear about it.
Kaayal never confirms prices, availability, or bookings on its own — the operator always does.</p>
"""
    return HTMLResponse(_page(
        "Kaayal — Alappuzha boats by phone",
        body,
        description="Call Kaayal and talk to Paayal in Malayalam or English: verified Alappuzha boat operators, booking requests, and a call back to confirm.",
    ))
