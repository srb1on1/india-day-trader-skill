"""News monitor for Indian tickers using Google News RSS; links disclose source."""

from __future__ import annotations

import argparse
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

from .storage import read_json, write_json

RSS = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


def fetch_news(query: str, limit: int = 15) -> list[dict]:
    url = RSS.format(query=urllib.parse.quote(query))
    req = urllib.request.Request(url, headers={"User-Agent": "india-day-trader-skill/0.1 (news research)"})
    with urllib.request.urlopen(req, timeout=20) as response:
        root = ET.fromstring(response.read())
    results = []
    for item in root.findall("./channel/item")[:limit]:
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub = item.findtext("pubDate", "")
        source = item.find("source")
        results.append({"title": title, "url": link, "published": pub, "publisher": source.text if source is not None else "unknown"})
    return results


def monitor(symbols: list[str], hours: int = 24) -> dict:
    state = read_json("trader/state/news.json", {"seen": []}) or {"seen": []}
    seen = set(state.get("seen", []))
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    found, failures = [], []
    for symbol in symbols:
        try:
            rows = fetch_news(f'"{symbol}" NSE India stock', limit=20)
            for row in rows:
                key = row["url"] or row["title"]
                row["symbol"] = symbol
                row["id"] = key
                try:
                    published = datetime.strptime(row["published"], "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
                    row["published_utc"] = published.isoformat()
                    if published < since:
                        continue
                except ValueError:
                    row["published_utc"] = None
                if key and key not in seen:
                    found.append(row)
                    seen.add(key)
        except Exception as exc:
            failures.append({"symbol": symbol, "error": str(exc)})
    state["seen"] = list(seen)[-2000:]
    write_json("trader/state/news.json", state)
    return {"as_of_utc": datetime.now(timezone.utc).isoformat(), "hours": hours,
            "items": sorted(found, key=lambda x: x.get("published_utc") or "", reverse=True), "failures": failures,
            "source": "Google News RSS; independently verify material claims against NSE/BSE filings or the company IR page."}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--symbols", required=True, help="comma-separated Indian ticker symbols")
    p.add_argument("--hours", type=int, default=24)
    a = p.parse_args(argv)
    result = monitor([x.strip().upper() for x in a.symbols.split(",") if x.strip()], a.hours)
    print(result)
    return 0 if result["items"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
