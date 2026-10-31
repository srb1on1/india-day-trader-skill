"""Small read-only FYERS V3 client. Credentials are read from the OS keyring."""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Any

SERVICE = "india-day-trader-skill"
_LAST_DATA_CALL = 0.0
MASTER_URLS = {
    "NSE": "https://public.fyers.in/sym_details/NSE_CM_sym_master.json",
    "BSE": "https://public.fyers.in/sym_details/BSE_CM_sym_master.json",
}


class FyersData:
    def __init__(self) -> None:
        try:
            import keyring
        except ImportError as exc:
            raise RuntimeError("Install dependencies from pyproject.toml first.") from exc
        client_id = keyring.get_password(SERVICE, "client_id")
        access_token = keyring.get_password(SERVICE, "access_token")
        if not client_id or not access_token:
            raise RuntimeError(
                "FYERS credentials are not set up or today's token has expired. "
                "Run the local authentication setup described in SETUP.md."
            )
        try:
            from fyers_apiv3 import fyersModel
        except ImportError as exc:
            raise RuntimeError("Install dependencies from pyproject.toml first.") from exc
        self.client = fyersModel.FyersModel(
            client_id=client_id,
            token=access_token,
            is_async=False,
            log_path="",
        )

    @staticmethod
    def _pace() -> None:
        global _LAST_DATA_CALL
        # Standard plan: 5/sec and 50/min. Use a conservative ~1.25 sec gap.
        now = time.monotonic()
        wait = 1.25 - (now - _LAST_DATA_CALL)
        if wait > 0:
            time.sleep(wait)
        _LAST_DATA_CALL = time.monotonic()

    def quotes(self, symbols: list[str]) -> dict[str, Any]:
        clean = [symbol.strip() for symbol in symbols if symbol.strip()]
        if not clean:
            raise ValueError("Provide at least one FYERS symbol.")
        if len(clean) > 50:
            raise ValueError("Standard-plan quote requests support at most 50 symbols.")
        self._pace()
        response = self.client.quotes(data={"symbols": ",".join(clean)})
        return _json_safe(response)

    def history(
        self,
        symbol: str,
        resolution: str,
        range_from: str,
        range_to: str,
    ) -> dict[str, Any]:
        if not symbol.strip():
            raise ValueError("Provide a FYERS symbol from the current Symbol Master.")
        if not range_from or not range_to:
            raise ValueError("Provide range_from and range_to.")
        request = {
            "symbol": symbol.strip(),
            "resolution": resolution,
            "date_format": "1",
            "range_from": range_from,
            "range_to": range_to,
            "cont_flag": "1",
        }
        self._pace()
        response = self.client.history(data=request)
        return _json_safe(response)

    @staticmethod
    def symbol_master(exchange: str = "NSE", refresh: bool = False) -> dict[str, Any]:
        exchange = exchange.upper()
        if exchange not in MASTER_URLS:
            raise ValueError("Symbol master exchange must be NSE or BSE.")
        path = Path("trader") / "state" / f"{exchange.lower()}_cm_symbol_master.json"
        if not refresh and path.exists():
            try:
                cached = json.loads(path.read_text(encoding="utf-8"))
                if cached.get("symbols") and cached.get("downloaded_at"):
                    return cached
            except (OSError, json.JSONDecodeError):
                pass
        request = urllib.request.Request(
            MASTER_URLS[exchange],
            headers={"User-Agent": "india-day-trader-skill/0.1 contact: local-user", "Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not isinstance(data, dict) or not data:
            raise RuntimeError(f"FYERS returned an empty {exchange} symbol master.")
        result = {"exchange": exchange, "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "symbols": data}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        return result

    @classmethod
    def resolve_symbol(cls, query: str, exchange: str = "NSE") -> dict[str, Any]:
        master = cls.symbol_master(exchange)
        symbols = master["symbols"]
        query = query.strip().upper()
        if query in symbols:
            item = symbols[query]
            return {"symbol": query, **item} if isinstance(item, dict) else {"symbol": query}
        candidates = []
        for key, item in symbols.items():
            if not isinstance(item, dict):
                continue
            ticker = str(item.get("symTicker", key)).upper()
            exsym = str(item.get("exSymbol", "")).upper()
            if query in {ticker, exsym, f"{exchange}:{exsym}"}:
                candidates.append({"symbol": key, **item})
        if not candidates:
            raise ValueError(f"No {exchange} symbol-master match for {query}.")
        # Prefer ordinary-equity EQ-series over alternate series when the query is ambiguous.
        candidates.sort(key=lambda x: (0 if str(x.get("exSeries", "")).upper() == "EQ" else 1, str(x.get("symbol", ""))))
        return candidates[0]


def _json_safe(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        return json.loads(json.dumps(value, default=str))
    except (TypeError, ValueError):
        return {"response": str(value)}
