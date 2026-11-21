"""Owner admin view — minimal HTML, token via ?t=<ADMIN_TOKEN> env secret.
Operators get portal URLs here; owner verifies boats and triages boat-less requests.
"""

import hmac

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from app.db import Boat, BookingRequest, Operator, utcnow
from app.portal import hash_token, new_token
from app.ui import esc as _esc, page as _page, status_badge as _status_badge

router = APIRouter(prefix="/admin")


def _check_admin(request: Request, t: str | None) -> str:
    expected = request.app.state.settings.admin_token
    if not expected:
        raise HTTPException(status_code=503, detail="admin_not_configured")
    if not t or not hmac.compare_digest(t, expected):
        raise HTTPException(status_code=401, detail="unauthorized")
    return t


@router.get("", response_class=HTMLResponse)
def admin_home(request: Request, t: str | None = None):
    _check_admin(request, t)
    engine = request.app.state.engine
    with Session(engine) as session:
        operators = session.exec(select(Operator).where(Operator.active)).all()
        boats = session.exec(select(Boat, Operator.name).join(Operator, Boat.operator_id == Operator.id).where(Boat.active)).all()
        requests = session.exec(select(BookingRequest).order_by(BookingRequest.created_at.desc())).all()

    op_rows = "".join(
        f"<tr><td>{o.id}</td><td>{_esc(o.name)}</td><td>{_esc(o.phone)}</td>"
        f"<td><code>/portal/&lt;token&gt;</code> (reissue not supported — create a new operator)</td></tr>"
        for o in operators
    ) or "<tr><td colspan=4>No operators yet.</td></tr>"

    boat_rows = "".join(
        f"<tr><td>{b.id}</td><td>{_esc(b.name)}</td><td>{_esc(op)}</td>"
        f"<td>{_status_badge('verified') if b.verified_at else _status_badge('unverified')}</td>"
        f"<td>{'' if b.verified_at else f'<form class=inline method=post action=/admin/boats/{b.id}/verify?t={t}><button>Verify</button></form>'}</td></tr>"
        for b, op in boats
    ) or "<tr><td colspan=5>No boats.</td></tr>"

    req_rows = "".join(
        f"<tr><td>{_esc(r.public_id)}</td><td>{_esc(r.customer_name)}</td><td>{_esc(r.customer_phone)}</td>"
        f"<td>boat #{r.boat_id or '— triage'}</td><td>{_esc(r.preferred_date)}</td>"
        f"<td>{_esc(str(r.group_size)) if r.group_size else '—'}</td><td>{_status_badge(r.status)}</td></tr>"
        for r in requests
    ) or "<tr><td colspan=7>No requests.</td></tr>"

    body = f"""
<h1>Owner admin</h1>
<p class=muted>Operators, listings, and every booking request.</p>
<h2>Operators</h2>
<table><thead><tr><th>#</th><th>Name</th><th>Phone</th><th>Portal link</th></tr></thead><tbody>{op_rows}</tbody></table>
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
<table><thead><tr><th>ID</th><th>Customer</th><th>Phone</th><th>Boat</th><th>Date</th><th>Group</th><th>Status</th></tr></thead><tbody>{req_rows}</tbody></table>
"""
    return HTMLResponse(_page("Kaayal admin", body, description="Kaayal owner admin"))


@router.post("/operators", response_class=HTMLResponse)
def create_operator(request: Request, t: str | None = None, name: str = Form(max_length=120), phone: str = Form(max_length=32)):
    _check_admin(request, t)
    token = new_token()
    engine = request.app.state.engine
    with Session(engine) as session:
        op = Operator(name=name.strip(), phone=phone.strip(), token_hash=hash_token(token))
        session.add(op)
        session.commit()
    base = request.app.state.settings.kaayal_public_base_url.rstrip("/")
    url = f"{base}/portal/{token}"
    body = f"""
<h1>Operator created</h1>
<div class=card>
<p><b>{_esc(name)}</b> — share this portal link with the operator (it is their only access; keep it private):</p>
<p><code>{_esc(url)}</code></p>
<p class="muted small">Raw tokens are never stored — if the link is lost, create a new operator.</p>
</div>
<p><a href='/admin?t={_esc(t)}'>← Back to admin</a></p>
"""
    return HTMLResponse(_page("Operator created — Kaayal", body))


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
