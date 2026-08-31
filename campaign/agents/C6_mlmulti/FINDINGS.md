# C6_mlmulti FINDINGS (ROUND 1)

## IDEA 1: Curve-ML (walk-forward Ridge, curve features -> next-day DGS10 dy -> 10y bond book -8.5*dy)
- Setup: 18 trailing features (DGS2/5/10 d1/d5/d21, slope z, 5yBE z, credit spread z, VIX z, butterfly z), Ridge alpha {10,100,1000} picked on trailing 252d, refit quarterly expanding (min 504d, 5d purge), 2008-04 -> 2026-08, 3737 OOS preds, vol-target 10% trailing, 6bps on |dw|.
- Result: FULL net SR -0.02, ann -0.09%, H1 -0.19 / H2 0.32, 9/18 neg yrs, worst -13.5%, MDD -20.4%, OOS 2017+ SR 0.32, corr vs blend -0.02.
- Diagnosis: predictions ~0 (positions ~0; scale mean 0.04 -> model R2 ~ 0). Simple baselines also dead: meanrev_dy_21 SR 0.15, fade_slope SR -0.35, long_bond_highvix SR 0.05. Daily DGS10 changes are unpredictable from free curve features.
- VERDICT: FAIL (full SR < 1.0). Domain exhausted at daily frequency — do not retry without new data.

## IDEA 2: KF-industry-ML (xs Ridge on 48-industry VW rank features -> 5d xs-z fwd ret -> top3/bottom3 LS, daily holds)
- Setup: 7 rank-z features (mom 21/63/126/252, vol21, ret1, market-wide dispersion), Ridge alpha {1,10,100} via trailing-half CV, refit quarterly expanding (purge 12d), scores from 2007-07, LS book +0.5 top3 / -0.5 bottom3, 6bps on rank changes, vol-target 10%.
- Result: FULL net SR -0.76 (ann -6.5%), H1 -0.63 / H2 -0.87, 16/19 neg yrs, MDD -75%, OOS SR -0.81, corr blend 0.04. Baseline mom63 top3/bot3 SR 0.42 -> ML overlay is sign-INVERTED (+0.76 if flipped, still < 1.0 gate).
- Diagnosis: 48 VW industry portfolios carry little 5d xs edge post-2008; trained model exploits 2004-2016 short-term reversal that died OOS.
- VERDICT: FAIL (full SR < 1.0).

## IDEA 3: Positioning-ML (COT/TFF money-manager z + price momentum/vol -> per-market GBM 5d sign, 14 markets)
- Setup: m_money_long-short (commod) / lf_net (financials) z(52w) + r21/r63/v21 -> GradientBoostingRegressor(60, d2, lr .05, monthly walk-forward refit, purge 7d) -> 5d sign, T+1, 6bps, vt 10%. Prices: FRED/newdata with futures sign alignment (wti/brent/natgas/gold/silver/spx/us10y negated where short-only convention).
- Per-market SR: natgas 0.31, gold 0.25, silver 0.09, copper 0.01, brent -0.01, jpy -0.07, wti -0.29, spx -0.27, us10y -0.26, cad -0.24, aud -0.19, chf -0.20, eur -0.34, gbp -0.83. Equal-weight book: FULL SR -0.15, ann -1.2%, H1 -0.45/H2 0.11, 11/19 neg yrs, OOS SR 0.04, corr blend 0.03, scramble p 0.83.
- Diagnosis: weekly MM positioning has no 5d directional edge at daily resolution post-2008; GBM signs are coin flips (book vol scaled by vt so noise -> flat-negative).
- VERDICT: FAIL (full SR < 1.0). COT domain unlikely to yield >1.0 SR without event-driven overlay.

## IDEA 4: FX-cross-ML (8 FX + gold/rates/vix features -> GBM 5d DXY sign -> inverse-DXY 4-major basket, vol-norm)
- Setup: 30 trailing features (per-pair r5/r21/z63/v21 for eur,gbp,jpy,cad,aud,chf + xau r21 + 2s10s spread/level + vix z + dxy r5/r21), GradientBoostingClassifier(80,d2,lr .05) monthly walk-forward (purge 7d), p-0.5 signal -> short-USD majors book (jpy sign-corrected), 10% vol/leg, vt 10%.
- Result: FULL net SR -0.76 (ann -9.9%), H1 -0.20 / H2 -1.44, 13/19 neg yrs, worst -34.7%, OOS 2017+ SR -1.47, corr blend -0.01.
- Diagnosis: GBM DXY sign ~ coin flip; short-USD carry-negative basis bled via vol-normalized sizing (2017-2020 disaster). No net edge.
- VERDICT: FAIL (full SR < 1.0).

## IDEA 5: Regime-ML meta-allocation (trailing sleeve-pool stats -> GBM 21d fwd excess ret -> monthly tilt, 60 sleeves)
- Setup: features per sleeve = trailing 126d vol, mom, windowed drawdown, excess-mom-vs-EW (all trailing); GradientBoostingRegressor(60,d2,lr .05) on pooled (date,sleeve) rows (750d train), monthly walk-forward refit, purge 22d, mild rank tilt 0.25 sigma around EW; T+1, 6bps on weight changes, vt 10%.
- Result: ML-tilt FULL SR 1.50 (ann 14.7%), H1 1.48/H2 1.52; OOS 2017+ SR 1.65 vs EW-pool OOS SR 1.63 (+0.02 — inside noise, no significance). Corr vs COORD blend 0.441 (>> 0.35, fails even secondary bucket). MDD -11.5%.
- Diagnosis: by construction this sleeve is a perturbation of the pool that IS the blend; 60-sleeve trailing-feature tilt has ~zero real OOS alpha over EW and guarantees high correlation. Charter correctly demands OOS beat EW — the +0.02 is not a beat.
- VERDICT: FAIL (corr 0.441 >> 0.35; OOS edge +0.02 SR = noise).

## ROUND-1 SUMMARY (C6_mlmulti) — all 5 charter ideas executed, ZERO sleeves saved
| # | idea | FULL net SR | H1/H2 | OOS 2017+ | corr blend | verdict |
|---|------|------------|-------|-----------|------------|---------|
| 1 | Curve-ML (bond book) | -0.02 | -0.19/0.32 | 0.32 | -0.02 | FAIL SR |
| 2 | KF-industry-ML (top3/bot3) | -0.76 | -0.63/-0.87 | -0.81 | 0.04 | FAIL SR (sign-inverted still 0.76<1.0) |
| 3 | Positioning-ML (COT 14 mkts) | -0.15 | -0.45/0.11 | 0.04 | 0.03 | FAIL SR |
| 4 | FX-cross-ML (DXY book) | -0.76 | -0.20/-1.44 | -1.47 | -0.01 | FAIL SR |
| 5 | Regime-ML meta (60-sleeve pool) | 1.50 | 1.48/1.52 | 1.65 vs EW 1.63 | 0.44 | FAIL corr + no real OOS edge |

HONEST VERDICT: walk-forward sklearn GBM/Ridge on free daily macro/curve/positioning/FX data shows NO
daily-directional edge (all raw signal SRs <= 0.3). The only sleeve above SR 1.0 was the meta-tilt,
which is just the existing pool (corr 0.44 to blend, +0.02 OOS vs EW = noise). A frontier jump toward
100% ann will NOT come from ML on these domains; it needs new structurally-inefficient books like the
Brent-WTI spread engine. Next-round candidates: (a) intraday/session FX crosses, (b) options-implied
skew surfaces, (c) non-US curve butterflies traded via on-disk 10y panels (au10y/ca10y/ch10y/ez10y...),
(d) cross-market energy crack/spread books beyond brwt.
ROUND 1 DONE

# ROUND 2 (charter: CHARTER_2.md) — ML re-tests conditioned on round-1 verdicts

Round-1 recap used for charter routing: curve-ML OOS SR 0.32 (<1.0), KF-industry OOS -0.81,
positioning dead (C3: 450-variant sweep max 0.60), FX/dxy GBM full SR -0.76. Therefore items
1-3 of charter 2 are conditional skips (conditions unmet) and were not re-run; items 4-6 executed,
plus 2 charter-linked rescue attempts. Shared lib: campaign/scripts/c6_round2_lib.py.

## CHARTER ITEM 1 (skip, condition unmet): multi-tenor curve-ML — round-1 curve-ML OOS SR was
0.32 << 1.0 (predictions ~0, R2≈0). Scaling a dead signal to more tenors cannot pass gate (a). SKIP.

## CHARTER ITEM 2 (skip, condition unmet): deep 48x5 KF feature set — round-1 OOS SR -0.81,
sign-inverted vs baseline; C1 (round 1) proved 48-industry xs is a post-2008 wasteland at 6bps. SKIP.

## CHARTER ITEM 3 (skip, condition unmet): positioning-ML — C3 swept ~450 COT/TFF variants,
top SR 0.60 (copx flow8 z52). Dead domain. SKIP.

## IDEA 4 (charter item 4): FX-cross-ML with DEX* daily panel + DTWEXBGS target
- Setup: 9 FRED DEX pairs (DEXSEUS empty — dropped) r5/r21/z63/v21 + DTWEXBGS r5/r21/z63 + dxy z63
  + vix z + 2s10s d21 + xau r21 (44 feats) -> GBM(80, d2, lr.05) next-5d DTWEXBGS sign, walk-forward
  refit 21d, purge 8d, min 504d, p-0.5 signal -> dollar book (majors via DEX noon-rate proxy;
  data/fx/*.csv start 2019-04 only -> unusable for a 2008+ engine), T+1, 6bps on full repositioning
  turnover, trailing expanding vt 10% cap 3. 2008-09..2026-08, n=4029 traded days.
- Result: FULL net SR **-3.01** (ann -4.6%), H1 -3.07/H2 -3.21, 17/19 neg yrs, worst -8.8%, corrB -0.036.
  Coin-flip signal (sig std 0.085) at max turnover = pure cost bleed (~12bps/day). Sign-timed DTWEXBGS
  momentum baselines: mom5 SR -3.31, mom21 SR -2.24 (same cost bleed).
- Diagnosis: FRED fixing-based FX has zero sign edge at 5d; the -99.9% MDD in first run was a
  pre-trade-zeros vt bug (fixed) — even corrected, edge is 0 and 6bps x full-turnover dominates.
- VERDICT: FAIL (full SR << 1.0). Confirms round-1 item 4; FX-sign-ML domain closed.

## IDEA 5 (charter item 5): ML on sleeve-pool meta-state (must beat EW OOS 2017+)
- Setup: pool = 62 saved sleeves (agents/*/sleeves + results/sleeve_library, >=1500 obs, complete to
  2025+, 2009-01..2026-08). Per sleeve-month features [sr21, sr63, sr252, vol21, vol63, dd252] +
  cross-sectional [63d dispersion, 63d avg pairwise corr] -> Ridge(alpha=10) on fwd-21d sleeve ret,
  walk-forward expanding, refit 12m, purge 42d, start 2014. Weights: top-5 long-only EW (Ridge) +
  top-5 GBM(60,2,.05) + exclude-predicted-worst-5 variant; T+1, monthly, 6bps on rebalance.
- Result (OOS 2017+): Ridge-top5 SR **0.96** ann 15.6% | GBM-top5 SR **0.99** ann 11.9% |
  exclude-worst5 SR **1.43** ann 12.0% | pool-EW SR **2.02** ann 20.5%. FULL: EW 1.75 vs best ML 1.43.
  corr(ml,blend) 0.19-0.22 — moot, since the required comparison (beat EW OOS) fails by ~0.6-1.1 SR.
- Diagnosis: every pool member is already a gate-passing (or near-passing) sleeve; EW-of-goods is
  nearly unbeatble, and trailing-SR features select the previous month's lucky sleeve (mild
  anti-persistence at 21d). ML adds concentration risk, not selection alpha.
- VERDICT: FAIL (loses to EW OOS in all 3 variants). Meta-ML closed unless pool gains weaker members
  (where relative ranking could matter) — not the current regime.

## IDEA 6 (charter item 6): XGB/GBM on full curve shape (PCA of DGS tenors)
- Setup: 10 tenors (DGS1MO/3MO/6MO/1/2/5/7/10/20/30 — DGS7 EXISTS (1969+), DGS3 does not; C2 note
  updated), expanding-demeaned PCA(3) refit 63d (purged: expanding window), feats = PC1/2/3 d1/d5/d21
  + 252d z + level + vix z + (baa-aaa) d21 + BE10 d21 (16 feats) -> GBM(80,2,.05) next-5d DGS10
  change, walk-forward refit 21d purge 6d min 504d, book -8.5*dy/5d, T+1, 6bps, vt 10%. 2003-08+,
  n=5754 (curve start 2001-07 limited by DGS1MO).
- Result: FULL net SR **-0.07** (ann -1.0%), H1 -0.04/H2 -0.12, 12/19 neg yrs, mdd -50.6%,
  OOS -0.15/IS -0.04, corrB 0.031. Top importances: PC2_d5 0.132, be_d21 0.118, level 0.110.
  PCA baselines: PC3-fade63 SR 0.08, PC2-fade63 -0.01, PC1-fade252 0.20 (scr p 1.0).
- Diagnosis: identical to round-1 curve-ML — daily 10y direction unpredictable from shape; PCA adds
  nothing over raw tenors (round 1). Confirms C2's finding that only static fly REVERSION (their
  saved SR 1.85 sleeve, corr 0.017) works in the curve domain — and that's already in the blend pool.
- VERDICT: FAIL (full SR << 1.0).

## IDEA 7 (charter-linked rescue, C1 recommendation): ML regime-gating of small-value spread momentum
- Setup: KF 25ff VW SMALL HiBM - SMALL LoBM spread; baseline C1 sv21 sign-timing repro: SR 0.70,
  H1 0.95/H2 0.52, 5 neg yrs worst -17.6% (matches C1's 0.68). Overlays: (a) Ridge(100) on 8
  trailing regime feats (vix z, slope z, cred z, umd mom/vol, sv mom/vol, mkt mom) -> fwd-21d,
  monthly walk-forward purge 22d, amplitude-weighted pos; (b) hard gates cred_z/vix_z > 756d median.
- Result: ML (a) SR **0.44** (ann 4.3%, OOS 0.33/IS 0.59) — DEGRADES baseline 0.70->0.44;
  gates: cred_z SR 0.25 (mdd -33.7%), vix_z SR 0.30 (mdd -39.5%).
- Diagnosis: small-value momentum has no exploitable linear regime structure in credit/vol/dollar
  features; conditioning removes the good months too. C1's hope for regime-lift 0.68->1.0 is dead.
- VERDICT: FAIL (all variants < 0.70 baseline, none near gate a).

## IDEA 8 (charter-linked rescue, C5 recommendation): ML tail-gating of natgas weekday premium
- Setup: C5 engine rebuilt (SR 1.53 repro vs C5's 1.74 — minor timing diff, same construction);
  HistGB(80,2,.05) quarterly walk-forward predicts next-day |strategy ret| from [rv5/10/21/63,
  absret10, price z252, month, dow dummies]; gate = 1/(1+50*pred) T+1 pre-vt. Control: rv10 gate
  1/(1+20*rv10).
- Result: ML gate SR **1.62**, mdd **-25.4%** (vs repro -27.5%); control SR 1.70, mdd -23.5%.
  Gate fires (scale<0.5) on 19% of days.
- Diagnosis: tail-gating trims DD by ~2-4pp at equal SR, but MaxDD -25% >> 8% — Henry Hub vol-of-vol
  makes the 8% sleeve-level DD gate structurally unreachable for any gas-spot book (C5's own verdict
  stands). Harness scramble gate also reports nonsense here (permuting PnL preserves mean/std; C5's
  position-shuffle is the valid test).
- VERDICT: FAIL (MaxDD gate unreachable; no save).

## ROUND-2 HONEST CONCLUSIONS
- 0 saves. All 6 charter items (3 conditional skips documented, 3 executed) + 2 rescues FAIL gate (a)
  or the idea-specific bar. Exact full-SR outcomes: FX-ML -3.01, meta-ML 0.96-1.43 vs EW 2.02 (OOS bar),
  PCA-curve -0.07, SV-regime 0.25-0.44, NG-tailgate 1.62 (DD fail).
- The only ML-ish artifact worth keeping on the shelf: the rv10 vol-responsive tail gate for
  gas-family books (control, SR 1.70, mdd -23.5% vs -27.5%) — construction tweak, not new alpha.
- Coordinator guidance: C6's domains (daily curve sign, FX sign, COT, KF xs, meta-selection over an
  all-goods pool) are exhausted for SR>=1.0 net engines at 6bps. New saves this campaign must come
  from new data domains, not ML on existing free panels. Meta-ML could re-run ONLY if the pool
  includes mediocre sleeves (relative ranking signal exists there), which the current gate contract
  discourages.
- Scripts: campaign/scripts/c6_round2_lib.py, c6_item4_fx_ml.py, c6_item5_meta_ml.py,
  c6_item6_pca_curve_gbm.py, c6_item7_sv_regime.py, c6_item8_ng_tail_ml.py. No sleeve CSVs saved.


## NUMBERED SUMMARY (round 2)
1. Charter-1 multi-tenor curve-ML: SKIPPED (condition unmet; round-1 OOS SR 0.32).
2. Charter-2 deep KF 48x5: SKIPPED (condition unmet; round-1 OOS SR -0.81).
3. Charter-3 positioning-ML: SKIPPED (condition unmet; C3 sweep max SR 0.60).
4. Charter-4 FX-ML (DEX 9 pairs + DTWEXBGS -> GBM 5d dollar sign): FULL SR -3.01, OOS -3.08, corrB -0.036, 17/19 neg yrs. FAIL.
5. Charter-5 meta-ML (62-sleeve pool, Ridge/GBM top5 + exclude-worst5, must beat EW OOS): Ridge-top5 0.96, GBM-top5 0.99, excl-worst5 1.43 vs pool-EW 2.02 (OOS 2017+). FAIL (loses to EW in all variants).
6. Charter-6 PCA-curve GBM (10 tenors, DGS7 exists, DGS3 missing): FULL SR -0.07, OOS -0.15, corrB 0.031; PC baselines <=0.20. FAIL.
7. Rescue A — ML regime-gate on small-value spread momentum (C1 near-miss 0.70): Ridge 0.44 (OOS 0.33), cred_z gate 0.25, vix_z gate 0.30 — all DEGRADE baseline. FAIL.
8. Rescue B — ML/vol tail-gate on natgas weekday premium (C5 repro SR 1.53/mdd -27.5%): HistGB gate SR 1.62/mdd -25.4%, rv10 control SR 1.70/mdd -23.5% — MaxDD <=8% structurally unreachable. FAIL (no save).
0 sleeves saved; 6 repro scripts saved under campaign/scripts/. Frontier unchanged by C6 this round.

ROUND 2 DONE
