#!/usr/bin/env python3
"""Round-2 completion: the must-fetch/retry items with no verified outcome.
 (a) still-missing: EWF (R2 404), BND, HYG (document start honestly), DBE (R1 said 2007-01, never written)
 (b) R1-fail retries via start_date paging (R1 fetched without start_date -> 5000-row truncation
     could HIDE pre-2008 depth, so recheck EWC EIS TUR USCI COPX DBP ENOR EPHE with start 1995).
TwelveData free tier: 8 req/min respected. PASS -> more_etf/{id}.csv [date,close] only."""
import time, json, urllib.request
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"

def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("TWELVEDATA_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")

def fetch(sym, k, start=None):
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&outputsize=5000&apikey={k}&format=JSON")
    if start:
        url += f"&start_date={start}"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())

def lint(df):
    r = dict(n=len(df), start="", end="", status="", detail="")
    if df is None or len(df) < 250:
        r["status"] = "FAIL(short)"; r["detail"] = f"n={len(df)}"; return r
    s = df.set_index("date")["close"].astype(float).sort_index()
    s = s[s > 0]
    r["start"], r["end"], r["n"] = str(s.index[0].date()), str(s.index[-1].date()), len(s)
    if s.index[0] > pd.Timestamp("2007-01-01"):
        r["status"] = "FAIL(start)"; r["detail"] = f"start={r['start']}"; return r
    gaps = s.index.to_series().diff().dt.days.dropna()
    mg = int(gaps.max())
    jr = int((s.pct_change().abs() > 0.5).sum())
    if mg > 10:
        r["status"] = "FAIL(gap)"; r["detail"] = f"maxgap={mg}d"; return r
    if jr > 3:
        r["status"] = "FAIL(jumps)"; r["detail"] = f"|ret|>50% on {jr}d"; return r
    r["status"] = "PASS"; r["detail"] = f"maxgap={mg}d jumps={jr}"
    return r

# (sym, why, start_date or None)
JOBS = [
    ("EWF", "(a) France country", None),
    ("BND", "(a) total US bond", None),
    ("HYG", "(a) HY credit — expect 2007-04, document honestly", None),
    ("DBE", "(b) R1-fail recheck; R1 log said 2007-01 but never wrote", None),
    ("EWC", "(b) R1-fail 2008-01 — retry with paging", "1995-01-01"),
    ("EIS", "(b) R1-fail 2008-03 — retry with paging", "1995-01-01"),
    ("TUR", "(b) R1-fail 2008-03 — retry with paging", "1995-01-01"),
    ("USCI", "(b) R1-fail 2010-08 — retry with paging", "1995-01-01"),
    ("COPX", "(b) R1-fail 2010-04 — retry with paging", "1995-01-01"),
    ("DBP", "(b) R1-fail 2008-01 — retry with paging", "1995-01-01"),
    ("ENOR", "(b) R1-fail 2012-01 — retry with paging", "1995-01-01"),
    ("EPHE", "(b) R1-fail 2010-09 — retry with paging", "1995-01-01"),
]

k = key()
print(f"{'sym':<6}{'status':<14}{'n':>7}  {'start':<12}{'end':<12} detail | why")
npass = 0
for i, (sym, why, st) in enumerate(JOBS):
    try:
        js = fetch(sym, k, start=st)
    except Exception as e:
        print(f"{sym:<6}{'FETCH_FAIL':<14}{0:>7}  {'':<12}{'':<12} {repr(e)[:70]} | {why}")
        time.sleep(8); continue
    if js.get("status") == "error" or "values" not in js:
        print(f"{sym:<6}{'API_ERR':<14}{0:>7}  {'':<12}{'':<12} {str(js.get('message', js))[:70]} | {why}")
    else:
        df = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
        df["date"] = pd.to_datetime(df["date"])
        lr = lint(df)
        if lr["status"] == "PASS":
            out = df[["date", "close"]].sort_values("date")
            out["date"] = out["date"].dt.strftime("%Y-%m-%d")
            out.to_csv(f"{OUT}/{sym}.csv", index=False)
            npass += 1
        print(f"{sym:<6}{lr['status']:<14}{lr['n']:>7}  {lr['start']:<12}{lr['end']:<12} {lr['detail']} | {why}")
    if (i + 1) % 8 == 0:
        print("... rate-limit sleep 62s (8 req/min) ...")
        time.sleep(62)
    else:
        time.sleep(8)

print(f"\nTOTAL {len(JOBS)} attempted, {npass} PASS, {len(JOBS)-npass} FAIL/ERR")
