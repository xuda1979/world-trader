# GOAL100 ITER 6.5 SYNTHESIS (2026-09-03) — verified by coordinator + independent recompute

Wave outcome of 7 parallel agents (superpowers rigor applied throughout). Every headline
independently recomputed by coordinator where marked (VERIFIED-INDEPENDENT).

## 1. NEW HONEST CHAMPION CANDIDATE (leverage-compliant) — delivered & VERIFIED-INDEPENDENT
**GOAL100_HONEST_RAWEW13_GEAR16_daily.csv** (13 engines, drop research-only FF2):
- ann_geo **28.89%** | SR_d **3.88** | MaxDD **-4.25%** | **0/19 neg yrs** (worst +10.18%) | n=4805
- Leverage = **exactly 1.6x** (geared EW of sleeve slots), 6.4bps/side on everything, **IBKR-style
  4.5%/yr margin on (gross-1) charged**, borrow 0.5%/yr inside sleeves.
- Coordinator independent recompute: 28.89%/3.88/-4.25/0-neg — EXACT match.
- Trade blotter: BLOTTER_RAWEW14_GEAR16.csv (67,242 records, TRADE_RECORD_STANDARD cols; per-sleeve
  |qty|==charged to 3.7e-9).
- **Dominates** prior honest capped champion (V3 BAL@1.6x+4.5% margin = 16.99/3.63/-3.59) on ann AND
  SR at comparable DD, with FULL margin honesty. This is the honest best at the goal's own 1.6x cap.
- Goal scoreboard vs this candidate: ann80 NO(28.9) | SR5 NO(3.88) | MDD7 YES(-4.25) | lev1.6 YES |
  profit0 YES every yr. Not delivered as THE champion (it is ~16-25% short of the return/SR goals)
  but is the correct construction baseline for any ≤1.6x emission.

## 2. LEVERAGE PATH - THE BINDING CONSTRAINT (AUDIT_LEVFRONTIER, VERIFIED)
- At capital-real ≤1.6x + 4.5% margin + 6.4bps, committed champion ceiling = **16.99-20.05%/yr**
  (not 43.6% which is a free-financing 3.48x gross number).
- **ann_geo ≈ exp(1.6·v·s − costs)** at fill=1.6x, INDEPENDENT of engine COUNT (K cancels): the
  leverage cap fixes ann = fill × SR × vol. SR~3.9 at 10% vol => ~57%; SR~5.2 at 16% vol => ~80-120%.
- **Required NEW-engine bar to reach ann80/SR5/DD7 at 1.6x: ~10 engines at NET SR≥3.9, corr≈0**
  (or ~4 engines at SR≥4.8). Best engine ever found = CFX4 at SR 1.91. So the 5-goal set is
  **infeasible on any on-disk data domain** — nothing has produced even ONE net-SR-3.9 engine.
- corr>0 makes it strictly harder (effective K shrinks).

## 3. TRADE-RECORD INFRASTRUCTURE FIXED (BLOTTER_TESTER found 9 bugs -> BLOTTER_FIXER fixed, VERIFIED)
- **Per-book ledgers** now emitted (BLOTTER_HONEST14V3_SAFE/_AGGRESSIVE/_BALANCED.csv, ~239k rows
  each) with `book` column; each reconciles EXACTLY to its own book turnover; ledger-alone PnL ==
  champion to ~1e-16 (admissibility gate now satisfiable FROM THE LEDGER ALONE, closing the v1 hole).
- Added `borrow_charge` + `cost_total` columns; Σcost_total == charged cost EXACTLY.
- Fixed carryv2 price (now REAL XAU gold 4,567 rows, 711.80-5330.95, not the 189,832 bug);
  honest labels for 2y/10y yields and Brent spread.
- t-1 close execution price (max gap 5e-7); holiday_trade flag added.
- Frozen champion files byte-identical (sha256 unchanged); blotter_v2.py --verify reproducible.
- TRADE_RECORD_STANDARD.md extended to a V2 standard (mandatory book/borrow/cost_total columns +
  from-ledger reconciliation gate).

## 4. NEW-ENGINE SEARCH THIS WAVE — ALL NEGATIVE (5 families confirmed dead)
- HUNT_INDUSTRY48: 48-industry cross-industry relative momentum DEAD (also execution fidelity
  unverified for 45/48 industries).
- HUNT_LIQREV: twelve_liq short-term reversal sign-inverted (confirms EQMOM); best zero-cost SR 0.27.
- HUNT_OVNIGHT: overnight momentum edge is a PAPER TRAP (paper SR 2.14, |corr|0.01, but needs 2
  extra executions/name/day => honest best SR 0.73 / conservative -0.82). No delivery.
- HUNT_CROSSASSET2: sector-basket (near-miss SEC3 fails 8/19 yearly), rates steepener DEAD,
  credit-OAS DEAD.
- (earlier) HUNT_FXDEPO FXD1 near-miss fails yearly gate (8/19 neg); DEX KRW crosses.
DEAD_IDEAS.csv now 42 entries. The only lever left for SR/ann = genuinely new decorrelated engines
NOT on any known data domain (per §2 bar of SR≥3.9, none found in 6 iterations).

## 5. BUGS CAUGHT BY AGENTS THIS WAVE (systematic-debugging, all root-caused)
- HUNT_OVNIGHT: union-calendar Sunday row (2009-07-26) fake overnight; two-stream scramble
  mis-spec; double-execution cost trap (the key one — caught BEFORE delivery).
- HUNT_INDUSTRY48: test double-shift, header parse, wrong missing-code mask, union-index
  vt inflation, effective-lag mislabel. All TDD RED->GREEN.
- HUNT_LIQREV: axis-confusion mask, NaN entry-cost skip (the same class as the committed blotter
  undercharge), vt convention. All RED->GREEN + revert-probes.
- HUNT_CROSSASSET2: scramble-on-net double-cost, duplicate-column aliasing, double-shift. Fixed.
- AUDIT_LEVFRONTIER: arithmetic-vs-geo ann convention, budget-fill clamp bug. Root-caused.
- BLOTTER_FIXER: missing sc throttle factor, cost-rows outside charged window, stale loop var,
  BAL NaN pairwise-mean. All fixed with revert-to-RED proof.

## NEXT STEPS (coordinator)
1. Keep RAW-EW13@1.6x as the honest construction baseline; consider emitting it as THE committed
   champion (replacing the free-financing 3.48x V3 headline) and re-score the board — decision
   requested, since it trades a lower ann for full leverage honesty.
2. Builder-cost re-audit (6.0->6.4bps + gap-convention) still pending — re-emits the *capped* champion
   at ~28.6% (delta ~0.3-0.5pp); must be paired with the v2 ledger.
3. Continue NEW-engine hunt for SR>=3.9 decorrelated engines (bar is 2x the best-ever; low prior).
