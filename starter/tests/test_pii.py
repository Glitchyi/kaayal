from datetime import timedelta, timezone

import pytest
from sqlmodel import Session, select

from app.db import BookingRequest, make_engine, utcnow
from app.pii import anonymize_stale_requests


@pytest.fixture
def session():
    engine = make_engine("sqlite://")
    with Session(engine) as s:
        yield s


def seed_request(session, **kwargs) -> BookingRequest:
    r = BookingRequest(
        public_id=kwargs.pop("public_id", "REQ-0001-ab12"),
        customer_name=kwargs.pop("customer_name", "Anu"),
        customer_phone=kwargs.pop("customer_phone", "+919876543210"),
        consent_given=True,
        **kwargs,
    )
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


def test_fresh_request_untouched(session):
    r = seed_request(session)
    assert anonymize_stale_requests(session) == 0
    session.refresh(r)
    assert r.customer_name == "Anu"
    assert r.customer_phone == "+919876543210"
    assert r.anonymized_at is None


def test_stale_request_anonymized(session):
    r = seed_request(
        session,
        created_at=utcnow() - timedelta(days=91),
        notes="birthday trip",
        status="confirmed",
    )
    assert anonymize_stale_requests(session) == 1
    session.refresh(r)
    assert r.customer_name == "(anonymized)"
    assert r.customer_phone == ""
    assert r.notes is None
    assert r.anonymized_at is not None
    # non-PII fields preserved for ops/audit
    assert r.public_id == "REQ-0001-ab12"
    assert r.status == "confirmed"


def test_already_anonymized_untouched(session):
    anonymized_at = utcnow() - timedelta(days=1)
    r = seed_request(
        session,
        created_at=utcnow() - timedelta(days=100),
        customer_name="(anonymized)",
        customer_phone="",
        anonymized_at=anonymized_at,
    )
    assert anonymize_stale_requests(session) == 0
    session.refresh(r)
    # sqlite drops tz on round-trip; the stored timestamp must be unchanged
    assert r.anonymized_at.replace(tzinfo=timezone.utc) == anonymized_at


def test_count_reflects_only_stale(session):
    seed_request(session, public_id="REQ-old-1", created_at=utcnow() - timedelta(days=95))
    seed_request(session, public_id="REQ-old-2", created_at=utcnow() - timedelta(days=200))
    seed_request(session, public_id="REQ-fresh")
    assert anonymize_stale_requests(session) == 2
    remaining = session.exec(
        select(BookingRequest).where(BookingRequest.anonymized_at.is_(None))
    ).all()
    assert [r.public_id for r in remaining] == ["REQ-fresh"]
