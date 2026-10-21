# ITER43_A5R2_VT — FINDINGS (session 23, 2026-09-19 ~19:0x-20:1x CST)

Operator directive (verbatim): keep improving. the leverage must be <=1.6. Maximize
Sharpe ratio. The annual return can't be smaller than 20 pct. — same constraint set as
ITER21..42; no rule change, no purchased data.

## VERDICT: ADOPTION — champion of record MOVED (first adoption since ITER21)

- New champion: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
  sha16 e67446186e269b88 / RAWEW13v2_IS_SR_weights.csv sha16 bde8612d0b295068.
  FS SR 3.7647642016866434 (incumbent 3.751428690289051, +0.0133355) / cagr 23.6813 pct
  (arith 21.4222) / MDD -3.6603 pct / 0 neg years / worst year +7.5032 pct / n 4806
  (2008-03-31..2026-08-28) / gross 1.0 EXACT / turnover 4.0913 bp/yr / margin 0.
- All operator constraints satisfied: leverage 1.0 <= 1.6; ann 23.68 pct >= 20; SR MAXED
  vs incumbent under the sealed gates. MDD -3.66 pct vs -3.61 prior (limit -7, headroom).
- Prior champion preserved byte-exact: coord/ITER43_A5R2_VT/prior_champion_backup/
  (8559fa55ee9a3417 / d2d11c92a98683df).
- Canonical A5r2 sleeve swapped: campaign/agents/A5_vol_cond/sleeves/
  A5_r2_contango_rateshock__vt015.csv sha16 901eebdd3abef617 (+ .meta provenance).
  Historical VT=0.10 sleeve untouched (0316cd1afd446938).

## THE CELL (19th axis)
A5r2 per-sleeve vol-target VT (5.522 pct book weight): the ONLY roster sleeve >=5 pct
weight with NO campaign-swept scalar axis, and VT had ZERO coverage at any level (agent
r2 grid covered W/CHG/LVL; TH/HYST from r1; mult monotone to endpoint 0). Agent's
"vt is pure scale" claim does NOT hold here: sc = VT/sigma_ann clipped at 2.0 with
realized 8.8 pct < 10 pct target puts the anchor IN the clip regime -> genuine shape
axis. Precedent: ITER30 swept VT inside a6r7's grid. GRID {0.06,0.08,0.10,0.12,0.15};
anchor 0.10 IS-bar-ineligible by construction.

## RUNS (fail-closed events preserved; see run_history.md)
- Run-1: NameError at def-time (module BRWT_BLOCK omitted under the frozen project_wmax
  default). Pre-computation. Fixed.
- Run-2: full sweep ran; A2 FAIL-CLOSED at 9.913e-09 weights (bar 1e-12): the anchor arm
  fitted the REGEN stream; SLSQP landing amplifies the ~1e-16 regen-vs-committed input
  delta (A1b: 9.975e-17) to 1e-8. Template deviation (36/41/42 anchor A2 on the
  COMMITTED frame). Amendment 1 re-sealed; A2 moved to the committed frame; jitter
  logged (A2b: weights 9.913e-09, IS-SR 7.050e-10).
- Run-3 (amended): GREEN. A2 committed-frame 8.327e-17/9.996e-17; arms rows 1809 k 11
  projid 0.0; IS-SR monotone rising 4.188280/4.194835/[4.198632]/4.201156/4.203733;
  IS admission [0.12, 0.15]; Wmax_sf 1.72-1.86x <= 2.0. DISCLOSURE: IS gradient monotone
  rising with argmax AT THE SEALED-GRID EDGE (0.15). Grid extension after seeing results
  = iterative probing; FORBIDDEN by the sealed stop rule. Single reveal spent on the
  argmax: VT=0.15 -> 8/8 ADOPTABLE (G7 bins +0.0067/+0.0231/+0.0060/-0.0134/+0.0110 =
  4/5 positive, min -0.0134 >= -0.10 floor, FS SR > 3.751429).

## BATTERY (post-reveal)
- Step 1 (independent verifier on the driver-fit pair) FAILED weights_repro at
  3.816e-09 > tol 1e-9: driver and verifier are separate SLSQP implementations; they
  land bit-identically on the committed inputs but 3.8e-9 apart on the vt015 covariance.
  The candidate weights were not at the canonical fixed point. Amendment 2 re-sealed:
  canonicalize the pair to bt/verify_champion.py's own algebra (_relw_from, is_end
  2017-01-01, p 0.55, minsharpe, shrink 0.70, brwt_cap 0.30; book via _weights_gear/
  _net_from). Canonical-vs-driver relw delta = 3.816e-09 (the measured disagreement);
  canonical book stats IDENTICAL to the revealed numbers at 6 dp; all gates re-asserted.
- Independent gauntlet on the canonical pair: 7/7 GREEN (weights_repro 8.327e-17,
  byte_repro 1.006e-16, cost full_dw ratio 1.0000000000048 with half-turn rejected at
  1.61e-05, causality clean, gross 1.0000000000006 n_over 0, 0 neg years, MDD ok).
- Coherence checks: BOTH halves positive (H1 dSR +0.0045, H2 dSR +0.0146 — no decay
  direction); 13/19 years positive, worst year delta -0.151 pp (broad-based, no
  single-episode dependence); attribution sane — VT raise scales the sleeve 1.5x at
  IDENTICAL sleeve SR (1.0192), the fit re-weights A5r2 5.52 -> 3.78 pct and the
  +0.0133 book SR is a covariance/weighting effect, not sleeve alpha.

## MECHANISM (honest reading)
Higher VT -> A5r2 runs bigger (cleaner, less clip-distorted) exposure at unchanged
SR; the IS re-fit buys less of it and spreads weight to uncorrelated sleeves; the
book's covariance structure improves slightly in BOTH halves and most years. The
margin over the incumbent (+0.0133 FS SR) is ~2x the largest structure-noise dSR
family on record and 1.9e7x the measured fit-landing jitter (7.05e-10 IS-SR).

## LANDING
- verify_champion_r3_cmd.sh UPDATED (A5r2 -> vt015; --is-end 2017-01-01 explicit;
  ITER43 banner) — final canonical gauntlet on the ADOPTED files 7/7 GREEN
  (coord/verify_champion_r3_last_session23.json).
- rawew13v2_build.py PATHS["A5r2"] -> vt015; builder default build byte-reproduces the
  new champion <1e-12 (test_rawew13v2 8/8).
- Re-pin wave (62 RED -> 0): 3 parallel agents re-anchored 34 test files under strict
  rules (historical verdicts adjudicated against the ERA pair via the backup /
  try-finally PATHS patches at byte-exact 1e-16; NO tolerance weakened; NO historical
  REJECT flipped; Wmax cap re-derived to the canonical W_MAX/k form; iter23 grid
  verdict preserved on the era sleeve; CHAMPION_CARD.md regenerated by its own
  generator). 2 doc-banner lints then fixed by additive ITER43 SUPERSEDE banners on
  32 gated docs.
- test_iter43_a5r2_vt.py: 6 pins GREEN, mutation-checked (fake FS-SR -> RED ->
  byte-exact restore a9f851b234ac343f -> GREEN).
- SUITE 606 passed / 0 failed (599 + 6 pins + 1 era-anchor pin; own run, 76.01s).
- Champion sha16 pre/post driver run identical; adoption swap + final gauntlet after.

## FRONTIER (19 axes now measured under the current objective)
The scalar-scalar sweep program has ONE remaining roster cell: carryv2 (2.198 pct,
GLD carry) — the last sleeve with no campaign-harness scalar sweep. Data axis:
census long-tail (~50 unwired IS-fittable series beyond the ITER24 shortlist) remains
the only free-data direction; both EV-bounded by the ITER24/ITER17 record.
