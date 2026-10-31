"""YoY and TTM analysis for normalized Indian quarterly-result CSV exports."""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from .storage import write_json

FIELDS = ("symbol", "period_end", "scope", "revenue_inr_cr", "operating_profit_inr_cr", "net_profit_inr_cr", "diluted_eps_inr", "source_url")


def analyze_csv(path: str, symbol: str | None = None) -> dict:
    with Path(path).open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [x for x in FIELDS if x not in (reader.fieldnames or [])]
        if missing:
            raise ValueError("CSV missing required columns: " + ", ".join(missing))
        rows = []
        for raw in reader:
            if symbol and raw["symbol"].upper() != symbol.upper():
                continue
            if raw["scope"].strip().lower() != "consolidated":
                continue
            row = dict(raw)
            row["period_end"] = date.fromisoformat(raw["period_end"])
            for key in FIELDS[3:7]:
                row[key] = float(raw[key]) if raw.get(key) else None
            row["gross_profit_inr_cr"] = float(raw["gross_profit_inr_cr"]) if raw.get("gross_profit_inr_cr") else None
            rows.append(row)
    rows.sort(key=lambda x: x["period_end"])
    if not rows:
        raise ValueError("No consolidated quarterly rows found for that symbol.")
    by_period = {(r["period_end"].month, r["period_end"].year): r for r in rows}
    latest = rows[-1]
    prior = by_period.get((latest["period_end"].month, latest["period_end"].year - 1))
    def margin(row, profit_key):
        revenue, profit = row.get("revenue_inr_cr"), row.get(profit_key)
        return (profit / revenue * 100) if revenue and profit is not None else None
    yoy = {}
    for key in ("revenue_inr_cr", "operating_profit_inr_cr", "net_profit_inr_cr", "diluted_eps_inr"):
        a, b = latest.get(key), prior.get(key) if prior else None
        yoy[key] = {"current": a, "year_ago": b, "change_pct": round((a / b - 1) * 100, 2) if a is not None and b not in (None, 0) else None}
    quarters = rows[-4:]
    ttm = {key: round(sum(float(r[key] or 0) for r in quarters), 2) for key in ("revenue_inr_cr", "operating_profit_inr_cr", "net_profit_inr_cr")}
    ttm["operating_margin_pct"] = round(ttm["operating_profit_inr_cr"] / ttm["revenue_inr_cr"] * 100, 2) if ttm["revenue_inr_cr"] else None
    ttm["net_margin_pct"] = round(ttm["net_profit_inr_cr"] / ttm["revenue_inr_cr"] * 100, 2) if ttm["revenue_inr_cr"] else None
    gross_values = [r.get("gross_profit_inr_cr") for r in quarters]
    if all(value is not None for value in gross_values):
        ttm["gross_profit_inr_cr"] = round(sum(gross_values), 2)
        ttm["gross_margin_pct"] = round(ttm["gross_profit_inr_cr"] / ttm["revenue_inr_cr"] * 100, 2) if ttm["revenue_inr_cr"] else None
    result = {"symbol": latest["symbol"], "latest_period_end": latest["period_end"].isoformat(), "scope": "consolidated",
              "units": "INR crore except EPS (INR/share)", "latest": {k: v for k, v in latest.items() if k != "period_end"} | {"period_end": latest["period_end"].isoformat()},
              "year_over_year": yoy, "latest_margins_pct": {"gross": (latest["gross_profit_inr_cr"] / latest["revenue_inr_cr"] * 100 if latest.get("gross_profit_inr_cr") is not None and latest.get("revenue_inr_cr") else None), "operating": margin(latest, "operating_profit_inr_cr"), "net": margin(latest, "net_profit_inr_cr")},
              "ttm_last_four_reported_quarters": ttm, "quarters_in_ttm": len(quarters),
              "source_urls": list(dict.fromkeys(r["source_url"] for r in rows if r.get("source_url"))),
              "data_limitations": "Rows must be standalone quarter figures in one consistent consolidated scope. Do not mix standalone/consolidated or cumulative periods. Gross profit is optional because Indian sector reporting varies. Q4 derived from FY minus 9M is not implemented in this input path."}
    write_json("trader/metrics.json", result)
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv")
    p.add_argument("--symbol")
    a = p.parse_args(argv)
    try:
        print(analyze_csv(a.csv, a.symbol))
        return 0
    except Exception as exc:
        print(f"ANALYSIS FAILED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
