"""Owner admin view — minimal HTML, token via ?t=<ADMIN_TOKEN> env secret.
Operators get portal URLs here; owner verifies boats and triages boat-less requests.
"""

import hmac
from datetime import timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select

from app.callbacks import ACTIVE as _CB_ACTIVE, MAX_ATTEMPTS as _CB_MAX_ATTEMPTS, fire_boat_available, process_due_callbacks
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


def _admin_nav(t: str | None = None) -> str:
    home = f"/admin?t={_esc(t)}" if t else "/"
    return (
        '<nav class="topnav" aria-label="Admin">'
        f'<a class="wordmark" href="{home}">Kaayal <span class="ml" lang="ml">കായൽ</span></a>'
        '<span class="role">Owner admin</span>'
        '<a class="navlink" href="/">View public site</a>'
        '</nav>'
    )


_IST = ZoneInfo("Asia/Kolkata")

# Plain-language labels for callback reasons and attempt outcomes.
_REASON = {
    "no_availability": "Boat was unavailable",
    "operator_unreachable": "Operator was unreachable",
    "booking_confirmed": "Tell customer: confirmed",
}


def _reason(code: str | None) -> str:
    return _esc(_REASON.get(code, (code or "—").replace("_", " ")))


# Friendly labels for machine `source` values — rendered as muted text,
# not badges (badges are reserved for product status).
_SRC = {
    "admin": "admin", "wa-demo": "whatsapp", "demo-seed": "demo",
    "operator-submitted": "operator", "owner-verified": "owner",
    "voice": "call", "callback": "callback",
}


def _src(s: str | None) -> str:
    return f'<span class="muted small">{_esc(_SRC.get(s, s or "—"))}</span>'


# Whitelisted post-action notices (redirect → ?done=<key>#section).
_DONE = {
    "boat_verified": "Boat verified — it's now listed for callers.",
    "op_deactivated": "Operator deactivated.",
    "op_reactivated": "Operator reactivated.",
    "cb_cancelled": "Callback cancelled.",
    "cbs_ran": "Due callbacks processed — results are in the queue below.",
    "demo_seeded": "Demo data seeded.",
    "demo_cleared": "Demo data cleared.",
}


def _done_url(t: str, key: str, anchor: str) -> str:
    return f"/admin?t={t}&done={key}#{anchor}"


def _portal_link_page(title: str, name: str, url: str, t: str, note: str) -> HTMLResponse:
    """One-time display of a raw portal URL — the only place a token is ever shown."""
    body = f"""
<header class="util-head"><h1>{title}</h1></header>
<div class=card style="margin-top:2rem">
<p><b>{_esc(name)}</b> — share this portal link with the operator. It is their only
way in, so send it privately.</p>
<div class=copyrow><code id=portal-url>{_esc(url)}</code>
<button type=button class=secondary id=copy-url hidden>Copy link</button></div>
<p class="muted small" role=status id=copy-status></p>
<p class="muted small">{_esc(note)}</p>
</div>
<p><a href='/admin?t={_esc(t)}#ops'>← Back to operators</a></p>
<script>
(() => {{
  const b = document.getElementById("copy-url");
  if (!navigator.clipboard) return;
  b.hidden = false;
  b.addEventListener("click", async () => {{
    try {{
      await navigator.clipboard.writeText(document.getElementById("portal-url").textContent);
      document.getElementById("copy-status").textContent = "Copied. This page won't show the link again.";
    }} catch (e) {{
      document.getElementById("copy-status").textContent = "Couldn't copy. Select the link and copy it by hand.";
    }}
  }});
}})();
</script>
"""
    return HTMLResponse(_page(f"{title} — Kaayal", body, nav=_admin_nav(t), body_class="wide util", motion=False))


def _fmt_dt(dt) -> str:
    """Stored datetimes are naive UTC; the owner thinks in IST (the calling
    window is IST too), so show IST and say so."""
    if not dt:
        return "—"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return _esc(dt.astimezone(_IST).strftime("%d %b, %H:%M")) + ' <span class="muted">IST</span>'


def _op_row(o: Operator, t: str) -> str:
    if o.approved_at is None:
        # Until approved, active-state is moot — show just the wait badge.
        badge = _status_badge("pending approval")
    else:
        badge = '<span class="badge ok">active</span>' if o.active else '<span class="badge bad">inactive</span>'
    actions = []
    if o.approved_at is None:
        actions.append(
            f"<form class=inline method=post action='/admin/operators/{o.id}/approve?t={t}'>"
            f"<button>Approve</button></form>"
        )
    else:
        # Portal links only work once approved_at is set — reissue before
        # approval would mint a link that 404s.
        actions.append(
            f"<form class=inline method=post action='/admin/operators/{o.id}/reissue?t={t}'>"
            f"<button class=secondary>Reissue link</button></form>"
        )
    verb, label, cls = ("deactivate", "Deactivate", "danger") if o.active else ("reactivate", "Reactivate", "secondary")
    guard = " onsubmit='return confirm(\"Deactivate this operator? Their portal link stops working until you reactivate.\")'" if verb == "deactivate" else ""
    actions.append(
        f"<form class=inline method=post action='/admin/operators/{o.id}/{verb}?t={t}'{guard}>"
        f"<button class={cls}>{label}</button></form>"
    )
    return (
        f"<tr><td class=num>{o.id}</td><td>{_esc(o.name)}</td><td class=small>{_esc(o.phone)}</td>"
        f"<td>{_src(o.source)}</td><td>{badge}</td>"
        f"<td class=actions>{''.join(actions)}</td></tr>"
    )


def _cb_rows(cbs: list[CallbackRequest], attempts: dict[int, list[CallbackAttempt]], t: str) -> str:
    out = []
    for cb in cbs:
        actions = ""
        if cb.status in _CB_ACTIVE:
            actions = (
                f"<form class=inline method=post action='/admin/callbacks/{cb.id}/cancel?t={t}'"
                f" onsubmit='return confirm(\"Cancel this callback? The customer will not be rung back.\")'>"
                f"<button class=danger>Cancel</button></form>"
            )
        out.append(
            f"<tr><td>{_esc(cb.public_id)}</td>"
            f"<td>{_esc(cb.customer_name)}<br><span class='muted small'>{_esc(cb.customer_phone)}</span></td>"
            f"<td class=small>{_reason(cb.reason)}</td><td>{_status_badge(cb.status)}</td>"
            f"<td class=num>{cb.attempts_this_trigger}/{_CB_MAX_ATTEMPTS}</td>"
            f"<td class=small>{_fmt_dt(cb.next_attempt_at)}</td>"
            f"<td class=small>{_fmt_dt(cb.expires_at)}</td><td class=actions>{actions}</td></tr>"
        )
        att = attempts.get(cb.id, [])
        if att:
            items = "".join(
                f"<li>{_fmt_dt(a.attempted_at)} — {_esc((a.outcome or '').replace('_', ' '))} · {_esc(a.provider)}</li>"
                for a in att
            )
            out.append(f"<tr><td colspan=8><ul class='muted small' style='margin:.2rem 0 .6rem' aria-label='Call attempts for {_esc(cb.public_id)}'>{items}</ul></td></tr>")
    return "".join(out) or ("<tr><td colspan=8 class='muted small'>No callbacks queued — "
                            "Paayal adds one only after the caller agrees.</td></tr>")


@router.get("", response_class=HTMLResponse)
def admin_home(request: Request, t: str | None = None, done: str | None = None):
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

    op_rows = "".join(_op_row(o, t) for o in operators) or ("<tr><td colspan=6 class='muted small'>"
        "No operators yet — add one below to get a portal link.</td></tr>")

    boat_names = {b.id: b.name for b, _ in boats}
    boat_rows = "".join(
        f"<tr><td class=num>{b.id}</td><td>{_esc(b.name)}</td>"
        f"<td class=small>{_esc(b.boat_type or '—')}</td>"
        f"<td class=small>{_esc(b.embarkation_point or '—')}</td>"
        f"<td class=small>{_esc(op)}</td>"
        f"<td>{_status_badge('available' if b.available else 'unavailable')}</td>"
        f"<td>{_status_badge('verified') if b.verified_at else _status_badge('unverified')}</td>"
        f"<td class=actions>{'' if b.verified_at else f'<form class=inline method=post action=/admin/boats/{b.id}/verify?t={t}><button>Verify</button></form>'}</td></tr>"
        for b, op in boats
    ) or "<tr><td colspan=8 class='muted small'>No boats yet — operators add them from their portal page.</td></tr>"

    def _req_row(r: BookingRequest) -> str:
        if r.boat_id:
            boat = _esc(boat_names.get(r.boat_id, f"boat #{r.boat_id} (removed)"))
        else:
            boat = '<span class="badge wait">no boat picked</span>'
        return (
            f"<tr><td>{_esc(r.public_id)}</td>"
            f"<td>{_esc(r.customer_name)}<br><span class='muted small'>{_esc(r.customer_phone)}</span></td>"
            f"<td class=small>{boat}</td><td class=small>{_esc(r.preferred_date)}</td>"
            f"<td class=num>{_esc(str(r.group_size)) if r.group_size else '—'}</td><td>{_src(r.source)}</td>"
            f"<td class='muted small'>{_esc(r.operator_note) if r.operator_note else '—'}</td>"
            f"<td>{_status_badge(r.status)}</td></tr>"
        )

    req_rows = "".join(_req_row(r) for r in requests) or ("<tr><td colspan=8 class='muted small'>"
        "No booking inquiries yet — they land here after a caller talks to Paayal.</td></tr>")

    cb_rows = _cb_rows(cbs, attempts_by_cb, t)

    # Triage ledger — the owner's actionable queue, hidden when everything is handled.
    pending_ops = sum(1 for o in operators if o.approved_at is None)
    unverified = sum(1 for b, _ in boats if b.verified_at is None)
    triage = sum(1 for r in requests if r.boat_id is None and r.status == "pending")
    active_cbs = sum(1 for c in cbs if c.status in _CB_ACTIVE)
    ledger = "" if (pending_ops or unverified or triage or active_cbs) else (
        '<p class="muted small">Nothing waiting on you: every operator is approved, every boat '
        'verified, and no request is unassigned.</p>'
    )
    pending_reqs = sum(1 for r in requests if r.status == "pending")

    def _jump(anchor: str, label: str, total: int, hot: int = 0, hot_label: str = "") -> str:
        n = (f'<span class="n hot">{hot} {hot_label}</span>' if hot
             else f'<span class="n">{total}</span>')
        return f'<li><a href="#{anchor}">{label} {n}</a></li>'

    # One jump bar doubles as the triage ledger: sections with work show what
    # is waiting in sand; the rest show their totals.
    jumps = (
        '<ul class="sectionnav" aria-label="Sections">'
        + _jump("ops", "Operators", len(operators), pending_ops, "awaiting approval")
        + _jump("boats", "Boats", len(boats), unverified, "to verify")
        + _jump("requests", "Requests", len(requests), triage, "unassigned")
        + _jump("callbacks", "Callbacks", len(cbs), active_cbs, "in queue")
        + '<li><a href="#demo">Demo data</a></li></ul>'
    )

    # The redirect lands on the section's anchor, so show the notice there —
    # a notice at the top of the page would be scrolled out of view.
    section_of = {"boat_verified": "boats", "op_deactivated": "ops", "op_reactivated": "ops",
                  "cb_cancelled": "callbacks", "cbs_ran": "callbacks",
                  "demo_seeded": "demo", "demo_cleared": "demo"}

    def notice(section: str) -> str:
        if done in _DONE and section_of.get(done) == section:
            return f'<div class="notice" role="status">{_DONE[done]}</div>'
        return ""

    body = f"""
<header class="util-head">
<h1>Owner admin</h1>
<p class=muted>Operators, listings, every booking request, and the callback queue.</p>
{jumps}
{ledger}
</header>
<h2 id="ops">Operators<span class="n">{len(operators)}</span></h2>
{notice("ops")}
<div class=tablewrap><table><thead><tr><th class=num>#</th><th>Name</th><th>Phone</th><th>Source</th><th>Status</th><th class=actions>Actions</th></tr></thead><tbody>{op_rows}</tbody></table></div>
<details class=disclose{"" if operators else " open"}>
<summary>Add an operator</summary>
<div>
<p class="muted small" style="margin-top:0">Operators you add here are approved straight away and get a portal link.
Operators who message the WhatsApp number show up above as <i>pending approval</i>.</p>
<form method=post action='/admin/operators?t={t}'>
<label for='op-name'>Operator name</label>
<input id='op-name' name=name placeholder='e.g. Raj Boat Service' required maxlength=120 autocomplete=off>
<label for='op-phone'>Phone</label>
<input id='op-phone' name=phone type=tel inputmode=tel placeholder='+91…' required maxlength=32>
<div style='margin-top:1rem'><button type=submit>Create and get portal link</button></div>
</form>
</div>
</details>
<h2 id="boats">Boats<span class="n">{len(boats)}</span></h2>
{notice("boats")}
<div class=tablewrap><table><thead><tr><th class=num>#</th><th>Name</th><th>Type</th><th>Boarding</th><th>Operator</th><th>Availability</th><th>Status</th><th class=actions>Actions</th></tr></thead><tbody>{boat_rows}</tbody></table></div>
<h2 id="requests">Booking requests<span class="n">{pending_reqs} pending of {len(requests)}</span></h2>
<p class="muted small">Requests with <span class="badge wait">no boat picked</span> came from callers who didn't choose a listing — follow up by phone.</p>
<div class=tablewrap><table><thead><tr><th>ID</th><th>Customer</th><th>Boat</th><th>Date</th><th class=num>Group</th><th>Source</th><th>Operator note</th><th>Status</th></tr></thead><tbody>{req_rows}</tbody></table></div>
<h2 id="callbacks">Callbacks<span class="n">{active_cbs} active of {len(cbs)}</span></h2>
{notice("callbacks")}
<p class=muted>Customers Paayal rings back. Calls go out 09:00–18:00 IST, at most {_CB_MAX_ATTEMPTS} tries per trigger. Times below are IST.</p>
<form class=inline method=post action='/admin/callbacks/run_due?t={t}' onsubmit='return confirm("Run due callbacks now? Queued customers may receive calls.")'><button class=secondary>Run due callbacks now</button></form>
<div class=tablewrap><table><thead><tr><th>ID</th><th>Customer</th><th>Reason</th><th>Status</th><th class=num>Tries</th><th>Next attempt</th><th>Expires</th><th class=actions>Actions</th></tr></thead><tbody>{cb_rows}</tbody></table></div>
<h2 id="demo">Demo data</h2>
{notice("demo")}
<div class=card>
<p class="muted small" style="margin-top:0">Labeled demo inventory for walkthroughs; it shows on the public site with a DEMO badge. Seeding twice won't create duplicates. Clearing removes the demo rows along with their requests and callbacks.</p>
<form class=inline method=post action='/admin/demo/seed?t={t}'><button class=secondary>Seed demo data</button></form>
<form class=inline method=post action='/admin/demo/clear?t={t}' onsubmit='return confirm("Clear demo data? This removes demo operators, boats, requests, and callbacks.")'><button class=danger>Clear demo data</button></form>
</div>
"""
    return HTMLResponse(_page("Kaayal admin", body, description="Kaayal owner admin", nav=_admin_nav(t), body_class="wide util", motion=False))


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
    return RedirectResponse(_done_url(t, "op_reactivated" if active else "op_deactivated", "ops"), status_code=303)


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
        # Verification makes the boat listed; if it's also bookable now,
        # parked no_availability callbacks should fire just like an
        # availability toggle in the portal.
        if boat.active and boat.available:
            op = session.get(Operator, boat.operator_id)
            if op and op.active:
                fire_boat_available(session, boat)
        session.commit()
    return RedirectResponse(_done_url(t, "boat_verified", "boats"), status_code=303)


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
    return RedirectResponse(_done_url(t, "cb_cancelled", "callbacks"), status_code=303)


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
    return RedirectResponse(_done_url(t, "cbs_ran", "callbacks"), status_code=303)


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
    return RedirectResponse(_done_url(t, "demo_seeded", "demo"), status_code=303)


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
    return RedirectResponse(_done_url(t, "demo_cleared", "demo"), status_code=303)
