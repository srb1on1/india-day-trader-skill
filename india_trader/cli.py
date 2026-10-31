"""Command line entry point for the India Day Trader skill."""

from __future__ import annotations

import argparse
import json

from . import alerts, analyst, broker, calendar, entry, exit as exit_planner, filings, news, risk, scanner, timemachine, budget
from .fyers_data import FyersData
from .storage import read_json


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="india-trader", description=__doc__)
    p.add_argument("command", choices=("market", "symbols", "universe", "quote", "history", "scan", "entry", "exit", "replay", "budget", "risk", "news", "filings", "alerts", "broker", "analyst", "auth"))
    a, rest = p.parse_known_args(argv)
    if a.command == "market":
        result = calendar.session_status()
    elif a.command == "symbols":
        sp = argparse.ArgumentParser(); sp.add_argument("--exchange", choices=("NSE", "BSE"), default="NSE"); sp.add_argument("--refresh", action="store_true"); sp.add_argument("--query"); o = sp.parse_args(rest)
        master = FyersData.symbol_master(o.exchange, o.refresh)
        if o.query:
            result = FyersData.resolve_symbol(o.query, o.exchange)
        else:
            result = {"exchange": o.exchange, "count": len(master["symbols"]), "downloaded_at": master["downloaded_at"], "cache": f"trader/state/{o.exchange.lower()}_cm_symbol_master.json"}
    elif a.command == "universe":
        from .universe import main as universe_main
        return universe_main(rest)
    elif a.command == "quote":
        sp = argparse.ArgumentParser(); sp.add_argument("symbols", nargs="+"); o = sp.parse_args(rest); result = FyersData().quotes(o.symbols)
    elif a.command == "history":
        sp = argparse.ArgumentParser(); sp.add_argument("symbol"); sp.add_argument("resolution"); sp.add_argument("range_from"); sp.add_argument("range_to"); o = sp.parse_args(rest)
        resolved = FyersData.resolve_symbol(o.symbol); result = FyersData().history(resolved["symbol"], o.resolution, o.range_from, o.range_to)
    elif a.command == "scan":
        return scanner.main(rest)
    elif a.command == "entry":
        return entry.main(rest)
    elif a.command == "exit":
        return exit_planner.main(rest)
    elif a.command == "replay":
        return timemachine.main(rest)
    elif a.command == "budget":
        return budget.main(rest)
    elif a.command == "risk":
        return risk.main(rest)
    elif a.command == "news":
        return news.main(rest)
    elif a.command == "filings":
        return filings.main(rest)
    elif a.command == "alerts":
        return alerts.main(rest)
    elif a.command == "broker":
        return broker.main(rest)
    elif a.command == "analyst":
        return analyst.main(rest)
    elif a.command == "auth":
        from .auth import main as auth_main
        return auth_main(rest)
    else:
        result = {}
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
