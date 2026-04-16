# Habib Distribution OS — Project State

> This file is the source of truth for what's built and what's next.
> Claude reads this at the start of every session. Rami updates it when things change.

Last updated: 2026-04-09

---

## Current Status: Phase 1 Complete

| Phase | What | Status |
|-------|------|--------|
| 0 | Foundation (scaffolding, core modules, base agent) | ✅ Complete |
| 1 | Inventory Agent | ✅ Complete — running, tested against real data |
| 2 | Telegram Bot + Approval Flow | ⬜ Not started |
| 3 | Executor Service (SP-API writes) | ⬜ Not started |
| 4 | PPC Agent | ⬜ Not started |
| 5 | Competitor Intel Agent | ⬜ Not started |
| 6 | Knowledge Compounding (weekly/monthly consolidation, wiki) | ⬜ Not started |
| 7 | Dashboard (Next.js on Vercel) | ⬜ Not started |
| 8 | Hardening & Deploy to Hetzner | ⬜ Not started |

---

## What Exists

```
habib-os/
├── .env                          ✅ All credentials (Supabase, Anthropic, OpenAI)
├── requirements.txt              ✅ Pinned dependencies
├── venv/                         ✅ Python venv (local Mac only)
│
├── core/
│   ├── config.py                 ✅ Env vars + L1_RULES
│   ├── supabase_client.py        ✅ Supabase REST client
│   ├── mem0_client.py            ✅ Mem0 client (graceful fallback if DB unreachable)
│   └── anthropic_client.py       ✅ Anthropic client
│
├── agents/
│   ├── base.py                   ✅ BaseAgent class
│   └── inventory_agent.py        ✅ Inventory Agent — tested, writes to Supabase
│
├── scripts/
│   └── setup_mem0.py             ✅ One-time Mem0 verification
│
├── executor/                     ⬜ Empty (Phase 3)
├── telegram/                     ⬜ Empty (Phase 2)
└── consolidation/                ⬜ Empty (Phase 6)
```

---

## Pending Before Hetzner Deploy

### 1. Add agent enum values in Supabase (SQL editor)
```sql
ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'inventory_agent';
ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'ppc_agent';
ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'competitor_agent';
ALTER TYPE agent_type ADD VALUE IF NOT EXISTS 'consolidation';
```
Until done: all DB writes use `agent: 'ops'` as a workaround.

### 2. Telegram credentials
- Create bot via BotFather → get `TELEGRAM_BOT_TOKEN`
- Get Rami's Telegram chat ID → set `RAMI_TELEGRAM_ID`
- Add both to `.env`

### 3. SP-API credentials (Phase 3)
- `SP_API_REFRESH_TOKEN`, `SP_API_CLIENT_ID`, `SP_API_CLIENT_SECRET`
- Add to `.env` when ready

### 4. Create `wiki_pages` table in Supabase (Phase 6)
SQL is in the architecture doc (CLAUDE.md section 3.2).

---

## Known Issues / Notes

- **Mem0 pgvector** — works on Hetzner, not resolvable from this Mac (DNS). Agent handles gracefully.
- **14 of 23 products have zero sales velocity** — real data, not a bug. Listings may be new/inactive.
- **Inventory snapshots** — latest is April 1 (sync runs on Supabase schedule).
- **Token cost** — ~$0.03 per Inventory Agent run (6.5K in / 1.8K out tokens).

---

## How to Run

```bash
cd /Users/mareekhalila/Documents/anabtawi-os
source venv/bin/activate

# Run inventory agent
python3 -m agents.inventory_agent
```
