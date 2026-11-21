"""Public web pages: /boats, /paayal, /explore, /inquire, /join + shared chrome."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from app.config import Settings
from app.db import Boat, BookingRequest, Operator, utcnow
from app.main import create_app
from app.portal import hash_token

SECRET = "test-tool-secret"
PHONE = "+91 94000 00000"


def make_settings() -> Settings:
    return Settings(
        sarvam_tool_shared_secret=SECRET,
        database_url="sqlite://",
        kaayal_phone_number=PHONE,
        kaayal_whatsapp_number="+91 94000 00001",
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


def seed_operator(app, name="Raj Boats", phone="+910000000001", reachable=True):
    with Session(app.state.engine) as s:
        op = Operator(
            name=name, phone=phone, token_hash=hash_token("tok-" + phone),
            reachable=reachable, approved_at=utcnow(),
        )
        s.add(op)
        s.commit()
        s.refresh(op)
        return op


def seed_boat(app, op, name="Lake Queen", verified=True, available=True,
              source="operator-submitted", **kw):
    with Session(app.state.engine) as s:
        b = Boat(
            operator_id=op.id, name=name, embarkation_point="Finishing Point",
            verified_at=utcnow() if verified else None, available=available,
            source=source, **kw,
        )
        s.add(b)
        s.commit()
        s.refresh(b)
        return b


def all_requests(app):
    with Session(app.state.engine) as s:
        return s.exec(select(BookingRequest)).all()


# --- shared chrome + page markers ---

async def test_landing_uses_shared_nav_and_footer(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert 'class="topnav"' in r.text and 'href="/boats"' in r.text
    assert "nothing on this site is a confirmed booking" in r.text
    assert f'tel:+{"".join(c for c in PHONE if c.isdigit())}' in r.text


async def test_boats_page_lists_verified_boat(client, app):
    op = seed_operator(app)
    seed_boat(app, op, price_display="₹9,500/night", amenities=["life jackets", "shaded deck"])
    r = await client.get("/boats")
    assert r.status_code == 200
    assert "Lake Queen" in r.text and "Raj Boats" in r.text
    assert "₹9,500/night" in r.text
    assert "life jackets" in r.text and "shaded deck" in r.text
    assert ">available<" in r.text
    assert "Paayal never confirms bookings" in r.text


async def test_boats_hides_unverified_and_badges_demo(client, app):
    op = seed_operator(app)
    seed_boat(app, op, name="Ghost Boat", verified=False)
    seed_boat(app, op, name="Seed Cruiser", source="demo-seed")
    r = await client.get("/boats")
    assert "Ghost Boat" not in r.text
    assert "Seed Cruiser" in r.text
    assert ">DEMO<" in r.text


async def test_boats_hides_inactive_operator_boats(client, app):
    op = seed_operator(app)
    seed_boat(app, op, name="Mothballed", verified=True)
    with Session(app.state.engine) as s:
        s.get(Operator, op.id).active = False
        s.commit()
    r = await client.get("/boats")
    assert "Mothballed" not in r.text


async def test_paayal_page(client):
    r = await client.get("/paayal")
    assert r.status_code == 200
    assert "Meet Paayal" in r.text
    assert "Malayalam" in r.text
    assert "never" in r.text.lower()  # what Paayal never does
    assert PHONE in r.text  # call CTA


async def test_explore_page(client):
    r = await client.get("/explore")
    assert r.status_code == 200
    assert "Alappuzha" in r.text
    assert "Finishing Point" in r.text and "Punnamada" in r.text
    assert 'href="/boats"' in r.text


async def test_inquire_form_renders(client, app):
    op = seed_operator(app)
    seed_boat(app, op)
    r = await client.get("/inquire")
    assert r.status_code == 200
    assert "booking inquiry" in r.text.lower()
    assert "No preference — general inquiry" in r.text
    assert "Lake Queen" in r.text
    assert "call me back" in r.text  # consent copy


async def test_join_form_renders(client):
    r = await client.get("/join")
    assert r.status_code == 200
    assert "operator" in r.text.lower()


# --- /inquire POST ---

async def test_inquire_valid_creates_web_request(client, app):
    op = seed_operator(app)
    boat = seed_boat(app, op)
    r = await client.post("/inquire", data={
        "name": "Anu", "phone": "+91 98765 43210", "boat_id": str(boat.id),
        "preferred_date": "next Saturday", "group_size": "4", "consent": "yes",
    })
    assert r.status_code == 200
    assert "REQ-" in r.text
    assert "nothing is booked yet" in r.text
    reqs = all_requests(app)
    assert len(reqs) == 1
    assert reqs[0].source == "web" and reqs[0].consent_given is True
    assert reqs[0].boat_id == boat.id and reqs[0].group_size == 4


async def test_inquire_no_consent_creates_no_row(client, app):
    op = seed_operator(app)
    boat = seed_boat(app, op)
    r = await client.post("/inquire", data={
        "name": "Anu", "phone": "+91 98765 43210", "boat_id": str(boat.id),
    })
    assert r.status_code == 200
    assert "consent" in r.text.lower()
    assert all_requests(app) == []


async def test_inquire_bad_phone_rejected(client, app):
    r = await client.post("/inquire", data={
        "name": "Anu", "phone": "not-a-phone", "consent": "yes",
    })
    assert r.status_code == 200
    assert all_requests(app) == []


async def test_inquire_unavailable_boat_honest_error(client, app):
    op = seed_operator(app)
    seed_boat(app, op, available=False)
    # boat_id must be guessed — unavailable boats aren't in the select,
    # but the POST still validates honestly.
    with Session(app.state.engine) as s:
        bid = s.exec(select(Boat.id)).one()
    r = await client.post("/inquire", data={
        "name": "Anu", "phone": "+91 98765 43210", "boat_id": str(bid),
        "consent": "yes",
    })
    assert r.status_code == 200
    assert "not available right now" in r.text
    assert PHONE in r.text and "Paayal can arrange a callback" in r.text
    assert all_requests(app) == []


async def test_inquire_unreachable_operator_honest_error(client, app):
    op = seed_operator(app, reachable=False)
    boat = seed_boat(app, op)
    r = await client.post("/inquire", data={
        "name": "Anu", "phone": "+91 98765 43210", "boat_id": str(boat.id),
        "consent": "yes",
    })
    assert "not available right now" in r.text
    assert all_requests(app) == []


async def test_inquire_general_inquiry_no_boat(client, app):
    r = await client.post("/inquire", data={
        "name": "Meera", "phone": "+91 90000 12345", "boat_id": "",
        "consent": "yes", "group_size": "2",
    })
    assert "REQ-" in r.text
    reqs = all_requests(app)
    assert len(reqs) == 1 and reqs[0].boat_id is None and reqs[0].source == "web"


# --- /join POST ---

async def test_join_creates_pending_operator(client, app):
    r = await client.post("/join", data={
        "name": "Kerala Crafts Boats", "phone": "+91 98470 11111",
    })
    assert r.status_code == 200
    assert "pending verification" in r.text
    with Session(app.state.engine) as s:
        op = s.exec(select(Operator).where(Operator.source == "web-signup")).one()
    assert op.approved_at is None
    assert op.name == "Kerala Crafts Boats"


async def test_join_duplicate_phone_friendly_page(client, app):
    seed_operator(app, phone="+919847011111")
    r = await client.post("/join", data={
        "name": "Copycat", "phone": "+91 98470-11111",  # same digits, other format
    })
    assert r.status_code == 200
    assert "already registered" in r.text.lower()
    with Session(app.state.engine) as s:
        assert len(s.exec(select(Operator)).all()) == 1


async def test_join_bad_phone_no_row(client, app):
    r = await client.post("/join", data={"name": "X", "phone": "abc"})
    assert r.status_code == 200
    with Session(app.state.engine) as s:
        assert s.exec(select(Operator)).all() == []
