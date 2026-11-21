"""Voice tool endpoint for Paayal: create a booking request (tool-token auth).

Paayal collects name + callback number WITH explicit spoken consent (spec FR-09).
Requests are never auto-confirmed — they land pending for the operator.
"""

import re
import secrets

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, func, select

from app.db import Boat, BookingRequest

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
    with Session(engine) as session:
        if payload.boat_id is not None:
            boat = session.get(Boat, payload.boat_id)
            if not boat or not boat.active or boat.verified_at is None:
                return CreateRequestOut(
                    request_id="",
                    status="rejected",
                    message="That boat isn't available; I can take a general request instead.",
                )
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

    return CreateRequestOut(
        request_id=public_id,
        status="pending",
        message="Your request has been sent to the operator. They will confirm and call you back.",
    )
