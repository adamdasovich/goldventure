# AI Assistant Tools — Analytics & Research

This document describes the analytics and research tools available to the
GoldVenture AI assistant, what each one does, and how users reach them.

---

## How users access these tools

These tools are **not pages or buttons** in the site navigation. They are
capabilities the **AI chatbot** calls automatically, based on what a user asks
in plain English. The user never selects a tool — they just ask a question, and
the assistant picks the right tool, runs it, and answers.

There are two places to chat with the assistant:

| Interface           | Where it lives                                                   | Scope                           |
| ------------------- | ---------------------------------------------------------------- | ------------------------------- |
| **Platform chat**   | Homepage, and the `/investor-tools/ni43-101-analyzer` page       | All companies, sector-wide      |
| **Company chatbot** | Floating widget on every company detail page (`/companies/{id}`) | That company, plus sector tools |

So "how do I use the resource-growth tool?" has no UI answer — you **ask the
chatbot** something like _"How has Aston Bay's gold resource grown over time?"_
and it runs `insights_resource_growth` behind the scenes.

> **Discoverability note:** because the tools are invisible, users only find
> them by asking. If broader adoption is wanted, consider surfacing example
> prompts in the chat UI (suggested-question chips) or a short "What can I ask?"
> help panel. That is a separate UI task and is not built yet.

---

## Analytics tools (`insights_*`)

Ten tools that turn the platform's historical data into investor insight.

### Market & performance

#### 1. Stock Performance Comparator

**Tool:** `insights_compare_stock_performance`
Compares the % share-price change of 2–10 companies over a chosen window, with a
best-to-worst ranking and each company's daily volatility.

_Ask the assistant:_

- "Compare the stock performance of Aftermath Silver, Aston Bay and GROY over 6 months."
- "How has 1911 Gold's share price moved over the last 90 days?"

_Returns:_ per-company start/end price, % change, daily volatility, ranking.

#### 2. Catalyst Impact Analyzer

**Tool:** `insights_catalyst_impact`
An event study for one company: measures how its share price historically
reacted to each _type_ of news (drill results, financings, resource updates,
etc.) at 1, 5 and 20 trading days after the release.

_Ask the assistant:_

- "Does Aston Bay's stock actually move on drill results?"
- "Which kind of news has moved 1911 Gold the most?"

_Returns:_ per news-type average price reaction at each horizon, with sample sizes.

#### 3. Unusual Activity Detector

**Tool:** `insights_unusual_activity`
Flags days when trading volume spiked far above the company's trailing 20-day
average, and cross-references news to label each spike _explained_ or
_unexplained_.

_Ask the assistant:_

- "Has there been any unusual trading volume in Aftermath Silver lately?"
- "Show me abnormal volume days for this company in the last 3 months."

_Returns:_ flagged days with volume ratio, price change, and related news (if any).

### Capital & financing

#### 4. Dilution Tracker

**Tool:** `insights_dilution_history`
Shows a company's share-dilution history from its financing record — shares
issued per raise, cumulative issuance vs. current shares outstanding, and
outstanding warrant tranches.

_Ask the assistant:_

- "How much has this company diluted shareholders?"
- "What's the warrant overhang on Affinity Metals?"

_Returns:_ per-financing detail, total shares issued, % of current float, active
warrant tranche count.

#### 5. Sector Capital-Flow Monitor

**Tool:** `insights_capital_flow`
Aggregates sector-wide financing activity into monthly trends — total raised,
deal count, average raise size, and breakdowns by financing type and commodity.

_Ask the assistant:_

- "How much capital has the junior mining sector raised this year?"
- "Show financing trends for gold companies over the last 12 months."

_Returns:_ monthly capital-raised series, by-type and by-commodity breakdowns.

### Projects & technical

#### 6. Project Due-Diligence Assistant

**Tool:** `insights_project_due_diligence`
Answers a technical question about a company by semantic search (RAG) across its
processed NI 43-101 reports, returning relevant passages with citations.

_Ask the assistant:_

- "What are the metallurgical recovery results in Aston Bay's reports?"
- "What does the technical report say about permitting risk?"

_Returns:_ ranked report passages with document title/date citations.

#### 7. Resource Growth Tracker

**Tool:** `insights_resource_growth`
Tracks how a company's mineral resource estimates evolved across successive
NI 43-101 reports — contained ounces, grade and tonnage by category over time.

_Ask the assistant:_

- "Has Aston Bay's gold resource grown over time?"
- "Show the resource estimate history for this project."

_Returns:_ per-project timeline of estimates with a first-vs-latest growth summary.

#### 8. Economic Study Re-Rater

**Tool:** `insights_economic_rerate`
Re-rates a project's economic study (PEA/PFS/FS) at today's gold price. Studies
bake in a gold-price assumption; this compares it to the live price and
estimates the revalued NPV and lifetime cash-flow uplift. **Gold projects only.**

_Ask the assistant:_

- "What is this project worth at today's gold price?"
- "How stale is the PEA's gold price assumption?"

_Returns:_ per-study original vs. re-rated NPV, margin leverage, lifetime cash-flow delta.

### Valuation

#### 10. Peer Valuation Screener

**Tool:** `insights_peer_valuation`
Ranks companies by market capitalization per contained resource ounce ("ounces
in the ground" valuation) to surface cheap vs. expensive peers. Filterable by
commodity and country.

_Ask the assistant:_

- "Which gold companies look cheap relative to their resources?"
- "Rank these companies by market cap per ounce."

_Returns:_ ranked list with market-cap-per-oz, plus the cheapest/most-expensive
and the median.

### Personal

#### 11. Daily Briefing

**Tool:** `insights_daily_briefing`
Generates a digest of recent activity across the logged-in user's watchlist —
price moves, news, new financings and new documents per company. **Requires a
logged-in user with a watchlist.**

_Ask the assistant:_

- "Give me a briefing on my watchlist."
- "What happened with my companies this week?"

_Returns:_ per-company recent activity, ordered most-active first.

---

## NI 43-101 report tools (`reports_*`)

Three tools that give the assistant direct access to NI 43-101 technical reports
stored in the platform's databases (previously it could only handle reports
supplied as a direct URL).

#### Vector report search — `reports_vector_search`

Semantic search over stored NI 43-101 reports in the vector database. Returns
ranked report passages with relevance scores and source metadata.
_Ask:_ "Find anything about gold recovery in stored technical reports."

#### Structured report search — `reports_search_technical`

Structured search of the documents table by company, project, commodity, date
and report type. Returns document identifiers and metadata.
_Ask:_ "What technical reports do we have for Aston Bay?"

#### Report content retrieval — `reports_get_content`

Fetches a report's full text (if processed) or an accessible URL, given a
document identifier from the two search tools above.
_Ask:_ (used automatically as a follow-up to the search tools)

---

## Data-coverage caveats

Several tools are fully built and deployed but depend on data that is currently
sparse. They return correct, honest "no data" responses until the data fills in:

| Tool                            | Depends on                                    | Current state                                                                                                  |
| ------------------------------- | --------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `insights_economic_rerate` (#8) | `EconomicStudy` rows                          | Ingestion bug fixed; populates on **newly processed** reports — existing reports need reprocessing to backfill |
| `insights_peer_valuation` (#10) | `Company.market_cap_usd` + `ResourceEstimate` | Only ~28 of 396 companies have a market cap; few have resource estimates                                       |
| `insights_resource_growth` (#7) | `ResourceEstimate` rows                       | Populated for only a handful of companies                                                                      |
| `insights_daily_briefing` (#11) | User watchlists                               | No users have watchlists yet                                                                                   |
| Metals re-rate / trends         | `MetalPrice`                                  | Gold/silver/platinum/palladium only — no base-metal price history                                              |

These are data-pipeline matters, not tool defects. The tools light up
automatically as coverage improves.

---

## Developer notes

- **Code:**
  - `backend/mcp_servers/insights_tools.py` — `InsightsToolsServer` (10 tools, `insights_` prefix)
  - `backend/mcp_servers/ni43101_reports.py` — `NI43101ReportsServer` (3 tools, `reports_` prefix)
- **Registration:** each tool is registered in `backend/mcp_servers/tool_registry.py`
  (metadata + prefix→server mapping) and routed in both
  `backend/claude_integration/client.py` and `client_optimized.py`.
- **Adding a tool:** add a definition to the server's `get_tool_definitions()`,
  a handler, a `tool_registry.py` metadata entry, and — only if introducing a
  new prefix — a routing entry in the registry and both clients.
- **Tool discovery:** the assistant uses progressive tool discovery; tools are
  loaded by category based on the user's query, or found via
  `search_available_tools`. Rich keywords in the registry metadata are what
  make a tool discoverable for a given question.
