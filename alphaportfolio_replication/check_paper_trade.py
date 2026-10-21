#!/usr/bin/env python3
"""PAPER-TRADE CHECKER: match recorded live signals against realized returns.

For each signal in data/live_champion_history.csv, the realized month is
the champion's net return in the month AFTER the signal date (T+1
execution, same as the backtest). Reads the champion's monthly net
series (data/wf_final.csv or a fresh run) and reports PASS/FAIL per
signal month plus cumulative stats.

Usage:
  python3 check_paper_trade.py              # vs existing wf_final.csv
  python3 check_paper_trade.py --fresh      # re-run the champion backtest first
"""
from __future__ import annotations
import os, sys
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    fresh = "--fresh" in sys.argv
    hist_p = os.path.join(HERE, "data", "live_champion_history.csv")
    if not os.path.exists(hist_p):
        print("no history yet — run run_live_champion.py first"); return 1
    hist = pd.read_csv(hist_p)
    if fresh:
        import subprocess
        subprocess.run([sys.executable, os.path.join(HERE, "run_champion_fund_tilt.py")],
                       env={**os.environ, "REV_SLEEVE": "0.0", "TILT_W": "0.10",
                            "VOL_TARGET": "0.10", "TILT_MODE": "vq", "GOLD_W": "0.20",
                            "GATE_LB": "13", "VIX_F1": "1", "VIX_F2": "1", "VIX_F3": "1",
                            "MOM_LB": "6 12 24", "G_DIV": "6", "VOL_CAP": "1.2",
                            "OUT_CSV": "wf_final.csv"}, check=True)
    champ = pd.read_csv(os.path.join(HERE, "data", "wf_final.csv"))
    champ["ym"] = pd.to_datetime(champ["ym"] + "-01") + pd.offsets.MonthEnd(0)  # month-end index
    champ = champ.sort_values("ym").set_index("ym")["net"]

    rows = []
    for _, s in hist.iterrows():
        sig_m = pd.Timestamp(s["as_of"])  # signal month (month-end)
        # realized month = month AFTER the signal (fwd return held from sig date)
        realized_m = (sig_m + pd.DateOffset(months=1)).to_period("M").to_timestamp() + pd.offsets.MonthEnd(0)
        if realized_m in champ.index:
            r = float(champ.loc[realized_m])
            rows.append({"signal": s["as_of"], "gate": s["gate"], "n_held": s["n_held"],
                         "realized_month": realized_m.strftime("%Y-%m"),
                         "realized_ret": r, "pass": r > 0})
        else:
            rows.append({"signal": s["as_of"], "gate": s["gate"], "n_held": s["n_held"],
                         "realized_month": realized_m.strftime("%Y-%m"),
                         "realized_ret": np.nan, "pass": None})
    out = pd.DataFrame(rows)
    print("PAPER-TRADE CHECK (champion composite, net):")
    for _, r in out.iterrows():
        if r["pass"] is None:
            print(f"  {r['signal']}: {r['realized_month']} PENDING (data not landed)")
        else:
            mark = "PASS" if r["pass"] else "FAIL"
            print(f"  {r['signal']}: {r['realized_month']} {r['realized_ret']*100:+.2f}% [{mark}]")
    done = out[out["pass"].notna()]
    if len(done):
        print(f"\n  {len(done)} realized signal-month(s): "
              f"{done['pass'].sum()} PASS / {len(done)-done['pass'].sum()} FAIL; "
              f"mean {done['realized_ret'].mean()*100:+.2f}%/mo")
    return 0

if __name__ == "__main__":
    sys.exit(main())
