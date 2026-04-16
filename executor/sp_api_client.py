"""
SP-API write client.
Handles price changes and listing updates via the Listings Items API.
PPC (Advertising API) is stubbed — requires separate auth setup.
FBA replenishment is manual — returns acknowledgement only.
"""
import logging
from urllib.parse import quote
from sp_api.api import Sellers, ListingsItems
from sp_api.base import Marketplaces
from core.config import (
    SP_API_CLIENT_ID,
    SP_API_CLIENT_SECRET,
    SP_API_REFRESH_TOKEN,
    SP_API_AWS_ACCESS_KEY,
    SP_API_AWS_SECRET_KEY,
    SP_API_ROLE_ARN,
    SP_API_MARKETPLACE_CA,
    SP_API_MARKETPLACE_US,
)

logger = logging.getLogger(__name__)

CREDENTIALS = {
    "lwa_app_id": SP_API_CLIENT_ID,
    "lwa_client_secret": SP_API_CLIENT_SECRET,
    "refresh_token": SP_API_REFRESH_TOKEN,
    "aws_access_key": SP_API_AWS_ACCESS_KEY,
    "aws_secret_key": SP_API_AWS_SECRET_KEY,
    "role_arn": SP_API_ROLE_ARN,
}

_MARKETPLACE_MAP = {
    SP_API_MARKETPLACE_CA: Marketplaces.CA,
    SP_API_MARKETPLACE_US: Marketplaces.US,
}


class SPAPIClient:

    def _marketplace(self, marketplace_id: str) -> Marketplaces:
        return _MARKETPLACE_MAP.get(marketplace_id, Marketplaces.CA)

    def validate_connection(self) -> dict:
        """Test SP-API auth by calling marketplaceParticipations."""
        sellers = Sellers(credentials=CREDENTIALS, marketplace=Marketplaces.CA)
        res = sellers.get_marketplace_participations()
        participations = res.payload if isinstance(res.payload, list) else []
        marketplace_ids = [p.get("marketplace", {}).get("id") for p in participations]
        logger.info(f"SP-API connected. Marketplaces: {marketplace_ids}")
        return {"status": "ok", "marketplace_ids": marketplace_ids}

    def update_price(
        self,
        sku: str,
        new_price: float,
        marketplace: str,
        seller_id: str,
        product_type: str = "FOOD",
    ) -> dict:
        """Update listing price via Listings Items API PATCH."""
        currency = "CAD" if marketplace == SP_API_MARKETPLACE_CA else "USD"
        encoded_sku = quote(sku, safe="")

        body = {
            "productType": product_type,
            "patches": [{
                "op": "replace",
                "path": "/attributes/purchasable_offer",
                "value": [{
                    "marketplace_id": marketplace,
                    "currency": currency,
                    "our_price": [{"schedule": [{"value_with_tax": new_price}]}],
                }],
            }],
        }

        listings = ListingsItems(
            credentials=CREDENTIALS,
            marketplace=self._marketplace(marketplace),
        )
        res = listings.patch_listings_item(
            sellerId=seller_id,
            sku=encoded_sku,
            marketplaceIds=[marketplace],
            body=body,
        )
        status = res.payload.get("status") if isinstance(res.payload, dict) else str(res.payload)
        logger.info(f"Price update {sku} → {currency}{new_price}: {status}")
        return {"status": status, "sku": sku, "new_price": new_price, "currency": currency}

    def update_listing(
        self,
        sku: str,
        updates: dict,
        marketplace: str,
        seller_id: str,
    ) -> dict:
        """Update listing attributes via Listings Items API PATCH."""
        encoded_sku = quote(sku, safe="")
        product_type = updates.pop("productType", "FOOD")
        patches = [
            {"op": "replace", "path": f"/attributes/{attr}", "value": value}
            for attr, value in updates.items()
        ]

        listings = ListingsItems(
            credentials=CREDENTIALS,
            marketplace=self._marketplace(marketplace),
        )
        res = listings.patch_listings_item(
            sellerId=seller_id,
            sku=encoded_sku,
            marketplaceIds=[marketplace],
            body={"productType": product_type, "patches": patches},
        )
        status = res.payload.get("status") if isinstance(res.payload, dict) else str(res.payload)
        logger.info(f"Listing update {sku}: {status}")
        return {"status": status, "sku": sku}

    def update_keyword_bid(
        self,
        campaign_id: str,
        keyword_id: str,
        new_bid: float,
        marketplace: str,
    ) -> dict:
        """PPC bid change — Advertising API not yet wired up."""
        logger.warning("PPC bid changes require Advertising API setup (not implemented)")
        return {
            "status": "not_implemented",
            "note": "Advertising API requires separate auth. Set up amazon-ads-api credentials.",
            "campaign_id": campaign_id,
            "keyword_id": keyword_id,
            "requested_bid": new_bid,
        }

    def update_campaign_budget(
        self,
        campaign_id: str,
        new_budget: float,
        marketplace: str,
    ) -> dict:
        """PPC budget change — Advertising API not yet wired up."""
        logger.warning("PPC budget changes require Advertising API setup (not implemented)")
        return {
            "status": "not_implemented",
            "note": "Advertising API requires separate auth. Set up amazon-ads-api credentials.",
            "campaign_id": campaign_id,
            "requested_budget": new_budget,
        }
