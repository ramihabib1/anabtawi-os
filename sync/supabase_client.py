"""
Async Supabase client singleton for the sync layer.

The sync jobs are async (SP-API calls + DB writes), so they need the
async Supabase client (acreate_client). This is separate from the sync
client in core/supabase_client.py used by the agents.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache

from supabase import AClient as AsyncClient, acreate_client

from sync.config import settings

_init_lock = asyncio.Lock()
_client: AsyncClient | None = None
_marketplace_uuid_cache: dict[str, str] = {}


@lru_cache(maxsize=1)
def _get_url_and_key() -> tuple[str, str]:
    return settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY


async def get_supabase() -> AsyncClient:
    """
    Return the shared async Supabase client (service_role).
    Initialises on first call; subsequent calls return the cached instance.
    """
    global _client
    if _client is not None:
        return _client
    async with _init_lock:
        if _client is None:
            url, key = _get_url_and_key()
            _client = await acreate_client(url, key)
    return _client


async def get_marketplace_uuid(marketplace_code: str) -> str:
    """
    Resolve an Amazon marketplace_id string to its DB UUID.
    Result is cached after the first lookup.
    """
    if marketplace_code in _marketplace_uuid_cache:
        return _marketplace_uuid_cache[marketplace_code]

    db = await get_supabase()
    result = await (
        db.table("marketplaces")
        .select("id")
        .eq("marketplace_id", marketplace_code)
        .single()
        .execute()
    )
    uuid = result.data["id"]
    _marketplace_uuid_cache[marketplace_code] = uuid
    return uuid


async def close_supabase() -> None:
    """Close the Supabase client — call on graceful shutdown."""
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except AttributeError:
            pass
        _client = None
