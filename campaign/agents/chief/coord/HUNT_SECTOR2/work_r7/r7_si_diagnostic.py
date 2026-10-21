#!/usr/bin/env python3
"""R7 (a) DIAGNOSTIC LEG -- sector short-ratio tilt on the on-disk Reg SHO vintage.

STATUS: UNJUDGEABLE BY CONSTRUCTION (GATES_CONTRACT_V2 9b: materially-short span).
The vintage gives 8 contiguous monthly observations (2024-01..2024-08) per SPDR.
Nothing here is a gate, a submission, or evidence of edge. It is reported so the
admission verdict is accompanied by what the data would have said, clearly labeled.

Vintage: tools/quant/bigmove/data/finra_short_ratio_monthly.parquet
  built by tools/quant/bigmove/finra_shortint_build.py from FINRA Reg SHO daily
  files (cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt, 181 files
  cached on disk 2019-01..2024-08 disjoint windows).
  short_ratio(m, tkr) = sum(short_vol)/sum(total_vol) over month m -- PIT-safe by
  construction (uses only data through month-end m; consumed for month m+1).

Signal (one pre-registered spec, no tuning): cross-sectional z of short_ratio
level at month m -> long bottom-3 (low SI), short top-3 (high SI) at equal weight,
held month m+1. T+1 via lib.t1 semantics at monthly frequency; 6.4bps on |dW|.
Inverse-sign variant reported as the SAME spec mirrored (not a second idea).

Run: python3 work_r7/r7_si_diagnostic.py
"""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = os.path.join(ROOT, "campaign/agents/chief/coord/HUNT_SECTOR2")
OUT = os.path.join(HERE, "work_r7", "r7_si_diagnostic.json")
sys.path.insert(0, os.path.join(ROOT, "campaign/scripts"))
import hunt_sector2_lib as L  # noqa: E402

PQ = os.path.join(ROOT, "tools/quant/bigmove/data/finra_short_ratio_monthly.parquet")
SPDRS = L.SECTORS


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main():
    df = pd.read_parquet(PQ)
    piv = (df[df["ticker"].isin(SPDRS)]
           .pivot(index="month", columns="ticker", values="short_ratio")
           .sort_index())
    # contiguous run containing the last month
    months = piv.index
    run = [months[-1]]
    for m in months[::-1][1:]:
        if (run[0] - m).days <= 31:
            run.insert(0, m)
        else:
            break
    piv8 = piv.loc[run]
    n_months, n_names = piv8.shape

    # monthly signal at month m (row) from that row's cross-section
    z = piv8.sub(piv8.mean(axis=1), axis=0).div(piv8.std(axis=1, ddof=0), axis=0)

    # build monthly portfolio returns: at each month m (signal), hold m+1 returns
    closes = pd.DataFrame({t: L.etf_close(t) for t in SPDRS}).sort_index()
    mret = closes.resample("ME").last().pct_change()  # calendar month returns
    # align month-END stamps to the parquet's month-START stamps
    mret.index = mret.index.to_period("M").to_timestamp()
    mret = mret[mret.index.isin(z.index)]

    rows = []
    for i in range(len(z) - 1):
        sig_m, hold_m = z.index[i], z.index[i + 1]
        if hold_m not in mret.index:
            continue
        zr = z.loc[sig_m].dropna()
        if len(zr) < n_names:
            continue
        longs = list(zr.nsmallest(3).index)   # low SI
        shorts = list(zr.nlargest(3).index)   # high SI
        w = pd.Series(0.0, index=SPDRS)
        w[longs] = +1.0 / 3
        w[shorts] = -1.0 / 3
        r = mret.loc[hold_m]
        gross = float((w * r).sum())
        rows.append({"signal_month": str(sig_m.date()), "hold_month": str(hold_m.date()),
                     "longs": ",".join(longs), "shorts": ",".join(shorts),
                     "gross": gross})
    book = pd.DataFrame(rows)
    if book.empty:
        res = {"status": "NO_EVALUABLE_MONTHS", "n_months_panel": int(n_months)}
    else:
        r = book.set_index("hold_month")["gross"]
        # costs: monthly rebalance of a 6-name basket; |dW| between consecutive books
        to = r.index.to_series().map(
            {hold: 1.0 for hold in r.index}).astype(float)
        w_series = []
        prev_w = pd.Series(0.0, index=SPDRS)
        for _, row in book.iterrows():
            w = pd.Series(0.0, index=SPDRS)
            for t in row["longs"].split(","):
                w[t] += 1 / 3
            for t in row["shorts"].split(","):
                w[t] -= 1 / 3
            w_series.append((row["hold_month"], float(w.sub(prev_w).abs().sum())))
            prev_w = w
        cost = pd.Series(dict(w_series)) * L.COST / 1e4
        net = r - cost.reindex(r.index).fillna(0.0)
        n = len(net)
        sr = float(net.mean() / net.std(ddof=1) * np.sqrt(12)) if n > 2 and net.std() > 0 else None
        cc = L.corr_champ(net) if n >= 12 else None  # meaningless at n=8; still report
        mirrored = -net
        res = {
            "status": "DIAGNOSTIC_UNJUDGEABLE",
            "vintage": {"path": PQ, "sha256_16": sha16(PQ),
                        "panel_rows_all": int(len(df)),
                        "months_panel": [str(m.date()) for m in months],
                        "contiguous_run": [str(m.date()) for m in run]},
            "spec": "z(short_ratio level) cross-section at month m -> long bottom-3 / short top-3, hold m+1, monthly, T+1, 6.4bps full-|dW|, no vol-target (monthly freq)",
            "n_hold_months": n,
            "mean_monthly_gross_pct": round(float(r.mean()) * 100, 4),
            "mean_monthly_net_pct": round(float(net.mean()) * 100, 4),
            "ann_pct_net": round(float(net.mean()) * 12 * 100, 2),
            "sr_net_annualized": round(sr, 3) if sr is not None else None,
            "hit_rate": round(float((net > 0).mean()), 3),
            "corr_champion_n8_meaningless": cc,
            "mirrored_sign_net_ann_pct": round(float(mirrored.mean()) * 12 * 100, 2),
            "per_month": book.assign(net=(net.values * 100).round(3)).to_dict("records"),
        }
    res["VERDICT"] = ("NOT EVIDENCE OF ANYTHING: %d monthly observations is a "
                      "materially-short span (V2 9b) -- unjudgeable, non-gate. "
                      "Reported only alongside the 0/6 admission verdict."
                      % res.get("n_hold_months", res.get("n_months_panel", 0)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != "per_month"}, indent=1))
    print("... written:", OUT)


if __name__ == "__main__":
    main()
