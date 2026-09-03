# Research behind the Anabtawi OS v2.1 design

Seven sourced surveys produced on 2026-09-02/03 by parallel research agents, each claim tagged
VERIFIED (fetched primary source), REPORTED (secondary source or search excerpt), or UNKNOWN.

| File | Covers |
|---|---|
| datadoe.md | DataDoe (Deltologic) MCP tool contract, data, writes, pricing, alternatives |
| advertising.md | Official Amazon Ads MCP, PPC platforms, keyword tools, campaign playbook, Walmart Connect |
| spapi-writes.md | SP-API MCP servers, private app registration and roles, BSA Section 19 Agent Policy, Notifications, Walmart Marketplace |
| supply-finance.md | Profit analytics, forecasting tools, reimbursements, accounting stack, freight, FDA/CFIA compliance |
| catalog-intel.md | Keyword/rank tools, free Brand Analytics, Keepa, repricers, listing production, catalog health, Grocery category |
| customer-health-runtime.md | Review tools, messaging APIs, Vine, account health, GST/HST and US tax, Claude runtime options, multi-agent patterns |
| grok.md | xAI Grok Bot, Tasks, API, multi-agent capability, verdict |
| comms-design.md | Draft of the inter-department communication design |
| orchestrators.md | Paperclip, OpenClaw, Hermes, NanoClaw, n8n, Windmill, Temporal and others; subscription-CLI subprocess evidence; security posture |
| subscription-clis.md | Claude Code, Codex, Grok Build, Gemini CLI, OpenCode, Goose and others: headless modes, terms, limits, capacity model |
| frameworks-standards.md | LangGraph, CrewAI, Pydantic AI, LiteLLM, MCP, A2A, Agent Skills, AGENTS.md, memory, DBOS, Langfuse |
| hosting-ops.md | Mac mini vs VPS vs PaaS, launchd, Docker, secrets, Tailscale, backups, drift, maintenance contract |
| interface-knowledge.md | Telegram approvals, brief delivery, MkDocs + Cloudflare Access, repo layout, ledgers, compounding, multi-brand |

Caveat: several agents framed recommendations around the retired v1 stack (Supabase, Hetzner
executor) because the repo's CLAUDE.md was in their context. The v2.1 design document translates
every finding into the zero-server architecture. Vendor sites blocked from the research
environment (datadoe.com, x.ai, developer-docs.amazon.com, sellercentral.amazon.com) are cited via
search excerpts and marked REPORTED.

The design itself: docs/ANABTAWI-OS-V3-DESIGN.html (rendered copy published at
https://claude.ai/code/artifact/4fe472f2-0d31-4de8-ad19-da068f8be074).
