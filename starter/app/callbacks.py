"""Event-driven callback engine.

Paayal offers callbacks when an operator is unreachable or no boat matches.
Consent-gated rows sit durable in SQLite; a background tick (or admin's
"run due" button) attempts them through an outbound provider.

Rules (spec): calls only 09:00–18:00 IST (queued otherwise), max 2 attempts
per trigger event, >=60 min between attempts, expiry after 7 days or before
the travel date, opt-outs honored, duplicates prevented, survives restarts.
"""

import logging
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Protocol
from zoneinfo import ZoneInfo

from sqlmodel import Session, select

from app.db import Boat, BookingRequest, CallbackAttempt, CallbackRequest, Operator, utcnow

logger = logging.getLogger("kaayal")

IST = ZoneInfo("Asia/Kolkata")
CALL_START_HOUR, CALL_END_HOUR = 9, 18
MAX_ATTEMPTS = 2
MIN_RETRY_MINUTES = 61  # >60 to keep "minimum 60 minutes between attempts" honest
RETENTION_DAYS = 7

ACTIVE = ("queued", "calling")


# ---------------------------------------------------------------------------
# Outbound providers
# ---------------------------------------------------------------------------

class OutboundProvider(Protocol):
    name: str

    def place(self, cb: CallbackRequest, context: dict) -> tuple[str, list[dict]]:
        """Attempt one outbound call. Returns (outcome, transcript).
        outcome: interested | not_interested | no_answer"""
        ...


class SimulatedProvider:
    """Deterministic simulator — no real calls, no charges. The outcome is
    fixed per run via KAAYAL_SIM_CALLBACK_OUTCOME so demos are repeatable;
    the transcript records what Paayal *would* say."""

    name = "simulator"

    def __init__(self, outcome: str = "interested") -> None:
        self.outcome = outcome if outcome in ("interested", "not_interested", "no_answer") else "interested"

    def place(self, cb: CallbackRequest, context: dict) -> tuple[str, list[dict]]:
        what = context.get("what") or "your earlier request"
        if cb.reason == "operator_unreachable":
            why = f"the operator for {what} is reachable again"
        else:
            why = f"a boat matching {what} is now listed as available"
        paayal = [
            {"who": "paayal", "text": "Namaskaram, this is Paayal, Kaayal's AI assistant. Is this a good time?"},
            {"who": "paayal", "text": f"You had asked us about {what}. I'm calling because {why}."},
            {"who": "paayal", "text": "Would you like me to send the operator a booking inquiry for you?"},
        ]
        if self.outcome == "no_answer":
            return "no_answer", paayal[:1]
        customer_line = (
            "Yes, please go ahead." if self.outcome == "interested" else "No, I'm not interested anymore."
        )
        closer = (
            "Done — I've sent the inquiry. The operator will call you to confirm; "
            "Kaayal itself never confirms bookings."
            if self.outcome == "interested"
            else "Understood — I've noted you don't want further calls. Have a good day."
        )
        return self.outcome, paayal + [{"who": "customer", "text": customer_line}, {"who": "paayal", "text": closer}]


class SarvamOutboundProvider:
    """Prepared adapter for real Sarvam outbound calls — DISABLED until the
    owner approves real calls/charges and supplies credentials + endpoint
    details (see docs/sarvam-dashboard-setup.md). Not wired by default."""

    name = "sarvam"

    def place(self, cb: CallbackRequest, context: dict) -> tuple[str, list[dict]]:
        raise RuntimeError("sarvam_outbound_not_configured")


def make_provider(settings) -> OutboundProvider:
    if getattr(settings, "outbound_provider", "simulator") == "sarvam":
        return SarvamOutboundProvider()
    return SimulatedProvider(getattr(settings, "sim_callback_outcome", "interested"))


# ---------------------------------------------------------------------------
# Calling window (IST)
# ---------------------------------------------------------------------------

def _to_ist(dt: datetime) -> datetime:
    return dt.astimezone(IST)


def in_call_window(now: datetime, ignore_window: bool = False) -> bool:
    if ignore_window:
        return True
    h = _to_ist(now).hour
    return CALL_START_HOUR <= h < CALL_END_HOUR


def next_window_start(now: datetime) -> datetime:
    """Next 09:00 IST at/after `now` (today if before 9am, else tomorrow)."""
    ist = _to_ist(now)
    candidate = ist.replace(hour=CALL_START_HOUR, minute=0, second=0, microsecond=0)
    if ist.hour >= CALL_END_HOUR or candidate <= ist:
        candidate += timedelta(days=1)
    return candidate.astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Creation / opt-out
# ---------------------------------------------------------------------------

def _public_id(session: Session) -> str:
    count = len(session.exec(select(CallbackRequest)).all())
    return f"CB-{count + 1:04d}-{secrets.token_hex(2)}"


def _expiry(preferred_date: str | None, now: datetime) -> datetime:
    cutoff = now + timedelta(days=RETENTION_DAYS)
    if preferred_date:
        try:
            travel = date.fromisoformat(preferred_date.strip()[:10])
            travel_start = datetime(travel.year, travel.month, travel.day, tzinfo=timezone.utc)
            cutoff = min(cutoff, travel_start)
        except ValueError:
            pass
    return cutoff


def create_callback(
    session: Session,
    *,
    customer_name: str,
    customer_phone: str,
    reason: str,
    boat_id: int | None = None,
    operator_id: int | None = None,
    keywords: str | None = None,
    preferred_date: str | None = None,
) -> CallbackRequest | None:
    """Consent-gated, deduplicated. Returns None when consent is absent."""
    phone = customer_phone.strip()
    want_digits = re.sub(r"\D", "", phone)
    candidates = session.exec(
        select(CallbackRequest).where(
            CallbackRequest.reason == reason,
            CallbackRequest.status.in_(ACTIVE),
            CallbackRequest.boat_id == boat_id if boat_id else CallbackRequest.boat_id.is_(None),
        )
    ).all()
    dup = next(
        (c for c in candidates if re.sub(r"\D", "", c.customer_phone) == want_digits),
        None,
    )
    if dup:
        return dup
    cb = CallbackRequest(
        public_id=_public_id(session),
        customer_name=customer_name.strip(),
        customer_phone=phone,
        consent_given=True,
        reason=reason,
        boat_id=boat_id,
        operator_id=operator_id,
        keywords=(keywords or "").strip() or None,
        preferred_date=preferred_date,
    )
    cb.expires_at = _expiry(preferred_date, utcnow())
    # Parked at expiry until an event requeues it — never called without a trigger.
    cb.next_attempt_at = cb.expires_at
    session.add(cb)
    session.commit()
    session.refresh(cb)
    return cb


def opt_out_phone(session: Session, phone: str) -> int:
    """Consent withdrawal: mark every active callback for this number opted out."""
    digits = re.sub(r"\D", "", phone)
    n = 0
    for cb in session.exec(select(CallbackRequest).where(CallbackRequest.status.in_(ACTIVE))).all():
        if re.sub(r"\D", "", cb.customer_phone) == digits:
            cb.status = "opted_out"
            cb.updated_at = utcnow()
            n += 1
    session.commit()
    return n


# ---------------------------------------------------------------------------
# Event triggers (called from portal/admin when state changes)
# ---------------------------------------------------------------------------

def _requeue(cb: CallbackRequest) -> None:
    cb.trigger_seq += 1
    cb.attempts_this_trigger = 0
    cb.status = "queued"
    cb.next_attempt_at = utcnow()  # engine re-clamps to the call window
    cb.updated_at = utcnow()


def fire_boat_available(session: Session, boat: Boat) -> int:
    """Boat flipped available: requeue matching no_availability callbacks."""
    n = 0
    for cb in session.exec(
        select(CallbackRequest).where(
            CallbackRequest.reason == "no_availability",
            CallbackRequest.status.in_(ACTIVE),
        )
    ).all():
        match = cb.boat_id == boat.id or (
            cb.keywords and cb.keywords.casefold() in boat.name.casefold()
        )
        if match:
            _requeue(cb)
            n += 1
    return n


def fire_operator_reachable(session: Session, op: Operator) -> int:
    """Operator back online: requeue that operator's unreachable callbacks."""
    n = 0
    for cb in session.exec(
        select(CallbackRequest).where(
            CallbackRequest.reason == "operator_unreachable",
            CallbackRequest.status.in_(ACTIVE),
        )
    ).all():
        boat = session.get(Boat, cb.boat_id) if cb.boat_id else None
        if cb.operator_id == op.id or (boat and boat.operator_id == op.id):
            _requeue(cb)
            n += 1
    return n


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def _context_for(session: Session, cb: CallbackRequest) -> dict:
    what = None
    if cb.boat_id:
        boat = session.get(Boat, cb.boat_id)
        what = f"the boat '{boat.name}'" if boat else None
    if not what and cb.keywords:
        what = f"'{cb.keywords}'"
    if not what:
        what = "a houseboat in Alappuzha"
    return {"what": what}


def _convert_to_inquiry(session: Session, cb: CallbackRequest) -> None:
    """Simulated 'yes' → a real pending booking inquiry for the operator."""
    count = len(session.exec(select(BookingRequest)).all())
    session.add(
        BookingRequest(
            public_id=f"REQ-{count + 1:04d}-{secrets.token_hex(2)}",
            boat_id=cb.boat_id,
            customer_name=cb.customer_name,
            customer_phone=cb.customer_phone,
            consent_given=True,
            preferred_date=cb.preferred_date,
            notes=f"From callback {cb.public_id} ({cb.reason}).",
            source="callback",
        )
    )
    cb.status = "converted"


def process_due_callbacks(
    engine,
    provider: OutboundProvider,
    *,
    now: datetime | None = None,
    force: bool = False,
    ignore_window: bool = False,
) -> int:
    """Attempt every due queued callback. Returns number of attempts made."""
    now = now or utcnow()
    made = 0
    with Session(engine) as session:
        cbs = session.exec(
            select(CallbackRequest).where(CallbackRequest.status == "queued")
        ).all()
        for cb in cbs:
            if cb.expires_at and cb.expires_at <= now:
                cb.status = "expired"
                cb.updated_at = now
                continue
            if not force and cb.next_attempt_at and cb.next_attempt_at > now:
                continue
            if not in_call_window(now, ignore_window):
                # Queue for the next permitted window — don't burn an attempt.
                cb.next_attempt_at = next_window_start(now)
                continue
            if cb.attempts_this_trigger >= MAX_ATTEMPTS:
                cb.status = "no_answer"
                continue

            cb.status = "calling"
            session.commit()  # durable claim before dialing
            try:
                outcome, transcript = provider.place(cb, _context_for(session, cb))
            except Exception as exc:  # provider failure → retry like no_answer
                logger.warning("callback %s provider_error=%s", cb.public_id, exc)
                outcome, transcript = "no_answer", []
            session.add(
                CallbackAttempt(
                    callback_id=cb.id,
                    trigger_seq=cb.trigger_seq,
                    outcome=outcome,
                    provider=provider.name,
                    transcript=transcript,
                )
            )
            cb.attempts_this_trigger += 1
            made += 1
            if outcome == "interested":
                _convert_to_inquiry(session, cb)
            elif outcome == "not_interested":
                cb.status = "not_interested"
            else:
                if cb.attempts_this_trigger >= MAX_ATTEMPTS:
                    cb.status = "no_answer"
                else:
                    cb.status = "queued"
                    cb.next_attempt_at = now + timedelta(minutes=MIN_RETRY_MINUTES)
            cb.updated_at = utcnow()
        session.commit()
    return made
