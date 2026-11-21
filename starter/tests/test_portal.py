import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.config import Settings
from app.db import Boat, BookingRequest, Operator, utcnow
from app.main import create_app
from app.portal import hash_token

SECRET = "test-tool-secret"
ADMIN = "test-admin-token"
OP_TOKEN = "op-portal-token-abc"
AUTH = {"X-Kaayal-Tool-Token": SECRET}


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


# --- voice request endpoint ---

# DEMO: tool auth is disabled (main.require_tool_auth returns early), so the
# voice-request endpoint accepts calls with no token. Revisit before real use.
async def test_create_request_open_without_auth(client):
    r = await client.post("/api/voice/request", json={
        "customer_name": "Anu", "customer_phone": "+9198765", "consent_given": True})
    assert r.status_code == 200
    assert r.json()["status"] == "pending"


async def test_create_request_consent_required(client):
    r = await client.post("/api/voice/request", headers=AUTH, json={
        "customer_name": "Anu", "customer_phone": "+9198765", "consent_given": False})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"


async def test_create_request_bad_phone_rejected(client):
    r = await client.post("/api/voice/request", headers=AUTH, json={
        "customer_name": "Anu", "customer_phone": "not a phone", "consent_given": True})
    assert r.json()["status"] == "rejected"


async def test_create_request_success_pending(app, client):
    _, boat = seed_operator(app)
    r = await client.post("/api/voice/request", headers=AUTH, json={
        "customer_name": "Anu", "customer_phone": "+91 98765 43210",
        "consent_given": True, "boat_id": boat.id, "preferred_date": "2026-12-01",
        "group_size": 4})
    body = r.json()
    assert body["status"] == "pending"
    assert body["request_id"].startswith("REQ-")


async def test_create_request_unverified_boat_rejected(app, client):
    _, boat = seed_operator(app, verified=False)
    r = await client.post("/api/voice/request", headers=AUTH, json={
        "customer_name": "Anu", "customer_phone": "+919876543210",
        "consent_given": True, "boat_id": boat.id})
    assert r.json()["status"] == "rejected"


async def test_create_request_no_boat_goes_to_triage(app, client):
    r = await client.post("/api/voice/request", headers=AUTH, json={
        "customer_name": "Anu", "customer_phone": "+919876543210", "consent_given": True})
    assert r.json()["status"] == "pending"


# --- operator portal ---

async def test_portal_bad_token_404(client):
    r = await client.get("/portal/nope")
    assert r.status_code == 404


async def test_portal_dashboard_shows_boats_and_requests(app, client):
    _, boat = seed_operator(app)
    seed_request(app, boat.id)
    r = await client.get(f"/portal/{OP_TOKEN}")
    assert r.status_code == 200
    assert "Lake Queen" in r.text
    assert "REQ-0001-ab12" in r.text
    # customer phone hidden until confirmed
    assert "+919876543210" not in r.text


async def test_portal_add_boat_is_unverified(app, client):
    seed_operator(app)
    r = await client.post(f"/portal/{OP_TOKEN}/boats",
                          data={"name": "New Cruiser", "capacity": "6"},
                          follow_redirects=False)
    assert r.status_code == 303
    from sqlmodel import select as _select

    with Session(app.state.engine) as s:
        boats = s.exec(_select(Boat).where(Boat.name == "New Cruiser")).all()
    assert len(boats) == 1 and boats[0].verified_at is None


async def test_portal_confirm_reveals_contact(app, client):
    _, boat = seed_operator(app)
    req = seed_request(app, boat.id)
    r = await client.post(f"/portal/{OP_TOKEN}/requests/{req.public_id}/confirm",
                          follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(BookingRequest, req.id).status == "confirmed"
    page = await client.get(f"/portal/{OP_TOKEN}")
    assert "+919876543210" in page.text


async def test_portal_block_request(app, client):
    _, boat = seed_operator(app)
    req = seed_request(app, boat.id)
    await client.post(f"/portal/{OP_TOKEN}/requests/{req.public_id}/block")
    with Session(app.state.engine) as s:
        assert s.get(BookingRequest, req.id).status == "blocked"


async def test_portal_cannot_touch_other_operators_request(app, client):
    _, boat = seed_operator(app)
    req = seed_request(app, boat.id)
    with Session(app.state.engine) as s:
        s.add(Operator(name="Other", phone="+9102", token_hash=hash_token("other-token"), approved_at=utcnow()))
        s.commit()
    r = await client.post("/portal/other-token/requests/REQ-0001-ab12/confirm")
    assert r.status_code == 404
    with Session(app.state.engine) as s:
        assert s.get(BookingRequest, req.id).status == "pending"


# --- admin ---

async def test_admin_requires_token(client):
    assert (await client.get("/admin")).status_code == 401
    assert (await client.get("/admin?t=wrong")).status_code == 401


async def test_admin_create_operator_returns_portal_url(app, client):
    r = await client.post(f"/admin/operators?t={ADMIN}",
                          data={"name": "Kerala Crafts Boats", "phone": "+910001"})
    assert r.status_code == 200
    assert "/portal/" in r.text


async def test_admin_verify_boat(app, client):
    _, boat = seed_operator(app, verified=False)
    r = await client.post(f"/admin/boats/{boat.id}/verify?t={ADMIN}", follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(Boat, boat.id).verified_at is not None


# --- landing ---

async def test_landing_lists_verified_only(app, client):
    seed_operator(app, verified=True)
    with Session(app.state.engine) as s:
        s.add(Boat(operator_id=1, name="Secret Boat", verified_at=None))
        s.commit()
    r = await client.get("/")
    assert r.status_code == 200
    assert "Lake Queen" in r.text
    assert "Secret Boat" not in r.text
