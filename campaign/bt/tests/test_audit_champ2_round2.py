"""AUDIT_CHAMP2 round 2 — pin the causal-vs-leak mechanism + TRUTH20Y provenance (charter d/c).

Charter (d), ORIGINAL 00:45 wave: champion (causal, ann 39.85%) vs archived leak (same-day,
ann 40.84%) differed by EXACTLY nav.shift(1) and nothing else.

SUPERSEDED 2026-09-07 07:2x (coordinator standup): CAMP_COST R2 fixed 4 sleeves from half-turn
to FULL |dW| @6.4bps (diescrack/dualmom/brwt15/QAxasts) and the coordinator re-emitted the
champion from the corrected sleeves (ann 39.69%). The lineage is now TWO sanctioned knobs,
pinned as an exact additive identity over prefix (pre-costfix, CAMP_COST/sleeves/*__prefix.csv)
and current (post-costfix) sleeve inputs:

    leaky(prefix sleeves)   == archived leak CSV      (byte <1e-12)   [measured 9.996e-17]
    causal(current sleeves) == committed champion CSV (byte <1e-12)
    shift delta   D2 = causal(prefix) - leaky(prefix)         (maxabs 3.962e-3, mechanism-only)
    costfix delta D1 = causal(current) - causal(prefix)      (maxabs 9.942e-4, sum -2.254e-2 <0)
    champion - archived == D1 + D2                           (|diff of diffs| < 1e-12,
                                                              measured 9.996e-17)

The identity is the pin: any THIRD knob sneaking into a future re-emit breaks it. relw is
IS-SR-fitted, so the costfix legitimately moved the weights file (sha256 8107aab3... ->
4e83acfb...); test_d_weights pins the new blob AND that it still equals an IS-only rebuild.

ITER43 (2026-09-19): champion of record -> the vt015 A5r2 input (sha16 e67446186e269b88,
weights bde8612d0b295068): PATHS["A5r2"] follows the builder; the leak-era VT=0.10 A5r2
bytes are pinned in PREFIX so the archived-leak arm is untouched.

ITER47 (2026-09-19): champion of record -> the vt024 A5r2 input (sha16 3c456aa53193eb89,
weights 8313bee1ad8a72fe); PATHS["A5r2"] below follows (vt024).

ITER49 (2026-09-19): champion of record -> the vt015 QAxasts input (sha16 cfa9ec4d38158691,
weights a384d6b92e258fd5); PATHS["QAxasts"] below follows (tsm-vt015); the leak-era VT=0.10
tsmom bytes stay pinned in PREFIX for the archived-leak arm.

Red-phase evidence (mutations of my own reconstruction, run before trusting the green):
    mutate shift->shift(2)   : causal-vs-committed maxdev 1.9e-3 (detected)
    mutate P 0.55->0.60      : diff-of-diffs ~1e-2        (detected)
    mutate BPS 6.4->5.0      : diff-of-diffs ~1.4e-4/2.4e-4 (detected)
"""
import os, sys
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

ROOT = "/Users/daxu/software/world-trader"
CHAMP = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
ARCH = f"{ROOT}/campaign/results/archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_SAMEDAYLEAK_ann40.84.csv"
WFILE = f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv"
PATHS = {
    "brwt15": "campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv",
    # R3 costfix era (coordinator swap 2026-09-07 ~11:1x): pool now consumes the
    # FULL|dW|@6.4 CAMP_COST emissions; legacy half@6.0 bytes live in __prefix.csv.
    "brwt10": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
    "brwt7": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
    "brwt5": "campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
    "C5ng": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
    "C5ngsum": "campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
    # ITER47 (2026-09-19): canonical A5r2 input -> the vt024 emission (upper-edge
    # extension argmax; the ITER43 vt015 vintage lives in coord/ITER43_A5R2_VT/).
    "A5r2": "campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock__vt024.csv",
    "a6r7": "campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
    # ITER49 (2026-09-19): canonical QAxasts input -> the tsm-vt015 emission (harness
    # vol-target argmax; the vt0.10 vintage lives in the committed 2006 file + PREFIX).
    "QAxasts": "campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv",
    "carryv2": "campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
    "dualmom": "campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
    "diescrack": "campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
    "CFX4": "campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
GEAR, RATE, BPS = 1.6, 0.045, 6.4  # the VINTAGE gear (everything archived pre-2026-09-18)
# ITER21 (2026-09-18): the champion of record moves to gear 1.0 (SAME weights; margin
# 4.5%/yr on (gear-1) makes net SR strictly decreasing above gear 1). GEAR becomes a
# FOURTH sanctioned knob: archived vintages rebuild at 1.6, the champion side at 1.0
# (passed explicitly to _rebuild -- this module stays an independent reconstruction).
IS_END = pd.Timestamp("2017-01-01")
P = 0.55

# Pre-costfix bytes of the 4 corrected sleeves (CAMP_COST R2, sha-verified == 00:45 git HEAD).
# Needed because the ARCHIVED leak CSV was built from THESE; rebuilding it from post-fix
# sleeves no longer byte-matches (that mismatch is what the old pin caught, correctly).
PREFIX = {
    "diescrack": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/diescrack__prefix.csv",
    "dualmom": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/dualmom__prefix.csv",
    "brwt15": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt15__prefix.csv",
    "QAxasts": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/QAxasts__prefix.csv",
    # R3 wave (coordinator 2026-09-07): pre-fix bytes of the brwt family. The archived
    # leak CSV was built from THESE half@6.0 files; note brwt10's stem is brwt10_2000.
    "brwt10": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__prefix.csv",
    "brwt7": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__prefix.csv",
    "brwt5": f"{ROOT}/campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__prefix.csv",
    # ITER43 (2026-09-19): the ARCHIVED leak (whole pre-ITER43 lineage) was built on the
    # VT=0.10 A5r2 emission; pin those leak-era bytes so the prefix arm survives the
    # PATHS swap above.
    "A5r2": f"{ROOT}/campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv",
}


def _load_any(p):
    df = pd.read_csv(p, index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def _load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0)
    df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)


def _pool(prefix=False):
    if prefix:
        # The ARCHIVED leak CSV predates ITER19 and was built from the full 13-sleeve pool.
        names = list(PATHS)
        df = pd.DataFrame({n: _load_any(PREFIX.get(n, f"{ROOT}/{PATHS[n]}")).dropna() for n in names})
    else:
        # ITER19 (2026-09-13): the champion prunes the dominated brwt15 -> 12 sleeves.
        names = [n for n in PATHS if n != "brwt15"]
        df = pd.DataFrame({n: _load(PATHS[n]).dropna() for n in names})
    return df[df.index >= "2008-03-31"]


def _relw(df, p=P):
    isr = df[df.index < IS_END]

    def is_sr(r):  # dropna BEFORE the guard: CFX4 starts 2019 -> 2286 all-NaN IS rows
        r = r.dropna()
        if len(r) < 200 or r.std(ddof=1) <= 1e-12:
            return 0.0
        return float(r.mean() / r.std(ddof=1) * np.sqrt(252))

    sr = pd.Series({n: is_sr(isr[n]) for n in df.columns})
    return np.maximum(sr, 0.0) ** p


def _relw_iter15(df, shrink_d=0.70, w_max=2.0):
    """ITER15 (2026-09-11) weight rule: long-only IS max-Sharpe on the covariance shrunk
    shrink_d toward its diagonal, each weight capped at w_max x equal weight.

    Replaces max(IS_SR,0)^P, which was a function of each sleeve's OWN SR only and therefore
    BLIND to the covariance matrix: the 4 brwt* trend sleeves are +0.62..+0.84 mutually
    correlated yet held 46.9% of relw under it. Own optimiser code here (not the builder's),
    so this file's rebuild stays an independent reconstruction.

    ITER20 (2026-09-18) re-anchor: the champion family adds the sanctioned brwt-block
    (brwt10/7/5) relw-share cap 0.30 with pro-rata redistribution of the excess (operator
    objective moved to Sharpe-max); the composite is applied below, still in own code.
    """
    from scipy.optimize import minimize
    names = list(df.columns)
    isr = df[df.index < IS_END]
    have = [n for n in names if isr[n].notna().sum() > 0]   # CFX4 has no IS coverage -> 0
    X = isr[have].dropna()
    mu = (X.mean() * 252).to_numpy()
    Sig = X.cov().to_numpy() * 252
    Sig = (1.0 - shrink_d) * Sig + shrink_d * np.diag(np.diag(Sig))
    sd = np.sqrt(np.diag(Sig))
    k = len(have)

    def neg_sharpe(w):
        v = float(np.sqrt(w @ Sig @ w))
        return -(float(w @ mu)) / v if v > 1e-14 else 0.0

    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    bnds = [(0.0, w_max)] * k
    best = None
    for w0 in (np.full(k, 1.0/k),
               np.maximum(mu, 0.0) / max(float(np.maximum(mu, 0.0).sum()), 1e-12),
               (1.0/sd) / (1.0/sd).sum()):
        r = minimize(neg_sharpe, w0, method="SLSQP", bounds=bnds, constraints=cons,
                     options={"maxiter": 800, "ftol": 1e-12})
        if r.success and (best is None or r.fun < best.fun):
            best = r
    assert best is not None, "ITER15 IS max-Sharpe fit must converge"
    out = pd.Series(0.0, index=names)
    out[have] = best.x
    # ITER20 composite: fitted shares THROUGH the brwt-block cap (own code, not builder's).
    share = out / out.sum()
    blk = [n for n in ("brwt10", "brwt7", "brwt5") if n in share.index]
    bs = float(share[blk].sum())
    cap = 0.30
    if bs > cap:
        excess = bs - cap
        share[blk] = share[blk] * (cap / bs)
        nonblk = [n for n in share.index if n not in blk]
        nb = float(share[nonblk].sum())
        share[nonblk] = share[nonblk] + excess * share[nonblk] / nb
    if "CFX4" in share.index:
        share["CFX4"] = 0.0
    return share


def _rebuild(df, relw, lag, bps=BPS, rate=RATE, gear=GEAR):
    nav = (1 + df.fillna(0)).cumprod()
    if lag:
        nav = nav.shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(df.columns)
    Wg = d2 * (gear / len(df.columns))
    port = pd.Series((df.fillna(0).values * Wg.values).sum(axis=1), index=df.index)
    to = Wg.diff().abs().sum(axis=1).fillna(0.0)
    return port - to * bps / 1e4 - max(gear - 1, 0) * rate / 252


def _maxdev(a, b):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1, join="inner").dropna()
    assert len(j) > 4000, f"inner join only {len(j)} rows — index mismatch"
    return float((j.a - j.b).abs().max())


def test_d_committed_is_exact_causal_rebuild():
    # ITER21: the champion of record is the SAME committed weights at gear 1.0.
    assert _maxdev(_rebuild(_pool(), _relw_iter15(_pool()), lag=True, gear=1.0),
                   pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0]) < 1e-12


def test_d_archived_is_exact_leaky_rebuild():
    """Corner 2: archived leak == SAME-DAY rebuild from PREFIX (pre-costfix) sleeves.
    (Rebuilding from current sleeves fails by ~1e-3 — the costfix moved the inputs,
    which is what the old version of this pin caught on 2026-09-07 07:1x.)

    RE-PINNED 2026-09-28 (E1/DHHNGSP refresh landing, commit 17e5be6): the archived
    leak file (frozen, ends 2026-08-27) now sees the E1_C5ng_summer_weekday sleeve's
    19 appended marks (2026-08-25..09-21) INSIDE its window — the first new mark
    (08-26) lands 2 days before ARCH's end. Attribution verified: pre-08-25 maxdev
    9.996e-17 (byte-repro of the archived leak through 08-24); ALL new drift is the
    appended-marks class, maxdev 1.322e-3 at 2026-08-26. Old pin: <1e-12 (held
    2026-09-07..2026-09-27)."""
    df_old = _pool(prefix=True)
    j = pd.concat([_rebuild(df_old, _relw(df_old), lag=False).rename("m"),
                   pd.read_csv(ARCH, index_col=0, parse_dates=True).iloc[:, 0].rename("a")],
                  axis=1, join="inner").dropna()
    pre = j[j.index < "2026-08-25"]
    assert float((pre.m - pre.a).abs().max()) < 1e-12, \
        "pre-refresh history drifted — NOT the appended-marks class; re-audit"
    assert float((j.m - j.a).abs().max()) < 2e-3, \
        "appended-marks drift grew beyond the pinned 1.322e-3 (cap 2e-3); re-attribute"


def test_d_mechanism_is_exactly_three_sanctioned_knobs():
    """THE pin: champion - archived == shift + costfix + weight-rule (additive identity).

    ITER15 (2026-09-11) added the THIRD sanctioned knob: relw moved from max(IS_SR,0)^P to
    the correlation-aware long-only IS max-Sharpe fit. The archived leak CSV and the
    pre-ITER15 champion remain exactly reproducible under the RETIRED rule, so the
    decomposition still telescopes exactly:
        c_prev - c_old  = costfix delta      (return-reducing, sum < 0)
        c_old  - l_old  = shift delta        (mechanism only)
        c_new  - c_prev = weight-rule delta  (return-ADDING, sum > 0)
    ITER21 (2026-09-18) added the FOURTH sanctioned knob: canonical gear 1.6 -> 1.0
    (SAME weights; the margin term max(gear-1,0)*RATE is strictly SR-negative above gear 1).
    The decomposition telescopes with the gear knob made explicit:
        c_prev  - c_old     = costfix delta      (return-reducing, sum < 0)
        c_old   - l_old     = shift delta        (mechanism only)
        c_prev10 - c_prev   = gear delta         (scale + margin-drag removal: vol down,
                                                   SR up; ITER21)
        c_new   - c_prev10  = weight-rule delta  (evaluated at the new gear)
    ITER43 (2026-09-19) added the FIFTH sanctioned knob: the canonical A5r2 sleeve input
    moved to the vt015 emission (old VT=0.10 bytes pinned in PREFIX for the archived arm);
    it is bundled in the c_prev - c_old input-refresh delta below.
    Any UNSANCTIONED knob beyond these four (BPS, margin RATE, pool membership, IS window,
    shift(2)) breaks the identity. Mutation evidence in the module docstring."""
    df_new, df_old = _pool(), _pool(prefix=True)
    relw_old = _relw(df_old)                 # retired SR^P, prefix sleeves
    relw_prev = _relw(df_new)                # retired SR^P, current sleeves
    relw_new = _relw_iter15(df_new)          # ITER15 correlation-aware fit

    c_new = _rebuild(df_new, relw_new, 1, gear=1.0)       # == committed champion (ITER21)
    c_prev10 = _rebuild(df_new, relw_prev, 1, gear=1.0)   # weightrule delta at the new gear
    c_prev = _rebuild(df_new, relw_prev, 1, gear=1.6)     # pre-ITER15 rule on the vt015 pool
    c_old = _rebuild(df_old, relw_old, 1, gear=1.6)
    l_old = _rebuild(df_old, relw_old, 0, gear=1.6)

    # every knob must be PRESENT (guard against a vacuous identity)
    assert _maxdev(c_old, l_old) > 1e-6, "shift knob vanished"
    d_cost, d_gear, d_wrule = c_prev - c_old, c_prev10 - c_prev, c_new - c_prev10
    assert float(d_cost.abs().max()) > 1e-6, "costfix knob vanished"
    assert float(d_cost.sum()) < 0           # costfix is return-reducing in aggregate
    assert float(d_gear.abs().max()) > 1e-6, "gear knob vanished"
    # The gear knob is SCALE + margin: absolute summed returns fall with the smaller book,
    # so its honest signatures are the vol drop and the SR gain (margin-drag removal).
    _s16, _s10 = float(c_prev.std(ddof=1)), float(c_prev10.std(ddof=1))
    assert _s10 < _s16, "gear knob must shrink book volatility"
    assert float(c_prev10.mean() / _s10 * np.sqrt(252)) > float(c_prev.mean() / _s16 * np.sqrt(252)), \
        "gear 1.6 -> 1.0 must RAISE SR (margin-drag removal -- the ITER21 lever)"
    assert float(d_wrule.abs().max()) > 1e-6, "weight-rule knob vanished"
    # Sign history: return-ADDING in aggregate under the ann-max objective (ITER15/19);
    # return-REDUCING under the ITER20 Sharpe-max objective BY DESIGN (de-concentration
    # trades raw return for SR 3.2176 -> 3.4551). Pinned as MATERIAL, two-sided.
    assert abs(float(d_wrule.sum())) > 0.02   # the weight-rule knob must stay material

    j_files = pd.concat([pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0].rename("a"),
                         pd.read_csv(ARCH, index_col=0, parse_dates=True).iloc[:, 0].rename("b")],
                        axis=1, join="inner").dropna()
    j_mid = pd.concat([c_new.rename("a"), l_old.rename("b")], axis=1, join="inner").dropna()
    ident = float(((j_files.a - j_files.b) - (j_mid.a - j_mid.b)).abs().max())
    assert ident < 1e-12, \
        f"champion-archived delta is not exactly shift+costfix+weightrule: residual {ident:.3e}"
    corr = float(j_files.a.corr(j_files.b))
    # ITER19 (2026-09-13): pruned pool moves the champion/archived-leak corr off 0.9938808973.
    # ITER20 (2026-09-18): de-concentration (brwt cap 0.30) moves it off 0.9901097119.
    # ITER43 (2026-09-19): the A5r2 -> vt015 input moves it off 0.9418451552.
    # ITER47 (2026-09-19): the A5r2 -> vt024 input moves it off 0.9385613294.
    # ITER49 (2026-09-19): the QAxasts -> tsm-vt015 input moves it off 0.9357692357.
    assert abs(corr - 0.9298157450) < 5e-6, f"champion/arch corr drifted: {corr!r}"


def test_d_weights_file_matches_post_costfix_is_fit():
    """relw is IS-fitted, so a legitimate rule/input change moves the weights blob. Pin the
    NEW blob hash AND that it equals an IS-only rebuild from current sleeves (drift would
    mean someone re-fit on OOS data, or silently changed SHRINK_D/W_MAX)."""
    import hashlib
    cur = hashlib.sha256(open(WFILE, "rb").read()).hexdigest()
    # ITER15 re-emit (2026-09-11): weight rule -> correlation-aware IS max-Sharpe fit.
    # ITER19 re-emit (2026-09-13): brwt15 pruned (13 -> 12 sleeves), shrink re-selected 0.62 -> 0.98.
    # ITER20 re-emit (2026-09-18): shrink 0.70 + brwt-block cap 0.30 (Sharpe-max objective).
    # ITER43 re-emit (2026-09-19): A5r2 -> vt015 sleeve, IS refit (sha16 bde8612d0b295068).
    # ITER47 re-emit (2026-09-19): A5r2 -> vt024 sleeve, IS refit (sha16 8313bee1ad8a72fe).
    # ITER49 re-emit (2026-09-19): QAxasts -> tsm-vt015 sleeve, IS refit (sha16 a384d6b92e258fd5).
    assert cur == "a384d6b92e258fd54dab448c93cd5f15bd3fa1cc79accdb5a3fa3ca01205ebe8"
    assert float((_relw_iter15(_pool()) - pd.read_csv(WFILE, index_col=0).iloc[:, 0]).abs().max()) < 1e-12


def test_d_committed_metrics_are_honest_current():
    """Pin the committed champion's honest metrics.

    Lineage of this pin: 39.687317% (R2-era) -> 37.195397% (R3 costfix re-emit 2026-09-07)
    -> 37.4923% (R8 RAWEW15 refresh) -> 38.114469% (ITER15 weight-rule re-emit 2026-09-11).
    """
    r = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    n = len(r)
    ann = (1 + r).prod() ** (252 / n) - 1
    sr = r.mean() / r.std(ddof=1) * np.sqrt(252)
    nav = (1 + r).cumprod()
    dd = float((nav / nav.cummax() - 1).min())  # ratio form (R2 bug: sub() is dollar-diff, -28 = -6.84% x nav)
    yby = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    # ITER15 re-emit (2026-09-11): correlation-aware IS max-Sharpe weights. Construction,
    # costs and gross are unchanged from the 37.4923% generation (see CHAMPION_CARD.md).
    # ITER19 re-emit (2026-09-13): brwt15 pruned, shrink 0.98. Was 38.114469% / SR 3.2358 / MDD -6.5620%.
    # ITER20 re-emit (2026-09-18): shrink 0.70 + brwt cap 0.30 (Sharpe-max objective).
    # Was 39.4995% / SR 3.2176 / MDD -6.5232% (archived byte-exact).
    # ITER21 re-emit (2026-09-18): SAME weights at canonical gear 1.0 (the gear lever --
    # margin 4.5%/yr on (gear-1) is strictly SR-negative above gear 1). Was
    # 36.4150% / SR 3.4551 / MDD -5.9284% (archived byte-exact, reproducible build(gear=1.6)).
    # ITER43 re-emit (2026-09-19): A5r2 -> vt015 sleeve. Was 23.6054% / SR 3.751429 /
    # MDD -3.6130% (prior_champion_backup, byte-exact).
    # ITER47 re-emit (2026-09-19): A5r2 -> vt024 sleeve. Was 23.6813% / SR 3.764764 /
    # MDD -3.6603% (coord/ITER47_A5R2_VTEXT/prior_champion_backup, byte-exact).
    # ITER49 re-emit (2026-09-19): QAxasts -> tsm-vt015 sleeve. Was 23.7668% / SR 3.784099 /
    # MDD -3.7012% (coord/ITER49_TSMOM_VT/prior_champion_backup, byte-exact).
    assert abs(ann - 0.2392147) < 5e-7, f"ann {ann:.6%} drifted from honest 23.9215%"
    assert 3.817 <= sr <= 3.823
    assert -0.0375 <= dd <= -0.0372
    assert int((yby < 0).sum()) == 0
    # and the leak must stay ABSENT: ann must NOT round-trip to the archived 40.84
    arch_ann = (1 + pd.read_csv(ARCH, index_col=0, parse_dates=True).iloc[:, 0].dropna()).prod() \
        ** (252 / 4805) - 1
    assert arch_ann > 0.4079  # archived leak is the 40.84 construction
    assert ann < arch_ann - 0.005  # honest number is >=0.5pp below the leak


def test_c_truth20y_json_bal_reconciles_with_its_csv():
    """TRUTH20Y is untracked with no builder in-tree (R2 provenance flag). Its JSON 'bal'
    block must at least reconcile with the CSV it ships next to, per ITS OWN conventions:
    ann/oos_ann arithmetic (mean*252), mdd geometric-nav. R2 measured: arith ann 53.0327%,
    oos arith 59.92%, geo MDD -7.88%, negy 1 (2006)."""
    r = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_TRUTH20Y_BALANCED_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0].dropna()
    import json
    bal = json.load(open(f"{ROOT}/campaign/results/GOAL100_TRUTH20Y.json"))["bal"]
    assert abs(r.mean() * 252 - bal["ann"] / 100) < 5e-4
    osm = r[r.index >= IS_END]
    assert abs(osm.mean() * 252 - bal["oos_ann"] / 100) < 5e-4
    nav = (1 + r).cumprod()
    assert abs(float((nav / nav.cummax() - 1).min()) * 100 - bal["mdd"]) < 0.05
    yby = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    assert int((yby < 0).sum()) == bal["negy"]


def test_c_truth20y_bal_is_not_a_constraint_passing_champion():
    """AUDIT_CHAMP2 R2 measured (work/r2_audit_fresh.py): TRUTH20Y BALANCED breaches TWO hard
    user walls — geometric MaxDD -7.88% (wall <= -7%) and 1 negative calendar year (2006) —
    so it must never be promoted to champion as-is. Also pins the CONVENTION gap: its JSON
    headline 'ann 53.0' is simple arithmetic (mean*252); compounded geo is 69.09%. If either
    fact drifts, this forces re-examination before anyone quotes TRUTH20Y as the champion."""
    r = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_TRUTH20Y_BALANCED_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0].dropna()
    nav = (1 + r).cumprod()
    mdd = float((nav / nav.cummax() - 1).min())
    assert mdd <= -0.07, f"TRUTH20Y BAL MDD {mdd:.2%} no longer breaches the -7% wall?"
    yby = r.groupby(r.index.year).apply(lambda x: (1 + x).prod() - 1)
    assert int((yby < 0).sum()) >= 1, "TRUTH20Y BAL neg year vanished — re-verify provenance flag"
    geo = (1 + r).prod() ** (252 / len(r)) - 1
    assert abs(geo - 0.6909) < 5e-4, f"TRUTH20Y BAL geo ann drifted: {geo:.4%}"
    assert abs(r.mean() * 252 - 0.5303) < 5e-4, "JSON 'ann 53.0' is simple-arith; keep conventions distinct"
    # and it is a DIFFERENT animal from the champion (pool corr 0.575 measured R2)
    c = pd.read_csv(CHAMP, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    j = pd.concat([r.rename("t"), c.rename("c")], axis=1, join="inner").dropna()
    assert abs(j.t.corr(j.c) - 0.575) < 0.02
