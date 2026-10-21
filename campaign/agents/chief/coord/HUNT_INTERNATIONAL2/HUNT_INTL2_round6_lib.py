"""HUNT_INTERNATIONAL2 ROUND 6 audit library — MY OWN implementations of every battery
quantity, written from the GATES_CONTRACT_V2 definitions, used to fraud-catch
HUNT_TIMESFM's R5 verdicts. Independent code, same contract. Nothing imported from bt.*
(except in the audit script, for a clearly-labeled cross-reference re-run).
"""
from __future__ import annotations

from math import erfc, sqrt

import numpy as np
import pandas as pd

ANN = 252.0
COST = 6.4e-4          # 6.4 bps one-side FULL |dW|
BORROW = 0.005         # 0.5%/yr on short notional
MARGIN = 0.045         # 4.5%/yr on notional above 1.0 (TimesFM meta convention)


# ---------------------------------------------------------------- metrics (own)

def sr_d(r) -> float:
    r = pd.Series(r).dropna()
    s = r.std(ddof=1)
    if not len(r) or not np.isfinite(s) or s < 1e-12:
        return 0.0
    return float(r.mean() / s * np.sqrt(ANN))


def halves(r) -> tuple:
    r = pd.Series(r)
    k = len(r) // 2
    return (sr_d(r.iloc[:k]), sr_d(r.iloc[k:]))


def neg_years(r) -> tuple:
    r = pd.Series(r).dropna()
    if not len(r):
        return (0, np.nan)
    if not isinstance(r.index, pd.DatetimeIndex):
        raise ValueError("neg_years needs a DatetimeIndex")
    yr = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    yr = yr.where(np.isfinite(yr), -1.0)   # ruined/NaN year counts as negative (fail-closed)
    return (int((yr < 0).sum()), float(yr.min()))


# ---------------------------------------------------------------- leak probe (own)

def _fisher_p(c: float, n: int) -> float:
    if not np.isfinite(c) or n < 3:
        return np.nan
    if abs(c) >= 1.0:
        return 0.0
    t = c * sqrt((n - 2) / (1.0 - c * c))
    return erfc(abs(t) / sqrt(2))


def leak_probe_own(score, ret) -> dict:
    """corr(sig_t, r_t) + two-sided Fisher p + lag scan -2..+2. leak=True requires
    |c0| >= 0.20 AND p < 0.05 AND lag 0 is the argmax of the |corr| profile.
    Fail-closed: unmeasurable => measurable=False, leak=NaN."""
    s = pd.Series(score).astype(float)
    r = pd.Series(ret).astype(float)
    j = pd.concat([s.rename("s"), r.rename("r")], axis=1).dropna()
    n = len(j)
    if n < 30 or j.s.std(ddof=1) <= 0 or j.r.std(ddof=1) <= 0:
        return dict(measurable=False, leak=np.nan, same_period_corr=np.nan,
                    same_period_p=np.nan, lag_scan={})
    c0 = float(j.s.corr(j.r))
    p0 = _fisher_p(c0, n)
    lag_scan = {}
    for lag in (-2, -1, 0, 1, 2):
        rr = r.shift(-lag) if lag != 0 else r
        jj = pd.concat([s.rename("s"), rr.rename("r")], axis=1).dropna()
        lag_scan[lag] = float(jj.s.corr(jj.r)) if len(jj) >= 30 else np.nan
    others = [abs(v) for k, v in lag_scan.items() if k != 0 and np.isfinite(v)]
    leak = bool(np.isfinite(c0) and np.isfinite(p0) and abs(c0) >= 0.20 and p0 < 0.05
                and (not others or abs(c0) >= max(others)))
    return dict(measurable=True, leak=leak, same_period_corr=c0, same_period_p=p0,
                lag_scan=lag_scan)


# ---------------------------------------------------------------- scramble (own)

def scramble_p_own(sig, r, n=200, block=20, seed=0) -> tuple:
    """Position-lag scramble: roll POSITIONS by a random lag in [block, T-block]; book =
    rolled_positions * r (no re-costing, positions only); p = frac(scrambled SR >= real
    book SR). Baseline is the REAL book's SR. Returns (p, real_sr)."""
    s = np.asarray(sig, dtype=float)
    rv = np.asarray(r, dtype=float)
    if not (np.isfinite(s).all() and np.isfinite(rv).all()):
        return (np.nan, np.nan)
    real = sr_d(pd.Series(s * rv))
    T = len(rv)
    lo, hi = block, T - block
    if hi <= lo:
        return (np.nan, real)
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n):
        lag = int(rng.integers(lo, hi + 1))
        book = np.roll(s, lag) * rv
        if sr_d(pd.Series(book)) >= real:
            cnt += 1
    return (cnt / n, real)


# ---------------------------------------------------------------- beats-passive trio (own)

def _as_ret_series_own(x):
    """Curve detection: all values > 1e3 => pct_change; else already returns."""
    v = pd.to_numeric(pd.Series(x), errors="coerce")
    d = v.dropna()
    if len(d) and bool((d > 1e3).all()):
        return v.pct_change().dropna()
    return d


def spy_buyhold_own(spy_ret, cand_index) -> pd.Series:
    """SPY B&H on the candidate span: flat day 0, ONE entry cost on the first held day,
    earns from day 1 on; NaN where SPY has no data (never fake 0.0)."""
    r = pd.to_numeric(pd.Series(spy_ret), errors="coerce").reindex(cand_index)
    if len(cand_index) < 2:
        return pd.Series(np.nan, index=cand_index, dtype=float)
    vals = r.to_numpy(copy=True)
    on = r.notna().to_numpy(copy=True)
    on[0] = False
    out = pd.Series(np.where(on, vals, 0.0), index=cand_index, dtype=float)
    k = int(np.argmax(on)) if on.any() else -1
    if k >= 0 and np.isfinite(out.iloc[k]):
        out.iloc[k] -= COST
    out[~on & r.isna().to_numpy()] = np.nan
    return out


def sixty_forty_own(spy_ret, ief_ret, cand_index) -> pd.Series:
    """60/40 SPY-IEF: flat day 0; entered at day 1; re-snapped to 0.60/0.40 at each month
    start; weights DRIFT intra-month by relative performance; 6.4bps on full |dW| each day
    (entry + every snap included); no short leg -> no borrow. Fail-closed to all-NaN when
    either leg has NO data on the span (a fabricated benchmark must not mask no-data)."""
    spy_raw = pd.to_numeric(pd.Series(spy_ret), errors="coerce").reindex(cand_index)
    ief_raw = pd.to_numeric(pd.Series(ief_ret), errors="coerce").reindex(cand_index)
    if not (spy_raw.notna().any() and ief_raw.notna().any()):
        return pd.Series(np.nan, index=cand_index, dtype=float)
    rs = spy_raw.fillna(0.0).to_numpy()
    ri = ief_raw.fillna(0.0).to_numpy()
    T = len(cand_index)
    per = cand_index.to_period("M")
    is_ms = np.r_[True, per[1:] != per[:-1]]
    w_s = w_i = 0.0
    prev_ws = prev_wi = 0.0
    gross = np.zeros(T)
    cost = np.zeros(T)
    for t in range(T):
        if t == 0:
            pass                                    # flat day 0 (T+1 honest entry)
        elif t == 1 or is_ms[t]:
            w_s, w_i = 0.60, 0.40                   # entry / monthly snap to target
        else:
            g = w_s * rs[t - 1] + w_i * ri[t - 1]   # drift with yesterday's relative P&L
            d = 1.0 + g
            if not np.isfinite(d) or d <= 0.0:      # ruin guard: weights undefined
                w_s = w_i = 0.0
            else:
                w_s = w_s * (1.0 + rs[t - 1]) / d
                w_i = w_i * (1.0 + ri[t - 1]) / d
        gross[t] = w_s * rs[t] + w_i * ri[t]
        cost[t] = (abs(w_s - prev_ws) + abs(w_i - prev_wi)) * COST
        prev_ws, prev_wi = w_s, w_i
    return pd.Series(gross - cost, index=cand_index, dtype=float)


def vt_scale_own(r, target=0.10, window=60, cap=3.0) -> pd.Series:
    """Trailing-only VT scale: scale_t = clip(target / expanding_std(r[0..t-1])), i.e.
    shift(1); clip<=3, floor 0.2, warmup fill 1.0."""
    vols = r.expanding(min_periods=window).std(ddof=1) * np.sqrt(ANN)
    scale = (target / vols.replace(0.0, np.nan)).clip(upper=cap).clip(lower=0.2)
    return scale.shift(1).fillna(1.0)


def cta_trend_own(cta_ret, target=0.10, window=60, cap=3.0) -> pd.Series:
    """CTA curve/returns -> 10% ann vol-target, TRAILING ONLY. Own implementation."""
    r = pd.Series(cta_ret).dropna()
    return (r * vt_scale_own(r, target=target, window=window, cap=cap)).dropna()


def best_passive_own(cand_ret, spy=None, ief=None, cta=None) -> tuple:
    """(best_sr, best_name, per-benchmark info). A benchmark is measurable only with
    >=60 obs AND >=50% span coverage. Fail-closed: none measurable => (NaN, None, info)."""
    cand = pd.Series(cand_ret).dropna()
    if not len(cand):
        return (np.nan, None, dict(reason="empty_candidate"))
    ci = cand.index
    spy_r = _as_ret_series_own(spy) if spy is not None else None
    ief_r = _as_ret_series_own(ief) if ief is not None else None
    benchmarks = {}
    if spy_r is not None:
        benchmarks["spy_bh"] = spy_buyhold_own(spy_r, ci)
    if spy_r is not None and ief_r is not None:
        benchmarks["sixty_forty"] = sixty_forty_own(spy_r, ief_r, ci)
    if cta is not None:
        benchmarks["cta_trend"] = cta_trend_own(cta).reindex(ci)
    info = {}
    for name, series in benchmarks.items():
        s = series.dropna()
        if len(s) >= 60 and len(s) >= 0.5 * len(cand):
            info[name] = dict(sr=sr_d(s), n=len(s))
        else:
            info[name] = dict(sr=np.nan, n=len(s),
                              note="unmeasurable(<MIN_OBS or sparse-overlap)")
    measurable = {k: v for k, v in info.items() if np.isfinite(v["sr"])}
    if not measurable:
        return (np.nan, None, info)
    bn = max(measurable, key=lambda k: measurable[k]["sr"])
    return (float(measurable[bn]["sr"]), bn, info)


# ---------------------------------------------------------------- book rebuild (own)

def book_net_own(w, r) -> tuple:
    """net = w*r - |dw|*6.4bps - borrow - margin; entry turnover charged (|w_0| on day 0);
    exit turnover (dw on a day w becomes 0) folded into the LAST ACTIVE day so no cost
    lands on a flat day; rpu = net/w SIGNED division, rpu=1.0 on flat days, so
    sig * rpu == net exactly for sig = the held-weight path."""
    r = r.reindex(w.index)
    act = w.abs() > 0
    if (act & r.isna()).any():
        bad = (act & r.isna()).idxmax()
        raise ValueError(f"silent zero-fill: active weight without return at {bad}")
    r = r.fillna(0.0)
    dw = w.diff().abs()
    dw.iloc[0] = abs(w.iloc[0])
    flat_cost = dw.where((w == 0) & (dw > 0))
    if flat_cost.notna().any():
        last_active = (w != 0).cummax() * (w != 0)
        idx_last = pd.Series(np.where(last_active > 0, np.arange(len(w)), -1), index=w.index)
        carry = idx_last.replace(-1, np.nan).ffill().fillna(-1).astype(int)
        for gi, c in flat_cost.dropna().items():
            li = carry.loc[gi]
            if li >= 0:
                dw.iloc[li] += c
        dw.loc[flat_cost.dropna().index] = 0.0
    cost = dw * COST
    borrow = (-w.clip(upper=0.0)) * BORROW / ANN
    margin = (w.abs() - 1.0).clip(lower=0.0) * MARGIN / ANN
    net = w * r - cost - borrow - margin
    rpu = (net / w.replace(0.0, np.nan)).fillna(1.0)
    return net, rpu


def held_weights_own(cal, pos, v) -> pd.Series:
    """w_t = pos_j * v_j for t in (D_j, D_{j+1}]; STRICT T+1: day t holds the last decision
    STRICTLY BEFORE t, so a decision date itself still holds the PRIOR decision and the
    new position starts the NEXT trading day."""
    pv = (pos * v).dropna().sort_index()
    w = pd.Series(0.0, index=cal)
    if len(pv) == 0:
        return w
    dec = pv.index
    j = np.searchsorted(dec.values, cal.values, side="left") - 1
    w_vals = np.where(j >= 0, pv.values[j.clip(0)], 0.0)
    return pd.Series(w_vals, index=cal, dtype=float)


# ---------------------------------------------------------------- builders (own)

def pos_from_forecast(fcst: pd.DataFrame, hcol: str) -> pd.Series:
    return np.sign(fcst[hcol] - fcst["last"])


def weekly_decisions_own(idx: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """Last trading day of each ISO week present in the calendar."""
    iso = idx.isocalendar()
    df = pd.DataFrame({"d": idx, "yw": iso.year * 100 + iso.week})
    return pd.DatetimeIndex(df.groupby("yw")["d"].max().sort_values().values)


def vt_frozen_own(r, dec, target=0.10, minlen=60, cap=3.0) -> pd.Series:
    """Trailing-only VT evaluated ONCE per decision date using returns <= D_j (PIT-legal:
    decided at close D_j after observing it), frozen through the holding week. 10% ann
    target, clip<=3, min 60 obs; NaN-free (0.0 where unmeasurable)."""
    rx = r.dropna()
    vol = rx.expanding(min_periods=minlen).std(ddof=1) * np.sqrt(ANN)
    s = (target / vol.replace(0.0, np.nan)).clip(upper=cap)
    v = s.reindex(dec)
    return v.fillna(0.0) if v.isna().any() else v


# ---------------------------------------------------------------- composite (own)

def run_battery_own(net=None, rpu=None, sig=None, ref=None, spy=None, ief=None, cta=None,
                    scramble_n=200, seed=0) -> dict:
    """MY OWN composite battery: contract thresholds (SR>=1.0, halves>=0.5, neg<=2 &
    worst>-5%, |corr|<0.15, scr_p<0.05, leak_ok, beats-passive) judged on the BOOK
    sig*rpu; leak probe + scramble on (sig, rpu). All kwarg-driven, fail-closed."""
    book = pd.Series(np.asarray(sig, dtype=float) * np.asarray(rpu, dtype=float),
                     index=rpu.index)
    sr = sr_d(book)
    h1, h2 = halves(book)
    neg, worst = neg_years(book)
    if ref is not None:
        j = pd.concat([ref.rename("r"), book.rename("b")], axis=1).dropna()
        corr = float(j.r.corr(j.b)) if len(j) > 2 else np.nan
        corr_ok = bool(np.isfinite(corr) and abs(corr) < 0.15)
    else:
        corr = np.nan
        corr_ok = False
    scr_p, _ = scramble_p_own(sig, rpu, n=scramble_n, seed=seed)
    lp = leak_probe_own(sig, rpu)
    sr_ok = sr >= 1.0
    halves_ok = bool(h1 >= 0.5 and h2 >= 0.5)
    neg_ok = bool(neg <= 2 and worst > -0.05)
    ac1 = float(book.autocorr(1)) if len(book) > 2 else 0.0
    uniq = float(book.round(10).nunique() / len(book)) if len(book) else 0.0
    scr_ok = bool(np.isfinite(scr_p) and scr_p < 0.05)
    leak_ok = bool(lp["measurable"] and lp["leak"] is False)
    bp_best, bp_name, bp_info = best_passive_own(book, spy=spy, ief=ief, cta=cta)
    bp_ok = bool(np.isfinite(bp_best) and sr > bp_best)
    res = dict(sr=sr, h1=h1, h2=h2, neg_years=neg, worst=worst, corr=corr, corr_ok=corr_ok,
               scr_p=scr_p, ac1=ac1, uniq=uniq, sr_ok=sr_ok, halves_ok=halves_ok,
               neg_ok=neg_ok, scr_ok=scr_ok, leak_ok=leak_ok, leak=lp,
               bp_best=bp_best, bp_name=bp_name, bp_info=bp_info, bp_ok=bp_ok,
               n=len(book))
    res["pass"] = all([sr_ok, halves_ok, neg_ok, corr_ok, scr_ok, leak_ok, bp_ok])
    return res
