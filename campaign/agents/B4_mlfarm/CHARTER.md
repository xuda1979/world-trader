# B4_mlfarm — MISSION: New decorrelated high-SR ML L/S books (more true SR = more return at high SR)

## OVERRIDING GOAL
20y, SR>=2, ann>=50%, MaxDD<=8%, 6bps/side, free data, no leverage, OOS. The current
champion's highest-return engines are XGB L/S books (h21_f5: ann 29%, h21_br: ann 19%,
near-zero corr to everything). Your mission: build MORE of these — genuinely fresh ML L/S
books from NEW feature sets / horizons / universes that add DECORRELATED high-SR return.

## Existing ML infrastructure (read these first)
- tools/quant/bigmove/xgb_horizon_ddfilter.py — the causal 21d-horizon L/S engine (shift(1),
  6bps, walk-forward quarterly refit). This produced h21 books.
- tools/quant/bigmove/xgb_multi_horizon.py — multi-horizon (h1/h5/h21) walk-forward W/O
  label-overlap leak fix. CAREFUL: naive versions show fake SR 8+ (daily-spread artifact /
  label overlap). You MUST reproduce the honest causal construction (training rows < block
  minus max_h, shift(1) execution) and verify MONTHLY SR — not the inflated daily.
- features.py .. features6.py — feature builders (70-120 free features incl FF, macro,
  commodity, FX, crypto, 52w-high, skew/kurt, earnings proximity).
- Data panel: tools/quant/data/twelve_big + twelve_extend.

## Ideas (each must be CAUSAL and pass OOS)
1. **New horizons/feature combos not yet used**: try h10, h42, h63 horizons; ensemble of
   shallow trees; different K (5/15/20 names per side); different feature subsets (drop
   macro to test pure price; add lagged fundamental via alphaportfolio_replication
   fundamentals_annual.parquet PIT).
2. **Breadth/regime-gated variants**: gate the L/S on breadth, VIX state, credit state
   (trailing-only) to add regimes — improves robustness not return alone.
3. **Different universes**: use twelve_extend (440 names) for a wider panel; or the
   commodity/cross-asset panel for a non-equity ML book.
4. **Long-horizon (60-250d) books**: momentum-style ML on the panel, but PIT and causal.
   The 1y-horizon XGB (XGB1y) exists; find variants with different decay.
5. **Ensemble of cost-scaled deciles**: expand the h21 decile portfolio to include the
   full ranked book vs top/bottom K, then blend for smoother returns.

## HONESTY CONTRACT (CRITICAL — this family has had the most lookahead traps)
T+1. 6bps/side. Gates: FULL SR>=0.6, halves>=0.3, <=2 negYr each>-5%, scramble 200x,
vol-target trailing-only, plateau, economic rationale. **MANDATORY: verify honest MONTHLY SR,
not inflated daily SR.** Cross-check: compare your daily SR vs monthly SR — if daily SR >~1.5x
monthly SR there is spread/autocorrelation inflation unless you can explain it (e.g., a
genuine high-turnover book; then cost-test at 8 and 10 bps). Report both daily and monthly SR
for every saved sleeve/failed idea in FINDINGS.md.

## DELIVERABLE
Save passing sleeves (with .csv.meta: rationale, params, validation incl. monthly+scramble),
repro scripts in campaign/scripts/. Target: sleeves with monthly SR>=1.0, corr<0.2 to all
library sleeves, that ADD ann at equal vol. Report all ideas + numbers in FINDINGS.md.
Last line: ROUND 1 DONE
