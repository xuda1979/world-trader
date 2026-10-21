# C1_kfindustry — FINDINGS (Round 1, 2026-09-01)

Domain: Ken French daily portfolios (48/49 ind, 25ff, ME deciles, 10 prior-12-2, 6x2x3).
Backtest contract everywhere: signal(t) from data<=t, position earns t+1 (T+1); costs 6bps x
one-side turnover per day; vol-target 10% ann via trailing expanding window (min 60d, clip 3.0);
window 2008-09..2026-08 (4652 days); gates = brief gates (full SR>=1.0, H1&H2>=0.5, negy<=2,
worst yr >-5%, scramble 200x p>0.05, |corr|<0.15 vs COORD_FINAL blend).
Lib: campaign/scripts/c1_lib.py. Repro: c1_idea1_indmom.py, c1_idea3456_spreads.py, c1_idea7_composite.py.

## Raw-material diagnostics (before any timing)
- 2008+ SR of underlying factor books: SMB -0.00, HML -0.01, UMD +0.11, Mom decile Hi-Lo +0.17,
  ME10 SMB raw -0.22, 25ff BM5-BM1 by size quintile: ME1 +0.35, ME2 -0.03, ME3 +0.04, ME4 -0.09, ME5 +0.11.
  => factor premia are essentially DEAD post-2008 in this dataset; timing engines had little to harvest.
- Lead-lag predictivity: industry lag-1 own autocorr mean -0.044 (6/48 positive); aggregate in-sample
  R2 of regressing all 48 industries on all lag-1 industries = 2.98% (upper bound, no cost) -> no tradeable lead-lag.
- EW-VW 48-industry breadth (idea 6 signal): 2008+ SR 0.28 unscaled, autocorr 0.07; breadth63 sign has
  corr -0.007 to next-21d avg industry momentum -> no predictive content. Idea 6 dead on arrival.

## Idea-by-idea results (all FAIL, no sleeve saved)

1. Industry momentum (48 VW + EW, look 21/63/126/252, skip 0/5/21, hold 1/5/21, k 3/6, raw/z/vol-norm).
   BEST cell 2008+: 126d skip21 hold21 top3-bot3 net SR +0.13 (ann 1.7% pre-VT), VT mdd -96.5% (scale
   blown up pre-2008), corrB +0.10. Daily rebalance variants: SR -0.1 to -2.6 (turnover 1.2-2.9x/day =
   7-17%/yr cost). Momentum crash 2009: gross -37.7% for 126d daily version. Scramble p n/a (SR~0).
   Code sanity: same code 1965-2000 gives net SR 0.36 -> decline is real regime, not a bug.
2. Industry reversal (5/10/21d, k 3/6/10, hold 1/5, raw + vol-normalized, 48 VW/EW). ALL negative.
   Best net SR -0.38. At industry level there is NO net short-term reversal after 6bps.
   Trap noted & rejected: 5d top3-bot3 daily rebalance shows NET SR -1.87 which I initially mis-read as
   gross 1.87; true GROSS SR is +0.02 (edge zero; cost drag 22%/yr at 8.6bps/day). No hidden gem.
3. Size/value spread timing (sv25=SMALL HiBM-LoBM, bv25, SMB10 ME deciles, SMBff; sign & z timing,
   w 10..126). BEST: sv25 w=21 sign: net SR 0.68, VT ann 8.6%, mdd -21.7%, H1 1.10 / H2 0.48,
   negy 5, worst yr -16.0%, corrB -0.02, scramble p 0.975. GENUINE signal (real, uncorrelated to blend,
   stable H1) but FAILS full-SR>=1.0, H2>=0.5, negy<=2, worst>-5%. Grid shows mild plateau (w21 0.68,
   w15 0.57, w42 0.47, w30 0.30) but peak too low to matter.
4. Momentum-decile engines (Hi-Lo decile raw SR 0.17; 63d sign-timing -0.20; vol-managed UMD SR 0.49,
   corrB +0.14). Vol-managed UMD is the single best single-factor artifact (Moreira-Muir works) but
   SR 0.49 << 1.0 and corrB 0.14 is borderline vs the 0.15 decorrelation cap. FAIL.
5. 6-portfolio 2x3 sleeves (Small/Big BM spread timing): Small BM w=63 z SR 0.14, Big BM -0.06; SMB-ish
   SHiBM-BLoBM not better. 25ff XS momentum top3-bot3 hold21: VT SR -0.04. FAIL.
6. EW-vs-VW breadth timing: breadth itself SR 0.28 (not tradeable after costs at 6bps given daily
  turnover), zero correlation to forward industry momentum (-0.007). FAIL.
7. Composite of best 3 (sv25-w21-sign + vol-managed UMD + indmom126/21skip/hold21): VT SR 0.81,
   ann 9.0%, mdd -16.6%, H1 0.87 / H2 0.75, negy 2, worst yr -7.8%, corrB +0.11, scramble p 0.93.
   BEST artifact of the round; legs are mutually decorrelated (pairwise corr 0.05/0.01/0.59) and
   negy/scramble/corr pass, but FAILS full-SR>=1.0 and worst-yr>-5%. Not saved per contract.

## Honest conclusions for the campaign
- KF daily industry/portfolio cross-sections are a WASTELAND post-2008 at 6bps: the only genuine
  2008+ phenomena are (a) small-value spread momentum (SR 0.68, corr -0.02) and (b) vol-managed UMD
  (SR 0.49). Both are far below the SR>=1.0 new-engine bar. Composite 0.81 confirms no additive magic.
- These datasets remain useful as REGIME/FILTER inputs for other agents (e.g., breadth, dispersion),
  not as standalone alpha. Recommend C-series not re-mine industry momentum/reversal; small-value
  timing (w=21 sign, T+1, ~27 pos flips/yr) is the one idea worth revisiting if a better construction
  (e.g., conditioning on credit or vol regime) can lift SR from 0.68 toward 1.0.

ROUND 1 DONE

# C1_kfindustry — ROUND 2 (2026-09-01, per CHARTER_2.md pivot)

Window/contract unchanged from Round 1: 2008-09..2026-08, T+1, 6bps/side on one-side turnover,
VT 10% ann trailing expanding (min 60d, clip 3.0), gates = full SR>=1.0, H1&H2>=0.5, negy<=2,
worst yr > -5%, scramble 200x p>0.05, |corr|<0.15 vs COORD_FINAL blend.
Scripts: campaign/scripts/c1r2_{lib,idea1_volsort,idea2_disp,idea345,idea5_rs,idea6_volmgmt,idea7_49ind}.py.

## CHARTER_2 idea-by-idea (ALL FAIL, nothing saved)

1. 48-industry VOL-SORTED rotation (long low-vol/short high-vol ind; L 21/63/126 x k 6/10 x
   daily/weekly = 12 cells): ALL NEGATIVE. Best = L126 k6 weekly net SR -0.19 (ann -1.5%, mdd
   -46.9%, corrB -0.18). Sign-flip best cell would be +0.57 SR (L21 k10 daily) but corrB +0.19
   fails decorrelation and H1 -0.17 fails halves. Post-2008 low-vol industries UNDERPERFORM
   high-vol at industry level — the defensive premium is absent/inverted in KF industries. FAIL.
2. Cross-industry DISPERSION timing (21d/5d RMS disp, z vs expanding): conditioning momentum on
   low-disp + reversal on high-disp gives net SR 0.11 (worst of both parents). Disp z DOES
   positively predict fwd-21d EW industry return (corr +0.103 at lag0, +0.136 at lag21), so I
   tested the direct book "long EW-48 when z<0, flat else": SR 0.51, ann 5.3%, mdd -18.6%, H1
   0.55/H2 0.48, negy 5, worst -9.3%, corrB 0.272 — fails full-SR, H2, negy, worst-yr, corr. FAIL.
3. SMB timing (ME Lo10-Hi10 sign, w 21/63/126/252): best w126 SR 0.38 (negy 6, worst -21.1%). FAIL.
4. Momentum-decile TS books (per-decile sign, vol-scaled EW, 63/126/252 daily+weekly): best
   look252 weekly SR 0.50, H1 0.51/H2 0.49, negy 6, worst -8.9%, corrB +0.33 (fails corr hard).
   Hi-Lo 126 sign: -0.08. FAIL.
5. 6-portfolio 2x3 factor momentum (EW of 6 sign-timed legs, 126/252 daily+weekly): best 0.17
   (look252 weekly), negy 10. 25ff legs are far too weak. FAIL. 48/49-industry RELATIVE-STRENGTH
   vs cap-wtd market (21/63/126 x k3/6/10 weekly, 9 cells): best 0.20 (126 k3), negy 11. FAIL.
6. Vol-MANAGEMENT overlays (Moreira-Muir) on factor books (SMB/HML/Mom, look 21/63) + own-vol
   overlay on R1-best industry momentum + reversal: VM Mom63 = best single new artifact at SR
   0.40 (ann 4.0%, mdd -25.2%, H1 0.21/H2 0.59, negy 6, corrB +0.14 — corr OK but SR far short);
   VM SMB and VM HML both NEGATIVE (-0.1 to -0.17); indmom+overlay max 0.35; rev5+overlay -0.80.
   FAIL (overlay confirms: only UMD responds to vol management; everything else is dead anyway).
7. 49-industry re-check + sv25 regime gating: 49ind mom 126-21 top3-bot3 weekly SR 0.40 (negy 8);
   49ind volsort -0.34. R1-best sv25 w21 sign recheck SR 0.59 (this round's lib; R1 said 0.68
   under slightly different windowing — same conclusion). Regime gating by market vol<75pct:
   SR 0.72, ann 9.3%, mdd -23.5%, H1 0.80/H2 0.63, negy 4, worst -16.8%, corrB -0.00, scramble
   p 1.0 — gating lifts SR 0.59->0.72 and H2 0.52->0.63 but STILL fails full-SR>=1.0, negy<=2,
   worst>-5%. Asymmetric long-only sv25: 0.56 (negy 9). FAIL.

## Composite (best 4 legs, pairwise corr 0.00-0.42)
sv25-volgated + VM-Mom63 + 49ind-mom + momdec252: equal-weight SR 0.68 (negy 4, corrB 0.183);
sv25-tilted (0.5/1/6 x 4) SR 0.79, ann 8.0%, mdd -16.1%, H1 0.69/H2 0.89, negy 3, worst -8.4%,
corrB 0.146, scramble p 0.995. BEST ROUND-2 ARTIFACT but fails full-SR>=1.0, negy<=2, worst>-5%.
Not saved per contract.

## Honest round-2 verdict
KF daily portfolio cross-sections are EXHAUSTED as an alpha domain for this campaign: across
2 rounds and ~80 tested configurations, the post-2008 net-of-cost ceiling is SR ~0.7-0.8
(sv25 spread-timing family), everything else <= 0.5. The negy<=2 and worst>-5% gates are
unreachable because factor spread books have genuine multi-year droughts (2010s small-value
crash is IN the signal's favor window but 2009/2015/2018 drawdown years remain). Recommend
coordinator stop assigning this domain to alpha mining; sv25 w21 + vol-gate could be offered
to C4_metaalloc as a LOW-corrB (0.00) diversifier at 1/10 weight if blend needs uncorrelated
bulk, accepting its 9% ann / -23.5% standalone mdd. Nothing saved this round; no frontier move.

ROUND 2 DONE

# C1_kfindustry — ROUND 3 (2026-09-01, per CHARTER_3.md: conditional books + reversal-within-winners)

Contract unchanged: 2008-09..2026-08 net window, T+1, 6bps/side on one-side turnover, VT 10%
trailing expanding (min60d, clip 3.0), gates = full SR>=1.0, H1&H2>=0.5, negy<=2, worst yr > -5%,
scramble 200x p>0.05, |corr|<0.15 vs COORD_FINAL blend. Repro: campaign/scripts/c1r3_charter.py.
NOTE: bugs found & fixed en route — my earlier c1 half-life formula had an off-by-one
(phi_mine = phi_AR - 1); corrected version used everywhere this round (HL 5-60d window).
Also note pre-VT raw numbers quoted here for grid comparison; gate numbers are post-VT net.

## Idea-by-idea (ALL FAIL, nothing saved)

1. MOMENTUM w/ SKIP (crash-avoidance): 48-ind VW, grid L{63,126,252} x skip{0,10,21} x k{3,6}
   x weekly/daily = 36 cells. Weekly cells NEGATIVE (best -0.36). Best cell mom252-skip21-k3
   daily: net SR 0.30 (ann 9.0%, mdd -68.2% pre-VT, negy 9, worst yr -47.4%, corrB +0.118).
   21d skip adds ~+0.1-0.2 SR over no-skip at L252 but nowhere near 1.0. FAIL full-SR, negy,
   worst-yr, mdd.
2. REVERSAL-WITHIN-WINNERS (dip-in-strength): rank(mom L{126,252} + reversal rv{5,10,21}) add/
   conditional, k{6,10}, wk/dy = 48 cells. 'add' variant produced empty books (NaN sig rank
   bug — dead weight, dropped); conditional long win&recent-down vs short lose&recent-up is
   uniformly NEGATIVE: best dip252-rv21-cond-k10-dy SR -0.14, worst -0.93. Buying the dip in
   industry strength loses post-2008; shorting recent strength among momentum losers also
   loses (consistent with idea 1: short side of industry momentum is toxic). FAIL.
3. 48-INDUSTRY PAIR SPREADS (brwt-style): walk-forward pair pick every 63d on trailing 756d
   log-ratio (corrected half-life 5-60d filter, top-20 by reversion ratio), z63-signal,
   gross-normalized book. Continuous z-scaled: SR -0.84. Threshold banded entry/exit
   zth{1,1.5,2} x ZW{21,63} x rev/mom: BEST -0.18 (mom ZW63 zth2.0); pure reversion all
   -0.48..-0.83. Industry-pair log-ratios do NOT mean-revert net of 6bps at daily/weekly
   horizon (n_cand ~265-365 pairs pass HL filter per window, so it's not selection sparsity —
   the edge is absent; beta-1 industrial pairs are dominated by sector trend). FAIL all.
4. VOL-MANAGED MOMENTUM (inverse-21d-vol weights inside top6/bot6 mom252 book): 16 cells,
   best vm-mom252-k6-ind-daily SR 0.24 (ann 2.8%), weekly negative to -1.98. Inverse-vol
   tilting CANNOT rescue a parent book at SR~0.2-0.3. FAIL.
5. WEEKLY/TOM SEASONALITY: turn-of-month (last day + first 3 days) long-EW-48: SR 0.20
   (ann 1.5%, corrB +0.147). Per-industry TOM-vs-rest t-stats: max |t| = 3.05 (Telcm) < 4.0
   Bonferroni-48 threshold — no industry passes. Anti-TOM (rest-of-month long) SR 0.61
   (ann 4.5%) — the complement is stronger than the effect itself, i.e. there is no exploitable
   TOM edge in 2008+ KF industries. FAIL.

## Composite of survivors (charter item 7)
Best 3 legs pairwise corr: mom252sk21 vs vm-mom252 +0.81 (same parent!), antiTOM vs each
-0.10/-0.20. EW-of-3 net: SR 0.50, ann 6.0%, mdd -26.4%, negy 7, worst -16.7%, H1 0.53/H2 0.47,
scramble p 0.995, corrB +0.215. FAILS full-SR, negy<=2, worst>-5%, |corr|<0.15. Not saved.

## Honest round-3 verdict
Round 3 CONFIRMS the round-2 conclusion with the conditional/interaction refinements the
charter proposed: the Ken-French daily industry cross-section has NO post-2008 net-of-cost
edge above SR~0.3-0.6 in any of the ~130 configurations tested this round (cumulative ~210
across 3 rounds). Structural diagnosis: (a) industry momentum works pre-2008 but its post-2008
net ceiling is ~0.3 with catastrophic drawdown years; (b) the short side of every winner-long
book is the loss source and skip/dip/vol-weighting variants cannot fix it; (c) industrial
pairs mean-revert too slowly (or trend) — no brwt analog exists inside KF industries;
(d) calendar effects are <4 t-stat. DOMAIN CLOSED for alpha mining. No sleeve saved; frontier
unchanged. Final recommendation stands: sv25 w21 vol-gated (R2, corrB 0.00, SR 0.72) remains
the only hand-off candidate for C4_metaalloc.

ROUND 3 DONE
