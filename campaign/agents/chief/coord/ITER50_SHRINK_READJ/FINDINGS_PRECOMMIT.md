# ITER50 PRE-COMMIT (2026-09-20, session 30) - written BEFORE any candidate computation

## Operator objective (verbatim, unchanged)
> "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
> can't be smaller than 20%."

## Baseline verified BEFORE this seal (fresh, this session)
- Gauntlet ok true 7/7 (coord/verify_champion_r3_last_session30.json): weights_repro 7.633e-17 /
  byte_repro 1.041e-16 / half-turn rejected 1.644e-5 / gross exact n_over 0 / 0 neg yrs /
  MDD -3.7339 pct / SR 3.8203573009568794 / cagr 23.92147218901779.
- Champion triple re-hashed fresh: cfa9ec4d38158691 / a384d6b92e258fd5 / c40d008ddbf7c579
  (+ A5r2 vt024 7ec85336e7f7d00f). Coord quiet since the session-29 landing (23:55).

## The cell: book-solver (shrink_d, brwt_cap) RE-ADJUDICATION at the CURRENT champion (26th measured axis)
The solver grid was last adjudicated at the PRE-adoption champion:
- ITER22: 15-pt grid argmax (0.70, 0.30) - sleeves then pre-vt (A5r2 un-vted, QAxasts vt010).
- ITER23: 7 edge points - ALL Wmax-inadmissible THEN; incumbent = last admissible point.
- ITER29: estimator neighborhood - incumbent = covariance fixed point at the THEN covariance.
Since that adjudication, TWO ADMITTED NON-UNIFORM RESCALES moved the covariance the shrink acts on
(ITER47 A5r2 vt010 to vt024, fit share 3.78 to 2.41 pct; ITER49 QAxasts vt010 to vt015, fit share
7.9566 to 5.5133 pct - the two largest adopted champion moves on record). The #48 mechanism law
(ITER48) states diag shrinkage re-prices hedging under ANY non-uniform rescale ("there is NO
pure-scale axis at book level"). The ITER22/23/29 closures are therefore measured at a stale
covariance basis; at the CURRENT champion this family is UNMEASURED. No anti-dog-chase seal exists
on the book-solver family (the three LAST-seal proclamations cover the A5r2-VT, C5ng and tsmom
SLEEVE families only; the ITER22/23/29 solver closures carried no seal).

## Why this is not dog-chase (disclosed at seal)
Motivation = measured structural change (two admitted rescales), not a rising edge: no cell of this
family has ever been revealed against the CURRENT champion; every prior verdict was computed at the
old covariance. EV honestly LOW-TO-MODERATE: LOW per the three plateau confirmations (weights
ITER22, estimator ITER29 A2 fixed point, recipe ITER30); MODERATE because the two rescales moved
fit shares by 1.4-2.4 pp. SEAL SCOPE (binding): a SINGLE re-adjudication. If argmax is the anchor,
the solver family RE-CLOSES at the current champion and no further solver-grid measurement is
possible this generation. If an argmax is admitted and the reveal passes: standard battery +
adoption. If the reveal fails: family closed with the verdict recorded.

## Grid (ZERO free choice - verbatim reuse of sealed families)
- ITER22 15 pts: shrink_d 0.98/0.85/0.70 x brwt_cap 0.45/0.40/0.35/0.30/0.25.
- ITER23 7 edge pts: cap 0.29/0.28/0.27/0.26 at shrink 0.70; shrink 0.60/0.50/0.40 at cap 0.30.
- s in 0/0.25 DROPPED per ITER22's sealed disclosure (Wmax-violating by construction at ITER20;
  the invariant is scale-free).
- (0.70, 0.30) = the anchor = the incumbent itself (ineligible for admission by construction).

## Pipeline per cell (ITER22 builder-native convention; DISCLOSED deviation from the committed path)
fit_relw(IS frame, shrink=s) then apply_cap(cap=c) then build_book(gear 1.0). NO water-filling
projection: the frozen project_wmax hard-asserts block mass <= 0.30 (valid only at the incumbent
cap), and the projection is IDENTITY on the incumbent (projid 0.000e+00 on every ITER48/49 arm
including the anchor), so no-projection is EXACTLY the committed path at the anchor and the ITER22
filter convention elsewhere: any cell whose raw path breaches Wmax_sf <= 2.0x (k_covered) is
INADMISSIBLE-BY-FILTER (the ITER23 "last admissible point" reading), recorded, not rescued (NOT
the ITER26 water-filling repair class).

## IS filters + admission (ITER22 filter set + the sealed iter49 admission margin)
1. Wmax_sf = max(share) x k_covered <= 2.0 + 1e-9
2. IS MDD >= -6 pct
3. 0 IS neg years
4. IS-SR > BAR + 1e-4 (jitter-margin admission, disclosed STRICTER than raw >BAR; measured landing
   jitter 4.221e-09 weights / 2.064e-09 IS-SR - the margin is ~48x jitter)
BAR = 4.218504 = the committed book's IS-SR at the current sleeves (vt015 arm, ITER49 run-4 log;
A2 continuity asserted equal to bar on BOTH sides). The driver asserts the anchor-cell IS-SR within
5e-6 of BAR and uses the computed anchor value for the admission comparison.

## Reveal + stop rule (frozen)
Exactly ONE reveal: the global IS-argmax among admitted cells. 8 gates verbatim (G1 ann >= 20 pct,
G2 gross <= 1.6, G3 FS MDD >= -7 pct, G4 0 FS neg yrs, G5 CFX4 = 0, G6 Wmax_sf <= 2.0x, G7 OOS
police = at least 4/5 positive bins AND min dSR >= -0.10 AND FS SR > FS_BAR = 3.820357, G8
fit-window shrink <= 2 pct). Any gate failure means REJECT, no second reveal. D19 lesson applied:
the incumbent label is FORMATTED from the constant, never inherited.

## Anchors (fail-closed)
- A2: anchor-cell (0.70, 0.30) rebuild from live B.PATHS must reproduce the committed pair:
  weights maxdev < 1e-12 (expect ~7.6e-17), bytes maxdev < 1e-12 (expect ~1e-16), projid 0.0,
  fit rows 1809, k_covered 11, IS-SR = BAR within 5e-6.
- Champion sha16 pre equals post, asserted (cfa9ec4d38158691 / a384d6b92e258fd5).
- Frozen four-block (fit_relw / apply_cap / project_wmax / build_book) AST text-identity vs
  driver_iter41.py AND driver_iter36.py at run start (project_wmax defined-unused by design).

## Frontier consequence either way
Anchor argmax: 26 axes measured; the solver family joins the vt families as CURRENT-champion-closed;
operator levers unchanged (purchased data / rule change). Non-anchor admitted argmax + reveal PASS:
fourth-adoption candidate, battery then landing. Reveal FAIL: family closed, tenth police verdict.
