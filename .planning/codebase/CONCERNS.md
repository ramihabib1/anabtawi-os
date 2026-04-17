# CONCERNS.md — Technical Debt, Issues & Risk Areas

## 🔴 Critical / Active Blockers

### 1. Supabase `agent_type` enum not migrated
**File:** `PROJECT_STATE.md` / `agents/base.py:log_run()`
All agent DB writes use `agent: 'ops'` as a workaround because the Supabase enum type hasn't been updated:
```sql
-- Not yet run on production:
ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'inventory_agent';
ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'ppc_agent';
ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'competitor_agent';
ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'consolidation';
```
Until done, `agent_runs.agent` is a lie — all rows appear as `'ops'`. Queries filtering by agent name will silently return wrong results.

### 2. PPC writes not implemented
**File:** `executor/sp_api_client.py:update_keyword_bid()`, `update_campaign_budget()`
Both return `{"status": "not_implemented"}`. PPC Agent (Phase 4) and Advertising API credentials (`ADS_API_*`) aren't wired up yet. Any approved PPC recommendation silently fails execution.

### 3. Mem0 unavailable in dev
**File:** `core/mem0_client.py`
Mem0/pgvector connection fails on local Mac (DNS doesn't resolve Supabase DB direct connection). Dev runs have zero memory context — observations are silently dropped. This means:
- Local testing never validates memory write/read paths
- Observations generated during local test runs are lost

## 🟡 Medium Risk / Tech Debt

### 4. No automated tests
As documented in TESTING.md: zero pytest coverage. Business logic in `_build_inventory_table()`, approval state transitions, and Claude response parsing are untested. Regressions will only be caught by manual runs against production.

### 5. Claude response parsing is fragile
**File:** `agents/inventory_agent.py:analyze()` lines ~150-160
```python
if raw_text.startswith("```"):
    lines = raw_text.split("\n")
    raw_text = "\n".join(lines[1:-1])
result = json.loads(raw_text)
```
If Claude adds a trailing code fence on a different line, or returns partial JSON on token limit, `json.loads()` will raise an unhandled exception — caught by BaseAgent but the whole run fails. No retry logic on malformed output.

### 6. Inventory agent creates approval requests every run for same products
**File:** `agents/inventory_agent.py:process_response()`
No idempotency check. If a restock recommendation for SKU-017 was created yesterday and is still pending, today's run creates a second identical `approval_requests` row. Rami would see duplicate approval requests in Telegram. Needs deduplication (check for pending restock for same product).

### 7. Supabase snapshot query is expensive
**File:** `agents/inventory_agent.py:fetch_data()`
```python
self.supabase.table("inventory_snapshots").select("...").order("snapshot_at", desc=True).limit(500).execute()
```
Fetches up to 500 rows and deduplicates in Python to find the latest per product. With hourly syncs and 30 products, this table grows ~720 rows/day. Over time this query gets slower. Should use `DISTINCT ON (product_id)` in a raw SQL query or a Supabase view.

### 8. Duplicate Supabase client modules
**Files:** `core/supabase_client.py` (sync) vs `sync/supabase_client.py` (async)
Two separate client implementations. The async one in sync/ has different method signatures and session handling. Any shared utility code will need to be duplicated or the two clients will drift. Not a bug today but will cause confusion as more agents are built.

### 9. `habib-os/` legacy directory
The `habib-os/` directory (gitignored) is an old project iteration sitting in the root. No code references it, but it wastes ~22 files of directory clutter and could confuse contributors.

## 🔵 Low Risk / Future Considerations

### 10. No log rotation in production (partial)
**File:** `deploy/crontab`
```
0 0 * * *   find /var/log/habib -name "*.log" -size +10M -exec truncate -s 0 {}
```
Truncates to 0 bytes (loses all history) rather than rotating. For debugging agent failures, losing log history is painful. Should use logrotate with compression instead.

### 11. Executor polls every 60s — approval delay
**File:** `executor/executor.py:run_forever()`
After Rami approves an action in Telegram, it can take up to 60 seconds for the Executor to pick it up. Not a bug but feels laggy for time-sensitive price changes. Could be reduced to 15s with minimal overhead.

### 12. Telegram bot `send_to_role()` in sync utils is not used by bot
**File:** `sync/utils/telegram.py`
This utility sends Telegram alerts from sync jobs (e.g., if inventory_sync fails). But `tgbot/bot.py` is a separate process — sync jobs can't call the bot's async context directly. The utility likely uses `httpx` to call the Bot API directly. This creates a second path for Telegram messaging alongside the bot daemon.

### 13. `consolidation/` is a stub
The knowledge compounding system (Phase 6) — weekly pattern synthesis, monthly review, wiki compiler — is entirely unbuilt. Only `__init__.py` exists. Until this is built, Mem0 observations accumulate but are never synthesized into patterns or playbooks. The system doesn't compound knowledge yet.

### 14. No retry on agent failure (cron gap)
**File:** `deploy/crontab`
The commented-out retry cron lines from `CLAUDE.md` were never added:
```
# 0 6 * * *   python -m scripts.retry_failed --agent inventory
```
`scripts/retry_failed.py` doesn't exist. If the inventory agent fails at 05:30, there's no automatic retry — Rami just doesn't get a brief that day.

### 15. Mem0 memory growth — no cleanup strategy
Observations accumulate daily with no expiry or decay mechanism until the monthly review (Phase 6) runs. After several months, `memory.search()` with limit=15 may surface stale observations. The monthly review's decay logic (confidence reduction, removal) is designed but not implemented.

## Security Observations

### Positive
- SP-API write credentials are only in `executor/` — agents genuinely cannot execute writes
- `.env` is in `.gitignore`, `habib-os/` (legacy) is also gitignored
- No secrets in any committed files

### Risks
- `SUPABASE_SERVICE_KEY` is used by all server-side services — no per-service credential scoping
- Telegram `callback_data` includes the raw UUID (`"approve:uuid"`) — anyone who intercepts the message (or guesses a UUID) could approve an action. In practice, Telegram messages are private but this is not cryptographically authenticated.
- No input validation on `approval_requests.payload` before Executor executes it — if a row is manually inserted with a malformed payload, the executor will throw and log but take no protective action
