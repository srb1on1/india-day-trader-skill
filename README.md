# India Day Trader Skill

An India-market adaptation of the original Day Trader workflow. It uses FYERS V3 for NSE/BSE quotes and OHLCV, Indian session rules and INR risk controls. The project is designed for Codex as a local read-only MCP server plus a beginner-friendly command-line interface.

## Implemented workflow

| Original workflow | India adaptation | Current scope |
|---|---|---|
| Scanner | Daily technical candidates and 15-minute opening-range breakout scan | User watchlist, symbols, or official Nifty 50 universe; reports partial failures |
| News monitor | Indian ticker headline search | Google News RSS discovery; verify against exchange/company filings |
| Entry timer | Completed-candle entry check | Long-only ORB or user-supplied price level |
| Exit planner | INR stop, target and R plan | Tick-rounded hypothetical plan; default stop is opening-range midpoint |
| Time machine | Historical candle bootstrap and replay | FYERS intraday history, stop-first tie rule, simulation caveats |
| Budget manager | Whole-share position sizing | INR cash, max loss, position cap, order cap, buffer and optional costs |
| Risk manager | Hard proposal gate | Stop/RR, per-trade and daily risk, order/trade limits, session, blocked symbols |
| Broker workflow | Ticket and paper approval journal | Does not send an order; live API execution is disabled |
| Price alerts | Local one-shot price and time rules | Evaluated when checked; no background service or broker order |
| Earnings analyst | YoY and TTM quarterly comparison | User-provided normalized CSV; consolidated figures; gross margin optional |
| Pelosi tracker | NSE corporate filings monitor | Exchange disclosure watcher; India has no equivalent consolidated MP trade feed |

## Setup

Follow [SETUP.md](SETUP.md). The app the user created on FYERS is a non-trading/market-data app. It can support quotes and history after local authentication, but cannot place orders. The full Codex skill is in [SKILL.md](SKILL.md).

After installation, copy `config.example.json` to `trader/config.json`, edit the limits to match your own rules, then start with `india-trader market`, `india-trader quote NSE:INFY-EQ`, and `india-trader scan daily --index nifty50`. Commands and examples are in SETUP.md.

## Data and operating limits

- FYERS Standard quotes support up to 50 symbols per request. The adapter spaces data calls conservatively (about one call every 1.25 seconds) against the published 50/minute limit. A 50-stock historical scan can therefore take about a minute.
- FYERS history supports up to 100 days per intraday request and 366 days for daily/weekly/monthly requests; the account plan can impose a shorter accessible lookback.
- Scanner and replay use bounded universes. A Nifty 50 scan does not mean every NSE/BSE listing.
- NSE regular equity hours are 09:15–15:30 IST. The bundled holiday calendar is only pinned to the official 2026 schedule. It fails closed on unknown future years and the 2026 Muhurat hours are deliberately treated as unverified. Refresh the calendar before using this beyond its documented coverage.
- News results are discovery leads, not verified facts. NSE announcements may block automated access or change their public endpoint; the tool points to the official page and reports failure without inventing filings.
- Earnings analysis is not an automatic result scraper: reporting formats vary. Use the example CSV structure, extract standalone quarter figures in one consistent consolidated scope, record the official source URL, and do not mix cumulative 9M/FY values with quarterly values.
- Backtest output is a historical bootstrap, not a validated strategy or forecast. It uses available intraday bars, approximate same-time sampling, and does not model slippage, taxes, impact, halts, survivorship, or corporate actions.
- Alerts are only checked when the command/tool runs. They do not continuously monitor in the background.

## Trading and compliance boundary

No live order, cancel, modification, GTT or account-write API is implemented. The `broker approve` command records a paper approval only. Connecting a trading-enabled app is a separate project and would require reviewing FYERS permissions, current SEBI/broker requirements, static IP and the broker's order workflow. This repository is not financial advice or a claim that a strategy is compliant or profitable.

## Official references

- [FYERS Quotes API](https://fyers.in/api-docs/v3/api/market-data/quotes/)
- [FYERS Historical Data API](https://fyers.in/api-docs/v3/api/market-data/historical-data)
- [FYERS API plans and rate limits](https://support.fyers.in/portal/en/kb/articles/what-are-the-fyers-api-rate-limits-for-standard-and-prime-plans)
- [FYERS Symbol Master](https://fyers.in/api-docs/v3/api/market-information/symbol-master/symbol-master-json/)
- [Nifty 50 constituents](https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv)
- [NSE exchange calendar](https://www.nseindia.com/resources/exchange-communication-holidays)
- [NSE corporate announcements](https://www.nseindia.com/companies-listing/corporate-filings-announcements)
- [NSE financial results](https://www.nseindia.com/companies-listing/corporate-filings-financial-results)
- [SEBI retail algo trading circular](https://www.sebi.gov.in/legal/circulars/feb-2025/safer-participation-of-retail-investors-in-algorithmic-trading_91614.html)

## Project status

Feature-complete local implementation for the read-only and paper workflow above. It still needs to be installed and connected on the user's Windows machine, then each live data route should be verified against FYERS. Third-party/public web endpoints (news and NSE filings) can change. No credentials or access tokens belong in GitHub.
