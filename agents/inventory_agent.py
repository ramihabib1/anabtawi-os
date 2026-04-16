"""
Inventory Agent — Daily stockout prediction and restock recommendations.
Schedule: 05:30 UTC daily.
"""

import json
import math
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from anthropic import Anthropic
from agents.base import BaseAgent
from core.config import L1_RULES, MODEL_DAILY


class InventoryAgent(BaseAgent):

    def __init__(self):
        super().__init__(agent_name="inventory_agent", domain="inventory")

    def fetch_data(self) -> dict:
        """Query Supabase for current inventory and sales data."""
        today = datetime.now(timezone.utc).date()
        thirty_days_ago = (today - timedelta(days=30)).isoformat()

        # Active products
        products_result = (
            self.supabase.table("products")
            .select(
                "id, sku, asin, product_name, units_per_box, "
                "fba_reorder_point, fba_reorder_qty, lead_time_days, "
                "fba_margin_pct, amazon_price, landed_cost, tags, is_active"
            )
            .eq("is_active", True)
            .execute()
        )
        products = {p["id"]: p for p in products_result.data}

        # Latest inventory snapshot per product
        # Get all snapshots, then pick most recent per product
        snapshots_result = (
            self.supabase.table("inventory_snapshots")
            .select(
                "product_id, fulfillable_qty, inbound_working_qty, "
                "inbound_shipped_qty, inbound_receiving_qty, "
                "reserved_qty, unfulfillable_qty, snapshot_at"
            )
            .order("snapshot_at", desc=True)
            .limit(500)
            .execute()
        )

        # Latest snapshot per product
        latest_snapshots = {}
        for snap in snapshots_result.data:
            pid = snap["product_id"]
            if pid not in latest_snapshots:
                latest_snapshots[pid] = snap

        # Sales last 30 days
        sales_result = (
            self.supabase.table("sales_daily")
            .select("product_id, sale_date, units_sold")
            .gte("sale_date", thirty_days_ago)
            .execute()
        )

        # Aggregate sales by product
        sales_by_product = defaultdict(list)
        for row in sales_result.data:
            sales_by_product[row["product_id"]].append(row["units_sold"])

        # Velocity calculation per product (avg daily units over 30 days)
        velocity = {}
        for pid, units_list in sales_by_product.items():
            total_units = sum(units_list)
            velocity[pid] = round(total_units / 30, 3)

        # Inbound shipments (in-transit to FBA) — lowercase enum values
        inbound_result = (
            self.supabase.table("inbound_shipments")
            .select("*")
            .in_("status", ["working", "shipped", "receiving"])
            .execute()
        )

        # Supplier shipments (on order, not yet received)
        supplier_result = (
            self.supabase.table("supplier_shipments")
            .select("*")
            .in_("status", ["confirmed", "in_transit", "draft"])
            .execute()
        )

        return {
            "products": products,
            "latest_snapshots": latest_snapshots,
            "velocity": velocity,
            "inbound_shipments": inbound_result.data,
            "supplier_shipments": supplier_result.data,
            "snapshot_date": today.isoformat(),
            "sales_window_days": 30,
        }

    def _build_inventory_table(self, data: dict) -> list[dict]:
        """Build a per-product inventory analysis table for the prompt."""
        products = data["products"]
        snapshots = data["latest_snapshots"]
        velocity = data["velocity"]
        rows = []

        for pid, product in products.items():
            snap = snapshots.get(pid, {})
            fulfillable = snap.get("fulfillable_qty", 0) or 0
            inbound = (
                (snap.get("inbound_working_qty") or 0)
                + (snap.get("inbound_shipped_qty") or 0)
                + (snap.get("inbound_receiving_qty") or 0)
            )
            daily_velocity = velocity.get(pid, 0.0)

            # Days of supply (based on fulfillable only — conservative)
            if daily_velocity > 0:
                days_of_supply = round(fulfillable / daily_velocity, 1)
                days_of_supply_with_inbound = round(
                    (fulfillable + inbound) / daily_velocity, 1
                )
            else:
                # No sales in 30 days — long runway
                days_of_supply = 999
                days_of_supply_with_inbound = 999

            # Reorder recommendation
            lead_time = product.get("lead_time_days") or 14
            reorder_point = product.get("fba_reorder_point") or 50
            reorder_qty = product.get("fba_reorder_qty") or 100
            units_per_box = product.get("units_per_box") or 1

            # Round up reorder qty to nearest case pack
            if units_per_box > 1:
                reorder_qty_rounded = (
                    math.ceil(reorder_qty / units_per_box) * units_per_box
                )
            else:
                reorder_qty_rounded = reorder_qty

            rows.append(
                {
                    "product_id": pid,
                    "sku": product["sku"],
                    "product_name": product["product_name"],
                    "fulfillable_qty": fulfillable,
                    "inbound_qty": inbound,
                    "avg_daily_velocity": daily_velocity,
                    "days_of_supply": days_of_supply,
                    "days_of_supply_with_inbound": days_of_supply_with_inbound,
                    "reorder_point": reorder_point,
                    "recommended_reorder_qty": reorder_qty_rounded,
                    "units_per_box": units_per_box,
                    "lead_time_days": lead_time,
                    "fba_margin_pct": product.get("fba_margin_pct"),
                    "amazon_price": product.get("amazon_price"),
                    "tags": product.get("tags", []),
                    "snapshot_date": data["snapshot_date"],
                }
            )

        # Sort by days_of_supply ascending (most critical first)
        rows.sort(key=lambda x: x["days_of_supply"])
        return rows

    def analyze(self, data: dict, memories: list) -> dict:
        """Build prompt and call Claude for inventory analysis."""
        inventory_table = self._build_inventory_table(data)

        # Format memories for context
        memory_text = ""
        if memories:
            memory_items = []
            for m in memories:
                mem_content = m.get("memory", "")
                mem_type = m.get("metadata", {}).get("memory_type", "observation")
                memory_items.append(f"[{mem_type.upper()}] {mem_content}")
            memory_text = "\n".join(memory_items)
        else:
            memory_text = "No prior knowledge accumulated yet — this is an early run."

        system_prompt = f"""You are the Inventory Agent for Habib Distribution, an Amazon seller
with ~30 SKUs of Middle Eastern food products (primarily sweets and baklava).

Your job: analyze current FBA inventory levels against sales velocity,
predict stockout risks, and recommend restock actions.

{L1_RULES}

Today's date: {data["snapshot_date"]}

ACCUMULATED KNOWLEDGE FROM PRIOR RUNS:
{memory_text}

ANALYSIS INSTRUCTIONS:
For each SKU, you already have pre-calculated days_of_supply and days_of_supply_with_inbound.
Use these directly. Your job is to reason about them contextually, not recalculate.

Flag products as:
- CRITICAL: days_of_supply <= 7 (stockout imminent)
- WARNING: days_of_supply <= 14 (below safe threshold)
- RESTOCK_NEEDED: days_of_supply <= lead_time_days + 7 (order now to avoid stockout)
- HEALTHY: everything else

For restock recommendations:
- Only recommend restocking if days_of_supply_with_inbound < (lead_time_days + 14)
- Quantity must be multiple of units_per_box (already rounded in the data)
- Consider seasonal factors from accumulated knowledge
- For products with 0 velocity but low stock, flag as WATCH (slow mover, low stock)

Inbound shipments and supplier shipments context:
- Inbound shipments: {json.dumps(data["inbound_shipments"]) if data["inbound_shipments"] else "None in transit"}
- Supplier shipments: {json.dumps(data["supplier_shipments"]) if data["supplier_shipments"] else "None pending"}

OUTPUT: You MUST respond with valid JSON only. No preamble, no markdown code blocks.
Just the raw JSON object matching this exact schema:

{{
  "analysis_date": "YYYY-MM-DD",
  "summary": "One sentence summary of overall inventory health",
  "alerts": [
    {{
      "severity": "critical|warning|info",
      "product_id": "...",
      "sku": "...",
      "product_name": "...",
      "title": "...",
      "body": "...",
      "days_of_supply": <number>
    }}
  ],
  "restock_recommendations": [
    {{
      "product_id": "...",
      "sku": "...",
      "product_name": "...",
      "current_stock": <number>,
      "inbound_qty": <number>,
      "daily_velocity": <number>,
      "days_of_supply": <number>,
      "recommended_qty": <number>,
      "units_per_box": <number>,
      "lead_time_days": <number>,
      "reasoning": "..."
    }}
  ],
  "healthy_products": [
    {{
      "sku": "...",
      "product_name": "...",
      "days_of_supply": <number>
    }}
  ],
  "observations": [
    {{
      "text": "Specific, factual observation worth remembering for future runs",
      "product_ids": ["..."],
      "confidence": <0.0-1.0>
    }}
  ]
}}"""

        user_message = f"""Here is today's inventory data for all {len(inventory_table)} active products:

{json.dumps(inventory_table, indent=2)}

Analyze this and produce your JSON response."""

        client = Anthropic()
        response = client.messages.create(
            model=MODEL_DAILY,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text.strip()

        # Strip markdown code fences if Claude added them anyway
        if raw_text.startswith("```"):
            lines = raw_text.split("\n")
            raw_text = "\n".join(lines[1:-1])

        result = json.loads(raw_text)
        result["_token_usage"] = {
            "input": response.usage.input_tokens,
            "output": response.usage.output_tokens,
        }
        return result

    def process_response(self, response: dict) -> str:
        """Write alerts to notifications and restocks to approval_requests."""
        alerts_written = 0
        approvals_written = 0

        # Write alerts to notifications
        for alert in response.get("alerts", []):
            try:
                self.supabase.table("notifications").insert(
                    {
                        "agent": self.agent_name,
                        "severity": alert["severity"],
                        "title": alert["title"],
                        "body": alert["body"],
                        "status": "unread",
                        "product_id": alert.get("product_id"),
                        "metadata": {
                            "days_of_supply": alert.get("days_of_supply"),
                            "sku": alert.get("sku"),
                            "run_id": self.run_id,
                        },
                    }
                ).execute()
                alerts_written += 1
            except Exception as e:
                print(f"[{self.run_id}] Failed to write alert: {e}")

        # Write restock recommendations to approval_requests
        for rec in response.get("restock_recommendations", []):
            try:
                self.supabase.table("approval_requests").insert(
                    {
                        "action_type": "fba_replenishment",
                        "agent": self.agent_name,
                        "description": (
                            f"Restock {rec['product_name']} — "
                            f"{rec['recommended_qty']} units "
                            f"({rec['recommended_qty'] // rec['units_per_box']} boxes). "
                            f"Current stock: {rec['current_stock']} units "
                            f"({rec['days_of_supply']} days supply)."
                        ),
                        "product_id": rec.get("product_id"),
                        "payload": {
                            "sku": rec["sku"],
                            "product_name": rec["product_name"],
                            "units_to_send": rec["recommended_qty"],
                            "boxes_to_send": rec["recommended_qty"] // rec["units_per_box"],
                            "units_per_box": rec["units_per_box"],
                            "fba_current_qty": rec["current_stock"],
                            "inbound_qty": rec["inbound_qty"],
                            "daily_velocity": rec["daily_velocity"],
                            "days_of_supply": rec["days_of_supply"],
                            "reasoning": rec["reasoning"],
                            "run_id": self.run_id,
                        },
                        "status": "pending",
                        "expires_at": (
                            datetime.now(timezone.utc) + timedelta(hours=24)
                        ).isoformat(),
                    }
                ).execute()
                approvals_written += 1
            except Exception as e:
                print(f"[{self.run_id}] Failed to write approval request: {e}")

        token_usage = response.get("_token_usage", {})
        summary = (
            f"{response.get('summary', '')} | "
            f"{alerts_written} alerts, {approvals_written} restock requests created. "
            f"Tokens: {token_usage.get('input', 0)}in / {token_usage.get('output', 0)}out"
        )
        return summary

    def log_run(self, success, error_message, output_summary, duration_ms):
        """Log to agent_runs."""
        try:
            self.supabase.table("agent_runs").insert(
                {
                    "agent": self.agent_name,
                    "task": "daily_inventory_analysis",
                    "trigger_type": "scheduled",
                    "input_summary": "Analyzed FBA inventory, sales velocity, inbound shipments",
                    "output_summary": output_summary[:1000] if output_summary else None,
                    "duration_ms": duration_ms,
                    "success": success,
                    "error_message": error_message[:500] if error_message else None,
                }
            ).execute()
        except Exception as e:
            print(f"[{self.run_id}] Failed to log run: {e}")


if __name__ == "__main__":
    agent = InventoryAgent()
    agent.run()
