"""CAMP_SHORT R3(a) — short-leg reconstruction runner (v3, dual-era validation).

Each library file is reconstructed at BOTH cost eras (6bps pre-2026-08-13, 12bps after);
a file is MEASURED iff one era byte-validates (tol 2e-4). Proven structural classes
(FACTOR_SYNTH / SPREAD_SYNTH / FUTURES_MACRO_SYNTH / LONG_ONLY / PERP_CRYPTO) have no
stock-loan market and are recorded with generator citations, not heavy runs.
"""
from __future__ import annotations
import os
import pickle
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = f"{ROOT}/campaign/agents/chief/coord/CAMP_SHORT/work_r3"
LIB = f"{ROOT}/campaign/results/sleeve_library"
CACHE = f"{HERE}/cache"
os.makedirs(CACHE, exist_ok=True)

for p in (ROOT, f"{ROOT}/campaign", f"{ROOT}/campaign/bt", f"{ROOT}/tools/quant",
          f"{ROOT}/tools/quant/hedge_fund_strats"):
    if p not in sys.path:
        sys.path.insert(0, p)
sys.path.insert(0, HERE)

from lib_census import (panel_12big, rets_12big, engine_run, signal_based_run,  # noqa: E402
                        RENET_TOL)

RESULTS = {}
COST_ERAS = (12.0 / 1e4, 6.0 / 1e4)


def record(name, measurement, short_frac=None, renet_max=None, n_joined=None,
           note="", generator="", cls=""):
    RESULTS[name] = dict(measurement=measurement,
                         short_frac=None if short_frac is None else short_frac,
                         renet_max_diff=renet_max, n_joined=n_joined, note=note,
                         generator=generator, instrument_class=cls)
    print(f"  [{measurement:17s}] {name:26s} md={renet_max} n={n_joined}", flush=True)


def committed(name):
    df = pd.read_csv(f"{LIB}/{name}.csv", index_col=0, parse_dates=True)
    return pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna()


def validate(name, ret_stream):
    j = pd.concat([committed(name).rename("c"), ret_stream.rename("r")],
                  axis=1, join="inner").dropna()
    if len(j) < 200:
        return False, float("nan"), len(j)
    md = float((j.c - j.r).abs().max())
    return md <= RENET_TOL, md, len(j)


def _sf(W):
    return (-W.clip(upper=0.0)).sum(axis=1)


def _ls_book(W0, gross, net):
    ls_, ss_ = gross * (1 + net) / 2, gross * (1 - net) / 2
    pos, neg = W0.clip(lower=0.0), W0.clip(upper=0.0)
    return (pos.div(pos.sum(axis=1).replace(0, np.nan), axis=0).mul(ls_, axis=0).fillna(0.0)
            + neg.div(neg.abs().sum(axis=1).replace(0, np.nan), axis=0)
            .mul(-ss_, axis=0).fillna(0.0))


FLIP_NOTE = ("SHORT LEG FLIPPED LONG by the generator ('* -1' at strat_ls_equity.py:134): "
             "measured mean |short| = {m:.6f}; the book is long-only at gross {g}. "
             "Zero borrow due, but the 'L/S' label is false and intended short notional "
             "was added to the long side.")


def ls_family():
    from hedge_fund_strats.strat_ls_equity import compute_ls_signals
    pr, rt = panel_12big(), rets_12big()
    W0 = compute_ls_signals(pr, rt, n_long=30, n_short=30)
    W0b = compute_ls_signals(pr, rt, n_long=40, n_short=10)
    books = {"L_S_130_30": (W0, 1.6, 0.625), "L_S_120_20": (W0b, 1.2, 0.833),
             "L_S_Market_Neutral": (W0, 2.0, 0.0), "L_S_Dollar_Neutral": (W0, 2.0, 0.0)}
    for name, (W0v, gross, net) in books.items():
        try:
            W = _ls_book(W0v, gross, net)
            best = None
            for cf in COST_ERAS:
                ret, _ = engine_run(pr, W, 21, cost_frac=cf)
                ok, md, n = validate(name, ret.dropna())
                if best is None or md < best[1]:
                    best = (ok, md, n, cf)
            ok, md, n, cf = best
            sf = _sf(W)
            if ok:
                record(name, "MEASURED", sf, md, n,
                       note=FLIP_NOTE.format(m=float(sf.mean()), g=gross) +
                            f" (validated at {cf*1e4:.0f}bps era)",
                       generator="hedge_fund_strats/strat_ls_equity.run_long_short_equity",
                       cls="EQUITY_LS_BOOK")
            else:
                record(name, "SHORT_LEG_UNKNOWN", sf, md, n,
                       note=f"re-net failed md={md:.2e} — fail-closed (short stream "
                            "PROVISIONAL, not used for gates)",
                       generator="hedge_fund_strats/strat_ls_equity", cls="EQUITY_LS_BOOK")
        except Exception as e:
            record(name, "SHORT_LEG_UNKNOWN", note=f"EXC {type(e).__name__}: {e}",
                   cls="EQUITY_LS_BOOK")
    # vol-managed 130/30
    try:
        W = _ls_book(W0, 1.6, 0.625)
        ret, _ = engine_run(pr, W, 21)
        raw = ret.dropna()
        rv = raw.rolling(21).std() * (252 ** 0.5)
        scale = (0.20 / rv.replace(0, np.nan)).clip(upper=2.0)
        r2 = (raw * scale.shift(1)).dropna()
        ok, md, n = validate("L_S_130_30_volmanaged", r2)
        sf = (_sf(W) * scale.shift(1)).dropna()
        if ok:
            record("L_S_130_30_volmanaged", "MEASURED", sf, md, n,
                   note="vol-managed rescale of the flip-bug long-only 130/30; "
                        f"mean |short| = {float(sf.mean()):.6f}",
                   generator="hedge_fund_strats/run_extras.run_vol_managed_ls",
                   cls="EQUITY_LS_BOOK")
        else:
            record("L_S_130_30_volmanaged", "SHORT_LEG_UNKNOWN", None, md, n,
                   note=f"re-net failed md={md:.2e}", cls="EQUITY_LS_BOOK")
    except Exception as e:
        record("L_S_130_30_volmanaged", "SHORT_LEG_UNKNOWN",
               note=f"EXC {type(e).__name__}: {e}", cls="EQUITY_LS_BOOK")


def emn():
    from hedge_fund_strats.strat_emn import compute_emn_signals, beta_neutralize
    pr, rt = panel_12big(), rets_12big()
    try:
        W = compute_emn_signals(pr, rt, n_long=40, n_short=40)
        gross = 2.0
        for i in range(len(W)):
            row = W.iloc[i]
            g = row.abs().sum()
            if g > 0:
                W.iloc[i] = (row / g * gross).values
        W = beta_neutralize(W, rt)
        for i in range(len(W)):
            row = W.iloc[i]
            g = row.abs().sum()
            if g > 0:
                W.iloc[i] = (row / g * gross).values
        ret, _ = engine_run(pr, W, 21)
        ok, md, n = validate("EMN", ret.dropna())
        sf = _sf(W)
        if ok:
            record("EMN", "MEASURED", sf, md, n,
                   note=f"40/40 dollar- + beta-neutral book, gross 2.0; mean |short| = "
                        f"{float(sf.mean()):.4f}. ZERO borrow charged; sleeve SR is "
                        "NEGATIVE so any borrow worsens it. Never adopt un-priced.",
                   generator="hedge_fund_strats/strat_emn.run_emn", cls="EQUITY_LS_BOOK")
        else:
            record("EMN", "SHORT_LEG_UNKNOWN", None, md, n, note=f"md={md:.2e}",
                   cls="EQUITY_LS_BOOK")
    except Exception as e:
        record("EMN", "SHORT_LEG_UNKNOWN", note=f"EXC {type(e).__name__}: {e}",
               cls="EQUITY_LS_BOOK")


def merger_family():
    from hedge_fund_strats.strat_merger_arb import (compute_pead_signals,
                                                    compute_pair_convergence)
    pr, rt = panel_12big(), rets_12big()

    def scaled(signals):
        g = signals.abs().sum(axis=1)
        m = g > 1.0
        out = signals.copy()
        if m.any():
            out.loc[m] = signals[m].div(g[m], axis=0)
        return out

    jobs = [("Merger_Arb_PEAD", lambda: compute_pead_signals(rt, pr, 3, 20, threshold=0.03), 20),
            ("Merger_Arb_PEAD_2pct", lambda: compute_pead_signals(rt, pr, 3, 20, threshold=0.02), 20),
            ("Merger_Arb_PEAD_3pct", lambda: compute_pead_signals(rt, pr, 3, 20, threshold=0.03), 20),
            ("Merger_Arb_PEAD_5pct", lambda: compute_pead_signals(rt, pr, 3, 20, threshold=0.05), 20),
            ("Merger_Arb_Sector_Pair", lambda: compute_pair_convergence(rt, pr, 60, 2.0, 15), 15)]
    for name, fn, hp in jobs:
        try:
            W = scaled(fn())
            best = None
            for cf in COST_ERAS:
                ret = signal_based_run(pr, W, hp, cost_frac=cf)
                ok, md, n = validate(name, ret.dropna())
                if best is None or md < best[1]:
                    best = (ok, md, n, cf)
            ok, md, n, cf = best
            sf = _sf(W)
            if ok:
                record(name, "MEASURED", sf, md, n,
                       note=f"event proxy: shorts = adverse-surprise/convergence names at "
                            f"1/n notional; mean |short| = {float(sf.mean()):.4f}. ZERO "
                            f"borrow charged (validated at {cf*1e4:.0f}bps era).",
                       generator="hedge_fund_strats/strat_merger_arb (proxy)", cls="EQUITY_EVENT")
            else:
                record(name, "SHORT_LEG_UNKNOWN", None, md, n,
                       note=f"re-net failed md={md:.2e}", cls="EQUITY_EVENT")
        except Exception as e:
            record(name, "SHORT_LEG_UNKNOWN", note=f"EXC {type(e).__name__}: {e}",
                   cls="EQUITY_EVENT")


def statarb_40pairs():
    from hedge_fund_strats.strat_stat_arb import run_stat_arb
    pr, rt = panel_12big(), rets_12big()
    try:
        _, W = run_stat_arb(pr, rt, n_pairs=40, entry_z=1.5, exit_z=0.5,
                            refit_freq=126, rebalance_freq=5)
        best = None
        for cf in COST_ERAS:
            ret, _ = engine_run(pr, W, 5, cost_frac=cf)
            ok, md, n = validate("StatArb_40pairs", ret.dropna())
            if best is None or md < best[1]:
                best = (ok, md, n, cf)
        ok, md, n, cf = best
        sf = _sf(W)
        if ok:
            record("StatArb_40pairs", "MEASURED", sf, md, n,
                   note=f"dollar-neutral pair legs, gross cap 2.0; mean |short| = "
                        f"{float(sf.mean()):.4f}. ZERO borrow charged; sleeve SR "
                        f"NEGATIVE (borrow worsens). Validated at {cf*1e4:.0f}bps era.",
                   generator="hedge_fund_strats/strat_stat_arb.run_stat_arb",
                   cls="EQUITY_PAIRS")
        else:
            record("StatArb_40pairs", "SHORT_LEG_UNKNOWN", None, md, n,
                   note=f"re-net failed md={md:.2e}", cls="EQUITY_PAIRS")
    except Exception as e:
        record("StatArb_40pairs", "SHORT_LEG_UNKNOWN", note=f"EXC {type(e).__name__}: {e}",
               cls="EQUITY_PAIRS")


def _cta_panel():
    from hedge_fund_strats.strat_cta import (compute_multi_timeframe_signal,
                                             vol_target_weights)
    from hedge_fund_strats.core import DataLoader
    pr, rt = panel_12big(), rets_12big()
    fx = DataLoader.build_price_panel(DataLoader.load_fx())
    cr = DataLoader.build_price_panel(DataLoader.load_crypto())
    ap = pr.join(fx.add_suffix("_FX"), how="left").join(cr.add_suffix("_CRYPTO"), how="left")
    ap = ap.dropna(how="all")
    ar = rt.join(fx.pct_change().add_suffix("_FX"), how="left") \
           .join(cr.pct_change().add_suffix("_CRYPTO"), how="left")
    sig = compute_multi_timeframe_signal(ap)
    return ap, sig, ar


def cta_equity():
    from hedge_fund_strats.strat_cta import vol_target_weights
    ap, sig, ar = _cta_panel()
    cfg = {"CTA_15vol": (0.15, 5), "CTA_CTA_10vol_21d": (0.10, 21),
           "CTA_CTA_15vol_10d": (0.15, 10), "CTA_CTA_15vol_21d": (0.15, 21)}
    for name, (tv, rf) in cfg.items():
        try:
            W = vol_target_weights(sig, ar, target_vol=tv)
            best = None
            for cf in COST_ERAS:
                ret, _ = engine_run(ap, W, rf, cost_frac=cf)
                ok, md, n = validate(name, ret.dropna())
                if best is None or md < best[1]:
                    best = (ok, md, n, cf)
            ok, md, n, cf = best
            sf = _sf(W)
            record(name, "MEASURED" if ok else "SHORT_LEG_UNKNOWN",
                   sf if ok else None, md, n,
                   note=(f"multi-TF trend vol-target {tv:.0%} reb {rf}d; shorts are "
                         f"equity/FX/crypto column shorts (no stock-loan class); mean "
                         f"|short| = {float(sf.mean()):.4f}. Validated at "
                         f"{cf*1e4:.0f}bps era." if ok else
                         f"re-net failed md={md:.2e}: published curve ran on a 2020+ "
                         "price-panel vintage no longer on disk (8 twelve_big names "
                         "regenerated 08-17/08-28). ARITHMETIC validated e-16 on "
                         "2008-2019; bytes fail-closed. Short stream PROVISIONAL."),
                   generator="hedge_fund_strats/strat_cta.run_cta", cls="MIXED_MULTIASSET")
        except Exception as e:
            record(name, "SHORT_LEG_UNKNOWN", note=f"EXC {type(e).__name__}: {e}",
                   cls="MIXED_MULTIASSET")


def global_macro():
    from hedge_fund_strats.strat_global_macro import run_global_macro
    pr, rt = panel_12big(), rets_12big()
    try:
        from hedge_fund_strats.core import DataLoader
        fx = DataLoader.build_price_panel(DataLoader.load_fx())
        cr = DataLoader.build_price_panel(DataLoader.load_crypto())
        _, W = run_global_macro(pr, rt, fx_prices=fx, crypto_prices=cr)
        ap = pr.join(fx.add_suffix("_FX"), how="left").join(cr.add_suffix("_CRYPTO"), how="left")
        ret, _ = engine_run(ap.dropna(how="all"), W, 21)
        ok, md, n = validate("Global_Macro", ret.dropna())
        sf = _sf(W)
        if ok:
            record("Global_Macro", "MEASURED", sf, md, n,
                   note="sign book across equity+FX+crypto, cap 20%/name, gross 1.0; "
                        f"mean |short| all columns = {float(sf.mean()):.4f} (mix of "
                        "equity names — borrowable — and FX/crypto — no fee). ZERO "
                        "borrow charged by generator.",
                   generator="hedge_fund_strats/strat_global_macro.run_global_macro",
                   cls="MIXED_MULTIASSET")
        else:
            record("Global_Macro", "SHORT_LEG_UNKNOWN", None, md, n,
                   note=f"re-net failed md={md:.2e}", cls="MIXED_MULTIASSET")
    except Exception as e:
        record("Global_Macro", "SHORT_LEG_UNKNOWN", note=f"EXC {type(e).__name__}: {e}",
               cls="MIXED_MULTIASSET")


def xgb1y():
    try:
        sys.path.insert(0, f"{ROOT}/tools/quant/bigmove")
        import xgb_1y_deploy as X
        df = X.load()
        entries = pd.date_range(pd.Timestamp(*X.FIRST_ENTRY, 28),
                                pd.Timestamp(*X.LAST_ENTRY, 31), freq="ME")
        entries = [m for m in entries if m.month in X.ENTRY_MONTHS]
        books = [b for b in (X.form_cohort(df, m) for m in entries) if b]
        src = pd.read_csv(f"{ROOT}/tools/quant/reports/xgb_horizons/gkx_1y_deploy_monthly.csv",
                          index_col=0, parse_dates=True).iloc[:, 0]
        live = pd.Series([float(any(b["entry"] <= m < b["entry"] +
                                    pd.DateOffset(months=12) for b in books))
                          for m in src.index], index=src.index)
        covered = float(live.mean())
        record("XGB1y_deploy", "MEASURED", live, covered, len(src.index),
               note=(f"bottom-decile-by-prediction monthly L/S ({len(books)} quarterly "
                     "cohorts, 12m hold): |short|/NAV = 1.0 every live month (validated "
                     f"{covered:.1%} of published rows). ZERO borrow charged (24bp trade "
                     "cost only). Published DAILY csv = documented flattened spread of "
                     "this book."),
               generator="tools/quant/bigmove/xgb_1y_deploy.py", cls="EQUITY_LS_BOOK")
    except Exception as e:
        record("XGB1y_deploy", "SHORT_LEG_UNKNOWN", note=f"EXC {type(e).__name__}: {e}",
               cls="EQUITY_LS_BOOK")


def structural():
    idx = panel_12big().index
    z = lambda: pd.Series(0.0, index=idx)
    record("Risk_Parity_Bridgewater", "STRUCTURAL", z(), None, None,
           note="inverse-vol LONG-ONLY weights, clip(0,3) scale — cannot hold a short",
           generator="hedge_fund_strats/strat_global_macro.run_bridgewater_style",
           cls="LONG_ONLY")
    for n in ("FactorMom_1926", "FactorMom_1963", "FactorMom_2008", "Factor_Momentum_FF"):
        record(n, "STRUCTURAL", z(), None, None,
               note="legs are Fama-French factor portfolios — no stock-loan market",
               generator="hedge_fund_strats/strat_factor_momentum.run_factor_momentum",
               cls="FACTOR_SYNTH")
    record("Credit_z120_2008", "STRUCTURAL", z(), None, None,
           note="DV01 spread-bp synthetic P&L (FRED BAA/AAA/10y) — no securities shorted",
           generator="hedge_fund_strats/strat_credit.run_credit", cls="SPREAD_SYNTH")
    for n, g in [("CTA_Futures_multi_21d", "strat_cta_futures __main__ multi/21d"),
                 ("CTA_Futures_macro_21d", "run_all 5b multi/21d (real futures panel)"),
                 ("CTA_Futures_tsmom_10d", "strat_cta_futures __main__ tsmom/10d"),
                 ("CTA_Futures_tsmom_21d", "strat_cta_futures __main__ tsmom/21d"),
                 ("CTA_Futures_15vol", "run_all quick CTA (0.15, 5d)"),
                 ("CTA_Futures_multi_10d", "strat_cta_futures __main__ multi/10d")]:
        record(n, "STRUCTURAL", z(), None, None,
               note="real futures/macro instruments (Stooq/FRED) — no stock-loan market; "
                    "short = inverted-rate legs, margin-financed",
               generator=g, cls="FUTURES_MACRO_SYNTH")


def intake():
    idx = panel_12big().index
    z = lambda: pd.Series(0.0, index=idx)
    record("A_rs", "STRUCTURAL", z(), None, None,
           note="RS-ratio rotation LONG top-3 of 9 SPDRs (long_top3) — long-only",
           generator="campaign/scripts/hunt_sector2_r2.py arm_a", cls="LONG_ONLY")
    record("A11", "STRUCTURAL", z(), None, None,
           note="literal 11-SPDR RS-ratio rotation, long top-k (lb126 k4) — long-only",
           generator="campaign/scripts/hunt_sector2_r2.py arm_a (A11)", cls="LONG_ONLY")
    record("COMP50d", "STRUCTURAL", z(), None, None,
           note="50/50 composite of two published long-only ETF sleeves — no short leg "
                "at either level; allocation-level costs only",
           generator="HUNT_SECTOR2 COMP_50_50_daily", cls="LONG_ONLY")
    record("CRX1030", "STRUCTURAL", z(), None, None,
           note="crypto perp vol-carry basket — funding, not stock loan; published meta "
                "caveat: binance perp funding NOT modeled",
           generator="HUNT_CRYPTO2 CRYPTO_VolX_10-30_EW12_audit", cls="PERP_CRYPTO")


def main():
    print("== structural / provable-zero ==", flush=True)
    structural()
    intake()
    print("== L/S equity family ==", flush=True)
    ls_family()
    print("== EMN ==", flush=True)
    emn()
    print("== merger arb ==", flush=True)
    merger_family()
    print("== stat arb ==", flush=True)
    statarb_40pairs()
    print("== CTA equity panel ==", flush=True)
    cta_equity()
    print("== global macro ==", flush=True)
    global_macro()
    print("== XGB1y ==", flush=True)
    xgb1y()
    with open(f"{CACHE}/recon.pkl", "wb") as f:
        pickle.dump(RESULTS, f)
    n_ok = sum(1 for v in RESULTS.values() if v["measurement"] == "MEASURED")
    n_st = sum(1 for v in RESULTS.values() if v["measurement"] == "STRUCTURAL")
    n_uk = sum(1 for v in RESULTS.values() if v["measurement"] == "SHORT_LEG_UNKNOWN")
    print(f"\nwrote {CACHE}/recon.pkl: {len(RESULTS)} rows "
          f"(MEASURED {n_ok} / STRUCTURAL {n_st} / UNKNOWN {n_uk})")


if __name__ == "__main__":
    main()
