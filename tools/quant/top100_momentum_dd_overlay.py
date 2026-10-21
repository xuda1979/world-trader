"""Layered drawdown-crusher overlays for the top-100 momentum book.

Goal: get MaxDD far below the credit-gate-only -31.8% by stacking levers:
  credit   BAA-AAA spread >= trailing-252d p85        -> exposure f
  spx_sma  SPY < N-day SMA (lagged 1d)                -> exposure f
  vix_stop VIX >= T (lagged 1d)                       -> exposure f
  voltgt   scale = min(scale, target / realized 20d vol of the book)
  dd_stop  own equity DD < -8% -> 0.5, < -12% -> 0.25
  cash     de-risked fraction earns 3m T-bill (monthly, ffilled)

All gates lagged 1 day (no lookahead). One-side toggle cost (3.8bp) charged
on every exposure change. Book is the unchanged monthly top-100 walk
(monthly rebalance costs already inside).

Output: tools/quant/reports/top100_momentum_dd_overlay.json
"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monthly_top100_momentum import prepare, walk_forward, stats, COST_ONE_SIDE
from top100_momentum_regime_filter import load_fred, exposure_pct

ROOT = "/Users/daxu/software/world-trader"
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats/data_fred")
OUTDIR = os.path.join(ROOT, "tools/quant/reports")


def gate_from_bool(cond, f, idx):
    """1 where cond True, f where cond False (cond = 'stay invested')."""
    c = cond.shift(1).reindex(idx).ffill().fillna(True)
    return c.astype(float) * (1.0 - f) + f


def overlay(book_r, gates, cash_r, vol_target=None, dd_map=None):
    """Daily loop: exposure = product of gates, capped by vol target and own-DD
    stop; de-risked fraction earns cash. Returns (final returns, exposure)."""
    n = len(book_r)
    gvals = [g.values for g in gates]
    br = book_r.values
    cr = cash_r.values
    exp = np.empty(n)
    ret = np.empty(n)
    prev_e = 1.0
    eq = 1.0
    peak = 1.0
    for i in range(n):
        e = 1.0
        for gv in gvals:
            e *= gv[i]
        if vol_target is not None and i >= 20:
            v = br[i - 20:i].std() * np.sqrt(252)
            if v > 0:
                e = min(e, vol_target / v)
        if dd_map is not None and i > 0:
            e = min(e, dd_map(eq / peak - 1.0))
        exp[i] = e
        ret[i] = br[i] * e - abs(e - prev_e) * COST_ONE_SIDE \
            + (1.0 - e) * cr[i]
        prev_e = e
        eq *= (1.0 + ret[i])
        peak = max(peak, eq)
    idx = book_r.index
    return pd.Series(ret, index=idx), pd.Series(exp, index=idx)


def yearly_mdd(r):
    out = {}
    for y, g in r.groupby(r.index.year):
        eq = (1 + g).cumprod()
        out[y] = float((eq / eq.cummax() - 1).min())
    return out


def cum_in_window(r, d0, d1):
    r = r[(r.index > d0) & (r.index <= d1)]
    return float((1 + r).prod() - 1) if len(r) else None


def main():
    prices, ret, sharpe, rdates = prepare()
    idx = prices.index
    book_r, _, _ = walk_forward(prices, ret, sharpe, rdates)  # unscaled book

    # baseline worst-DD window (2008-09) for targeted scoring
    b_s, b_ann, b_vol, b_dd, b_n = stats(book_r)
    base_eq = (1 + book_r).cumprod()
    trough_i = (base_eq / base_eq.cummax() - 1).idxmin()
    peak_i = base_eq.loc[:trough_i].idxmax()
    print(f"book: SR {b_s:.3f} MaxDD {b_dd:.2%} "
          f"DDwin {peak_i.date()}->{trough_i.date()}")

    # ---- gate inputs (all lagged inside gate_from_bool / exposure_pct) ----
    vix = load_fred("vix.csv")
    baa = load_fred("baa.csv")
    aaa = load_fred("aaa.csv")
    spread = (baa - aaa).dropna()
    spy = pd.read_csv(os.path.join(ROOT, "tools/quant/data/twelve_big", "SPY.csv"),
                      parse_dates=["date"]).set_index("date")["close"]
    spy = spy.reindex(book_r.index).ffill()

    credit30 = exposure_pct(spread, book_r.index, 0.85, 0.3)
    credit0 = exposure_pct(spread, book_r.index, 0.85, 0.0)
    s100 = gate_from_bool(spy > spy.rolling(100).mean(), 0.0, book_r.index)
    s200 = gate_from_bool(spy > spy.rolling(200).mean(), 0.0, book_r.index)
    v32 = gate_from_bool(vix < 32, 0.0, book_r.index)
    v35 = gate_from_bool(vix < 35, 0.0, book_r.index)

    # cash: monthly 3m T-bill (percent) -> daily, ffilled
    tb = load_fred("tbill3m.csv") / 100.0
    cash_r = (tb / 252.0).reindex(book_r.index).ffill().fillna(0.0)

    dd_map = lambda dd: 1.0 if dd > -0.08 else (0.5 if dd > -0.12 else 0.25)

    configs = [
        ("book_only", []),
        ("credit30", [credit30]),
        ("credit0", [credit0]),
        ("s200", [s200]),
        ("s200_v32", [s200, v32]),
        ("credit30_s200", [credit30, s200]),
        ("credit30_s200_v32", [credit30, s200, v32]),
        ("credit30_s200_v32_vt15", [credit30, s200, v32], 0.15),
        ("credit30_s200_v32_vt12", [credit30, s200, v32], 0.12),
        ("credit30_s200_v32_vt10", [credit30, s200, v32], 0.10),
        ("credit30_s200_v32_vt12_dd", [credit30, s200, v32], 0.12, dd_map),
        ("credit0_s200_v32_vt12", [credit0, s200, v32], 0.12),
        ("credit0_s200_v35_vt12", [credit0, s200, v35], 0.12),
        ("s200_v32_vt12", [s200, v32], 0.12),
        ("s100_v32_vt12", [s100, v32], 0.12),
        ("dd_only", [], None, dd_map),
    ]

    rows = []
    for cfg in configs:
        name, gates = cfg[0], cfg[1]
        vt = cfg[2] if len(cfg) > 2 else None
        dd = cfg[3] if len(cfg) > 3 else None
        r, exp = overlay(book_r, gates, cash_r, vol_target=vt, dd_map=dd)
        s, ann, vol, mdd, n = stats(r)
        h = len(r) // 2
        s1, *_ = stats(r.iloc[:h])
        s2, *_ = stats(r.iloc[h:])
        ymdd = yearly_mdd(r)
        rows.append({
            "name": name,
            "sharpe": round(s, 3),
            "ann_ret": round(ann, 6),
            "ann_vol": round(vol, 6),
            "maxdd": round(mdd, 6),
            "split_half": [round(s1, 3), round(s2, 3)],
            "ddwin_0809": cum_in_window(r, peak_i, trough_i),
            "mdd_2020": ymdd.get(2020),
            "mdd_2008": ymdd.get(2008),
            "mdd_2022": ymdd.get(2022),
            "ret_2022": float((1 + r[r.index.year == 2022]).prod() - 1),
            "pct_invested": round(float((exp > 0.99).mean()), 4),
            "n_toggles": int((exp.diff().abs() > 1e-9).sum()),
            "yearly": {y: round((1 + g).prod() - 1, 4)
                       for y, g in r.groupby(r.index.year)},
        })

    print(f"\n{'config':<28}{'SR':>6}{'ann':>8}{'vol':>7}{'MaxDD':>8}"
          f"{'0809win':>9}{'2020':>8}{'2022':>8}{'half':>11}{'%in':>6}{'tgl':>5}")
    for r in sorted(rows, key=lambda x: x["maxdd"]):
        print(f"{r['name']:<28}{r['sharpe']:>6.3f}{r['ann_ret']:>8.2%}"
              f"{r['ann_vol']:>7.2%}{r['maxdd']:>8.2%}{r['ddwin_0809']:>9.2%}"
              f"{r['mdd_2020']:>8.2%}{r['ret_2022']:>8.2%}"
              f"{r['split_half'][0]:>5.2f}/{r['split_half'][1]:<5.2f}"
              f"{r['pct_invested']:>6.2%}{r['n_toggles']:>5d}")

    with open(os.path.join(OUTDIR, "top100_momentum_dd_overlay.json"), "w") as f:
        json.dump({
            "book_baseline": {
                "sharpe": round(b_s, 3), "ann_ret": round(b_ann, 6),
                "ann_vol": round(b_vol, 6), "maxdd": round(b_dd, 6),
                "dd_window": [str(peak_i.date()), str(trough_i.date())],
            },
            "configs": rows,
        }, f, indent=2)
    print(f"\nsaved -> {OUTDIR}/top100_momentum_dd_overlay.json")


if __name__ == "__main__":
    main()
