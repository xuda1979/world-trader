"""check_champion_health.py -- monitor the ONLY scramble-validated leg.

For the recurring research/portfolio loop: on each fire, report the equity L/S
champion's honest OOS health so the loop does NOT re-run dead-end portfoliio
construction. Reports:
  1. full run OOS Sharpe (live_signal)
  2. recent fwd_validate IC trend (is the edge decaying into 2026?)
  3. scramble-validation status reminder
  4. gate: is it safe to keep allocating / is a regime warning active?
"""
import pandas as pd, numpy as np, os, json

def loader(p, col="daily_return"):
    d = pd.read_csv(p, index_col=0, parse_dates=True)[col]
    return d

def main():
    live = loader("results/live_signal/daily_returns.csv")
    sr = live.mean() / live.std() * np.sqrt(252)
    print(f"LS_GBRT full-run OOS (n={len(live)}): Sharpe={sr:.2f} "
          f"ann_ret={(1+live).prod()**(252/len(live))-1:.2%} "
          f"last={live.index[-1].date()}")
    # recent IC from honest fwd_validate
    icp = "results/live_signal/fwd_validate/ic_series.csv"
    if os.path.exists(icp):
        ic = pd.read_csv(icp, index_col=0, parse_dates=True)
        # last 5 factor ICs averaged per date (cross-factor mean of non-null)
        m = ic.mean(axis=1).dropna()
        recent = m.tail(6)
        print("\nRecent OOS factor-IC (mean across factors, last 6):")
        for dt, v in recent.items():
            print(f"  {dt.date()}  {v:+.3f}")
        print(f"  -> mean last-6 IC = {recent.mean():+.3f}  "
              f"(negative = edge decaying/regime adverse)")
    # Risk flag: is the validated edge currently healthy?
    if icp and os.path.exists(icp):
        ic = pd.read_csv(icp, index_col=0, parse_dates=True)
        m = ic.mean(axis=1).dropna()
        last6 = m.tail(6).mean()
        if last6 < -0.05:
            print(f"\n[RISK] recent OOS factor-IC (mean last6={last6:+.3f}) is "
                  "degrading/negative -> champion edge currently weak in this "
                  "regime. De-risk: reduce allocation, hold flat, revisit. "
                  "Do NOT size up on the 0.79 long-run average.")
        elif last6 < 0.03:
            print(f"\n[CAUTION] recent factor-IC ({last6:+.3f}) is flat/low -> "
                  "edge not currently contributing.")
        else:
            print(f"\n[OK] recent factor-IC ({last6:+.3f}) positive -> edge intact.")
    print("\nVALIDATION GATE: only LS_GBRT passes price-lag scramble. "
          "tsmom/gold/fx/pairs all FAIL (see VALIDATION_STATUS.md).")
    print("No validated multi-leg high-Sharpe book exists yet.")

if __name__ == "__main__":
    main()
