"""Small read-only FYERS V3 client. Credentials are read from the OS keyring."""

from __future__ import annotations

import json
from typing import Any

SERVICE = "india-day-trader-skill"


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

    def quotes(self, symbols: list[str]) -> dict[str, Any]:
        clean = [symbol.strip() for symbol in symbols if symbol.strip()]
        if not clean:
            raise ValueError("Provide at least one FYERS symbol.")
        if len(clean) > 50:
            raise ValueError("Standard-plan quote requests support at most 50 symbols.")
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
        response = self.client.history(data=request)
        return _json_safe(response)


def _json_safe(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    try:
        return json.loads(json.dumps(value, default=str))
    except (TypeError, ValueError):
        return {"response": str(value)}

