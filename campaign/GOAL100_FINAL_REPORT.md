# GOAL100 CAMPAIGN — FINAL HONEST REPORT (2026-09-01)
## Goal: 20y backtest, ann>=100%, SR>=2, MaxDD<=8%, NO leverage, 6bps/side, free data, OOS mandatory.

---

## 1. EXECUTIVE VERDICT

| Metric | Requirement | Delivered (BEST HONEST) | Status |
|---|---|---|---|
| Annual Sharpe | >= 2.0 | **5.2 daily / 3.6 monthly** (bootstrap CI [3.1, 4.1]) | **EXCEEDED (2.6x)** |
| MaxDD | <= 8% | **-6.9%..-7.9%** (every calendar year <= -7.0%) | **PASS** |
| No leverage | weights sum 1 | EW-of-vol-normalized, caps enforced | **PASS** |
| Costs | 6bps/side embedded | yes, incl. throttle switching | **PASS** |
| OOS | mandatory | IS 2008-16 selection -> OOS 2017-26 revealed once | **PASS** |
| 20y test | 2006/08-2026 | 18.6y (2008-09..2026-08; sleeve starts cap it) | 93% of 20y |
| Annual return | >= 100% | **55.5% (balanced) / 62.4% (aggressive, DD -7.9%)** | **NOT MET — 1.8x short** |

**Bottom line:** The 6-agent campaign raised the honest no-leverage frontier from 43.2% (GOAL80)
to **~55-62% ann @ MaxDD<=8%** via two new genuinely-decorrelated engine families (natgas
cash-market calendar economics; plus construction headroom discovered by C4). SR>=2 and
MaxDD<=8% are satisfied with huge margin. The 100% ann leg remains **physically out of reach
on free daily data at 6bps**: it needs either ~2x more decorrelated SR>=2 engines than exist
in any free-data domain we could find, or DD/return ratio ~0.08-0.10 (best real: ~0.11 here
vs ~0.17-0.33 for typical systems; intraday tick-data firms: ~0.15-0.20).

---

## 2. THE 6-AGENT CAMPAIGN (14 agent-rounds total, dynamic re-chartering after each round)

| Agent | Rounds | New engines saved | Key honest findings |
|---|---|---|---|
| **C1_kfindustry** | 3 | 0 | KF daily portfolios (48/49 ind, 25ff, ME/OP/INV deciles, 1926+): ~210 configs tested; static mom/rev/vol-sort/dispersion/SMB/factor-mom ALL dead post-2008 (net SR<=0.35); short side of every winner-book is the loss source; domain CLOSED. |
| **C2_ratescurve** | 3 | 0 (1 quarantined) | Fly reversion GROSS edge is real (flyC SR 1.75, p=0.000) but 1-3%/yr gross vs 7-13%/yr costs at 6bps — economics impossible. Round-2 **found its own round-1 units bug** (pct-pt vs decimal costs, 100x understatement) and QUARANTINED C2_fly2AB_75 (honest net SR -2.04). Always-on steepener carry (SR 1.33, corr -0.05) fails yearly-DD gate (2011/2014 bull-flattening -15%). Rates domain CLOSED at 6bps. |
| **C3_positioning** | 1 | 0 | COT/TFF positioning: 0/7 charter ideas (~450 variants); **found+fixed a 1-day lookahead bug in its own harness** (SR 3.18 -> -0.26 after fix). Intraday overnight: negative. Domain exhausted. |
| **C4_metaalloc** | 2 | **1 construction** | **C4_construct_v2**: vt .11 + 126d DD-throttle thr .03 — coordinator-audited: every calendar year DD <= 7.0%, OOS 60.5% @ -7.8%. Discovered GOAL80's vt=8 "wall" was a lookahead artifact + wrong throttle horizon. |
| **C5_newdata** | 3 | **3 sleeves** | **Natgas weekday family (THE find of GOAL100)**: Fri->Mon weekend premium + Wed/Thu storage-report short (SR 2.19 summer / ~1.0 all-year; per-year SR all positive 2008-26; calendar-scramble p=0.015; corr to blend -0.01; economic rationale: EIA storage season hedging flows). Exhaustively proved: no oil/gold/FX/propane weekday analog exists (604-test multiple-testing-controlled scan). |
| **C6_mlmulti** | 2 | 0 | ML on curve/KF/positioning/FX domains: NO daily directional edge (raw SR<=0.3); meta-ML loses to plain EW OOS; ML gates degrade baselines. Honest negative. |

Coordinator (me) ran in parallel: spread sweep across 19 economically-linked pairs (only brent/wti
passes; corr 0.76 to brwt = same trade), crack spreads (DD too deep), level reversion (dead),
EM-FX/broad-dollar (dead), KF OP/INV spread momentum (**caught my own T+1 lookahead**: SR 2.8 ->
0.1 with proper shift), NFCI books (param spikes), equity calendars (dead), accruals/gross-margin
PIT books (dead), steepener carry (fails DD envelope), credit/bond2y sleeve re-audits (clean).

## 3. FINAL CHAMPION SYSTEMS (all 16 sleeves, EW-of-vt10, 126d DD-throttle, 6bps, no leverage)

Pool: 14 GOAL80 sleeves + C5_ng_weekday_prem + C5_ng_summer_weekday. Files in campaign/results/.

| Variant | vt / throttle | ann | SR(d) | SR(m) | MaxDD | OOS17+ ann/DD | Neg yrs |
|---|---|---|---|---|---|---|---|
| **CHAMPION_BALANCED** | 50-50 avg of A/B | **55.5%** | 5.24 | ~3.6 | **-6.9%** | 60.2% / -6.9% | 0/19 |
| CHAMPION (A, safe) | vt .085 thr .04 | 48.5% | 5.18 | | -7.3% | 52.5% / -7.3% | 0/19 |
| CHAMPION_AGGRESSIVE (B=C4_v2) | vt .11 thr .03 | **62.4%** | 5.27 | | -7.9% | 67.8% / -7.9% | 0/19 |

Robustness (balanced): leave-one-year-out ann 45.5-50.0%; 5y-subwindow CAGRs 53.4/53.4/73.1/64.3%;
worst calendar-year DD -7.0% (2025), worst year +7.9% (2026 partial), best 163% (2023).
Keystone: XGB1y (drop => -10pp); brwt +3.5pp; natgas sleeves +7.7pp combined vs GOAL80 pool.

## 4. WHY 100% @ MaxDD<=8% NO-LEVERAGE REMAINS UNREACHABLE (updated math)

- Best systems run SR~5.2 daily at vt 11% vol. 100% ann needs vol ~19% at that SR.
- Pooled MaxDD/vol ratio floor measured across ALL constructions this session: ~0.62-0.88
  (throttle helps but floors at ~0.62). At 19% vol => MaxDD ~11.8-16.7%: 1.5-2x over the 8% cap.
- Needed: DD/return ~0.08. Best real-world stat-arb (tick-data, co-located, sub-bp costs): ~0.15-0.20.
  Free daily OHLCV + 6bps is strictly harder (proven again by C2's cost-vs-edge analysis and C3's
  positioning nulls).
- Engine inventory is the binding constraint: the frontier moves ONLY with new decorrelated
  SR>=1.5 engines. GOAL100's 14 rounds found exactly one new family (natgas calendar, +7.7pp
  blended). Every other free-data domain is now honestly CLOSED: KF portfolios (C1), rates/curve
  (C2), COT positioning (C3), crack/level/EM-FX/NFCI/equity-calendar/accrual spreads (coordinator),
  ML directional on free daily data (C6).
- Reaching 100% honestly would need ~10-15 more natgas-quality decorrelated engines. No free
  daily data source we could access (STOOQ blocked, FRED-only universe mapped) contains them.

## 5. HONESTY INFRASTRUCTURE IMPROVEMENTS THIS SESSION
1. **gates.py scramble_pval proven degenerate** (return-permutation preserves mean/std => p~1.0).
   Replaced by signal-permutation and calendar-scramble (circular input shifts) in audits.
2. **T+1 shift discipline**: demonstrated that omitting shift(1) inflates SR by 1.5-2.5x
   (KF OP/INV momentum SR 2.8 -> 0.1). Every coordinator quick-test now shifts.
3. **Units convention**: pct-pt vs decimal yield-changes caused C2's 100x cost understatement;
   agent self-quarantined; all yield-approx sleeves re-audited (a6r7, A1credit clean).
4. C3 found and fixed a pos.shift(0) lookahead in its own shared loader before any saves.
5. IS/OOS protocol enforced everywhere: single OOS reveal after frozen IS rules; post-hoc
   configs labeled FAIL and discarded (B5 lesson from GOAL80 held).

## 6. ARTIFACTS
- Champions: campaign/results/GOAL100_CHAMPION_{daily,BALANCED_daily,AGGRESSIVE_daily}.csv + JSON
- New sleeves: campaign/agents/C5_newdata/sleeves/C5_ng_{weekday_prem,summer_weekday,summer_weekday_ddt}.csv
- C4 construction: campaign/agents/C4_metaalloc/sleeves/C4_construct_v2.csv + repro script
- Quarantine: campaign/agents/C2_ratescurve/sleeves/QUARANTINED/ (units-bug postmortem)
- All agent logs: campaign/agents/C{1..6}*/LOG_*.log, FINDINGS.md (every failed idea with numbers)
- Data added: kenfrench/ (48/49-ind, 25ff, ME/OP/INV, 10-mom daily 1926+), newdata/ (full UST curve,
  breakevens, EM-FX 16 pairs, broad dollar, heating oil/jet fuel spots, NFCI/STLFSI4)

## 7. ACCEPT
- **SR >= 2, MaxDD <= 8%, no leverage, 6bps, OOS-validated: EXCEEDED by wide margin.**
- **ann >= 100%: NOT achievable on free data — honest ceiling ~55-62% frozen / ~65% post-hoc wall (up from 43% at session start).**
- Coordinator post-mortem additions: pre-FOMC drift (t=2.48 raw, book SR 0.67 FAIL — regime-decayed), always-on steepener carry (fails DD envelope), fine-grid wall mapping (max 68% at full-sample-selection, breaches honesty).
- Remaining gap is a data/engine problem, not a construction problem: the campaign's 14 agent-rounds
  + coordinator sweeps systematically exhausted every accessible domain.
