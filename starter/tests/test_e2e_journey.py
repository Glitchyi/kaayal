"""End-to-end journey suite — walks the whole product over HTTP with stubbed
externals (no real OpenAI, WhatsApp, or outbound calls).

Mirrors docs/demo-runbook.md: WhatsApp-sim operator onboarding → admin
approval → boat verification → voice booking inquiry → masked/confirmed
request flow → callback triggers → simulated dialer → opt-outs → admin ops.
Each test gets a fresh in-memory app; wa_notify._send is monkeypatched to
record what *would* be pushed to WhatsApp.
"""

import re
from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, select

from app import wa_notify
from app.callbacks import process_due_callbacks
from app.config import Settings
from app.db import Boat, BookingRequest, CallbackAttempt, CallbackRequest, Operator, utcnow
from app.main import create_app
from app.openai_adapter import OpenAIAdapterError
from app.pii import anonymize_stale_requests

ADMIN = "test-admin-token"
BASE = "https://kaayal.test"

OP_PHONE = "+919000000001"
OP2_PHONE = "+919000000002"
CUST_PHONE = "+919800000001"


def make_settings(**overrides) -> Settings:
    base = dict(
        admin_token=ADMIN,
        database_url="sqlite://",
        kaayal_public_base_url=BASE,
        demo_ignore_call_window=True,
        sim_callback_outcome="interested",
        _env_file=None,
    )
    base.update(overrides)
    return Settings(**base)


def make_app(**overrides):
    return create_app(settings=make_settings(**overrides), responder=noop_responder)


async def noop_responder(u, lang):
    return "Kaayal can answer simple questions over the phone."


async def failing_responder(u, lang):
    raise OpenAIAdapterError("openai timeout")


@pytest.fixture
def app():
    return make_app()


@pytest.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
def wa_outbox(monkeypatch):
    """Records every WhatsApp message the app would send via wa-bot /send."""
    sent = []

    def fake_send(settings, phone, text):
        sent.append({"phone": phone, "text": text})
        return True

    monkeypatch.setattr(wa_notify, "_send", fake_send)
    return sent


# ---------------------------------------------------------------------------
# Journey helpers — every step goes through the real HTTP endpoints.
# ---------------------------------------------------------------------------

def _token_from(html: str) -> str:
    m = re.search(r"/portal/([A-Za-z0-9_-]{20,})", html)
    assert m, "no portal URL found in response"
    return m.group(1)


async def onboard_operator(client, phone=OP_PHONE, name="Raj Boat Service",
                           boat_name="Lake Queen", boat_type="shikara",
                           embarkation="Finishing Point") -> dict:
    r = await client.post("/api/ops/wa_onboard", json={
        "phone": phone, "name": name, "boat_name": boat_name,
        "boat_type": boat_type, "embarkation": embarkation,
    })
    assert r.status_code == 200
    return r.json()


async def approve_operator(client, op_id: int) -> str:
    r = await client.post(f"/admin/operators/{op_id}/approve?t={ADMIN}")
    assert r.status_code == 200
    return _token_from(r.text)


async def verify_boat(client, boat_id: int) -> None:
    r = await client.post(f"/admin/boats/{boat_id}/verify?t={ADMIN}", follow_redirects=False)
    assert r.status_code == 303


async def approved_listing(client, wa_outbox=None, phone=OP_PHONE,
                           boat_name="Lake Queen") -> tuple[str, int, int]:
    """wa_onboard → admin approve → admin verify. Returns (token, op_id, boat_id)."""
    body = await onboard_operator(client, phone=phone, boat_name=boat_name)
    token = await approve_operator(client, body["operator_id"])
    await verify_boat(client, body["boat_id"])
    return token, body["operator_id"], body["boat_id"]


async def voice_request(client, boat_id, name="Anu", phone=CUST_PHONE,
                        consent=True, **extra) -> dict:
    r = await client.post("/api/voice/request", json={
        "customer_name": name, "customer_phone": phone,
        "consent_given": consent, "boat_id": boat_id,
        "preferred_date": "2026-12-24", "group_size": 4, **extra,
    })
    assert r.status_code == 200
    return r.json()


async def voice_callback(client, boat_id, reason, name="Anu",
                         phone=CUST_PHONE, consent=True, **extra) -> dict:
    r = await client.post("/api/voice/callback", json={
        "customer_name": name, "customer_phone": phone,
        "consent_given": consent, "reason": reason,
        "boat_id": boat_id, **extra,
    })
    assert r.status_code == 200
    return r.json()


async def run_due(client) -> None:
    r = await client.post(f"/admin/callbacks/run_due?t={ADMIN}", follow_redirects=False)
    assert r.status_code == 303


def one_cb(app, **where):
    with Session(app.state.engine) as s:
        q = select(CallbackRequest)
        for k, v in where.items():
            q = q.where(getattr(CallbackRequest, k) == v)
        return s.exec(q).one()


# ---------------------------------------------------------------------------
# S1 — WhatsApp-sim onboarding → pending → approve → portal → verify → catalog
# ---------------------------------------------------------------------------

async def test_s1_operator_onboarding_to_listed_boat(app, client, wa_outbox):
    # New self-signup: pending, no portal access, boat hidden from callers.
    body = await onboard_operator(client)
    assert body["status"] == "pending_approval" and body["portal_url"] is None
    assert (await client.get("/portal/whatever")).status_code == 404
    assert (await client.get("/api/catalog/boats")).json() == {"boats": []}
    with Session(app.state.engine) as s:
        op = s.get(Operator, body["operator_id"])
        boat = s.get(Boat, body["boat_id"])
        assert op.approved_at is None and op.source == "wa-demo"
        assert boat.verified_at is None and boat.boat_type == "shikara"

    # Owner approves → link minted once in HTML, pushed over WhatsApp too.
    token = await approve_operator(client, body["operator_id"])
    assert len(wa_outbox) == 1
    assert wa_outbox[0]["phone"] == OP_PHONE
    assert f"/portal/{token}" in wa_outbox[0]["text"]
    page = await client.get(f"/portal/{token}")
    assert page.status_code == 200 and "Raj Boat Service" in page.text

    # Repeat DM → fresh link; the previous one dies immediately.
    r = await client.post("/api/ops/wa_reissue", json={"phone": OP_PHONE})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    new_token = _token_from(r.json()["portal_url"])
    assert new_token != token
    assert (await client.get(f"/portal/{token}")).status_code == 404
    token = new_token
    assert (await client.get(f"/portal/{token}")).status_code == 200
    assert (await client.post("/api/ops/wa_reissue",
                              json={"phone": "+919999999999"})).status_code == 404

    # Owner verifies the boat → callers can finally see it.
    await verify_boat(client, body["boat_id"])
    boats = (await client.get("/api/catalog/boats")).json()["boats"]
    assert [b["name"] for b in boats] == ["Lake Queen"]
    detail = await client.get(f"/api/catalog/boats/{body['boat_id']}")
    assert detail.status_code == 200
    assert detail.json()["operator_name"] == "Raj Boat Service"


async def test_wa_onboard_repeat_dm_reissues_link(app, client):
    await onboard_operator(client)
    first = await onboard_operator(client, phone="+91 90000 00001")
    # Still pending — normalized digits matched the same operator.
    assert first["status"] == "pending_approval" and first["portal_url"] is None


# ---------------------------------------------------------------------------
# S2 — happy path: inquiry → masked → confirm → notify call → caller context
# ---------------------------------------------------------------------------

async def test_s2_booking_request_confirm_and_notify(app, client, wa_outbox):
    token, op_id, boat_id = await approved_listing(client)

    body = await voice_request(client, boat_id)
    assert body["status"] == "pending" and body["request_id"].startswith("REQ-")
    req_id = body["request_id"]

    # Operator got a booking ping over WhatsApp — no customer PII in it.
    ping = next(m for m in wa_outbox if req_id in m["text"])
    assert ping["phone"] == OP_PHONE
    assert "9800000001" not in re.sub(r"\D", "", ping["text"])

    # WhatsApp-side view: pending request listed; portal keeps the number masked.
    reqs = await client.post("/api/ops/wa_requests", json={"phone": OP_PHONE})
    assert reqs.status_code == 200
    assert reqs.json()["requests"][0]["request_id"] == req_id
    page = await client.get(f"/portal/{token}")
    assert req_id in page.text and CUST_PHONE not in page.text
    assert "number revealed after you confirm" in page.text

    # Confirm → number unmasked; booking_confirmed notify call fires and the
    # simulator "connects" → notified.
    r = await client.post(
        f"/portal/{token}/requests/{req_id}/confirm", follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        req = s.exec(select(BookingRequest).where(BookingRequest.public_id == req_id)).one()
        assert req.status == "confirmed"
        cb = s.exec(select(CallbackRequest).where(
            CallbackRequest.reason == "booking_confirmed")).one()
        assert cb.status == "notified"
        assert s.exec(select(CallbackAttempt).where(
            CallbackAttempt.callback_id == cb.id)).one().outcome == "interested"
    page = await client.get(f"/portal/{token}")
    assert CUST_PHONE in page.text and "wa.me/" in page.text

    # Paayal recognizes the caller on their next call.
    ctx = await client.post("/api/voice/caller_context",
                            json={"customer_phone": CUST_PHONE})
    assert ctx.json()["known"] is True
    assert ctx.json()["requests"][0]["request_id"] == req_id


async def test_wa_confirm_path_matches_portal(app, client, wa_outbox):
    await approved_listing(client)
    req_id = (await voice_request(client, 1))["request_id"]

    r = await client.post("/api/ops/wa_confirm", json={
        "phone": OP_PHONE, "request_id": req_id.lower(), "action": "confirm",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "confirmed"
    assert body["customer_phone"] == CUST_PHONE  # unmasked by confirming
    assert body["customer_notified"] is True and body["notify_channel"] == "call"

    # Cross-operator isolation: another operator can't touch the request.
    other = await onboard_operator(client, phone=OP2_PHONE, name="Other Tours",
                                   boat_name="Sea Pearl")
    await approve_operator(client, other["operator_id"])
    r = await client.post("/api/ops/wa_confirm", json={
        "phone": OP2_PHONE, "request_id": req_id, "action": "confirm"})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# S3 — boat unavailable → callback parked → availability flip → conversion
# ---------------------------------------------------------------------------

async def test_s3_unavailable_boat_callback_converts(app, client):
    token, op_id, boat_id = await approved_listing(client)

    r = await client.post(f"/portal/{token}/boats/{boat_id}/toggle_available",
                          follow_redirects=False)
    assert r.status_code == 303
    body = await voice_request(client, boat_id)
    assert body["status"] == "unavailable" and "callback" in body["message"].lower()

    cb_body = await voice_callback(client, boat_id, "no_availability")
    assert cb_body["status"] == "queued" and cb_body["request_id"].startswith("CB-")
    cb = one_cb(app, public_id=cb_body["request_id"])
    assert cb.next_attempt_at == cb.expires_at  # parked — never dialed untriggered

    # Operator flips availability back on → callback requeued, engine converts.
    await client.post(f"/portal/{token}/boats/{boat_id}/toggle_available")
    cb = one_cb(app, public_id=cb_body["request_id"])
    assert cb.trigger_seq == 1 and cb.status == "queued"
    await run_due(client)
    with Session(app.state.engine) as s:
        cb = s.exec(select(CallbackRequest).where(
            CallbackRequest.public_id == cb_body["request_id"])).one()
        assert cb.status == "converted"
        att = s.exec(select(CallbackAttempt).where(
            CallbackAttempt.callback_id == cb.id)).one()
        assert att.outcome == "interested" and att.provider == "simulator"
        assert any(t["who"] == "paayal" for t in att.transcript)
        req = s.exec(select(BookingRequest).where(BookingRequest.source == "callback")).one()
        assert req.status == "pending" and req.boat_id == boat_id

    # Operator confirms the auto-created inquiry over WhatsApp.
    r = await client.post("/api/ops/wa_confirm", json={
        "phone": OP_PHONE, "request_id": req.public_id, "action": "confirm"})
    assert r.json()["status"] == "confirmed"


# ---------------------------------------------------------------------------
# S4 — operator unreachable → callback → reachable flip → conversion
# ---------------------------------------------------------------------------

async def test_s4_unreachable_operator_callback_converts(app, client):
    token, op_id, boat_id = await approved_listing(client)

    r = await client.post("/api/ops/wa_reachable",
                          json={"phone": OP_PHONE, "reachable": False})
    assert r.status_code == 200 and r.json()["reachable"] is False
    body = await voice_request(client, boat_id)
    assert body["status"] == "unreachable"

    cb_body = await voice_callback(client, boat_id, "operator_unreachable")
    assert cb_body["status"] == "queued"
    assert one_cb(app, public_id=cb_body["request_id"]).operator_id == op_id

    r = await client.post("/api/ops/wa_reachable",
                          json={"phone": OP_PHONE, "reachable": True})
    assert r.json()["reachable"] is True
    cb = one_cb(app, public_id=cb_body["request_id"])
    assert cb.trigger_seq == 1 and cb.status == "queued"
    await run_due(client)
    assert one_cb(app, public_id=cb_body["request_id"]).status == "converted"


# ---------------------------------------------------------------------------
# S5 — simulator outcome branches
# ---------------------------------------------------------------------------

async def test_s5_not_interested_is_terminal_no_inquiry():
    a = make_app(sim_callback_outcome="not_interested")
    async with AsyncClient(transport=ASGITransport(app=a), base_url="http://test") as c:
        token, op_id, boat_id = await approved_listing(c)
        await c.post(f"/portal/{token}/boats/{boat_id}/toggle_available")
        cb_body = await voice_callback(c, boat_id, "no_availability")
        await c.post(f"/portal/{token}/boats/{boat_id}/toggle_available")
        await c.post(f"/admin/callbacks/run_due?t={ADMIN}", follow_redirects=False)
    with Session(a.state.engine) as s:
        cb = s.exec(select(CallbackRequest)).one()
        assert cb.status == "not_interested"
        assert s.exec(select(BookingRequest)).all() == []


async def test_s5_no_answer_retries_twice_then_terminal():
    a = make_app(sim_callback_outcome="no_answer")
    async with AsyncClient(transport=ASGITransport(app=a), base_url="http://test") as c:
        token, op_id, boat_id = await approved_listing(c)
        await c.post(f"/portal/{token}/boats/{boat_id}/toggle_available")
        cb_body = await voice_callback(c, boat_id, "no_availability")
        await c.post(f"/portal/{token}/boats/{boat_id}/toggle_available")
        for _ in range(2):
            await c.post(f"/admin/callbacks/run_due?t={ADMIN}", follow_redirects=False)
    with Session(a.state.engine) as s:
        cb = s.exec(select(CallbackRequest)).one()
        assert cb.status == "no_answer" and cb.attempts_this_trigger == 2
        attempts = s.exec(select(CallbackAttempt)).all()
        assert len(attempts) == 2 and all(a2.outcome == "no_answer" for a2 in attempts)


async def test_s5_confirmed_notify_no_answer_falls_back_to_whatsapp(wa_outbox):
    a = make_app(sim_callback_outcome="no_answer")
    async with AsyncClient(transport=ASGITransport(app=a), base_url="http://test") as c:
        token, op_id, boat_id = await approved_listing(c)
        req_id = (await voice_request(c, boat_id))["request_id"]
        # Confirm → notify call attempt 1 (no_answer) → queued for retry.
        await c.post(f"/portal/{token}/requests/{req_id}/confirm")
        # Forced run → attempt 2 → exhausted → WhatsApp fallback fires.
        await c.post(f"/admin/callbacks/run_due?t={ADMIN}", follow_redirects=False)
    with Session(a.state.engine) as s:
        cb = s.exec(select(CallbackRequest).where(
            CallbackRequest.reason == "booking_confirmed")).one()
        assert cb.status == "no_answer" and cb.attempts_this_trigger == 2
    confirm_msgs = [m for m in wa_outbox if m["phone"] == CUST_PHONE]
    assert len(confirm_msgs) == 1 and "confirmed" in confirm_msgs[0]["text"].lower()
    assert req_id in confirm_msgs[0]["text"]


# ---------------------------------------------------------------------------
# S6 — opt-outs and admin cancel
# ---------------------------------------------------------------------------

async def test_s6_opt_out_withdraws_all_active_callbacks(app, client):
    token, op_id, boat_id = await approved_listing(client, boat_name="Lake Queen")
    cb1 = await voice_callback(client, boat_id, "no_availability")
    cb2 = await voice_callback(client, boat_id, "operator_unreachable")

    r = await voice_callback(client, boat_id, "no_availability", consent=False)
    assert r["status"] == "opted_out"
    for pid in (cb1["request_id"], cb2["request_id"]):
        assert one_cb(app, public_id=pid).status == "opted_out"

    # Nothing to withdraw → honest "rejected".
    r = await client.post("/api/voice/callback", json={
        "customer_name": "Meera", "customer_phone": "+919800000099",
        "consent_given": False, "reason": "no_availability"})
    assert r.json()["status"] == "rejected"


async def test_s6_admin_cancel_marks_opted_out(app, client):
    await approved_listing(client)
    cb_body = await voice_callback(client, 1, "no_availability")
    cb = one_cb(app, public_id=cb_body["request_id"])
    r = await client.post(f"/admin/callbacks/{cb.id}/cancel?t={ADMIN}",
                          follow_redirects=False)
    assert r.status_code == 303
    assert one_cb(app, public_id=cb_body["request_id"]).status == "opted_out"


# ---------------------------------------------------------------------------
# S7 — admin & portal day-to-day ops
# ---------------------------------------------------------------------------

async def test_s7_admin_created_operator_deactivate_reactivate(app, client):
    r = await client.post(f"/admin/operators?t={ADMIN}",
                          data={"name": "Pre Approved Tours", "phone": "+919000000003"})
    assert r.status_code == 200
    token = _token_from(r.text)
    with Session(app.state.engine) as s:
        op = s.exec(select(Operator).where(Operator.name == "Pre Approved Tours")).one()
        assert op.approved_at is not None and op.source == "admin"
        op_id = op.id

    # Portal → add boat → unverified → hidden → verify → listed.
    r = await client.post(f"/portal/{token}/boats", data={
        "name": "Morning Mist", "boat_type": "houseboat", "capacity": "8",
        "embarkation_point": "Punnamada", "price_display": "₹9,500/night",
        "amenities": "AC, meals, upper deck", "photo_url": "",
    }, follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        boat = s.exec(select(Boat).where(Boat.name == "Morning Mist")).one()
        assert boat.verified_at is None and boat.source == "operator-submitted"
        assert boat.amenities == ["AC", "meals", "upper deck"] and boat.capacity == 8
        boat_id = boat.id
    assert (await client.get("/api/catalog/boats")).json() == {"boats": []}
    await verify_boat(client, boat_id)
    boats = (await client.get("/api/catalog/boats")).json()["boats"]
    assert boats[0]["name"] == "Morning Mist"

    # Catalog search: name/type/group-size matching, miss → full catalog.
    assert (await client.get("/api/catalog/boats?q=houseboat")).json()["boats"]
    assert (await client.get("/api/catalog/boats?q=8 people")).json()["boats"]
    assert (await client.get("/api/catalog/boats?q=zzz")).json()["boats"]

    # Deactivate → boats vanish for callers; reactivate → back.
    await client.post(f"/admin/operators/{op_id}/deactivate?t={ADMIN}")
    assert (await client.get("/api/catalog/boats")).json() == {"boats": []}
    await client.post(f"/admin/operators/{op_id}/reactivate?t={ADMIN}")
    assert (await client.get("/api/catalog/boats")).json()["boats"]


async def test_s7_portal_boat_delete_and_request_transitions(app, client):
    # "Pearl Diver" — the portal's add-boat form placeholder is "e.g. Lake
    # Queen", so a unique name keeps the delete assertion honest.
    token, op_id, boat_id = await approved_listing(client, boat_name="Pearl Diver")
    req_id = (await voice_request(client, boat_id))["request_id"]

    # Decline + block are one-way transitions on pending requests.
    r = await client.post(f"/portal/{token}/requests/{req_id}/decline",
                          follow_redirects=False)
    assert r.status_code == 303
    with Session(app.state.engine) as s:
        req = s.exec(select(BookingRequest).where(
            BookingRequest.public_id == req_id)).one()
        assert req.status == "declined"

    req2 = (await voice_request(client, boat_id, name="Vikram",
                                phone="+919800000002"))["request_id"]
    await client.post(f"/portal/{token}/requests/{req2}/block")
    with Session(app.state.engine) as s:
        req = s.exec(select(BookingRequest).where(
            BookingRequest.public_id == req2)).one()
        assert req.status == "blocked"

    # Delete = soft-delete: hidden from catalog and the portal.
    await client.post(f"/portal/{token}/boats/{boat_id}/delete")
    assert (await client.get("/api/catalog/boats")).json() == {"boats": []}
    page = await client.get(f"/portal/{token}")
    assert f"/portal/{token}/boats/{boat_id}/" not in page.text

    # Reachability toggle from the portal.
    await client.post(f"/portal/{token}/toggle_reachable")
    with Session(app.state.engine) as s:
        assert s.get(Operator, op_id).reachable is False


async def test_s7_demo_seed_and_clear_round_trip(app, client):
    for _ in range(2):
        r = await client.post(f"/admin/demo/seed?t={ADMIN}", follow_redirects=False)
        assert r.status_code == 303
    boats = (await client.get("/api/catalog/boats")).json()["boats"]
    assert {b["name"] for b in boats} == {"Demo Shikara", "Demo Deluxe"}
    r = await client.post(f"/admin/demo/clear?t={ADMIN}", follow_redirects=False)
    assert r.status_code == 303
    assert (await client.get("/api/catalog/boats")).json() == {"boats": []}


# ---------------------------------------------------------------------------
# S8 — validation, auth, guards
# ---------------------------------------------------------------------------

async def test_s8_voice_request_validation(client):
    await approved_listing(client)
    # No consent → rejected before anything is stored.
    body = await voice_request(client, 1, consent=False)
    assert body["status"] == "rejected"
    # Bad phone: passes the length bound but fails the phone regex → rejected.
    body = await voice_request(client, 1, phone="notaphone!")
    assert body["status"] == "rejected"
    # Too short even for the field bound → 400.
    r = await client.post("/api/voice/request", json={
        "customer_name": "Anu", "customer_phone": "abc", "consent_given": True})
    assert r.status_code == 400
    # Unlisted boat id.
    body = await voice_request(client, 999)
    assert body["status"] == "rejected"
    # Extra fields are forbidden → 400 invalid_request.
    r = await client.post("/api/voice/request", json={
        "customer_name": "Anu", "customer_phone": CUST_PHONE,
        "consent_given": True, "surprise": "x"})
    assert r.status_code == 400 and r.json()["detail"] == "invalid_request"
    # Oversized raw body → 413 from the size middleware.
    r = await client.post("/api/voice/request", content=b" " * 20_000,
                          headers={"Content-Type": "application/json"})
    assert r.status_code == 413
    # Bad callback reason → 400.
    r = await client.post("/api/voice/callback", json={
        "customer_name": "Anu", "customer_phone": CUST_PHONE,
        "consent_given": True, "reason": "whenever"})
    assert r.status_code == 400


async def test_s8_admin_and_portal_auth(client):
    assert (await client.get("/admin")).status_code == 401
    assert (await client.get("/admin?t=wrong")).status_code == 401
    assert (await client.post("/admin/operators",
                              data={"name": "x", "phone": "+9100"})).status_code == 401
    assert (await client.get("/portal/not-a-token")).status_code == 404


async def test_s8_voice_reply_paths(client):
    r = await client.post("/api/voice/reply", json={
        "utterance": "What boats do you have?", "language": "en-IN",
        "interaction_id": "e2e-1"})
    assert r.status_code == 200
    body = r.json()
    assert body["reply_text"] and body["trace_id"]


async def test_s8_voice_reply_upstream_error_and_rate_limit():
    a = make_app(rate_limit_per_minute=1)
    a.state.responder = failing_responder
    async with AsyncClient(transport=ASGITransport(app=a), base_url="http://test") as c:
        r = await c.post("/api/voice/reply", json={"utterance": "hi"})
        assert r.status_code == 502 and r.json()["detail"] == "upstream_unavailable"
        # Second call in the same window → 429 (rate limit checked first).
        r = await c.post("/api/voice/reply", json={"utterance": "hi"})
        assert r.status_code == 429 and r.json()["detail"] == "rate_limited"


async def test_s8_wa_transcribe_guards(client):
    r = await client.post("/api/ops/wa_transcribe",
                          json={"audio_b64": "QUJD" * 40, "mimetype": "audio/ogg"})
    assert r.status_code == 503  # no OPENAI_API_KEY in test settings
    a = make_app(openai_api_key="sk-test")
    async with AsyncClient(transport=ASGITransport(app=a), base_url="http://test") as c:
        r = await c.post("/api/ops/wa_transcribe",
                         json={"audio_b64": "!" * 200, "mimetype": "audio/ogg"})
        assert r.status_code == 400 and r.json()["detail"] == "invalid_audio"


# ---------------------------------------------------------------------------
# S9 — engine rules: IST window, expiry, PII retention, dedup
# ---------------------------------------------------------------------------

async def test_s9_outside_ist_window_requeues_without_attempt(app, client):
    await approved_listing(client)
    cb_body = await voice_callback(client, 1, "no_availability")
    cb = one_cb(app, public_id=cb_body["request_id"])
    with Session(app.state.engine) as s:
        s.get(CallbackRequest, cb.id).trigger_seq = 1
        s.get(CallbackRequest, cb.id).status = "queued"
        s.get(CallbackRequest, cb.id).next_attempt_at = utcnow()
        s.commit()

    # 14:30 UTC = 20:00 IST — outside the 09:00–18:00 window.
    now = datetime.now(timezone.utc).replace(hour=14, minute=30, second=0)
    made = process_due_callbacks(app.state.engine, app.state.callback_provider,
                                 now=now, force=True)
    assert made == 0
    cb = one_cb(app, public_id=cb_body["request_id"])
    assert cb.status == "queued" and cb.next_attempt_at > now
    with Session(app.state.engine) as s:
        assert s.exec(select(CallbackAttempt)).all() == []


async def test_s9_past_travel_date_expires_callback(app, client):
    await approved_listing(client)
    cb_body = await voice_callback(client, 1, "no_availability",
                                   preferred_date="2020-01-01")
    cb = one_cb(app, public_id=cb_body["request_id"])
    assert cb.expires_at < utcnow()
    await run_due(client)
    assert one_cb(app, public_id=cb_body["request_id"]).status == "expired"


async def test_s9_pii_anonymization_and_caller_context(app, client):
    token, op_id, boat_id = await approved_listing(client)
    req_id = (await voice_request(client, boat_id))["request_id"]
    with Session(app.state.engine) as s:
        req = s.exec(select(BookingRequest).where(
            BookingRequest.public_id == req_id)).one()
        req.created_at = utcnow() - timedelta(days=91)
        s.add(req)
        s.commit()
        assert anonymize_stale_requests(s) == 1
    ctx = await client.post("/api/voice/caller_context",
                            json={"customer_phone": CUST_PHONE})
    assert ctx.json()["known"] is False


async def test_s9_duplicate_callback_returns_same_id(app, client):
    await approved_listing(client)
    first = await voice_callback(client, 1, "no_availability")
    second = await voice_callback(client, 1, "no_availability")
    assert first["request_id"] == second["request_id"]
    with Session(app.state.engine) as s:
        assert len(s.exec(select(CallbackRequest)).all()) == 1


# ---------------------------------------------------------------------------
# S10 — public surface
# ---------------------------------------------------------------------------

async def test_s10_public_site_and_meta(client):
    assert (await client.get("/health")).json() == {"status": "ok"}
    home = await client.get("/")
    assert home.status_code == 200 and "കായൽ" in home.text
    for path, frag in {
        "/paayal": "#paayal", "/boats": "#boats", "/explore": "#explore",
        "/before-you-book": "#before-you-book",
        "/dtpc-houseboat-counter": "#dtpc", "/faq": "#faq",
    }.items():
        r = await client.get(path, follow_redirects=False)
        assert r.status_code == 301 and r.headers["location"].endswith(frag)
    assert (await client.get("/privacy")).status_code == 200
    robots = await client.get("/robots.txt")
    assert "Disallow: /admin" in robots.text and "Disallow: /api" in robots.text
    sitemap = await client.get("/sitemap.xml")
    assert sitemap.status_code == 200 and "<loc>" in sitemap.text


async def test_caller_context_new_vs_returning(app, client):
    r = await client.post("/api/voice/caller_context",
                          json={"customer_phone": CUST_PHONE})
    assert r.json()["known"] is False
    await approved_listing(client)
    await voice_request(client, 1)
    r = await client.post("/api/voice/caller_context",
                          json={"customer_phone": "+91 98000 00001"})
    body = r.json()
    assert body["known"] is True and body["customer_name"] == "Anu"
    assert body["requests"][0]["status"] == "pending"
