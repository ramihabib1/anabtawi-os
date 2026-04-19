# Roadmap: Habib Distribution OS

## Overview

Foundation is live: three agents run daily on Hetzner, Mem0 observations accumulate, Telegram delivers approvals, and the Executor closes the loop to SP-API. The remaining work builds the intelligence layer that turns daily observations into compounding knowledge, then exposes that knowledge through a dashboard that gives Rami, his father, and his brother the right view of the business. Two agents (PPC, Competitor Intel) are blocked by missing credentials and data — they are stubbed as placeholder phases that activate when prerequisites are met.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Schema & Agent Extensions** - Additive schema migrations and inventory agent extensions that all downstream phases depend on
- [ ] **Phase 2: Weekly Consolidation & Validation** - First compounding loop: observations synthesize into patterns weekly, predictions validate daily
- [ ] **Phase 3: Monthly Review & Wiki Compiler** - Second compounding loop: patterns promote to playbooks monthly, wiki pages compile from validated knowledge
- [ ] **Phase 4: Dashboard Core** - Operational visibility for all three operators: health overview, approvals, agent logs, ROI ledger, wiki viewer
- [ ] **Phase 5: Dashboard Intelligence** - Intelligence features that expose the compounding knowledge layer: anomaly feed, prediction scoreboard, seasonal calendar, knowledge heatmap
- [ ] **Phase 6: Hardening & Ops** - Production reliability: retry crons, weekly health reports, bilingual notifications
- [ ] **Phase 7: PPC Agent** *(BLOCKED — ADS_API credentials not configured)*
- [ ] **Phase 8: Competitor Intel Agent** *(BLOCKED — competitors table empty)*

## Phase Details

### Phase 1: Schema & Agent Extensions
**Goal**: All new tables exist and the inventory agent captures predictions and recommendation baselines so every downstream phase has the data it needs
**Depends on**: Nothing (first phase)
**Requirements**: SCHEMA-01, SCHEMA-02, SCHEMA-03, SCHEMA-04, KCL-04, KCL-06
**Success Criteria** (what must be TRUE):
  1. `consolidation_log`, `prediction_log`, `recommendation_outcomes`, and `wiki_pages` tables exist in Supabase with correct columns and indexes
  2. After any inventory agent run, new rows appear in `prediction_log` with `predicted_value`, `resolution_date`, and `confidence` filled
  3. After any executor write, a row exists in `recommendation_outcomes` with `baseline_metrics` and `measurement_window_days` set at execution time
  4. All four migrations are idempotent (safe to re-run without error or data loss)
**Plans**: 3 plans
- [ ] 01-01-PLAN.md — Schema migrations (4 idempotent SQL files) + core/models.py Pydantic validators (PredictionRow, BaselineMetrics, MEASUREMENT_WINDOWS) + manual Supabase apply checkpoint
- [ ] 01-02-PLAN.md — Inventory agent extension: emit predictions[] for at-risk SKUs, write to prediction_log with PredictionRow validation + zero-prediction guardrail
- [ ] 01-03-PLAN.md — Executor extension: _build_baseline_metrics helper for all four action_types, write to recommendation_outcomes after successful SP-API dispatch with BaselineMetrics validation

### Phase 2: Weekly Consolidation & Validation
**Goal**: Observations compound into patterns every Saturday, and prediction accuracy is measured daily so the system is self-evaluating from day one
**Depends on**: Phase 1
**Requirements**: KCL-01, KCL-05
**Success Criteria** (what must be TRUE):
  1. After Saturday 20:00 UTC, new pattern memories appear in `vecs.memories` with `memory_type: pattern` and at least 3 supporting observation references
  2. `consolidation_log` watermark advances after each successful weekly job, preventing double-processing on re-run
  3. After daily 08:00 UTC validation run, `prediction_log` rows whose `resolution_date` has passed have `resolution_status` and `actual_outcome` filled
  4. Rami receives a Telegram alert if the weekly consolidation job fails
**Plans**: TBD

### Phase 3: Monthly Review & Wiki Compiler
**Goal**: Patterns are validated against real outcome data and promoted to playbooks, and the wiki makes all accumulated knowledge readable
**Depends on**: Phase 2
**Requirements**: KCL-02, KCL-03
**Success Criteria** (what must be TRUE):
  1. After the 1st-of-month job, patterns with outcome support are promoted to `memory_type: playbook` in Mem0 with confidence >= 0.9 and cited outcome evidence
  2. Contradicted patterns have reduced confidence scores or are marked for decay
  3. `wiki_pages` table contains at least one row per active product SKU with rendered markdown content and a `generated_at` timestamp from the current month
  4. Wiki pages include confidence indicators (high/medium/low) and cite the Mem0 observation IDs they were compiled from
**Plans**: TBD

### Phase 4: Dashboard Core
**Goal**: Rami, his father, and his brother can see the business health and act on recommendations from a browser without touching Telegram
**Depends on**: Phase 1
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05
**Success Criteria** (what must be TRUE):
  1. Home page shows inventory days-of-supply per SKU with red/yellow/green coding, today's agent run statuses, pending approval count, and today's revenue and order count — all from live Supabase data
  2. Approvals page lists all requests filterable by status; expanding any row shows the agent's full reasoning, the recommendation payload, and what-if projections; approve and reject buttons update `approval_requests.status`
  3. Agent logs page shows run history with token spend per run, expandable error details, and a 30-day token spend line chart
  4. ROI ledger shows per-executed-recommendation outcomes: baseline metric, measured result, revenue delta — sortable by impact
  5. Wiki viewer renders `wiki_pages` markdown with the page tree sidebar, confidence indicators, and last-compiled timestamp
**Plans**: TBD
**UI hint**: yes

### Phase 5: Dashboard Intelligence
**Goal**: The accumulated knowledge layer is visible as actionable intelligence: unusual patterns surface automatically, predictions are scored, and seasonal risk is visible weeks in advance
**Depends on**: Phase 3, Phase 4
**Requirements**: DASH-06, DASH-07, DASH-08, DASH-09
**Success Criteria** (what must be TRUE):
  1. Anomaly detection feed surfaces deviations 2+ standard deviations from the 30-day rolling baseline, ranked by estimated business impact, with current value, baseline, and suggested action shown
  2. Prediction scoreboard shows per-agent accuracy over rolling 30-day and 90-day windows; calibration view shows whether 0.8+ confidence predictions are statistically more accurate than lower-confidence ones
  3. Seasonal intelligence calendar shows 90-day forward demand predictions per SKU with confidence bands, and highlights Ramadan and Q4 windows with historical multipliers drawn from Mem0 playbooks
  4. Knowledge age heatmap shows all tracked SKUs and domains with last-observation date color-coded: green <7 days, yellow 7-21 days, red >21 days — blind spots are immediately visible
**Plans**: TBD
**UI hint**: yes

### Phase 6: Hardening & Ops
**Goal**: The system handles its own failures gracefully — failed agents retry automatically, Rami gets a weekly health pulse, and Arabic notifications reach the right people
**Depends on**: Phase 2
**Requirements**: OPS-01, OPS-02, OPS-03
**Success Criteria** (what must be TRUE):
  1. When an agent run fails, a retry cron fires 30 minutes later; if the retry also fails, Rami receives a Telegram alert identifying the agent and error
  2. Every Sunday at 10:00 UTC, Rami receives a Telegram health report showing agent run success rate, per-agent token spend for the week, Mem0 memory counts by tier (observations / patterns / playbooks), and pending approval count
  3. When a notification is created with `title_ar` and `body_ar` fields set, the Telegram formatter delivers the Arabic text alongside the English text
**Plans**: TBD

### Phase 7: PPC Agent *(BLOCKED)*
**Goal**: PPC campaign and keyword performance is analyzed daily, bid/budget recommendations flow through the approval pipeline, and PPC observations compound into the knowledge layer
**Depends on**: Phase 2
**Requirements**: PPC-01, PPC-02
**Status**: BLOCKED — `ADS_API_REFRESH_TOKEN`, `ADS_API_CLIENT_ID`, `ADS_API_CLIENT_SECRET` not configured in `.env`
**Prerequisite to unblock**: Add ADS API credentials to `.env` on Hetzner
**Success Criteria** (what must be TRUE):
  1. PPC agent runs daily at 06:00 UTC, analyzes ACOS / TACoS / conversion rates / wasted spend across all active campaigns and keywords
  2. Bid and budget recommendations appear in `approval_requests` with full reasoning and projected impact
  3. After each run, new observation memories appear in `vecs.memories` with `campaign_ids` metadata populated
**Plans**: None until unblocked

### Phase 8: Competitor Intel Agent *(BLOCKED)*
**Goal**: Competitor price, BSR, and OOS changes are monitored daily, pricing opportunities flow through the approval pipeline, and own listing health is watched automatically
**Depends on**: Phase 2
**Requirements**: COMP-01, COMP-02, COMP-03
**Status**: BLOCKED — `competitors` table is empty; no competitor ASINs to monitor
**Prerequisite to unblock**: Populate `competitors` table with at least one competitor ASIN per tracked product
**Success Criteria** (what must be TRUE):
  1. Competitor agent runs daily at 06:30 UTC, detects price changes >5%, OOS events, and BSR movements >20% across all tracked competitor ASINs
  2. Pricing opportunity recommendations appear in `approval_requests` when a competitor goes OOS or raises price, with estimated margin at recommended price shown
  3. Own listing health alerts appear in `notifications` when buy box is lost, BSR trend is declining, or review sentiment shifts
  4. After each run, competitor behavior observations appear in `vecs.memories` with `competitor_asins` metadata populated
**Plans**: None until unblocked

## Progress

**Execution Order:**
Phases execute in numeric order. Phase 4 may execute in parallel with Phase 2/3 if schema work (Phase 1) is complete. Phases 7 and 8 execute only after their prerequisites are resolved.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Schema & Agent Extensions | 0/3 | Not started | - |
| 2. Weekly Consolidation & Validation | 0/TBD | Not started | - |
| 3. Monthly Review & Wiki Compiler | 0/TBD | Not started | - |
| 4. Dashboard Core | 0/TBD | Not started | - |
| 5. Dashboard Intelligence | 0/TBD | Not started | - |
| 6. Hardening & Ops | 0/TBD | Not started | - |
| 7. PPC Agent (BLOCKED) | 0/TBD | Blocked | - |
| 8. Competitor Intel Agent (BLOCKED) | 0/TBD | Blocked | - |
