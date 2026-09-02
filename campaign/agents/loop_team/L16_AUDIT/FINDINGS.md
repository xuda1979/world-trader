# L16_AUDIT — adversarial re-audit of GOAL100_HONEST11L16_BALANCED (2026-09-02)

Auditor: loop_team/L16_AUDIT. Read-only on campaign; all scratch under
`campaign/agents/loop_team/L16_AUDIT/scratch/` (audit_a/b, diag2-7, leverage, ablation,
x804_check, calendar_*, brwt_*, missing_costs, lookahead_corr, outliers, lev_conv).

## 1. PROVENANCE & BYTE REPRODUCTION — VERIFIED (after recovering an UNCOMMITTED recipe)
- Committed CSVs are unmodified since commit 63da4bd: `git show 63da4bd:...` sha256 ==
  working-tree sha256 for all three L16 files (BAL 6568994c…, SAFE 6a9de136…, AGGR 85ff2327…).
- I rebuilt the champion from the 11 sleeve CSVs. The frozen `campaign/scripts/honest11_build.py`
  (Sn at per-sleeve target 0.10, TGT 0.07/0.091) does NOT match L16 (max|diff| 4.8e-05 vs SAFE).
  **Exact match (max|diff| = 1.0e-16 on all three files) requires per-sleeve vt target 0.08 applied
  to BOTH the return scaling AND the Sn scale book (cap weights, turnover, borrow).**
- GAP: no L16 builder is committed anywhere (LOOP_L16/ has only FINDINGS.md). The recipe above is
  my recovery; it reproduces byte-exactly, so provenance is re-established, but the frozen builder
  on disk does not build the current champion. Recommend committing an `honest11l16_build.py`.

## 2. HEADLINE STATS — VERIFIED INDEPENDENTLY (my own code, n=4522, 2008-03-31..2026-07-31)
- BAL: ann(geo) 47.55% | SR_d 4.177 | SR_m 4.173 | MaxDD -4.85% (worst 3y-subwindow also -4.85%)
  | OOS17+ ann 43.9% SR 4.35. Matches FINDINGS' 47.6/4.18/4.17/-4.85/43.9.
- SAFE: 40.79% / 4.182 / 4.271 / -4.27%. AGGR: 54.62% / 4.165 / 4.091 / -5.59%.
- BAL == (SAFE+AGGR)/2 exactly (max|diff| 7.5e-17). Internally consistent.
- **0-neg-year claim: CONFIRMED.** 0/19 negative calendar years, worst year 2011 +15.28%.

## 3. FLATTENING / LOOKAHEAD / CALENDAR / MECHANICAL — PASS on the blend
- 4522/4522 distinct return values (uniqR=1.0000); ac1 = -0.074; no zero runs; no weekend,
  no US-federal-holiday, no Good Friday rows. Max |daily| = +14.40% (2020-09-01; see §6).
- No lookahead: corr(BAL_t, sleeve-contrib_{t+1}) = -0.032, {t+2} = +0.001 (vs +0.399 contemporaneous).
  All vt/throttle layers use shift(1) trailing stats (verified in code).
- T+1 robustness probe (all sleeve returns shifted +1 extra day): ann 47.5% SR_d 4.16 — virtually
  unchanged; consistent with genuinely slow signals, not an execution-timing artifact.
- All 11 sleeves pass the flatten gates (uniqR>=0.08, ac1<0.5; SR 2008+ all >=0.6; XGB1y absent).

## 4. LEVERAGE 1.59x — VERIFIED **AS A FULL-SAMPLE MEAN UNDER THE PUBLISHED DEFINITION ONLY**
Published def (EW of per-sleeve |vt scale| x throttle), BAL 2008+: **mean 1.595x**, median 1.531x,
p95 2.554x, max 3.346x (single-config max 4.704x — matches FINDINGS' "max 4.70x spike").
- BUT: **44.7% of days (2020/4522) exceed 1.6x; 20.8% exceed 2.0x; yearly-mean gross exceeds 1.6
  in 7/19 yrs** (2021 1.974, 2022 2.360, 2023 2.415, 2018 1.921, 2013 1.821, 2012 1.705, 2014 1.696).
- Conservative all-in (x global vt scalar): BAL **mean 3.43x, p95 7.0x, max 10.6x** — consistent
  with LOOP_L16's own "~3.3x" sensitivity note. Financing at 4.75% on (pub-def gross - 1): ann
  43.3%, SR_d 3.87, MDD -5.19%, still 0 neg. On full all-in gross: ann 36.8%, SR_d 3.37, MDD
  -5.71%, 0 neg, worst yr +7.5%.
- **DEFINITION HOLE (material):** the published definition excludes the global vol-target scalar,
  so it is INVARIANT to the global dial. Rebuilding the identical pool at TGT 0.11/0.14 (per-sleeve
  still 0.08) yields ann 75.7%, SR 4.21-4.27, MDD -6.92%, 0 neg — with pub-def leverage STILL
  1.595x mean. I.e. **"leverage<=1.6 mean" under this definition does not constrain Ann at all**;
  the real (capital-real) gross of that 75.7% variant is 4.85x mean / 18.7x max. The L16
  "infeasible at <=1.6" verdict is only true under a capital-real definition; under the campaign's
  own published definition it would be trivially circumventable. Constraint must be restated in
  capital-real terms to bind.

## 5. CALENDAR = INNER JOIN — 57 weekdays dropped, mild adverse selection (NEW, minor-material)
- Output rows are the intersection of the 9 borrow-bearing sleeves' calendars (borrow term is NaN
  when any of them lacks a row). 75 blend-index weekdays >=2008-03-31 are missing from the CSV:
  18 Good Fridays (NYSE closed — correct) + **57 genuine trading days** (Easter/UK bank holidays,
  Hurricane Sandy 2012-10-29/30, mourning closes 2018-12-05 & 2025-01-09, July-3 and Christmas-Eve
  sessions, etc.) where SOME sleeves have real P&L that is silently discarded.
- Dropped days are adverse-selected: blend mean +4.94bp on the 94 dropped in-window days vs +7.60bp
  overall — dropping below-average positive days inflates the average.
- Rows-kept rebuild (P&L kept from sleeves present; borrow charged only on sleeves present):
  in-window ann 47.0% (vs 47.55), SR_d 4.12, SR_m 4.17, **MaxDD -5.53% (vs -4.85)**, **0 neg years,
  worst +16.2%**. Verdict: claims survive the fix (0/19 stands; DD headroom to 7% shrinks ~0.7pp),
  but the committed -4.85% is mildly flattered by the join.

## 6. ZERO-GATED brwt FAMILY — by design, but risk understated; harness check is BROKEN (NEW)
- E1_brwt_spread_rev15_2000: **66.8% of rows are exactly 0.0**; 349 zero-runs >=5d, 19 runs >=20d,
  longest 33d. brwt10 38.0%, brwt7 37.3%, brwt5 36.5% zeros; C5ngsum 53.8%; C5ng 22.8%.
- Verified from the committed generator (`scripts/backtest_brwt_spread_rev15.py`): position is
  flat unless |z|>1.5 — zeros are genuine gate-off days, NOT artificial flattening. However the
  8% vol target applies to a zero-inflated series, so active-day vol is ~1.7x stated (brwt15
  active-day SR 4.14 vs 2.37 all-day). Consequence: 2020-09-01 the four brwt books (mutual corr
  0.66-0.86; effectively ONE engine family, 4/11 of the pool) contributed +1563/+787/+918/+598bp
  -> blend day +14.40% = **24.3 sigma**. Symmetric -14% days are possible; single-day tail risk is
  understated by the -4.85% MaxDD figure.
- **BUG in campaign/audit_harness.py:** the interior-zero-run check (`z & ~z.shift(1).fillna(False)`)
  promotes bool->object; `~` yields -1/-2 and every run collapses to length 1 — it reports zRuns=0
  for brwt15 despite 19 runs >=20d (bool-safe rerun: max run 33). The zRuns column has been
  silently vacuous for every audit that used it.

## 7. COSTS — 6bps/side charged on weight turnover (0.39%/yr); vt-overlay rebalance NOT charged
- Sleeve-scale overlay turns over 2.80%/day one-side, global scalar 3.36%/day; at 6bps that is
  **~0.93%/yr mean** (p95 3.65%/yr) of uncharged rebalance cost (same convention caveat as
  STRICTAUDIT_EXECUTION §7). Charging it: ann 46.2%, SR_d 4.08, MDD -5.02%, still 0 neg.
- Borrow charged at 0.5%/yr (1.1% dualmom) on short-flag x scale/N — flags are conservative
  (dualmom has no shorts per STRICTAUDIT_EXECUTION). No rebate credited. OK/conservative.

## 8. X804 ("80.5% at ~2.5-3x") — committed STATS verify, builder does NOT, leverage unclear
- Committed GOAL100_HONEST11X804_* re-measured: BAL 80.5% ann, SR_d 4.22, 0 neg yrs, worst +21.5%,
  MDD -6.73% — matches LOOP_SR_LEVERAGE. SAFE 70.2%, AGGR 91.4%.
- **UNVERIFIED construction:** no builder exists for X804; my best reconstructions give 72.1-75.7%
  ann, max|diff| vs committed 2.7e-02 (not a match). Loop-Leverage's "approx gross ~2.5x" at
  0.11/0.14 matches NEITHER my pub-def (1.91x at per-slv 0.10) NOR my all-in (4.55-5.15x mean,
  max 13-19x) — provenance UNVERIFIED. Honest capital-real gross of X804 is ~4.6-5.2x, not ~2.5x.
- Concentration note: leave-one-out (BAL) — dropping carryv2 is the only large hit (ann 39.4%,
  SR_m 3.29); all others 45.1-47.3% ann. No single-sleeve dependency beyond carryv2 (0/19 neg
  preserved in every ablation).

## 9. VERDICT on HONEST11-L16 champion
Honest as built: no flattening, no lookahead, T+1 robust, costs+borrow charged, 0/19 neg years
CONFIRMED, stats reproduce byte-exactly. Caveats that must accompany any external claim:
(a) leverage "1.59x" is a MEAN under a definition that excludes the global scalar and ignores
    44.7% of days >1.6x; capital-real gross is ~3.4x mean;
(b) calendar inner-join flatters ann ~+0.5pp and MaxDD ~+0.7pp (fixed: 47.0%, -5.53%, still 0/19);
(c) single-day tail (+/-14% gate-on days) is understated by DD-based gates;
(d) uncharged vt-rebalance cost ~0.9%/yr (fixed: 46.2% ann);
(e) the 5-goal set (Ann>=80, SR>=5, DD<=7, lev<=1.6, prof>=0) remains INFEASIBLE — and under the
    current published leverage definition it would be trivially circumventable at ~76% ann;
    the binding statement must use capital-real gross.
UNVERIFIED items: X804 builder/leverage; C5ng print-timing (inherits prior open item); Good-Friday
+federal calendar assumed = NYSE (no exchange-holiday file checked).
L16_AUDIT DONE
