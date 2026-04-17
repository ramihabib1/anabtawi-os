# Requirements: Habib Distribution OS

**Defined:** 2026-04-17
**Core Value:** Knowledge that compounds daily — after 6 months, the system knows more about this business than any human or competitor's AI

## v1 Requirements

### Schema Migrations

- [ ] **SCHEMA-01**: System tracks consolidation job state via `consolidation_log` table (`job_type`, `last_processed_cutoff` timestamp) so weekly/monthly jobs are idempotent and safe to re-run after failures
- [ ] **SCHEMA-02**: Inventory agent writes structured predictions to `prediction_log` table (`product_id`, `predicted_value`, `resolution_date`, `confidence`, `actual_outcome`, `resolution_status`) so prediction accuracy is measurable
- [ ] **SCHEMA-03**: Executor writes baseline metrics to `recommendation_outcomes` table at execution time (`approval_id`, `baseline_metrics`, `measurement_window_days`, `actual_outcome`, `revenue_delta`) so agent ROI is traceable
- [ ] **SCHEMA-04**: Wiki compiler writes compiled knowledge pages to `wiki_pages` table (`slug`, `title`, `category`, `content`, `generated_from`, `generated_at`) so the dashboard can render the knowledge base

### Knowledge Compounding Layer

- [ ] **KCL-01**: Weekly consolidation job (Saturday 20:00 UTC) queries `vecs.memories` directly via Postgres bounded by `consolidation_log` watermark, synthesizes patterns using Claude Sonnet (minimum 3 supporting observations required before creating a new pattern), writes pattern memories to Mem0, and updates watermark
- [ ] **KCL-02**: Monthly review job (1st of month 08:00 UTC) reads all patterns from Mem0, validates each against Supabase outcome data (sales_daily, profit_daily) using Claude Opus, promotes validated patterns to playbooks, decays contradicted patterns, and updates consolidation_log
- [ ] **KCL-03**: Wiki compiler runs after monthly review; generates per-product, per-competitor, and per-playbook markdown pages with confidence indicators and source citations; upserts into wiki_pages table
- [ ] **KCL-04**: Inventory agent extended to write a `predictions` array to `prediction_log` alongside existing `observations`, capturing predicted stockout dates and days-of-supply per SKU with confidence scores
- [ ] **KCL-05**: `validation_runner.py` runs daily (08:00 UTC); queries `prediction_log` for predictions whose `resolution_date` has passed; resolves each against current Supabase inventory data; writes `resolution_status` (accurate / inaccurate / partial) and `actual_outcome`
- [ ] **KCL-06**: Executor extended to capture baseline metrics from approval payload at execution time and write initial `recommendation_outcomes` row; `validation_runner.py` fills `actual_outcome` after measurement window expires

### Dashboard — Core

- [ ] **DASH-01**: Home page shows today's operational health at a glance: inventory status per SKU (days-of-supply with color coding: red <7d, yellow <14d, green 14d+), agent run status for today (all ran / partial / failed), pending approval count with direct link, today's revenue and order count
- [ ] **DASH-02**: Approvals page shows all approval requests filterable by status (pending / approved / rejected / expired); each request expands to show full agent reasoning, recommendation payload, what-if projections, and estimated financial impact; approve/reject buttons as Telegram backup
- [ ] **DASH-03**: Agent logs page shows run history table (timestamp, agent, success/failure, duration, token spend per run); expandable error details; line chart of daily token spend over last 30 days; cumulative spend this month
- [ ] **DASH-04**: ROI ledger tab on Agent Logs shows per-executed-recommendation outcome: action type, baseline metric, measured outcome after window, revenue delta attribution; sortable by impact
- [ ] **DASH-05**: Wiki viewer shows compiled knowledge pages in a browsable page tree (products / competitors / playbooks / briefs sidebar); renders markdown with confidence indicators (✅ ⚠️ ❓); shows last-compiled timestamp and source observation count per page

### Dashboard — Intelligence Features

- [ ] **DASH-06**: Anomaly detection feed shows statistically unusual patterns (2σ+ deviation from 30-day rolling baseline) ranked by estimated business impact; each anomaly shows: current value, historical baseline, deviation score, and suggested action
- [ ] **DASH-07**: Prediction scoreboard shows per-agent accuracy metrics over rolling 30-day and 90-day windows; calibration view showing whether high-confidence predictions (0.8+) are accurate at statistically higher rates than low-confidence ones
- [ ] **DASH-08**: Seasonal intelligence calendar shows forward-looking demand predictions by SKU for next 90 days based on accumulated Mem0 patterns, with confidence bands; highlights Ramadan and Q4 windows with historical multipliers
- [ ] **DASH-09**: Knowledge age heatmap shows a color-coded grid of all tracked SKUs and domains with last-observation date (green: <7d, yellow: 7-21d, red: >21d) so blind spots are visible

### Hardening & Ops

- [ ] **OPS-01**: Retry cron fires 30 minutes after each scheduled agent slot; checks `agent_runs` for failed runs today; re-runs agent if no successful run exists; sends Telegram alert if retry also fails
- [ ] **OPS-02**: Weekly health report (Sunday 10:00 UTC) sends Telegram summary covering: agent run success rate, total token spend for the week per agent, Mem0 memory count trend (observations / patterns / playbooks), pending approval count
- [ ] **OPS-03**: Notifications table and Telegram formatter support Arabic fields (`title_ar`, `body_ar`) for bilingual alert delivery

## v1 Blocked (Placeholder Phases)

These phases are included in the roadmap but will not be executed until prerequisites are met.

### PPC Agent *(blocked: ADS_API credentials not configured)*

- **PPC-01**: PPC agent analyzes campaign and keyword performance daily (ACOS, TACoS, conversion rates, wasted spend) and generates bid/budget recommendations → `approval_requests`
- **PPC-02**: PPC agent writes campaign and keyword observations to Mem0 with `campaign_ids` metadata
- **Prerequisite**: `ADS_API_REFRESH_TOKEN`, `ADS_API_CLIENT_ID`, `ADS_API_CLIENT_SECRET` added to `.env`

### Competitor Intel Agent *(blocked: competitors table is empty)*

- **COMP-01**: Competitor agent monitors tracked competitor ASINs daily (price, BSR, OOS status, review velocity) and generates pricing opportunity recommendations → `approval_requests`
- **COMP-02**: Competitor agent monitors own listing health (buy box ownership, BSR trend, review sentiment) and writes listing health alerts → `notifications`
- **COMP-03**: Competitor agent writes competitor behavior observations to Mem0 with `competitor_asins` metadata
- **Prerequisite**: `competitors` table populated with at least one competitor ASIN per tracked product

## v2 Requirements

Deferred to future milestone. Tracked but not in current roadmap.

### Role-Based Views

- **ROLE-01**: Father view shows finance-focused dashboard: revenue/COGS/margin per SKU and total, approval history with financial impact, agent ROI cumulative summary, system cost tracking
- **ROLE-02**: Brother view shows sales/marketing dashboard: BSR trends, competitor intel feed, PPC performance summary, listing health, seasonal calendar
- **ROLE-03**: Role assignment enforced via Supabase RLS based on `users.role` field

### Knowledge Graph

- **GRAPH-01**: Knowledge graph visualization shows entity relationship map (products ↔ competitors ↔ seasons ↔ keywords) built from co-occurrence metadata in Mem0 memories; rendered with React Flow (`@xyflow/react`)
- **GRAPH-02**: Graph nodes link to related wiki pages and observation history

## Out of Scope

| Feature | Reason |
|---------|--------|
| Walmart Canada | Future marketplace — add after Amazon is fully automated |
| Multi-tenant / productization | Future agency expansion — zero code forking needed when ready, but not now |
| FalkorDB graph memory | Deferred until 100+ SKUs justify traversal over vector search |
| Mobile app | Web dashboard sufficient for this operator profile |
| Real-time WebSocket feeds | Batch agent system; polling is sufficient |
| Custom ML anomaly models | Rolling mean + stddev is interpretable and sufficient for 30 SKUs |
| Editable wiki pages | Single source of truth is Mem0 — direct wiki edits would be overwritten on next compilation |
| Social login / OAuth | Email/password sufficient for 3-person team |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SCHEMA-01 | Phase 1 | Pending |
| SCHEMA-02 | Phase 1 | Pending |
| SCHEMA-03 | Phase 1 | Pending |
| SCHEMA-04 | Phase 1 | Pending |
| KCL-04 | Phase 1 | Pending |
| KCL-06 | Phase 1 | Pending |
| KCL-01 | Phase 2 | Pending |
| KCL-05 | Phase 2 | Pending |
| KCL-02 | Phase 3 | Pending |
| KCL-03 | Phase 3 | Pending |
| DASH-01 | Phase 4 | Pending |
| DASH-02 | Phase 4 | Pending |
| DASH-03 | Phase 4 | Pending |
| DASH-04 | Phase 4 | Pending |
| DASH-05 | Phase 4 | Pending |
| DASH-06 | Phase 5 | Pending |
| DASH-07 | Phase 5 | Pending |
| DASH-08 | Phase 5 | Pending |
| DASH-09 | Phase 5 | Pending |
| OPS-01 | Phase 6 | Pending |
| OPS-02 | Phase 6 | Pending |
| OPS-03 | Phase 6 | Pending |
| PPC-01 | Phase 7 (BLOCKED) | Pending |
| PPC-02 | Phase 7 (BLOCKED) | Pending |
| COMP-01 | Phase 8 (BLOCKED) | Pending |
| COMP-02 | Phase 8 (BLOCKED) | Pending |
| COMP-03 | Phase 8 (BLOCKED) | Pending |

**Coverage:**
- v1 requirements: 22 total (+ 5 blocked placeholders)
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-17*
*Last updated: 2026-04-17 after initial definition*
