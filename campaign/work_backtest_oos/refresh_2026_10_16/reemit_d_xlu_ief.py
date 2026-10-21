#!/usr/bin/env python3
"""ITER62 wave-1 (2026-10-16) #7: re-emit HUNT_SECTOR2 D_xlu_ief on refreshed leaves.

Rebuilds the CANONICAL committed variant "D|lb21|riskoff|IEF" per the exact ARM D
scan recipe (hunt_sector2_r2_scan.py) + harness accounting (weekly_weights ->
net_multi: T+1, 6.4bps FULL |dW|, 0.5%/yr borrow, trailing VT10 clip3), verifies
overlap vs the committed sleeve (tol 1e-12), extends append-only, and records fresh
tail stats in reemit_report.json. Fail-closed on overlap deviation."""
import sys, json
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np
import pandas as pd
import hunt_sector2_r2_harness as H
import hunt_sector2_lib as L

ROOT = "/Users/daxu/software/world-trader"
SLEEVE = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/sleeves/D_xlu_ief.csv"

# ---- book D per scan recipe ----
px = {t: L.etf_close(t) for t in H.S9 + ["IEF"]}
bookD = L.book_rets(H.S9, extra=["IEF"])
bookD = bookD[bookD.index >= H.START]
retsD = bookD[H.S9 + ["IEF"]]

# ---- variant D|lb21|riskoff|IEF per scan ARM D block ----
ratio = np.log(px["XLU"] / px["IEF"]).reindex(bookD.index).ffill()
lb = 21
tr = (ratio - ratio.rolling(lb).mean()) > 0
bad = tr.fillna(False)                    # dirn == "riskoff"
w = pd.DataFrame(0.0, index=bookD.index, columns=H.S9 + ["IEF"])
for t in H.S9:
    w[t] = np.where(~bad, 1 / len(H.S9), 0.0)
w["IEF"] = np.where(bad, 1.0, 0.0)

net = H.net_multi(H.weekly_weights(w), retsD)
s = L.stats(net)
print(f"rebuilt D|lb21|riskoff|IEF: n={s['n']} sr={s['sr']:.3f} ann={s['ann']:.2f}% "
      f"negyr={s['neg_yr']}/{s['n_yr']} worst={s['worst']:.1f}% "
      f"last={net.index.max().date()}")

# ---- overlap vs committed, append-only extend ----
committed = pd.read_csv(SLEEVE, index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([net.rename("c"), committed.rename("m")], axis=1, join="inner").dropna()
dev = float((j.c - j.m).abs().max()) if len(j) else float("nan")
new = net[net.index > committed.index.max()]
rep = {"name": "D_xlu_ief", "variant": "D|lb21|riskoff|IEF",
       "overlap_n": len(j), "overlap_maxdev": dev, "tol": 1e-12,
       "committed_last": str(committed.index.max().date()),
       "new_rows": len(new),
       "new_first": str(new.index.min().date()) if len(new) else None,
       "new_last": str(new.index.max().date()) if len(new) else None}
rep["overlap_ok"] = bool(len(j) and dev <= 1e-12)
if not rep["overlap_ok"]:
    rep["action"] = "SKIPPED - overlap deviation exceeds tolerance"
    print(json.dumps(rep, indent=1))
    sys.exit(1)
if len(new) == 0:
    rep["action"] = "no new rows"
else:
    out = pd.concat([committed, new.rename("ret")])
    out.index.name = "date"
    out.to_frame("ret").to_csv(SLEEVE)
    rep["action"] = f"extended -> {out.index.max().date()} (n={len(out)})"
    rep["fresh_sr"] = round(s["sr"], 3)
    rep["fresh_ann"] = round(s["ann"], 2)
    rep["fresh_negyr"] = s["neg_yr"]
    rep["fresh_nyr"] = s["n_yr"]
    rep["fresh_worst"] = round(s["worst"], 1)

print(json.dumps(rep, indent=1, default=str))

RP = f"{ROOT}/campaign/work_backtest_oos/refresh_2026_10_16/reemit_report.json"
r = json.load(open(RP))
r["D_xlu_ief"] = rep
json.dump(r, open(RP, "w"), indent=1, default=str)
print("updated", RP)
