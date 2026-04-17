# INTEGRATIONS.md — External APIs & Services

## Supabase (Primary Database)
- **Project:** `thenkkiaeuuxvuoxizjd` (us-east-1)
- **Connection:** `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` via `supabase-py`
- **Direct DB:** `SUPABASE_DB_URL` (PostgreSQL connection string) — used by Mem0 pgvector
- **Client:** `core/supabase_client.py` (sync singleton), `sync/supabase_client.py` (async variant)
- **Access pattern:** Service key for all server-side; future RLS for dashboard
- **Tables written by agents:** `notifications`, `approval_requests`, `agent_runs`, `audit_log`
- **Tables written by sync:** `inventory_snapshots`, `orders`, `order_items`, `sales_daily`, `fees_daily`, `ppc_campaign_stats_daily`, `ppc_keyword_stats_daily`, `competitor_snapshots`, `product_snapshots`, `sync_log`

## Anthropic API (Claude LLM)
- **Auth:** `ANTHROPIC_API_KEY`
- **Client:** `core/anthropic_client.py` (singleton wrapper), also direct `Anthropic()` in agents
- **Usage:** Agent analysis — structured JSON output via `messages.create()` with system prompt + user message
- **Models:** `claude-sonnet-4-20250514` (daily), `claude-opus-4-20250514` (monthly consolidation)
- **Token cost:** ~$0.03/run for Inventory Agent (6.5K in / 1.8K out)
- **No streaming, no tool_use definitions** — agents use JSON mode via system prompt instruction

## OpenAI API (Mem0 embeddings + LLM)
- **Auth:** `OPENAI_API_KEY`
- **Usage:** Called indirectly through Mem0 SDK
  - Embeddings: `text-embedding-3-small` (all memory writes/searches)
  - LLM: `gpt-4o-mini` (fact extraction during `memory.add()`)
- **Not used directly** — all calls go through `mem0ai` SDK

## Amazon SP-API (Selling Partner API)
- **Auth:** LWA (Login with Amazon) OAuth + AWS SigV4 + IAM role assumption
  - `SP_API_REFRESH_TOKEN`, `SP_API_CLIENT_ID`, `SP_API_CLIENT_SECRET`
  - `SP_API_AWS_ACCESS_KEY`, `SP_API_AWS_SECRET_KEY`, `SP_API_ROLE_ARN`
- **Read path:** Sync layer — `sync/spapi/` — custom httpx client with SigV4 signing
  - `sync/spapi/auth.py` — LWA token fetch + AWS STS credential refresh
  - `sync/spapi/client.py` — base HTTP client (paginated, retried via tenacity)
  - `sync/spapi/inventory.py`, `orders.py`, `listings.py`, `catalog.py` — domain endpoints
- **Write path:** Executor — `executor/sp_api_client.py` — uses `python-amazon-sp-api` library
  - Supports: price changes (`ListingsItems` PATCH), listing updates
  - **Not implemented yet:** PPC bid/budget changes (requires separate Advertising API credentials)
- **Marketplaces:** CA (`A2EUQ1WTGCTBG2`), US (`ATVPDKIKX0DER`) — CA is primary

## Amazon Advertising API (PPC)
- **Status:** Stubbed — credentials configured (`ADS_API_CLIENT_ID`, `ADS_API_CLIENT_SECRET`, `ADS_API_REFRESH_TOKEN`, `ADS_API_PROFILE_ID`) but Advertising API not yet wired up
- **When called:** `executor/sp_api_client.py:update_keyword_bid()` and `update_campaign_budget()` return `{"status": "not_implemented"}`
- **Base URL:** `https://advertising-api.amazon.com` (in `sync/config.py`)

## Telegram Bot API
- **Auth:** `TELEGRAM_BOT_TOKEN` (BotFather)
- **Library:** `python-telegram-bot[job-queue]>=21.0`
- **Recipients:** `RAMI_TELEGRAM_ID`, `FATHER_TELEGRAM_ID`, `MAREE_TELEGRAM_ID`
- **Bot module:** `tgbot/bot.py` — polling mode, two repeating jobs (30s interval)
  - `watch_notifications` — sends critical/warning notifications from Supabase
  - `watch_approvals` — sends pending approval requests with inline Approve/Reject buttons
- **Callback handler:** `tgbot/handlers.py` — `approve:{id}` / `reject:{id}` pattern → updates `approval_requests.status`
- **Daily brief:** `tgbot/daily_brief.py` — standalone script called by cron at 07:00 UTC

## Mem0 (Knowledge Store)
- **SDK:** `mem0ai>=1.0.11`
- **Client:** `core/mem0_client.py` — lazy singleton, graceful fallback to `None` if DB unreachable
- **Vector store:** Supabase pgvector (`memories` table, `connection_string=SUPABASE_DB_URL`)
- **user_id:** `"habib_distribution"` (single tenant)
- **Operations used:** `memory.add()` (observations), `memory.search()` (retrieval with filters)
- **Known issue:** Mem0/pgvector not resolvable from local Mac dev environment (DNS). Works on Hetzner.

## GitHub (CI/CD)
- **Repo:** Private (git remote not visible in code)
- **Workflow:** `.github/workflows/deploy.yml` — on push to `main`
  - SSH into Hetzner, `git pull`, `pip install`, `systemctl restart habib-tgbot habib-executor`
- **Secrets:** `HETZNER_HOST`, `HETZNER_SSH_KEY`
