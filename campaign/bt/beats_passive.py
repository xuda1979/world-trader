"""bt.beats_passive — the MANDATORY "beats passive" acceptance gate (HUNT_INTERNATIONAL2 R3).

Motivation: rounds 1-2 of the international hunt kept producing positive-SR configs that were
provably long-beta in disguise (R1 EXT-B 0.68 losing to static 50/50; R2 RS252_LS 0.62 losing
to long-SPY 0.73). The campaign applied that audit ad-hoc each time. This module makes it a
first-class, TDD-tested gate so every future sleeve is judged against what NOT TRADING would
have earned on the SAME span, net of the SAME costs.

Benchmarks (all net of campaign-standard costs, all on the CANDIDATE's matched span):
  spy_bh       SPY buy-and-hold: flat on day 0 (the entry is decided at the first common
               close), earns from day 1 on, 6.4bps charged ONCE on the entry notional.
               No churn, no borrow.
  sixty_forty  60% SPY / 40% IEF, entered at day 1, re-balanced to target at each month
               start, weights DRIFT intra-month (a real monthly-rebalanced book), T+1,
               6.4bps on full |dW| via bt.engine.cost_turnover, no short leg -> no borrow.
  cta_trend    the library CTA_15vol curve (campaign/results/sleeve_library, [date,ret])
               converted to returns (native format passes through untouched; a price/equity
               curve is pct_change'd) and vol-targeted to 10% ann trailing-only
               (bt.engine.vol_target_scale, clip<=3) — same no-lookahead rule as sleeves.

Verdict (fail-closed): pass ONLY if candidate net SR > best passive SR on the matched span,
with at least one measurable benchmark (>= MIN_OBS usable observations). SR <= best passive
SR FAILS — ties are a fail (the sleeve's whole complexity buys nothing over not trading).
Missing benchmark data, empty overlap, or an invalid candidate all FAIL (never fail-open).

Wiring: opt-in via bt.gates.run(..., beats_passive=True, spy=..., ief=..., cta=...).
Default OFF — existing gates.run callers' semantics are unchanged.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from bt.engine import COST_BPS, ANN, cost_turnover, vol_target_scale
from bt.metrics import sharpe_d

MIN_OBS = 60  # matched-span benchmark needs >= 60 usable obs to be a fair comparison

REQUIRED = ("spy_bh", "sixty_forty", "cta_trend")


def _sr(r: pd.Series) -> float:
    return sharpe_d(r)


def _as_ret_series(x) -> pd.Series:
    """Accept a price/equity curve or a return series; return a daily return series.

    Normalization for benchmark inputs: values that look like a cumulated curve (all > 1e3)
    are pct_change'd; anything else is already a return series (the sleeve-library [date,ret]
    convention) and passes through untouched. A curve loses its first row (no prior close);
    returns lose none.

    Returns might be named 'close'/'px'/'equity' when the caller differenced a price column
    without renaming — the series VALUES, not the label, decide the transform (R3 real-data
    bug: SPY returns named 'close' were re-differenced, benchmark SR printed 0.000)."""
    if isinstance(x, pd.DataFrame):
        x = x.iloc[:, 0]
    x = pd.to_numeric(pd.Series(x), errors='coerce')
    looks_like_curve = bool(len(x.dropna()) and (x.dropna() > 1e3).all())
    return x.pct_change().dropna() if looks_like_curve else x.dropna()


def spy_buyhold(spy_ret: pd.Series, cand_index: pd.Index) -> pd.Series:
    """SPY B&H net return on the candidate's span. T+1 honest: you decide at the first
    common close, pay 6.4bps once on that entry, and earn from the NEXT close onward.
    Day 0 is flat 0.0 (you cannot earn day 0's close-to-close return off a day-0 decision).

    spy_ret: DAILY RETURNS (already differenced by the caller via _as_ret_series).
    Returns a series aligned to cand_index (NaN where SPY has no data -> the overlap
    accounting in best_passive_sr counts only real observations)."""
    r = pd.to_numeric(pd.Series(spy_ret), errors='coerce').reindex(cand_index)
    empty = pd.Series(np.nan, index=cand_index, dtype=float)
    if len(cand_index) < 2:
        return empty  # cannot establish even a 1-day position -> unmeasurable
    vals = r.to_numpy(copy=True)   # copy: the input series' buffer must never be mutated
    on = r.notna().to_numpy(copy=True)
    on[0] = False  # flat on day 0: entry decided at day-0 close, earns from day 1
    out = pd.Series(np.where(on, vals, 0.0), index=cand_index, dtype=float)
    k = int(np.argmax(on)) if on.any() else -1
    if k >= 0 and np.isfinite(out.iloc[k]):
        out.iloc[k] -= COST_BPS / 1e4  # ONE entry cost, charged on the first held day
    out[~on & r.isna().to_numpy()] = np.nan  # no SPY data -> NaN, not fake 0.0
    return out


def sixty_forty(spy_ret: pd.Series, ief_ret: pd.Series,
                cand_index: pd.DatetimeIndex) -> pd.Series:
    """60/40 SPY-IEF, entered at day 1, re-balanced to target at each month start, T+1,
    6.4bps on full |dW|, no borrow (no short leg).

    Weights DRIFT within each month with relative performance and snap back to 0.60/0.40 on
    the first trading day of each month — i.e. an actual monthly-rebalanced book, not a
    fixed-weight approximation. Turnover (and hence cost) includes the day-1 establishment
    and every monthly snap, via bt.engine.cost_turnover.

    Returns net daily return series aligned to cand_index."""
    if not isinstance(cand_index, pd.DatetimeIndex):
        raise ValueError("sixty_forty: cand_index must be a DatetimeIndex (monthly grouping)")
    spy_raw = pd.to_numeric(pd.Series(spy_ret), errors='coerce').reindex(cand_index)
    ief_raw = pd.to_numeric(pd.Series(ief_ret), errors='coerce').reindex(cand_index)
    # R4 mutation-found fail-open: with NO real data on a leg, the fillna(0.0) below
    # fabricates a benchmark out of the entry cost alone (SR -0.92 "measurable", n=span)
    # and an alpha candidate PASSES a comparison backed by zero market data. A benchmark
    # with a fabricated leg is not the documented 60/40: unmeasurable (all-NaN).
    if not (spy_raw.notna().any() and ief_raw.notna().any()):
        return pd.Series(np.nan, index=cand_index, dtype=float)
    rs = spy_raw.fillna(0.0).to_numpy()
    ri = ief_raw.fillna(0.0).to_numpy()
    T = len(cand_index)
    per = cand_index.to_period('M')
    is_ms = np.r_[True, per[1:] != per[:-1]]
    w_s = w_i = 0.0
    ws = np.zeros(T)
    wi = np.zeros(T)
    gross = np.zeros(T)
    for t in range(T):
        if t == 0:
            pass                       # flat day 0 (T+1 honest entry)
        elif t == 1 or is_ms[t]:
            w_s, w_i = 0.60, 0.40      # entry / monthly snap to target
        else:
            g = w_s * rs[t - 1] + w_i * ri[t - 1]
            d = 1.0 + g
            if not np.isfinite(d) or d <= 0.0:   # ruin guard: weights undefined
                w_s = w_i = 0.0
            else:
                w_s = w_s * (1.0 + rs[t - 1]) / d
                w_i = w_i * (1.0 + ri[t - 1]) / d
        gross[t] = w_s * rs[t] + w_i * ri[t]
        ws[t], wi[t] = w_s, w_i
    w_df = pd.DataFrame({'spy': ws, 'ief': wi}, index=cand_index)
    cost = cost_turnover(w_df)         # full |dW| incl. day-1 establishment (engine convention)
    return pd.Series(gross - cost.to_numpy(), index=cand_index, dtype=float)


def cta_trend_proxy(cta_curve: pd.Series, target: float = 0.10, window: int = 60,
                    cap: float = 3.0) -> pd.Series:
    """Library CTA_15vol equity curve/return series -> daily returns -> 10% ann vol-target
    (trailing only, bt.engine.vol_target_scale, same clip bounds as every campaign sleeve).
    T+1 via the shift(1) inside vol_target_scale."""
    r = _as_ret_series(cta_curve)
    scale = vol_target_scale(r.to_frame('r'), target=target, window=window, cap=cap)['r']
    return (r * scale).dropna()


def best_passive_sr(cand_ret: pd.Series, spy=None, ief=None, cta=None) -> tuple:
    """Compute all supplied benchmarks on the candidate's span; return
    (best_sr, info_dict). Benchmarks: spy_bh, sixty_forty (needs ief), cta_trend.
    A benchmark whose overlap has < MIN_OBS observations is 'unmeasurable' and skipped
    (fail-closed happens only when NONE are measurable)."""
    cand = pd.Series(cand_ret).dropna()
    if len(cand) == 0:
        return (np.nan, dict(reason='empty_candidate'))
    ci = cand.index
    spy_ret = _as_ret_series(spy) if spy is not None else None
    ief_ret = _as_ret_series(ief) if ief is not None else None

    benchmarks = {}
    if spy_ret is not None:
        benchmarks['spy_bh'] = spy_buyhold(spy_ret, ci)
    if spy_ret is not None and ief_ret is not None:
        benchmarks['sixty_forty'] = sixty_forty(spy_ret, ief_ret, ci)
    if cta is not None:
        benchmarks['cta_trend'] = cta_trend_proxy(cta).reindex(ci)

    info = {}
    for name, series in benchmarks.items():
        s = series.dropna()
        # a benchmark is only measurable if it has a real position history on the span.
        # NaN-poisoning guard (R3 real-data bug: a benchmark whose returns were NaN over
        # half the span computed a garbage SR from the surviving points): require real
        # observations over at least half the candidate span, else unmeasurable.
        n_span = len(cand)
        # DATA_ETF_MORE R6 (GATES_CONTRACT_V2 §7 discipline): a benchmark book that never
        # varies on the span (all-0.0 returns — the library CTA_15vol placeholder window
        # 2008-01-03..2008-10-17, rows 0..200; or an all-NaN leg already returning all-NaN)
        # has NO position history to compare against. sharpe_d() floors its zero variance
        # to a finite SR 0.0, which HEAD accepted as 'measurable' and which wins 'best' on
        # crash spans where every tradable benchmark is negative. Zero variance on a
        # benchmark BOOK is unmeasurable, loud — same fail-closed rule as <MIN_OBS.
        if s.std(ddof=1) < 1e-12:
            info[name] = dict(sr=np.nan, n=len(s),
                              note='unmeasurable(zero-variance book: benchmark never traded on span)')
        elif len(s) >= MIN_OBS and len(s) >= 0.5 * n_span:
            info[name] = dict(sr=_sr(s), n=len(s))
        else:
            info[name] = dict(sr=np.nan, n=len(s),
                              note='unmeasurable(<MIN_OBS or sparse-overlap)')
    measurable = {k: v for k, v in info.items() if np.isfinite(v['sr'])}
    if not measurable:
        return (np.nan, info)
    bk = max(measurable, key=lambda k: measurable[k]['sr'])
    return (float(measurable[bk]['sr']), info)


def evaluate(cand_ret: pd.Series, spy=None, ief=None, cta=None) -> dict:
    """Full gate: dict with candidate_sr, per-benchmark SRs on the matched span, the best
    passive SR, margin (cand - best), and the fail-closed verdict."""
    cand = pd.Series(cand_ret).dropna()
    best_sr, info = best_passive_sr(cand, spy=spy, ief=ief, cta=cta)
    out = dict(candidate_sr=_sr(cand) if len(cand) else np.nan,
               benchmarks=info, best=None, reason=None)
    if not np.isfinite(out['candidate_sr']) or len(cand) == 0:
        out['reason'] = 'invalid_candidate'
        return _finish(out)
    if not np.isfinite(best_sr):
        # no benchmark data supplied at all vs. benchmarks supplied but unmeasurable on the span
        out['reason'] = 'no_benchmark' if not info else 'no_overlap'
        return _finish(out)
    name = max((k for k, v in info.items() if np.isfinite(v['sr'])),
               key=lambda k: info[k]['sr'])
    out['best'] = dict(sr=best_sr, name=name, n=info[name]['n'])
    out['margin'] = out['candidate_sr'] - best_sr
    if out['margin'] <= 0.0:
        out['reason'] = 'candidate_sr_le_passive'
    return _finish(out)


def _finish(out: dict) -> dict:
    """pass is True only when a best passive SR was measurable AND strictly beaten."""
    out['pass'] = bool(out.get('margin') is not None and out['margin'] > 0.0)
    return out


# ------------------------------------------------------------------ gates.run wiring

def gate(r: pd.Series, spy=None, ief=None, cta=None) -> dict:
    """Boolean gate result shaped like the other gates.* verdicts: {'beats_passive_ok', ...}."""
    ev = evaluate(r, spy=spy, ief=ief, cta=cta)
    return dict(beats_passive_ok=bool(ev['pass']), candidate_sr=ev['candidate_sr'],
                best_passive_sr=(ev['best'] or {}).get('sr', np.nan),
                best_passive_name=(ev['best'] or {}).get('name'),
                margin=ev.get('margin'), reason=ev['reason'], detail=ev['benchmarks'])


# alias: the gate is also addressable by the module's own name (tests/callers both work)
beats_passive = gate
