# Stack Research

**Domain:** Knowledge compounding layer (observation → pattern → playbook) + operational intelligence dashboard for autonomous e-commerce AI agent system
**Researched:** 2026-04-17
**Confidence:** MEDIUM-HIGH (training data through August 2025; external docs unavailable in this environment; locked-in stack constraints verified against existing codebase files)

---

## Context: What's Already Locked In

The following are non-negotiable — do not recommend changing these:

| Layer | Technology | Version (confirmed in `requirements.txt`) |
|-------|-----------|-------------------------------------------|
| Agent runtime | Python 3.12 + anthropic SDK | `anthropic>=0.92.0` |
| Database | Supabase (Postgres + pgvector) | `supabase>=2.28.0` |
| Knowledge store | Mem0 OSS | `mem0ai>=1.0.11` |
| Dashboard framework | Next.js 14 App Router | locked |
| Dashboard UI | Tailwind CSS + shadcn/ui | locked |
| LLM | Claude Sonnet (daily) / Opus (monthly) | `claude-sonnet-4-20250514` / `claude-opus-4-20250514` |
| Embeddings | OpenAI text-embedding-3-small | via Mem0 |
| Hosting (backend) | Hetzner CX22, systemd | locked |
| Hosting (dashboard) | Vercel free tier | locked |

Research scope: what NEW libraries to add for (a) knowledge compounding consolidation jobs and (b) the dashboard features described in PROJECT.md.

---

## Part 1: Knowledge Compounding Layer (Python)

### The Pattern Being Implemented

Three jobs need to be built in `consolidation/`:

1. **Weekly consolidation** (`weekly_patterns.py`) — reads Mem0 observations, synthesizes patterns, writes pattern memories
2. **Monthly review** (`monthly_review.py`) — validates patterns against Supabase outcome data, promotes to playbooks, decays unvalidated
3. **Wiki compiler** (`wiki_compiler.py`) — reads Mem0 by entity, generates markdown pages, upserts into `wiki_pages` table

Plus two cross-cutting concerns:

4. **Prediction accuracy tracking** — record agent predictions with expected dates, validate outcomes, store calibration data
5. **Confidence calibration logging** — track whether high-confidence memories prove accurate at higher rates

### Recommended Stack: Knowledge Compounding Layer

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `anthropic` | `>=0.92.0` (already installed) | Claude Sonnet for weekly synthesis, Opus for monthly review | Already in codebase; use `client.messages.create()` with `system` + structured JSON output via prompt — same pattern as existing agents |
| `mem0ai` | `>=1.0.11` (already installed) | Read observations, write patterns/playbooks | Already wired; `memory.search(filters={"memory_type": "observation"})` pulls the week's data |
| `supabase` | `>=2.28.0` (already installed) | Read outcome data (profit_daily, sales_daily) for pattern validation; upsert wiki_pages | Already in codebase |
| `pydantic` | `>=2.0.0` (already installed) | Validate Claude's JSON output before writing to Mem0/Supabase | Already in codebase; define `PatternModel`, `PlaybookModel`, `WikiPageModel` — the single safeguard against malformed JSON |
| `jinja2` | `>=3.1.4` | Render wiki page markdown from templates | New addition. Consolidation jobs need to produce structured markdown. Jinja2 lets you define templates per wiki category (product, competitor, playbook) and fill from structured data rather than free-form Claude text. Prevents formatting drift across 30 products. |
| `python-dateutil` | `>=2.9.0` (already installed) | Date arithmetic for "observations from last 7 days", "patterns from last 30 days" | Already in codebase |

**Confidence calibration and prediction tracking** — no new library needed. Use two Supabase tables:

```sql
-- prediction_log: record predictions at time of recommendation
CREATE TABLE prediction_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  agent TEXT NOT NULL,
  run_id TEXT NOT NULL,
  prediction_type TEXT NOT NULL,     -- 'stockout', 'velocity_change', 'acos_impact'
  product_id UUID REFERENCES products(id),
  predicted_value NUMERIC,
  predicted_direction TEXT,          -- 'increase', 'decrease', 'stable'
  predicted_date DATE,               -- when outcome should be measurable
  confidence NUMERIC,                -- 0.0-1.0, from Claude's output
  actual_value NUMERIC,              -- filled in by validation job
  outcome_date DATE,                 -- when validation ran
  validated BOOLEAN DEFAULT FALSE,
  accuracy_score NUMERIC,            -- |predicted - actual| / actual, lower is better
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Run validation weekly: join prediction_log with sales_daily / inventory_snapshots
-- WHERE predicted_date <= CURRENT_DATE AND NOT validated
```

This is plain Supabase — no new Python library required.

### Supporting Libraries: Knowledge Compounding

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `jinja2` | `>=3.1.4` | Wiki markdown templates | Use for `wiki_compiler.py`; define templates per category in `consolidation/templates/` |
| `tenacity` | `>=8.2.0` (already installed) | Retry on Claude API calls in consolidation jobs | Already in codebase; wrap `client.messages.create()` in `@retry` with exponential backoff — consolidation jobs run rarely but are high-value |

**What NOT to add for knowledge compounding:**

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `langchain` | 1.5MB dependency tree, abstracts away the exact prompting patterns that need to be tuned; adds an indirection layer between Claude and Mem0 that makes debugging pattern synthesis failures harder | Plain anthropic SDK + Pydantic, same as existing agents |
| `llama-index` | Same problem as LangChain; designed for RAG pipelines, not for the Karpathy knowledge-promotion pattern | Mem0's native search + Supabase queries |
| `celery` + `redis` | Overkill for 2 jobs/week; introduces Redis as a new dependency on a 4GB CX22 | Cron + systemd (already in place) |
| `apscheduler` | `schedule` is already in use and sufficient; APScheduler adds features (persistence, timezone handling) that aren't needed here | `schedule` (already installed) |
| Custom graph database | CONCERNS.md documents FalkorDB as out-of-scope until 100+ SKUs; 30 SKUs with 3 agents doesn't justify graph traversal overhead | Mem0 semantic search is sufficient |

---

## Part 2: Dashboard (Next.js 14 App Router)

### Feature-to-Library Mapping

The PROJECT.md dashboard requirements, grouped by capability:

**Group A: Data visualization** — anomaly detection feed, prediction scoreboard, agent ROI ledger, seasonal intelligence calendar, knowledge age heatmap, agent health panel, confidence trending

**Group B: Knowledge graph** — entity relationship map of products / competitors / seasons / keywords

**Group C: Decision audit trail** — full chain linkable from observation → recommendation → action → outcome

**Group D: Role-based access** — Rami (all), Father (finance Arabic), Brother (marketing)

**Group E: Wiki viewer** — markdown rendering with confidence indicators

---

### Recommended Stack: Dashboard

#### Core Technologies

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Next.js | 14 (App Router) | Framework | Already locked |
| Tailwind CSS | `>=3.4` | Styling | Already locked |
| shadcn/ui | latest (registry-based) | Component primitives | Already locked |
| `@supabase/supabase-js` | `>=2.43.0` | Data access + auth + RLS | Official Supabase JS client; handles session management, RLS enforcement, and Realtime subscriptions in one package |
| `@supabase/ssr` | `>=0.4.0` | Server-side Supabase auth for App Router | Required for App Router auth; `@supabase/auth-helpers-nextjs` is deprecated for App Router — use `@supabase/ssr` instead |

#### Charting — Use Recharts via shadcn/ui Charts

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `recharts` | `>=2.12.0` | Line, bar, area, radar, composed charts | shadcn/ui's chart system (`/components/ui/chart`) is built on Recharts; you get shadcn's Chart primitives (ChartContainer, ChartTooltip, ChartLegend) for free, which handle theming, responsiveness, and tooltip formatting — no separate charting library needed. Recharts is React-native (SVG, no canvas), has excellent TypeScript types, and is well-maintained through 2025. |

**Why NOT other chart libraries:**

| Avoid | Why |
|-------|-----|
| Tremor | Tremor's chart components wrap Recharts but add their own theme layer that conflicts with shadcn/ui's design tokens. Using both creates two parallel theme systems. Tremor v4 abandoned the Recharts dependency and now uses their own engine — the community has split. |
| Nivo | Excellent for complex visualizations (treemap, chord, stream) but extremely heavyweight (imports the whole library unless you tree-shake carefully). For time-series line/bar charts, Recharts with shadcn wrappers is cleaner. |
| Chart.js / react-chartjs-2 | Canvas-based; harder to customize SVG-level styling; no native React integration; tooltip handling is more complex than Recharts composable approach. |
| Victory | Poorly maintained through 2025; smaller community than Recharts. |

**Specific Recharts chart types per feature:**

| Dashboard Feature | Chart Type | shadcn Component |
|-------------------|-----------|-----------------|
| Agent ROI ledger (revenue delta per recommendation) | `BarChart` + `ReferenceLine` (baseline) | `<ChartContainer>` |
| Prediction scoreboard (accuracy over time) | `LineChart` + `ReferenceLine` at 50% | `<ChartContainer>` |
| Anomaly detection feed (metric with anomaly band) | `AreaChart` + `ReferenceArea` | `<ChartContainer>` |
| Seasonal calendar (velocity bands by month) | `AreaChart` with confidence bands using `Area` stacking | `<ChartContainer>` |
| Knowledge age heatmap | `<Table>` with colored cells (Tailwind bg classes) — NOT a chart | shadcn Table |
| Agent health panel (token spend, run success) | `LineChart` (spend trend) + `RadialBarChart` (success rate) | `<ChartContainer>` |
| Confidence calibration (predicted vs actual) | `ScatterChart` | `<ChartContainer>` |

#### Knowledge Graph Visualization

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `@xyflow/react` (React Flow) | `>=12.0.0` | Entity relationship graph for product/competitor/keyword/season nodes | React Flow is the standard library for interactive node-edge graphs in React as of 2025. It's maintained by a dedicated team (Xyflow), has excellent TypeScript support, handles pan/zoom/minimap natively, and supports custom node renderers — essential for showing Mem0 memory connections. The free tier is sufficient; no license cost. Renders to SVG (not canvas), so it integrates cleanly with Tailwind and shadcn styling. |

**Why NOT D3.js for the knowledge graph:**

D3 is a lower-level visualization primitive. Building an interactive graph editor/viewer in D3 requires implementing pan, zoom, drag, node layout, and edge routing from scratch — React Flow provides all of this. For a knowledge graph where you want to click a product node and see connected memories, React Flow is 10x less code.

**Why NOT Cytoscape.js:**

Cytoscape is designed for scientific network graphs (biological, social networks). The API is verbose for simple product-competitor-keyword relationships. React Flow's component-based API fits Next.js App Router better.

#### Markdown Rendering (Wiki Viewer)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `react-markdown` | `>=9.0.0` | Render wiki page content from `wiki_pages.content` | Pure React renderer; outputs semantic HTML; composable with `remarkGfm` for tables and task lists. Version 9 supports async component rendering in React 18. |
| `remark-gfm` | `>=4.0.0` | GitHub Flavored Markdown (tables, strikethrough, task lists) | Wiki pages will have tables (product comparison, playbook steps); GFM is required. |
| `rehype-sanitize` | `>=6.0.0` | Sanitize HTML in rendered markdown | Wiki content is LLM-generated; sanitization prevents XSS if Claude ever outputs `<script>` or similar. |

**Confidence indicators in wiki pages:**

Use the `✅ / ⚠️ / ❓` marker scheme already defined in CLAUDE.md. These render as-is in `react-markdown`. No special plugin needed — the wiki compiler (Python) embeds them in the markdown text.

#### Role-Based Access

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Supabase Auth (email/password) | via `@supabase/ssr` | Authentication for 3 operators | No OAuth needed; 3 users, email/password is sufficient and free. Supabase Auth handles session JWTs that RLS policies read. |
| Supabase RLS | (database-level) | Data filtering per role | Already designed in CLAUDE.md: ops sees everything, finance sees financial tables, marketing sees PPC/reviews/competitors. RLS enforces this at DB level — no application-layer filtering needed. |

**No NextAuth.js.** NextAuth adds complexity (providers, session callbacks, JWT strategies) that's unnecessary for 3 known users with email/password. Supabase Auth with `@supabase/ssr` handles the App Router pattern directly.

#### RTL / Arabic Support (Father's finance view)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Tailwind CSS `dir="rtl"` attribute | built-in | Logical property utilities (`ms-4`, `ps-4`) flip layout for Arabic | Tailwind v3.3+ has full RTL logical property support. Add `dir="rtl"` on Arabic views, use `ms-/me-/ps-/pe-` instead of `ml-/mr-` in those layouts. |

No `react-i18next` or similar. Arabic content is pre-generated by the Finance agent (Python) and stored in `notifications.body_ar` / `notifications.title_ar`. No runtime translation needed — just display the stored Arabic strings in RTL layout.

#### Supporting Libraries: Dashboard

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `date-fns` | `>=3.6.0` | Date formatting, relative time ("3 days ago"), date arithmetic | Use for all date display in dashboard; smaller than moment.js, tree-shakeable, TypeScript-first |
| `nuqs` | `>=1.17.0` | URL-based state management for filters (agent type, date range, status) | Use for Approvals table filters and Agent Logs filters; URL state = shareable filter state = no Redux needed for this use case |
| `zod` | `>=3.23.0` | Runtime validation of Supabase API responses | Use at the boundary where Supabase data enters React components; catches schema drift before it silently corrupts displays |
| `@tanstack/react-table` | `>=8.17.0` | Headless table for Approvals, Agent Logs, Decision Audit Trail | shadcn/ui's DataTable component is built on TanStack Table; use the same pattern for all tabular data — sorting, filtering, pagination built in |

**What NOT to add to the dashboard:**

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Redux / Zustand | No global client state needed; Supabase data is server-fetched in RSCs; approval actions are mutations; URL state handles filters | Supabase SSR + `nuqs` for URL state |
| `axios` | `fetch` API is available in Next.js 14 App Router natively; Supabase client handles its own HTTP | `@supabase/supabase-js` |
| `react-query` / TanStack Query | For this pattern (mostly server-rendered with Supabase direct queries), RSC data fetching + `revalidatePath` on mutations handles 90% of cases | Next.js RSC + Server Actions |
| `socket.io` | Supabase Realtime handles real-time subscriptions for approval status changes | Supabase Realtime (already in `@supabase/supabase-js`) |
| `tailwind-merge` + `clsx` separately | shadcn/ui already installs `cn()` utility from `class-variance-authority` + `clsx` + `tailwind-merge` | `cn()` already available |

---

## Installation

### Python (knowledge compounding additions to `requirements.txt`)

```
# New additions for consolidation/
jinja2>=3.1.4
```

All other consolidation dependencies (`anthropic`, `supabase`, `mem0ai`, `pydantic`, `tenacity`, `python-dateutil`) are already in `requirements.txt`.

### Dashboard (new Next.js project)

```bash
# Framework (if not already scaffolded)
npx create-next-app@14 dashboard --typescript --tailwind --app --use-npm

# shadcn/ui init
npx shadcn-ui@latest init

# Supabase
npm install @supabase/supabase-js @supabase/ssr

# Charts (via shadcn)
npm install recharts

# Knowledge graph
npm install @xyflow/react

# Markdown rendering
npm install react-markdown remark-gfm rehype-sanitize

# Utilities
npm install date-fns nuqs zod

# TanStack Table (for DataTable)
npm install @tanstack/react-table

# shadcn/ui components needed
npx shadcn-ui@latest add table card badge button dialog select tabs avatar skeleton chart
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Recharts (via shadcn charts) | Nivo | Only if you need treemap, chord diagram, or sankey chart; Nivo's network graph could replace React Flow for the knowledge graph if you prefer D3-style API |
| `@xyflow/react` | D3-force + custom SVG | Only if you need physics-based force-directed layout with >200 nodes; React Flow's layout algorithms are sufficient for 30 products + competitors + keywords |
| `@supabase/ssr` | NextAuth.js + Supabase adapter | Only if you later add third-party OAuth (Google, GitHub) for agency clients |
| `nuqs` | `useSearchParams` + manual state | `nuqs` only if you need type-safe URL state; raw `useSearchParams` works but is verbose |
| `jinja2` | f-strings / string templates in Python | Only for simple single-line wiki content; Jinja2 pays off when templates exceed 3 sections |
| `react-markdown` | `@mdx-js/react` | Only if wiki pages need embedded React components (unlikely for LLM-generated content) |

---

## Version Compatibility Notes

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `@supabase/ssr@>=0.4.0` | Next.js 14 App Router | Requires App Router; do NOT use `@supabase/auth-helpers-nextjs` which is the Pages Router version — it's deprecated |
| `recharts@>=2.12.0` | React 18 | shadcn/ui chart components require Recharts 2.x; do NOT use Recharts 3.x beta — shadcn templates were written for 2.x |
| `@xyflow/react@>=12.0.0` | React 18 | React Flow v12 renamed the package from `reactflow` to `@xyflow/react`; `reactflow` (v11) still works but v12 adds better TypeScript and SSR handling |
| `react-markdown@>=9.0.0` | React 18 | v9 drops CommonJS support; Next.js App Router is ESM-compatible, no issue |
| `nuqs@>=1.17.0` | Next.js 14 App Router | Use `NuqsAdapter` from `nuqs/adapters/next/app` — the Next.js 14 App Router adapter |
| `mem0ai@>=1.0.11` | Python 3.12 | Verified in existing `requirements.txt`; `vecs>=0.4.5` must stay compatible |
| `jinja2>=3.1.4` | Python 3.12 | No conflicts with existing requirements |

---

## Architecture Notes for Consolidation Jobs

**Do not introduce new scheduling infrastructure.** The existing cron on Hetzner handles:
- Saturday 20:00 UTC → `python3 -m consolidation.weekly_patterns`
- 1st of month 08:00 UTC → `python3 -m consolidation.monthly_review`
- Monthly → `python3 -m consolidation.wiki_compiler` (triggered by monthly review)

Each consolidation job follows the same `BaseAgent` pattern already established: sync Supabase query → Mem0 search → Claude call → parse JSON with Pydantic → write back to Mem0/Supabase. No new process management needed.

**JSON output robustness.** The existing `CONCERNS.md` flags Claude response parsing as fragile (#5). For consolidation jobs — which run rarely and handle large batches — wrap Claude's response parsing in:
1. Strip code fences (existing pattern)
2. `pydantic.model_validate_json()` (not `json.loads()`) — Pydantic gives you field-level validation errors, not just "invalid JSON"
3. On validation failure: log full raw text to Supabase `agent_runs.output_summary`, send Telegram alert, skip this run — do NOT retry automatically (consolidation jobs process a week of observations; a retry could double-write patterns)

**Mem0 filter syntax.** The existing codebase uses:
```python
memory.search(query="...", filters={"memory_type": "observation"})
```
For consolidation, you need date-bounded searches. Mem0's filter syntax supports metadata key comparisons; verify `created_date` filter works against production data before relying on it in the weekly job. If date filtering isn't supported in `mem0ai>=1.0.11`, fall back to filtering in Python after retrieval (fetch `limit=200`, filter by `metadata["created_date"] >= seven_days_ago`).

**Wiki compiler output.** Store rendered markdown in `wiki_pages.content`. Use `jinja2` templates per category (not free-form Claude text) to ensure consistent structure across 30 product pages. Claude still writes the prose; Jinja structures which sections appear in which order.

---

## Architecture Notes for Dashboard

**Server Components for all data fetching.** Next.js 14 App Router: fetch Supabase data in RSC (server-side), pass to client components only what needs interactivity. Approval actions are Server Actions (not API routes).

**Knowledge graph data shape.** The graph for `@xyflow/react` needs nodes + edges. Query this from Supabase at page load — no real-time update needed. Build a `GET /api/knowledge-graph` route (or RSC query function) that:
1. Reads all products, competitors, recent Mem0 patterns (via a Supabase-side query on `vecs.memories` metadata)
2. Constructs `{nodes: [], edges: []}` — product nodes, competitor nodes, observation count as edge weight
3. Returns as JSON for React Flow

The graph is read-only — no drag-to-connect UX needed.

**Supabase Realtime for approvals.** Use `supabase.channel()` subscription on `approval_requests` table changes to update the Approvals page without polling. One channel subscription per page load is sufficient — the table changes a few times per day at most.

---

## Sources

- Existing codebase files (`requirements.txt`, `.planning/codebase/STACK.md`, `.planning/codebase/CONCERNS.md`, `.planning/codebase/INTEGRATIONS.md`, `.planning/codebase/ARCHITECTURE.md`) — HIGH confidence (direct inspection)
- `PROJECT.md` feature requirements — HIGH confidence (direct inspection)
- Recharts + shadcn/ui chart integration — MEDIUM confidence (training data through Aug 2025; shadcn chart docs built on Recharts 2.x is well-documented pattern)
- `@xyflow/react` v12 package name — MEDIUM confidence (package rename from `reactflow` happened in late 2023, confirmed pattern through mid-2025)
- `@supabase/ssr` vs `@supabase/auth-helpers-nextjs` deprecation — MEDIUM confidence (Supabase deprecated auth-helpers for App Router in 2024, replaced with `@supabase/ssr`)
- `nuqs` v1.17 NuqsAdapter for Next.js App Router — MEDIUM confidence (nuqs v1 stable pattern as of training cutoff)
- `react-markdown` v9 ESM — MEDIUM confidence (v9 released 2024, drops CJS)

**Verify before implementing:**
1. `recharts` version compatibility with the current shadcn/ui chart component (run `npx shadcn-ui@latest add chart` and check what Recharts version it pins)
2. `mem0ai>=1.0.11` metadata filter syntax for `created_date` — test on production Hetzner before writing weekly consolidation job
3. `@xyflow/react` — confirm package is `@xyflow/react` not `reactflow` at install time (run `npm info @xyflow/react`)

---

*Stack research for: Habib Distribution OS — Knowledge Compounding + Operational Intelligence Dashboard*
*Researched: 2026-04-17*
