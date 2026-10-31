"""Local Codex MCP server for the read-only India-market research workflow."""

from __future__ import annotations

import json
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from . import analyst, alerts, budget, broker, calendar, entry, exit as exit_planner, filings, news, risk, scanner, timemachine, universe
from .fyers_data import FyersData

mcp = FastMCP("FYERS India Market Data (read-only)")


@mcp.tool()
def get_quotes(symbols: list[str]) -> str:
    """Get current FYERS quotes for up to 50 exact NSE/BSE symbols."""
    return json.dumps(FyersData().quotes(symbols), ensure_ascii=False)


@mcp.tool()
def get_history(
    symbol: str,
    resolution: str,
    range_from: str,
    range_to: str,
) -> str:
    """Get FYERS OHLCV candles. Intraday request ranges are limited to 100 days."""
    return json.dumps(
        FyersData().history(symbol, resolution, range_from, range_to),
        ensure_ascii=False,
    )


@mcp.tool()
def get_market_status(exchange: str = "NSE") -> str:
    """Get the India-local exchange session state; calendar coverage must be current."""
    return json.dumps(calendar.session_status(exchange=exchange), ensure_ascii=False)


@mcp.tool()
def scan_watchlist(mode: str, symbols: list[str], exchange: str = "NSE") -> str:
    """Scan a bounded symbol list for daily candidates or completed 15-minute opening-range breaks."""
    if mode not in {"daily", "orb"}:
        raise ValueError("mode must be daily or orb")
    return json.dumps(scanner.run_scan(mode, symbols, exchange), ensure_ascii=False)


@mcp.tool()
def refresh_index_universe(index: str = "nifty50") -> str:
    """Download official Nifty 50 constituents and map them to current FYERS symbols."""
    return json.dumps(universe.constituents(index), ensure_ascii=False)


@mcp.tool()
def check_entry(symbol: str, setup: str = "orb", level: float | None = None, exchange: str = "NSE") -> str:
    """Check a long-only setup against completed FYERS candles. Does not place orders."""
    return json.dumps(entry.check(symbol, setup, level, exchange), ensure_ascii=False)


@mcp.tool()
def plan_exit(symbol: str | None = None, entry_price: float | None = None, stop: float | None = None,
              target_r: float = 2.0, exchange: str = "NSE") -> str:
    """Write a hypothetical stop/target plan from an entry observation or supplied prices."""
    return json.dumps(exit_planner.plan(entry_price, stop, target_r, "or_mid", symbol, exchange), ensure_ascii=False)


@mcp.tool()
def replay_plan(replays: int = 10000, seed: int = 19) -> str:
    """Run a historical candle bootstrap for trader/plan.json; results are not forecasts."""
    return json.dumps(timemachine.run(replays, seed), ensure_ascii=False)


@mcp.tool()
def size_plan(cash_inr: float | None = None) -> str:
    """Calculate a whole-share INR proposal from configured max-loss and cash rules."""
    return json.dumps(budget.size_trade(cash_inr=cash_inr), ensure_ascii=False)


@mcp.tool()
def check_order_risk() -> str:
    """Apply configured hard risk rules to the current proposed order; never sends it."""
    return json.dumps(risk.check(), ensure_ascii=False)


@mcp.tool()
def monitor_company_news(symbols: list[str], hours: int = 24) -> str:
    """Find new India-market headlines. Verify important items against exchange filings."""
    return json.dumps(news.monitor(symbols, hours), ensure_ascii=False)


@mcp.tool()
def monitor_nse_filings(symbols: list[str], since_days: int = 7) -> str:
    """Read new NSE corporate announcements. If NSE blocks access, returns its official filing page."""
    return json.dumps(filings.new_filings(symbols, since_days), ensure_ascii=False)


@mcp.tool()
def add_price_alert(symbol: str, above: float | None = None, below: float | None = None) -> str:
    """Add a local one-shot alert rule; this does not submit a broker order."""
    return json.dumps(alerts.add(symbol=symbol, above=above, below=below), ensure_ascii=False)


@mcp.tool()
def check_price_alerts() -> str:
    """Evaluate local alerts against FYERS quotes; reports hits but does not trade."""
    return json.dumps(alerts.check(), ensure_ascii=False)


@mcp.tool()
def show_order_tickets() -> str:
    """Show paper/order tickets and whether their exact risk check passed today."""
    return json.dumps(broker.show(), ensure_ascii=False)


@mcp.tool()
def analyze_results_csv(path: str, symbol: str | None = None) -> str:
    """Compare normalized consolidated quarterly results YoY and calculate TTM margins."""
    return json.dumps(analyst.analyze_csv(path, symbol), ensure_ascii=False, default=str)


if __name__ == "__main__":
    mcp.run(transport="stdio")
