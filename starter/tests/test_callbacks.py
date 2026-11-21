from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from app.callbacks import (
    SimulatedProvider,
    create_callback,
    fire_boat_available,
    fire_operator_reachable,
    next_window_start,
    opt_out_phone,
    process_due_callbacks,
)
from app.config import Settings
from app.db import Boat, BookingRequest, CallbackAttempt, CallbackRequest, Operator, utcnow
from app.main import create_app
from app.portal import hash_token

IST = ZoneInfo("Asia/Kolkata")
SECRET = "test-tool-secret"
AUTH = {"X-Kaayal-Tool-Token": SECRET}


def make_settings() -> Settings:
    return Settings(
        sarvam_tool_shared_secret=SECRET,
        database_url="sqlite://",
        kaayal_public_base_url="https://kaayal.test",
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


def seed_boat(app, *, available=False, reachable=True, verified=True):
    with Session(app.state.engine) as s:
        op = Operator(name="Test Op", phone="+910000000001",
                      token_hash=hash_token("t"), approved_at=utcnow(), reachable=reachable)
        s.add(op)
        s.commit()
        s.refresh(op)
        boat = Boat(operator_id=op.id, name="Lake Queen", available=available,
                    verified_at=utcnow() if verified else None)
        s.add(boat)
        s.commit()
        s.refresh(boat)
        return op.id, boat.id


def ist(hour: int, day_offset: int = 0) -> datetime:
    base = datetime.now(IST).replace(hour=hour, minute=0, second=0, microsecond=0)
    return (base + timedelta(days=day_offset)).astimezone(timezone.utc)


def make_cb(app, *, reason="no_availability", boat_id=None, phone="+919000000001", **kw):
    with Session(app.state.engine) as s:
        return create_callback(
            s, customer_name="Asha", customer_phone=phone, reason=reason,
            boat_id=boat_id, **kw,
        ).public_id


def get_cb(app, public_id) -> CallbackRequest:
    with Session(app.state.engine) as s:
        cb = s.exec(select(CallbackRequest).where(CallbackRequest.public_id == public_id)).one()
        s.expunge(cb)
        return cb


# --- creation / dedupe / opt-out -------------------------------------------

def test_fresh_callback_is_parked_not_due(app):
    """A new callback must wait for its trigger event, never fire immediately."""
    pid = make_cb(app)
    made = process_due_callbacks(app.state.engine, SimulatedProvider(), now=ist(10))
    assert made == 0
    assert get_cb(app, pid).status == "queued"


def test_dedupe_same_phone_reason_boat(app):
    with Session(app.state.engine) as s:
        a = create_callback(s, customer_name="A", customer_phone="+91 90000 00001",
                            reason="no_availability", keywords="queen")
        b = create_callback(s, customer_name="A", customer_phone="+919000000001",
                            reason="no_availability", keywords="queen")
        assert a.id == b.id


def test_opt_out_marks_active(app):
    pid = make_cb(app)
    with Session(app.state.engine) as s:
        assert opt_out_phone(s, "919000000001") == 1
    assert get_cb(app, pid).status == "opted_out"


# --- triggers ---------------------------------------------------------------

def test_boat_available_trigger_requeues(app):
    op_id, boat_id = seed_boat(app, available=False)
    pid = make_cb(app, boat_id=boat_id)
    cb = get_cb(app, pid)
    assert cb.trigger_seq == 0
    with Session(app.state.engine) as s:
        boat = s.get(Boat, boat_id)
        boat.available = True
        n = fire_boat_available(s, boat)
        s.commit()
    assert n == 1
    cb = get_cb(app, pid)
    assert cb.trigger_seq == 1 and cb.attempts_this_trigger == 0


def test_operator_reachable_trigger(app):
    op_id, boat_id = seed_boat(app, reachable=False)
    pid = make_cb(app, reason="operator_unreachable", boat_id=boat_id, operator_id=op_id)
    with Session(app.state.engine) as s:
        op = s.get(Operator, op_id)
        op.reachable = True
        n = fire_operator_reachable(s, op)
        s.commit()
    assert n == 1
    assert get_cb(app, pid).trigger_seq == 1


# --- engine ------------------------------------------------------------------

def test_window_blocks_and_reschedules(app):
    """Outside 09:00–18:00 IST the callback stays queued for next window."""
    pid = make_cb(app)
    evening = ist(20)
    _trigger(app, pid, due_at=evening - timedelta(hours=1))
    made = process_due_callbacks(app.state.engine, SimulatedProvider(), now=evening)
    assert made == 0
    cb = get_cb(app, pid)
    assert cb.status == "queued"
    nxt = cb.next_attempt_at.replace(tzinfo=timezone.utc)
    assert nxt > evening and nxt.astimezone(IST).hour == 9


def _trigger(app, public_id, due_at=None):
    with Session(app.state.engine) as s:
        cb = s.exec(select(CallbackRequest).where(CallbackRequest.public_id == public_id)).one()
        cb.next_attempt_at = due_at or (utcnow() - timedelta(minutes=1))
        cb.trigger_seq = max(cb.trigger_seq, 1)
        s.commit()


def test_interested_converts_to_booking_inquiry(app):
    _, boat_id = seed_boat(app)
    pid = make_cb(app, boat_id=boat_id)
    _trigger(app, pid, due_at=ist(9))
    made = process_due_callbacks(app.state.engine, SimulatedProvider("interested"), now=ist(10))
    assert made == 1
    assert get_cb(app, pid).status == "converted"
    with Session(app.state.engine) as s:
        req = s.exec(select(BookingRequest)).one()
        assert req.source == "callback" and req.boat_id == boat_id and req.status == "pending"
        att = s.exec(select(CallbackAttempt)).one()
        assert att.outcome == "interested" and att.transcript


def test_not_interested_is_terminal(app):
    pid = make_cb(app)
    _trigger(app, pid, due_at=ist(9))
    process_due_callbacks(app.state.engine, SimulatedProvider("not_interested"), now=ist(10))
    assert get_cb(app, pid).status == "not_interested"


def test_no_answer_retries_then_exhausts(app):
    pid = make_cb(app)
    _trigger(app, pid, due_at=ist(9))
    provider = SimulatedProvider("no_answer")
    process_due_callbacks(app.state.engine, provider, now=ist(10))
    cb = get_cb(app, pid)
    assert cb.status == "queued" and cb.attempts_this_trigger == 1
    # Second attempt blocked by the 60-min gap…
    process_due_callbacks(app.state.engine, provider, now=ist(10, 0) + timedelta(minutes=30))
    assert get_cb(app, pid).attempts_this_trigger == 1
    # …allowed after 61 minutes, then exhausted at 2.
    process_due_callbacks(app.state.engine, provider, now=ist(12))
    cb = get_cb(app, pid)
    assert cb.status == "no_answer" and cb.attempts_this_trigger == 2


def test_expiry(app):
    pid = make_cb(app)
    _trigger(app, pid, due_at=ist(9))
    with Session(app.state.engine) as s:
        cb = s.exec(select(CallbackRequest).where(CallbackRequest.public_id == pid)).one()
        cb.expires_at = ist(9)  # before the simulated now=ist(10)
        s.commit()
    process_due_callbacks(app.state.engine, SimulatedProvider(), now=ist(10))
    assert get_cb(app, pid).status == "expired"


def test_force_attempts_queued(app):
    pid = make_cb(app)
    made = process_due_callbacks(
        app.state.engine, SimulatedProvider(), force=True, ignore_window=True
    )
    assert made == 1
    assert get_cb(app, pid).status == "converted"


# --- HTTP endpoint -----------------------------------------------------------

async def test_endpoint_creates_queued(client, app):
    _, boat_id = seed_boat(app)
    r = await client.post(
        "/api/voice/callback",
        headers=AUTH,
        json={"customer_name": "Asha", "customer_phone": "+91 90000 00001",
              "consent_given": True, "reason": "no_availability", "boat_id": boat_id},
    )
    assert r.status_code == 200 and r.json()["status"] == "queued"
    assert r.json()["request_id"].startswith("CB-")


async def test_endpoint_opt_out_path(client, app):
    await client.post(
        "/api/voice/callback", headers=AUTH,
        json={"customer_name": "A", "customer_phone": "+91 90000 00001",
              "consent_given": True, "reason": "no_availability"},
    )
    r = await client.post(
        "/api/voice/callback", headers=AUTH,
        json={"customer_name": "A", "customer_phone": "+91 90000 00001",
              "consent_given": False, "reason": "no_availability"},
    )
    assert r.json()["status"] == "opted_out"


async def test_endpoint_rejects_unverified_boat(client, app):
    _, boat_id = seed_boat(app, verified=False)
    r = await client.post(
        "/api/voice/callback", headers=AUTH,
        json={"customer_name": "A", "customer_phone": "+91 90000 00001",
              "consent_given": True, "reason": "no_availability", "boat_id": boat_id},
    )
    assert r.json()["status"] == "rejected"


async def test_request_on_unavailable_boat_suggests_callback(client, app):
    _, boat_id = seed_boat(app, available=False)
    r = await client.post(
        "/api/voice/request", headers=AUTH,
        json={"customer_name": "A", "customer_phone": "+91 90000 00001",
              "consent_given": True, "boat_id": boat_id},
    )
    assert r.json()["status"] == "unavailable"


async def test_request_on_unreachable_operator_suggests_callback(client, app):
    _, boat_id = seed_boat(app, available=True, reachable=False)
    r = await client.post(
        "/api/voice/request", headers=AUTH,
        json={"customer_name": "A", "customer_phone": "+91 90000 00001",
              "consent_given": True, "boat_id": boat_id},
    )
    assert r.json()["status"] == "unreachable"
