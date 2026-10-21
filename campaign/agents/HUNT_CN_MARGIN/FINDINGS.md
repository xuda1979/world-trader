# HUNT_CN_MARGIN + HUNT_CN_HSGT — FINDINGS (honest negatives; seam census CLOSED)

Date: 2026-09-22. Closes the two remaining "genuinely un-mined" daily seams from the
AUDIT_R7REDO R8 §7b census (LEDGER=0, SLEEVES=0): eastmoney China A-share margin
panel and em_hsgt HK Stock Connect northbound flows. Pre-commit sealed in
PRECOMMIT.md BEFORE any evaluation; all engines T+1, 6.4bps full-|dW|, IS<2017-01-01.

## 1. China margin-balance sentiment (eastmoney_margin, 2010-03..2026-09, 3992 rows)
13 pre-registered configs across 3 stages (S1 balance momentum lb21/63/126 ±,
S1b index-leg variant, S2 margin-ratio z252 fade ±, S3 net-buy pressure ±)
on the tradable leg (sz510300 CSI300 ETF, 2012-05+):
- BEST: S1_mom_lb21_d+1 IS SR 0.422 — 2.4x below the 1.0 bar. FAIL.
- Index-leg variants (S1b) all |IS SR| <= 0.22. FAIL.
- Every config fails halves or neg-years or both; no exception worth a second stage.

## 2. HK Stock Connect northbound flows (em_hsgt, 2014-11..2026-09, 2746 rows)
8 pre-registered configs (SH1 net-flow z21/z63 pressure ±, SH2 activity momentum lb21/63 ±):
- SH1_netz21_d+1: **IS SR 1.087 — the only nominal IS-bar pass of this hunt. KILLED by autopsy:**
  (a) t = 1.6 sigma over just 26 IS months (SE 0.679); NOT significant, and 8-config family
      Bonferroni buries it completely.
  (b) Top-4 months (2015-05..2016-03, A-share bubble+crash) = 100% of IS edge; pre-2015
      contribution negative; the "edge" IS the 2015 episode.
  (c) H2 SR -0.16 (halves fail); full-span SR 0.545 < 0.6 floor; 5/13 neg years.
  (d) Turnover 0.67 |dW|/day = 10.8%/yr cost drag at 6.4bps — cost-fragile.
  (e) **DECISIVE: net_deal_amt (buy/sell) publication DIED 2024-08-16** (exchange stopped
      daily northbound flow disclosure — real regulatory break). The signal is
      UNIMPLEMENTABLE live regardless of backtest beauty. Position would be frozen flat
      since Aug-2024.
  Verdict: DEAD — recorded with the 2015-episode concentration + data-death as the two
  headline reasons.
- SH2 activity momentum: all |IS SR| <= 0.50. FAIL.

## 3. Ledger action (2 rows appended)
- "China A-share margin-balance sentiment (mom/fade/pressure engines on sz510300)" — dead,
  source HUNT_CN_MARGIN, "13 configs, best IS SR 0.422 (S1 mom lb21) vs 1.0 bar".
- "HK Stock Connect northbound net-flow pressure (z21/z63) on CSI300 ETF" — dead, source
  HUNT_CN_HSGT, "IS SR 1.087 over 26 months = 2015 bubble+crash episode (top-4 months=100%
  of edge, t=1.6σ, H2 -0.16); flow publication died 2024-08-16 -> unimplementable".

## 4. V7 impact: NONE (unchanged)
reproduce_v7.py re-run after the hunts: 9/9 PASS (IS SR gross 6.3821 / OOS SR 4.0983 /
net ann 29.66% / net monthly SR 3.6343 — all reproduced). No sleeve, weight, or ledger
artifact touched. The seam census from AUDIT_R7REDO R8 §7b is now FULLY consumed:
EIA PADD (closed 2026-09-22, prior commit), CN margin + HSGT (this hunt). Remaining
§7b entries were pre-excluded with recorded reasons (EU gas storage = same-priced
mechanism; SEC FTD 2017+ inception too short for 2009-16 IS; China margin monthly/TIC/CAPE
stale or monthly).

## 5. Incidental integrity note (non-blocking, disclosed)
The `OPT_20V7_full_monthly.csv` 2026-09-30 row (value 0.000019) is a pandas `ME` label
on an IN-PROGRESS partial month — daily data genuinely ends 2026-09-14 (ledger verified,
0 rows after today). Not lookahead; but 16/20 V7 sleeves now end before 2026-09-01
(median end 2026-08-24), so live marks are going stale. Flagged for the operator: the
decay-monitor 2y-trail window (ends 2026-08-31/09-30) is computed on real data, but a
live IBKR session would trade on sleeves whose most recent 2-6 weeks of signals are
unrefreshed. Recommend a data-refresh round before any live order.

## Artifacts
- PRECOMMIT.md (sealed first), honest_gate_cn_margin.py, honest_gate_hsgt.py,
  screen_results.csv (13 rows), hsgt_screen_results.csv (8 rows).
- Reproduce: python3 campaign/agents/HUNT_CN_MARGIN/honest_gate_cn_margin.py && \
  python3 campaign/agents/HUNT_CN_MARGIN/honest_gate_hsgt.py
