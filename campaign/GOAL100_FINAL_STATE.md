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

---

## ⚠️ REAL-TIME AUDIT CORRECTION (2026-09-02, /loop) — XGB1y FLATTENED-DAILY BUG

**The committed STRICTTRADE headline SR=5.24 is NOT trustable.** XGB1y (a MONTHLY-rebalance
20-name L/S book) was committed as a constant daily return ("spread to daily"), erasing all
intra-month volatility. That artifact-lifts the blended daily SR.

Evidence (XGB1y_deploy.csv): only 211 distinct values / 4684 rows; lag-1 autocorr 0.951;
Jan-2023 = +21.1bp EVERY day, Feb-2023 = +35.8bp EVERY day.

Impact (exact 4522-row rebuild, rebuild_exact.py recipe):
| Variant | ann | SR(d) | MaxDD | OOS17+ |
|---|---|---|---|---|
| As committed (XGB flat) | 49.4% | 5.24 | -6.05% | 55.9% |
| **XGB dropped (11)** | 39.6% | **4.22** | -4.85% | 44.1% |
| **XGB fairly reconstructed** | 45.7% | **2.23** | -4.96% | 49.6% |

**Honest SR is ~2.2-4.2, NOT 5.24.** Finding + corrected champions committed:
- campaign/agents/LOOP_XGB1YFLAT/FINDINGS.md (full writeup)
- campaign/results/GOAL100_HONEST11_daily_*  (39.6% ann, SR 4.22, DD -4.85%)
- campaign/results/GOAL100_HONEST12_XGBFAIR_daily_* (45.7% ann, SR 2.23, DD -4.96%)

Corrective actions still required (next loop iterations):
1. Re-emit XGB1y as a FAITHFUL daily series from actual daily holdings (SR(mo)=1.06 is honest
   but the daily path matters) OR drop it and use the 11-sleeve HONEST11 champion.
2. The DISTINCT-VALUES / autocorr sweep should be a permanent gate: any sleeve with ac1>0.5 or
   <8% distinct daily values in a daily blend is a RED FLAG (see sweep in /tmp).
3. SR>=5 target is NOT met by the honest champion. Path forward = genuinely new decorrelated
   DAILY engines (the current DD headroom: honest MaxDD ~5% vs 7% wall is ample).
