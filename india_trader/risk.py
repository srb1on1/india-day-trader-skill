"""Hard-gate a hypothetical cash-equity order against INR risk rules."""

from __future__ import annotations

import argparse
from datetime import datetime

from .calendar import IST, session_status
from .storage import read_json, write_json


def check(order: dict | None = None, config: dict | None = None, now: datetime | None = None) -> dict:
    order = order or ((read_json("trader/orders.json", {}) or {}).get("orders") or [{}])[0]
    config = config or read_json("trader/config.json", {}) or {}
    now = (now or datetime.now(IST)).astimezone(IST)
    reasons = []
    symbol = str(order.get("symbol", "")).upper()
    side = str(order.get("side", "")).lower()
    qty = int(order.get("qty", 0) or 0)
    entry, stop, target = (float(order.get(k, 0) or 0) for k in ("entry", "stop", "target"))
    if not symbol or side != "buy" or qty <= 0:
        reasons.append("Only a positive-quantity cash-equity buy proposal is supported.")
    if any(tag in symbol for tag in ("CE", "PE", "FUT")) and not config.get("allow_options", False):
        reasons.append("F&O is disabled in config.")
    if symbol in {str(x).upper() for x in config.get("blocked", [])}:
        reasons.append("Symbol is on the blocked list.")
    if not (0 < stop < entry < target):
        reasons.append("Require stop < entry < target.")
    else:
        loss = qty * (entry - stop) + qty * entry * float(config.get("cost_buffer_pct", 0) or 0) / 100
        if loss > float(config.get("max_loss_per_trade_inr", 0)):
            reasons.append(f"Stop loss risk ₹{loss:,.2f} exceeds per-trade cap.")
        rr = (target - entry) / (entry - stop)
        if rr < float(config.get("minimum_reward_risk", 1.5)):
            reasons.append(f"Reward:risk {rr:.2f} is below configured minimum.")
        order_value = qty * entry
        if order_value > float(config.get("max_order_inr", float("inf"))):
            reasons.append("Order value exceeds max_order_inr.")
    market = session_status(now, str(order.get("exchange", "NSE")))
    if not market["open"]:
        reasons.append(f"No new entries: exchange status is {market['status']}.")
    daily = read_json("trader/state/broker.json", {}) or {}
    today = now.date().isoformat()
    today_orders = [x for x in daily.get("events", []) if x.get("date") == today and x.get("event") in {"paper_approved", "placed", "filled"}]
    if len(today_orders) >= int(config.get("max_trades_per_day", 3)):
        reasons.append("Configured maximum trades for today is already reached.")
    if len(today_orders) >= int(config.get("max_orders_per_day", config.get("max_trades_per_day", 3))):
        reasons.append("Configured maximum order count for today is already reached.")
    today_risk = sum(float(x.get("max_loss_inr", 0)) for x in today_orders)
    proposed_risk = qty * max(0, entry - stop) + qty * entry * float(config.get("cost_buffer_pct", 0) or 0) / 100
    if today_risk + proposed_risk > float(config.get("max_daily_loss_inr", 0)):
        reasons.append("Total recorded plus proposed stop risk exceeds max_daily_loss_inr.")
    result = {"status": "PASS" if not reasons else "BLOCK", "symbol": symbol, "date": today,
              "checked_at_ist": now.isoformat(), "reasons": reasons, "market": market,
              "order": order, "fingerprint": f"{symbol}|{side}|{qty}|{entry:.4f}|{stop:.4f}|{target:.4f}"}
    state = read_json("trader/state/risk.json", {"checks": []}) or {"checks": []}
    state.setdefault("checks", []).append(result)
    state["checks"] = state["checks"][-500:]
    write_json("trader/state/risk.json", state)
    return result


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__).parse_args(argv)
    result = check()
    print(result)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
