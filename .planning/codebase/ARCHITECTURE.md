# ARCHITECTURE.md — System Architecture

## Pattern
**Layered batch pipeline with human-in-the-loop approval gate.**

Five runtime processes run independently on Hetzner, coordinated through Supabase as shared state:
1. **Sync daemon** — pulls SP-API data into Supabase on schedule
2. **Agent scripts** — read Supabase + Mem0, write recommendations to Supabase
3. **Telegram bot** — watches Supabase notifications/approvals, pushes to phone
4. **Executor daemon** — polls Supabase for approved actions, executes SP-API writes
5. **Cron** — orchestrates all of the above via systemd/cron on Hetzner

## Layers

```
┌─────────────────────────────────────────┐
│  Layer 0: SP-API (Amazon)               │  Read: sync jobs   Write: executor only
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Layer 1: Supabase (Data + State)       │  Postgres + pgvector
│  Shared state for all services          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Layer 2: Sync Layer (sync/)            │  SP-API → Supabase
│  Hourly/daily scheduled jobs            │  async httpx + SigV4
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Layer 3: Knowledge Layer (Mem0)        │  Observations → Patterns → Playbooks
│  pgvector backed, OpenAI embeddings     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Layer 4: Agent Layer (agents/)         │  Read Supabase + Mem0, call Claude
│  Synchronous Python, scheduled by cron  │  Write: notifications, approval_requests
└──────────────┬──────────────────────────┘
               │
     ┌─────────┴──────────┐
┌────▼────┐          ┌────▼────────────────┐
│Telegram │          │ Executor (executor/) │
│Bot      │          │ Watches approved reqs│
│Approval │          │ Executes SP-API write│
│UI       │          └─────────────────────┘
└─────────┘
```

## Data Flow (Daily Cycle)

```
04:30 UTC  inventory_sync    →  inventory_snapshots (Supabase)
04:30 UTC  listings_sync     →  products, product_snapshots
05:00 UTC  fees_sync         →  fees_daily, profit_daily
05:10 UTC  ppc_sync          →  ppc_campaign_stats_daily, ppc_keyword_stats_daily

05:30 UTC  inventory_agent   →  reads: inventory_snapshots, sales_daily, products
                               reads: Mem0 patterns + observations
                               calls: Claude Sonnet (JSON response)
                               writes: notifications, approval_requests
                               writes: Mem0 observations

07:00 UTC  daily_brief       →  reads: notifications, approval_requests, sales_daily
                               sends: Telegram HTML message

[anytime]  telegram_bot      →  watches: notifications (30s poll)
                               watches: approval_requests (30s poll)
                               handles: approve/reject callbacks → updates status

[anytime]  executor          →  polls: approval_requests WHERE status=approved (60s)
                               executes: SP-API writes
                               writes: audit_log, approval_requests.execution_result
```

## Abstractions

### BaseAgent (`agents/base.py`)
Template Method pattern. Subclasses override:
- `fetch_data() → dict` — Supabase queries
- `analyze(data, memories) → dict` — Claude call, returns structured JSON
- `process_response(response) → str` — write to Supabase, return summary string

Shared infrastructure in base: `fetch_memories()`, `write_observations()`, `create_approval_request()`, `create_notification()`, `log_run()`, `send_failure_alert()`

### Sync Layer (`sync/spapi/`)
Custom HTTP client pattern: `sync/spapi/client.py` handles auth, SigV4 signing, pagination, retry. Domain modules (`inventory.py`, `orders.py`, etc.) call the base client.

Auth chain: `LWA refresh_token → access_token` + `AWS STS AssumeRole → temporary creds` → SigV4-signed headers

### Executor (`executor/executor.py`)
Simple polling loop: `while True: process_approved_requests(); sleep(60)`. Action dispatch via `if/elif` on `action_type`. Result always written back to DB regardless of success/failure.

## Entry Points
| Module | How to invoke |
|--------|---------------|
| `agents/inventory_agent.py` | `python3 -m agents.inventory_agent` |
| `executor/executor.py` | `python3 -m executor.executor` (daemon) |
| `tgbot/bot.py` | `python3 -m tgbot.bot` (daemon, systemd) |
| `tgbot/daily_brief.py` | `python3 -m tgbot.daily_brief` (cron) |
| `sync/scheduler.py` | `python3 -m sync.scheduler` (daemon) |
| `sync/jobs/*.py` | `python3 -m sync.jobs.inventory_sync` (individual cron jobs) |
| `scripts/setup_mem0.py` | `python3 scripts/setup_mem0.py` (one-time) |

## State Machine: Approval Requests
```
pending → (Telegram or Dashboard approve/reject)
                ↓
          approved → (Executor executes) → execution_result set
          rejected → terminal
          expired  → (expire_approvals job runs every 30 min)
```

## Key Design Decisions
- **Agents don't call SP-API.** Only the Executor has SP-API write credentials.
- **No agent-to-agent communication.** Each agent is independent; they share state via Supabase only.
- **Mem0 is optional.** `get_memory()` returns `None` if connection fails; agents degrade gracefully.
- **Sync layer is async, agents are sync.** Sync layer uses `asyncio` + `httpx` for throughput; agents are simpler synchronous scripts.
- **No Claude tool_use schema.** Claude returns structured JSON via system prompt instruction + manual `json.loads()` parsing.
