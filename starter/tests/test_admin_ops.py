import re

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session

from app.config import Settings
from app.db import Boat, Operator, utcnow
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
        op = Operator(name="Raj Boats", phone="+910000000001", token_hash=hash_token(OP_TOKEN))
        s.add(op)
        s.commit()
        s.refresh(op)
        boat = Boat(operator_id=op.id, name="Lake Queen", capacity=8,
                    embarkation_point="Finishing Point",
                    verified_at=utcnow() if verified else None)
        s.add(boat)
        s.commit()
        s.refresh(boat)
        return op.id, boat.id


def portal_token_from(html_text: str) -> str:
    m = re.search(r"/portal/([A-Za-z0-9_-]{20,})", html_text)
    assert m, "no portal URL found in response"
    return m.group(1)


# --- admin operator lifecycle ---

async def test_operator_actions_require_admin(app, client):
    op_id, _ = seed_operator(app)
    for path in ("reissue", "deactivate", "reactivate"):
        assert (await client.post(f"/admin/operators/{op_id}/{path}")).status_code == 401
        assert (await client.post(f"/admin/operators/{op_id}/{path}?t=wrong")).status_code == 401


async def test_reissue_rotates_portal_url(app, client):
    op_id, _ = seed_operator(app)
    r = await client.post(f"/admin/operators/{op_id}/reissue?t={ADMIN}")
    assert r.status_code == 200
    new_token = portal_token_from(r.text)
    assert new_token != OP_TOKEN
    # old link dies immediately, new link works
    assert (await client.get(f"/portal/{OP_TOKEN}")).status_code in (403, 404)
    assert (await client.get(f"/portal/{new_token}")).status_code == 200
    with Session(app.state.engine) as s:
        assert s.get(Operator, op_id).token_hash == hash_token(new_token)


async def test_reissue_unknown_operator_404(client):
    r = await client.post(f"/admin/operators/9999/reissue?t={ADMIN}")
    assert r.status_code == 404


async def test_deactivate_blocks_portal(app, client):
    op_id, _ = seed_operator(app)
    r = await client.post(f"/admin/operators/{op_id}/deactivate?t={ADMIN}", follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        assert s.get(Operator, op_id).active is False
    assert (await client.get(f"/portal/{OP_TOKEN}")).status_code in (403, 404)
    # portal POSTs are blocked too
    assert (await client.post(f"/portal/{OP_TOKEN}/boats", data={"name": "X"})).status_code in (403, 404)


async def test_deactivated_operator_boats_leave_catalog(app, client):
    op_id, boat_id = seed_operator(app, verified=True)
    r = await client.get("/api/catalog/boats", headers=AUTH)
    assert [b["name"] for b in r.json()] == ["Lake Queen"]
    await client.post(f"/admin/operators/{op_id}/deactivate?t={ADMIN}")
    assert (await client.get("/api/catalog/boats", headers=AUTH)).json() == []
    assert (await client.get(f"/api/catalog/boats/{boat_id}", headers=AUTH)).status_code == 404


async def test_reactivate_restores_portal(app, client):
    op_id, _ = seed_operator(app)
    await client.post(f"/admin/operators/{op_id}/deactivate?t={ADMIN}")
    assert (await client.get(f"/portal/{OP_TOKEN}")).status_code in (403, 404)
    r = await client.post(f"/admin/operators/{op_id}/reactivate?t={ADMIN}", follow_redirects=False)
    assert r.status_code == 303
    page = await client.get(f"/portal/{OP_TOKEN}")
    assert page.status_code == 200
    assert "Lake Queen" in page.text


async def test_admin_lists_inactive_operators(app, client):
    op_id, _ = seed_operator(app)
    await client.post(f"/admin/operators/{op_id}/deactivate?t={ADMIN}")
    r = await client.get(f"/admin?t={ADMIN}")
    assert r.status_code == 200
    assert "Raj Boats" in r.text
    assert "Reactivate" in r.text
