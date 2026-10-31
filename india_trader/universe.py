"""Refresh official index constituents and resolve them to exact FYERS symbols."""

from __future__ import annotations

import csv
import io
import urllib.request
from datetime import datetime, timezone

from .fyers_data import FyersData
from .storage import write_json

INDEX_CSV = {
    "nifty50": "https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv",
}


def constituents(index: str = "nifty50", refresh: bool = False) -> dict:
    key = index.lower()
    if key not in INDEX_CSV:
        raise ValueError(f"Unknown index {index}. Supported: {', '.join(INDEX_CSV)}")
    request = urllib.request.Request(INDEX_CSV[key], headers={"User-Agent": "Mozilla/5.0 india-day-trader-skill/0.1", "Accept": "text/csv,*/*"})
    with urllib.request.urlopen(request, timeout=25) as response:
        text = response.read().decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        raise RuntimeError("Official constituent CSV was empty or changed format.")
    fields = rows[0].keys()
    symbol_col = next((x for x in fields if x.lower() == "symbol"), None)
    if not symbol_col:
        raise RuntimeError(f"Official CSV has no Symbol column; got {list(fields)}")
    mapped, missing = [], []
    for row in rows:
        code = row.get(symbol_col, "").strip().upper()
        if not code:
            continue
        try:
            item = FyersData.resolve_symbol(code, "NSE")
            ticker = item.get("symbol", "")
            if item.get("tradeStatus") in (0, "0"):
                missing.append({"code": code, "reason": "inactive in FYERS Symbol Master"})
                continue
            mapped.append(ticker)
        except Exception as exc:
            missing.append({"code": code, "reason": str(exc)})
    result = {"index": key, "source": INDEX_CSV[key], "as_of_utc": datetime.now(timezone.utc).isoformat(),
              "constituent_count": len(rows), "resolved_count": len(mapped), "partial": bool(missing),
              "symbols": mapped, "missing": missing}
    write_json(f"trader/universes/{key}.json", result)
    return result


def main(argv=None) -> int:
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index", choices=tuple(INDEX_CSV), nargs="?", default="nifty50")
    parser.add_argument("--refresh", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = constituents(args.index, args.refresh)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 2 if result["partial"] else 0
    except Exception as exc:
        print(f"UNIVERSE FAILED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
