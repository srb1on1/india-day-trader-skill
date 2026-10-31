# Install and run on Windows

These steps install the full local India workflow. You can use its command-line tools in PowerShell, or connect the same tools to Codex over local MCP. PowerShell is just the setup/launch surface; analysis is provided by this repository.

## 1. Open the repository folder

In Codex, open the `india-day-trader-skill` folder you cloned from GitHub. In the file list you should see `pyproject.toml`, `india_trader`, and this guide.

## 2. Install the project

Open the Codex terminal for that folder (or PowerShell in that exact folder), then enter each command separately:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
```

If Windows says `py` is not recognized, install Python 3.11 from python.org, check “Add Python to PATH”, reopen the terminal, and retry. FYERS SDK and Codex MCP dependencies install from `pyproject.toml`.

## 3. Create your local settings

Create a folder named `trader` inside the repository. Copy `config.example.json` into it and rename the copy to `config.json`. You can do this in File Explorer. Edit `trader/config.json` in a text editor and set your own cash budget and risk limits. Do not change values unless they represent your own rules. The example values are illustrative only.

The program writes watchlists, plans, alerts and journals into the same `trader` folder. It is excluded from Git by `.gitignore`.

## 4. Save FYERS credentials safely

The repository reads credentials from Windows Credential Manager via Python `keyring`. Set up your FYERS App ID, App Secret and configured redirect URL without putting them into a source file. Use:

```powershell
.\.venv\Scripts\india-trader.exe auth setup
.\.venv\Scripts\india-trader.exe auth login
```

Sign in to FYERS in the browser opened by the script. Copy only the `auth_code` value from the redirect URL into its hidden prompt. Never share App Secret, auth code, or access token in chat, screenshots, GitHub, or an MCP configuration. FYERS access tokens expire daily at 06:30 IST, so repeat `auth login` after expiry.

## 5. Confirm one live quote

```powershell
.\.venv\Scripts\india-trader.exe market
.\.venv\Scripts\india-trader.exe quote NSE:INFY-EQ
```

Compare the quote with FYERS Web and check its exchange/source details. If it fails, stop and resolve the auth/API error before running scans. You already verified a live INFY quote in the earlier setup; re-auth if its token expired.

## 6. Try the main features

```powershell
# Refresh official Nifty 50 membership and FYERS symbol mapping
.\.venv\Scripts\india-trader.exe universe nifty50

# Daily candidates; a 50-stock scan is paced to FYERS limits
.\.venv\Scripts\india-trader.exe scan daily --index nifty50

# 15-minute opening-range scan during a regular market session
.\.venv\Scripts\india-trader.exe scan orb --index nifty50

# Check a single stock's completed-candle opening range
.\.venv\Scripts\india-trader.exe entry NSE:INFY-EQ

# From a triggered entry, create stop/target plan; size; apply risk gate
.\.venv\Scripts\india-trader.exe exit
.\.venv\Scripts\india-trader.exe budget
.\.venv\Scripts\india-trader.exe risk

# Run candle replay from the current plan
.\.venv\Scripts\india-trader.exe replay

# Discover headlines and official exchange announcements
.\.venv\Scripts\india-trader.exe news --symbols INFY,RELIANCE
.\.venv\Scripts\india-trader.exe filings --symbols INFY,RELIANCE

# Add a one-shot price alert and check it when desired
.\.venv\Scripts\india-trader.exe alerts add --symbol NSE:INFY-EQ --above 1600
.\.venv\Scripts\india-trader.exe alerts check

# Analyze the included DEMO CSV format (example values are not real company results)
.\.venv\Scripts\india-trader.exe analyst results.example.csv --symbol DEMO
```

## 7. Optional: connect it to Codex as MCP

In Codex settings, add a local STDIO MCP server with:

- **Command:** absolute path to this project's `.venv\Scripts\python.exe`
- **Arguments:** `-m`, `india_trader.mcp_server`
- **Working directory:** absolute path to this repository folder

Restart the MCP connection and look for `get_quotes`, `get_history`, `get_market_status`, `scan_watchlist`, `refresh_index_universe`, `check_entry`, `plan_exit`, `replay_plan`, `size_plan`, `check_order_risk`, `monitor_company_news`, `monitor_nse_filings`, `add_price_alert`, `check_price_alerts`, `show_order_tickets`, and `analyze_results_csv`.

The MCP process uses the same `trader/config.json`, Windows keyring and local journals. If Codex reports that the server exited, check the configured executable and working directory first.

## Important limits

- Your current FYERS app is market-data-only. This skill cannot submit orders. `india-trader broker approve --index 1 --reply yes` only records a paper approval after risk checks; it does not connect to the broker.
- Calendar coverage is pinned to NSE's 2026 holiday schedule; future dates fail closed until refreshed. Special-session hours are not guessed.
- The public NSE filing endpoint can block automated requests. On failure, use its official filings page and provide the downloaded data for analysis.
- Result analysis expects a CSV based on `results.example.csv`: one row per reported quarter, standalone quarter amounts, same consolidated scope, values in INR crore except EPS in rupees, plus source URL. Do not use cumulative 9M figures as quarter figures.
- Backtest/replay approximates outcome distributions from available FYERS candles and does not model actual fill quality, taxes or slippage.
