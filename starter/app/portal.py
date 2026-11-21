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


def _get_operator(session: Session, token: str) -> Operator:
    op = session.exec(
        select(Operator).where(Operator.token_hash == hash_token(token), Operator.active)
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

    rows = "".join(
        f"<tr><td>{_esc(b.name)}</td><td>{_esc(b.capacity) if b.capacity else '—'}</td>"
        f"<td>{_esc(b.embarkation_point)}</td>"
        f"<td>{_status_badge('verified') if b.verified_at else _status_badge('pending verification')}</td>"
        f"<td><form class=inline method=post action='/portal/{token}/boats/{b.id}/delete'>"
        f"<button class='secondary'>Remove</button></form></td></tr>"
        for b in boats
    ) or "<tr><td colspan=5>No boats yet — add your first below.</td></tr>"

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
            actions = (
                f"<form class=inline method=post action='/portal/{token}/requests/{r.public_id}/confirm'>"
                f"<button>Confirm</button></form> "
                f"<form class=inline method=post action='/portal/{token}/requests/{r.public_id}/block'>"
                f"<button class=danger>Block</button></form>"
            )
        req_cards += (
            f"<div class=card><p><b>{_esc(r.public_id)}</b> · {_esc(boat_names.get(r.boat_id, '?'))} · "
            f"{_status_badge(r.status)}</p>"
            f"<p class=muted>Date: {_esc(r.preferred_date) or '—'} · Group: {_esc(r.group_size) if r.group_size else '—'}"
            f"{' · Notes: ' + _esc(r.notes) if r.notes else ''}</p>{contact}{actions}</div>"
        )
    if not req_cards:
        req_cards = "<p class=muted>No booking requests yet.</p>"

    body = f"""
<h1>{_esc(op.name)}</h1>
<p class=muted>Your Kaayal operator dashboard.</p>
<h2>Your boats</h2>
<table><thead><tr><th>Name</th><th>Capacity</th><th>Embarkation</th><th>Status</th><th></th></tr></thead>
<tbody>{rows}</tbody></table>
<div class=card>
<h3>Add a boat</h3>
<form method=post action='/portal/{token}/boats'>
<label for='boat-name'>Boat name</label>
<input id='boat-name' name=name placeholder='e.g. Lake Queen' required maxlength=120 autocomplete=off>
<label for='boat-cap'>Capacity</label>
<input id='boat-cap' name=capacity type=number min=1 inputmode=numeric placeholder='e.g. 8'>
<label for='boat-embark'>Embarkation point</label>
<input id='boat-embark' name=embarkation_point placeholder='e.g. Alappuzha Finishing Point' maxlength=200 autocomplete=off>
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
    capacity: int | None = Form(default=None),
    embarkation_point: str | None = Form(default=None, max_length=200),
    photo_url: str | None = Form(default=None, max_length=500),
):
    engine = request.app.state.engine
    with Session(engine) as session:
        op = _get_operator(session, token)
        boat = Boat(
            operator_id=op.id,
            name=name.strip(),
            capacity=capacity,
            embarkation_point=(embarkation_point or "").strip() or None,
            photo_urls=[photo_url.strip()] if photo_url and photo_url.strip() else [],
            source="operator-submitted",
        )
        session.add(boat)
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


def _transition(token: str, public_id: str, request: Request, target: str):
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
            req.updated_at = utcnow()
            session.commit()
    return RedirectResponse(f"/portal/{token}", status_code=303)


@router.post("/{token}/requests/{public_id}/confirm")
def confirm_request(token: str, public_id: str, request: Request):
    return _transition(token, public_id, request, "confirmed")


@router.post("/{token}/requests/{public_id}/block")
def block_request(token: str, public_id: str, request: Request):
    return _transition(token, public_id, request, "blocked")
