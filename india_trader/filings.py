"""NSE corporate-announcement watcher, replacing the US-only Pelosi tracker."""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

from .storage import read_json, write_json

NSE_HOME = "https://www.nseindia.com/"
NSE_ANNOUNCEMENTS = "https://www.nseindia.com/api/corporate-announcements"
NSE_FILINGS_PAGE = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"


def fetch_announcements(symbols: list[str], since_days: int = 7) -> dict:
    start = date.today() - timedelta(days=since_days)
    end = date.today()
    cookie_jar = urllib.request.HTTPCookieProcessor()
    opener = urllib.request.build_opener(cookie_jar)
    base_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36",
                    "Accept": "application/json,text/plain,*/*", "Referer": NSE_FILINGS_PAGE, "Origin": "https://www.nseindia.com"}
    try:
        opener.open(urllib.request.Request(NSE_HOME, headers={"User-Agent": base_headers["User-Agent"]}), timeout=15).read(1024)
        all_rows = []
        for symbol in symbols:
            query = urllib.parse.urlencode({"index": "equities", "symbol": symbol.upper(),
                                            "from_date": start.strftime("%d-%m-%Y"), "to_date": end.strftime("%d-%m-%Y")})
            req = urllib.request.Request(f"{NSE_ANNOUNCEMENTS}?{query}", headers=base_headers)
            with opener.open(req, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if isinstance(payload, dict):
                rows = payload.get("data", [])
            else:
                rows = payload
            for row in rows or []:
                row["requested_symbol"] = symbol.upper()
                row["filing_url"] = row.get("attchmntFile") or row.get("url")
                all_rows.append(row)
        return {"source": "NSE corporate announcements", "items": all_rows, "source_page": NSE_FILINGS_PAGE,
                "as_of": datetime.now().astimezone().isoformat()}
    except Exception as exc:
        return {"source": "NSE corporate announcements", "items": [], "partial": True,
                "error": f"NSE endpoint unavailable or changed: {exc}", "source_page": NSE_FILINGS_PAGE,
                "action": "Open the official filings page and provide/download the announcement CSV; no events were inferred."}


def new_filings(symbols: list[str], since_days: int = 7) -> dict:
    state = read_json("trader/state/filings.json", {"seen": []}) or {"seen": []}
    seen = set(state.get("seen", []))
    result = fetch_announcements(symbols, since_days)
    new = []
    for row in result["items"]:
        key = str(row.get("seq_id") or row.get("symbol") or "") + "|" + str(row.get("an_dt") or row.get("broadcastDate") or "") + "|" + str(row.get("desc") or row.get("subject") or "")
        if key not in seen:
            row["id"] = key
            new.append(row)
            seen.add(key)
    state["seen"] = list(seen)[-4000:]
    write_json("trader/state/filings.json", state)
    result["items"] = new
    result["new_count"] = len(new)
    return result


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbols", required=True)
    p.add_argument("--since-days", type=int, default=7)
    a = p.parse_args(argv)
    result = new_filings([x.strip().upper() for x in a.symbols.split(",") if x.strip()], a.since_days)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["items"] else (2 if result.get("partial") else 1)


if __name__ == "__main__":
    raise SystemExit(main())
