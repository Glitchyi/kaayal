from collections.abc import Generator
from datetime import datetime, timezone

from sqlalchemy import JSON
from sqlalchemy.pool import StaticPool
from sqlmodel import Field, Session, SQLModel, create_engine


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Operator(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    phone: str
    # SHA-256 of the portal login token; raw token is only ever shown once to the owner.
    token_hash: str
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)


class Boat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    operator_id: int = Field(foreign_key="operator.id", index=True)
    name: str
    capacity: int | None = None
    embarkation_point: str | None = None
    photo_urls: list[str] = Field(default_factory=list, sa_type=JSON)
    # owner-entered | operator-submitted | govt-registry
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
    # pending | confirmed | blocked | cancelled
    status: str = "pending"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    anonymized_at: datetime | None = Field(default=None)


def make_engine(url: str = "sqlite:///kaayal.db"):
    if url in ("sqlite://", "sqlite:///:memory:"):
        # In-memory: keep one shared connection or each session sees an empty db.
        engine = create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        engine = create_engine(url, connect_args=connect_args)
    SQLModel.metadata.create_all(engine)
    return engine


def get_session(engine) -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
