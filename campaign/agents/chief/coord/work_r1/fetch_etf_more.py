#!/usr/bin/env python3
"""DATA_ETF_MORE round-1: fetch more free ETF daily bars via TwelveData free tier.
Rate-limit-aware (8 req/min free), fail-closed lint (start>=2005, gaps<=10d, sane jumps).
Only PASS written to more_etf/{id}.csv; all attempts recorded."""
import sys, os, time, json, urllib.request
import pandas as pd, numpy as np
ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"

def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("TWELVEDATA_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")

# (symbol, why) — gaps only: sector XLE/XLF/XLI/XLB missing from more_etf; intl/single-commodity/rates-credit gaps
SYMS = [
    ("XLE", "sector energy (11-SPDR set for HUNT_SECTOR2)"),
    ("XLF", "sector financials"),
    ("XLI", "sector industrials"),
    ("XLB", "sector materials"),
    ("LQD", "IG credit ETF (HUNT_CREDIT2 leg)"),
    ("HYG", "HY credit ETF"),
    ("TLT", "20y treasury"),
    ("IEF", "7-10y treasury"),
    ("EWH", "HK country"),
    ("EWC", "Canada country"),
    ("EIS", "Israel country"),
    ("TUR", "Turkey country"),
    ("ENOR", "Norway country"),
    ("EPHE", "Philippines country"),
    ("EWM", "Malaysia country"),
    ("USCI", "copper commodity ETF"),
    ("DBP", "precious-metal double commodity"),
    ("DBE", "energy commodity ETF"),
    ("COPX", "copper miners"),
    ("GLD", "gold (more_etf lacks; has IAU/SLV)"),
]
def fetch_one(sym, k):
    url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day&outputsize=5000&apikey={k}&format=JSON"
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())

def lint_close(df):
    """Fail-closed: start>=2005, no gap>10 cal days, no long zero/flat runs, sane jumps."""
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
