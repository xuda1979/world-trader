"""Forward-return validation for the live net-net list (start of the
historical leg). For each candidate in full_screen.json, pulls Finnhub
daily candles from the NCAV report period to today and measures the return
since the report became knowable — the first honest read on whether these
cigar butts actually re-rate (or die).

Caveat: most reports are 2026-06-30 (report-period dates are recent), so
ret_since_period is mostly a 1-2 month window; BIYA (2025-12-31) has ~7.5
months. Longer-horizon validation needs historical price feeds for these
micros (yfinance throttled; Stooq blocked) — noted for later iterations.
"""
from __future__ import annotations
import json, os, sys, time, urllib.request
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.chdir(HERE)

def api_key(name, var):
    for p in ("/Users/daxu/software/world-trader/.env.local",
              "/Users/daxu/software/world-trader/.env"):
        if os.path.exists(p):
            for line in open(p):
                if line.startswith(f"{var}="):
                    return line.strip().split("=", 1)[1]
    raise SystemExit(f"no {var}")

def candles(t, pk, from_ts, to_ts):
    """Polygon daily aggs (free tier: ~2y history, 5 req/min)."""
    d0 = pd.Timestamp(from_ts, unit="s").date().isoformat()
    d1 = pd.Timestamp(to_ts, unit="s").date().isoformat()
    url = f"https://api.polygon.io/v2/aggs/ticker/{t}/range/1/day/{d0}/{d1}?apiKey={pk}"
    d = json.load(urllib.request.urlopen(url, timeout=25))
    if not d.get("results"):  # v2 aggs has no "status" field; results list is it
        return None
    df = pd.DataFrame(d["results"])
    df["date"] = pd.to_datetime(df["t"], unit="ms")
    return df.set_index("date")[["c"]].rename(columns={"c": "close"}).sort_index()

def main():
    screen = json.load(open("data/full_screen.json"))
    cands = (screen.get("netnets", []) + screen.get("near_misses", []))
    cache = json.load(open("data/full_cache.json"))
    pk = api_key("polygon", "POLYGON_KEY")
    now_ts = int(time.time())
    rows = []
    for c in cands:
        t = c["ticker"]
        rec = cache.get(t, {})
        per = rec.get("ncav_period")
        if not per:
            print(f"  {t}: no ncav_period, skip"); continue
        p0 = pd.Timestamp(per)
        from_ts = max(int((p0 - pd.Timedelta(days=3)).timestamp()),
                      now_ts - 800 * 86400)  # polygon free ~2y window
        df = candles(t, pk, from_ts, now_ts)
        time.sleep(12.5)  # polygon free: 5 req/min
        if df is None or len(df) == 0:
            print(f"  {t}: no candles"); continue
        base = df[df.index <= p0]
        if len(base) == 0:
            base = df.iloc[[0]]
        p_b = float(base["close"].iloc[-1])
        p_n = float(df["close"].iloc[-1])
        mos = (pd.Timestamp.today() - p0).days / 30.4
        rows.append({"ticker": t, "period": per, "months_since": round(mos, 1),
                     "price_at_period": round(p_b, 2), "price_now": round(p_n, 2),
                     "ret_since_period_pct": round((p_n / p_b - 1) * 100, 1),
                     "ratio": round(c["ncav_mc_ratio"], 2)})
    df = pd.DataFrame(rows).sort_values("ratio", ascending=False)
    with pd.option_context("display.float_format", lambda x: f"{x:,.2f}",
                           "display.max_columns", None, "display.width", 220):
        print(df.to_string(index=False))
    df.to_json("data/full_validation.json", orient="records", indent=1)
    print(f"wrote data/full_validation.json ({len(df)} names)")

if __name__ == "__main__":
    main()
