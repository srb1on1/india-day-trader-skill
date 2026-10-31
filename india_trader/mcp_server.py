"""Local Codex MCP server exposing only FYERS quotes and candle history."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

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


if __name__ == "__main__":
    mcp.run(transport="stdio")

