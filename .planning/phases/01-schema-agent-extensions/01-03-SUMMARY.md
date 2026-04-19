---
phase: 01-schema-agent-extensions
plan: "03"
subsystem: executor
tags: [executor, recommendation-outcomes, baseline-metrics, roi-ledger, knowledge-compounding]

dependency_graph:
  requires:
    - 01-01 (recommendation_outcomes table, core/models.py BaselineMetrics + MEASUREMENT_WINDOWS)
  provides:
    - _build_baseline_metrics() helper on Executor class
    - recommendation_outcomes row written per successful SP-API execution
    - baseline_metrics JSONB captured at execution time (cannot be retroactively reconstructed)
  affects:
    - Phase 4 DASH-04 ROI ledger (reads recommendation_outcomes baselines)
    - Phase 5 prediction scoreboard (revenue_delta attribution)

tech_stack:
  modified:
    - executor/executor.py
  patterns:
    - Private method dispatched on action_type (matches BaseAgent pattern)
    - try/except per Supabase query (logger.warning, not exception propagation)
    - Non-critical write pattern: failure logs warning, does not block audit_log

key_files:
  created: []
  modified:
    - executor/executor.py

decisions:
  - "Baseline captured at execution time, not at approval time (per AI-SPEC §1b)"
  - "fba_replenishment reads from payload — no extra DB query (data already present per D-05)"
  - "daily_velocity_7d == daily_velocity_30d for fba_replenishment (30d proxy, intentional per Task 1 plan note)"
  - "Phase 7 BLOCKED: PPC stats tables may be empty — warning logged, None values returned (not an error)"
  - "Unknown action_types return empty dict — BaselineMetrics allows, ROI ledger shows gap"
  - "MEASUREMENT_WINDOWS.get(action_type, 14) provides 14-day fallback for unknown action_types"

metrics:
  completed_date: "2026-04-19"
  tasks_completed: 2
  tasks_total: 3
  files_created: 0
  files_modified: 1
---

# Phase 01 Plan 03: Executor Baseline Snapshot Summary

Executor extended additively to capture baseline metrics to `recommendation_outcomes` at execution time for every successful approved action. Establishes the data substrate Phase 4's ROI ledger and Phase 5's prediction scoreboard depend on.

## Tasks Completed

### Task 1: Add _build_baseline_metrics helper method to Executor

Two surgical edits to `executor/executor.py`:

**Edit 1 — Imports** added after existing imports:
- `from datetime import timedelta`
- `from core.models import BaselineMetrics, MEASUREMENT_WINDOWS`
- `from pydantic import ValidationError`

**Edit 2 — `_build_baseline_metrics(action_type, payload)` private method** inserted between `execute()` and `expire_stale_requests()`. Four dispatch branches:

- **fba_replenishment**: reads `fba_current_qty → current_stock`, `daily_velocity → daily_velocity_7d + daily_velocity_30d` (proxy), `days_of_supply` from payload. No DB query.
- **price_change**: queries `products.amazon_price`, `product_snapshots.bsr` (latest), `sales_daily.gross_revenue` (sum last 7 days). Each query wrapped in try/except with `logger.warning` on failure.
- **ppc_bid_change**: queries `ppc_keyword_stats_daily` for last 30 days, computes `acos_7d`, `acos_30d`, `spend_7d`. Logs Phase 7 BLOCKED warning when table is empty.
- **ppc_budget_change**: queries `ppc_campaign_stats_daily` for last 30 days, computes `acos_7d`, `acos_30d`, `spend_30d`. Logs Phase 7 BLOCKED warning when table is empty.
- **unknown action_types**: returns `{}` (BaselineMetrics passes, no required keys defined).

### Task 2: Insert recommendation_outcomes write into execute()

One surgical edit to `execute()` method. Block inserted after `success = "error" not in result` and before the existing `audit_log` insert:

```python
if success:
    try:
        baseline = self._build_baseline_metrics(action_type, payload)
        validated = BaselineMetrics(action_type=action_type, metrics=baseline)
        self.supabase.table("recommendation_outcomes").insert({
            "approval_id": req["id"],
            "action_type": action_type,
            "agent": req["agent"],
            "product_id": req.get("product_id"),
            "baseline_metrics": validated.metrics,
            "measurement_window_days": MEASUREMENT_WINDOWS.get(action_type, 14),
            "outcome_status": "pending",
        }).execute()
    except ValidationError as e:
        logger.warning(f"Baseline metrics validation failed... ROI ledger will have a gap.")
    except Exception as e:
        logger.warning(f"Failed to write recommendation_outcomes... ROI ledger will have a gap.")
```

Failure path uses `logger.warning` — does not block the existing `audit_log` insert or the executor loop.

### Task 3: PENDING — human checkpoint

Rami must restart `habib-executor.service` on Hetzner, approve a pending `fba_replenishment` request, and verify a `recommendation_outcomes` row is created with all four required baseline_metrics keys (`current_stock`, `daily_velocity_7d`, `daily_velocity_30d`, `days_of_supply`) and `measurement_window_days=30`.

Verification SQL:
```sql
SELECT ro.approval_id, ro.action_type, ro.agent, ro.baseline_metrics,
       ro.measurement_window_days, ro.outcome_status
FROM recommendation_outcomes ro
ORDER BY ro.created_at DESC LIMIT 1;
```

## Deviations from Plan

None. All edits applied exactly as specified.

## Notes

- PPC stats tables are expected to be empty (Phase 7 BLOCKED status). The executor handles this gracefully: None values are returned for acos_7d/acos_30d/spend fields, Phase 7 BLOCKED warning is logged. BaselineMetrics validation passes (presence of key, not value, is enforced).
- The existing audit_log write path is unaffected — recommendation_outcomes is a non-critical additive write.

## Self-Check: PASSED (Tasks 1 and 2)
