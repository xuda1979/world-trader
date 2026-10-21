#!/usr/bin/env python3
"""DATA_FREDMORE round-1: fetch genuinely-new FRED series via existing fred_dl.fetch.
Fail-closed lint per fred_dl.lint; only PASS written to more_fred/{id}.csv."""
import sys, os, json
ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/tools/quant/data/more_fred")
import fred_dl

def key():
    for line in open(f"{ROOT}/.env.local"):
        if line.startswith("FRED_KEY"):
            return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("no FRED_KEY")

# (series_id, freq hint for lint) — genuinely NEW vs the 94 present (checked against dir listing)
SERIES = [
    ("VIXCLS",        "daily"),   # equity vol index (only OVX/GVZ/VXV present)
    ("T10Y2Y",        "daily"),   # 2s10s curve spread for HUNT_CREDIT2
    ("T5YIFR",        "daily"),   # 5y5y fwd inflation expectation
    ("DGS2",          "daily"),   # 2y CMT (curve construction)
    ("DGS10",         "daily"),   # 10y CMT
    ("DGS30",         "daily"),   # 30y CMT
    ("NROU",          "quarterly"),# natural rate of unemployment (charter labor)
    ("LNS11300060",   "monthly"), # labor force participation 16-24 (charter)
    ("AWHAETP",       "monthly"), # avg weekly hours production (charter)
    ("CSUSHPISA",     "monthly"), # S&P/CS house price idx (charter leading)
    ("TOTALSL",       "monthly"), # total consumer credit (charter credit)
    ("IRLTLT01NZM156N","monthly"),# NZ long rate -> FX carry NZD leg
    ("IPMAN",         "monthly"), # manufacturing output (activity nowcast)
    ("DGORDER",       "monthly"), # durable goods orders (leading)
    ("USREC",         "monthly"), # NBER recession flag (regime labels)
    ("CPILFESL",      "monthly"), # core CPI (inflation-regime)
    ("HSN1F",         "monthly"), # new home sales (leading)
]
out = []
for sid, freq in SERIES:
    (rows, _nmiss), err = fred_dl.fetch(sid, key())
    if err:
        out.append((sid, freq, "FETCH_FAIL", err, 0, "", ""))
        continue
    lint = fred_dl.lint(rows, freq=freq)
    status = "PASS" if lint["pass"] else f"FAIL({lint['reason']})"
    if lint["pass"]:
        path = f"{ROOT}/tools/quant/data/more_fred/{sid}.csv"
        with open(path, "w") as f:
            fred_dl.write_csv(f, rows, sid)
    out.append((sid, freq, status, lint["reason"], lint["n"], lint["start"], lint["end"]))

print(f"{'series':<18}{'freq':<11}{'status':<34}{'n':>7}  start-end")
for r in out:
    print(f"{r[0]:<18}{r[1]:<11}{r[2]:<34}{r[4]:>7}  {r[5]}..{r[6]}")
npass = sum(1 for r in out if r[2] == "PASS")
print(f"\nTOTAL {len(out)} attempted, {npass} PASS, {len(out)-npass} FAIL")
