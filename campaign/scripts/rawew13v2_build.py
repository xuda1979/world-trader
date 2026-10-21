#!/usr/bin/env python3
"""GOAL100 RAW-EW13v2 — canonical builder for the WEIGHTED 12-sleeve champion at the SR-max
canonical gear 1.0 (ITER21, 2026-09-18; ran at capital-real 1.6x through ITER20).

Improvement over the committed RAW-EW13@1.6x (28.89% ann / SR 3.88 / MDD -4.25%):
  Replace the naive 1/13 equal-weight slot allocation with IS-fitted relative weights.

  ITER15 (2026-09-11) — CORRELATION-AWARE WEIGHT FIT, supersedes the SR^P heuristic.
  History: weights were originally relw_i = max(IS_SR_i, 0)^P, P=0.55, chosen by a
  PRE-COMMITTED a-priori rule ("largest P maximizing IS annualized-return subject to
  (IS SR>=3.5) AND (IS MaxDD >= -6.0%) AND (IS 0 negative years)"). That rule is a function
  of each sleeve's OWN SR only and is BLIND to the covariance matrix -- a defect, because the
  pool's 4 brwt* trend sleeves are +0.62..+0.84 mutually correlated yet held 46.9% of relw
  (one bet expressed four times), while QAxasts/carryv2/diescrack/a6r7 are ~0-correlated to
  everything and held only 4.3-6.4% each. For a zero-correlation asset the max-Sharpe
  identity SR_new = sqrt(SR_p^2 + IR^2) says a positive-SR decorrelated sleeve must earn
  weight; the SR^P rule cannot express that.

  relw is now the LONG-ONLY MAX-SHARPE weight on the IS window's own mean/covariance, with
  the covariance shrunk SHRINK_D=0.62 toward its diagonal and each weight capped at W_MAX=2.0x
  the equal weight. Fitted ONLY on data < IS_END (same window as before). The hyper-parameter
  SHRINK_D was selected by the SAME pre-committed rule above, applied to the new family; the
  OOS reveal then confirmed it (IS ann 34.2753% vs 33.4836% under identical constraints;
  OOS SR 3.0916 vs 3.0617; FULL ann 38.11% / SR 3.2358 / MDD -6.56% / 0 neg yrs). A (SHRINK_D,
  NAV-drift-mixer) scan that NESTS the old construction picks the canonical NAV-drift mixer,
  so the construction is unchanged -- only the weights moved. See
  campaign/agents/chief/coord/ITER15_WEIGHTOPT/FINDINGS.md.

Construction (byte-reproducible):
  sleeve i net daily ret  ->  NAV  ->  NAV-drift weight (row-normalized) * relw_i /
  sum(w) -> gross exactly 1.6 daily. Costs: 6.4bps one-side turnover (FULL |dW| per
  TRADE_RECORD_STANDARD; audit A1 — no 0.5 half-turn undercharge), margin
  4.5%/yr on (1.6-1). Borrow is already inside the sleeve net files (per TRADE_RECORD_STANDARD).

  ITER20 (2026-09-18) — SHARPE-MAX CHAMPION OF RECORD. The operator objective moved to
  "Maximize Sharpe ratio" subject to ann>=20% and gross<=1.6 (direct instruction). On the
  pre-committed admissible family (IS max-Sharpe fit x shrink x brwt-block cap, CFX4 pinned 0,
  W_MAX 2x equal, IS MDD >= -6%, IS ann >= 20%, 0 IS neg years, FS MDD wall -7%) the IS-SR
  argmax is (shrink 0.70, cap 0.30, s=0): FULL SR 3.2176 -> 3.4551, ann 39.50% -> 36.42%
  (floor 20% not binding), MDD -6.52% -> -5.93%, worst year +5.63% -> +8.89%, 0 neg years,
  gross 1.6 exact / 0 days over, OOS dSR positive in all five 2017+ 2-yr bins
  (+0.29/+0.36/+0.23/+0.32/+0.42). The admissible plateau is flat (FS SR 3.42-3.47 across
  neighbours) -- no cherry-pick edge. The ann-max vintage (shrink 0.98, no cap; sha16
  7559e82b022c6236) is archived as archive_*_SUPERSEDED_by_ITER20_srmax.csv and remains
  byte-reproducible via build(shrink_d=0.98, brwt_cap=None). See
  campaign/GOAL100_ITER20_SRMAX_FRONTIER.md and campaign/GOAL100_ITER20_ADOPTION.md.

  ITER21 (2026-09-18) — THE GEAR DIMENSION. The operator objective is unchanged
  ("Maximize Sharpe ratio" s.t. ann>=20%, gross<=1.6), but ITER20 had pinned gross == 1.6
  as a family assumption while the operator's constraint is a CAP. The net series charges
  margin max(gear-1,0)*RATE/252 while turnover/borrow scale ~ gear, so net SR is EXACTLY
  flat on (0, 1.0] and STRICTLY DECREASING on [1, 1.6] -- a cost-structure identity, not
  an estimate (consistent with the #109 gear-1.705 result: SR FELL as gear rose). The SR
  argmax under the true constraint set is therefore the SAME weight vector at gear 1.0:
  ann 36.4150% -> 23.6054% (floor 20% kept), SR 3.455068 -> 3.751429 (+0.2964 -- THE
  objective), MDD -5.9284% -> -3.6130%, margin 2.70%/yr -> 0, turnover 6.45 -> 4.03 bp/yr,
  0 neg years, gross 1.0 exact / 0 days over, weights sha16 d2d11c92a98683df UNCHANGED.
  OOS dSR vs the gear-1.6 book, five 2017+ 2-yr bins: +0.362/+0.155/+0.411/+0.328/+0.274
  (5/5 positive -- analytic: removing a constant drag raises SR in every sub-window).
  Pre-committed BEFORE the reveal: campaign/agents/chief/coord/ITER21_SRMAX_EW_GEAR/
  FINDINGS_PRECOMMIT.md (2-point family: uniform EW vs the committed vector; g=1.05
  pre-selected; corrected to the plateau's argmax edge g=1.0 by the pre-committed
  objective -- disclosed in the adoption memo). The ITER20 vintage is archived byte-exact
  as archive_GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily_SUPERSEDED_by_ITER21_gear10.csv
  (sha16 766fc0ce9926d793) and stays reproducible via build(gear=1.6). See
  campaign/GOAL100_ITER21_ADOPTION.md.

Usage: python3 campaign/scripts/rawew13v2_build.py [--verify]
  (the canonical gear is now 1.0; pass --gear 1.6 to rebuild the archived pre-ITER21
   vintages byte-exactly)
"""
import sys; sys.path.insert(0, 'campaign')
import numpy as np, pandas as pd
from scipy.optimize import minimize
ROOT = "/Users/daxu/software/world-trader"

POOL = {
 # ITER19 (2026-09-13, operator-approved): brwt15 is PRUNED. It was the weakest and dominated
 # member of the brwt block -- IS SR 2.937 against siblings brwt5 2.978 / brwt10 3.614 /
 # brwt7 3.726, mutually +0.62..+0.84 correlated (one Brent-WTI mean-reversion bet expressed
 # four times) -- and it held 12.7% of the book. Its presence forced the rule's IS-MDD bound to
 # bite at shrink 0.62; without it the rule concentrates to 0.98 and the pool is 13 -> 12.
 # The gain is OOS-DRIVEN (OOS +1.44pp EXCEEDS the IS +1.16pp) and positive in all 5
 # sub-windows, with SR flat, MDD BETTER (-6.52% vs -6.56%) and turnover LOWER.
 # Archived pre-prune sleeve: campaign/agents/E1_20yspan/sleeves/E1_brwt_spread_rev15_2000.csv
 # brwt10/7/5: CAMP_COST R3 costfix re-emit (FULL|dW|@6.4bps). The legacy COORD/sleeves
 # bytes charge half@6.0 (undercharge ~150-190bps/yr on this flip-heavy family);
 # test_camp_cost_r2's gate enforces this swap fail-closed.
 "brwt10":"campaign/agents/chief/coord/CAMP_COST/sleeves/brwt10_2000__costfix.csv",
 "brwt7" :"campaign/agents/chief/coord/CAMP_COST/sleeves/brwt7__costfix.csv",
 "brwt5" :"campaign/agents/chief/coord/CAMP_COST/sleeves/brwt5__costfix.csv",
 "C5ng"  :"campaign/agents/E1_20yspan/sleeves/E1_C5ng_weekday_prem.csv",
 "C5ngsum":"campaign/agents/E1_20yspan/sleeves/E1_C5ng_summer_weekday.csv",
 "A5r2"  :"campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock__vt024.csv",
 "a6r7"  :"campaign/agents/E1_20yspan/sleeves/E1_a6r7_bond2y_trend_1990.csv",
 "QAxasts":"campaign/agents/E1_20yspan/sleeves/E1_QAxasts_tsmom189__vt015.csv",
 "carryv2":"campaign/agents/E1_20yspan/sleeves/E1_carryv2_GLD_2006.csv",
 "dualmom":"campaign/agents/A3_xs_quality/sleeves/QA_dualmom_band121.csv",
}
NEW = {
 "diescrack":"campaign/agents/loop_team/HUNT_BASIS2/sleeves/diescrack_L40Z20_net.csv",
 "CFX4"     :"campaign/agents/loop_team/HUNT_CARRYFX/sleeves/CFX4_DTF21_63_raw_daily.csv",
}
NAMES = list(POOL) + list(NEW)
PATHS = {**POOL, **NEW}

GEAR, RATE, BPS = 1.0, 0.045, 6.4
# ITER21 (2026-09-18): canonical GEAR moved 1.6 -> 1.0 under the unchanged operator
# objective (Sharpe-max s.t. ann>=20% and gross<=1.6). Margin is charged on
# max(gear-1, 0)*RATE while turnover/borrow scale ~ gear, so net SR is EXACTLY flat on
# (0, 1.0] and STRICTLY DECREASING on [1, 1.6]: the SR argmax under the cap is the lowest
# admissible gear, not the cap itself. Champion = the ITER20 weight vector (shrink 0.70 +
# brwt-cap 0.30, weights sha16 d2d11c92a98683df -- UNCHANGED) at gear 1.0:
# ann 23.6054% / SR 3.751429 / MDD -3.6130% / 0 neg yrs / gross 1.0 exact /
# sha16 8559fa55ee9a3417. The ITER20 vintage (same weights at gear 1.6, 36.4150% /
# 3.455068 / -5.9284%, sha16 766fc0ce9926d793) is archived byte-exact as
# archive_*_SUPERSEDED_by_ITER21_gear10.csv and stays reproducible via build(gear=1.6).
# See campaign/GOAL100_ITER21_ADOPTION.md and
# campaign/agents/chief/coord/ITER21_SRMAX_EW_GEAR/ (pre-commit + driver + gear curve).
IS_END = pd.Timestamp('2017-01-01')
P = 0.55          # legacy SR^P exponent — retained for provenance/tests; NOT used for the fit
SHRINK_D = 0.70   # ITER20 (2026-09-18): the OPERATOR OBJECTIVE moved from ann-max to
                  # Sharpe-max subject to ann>=20% and gross<=1.6 ("keep improving. the
                  # leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be
                  # smaller than 20%."). IS-SR argmax over the pre-committed (shrink, brwt-cap)
                  # grid selects (0.70, cap 0.30). Was 0.98 under the ann-max objective
                  # (ITER19 re-selection after the brwt15 prune; was 0.62 on the 13-sleeve
                  # pool). That ann-max vintage is archived byte-exact:
                  # archive_*_SUPERSEDED_by_ITER20_srmax.csv (daily sha16 7559e82b022c6236,
                  # weights be2265ff026dafb3) and stays reproducible via
                  # build(shrink_d=0.98, brwt_cap=None, gear=1.6) -- gear=1.6 because the
                  # canonical GEAR moved to 1.0 in ITER21.
W_BRWT_CAP = 0.30 # ITER20: brwt-block (brwt10/7/5) relw-share cap; the excess is
                  # redistributed pro-rata on the committed non-block shares. The fit's raw
                  # block share is 0.4605, so the cap binds. Within-block substitution into
                  # C5ngsum (s>=0.25) reaches FS SR ~3.50 but violates W_MAX (2.6x) and is
                  # NOT part of the champion family.
W_MAX = 2.0       # ITER15: per-sleeve cap, in units of the equal weight
NG_BLOCK = ("C5ng", "C5ngsum")
# ITER61 (2026-10-12) SEALED VINTAGE basis (pre-registered: ITER61_DDCON charter §3,
# coord/ITER61_DDCON/work/driver_iter61.py). The champion of record is built on the
# PRE-09-28-refresh C5ngsum vintage: commit 17e5be62 (2026-09-28) appended 19 rows
# (2026-08-25..09-21, DHHNGSP refresh, byte-identical history maxdev 0.0) which are NOT
# in the champion. Evaluation window pinned to the staged-vintage last row 2026-08-28.
# Without these pins build() would follow the working-tree sleeves (4821 rows) and
# diverge from the committed champion on the 2026-08-26..28 tail (maxdev 1.5e-3).
VINTAGE_END = pd.Timestamp("2026-08-28")
C5NGSUM_TRUNC = pd.Timestamp("2026-08-24")
W_NG_CAP = 0.28   # ITER61 (2026-10-12): natgas-block (C5ng + C5ngsum) relw-share cap,
                  # applied as a SECOND post-fit cap pass after apply_brwt_cap (same
                  # mechanism family: proportional down-scale of the block, pro-rata
                  # redistribution on the rest; cap_block in
                  # coord/ITER61_DDCON/work/driver_iter61.py). The fit's raw NG share
                  # is 0.32857, so the cap binds through the window. Pays -0.036 SR
                  # / -0.06pp ann for +0.43pp shallower MDD (-3.7339% -> -3.3048%),
                  # 28d-faster recovery, turnover down (4.33 -> 4.19 bp/yr). Adopted
                  # as champion of record 2026-10-12 (ITER61_DDCON; 8/8 pre-registered
                  # gates + B1-B5 battery; all evidence in the coord dir). The prior
                  # champion (sha16 cfa9ec4d38158691 / weights a384d6b92e258fd5) is
                  # archived as archive_*_SUPERSEDED_by_ITER61_DDCON.* and stays
                  # reproducible via build(ng_cap=None).

def load(p):
    df = pd.read_csv(f"{ROOT}/{p}", index_col=0); df.index = pd.to_datetime(df.index)
    c = "ret" if "ret" in df.columns else df.columns[0]
    return df[c].astype(float)

def is_sr(r):
    r = r.dropna()
    if len(r) < 200 or r.std(ddof=1) <= 1e-12:
        return 0.0
    return float(r.mean()/r.std(ddof=1)*np.sqrt(252))


def fit_relw(isr, shrink_d=SHRINK_D):
    """ITER15-annealed correlation-aware IS weight fit. Deterministic; IS window only.

    Long-only max-Sharpe over the sleeves that have IS coverage, on the IS mean/covariance
    annualised by 252, with the covariance shrunk `shrink_d` toward its diagonal and weights
    capped at W_MAX x equal weight. Sleeves without IS coverage (CFX4) get weight 0, exactly
    as the retired SR^P rule gave them (is_sr -> 0). Returns SHARES summing to 1; absolute
    scale is irrelevant because build() row-normalises d2 before applying GEAR.
    """
    have = [n for n in NAMES if isr[n].notna().sum() > 0]
    X = isr[have].dropna()
    mu = (X.mean() * 252).values
    Sig = X.cov().values * 252
    Sig = (1.0 - shrink_d) * Sig + shrink_d * np.diag(np.diag(Sig))
    k, sd = len(have), np.sqrt(np.diag(Sig))

    def neg_sharpe(w):
        v = float(np.sqrt(w @ Sig @ w))
        return -(float(w @ mu)) / v if v > 1e-14 else 0.0

    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1.0}]
    # The documented rule is w_i <= W_MAX x the EQUAL weight. These shares sum to 1, so the
    # equal weight is 1/k and the cap must be expressed in the same units: W_MAX/k. The former
    # `[(0.0, W_MAX)]` was INERT (W_MAX=2.0 > 1.0 can never bind against sum(w)=1), so a fit
    # could concentrate 100% of the book in one sleeve while every doc advertised a 2x cap.
    # Cleared 2026-09-13 (test_iter17_wmax_cap); champion-neutral, the committed fit's largest
    # weight is 0.1457 < 2/13, so --verify stays IDENTICAL.
    cap = W_MAX / k

    def solve(bounds):
        best = None
        for w0 in (np.full(k, 1.0/k),
                   np.maximum(mu, 0.0) / max(float(np.maximum(mu, 0.0).sum()), 1e-12),
                   (1.0/sd) / (1.0/sd).sum()):
            r = minimize(neg_sharpe, w0, method="SLSQP", bounds=bounds, constraints=cons,
                         options={"maxiter": 800, "ftol": 1e-12})
            if r.success and (best is None or r.fun < best.fun):
                best = r
        return best

    # Solve WITHOUT the cap first, then enforce it only if the documented rule is violated.
    # The two-stage form is deliberate: adding the cap bound changes SLSQP's convergence path
    # by ~2e-8 even when the optimum is interior to it, which would break the byte-reproducibility
    # of the champion of record (--verify < 1e-12). The committed fit's largest weight is
    # 0.1457 < 2/13 = 0.1538, so it takes the first branch and its bytes are untouched.
    best = solve([(0.0, W_MAX)] * k)
    if best is not None and float(best.x.max()) > cap + 1e-9:
        best = solve([(0.0, cap)] * k)
    if best is None:
        raise RuntimeError("ITER15 IS max-Sharpe fit failed to converge — fail closed")
    relw = pd.Series(0.0, index=NAMES)
    relw[have] = best.x
    return relw

BRWT_BLOCK = ("brwt10", "brwt7", "brwt5")


def apply_brwt_cap(relw, cap=W_BRWT_CAP):
    """ITER20 (2026-09-18): cap the brwt block's relw share at `cap` and redistribute the
    excess pro-rata on the non-block shares. Deterministic, weight-space only -- the NAV-drift
    mechanics in build() are untouched (verified: emitted weights round-trip the champion
    bytes at 1.04e-16; the transform reproduces the committed weight vector at 8.3e-17).
    CFX4 is re-pinned to 0: the discredited twelvedata vendor feed is a champion invariant
    (ITER14/ITER17 findings). Pass cap=None to disable (the pre-ITER20 construction)."""
    share = relw / relw.sum()
    if cap is None:
        return share
    blk = [n for n in BRWT_BLOCK if n in share.index]
    bs = float(share[blk].sum())
    out = share.copy()
    if bs > cap:
        excess = bs - cap
        out[blk] = share[blk] * (cap / bs)
        nonblk = [n for n in share.index if n not in blk]
        nb = float(share[nonblk].sum())
        out[nonblk] = share[nonblk] + excess * share[nonblk] / nb
    if "CFX4" in out.index:
        out["CFX4"] = 0.0
    return out


def cap_block(relw, block, cap):
    """ITER61 (2026-10-12): generalized block cap — proportional down-scale of
    `block`'s relw share to `cap`, pro-rata redistribution on the rest.
    Same mechanism family as apply_brwt_cap (weight-space only, deterministic;
    NAV-drift mechanics untouched). cap_block(share, NG_BLOCK, 0.28) is the
    second cap pass of the ITER61 champion construction. No-op when the block
    share is already <= cap. Mirrors driver_iter61.cap_block exactly (byte-equal
    inputs -> byte-equal outputs)."""
    relw = relw.copy()
    blk = [n for n in block if n in relw.index]
    s = float(relw[blk].sum())
    if s <= cap or s <= 0:
        return relw
    other = [n for n in relw.index if n not in blk and relw[n] > 0]
    excess = s - cap
    k = excess / s
    relw[blk] = relw[blk] * (1 - k)
    oo = float(relw[other].sum())
    if oo > 0:
        relw[other] = relw[other] * (1 + excess / oo)
    return relw


WF_MIN_ROWS = 500  # a refit needs at least this many past rows to be well-posed
WF_FIRST = "2011-01-03"
# ITER17 (2026-09-13): walk-forward refits are OPT-IN and NOT part of the champion.
# They were built, measured (+0.389pp ann on the full window) and REJECTED: the whole gain
# is CFX4 -- the sleeve whose twelvedata FX feed was discredited as a vendor artifact and
# which the champion deliberately holds at zero. Once 2019+ enters the expanding window the
# refit loads CFX4 at ~15%; drop CFX4 from the pool and the refit's edge is -0.016pp.
# See campaign/agents/chief/coord/ITER17_WALKFORWARD/FINDINGS.md and the pinning test
# test_iter17_walkforward::test_walkforward_edge_is_attributed_to_cfx4_and_rejected.
WF_STEP_TRIED = "YS"


def wf_relw_frame(df, shrink_d=SHRINK_D, step="YS", first=WF_FIRST):
    """ITER17: CAUSAL walk-forward refits of the slot weights (expanding window).

    The champion fits its weights ONCE on `< IS_END` and holds them for 19 years. Here the
    SAME fit_relw() is re-run at every refit date t in `pd.date_range(first, df.index[-1],
    freq=step)` on `df[df.index < t]` -- strictly past data -- and the resulting weights
    apply from t until the next refit date. No lookahead: proved by
    test_iter17_walkforward::test_walk_forward_weights_are_causal (perturbing future
    returns leaves past weights bit-identical). Refits with < WF_MIN_ROWS of history are
    skipped. The cadence default is the one IS-only selection picked (annual); see
    campaign/agents/chief/coord/ITER17_WALKFORWARD/FINDINGS.md.

    Returns a DataFrame (dates x NAMES); sleeves with no history are 0 (coverage rule).
    """
    start = fit_relw(df[df.index < IS_END], shrink_d=shrink_d)
    frame = pd.DataFrame(np.tile(start.values, (len(df), 1)), index=df.index, columns=NAMES)
    for t in pd.date_range(first, df.index[-1], freq=step):
        hist = df[df.index < t]
        if len(hist) < WF_MIN_ROWS:
            continue
        frame.loc[frame.index >= t] = fit_relw(hist, shrink_d=shrink_d).values
    return frame


def build(shrink_d=SHRINK_D, gear=GEAR, wf_step=None, wf_first=WF_FIRST,
          brwt_cap=W_BRWT_CAP, ng_cap=W_NG_CAP):
    parts = {}
    for n in NAMES:
        s = load(PATHS[n])
        if n == "C5ngsum":
            s = s[s.index <= C5NGSUM_TRUNC]  # ITER61 sealed vintage (see constants)
        parts[n] = s.dropna()
    df = pd.DataFrame(parts)
    df = df[df.index >= '2008-03-31']
    df = df[df.index <= VINTAGE_END]  # ITER61 sealed vintage: pin to staged-vintage last row
    # ITER15-annealed: correlation-aware IS weight fit (deterministic, IS-only). Replaces the
    # retired SR^P heuristic, which ignored the covariance matrix. See fit_relw() and docstring.
    isr = df[df.index < IS_END]
    if wf_step is None:
        relw = apply_brwt_cap(fit_relw(isr, shrink_d=shrink_d), cap=brwt_cap)
        if ng_cap is not None:
            # ITER61: second post-fit cap pass (NG block). Applied AFTER the brwt
            # cap so the two passes compose exactly as measured in ITER61_DDCON
            # (D1 relw -> cap_block NG_BLOCK 0.28; deterministic, weight-space only).
            relw = cap_block(relw, NG_BLOCK, ng_cap)
        relw_ts = relw
    else:
        # ITER17: expanding-window refits. relw (returned) is the CURRENT live weights = the
        # last refit's fit; relw_ts drives the NAV-drift weighting below.
        relw_ts = wf_relw_frame(df, shrink_d=shrink_d, step=wf_step, first=wf_first)
        relw = relw_ts.iloc[-1]
    # NAV-drift weights * relw, row-normalized to sum K, scaled to gross.
    # T+1 CAUSAL (AUDIT_CHAMP2 R1 re-emit wave, coordinator-approved): weights at day t are
    # formed from NAV through day t-1 ONLY (nav.shift(1)). The prior construction used
    # nav_t = cumprod(1+r)_t which contains r_t, letting day-t weights earn on day-t returns
    # (same-day leak, corr(dW_t,r_t)=0.78; honest ann 39.85% vs leaked 40.84%).
    nav = (1 + df.fillna(0)).cumprod().shift(1).fillna(1.0)
    d2 = nav.div(nav.mean(axis=1), axis=0).mul(relw_ts, axis=1)
    d2 = d2.div(d2.sum(axis=1), axis=0) * len(NAMES)
    Wg = d2 * (gear / len(NAMES))
    port = (df.fillna(0).values * Wg.values).sum(axis=1)
    # One-side turnover = FULL |dW| (TRADE_RECORD_STANDARD: qty_notional=|position change|).
    # No 0.5 half-turn factor (audit A1: 0.5x was a BLOCKING undercharge 41.7% of champion cost
    # rate). Charged at full BPS=6.4 one-side on all turnover.
    to = (Wg.diff().abs().sum(axis=1)).fillna(0.0)
    net = (pd.Series(port, index=df.index)
           - to * BPS/1e4
           - np.maximum(gear-1, 0)*RATE/252)
    gross = Wg.abs().sum(axis=1)
    return net, relw, gross, to, df

def parse_mode(args):
    """Resolve the CLI mode explicitly.

    The previous inline form -- `args[0] if args and not args[0].startswith('--') else
    '--verify'` -- sent EVERY long flag to '--verify', so `--emit` was unreachable and a
    documented re-emit silently no-op'd while printing a verify table that looks like
    success. Cleared 2026-09-13 (test_iter17_cli_modes)."""
    if '--emit-candidate' in args:
        return '--emit-candidate'
    if '--emit' in args:
        return '--emit'
    return '--verify'


def check_emit_safe(shrink_d, gear, wf_step, force, brwt_cap=W_BRWT_CAP,
                    ng_cap=W_NG_CAP):
    """--emit writes the CHAMPION OF RECORD paths unconditionally. Once --emit is actually
    reachable, `--emit --gear 1.75` (the RAWEW17 stray) or `--emit --shrink-d 0.8` would
    silently replace the champion with a book nobody vetted. Refuse unless --force says so;
    --emit-candidate NAME is the safe path for anything else."""
    dev = []
    if abs(float(shrink_d) - SHRINK_D) > 1e-12:
        dev.append(f"shrink_d={shrink_d} (canonical {SHRINK_D})")
    canon_cap = W_BRWT_CAP
    if (brwt_cap is None) != (canon_cap is None) or (
            brwt_cap is not None and abs(float(brwt_cap) - canon_cap) > 1e-12):
        dev.append(f"brwt_cap={brwt_cap} (canonical {canon_cap})")
    canon_ng = W_NG_CAP
    if (ng_cap is None) != (canon_ng is None) or (
            ng_cap is not None and abs(float(ng_cap) - canon_ng) > 1e-12):
        dev.append(f"ng_cap={ng_cap} (canonical {canon_ng})")
    if abs(float(gear) - GEAR) > 1e-12:
        dev.append(f"gear={gear} (canonical {GEAR})")
    if wf_step is not None:
        dev.append(f"wf_step={wf_step} (canonical: static fit; use --emit-candidate)")
    if dev and not force:
        return False, ("--emit would overwrite the champion of record with a DIFFERENT book: "
                       + ", ".join(dev) + ". Use --emit-candidate NAME, or --force to override")
    return True, ""


def main():
    args = [a for a in sys.argv[1:]]
    mode = parse_mode(args)
    # optional --shrink-d / --gear / --wf-step overrides (ITER17 d/grid + walk-forward)
    shrink_d = SHRINK_D; gear = GEAR; wf_step = None; wf_first = WF_FIRST
    if '--shrink-d' in args:
        shrink_d = float(args[args.index('--shrink-d') + 1])
    if '--gear' in args:
        gear = float(args[args.index('--gear') + 1])
    brwt_cap = W_BRWT_CAP
    if '--brwt-cap' in args:
        v = args[args.index('--brwt-cap') + 1]
        brwt_cap = None if v in ('none', 'None') else float(v)
    ng_cap = W_NG_CAP
    if '--ng-cap' in args:
        v = args[args.index('--ng-cap') + 1]
        ng_cap = None if v in ('none', 'None') else float(v)
    if '--wf-step' in args:
        v = args[args.index('--wf-step') + 1]
        wf_step = None if v in ('static', 'none') else v  # superseded static-fit lineage
    if '--wf-first' in args:
        wf_first = args[args.index('--wf-first') + 1]
    net, relw, gross, to, _ = build(shrink_d=shrink_d, gear=gear,
                                    wf_step=wf_step, wf_first=wf_first,
                                    brwt_cap=brwt_cap, ng_cap=ng_cap)
    if mode == '--emit':
        ok, why = check_emit_safe(shrink_d, gear, wf_step, force='--force' in args,
                                  brwt_cap=brwt_cap)
        if not ok:
            print(f"REFUSED --emit: {why}")
            raise SystemExit(2)
        net.to_frame('ret').to_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv")
        relw.to_frame('relw').to_csv(f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv")
        print(f"emitted champion + weights (shrink_d={shrink_d}, gear={gear}, wf_step={wf_step})")
        return
    if mode == '--emit-candidate':
        name = args[args.index('--emit-candidate') + 1]
        net.to_frame('ret').to_csv(f"{ROOT}/campaign/results/{name}_daily.csv")
        relw.to_frame('relw').to_csv(f"{ROOT}/campaign/results/{name}_weights.csv")
        print(f"emitted CANDIDATE {name} (shrink_d={shrink_d}, gear={gear}, "
              f"wf_step={wf_step}, wf_first={wf_first})")
        return
    # --verify: compare to committed files
    champ_path = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
    wgt_path = f"{ROOT}/campaign/results/RAWEW13v2_IS_SR_weights.csv"
    try:
        old = pd.read_csv(champ_path, index_col=0, parse_dates=True).iloc[:, 0]
        oldw = pd.read_csv(wgt_path, index_col=0).iloc[:, 0]
    except FileNotFoundError:
        print("NO COMMITTED FILES — run --emit first"); return
    j = pd.concat([old.rename('old'), net.rename('new')], axis=1, join='inner').dropna()
    md = float((j.old - j.new).abs().max())
    wr = (oldw - relw).abs().max()
    print(f"champion: n_committed={len(old)} n_built={len(net)} inner={len(j)} max|new-old|={md:.3e} "
          f"{'IDENTICAL' if md < 1e-12 else 'DIFF'}")
    print(f"weights:  max|committed-built|={wr:.3e} {'IDENTICAL' if wr < 1e-12 else 'DIFF'}")
    # gross / leverage audit
    print(f"gross mean {gross.mean():.6f} max {gross.max():.12f} days>1.6 {int((gross>1.6+1e-9).sum())}")
    # turnover in bp/yr: mean|dW|/day * 252 * 6.4bp (AUDIT_CHAMP2: prior print was
    # percent/yr mislabeled 'bps/yr' -- 0.0494 shown where true figure is 4.935bp/yr)
    print(f"turnover {to.mean()*252*BPS:.4f} bp/yr  margin {np.maximum(GEAR-1,0)*RATE*100:.2f}%/yr")

if __name__ == "__main__":
    main()
