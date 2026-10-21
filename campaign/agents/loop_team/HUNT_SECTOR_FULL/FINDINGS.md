# HUNT_SECTOR_FULL — FINDINGS (iter 7.5, 2026-09-03)

**VERDICT: REJECTED — best honest candidate SR08+ = 0.262 (gate 0.60), yearly gate 12/19 neg yrs.
The full SPDR universe does NOT fix SEC3's yearly-gate failure: the failure is INTRINSIC (hardened
negative). Additionally, the SEC3 "0.667 near-miss" was exposed as a cost-undercharge artifact —
under the honest 6.4bps/side FULL-turnover convention it was never 0.667 (exact decomposition below).**

## 1. TDD (superpowers RED->GREEN)
- tests/test_sector_eng.py written FIRST, observed RED: `ModuleNotFoundError: no sector_eng` (collection error).
- Minimal engine (sector_eng.py) written; GREEN 6/6 passed (fresh run: `6 passed in 0.25s`).
- 2 intermediate failures were TEST-fixture bugs (systematic-debugging, root-caused, no engine change):
  (a) Series.name attr mismatch; (b) linear/exp trend fixtures only reached z=1.481/1.486 < cap=1.5,
  plus warmup rows are 0.0 so `w.max()` is 0.0 — fixed fixtures to assert the intended SEC3-family
  property (saturated z pins w_A at exactly -0.5; verified z pins at 1.486 on exp trend with all
  nonzero w == -0.5). Engine semantics match committed sec3_sector_trio.py byte-for-method.
- bt framework regression after all work: `28 passed in 0.06s` (untouched).

## 2. Data premise lint (fail-closed at start)
- more_etf: XLK,XLY,XLP,XLU,XLV,KBE,KRE,ITB,XHB,SMH,IGV,XME each 5000 rows, 2006-10-17 -> 2026-09-02,
  manifest status OK; XLB,XLF,XLI from twelvedata 2006-09-26 -> 2026-08-12, 5000 rows each. All REAL
  closes, no dup idx, closes>0. Eval 2008+ => n=4682-4697 rows. price_source=REAL for all trades.
- Cross-validation: corr(XLK r, 0.5*AAPL+0.5*MSFT r)=0.8592 (n=4984); XLV vs JNJ/UNH 0.7684;
  XLY vs AMZN/HD 0.8205 — plausible for cap-weighted sector ETFs (not constituent clones, as expected).
- 54 XLK zero-ret rows spread 2006-2026 (54/5000=1.1%, no year clustering) — same vendor quirk class
  as manifest zero_ret_rows=54; levels plausible (XLK ann vol 23.3%, 2020-03 ann vol 103.7%).

## 3. Champion baselines (fresh, this session)
- V3 BALANCED: n=4696, 2008-09-01..2026-08-28, SR08+ = 6.363.
- RAW-EW13@1.6x: n=4805, 2008-03-31..2026-08-27, SR08+ = 3.884; corr(V3,EW13)=0.5435.

## 4. Screen (charter step 1) — honest costs 6.4bps/side FULL turnover + borrow 0.5%/yr, T+1
- EW over ALL 105 pairs, cap 1.5: lb10 SR08+ = -0.684; lb15 = -0.555; lb21 = -0.503; lb63 = -0.266.
  cap sweep changes nothing materially (lb15: cap2.0 -0.576, cap2.5 -0.602, cap3.0 -0.633). ALL NEGATIVE.
- Best single PAIR (own best lb of 10/15/21/63): XLB/SMH SR08+ = 0.342 (lb21); then XLF/XLI 0.312 (lb15),
  KBE/XHB 0.263, XLB/XLF 0.261, KRE/XHB 0.222. Across 420 variants (105 pairs x 4 lb): ZERO >= 0.60;
  4 >= 0.30; 77 >= 0.
- Best TRIO: SEC3 (XLB/XLF/XLI) lb21 cap1.5 SR08+ = 0.221 — #1 of 56 trios (8 majors), next best
  (XLB,XLF,XLY) lb21 = 0.115.
- Best QUARTET (lb15): (XLB,XLF,XLI,XLY) = -0.048; all 70 quartets NEGATIVE.
- SEC3 27-book EW (3 pairs x lb{10,15,21} x cap{1.5,2,3}): SR08+ = 0.102 (cap1.0-only variant: 0.150).
- Curated TOP-5 pairs EW (own lb): SR08+ = 0.440, 8/19 neg yrs, worst -8.81% — still below SR gate 0.60
  and fails yearly gate (gate: <=2 neg).

## 5. ROOT CAUSE of the SEC3 "0.667" vs honest 0.179 gap (systematic-debugging)
Exact replication of original sec3_sector_trio.py on original twelvedata data reproduces SR08+ = 0.667
byte-level method match. Decomposition per pair (2008+, lb15 cap1.5):

| pair    | gross SR | 6.0bps HALF-turn SR | 6.4bps FULL one-side SR | one-side turnover/day |
|---------|----------|---------------------|-------------------------|-----------------------|
| XLB/XLF | 0.828    | 0.554               | 0.244                   | 0.323 (81x/yr)        |
| XLB/XLI | 0.737    | 0.278               | -0.239                  | 0.316 (80x/yr)        |
| XLF/XLI | 0.988    | 0.683               | 0.338                   | 0.324 (82x/yr)        |

The original charged 6.0bps on (|dw|/2) = **3.0bps per one-side unit — a 2.13x undercharge** of the
TRADE_RECORD_STANDARD 6.4bps/side. At 80x/yr turnover the cost drag is ~0.77 of gross vol; the
champion cost convention (bt.cost_turnover: full |dw| at 6.4bps, A1-fixed) cuts the trio from
gross SR 1.047-1.134 to net 0.179-0.262. **Gross edge was real but small; net edge was never close.**

## 6. Best honest candidate: SEC3 trio lb21 cap1.0 (SR gate battery — all numbers)
SR08+ = 0.262 (FAIL >= 0.60) | ann_geo +1.37% | vol 5.85% | maxDD -30.25% |
H1 = 0.575 PASS / H2 = -0.283 FAIL (>= 0.30) | neg yrs 12/19 FAIL (<=2), worst -5.04% (floor -5% FAIL) |
ac1 = -0.0564 PASS (< 0.5) | uniqR = 1.0000 PASS (>= 0.08) |
corr to V3 = -0.0175 PASS (|.|<0.15); corr to EW13 = +0.0315 PASS |
position-lag scramble FULLY RE-COSTED: p = 0.000 (200 draws x seeds {0,1,2}, block 10) PASS —
the book is genuinely anti-predictive, not an artifact; it is just too weak and too dead-after-2016.
Yearly: 2008 +37.74, 2009 +15.35, 2010 +3.12, 2011 +4.81, 2012 -1.46, 2013 -4.55, 2014 -1.83,
2015 -2.77, 2016 -4.94, 2017 -1.59, 2018 +1.48, 2019 -2.27, 2020 +2.47, 2021 -4.81, 2022 -3.70,
2023 -1.87, 2024 -5.04, 2025 +2.88, 2026 -0.15 (%). SR 2017+ = -0.328 (lb15 variant: -0.455).
Original-params trio (lb15 cap1.5): SR08+ = 0.179, H1 0.499 / H2 -0.392, 11/19 neg, 2017+ -0.455.

## 7. Charter Q3 ANSWER: yearly-gate failure is INTRINSIC
- Every universe expansion makes it WORSE: trio 0.221 -> quartets -0.048 -> all-105 EW -0.503..-0.555.
- The z-reversion edge is a 2008-2016 crisis/JPY-carry-unwind-era phenomenon concentrated in the
  XLB/XLF/XLI triangle; 8/19 neg (original claim) was OPTIMISTIC — honest costs give 11-12/19 neg.
- Unlike FXD1/HUNT_FXDEPO (KRW crosses), here even the SIGN survives scramble p=0.000 — the family is
  statistically real but economically dead at honest costs. Hardened negative, same verdict class.

## 8. Champion-integration test (charter step 2)
- corr gates to both champions PASS (see §6).
- Blend EW13: 0.95*EW13 + 0.05*sec3_lb21cap10: SR08+ = 3.893 vs 3.884 alone (+0.009), 0 neg yrs
  preserved, worst yr +9.19%. At w=0.10: SR08+ = 3.885 (-0.000 vs alone), 0 neg. => No material lift;
  max improvement +0.009 SR at w=0.05 << the campaign's materiality bar; NOT pursued (lev stays <=1.6
  by construction). Adding to V3 pointless: corr -0.02 but sec3 net SR 0.262 contributes ~nothing.

## 9. Deliverables (provenance)
- Engine: campaign/agents/loop_team/HUNT_SECTOR_FULL/sector_eng.py (TDD, uses bt semantics)
- Tests: campaign/agents/loop_team/HUNT_SECTOR_FULL/tests/test_sector_eng.py (6/6 GREEN)
- Series: sleeves/SECTOR_FULL_trio_lb21_cap10_honest_daily.csv (n=4682, 2008+, SR 0.262) — DISCLOSED
  as hardened-negative evidence, NOT champion-eligible (FXD1 precedent).
- Ledger: sleeves/SECTOR_FULL_trio_lb21_cap10_ledger.csv — 10,886 records, columns
  date,sleeve,instrument,side,price,price_source,qty_notional,weight_from,weight_to,cost_bps.
  Reconciliation: sum|qty_notional| = 3990.767003 == charged turnover 3990.767003 (rel diff 1.1e-16).
  instrument = twelvedata/{XLB,XLF,XLI}.csv, price_source = REAL (REAL market closes).
- DEAD_IDEAS.csv updated (2 rows).

## 10. Explicitly excluded per charter: XLE/XOP (oil — redundant with champion brent/WTI sleeve).

HUNT_SECTOR_FULL DONE
