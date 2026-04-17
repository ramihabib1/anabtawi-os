# Habib Distribution OS — Complete Architecture & Implementation Plan

> **Version:** 1.0 — April 9, 2026
> **Author:** Architecture session between Rami Anabtawi and Claude (Senior Systems Architect)
> **Status:** Approved for implementation

---

## Table of Contents

1. Executive Summary
2. Architecture Overview
3. Layer 1: Data Layer (Supabase)
4. Layer 2: Sync Layer (SP-API)
5. Layer 3: Knowledge Layer (Mem0 + pgvector)
6. Layer 4: Agent Layer (Claude Agent SDK)
7. Layer 5: Action Layer (Executor Service)
8. Layer 6: Interface Layer (Telegram + Dashboard)
9. Agent Designs (Detailed)
10. Knowledge Compounding System
11. Infrastructure & Deployment
12. Error Handling & Monitoring
13. Security & Safety Invariants
14. Implementation Plan (Phased)
15. Cost Projections
16. Future Considerations

---

## 1. Executive Summary

The Habib Distribution OS is an AI-powered autonomous operating system for managing an e-commerce distribution business on Amazon Canada, Amazon US, and (future) Walmart Canada. It is designed for a solo technical operator with no DevOps team.

### Core Design Principles

- **Solo operator first.** Every component must be maintainable by one person. If it needs babysitting, it's wrong.
- **Simplicity over cleverness.** Fewer moving parts. Fewer failure modes. Fewer things to debug at 2am.
- **Knowledge compounds.** The system gets smarter every day. After 12 months, it should know the business better than any human.
- **Humans approve, machines execute.** No financial action without explicit human approval. Ever.
- **One source of truth.** Supabase is the database. Mem0 is the knowledge store. No parallel systems that drift.

### What It Does

Three AI agents run daily on a schedule:

1. **Inventory Agent** — Predicts stockouts, recommends restocks, optimizes FBA inbound timing
2. **PPC Agent** — Analyzes campaign performance, recommends bid/budget changes
3. **Listing & Competitor Intel Agent** — Monitors competitors, detects pricing opportunities, guards listing health

Each agent reads current data from Supabase, reads accumulated knowledge from Mem0, reasons with Claude, writes recommendations and observations back. Recommendations that require financial action go through a Telegram approval flow. A daily brief lands on Rami's phone every morning. A Next.js dashboard provides deep review.

### Technology Stack

| Component | Technology | Where It Runs |
|-----------|-----------|---------------|
| Database | Supabase (Postgres + pgvector) | Supabase Cloud (us-east-1) |
| Knowledge Store | Mem0 OSS (Python SDK) | Hetzner VPS |
| Vector Store | Supabase pgvector (via Mem0) | Supabase Cloud |
| Agent Runtime | Claude Agent SDK (Python) | Hetzner VPS |
| LLM | Claude Sonnet (daily), Claude Opus (consolidation) | Anthropic API |
| Executor | Python service | Hetzner VPS |
| Telegram Bot | Python (python-telegram-bot) | Hetzner VPS |
| Dashboard | Next.js | Vercel |
| Scheduler | Cron (systemd timers) | Hetzner VPS |
| VPS | Hetzner CX22 (2 vCPU, 4GB RAM) | Hetzner Cloud |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AMAZON SP-API                            │
│              (reads: scheduled sync | writes: executor)         │
└──────────────────┬──────────────────────────┬───────────────────┘
                   │ scheduled sync           │ approved writes
                   ▼                          ▲
┌─────────────────────────────────────────────────────────────────┐
│                     SUPABASE (us-east-1)                        │
│                                                                 │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────────────┐   │
│  │ Core Tables │ │ Agent Tables │ │ Mem0 Vector Store      │   │
│  │ products    │ │ agent_runs   │ │ memories (pgvector)    │   │
│  │ orders      │ │ audit_log    │ │                        │   │
│  │ inventory   │ │ decision_log │ │                        │   │
│  │ ppc_*       │ │ approval_req │ │                        │   │
│  │ competitors │ │ notifications│ │                        │   │
│  └─────────────┘ └──────────────┘ └────────────────────────┘   │
└──────────────────┬──────────────────────────────────────────────┘
                   │ direct queries (psycopg2/supabase-py)
                   │
┌──────────────────▼──────────────────────────────────────────────┐
│                    HETZNER VPS (CX22)                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   AGENT LAYER                             │   │
│  │  ┌────────────┐ ┌────────────┐ ┌─────────────────────┐   │   │
│  │  │ Inventory  │ │    PPC     │ │ Listing & Competitor│   │   │
│  │  │   Agent    │ │   Agent    │ │    Intel Agent      │   │   │
│  │  └─────┬──────┘ └─────┬──────┘ └──────────┬──────────┘   │   │
│  │        │              │                    │              │   │
│  │        ▼              ▼                    ▼              │   │
│  │  ┌──────────────────────────────────────────────────┐     │   │
│  │  │              Mem0 Python SDK                      │     │   │
│  │  │         (read/write knowledge layer)              │     │   │
│  │  └──────────────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐   │
│  │   Executor   │ │ Telegram Bot │ │   Consolidation Jobs   │   │
│  │  (SP-API     │ │ (approvals,  │ │  (weekly patterns,     │   │
│  │   writes)    │ │  alerts,     │ │   monthly playbooks,   │   │
│  │              │ │  daily brief)│ │   wiki generation)     │   │
│  └──────────────┘ └──────────────┘ └────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    CRON SCHEDULER                         │   │
│  │  05:00 SP-API sync | 05:30 Inventory | 06:00 PPC        │   │
│  │  06:30 Competitor  | 07:00 Daily Brief                   │   │
│  │  Saturday 20:00 Weekly Consolidation                     │   │
│  │  1st of Month Monthly Review                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                   │
                   │ API calls
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VERCEL (Dashboard)                            │
│  Next.js: Wiki viewer, approval history, agent logs, stats      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Layer 1: Data Layer (Supabase)

### 3.1 Existing Schema — No Changes Required

The existing Supabase schema (project `thenkkiaeuuxvuoxizjd`, us-east-1) is production-ready. All tables listed in the architecture brief are retained as-is. Key tables by domain:

**Core:** `brands`, `marketplaces`, `warehouses`, `products`, `users`

**Inventory:** `inventory_snapshots`, `warehouse_inventory`, `warehouse_stock_movements`, `inbound_shipments`, `inbound_shipment_items`, `supplier_shipments`, `supplier_shipment_items`

**Sales & Financials:** `orders`, `order_items`, `sales_daily`, `fees_daily`, `profit_daily`, `product_cost_history`

**PPC:** `ppc_campaigns`, `ppc_ad_groups`, `ppc_keywords`, `ppc_campaign_stats_daily`, `ppc_keyword_stats_daily`

**Reviews:** `reviews`

**Competitors:** `competitors`, `competitor_snapshots`, `competitor_reviews`

**Agent Infrastructure:** `approval_requests`, `audit_log`, `notifications`, `agent_runs`, `decision_log`

**Sync:** `sync_log`, `product_snapshots`

### 3.2 Schema Modifications

**Remove `agent_memory` table.** Mem0 manages its own storage in Supabase pgvector. The `agent_memory` table with custom vector embeddings is redundant.

**Add Mem0's required table.** Mem0 OSS creates its own `memories` table in Supabase with pgvector. Run Mem0's setup migration:

```sql
-- Enable pgvector extension (if not already)
CREATE EXTENSION IF NOT EXISTS vector;

-- Mem0 creates this table automatically via its Python SDK
-- Shown here for documentation purposes:
-- CREATE TABLE IF NOT EXISTS memories (
--   id TEXT PRIMARY KEY,
--   embedding VECTOR(1536),
--   metadata JSONB,
--   created_at TIMESTAMPTZ DEFAULT NOW(),
--   updated_at TIMESTAMPTZ DEFAULT NOW()
-- );
```

**Add `wiki_pages` table** for storing generated wiki content:

```sql
CREATE TABLE wiki_pages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,           -- e.g., 'products/sku-017-baklava'
  title TEXT NOT NULL,
  category TEXT NOT NULL,              -- 'product', 'competitor', 'playbook', 'brief'
  content TEXT NOT NULL,               -- Markdown content
  generated_from JSONB,               -- Array of Mem0 memory IDs used to compile
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_wiki_pages_category ON wiki_pages(category);
CREATE INDEX idx_wiki_pages_slug ON wiki_pages(slug);
```

### 3.3 Data Access Pattern

Agents access Supabase via direct Python queries using `supabase-py` (the official Supabase Python client). No MCP for batch agent runs — it adds unnecessary network hops for scheduled jobs.

```python
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
```

The dashboard accesses Supabase via the Supabase JS client with RLS policies applied per user role.

---

## 4. Layer 2: Sync Layer (SP-API)

### 4.1 Existing Sync Jobs — No Changes

The existing scheduled Supabase jobs that sync SP-API data into the database are retained. These run before agent jobs to ensure fresh data.

**Sync schedule (all times UTC):**

| Job | Schedule | Target Tables |
|-----|----------|---------------|
| Inventory sync | Daily 04:30 | `inventory_snapshots` |
| Orders sync | Daily 04:45 | `orders`, `order_items` |
| Sales aggregation | Daily 05:00 | `sales_daily`, `fees_daily`, `profit_daily` |
| Product snapshots | Daily 05:00 | `product_snapshots` |
| PPC stats sync | Daily 05:10 | `ppc_campaign_stats_daily`, `ppc_keyword_stats_daily` |
| Competitor snapshots | Daily 05:15 | `competitor_snapshots` |
| Reviews sync | Weekly Sun 04:00 | `reviews`, `competitor_reviews` |

### 4.2 SP-API Write Operations

All SP-API writes go through the Executor service (Layer 5). Agents never call SP-API directly. The three write operations:

1. **PPC bid/budget changes** — Advertising API
2. **Price changes** — Listings API (`PATCH /listings/{sku}`)
3. **Listing content updates** — Listings API

Each write requires prior human approval via the `approval_requests` table.

---

## 5. Layer 3: Knowledge Layer (Mem0 + pgvector)

### 5.1 Architecture

Mem0 OSS serves as the knowledge accumulation engine. It stores atomic facts extracted from agent outputs, deduplicates them, and provides semantic search for retrieval.

```
Agent Output (analysis text)
        │
        ▼
   Mem0 Python SDK
        │
        ├── Extracts atomic facts from text
        ├── Deduplicates against existing memories
        ├── Generates embeddings (text-embedding-3-small via OpenAI)
        ├── Stores in Supabase pgvector
        └── Returns confirmation
```

### 5.2 Mem0 Configuration

```python
import os
from mem0 import Memory

mem0_config = {
    "llm": {
        "provider": "anthropic",
        "config": {
            "model": "claude-sonnet-4-20250514",
            "api_key": os.environ["ANTHROPIC_API_KEY"],
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "model": "text-embedding-3-small",
            "api_key": os.environ["OPENAI_API_KEY"],
        }
    },
    "vector_store": {
        "provider": "supabase",
        "config": {
            "connection_string": os.environ["SUPABASE_DB_URL"],
            "collection_name": "memories",
        }
    }
}

memory = Memory.from_config(mem0_config)
```

**Note:** Mem0 uses OpenAI's embedding model because it's the most mature and cheapest embedding option. The LLM for fact extraction uses Claude Sonnet to stay within the Anthropic ecosystem for reasoning.

### 5.3 Memory Metadata Schema

Every memory written to Mem0 includes structured metadata:

```python
memory.add(
    messages=[{"role": "assistant", "content": observation_text}],
    user_id="habib_distribution",  # Single tenant for now
    metadata={
        "agent": "inventory",                    # Which agent wrote this
        "memory_type": "observation",            # observation | pattern | playbook
        "product_ids": ["sku-017"],              # Related products
        "campaign_ids": [],                      # Related campaigns
        "competitor_asins": [],                  # Related competitors
        "confidence": 0.7,                       # 0.0-1.0
        "domain": "inventory",                   # inventory | ppc | competitor | pricing | listing
        "source_run_id": "run_20260410_0530",    # Traceability
        "created_date": "2026-04-10",
        "last_reinforced": "2026-04-10",
        "reinforcement_count": 1,
        "outcome_validated": False,              # Has this been validated by outcome data?
    }
)
```

### 5.4 Memory Retrieval Pattern

Before each agent run, the agent queries Mem0 for relevant context:

```python
# Retrieve memories relevant to the agent's domain
relevant_memories = memory.search(
    query="What do I know about current inventory risks and seasonal patterns?",
    user_id="habib_distribution",
    limit=20
)

# Filter by metadata for domain-specific memories
patterns = memory.search(
    query="inventory patterns and playbooks",
    user_id="habib_distribution",
    limit=10,
    filters={"memory_type": {"in": ["pattern", "playbook"]}}
)
```

### 5.5 Three-Tier Knowledge Promotion

**Tier 1: Observations** (written daily by agents)
- Raw findings from each agent run
- High volume, short-lived
- Example: "SKU-017 velocity increased 15% this week, 42 units vs. 37 last week"
- Confidence: starts at 0.5-0.7

**Tier 2: Patterns** (synthesized weekly)
- Consolidated from multiple observations
- Updated when new evidence arrives
- Example: "SKU-017 shows consistent Q4 velocity increase — 3rd consecutive week of growth, correlating with competitor B0xxx price increase on Oct 1"
- Confidence: 0.7-0.9

**Tier 3: Playbooks** (promoted monthly)
- Validated strategies with outcome evidence
- The crown jewels — what makes the system an expert
- Example: "Ramadan Stocking Protocol: Begin FBA inbound 8 weeks prior, order 3.2x normal quantity. Evidence: 2026 Ramadan saw 2.8x velocity increase, zero stockouts when buffer was applied. Revenue impact: +$4,200 vs. baseline."
- Confidence: 0.9-1.0

### 5.6 L1 Rules (System Prompt — Always Loaded)

Critical business rules that every agent must know on every run, without querying Mem0:

```
L1 BUSINESS RULES (immutable):
- NEVER recommend or execute financial actions without approval
- Minimum FBA days-of-supply alert threshold: 14 days
- Critical FBA days-of-supply threshold: 7 days
- Minimum FBA margin threshold: 15% (do not recommend prices below this)
- FBA inbound lead time: 5-7 business days (standard)
- Landed cost currency: CAD for CA marketplace, USD for US marketplace
- Seasonal products: Baklava (Ramadan +3x, Q4 holiday +1.5x)
- Reorder quantities must be in multiples of case pack size
- All PPC recommendations require approval regardless of amount
- Price changes require approval regardless of direction
```

These are static text in each agent's system prompt. Over time, as playbooks are validated, new L1 rules can be manually promoted from playbook tier.

---

## 6. Layer 4: Agent Layer (Claude Agent SDK)

### 6.1 Agent Runtime Architecture

Each agent is a standalone Python script that:
1. Queries Supabase for current data
2. Queries Mem0 for relevant accumulated knowledge
3. Constructs a prompt with L1 rules + data + memories
4. Calls Claude via the Anthropic API with tool definitions
5. Parses Claude's structured response
6. Writes outputs to appropriate tables

Agents do NOT use the full Agent SDK agent loop for v1. They use the Anthropic Python SDK directly with tool use. This is simpler, cheaper, and sufficient for structured batch analysis. The Agent SDK becomes relevant if agents need multi-step exploration or dynamic tool chaining — we'll upgrade when that need arises.

### 6.2 Agent Code Structure

```
habib-os/
├── agents/
│   ├── base.py              # Shared agent infrastructure
│   ├── inventory_agent.py   # Inventory & stockout prediction
│   ├── ppc_agent.py         # PPC optimization
│   └── competitor_agent.py  # Listing & competitor intel
├── core/
│   ├── config.py            # Environment variables, constants
│   ├── supabase_client.py   # Supabase connection + query helpers
│   ├── mem0_client.py       # Mem0 connection + read/write helpers
│   ├── anthropic_client.py  # Claude API wrapper
│   └── models.py            # Pydantic models for agent I/O
├── executor/
│   ├── executor.py          # Approval watcher + SP-API write executor
│   └── sp_api_client.py     # SP-API write operations
├── telegram/
│   ├── bot.py               # Telegram bot main loop
│   ├── handlers.py          # Message and callback handlers
│   └── formatters.py        # Message formatting (daily brief, alerts)
├── consolidation/
│   ├── weekly_patterns.py   # Weekly observation → pattern synthesis
│   ├── monthly_review.py    # Monthly pattern → playbook promotion
│   └── wiki_compiler.py     # Generate wiki pages from Mem0
├── scripts/
│   ├── setup_mem0.py        # One-time Mem0 setup
│   ├── populate_competitors.py  # Initial competitor ASIN population
│   └── backfill_memories.py     # Seed Mem0 with historical knowledge
├── .env                     # Environment variables (never committed)
├── requirements.txt
└── README.md
```

### 6.3 Base Agent Class

```python
# agents/base.py
import os
import time
import uuid
from datetime import datetime, timezone
from anthropic import Anthropic
from core.supabase_client import get_supabase
from core.mem0_client import get_memory

class BaseAgent:
    """Shared infrastructure for all agents."""

    def __init__(self, agent_name: str, domain: str):
        self.agent_name = agent_name
        self.domain = domain
        self.run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}_{agent_name}"
        self.supabase = get_supabase()
        self.memory = get_memory()
        self.anthropic = Anthropic()
        self.model = "claude-sonnet-4-20250514"

    def run(self):
        """Main execution flow for every agent."""
        start_time = time.time()
        success = True
        error_message = None
        output_summary = ""

        try:
            # Step 1: Fetch current data from Supabase
            data = self.fetch_data()

            # Step 2: Retrieve relevant memories from Mem0
            memories = self.fetch_memories()

            # Step 3: Build prompt and call Claude
            response = self.analyze(data, memories)

            # Step 4: Process Claude's response
            output_summary = self.process_response(response)

            # Step 5: Write observations to Mem0
            self.write_observations(response)

        except Exception as e:
            success = False
            error_message = str(e)
            self.send_failure_alert(e)

        finally:
            # Step 6: Log the run
            duration_ms = int((time.time() - start_time) * 1000)
            self.log_run(success, error_message, output_summary, duration_ms)

    def fetch_data(self) -> dict:
        """Override in subclass. Query Supabase for domain-specific data."""
        raise NotImplementedError

    def fetch_memories(self) -> list:
        """Retrieve relevant memories from Mem0."""
        # Get patterns and playbooks for this domain
        high_value = self.memory.search(
            query=f"{self.domain} patterns strategies insights",
            user_id="habib_distribution",
            limit=15,
            filters={"memory_type": {"in": ["pattern", "playbook"]}}
        )
        # Get recent observations
        recent = self.memory.search(
            query=f"recent {self.domain} observations",
            user_id="habib_distribution",
            limit=10,
            filters={"memory_type": "observation"}
        )
        return high_value.get("results", []) + recent.get("results", [])

    def analyze(self, data: dict, memories: list) -> dict:
        """Override in subclass. Build prompt and call Claude."""
        raise NotImplementedError

    def process_response(self, response: dict) -> str:
        """Override in subclass. Write recommendations/alerts to Supabase."""
        raise NotImplementedError

    def write_observations(self, response: dict):
        """Write agent's observations to Mem0."""
        observations = response.get("observations", [])
        for obs in observations:
            self.memory.add(
                messages=[{"role": "assistant", "content": obs["text"]}],
                user_id="habib_distribution",
                metadata={
                    "agent": self.agent_name,
                    "memory_type": "observation",
                    "product_ids": obs.get("product_ids", []),
                    "campaign_ids": obs.get("campaign_ids", []),
                    "competitor_asins": obs.get("competitor_asins", []),
                    "confidence": obs.get("confidence", 0.6),
                    "domain": self.domain,
                    "source_run_id": self.run_id,
                    "created_date": datetime.now(timezone.utc).isoformat(),
                    "last_reinforced": datetime.now(timezone.utc).isoformat(),
                    "reinforcement_count": 1,
                    "outcome_validated": False,
                }
            )

    def create_approval_request(self, action_type: str, description: str,
                                 payload: dict, estimated_cost: float = None):
        """Create an approval request for a financial action."""
        self.supabase.table("approval_requests").insert({
            "action_type": action_type,
            "agent": self.agent_name,
            "description": description,
            "payload": payload,
            "estimated_cost": estimated_cost,
            "status": "pending",
            "expires_at": (datetime.now(timezone.utc)
                          + timedelta(hours=24)).isoformat(),
        }).execute()

    def create_notification(self, severity: str, title: str, body: str,
                            product_id: str = None, metadata: dict = None):
        """Create a notification for the dashboard/Telegram."""
        self.supabase.table("notifications").insert({
            "agent": self.agent_name,
            "severity": severity,
            "title": title,
            "body": body,
            "status": "unread",
            "product_id": product_id,
            "metadata": metadata or {},
        }).execute()

    def log_run(self, success: bool, error_message: str,
                output_summary: str, duration_ms: int):
        """Log agent run to agent_runs table."""
        self.supabase.table("agent_runs").insert({
            "agent": self.agent_name,
            "task": f"daily_{self.domain}_analysis",
            "trigger_type": "scheduled",
            "input_summary": f"Analyzed {self.domain} data",
            "output_summary": output_summary,
            "duration_ms": duration_ms,
            "success": success,
            "error_message": error_message,
        }).execute()

    def send_failure_alert(self, error: Exception):
        """Send Telegram alert on agent failure."""
        self.create_notification(
            severity="critical",
            title=f"{self.agent_name} failed",
            body=f"Error: {str(error)[:500]}. Will retry in 30 minutes.",
        )
```

---

## 7. Layer 5: Action Layer (Executor Service)

### 7.1 Purpose

The Executor is the only code that writes to Amazon SP-API. It watches the `approval_requests` table for approved actions and executes them.

### 7.2 Design

```python
# executor/executor.py
"""
Watches for approved requests and executes SP-API writes.
Runs as a persistent daemon on Hetzner via systemd.
Checks every 60 seconds for new approvals.
"""

import time
from datetime import datetime, timezone
from core.supabase_client import get_supabase
from executor.sp_api_client import SPAPIClient

class Executor:
    def __init__(self):
        self.supabase = get_supabase()
        self.sp_api = SPAPIClient()

    def run_forever(self):
        """Main loop — poll for approved requests."""
        while True:
            try:
                self.process_approved_requests()
                self.expire_stale_requests()
            except Exception as e:
                print(f"Executor error: {e}")
            time.sleep(60)

    def process_approved_requests(self):
        """Find and execute all approved requests."""
        result = self.supabase.table("approval_requests") \
            .select("*") \
            .eq("status", "approved") \
            .is_("execution_result", "null") \
            .execute()

        for request in result.data:
            self.execute(request)

    def execute(self, request: dict):
        """Execute a single approved action."""
        try:
            action_type = request["action_type"]
            payload = request["payload"]

            if action_type == "ppc_bid_change":
                result = self.sp_api.update_keyword_bid(
                    campaign_id=payload["campaign_id"],
                    keyword_id=payload["keyword_id"],
                    new_bid=payload["recommended_bid"],
                    marketplace=payload["marketplace"]
                )
            elif action_type == "ppc_budget_change":
                result = self.sp_api.update_campaign_budget(
                    campaign_id=payload["campaign_id"],
                    new_budget=payload["recommended_budget"],
                    marketplace=payload["marketplace"]
                )
            elif action_type == "price_change":
                result = self.sp_api.update_price(
                    sku=payload["sku"],
                    new_price=payload["recommended_price"],
                    marketplace=payload["marketplace"]
                )
            elif action_type == "listing_change":
                result = self.sp_api.update_listing(
                    sku=payload["sku"],
                    updates=payload["listing_updates"],
                    marketplace=payload["marketplace"]
                )
            else:
                result = {"error": f"Unknown action type: {action_type}"}

            # Record result
            self.supabase.table("approval_requests").update({
                "execution_result": result,
            }).eq("id", request["id"]).execute()

            # Audit log
            self.supabase.table("audit_log").insert({
                "agent": request["agent"],
                "action": action_type,
                "entity_type": "approval_request",
                "entity_id": request["id"],
                "details": result,
                "approval_id": request["id"],
                "success": "error" not in result,
                "error_message": result.get("error"),
            }).execute()

        except Exception as e:
            self.supabase.table("approval_requests").update({
                "execution_result": {"error": str(e)},
            }).eq("id", request["id"]).execute()

    def expire_stale_requests(self):
        """Mark expired pending requests."""
        self.supabase.table("approval_requests").update({
            "status": "expired"
        }).eq("status", "pending") \
          .lt("expires_at", datetime.now(timezone.utc).isoformat()) \
          .execute()
```

---

## 8. Layer 6: Interface Layer

### 8.1 Telegram Bot

The Telegram bot serves three functions:
1. **Approval flow** — push notifications with inline approve/reject buttons
2. **Critical alerts** — immediate notification for urgent issues
3. **Daily brief** — morning summary of all agent findings

#### Bot Architecture

```python
# telegram/bot.py
"""
Two concurrent loops:
1. Telegram polling (handles user interactions)
2. Notification watcher (polls Supabase for new notifications/approvals)
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler

RAMI_TELEGRAM_ID = os.environ["RAMI_TELEGRAM_ID"]

async def watch_notifications(context):
    """Poll Supabase every 30s for unread critical/warning notifications."""
    supabase = get_supabase()
    result = supabase.table("notifications") \
        .select("*") \
        .eq("status", "unread") \
        .in_("severity", ["critical", "warning"]) \
        .execute()

    for notif in result.data:
        await send_notification(context.bot, notif)
        supabase.table("notifications").update(
            {"status": "read"}
        ).eq("id", notif["id"]).execute()

async def watch_approvals(context):
    """Poll for pending approval requests without telegram_msg_id."""
    supabase = get_supabase()
    result = supabase.table("approval_requests") \
        .select("*") \
        .eq("status", "pending") \
        .is_("telegram_msg_id", "null") \
        .execute()

    for req in result.data:
        msg = await send_approval_request(context.bot, req)
        supabase.table("approval_requests").update(
            {"telegram_msg_id": str(msg.message_id)}
        ).eq("id", req["id"]).execute()
```

#### Daily Brief Format

```
📊 Habib Distribution — April 10, 2026

🔴 CRITICAL
• SKU-017 Baklava: 6 days of stock. Restock 200 units recommended.
  [✅ Approve Restock]

🟡 ATTENTION
• PPC "Baklava CA": ACOS 38% (was 29%). Recommend pausing
  keyword "middle eastern sweets" — low conversion.
• Competitor B0xxx dropped tahini price by 12%.

🟢 ALL CLEAR
• 27/30 SKUs healthy (21+ days supply)
• No listing issues detected
• No review anomalies

📈 YESTERDAY
Revenue: $1,247 | Orders: 34 | PPC Spend: $89 | ACOS: 24%

🧠 LEARNING
• 3 new observations stored
• 1 pattern updated: "Baklava Q4 velocity trend"

⏳ PENDING
• 2 approvals awaiting your response
```

#### Approval Message Format

```
🔔 APPROVAL REQUIRED

Agent: PPC Agent
Action: Bid increase
Campaign: Baklava CA — Exact Match
Keyword: "baklava toronto"

Current bid: $1.20
Recommended: $1.45 (+21%)
Reasoning: This keyword converts at 18% (vs. campaign avg 12%).
ACOS at current bid: 22%. Projected ACOS at new bid: 26%.
Estimated daily impact: +$2.30/day spend, +$8.50/day revenue.

Expires: Apr 11, 10:00 AM

[✅ Approve] [❌ Reject] [🔗 Dashboard]
```

The "Dashboard" button opens a deep link to the approval detail page on the Next.js dashboard.

### 8.2 Dashboard (Next.js on Vercel)

#### MVP Scope — Four Pages Only

**Page 1: Home / Daily Overview**
- Today's quick stats (revenue, orders, PPC spend, inventory health)
- Pending approvals count with links
- Latest notifications (last 24h)
- Link to today's wiki brief

**Page 2: Wiki Viewer**
- Left sidebar: wiki page tree (products, competitors, playbooks, briefs)
- Main area: rendered markdown content
- Each page shows "Last compiled" timestamp and confidence indicators
- Read-only — no editing

**Page 3: Approvals**
- Table of all approval requests, filterable by status (pending/approved/rejected/expired)
- Click to expand full context (agent reasoning, payload, execution result)
- Approve/reject buttons for pending items (backup for Telegram)

**Page 4: Agent Logs**
- Table of agent runs: timestamp, agent, success/failure, duration, token cost
- Click to expand run details
- Simple line chart: daily token spend over last 30 days

#### Dashboard Tech

```
Next.js 14 (App Router)
├── Supabase JS client for data access (with RLS)
├── Tailwind CSS for styling
├── react-markdown for wiki page rendering
└── Deployed on Vercel (free tier sufficient for MVP)
```

---

## 9. Agent Designs (Detailed)

### 9.1 Inventory Agent

**Schedule:** Daily 05:30 UTC

**Data fetched from Supabase:**
- `inventory_snapshots` — current FBA inventory levels (all SKUs)
- `sales_daily` — last 30 days of sales velocity per SKU
- `products` — reorder points, lead times, case pack sizes, landed costs
- `inbound_shipments` — any in-transit shipments
- `supplier_shipments` — any pending supplier orders

**Memories fetched from Mem0:**
- Seasonal patterns for each product
- Historical stockout incidents and their revenue impact
- Validated restock playbooks

**System prompt (core):**

```
You are the Inventory Agent for Habib Distribution, an Amazon seller
with ~30 SKUs of Middle Eastern food products.

Your job: analyze current inventory levels against sales velocity,
predict stockout risks, and recommend restock actions.

L1 RULES:
[...L1 rules from Section 5.6...]

For each SKU, calculate:
1. Current days-of-supply = fulfillable_qty / avg_daily_velocity_30d
2. Projected stockout date
3. Whether a restock is needed given lead time

Consider:
- Inbound shipments already in transit
- Seasonal patterns from your accumulated knowledge
- Competitor stockout opportunities (if relevant memories exist)

OUTPUT FORMAT (strict JSON):
{
  "alerts": [
    {
      "severity": "critical|warning|info",
      "product_id": "...",
      "title": "...",
      "body": "...",
      "days_of_supply": N
    }
  ],
  "restock_recommendations": [
    {
      "product_id": "...",
      "sku": "...",
      "current_stock": N,
      "daily_velocity": N,
      "days_of_supply": N,
      "recommended_qty": N,
      "recommended_ship_date": "YYYY-MM-DD",
      "reasoning": "..."
    }
  ],
  "observations": [
    {
      "text": "...",
      "product_ids": ["..."],
      "confidence": 0.0-1.0
    }
  ]
}
```

**Output processing:**
- `alerts` → written to `notifications` table
- `restock_recommendations` → written to `approval_requests` with `action_type: "fba_replenishment"`
- `observations` → written to Mem0

### 9.2 PPC Agent

**Schedule:** Daily 06:00 UTC

**Data fetched from Supabase:**
- `ppc_campaign_stats_daily` — last 30 days of campaign-level metrics
- `ppc_keyword_stats_daily` — last 30 days of keyword-level metrics
- `ppc_campaigns` — campaign configs, budgets, states
- `ppc_keywords` — keyword bids, match types
- `products` — margin data (to calculate profitability targets)
- `sales_daily` — organic vs. PPC unit split

**Memories fetched from Mem0:**
- Keyword performance patterns (which keywords convert seasonally)
- Bid strategy playbooks
- Budget allocation patterns that worked

**System prompt (core):**

```
You are the PPC Agent for Habib Distribution, managing Sponsored
Products campaigns on Amazon Canada and Amazon US.

Your job: analyze campaign and keyword performance, identify
optimization opportunities, and recommend bid/budget changes.

L1 RULES:
[...L1 rules from Section 5.6...]

Key metrics to analyze:
- ACOS (Advertising Cost of Sales) — target varies by product margin
- TACoS (Total ACOS) — PPC spend / total revenue
- Conversion rate by keyword
- Click-through rate trends
- Wasted spend (keywords with spend but no conversions in 14+ days)

For each recommendation:
- Show current metric, recommended change, projected impact
- Tie to product-level profitability
- Flag if a keyword is cannibalizing organic sales

OUTPUT FORMAT (strict JSON):
{
  "campaign_summary": {
    "total_spend_30d": N,
    "total_sales_30d": N,
    "overall_acos": N,
    "overall_tacos": N
  },
  "recommendations": [
    {
      "type": "bid_change|budget_change|pause_keyword|add_negative",
      "campaign_id": "...",
      "keyword_id": "...",
      "current_value": N,
      "recommended_value": N,
      "reasoning": "...",
      "projected_impact": "..."
    }
  ],
  "alerts": [...],
  "observations": [...]
}
```

**Output processing:**
- `recommendations` with financial impact → `approval_requests`
- `alerts` → `notifications`
- `observations` → Mem0

### 9.3 Listing & Competitor Intel Agent

**Schedule:** Daily 06:30 UTC

**Data fetched from Supabase:**
- `competitor_snapshots` — latest + 30-day history for all tracked competitors
- `competitors` — competitor ASIN mappings
- `product_snapshots` — own BSR, rating, review count, buy box status
- `reviews` — own review trends
- `competitor_reviews` — competitor review trends
- `products` — current prices, listing status

**Memories fetched from Mem0:**
- Competitor behavior patterns (pricing cycles, stockout patterns)
- Listing health incidents and resolutions
- Pricing opportunity playbooks

**System prompt (core):**

```
You are the Listing & Competitor Intelligence Agent for Habib
Distribution.

Your job has two parts:
1. COMPETITOR MONITORING: Detect actionable changes in competitor
   behavior — price drops, stockouts, review velocity changes,
   buy box losses.
2. LISTING HEALTH: Monitor our own listings for suppression, buy box
   loss, BSR anomalies, review sentiment shifts.

L1 RULES:
[...L1 rules from Section 5.6...]

COMPETITOR ANALYSIS:
For each tracked competitor, compare today's snapshot to 7-day and
30-day baselines. Flag:
- Price changes > 5%
- Out-of-stock events (was in stock, now isn't)
- Review count jumps (possible manipulation)
- BSR improvements > 20% (they're gaining share)
- Buy box loss (opportunity if we have better offer)

OWN LISTING HEALTH:
For each of our products, check:
- BSR direction (improving, stable, declining)
- Buy box ownership (are we still winning it?)
- Review sentiment (any new negative themes?)
- Price competitiveness vs. tracked competitors

PRICING OPPORTUNITIES:
When a competitor goes OOS or raises price significantly,
recommend a price adjustment if our margins allow.

OUTPUT FORMAT (strict JSON):
{
  "competitor_alerts": [
    {
      "competitor_asin": "...",
      "our_product_id": "...",
      "alert_type": "price_drop|stockout|review_spike|bsr_jump|buybox_lost",
      "details": "...",
      "recommended_action": "...",
      "severity": "critical|warning|info"
    }
  ],
  "listing_health": [
    {
      "product_id": "...",
      "status": "healthy|warning|critical",
      "issues": ["..."],
      "bsr_trend": "improving|stable|declining"
    }
  ],
  "pricing_recommendations": [
    {
      "product_id": "...",
      "current_price": N,
      "recommended_price": N,
      "reasoning": "...",
      "estimated_margin_at_new_price": N
    }
  ],
  "observations": [...]
}
```

**Output processing:**
- `competitor_alerts` with severity critical/warning → `notifications`
- `pricing_recommendations` → `approval_requests` with `action_type: "price_change"`
- `listing_health` issues → `notifications`
- `observations` → Mem0

---

## 10. Knowledge Compounding System

### 10.1 Weekly Consolidation (Saturday 20:00 UTC)

```python
# consolidation/weekly_patterns.py
"""
Reads all observations from the past week.
Groups by product/domain.
Synthesizes patterns using Claude Sonnet.
Writes pattern memories to Mem0.
"""

def run_weekly_consolidation():
    memory = get_memory()
    anthropic = Anthropic()

    # Get all observations from past 7 days
    recent_observations = memory.search(
        query="all recent observations this week",
        user_id="habib_distribution",
        limit=100,
        filters={"memory_type": "observation"}
    )

    # Get existing patterns to update
    existing_patterns = memory.search(
        query="all current patterns",
        user_id="habib_distribution",
        limit=50,
        filters={"memory_type": "pattern"}
    )

    # Ask Claude to synthesize
    prompt = f"""
    You are the Knowledge Consolidation Engine for Habib Distribution.

    Here are this week's observations from all agents:
    {format_memories(recent_observations)}

    Here are existing patterns:
    {format_memories(existing_patterns)}

    Your job:
    1. Identify new patterns emerging from this week's observations
    2. Update existing patterns with new evidence (increase confidence
       if reinforced, note contradictions if found)
    3. Flag patterns that were NOT reinforced this week
       (potential decay candidates)

    For each pattern, provide:
    - A clear statement of the pattern
    - Supporting evidence (which observations)
    - Confidence score (0.0-1.0)
    - Related product_ids, campaign_ids, competitor_asins

    Output strict JSON array of patterns.
    """

    response = anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse and write patterns to Mem0
    patterns = parse_patterns(response)
    for pattern in patterns:
        memory.add(
            messages=[{"role": "assistant", "content": pattern["text"]}],
            user_id="habib_distribution",
            metadata={
                "agent": "consolidation",
                "memory_type": "pattern",
                "confidence": pattern["confidence"],
                "domain": pattern["domain"],
                "product_ids": pattern.get("product_ids", []),
                # ... other metadata
            }
        )
```

### 10.2 Monthly Review (1st of Month, 08:00 UTC)

```python
# consolidation/monthly_review.py
"""
Uses Claude Opus for deeper reasoning.
Reads all patterns + outcome data from Supabase.
Promotes validated patterns to playbooks.
Decays unvalidated patterns.
Regenerates all wiki pages.
"""

def run_monthly_review():
    memory = get_memory()
    anthropic = Anthropic()
    supabase = get_supabase()

    # Get all patterns
    patterns = memory.search(
        query="all patterns",
        user_id="habib_distribution",
        limit=200,
        filters={"memory_type": "pattern"}
    )

    # Get outcome data from Supabase
    sales_data = supabase.table("sales_daily").select("*") \
        .gte("date", thirty_days_ago).execute()
    profit_data = supabase.table("profit_daily").select("*") \
        .gte("date", thirty_days_ago).execute()

    # Use Opus for deep synthesis
    prompt = f"""
    You are the Monthly Strategic Review Engine for Habib Distribution.

    Review all accumulated patterns against actual business outcomes.

    PATTERNS:
    {format_memories(patterns)}

    OUTCOME DATA (last 30 days):
    Sales: {format_sales(sales_data)}
    Profit: {format_profit(profit_data)}

    For each pattern:
    1. VALIDATE: Does outcome data support this pattern?
       If yes → promote to playbook with evidence.
    2. CONTRADICT: Does outcome data contradict this pattern?
       If yes → flag for review, reduce confidence.
    3. INSUFFICIENT: Not enough data yet?
       If yes → maintain as pattern, note gap.

    For promoted playbooks, write them as actionable protocols:
    - Clear trigger condition
    - Specific actions to take
    - Expected outcome with evidence
    - When to revisit

    Output strict JSON.
    """

    response = anthropic.messages.create(
        model="claude-opus-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}]
    )

    # Process: promote, decay, or maintain each pattern
    results = parse_review_results(response)
    process_promotions(results, memory)
    process_decays(results, memory)

    # Regenerate wiki
    compile_wiki(memory, supabase)
```

### 10.3 Wiki Compiler

```python
# consolidation/wiki_compiler.py
"""
Reads Mem0 memories organized by entity.
Generates markdown wiki pages.
Stores in wiki_pages table for dashboard rendering.
"""

def compile_wiki(memory, supabase):
    anthropic = Anthropic()

    # Get all products
    products = supabase.table("products").select("*").execute()

    for product in products.data:
        # Get all memories related to this product
        product_memories = memory.search(
            query=f"everything about {product['product_name']} {product['sku']}",
            user_id="habib_distribution",
            limit=50
        )

        if not product_memories.get("results"):
            continue

        prompt = f"""
        Compile a wiki page for this product. Include all accumulated
        knowledge organized into sections:

        Product: {product['product_name']} (SKU: {product['sku']})
        Current data: Price ${product['amazon_price']}, Margin {product['fba_margin_pct']}%

        Accumulated knowledge:
        {format_memories(product_memories)}

        Write a comprehensive markdown page with sections:
        - Overview (one paragraph)
        - Inventory Patterns (seasonal trends, velocity patterns)
        - PPC Performance (what keywords work, ACOS trends)
        - Competitor Landscape (who competes, their behavior)
        - Validated Playbooks (proven strategies)
        - Open Questions (things we're still learning)

        Include confidence indicators: ✅ High confidence, ⚠️ Medium, ❓ Low
        Include dates for when knowledge was last updated.
        """

        response = anthropic.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )

        wiki_content = response.content[0].text

        # Upsert wiki page
        supabase.table("wiki_pages").upsert({
            "slug": f"products/{product['sku'].lower()}",
            "title": product['product_name'],
            "category": "product",
            "content": wiki_content,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, on_conflict="slug").execute()

    # Similarly compile: competitor pages, playbook pages, weekly brief
    compile_competitor_pages(memory, supabase, anthropic)
    compile_playbook_pages(memory, supabase, anthropic)
    compile_weekly_brief(memory, supabase, anthropic)
```

---

## 11. Infrastructure & Deployment

### 11.1 Hetzner VPS Setup

**Server:** CX22 (2 vCPU, 4GB RAM, 40GB SSD) — current. Upgrade to CX32 if memory pressure occurs.

**OS:** Ubuntu 24.04 LTS

**Services running:**
1. Agent cron jobs (Python scripts)
2. Executor daemon (systemd service)
3. Telegram bot (systemd service)
4. Consolidation cron jobs

### 11.2 System Services

```bash
# /etc/systemd/system/habib-executor.service
[Unit]
Description=Habib OS Executor Service
After=network.target

[Service]
Type=simple
User=habib
WorkingDirectory=/home/habib/habib-os
EnvironmentFile=/home/habib/habib-os/.env
ExecStart=/home/habib/habib-os/venv/bin/python -m executor.executor
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

```bash
# /etc/systemd/system/habib-telegram.service
[Unit]
Description=Habib OS Telegram Bot
After=network.target

[Service]
Type=simple
User=habib
WorkingDirectory=/home/habib/habib-os
EnvironmentFile=/home/habib/habib-os/.env
ExecStart=/home/habib/habib-os/venv/bin/python -m telegram.bot
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

### 11.3 Cron Schedule

```cron
# /etc/cron.d/habib-os

# Data sync (existing Supabase jobs handle most of this)
# Agents run after sync completes

# Daily agents (sequential to avoid resource contention)
30 5 * * * habib cd /home/habib/habib-os && ./venv/bin/python -m agents.inventory_agent >> /var/log/habib/inventory.log 2>&1
00 6 * * * habib cd /home/habib/habib-os && ./venv/bin/python -m agents.ppc_agent >> /var/log/habib/ppc.log 2>&1
30 6 * * * habib cd /home/habib/habib-os && ./venv/bin/python -m agents.competitor_agent >> /var/log/habib/competitor.log 2>&1

# Daily brief (after all agents complete)
00 7 * * * habib cd /home/habib/habib-os && ./venv/bin/python -m telegram.daily_brief >> /var/log/habib/brief.log 2>&1

# Weekly consolidation (Saturday 20:00 UTC = Saturday 23:00 Haifa)
00 20 * * 6 habib cd /home/habib/habib-os && ./venv/bin/python -m consolidation.weekly_patterns >> /var/log/habib/weekly.log 2>&1

# Monthly review (1st of month 08:00 UTC)
00 8 1 * * habib cd /home/habib/habib-os && ./venv/bin/python -m consolidation.monthly_review >> /var/log/habib/monthly.log 2>&1

# Retry failed agents (30 min after each slot)
00 6 * * * habib cd /home/habib/habib-os && ./venv/bin/python -m scripts.retry_failed --agent inventory >> /var/log/habib/retry.log 2>&1
30 6 * * * habib cd /home/habib/habib-os && ./venv/bin/python -m scripts.retry_failed --agent ppc >> /var/log/habib/retry.log 2>&1
00 7 * * * habib cd /home/habib/habib-os && ./venv/bin/python -m scripts.retry_failed --agent competitor >> /var/log/habib/retry.log 2>&1

# Log rotation
00 0 * * * habib find /var/log/habib -name "*.log" -size +10M -exec truncate -s 0 {} \;
```

### 11.4 Environment Variables

```bash
# .env (never committed to git)

# Supabase
SUPABASE_URL=https://thenkkiaeuuxvuoxizjd.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
SUPABASE_DB_URL=postgresql://postgres:...@db.thenkkiaeuuxvuoxizjd.supabase.co:5432/postgres

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI (for Mem0 embeddings only)
OPENAI_API_KEY=sk-...

# Telegram
TELEGRAM_BOT_TOKEN=...
RAMI_TELEGRAM_ID=...

# SP-API
SP_API_REFRESH_TOKEN=...
SP_API_CLIENT_ID=...
SP_API_CLIENT_SECRET=...
SP_API_MARKETPLACE_CA=A2EUQ1WTGCTBG2
SP_API_MARKETPLACE_US=ATVPDKIKX0DER
```

---

## 12. Error Handling & Monitoring

### 12.1 Agent Failure Handling

```
Agent fails
    │
    ├── Exception caught by BaseAgent.run()
    ├── Error logged to agent_runs table
    ├── Critical notification created (→ Telegram alert)
    ├── 30 minutes later: retry cron fires
    │   ├── Checks agent_runs for failed run today
    │   ├── If failed and no successful retry yet → re-run agent
    │   └── If retry fails → second Telegram alert, skip until tomorrow
    └── Next scheduled run proceeds independently (agents are independent)
```

### 12.2 Executor Failure Handling

```
SP-API write fails
    │
    ├── Error recorded in approval_requests.execution_result
    ├── Audit log entry with success=false
    ├── Telegram notification: "Execution failed for [action]. Error: [msg]"
    └── Does NOT auto-retry (financial actions need manual review)
```

### 12.3 Monitoring (Telegram-native)

No external monitoring tools. Telegram IS the monitoring layer.

**Automated health check** (daily at 23:00 UTC):

```python
# scripts/health_check.py
"""
Runs daily. Checks:
1. Did all 3 agents run successfully today?
2. Are Supabase sync jobs current? (sync_log)
3. Mem0 memory count trend (growing, not shrinking)
4. Token spend today (from agent_runs)
5. Any pending approvals older than 12h?
Sends summary to Telegram.
"""
```

**Weekly ops report** (Sunday 10:00 UTC):

```
🏥 WEEKLY HEALTH — Apr 6-12, 2026

Agent Runs: 21/21 successful ✅
Sync Jobs: 42/42 current ✅
Memories: 847 total (+23 this week)
  - Observations: 689
  - Patterns: 142
  - Playbooks: 16

Token Spend: $18.40 this week
  - Inventory Agent: $4.20
  - PPC Agent: $5.80
  - Competitor Agent: $3.90
  - Consolidation: $4.50

Approvals: 8 processed, 1 expired
```

---

## 13. Security & Safety Invariants

### 13.1 The Golden Rule

**No financial action without explicit human approval.** This is enforced at three levels:

1. **Agent level:** Agents never receive SP-API write credentials. They can only write to `approval_requests`.
2. **Executor level:** The Executor only processes rows with `status = 'approved'`.
3. **Telegram level:** The approve button is the only way to set `status = 'approved'` (plus dashboard backup).

### 13.2 Access Control

| Component | Has SP-API Read? | Has SP-API Write? | Has Supabase Write? |
|-----------|:---:|:---:|:---:|
| Sync Jobs | ✅ | ❌ | ✅ (sync tables only) |
| Agents | ❌ | ❌ | ✅ (agent tables only) |
| Executor | ❌ | ✅ | ✅ (approval_requests only) |
| Telegram Bot | ❌ | ❌ | ✅ (approval status only) |
| Dashboard | ❌ | ❌ | Read only (via RLS) |

### 13.3 Supabase RLS Policies

- Dashboard users: read-only access to all tables based on `role` in `users` table
- Service key (agents, executor): full access — used server-side only, never exposed to frontend
- Anon key (dashboard): RLS-filtered read access

### 13.4 Secret Management

- All secrets in `.env` file on Hetzner, readable only by `habib` user
- Vercel environment variables for dashboard's Supabase anon key
- No secrets committed to git, ever
- SP-API refresh token stored in `.env`, rotated per Amazon's schedule

---

## 14. Implementation Plan (Phased)

### Phase 0: Foundation (Days 1-3)

**Goal:** Project scaffolding, Mem0 integration, base agent class working.

- [ ] Create project repo with directory structure from Section 6.2
- [ ] Set up Python virtual environment, install dependencies
- [ ] Configure `.env` with all credentials
- [ ] Set up `core/supabase_client.py` — test connection, basic queries
- [ ] Set up `core/mem0_client.py` — initialize Mem0 with Supabase pgvector config
- [ ] Test Mem0: write a memory, search for it, verify it's in Supabase
- [ ] Run Mem0's Supabase migration (enable pgvector, create memories table)
- [ ] Remove `agent_memory` table (replaced by Mem0)
- [ ] Create `wiki_pages` table
- [ ] Implement `agents/base.py` — full BaseAgent class
- [ ] Test BaseAgent with a dummy agent that reads Supabase and writes to Mem0

**Deliverable:** Working foundation — Supabase connected, Mem0 storing/retrieving memories, base agent class tested.

### Phase 1: Inventory Agent (Days 4-7)

**Goal:** First agent running end-to-end, producing real recommendations.

- [ ] Implement `agents/inventory_agent.py`
  - [ ] `fetch_data()` — query inventory_snapshots, sales_daily, products, inbound_shipments
  - [ ] `analyze()` — build prompt with L1 rules + data + memories, call Claude
  - [ ] `process_response()` — parse JSON, write alerts to notifications, restocks to approval_requests
  - [ ] `write_observations()` — write inventory observations to Mem0
- [ ] Test with real production data (read-only, no actions)
- [ ] Validate output: do the stockout predictions make sense?
- [ ] Tune system prompt based on output quality
- [ ] Set up cron job (05:30 UTC)
- [ ] Set up retry cron (06:00 UTC)
- [ ] Set up log directory `/var/log/habib/`

**Deliverable:** Inventory Agent running daily, producing stockout alerts and restock recommendations.

### Phase 2: Telegram Bot + Approval Flow (Days 8-11)

**Goal:** Rami can see and act on agent recommendations from his phone.

- [ ] Create Telegram bot via BotFather
- [ ] Implement `telegram/bot.py` — polling loop + notification/approval watchers
- [ ] Implement `telegram/handlers.py` — approve/reject callback handlers
- [ ] Implement `telegram/formatters.py` — message formatting
- [ ] Implement daily brief compiler (`telegram/daily_brief.py`)
- [ ] Test: Inventory Agent creates approval → Telegram shows it → approve → status updates
- [ ] Set up systemd service for Telegram bot
- [ ] Implement health check script

**Deliverable:** Full approval loop working — agent recommends, Telegram notifies, human approves, status updates.

### Phase 3: Executor Service (Days 12-14)

**Goal:** Approved actions actually execute on Amazon.

- [ ] Implement `executor/sp_api_client.py` — PPC bid/budget changes, price changes
- [ ] Implement `executor/executor.py` — approval watcher + execution loop
- [ ] Test with a real (small) PPC bid change on a low-stakes campaign
- [ ] Verify audit log entries
- [ ] Verify execution_result written back to approval_requests
- [ ] Set up systemd service for Executor
- [ ] Test expiration of stale approvals

**Deliverable:** End-to-end: agent recommends → Telegram → approve → SP-API executes → result logged.

### Phase 4: PPC Agent (Days 15-18)

**Goal:** Second agent running, PPC recommendations flowing.

- [ ] Implement `agents/ppc_agent.py`
- [ ] Test with real PPC data
- [ ] Tune system prompt for PPC-specific analysis quality
- [ ] Verify integration: PPC recommendations → approval_requests → Telegram
- [ ] Set up cron (06:00 UTC)

**Deliverable:** PPC Agent running daily alongside Inventory Agent.

### Phase 5: Competitor Intel Agent (Days 19-23)

**Goal:** Third agent running. Full agent layer complete.

- [ ] Populate `competitors` table with initial competitor ASINs (run `scripts/populate_competitors.py`)
- [ ] Verify competitor_snapshots are being populated by sync jobs
- [ ] Implement `agents/competitor_agent.py`
- [ ] Test with real competitor data
- [ ] Tune system prompt
- [ ] Verify pricing recommendations flow through approval pipeline
- [ ] Set up cron (06:30 UTC)
- [ ] Update daily brief to include all three agents

**Deliverable:** All three agents running daily. Full agent layer operational.

### Phase 6: Knowledge Compounding (Days 24-28)

**Goal:** The system starts learning and accumulating intelligence.

- [ ] Implement `consolidation/weekly_patterns.py`
- [ ] Run first weekly consolidation manually — review output quality
- [ ] Tune consolidation prompt
- [ ] Implement `consolidation/monthly_review.py`
- [ ] Implement `consolidation/wiki_compiler.py`
- [ ] Run first wiki compilation — review generated pages
- [ ] Set up consolidation crons
- [ ] Implement weekly health report

**Deliverable:** Knowledge layer active — observations consolidating into patterns, wiki pages generating.

### Phase 7: Dashboard MVP (Days 29-35)

**Goal:** Visual interface for deep review and wiki browsing.

- [ ] Scaffold Next.js project on Vercel
- [ ] Configure Supabase JS client with RLS
- [ ] Build Page 1: Home / Daily Overview
- [ ] Build Page 2: Wiki Viewer (markdown rendering, page tree navigation)
- [ ] Build Page 3: Approvals (table + detail view + approve/reject)
- [ ] Build Page 4: Agent Logs (run history + cost chart)
- [ ] Deploy to Vercel
- [ ] Test RLS policies for different user roles

**Deliverable:** Dashboard live. Rami's father and brother can view the wiki and business intelligence.

### Phase 8: Hardening & Polish (Days 36-42)

**Goal:** Production-grade reliability.

- [ ] Backfill Mem0 with any manual business knowledge Rami wants to seed
- [ ] Review and tune all three agent system prompts after 1-2 weeks of real data
- [ ] Add Arabic support to notifications (title_ar, body_ar fields exist)
- [ ] Load test: run all agents sequentially, verify CX22 handles it
- [ ] Document all runbooks: "what to do if X fails"
- [ ] Set up git repo backup (push to GitHub private)
- [ ] Final review of all security: RLS policies, env file permissions, no leaked secrets

**Deliverable:** Production-ready system running autonomously.

---

## 15. Cost Projections

### 15.1 Monthly Infrastructure

| Item | Cost |
|------|------|
| Hetzner CX22 | ~€4.50/mo |
| Supabase (Free tier → Pro if needed) | $0-25/mo |
| Vercel (Free tier) | $0/mo |
| **Infrastructure Total** | **~$5-30/mo** |

### 15.2 Monthly AI/API Costs

Assumptions: 30 SKUs, 3 agents running daily, Sonnet for daily, Opus for monthly.

| Item | Estimate |
|------|----------|
| Claude Sonnet (3 agents × 30 days × ~5K tokens in/out each) | ~$15-25/mo |
| Claude Opus (monthly consolidation, ~50K tokens) | ~$5-10/mo |
| OpenAI text-embedding-3-small (Mem0 embeddings) | ~$1-3/mo |
| **AI Total** | **~$20-40/mo** |

### 15.3 Total Monthly Cost

**$25-70/month** for a fully autonomous business operating system. This scales linearly with SKU count and agent complexity.

---

## 16. Future Considerations

### 16.1 When to Add (Not Now)

| Feature | Trigger to Add |
|---------|---------------|
| **FalkorDB graph memory** | When you hit 100+ SKUs or semantic search stops surfacing cross-domain connections |
| **Compiler agent** | When reading three agent outputs takes more than 2 minutes and cross-domain synthesis is needed |
| **Managed Agents** | When you onboard first agency client and need per-tenant isolation |
| **Amazon US expansion** | When US marketplace is active — add marketplace filtering to all agents |
| **Walmart integration** | After Amazon is fully automated — new sync layer + marketplace-specific agent logic |
| **Diaspora Trend Spotter** | When brand expansion is active and you need market research automation |
| **New Brand Onboarding** | When you're actually onboarding a new brand |
| **Review Intelligence** | When review volume justifies a dedicated agent (vs. current Competitor Intel coverage) |

### 16.2 Productization Path (Future)

When ready to deploy for agency clients:

- **Shared:** Agent code, system prompt templates, wiki structure, dashboard UI, Telegram bot framework
- **Per-client:** Supabase project, Mem0 user_id namespace, SP-API credentials, Telegram bot instance, L1 rules
- **Deployment:** One Supabase project per client, shared Hetzner VPS (or Managed Agents for isolation), client-specific `.env`

This architecture supports multi-tenant deployment with zero code forking. Each client gets their own data namespace, their own knowledge accumulation, and their own approval flow.

---

## Appendix A: Dependencies

```
# requirements.txt
anthropic>=0.45.0
supabase>=2.0.0
mem0ai>=1.0.0
python-telegram-bot>=21.0
python-dotenv>=1.0.0
pydantic>=2.0.0
httpx>=0.27.0
```

## Appendix B: Key Decisions Log

| Decision | Choice | Reasoning |
|----------|--------|-----------|
| Agent count | 3 (Inventory, PPC, Competitor Intel) | Matches day-one pain points. Others deferred. |
| Agent runtime | Anthropic Python SDK (not Agent SDK, not Managed Agents) | Simplest option for structured batch jobs. No sandbox needed. |
| Knowledge layer | Mem0 OSS + Supabase pgvector | Purpose-built for agent memory. Native Supabase integration. |
| Graph memory | Deferred | Overkill for 30 SKUs. Add when entity count justifies traversal. |
| Wiki | Generated view from Mem0, stored in wiki_pages table | Single source of truth (Mem0). No parallel filesystem. |
| Approval channel | Telegram (primary) + Dashboard (backup) | Mobile-native for solo operator. Dashboard for deep review. |
| Model | Sonnet daily, Opus monthly consolidation only | Cost-effective. Sonnet is sufficient for structured analysis. |
| Data access | Direct Supabase queries (not MCP) | No unnecessary network hops for batch jobs. |
| Scheduling | Cron on Hetzner | Simplest possible. Systemd timers as alternative. |
| Monitoring | Telegram alerts + health check script | No external tools. Telegram IS the monitoring layer. |
| Watchdog agent | Replaced by Competitor Intel | No agency to watch. Competitor monitoring + listing health adds more value. |

---

*This document is the complete architectural specification for the Habib Distribution OS. Implementation begins with Phase 0.*

<!-- GSD:project-start source:PROJECT.md -->
## Project

**Habib Distribution OS**

An autonomous business operating system for a family-run Amazon FBA distribution company (~30 SKUs of Middle Eastern food products). Three AI agents run daily, accumulate knowledge over time via Mem0, and surface intelligence to three operators — Rami (technical/ops), Father (finance), and Brother (sales/marketing) — through Telegram and a Next.js dashboard. The system is live with foundation through Phase 3 built and running on Hetzner. The remaining work is the intelligence layer (knowledge compounding) and the visibility layer (dashboard) that turn the system from a daily reporter into a compounding business brain.

**Core Value:** Knowledge that compounds over time. After 6 months, the system should know more about Habib Distribution's market — seasonal patterns, competitor behavior, PPC dynamics, stockout risk factors — than any competitor's AI, because every observation is captured, synthesized against real outcomes, and promoted into validated playbooks. The wiki becomes the institutional memory of the business.

### Constraints

- **Solo operator**: Rami maintains everything — no DevOps team. Every component must be self-healing or fail with a clear Telegram alert.
- **Hetzner CX22**: 2 vCPU, 4GB RAM. Sequential agent runs (not parallel) to avoid resource contention. Upgrade to CX32 if memory pressure occurs.
- **Approval invariant**: No financial action without explicit human approval. Hard requirement — enforced at agent level, executor level, and Telegram level.
- **SP-API access**: Agents never hold SP-API write credentials. Writes go through Executor only.
- **Cost target**: $25-70/month total (infra + AI). Track token spend per agent run in agent_runs table.
- **Model allocation**: Claude Sonnet for daily agent runs and weekly consolidation; Claude Opus for monthly review only (cost control).
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Language & Runtime
- **Python 3.12** — all backend services (agents, sync, executor, bot)
- **Node.js** — only for GSD tooling (`.claude/` directory), not business logic
## Dependency Manifest
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Language Style
- Python 3.12, no type: ignore comments, modern union syntax (`X | Y`)
- `from __future__ import annotations` used in async modules (sync layer)
- f-strings throughout; no `.format()` or `%` formatting
- `pydantic>=2.0.0` in deps but not currently used in implemented code — future use
## Module-Level Patterns
### Singletons (lazy, module-level)
### Config as Module Constants
### Agent Pattern (Template Method)
## Logging
### Sync Layer — structlog
### Agent/Executor Layer — stdlib logging + print
## Error Handling
### Agents: catch-all in BaseAgent.run()
### Mem0: graceful None fallback
### Sync Layer: tenacity retry on HTTP
### DB writes: wrapped in try/except with print
## Claude Prompt Conventions
### JSON-only output instruction
### Defensive parsing (strip markdown fences)
### L1 Rules injection
## Telegram Message Formatting
- HTML parse mode everywhere (`parse_mode="HTML"`)
- `<b>Bold</b>` for labels, no markdown
- Emoji-coded severity: 🔴 critical, 🟡 warning, 🔵 info, 🟢 healthy
- Inline keyboards use `callback_data="action:id"` pattern (e.g., `"approve:uuid"`)
## Supabase Query Patterns
## Naming Conventions Summary
| Context | Convention | Example |
|---------|------------|---------|
| Module files | snake_case | `inventory_agent.py` |
| Classes | PascalCase | `InventoryAgent`, `SPAPIClient` |
| Functions | snake_case | `fetch_data()`, `write_observations()` |
| Constants | UPPER_SNAKE | `L1_RULES`, `MODEL_DAILY` |
| DB table names | snake_case | `approval_requests`, `agent_runs` |
| Agent names in DB | snake_case string | `"inventory_agent"` |
| Memory types | lowercase | `"observation"`, `"pattern"`, `"playbook"` |
| Action types | snake_case | `"fba_replenishment"`, `"price_change"` |
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern
## Layers
```
```
## Data Flow (Daily Cycle)
```
```
## Abstractions
### BaseAgent (`agents/base.py`)
- `fetch_data() → dict` — Supabase queries
- `analyze(data, memories) → dict` — Claude call, returns structured JSON
- `process_response(response) → str` — write to Supabase, return summary string
### Sync Layer (`sync/spapi/`)
### Executor (`executor/executor.py`)
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
```
## Key Design Decisions
- **Agents don't call SP-API.** Only the Executor has SP-API write credentials.
- **No agent-to-agent communication.** Each agent is independent; they share state via Supabase only.
- **Mem0 is optional.** `get_memory()` returns `None` if connection fails; agents degrade gracefully.
- **Sync layer is async, agents are sync.** Sync layer uses `asyncio` + `httpx` for throughput; agents are simpler synchronous scripts.
- **No Claude tool_use schema.** Claude returns structured JSON via system prompt instruction + manual `json.loads()` parsing.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
