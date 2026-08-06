"""check_champion_health.py -- monitor the ONLY scramble-validated leg.

For the recurring research/portfolio loop: on each fire, report the equity L/S
champion's honest OOS health so the loop does NOT re-run dead-end portfoliio
construction. Reports:
  1. full run OOS Sharpe (live_signal)
  2. recent fwd_validate IC trend (is the edge decaying into 2026?)
  3. scramble-validation status reminder
  4. gate: is it safe to keep allocating / is a regime warning active?
"""
import sys
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
    # FRESH reading: recompute cross-sectional IC from live predictions vs
    # realized returns (fresher than the possibly-stale fwd_validate IC).
    try:
        fr = fresh_ic_from_predictions("results/live_signal/predictions.csv",
                                       "../data/twelvedata", horizon=10)
        if fr:
            print("\nFresh 10d-horizon IC (live preds vs realized, recent):")
            for dt, ic, n in fr[-6:]:
                print(f"  {dt.date()}  IC={ic:+.3f} (n={n})")
            fresh_last6 = np.mean([r[1] for r in fr[-6:]])
            print(f"  -> fresh last-6 mean IC = {fresh_last6:+.3f}")
    except Exception as e:
        print("fresh_ic unavailable:", e)

    # Risk flag -- PREFER the fresh predictions-based IC (most current) when
    # available; fall back to the possibly-stale fwd_validate factor-IC.
    use_fresh = 'fresh_last6' in dir() or 'fresh_last6' in locals()
    eff = locals().get('fresh_last6', None)
    src = "fresh 10d IC"
    if eff is None and icp and os.path.exists(icp):
        ic = pd.read_csv(icp, index_col=0, parse_dates=True)
        m = ic.mean(axis=1).dropna()
        eff = m.tail(6).mean()
        src = "fwd_validate factor-IC"
    if eff is not None:
        if eff < -0.05:
            print(f"\n[RISK] recent edge ({src}, last6={eff:+.3f}) negative -> "
                  "de-risk: reduce allocation / hold flat. Do NOT size up on "
                  "the 0.79 historical average.")
        elif eff < 0.03:
            print(f"\n[CAUTION] recent edge ({src}, last6={eff:+.3f}) neutral/flat "
                  "-> edge not currently contributing strongly; size conservatively.")
        else:
            print(f"\n[OK] recent edge ({src}, last6={eff:+.3f}) positive -> intact.")
    print("\nVALIDATION GATE: only LS_GBRT passes price-lag scramble. "
          "tsmom/gold/fx/pairs all FAIL (see VALIDATION_STATUS.md).")
    print("No validated multi-leg high-Sharpe book exists yet.")


def fresh_ic_from_predictions(pred_path, data_dir, horizon=10, n_recent=6):
    """Compute fresh cross-sectional 10d-horizon IC from live predictions vs
    realized forward returns (fresher than the fwd_validate IC, which can lag)."""
    import glob
    pred = pd.read_csv(pred_path, index_col=0, parse_dates=True).dropna(how='all')
    have = {os.path.basename(f)[:-4] for f in glob.glob(os.path.join(data_dir, "*.csv"))}
    cols = [c for c in pred.columns if c in have]
    px = {c: pd.read_csv(os.path.join(data_dir, f"{c}.csv"), index_col=0,
                         parse_dates=True)['close'].ffill() for c in cols}
    P = pd.DataFrame(px)
    fwd = P.shift(-horizon) / P - 1.0
    recent = pred.index[pred.index >= pred.index[-1] - pd.Timedelta(days=n_recent*30)]
    out = []
    for dt in recent:
        m = pd.concat([pred.loc[dt, cols], fwd.loc[dt, cols]], axis=1).dropna()
        if len(m) < 15:
            continue
        from scipy.stats import spearmanr
        ic, _ = spearmanr(m.iloc[:, 0], m.iloc[:, 1])
        out.append((dt, ic, len(m)))
    return out


if __name__ == "__main__":
    sys.exit(main())
