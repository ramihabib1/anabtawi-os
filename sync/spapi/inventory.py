"""SP-API FBA inventory queries — targeted query for active SKUs only."""

from __future__ import annotations

from typing import Any

from sync.spapi.client import SPAPIClient
from sync.utils.logging import get_logger

logger = get_logger(__name__)

_PATH = "/fba/inventory/v1/summaries"
_SKU_BATCH_SIZE = 50


async def get_fba_inventory_summaries(
    marketplace_id: str,
    known_skus: list[str],
) -> list[dict[str, Any]]:
    """
    Fetch FBA inventory for a specific list of active SKUs.
    Only queries for known_skus — no full marketplace scan (returns ghost SKUs).
    """
    if not known_skus:
        logger.warning("fba_inventory_no_skus_provided")
        return []

    results: dict[str, dict[str, Any]] = {}

    async with SPAPIClient(marketplace_id=marketplace_id) as client:
        targeted = await _fetch_by_skus(client, marketplace_id, known_skus)
        for s in targeted:
            sku = s.get("sellerSku")
            if sku:
                results[sku] = s

    logger.info("fba_inventory_done", requested=len(known_skus), returned=len(results))
    return list(results.values())


async def _fetch_by_skus(
    client: SPAPIClient,
    marketplace_id: str,
    skus: list[str],
) -> list[dict[str, Any]]:
    """Fetch inventory for specific SKUs in batches of up to 50."""
    results: list[dict[str, Any]] = []

    for i in range(0, len(skus), _SKU_BATCH_SIZE):
        batch = skus[i: i + _SKU_BATCH_SIZE]
        response = await client.get(_PATH, params={
            "details": "true",
            "granularityType": "Marketplace",
            "granularityId": marketplace_id,
            "marketplaceIds": marketplace_id,
            "sellerSkus": ",".join(batch),
        })
        payload = response.get("payload", {})
        results.extend(payload.get("inventorySummaries", []))

    return results
