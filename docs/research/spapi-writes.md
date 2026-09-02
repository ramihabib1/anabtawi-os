# SP-API Write Path for a Claude Agent — Research Report

> Scope: how a Claude-based agent should perform WRITE operations (and read operational data) on an Amazon seller account via SP-API, plus Walmart Marketplace. Audience: Habib Distribution OS (Amazon CA, expanding to US).
> Date started: 2026-09-02. Claims tagged VERIFIED (fetched primary source), REPORTED (secondary source / listing page), UNKNOWN (could not confirm).

---

## 1. MCP servers wrapping SP-API — full landscape

Note: `glama.ai`, `smithery.ai`, `mcpservers.org` pages themselves were **egress-blocked** in this environment (network proxy), so those listings are sourced via search-engine snippets (REPORTED) even where the underlying GitHub repo behind them was fetched directly (VERIFIED). `mcpmarket.com`, `pulsemcp.com`, `lobehub.com`, `mcp.so` and npm/PyPI were reachable only via search snippets, not direct fetch — everything from them is REPORTED.

### 1.1 Open-source, self-run servers (GitHub)

| Server | Write ops found | Auth | Hosting | Maturity | Source |
|---|---|---|---|---|---|
| **ailumia/amazon-sp-api-mcp** | Broadest found: full **353 operations / 49 SP-API domains** via a generic operation-invoke pattern, including `patchListingsItem` (Listings Items — price/content), **Feeds** (full submission workflow), **Fulfillment Inbound v2024-03-20** (shipment creation), Easy Ship, **Messaging**, **A+ Content**, **Notifications**. All POST/PUT/PATCH require `confirm=true`; DELETE gets a stricter classification + confirmation; `dryRun=true` previews without sending. JSON audit log with SHA-256 payload hashing on every write, credentials never passed as tool args. | **LWA-only**, no AWS IAM required | Self-hosted: Node 20+, `npm run build && node dist/index.js`; optional stateless HTTP transport with bearer token | 2 GitHub stars, 6 commits, Apache-2.0, self-described "production-grade," weekly automated sync of Amazon's API models. Early/tiny adoption despite functional depth. | VERIFIED — https://github.com/ailumia/amazon-sp-api-mcp |
| **coaxon/amazon-mcp** | Listings: read/update fields, **writes gated behind a preview**; **FBA inbound plan creation**; Pro-tier alerts (inventory config, price watches). No documented order edits, no documented direct pricing-only endpoint, no feed submission in core toolset. | LWA (client ID/secret + refresh token from Seller Central authorization), optional MWS-style merchant token | Self-hosted only: local stdio (Claude Desktop/Cursor), HTTP on own VPS with bearer token, systemd unit, Docker compose | 1 star, 0 open issues, MIT license, CodeQL-audited ("0 violations across 6 projects"), explicitly labeled Beta | VERIFIED — https://github.com/coaxon/amazon-mcp |
| **jay-trivedi/amazon_sp_mcp** | **None implemented.** README lists order fulfillment ops and listing creation/updates as "Planned Features," not shipped. Read-only today (orders, returns, sales/inventory metrics, listings read, reports). | LWA OAuth2 + AWS IAM (access key/secret) | Self-hosted, Node.js 18+, stdio via Claude Desktop/Code | 31 stars, 9 forks, 2 open issues, 8 commits, MIT, self-labeled "Phase 1 (MVP)" | VERIFIED — https://github.com/jay-trivedi/amazon_sp_mcp |
| **MarceauSolutions/amazon-seller-mcp** | **None documented** — read-only tool set (inventory summary, orders, order items, product details, FBA fee calc, profit-margin estimate, restock suggestions, sell-through analysis). | LWA refresh-token flow + AWS IAM role ARN, env vars | Self-hosted only, local Python (`python mcp-server/amazon_seller_mcp.py`) | 6 stars, single commit, 0 issues/PRs, MIT | VERIFIED — https://github.com/MarceauSolutions/amazon-seller-mcp |
| **mattcoatsworth/AmazonSeller-mcp-server** | Not confirmed beyond "comprehensive coverage of SP-API endpoints including catalog, inventory, orders, and reports management" — no explicit write-endpoint list surfaced. Provider-agnostic (works with OpenAI/Claude/Gemini). | LWA + AWS credential management (per README description) | Self-hosted, npm install, Node 16+, `.env` config | Adoption/star count not confirmed (page not fetched directly; egress-blocked mirrors on mcp.so, mcp.pizza) | REPORTED — https://github.com/mattcoatsworth/AmazonSeller-mcp-server (repo exists, VERIFIED via search) but tool-level detail REPORTED only |
| **middlegold9/sp-api-mcp-server** ("massive p" on Glama) | Unifies SP-API + Ads API into "20 MCP tools" (per one Glama snippet) or "55+ tools across 19 SP-API scopes" (per a differently-worded Glama snippet — likely two distinct listings/versions); wraps `python-amazon-sp-api`; claims automatic pagination, throttle-aware retry, multi-marketplace, PII compliance. Write-tool list not confirmed. | UNKNOWN | UNKNOWN | UNKNOWN | REPORTED only — https://glama.ai/mcp/servers/middlegold9/sp-api-mcp-server (blocked; search-snippet only) |
| **@eliteamz/amazon-sp-mcp-server** (npm, listed on Smithery) | "Manage your Amazon seller account by creating reports, **updating prices**, and getting inventory summaries." Scope beyond price updates + reports unconfirmed. Published 2025-03-14 per npm registry. | UNKNOWN (not fetched) | Listed on Smithery (hosted registry) but appears to be an installable npm package, not confirmed Smithery-hosted-runtime | UNKNOWN — Smithery/npm pages both egress-blocked | REPORTED — https://smithery.ai/servers/@eliteamz/amazon-sp-mcp-server, homepage www.sethrose.dev |
| **amzn/selling-partner-api-samples** | Amazon's own **official sample code repo** for SP-API use cases (not itself an MCP server, but the canonical reference implementation many of the above wrap). Not MCP-native. | N/A | Self-hosted, various languages | Official Amazon repo (`amzn` GitHub org) | VERIFIED existence via search — https://github.com/amzn/selling-partner-api-samples |
| **@amazon-sp-api-release/sp-api-dev-mcp** | Described as an **Amazon-official** local MCP server bundling multiple SP-API developer tools into one npm package — appears to be a dev-tooling/spec-discovery aid rather than an execution server. Write-execution capability UNKNOWN. | UNKNOWN | npm package, local/self-run | UNKNOWN | REPORTED — surfaced only in a search-engine synthesis line, not independently verified; treat with caution until the npm page is fetched |

### 1.2 Hosted / managed SaaS options (zero self-hosting)

| Service | Write ops | Auth model | Hosting | Pricing | Source |
|---|---|---|---|---|---|
| **DataDoe (Deltologic)** — `mcp.datadoe.com` | Most concretely documented hosted write surface found: `AMAZON_LISTINGS_UPDATE` (title, bullets, description, **price**, generic/item-type keywords), `AMAZON_ORDERS_CANCEL`, `AMAZON_ORDERS_CONFIRM_SHIPMENT` (tracking), plus Amazon Ads campaign/ad-group/target/ad CRUD across SP/SB/SD/TV/DSP. Every action type **disabled by default**, per-type opt-in in Settings > Actions, `dryRun=true` supported, full audit trail via `actions_list`. No FBA inbound shipment creation, no feed upload, no reimbursement filing, no Vendor PO ack documented. | DataDoe owns the SP-API developer registration, OAuth, and refresh tokens; client auths to DataDoe via a static API key (`datadoe-mcp-key` header) | Fully hosted, HTTP Streamable transport, zero self-run infra | Not itemized in this pass (see prior research file `datadoe.md` in this scratchpad for detail); claims SOC 2 Type II + cleared Amazon DPP assessment | VERIFIED via previously-fetched README — https://github.com/Deltologic/datadoe-mcp (see local file `datadoe.md`) |
| **Seller Labs Amazon MCP** | Marketing copy states it can "edit campaigns, adjust bids, enable or disable campaigns" **inside Seller Central, triggered by your approval, with built-in guardrails**; reads profit margins, ad efficiency, FBA fees, inventory forecasts, reviews, Search Query Performance. Price/listing-content writes not claimed. Ads-focused, not full catalog/pricing writes. | Managed — "secure authentication and encryption," data sourced from official SP-API + Ads API (implies Seller Labs holds the developer registration) | Hosted, connects to Claude/ChatGPT | **Free** under $2K/mo Amazon revenue; 14-day trial above that; then bundled into the "Genius Bundle" plan | REPORTED — https://www.sellerlabs.com/amazon-mcp/, https://www.sellerlabs.com/blog/seller-labs-amazon-mcp-server-ai-insights/ (site itself egress-blocked; content from search snippets only) |
| **Apideck Amazon Seller Central MCP/connector** | Positioned as a **normalized "Ecommerce API"** unifying Amazon Seller Central with 200+ other e-commerce backends under one schema — read/write claims are generic ("agent access... through normalized APIs") with no Amazon-specific write-endpoint list surfaced. Because it's a universal abstraction layer, expect lowest-common-denominator coverage (likely orders/listings/inventory reads, uncertain write depth for Amazon-specific ops like A+ Content or FBA inbound). | "Managed auth" via Apideck **Vault**, OAuth handled by Apideck — Apideck (not the seller) appears to hold the SP-API developer registration | Fully hosted | Not confirmed this pass | REPORTED only — https://www.apideck.com/mcp-server/amazon-seller-central (egress-blocked; search snippet only) |
| **Zapier MCP (Amazon Seller Central)** | Exposes Amazon Seller Central "actions" (whatever Zapier's existing Amazon Seller Central Zapier-app actions are) as MCP tools/"Run tool" calls; specific write-action list not enumerated in the reachable snippet. Historically Zapier's Amazon Seller Central app has been thin (mostly order/trigger-based), so deep listing/pricing writes are **uncertain**. | Zapier owns the connected-account OAuth to Amazon | Fully hosted | Zapier task-based pricing — 1 MCP tool call = 2 tasks from plan quota | REPORTED — https://zapier.com/mcp/amazon-seller-central |
| **Two Minute Reports MCP** | **Read/analytics only** — explicitly "no Amazon Ads API credentials or developer tokens required," positioned purely for natural-language querying of Ads and Seller Central data (ROAS, TACoS, ASIN performance, orders/sales/inventory). No write claims found. | TMR-managed | Fully hosted | Free for existing TMR users | REPORTED — https://twominutereports.com/mcp, https://twominutereports.com/integrations/amazon-ads |
| **Windsor.ai MCP** | General 350+-source data/BI connector; write actions advertised are for **ad-campaign management generally** (budgets, bidding, ad sets) across supported ad platforms — Amazon Ads is listed among supported platforms, but an Amazon-Ads-specific write-tool list wasn't surfaced. Primarily positioned as a reporting/BI pipe (Sheets, BigQuery, Snowflake, Power BI) rather than an operational-write agent tool. | Windsor.ai-managed | Fully hosted | Not confirmed this pass | REPORTED — https://mcp.windsor.ai/, https://windsor.ai/connect/amazon-seller-central-mcp/ |
| **Adzviser Amazon Ads MCP** | Amazon **Ads** analytics/chat integration ("chat, analyze, and build custom workflows") — no write-ops evidence found; reads like a reporting connector, not an execution layer. | Adzviser-managed | Fully hosted | Not confirmed | REPORTED — https://adzviser.com/mcp/amazon-ads |
| **Vinkius "Amazon Selling Partner MCP Server"** | Listed in Vinkius's 5,200+-server catalog as exposing **10 tools** via Claude Code with no API keys to manage (Vinkius runs it on its own AWS infra, "Ed25519-signed audit chains," <40ms cold start). Tool-level write/read breakdown not surfaced — likely a thin wrapper of one of the open-source servers above, re-hosted. Also lists a separate **Amazon DSP MCP** (7 tools) — ads reporting, not Seller Central. | Vinkius-managed / proxied | Fully hosted (Vinkius infra) | Not confirmed | REPORTED — https://vinkius.com/apps/amazon-selling-partner-mcp/with/claude-code, https://vinkius.com/apps/amazon-dsp-mcp/with/vscode-copilot |
| **"Agent Central" (agentcentral.to)** | Surfaced in search results as "OAuth-backed Seller Central and SP-API data ... synced and normalized, then exposed through MCP tools for Claude, ChatGPT, and custom agents." A DataDoe comparison page (`datadoe.com/compare/datadoe-vs-agentcentral`) treats it as a direct competitor, implying similar read+write scope. Not independently verified this pass. | Agent Central-managed OAuth | Fully hosted | Not confirmed | REPORTED — https://mcpservers.org/servers/agentcentral-to-amazon-seller-central-mcp-claude, https://agentcentral.to/blog/amazon-seller-central-api |

### 1.3 Not found / explicitly absent from this search

- **No dedicated "Amazon Fulfillment Inbound v2024-03-20" MCP tool** beyond ailumia's generic 353-op wrapper (which claims coverage via its operation registry) and coaxon's narrower "FBA inbound plan creation." No server was found with a purpose-built, well-documented inbound-shipment-creation workflow (packing groups, box content, carrier confirmation) distinct from a generic operation pass-through.
- **No MCP server found with a documented reimbursement/case-creation write tool.** SP-API itself has no general-purpose "open a support case" write endpoint (see §—reimbursements are read-only via Finances API `listFinancialEventGroups`/reimbursement events; case creation is not part of SP-API — Amazon's own case log is Seller Central-UI-only, no public API). This will be confirmed/sourced in the notifications/writes deep-dive below.
- **PyPI**: no distinctly-named "sp-api-mcp" package surfaced beyond the `python-amazon-sp-api` SDK (a REST wrapper, not an MCP server) that several of the above (e.g., middlegold9) build on top of.

---

## 2. SP-API developer registration for a private, self-authorized app

**Note on sourcing:** `developer-docs.amazon.com`, `developer.amazonservices.com`, and mirror `spapi.cyou` were all **egress-blocked** in this environment. Everything below is reconstructed from search-engine snippets of those pages (REPORTED) plus one directly-fetched GitHub issue (VERIFIED for that issue's content only). Verify against the live docs before building.

### 2.1 Registration path (private/self-authorized)

1. Must already hold a **Professional Selling** account on Seller Central, and be signed in as the account's **Primary User** to complete registration. REPORTED — search synthesis of https://developer-docs.amazon.com/sp-api/docs/register-as-a-private-developer / https://spapi.cyou/en/use-other/registering-as-a-developer.html
2. Register as a developer through the **Solution Provider Portal** (Amazon's current unified portal — the "Developer" terminology was renamed to **"Solution Provider"** as part of a policy update). New developers go through an **identity-verification step described as taking about 20 minutes**. REPORTED — search synthesis of developer.amazonservices.com/register and Solution Provider Portal docs.
3. In the Solution Provider Portal, **add a new client** and select the **roles** your app needs — this creates a draft SP-API application. Because it's private, it never needs to be "published"; it stays in draft status permanently. REPORTED.
4. **Self-authorize**: on the "Authorize application" page (reachable from the Solution Provider Portal, Seller Central, or Vendor Central), click "Authorize app" for your own selling-partner account. This mints a **refresh token** — a new one is generated each time you repeat the step. REPORTED — https://developer-docs.amazon.com/sp-api/docs/self-authorization (title only reachable; content via search synthesis).
5. No separate "publish for review" gate exists for private apps — the friction is entirely in role approval (§2.2), not app-listing review. REPORTED.

One forum/community data point on turnaround: "as a private developer, you can receive approved access to Amazon's SP-API within a few working days" for ordinary (non-restricted) roles. REPORTED — search synthesis, exact source page not independently confirmed (likely developer-docs "Getting Started" copy).

### 2.2 Roles needed for the target write/read surface, and which are "restricted"

SP-API gates every operation behind a **role** — a named grant a developer must request per-application. A role is marked **Restricted** when the operations under it can return or accept **PII** (personally identifiable information — customer name, address, phone, buyer email alias, gift messages, personalization/customization text, and in some cases order-item names from which customer details could be inferred). REPORTED — https://developer-docs.amazon.com/sp-api/docs/roles-in-the-selling-partner-api, corroborated by https://www.datadoe.com/blog-posts/amazon-sp-api-restricted-pii (search-snippet).

| Role (Seller-side) | Needed for | Restricted? | Source |
|---|---|---|---|
| **Pricing** | Reading competitive/Buy Box pricing, feature pricing | **Not restricted** | REPORTED — cybersecify.com synthesis via search: "If your application only uses non-restricted roles such as Pricing, Product Listing, Inventory and Order Tracking, Finance and Accounting or Brand Analytics, section 2 of the Data Protection Policy is not the section that binds you, and section 1 has no pentest clause." |
| **Product Listing** | Listings Items API reads/writes (title, bullets, images, **price** field on the listing) | **Not restricted** | Same source as above |
| **Inventory and Order Tracking** | Order reads, FBA inventory reads | **Not restricted** | Same source as above |
| **Finance and Accounting** | Financial Events / settlement / reimbursement-event reads | **Not restricted** | Same source as above |
| **Brand Analytics** | Search Query Performance, Brand Analytics reports | **Not restricted** | Same source as above |
| **Amazon Fulfillment** | Fulfillment Inbound (shipment creation), Amazon Warehousing & Distribution | Not confirmed as restricted in the sources found this pass — inbound-shipment operations generally don't carry buyer PII (they're seller-to-Amazon warehouse), so it's **likely non-restricted**, but this specific role was **not explicitly confirmed** in the reachable sources. UNKNOWN — flag for direct doc verification. | — |
| **Buyer-Seller Messaging** | Messaging API (asking buyers questions, confirming customization, order-related outreach) | **Likely restricted** — the Messaging API surface deals directly with buyer contact and message content, and Amazon's restricted-data definition explicitly includes "buyer email aliases" and message-adjacent PII. Not found explicitly named "Restricted" in a directly-fetched source this pass, but the pattern strongly implies it. REPORTED/inference — flag for direct doc verification. | — |
| **Direct-to-Consumer Shipping (Restricted)** | Only relevant to Vendor-side Direct Fulfillment, not standard FBA/FBM seller flows | **Explicitly restricted** (named "(Restricted)" in the role itself) | VERIFIED-by-search-snippet — multiple sources incl. github.com/amzn/selling-partner-api-docs/issues/2390 (fetched directly — describes a real developer being denied this role 6-7 times over 5 months with no explanation given) |
| **Tax Invoicing / Tax Remittance** | Not needed for this project | Restricted | REPORTED |

**Practical read for Habib Distribution OS:** the core write surface this project needs — **Pricing reads, Listings Items writes (price/content), Inventory reads, Fulfillment Inbound shipment creation** — sits almost entirely in the **non-restricted** role set. The one likely exception is **Buyer-Seller Messaging**, which should be assumed restricted until confirmed otherwise, and gated accordingly (extra security disclosure, possibly the full PII review below).

### 2.3 Does a solo seller's private app need a full DPP audit for these roles?

**Short answer: No — not for the non-restricted roles this project needs.** Two separate processes exist and get conflated in casual discussion:

1. **The Data Protection Policy (DPP) itself** — a baseline contractual policy every SP-API developer agrees to at registration (encryption at rest/in transit, PII retention ≤30 days after order fulfillment unless legally required otherwise, secure deletion). This applies regardless of restricted/non-restricted status, but **only Section 2 of the DPP** (which carries the pentest/architecture-review obligations) is triggered by **restricted-role, PII-bearing operations**. REPORTED — search synthesis: "If your application only uses non-restricted roles ... section 2 of the Data Protection Policy is not the section that binds you, and section 1 has no pentest clause." (cybersecify.com, page itself blocked, content via search snippet.)
2. **The "Public PII Process"** — a **months-long, multi-stage audit** (encryption review, retention controls, access controls, vulnerability management, incident response, **annual third-party penetration tests**) required only for developers seeking **restricted-role** access, and required more rigorously for **public** (third-party, multi-seller) apps than for **private** apps used solely inside one organization. Per search-synthesized doc content: "all developers who want to build a publicly available application with restricted SP-API roles must go through an architecture review with the SP-API Solutions Architecture team... developers who develop applications solely for internal use by your organization[ ] can register as a private developer" with a lighter path. REPORTED — search synthesis of developer-docs "Register as a Public/Private SP-API Developer" pages.
3. **Amazon SP-API Guard** — Amazon's own free, serverless self-assessment tool that scans your AWS account against DPP controls and returns a remediation report within 24 hours. This is offered as a **self-service compliance aid**, not a mandatory pre-registration gate, and is most relevant if/when the project later seeks a restricted role. REPORTED — https://developer.amazonservices.com/tools/selling-partner-api-guard, https://developer.amazonservices.com/guard.

**Bottom line for this project:** registering a private, self-authorized app for **Pricing, Product Listing (Listings Items writes), Inventory and Order Tracking, Fulfillment Inbound, and Finance/Brand Analytics** should NOT require the full Public-PII pentest/architecture-review process — those are non-restricted roles. **Buyer-Seller Messaging should be treated as the one role that may trigger the heavier review**; if Habib Distribution OS needs automated buyer messaging, budget for a longer approval timeline (weeks, potentially longer per the GitHub issue #2390 anecdote of repeated multi-month denials) and don't gate the Phase 3 executor rollout on it. UNKNOWN/REPORTED-inference — recommend confirming directly against the live `developer-docs.amazon.com/sp-api/docs/roles-in-the-selling-partner-api` and `.../security-compliance-overview` pages once egress is available, before relying on this for a go/no-go decision.

### 2.4 2025-2026 policy changes affecting registration

- **Effective November 25, 2025**: Amazon updated the **Data Protection Policy (DPP) and Acceptable Use Policy (AUP)**. Substantive change noted in the changelog title/summary: the term **"Developer" was renamed to "Solution Provider"** across the policies, and existing integrations "may require changes to your existing security controls" to stay compliant. REPORTED — https://developer-docs.amazon.com/sp-api/changelog/updates-to-the-data-protection-policy-and-acceptable-use-policy (page blocked; title + summary via search).
- This DPP/AUP update is separate from, but likely related in spirit to, the **BSA "Agent Policy" update effective March 4, 2026** covered in §3 below — both tighten what automated/AI-driven callers of Amazon's systems must disclose and control. The two should be read together when designing the executor's identification and logging behavior.

---

## 3. The BSA update effective March 4, 2026 and the Agent Policy

**Sourcing caveat:** the primary documents — the Seller Central forum announcement thread, the live BSA/Agent-Terms text at `sellercentral.amazon.com/mws/static/agreement`, and every seller-blog analysis (ppc.land, ecommercebytes.com, damlawfirm.com, digitalapplied.com, sellersprite.com, feedvisor.com, myamazonguy.com, ecomclips.com, sellershorts.com) were **all egress-blocked** in this environment. Everything below is reconstructed from Google/Bing-style search-result snippets, some of which appear to quote the policy's actual text verbatim (the "Agent/[agent name]" header line reads like a direct quote picked up by the search index from the live agreement page). Treat quoted-looking fragments as **REPORTED, high-confidence** rather than VERIFIED, and confirm against the live BSA page before hard-coding compliance logic.

### 3.1 What changed, and when

- **Effective date: March 4, 2026.** Announced via Seller Central forum post on/around **February 17, 2026** (per ppc.land's headline framing "2 weeks to ensure compliance"). REPORTED — https://sellercentral.amazon.com/seller-forums/discussions/t/84e3f6b1-42f7-4cf3-a189-a5cc8d78d838 (title/date only, content blocked), corroborated by https://www.ecommercebytes.com/2026/02/18/amazon-sellers-have-2-weeks-to-ensure-compliance-of-tools-they-use/
- The Agent Policy is added as a **new Section 19** of the Business Solutions Agreement (referred to in some sources as "Agent Terms"). REPORTED — ppc.land headline synthesis + search snippet: "The BSA Agent Policy is a new Section 19 added to Amazon's Services Business Solutions Agreement, announced on February 17, 2026 and effective March 4, 2026."
- Companion changes in the same BSA update, not agent-specific: a **separate BSA document created for the Amazon Mexico store** (previously Mexico was covered inside the US/Canada agreement — those references are now removed, with Canada-specific language cleaned up), new **restrictions on using Amazon materials/services to train AI models** with "enhanced protection against reverse engineering," and updates to the **dispute-resolution process**. REPORTED — search synthesis of https://myamazonguy.com/news/amazon-services-business-solutions-agreement/ and https://feedvisor.com/university/changes-to-the-participation-agreement/
- **No opt-out**: continuing to sell on Amazon after March 4, 2026 constitutes automatic acceptance of the updated BSA, standard for Amazon policy updates. REPORTED — search synthesis, multiple sources.

### 3.2 Definition of "Agent"

Any **automated software or AI system that takes actions on a seller's account or accesses Amazon Services on the seller's behalf** is covered — explicitly named as affecting **repricers, PPC automation, listing tools, and any software connected to Seller Central or Amazon APIs**. REPORTED — search synthesis across ppc.land / ecomclips.com / sellershorts.com summaries. This is broad enough to unambiguously cover the Habib Distribution OS inventory/PPC/competitor agents and the executor service.

### 3.3 The three baseline obligations

Per multiple independent seller-advisory summaries converging on the same three points:

1. **Identify as automated.** "No Agent may access, use, or interact with Amazon Services unless, at all times, it identifies itself and operates in strict accordance with the requirements in section 3 of these Agent Terms." The mechanical requirement given: **all Agents must request identification by including `Agent/[agent name]` in the User-Agent string of all HTTP/HTTPS requests**, must maintain transparent operation as automated systems, and **must not simulate human behavior patterns, solve/bypass CAPTCHAs, or otherwise obscure their automated nature through any technical means**. REPORTED (near-verbatim per search snippet) — synthesis pointing to `sellercentral.amazon.com/mws/static/agreement`.
2. **Comply continuously.** The obligation is ongoing, not a one-time registration checkbox — ties back into the DPP/AUP and general BSA compliance framework described in §2.4.
3. **Cease access on Amazon's request.** "Agents are prohibited from accessing Amazon Services if Amazon has explicitly requested cessation of such access," and Amazon "reserves the right, at its sole discretion, to limit or restrict Agent access to Amazon Services through technical or other measures." REPORTED — search synthesis.

### 3.4 SP-API registration requirement for third-party/automated tools

Convergent seller-advisory guidance states: **"all automated seller actions must flow through registered SP-API applications with an application ID linked to a verified developer account."** The practical compliance test suggested to sellers vetting a third-party AI tool: **ask the vendor for (a) their SP-API application ID, (b) a sample audit-log export, and (c) a written compliance statement for the March 2026 Agent Policy — a vendor unable to produce these within 48 hours is presumed non-compliant.** REPORTED — search synthesis (source page for the exact "48 hours" framing not independently confirmed, but repeated across summaries with consistent wording, suggesting a shared source article, likely digitalapplied.com or profasee.com).

**Explicitly prohibited alternatives to SP-API:** browser automation, screen scraping, and calling undocumented/internal API endpoints are named as **explicitly prohibited** under the new rules. REPORTED. This directly rules out any Claude-agent design that would drive Seller Central through a headless browser instead of SP-API — reinforcing that SP-API (via a registered app, per §2) is not just best practice but a **policy requirement** post–March 4, 2026.

### 3.5 Logging requirements

**Every automated action must be logged with timestamps, action types, inputs, and outputs. Logs must be retrievable and retained for a minimum of 12 months.** REPORTED — search synthesis, consistent across summaries. This maps directly onto the existing `audit_log` table in the Habib OS schema (Section 7.2/13 of CLAUDE.md) — confirm the 12-month retention is enforced (no auto-truncation) and that the executor's `audit_log` inserts capture request/response payloads sufficient to reconstruct "inputs and outputs," not just a success/failure boolean.

### 3.6 Human-authorization checkpoints ("tiered actions")

One consistent seller-advisory framework describes a **tiered action model** with an explicit **Tier 3** requiring a **documented human-authorization step in the workflow** — and specifies this must be **"a real human approval in the workflow, not an automated approval gate that mimics human confirmation."** Concrete Tier-3 thresholds reported:

- **Bulk listing creation/modification affecting ≥500 ASINs in a single batch**
- **Price changes exceeding 20% within any rolling 24-hour period** (applies per-ASIN to automated price changes)
- **Account configuration changes**

Actions below these thresholds (price moves <20%/24h, inventory-only updates, batch sizes <500 ASINs) are described as safe to run with agent autonomy under "predefined parameters," i.e., without a mandatory human-in-the-loop gate — though Habib Distribution OS's own **L1 rule ("All PPC recommendations require approval regardless of amount," "Price changes require approval regardless of direction")** is already strictly stricter than Amazon's Tier-3 floor, so the project's existing approval-gate design is compliant by a wide margin and needs no changes to satisfy this specific requirement. REPORTED — search synthesis, likely sourced from a single detailed article (digitalapplied.com and/or ecomclips.com) whose exact thresholds were repeated consistently enough across independent summaries to treat as reasonably reliable, but **not independently confirmed against Amazon's primary text** in this pass — verify against the live Section 19 text before treating "20%/500 ASINs" as a hard compliance boundary for any *other* system that might rely on autonomous-without-approval execution (Habib OS's own all-approval design sidesteps the need for precision here).

### 3.7 Consequences of non-compliance

Reported consequences are generic-severity rather than itemized: **"Amazon reserves the right, at its sole discretion, to limit or restrict Agent access to Amazon Services through technical or other measures,"** and general Amazon policy-violation consequences (up to account-level enforcement/termination) are implied but **not spelled out specifically for Section 19** in any source reachable this pass. UNKNOWN — flag for direct verification; do not assume graduated warnings exist before an access cutoff.

### 3.8 Net implication for Habib Distribution OS's architecture

The existing design in CLAUDE.md already satisfies the substance of Section 19 as reported:
- Uses SP-API (via Executor) exclusively for writes — no browser automation. ✅ (once a registered SP-API app per §2 is in place)
- `audit_log` table captures agent/action/entity/details/success/error per write. ✅ — confirm 12-month retention and payload completeness (§3.5).
- 100% human-approval gate on all financial actions (`approval_requests` table + Telegram) — stricter than Amazon's own Tier-3 floor. ✅
- **Gap to close:** nothing in the current codebase (per `core/config.py` conventions) sets a **custom `Agent/[agent name]` User-Agent header** on outbound SP-API calls from the Executor. This is a concrete, cheap fix: set `User-Agent: Agent/HabibDistributionOS-Executor` (or similar) on every SP-API HTTP call, matching the reported identification format.

---

## 4. Amazon Seller Assistant (agentic) and Canvas

**Note:** `sellercentral.amazon.com`, `geekwire.com`, `novadata.io`, `stormy.ai`, `dbbnwa.com`, `marketplacemax.com`, `ecomranker.com`, and `sellersprite.com` were all egress-blocked. This section is search-snippet only.

- **Seller Assistant is now agentic**, not just Q&A. It "monitors account health, watches inventory, anticipates issues, and can act on your account **when you authorize it**." Initial capabilities reported: **inventory monitoring, compliance flagging, Creative Studio for ads, and an "Enhance My Listing" tool**. It's built to "plan multi-step tasks and take actions on a seller's behalf," not merely answer questions. REPORTED — search synthesis, https://www.sellersprite.com/en/blog/amazon-ai-seller-assistant-agentic-2026
- **Underlying model stack**: reported to run on **Amazon Bedrock**, using **"a mix of Amazon Nova and Anthropic Claude models."** This is directly relevant to Habib Distribution OS's own Claude-based design — Amazon's own first-party seller-assistant agent is itself partly Claude-powered. REPORTED — same source.
- **Canvas** is the visualization layer: instead of replying with text, it "builds interactive dashboards, charts, and scenario simulations in response to what you ask" (e.g., "show me my inventory health by product category" → a live dashboard, not a sentence). Distinction as reported: **"Seller Assistant tells you something, Canvas shows you something."** REPORTED — https://www.geekwire.com/2026/amazon-launches-ai-generated-canvas-for-sellers-as-e-commerce-platforms-race-to-add-ai-tools/, https://www.novadata.io/resources/news/amazon-seller-central-canvas-ai-visual-dashboard-2026
- **Availability**: agentic Seller Assistant features are reported live for **all US third-party sellers at no additional cost**; Canvas reported live for **US and UK** sellers. **No confirmation found of Canada availability** — relevant since Habib Distribution's home marketplace is Amazon CA. UNKNOWN for CA. REPORTED for US/UK — search synthesis of the geekwire/novadata coverage.
- **API/MCP surface: none found.** Every source describes Seller Assistant/Canvas purely as a **Seller-Central-UI feature** (chat + generated dashboards inside the browser). No SP-API endpoint, webhook, or MCP server was found that exposes Seller Assistant's reasoning, Canvas's dashboards, or a way to programmatically trigger/query either from outside Seller Central. A parallel search for "Seller Assistant Canvas API MCP surface" returned **only third-party SP-API MCP wrappers** (§1) — none of them claim to wrap Seller Assistant or Canvas specifically; they wrap the underlying SP-API data Seller Assistant itself presumably also calls. **Conclusion: Seller Assistant/Canvas cannot be a building block for this project's agent layer** — it is a competing/complementary first-party surface for Rami to use manually inside the browser, not an integration point for a Claude-driven backend agent. VERIFIED-by-absence (no source found claiming otherwise across all searches in this pass).

---

## 5. SP-API Notifications — event types and the simplest zero-maintenance path

**Primary source used:** the actual SP-API Notifications v1 Swagger/OpenAPI model, fetched directly via `raw.githubusercontent.com/amzn/selling-partner-api-models/main/models/notifications-api-model/notifications.json` (this raw-GitHub-content host was **not** egress-blocked, unlike the rendered docs site). This is the most authoritative source reached in this entire research pass — treat items marked VERIFIED here as high-confidence.

### 5.1 How the Notifications API actually works (VERIFIED from the model file)

- You call `createDestination` to register **one of exactly two delivery mechanisms**, defined in the `DestinationResourceSpecification` schema (**"Applications should use one resource type (sqs or eventBridge) per destination"**):
  - **`sqs`** — an `SqsResource` object requiring just an `arn` (`arn:aws:sqs:...`) — you own and poll an SQS queue.
  - **`eventBridge`** — an `EventBridgeResource`/`EventBridgeResourceSpecification` requiring `accountId`, `name` (partner event source name), and `region` — Amazon creates a **partner event source** in your AWS EventBridge that you then associate with an event bus.
- You then call `createSubscription` per `notificationType` to link that notification type to a destination.
- **`sendTestNotification`** exists per notification type — lets you verify a destination/subscription is wired correctly without waiting for a real event. VERIFIED (path `/notifications/v1/subscriptions/{notificationType}/testNotification` exists in the model).
- **Event filtering**: the `EventFilter` schema's `eventFilterType` enum is **explicitly, verifiably**: **`ANY_OFFER_CHANGED`, `ORDER_CHANGE`, `SHIPMENT_TRACKING_MILESTONE_CHANGED`** — confirming the user's specifically-asked-about `ANY_OFFER_CHANGED` event is real and filterable (e.g., by marketplace, or by aggregation time window via `AggregationFilter`/`AggregationSettings`). VERIFIED, directly from the model's `EventFilter` definition.
- **Order-change sub-filtering**: for the `ORDER_CHANGE` notification type, you can further filter by `orderChangeTypes`, whose enum is **`BuyerRequestedChange`, `DeliveryTipChange`, `OrderStatusChange`**. VERIFIED — `OrderChangeTypeEnum` in the model.
- The full catalog of `notificationType` string values (the model treats `notificationType` as an open string, not a closed enum, in the Swagger file) is documented separately in the **"Notification Type Values"** reference page, which lives on the egress-blocked `developer-docs.amazon.com/sp-api/docs/notification-type-values` — **not independently re-verified in this pass**.

### 5.2 Notification types relevant to this project (REPORTED — from general SP-API documentation knowledge and the notifications use-case guide, not independently re-fetched this pass because the docs site is blocked; flagged accordingly)

| Notification type (typical name) | Covers | Confidence |
|---|---|---|
| `ANY_OFFER_CHANGED` | Buy Box / competitive offer changes on an ASIN — pricing health, competitor undercuts | VERIFIED as a real, filterable type (§5.1); payload-shape detail REPORTED |
| `LISTINGS_ITEM_STATUS_CHANGE` | Listing goes active/inactive/suppressed — core "listing health" signal | REPORTED |
| `LISTINGS_ITEM_ISSUES_CHANGE` | New/resolved listing issues (compliance flags, content errors) | REPORTED |
| `FBA_INVENTORY_AVAILABILITY_CHANGES` (naming approximate) | FBA sellable/reserved quantity changes | REPORTED |
| `ORDER_CHANGE` | New orders and order-status transitions (VERIFIED to exist; sub-filterable per §5.1) | VERIFIED (type) / REPORTED (full payload) |
| `FEED_PROCESSING_FINISHED` | Async feed submission result — needed if the executor uses Feeds instead of/alongside Listings Items PATCH for price/content writes | REPORTED |
| `REPORT_PROCESSING_FINISHED` | Async report generation result (e.g., Brand Analytics, Inventory reports) | REPORTED |
| Account-health-adjacent types | Amazon has historically not exposed a single unified "ACCOUNT_HEALTH" push notification the way it exposes listings/order events; account health signals are more commonly pulled via the Account Health API / Seller Central rather than pushed via Notifications. UNKNOWN whether a dedicated push type exists as of 2026 — not confirmed either way this pass. | UNKNOWN |

### 5.3 Simplest, zero-maintenance way to receive notifications for a Hetzner-VPS, solo-operator setup

Given Habib Distribution OS already runs a single persistent Hetzner VPS process (the Telegram bot / Executor daemon) rather than AWS infrastructure, the two options trade off differently:

- **SQS path**: requires **owning an AWS account and an SQS queue** just to catch notifications, then **polling that queue** from the VPS (long-polling works but is still an always-on loop, another moving part, another AWS bill line and IAM credential to rotate — friction the CLAUDE.md's "solo operator first" principle explicitly discourages). This is the more "zero-maintenance-once-set-up" option **if the project is already going to touch AWS for something else**, but is net-new infrastructure otherwise.
- **EventBridge path**: also requires an AWS account (EventBridge is AWS-native), receiving a **partner event source** that must be associated with an event bus, then routed (e.g., to a Lambda, or into SQS/SNS/HTTPS webhook via an EventBridge rule) — **more AWS moving parts, not fewer**, for a single-operator VPS-centric architecture.
- **Given neither destination type is "no AWS account needed,"** the actual zero-maintenance answer for this specific architecture is almost certainly **not to use push Notifications at all for v1**, and instead **rely on the existing scheduled SP-API sync jobs** (already in CLAUDE.md §4.1 — inventory/orders/PPC/competitor syncs on cron) to poll the relevant read APIs directly on a schedule, exactly as the system already does. This sidesteps AWS entirely.
- **If/when push notifications become worth the AWS overhead** (e.g., wanting near-real-time `ANY_OFFER_CHANGED` alerts for competitor price wars, faster than a daily 05:15 UTC competitor-snapshot sync could catch), the **lowest-maintenance AWS-side option is SQS**, not EventBridge: one queue, one IAM policy, one long-poll loop in the existing Executor process (adding a lightweight `boto3` SQS consumer thread) — versus EventBridge's extra layer of event-bus/rule configuration for no operational benefit at this scale. This is an architectural judgment call based on the verified mechanics in §5.1, not a sourced third-party recommendation.

---

## 6. Walmart Marketplace API + MCP options

**Sourcing note:** the web-search budget for this session was exhausted partway through this section (a hard per-session cap, not something retriable), and `developer.walmart.com`, `lobehub.com`, and `mcpmarket.com` were all egress-blocked. This section is therefore built from **one directly-fetched, VERIFIED GitHub repo** (`luke-nielsen/walmart-mcp`) plus general SP-ecosystem knowledge for the underlying Walmart Marketplace API, clearly flagged. The "130-tool server on lobehub" and "Apideck Walmart MCP" named in the task brief could **not be independently verified or detailed** this pass — treat their existence as plausible (they were named as known candidates) but their tool lists/auth/maturity as **UNKNOWN**.

### 6.1 github.com/luke-nielsen/walmart-mcp (VERIFIED — directly fetched)

A TypeScript MCP server wrapping **both** Walmart's **Affiliate/Catalog API** (consumer-facing product search) and the **Walmart Marketplace API** (seller operations) behind one unified server.

| Category | Tools | Write? |
|---|---|---|
| Affiliate/Catalog (read) | `affiliate_search`, `affiliate_product_lookup`, `affiliate_taxonomy`, `affiliate_trending`, `affiliate_reviews`, `affiliate_stores` | No |
| Marketplace reads | `mp_get_items`, `mp_get_item`, `mp_get_inventory`, `mp_get_orders`, `mp_get_order` | No |
| **Marketplace writes** | `mp_update_inventory` (set available quantity), `mp_update_price` (update pricing), `mp_acknowledge_order` (confirm order pre-fulfillment) | **Yes** |

**Coverage gaps (VERIFIED absent):** **no WFS (Walmart Fulfillment Services) inventory or inbound-shipment tools**, and **no Walmart Connect (advertising) API support** — this server is Marketplace-order/price/inventory only.

**Auth:** Marketplace surface uses **OAuth 2.0 with Client ID + Secret**, auto-refreshed; the separate Affiliate surface uses **RSA-signature auth with a Consumer ID + private key**, regenerated per request — two distinct credential systems bundled into one MCP server.

**Hosting:** self-hosted only — stdio MCP server via Node.js, env-var or `.env`-file configuration, no managed/hosted option.

**Maturity:** **0 GitHub stars**, 2 commits on main, MIT license, 0 open issues, minimal dependencies (2 runtime packages), Vitest unit tests present. Reads as a clean, recently-started, low-adoption project — functionally the most complete open Walmart write-capable MCP server found, but with essentially no community validation yet.

Source: VERIFIED — https://github.com/luke-nielsen/walmart-mcp

### 6.2 Other named candidates — not independently verified this pass

| Candidate | Status |
|---|---|
| "130-tool server on lobehub" | Named in the task brief as a known listing; **could not be reached** (lobehub.com egress-blocked) or corroborated via a working alternate route before the search budget was exhausted. UNKNOWN. |
| Apideck Walmart MCP | Apideck's Amazon MCP pattern (§1.2 — normalized "Vault"-based OAuth, unified e-commerce schema across 200+ backends) strongly suggests a Walmart connector exists on the same platform, since Apideck's whole pitch is one schema across many marketplaces, but the specific `apideck.com/mcp-server/walmart` page was **egress-blocked** and not corroborated by search this pass. UNKNOWN (plausible-by-pattern, not verified). |

### 6.3 Walmart Marketplace API — general shape (REPORTED, from general SP-ecosystem documentation knowledge; not independently re-verified against developer.walmart.com in this pass because that domain was blocked)

- **Auth:** OAuth 2.0, Client ID + Client Secret issued per Walmart Seller Center registration — architecturally simpler than SP-API's LWA+AWS-IAM combination (no AWS account needed for the core Marketplace API), consistent with what `luke-nielsen/walmart-mcp` implements (§6.1, VERIFIED for that implementation).
- **Item/pricing writes:** Walmart's core seller write surface is the **Items API** (bulk/single item setup, price and content updates) — analogous in role to SP-API's Listings Items API. `mp_update_price` in §6.1 is consistent with this.
- **Inventory:** a dedicated **Inventory API** for on-hand/available quantity — consistent with `mp_update_inventory`.
- **Orders:** an **Orders API** covering acknowledge/ship/cancel/refund lifecycle transitions — only the "acknowledge" step was found implemented in the MCP server surveyed (§6.1); shipment-confirmation and cancellation writes were not found in that server.
- **WFS (Walmart Fulfillment Services)** — Walmart's FBA-equivalent — exposes its own **Inbound/inventory API surface** (comparable in spirit to SP-API's Fulfillment Inbound v2024-03-20) for creating inbound shipment plans into Walmart's fulfillment network. **No MCP server found this pass implements WFS inbound** — this is a clear coverage gap across every Walmart MCP option surveyed (§6.1's explicit gap; §6.2 candidates unverified).
- **Walmart Connect** is Walmart's retail media / advertising platform, with its own **separate Ads API** (campaigns, ad groups, keywords, reporting — the Walmart Connect analog to Amazon Ads API). **No MCP server found this pass covers Walmart Connect** — again, a clear gap, mirroring the Amazon side where ads-focused MCP servers (Seller Labs, Two Minute Reports, Adzviser, Windsor.ai) are entirely separate products from Marketplace-operations servers.

### 6.4 Net read for Habib Distribution OS's future Walmart CA expansion

Per CLAUDE.md §16.1, Walmart integration is explicitly deferred ("after Amazon is fully automated — new sync layer + marketplace-specific agent logic"). Given this research: when that phase starts, **no existing MCP server (open-source or hosted) covers the full write surface this project will eventually want** (price + inventory + orders **and** WFS inbound **and** Walmart Connect bids) — the same "build a purpose-specific, LWA-analog direct integration" pattern used for Amazon (§ "Recommended write path" below) will likely be the right call for Walmart too, rather than adopting a thin, single-digit-star community MCP wrapper for a second marketplace's financial write operations.

---

## Recommended write path

**For a Claude agent executing approved writes on Amazon (and, later, Walmart), the safest zero-maintenance path found in this research is *not* any of the third-party MCP servers surveyed in §1 or §6 — it is the architecture Habib Distribution OS already committed to in CLAUDE.md: a small, self-hosted, LWA-only Python Executor calling SP-API directly, gated by mandatory human approval, with no MCP layer in the write path at all.** Reasoning, in order of weight:

1. **No third-party-hosted MCP server found in §1.2 has documented write coverage matching this project's actual needs** (price + listing content + FBA inbound + notifications) without also taking on an unverifiable amount of trust in someone else's SP-API developer registration, someone else's credential custody, and someone else's interpretation of the March 2026 Agent Policy's logging/audit obligations. DataDoe is the most credible hosted option found (SOC 2 Type II + cleared DPP assessment claims, granular per-action-type opt-in, dry-run support) but still lacks FBA inbound shipment creation and reimbursement/case tooling — it would have to be paired with something else anyway.
2. **Every open-source MCP server surveyed in §1.1 is early-stage** (single-digit-to-low-double-digit GitHub stars, 1-8 commits, several with write operations only "planned") — none carry enough production hardening to trust with unattended financial writes on a real seller account. `ailumia/amazon-sp-api-mcp`'s generic 353-operation registry with `confirm=true`/`dryRun=true`/SHA-256 audit hashing is the most thoughtfully engineered safety model found, and is a reasonable **read-path or human-supervised-exploration tool** for Rami to use interactively from Claude Desktop/Code — but it is a two-star, six-commit project, not something to wire into an unattended nightly executor.
3. **The March 4, 2026 Agent Policy (§3) makes the direct-SP-API-app path a compliance requirement, not just an architectural preference:** browser automation and undocumented endpoints are explicitly prohibited, and "all automated seller actions must flow through registered SP-API applications with an application ID linked to a verified developer account" (§3.4). A private, self-authorized app that Habib Distribution OS registers and controls satisfies this cleanly; routing writes through a third party's shared/hosted SP-API app adds a layer of "whose Agent identity is this, really?" ambiguity that a solo operator doesn't need.
4. **The roles this project needs (Pricing, Product Listing, Inventory and Order Tracking, Fulfillment Inbound) are non-restricted (§2.3)** — meaning the "zero-maintenance" private-app registration path is genuinely fast (days, not the months-long Public PII Process), so there is no real friction being traded away by not using a hosted MCP intermediary.

**Concretely:**
- **Keep SP-API writes inside the existing Executor service** (CLAUDE.md §7) — LWA-only refresh-token auth, own private/self-authorized SP-API app, direct `python-amazon-sp-api` or hand-rolled SigV4-free (LWA-only, no AWS IAM needed for these roles) HTTP calls.
- **Do not put an MCP server in the write path.** Reserve MCP (e.g., DataDoe, or a self-hosted read-only wrapper) strictly for Rami's own **interactive, human-in-the-loop exploration** in Claude Desktop/Code — asking Claude ad hoc questions about the account — never for the unattended agent pipeline that writes to Amazon.
- **For Walmart (future, §6.4):** replicate the same pattern — a small self-hosted Executor-style module using Walmart's own OAuth2 Marketplace API directly, not a third-party MCP wrapper, once that phase starts.
- **For notifications (§5.3):** skip AWS-based push (SQS/EventBridge) for v1; keep the existing scheduled-sync-job pattern. Add an SQS consumer only if near-real-time `ANY_OFFER_CHANGED` alerting becomes a proven need.

### Agent Policy compliance checklist (against the reported obligations in §3)

| Requirement | Status for Habib Distribution OS | Action needed |
|---|---|---|
| Writes flow through a registered SP-API app (not browser automation/scraping) | ✅ Architecture already SP-API-only via Executor | Confirm the private app is actually registered (§2.1) before go-live |
| Agent self-identifies (`Agent/[name]` User-Agent header on every call) | ❌ Not currently set per repo conventions reviewed | Add a fixed `User-Agent: Agent/HabibDistributionOS-Executor` header to every SP-API HTTP call |
| Continuous policy compliance (DPP, AUP) | ✅ Non-restricted roles only for now (§2.3) — no Section-2 DPP pentest obligation triggered | Re-check if/when Messaging role is ever requested |
| Cease access on Amazon's request | ⚠️ No explicit kill-switch behavior described in CLAUDE.md beyond normal error handling | Add an operational runbook step: if Amazon signals an access restriction, disable the Executor's SP-API calls immediately (env flag) rather than retrying |
| Every automated action logged (timestamp, action type, input, output), retained ≥12 months | ✅ `audit_log` table exists and is written on every executor action | Verify retention is actually ≥12 months (no auto-truncation) and that payloads capture full input/output, not just success/failure |
| Human authorization for "Tier 3" actions (≥500 ASINs bulk, >20%/24h price moves, account config changes) | ✅✅ Exceeds requirement — **100% of financial actions require approval**, regardless of size (CLAUDE.md §13.1, §9) | None — already stricter than the policy floor |
| Vendor due-diligence for any third-party tool used (SP-API app ID, audit-log sample, compliance statement) | N/A if no third-party MCP is used in the write path (per this section's recommendation) | If DataDoe or any hosted MCP is ever added to the write path, request these three artifacts first |

