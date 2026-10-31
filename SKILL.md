---
name: india-day-trader
description: >-
  Analyze NSE/BSE equities and index instruments using FYERS market data.
  Use for Indian-market scans, company news and filings, completed-candle entries,
  INR stop/target plans, historical replays, position sizing, risk checks,
  price alerts, and quarterly-result comparisons. Read-only; no live orders.
---

# India Day Trader

Follow the original day-trader workflow in an Indian market context. Prefer the connected local FYERS MCP tools when available. If they are unavailable, say so and offer analysis from data the user supplies; never invent quotes, candles, filings, or scan results.

## Session, instruments and data

- Use `Asia/Kolkata`. NSE regular equity hours are 09:15–15:30 IST. Check exchange, date, holidays and special sessions. The bundled calendar only certifies 2026 and fails closed for later years until refreshed. Do not guess Muhurat or early-close hours.
- Resolve each symbol through the current FYERS Symbol Master and retain the full exchange symbol and series. NSE and BSE listings are distinct.
- Respect account limits: FYERS Standard quotes permit up to 50 symbols per request; the local adapter paces REST calls to about 48/minute. Intraday candles are available in requests of up to 100 days subject to plan lookback.
- Exclude incomplete candles from triggers and state the timestamp, interval, universe size, successes, failures and partial coverage.
- Use bounded watchlists or the official Nifty 50 constituent file. Never imply that Nifty 50 is all of India.

## Full workflow

1. **Scan** — daily candidate rules (20-session closing high, SMA20 reclaim, oversold and bull-flag candidate) or intraday completed-bar opening-range breakout. The rules identify candidates; they do not predict returns.
2. **News and filings** — discover headlines for the watchlist and monitor NSE company announcements. Verify important claims from the actual NSE/BSE notice or issuer investor-relations source. If a public endpoint is unavailable, report it as unavailable rather than inferring events.
3. **Entry** — check a long-only ORB or a user-supplied price level using completed bars. Report waiting/triggered/closed and the observed candle. No order is sent.
4. **Exit plan** — require entry below target and above stop, round prices to the instrument tick, and state the rule, reward:risk and flat-by time. Default stop is the OR midpoint when available.
5. **Replay** — run the plan against available historical intraday candles and a same-time bootstrap. Show historical sample size and model limits; results are not a forecast.
6. **Budget** — calculate whole-share quantity in rupees under max loss, position size, max order and cash buffer. Include the configured cost buffer; don't invent a broker fee.
7. **Risk** — block malformed/unsupported instruments, missing stop, excessive trade/daily loss, low reward:risk, blocked symbol, closed/unverified sessions, and daily order/trade cap breaches. Report the gate and reasons.
8. **Ticket/paper broker workflow** — display a proposal and record an exact `yes` only in the paper journal after the risk gate. Live execution remains disabled because the user's configured FYERS app is read-only.
9. **Alerts** — set one-shot price or time rules and evaluate them when the user asks. They are not background monitoring and never submit orders.
10. **Earnings analyst** — compare consolidated quarter metrics with the same quarter a year earlier and calculate latest/TTM margins from normalized CSV. Keep standalone quarter values separate from cumulative financial statements. Gross margin is optional when the company reports comparable gross profit.
11. **India disclosure replacement** — use NSE corporate filings to replace the source skill's US Congress/Pelosi disclosure tracker. Do not imply that India supplies a consolidated, timely MP stock-trade feed equivalent to House PTRs.

## Technical analysis rules

- Identify exact setup rule and timeframe. Use completed OHLCV candles only; disclose the candle source and sample size.
- Opening range defaults to the first 15 minutes after 09:15, with a 5-minute close above range high as trigger. Only use a verified regular session.
- The daily scanner's bull flag and oversold labels are screening heuristics, not recommendations.
- The historical bootstrap rescales past candles around the plan's entry reference. Same-candle stop/target touches are resolved stop-first. Slippage, taxes, market impact, halts and corporate-action adjustments are not modeled.

## Safety and scope

- Keep prices, capital, costs and risk in INR. No short selling, options or leverage unless a future version implements and explicitly gates them; current risk gate supports cash-equity buys only.
- This repository does not place, modify, cancel, or exit real orders; does not manage positions/GTT; and does not connect to the FYERS order API. The paper broker is a local journal only.
- Do not ask for or print the App Secret, auth code or access token. They belong in Windows Credential Manager.
- Do not claim the strategy is profitable, compliant, or suitable for the user. Describe outputs as observations, plans, proposals, or historical simulations.
