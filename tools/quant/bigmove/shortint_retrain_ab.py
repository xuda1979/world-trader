"""A/B: does adding the public FINRA short-ratio feature improve OOS SR?

SESSION 3 deliverable (2026-08-24 standup, Agent C). Retrains the 1y-ex1st and
1m champions from the PIT panel with `short_ratio` (point-in-time, lagged)
added to the 47-PIT feature set, vs the baseline PIT set. Both use the same
purged walk-forward protocol and model configs as the champions, so the OOS
SR/ann/dd delta is the honest answer to "should we feed short interest into
the models?"

Requires data/finra_short_ratio_monthly.parquet (built by finra_shortint_build).
Runs the 1y XGB (depth3/lr.02/600t, ex1st target) and the 1m Ridge+XGB
retrains; each reports OOS monthly-decile L/S net of 6bp/side.
"""
from __future__ import annotations
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault("DYLD_LIBRARY_PATH", "/Users/daxu/homebrew/opt/libomp/lib:" + os.environ.get("DYLD_LIBRARY_PATH", ""))
import union_panel
import xgboost as xgb
from scipy.stats import spearmanr

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
COST = 0.0006
START = "2009-01-01"
SNAP = ["marketCap", "pe", "pb", "roe", "rev_growth", "eps_growth",
        "asset_turn", "debt_eq", "div_yield", "log_mcap"]
TRAIN_MONTHS = 84
H = 12


def load_panel():
    df = pd.read_parquet(f"{HERE}/data/gkx_monthly_panel.parquet")
    df["month"] = pd.to_datetime(df["month"])
    mclose = union_panel.load_union()["close"].resample("ME").last()
    fwd12 = (mclose.shift(-H) / mclose - 1.0).stack().rename("ret_fwd12")
    fwd12.index.names = ["month", "ticker"]
    df = df.join(fwd12, on=["month", "ticker"], how="left")
    fwd1 = (mclose.shift(-1) / mclose - 1.0).stack().rename("ret_fwd1")
    fwd1.index.names = ["month", "ticker"]
    df = df.join(fwd1, on=["month", "ticker"], how="left")
    rn = (mclose.shift(-1) / mclose - 1.0).stack().rename("ret_next")
    rn.index.names = ["month", "ticker"]
    df = df.drop(columns=["ret_next"]).join(rn, on=["month", "ticker"], how="left")
    df["ret_fwd12_train"] = df["ret_fwd12"] - df["ret_fwd1"]  # ex1st target
    # join short_ratio (lagged 1 month = point-in-time; used to predict m+1)
    sr = pd.read_parquet(f"{HERE}/data/finra_short_ratio_monthly.parquet")
    sr["month"] = pd.to_datetime(sr["month"]) + pd.offsets.MonthEnd(0)
    sr = sr.rename(columns={"ticker": "ticker", "short_ratio": "short_ratio"})
    sr_lag = sr.copy()
    sr_lag["month"] = sr_lag["month"] + pd.DateOffset(months=1)  # feature known at m for m+1 booking
    df = df.merge(sr_lag[["month", "ticker", "short_ratio"]], on=["month", "ticker"], how="left")
    return df


def run_1y(df, feats, label):
    X = df[feats].replace([np.inf, -np.inf], np.nan)
    months = np.sort(df["month"].unique())
    ud = months[months >= pd.Timestamp(START)]
    refits = np.arange(0, len(ud), 12)
    pred = np.full(len(df), np.nan)
    for k, kk in enumerate(refits):
        m = ud[kk]
        tr = (df["month"] <= m - pd.DateOffset(months=H + 1)) & \
             (df["month"] > m - pd.DateOffset(months=TRAIN_MONTHS + H + 1))
        tr_idx = np.where(tr)[0]
        Xtr = X.iloc[tr_idx].to_numpy(); ytr = df["ret_fwd12_train"].iloc[tr_idx].to_numpy()
        ok = np.isfinite(Xtr).sum(axis=1) > 0
        Xtr, ytr = Xtr[ok], ytr[ok]
        ok2 = np.isfinite(ytr); Xtr, ytr = Xtr[ok2], ytr[ok2]
        if len(Xtr) < 2000:
            continue
        meds = np.nanmedian(Xtr, axis=0); meds = np.where(np.isnan(meds), 0.0, meds)
        Xtr = np.where(np.isnan(Xtr), meds, Xtr)
        model = xgb.XGBRegressor(n_estimators=600, learning_rate=0.02, max_depth=3,
                                 min_child_weight=10, subsample=0.8, colsample_bytree=0.8,
                                 tree_method="hist", n_jobs=8, random_state=42)
        model.fit(Xtr, ytr)
        blk = (df["month"] > m) & (df["month"] <= m + pd.DateOffset(months=12))
        bi = np.where(blk)[0]
        Xb = X.iloc[bi].to_numpy(); Xb = np.where(np.isnan(Xb), meds, Xb)
        bok = np.isfinite(Xb).sum(axis=1) > 0
        p = np.full(len(bi), np.nan)
        if bok.sum() > 0:
            p[bok] = model.predict(Xb[bok])
        pred[bi] = p
    df["pred"] = pred
    return decile_ls(df, label)


def decile_ls(df, label):
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["pred", "ret_next"])
        if len(g) < 40:
            continue
        g = g.sort_values("pred", ascending=False)
        nq = max(int(len(g) * 0.1), 5)
        rows.append((m, g["ret_next"].iloc[:nq].mean() - g["ret_next"].iloc[-nq:].mean() - 4 * COST))
    s = pd.Series(dict(rows)).sort_index()
    return stats(s), s


def run_1m(df, feats, label):
    """1m Ridge+XGB ensemble, purged walk-forward, monthly decile L/S."""
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler
    X = df[feats].replace([np.inf, -np.inf], np.nan)
    months = np.sort(df["month"].unique())
    ud = months[months >= pd.Timestamp(START)]
    refits = np.arange(0, len(ud), 12)
    pr = np.full(len(df), np.nan); px = np.full(len(df), np.nan)
    for k, kk in enumerate(refits):
        m = ud[kk]
        # train on months where label (m+1) realized before m: t < m
        tr = (df["month"] < m) & (df["month"] >= m - pd.DateOffset(months=TRAIN_MONTHS))
        tr_idx = np.where(tr)[0]
        Xtr = X.iloc[tr_idx].to_numpy(); ytr = df["ret_next"].iloc[tr_idx].to_numpy()
        ok = (np.isfinite(Xtr).sum(axis=1) > 0) & np.isfinite(ytr)
        Xtr, ytr = Xtr[ok], ytr[ok]
        if len(Xtr) < 2000:
            continue
        meds = np.nanmedian(Xtr, axis=0); meds = np.where(np.isnan(meds), 0.0, meds)
        Xtr = np.where(np.isnan(Xtr), meds, Xtr)
        sc = StandardScaler().fit(Xtr)
        m1 = Ridge(alpha=10).fit(sc.transform(Xtr), ytr)
        m2 = xgb.XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=5,
                              subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                              n_jobs=8, random_state=42).fit(Xtr, ytr)
        blk = (df["month"] == m)
        bi = np.where(blk)[0]
        Xb = X.iloc[bi].to_numpy(); Xb = np.where(np.isnan(Xb), meds, Xb)
        bok = np.isfinite(Xb).sum(axis=1) > 0
        pb = np.full(len(bi), np.nan); pi = np.full(len(bi), np.nan)
        if bok.sum() > 0:
            pb[bok] = m1.predict(sc.transform(Xb[bok]))
            pi[bok] = m2.predict(Xb[bok])
        pr[bi] = pb; px[bi] = pi
    df["pr"] = pr; df["px"] = px
    df["zr"] = df.groupby("month")["pr"].transform(lambda s: zsafe(s))
    df["zx"] = df.groupby("month")["px"].transform(lambda s: zsafe(s))
    df["ens"] = 0.6 * df["zr"] + 0.4 * df["zx"]
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["ens", "ret_next"])
        if len(g) < 40:
            continue
        g = g.sort_values("ens", ascending=False)
        nq = max(int(len(g) * 0.1), 5)
        rows.append((m, g["ret_next"].iloc[:nq].mean() - g["ret_next"].iloc[-nq:].mean() - 4 * COST))
    s = pd.Series(dict(rows)).sort_index()
    return stats(s), s


def zsafe(x):
    from scipy.stats import zscore
    return zscore(x, nan_policy="omit")


def stats(s):
    s = s.dropna()
    if len(s) < 12 or s.std() == 0:
        return None
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 2),
            "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4),
            "n": int(len(s))}


def main():
    df = load_panel()
    if "short_ratio" not in df.columns or df["short_ratio"].notna().sum() == 0:
        print("no short_ratio data yet — run finra_shortint_build first (full build still downloading)")
        return
    feats_all = json.load(open(f"{HERE}/data/gkx_names.json"))
    pit = [f for f in feats_all if f not in SNAP]
    res = {}
    print("=== 1y ex1st XGB: PIT vs PIT+short_ratio ===", flush=True)
    for tag, feats in [("pit", pit), ("pit+short", pit + ["short_ratio"])]:
        st, s = run_1y(df, feats, tag)
        res[f"1y_{tag}"] = {"sr": st, "obs": len(s)}
        print(f"  1y {tag}: SR {st['sr']}  ann {st['ann']:+.1%}  dd {st['dd']:+.1%}")
    print("\n=== 1m Ridge+XGB ens: PIT vs PIT+short_ratio ===", flush=True)
    for tag, feats in [("pit", pit), ("pit+short", pit + ["short_ratio"])]:
        st, s = run_1m(df, feats, tag)
        res[f"1m_{tag}"] = {"sr": st, "obs": len(s)}
        print(f"  1m {tag}: SR {st['sr']}  ann {st['ann']:+.1%}  dd {st['dd']:+.1%}")
    json.dump(res, open(os.path.join(OUT, "shortint_ab_retrain.json"), "w"), indent=2, default=str)
    print(f"\nsaved -> {OUT}/shortint_ab_retrain.json")


if __name__ == "__main__":
    main()
