from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import JSON, text
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Operator(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    phone: str
    # SHA-256 of the portal login token; raw token is only ever shown once.
    token_hash: str
    active: bool = True
    # Can customers/operators currently reach this operator? Portal-toggleable;
    # flipping it back on fires queued "operator unreachable" callbacks.
    reachable: bool = True
    # NULL = self-signup awaiting admin approval (no portal access yet).
    approved_at: datetime | None = None
    # admin | wa-demo | web-signup | demo-seed
    source: str = "admin"
    created_at: datetime = Field(default_factory=utcnow)


class Boat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    operator_id: int = Field(foreign_key="operator.id", index=True)
    name: str
    # Free text: houseboat | shikara | canoe | speedboat | … (operator-supplied)
    boat_type: str | None = None
    capacity: int | None = None
    embarkation_point: str | None = None
    photo_urls: list[str] = Field(default_factory=list, sa_type=JSON)
    amenities: list[str] = Field(default_factory=list, sa_type=JSON)
    # Free display text, e.g. "₹9,500/night" — pricing is operator-supplied,
    # never computed or guaranteed by Kaayal.
    price_display: str | None = None
    # Operator-set availability flag; False → True flips fire callbacks.
    available: bool = True
    # owner-entered | operator-submitted | govt-registry | wa-demo | demo-seed
    source: str = "operator-submitted"
    verified_at: datetime | None = None
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class BookingRequest(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    public_id: str = Field(index=True)  # e.g. REQ-0007 — safe to expose
    # NULL = caller didn't pick a boat → owner triage queue
    boat_id: int | None = Field(default=None, foreign_key="boat.id", index=True)
    customer_name: str
    customer_phone: str
    consent_given: bool
    preferred_date: str | None = None
    group_size: int | None = None
    notes: str | None = None
    # pending | confirmed | declined | blocked | cancelled
    status: str = "pending"
    # Free-text reply from the operator alongside a status change.
    operator_note: str | None = None
    # voice | web | callback
    source: str = "voice"
    anonymized_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class CallbackRequest(SQLModel, table=True):
    """Consent-gated request for Paayal to call the customer back when an
    operator becomes reachable or a boat becomes available. Durable across
    restarts; the engine processes due rows on a tick."""

    id: int | None = Field(default=None, primary_key=True)
    public_id: str = Field(index=True)  # e.g. CB-0003-9f2a
    customer_name: str
    customer_phone: str
    consent_given: bool
    # operator_unreachable | no_availability
    reason: str
    boat_id: int | None = Field(default=None, foreign_key="boat.id", index=True)
    operator_id: int | None = Field(default=None, foreign_key="operator.id")
    keywords: str | None = None
    preferred_date: str | None = None
    # queued | calling | interested | not_interested | no_answer(exhausted)
    # opted_out | expired | converted (booking inquiry created)
    status: str = "queued"
    trigger_seq: int = 0          # increments per qualifying event
    attempts_this_trigger: int = 0
    next_attempt_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class CallbackAttempt(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    callback_id: int = Field(foreign_key="callbackrequest.id", index=True)
    trigger_seq: int = 0
    attempted_at: datetime = Field(default_factory=utcnow)
    # interested | not_interested | no_answer (provider-driven)
    outcome: str
    # provider name: "simulator" | "sarvam"
    provider: str = "simulator"
    transcript: list[dict] = Field(default_factory=list, sa_type=JSON)


# ---------------------------------------------------------------------------
# SQLite is the prototype store: create_all handles new tables, but won't add
# columns to existing ones. This naive adder keeps the live DB migratable
# without pulling in Alembic.
_COLUMN_DDLS: dict[str, dict[str, str]] = {
    "operator": {
        "reachable": "ALTER TABLE operator ADD COLUMN reachable BOOLEAN DEFAULT 1",
        "approved_at": "ALTER TABLE operator ADD COLUMN approved_at DATETIME",
        "source": "ALTER TABLE operator ADD COLUMN source VARCHAR DEFAULT 'admin'",
    },
    "boat": {
        "amenities": "ALTER TABLE boat ADD COLUMN amenities JSON DEFAULT '[]'",
        "price_display": "ALTER TABLE boat ADD COLUMN price_display VARCHAR",
        "available": "ALTER TABLE boat ADD COLUMN available BOOLEAN DEFAULT 1",
    },
    "bookingrequest": {
        "operator_note": "ALTER TABLE bookingrequest ADD COLUMN operator_note VARCHAR",
        "source": "ALTER TABLE bookingrequest ADD COLUMN source VARCHAR DEFAULT 'voice'",
    },
}


def _ensure_columns(engine) -> None:
    with engine.connect() as conn:
        for table, cols in _COLUMN_DDLS.items():
            existing = {r[1] for r in conn.exec_driver_sql(f"PRAGMA table_info({table})")}
            for col, ddl in cols.items():
                if col not in existing:
                    conn.exec_driver_sql(ddl)
        conn.commit()


def make_engine(url: str = "sqlite:///kaayal.db"):
    if url in ("sqlite://", "sqlite:///:memory:"):
        # In-memory: keep one shared connection or each session sees an empty db.
        engine = create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
    SQLModel.metadata.create_all(engine)
    if url.startswith("sqlite"):
        _ensure_columns(engine)
    return engine


def get_session(engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
