# Customer, Health/Compliance, and Runtime Research — Habib Distribution OS

> Research date: 2026-09-02. Status legend: **VERIFIED** = confirmed against a primary/official source fetched during research; **REPORTED** = from a secondary source (vendor page, blog, forum) not independently confirmed; **UNKNOWN** = could not be confirmed. Note: `developer-docs.amazon.com`, `sellercentral.amazon.com`, and several SP-API doc mirrors were blocked by network egress this session — all SP-API/Amazon-policy claims below are therefore REPORTED (secondary-source-derived), not VERIFIED against Amazon's own docs, and should be re-checked before an agent acts on them. `code.claude.com` and `platform.claude.com` were fetchable directly, so Area C's Anthropic-platform claims include genuine VERIFIED entries.

---

## AREA A — Customer & Reputation

### A1. Review/feedback monitoring tools — API access and pricing

No vendor in this set publishes a documented, agent-consumable REST API or webhook (REPORTED, no developer-docs page surfaced for any). Delivery is email/Slack/dashboard, built for humans.

| Tool | What it does | Agent interface | Pricing (2026, REPORTED) |
|---|---|---|---|
| **FeedbackWhiz** (Threecolts) | 27+ conditions monitored (hijackers, suppressions, Buy Box, reviews); alerts via dashboard/email/**Slack** | No public API; Slack webhook is the closest machine-readable channel | ~$25+/mo, tiered by email volume |
| **Sellerise** | Finance, alerts (39+ types), reviews, keywords, PPC | No public API | $19.99–$599.99/mo across 6 tiers, custom Agency tier |
| **Helium 10 Alerts** | Listing/inventory/review/Buy-Box monitoring | No public API for Alerts | Post-Apr-2026 repricing: Platinum $129/mo (5 ASINs, lifetime cap), Diamond $359/mo (200 ASINs); Starter discontinued |
| **Jungle Scout Review Automation** | Automates review-request emails (Solicitations-API wrapper) | No public API | Bundled in Basic ($45/mo) through Professional |
| **SageMailer** | Buyer messaging + review requests/monitoring | No public API | Basic $10/mo (unlimited ASIN monitoring); $25/mo for 2,000 emails |
| **FeedbackFive** (eComEngine) | Review-request automation, monitoring | UNKNOWN — an apitracker.io listing implies some developer surface but the page was unreachable this session | $24–$199/mo by order volume + $4/mo ASIN add-on |
| **AMZAlert** | Rule-based review alerting → SMS/email | No public API; push-only to humans | UNKNOWN (not found) |

**Implication:** don't build agent integration on any of these. Pull review/rating-change signal from first-party Supabase data already synced (`product_snapshots`) plus SP-API's `PRICING_HEALTH` notification (see B5); keep a cheap tool (SageMailer/FeedbackFive, $10–25/mo) only for the review-*request* half, which legitimately rides the Solicitations API (A2).

### A2. Buyer messaging: SP-API Messaging and Solicitations APIs

All REPORTED (primary docs blocked; reconstructed from GitHub SP-API model discussions and SDK-wrapper summaries — re-verify before sending anything to a real buyer).

**Messaging API v1** — order-tied, single-buyer messages. Allowed types: non-critical negative-feedback-removal requests (only *after* the issue is actually resolved), pre-shipment order questions, delivery-arrangement messages, and legally-required disclosures (the one "critical message" exception). Amazon gates this by automated content scanning/message-type matching plus order-status, seller-type, and per-order message-count restrictions.

**Solicitations API v1** — narrower: one templated action per order requesting both a product review and seller feedback in a single email (Amazon's fixed template — no custom copy). Buyers can't reply; it never appears in Message Center. This is exactly what SageMailer/FeedbackFive/Jungle Scout/FeedbackWhiz wrap (`solicitations.postRequest`), fired a few days post-delivery, subject to per-order eligibility windows.

**Manage Your Customer Engagement (MYCE)** — a separate, Brand-Registry-gated marketing feature, largely Seller-Central-UI with no confirmed public SP-API surface (UNKNOWN).

**Hard limits an agent must never cross** (REPORTED — verify against Amazon's "Prohibited Seller Activities" policy before implementation): never solicit reviews outside the Solicitations template; never offer compensation/discounts/replacements for a review or to change/remove one; never request negative-feedback removal before the issue is resolved; never use Messaging API for marketing content. Because agents here never hold SP-API write credentials, any buyer-facing message should be gated the same way as a price change — recommend adding `action_type: "buyer_message"` / `"review_solicitation"` to `approval_requests`, since a messaging-policy suspension is existential for a solo-operator brand.

### A3. Returns data — quality feedback loop to the manufacturer

**Report:** `GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA` (REPORTED, from report-type-values docs summarized by secondary sources) — one row per returned unit, updated daily: `return-date`, `order-id`, `sku`, `asin`, `fnsku`, `quantity`, `fulfillment-center-id`, `detailed-disposition` (SELLABLE/DEFECTIVE/CUSTOMER_DAMAGED/CARRIER_DAMAGED/WAREHOUSE_DAMAGED), `reason`, `customer-comments` (field names approximate — verify against the live schema).

**Return reason codes** (REPORTED): `NO_REASON_GIVEN`, `ORDERED_WRONG_ITEM`, `FOUND_BETTER_PRICE`, `QUALITY_UNACCEPTABLE`, `NOT_COMPATIBLE`, `DAMAGED_BY_FC`, `DAMAGED_BY_CARRIER`, `MISSED_ESTIMATED_DELIVERY`, `MISSING_PARTS`, `SWITCHEROO`, `DEFECTIVE`, `EXTRA_ITEM`, `UNWANTED_ITEM`, plus irrelevant jewelry/warranty codes. The `listReturnReasonCodes` endpoint returns the current canonical list programmatically.

**Quality loop for Habib:** `QUALITY_UNACCEPTABLE`/`DEFECTIVE` trending up on a SKU is a supplier-quality signal, not just a listing problem. Recommend a nightly `returns_daily` sync job aggregated by `product_id` + `reason`, joined against `supplier_shipments`/`supplier_shipment_items` (already in schema) to correlate a bad-return spike with a specific PO/lot, feeding a notification + wiki-page entry when the rate crosses a rolling-30-day threshold.

### A4. Amazon Vine — 2026 rules

**Eligibility (REPORTED):** Professional Selling Plan + Brand Registry + FBA + under 30 reviews on the parent ASIN; individual/FBM sellers are ineligible. Cap: 30 units per parent product.

**Cost (REPORTED, US):** legacy tiers $0 (≤2 units) / $75 (3–10) / $200 (11–30); Amazon reportedly moved to **$0 enrollment fee for products under $100 starting March 2026** — a real 2026 change worth flagging given Habib's low ASPs. No charge until the first review publishes; nothing owed if no review posts within 90 days.

**Review policy (hard constraints):** reviewers have no obligation to review; Amazon does not pre-screen or filter Vine reviews (negative ones are not removed for being unfavorable); sellers cannot pick reviewers or offer any incentive beyond the free unit. Giveaway units, FBA fees, and storage are sunk regardless of outcome — model Vine as an inventory-allocation decision. Because it carries real financial cost and irreversible reputational exposure, gate enrollment through `approval_requests` (`action_type: "vine_enrollment"`).

---

## AREA B — Account Health & Compliance

### B5. Account Health Rating, notifications, IP complaints

**Account Health Rating (AHR)** (REPORTED across multiple 2026 seller-service blogs; primary Seller Central page blocked): 0–1000 score, near-real-time, baseline 200; violations subtract, resolution/appeal adds back. Thresholds: ≥200 healthy, 100–199 at-risk, ≤99 deactivation-eligible. **Account Health Assurance (AHA)** unlocks after ≥250 sustained for 6 months and inserts a mandatory advance-notice window (REPORTED ~72 hours) before deactivation, rather than deactivating first. Response paths: formal appeal, a Plan of Action (Amazon wants the systemic fix, not an apology), or direct acknowledgment with evidence of resolution. **No confirmed SP-API field reads the AHR score itself — UNKNOWN**; treat AHR as human-checked only.

**SP-API Notifications API** (push subscription, REPORTED): `ACCOUNT_STATUS_CHANGED` fires on any `NORMAL`/`AT_RISK`/`DEACTIVATED` transition — the one directly automatable account-health signal; wire it to an always-on critical Telegram alert. `PRICING_HEALTH` fires when an offer loses Featured-Offer eligibility on price — useful for the Competitor Intel agent and a legitimate free substitute for what Helium 10 Alerts/FeedbackWhiz sell on Buy Box. The full notification-type catalog wasn't enumerated this session; pull it directly once egress access is available.

**IP complaints** (REPORTED, seller-law-firm 2026 guides): three buckets — suspected violations (Amazon's own detection), received complaints (rights holder files), and authenticity complaints (buyer-flagged). Food-brand-relevant triggers: trademark misuse in copy/keywords, unauthorized packaging/photo use, occasionally packaging-design patent conflicts. **Detection is automatable** (watch the notification/violation feed, alert immediately); **response is not** — a POA or IP-complaint reply is legally consequential and must stay human-authored, never auto-submitted. Recommend: any suppression/IP-complaint/status-change notification triggers an immediate critical alert plus an agent-drafted POA for human review — submission itself stays manual, extending the existing "no action without approval" invariant to account-health actions.

### B6. Tax — Canadian seller, Amazon CA/US, US federal exposure

**GST/HST on Amazon.ca** (REPORTED, CRA rules effective July 1, 2021; CRA's own page not fetched this session): if a seller is **not** GST/HST-registered, Amazon must calculate/collect/remit GST/HST on their behalf for domestic sales. Once registered (e.g., past the CA$30,000 threshold), that obligation reverts to the seller — they charge/collect/remit directly and Amazon stops collecting for them. Habib, as an established Canadian operator, is almost certainly past $30K and should confirm its GST/HST number is correctly on file in Seller Central rather than silently relying on facilitator collection.

**US sales tax** (REPORTED): Amazon is marketplace facilitator in all ~45 US sales-tax states (5 states have none), collecting/remitting automatically on marketplace transactions — no seller registration needed for that coverage. **What isn't covered:** any future direct-to-consumer sales outside the marketplace, and — the big gap — **income/franchise tax**, a separate tax untouched by facilitator laws; ~40 states with corporate income/franchise tax can still assert nexus purely from FBA inventory sitting in their fulfillment centers, independent of the (well-covered) sales-tax question.

**US federal income tax / permanent establishment** (REPORTED, expat/cross-border tax advisory sources): under Canada–US treaty independent-agent principles, storing inventory via FBA (an independent third party serving many unrelated sellers) generally does **not** by itself create a US permanent establishment. This is fact-specific, not a blanket exemption — a non-US corporation with US-source income should still weigh a **protective Form 1120-F** filing (preserves deduction rights, starts the statute of limitations) and disclose any treaty position via **Form 8833**. **Form W-8BEN-E** certifies foreign status/treaty benefits to withholding agents but doesn't resolve the 1120-F question and can't shelter income actually attributable to a real PE. Net: low-but-not-zero federal exposure for an FBA-only presence — a determination for a cross-border tax professional, not this research pass.

| Tool/Service | Role | Notes (REPORTED) |
|---|---|---|
| **TaxJar** | US sales-tax automation, nexus monitoring | From ~$19/mo; addresses the *non-marketplace* gap and nexus tracking, not marketplace sales tax (already Amazon's job) |
| **Avalara** | Broader compliance suite incl. cross-border/customs | 1,200+ integrations; stronger fit if Habib ever ships DTC cross-border |
| **Cross-border accountants** (e.g., SAL Accounting, Insight Accounting CPA, Toronto) | GST/HST correctness, 1120-F decision, treaty position | Engage before the January 2027 US launch to settle 1120-F in advance |

**Primary sources to verify directly:** CRA GST/HST digital-economy guidance, IRS Instructions for W-8BEN-E and Form 1120-F, IRS Pub. 515, Amazon Seller Central's tax/marketplace-collection help pages — none fetched this session; all B6 claims are REPORTED.

---

## AREA C — Runtime and Multi-Agent Coordination on Claude

### C7. Claude Code on the web — cloud sessions, Routines, MCP, phone, Max limits

**VERIFIED** (`code.claude.com/docs/en/routines`, `.../claude-code-on-the-web`, fetched directly). Cloud sessions run on Anthropic-managed (or self-hosted) infrastructure, persist across browser closes, and are monitorable/steerable from the Claude mobile app — there's no separate push API, but this covers the "phone notification" need in practice.

**Routines** (research preview): a saved prompt + repos + connectors with one or more triggers — **Scheduled** (presets, or custom cron via `/schedule update`, 1-hour minimum interval, or one-off), **API** (per-routine bearer-token endpoint; fired `text` arrives wrapped as untrusted `<routine-fire-payload>`, not live instructions), **GitHub event** (PR/release, field-filtered). Routines run as **full autonomous sessions with no permission prompts** — meaning a Routine must never also hold SP-API write credentials, consistent with this system's write-credential-free-agent design. All connected MCP connectors are included by default (should be pruned per-routine). Available on Pro/Max/Team/Enterprise; draws normal subscription usage plus a separate daily run-start cap (one-offs exempt); GitHub-trigger events are additionally hourly-capped in preview. **Claude Max (REPORTED, 2026):** 5x at $100/mo, 20x at $200/mo, both on the standard 5-hour/weekly usage model, not metered.

**Fit:** a plausible complement to (not replacement for) the Hetzner cron + Python stack — best suited to read-only ops automation (e.g., a nightly Routine reading `agent_runs`/`sync_log` via an MCP Postgres connector to replace `scripts/health_check.py`) rather than the core agent/executor loop, given the preview status and no-approval-prompt execution model.

### C8. Claude Cowork scheduled tasks

REPORTED (Anthropic support article, not fetched directly). `/schedule` lets a user describe a recurring task once; it runs server-side (even offline) on any paid plan, using Cowork's connectors/plugins/skills. This is a knowledge-work automation surface (Slack/Drive/email), not an infrastructure runtime — a good fit for human-facing digests (e.g., a Monday summary of `wiki_pages` updates) at the Interface Layer, not for the Agent Layer's Supabase-writing, approval-gated work.

### C9. Claude Managed Agents — deployments, memory, vaults, multiagent, pricing

**VERIFIED** (`platform.claude.com/docs/en/managed-agents/overview` and `.../multiagent-orchestration`, fetched directly); pricing/webhooks/memory detail below is REPORTED.

A managed agent harness (Bash, file ops, web search/fetch, MCP) as an alternative to hand-rolling an agent loop; **beta**, `managed-agents-2026-04-01` header. **Scheduled deployments** are the platform-native cron analog. **Vaults** expose credentials as runtime env vars and are session-scoped (one `vault_ids` list supplies every thread in a multiagent session; per-agent MCP-server declarations control actual access). **Memory stores** are cross-session, file-based (inspectable/exportable, unlike opaque vector rows) — architecturally simpler than but weaker on semantic search than the Mem0/pgvector design here; **Dreaming** (research preview) auto-curates memory between sessions, a platform-native analog to this system's own weekly/monthly consolidation jobs.

**Multiagent orchestration (VERIFIED, full page):** one coordinator declares a `multiagent.agents` roster of **up to 20 unique agents** (can spawn multiple copies of any); delegation is **one level only** — a roster member with its own roster is rejected. All agents share a sandbox/filesystem but run in isolated, **persistent** session threads (a coordinator can follow up later and the agent remembers). **Max 25 concurrent threads**; agents communicate via typed `agent.thread_message_sent`/`received` events, not free text — a clean request/response handoff primitive. **Session budgets** are a shared cost cap across all threads, pausing them independently as it's approached. An **advisor** roster entry (max one) lets the primary thread consult a stronger model mid-turn for a single opinion, cheaper than a full second thread. MCP servers are agent-scoped; vault credentials are session-scoped.

**Pricing (REPORTED):** standard Claude token rates plus **$0.08/active session-hour**; idle time free.

**Fit:** the multiagent primitives (typed handoffs, shared filesystem, session budgets, roster, advisor) map closely onto the CLAUDE.md §16.1 "Compiler Agent" — a future trigger, not a Phase 0–5 change. When that trigger is hit, this is the most credible upgrade path over bespoke orchestration.

### C10. Claude Agent SDK / Claude Code subagents — context passing

REPORTED (docs not fetched directly this session). A subagent runs in a **fresh, isolated context**: no inherited conversation history, system prompt, or skills unless explicitly listed; only its **final message** returns to the parent — a much tighter, single-shot boundary than Managed Agents' persistent threads. Defined via `.claude/agents/*.md` (YAML frontmatter) or the SDK's `agents` parameter, invoked through the built-in Task/Agent tool. Optimized for **context economy and parallelism** (a research subagent can read fifty files without bloating the parent; independent subagents run concurrently). Contrast with Managed Agents: subagents are stateless-to-parent, call-and-forget; Managed Agents threads are addressable and remember prior turns. For a future Compiler Agent, subagents suit one-off research fan-out; Managed Agents threads suit a standing specialist you can keep questioning across a session.

### C11. Multi-agent communication patterns — when to talk vs. share state

Anthropic's own guidance (REPORTED — the "when to use multi-agent systems" blog was egress-blocked; summarized via search excerpts and the directly-fetched Managed Agents doc, which cites it). **"Building Effective Agents"** distinguishes predefined-code-path **workflows** from self-directing **agents**, catalogs five workflow patterns (prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer), and recommends starting with the simplest workflow that solves the problem — directly consistent with this system's own choice to keep agents as direct-SDK batch jobs today. The **multi-agent research system** post describes a production orchestrator-workers deployment (lead agent → 3–5 parallel subagents → synthesis → citation pass) that reportedly beat single-agent Opus 4 by ~90% on breadth-first research, at a real token-cost premium — justified specifically for parallelizable, exploratory work, not tightly-coupled or shared-evolving-state tasks.

**Concrete recommendation for this architecture:**

| Situation | Pattern | Why |
|---|---|---|
| Three daily domain agents (Inventory, PPC, Competitor) | **Share state via Supabase**, no messaging (current design) | Independent tasks, no live interdependency — no orchestration overhead justified |
| Future Compiler/Synthesis Agent over the three agents' output | **Coordinator-worker, typed handoffs** (Managed Agents roster or subagent fan-out) | Textbook orchestrator-workers case; CLAUDE.md §16.1 already names this trigger |
| Weekly/monthly knowledge consolidation | **Blackboard via Mem0 + `wiki_pages`** (current design) | Asynchronous read/write to a shared durable store, not a live conversation — also keeps it human-auditable |
| Second opinion on a high-stakes recommendation | **Advisor pattern** or a lightweight second Claude call | Cheaper than a full coordinator-worker session for a single spot-check |
| Real-time external triggers (SP-API notification, GitHub event) | **Event-driven trigger → single-purpose session** | Maps directly to Routines' API/GitHub triggers and Managed Agents scheduled deployments |

**Framework landscape (REPORTED, general 2026 comparisons):** LangGraph (explicit graph/state-machine, adopted the cross-vendor Agent Protocol), CrewAI (role-based crews, output-mediated delegation, fastest to prototype), AutoGen (conversational GroupChat), OpenAI Agents SDK (explicit handoffs, lowest-latency but model-locked) each sit at different points on the talk-vs-share-state spectrum. Google's A2A protocol (2025, 50+ partners, CrewAI support) is the leading cross-vendor interoperability standard — not a near-term need for a single-operator, single-vendor stack, but relevant if a future Walmart-side or acquired vendor's agent needs to interoperate.

---

## Recommended: Customer Stack

1. **Skip third-party review/alert tools as agent-integration dependencies** — none expose a real API. Build the signal from Supabase `product_snapshots` plus SP-API's `PRICING_HEALTH` notification instead.
2. **Use the Solicitations API** (directly, or via the cheapest wrapper, ~$10–25/mo) for review requests; never the Messaging API for anything marketing-flavored. Add `action_type: "buyer_message"`/`"review_solicitation"` to `approval_requests` — a messaging-policy suspension is existential for a solo operator.
3. **Build a `returns_daily` sync job** on the FBA Customer Returns report, joined to `supplier_shipments`, to turn returns into a supplier-quality feedback loop (a natural Phase 6 knowledge-compounding addition).
4. **Gate Vine enrollment through `approval_requests`** (`action_type: "vine_enrollment"`) and model it as an inventory-allocation decision — the March 2026 fee change makes it newly cheap for Habib's low-ASP SKUs, which raises the temptation to skip the review step.

## Recommended: Compliance Stack

1. **Subscribe to SP-API's `ACCOUNT_STATUS_CHANGED`** as an always-on critical alert — the one automatable account-health signal available; AHR itself has no confirmed API and needs periodic manual checks.
2. **Never let an agent submit an appeal, POA, or IP-complaint response** — detection is automatable, response is human-only, mirroring the existing approval invariant.
3. **Confirm the GST/HST number is correctly on file in Seller Central now** — Habib is almost certainly past the $30K threshold and should be self-remitting, not relying on facilitator collection.
4. **Engage a cross-border accountant before the January 2027 US launch** specifically to settle the Form 1120-F protective-filing decision, and layer TaxJar/Avalara only for the non-marketplace/nexus-tracking gap Amazon's facilitator status doesn't cover.

## Recommended: Runtime and Coordination Design

1. **Keep Phase 0–5 as specified**: direct Anthropic SDK, independent agents, Supabase as the only shared state, no agent-to-agent messaging — this is what Anthropic's own guidance recommends for non-interdependent tasks, not just the simplest option.
2. **When the Phase 6+ Compiler Agent trigger is actually hit, reach for Managed Agents' coordinator/roster pattern first**: one coordinator, three domain agents as roster members, typed thread-message handoffs, a session budget cap, and an advisor entry for high-stakes second opinions — at $0.08/session-hour plus standard token rates.
3. **Consider Claude Code Routines for read-only ops/monitoring** (health reports, SP-API-notification-triggered triage) — not for anything touching SP-API writes or buyer messaging, since Routines run with no approval prompts. Keep Cowork scheduled tasks at the human-facing digest layer only.
4. **Don't adopt LangGraph/CrewAI/AutoGen/OpenAI Agents SDK or A2A now** — no near-term multi-vendor interoperability need exists for this single-operator, single-vendor stack; Anthropic's own subagents (one-off fan-out) and Managed Agents multiagent (persistent coordinator-worker) already cover both ends of the spectrum this system needs.
