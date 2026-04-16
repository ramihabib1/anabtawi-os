"""SP-API Catalog Items API — BSR, ratings, review count."""

from __future__ import annotations

from typing import Any

from sync.spapi.client import SPAPIClient
from sync.utils.logging import get_logger

logger = get_logger(__name__)


async def get_catalog_item(
    asin: str,
    marketplace_id: str,
) -> dict[str, Any]:
    """
    Fetch catalog item details for an ASIN.
    Returns salesRanks, summaries (rating, reviewCount), etc.
    """
    async with SPAPIClient(marketplace_id=marketplace_id) as client:
        return await client.get(
            f"/catalog/2022-04-01/items/{asin}",
            params={
                "marketplaceIds": marketplace_id,
                "includedData": "salesRanks,summaries",
            },
        )
