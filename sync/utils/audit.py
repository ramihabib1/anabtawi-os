"""
Audit log helper — every system action is written to the audit_log table.
Use log_action() from any module; it never raises (errors are swallowed and logged).
"""

from __future__ import annotations

import traceback
from typing import Any

from sync.utils.logging import get_logger

logger = get_logger(__name__)

# Valid agent_type enum values in the DB — sync jobs map to "system"
_VALID_AGENTS = {"inventory_agent", "ppc_agent", "competitor_agent", "consolidation", "system"}


async def log_action(
    agent: str,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    details: dict[str, Any] | None = None,
    status: str = "success",
) -> None:
    """
    Write one row to the audit_log table.

    Args:
        agent:       Which agent/job performed the action. Non-enum values
                     (sync job names) are mapped to "system".
        action:      What happened (e.g. "sync_complete").
        entity_type: Table or domain affected (e.g. "inventory_snapshots").
        entity_id:   UUID of the affected row (optional).
        details:     Arbitrary JSON payload with context.
        status:      "success" | "error" | "skipped".
    """
    from sync.supabase_client import get_supabase

    db_agent = agent if agent in _VALID_AGENTS else "system"
    is_success = status != "error"
    error_message: str | None = None
    if not is_success and isinstance(details, dict):
        error_message = details.get("error") or details.get("exc")

    row: dict[str, Any] = {
        "agent": db_agent,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
        "success": is_success,
        "error_message": error_message,
    }

    try:
        db = await get_supabase()
        await db.table("audit_log").insert(row).execute()
    except Exception:
        logger.warning("audit_log_write_failed", row=row, exc=traceback.format_exc())
