# Architecture Research

**Domain:** Knowledge compounding system + agent outcome tracking for AI-driven e-commerce operations
**Researched:** 2026-04-17
**Confidence:** MEDIUM — based on training knowledge (cutoff Aug 2025), existing codebase analysis, and first-principles reasoning. Web search was unavailable. Claims about specific library APIs are flagged where verification is needed.

---

## Standard Architecture

### System Overview

The knowledge compounding layer sits between the raw Mem0 observations (already working) and the dashboard that visualises the resulting intelligence. It consists of four sub-systems:

```
┌─────────────────────────────────────────────────────────────────────┐
│  DAILY OBSERVATION LAYER (exists — Phase 1)                         │
│                                                                     │
│  inventory_agent → write_observations() → vecs.memories (Mem0)     │
│  ppc_agent      ─┘  (role:"user", metadata: memory_type=obs)       │
│  competitor_agent ─┘                                                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │  daily observations accumulate
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CONSOLIDATION LAYER (to build)                                     │
│                                                                     │
│  ┌──────────────────────────┐  ┌──────────────────────────────────┐  │
│  │  weekly_patterns.py      │  │  monthly_review.py               │  │
│  │  Saturday 20:00 UTC      │  │  1st of month 08:00 UTC          │  │
│  │  Claude Sonnet           │  │  Claude Opus                     │  │
│  │                          │  │                                  │  │
│  │  observations → patterns │  │  patterns + outcome data         │  │
│  │  write: memory_type=     │  │  → playbooks                     │  │
│  │    "pattern"             │  │  write: memory_type="playbook"   │  │
│  │                          │  │  + wiki_compiler.py              │  │
│  └──────────────────────────┘  └──────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  consolidation_log (Supabase table — new)                    │   │
│  │  Tracks which observations have been processed, last run      │   │
│  │  timestamps, and output counts per job                        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────┬────────────────────────────────────┘
                                 │  patterns and playbooks stored in Mem0
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  OUTCOME TRACKING LAYER (to build alongside consolidation)          │
│                                                                     │
│  ┌──────────────────────┐   ┌──────────────────────────────────┐    │
│  │  prediction_log      │   │  recommendation_outcomes         │    │
│  │  Supabase table      │   │  Supabase table                  │    │
│  │                      │   │                                  │    │
│  │  Records every       │   │  Records whether agent action    │    │
│  │  forward-looking     │   │  improved business outcome       │    │
│  │  claim agents make   │   │  (linked to approval_requests)   │    │
│  └──────────────────────┘   └──────────────────────────────────┘    │
│                                                                     │
│  validation_runner.py (cron, daily)                                 │
│  Checks prediction_log for past-due predictions, resolves outcomes  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│  WIKI + KNOWLEDGE GRAPH LAYER (to build last)                       │
│                                                                     │
│  wiki_pages (Supabase) — rendered markdown, re-compiled monthly     │
│  entity_graph (Supabase JSONB view) — edges derived from metadata   │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Key Invariant |
|-----------|---------------|---------------|
| `consolidation/weekly_patterns.py` | Read new observations since last run, synthesise patterns using Claude Sonnet, write pattern memories to Mem0 | Idempotent via `consolidation_log` — never re-processes same observation window |
| `consolidation/monthly_review.py` | Read all patterns, cross-reference against Supabase outcome data, promote validated patterns to playbooks, decay unvalidated ones, trigger wiki compiler | Uses Claude Opus; runs once/month; outcome data window is trailing 30 days |
| `consolidation/wiki_compiler.py` | Pull Mem0 memories by entity (product, competitor), ask Claude to write structured markdown, upsert into `wiki_pages` | Re-runs monthly; idempotent via upsert on slug |
| `prediction_log` table | Record every forward-looking quantified claim the inventory agent makes (stockout date, velocity trend, revenue projection) | Written at agent run time; validated by `validation_runner.py` |
| `recommendation_outcomes` table | Record what happened after an approved recommendation was executed | Written by executor (post-execution) + validation_runner (post-outcome-window) |
| `consolidation_log` table | Track consolidation job state — last run, observations processed, patterns written | Single row per job type; prevents double-processing |
| `validation_runner.py` | Daily cron: find past-due predictions, query Supabase for ground truth, mark accurate/inaccurate, update Mem0 metadata | Requires no human input; fully automated |

---

## Data Flow: Observation → Pattern → Playbook → Wiki

### Full Pipeline

```
[Agent Run]
    │
    ├── Claude outputs JSON with "observations" array
    │       Each observation: { text, product_ids, confidence }
    │
    ├── write_observations() → Mem0.add()
    │       Stored in vecs.memories with metadata:
    │           memory_type: "observation"
    │           source_run_id: run_YYYYMMDD_HHMM_agent
    │           created_date: ISO timestamp
    │           reinforcement_count: 1
    │           outcome_validated: false
    │
    └── [end of agent run]

[Saturday 20:00 UTC — weekly_patterns.py]
    │
    ├── Read consolidation_log WHERE job_type='weekly_patterns'
    │       Get: last_processed_cutoff timestamp
    │
    ├── Mem0.search() — observations since last_processed_cutoff
    │       filter: memory_type="observation"
    │       limit: 200 (all observations for the week, not semantic subset)
    │
    ├── Mem0.search() — existing patterns (for update vs. create decision)
    │       filter: memory_type="pattern"
    │       limit: 100
    │
    ├── Claude Sonnet prompt:
    │       "Here are N observations from this week.
    │        Here are existing patterns.
    │        Identify: new patterns | reinforced patterns | contradicted patterns.
    │        Return JSON array."
    │
    ├── For each returned pattern:
    │       IF new → Mem0.add() with memory_type="pattern"
    │       IF update → Mem0.update() on existing pattern ID
    │                   increment reinforcement_count
    │                   update confidence
    │
    └── Update consolidation_log: last_processed_cutoff = NOW()

[1st of month 08:00 UTC — monthly_review.py]
    │
    ├── Read all patterns (memory_type="pattern") from Mem0
    │
    ├── Read outcome data from Supabase:
    │       sales_daily (last 30 days)
    │       profit_daily (last 30 days)
    │       recommendation_outcomes (approved → executed → measured)
    │       prediction_log (predicted vs. actual)
    │
    ├── Claude Opus prompt:
    │       "Validate each pattern against outcome data.
    │        Promote | maintain | decay each.
    │        For promoted: write as actionable playbook protocol."
    │
    ├── For promoted patterns:
    │       Mem0.add() new memory with memory_type="playbook"
    │       Mem0 metadata: outcome_validated=true, confidence >= 0.9
    │       Update original pattern: mark as superseded
    │
    ├── For decayed patterns:
    │       Mem0.update() — reduce confidence, add decay_flag=true
    │
    └── Trigger wiki_compiler.py
```

### Confidence Mechanics

Confidence is stored in Mem0 metadata and updated by consolidation jobs. It is NOT managed by Mem0 itself — Mem0 stores it as a metadata field.

```
Observation (new):          confidence = 0.5-0.7 (set by agent Claude call)
Observation (reinforced):   confidence += 0.1 per reinforcement, cap 0.85
Pattern (new):              confidence = avg(supporting observation confidences)
Pattern (reinforced):       confidence += 0.05 per additional observation
Pattern (contradicted):     confidence -= 0.15, add contradiction_note
Playbook (promoted):        confidence >= 0.9, outcome_validated=true
Playbook (decay trigger):   reinforcement_count unchanged for 60+ days → flag for review
```

The `reinforcement_count` in Mem0 metadata is the key signal. Patterns that accumulate observations become playbooks. Patterns that are never re-seen in new data decay.

---

## Schema: Prediction Log

Records every forward-looking quantified claim at agent run time. The validation runner checks these daily.

```sql
CREATE TABLE prediction_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  -- Source
  agent TEXT NOT NULL,                        -- 'inventory_agent', 'ppc_agent', etc.
  run_id TEXT NOT NULL,                       -- matches agent_runs.run_id format
  agent_run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,

  -- Prediction content
  prediction_type TEXT NOT NULL,              -- 'stockout', 'velocity_trend', 'acos_change',
                                              --   'competitor_oos', 'bsr_change', 'revenue_impact'
  prediction_text TEXT NOT NULL,             -- human-readable: "SKU-017 will stock out in 6 days"
  predicted_value NUMERIC,                   -- quantified: 6 (days), 0.38 (ACOS), 200 (units)
  predicted_unit TEXT,                       -- 'days', 'pct', 'units', 'cad', 'usd'
  predicted_direction TEXT,                  -- 'increase', 'decrease', 'stockout', 'recover'
  confidence NUMERIC NOT NULL CHECK (confidence BETWEEN 0 AND 1),

  -- Entity references
  product_id UUID REFERENCES products(id) ON DELETE SET NULL,
  sku TEXT,                                  -- denormalised for query convenience
  campaign_id UUID,                          -- FK to ppc_campaigns when relevant
  competitor_asin TEXT,

  -- Temporal
  predicted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  resolution_date DATE NOT NULL,             -- the date by which ground truth is checkable
                                             -- inventory_agent: predicted_at::date + predicted_value::int

  -- Resolution (filled by validation_runner.py)
  resolved_at TIMESTAMPTZ,
  resolution_status TEXT CHECK (resolution_status IN (
    'accurate', 'inaccurate', 'partially_accurate', 'unresolvable', 'pending'
  )) DEFAULT 'pending',
  actual_value NUMERIC,                      -- what actually happened
  resolution_notes TEXT,                     -- e.g. "stockout occurred on 2026-04-16 (predicted 04-17)"

  -- Mem0 linkage
  mem0_memory_id TEXT,                       -- the Mem0 memory this prediction came from

  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_prediction_log_agent ON prediction_log(agent);
CREATE INDEX idx_prediction_log_product ON prediction_log(product_id);
CREATE INDEX idx_prediction_log_resolution_date ON prediction_log(resolution_date)
  WHERE resolution_status = 'pending';
CREATE INDEX idx_prediction_log_run ON prediction_log(run_id);
```

**How inventory_agent populates this:** The agent's `process_response()` method should extract restock_recommendations that include `days_of_supply` and write a prediction row for each:

```python
# In inventory_agent.process_response() — add alongside approval_requests
for rec in response.get("restock_recommendations", []):
    days = rec["days_of_supply"]
    resolution_date = (date.today() + timedelta(days=int(days))).isoformat()
    supabase.table("prediction_log").insert({
        "agent": self.agent_name,
        "run_id": self.run_id,
        "prediction_type": "stockout",
        "prediction_text": f"{rec['sku']} projected to stock out in {days} days",
        "predicted_value": days,
        "predicted_unit": "days",
        "predicted_direction": "stockout",
        "confidence": 0.7,          # default; Claude can override per-prediction
        "product_id": rec["product_id"],
        "sku": rec["sku"],
        "predicted_at": datetime.now(timezone.utc).isoformat(),
        "resolution_date": resolution_date,
        "resolution_status": "pending",
    }).execute()
```

---

## Schema: Recommendation Outcomes

Records whether approved actions produced the expected business result. Linked to approval_requests.

```sql
CREATE TABLE recommendation_outcomes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  -- Source
  approval_request_id UUID NOT NULL REFERENCES approval_requests(id) ON DELETE CASCADE,
  agent TEXT NOT NULL,
  action_type TEXT NOT NULL,                 -- matches approval_requests.action_type

  -- What was recommended
  recommendation_text TEXT NOT NULL,
  expected_outcome TEXT NOT NULL,            -- "Prevent stockout for 30 additional days"
  expected_value NUMERIC,                    -- quantified expected improvement
  expected_unit TEXT,                        -- 'days', 'pct_acos_reduction', 'cad_revenue'
  expected_window_days INTEGER NOT NULL,     -- how many days after execution to measure

  -- Measurement window
  measure_after DATE NOT NULL,              -- execution_date + expected_window_days
  measured_at TIMESTAMPTZ,

  -- Entity references
  product_id UUID REFERENCES products(id) ON DELETE SET NULL,
  sku TEXT,
  campaign_id UUID,

  -- Outcome (filled after measure_after passes)
  outcome_status TEXT CHECK (outcome_status IN (
    'positive', 'neutral', 'negative', 'unresolvable', 'pending'
  )) DEFAULT 'pending',
  actual_value NUMERIC,
  delta_value NUMERIC,                       -- actual - baseline at recommendation time
  revenue_impact_cad NUMERIC,               -- estimated revenue delta over measurement window
  revenue_impact_usd NUMERIC,
  outcome_notes TEXT,

  -- Mem0 linkage
  mem0_memory_id TEXT,                       -- memory that generated this recommendation

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_rec_outcomes_approval ON recommendation_outcomes(approval_request_id);
CREATE INDEX idx_rec_outcomes_agent ON recommendation_outcomes(agent);
CREATE INDEX idx_rec_outcomes_measure ON recommendation_outcomes(measure_after)
  WHERE outcome_status = 'pending';
CREATE INDEX idx_rec_outcomes_product ON recommendation_outcomes(product_id);
```

**Who writes initial rows:** The Executor service writes the initial row when it successfully executes an action. It has the context from the approval payload to set `expected_outcome`, `expected_value`, and `measure_after`. For FBA replenishment: measure window = 30 days (does stockout occur?). For PPC bids: measure window = 14 days (does ACOS improve?).

**Who fills outcome:** `validation_runner.py` — daily cron after `measure_after` passes. It queries Supabase ground truth tables (sales_daily, inventory_snapshots, ppc_keyword_stats_daily) and computes deltas vs. the baseline captured at recommendation time.

---

## Schema: Consolidation Log

State management for weekly/monthly jobs. Prevents re-processing observations that were already synthesised.

```sql
CREATE TABLE consolidation_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  job_type TEXT NOT NULL UNIQUE,             -- 'weekly_patterns', 'monthly_review', 'wiki_compile'
  last_run_at TIMESTAMPTZ,
  last_run_status TEXT CHECK (last_run_status IN ('success', 'failed', 'running')),

  -- Idempotency fence — observations with created_date > this were NOT yet processed
  last_processed_cutoff TIMESTAMPTZ,

  -- Output accounting
  observations_read INTEGER DEFAULT 0,
  patterns_written INTEGER DEFAULT 0,
  patterns_updated INTEGER DEFAULT 0,
  playbooks_promoted INTEGER DEFAULT 0,
  wiki_pages_compiled INTEGER DEFAULT 0,

  -- Token cost tracking
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  model_used TEXT,

  -- Error detail
  error_message TEXT,

  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed rows on first deploy:
INSERT INTO consolidation_log (job_type, last_processed_cutoff)
VALUES
  ('weekly_patterns', NOW()),
  ('monthly_review', NOW()),
  ('wiki_compile', NOW())
ON CONFLICT (job_type) DO NOTHING;
```

**The idempotency pattern:** At job start, read `last_processed_cutoff`. At job end (success only), update it to `NOW()`. Any observation with `created_date <= last_processed_cutoff` is skipped. This ensures a failed Saturday job can safely re-run Sunday without double-processing.

The problem with using Mem0's semantic search for consolidation windowing is that `limit=100` returns the semantically closest matches, not the most recent ones. The solution is to query `vecs.memories` directly via Supabase's Postgres connection, filtering on the `metadata->>created_date` JSON field:

```python
# In weekly_patterns.py — bypass Mem0 SDK for time-windowed retrieval
from core.supabase_client import get_supabase

def get_new_observations(cutoff: datetime) -> list[dict]:
    """Query vecs.memories directly for observations since cutoff."""
    supabase = get_supabase()
    # vecs.memories stores metadata as JSONB
    result = supabase.rpc("get_observations_since", {
        "cutoff_ts": cutoff.isoformat(),
        "memory_type": "observation"
    }).execute()
    return result.data

# Alternatively, use raw Postgres via psycopg2 for complex JSONB queries:
# SELECT id, memory, metadata
# FROM vecs.memories
# WHERE metadata->>'memory_type' = 'observation'
#   AND (metadata->>'created_date')::timestamptz > %s
# ORDER BY (metadata->>'created_date')::timestamptz DESC
# LIMIT 200
```

This is the correct pattern for consolidation jobs. Mem0's `.search()` is for semantic retrieval by agents. Consolidation jobs need temporal/filter-based retrieval — they should query the underlying table directly.

---

## Component Boundaries

### What Lives Where

```
consolidation/
├── __init__.py
├── weekly_patterns.py          # Observation → Pattern synthesis
├── monthly_review.py           # Pattern → Playbook promotion + decay
├── wiki_compiler.py            # Mem0 → wiki_pages (markdown generation)
└── validation_runner.py        # Prediction + outcome resolution (daily cron)

core/
├── supabase_client.py          # Existing — add direct postgres helper for vecs queries
└── mem0_client.py              # Existing — add update_memory() wrapper if Mem0 SDK supports it

[New Supabase tables]
├── prediction_log              # Written by: agents | Read by: validation_runner, dashboard
├── recommendation_outcomes     # Written by: executor | Read by: validation_runner, dashboard
├── consolidation_log           # Written by: consolidation jobs | Read by: consolidation jobs
└── wiki_pages                  # Written by: wiki_compiler | Read by: dashboard (read-only)
```

### Communication Rules

| From | To | How | Notes |
|------|----|-----|-------|
| Agents | prediction_log | Direct Supabase insert | At process_response() time |
| Executor | recommendation_outcomes | Direct Supabase insert | After successful SP-API execution |
| weekly_patterns.py | vecs.memories (Mem0) | Direct Postgres query (time filter) + Mem0.add/update | Bypasses Mem0 search for windowed retrieval |
| monthly_review.py | vecs.memories (Mem0) | Mem0.search() (patterns + playbooks) + Mem0.add() | Semantic search is fine — wants best patterns |
| validation_runner.py | prediction_log | Supabase update | Fills resolution_status, actual_value |
| validation_runner.py | recommendation_outcomes | Supabase update | Fills outcome_status, revenue_impact |
| validation_runner.py | vecs.memories | Mem0 metadata update (if API supports) | Updates outcome_validated flag |
| wiki_compiler.py | wiki_pages | Supabase upsert (slug conflict) | Idempotent re-runs |

---

## Architectural Patterns

### Pattern 1: Idempotent Consolidation via Cutoff Timestamp

**What:** Store last-processed cutoff in `consolidation_log`. Query observations using `created_date > cutoff`. On success, update cutoff to NOW().

**When to use:** All weekly and monthly jobs. Prevents duplicate pattern synthesis if job fails mid-run.

**Trade-offs:** Simple; slightly over-inclusive if clock skew exists between Hetzner and Supabase (mitigate by subtracting 5 minutes from cutoff read).

### Pattern 2: Hybrid Retrieval — Direct SQL for Temporal, Mem0 SDK for Semantic

**What:** Consolidation jobs query `vecs.memories` directly via Postgres for time-windowed observation retrieval. Agents use `Mem0.search()` for semantic similarity retrieval. These are distinct access patterns.

**When to use:** Any time you need "all observations since date X" — use SQL. Any time you need "observations most relevant to topic Y" — use Mem0 SDK.

**Trade-offs:** Two retrieval paths means two places to maintain. The Supabase direct connection is already available via `SUPABASE_DB_URL`. The vecs schema and column names should be confirmed against the running Mem0 instance before building consolidation queries.

### Pattern 3: Executor Writes Outcome Baseline at Execution Time

**What:** When the Executor executes an approved action, it writes a `recommendation_outcomes` row immediately, capturing the baseline metrics at execution time (current inventory level, current ACOS, current price). The `validation_runner` later fills the actual outcome after `measure_after` days.

**When to use:** Outcome tracking for all approval types.

**Why this works:** The Executor already has the approval payload, which contains `days_of_supply`, `daily_velocity`, etc. This is the natural point to capture the baseline — the agent run already computed these values.

**Trade-offs:** The Executor currently only writes to `audit_log` and `approval_requests`. Adding a third write point increases the Executor's surface area slightly. It remains safe: the outcome row has no financial implications.

### Pattern 4: Confidence as Explicit Metadata, Not Implicit Retrieval Score

**What:** Confidence is stored as a float in Mem0's `metadata` JSON field, not derived from Mem0's vector similarity scores. It is explicitly set and updated by consolidation jobs.

**When to use:** Always. Mem0's similarity score is a retrieval relevance signal, not a business confidence signal.

**Why this matters:** A memory with high vector similarity to a query but low `confidence` (e.g., an early observation that was later contradicted) should be surfaced with its true confidence, not its retrieval rank. Agents read `m.get("metadata", {}).get("confidence", 0.6)` and weight accordingly.

---

## Anti-Patterns

### Anti-Pattern 1: Using Mem0.search() for Consolidation Windowing

**What people do:** Call `memory.search(query="all observations this week", limit=200)` expecting to get all 7 days of observations.

**Why it's wrong:** Mem0's search is semantic — "all observations this week" is a natural-language query that returns the semantically closest observations, not observations from the past 7 days. With 200+ memories accumulating, the top 200 by semantic similarity to "this week" will be biased toward recent topics, not the actual time window.

**Do this instead:** Query `vecs.memories` directly via Supabase Postgres, filtering on `metadata->>'created_date' > cutoff_timestamp`. This is accurate, deterministic, and fast with the HNSW index in place (though the index is on embedding, not metadata — a JSONB index on `metadata->>'created_date'` would help if observation volume grows large).

### Anti-Pattern 2: Writing Predictions as Prose Only in Observations

**What people do:** Let the agent write "SKU-017 is expected to stock out in 6 days" as a Mem0 observation text, then try to track accuracy by asking Claude to re-read the observation months later.

**Why it's wrong:** Prose is not queryable. You cannot run `SELECT COUNT(*) FROM memories WHERE prediction_text LIKE '%stock out%' AND was_accurate = true`. Prediction accuracy requires a structured, resolvable record with a `resolution_date` and `actual_value`.

**Do this instead:** Write the quantified prediction to `prediction_log` at agent run time. The observation in Mem0 serves as the knowledge layer (human-readable context). The prediction_log row serves as the measurement layer (machine-queryable ground truth comparison).

### Anti-Pattern 3: Promoting Playbooks Based on Pattern Age Alone

**What people do:** After a pattern has been observed for 4 weeks, promote it to a playbook.

**Why it's wrong:** A pattern that says "baklava velocity increases in October" may be consistent over 4 weeks of October observations, but it hasn't been validated against outcome data. The promotion criterion is validation against actual business outcomes, not age.

**Do this instead:** Promotion in `monthly_review.py` requires that `recommendation_outcomes` rows linked to the pattern show `outcome_status = 'positive'` AND `prediction_log` rows for related predictions show `resolution_status IN ('accurate', 'partially_accurate')`. Both conditions together trigger playbook promotion.

### Anti-Pattern 4: Re-Running Monthly Review Without Idempotency

**What people do:** Monthly review fails at the Opus API call. Re-running it processes the same observations again, writing duplicate patterns.

**Why it's wrong:** Duplicate patterns in Mem0 dilute retrieval quality — agents get the same information twice, consuming context window, and the Mem0 deduplication (which uses vector similarity) may not catch exact duplicates if they're slightly reworded.

**Do this instead:** Use `consolidation_log.last_processed_cutoff` as the fence. Only update this on success. Add a running-status check: if `last_run_status = 'running'`, abort (another process is running or died mid-run — alert and wait).

---

## Build Order (Phase Dependencies)

This is the critical sequencing for the next phases. Each item depends on the items above it.

```
1. [FOUNDATION — Already Exists]
   ├── vecs.memories table with daily observations (✅ working)
   ├── approval_requests table (✅ working)
   ├── agent_runs table (✅ working)
   └── BaseAgent with write_observations() (✅ working)

2. [SCHEMA MIGRATION — Must Be First]
   ├── CREATE TABLE consolidation_log          ← enables idempotent jobs
   ├── CREATE TABLE prediction_log             ← enables accuracy tracking
   ├── CREATE TABLE recommendation_outcomes    ← enables ROI tracking
   └── CREATE TABLE wiki_pages                 ← enables wiki compiler
   (These are independent of each other; can be one migration)

3. [AGENT EXTENSION — Runs Against Existing Schema]
   └── Extend inventory_agent.process_response()
       └── Write prediction_log rows for each restock_recommendation
       (Simple addition; no architecture change required)

4. [EXECUTOR EXTENSION — Requires prediction_log Exists]
   └── Extend executor.execute()
       └── Write recommendation_outcomes row after successful SP-API call
       (Requires: schema migration from step 2)

5. [WEEKLY CONSOLIDATION — Requires Observations Exist]
   ├── Requires: consolidation_log table (step 2)
   ├── Requires: 7+ days of observations in vecs.memories
   └── consolidation/weekly_patterns.py
       └── Needs direct vecs.memories Postgres query helper in supabase_client.py

6. [VALIDATION RUNNER — Requires prediction_log + outcome tables]
   ├── Requires: prediction_log, recommendation_outcomes (step 2)
   ├── Requires: executor extension (step 4) for outcome rows to exist
   └── consolidation/validation_runner.py
       (Daily cron; can run against empty tables safely)

7. [MONTHLY REVIEW — Requires Patterns Exist]
   ├── Requires: weekly_patterns.py has run at least once (step 5)
   ├── Requires: recommendation_outcomes with some resolved rows (step 6)
   └── consolidation/monthly_review.py

8. [WIKI COMPILER — Requires Patterns + Playbooks]
   ├── Requires: wiki_pages table (step 2)
   ├── Requires: monthly_review.py has promoted at least some playbooks (step 7)
   └── consolidation/wiki_compiler.py
       (Can run earlier with just observations — pages will be sparse but valid)

9. [DASHBOARD — Reads All Tables]
   ├── Requires: wiki_pages (step 2, step 8)
   ├── Requires: prediction_log with resolved rows (step 6)
   └── Uses: recommendation_outcomes for ROI ledger view
```

**Key insight for scheduling:** Steps 2-4 can be built in a single phase. Steps 5-6 form the second phase. Steps 7-8 form the third. This maps naturally to the project's milestone structure.

---

## Knowledge Graph: Entity Relationship Approach

The PROJECT.md requirement for a "knowledge graph visualization" does not require a graph database (FalkorDB is explicitly deferred until 100+ SKUs). The entity relationships already exist implicitly in Mem0 metadata and can be surfaced via Postgres JSONB queries.

**How entity relationships exist in the current data:**

Every Mem0 memory has metadata:
```json
{
  "product_ids": ["uuid-1", "uuid-2"],
  "campaign_ids": ["uuid-3"],
  "competitor_asins": ["B0xxxxxxxxx"],
  "domain": "inventory",
  "memory_type": "observation"
}
```

A knowledge graph edge is an implicit relationship: if two entities (product A and competitor B) co-appear in the same memory's metadata, there is a relationship between them with a strength proportional to co-occurrence frequency.

**The lightweight graph approach:**

```sql
-- Materialised view: entity co-occurrences (updated monthly by wiki_compiler)
CREATE MATERIALIZED VIEW entity_cooccurrences AS
SELECT
  unnest(
    array_cat(
      ARRAY(SELECT jsonb_array_elements_text(metadata->'product_ids')),
      ARRAY(SELECT jsonb_array_elements_text(metadata->'campaign_ids'))
    )
  ) AS entity_a,
  unnest(
    ARRAY(SELECT jsonb_array_elements_text(metadata->'competitor_asins'))
  ) AS entity_b,
  COUNT(*) AS co_occurrence_count,
  MAX((metadata->>'confidence')::float) AS max_confidence,
  MAX((metadata->>'created_date')::timestamptz) AS last_seen
FROM vecs.memories
WHERE metadata->>'memory_type' IN ('pattern', 'playbook')
GROUP BY entity_a, entity_b
HAVING COUNT(*) > 1;
```

The dashboard reads this materialized view and renders it as a force-directed graph using a library like react-force-graph or Recharts. This gives the entity relationship visualization without requiring any graph database infrastructure.

**Confidence:** LOW — this approach is first-principles reasoning. The exact JSONB syntax for querying the vecs schema should be verified against the live Supabase instance before building the materialized view.

---

## Integration Points

### vecs.memories Table — Direct Access Pattern

The Mem0 SDK writes to the `vecs.memories` table in the `vecs` schema. For consolidation jobs, direct Postgres queries are required:

```python
# core/supabase_client.py — add this helper
import psycopg2
from core.config import SUPABASE_DB_URL

def get_observations_since(cutoff: datetime, limit: int = 500) -> list[dict]:
    """Query vecs.memories directly for time-windowed observation retrieval."""
    conn = psycopg2.connect(SUPABASE_DB_URL)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, content, metadata
            FROM vecs.memories
            WHERE metadata->>'memory_type' = 'observation'
              AND (metadata->>'created_date')::timestamptz > %s
            ORDER BY (metadata->>'created_date')::timestamptz DESC
            LIMIT %s
        """, (cutoff, limit))
        rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "memory": r[1], "metadata": r[2]} for r in rows]
```

**Note on vecs schema internals:** The Mem0 SDK uses the `vecs` library. The actual column names (`id`, `content`/`vec`, `metadata`) should be verified against the running Supabase instance. The `vecs` library has historically used `vec` for the embedding column and `metadata` for JSON metadata. Verify before building consolidation queries.

**Confidence:** MEDIUM — based on vecs library source code patterns known from training data, but schema names should be confirmed by running `\d vecs.memories` on the live Supabase instance.

### Mem0.update() — If SDK Supports It

The consolidation jobs need to update existing pattern memories (increment `reinforcement_count`, update confidence). The Mem0 OSS SDK has a `.update()` method as of v1.x. The pattern is:

```python
memory.update(
    memory_id=existing_pattern_id,
    data=updated_memory_text
)
# Note: metadata updates may require delete + re-add if .update() only changes content.
# Verify Mem0 SDK version supports metadata patch before building.
```

**Confidence:** LOW — Mem0's Python SDK update API changed between versions. The actual method signature for updating metadata (not just content) should be confirmed against `mem0ai>=1.0.11` as specified in requirements.txt.

---

## Scaling Considerations

This is a single-operator system on a CX22. Scaling concerns are irrelevant until >100 SKUs or multi-tenant productization.

| Current Scale | Concern | Approach |
|--------------|---------|----------|
| 30 SKUs, 3 agents/day | vecs.memories grows ~20 rows/day | No concern — pgvector handles millions of rows |
| 30 SKUs, weekly consolidation | Claude Sonnet call with 100 observations | ~30K input tokens = ~$0.09/week. Fine. |
| 30 SKUs, monthly review | Claude Opus call with 200 patterns | ~80K input tokens = ~$2.40/month. Fine. |
| 30 SKUs, wiki compiler | 30 product pages × 1 Claude Sonnet call each | ~$0.90/month. Fine. |

The CX22 (4GB RAM) constraint means weekly/monthly consolidation jobs must run sequentially, not in parallel. This is already the design intent.

---

## Sources

- Existing codebase: `/Users/mareekhalila/Documents/anabtawi-os/agents/base.py`, `inventory_agent.py`, `core/mem0_client.py`
- Project architecture: `CLAUDE.md` (project root), `.planning/PROJECT.md`
- Existing architecture doc: `.planning/codebase/ARCHITECTURE.md`
- Mem0 OSS library patterns: training knowledge (cutoff Aug 2025), confidence MEDIUM
- vecs library schema: training knowledge (cutoff Aug 2025), confidence MEDIUM — verify against live instance
- Knowledge graph approaches: first-principles reasoning, confidence LOW — verify JSONB queries against live schema

---
*Architecture research for: Habib Distribution OS — Knowledge Compounding Layer*
*Researched: 2026-04-17*
