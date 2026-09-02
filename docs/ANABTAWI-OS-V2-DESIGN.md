# Anabtawi Operating System — Design v2

> September 2, 2026. Owner: Rami Anabtawi. Status: proposed, awaiting decisions in section 10.
> Rendered version: https://claude.ai/code/artifact/4fe472f2-0d31-4de8-ad19-da068f8be074

A company of AI departments that runs the e-commerce business every day, with Rami as CEO and final judge. Nothing to host, nothing to babysit. The system lives where the work already happens: Claude sessions with live Amazon data.

## 1. Why v1 failed, and the one rule for v2

Version 1 was a software project: Python daemons on Hetzner, a custom sync layer, Mem0, a Telegram bot, a dashboard roadmap. It produced infrastructure, not decisions, and it was never used. The loop that actually ran the business was: Rami, a Claude session, and live account data through an MCP (DataDoe).

Version 2 takes that working loop and gives it structure, a schedule, memory, and authority to act. It adds zero servers.

**The rule:** every component is either a hosted tool we buy, or a plain text file in a git repo. If it needs deploying, restarting, or debugging at 2am, it does not belong.

Ideas that survive from v1: humans approve money; business rules live in one constitution file; knowledge compounds from observations into playbooks. Everything else is retired.

## 2. The company

| Role | Kind | Mandate | Tools | Start tier |
|---|---|---|---|---|
| CEO | Rami | Targets, money, quality. 20 min/day on the brief, 90 min Monday review. | — | — |
| Chief of Staff | agent, coordinator | Morning brief, decision queue, alert routing, weekly business review, wiki and playbooks, audits departments | repo, all read tools | — |
| Finance & Planning | agent | P&L per SKU per marketplace, cash flow, unit economics, PO budgets, FX, settlement reconciliation, reimbursements | Sellerboard, SP-API | T2 |
| Supply Chain | agent | Demand forecast, PO proposals, supplier emails, FBA inbound plans, IPI/capacity, aged and stranded stock, expiry | SP-API, Gmail | T2 |
| Advertising | agent | SP/SB/SD: harvesting, negatives, bids, budgets, structure, deals, coupons, Subscribe & Save | Amazon Ads MCP | T1 within limits |
| Catalog & Brand | agent | Listing quality, SEO, A+, image briefs, variations, catalog errors, compliance attributes, US/Walmart localisation, launch pages | SP-API, Helium 10 | T2 |
| Pricing & Market Intel | agent | Buy Box, competitor price/stock moves, price tests, cross-market parity, category trends | Keepa, SP-API, web | T2 |
| Customer & Reputation | agent | Reviews, buyer messages, returns analysis, Vine, quality loop to manufacturer | SP-API | T1 replies |
| Account Health & Compliance | agent | Account health, policy notices, IP complaints, food regulatory (CFIA, FDA, FSVP), GST/HST, US sales tax, BSA Agent Policy | SP-API, web | T0 |
| Expansion & BizDev | agent | US launch program, Walmart activation, catalog activation from the 50–60 brand SKUs, manufacturer evaluation, brand onboarding | all | T3 |

Activation order: Chief of Staff, Advertising, Supply Chain, Finance, Catalog, Pricing, Customer, Account Health, Expansion.

## 3. Authority tiers and the trust ratchet

Amazon's Business Solutions Agreement update (effective March 4, 2026) added an Agent Policy: official APIs only, agents identify as automated, audit logs, human authorization checkpoints, stop on request. The tiers comply by construction.

- **Tier 0, observe and report.** Reads only. Every department's first week.
- **Tier 1, act inside guardrails, logged.** Reversible bounded actions without asking: bids ±15%, negatives, budgets ±20% up to a daily cap, pause keyword with 0 orders after 30 clicks, template buyer replies. Every action in the ledger and next brief.
- **Tier 2, propose, Rami approves.** Price changes, POs, new campaigns, listing changes, FBA shipments, coupons/deals, reimbursement claims. Numbered list in the brief; Rami replies "approve 1 and 3, reject 2, hold 4".
- **Tier 3, Rami only.** New marketplaces, brand/supplier contracts, payment terms, spend above the monthly PO ceiling, legal/regulatory.

**Ratchet:** an action class moves T2→T1 after 30 days, ≥20 approvals, <5% rejections. Chief of Staff proposes, Rami confirms. Any class demotes by editing one line in the constitution. Kill switch: revoke the credential in the vault. Money never moves on Tier 1.

## 4. Operating calendar (Asia/Jerusalem; Amazon day closes 07:00 local)

### Daily
| Time | Dept | Task | Output | Tier |
|---|---|---|---|---|
| 06:30 | Account Health | Health rating, notifications, suppressed/stranded listings, policy messages, expiring docs | Alerts to brief | T0 |
| 06:30 | Supply Chain | Days of cover per SKU/market, inbound status, receiving discrepancies, stranded | Stockout risks, shipment actions | T2 |
| 06:40 | Advertising | Search-term harvesting, negatives, bid hygiene, budget pacing, spend anomalies vs 7d | Ledger actions, exceptions | T1 |
| 06:40 | Pricing & Intel | Buy Box, competitor price/stock changes >5%, price vs market | Price proposals | T2 |
| 06:45 | Customer | New reviews (flag ≤3★), messages within 24h, return reasons, A-to-z | Replies, quality flags | T1 |
| 07:00 | Chief of Staff | Brief: revenue, units, ad spend, ACOS, TACoS, margin; exceptions; decision queue; today's tasks | Brief to phone + repo | — |
| — | Rami | Read brief, answer queue in one message | Approvals executed | — |

### Weekly (Monday)
- Finance: weekly P&L per SKU/market, contribution after ads, cash position, 8-week cash forecast, reimbursements.
- Supply Chain: 12-week forecast refresh, reorder points, PO proposals with landed cost and cash need.
- Advertising: scale winners, cut losers, restructure, keyword ranks, 4-week deals calendar.
- Catalog: audit 3 SKUs on rotation; one listing experiment.
- Pricing & Intel: competitor report, category trend, new entrants, test results.
- Customer: sentiment themes, return rate by SKU, quality memo to manufacturer.
- Chief of Staff: WBR pack, scorecard vs targets, task board, playbook diffs. 90-minute review with Rami.

### Monthly (1st business day)
Finance close and pricing review; supplier scorecards and landed-cost updates; expansion pipeline and gate checks; tier promotions/demotions, wiki pruning, OKR check.

### Quarterly
Strategy and targets; seasonal plan (Ramadan 2027 starts ~Feb 8, so Q4 2026 is the Ramadan plan); brand onboarding and supplier negotiations.

### Event-driven (hourly checks)
Cover <14 days, Buy Box lost, listing suppressed, 1–2★ review, health drop, competitor OOS on matched ASIN, ad spend >2× 7d average by noon, inbound delayed, policy notice.

## 5. Architecture

| Layer | Choice |
|---|---|
| Runtime (Anthropic-hosted) | **Claude Code on the web + Routines** as v1: the company repo is the project; each department is a scheduled Routine starting a fresh cloud session with repo + MCP connectors; runs on Claude Max. **Managed Agents** as graduation path when a department needs isolation, hard per-run dollar budgets, credential vaults, or a persistent memory store; same repo and skills. |
| Tools (MCP) | Amazon Ads MCP (official, open beta Feb 2026) for all ads reads/writes. DataDoe for Seller/Vendor/Ads reads. A vetted SP-API MCP with write tools for listings, prices, inventory, shipments (credential in a vault). Walmart Marketplace MCP when Walmart activates. Gmail for supplier/freight drafts. Web search/fetch for intel. Nothing custom. |
| Data (bought) | Sellerboard = profit truth per SKU. Helium 10 = keywords and rank tracking. Keepa = competitor price/Buy Box history via API. Amazon via MCP = live orders, inventory, account state. No warehouse. Weekly KPI snapshots appended to a CSV in the repo. |
| Knowledge (git repo) | Constitution, charters, playbooks, SKU dossiers, supplier files, market files, decision ledger, every brief, all as markdown. Agents read before acting, write after. Git history is the audit log. |
| Interface | Morning brief pushed to phone and saved to repo. Approvals are a reply in a Claude session. Deep work in the same session. No dashboard until asked for twice. |

Compliance by construction: official APIs only via MCP, no browser automation; every write in the ledger with department, reasoning, tier, approval ref; T2/T3 are human checkpoints; one credential revocation stops everything.

Not built: Python daemons, sync layer, vector DB, Telegram bot, dashboard, VPS cron.

## 6. The company repo (`anabtawi-company`)

```
anabtawi-company/
├── COMPANY.md                 # constitution: mission, targets, org chart, tiers, guardrails, kill switch
├── departments/<dept>/CHARTER.md, memory.md, playbooks/
├── products/<SKU>.md          # unit economics, keywords, competitors, history, decisions
├── markets/ ca.md us.md walmart-ca.md
├── suppliers/<manufacturer>.md
├── playbooks/ us-launch.md ramadan-stocking.md q4-holiday.md new-brand-onboarding.md
├── ledger/ actions.jsonl decisions.md kpis.csv
├── briefs/ YYYY-MM-DD.md
├── routines/                  # the schedule as text
└── .claude/skills/            # kpi-pull, listing-audit, ppc-hygiene, po-proposal, brief-compile
```

Compounding: daily briefs record; Monday review turns lessons into diffs on memory and playbooks; monthly review prunes. Every playbook fact links to the brief or ledger entry that produced it.

## 7. Growth program

Seven figures is $85k/month. Planning hypotheses (Finance revises monthly):
- Today: $8–10k/mo, Amazon CA, 10–15 winning SKUs.
- Canada disciplined: $20k/mo by March 2027, plus 10 activated SKUs.
- US year one: $40–60k/mo (US ≈ 10× Canada).
- Walmart + second brand: $15–25k/mo.

**Track A, Canada as proving ground (now–December):** top-15 listings to standard; PPC rebuilt into launch/ranking/defence per hero SKU; never stock out on a hero (6-week seasonal buffer); activate 10 dormant brand SKUs, kill misses after 60 days; 30 consecutive briefs read and a first ratchet promotion.

**Track B, US launch for Ramadan 2027 (date-driven):** Ramadan ~Feb 8, 2027 → stock in US FBA by mid-January → freight/customs 4–8 weeks → US POs in November → compliance and setup due September–October. Regulatory: FDA facility registration, FSVP importer, prior notice, US nutrition label, allergens, origin (broker confirms). Account: NA unified, US Brand Registry, tax interview, nexus plan. Catalog: localise top 10, US A+, landed-cost pricing. Launch: Vine, launch PPC, 30-day coupon, Subscribe & Save. Logistics: 3PL vs direct-to-FBA, HTS codes, duties in landed cost.

**Track C, Walmart on the same pipeline (Q1 2027):** 10 hero SKUs, WFS where eligible, Walmart Connect only after organic conversion proven.

**Track D, second brand (Q2 2027):** new supplier file, new dossiers, same departments and calendar; playbook written from A and B.

## 8. 30-day build

| Week | Goal | Exit |
|---|---|---|
| Sep 3–9 | Repo, COMPANY.md, connectors (DataDoe, Ads MCP, Sellerboard, Helium 10, Keepa), top-15 dossiers, first brief by hand | A brief Rami would read daily, with a decision queue |
| Sep 10–16 | Daily routines + Monday review scheduled; Advertising and Supply Chain at T0; ledger starts | 7 consecutive automated briefs, first review pack |
| Sep 17–23 | Advertising to T1 hygiene; Catalog audits; first weekly P&L; first PO proposals; US compliance checklist | First approved and executed T2 actions |
| Sep 24–30 | Expansion writes dated US plan + Walmart checklist; September close; first ratchet proposals; Managed Agents graduation decision | Company running on the calendar; US plan with owners and dates |

## 9. Cost (monthly)

Claude Max $200 (paid) · Claude API $0–300 only if departments graduate · Sellerboard $19–39 · Helium 10 $99–229 · Keepa ~$20 · DataDoe / write MCP TBD. Total ≈ $350–800.

## 10. Decisions needed from Rami

1. Runtime: Routines first, Managed Agents on graduation (recommended) vs Managed Agents from day one.
2. SP-API write path: which MCP holds write credentials.
3. Timezone and brief time (assumed Asia/Jerusalem, 07:00).
4. Account facts: NA unified account, Brand Registry CA/US, Walmart CA or US, Professional plan.
5. Guardrail numbers: monthly PO ceiling (T2 vs T3), daily ad budget cap (T1), minimum margin floor.
6. Repo name and location.

## Sources
- Amazon Ads MCP Server open beta: https://advertising.amazon.com/library/news/amazon-ads-mcp-server-open-beta
- Amazon BSA update effective March 4, 2026: https://sellercentral.amazon.com/seller-forums/discussions/t/84e3f6b1-42f7-4cf3-a189-a5cc8d78d838
- Amazon AI Agent Policy summary: https://sellershorts.com/resources/ai-for-amazon-sellers/amazon-ai-agent-policy
- DataDoe Amazon MCP: https://www.datadoe.com/connect/amazon/mcp
- amazon-seller-mcp (open source SP-API MCP): https://github.com/MarceauSolutions/amazon-seller-mcp
- walmart-mcp: https://github.com/luke-nielsen/walmart-mcp
- Seller Assistant agentic AI: https://novadata.io/resources/news/amazon-seller-assistant-agentic-ai
