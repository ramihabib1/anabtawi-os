"""
Hourly job: expire stale approval requests older than 24 hours.

Calls the Supabase RPC function expire_stale_approvals() which marks
pending requests with expires_at < now() as 'expired'.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from sync.supabase_client import get_supabase
from sync.utils.audit import log_action
from sync.utils.logging import get_logger
from sync.utils.telegram import send_to_role

logger = get_logger(__name__)

_JOB_NAME = "expire_approvals"


async def run() -> dict[str, Any]:
    start = time.monotonic()
    expired = 0

    try:
        db = await get_supabase()

        result = await db.rpc("expire_stale_approvals").execute()
        expired_rows = result.data or []
        expired = len(expired_rows) if isinstance(expired_rows, list) else 0

        if expired:
            logger.info("approvals_expired", count=expired)
            await send_to_role(
                "rami",
                f"⏰ *{expired} approval request(s) expired* (24h limit).\n"
                "Check pending approvals.",
            )
            await log_action(
                agent=_JOB_NAME,
                action="expire_approvals",
                entity_type="approval_requests",
                details={"expired": expired},
            )

    except Exception as exc:
        logger.error("expire_approvals_error", exc=str(exc))

    return {
        "expired": expired,
        "duration_seconds": round(time.monotonic() - start, 2),
    }


if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
