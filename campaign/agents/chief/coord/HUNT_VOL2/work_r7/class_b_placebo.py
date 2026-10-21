"""Class-B LEVEL-MATCHED null placebo — reference implementation (HUNT_VOL2 R7).

V3 PROPOSAL instrument per work_r6/placebo_orthogonal_memo.md (docs-only R6 memo). This
module is a REUSABLE HELPER + reference implementation for the V3 contract discussion;
it is NOT an edit to GATES_CONTRACT_V2 (AUDIT_GATES2 ratifies) and NOT wired into
bt/gates.py. Zero thresholds move; a placebo verdict is a necessary-condition reading,
never an adoption claim (out["verdict"] carries "not_an_adoption" by construction).

WHY (R6 memo, one paragraph): GATES_CONTRACT_V2 §8h as flown (200 circular shifts /
matched random trims) is a valid significance instrument exactly when a candidate's
delta lives in co-movement with the champion (Class A, correlated overlays). For an
ORTHOGONAL positive-mean candidate (Class B, e.g. HOBR corr_champ +0.0219) mistiming
cannot destroy what the blend uses: variance-reduction is shift-invariant and
mean-injection survives re-ordering, so the null saturates by arithmetic (coordinator
measurement: 169/200 mistimed draws reproduce the dSR delta). The Class-B instrument
instead builds 200 block-bootstrap draws of the candidate's OWN stream re-matched on
(mean, vol, skew, ac1) — level-matched, so "any positive-mean stream at this vol" is
the null — and requires the real candidate's blend dSR to sit at p95+ of that null
before any timing/signal reading is allowed.

CLASS RULES (memo §3):
  classify(|corr|)      -> A: |corr| > 0.50 (§8h as flown, UNCHANGED)
                           B: |corr| < 0.40 (B1 below; B2 corroborator only)
                           STRADDLER: 0.40 <= |corr| <= 0.50 (run BOTH; stricter wins;
                           a placebo can never upgrade a candidate)
  timing_split          -> DIAGNOSTIC-ONLY (B2 corroborator, §11 diagnostics-not-gates)

Costs/conventions (mirrors work_r3/blend_r3_lib.py, pinned by its tests): constant-mix
blend (1-w)*champ + w*sleeve on ALREADY-COSTED nets; champion gross 1.6 / sleeve gross
1.0 inside their slices (margin cancels in the linear blend at equal rates); the only
new trade is blend-weight rebalancing, one-side FULL |dW| = 2*|(1-w) - Wc_prev| at
6.4 bps, Wc from PRIOR-day NAVs (T+1, no lookahead), day-0 establishment uncharged.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ANN = 252.0
BPS = 6.4

CLASS_A_ABS_CORR = 0.50   # > this: correlated overlay, §8h as flown
CLASS_B_ABS_CORR = 0.40   # < this: orthogonal standalone, B1 instrument
STRADDLE_LO, STRADDLE_HI = 0.40, 0.50

MIN_OBS = 100             # a blend null needs a usable span
MIN_BLOCK, MAX_BLOCK_FRAC = 2, 0.10
P_TAIL = 0.95             # "right tail of its own null" bar (memo B1)


# ------------------------------------------------------------------- utilities
def stream_moments(s: pd.Series) -> dict:
    """(mean, vol, skew, ac1) of a daily return stream — the level-match target set."""
    s = pd.Series(s).astype(float)
    if s.isna().any():
        raise ValueError("stream_moments: NaN in stream (fail-closed, no forward-fill)")
    return dict(mean=float(s.mean()), vol=float(s.std(ddof=1)),
                ac1=float(s.autocorr(1)), skew=float(s.skew()))


def _daily_sharpe(r: pd.Series) -> float:
    sd = float(r.std(ddof=1))
    return float("nan") if sd <= 1e-12 else float(r.mean() / sd * np.sqrt(ANN))


def blend_simple(rc: pd.Series, rs: pd.Series, w: float, bps: float = BPS) -> pd.Series:
    """Constant-mix blend (1-w)*rc + w*rs minus 6.4bps FULL-|dW| rebalance drift cost
    (one-side book turnover = 2*|(1-w) - Wc_prev|, Wc from PRIOR-day NAVs, T+1).
    Mirror of work_r3/blend_r3_lib.blend_metrics cost algebra on clean shared-index
    inputs; margin cancels in the linear blend at equal rates (R3 test-pinned)."""
    if not rc.index.equals(rs.index):
        raise ValueError("blend_simple: champion and sleeve must share one index")
    if not 0.0 < w < 1.0:
        raise ValueError(f"blend_simple: w out of range: {w}")
    Wc = (1 - w) * (1 + rc) / ((1 - w) * (1 + rc) + w * (1 + rs))
    to = (2.0 * ((1 - w) - Wc.shift(1))).abs().fillna(0.0)
    return (1 - w) * rc + w * rs - to * bps / 1e4


def blend_delta(rc: pd.Series, rs: pd.Series, w: float, bps: float = BPS) -> dict:
    """dSR and dAnn (CAGR) of blending the candidate in at w, vs champion alone."""
    base = rc
    bl = blend_simple(rc, rs, w, bps)
    nav = lambda x: (1 + x).cumprod()
    cagr = lambda x: float((1 + x).prod() ** (ANN / len(x)) - 1)
    return dict(dsr=_daily_sharpe(bl) - _daily_sharpe(base),
                dann=float(cagr(bl) - cagr(base)),
                sr_base=_daily_sharpe(base), sr_blend=_daily_sharpe(bl))


def level_matched_nulls(s: pd.Series, n: int, block: int,
                        rng: np.random.Generator, tries: int = 8) -> list:
    """n block-bootstrap draws of the candidate's OWN stream, each re-matched on
    (mean, vol) exactly and (skew, ac1) approximately.

    Construction per memo B1: circular block bootstrap of the candidate's own daily
    returns at block length L (destroys day-alignment/calendar structure, preserves
    marginal + short-memory structure on average), then EXACT re-match of mean (additive)
    and vol (multiplicative). Within-bootstrap-family moment retry: each published draw
    is the best of `tries` bootstrap resamples by |dSkew| + |dAC1| vs the real stream
    (spike-heavy streams — HOBR skew 3.6 — have noisy draw-level higher moments; the
    retry tightens the match WITHOUT leaving the candidate's own data family, i.e. no
    synthetic observations are ever introduced). Level-matching is the point: the null
    answers "any stream with this risk fingerprint and this LEVEL, no timing content",
    so mean-injection is priced OUT of the statistic instead of saturating it (the
    §8h-as-mistiming failure)."""
    s = pd.Series(s).astype(float)
    if s.isna().any():
        raise ValueError("level_matched_nulls: NaN interior (fail-closed)")
    if len(s) < MIN_OBS:
        raise ValueError(f"level_matched_nulls: n={len(s)} < MIN_OBS {MIN_OBS}")
    if not (MIN_BLOCK <= block <= max(MIN_BLOCK, int(MAX_BLOCK_FRAC * len(s)))):
        raise ValueError(f"level_matched_nulls: block={block} outside "
                         f"[{MIN_BLOCK}, {MAX_BLOCK_FRAC:.0%} of n]")
    if float(s.std(ddof=1)) <= 1e-12:
        raise ValueError("level_matched_nulls: zero-vol stream")
    x = s.values
    T = len(x)
    n_blocks = int(np.ceil(T / block))
    starts_max = T - block + 1
    if starts_max < MIN_BLOCK:
        raise ValueError("level_matched_nulls: span too short for one block")
    m0, v0 = float(s.mean()), float(s.std(ddof=1))
    sk0, ac0 = float(s.skew()), float(s.autocorr(1))

    def one_raw():
        starts = rng.integers(0, starts_max, size=n_blocks)
        idx = (starts[:, None] + np.arange(block)[None, :]).ravel()[:T]
        d = x[idx].copy()                       # circular: may wrap; marginal preserved
        d = d - d.mean()
        d = d * (v0 / d.std(ddof=1))
        d = d + m0
        return d

    def moment_gap(d):
        return abs(float(pd.Series(d).skew()) - sk0) + \
               3.0 * abs(float(pd.Series(d).autocorr(1)) - ac0)

    out = []
    for _ in range(int(n)):
        best = None
        best_gap = np.inf
        for _ in range(max(1, int(tries))):
            d = one_raw()
            gap = moment_gap(d)
            if gap < best_gap:
                best, best_gap = d, gap
        out.append(pd.Series(best, index=s.index))
    return out


# ------------------------------------------------------------- the instruments
def class_b_placebo(rc: pd.Series, rs: pd.Series, w: float, n_nulls: int = 200,
                    block: int = 20, rng: np.random.Generator = None,
                    bps: float = BPS) -> dict:
    """B1: blend dSR/dAnn of the REAL candidate vs the null distribution of 200
    level-matched re-orderings of the SAME stream. SURVIVES only at p95+ of its own
    null (P_TAIL) — i.e. the gain is not reproducible by a no-timing stream with the
    same level/vol/skew/AC. Real-vs-null is the decision reading; the dAnn side is
    reported in parallel (the R6 HOBR case: dSR p1.00 / dAnn p0.00 = positive-SR
    arithmetic, negative absolute-return trade)."""
    rng = rng or np.random.default_rng(0)
    rc, rs = pd.Series(rc).astype(float), pd.Series(rs).astype(float)
    if len(rc) != len(rs) or not rc.index.equals(rs.index):
        raise ValueError("class_b_placebo: champion/candidate must share one index")
    if rc.isna().any() or rs.isna().any():
        raise ValueError("class_b_placebo: NaN interior (fail-closed)")
    if len(rc) < MIN_OBS:
        raise ValueError(f"class_b_placebo: n={len(rc)} < MIN_OBS {MIN_OBS}")
    if int(n_nulls) < 2:
        raise ValueError("class_b_placebo: n_nulls < 2 (no distribution)")
    if not 0.0 < w <= 0.15:
        raise ValueError(f"class_b_placebo: w={w} outside (0, 0.15] charter rung cap")
    real = blend_delta(rc, rs, w, bps)
    nulls = level_matched_nulls(rs, n=int(n_nulls), block=int(block), rng=rng)
    null_d = [blend_delta(rc, d, w, bps) for d in nulls]
    ndsr = np.array([d["dsr"] for d in null_d])
    ndann = np.array([d["dann"] for d in null_d])
    pct = lambda arr, v: float((arr < v).mean() + 0.5 * (arr == v).mean())
    out = dict(
        instrument="class_b_level_matched_block_bootstrap",
        n_nulls=int(n_nulls), block=int(block), w=float(w), n=len(rc),
        real_dsr=real["dsr"], real_dann=real["dann"],
        null_dsr_p50=float(np.percentile(ndsr, 50)),
        null_dsr_p95=float(np.percentile(ndsr, 95)),
        null_dann_p50=float(np.percentile(ndann, 50)),
        real_percentile=pct(ndsr, real["dsr"]),
        real_ann_percentile=pct(ndann, real["dann"]),
        right_tail_p95_pass=bool(pct(ndsr, real["dsr"]) >= P_TAIL),
        verdict="SURVIVES_PLACEBO" if pct(ndsr, real["dsr"]) >= P_TAIL
        else "PLACEBO_ARTIFACT",
        matched=stream_moments(rs),
        not_an_adoption=("placebo verdicts are necessary-condition readings; "
                         "adoption requires the FULL V2 battery (gates 8a-8j)"))
    return out


def gaussian_matched_placebo(rc: pd.Series, rs: pd.Series, w: float, n_nulls: int = 200,
                             rng: np.random.Generator = None, bps: float = BPS) -> dict:
    """Class-A §8h instrument AS FLOWN in R3 (unchanged): n vol+corr-matched Gaussian
    nulls (exact per-draw vol and champion-corr, in-sample orthogonalization), same
    blend machinery; majority-positive null dSR => DIVERSIFICATION ARTIFACT. Kept for
    straddlers and for Class-A candidates; do NOT use on Class-B (saturates by
    arithmetic — the documented failure mode)."""
    rng = rng or np.random.default_rng(0)
    rc, rs = pd.Series(rc).astype(float), pd.Series(rs).astype(float)
    if not rc.index.equals(rs.index):
        raise ValueError("gaussian_matched_placebo: must share one index")
    if rc.isna().any() or rs.isna().any():
        raise ValueError("gaussian_matched_placebo: NaN interior (fail-closed)")
    target_corr = float(pd.concat([rc, rs], axis=1).corr().iloc[0, 1])
    target_vol = float(rs.std(ddof=1))
    base_sr = _daily_sharpe(rc)
    z = ((rc - rc.mean()) / rc.std(ddof=1)).values
    null_dsrs = np.empty(int(n_nulls))
    null_dsrs_ann = np.empty(int(n_nulls))
    for i in range(int(n_nulls)):
        e = rng.standard_normal(len(rc))
        e = e - e.mean()
        e = e - z * (z @ e) / (z @ z)          # orthogonalize noise in sample
        e = e / e.std(ddof=1)
        x = target_corr * z + np.sqrt(max(1.0 - target_corr ** 2, 1e-12)) * e
        s = pd.Series(x, index=rc.index)
        s = s * (target_vol / s.std(ddof=1))   # exact vol match
        d = blend_delta(rc, s, w, bps)
        null_dsrs[i] = d["dsr"]
        null_dsrs_ann[i] = d["dann"]
    frac_pos = float((null_dsrs > 0).mean())
    out = dict(instrument="gaussian_vol_corr_matched", n_nulls=int(n_nulls),
               w=float(w), frac_null_dsr_pos=frac_pos,
               null_dsr_p50=float(np.percentile(null_dsrs, 50)),
               null_dsr_p95=float(np.percentile(null_dsrs, 95)),
               null_dsr=np.sort(null_dsrs).tolist(),
               real_dsr=None, target_vol=target_vol, target_corr=target_corr,
               verdict="PLACEBO_ARTIFACT" if frac_pos > 0.5 else "SURVIVES_PLACEBO",
               not_an_adoption=("placebo verdicts are necessary-condition readings; "
                                "adoption requires the FULL V2 battery (gates 8a-8j)"))
    return out


def circular_shift_placebo(rc: pd.Series, rs: pd.Series, w: float, n_nulls: int = 200,
                           rng: np.random.Generator = None, bps: float = BPS) -> dict:
    """§8h circular-shift variant (the coordinator's R6 instrument on HOBR), kept for
    Class-A use and for reproduction of the 169/200 measurement. For Class-B candidates
    this saturates by arithmetic — B1 above is the decision instrument (memo §3)."""
    rng = rng or np.random.default_rng(0)
    rc, rs = pd.Series(rc).astype(float), pd.Series(rs).astype(float)
    if not rc.index.equals(rs.index):
        raise ValueError("circular_shift_placebo: must share one index")
    base = _daily_sharpe(rc)
    real = _daily_sharpe(blend_simple(rc, rs, w, bps)) - base
    null_dsr = []
    T = len(rs)
    vals = rs.values
    for _ in range(int(n_nulls)):
        k = int(rng.integers(0, T))
        d = pd.Series(np.roll(vals, k), index=rs.index)
        null_dsr.append(_daily_sharpe(blend_simple(rc, d, w, bps)) - base)
    ndsr = np.array(null_dsr)
    out = dict(instrument="circular_shift", n_nulls=int(n_nulls), w=float(w),
               real_dsr=float(real), null_dsr_p50=float(np.percentile(ndsr, 50)),
               null_dsr_p95=float(np.percentile(ndsr, 95)),
               null_dsr=np.sort(ndsr).tolist(),
               reproduced_frac=float((ndsr > 0).mean()),
               matched=stream_moments(rs),
               not_an_adoption=("placebo verdicts are necessary-condition readings; "
                                "adoption requires the FULL V2 battery (gates 8a-8j)"))
    return out


def timing_split_diagnostic(rc: pd.Series, rs: pd.Series, w: float, n_nulls: int = 40,
                            block: int = 20, rng: np.random.Generator = None,
                            bps: float = BPS) -> dict:
    """B2 SUBSAMPLE TIMING SPLIT — DIAGNOSTIC ONLY, NEVER A GATE (§11 rule, memo §3).
    Corroborator question: is the real-vs-null gap stable across time halves? No
    verdict key is emitted (nothing can be accepted or rejected with this)."""
    out = _timing_split_impl(rc, rs, w, n_nulls, block, rng, bps)
    return out


def _timing_split_impl(rc, rs, w, n_nulls, block, rng, bps):
    rc, rs = pd.Series(rc).astype(float), pd.Series(rs).astype(float)
    if not rc.index.equals(rs.index):
        raise ValueError("timing_split_diagnostic: must share one index")
    if rc.isna().any() or rs.isna().any():
        raise ValueError("timing_split_diagnostic: NaN interior (fail-closed)")
    k = len(rc) // 2
    halves = {}
    for name, (a, b) in {"H1": (rc.iloc[:k], rs.iloc[:k]),
                         "H2": (rc.iloc[k:], rs.iloc[k:])}.items():
        try:
            h = class_b_placebo(a, b, w=w, n_nulls=int(n_nulls), block=int(block),
                                rng=rng, bps=bps)
            halves[name] = dict(real_dsr=h["real_dsr"],
                                null_dsr_p50=h["null_dsr_p50"],
                                real_percentile=h["real_percentile"])
        except ValueError as exc:
            halves[name] = dict(unmeasurable=str(exc))
    return dict(status="DIAGNOSTIC_ONLY_never_a_gate", instrument="b2_timing_split",
                H1=halves["H1"], H2=halves["H2"], halves=halves,
                note=("stable real-vs-null gap across halves CORROBORATES timing "
                      "content; instability is expected for pure mean-injection — "
                      "evidence only, never accepted or rejected on this"))


# ---------------------------------------------------------- routing / verdicts
def classify(corr: float) -> str:
    """Candidate class from |corr to champion| (memo §3 thresholds; V3 proposal)."""
    c = abs(float(corr))
    if c > 1.0:
        raise ValueError(f"classify: |corr|>1: {corr}")
    if c > CLASS_A_ABS_CORR:
        return "A"
    if c < CLASS_B_ABS_CORR:
        return "B"
    return "STRADDLER"


def placebo_verdict(rc: pd.Series, rs: pd.Series, w: float, n_nulls: int = 200,
                    block: int = 20, corr: float = None,
                    rng: np.random.Generator = None, bps: float = BPS) -> dict:
    """Full routing per memo §3: classify on |corr_to_champion| (measured here if not
    given), run the right instrument(s) — Class A -> §8h Gaussian-matched AS FLOWN;
    Class B -> B1 level-matched (B2 split as corroborator, caller-invoked); STRADDLER
    -> BOTH, stricter reading wins. A placebo verdict can never UPGRADE a candidate:
    the composite survives only if EVERY instrument run says SURVIVES_PLACEBO."""
    rc, rs = pd.Series(rc).astype(float), pd.Series(rs).astype(float)
    if not rc.index.equals(rs.index):
        raise ValueError("placebo_verdict: champion/candidate must share one index")
    if corr is None:
        corr = float(pd.concat([rc, rs], axis=1).corr().iloc[0, 1])
    cls = classify(corr)
    out = dict(corr_to_champion=float(corr), **{"class": cls})
    runs = {}
    if cls == "A":
        runs["gaussian_matched"] = gaussian_matched_placebo(
            rc, rs, w=w, n_nulls=n_nulls, rng=rng, bps=bps)
    elif cls == "B":
        runs["class_b"] = class_b_placebo(rc, rs, w=w, n_nulls=n_nulls, block=block,
                                          rng=rng, bps=bps)
    else:  # STRADDLER: run BOTH, stricter wins
        seed0 = int(rng.integers(0, 2**31 - 1)) if rng is not None else 0
        runs["class_b"] = class_b_placebo(
            rc, rs, w=w, n_nulls=n_nulls, block=block,
            rng=np.random.default_rng(seed0), bps=bps)
        runs["gaussian_matched"] = gaussian_matched_placebo(
            rc, rs, w=w, n_nulls=n_nulls,
            rng=np.random.default_rng(seed0 + 1), bps=bps)
    survives = all(v["verdict"] == "SURVIVES_PLACEBO" for v in runs.values())
    killed_by = [k for k, v in runs.items() if v["verdict"] != "SURVIVES_PLACEBO"]
    out.update(
        instruments_run=list(runs.keys()),
        instruments=runs,
        survives_placebo=bool(survives),
        killed_by=killed_by,
        verdict="SURVIVES_PLACEBO" if survives else "PLACEBO_ARTIFACT",
        stricter_reading="both instruments must agree to survive; any PLACEBO_ARTIFACT kills",
        not_an_adoption=("placebo verdicts are necessary-condition readings; "
                         "adoption requires the FULL V2 battery (gates 8a-8j)"))
    return out
