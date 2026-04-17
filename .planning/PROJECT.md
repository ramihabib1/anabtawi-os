# Habib Distribution OS

## What This Is

An autonomous business operating system for a family-run Amazon FBA distribution company (~30 SKUs of Middle Eastern food products). Three AI agents run daily, accumulate knowledge over time via Mem0, and surface intelligence to three operators — Rami (technical/ops), Father (finance), and Brother (sales/marketing) — through Telegram and a Next.js dashboard. The system is live with foundation through Phase 3 built and running on Hetzner. The remaining work is the intelligence layer (knowledge compounding) and the visibility layer (dashboard) that turn the system from a daily reporter into a compounding business brain.

## Core Value

Knowledge that compounds over time. After 6 months, the system should know more about Habib Distribution's market — seasonal patterns, competitor behavior, PPC dynamics, stockout risk factors — than any competitor's AI, because every observation is captured, synthesized against real outcomes, and promoted into validated playbooks. The wiki becomes the institutional memory of the business.

## Requirements

### Validated

- ✓ Project foundation: Python asyncio, Supabase client, Mem0 client, env config, L1 rules — Phase 0
- ✓ CI/CD pipeline: GitHub Actions → SSH → Hetzner, git pull + restart services — Phase 0
- ✓ Inventory Agent: daily stockout prediction, restock recommendations → approval_requests — Phase 1
- ✓ Mem0 observations: fact extraction working, vecs.memories table populated daily — Phase 1
- ✓ Telegram Bot: daily brief, inline approval/reject buttons, critical alerts — Phase 2
- ✓ Executor Service: polls approval_requests every 60s, executes SP-API writes — Phase 3
- ✓ Sync Layer: inventory, orders, fees, listings sync jobs deployed and running — Phase 3
- ✓ Systemd services: habib-tgbot and habib-executor with auto-restart on Hetzner — Phase 3

### Active

**Knowledge Compounding Layer (Karpathy LLM Knowledge Base pattern)**
- [ ] Weekly consolidation job: observation → pattern synthesis (Claude Sonnet, Saturday 20:00 UTC)
- [ ] Monthly review job: pattern → playbook promotion with confidence validation against Supabase outcome data (Claude Opus, 1st of month)
- [ ] Wiki compiler: generate per-product, per-competitor, per-playbook markdown pages → wiki_pages table
- [ ] wiki_pages schema migration: create table if not already present
- [ ] Prediction accuracy tracking: record agent predictions with expected_date; validate outcome when date passes; store result in Supabase
- [ ] Confidence calibration logging: track whether high-confidence memories (0.8+) prove accurate at statistically higher rates over time

**Dashboard — Role-Based Operational Intelligence (Next.js on Vercel)**
- [ ] Role-based access: Rami (all), Father (finance KPIs only), Brother (sales/marketing metrics)
- [ ] Home overview: today's business health at a glance — revenue, orders, PPC spend, inventory health, pending approvals, agent status
- [ ] Wiki viewer: Karpathy-style compiled knowledge pages, browsable by product / competitor / playbook / brief; last-compiled timestamp; confidence indicators
- [ ] Approvals center: full context per request; what-if projections before approving; audit trail from recommendation → execution → outcome
- [ ] Agent ROI ledger: per-recommendation outcome tracking (did this bid change reduce ACOS? did this restock prevent a stockout? what was the revenue delta?)
- [ ] Anomaly detection feed: statistically unusual patterns surfaced with severity scoring and historical baseline comparison
- [ ] Decision audit trail: full chain — raw observation → pattern → recommendation → action → business outcome — all linkable
- [ ] Knowledge graph visualization: entity relationship map showing how products, competitors, seasons, and keywords connect across observations
- [ ] Prediction scoreboard: per-agent accuracy metrics over time (rolling 30/90 day windows)
- [ ] Seasonal intelligence calendar: forward-looking view of predicted high/low periods with confidence bands, based on historical patterns
- [ ] Knowledge age heatmap: visual indicator of which products/domains have fresh vs. stale intelligence (last observation date per entity)
- [ ] Agent health panel: reasoning quality trending over time; token spend per agent; run success rate

**PPC Agent (skip until ADS_API creds configured)**
- [ ] Campaign performance analysis: ACOS, TACoS, conversion rates, wasted spend detection (no conversions in 14+ days)
- [ ] Keyword bid recommendations → approval_requests
- [ ] Campaign budget change recommendations → approval_requests
- [ ] PPC observations written to Mem0 with campaign_ids metadata

**Competitor Intel Agent (skip until competitors table populated with ASINs)**
- [ ] Competitor price/OOS/BSR monitoring with 7-day and 30-day baseline comparison
- [ ] Pricing opportunity recommendations when competitor goes OOS or raises price → approval_requests
- [ ] Own listing health monitoring: buy box, BSR trend, review sentiment shifts
- [ ] Competitor observations written to Mem0 with competitor_asins metadata

**Hardening & Ops**
- [ ] Retry cron for failed agent runs (30 min after each scheduled slot)
- [ ] Weekly health report via Telegram: agent runs, token spend, memory count trend, pending approvals
- [ ] Arabic support for notifications (title_ar, body_ar fields in notifications table)
- [ ] Runbook documentation: "what to do if X fails" for each component

### Out of Scope

- Walmart Canada — future marketplace, add after Amazon is fully automated
- Multi-tenant / productization / managed agents — future agency expansion
- FalkorDB graph memory — deferred until entity count justifies traversal (100+ SKUs trigger)
- Mobile app — web dashboard sufficient for this operator profile
- Real-time WebSocket feeds — polling is sufficient for batch agent workload
- Custom ML models — Mem0 + Claude is the intelligence layer
- OAuth social login — email/password sufficient for 3-person team

## Context

**Running infrastructure:** Python asyncio agents on Hetzner CX22 (habib-os-prod, user `habib`, /home/habib/anabtawi-os/). Supabase project thenkkiaeuuxvuoxizjd (us-east-1). Mem0 OSS with pgvector (vecs schema, vecs.memories table, HNSW index, 1536-dim embeddings via text-embedding-3-small). Mem0 fact extraction uses gpt-4o-mini (not Claude — Mem0 ignores assistant-role messages; write_observations must use role "user"). Telegram via python-telegram-bot[job-queue]. Custom async SP-API client in sync/spapi/.

**Dashboard stack:** Next.js 14 App Router on Vercel, Tailwind CSS + shadcn/ui components.

**Three operators:** Rami handles technical and operational decisions (full access). Father handles finance (revenue, cost, margin, approval history). Brother handles sales and marketing (BSR trends, competitor intel, listing health, PPC performance). Dashboard design serves all three from a shared intelligence layer — same data, role-appropriate views.

**Knowledge compounding trajectory (Karpathy pattern):**
- Month 1: Daily observations accumulate. Raw signal.
- Month 2-3: Weekly patterns emerge. Seasonal correlations appear.
- Month 4-5: Playbooks validated against outcome data. Confidence calibrated.
- Month 6+: System knows the business better than any human. Moat established.

**Current blockers:**
- PPC agent: ADS_API_REFRESH_TOKEN, ADS_API_CLIENT_ID, ADS_API_CLIENT_SECRET not configured
- Competitor agent: competitors table is empty, needs ASINs populated
- Both: resolve independently, don't hold up knowledge compounding or dashboard

**Supabase schema notes:**
- agent_type enum: `inventory_agent`, `ppc_agent`, `competitor_agent`, `consolidation`
- wiki_pages table: may need to be created (check before compiling)
- vecs.memories: working, HNSW index confirmed

## Constraints

- **Solo operator**: Rami maintains everything — no DevOps team. Every component must be self-healing or fail with a clear Telegram alert.
- **Hetzner CX22**: 2 vCPU, 4GB RAM. Sequential agent runs (not parallel) to avoid resource contention. Upgrade to CX32 if memory pressure occurs.
- **Approval invariant**: No financial action without explicit human approval. Hard requirement — enforced at agent level, executor level, and Telegram level.
- **SP-API access**: Agents never hold SP-API write credentials. Writes go through Executor only.
- **Cost target**: $25-70/month total (infra + AI). Track token spend per agent run in agent_runs table.
- **Model allocation**: Claude Sonnet for daily agent runs and weekly consolidation; Claude Opus for monthly review only (cost control).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Knowledge compounding = Karpathy LLM Knowledge Base pattern | Proven pattern for structured knowledge accumulation from LLM outputs; makes wiki human-readable | — Pending |
| Knowledge compounding before dashboard | Inventory agent has been running; observations exist to consolidate now | — Pending |
| Dashboard research before scoping | User wants features beyond 4-page MVP; logistics/supply chain patterns inform better design | — Pending |
| Prediction accuracy tracking as first-class feature | Intelligence layer must be self-evaluating; playbooks are only valid if predictions prove accurate | — Pending |
| Skip PPC + Competitor agents until unblocked | Don't plan blocked work; add phases when ADS_API creds and competitor ASINs are available | — Pending |
| Role-based dashboard (3 views) | Rami/Father/Brother have distinct information needs; shared intelligence, role-appropriate access | — Pending |
| gpt-4o-mini for Mem0 fact extraction | Mem0's Python SDK only processes "user" role messages; gpt-4o-mini is cheaper and reliable for structured extraction | ✓ Good |
| Raw Anthropic SDK (not Agent SDK) | Simpler for structured batch jobs; no multi-step exploration needed in v1 | ✓ Good |
| Executor as separate daemon | Financial writes isolated from agent logic; approval_requests as the contract between them | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-17 after initialization*
