"""Operator portal — no login step: the unique unguessable URL IS the access
(owner decision, spec FR-08). Token stored hashed; raw token only in the URL.
"""

import hashlib
import re
import secrets
from urllib.parse import quote

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from app.callbacks import fire_boat_available, fire_booking_confirmed, fire_operator_reachable, process_due_callbacks
from app.db import Boat, BookingRequest, Operator, utcnow
from app.ui import esc as _esc, page as _page, status_badge as _status_badge

router = APIRouter(prefix="/portal")


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_token() -> str:
    return secrets.token_urlsafe(32)


def _wa_link(phone_digits: str, text: str) -> str:
    """Click-to-chat deep link — opens WhatsApp on the operator's own device
    with a prefilled message. Kaayal never sends messages itself."""
    return f"https://wa.me/{phone_digits}?text={quote(text)}"


_REACH_BADGE = '<span class="badge ok">reachable</span>'
_UNREACH_BADGE = '<span class="badge bad">unreachable</span>'
_AVAIL_BADGE = '<span class="badge ok">available</span>'
_UNAVAIL_BADGE = '<span class="badge wait">unavailable</span>'


def _get_operator(session: Session, token: str) -> Operator:
    op = session.exec(
        select(Operator).where(
            Operator.token_hash == hash_token(token),
            Operator.active,
            Operator.approved_at.is_not(None),  # pending signups get the same 404 as bad tokens
        )
    ).first()
    if not op:
        raise HTTPException(status_code=404, detail="not_found")
    return op


@router.get("/{token}", response_class=HTMLResponse)
def dashboard(token: str, request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        op = _get_operator(session, token)
        boats = session.exec(select(Boat).where(Boat.operator_id == op.id, Boat.active)).all()
        boat_ids = [b.id for b in boats]
        requests = []
        if boat_ids:
            requests = session.exec(
                select(BookingRequest)
                .where(BookingRequest.boat_id.in_(boat_ids))
                .order_by(BookingRequest.created_at.desc())
            ).all()
        boat_names = {b.id: b.name for b in boats}

    reach_badge = _REACH_BADGE if op.reachable else _UNREACH_BADGE
    reach_card = (
        f"<div class=card><p style='margin:0 0 .6rem'><b>You are {reach_badge}</b> "
        f"{'— callers can send you booking inquiries.' if op.reachable else '— callers are offered a callback instead, and Paayal rings them when you mark yourself reachable again.'}</p>"
        f"<form class=inline method=post action='/portal/{token}/toggle_reachable'>"
        f"<button class=secondary>{'Mark me unreachable' if op.reachable else 'Mark me reachable'}</button></form></div>"
    )

    rows = "".join(
        f"<tr><td>{_esc(b.name)}</td><td class=num>{_esc(b.capacity) if b.capacity else '—'}</td>"
        f"<td>{_esc(b.embarkation_point) if b.embarkation_point else '—'}</td>"
        f"<td>{_esc(b.price_display) if b.price_display else '—'}</td>"
        f"<td class=small>{_esc(', '.join(b.amenities)) if b.amenities else '—'}</td>"
        f"<td>{_status_badge('verified') if b.verified_at else _status_badge('pending verification')}</td>"
        f"<td>{_AVAIL_BADGE if b.available else _UNAVAIL_BADGE}</td>"
        f"<td class=actions><form class=inline method=post action='/portal/{token}/boats/{b.id}/toggle_available'>"
        f"<button class=secondary>{'Set unavailable' if b.available else 'Set available'}</button></form>"
        f"<form class=inline method=post action='/portal/{token}/boats/{b.id}/delete'"
        f" onsubmit='return confirm(\"Remove {_esc(b.name)}? Callers will stop hearing about it.\")'>"
        f"<button class=danger>Remove</button></form></td></tr>"
        for b in boats
    ) or "<tr><td colspan=8 class='muted small'>No boats yet — add your first one below.</td></tr>"

    def _req_card(r: BookingRequest) -> str:
        if r.status == "confirmed":
            wa = ""
            digits = re.sub(r"\D", "", r.customer_phone)
            if len(digits) >= 10:
                msg = (f"Hello {r.customer_name}, this is {op.name} from Kaayal "
                       f"about your boat request {r.public_id}")
                if r.preferred_date:
                    msg += f" on {r.preferred_date}"
                if r.group_size:
                    msg += f" for {r.group_size} guests"
                wa = (f" <a class=btn href='{_wa_link(digits, msg + '.')}'"
                      f" target='_blank' rel='noopener'>WhatsApp customer</a>")
            contact = (
                f"<p><b>Customer:</b> {_esc(r.customer_name)} — "
                f"<b>call</b> <a href='tel:{_esc(r.customer_phone)}'>{_esc(r.customer_phone)}</a>{wa}</p>"
            )
        elif r.status == "pending":
            contact = (f"<p><b>Customer:</b> {_esc(r.customer_name)} "
                       f"<span class='muted small'>(number revealed after you confirm)</span></p>")
        else:
            contact = (f"<p><b>Customer:</b> {_esc(r.customer_name)} "
                       f"<span class='muted small'>(number stays hidden — you didn't confirm)</span></p>")
        actions = ""
        if r.status == "pending":
            base = f"/portal/{token}/requests/{r.public_id}"
            nid = f"note-{_esc(r.public_id)}"
            actions = (
                f"<form method=post action='{base}/confirm' class=req-actions>"
                f"<label for='{nid}' class=sr-only>Note to the customer record (optional)</label>"
                f"<input id='{nid}' name=note maxlength=200 placeholder='Note (optional), e.g. pickup 9am'>"
                f"<button>Confirm</button>"
                f"<button class=secondary formaction='{base}/decline'>Decline</button>"
                f"<button class=danger formaction='{base}/block'"
                f" onclick='return confirm(\"Block this request? Use this for spam or abusive callers.\")'>Block</button>"
                f"</form>"
            )
        details = " · ".join(x for x in (
            f"Date {_esc(r.preferred_date)}" if r.preferred_date else "",
            f"{_esc(r.group_size)} guests" if r.group_size else "",
            f"via {_esc({'voice': 'call'}.get(r.source, r.source))}",
        ) if x)
        your_note = (f"<p class='muted small'><b>Your note:</b> {_esc(r.operator_note)}</p>"
                     if r.operator_note else "")
        quiet = "" if r.status == "pending" else " quiet"
        return (
            f"<div class='card req{quiet}'><p class=req-head><b>{_esc(r.public_id)}</b>"
            f"<span>{_esc(boat_names.get(r.boat_id, '?'))}</span>{_status_badge(r.status)}</p>"
            f"<p class='muted small'>{details}</p>"
            f"{f'<p class=small><b>Caller notes:</b> {_esc(r.notes)}</p>' if r.notes else ''}"
            f"{contact}"
            f"{your_note}"
            f"{actions}</div>"
        )

    pending = [r for r in requests if r.status == "pending"]
    earlier = [r for r in requests if r.status != "pending"]
    pending_html = "".join(_req_card(r) for r in pending) or (
        "<p class=muted>Nothing waiting for you. New inquiries from Paayal's callers land here.</p>")
    earlier_html = (
        f"<h2 id=earlier>Earlier requests<span class=n>{len(earlier)}</span></h2>"
        + "".join(_req_card(r) for r in earlier)
    ) if earlier else ""

    body = f"""
<header class="util-head">
<h1>{_esc(op.name)}</h1>
<p class=muted>Your Kaayal operator page. Bookmark it — this link is your login, so keep it private.</p>
<ul class="sectionnav" aria-label="Sections">
<li><a href="#requests">Waiting for you <span class="n{' hot' if pending else ''}">{len(pending)}</span></a></li>
<li><a href="#boats">Your boats <span class="n">{len(boats)}</span></a></li>
{f'<li><a href="#earlier">Earlier <span class="n">{len(earlier)}</span></a></li>' if earlier else ''}
</ul>
</header>
<div style="margin-top:2rem">{reach_card}</div>
<h2 id=requests>Waiting for your answer<span class=n>{len(pending)}</span></h2>
{pending_html}
<h2 id=boats>Your boats<span class=n>{len(boats)}</span></h2>
<div class=tablewrap><table><thead><tr><th>Name</th><th class=num>Guests</th><th>Boarding point</th><th>Price</th><th>Amenities</th><th>Listing</th><th>Today</th><th class=actions>Actions</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<details class=disclose{'' if boats else ' open'}>
<summary>Add a boat</summary>
<div>
<form method=post action='/portal/{token}/boats'>
<label for='boat-name'>Boat name</label>
<input id='boat-name' name=name placeholder='e.g. Lake Queen' required maxlength=120 autocomplete=off>
<label for='boat-type'>Boat type <span class=muted>(optional)</span></label>
<input id='boat-type' name=boat_type placeholder='e.g. houseboat, shikara, canoe' maxlength=60 autocomplete=off>
<label for='boat-cap'>How many guests</label>
<input id='boat-cap' name=capacity type=number min=1 inputmode=numeric placeholder='e.g. 8'>
<label for='boat-embark'>Boarding point</label>
<input id='boat-embark' name=embarkation_point placeholder='e.g. Alappuzha Finishing Point' maxlength=200 autocomplete=off>
<label for='boat-price'>Price to show callers <span class=muted>(optional)</span></label>
<input id='boat-price' name=price_display placeholder='e.g. ₹9,500/night' maxlength=60 autocomplete=off>
<label for='boat-amen'>Amenities <span class=muted>(comma-separated, optional)</span></label>
<input id='boat-amen' name=amenities placeholder='e.g. AC, meals, upper deck' maxlength=200 autocomplete=off>
<label for='boat-photo'>Photo link <span class=muted>(optional)</span></label>
<input id='boat-photo' name=photo_url type=url placeholder='https://…' maxlength=500 autocomplete=off>
<div style='margin-top:1rem'><button type=submit>Add boat</button></div>
</form>
<p class="muted small">New boats reach callers only after the Kaayal owner verifies them.</p>
</div>
</details>
{earlier_html}
"""
    nav = (
        '<nav class="topnav" aria-label="Operator">'
        '<span class="wordmark">Kaayal <span class="ml" lang="ml">കായൽ</span></span>'
        '<span class="role">Operator page</span>'
        '</nav>'
    )
    return HTMLResponse(_page(f"{op.name} — Kaayal portal", body,
                            description="Kaayal boat operator dashboard",
                            nav=nav, body_class="wide util", motion=False))


@router.post("/{token}/boats")
def add_boat(
    token: str,
    request: Request,
    name: str = Form(max_length=120),
    boat_type: str | None = Form(default=None, max_length=60),
    capacity: int | None = Form(default=None),
    embarkation_point: str | None = Form(default=None, max_length=200),
    price_display: str | None = Form(default=None, max_length=60),
    amenities: str | None = Form(default=None, max_length=200),
    photo_url: str | None = Form(default=None, max_length=500),
):
    engine = request.app.state.engine
    with Session(engine) as session:
        op = _get_operator(session, token)
        boat = Boat(
            operator_id=op.id,
            name=name.strip(),
            boat_type=(boat_type or "").strip() or None,
            capacity=capacity,
            embarkation_point=(embarkation_point or "").strip() or None,
            price_display=(price_display or "").strip() or None,
            amenities=[a.strip() for a in (amenities or "").split(",") if a.strip()],
            photo_urls=[photo_url.strip()] if photo_url and photo_url.strip() else [],
            source="operator-submitted",
        )
        session.add(boat)
        session.commit()
    return RedirectResponse(f"/portal/{token}", status_code=303)


@router.post("/{token}/toggle_reachable")
def toggle_reachable(token: str, request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        op = _get_operator(session, token)
        op.reachable = not op.reachable
        if op.reachable:  # back online → requeue "operator unreachable" callbacks
            fire_operator_reachable(session, op)
        session.commit()
    return RedirectResponse(f"/portal/{token}", status_code=303)


@router.post("/{token}/boats/{boat_id}/delete")
def delete_boat(token: str, boat_id: int, request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        op = _get_operator(session, token)
        boat = session.get(Boat, boat_id)
        if boat and boat.operator_id == op.id:
            boat.active = False
            boat.updated_at = utcnow()
            session.commit()
    return RedirectResponse(f"/portal/{token}", status_code=303)


@router.post("/{token}/boats/{boat_id}/toggle_available")
def toggle_boat_available(token: str, boat_id: int, request: Request):
    engine = request.app.state.engine
    with Session(engine) as session:
        op = _get_operator(session, token)
        boat = session.get(Boat, boat_id)
        if boat and boat.operator_id == op.id:
            boat.available = not boat.available
            boat.updated_at = utcnow()
            if boat.available:  # back on the market → requeue matching callbacks
                fire_boat_available(session, boat)
            session.commit()
    return RedirectResponse(f"/portal/{token}", status_code=303)


def _transition(token: str, public_id: str, request: Request, target: str, note: str | None = None):
    engine = request.app.state.engine
    with Session(engine) as session:
        op = _get_operator(session, token)
        req = session.exec(
            select(BookingRequest).where(BookingRequest.public_id == public_id)
        ).first()
        if not req:
            raise HTTPException(status_code=404, detail="not_found")
        boat = session.get(Boat, req.boat_id) if req.boat_id else None
        if not boat or boat.operator_id != op.id:
            raise HTTPException(status_code=404, detail="not_found")
        if req.status == "pending":
            req.status = target
            req.operator_note = (note or "").strip() or None
            req.updated_at = utcnow()
            session.commit()
            if target == "confirmed":
                fire_booking_confirmed(session, req, boat, op)
    if target == "confirmed":
        # Attempt the customer notify call immediately rather than waiting
        # for the background tick; WhatsApp fallback fires on final no_answer.
        process_due_callbacks(
            engine,
            request.app.state.callback_provider,
            settings=request.app.state.settings,
            ignore_window=request.app.state.settings.demo_ignore_call_window,
        )
    return RedirectResponse(f"/portal/{token}", status_code=303)


@router.post("/{token}/requests/{public_id}/confirm")
def confirm_request(token: str, public_id: str, request: Request,
                    note: str | None = Form(default=None, max_length=200)):
    return _transition(token, public_id, request, "confirmed", note)


@router.post("/{token}/requests/{public_id}/decline")
def decline_request(token: str, public_id: str, request: Request,
                    note: str | None = Form(default=None, max_length=200)):
    return _transition(token, public_id, request, "declined", note)


@router.post("/{token}/requests/{public_id}/block")
def block_request(token: str, public_id: str, request: Request,
                  note: str | None = Form(default=None, max_length=200)):
    return _transition(token, public_id, request, "blocked", note)
