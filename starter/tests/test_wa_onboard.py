import re

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from app.callbacks import process_due_callbacks
from app.config import Settings
from app.db import Boat, BookingRequest, CallbackRequest, Operator, utcnow
from app.main import create_app
from app.portal import hash_token

SECRET = "test-tool-secret"
AUTH = {"X-Kaayal-Tool-Token": SECRET}
BASE = "https://kaayal.test"


def make_settings() -> Settings:
    return Settings(
        sarvam_tool_shared_secret=SECRET,
        database_url="sqlite://",
        kaayal_public_base_url=BASE,
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


def _token_from(url: str) -> str:
    return url.rsplit("/portal/", 1)[1]


async def test_new_signup_is_pending(client, app):
    r = await client.post(
        "/api/ops/wa_onboard",
        headers=AUTH,
        json={"phone": "919400354625", "name": "Raj", "boat_name": "Lake Queen", "embarkation": "Finishing Point"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "pending_approval" and body["portal_url"] is None
    with Session(app.state.engine) as s:
        op = s.exec(select(Operator)).one()
        assert op.approved_at is None and op.source == "wa-demo"
        boat = s.exec(select(Boat)).one()
        assert boat.name == "Lake Queen" and boat.verified_at is None


async def test_approved_operator_gets_link(client, app):
    with Session(app.state.engine) as s:
        s.add(Operator(name="Raj", phone="+919400354625",
                       token_hash=hash_token("old"), approved_at=utcnow()))
        s.commit()
    r = await client.post(
        "/api/ops/wa_onboard",
        headers=AUTH,
        json={"phone": "+91 94003 54625", "name": "Raj"},
    )
    body = r.json()
    assert body["status"] == "approved" and body["portal_url"].startswith(f"{BASE}/portal/")
    portal = await client.get(f"/portal/{_token_from(body['portal_url'])}")
    assert portal.status_code == 200
    # And the pre-existing token is dead.
    assert (await client.get("/portal/old")).status_code in (403, 404)


async def test_repeat_message_reissues_link(client, app):
    with Session(app.state.engine) as s:
        s.add(Operator(name="Raj", phone="+919400354625",
                       token_hash=hash_token("seed"), approved_at=utcnow()))
        s.commit()
    payload = {"phone": "+91 94003 54625", "name": "Raj"}
    first = (await client.post("/api/ops/wa_onboard", headers=AUTH, json=payload)).json()
    second = (await client.post("/api/ops/wa_onboard", headers=AUTH, json=payload)).json()
    assert first["operator_id"] == second["operator_id"]
    assert first["portal_url"] != second["portal_url"]
    assert (await client.get(f"/portal/{_token_from(first['portal_url'])}")).status_code in (403, 404)
    assert (await client.get(f"/portal/{_token_from(second['portal_url'])}")).status_code == 200


# DEMO: tool auth is disabled (main.require_tool_auth returns early), so
# onboarding accepts calls with no token. Revisit before real use.
async def test_open_without_auth(client):
    r = await client.post("/api/ops/wa_onboard", json={"phone": "919400354625", "name": "R"})
    assert r.status_code == 200


async def test_rejects_invalid_phone(client):
    assert (
        await client.post("/api/ops/wa_onboard", headers=AUTH, json={"phone": "x", "name": "R"})
    ).status_code in (400, 422)


async def test_boat_deduped_on_repeat(client, app):
    payload = {"phone": "919400354625", "name": "Raj", "boat_name": "Lake Queen"}
    await client.post("/api/ops/wa_onboard", headers=AUTH, json=payload)
    r = await client.post("/api/ops/wa_onboard", headers=AUTH, json=payload)
    assert r.status_code == 200
    with Session(app.state.engine) as s:
        boats = s.exec(select(Boat)).all()
        assert len(boats) == 1
        assert r.json()["boat_id"] == boats[0].id


async def test_reissue_unknown_number_404(client):
    r = await client.post("/api/ops/wa_reissue", headers=AUTH, json={"phone": "919400354625"})
    assert r.status_code == 404


async def test_reissue_rejects_invalid_phone(client):
    r = await client.post("/api/ops/wa_reissue", headers=AUTH, json={"phone": "nope!!"})
    assert r.status_code == 400
    assert r.json()["detail"] == "invalid_phone"


async def test_payloads_forbid_extra_fields(client):
    r = await client.post("/api/ops/wa_onboard", headers=AUTH,
                          json={"phone": "919400354625", "name": "R", "admin": True})
    assert r.status_code == 400
    r = await client.post("/api/ops/wa_reissue", headers=AUTH,
                          json={"phone": "919400354625", "boat_name": "X"})
    assert r.status_code == 400


async def test_reissue_pending_returns_no_link(client, app):
    with Session(app.state.engine) as s:
        s.add(Operator(name="Raj", phone="+919400354625",
                       token_hash=hash_token("seed"), approved_at=None))
        s.commit()
    r = await client.post("/api/ops/wa_reissue", headers=AUTH, json={"phone": "919400354625"})
    body = r.json()
    assert r.status_code == 200 and body["status"] == "pending_approval"
    assert body["portal_url"] is None and body["name"] == "Raj"


async def test_reissue_approved_rotates_link(client, app):
    with Session(app.state.engine) as s:
        s.add(Operator(name="Raj", phone="+919400354625",
                       token_hash=hash_token("seed"), approved_at=utcnow()))
        s.commit()
    r = await client.post("/api/ops/wa_reissue", headers=AUTH, json={"phone": "+91 94003 54625"})
    body = r.json()
    assert body["status"] == "approved" and body["portal_url"].startswith(f"{BASE}/portal/")
    assert (await client.get("/portal/seed")).status_code in (403, 404)
    assert (await client.get(f"/portal/{_token_from(body['portal_url'])}")).status_code == 200


async def test_confirm_unknown_number_404(client):
    r = await client.post("/api/ops/wa_confirm", headers=AUTH,
                          json={"phone": "919400354625", "request_id": "REQ-0001-ab12"})
    assert r.status_code == 404


async def test_confirm_request_reveals_caller(client, app):
    with Session(app.state.engine) as s:
        op = Operator(name="Fuad", phone="+919400354625",
                      token_hash=hash_token("x"), approved_at=utcnow())
        s.add(op)
        s.commit()
        boat = Boat(operator_id=op.id, name="Queen", verified_at=utcnow())
        s.add(boat)
        s.commit()

        s.add(BookingRequest(public_id="REQ-0009-ab12", boat_id=boat.id,
                             customer_name="Manan", customer_phone="9845012345",
                             consent_given=True, group_size=4))
        s.commit()
    r = await client.post("/api/ops/wa_confirm", headers=AUTH,
                          json={"phone": "919400354625", "request_id": "req-0009-ab12"})
    body = r.json()
    assert r.status_code == 200 and body["status"] == "confirmed"
    assert body["customer_phone"] == "9845012345" and body["boat_name"] == "Queen"
    # Second confirm is idempotent — still revealed, no error.
    again = (await client.post("/api/ops/wa_confirm", headers=AUTH,
                               json={"phone": "919400354625", "request_id": "REQ-0009-AB12"})).json()
    assert again["status"] == "confirmed"


async def test_confirm_rejects_other_operators_request(client, app):
    with Session(app.state.engine) as s:
        owner = Operator(name="Owner", phone="+911111111111",
                         token_hash=hash_token("x"), approved_at=utcnow())
        other = Operator(name="Other", phone="+912222222222",
                         token_hash=hash_token("y"), approved_at=utcnow())
        s.add(owner)
        s.add(other)
        s.commit()
        boat = Boat(operator_id=owner.id, name="Queen", verified_at=utcnow())
        s.add(boat)
        s.commit()

        s.add(BookingRequest(public_id="REQ-0010-cd34", boat_id=boat.id,
                             customer_name="M", customer_phone="9845012345",
                             consent_given=True))
        s.commit()
    r = await client.post("/api/ops/wa_confirm", headers=AUTH,
                          json={"phone": "2222222222", "request_id": "REQ-0010-CD34"})
    assert r.status_code == 404


def _seed_request(s, phone: str = "+919400354625", req_id: str = "REQ-0011-ef56"):
    op = Operator(name="Fuad", phone=phone, token_hash=hash_token("x"), approved_at=utcnow())
    s.add(op)
    s.commit()
    boat = Boat(operator_id=op.id, name="Queen", verified_at=utcnow())
    s.add(boat)
    s.commit()
    s.add(BookingRequest(public_id=req_id, boat_id=boat.id,
                         customer_name="M", customer_phone="9845012345",
                         consent_given=True))
    s.commit()


async def test_confirm_calls_customer_with_simulated_dialer(client, app):
    app.state.settings.demo_ignore_call_window = True
    with Session(app.state.engine) as s:
        _seed_request(s)
    r = await client.post("/api/ops/wa_confirm", headers=AUTH,
                          json={"phone": "919400354625", "request_id": "REQ-0011-ef56"})
    body = r.json()
    assert body["status"] == "confirmed" and body["notify_channel"] == "call"
    assert body["customer_notified"] is True
    with Session(app.state.engine) as s:
        cb = s.exec(select(CallbackRequest).where(CallbackRequest.reason == "booking_confirmed")).one()
        assert cb.status == "notified" and cb.keywords == "REQ-0011-ef56"


async def test_notify_call_no_answer_falls_back_to_whatsapp(client, app):
    app.state.settings.demo_ignore_call_window = True
    app.state.callback_provider.outcome = "no_answer"
    with Session(app.state.engine) as s:
        _seed_request(s, req_id="REQ-0012-ab34")
    r = await client.post("/api/ops/wa_confirm", headers=AUTH,
                          json={"phone": "919400354625", "request_id": "REQ-0012-ab34"})
    body = r.json()
    assert body["status"] == "confirmed" and body["notify_channel"] == "queued"
    # Second (forced) attempt exhausts retries → WhatsApp fallback fires.
    process_due_callbacks(
        app.state.engine, app.state.callback_provider,
        force=True, ignore_window=True, settings=app.state.settings,
    )
    with Session(app.state.engine) as s:
        cb = s.exec(select(CallbackRequest).where(CallbackRequest.reason == "booking_confirmed")).one()
        assert cb.status == "no_answer"


async def test_requests_lists_pending_only(client, app):
    with Session(app.state.engine) as s:
        op = Operator(name="Fuad", phone="+919400354625",
                      token_hash=hash_token("x"), approved_at=utcnow())
        s.add(op)
        s.commit()
        boat = Boat(operator_id=op.id, name="Queen", verified_at=utcnow())
        s.add(boat)
        s.commit()
        s.add(BookingRequest(public_id="REQ-0001-aa11", boat_id=boat.id,
                             customer_name="A", customer_phone="9845012345",
                             consent_given=True, group_size=4))
        s.add(BookingRequest(public_id="REQ-0002-bb22", boat_id=boat.id,
                             customer_name="B", customer_phone="9845012345",
                             consent_given=True, status="confirmed"))
        s.commit()
    r = await client.post("/api/ops/wa_requests", headers=AUTH, json={"phone": "919400354625"})
    body = r.json()
    assert [x["request_id"] for x in body["requests"]] == ["REQ-0001-aa11"]
    assert body["requests"][0]["customer_name"] == "A"


async def test_reachable_toggle(client, app):
    with Session(app.state.engine) as s:
        s.add(Operator(name="Fuad", phone="+919400354625",
                       token_hash=hash_token("x"), approved_at=utcnow()))
        s.commit()
    r = await client.post("/api/ops/wa_reachable", headers=AUTH,
                          json={"phone": "919400354625", "reachable": False})
    assert r.json()["reachable"] is False
    with Session(app.state.engine) as s:
        assert s.exec(select(Operator)).one().reachable is False
    r = await client.post("/api/ops/wa_reachable", headers=AUTH,
                          json={"phone": "919400354625", "reachable": True})
    assert r.json()["reachable"] is True


async def test_decline_action(client, app):
    with Session(app.state.engine) as s:
        op = Operator(name="Fuad", phone="+919400354625",
                      token_hash=hash_token("x"), approved_at=utcnow())
        s.add(op)
        s.commit()
        boat = Boat(operator_id=op.id, name="Queen", verified_at=utcnow())
        s.add(boat)
        s.commit()
        s.add(BookingRequest(public_id="REQ-0011-ee55", boat_id=boat.id,
                             customer_name="A", customer_phone="9845012345",
                             consent_given=True))
        s.commit()
    r = await client.post("/api/ops/wa_confirm", headers=AUTH,
                          json={"phone": "919400354625", "request_id": "REQ-0011-EE55",
                                "action": "decline"})
    body = r.json()
    assert body["status"] == "declined" and body["customer_phone"] is None


async def test_unverified_boat_hidden_from_catalog(client):
    await client.post(
        "/api/ops/wa_onboard",
        headers=AUTH,
        json={"phone": "919400354625", "name": "Raj", "boat_name": "Lake Queen"},
    )
    r = await client.get("/api/catalog/boats", headers=AUTH)
    assert r.status_code == 200 and r.json()["boats"] == []
