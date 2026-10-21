#!/usr/bin/env python3
"""DATA_ETF_MORE round-2: fetch charter must-fetch tickers still missing from more_etf.
Same fetcher contract as work_r1/fetch_etf_more.py (TwelveData free tier, 8 req/min,
fail-closed lint: start<=2007-01-01, max gap<=10 cal days, |ret|>50% on <=3 days).
Only PASS written to more_etf/{id}.csv as [date,close]."""
import sys, time, json, urllib.request
import pandas as pd, numpy as np
ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"

def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("TWELVEDATA_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")

# (symbol, why) — round-2 charter (a): only tickers NOT already in more_etf/.
# DBE: exact start recheck (R1 log said 2007-01 but did not write it).
SYMS = [
    ("EWF", "France country (intl rotation)"),
    ("EWQ", "Germany country (intl rotation)"),
    ("EWI", "Italy country (intl rotation)"),
    ("IYR", "US real estate (REIT)"),
    ("BND", "total US bond agg"),
    ("AGG", "US agg bonds"),
    ("HYG", "HY credit — document start-bound fail honestly"),
    ("DBE", "energy commodity ETF — exact-start recheck"),
]

def fetch_one(sym, k):
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&outputsize=5000&apikey={k}&format=JSON")
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())

def lint_close(df):
    """Fail-closed: start<=2007-01-01, gap<=10 cal days, <=3 days with |ret|>50%."""
    r = dict(n=len(df), start="", end="", status="", detail="")
    if df is None or len(df) < 250:
        r["status"] = "FAIL(short)"; r["detail"] = f"n={len(df)}"; return r
    s = df.set_index("date")["close"].astype(float).sort_index()
    s = s[s > 0]
    r["start"], r["end"], r["n"] = str(s.index[0].date()), str(s.index[-1].date()), len(s)
    if s.index[0] > pd.Timestamp("2007-01-01"):
        r["status"] = "FAIL(start)"; r["detail"] = r["start"]; return r
    gaps = s.index.to_series().diff().dt.days.dropna()
    mg = int(gaps.max())
    zrun = int((s.diff() == 0).groupby((s.diff() != 0).cumsum()).cumsum().max())
    jr = (s.pct_change().abs() > 0.5).sum()
    if mg > 10:
        r["status"] = "FAIL(gap)"; r["detail"] = f"maxgap={mg}d"; return r
    if jr > 3:
        r["status"] = "FAIL(jumps)"; r["detail"] = f"|ret|>50% on {jr}d"; return r
    r["status"] = "PASS"; r["detail"] = f"maxgap={mg}d flatrun={zrun}"
    return r

k = key()
rows = []
for i, (sym, why) in enumerate(SYMS):
    try:
        js = fetch_one(sym, k)
    except Exception as e:
        rows.append((sym, why, "FETCH_FAIL", repr(e)[:90], "", "", 0)); time.sleep(8); continue
    if js.get("status") == "error" or "values" not in js:
        rows.append((sym, why, "API_ERR", str(js.get("message", js))[:90], "", "", 0))
    else:
        df = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
        df["date"] = pd.to_datetime(df["date"])
        lr = lint_close(df)
        if lr["status"] == "PASS":
            out = df[["date", "close"]].sort_values("date")
            out["date"] = out["date"].dt.strftime("%Y-%m-%d")
            out.to_csv(f"{OUT}/{sym}.csv", index=False)
        rows.append((sym, why, lr["status"], lr["detail"], lr["start"], lr["end"], lr["n"]))
    if (i + 1) % 8 == 0:
        time.sleep(62)   # free tier 8 req/min

print(f"{'sym':<6}{'status':<18}{'n':>7}  {'start':<12}{'end':<12} detail / why")
for sym, why, st, det, s0, s1, n in rows:
    print(f"{sym:<6}{st:<18}{n:>7}  {s0:<12}{s1:<12} {det} | {why}")
npass = sum(1 for r in rows if r[2] == "PASS")
print(f"\nTOTAL {len(rows)} attempted, {npass} PASS, {len(rows)-npass} FAIL/ERR")
