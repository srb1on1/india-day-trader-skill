"""Historical replay and Monte Carlo sanity check over FYERS intraday candles."""

from __future__ import annotations

import argparse
import random
from collections import defaultdict
from datetime import datetime, timedelta

from .calendar import IST
from .fyers_data import FyersData
from .storage import read_json, write_json
from .technical import normalized_candles


def run(replays: int = 10_000, seed: int = 19) -> dict:
    plan = read_json("trader/plan.json", {}) or {}
    if not plan.get("symbol") or not all(k in plan for k in ("entry", "stop", "target")):
        raise ValueError("Create trader/plan.json with trader-exit first.")
    now = datetime.now(IST)
    data = FyersData()
    symbol = plan["symbol"]
    start = (now.date() - timedelta(days=95)).isoformat()
    response = data.history(symbol, "5", start, now.date().isoformat())
    candles = normalized_candles(response.get("candles", []))
    sessions: dict[str, list[dict]] = defaultdict(list)
    for candle in candles:
        day = datetime.fromtimestamp(candle["time"], IST).date().isoformat()
        if day < plan.get("date", now.date().isoformat()):
            sessions[day].append(candle)
    complete = [rows for rows in sessions.values() if len(rows) >= 70]
    if len(complete) < 10:
        raise ValueError(f"Only {len(complete)} usable historical sessions; at least 10 are required for a replay.")
    complete.sort(key=lambda rows: rows[0]["time"])
    entry = float(plan["entry"])
    stop = float(plan["stop"])
    target = float(plan["target"])
    risk = entry - stop
    if risk <= 0 or target <= entry:
        raise ValueError("Plan must have stop < entry < target.")
    # Entry candle index is approximated from the plan's IST clock. Plans store
    # the trigger close time, so replay starts on the following bar.
    hhmm = str(plan.get("entry_observation", "09:30"))
    try:
        t = datetime.fromisoformat(hhmm)
        start_minute = t.hour * 60 + t.minute
    except ValueError:
        start_minute = 9 * 60 + 30
    entry_index = max(3, (start_minute - (9 * 60 + 15)) // 5)
    historical = {"target_first": 0, "stop_first": 0, "neither": 0}
    historical_r = []
    for rows in complete:
        outcome = "neither"
        final_price = rows[-1]["close"]
        for candle in rows[entry_index:]:
            if candle["low"] <= stop:
                outcome = "stop_first"
                historical_r.append(-1.0)
                break
            if candle["high"] >= target:
                outcome = "target_first"
                historical_r.append((target - entry) / risk)
                break
        else:
            historical_r.append((final_price - entry) / risk)
        historical[outcome] += 1
    pool_by_index: dict[int, list[dict]] = defaultdict(list)
    for rows in complete:
        for index, candle in enumerate(rows):
            if index >= entry_index:
                pool_by_index[index].append(candle)
    rng = random.Random(seed)
    counts = {"target_first": 0, "stop_first": 0, "neither": 0}
    r_values = []
    for _ in range(replays):
        price = entry
        outcome = "neither"
        for index in sorted(pool_by_index):
            sampled = rng.choice(pool_by_index[index])
            # Preserve the past bar's range and close return relative to its open.
            anchor = sampled["open"] or sampled["close"]
            scale = price / anchor if anchor else 1.0
            high = sampled["high"] * scale
            low = sampled["low"] * scale
            close = sampled["close"] * scale
            if low <= stop:
                outcome = "stop_first"  # conservative if a single candle touches both levels
                r_values.append(-1.0)
                break
            if high >= target:
                outcome = "target_first"
                r_values.append((target - entry) / risk)
                break
            price = close
        else:
            r_values.append((price - entry) / risk)
        counts[outcome] += 1
    total = max(1, replays)
    result = {"symbol": symbol, "plan": plan, "model": "same-time-of-day historical candle bootstrap",
              "historical_sessions": len(complete), "bars_from_entry": sum(len(x) for x in pool_by_index.values()) // len(complete),
              "historical_fixed_level_outcomes": historical,
              "historical_fixed_level_average_r": round(sum(historical_r) / len(historical_r), 3),
              "replays": replays, "seed": seed, "odds_pct": {k: round(v / total * 100, 2) for k, v in counts.items()},
              "average_r": round(sum(r_values) / len(r_values), 3),
              "caveats": ["not a forecast", "standard-plan lookback limits apply", "slippage, gaps, halts and costs are not modeled", "same-candle stop/target ties count as stop"]}
    write_json("trader/timemachine.json", result)
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--replays", type=int, default=10_000)
    p.add_argument("--seed", type=int, default=19)
    a = p.parse_args(argv)
    try:
        if not 100 <= a.replays <= 100_000:
            raise ValueError("--replays must be between 100 and 100000.")
        result = run(a.replays, a.seed)
        print(result)
        return 0
    except Exception as exc:
        print(f"TIME MACHINE FAILED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
