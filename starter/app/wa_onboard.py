"""WhatsApp demo onboarding endpoint (internal, tool-token auth).

Called only by the open-wa demo bot (wa-bot/) — creates an operator (or
re-issues their link on repeat messages) and returns the one-time portal
URL to send back over WhatsApp. Demo path; production = Business API.
"""

import base64
import io
import re

import openai
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, func, select

from app.callbacks import fire_booking_confirmed, fire_operator_reachable, process_due_callbacks
from app.db import Boat, BookingRequest, CallbackRequest, Operator
from app.portal import hash_token, new_token

router = APIRouter(prefix="/api/ops", tags=["wa-demo"])

_PHONE_RE = re.compile(r"^[+0-9][0-9 ()-]{5,24}$")


class WaOnboardIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=6, max_length=25)
    name: str = Field(min_length=1, max_length=120)
    boat_name: str | None = Field(default=None, max_length=120)
    boat_type: str | None = Field(default=None, max_length=60)
    embarkation: str | None = Field(default=None, max_length=120)


class WaOnboardOut(BaseModel):
    operator_id: int
    # NULL while the operator awaits admin approval — bot says "pending" instead.
    portal_url: str | None
    status: str  # pending_approval | approved
    boat_id: int | None


class WaReissueIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=6, max_length=25)


class WaReissueOut(BaseModel):
    operator_id: int
    name: str
    portal_url: str | None
    status: str  # pending_approval | approved


class WaConfirmIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=6, max_length=25)
    request_id: str = Field(min_length=3, max_length=40)
    action: str = Field(default="confirm", pattern="^(confirm|decline)$")


class WaConfirmOut(BaseModel):
    request_id: str
    status: str
    customer_name: str | None
    customer_phone: str | None
    boat_name: str | None
    preferred_date: str | None
    group_size: int | None
    customer_notified: bool
    notify_channel: str | None = None  # "call" | "whatsapp" | "queued"


class WaRequestsIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=6, max_length=25)


class WaRequestItem(BaseModel):
    request_id: str
    boat_name: str | None
    customer_name: str
    preferred_date: str | None
    group_size: int | None


class WaRequestsOut(BaseModel):
    requests: list[WaRequestItem]


class WaReachableIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=6, max_length=25)
    reachable: bool


class WaReachableOut(BaseModel):
    reachable: bool


def _digits(phone: str) -> str:
    return re.sub(r"\D", "", phone)


@router.post("/wa_onboard", response_model=WaOnboardOut)
def wa_onboard(payload: WaOnboardIn, request: Request):
    if not _PHONE_RE.match(payload.phone):
        raise HTTPException(status_code=400, detail="invalid_phone")

    engine = request.app.state.engine
    base = request.app.state.settings.kaayal_public_base_url.rstrip("/")
    want_digits = _digits(payload.phone)

    with Session(engine) as session:
        # Match by normalized digits so "+91 94003 54625" == "919400354625".
        op = next(
            (o for o in session.exec(select(Operator)).all() if _digits(o.phone) == want_digits),
            None,
        )
        token = new_token()
        if op is None:
            # Self-signup: no portal access until the owner approves in /admin.
            op = Operator(
                name=payload.name.strip(),
                phone=f"+{want_digits}",
                token_hash=hash_token(token),
                approved_at=None,
                source="wa-demo",
            )
        else:
            # Repeat DM → re-issue: the old portal link immediately dies.
            op.token_hash = hash_token(token)
        session.add(op)
        session.commit()

        boat_id = None
        if payload.boat_name:
            name = payload.boat_name.strip()
            existing = session.exec(
                select(Boat).where(Boat.operator_id == op.id, Boat.name == name)
            ).first()
            if existing is None:
                boat = Boat(
                    operator_id=op.id,
                    name=name,
                    boat_type=payload.boat_type.strip() if payload.boat_type else None,
                    embarkation_point=payload.embarkation.strip() if payload.embarkation else None,
                    source="wa-demo",
                )
                session.add(boat)
                session.commit()
                boat_id = boat.id
            else:
                boat_id = existing.id
        operator_id = op.id
        approved = op.approved_at is not None

    return WaOnboardOut(
        operator_id=operator_id,
        portal_url=f"{base}/portal/{token}" if approved else None,
        status="approved" if approved else "pending_approval",
        boat_id=boat_id,
    )


@router.post("/wa_reissue", response_model=WaReissueOut)
def wa_reissue(payload: WaReissueIn, request: Request):
    """Repeat-DM fast path: recognized number gets a fresh link (or pending
    status) without re-running the onboarding questionnaire."""
    if not _PHONE_RE.match(payload.phone):
        raise HTTPException(status_code=400, detail="invalid_phone")

    engine = request.app.state.engine
    base = request.app.state.settings.kaayal_public_base_url.rstrip("/")
    want_digits = _digits(payload.phone)

    with Session(engine) as session:
        op = next(
            (o for o in session.exec(select(Operator)).all() if _digits(o.phone) == want_digits),
            None,
        )
        if op is None:
            raise HTTPException(status_code=404, detail="unknown_operator")
        token = new_token()
        # Same contract as a repeat onboard: the old link dies immediately.
        op.token_hash = hash_token(token)
        session.add(op)
        session.commit()
        operator_id, name, approved = op.id, op.name, op.approved_at is not None

    return WaReissueOut(
        operator_id=operator_id,
        name=name,
        portal_url=f"{base}/portal/{token}" if approved else None,
        status="approved" if approved else "pending_approval",
    )


@router.post("/wa_confirm", response_model=WaConfirmOut)
def wa_confirm(payload: WaConfirmIn, request: Request):
    """Operator replies to a booking ping with the request ID → confirm it
    over WhatsApp. Same rules as the portal: must be their boat's request,
    and confirming is what unmasks the customer's number."""
    want_digits = _digits(payload.phone)
    engine = request.app.state.engine
    with Session(engine) as session:
        op = next(
            (o for o in session.exec(select(Operator)).all() if _digits(o.phone) == want_digits),
            None,
        )
        if op is None:
            raise HTTPException(status_code=404, detail="unknown_operator")
        req = session.exec(
            select(BookingRequest).where(
                func.upper(BookingRequest.public_id) == payload.request_id.strip().upper()
            )
        ).first()
        boat = session.get(Boat, req.boat_id) if req and req.boat_id else None
        if req is None or boat is None or boat.operator_id != op.id:
            raise HTTPException(status_code=404, detail="unknown_request")
        notify_cb = None
        if req.status == "pending":
            req.status = "confirmed" if payload.action == "confirm" else "declined"
            session.add(req)
            session.commit()
            if req.status == "confirmed":
                notify_cb = fire_booking_confirmed(session, req, boat, op)
        notify_channel = None
        if notify_cb is not None:
            # Attempt the notify call right now instead of waiting for the tick.
            process_due_callbacks(
                engine,
                request.app.state.callback_provider,
                settings=request.app.state.settings,
                ignore_window=request.app.state.settings.demo_ignore_call_window,
            )
            with Session(engine) as s2:
                cb = s2.exec(
                    select(CallbackRequest).where(CallbackRequest.id == notify_cb.id)
                ).first()
                if cb.status == "notified":
                    notify_channel = "call"
                elif cb.status == "no_answer":
                    notify_channel = "whatsapp"  # engine already pushed the fallback
                else:
                    notify_channel = "queued"  # outside the IST call window
        out = WaConfirmOut(
            request_id=req.public_id,
            status=req.status,
            customer_name=req.customer_name,
            customer_phone=req.customer_phone if req.status == "confirmed" else None,
            boat_name=boat.name,
            preferred_date=req.preferred_date,
            group_size=req.group_size,
            customer_notified=notify_channel in ("call", "whatsapp"),
            notify_channel=notify_channel,
        )
    return out


def _op_by_phone(session: Session, phone: str) -> Operator | None:
    want = _digits(phone)
    return next(
        (o for o in session.exec(select(Operator)).all() if _digits(o.phone) == want),
        None,
    )


@router.post("/wa_requests", response_model=WaRequestsOut)
def wa_requests(payload: WaRequestsIn, request: Request):
    """Operator's pending booking requests — names shown, numbers stay
    masked until a request is confirmed (same rule as the portal)."""
    engine = request.app.state.engine
    with Session(engine) as session:
        op = _op_by_phone(session, payload.phone)
        if op is None:
            raise HTTPException(status_code=404, detail="unknown_operator")
        rows = session.exec(
            select(BookingRequest, Boat)
            .join(Boat, BookingRequest.boat_id == Boat.id)
            .where(Boat.operator_id == op.id, BookingRequest.status == "pending")
            .order_by(BookingRequest.created_at)
        ).all()
    return WaRequestsOut(
        requests=[
            WaRequestItem(
                request_id=r.public_id,
                boat_name=b.name,
                customer_name=r.customer_name,
                preferred_date=r.preferred_date,
                group_size=r.group_size,
            )
            for r, b in rows
        ]
    )


@router.post("/wa_reachable", response_model=WaReachableOut)
def wa_reachable(payload: WaReachableIn, request: Request):
    """WhatsApp PAUSE/RESUME — same semantics as the portal toggle; coming
    back online fires queued 'operator unreachable' callbacks."""
    engine = request.app.state.engine
    with Session(engine) as session:
        op = _op_by_phone(session, payload.phone)
        if op is None:
            raise HTTPException(status_code=404, detail="unknown_operator")
        if payload.reachable and not op.reachable:
            fire_operator_reachable(session, op)
        op.reachable = payload.reachable
        session.add(op)
        session.commit()
    return WaReachableOut(reachable=payload.reachable)


# ---------------------------------------------------------------------------
# Voice-note transcription — bot decrypts the audio and posts it here; the
# OpenAI key stays server-side. Exempt from the global body-size cap (audio
# is bigger than JSON) but bounded by audio_b64's max_length (~6MB audio).
# ---------------------------------------------------------------------------

class WaTranscribeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audio_b64: str = Field(min_length=100, max_length=8_000_000)
    mimetype: str = Field(default="audio/ogg", max_length=60)


@router.post("/wa_transcribe")
async def wa_transcribe(payload: WaTranscribeIn, request: Request):
    settings = request.app.state.settings
    if not settings.openai_api_key:
        raise HTTPException(status_code=503, detail="transcription_not_configured")
    try:
        audio = base64.b64decode(payload.audio_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_audio")

    ext = payload.mimetype.split("/")[-1].split(";")[0] or "ogg"
    client = openai.AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=30,
        max_retries=0,
    )
    try:
        result = await client.audio.transcriptions.create(
            model="whisper-1",
            file=(f"note.{ext}", io.BytesIO(audio), payload.mimetype),
        )
    except openai.APIError:
        raise HTTPException(status_code=502, detail="transcription_failed")
    return {"text": result.text or ""}
