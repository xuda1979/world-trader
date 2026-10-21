"""HUNT_TIMESFM ROUND 4 engine: honest sleeve construction from any position path.

Costs/skeleton follow campaign/bt/engine.py + hunt_sector2_lib conventions:
 6.4bps one-side on FULL |dW| (entry day charged), borrow 0.5%/yr on short notional,
 margin 4.5%/yr on (gross-1), vol-target trailing-only clip<=3, strict T+1 (shift).
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

COST = 6.4e-4
BORROW = 0.005
MARGIN = 0.045
ANN = 252.0


def vt_scale(ret: pd.Series, target: float = 0.10, minlen: int = 60,
             cap: float = 3.0) -> pd.Series:
    """Trailing-only vol-target: scale_t uses ret[0..t-1] (shift(1)); clip [_,cap]."""
    vol = ret.expanding(min_periods=minlen).std(ddof=1) * np.sqrt(ANN)
    s = (target / vol.replace(0.0, np.nan)).clip(upper=cap)
    return s.shift(1).fillna(0.0)


def sleeve_net(pos: pd.Series, rets: dict, vt: str = "on", w_ref=None) -> pd.Series:
    """pos = RAW desired exposure at close t (unshifted, in [-1,1] or {-1,0,1}).
    rets: {leg: ret series}; single-leg uses {None: r}. Applies strict T+1, optional
    trailing VT, 6.4bps on FULL |dW| of held weight, borrow on shorts, margin on
    (gross-1). Fail-closed: no silent zero-fill (active leg must have real ret)."""
    p = pos.shift(1).fillna(0.0).dropna()
    if not len(p):
        return pd.Series(dtype=float)
    if len(rets) == 1 and None in rets:
        w = p.to_frame("w"); rs = rets[None].reindex(p.index)
        rs = rs.to_frame("r")
    else:
        raise ValueError("multi-leg: build weights frame upstream")
    r = rs.iloc[:, 0]
    if vt == "on":
        p = p * vt_scale(r.fillna(0.0))
    w = p.rename("w").to_frame()
    w["r"] = r
    act = w["w"].abs() > 0
    bad = act & w["r"].isna()
    if bad.any():
        d = bad.idxmax()
        raise ValueError(f"silent zero-fill: active leg without return at {d}")
    w["r"] = w["r"].fillna(0.0)
    to = w["w"].diff().abs()
    to.iloc[0] = abs(w["w"].iloc[0])          # entry turnover 0 -> w0 (charged)
    gross = w["w"] * w["r"]
    net = (gross - to * COST
           - (-w["w"].clip(upper=0.0)) * BORROW / ANN
           - (w["w"].abs() - 1.0).clip(lower=0.0) * MARGIN / ANN)
    return net.dropna()


def stats(r: pd.Series) -> dict:
    r = r.dropna()
    if len(r) < 2 or r.std(ddof=1) == 0:
        return dict(n=len(r), sr=0.0, ann=np.nan, vol=0.0, neg_yr=0, worst=0.0,
                    h1=0.0, h2=0.0)
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod(min_count=1) - 1)
    k = len(r) // 2
    def _sr(x):
        return float(x.mean() / x.std(ddof=1) * np.sqrt(ANN)) if len(x) > 1 and x.std(ddof=1) > 0 else 0.0
    return dict(n=len(r), sr=float(r.mean() / r.std(ddof=1) * np.sqrt(ANN)),
                ann=float(np.prod(1 + r) ** (ANN / len(r)) - 1),
                vol=float(r.std(ddof=1) * np.sqrt(ANN)),
                neg_yr=int((yr < 0).sum()), worst=float(yr.min()),
                h1=_sr(r.iloc[:k]), h2=_sr(r.iloc[k:]))
