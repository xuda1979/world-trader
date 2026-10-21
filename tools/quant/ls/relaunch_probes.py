#!/usr/bin/env python3
"""Relaunch the three in-flight probes on the EXACT live winner config.

The winner config is results/live_signal/config.json (h21_n13 @6bps,
refit 4, tw320, mean_var). Probes override a single axis:
  w8y_r2      - refit_freq 2 (even fresher)
  w8y_r4_vix32- refit 4 + VIX>=32/0.3 stress gate
  w10y        - refit 4, window starts 2016-01-01
Usage: python -m tools.quant.ls.relaunch_probes [w8y_r2|w8y_r4_vix32|w10y|all]
"""
from __future__ import annotations
import os, sys, json, time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.quant.ls.config import Config
from tools.quant.ls.runner import run

PROBES = {
    # w8y_r2 (refit 2) dropped 2026-08-12: 190 min for a marginal question;
    # deployed cadence is r4. Re-add if desired: {"refit_freq": 2},
    # vix32 DONE 2026-08-12: FAIL (SR -0.173, DD -39%, OOS IC -0.0035) - 20y + VIX gate dead.
    # "w8y_r4_vix32": {"refit_freq": 4, "vix_level_threshold": 32, "vix_level_factor": 0.3},
    # RE-VALIDATION on the CURRENT 20y-extended panel: the twelvedata CSVs
    # now span 2006-2026 (extended ~08-11/12); the trailing IC screen now
    # keeps only vol_60d (was mom_12m+mom_12_1m+vol_60d on the 8y-era
    # panel). Question: does the deployed winner config still deliver on
    # today's data with an 8y backtest window (start 2018)?
    "w8y_reval": {"refit_freq": 4, "start_date": "2018-01-01"},
    "w10y": {"refit_freq": 4, "start_date": "2016-01-01"},
}

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    base = json.load(open(os.path.join(ROOT, "tools/quant/ls/results/live_signal/config.json")))
    names = list(PROBES) if which == "all" else [which]
    valid = set(Config.__dataclass_fields__)
    base = {k: v for k, v in base.items() if k in valid}
    for name in names:
        t0 = time.time()
        cfg = Config(**{**base, **{"name": name}, **PROBES[name], "diag_window_sweep": ()})
        print(f"### {name}: refit={cfg.refit_freq} start={cfg.start_date} "
              f"vix_th={cfg.vix_level_threshold} (winner base h21 n13 tw{cfg.train_window})")
        res = run(cfg)
        m = res["metrics"]
        print(f"### {name} DONE in {time.time()-t0:.0f}s: "
              f"SR={m['sharpe']:.3f} ret={m['annual_return']*100:+.2f}% "
              f"DD={m['max_drawdown']*100:.2f}% verdict={res['diagnostics'].get('verdict','?')}")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
