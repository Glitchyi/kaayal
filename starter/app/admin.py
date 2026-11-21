"""Owner admin view — minimal HTML, token via ?t=<ADMIN_TOKEN> env secret.
Operators get portal URLs here; owner verifies boats and triages boat-less requests.
"""

import hmac

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from app.callbacks import ACTIVE as _CB_ACTIVE, MAX_ATTEMPTS as _CB_MAX_ATTEMPTS, process_due_callbacks
from app.db import Boat, BookingRequest, CallbackAttempt, CallbackRequest, Operator, utcnow
from app.portal import hash_token, new_token
from app.ui import esc as _esc, page as _page, status_badge as _status_badge
from app.wa_notify import notify_portal_link

router = APIRouter(prefix="/admin")


def _check_admin(request: Request, t: str | None) -> str:
    expected = request.app.state.settings.admin_token
    if not expected:
        raise HTTPException(status_code=503, detail="admin_not_configured")
    if not t or not hmac.compare_digest(t, expected):
        raise HTTPException(status_code=401, detail="unauthorized")
    return t


def _portal_link_page(title: str, name: str, url: str, t: str, note: str) -> HTMLResponse:
    """One-time display of a raw portal URL — the only place a token is ever shown."""
    body = f"""
<h1>{title}</h1>
<div class=card>
<p><b>{_esc(name)}</b> — share this portal link with the operator (it is their only access; keep it private):</p>
<p><code>{_esc(url)}</code></p>
<p class="muted small">{_esc(note)}</p>
</div>
<p><a href='/admin?t={_esc(t)}'>← Back to admin</a></p>
"""
    return HTMLResponse(_page(f"{title} — Kaayal", body))


def _fmt_dt(dt) -> str:
    return _esc(dt.strftime("%d %b %Y %H:%M")) if dt else "—"


def _op_row(o: Operator, t: str) -> str:
    badge = '<span class="badge ok">active</span>' if o.active else '<span class="badge bad">inactive</span>'
    approve = ""
    if o.approved_at is None:
        badge += f" {_status_badge('pending approval')}"
        approve = (
            f"<form class=inline method=post action='/admin/operators/{o.id}/approve?t={t}'>"
            f"<button>Approve</button></form> "
        )
    verb, label, cls = ("deactivate", "Deactivate", "danger") if o.active else ("reactivate", "Reactivate", "secondary")
    return (
        f"<tr><td>{o.id}</td><td>{_esc(o.name)}</td><td>{_esc(o.phone)}</td>"
        f"<td>{_status_badge(o.source)}</td><td>{badge}</td>"
        f"<td>{approve}<form class=inline method=post action='/admin/operators/{o.id}/reissue?t={t}'>"
        f"<button class=secondary>Reissue link</button></form> "
        f"<form class=inline method=post action='/admin/operators/{o.id}/{verb}?t={t}'>"
        f"<button class={cls}>{label}</button></form></td></tr>"
    )


def _cb_rows(cbs: list[CallbackRequest], attempts: dict[int, list[CallbackAttempt]], t: str) -> str:
    out = []
    for cb in cbs:
        actions = ""
        if cb.status in _CB_ACTIVE:
            actions = (
                f"<form class=inline method=post action='/admin/callbacks/{cb.id}/cancel?t={t}'>"
                f"<button class=danger>Cancel</button></form>"
            )
        out.append(
            f"<tr><td>{_esc(cb.public_id)}</td>"
            f"<td>{_esc(cb.customer_name)}<br><span class='muted small'>{_esc(cb.customer_phone)}</span></td>"
            f"<td>{_status_badge(cb.reason)}</td><td>{_status_badge(cb.status)}</td>"
            f"<td>{cb.attempts_this_trigger}/{_CB_MAX_ATTEMPTS}</td>"
            f"<td class=small>{_fmt_dt(cb.next_attempt_at)}</td>"
            f"<td class=small>{_fmt_dt(cb.expires_at)}</td><td>{actions}</td></tr>"
        )
        att = attempts.get(cb.id, [])
        if att:
            items = "".join(
                f"<li>{_fmt_dt(a.attempted_at)} — {_esc(a.outcome)} · {_esc(a.provider)}</li>"
                for a in att
            )
            out.append(f"<tr><td colspan=8><ul class='muted small' style='margin:.2rem 0 .6rem'>{items}</ul></td></tr>")
    return "".join(out) or "<tr><td colspan=8>No callbacks.</td></tr>"


@router.get("", response_class=HTMLResponse)
def admin_home(request: Request, t: str | None = None):
    _check_admin(request, t)
    engine = request.app.state.engine
    with Session(engine) as session:
        operators = session.exec(select(Operator).order_by(Operator.id)).all()
        boats = session.exec(select(Boat, Operator.name).join(Operator, Boat.operator_id == Operator.id).where(Boat.active)).all()
        requests = session.exec(select(BookingRequest).order_by(BookingRequest.created_at.desc())).all()
        cbs = session.exec(select(CallbackRequest).order_by(CallbackRequest.created_at.desc())).all()
        attempts_by_cb: dict[int, list[CallbackAttempt]] = {}
        for a in session.exec(select(CallbackAttempt).order_by(CallbackAttempt.attempted_at)).all():
            attempts_by_cb.setdefault(a.callback_id, []).append(a)

    op_rows = "".join(_op_row(o, t) for o in operators) or "<tr><td colspan=6>No operators yet.</td></tr>"

    boat_rows = "".join(
        f"<tr><td>{b.id}</td><td>{_esc(b.name)}</td><td>{_esc(op)}</td>"
        f"<td>{_status_badge('verified') if b.verified_at else _status_badge('unverified')}</td>"
        f"<td>{'' if b.verified_at else f'<form class=inline method=post action=/admin/boats/{b.id}/verify?t={t}><button>Verify</button></form>'}</td></tr>"
        for b, op in boats
    ) or "<tr><td colspan=5>No boats.</td></tr>"

    req_rows = "".join(
        f"<tr><td>{_esc(r.public_id)}</td><td>{_esc(r.customer_name)}</td><td>{_esc(r.customer_phone)}</td>"
        f"<td>boat #{r.boat_id or '— triage'}</td><td>{_esc(r.preferred_date)}</td>"
        f"<td>{_esc(str(r.group_size)) if r.group_size else '—'}</td><td>{_status_badge(r.source)}</td>"
        f"<td class='muted small'>{_esc(r.operator_note) if r.operator_note else '—'}</td>"
        f"<td>{_status_badge(r.status)}</td></tr>"
        for r in requests
    ) or "<tr><td colspan=9>No requests.</td></tr>"

    cb_rows = _cb_rows(cbs, attempts_by_cb, t)

    body = f"""
<h1>Owner admin</h1>
<p class=muted>Operators, listings, every booking request, and the callback queue.</p>
<h2>Operators</h2>
<table><thead><tr><th>#</th><th>Name</th><th>Phone</th><th>Source</th><th>Status</th><th>Actions</th></tr></thead><tbody>{op_rows}</tbody></table>
<div class=card>
<h3>Add operator</h3>
<form method=post action='/admin/operators?t={t}'>
<label for='op-name'>Operator name</label>
<input id='op-name' name=name placeholder='e.g. Raj Boat Service' required maxlength=120 autocomplete=off>
<label for='op-phone'>Phone</label>
<input id='op-phone' name=phone type=tel placeholder='+91…' required maxlength=32>
<div style='margin-top:1rem'><button type=submit>Create + get portal link</button></div>
</form>
</div>
<h2>Boats</h2>
<table><thead><tr><th>#</th><th>Name</th><th>Operator</th><th>Status</th><th></th></tr></thead><tbody>{boat_rows}</tbody></table>
<h2>All booking requests</h2>
<table><thead><tr><th>ID</th><th>Customer</th><th>Phone</th><th>Boat</th><th>Date</th><th>Group</th><th>Source</th><th>Operator note</th><th>Status</th></tr></thead><tbody>{req_rows}</tbody></table>
<h2>Callbacks</h2>
<p class=muted>Customers Paayal rings back — calls go out 09:00–18:00 IST, max {_CB_MAX_ATTEMPTS} tries per trigger.</p>
<form class=inline method=post action='/admin/callbacks/run_due?t={t}'><button class=secondary>Run due callbacks now</button></form>
<table><thead><tr><th>ID</th><th>Customer</th><th>Reason</th><th>Status</th><th>Tries</th><th>Next attempt</th><th>Expires</th><th></th></tr></thead><tbody>{cb_rows}</tbody></table>
<h2>Demo data</h2>
<div class=card>
<p class="muted small">Clearly-labeled demo inventory for walkthroughs. Seeding is idempotent; clearing removes the demo rows and their requests/callbacks.</p>
<form class=inline method=post action='/admin/demo/seed?t={t}'><button class=secondary>Seed demo data</button></form>
<form class=inline method=post action='/admin/demo/clear?t={t}'><button class=danger>Clear demo data</button></form>
</div>
"""
    return HTMLResponse(_page("Kaayal admin", body, description="Kaayal owner admin"))


@router.post("/operators", response_class=HTMLResponse)
def create_operator(request: Request, t: str | None = None, name: str = Form(max_length=120), phone: str = Form(max_length=32)):
    _check_admin(request, t)
    token = new_token()
    engine = request.app.state.engine
    with Session(engine) as session:
        # Admin-created operators are pre-approved — portal link works immediately.
        op = Operator(name=name.strip(), phone=phone.strip(), token_hash=hash_token(token), approved_at=utcnow())
        session.add(op)
        session.commit()
    base = request.app.state.settings.kaayal_public_base_url.rstrip("/")
    url = f"{base}/portal/{token}"
    return _portal_link_page(
        "Operator created", name, url, t,
        "Raw tokens are never stored — if the link is lost, reissue a new one from the admin list.",
    )


@router.post("/operators/{op_id}/reissue", response_class=HTMLResponse)
def reissue_operator_link(op_id: int, request: Request, t: str | None = None):
    _check_admin(request, t)
    token = new_token()
    engine = request.app.state.engine
    with Session(engine) as session:
        op = session.get(Operator, op_id)
        if not op:
            raise HTTPException(status_code=404, detail="not_found")
        op.token_hash = hash_token(token)
        name = op.name
        session.commit()
    base = request.app.state.settings.kaayal_public_base_url.rstrip("/")
    url = f"{base}/portal/{token}"
    return _portal_link_page(
        "Portal link reissued", name, url, t,
        "The previous link stopped working immediately. Raw tokens are never stored — if this link is lost, reissue again.",
    )


@router.post("/operators/{op_id}/deactivate")
def deactivate_operator(op_id: int, request: Request, t: str | None = None):
    return _set_operator_active(op_id, False, request, t)


@router.post("/operators/{op_id}/reactivate")
def reactivate_operator(op_id: int, request: Request, t: str | None = None):
    return _set_operator_active(op_id, True, request, t)


def _set_operator_active(op_id: int, active: bool, request: Request, t: str | None):
    _check_admin(request, t)
    engine = request.app.state.engine
    with Session(engine) as session:
        op = session.get(Operator, op_id)
        if not op:
            raise HTTPException(status_code=404, detail="not_found")
        op.active = active
        session.commit()
    return RedirectResponse(f"/admin?t={t}", status_code=303)


@router.post("/boats/{boat_id}/verify")
def verify_boat(boat_id: int, request: Request, t: str | None = None):
    _check_admin(request, t)
    engine = request.app.state.engine
    with Session(engine) as session:
        boat = session.get(Boat, boat_id)
        if not boat:
            raise HTTPException(status_code=404, detail="not_found")
        boat.verified_at = utcnow()
        boat.source = "owner-verified"
        boat.updated_at = utcnow()
        session.commit()
    return RedirectResponse(f"/admin?t={t}", status_code=303)


@router.post("/operators/{op_id}/approve", response_class=HTMLResponse)
def approve_operator(op_id: int, request: Request, t: str | None = None):
    """Approve a self-signup operator: stamp approval and mint their first
    real portal link (shown once, then never again — raw tokens aren't stored)."""
    _check_admin(request, t)
    token = new_token()
    engine = request.app.state.engine
    with Session(engine) as session:
        op = session.get(Operator, op_id)
        if not op:
            raise HTTPException(status_code=404, detail="not_found")
        op.approved_at = utcnow()
        op.token_hash = hash_token(token)
        name = op.name
        phone = op.phone
        session.commit()
    base = request.app.state.settings.kaayal_public_base_url.rstrip("/")
    url = f"{base}/portal/{token}"
    sent = notify_portal_link(request.app.state.settings, phone, name, url)
    return _portal_link_page(
        "Operator approved", name, url, t,
        "Sent to the operator over WhatsApp. This link is also shown once — raw tokens are never stored; reissue if lost."
        if sent else
        "This link is shown once — send it to the operator now. Raw tokens are never stored; reissue a new one if it is lost.",
    )


@router.post("/callbacks/{cb_id}/cancel")
def cancel_callback(cb_id: int, request: Request, t: str | None = None):
    _check_admin(request, t)
    engine = request.app.state.engine
    with Session(engine) as session:
        cb = session.get(CallbackRequest, cb_id)
        if not cb:
            raise HTTPException(status_code=404, detail="not_found")
        cb.status = "opted_out"
        cb.updated_at = utcnow()
        session.commit()
    return RedirectResponse(f"/admin?t={t}", status_code=303)


@router.post("/callbacks/run_due")
def run_due_callbacks(request: Request, t: str | None = None):
    """Force-run the callback engine. force=True ignores next_attempt_at;
    the 09:00–18:00 IST window still applies unless the demo flag is on."""
    _check_admin(request, t)
    process_due_callbacks(
        request.app.state.engine,
        request.app.state.callback_provider,
        force=True,
        ignore_window=request.app.state.settings.demo_ignore_call_window,
        settings=request.app.state.settings,
    )
    return RedirectResponse(f"/admin?t={t}", status_code=303)


# (name, phone, reachable, boats[(name, available, price_display, amenities)])
_DEMO_INVENTORY = [
    ("Backwater Demo Cruises (DEMO)", "+910000000091", True,
     [("Demo Shikara", True, "₹2,000/hour (demo)", ["shaded deck", "life jackets"])]),
    ("Monsoon Houseboats (DEMO)", "+910000000092", False,
     [("Demo Deluxe", False, None, [])]),
]


@router.post("/demo/seed")
def seed_demo_data(request: Request, t: str | None = None):
    """Idempotent: every row is matched by name, so re-seeding never duplicates."""
    _check_admin(request, t)
    engine = request.app.state.engine
    with Session(engine) as session:
        for op_name, phone, reachable, boats in _DEMO_INVENTORY:
            op = session.exec(select(Operator).where(Operator.name == op_name)).first()
            if not op:
                op = Operator(
                    name=op_name, phone=phone, token_hash=hash_token(new_token()),
                    reachable=reachable, approved_at=utcnow(), source="demo-seed",
                )
                session.add(op)
                session.commit()
                session.refresh(op)
            for boat_name, available, price, amenities in boats:
                if session.exec(select(Boat).where(Boat.name == boat_name)).first():
                    continue
                session.add(Boat(
                    operator_id=op.id, name=boat_name, available=available,
                    price_display=price, amenities=amenities,
                    verified_at=utcnow(), source="demo-seed",
                ))
        session.commit()
    return RedirectResponse(f"/admin?t={t}", status_code=303)


@router.post("/demo/clear")
def clear_demo_data(request: Request, t: str | None = None):
    _check_admin(request, t)
    engine = request.app.state.engine
    with Session(engine) as session:
        demo_boats = session.exec(select(Boat).where(Boat.source == "demo-seed")).all()
        demo_ops = session.exec(select(Operator).where(Operator.source == "demo-seed")).all()
        boat_ids = {b.id for b in demo_boats}
        op_ids = {o.id for o in demo_ops}
        # Children first: requests and callback attempts/callbacks on demo rows.
        for req in session.exec(select(BookingRequest).where(BookingRequest.boat_id.in_(boat_ids))).all():
            session.delete(req)
        for cb in session.exec(select(CallbackRequest)).all():
            if cb.boat_id in boat_ids or cb.operator_id in op_ids:
                for att in session.exec(
                    select(CallbackAttempt).where(CallbackAttempt.callback_id == cb.id)
                ).all():
                    session.delete(att)
                session.delete(cb)
        for b in demo_boats:
            session.delete(b)
        for o in demo_ops:
            session.delete(o)
        session.commit()
    return RedirectResponse(f"/admin?t={t}", status_code=303)
