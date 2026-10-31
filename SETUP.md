# Local FYERS and Codex setup (prototype)

This project uses a local MCP server because the FYERS remote MCP example uses SSE, while Codex documents STDIO and Streamable HTTP. The server in this repo uses STDIO and exposes only quote and candle-history tools. It does not include FYERS order APIs.

## One-time setup

1. Install Python 3.10 or newer on the same Windows account that runs Codex.
2. Open this repository in Codex and install the project dependencies in a virtual environment using the project interpreter. The dependencies are listed in `pyproject.toml` (`fyers-apiv3`, `mcp`, and `keyring`).
3. Run the local auth setup once. It asks for your FYERS App ID, App Secret, and the exact redirect URL configured in your FYERS app. It stores those values in the operating system credential store, not in the repo.
4. Run local login. FYERS requires you to sign in in a browser. Copy only the `auth_code` value from the redirect URL into the hidden prompt. The script exchanges it for an access token and stores that token in the operating system credential store.
5. Add a local STDIO MCP server in Codex settings, using the project interpreter to run `-m india_trader.mcp_server` with this project as its working directory. Restart Codex and confirm that only `get_quotes` and `get_history` are listed.
6. Ask for one quote on a known symbol (for example `NSE:INFY-EQ`) and compare the timestamp and value with FYERS Web. Then try one completed historical candle request.

The FYERS access token expires daily at 06:30 IST. After it expires, run local login again before requesting data. This daily browser login is a FYERS authentication requirement, not a Codex setting. Never paste the App Secret or access token into this chat, a repository, a screenshot, or a Codex configuration file.

## Data limits

On FYERS Standard, quotes accept at most 50 symbols per request and Data APIs allow 5 requests/second, 50/minute and 5,000/day. Intraday history is limited to 100 days per request; daily, weekly and monthly history to 366 days per request. The plan determines total available lookback. See the linked official FYERS docs in `README.md` for current limits.

## Current prototype gaps

- No live account verification has been done from this Codex environment.
- This prototype does not include a scanner, exchange-calendar loader, news/filing monitor, backtester, option analytics, or order execution.
- Authentication and keyring behavior must be verified on the user's Windows account before relying on it. If Codex starts the server under a different account or Python installation, it will not see the same credential store.
- FYERS symbols must be validated against the latest Symbol Master. This prototype deliberately does not guess symbol mappings.

