#!/usr/bin/env python3
"""Round-2 (b) spirit: recover PRE-2008 depth for charter-(a) series truncated at
2006-10-17 by the vendor 5000-row cap (EWT precedent: 'OK+EXTEND(dedup-kept-first-vendor;2windows)').
One API call per symbol: head window 1995-01-01..2012-12-31; stitch onto the EXISTING
on-disk tail (already fetched fresh), keep first occurrence (head wins at the seam,
matching the recorded 'kept-first' precedent); re-lint fail-closed; report seam noise.
"""
import json, time, urllib.request
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"
START_BOUND = pd.Timestamp("2007-01-01")

def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("TWELVEDATA_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no TWELVEDATA_KEY")

K = key()
CALLS = 0

def fetch(sym):
    global CALLS
    if CALLS and CALLS % 8 == 0:
        print("   ... rate-limit sleep 62s (8 req/min) ...", flush=True)
        time.sleep(62)
    url = (f"https://api.twelvedata.com/time_series?symbol={sym}&interval=1day"
           f"&outputsize=5000&start_date=1995-01-01&end_date=2012-12-31"
           f"&apikey={K}&format=JSON")
    with urllib.request.urlopen(url, timeout=60) as r:
        js = json.loads(r.read().decode())
    CALLS += 1
    time.sleep(8)
    return js

# charter-(a) series only; expected true inceptions (public record)
JOBS = [
    ("EWH", 1994), ("EWJ", 1996), ("EWG", 1996), ("EWU", 1996), ("EWQ", 1996),
    ("EWL", 1996), ("EWS", 1996), ("EWI", 1996), ("EWP", 1996),
    ("IYR", 2000), ("VNQ", 2004), ("AGG", 2003), ("SHY", 2002), ("TIP", 2003),
]

res = []
for sym, exp_inc in JOBS:
    head_old = None
    try:
        js = fetch(sym)
        if js.get("status") == "error" or "values" not in js:
            print(f"{sym:<5} API_ERR {str(js.get('message', js))[:70]}"); res.append((sym, "API_ERR", 0, 0, "")); continue
        h = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
        h["date"] = pd.to_datetime(h["date"]); h["close"] = h["close"].astype(float)
        h = h.sort_values("date").reset_index(drop=True)
        head_old = h
    except Exception as e:
        print(f"{sym:<5} FETCH_FAIL {repr(e)[:70]}"); res.append((sym, "FETCH_FAIL", 0, 0, "")); continue

    old = pd.read_csv(f"{OUT}/{sym}.csv")
    old["date"] = pd.to_datetime(old["date"]); old["close"] = old["close"].astype(float)
    cur_start = old["date"].min()
    seam = h[h["date"].isin(old["date"])]
    noise = float(np.abs(seam["close"].values - old.set_index("date").loc[seam["date"], "close"].values).max()) if len(seam) else 0.0
    both = pd.concat([h, old]).drop_duplicates(subset="date", keep="first").sort_values("date").reset_index(drop=True)  # head wins at seam
    new_start = both["date"].min()
    added = len(both) - len(old)

    # fail-closed lint on stitched series
    s = both.set_index("date")["close"].sort_index(); s = s[s > 0]
    gaps = s.index.to_series().diff().dt.days.dropna(); mg = int(gaps.max())
    jr = int((s.pct_change().abs() > 0.5).sum())
    ok = (s.index[0] <= START_BOUND) and mg <= 10 and jr <= 3 and len(s) >= 250 and s.index[-1] >= pd.Timestamp("2026-06-01")
    if ok and added > 0:
        o = both.copy(); o["date"] = o["date"].dt.strftime("%Y-%m-%d")
        o[["date", "close"]].to_csv(f"{OUT}/{sym}.csv", index=False)
    st = "EXTENDED" if (ok and added > 0) else ("NO_GAIN" if ok else f"LINT_FAIL(gap={mg},jumps={jr})")
    print(f"{sym:<5} {st:<10} cur_start={cur_start.date()} -> new_start={new_start.date()} (inc~{exp_inc}) +{added} rows, seam_n={len(seam)}, seam_noise={noise:.4f}")
    res.append((sym, st, int(added), len(seam), f"{noise:.4f}"))

print("\nSUMMARY:", sum(1 for r in res if r[1] == "EXTENDED"), "extended /", len(res))
import json as J
J.dump([dict(sym=r[0], status=r[1], added=r[2], seam_n=r[3], seam_noise=r[4]) for r in res],
       open(f"{ROOT}/campaign/agents/chief/coord/DATA_ETF_MORE/work_r2/results_extend.json", "w"), indent=1)
