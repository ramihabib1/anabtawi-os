# STACK.md — Technology Stack

## Language & Runtime
- **Python 3.12** — all backend services (agents, sync, executor, bot)
- **Node.js** — only for GSD tooling (`.claude/` directory), not business logic

## Dependency Manifest
`requirements.txt` (key packages):
```
anthropic>=0.92.0          # Claude API calls (agents)
supabase>=2.28.0           # Supabase REST client (sync layer uses supabase-py async variant)
mem0ai>=1.0.11             # Knowledge layer (Mem0 OSS)
vecs>=0.4.5                # pgvector helper (used by Mem0 internally)
python-telegram-bot[job-queue]>=21.0  # Telegram bot
python-amazon-sp-api>=2.0.0           # SP-API REST (executor, legacy)
python-dotenv>=1.0.0
pydantic>=2.0.0
httpx>=0.28.0              # async HTTP (sync layer uses direct SigV4 signed requests)
boto3>=1.34.0              # AWS STS for SP-API role assumption
tenacity>=8.2.0            # retry/backoff
schedule>=1.2.0            # in-process scheduling (scheduler daemon)
structlog>=24.0.0          # structured JSON logging (sync layer)
```

## Frameworks & Libraries (by layer)

### Agent Layer (`agents/`, `core/`)
- **anthropic Python SDK** — direct API calls with tool-use JSON schema
- **supabase-py** (synchronous client) — reads/writes via Supabase REST API
- **Mem0 OSS** — memory add/search over pgvector
- Standard `logging` module

### Sync Layer (`sync/`)
- **httpx** (async) — custom SigV4-signed requests to SP-API
- **boto3 + STS** — IAM role assumption for SP-API AWS auth
- **structlog** — structured JSON logs (production), colored console (dev)
- **tenacity** — exponential backoff with jitter on all SP-API calls
- **schedule** — daemon-based job scheduling (alternative to cron)
- **supabase-py** (async) — DB writes

### Executor (`executor/`)
- **python-amazon-sp-api** — higher-level SP-API wrapper for price/listing writes
- Standard `logging`, `time.sleep` polling loop

### Telegram Bot (`tgbot/`)
- **python-telegram-bot[job-queue]** — bot polling + JobQueue for repeating tasks

## Models
- **Daily agents:** `claude-sonnet-4-20250514` (configured in `core/config.py:MODEL_DAILY`)
- **Consolidation:** `claude-opus-4-20250514` (configured in `core/config.py:MODEL_CONSOLIDATION`)
- **Mem0 LLM:** `gpt-4o-mini` (OpenAI — fact extraction)
- **Mem0 embeddings:** `text-embedding-3-small` (OpenAI)

## Configuration
All config lives in `core/config.py`, loaded from `.env` via `python-dotenv`. The sync layer wraps this via `sync/config.py` (a `SimpleNamespace` adapter). No `.env.example` or config schema exists.

Key constants:
- `L1_RULES` — immutable business rules string embedded in every agent system prompt
- `MODEL_DAILY`, `MODEL_CONSOLIDATION` — model ID strings
- Marketplace IDs: `SP_API_MARKETPLACE_CA = "A2EUQ1WTGCTBG2"`, `SP_API_MARKETPLACE_US = "ATVPDKIKX0DER"`
- `PROBE_ASIN = "B0FT3HN2XV"` — used for seller ID discovery

## Infrastructure
- **Hetzner CX22** — Python services (agents, executor, bot, sync)
- **Supabase Cloud (us-east-1)** — Postgres + pgvector for data + Mem0 memories
- **Vercel** — planned Next.js dashboard (Phase 7, not built)
- **GitHub Actions** — CI/CD: push to `main` → SSH deploy to Hetzner (`deploy/habib-executor.service`, `deploy/habib-tgbot.service`, `deploy/crontab`)

## Python Version Compatibility Notes
- Uses `X | Y` union type syntax (Python 3.10+)
- Uses `list[dict]` etc. generic syntax (Python 3.9+)
- Async used extensively in sync layer; agent layer is synchronous
