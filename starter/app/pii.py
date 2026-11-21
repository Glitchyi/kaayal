"""PII retention — customer name/phone on booking requests is scrubbed after
the retention window. Counts only are ever logged; never the PII itself.
"""

from datetime import timedelta

from sqlmodel import Session, select

from app.db import BookingRequest, utcnow


def anonymize_stale_requests(session: Session, retention_days: int = 90) -> int:
    cutoff = utcnow() - timedelta(days=retention_days)
    stale = session.exec(
        select(BookingRequest).where(
            BookingRequest.anonymized_at.is_(None),
            BookingRequest.created_at < cutoff,
        )
    ).all()
    for req in stale:
        req.customer_name = "(anonymized)"
        req.customer_phone = ""
        req.notes = None
        req.anonymized_at = utcnow()
    session.commit()
    return len(stale)
