"""HUNT_VOL2 ROUND 5 — CBOE put/call-ratio archive (1995-2019, frozen 2019-10-04) as a
vol-timing OVERLAY on the champion. Charter (a): evaluated ONLY over 2006-2019;
era-robustness WITHIN the window is the gate (TimesFM single-era kill applied).

Data: tools/quant/data/cboe_pcr/pcr_covariates_SPY_daily.csv (DATA_COTMORE-R3) — PIT
strictly-prior covariates, 1-session carry cap, NaN before first obs and after freeze.
Raw stitched obs re-derived from build_pcr.build_series for the PIT audit (test-enforced).

Cost convention = R2's champion-identical one (test-enforced: gate==1 -> net == champion
exactly). Overlay position p in [0,1]: champion gross is exactly 1.6 (§8e cap binding),
so lever-up arms are excluded by contract.

V2 battery wiring:
  * gates.run(net, ref=champion_full, sig=<positions>, leak_check=True) — the mandatory
    §6 Step-1 leak probe (sig-ful; sig= is REQUIRED, fail-closed if omitted).
  * §8 blend battery for overlays: 8a negy 0, 8b MDD > -7%, 8c dAnn > 0 HARD,
    8d dSR >= 0 AND dH2 >= 0, 8f delta-halves consistency, 8g plateau on the threshold
    grid, 8h placebo (frequency/episode-matched random trims), 8j corr reported not failed.
  * Era-robustness (charter R5): contiguous thirds + 5 sub-eras of the WINDOW; deltas
    reported per era. §8f's both-halves test is the ratified era gate.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/daxu/software/world-trader")
CAMP = ROOT / "campaign"
if str(CAMP) not in sys.path:
    sys.path.insert(0, str(CAMP))

from bt import gates as G  # noqa: E402
from bt.metrics import ann_geo, max_dd, neg_years, sharpe_d  # noqa: E402

PCR_DIR = ROOT / "tools/quant/data/cboe_pcr"
PCR_CSV = PCR_DIR / "pcr_covariates_SPY_daily.csv"
CHAMP_CSV = ROOT / "campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
CHAMP_SHA = "4358dfab95679b97"
WIN_LO = "2008-03-31"          # champion start
WIN_HI = "2019-10-07"          # last PIT covariate session (obs freeze 2019-10-04)
ANN = 252.0
COST = 6.4e-4                   # one-side bps on FULL |dW|
GEAR = 1.6

_PC = None
_CH = None
_RAW = {}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def champion() -> pd.Series:
    """Champion of record (sha-pinned, fail-closed on drift)."""
    global _CH
    if _CH is None:
        sha = sha256_of(CHAMP_CSV)
        if not sha.startswith(CHAMP_SHA):
            raise RuntimeError(f"champion sha drift: {sha[:16]} != {CHAMP_SHA}")
        _CH = pd.read_csv(CHAMP_CSV, parse_dates=["date"]).set_index("date")["ret"]
    return _CH


def covariates() -> pd.DataFrame:
    """PIT covariate frame on the SPY proxy calendar, as shipped by DATA_COTMORE-R3."""
    global _PC
    if _PC is None:
        _PC = (pd.read_csv(PCR_CSV, parse_dates=["date"])
                 .set_index("date").sort_index())
    return _PC


def raw_series(col: str) -> pd.Series:
    """Stitched PCR observation series for `col` from build_pcr (the SOURCE of the
    covariate mapping) — used only for the PIT audit."""
    if col not in _RAW:
        if str(PCR_DIR) not in sys.path:
            sys.path.insert(0, str(PCR_DIR))
        import build_pcr  # noqa: PLC0415
        df = build_pcr.build_series(col)
        _RAW[col] = df.set_index("date")["pcr"].sort_index()
    return _RAW[col]


def window_frame(col: str):
    """(covariates reindexed on champion days, champion) over the eval window.
    Champion sessions without a PIT covariate -> NaN (overlay holds champion there)."""
    ch = champion()
    champ_w = ch.loc[WIN_LO:WIN_HI]
    w = covariates()[[col]].reindex(champ_w.index)
    return w, champ_w


def expanding_z(s: pd.Series, minp: int = 502) -> pd.Series:
    """Causal expanding z-score (ddof=0, min_periods) of the PIT covariate."""
    m = s.expanding(min_periods=minp).mean()
    sd = s.expanding(min_periods=minp).std(ddof=0)
    return (s - m) / sd.replace(0.0, np.nan)


def pcr_gate(s: pd.Series, kind: str, op: str, thr: float, to: float,
             minp: int = 502) -> pd.Series:
    """Overlay gate from a PCR-derived signal.
    kind: 'level' | 'z' (expanding causal z) | 'chg' (5-session diff, level units).
    op: 'gt' -> trim when signal > thr; 'lt' -> trim when signal < thr.
    to: position while triggered (1.0 = no change). NaN signal -> NaN gate (hold champ)."""
    if kind == "z":
        x = expanding_z(s, minp=minp)
    elif kind == "chg":
        x = s.diff(5)
    elif kind == "level":
        x = s
    else:
        raise ValueError(kind)
    trig = (x > thr) if op == "gt" else ((x < thr) if op == "lt" else (_ for _ in ()).throw(ValueError(op)))
    g = pd.Series(np.where(trig, to, 1.0), index=s.index)
    g[x.isna()] = np.nan
    return g


def overlay_net(g: pd.Series, r: pd.Series) -> pd.Series:
    """Champion-identical cost convention (R2 lib, test-enforced):
      p_t = g_{t-1} (T+1), NaN gate -> champion 1.0, p_{-1} := 1.0
      net_t = p_t * r_t - 6.4e-4 * 1.6 * |p_t - p_{t-1}|
    Causal: net at t depends on g up to t-1 and r at t only."""
    g = g.reindex(r.index).fillna(1.0)  # no-covariate sessions hold the champion
    p = g.shift(1).fillna(1.0)
    to = p.diff().abs()
    if len(p):
        to.iloc[0] = abs(p.iloc[0] - 1.0)
    return p * r.fillna(0.0) - to * COST * GEAR


def stats(x: pd.Series) -> dict:
    x = x.dropna()
    neg, worst = neg_years(x)
    k = len(x) // 2
    return dict(ann=float(ann_geo(x)), sr=float(sharpe_d(x)), mdd=float(max_dd(x)),
                neg_yrs=int(neg), worst_yr=float(worst), n=len(x),
                h1=float(sharpe_d(x.iloc[:k])), h2=float(sharpe_d(x.iloc[k:])))


def delta_stats(net: pd.Series, champ: pd.Series) -> dict:
    """Full §8-style delta table (dAnn geometric, dSR, dMDD, halves, negy, worstyr)."""
    c, n = stats(champ), stats(net)
    return dict(champ=c, net=n,
                d_ann=n["ann"] - c["ann"], d_sr=n["sr"] - c["sr"],
                d_mdd=n["mdd"] - c["mdd"], d_h1=n["h1"] - c["h1"],
                d_h2=n["h2"] - c["h2"],
                neg_yrs_net=n["neg_yrs"], worst_yr_net=n["worst_yr"])


def era_splits(champ_w: pd.Series, n: int = 3) -> dict:
    """Contiguous equal-length era splits of the window: name -> (start_ts, end_ts)."""
    out = {}
    segs = np.array_split(np.arange(len(champ_w)), n)
    for i, seg in enumerate(segs):
        out[f"era{i + 1}of{n}"] = (champ_w.index[seg[0]], champ_w.index[seg[-1]])
    return out


def trim_frequency(g: pd.Series, to: float) -> float:
    return float((g == to).mean())


def random_trim_null(champ: pd.Series, freq: float, to: float, n: int = 200,
                     seed: int = 0) -> np.ndarray:
    """Frequency-matched random-trim null (R2 instrument; §8h analogue): n random trim
    schedules at trim frequency `freq` to position `to`; returns n dSR values. Seed fixed."""
    rng = np.random.default_rng(seed)
    idx = champ.index
    m = len(idx)
    k = int(round(freq * m))
    base_sr = float(sharpe_d(champ))
    out = np.empty(n)
    for j in range(n):
        sel = rng.choice(m, size=k, replace=False)
        g = pd.Series(1.0, index=idx)
        g.iloc[sel] = to
        out[j] = float(sharpe_d(overlay_net(g, champ))) - base_sr
    return out


def placebo_matched(champ: pd.Series, g: pd.Series, to: float, n: int = 200,
                    seed: int = 0) -> dict:
    """§8h placebo: random trims matching BOTH the trim frequency AND the real gate's
    trim-episode length distribution. Returns dSR draws + frac_pos + p_repro."""
    rng = np.random.default_rng(seed)
    idx = champ.index
    m = len(idx)
    flat = (g.fillna(1.0) == to).values
    eps, run = [], 0
    for f in flat:
        if f:
            run += 1
        elif run:
            eps.append(run); run = 0
    if run:
        eps.append(run)
    if not eps:
        return dict(dsr=np.array([]), frac_pos=np.nan, p_repro=np.nan, n=0,
                    eps_len_med=np.nan, n_eps=0)
    eps = np.array(eps)
    base_sr = float(sharpe_d(champ))
    dsr = np.empty(n)
    for j in range(n):
        g2 = pd.Series(1.0, index=idx)
        pos = 0
        while pos < m:
            ln = int(eps[rng.integers(0, len(eps))])
            if pos + ln <= m:
                g2.iloc[pos:pos + ln] = to
            pos += ln + int(rng.integers(1, 8))
        dsr[j] = float(sharpe_d(overlay_net(g2, champ))) - base_sr
    real_dsr = float(sharpe_d(overlay_net(g, champ))) - base_sr
    return dict(dsr=dsr, frac_pos=float((dsr > 0).mean()),
                p_repro=float((dsr >= real_dsr).mean()), n=n,
                eps_len_med=float(np.median(eps)), n_eps=int(len(eps)))


def gate_run(net: pd.Series, champ_full: pd.Series, sig: np.ndarray) -> dict:
    """V2 battery call: gates.run on the overlay BOOK — sig= and leak_check=True are
    BOTH mandatory (§6 Step-1; sig omitted raises, fail-closed). ref = full champion;
    corr_ok is REPORTED for overlays but never used in the verdict (§8j)."""
    if sig is None:
        raise ValueError("sig= is mandatory on acceptance-track calls (V2 §6 Step-1)")
    res = G.run(net, ref=champ_full, sig=sig, leak_check=True)
    return res
