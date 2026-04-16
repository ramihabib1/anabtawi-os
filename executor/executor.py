"""
Executor daemon — watches approval_requests for approved actions and executes them.
Runs as a persistent systemd service on Hetzner. Polls every 60s.

Usage: python3 -m executor.executor
"""
import time
import logging
from datetime import datetime, timezone
from core.supabase_client import get_supabase
from executor.sp_api_client import SPAPIClient

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class Executor:

    def __init__(self):
        self.supabase = get_supabase()
        self.sp_api = SPAPIClient()

    def run_forever(self):
        logger.info("Executor started. Polling every 60s.")
        while True:
            try:
                self.process_approved_requests()
                self.expire_stale_requests()
            except Exception as e:
                logger.error(f"Executor loop error: {e}")
            time.sleep(60)

    def process_approved_requests(self):
        result = (
            self.supabase.table("approval_requests")
            .select("*")
            .eq("status", "approved")
            .is_("execution_result", "null")
            .execute()
        )
        for req in result.data:
            logger.info(f"Executing {req['action_type']} ({req['id'][:8]})")
            self.execute(req)

    def execute(self, req: dict):
        action_type = req["action_type"]
        payload = req.get("payload", {})
        result = {}

        try:
            if action_type == "ppc_bid_change":
                result = self.sp_api.update_keyword_bid(
                    campaign_id=payload["campaign_id"],
                    keyword_id=payload["keyword_id"],
                    new_bid=payload["recommended_bid"],
                    marketplace=payload["marketplace"],
                )
            elif action_type == "ppc_budget_change":
                result = self.sp_api.update_campaign_budget(
                    campaign_id=payload["campaign_id"],
                    new_budget=payload["recommended_budget"],
                    marketplace=payload["marketplace"],
                )
            elif action_type == "price_change":
                result = self.sp_api.update_price(
                    sku=payload["sku"],
                    new_price=payload["recommended_price"],
                    marketplace=payload["marketplace"],
                    seller_id=payload["seller_id"],
                )
            elif action_type == "listing_change":
                result = self.sp_api.update_listing(
                    sku=payload["sku"],
                    updates=payload["listing_updates"],
                    marketplace=payload["marketplace"],
                    seller_id=payload["seller_id"],
                )
            elif action_type == "fba_replenishment":
                # FBA inbound shipment creation is done manually in Seller Central
                result = {
                    "status": "manual_action_required",
                    "note": "Create FBA inbound shipment in Seller Central",
                    "sku": payload.get("sku"),
                    "units_to_send": payload.get("units_to_send"),
                    "boxes_to_send": payload.get("boxes_to_send"),
                }
            else:
                result = {"error": f"Unknown action type: {action_type}"}

        except Exception as e:
            result = {"error": str(e)}
            logger.error(f"Execution error for {req['id'][:8]}: {e}")

        # Write result back to approval_requests
        self.supabase.table("approval_requests").update({
            "execution_result": result,
        }).eq("id", req["id"]).execute()

        # Write to audit_log
        success = "error" not in result
        self.supabase.table("audit_log").insert({
            "agent": req["agent"],
            "action": action_type,
            "entity_type": "approval_request",
            "entity_id": req["id"],
            "details": result,
            "approval_id": req["id"],
            "success": success,
            "error_message": result.get("error"),
        }).execute()

        logger.info(f"Done {req['id'][:8]}: {result.get('status', result)}")

    def expire_stale_requests(self):
        now = datetime.now(timezone.utc).isoformat()
        expired = (
            self.supabase.table("approval_requests")
            .update({"status": "expired"})
            .eq("status", "pending")
            .lt("expires_at", now)
            .execute()
        )
        if expired.data:
            logger.info(f"Expired {len(expired.data)} stale approval request(s)")


if __name__ == "__main__":
    executor = Executor()
    executor.run_forever()
