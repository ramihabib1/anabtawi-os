# STRUCTURE.md — Directory Layout & Organization

## Project Root
`/Users/mareekhalila/Documents/anabtawi-os/` (deployed as `/home/habib/anabtawi-os/` on Hetzner)

```
anabtawi-os/
├── CLAUDE.md                  # Full architecture spec (read by Claude every session)
├── PROJECT_STATE.md           # Phase tracker — what's built, what's next
├── requirements.txt           # Python dependencies
├── .env                       # Secrets (never committed)
├── .gitignore
│
├── core/                      # Shared utilities used by agents + executor + bot
│   ├── config.py              # All env vars, L1_RULES, model names
│   ├── supabase_client.py     # Sync supabase-py singleton
│   ├── mem0_client.py         # Mem0 Memory singleton (graceful None fallback)
│   └── anthropic_client.py    # Anthropic SDK singleton
│
├── agents/                    # AI agents (Claude-powered batch scripts)
│   ├── base.py                # BaseAgent class (Template Method pattern)
│   └── inventory_agent.py     # ✅ Phase 1 — fully implemented and tested
│   # ppc_agent.py             ← Phase 4 (not built)
│   # competitor_agent.py      ← Phase 5 (not built)
│
├── executor/                  # SP-API write executor (systemd daemon)
│   ├── executor.py            # Approval watcher + action dispatcher
│   └── sp_api_client.py       # Price/listing updates via SP-API
│
├── tgbot/                     # Telegram bot (systemd daemon + cron brief)
│   ├── bot.py                 # Main loop — notification + approval watchers
│   ├── handlers.py            # Callback handler for approve/reject buttons
│   ├── formatters.py          # Message formatting helpers
│   └── daily_brief.py         # Cron script — morning summary to Telegram
│
├── sync/                      # SP-API → Supabase sync layer (async)
│   ├── config.py              # SimpleNamespace wrapper around core/config.py
│   ├── scheduler.py           # Optional in-process scheduler daemon
│   ├── supabase_client.py     # Async supabase client (separate from core/)
│   ├── db_helpers.py          # write_sync_log() helper
│   ├── spapi/                 # SP-API HTTP client suite
│   │   ├── client.py          # Base client (SigV4, retry, pagination)
│   │   ├── auth.py            # LWA + STS credential management
│   │   ├── inventory.py       # FBA inventory summaries
│   │   ├── orders.py          # Orders + order items
│   │   ├── listings.py        # Product snapshots + listing status
│   │   ├── catalog.py         # ASIN catalog lookups
│   │   └── advertising.py     # Advertising API (stubbed)
│   ├── jobs/                  # Individual sync jobs (called by cron or scheduler)
│   │   ├── inventory_sync.py  # Hourly — FBA inventory → inventory_snapshots
│   │   ├── orders_sync.py     # Hourly — orders → orders, order_items, sales_daily
│   │   ├── listings_sync.py   # Daily 04:30 — product status → products
│   │   ├── fees_sync.py       # Daily 05:00 — fees → fees_daily, profit_daily
│   │   ├── ppc_sync.py        # Daily 05:10 — PPC stats → ppc_*_stats_daily
│   │   ├── reviews_sync.py    # Weekly — reviews → reviews, competitor_reviews
│   │   ├── competitor_sync.py # Weekly — competitor ASINs → competitor_snapshots
│   │   └── expire_approvals.py # Hourly — marks stale pending requests as expired
│   └── utils/
│       ├── logging.py         # structlog setup (configure_logging, get_logger)
│       ├── audit.py           # log_action() helper → audit_log table
│       └── telegram.py        # send_to_role() — Telegram alerts from sync jobs
│
├── consolidation/             # Knowledge compounding (Phase 6 — not built)
│   └── __init__.py
│   # weekly_patterns.py       ← not built
│   # monthly_review.py        ← not built
│   # wiki_compiler.py         ← not built
│
├── scripts/                   # One-time + diagnostic scripts
│   ├── setup_mem0.py          # Verify Mem0 connection (write + search test)
│   ├── test_approval.py       # Create a test approval request
│   └── verify_approval.py     # Check approval request status
│
├── deploy/                    # Hetzner deployment artifacts
│   ├── crontab                # Full cron schedule (copy to /etc/cron.d/habib)
│   ├── habib-executor.service # systemd service for executor daemon
│   ├── habib-tgbot.service    # systemd service for Telegram bot
│   └── setup.sh               # Server setup script
│
├── venv/                      # Local Python venv (not deployed — server has own venv)
├── habib-os/                  # Legacy directory (old project iteration — gitignored)
│
└── .claude/                   # Claude Code + GSD tooling (not business logic)
    └── get-shit-done/         # GSD workflow system
```

## Key File Locations
| What | Where |
|------|-------|
| Business rules (L1_RULES) | `core/config.py:L1_RULES` |
| Model names | `core/config.py:MODEL_DAILY`, `MODEL_CONSOLIDATION` |
| Cron schedule | `deploy/crontab` |
| All credentials | `.env` (never committed) |
| Phase tracker | `PROJECT_STATE.md` |
| Full architecture spec | `CLAUDE.md` |

## Naming Conventions
- **Modules:** snake_case (Python standard)
- **Classes:** PascalCase (`BaseAgent`, `Executor`, `SPAPIClient`)
- **Functions:** snake_case
- **Constants:** UPPER_SNAKE_CASE (`L1_RULES`, `MODEL_DAILY`, `SUPABASE_URL`)
- **Agent names (in DB):** snake_case strings (`"inventory_agent"`, `"ppc_agent"`)
- **Memory types (in Mem0):** lowercase strings (`"observation"`, `"pattern"`, `"playbook"`)
- **Action types (approval_requests):** snake_case (`"fba_replenishment"`, `"price_change"`, `"ppc_bid_change"`)

## Dual Client Pattern (Known Divergence)
There are two Supabase client modules:
- `core/supabase_client.py` — synchronous, used by agents + executor + tgbot
- `sync/supabase_client.py` — async, used by sync jobs

These are intentionally separate due to the async/sync split between layers.
