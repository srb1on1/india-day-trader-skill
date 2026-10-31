"""Completed-candle entry checks; long-only and analysis-only."""

from __future__ import annotations

import argparse
from datetime import datetime, time

from .calendar import IST, NSE_OPEN, session_status
from .fyers_data import FyersData
from .storage import write_json
from .technical import normalized_candles, orb_trigger


def check(symbol: str, setup: str = "orb", level: float | None = None, exchange: str = "NSE", now: datetime | None = None) -> dict:
    now = (now or datetime.now(IST)).astimezone(IST)
    status = session_status(now, exchange)
    if status["status"] == "calendar_refresh_required" or status["status"] == "special_session_hours_unverified":
        return {"status": "unverified_session", "market": status}
    if status["status"] in {"closed", "pre_open"}:
        return {"status": "not_open" if status["status"] == "pre_open" else "expired_or_closed", "market": status}
    data = FyersData()
    resolved = data.resolve_symbol(symbol, exchange)
    fy_symbol = resolved.get("symbol", symbol)
    response = data.history(fy_symbol, "5", now.date().isoformat(), now.date().isoformat())
    candles = normalized_candles(response.get("candles", []))
    candles = [c for c in candles if c["time"] + 300 <= int(now.timestamp())]
    open_epoch = int(datetime.combine(now.date(), NSE_OPEN, IST).timestamp())
    if setup == "orb":
        result = orb_trigger(candles, open_epoch, 15, 5)
        if result:
            bar = result["trigger"]
            outcome = {"status": "triggered", "symbol": fy_symbol, "time_ist": datetime.fromtimestamp(bar["time"] + 300, IST).isoformat(),
                       "entry_reference": bar["close"], "range_high": result["range_high"], "range_low": result["range_low"], "volume": bar["volume"]}
        else:
            opening_bars = [c for c in candles if open_epoch <= c["time"] < open_epoch + 900]
            if len(opening_bars) < 3:
                outcome = {"status": "forming_opening_range", "symbol": fy_symbol, "completed_opening_bars": len(opening_bars), "required": 3}
            else:
                high = max(c["high"] for c in opening_bars)
                last = candles[-1] if candles else None
                outcome = {"status": "waiting", "symbol": fy_symbol, "range_high": high,
                           "last_completed_close": last["close"] if last else None,
                           "distance_to_trigger": round(high - last["close"], 2) if last else None}
    elif setup == "level" and level is not None:
        after = [c for c in candles if c["close"] > level]
        outcome = ({"status": "triggered", "symbol": fy_symbol, "time_ist": datetime.fromtimestamp(after[0]["time"] + 300, IST).isoformat(),
                    "entry_reference": after[0]["close"], "level": level} if after else
                   {"status": "waiting", "symbol": fy_symbol, "level": level, "last_completed_close": candles[-1]["close"] if candles else None})
    else:
        raise ValueError("Use --setup orb or --setup level with --level PRICE.")
    outcome["exchange"] = exchange
    outcome["as_of_ist"] = now.isoformat()
    write_json("trader/entry.json", outcome)
    return outcome


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("symbol")
    p.add_argument("--setup", choices=("orb", "level"), default="orb")
    p.add_argument("--level", type=float)
    p.add_argument("--exchange", choices=("NSE", "BSE"), default="NSE")
    a = p.parse_args(argv)
    try:
        print(check(a.symbol, a.setup, a.level, a.exchange))
        return 0
    except Exception as exc:
        print(f"ENTRY CHECK FAILED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
