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
        f"<div class=card><p><b>Reachability:</b> {reach_badge} — "
        f"when unreachable, callers are offered a callback instead. "
        f"<form class=inline method=post action='/portal/{token}/toggle_reachable'>"
        f"<button class=secondary>{'Mark unreachable' if op.reachable else 'Mark reachable'}</button></form></p></div>"
    )

    rows = "".join(
        f"<tr><td>{_esc(b.name)}</td><td>{_esc(b.capacity) if b.capacity else '—'}</td>"
        f"<td>{_esc(b.embarkation_point)}</td>"
        f"<td>{_esc(b.price_display) if b.price_display else '—'}</td>"
        f"<td>{_esc(', '.join(b.amenities)) if b.amenities else '—'}</td>"
        f"<td>{_status_badge('verified') if b.verified_at else _status_badge('pending verification')}</td>"
        f"<td>{_AVAIL_BADGE if b.available else _UNAVAIL_BADGE}</td>"
        f"<td><form class=inline method=post action='/portal/{token}/boats/{b.id}/toggle_available'>"
        f"<button class=secondary>{'Set unavailable' if b.available else 'Set available'}</button></form> "
        f"<form class=inline method=post action='/portal/{token}/boats/{b.id}/delete'>"
        f"<button class='secondary'>Remove</button></form></td></tr>"
        for b in boats
    ) or "<tr><td colspan=8>No boats yet — add your first below.</td></tr>"

    req_cards = ""
    for r in requests:
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
                f"<b>call:</b> <a href='tel:{_esc(r.customer_phone)}'>{_esc(r.customer_phone)}</a>{wa}</p>"
            )
        else:
            contact = f"<p><b>Customer:</b> {_esc(r.customer_name)} <span class=muted small>(number revealed after you confirm)</span></p>"
        actions = ""
        if r.status == "pending":
            note_input = (
                "<input name=note maxlength=200 placeholder='note (optional)' "
                "style='display:inline-block;width:9rem;padding:.3rem .5rem'>"
            )
            actions = (
                f"<form class=inline method=post action='/portal/{token}/requests/{r.public_id}/confirm'>"
                f"{note_input}<button>Confirm</button></form> "
                f"<form class=inline method=post action='/portal/{token}/requests/{r.public_id}/decline'>"
                f"{note_input}<button class=secondary>Decline</button></form> "
                f"<form class=inline method=post action='/portal/{token}/requests/{r.public_id}/block'>"
                f"{note_input}<button class=danger>Block</button></form>"
            )
        req_cards += (
            f"<div class=card><p><b>{_esc(r.public_id)}</b> · {_esc(boat_names.get(r.boat_id, '?'))} · "
            f"{_status_badge(r.status)} <span class='badge muted'>{_esc(r.source)}</span></p>"
            f"<p class=muted>Date: {_esc(r.preferred_date) or '—'} · Group: {_esc(r.group_size) if r.group_size else '—'}"
            f"{' · Notes: ' + _esc(r.notes) if r.notes else ''}</p>{contact}"
            f"{f'<p class=muted><b>Your note:</b> {_esc(r.operator_note)}</p>' if r.operator_note else ''}"
            f"{actions}</div>"
        )
    if not req_cards:
        req_cards = "<p class=muted>No booking requests yet.</p>"

    body = f"""
<h1>{_esc(op.name)}</h1>
<p class=muted>Your Kaayal operator dashboard.</p>
{reach_card}
<h2>Your boats</h2>
<table><thead><tr><th>Name</th><th>Capacity</th><th>Embarkation</th><th>Price</th><th>Amenities</th><th>Status</th><th>Available</th><th></th></tr></thead>
<tbody>{rows}</tbody></table>
<div class=card>
<h3>Add a boat</h3>
<form method=post action='/portal/{token}/boats'>
<label for='boat-name'>Boat name</label>
<input id='boat-name' name=name placeholder='e.g. Lake Queen' required maxlength=120 autocomplete=off>
<label for='boat-type'>Boat type <span class=muted>(optional)</span></label>
<input id='boat-type' name=boat_type placeholder='e.g. houseboat, shikara, canoe' maxlength=60 autocomplete=off>
<label for='boat-cap'>Capacity</label>
<input id='boat-cap' name=capacity type=number min=1 inputmode=numeric placeholder='e.g. 8'>
<label for='boat-embark'>Embarkation point</label>
<input id='boat-embark' name=embarkation_point placeholder='e.g. Alappuzha Finishing Point' maxlength=200 autocomplete=off>
<label for='boat-price'>Price display <span class=muted>(optional)</span></label>
<input id='boat-price' name=price_display placeholder='e.g. ₹9,500/night' maxlength=60 autocomplete=off>
<label for='boat-amen'>Amenities <span class=muted>(comma-separated, optional)</span></label>
<input id='boat-amen' name=amenities placeholder='e.g. AC, meals, upper deck' maxlength=200 autocomplete=off>
<label for='boat-photo'>Photo URL <span class=muted>(optional)</span></label>
<input id='boat-photo' name=photo_url type=url placeholder='https://…' maxlength=500 autocomplete=off>
<div style='margin-top:1rem'><button type=submit>Add boat</button></div>
</form>
<p class="muted small">New boats reach callers only after the Kaayal owner verifies them.</p>
</div>
<h2>Booking requests</h2>
{req_cards}
"""
    return HTMLResponse(_page(f"{op.name} — Kaayal portal", body,
                            description="Kaayal boat operator dashboard"))


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
