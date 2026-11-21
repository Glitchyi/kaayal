import re
from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from app.config import Settings
from app.db import Boat, BookingRequest, CallbackAttempt, CallbackRequest, Operator, utcnow
from app.main import create_app
from app.portal import hash_token

SECRET = "test-tool-secret"
ADMIN = "test-admin-token"
OP_TOKEN = "op-portal-token-abc"


def make_settings() -> Settings:
    return Settings(
        sarvam_tool_shared_secret=SECRET,
        admin_token=ADMIN,
        database_url="sqlite://",
        demo_ignore_call_window=True,
        _env_file=None,
    )


async def noop_responder(u, lang):
    return "ok"


@pytest.fixture
def app():
    return create_app(settings=make_settings(), responder=noop_responder)


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def seed_operator(app, approved=True):
    with Session(app.state.engine) as s:
        op = Operator(
            name="Raj Boats", phone="+910000000001",
            token_hash=hash_token(OP_TOKEN),
            approved_at=utcnow() if approved else None,
        )
        s.add(op)
        s.commit()
        s.refresh(op)
        return op


def seed_callback(app, **kw):
    with Session(app.state.engine) as s:
        cb = CallbackRequest(
            public_id=kw.pop("public_id", "CB-0001-ab12"),
            customer_name=kw.pop("customer_name", "Anu"),
            customer_phone=kw.pop("customer_phone", "+919876543210"),
            consent_given=True,
            reason=kw.pop("reason", "operator_unreachable"),
            **kw,
        )
        s.add(cb)
        s.commit()
        s.refresh(cb)
        return cb


def portal_token_from(html_text: str) -> str:
    m = re.search(r"/portal/([A-Za-z0-9_-]{20,})", html_text)
    assert m, "no portal URL found in response"
    return m.group(1)


# --- operator approval ---

async def test_new_admin_endpoints_require_admin(app, client):
    op = seed_operator(app, approved=False)
    cb = seed_callback(app)
    for path in (
        f"/admin/operators/{op.id}/approve",
        f"/admin/callbacks/{cb.id}/cancel",
        "/admin/callbacks/run_due",
        "/admin/demo/seed",
        "/admin/demo/clear",
    ):
        assert (await client.post(path)).status_code == 401
        assert (await client.post(f"{path}?t=wrong")).status_code == 401


async def test_pending_operator_shows_approve_action(app, client):
    op = seed_operator(app, approved=False)
    r = await client.get(f"/admin?t={ADMIN}")
    assert r.status_code == 200
    assert "pending approval" in r.text
    assert f"/admin/operators/{op.id}/approve" in r.text


async def test_approve_grants_portal_access(app, client):
    op = seed_operator(app, approved=False)
    r = await client.post(f"/admin/operators/{op.id}/approve?t={ADMIN}")
    assert r.status_code == 200
    assert "/portal/" in r.text
    token = portal_token_from(r.text)
    assert token != OP_TOKEN
    with Session(app.state.engine) as s:
        o = s.get(Operator, op.id)
        assert o.approved_at is not None
        assert o.token_hash == hash_token(token)
    page = await client.get(f"/portal/{token}")
    assert page.status_code == 200
    assert "Raj Boats" in page.text


async def test_approve_unknown_operator_404(client):
    r = await client.post(f"/admin/operators/9999/approve?t={ADMIN}")
    assert r.status_code == 404


async def test_create_operator_is_preapproved(app, client):
    r = await client.post(f"/admin/operators?t={ADMIN}",
                          data={"name": "Pre Approved Tours", "phone": "+910002"})
    assert r.status_code == 200
    token = portal_token_from(r.text)
    with Session(app.state.engine) as s:
        op = s.exec(select(Operator).where(Operator.name == "Pre Approved Tours")).one()
        assert op.approved_at is not None
        assert op.source == "admin"
    assert (await client.get(f"/portal/{token}")).status_code == 200


# --- booking request columns ---

async def test_booking_requests_show_source_and_operator_note(app, client):
    with Session(app.state.engine) as s:
        s.add(BookingRequest(
            public_id="REQ-0007-zz99", customer_name="Anu",
            customer_phone="+919876543210", consent_given=True,
            source="web", operator_note="can only do mornings",
        ))
        s.commit()
    r = await client.get(f"/admin?t={ADMIN}")
    assert r.status_code == 200
    assert "web" in r.text
    assert "can only do mornings" in r.text


# --- callbacks section ---

async def test_admin_lists_callbacks_and_attempts(app, client):
    cb = seed_callback(
        app, status="queued", attempts_this_trigger=1,
        next_attempt_at=utcnow(), expires_at=utcnow() + timedelta(days=2),
    )
    with Session(app.state.engine) as s:
        s.add(CallbackAttempt(
            callback_id=cb.id, outcome="no_answer", provider="simulator",
            transcript=[{"who": "paayal", "text": "Namaskaram"}],
        ))
        s.commit()
    r = await client.get(f"/admin?t={ADMIN}")
    assert r.status_code == 200
    assert "CB-0001-ab12" in r.text
    assert "Anu" in r.text
    assert "operator_unreachable" in r.text
    assert "queued" in r.text
    assert "1/2" in r.text
    assert "no_answer" in r.text
    assert "simulator" in r.text
    # active callback gets a cancel action
    assert f"/admin/callbacks/{cb.id}/cancel" in r.text
    assert "/admin/callbacks/run_due" in r.text


async def test_cancel_callback_marks_opted_out(app, client):
    cb = seed_callback(app, status="queued")
    r = await client.post(f"/admin/callbacks/{cb.id}/cancel?t={ADMIN}", follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(CallbackRequest, cb.id).status == "opted_out"
    # opted-out rows no longer offer a cancel action
    page = await client.get(f"/admin?t={ADMIN}")
    assert f"/admin/callbacks/{cb.id}/cancel" not in page.text


async def test_run_due_processes_queued_callback(app, client):
    cb = seed_callback(
        app, status="queued",
        next_attempt_at=utcnow() - timedelta(hours=1),
        expires_at=utcnow() + timedelta(days=2),
    )
    r = await client.post(f"/admin/callbacks/run_due?t={ADMIN}", follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        cb = s.get(CallbackRequest, cb.id)
        # simulator default outcome is "interested" → converted to an inquiry
        assert cb.status == "converted"
        assert cb.attempts_this_trigger == 1
        attempts = s.exec(
            select(CallbackAttempt).where(CallbackAttempt.callback_id == cb.id)
        ).all()
        assert len(attempts) == 1
        assert attempts[0].outcome == "interested"
        assert attempts[0].provider == "simulator"
        assert attempts[0].transcript
        req = s.exec(select(BookingRequest).where(BookingRequest.source == "callback")).first()
        assert req is not None


# --- demo data ---

async def test_demo_seed_creates_labeled_rows_idempotently(app, client):
    for _ in range(2):
        r = await client.post(f"/admin/demo/seed?t={ADMIN}", follow_redirects=False)
        assert r.status_code == 303
    with Session(app.state.engine) as s:
        ops = s.exec(select(Operator).where(Operator.source == "demo-seed")).all()
        boats = s.exec(select(Boat).where(Boat.source == "demo-seed")).all()
    assert {o.name for o in ops} == {"Backwater Demo Cruises (DEMO)", "Monsoon Houseboats (DEMO)"}
    assert {b.name for b in boats} == {"Demo Shikara", "Demo Deluxe"}
    shikara = next(b for b in boats if b.name == "Demo Shikara")
    assert shikara.available is True
    assert shikara.price_display == "₹2,000/hour (demo)"
    assert shikara.amenities == ["shaded deck", "life jackets"]
    assert shikara.verified_at is not None
    backwater = next(o for o in ops if "Backwater" in o.name)
    monsoon = next(o for o in ops if "Monsoon" in o.name)
    assert backwater.reachable is True and backwater.approved_at is not None
    assert monsoon.reachable is False and monsoon.approved_at is not None
    page = await client.get(f"/admin?t={ADMIN}")
    assert "Backwater Demo Cruises (DEMO)" in page.text
    assert "demo-seed" in page.text


async def test_demo_clear_removes_demo_rows_and_children(app, client):
    await client.post(f"/admin/demo/seed?t={ADMIN}")
    # attach a request + callback to a demo boat to prove children are deleted first
    with Session(app.state.engine) as s:
        boat = s.exec(select(Boat).where(Boat.name == "Demo Shikara")).one()
        s.add(BookingRequest(
            public_id="REQ-DEMO-1", boat_id=boat.id, customer_name="Demo Cust",
            customer_phone="+9100001", consent_given=True,
        ))
        s.add(CallbackRequest(
            public_id="CB-DEMO-1", customer_name="Demo Cust",
            customer_phone="+9100001", consent_given=True,
            reason="no_availability", boat_id=boat.id,
        ))
        s.commit()
    r = await client.post(f"/admin/demo/clear?t={ADMIN}", follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.exec(select(Operator).where(Operator.source == "demo-seed")).all() == []
        assert s.exec(select(Boat).where(Boat.source == "demo-seed")).all() == []
        assert s.exec(select(BookingRequest).where(BookingRequest.public_id == "REQ-DEMO-1")).all() == []
        assert s.exec(select(CallbackRequest).where(CallbackRequest.public_id == "CB-DEMO-1")).all() == []


async def test_verify_boat_fires_parked_no_availability_callback(app, client):
    # Verifying a boat makes it listed; when it's also bookable the parked
    # no_availability callback must requeue like an availability toggle.
    op = seed_operator(app)
    with Session(app.state.engine) as s:
        boat = Boat(operator_id=op.id, name="Lake Queen",
                    available=True, active=True, verified_at=None)
        s.add(boat)
        s.commit()
        s.refresh(boat)
    cb = seed_callback(app, reason="no_availability", boat_id=boat.id)

    r = await client.post(f"/admin/boats/{boat.id}/verify?t={ADMIN}",
                          follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(CallbackRequest, cb.id).trigger_seq == 1


async def test_verify_unavailable_boat_does_not_fire(app, client):
    op = seed_operator(app)
    with Session(app.state.engine) as s:
        boat = Boat(operator_id=op.id, name="Lake Queen",
                    available=False, active=True, verified_at=None)
        s.add(boat)
        s.commit()
        s.refresh(boat)
    cb = seed_callback(app, reason="no_availability", boat_id=boat.id)

    r = await client.post(f"/admin/boats/{boat.id}/verify?t={ADMIN}",
                          follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(CallbackRequest, cb.id).trigger_seq == 0
