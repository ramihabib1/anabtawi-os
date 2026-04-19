---
phase: 01-schema-agent-extensions
plan: "01"
subsystem: schema
tags: [migrations, pydantic, data-contracts, sql, knowledge-compounding]

dependency_graph:
  requires: []
  provides:
    - consolidation_log table DDL (ready to apply)
    - prediction_log table DDL (ready to apply)
    - recommendation_outcomes table DDL (ready to apply)
    - wiki_pages table DDL (ready to apply)
    - PredictionRow Pydantic model (importable by Plans 02 and 03)
    - BaselineMetrics Pydantic model (importable by Plan 03)
    - MEASUREMENT_WINDOWS constant (importable by Plan 03)
  affects:
    - Plans 02 and 03 (Wave 2) — cannot start until migrations applied and tables exist

tech_stack:
  added:
    - Pydantic v2 field_validator and model_validator patterns
  patterns:
    - Idempotent SQL migrations using CREATE TABLE/INDEX IF NOT EXISTS
    - Per-action_type required key enforcement via _REQUIRED_BASELINE_KEYS dict
    - Module-level UPPER_SNAKE constants (matches core/config.py convention)

key_files:
  created:
    - scripts/migrations/001_consolidation_log.sql
    - scripts/migrations/002_prediction_log.sql
    - scripts/migrations/003_recommendation_outcomes.sql
    - scripts/migrations/004_wiki_pages.sql
    - core/models.py
  modified: []

decisions:
  - "D-07 honored: four SQL files in scripts/migrations/ for manual apply via Supabase SQL editor — no migration runner"
  - "PredictionRow field names match prediction_log columns exactly for model_dump() insert pattern"
  - "MEASUREMENT_WINDOWS exported from core/models.py (not re-defined in executor.py) for single source of truth"
  - "BaselineMetrics raises ValueError with sorted missing keys for operator-readable error messages"

metrics:
  duration: "116 seconds"
  completed_date: "2026-04-19"
  tasks_completed: 3
  tasks_total: 3
  files_created: 5
  files_modified: 0
---

# Phase 01 Plan 01: Schema Migrations and Pydantic Validation Models Summary

Four idempotent SQL migration files and two Pydantic validation models establishing the data contracts the entire knowledge-compounding and ROI-ledger system depends on.

## Tasks Completed

### Task 1: Four idempotent SQL migration files (commit 7ca9729)

All four files written to `scripts/migrations/`. Each file uses `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` throughout. No `DROP TABLE`, `TRUNCATE`, or `DELETE` statements.

**001_consolidation_log.sql** — watermark table tracking consolidation job state. Uses `job_type TEXT PRIMARY KEY` as the unique key. Includes `ON CONFLICT (job_type) DO NOTHING` seed rows for `weekly_patterns` and `monthly_review`, ensuring Phase 2 upserts are safe on first run.

**002_prediction_log.sql** — tracks stockout predictions with binary resolution (`pending | accurate | inaccurate`). `product_id UUID` references `products(id)`. Three indexes: `(resolution_date, resolution_status)` for validation_runner queries, `(product_id, created_at DESC)` for dashboard scoreboard, `(run_id)` for agent run correlation.

**003_recommendation_outcomes.sql** — ROI ledger capturing baseline metrics at execution time. `approval_id UUID` references `approval_requests(id)`. `product_id UUID` nullable reference to `products(id)`. `baseline_metrics JSONB NOT NULL DEFAULT '{}'::jsonb`. `outcome_status` enum: `pending | measured | inconclusive`. Three indexes.

**004_wiki_pages.sql** — wiki content store with `slug TEXT UNIQUE NOT NULL` and `category CHECK (category IN ('product', 'competitor', 'playbook', 'brief'))`. Two indexes on category and slug for dashboard wiki viewer navigation.

### Task 2: core/models.py with PredictionRow and BaselineMetrics (commit f91817a)

**PredictionRow** — validates one entry from Claude's `predictions[]` array before `prediction_log` insert. Field names map 1:1 to prediction_log columns so `.model_dump()` can be passed directly to `supabase.table('prediction_log').insert()`.

Three validators:
- `predicted_value_must_be_positive` — rejects 0 (already stocked out, use alert not prediction row)
- `must_be_valid_iso_date` — validates `snapshot_date` and `resolution_date` as ISO YYYY-MM-DD
- `confidence_in_range` — enforces [0.0, 1.0]

**_REQUIRED_BASELINE_KEYS** — module-level dict enforcing D-05 required key sets per action_type:
- `fba_replenishment`: current_stock, daily_velocity_7d, daily_velocity_30d, days_of_supply
- `price_change`: current_price, current_bsr, revenue_7d
- `ppc_bid_change`: current_bid, acos_7d, acos_30d, spend_7d
- `ppc_budget_change`: current_budget, acos_7d, acos_30d, spend_30d

**MEASUREMENT_WINDOWS** — module-level constant (D-06 defaults) exported for import by executor/executor.py in Plan 03.

**BaselineMetrics** — validates `baseline_metrics` JSONB before `recommendation_outcomes` insert. `@model_validator(mode="after")` checks key presence (not values), raises with sorted list of missing keys for operator-readable error messages.

### Task 3: Apply migrations to Supabase (commit — checkpoint resolved)

All four migrations applied manually via Supabase SQL editor. All four tables confirmed in `information_schema.tables`. Consolidation_log seed rows verified (monthly_review, weekly_patterns, both with last_run_success=false, total_runs_count=0). Idempotency confirmed — re-running each file produced no errors.

## Deviations from Plan

None — plan executed exactly as written. The four SQL files and core/models.py match the exact DDL and code specified in the plan.

## Known Stubs

None. No UI-visible stubs. Migration files are SQL DDL ready for direct application. core/models.py exports working Pydantic validators with no placeholder logic.

## Threat Flags

None identified. This plan creates no network endpoints, auth paths, or file access patterns. The new tables contain no PII. All writes go through the existing Supabase service key pattern (server-side only, never exposed to dashboard frontend).

## Self-Check

Files exist:
- FOUND: scripts/migrations/001_consolidation_log.sql
- FOUND: scripts/migrations/002_prediction_log.sql
- FOUND: scripts/migrations/003_recommendation_outcomes.sql
- FOUND: scripts/migrations/004_wiki_pages.sql
- FOUND: core/models.py

Commits exist:
- FOUND: 7ca9729 — feat(01-01): write four idempotent SQL migration files
- FOUND: f91817a — feat(01-01): create core/models.py with PredictionRow and BaselineMetrics

Post-commit deletion check: No deletions — CLEAN

## Self-Check: PASSED
