"""Market-session awareness: is a given market OPEN right now?

THE TRADING RULE (read this): a price is only actionable if its market is
currently open (or just closed within a tradeable buffer). A US-equity quote
from Friday's close shown on a Sunday is ~36h stale and USELESS for a trade --
worse than nothing, because it looks actionable but isn't. So the scanner must:

  1. Know each market's real session (in UTC, DST-aware for the US).
  2. Only surface a backtested opportunity if its market is OPEN (or within a
     short post-close buffer), with data fresh enough to act on.

Sessions implemented (UTC). Days are Mon=0..Sun=6 in US/Asia local time:
  CRYPTO : 24/7 -- always open, the only truly always-tradeable book.
  FX     : continuous Sun 21:00 UTC -> Fri 21:00 UTC (closed weekends).
  US     : Mon-Fri 13:30-20:00 UTC (EDT) / 14:30-21:00 UTC (EST). DST-aware.
  CN-A   : Mon-Fri 01:30-03:30 and 05:00-07:00 UTC (lunch break). No DST.
  TW     : Mon-Fri 01:00-05:30 UTC. No DST.
  HK     : Mon-Fri 01:30-04:00 and 05:00-08:00 UTC. No DST.

We intentionally treat the equity close + a short buffer as still "actionable"
(you can act at the next open / in post-market), but anything older -- and
ALWAYS a full weekend -- is flagged CLOSED and excluded from actionable ranking.
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta

try:
    from zoneinfo import ZoneInfo
    _ET = ZoneInfo("America/New_York")
except Exception:                       # pragma: no cover
    _ET = timezone(timedelta(hours=-4))

# Minutes after an equity/Asia close during which a quote is still "actionable"
# (you can plan the trade for the next session). Beyond this -> CLOSED/stale.
POSTCLOSE_BUFFER_MIN = 30

def _utc_now():
    return datetime.now(timezone.utc)

def _us_session_utc(now):
    """Return (open_utc, close_utc) for the US cash session on `now`'s ET date,
    DST-aware. 09:30-16:00 ET converted to UTC."""
    et = now.astimezone(_ET)
    open_et = et.replace(hour=9, minute=30, second=0, microsecond=0)
    close_et = et.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_et.astimezone(timezone.utc), close_et.astimezone(timezone.utc)

def _in_window(now, ranges, weekday_local):
    """weekday_local in 0..6 (Mon..Sun). ranges: list of (h1,m1,h2,m2) in UTC."""
    if weekday_local >= 5:           # Sat/Sun -> closed
        return False, None
    for h1, m1, h2, m2 in ranges:
        o = now.replace(hour=h1, minute=m1, second=0, microsecond=0)
        c = now.replace(hour=h2, minute=m2, second=0, microsecond=0)
        if o <= now <= c:
            return True, c
    return False, None

def market_status(market, now=None):
    """Return a dict: {open: bool, actionable: bool, label: str, next_close: dt|None}.

    `actionable` = open OR within POSTCLOSE_BUFFER_MIN of today's close (so a
    fresh just-closed quote can still be planned/traded next session). A weekend
    or a quote from a prior day is NOT actionable.
    """
    now = now or _utc_now()
    m = market.upper()

    if m == "CRYPTO":
        return {"open": True, "actionable": True, "label": "OPEN (24/7)",
                "next_close": None}

    if m == "FX":
        # Continuous Sun 21:00 UTC -> Fri 21:00 UTC.
        wd = now.weekday()  # Mon=0..Sun=6 (UTC)
        h = now.hour
        if wd == 5:                      # Saturday -> always closed
            openq = False
        elif wd == 6:                    # Sunday -> opens 21:00 UTC
            openq = h >= 21
        elif wd == 4:                    # Friday -> closes 21:00 UTC
            openq = h < 21
        else:
            openq = True
        return {"open": openq, "actionable": openq,
                "label": "OPEN (FX 24/5)" if openq else "CLOSED (FX weekend)",
                "next_close": None}

    if m == "US":
        o, c = _us_session_utc(now)
        et = now.astimezone(_ET)
        if et.weekday() >= 5:
            return {"open": False, "actionable": False,
                    "label": "CLOSED (US weekend)", "next_close": None}
        if o <= now <= c:
            return {"open": True, "actionable": True, "label": "OPEN (US cash)",
                    "next_close": c}
        # within buffer after close -> still actionable for next session
        if c < now <= c + timedelta(minutes=POSTCLOSE_BUFFER_MIN):
            return {"open": False, "actionable": True,
                    "label": "JUST CLOSED (US)", "next_close": c}
        return {"open": False, "actionable": False, "label": "CLOSED (US)",
                "next_close": None}

    # Asia markets quote in UTC windows; convert "local weekday" via UTC (their
    # sessions sit well within a single UTC day, so UTC weekday is fine here).
    ASIA = {
        "CN-A": [(1, 30, 3, 30), (5, 0, 7, 0)],
        "TW":   [(1, 0, 5, 30)],
        "HK":   [(1, 30, 4, 0), (5, 0, 8, 0)],
    }
    if m in ASIA:
        openq, close_c = _in_window(now, ASIA[m], now.weekday())
        if openq:
            return {"open": True, "actionable": True, "label": f"OPEN ({m})",
                    "next_close": close_c}
        # buffer after the LAST close window of the day
        if now.weekday() < 5:
            last_close_h, last_close_m = ASIA[m][-1][2], ASIA[m][-1][3]
            lc = now.replace(hour=last_close_h, minute=last_close_m,
                             second=0, microsecond=0)
            if lc < now <= lc + timedelta(minutes=POSTCLOSE_BUFFER_MIN):
                return {"open": False, "actionable": True,
                        "label": f"JUST CLOSED ({m})", "next_close": lc}
        return {"open": False, "actionable": False, "label": f"CLOSED ({m})",
                "next_close": None}

    # Unknown markets (FUT/IDX): be conservative -> treat as not-actionable unless
    # a fresh timestamp says otherwise (handled by the data-freshness gate).
    return {"open": False, "actionable": False, "label": "CLOSED (unknown)",
            "next_close": None}

def is_actionable(market, now=None):
    """True if `market` is open or just-closed (within buffer) -> tradeable now."""
    return market_status(market, now)["actionable"]

def open_markets(now=None):
    """Set of markets currently OPEN -- handy for headers/diagnostics."""
    now = now or _utc_now()
    return {m for m in ("CRYPTO", "FX", "US", "CN-A", "TW", "HK")
            if market_status(m, now)["open"]}
