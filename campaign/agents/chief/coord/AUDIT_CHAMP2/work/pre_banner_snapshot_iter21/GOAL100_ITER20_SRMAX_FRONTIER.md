> **[ITER20 SUPERSEDE BANNER — 2026-09-18]** The champion of record is now the ITER20
> SR-max book: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv — ann 36.41% / SR 3.4551 /
> MDD -5.93% / 0 neg years / gross 1.6 exact (sha16 766fc0ce9926d793). Operator objective
> 2026-09-18: Sharpe-max subject to ann>=20% and gross<=1.6; the prior ann-max vintage
> (39.50 / 3.2176, ITER19) is archived byte-exact as archive_*_SUPERSEDED_by_ITER20_srmax.csv.
> Every earlier headline quoted in this document (39.50, 38.11, 37.49, 37.195, 40.84,
> 55.5, 62.4, ...) is SUPERSEDED history kept for provenance — it WAS current once, it is
> not current now.

# ITER20 — SR-MAX FRONTIER (2026-09-18, coordinator)

## Operator objective (2026-09-18, direct instruction)
"keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be
smaller than 20%." — i.e. the objective moved from the campaign's historical ann-max (subject to
gates) to **Sharpe-max subject to ann>=20% and gross<=1.6**. The champion of record is the
ANN-MAX point of its family; R8 memo #88 already documented that SR falls as weights concentrate
toward the ann-max fit. ITER20 quantifies the SR-max end of that frontier under full admissibility.

## Method (pre-committed before the reveal)
- Mechanics-exact replica of rawew13v2_build.build() with custom relw (anchor: reproduces the
  committed champion bytes at maxdev 9.996e-17 — verified first).
- Unified family: relw = fit_relw(IS, shrink) with shrink in {0.98, 0.85, 0.70}; brwt-block
  (brwt10/7/5) relw-share capped at cap in {0.45..0.25}, excess redistributed pro-rata on the
  committed non-block shares; optional within-block substitution s in {0, 0.25} of residual brwt
  weight into C5ngsum (s>=0.5 blows the MDD wall — C5ngsum over-concentration, see grid).
- Admissibility (all structural or IS-computable): per-sleeve weight <= W_MAX 2x equal;
  IS MDD >= -6%; 0 IS neg years; IS ann >= 20%; FS MDD >= -7% wall; gross exactly 1.6.
- Selection rule: argmax IS-SR over the pre-committed grid (same epistemic status as the
  champion's own shrink/P selections; no full-sample term enters the selection).

## Winner: shrink=0.70, cap=0.30, s=0  (emitted ITER20_SRMAX_c30_s70_{daily,weights}.csv)
| metric | champion 7559e82b | ITER20 SR-max | delta |
|---|---|---|---|
| SR (full) | 3.2176 | **3.4551** | +0.238 |
| ann (geo) | 39.4995% | 36.4150% | -3.08pp (floor 20% not binding) |
| MDD | -6.5232% | **-5.9284%** | +0.59pp better |
| worst year | +5.6250% (2013) | **+8.8898%** (2013) | better |
| neg years | 0/19 | 0/19 | = |
| IS SR / ann | 3.504 / 35.58% | 3.808 / 29.75% | +0.304 / -5.83pp |
| OOS SR / ann | 3.083 / 43.15% | 3.3754 / 42.76% | +0.292 / -0.39pp |
| gross | 1.6 exact, 0 over | 1.6 exact, 0 over | = |
| turnover | 4.766 bp/yr | 6.449 bp/yr | +1.68bp (charged in net) |
| Wmax | 2.0x cap ok | 1.98x | ok |
- Realized brwt-block gross share falls 76.1% -> ~57.6%; C5ng+C5ngsum rise to ~27.6%.
- Round-trip: emitted weights -> bytes maxdev 1.04e-16; fresh refit -> bytes 9.996e-17.

## Honest caveats
1. 5 OOS sub-windows dSR: +0.112 / +0.378 / -0.004 / -0.155 / +0.496 — 3 positive, 2 flat-to-
   slightly-negative (win4 is dSR-negative but dAnn +5.88pp). The gain is broad, not uniform;
   NOT the ITER15 "positive in all windows" gold standard.
2. The admissible plateau is flat: every admissible (shrink, cap<=0.30, s=0) point has FS SR
   3.42-3.47 and IS-SR 3.59-3.81 — the selection among neighbours is not doing real work, which
   is the robustness FEATURE of this adoption (no cherry-pick edge).
3. Free 12-dim mechanics-IS-SR argmax was tried and REJECTED: FS MDD -7.39% breaks the wall and
   OOS dAnn -12.7pp in 2018-20 (IS-overfit). Structured family only.
4. Inadmissible-but-tempting: (0.98, 0.25, 0) has FS SR 3.4654 with Wmax exactly 2.00 (admissible
   by the letter); (shrink, cap) pairs with s=0.25 reach FS SR ~3.50 but violate Wmax 2.6x.
   The winner was chosen by the pre-committed rule, not by FS SR rank.

## Adoption status
CANDIDATE ONLY — champion of record (GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv, sha
7559e82b022c6236, 39.4995% / 3.2176 / -6.5232%) is UNTOUCHED. Adoption swaps the objective from
ann-max to Sharpe-max per the operator's 2026-09-18 instruction and requires operator approval
(builder --emit is refused without --force by design).

## Repro
python3 with rawew13v2_build imported; construction = build() with relw from
fit_relw(isr, shrink_d=0.70) + brwt-block cap 0.30 + pro-rata redistribution (see
campaign/results/ITER20_SRMAX_c30_s70_weights.csv for the exact vector).
