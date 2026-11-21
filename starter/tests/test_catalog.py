import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.config import Settings
from app.db import Operator, Boat, utcnow
from app.main import create_app

SECRET = "test-tool-secret"
AUTH = {"X-Kaayal-Tool-Token": SECRET}


def make_settings() -> Settings:
    return Settings(
        sarvam_tool_shared_secret=SECRET,
        database_url="sqlite://",
        _env_file=None,
    )


async def noop_responder(u: str, lang: str | None) -> str:
    return "ok"


@pytest.fixture
def app():
    return create_app(settings=make_settings(), responder=noop_responder)


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def seed(app, *, verified: bool = True, boat_name: str = "Lake Queen"):
    with Session(app.state.engine) as s:
        op = Operator(name="Raj Boats", phone="+910000000001", token_hash="x")
        s.add(op)
        s.commit()
        s.refresh(op)
        boat = Boat(
            operator_id=op.id,
            name=boat_name,
            capacity=8,
            embarkation_point="Alappuzha Finishing Point",
            source="operator-submitted",
            verified_at=utcnow() if verified else None,
        )
        s.add(boat)
        s.commit()
        s.refresh(boat)
        return op.id, boat.id


async def test_catalog_requires_auth(client):
    r = await client.get("/api/catalog/boats")
    assert r.status_code == 401


async def test_catalog_lists_verified_only(app, client):
    seed(app, verified=True, boat_name="Lake Queen")
    seed(app, verified=False, boat_name="Hidden Dinghy")

    r = await client.get("/api/catalog/boats", headers=AUTH)
    assert r.status_code == 200
    names = [b["name"] for b in r.json()]
    assert names == ["Lake Queen"]


async def test_catalog_search(app, client):
    seed(app, boat_name="Lake Queen")
    r = await client.get("/api/catalog/boats", params={"q": "queen"}, headers=AUTH)
    assert [b["name"] for b in r.json()] == ["Lake Queen"]
    r = await client.get("/api/catalog/boats", params={"q": "yacht"}, headers=AUTH)
    assert r.json() == []


async def test_catalog_get_boat(app, client):
    _, boat_id = seed(app)
    r = await client.get(f"/api/catalog/boats/{boat_id}", headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert body["operator_name"] == "Raj Boats"
    assert body["embarkation_point"] == "Alappuzha Finishing Point"


async def test_catalog_get_unverified_is_404(app, client):
    _, boat_id = seed(app, verified=False)
    r = await client.get(f"/api/catalog/boats/{boat_id}", headers=AUTH)
    assert r.status_code == 404
