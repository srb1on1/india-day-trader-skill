"""Pure indicator and setup calculations over FYERS candle arrays."""

from __future__ import annotations

from math import isfinite
from typing import Iterable


def normalized_candles(raw: Iterable) -> list[dict]:
    rows = []
    for item in raw or []:
        if isinstance(item, dict):
            ts = item.get("time", item.get("timestamp"))
            o, h, l, c, v = (item.get(k) for k in ("open", "high", "low", "close", "volume"))
        elif isinstance(item, (list, tuple)) and len(item) >= 6:
            ts, o, h, l, c, v = item[:6]
        else:
            continue
        try:
            vals = [float(o), float(h), float(l), float(c), float(v or 0)]
            if not all(isfinite(x) for x in vals) or vals[1] < vals[2]:
                continue
            rows.append({"time": int(ts), "open": vals[0], "high": vals[1], "low": vals[2], "close": vals[3], "volume": vals[4]})
        except (TypeError, ValueError, OverflowError):
            continue
    return sorted(rows, key=lambda x: x["time"])


def sma(values: list[float], period: int) -> float | None:
    if period <= 0 or len(values) < period:
        return None
    return sum(values[-period:]) / period


def rsi(values: list[float], period: int = 14) -> float | None:
    if len(values) <= period:
        return None
    changes = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(0.0, x) for x in changes]
    losses = [max(0.0, -x) for x in changes]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(changes)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0 if avg_gain else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def atr(candles: list[dict], period: int = 14) -> float | None:
    if len(candles) <= period:
        return None
    tr = []
    for i in range(1, len(candles)):
        prev = candles[i - 1]["close"]
        row = candles[i]
        tr.append(max(row["high"] - row["low"], abs(row["high"] - prev), abs(row["low"] - prev)))
    value = sum(tr[:period]) / period
    for current in tr[period:]:
        value = ((period - 1) * value + current) / period
    return value


def daily_setups(candles: list[dict]) -> list[dict]:
    hits = []
    closes = [c["close"] for c in candles]
    if len(candles) < 21:
        return hits
    last = candles[-1]
    prior20 = candles[-21:-1]
    if last["close"] > max(c["close"] for c in prior20):
        hits.append({"setup": "20d_close_breakout", "close": last["close"]})
    ma20_prev = sma(closes[:-1], 20)
    ma20_now = sma(closes, 20)
    if ma20_prev is not None and ma20_now is not None and closes[-2] < ma20_prev <= closes[-1]:
        hits.append({"setup": "reclaim_sma20", "close": last["close"], "sma20": ma20_now})
    value = rsi(closes, 14)
    if value is not None and value < 30:
        hits.append({"setup": "oversold_rsi14", "rsi14": round(value, 2)})
    if len(candles) >= 25:
        base = closes[-15:-5]
        recent = closes[-5:]
        if base[0] and (max(base) / min(base) - 1) > 0.10 and (max(recent) / min(recent) - 1) < 0.05:
            hits.append({"setup": "bull_flag_candidate", "prior_impulse_pct": round((max(base) / min(base) - 1) * 100, 2)})
    return hits


def opening_range(candles: list[dict], session_open_epoch: int, minutes: int = 15, bar_minutes: int = 5) -> dict | None:
    end = session_open_epoch + minutes * 60
    bars = [c for c in candles if session_open_epoch <= c["time"] < end]
    expected = minutes // bar_minutes
    if len(bars) != expected:
        return None
    return {"high": max(x["high"] for x in bars), "low": min(x["low"] for x in bars), "bars": bars,
            "end_epoch": end, "minutes": minutes}


def orb_trigger(candles: list[dict], session_open_epoch: int, minutes: int = 15, bar_minutes: int = 5) -> dict | None:
    rng = opening_range(candles, session_open_epoch, minutes, bar_minutes)
    if not rng:
        return None
    after = [c for c in candles if c["time"] >= rng["end_epoch"]]
    for candle in after:
        if candle["close"] > rng["high"]:
            return {"trigger": candle, "range_high": rng["high"], "range_low": rng["low"]}
    return None
