"""Daily-panel 252d-horizon XGB cross-check of the 1y signal.

Same walk-forward machinery as xgb_multi_horizon (features6, 285-name
twenty-year daily panel) but the target is the 252-DAY forward return.
Evaluation books the 21-DAY forward return of the selected deciles at
month-ends (monthly rebalance, 24bp/mo) — the monthly 1m-hold scheme on a
DIFFERENT universe/feature set. Leak margin: training rows end 252 days
before the block; TRAIN_WIN=4y so ~2y usable per refit.
"""
from __future__ import annotations
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault("DYLD_LIBRARY_PATH",
    "/Users/daxu/homebrew/opt/libomp/lib:" + os.environ.get("DYLD_LIBRARY_PATH",""))
import numpy as np
import pandas as pd
import xgboost as xgb

from pipeline_common import load_ohlcv
from features6 import build_features6
from features import to_xy

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
os.makedirs(OUT, exist_ok=True)

TRAIN_WIN = int(os.environ.get("TRAIN_WIN", 252*4))
REFIT = 63
COST = 0.0006
START = "2014-01-01"
HORIZONS = [252]
H_BOOK = 21   # book the 21d forward return at month-end selection
K = 10


def XGB_PARAMS():
    return dict(n_estimators=600, learning_rate=0.02, max_depth=3,
                min_child_weight=8, subsample=0.8, colsample_bytree=0.8,
                tree_method="hist", early_stopping_rounds=40, n_jobs=8,
                random_state=42, objective="reg:squarederror",
                eval_metric="rmse")


def build_frame():
    P = load_ohlcv(); close = P["close"]
    feats = build_features6(P)
    ret_next = close.pct_change().shift(-1)
    X_full, _, _, meta, names = to_xy(feats, ret_next)
    X_full = X_full.replace([np.inf, -np.inf], np.nan)
    dates = pd.to_datetime(meta["date"].to_numpy())
    tickers = meta["ticker"].to_numpy()
    frame = pd.DataFrame({"date": dates, "ticker": tickers}).set_index(["date", "ticker"])
    close_long = close.stack().rename("close")
    close_long.index.names = ["date", "ticker"]
    base = close_long.reindex(frame.index)
    frame["close"] = base.to_numpy()
    for H in set(HORIZONS + [H_BOOK]):
        fut = close.shift(-H).stack().rename(f"ret_{H}")
        fut.index.names = ["date", "ticker"]
        r = fut.reindex(frame.index) / base - 1.0
        frame[f"ret_{H}"] = r.to_numpy()
    frame = frame.reset_index()
    return X_full, frame, names


def walkforward_predict(X_full, frame, names):
    dates = frame["date"].to_numpy(); tickers = frame["ticker"].to_numpy()
    ud = np.unique(dates); start = pd.Timestamp(START)
    pd_ = ud[ud >= np.datetime64(start)]
    refit = np.arange(0, len(pd_), REFIT)
    print(f"OOS {pd.Timestamp(pd_[0]).date()}..{pd.Timestamp(pd_[-1]).date()} "
          f"| {len(refit)} refits | {len(names)} feats", flush=True)
    Xn = X_full.to_numpy()
    fin = np.isfinite(Xn)
    preds = {H: np.full(len(frame), np.nan) for H in HORIZONS}
    retcols = {H: frame["ret_%d" % H].to_numpy() for H in HORIZONS}
    t0 = time.time()
    for k, kk in enumerate(refit):
        if k % 10 == 0:
            print(f"  refit {k+1}/{len(refit)} @ {pd.Timestamp(pd_[kk]).date()} ({time.time()-t0:.0f}s)", flush=True)
        d = pd_[kk]; dmin = d - np.timedelta64(TRAIN_WIN, "D")
        max_h = max(HORIZONS)
        tr = (dates < d) & (dates >= dmin) & (dates < d - np.timedelta64(max_h, "D"))
        tr_idx = np.where(tr)[0]
        fok = fin[tr_idx].sum(axis=1) > 0
        tr_idx = tr_idx[fok]
        np.random.seed(42); np.random.shuffle(tr_idx)
        nv = max(int(len(tr_idx)*0.1), 1000); nv = min(nv, len(tr_idx)//4)
        val_idx, tr2 = tr_idx[:nv], tr_idx[nv:]
        Xtr2 = Xn[tr2]
        d_end = pd_[kk+REFIT] if kk+REFIT < len(pd_) else pd_[-1]+np.timedelta64(1, "D")
        blk = (dates >= d) & (dates < d_end)
        blk_idx = np.where(blk)[0]
        bob = fin[blk_idx].sum(axis=1) > 0
        bb = blk_idx[bob]
        if len(bb) == 0:
            continue
        for H in HORIZONS:
            ytr = retcols[H][tr2]; yv = retcols[H][val_idx]
            ok_t = np.isfinite(ytr)
            ok_v = np.isfinite(yv)
            if ok_t.sum() < 500 or ok_v.sum() < 200:
                continue
            m = xgb.XGBRegressor(**XGB_PARAMS())
            m.fit(Xtr2[ok_t], ytr[ok_t],
                  eval_set=[(Xn[val_idx][ok_v], yv[ok_v])], verbose=False)
            pb = np.full(len(blk_idx), np.nan)
            pb[bob] = m.predict(Xn[bb])
            preds[H][blk_idx] = pb
    return preds


def monthly_ls(frame, pred):
    """Month-end selection by the 252d prediction, book the 21d forward
    return of top/bottom decile, net 24bp full cycle."""
    fw = frame.copy()
    fw["pred"] = pred
    fw["fwd"] = fw["ret_%d" % H_BOOK]
    fw = fw[np.isfinite(fw["pred"]) & np.isfinite(fw["fwd"])]
    fw["month"] = fw["date"].dt.to_period("M")
    rows = []
    for m, g in fw.groupby("month"):
        g = g[g["date"] == g["date"].max()]   # last trading day of the month
        n = len(g)
        if n < 2*K+2: continue
        g = g.sort_values("pred", ascending=False)
        rows.append((m, g["fwd"].iloc[:K].mean() - g["fwd"].iloc[-K:].mean() - 4*COST))
    return pd.Series(dict(rows)).sort_index()


def stats(full):
    full = full.dropna()
    if len(full) < 20 or full.std() == 0:
        return {"sr": None, "ann": None, "dd": None}
    eq = (1+full).cumprod()
    sr = (full.mean()/full.std())*np.sqrt(12)
    ann = (1+full).prod()**(12/len(full))-1
    dd = (eq/eq.cummax()-1).min()
    return {"sr": round(float(sr),3), "ann": round(float(ann),4),
            "dd": round(float(dd),4), "win": round(float((full>0).mean()),3)}


def main():
    print("Building feature matrix + 252d target...", flush=True)
    X_full, frame, names = build_frame()
    print(f"frame {frame.shape} | X {X_full.shape}", flush=True)
    preds = walkforward_predict(X_full, frame, names)
    s = monthly_ls(frame, preds[252])
    print(f"monthly rebalance L/S on 252d pred: {stats(s)}", flush=True)
    s.to_frame("daily1y").to_csv(os.path.join(OUT, "daily_1y_monthly.csv"))
    json.dump({k: stats(v) for k, v in [("ls", s)]},
              open(os.path.join(OUT, "daily_1y_results.json"), "w"), indent=1)
    print("saved daily_1y results", flush=True)


if __name__ == "__main__":
    main()
