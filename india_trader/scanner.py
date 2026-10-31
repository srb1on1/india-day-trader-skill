"""FYERS-backed daily and opening-range scans for a bounded Indian watchlist."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta

from .calendar import IST, NSE_OPEN, session_status
from .fyers_data import FyersData
from .storage import read_json, write_json
from .technical import daily_setups, normalized_candles, orb_trigger


def _symbols(args) -> list[str]:
    values = []
    if args.symbols:
        values.extend(x.strip() for x in args.symbols.split(",") if x.strip())
    if args.watchlist:
        watch = read_json(args.watchlist, {}) or {}
        values.extend(x if isinstance(x, str) else x.get("symbol", "") for x in watch.get("symbols", []))
    if args.index:
        from .universe import constituents
        values.extend(constituents(args.index)["symbols"])
    if not values:
        config = read_json("trader/config.json", {}) or {}
        values.extend(config.get("watchlist", []))
    return list(dict.fromkeys(values))


def run_scan(mode: str, symbols: list[str], exchange: str = "NSE", minutes: int = 15, now: datetime | None = None) -> dict:
    if not symbols:
        raise ValueError("Provide --symbols, --watchlist, or trader/config.json watchlist.")
    if len(symbols) > 100:
        raise ValueError("This implementation caps one scan at 100 symbols. Split larger scans and label each batch.")
    now = (now or datetime.now(IST)).astimezone(IST)
    market = session_status(now, exchange)
    if market["status"] == "calendar_refresh_required":
        raise RuntimeError("Refresh the official exchange holiday calendar before scanning this year.")
    if market["status"] == "special_session_hours_unverified":
        raise RuntimeError(market["note"])
    client = FyersData()
    hits, failures = [], []
    for query in symbols:
        try:
            record = client.resolve_symbol(query, exchange)
            symbol = record.get("symbol", query)
            if mode == "daily":
                response = client.history(symbol, "1D", (now.date() - timedelta(days=60)).isoformat(), now.date().isoformat())
                candles = normalized_candles(response.get("candles", []))
                # Do not include today's unfinished daily bar.
                candles = [x for x in candles if datetime.fromtimestamp(x["time"], IST).date() < now.date()]
                setups = daily_setups(candles)
                if setups:
                    hits.append({"symbol": symbol, "name": record.get("symDetails", record.get("symbolDesc", "")), "setups": setups,
                                 "last_close": candles[-1]["close"] if candles else None})
            elif mode == "orb":
                response = client.history(symbol, "5", now.date().isoformat(), now.date().isoformat())
                candles = normalized_candles(response.get("candles", []))
                opening = datetime.combine(now.date(), NSE_OPEN, IST)
                opening_epoch = int(opening.timestamp())
                # FYERS returns candle start times; discard any bar not yet complete.
                candles = [x for x in candles if x["time"] + 300 <= int(now.timestamp())]
                result = orb_trigger(candles, opening_epoch, minutes=minutes)
                if result:
                    candle = result["trigger"]
                    hits.append({"symbol": symbol, "name": record.get("symDetails", ""), "setup": "opening_range_breakout",
                                 "time_ist": datetime.fromtimestamp(candle["time"] + 300, IST).isoformat(),
                                 "close": candle["close"], "volume": candle["volume"],
                                 "range_high": result["range_high"], "range_low": result["range_low"]})
            else:
                raise ValueError(f"Unknown scan mode: {mode}")
        except Exception as exc:
            failures.append({"query": query, "error": str(exc)})
    result = {"mode": mode, "exchange": exchange, "as_of_ist": now.isoformat(), "market": market,
              "universe": len(symbols), "scanned": len(symbols) - len(failures), "failed": failures,
              "partial": bool(failures), "hits": hits}
    write_json("trader/watchlist.json", result)
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("daily", "orb"))
    p.add_argument("--symbols", help="comma-separated FYERS symbols or share codes")
    p.add_argument("--watchlist", help="JSON watchlist file with a symbols array")
    p.add_argument("--index", choices=("nifty50",), help="refresh an official index constituent list")
    p.add_argument("--exchange", choices=("NSE", "BSE"), default="NSE")
    p.add_argument("--or-minutes", type=int, default=15)
    a = p.parse_args(argv)
    try:
        result = run_scan(a.mode, _symbols(a), a.exchange, a.or_minutes)
    except Exception as exc:
        print(f"SCAN FAILED: {exc}")
        return 2
    print(f"{result['mode'].upper()} {result['exchange']} {result['as_of_ist']} — {result['scanned']}/{result['universe']} scanned; {len(result['hits'])} hits; {len(result['failed'])} failed")
    for hit in result["hits"]:
        print(hit)
    if result["partial"]:
        print("PARTIAL SCAN — inspect trader/watchlist.json for omissions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
