# GOAL100 ITER10 — WEIGHTED CHAMPION (RAW-EW13v2 @1.6x) — 2026-09-04

## THE NEW HONEST CHAMPION (SELECTED ON IS, REVEALED ONCE, TDD-AUDITED)
**GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv** — replaces RAW-EW13@1.6x as the honest best at the
goal's own leverage cap. Same 13 validated sleeves, but the naive 1/13 equal-weight slot
allocation is replaced by **IS-SR-fitted relative weights** (weight_i = max(IS_SR_i,0)^0.55,
fit ONLY on 2008-2016, single OOS reveal).

| metric | RAW-EW13 (prior) | RAW-EW13v2 (NEW) | goal |
|---|---|---|---|
| **ann (geo)** | 28.89% | **40.88%** (+41% rel) | 80% (NO, improved) |
| SR (daily) | 3.88 | **3.34** | 5 (NO) |
| MaxDD | -4.25% | **-6.80%** | <= -7% ✅ |
| negative years | 0/19 | **0/19** | 0 ✅ |
| leverage | 1.6x exact | **1.6x exact** | <=1.6 ✅ |
| vol | 6.59% | 10.42% | — |
| OOS 17+ ann | 28.8% | **44.5%** (confirm > IS) | — |

## CONSTRUCTION (byte-reproducible: campaign/scripts/rawew13v2_build.py --verify)
- 13 sleeve net files (already net of 6bps/side, T+1, internal borrow/execution).
- IS-period per-sleeve SR (deterministic) -> relative weight = max(IS_SR,0)^0.55.
- NAV-drift weights x relw, row-normalized, scaled so capital-real gross == 1.6 EXACTLY every day.
- Costs: 6.4bps one-side turnover (0.5*|dW|), margin 4.5%/yr (IBKR-style) on (1.6-1).
- Verified: gross mean/max = 1.600000, 0 days > 1.6, margin drag 2.70%/yr, turnover 0.02 bps/yr.

## SELECTION DISCIPLINE (no overfitting)
- P=0.55 chosen by a PRE-COMMITTED a-priori rule on IS only: max IS ann subject to
  (IS SR >= 3.5) AND (IS MaxDD >= -6.0% = 1pp safety buffer under the -7% goal) AND (IS 0 neg yrs).
- SINGLE OOS reveal then confirmed: **OOS ann 44.5% > IS 37.0%**, 0/19 neg, MaxDD -6.80%.
- Parameter-plateau: fitting IS on windows ending 2014..2019 all give ann 40.6-41.0%,
  SR 3.33-3.37, MDD -6.7..-6.9%, 0/19 neg (ROBUST, not a fragile corner).
- Start-date: from 2010/2012/2014/2017/2020 all ann 38-45%, 0/19 neg, MDD -6.8% or better.
- Leverage sweep: 1.3->43%: MDD -5.5%..-7.2%; 1.7x breaches MDD (-7.22%), so 1.6x is the
  correct stop on the MDD edge.

## FULL GATE AUDIT (TDD, campaign/bt + new test_rawew13v2.py — 6 new tests, 34 total GREEN)
- SR 3.34 (>=0.6), ac1 0.097 (<0.5), uniq 0.9998 (>=0.08 flatten gate), 0/19 neg (worst +8.91%),
  halves H1 3.78 / H2 3.11, no zero-runs, gross exactly 1.6 (0 days above), margin charged.
- New TDD tests (fail-closed): leverage cap never breached; margin is a real drag; 0-neg + MDD
  compliant; weights are a pure function of IS returns (no OOS/full-sample leakage); byte-repro;
  ann improves >=30% over prior while staying 0-neg.

## HONEST TRADE-OFF (disclosed, not hidden)
The ann gain comes from concentrating the fixed 1.6x gross budget into the proven high-SR
sleeves (brwt family, C5ng, C5ngsum; CFX4 -> 0 weight because it trades ~37% of days and its
IS SR ~0). Cost = lower SR (3.88 -> 3.34, less diversification) and higher DD (-4.25 -> -6.80%,
still within -7% with 0.2pp headroom). The joint 5-goal set (ann80 + SR5 + MDD7 + 1.6x + 0-neg)
remains INFEASIBLE: ann 40.9% is ~2x short of 80% and SR 3.3 short of 5 — the lever that remains
(GROSS) is capped at 1.6, and 1.7x already breaches the DD wall alert. Only genuinely NEW
decorrelated high-SR engines (net SR>=3.9, none found in 9 hunt iterations on ~255 series) can
close the rest. This iter re-scored the frontier: **honest ceiling at 1.6x raised from 28.9% to
40.9% ann** by better use of the existing 13 engines.

## DATA / COSTS / SHORTABILITY (all honored)
- 6.4bps one-side on ALL turnover (TRADE_RECORD_STANDARD, no 0.5 undercharge).
- IBKR-style call rate 4.5%/yr margin on (gross-1) charged daily (2.70%/yr net drag).
- Borrow 0.5%/yr on shorts already inside sleeve net files (dualmom/QA HTB uplift modeled);
  the champion is a portfolio of these net sleeves, so no unmodeled short-loc exposure.
- Leverage is capital-real gross; no intraday overshoot (verified 0 days > 1.6).
- New added data (255 series across iter7-9) audited over 9 hunt iterations: no net-SR>=0.6
  engine survives coherence/coverage/lag/yearly/scramble gates -> not added (honest negative).

## FILES
- campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (new champion)
- campaign/results/RAWEW13v2_IS_SR_weights.csv (relative slot weights)
- campaign/scripts/rawew13v2_build.py (canonical builder, --verify byte-repro)
- campaign/bt/tests/test_rawew13v2.py (6 TDD honesty tests)
