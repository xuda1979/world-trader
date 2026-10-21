# FINAL HONEST STATE (2026-09-02, loop iter 5) — verbatim, verifiable

## THE ONE NUMBER YOU CAN BET TODAY
**GOAL100_HONEST13V2_BALANCED_daily.csv** — committed
- 13 engines: 11 instrument-real sleeves + diescrack_L40Z20 (diesel-crack basis, SR 1.01,
  corr 0.05) + CFX4 (FX 4-book z-reversion, SR 1.91, corr 0.00), new sleeves at capital slot
  weight 0.10 each
- ann(geo) 43.8% | SR_d 3.91 | SR_m 3.99 (block-boot 95% CI [3.55,4.55])
- MaxDD -4.96% (worst 3y-subwindow also -4.96%) — 2.0pp headroom to the 7% wall
- 0/19 negative years 2008+ (worst +13.9% 2011); full-span file has 2006 warmup stub -1.4% (60/61
  zero-signal days — pre-live, disclosed)
- OOS17+ arithmetic 40.8%
- costs: 6bps/side on ALL turnover incl. exact position-path vol-target rebalance; borrow
  0.5%/yr (dualmom HTB uplift); capital-real gross mean 3.45x / p95 7.18x (leverage<=1.6
  capital-real would cap ann at ~19% — infeasible with the 80% goal, exact sweep committed)
- construction: trailing-only (T+1 verified by extra-lag probes), NYSE-rows-kept calendar,
  byte-reproducible 11-pool builder (campaign/scripts/honest11_build.py --verify/--verify-l16)

## WHY NOT THE OLDER BIGGER NUMBERS (audit truth, keep in every claim)
- STRICTTRADE SR 5.24: XGB1y flattened-daily artifact → removed
- L16 47.6% @ "1.59x": inner-join calendar hole + leverage definition excluded global scalar →
  corrected (rows-kept FIX) and definition fixed to capital-real
- X804 "80.5% @ 2.5x": NOT byte-reproducible by two independent auditors (best 75.7%); capital-
  real gross actually ~4.6-5.2x → UNRELIABLE, do not quote
- The scramble gate as charter-written (return permutation) is DEGENERATE — two agents proved it
  independently; the meaningful test is the position-lag scramble (p=0.0000 for both new sleeves)
- audit_harness zRuns gate was bool-broken (always 0) since inception — fixed 2026-09-02

## Goal scoreboard (V2, exact)
| Goal | Achieved | Verdict |
|---|---|---|
| ann >= 80% | 43.8% (80% needs ~5x gross & breaches 7% wall even there) | FAIL |
| SR >= 5 | 3.91 d / 3.99 m; scale-invariant; CI excludes 5 | FAIL |
| MaxDD <= 7% | -4.96% (worst-3y same) | PASS |
| leverage <= 1.6 | 3.45x capital-real mean (1.6x caps ann ~19%) | FAIL |
| profit >= 0 every year | 0/19 (2008+), worst +13.9% | PASS (scoped) |

## What was IDENTIFIED and REMOVED (2026-09-01 session + iter1-4 corrections)
- MHX: failed fresh retrain (SR 0.45 vs claimed 5.20) - unreproducible artifact, removed
- A1inf: same-close signal leak - removed; H21_f5/br: not byte-reproducible - removed
- A5r7, A1credit: PAPER credit (synth corr 0.03 to real LQD/HYG) - removed
- B3momhml: non-validated - removed; A5r4: duplicate of A5r2 - removed
- XGB1y: flattened-daily (211 distinct values/4684 rows, ac1 0.951) - removed
- Phantom NYSE-closed days, hidden leverage (now capital-real disclosed), OOS geo/arith
  convention standardized to ARITHMETIC

## Verified-SOLID keeps (13-engine pool)
- brwt5/7/10/15 (Brent-WTI), C5ng/C5ngsum (NG), A5r2 (SPY), a6r7/QAxasts (rates),
  carryv2 (lag-1 honest), dualmom (equity L/S) + diescrack_L40Z20 + CFX4 (iter4 team finds,
  gate-audited; CFX4 concentration top-50d=74% PnL disclosed)

## Honest ceiling assessment
SR is scale-invariant ~4.0 on this pool. SR>=5 AND ann>=80% at capital-real leverage<=1.6 and
DD<=7% remains INFEASIBLE on current engines/data. Feasibility frontier (exact, committed):
at all-in 1.6x → ann ~19%; at DD 7% wall → ann ~55% (SR 3.9); at 5x gross → 77-80% but DD
breaches 7%. Only genuinely new decorrelated engines (need >=2 more at SR>=1.5, corr<0.1) or
new data (FX deposit rates, futures chains, intraday) move the ceiling.

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

---

## /loop ITER 2 (2026-09-02) — honest return/DD/leverage lever discovered; SR is scale-invariant
Canonical builder frozen: `campaign/scripts/honest11_build.py` (reproduces HONEST11 byte-for-byte,
max|diff| 9.9e-17) — fixes the "builder not committed" provenance hole. 11 real sleeves.

**Ann >=80% AND MaxDD <=7% ARE jointly achievable and COMMITTED (HONEST11X804):**
TGT 0.11/0.14 -> ann(geo) 80.5%, MaxDD -6.73% (worst 3y-subwindow also -6.73%), 0/19 neg yrs,
OOS17+ 67.3%. Single global scalar; full broker costs + borrow already in construction.

**BUT the honest cost = ~2.5-3x GROSS LEVERAGE** (decorrelated blend realized vol ~5.3% << 10%
per-sleeve target, so the global vt applies a large scale). "Weights sum to 1" is normalized-only.

**SR is scale-INVARIANT ~4.2 (daily) / 4.0-4.2 (monthly).** Raising vol target does NOT raise SR.
So SR>=5 is NOT reachable by scaling; only new decorrelated high-SR DAILY engines would help, and
that search remains hard (FX spot/carry, EM/DM factors, global indices, gold-silver all failed).

Current trustworthy frontier (HONEST11, 11 real sleeves, no flattening artifact):
  - Unlevered-ish (~1.4x gross): 47.9% ann, SR 4.19, MaxDD -4.85%
  - Disclosed-leverage 80.5% ann (HONEST11X804, ~2.5x): MaxDD -6.73%, 0/19 neg yrs
