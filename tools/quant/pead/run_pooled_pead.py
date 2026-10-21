"""Run the repo's pooled cross-sectional PEAD backtest on the available price panels.

PEAD is a CROSS-SECTIONAL effect: the edge lives across many earnings-gap events,
not within one name. analysis.backtest_pead_pooled() already implements the correct,
cost-aware, OOS-split pooled backtest (Bernard/Thomas method). Our job here is to
FEED it the largest price universe the free panels allow and report the live t-stat.

This is the honest validation path: unlike a per-name backtest (4 events/yr/name ->
underpowered), pooling across ~300+ names gives enough earnings-gap events for a
real t-stat. Limitation acknowledged up front: the free panels are large/liquid
caps (twelve_big/liq) + a thin polygon micro-cap slice ending early -> the small-cap
name where PEAD is strongest are under-represented.
"""
from __future__ import annotations
import sys, os, glob, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))  # tools/
from wt import analysis
import pandas as pd

PANELS = ["twelve_big", "twelve_liq", "twelvedata", "polygon", "polygon_v2"]

def load_panels(max_names=320):
    """Return list of (sym, history_dict) with parallel arrays open/high/low/close/vol."""
    universe = []
    seen = set()
    for panel in PANELS:
        d = os.path.join(os.path.dirname(__file__), "..", "data", panel)
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "*.csv"))):
            sym = os.path.basename(f)[:-4].upper()
            if sym in seen:
                continue
            seen.add(sym)
            try:
                df = pd.read_csv(f).tail(750)  # recent ~3y window: faster AND more relevant
                if len(df) < 80:
                    continue
                h = {
                    "open":  df["open"].tolist(),
                    "high":  df["high"].tolist(),
                    "low":   df["low"].tolist(),
                    "close": df["close"].tolist(),
                    "vol":   df["vol"].tolist(),
                }
                universe.append((sym, h))
            except Exception:
                pass
            if len(universe) >= max_names:
                return universe
    return universe

def main():
    universe = load_panels()
    print(f"loaded {len(universe)} price series from panels")
    out = {}
    for side, horizon in [("Long", 5), ("Short", 5), ("Long", 10), ("Short", 10)]:
        try:
            res = analysis.backtest_pead_pooled(universe, market="US", horizon=horizon,
                                                side=side, min_events=30)
        except Exception as e:
            print(f"{side} h={horizon}: ERROR {e}")
            continue
        if res is None:
            print(f"{side} h={horizon}: too few pooled events (<30)")
            continue
        out[f"{side}_{horizon}d"] = res
        print(f"\n=== PEAD{'up' if side=='Long' else 'dn'} pooled h={horizon} ===")
        print(f"  n={res['n']} exp_ret={res['exp_ret']:.4f} edge={res['edge']:.4f} "
              f"tstat={res['tstat']:.2f} p_win={res['p_win']:.3f}")
        print(f"  OOS: n={res['oos_n']} exp_ret={res['oos_exp_ret']} oos_edge={res['oos_edge']}")
    rdir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(rdir, "pead_pooled.json"), "w") as f:
        json.dump({"n_universe": len(universe), "results": out}, f, indent=2)
    print(f"\nsaved reports/pead_pooled.json")

if __name__ == "__main__":
    main()
