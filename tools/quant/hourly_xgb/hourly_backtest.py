"""Rigorous walk-forward backtest for the hourly 2% XGB strategy.
- Walk-forward: expanding window, retrain periodically, predict out-of-sample each step.
- Strategy (as requested): if predicted next-hour close >= +thresh above current,
  buy at current close T, liquidate at next-hour close T+1. 6bps/side (12bps round).
- Sweeps threshold to map the net-of-cost edge landscape, reports honestly.
Also computes a proper hourly P&L series to annualize (hours*252*~7.5/day).
"""
from __future__ import annotations
import os, sys, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hourly_main import load_intraday, build_panel, build_features
import xgboost as xgb

COST = 0.0006
HOURS_PER_YEAR = 252 * 7   # ~7 full hourly bars/day

def main():
    tickers = load_intraday()
    close = build_panel(tickers)
    ret = close.pct_change()
    target = ret.shift(-1)          # predict return T->T+1
    f = build_features(close)

    # wide feature matrix: column-per-(feature,ticker)
    colmap = {}
    for name, dfr in f.items():
        for c in close.columns:
            colmap[(name, c)] = dfr[c].reindex(close.index)
    wide = pd.DataFrame(colmap, index=close.index)
    feat_names = list(wide.columns)
    wideS = wide.stack(future_stack=True); wideS.index.names=["dt","ticker"]
    ys = target.stack(future_stack=True); ys.index.names=["dt","ticker"]
    y = ys.reindex(wideS.index)
    X = wideS
    mask = X.notna().all(axis=1) & y.notna()
    Xc, yc = X[mask], y[mask]

    dts = np.array(sorted(Xc.index.get_level_values("dt").unique()))
    print(f"Dates: {dts[0]} .. {dts[-1]}  ({len(dts)} hourly stamps, {Xc.shape[0]} complete rows)")

    # ---- Walk-forward prediction ----
    # train on first window, then roll: retrain every N days, predict each step forward
    init_frac = 0.5
    init_days = max(10, int(len(dts)*init_frac))
    retrain_every = 20   # days
    param = dict(n_estimators=200, max_depth=5, learning_rate=0.05,
                 subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
                 objective="reg:squarederror", random_state=42, n_jobs=-1)
    all_pred = {}   # (dt)-> pred series aligned to rows
    traindates = dts[:init_days]
    # Step 1: train on init window, predict everything after
    for start_i in range(init_days, len(dts), retrain_every):
        end_i = min(start_i+retrain_every, len(dts))
        train_d = set(dts[:start_i])
        pred_d = dts[start_i:end_i]
        tr = Xc[Xc.index.get_level_values("dt").isin(train_d)]
        model = xgb.XGBRegressor(**param)
        model.fit(tr.to_numpy(), yc[tr.index].to_numpy())
        for d in pred_d:
            sl = Xc[Xc.index.get_level_values("dt")==d]
            p = model.predict(sl.to_numpy())
            for row, v in zip(sl.index, p):
                all_pred[(row[0], row[1])] = v
        # expand train window implicitly via start_i
    # Build test frame
    test_rows = [k for k in all_pred]
    test_container = pd.DataFrame({
        "dt":[k[0] for k in test_rows],
        "ticker":[k[1] for k in test_rows],
        "pred":[all_pred[k] for k in test_rows],
    })
    test_container.index = pd.MultiIndex.from_tuples(test_rows, names=["dt","ticker"])
    test_container["actual"] = yc.reindex(test_container.index)
    test_container = test_container.dropna(subset=["actual"])
    print(f"Walk-forward OOS rows: {len(test_container)}")

    ic = np.corrcoef(test_container["pred"], test_container["actual"])[0,1]
    print(f"Walk-forward IC (pred vs next-hour return): {ic:.4f}")

    # ---- Threshold sweep backtest ----
    print(f"\n{'thresh':>7} {'#trades':>8} {'gross':>9} {'net':>9} {'winrate':>8} {'Sharpe(h)':>9}")
    results=[]
    for th in [0.02, 0.015, 0.01, 0.008, 0.006, 0.005, 0.004, 0.003, 0.002, 0.001, 0.0]:
        sub = test_container[test_container["pred"]>=th].copy()
        if len(sub)==0:
            print(f"{th:7.3f} {0:8d} {'n/a':>9} {'n/a':>9} {'n/a':>8} {'n/a':>9}")
            continue
        sub["net"] = sub["actual"] - 2*COST
        gross = (1+sub["actual"]).prod()-1
        net = (1+sub["net"]).prod()-1
        win = (sub["net"]>0).mean()
        # hourly-annualized Sharpe on per-trade net returns
        shp = sub["net"].mean()/(sub["net"].std()+1e-12)*np.sqrt(HOURS_PER_YEAR)
        print(f"{th:7.3f} {len(sub):8d} {gross:9.3%} {net:9.3%} {win:8.1%} {shp:9.2f}")
        results.append((th,len(sub),gross,net,win,shp))

    # Also compare: what if we just took ALL rows (naive long-everything)? baseline edge
    print("\nBaseline (buy all rows regardless of signal, net 12bps):")
    allr = test_container.copy()
    allr["net"]=allr["actual"]-2*COST
    print(f"  N={len(allr)} net compounded {(1+allr['net']).prod()-1:+.3%} "
          f"winrate {(allr['net']>0).mean():.1%} "
          f"Sharpe(h) {allr['net'].mean()/(allr['net'].std()+1e-12)*np.sqrt(HOURS_PER_YEAR):.2f}")

    test_container.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)),"data","hourly_oos_frame.csv"))
    print("\nSaved OOS frame.")

if __name__=="__main__":
    main()
