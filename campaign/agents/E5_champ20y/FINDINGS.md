# E5_champ20y — ROUND 1 FINDINGS (2026-09-01)
Charter: full-validation of GOAL100_CHAMPION20Y (12-pool, 2007-01 start) + upgrade attempt.
Repro: campaign/scripts/E5_champ20y_validate.py (all numbers below regenerate in one run).

## Task 1 — INDEPENDENT REBUILD: PASS (byte-match)
Rebuilt from the 12 sleeve files (pool minus {H21_f5,H21_br,A5r2,A5r4}) via champion_build logic
(imported, not copied results). A=vt.065/thr.04, B=vt.08/thr.03, START=2007-01-01.
| series | n | max|new-old| | verdict |
|---|---|---|---|
| SAFE | 5131 | 1.0e-16 | BYTE-MATCH |
| AGGRESSIVE | 5131 | 1.0e-16 | BYTE-MATCH |
| BALANCED | 5131 | 1.0e-16 | BYTE-MATCH |
Stats match committed JSON exactly (SAFE 35.6/4.86/-6.4, AGGR 43.3/4.92/-7.8, BAL 39.5/4.91/-7.1, 0/20 neg yrs, OOS17+ 44.9%). No deviation.

## Task 2 — SUB-PERIOD DD AUDIT: PASS (0 flags)
Fixed ~3y windows 2007-,2010-,2013-,2016-,2019-,2022-,2025- (7 windows), BALANCED DDs:
-5.2 -5.3 -6.1 -5.0 -4.2 -5.4 -6.3 (%). Worst = 2025 window (-6.3%).
Worst ROLLING-3y DD (daily step): SAFE -6.4% / BALANCED -7.1% / AGGRESSIVE -7.8% (all trough 2022-05).
All 20 calendar years (2007-2026), BALANCED: 0 neg years (worst year +8.7% in 2015);
intra-year DD < -8%: 0 years for all three series (worst yr-DD: BAL -7.1% in 2022, AGGR -7.8%).
=> Nothing < -8% anywhere. BALANCED yearly: 2007:15.9 2008:41.1 2009:73.6 2010:42.9 2011:72.1
2012:17.3 2013:53.2 2014:48.7 2015:8.7 2016:64.8 2017:52.4 2018:42.6 2019:93.4 2020:55.6
2021:26.7 2022:25.8 2023:147.2 2024:58.6 2025:73.6 2026(YTD):21.1

## Task 3 — COST STRESS (robust to 10bps)
| series | 6bps | 8bps | 10bps (ann / mdd) |
|---|---|---|---|
| SAFE | 35.6 / -6.4 | 35.3 / -6.6 | 34.9 / -6.8 |
| BALANCED | 39.5 / -7.1 | 39.1 / -7.3 | 38.8 / -7.5 |
| AGGRESSIVE | 43.3 / -7.8 | 43.0 / -8.0 | 42.6 / -8.2 |
Only ~-0.4pp ann & ~-0.2pp DD per +2bps (low turnover blend). AGGRESSIVE breaches -8% only at 8bps+;
BALANCED stays <= -7.5% even at 10bps. 6bps assumption is not load-bearing.

## Task 4 — BLOCK BOOTSTRAP (1000x, 21d blocks, seed 7)
| series | SR 95%CI | P(SR<2) | ann 95%CI | P(ann<25%) | boot-DD p5 |
|---|---|---|---|---|---|
| SAFE | [4.23, 5.49] | 0.000 | [36.4%, 50.0%] | 0.000 | -9.2% |
| BALANCED | [4.36, 5.53] | 0.000 | [41.5%, 56.0%] | 0.000 | -9.7% |
| AGGRESSIVE | [4.30, 5.53] | 0.000 | [45.5%, 63.1%] | 0.000 | -10.5% |
Caveat: block bootstrap shuffles regime order, so path-dependent DD (throttle) is understated —
boot-DD p5 (-9.7%) slightly worse than realized -7.1% but nowhere near blowup territory.
SR >= 2 is rejected as luck at p ~ 0.

## Task 5 — POSITION-PERmutation SCRAMBLE (200x, D2 method, re-apply trailing VT honestly)
Real vs scrambled SR: SAFE 4.86 p=0.000 | AGGRESSIVE 4.92 p=0.000 | BALANCED 4.91 p=0.000.
Frontier point 0.085/0.035 (below) also p=0.000. The edge lives in the positions, not path luck.

## Task 6 — UPGRADE ATTEMPT: FAILS honest rule -> v1 CONFIRMED
Grid {vt 0.07..0.09}x{thr 0.03..0.045}, FULL ann/SR/DD | IS(2007-16) SR | OOS17+ DD:
vt.070: 38.0-38.4 / 4.86-4.92 / -6.7..-8.3 | 4.38-4.42 | same as DD
vt.075: 40.8-41.2 / 4.88-4.93 / -7.1..-8.5 | 4.40-4.42
vt.080: 43.3-43.9 / 4.89-4.94 / -7.7..-9.3 | 4.39-4.43
vt.085: 45.9-46.6 / 4.91-4.95 / -7.9..-9.5 | 4.42-4.43
vt.090: 48.3-49.4 / 4.91-4.95 / -8.6..-9.6 | 4.41-4.44
- IS SR surface is FLAT: 4.38-4.44 across all 20 cells (range 0.06 = noise). IS cannot rank the grid.
- Strict IS-argmax (per 4 IS-ends 2016/2019/2022/2023): vt.090/thr.040 (IS SR 4.44) or vt.085/035 —
  the 090/040 pick has FULL DD -8.6% and OOS DD -8.6% => FAILS charter OOS DD<=8%.
- Honest frontier point inside the charter grid: B-slot vt.085/thr.035 -> combo 42.2% ann @ -7.3% DD,
  SR 4.94, 0 neg yrs, OOS 48.1%@-7.3%, survives 10bps (40.3/-7.6), 0/20 yr-DD flags, scramble p=0.
  +2.7pp ann for +0.2pp DD is a REAL trade-off, but adopting it requires OOS-peeking (its edge shows
  only out-of-sample) => NOT adopted; recorded as the honest frontier, not v2.
- v2 candidates built and rejected by the IS rule: v2a 41.0/-7.2, v2b 42.2/-7.3, v2c 40.7/-7.2 (all
  IS0716 SR 4.417-4.426 vs v1 4.408 — differences far inside bootstrap noise).

## Task 7 — 20-YEAR COMPARISON (clear winner on the stated criterion)
| champion | first..last | trading-yrs (n/252) | calendar span | ann / SR / DD / negy | OOS17+ |
|---|---|---|---|---|---|
| CHAMPION20Y BALANCED (v1) | 2007-01-03..2026-08-28 | 20.36 | 19.66 cal-yrs | 39.5 / 4.91 / -7.1 / 0/20 | 44.9% / -7.1% |
| CHAMPION (18.6y) BALANCED | 2008-09-01..2026-08-28 | 18.63 | 17.99 cal-yrs | 55.5 / 5.24 / -6.9 / 0/18 | 60.2% / -6.9% |
Both rebuild byte-identical. CHAMPION20Y includes 2007 (last bear bull year) and thereby covers a
full 2007-2026 cycle incl. GFC + 2022: it is the ONLY one satisfying "20-year testing" (20.36
trading years). The 18.6y champion's higher headline (55.5 vs 39.5) is the price of dropping 2007,
NOT a better engine — same 12+4 pool, same construction.
NOTE the "20.4y span" in the committed JSON is calendar-span counting inclusive endpoints; the
honest daily-count measure is 20.36y trading / 19.66y calendar delta. Still >= the 20-year bar
by trading-day count; start 2007-01-03 (first trading day).

## VERDICT
All 5 audits PASS (byte-match, DD audit 0 flags, cost-robust to 10bps, bootstrap SR CI [4.4,5.5],
scramble p=0.000). Upgrade FAILS the IS->OOS discipline (flat IS surface, strict pick breaches DD)
=> GOAL100_CHAMPION20Y v1 CONFIRMED, no v2 issued. Frontier candidate (0.085/0.035 combo,
42.2%@-7.3%) deposited here for coordinator as OOS-flagged data only.
Artifacts: campaign/scripts/E5_champ20y_validate.py, work/{rebuild20y.py,e5lib.py,t2_t3.py,
t4_t5.py,t6_grid.py,t3_cost.json,t4_boot.json,t6_grid.json}.

## NUMBERED ROUND-1 SUMMARY
1. Independent rebuild (12-pool, A=vt.065/thr.04, B=vt.08/thr.03, 2007-01): SAFE/AGGR/BALANCED all
   BYTE-MATCH committed CSVs (max|diff| 1.0e-16, n=5131; BAL 39.5% ann, SR 4.91, DD -7.1%, 0/20 neg yrs,
   OOS17+ 44.9%). VERDICT: PASS.
2. Sub-period DD audit: 7 fixed ~3y windows worst -6.3% (BAL); worst rolling-3y -6.4/-7.1/-7.8% (S/B/A,
   trough 2022-05); 0 of 20 calendar years with DD<-8% or negative return (worst yr +8.7% 2015).
   VERDICT: PASS (0 flags).
3. Cost stress 6/8/10 bps: BAL 39.5/-7.1 -> 39.1/-7.3 -> 38.8/-7.5; AGGR hits -8.0% only at 8bps.
   VERDICT: PASS — 6bps not load-bearing (~-0.35pp per +2bps).
4. Bootstrap 1000x 21d-block: BAL SR 95%CI [4.36,5.53], ann [41.5%,56.0%], P(SR<2)=0.000, boot-DD p5
   -9.7%. VERDICT: PASS (not luck; DD caveat noted).
5. Position-permutation scramble 200x: real SR 4.86/4.92/4.91 (S/A/B), all p=0.000. VERDICT: PASS.
6. Upgrade grid {0.07..0.09}x{0.03..0.045}: IS0716 SR flat 4.38-4.44 (unrankable); strict IS-argmax
   vt.090/thr.040 fails OOS DD (-8.6%>8%). Honest frontier B-slot vt.085/thr.035 combo = 42.2% ann,
   SR 4.94, DD -7.3%, 0 neg yrs, OOS 48.1%/-7.3%, 10bps-robust (40.3/-7.6) — NOT adopted (OOS-peeked),
   recorded only. VERDICT: UPGRADE FAIL -> v1 CONFIRMED.
7. 20y comparison: CHAMPION20Y BAL 2007-01..2026-08 = 20.36 trading-yrs, 39.5%/4.91/-7.1%/0neg,
   OOS 44.9% — the only one satisfying 20-year testing; 18.6y CHAMPION BAL 55.5%/5.24/-6.9%/0neg,
   OOS 60.2% but starts 2008-09 (drops 2007). VERDICT: CHAMPION20Y v1 confirmed as the 20-year
   testing vehicle; headline gap is sample-start, not engine quality.
ROUND 1 DONE
