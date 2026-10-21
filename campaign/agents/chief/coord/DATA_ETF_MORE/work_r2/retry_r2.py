#!/usr/bin/env python3
"""Round-2 retries: (1) EWF after 404; (2) charter-(b) R1 fails where same ticker may
have pre-2008 depth via start_date paging (R1 fetched without start_date, so
outputsize=5000 truncated all series at ~2006-10)."""
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

def write_pass(sym, df):
    out = df[["date", "close"]].sort_values("date")
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    out.to_csv(f"{OUT}/{sym}.csv", index=False)

k = key()
time.sleep(62)  # reset the 8/min window after the previous 8 calls

print("--- retry EWF (was HTTP 404) ---")
try:
    js = fetch("EWF", k)
    print("raw keys:", sorted(js.keys()), "| status:", js.get("status"), "| code:", js.get("code"), "| msg:", str(js.get("message"))[:80])
    if "values" in js:
        df = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
        df["date"] = pd.to_datetime(df["date"])
        lr = lint(df)
        print("EWF lint:", lr)
except Exception as e:
    print("EWF fetch exception:", repr(e))

time.sleep(8)
print("--- retry EWC with start_date=1995-01-01 (R1 artifact suspect, true inception 1996) ---")
try:
    js = fetch("EWC", k, start="1995-01-01")
    if "values" in js:
        df = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
        df["date"] = pd.to_datetime(df["date"])
        lr = lint(df)
        print("EWC lint:", lr)
        if lr["status"] == "PASS":
            write_pass("EWC", df); print("EWC WRITTEN to more_etf/EWC.csv")
    else:
        print("EWC API_ERR:", str(js.get("message", js))[:100])
except Exception as e:
    print("EWC fetch exception:", repr(e))

time.sleep(8)
print("--- retry DBP with start_date=1995-01-01 (true inception 2006-01, R1 saw 2008-01) ---")
try:
    js = fetch("DBP", k, start="1995-01-01")
    if "values" in js:
        df = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
        df["date"] = pd.to_datetime(df["date"])
        lr = lint(df)
        print("DBP lint:", lr)
        if lr["status"] == "PASS":
            write_pass("DBP", df); print("DBP WRITTEN to more_etf/DBP.csv")
    else:
        print("DBP API_ERR:", str(js.get("message", js))[:100])
except Exception as e:
    print("DBP fetch exception:", repr(e))
