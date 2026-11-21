"""Scrub PII on booking requests older than the retention window.
Usage: .venv/bin/python scripts/anonymize_pii.py   (prints count anonymized)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlmodel import Session

from app.config import get_settings
from app.db import make_engine
from app.pii import anonymize_stale_requests


def main() -> None:
    engine = make_engine(get_settings().database_url)
    with Session(engine) as session:
        print(anonymize_stale_requests(session))


if __name__ == "__main__":
    main()
