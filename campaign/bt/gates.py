"""Acceptance gates for a candidate sleeve (honest, TDD-tested, all numbers explicit)."""
from __future__ import annotations
import numpy as np
import pandas as pd
from bt.metrics import sharpe_d, half_split, neg_years

# campaign-standard acceptance thresholds — aligned to GATES_CONTRACT.md (AUDIT_GATES2 R1:
# were 0.6/0.3, i.e. LOOSER than the contract's SR>=1.0 / halves>=0.5, so gates.run() could
# declare 'pass' on a sleeve that is NOT champion-eligible under the contract).
DEFAULTS = dict(sr_min=1.0, h_min=0.5, neg_max=2, neg_floor=-0.05,
                corr_max=0.15, ac1_max=0.5, uniq_min=0.08, p_max=0.05)


def lag1_autocorr(r: pd.Series) -> float:
    return float(r.autocorr(1)) if len(r) > 2 else 0.0


def uniq_ratio(r: pd.Series) -> float:
    """Fraction of distinct daily values (flattening gate: XGB1y trap)."""
    r = r.round(10)
    return float(r.nunique() / len(r)) if len(r) else 0.0


def zero_runs_long(r: pd.Series, min_run: int = 20):
    """Indices of interior exact-zero runs >= min_run (design-explained or red flag)."""
    z = r.eq(0.0)
    # drop only the boundary bookends if they are NOT part of an interior run; simplest: count runs
    # over the FULL series (including leading/trailing), which is the honest 'interior>=min' semantics
    out = []
    if z.any():
        groups = (z & ~z.shift(1, fill_value=False)).cumsum()
        cnt = z.groupby(groups).sum()
        for k, v in cnt.items():
            if v >= min_run:
                out.append(int(v))
    return out


def corr_to(ref: pd.Series, r: pd.Series) -> float:
    j = pd.concat([ref.rename('r'), r.rename('s')], axis=1).dropna()
    return float(j.r.corr(j.s)) if len(j) > 2 else np.nan


def plateau_ok(grid: dict, chosen, tol: float = 0.2) -> tuple:
    """Contract gate b): the chosen param must sit on a PLATEAU, not a spike.

    grid: {param_value: sr_at_that_param}. ALL of the chosen point's adjacent neighbors must
    have SR >= (1-tol) * peak SR, where peak = max over the grid. A single-spike grid (both
    neighbors far below peak) AND a half-spike (one strong + one collapsed neighbor) are
    rejected (AUDIT_GATES2 R1: neighbor_frac=0.5 let a one-sided cliff pass with neighbor SR
    0.08 vs peak 2.50). At a grid edge only the available neighbors count.
    Returns (ok: bool, info: dict with neighbor details)."""
    if not grid or chosen not in grid:
        return (False, dict(reason='chosen_param_not_in_grid'))
    keys = sorted(grid)
    i = keys.index(chosen)
    nb = [k for k in (keys[i - 1] if i > 0 else None, keys[i + 1] if i + 1 < len(keys) else None)
          if k is not None]
    peak = max(grid.values())
    if peak <= 0:
        return (False, dict(reason='nonpositive_peak', peak=peak))
    good = [k for k in nb if grid[k] >= (1.0 - tol) * peak]
    ok = bool(nb) and len(good) == len(nb)
    return (ok, dict(neighbors={k: grid[k] for k in nb}, peak=peak,
                     threshold=(1.0 - tol) * peak, good_neighbors=good,
                     edge=(len(nb) < 2)))


def run(r: pd.Series, ref=None, sig=None, scramble_n: int = 200, **kw) -> dict:
    """Outer acceptance gate. Returns per-gate result dict + a boolean PASS (all True).

    AUDIT_GATES2 R2 charter (a): the scramble gate is ENFORCED here, fail-closed. Pass the
    candidate's positions as `sig`; without them the scramble is unmeasurable -> scr_p=NaN,
    scr_ok=False, composite pass=False (procedural-only compliance was the R1 caveat).

    GATES_CONTRACT_V2 section-6 Step-2 (2026-09-08): the leak gate is DEFAULT-ON — every
    run() call without an explicit leak_check kwarg is probed for same-period lookahead;
    sig-less calls fail closed via leak_ok=False. Pass sig= (the candidate's positions)
    on any acceptance-track call; leak_check=False is measurement-only (V2 section 6e).

    Contract when sig IS supplied: r = PER-UNIT returns, and every performance gate judges
    the candidate BOOK sig*r (the thing that would actually be held), while the scramble
    judges the positions against those same per-unit returns. A mismatched/noise claim then
    destroys the book SR (sr_ok fails) AND fails the scramble — the two controls the R2
    audit demanded. (Reconstructing raw from (sig, book) instead was tried and REJECTED:
    with +-1 positions any claimed sig "reconstructs" a raw that reproduces the book, so
    the scramble certifies noise — vacuous.)
    """
    p = {**DEFAULTS, **kw}
    # HUNT_INTERNATIONAL2 R3 charter (a): OPTIONAL mandatory-beats-passive gate. Default OFF
    # (existing callers' semantics unchanged); when opted in via beats_passive=True the
    # verdict is ANDed into the composite pass — a sleeve that loses to buy-and-hold on its
    # own span is not champion-eligible no matter what the other gates say.
    bp_on = bool(p.pop('beats_passive', False))
    bp_data = {k: p.pop(k, None) for k in ('spy', 'ief', 'cta')}
    # GATES_CONTRACT_V2 section-6 Step-2 (ratified 2026-09-08, flip executed by AUDIT_FWBUGS
    # R5): the same-period lookahead gate is DEFAULT-ON. leak_probe correlates the day-t
    # decision quantity with r_t (the T+1 enforcement gap — AUDIT_GATES2's top caveat, and
    # the exact defect that put the archived champion at 40.84% vs honest 39.85%).
    # Unmeasurable => leak_ok=False (fail-closed); without sig the probe has nothing to
    # test => leak_ok=False (fail-closed, same rule as scr). leak_check=False explicitly
    # restores measurement-only semantics — a contract violation on an acceptance-track
    # call (V2 section 6e), it exists only for module-level measurement use.
    leak_on = bool(p.pop('leak_check', True))
    if sig is not None:
        sig_arr = np.asarray(sig, dtype=float)
        r_eff = pd.Series(sig_arr * r.values, index=r.index)
        # block=20 matches scramble_positions' own default and the R2 controls: series too
        # short to roll (2*block >= T) come back p=NaN -> fail closed, which is the point.
        scr_p, _ = scramble_positions(sig_arr, r.values, n=scramble_n, block=20)
    else:
        r_eff = r
        scr_p = np.nan
    sr = sharpe_d(r_eff); h1, h2 = half_split(r_eff); neg, worst = neg_years(r_eff)
    # autocorr/uniq/zero-runs are book diagnostics too -> judge the claimed book
    ac1v = lag1_autocorr(r_eff); univ = uniq_ratio(r_eff); zr = zero_runs_long(r_eff)
    res = dict(
        sr=sr, sr_ok=sr >= p['sr_min'],
        h1=h1, h2=h2, halves_ok=(h1 >= p['h_min'] and h2 >= p['h_min']),
        neg_years=neg, worst=worst,
        neg_ok=(neg <= p['neg_max'] and worst > p['neg_floor']),
        ac1=ac1v, ac1_ok=ac1v < p['ac1_max'],
        uniq=univ, uniq_ok=univ >= p['uniq_min'],
        corr=(corr_to(ref, r_eff) if ref is not None else np.nan),
        # AUDIT_GATES2 R1: ref=None used to set corr_ok=True (fail-OPEN) — a sleeve evaluated
        # without the champion ref sailed through decorrelation unchecked. Fail closed.
        corr_ok=(bool(abs(corr_to(ref, r_eff)) < p['corr_max']) if ref is not None else False),
        zruns=zr,
        scr_p=scr_p,
        # p NaN (unmeasurable) must fail; p_max=0.05 threshold from DEFAULTS stands.
        scr_ok=(bool(np.isfinite(scr_p)) and scr_p < p['p_max']),
    )
    res['pass'] = all(res[k + '_ok'] for k in ['sr', 'halves', 'neg', 'ac1', 'uniq', 'corr', 'scr'])
    if leak_on:
        from bt.leakcheck import leak_probe, gates_flag
        # AUDIT_FWBUGS R3 bugfix (TDD, found 2026-09-07): leak_check on WITHOUT a signal
        # previously raised UnboundLocalError on sig_arr (defined only under `if sig is not
        # None`) — a fail-LOUD crash instead of fail-CLOSED. Unmeasurable => leak_ok=False,
        # consistent with the scr/leak fail-closed contract for absent sig.
        if sig is not None:
            probe = leak_probe(sig_arr, r.values)
            res['leak'] = probe
            res['leak_ok'] = gates_flag(probe)
            res['pass'] = bool(res['pass'] and res['leak_ok'])
        else:
            res['leak'] = None
            res['leak_ok'] = False
            res['pass'] = False
    if bp_on:
        from bt.beats_passive import gate as bp_gate
        # AUDIT_GATES2 R3 (GATES_CONTRACT v2 draft 7a): the gate is "beat the best of the
        # TRIO {spy_bh, sixty_forty, cta_trend}". A subset (e.g. spy only) judged the
        # candidate against the survivors alone — a book that beats SPY but loses to 60/40
        # read beats_passive_ok=True (fail-OPEN vs the contract). The acceptance layer
        # therefore requires the complete trio; a missing benchmark fails closed with an
        # explicit reason, same rule as ref=None -> corr_ok=False (R1) and sig=None ->
        # scr_ok/leak_ok=False (R2 / FWBUGS R3). (bt.beats_passive.evaluate keeps subset
        # semantics for measurement; the strictness lives at the acceptance layer.)
        if any(v is None for v in bp_data.values()):
            bp = dict(beats_passive_ok=False, candidate_sr=sr, best_passive_sr=np.nan,
                      best_passive_name=None, margin=None, reason='incomplete_trio',
                      detail={k: ('supplied' if v is not None else 'missing')
                              for k, v in bp_data.items()})
        else:
            bp = bp_gate(r_eff, **bp_data)
        res['beats_passive'] = bp
        res['beats_passive_ok'] = bp['beats_passive_ok']
        res['pass'] = bool(res['pass'] and bp['beats_passive_ok'])
    return res


def scramble_positions(sig, r, side=0, n=200, block=10, rng=None):
    """Position-lag scramble p-value for a 2-leg book. Rolls POSITIONS by a random lag in
    [block, len-block]; returns fraction of scrambled-book SR >= real SR. Returns (p, real_sr)."""
    rng = rng or np.random.default_rng(0)
    sig = np.asarray(sig, dtype=float); r = np.asarray(r, dtype=float)
    # FIX (VERIFY_BEST §4c): baseline must be the REAL BOOK's SR (positions x returns),
    # NOT the raw-return SR (which would accept a destroyed book and spuriously fail real ones).
    # AUDIT_GATES2 R2: sharpe_d() skips NaNs, so a NaN-contaminated book used to report a
    # bogus real SR and a garbage p. Unmeasurable = fail closed: (NaN, NaN).
    if not np.isfinite(sig).all() or not np.isfinite(r).all():
        return (np.nan, np.nan)
    real_sr = sharpe_d(pd.Series(sig * r))
    T = len(r)
    lo, hi = block, T - block
    if hi <= lo:
        return (np.nan, real_sr)
    cnt = 0
    for _ in range(n):
        lag = rng.integers(lo, hi + 1)
        s = np.roll(sig, lag)
        # re-costs not applied here (positions only) — conservative for positive-SR
        book = s * r
        if sharpe_d(pd.Series(book)) >= real_sr:
            cnt += 1
    return (cnt / n, real_sr)
