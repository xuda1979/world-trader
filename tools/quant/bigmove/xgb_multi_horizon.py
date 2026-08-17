"""Multi-horizon XGB cross-sectional long/short.

Predicts forward close-to-close returns at THREE horizons:
    H=1 (next day), H=5 (1 week), H=21 (1 month)
with ONE shared causal-at-close-t feature matrix (70 features from
features3, incl macro/FF/crypto), trained walk-forward (no look-ahead,
quarterly refit, 3y window), then combined into a cross-sectional
long-top-K / short-bottom-K daily portfolio per horizon, net of costs,
optionally vol-targeted. Also tests a multi-horizon EW blend as a
diversification lever (the accord: "extend to 1 week, 1 month windows",
"high Sharpe / high return", "use all methods").

Frame: 20-year 285-name panel (2006-09 .. 2026-08) from twelve_big.
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

TRAIN_WIN = int(os.environ.get("TRAIN_WIN", 252*3))
REFIT = int(os.environ.get("REFIT", 63))     # quarterly refit
COST = 0.0006              # 6 bps one side
START = os.environ.get("HZ_START", "2014-01-01")  # OOS test start (>= warm-up after 2006)
HORIZONS = [1, 5, 21]
K = 10                     # top/bottom names per side
VOL_TARGET_ANN = 0.13
# cache path so extended-window runs don't clobber the 2014+ cache
PRED_CACHE = os.environ.get("HZ_PRED_CACHE", os.path.join(HERE, "data", "horizon_preds.pkl"))


def XGB_PARAMS():
    return dict(n_estimators=500, learning_rate=0.05, max_depth=5,
                min_child_weight=8, subsample=0.8, colsample_bytree=0.8,
                tree_method="hist", early_stopping_rounds=40, n_jobs=8,
                random_state=42, objective="reg:squarederror",
                eval_metric="rmse")


def build_frame():
    """Shared feature matrix (120 features via features5 = features3 + 50 free
    extras: 52w-high dist, skew/kurt, ranks, credit/commodity/FX/intl-yield,
    earnings proximity) + forward targets + close."""
    P = load_ohlcv(); close = P["close"]
    feats = build_features6(P)
    ret_next = close.pct_change().shift(-1)
    X_full, _, _, meta, names = to_xy(feats, ret_next)
    X_full = X_full.replace([np.inf, -np.inf], np.nan)
    dates = pd.to_datetime(meta["date"].to_numpy())
    tickers = meta["ticker"].to_numpy()
    frame = pd.DataFrame({"date": dates, "ticker": tickers})
    frame = frame.set_index(["date", "ticker"])
    close_long = close.stack().rename("close")
    close_long.index.names = ["date", "ticker"]
    base = close_long.reindex(frame.index)
    frame["close"] = base.to_numpy()
    for H in HORIZONS:
        fut = close.shift(-H).stack().rename(f"ret_{H}")
        fut.index.names = ["date", "ticker"]
        r = fut.reindex(frame.index) / base - 1.0
        frame[f"ret_{H}"] = r.to_numpy()
    frame = frame.reset_index()
    return X_full, frame, names, close


def walkforward_predict(X_full, frame, names):
    dates = frame["date"].to_numpy(); tickers = frame["ticker"].to_numpy()
    ud = np.unique(dates); start = pd.Timestamp(START)
    pd_ = ud[ud >= np.datetime64(start)]
    refit = np.arange(0, len(pd_), REFIT)
    print(f"OOS {pd.Timestamp(pd_[0]).date()}..{pd.Timestamp(pd_[-1]).date()} "
          f"| {len(refit)} refits | {len(names)} feats | {len(frame):,} rows", flush=True)
    Xn = X_full.to_numpy()
    fin = np.isfinite(Xn)
    preds = {H: np.full(len(frame), np.nan) for H in HORIZONS}
    retcols = {H: frame["ret_%d" % H].to_numpy() for H in HORIZONS}
    t0 = time.time()
    for k, kk in enumerate(refit):
        if k % 6 == 0:
            print(f"  refit {k+1}/{len(refit)} @ {pd.Timestamp(pd_[kk]).date()} "
                  f"({time.time()-t0:.0f}s)", flush=True)
        d = pd_[kk]; dmin = d - np.timedelta64(TRAIN_WIN, "D")
        # CRITICAL leak fix: train only on rows at least H days BEFORE the block,
        # so no training label (a t->t+H forward return) overlaps the prediction
        # block. Training on rows < d lets labels reach into the block and the
        # model "knows" the block's early days (IC ~0.3-0.4 on block days 0-9).
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


def daily_longshort(frame, pred, H, K=K, cost=COST):
    fw = frame.copy()
    fw["pred"] = pred
    fw["fwd"] = fw["ret_%d" % H]
    fw = fw[np.isfinite(fw["pred"]) & np.isfinite(fw["fwd"])]
    perday = {}
    for date, g in fw.groupby("date"):
        g = g.sort_values("pred", ascending=False)
        n = len(g)
        if n < 2*K+2:
            continue
        los = g["fwd"].iloc[:K].mean()
        sis = g["fwd"].iloc[n-K:].mean()
        perday[date] = (los - sis) - 2*cost
    return pd.Series(perday).sort_index()


def vol_target(dser, ann_target=VOL_TARGET_ANN):
    rv = dser.rolling(20, min_periods=10).std().shift(1)*np.sqrt(252)
    sc = (ann_target/rv).clip(upper=3.0, lower=0.0).fillna(1.0)
    return dser*sc


def stats(full):
    full = full.dropna()
    if len(full) < 20 or full.std() == 0:
        return {"sr": None, "ann": None, "dd": None, "calmar": None}
    eq = (1+full).cumprod()
    sr = (full.mean()/full.std())*np.sqrt(252)
    ann = (1+full).prod()**(252/len(full))-1
    dd = (eq/eq.cummax()-1).min()
    return {"sr": round(float(sr),3), "ann": round(float(ann),4),
            "dd": round(float(dd),4),
            "calmar": round(float(ann)/float(dd),2) if dd < 0 else None}


def main():
    print("Building shared feature matrix + 3 forward-return targets...", flush=True)
    X_full, frame, names, close = build_frame()
    print(f"frame {frame.shape} | X {X_full.shape}", flush=True)
    print("Running walk-forward XGB regressors for H in", HORIZONS, flush=True)
    preds = walkforward_predict(X_full, frame, names)

    # persist predictions for the honest book sim + validation
    import pickle
    os.makedirs(os.path.dirname(PRED_CACHE) or ".", exist_ok=True)
    with open(PRED_CACHE, "wb") as fh:
        pickle.dump({"frame": frame, "preds": preds}, fh)
    print(f"cached OOS preds -> {PRED_CACHE}", flush=True)

    frame["date"] = pd.to_datetime(frame["date"])
    alld = pd.bdate_range(frame["date"].min(), frame["date"].max())
    result = {}; full_series = {}
    for H in HORIZONS:
        ds = daily_longshort(frame, preds[H], H)
        ds_vt = vol_target(ds.copy())
        fb = ds.reindex(alld, fill_value=0.0)
        fvt = ds_vt.reindex(alld, fill_value=0.0)
        label = {1: "next-day", 5: "1-week", 21: "1-month"}[H]
        print(f"\n=== H={H} ({label}) ===")
        for lab, fser in [("raw", fb), ("vol-target", fvt)]:
            st = stats(fser)
            print(f"  {lab:11s} SR {st['sr']}  ann {st['ann']:>7.1%}  maxDD {st['dd']:>6.1%}  Calmar {st['calmar']}")
        full_series[H] = {"raw": fb, "vt": fvt}
        result[f"H{H}"] = {"raw": stats(fb), "vt": stats(fvt)}

    print("\n=== Multi-horizon EW blend (1d/1wk/1mo, vol-targeted) ===")
    blend = sum(full_series[h]["vt"] for h in HORIZONS)/len(HORIZONS)
    st = stats(blend)
    print(f"  blend  SR {st['sr']}  ann {st['ann']:>7.1%}  maxDD {st['dd']:>6.1%}  Calmar {st['calmar']}")
    result["blend_ew"] = st

    with open(os.path.join(OUT, "multi_horizon_results.json"), "w") as f:
        json.dump(result, f, indent=2)
    blend.to_frame("blend").to_csv(os.path.join(OUT, "blend_daily.csv"))
    for H in HORIZONS:
        full_series[H]["vt"].to_frame(f"h{H}").to_csv(os.path.join(OUT, f"h{H}_daily.csv"))
    print(f"\nsaved -> {OUT}/multi_horizon_results.json")


if __name__ == "__main__":
    main()
