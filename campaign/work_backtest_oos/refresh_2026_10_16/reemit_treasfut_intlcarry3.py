#!/usr/bin/env python3
"""ITER62 wave-1 (2026-10-16) #6: extend IRLTLT01{DEM,CAM,JPM,USM}156N leaves to
2026-09 (FRED API publishes Sep-2026) then re-emit TREASFUT_intlcarry3_lag1_NEG.

Steps (all fail-closed):
1. FRED API pull of the 4 IRLTLT01 series (api.stlouisfed.org; fredgraph.csv down today).
   Overlap vs on-disk more_fred CSVs must be EXACT (dot-rows dropped, values match).
   Append-only extend of leaves. Snapshot pre-state.
2. Rebuild the committed variant via the CANONICAL builder path:
   run_intl_carry(lag_m=1) + net_intl(lag_m=1) from HUNT_TREASFUT_round1 (imported, not
   re-typed), overlap vs committed sleeve (tol 1e-12), append-only extend.
"""
import json, os, shutil, sys, urllib.request
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
WORK = f"{ROOT}/campaign/work_backtest_oos/refresh_2026_10_16"
FREDDIR = f"{ROOT}/tools/quant/data/more_fred"
SLEEVE = f"{ROOT}/campaign/agents/chief/coord/HUNT_TREASFUT/sleeves/TREASFUT_intlcarry3_lag1_NEG.csv"
SERIES = ["IRLTLT01DEM156N", "IRLTLT01CAM156N", "IRLTLT01JPM156N", "IRLTLT01USM156N"]

key = None
for line in open(f"{ROOT}/.env.local"):
    if line.strip().startswith("FRED_KEY"):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
if not key:
    print("FATAL: FRED_KEY not found"); sys.exit(1)

def fetch_obs(sid):
    url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
           f"&api_key={key}&file_type=json&observation_start=1980-01-01&sort_order=asc")
    with urllib.request.urlopen(url, timeout=30) as r:
        d = json.loads(r.read().decode())
    rows = []
    for o in d["observations"]:
        v = o["value"]
        if v == "." or v == "":
            continue
        rows.append((o["date"], float(v)))
    s = pd.Series(dict(rows), name=sid)
    s.index = pd.to_datetime(s.index)
    return s.sort_index()

# ---- 1. leaf extension ----
report = {}
snapdir = os.path.join(WORK, "fred_leaf_snapshot_pre")
os.makedirs(snapdir, exist_ok=True)
for sid in SERIES:
    path = f"{FREDDIR}/{sid}.csv"
    disk = pd.read_csv(path, index_col=0, parse_dates=True)["value"].astype(float)
    disk.index = pd.to_datetime(disk.index)
    api = fetch_obs(sid)
    j = pd.concat([api.rename("a"), disk.rename("d")], axis=1, join="inner").dropna()
    dev = float((j.a - j.d).abs().max()) if len(j) else float("nan")
    new = api[api.index > disk.index.max()]
    rep = {"overlap_n": len(j), "overlap_maxdev": dev,
           "committed_last": str(disk.index.max().date()),
           "new_rows": len(new)}
    if len(j) == 0 or dev > 1e-9:
        rep["action"] = "SKIPPED - overlap deviation"
        report[sid] = rep
        print(sid, rep); sys.exit(1)
    if len(new) == 0:
        rep["action"] = "no new rows"
        report[sid] = rep
        print(sid, rep); continue
    shutil.copy2(path, os.path.join(snapdir, f"{sid}.csv"))
    out = pd.concat([disk.rename("value"), new.rename("value")])
    out.index.name = "date"
    out.to_frame("value").to_csv(path)
    rep.update({"action": f"extended -> {out.index.max().date()} (n={len(out)})",
                "new_first": str(new.index.min().date()),
                "new_last": str(new.index.max().date())})
    report[sid] = rep
    print(sid, rep["action"])

# ---- 2. rebuild committed variant via canonical builder ----
sys.path.insert(0, f"{ROOT}/campaign/scripts")
import HUNT_TREASFUT_round1 as T1

comb2, nets_d2 = T1.net_intl(lag_m=1)
comb2 = comb2.rename("ret")
print(f"rebuilt intlcarry3_lag1: n={len(comb2)} last={comb2.index.max().date()}")

committed = pd.read_csv(SLEEVE, index_col=0, parse_dates=True).iloc[:, 0]
committed.index = pd.to_datetime(committed.index)
j = pd.concat([comb2.rename("c"), committed.rename("m")], axis=1, join="inner").dropna()
dev = float((j.c - j.m).abs().max()) if len(j) else float("nan")
new = comb2[comb2.index > committed.index.max()]
rep = {"name": "TREASFUT_intlcarry3_lag1_NEG",
       "overlap_n": len(j), "overlap_maxdev": dev, "tol": 1e-12,
       "committed_last": str(committed.index.max().date()),
       "new_rows": len(new),
       "new_first": str(new.index.min().date()) if len(new) else None,
       "new_last": str(new.index.max().date()) if len(new) else None}
print(f"overlap n={len(j)} maxdev={dev:.3e} new_rows={len(new)}")
if len(j) == 0 or dev > 1e-12:
    rep["action"] = "SKIPPED - sleeve overlap deviation"
    print(json.dumps(rep, indent=1, default=str)); sys.exit(1)
if len(new) > 0:
    out = pd.concat([committed.rename("ret"), new.rename("ret")])
    out.index.name = "date"
    out.to_frame("ret").to_csv(SLEEVE)
    rep["action"] = f"extended -> {out.index.max().date()} (n={len(out)})"
else:
    rep["action"] = "no new rows"
print(json.dumps(rep, indent=1, default=str))

RP = f"{WORK}/reemit_report.json"
r = json.load(open(RP))
r["TREASFUT_intlcarry3_lag1_NEG"] = {"leaves": report, "sleeve": rep}
json.dump(r, open(RP, "w"), indent=1, default=str)
print("updated", RP)
