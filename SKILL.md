---
name: india-day-trader
description: >-
  Analyze Indian equities and index instruments using FYERS market data.
  Use for Indian-market watchlist scans, completed-candle setup checks,
  Indian-market trading-session questions, or INR-denominated trade planning.
  Requires a connected read-only FYERS data source; do not silently substitute
  US-market assumptions or claim live data without a live tool result.
---

# India Day Trader

Use this skill for Indian-market data and analysis. Prefer the connected FYERS data tools when available. If they are unavailable, say so and offer analysis from user-provided data; never invent a quote, candle, or scan result.

## Market and instrument conventions

- Work in `Asia/Kolkata` and use the relevant exchange's current session and holiday calendar. NSE's normal equity session is 09:15–15:30 IST; check for pre-open, special/Muhurat sessions, holidays, and early closes before describing a market as open or closed.
- Resolve symbols through FYERS Symbol Master or an authoritative exchange instrument list. Preserve the exact FYERS exchange/symbol/series identifier in outputs (for example `NSE:INFY-EQ`); don't assume a company ticker maps to one tradeable instrument.
- Keep NSE and BSE listings distinct. State the exchange, series/contract and timestamp in results.
- Keep all prices, risk, capital and size calculations in INR. Account for slippage and applicable costs when the user supplies or requests them; don't fabricate a brokerage tariff.

## Data handling

- Use quotes for current snapshots and historical OHLCV for chart calculations. Report the provider timestamp and resolution.
- Only use completed candles for signals. Exclude the currently forming candle; if the provider's range includes it, trim it using the exchange-local close time.
- Respect the user's FYERS plan limits. Standard quotes support at most 50 symbols per request; chunk requests and state the universe size, successful count, and failures. Avoid rapid REST polling; use a supported data socket for continuous updates.
- Treat missing bars, stale quotes, holidays, halts and rejected symbols as unavailable evidence, not as neutral price action. Label any scan partial and list the omissions.
- Never mix adjusted daily series and intraday OHLCV without documenting the adjustment basis.

## Analysis workflow

1. Establish the request: exchange, symbols/universe, timeframe, session date, and whether the user wants a snapshot, historical comparison, or setup scan.
2. Check that the exchange is open for the requested session and that the data source is connected and fresh.
3. Fetch only the needed data. Prefer a watchlist or a bounded index constituent list over an unsupported claim to scan every Indian listing.
4. Apply the requested, explicit rule to completed candles. Explain the rule and show the observed values that triggered or failed it.
5. If planning a hypothetical trade, show entry assumption, invalidation/stop, target, INR risk per share and share count only from user-provided risk/capital limits. A setup is not an instruction to trade.
6. End with data timestamp, coverage/limitations, and whether the output is a quote, observation, hypothetical plan, or backtest.

## Scope boundary

This skill is read-only. It must not place, modify, cancel, or simulate a live order; create/modify GTTs; exit/convert positions; or mutate account watchlists/alerts. If a connected server exposes such tools, do not call them. Do not describe an alert as active unless it was actually created by a permitted tool.

Do not reuse US market hours, New York time, Nasdaq Trader universe assumptions, SEC EDGAR as the Indian company filing source, or Alpaca order assumptions. For Indian company disclosures, use NSE/BSE filings and company investor-relations material; identify the source and filing date.

