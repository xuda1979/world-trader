"""Modeling that SOME names are not shortable (hard-to-borrow / no locate).

User ask (2026-08-23): "we need to consider/model sometimes some stocks are not
shortable."

We do NOT fabricate per-name locate tables we don't have. Instead we model the
short-availability constraint honestly at the rate level: in any month, a
fraction `p` of the model's chosen short names cannot be borrowed (no locate /
hard-to-borrow / threshold-security). The practical proxy for shortability is
LIQUIDITY -- non-shortable U.S. names are overwhelmingly small / low-float /
illiquid ($0 $m ADV). So we DROP the least-liquid `p` fraction of each month's
short decile (by dollar_vol ADV) and renormalize the remaining short weights.
If the short side cannot be filled at all, the short is skipped (exposure gap).

We recompute BOTH legs under the restriction (1y ex1st quarterly book + 1m
ensemble), then run the FULL champion overlay (vol-target + DXY + credit +
MR-union) AND the borrow-cost model at the blended 1.0%/yr, so the realistic
"short-constrained + borrow-paid" champion is reported.

Unrestricted champion (xgb_combo_w1y_opt + xgb_combo_borrow):
  no borrow : SR 1.774  ann +24.8%  dd -16.5%
  1% borrow : SR 1.701  ann +23.6%  dd -17.0%
"""
from __future__ import annotations
import os, sys, json
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import union_panel

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")
COST = 0.0006
MIN_PRICE = 2.0
ENTRY_MONTHS = [2, 5, 8, 11]
W1Y = 0.75
VT_WIN, VT_TGT, VT_CAP = 12, 0.14, 1.5
DXY_Z, DXY_F = 1.5, 0.5
CR_WIN, CR_THR, CR_F2 = 12, 1.3, 0.5
MR_F, MR_MC = 0.4, 1.0

sys.path.insert(0, ROOT)
from tools.quant.hedge_fund_strats.meanrev_episode_research import load_prices_rets, backtest

# annual borrow rate applied on top (blended IBKR center)
BORROW_RATE = 0.01


def stats_monthly(s):
    s = s.dropna()
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 3),
            "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4),
            "win": round(float((s > 0).mean()), 3),
            "n": int(len(s))}


def restrict_shorts(shorts_df, p, liq_col):
    """Drop the least-liquid 'p' fraction of a short-side frame, renormalize."""
    g = shorts_df.dropna(subset=[liq_col])
    if len(g) < 5:
        return g
    g = g.sort_values(liq_col, ascending=True)   # least liquid first
    n_drop = int(round(len(g) * p))
    if n_drop >= len(g):
        n_drop = len(g) - 1
    return g.iloc[n_drop:]


def load_1y_ex1st_monthly(p):
    """Quarterly-ex1st EW t=0.25 book, staggered 12m cohorts, short leg restricted."""
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_xgb_1y_pit.parquet")
    df["month"] = pd.to_datetime(df["month"])
    mclose = union_panel.load_union()["close"].resample("ME").last()
    px = mclose.stack().rename("px_m"); px.index.names = ["month", "ticker"]
    df = df.join(px, on=["month", "ticker"], how="left")

    def form(m):
        g = df[df["month"] == m].dropna(subset=["pred"])
        g = g[g["px_m"] >= MIN_PRICE]
        g = g.sort_values("pred", ascending=False)
        if len(g) < 40:
            return None
        nq = max(int(len(g) * 0.1), 5)
        longs = g.iloc[:nq]
        shorts = restrict_shorts(g.iloc[-nq:], p, "dollar_vol")
        if len(shorts) < 2:
            return None
        return {"entry": m, "longs": list(longs["ticker"]),
                "shorts": list(shorts["ticker"])}

    books = []
    for m in df["month"].unique():
        if m.month in ENTRY_MONTHS and 2009 <= m.year <= 2025:
            b = form(m)
            if b:
                books.append(b)
    port = {}
    for b in books:
        m0 = b["entry"]
        for k in range(12):
            m = m0 + pd.DateOffset(months=k) + pd.offsets.MonthEnd(0)
            g = df[df["month"] == m]
            lr = g[g["ticker"].isin(b["longs"])]["ret_next"].dropna()
            sr = g[g["ticker"].isin(b["shorts"])]["ret_next"].dropna()
            if len(lr) < 5 or len(sr) < 2:
                continue
            pnl = 1.25 * lr.mean() - 0.75 * sr.mean()
            if k == 0:
                pnl -= 4 * COST
            if k == 11:
                pnl -= 4 * COST
            port.setdefault(m, []).append(pnl)
    return pd.Series({m: np.mean(v) for m, v in sorted(port.items())})


def load_1m_monthly(p):
    """1m ensemble book: monthly decile L/S, short leg restricted by ADV."""
    df = pd.read_parquet(f"{HERE}/data/gkx_preds_ens1m.parquet")
    df["month"] = pd.to_datetime(df["month"])
    mclose = union_panel.load_union()["close"].resample("ME").last()
    # build dollar_vol from union close*vol if available
    un = union_panel.load_union()
    dv = (un["close"] * un.get("vol", np.nan)).resample("ME").last().stack().rename("dollar_vol")
    dv.index.names = ["month", "ticker"]
    df = df.join(dv, on=["month", "ticker"], how="left")
    rows = []
    for m, g in df.groupby("month"):
        g = g.dropna(subset=["ens", "ret_next"])
        n = len(g)
        if n < 40:
            continue
        g = g.sort_values("ens", ascending=False)
        nq = max(int(n * 0.1), 5)
        lg = g["ret_next"].iloc[:nq].mean()
        shorts = restrict_shorts(g.iloc[-nq:], p, "dollar_vol")
        if len(shorts) < 2:
            continue
        sg = shorts["ret_next"].mean()
        rows.append((m, lg - sg - 4 * COST))
    return pd.Series(dict(rows)).sort_index()


def main():
    p_sweep = [0.0, 0.1, 0.2, 0.3, 0.4]
    print("=== NON-SHORTABLE MODELING on the champion stack ===")
    print("p = fraction of the short decile assumed NOT shortable (least-liquid dropped)\n")
    rows = []
    for p in p_sweep:
        print(f"building legs p={p:.0%}...", flush=True)
        ys = load_1y_ex1st_monthly(p)
        ms = load_1m_monthly(p)
        legs = pd.concat([ys.rename("y1"), ms.rename("m1")], axis=1).dropna()
        legs = legs[legs.index >= "2009-01-01"]
        combo = W1Y * legs["y1"] + (1 - W1Y) * legs["m1"]

        # MR sleeve
        prices, rets = load_prices_rets()
        mr_d = backtest(prices, rets, 5, 30)
        mr = mr_d.resample("ME").apply(lambda x: (1 + x).prod() - 1)
        mr.index = pd.to_datetime(mr.index)
        al = pd.concat([combo.rename("combo"), mr.reindex(combo.index).rename("mr")], axis=1).dropna()
        combo, mr = al["combo"], al["mr"]

        rv = combo.rolling(VT_WIN, min_periods=VT_WIN - 3).std() * np.sqrt(12)
        sc_vt = (VT_TGT / rv).clip(upper=VT_CAP, lower=0.0).fillna(1.0)
        dxy = pd.read_csv(os.path.join(FRED, "dxy.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
        dm = dxy.rolling(12, min_periods=8).mean(); dsd = dxy.rolling(12, min_periods=8).std()
        dFLAG = (((dxy - dm) / dsd).reindex(combo.index).ffill().shift(1) > DXY_Z).fillna(False)
        dgate = pd.Series(1.0, index=combo.index); dgate[dFLAG] = DXY_F
        aaa = pd.read_csv(os.path.join(FRED, "aaa.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
        baa = pd.read_csv(os.path.join(FRED, "baa.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
        cs = (baa - aaa)
        cz = (cs - cs.rolling(CR_WIN, min_periods=8).mean()) / cs.rolling(CR_WIN, min_periods=8).std()
        cFLAG = (cz.reindex(combo.index).ffill().shift(1) > CR_THR).fillna(False)
        fac = sc_vt * dgate
        fac[cFLAG] *= CR_F2
        champ = combo * fac - fac.diff().abs().fillna(0.0) * 2 * COST
        uFLAG = (dFLAG | cFLAG)
        base = champ + mr * MR_MC * MR_F * uFLAG.astype(float)

        short_notional = fac + MR_F * uFLAG.astype(float) * MR_MC
        borrow = short_notional * BORROW_RATE / 12.0
        final = base - borrow

        no_borrow = stats_monthly(base)
        net = stats_monthly(final)
        rows.append({"p": p, "no_borrow": no_borrow, "with_1pct_borrow": net})
        print(f"  p={p:.0%}: no-borrow SR {no_borrow['sr']} ann {no_borrow['ann']:+.1%} dd {no_borrow['dd']:+.1%}"
              f" | +1% borrow SR {net['sr']} ann {net['ann']:+.1%} dd {net['dd']:+.1%}")

    json.dump({"p_sweep": rows, "borrow_rate_annual": BORROW_RATE,
               "note": "p = fraction of short decile not shortable (least-liquid dropped); "
                       "short weights renormalized over located subset"},
              open(os.path.join(OUT, "xgb_combo_nonshortable.json"), "w"), indent=2, default=str)
    print(f"\nsaved -> {OUT}/xgb_combo_nonshortable.json")


if __name__ == "__main__":
    main()
