"""Best-effort push to the wa-bot send listener (demo path).

Approving an operator in /admin mints their portal link; when WA_BOT_URL is
set we ask the bot to WhatsApp it to them so they don't have to DM again.
Booking requests also ping the boat's operator — without customer PII, which
stays in the portal until they confirm.
"""

import logging

import httpx

logger = logging.getLogger(__name__)


def _send(settings, phone: str, text: str) -> bool:
    base = (settings.wa_bot_url or "").rstrip("/")
    if not base:
        return False
    try:
        httpx.post(
            f"{base}/send",
            json={"phone": phone, "text": text},
            headers={"X-Kaayal-Tool-Token": settings.sarvam_tool_shared_secret or ""},
            timeout=5,
        ).raise_for_status()
        return True
    except Exception:
        # Never log the phone or link — PII + raw token.
        logger.warning("wa_notify: send failed")
        return False


def notify_portal_link(settings, phone: str, name: str, portal_url: str) -> bool:
    return _send(
        settings,
        phone,
        f"You're verified on Kaayal, {name}!\n\n"
        f"Your private portal link (it IS your login — keep it secret):\n{portal_url}\n\n"
        "Open it to add boat details and photos. If the link ever leaks, ask us to re-issue it.",
    )


def notify_booking_request(
    settings, phone: str, boat_name: str, request_id: str,
    group_size: int | None, preferred_date: str | None,
) -> bool:
    bits = [request_id]
    if group_size:
        bits.append(f"{group_size} people")
    if preferred_date:
        bits.append(preferred_date)
    return _send(
        settings,
        phone,
        f"New booking request for {boat_name}!\n"
        + " · ".join(bits)
        + "\nThe caller's name and number are in your portal.",
    )
