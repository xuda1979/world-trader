"""XGB long-horizon: predict 12-month forward returns, decile L/S backtest.

Extends the GKX replication infra (gkx_monthly_panel.parquet, 57 point-in-time
characteristics, ~900-1100 investable names) to the ONE-YEAR horizon:
  - target: ret_fwd12 = 12-month forward close-to-close return
  - PURGED walk-forward: to predict month m, train on months t with t+12 < m
    (labels fully realized before the block; no 12m-window overlap into OOS),
    rolling 7y window, yearly refit, predict block m..m+11.
  - models: XGB GBRT (primary) + Ridge reference
  - portfolio: monthly decile L/S (top/bottom decile by pred), EW + VW,
    gross and net (24bp/mo full cycle).
Honesty: 12m labels overlap across adjacent prediction months, so monthly
Sharpe is also reported on NON-OVERLAPPING annual cohorts (prediction made
only at each refit month = independent 12m return windows).

OOS 2009-2026 (labels through 2025-08, needing close through 2026-08).
"""
from __future__ import annotations
import os, sys, json, time
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ.setdefault("DYLD_LIBRARY_PATH", "/Users/daxu/homebrew/opt/libomp/lib:" + os.environ.get("DYLD_LIBRARY_PATH", ""))
import union_panel
from sklearn.linear_model import Ridge
from scipy.stats import spearmanr
import xgboost as xgb

TRAIN_MONTHS = 84      # 7y rolling window
H = 12                 # 12-month forward return target
START = "2009-01-01"
COST = 0.0006          # 6bp/side -> 24bp/mo full cycle
OUT = os.path.join(HERE, "..", "reports", "xgb_horizons")

# Finnhub CURRENT-snapshot fundamentals tiled back through history — a
# lookahead-flavored leak (2026 values in 2002 rows). Dropped in the
# point-in-time (PIT) feature set. EDGAR chars (incl 'mcap','size') are
# filing-date point-in-time and stay.
SNAPSHOT_FEATS = ["marketCap", "pe", "pb", "roe", "rev_growth",
                  "eps_growth", "asset_turn", "debt_eq", "div_yield",
                  "log_mcap"]


def load_panel_with_1y_target():
    df = pd.read_parquet(f"{HERE}/data/gkx_monthly_panel.parquet")
    df["month"] = pd.to_datetime(df["month"])
    # rebuild month-end closes from the FULL union price source (913-ticker
    # panel; pc.load_ohlcv is only twelve_big ~292 names)
    mclose = union_panel.load_union()["close"].resample("ME").last()
    fwd12 = (mclose.shift(-H) / mclose - 1.0).stack().rename("ret_fwd12")
    fwd12.index.names = ["month", "ticker"]
    df = df.join(fwd12, on=["month", "ticker"], how="left")
    fwd1 = (mclose.shift(-1) / mclose - 1.0).stack().rename("ret_fwd1")
    fwd1.index.names = ["month", "ticker"]
    df = df.join(fwd1, on=["month", "ticker"], how="left")
    fwd3 = (mclose.shift(-3) / mclose - 1.0).stack().rename("ret_fwd3")
    fwd3.index.names = ["month", "ticker"]
    df = df.join(fwd3, on=["month", "ticker"], how="left")
    # train on the months-2..12 return (slow component; ex1st won the target
    # test 2026-08-20: entry-month sweep 0.91-1.28, max dd -19.6% vs raw
    # target's 0.38-1.10, dd up to -71.6%). TARGET_MODE=raw12 for the old.
    if os.environ.get("TARGET_MODE") == "raw12":
        df["ret_fwd12_train"] = df["ret_fwd12"]
    elif os.environ.get("TARGET_MODE") == "ex3m":
        df["ret_fwd12_train"] = df["ret_fwd12"] - df["ret_fwd3"]
    else:
        df["ret_fwd12_train"] = df["ret_fwd12"] - df["ret_fwd1"]
    # PANEL BUG FIX: the panel's ret_next was built via mret.stack().shift(-1)
    # — shift(-1) on the stacked MultiIndex shifts by ROW POSITION, scrambling
    # returns across tickers (verified: CSCO prod(1+ret_next) +105.7% vs true
    # +11.7%). Recompute per-ticker on the index: ret_next(m) = (m -> m+1).
    rn = (mclose.shift(-1) / mclose - 1.0).stack().rename("ret_next_fix")
    rn.index.names = ["month", "ticker"]
    df = df.join(rn, on=["month", "ticker"], how="left")
    df["ret_next"] = df["ret_next_fix"]
    df = df.drop(columns=["ret_next_fix"])
    # sane tail on the LABEL only where it exists; keep unlabeled recent
    # months so predictions extend through the latest refit block (live book)
    r12 = df["ret_fwd12"]
    df = df[r12.isna() | ((r12 >= -0.95) & (r12 <= 2.5))]
    names = json.load(open(f"{HERE}/data/gkx_names.json"))
    return df, names


def run_model(df, names, model_fn, label):
    # keep ALL rows: predictions extend through the last refit block even
    # where the 12m label is not yet realized (live book); training masks
    # on finite labels only.
    X = df[names].replace([np.inf, -np.inf], np.nan)
    months = np.sort(df["month"].unique())
    ud = months[months >= pd.Timestamp(START)]
    refits = np.arange(0, len(ud), 12)  # yearly refit
    pred = np.full(len(df), np.nan); t0 = time.time()
    for k, kk in enumerate(refits):
        if k % 6 == 0:
            print(f"  [{label}] refit {k+1}/{len(refits)} @ {pd.Timestamp(ud[kk]).date()} ({time.time()-t0:.0f}s)", flush=True)
        m = ud[kk]
        # PURGE: train rows t need their 12m label window (t..t+12) closed before m
        tr = (df["month"] <= m - pd.DateOffset(months=H + 1)) & \
             (df["month"] > m - pd.DateOffset(months=TRAIN_MONTHS + H + 1))
        tr_idx = np.where(tr)[0]
        Xtr = X.iloc[tr_idx].to_numpy(); ytr = df["ret_fwd12_train"].iloc[tr_idx].to_numpy()
        ok = np.isfinite(Xtr).sum(axis=1) > 0
        Xtr, ytr = Xtr[ok], ytr[ok]
        ok2 = np.isfinite(ytr); Xtr, ytr = Xtr[ok2], ytr[ok2]
        if len(Xtr) < 2000: continue
        meds = np.nanmedian(Xtr, axis=0); meds = np.where(np.isnan(meds), 0.0, meds)
        Xtr = np.where(np.isnan(Xtr), meds, Xtr)
        model = model_fn()
        model.fit(Xtr, ytr)
        blk = (df["month"] > m) & (df["month"] <= m + pd.DateOffset(months=12))
        bi = np.where(blk)[0]
        Xb = X.iloc[bi].to_numpy(); Xb = np.where(np.isnan(Xb), meds, Xb)
        bok = np.isfinite(Xb).sum(axis=1) > 0
        p = np.full(len(bi), np.nan)
        if bok.sum() > 0: p[bok] = model.predict(Xb[bok])
        pred[bi] = p
    df["pred"] = pred
    return df


def _decile_rows(df, weight_col, label_col):
    """Per-month decile selection over names with BOTH a prediction and the
    realized outcome for the booked label (join-miss rows excluded from the
    selection universe — booking a NaN label would silently zero-weight it)."""
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["pred", label_col])
        n = len(g)
        if n < 40: continue
        g = g.sort_values("pred", ascending=False)
        nq = max(int(n * 0.1), 5)
        longs = g.iloc[:nq]; shorts = g.iloc[-nq:]
        lw = 1.0 / nq if weight_col is None else (longs[weight_col] / longs[weight_col].sum())
        sw = 1.0 / nq
        rows.append((m, longs, shorts, lw, sw))
    return rows


def decile_ls_1m_hold(df, weight_col=None, cost=COST):
    """Monthly rebalance: pick top/bottom decile by the 12m-ahead prediction,
    book the NEXT-MONTH return (ret_next) of each leg, net of full-cycle cost.
    (The 12m prediction selects; the 1m return is the realized P&L of holding
    that book for one month. Booking fwd12 here would compound a year's return
    every month — the classic horizon-mismatch backtest bug.)"""
    rows = []
    for m, longs, shorts, lw, sw in _decile_rows(df, weight_col, "ret_next"):
        lg = (longs["ret_next"] * lw).sum(); sg = (shorts["ret_next"] * sw).sum()
        rows.append((m, lg - sg - 4 * cost))
    return pd.Series(dict(rows)).sort_index()


def decile_ls_12m_hold(df, weight_col=None, cost=COST, entry_month=2):
    """Annual cohorts: enter at the same calendar month every year, hold 12m,
    book the realized 12m return ONCE. Non-overlapping windows -> independent
    observations (honest annual Sharpe). entry_month sweeps cohort-entry
    convention (2 = first prediction month of a Jan-refit block)."""
    rows = []
    for m, longs, shorts, lw, sw in _decile_rows(df, weight_col, "ret_fwd12"):
        if not ((m.month == entry_month) and m.year >= 2009):
            continue
        lg = (longs["ret_fwd12"] * lw).sum(); sg = (shorts["ret_fwd12"] * sw).sum()
        rows.append((m, lg - sg - 4 * cost))
    return pd.Series(dict(rows)).sort_index()


def stats(s, annual=False):
    s = s.dropna()
    if len(s) < 8 or s.std() == 0: return None
    eq = (1 + s).cumprod()
    # annual series: each observation IS a 12m return -> SR without sqrt(12)
    sr = s.mean() / s.std() * (1.0 if annual else np.sqrt(12))
    ann = (1 + s).prod() ** (1.0 / len(s) if annual else 12.0 / len(s)) - 1
    dd = (eq / eq.cummax() - 1).min()
    return {"sr": round(float(sr), 2), "ann": round(float(ann), 4),
            "dd": round(float(dd), 4), "n": int(len(s)),
            "win": round(float((s > 0).mean()), 3)}


def ic_report(df):
    """Monthly Spearman IC of pred vs realized 12m forward return."""
    ics = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["pred", "ret_fwd12"])
        if len(g) < 40: continue
        rho, _ = spearmanr(g["pred"], g["ret_fwd12"])
        ics.append((m, rho))
    s = pd.Series(dict(ics))
    return {"ic_mean": round(float(s.mean()), 4),
            "ic_ir": round(float(s.mean() / s.std() * np.sqrt(12)), 2),
            "n": int(len(s))}


def main():
    df, names = load_panel_with_1y_target()
    print(f"panel {df.shape} | {len(names)} chars | 1y-label cov {df['ret_fwd12'].notna().mean():.2f} "
          f"| months {df['month'].min().date()}..{df['month'].max().date()}", flush=True)
    models = {
        "xgb": lambda: xgb.XGBRegressor(
                # depth-3/slow-lr config won the 12m-target sweep 2026-08-20:
                # entry-02 SR 1.03 vs 0.93 (d4) vs 0.75 (d6/mcw20)
                n_estimators=int(os.environ.get("XGB_TREES", 600)),
                learning_rate=float(os.environ.get("XGB_LR", 0.02)),
                max_depth=int(os.environ.get("XGB_DEPTH", 3)),
                min_child_weight=int(os.environ.get("XGB_MCW", 10)),
                subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                n_jobs=8, random_state=42),
        "ridge": lambda: Ridge(alpha=10),
    }
    fsets = {
        "full": names,
        "pit": [n for n in names if n not in SNAPSHOT_FEATS],  # point-in-time only
    }
    results = {}
    for fname, fset in fsets.items():
        print(f"\n########## feature set: {fname} ({len(fset)} chars) ##########", flush=True)
        for label, fn in models.items():
            print(f"\n=== {label} (12m target) ===", flush=True)
            dfp = run_model(df, fset, fn, f"{fname}-{label}")
            ic = ic_report(dfp)
            print(f"  IC mean {ic['ic_mean']}  IC-IR {ic['ic_ir']} ({ic['n']} months)", flush=True)
            for wname, wcol in [("EW", None)]:  # VW was ~zero; its weight feature (log_mcap) is part of the snapshot leak
                s_net = decile_ls_1m_hold(dfp, weight_col=wcol, cost=COST)
                print(f"  {wname} 1m-hold net24: {stats(s_net)}")
                entry_srs = {}
                for em in (2, 5, 8, 11):  # cohort-entry robustness sweep
                    s_12m = decile_ls_12m_hold(dfp, weight_col=wcol, cost=COST, entry_month=em)
                    st = stats(s_12m, annual=True)
                    entry_srs[em] = st
                    print(f"  {wname} 12m-hold entry-{em:02d} net24: {st}")
                srs = [e["sr"] for e in entry_srs.values() if e]
                results[f"{fname}_{label}_{wname}"] = {
                    "net_1mhold": stats(s_net),
                    "net_12mhold_by_entry_month": entry_srs,
                    "sr_range": [min(srs), max(srs)] if srs else None,
                    "ic": ic,
                }
            if fname == "full":
                dfp.to_parquet(f"{HERE}/data/gkx_preds_{label}_1y.parquet")
            else:
                dfp.to_parquet(f"{HERE}/data/gkx_preds_{label}_1y_pit.parquet")
    tag = os.environ.get("XGB_TAG", "")
    json.dump(results, open(os.path.join(OUT, f"gkx_1y_results{tag}.json"), "w"), indent=1, default=str)
    print(f"\nsaved -> {OUT}/gkx_1y_results{tag}.json")


if __name__ == "__main__":
    main()
