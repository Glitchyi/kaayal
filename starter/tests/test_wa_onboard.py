import re

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from app.config import Settings
from app.db import Boat, Operator, utcnow
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


async def test_requires_auth_and_valid_phone(client):
    assert (await client.post("/api/ops/wa_onboard", json={"phone": "919400354625", "name": "R"})).status_code == 401
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


async def test_unverified_boat_hidden_from_catalog(client):
    await client.post(
        "/api/ops/wa_onboard",
        headers=AUTH,
        json={"phone": "919400354625", "name": "Raj", "boat_name": "Lake Queen"},
    )
    r = await client.get("/api/catalog/boats", headers=AUTH)
    assert r.status_code == 200 and r.json() == []
