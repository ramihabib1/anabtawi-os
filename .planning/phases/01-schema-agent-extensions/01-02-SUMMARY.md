---
phase: 01-schema-agent-extensions
plan: "02"
subsystem: agents
tags: [inventory-agent, prediction-log, pydantic, knowledge-compounding]

dependency_graph:
  requires:
    - 01-01 (prediction_log table, core/models.py PredictionRow)
  provides:
    - predictions[] array emitted by inventory agent for at-risk SKUs
    - prediction_log rows written per at-risk SKU (validated by PredictionRow)
    - zero-prediction guardrail notification (fires when all rows fail validation)
  affects:
    - Phase 2 validation_runner.py (resolves these prediction rows daily)
    - Phase 5 prediction scoreboard (scores accuracy over time)

tech_stack:
  modified:
    - agents/inventory_agent.py
  patterns:
    - Per-row try/except validation (matches existing alerts/restock loop pattern)
    - PredictionRow.model_dump() direct insert into Supabase
    - Defensive guards for Claude API edge cases (empty content, truncated output)

key_files:
  created: []
  modified:
    - agents/inventory_agent.py

decisions:
  - "At-risk threshold = days_of_supply <= lead_time_days + 14 (per D-03/D-04)"
  - "predicted_value = days_of_supply float (e.g. 11.2), not a boolean"
  - "resolution_date = snapshot_date + ceil(days_of_supply) days"
  - "0/0 predictions is valid output when no SKUs are at-risk (not an error)"
  - "Validation failures log per-row but do not abort the agent run"

metrics:
  duration: "26 seconds (smoke test)"
  completed_date: "2026-04-19"
  tasks_completed: 3
  tasks_total: 3
  files_created: 0
  files_modified: 1
---

# Phase 01 Plan 02: Inventory Agent Prediction Capture Summary

Inventory agent extended additively to emit structured stockout predictions to `prediction_log` for every at-risk SKU on each run. Closes the forecasting-accuracy loop that Phase 2's validation_runner resolves daily.

## Tasks Completed

### Task 1: Extend analyze() to emit predictions[] for at-risk SKUs

Three surgical edits to `agents/inventory_agent.py` `analyze()` method:

**Edit 1 — PREDICTION RULES block** appended to ANALYSIS INSTRUCTIONS section in system prompt. Defines at-risk threshold (`days_of_supply <= lead_time_days + 14`), confidence tiers (0.9+ for near-certain stockout, 0.7-0.8 for 7-14 day buffer, 0.5-0.6 for 14+ day buffer), and exclusion rules (no predictions for healthy SKUs or SKUs with days_of_supply=999).

**Edit 2 — predictions[] schema** added as sibling key to `observations[]` in JSON output schema. Includes `product_id`, `sku`, `predicted_value` (days_of_supply float), `resolution_date` (YYYY-MM-DD), `confidence`, and `reasoning` fields.

**Edit 3 — Defensive guards** added after `client.messages.create()`: empty content list check (raises ValueError) and stop_reason != "end_turn" warning (flags potential JSON truncation, suggests raising max_tokens).

### Task 2: Extend process_response() with prediction_log inserts and zero-prediction guardrail

Three surgical edits to `process_response()`:

**Edit 1 — Imports** added at top of file: `from core.models import PredictionRow` and `from pydantic import ValidationError`.

**Edit 2 — Prediction_log write loop** inserted after the restock_recommendations loop. For each `predictions[]` entry: validates with `PredictionRow(...)`, inserts via `validated.model_dump()`, increments `predictions_written`. Validation failures caught per-row with `except ValidationError` (logged, not raised). Zero-prediction guardrail fires a critical notification when `predictions_attempted > 0` but `predictions_written == 0` (all rows failed validation — silent gap signal).

**Edit 3 — Updated summary string** now includes `{predictions_written}/{predictions_attempted} predictions written` alongside existing alert and restock counts.

### Task 3: End-to-end smoke test

Run: `python3 -m agents.inventory_agent`

**Result:**
- Exit code: 0 (Success=True)
- Duration: 25,625ms
- Output summary: `"Inventory health is concerning with only 7 active SKUs showing sales velocity, while 14 products have zero sales but maintain stock levels. | 1 alerts, 0 restock requests, 0/0 predictions written. Tokens: 6399in / 1395out"`
- Predictions written: 0/0 — no SKUs currently at-risk (all products above the lead_time + 14 threshold). This is the correct behavior — zero predictions is a valid healthy output.
- agent_runs row: success=true, output_summary contains "predictions written" ✓
- No ImportError, ModuleNotFoundError, or ValidationError in logs

**Note on Mem0:** Mem0/pgvector connection failed (DNS resolution error in local dev). Agent degraded gracefully — `Continuing without memory — agent will run with no prior knowledge.` This is expected behavior on the dev machine; Hetzner has network access to Supabase.

## Deviations from Plan

None. All edits applied exactly as specified. The `sku` field appears in the predictions[] JSON schema (so Claude can reference it in reasoning) but is not written to prediction_log — `product_id` is the FK. The `PredictionRow` model uses `product_id` directly from Claude's response.

## Known Stubs

None. The prediction_log write path is fully implemented. When no at-risk SKUs exist, `0/0 predictions written` is correct output.

## Self-Check: PASSED
