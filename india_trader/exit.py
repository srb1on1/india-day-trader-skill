"""Create a hypothetical INR trade plan from an entry observation."""

from __future__ import annotations

import argparse
import math
from datetime import datetime

from .calendar import IST
from .fyers_data import FyersData
from .storage import read_json, write_json


def floor_to_tick(price: float, tick: float) -> float:
    return round(math.floor(price / tick + 1e-10) * tick, 4)


def plan(entry: float | None = None, stop: float | None = None, target_r: float = 2.0,
         stop_rule: str = "or_mid", symbol: str | None = None, exchange: str = "NSE") -> dict:
    setup = read_json("trader/entry.json", {}) or {}
    entry = float(entry if entry is not None else setup.get("entry_reference", 0))
    symbol = symbol or setup.get("symbol")
    if not symbol or entry <= 0:
        raise ValueError("Need a triggered trader/entry.json or explicit --symbol and --entry.")
    record = FyersData.resolve_symbol(symbol, exchange)
    tick = float(record.get("tickSize", 0.05) or 0.05)
    if stop is None:
        if stop_rule == "or_mid":
            high, low = setup.get("range_high"), setup.get("range_low")
            if high is None or low is None:
                raise ValueError("Opening-range stop needs range_high and range_low from an ORB entry.")
            stop = (float(high) + float(low)) / 2
        else:
            raise ValueError("Provide --stop or use --stop-rule or_mid with an ORB entry.")
    stop = floor_to_tick(float(stop), tick)
    entry = round(round(entry / tick) * tick, 4)
    if stop >= entry:
        raise ValueError("Stop must be below entry for a long-only plan.")
    risk = entry - stop
    target = round(round((entry + risk * target_r) / tick) * tick, 4)
    if target <= entry:
        raise ValueError("Target must be above entry.")
    result = {"symbol": symbol, "exchange": exchange, "currency": "INR", "date": datetime.now(IST).date().isoformat(),
              "entry": entry, "stop": stop, "target": target, "risk_per_share": round(risk, 4),
              "target_r": target_r, "reward_risk": round((target-entry)/risk, 3), "stop_rule": stop_rule,
              "tick_size": tick, "flat_by_ist": "15:20", "analysis_only": True,
              "entry_observation": setup.get("time_ist")}
    write_json("trader/plan.json", result)
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbol")
    p.add_argument("--entry", type=float)
    p.add_argument("--stop", type=float)
    p.add_argument("--stop-rule", choices=("or_mid",), default="or_mid")
    p.add_argument("--target-r", type=float, default=2)
    p.add_argument("--exchange", choices=("NSE", "BSE"), default="NSE")
    a = p.parse_args(argv)
    try:
        print(plan(a.entry, a.stop, a.target_r, a.stop_rule, a.symbol, a.exchange))
        return 0
    except Exception as exc:
        print(f"PLAN FAILED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
