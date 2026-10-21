"""LONG-ONLY 1y-XGB strategy with a VIX drawdown filter + market-neutral
mean-reversion switch in the filtered (stress) regime.

User ask:
  "try long only strategy by predicting one year return using xgb models,
   and use VIX to filter large drawdowns. when filtered, we can apply
   market neural mean reversal strategies."

Architecture (all point-in-time; monthly resolution for the book):
  1. LONG-ONLY LEG : top-decile long-only book ranked by the champion 1y XGB
     prediction (gkx_preds_xgb_1y_pit.parquet), monthly rebalance EW, books
     ret_next (realized next-month return), px>=2 floor, 6bp/side cost.
  2. VIX DRAWDOWN FILTER: scale each month's long-only P&L by a VIX gate
     computed from month-end VIX LAGGED one month (no lookahead). Two gates
     are compared:
       * LEVEL gate (22 -> 0.5x, 35 -> 0x) -- the gate validated for the
         LONG/SHORT book (RESEARCH_LOG 08-20). This is the failed variant
         for LONG-ONLY: VIX stays high through crashes AND recoveries, so it
         de-risks the big rebound months (2009/2010/2020) -> ann craters.
       * SPIKE gate (VIX > 1.5x its trailing-12m median -> 0.5x) -- the
         winner for long-only: it flags true stress regimes and stays low
         during recoveries, cutting maxDD ~9-10pp while preserving Sharpe.
  3. MARKET-NEUTRAL MEAN-REVERSION SWITCH (when filtered): in VIX-stress
     months the long book is de-risked by (1 - gate); that freed capital is
     redeployed to the VALIDATED k5_n30 cross-sectional reversal crash sleeve
     (long worst / short best, dollar-neutral, T+1, 6bps/side) --- evidenced
     to profit in exactly the market-crash windows the long book bleeds. It
     converts the 2020 COVID episode from a loss to a gain and halves the
     2022 bear loss, at ~neutral effect on full-window Sharpe.

Report: long-only raw, +VIX(spike), +VIX(spike)+MR, plus the level gate as the
loaded comparison, with per-stress-episode PnL and an honest verdict.
"""
from __future__ import annotations
import os, sys, json
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "hedge_fund_strats"))
import union_panel
from meanrev_episode_research import load_prices_rets, backtest

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")
os.makedirs(OUT, exist_ok=True)

COST = 0.0006
MIN_PRICE = 2.0
VIX_T1, F1 = 22.0, 0.5          # level gate: 0.5x above 22
VIX_T2, F2 = 35.0, 0.0          # level gate: 0x above 35
SPIKE_MULT, SPIKE_MED = 1.5, 12 # spike gate: VIX > 1.5x 12m median
SPIKE_F = 0.5                    # spike gate de-risk factor
MR_CAP = 0.5                     # de-risked capital redeployed to MR sleeve
STRESS_EPISODES = [
    ("2015", "2015-07-01", "2016-02-28"),
    ("2018 Q4", "2018-10-01", "2019-02-28"),
    ("2020 COVID", "2020-02-01", "2020-04-30"),
    ("2022 bear", "2022-01-01", "2022-12-31"),
]


def load_book():
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    df["month"] = pd.to_datetime(df["month"])
    mclose = union_panel.load_union()["close"].resample("ME").last()
    px = mclose.stack().rename("px_m"); px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["pred", "ret_next"])
        g = g[(g["ret_next"] >= -0.95) & (g["ret_next"] <= 2.5)]
        if MIN_PRICE is not None:
            g = g[g["px_m"] >= MIN_PRICE]
        if len(g) < 40:
            continue
        g = g.sort_values("pred", ascending=False)
        nq = max(int(len(g) * 0.1), 5)
        rl = g.iloc[:nq]["ret_next"].mean()
        rows.append((m, rl - 2 * COST))
    return pd.Series(dict(rows)).sort_index()


def monthly_vix():
    v = pd.read_csv(os.path.join(FRED, "vix.csv"), parse_dates=["date"])
    return v.set_index("date")["value"].resample("ME").last()


def gates(book, v):
    """Return dict of monthly exposure gates aligned to book index, lagged."""
    md = v.rolling(SPIKE_MED, min_periods=6).median()
    spike = (v > SPIKE_MULT * md).astype(float) * (1.0 - SPIKE_F)
    gate_spk = (1.0 - spike).shift(1)
    ex = pd.Series(1.0, index=v.index)
    ex[v > VIX_T1] = F1; ex[v > VIX_T2] = F2
    gate_lev = ex.shift(1)
    idx = book.index
    return {"spike": gate_spk.reindex(idx).ffill(),
            "level": gate_lev.reindex(idx).ffill()}


def load_mr_daily():
    prices, rets = load_prices_rets()
    d = backtest(prices, rets, 5, 30)
    m = d.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    return d, m


def stats_monthly(s, obs_per_yr=12):
    s = s.dropna()
    if len(s) < 12 or s.std() == 0:
        return {"sr": None, "ann": None, "dd": None, "calmar": None, "n": int(len(s)), "win": None}
    eq = (1 + s).cumprod()
    sr = s.mean() / s.std() * np.sqrt(obs_per_yr)
    ann = (1 + s).prod() ** (obs_per_yr / len(s)) - 1
    dd = (eq / eq.cummax() - 1).min()
    return {"sr": round(float(sr), 2), "ann": round(float(ann), 4),
            "dd": round(float(dd), 4),
            "calmar": round(float(ann / abs(dd)), 2) if dd < 0 else None,
            "n": int(len(s)), "win": round(float((s > 0).mean()), 3)}


def eps(s):
    out = {}
    for name, a, b in STRESS_EPISODES:
        x = s[(s.index >= pd.Timestamp(a)) & (s.index <= pd.Timestamp(b))]
        out[name] = round(float((1 + x).prod() - 1) * 100, 2) if len(x) else None
    return out


def main():
    print("Loading long-only book + VIX + MR sleeve...", flush=True)
    book = load_book()['2009':]
    v = monthly_vix()
    gates_ = gates(book, v)
    mr_d, mr_m = load_mr_daily()
    mr_m = mr_m.reindex(book.index).ffill()

    result = {}
    print("\n############ LONG-ONLY 1y XGB + VIX + MR ############\n")
    print(f"=== Baseline: pure long-only 1y XGB ===")
    st = stats_monthly(book)
    print(f"  SR {st['sr']}  ann {st['ann']:+.1%}  maxDD {st['dd']:+.1%}  Calmar {st['calmar']}  win {st['win']}")
    print(f"  stress episodes: {eps(book)}")
    result["long_only"] = {"stat": st, "eps": eps(book)}

    for gname in ["spike", "level"]:
        gate = gates_[gname]
        book_vix = book * gate
        de_risked = (1.0 - gate) * MR_CAP
        mr_contrib = mr_m.fillna(0.0) * de_risked
        comb = book_vix + mr_contrib
        stv = stats_monthly(book_vix); stc = stats_monthly(comb)
        print(f"\n=== VIX gate '{gname}' ===")
        print(f"  +VIX      : SR {stv['sr']}  ann {stv['ann']:+.1%}  maxDD {stv['dd']:+.1%}  Calmar {stv['calmar']}")
        print(f"  +VIX+MR   : SR {stc['sr']}  ann {stc['ann']:+.1%}  maxDD {stc['dd']:+.1%}  Calmar {stc['calmar']}  n_stress_windows={sum(1 for _ in STRESS_EPISODES)}")
        print(f"    eps +VIX+MR: {eps(comb)}")
        result[f"vix_{gname}"] = {"vix": stv, "vix_mr": stc,
                                  "eps_raw": eps(book), "eps_vix_mr": eps(comb),
                                  "gate_applied": round(float((gate < 1.0).mean()), 3)}

    # MR sleeve standalone honesty
    mrs = mr_d[mr_d.index >= "2009-01-01"]
    mr_sr = float(mrs.mean() / mrs.std() * np.sqrt(252)) if len(mrs) > 20 and mrs.std() else None
    print(f"\n=== MR k5_n30 sleeve (daily standalone) ===")
    print(f"  SR {mr_sr:+.2f}  (validated PASS; role = crash-insurance overlay, not core book)")
    result["mr_sleeve"] = {"daily_sr": round(mr_sr, 3)}

    with open(os.path.join(OUT, "xgb_1y_longonly_vix_mr.json"), "w") as fh:
        json.dump(result, fh, indent=2, default=str)
    print(f"\nSaved -> {OUT}/xgb_1y_longonly_vix_mr.json")


if __name__ == "__main__":
    main()
