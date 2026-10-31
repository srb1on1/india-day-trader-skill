# India Day Trader Skill

An India-focused adaptation of the open-source Day Trader skill. The project is intended to help Codex analyze Indian cash-market data and produce transparent, read-only setups from FYERS market data.

## Feasibility

**Feasible.** FYERS V3 exposes quotes, historical OHLCV candles, symbol information, screeners, option chains, and streaming market data. The original skill's reusable ideas—watchlists, completed-candle breakout checks, exits, sizing, replay, and risk checks—can be adapted. Its US-specific data universe, time zone, exchange calendar, news sources, and broker integration cannot be reused as-is.

The main integration wrinkle is the AI connector: FYERS documents a remote MCP endpoint and examples for Claude/Cursor, while Codex currently documents local STDIO and remote Streamable HTTP MCP connections. FYERS's Cursor example calls its transport `sse`. Therefore this repo targets a **local STDIO, read-only adapter** using the official FYERS Python SDK, instead of assuming FYERS's remote endpoint will connect directly to Codex. The adapter must be validated with the user's FYERS app before it is treated as production-ready.

## Planned Indian-market workflow

1. Resolve NSE/BSE instruments from the latest FYERS Symbol Master; do not guess symbol strings.
2. Fetch quotes in batches and candles with explicit resolution, range, source timestamp, and completeness checks.
3. Scan a user watchlist or a bounded index universe first. Clearly report partial scans and data failures.
4. Use Indian exchange sessions in `Asia/Kolkata`, including exchange holidays and special sessions. Do not assume every session is a normal day.
5. Evaluate only completed candles for opening-range and daily setups.
6. Produce an analysis/plan, with INR sizing inputs and risks. The initial project is read-only: it has no order, GTT, position-exit, or account-write tool.

## Initial scope

The first usable increment should provide only:

- `get_quotes(symbols)` — FYERS quotes for up to 50 symbols per request on Standard.
- `get_history(symbol, resolution, range_from, range_to)` — historical OHLCV candles, with completed-bar semantics.
- Codex skill instructions for India-market analysis, market-session checks, data freshness, partial-result reporting, and safe handoffs.

Scanner, entry timer, exit planner, time-machine, INR budget/risk manager, company filings/news, and Indian exchange calendar should be added after the data connector is verified. Do not claim a whole-market scan from a small watchlist or a Standard-plan batch.

## Data and limits to design around

FYERS documents up to 50 symbols per Standard-plan Quotes request, 5 data requests/second, 50/minute and 5,000/day. Historical requests return at most 100 days for intraday resolutions and 366 days for daily/weekly/monthly resolutions; the accessible lookback also depends on the user's plan. Live streaming is the appropriate approach for continuous updates; do not poll quotes rapidly.

NSE's normal equity session is 09:15–15:30 IST, with pre-open and closing sessions around it. The calendar and special-session schedule must be refreshed from the exchange; a hard-coded annual calendar will go stale.

## Regulatory boundary

The initial version analyzes data and prepares hypothetical plans only. It does not automate orders. SEBI's retail algorithmic-trading framework and subsequent implementation circulars apply to broker/API algo workflows; broker-side registration and operational requirements should be reviewed before anyone adds execution. This repository is not legal advice or a claim that a strategy is compliant.

## Sources

- [FYERS Quotes API](https://fyers.in/api-docs/v3/api/market-data/quotes/)
- [FYERS Historical Data API](https://fyers.in/api-docs/v3/api/market-data/historical-data)
- [FYERS API plans and rate limits](https://support.fyers.in/portal/en/kb/articles/what-are-the-fyers-api-rate-limits-for-standard-and-prime-plans)
- [FYERS MCP installation guide](https://fyers.in/api-docs/ai/mcp/installation/)
- [Codex MCP connection guide](https://learn.chatgpt.com/docs/extend/mcp)
- [NSE market timings and holidays](https://www.nseindia.com/resources/exchange-communication-holidays)
- [SEBI retail algo trading circular](https://www.sebi.gov.in/legal/circulars/feb-2025/safer-participation-of-retail-investors-in-algorithmic-trading_91614.html)
- [SEBI implementation timeline extension, September 2025](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2025/1759232056254.pdf)

## Status

Research-backed project starter, published as a private GitHub repository. It has not yet been connected to a live FYERS account or validated against the user's local SDK/token. No credentials belong in this repository.

