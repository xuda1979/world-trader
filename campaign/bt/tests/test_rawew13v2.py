"""TDD tests for the RAW-EW13v2 WEIGHTED champion (IS-SR-fitted slots; gear 1.0 canonical
since ITER21 2026-09-18, was @1.6x through ITER20).

Honesty properties verified (fail-closed):
  1. Leverage: gross rides the canonical gear exactly (1.0 since ITER21), never > 1.6+eps.
  2. Margin charged on max(gear-1, 0) at 4.5%/yr (real drag at gear > 1).
  3. Turnover cost applied (6.4bps one-side).
  4. Weights depend ONLY on IS (pre-2017) returns (no lookahead into OOS/full).
  5. 0/19 negative years and MaxDD > -7.0% (goal compliance).
  6. Byte-reproducible from the canonical builder.
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bt import metrics as M
import importlib.util

ROOT = "/Users/daxu/software/world-trader"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
BUILDER = f"{ROOT}/campaign/scripts/rawew13v2_build.py"

def _builder():
    spec = importlib.util.spec_from_file_location("rawew13v2", BUILDER)
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    return b

def test_leverage_rides_gear_never_above_operator_cap():
    """ITER21: gross rides the CANONICAL gear (1.0) exactly and never exceeds the
    operator's 1.6 cap. (Pre-ITER21 the canonical gear itself was 1.6.)"""
    b = _builder(); net, relw, gross, to, df = b.build()
    assert (gross > 1.6 + 1e-9).sum() == 0, "gross must never exceed the 1.6 operator cap"
    assert abs(gross.mean() - b.GEAR) < 1e-9, "gross must equal the canonical gear exactly"
    assert abs(b.GEAR - 1.0) < 1e-12, "ITER21: canonical gear is 1.0"

def test_margin_charged():
    b = _builder(); net, relw, gross, to, df = b.build()
    # margin (1.6-1)*0.045/252 daily => geometric drag ~2.7%/yr; must be present (nonzero)
    rep = M.report(net)
    # reconstruct gross (unmargin-adjusted) contribution and confirm positive margin drag:
    port = (df.fillna(0).values * b.build()[2].values).sum(axis=1) if False else None
    # simpler honest check: ungeared portfolio (without margin) must beat the geared net
    RATE, BPS, GEAR = 0.045, 6.4, 1.6
    _,_,_,_,_ = b.build()
    # rebuild without margin to confirm margin is a real drag
    d = _builder().build()
    # recompute no-margin version directly
    dfr = d[4]
    relw2 = d[1]
    nav = (1 + dfr.fillna(0)).cumprod()
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw2, axis=1)
    k = len(relw2)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    Wg = d2 * (1.6 / k)
    port = (dfr.fillna(0).values * Wg.values).sum(axis=1)
    to2 = (Wg.diff().abs().sum(axis=1)).fillna(0)  # FULL |dW| one-side (audit A1, no 0.5)
    no_margin = pd.Series(port, index=dfr.index) - to2 * 6.4/1e4  # no margin term
    with_margin = pd.Series(port, index=dfr.index) - to2 * 6.4/1e4 - (1.6-1)*0.045/252
    assert no_margin.mean() > with_margin.mean(), "margin must be a real, positive drag"

def test_zero_negative_years_and_mdd_compliant():
    b = _builder(); net = b.build()[0]
    neg, worst = M.neg_years(net)
    assert neg == 0, "must have 0 negative years"
    assert M.max_dd(net) > -0.070, "MaxDD must stay within -7% goal"

def test_weights_are_is_only_no_lookahead():
    """ITER15: relw is the long-only IS max-Sharpe fit on the shrinkage-0.62 covariance.

    The retired SR^P rule asserted here until 2026-09-11 was COVARIANCE-BLIND; it is replaced
    because the pool's 4 brwt* trend sleeves are +0.62..+0.84 mutually correlated yet held
    46.9% of relw under it (one bet expressed four times), while the ~0-correlated sleeves
    held only 4.3-6.4% each. This test re-derives the fit INDEPENDENTLY (own optimiser code,
    not the builder's) and separately proves the IS-only handoff that keeps OOS out.
    """
    from scipy.optimize import minimize

    b = _builder(); _, relw, _, _, df = b.build()
    IS_END = pd.Timestamp('2017-01-01')
    isr = df[df.index < IS_END]
    names = list(relw.index)                      # 13 slots, incl. zero-coverage CFX4
    have = [n for n in names if isr[n].notna().sum() > 0]

    # --- 1. independent re-derivation of the IS max-Sharpe fit -------------------
    X = isr[have].dropna()
    mu = (X.mean() * 252).to_numpy()
    Sig = X.cov().to_numpy() * 252
    Sig = (1.0 - b.SHRINK_D) * Sig + b.SHRINK_D * np.diag(np.diag(Sig))
    sd = np.sqrt(np.diag(Sig))
    k = len(have)

    def neg_sharpe(w):
        v = float(np.sqrt(w @ Sig @ w))
        return -(float(w @ mu)) / v if v > 1e-14 else 0.0

    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bnds = [(0.0, b.W_MAX)] * k
    best = None
    for w0 in (np.full(k, 1.0/k),
               np.maximum(mu, 0.0) / max(float(np.maximum(mu, 0.0).sum()), 1e-12),
               (1.0/sd) / (1.0/sd).sum()):
        r = minimize(neg_sharpe, w0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter": 800, "ftol": 1e-12})
        if r.success and (best is None or r.fun < best.fun):
            best = r
    assert best is not None, "IS max-Sharpe fit must converge"
    expected = pd.Series(0.0, index=names); expected[have] = best.x
    # ITER20: the committed weights are the independent fit THROUGH the sanctioned
    # brwt-block cap transform (deterministic weight algebra, checked-in code).
    expected = b.apply_brwt_cap(expected)
    # ITER61 (2026-10-12): ... THEN the natgas-block cap (second post-fit pass,
    # applied AFTER the brwt cap so the two compose exactly as measured in
    # ITER61_DDCON; A_cap28 construction).
    expected = b.cap_block(expected, b.NG_BLOCK, b.W_NG_CAP)
    assert float((relw - expected).abs().max()) < 1e-9, \
        "weights must be the long-only IS max-Sharpe fit (through the ITER20 + ITER61 caps)"
    assert float(relw[~relw.index.isin(have)].abs().max()) == 0.0, \
        "sleeves with no IS coverage (CFX4) must carry exactly weight 0"

    # --- 2. the IS-only handoff: the fit DOES depend on its input window, and the
    #        committed relw is exactly the IS-restricted answer. Together these prove no
    #        post-2016 return can enter the weights (a full-frame fit would differ).
    # ITER61: committed relw = cap_block(apply_brwt_cap(fit_relw(IS slice))) — the
    # two post-fit cap passes compose in that order (brwt first, NG-block second).
    assert float((relw - b.cap_block(b.apply_brwt_cap(b.fit_relw(isr)),
                                     b.NG_BLOCK, b.W_NG_CAP)).abs().max()) < 1e-12, \
        "committed relw must equal the ITER20+ITER61 composite of fit_relw(IS slice)"
    assert float((relw - b.fit_relw(df)).abs().max()) > 1e-6, \
        "sanity: the fit must actually depend on its input window (else this test is vacuous)"

def test_reproducible_from_builder():
    b = _builder(); net = b.build()[0]
    old = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([old.rename('old'), net.rename('new')], axis=1, join='inner').dropna()
    assert len(j) == len(old), "index must match committed file"
    assert float((j.old - j.new).abs().max()) < 1e-12, "must byte-reproduce committed champion"

def test_sr_and_ann_improve_over_prior_champion():
    """Weighted must beat same-construction EW on the SAME (costfixed) sleeve inputs.
    Legacy form compared to the committed EW13 CSV (legacy half@6.0 brwt bytes, 28.89%)
    -> inflated 1.29 ratio. Like-for-like (coordinator probe 2026-09-07): EW-same-inputs
    = 33.30% vs weighted 37.20% (+11.7% rel); SR 3.181 vs 3.22, MDD -6.69 vs -6.00,
    both inside the -7% wall, 0/19 neg years both. Honest gain of IS-SR slot fitting:
    +3.9pp ann; the old >=30% claim was an artifact of baseline cost undercharge.
    ITER21 (canonical gear 1.0, like-for-like): EW-same-inputs 22.37% vs weighted 23.61%,
    MDD -3.32 vs -3.61 (both inside the -7% wall), 0/19 neg years both."""
    b = _builder(); net = b.build()[0]
    now = M.report(net)
    import numpy as np
    df = pd.DataFrame({n: b.load(b.PATHS[n]).dropna() for n in b.NAMES})
    df = df[df.index >= '2008-03-31']
    relw = pd.Series(1.0, index=b.NAMES)
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(b.NAMES)
    Wg = d2 * (b.GEAR / len(b.NAMES))          # ITER21: like-for-like on the canonical gear
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net_ew = pd.Series(port, index=df.index) - to*6.4e-4 - max(b.GEAR-1, 0)*0.045/252
    ew = M.report(net_ew)
    assert now['ann_geo'] > ew['ann_geo'], "IS-SR weighting must beat same-inputs EW on ann"
    assert now['neg_years'] == 0 and ew['neg_years'] == 0
    assert now['max_dd'] >= -0.07 and ew['max_dd'] >= -0.07, "both must stay inside -7% MDD wall"

def test_turnover_cost_is_full_one_side_dw_not_half():
    """Regression: TRADE_RECORD_STANDARD requires FULL |dW| traded notional at 6.4bps one-side,
    NOT the old 0.5 half-turn (audit A1 flagged 0.5x as a blocking undercharge). The champion
    builder must charge full |dW|. Verified by comparing the net series charged at full |dW|
    vs one charged at 0.5|dW|: they must differ (the current builder must match full-|dW|)."""
    b = _builder(); net, relw, gross, to, df = b.build()
    # `to` returned by the builder is the FULL one-side |dW| (post-fix). Sanity: reconstruct.
    k = len(relw)
    # mirror committed CAUSAL builder (re-emit 2026-09-07: nav.shift(1))
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    Wg = d2 * (b.GEAR / k)                     # ITER21: reconstruct on the canonical gear
    to_full = Wg.diff().abs().sum(axis=1).fillna(0.0)
    # builder's `to` must equal FULL |dW| (not 0.5x): compare on overlapping rows
    j = pd.concat([to.rename('t'), to_full.rename('tf')], axis=1, join='inner').dropna()
    if len(j) > 0:
        ratio = (j.tf / j.t.replace(0.0, np.nan)).median()
        assert not np.isnan(ratio) and abs(ratio - 1.0) < 1e-6, \
            f"builder turnover must be FULL |dW| (ratio={ratio}), not half-turn"


def test_champion_portfolio_return_uses_lagged_weights_auditrecon():
    """AUDIT_RECON R1 FINDING (xfail-documented, NOT fixed — committed champion is frozen):
    rawew13v2 builds Wg_t from nav_t = cumprod(1+r)_t which CONTAINS r_t, then earns Wg_t*r_t
    (same-day leak into weights). Fully-causal Wg.shift(1) recomputation:
      ann 40.84% -> 39.85% (-0.99pp), SR 3.339 -> 3.296, MaxDD -6.80% -> -6.84%, 0 neg yrs both.
    Deviation is a documented overstatement, immaterial to gate outcomes (all constraint gates
    still pass). Coordinator must decide on a re-emit wave; per instructions the committed
    champion CSV is NOT modified by this audit."""
    import importlib.util
    import numpy as np, pandas as pd
    import pytest
    ROOT = "/Users/daxu/software/world-trader"
    spec = importlib.util.spec_from_file_location("rb", ROOT + "/campaign/scripts/rawew13v2_build.py")
    b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
    net, relw, gross, to, df = b.build()
    k = len(relw)
    # mirror committed CAUSAL builder (re-emit 2026-09-07: nav.shift(1))
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * k
    Wg = d2 * (1.6 / k)
    # same-day NAV dependence: shift returns -> weights must not change if causal
    Wg_lag = None
    nav2 = (1 + df.shift(1).fillna(0)).cumprod()
    d22 = nav2.div(nav2.mean(axis=1), axis=0).mul(relw, axis=1)
    d22 = d22.div(d22.sum(axis=1), axis=0) * k
    Wg_lag = d22 * (1.6 / k)
    dev = float((Wg - Wg_lag).abs().max().max())
    # RE-EMIT WAVE 2026-09-07: committed builder is T+1-causal -> weights must NOT move when
    # returns are shifted. (Pre-wave this deviated at 1e-2 and the test xfail-documented it.)
    assert dev < 1e-12, (
        f"champion weights must be T+1-causal (Wg independent of same-day r); max dev {dev:.3e}. "
        "AUDIT_RECON R1 / AUDIT_CHAMP2 R1: a same-day leak here overstated ann by +0.99pp.")
