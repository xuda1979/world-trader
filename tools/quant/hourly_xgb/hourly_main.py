"""
Hourly XGB prediction model for US equities (intraday proof-of-concept).
Predict next-hour close return. If predicted next-hour close is > +2.0% above
current close, BUY at current close and liquidate at next hour close.
Trading cost: 6 bps per side (12 bps round-trip).
Backtest on regular-session hourly bars from polygon_intraday (17 liquid names).

Data: 5-min bars -> resample to regular-session hourly bars (10:00..16:00 ET).
Features are strictly causal at bar close(T): all info known at/ before T.
Target: close(T+1)/close(T) - 1.
"""
from __future__ import annotations
import os, glob, sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
INTRADAY = os.path.join(ROOT, "tools/quant/data/polygon_intraday")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

import xgboost as xgb
from sklearn.metrics import mean_squared_error

THRESH = 0.02          # 2% predicted next-hour return to trigger buy
COST = 0.0006          # 6 bps per side


def load_intraday():
    """Load all tickers, resample to regular-session hourly bars, return per-ticker
    DataFrame indexed by (datetime) with close. Align on a common datetime index."""
    tickers = {}
    for fn in sorted(glob.glob(os.path.join(INTRADAY, "*.csv"))):
        sym = os.path.basename(fn)[:-4]
        df = pd.read_csv(fn)
        ts = pd.to_datetime(df["t"], unit="ms").dt.tz_localize("UTC").dt.tz_convert("America/New_York")
        df["dt"] = ts
        # regular session only
        t0 = pd.to_datetime("09:30").time()
        t1 = pd.to_datetime("16:00").time()
        reg = df[(df.dt.dt.time >= t0) & (df.dt.dt.time <= t1)].copy()
        if len(reg) < 10:
            continue
        s = reg.set_index("dt")["close"].sort_index()
        hb = s.resample("1h").last().dropna()
        # drop partial first bucket (09:00) -> keep full hours 10:00..16:00
        hb = hb[hb.index.hour >= 10]
        # dedupe index
        hb = hb[~hb.index.duplicated(keep="last")]
        tickers[sym] = hb
    return tickers


def build_panel(tickers):
    """Return close DataFrame (datetime x ticker) + valid-mask."""
    idx = sorted(set().union(*[set(t.index) for t in tickers.values()]))
    close = pd.DataFrame(index=idx)
    for sym, s in tickers.items():
        close[sym] = s.reindex(idx)
    return close


def build_features(close: pd.DataFrame):
    """Build rich causal features (datetime x ticker), all known at bar close T.
    Returns f (dict name->DataFrame), feats (list of names)."""
    f = {}
    ret = close.pct_change()
    # per-ticker return horizons (hours)
    for n in [1, 2, 3, 6, 12, 24]:
        f[f"ret_{n}h"] = close / close.shift(n) - 1.0
    # realized volatility over horizons
    for n in [3, 6, 12, 24]:
        f[f"rvol_{n}h"] = ret.rolling(n).std()
    # momentum: close vs rolling mean over various windows
    for n in [6, 12, 24, 48]:
        f[f"dist_ma{n}"] = close / close.rolling(n).mean() - 1.0
    # distance from rolling min/max high-low range
    roll_max = close.rolling(12).max()
    roll_min = close.rolling(12).min()
    rng = (roll_max - roll_min)
    f["pos_ma12"] = (close - roll_min) / rng.replace(0, np.nan)
    # RSI(14 on hourly)
    delta = ret
    up = delta.clip(lower=0).rolling(14).mean()
    dn = (-delta.clip(upper=0)).rolling(14).mean()
    rs = up / dn.replace(0, np.nan)
    f["rsi14"] = 100 - 100 / (1 + rs)
    # gap: overnight / opening move relative to prev session close handled implicitly
    # time seasonality
    hh = close.index.hour
    dow = close.index.dayofweek
    f["hour"] = pd.DataFrame({c: hh for c in close.columns}, index=close.index)
    f["dow"] = pd.DataFrame({c: dow for c in close.columns}, index=close.index)

    # ---- cross-sectional / market features (known at T) ----
    xs_ret = ret.mean(axis=1)           # equal-weight market hourly return
    xs_vol = ret.iloc[:, :].std(axis=1) # cross-sectional dispersion this hour
    for n in [1, 2, 3, 6]:
        f[f"xs_ret_{n}h"] = pd.DataFrame({c: xs_ret.rolling(n).sum() for c in close.columns}, index=close.index)
    for n in [6, 12]:
        f[f"xs_vol_{n}h"] = pd.DataFrame({c: xs_vol.rolling(n).mean() for c in close.columns}, index=close.index)
    # rolling market vol
    for n in [6, 12]:
        f[f"xs_rvol_{n}h"] = pd.DataFrame({c: xs_ret.rolling(n).std() for c in close.columns}, index=close.index)
    # breadth: share of universe up this hour
    breadth = (ret > 0).mean(axis=1)
    f["xs_breadth"] = pd.DataFrame({c: breadth for c in close.columns}, index=close.index)

    return f


def to_xy(f, target, close):
    """Stack feature dict + target into tidy rows (drop rows with any NaN feature or target)."""
    feats = list(f.keys())
    names = []
    frames = []
    for name in feats:
        df = f[name]
        # align feature to close index
        ff = df.reindex(close.index)
        for c in close.columns:
            frames.append(ff[c].to_frame(name + "_" + c))
            names.append(name + "_" + c)
    X = pd.concat(frames, axis=1)
    # target: flattened next-hour return in same row order
    y_all = target.stack()
    X = X.stack()  # -> MultiIndex (datetime, ticker)
    y = y_all.reindex(X.index)
    X = X.unstack() if False else X
    # X is Series? we need wide: build wide frame aligned by (dt,ticker)
    return X, y, feats


def main():
    tickers = load_intraday()
    print(f"Loaded {len(tickers)} tickers")
    close = build_panel(tickers)
    print(f"Panel: {close.shape[0]} hourly rows x {close.shape[1]} tickers")
    print(f"Date range: {close.index.min()} .. {close.index.max()}")

    # target: next-hour return
    ret = close.pct_change()
    target = ret.shift(-1)   # row T predicts return T->T+1

    f = build_features(close)
    feats = list(f.keys())

    # Build tidy stacked frame: column-per-(feature,ticker) wide then stack
    # into a long DataFrame indexed by (dt, ticker).
    colmap = {}
    for name in feats:
        for c in close.columns:
            colmap[(name, c)] = f[name][c].reindex(close.index)
    wide = pd.DataFrame(colmap, index=close.index)
    # stack
    wide = wide.stack(future_stack=True)  # MultiIndex (dt, ticker)
    wide.index.names = ["dt", "ticker"]
    # target same order
    ys = target.stack(future_stack=True)
    ys.index.names = ["dt", "ticker"]
    y = ys.reindex(wide.index)
    X = wide
    feat_names = list(wide.columns)

    mask = X.notna().all(axis=1) & y.notna()
    Xc = X[mask]
    yc = y[mask]
    print(f"Complete rows: {len(Xc)} (out of {len(wide)})")

    # walk-forward split by date: train first 70% of dates, test last 30%
    dts = np.array(sorted(Xc.index.get_level_values("dt").unique()))
    split = int(len(dts) * 0.70)
    train_dts = set(dts[:split])
    test_dts = set(dts[split:])
    tr_mask = Xc.index.get_level_values("dt").isin(train_dts)
    te_mask = Xc.index.get_level_values("dt").isin(test_dts)
    Xtr, ytr = Xc[tr_mask].to_numpy(), yc[tr_mask].to_numpy()
    Xte, yte = Xc[te_mask].to_numpy(), yc[te_mask].to_numpy()
    print(f"Train rows {len(Xtr)}, Test rows {len(Xte)}")

    model = xgb.XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0,
        objective="reg:squarederror", random_state=42, n_jobs=-1,
    )
    model.fit(Xtr, ytr, eval_set=[(Xte, yte)], verbose=False)
    pred = model.predict(Xte)
    rmse = float(np.sqrt(np.mean((pred - yte) ** 2)))
    print(f"XGB test RMSE {rmse:.5f}  (hourly ret std {yte.std():.5f})")
    ic = np.corrcoef(pred, yte)[0, 1]
    print(f"IC (pred vs actual next-hour return): {ic:.4f}")

    # ---- backtest the 2% threshold long strategy ----
    tr_slots = Xc[te_mask].index
    df = pd.DataFrame({
        "dt": tr_slots.get_level_values("dt"),
        "ticker": tr_slots.get_level_values("ticker"),
        "pred": pred, "actual": yte,
    })
    trades = df[df["pred"] > THRESH].copy()
    print(f"\nTrades triggered (pred > {THRESH:.1%}): {len(trades)} / {len(df)} test rows ({len(trades)/len(df):.2%})")

    # for each trade, next hour return is 'actual' (close T->T+1); gross return before cost
    trades["gross"] = trades["actual"]
    trades["net"] = trades["gross"] - 2 * COST   # 6bps buy + 6bps sell
    gross_tot = (1 + trades["gross"]).prod() - 1
    net_tot = (1 + trades["net"]).prod() - 1
    win = (trades["net"] > 0).mean()
    print(f"Backtest over test period (net of 12bps round-trip):")
    print(f"  N trades           : {len(trades)}")
    print(f"  Gross compounded   : {gross_tot:+.2%}")
    print(f"  Net  compounded    : {net_tot:+.2%}")
    print(f"  Net win rate       : {win:.1%}")
    print(f"  Avg gross/trade    : {trades['gross'].mean():+.4%}")
    print(f"  Avg net/trade      : {trades['net'].mean():+.4%}")
    if len(trades):
        per_day = trades.groupby(trades["dt"].dt.date)["net"].agg(["sum", "count"])
        daily_ret = per_day["sum"]
        sharpe = daily_ret.mean() / (daily_ret.std() + 1e-12) * np.sqrt(252)
        print(f"  Daily-agg Sharpe (test) : {sharpe:.2f}")
    if len(trades):
        # equity curve by trade order (equal-weight per trade)
        eq = (1 + trades["net"]).cumprod()
        maxdd = (eq / eq.cummax() - 1).min()
        print(f"  Max drawdown (per-trade) : {maxdd:.1%}")

    # top-k bucket analysis - does higher prediction translate to higher realized?
    print("\nPrediction bucket -> realized next-hour return (test):")
    df["bucket"] = pd.cut(df["pred"], bins=[-1, 0, 0.005, 0.01, 0.015, 0.02, 0.03, 1])
    print(df.groupby("bucket")["actual"].agg(["mean", "count"]))

    model.save_model(os.path.join(OUT, "hourly_xgb_model.json"))
    trades.to_csv(os.path.join(OUT, "hourly_trades.csv"), index=False)
    print("\nSaved model + trades to", OUT)


if __name__ == "__main__":
    main()
