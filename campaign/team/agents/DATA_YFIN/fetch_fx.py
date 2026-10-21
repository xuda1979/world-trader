"""DATA_YFIN fallback leg 1: FX daily closes via Frankfurter (ECB, no key, direct HTTP).

Yahoo is geo-blocked from this egress (ATS 403, lang=zh page, pre-existing) —
evidence in FINDINGS.md. Frankfurter verified 200 with 1999+ span. FX = charter
'more FX' leg. Writes canonical date,open,high,low,close,volume (OHLC=close, vol=0).
"""
import json
import sys
import time

import requests

HERE = "/Users/daxu/software/world-trader/campaign/team/agents/DATA_YFIN"
sys.path.insert(0, HERE)
import yfin_dl  # noqa: E402

BASE = "https://api.frankfurter.app"
START = "1999-01-04"
USD_PAIRS = {"CHF", "SEK", "NOK", "SGD", "MXN", "ZAR", "TRY", "INR", "BRL", "KRW",
             "HKD", "TWD", "PLN", "CZK", "HUF", "ILS", "PHP", "IDR", "THB", "CLP",
             "COP", "RON", "BGN", "DKK", "ISK", "CNH"}


def fx_url(start):
    return f"{BASE}/{start}..2026-09-08?from=USD"


def fetch_fx(start=START, pause=1.0):
    """Fetch USD base matrix; return {sym: rows} with USD_XXX and XXX_USD pairs."""
    r = requests.get(fx_url(start), timeout=60)
    r.raise_for_status()
    data = r.json()
    rates = data.get("rates", {})
    if not rates:
        raise RuntimeError("empty frankfurter payload")
    dates = sorted(rates)
    out = {}
    cur = set()
    for d in dates:
        cur.update(rates[d].keys())
    for ccy in sorted(cur):
        for sym_base, invert in ((f"USD_{ccy}", False), (f"{ccy}_USD", True)):
            rows = _pair_rows(dates, rates, ccy, invert)
            if len(rows) >= 250:
                out[sym_base] = rows
        time.sleep(pause)
    return out


def _pair_rows(dates, rates, ccy, invert):
    rows = []
    prev = None
    for d in dates:
        v = rates[d].get(ccy)
        if not v:
            prev = None
            continue
        px = (1.0 / v) if invert else float(v)
        rows.append((d, px, px, px, px, 0))
        prev = px
    return rows


def main():
    pairs = fetch_fx()
    written = []
    for sym, rows in sorted(pairs.items()):
        if yfin_dl.write_csv(sym, rows):
            written.append((sym, len(rows)))
    print(json.dumps({"written": written}, indent=1))


if __name__ == "__main__":
    main()
