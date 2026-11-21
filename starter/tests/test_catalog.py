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


def seed(app, *, verified: bool = True, boat_name: str = "Lake Queen",
         capacity: int | None = 8, reachable: bool = True,
         embarkation: str = "Alappuzha Finishing Point"):
    with Session(app.state.engine) as s:
        op = Operator(name="Raj Boats", phone="+910000000001", token_hash="x",
                      reachable=reachable)
        s.add(op)
        s.commit()
        s.refresh(op)
        boat = Boat(
            operator_id=op.id,
            name=boat_name,
            capacity=capacity,
            embarkation_point=embarkation,
            source="operator-submitted",
            verified_at=utcnow() if verified else None,
        )
        s.add(boat)
        s.commit()
        s.refresh(boat)
        return op.id, boat.id


# DEMO: tool auth is disabled (main.require_tool_auth returns early), so the
# catalog is reachable without a token. Revisit before any real deployment.
async def test_catalog_open_without_auth(client):
    r = await client.get("/api/catalog/boats")
    assert r.status_code == 200


async def test_catalog_lists_verified_only(app, client):
    seed(app, verified=True, boat_name="Lake Queen")
    seed(app, verified=False, boat_name="Hidden Dinghy")

    r = await client.get("/api/catalog/boats", headers=AUTH)
    assert r.status_code == 200
    names = [b["name"] for b in r.json()["boats"]]
    assert names == ["Lake Queen"]


async def test_catalog_search(app, client):
    seed(app, boat_name="Lake Queen")
    r = await client.get("/api/catalog/boats", params={"q": "queen"}, headers=AUTH)
    assert [b["name"] for b in r.json()["boats"]] == ["Lake Queen"]
    r = await client.get("/api/catalog/boats", params={"q": "yacht"}, headers=AUTH)
    # Keyword miss falls back to the full (small demo) catalog.
    assert [b["name"] for b in r.json()["boats"]] == ["Lake Queen"]


async def test_catalog_search_group_size(app, client):
    seed(app, boat_name="Lake Queen")
    r = await client.get("/api/catalog/boats", params={"q": "boat for 4 people"}, headers=AUTH)
    assert [b["name"] for b in r.json()["boats"]] == ["Lake Queen"]


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


async def test_catalog_get_unknown_id_is_404(client):
    r = await client.get("/api/catalog/boats/4242", headers=AUTH)
    assert r.status_code == 404
    assert r.json()["detail"] == "boat_not_found"


async def test_catalog_search_matches_operator_and_embarkation(app, client):
    seed(app)
    r = await client.get("/api/catalog/boats", params={"q": "raj"}, headers=AUTH)
    assert [b["name"] for b in r.json()["boats"]] == ["Lake Queen"]
    r = await client.get("/api/catalog/boats", params={"q": "finishing point"}, headers=AUTH)
    assert [b["name"] for b in r.json()["boats"]] == ["Lake Queen"]


async def test_catalog_group_size_query_matches_capacity(app, client):
    """'6 people' matches boats with capacity >= 6; smaller boats drop out,
    unknown-capacity boats stay (see catalog.py comment)."""
    seed(app, boat_name="Small Shikara", capacity=4)
    seed(app, boat_name="Big Houseboat", capacity=10)
    seed(app, boat_name="Mystery Canoe", capacity=None)

    r = await client.get("/api/catalog/boats", params={"q": "6 people"}, headers=AUTH)
    names = {b["name"] for b in r.json()["boats"]}
    assert names == {"Big Houseboat", "Mystery Canoe"}


async def test_catalog_out_shape_and_reachable_flag(app, client):
    seed(app, reachable=False)
    r = await client.get("/api/catalog/boats", headers=AUTH)
    (boat,) = r.json()["boats"]
    assert boat["operator_reachable"] is False
    assert set(boat) == {
        "id", "name", "operator_name", "operator_reachable", "capacity",
        "embarkation_point", "photo_urls", "amenities", "price_display",
        "available",
    }
