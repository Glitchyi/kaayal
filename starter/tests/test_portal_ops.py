import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from app.config import Settings
from app.db import Boat, BookingRequest, CallbackRequest, Operator, utcnow
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
        boat = Boat(operator_id=op.id, name="Lake Queen", capacity=8,
                    embarkation_point="Finishing Point", verified_at=utcnow())
        s.add(boat)
        s.commit()
        s.refresh(boat)
        s.refresh(op)  # boat commit expired op's attrs — reload before detach
        return op, boat


def seed_request(app, boat_id, status="pending"):
    with Session(app.state.engine) as s:
        r = BookingRequest(
            public_id="REQ-0001-ab12", boat_id=boat_id,
            customer_name="Anu", customer_phone="+919876543210",
            consent_given=True, preferred_date="2026-12-01", group_size=4,
            status=status,
        )
        s.add(r)
        s.commit()
        s.refresh(r)
        return r


def seed_callback(app, reason, *, operator_id=None, boat_id=None):
    with Session(app.state.engine) as s:
        cb = CallbackRequest(
            public_id="CB-0001-ab12", customer_name="Anu",
            customer_phone="+919876543210", consent_given=True,
            reason=reason, operator_id=operator_id, boat_id=boat_id,
        )
        s.add(cb)
        s.commit()
        s.refresh(cb)
        return cb


# --- approval gate ---

async def test_pending_operator_gets_404(app, client):
    seed_operator(app, approved=False)
    assert (await client.get(f"/portal/{OP_TOKEN}")).status_code == 404
    assert (await client.post(f"/portal/{OP_TOKEN}/toggle_reachable")).status_code == 404


async def test_approved_operator_gets_dashboard(app, client):
    seed_operator(app)
    r = await client.get(f"/portal/{OP_TOKEN}")
    assert r.status_code == 200
    assert "reachable" in r.text


# --- reachability toggle ---

async def test_toggle_reachable_flips_and_fires_callbacks(app, client):
    op, _ = seed_operator(app)
    cb = seed_callback(app, "operator_unreachable", operator_id=op.id)

    r = await client.post(f"/portal/{OP_TOKEN}/toggle_reachable", follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(Operator, op.id).reachable is False
        assert s.get(CallbackRequest, cb.id).trigger_seq == 0  # off → no fire

    await client.post(f"/portal/{OP_TOKEN}/toggle_reachable")
    with Session(app.state.engine) as s:
        assert s.get(Operator, op.id).reachable is True
        cb2 = s.get(CallbackRequest, cb.id)
        assert cb2.trigger_seq == 1  # False→True requeued the queued callback
        assert cb2.status == "queued"


# --- boat availability toggle ---

async def test_toggle_boat_available_flips_and_fires_callbacks(app, client):
    _, boat = seed_operator(app)
    cb = seed_callback(app, "no_availability", boat_id=boat.id)

    r = await client.post(f"/portal/{OP_TOKEN}/boats/{boat.id}/toggle_available",
                          follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(Boat, boat.id).available is False
        assert s.get(CallbackRequest, cb.id).trigger_seq == 0

    await client.post(f"/portal/{OP_TOKEN}/boats/{boat.id}/toggle_available")
    with Session(app.state.engine) as s:
        b = s.get(Boat, boat.id)
        assert b.available is True
        assert s.get(CallbackRequest, cb.id).trigger_seq == 1


async def test_cannot_toggle_other_operators_boat(app, client):
    _, boat = seed_operator(app)
    with Session(app.state.engine) as s:
        s.add(Operator(name="Other", phone="+9102",
                       token_hash=hash_token("other-token"), approved_at=utcnow()))
        s.commit()
    r = await client.post(f"/portal/other-token/boats/{boat.id}/toggle_available")
    with Session(app.state.engine) as s:
        assert s.get(Boat, boat.id).available is True  # unchanged
    assert r.status_code == 303


# --- add boat: price + amenities ---

async def test_add_boat_saves_price_and_amenities(app, client):
    seed_operator(app)
    r = await client.post(f"/portal/{OP_TOKEN}/boats",
                          data={"name": "New Cruiser", "capacity": "6",
                                "price_display": "₹9,500/night",
                                "amenities": "AC, meals,  , upper deck"},
                          follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        boat = s.exec(select(Boat).where(Boat.name == "New Cruiser")).one()
    assert boat.price_display == "₹9,500/night"
    assert boat.amenities == ["AC", "meals", "upper deck"]


# --- decline + operator_note ---

async def test_decline_sets_status_and_note(app, client):
    _, boat = seed_operator(app)
    req = seed_request(app, boat.id)
    r = await client.post(f"/portal/{OP_TOKEN}/requests/{req.public_id}/decline",
                          data={"note": "fully booked that week"},
                          follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        r2 = s.get(BookingRequest, req.id)
        assert r2.status == "declined"
        assert r2.operator_note == "fully booked that week"
    page = await client.get(f"/portal/{OP_TOKEN}")
    assert "fully booked that week" in page.text
    assert "voice" in page.text  # source badge shown


# --- delete boat: soft-delete only ---

async def test_delete_boat_soft_deletes(app, client):
    _, boat = seed_operator(app)
    r = await client.post(f"/portal/{OP_TOKEN}/boats/{boat.id}/delete",
                          follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        b = s.get(Boat, boat.id)
        assert b.active is False          # row kept for request history
    page = await client.get(f"/portal/{OP_TOKEN}")
    assert "Lake Queen</td>" not in page.text


async def test_delete_other_operators_boat_is_noop(app, client):
    _, boat = seed_operator(app)
    with Session(app.state.engine) as s:
        s.add(Operator(name="Other", phone="+9102",
                       token_hash=hash_token("other-token"), approved_at=utcnow()))
        s.commit()
    r = await client.post(f"/portal/other-token/boats/{boat.id}/delete")
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(Boat, boat.id).active is True  # untouched


# --- request transitions: guards ---

async def test_transition_on_non_pending_is_noop(app, client):
    """Only pending requests can transition; a confirmed request ignores
    later decline/block posts instead of flipping status."""
    _, boat = seed_operator(app)
    req = seed_request(app, boat.id, status="confirmed")
    for action in ("confirm", "decline", "block"):
        r = await client.post(
            f"/portal/{OP_TOKEN}/requests/{req.public_id}/{action}",
            follow_redirects=False)
        assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(BookingRequest, req.id).status == "confirmed"


async def test_transition_unknown_public_id_404(app, client):
    seed_operator(app)
    r = await client.post(f"/portal/{OP_TOKEN}/requests/REQ-9999-zzzz/confirm")
    assert r.status_code == 404


async def test_portal_post_with_bad_token_404(app, client):
    seed_operator(app)
    # /boats needs the required form field to reach the token check.
    assert (await client.post("/portal/nope/boats", data={"name": "X"})).status_code == 404
    for path in ("/portal/nope/toggle_reachable", "/portal/nope/boats/1/delete",
                 "/portal/nope/requests/REQ-0001-ab12/confirm"):
        assert (await client.post(path)).status_code == 404
