# Supply Chain & Finance Tooling Survey — AI-Agent-Run Amazon FBA Food Brand

> Research date: 2026-09-02. Context: ~15 hero SKUs / 50-60 catalog SKUs, Amazon.ca live, Amazon.com launch Jan 2027, Walmart later, ~$10k/mo → $85k/mo. Agents run on Claude via MCP/APIs.
> Claim tags: **VERIFIED** = confirmed from vendor/official page fetched during research. **REPORTED** = from third-party review/blog/forum or vendor marketing not directly confirmed. **UNKNOWN** = could not confirm.


---

## 1. Profit Analytics / P&L Per SKU

**Context for scoring:** Habib needs true net profit per SKU across Amazon CA (now), Amazon US (Jan 2027), and eventually Walmart, feeding a weekly number into an AI Finance agent — ideally via API/MCP rather than manual CSV pulls.

### Sellerboard

- **Accuracy:** REPORTED — tracks true net profit per order factoring in 100+ distinct Amazon fees, ad spend, refunds, and user-supplied COGS (by period/batch/FIFO); reviewers note accuracy is entirely dependent on correct COGS input, VAT, and FX data supplied by the user. [Sellerboard Review 2026](https://www.thepricegeek.com/profit-analytics/sellerboard-review/), [Is Sellerboard Worth It](https://vovaeven.com/blog/is-sellerboard-worth-it)
- **Multi-marketplace:** REPORTED — supports 120+ marketplaces including Amazon, Shopify; **Walmart profit dashboard is live** as of the pages indexed in 2026 ("more features coming soon"). [sellerboard.com/walmart](https://sellerboard.com/walmart), [MyAmazonGuy comparison](https://myamazonguy.com/amazon-account-management/choosing-amazon-analytics-tools-merchantspring-vs-sellerboard/)
- **Official API:** UNKNOWN/likely NO for third-party pull. Sellerboard's own ingestion uses Amazon's SP-API (token-based, no seller credentials needed) to *pull data in* — this is not a public API for *pulling Sellerboard's processed output out*. No public REST API docs surfaced. A third-party Apify actor ("Sellerboard Multi-Account Sales & Profit Scraper") exists as an **unofficial scraper workaround**, and a knowledge-base article from a repricer vendor (bidx.io) references "connecting the Sellerboard API," suggesting sellers rely on scraping/browser automation or third-party connectors rather than an official endpoint. [Apify Sellerboard Scraper](https://apify.com/softdev-automations/sellerbord-actor/api), [bidx.io KB article](https://go.bidx.io/knowledge/en/knowledge-base/how-do-i-connect-the-sellerboard-api)
- **Automation without an API:** VERIFIED-by-vendor-blog — Sellerboard's built-in "Automation" page schedules recurring exports (Orders/Dashboard/Ads reports) as CSV or Excel, delivered by email or secure link, on a daily/weekly/monthly cadence — this is the practical integration path (an agent/inbox rule ingests the emailed CSV) rather than a live API. [Sellerboard blog: Automated Reporting](https://blog.sellerboard.com/2025/05/19/automated-reporting-for-amazon-sellers-best-practices-and-benefits/), [Sellerboard Reports Explained](https://vovaeven.com/blog/what-are-sellerboard-reports-and-why-do-they-matter)
- **Pricing:** REPORTED — starts around $15-19/month for the lowest tier scaling with order volume. [G2 pricing](https://www.g2.com/products/sellerboard/pricing)
- **Verdict for Habib:** Cheapest credible profit tool, Walmart-ready, but no clean API/MCP path — would require an email-CSV ingestion pipeline for the Finance agent, adding fragility.

### Shopkeeper

- **Accuracy:** REPORTED — pulls via Amazon's official API (SP-API), computes 150+ Amazon fees, pulls up to 3 years of historical data on signup then tracks in real time. [shopkeeper.com](https://shopkeeper.com/), [Shopkeeper Review 2026](https://www.webretailer.com/reviews/shopkeeper/)
- **Multi-marketplace:** REPORTED — reviewers note it is Amazon-focused and "lacked scalability" for multichannel/in-depth PPC vs. competitors; no clear Walmart support found. [marginbusiness.com review](https://marginbusiness.com/how-shopkeeper-helps-you-track-fba-profits/)
- **API/automation:** UNKNOWN — no dedicated public API found in search results.
- **Pricing:** 14-day free trial, no card required; tiered by order volume (specific numbers not confirmed in fetchable sources). [webretailer.com](https://www.webretailer.com/reviews/shopkeeper/)
- **Verdict:** Amazon-only, no evidence of Walmart or API — weaker fit than Sellerboard or Nova for a multi-marketplace roadmap.

### ManageByStats (MBS)

- **Multi-marketplace:** REPORTED — explicitly **does not** support Shopify/Walmart/eBay; Amazon-only. [MerchantSpring review of MBS](https://merchantspring.io/resources/managebystats-free-marketplace-analytics-review)
- **Pricing/API:** UNKNOWN — no pricing or API details surfaced from searchable sources (vendor requires direct contact).
- **Verdict:** SKIP — wrong shape for a business planning a US and Walmart expansion.

### Sellerise

- **Scope:** REPORTED — all-in-one for FBA/FBM sellers: profit analytics, listing optimization, keyword research, review management, and **FBA reimbursement** features bundled in. [Capterra](https://www.capterra.com/p/10004857/Sellerise/)
- **Multi-marketplace:** REPORTED — 20 Amazon marketplaces (incl. US, CA) but **no Walmart**. [revenuegeeks.com Sellerise review](https://revenuegeeks.com/software/sellerise)
- **Pricing:** REPORTED — 6 tiers, Starter $19.99/mo up to Top-Seller $599.99/mo, plus custom Agency; 7-day trial, no card. [revenuegeeks.com pricing guide](https://revenuegeeks.com/sellerise-pricing/)
- **API:** UNKNOWN — no dedicated API/MCP documentation found.
- **Verdict:** Reasonable bundled Amazon-only tool (profit + reimbursements in one), but no Walmart and no confirmed API — a "nice-to-have" not core infra.

### Threecolts (Seller 365 — bundles InventoryLab, FeedbackWhiz, Tactical Arbitrage, SmartRepricer, ScoutIQ, etc.)

- **Scope:** VERIFIED (vendor page) — Seller 365 is a 10-tool subscription bundle covering sourcing, listing, repricing, feedback, and profit tracking; **Reimbursements product explicitly covers both FBA and Walmart WFS**, auto-detecting and filing claims for lost/damaged inventory, miscounts, underpaid reimbursements, and unused shipping labels; claims to have recovered **$1B+** to date. [Threecolts Seller 365](https://www.threecolts.com/seller-365), [Threecolts 3P Sellers solutions](https://www.threecolts.com/solutions/3p-sellers)
- **Pricing:** REPORTED — Seller 365 from $69/mo (1 user), Teams $79/mo (10 users), Pro tier adds commission-free reimbursements. [revenuegeeks.com Seller 365 pricing](https://revenuegeeks.com/software/seller-365/pricing)
- **API/automation:** UNKNOWN for a general API; InventoryLab (bundled) has its own export/accounting integration (see Section 4).
- **Verdict:** Interesting mainly for the **Walmart-aware reimbursement engine** — worth revisiting once Walmart is live; overkill today given Habib doesn't need sourcing/repricing tools for 15-60 owned SKUs.

### Helium 10 (Profits / Refund Genie / Inventory Protector)

- **Accuracy/data source:** VERIFIED (vendor-adjacent) — Profits, Refund Genie, Follow-Up and Inventory Protector pull directly via Amazon's Seller Central API integration, so figures reconcile to Seller Central. [revenuegeeks.com Helium 10 review](https://revenuegeeks.com/software/helium-10)
- **Pricing:** REPORTED — prices rose April 2026; Platinum $129/mo (1 user, 1 account), Diamond $279/mo annual (5 users/accounts, rules-based ad automation); the old cheap Starter plan was discontinued. [SellerSprite Helium 10 pricing guide 2026](https://www.sellersprite.com/en/blog/helium-10-pricing-2026-guide)
- **API:** VERIFIED-by-multiple-sources — Helium 10 **does have an API, but gated to the Enterprise plan only**. [revenuegeeks.com "Does Helium 10 Have an API?"](https://revenuegeeks.com/software/helium-10/api)
- **Multi-marketplace:** Amazon-only tool set; no Walmart evidence found.
- **Verdict:** Expensive for Habib's size, API locked behind Enterprise pricing not disclosed publicly — SKIP for now; the keyword/PPC modules could matter later for the PPC agent but that's a separate evaluation.

### Jungle Scout (Cobalt / API)

- **Multi-marketplace:** VERIFIED (vendor) — Cobalt suite covers 19 Amazon marketplaces; the **API specifically covers 10** marketplaces (US, UK, DE, IN, **CA**, FR, IT, ES, MX, JP) — no Walmart. [Jungle Scout API product page](https://www.junglescout.com/products/jungle-scout-api/)
- **API pricing:** VERIFIED (vendor) — $29–$199/month tiered by call volume, **only available on Growth Accelerator or Brand Owner+CI plans** ($79+/mo base). [Jungle Scout pricing](https://www.junglescout.com/pricing/), [Jungle Scout API article](https://www.junglescout.com/resources/articles/jungle-scout-api/)
- **Reports automation:** REPORTED — can automate weekly/monthly sales, profit, inventory, and keyword-ranking reports.
- **Verdict:** Positioned more as product-research/market-intelligence than SKU-level P&L; API exists and is real but priced/scoped for research use cases, not core profit accounting.

### SellerApp

- **Pricing:** REPORTED — Professional ~$99/mo, Business ~$149/mo, Enterprise custom; also lower "Seller" tier ~$42/mo and add-on managed services. [revenuegeeks.com SellerApp pricing](https://revenuegeeks.com/sellerapp-pricing/)
- **API:** VERIFIED (vendor) — SellerApp offers an e-commerce API for product data, pricing intelligence, and market insight (not specifically a profit/P&L export API), gated to higher tiers. [sellerapp.com](https://www.sellerapp.com/)
- **Verdict:** Similar to Jungle Scout — a research/PPC tool with a profit calculator bolted on, not a dedicated profit-analytics API.

### Nova Analytics (novadata.io) — the standout for an agent-run business

- **What it is:** VERIFIED (vendor) — an Amazon analytics/P&L platform built explicitly for AI-agent consumption: "AI for Amazon Sellers: Your Data in Claude & ChatGPT." [novadata.io](https://novadata.io/)
- **MCP server:** VERIFIED (vendor) — Nova ships a **read-only MCP server** ("Nova MCP") that connects directly to Claude, ChatGPT, or Gemini. Setup is a documented 4-step flow, connecting Seller Central + Amazon Ads (read-only), with the first sync landing within an hour. [Connect Nova MCP to Claude](https://novadata.io/amazon-ai-agents/connect-claude), [Build AI Agents on Amazon Data](https://novadata.io/build-agents), [Amazon MCP Tools list](https://novadata.io/amazon-mcp-tools)
- **Data coverage:** VERIFIED (vendor) — orders, 40+ Amazon fee types, COGS, PPC spend at product level, FBA inventory, and organic performance across **21 marketplaces**, refreshed hourly; claims 99.8% profit-calculation accuracy. [Amazon Seller Dashboard](https://novadata.io/amazon-seller-dashboard-software), [Amazon Marketplace Analytics](https://novadata.io/amazon-marketplace-analytics)
- **Pricing:** REPORTED — paid plans from $29/mo (annual), 14-day free trial, and a promo ("sign up before Aug 31, free for life") was live on the marketing pages indexed — treat the free-for-life claim as a time-limited promo, verify current status before relying on it. [novadata.io pricing context](https://novadata.io/resources/blog/can-chatgpt-read-seller-central-data)
- **Walmart:** UNKNOWN — marketing focuses on Amazon's 21 marketplaces; no explicit Walmart mention found.
- **Verdict:** **Best architectural fit for the Habib OS agent model** — it is the only tool in this category built around MCP/agent access rather than a human dashboard first. Given CLAUDE.md already plans direct Supabase queries for agents (no MCP for batch runs), Nova's MCP would most plausibly serve as a **cross-check / secondary data source** or a fast way to prototype before Habib's own sync/agent pipeline is fully built out — not a replacement for the Supabase-native profit_daily table, since CLAUDE.md's "one source of truth" principle argues against a second live profit system. Worth a trial specifically to validate Habib's own fee/profit math against Nova's numbers.

### Section 1 Comparison Table

| Tool | Net profit accuracy | CA+US+Walmart | API/MCP for automation | Entry price | Verdict |
|---|---|---|---|---|---|
| Sellerboard | REPORTED strong (COGS-dependent) | CA/US yes, Walmart dashboard live | No public API; scheduled email/CSV export only; unofficial scraper exists | ~$15-19/mo | Buy — cheapest, Walmart-ready, use email-CSV automation |
| Shopkeeper | REPORTED good | Amazon-only reported | Unknown | Trial, no pricing confirmed | Skip |
| ManageByStats | Unknown | Amazon-only (confirmed no Walmart/Shopify) | Unknown | Unknown | Skip |
| Sellerise | REPORTED, bundles reimbursements | 20 Amazon markets, no Walmart | Unknown | $19.99-$599.99/mo | Skip (redundant with Sellerboard) |
| Threecolts Seller 365 | REPORTED (via InventoryLab) | Reimbursements cover FBA **and Walmart WFS** | Unknown general API | $69-79+/mo | Revisit at Walmart launch |
| Helium 10 Profits | REPORTED, reconciles to Seller Central | Amazon-only | API exists, Enterprise-gated only | $129-279+/mo | Skip — overpriced for scope |
| Jungle Scout | Research-oriented | 19 markets, API covers 10 (incl. CA), no Walmart | VERIFIED API, $29-199/mo add-on | $79+/mo base | Skip for P&L; maybe for market research later |
| SellerApp | Research-oriented | Unclear | VERIFIED API (data/pricing intel) | $42-149+/mo | Skip |
| Nova Analytics | REPORTED 99.8% claim | 21 Amazon markets; Walmart unconfirmed | **VERIFIED MCP server, agent-native** | From $29/mo | Trial as agent-native cross-check |


---

## 2. Demand Forecasting & PO/Restock Planning

**Context:** Habib is at 15-60 SKUs — squarely in the zone where sources disagree on whether dedicated software earns its keep yet (see "SKU threshold" discussion at the end of this section).

### SoStocked (now Carbon6-owned)

- **Method:** REPORTED — statistical demand forecasting using historical sales, seasonality weighting (adjustable by hand, not just flat assumptions), and promotional-activity adjustment; forecasts up to **12 months out**. [Best Amazon Inventory Management Tools 2026 — Nova blog](https://novadata.io/resources/blog/best-amazon-inventory-management-tools), [SoStocked review — Profit Hawk](https://www.profithawk.io/software-tools/sostocked/)
- **FBA-aware:** VERIFIED-ish (multi-source) — IPI-aware stock levels, overseas lead-time modeling, FBA shipment planning, inbound tracking, stockout-risk monitor, and an Overstock/Aged-Fees report forecasting long-term storage costs. [SoStocked vs RestockPro comparison](https://jarvio.io/alternatives/restockpro)
- **PO workflow:** REPORTED — generates purchase orders from the forecast; **ProfitFlow** add-on ($97/mo standalone) runs the same engine against projected COGS/margins/future fees for a profit-aware PO.
- **API:** REPORTED — pulls FBA shipment data back in automatically via API once shipments are created in Amazon (one-directional sync, not a general-purpose developer API).
- **Multi-marketplace:** UNKNOWN for Walmart specifically under the SoStocked brand (Carbon6's broader suite markets Walmart expansion tools separately — see below).
- **Pricing:** REPORTED — inventory tier starts around **$250/month** (scales with SKU/order volume; no published rate card, quote-gated). [SoStocked vs RestockPro](https://jarvio.io/alternatives/restockpro)
- **Verdict:** The deepest forecasting engine in this category, but priced and scoped for sellers well past Habib's current 15-60 SKU / $10k-mo stage.

### Inventory Planner (Carbon6 brand, formerly a Sellery-adjacent product)

- **Note:** Carbon6 owns both SoStocked and the separate "Inventory Planner" brand; marketing pages are inconsistent about how distinct the products are — treat as UNKNOWN/overlapping until confirmed directly with vendor.
- **Pricing:** REPORTED — entry pricing for standalone inventory forecasting tools (SKU Compass, Inventory Planner, Cin7 Core) in the **$300-500/month** range, per an aggregator comparison; a separate source cites Carbon6 suite pricing "starting at $49/month" for a lower tier. [SKU Compass multi-channel comparison](https://skucompass.com/best-multi-channel-inventory-forecasting-2026/), [Carbon6 review — dupple.com](https://dupple.com/tools/carbon6)
- **Verdict:** Same Carbon6-family caution as SoStocked — expensive relative to Habib's stage; the pricing-page inconsistency across sources itself is a signal to get a live quote rather than trust marketing pages.

### RestockPro

- **Method/PO workflow:** REPORTED — **strongest supplier and PO workflow** in the category: reorder-point logic = daily sales velocity × supplier lead time + safety buffer; excels specifically at telling you when to restock and generating FBA shipments. [Jarvio RestockPro alternatives page](https://jarvio.io/alternatives/restockpro)
- **Pricing:** REPORTED — ~$99/month entry, simpler setup than SoStocked.
- **Verdict:** A lighter, cheaper alternative focused on the restock-decision + PO/shipment-creation workflow rather than deep seasonality modeling — closer to Habib's actual need at 15-60 SKUs if a dedicated tool is wanted at all.

### Forecastly

- **Method:** REPORTED — straightforward inventory forecasting with restock alerts and FBA shipment tracking, positioned as budget-conscious; SoStocked and Forecastly are named together as the two strongest dedicated-forecasting options using historical velocity with seasonal adjustment. [Forecastly review — Nova Analytics](https://novadata.io/resources/best-amazon-seller-tools/forecastly)
- **Verdict:** Reasonable budget dedicated-forecasting option; no pricing figure was confirmed in these searches — get a quote before committing.

### Helium 10 Inventory Management

- **Method:** VERIFIED (vendor KB) — two selectable forecasting models (Helium 10 "Exponential" and "Additive"), configurable lead time/reorder-frequency/shipment-speed presets, Restock Suggestions dashboard showing days-of-supply, reorder status, forecasted reorder date, and recommended order quantity/cost. [Helium 10 Inventory Manager restock calc KB](https://kb.helium10.com/hc/en-us/articles/360060376193-How-Does-the-Helium-10-Inventory-Manager-Calculate-My-Restock-Recommendations)
- **IPI:** UNKNOWN — no explicit 2026 confirmation of IPI-specific handling found.
- **Pricing:** Bundled into Helium 10 Platinum/Diamond plans (see Section 1) — $129-279+/mo for the whole suite, not sold standalone.
- **Verdict:** Only worth it if Habib is already paying for Helium 10 for PPC/keyword tooling; not a standalone buy for inventory alone.

### SkuVault / Cin7

- **Category mismatch:** VERIFIED-by-comparison — SkuVault Core is fundamentally a **warehouse management system** (on-hand accuracy, pick/pack), not a forecasting tool; "many brands run a WMS and a forecasting tool side by side." [SKU Compass SkuVault alternative guide](https://skucompass.com/skuvault-alternative-2026/)
- **Cin7:** VERIFIED (vendor) — ForesightAI module forecasts up to 24 months using ML on historical trends/seasonality; positioned for **$2M-$50M revenue** multi-channel brands (DTC + wholesale + marketplace); Core tier starts at **$349/month**, most growing brands need the $599+ tier. [Cin7 features page](https://www.cin7.com/features/inventory/inventory-management/), [SKU Compass pricing comparison](https://skucompass.com/best-multi-channel-inventory-forecasting-2026/)
- **Verdict:** Both are the wrong tool class/scale for Habib today — SkuVault solves a warehousing problem Habib doesn't have (FBA holds the inventory), and Cin7 is priced and positioned for 10-100x Habib's current revenue.

### Flieber, Fabrikatör, Prediko (Shopify-native, DTC-first)

- **Flieber:** REPORTED — AI-based omnichannel forecasting across Shopify/Amazon/wholesale, anomaly-adjusted; **from $299/month**. [Flieber Shopify App listing](https://apps.shopify.com/flieber)
- **Fabrikatör:** REPORTED — Shopify-native, "covers the basics well," less sophisticated on the AI side than Prediko/Inventory Planner but cheaper and faster to set up. [Prediko demand/supply planning roundup](https://www.prediko.io/forecasting-demand-planning/demand-and-supply-planning-tools)
- **Prediko:** REPORTED — closes the full demand-to-PO loop natively and syncs to accounting tools, **but its native Amazon connector is still "coming soon"** — a marketplace seller needs a third-party bridge today. [same source]
- **Verdict:** All three are Shopify-first; Habib has no Shopify store in scope, so these are SKIP unless Habib later adds a DTC channel.

### The SKU-count threshold question

Multiple aggregator sources (not single-sourced, treat as REPORTED consensus rather than a hard rule) converge on a similar shape:
- **Under ~20 SKUs / <$30k/mo:** a spreadsheet with a days-of-supply + reorder-flag formula does the core job. [Inventory Spreadsheet vs Software — Inventory Hero](https://www.inventoryhero.ai/alternatives/inventory-spreadsheet-vs-software)
- **~20 SKUs:** "proactive FBA forecasting is no longer optional" per one operator guide — though this is a single source and reads as marketing-adjacent. [SKU Compass operator guide](https://skucompass.com/amazon-inventory-forecasting-guide/)
- **~50 SKUs:** dedicated forecasting tools reduce stockouts 20-30% vs. Excel-based management in one cited comparison; SoStocked specifically is positioned as "best for 50+ SKUs." [SKU Compass multi-channel comparison](https://skucompass.com/best-multi-channel-inventory-forecasting-2026/)
- **~150-250 SKUs (single channel):** a well-built spreadsheet can still handle the core days-of-coverage math; above that, per-FNSKU reorder points and multi-channel demand signals overwhelm manual upkeep. [same source]

**Applied to Habib (15 hero SKUs now, 50-60 catalog, adding a 2nd and eventually 3rd marketplace):** Habib sits right at the boundary these sources describe (20-50 SKUs) where opinions diverge, but two things push toward the LLM-agent-on-clean-CSV side of that boundary rather than a paid tool: (1) Habib is *already building* a Supabase `inventory_snapshots` + `sales_daily` + `products` (case pack, lead time, landed cost) schema with a Claude agent doing exactly the days-of-supply/velocity/reorder-point math the cheap tools do — this is sunk architecture, not a new build; (2) the multi-marketplace complexity that forces sellers toward paid tools (per-FNSKU reorder points across channels) is *exactly* the kind of structured, rule-based calculation an LLM agent handles well from clean tabular data, whereas the parts sellers actually pay for in SoStocked/RestockPro — hand-tunable seasonality curves, 12-month projections, PO-generation UI — are either already planned in CLAUDE.md's L1 rules (seasonal multipliers for Ramadan/Q4) or are UI conveniences a solo technical operator doesn't need. **The crossover point where a dedicated tool clearly wins is when SKU × marketplace combinations exceed what fits in a single Claude context window with room for reasoning — roughly 100-150 active SKU/marketplace pairs** by extrapolating the 150-250-SKU single-channel spreadsheet ceiling cited above down to account for 2-3x marketplace multiplication. Habib's 50-60 SKUs × 2-3 marketplaces (~100-180 pairs) means this crossover arrives around the same time as the Amazon US launch — worth re-evaluating RestockPro (cheapest, PO-workflow-focused) at that point rather than SoStocked/Cin7.

### Section 2 Comparison Table

| Tool | Method | FBA/IPI-aware | PO workflow | Multi-marketplace | API/CSV | Entry price | Beats LLM-from-CSV at |
|---|---|---|---|---|---|---|---|
| SoStocked | Statistical, 12-mo, hand-tunable seasonality | Yes (IPI, inbound, transfers) | Yes + ProfitFlow profit layer | Unclear re: Walmart | One-way API sync (shipments) | ~$250/mo | 50+ SKUs per vendor positioning |
| Inventory Planner (Carbon6) | Overlaps with SoStocked | Reported yes | Reported yes | Unclear | Unknown | $300-500/mo (aggregator estimate) | Unclear — get quote |
| RestockPro | Velocity × lead time + buffer | FBA shipment creation | Strongest PO/supplier workflow | Unknown | Unknown | ~$99/mo | Good mid-point if a tool is wanted |
| Forecastly | Historical velocity + seasonal adj. | FBA shipment tracking | Restock alerts | Unknown | Unknown | Unconfirmed | Budget dedicated option |
| Helium 10 Inventory | Exponential/Additive models | Reorder presets | Restock Suggestions dashboard | Amazon-only | Bundled in suite | Part of $129-279/mo suite | Only if already on Helium 10 |
| SkuVault | N/A (WMS, not forecasting) | N/A | N/A | N/A | N/A | N/A | Wrong tool class |
| Cin7 | ML, 24-mo (ForesightAI) | Reported yes | Yes | Yes (DTC+wholesale+marketplace) | Yes (vendor) | $349-599+/mo | $2M-$50M revenue brands |
| Flieber | AI omnichannel | Reported | Yes | Shopify+Amazon+wholesale | Unknown | $299/mo | Shopify-first brands |
| Fabrikatör | Basic, Shopify-native | Reported | Yes | Shopify-centric | Unknown | Cheap/fast setup | Shopify-first, low sophistication need |
| Prediko | AI demand-to-PO loop | Amazon connector "coming soon" | Yes, syncs accounting | Shopify-centric | Unknown | Unknown | Shopify-first, not Amazon-ready today |


---

## 3. FBA Reimbursements & Fee Audits

### Amazon's own policy — the ground has shifted under all these vendors (2024-2026)

- **Reimbursement basis changed from selling price to manufacturing cost.** VERIFIED-by-multiple-independent-sources (vendor blogs + seller-forum threads) — announced Dec 10, 2024, effective **March 31, 2025** (pushed back from an original March 10, 2025 date). Amazon now reimburses lost/damaged inventory using either Amazon's Estimated Manufacturing Cost or the seller's own submitted cost data (via the "Manage Your Sourcing Cost" page) — if the seller supplies nothing, Amazon's (typically lower) estimate is used. [Carbon6 policy explainer](https://www.carbon6.io/blog/amazon-reimbursement-policy/), [Amazon seller forum: new effective date](https://sellercentral.amazon.com/seller-forums/discussions/t/ed8abc33-a1d5-417d-b2e2-03b789099833), [RefundRetriever on manufacturing cost](https://www.refundretriever.com/blog/fba-manufacturing-cost)
  - **Action item for Habib's Finance agent:** submit real per-SKU cost data via the Sourcing Cost page — otherwise every future reimbursement defaults to Amazon's (self-interested, typically lower) manufacturing-cost estimate.
- **Auto-reimbursement launched Jan 15, 2025** for items lost in fulfillment centers — Amazon proactively compensates without a manual claim in these cases; a manual claim is still needed when auto-reimbursement doesn't trigger despite an actual loss/damage event. [Seller forum: reimbursement automation update](https://sellercentral.amazon.com/seller-forums/discussions/t/81c3235d-4c44-47ba-96c5-883cecab3244)
- **Claim windows shortened significantly:** REPORTED — fulfillment-center lost/damaged claims must be filed within **60 days** of the loss/damage being reported; customer-return claims within **60-120 days** of refund/replacement; removal-shipment-lost-in-transit claims within **15-75 days** of shipment creation; other removal claims within **60 days** of delivery back to seller. [Leviathan Sellers 60-day rule explainer](https://www.leviathansellers.com/blog/amazon-fba-reimbursement-policy-2026)
- **Net effect on third-party services:** REPORTED, industry-estimate — despite auto-reimbursement, one industry estimate cited says the new program could leave **up to 40% of potential reimbursements unclaimed** (some sellers forfeiting up to 60%), meaning third-party audit services remain relevant for catching what auto-reimbursement misses, but the addressable claim pool per seller is shrinking versus the pre-2025 era. Treat the 40%/60% figures as REPORTED industry commentary, not an audited statistic.

### SP-API and reimbursements — is there a direct endpoint?

- UNKNOWN/not clearly documented in these searches. Reimbursement tools historically **poll the Reports API** for FBA reimbursement reports rather than using a dedicated "claims" endpoint; no evidence of a first-class "submit a reimbursement claim" write endpoint was found. [general context from search](https://novadata.io/amazon-reimbursement-tracker)
- **Important cost note (verify before building):** SP-API introduced developer subscription/usage fees in early 2026 ($1,400/year + per-call overage from Jan-Apr 2026) but **Amazon cancelled these fees entirely on May 12, 2026** — confirmed by an email to developers rescinding both the annual subscription and the overage charges. [Nova Analytics: SP-API fees cancelled](https://novadata.io/resources/news/amazon-cancels-sp-api-fees-may-2026), [full chronology](https://novadata.io/resources/news/amazon-subscription-fees-2026) — good news for Habib's existing sync layer, which was built assuming free SP-API access.

### Getida

- **Pricing:** VERIFIED-by-multiple-sources — no monthly fee, **25% commission** on successfully recovered reimbursements, nothing charged if Amazon doesn't pay. [Getida Review — RevenueGeeks](https://revenuegeeks.com/software/getida), [FBA Tactics Getida pricing](https://fbatactics.com/reviews/getida/)
- **Audit depth:** REPORTED — audits the trailing **18 months** of inbound shipments, returns, lost/damaged inventory, and Amazon fee errors. [Getida FBA reimbursement process blog](https://getida.com/resources/blog/fba-reimbursements/understanding-the-amazon-fba-reimbursement-process/)
- **Typical recovery:** REPORTED — sellers with $1M+ annual revenue recover $5,000-$50,000/year; at Habib's $10k-85k/month ($120k-$1M/year) revenue this figure is likely proportionally smaller, but the risk-free/commission-only structure means there's no downside to trying.

### Seller Investigators (Carbon6-owned)

- **Pricing:** REPORTED — 25% recovery fee, no upfront/monthly cost, commission reversed if Amazon later reclaims a reimbursement. [Seller Investigators review — RevenueGeeks](https://revenuegeeks.com/software/seller-investigators)
- **Model:** REPORTED — hybrid: software flags discrepancies, human "Recovery Specialists" (two assigned per client) manually file complex claims, with weekly audits. [Profit Hawk review](https://www.profithawk.io/software-tools/seller-investigators/)

### Refunds Manager

- **Pricing:** REPORTED — 25% commission, same category-standard rate as Getida/Seller Investigators. [goaura.com reimbursement services roundup](https://goaura.com/blog/amazon-reimbursement-services)
- **Model:** REPORTED — automated connection + audit + auto-filing, positioned as simpler/more self-serve than Seller Investigators' hybrid-human model. [startupbros.com best/worst reimbursement tools](https://startupbros.com/best-amazon-reimbursement-management-tools/)

### Threecolts / Sellerise

- Already covered in Section 1 — both bundle reimbursement recovery into broader suites rather than selling it standalone; Threecolts' Seller 365 Reimbursements notably covers **both FBA and Walmart WFS**, which is the only Walmart-aware reimbursement product surfaced in this research. [Threecolts 3P Sellers](https://www.threecolts.com/solutions/3p-sellers)

### Section 3 Verdict

All the standalone commission-based services (Getida, Seller Investigators, Refunds Manager) charge the same **~25% of recovered amount, no monthly fee, no risk** — meaning the choice between them is low-stakes and reversible. Given Amazon's own auto-reimbursement now catches straightforward fulfillment-center losses, the case for one of these services is specifically to catch the **manual-claim gaps**: customer-return non-credits, weight/dimension fee discrepancies, and cases where auto-reimbursement silently fails to trigger. Because these are zero-fixed-cost and contingency-based, **buy one (Getida or Refunds Manager — simplest self-serve onboarding)** rather than build this in-house; an in-house Claude agent auditing FBA fee line-items against expected values is a plausible future build (SP-API Reports data is available), but is not worth prioritizing over the core Inventory/PPC/Competitor agents while a 25%-of-upside contingency vendor exists for free downside.


---

## 4. Accounting & Cash

### The two-layer pattern

VERIFIED-by-consensus — every source agrees the stack has two layers: a **general ledger** (QuickBooks Online or Xero) plus a **settlement connector** (A2X, Link My Books, Synder, or Taxomate) because neither QBO nor Xero can natively parse Amazon's batched settlement deposits (which bundle sales, fees, refunds, and reserve movements into one bank line) into clean journal entries. [Webgility accounting software roundup](https://www.webgility.com/blog/best-accounting-software-for-amazon)

### A2X

- **Coverage:** VERIFIED (vendor) — Amazon, Shopify, eBay, Etsy, **Walmart**, and PayPal; posts to QuickBooks Online, Xero, NetSuite, or Sage. [A2X pricing detail](https://www.capterra.ca/software/173271/a2x-accounting)
- **Pricing:** VERIFIED — Amazon/Shopify/Etsy/eBay plans start at **$29/month**; the **Walmart plan starts at $79/month**; multi-channel "A2X Multi" plans cost more; pricing scales with monthly order volume. Suitable from 100 to 1,000,000 orders/month, so it doesn't need to be revisited as Habib scales.
- **Track record:** REPORTED — won Xero's "Practice App of the Year" (UK/Canada, 2024) and "Small Business App of the Year" (US, 2025), suggesting mature Xero integration specifically.
- **Verdict:** The category leader; buy this when Amazon US or Walmart makes settlement complexity worth automating (arguably already worth it for Amazon.ca alone given multi-currency).

### Link My Books

- **Pricing model:** Uses an interactive calculator (order volume × channel count × currency) rather than flat published tiers; supports GBP/USD/AUD in its calculator (CAD not explicitly listed — verify before buying, given Habib's Canadian home currency). [Link My Books A2X alternatives comparison](https://linkmybooks.com/blog/comparison-of-the-best-a2x-alternatives-for-ecommerce-accounting-2026-guide)
- **Verdict:** Credible A2X alternative; the CAD-currency gap in its own marketing needs direct confirmation before ruling it in or out for Habib.

### Synder

- **Pricing:** VERIFIED (vendor-adjacent) — Basic $65/mo (monthly) or $52/mo (annual): up to 500 transactions, 2 integrations, daily sync, basic inventory tracking, multi-currency; Essential from $115/mo ($92 annual); Pro from $275/mo ($220 annual). [Synder/Taxomate pricing comparison](https://linkmybooks.com/blog/synder-alternatives)
- **Verdict:** Pricier than A2X/Taxomate at comparable transaction volumes; multi-currency support is built in from the Basic tier, relevant for Habib's CAD/USD split.

### Taxomate

- **Pricing:** VERIFIED (vendor-adjacent) — Basic $52/mo (500 transactions, 2 integrations, daily sync); Essential from $92/mo (500-3,000 transactions, unlimited integrations, hourly sync); Pro from $220/mo (3,000-50,000 transactions, bundle/assembly sync). The **Multi plan scales by order volume while keeping channel connections unlimited** — a materially better model than per-channel pricing once Habib adds Amazon US and Walmart. [Taxomate pricing analysis](https://linkmybooks.com/blog/taxomate-pricing)
- **Verdict:** Best-value settlement connector for a seller actively adding marketplaces, specifically because of the unlimited-channels-on-Multi-plan structure — worth comparing head-to-head against A2X's Multi plan pricing before Amazon US launch.

### QuickBooks Online vs Xero — general ledger choice

- **QuickBooks:** VERIFIED-ish — Solopreneur $20/mo, Simple Start $35/mo, **Plus $99/mo is the minimum tier with native inventory tracking** — most Amazon-relevant features sit in the pricier tiers. [Eightx QBO vs Xero](https://eightx.co/blog/xero-vs-quickbooks-for-ecommerce)
- **Xero:** VERIFIED-ish — Early $25/mo, Growing $47/mo (unlimited users, no invoice cap); reported as **stronger for international sellers needing multi-currency and GST/VAT handling** — directly relevant to Habib's CAD/USD split and GST/HST obligations.
- **Blended stack cost:** REPORTED — most $1M-revenue sellers land at **$113/mo (Xero + A2X)** to **$173/mo (QBO + A2X)** for the combined GL + connector stack. [same source]
- **Official MCP servers:**
  - **QuickBooks Online: VERIFIED — Intuit released an official, open-source QBO MCP server** (TypeScript/Node.js) in October 2025 as an early preview, providing full CRUD across 29 entity types and 11 financial reports, runnable locally for Claude Code and other MCP clients. [Intuit's official GitHub repo](https://github.com/intuit/quickbooks-online-mcp-server), [Numeric QuickBooks MCP setup guide](https://www.numeric.io/blog/quickbooks-mcp)
  - **Xero: no official MCP server as of April 2026** — only third-party/community implementations exist (StackOne — 70 actions; Composio — Claude Agent SDK integration guide; CData; community GitHub projects). [Composio Xero + Claude Agent SDK](https://composio.dev/toolkits/xero/framework/claude-agents-sdk"), [StackOne Xero MCP](https://www.stackone.com/connectors/xero/mcp/)
- **Verdict for Habib's Finance agent architecture:** This is a real trade-off. Xero is the better fit on multi-currency/GST grounds and per-dollar cost, but **QuickBooks Online is the only one of the two with an official first-party MCP server** — meaningfully lower integration risk for an agent-run Finance function (Habib's CLAUDE.md already avoids "parallel systems that drift"; a third-party Xero MCP connector is one more unofficial dependency). Given CLAUDE.md's "solo operator, simplicity over cleverness" principle, **recommend QuickBooks Online Plus ($99/mo) + A2X**, accepting the higher sticker price for first-party MCP support, unless Rami is comfortable maintaining a community Xero MCP connector for the multi-currency/GST advantage.

### Canadian GST/HST — what actually applies to Habib

- **Marketplace facilitator collection:** VERIFIED (multiple CPA-firm sources) — since July 1, 2021, Amazon as a "distribution platform operator" must collect and remit GST/HST on behalf of non-resident (or unregistered) sellers on sales to Canadian addresses; Amazon does this automatically if the seller isn't separately GST/HST-registered. [Jones & Cosman: Does Amazon collect GST/HST](https://jonescosman.com/does-amazon-collect-and-pay-sales-tax-gst-for-sellers-on-amazon-canada.html)
- **Registration threshold is worldwide, not Canada-only:** VERIFIED (multiple sources) — the CAD $30,000 GST/HST registration threshold is calculated on **worldwide sales** over any four rolling calendar quarters, not just Canadian-address sales. A seller with $0 Canadian revenue but $40,000 in US sales is already past the threshold. [Beancount.io GST/HST guide](https://beancount.io/blog/2026/07/13/canada-gst-hst-cross-border-online-sellers-guide), [Eightx GST/HST explainer](https://eightx.co/blog/what-is-gst-hst-ecommerce)
  - **Applies directly to Habib:** at $10k/mo now scaling to $85k/mo, Habib is already well past the $30k/year worldwide threshold and should already be GST/HST-registered if not already.
- **Input tax credit upside:** REPORTED — once registered, GST paid on Amazon fees, advertising, freight, and customs becomes recoverable as input tax credits — a reason to register proactively rather than wait to be forced to.
- **USD/CAD FX:** UNKNOWN from these searches — no dedicated authoritative source on FX handling/hedging was surfaced; this needs either a follow-up query focused specifically on multi-currency bookkeeping mechanics (A2X/Xero both claim native multi-currency handling per their marketing) or direct consultation with a cross-border CPA, which several of the sources above (salaccounting.ca, jonescosman.com) explicitly specialize in.

### Cash-flow forecasting tools with API

- **Float:** REPORTED — best pure visual forecaster for Xero/QuickBooks users; **$49/mo** entry scaling to **$179/mo** for advanced/higher-volume. [Fathom cash flow tools roundup](https://www.fathomhq.com/blog/the-best-cash-flow-forecasting-software)
- **Fathom:** REPORTED — wins on board-style reporting and three-way (P&L/balance sheet/cash flow) modeling; 4.7 G2 rating.
- **Pulse:** REPORTED — cheapest option at **$29/mo**, simple cash calendar, positioned for small businesses/solopreneurs without needing a full finance-automation platform. [successknocks.com solopreneur cash flow tools](https://successknocks.com/best-cash-flow-forecasting-tools-for-solopreneurs/)
- **API availability:** UNKNOWN for all three — no dedicated API documentation surfaced in these searches; all three connect via Xero/QBO's own data (so once the GL is chosen, these read from it rather than requiring a separate SP-API integration).
- **Verdict:** None of these are essential yet. At Habib's stage, a Claude Finance agent reading `profit_daily`/`sales_daily`/`fees_daily` directly from Supabase (already the planned architecture per CLAUDE.md) plus GL data via the QBO MCP server can produce a cash-flow projection without paying for Float/Fathom/Pulse — revisit only if Rami specifically wants a human-facing visual dashboard for his father (a finance stakeholder per CLAUDE.md's operator roster) rather than an agent-generated brief.

### Section 4 — Minimum Viable Stack for a Solo Operator + AI Finance Agent

1. **GL:** QuickBooks Online Plus ($99/mo) — for the official MCP server — or Xero Growing ($47/mo) if Rami accepts a community MCP connector for better multi-currency/GST fit.
2. **Settlement connector:** A2X Amazon plan ($29/mo, add Walmart plan $79/mo when Walmart launches) or Taxomate Multi (unlimited channels) if adding Amazon US + Walmart makes per-channel A2X pricing add up.
3. **GST/HST:** confirm registration status now (worldwide-revenue threshold already passed); register if not done; set up input tax credit tracking.
4. **Cash-flow forecasting:** skip dedicated software initially — build from Supabase `profit_daily`/`fees_daily` + GL data via Claude Finance agent; revisit Float/Pulse only for a human-visual dashboard need.
5. **FX:** flag as an open item requiring direct CPA consultation (see Section 5's customs-broker/CPA discussion for a parallel need).


---

## 5. Freight, Customs, Landed Cost & Food Import Compliance (CA + US)

> **Note on this section:** the session's web search budget was exhausted partway through this section (200/200 calls used across this research session). The freight/customs sub-sections below are fully sourced; the **US nutrition-label** and **end-to-end consultant cost** items could not be freshly verified and are marked UNKNOWN / flagged for follow-up — treat those specific bullets as needing a dedicated follow-up search or a compliance consultant call before acting on them, rather than as researched findings.

### Flexport — API and AI agents

- **Scale of AI adoption:** VERIFIED (vendor announcement, reported via BusinessWire) — Flexport announced in March 2026 that its AI agent system **autonomously manages 40% of freight forwarding operations**, up from 8% in January 2025. [BigGo Finance coverage](https://finance.biggo.com/news/Q8AunZwB5edQG9E4Sufw), [callsphere.ai agentic AI coverage](https://callsphere.ai/blog/agentic-ai-supply-chain-flexport-maersk-autonomous-logistics)
- **2026 Winter Release agents:** VERIFIED (vendor page) — includes an AI customs auditor ("Audit Your Customs Broker," which audits all past customs entries for errors), an automated tariff-refund/duty-drawback agent, a container-consolidation optimization agent (reported ~10% average freight cost savings by pooling shipments), and a real-time AI translator. [Flexport 2026 Winter Release](https://www.flexport.com/technology/product-release/winter-2026/), [Businesswire: Flexport tariff refund automation](https://www.businesswire.com/news/home/20260226536552/en/Flexport-Launches-Technology-to-Automate-Tariff-Refunds)
- **Fit for a business Habib's size:** UNKNOWN — none of the sources confirmed Flexport's minimum shipment volume or a small-importer pricing tier; Flexport is generally known as an enterprise-oriented freight forwarder. The AI-agent tooling is compelling in principle (a "customs broker audit agent" is directly relevant to catching CBP/CBSA classification errors) but worth confirming Flexport will even onboard a business shipping Habib's current container volumes before treating this as a real option.
- **General guidance for small forwarders:** REPORTED — most small importers start AI adoption with document extraction or quoting automation (highest manual-hour consumers), adding shipment-visibility tooling only as volume grows. [Mirage Metrics: Best AI tools for freight forwarders 2026](https://miragemetrics.com/blog/best-ai-tools-freight-forwarders/)

### Freightos

- **What it offers:** VERIFIED (vendor) — a free, embeddable landed-cost calculator and container/international-freight shipping-cost calculators, plus a developer portal with freight APIs (rate/routing data). [Freightos Developer Portal](https://developers.freightos.com/freight-tools), [Freightos landed cost explainer](https://www.freightos.com/freight-resources/understanding-landed-cost-and-profitability/)
- **Digital customs brokerage:** REPORTED — Freightos (the parent of WebCargo) operates a vendor-neutral freight-booking/payment marketplace and reportedly also offers digital customs brokerage services connecting importers to providers.
- **Currency/timeliness warning:** REPORTED, important — a landed-cost model built before the 2025-2026 US tariff and de minimis rule changes will **understate true import costs**; Freightos' own calculators were updated for May 2026 tariff rates, underscoring that any landed-cost spreadsheet Habib's Finance agent builds needs a live tariff-rate input, not a static assumption. [context from search results on 2026 tariff changes]
- **Verdict:** Freightos' free calculator/API tooling is the more realistic starting point for Habib than Flexport given company size — worth wiring the landed-cost API into the Supply Chain agent's PO-costing math rather than hardcoding tariff assumptions.

### FDA food-import compliance (for the Jan 2027 Amazon US launch)

- **Food Facility Registration (FFR):** VERIFIED (FDA-adjacent sources) — must be renewed on the **Biennial Renewal window, Oct 1 - Dec 31 of every even-numbered year** (2026, 2028, ...); missing the window **automatically cancels registration and blocks all US food shipments** until re-registered. [Registrar Corp FSVP/FFR guide](https://www.registrarcorp.com/blog/food-beverage/food-facility-registration/must-fsvp-food-importers-register-fda/)
  - **Timing flag for Habib:** 2026's biennial renewal window (Oct-Dec 2026) lands directly before the planned Jan 2027 US launch — registration/renewal needs to be confirmed as part of that launch's compliance checklist, not treated as a formality.
- **Prior Notice:** VERIFIED-ish — FDA requires advance notice of incoming food shipments, filed **2-8 hours before arrival depending on transport mode**, and Prior Notice filings must reference the supplier's valid FFR number or shipments risk detention at the port of entry. [context from FDA/Prior Notice guidance search results]
- **FSVP (Foreign Supplier Verification Program):** VERIFIED-ish — as the US importer, Habib (or its designated US agent/importer of record) is responsible for hazard analysis of the food, evaluating and approving foreign suppliers' food-safety performance **before** importing, periodic supplier verification, and FSVP recordkeeping. This is an ongoing compliance program, not a one-time filing.
- **US nutrition label rules:** **UNKNOWN — not independently verified this session** (search budget exhausted before this sub-topic could be researched). Recommend a dedicated follow-up: confirm current FDA Nutrition Facts label format requirements (post-2020 rule updates), any bilingual/French-Canadian label differences vs. US-only labels, and whether Habib's existing Canadian packaging needs separate US-market SKUs or can use a dual-market label design.

### CFIA SFCR licensing (Canada — Habib's home base)

- **Licence required before border presentation:** VERIFIED (CFIA-adjacent + CBSA sources) — an SFC licence must be obtained **before** presenting a shipment at the border; it **cannot be obtained at the border**. [CBSA Customs Notice 24-03](https://www.cbsa-asfc.gc.ca/publications/cn-ad/cn24-03-eng.html)
- **Manufactured foods sector coverage:** VERIFIED — licensing requirement for the "manufactured foods" sector (confectionery, snack foods, non-alcoholic beverages, grain-based foods — **the category Habib's Middle Eastern food products likely fall under**) came into force **July 15, 2020**. [CFIA food business activities requiring a licence](https://inspection.canada.ca/en/food-licences/food-business-activities)
- **Application process:** VERIFIED — done through the **My CFIA** online portal; no fax/email applications accepted. [CFIA licensing page](https://inspection.canada.ca/en/food-safety-industry/information-media/licensing)
- **Additional requirements:** REPORTED — most importers need a documented Preventive Control Plan (PCP), traceability systems, recall procedures, and a supplier-approval program alongside the licence itself — this is an ongoing compliance program similar in shape to the US FSVP, not a one-time application.
- **Verdict:** Assuming Habib already imports/distributes in Canada today, an SFC licence under SFCR is very likely already required — this should be confirmed as already-in-place rather than treated as new work; if not yet licensed, this is higher-priority than the US launch prep given it governs current Amazon.ca operations.

### End-to-end consultants/services for small food brands

**UNKNOWN — not independently researched this session** due to exhausted search budget. This is a genuine gap: the user asked specifically for "services/consultants that handle this end-to-end for a small brand and rough costs," and no vendor names or price ranges were verified. **Recommend a dedicated follow-up research pass** (or a direct outreach round) covering: FDA compliance consulting firms (e.g., the type of firms indexed in the FDA-guide sources above — Registrar Corp, Stile Associates, JADE International appeared in search results as FDA-import-compliance content publishers and may also offer consulting services, but this was not confirmed), customs brokerage firms serving small CA-US food importers, and CFIA-side compliance consultants for the SFCR PCP/traceability requirements. Do not treat any dollar figure as known until that follow-up is done.

### Section 5 Verdict

The clearest, best-sourced action items from this section: (1) confirm Habib's CFIA SFC licence is current for existing Canadian operations — likely already required; (2) build the Jan 2027 US-launch compliance checklist around the Oct-Dec 2026 FFR biennial renewal window, Prior Notice filing setup, and an FSVP program with a named "qualified individual" — this is a real workstream, not a checkbox; (3) wire a live landed-cost/tariff feed (Freightos' API is the accessible option) into the Supply Chain agent rather than hardcoding tariff assumptions, given how fast 2025-2026 tariff rules have moved; (4) Flexport's AI-agent tooling is interesting to watch but unconfirmed as accessible/priced for Habib's shipment volume; (5) nutrition-label rules and end-to-end compliance-consultant options are genuine open items requiring follow-up research beyond this session's search budget.


---

## 6. Supplier Communication & PO Management

> **Sourcing note:** this section's web-search budget was fully consumed before reaching this topic (see Section 5 note). The tool comparisons below draw on general knowledge of these products' known positioning rather than freshly fetched 2026 pricing/feature pages, and are marked accordingly. Verify pricing and current feature sets directly with vendors before purchasing.

### The baseline: Gmail + markdown supplier file + PO template

- This is effectively what CLAUDE.md's own architecture already implies for Habib: Supabase already holds `supplier_shipments`, `supplier_shipment_items`, `product_cost_history`, and `inbound_shipments` — i.e., the **structured PO/shipment data already lives in the source of truth**, not in a separate tool. Gmail remains the communication channel with suppliers (POs sent as PDF/email, confirmations received by email), and a markdown or Supabase-backed supplier directory (contact info, lead times, MOQs, payment terms) covers the reference data.
- **UNKNOWN/REPORTED (general knowledge, not independently verified this session):** for ~10-30 active suppliers (plausible count for 15-60 SKUs of Middle Eastern food products, likely concentrated among fewer manufacturers/importers), a dedicated supplier-management tool's main value-add over Gmail+markdown is (a) a shared multi-user view when more than one person emails suppliers, (b) automated PO-status tracking with reminders, and (c) supplier scorecarding (on-time %, defect rate) over time. None of these are pressing needs for a solo operator per CLAUDE.md's explicit "solo operator first" principle.

### Anvyl

- REPORTED (general knowledge) — a supply-chain collaboration platform positioned for consumer brands managing multiple contract manufacturers, with PO tracking, supplier messaging threads, and production-milestone tracking. Historically priced/positioned for mid-market brands with dedicated supply-chain staff, not solo operators. **Not independently verified this session — treat pricing/current features as UNKNOWN.**
- **Verdict:** likely SKIP — built for a supply-chain team's workflow, not a solo operator's.

### Sourcify

- REPORTED (general knowledge) — historically more of a sourcing/manufacturer-matching service (find and vet a factory) than an ongoing PO-management tool. Not a natural fit for Habib, which already has established suppliers rather than needing new-factory sourcing.
- **Verdict:** SKIP — solves a different problem (finding suppliers) than the one Habib has (managing known suppliers).

### Zoho Inventory

- REPORTED (general knowledge) — a genuine low-cost inventory/PO/order-management tool with multi-warehouse tracking, PO generation, and some Amazon/Shopify integrations; part of the broader Zoho suite so it can pull in Zoho Books (accounting), Zoho CRM, etc. Pricing historically in the $0-$249/mo range depending on tier and order volume. **Not independently verified this session.**
- **API:** Zoho has historically published REST APIs across its suite, which would make it a plausible (if redundant) structured store if Habib wanted an off-the-shelf PO/inventory UI instead of a Supabase-native one.
- **Verdict:** Possible SKIP given redundancy — Habib's Supabase schema already covers `supplier_shipments`/`inbound_shipments`/`product_cost_history`, and introducing Zoho Inventory as a second inventory system directly violates CLAUDE.md's "one source of truth" principle (Section 1's Core Design Principles explicitly warn against "parallel systems that drift"). Only reconsider if the Supabase-native PO workflow proves to need more UI polish than a Telegram/dashboard approval flow can deliver.

### Airtable / Notion as ad hoc supplier trackers

- Commonly used by small brands as a lightweight supplier CRM (contact info, lead times, pricing history, document links) with more structure than a spreadsheet but less overhead than a full SCM platform. See Section 7 for the MCP-server angle on these two specifically, since the question of "Airtable/Notion vs. plain CSV/markdown" is really the same architectural question as Section 7's data-store comparison, just applied to supplier data specifically.

### Section 6 Verdict

**Skip all four named tools (Anvyl, Sourcify, Zoho Inventory) as core infrastructure.** Habib's Supabase schema already models suppliers/shipments/costs, and CLAUDE.md's own design principles (solo operator, one source of truth, simplicity over cleverness) argue directly against adding a parallel supplier-management SaaS product for what is currently a Gmail-and-structured-database workflow. The one plausible exception is a **lightweight Notion or Airtable page as a human-readable supplier directory** (contact info, MOQs, payment terms, lead times) that a Claude Supply Chain agent can also read via MCP (Section 7) — useful as the *qualitative* reference data that doesn't belong in relational tables, sitting alongside (not replacing) the Supabase `supplier_shipments` tables that hold the *quantitative* PO/shipment data.

---

## 7. Structured Store for an Agent Company

> **Sourcing note:** same search-budget caveat as Section 6 — this section draws on general/training knowledge of Google Sheets MCP, Airtable MCP, and Notion MCP server availability and characteristics as of early-to-mid 2026, not freshly verified vendor pages. The Anthropic MCP ecosystem moves quickly; verify current server availability and auth model directly (e.g., via an MCP marketplace or the vendor's own developer docs) before building on any specific server.

### The question CLAUDE.md already answers for the core system

CLAUDE.md is explicit and consistent throughout: **Supabase is the single source of truth** ("One source of truth... No parallel systems that drift," Section 1) and agents access it via direct `supabase-py` queries, not MCP, specifically because MCP "adds unnecessary network hops for scheduled jobs" (Section 3.3). This is the right call for the system's *core* structured data (products, orders, inventory, PPC stats, financials) — nothing in this research changes that recommendation. The open question this section actually addresses is narrower: **where should the small amount of unstructured/semi-structured reference data live** — supplier notes, competitor research scratch-notes, one-off business knowledge that doesn't fit a relational schema and isn't performance-sensitive enough to need synchronous Python queries.

### Google Sheets MCP servers

- REPORTED (general knowledge) — several community and first-party-adjacent Google Sheets MCP servers exist, generally wrapping the Google Sheets API for read/write/append operations authenticated via a Google service account or OAuth. Because Google Sheets is free, familiar to non-technical stakeholders (Rami's father, brother), and already the lowest-friction way to hand a spreadsheet to a human collaborator, it's a plausible "human-editable, agent-readable" layer for things like a manually-maintained supplier price list or a father/brother-editable notes sheet the agents periodically read.
- **Fit:** Good for **human-in-the-loop reference data** that non-technical operators (father: finance, brother: sales/marketing — both named explicitly in CLAUDE.md's Project description) want to edit directly without touching Supabase or a dashboard.

### Airtable MCP

- REPORTED (general knowledge) — Airtable's own API is mature and well-documented, and MCP servers wrapping it (community-built) are common. Airtable's relational-lite structure (linked records, views, kanban boards) is a genuinely better fit than a flat spreadsheet for something like a supplier directory with linked PO history, or a competitor-tracking board with linked product records — closer to a lightweight relational database with a friendlier UI than Sheets, at a real monthly cost (Airtable's paid tiers) that Sheets doesn't have.
- **Fit:** Better than Sheets specifically when the reference data has real relationships (supplier → products → shipments) that a flat sheet handles awkwardly, but that don't warrant a new Supabase table.

### Notion MCP

- REPORTED (general knowledge) — Notion has an official public API and MCP server; strong for **long-form, narrative content** — which maps directly onto CLAUDE.md's own `wiki_pages` design (Section 3.2, Section 10.3 Wiki Compiler) that already stores generated markdown wiki content in Supabase for a Next.js dashboard to render. Notion could serve as either (a) a competing wiki surface (redundant with the planned `wiki_pages`/dashboard approach — avoid, per "one source of truth"), or (b) a place for **human-authored** notes (Rami's own working notes, meeting notes, ideas) that are separate from agent-generated content and don't need to feed back into the agent's knowledge loop at all.

### Plain CSV/markdown in git

- The lowest-overhead, most durable, most version-controlled option — and the one CLAUDE.md's own GSD workflow and repo structure already lean toward for anything code- or config-adjacent. Zero cost, zero new auth surface, zero new failure mode (no third-party API to go down), and naturally diffable/auditable via git history — a meaningful advantage for a solo operator per CLAUDE.md's "if it needs babysitting, it's wrong" principle. The tradeoff: no non-technical collaborator (father, brother) can edit it without a developer workflow, and no MCP server is needed at all since Claude Code (or the agents' own file access) can read files in the repo directly.

### Section 7 Verdict — matched to who needs to touch the data

| Data | Best store | Why |
|---|---|---|
| Core business data (products, orders, inventory, PPC, financials) | **Supabase** (already CLAUDE.md's decision) | Single source of truth; direct Python queries, no MCP hop for scheduled agent runs |
| Mem0 knowledge (observations/patterns/playbooks) | **Mem0 + pgvector on Supabase** (already CLAUDE.md's decision) | Purpose-built for agent memory; no change indicated by this research |
| Generated wiki content | **`wiki_pages` table in Supabase** (already CLAUDE.md's decision) | Avoids a second wiki system (Notion) drifting from the Mem0-derived source |
| Supplier directory / reference notes that non-technical operators (father, brother) may want to glance at or lightly edit | **Google Sheets (with MCP for agent read access)** or a Notion page | Free/cheap, familiar UI for non-technical stakeholders, agent-readable via MCP without becoming a second system of record for transactional data |
| Structured-but-relational reference data with real cross-links (e.g., supplier ↔ products ↔ shipment history) if it ever outgrows a flat sheet | **Airtable (with MCP)** | Better fit than Sheets for linked-record data; still cheap relative to a new Supabase migration for low-stakes reference data |
| Anything code-, config-, or prompt-adjacent (system prompts, L1 rules drafts, runbooks) | **Plain markdown/CSV in the git repo** | Zero new auth surface, version-controlled, matches CLAUDE.md's existing GSD/repo-based workflow; no non-technical editing need for this category |

**Recommendation:** Don't add Airtable or Notion as new paid infrastructure yet — Habib's actual unmet need in this category is small (a supplier directory, maybe some competitor scratch-notes) and a **free Google Sheet with a Google Sheets MCP server for agent read access** covers it with zero new recurring cost, while keeping git/markdown for anything developer-facing. Revisit Airtable specifically if the supplier directory grows enough cross-linked structure (multiple contacts per supplier, linked PO history, linked product mappings) that a flat sheet becomes error-prone — a threshold likely to arrive around the same SKU/marketplace growth point discussed in Section 2, not before.


---

## Recommended Stack for Supply Chain

| Candidate | Buy / Skip | Weekly data fed to the agent |
|---|---|---|
| Sellerboard | **Buy** ($15-19/mo) | Cross-check profit-per-SKU numbers against Habib's own `profit_daily`; Walmart-ready for later. Delivered via scheduled CSV/email, not live API. |
| Nova Analytics MCP | **Trial** (free/$29/mo) | Prototype/validation feed only — orders, fees, PPC, inventory across marketplaces, MCP-native. Not a replacement for Supabase. |
| SoStocked / Inventory Planner / Cin7 / Flieber | **Skip now** | None — re-evaluate RestockPro specifically once SKU × marketplace pairs exceed ~100-150 (roughly the Amazon US launch). |
| RestockPro | **Watchlist** | PO/restock decisions, if the in-house agent's restock math needs a UI/workflow layer later. |
| Getida or Refunds Manager | **Buy** (0 fixed cost, 25% of recovered $) | Weekly/monthly reimbursement-recovery report — pure upside, no agent build needed. |
| Threecolts Seller 365 Reimbursements | **Revisit at Walmart launch** | Walmart WFS + FBA combined reimbursement coverage. |
| Freightos landed-cost API | **Buy/integrate** | Live tariff-adjusted landed cost per shipment, feeding the Supply Chain agent's PO-costing math. |
| Flexport | **Watch, don't commit** | Unconfirmed fit for Habib's volume — revisit if shipment volume grows enough to need a full forwarder relationship. |
| CFIA SFCR licence / FDA FSVP-FFR-Prior Notice program | **Mandatory compliance, not optional** | Feeds the Supply Chain agent a go/no-go gate on the Jan 2027 US launch timeline (FFR biennial renewal window Oct-Dec 2026). |
| Anvyl / Sourcify / Zoho Inventory | **Skip** | N/A — redundant with Supabase `supplier_shipments`/`inbound_shipments`. |
| Google Sheets + MCP (supplier directory) | **Buy** (free) | Weekly-refreshed supplier contact/lead-time/MOQ reference data, human-editable by non-technical operators. |

## Recommended Stack for Finance

| Candidate | Buy / Skip | Weekly data fed to the agent |
|---|---|---|
| QuickBooks Online Plus + official MCP server | **Buy** ($99/mo) | GL balances, AP/AR, reconciliation status — via first-party MCP, lowest integration risk. |
| A2X (Amazon plan now, Walmart plan later) | **Buy** ($29/mo, +$79/mo at Walmart launch) | Weekly settlement-to-GL journal entries reconciling Amazon deposits to `sales_daily`/`fees_daily`. |
| Xero + community MCP | **Alternative, not primary** | Same GL role as QBO, better multi-currency/GST fit, but no first-party MCP — accept only if Rami will maintain the connector. |
| Taxomate Multi | **Watchlist** | Reconsider vs. A2X specifically once Amazon US + Walmart both active (unlimited-channel pricing). |
| GST/HST registration | **Mandatory, likely overdue** | Feeds the Finance agent input-tax-credit tracking and remittance status. |
| Float / Fathom / Pulse | **Skip for now** | None — build cash-flow projection from Supabase `profit_daily` + QBO MCP data instead. |
| Getida / Refunds Manager | **Buy** (see Supply Chain table — same tool, dual relevance) | Recovered-reimbursement dollars flow into `profit_daily` reconciliation. |
| Freightos landed cost | **Buy/integrate** (see Supply Chain table) | Feeds true COGS into per-SKU profit calculations, closing the loop with Section 1's profit-analytics tools. |

