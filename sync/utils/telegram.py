"""
Telegram notification helpers for the sync layer.

send_to_role() sends a message to a specific team member by role name.
Used by sync jobs to alert on significant events (competitor price drops,
expired approvals, etc.).
"""

from __future__ import annotations

import httpx

from sync.config import settings

_ROLE_TO_CHAT_ID: dict[str, str] = {
    "rami": settings.RAMI_TELEGRAM_ID,
    "father": settings.FATHER_TELEGRAM_ID,
    "maree": settings.MAREE_TELEGRAM_ID,
}


async def send_to_role(role: str, text: str) -> None:
    """
    Send a Markdown message to a team member by role.

    Args:
        role: "rami" | "father" | "maree"
        text: Telegram Markdown message body.
    """
    chat_id = _ROLE_TO_CHAT_ID.get(role)
    if not chat_id or not settings.TELEGRAM_BOT_TOKEN:
        return

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
        except Exception:
            pass  # Telegram alerts must never crash the caller
