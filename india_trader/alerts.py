"""One-shot local price/time alerts evaluated from FYERS quotes."""

from __future__ import annotations

import argparse
from datetime import datetime

from .calendar import IST, session_status
from .fyers_data import FyersData
from .storage import read_json, write_json


def add(symbol: str | None = None, above: float | None = None, below: float | None = None,
        at: str | None = None, label: str | None = None, from_plan: bool = False) -> dict:
    rules = read_json("trader/alerts.json", {"alerts": []}) or {"alerts": []}
    new = []
    if from_plan:
        plan = read_json("trader/plan.json", {}) or {}
        if not plan.get("symbol"):
            raise ValueError("No trader/plan.json found.")
        symbol = plan["symbol"]
        new = [{"id": f"{symbol}-stop-{plan['date']}", "symbol": symbol, "type": "below", "price": plan["stop"], "label": "planned stop"},
               {"id": f"{symbol}-target-{plan['date']}", "symbol": symbol, "type": "above", "price": plan["target"], "label": "planned target"},
               {"id": f"{symbol}-flat-{plan['date']}", "type": "time", "at": plan.get("flat_by_ist", "15:20"), "date": plan["date"], "label": "flat by planned time"}]
    elif at:
        new = [{"id": f"time-{datetime.now(IST).strftime('%Y%m%d%H%M%S')}", "type": "time", "at": at, "date": datetime.now(IST).date().isoformat(), "label": label or f"time {at}"}]
    elif symbol and (above is not None or below is not None):
        if above is not None:
            new.append({"id": f"{symbol}-above-{above}", "symbol": symbol, "type": "above", "price": above, "label": label or f"above ₹{above}"})
        if below is not None:
            new.append({"id": f"{symbol}-below-{below}", "symbol": symbol, "type": "below", "price": below, "label": label or f"below ₹{below}"})
    else:
        raise ValueError("Use --from-plan, --at HH:MM, or --symbol with --above/--below.")
    current = rules.setdefault("alerts", [])
    ids = {x.get("id") for x in current}
    for rule in new:
        if rule["id"] not in ids:
            current.append(rule)
    write_json("trader/alerts.json", rules)
    return {"added": new, "total": len(current)}


def check() -> dict:
    doc = read_json("trader/alerts.json", {"alerts": []}) or {"alerts": []}
    state = read_json("trader/state/alerts.json", {"fired": []}) or {"fired": []}
    fired_keys = set(state.get("fired", []))
    now = datetime.now(IST)
    eligible = []
    for rule in doc.get("alerts", []):
        key = f"{rule.get('id')}|{now.date().isoformat()}"
        if key in fired_keys:
            continue
        if rule.get("date") and rule["date"] != now.date().isoformat():
            continue
        if rule.get("type") == "time" and now.strftime("%H:%M") >= rule.get("at", "23:59"):
            if session_status(now).get("status") == "open" or not rule.get("before_close", False):
                eligible.append((rule, key, None))
    price_rules = [r for r in doc.get("alerts", []) if r.get("symbol") and r.get("type") in {"above", "below"}]
    symbols = list(dict.fromkeys(r["symbol"] for r in price_rules))
    quotes_by_symbol = {}
    if symbols:
        response = FyersData().quotes(symbols[:50])
        for item in response.get("d", []) or []:
            values = item.get("v", {})
            quotes_by_symbol[item.get("n", "")] = values.get("lp")
    for rule in price_rules:
        key = f"{rule.get('id')}|{now.date().isoformat()}"
        if key in fired_keys or (rule.get("date") and rule["date"] != now.date().isoformat()):
            continue
        price = quotes_by_symbol.get(rule["symbol"])
        if price is None:
            continue
        hit = price >= float(rule["price"]) if rule["type"] == "above" else price <= float(rule["price"])
        if hit:
            eligible.append((rule, key, price))
    events = []
    for rule, key, price in eligible:
        fired_keys.add(key)
        events.append({"id": rule.get("id"), "symbol": rule.get("symbol"), "label": rule.get("label"), "price": price,
                       "time_ist": now.isoformat(), "type": rule.get("type")})
    state["fired"] = list(fired_keys)[-5000:]
    write_json("trader/state/alerts.json", state)
    return {"as_of_ist": now.isoformat(), "events": events, "quotes": quotes_by_symbol,
            "note": "Alerts only report; they never submit or modify orders."}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    addp = sub.add_parser("add")
    addp.add_argument("--from-plan", action="store_true")
    addp.add_argument("--symbol")
    addp.add_argument("--above", type=float)
    addp.add_argument("--below", type=float)
    addp.add_argument("--at")
    addp.add_argument("--label")
    sub.add_parser("check")
    sub.add_parser("list")
    a = p.parse_args(argv)
    if a.command == "add":
        print(add(a.symbol, a.above, a.below, a.at, a.label, a.from_plan))
    elif a.command == "list":
        print(read_json("trader/alerts.json", {"alerts": []}))
    else:
        result = check()
        for event in result["events"]:
            print("\aALERT", event)
        if not result["events"]:
            print("No new alerts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
