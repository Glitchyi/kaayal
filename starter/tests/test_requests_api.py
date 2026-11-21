"""Contract tests for POST /api/voice/request and /api/voice/callback —
the two tool endpoints Paayal calls — plus app-level guards (body cap,
validation envelope, admin-token-not-configured).

DEMO: tool auth is disabled, so none of these send X-Kaayal-Tool-Token.
"""

import re

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from app.config import Settings
from app.db import Boat, BookingRequest, CallbackRequest, Operator, utcnow
from app.main import create_app
from app.portal import hash_token

BASE_REQ = {"customer_name": "Anu", "customer_phone": "+91 98765 43210",
            "consent_given": True}
BASE_CB = {"customer_name": "Asha", "customer_phone": "+91 90000 00001",
           "consent_given": True, "reason": "no_availability"}


def make_settings(**overrides) -> Settings:
    base = dict(database_url="sqlite://", _env_file=None)
    base.update(overrides)
    return Settings(**base)


async def noop_responder(u, lang):
    return "ok"


@pytest.fixture
def app():
    return create_app(settings=make_settings(), responder=noop_responder)


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def seed_boat(app, *, verified=True, active=True, available=True, reachable=True):
    with Session(app.state.engine) as s:
        op = Operator(name="Test Op", phone="+910000000001",
                      token_hash=hash_token("t"), approved_at=utcnow(),
                      reachable=reachable)
        s.add(op)
        s.commit()
        s.refresh(op)
        boat = Boat(operator_id=op.id, name="Lake Queen", available=available,
                    active=active, verified_at=utcnow() if verified else None)
        s.add(boat)
        s.commit()
        s.refresh(boat)
        return op.id, boat.id


# --- POST /api/voice/request ------------------------------------------------

async def test_request_rejects_unknown_boat(client):
    r = await client.post("/api/voice/request", json={**BASE_REQ, "boat_id": 4242})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


async def test_request_rejects_inactive_boat(client, app):
    _, boat_id = seed_boat(app, active=False)
    r = await client.post("/api/voice/request", json={**BASE_REQ, "boat_id": boat_id})
    assert r.json()["status"] == "rejected"


async def test_request_public_id_format_and_stored_row(client, app):
    r = await client.post("/api/voice/request", json={
        **BASE_REQ, "customer_name": "  Anu  ", "preferred_date": "2026-12-01",
        "group_size": 4, "notes": "sunset cruise",
    })
    assert r.status_code == 200
    body = r.json()
    assert re.fullmatch(r"REQ-\d{4}-[0-9a-f]{4}", body["request_id"])
    with Session(app.state.engine) as s:
        req = s.exec(select(BookingRequest)).one()
        assert req.customer_name == "Anu"          # stripped
        assert req.consent_given is True
        assert req.status == "pending"             # never auto-confirmed
        assert req.group_size == 4
        assert req.boat_id is None                 # general request → triage


async def test_request_empty_strings_become_null(client, app):
    """Sarvam renders unset optional vars as "" — must store NULL, not ''."""
    r = await client.post("/api/voice/request", json={
        **BASE_REQ, "preferred_date": "", "notes": "", "boat_id": "",
        "group_size": "", "interaction_id": "",
    })
    assert r.status_code == 200 and r.json()["status"] == "pending"
    with Session(app.state.engine) as s:
        req = s.exec(select(BookingRequest)).one()
        assert req.preferred_date is None and req.notes is None and req.boat_id is None


@pytest.mark.parametrize("group_size", [0, 201])
async def test_request_group_size_out_of_bounds(client, group_size):
    r = await client.post("/api/voice/request", json={**BASE_REQ, "group_size": group_size})
    assert r.status_code == 400
    assert r.json()["detail"] == "invalid_request"


@pytest.mark.parametrize("group_size", [1, 200])
async def test_request_group_size_bounds_ok(client, group_size):
    r = await client.post("/api/voice/request", json={**BASE_REQ, "group_size": group_size})
    assert r.status_code == 200 and r.json()["status"] == "pending"


async def test_request_extra_field_forbidden(client):
    r = await client.post("/api/voice/request",
                          json={**BASE_REQ, "caller_lat": 9.98})
    assert r.status_code == 400
    assert r.json()["detail"] == "invalid_request"


async def test_request_missing_required_field(client):
    r = await client.post("/api/voice/request",
                          json={"customer_phone": "+91 90000 00001", "consent_given": True})
    assert r.status_code == 400
    assert r.json()["detail"] == "invalid_request"


async def test_request_consent_false_never_writes_row(client, app):
    r = await client.post("/api/voice/request",
                          json={**BASE_REQ, "consent_given": False})
    assert r.status_code == 200 and r.json()["status"] == "rejected"
    with Session(app.state.engine) as s:
        assert s.exec(select(BookingRequest)).all() == []


# --- POST /api/voice/callback ------------------------------------------------

async def test_callback_invalid_reason(client):
    r = await client.post("/api/voice/callback",
                          json={**BASE_CB, "reason": "price_drop"})
    assert r.status_code == 400
    assert r.json()["detail"] == "invalid_request"


async def test_callback_missing_reason(client):
    body = {k: v for k, v in BASE_CB.items() if k != "reason"}
    r = await client.post("/api/voice/callback", json=body)
    assert r.status_code == 400


async def test_callback_bad_phone_rejected(client):
    # Passes min_length, fails the phone-shape regex → polite rejection, not 400.
    r = await client.post("/api/voice/callback",
                          json={**BASE_CB, "customer_phone": "abcdef"})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


async def test_callback_extra_field_forbidden(client):
    r = await client.post("/api/voice/callback", json={**BASE_CB, "vip": True})
    assert r.status_code == 400


async def test_callback_opt_out_with_nothing_scheduled(client):
    r = await client.post("/api/voice/callback",
                          json={**BASE_CB, "consent_given": False})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


async def test_callback_links_operator_from_boat(client, app):
    op_id, boat_id = seed_boat(app)
    r = await client.post("/api/voice/callback",
                          json={**BASE_CB, "boat_id": boat_id})
    assert r.json()["status"] == "queued"
    with Session(app.state.engine) as s:
        cb = s.exec(select(CallbackRequest)).one()
        assert cb.boat_id == boat_id and cb.operator_id == op_id


async def test_callback_dedupe_same_phone_reason_boat(client, app):
    _, boat_id = seed_boat(app)
    first = (await client.post("/api/voice/callback",
                               json={**BASE_CB, "boat_id": boat_id})).json()
    # Same number formatted differently still dedupes.
    second = (await client.post("/api/voice/callback", json={
        **BASE_CB, "customer_phone": "919000000001", "boat_id": boat_id,
    })).json()
    assert first["request_id"] == second["request_id"]
    with Session(app.state.engine) as s:
        assert len(s.exec(select(CallbackRequest)).all()) == 1


async def test_callback_keywords_stored(client, app):
    r = await client.post("/api/voice/callback",
                          json={**BASE_CB, "keywords": "shikara, sunset"})
    assert r.json()["status"] == "queued"
    with Session(app.state.engine) as s:
        cb = s.exec(select(CallbackRequest)).one()
        assert cb.keywords == "shikara, sunset"


# --- app-level guards ---------------------------------------------------------

async def test_oversized_body_413():
    app = create_app(settings=make_settings(max_body_bytes=64),
                     responder=noop_responder)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/voice/request", json={**BASE_REQ, "notes": "x" * 500})
    assert r.status_code == 413
    assert r.json()["detail"] == "request_too_large"


async def test_admin_unconfigured_returns_503():
    app = create_app(settings=make_settings(admin_token=None),
                     responder=noop_responder)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        assert (await c.get("/admin")).status_code == 503
        assert (await c.post("/admin/operators", data={"name": "X", "phone": "1"})).status_code == 503
