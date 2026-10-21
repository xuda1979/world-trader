"""HUNT_VOL2 round-2 lib: champion-integrated conditional vol gates.

Design contract (charter round 2, coordinator standup 2026-09-07):
  pos = champion * gate, T+1 on the gate (champion itself is the committed
  causal T+1 construction from rawew13v2_build.py, nav.shift(1)).
  Costs: INCREMENTAL 6.4bps one-side on FULL |dW| where W = 1.6*gate
  (champion gross is exactly 1.6 — verified vs rawew13v2_build --verify).
  Day-0 entry measured vs the flat 1.6 the champion actually built.

Pass bar (charter): ann delta > +0.3pp net of costs; also report MDD and
worst-year deltas. Corr gate is moot for overlays (corr with champion is ~+0.9
by construction); instead the gate must be causally JUSTIFIED (expanding-q
thresholds, no full-sample stats) and beat a frequency-matched random-trim null.
"""
import sys
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/HUNT_VOL2/scratch")
import vol2_lib as L  # champion(), vol(), stats machinery

GEAR = 1.6
COST = 6.4e-4  # one-side bps on FULL |dW|, W=1.6*gate
ANN = 252.0

_CH = None


def champion() -> pd.Series:
    global _CH
    if _CH is None:
        _CH = L.champion()
    return _CH


def overlay_net(g: pd.Series, r: pd.Series) -> pd.Series:
    """Champion-IDENTICAL cost convention (rawew13v2_build: to_t = |W_t - W_{t-1}|,
    cost charged the day the new position is HELD; champion gross exactly 1.6):
      p_t = g_{t-1} (T+1), p_{-1} := 1.0 (champion built flat 1.6 on day 0)
      net_t = p_t * r_t - 6.4e-4 * 1.6 * |p_t - p_{t-1}|
    gate==1 everywhere  ->  net EXACTLY the champion (test-enforced).
    Causal: net at t depends on g up to t-1 and r at t only."""
    g = g.reindex(r.index)
    p = g.shift(1).fillna(1.0)
    to = p.diff().abs()
    if len(p):
        to.iloc[0] = abs(p.iloc[0] - 1.0)
    return p * r.reindex(p.index).fillna(0.0) - to * COST * GEAR


def trail_ret(r: pd.Series, win: int) -> pd.Series:
    """Champion trailing `win`-day return INCLUDING day t (decided at close t)."""
    return (1 + r).rolling(win).apply(np.prod, raw=True) - 1.0


def expanding_q(d: pd.Series, q: float, minp: int) -> pd.Series:
    """Causal expanding quantile: thr_t = quantile_q(d[0..t]) with min_periods."""
    return d.expanding(min_periods=minp).quantile(q)


def sustained(cond: pd.Series, k: int) -> pd.Series:
    """True iff the last k rows of cond are all True."""
    return cond.rolling(k).apply(lambda x: int(x.all()), raw=True).fillna(0).astype(bool)


def hold_after(trig: pd.Series, hold: int) -> pd.Series:
    """Trigger day + `hold` further days on. min_periods=1 so a trigger inside the
    first `hold` rows still fires (no spurious warmup); window is backward-only."""
    return trig.rolling(hold + 1, min_periods=1).max().fillna(0).astype(bool)


def null_trim_p(gate: pd.Series, r: pd.Series, n=200, seed=0) -> float:
    """Frequency-matched random-trim null: p = fraction of same-fire-rate random
    gates with ann_delta >= real gate's ann_delta. Tests TIMING skill, not luck of
    exposure: an unconditional trim on a +40%/yr book must beat ~50%, not 95%."""
    real = float(geo_ann(overlay_net(gate, r)))
    rng = np.random.default_rng(seed)
    cnt = 0
    k = int(round(gate.mean() * len(gate)))
    for _ in range(n):
        q = pd.Series(rng.permutation(gate.values), index=gate.index)  # keeps fire rate
        if float(geo_ann(overlay_net(q, r))) >= real:
            cnt += 1
    return cnt / n


def geo_ann(r: pd.Series) -> float:
    r = r.dropna()
    return float((1 + r).prod() ** (252 / len(r)) - 1.0) if len(r) else 0.0


def arith_ann(r):
    r = r.dropna()
    return float(r.mean() * ANN) if len(r) else 0.0


def mdd(r: pd.Series) -> float:
    nav = (1 + r.dropna()).cumprod()
    return float((nav / nav.cummax() - 1).min())


def worst_year(r: pd.Series) -> float:
    yr = r.dropna().groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    return float(yr.min())


def deltas(net: pd.Series, base: pd.Series) -> dict:
    """ann delta (geometric, pp) + MDD delta + worst-year delta vs base book."""
    j = pd.concat([net.rename("a"), base.rename("b")], axis=1, join="inner").dropna()
    return dict(
        d_ann_geo_pp=(geo_ann(j.a) - geo_ann(j.b)) * 100,
        d_ann_arith_pp=(arith_ann(j.a) - arith_ann(j.b)) * 100,
        d_sr=(j.a.mean() / j.a.std() * np.sqrt(ANN)) - (j.b.mean() / j.b.std() * np.sqrt(ANN)),
        d_mdd_pp=(mdd(j.a) - mdd(j.b)) * 100,
        d_worst_pp=(worst_year(j.a) - worst_year(j.b)) * 100,
    )


def gate_stats(g: pd.Series, r: pd.Series) -> dict:
    """Fire-rate + trigger count for honesty reporting."""
    g = g.reindex(r.index).fillna(1.0)
    trig = (g < 1.0 - 1e-12)
    # count *episodes* (runs of fired days), not days
    eps = (trig & ~trig.shift(1, fill_value=False)).sum()
    return dict(trigger_frac=float(trig.mean()), n_trig=int(eps), n=int(len(g)))


def vol(name: str) -> pd.Series:
    return L.vol(name)


def fmt(name, st, d, extra="") -> str:
    return (f"[{name}] trig={st['trigger_frac']*100:.2f}% ({st['n_trig']} eps) "
            f"dAnn_geo={d['d_ann_geo_pp']:+.2f}pp dAnn_arith={d['d_ann_arith_pp']:+.2f}pp "
            f"dSR={d['d_sr']:+.3f} dMDD={d['d_mdd_pp']:+.2f}pp dWorst={d['d_worst_pp']:+.2f}pp {extra}")
