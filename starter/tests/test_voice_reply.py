import logging

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.main import create_app
from app.openai_adapter import OpenAIAdapterError

SECRET = "test-tool-secret"


def make_test_settings(**overrides) -> Settings:
    base = dict(
        openai_api_key=None,
        sarvam_tool_shared_secret=SECRET,
        rate_limit_per_minute=60,
        database_url="sqlite://",
        _env_file=None,
    )
    base.update(overrides)
    return Settings(**base)


async def ok_responder(utterance: str, language: str | None) -> str:
    return "Kaayal can answer simple questions over the phone."


async def failing_responder(utterance: str, language: str | None) -> str:
    raise OpenAIAdapterError("openai timeout")


@pytest.fixture
def app():
    return create_app(settings=make_test_settings(), responder=ok_responder)


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


AUTH = {"X-Kaayal-Tool-Token": SECRET}


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_reply_success(client):
    r = await client.post(
        "/api/voice/reply",
        json={"utterance": "What can Kaayal do?", "interaction_id": "call-123", "language": "en-IN"},
        headers=AUTH,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["reply_text"]
    assert body["trace_id"]


async def test_reply_missing_token(client):
    r = await client.post("/api/voice/reply", json={"utterance": "hello"})
    assert r.status_code == 401


async def test_reply_wrong_token(client):
    r = await client.post(
        "/api/voice/reply",
        json={"utterance": "hello"},
        headers={"X-Kaayal-Tool-Token": "wrong"},
    )
    assert r.status_code == 401


async def test_reply_missing_utterance(client):
    r = await client.post("/api/voice/reply", json={"language": "ml-IN"}, headers=AUTH)
    assert r.status_code == 400


async def test_reply_empty_utterance(client):
    r = await client.post("/api/voice/reply", json={"utterance": ""}, headers=AUTH)
    assert r.status_code == 400


async def test_reply_oversized_utterance(client):
    r = await client.post("/api/voice/reply", json={"utterance": "x" * 2001}, headers=AUTH)
    assert r.status_code == 400


async def test_reply_extra_field_rejected(client):
    r = await client.post(
        "/api/voice/reply",
        json={"utterance": "hi", "caller_phone": "+911234"},
        headers=AUTH,
    )
    assert r.status_code == 400


async def test_reply_not_json(client):
    r = await client.post(
        "/api/voice/reply",
        content="utterance=hi",
        headers={**AUTH, "Content-Type": "application/x-www-form-urlencoded"},
    )
    assert r.status_code == 400


async def test_reply_upstream_error_returns_502():
    app = create_app(settings=make_test_settings(), responder=failing_responder)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/voice/reply", json={"utterance": "hi"}, headers=AUTH)
    assert r.status_code == 502
    assert r.json()["trace_id"]


async def test_reply_unconfigured_secret_returns_503():
    app = create_app(settings=make_test_settings(sarvam_tool_shared_secret=None), responder=ok_responder)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/api/voice/reply", json={"utterance": "hi"}, headers=AUTH)
    assert r.status_code == 503


async def test_rate_limit():
    app = create_app(settings=make_test_settings(rate_limit_per_minute=2), responder=ok_responder)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        codes = [
            (await c.post("/api/voice/reply", json={"utterance": "hi"}, headers=AUTH)).status_code
            for _ in range(3)
        ]
    assert codes[:2] == [200, 200]
    assert codes[2] == 429


async def test_utterance_never_logged(client, caplog):
    secret_text = "un1qu3-utterance-string"
    with caplog.at_level(logging.INFO, logger="kaayal"):
        r = await client.post(
            "/api/voice/reply",
            json={"utterance": secret_text, "interaction_id": "int-9"},
            headers=AUTH,
        )
    assert r.status_code == 200
    logged = "\n".join(rec.getMessage() for rec in caplog.records)
    assert secret_text not in logged
    assert "int-9" in logged
