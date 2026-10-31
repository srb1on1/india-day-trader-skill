"""India exchange session helpers. Unknown dates/special sessions fail closed."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .storage import read_json

IST = ZoneInfo("Asia/Kolkata")
NSE_OPEN = time(9, 15)
NSE_CLOSE = time(15, 30)
# NSE's official 2026 equity holiday list as checked on 2026-10-31.
NSE_2026_HOLIDAYS = {
    date.fromisoformat(x)
    for x in (
        "2026-01-15", "2026-01-26", "2026-03-03", "2026-03-26",
        "2026-03-31", "2026-04-03", "2026-04-14", "2026-05-01",
        "2026-05-28", "2026-06-26", "2026-09-14", "2026-10-02",
        "2026-10-20", "2026-11-10", "2026-11-24", "2026-12-25",
    )
}
SPECIAL_SESSIONS = {date(2026, 11, 8): "Muhurat session; use exchange-announced hours"}


def extra_holidays() -> set[date]:
    cfg = read_json("trader/config.json", {}) or {}
    values = cfg.get("extra_market_holidays", [])
    result: set[date] = set()
    for value in values:
        try:
            result.add(date.fromisoformat(str(value)))
        except ValueError:
            continue
    return result


def session_status(now: datetime | None = None, exchange: str = "NSE") -> dict:
    now = (now or datetime.now(IST)).astimezone(IST)
    day = now.date()
    if exchange.upper() not in {"NSE", "BSE"}:
        return {"open": False, "status": "unsupported_exchange", "exchange": exchange, "as_of": now.isoformat()}
    if day in SPECIAL_SESSIONS:
        return {"open": False, "status": "special_session_hours_unverified", "exchange": exchange, "note": SPECIAL_SESSIONS[day], "as_of": now.isoformat()}
    if day.weekday() >= 5 or day in NSE_2026_HOLIDAYS or day in extra_holidays():
        return {"open": False, "status": "closed", "exchange": exchange, "session_date": day.isoformat(), "as_of": now.isoformat()}
    current = now.timetz().replace(tzinfo=None)
    opened = NSE_OPEN <= current < NSE_CLOSE
    state = "open" if opened else ("pre_open" if current < NSE_OPEN else "closed")
    # A hard-coded calendar is only certified for the listed year. Do not
    # assert a future date is a valid trading day without refreshing holidays.
    if day.year > 2026:
        state = "calendar_refresh_required"
        opened = False
    return {"open": opened, "status": state, "exchange": exchange, "session_date": day.isoformat(),
            "opens_ist": NSE_OPEN.strftime("%H:%M"), "closes_ist": NSE_CLOSE.strftime("%H:%M"), "as_of": now.isoformat()}


def next_session_day(start: date) -> date:
    day = start + timedelta(days=1)
    if day.year > 2026:
        raise RuntimeError("Refresh the official exchange holiday calendar before calculating future sessions beyond 2026.")
    while day.weekday() >= 5 or day in NSE_2026_HOLIDAYS or day in extra_holidays():
        day += timedelta(days=1)
        if day.year > 2026:
            raise RuntimeError("Refresh the official exchange holiday calendar before calculating future sessions beyond 2026.")
    return day
