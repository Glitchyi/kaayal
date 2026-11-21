import re
from urllib.parse import quote, unquote

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.config import Settings
from app.db import Boat, BookingRequest, Operator, utcnow
from app.main import create_app
from app.portal import _wa_link, hash_token

SECRET = "test-tool-secret"
ADMIN = "test-admin-token"
OP_TOKEN = "op-portal-token-abc"


def make_settings() -> Settings:
    return Settings(
        sarvam_tool_shared_secret=SECRET,
        admin_token=ADMIN,
        database_url="sqlite://",
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


def seed_operator(app, verified=True):
    with Session(app.state.engine) as s:
        op = Operator(name="Raj Boats", phone="+910000000001", token_hash=hash_token(OP_TOKEN), approved_at=utcnow())
        s.add(op)
        s.commit()
        s.refresh(op)
        boat = Boat(operator_id=op.id, name="Lake Queen", capacity=8,
                    embarkation_point="Finishing Point",
                    verified_at=utcnow() if verified else None)
        s.add(boat)
        s.commit()
        s.refresh(boat)
        return op, boat


def seed_request(app, boat_id, status="pending", phone="+919876543210",
                 preferred_date="2026-12-01", group_size=4):
    with Session(app.state.engine) as s:
        r = BookingRequest(
            public_id="REQ-0001-ab12", boat_id=boat_id,
            customer_name="Anu", customer_phone=phone,
            consent_given=True, preferred_date=preferred_date, group_size=group_size,
            status=status,
        )
        s.add(r)
        s.commit()
        s.refresh(r)
        return r


def wa_hrefs(html: str) -> list[str]:
    return re.findall(r"href='(https://wa\.me/[^']+)'", html)


# --- _wa_link helper ---

def test_wa_link_encodes_text():
    url = _wa_link("919876543210", "Hello Anu, it's me & you")
    assert url.startswith("https://wa.me/919876543210?text=")
    assert quote("Hello Anu, it's me & you") in url
    assert " " not in url


# --- confirmed requests ---

async def test_confirmed_request_shows_wa_link(app, client):
    _, boat = seed_operator(app)
    seed_request(app, boat.id, status="confirmed")
    r = await client.get(f"/portal/{OP_TOKEN}")
    assert r.status_code == 200
    hrefs = wa_hrefs(r.text)
    assert len(hrefs) == 1
    assert hrefs[0].startswith("https://wa.me/919876543210?text=")
    msg = unquote(hrefs[0].split("?text=", 1)[1])
    assert "Anu" in msg and "Raj Boats" in msg
    assert "REQ-0001-ab12" in msg and "2026-12-01" in msg and "4 guests" in msg
    assert "target='_blank'" in r.text and "rel='noopener'" in r.text


async def test_confirmed_request_formatted_phone_digits_only(app, client):
    _, boat = seed_operator(app)
    seed_request(app, boat.id, status="confirmed", phone="+91 98470 12345")
    r = await client.get(f"/portal/{OP_TOKEN}")
    hrefs = wa_hrefs(r.text)
    assert len(hrefs) == 1
    assert hrefs[0].startswith("https://wa.me/919847012345?text=")


async def test_confirmed_request_omits_empty_fields(app, client):
    _, boat = seed_operator(app)
    seed_request(app, boat.id, status="confirmed",
                 preferred_date=None, group_size=None)
    r = await client.get(f"/portal/{OP_TOKEN}")
    hrefs = wa_hrefs(r.text)
    assert len(hrefs) == 1
    msg = unquote(hrefs[0].split("?text=", 1)[1])
    assert "REQ-0001-ab12" in msg
    assert " on " not in msg and "guests" not in msg


async def test_confirmed_request_short_phone_no_link(app, client):
    _, boat = seed_operator(app)
    seed_request(app, boat.id, status="confirmed", phone="12345")
    r = await client.get(f"/portal/{OP_TOKEN}")
    assert wa_hrefs(r.text) == []
    # phone is still revealed for calling once confirmed
    assert "12345" in r.text


# --- other statuses get nothing ---

async def test_pending_request_has_no_wa_link(app, client):
    _, boat = seed_operator(app)
    seed_request(app, boat.id, status="pending")
    r = await client.get(f"/portal/{OP_TOKEN}")
    assert r.status_code == 200
    assert "wa.me" not in r.text


async def test_blocked_request_has_no_wa_link(app, client):
    _, boat = seed_operator(app)
    seed_request(app, boat.id, status="blocked")
    r = await client.get(f"/portal/{OP_TOKEN}")
    assert r.status_code == 200
    assert "wa.me" not in r.text


async def test_cancelled_request_has_no_wa_link(app, client):
    _, boat = seed_operator(app)
    seed_request(app, boat.id, status="cancelled")
    r = await client.get(f"/portal/{OP_TOKEN}")
    assert "wa.me" not in r.text
