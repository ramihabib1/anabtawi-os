# Features Research

**Domain:** Operational intelligence dashboards + knowledge compounding systems (e-commerce / Amazon FBA, 3-role family team, AI agent context)
**Researched:** 2026-04-17
**Confidence:** HIGH — derived from user requirements, operational intelligence best practices, and logistics/supply chain dashboard patterns

---

## Feature Categories

### Table Stakes
*Must have or the system fails its core purpose — users abandon it*

**1. Business health overview (Home)**
Every operational dashboard must answer "is everything okay right now?" in one glance. For an FBA business: inventory health (days-of-supply per SKU), pending approvals count, agent status (did all agents run?), today's revenue/orders. Absence of this = operators check Seller Central instead.

**2. Approval center with full context**
The approval flow is the system's primary human touchpoint. Each pending request must show: what the agent recommended, why, what happens if approved vs. not, and when it expires. Without full context, approvals are blind — operators either rubber-stamp everything (defeating the purpose) or reject everything (blocking the system).

**3. Agent run log with success/failure status**
Operators need to know if the system worked today. A simple log (timestamp, agent, success/failure, duration) with expandable error details is table stakes. If this doesn't exist, every failure is invisible until outcomes are already bad.

**4. Notification history / alert feed**
All critical and warning alerts should be browsable, filterable by severity, product, and date. This is the paper trail for "why did this happen?" investigations.

**5. Role-based access**
Three operators (Rami: all, Father: finance, Brother: sales/marketing) with different information needs. Without this, the dashboard either overwhelms non-technical users or exposes sensitive operational data to the wrong people.

---

### Differentiators
*Competitive advantage — what makes this system compound intelligence rather than just display data*

**6. Decision audit trail (observation → outcome chain)**
The full chain: raw observation → pattern → recommendation → approval → SP-API execution → measured business outcome. Each step should be linkable. This is what makes the system self-explaining and trustworthy. When Rami asks "why did the PPC agent recommend that bid increase?", the answer should be one click away.

**Complexity:** Medium — requires linking approval_requests → audit_log → recommendation_outcomes at the data layer. UI is a timeline/chain component.

**7. Agent ROI ledger**
Per-recommendation outcome tracking. For each approved and executed recommendation, measure what actually happened. Examples:
- Inventory restock: Did the stockout get prevented? Revenue saved = velocity × days × price.
- PPC bid change: ACOS before vs. 14 days after. Revenue delta.
- Price change: Units × margin delta over measurement window.

This turns the system from a cost center into a measurable profit center. After 6 months, Rami can say "the inventory agent prevented $X in stockout losses."

**Complexity:** High — requires measurement windows, baseline capture at execution time, and validation runs. But the data model (recommendation_outcomes table) can be built incrementally.

**8. Prediction accuracy scoreboard**
Per-agent accuracy metrics over rolling 30/90-day windows. Did the inventory agent's stockout predictions happen when predicted? Were the PPC ACOS projections accurate? A calibration chart (confidence vs. actual accuracy) shows whether the system is well-calibrated.

This creates accountability for the AI — the system must earn trust, not assume it. When accuracy drops, it's a signal to retune the system prompt.

**Complexity:** Medium — requires prediction_log table (written at agent run time) and validation_runner (resolves predictions daily). UI is a simple accuracy chart.

**9. Seasonal intelligence calendar**
Forward-looking view of predicted high/low demand periods, based on accumulated patterns. Highlights upcoming events (Ramadan, Q4) with confidence bands and recommended lead times. This is the "know things before they happen" feature that makes the knowledge base feel like institutional memory.

**Complexity:** Medium — driven by playbook and pattern data already in Mem0. Requires a calendar rendering component with confidence visualization.

**10. Knowledge age heatmap**
Visual indicator showing which products/domains have fresh vs. stale intelligence. A SKU with no new observations in 14 days is a blind spot. This tells the operator which areas of the business the system knows well vs. where it's flying blind.

**Complexity:** Low — derived from `last_reinforced` field in Mem0 metadata. Simple color-coded grid.

**11. Anomaly detection feed**
Surfacing statistically unusual patterns before they become problems. Examples: velocity 2σ above baseline, competitor price drop, ACOS spike, review sentiment shift. Each anomaly should show: what's normal (baseline), what's happening now, statistical significance, and suggested action.

The key differentiator from a simple alert system: anomalies are ranked by business impact, not just statistical significance. A 3σ velocity spike on a $5 item matters less than a 1.5σ margin compression on a top-10 SKU.

**Complexity:** Medium — requires baseline calculation per metric (rolling 30-day mean/stddev) stored in Supabase. Anomaly scoring logic in Python or database functions.

**12. Knowledge graph visualization**
Entity relationship map showing how products, competitors, seasons, and keywords connect through shared observations and patterns. Example: "Baklava" → connected to "Ramadan" (3x velocity pattern) → connected to "Competitor B0XXX" (OOS during Ramadan 2025) → connected to "keyword: baklava toronto" (top converter). This makes the compound knowledge visible and navigable.

**Complexity:** High (React Flow + graph data model from Mem0 metadata co-occurrences). High value for understanding cross-domain patterns.

**13. Wiki viewer (Karpathy LLM Knowledge Base)**
Browsable, rendered knowledge pages per product, competitor, and playbook. Shows accumulated intelligence in human-readable form. Each page includes: confidence indicators (✅ High / ⚠️ Medium / ❓ Low), last-compiled timestamp, source observation count, and links to related entities.

This is the system's "institutional memory interface" — what Rami's brother and father interact with to understand the business's accumulated intelligence.

**Complexity:** Low — content already in wiki_pages table. UI is markdown rendering with a page tree.

**14. What-if approval interface**
Before approving a recommendation, show a simulation of the expected outcome. For a bid increase: "Current ACOS 28% → Projected ACOS 24% based on keyword conversion history. Estimated additional revenue: $180/month." This makes approvals informed rather than blind.

**Complexity:** Medium — projections are already in the recommendation payload from the agent. The UI just needs to surface them clearly with visual before/after comparison.

---

### Role-Specific Views

**15. Father view (Finance)**
- Revenue, COGS, gross margin per SKU and total — daily/weekly/monthly
- Approval history with financial impact summary
- Agent ROI ledger (cumulative savings/revenue attributed to AI recommendations)
- Cost of running the system (infrastructure + AI API spend)
- No operational details (no agent logs, no competitor intel, no PPC minutiae)

**16. Brother view (Sales & Marketing)**
- BSR trends per SKU with period-over-period comparison
- Competitor intel feed (price changes, OOS events, review velocity)
- PPC performance summary (ACOS, top keywords, wasted spend)
- Listing health status (buy box, reviews, suppression alerts)
- Seasonal calendar (upcoming demand events)
- No technical operations (no agent logs, no Mem0 stats, no infrastructure metrics)

---

### Anti-Features
*Deliberately NOT building these — they create complexity without value or actively harm the system*

**17. Real-time WebSocket feeds**
The business data is batch-updated (agents run at scheduled times). Real-time feeds create infrastructure complexity for no operational benefit. Polling every 30-60s is sufficient. **Anti-pattern: the "live dashboard" illusion on batch data.**

**18. Custom ML models for anomaly detection**
The system already has Claude for reasoning and Supabase for querying. Building custom anomaly detection models (isolation forest, ARIMA forecasting) is overkill for 30 SKUs and adds maintenance burden. Use statistical baselines (rolling mean + stddev) — they're interpretable and sufficient. **Anti-pattern: over-engineering what can be solved with simple statistics.**

**19. Editable wiki pages**
The wiki is generated from Mem0 — it's the output of accumulated knowledge. Making it editable breaks the single source of truth. If Rami wants to correct something, the correction should go into Mem0 as an observation, not into the wiki directly. **Anti-pattern: human edits that get overwritten on next compilation.**

**20. Push notification overload**
Every dashboard observation, pattern update, and wiki compile does NOT need to generate a Telegram message. Only critical/warning severity notifications justify an interrupt. Information overload causes operators to mute the bot entirely — the most dangerous failure mode for this system. **Anti-pattern: notification spam that trains operators to ignore alerts.**

**21. Complex user management / RBAC**
Three users with three static roles. Do not build a roles/permissions admin UI. Hard-code the three role mappings in the database and config. **Anti-pattern: building for hypothetical scale with 3 actual users.**

**22. Vanity metrics on the home page**
"Total memories stored: 847" is not an actionable business metric. The home page should show actionable operational status, not system self-statistics. Memory counts, embedding dimensions, and consolidation job runtimes belong in the agent health panel, not the home overview. **Anti-pattern: LLM system metrics substituting for business metrics.**

---

## Feature Priority Matrix

| Feature | Role | Phase | Business Impact | Build Complexity |
|---------|------|-------|----------------|-----------------|
| Business health overview | All | Dashboard | High | Low |
| Approval center | All | Dashboard | Critical | Medium |
| Agent run log | Rami | Dashboard | High | Low |
| Wiki viewer | All | Dashboard | High | Low |
| Role-based views | All | Dashboard | High | Medium |
| Decision audit trail | Rami | Dashboard | High | Medium |
| Agent ROI ledger | All | Dashboard + KCL | High | High |
| Prediction scoreboard | Rami | KCL then Dashboard | Medium | Medium |
| Seasonal calendar | Brother | Dashboard | Medium | Low |
| Knowledge age heatmap | Rami | Dashboard | Medium | Low |
| Anomaly detection feed | All | Dashboard | High | Medium |
| Knowledge graph viz | Rami | Dashboard v2 | Medium | High |
| What-if approvals | All | Dashboard | High | Medium |
| Father finance view | Father | Dashboard | High | Low |
| Brother sales view | Brother | Dashboard | High | Low |

*KCL = Knowledge Compounding Layer (must be built first)*

---

## Dependencies Between Features

- **ROI ledger requires**: recommendation_outcomes table (Architecture phase) + Executor extended to write outcomes
- **Prediction scoreboard requires**: prediction_log table + inventory_agent extended to write predictions + validation_runner job
- **Wiki viewer requires**: wiki_compiler producing wiki_pages rows (knowledge compounding layer)
- **Anomaly detection requires**: baseline statistics computed per metric (can be a Supabase scheduled function)
- **Knowledge graph requires**: materialized view over vecs.memories metadata co-occurrences (Architecture phase)
- **Decision audit trail requires**: approval_requests + audit_log + recommendation_outcomes all linked by IDs

---
*Features defined: 2026-04-17*
