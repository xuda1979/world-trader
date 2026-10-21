#!/usr/bin/env python3
"""Round-2 (b) applied dir-wide: recover vendor-hidden pre-2008 depth for EVERY on-disk
more_etf series still capped by the 5000-row truncation (EWT precedent, R1: 'OK+EXTEND').
Same stitch as extend_heads.py: head window 1995-01-01..2012-12-31 onto existing tail,
head wins at seam. Fail-closed re-lint (start<=2007-01-01, n>=250, maxgap<=10d,
|ret|>50% on <=3d, end>=2026-06) PLUS a seam-noise gate: if head/tail closes disagree
on the overlap by >0.5% of price level, DO NOT write (adjustment-basis mismatch).
Overwrite only on (PASS && added>0 && seam ok). Results -> results_extend_all.json."""
import os, json, time, urllib.request
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = f"{ROOT}/tools/quant/data/more_etf"
START_BOUND = pd.Timestamp("2007-01-01")
FRESH = pd.Timestamp("2026-06-01")
SKIP = {"manifest.csv"}

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

# already extended this round (results_extend.json) — skip to save API calls
already = {d["sym"] for d in json.load(open(f"{ROOT}/campaign/agents/chief/coord/DATA_ETF_MORE/work_r2/results_extend.json"))}

res = []
for fn in sorted(os.listdir(OUT)):
    if fn in SKIP or not fn.endswith(".csv"):
        continue
    sym = fn[:-4]
    if sym in already:
        print(f"{sym:<5} SKIP (already extended this round)", flush=True)
        res.append(dict(sym=sym, status="SKIP")); continue
    old = pd.read_csv(f"{OUT}/{fn}")
    old["date"] = pd.to_datetime(old["date"]); old["close"] = old["close"].astype(float)
    cur_start = old["date"].min()
    if cur_start <= pd.Timestamp("1998-01-01"):
        res.append(dict(sym=sym, status="SKIP(start<=1998)")); continue

    try:
        js = fetch(sym)
    except Exception as e:
        print(f"{sym:<5} FETCH_FAIL {repr(e)[:70]}", flush=True)
        res.append(dict(sym=sym, status="FETCH_FAIL", detail=repr(e)[:90])); continue
    if js.get("status") == "error" or "values" not in js:
        print(f"{sym:<5} API_ERR {str(js.get('message', js))[:70]}", flush=True)
        res.append(dict(sym=sym, status="API_ERR", detail=str(js.get("message", js))[:90])); continue

    h = pd.DataFrame(js["values"]).rename(columns={"datetime": "date"})
    h["date"] = pd.to_datetime(h["date"]); h["close"] = h["close"].astype(float)
    h = h.sort_values("date").reset_index(drop=True)

    oldi = old.set_index("date")
    seam = h[h["date"].isin(oldi.index)]
    med = float(old["close"].median())
    noise = float(np.abs(seam["close"].values - oldi.loc[seam["date"], "close"].values).max()) if len(seam) else 0.0
    seam_rel = noise / med if med > 0 else 1.0

    both = pd.concat([h, old]).drop_duplicates(subset="date", keep="first").sort_values("date").reset_index(drop=True)
    added = len(both) - len(old)

    s = both.set_index("date")["close"].sort_index(); s = s[s > 0]
    gaps = s.index.to_series().diff().dt.days.dropna(); mg = int(gaps.max())
    jr = int((s.pct_change().abs() > 0.5).sum())
    dup = int(s.index.duplicated().sum())
    ok = (s.index[0] <= START_BOUND and mg <= 10 and jr <= 3 and dup == 0
          and len(s) >= 250 and s.index[-1] >= FRESH)

    if ok and added > 0 and seam_rel <= 0.005:
        o = both.copy(); o["date"] = o["date"].dt.strftime("%Y-%m-%d")
        o[["date", "close"]].to_csv(f"{OUT}/{fn}", index=False)
        st = "EXTENDED"
    elif not ok:
        st = f"FAIL(start={s.index[0].date()},gap={mg},jumps={jr})" if s.index[0] > START_BOUND else f"FAIL(gap={mg},jumps={jr},dup={dup})"
    elif seam_rel > 0.005:
        st = f"NO_WRITE(seam_rel={seam_rel:.4f})"
    else:
        st = "NO_GAIN"

    print(f"{sym:<5} {st:<42} cur_start={cur_start.date()} -> new_start={s.index[0].date()} +{added} rows, seam_rel={seam_rel:.5f}", flush=True)
    res.append(dict(sym=sym, status=st, cur_start=str(cur_start.date()),
                    new_start=str(s.index[0].date()), added=int(added),
                    seam_rel=f"{seam_rel:.5f}", maxgap=mg, jumps=jr))

json.dump(res, open(f"{ROOT}/campaign/agents/chief/coord/DATA_ETF_MORE/work_r2/results_extend_all.json", "w"), indent=1, default=str)
n_ext = sum(1 for r in res if r["status"] == "EXTENDED")
n_fail = sum(1 for r in res if r["status"].startswith("FAIL"))
print(f"\nSUMMARY: {len(res)} considered, {n_ext} EXTENDED, {n_fail} still FAIL, {sum(1 for r in res if r['status']=='NO_GAIN')} NO_GAIN")
