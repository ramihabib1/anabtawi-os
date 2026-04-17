# Pitfalls Research

**Domain:** Knowledge compounding systems + operational intelligence dashboards (LLM agent context, e-commerce / Amazon FBA, solo operator)
**Researched:** 2026-04-17
**Confidence:** HIGH — grounded in system architecture review, implemented code analysis, and established failure patterns in production LLM agent systems

---

## Critical Pitfalls

### Pitfall 1: Garbage-In Consolidation — LLM Hallucination Laundered as Patterns

**What goes wrong:**
The weekly consolidation job takes observations from the past 7 days and asks Claude to synthesize patterns. If the input observations are low-quality (vague, confidently stated but data-unsupported, or derived from a day with anomalous data), Claude will produce patterns that sound authoritative but are not grounded in statistical reality. A single day where Almond Fingers happened to sell 40 units instead of 18 can produce a "Almond Fingers demand spike on Tuesdays" pattern that gets reinforced every time Tuesday is above-average by chance. Over months, this creates a false seasonal calendar.

**Why it happens:**
Claude is a very good pattern-recognizer operating on text. It will identify connections in observations even when those connections are noise. The consolidation prompt instructs it to "find patterns" — it will always find patterns, even in random data. There is no statistical significance test in an LLM prompt.

**How to avoid:**
1. Observation schema must include `sample_size` and `data_period_days`. Example: "Almond Fingers sold 40 units Tuesday (sample: 1 day, vs 7-day avg 18.3). Possible anomaly, not pattern." The consolidation prompt must explicitly instruct Claude to require a minimum observation count before synthesizing a pattern (require 3+ consistent observations before creating a new pattern memory).
2. In the consolidation prompt, include this hard rule: "Do NOT promote to pattern unless you have at least 3 independent observations showing the same signal. Mark single-observation findings as 'early signal' with confidence < 0.4."
3. Validate pattern claims against raw Supabase data. For any numeric claim in a pattern ("velocity increased 15%"), the monthly review job should verify it against `sales_daily`. If the data doesn't support the claim, delete the pattern.

**Warning signs:**
- Patterns with 1-2 supporting observations promoted at confidence > 0.7
- Pattern text that contains specific numbers not traceable to Supabase queries
- Growing pattern count that outpaces actual business changes (30 SKUs should not generate 200 unique patterns)
- Contradictory patterns co-existing (e.g., "SKU-X sells better in cold weather" and "SKU-X sells better in summer")

**Phase to address:**
Knowledge Compounding phase — weekly consolidation job design. The observation schema and consolidation prompt rules must be in place before the first consolidation run.

---

### Pitfall 2: Memory Markdown File Becoming an Append-Only Garbage Pile

**What goes wrong:**
The current `AgentMemory.append_learning()` implementation appends every task run as a new entry to a markdown file. The `load_context()` method loads the last 100 lines. After a few weeks of daily agent runs, the markdown file is thousands of lines long. The "last 100 lines" are always the most recent entries — which are less valuable than patterns from 3 weeks ago that proved accurate. The agent's context is dominated by recency, not relevance. After 6 months, the file becomes a wall of text that the agent reads linearly without any signal about which entries are important.

**Why it happens:**
Append-only is the simplest implementation. The developer correctly avoids premature optimization. But without a compaction strategy, the system silently degrades: the agent still "works" (it reads the file), but the intelligence it provides decreases as the noise-to-signal ratio of the markdown context grows.

**How to avoid:**
1. Implement a compaction step in the weekly consolidation job. Each week, the last week's raw entries get summarized into a single "Week of [date]" section. The raw entries are removed. The file stays a manageable 200-400 lines regardless of runtime.
2. Add a `---PERMANENT---` section to each markdown memory file for rules and validated playbooks that should never be compacted. The agent explicitly checks this section before recency-based entries.
3. Cap the markdown file at 500 lines. If it exceeds that, trigger compaction.

**Warning signs:**
- Memory markdown files > 1000 lines
- `load_context()` always returning entries from the last 2-3 days with nothing older represented
- Agent making the same observation repeatedly ("FBA stock for Walnut Fingers is low") without recognizing it as a recurring issue
- Memory files growing at 50+ lines/week

**Phase to address:**
Knowledge Compounding phase — before memory markdown files grow beyond manageable size. Add compaction to the weekly consolidation job as a first-class step.

---

### Pitfall 3: Prediction Tracking With No Counterfactual — All Predictions Appear Correct

**What goes wrong:**
The system records agent predictions with an `expected_date` and validates outcomes. But without a counterfactual baseline, the validation is meaningless. Example: the agent predicts "Almond Fingers will stock out in 12 days." It does stock out in 14 days — the system marks this as a correct prediction. But the naive rule "anything under 14 days supply will stock out within 14 days" would also be correct 100% of the time. The prediction accuracy metric shows 94% accuracy, Rami gains confidence in the system, starts approving everything — and the one time the system is genuinely wrong (bad velocity estimate during a promotion), he doesn't catch it.

**Why it happens:**
Prediction accuracy tracking gets implemented as binary "did the event happen?" without modeling what would have happened without intervention or what the trivially correct baseline looks like. This is survivorship bias in reverse: you count hits, not accounting for how easy the hits are to score.

**How to avoid:**
1. For each prediction category, define a naive baseline and track both. For stockout predictions: baseline = "any SKU under 14 days supply will stock out." Metric: "Agent accuracy minus baseline accuracy." If the agent is only 3 points better than the rule, the prediction isn't adding value.
2. Track confidence calibration explicitly: high-confidence predictions (> 0.8) should prove correct at higher rates than medium-confidence (0.5-0.7). If there's no statistical difference, the confidence scores are noise.
3. Record every prediction that was NOT acted on (rejected approvals, expired approvals) and track whether the predicted outcome occurred anyway. This tests whether the agent is predicting things that would happen regardless.

**Warning signs:**
- Prediction accuracy > 90% consistently (too good, likely predicting easy things)
- Confidence scores clustered in a narrow band (0.6-0.75) — the agent isn't differentiating
- No "misses" recorded in the prediction log
- Predictions that match what any rule-based threshold would produce

**Phase to address:**
Knowledge Compounding phase — the prediction tracking schema and evaluation logic must be designed with counterfactual baselines before any predictions are logged.

---

### Pitfall 4: Vector Store Semantic Drift — Irrelevant Memories Surface Consistently

**What goes wrong:**
The `match_memories()` function retrieves memories by cosine similarity at a 0.7 threshold. After several months of operation, the `agent_memory` table contains thousands of entries. The embedding space becomes polluted: memories from different domains start competing for relevance to any given query. An inventory query surfaces old PPC memories because "keywords with high ACOS" happens to be semantically close to "inventory velocity keywords." The agent's context gets contaminated with off-domain information, leading to spurious connections ("maybe we should pause baklava PPC when doing an FBA shipment") that waste tokens and distract reasoning.

**Why it happens:**
`text-embedding-3-small` produces general-purpose embeddings that don't respect business domain separation. "campaign spending is high" and "cost is high" have similar embeddings even though one is PPC and the other is landed cost. With a small catalog (30 SKUs), the embedding space is tight and many memories cluster near each other.

**How to avoid:**
1. Filter memories by `agent` and/or domain metadata before semantic search. The ops agent should never retrieve memories tagged as PPC-domain unless explicitly doing a cross-domain synthesis. Add a metadata filter to every `match_memories()` call: `match_agent = self.agent_name`.
2. Use separate embedding "namespaces" if possible — even just different `match_agent` values act as partitions. The existing schema already has `match_agent` as a parameter in the `match_memories()` RPC function. Enforce it everywhere.
3. Increase the similarity threshold from 0.7 to 0.75 for routine retrieval. Lower it (0.65) only during the consolidation jobs when cross-domain synthesis is intentional.

**Warning signs:**
- Agent response contains references to irrelevant SKUs ("as we discussed with baklava pricing" in an ops briefing about Mamoul)
- Memory retrieval returning memories from wrong agents in logs
- Increasing token count per agent run without corresponding increase in business complexity
- Agent recommendations referencing historical decisions that were later overridden

**Phase to address:**
Knowledge Compounding phase — the `match_memories()` call must enforce domain filtering. This should be added during consolidation job implementation, not after.

---

### Pitfall 5: The Dashboard Becomes a Vanity Metric Museum

**What goes wrong:**
The dashboard has 12+ proposed features including knowledge graph visualization, prediction scoreboards, seasonal intelligence calendars, and knowledge age heatmaps. Each feature is built and works correctly. But Rami checks the daily briefing on Telegram and only visits the dashboard when something breaks. Father never opens it (the Arabic Telegram summary is sufficient). Maree checks the PPC page occasionally. The wiki, prediction scoreboard, and knowledge age heatmap are visited once on launch day and never again. Six months of development time produces features that drive exactly zero decisions.

**Why it happens:**
Dashboard features are designed for an idealized rational user who reads everything and acts on it. Real operators under time pressure read what arrives in their inbox (Telegram) and investigate when something seems wrong. Pull-based dashboards require habit formation that busy people don't develop unless the dashboard replaces a task they already do.

**How to avoid:**
1. Build the dashboard Home page last, not first. Validate that Telegram is insufficient for a specific workflow before building a dashboard for it. The test: "What decision can I only make correctly by visiting the dashboard, not Telegram?"
2. For every proposed dashboard feature, define the exact operator action it enables: "Rami approves FBA replenishment faster because the dashboard shows projected stockout date vs. current approval." If you can't name the decision, don't build the feature.
3. The Approvals center is the one dashboard feature that clearly passes this test — Telegram is the primary approval channel, but complex approvals (what-if projections, audit trail) benefit from a larger screen. Build this first, validate usage, then expand.
4. Knowledge graph visualization and seasonal intelligence calendar are high-complexity, low-decision-value features. Defer them until Rami asks for them specifically.

**Warning signs:**
- Building dashboard before validating Telegram workflow limitations
- Dashboard features with no direct path to approval or decision
- Features requiring new data collection (not already in Supabase) before they can work
- Total dashboard scope > 6 months of development for a solo operator system

**Phase to address:**
Dashboard phase — scope ruthlessly before building. Apply the "what decision does this enable" test to every feature before starting implementation.

---

### Pitfall 6: Consolidation Double-Processing — Observations Synthesized Multiple Times

**What goes wrong:**
The weekly consolidation job queries Mem0 for "all observations from the past 7 days." But if the consolidation job runs Saturday night and finishes Sunday morning, the next Saturday's run picks up observations from "the past 7 days" including observations from the previous consolidation window's tail. Observations from the overlap period get processed twice. Over time, patterns derived from those observations show inflated reinforcement counts, appearing more confident than they should be. Alternatively: if the consolidation job fails partway through and is re-run, the successfully-processed observations get processed again.

In the Habib OS implementation, the existing codebase doesn't yet have a `last_consolidated_at` watermark or an "already_consolidated" flag on observations. The risk is real.

**Why it happens:**
Date-range queries ("past 7 days") don't provide exactly-once semantics. Any re-run or overlapping window causes duplication. This is a classic message processing idempotency problem applied to LLM knowledge pipelines.

**How to avoid:**
1. Add a `consolidated_at` TIMESTAMPTZ column to `agent_memory` (or use Mem0's metadata). After each successful consolidation, mark all processed memories with the consolidation job's run timestamp. Future consolidation jobs filter to `consolidated_at IS NULL`.
2. Log consolidation runs to a `consolidation_log` table with: run_id, started_at, completed_at, observations_processed, patterns_created, patterns_updated. The next consolidation job checks this log before starting — if a run is in progress (started but no completed_at), it aborts.
3. Make the consolidation prompt idempotent: include the list of observation IDs that contributed to each synthesized pattern. If the same observation ID appears in a future consolidation window, skip it.

**Warning signs:**
- Pattern reinforcement counts growing faster than weekly cadence explains
- Same observation appearing in multiple pattern "evidence" lists
- Consolidation job taking significantly longer than the first run
- Pattern confidence scores exceeding 0.9 on patterns less than 3 weeks old

**Phase to address:**
Knowledge Compounding phase — the consolidation job must have idempotency built in from day one. Do not ship the consolidation job without a processed-observations watermark.

---

### Pitfall 7: Agent ROI Attribution Collapse

**What goes wrong:**
The planned "Agent ROI ledger" shows whether each recommendation made money. The system records that the agent recommended a bid increase on "baklava" keyword, the bid was raised, and then sales increased. It attributes the revenue delta to the agent's recommendation. But three other things happened the same week: a competitor went OOS, it was Ramadan, and Rami ran a coupon. The system shows the agent generated $1,200 in PPC revenue lift — but the actual lift was driven by the competitor stockout and the seasonal event. When Rami over-trusts this ROI figure, he approves aggressive bids during non-Ramadan periods expecting the same lift. The bids perform poorly and he spends 3 weeks debugging why the system's predictions don't hold.

**Why it happens:**
Revenue attribution in e-commerce is genuinely hard even for billion-dollar analytics platforms with A/B testing infrastructure. A solo operator system with no ability to run holdout groups cannot cleanly attribute outcomes to specific interventions. But the dashboard presents the number as if it's clean.

**How to avoid:**
1. Present attribution ranges, not point estimates. Instead of "Agent recommendation generated +$340 revenue," show: "Revenue changed +$340 in the 7 days after this recommendation. Contributing factors detected: competitor OOS (yes), Ramadan season (yes), coupon active (no). Attribution confidence: LOW."
2. Track confounders explicitly. For every outcome measurement, the system should query: Was a competitor OOS during this period? Was this a seasonal event window? Was there a promotion active? Each confounder detected lowers attribution confidence.
3. Use a 28-day rolling baseline window offset to current conditions. Compare to the same period last year when available. Acknowledge in the UI that attribution is approximate.
4. Never present ROI figures in isolation without the "contributing factors" context. This is a UX and labeling decision, not just a data decision.

**Warning signs:**
- ROI dashboard showing clean dollar figures with no confidence bands
- No confounder tracking in the outcome measurement code
- Attribution numbers growing over time as more recommendations are "validated" (classic data mining artifact)
- Recommendations in low-revenue periods show poor ROI even when technically correct

**Phase to address:**
Dashboard phase — the ROI ledger data model must include confounder fields before any attribution numbers are displayed. Design the schema to capture attribution confidence, not just delta revenue.

---

### Pitfall 8: Knowledge Base Temporal Drift — Stale Playbooks Drive Wrong Decisions

**What goes wrong:**
A playbook is validated and promoted: "Raise FBA buffer to 35 days before Ramadan, 8 weeks out." This playbook is correct when validated in April 2026. By November 2026, the business has changed: a new supplier shipping route cuts lead time from 7 days to 4 days, a second warehouse is added, and the product mix changes with 10 new SKUs. The playbook still fires — the system still recommends the 35-day buffer and 8-week lead time. Rami over-orders, ties up $15,000 in slow-moving inventory, and blames the system.

**Why it happens:**
LLM-based knowledge systems have no built-in mechanism for detecting that a validated rule is now outdated. The monthly review job only promotes new playbooks — it doesn't re-validate old ones against changed business conditions. Playbooks accumulate without expiration.

**How to avoid:**
1. Every playbook must have a `valid_until` date or a `re_validate_after` date (maximum 90 days from creation). The monthly review job's scope must include re-validation of all playbooks older than 90 days, not just promotion of new patterns.
2. Track "contextual assumptions" as part of each playbook: {"lead_time_days": 7, "active_warehouses": 1, "active_sku_count": 30}. When these assumptions change by more than 20%, automatically flag the playbook for re-validation.
3. Include a "last validated against outcome data" date in the wiki page for each playbook. Make stale validation visually prominent (> 90 days = orange, > 180 days = red warning).

**Warning signs:**
- Playbooks older than 3 months not appearing in re-validation logs
- Playbook text referencing business parameters that have changed (old lead times, old warehouse count)
- Monthly review job only promoting new patterns, not reviewing existing playbooks
- Wiki pages showing "last compiled" dates but no "last validated" dates

**Phase to address:**
Knowledge Compounding phase — the monthly review prompt must include re-validation of existing playbooks as a first-class step. The `wiki_pages` schema needs a `last_validated_at` field distinct from `updated_at`.

---

### Pitfall 9: Markdown Memory Files Not in `.gitignore` — Secrets in Version Control

**What goes wrong:**
The `.claude/memory/` directory contains markdown files that accumulate agent learnings. These files can contain business-sensitive information: specific revenue figures, pricing strategies, competitor weaknesses identified, margin data. If these files are committed to the git repository (even a private one), they create a persistent record of business intelligence that: (a) could be exposed in a future repo access incident, (b) are hard to redact from git history, (c) bloat the repo over time.

Looking at the existing `.gitignore` in `CLAUDE.md`, it specifies `".gitignore (include .env, .venv, __pycache__, .claude/memory/*.md)"` but this needs verification in the actual file — if it was only documented but not implemented, the files are being committed.

**Why it happens:**
Markdown files don't look like secrets. Developers forget to exclude them. The `.gitignore` entry for `*.md` might inadvertently be scoped too broadly or not at all.

**How to avoid:**
1. Verify `.gitignore` contains `.claude/memory/` (directory-level exclusion, not just `*.md`).
2. Run `git ls-files .claude/memory/` — if any files are tracked, remove them with `git rm --cached`.
3. The CI/CD pipeline should include a pre-push check that `.claude/memory/` contains no tracked files.

**Warning signs:**
- `git status` shows `.claude/memory/*.md` as tracked files
- Commit history contains memory file changes
- `git log --all --full-history -- .claude/memory/` returns results

**Phase to address:**
Pre-launch hardening phase — verify `.gitignore` coverage before the first memory file is written by a production agent run.

---

### Pitfall 10: Weekly Consolidation Prompt "Pattern Inflation" From CLAUDE.md Anchoring

**What goes wrong:**
Every agent run in this system loads the full `CLAUDE.md` (the architecture specification document — 600+ lines) as part of the system prompt. The consolidation job also loads CLAUDE.md. CLAUDE.md contains the L1 rules, example patterns, example observations, and the three-tier knowledge promotion system with examples. Claude will generate patterns that look like the examples in CLAUDE.md, regardless of whether the actual data supports them. Example: CLAUDE.md says "SKU-017 shows consistent Q4 velocity increase." Even before Q4 data exists, Claude may synthesize a pattern echoing this framing because it matches the training distribution in the prompt.

**Why it happens:**
LLMs are extremely sensitive to in-context examples. When the system prompt contains examples of what a "good pattern" looks like, the LLM will produce outputs matching those examples. This is prompt contamination: the architecture document is written for human readers describing desired future state, but the LLM treats it as behavioral instruction for current output.

**How to avoid:**
1. The consolidation job should NOT load CLAUDE.md in the system prompt. It should load only: the L1 rules section, the memory schema definition, and the consolidation task instructions. Strip the narrative examples before passing to Claude.
2. Create a separate `CONSOLIDATION_RULES.md` that contains only what the consolidation job needs (output format, confidence thresholds, minimum observation count rules) without narrative examples.
3. During consolidation, include a negative instruction: "DO NOT generate patterns that are not directly supported by the observations below. Do not infer patterns from general e-commerce knowledge or examples you have been trained on."

**Warning signs:**
- Patterns appearing during consolidation that reference products or scenarios not present in the input observations
- Pattern text that closely mirrors the wording in CLAUDE.md examples
- High-confidence patterns appearing in week 1 of system operation (real patterns take weeks of observation to validate)

**Phase to address:**
Knowledge Compounding phase — the consolidation job prompt design must explicitly exclude narrative examples. Write and test the consolidation prompt before the first weekly run.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `append_learning()` with no compaction | Simple, no data loss | Markdown files grow unboundedly, recency bias dominates context | Only acceptable if compaction is planned for Month 2 |
| Loading full CLAUDE.md in every agent run | Consistency, no prompt management overhead | Anchoring bias in LLM outputs, 600+ tokens per run (cost) | Acceptable for agents; NOT acceptable for consolidation jobs |
| Binary outcome tracking ("did stockout happen?") | Easy to implement | Misleading accuracy metrics, over-trust in system | Never acceptable for the prediction scoreboard feature |
| Date-range window for consolidation ("past 7 days") | Simple query | Double-processing on re-runs, overlapping windows | Never acceptable without an idempotency watermark |
| Confidence score as float (0.0-1.0) on every memory | Flexible | Without calibration tracking, the number is meaningless | Acceptable initially; must be calibrated within 90 days |
| `top_k=5` static memory retrieval | Predictable | May miss critical memories as store grows; no relevance feedback | Acceptable at < 500 memories; revisit at 1000+ |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Mem0 / pgvector via `match_memories()` | Querying without agent filter — all agents' memories compete for relevance | Always pass `match_agent=self.agent_name` except during intentional cross-domain consolidation |
| OpenAI embeddings (`text-embedding-3-small`) | Embedding the raw LLM output text verbatim, including preamble like "Based on the analysis..." | Strip metadata/framing before embedding; embed only the factual claim text |
| Supabase pgvector HNSW index | Inserting high volumes of embeddings without a batch insert strategy — each insert is a round-trip | Batch `agent_memory` inserts; a single consolidation job may generate 20+ memories |
| Claude Sonnet for consolidation | Sending all 100+ observations in a single message — context window saturation causes truncation | Batch by domain (inventory observations separate from PPC); max 30 observations per consolidation call |
| `agent_runs` cost tracking | Logging `cost_usd` calculated from token counts using hardcoded rates | Rate constants will change with Claude pricing; store raw `tokens_input` and `tokens_output` and calculate cost at display time |
| Supabase service key in Python backend | Using anon key for backend jobs to "be safe" — anon key triggers RLS, many queries silently return empty | Backend Python always uses service key; anon key only for Next.js dashboard |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| `load_context()` loading last 100 lines of markdown | Context is always recent, never most-relevant | Add explicit compaction and `---PERMANENT---` section | After ~4 weeks of daily runs |
| `search_memories()` with `top_k=5` on a growing store | Most relevant memories not retrieved as store exceeds 500 entries | Tune `top_k` dynamically based on store size; 5 is too few at 1000+ memories | At ~1000 `agent_memory` rows |
| Weekly consolidation loading 100 observations in one Claude call | Context window pressure, last observations truncated | Batch by domain/agent; chunk to 30 per call | At ~60+ observations/week |
| Monthly wiki compiler generating all 30 product pages sequentially | Monthly review job takes 45+ minutes, risk of Hetzner OOM | Implement as async queue; process 5 products per Claude call | At 30+ SKUs or slow Claude response times |
| Supabase pgvector IVFFlat vs HNSW | Slow similarity searches as table grows | Already using HNSW (confirmed in PROJECT.md) — maintain this, don't switch | HNSW degrades if rebuild is not triggered after bulk inserts |
| Confidence score recalculation during monthly review | If review re-scores all memories, it creates a cascade of writes | Only update memories whose confidence actually changes; use a dirty flag | At 500+ memories |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Memory markdown files tracked in git | Business intelligence (revenue, margins, competitor strategy) exposed in commit history | Verify `.gitignore` has `.claude/memory/` directory exclusion; run `git ls-files .claude/memory/` to confirm |
| Consolidation job logs containing raw observation text | Observation text often contains specific financial figures; if log files are world-readable | Set `/var/log/habib/` to 640 permissions, owned by `habib:habib`; rotate and truncate aggressively |
| `wiki_pages` table containing margin data accessible via anon key | Competitor or employee sees cost structure | RLS policy must restrict `wiki_pages` to authenticated users with ops role; Father and Maree should see wiki but not cost/margin sections |
| Approval request payloads containing raw prices/bids in plaintext | If `approval_requests` table is readable by wrong role | Ensure RLS on `approval_requests` restricts to ops role (Rami only); Father should not see bid amounts in approval history |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Prediction scoreboard shows raw accuracy % | Rami interprets 94% as "system is very smart" when baseline is 91% | Show delta over baseline ("4 points above naive rule"); frame as calibration, not score |
| Knowledge age heatmap always shows "fresh" if agent runs daily | Feature becomes meaningless decoration | Measure knowledge age by domain-specific freshness: "last time a NEW pattern was learned," not "last observation recorded" |
| Wiki pages regenerated monthly — Father reads stale wiki | Wiki may be 3 weeks old during fast-changing period | Add "data freshness" banner to wiki pages: "Based on data through [date]. Next update: [date]." |
| Approvals center shows all approvals including expired | 80% of rows are noise for Rami who wants action | Default filter to `status = 'pending'`; archived view requires explicit click |
| Agent ROI ledger shows dollar figures for all agents equally | Ops agent replenishment ROI ($4,200 stockout prevented) dwarfs PPC agent ROI ($23 ACOS reduction) — PPC looks useless | Normalize by baseline comparison ("$23 better than expected" vs. "$4,200 crisis prevented"); different scales for different agent types |

---

## "Looks Done But Isn't" Checklist

- [ ] **Weekly consolidation job:** Appears complete after first successful run — verify it has idempotency watermarks AND output validation against Supabase before calling it production-ready.
- [ ] **Prediction tracking:** Appears complete when predictions are recorded with expected_date — verify that validation logic runs on the expected_date AND that counterfactual baseline comparison is implemented.
- [ ] **Confidence calibration:** Appears complete when confidence floats are attached to memories — verify that a calibration check runs monthly comparing high-confidence prediction accuracy vs. low-confidence prediction accuracy.
- [ ] **Wiki compiler:** Appears complete when wiki_pages rows are generated — verify that the wiki page for each product includes a "last validated" date AND that stale playbooks are flagged, not just displayed.
- [ ] **Dashboard Approvals page:** Appears complete when pending approvals are shown — verify that approved-and-executed approvals show the execution result AND that the audit chain (recommendation → action → outcome) is navigable.
- [ ] **Agent ROI ledger:** Appears complete when revenue delta is computed — verify that confounder detection (competitor OOS, seasonal window, active promotions) is present AND that attribution confidence is shown next to every dollar figure.
- [ ] **Memory compaction:** Appears unnecessary until markdown files are large — verify a compaction strategy exists before week 4 of production operation.

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Hallucinated patterns in Mem0 | MEDIUM | Delete all pattern-type memories with `memory_type = 'pattern'`; re-run consolidation with stricter prompt; accept 1 week of observation collection before re-running |
| Markdown memory file with contradictory history | LOW | Manually compact the file — keep `---PERMANENT---` section, replace recent entries with a summary paragraph; agent resumes normally |
| Double-processed observations inflating pattern confidence | MEDIUM | Reset `reinforcement_count` on affected patterns; add `consolidated_at` watermark; re-run consolidation from clean slate |
| Attribution numbers misleading Rami into over-trusting system | HIGH | Requires rebuilding trust — add confounder tracking retroactively, add confidence bands, and explicitly brief Rami on the limitation; dashboard copy must be updated to "indicative, not causal" |
| Stale playbooks driving wrong inventory decisions | HIGH | Immediate: override playbook manually with correct parameters. Longer-term: add re-validation cadence and `valid_until` dates to all playbooks |
| Memory files committed to git | MEDIUM | `git rm --cached .claude/memory/` + force-push (with Rami's approval) + update `.gitignore`; if repo is truly private risk is contained |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Garbage-in consolidation (LLM hallucination in patterns) | Knowledge Compounding — consolidation job prompt | Run consolidation manually, review 5 generated patterns against raw Supabase data to verify numeric claims |
| Markdown memory becoming garbage pile | Knowledge Compounding — add compaction to weekly job | Check markdown file line count after 4 weeks; should be < 300 lines after compaction |
| Prediction tracking without counterfactual | Knowledge Compounding — prediction schema design | Verify baseline comparison query exists before first prediction is logged |
| Vector store semantic drift | Knowledge Compounding — `match_memories()` filter enforcement | Audit retrieval logs: verify no cross-agent memories surfacing in agent context |
| Dashboard vanity metric museum | Dashboard — scope gate before build | Apply "what decision does this enable?" test to every feature; document decision for each feature included |
| Consolidation double-processing | Knowledge Compounding — idempotency watermark | Deliberately re-run consolidation job and verify no new patterns are created on re-run |
| Agent ROI attribution collapse | Dashboard — ROI ledger schema design | Schema must include confounder fields before any attribution numbers are displayed |
| Knowledge base temporal drift | Knowledge Compounding — monthly re-validation step | Verify monthly review prompt includes re-validation of all playbooks older than 90 days |
| Memory files in git | Pre-launch hardening | `git ls-files .claude/memory/` returns empty |
| Consolidation prompt anchoring to CLAUDE.md examples | Knowledge Compounding — consolidation prompt design | Consolidation prompt must not load full CLAUDE.md; verify by inspecting prompt construction in consolidation job code |

---

## Sources

- System architecture analysis: `/Users/mareekhalila/Documents/anabtawi-os/CLAUDE.md` and `.planning/PROJECT.md`
- Implemented code review: `habib-os/src/agents/base.py`, `habib-os/src/agents/memory.py`
- Established failure modes in LLM agent memory systems: prompt contamination, semantic drift, append-only degradation — well-documented in production agent deployments
- E-commerce attribution complexity: standard industry limitation in Amazon seller analytics (no holdout groups, correlated variables, seasonal confounding)
- Consolidation idempotency: classic distributed systems problem applied to LLM pipelines; date-range queries never provide exactly-once semantics
- Dashboard adoption failure patterns: dashboard tools universally report that pull-based dashboards lose to push notifications for busy operators; decision-enabling test is a standard product design heuristic

---
*Pitfalls research for: Knowledge compounding systems + operational intelligence dashboards, Amazon FBA e-commerce, solo operator*
*Researched: 2026-04-17*
