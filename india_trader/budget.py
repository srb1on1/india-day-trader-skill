"""INR position sizing from explicit user-configured limits."""

from __future__ import annotations

import argparse
import math

from .storage import read_json, write_json

DEFAULT_CONFIG = {
    "cash_budget_inr": 100000, "cash_buffer_pct": 10, "max_loss_per_trade_inr": 500,
    "max_daily_loss_inr": 1500, "max_position_pct": 25, "max_order_inr": 50000,
    "min_order_inr": 500, "minimum_reward_risk": 1.5, "max_trades_per_day": 3,
    "blocked": [], "watchlist": [], "allow_short": False, "allow_options": False,
    "cost_buffer_pct": 0,
}


def size_trade(config: dict | None = None, plan: dict | None = None, cash_inr: float | None = None) -> dict:
    config = config or read_json("trader/config.json", DEFAULT_CONFIG) or DEFAULT_CONFIG
    plan = plan or read_json("trader/plan.json", {}) or {}
    entry, stop, target = (float(plan.get(k, 0) or 0) for k in ("entry", "stop", "target"))
    if not plan.get("symbol") or not (0 < stop < entry < target):
        raise ValueError("Need a valid plan with stop < entry < target.")
    risk_per_share = entry - stop
    cost_pct = float(config.get("cost_buffer_pct", 0) or 0) / 100
    effective_risk = risk_per_share + entry * cost_pct
    budget = float(config.get("cash_budget_inr", 0))
    cash = float(cash_inr if cash_inr is not None else budget)
    buffer = cash * float(config.get("cash_buffer_pct", 10)) / 100
    limits = {
        "max_loss": math.floor(float(config.get("max_loss_per_trade_inr", 0)) / effective_risk),
        "position_cap": math.floor(budget * float(config.get("max_position_pct", 25)) / 100 / entry),
        "max_order": math.floor(float(config.get("max_order_inr", budget)) / entry),
        "cash_after_buffer": math.floor(max(0, cash - buffer) / entry),
    }
    qty = min(limits.values())
    limiting_rule = min(limits, key=limits.get)
    gross = round(qty * entry, 2)
    max_loss = round(qty * effective_risk, 2)
    if qty <= 0 or gross < float(config.get("min_order_inr", 0)):
        raise ValueError("No whole-share quantity meets the configured minimum order and risk limits.")
    result = {"symbol": plan["symbol"], "exchange": plan.get("exchange", "NSE"), "side": "buy", "qty": qty,
              "entry": entry, "stop": stop, "target": target, "gross_value_inr": gross,
              "estimated_max_loss_inr": max_loss, "risk_per_share_inr": round(effective_risk, 4),
              "limits_shares": limits, "limiting_rule": limiting_rule, "cost_buffer_pct": cost_pct * 100,
              "status": "proposal_only", "paper": True}
    write_json("trader/orders.json", {"orders": [result]})
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cash-inr", type=float)
    a = p.parse_args(argv)
    try:
        print(size_trade(cash_inr=a.cash_inr))
        return 0
    except Exception as exc:
        print(f"SIZING BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
