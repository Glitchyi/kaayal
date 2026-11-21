"""WhatsApp demo onboarding endpoint (internal, tool-token auth).

Called only by the open-wa demo bot (wa-bot/) — creates an operator (or
re-issues their link on repeat messages) and returns the one-time portal
URL to send back over WhatsApp. Demo path; production = Business API.
"""

import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlmodel import Session, select

from app.db import Boat, Operator
from app.portal import hash_token, new_token

router = APIRouter(prefix="/api/ops", tags=["wa-demo"])

_PHONE_RE = re.compile(r"^[+0-9][0-9 ()-]{5,24}$")


class WaOnboardIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=6, max_length=25)
    name: str = Field(min_length=1, max_length=120)
    boat_name: str | None = Field(default=None, max_length=120)
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
