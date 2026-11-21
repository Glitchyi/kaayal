"""Voice tool endpoint for Paayal: create a booking request (tool-token auth).

Paayal collects name + callback number WITH explicit spoken consent (spec FR-09).
Requests are never auto-confirmed — they land pending for the operator.
"""

import re
import secrets

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlmodel import Session, func, select

from app.callbacks import create_callback, opt_out_phone
from app.catalog import listed_boat
from app.db import BookingRequest
from app.wa_notify import notify_booking_request

router = APIRouter(prefix="/api/voice", tags=["voice-requests"])

_PHONE_RE = re.compile(r"^[+0-9][0-9 ()-]{5,24}$")


class CreateRequestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_name: str = Field(min_length=1, max_length=120)
    customer_phone: str = Field(min_length=6, max_length=25)
    consent_given: bool
    boat_id: int | None = None
    preferred_date: str | None = Field(default=None, max_length=40)
    group_size: int | None = Field(default=None, ge=1, le=200)
    notes: str | None = Field(default=None, max_length=500)
    interaction_id: str | None = Field(default=None, max_length=120)

    # Sarvam variables render unset optionals as "" — treat as absent.
    @field_validator("*", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v):
        return None if v == "" else v


class CreateRequestOut(BaseModel):
    request_id: str
    status: str
    message: str


def _next_public_id(session: Session) -> str:
    count = session.exec(select(func.count()).select_from(BookingRequest)).one()
    return f"REQ-{count + 1:04d}-{secrets.token_hex(2)}"


@router.post("/request", response_model=CreateRequestOut)
def create_booking_request(payload: CreateRequestIn, request: Request):
    if not payload.consent_given:
        return CreateRequestOut(
            request_id="",
            status="rejected",
            message="Consent is required before collecting contact details.",
        )
    if not _PHONE_RE.match(payload.customer_phone):
        return CreateRequestOut(
            request_id="",
            status="rejected",
            message="The callback number doesn't look valid.",
        )

    engine = request.app.state.engine
    notify_phone = None
    notify_boat = None
    with Session(engine) as session:
        if payload.boat_id is not None:
            row = listed_boat(session, payload.boat_id)
            if not row:
                return CreateRequestOut(
                    request_id="",
                    status="rejected",
                    message="That boat isn't listed; I can take a general request instead.",
                )
            boat, op = row
            if not boat.available:
                return CreateRequestOut(
                    request_id="",
                    status="unavailable",
                    message="That boat isn't available right now. I can arrange a callback when it is — shall I take your number?",
                )
            if not op.reachable:
                return CreateRequestOut(
                    request_id="",
                    status="unreachable",
                    message="That operator can't be reached right now. I can call you back when they're reachable — shall I take your number?",
                )
            if op.phone:
                notify_phone = op.phone
                notify_boat = boat.name
        req = BookingRequest(
            public_id=_next_public_id(session),
            boat_id=payload.boat_id,
            customer_name=payload.customer_name.strip(),
            customer_phone=payload.customer_phone.strip(),
            consent_given=True,
            preferred_date=payload.preferred_date,
            group_size=payload.group_size,
            notes=payload.notes,
        )
        session.add(req)
        session.commit()
        public_id = req.public_id

    if notify_phone:
        notify_booking_request(
            request.app.state.settings, notify_phone, notify_boat,
            public_id, payload.group_size, payload.preferred_date,
        )

    return CreateRequestOut(
        request_id=public_id,
        status="pending",
        message="Your request has been sent to the operator. They will confirm and call you back.",
    )


# ---------------------------------------------------------------------------
# Callback requests — consent-gated; same endpoint also handles opt-outs
# (consent_given=false + phone withdraws all active callbacks for the number).
# ---------------------------------------------------------------------------

class CreateCallbackIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_name: str = Field(min_length=1, max_length=120)
    customer_phone: str = Field(min_length=6, max_length=25)
    consent_given: bool
    # operator_unreachable | no_availability
    reason: str = Field(pattern="^(operator_unreachable|no_availability)$")
    boat_id: int | None = None
    keywords: str | None = Field(default=None, max_length=200)
    preferred_date: str | None = Field(default=None, max_length=40)
    interaction_id: str | None = Field(default=None, max_length=120)

    @field_validator("*", mode="before")
    @classmethod
    def _empty_str_to_none(cls, v):
        return None if v == "" else v


@router.post("/callback", response_model=CreateRequestOut)
def create_callback_request(payload: CreateCallbackIn, request: Request):
    if not payload.consent_given:
        engine = request.app.state.engine
        with Session(engine) as session:
            n = opt_out_phone(session, payload.customer_phone)
        return CreateRequestOut(
            request_id="",
            status="opted_out" if n else "rejected",
            message=(
                "Understood — I've removed any scheduled callbacks for that number."
                if n
                else "No callback was scheduled. I won't call unless you ask me to."
            ),
        )
    if not _PHONE_RE.match(payload.customer_phone):
        return CreateRequestOut(
            request_id="", status="rejected", message="That number doesn't look valid."
        )

    engine = request.app.state.engine
    with Session(engine) as session:
        operator_id = None
        if payload.boat_id is not None:
            row = listed_boat(session, payload.boat_id)
            if not row:
                return CreateRequestOut(
                    request_id="", status="rejected",
                    message="That boat isn't listed; I can take a general callback instead.",
                )
            boat, op = row
            operator_id = op.id
        cb = create_callback(
            session,
            customer_name=payload.customer_name,
            customer_phone=payload.customer_phone,
            reason=payload.reason,
            boat_id=payload.boat_id,
            operator_id=operator_id,
            keywords=payload.keywords,
            preferred_date=payload.preferred_date,
        )
        public_id = cb.public_id if cb else ""

    return CreateRequestOut(
        request_id=public_id,
        status="queued",
        message="Noted — I'll call you back when that changes. Kaayal will only call for this reason.",
    )
