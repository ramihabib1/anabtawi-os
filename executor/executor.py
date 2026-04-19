"""
Executor daemon — watches approval_requests for approved actions and executes them.
Runs as a persistent systemd service on Hetzner. Polls every 60s.

Usage: python3 -m executor.executor
"""
import time
import logging
from datetime import datetime, timedelta, timezone
from core.supabase_client import get_supabase
from executor.sp_api_client import SPAPIClient
from core.models import BaselineMetrics, MEASUREMENT_WINDOWS
from pydantic import ValidationError

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

        # Write recommendation_outcomes ONLY on successful execution (per AI-SPEC §4 Pattern C).
        # Failure here must NOT block the audit_log write — non-critical defensive try/except.
        if success:
            try:
                baseline = self._build_baseline_metrics(action_type, payload)
                validated = BaselineMetrics(action_type=action_type, metrics=baseline)
                self.supabase.table("recommendation_outcomes").insert({
                    "approval_id":             req["id"],
                    "action_type":             action_type,
                    "agent":                   req["agent"],
                    "product_id":              req.get("product_id"),
                    "baseline_metrics":        validated.metrics,
                    "measurement_window_days": MEASUREMENT_WINDOWS.get(action_type, 14),
                    "outcome_status":          "pending",
                }).execute()
            except ValidationError as e:
                logger.warning(
                    f"Baseline metrics validation failed for {req['id'][:8]} "
                    f"(action_type={action_type}): {e}. ROI ledger will have a gap."
                )
            except Exception as e:
                logger.warning(
                    f"Failed to write recommendation_outcomes for {req['id'][:8]}: {e}. "
                    "ROI ledger will have a gap."
                )

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

    def _build_baseline_metrics(self, action_type: str, payload: dict) -> dict:
        """Capture baseline metrics at execution time per D-05.

        For fba_replenishment: data is already in the approval payload (no DB query).
        For price_change and PPC actions: queries Supabase for current state.

        Returns a dict suitable for recommendation_outcomes.baseline_metrics JSONB.
        Required keys per action_type are enforced by BaselineMetrics validator (D-05).
        Missing source data results in None values, not missing keys — validator passes
        but downstream consumers (DASH-04) will display "no data" rather than crash.
        """
        if action_type == "fba_replenishment":
            # All four required keys come from the approval payload (D-05; CONTEXT §Specific Ideas).
            # daily_velocity in payload is the 30-day average; use it as proxy for both windows
            # until the inventory agent emits separate 7d/30d velocities (out of Phase 1 scope).
            velocity = payload.get("daily_velocity")
            return {
                "current_stock":      payload.get("fba_current_qty"),
                "daily_velocity_7d":  velocity,
                "daily_velocity_30d": velocity,
                "days_of_supply":     payload.get("days_of_supply"),
            }

        elif action_type == "price_change":
            # Query Supabase for current state. Required keys (D-05):
            # current_price, current_bsr, revenue_7d
            product_id = payload.get("product_id")
            sku = payload.get("sku")

            # current_price: prefer payload value if present, else query products
            current_price = payload.get("current_price")
            if current_price is None and (product_id or sku):
                try:
                    q = self.supabase.table("products").select("amazon_price")
                    if product_id:
                        q = q.eq("id", product_id)
                    else:
                        q = q.eq("sku", sku)
                    r = q.limit(1).execute()
                    if r.data:
                        current_price = r.data[0].get("amazon_price")
                except Exception as e:
                    logger.warning(f"price_change baseline: products query failed: {e}")

            # current_bsr: latest product_snapshots row for this product
            current_bsr = None
            if product_id:
                try:
                    r = (
                        self.supabase.table("product_snapshots")
                        .select("bsr")
                        .eq("product_id", product_id)
                        .order("snapshot_at", desc=True)
                        .limit(1)
                        .execute()
                    )
                    if r.data:
                        current_bsr = r.data[0].get("bsr")
                except Exception as e:
                    logger.warning(f"price_change baseline: product_snapshots query failed: {e}")

            # revenue_7d: sum gross_revenue from sales_daily over last 7 days
            revenue_7d = None
            if product_id:
                try:
                    cutoff = (datetime.now(timezone.utc).date() - timedelta(days=7)).isoformat()
                    r = (
                        self.supabase.table("sales_daily")
                        .select("gross_revenue")
                        .eq("product_id", product_id)
                        .gte("sale_date", cutoff)
                        .execute()
                    )
                    if r.data:
                        revenue_7d = round(sum((row.get("gross_revenue") or 0) for row in r.data), 2)
                    else:
                        revenue_7d = 0.0
                except Exception as e:
                    logger.warning(f"price_change baseline: sales_daily query failed: {e}")

            return {
                "current_price": current_price,
                "current_bsr":   current_bsr,
                "revenue_7d":    revenue_7d,
            }

        elif action_type == "ppc_bid_change":
            # Required keys (D-05): current_bid, acos_7d, acos_30d, spend_7d
            # PPC tables may be empty (Phase 7 BLOCKED). Defaults are None on missing data.
            keyword_id = payload.get("keyword_id")
            current_bid = payload.get("current_bid")
            acos_7d = acos_30d = spend_7d = None

            if keyword_id:
                try:
                    cutoff_30 = (datetime.now(timezone.utc).date() - timedelta(days=30)).isoformat()
                    cutoff_7 = (datetime.now(timezone.utc).date() - timedelta(days=7)).isoformat()
                    r = (
                        self.supabase.table("ppc_keyword_stats_daily")
                        .select("stat_date, acos, spend")
                        .eq("keyword_id", keyword_id)
                        .gte("stat_date", cutoff_30)
                        .execute()
                    )
                    if r.data:
                        rows_30 = r.data
                        rows_7 = [row for row in rows_30 if row.get("stat_date", "") >= cutoff_7]
                        acos_30d = (
                            round(sum(row.get("acos") or 0 for row in rows_30) / len(rows_30), 4)
                            if rows_30 else None
                        )
                        acos_7d = (
                            round(sum(row.get("acos") or 0 for row in rows_7) / len(rows_7), 4)
                            if rows_7 else None
                        )
                        spend_7d = round(sum(row.get("spend") or 0 for row in rows_7), 2)
                    else:
                        logger.warning(
                            f"ppc_bid_change baseline: no ppc_keyword_stats_daily rows for "
                            f"keyword_id={keyword_id} (Phase 7 BLOCKED — table may be empty)"
                        )
                except Exception as e:
                    logger.warning(f"ppc_bid_change baseline: query failed: {e}")

            return {
                "current_bid": current_bid,
                "acos_7d":     acos_7d,
                "acos_30d":    acos_30d,
                "spend_7d":    spend_7d,
            }

        elif action_type == "ppc_budget_change":
            # Required keys (D-05): current_budget, acos_7d, acos_30d, spend_30d
            campaign_id = payload.get("campaign_id")
            current_budget = payload.get("current_budget")
            acos_7d = acos_30d = spend_30d = None

            if campaign_id:
                try:
                    cutoff_30 = (datetime.now(timezone.utc).date() - timedelta(days=30)).isoformat()
                    cutoff_7 = (datetime.now(timezone.utc).date() - timedelta(days=7)).isoformat()
                    r = (
                        self.supabase.table("ppc_campaign_stats_daily")
                        .select("stat_date, acos, spend")
                        .eq("campaign_id", campaign_id)
                        .gte("stat_date", cutoff_30)
                        .execute()
                    )
                    if r.data:
                        rows_30 = r.data
                        rows_7 = [row for row in rows_30 if row.get("stat_date", "") >= cutoff_7]
                        acos_30d = (
                            round(sum(row.get("acos") or 0 for row in rows_30) / len(rows_30), 4)
                            if rows_30 else None
                        )
                        acos_7d = (
                            round(sum(row.get("acos") or 0 for row in rows_7) / len(rows_7), 4)
                            if rows_7 else None
                        )
                        spend_30d = round(sum(row.get("spend") or 0 for row in rows_30), 2)
                    else:
                        logger.warning(
                            f"ppc_budget_change baseline: no ppc_campaign_stats_daily rows for "
                            f"campaign_id={campaign_id} (Phase 7 BLOCKED — table may be empty)"
                        )
                except Exception as e:
                    logger.warning(f"ppc_budget_change baseline: query failed: {e}")

            return {
                "current_budget": current_budget,
                "acos_7d":        acos_7d,
                "acos_30d":       acos_30d,
                "spend_30d":      spend_30d,
            }

        else:
            # Unknown action type — return empty dict, BaselineMetrics will accept it
            # (no required keys defined for unknown action_types).
            return {}

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
