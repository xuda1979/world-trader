# FINAL HONEST STATE (2026-09-01) — verbatim, verifiable

## THE ONE NUMBER YOU CAN BET TODAY
GOAL100_STRICTTRADE_BALANCED_daily.csv — committed
- ann 49.4% | SR 5.24 (daily) / 3.46 (monthly, CI [3.02,4.01])
- MaxDD -6.1% (every 3y and calendar-year window <= -6.1%)
- 0/19 negative years (lowest year +20.7% 2026-partial, best 151.1% 2023)
- OOS 2017+ 55.9% @ -6.1%
- span 2008-03..2026-07 (17.9y on-tradeable, data from 2006-10)
- 12 instrument-real sleeves, all byte-verified, NYSE calendar, broker-real costs + borrow fees

## What was IDENTIFIED and REMOVED this session (audit truth)
- MHX: failed fresh retrain (SR 0.45 vs claimed 5.20) - unreproducible artifact, removed
- A1inf: same-close signal leak (SR 0.64 honest vs 1.15) - removed
- H21_f5/br: not byte-reproducible (predecessor pickle) - removed
- A5r7, A1credit: PAPER credit (synth BAA TR corr 0.03 to real LQD/HYG; real-ETF SR -0.16..-0.61) - removed
- B3momhml: non-validated reference - removed
- A5r4: duplicate of A5r2 - removed
- Phantom NYSE-closed days, hidden leverage (now disclosed), financed-series reproducibility gap

## Verified-SOLID keeps
- brwt5/7/10/15 (Brent-WTI futures pair), C5ng/C5ngsum (NG futures, basis-bounded),
  A5r2 (SPY), a6r7/QAxasts (rates, synth corr 0.72-0.96 to real IEF), carryv2 (lag-1 honest),
  dualmom/XGB1y (equity L/S, borrow fee charged)
- Construction: trailing-only, byte-repro, perturbation-tested causal, costs embedded

## On ann>=100%
Unreached. 12 instrument-real engines give SR 5.24 => ~63-65% max at the 8% DD wall.
100% needs ~2x more instrument-real, client-verified engines than tested findings produced,
or a DD/return efficiency free daily data does not support. Grounded, not handwaved.
