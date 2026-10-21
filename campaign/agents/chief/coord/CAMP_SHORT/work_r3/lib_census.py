"""CAMP_SHORT R3(a) — library borrow census: short-leg reconstruction.

For each sleeve the short-leg notional stream |short|/NAV is reconstructed from its
frozen generator, then re-netted against the committed sleeve CSV (tol 2e-4, the
float/CSV round-trip bound). Every reconstruction either validates or the sleeve is
flagged SHORT_LEG_UNKNOWN / NOT_INTEGRABLE (fail-closed, loud) — never guessed.

Instrument-class census (evidence = the generator source cited per row):
  EQUITY_LS_BOOK   single-name equity long/short (BacktestEngine, ZERO borrow charged)
  EQUITY_PAIRS     dollar-neutral pair legs on single names (same engine, zero borrow)
  EQUITY_EVENT     PEAD proxy long/short single names (same engine, zero borrow)
  FACTOR_SYNTH     legs are Fama-French factor portfolios (no stock loan exists)
  SPREAD_SYNTH     legs are synthetic spread paths / DV01 units (no stock loan)
  FUTURES_MACRO_SYNTH  CTA/macro book on futures & spot proxies (no stock loan)
  LONG_ONLY        construction cannot express a short (inverse-vol risk parity)
  PERP_CRYPTO      crypto perp (funding, not stock loan — published caveat)
  CALLRATE_FINANCED  ls/n10r14: charges (DFF-rebate)+ETB borrow inside the generator
"""
from __future__ import annotations
import os
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
for p in (ROOT, f"{ROOT}/campaign", f"{ROOT}/tools/quant", f"{ROOT}/tools/quant/ls",
          f"{ROOT}/alphaportfolio_replication", f"{ROOT}/tools/quant/bigmove",
          f"{ROOT}/campaign/agents/A3_xs_quality",
          f"{ROOT}/campaign/agents/loop_team/HUNT_CARRYFX/scratch",
          f"{ROOT}/campaign/agents/chief/coord/HUNT_CMDT2"):
    if p not in sys.path:
        sys.path.insert(0, p)

from bt import metrics as M  # noqa: E402
ANN = 252.0
RENET_TOL = 2e-4

# ------------------------------------------------------------------ data loaders
_D12 = None


def panel_12big() -> pd.DataFrame:
    """twelve_big close panel exactly as the suite builds it (run_all.prepare_data)."""
    global _D12
    if _D12 is None:
        from hedge_fund_strats.core import DataLoader
        eq = DataLoader.load_equities(source="twelve_big", min_rows=1000)
        pr = DataLoader.build_price_panel(eq)
        pr = pr[pr.index >= "2008-01-01"].dropna(how="all")
        pr = pr.ffill(limit=5)
        nf = pr.isna().mean()
        pr = pr[nf[nf < 0.3].index.tolist()]
        _D12 = pr
    return _D12


def rets_12big() -> pd.DataFrame:
    from hedge_fund_strats.core import DataLoader
    return DataLoader.build_return_panel(panel_12big(), method="simple")


# ------------------------------------------------------------------ engine shim
def engine_run(prices: pd.DataFrame, weights: pd.DataFrame, rebalance_freq: int,
               cost_frac: float = 12.0 / 1e4):
    """Verbatim BacktestEngine.run arithmetic (core.py:352-384), returning the daily
    EQUITY-CURVE growth rate — the exact object saved as `equity_*.csv` and re-exported
    as library `ret = curve.pct_change()`. Ordering matters and is preserved: MTM first,
    THEN curve append, THEN rebalance (cost deducted after the append, so it first
    appears in tomorrow's growth rate)."""
    w = weights.reindex(index=prices.index, columns=prices.columns).ffill()
    w_current = pd.Series(0.0, index=prices.columns)
    equity = 1.0
    curve = []
    tot = 0.0
    last = -999
    for i, date in enumerate(prices.index):
        if i > 0:
            pr = (prices.iloc[i] / prices.iloc[i - 1] - 1).fillna(0.0)
            equity *= (1.0 + float((w_current * pr).sum()))
        curve.append(equity)
        if (i - last >= rebalance_freq) and (i > 0) and (i < len(prices) - 1):
            wt = w.iloc[i].fillna(0.0)
            to = float((wt - w_current).abs().sum())
            tot += to
            equity -= to * cost_frac * equity
            w_current = wt.copy()
            last = i
    curve = pd.Series(curve, index=prices.index)
    return curve.pct_change(), tot


def vol_target(raw: pd.Series):
    """B2 gates vol target — the family's published-net convention."""
    from bt.gates import vol_target as vt
    return vt(raw)


def renet(raw: pd.Series, committed: pd.Series):
    """Inner-join compare of two daily streams. Returns (ok, max_diff, n)."""
    j = pd.concat([committed.rename("c"), raw.rename("n")], axis=1, join="inner").dropna()
    if len(j) < 200:
        return False, float("nan"), len(j)
    md = float((j.c - j.n).abs().max())
    return md <= RENET_TOL, md, len(j)


def signal_based_run(prices: pd.DataFrame, signals: pd.DataFrame, holding_period: int,
                     cost_frac: float = 12.0 / 1e4):
    """Verbatim BacktestEngine.run_signal_based (core.py:399-443) — used by the merger
    arb proxy: EW across active signals each rebalance, held `holding_period`."""
    signals = signals.reindex(index=prices.index, columns=prices.columns).ffill()
    equity = 1.0
    w_cur = pd.Series(0.0, index=prices.columns)
    curve = []
    dsr = 0
    for i, date in enumerate(prices.index):
        if i > 0:
            prt = (prices.iloc[i] / prices.iloc[i - 1] - 1).fillna(0.0)
            equity *= (1.0 + float((w_cur * prt).sum()))
        curve.append(equity)
        dsr += 1
        if dsr >= holding_period and i < len(prices) - 1:
            sig = signals.iloc[i].fillna(0.0)
            n_active = int((sig != 0).sum())
            w_t = sig / n_active if n_active > 0 else pd.Series(0.0, index=prices.columns)
            to = float((w_t - w_cur).abs().sum())
            equity -= to * cost_frac * equity
            w_cur = w_t.copy()
            dsr = 0
    return pd.Series(curve, index=prices.index).pct_change()


# ------------------------------------------------------------------ generators
def gen_l_130_30(which: str):
    """strat_ls_equity variants: 130/30, 120/20, Dollar_Neutral (post-fix names)."""
    from strat_ls_equity import run_long_short_equity, compute_ls_signals
    pr, rt = panel_12big(), rets_12big()
    cfg = {"130_30": dict(gross_leverage=1.6, net_exposure=0.625, n_long=30, n_short=30),
           "120_20": dict(gross_leverage=1.2, net_exposure=0.833, n_long=40, n_short=10),
           "Dollar_Neutral": dict(gross_leverage=2.0, net_exposure=0.0, n_long=30, n_short=30)}[which]
    w = compute_ls_signals(pr, rt, n_long=cfg["n_long"], n_short=cfg["n_short"])
    ls = cfg["gross_leverage"] * (1 + cfg["net_exposure"]) / 2
    ss = cfg["gross_leverage"] * (1 - cfg["net_exposure"]) / 2
    pos = w.clip(lower=0.0)
    neg = w.clip(upper=0.0)
    w = pos.div(pos.sum(axis=1).replace(0, np.nan), axis=0).mul(ls, axis=0).fillna(0.0) \
        + neg.div(neg.abs().sum(axis=1).replace(0, np.nan), axis=0).mul(-ss, axis=0).fillna(0.0)
    raw, _ = engine_run(pr, w, 21)
    short_frac = (-w.clip(upper=0.0)).sum(axis=1)
    return raw, short_frac


def gen_market_neutral():
    """The committed 'Market Neutral' variant: gross 2.0 net 0.0 n=30/30 (suite commit
    c0f75c0 strat_ls_equity.run_ls_variants, before the Dollar_Neutral rename)."""
    return gen_l_130_30("Dollar_Neutral")


def gen_volmanaged_130_30():
    """run_extras.run_vol_managed_ls: ex-post rescale of the 130/30 net stream."""
    from strat_ls_equity import run_long_short_equity  # noqa: F401 (provenance)
    raw, sf = gen_l_130_30("130_30")
    rv = raw.rolling(21).std() * (252 ** 0.5)
    scale = (0.20 / rv.replace(0, np.nan)).clip(upper=2.0)
    r2 = (raw * scale.shift(1)).dropna()
    # short frac scales identically
    return r2, (sf * scale.shift(1)).dropna()


def gen_emn():
    from strat_emn import run_emn
    pr, rt = panel_12big(), rets_12big()
    _, w = run_emn(pr, rt, n_long=40, n_short=40, gross_leverage=2.0,
                   rebalance_freq=21, beta_neutral=True)
    raw, _ = engine_run(pr, w, 21)
    return raw, (-w.clip(upper=0.0)).sum(axis=1)


def gen_merger_arb(threshold: float, label: str):
    from strat_merger_arb import run_merger_arb_proxy
    pr, rt = panel_12big(), rets_12big()
    _, w = run_merger_arb_proxy(pr, rt, method="pead", threshold=threshold,
                                holding_period=20)
    raw, _ = engine_run(pr, w, 21)
    return raw, (-w.clip(upper=0.0)).sum(axis=1)


def gen_merger_pair():
    from strat_merger_arb import run_merger_arb_proxy
    pr, rt = panel_12big(), rets_12big()
    _, w = run_merger_arb_proxy(pr, rt, method="pair", holding_period=15)
    raw, _ = engine_run(pr, w, 21)
    return raw, (-w.clip(upper=0.0)).sum(axis=1)


def gen_statarb(n_pairs: int, entry_z: float, exit_z: float):
    from strat_stat_arb import run_stat_arb
    pr, rt = panel_12big(), rets_12big()
    _, w = run_stat_arb(pr, rt, n_pairs=n_pairs, entry_z=entry_z, exit_z=exit_z,
                        refit_freq=126, rebalance_freq=5)
    raw, _ = engine_run(pr, w, 5)
    return raw, (-w.clip(upper=0.0)).sum(axis=1)


def gen_cta_equity(variant: str):
    """CTA variants on the equity/FX/crypto panel: signal via frozen arithmetic."""
    from strat_cta import compute_multi_timeframe_signal, vol_target_weights
    pr, rt = panel_12big(), rets_12big()
    from core import DataLoader
    fx = DataLoader.build_price_panel(DataLoader.load_fx())
    cr = DataLoader.build_price_panel(DataLoader.load_crypto())
    ap = pr.copy()
    ar = rt.copy()
    if fx is not None and len(fx) > 100:
        fxa = fx.reindex(ap.index).ffill()
        ap = ap.join(fxa.add_suffix("_FX"), how="left")
        ar = ar.join(fxa.pct_change().add_suffix("_FX"), how="left")
    if cr is not None and len(cr) > 100:
        cra = cr.reindex(ap.index).ffill()
        ap = ap.join(cra.add_suffix("_CRYPTO"), how="left")
        ar = ar.join(cra.pct_change().add_suffix("_CRYPTO"), how="left")
    sig = compute_multi_timeframe_signal(ap)
    w = vol_target_weights(sig, ar, target_vol={"CTA_15vol": 0.15, "CTA_CTA_10vol_21d": 0.10,
                                                "CTA_CTA_15vol_10d": 0.15, "CTA_CTA_15vol_21d": 0.15}[variant])
    rfq = {"CTA_15vol": 5, "CTA_CTA_10vol_21d": 21, "CTA_CTA_15vol_10d": 10, "CTA_CTA_15vol_21d": 21}[variant]
    raw, _ = engine_run(ap.dropna(how="all"), w, rfq)
    return raw, (-w.clip(upper=0.0)).sum(axis=1)


def gen_cta_futures(variant: str):
    """CTA on real futures/macro (Stooq/FRED) — no stock loan exists."""
    from strat_cta_futures import run_cta_futures
    perf, w = run_cta_futures(rebalance_freq={"multi_21d": 21, "multi_10d": 10,
                                              "tsmom_21d": 21, "tsmom_10d": 10,
                                              "macro_21d": 21}[variant[len("CTA_Futures_"):]],
                              signal_mode="multi" if "multi" in variant else
                              ("macro" if "macro" in variant else "tsmom"))
    return None, None   # placeholder; not needed — class FUTURES_MACRO_SYNTH


def gen_global_macro():
    from strat_global_macro import run_global_macro
    pr, rt = panel_12big(), rets_12big()
    from core import DataLoader
    fx = DataLoader.build_price_panel(DataLoader.load_fx())
    cr = DataLoader.build_price_panel(DataLoader.load_crypto())
    _, w = run_global_macro(pr, rt, fx_prices=fx, crypto_prices=cr)
    raw, _ = engine_run(pr, w, 21)
    return raw, (-w.clip(upper=0.0)).sum(axis=1)


def gen_risk_parity():
    from strat_global_macro import run_bridgewater_style
    pr, rt = panel_12big(), rets_12big()
    run_bridgewater_style(pr, rt)
    return None, pd.Series(0.0, index=pr.index)   # long-only by construction


def gen_factor_mom(start: str):
    from strat_factor_momentum import run_factor_momentum
    run_factor_momentum(start=start)
    return None, None    # FACTOR_SYNTH class — short frac measured from weights inside
