"""Order-ticket and paper approval journal; this module never sends broker orders."""

from __future__ import annotations

import argparse
from datetime import datetime

from .calendar import IST
from .risk import check as risk_check
from .storage import read_json, write_json


def _fingerprint(order: dict) -> str:
    return f"{order.get('symbol','')}|{order.get('side','')}|{order.get('qty',0)}|{float(order.get('entry',0)):.4f}|{float(order.get('stop',0)):.4f}|{float(order.get('target',0)):.4f}"


def show() -> dict:
    orders = read_json("trader/orders.json", {"orders": []}) or {"orders": []}
    risk = read_json("trader/state/risk.json", {"checks": []}) or {"checks": []}
    result = []
    today = datetime.now(IST).date().isoformat()
    passed = {x.get("fingerprint") for x in risk.get("checks", []) if x.get("status") == "PASS" and x.get("date") == today}
    for order in orders.get("orders", []):
        result.append({"ticket": order, "risk_passed_today": _fingerprint(order) in passed,
                       "execution": "disabled: ticket/paper workflow only"})
    return {"tickets": result}


def approve(index: int, reply: str, mode: str = "paper") -> dict:
    if mode != "paper":
        raise PermissionError("Live execution is disabled. The current FYERS app is market-data-only; this project has no order endpoint.")
    orders = (read_json("trader/orders.json", {}) or {}).get("orders", [])
    if index < 1 or index > len(orders):
        raise IndexError("Ticket index does not exist.")
    order = orders[index - 1]
    risk = risk_check(order)
    if risk["status"] != "PASS":
        raise PermissionError("Risk check blocked this ticket: " + "; ".join(risk["reasons"]))
    if reply.strip().lower() != "yes":
        raise PermissionError("This exact ticket requires the literal reply 'yes'. No paper approval recorded.")
    journal = read_json("trader/state/broker.json", {"events": []}) or {"events": []}
    event = {"event": "paper_approved", "date": datetime.now(IST).date().isoformat(), "time_ist": datetime.now(IST).isoformat(),
             "symbol": order["symbol"], "side": order["side"], "qty": order["qty"], "fingerprint": risk["fingerprint"],
             "max_loss_inr": order.get("estimated_max_loss_inr"), "submission": "none; paper journal only"}
    journal.setdefault("events", []).append(event)
    write_json("trader/state/broker.json", journal)
    return event


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("show")
    ap = sub.add_parser("approve")
    ap.add_argument("--index", type=int, required=True)
    ap.add_argument("--reply", required=True)
    sub.add_parser("log")
    a = p.parse_args(argv)
    try:
        result = show() if a.command == "show" else (read_json("trader/state/broker.json", {"events": []}) if a.command == "log" else approve(a.index, a.reply))
        print(result)
        return 0
    except Exception as exc:
        print(f"TICKET NOT APPROVED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
