"""RES_META cross-asset engine library (campaign/bt-based, short + TDD-tested).

Families (charter RES_META): cross-asset short-horizon reversal on a TRADEABLE
universe (ETFs + FRED daily FX closes; NO VIX spot — it is not ownable), plus
meta-alloc helpers. All costs via bt.engine (6.4bps full |dW|, borrow, margin).
"""
import os
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
DATA = os.path.join(ROOT, "tools/quant/data")
COST_BPS = 6.4
BORROW_FRAC = 0.005
ANN = 252.0


def load_px(sym: str) -> pd.Series:
    """Fail-closed close-price loader. Search order: more_etf, twelvedata, more_vol
    (column 'close'); more_fx / more_fred (FRED spot, column 'value')."""
    for sub, col in (("more_etf", "close"), ("twelvedata", "close"),
                     ("more_vol", "close"), ("more_fx", "value"), ("fx", "close"),
                     ("more_fred", "value")):
        p = os.path.join(DATA, sub, f"{sym}.csv")
        if os.path.exists(p):
            df = pd.read_csv(p, parse_dates=["date"]).set_index("date")
            s = df[col].astype(float)
            s = s[~s.index.duplicated(keep="last")].sort_index().dropna()
            if len(s) == 0:
                raise ValueError(f"empty series: {sym}")
            return s
    raise FileNotFoundError(sym)


def rets(px: pd.Series) -> pd.Series:
    return px.pct_change().dropna()


def universe() -> list:
    """12 liquid TRADEABLE cross-asset legs (no spot-VIX; every file on disk)."""
    return ["SPY", "IWM", "EEM", "TLT", "GLD", "UUP", "DEXUSEU", "DEXJPUS",
            "DEXUSUK", "DEXCAUS", "DEXUSAL", "DEXSZUS"]


def clip_rets(r: pd.Series, cap: float = 0.18) -> pd.Series:
    return r.clip(lower=-cap, upper=cap).where(r.notna())


def reversal_positions(R: pd.DataFrame, L: int = 8, n_leg: int = 1) -> pd.DataFrame:
    """Dollar-neutral cross-asset reversal: long the n_leg worst L-day performers,
    short the n_leg best, equal-dollar. Uses ONLY returns up to and including t-1
    (the L-day window ends yesterday) so a position earned at t is T+1-causal."""
    past = R.shift(1)                                   # info up to t-1
    mom = past.rolling(L, min_periods=L).sum()
    out = pd.DataFrame(0.0, index=R.index, columns=R.columns)
    for t in range(len(mom)):
        row = mom.iloc[t]
        ok = row.dropna()
        if len(ok) < max(2 * n_leg, 2):
            continue
        order = ok.sort_values()
        out.iloc[t, R.columns.get_indexer(order.index[:n_leg])] = 1.0 / n_leg
        out.iloc[t, R.columns.get_indexer(order.index[-n_leg:])] = -1.0 / n_leg
    out[~R.shift(1).rolling(L, min_periods=L).sum().notna()] = 0.0
    return out


def borrow_cost(w: pd.DataFrame) -> pd.Series:
    """bt.engine.borrow_cost wrapper with campaign defaults (short notional)."""
    from bt.engine import borrow_cost as _bc
    return _bc(w, BORROW_FRAC, 1.0)


def sleeve_net(P: pd.DataFrame, R: pd.DataFrame) -> pd.Series:
    """Net daily book from positions P (already T+1-safe) x per-unit returns R.
    Costs: 6.4bps x full |dW| one-side (bt.engine), borrow on shorts; margin via
    bt.engine.margin_cost on (gross-1)+. T+1: shift(1) applied HERE, once."""
    from bt.engine import cost_turnover, margin_cost
    w = P.reindex(R.index).fillna(0.0).shift(1).fillna(0.0)
    wc = _cap_lev(w)
    r = (wc * R.fillna(0.0)).sum(axis=1)
    gross = wc.abs().sum(axis=1)
    net = (r - cost_turnover(wc, COST_BPS)
           - borrow_cost(wc)
           - margin_cost(gross)).dropna()
    return net


def _cap_lev(w: pd.DataFrame, max_lev: float = 1.6) -> pd.DataFrame:
    from bt.engine import cap_leverage
    return cap_leverage(w, max_lev)


def vol_norm_scale(r: pd.Series, target: float = 0.10, min_p: int = 60,
                   cap: float = 3.0) -> pd.Series:
    """Trailing-only expanding vol-target scale (bt.engine semantics, 1-col)."""
    from bt.engine import vol_target_scale
    return vol_target_scale(r.to_frame("r"), target=target, window=min_p, cap=cap)["r"]


def report_lite(net: pd.Series, champ: pd.Series) -> dict:
    """One-line screening report (SR/halves/neg/worst/corr-to-champion)."""
    from bt.metrics import sharpe_d, half_split, neg_years
    neg, worst = neg_years(net)
    j = pd.concat([champ.rename("c"), net.rename("s")], axis=1).dropna()
    return dict(n=len(net), sr=round(sharpe_d(net), 3),
                h1=round(half_split(net)[0], 2), h2=round(half_split(net)[1], 2),
                neg=neg, worst=round(worst, 4),
                corr=round(float(j.c.corr(j.s)), 3) if len(j) > 2 else np.nan,
                ann=round(float((1 + net).prod() ** (ANN / len(net)) - 1), 4))
