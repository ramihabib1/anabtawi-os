# Inter-department communication design (draft, pre-research)

## Principle
Departments do not chat. They share state, send typed requests, and meet when a decision crosses departments. Free-form agent-to-agent conversation is expensive, non-auditable, and drifts. Three channels instead:

## Channel 1: Shared state (the blackboard) — always on
The company repo is mounted in every session. Each department writes to fixed locations others read first:
- `state/inventory.md` (Supply Chain): days of cover per SKU/market, inbound ETAs, capacity limits. Refreshed daily.
- `state/cash.md` (Finance): cash position, 8-week forecast, PO ceiling remaining this month. Weekly.
- `state/ads.md` (Advertising): active launches, spend pacing, ACOS by SKU, campaigns in ramp. Daily.
- `state/prices.md` (Pricing): current price, floor, competitor positions, active tests. Daily.
- `state/catalog.md` (Catalog): listing changes in flight, experiments running, suppressed listings. Weekly.
- `state/health.md` (Account Health): health rating, open violations, compliance deadlines. Daily.
- `state/calendar.md` (Chief of Staff): launches, deals, seasonal windows, blackout dates (no price/listing changes during Vine, deals, or a ranking push).
Rule: before proposing anything, a department reads every state file that touches its proposal. The Chief of Staff checks and rejects proposals that ignore relevant state (e.g., a price cut during an ads ranking push).

## Channel 2: Typed requests (the inbox) — asynchronous
`requests/<dept>/inbox/<id>.md` with a fixed schema: from, to, type, SKU(s), question or ask, needed-by, context links. Types are enumerated, not free text:
- `need-forecast` (Advertising → Supply Chain before scaling spend)
- `need-cash-check` (Supply Chain → Finance before PO proposal)
- `need-margin-floor` (Pricing → Finance)
- `need-launch-plan` (Supply Chain → Advertising/Catalog before inbound sizing)
- `quality-issue` (Customer → Supply Chain/Catalog)
- `blackout` (Advertising/Catalog → Pricing: do not change price on SKU X until date)
- `competitor-oos` (Pricing → Advertising: opportunity, raise bids on X)
- `stockout-risk` (Supply Chain → Advertising: throttle spend on X)
Each department checks its inbox at the start of every run and answers before its own work. Answers are appended to the same file. Unanswered by needed-by escalates to Chief of Staff.

## Channel 3: Meetings (synchronous, coordinated) — scheduled and event-driven
Run as one Managed Agents multiagent session (or one Claude Code session that spawns department subagents): the Chief of Staff is the coordinator; departments are roster threads; the coordinator poses the decision, collects positions, resolves with the constitution, writes the decision to the ledger, and puts anything Tier 2+ in Rami's queue.
Standing meetings:
- Monday WBR (all departments): scorecard, cross-department conflicts, next week's plan.
- Monthly S&OP (Supply Chain, Finance, Advertising, Catalog, Expansion): demand plan → supply plan → cash plan → launch calendar. This is where POs get sized.
- Launch review (Catalog, Advertising, Supply Chain, Pricing) for every new SKU or market.
Event meetings: stockout imminent on hero SKU (Supply Chain + Advertising + Pricing: throttle ads, raise price, expedite); competitor OOS (Pricing + Advertising); account health drop (Health + Catalog + Chief of Staff).

## Why the coordinator, not peer-to-peer
Managed Agents supports coordinator ↔ roster messaging with persistent threads and a shared filesystem, one level deep, no peer-to-peer. This is a feature: every cross-department exchange passes through the Chief of Staff, which gives a single audit trail, a single place to apply the constitution, and a single escalation point to Rami. Departments can still "talk" asynchronously through the inbox without the coordinator; the coordinator only sees escalations.

## What Rami sees
- Morning brief lists unresolved cross-department conflicts as decisions, with each department's position in two lines.
- Every meeting produces a one-page minutes file in `meetings/YYYY-MM-DD-<name>.md`.
- Rami can join any meeting live in a session, or read minutes later.
