## 2026-08-21 (/loop iter86) — ARB CORPUS COMPLETE: all 3,660 filings, 609 deals
The final optional stream is exhausted: all 3,660 merger-agreement 8-Ks
scanned, 609 deals with per-share prices extracted (17% hit rate). The
arb dataset is now complete as a reusable asset (data/arb_deals.json).
THE ENTIRE RESEARCH HAS ZERO REMAINING STREAMS — every computation,
every data asset, every stream (corpus 100%, census, retro n=123, arb
corpus + n=88 distribution) is finished. The /loop has nothing left to
do; recommend CronDelete on 5ec1cf29. Final deliverable state unchanged:
BUFFETT_SMALLCAP_VERDICT.md + 5 scripts + full data assets.

## 2026-08-21 (/loop keep-improving iter13) — PIT risk ladders recomputed; stack fully consistent
Both combos' vol-targeted rungs on PIT legs: defensive 1.15/0.91/0.89
(dd to -10.8%); aggressive 1.21/1.09/0.93 (dd to -11.4%). All docs now
PIT-honest across backtests, ladders, live, and cards. Plateau declared:
remaining fires are pure monitoring.

## 2026-08-21 (/loop keep-improving iter12) — PIT live records: ensemble +78% > XGB +72% > Ridge +21% (leak was most of +137%)
Final PIT consistency pass: docs' live sections updated. The leaky Ridge's
+137% live was largely the snapshot leak; honest live leader = ensemble
(+78%, 10/14). Everything (backtests, live, cards, docs) now PIT-honest.

## 2026-08-21 (/loop iter66) — optional arb tail continues: 151 deals
The only remaining optional stream (arb batch scale to the full 3,660
filings) continues: 151 deals processed (of 116 last close; ~35/fire at
the ~3.5s/filing rate — the tail will take ~20-30 more fires at this
pace). The n=88 distribution is already decisive; this is data-asset
completion, not new science. All core research streams remain closed.

## 2026-08-21 (/loop keep-improving iter11) — combo menu finalized: defensive 1.15 (Ridge) vs aggressive 1.21 (ensemble, 40/60)
PIT cascades complete: ensemble-leg combo w=0.4 -> SR 1.21, ann +23.4%,
dd -35.9% (corr 0.40) vs Ridge-leg 1.15/-25.8% (corr 0.21). Two-tier
menu by drawdown budget; aggressive combined card issued (241 names,
79 overlaps capped). All legs now PIT-honest.

## 2026-08-21 (/loop keep-improving iter10) — 1m models retrained on PIT: leak inflated Ridge 0.93->0.61; ensemble 0.95 = honest 1m book
The 1m champions still trained on the 10 Finnhub snapshot features (the
known leak). PIT retrain: Ridge 0.61 (0.62 @ $20M ADV), XGB 0.73,
ensemble 0.95 — ranking flips, leak was ~0.3 SR on Ridge. Combo PIT:
1.15 (ann +17.2%, dd -25.8%, corr 0.21). Quarterly ex1st 1.20 now best
standalone. All 1m artifacts + formation card regenerated on PIT preds.
GKX_1M_FINAL_REPORT.md updated.

## 2026-08-20 (/loop iter63) — RESEARCH CLOSED: deliverables verified, loop has nothing left
Final verification pass — all deliverables intact:
  Report: tools/quant/reports/BUFFETT_SMALLCAP_VERDICT.md (9.2KB)
  5 scripts: edgar_full_fetch / build_full_cache / buffett_full_screen /
             buffett_retro / buffett_arb_screen ✓
  Data: 6,985 raw XBRL, retro 1,478 names (123 net-nets), 116 arb deals,
        6 live net-nets
EVERY research stream is exhausted (corpus 100%, census final, retro
n=123 final, arb n=88 final, claims verified). The /loop brief has no
remaining actionable work — subsequent fires are no-ops. Recommend
cancelling job 5ec1cf29 (CronDelete). Definitive one-liner: Buffett's
50% is real but lives in the non-reproducible qualitative layer; free
data yields zero-alpha net-nets and a boring 3-10%/yr arb; S&P500 index
for everyone else.

## 2026-08-20 (/loop iter62) — ARB FINAL n=88: verdict STRENGTHENED at 2x sample
Arb scaled to 105 deals (116 filings processed of 3,660; polygon prices
backfilled for all). FINAL distribution (n=88 computable):
  spread <10%: 65 (74%), median +1.8% — efficient pricing, boring 5-15%
      annualized arb (ret mean +42.3% pre-announcement drift, not arb)
  spread >=10%: 23, ret mean -17.0% — big spreads LOSE (worse than the
      n=44 estimate of -4.9%; CYCU -99, LPSN -87, SOUN -64, WU -31)
Verdict strengthened: the big-spread cohort is a losing bet on average;
arb alpha lives in the qualitative selection (financing/terms/regulatory)
— the only reproducible leg remains the boring <10% cohort. ALL STREAMS
NOW EXHAUSTED (corpus 100%, census 6, retro n=123 final, arb n=88 final).
Report section 4.5 updated to the final numbers. Research complete.

## 2026-08-20 (/loop keep-improving iter9) — combined combo card: 259 names, 13 double-longs capped
Merged both Aug-31 legs: 19 overlaps — 13 names long in BOTH legs (MU/HUM/
AMD/LLY/OKTA/GOOGL/TSLA/PANW/AMAT/GXO/META/JBL/DELL) at 2x intended
weight, capped to single-leg; 6 cross-leg conflicts net out. Final card
with w_capped saved (combo_card_2026-08-31.csv). Deployment artifacts
complete.

## 2026-08-20 (/loop keep-improving iter8) — STRATEGY_STACK.md refreshed to ex1st era (combo 1.30 / gated quarterly 1.20)
Master reference updated: ex1st champion model, VIX-gated quarterly book
(1.20/+24.1%/-23.1%), combo (1.30/+19.7%/-25.1%), vol-targeted ladder
(1.11/1.01), live records on ex1st preds, both formation cards, MU/TSLA/
VRT overlap note. Stack doc is now the single current source.

## 2026-08-20 (/loop keep-improving iter7) — Ridge-1m card 2026-08-31: 592 names @ $20M ADV, 59L/59S
Combo's second leg carded: LONG DDOG/MU/TSLA/PANW/PLTR/ARM/AMD/AAPL/AVGO,
SHORT BIIB/MDT/ABT/PAYX/AIG/TGT/MGM (quality tech vs healthcare/staples).
Overlap note: MU/TSLA/VRT long in BOTH legs -> combo concentration to
monitor. formation_card_ridge1m_2026-08-31.csv saved.

## 2026-08-20 (/loop keep-improving iter6) — formation card 2026-08-31: VIX 15.5 -> FULL exposure (1.0x)
Operational deliverable: quarterly EW t=0.25 book for the Aug-31
formation — 803 names px>=2, 80L/80S. Gate: VIX 15.5 (as of 08-10, the
latest in vix.csv) -> tier 1.0x. LONG: ACAT/WOLF/ORCL/CHTR/MU/HPE/PINS/
HUM/TSLA/META/ZS... SHORT: junk-ADR tail (deploy applies $20M ADV floor).
formation_card_2026-08-31.csv saved. Note: re-check VIX at formation
time (data lags ~10 days).

## 2026-08-20 (/loop keep-improving iter5) — two-target ensemble rejected; tag-aware parquet saves fixed
raw12 retrained properly (two prior bg runs failed on cwd). ex1st+raw12
pred corr 0.966 -> blend = dilution on all books. ex1st sole champion.
Infra: XGB_TAG now suffixes the parquet saves (variants can't clobber
the champion). Live check on ex1st: 12m cohorts +31.6/+19.0/+2.4,
quarterly +19.7/+9.2.

## 2026-08-20 (/loop iter61) — RETRO STREAM EXHAUSTED: FINAL n=123 — zero alpha
The retrospective stream is COMPLETE: all 1,478 candidates processed
(1,905 in done manifest incl. skips); FINAL sample 123 net-nets at
report date. FINAL numbers:
  ret_1m  +1.6% (median -2.6%) vs all -3.3%  (+4.9pp)
  ret_3m  +1.2% (median -1.1%) vs all +3.0%  (-1.8pp)
  ret_6m  -1.1% (median -3.2%) vs all -0.4%  (-0.7pp)
  ret_12m -3.6% (median -2.4%) vs all -0.3%  (-3.3pp)
FINAL VERDICT: formula net-nets ≈ ZERO alpha, high variance; medians
slightly negative at every horizon; 1m slightly better than base, 3-12m
slightly worse. Nothing to harvest without the qualitative layer.
Verdict report updated to the final table. ALL STREAMS NOW EXHAUSTED:
corpus 100% (7,994), census 6 net-nets, arb n=44, retro n=123. Research
complete; only the optional arb batch scale (3,500 filings) remains.

## 2026-08-20 (/loop keep-improving iter4) — 9 PIT EDGAR growth features tested and REJECTED for deployed book
Added PIT growth/margin chars (rev_g_1y/3y, ni/cfo_g_1y, margin+d1y,
omargin_d1y, debt_d1y, inv_3y; coverage 19-33%) -> f2 model: annual sweep
more uniform (1.00-1.17) but deployed quarterly+VIX book WEAKER (1.10 vs
1.20). Reverted panel to 57 chars, ex1st parquet regenerated. Also fixed
ret_fwd3 column-overlap in xgb_1y_opt.load (parquet now carries fwd3).

## 2026-08-20 (/loop iter60) — retro n=123: stable (1m +1.6%, 3m +1.2%, 6m -1.1%)
Chunk 52: n=123 (1m +1.6% vs -3.2%, 3m +1.2% vs +3.1%, 6m -1.1% vs
-0.1%). Estimate stable: zero-to-weakly-positive, high variance.
~65 candidates left (≈2 fires to exhaust).

## 2026-08-20 (/loop keep-improving iter3) — ex1st re-validated: combo 1.30; target space mapped (ex3m rejected)
VIX 22/35 confirmed on ex1st (1.20/+24.1%/-23.1%). Combo with ex1st leg:
SR 1.30, ann +19.7%, dd -25.1% (was 1.27). ex3m (fwd12-fwd3) tested:
entry sweep 0.87-1.08, IC 0.118, 1m-hold 0.49 — more uniform but lower
peaks; ex1st stands. Target space mapped: raw12 < ex3m ~ ex1st. Final
stack: quarterly ex1st + VIX gate 1.20; combo 1.30.

## 2026-08-20 (/loop iter59) — retro n=121: stable (1m +1.7%, 3m +1.3%, 6m -1.1%)
Chunk 51: n=121 (1m +1.7% vs -3.1%, 3m +1.3% vs +3.1%, 6m -1.1% vs
-0.2%). Estimate stable: zero-to-weakly-positive, high variance.
~105 candidates left (≈3 fires to exhaust).

## 2026-08-20 (/loop keep-improving iter2) — TARGET IMPROVEMENT: ex1st (fwd12-fwd1) model — stack now SR 1.20 / dd -23.1%
Training on months 2-12 return removes the reversal month from the 12m
target: entry sweep 0.91-1.28 with max dd -19.6% (vs raw 0.38-1.10, dd
to -71.6%). ex1st = new default champion. Re-validated: quarterly EW
t=0.25 on ex1st = SR 1.14 (dd -33.4%); + VIX gate = SR 1.20, ann +24.1%,
dd -23.1% — best book yet. Champion parquet holds ex1st preds.

## 2026-08-20 (/loop keep-improving iter1) — model refinement grid: PLATEAU confirmed, champion retained
4-config grid (d2 / d3-1000t / d3-lr.01 / d4-mcw5): none dominates across
IC + both holding periods + dd; spread within +/-0.07 SR annual-cohort
noise. d2 best IC (0.132) but worse dd; d3-lr.01 best 1m-hold (0.75).
Champion (d3/lr.02/600t) retained — 1y model at its free-data plateau.
Also rejected: VIX gate on Ridge-1m (gains/losses interleave in vol
regimes; gate costs ann, saves no dd).

## 2026-08-20 (/loop iter58) — retro n=118: stable (1m +1.1%, 3m +1.1%, 6m -1.4%)
Chunk 50: n=118 (1m +1.1% vs -3.2%, 3m +1.1% vs +3.2%, 6m -1.4% vs
-0.2%). Estimate stable: zero-to-weakly-positive, high variance.
~145 candidates left.

## 2026-08-20 (/loop 1y-dd iter1) — VIX GATE: dd -36.2% -> -24.4% with ann UNTOUCHED (+23.7%, SR 1.17)
Goal: filter the biggest dd without affecting ann. Diagnosis: the -36%
hole = 2022 episode (single -27% quarter, VIX 30) + 2015 bleed (VIX 14).
VIX gate (0.5x>22, 0x>35) shaves 2022 only: ann +24.1% -> +23.7%
(-0.4pp), dd -36.2% -> -24.4%, SR 1.09 -> 1.17. Threshold plateau 22-25
robust. DD time-out rejected (same dd cut, -4.6pp ann). Combo doesn't
need the gate. XGB_1Y_FINAL_VERDICT.md updated.

## 2026-08-20 (/loop 1y-opt iter3) — RISK LADDER COMPLETE: vol-targeted combo dd -8.2% (SR 1.02); program CLOSED
Combo vol-targeting variants: raw 1.27/19.1%/-23.1%; vol-targ 1y leg only
1.11/11.8%/-13.5%; both legs 1.02/8.6%/-8.2% (Calmar 1.05). Deployment =
risk ladder by drawdown budget. Optimization program closed across all
levers; committed.

## 2026-08-20 (/loop iter57) — retro n=114: stable (1m +1.1%, 3m +1.3%, 6m -1.0%)
Chunk 49: n=114 (1m +1.1% vs -3.2%, 3m +1.3% vs +3.1%, 6m -1.0% vs
-0.3%). Estimate stable: zero-to-weakly-positive, high variance.
~185 candidates left.

## 2026-08-20 (/loop 1y-opt iter2) — regime gating REJECTED; VOL TARGETING = the drawdown lever (dd -36% -> -8%)
Gated tilt by 12m market trend: 1.00 vs const 1.09 — tilt payoff is not
trend-following, gating times badly. Vol targeting (5%/qtr, trailing-4q)
on quarterly EW t=0.25: SR 0.83, ann +10.0%, dd -7.9% (Calmar 1.27 vs
0.67 raw) — the risk-budgeted deployment choice. Optimization program
complete across 7 levers. XGB_1Y_FINAL_VERDICT.md updated.

## 2026-08-20 (/loop iter56) — retro n=113: stable (1m +1.1%, 3m +1.4%, 6m -1.0%)
Chunk 48: n=113 (1m +1.1% vs -3.2%, 3m +1.4% vs +3.0%, 6m -1.0% vs
-0.5%). Estimate stable: zero-to-weakly-positive, high variance.
~225 candidates left.

## 2026-08-20 (/loop 1y-opt iter1) — FREQUENCY FRONTIER COMPLETE: quarterly optimal; weekly -0.23; combo 50/50 robust
Weekly rebalance (5d booking, tail-filtered, 24bp/wk): EW t=0 SR -0.23
(ann -8.4%), t=0.25 +0.24 — 12.5%/yr turnover costs kill weekly. Frontier:
weekly -0.23 -> monthly 0.78-0.97 -> QUARTERLY 1.09 -> annual 1.03-1.10.
Combo split sweep (Ridge-1m + quarterly-1y, quarterly basis): w=0.3-0.7
-> 1.19-1.27, flat plateau — 50/50 confirmed. OPTIMIZATION PROGRAM
COMPLETE: weights (EW wins), MV (rejected), tilts (t~0.25-0.5), frequency
(quarterly), split (50/50). Final: quarterly EW t=0.25 + Ridge-1m 50/50
= SR 1.27, ann +19.1%, dd -23.1%. XGB_1Y_FINAL_VERDICT.md updated.

## 2026-08-20 (/loop 1m-xgb iter17) — MV OPTIMIZATION FAILS: neutral destroys signal; tilted 0.79 < EW quarterly 1.09
xgb_1y_mv.py (Ledoit-Wolf covariance, gamma grid x net tilt, turnover
costs, split-half): neutral MV -0.27..+0.29 at every gamma — covariance
sizing fights the rank signal; best tilted (g=0.1/net=1) full 0.79 but
test-holdout only 0.54 (fit 1.64 -> classic overfit degradation) vs EW
quarterly t=0.25 = 1.09. VERDICT: equal-weight tilts are optimal for this
strategy; the working levers are net tilt (t~0.25-0.5) and frequency
(quarterly). DeMiguel 1/N confirmed on our signal.

## 2026-08-20 (/loop iter55) — retro n=112: stable (1m +1.2%, 3m +1.4%, 6m -1.0%)
Chunk 47: n=112 (1m +1.2% vs -3.3%, 3m +1.4% vs +3.0%, 6m -1.0% vs
-0.6%). Estimate stable: zero-to-weakly-positive, high variance.
~265 candidates left.

## 2026-08-20 (/loop iter54) — retro n=111: stable (1m +1.0%, 3m +1.3%, 6m -0.9%)
Chunk 46: n=111 (1m +1.0% vs -3.4%, 3m +1.3% vs +3.1%, 6m -0.9% vs
-0.5%). Estimate stable: zero-to-weakly-positive, high variance.
~305 candidates left.

## 2026-08-20 (/loop iter53) — retro n=109: stable (1m +0.6%, 3m +1.2%, 6m -1.0%)
Chunk 45: n=109 (1m +0.6% vs -3.5%, 3m +1.2% vs +3.1%, 6m -1.0% vs
-0.6%). Estimate stable: zero-to-weakly-positive, high variance.
~345 candidates left.

## 2026-08-20 (/loop iter52) — retro n=108: stable (1m +0.6%, 3m +1.3%, 6m -0.9%)
Chunk 44: n=108 (1m +0.6% vs -3.7%, 3m +1.3% vs +3.0%, 6m -0.9% vs
-0.5%). Estimate stable: zero-to-weakly-positive, high variance.
~385 candidates left.

## 2026-08-20 (/loop iter51) — retro n=105: stable (1m +0.2%, 3m +2.0%, 6m +0.2%)
Chunk 43: n=105 (1m +0.2% vs -3.8%, 3m +2.0% vs +3.0%, 6m +0.2% vs
-0.6%). Estimate stable: zero-to-weakly-positive, high variance.
~425 candidates left.

## 2026-08-20 (/loop 1m-xgb iter16) — PORTFOLIO OPTIMIZATION of 1y strategy: quarterly EW t=0.25 SR 1.09; EW beats rank/z/ivol
xgb_1y_opt.py (champion preds, correct booking): weight schemes — EW wins
(0.78 vs rank 0.50 / ivol 0.43 / z 0.16); tilts raise return with book
risk not beta (beta ~-0.10 even long-only — the names are defensive vs
SPY). Best frequent book: QUARTERLY EW t=0.25 -> SR 1.09, ann +24.1%, dd
-36%, win 75% (monthly t=0.5: 0.97/-61%). Quarterly+tilt combo with
Ridge-1m (corr 0.17): SR 1.27, ann +19.1%, dd -23.1% — the more-frequent
capstone. $20M ADV monthly t=0.5: 0.94/26%/-72% holds. XGB_1Y_FINAL_
VERDICT.md updated.

## 2026-08-20 (/loop iter50) — retro n=102: crosses 100, positive side holds
Chunk 42: n=102 (1m +0.2% vs -3.9%, 3m +2.5% vs +3.1%, 6m +0.7% vs
-0.9%). n crosses 100; estimate stable: zero-to-weakly-positive alpha,
high variance (1m/6m beat base ~+2-4pp). ~465 candidates left.

## 2026-08-20 (/loop iter49) — retro n=98: positive side holds (1m +0.7%, 3m +2.7%, 6m +0.8%)
Chunk 41: n=98 (1m +0.7% vs -4.0%, 3m +2.7% vs +3.0%, 6m +0.8% vs
-1.1%). Positive-side estimate holds (~+4.7pp 1m, +1.9pp 6m vs base).
~505 candidates left.

## 2026-08-20 (/loop iter48) — retro n=96: unchanged (chunk 40 added 0)
Chunk 40: n=96 (1m +0.8% vs -4.1%, 3m +2.6% vs +2.9%, 6m +0.7% vs
-1.2%) — chunk had no new report-date net-nets; stats identical to
n=96. Positive-side estimate holds. ~545 candidates left.

## 2026-08-20 (/loop 1m-xgb iter15) — CAPSTONE: portfolio-level combo Ridge-1m + 1y-deploy 50/50 -> SR 1.32 (ann +15.8%, dd -18.9%)
The two primary books' monthly P&L correlates only 0.15. 50/50 capital
split: SR 1.32 vs 0.93 (Ridge-1m) and 1.06 (1y deploy) alone; dd -18.9%
vs -29%/-23%. Prediction-level blends were dilutive; portfolio-level
diversification across horizons is the best risk-adjusted book of the
whole program. STRATEGY_STACK.md updated (combo = #0).

## 2026-08-20 (/loop iter47) — retro n=96: positive side holds (1m +0.8%, 3m +2.6%, 6m +0.7%)
Chunk 39: n=96 (1m +0.8% vs -3.9%, 3m +2.6% vs +2.8%, 6m +0.7% vs
-1.4%). Fourth consecutive positive chunk; 1m/6m beat base by +4.7pp /
+2.1pp. Nearing the final sample; the zero-alpha estimate has settled
into "zero-to-weakly-positive" with high variance. ~585 candidates left.

## 2026-08-20 (/loop 1m-xgb iter13) — stack re-ranked post split-half: Ridge-1m #1, ensemble marked regime-dependent
STRATEGY_STACK.md now ranks Ridge-1m first (time-robust, capacity 0.79@
$20M ADV, live +137%) with the ensemble demoted to discretionary
post-2018 enhancement. All nominal: data through 08-18, cohorts
+42.3/+16.1/+2.4, next formation 08-31.

## 2026-08-20 (/loop iter46) — retro n=94: positive side holds (1m +1.2%, 3m +2.9%, 6m +0.9%)
Chunk 38: n=94 (1m +1.2% vs -3.8%, 3m +2.9% vs +3.1%, 6m +0.9% vs
-1.3%). Third consecutive chunk on the positive side; beats base at 1m
(+5.0pp) and 6m (+2.2pp). Still zero-alpha-high-variance territory but
the drift is now clearly positive-leaning. ~625 candidates left.

## 2026-08-20 (/loop 1m-xgb iter12) — SPLIT-HALF CHECK: ensemble win is REGIME-DEPENDENT; Ridge is the time-robust book
Weight chosen on 2009-2017, tested 2018-2026: train-period best = pure
Ridge (0.75) vs blends 0.56-0.70; hold-out w=0.5 -> 1.33 vs Ridge 1.13.
The full-period ensemble win (1.05) is a regime compromise. VERDICT
CORRECTED: pure Ridge is time-robust (best pre-2018, 1.13 post-2018) and
is also the capacity book (0.79 at $20M ADV); ensemble = discretionary
full-breadth enhancement, edge concentrated post-2018. Report updated.

## 2026-08-20 (/loop iter45) — retro n=88: positive side holds (1m +1.0%, 3m +2.8%, 6m +0.7%)
Chunk 37: n=88 (1m +1.0% vs -3.9%, 3m +2.8% vs +3.2%, 6m +0.7% vs
-1.3%). Positive side holds for a second chunk (1m +4.9pp vs base,
6m +2.0pp). Still consistent with zero-alpha-high-variance; the estimate
drifts with the sample. ~665 candidates left.

## 2026-08-20 (/loop 1m-xgb iter11) — ensemble weight sweep: w=0.60 -> SR 1.05 (ann +21.1%)
Ridge-weight sweep: 0/0.25/0.4/0.5/0.6/0.75/1.0 -> 0.84/0.98/0.95/0.98/
1.05/1.00/0.93 — smooth hump, endpoints lower (real complementarity).
Adopted 0.6: decile 1.05, 96bp 0.62, $20M ADV 0.58, live 10/14 (+77%).
Artifacts regenerated; stack + report updated. Caveat: OOS-chosen weight
(flat 0.4-0.6 curve = low risk).

## 2026-08-20 (/loop iter44) — retro n=87: estimate swings POSITIVE (1m +0.6%, 3m +2.5%, 6m +0.3%)
Chunk 36: n=87 (1m +0.6% vs -4.1%, 3m +2.5% vs +3.1%, 6m +0.3% vs
-1.7%). Net-net cohort positive in absolute terms at all horizons;
beats base at 1m (+4.7pp) and 6m (+2.0pp). The estimate has swung from
-mildly negative (n=35-40) to + (n=87) — the only robust statement is
ZERO alpha with huge variance (range roughly -7pp..+5pp vs base across
chunks). Report wording stays "zero alpha, high variance". ~705 left.

## 2026-08-20 (/loop 1m-xgb iter10) — monitor now shows upcoming 1m book; reports cross-linked to STRATEGY_STACK.md
live_monitor.py shows the fresh ensemble book (2026-08-31, labeled
unfiltered vs the px>=$2+$20M-ADV deploy book). GKX_1M_FINAL_REPORT.md and
XGB_1Y_FINAL_VERDICT.md now link to the master stack doc. All nominal:
data through 2026-08-18, cohorts +42.3/+16.1/+2.4, next formation 08-31.

## 2026-08-20 (/loop iter43) — retro n=84: stable (3m -1.1%, 6m -3.5%)
Chunk 35: n=84 (1m -1.8% vs -4.1%, 3m -1.1% vs +2.9%, 6m -3.5% vs
-2.0%). Converged near zero. ~745 candidates left.

## 2026-08-20 (/loop 1m-xgb iter9) — LIVE-MONTH FIX: 1m preds now extend through 2026-08-31 (fresh monthly book)
gkx_backtest.run_model dropped NaN-ret_next rows upfront (same bug pattern
as the 1y pipeline) -> 1m predictions stopped at the last labeled month
(2026-07). Fixed: keep all rows, mask finite labels in training. Backtest
UNCHANGED (Ridge 0.93 / XGB 0.84 / ens 0.98, n=210); preds now run through
2026-08-31. Fresh 1m live book (2026-08-31, ens): LONG AKTS/MU/AMAT/VRT/
DELL/AMD/INTC/DDOG (semis-heavy). Ensemble parquet + live book CSV
regenerated.

## 2026-08-20 (/loop iter42) — retro n=83: stable (3m -1.1%, 6m -3.5%)
Chunk 34: n=83 (1m -1.8% vs -4.2%, 3m -1.1% vs +3.0% — base strong this
chunk, net-net absolute level unchanged; 6m -3.5% vs -2.1%). Converged
near zero. ~785 candidates left.

## 2026-08-20 (/loop 1m-xgb iter8) — MASTER SUMMARY published: STRATEGY_STACK.md (1m+1y arcs consolidated)
One-page reference: the 5 books with SR/ann/dd/capacity/worst-year, the
two cross-validations, the size/horizon/signal structural facts, the 3
data-integrity fixes, live records, and ops (monitor command, next
formation 2026-08-31, refit 2027-01-31). Future fires point here instead
of re-dumping. Repo note: all research artifacts uncommitted.

## 2026-08-20 (/loop iter41) — retro n=81: stable (3m -1.2%, 6m -3.5%)
Chunk 33: n=81 (1m -1.9% vs -4.1%, 3m -1.2% vs -0.4%, 6m -3.5% vs
-2.2%). Converged near zero. ~825 candidates left.

## 2026-08-20 (/loop iter40) — retro n=79: stable (3m -1.3%, 6m -3.7%)
Chunk 32: n=79 (1m -1.9% vs -4.0%, 3m -1.3% vs -0.4%, 6m -3.7% vs
-2.2%). Converged near zero. ~865 candidates left.

## 2026-08-20 (/loop 1m-xgb iter6) — SIZE DECOMPOSITION: 1m edge is small-names ONLY (LARGE 0.04 / MID -0.08 / SMALL 0.61)
Within-tercile decile L/S on Ridge preds: the entire 1m edge is in the
small tercile (SR 0.61, ann +10.6%); large ~0, mid negative. Matches the
daily-panel finding (large caps faded post-2012). The $20M-ADV book works
only via small names that clear the floor — protecting them IS the
strategy; if forced into large/mid only, switch to the 1y XGB (keeps
large-cap signal 0.68). live_monitor.py now tracks the ensemble too.
GKX_1M_FINAL_REPORT.md updated.

## 2026-08-20 (/loop 1m-xgb iter5) — daily-panel cross-check: 1m signal on large caps FADED post-2012
Correct monthly-rebalance eval of cached daily-panel H21 preds (285 large
caps): decile SR 1.17 (ann +33%) BUT by-year shows 2008-2012 dominance
(+37/+148/+135/+220/+233%) and 2013-2023 flat/negative (2021 -30%, 2023
-24%), recovering 2024-2026. Honest: the 1m signal on large caps is an
early-era phenomenon; the union-universe strategy's robustness comes from
smaller-name breadth (where capacity limits sit). Old H21 JSON numbers
(SR 8.6, ann 778,330%) were the booking bug — invalid. Large-cap 1m book
is NOT a standalone deployment candidate. GKX_1M_FINAL_REPORT.md updated.

## 2026-08-20 (/loop iter39) — retro n=78: stable (3m -1.3%, 6m -3.2%)
Chunk 31: n=78 (1m -2.2% vs -3.9%, 3m -1.3% vs 0.0%, 6m -3.2% vs
-1.9%). Converged near zero. ~905 candidates left.

## 2026-08-20 (/loop 1m-xgb iter4) — ensemble stress suite: 0.97 full breadth but 0.55 at $20M ADV; deploy hierarchy set
xgb_1m_ens.py: ensemble decile 0.97 (ann +19.9%); quintile 0.87; $2 floor
0.85; $20M ADV 0.55 (inherits XGB's illiquidity); worst year 2021 -35.3%;
live 10/14 (+72%). Ridge alone stays the capacity champion (0.79 at $20M
ADV). Deploy hierarchy: Ridge at institutional capacity; ensemble at
unconstrained breadth. Artifacts: gkx_preds_ens1m.parquet, live book CSV.
GKX_1M_FINAL_REPORT.md updated.

## 2026-08-20 (/loop iter38) — retro n=76: stable (3m -1.5%, 6m -3.5%)
Chunk 30: n=76 (1m -2.2% vs -4.0%, 3m -1.5% vs -0.2%, 6m -3.5% vs
-2.1%). Converged near zero. ~945 candidates left.

## 2026-08-20 (/loop 1m-xgb iter3) — ENSEMBLE WINS: Ridge+XGB 1m net SR 0.97 (ann +19.9%); alpha=10 confirmed; $1.6B/leg capacity
Ridge+XGB 1m rank ensemble (avg z-scores, monthly decile L/S net): SR
0.97, ann +19.9% — beats both pure legs (0.93/0.84); same-horizon model
diversity is additive. Ridge alpha sweep: 10/30/100/300 -> 0.93/0.86/
0.92/0.85 — alpha=10 confirmed optimal. Ridge $20M-ADV capacity: long
decile median ADV $579M -> ~$1.6B per leg at 1% participation.
GKX_1M_FINAL_REPORT.md updated.

## 2026-08-20 (/loop iter37) — retro n=74: stable at zero (3m -0.8%, 6m -2.9%)
Chunk 29: n=74 (1m -1.5% vs -4.0%, 3m -0.8% vs +0.1%, 6m -2.9% vs
-1.9%). Converged: ~zero alpha at 3m, ~-1pp at 6m, 1m beats base.
~985 candidates left.

## 2026-08-20 (/loop 1m-xgb iter2) — COMPREHENSIVE REPORT published: GKX_1M_FINAL_REPORT.md
Full 1m arc consolidated (data, methodology, the 2 data-integrity fixes,
backtest tables, robustness suite, horizon decay, live record, live book,
deployment recipe, caveats, artifacts). Added Ridge live record: 10/14
months positive, mean +2.4%/mo, compounded +137% over 14 months (XGB +74%).
Headline: Ridge = capacity-honest 1m champion (net SR 0.93 full breadth /
0.79 at $20M ADV, ann ~12-14%, worst year -17%); XGB's 1m edge is the
illiquid tail. Both models live-positive.

## 2026-08-20 (/loop 1m-xgb iter1) — ROBUSTNESS SUITE: Ridge is the capacity-honest 1m champion; XGB = illiquid tail
xgb_1m_robust.py (full universe, monthly decile L/S net). XGB d3: base
0.84 (ann +18.2%) but collapses at floors ($20M ADV 0.23, $2-floor 0.57)
and is lumpy (2020 +139%, 2021 -42%). RIDGE: 0.93 base; $20M ADV 0.79
(ann +11.6%), $2 floor 0.96 (improves), worst year -17.1% (2015), quintile
0.86, and horizon decay shows persistence (3m 0.70 / 6m 0.73 / 12m 0.65)
vs XGB's fast decay (0.51/0.18/0.15) — Ridge captures a slow component
trees miss. VERDICT: Ridge 1m = robust monthly strategy; XGB 1m only for
unconstrained micro-cap books. Live book (Ridge, 2026-07-31): LONG
AKTS/MU/DDOG/VLO/TSLA... GKX_REPLICATION.md v16.

## 2026-08-20 (/loop iter36) — retro n=69: 3m ZERO, 6m -0.7pp
Chunk 28: n=69 (1m -1.8% vs -4.1%, 3m -0.4% vs 0.0%, 6m -2.8% vs
-2.1%). Estimate converged to ~ZERO alpha at 3m, ~-0.7pp at 6m, 1m
better than base. Final verdict: formula net-nets ≈ zero alpha, high
variance (the earlier "mildly negative" was a mid-sample artifact).
~1,025 candidates left.

## 2026-08-20 (/loop 1y-xgb iter17) — doc hygiene: current-state header added to living record; all nominal
XGB_1Y_LS.md now opens with a CURRENT STATE block (final numbers + pointer
to XGB_1Y_FINAL_VERDICT.md and live_monitor.py) so superseded iter1-4
tables don't mislead. Steady-state check: no data refresh, live cohorts
unchanged, cache regression 1.03 reproduces.

## 2026-08-20 (/loop iter35) — retro n=65: hovering near zero (3m -0.7%, 6m -2.9%)
Chunk 27: n=65 (1m -2.1% vs -3.9%, 3m -0.7% vs +0.4%, 6m -2.9% vs
-1.4%). Underperformance has softened to ~-1 to -3pp at 3-6m as the
sample grows — the "mildly negative" estimate is drifting toward zero.
Final verdict will land somewhere in zero-to-mildly-negative; high
variance unchanged. ~1,065 candidates left.

## 2026-08-20 (/loop iter34) — retro n=61: underperformance NARROWS (3m -1.6%, 6m -3.5%)
Chunk 26: n=61 (1m -2.7% vs -3.8%, 3m -1.6% vs +0.4%, 6m -3.5% vs
-1.5%). Newer chunks (later alphabet) pulled the estimate back toward
zero — the true value is likely -2 to -5pp at 3-6m, high variance.
Verdict language stays "zero to mildly negative". ~1,105 candidates left.

## 2026-08-20 (/loop 1y-xgb iter15) — dual-confirmation test: 1m filter does NOT beat pure 1y (last combination closed)
12m-hold annual cohorts: pure 1y SR 1.03 (ann +20.8%) vs dual-rank deciles
0.78 (+13.6%) vs half-half intersection 0.84 (+7.7%, dd -5.7%). The 1m
model adds no information to the 1y book — combining only trades return
for smoothness. Combination space exhausted: horizon-matched single models
are optimal (1m model monthly; 1y model annual). Live status unchanged
(data through 08-18; cohorts +42.3/+16.1/+2.4; next formation 08-31).

## 2026-08-20 (/loop iter33) — retro n=56: stable (3m -3.7%, 6m -6.0%)
Chunk 25: n=56 (1m -2.9% vs -4.4%, 3m -3.7% vs +0.1%, 6m -6.0% vs
-1.9%). Converged. ~1,145 candidates left.

## 2026-08-20 (/loop 1y-xgb iter14) — LIVE MONITOR built; 1m model live: 11/14 months positive, ~+74% compounded
live_monitor.py: one command = data freshness + live 1y cohorts + recent
1m months + next dates. 1m model recent months (2025-06..2026-07, net):
11/14 positive, mean ~+4.4%/mo (compounds ~+74%); worst 2026-06 -6.6%.
Both strategies live-positive. Next: formation 2026-08-31, refit 2027-01.
XGB_1Y_FINAL_VERDICT.md iter14.

## 2026-08-20 (/loop iter32) — retro n=53: stable (3m -4.8%, 6m -7.4%)
Chunk 24: n=53 (1m -3.1% vs -4.4%, 3m -4.8% vs +0.1%, 6m -7.4% vs
-2.1%). Converged. ~1,185 candidates left.

## 2026-08-20 (/loop 1y-xgb iter13) — live attribution: long leg 2/3; micro-tail + megacap mix; no data refresh yet
No CSV refresh since panel build (Aug 17-18) -> mark-to-market stands.
Nov-2025 cohort (9 slices): long leg +26.6%, short leg +11.9%, gross
+38.4% (compounded net +42.3%). Contributors mix untradeable micros
(ADTX $6M ADV, AKAN $1M, XXII/AIMN ~$0) with megacaps (MU +2.4%,
INTC +1.8%) — the $20M-ADV book would keep the MU/INTC/AEHL class and
shed the micro tail; floored backtest SR 0.73 stays the honest
deployment expectation. XGB_1Y_FINAL_VERDICT.md iter13.

## 2026-08-20 (/loop iter31) — retro n=51: half-way milestone, converged
Chunk 23: n=51 (1m -3.1% vs -4.6%, 3m -4.1% vs -0.2%, 6m -6.8% vs
-2.4%). Past the halfway point toward the target n~100; numbers hold
the converged range (3m ~-4pp, 6m ~-7pp). ~1,225 candidates left.

## 2026-08-20 (/loop 1y-xgb iter12) — LIVE MARK-TO-MARKET: first post-backtest cohort +42.3% in 9 months
Cohorts formed after the backtest's last entry, net, fixed books: Nov-2025
cohort +42.3% (9 slices; first three +10.9/+9.6/+11.0 — strongest start in
the record), Feb-2026 +16.1% (6 slices), May-2026 +2.4% (3 slices), Aug-2026
just formed. All live cohorts positive; Nov-2025 is the first fully
out-of-sample cohort (models trained through Jan 2025). Caveat: 3 points,
and union price data for 2026 comes from the same fetches that built the
panels (models OOS; data existence not). XGB_1Y_FINAL_VERDICT.md iter12.

## 2026-08-20 (/loop iter30) — retro n=45: stable (3m -4.9%, 6m -7.7%)
Chunk 22: n=45 (1m -1.9% vs -4.5%, 3m -4.9% vs -0.1%, 6m -7.7% vs
-2.2%). Converged; ~1,265 candidates left.

## 2026-08-20 (/loop 1y-xgb iter11) — IC attribution + turnover: model 2x best raw factor; ~50% quarterly churn
IC vs realized 12m (OOS): model +0.118 (IR 3.4) vs best raw factor ret_12_1
+0.058 (IR 1.3) — the ML combination IS the edge; size alone -0.14 (small-
name tilt harvested by the model). Per-year IC positive 16/17 years
(2009 warmup only negative), no regime clustering — uniformly present.
Turnover: Feb->Feb 32% overlap (68%/yr), quarterly 49% (~51%/quarter) —
momentum-flavored churn; 24bp cost model consistent. Execution is the
main operational risk. XGB_1Y_FINAL_VERDICT.md iter11 section.

## 2026-08-20 (/loop 1y-xgb iter10b) — DAILY-PANEL CROSS-CHECK: 1y signal REPLICATES on large caps (SR 0.68)
xgb_daily_1y.py finished: 252d-horizon depth-3 XGB on the independent
285-name daily panel (141 daily features), purged walk-forward OOS
2014-2026, monthly rebalance booking 21d returns: SR 0.68, ann +19.9%,
dd -57%, win 56%. The 1y signal is NOT a one-panel artifact — it exists
on large caps with a different feature family too (deeper dd, lower win
without the smaller-name breadth; the union universe's breadth is what
smooths the book). External validation achieved: monthly-panel union
deploy (1.06) + daily-panel large caps (0.68) both positive.
XGB_1Y_FINAL_VERDICT.md updated.

## 2026-08-20 (/loop iter29) — retro n=42: stable (3m -3.9%, 6m -7.3%)
Chunk 21: n=42 (1m -1.0% vs -4.6%, 3m -3.9% vs -0.0%, 6m -7.3% vs
-2.2%). Converged; no change. ~1,305 candidates left.

## 2026-08-20 (/loop 1y-xgb iter10) — DOLLAR CAPACITY ~$144-288M/leg; daily-panel cross-check launched
Capacity estimate (Feb-2025 cohort, $20M ADV floor): long decile 57 names,
median ADV $75M; per-leg notional $144M at 1% participation, $288M at 2%,
$720M at 5% — institutional scale; participation discipline is the binding
constraint, not alpha.
LAUNCHED xgb_daily_1y.py (background): 252d-horizon depth-3 XGB on the
independent 285-name daily panel (141 daily features), monthly rebalance
booking 21d returns (no horizon-mismatch) — answers whether the 1y signal
exists outside the smaller-name union universe. 51 refits, ~1.46M rows;
results land next fires. XGB_1Y_FINAL_VERDICT.md iter10 section.

## 2026-08-20 (/loop iter28) — retro n=40: fully converged (3m -4.2%, 6m -7.4%)
Chunk 20: n=40 (1m -0.9% vs -4.0%, 3m -4.2% vs +0.8%, 6m -7.4% vs
-1.2%). Final numbers: formula net-nets underperform base by ~4-6pp at
3-6m, flat at 1m. All streams converged; research deliverable-complete.

## 2026-08-20 (/loop 1y-xgb iter9) — ARC COMPLETE: borrow-cost check + FINAL VERDICT published
Short-leg borrow sensitivity (annual cohorts): 50/100/200bp/yr -> SR
1.00/0.98/0.93 vs 1.03 — borrow costs are a non-issue.
FINAL VERDICT published: tools/quant/reports/xgb_horizons/
XGB_1Y_FINAL_VERDICT.md — full arc synthesis (9 iterations): 3 critical
bugs found+fixed (horizon-mismatch booking, scrambled ret_next, 292-name
universe), final numbers (1y XGB d3: 12m-hold SR 1.03-1.10 ann +21-25%,
staggered deploy 1.06 market-neutral, 24m 0.96, $20M ADV 0.73), deployment
recipe (Jan refit, quarterly Feb/May/Aug/Nov cohorts, 12m fixed-book holds,
px>=2 + ADV floor, 48bp/cohort/yr costs, current book LONG ACAT/INTC/ORCL/
WOLF/MU/CHTR...), caveats (n=17 cohorts, smaller-name capacity). The 1y
research arc is COMPLETE: the strategy is real, robust, and deployment-
ready; remaining risks are operational (data refreshes, refit cadence).

## 2026-08-20 (/loop 1y-xgb iter8) — depth-3 wins everywhere; tuned stack finalized; blend verdict revised
Depth-3/slow-lr helps the 1m target too: XGB EW net 0.76 -> 0.84 (ann
+18.2%); promoted to gkx_backtest default (Ridge 0.93 still 1m champion).
Tuned 1y re-validation: 12m-hold 1.03 (ann +20.8%), 24m 0.96 (dd -8.9%),
quintile 1.04, $2 floor 1.05, ADV floors improved ($20M: 0.63 -> 0.73,
ann +15.5%; $50M 0.64). Live book: LONG ACAT/INTC/ORCL/WOLF/MU/CHTR/HUM/
TSLA/PANW (chips + beaten-down).
BLEND VERDICT REVISED: with the tuned 1m model, monthly 50/50 blend 0.80
< pure 1m 0.83 — blending dilutes; horizon-matched models only (the
earlier blend win was the undertuned 1m leg). Final stack (net, full
universe): 1m Ridge 0.93 / 1m XGB 0.84 monthly; 1y XGB 1.03-1.10 annual,
deploy 1.06; $20M ADV 0.73. XGB_1Y_LS.md iter8 section.

## 2026-08-20 (/loop iter27) — retro n=39 converged; arb batch 96/3,660
Retro chunk 19: n=39 (1m -0.6% vs -4.7%, 3m -3.5% vs +0.1%, 6m -6.7% vs
-1.7%) — converged, no change. Arb batch scaled to 96 processed deals
(rate ~3.5s/filing; full 3,660 = ~10 more fires — downgraded to
background nicety since the n=44 distribution is already decisive).
Verdict, reports, and deliverables all final; remaining fires are pure
CI tightening on both streams.

## 2026-08-20 (/loop 1y-xgb iter7) — TUNED: depth-3 XGB doubles IC to 0.118; 12m-hold SR 1.10, deploy 1.06
Hyperparameter sweep on the 12m target (full universe, PIT): d6/mcw20 0.75,
old d4 0.93, d3/lr.02/600t -> 12m-hold entry-02 SR 1.03-1.10 (ann +24.8%,
dd -15.3%), IC 0.062 -> 0.118 (IC-IR 3.43), 1m-hold 0.70, staggered deploy
SR 1.06 (ann +16.4%, dd -22.8%, 15/18 yrs positive). Config promoted to
default; champion parquets regenerated.
Signal profile shifted: ret_m1 now top feature + ret_12_1 + macro-
conditional momentum — the full universe's smaller names carry the
momentum/reversal dynamics the subset model lacked.
BLEND VERDICT by holding period: 12m-hold pure 1y 0.75 >> blend 0.43 >
pure 1m 0.21 (1m signal decays at long horizons); monthly blend 0.68 >
1m 0.66. Rule: 1y prediction alone for 12m holds; blend only for monthly
rebalance. XGB_1Y_LS.md iter7 section.

## 2026-08-20 (/loop 1y-xgb iter6) — full-universe stress: edge HOLDS at $20M ADV; $2 floor IMPROVES SR to 0.99
Horizon profile (full universe, net): 3m 0.78 / 6m 0.88 / 12m 0.93 (ann
+18.1%, dd -18%) / 24m 0.82 (dd -7.9%, 15/16 yrs positive). 12m sensitivity:
4x costs 0.89; quintile 0.84 (dd -13%); PIT $2 floor -> SR 0.99 (sub-$2
names are noise, not signal); ADV floors $1M/$5M -> 0.73, $20M -> 0.63
(ann +13.2%) — tradeable at institutional capacity. Entry-month sweep:
XGB 0.72-0.93 all four conventions (champion); Ridge 0.36-0.87 unstable.
Live book 2026-08-31: 803/885 >= $2; LONG WOLF/ACAT/CHTR/HUM/FTNT/GOOGL/
ADBE/TSLA... Final 1y verdict: net SR ~0.6-1.0 across schemes (0.93 annual
hold, 1.02 staggered, 0.63 at $20M ADV), ann ~13-18%, market-neutral, no
disaster years (worst 2012 -12.1%). XGB_1Y_LS.md iter6 section.

## 2026-08-20 (/loop 1y-xgb iter5) — UNIVERSE BUG: backtests ran on 292 names; FULL-UNIVERSE numbers 2-3x BETTER
pc.load_ohlcv() = twelve_big only (~292 tickers), but the panel holds 913
(union of 6 local panels). All label joins (fwd12/ret_next/px) silently
restricted iters 1-4 to the 292-name subset; the v14 GKX rerun too. Fixed:
all loaders -> union_panel.load_union() (1,097); panel ret_next rebuilt
from union with sane-tail filter (cov 50%->85%, CSCO identity verified).
FULL-UNIVERSE RERUNS (OOS 2009-2026, decile L/S net):
  GKX 1m: Ridge EW SR +0.93 (ann +14.1%), XGB +0.76 (ann +14.6%) — was
  0.61/0.57 on the subset; approaches GKX's VW 1.35 gross on free data.
  1y XGB PIT: 1m-hold +0.58; 12m-hold +0.93 (ann +18.1%, dd -18%);
  staggered deploy SR +1.02 (ann +14.6%, dd -25.9%, beta -0.06,
  market-neutral; worst year only -12.1% — breadth softened 2021/22
  from -24%/-37%).
  BLEND: 1m+1y 50/50 monthly SR +0.68 (ann +12.5%) — now BEATS both pure
  legs (0.66/0.58; corr dropped to 0.68 on the full universe).
Best free-data results on the desk: 1m GKX replication net SR ~0.8-0.9,
1y staggered deploy net SR ~1.0, ann ~14-15%, on verified-clean labels
and the correct ~900-name universe. Artifacts: loaders patched
(xgb_1y_ls/deploy/profile, gkx_backtest), XGB_1Y_LS.md iter5,
GKX_REPLICATION.md v15.

## 2026-08-20 (/loop iter26) — retro n=37: CONVERGED (3m -3.9%, 6m -6.8%)
Chunk 18: n=37, stats stable vs n=35 (1m -0.6% vs -4.5%, 3m -3.9% vs
+0.5%, 6m -6.8% vs -1.3%). Estimate CONVERGED: formula net-nets
underperform the base cohort by ~4-5.5pp at 3-6m, flat at 1m. Remaining
~1,425 candidates; no further verdict changes expected.

## 2026-08-20 (/loop 1y-xgb iter4) — PANEL BUG: ret_next was SCRAMBLED (stack().shift(-1)); true results BETTER
CRITICAL bug found while building the deploy backtest: the monthly panel's
ret_next was built via mret.stack().shift(-1) — shift on a stacked MultiIndex
moves by ROW POSITION, scrambling returns across tickers. Proof: CSCO
Feb-2020..Feb-2021 prod(1+panel ret_next)=+105.7% vs true +11.7% (raw CSV;
the 1y fwd12 join said +12.4%). Contaminated: all GKX 1m results (v1-v13),
1m-hold stats, deploy slices. CLEAN: all 12m-forward results (independent
fwd12 join, models never touch ret_next). Fixed builder + panel parquet
(identity verified) + gkx_backtest/xgb_1y_ls loaders.
RERUNS: (a) GKX 1m replication: TRUE numbers BETTER — Ridge EW net SR +0.61
(ann +9.9%), XGB +0.57 (ann +10.0%) vs contaminated 0.54/~0.09: the scrambled
label was SUPPRESSING the edge; XGB's 1m weakness was mostly the bug. New
free-data 1m ceiling: net SR ~0.6, ann ~10%. (b) 1y 1m-hold flips -0.68 ->
+0.29 (the 'monthly mean-reversion' story was an artifact). (c) Deploy
(quarterly staggered, 12m hold, 67 cohorts, fixed books): SR +0.42, ann
+5.9%, win 62%, dd -64.6% (2021-22), beta +0.05 — market-neutral. 12m-hold
numbers unchanged (0.34). 1m-horizon XGB (SR 0.57) remains the desk's best
monthly-rebalanced strategy; the 1y signal is the hold-12m variant. Artifacts:
xgb_1y_deploy.py, gkx_1y_deploy_monthly.csv, XGB_1Y_LS.md iter4,
GKX_REPLICATION.md v14.

## 2026-08-20 (/loop iter25) — retro n=35: estimate sharpens to MILDLY NEGATIVE
Chunk 17: n=35. ret_1m -0.5% (median -6.3%) vs all -4.4%; ret_3m -4.7%
vs +0.7%; ret_6m -7.0% vs -1.5%. Trajectory vs n: 3m (+0.5 -> -2.4 ->
-0.7 -> -4.7), 6m (+2.1 -> -3.9 -> -2.1 -> -7.0). The "zero alpha" estimate
has moved to MILDLY NEGATIVE with sample growth — formula net-nets now
underperform the base cohort by ~5pp at 6m. Verdict report section 3
update: zero-to-slightly-negative alpha, high variance. Remaining ~1,465
candidates (~37 fires) will pin the CI.

## 2026-08-20 (/loop 1y-xgb iter3) — HORIZON PROFILE + LIVE BOOK; edge survives $2 floor, not penny artifact
New xgb_1y_horizon_profile.py (no retraining, reuses PIT preds). Fixed 3 infra
bugs: (1) label-drop cutoff hid preds beyond 2025-08 -> predictions now run
through the latest refit block (live book enabled, 2026-08); (2) NaN-label
join-miss rows zero-weighted into cohorts (pandas sum skipna) -> per-group
label dropna; (3) profile's destructive shared-frame tail filter -> per-horizon.
HORIZON PROFILE (same preds, EW decile L/S net): 1m -0.68 / 3m +0.27 / 6m
+0.34 / 12m +0.34 / 24m +0.43 (win 81%, 13/16 yrs positive; 2nd year adds
more than the 1st: +7.8% -> +18.1% per window — slow-burn value/reversal).
SENSITIVITY: costs near-irrelevant (96bp -> SR 0.31); quintile 0.36 dd -47%;
PIT $2 price floor -> SR 0.32: the edge is NOT a penny-stock artifact.
LIVE BOOK 2026-08-31 (291/885 names >= $2): LONG LCID/HUBS/DOCU/CHTR/RIVN/
CLF... (beaten-down growth), SHORT KO/COST/WMT/JPM/XOM... (stable megacaps).
Artifacts: gkx_1y_live_book_2026-08-31.csv, gkx_1y_profile_{3,6,12,24}m.csv,
XGB_1Y_LS.md iter3 section.

## 2026-08-20 (/loop iter24) — RESEARCH ARC COMPLETE: final report + retro n=31
Retro chunk 16: n=31 (1m +0.4% vs all -4.5%, 3m -0.7% vs +0.7%, 6m -2.1%
vs -1.3%) — verdict stable with sample growth: formula net-nets ≈ zero
alpha, high variance. ARB leg finalized: n=44 distribution (77% efficient
spreads <10%, median +1.6% ≈ 3-10% annualized; big-spread cohort -4.9%).
FINAL REPORT tools/quant/reports/BUFFETT_SMALLCAP_VERDICT.md updated
(sections 4.5, 6, 7): executable deliverables = 5 reusable scripts
(edgar_full_fetch, build_full_cache, buffett_full_screen, buffett_retro,
buffett_arb_screen) + data assets (7k raw XBRL, caches, deals). One-line
verdict: Buffett's 50% is real; free data reproduces only the "boring"
parts (arb 3-10%/yr, net-nets zero alpha); the 50% lives in the
non-reproducible qualitative layer; S&P500 index for everyone else.
Remaining: retro ~1,505 candidates (CI tightening only), arb batch scale.
(Note: RESEARCH_LOG top now shared with a parallel 1y-xgb loop thread.)

## 2026-08-20 (/loop 1y-xgb iter2) — LEAK-FREE rerun: XGB PIT net SR ~0.4 (annual hold) SURVIVES
Honesty checks on iter1: (1) dropped the 10 Finnhub current-snapshot features
(marketCap/pe/pb/roe/growth/turnover/debt_eq/div_yield/log_mcap tiled back
through history) -> 47 point-in-time chars. (2) annual-cohort entry-month
sweep Feb/May/Aug/Nov.
RESULTS: XGB PIT EW 12m-hold net SR 0.34/0.45/0.51/0.38 by entry month
(ann ~5.5-9%, win 71-82%) — positive at EVERY entry month, so NOT a
lookahead artifact. The snapshot leak ~doubled the headline (full-set XGB
0.46-0.57) and ~half the IC (0.108->0.063). XGB stable across entry
conventions (0.34-0.51); Ridge swings 0.10-0.86 with an ann-nan year —
XGB confirmed champion. Monthly 1m-hold still negative under PIT (-0.68):
the strategy IS a 1-year hold, full stop. Honest headline: XGB PIT EW
decile L/S annual hold net SR ~0.4, ann ~6-9%, OOS 2009-2026. Artifacts:
gkx_preds_{xgb,ridge}_1y_pit.parquet, XGB_1Y_LS.md iter2 section,
gkx_1y_results.json (per-entry-month stats).

## 2026-08-20 (/loop 1y-xgb iter1) — XGB 12-MONTH-FORWARD prediction: L/S net SR +0.57 (annual hold)
Extended the GKX monthly panel (57 chars, ~885 investable names) to a
12-month forward-return target with purged walk-forward XGB (+ Ridge ref).
CRITICAL BACKTEST BUG CAUGHT: booking the realized 12m return as a monthly
return compounds a year's P&L every month -> EW ann +297%, maxDD -99.3%
(garbage). Fixed: 1m-hold booking for monthly rebalance, annual-cohort
booking for 12m hold.
RESULTS (OOS 2009-2026, decile L/S): monthly-rebalanced 1m-hold LOSES
(XGB EW net SR -1.07; short-term reversal of the signal). Annual 12m-hold:
XGB EW net SR +0.57 (ann +9.7%, win 71%, dd -49.6%, 12/17 positive years);
Ridge +0.30; VW ~zero. XGB > Ridge at 1y (inverts the 1m ranking) — the
strongest XGB result on the desk.
NOT MOMENTUM: 12m-momentum control lost -104.8% in the 2009 crash vs XGB
+26.3%; importances = vol/liquidity/size/macro + few fundamentals, no
momentum in top-15. Loss years are 2021/2022 (value era). Caveats: 7
Finnhub snapshot fundamentals tiled back in time (leak shared with GKX 1m
infra); n=17 annual cohorts. Artifacts: bigmove/xgb_1y_ls.py,
gkx_preds_{xgb,ridge}_1y.parquet, reports/xgb_horizons/XGB_1Y_LS.md +
gkx_1y_results.json + annual equity CSVs.


## 2026-08-20 (/loop iter23) — ARB n=44 FINAL DISTRIBUTION: 77% efficient; big spreads lose
Batch scaled to 160 filings -> 53 deals -> 50 with spreads (artifacts
filtered to 44). ACTIONABLE SPREAD (post-announcement, ann+3d) distribution:
  spread <10%: 34/44 (77%), median +1.6% — market prices announced deals
      efficiently; the arb earns the boring 5-15% annualized per deal.
  spread >=10%: 10/44 (23%), mean ret_to_now -4.9% — CYCU -99%, LPSN
      -87%, SOUN -64%, WU -31%, CRBD -13%, SYBX -13% vs winners PSNL
      +152%, DAWN +69%, BCRX +29%, MACI +8. Big spread = break risk;
      formula-buying big spreads LOSES on average.
FINAL ARB VERDICT: 策略三 is the only leg with a reproducible positive
edge (median 1.6% per deal, ~5-15% annualized, low vol when restricted
to the <10% cohort), but it is NOT 50%/yr — Buffett's workouts made low
double digits; the 50% came from concentrated value. Selecting among big
spreads requires the qualitative layer (financing, terms, regulatory).
Report section 4.5 finalized with the n=44 distribution.

## 2026-08-20 (/loop iter22) — ARB CORRECTED: actionable spreads ~1-3%; huge spreads = noise
Batch scaled: 60 filings -> 18 deals; spread module built (poly_cache.json,
no re-fetch). CRITICAL CORRECTION to iter21: ret_to_now measured from the
PRE-announcement close — fictitious (you can't buy before the news). With
the post-announcement (ann+3d) price as entry:
  REAL CASH MERGERS (11): actionable spread 0.8-5.8%, mean ~+1.7%
      (ALOT +1.5, HZO +1.0, DAWN +0.8, KORE +2.9, FONR +2.4, ESPR +1.3,
      SEM +1.5, CWAN +1.9, TRUE +5.8, EEX +0.8, GES -0.5) — the market
      prices announced cash deals EFFICIENTLY; the arb earns ~5-15%
      annualized per deal over the close horizon.
  HUGE SPREADS = BROKEN/NOISE (3): WU +91.4% (never believed, -31% to
      now), SOUN +72.4% (financing floor, -64.5%), LPSN +541.7% (not a
      merger — financing terms, -86.8%). Exactly the class Buffett's
      "announced + financed + low break risk" filter removes.
VERDICT for 策略三: the arb leg IS the one with a positive edge, but it
is a boring 5-15% annualized grind (matching Buffett's partnership
workouts record — low double digits, near-zero vol), NOT 50%. The 50%
came from concentrated value bets. Report section 4.5 added. Retro
parallel stream continues (n=28).

## 2026-08-20 (/loop iter21) — ARB CONVERGENCE: 6/7 deals captured spread in 60d
Buy-at-announcement -> +60d realized returns (Polygon, per deal):
  TRUE +56.8% (spr@ann 72%), SEM +9.7% (10%), HZO +46.4% (48%), FONR
  +26.1% (30%), ALOT +73.1% (74%), LPSN +48.5% (519% spr — market prices
  near-certain break; stock rallied but stays 4x below deal)
  WU -4.2% (88% spr from day one — the only loser; market never believed
  the $16 deal; stayed broken at ~$8).
MEAN of live deals +43% over 60d. The spread at announcement IS the
market's break-discount; sane-spread deals mostly converged, the never-
believed deal (WU) stayed dead. LPSN shows the tail risk — huge spread =
huge break probability, but the +48.5% shows even the "dead" ones bounce.
CAVEATS: n=7, sample = first 30 hits (recent-biased), 4 deals appear
CLOSED (TRUE/SEM/FONR/ALOT trade at deal price) — survivorship-ish
selection; full 3,660-filing batch needed for the real distribution.
RETRO n=28 (chunk 14): 1m +0.7% vs all -4.6% (first 1m beat), 3m -2.4%
vs +0.9%, 6m -3.9% vs -1.6% — verdict unchanged (~zero alpha, high
variance; wobbles with chunks).

## 2026-08-20 (/loop iter20) — ARB FIRST BATCH: spread distribution is BIMODAL
Refined extractor (par-value boilerplate filtered, max-plausible rule) on
30 filings -> 9 deals with per-share prices. Spreads vs current price:
  CONVERGED (5): TRUE +0.4%, SEM -0.1%, HZO +1.5%, FONR -0.5%, ALOT +0.4%
      — trade essentially AT deal price (arb played out / deal closed)
  BROKEN / AT-RISK (3): LPSN +316.7% ($12 deal vs $2.88), WU +122.2%
      ($16 vs $7.20 — Western Union), SOUN ~+60-68% ($12 vs $7.16)
CORE FINDING: the arb spread is BIMODAL — converged deals sit near zero
residual; broken deals show catastrophic gaps (market -70-80% from deal).
A naive "buy every announced deal" strategy gets wrecked by the broken
tail — precisely Buffett's rule ("only announced, financed deals, minimal
break risk") and his practice of treating each workout on its own
probabilistic merits. LPSN/WU are the modern textbook cases of announced-
deal death. Next: convergence analysis (price at announcement -> +30/60d)
to measure realized capture and the cost of the broken tail; then scale
batch over the 3,660 hits.

## 2026-08-20 (/loop iter19) — ARB BUILD: collector + extractor working (SOUN case!)
buffett_arb_screen.py step 1 DONE: 3,660 merger-agreement 8-Ks collected for
2025-08-01..2026-08-20 via EFTS pagination (resilient, incremental saves).
Step 2 (8-K text + deal terms) works: index.json listing -> main doc ->
regex. Pitfalls fixed: CIK zero-pad (500s), index.json explicit, main doc
selection ("8k" in name, largest .htm), EFTS 500 retries.
FIRST SPREAD READ: SOUN (SoundHound) 8-K 2026-07-02 says $11.50/share;
Polygon last close $7.16 -> +61% spread. Either a BROKEN deal (the arb
nightmare — why Buffett only did "announced, financed" deals) or the
11.5 is a stock-exchange-ratio/other term mis-extracted. MCW/ARX prices
checked; extractor caught legal boilerplate ("par value of $0.01 per
share") — refinement needed: exclude par-value context, prefer max
plausible per-share price. Next: refined extraction over a batch, spread
distribution, classify live vs broken deals.

## 2026-08-20 (/loop iter18) — retro n=25; ARB LEG (策略三) feasibility CONFIRMED
Retro chunk 12: n=25, stats unchanged (1m -8.1% vs -5.6%, 3m +0.3% vs
+1.4%, 6m +1.7% vs -1.3%). Verdict locked.
ARBITRAGE LEG reconnaissance (the last untested playbook leg — Buffett's
"workouts"): SEC EDGAR full-text search (efts.sec.gov) WORKS for deal
announcements — "merger agreement" in 8-Ks: 1,561 hits in 2026-06-01..
08-20 (~7k/yr). Hit structure: adsh (accession), file_date, display_names
(with ticker in parens), items, ciks. NOTE: display name is often the
ACQUIRER; the arb target ticker must be parsed from filing text. Pipeline
(planned): paginate EFTS 1y window -> fetch 8-K main doc -> regex per-share
deal price + target -> Polygon price -> spread + convergence. Task #4
created. This is the leg that historically WORKED for Buffett (workouts
~10% of partnership returns, near-zero variance) and is implementable on
free data (unlike the qualitative net-net layer).

## 2026-08-20 (/loop iter17) — retro n=24: 12m horizon now measured (~flat)
Chunk 11: n=24. ret_1m -8.1% (median -10.0%) vs all -5.6%; ret_3m +0.5%
vs +2.7%; ret_6m +2.1% vs -0.3%; ret_12m +0.3% vs -0.5% (n=24 — 12m now
has full coverage). Verdict locked: net-nets underperform at 1m, flat at
3-12m. Zero relative alpha. ~1,625 retro candidates left (~41 fires).
Nothing structural changes from here; fires just tighten CIs.

## 2026-08-20 (/loop iter16) — CORPUS 100%: final census 6 net-nets; retro n=23
FETCH COMPLETE: 7,994 CIKs fully processed = 6,985 XBRL files + 1,009
no-XBRL (funds/delisted). Final full-universe census: 4,158 names with
NCAV inputs, 1,672 NCAV>0, SIX clean net-nets (BIYA 7.51x, ENLV 3.29x,
IMA 2.03x, CYPH 1.16x, KROS 1.10x, OKUR 1.03x) + 9 near-misses (new:
GME 0.68x — GameStop, $8.1B mcap vs $7.4B cash, an odd large-cap cash
special). Ladder intercepts: 15 shares-artifacts, 1 ratio-artifact (UPC),
3 stale (DDI, HTT, ACMR). Verdict report updated to final census.
RETRO n=23 (chunk 10): ret_1m -8.6% (median -14.6%) vs all -6.0%;
ret_3m +0.6% vs +2.1%; ret_6m +1.9% vs -1.0%. Verdict unchanged:
formula net-nets underperform at 1m, ~flat thereafter. ~1,665 candidates
left (~42 fires). The quantitative research arc is COMPLETE at the
population level; remaining fires only tighten retro CIs.

## 2026-08-20 (/loop iter15) — VERDICT REPORT published; retro n=20 definitive
Corpus 6,755/7,994 (84.5%). RETRO n=20 (chunk 9): ret_1m -10.0% (median
-17.6%) vs all -6.0%; ret_3m -1.2% vs +1.4%; ret_6m +0.0% vs -1.5%.
VERDICT DEFINITIVE: formula net-nets UNDERPERFORM the base cohort at 1-3m,
flat at 6m. The iter10-14 "weak edge" was sample noise (n=20 kills it).
DELIVERABLE: tools/quant/reports/BUFFETT_SMALLCAP_VERDICT.md — full
synthesis: claim verification table (50%/yr quote REAL, Moody's 20k pages
REAL, three examples real with garbled numbers), data infrastructure +
4-layer quality ladder, full-universe census (6 clean net-nets of 7,994 =
0.1%; cash specials are a subset), retro evidence, integration with
iter1/iter2 (no micro-caps in priced universe / flat value factor), and
the final verdict: formula = zero-alpha high-variance; the edge lives in
the qualitative layer after the screen (ENLV deal closure, BIYA burn
rate) — matching Buffett's own narrative; S&P500 index for everyone else.
Remaining: corpus finishes (1-2 fires), retro ~1,630 candidates (~40
fires), optional merger-arbitrage leg (策略三) untested.
Loop re-scheduled (old job cancelled): 5ec1cf29, */10 * * * *.

## 2026-08-20 (/loop iter14) — shares-staleness fix; retro n=19 confirms ~zero alpha
Corpus 6,663/7,994 (83.3%). RETRO n=19: ret_1m netnet -9.4% vs all -5.9%;
ret_3m -0.3% vs +3.1%; ret_6m +1.1% vs -0.2%. iter13's correction CONFIRMED:
net-nets now slightly UNDERPERFORM at 1-3m; 6m within noise. Final verdict
shaping: pure-formula net-net ≈ zero-to-slightly-negative alpha, huge
variance. The edge seen at n=10-14 was sample luck.
FOURTH data-quality fix — SHARES STALENESS: ACMR (ACM Research) showed
1.21x net-net with fresh 2026-06-30 balance sheet but shares from
2019-03-08 (14.2M vs ~62M real) -> real ratio 0.28x. Screen now flags
shares filed >400d before the NCAV period (excluded from count; retro
skips shares >180d before report). Full data-quality ladder now:
(1) period-aligned NCAV triple (DDI), (2) ratio>20x artifact flag (UPC),
(3) shares<10k sanity (FOXA), (4) shares staleness (ACMR). Clean live
net-nets: 6 (BIYA, ENLV, IMA, CYPH, KROS, OKUR); stale-flagged 3.
CASH-SPECIAL census (Union-Street-Railway type, mcap<cash): 3 real names
(IMA 1.47x, KROS 1.17x, OKUR 1.01x) — all already in the net-net list;
cash specials are a subset, not a separate opportunity set.
~1,511 retro candidates left (~38 fires).

## 2026-08-20 (/loop iter13) — retro n=18: EDGE WEAKENS back to ~noise
Corpus 5,805/7,994 (72.6%; progress: 5,720 done + 831 no-XBRL errors; fetch
alive 79min continuously). Chunk 7 added 4 net-nets (n=18). CUMULATIVE:
ret_1m netnet -7.5% (median -10.0%) vs all -6.0%; ret_3m +2.3% vs +2.8%;
ret_6m +3.7% vs +0.3%. The 3m/6m edge SHRANK vs n=14 (+7.1/+8.9) — it
wobbles with the sample (n=10: +4.0/+6.5; n=13: +8.9/+10.9; n=18:
+2.3/+3.7). 1m consistently slightly-negative vs base (-0.5..-7.5).
HONEST READ: no robust formula edge; at best ~zero alpha at 3-6m with
massive variance (1m range -42%..+40%). The "weak positive edge" from
iter10-12 was sample noise, not signal. Converging verdict: pure-formula
net-nets ≈ zero-alpha high-variance; value is in the qualitative layer
after the screen. ~1,457 retro candidates left (~36 fires); target final
n ~40-60 net-nets will tighten the CI.

## 2026-08-20 (/loop iter12) — retro n=14: edge persists; corpus 71.2%
Corpus 5,745/7,994 (71.2%). Live screen: 7 clean net-nets (UPC now
artifact-flagged as designed): BIYA 7.51x, ENLV 3.29x, IMA 2.03x, ACMR
1.21x, CYPH 1.16x, KROS 1.10x, OKUR 1.03x. Near-misses 8 (new QFIN 0.83x
— Qifu Technology). 4,007 names with NCAV inputs; 1,551 NCAV>0.
RETRO n=14 (chunk 6 added APRE 3.77x -20.9% 1m): ret_1m -4.8% vs all
-6.0%; ret_3m +7.1% vs +3.3%; ret_6m +8.9% vs +0.8%. 6m cohort: 6
positive (ASBP +47.9, ADVB +83.1, AIFA +32.3, ATOS +36.8, CCTG +49.7,
ACRV +34.3), 7 negative (BBLG -53.3 deepest). Edge stable across 6
chunks; high variance persists (1m range -42%..+40%).
~1,470 retro candidates left (~37 fires at 40/fire). Corpus completes
next 1-2 fires; then full-universe live count is final.

## 2026-08-20 (/loop iter11) — retro n=13: 3m/6m edge STABILIZES (~+7-9pp)
Corpus 4,950/7,994 (61.3%). Live screen: 8 clean net-nets — BIYA 7.51x,
ENLV 3.29x (asset-sale special), IMA 2.03x, ACMR 1.21x (NEW, cash $969M),
CYPH 1.16x, KROS 1.10x, OKUR 1.03x; +7 near-misses (HUYA, JANX 0.84x NEW,
SION, CRON, MBLY, INGN, TRS).
ARTIFACT FILTER ADDED: UPC showed 13,439x (mcap $3M vs NCAV $40.4B) —
verified as XBRL tag garbage (Universe Pharmaceuticals: $53.6B cur_assets
for a 563K-share Chinese micro; also cash tag from 2022). Screen now flags
ratio>20x as artifact (excluded from count); retro skips them too.
RETRO CHUNK 5 (resilience added: polygon retry x3, SSL-tolerant; +3
net-nets: ACET 1.15x +4.9% 1m; ACRV 1.04x -14.6% 1m -> +34.3% 3m; AIFA
1.35x -31.4% 1m -> +32.3% 3m — the 1m dip-then-rerate pattern repeats).
CUMULATIVE n=13: ret_1m netnet -3.5% vs all -6.9%; ret_3m +8.9% vs
+3.7%; ret_6m +10.9% vs +1.8% (median +9.8%). SIGNAL: net-nets roughly
match the base at 1m (huge variance -42%..+40%) and BEAT it by ~7-9pp at
3/6m across 5 chunks (only chunk 1, shell-heavy A*, was net-negative).
Caveats: n=13, mostly A-C names (SPACs/shells/biotechs), 2026-06-30
reports truncated at ~2m of forward data. Remaining ~1,300 candidates.

## 2026-08-20 (/loop iter10) — RETRO CORRECTED (n=10): flat at 1m, + at 3m/6m
Corpus 3,984/7,994 (49.8%). DATA BUG FOUND: buffett_retro.py OVERWROTE
retro_screen.json each run (only latest chunk kept); chunks 1-2 rows lost.
Recovered by clearing the done manifest and re-running against the cached
history (zero API calls) + merging. CORRECTED CUMULATIVE (chunks 1-4, 92
rows, 10 net-nets at report date):
  ret_1m: netnet mean -0.5% median +1.2%  | all -7.6%
  ret_3m: netnet mean +4.0%                | all +2.0%
  ret_6m: netnet mean +6.5%                | all +0.2%
  Winners 1m: ADVB +17, ASBP +26, ATOS +13, BTCT +5, CCTG +40
  Losers 1m: ACON -30, AEMD -31, BBLG -37, BCYC -5, BON -3
REVISED READING vs iter8: the "all net-nets die" result was chunk-1-only
(A* shell-heavy: ACON/ASNS/ATPC/AUUD sub-$5M shells, ASNS $0.076/sh).
Full A-D sample: net-net cohort is FLAT at 1m (≈0 mean, huge variance
-42%..+40%) and BETTER than the base cohort at 3m/6m (+4-6.5% vs
+2.0/+0.2%). Longer-horizon names (report >= 2026-03-31): ADVB +83% 6m,
CCTG +50% 6m vs BON -34%, BTCT -27% — split, not one-sided. Caveats: n=10
tiny; most 2026-06-30 reports have only ~1.7mo of forward data (3m==6m
values are truncated); huge variance = position sizing matters.
VERDICT SHIFTING: no death-sentence for the formula; more like
zero-alpha-high-variance — the edge (if any) comes from WHICH net-nets
(qualitative leg), exactly Buffett's 20,000-page thesis. ~780 candidates
left (~20 fires). Retro file now append-mode (dedup by ticker).

## 2026-08-20 (/loop iter9) — retro n=6: 5/6 net-nets lost; corpus 28.5%
Corpus 2,279/7,994 (28.5%) — fetch ran hot across the gap (4-worker nohup;
+1,400 files in ~10 min). Live screen: 6 clean net-nets, new ENLV 3.29x
(Enlivex: NCAV $1.35B vs mcap $411M — but cash only $1.9M; the balance
sheet reflects a 2025 asset sale (NI +$1.24B); cur_assets likely a sale
receivable. A real "asset-sale special" IF the deal proceeds are real —
needs qualitative check = the 20,000-page leg). New near-misses: CRON
0.66x (cannabis, cash $467M), TRS 0.54x (cash $1.24B).
RETRO CHUNK 2 (33 processed, 558 left): 2 net-nets at report date — AEMD
1.56x -31.3% (1m), ATXG 5.22x +16.5% (1m) / +24.4% (3m) — FIRST POSITIVE.
CUMULATIVE retro n=6: 5 lost (mean 1m -21.6% across 6; chunk2 base cohort
+7.2% at 3m vs net-net -4.0% — underperformance not a down-market
artifact). Single winner ATXG is a Chinese micro (same 无人区).
Pattern so far: formula net-nets are mostly broken shells priced for death;
occasional re-rater. n grows 30-40/fire; ~14 fires to exhaust.

## 2026-08-20 (/loop iter8) — RETRO VALIDATION: net-nets at report date ALL LOST
Corpus 843/7,994 (10.5%). Live screen: 5 clean net-nets (BIYA 7.51x, IMA
2.03x, CYPH 1.16x, KROS 1.10x, OKUR 1.03x) + 4 near-misses (HUYA 0.90x,
SION 0.70x, MBLY 0.63x, INGN 0.55x).
INTERIM VALIDATION (live list, polygon prices): ret since report period —
BIYA -94.9% (7.6mo), SION -85.5%, HUYA -23.8%, INGN -18.0%, OKUR -9.3%,
IMA -6.3%; CYPH +68.5%, MBLY +16.5%, KROS +1.6%. Deepest discounts fell
most. CRITICAL WINDOW MISMATCH: names crashed INTO cheapness AFTER their
report — at report date BIYA was 0.39x (NOT a net-net). Live screen mixes
today's price with the latest balance sheet; that's correct for buying,
but not for measuring the strategy.
NEW RETRO LEG (buffett_retro.py): at each report period, recompute ratio
with the THEN price + shares as of the report filing; measure forward
returns. FIRST CHUNK (28 of 205 NCAV>0 names, alphabetical A* — shell/
SPAC-heavy): 4 were net-nets at report date — ACON 1.90x, ASNS 2.70x
($0.076/sh!), ATPC 7.38x, AUUD 1.13x. ALL FOUR LOST: 1m mean -28.7% (each
-20 to -42%), 3m -21.6% vs all-name cohort -5.0%/-3.4%. Net-net cohort
underperformed the base at every horizon. Formula-bought names were priced
broken for a reason (dilution/delisting); the screen finds them, the market
knows why they're cheap. Consistent with: US net-net edge largely gone
post-2000s (survives in Japan/China micros per literature); iter2 value-
factor-flat finding. NOTE: chunk 1 is shell-heavy (A-names, sub-$5M
mcaps) — n will grow over fires; live-screen list validation on the
$50-200M band (HUYA/MBLY band) shows mixed-to-positive so far.
MECHANICS: Finnhub candle endpoint = 403 on free tier (quote only);
yfinance still IP-throttled; POLYGON free tier WORKS for 2y daily aggs
(5 req/min, ~12.5s spacing, history cached in data/history_cache.json) —
now the validation price source. Fetch at 843 files, 4 workers, ~76/min.

## 2026-08-20 (/loop iter7) — 5 net-nets at 629 files; FETCH 4x SPEEDUP
Corpus 629/7,994 (7.9%). New net-net: CYPH 1.16x (Cypherpunk Technologies,
crypto SPAC-ish; data fresh 2026-06-30 filed 2026-08-12; cash only $7.6M of
$137.5M cur assets = low-quality NCAV — receivables/crypto-assets heavy).
New near-miss: SION 0.70x (Sionna, biotech). Full clean list: BIYA 7.51x,
IMA 2.03x, CYPH 1.16x, KROS 1.10x, OKUR 1.03x; near-misses SION 0.70x,
MBLY 0.63x, INGN 0.55x. Yield still ~0.8% of corpus.
SPEEDUP: fetch refactored single-thread -> 4 parallel workers (per-worker
2/s, ~8/s aggregate, under SEC's 10/s). Rate 20 -> 76 files/min (~3.8x).
Remaining ~7.4k names ≈ 100 min of active fetch at this rate. Turn-end
suspension quirk (sandbox stops bg procs between turns) means real wall
time is a few hours of loop fires. Threaded fetch also records exhausted-
retry names in errors so runs skip them.
Next: historical validation leg at ~1,500 files — Finnhub 1y candles for
the net-net list (3/6/12m forward returns from screen dates).

## 2026-08-20 (/loop iter6) — 4 CLEAN net-nets at 505 files; DATA-QUALITY FIX
Corpus 505/7,994 (6.3%). Clean point-in-time net-nets (mcap<NCAV, current
report period): BIYA 7.51x (Chinese micro, cash-burn caveat), IMA 2.03x
(ImageneBio, cash $95M), KROS 1.10x (cash-special biotech), OKUR 1.03x
(Onkure, cash $167M). Near-misses: MBLY 0.63x, INGN 0.55x.
DATA-QUALITY BUG FOUND+FIXED: NCAV tags and shares can come from different
report periods (latest-filed per tag). DDI (DoubleDown) looked like 11.2x
net-net: NCAV $351M from 2024-09-30 but shares from 2025-12-31 (massive
post-buyback float shrink) -> inflated ratio = FALSE POSITIVE. Fix: cache
builder now period-ALIGNS the NCAV triple (latest period where all three of
cur_assets/assets/book_equity exist) and the screen flags reports older than
18 months as STALE (excluded from net-net count; DDI now correctly flagged).
Cache format versioned (CACHE_VERSION=2) to force full rebuilds. Stale rate
only 22/340 (6%) — most filers report current tags.
SCALE: cache builder ~8s for 500 files; screen 1-3 min (Finnhub price leg
capped 50/run, cached). Net-net yield so far 4/505 (~0.8%) -> extrapolates
to ~60 in the full 7,994. Next: at corpus ~1,500, run the historical
validation leg — Finnhub candles (1y free) forward returns for the net-net
list; yfinance still IP-throttled.

## 2026-08-20 (/loop iter5) — CLAIMS VERIFIED vs primary sources; screen at 129 files
WEB VERIFICATION of the brief's factual claims (first pass, 3 searches):
  1) "$1M -> 50%/yr guaranteed" — CONFIRMED. BusinessWeek interview (1999):
     "I think I could make you 50% a year on $1 million. No, I know I could.
     I guarantee that." 1999 AM: Buffett ("very slightly misquoted" from a
     Wharton talk) affirmed half a dozen people could compound $1M at 50%/yr
     with full attention via "little tiny areas" (small securities, arb,
     "little wrinkles"); impossible at $100M+. 2024 AM: asked exactly this
     question, answer = go through Moody's 20,000 pages again.
  2) "Moody's Manual 20,000 pages" — CONFIRMED. 2001 AM: "I went through
     20,000 pages in the Moody's industrial, transportation, banks and
     finance manuals — twice." 1993 interview: "learn about every company...
     start with the A's". Transportation manual ~1,500-2,000 pages ("hundreds
     and hundreds of railroad companies") matches brief's ~1500-page claim.
  3) Three famous examples — REAL, numbers garbled across retellings:
     Genesee Valley Gas: price = earnings (~$5/$5, P/E 1; brief says 2).
     Western Insurance (Fort Scott KS): 1993 Columbia talk $12-20 price /
     $16 EPS; Miller/MOI: early-50s personal buy at $3 while earning $29
     (after selling GEICO) — brief's "$3 / $20" is a hybrid of tellings.
     Union Street Railway: 1993 talk $45/sh with $120 cash (Miller: $30-35
     vs $60 NCAV; brief says $30/$100). Verdict: premise TRUE, figures
     approximate — typical of secondary Chinese sources.
SCREEN status: 129 files (1.6% of 7,994), 77 parsed, 22 NCAV>0, 2 net-nets
(BIYA 7.5x, KROS 1.10x — unchanged). Ratio dist: 1x >2x, 1x 1-2x, 16x <0.5x.
Fetch: nohup survives across turns (mechanism semi-reliable; ~6-18 files/min
during turns, ~2/min between); ETA 12-20h for the full corpus at current
rate. Next fires: keep screening; when corpus ~1k+, start historical-price
validation leg on net-net survivors (Finnhub/yfinance history; local panel
won't cover these micros).

## 2026-08-20 (/loop iter4) — FIRST NET-NETS FOUND in full-universe screen
On the first 69 files (0.9% of the 7,994-name universe), the incremental
screen (buffett_full_screen.py) found 2 genuine Graham net-net/cash-special
candidates, point-in-time verified:
  BIYA (Baiya International Group, CIK 1944712): $2.41/sh, mcap $2.86M vs
       NCAV $21.5M = 7.5x NCAV. 2025-12-31 facts filed 2026-04-30. Caveats:
       Chinese micro-cap, cash burn -$9.5M/yr vs NCAV (cigar with ~2 puffs
       left), ~1.2M share float (near-zero liquidity) — the classic
       "smoke but no cigar" profile; also classic Buffett-era setup minus
       the earnings.
  KROS (Keros Therapeutics): mcap $220M vs cash $258M = cash-special at
       1.10x (Union-Street-Railway-style); clinical-stage biotech, dilution
       risk. Not strict NCAV net-net (cur assets 267M vs liab ~21M).
KEY RESULT: iter1's "no micro-caps exist in free data" was an artifact of
the ~530-name priced universe. The FULL SEC population (7,994 filers) DOES
contain net-nets — in exactly the neglected corners Buffett described
(foreign micros, shells, cash-rich biotech). Open questions now: (a) how
many of the full population are net-nets (screen continues as corpus
fills); (b) tradability — floats are tiny, many are Chinese/OTC;
(c) historical validation impossible from local prices — need yfinance/
finnhub history for the survivors (yfinance currently IP-throttled).
MECHANICS: background fetch via run_in_background DIES at turn end
(exit 144 = SIGHUP family); relaunched detached via nohup (pid file
/tmp/edgar_fetch_pid) — survival across fires pending confirmation.
RPS bumped 4->6 (SEC allows 10/s). Pipeline: ~18 files/min while alive.

## 2026-08-20 (/loop iter3) — Buffett $1M/50%: FULL-universe net-net screen UNLOCKED
iter1/iter2 killed the micro-cap net-net premise on the ~530-name priced
universe, leaving one open item: screen the ENTIRE SEC-filer population.
Built the missing machinery this iteration:
  (1) edgar_cik_map_full.json — ticker->CIK for all 16,358 us_stock_list
      entries, resolved via SEC company_tickers.json + company_tickers_exchange
      (normalized matching; earlier map only covered 626). Of the 16,358 list
      entries, 6,840 are current SEC filers; the rest are dead OTC names
      (never-filers, no XBRL possible). CIK-dedup'd SEC population = 7,994
      unique filers — the true full tradable free-data universe.
  (2) edgar_full_fetch.py — resumable companyfacts fetcher for all 7,994 CIKs
      (data/edgar_facts_full/, raw payloads, SEC rate-limit 4/s, 429/404
      handled, progress JSON, deterministic shuffle so early batches are an
      unbiased population sample). RUNNING in background; ~2-4h at avg
      payload sizes. Fixed bugs: norm regex stripped uppercase (all tickers ->
      '') and (cik,ticker) tuple order swapped in main().
  (3) buffett_full_screen.py — per-fire incremental live NCAV screen over the
      growing corpus: NCAV = cur_assets-(assets-book_equity), mcap from local
      price panel or Finnhub quote API (yfinance currently IP-throttled),
      net-net flag mcap<NCAV, output data/full_screen.json.
PIPELINE VERIFIED END-TO-END on first 40 files (megacaps+funds+SPACs mix):
14 parsed, 8 NCAV>0, 8/8 priced via Finnhub, 0 net-nets so far (n tiny).
This is the definitive test iter1 named: if net-nets exist anywhere in free
data, they are in this 7,994-name population. Next fires: re-run the screen
as the corpus fills; then historical validation on the subset with local
price history.

Completed absolute VIX-level gate sweep (full 2001-day OOS, VIX>=level -> scale):
  VIX>=22, f0.0  SR 0.564  DD -19.9%
  VIX>=22, f0.3  SR 0.793  DD -19.9%
  VIX>=25, f0.3  SR 0.793  DD -19.9%
  VIX>=28, f0.3  SR 0.793  DD -19.9%
  VIX>=32, f0.0  SR 0.683  DD -19.9%
  VIX>=32, f0.3  SR **0.855** DD -19.9%   <- best: beats no-filter Sharpe (0.847)
                                                 AND halves maxDD (-33.4%->-19.9%)

Finding: VIX>=32 (true stress regime) + partial de-risk to 30% exposure is the
Sharpe-AND-drawdown optimal risk filter, slightly superior to (a) no filter and
(b) the champion's percentile-0.9/0.5 setting. Lower thresholds (22/25/28)
over-trigger and cost Sharpe sequence ({, so avoided). Implemented as additive
config vix_level_threshold=32.0 / vix_level_factor=0.3.
Deliverable: config.py + backtest.py absolute VIX-level gate (additive, default off).

## Update 2026-08-07 (loop) — data refreshed + champion OOS re-verified on fresh bars

Refreshed both panels (polygon 85 names, twelvedata 90 names) through 2026-08-06
(+2 fresh OOS days). Re-ran champion (tw320d4 full, twelvedata, VIX>=32/0.3 gate):
  OOS Sharpe 0.868 (n=2003), ann_ret 14.2%, maxDD -19.9%, fresh 10d IC last6=+0.016 (flat).
Edge still neutral/flat -> size conservatively; holds prior risk posture.

New: GBRT hyperparameter OOS sweep (the flagged untested lever) in progress on
twelvedata panel. Early (noisy) signal: lower learning_rate helps,
fewer trees hurt:
  base_lr.05 0.466 | lr.10 0.429 | lr.03 0.520 | nest150 0.394

## Update 2026-08-13 (loop) — Hedge-fund suite: full backtest refreshed + multi-strategy refined

- Re-ran `hedge_fund_strats/run_all.py` (21 strategies) + `run_extras.py`
  (blend, vol-managed LS) at 6 bps on free daily data through 2026-08-12
  (fresh panels confirmed 2026-08-12; refresh silent/current). Full
  four/five-category hedge-fund taxonomy now covered with fresh numbers
  (mapping logged in hedge_fund_strats/RESEARCH_REPORT.md addendum).
- Standalone best remains L/S 130/30 (SR 0.80, β1.06); at zero beta the
  multi-strategy EW (w/ statarb) SR 0.50.
- **New refinement**: the standard multi-strategy EW carries the negative
  stat-arb stream. Re-blending with ONLY positive low-correlation streams
  (L/S **vol-managed** + Risk Parity + CTA Futures + FX Carry) DOUBLES the
  full-18y Sharpe (0.50 -> **1.05**) at β≈0.22, MaxDD -11.7% (better than
  -13.0%). Adding AP gold composite keeps SR 1.05 with slightly better DD.
- The polygon LS champion leg lifts the recent-window blend to SR ~2.3 but
  only on a short ~310d common window (LS coverage gap) — flagged indicative,
  not validated. Robust claim is the 4-stream positive-only SR 1.05 on 18y.
- Data free sources re-checked: Stooq still PoW-blocked, yfinance
  rate-limited — the CTA-futures universe expansion (real gold/copper) still
  gated; future reopen would fill the 2000-08 metals gap.

## Update 2026-08-13 (loop) — VALIDATED: multi-strategy IV blend SR 1.24, MaxDD -5.9% (7.5y, 6bps)

Robust, single-source-verified result for the MULTI-STRATEGY category on the
dense 2019-2026 window (n=2054, all 6 bps cost-inclusive, ffill+dropna,
computed with df.dot(weights)):

  Hedge-pos 4 EW (L/S volman+RP+CTA+FX)      SR 1.05 ret 9.4% MaxDD -11.7%
  +AP gold + LS n10r14 EW                    SR 1.10 ret 8.3% MaxDD -9.0%
  +AP gold + LS n10r14 IV   <BEST>           SR 1.24 ret 6.1% MaxDD -5.9%

  IV sub-period 2019-2022: SR 1.48 (DD -5.2%) | 2023-2026: SR 1.01 (DD -5.9%)
  (positive in BOTH halves — no regime flip)

Mechanism: inverse-vol gives ls_n10r14 weight 0.38 + fx_carry 0.20 (the two
lowest-vol, near-independent legs), cutting MaxDD ~5.5pp while raising Sharpe
vs EW. The LS n10r14 stream is the strongest diversifier (mean|corr| 0.12).
This is the best zero-beta multi-strategy construction on a robust long window.

Data-loading bug fixed in blend_robust.py (ROOT path one level too shallow -> 
ls/ap coverage under-stated on EW rows); numbers above are the authoritative
df.dot values it now reproduces. Logged in hedge_fund_strats/RESEARCH_REPORT.md.

## Update 2026-08-13 (loop) — Out-of-sample validation: multi-strategy IV blend is NOT overfit

Walk-forward test of the inverse-vol (IV) 6-stream multi-strategy blend
(L/Svolman + RiskParity + CTA + FX + AP gold + LS n10r14), 2019-2026, 6 bps:
estimate IV weights on one half, apply to the other half.

  Train 2019-2022 -> Test 2023-2026: SR 1.010   (in-sample full IV: 1.240)
  Train 2023-2026 -> Test 2019-2022: SR 1.477
  EW full baseline (no weighting):  SR 1.103

BOTH out-of-sample directions stay positive and BOTH beat the equal-weight
baseline -> the inverse-vol tilt (concentrating low-vol, near-independent
ls_n10r14 + fx_carry legs) transfers out of sample; it is NOT an artifact of
in-sample optimization. This, plus the split-half sub-periods (2019-22 SR 1.48,
2023-26 SR 1.01), establishes the multi-strategy IV construction as the most
robust zero-beta book in the suite (SR ~1.24 in-sample, OOS 1.0-1.5).
Data check this fire: Stooq still PoW-blocked, yfinance still rate-limited
(no new free data to expand the CTA-futures metals universe).

## Update 2026-08-13 (loop) — Regime-adaptive layer: tested dynamic levers, ALL negative for flagship

Direct answer to "dynamically adjust strategies for different market
scenarios": built `regime_adaptive_report.py` (no-lookahead, VIX lagged 1d)
testing the candidate dynamic levers on the validated all-weather flagship
(h3+AP, 2008-2026):

- **Static baseline is already regime-optimal**: SR 1.04, CAGR 11.1%,
  MaxDD -12.9%, positive 17/19 calendar years (only 2022 -3.1%, 2023 -1.5%),
  positive all 4 sub-periods. This is the "any time, any scenario" spec.
- **L1 VIX-de-risk HURTS**: all gate variants SR 0.92-0.96 vs static 1.04
  at ~same MaxDD. 1-day-lagged VIX can't pre-empt the fast drawdown moves,
  so it only surrenders upside.
- **L2 switch-to-RP-in-stress FAILS**: SR 0.90, MaxDD -23.4% (doubled).
  RP is a leveraged equity/carry book; for once calls on it in stress it
  bleeds worse than the low-beta flagship.
- **Operational conclusion**: for a low-beta all-weather book the right
  "dynamic" layer is a HEALTH MONITOR (flag sustained 2022-23-style regime
  degradation), NOT an exposure gate or defensive rotation. Dynamic gates
  only add value for HIGH-beta books that lack the all-weather hedge.
- Card: `results/regime_adaptive_card.json`; report addendum appended.

## Update 2026-08-13 (loop) — Deployable DYNAMIC-Regime layer: portfolio HEALTH MONITOR (the lever that works)

Previous fire proved fast VIX-gating (L1) and defensive rotation (L2) FAIL for
the low-beta all-weather flagship. The correct dynamic lever is a PERSISTENCE-
BASED health monitor, now built as `portfolio_health_monitor.py` (deployable,
CI-friendly exit codes: 0=GO/1=CAUTION/2=TRIM).

Rule (no lookahead, realized returns only):
  STRESS(TRIM) = 252d rolling Sharpe < 0 for 21 CONSECUTIVE days AND 63d dd vs
  1y-high < -3%  (a real sustained regime, not a fast blip)
  CAUTION       = either one of the two conditions alone
  GO            = neither

Backtested over 2008-2026 with the persisted rule — fires TRIM ONLY in the
2022-23-24 inflation-shock soft patch (29/61/19 days) + tiny 2009(5)/2016(11);
holds GO through the 2020 COVID crash (0 TRIM) correctly (book +18% through it;
de-risking through fast recoveries was the L1 failure). CAUTION=1609d is by
design (conservative "hold & re-check", no action).

This is the evidence-backed answer to "dynamically adjust strategies for
different market scenarios": the flagship is already regime-optimal (stay in
it), the monitor is the dynamic-risk switch that tells the operator WHEN a
sustained adverse regime has arrived (2022-23-style) to trim gross — and it
converged to the exact 2022-24 stretch that was the book's only impairment.
Current live stance: GO (rolling SR +2.46, asof 2026-08-12).
Artifacts: portfolio_health_monitor.py, results/portfolio_health.json,
results/portfolio_health_history.json.

## Update 2026-08-13 (loop) — L3 (monitor-as-actuator) also FAILS; master system spec consolidated

Third regime-timing lever tested on the flagship (no lookahead): acting on the
health monitor's persistent-TRIM signal (trim to 50%/30% on flagged days) does
NOT improve the book — SR 1.10/1.09 vs static 1.11, MaxDD unchanged -12.9%.
Cause (verified): the flagship's worst drawdowns are FAST single-day troughs
(2018-12-24 -12.9%, 2020-03-16 -12.4%, 2011-08-08 -11.9%) that the durable-
regime monitor correctly does NOT catch; the durable soft patches it DOES catch
(2022-24) are flat/sluggish, not crash-like, so trimming forfeits recovery
upside with no drawdown gain.

L1 (fast VIX-gate) + L2 (rotate to RP) + L3 (monitor-actuator) ALL fail ->
triangulated conclusion: this low-beta all-weather book is fully
TIMING-OPTIMAL statically; the edge is in construction, not reactive timing.
The monitor remains a SITUATIONAL-awareness / capital-deployment go-no-go tool,
NOT an automated de-risking actuator.

Deliverable: consolidated **SYSTEM_PORTFOLIO.md** (project root) — the
company-level master spec tying the validated flagship + rejected dynamic
levers + monitor operating rule into one operational document.

## Update 2026-08-13 (loop) — Robustness / tail audit of the flagship (any-scenario evidence)

Quantified the all-weather flagship's behavior in every major historical crash
(robustness_audit.py -> results/robustness_audit.json). This is the concrete
"any market scenario" evidence the user asked for:

Crash episodes (flagship vs SPX, SPX data 2016+):
  2008 GFC  -6.7%  | 2011 -6.3% | 2015-16 -6.0%
  2018 Q4  -11.9%  vs SPX -20.7%
  2020 COVID -12.1% vs SPX -37.8%   (~1/3 the equity loss)
  2022 Bear -5.3%  vs SPX -26.4%    (~1/5 the equity loss)

Tail profile (2008-2026 daily): VaR(5%) -0.99%, CVaR -1.54%, POSITIVE skew
+1.73; worst month -7.8%, worst cal-year -3.1% (2022), longest stretch below
-5% = 167 days.

Reading: the flagship is a genuine CRASH-DIVERSIFIER (cuts equity crash losses
by 2/3-4/5) with positive skew — but it is NOT crash-immune (loses -6 to -12%
in fast crashes). Its deepest drawdowns come from FAST equity crashes
(2018 Q4, 2020) that a 1-day-lagged monitor cannot pre-empt — consistent with
L1/L2/L3 all failing. The book's edge in bad scenarios is structural (low beta
+34, diversified sleeves), not tactical. This closes the robustness evidence
chain for SYSTEM_PORTFOLIO.md's "any market scenario" claim.

## Update 2026-08-13 (loop) — Mean-reversion market-neutral crash-hedge research (NEW direction)

User asked: mean-reversion market-neutral strategies for the episodes where the
flagship loses money. (New loop job_3f0be364726f.) Built
`meanrev_episode_research.py` -> `results/meanrev_episode_research.json`:
short-horizon cross-sectional equity reversal (long bottom-N worst / short
top-N best, dollar-neutral, T+1, 6bps/side, no lookahead) on twelve_big 290.

KEY RESULT — reversal is positive IN the flagship's loss episodes:
  k5 n30: 2020 COVID +32% (SR 2.6), 2018 Q4 +23% (SR 1.7), 2022-24 +8%, 2011 +4%
    (vs FULL-window SR only +0.34, outside +0.24) — the edge is CRASH-CONCENTRATED.
  k3: 2020 +48-51%, 2011 +8%, 2022-24 +14-22%; k10 FAILS (full SR -0.1..-0.3).

BUT not a pure upgrade when blended:
  - corr(flagship, reversal) = +0.089 (genuine diversifier, per project standard)
  - unconditional/VIX-gated 50% overlay turns flagship loss-episode totals positive
    (2020 -2.2% -> +8.5..+11.8%, 2022-24 -1.6% -> +4.5..+7.3%) BUT
  - adds MaxDD (-13% -> -21..-27%): the reversal's OWN fat tails outside crashes
  - net Sharpe ~neutral (1.03-1.07 vs 1.04 static)
  - good only in EXPLOSIVE high-VIX crashes (COVID) + long 2022-24 bleed; 2011
    worsens under stress-only gate; 2018 Q4 marginal.

Honest verdict / deployment guidance: reversal is a CRASH-HEDGE OVERLAY, not a
standalone Sharpe engine. Only the extreme-stress gate (VIX>32, ~50% overlay,
holding 65% flagship) keeps the trade favorable-ish (SR ~1.03, MaxDD -27%).
Its value is specifically as COVID-type-crash insurance (turns -2% into +9-12%).
Do NOT add statically; treat as a stress-gated sleeve with tight risk controls,
given it contributes its own tail risk. Caveat: episode boundaries/quantiles
mildly in-sample; the no-lookahead VIX gate is the deployable form.

## Update 2026-08-13 (loop) — Flagship construction re-audit + NEW free data: CFTC COT/TFF acquired

Sleeve-level review of the h3+AP flagship (daily, 2008-2026, 4663 days):

- **50/50 weights confirmed robust** (`weight_sweep.py`): SR surface is flat
  (0.811-0.830 for h3 weight 0.10-0.60); in-sample max at h3=0.35 (SR 0.830 vs
  0.824) but with WORSE MaxDD (-13.8% vs -12.9%). 50/50 is the right robust
  pick. Inverse-vol (0.814) and rolling-IV (0.822) both fail to beat EW.
- **Sleeve-level h3 vol-targeting is a small real improvement** (monthly
  rebalance, annualized 252d vol, scale-change costs ~2 bps/yr included):
  10% target SR 0.849 vs 0.824 static at ~same MaxDD -13.0%; 8% target SR
  0.835 with BETTER MaxDD -12.1%. Candidate modification — needs monthly-view
  + sub-period validation before any spec change.
- **Vol-managed L/S swap inside h3 REJECTED**: h3vm SR 0.555 vs h3 0.647;
  flagship 0.775 vs 0.824. The existing plain-L/S construction is correct.

NEW FREE DATA (user request): CFTC Commitments of Traders pipeline built
(`download_cot.py`, browser UA required — CFTC 403s urllib like Stooq):
  - `data_cot/cot_tidy.csv` — disagg futures+options combined, 2006-06..2026-08,
    189k rows, 680 commodity contracts (spec = managed money net).
  - `data_cot/tff_tidy.csv` — Traders in Financial Futures, 2010 + 2017-2026
    (2011-16 zips absent on server), 39k rows, 135 contracts incl. equity-index
    positioning: S&P 500 Consolidated, NDX Consolidated, Russell E-mini, VIX.
  URL patterns: com_disagg_txt_YYYY.zip (2017+), com_disagg_txt_hist_2006_2016.zip,
  com_fin_txt_YYYY.zip. Raw zips cached in data_cot/zips/.

First signal test — equity-index positioning is MOMENTUM, not contrarian:
  lf_z (lev funds net, z-scored) vs fwd 13w SPX: corr +0.246
  am_z (asset mgrs): +0.173; dealers: -0.196 (counterparty mirror)
  lf_z>1.5: fwd13w SPX +1.66% (n=20); lf_z<-1.5: -0.57% (n=58) — trend-
  following confirmation, opposite of the classic commodity-contrarian COT.
- Naive positioning tilt overlay on the flagship FAILS (SR 0.663 vs 0.794
  static on 2017+): adding SPX beta dilutes the all-weather book — consistent
  with N18 (no beta-timing overlays). Next: use positioning INSIDE the CTA leg
  (energy/metals contrarian COT filter) or as a standalone cost-hurdled sleeve.

## Update 2026-08-13 (loop) — Mean-reversion crash-sleeve: VOL-MANAGEMENT DESTROYS the crash alpha (negative R2)

Testing the project's standard Moreira-Muir inverse-vol scaling (which halved
the L/S 130/30 MaxDD at ~same SR, P8) on the mean-reversion crash-sleeve from
last fire (`meanrev_volmanaged.py` -> results/meanrev_volmanaged.json):

  k5 n30 RAW sleeve:  SR +0.34, MaxDD -44.7%,  2020 COVID +32.2% (crash alpha)
  + voltgt=25%:       SR +0.13, MaxDD -58.9%,  2020 COVID -5.6%  (ALPHA GONE)
  + voltgt=20%:       SR +0.11, MaxDD -54.1%,  2020 COVID -4.5%
  + voltgt=15%:       SR +0.09, MaxDD -47.6%,  2020 COVID -3.4%

MECHANISM (fundamental): inverse-realized-vol scaling CUTS exposure when vol
spikes. But mean-reversion earns its money BECAUSE of vol spikes (buying the
crush). So vol-scaling reduces position size exactly when the crash alpha is
biggest -> it converts a crash-hedge into a normal (positive-vol) book that
then LOSES in crashes. The same tool that tames momentum alpha (P8) does the
OPPOSITE to reversal alpha.

DEPLOYMENT IMPLICATION: the reversal crash-sleeve's risk management should be
COUNTER-cyclical, not vol-scaling: raise exposure VIX-gated in stress (as last
fire showed: VIX>32 high-weight overlay turns 2020 -2% -> +9-12%), plus a HARD
gross cap to bound its own outside-crash tails. Do NOT apply Moreira-Muir to it.
The rejection of vol-scaling is what makes this sleeve different from the
momentum leg and correctly wedges it as a niche crash-hedge only.

## Update 2026-08-13 (loop) — Mean-reversion crash-sleeve: COUNTER-cyclical VIX scaling is the correct risk design (resolution)

Resolving the sleeve's tail-risk problem in the correct direction. Standard
vol-scaling FAILS (previous entry) because it de-risks in the crash where the
reversal's edge lives. Testing the OPPOSITE - counter-cyclical scaling (raise
leverage as VIX rises, no lookahead, VIX lagged 1d) on the k5 n30 reversal:

  raw                    : SR +0.34 MaxDD -44.7% | 2020 +32%  2022-24 +8%
  counter-cyclical 2x/1.4: SR +0.43 MaxDD -61.7% | 2020 +66%  2022-24 +26%
  counter-cyclical 1.5/1.2: SR +0.40 MaxDD -50.9% | 2020 +49%  2022-24 +17%

Full-window SR IMPROVES (0.34 -> 0.40-0.43) AND the crash alpha accelerates
(2020 +32 -> +49..66%). Mechanism: mean-reversion alpha scales WITH crush
volatility, so you want MORE exposure as VIX spikes - the exact inverse of
Moreira-Muir. This is what makes it a crash-hedge.

CAVEAT (honest): standalone MaxDD worsens (-61%) => it is ONLY deployable as a
small VIX-gated overlay on the flagship with a hard gross cap, never as a
standalone equity book. Its company-system role: COVID-type crash insurance
(2020 swing -2% -> +9-12% in blended form), counter-cyclically sized, capped.
Full design for the mean-reversion crash-sleeve now resolved:
  signal k=5d cross-sectional reversal, n=30,
  counter-cyclical VIX leverage (raise in VIX>25/32),
  hard gross cap, deploy only as stress-gated overlay on flagship.
Caveat: quantile/cap choices mildly in-sample; no-lookahead VIX gate deployable.

## Update 2026-08-13 (loop) — COT strategy candidates tested; vol-target REJECTED at monthly cadence

Deployment-cadence validation of the iteration-1 h3 vol-target candidate
(monthly view, 2008-2026, scale-change costs included, no lookahead):

  static 50/50:   SR 0.951  CAGR 10.9%  MaxDD -10.2%
  vol-target 8%:  SR 0.900  CAGR  9.9%  MaxDD  -9.2%
  vol-target 10%: SR 0.915  CAGR 10.7%  MaxDD -10.0%
  vol-target 12%: SR 0.926  CAGR 11.5%  MaxDD -10.8%

-> REJECTED: the daily-frequency gain (+0.025 SR) does NOT survive monthly
sampling (all targets below static SR at the deployment cadence). Another
confirmation of the campaign rule: small daily artifacts die at monthly view.
Flagship construction unchanged; static 50/50 remains the spec.

COT-derived strategy candidates (all tested at 12 bps RT, vol-scaled):

1. Equity-index positioning -> SPX timing (lf_z/am_z linear + threshold):
   corr(lf_z, fwd13w SPX)=+0.246 real, but standalone strategies SR -0.03..
   +0.11, MaxDD -21..-42%, halves inconsistent -> FAILS cost hurdle.
2. Natgas COT-momentum: corr(z, fwd13w)=+0.172/+0.169 (STABLE across
   2007-16 and 2017-26 splits — the one genuine signal). COT-agreement filter
   improves 63d natgas trend in EVERY sub-period (unfiltered SR -0.484 /
   MaxDD -89% -> filtered -0.220 / -48%) but the base natgas trend leg is
   negative standalone -> not a deployable sleeve. Jan-2024 +319% squeeze day
   is the steamroller behind the -89% MaxDD (real data, not a glitch).
3. WTI (asymmetric short-capitulation bucket +6% fwd13w) and GOLD: linear
   corr ~0 and unstable across splits -> REJECT.
4. Positioning tilt overlay on the flagship (iter-1): FAILS (0.663 vs 0.794).

Net: COT is real predictive data, but no standalone sleeve clears the cost
hurdle yet. Open follow-ups: (a) COT-agreement filter INSIDE the existing
CTA leg (engine-level test — the filter's marginal value on the leg's small
natgas exposure), (b) lf_z extreme-short as a regime-marker input to the
health monitor, (c) TFF rates/FX positioning vs the Global Macro leg.

## Update 2026-08-13 (loop) — CTA-leg A/B suite: COT filter, natgas tail, metals expansion

Engine-level A/B on the CTA leg (reproduction fidelity 0.9998 vs official
multi_21d — pipeline trusted). All costs 12 bps RT, no lookahead.

1. **COT-agreement filter on natgas (zero-out when multi-TF signal disagrees
   with COT positioning, |z|>=0.25, 39.5% of days)**:
   - CTA leg alone: SR 0.103 -> 0.211 (official base), MaxDD -39.2% -> -36.0%
   - Flagship monthly: SR 0.967 -> 0.978, MaxDD -10.1% -> -10.4%
   - SCRAMBLE GATE: FAILS (real z beats only 70% of 10 scrambled-z runs;
     scramble mean SR 0.179, max 0.226 vs real 0.211). Most of the gain is
     "trade natgas less", not positioning timing -> not deployable as a
     signal per campaign rules.
2. **Natgas tail finding (the robust one)**: dropping natgas from the CTA leg
   entirely keeps leg SR/CAGR IDENTICAL (0.161/3.3%) but cuts leg MaxDD
   -37.8% -> -33.0% (monotone with weight). Natgas trend contributes pure
   tail risk (Jan-2024 +319% squeeze) with zero risk-adjusted return at
   12 bps. At the FLAGSHIP level this dilutes to +0.003 SR / -0.3pp MaxDD
   (CTA is 1/6 of the book) — recorded as a construction option, not adopted.
3. **Metals expansion (new free data via twelvedata)**: XAU/USD (gold spot,
   2007+), SLV, COPX added to data_fred/ (xau/slv/copx.csv, FRED format).
   17-inst CTA vs 14-inst base at flagship level: monthly SR FLAT (0.968 vs
   0.967), 3/4 monthly sub-periods better (2008-12 +0.017, 2013-17 +0.071,
   2022-26 +0.033; 2018-21 -0.093) BUT flagship daily MaxDD worsens
   -12.9% -> -15.0% -> NOT adopted (opt-in via FRED list comment in
   strat_cta_futures.py).

Iteration verdict: the flagship is input-robust — leg-level SR changes of
+/-0.05 barely move the book (+/-0.01 monthly SR). No spec change adopted;
all variants + data logged. Reproducibility artifacts:
run_cot_filter_test.py, weight_sweep.py, _ab_*.csv in results/.

## Update 2026-08-13 (loop) — Mean-reversion crash-sleeve PASSES signal-scramble gate -> VALIDATED

Ran the project's gold-standard signal-scramble validation (normalize: randomize
the per-rebalance rank order, destroying 'long-worst/short-best->future return';
40 scrambles, single validated engine meanrev_episode_research.backtest with a
logical scramble flag). Results (meanrev_scramble_val.py -> 
results/meanrev_scramble_val.json):

  k=5 n=30: real SR +0.34 | scramble mean -0.82 (p95 -0.27) | p=0.000 >> PASS
  k=3 n=30: real SR +0.37 | scramble mean -1.34 (p95 -0.96) | p=0.000 >> PASS

Both real runs are far above EVERY scramble -> the short-horizon cross-sectional
reversal edge is REAL, not overfit. Real episodes reproduce the original research
(k5: 2018Q4 +22.6%, 2020 +32.2%, 2011 +4.4%, 2022-24 +8.3%), confirming the PnL
engine is correct.

PROCESS NOTE (honesty): an earlier vectorized-approximation of the backtest
produced a WRONG (broken) baseline (f-encapsulated fail); the scramble PASS only
became trustworthy after patching the SINGLE validated engine to accept a
scramble flag and re-validating that real SR still equals +0.34/+0.37. Lesson
reaffirmed: never report a validation from a divergent re-implementation -
only from the engine that reproduces the published baseline.

STATUS UPGRADE: the mean-reversion crash-sleeve is now VALIDATED (was 'watch')
under the project's scramble gate - one of only a handful of sleeves to pass.
It remains a crash-HEDGE overlay (correct risk design is counter-cyclical VIX
sizing + hard cap; vol-scaling destroys it), not a standalone Sharpe engine.

## Update 2026-08-13 (loop) — h3 internal weights: EW is CRASH-OPTIMAL, not just robust

Swept ls/cta/macro weights inside h3 (0.1 grid, AP=50%, monthly view):
  EW 1/3-1/3-1/3:        SR 0.950  CAGR 10.8%  MaxDD -10.2%
  max-SR grid (0.7/0.3/0): SR 1.028  CAGR 14.5%  MaxDD -13.9%
  ls+cta only (0.5/0.5/0): SR 1.005  CAGR 12.8%  MaxDD -12.0%

The max-SR grid beats EW in ALL FOUR sub-periods, but crash-episode
decomposition is decisive:
  2008 GFC:  EW -6.6%  vs best -10.2%
  2011:      EW -6.5%  vs best -10.2%
  2018 Q4:   EW -11.5% vs best -16.7%
  2020 COVID: EW -11.7% vs best -20.3% (nearly DOUBLE)
  2022:      EW -5.5%  vs best -7.4%
  beta: EW +0.41 vs best +0.65; Calmar 0.84 vs 0.71.

-> EW REJECTED any change. The Global Macro leg (standalone daily SR -0.244)
is the flagship's CRASH INSURANCE: its negative calm-market SR is the premium
for losing the least in every crisis. The 1/3-1/3-1/3 EW is crash-optimal,
not merely robust — this closes the last untested construction dimension
(h3 internal weights). The h3+AP 50/50 static construction is now
comprehensively validated: sleeve weights (N17), h3/AP mix (iter-1 sweep),
internal leg weights (this entry), timing (L1/L2/L3), vol-target (iter-2).

NEW: TFF FX positioning vs forward FX returns (2019+, weekly, n~360-370):
  GBP CONTRARIAN: corr(lf_z, fwd13w) = -0.218 (fwd4w -0.227) — crowded spec
  GBP longs precede declines (t~4.3); strongest FX positioning signal found.
  CAD momentum +0.187; EUR +0.060; JPY ~0; AUD +0.110.
  No leg modification: macro leg FX sleeve is momentum-based and the flagship
  is input-robust; GBP-contrarian filter logged as a future macro-leg option.

## Update 2026-08-13 (loop) — LEGACY COT acquired (1986-2016): 40-year positioning dataset + health-monitor lens

NEW FREE DATA: legacy COT futures+options combined downloaded
(deacot1986_2016.zip, 22MB zip) -> data_cot/legacy_tidy.csv: 146,677 rows,
612 contracts, 1986-01-15..2016-12-27 (non-commercial/commercial split).
Combined with disagg (2006+) + TFF, positioning research now spans 40 years.
SPY price history extended to 1993 (twelvedata ranged queries, FRED blocked
from this network) -> data_fred/spy_early.csv. FRED (fred.stlouisfed.org +
api.stlouisfed.org) currently times out from this machine — note for future
data fetches; twelvedata free-tier ranged queries are the working fallback.

30-year signal tests (weekly, split-sample):
- S&P spec positioning (legacy noncomm z, 1993-2016, n=1195): linear corr ~0
  (-0.05/-0.07), but the SHORT-CAPITULATION tail is real: z<-1.5 -> fwd13w
  SPY +5.16% vs +0.94% at z>1.5 (n=122/156). Held 1993-2004 (corr -0.15) and
  faded 2005-16 (+0.04); post-2017 TFF era the same extreme was momentum-
  flavored (iter-2: -0.57%) -> the capitulation effect is era-dependent,
  NOT a stable tradable signal. Informational only.
- WTI legacy positioning (2001-2016): corr +0.005 overall, sign flips
  across halves (+0.183 / -0.156) -> REJECT.

HEALTH MONITOR UPGRADE: added an informational "equity spec positioning z"
lens to portfolio_health_monitor.py (TFF lf_z with legacy noncomm fallback,
1993+ continuous). Stance logic UNCHANGED (positioning is display-only —
consistent with L1/L2/L3: no actuator role). Current card: stance GO,
rolling SR +2.46, positioning z -0.25 (neutral).

## Update 2026-08-13 (loop) — TFF rates positioning + DISCOVERIES consolidation + 1987 reference

TFF rates positioning (10Y note lf_z vs fwd TLT, weekly):
  corr(lf_z, fwd13w TLT) = -0.147 (n=774), STABLE in BOTH halves
  (-0.270 / -0.235) — leveraged funds net-long bonds precedes bond declines.
  Strongest stable positioning signal found in the campaign (t~4). BUT
  standalone TLT contrarian strategies fail the cost hurdle: best SR -0.01
  (threshold 1.5), sub-periods +1.33 (2012-17) vs -0.88 (2018-26) — the
  fade pays at capitulation, bleeds through trend phases. Same verdict as
  N21: statistically real, not sleeve-grade.

Legacy positioning episode reference (1986+): 1987 crash — specs ~flat
pre-crash, -6.3% net after (exogenous, no capitulation setup); 1990-10 and
1994-07 bottoms — extreme -20% capitulation shorts; 1998/2002 — moderate.
Monitor historical_note updated accordingly.

Canonical ledger updated: DISCOVERIES.md now carries P15 (EW crash-optimality:
max-SR internal-weight grid doubles COVID loss -20.3% vs -11.7%; macro leg =
crash insurance), P16 (40-year COT dataset + signal map), N21 (COT signals
real but not tradeable standalone; positioning = informational lens).

## Update 2026-08-13 (loop) — Crash-sleeve HORIZON-FRAGILITY + constructed-overlay tradeoff (completes the research)

Two final robustness findings on the mean-reversion crash-sleeve
(meanrev_robustness.py -> results/meanrev_robustness.json, + constructed-overlay test):

(1) HORIZON FRAGILITY — the crash alpha is a FAST-reversal phenomenon only:
    sweep k in {3,5,8,10} x n {10..40}: 2020 COVID positive in 8/16 cells,
    2018 Q4 in 10/16. ALL positive cells are k<=5; k=8/10 go NEGATIVE in the
    crash episodes (2018 Q4 -21..-41%, 2020 -3..-11% for k=10). Within k=3/5,
    n is not knife-edge (10-40 all keep 2020 +17..+58% mostly). Deployment must
    LOCK k<=5; the edge is short-horizon by nature (fast crush -> fast reversal).

(2) CONSTRUCTED OVERLAY (flagship + VIX-gated k5n30) tradeoff:
    FULL 2008-2026: SR 1.04->1.06-1.07 (slightly better) but MaxDD -12.9% ->
    -19..-24% (the sleeve adds tail risk outside loss episodes).
    HOLDOUT 2023-26: SR 0.95->0.97, total +26.3%->+28.4%, MaxDD ~same (-6.3/6.4).
    => helps in the stress-heavy recent window, hurts the long-run DD profile.

FINAL THE RECOMMENDATION (fully evidenced): the mean-reversion crash-sleeve is a
real, validated (scramble PASS), FAST (k<=5), counter-cyclically-sized crash-
insurance tool. Deploy ONLY opportunistically during stress (VIX-gated) with a
hard cap -- it is NOT a permanent core member (long-run MaxDD drag). Its value
is specifically turning 2020/2022-24-type flagship losses into gains, at the
cost of a wider tail elsewhere. Research on this direction is now comprehensive
(episode value + validation + sizing + horizon + overlay tradeoff).

## Update 2026-08-13 (loop) — AP-half audit + CTA variant confirmation

AP sleeve (the 50% of the flagship never audited in this campaign):
  - Deployed wf_champion_gold_opt_daily.csv: vol 14.0%, SR 0.94 (no rf),
    2008-02..2026-08-12, n=4664 — the realization-timed honest record.
  - AP holds ~64% of the flagship's variance at 50/50 (14.0% vs h3 10.4% vol);
    vol-balanced weighting already tested (iter-1 IV: 0.814 vs 0.824 EW).
  - vt6 champion (DEPLOYMENT_SPEC: SR 1.40, MaxDD -7.6%) has NO daily audit ->
    blocked by the N13 honest-daily-record rule; linear vol-scaling of the
    audit = a weight change already covered by the iter-1 sweep (cash drag).
  - Live paper trade current: gate ON, 25 holdings, as_of 2026-07-31;
    audit series up to 2026-08-12. AP side: NO CHANGE warranted.
  - CTA leg variant recheck (all four on-disk variants in-flagship, monthly):
    multi 21d (deployed) SR 0.954 BEST (multi 10d 0.885, tsmom 21d 0.893,
    tsmom 10d 0.891) — deployed choice confirmed optimal.
  - Stooq retry with browser UA: still connection-timeout (N19 stands).

Campaign state: every construction choice of the flagship is now
independently re-verified optimal in this loop (h3/AP mix, internal leg
weights, CTA variant, CTA rebalance, sleeve set, AP champion, timing=static).
portfolio_spec.py re-run clean after all edits.

## Update 2026-08-13 (loop) — Recent-era verification: recovery confirmed, no degradation

P1 verification with the current pipeline: every 5y rolling window positive,
min +0.31 — BUT the minimum IS the most recent window (2022-2027), and the
rolling 5y SR shows a decay trend (2016-21 +1.27 -> 2020-25 +0.73 -> 2022-27
+0.31). Decomposed by calendar year, this is the KNOWN 2022-23 soft patch
still inside those windows, not live-era degradation:
  2019 +1.90 / 2020 +1.45 / 2021 +1.54  (strong era)
  2022 -0.73 / 2023 -0.54              (soft patch, known)
  2024 +0.52 / 2025 +1.28 / 2026 YTD +0.72 (+9.1% CAGR) — RECOVERY.
Monitor stance GO is correct; no action. (Also confirmed: Stooq still
connection-timeout with browser UA — N19 stands; macro-leg rates-filter
rebuild deferred as low expected value + crash-insurance risk.)

## Update 2026-08-13 (loop) — Rates-crowding filter CLOSED; monitor slow-decay lens added

Final open strategy question answered: does the rates-contrarian signal
(10Y lf_z corr -0.15 with fwd TLT, stable) help as a filter on the macro
leg's TLT trend sleeve (20/200 MA, vol-scaled, 12 bps)?
  A trend only:               SR +0.180, MaxDD -23.0%
  B zero when crowded-against: SR +0.031  (WORSE in both halves: -0.23/-0.03,
                                  +0.11/+0.26)
  C half when crowded-against: SR +0.117
-> The crowded-against positions WERE the profitable trend positions
(bond-bull crowding is trend-confirming, not capitulation, inside a trend
framework). REJECTED permanently; the macro leg stays untouched. Every
positioning signal now has a complete verdict (see P16/N21).

Monitor: added rolling 5y monthly Sharpe line (slow-decay lens) so the
2026-08-13 rolling-window decay finding is visible to the operator
(informational; stance logic unchanged).

## Update 2026-08-13 (loop) — L/S variant audit: Market Neutral rejected, construction space FULLY CLOSED

Last unaudited leg choice tested: L/S variant in-flagship (monthly):
  130/30 (deployed)  SR 0.954  CAGR 10.9%  MaxDD -10.2%
  120/20             SR 0.924  CAGR 10.0%  MaxDD  -9.2%
  Dollar Neutral     SR 0.952  CAGR 11.4%  MaxDD -10.7%
  Market Neutral     SR 0.981  CAGR 11.7%  MaxDD -10.6%  <- tempting

Market Neutral decomposition: standalone beta +1.69 (vs 130/30 +1.38),
MaxDD -56.1% — the name lies, it is MORE equity beta, not less. Flagship
crash episodes: MN worse in ALL FIVE (2008 -8.0 vs -6.6; 2011 -8.0 vs -6.5;
2018Q4 -12.4 vs -11.5; COVID -14.1 vs -11.7; 2022 -8.0 vs -5.5); flagship
beta +0.46 vs +0.41. Its in-flagship SR gain = calm-market beta harvest,
exactly what the crash-discipline rejects (same mechanism as the iter-4
internal-weight tilt). REJECTED; 130/30 confirmed as the optimal
beta/return/crash trade-off.

With this, EVERY construction choice in the suite has been audited
in-flagship this campaign: sleeve set (N1/N2/N17), h3/AP mix, internal leg
weights, L/S variant, CTA variant + rebalance + universe, AP champion,
timing layers (L1/L2/L3), vol-target, drawdown filters (N18). The static
h3+AP spec is the verified optimum of the available strategy space.

## Update 2026-08-13 (loop) — Crash-sleeve validated against the flagship's ACTUAL drawdown windows

Tested the fast (k5_n30) reversal against the flagship's genuine losing
windows (from the drawdown inventory, not just 4 pre-selected crises):

  window          flagship   reversal  rev SR | corr
  2011 Euro        -1.1%      +4.4%     +0.50 | +0.26
  2015-16          -0.7%     +24.8%     +2.40 | +0.21
  2018 crash       -0.6%     +22.6%     +1.72 | +0.22
  2020 COVID       -2.2%     +32.2%     +2.64 | +0.26
  2010             -1.5%      +4.8%     +0.94 | +0.30
  2022 Q1          -2.0%      -6.5%     -0.68 | +0.30   <- only miss (slow grind)
  2022-24 soft     -1.2%     +13.7%     +0.34 | +0.11

Profits in 6 of 7 flagship drawdown windows, strongly in the deep ones
(2015/2018/2020 +22..32%, SR 1.7-2.6). CORR STRUCTURE is ideal for insurance:
+0.197 on drawdown days (out-earns the book's stress) vs +0.051 on benign days
(pure diversification when calm). The one miss (2022 Q1) is a slow-grind window
the fast reversal doesn't trigger -- a known, tradeoff-consistent limitation.

This is the definitive episode-level test of the user's ask ("mean-reversion
market-neutral in episodes the flagship lost money"): the sleeve delivers across
the flagship's real losing periods, with favorable benign-day diversification.
COMPLETES the crash-sleeve research (value + validation + sizing + horizon +
overlay + actual-drawdown-window coverage). Recommendation unchanged: fast
(k<=5) counter-cyclical stress-gated capped crash-insurance overlay only.

## Update 2026-08-13 (loop "continue") — Crash-sleeve INTEGRATED into company master spec

Reconciled the mean-reversion crash-sleeve research into the company-level
system portfolio. SYSTEM_PORTFOLIO.md gained Sec. 5 (the validated crash-
insurance overlay) with full evidence: validated (scramble PASS), episode
coverage (6/7 flagship drawdown windows), counter-cyclical sizing rule,
and the honest deployment constraint (VIX-gated, hard-capped, opportunistic
overlay NOT permanent core). Sec. 1 cross-references it as the designed
mitigation for the flagship's fast-crash losses. The system portfolio is now
a complete, deployed spec: all-weather flagship (core) + health-monitor
(dynamic layer) + validated crash-sleeve (stress-gated insurance).

ONGOING LOOP CONTAMINATION NOTE: the /loop system now has ~6+ active
10-min recurring jobs across the campaign (flagship-spec, mean-reversion,
and this generic 'continue'), all running concurrent/competing fires. Recommend
pruning to ONE active loop (e.g. keep the flagship-spec job_25bfe73dec88 or the
'continue' job, cancel the rest via CronDelete) to avoid redundant competing
work each cycle.

## Update 2026-08-13 (loop) — FRED API UNLOCKED (real key); 30-year WTI + copper tests

FRED api.stlouisfed.org WORKS with the repo's FRED_KEY (earlier probe used a
fake key and misled; fredgraph.csv still times out, API endpoint fine).
Fetched: wti_full.csv (DCOILWTICO, 10,221 rows, 1986-01..2026-08 — the
1986-2000 WTI gap is CLOSED), copper_monthly.csv (PCOPPUSDM, 1992-2026).
Gold/silver LBMA series removed from FRED entirely (IDs 404) — the pre-2007
gold price gap remains (blocked: Stooq/yahoo/twelvedata free tier).

30-year positioning re-tests:
- WTI (2001-2016, n=815): linear corr ~0 (fwd4w +0.010, fwd13w +0.005),
  but the SHORT-CAPITULATION asymmetry replicates S&P: z<-1.5 -> fwd13w
  +4.86% vs +2.11% at z>1.5 (n=74/117). Extreme spec short = capitulation
  buy across BOTH markets (S&P +5.2%, WTI +4.9%), era-dependent.
- Copper (monthly 1992-2016, n=299): corr(z, fwd3m) +0.064 — weak.
Monitor historical_note updated with the WTI asymmetry.

## Update 2026-08-13 (loop) — L1 VIX audit clean; FRED reachability intermittent

L1 VIX-gate audit: regime_adaptive_report.py loads data_fred/vix.csv
(2000-2026, 6,724 rows) — the flagship window (2008+) is FULLY VIX-covered,
so the L1 conclusion (fast VIX-gating fails) stands on complete evidence.
(AP suite holds full VIX 1990+, vix_daily.csv, if ever needed.)

FRED API: reachable in brief windows (wti_full 1986+, copper_monthly 1992+
landed earlier this fire-day) then ConnectTimeout again — intermittent, not
key-gated. QUEUED for a future fire when FRED is up: dxy.csv (DTWEXBGS broad
dollar 2006+) and t10y2y.csv (curve spread 1976+) -> 16-instrument CTA leg
test (dollar trend + curve momentum are classic CTA macro inputs the leg
lacks). Expected flagship impact tiny (iter-3 metals precedent); leg-level
diversification is the goal.

## Update 2026-08-13 (loop) — dxy fetched + 15-inst CTA leg test; t10y2y rejected for engine

FRED reachable again: dxy.csv (DTWEXBGS, 5,164 rows, 2006-01..2026-08-07),
t10y2y.csv (5,407 rows, 2005-01..2026-08-12) landed. A/B (same pipeline,
15-inst = 14 + dxy, 21d multi, 12 bps RT):
  CTA leg:  14-inst SR 0.045 MaxDD -46.5% -> 15-inst SR 0.048 MaxDD -42.2%
            (dxy = +0.003 SR, -4.3pp leg MaxDD — genuine robustness gain)
  Flagship: monthly SR 0.950 -> 0.954 (+0.004), MaxDD -11.2 -> -11.1,
            daily MaxDD FLAT (-14.4/-14.5) — no degradation (unlike metals).
  Sub-periods: +0.019 / +0.013 / -0.013 / ~0.00 — mixed-positive.
Verdict: dxy is strictly better than the metals addition and free, but the
flagship effect (+0.004 monthly SR) is below the deployment-noise floor ->
OPT-IN (documented in strat_cta_futures.py), deployed leg unchanged.
t10y2y: crosses zero (2006/2019/2022-24), breaking pct-change signals in the
CTA engine -> REJECTED for this leg; queued as a macro-leg level-signal
input (curve steepener/flattener) for a future research pass.

## Update 2026-08-13 (loop) — t10y2y CLOSED: predictive but fails as a gate

Curve spread (10y-2y) vs forward TLT (weekly, n=1024, 2006-2026):
  corr(level, fwd13w) = +0.187 (t~6); inverted -> fwd13w TLT -1.58% vs
  steep +1.37%; split-sample same sign (+0.174 / +0.071). REAL macro signal.
BUT as a gate on the macro leg's TLT trend sleeve (20/200 MA, vol-scaled):
  A trend only:          SR +0.073
  B long only if s>0.5:  SR -0.155 (2016-26: -0.42 vs +0.16 — the spread
                         stayed low all era, gate killed every bond long)
  C + short when s<0.5:  SR -0.331 (MaxDD -63.9%)
-> CLOSED: the curve spread is macro CONTEXT (already visible in the rates
legs), not a tradable gate. Same verdict family as all COT signals (N21).
t10y2y.csv remains in data_fred/ as a research/monitor resource.

## Update 2026-08-13 (loop) — Shiller probe blocked; routine checks green

Shiller long S&P (econ.yale.edu) unreachable from this network — the
1986-1993 S&P price gap is now CONFIRMED unfillable from reachable free
sources (FRED daily equity indices start 2016; SPY ETF 1993; twelvedata
free-tier ranges gated; Yahoo 403; Stooq/Shiller timeout). Legacy S&P
positioning research remains 1993+.

Routine: AP live champion gate ON (SPY 747 > 13ma 691.4, 25 holdings,
as_of 2026-07-31); COT disagg+TFF latest 2026-08-04 (next CFTC publish
~2026-08-14, as-of 08-11); monitor stance GO.

## Update 2026-08-13 (loop) — Top-100 momentum: credit-spread gate FIXES the bad regimes

Direct answer to "the top momentum strategy works well sometimes, not always —
filter the drawdown/underperformance periods with VIX or a macro index".
Baseline (monthly top-100 high-Sharpe, 2007-2026): SR 0.626, MaxDD -50.6%,
split-half 0.34/0.98. Swept 36 no-lookahead filters (index lagged 1d, toggle
cost 3.8bp one-side on traded fraction, net of monthly rebalance cost):

  baseline                     SR 0.626  MaxDD -50.6%
  credit_pct 0.85 -> 30%       SR 0.779  MaxDD -31.8%   <- BEST (BAA-AAA spread)
  vix_abs 25 -> 30%            SR 0.739  MaxDD -32.9%
  vix_abs 22 -> 30%            SR 0.730  MaxDD -33.1%
  vix_pct 0.85 -> 30%          SR 0.700  MaxDD -43.4%
  curve_inv (10y-2y<0) -> 50%  SR 0.585  MaxDD -50.6%   <- fails (curve already
                                                          re-steepened by 2008)

Winner mechanics: BAA-AAA spread >= trailing-252d p85 -> cut to 30% exposure
(de-risk to cash). 2008: -35.2% -> -14.6%; 2009: -5.7% -> +2.4%; 2018:
-1.5% -> +4.7%; 2020 MaxDD -32.8% -> -23.5%. Return UP (11.3% -> 11.8%);
split-half 0.34/0.98 -> 0.50/1.12 (BOTH halves improve). Toggle cost ~0.2%/yr.

Why credit spread beats VIX here: VIX gates whipsaw (204-298 toggles, give
back return); the spread is a slow persistent systemic-stress signal. This is
the OPPOSITE verdict of the low-beta all-weather flagship (where VIX gates
failed — that book has no high-beta crash leg to filter).

Walk-forward OOS (threshold chosen on one half, tested on the other):
h1->h2: OOS SR 1.120 vs baseline 0.993 | h2->h1: OOS 0.504 vs 0.330.
Same q=0.85 wins both halves independently -> NOT a sweep artifact.

Deliverables: monthly_top100_momentum.py refactored (prepare/walk_forward
with additive exposure overlay, original behavior unchanged);
top100_momentum_regime_filter.py + .json (full sweep, per-year);
top100_momentum_credit_wf.py (OOS check);
reports/top100_momentum_regime_filter.md (card).

## Update 2026-08-13 (loop "continue") — Crash-sleeve is Pareto-optimal-independent: NO free-lunch overlay (closing result)

Tried to find a MaxDD-constrained VIX-gated overlay that keeps crash gains
without the long-run MaxDD drag (the one remaining caveat). Swept overlay
weights (VIX>28 in {0.10..0.30}, VIX>22 in {0.05..0.10}):

  overlay cfg        fullSR  MaxDD  2020     2022-24
  VIX>28 .20 >22 .10  1.08  -17.7%  +3.3%    +0.0%   (flagship 2020 was -2.2%)
  VIX>28 .15 >22 .08  1.07  -16.1%  +1.9%    -0.2%
  VIX>28 .12 >22 .06  1.07  -15.1%  +1.1%    -0.6%
  VIX>28 .10 >22 .05  1.07  -14.4%  +0.5%    -0.8%
  flags baseline 1.04 -12.9% -2.2% -1.6%

RESULT: NO configuration dominates the static flagship on SR AND MaxDD together.
Every increase in crash protection (2020 more positive) comes with proportional
MaxDD cost (-14..-21%); the smallest overlay already lifts MaxDD to -14.4% for
only +0.5% 2020 improvement. The insurance value and tail cost are INSEPARABLE.

CLOSING DEPLOYMENT CONCLUSION: the static all-weather flagship (SR 1.04, MaxDD
-12.9%) is already PARETO-OPTIMAL with respect to the crash-sleeve overlay. The
validated mean-reversion sleeve is a deliberate RISK-REALLOCATION tool -- deploy
it only as an explicit decision to trade some tail-risk for intra-crash gains,
never as an expectation of better risk-adjusted returns (it cannot beat the
flagship on both axes). Crash-sleeve research is now COMPLETE. Recommend priority
shift back to the flagship-spec / company-system loop.

## Update 2026-08-13 (loop) — DATA BOUNDARY DEFINITIVELY MAPPED (free-tier, this machine)

Final route tested: Yahoo chart API via curl_cffi with chrome TLS
impersonation -> still 403 (IP/region-level block, not fingerprinting).
Complete free-data boundary for the remaining research gaps:
  - S&P daily 1986-1993: UNFILLABLE (FRED daily indices 2016+, SPY 1993+,
    twelvedata ranges gated, Yahoo 403, Stooq/Shiller timeout)
  - Gold/silver daily pre-2007: UNFILLABLE (FRED LBMA discontinued, XAU/USD
    free tier 2007+, GC=F 403, Stooq timeout)
  - Real futures (Stooq): blocked (N19)
  - FRED API: intermittent windows (works when up; wti_full/copper/dxy/
    t10y2y landed this session)
  - CFTC COT (disagg+TFF+legacy): WORKING, current
  - twelvedata free: WORKING for recent 5000-row pulls (metals, SPY/TLT/GLD)
The research frontier for "more free data" is now exhaustively documented —
further strategy work on pre-2007 assets requires paid feeds.

## Update 2026-08-13 (loop) — Top-100 momentum: LAYERED overlay crushes MaxDD to -12.6%

Follow-up: credit gate alone (-31.8% MaxDD) deemed "still huge". Stacked levers
on the monthly top-100 book (all lagged-1d, toggle costs net, de-risked cash
earns 3m T-bill):

  book only                          SR 0.626  MaxDD -50.6%
  credit p85->0 only                 SR 0.755  MaxDD -30.0%
  credit + SPY<200d flat + VIX>=32 flat      SR 0.796  MaxDD -24.1% (0809 win +1.6%!)
  + vol-target 12% (5% band)         SR 0.890  MaxDD -12.6%  <- WINNER
  + vol-target 10%                   SR 0.846  MaxDD -10.5%
  + vol-target 15%                   SR 0.858  MaxDD -15.7%

Winner (credit0+s200+v32+vt12): ann 8.7%, vol 10.0%, MaxDD -12.6% (4x better),
Sharpe UP 0.63->0.89, ZERO negative calendar years (book had 4). 2008: -35.2%
-> +1.6%; 2018: -1.5% -> +3.7%; 2020 MDD -32.8% -> -12.2%; 2022: -5.5% -> -3.0%.
Price: muted bull years (2019 7.1% vs 24.6%; 2020 8.8% vs 29.4%) — the honest
cost of the drawdown dial. Split-half 0.78/0.99 (both regimes strong).

Robustness: 5% no-trade band -> 463 toggles/19y, SR unchanged (0.92);
10% band -> 294 toggles, SR 0.94. Walk-forward (vt chosen on one half, OOS
other): h1->h2 OOS 1.05 vs book 0.99 | h2->h1 OOS 0.64 vs book 0.33.
Vol-targeting 10-15% transfers OOS; not a sweep artifact. Own-DD stop tested
and redundant once vt on (dropped). Deploy: credit p85->flat, SPY<200d->flat,
VIX>=32->flat, vt12, 5% band, cash=T-bill. Long-only, no leverage.

Deliverables: top100_momentum_dd_overlay.py + .json (16-config sweep, per-year);
top100_momentum_dd_wf.py (band + WF); reports/top100_momentum_dd_overlay.md.

## Update 2026-08-13 (loop) — 90d trend top-100 tested: good raw, 252d Sharpe+overlay still best deploy

"how about 90 day trend top 100": ranked the top-100 book by past-n cumulative
return instead of past-year Sharpe (same universe/window/costs; signal is the
only change). Raw books:

  t252_sharpe (current)  SR 0.626  ann 11.3%  MaxDD -50.6%  half 0.33/0.99
  t90_ret  (the ask)     SR 0.695  ann 12.3%  MaxDD -47.7%  half 0.54/0.87
  t126_ret (6m)          SR 0.730  ann 13.0%  MaxDD -47.2%  half 0.61/0.86  <- best raw
  t90_sharpe             SR 0.594  ann 10.3%  MaxDD -53.6%  half 0.37/0.87

Findings: (1) return-trend beats Sharpe-trend at every horizon — the vol
penalty in the Sharpe signal discards exactly the strong high-vol winners;
(2) sweet spot ~6m not 3m; (3) 90d fixes the weak first half (0.33->0.54).

With the layered DD overlay (credit0+s200+v32+vt12): t252_sharpe 0.890/-12.6%
STILL wins; t126_ret 0.874/-13.3% near-tie second; t90_ret 0.786/-12.5%.
Overlay owns drawdown control regardless of signal; the slower signal keeps
more return under the overlay (8.7% vs 7.4%). VERDICT: keep 252d Sharpe +
overlay as deploy; 6m return-trend is the fallback signal. Card:
reports/top100_momentum_horizon.md; script: top100_momentum_horizon.py.

## Update 2026-08-13 — bigmove: next-day >=5% return prediction — honest precision-ceiling result

Developed a no-look-ahead ML pipeline to predict next-day huge returns
(defined as next_close/today_close - 1 >= +5%; signal from close[T] only).
Universe: 285 US large caps, twelve_big daily panel (2006-2026).

Method: 49 technical features (momentum, realized vol, RSI, range/gap, volume
ratios, per-stock vol-normalized + market-relative + stock big-move frequency),
HistGradientBoosting (class-balanced), rolling 3y window refit quarterly.
Out-of-sample walk-forward 2018-2026.

VERDICT: 70% hit precision on next-day >=5% is NOT achievable from daily OHLCV
alone. OOS ROC-AUC ~0.82 (real edge), but precision caps:
  up5  : ~10% @thr0.7, ~16% @thr0.9   (base rate ~1.6%)
  up3  : ~19% @thr0.7, ~28% @thr0.9
  abs5 : ~19% @thr0.7, ~30% @thr0.9
  down5: ~8%  @thr0.7, ~9%  @thr0.9
Because a single-day >=5% large-cap move is dominated by unobservable-to-close
idiosyncratic news. The model is a useful RISK RANKER (~10-18x lift) but not a
70%-reliable trading signal. Reaching 70% needs earnings-calendar + news/NLP +
options-flow data, NOT more technical features.
Deliverable: tools/quant/bigmove/ (README.md) + reports/BIGMOVE_RESEARCH.md.
Not deploying standalone (concentration, deep drawdowns); recommend as a
small-risk overlay at most.

## Update (continue) — FLOORED flagship integrated into company master spec

Reconciled the parallel fires' floored flagship (no-losing-year book,
portfolio_floored.py, P15/P19): added as the PRIMARY CORE in SYSTEM_PORTFOLIO.md
Sec. 1 (SR 0.98 daily / 1.17 monthly, MaxDD -6.2% daily, ZERO negative calendar
years 2008-26, worst 2022 +0.61%). Also added the reconciliation that the
crash-sleeve's Pareto-independence holds even MORE strongly for the floored core
(already -6.2% MaxDD + no losing years -> crash-sleeve even more optional).
The floored book is the strongest answer yet to "profitable high Sharpe ANY
TIME in any market scenario" (worst year +0.61%, no losing years), with the
un-floored flagship retained as the higher-return variant (+360bp/yr CAGR at
the cost of -12.9% MaxDD / 2 losing years).

## Update 2026-08-13 — bigmove stop-loss variant: 1% stop HURTS (decisive)

Extended the bigmove next-day>=5% strategy with the user's intraday stop-loss
rule (exit at next open if gap below stop, else at stop if low<stop, else next
close; 6bp one-side = 12bp round trip; same no-look-ahead walk-forward).

Key result @ probability>=0.9 (OOS 2018-2026):
  no-stop: hit5 16.5% | +0.18% net/trade | active-day Sharpe 0.63 | DD -48%
  stop 1%: hit5 12.8% | +0.20% net/trade | active-day Sharpe -0.12 | DD -61%
  stop 3%: hit5 15.1% | +0.08% net/trade | active-day Sharpe -0.02 | DD -63%

Mechanism (measured, thr>=0.9): 72% of all predicted-big-up trades touch -1%
intraday; winners-touched-stop still closed +8.5% avg. The strategy earns by
harvesting rare +5% days; a 1% stop truncates exactly that right tail, capping
per-trade loss but also capping the big wins that drive the edge -> Sharpe and
hit-rate worsen. Per-trade net ~flat because loser-truncation ~ winner-truncation.

Decision (delegated): operational rule = probability>=0.9 with 1% stop (best
per-trade net, caps per-trade risk), runnable via
tools/quant/bigmove/backtest_stoploss.py. Flagged: far below 70% precision,
weak per-trade, negative active-day Sharpe, not standalone-deployable (small
overlay at most). Full writeup reports/BIGMOVE_STOPLOSS.md.

## Update (continue) — FLOORED flagship no-losing-year GUARANTEE verified against live T-bill

Verified the floored flagship's binding "any time" constraint: the no-losing-year
guarantee holds while the 3M T-bill >= 3.4%. Current T-bill = 3.73% (2026-07),
a 0.33pp (~10%) buffer above the floor => guarantee HEALTHY now.
Tripwire: T-bill drops below 3.4% (a ~9% drop) OR the un-floored flagship's
worst-year worsens below -3.4% by the same 33bp. Re-check T-bill each fire as an
operational monitor. (portfolio_floored card: SR 0.98 daily / 1.17 monthly,
MaxDD -6.2%, worst year 2022 +0.61%.)

## Update 2026-08-13 — bigmove stop sweep incl 10%: loose stops = "no stop"

Swept stop-loss levels 1/3/5/10% (6bp one-side, no-look-ahead walk-forward, thr>=0.9):
  stop 1% : hit 12.8% | +0.199% net/trade | aSharpe -0.12 | DD -61%
  stop 3% : hit 15.0% | +0.076% | -0.02 | -63%
  stop 5% : hit 16.0% | +0.051% | +0.11 | -52%
  stop 10%: hit 16.3% | +0.034% | +0.07 | -58%   (94% held to close = ~no stop)

10% stop rarely triggers in large-caps -> converges to no-stop hit-rate (~16.3%)
but gives WORST per-trade net (lets fat-left-tail losses run). 1% stop best for
per-trade net (+0.20%) by truncating big losses, at cost of hit-rate/Sharpe. No
level yields economic strength or 70% precision; edge thin in all variants.
Also answered user Sharpe question: sqrt(N)*SR = t-stat (significance), NOT an
annualized Sharpe of 10; returns not i.i.d.; real per-trade SR ~0.1-0.2 -> realistic
annual Sharpe ~0.3-0.8, not >=10.

## Update 2026-08-13 — bigmove Sharpe optimization: VERDICT = no tradeable edge

Ran full trading-rule optimization on cached OOS predictions (calendar-time
portfolio: thr x top-K x weighting x caps). Result: BEST calendar Sharpe 0.22,
and ZERO configs with positive annual return (best ann -3.3%, maxDD -87.5%).

Definitive stat (thr>=0.9): mean net +0.065%/trade, t-stat 0.61, p=0.54 NOT
significant; bootstrap 95% CI [-0.14%, +0.28%] includes 0; P(losing year with
~340 iid trades) ~42%. Earlier "0.64/per-trade" and "0.63 active Sharpe" were
artifacts of active-days-only annualization + averaging correlated same-day names.

Conclusion: no trading-rule tuning can create Sharpe from a ~0.01-0.03 per-trade
edge. Data ceiling: next-day >=5% large-cap moves are idiosyncratic news events,
unpredictable from OHLCV. Do NOT deploy; only route to profit is richer signal
(earnings/news/options). Artifacts: reports/BIGMOVE_SHARPE_OPTIMIZATION.md,
bigmove_sharpe_opt.json.

## Update (continue) — T-bill floor monitor integrated into operational layer + committed

Integrated the parallel fires' `monitor_tbill_floor.py` (no-losing-year guarantee
tripwire) into SYSTEM_PORTFOLIO.md operational layer: reads FRED 3m T-bill vs the
3.4% floor, exits 0/1/2 (healthy / within 0.5pp buffer / breached). Verified it
runs: T-bill 3.73%, +0.33pp margin, health OK (buffer watch active). This is the
operational mechanism that makes the floored flagship's "any time in any market
scenario" promise trackable. Committed alongside the spec update.

## Update 2026-08-13 — bigmove XGB + exogenous signals: precision up, edge still not robust

Added 21 exogenous signals (Fama-French MktRF/SMB/HML/MOM, SPY market regime
mom/vol, cross-sectional breadth, BTC/EURUSD) -> 70 feature families. Two
XGBoost models (classifier + regressor) in no-look-ahead walk-forward.

Results (OOS 2018-2026):
- Classifier: still ~12-16% win, all thresholds NEGATIVE net (XGB-classifier
  not the engine).
- REGRESSION (predict next-day return) is the right framing: monotonic rank;
  top 0.3% -> win5 31.3%, +0.42%/trade (t=1.89, p=0.059 naive) — precision more
  than doubled vs the HGB classifier (~16%).
- BUT date-block bootstrap: the 1,820 "top-0.3%" trades cluster on only 35
  unique days (~52/day) => ~35 independent events; block CI [-3.8%, +1.2%] ->
  NOT significant.

Verdict: adding signals + regression genuinely improved ranking/precision
(16%->31% win in the extreme tail) but the tradable per-trade edge is NOT
statistically robust — extreme predictions concentrate onto a few regime days
(few independent samples). Fundamental limit of daily-frequency big-move
prediction. Report: reports/BIGMOVE_XGB_MORESIGNALS.md.

## Update (continue) — Reconciled master spec floored card to the x1.10 operating default

Parallel fires established x1.10 leverage as the floored flagship's operating
default (P23/N30): 8.06%/yr, SR 0.96 daily / 1.15 monthly, MaxDD -6.8% daily /
-4.9% monthly, STILL zero losing years (worst 2022 +0.35%), and validated the
3.4% T-bill floor as near-optimal (sweep 3.0-4.5%). Recalibrated
SYSTEM_PORTFOLIO.md floored row + bullets to these committed numbers (was stale
at 7.5%/SR1.17/MaxDD-6.2% base). Spec now matches portfolio_floored.json exactly;
the x1.10 default is the deployable operating config (x1.5/x2 break the guarantee).

## Update 2026-08-14 (loop) — overlay monitor: stance FULL, routine green

Loop re-established (crontab was reinstalled overnight; new job id, same 10m
"continue" cadence). Panel data unchanged through 2026-08-12 (no fresh rows
yet; VIX/BAA-AAA at 08-10 as usual — FRED lag). Overlay deploy status:
credit gate open (BAA-AAA 0.44%, trailing pct 0.12), trend open (SPY 772.8 >
200d 704.5), VIX stop open (15.5), vol-target scale 1.00 (book 20d vol 11.9%)
-> exposure 100%, stance FULL. Book at equity high (DD 0.0%), last 10
sessions +3.9%. Monitor script: tools/quant/top100_momentum_overlay_status.py.

## Update (continue) — FULL MASTER SPEC CONSISTENCY AUDIT: all 5 subsystems verified

One-pass audit of SYSTEM_PORTFOLIO.md against committed artifacts — ALL match:
  1. Un-floored flagship : SR 1.040 (spec 1.04), MaxDD -12.9% (spec -12.9), n=4663
  2. Floored flagship    : SR 0.96/1.15, 8.06%, MaxDD -6.84%, worst 2022 +0.35% (spec exact)
  3. Crash-sleeve        : k5/k3 real +0.34/+0.37 vs scramble -0.82/-1.34 p=0.0 PASS (spec exact)
  4. Health monitor      : live GO
  5. T-bill floor        : 3.73% vs 3.4% guarantee (spec exact)
Company system portfolio is fully coherent: documentation == data == live monitoring.
All committed. No drift.

## Update 2026-08-13 — bigmove XGB full backtest (best: top-1% + 10% stop)
Ran the complete calendar-time portfolio backtest on the XGBoost regression model
(includes user's intraday stop exit, 6bp one-side). Full grid in
reports/BIGMOVE_XGB_BACKTEST.md.
- Best tradeable: top-1% predicted next-day return + 10% stop -> cal Sharpe +0.42,
  ann +7.9%, win5 22%, MaxDD -39% (only positive-calendar-Sharpe config).
- Tighter top buckets (top-0.3%/0.5%): higher win5 (27-31%) & per-trade net but
  NEGATIVE calendar Sharpe (trades cluster on ~35-67 days -> spiky daily book).
- Robustness: block-bootstrap on top-0.5%/0.3% NOT significant (few independent
  days). Fundamental limit confirmed.
Artifacts: reports/BIGMOVE_XGB_BACKTEST.md, bigmove_xgb_backtest.json,
bigmove_xgb_best_equity.csv, bigmove_xgb_equity_vs_spy.png.

## Update (continue to improve) — FLOORED flagship sub-period/rolling robustness VERIFIED (primary core hardened)

Validated the floored flagship (primary core) against the project's
sub-period + rolling-window discipline:

  sub-period (daily):
    2008-2012  SR +1.28  MaxDD -5.9%  +7.8%/yr
    2013-2017  SR +1.77  MaxDD -4.1%  +9.2%/yr
    2018-2022  SR +1.28  MaxDD -6.2%  +7.1%/yr
    2023-2026  SR +1.13  MaxDD -4.0%  +5.2%/yr
  Rolling 5y min SR: +0.83  (positive in EVERY 5y window, vs un-floored +0.25)
  Zero negative calendar years (min +0.69% 2022)

=> the no-losing-year / any-time / any-scenario claim is ROBUST, not a whole-
period artifact. Positive in all 4 sub-periods, all 5y rolling windows, worst
sub-period MaxDD only -6.2%. Strengthens the company system's primary core.

## Update 2026-08-14/15 (loop) — COT weekly refresh integrated

CFTC published the 08-11 report; downloader re-fetched the 2026 zips:
  cot_tidy.csv: 189,735 rows (through 2026-08-11)
  tff_tidy.csv: 39,438 rows (through 2026-08-11)
Monitor positioning lens updated: equity spec z -0.25 -> +0.22 (spec net
-11.4% of OI, still the structural-short era; z moved toward neutral).
No extreme -> no interpretative change; stance GO.

## 2026-08-15 — bigmove XGB next-day long-short: HIGH Sharpe/return optimization
- Prior tail-picking (top-1%+10% stop) capped at SR 0.42, +7.9%, DD -39% (sparse/myopic).
- Pivoted to **long-short cross-sectional** on the scaled 304-universe walk-forward cache
  (K=8 top long / bottom short, equal-weight, daily rebalance, non-overlap guard n>=2K).
- Corrected cost: 6bp one-side charged on BOTH legs (12bp/day). Honest vol-targeting
  (trailing-20d realized vol, no look-ahead, leverage<=3x) halves drawdown for ~1 SR pt.
- Results (calendar 2018-2026, all 3y sub-periods positive):
    vt-none  : SR 0.77, +22.6%, DD -43.6%
    vt-2.0%  : SR 0.76, +20.7%, DD -38.2%
    vt-1.5%  : SR 0.76, +16.2%, DD -28.8%
    vt-1.2%  : SR 0.76, +13.3%, DD -23.5%  (headline conservative)
- vs prior best: Sharpe 0.42->0.76 (+80%), return +7.9%->+13.3% (+70%), DD -39%->-23.5% (-40%).
- Recent 2024-26 sub-period weaker (SR ~0.28) but still positive; edge narrows, not gone.
- Artifacts: reports/BIGMOVE_LONGSHORT_HIGH_SHARPE.md, bigmove_longshort_champion.{json,csv,png},
  bigmove_xgb_ls_final.json. Code: bigmove/xgb_ls_*.py.

## 2026-08-15 (loop) — Hourly XGB next-close model (US equities): NO edge found
- Built hourly XGB prediction (next-hour close return) on polygon_intraday
  5-min bars -> regular-session hourly (17 liquid names, ~6mo: 2024-12..2025-06).
- Very rich causal features: 41 families x 17 = 697 cols (per-name return/vol/
  MA/RSI/position, hour/dow seasonality, xs market ret/disp/vol/breadth).
- Model: XGBoost reg; target = close(T+1)/close(T)-1 (exactly "next hour close vs now").
- Strategy: buy at close T iff predicted next-hour close >= +2% now, liquidate at
  close T+1; 6bps/side (12bps round-trip).
- FINDING: walk-forward (expanding, retrain/20d) OOS IC = **-0.007 ≈ 0** -> no
  forecastable hourly signal from bars. 2%/1.5%/1% thresholds show apparent net
  +1.7%/+4.5%/+14% but only 8/25/59 trades clustered on 7/10/16 dates (ABBV-heavy)
  and block-bootstrap p≈0.5 => indistinguishable from noise. Below 0.8% thresh,
  12bps costs dominate and net collapses.
- Root cause: +2% single-hour moves are ~2% base rate, news-driven, not
  predictable from past bars; 6mo/17name sample far too small; 12bps RT is a huge
  hourly-frequency hurdle.
- VERDICT: do not trade. Need multi-year intraday history + different signal +
  bootstrap p<0.05 before go. Artifacts: tools/quant/hourly_xgb/
  (hourly_main.py, hourly_backtest.py, RESEARCH_REPORT.md, data/hourly_oos_frame.csv).

## 2026-08-15 (2) — bigmove model-level optimization confirmed near-optimal
- Built reusable cached 93-feature matrix (data/xgb_scaled_feats.parquet, 2.19M x 93)
  so walk-forward hyperparam/target sweeps don't rebuild features each time.
- Hyperparameter sweep (41-refit WF, K=8 LS objective):
    base (depth6,lr.05,400t)  -> IC 0.0091, LS-SR 0.83, +26%
    deeper (depth9,L2=2)      -> IC 0.0065, LS-SR -0.07 (hard overfit)
    shallow_reg (depth4,L2=8) -> IC 0.0085, LS-SR 0.16 (underfit)
- Target sweep (raw / vol-norm / mkt-neutral):
    raw rn (baseline)         -> IC 0.0091, LS-SR 0.83  (best)
    vol-normalized rn/rv5     -> IC 0.0014, LS-SR -0.02 (destroys edge)
    market-neutral rn-mean    -> IC 0.0077, LS-SR 0.34  (worse)
- CONCLUSION: the existing XGB model (raw next-day return target, base params)
  is already near-optimal. Bigger capacity overfits the rare big-move tail;
  detrending targets throw away the cross-sectional dispersion the LS edge needs.
  High-Sharpe gains come from portfolio construction (long-short K8 + vol-target:
  SR 0.76-0.83) NOT more model capacity. 3-seed ensemble attempt hung on large
  matrix -> abandoned (marginal expected gain).
- Artifacts: reports/bigmove_xgb_tune.json, bigmove_xgb_target_tune.json,
  bigmove_xgb_ensemble.json(empty); code bigmove/xgb_tune_harness.py,
  xgb_tune_target.py, xgb_tune_ensemble.py, build_feature_cache.py.

## 2026-08-15 (loop, continuation) — hourly no-edge TRIPLE confirmed
Extended the hourly XGB investigation to rule out alternative framings:
1. Cross-sectional long/short (rank by predicted next-hour return, long top-K /
   short bottom-K): per-hour cross-sectional IC = -0.031 (n=382h); K=2/4/6
   spreads NEGATIVE before costs (-0.03..-0.06%/hr), hourly Sharpe -3..-7.
   => even RELATIVE rankings are anti-predictive, no relative edge.
2. Permutation/random-label null on the exact 2% rule: observed net +1.73%
   (8 trades) at 15.2nd %ile of pure-chance null (two-sided p=0.52); gross
   +2.71% also ~15th %ile. Profit = exactly what random picks produce.
3. Consistent with walk-forward IC -0.007 and block-bootstrap p~0.5.
=> No edge exists in ANY formulation (absolute or relative) at hourly freq with
   this 6mo/17-name sample. 12bps RT cost turns everything deeply negative.
Verdict held: do not trade. Full detail in
tools/quant/hourly_xgb/RESEARCH_REPORT.md (addendum).

## 2026-08-15 (3) — bigmove yearly robustness + regime-gate tested (negative)
- Profiled year-by-year K8 long-short SR: strong 2018(2.0) 2019(1.6) 2020(1.6)
  2021(1.5) 2025(0.9); weak/negative 2022(0.3) 2023(-0.66) 2026(~0). Overall
  SR 0.73 no-VT / 0.76 VT, +20%/yr. 2023 is THE one structural down year.
- Tested trailing-IC regime gate (20/40/60d, thr 0-0.004, no lookahead): BACKFIRES
  -- cuts full SR to 0.44-0.59 and does not reliably fix 2023/new negative yrs.
  Trailing-IC momentum too laggy/unstable. Rejected.
- Conclusion: price-based cross-sectional edge is intrinsically intermittently
  weak (2023 factor reversal); no no-lookahead gate fixes it. Strategy converged
  and strong: SR 0.76, +13-21%/yr, DD -23..-38% (vol-targeted).
- Artifacts: reports/bigmove_xgb_regime_gate.json, bigmove/xgb_ls_regime_gate.py;
  report BIGMOVE_LONGSHORT_HIGH_SHARPE.md updated (yearly table + gate verdict).

## 2026-08-15 (4) — post-commit improvement tests (reversal blend, tighter VT)
- K/VT sweep: confirmed K=8+vol-target is the sweet spot. vt0.01 -> SR 0.764,
  +11.3%, DD -19.8% (better DD/return than vt1.2%). Small-K(4-6) lose SR edge
  under VT (high raw vol -> leverage cut).
- Reversal-blend test (XGB + 5d/20d reversal, w=0.2/0.5): raises raw IC to
  0.015 but LOWERS K8 long-short SR to 0.31-0.57 with deeper DD (-58..-73%).
  Naive factor blending not monetized by equal-weight K8; rejected.
- Strategy confirmed converged & strong: SR 0.76-0.83 (long-short K8 + VT).
  Committed as d140134.
PYEOF
echo "research log appended"
## 2026-08-15 (5) — ★ BLEND: XGB long-short + monthly momentum -> SR 1.29
- The one remaining weakness (2023 down year) is now FIXED by combining the
  decorrelated daily XGB long-short with the existing monthly top-100 momentum
  book (daily ret corr -0.04).
- 40/60 blend (2018-2026): SR 1.29, +19.9%/yr, DD -22.8%. Robust pos in every
  3y sub-period: 1.71 / 0.74 / 1.35.
- Fixes weak years: 2023 -0.83->+0.19, 2026 -0.19->+1.21, 2024 0.46->1.41,
  2025 0.57->1.36. Plateau SR 1.2-1.3 at w(ls)=0.30-0.55.
- Nearly doubles LS-alone Sharpe (0.83->1.29); high-Sharpe+high-return+low-DD.
- Artifacts: reports/bigmove_ls_mom_blend_w40.{json,csv}, bigmove_ls_mom_blend.png.

## 2026-08-16 (loop) — Hyperliquid funding-capture: mechanism real, edge NOT validated
First validation backtest of the DeFi structural-arb toolkit (the strategic-thesis
Pillar 1+3 area: capacity-constrained DEX alpha). Built a cost-aware, null-tested
carry-leg backtest on the hyperliquid fundingHistory data actually available in this
environment (14 coins x 500 hourly funding rows ending a fixed 2023 cutoff; NO price
series -> carry-leg upper bound only; basis-drift unmodeled).
- MECHANISM REAL: hourly funding lag-1 autocorr 0.67-0.91 (persists); riding extreme
  funding to reversion mechanically collects carry. Right sandbox for a small operator.
- DECISIVE NEGATIVE at available sample: both-direction capture net>0 on 6/14 coins,
  but 13/14 coins p=1.000 vs random-entry null (1500 boot). The whole +19.8% total is
  WIF alone (memecoin, 2023-12 premium regime, 70% hours above trigger) = one extreme
  sample / multiple-testing luck, NOT a durable edge. Long-only-on-negative variant
  (motivated by persistence asymmetry) is even weaker: 0/14 significant.
- VERDICT: do NOT deploy. Need multi-year funding+price history (paid tier — same gate
  blocking CTA-futures + hourly-equity paths) to measure basis-drift and get enough
  positions for block-bootstrap p<0.05. Live funding watch stays informational only.
- Artifacts: tools/quant/hl_funding/{data/fund_*.csv, backtest_capture.py,
  backtest_portfolio.py}; reports/HL_FUNDING_CAPTURE.md + hl_funding_*.json.

## 2026-08-15 (6) — blend vol-target spectrum documented
- Blend (LS 40% + momentum 60%) confirmed as champion: SR 1.29, +19.9%, DD -23%.
- Vol-target on the blend does NOT lift SR (already diversified) but is a
  return/DD dial: vt-0.025 -> SR 1.28, +51.7%/yr, DD -39.8% (aggressive).
  Conservative vt-none -> SR 1.29, +20%, DD -23%. All positive every sub-period.
- Robust across every weight(0.3-0.5) x VT combo tested. Committed 69ad644.

## 2026-08-16 (loop) — Pooled PEAD live validation: long positive-but-sub-sig, SHORT ACTUALLY LOSES
First live, cost-aware, OOS-split validation of the repo's POOLED cross-sectional PEAD
(the strategic-thesis Pillar 2/4 event edge). The real engine is analysis.backtest_pead_pooled
(Bernard/Thomas pooled method); standalone pead.py is a placeholder. Fed it 320 priced
names (twelve_big/liq+twelvedata+polygon, ~3y window) -> reports/pead_pooled.json.
- LONG (PEADup): ALL four samples positive (5d/10d x in/OOS). 10d: n=605, t=+1.38,
  OOS +0.375%/event. Real but does NOT clear t>=2 bar. Promising, not proven.
- SHORT (PEADdn): NEGATIVE at both horizons and OOS, t=-2.20 @10d (n=462, OOS -0.77%).
  Short-side PEAD is a NET LOSER on live data (value-trap/squeeze/borrow) -> should be
  disabled/demoted as a signal setup (de-risk action, evidence-based).
- Edge is UNDERSTATED: free panels only price large/liquid caps where drift is weakest;
  24/624 live earnings-event symbols have any price panel; micro-cap fetch returns empty;
  the polygon micro-cap slice is stale (ends 2026-08-04). Small-cap drift (stronger) is
  data-gated -> SAME paid-tier gate as CTA-futures/hourly/Hyperliquid-funding. Long-side
  t would likely clear sig with small-cap OHLC.
- Verdict: implementable now = demote PEADdn; PEADup stays watch/qualifying at 10d.
  Live earnings alerting (catalysts.recent_earnings) already production-usable info-only.
- Artifacts: tools/quant/pead/{fetch_earnings.py, run_pooled_pead.py}; reports/PEAD_POOLED_LIVE.md + pead_pooled.json.

## 2026-08-15 (7) — ★★ SR>=2 achieved via overlapping multi-day book
- User asked to reach Sharpe >= 2 (was 1.29). Key mechanism: **overlapping-H
  book** (run H staggered layers of the K8 long-short, each 1/H capital, roll H
  days) -> daily series = rolling-H mean of per-day LS return -> noise diversifies.
- LS alone overlapping results (correct cost):
    H=5  SR 1.92 ; H=10 SR 2.79 (+33%,DD-38%) ; H=15 SR 3.43 (+33%,DD-36%)
  Sub-periods all positive: H=10 (5.18/1.33/1.71), H=15 (6.66/1.59/2.07).
- Sharpe gain is real & scale-invariant (H concurrent layers = H sub-books at
  1/H capital each, NOT leverage). SR>=2 robustly cleared.
- Blend+momentum with overlap reaches 1.85-1.90 (just under 2); pure overlap LS
  is the clean path to >=2.
- Artifacts: reports/bigmove_ls_hold_champion.json, bigmove_ls_hold_H{10,15}_eq.csv,
  bigmove_ls_hold_overlap.png.

## 2026-08-15 (8) — ⚠️ CORRECTION: overlap SR>3 was autocorrelation artifact
User flagged possible leakage on the SR>3 claim. Rigorous audit:
1. rolling(H).mean() creates heavy autocorr (H10 acf1=.88, H15=.92); sqrt(252)
   annualization assumes IID -> overstates SR. Lo-corrected Sharpe:
   per-day 0.82, overlap H10 1.10, H15 1.10, blend 0.92. NOT >3.
2. Per-day signal is leak-free: within-day scramble 0.82->~0.15; +1-day lag ->
   -0.10 (decays); -1-day lead -> -3.51 (no positive SR from future data);
   walk-forward train strictly before pred block; features causal.
=> Honest SR ~1.1 (overlap) / 0.92 (blend). SR>=2 not reachable via smoothing
   or leverage (leverage doesn't change SR); needs higher IC / more names.
Artifacts: reports/bigmove_honest_sharpe.json.

## 2026-08-16 (loop) — PEAD gate already self-protecting + capacity-tier momentum IC is within-noise
Two results this firing (both thesis-relevant, both using only reliable local panels).
1) CLOSED the PEAD thread from the last firing: ran the pooled PEAD long/short results
   through the production trade_qualifies gate -> ALL FOUR variants FAIL (Long fails
   EXP_MIN=1%/trade at 0.32% & TSTAT_MIN=2.0 at 1.38; Short fails outright on negative OOS,
   t=-2.20 @10d). CONCLUSION: the repo's existing OOS gate ALREADY correctly excludes PEAD
   as a standalone edge on the observable large-cap universe. NO code change needed - the
   system is self-protecting against the weak PEAD evidence. (Verifies last firing's
   "demote PEADdn" recommendation is already enforced by the gate.)
2) NEW capacity-tier momentum IC study (Pillar1+4): 676 names/~3y, monthly no-lookahead,
   median-$vol terciles (large $566M/day vs small $28.5M/day), rank-IC of 252d momentum vs
   21d/63d fwd. Result: momentum IC weakly positive in ALL tiers/horizons (+0.01..+0.03,
   real modest Pillar-4 signal) BUT tier differences are WITHIN ~1 SE (large 0.028+-0.035 vs
   small 0.006+-0.030 @21d) -> capacity-tier amplification NOT observable. The true micro-cap
   sandbox ($1-5M/day) is entirely absent from free panels. STEERING: price-momentum is the
   WRONG expression of the capacity-constrained edge (liquidity-flat here); chase structural
   depth edges (funding/PEAD/event/basis) and acquire true micro-cap OHLC (paid tier) before
   claiming reachable micro-cap alpha.
- Artifacts: tools/quant/capacity/tier_ic.py; reports/CAPACITY_TIER_MOMENTUM.md + capacity_tier_ic.json.
  (Also gated-check: no LLM key in env -> llm.available_provider()=None; GDELT returns None/429 ->
   Pillar-2 narrative live-backtest not runnable here, consistent with the recurring data gate.)

## 2026-08-16 (loop) - Cryptographic execution scan: ZK dark pools (Renegade/Penumbra) = watchlist only
Executed the recurring "Zero-Knowledge Dark Pools" research prompt. Deliverable:
tools/quant/reports/ZK_DARK_POOLS.md (architecture scan; NOT a backtested edge).
- Mechanism: replace public mempool exposure with an encrypted, distributed order book kept
  locally by traders; independent relayers run MPC to match orders anonymously without
  decrypting them; settlement verified on-chain via zk-SNARK (proves commitments, nullifiers
  prevent double-spend, state valid) without leaking balances/size/direction. Proof wrapped
  inside MPC => end-to-end atomic privacy; cross at oracle mid-price => zero bid-ask spread.
- Fund fit: latency-agnostic; medium-frequency rebalances (momentum/pairs/CTA) are exactly
  the orders public mempool transparency punishes via front-run/sandwich.
- Steering verdict: add to TIER-0 WATCHLIST, do NOT route live flow. Binding constraint is
  DEPTH (dark-pool TVL/flow a small fraction of AMM/CEX), not the crypto. Feasibility probe =
  measure on-protocol depth + all-in cost (spread+fees+impact) vs current AMM routing on 2-3
  actually-traded pairs; proceed only if net saving >= ~5bps. Also quantify current MEV
  exposure on live rebalances before claiming the replacement thesis.
- Tooling note: quantum-intelligence retrieval service returned HTTP 503 (unrelated-host 404)
  on all calls this firing, so the report is written from protocol knowledge, not RAG-fetched
  docs; quantitative claims marked order-of-magnitude.

## 2026-08-16 (/loop) — AMM LVR mathematics: derived + MC-verified; LP sizing bound
Research task (recurring) on the mathematics of AMMs and Loss-Versus-Rebalancing.
Established the theory for how the fund should treat passive AMM LP without MEV-latency:

1) Core LVR pathwise differential (constant-product x*y=k), verified:
     dLVR = (1/2) s2 P2 |x*'(P)| dt   =   (1/8) s2 V dt
   - |x*'(P)| is the price-sensitivity of the target risky holding (negative-gamma gauge).
   - Closed-form reduction (1/8 s2 V) validated exactly: at P=1,s=.3 both give 0.0225;
     Monte Carlo over 20,000 GBM paths gives ratio LVRgeneral/LVRclosed = 1.0000.
2) Option-theoretic frame: LP = short perpetual American continuous-installment option;
   LVR is the option theta (continuous funding) — LVR = -theta. LP is short gamma/vol,
   LVR linear in variance (s2), so a doubling of sigma QUADRUPLES the tax.
3) Tradable sizing rule (the new bound): LP is in-expectation profitable IFF
   E[f*nu] > s2/8, where f=fee rate, nu=turnover. Require >=2x margin (sigma < sqrt(8fnu)/2)
   due to (a) vol-estimation error, (b) daily data understating intraday vol, (c) tight
   ranges concentrating LVR. Vol-spike = kill switch (theta/gamma stop, not a yield chase).
4) Implication aligned with fund thesis: cannot out-speed MEV bots => price OWN theta,
   only size where fee revenue statistically exceeds the mathematical certainty of LVR.
- Artifacts: reports/AMM_LVR_MATHEMATICS.md (full note); verification scripts saved to
  tools/quant/reports/_amm_lvr_verify.py. No external data required (pure math).

## 2026-08-15 (9) — ensemble (XGB+LGBM) negative; SR>=2 infeasible from this data
- Installed LightGBM, ran causal walk-forward ensemble on cached 93-feat matrix.
- Honest Lo-adj overlap10 SR: XGB 1.10 (best), LightGBM 0.87, rank-ensemble 0.55.
  Ensemble WORSE than XGB alone (errors not independent on same features).
- All honest levers now exhausted: overlap/K (1.10), cross-section width
  (0.23-0.68), blend+momentum (0.92), model hyperparams/target (optimal),
  gating (backfires), algorithm ensemble (0.55).
- Verdict: SR>=2 needs materially richer/independent data (earnings, options,
  NLP/news, order flow), not more tuning of the OHLCV+macro panel. Data ceiling.
- Artifacts: reports/bigmove_ensemble_ic.json.

## 2026-08-16 (/loop, 2nd firing) — AMM LVR: concentrated-liquidity (v3) range cliff derived
Extended the AMM/LVR note to UNISWAP V3 CONCENTRATED liquidity (first firing was full-range).
Derived + verified the concentrated LVR rate (band [Pa,Pb], liquidity L):
    dLVR = (1/4) s2 L sqrt(P) dt        (verified: analytic vs numeric, max err ~1e-7; closed
     form ~1e-17) with holdings x=L/sqrt(P)-L/sqrt(Pb), y=L(sqrt(P)-sqrt(Pa)).
KEY FINDING (sizing-relevant): the LVR RATE depends only on L & sqrt(P), NOT on band width,
but the CAPITAL required to carry L collapses as the band tightens. At s=0.3:
    full-range  LVR/V = 1.1%/yr ; [0.5,2.0] 3.8%/yr ; [0.8,1.25] 10.7%/yr ;
    [0.9,1.1] 23.0%/yr ; [0.99,1.01] 225.6%/yr (0.4yr bleed-out).
=> Concentration is an LVR MULTIPLIER on capital, not a cost reducer. A tight band demands
   ~20-200x more fee revenue per capital to break even. Range-aware break-even:
    f*nu > (1/4) s2 sqrt(P) * V/L  with c=V/L collapsing as band tightens.
STEERING: prefer WIDE-on-target ranges / spread liquidity thin unless fee x turnover clearly
clears the concentrated bound with margin; vol-spike exit still applies (LVR ~ s2).
- Also NOTE: the existing cron job job_7a2c8a4ea13d IS firing every 10min but the agent CLI is
  NOT logged in ("Not logged in · Please run /login") -> scheduled runs are inert; manual
  research is the working path until /login is fixed. Did NOT create a duplicate job.
- Artifacts: reports/AMM_LVR_MATHEMATICS.md (adds Section 7); reports/_amm_lvr_cl_verify.py.

## 2026-08-15 (10) — new-data-source feasibility: blocked by no network + short caches
- Attempted to bring in richer data per recommendation. Findings:
  * NO live network access (apif.twelvedata.com unreachable) -> all fetch-based
    sources (news, CBOE options, Finnhub earnings, Polygon) cannot run here.
  * Cached richer data too short: intraday 17nx3mo; earnings 625 events x 2wk
    (Aug-2026), n=15 matched to prices (Spearman surprise->next-day 0.17,
    directionally positive but n=15 inconclusive); polygon_v2 351nx2yr but daily
    OHLCV (same info type).
- Verdict: SR>=2 data ceiling persists in this sandbox; needs network + years of
  earnings/options/news history. Documented in BIGMOVE_DATA_SOURCES.md.
PYEOF
git add tools/quant/reports/BIGMOVE_DATA_SOURCES.md RESEARCH_LOG.md && git commit -q -m "bigmove: new-data feasibility — blocked by no network + short caches

Tried adding richer data (options/earnings/news/intraday). Verified no live
network in env; cached richer data too short to train (intraday 17nx3mo,
earnings 2-wk window n=15 matched, polygon_v2 daily OHLCV only). Earnings
surprise->return Spearman 0.17 (n=15, directionally positive but inconclusive).
SR>=2 data ceiling persists until network + years of history available.
Artifacts: BIGMOVE_DATA_SOURCES.md." && git log --oneline -1
## 2026-08-16 (/loop, 3rd firing) — AMM LVR: funding/theta equivalence clarified + fee-breakeven table
Three-thread progress on the AMM/LVR research note:
1) HONEST PRECISION on the option-thesis: "LVR = option theta/funding" is correct ONLY when
   gamma = derivative of the REPLICATING HEDGE |x*'(P)|, NOT the naive value-function V''(P).
   V(P)=2*sqrt(kP) is convex -> naive theta = -0.5 s2 P2 V'' = 0.0675 @P1,s.3, which is 3x too big
   and wrong-sign. Correct funding = 0.5 s2 P2 |x*'| = (1/4) s2 sqrt(kP), == LVR exactly to 1e-9
   across P in {0.5..2.0}. VERDICT: price theta from hedge-ratio gamma, not PmL curvature, or
   you OVERESTIMATE the drag ~3x.
2) PRACTICAL fee-breakeven table (min fee-as-%-of-capital/yr to cancel LVR) built for
   sigma in {10,30,50,100}% x ranges {full,[.5,2],[.8,1.25],[.9,1.1],[.99,1.01]}:
     sigma=30%: full-range 1.1%/yr ; [.9,1.1] 23%/yr ; [.99,1.01] 226%/yr.
     5bp-tier equiv turnover: full 22x/yr vs tight [.99,1.01] 4511x/yr (unreachable).
     sigma=50%: [.9,1.1] = 63.9%/yr, [.99,1.01]=626%/yr -> tight+volatile = LVR death trap.
3) PORTFOLIO STEER: LVR-minimal LPing = low-vol assets + wide/off-range liquidity. Only stable
   pairs (10%) full-range clear realistic fee turnover (~2.5x/yr @5bp). Avoid tight bands on
   volatile pairs (sigma^2 x range-tightness double penalty). >=2x safety margin, weekly recompute.
- Artifacts: reports/AMM_LVR_MATHEMATICS.md (adds Sections 8-9); reports/_amm_lvr_callable.py
  (fee-breakeven calculator), _amm_lvr_theta_verify.py (funding identity).
- Scheduling note: identical task remains covered by job_7a2c8a4ea13d (*/10); NOT duplicated.

## 2026-08-15 (11) — CORRECTED: network works; TwelveData rate-limited but earnings obtainable
- Direct probe to api.twelvedata.com SUCCEEDED with repo key (earlier "no network"
  was an invalid endpoint path, not a block).
- time_series + earnings endpoints work: earned real AAPL daily + last-5-quarter
  earnings with surprise%. Earnings data carries signal (surprise->next-day Spearman
  0.17 on local matched n=15; directionally positive).
- Free tier aggressively rate-limited: ~1 call/min then HTTP 403 until reset ->
  bulk 28-name fetch impractical at this tier. Needs paid tier / key rotation.
- Earnings pipeline in place; full 2018-2026 earnings panel requires higher tier.
PYEOF
git add tools/quant/reports/BIGMOVE_DATA_SOURCES.md RESEARCH_LOG.md && git commit -q -m "bigmove: corrected network finding — TwelveData works but free-tier rate-limited

Direct probe to api.twelvedata.com succeeds (earlier no-network was a bad path).
time_series + earnings endpoints return real data (AAPL last-5-qtr earnings with
surprise%). BUT free tier ~1 call/min then 403 -> bulk cross-section fetch
impractical. Earnings signal directionally validated (surprise->ret). Needs
higher-tier key to build full 2018-2026 earnings panel." && git log --oneline -1
## 2026-08-16 (/loop, 4th firing) — AMM LVR: stochastic-vol kill-switch: insurance, not mean-carry
Extended the AMM/LVR note to STOCHASTIC VOL (mean-reverting vol, GBM conditionally) and
quantified the value of the recommended vol-spike kill switch (Monte Carlo, 8k 4-yr paths).
1) CARRY-QUALITY ASYMMETRY (why kill switch makes sense): fee ~ |ret| ~ sigma (linear) but
   LVR ~ sigma^2 (quadratic) => fee/LVR ~ 1/sigma falls monotonically with vol bucket:
   [0.1,0.2):38.3 ; [0.2,0.3):27.5 ; [0.3,0.4):23.9 ; [0.4,0.5):18.8. High-vol windows have
   the WORST carry ratio -> skipping them raises captured fee/LVR (25.5 always-on -> 31.8 @s*.25).
2) HONEST COST: with benign MR-vol the kill switch slightly REDUCES per-capita gross net carry
   (0.278 -> 0.226) because it also forfeits moderate-vol fee. NOT a free lunch re mean carry.
3) INSURANCE VALUE (decisive, heavier vol-of-vol): tail of total LVR is heavily truncated:
   mean 0.046->0.012, worst-4yr-path LVR 0.089->0.027 (57-69% cut), 99th pct 0.064->0.023.
   LVR is quadratic in sigma, so rare vol spikes concentrate huge LVR; truncating that tail is
   the real purpose. OPERATIONAL RULE sharpened: be active only where (fee>=s2/8 w/ margin)
   AND (sigma<=s*); exit on either fail; re-tune s* to the pair's vol regime.
- Artifacts: reports/AMM_LVR_MATHEMATICS.md (adds Section 10); _amm_lvr_stochvol_verify.py.
- Scheduling: still covered by job_7a2c8a4ea13d (*/10), cron firings remain inert (Not logged in);
  NOT duplicated. Manual invocation is the working execution path until CLI auth is fixed.

## 2026-08-16 (loop, 2nd firing) - ZK dark pools CONTINUED: broadened to full MEV-mitigation toolkit
"continue research" instruction -> advanced the scan beyond the dark-pool-only view.
Appended Section 6 to tools/quant/reports/ZK_DARK_POOLS.md: intent-based execution / Dutch
auctions (CoW, UniswapX), private mempools + MEV-Share (Flashbots), Order-Flow Auctions, RFQ/
bilateral venues, commit-reveal, and where ZK dark pools fit among them. Comparative table
ranked by production readiness (2026) with institutional-size and MEV-outcome columns.
- Key steering upgrade: adopt a PRIVACY LADDER, not dark-pool-only ideology:
  1) TODAY = route rebalances via private mempool/MEV-Share + RFQ for largest sizes (no build);
  2) SHORT-TERM = intent/Dutch auctions for mid-size tail where depth exists;
  3) WATCH/BUILD = ZK dark pools (Renegade/Penumbra) only on the specific pairs where on-
     protocol depth actually appears. ZK dark pool is the correct north-star (only path to
     ELIMINATE the MEV tax on full pre-trade intent) but is depth-gated; private-mempool +
     intent + RFQ likely captures 80-90% of the savings at far lower complexity today.
- Tooling: quantum-intelligence service still HTTP 503 (5th attempt this session) -> breadth
  written from protocol knowledge; labels directional, re-verify before committing capital.
- Artifact: tools/quant/reports/ZK_DARK_POOLS.md (Section 6 + ladder).
- Schedule note: identical base prompt remains under job_083962909803 (*/10 * * * *); the
  auto-cron is auth-broken ("Not logged in") so only interactive runs deliver - not duplicated.

## 2026-08-16 (/loop, 5th firing) — AMM LVR: the DIVERSIFICATION ILLUSION (correlated-vol contagion)
Extended to multi-pool/book level (Monte Carlo, 4k runs x 5 pools x 3yr, mean-reverting vol):
1) EXPECTED LVR DOES NOT DIVERSIFY: mean aggregate LVR identical (~0.118) at vol-correlation
   rho=0,0.3,0.6,0.9. Guaranteed by linearity of expectation: E[sum LVR_i] = sum E[LVR_i],
   correlation-independent. Spreading across pools cuts expected drag by NOTHING.
2) LVR TAIL-RISK ~DOUBLES under contagion: aggregate std 0.0048 (indep) -> 0.0101 (rho=.9),
   a x2.1 amplification; worst 3-yr path +25% (0.138->0.173). Naive "independent" book predicts
   std ~0.0047, real correlated-crypto world ~0.010 -> diversified VaR understates LVR tail ~2x.
STEERING: (a) size the book as a SINGLE correlated-vol bet (budget rho~1), because crypto vol
spikes are systematic; (b) per-pool kill switch ($10) is the TRUE diversifier - it bounds each
pool's spike LVR at source, the only protection vs the non-diversifiable systematic-vol component;
(c) gap between independent-implied and correlated std (~2x) is the "diversification illusion".
- Artifacts: reports/AMM_LVR_MATHEMATICS.md (adds Section 11); _amm_lvr_corr_verify.py.
- Scheduling: still covered by job_7a2c8a4ea13d (*/10), runs inert (Not logged in); NOT duplicated.

## 2026-08-16 (loop, 3rd firing) - ZK dark pools CONTINUED (2nd continue): implementable plan
Moved the scan to actionable: appended Section 7 to tools/quant/reports/ZK_DARK_POOLS.md.
- 7.1 Booking-route decision matrix: classify orders by size/urgency -> venue (large/illiquid:
  CEX RFQ/OTC; mid-tail: intent/Dutch if depth else RFQ; liquid/small: MEV-Share private
  mempool vs AMM; sensitive atomic: ZK dark pool where depth exists).
- 7.2 Gated MVP probe (2-3 wks, low build): log MEV-leakage baseline on current path (week 1),
  pilot a disjoint 20% of notional through the privacy ladder (weeks 2-3), paired per-order
  all-in cost comparison (fills+fees+gas+impact) with paired t-stat on cost delta.
- 7.3 Pre-committed go/no-go: GO if median all-in cost improvement >= ~5bps/order and no class
  p95 degradation >5bps (p95-worse is a class veto); NO-GO/fallback if MEV-save <3bps all-in.
  Guardrails: pilot orders still pass existing trade_qualifies/risk gates; additive routing only.
- 7.4 Non-goals: no signal-layer change, no in-house ZK/MPC build (consume mature venues).
- 7.5 Done = one-page routing policy + measured cost delta + dated go/no-go per class.
- Tooling: quantum-intelligence still HTTP 503 (6th attempt) -> figures directional, replace
  with desk's own ADV/slippage before GO gate. Artifact: ZK_DARK_POOLS.md Section 7.
- Schedule: identical base prompt still under job_083962909803 (auth-broken cron, no-op); the
  "continue research" increment has no separate cron. Not duplicated.

## 2026-08-16 (/loop, 6th firing) — AMM LVR: the OUT-OF-RANGE trap -> wide bands (all 3 costs align)
Extended the AMM/LVR note to the concentrated-LP out-of-range state (price drifts out of band
[Pa,Pb]: LP goes 100% one asset, earns no fees, capital locked; must re-bridge back at adverse price).
Monte Carlo, 8k x 1yr hourly GBM (sigma=0.30):  in/out occupation and re-bridge count vs half-width h:
   h=0.05: out 76.5% of the year, 49 re-bridges/yr   <- DEAD MONEY trap
   h=0.10: out 58.7%, 39/yr ; h=0.20: 34%, 25/yr ; h=0.30: 20%, 16/yr ; h=0.50: 6.8% out, 6/yr
TOTAL-COST optimal band (sum LVR-per-capital $7 + out-of-range staging + re-bridge cost):
   optimum at h*=0.50 (band [0.67,1.50]); tight h=0.05 costs 0.389/yr = ~11x the wide optimum 0.036/yr.
   All 3 cost components decline monotonically with widening -> WIDER IS BETTER for every LVR motive.
HONEST CAVEAT: the only countervailing force is FEE DENSITY (concentrating capital where trades
happen). The fee-density benefit must clear the 0.04-0.39/yr tight-band cost penalty - a much higher
bar than the simple LVR-only breakeven of $9. STEERING: center at expected price, keep band wide
(target >~85% in-range), widen bands as sigma rises (rho/sigma^2 sensitivity), only accept narrow
bands where fee rate x turnover is extremely high, small size.
- Artifacts: reports/AMM_LVR_MATHEMATICS.md (adds Section 12); _amm_lvr_ooor_verify.py.
- Scheduling: still covered by job_7a2c8a4ea13d (*/10), runs inert (Not logged in); NOT duplicated.

## 2026-08-16 (loop, 3rd continue) - ZK dark pools capstone: skeptic's audit / falsification
Rather than add more breadth (would be padding), appended Section 8 to
tools/quant/reports/ZK_DARK_POOLS.md as the honest capstone, consistent with the desk's
evidence-gated culture.
- 8.1 Falsifiable predictions: P1 material leakage observed on current AMM/mempool path; P2
  net-positive >= ~5bps/order all-in saving; P3 depth is not the binding constraint. Any fails
  => migration not worth doing now.
- 8.2 Steelman against: (1) leakage may be immaterial at a startup fund's small true size
  (the "fatal mempool exposure" is a large-institutional problem - the baseline probe must
  settle it, first); (2) execution is a 2nd-order lever when signal alpha is already thin/
  within-noise; (3) private-mempool/intent/RFQ add builder/solver/CEX counterparty risk
  surfaces; (4) ZK dark pools too thin to take real size without moving the market anyway.
- 8.3 Discipline: run the Week-1 leakage baseline FIRST; if P1 fails, the publishable result
  is "thesis does not apply at this scale; no routing change" - not a failure.
- 8.4 Arc now complete: problem -> architecture -> toolkit -> ladder -> route matrix -> gated
  MVP -> falsifiability. STABILIZE this report; further "continue" should trigger live
  measurement, not more writing.
- Tooling: quantum-intelligence still HTTP 503 (7th attempt). Artifact: ZK_DARK_POOLS.md S8.

## 2026-08-16 (/loop, 7th firing) — RETURN/Sharpe reframe: "how much can we make"
User feedback: the note was cost-centric; they want RETURN, SHARPE. Rebuilt the AMM LP model
around net P&L (fees - LVR - out-of-range staging - re-bridging), annualized with vol -> SHARPE.
Net annual return & Sharpe by config (3bp fee, 300x turnover, hourly GBM MC):
   h=0.05 sig=0.15: -4.8%, SR -8.0  |  sig=0.30: -6.4%, SR -8.7
   h=0.15 sig=0.15: -1.4%, SR -1.8  |  sig=0.30: -3.9%, SR -6.0
   h=0.30 sig=0.15: +0.15%, SR 0.5  |  sig=0.30: -1.8%, SR -2.6
   h=0.50 sig=0.15: +0.42%, SR 2.2  |  sig=0.30: -0.5%, SR -1.1   <- ONLY positive cells
P&L decomposition (sig=0.15): LVR is SMALL (<=0.3%/yr); the real killers at tight bands are
OUT-OF-RANGE STAGING + RE-BRIDGING (2.6%+2.3% at h=0.05 vs 0.01%+0.01% at h=0.5) which dwarf
LVR. Widening bands collapses those AND slightly raises gross fees (more in-range time).
Turnover only amplifies an already-positive book; cannot rescue a volatile/tight one.
PORTFOLIO RULE: deploy LP capital ONLY into low-vol (sigma<=~15%) + wide bands (h>=~0.3, >=85%
in-range). Size by net return x Sharpe.
- Artifacts: NEW reports/AMM_LVR_RETURNS.md (decision-facing returns/Sharpe summary, Tables A/B);
  reports/_amm_lvr_ret_sharpe.py (reusable return/Sharpe model). Consistent with AMM_LVR_MATHEMATICS.md 1-12.
- Scheduling: still covered by job_7a2c8a4ea13d (*/10), inert; NOT duplicated.

## 2026-08-16 (loop, 4th continue) - ZK dark pools: built the P1 MEV-leakage baseline probe (code, not prose)
Stopped adding prose (report arc complete in S8) and, per the report's own recommendation,
turned "continue" into the measurable artifact: a runnable P1 baseline probe.
- New: tools/quant/execution/mev_baseline.py
- What it does: Fill -> fill_vs_fair_bps (signed slippage vs fair/oracle benchmark), sandwich_flag
  (deep-in-block position AND adverse reversal => classic sandwich signature), MevBaseline
  aggregator (mean/median/p95 slippage, mean reversal, sandwich rate), and est_leak_bps = observed
  mean slippage minus a ~12bps non-MEV floor (spread+impact+gas from costs.py CRYPTO model) =>
  isolates the MEV/adverse-selection increment the existing flat-cost model does NOT capture.
- Verdict() implements Section 8.1 prediction P1: leak >= 2bps => "leak present, proceed to P2
  pilot"; leak ~0 => "thesis does not apply at this scale" (valid negative result). No-data guard
  if fills list empty.
- Built-in synthetic self-test (40 fills, 20% attacked) runs clean: n=40, median 4bps, p95 111bps,
  sandwich rate 20%, est leak ~13.3bps => P1 LEAK PRESENT (demo only, NOT market data).
- Purpose: gives the desk the exact measurement contract (which fields to capture per live fill:
  fill price, fair/fair-benchmark, tx position in block, block size, post-fill reversal) so the
  Week-1 baseline is runnable. It is NOT a live mempool watcher and NOT a capital decision; all
  thresholds directional, replace with real fills before go/no-go.
- Tooling: quantum-intelligence still HTTP 503 (8th attempt). No schedule change (base prompt under
  the auth-broken job_083962909803; not duplicated).

## 2026-08-17 (/loop) — XGB multi-horizon close-to-close: the edge is at 1-MONTH, not next-day
Built a multi-horizon XGB framework (H=1 next-day, H=5 1-week, H=21 1-month) on the
20-year 285-name twelve_big panel (2006-2026, 1.43M rows, 70 causal features incl
momentum/vol/RSI/FF/crypto/macro), walk-forward no-look-ahead (quarterly refit), cross-
sectional long-top/short-bottom with **honest overlapping position-book accounting**
(monthly tranches held to maturity, daily MTM, 6bp/side). OOS 2014-2026, vol-targeted.

  Horizon     raw SR / vt SR   ann(vt)   maxDD(vt)
  Next-day H=1  -4.0 / -2.5     -64%      -99%   <- ANTI-signal, do not trade
  1-week  H=5   -0.73 / -0.65   -17%      -68%   <- weak/negative
  1-month H=21  +2.33 / +1.71   +41%      -45%   <- ROBUST EDGE  (K=20: SR~1.96, ann 40%, DD -29%)

KEY FINDING: the XGB close-to-close edge lives at the 1-MONTH horizon. Next-day ranking is
anti-predictive after costs (short-horizon reversal) - which is WHY the earlier bigmove
next-day>=5% and hourly work found no usable signal. The accord's "extend to 1 week/1 month"
is exactly where the signal is.

ROBUSTNESS (validated, no overfit):
  1) Permutation null (200 shuffles/date): actual SR 2.33 vs null -0.12±0.37 => p<0.5%.
  2) No regime flip: 2014-19 SR 2.93 (ann 70%), 2020-26 SR 1.01 (ann 23%).
  3) Beats naive 20d-momentum rank 2.4x (XGB 2.33 vs 0.68 raw) - ML > simple momentum.
  4) Cost-immune: 6bp barely dents SR (1.76->1.71).
  5) K-robust (5/10/20 -> SR 1.9/1.7/2.0); K=20 cuts DD to -29%.
HONEST CAVEAT: 2020-26 half weakens to SR~1.0, DD -37% at K=10; single price source.
Recommend deployable: K=20 monthly-rebalance L/S, 6bp, 13% vol-target, optional VIX gate.
Artifacts: tools/quant/reports/xgb_horizons/ (RESEARCH_REPORT.md, 3 scripts, results jsons,
cached OOS preds horizon_preds.pkl). Next levers: union wider panels (twelvedata/polygon),
blend monthly-equity signal with low-beta streams, add earnings/news features.

## 2026-08-17 (/loop, CORRECTION + upgrade) — 1-month XGB L/S: SR 2.5, ann 44.6%, DD -14.4% (fixes missing-quote bug)
CAUGHT AND FIXED a bookkeeping bug in the hold-H sim just posted: missing
quotes for a held ticker on a given day produced NaN daily P&L (1864 NaN days),
so stats() dropped them and UNDERSTATED return and OVERSTATED drawdown. Treating
missing quote as 0% change + fillna(0) gives the honest profile:

  H=1 next-day  wt SR -3.8 ann -45%  DD -100%   <- anti-signal, do NOT trade
  H=5 1-week    wt SR -1.6 ann -22%  DD -96%    <- negative
  H=21 1-month  wt SR 2.51 ann 44.6% DD -14.4%  <- DEPLOY (K=10, monthly rebal, 13% vol-target, 6bp)
        raw SR 2.35 ann 96%   DD -38.8%

VALIDATED (H=21, no overfit):
  1) Permutation null n=200: actual 2.35 vs null -0.11±0.27 => p<0.5%.
  2) Both halves strong: 2014-19 SR 2.54 (ann 44), 2020-26 SR 2.34 (ann 42) - no regime flip.
  3) Beats naive 20d-momentum rank ~2.5x (XGB 2.35 vs 0.67 raw / 0.94 vt).
  4) Cost-immune: 0->6bp leaves vt SR ~unchanged (2.57->2.51 at K=10).
  5) K-robust: K=5/10/20 -> vt SR 2.28/2.51/2.07, DD ~-14%.
KEY: the XGB close-to-close edge is at the 1-MONTH horizon; next-day/week are
anti-signals after costs (why earlier next-day bigmove/hourly work found none).
ML beats simple momentum by 2.5x (not just rediscovering momentum).
CAVEAT: single price source; SR~2.5 exceptional -> size conservatively, paper
before capital. Artifacts updated in tools/quant/reports/xgb_horizons/
(RESEARCH_REPORT.md corrected, book_results/validate jsons, equity/subperiod pngs).
Next levers: union twelvedata+polygon panels, blend with low-beta streams,
VIX gate for the -14% tail, live paper forward.

## 2026-08-16 (loop, 5th continue) - ZK dark pools: made the P1 probe load-bearing (opt-in cost add-on)
Wired the measured MEV-leak estimate into the desk's PRODUCTION crypto cost model so the
baseline is load-bearing, not a standalone demo - while defaulting OFF so no existing
backtest result changes (by-design: cost model is production; we don't silently alter it).
- tools/wt/costs.py: new CRYPTO_MEV_LEAK_BPS (bps, default 0.0 => OFF, read from env/.env.local).
  round_trip_cost_frac() adds leak/1e4 for market=="CRYPTO". Goal: flat CRYPTO taker modeled
  commission+spread+impact but NOT the incremental sandwich/front-run/adverse-selection the
  ZK-thesis targets; this closes that gap once P1 is measured on real fills.
- Verified: default off => CRYPTO RT unchanged 41.49bps; CRYPTO_MEV_LEAK_BPS=13 => 54.49bps
  (+13bps one-way leak). Note the realistic CRYPTO RT is ~41bps (2x10 taker + 2x~10 spread +
  impact), already above the flat 20bp COST_RT - but still had zero explicit MEV increment.
- Workflow: run mev_baseline.py on live fills -> read est_leak_bps -> set CRYPTO_MEV_LEAK_BPS
  to that value -> backtests now reflect the real AMM-path net edge. Default stays off until then.
- Artifacts: mev_baseline.py (P1 probe) + costs.py CRYPTO_MEV_LEAK_BPS opt-in leak add-on.
- Tooling: quantum-intelligence still HTTP 503 (9th attempt). No schedule change (base prompt
  under auth-broken job_083962909803; not duplicated). Research + tooling chain now complete;
  further "continue" should be LIVE measurement (collect fills), not more code/writing.

## 2026-08-17 (/loop) — AUTHORITATIVE 20-YEAR TEST: 1-month XGB L/S 20y Sharpe ~1.9 (confirmed reliable, optimized, committed)
User asked for the 20-year testing Sharpe (model updated on time, quarterly retrain)
and to verify/double-check, then optimize+commit.

EXTENDED OOS TO FULL WINDOW: walk-forward now OOS 2008-09-02 -> 2026-08-12 (~18y, 4516
trading days, 1.29M OOS rows, 72 quarterly refits on trailing 2y window). Honest hold-H book:

  Horizon       raw SR   vt SR   ann(vt)  maxDD(vt)
  Next-day H=1   -3.6     -4.0    -48%    -100%   <- anti-signal (confirmed)
  1-week   H=5   -1.4     -1.4    -19%     -98%   <- negative
  1-month H=21    1.63     1.90    32.0%  -30.1%  <- DEPLOYABLE

=> **20-year testing Sharpe = 1.90 vt / 1.63 raw, positive in both halves (08-15 1.66, 16-26 2.16).**

RELIABILITY AUDIT (doubled-checked, all pass):
  1) Permutation null n=120 (20y): actual 1.63 vs null -0.12+-0.22 => p<1%.
  2) Breadth: HHI 0.017 (~59 effective names), 74% months positive, EVERY year '08-'26 positive.
  3) Outlier-month robust: drop best/worst month -> SR 2.33/2.42 (2014+).
  4) SURVIVORSHIP de-biased: survivor-in-2007 universe (231 names) -> vt SR 1.92 ann 32.9% DD -23.9%
     (SR holds, DD improves). The 2014+ recent-window 2.5->2.1 gap was window-specific, not systemic.
  5) Beats naive 20d-momentum rank ~2.4x (XGB 1.9-2.5 vs 0.94 vt).
  6) Cost-immune: 0->6bp leaves vt SR near-flat (1.99->1.92 at K10).
OPTIMIZED CONFIG (20y, survivor-in): K=10 monthly rebalance, 6bp, 13% vol-target
  -> vt SR 1.92, ann 32.9%, maxDD -23.9%, Calmar 1.38  (K=20: SR 1.55/ann 25%/DD -18%/Calmar 1.41).
HONEST CAVEATS: residual survivorship (long-side-biased; point-in-time CRSP would confirm),
single price source, 2y train window for 20y run vs 3y for 2014+ run, paper-trade before capital.
ARTIFACTS COMMITTED: tools/quant/reports/xgb_horizons/RESEARCH_REPORT.md (authoritative),
  bigmove/xgb_multi_horizon.py + xgb_horizon_portfolio.py + xgb_horizon_validate.py
  + xgb_horizons_run.py (one-command reproducible), data/horizon_preds_20y.pkl (1.29M OOS preds),
  20y equity/subperiod pngs, results jsons.

## 2026-08-17 (/loop) — Drawdown filter for 1-month XGB L/S (20y, causal overlays)
User: "filter the drawdown without affecting the return." Swept ~30 causal (lagged)
risk overlays on the 20y H=21 K10 vt book. HONEST finding: DD/return tradeoff is real
(halving DD costs ~13pp ann). Two validated answers:

1) RETURN-PRESERVING (keep ~30%): VIXz<2 OFF & |mt20|<.01->0.5 => SR 1.96, ann 30.1%,
   DD -21.8% (trim 2pp), Calmar 1.38, Sharpe UP. Best "don't touch return" option.
2) RISK-REBALANCED (drawdown-killer) BREADTH GATE: de-risk to 0.5 when strategy's own
   breadth <0.35 or >0.80 (extreme one-sided momentum => whipsaw regime). RESULT:
   SR 1.97 (up from 1.92), ann ~20%, **maxDD HALVED -23.9% -> -11.8%**, Calmar 1.69
   (up), both 20y halves positive (1.94/1.99), no regime flip. Specifically blunts
   worst 2011-2013 grind (-23.9%->-11.8%); all later DDs <= ~-12%. Best SR+Calmar seen.
Alternative breadth<.4|>.75->.3: DD -6.3%, Calmar 2.13 but ann 13%.

VERDICT: can't have both 33% ret and 10% DD from OHLCV momentum (2011-13 grinds are
intrinsic). Choose: (a) breadth gate = SR~2.0, ann~20%, DD~-11%, Calmar~2.0, or
(b) VIXz/mt20 gate = SR~1.96, ann~30%, DD~-22% (return-preserving). Both additive, causal.

NEW ARTIFACT: tools/quant/bigmove/xgb_horizon_ddfilter.py (additive default-off overlay
module: breadth+VIX+choppy gates; get_overlays() returns causal exposure factors);
reports/xgb_horizons/multi_horizon_ddfilter.png (equity+DD baseline vs breadth gate);
h21_breadth_gate_daily.csv; RESEARCH_REPORT.md addendum. Commit follows.

## 2026-08-17 (/loop) — features5: +50 free features -> IC 2.45x, DD -16.6%, return preserved (overlays now dominated)
User: "add more free data features. filter big drawdown without affecting return."
BUILT features5.py (+50 causal features over features3): 52-week-high distance,
realized skew/kurt/downside-vol, cross-sectional momentum percentile ranks,
EARNINGS-date proximity (PEAD from earnings_panel), baa-aaa default spread,
WTI/natgas/gold/silver/copper momentum, DXY+EUR/GBP/JPY/CAD/CNY FX momentum,
CH/GB/JP/EZ/AU/CA 10y changes, US30Y/3M levels + 30Y-2Y slope, VIX 21d chg, vol trend.

RESULT (20y OOS, H21, K10 survivor-in, 6bp, 13% vt):
  70-feat : IC 0.0132 | vt SR 1.92 | ann 32.9% | DD -23.9% | Calmar 1.38
  120-feat: IC 0.0324 | vt SR 1.92 | ann 32.4% | DD -16.6% | Calmar 1.95
  => IC 2.45x; **DD cut -23.9%->-16.6% with return & Sharpe preserved, Calmar 1.38->1.95**.
  Both halves positive (2.13/1.77), 67% months positive.

DRAWDOWN-FILTER VERDICT on improved model: all causal DD overlays (breadth gate,
VIXz gate, |mt20| choppy gate) are now DOMINATED - either no DD cut (VIXz/|mt20|)
or DD cut at disproportionate return cost (breadth: DD -10~-11% but ann ~19%,
Calmar 1.72 < 1.95 no-overlay). The 120-feature model's intrinsic drawdown beats
every overlay tested. DEPLOYABLE = 120-feature model WITHOUT overlay.

Artifacts: features5.py; xgb_multi_horizon.build_frame now uses features5 (120feat)
by default; data/horizon_preds_20y_f5.pkl (new champion preds); RESEARCH_REPORT.md
addendum. Commit follows.

## 2026-08-17 (/loop) — SPY-hedge test: bottom-K short leg is ALPHA (keep full L/S)
User: "how about we only short SPY as the short positions? backtest again."
Backtested long-top-K ML picks / short SPY (equal notional, beta 0.5/0.8/1.0,
K10/20, 6bp, 13% vt, 20y OOS, features5):

  Full L/S top10/bottom10 (baseline): vt SR 1.92 ann 32.4% DD -16.6% Calmar 1.95
  long10 / short SPY 1.0x: SR 1.54 ann 24.5% DD -19.1% Calmar 1.28
  long10 / short SPY 0.8x: SR 1.60 ann 25.8% DD -18.3% Calmar 1.41
  long10 / short SPY 0.5x: SR 1.60 ann 25.7% DD -18.5% Calmar 1.39
  long20 / short SPY 0.5-1.0x: SR 1.56-1.63, DD -18~-23%
  long-only (no hedge): SR 1.50 ann 23.5% DD -17.7% Calmar 1.33

VERDICT: keep the full long/short. The bottom-K short leg is an ALPHA source
(~0.3-0.4 SR, ~7pp ann) not a hedge: every SPY-hedge variant is worse on
SR/ann/Calmar, and SPY hedge does NOT cut drawdown (shorting 10 diversified
losers hedges better than SPY: diversification + loser reversal in stress).
Beta 0.5-1.0x barely matters; long-only worst. Added long_only param to
build_position_book (reusable). Report addendum written; commit follows.

## 2026-08-17 (/loop) — Honest cost model (24bp/mo full cycle) + short borrow fee (IBKR) added
User confirmed 6bp one-side cost and asked about the short borrow fee (IBKR call rate).
1) COST MODEL CORRECTION: old model charged 2*cost=12bp/mo (open-only, one-way both
   legs). Honest full cycle at monthly rebalance = close old tranche (L6+S6) + open new
   (L6+S6) = 4*cost = 24bp/mo (~2.9%/yr). Champion H21 K10 f5: SR 1.92/ann 32.4% ->
   SR 1.85/ann 31.1%, DD -16.7%, Calmar 1.86.
2) BORROW FEE (borrow_rate param, daily on short leg): shorts are bottom-10 of 285
   LARGE caps -> all easy-to-borrow; IBKR ETB ~0.25-1%/yr. Sensitivity at honest cost:
   0.25%: SR 1.84 ann 30.9% | 1%: SR 1.82 ann 30.5% | 2%: SR 1.79 ann 29.9% |
   5% (HTB, shouldn't occur): SR 1.71 ann 28.2%.
   VERDICT: robust. Deployable = SR ~1.84, ann ~30.9%, DD ~-16.7%, Calmar ~1.85.
Results json regenerated with honest cost + borrow sens. Commit follows.

## 2026-08-17 (/loop) — Portfolio optimization: pred-scaled weights -> SR 1.94 (Sharpe up), inverse-vol negative
User: "apply portfolio optimization techniques to improve the Sharpe ratio" /
"we want to optimize to make the Sharpe ratio larger".
Tested within-leg weighting on champion (f5 H21 K10 survivor-in, honest costs
24bp/mo, ETB borrow 0.25%, 20y OOS):
  equal weight      : vt SR 1.84 ann 30.9% DD -16.7% Calmar 1.85
  PRED-SCALED (new) : vt SR 1.94 ann 37.3% DD -15.8% Calmar 2.35  <- WINNER
  inverse-vol (60d) : vt SR 1.69 ann 28.0% DD -18.5% Calmar 1.51  <- negative
  pred x invvol     : vt SR 1.87 ann 35.8% DD -17.1% Calmar 2.10
Weight = (pred - xs median) within each leg, normalized per leg; concentrates
in strongest signals -> Sharpe +0.1, return +6.4pp, DD slightly lower.
Inverse-vol HURTS monthly momentum (consistent with prior findings) - don't use.
CODE: build_position_book(..., weight_scheme='pred') now default.
ALSO (user): "update the model monthly before make predictions" -> walk-forward
REL launched with REFIT=21 (monthly retrain on 2y window) + features6 (141
feats, 292-name union pool incl ARM/COIN/DOCU/PLTR/SHOP/SQ/ZM) -> data/
horizon_preds_20y_f6.pkl. Result pending (~40min). Commit of weight-scheme now.

## 2026-08-17 (/loop) — Short-borrow realism: AVAILABILITY is the binding constraint, not fees
User: "the best stocks to short usually can't be sold short. we need to model this effect."
Added to build_position_book: short_unavail_frac (deepest losers unavailable ->
replace with next-shortable names) + borrow_graded (per-short fee scales with
short rank, deepest 10x base). Test on pred-scaled champion (f5 H21 K10, honest
costs, 20y):
  flat 0.25%: SR 1.94 ann 37.3% DD -15.8% Calmar 2.35
  graded 0.25% base (deepest 2.5%): SR 1.91 ann 36.7%  <- fees ~free
  graded 1% base (deepest 10%): SR 1.81 ann 34.3%
  30% best-shorts UNAVAILABLE: SR 1.77 ann 30.6% DD -18.3% Calmar 1.67  <- big
  30% unavail + graded: SR 1.74 ann 30.0%
  50% unavail + graded: SR 1.71 ann 29.4%
  30% unavail + graded 1%: SR 1.62 ann 27.7%
FINDING: borrow FEES ~irrelevant (even 10x graded costs 0.1 SR); AVAILABILITY
is the binding constraint: losing 30% of deepest shorts costs ~0.17 SR and
~6.7pp ann. HONEST deployable with borrow realism: SR ~1.7-1.8, ann ~30%,
DD ~-18%, Calmar ~1.6-1.7 (headline ~1.9-2.0 conditional on short availability).
Code committed with params short_unavail_frac + borrow_graded.

## 2026-08-17 (/loop) — CRITICAL LEAK FOUND & FIXED: monthly XGB L/S not deployable (honest IC 0.031, net SR -0.2)
FOUND a label-overlap leak in the walk-forward: training rows used dates < block_start,
but a row at t has target ret_21[t] = close[t+21]/close[t], so the last 21 days of the
train window have labels extending INTO the prediction block. Evidence: OOS IC by
position within 63d block = 0.32 (days 0-9), 0.00 (10-20), -0.06 (21-41), 0.00 (42-62).
Monthly refits (block=21d) made the leak cover 95% of the block -> fake IC 0.168, fake
SR ~7. THE L/S BOOK REBALANCES AT BLOCK STARTS = THE LEAKED ROWS -> the entire SR
1.85-1.94 champion was a leak artifact.

FIX committed in xgb_multi_horizon.walkforward_predict: train only on dates <
block_start - max(H) (no training label overlaps the prediction block).

HONEST leak-free numbers (141-feat stack, quarterly, 2y win, 20y OOS):
  H=1 IC 0.0377 | H=5 IC 0.0209 | H=21 IC 0.0307 (leak gone: block-day ICs ~0.01-0.03)
  H21 book K10 survivor-in, 24bp/mo honest cost + ETB borrow: vt SR -0.25 (equal)
  / -0.22 (pred), ann -4.6%, DD -66%.
VERDICT: the monthly cross-sectional edge is REAL but SMALL (IC 0.031 ~ 0.22%/mo
spread) and BELOW the honest 24bp/mo full-cycle cost -> net book slightly NEGATIVE.
NOT deployable. All prior H=21 headline numbers VOID (features5/6 IC gains, DD
filters, pred-scaled weights, borrow-realism, K=15 optimum).
NOTE: H=1 (bigmove) work unaffected (1-day overlap negligible).
Artifacts: data/horizon_preds_20y_f5fix.pkl (honest cache), report addendums.

## 2026-08-17 (/loop) — GKX replication with FREE data: does NOT reproduce (XGB SR +0.21 gross, ~0 net)
User: "replicate Gu's result with best efforts. Get free data for it."
BUILT: GKX-style monthly pipeline on free data — 292 large caps (local panel),
33 characteristics (24 technicals + 7 Finnhub-free fundamentals: size/ROE/rev
growth/asset turnover/PE/EPS growth/div yield + earnings + macro interactions),
purged walk-forward (train <= m-1, no label overlap), yearly refit 7y window,
OOS 2009-2026, decile L/S EW+VW, gross+net (24bp/mo full cycle).
RESULTS: Ridge gross SR -0.57 (net -0.96) | XGB gross +0.21 (net ~-0.04) |
MLP -0.26 (net -0.68). vs GKX 2.45 EW / 1.35 VW GROSS.
CONCLUSION: Gu's result does NOT replicate with free data. Gap is structural:
(1) universe 292 large caps vs 30k stocks (their EW 2.45 lives in the micro-cap
tail - they say so; VW is 1.35); (2) 33 chars vs 94+ point-in-time CRSP/Compustat
fundamentals (free tier: no PB/leverage, fundamentals are current snapshots, no
history); (3) costs (24bp/mo honest vs their gross). The data IS the edge; free
data on large caps yields ~0 net Sharpe. Consistent with our leak-free IC ~0.02.
Artifacts: tools/quant/bigmove/gkx_monthly.py + gkx_backtest.py + data/
gkx_monthly_panel.parquet + finnhub_metrics.json + reports/xgb_horizons/
GKX_REPLICATION.md. Commit follows.

## 2026-08-17 (/loop) — GKX v2: +SEC EDGAR free fundamentals + 657-name union -> XGB EW net SR +0.18
User: "get the free data to replicate it." Found the two missing free data
levers: (1) SEC EDGAR companyfacts API (FREE, no key, all US public cos):
parsed XBRL -> point-in-time quarterly fundamentals (book equity, assets, NI,
revenue, op income, gross profit, CFO, shares) dated by FILING date ->
GKX-style chars: bm, size, roe, gross/op profitability, accruals, investment.
(2) Union universe 292->657 names (twelve_big+twelvedata+twelve_liq+polygon+
polygon_v2; ~290 full-history, 657 in 2024-26).
RESULTS (purged monthly walk-forward, decile L/S, OOS 2009-26):
  XGB EW: gross SR +0.21->+0.44, net -0.04->+0.18 (now positive)
  Ridge EW: -0.57->+0.11 | MLP: -0.26->-0.19
Still ~1/5 of GKX 2.45 (their universe 30k incl micro-caps, gross, 94 chars).
EDGAR fetch for 626 CIKs completing in background (387/626 now) -> rerun when
done. Artifacts: union_panel.py, edgar_fundamentals.py, edgar_to_panel.py,
data/edgar_facts/*, data/edgar_chars.parquet, gkx_monthly_panel.parquet (v2),
GKX_REPLICATION.md update.

## 2026-08-17 (/loop) — GKX FINAL (free data): XGB EW net SR +0.21 (gross +0.43) ~ 1/6 of Gu's 2.45
EDGAR fetch completed (600 companies). Final replication on 657-name union,
39 chars (point-in-time bm/size/roe/gross-prof/op-prof/accruals/investment +
technicals + Finnhub + earnings + macro), purged monthly walk-forward, decile
L/S OOS 2009-26:
  XGB EW: gross SR 0.43 (ann 5.0%), net +0.21 (ann 2.1%, win 54%)  <- BEST
  MLP EW: gross 0.30, net -0.08 | Ridge EW: gross 0.15, net -0.10
  VW negative for all (large-cap VW no edge; GKX VW 1.35 << EW 2.45 too)
VERDICT: free-data replication lands at net SR ~+0.21, ~1/6 of GKX 2.45 gross
EW. Gap: universe (657 vs 30k, no micro-caps = where their EW alpha lives),
chars (39 vs 94), our net vs their gross, their EW is micro-cap/illiquid
weighted (VW=1.35). Free data cannot close this; the CRSP universe is the
edge. Commit follows.

## 2026-08-17 (/loop) — More data (EDGAR chars x12, TwelveData +400 names) -> investable-filter kills the edge
User: "try to get more data." Got: (1) 5 more EDGAR characteristics (payout,
rd_a, capex_a, leverage, cur_ratio — 12 fundamentals total), (2) 400 more
names' daily prices from TwelveData free tier (8 req/min background, 124/400
done). Universe 657->713+.
SANITY: expanded panel had garbage (DD -1.7M from penny/split artifacts) ->
added investable filter (median price >= $2, monthly ret in [-0.95, 2.5]).
HONEST v5 (investable): XGB EW gross SR +0.06, net -0.18 | MLP 0.04/-0.25 |
Ridge 0.14/-0.16. The v3 +0.44 gross included sub-$2 penny/extreme-tail names
(not investable at size) - same micro-cap caveat as GKX's own 2.45. Verdict:
investable free-data GKX-style L/S is ~zero net of costs on large/mid caps.
TwelveData fetch continues in background; rerun when done.

## 2026-08-18 (/loop) — GKX v6: 1032-name investable universe -> Ridge EW net SR +0.42 (best free-data result)
TwelveData batch 1 completed (375 names) -> union 657->1032, panel 874
investable tickers. Purged walk-forward decile L/S OOS 2009-26:
  Ridge EW: gross 0.64, NET +0.42 (ann 4.6%)  <- best
  XGB EW: gross 0.51, net +0.33 | XGB VW: gross 0.29, net +0.15
  MLP EW: 0.05 (NN needs the full 30k universe to win)
vs v5 (657 names): Ridge -0.16->+0.42, XGB -0.18->+0.33. CONFIRMED: more
investable names = more edge. ~1/6 of GKX 2.45 gross EW, but now NET positive
on an investable >=$2 universe. Batch 2 (~400 more names) fetching in
background; rerun after. Commit follows.

## 2026-08-18 (/loop) — GKX v7: 1092 names -> Ridge EW net SR +0.48 (converged; quality queue exhausted)
Batch 2 TwelveData (~60 usable of 400, rest junk/errors) -> union 1092 names,
901 investable tickers. Purged decile L/S OOS 2009-26:
  Ridge EW: gross 0.69, NET +0.48 (ann 5.9% net)  <- best free-data result
  XGB EW: gross 0.23, net +0.06 (degraded - greedy trees overfit noisy names)
  MLP: -0.01
Ridge robust to junk names; XGB not. Quality queue nearly exhausted (batch 2
~40% error, sub-$2/<200 rows). CONVERGED: Ridge EW net SR ~+0.5, ann ~6% net,
~1000-name investable universe ~ 1/5 of GKX 2.45 gross EW. Remaining levers:
more EDGAR chars, ensembling, paid universe. Commit follows.

## 2026-08-18 (/loop) — GKX v8: +4 EDGAR chars (48 total) -> Ridge EW net SR +0.54
Added inventory/assets, receivables/assets, cash/assets, PPE growth from the
same EDGAR files (16 fundamentals, 48 chars total). Purged decile L/S OOS
2009-26: Ridge EW gross 0.75 / NET +0.54 (ann 6.7% net) - new best; XGB 0.18
gross / +0.01 net (still overfits noisy names). Trajectory: Ridge net SR
0.42 (v6) -> 0.48 (v7) -> 0.54 (v8). Every free-data lever (names, chars)
raises the regularized linear model. VW negative. Commit follows.

## 2026-08-18 (/loop) — GKX v9: 57 chars, Ridge net SR +0.54 (free-data ceiling reached)
Added 4 more EDGAR fundamentals (depr_a, ret_equity, pay_a, int_cov) + 2 price
chars (ret_36 long-term reversal, dollar_vol) -> 57 characteristics. Purged
decile L/S OOS 2009-26: Ridge EW gross 0.75/net +0.54 (unchanged); XGB
0.25/0.09 (up); VW improved (Ridge net -0.05). DIMINISHING RETURNS confirmed:
9 extra chars didn't move Ridge. Free-data ceiling ~net SR 0.54 for Ridge EW
decile L/S on the ~1100-name investable universe. Next: ensembling (marginal),
or paid universe for the real jump. Commit follows.

## 2026-08-18 (/loop) — GKX scale-up attempt: universe-margin FRAGILITY (converged ~0.3-0.5)
Attempted to scale up via remaining free sources: TwelveData batch3 (~65 names,
mostly junk), Stooq anti-bot blocked, yfinance rate-limited. Findings:
(1) junk names (100-500 rows) destabilize: Ridge net 0.54->0.20, XGB 0.09->0.48
(model ranking flipped = noise overfit).
(2) quality filter (>=1000 rows, 913 tickers): Ridge 0.23, XGB 0.00 - vs v9's
0.54 on a nearly identical universe (901 tickers). RESULT IS FRAGILE to
marginal universe changes.
CONVERGED ESTIMATE: Ridge EW net SR ~0.3-0.5 (0.23-0.54 across near-identical
configs), ann ~3-7% net, ~900-1100 investable names, 57 point-in-time chars.
Free sources exhausted (EDGAR complete, TwelveData quota spent, Stooq/yfinance
blocked); marginal names add noise not signal. Gap to GKX 2.45 = paid CRSP
universe. SCALE-UP VERDICT: stop expanding free universe; ~900 investable
names is the free-data ceiling. Commit follows.

## 2026-08-18 (/loop) — free-data exploration EXHAUSTED: converged Ridge net SR ~0.2-0.5
Tested every remaining free lever: (1) Finnhub industry dummies (39 industries)
+ macro interactions (credit/DXY) -> Ridge 0.23->0.15 (negative); (2) Finnhub
analyst recs fetch rate-limited (killed after 40min); (3) TwelveData queue has
0 EDGAR-known names left (quality pool exhausted); (4) universe-margin test:
v9 features on cleaned universe = 0.23 vs v9's 0.54 on 901-ticker universe.
FINAL: Ridge EW decile L/S net SR ~0.2-0.5 (~0.3 point), ann ~3-7% net, 57
point-in-time chars, ~900-1100 investable names. All free levers tested and
neutral-to-negative at the margin. Free-data ceiling reached. GKX 2.45 needs
the paid universe. Commit follows.

## 2026-08-19 (/loop) — Buffett $1M / 50% "small-cap strategy": data reality-check
Premise: Buffett's stated playbook for ~$1M is micro-cap deep value / Graham
net-net (烟蒂股) — 地毯式 research on sub-$2B neglected names, cash-specials,
extreme concentration, high turnover, margin-of-safety. Tested whether the
repo's free data can support it. DELIVERABLE: buffett_smallcap_screener.py
(built on the point-in-time EDGAR panel; computes NCAV = cur_assets -
(assets - book_equity), true mcap = shares * price, then net-net/cash/PE<5
flags + forward 1/3/6/12m returns from local prices; no lookahead).
FINDING 1 — UNIVERSE CANNOT SUPPORT THE PLAYBOOK: of ~532 EDGAR-priced names
(2024), only 59 are sub-$2B, 20 sub-$500M, 9 sub-$100M. Median mktcap ~$24B.
This is a LARGE/MID-cap universe, the opposite of Buffett's micro-cap "无人区".
Coverage is too thin to ever diversify a micro-cap basket: 0 net-nets and 0
micro-caps in the latest month; only 754 micro observations across all history.
FINDING 2 — NO NET-NET EDGE IN WHAT DOES EXIST: net-net n=37 -> 1m/3m/6m/12m
+0.93/+2.97/-1.64/+16.25% vs micro base +0.99/+3.53/+8.21/+101.6%. Net-nets
LOST at 6m/12m. cash-special n=129 slightly better at 3m/6m (+5.2/+10.5 vs
+3.5/+8.2) but 12m collapses. deep-value (PE<5) n=275 best at 12m (+152%) but
it's the same large-cap value factor already harvested elsewhere.
VERDICT: this premise is NOT reproducible on the ~900-name free investable
universe — there is no reliable micro-cap edge to be had because there are
almost no micro-caps. Buffett's alpha came from a book of thousands of tiny
names (Moody's 20,000 pages) + a real micro-cap price/float source; neither
exists in free data (Stooq blocked, yfinance rate-limited, TwelveData quota
spent). NEXT (candidate iterations): (a) screen EDGAR's full 16,358-name
us_stock_list for names with cur_assets > mktcap using only fundamentals (list
exists but needs price feed for mktcap); (b) or treat this as evidence to stop
pursuing Buffett micro-cap style on free data and keep the ~900-name large-cap
value/turnover edge already converged (net SR ~0.3-0.5). Reports:
buffett_smallcap_screen.json + tools/quant/bigmove/buffett_smallcap_screener.py

## 2026-08-19 (/loop iter2) — Buffett deep-value: full-universe cross-section ALSO dead
Extended iter1: does Graham margin-of-safety predict ANYTHING in the repo's
actual TRADABLE (large/mid) universe, not just the (absent) micro-caps? Ran
point-in-time decile/quintile cross-section on ncav_ratio, book-to-market,
and P/E at 12m horizon. QUINTILE SPREADS (Q_deep - Q_rich): ncav_ratio -1.7pp,
bm +0.8pp, pe_est -2.2pp. net-nets (ncav>mktcap, n=80) 12m +12.3% vs +16.5%
base = UNDERPERFORM. CONCLUSION: the value/net-net edge is not just missing
in micro-caps (too thin, iter1) — it is absent cross-sectionally in the whole
tradable universe. Double negative. This repo's existing ~900-name large-cap
momentum/PEAD factor edge (already net SR ~0.3-0.5) is the only real free-data
edge; Buffett's "cheap cigar butt" alpha does not materialize on this data
(no micro-cap breadth + value factor flat). STOP pursuing Buffett deep-value
on free data; keep momentum/PEAD. Mechanisms (union of Pawn: thin micro-cap
tradeability, 20k-pages research edge not reproducible from fundamentals
alone, ii) + value factor crowded out post-2008.

## 2026-08-22 (/loop) — equity research report pipeline integrated + 5 reports
Surveyed open-source agent-debate→equity-research projects (ai-hedge-fund v1/v2,
AlphaAnalyst, StockSense-AI, FinAgent, FinRpt, QuantAgent, FinRobot; + FINSABER /
debate-or-vote guardrail papers). Verdict: none production-grade for wholesale
integration; the valuable architecture ideas were adapted into
`tools/wt/agent/research_report.py` (stdlib-only, cited in RESEARCH_NOTES.md):
anti-sycophancy data ordering, bull/bear + mandatory rebuttal round, rule-based
evidence grading, deterministic Python valuation ("LLM writes no numbers"),
judge with convergence detection + bull/base/bear 12-mo PTs. Wired into
`agent_cli.py --report/--watchlist/--force`; `llm_chat.py` gained
`WT_LLM_TIMEOUT` + `disable_thinking` (reasoning models otherwise burn the
budget on hidden CoT and return no text). Screening: 12-mo Sharpe rank on the
twelve_big US panel -> top-5 diverse names. Reports in
`results/equity_research/*.md` (+.json): MU BUY(0.72, base PT 1500), INTC
HOLD(0.35, 88), VLO HOLD(0.55, 355), DELL HOLD(0.55, 760), LLY HOLD(0.55, 1300).
All with grounded claims (6/6), rebuttals, evidence grading, valuations.

## 2026-08-22 (/loop iter2) — coverage extended to 10 names + INDEX.md
Fixed two module gaps: (1) valuation now falls back to trailing-EPS P/E band
when the catalyst calendar has no forward consensus (LLY/VLO/MPC/AMAT/BK/FTNT
get mechanical anchors; INTC honestly abstains — negative earnings, no P/E);
(2) judge told to use the data's catalyst date when present. Added
`tools/wt/agent/build_index.py` -> `results/equity_research/INDEX.md` ranking
coverage by judge base-case PT implied return. 10 names covered, all
reports errors=0. Top by expected return: DELL +72% (OVERWEIGHT, forward-EPS
anchor), PANW +10%, MU +8.6%; INTC -2.3% bottom. Note: MU rating varied
BUY(0.72)->HOLD(0.55) across runs — single-run LLM ratings are directional,
not precise; the evidence-graded debate is the durable output.

## 2026-08-22 (/loop iter3) — 13 names covered; evidence grader upgraded to field level
- Idempotency verified: same-day reports skip without --force (loop-safe).
- Coverage +3 (STLD, WBD, CAT) -> 13 names, all errors=0. Ranking stable:
  DELL +72% OVERWEIGHT, PANW +10%, MU +8.6% top; WBD -1.9%, INTC -2.3% bottom.
- Adversarial spot-check of the top-rated report (DELL): 11/11 evidence
  citations resolve to real data; key numbers match the raw gather exactly
  (ROE 130.7, P/E 38.1, D/E 13.29, 45 insider sells, EPS est 4.99; judge's
  base PT 760.46 == 4.99*4*38.1). The checker itself had one false
  negative (list-of-dicts sections like earnings history) -> grader upgraded
  to field-level checks incl. list items. Verdict: pipeline output is
  grounded, not fabricated.

## 2026-08-22 (/loop iter4) — coverage complete: 17 names; INDEX gains top-picks
- Added NUE, JNJ, PSX, HPE -> 17 names covered (all of the top-19 by 12-mo
  Sharpe except CNC/FDX), all reports errors=0.
- INDEX.md now leads with a "Top picks" block: names with positive
  expected return AND a forward-EPS valuation anchor -> DELL +72%
  (OVERWEIGHT), PANW +10.4%, MU +8.6%, HPE +8.5% (all HOLD/OW, bear-case
  PTs shown). Caveat block restates run-variance honesty.
- Coverage saturated for this screen; future fires are pure monitoring.
  Candidate extension (not done): richer forward consensus for names
  without catalyst eps_est (e.g. analyst_target / target-price sources).

## 2026-08-22 (/loop iter5) — forward-anchor gap attacked: 90-day catalyst window
- The ~0% cluster was caused by missing forward-consensus EPS (Finnhub
  price-target is 403 on free tier; analyst_target is None everywhere).
- Fix: research_report._gather now widens the catalyst window 30d -> 90d.
  Gains: AMAT (eps_est 3.75, 2026-11-12) and FDX (4.05, 2026-09-16) now
  have real forward anchors; the other 13 names genuinely have no free
  consensus feed -> abstention stands (documented limitation).
- AMAT's expected return re-estimated 0% -> +39.6% (HOLD, base PT 687.14)
  once anchored on forward EPS — demonstrates the anchor's effect.
- FDX report added (18 names total; full top-19 minus CNC, which has no
  earnings estimate in the free calendar).
- Top picks now: DELL +72%, AMAT +39.6%, PANW +10.4%, MU +8.6%, HPE +8.5%.

## 2026-08-22 (/loop iter6) — coverage complete (19/19 top Sharpe names); JSON repair
- CNC report completed (the last top-19 name) -> 19 names, all errors=0.
- Root-caused the recurring bear_rebuttal truncation: deepseek-flash
  intermittently stops mid-JSON list. The 4000-token retry with a brevity
  hint made it WORSE (traced: attempt1 parses, retry truncates). Fix:
  `_repair_truncated_json` — deterministic closer-appending repair (zero
  LLM cost) before a plain 4000-token retry. Unit-tested; CNC now clean.
- LOOP PLATEAU: the user's original task (integrate valuable projects,
  write reports on the most promising US names) is complete: 19 reports,
  index, integration, docs, verification. Recommend CronDelete c90ba8cc.

## 2026-08-22 (/loop iter7) — TOP_PICKS.md synthesis; plateau confirmed
- New `tools/wt/agent/build_top_picks.py` -> `results/equity_research/TOP_PICKS.md`:
  actionable synthesis (rating/PT/expected return, judge rationale, catalysts,
  risks per name) assembled deterministically from the report JSONs — no
  extra LLM cost. 6 picks: DELL +72% (OW), AMAT +39.6%, PANW +10.4%,
  MU +8.6%, HPE +8.5%, CNC +4.6%.
- `--doctor` health check passes (anthropic provider, 15 tools).
- LOOP IS DONE. The task (integrate valuable agent-debate projects; write
  reports on the most promising US names) is fully delivered: 19 reports +
  INDEX + TOP_PICKS + integration + verification + docs. Recommend
  CronDelete c90ba8cc; fires are no-ops until then.

## 2026-08-23 (/loop iter8, new prompt: top-20) — coverage completed to exactly 20
- User's new loop prompt: top-20 equities. ROST (the 20th by 12-mo Sharpe)
  report added -> 20/20 names covered, ROST errors=0 (HOLD 0.55, base PT 236
  vs 239 = -1.2%, not a pick).
- The other 19 were skipped by the per-day guard: filenames use UTC dates
  (still 2026-08-22 at run time; local is UTC+8), so "daily refresh" fires
  at UTC midnight (08:00 CST), not local midnight. Behavior is fine; noted.
- INDEX.md + TOP_PICKS.md rebuilt: 20 names, 6 picks unchanged (DELL +72%,
  AMAT +39.6%, PANW +10.4%, MU +8.6%, HPE +8.5%, CNC +4.6%).
- New loop job 96347070 replaces c90ba8cc (old prompt superseded).

## 2026-08-23 (/loop iter9) — first automatic daily refresh (worked as designed)
- First fire after UTC midnight regenerated all 20 reports with fresh data
  (20/20 done, 19 errors=0; HPE bear_rebuttal truncated again — residual
  mid-object truncation the closer-repair can't fix; judge still produced
  BUY 0.65 base PT 62).
- build_index.py / build_top_picks.py now dedup to the newest date per
  symbol (they were double-counting 8/22 + 8/23 JSONs -> 40 rows).
- New-day top picks (run variance visible vs yesterday): MU OVERWEIGHT
  +129.6% (judge anchored to the mechanical fwd fair value this run vs
  1050 yesterday), DELL OW +72%, AMAT +39.6%, HPE BUY +16% (up from HOLD),
  PANW +6.2%. CNC dropped off (base PT ~price).

## 2026-08-23 (/loop) — Long-only 1y-XGB + VIX drawdown filter + Mean-Reversion switch
User ask: try a LONG-ONLY strategy by predicting 1y return with XGB, use VIX to
filter large drawdowns, and when filtered apply market-neutral mean-reversal.
Built `tools/quant/bigmove/xgb_1y_longonly_vix_mr.py` (all PIT, monthly, 2009-):
  L1 long-only = top-decile by 1y XGB (gkx_preds_xgb_1y_pit), monthly EW, book
     ret_next, px>=2, 6bp/side.  LU raw: SR 0.80, ann +16.3%, maxDD -55.4%.
  L2 VIX filter: two gates compared (month-end VIX lagged 1m, no lookahead).
  L3 when filtered -> deploy validated k5_n30 market-neutral reversal sleeve
     (long-worst/short-best, dollar-neutral) sized to the de-risked capital.

FINDING 1 — the LEVEL VIX gate (22->0.5x, 35->0x) is WRONG for long-only.
It was tuned for the L/S book (RESEARCH_LOG 08-20) where it cut dd -36->-24%
at neutral ann. For the long-only book it DESTROYS Sharpe: SR 0.80->0.59,
ann +16.3%->+9.1%. Mechanism: VIX stays high through crashes AND the big
rebound months (2009/2010/2020 avg +7.8%/+2.8%/+6.7% but gate de-risks them);
of the book's 20 worst months only 7 even had VIX>22 (the drawdowns are mostly
idiosyncratic factor losses, not market crashes).

FINDING 2 — a VIX SPIKE gate (VIX > 1.5x trailing-12m median -> 0.5x) is the
right long-only filter: flags true stress, stays low during recoveries.
  LU+spike: SR 0.81 (preserved), ann +15.5%, maxDD -55.4% -> -45.7%,
  Calmar 0.29 -> 0.34. Cuts ~10pp off the DD at neutral Sharpe.

FINDING 3 — the MR switch WORKS as designed (crash insurance). LU+spike+MR:
  SR 0.81, ann +15.6%, DD -44.9%. It converts the stress windows:
    2020 COVID raw +7.6% (FEB-APR: crash + recovery) -> +4.1% under gate, net
       stays positive; vs pure level-gate which over-de-risks recovery -> -0.6%.
    2022 bear raw -31.9% -> -15.8% (halved).
  MR standalone daily SR +0.21 (validated PASS crash-insurance role).

VERDICT: long-only 1y-XGB is a solid standalone (SR 0.80) but has a big -55%
DD that VIX cannot fully fix (most of its drawdowns are idiosyncratic, not
market crashes). The CORRECT VIX filter for long-only is the SPIKE gate (not
the L/S level gate), which trims DD ~10pp at neutral Sharpe. The MR sleeve is
the right complement in the FILTERED (market-stress) regime ONLY — it converts
market crashes (2020/2022) from losses to gains/trimmed losses, at ~neutral
full-window Sharpe. Deploy MR only stress-gated at small size (0.3-0.5x
de-risked capital) as a crash overlay, never standalone.
Artifact: tools/quant/reports/xgb_horizons/xgb_1y_longonly_vix_mr.json

## 2026-08-23 (/loop iter2) — RECONCILE: why long-only is worse than the L/S champion
User (rightly) pushed back: the repo had ALREADY converged a far stronger
L/S stack (ex1st champion: quarterly EW t=0.25 + VIX gate -> SR 1.20, ann
+24.1%, dd -23.1%; combo 1.15/1.21). My previous long-only test was worse
(lower ann, bigger dd, poorer SR). Root-caused with a leg-level decomposition
(correct quarterly ret_fwd3 booking, EW, px>=2, 2009-):

  champion t=0.25 L/S : SR 1.14  ann +25.3%  dd -33.4%
  long-only  t=1.0    : SR 0.93  ann +36.1%  dd -73.0%
  (leg contribution)  long leg 1.25x: SR 0.95 ann +24.8% dd -51.3%
                       short leg -0.75x: SR 0.02 ann -0.9%  dd -56.4%

WHY THE SHORT LEG MATTERS (the answer): the SHORT leg itself makes ~zero
return (ann -0.9%), but it is the DRAWDOWN HEDGE. Long-only has HIGHER ann
(+36.1% vs +25.3% -- beta pays in a bull-heavy window) but carries the full
-73% market/beta tail. The t=0.25 short hedge costs ~11pp ann but CUTS the
drawdown by ~40pp (-73% -> -33%), which is what lifts Sharpe 0.93->1.14 and
Calmar ~0.5->0.76. So the "market neural mean-reversion" idea the user asked
about is ALREADY implemented as the short leg of the L/S construction plus
the VIX gate at formation -- not a separate MR sleeve on top of a bare
long-only book. Long-only is not an upgrade; it removes the hedge.

ALSO CORRECTED: my earlier long-only numbers (SR 0.80/ann +16.3%/dd -55.4%)
were themselves MIS-SPECIFIED -- I booked the monthly ret_next on the 1-YEAR
signal (the horizon-mismatch backtest bug this repo's logs repeatedly warn
about). Booked correctly (quarterly ret_fwd3) the long-only book is
SR 0.93/ann +36.1%/dd -73.0%. So the long leg is far stronger than my first
pass suggested, but it is unhedged and un-investable as-is.

CONCLUSION: keep the L/S stack (ex1st ex1st + VIX gate = the deployed master;
STRATEGY_STACK.md). The short leg = market-neutral-ish CRASH HEDGE (low-cost
dd reducer); the VIX gate trims the non-crash factor tail. If the user wants
a long-only book it must keep SOME hedge/tilt (e.g. t>=0.5 -> dd -47%, SR
1.09) and the VIX gate; a pure t=1.0 -73% dd book is not deployable.

## 2026-08-23 (/loop keep-optimizing iter1) — COMBO WEIGHT SWEPT: optimal is ~2:1 1y:1m (SR 1.45)
Swept the champion combo's blend weight on the actual monthly return series
(no retraining; 1y ex1st leg = staggered quarterly t=0.25 book; 1m leg = ens1m
monthly decile L/S). Aligned 2009-2026 monthly (n=210).

  legs           : 1y ex1st SR 1.30 ann +25.4% dd -35.6% Calmar 0.71
                   1m ens   SR 0.95 ann +19.5% dd -59.5% Calmar 0.33
                   corr 0.26 (real diversification)
  combo w=w1y    : 0.4->SR1.34/-46.9% | 0.5->1.41/-43.7% | 0.65->1.447/-38.6%
                     | 0.7->1.444/-37.1% | 0.8->1.41/-36.4% | 1.0->1.30/-35.6%
  OPTIMUM        : w1y ~0.65-0.70 than the deployed 50/50 (1.15) or 40/60
                    (1.21): SR 1.44-1.447, ann +24.1-24.4%, dd -38.6 to -37.1%.
                    Robust plateau 0.60-0.75 (all ~1.44), not knife-edge.

FINDING: the deployed combo underweights the 1y leg. Shifting to ~2/3 1y
(ex1st) / 1/3 1m (ens) raises SR ~1.41->1.45 AND cuts dd ~-44%->-38% vs the
current 50/50, because the 1y leg has far better Calmar (0.71 vs 0.33) and
the 1m leg's high-vol tail dominates the blend. Rationale is structural, not
a lucky pick: the 1y leg is the lower-vol, higher-quality book; the 1m leg
adds return diversification (corr 0.26) but at high dd.
Honesty: blend weight chosen in-sample (champion legs already picked); treat
as re-weighting guidance, not a fresh OOS claim. Robust plateau makes it
safe: any 0.6-0.75 works.
Artifact: tools/quant/bigmove/xgb_combo_weight_sweep.py +
tools/quant/reports/xgb_horizons/gkx_combo_legs_monthly.csv

## 2026-08-23 (/loop, revised prompt) — explicit current/1yr/expected-return format
- User refined the task: each report must list CURRENT price, PREDICTED
  ONE-YEAR-LATER price, and EXPECTED RETURN (not an ambiguous target).
- report renderer now opens every report with a "1. Expected return
  (current -> predicted 1-yr price)" table (Current | Predicted 12-mo |
  Expected return), then scenarios; sections renumbered to 9. Docs
  (INDEX.md / TOP_PICKS.md) relabeled with explicit "Current price |
  Predicted 1-yr price | ExpRet" columns.
- New helper `tools/wt/agent/print_expected_returns.py` prints the whole
  top-20 as a clean Current | Pred-1yr | ExpRet | Rating table.
- INCIDENT (handled honestly): mid-session the LLM API key (DEEPSEEK_API_KEY,
  used as ANTHROPIC_API_KEY) became unavailable in the shell, so a --force
  batch regenerated all 20 reports as DATA-ONLY shells (3 LLM nodes failed:
  "no LLM provider configured"). Detected via the error strings,
  CONFIRMED all 20 had no judge, DELETED the broken 8/23 shells, and kept
  the intact 8/22 full-debate set. Reports re-rendered to the new format
  deterministically from the intact JSONs (no LLM needed) -> 20/20 md
  updated, 0 data loss. This is why fresh 8/23 LLM debates are NOT present:
  the key isn't persisted anywhere in the repo/env; restore the key to get
  the next daily refresh.

## 2026-08-23 (/loop lower-dd) — VOL-TARGET the COMBO = the drawdown lever (SR 1.58, dd cut 11-14pp, ann KEPT)
User ask: lower the champion (combo w1y=0.65, SR 1.447, ann +24.1%, dd
-38.6%) drawdown, KEEP ann, IMPROVE Sharpe, using any macro/market data.
Tested on the champion combo's monthly return series (2009-2026):
  - VIX level gates (22/25/28/...)   : cut dd 8-18pp but ann -3 to -6pp (SR<base)
  - VIX spike gates (k x 12m med)    : k=1.4/f0.6 -> SR 1.489, ann -1.5pp,
                                       dd -30.5%; dominated by vol-target.
  - market-trend (union-index ret12<0 / below 12m MA): DISASTER for ann
                                       (+24% -> +12%), withdraws in the
                                       up-trends too. Discarded.
  => HEADLINE: VOL-TARGETING THE WHOLE COMBO (not per-leg, at a HIGHER
     target ~0.13-0.14) is the only overlay that satisfies all three asks:
       win=9/12, ann-target 0.13-0.14 (cap 1.5x):
         SR 1.582-1.639 (base 1.447)  -- IMPROVE
         ann +23.8% to +24.7%         -- KEPT (base +24.1%)
         dd -24% to -27.5%            -- CUT 11-14pp (base -38.6%)
  Robust: EVERY (window 9-18 x target 0.12-0.16) config improves SR
  (+0.09..+0.20) and cuts dd. The ann=0.14/win=12 point is the balanced pick.
  Mechanism: vol-target SCALES UP in the book's calm-strong months and DOWN
  in turbulent ones -- it captures the same/more return with far less tail,
  vs macro-gates which WITHDRAW to cash in stress and miss the re-upticks
  (that's why trend/VIX-level gates halve ann).
  Distinction: this is whole-combo vol-targeting at target ~0.14, NOT the
  per-leg vol-targ in STRATEGY_STACK (which ran both legs at ~5-6% -> ann +8-
  9%). The higher target is what preserves ann while still cutting the tail.
Artifact: tools/quant/bigmove/xgb_combo_dd_filters.py (sweep)

## 2026-08-23 (/loop lower-dd iter2) — 6 BPS COST CHECK: vol-target survives; drag ~8bp/yr
User reminder: trade cost is 6 bps. Verified:
1. The combo legs ALREADY net 6 bps/side (COST=0.0006): 1y ex1st book
   applies 4*COST at formation/exit (24bp full cycle), 1m ens book applies
   4*COST monthly. So base SR 1.447 is already net of book-level 6bps costs.
2. The vol-targeting OVERLAY's own turnover cost (6bps/side on the exposure
   rescale, gross ~2x) is NEGLIGIBLE because vol-scaled exposure moves slowly:
     monthly-churn drag ~0.0068%/mo (~8bp/yr). Honest (B) model:
       SR 1.576 (vs 1.582 no-cost), ann +24.6%, dd -27.5%  -- UNCHANGED.
     quarterly-churn (C): SR 1.481, dd -28.7% (drag 0.0051%/mo)
     threshold-churn (D, 22 rebalances): SR 1.549, ann +25.1%, dd -30.8%
   => the vol-target Sharpe improvement (1.447->~1.55-1.58) is REAL, not a
   cost-accounting artifact. Vol-scaled exposure is smooth -> low churn.
Artifact note: /tmp/vt_cost.py (turnover-cost check).

## 2026-08-23 (/loop lower-dd iter3) — VOL-TARGET IS STRICTLY-DOMINANT: ann & SR BOTH rise, dd cut 11pp
User asked (stricter): filter the champion drawdown with best efforts WITHOUT
lowering annual return AND without lowering Sharpe. Clean result on the combo
(monthly 2009-2026, all net of 6 bps incl. overlay churn cost):

  BASE:                SR 1.447   ann +24.15%   dd -38.6%
  vol-targ win12 @0.14 SR 1.576   ann +24.62%   dd -27.5%
    -> SR +0.13 (UP), ann +0.47pp (UP), dd CUT 11.1pp
  => STRICTLY DOMINANT: does NOT lower ann or Sharpe, both RISE, dd cut 11pp.
  Best-effort alternative (accept a hair of ann for more dd cut + higher SR):
  vol-targ win9 @0.13  SR 1.630 (Δ+0.183) ann -0.49pp dd -24.3% (cut 14.4pp)

A fine grid found NO config that needs to sacrifice the exact win12@0.14
Pareto point on the ann/SR frontier: it is the recommended deployment. The
strict "no lowering" ask is met by win12@0.14 precisely (ann +24.6%, SR
1.576, dd -27.5%); win9@0.13 only if a -0.5pp ann cost is tolerable in
exchange for SR 1.63 and dd -24%. Vol-targeting captures the book's own
high-vol reward months (scales up) while cutting the tail -- the mechanism
that lets it improve BOTH ann and SR together (macro-gates can't, they
withdraw to cash in the recovery).

## 2026-08-23 (/loop lower-dd iter4) — ALT-DATA: DXY dollar-stress gate ON TOP of vol-target = new champion dd filter
User pivot: can NEW signals / alternative data (not just VIX/vol) filter the
big drawdown? Tested macro/alternative series on the combo (monthly 2009-26,
all net of 6 bps incl overlay churn).
NEGATIVE (standalone): credit BAA-AAA/BAA-10y z-scores, t10y2y inversion,
gold-12m, breadth<0.4/0.5 ALL fail standalone -- they either lag the equity
drawdowns (credit/curve: cost 1-4pp ann, dd ~unchanged) or mis-time the
recovery (gold/breadth: halve ann like VIX-level/MR-gates). DXY alone is the
best macro single (SR 1.54) but still < vol-targ.
BREAKTHROUGH (STACK): DXY-z>1.5->0.7 gate ON TOP of vol-targ win12@0.14
strictly dominates both the raw combo and vol-targ alone:
  raw combo           : SR 1.447  ann +24.15%  dd -38.6%
  vol-targ win12@0.14 : SR 1.576  ann +24.62%  dd -27.5%
  + DXY z>1.5 ->0.7   : SR 1.630  ann +24.10%  dd -24.1%   <-- NEW champion
Robust: zt 1.3-2.0 -> SR 1.59-1.63 (plateau, not knife-edge). Gates ~20% of
months spread across years (esp. 2022=6mo); not a single-episode overfit.
MECHANISM: DXY spikes mark dollar/liquidity-deleveraging stress that hits an
equity L/S book but lags the book's OWN trailing vol -- so it adds orthogonal
signal on top of vol-target. Unlike gold/VIX, DXY does NOT stay elevated
during equity recoveries, so it trims the dollar-driven tail without giving
back the recovery.
VERDICT: keep vol-targ win12@0.14 AS the base dd filter, add a LIGHTER DXY-z
gate (z>1.5, de-risk to 0.7) on top. Best 6-bps result so far for
"cut dd, keep ann, improve SR".

## 2026-08-23 (/loop, task: get more stocks with expected return >=30%)
- Scheduling: cron tools unavailable in this session's context -> could NOT
  create a new persistent recurring job for this prompt. Prior MCP/session
  jobs for older prompts remain intact server-side.
- Research (deterministic, no LLM needed; LLM key still absent):
  * Re-ran the full 292-stock momentum screen. Beyond the current top-20,
    the next-tier names (MRK, CSCO, AMD, GOOGL, USB, WAB, CRWD, APA, TRV,
    XOM, ILMN, BAC, HWM, CSX) were evaluated for forward-EPS-anchored
    expected return.
  * RESULT: NONE of them carry a forward-consensus EPS in the free data
    stack (only DELL, AMAT, PANW, MU, HPE, CNC do). Without a forward
    anchor the deterministic valuation abstains and reports 0% -- no basis
    for a >=30% claim.
  * Names currently clearing >=30% in trusted coverage: DELL +72.0%,
    AMAT +39.6%. (MU was +129.6% on the 8/23 censored run but reverted to
    +8.6% on the trusted set -- single-run variance.)
  * CONCLUSION: more >=30% names require (a) LLM key to re-run debates AND
    (b) a paid/better consensus feed (Finnhub target-price is 403 on free
    tier). With free data the >=30% universe is capped at DELL + AMAT.

## 2026-08-23 — REGIME-SWITCH champion: market-neutral MR sleeve during the downside

**User ask (recurring loop prompt):** "during the downside, we can develop
market neutral mean reversal strategies."

**Thesis confirmed + built.** The deck already had a *validated* market-neutral
MR crash-sleeve (k5_n30: long-worst/short-best, dollar-neutral, pass
signal-scramble gate). Empirically it returns +0.52%/mo in the 20 worst
combo-drawdown months (combo -0.62% same months), monthly rho -0.09 vs combo,
SR 1.00 / ann +20.7% in DXY-stress months where the de-risked champion makes
only +3.4% (SR 0.45). Those 41 stress months are exactly where the champion
steps to 0.5x — so rotate that capital into the MR sleeve instead of cash.

**Result (210 months, all net 6 bps, no lookahead; artifact
xgb_combo_regime_mr.py/json):**

| Config | SR | ann | dd |
|---|---|---|---|
| raw combo | 1.447 | +24.1% | -38.6% |
| vol-targ win12@0.14 | 1.576 | +24.6% | -27.5% |
| + DXY z>1.5→0.5 | 1.650 | +23.7% | -22.5% |
| **+ MR overlay f=0.4 in stress** | **1.715** | **+25.6%** | **-23.8%** |

New champion beats the prior DXY champion (1.63) on ALL THREE axes: SR 1.715
vs 1.63, ann +25.6% vs +24.1%, dd -23.8% vs -24.1%. The MR overlay adds
+0.065 SR / +1.9% ann at a modest dd cost.

**Robustness (flat plateau, no single pick):** MR f=0.2-0.6 all SR 1.67-1.72;
VT target 0.12-0.16 all >=1.66; DXY z 1.3-2.0 all >=1.61; DXY_F 0.5-0.8 all
>=1.67; MR k5_n20/30/40 + k3_n20 all >=1.66. Softer DXY de-risk (0.7) also
works (SR 1.69), but the harder 0.5 + MR gives the best overall.

**Honesty check:** SR 1.715 is the tuned best among a stable plateau
(1.67-1.72), not a lone overfit spike. The MR sleeve is validated by the
signal-scramble gate from earlier work; its monthly contribution here is
strictly additive to the de-risked champion across MR f=0.1-1.0 INDEPENDENT
of the champion's own params — so the regime-switch result is a genuine,
robust improvement, not parameter luck.

**Deployment:** vol-target whole combo (win12@0.14 cap1.5) + DXY z>1.5→0.5 +
MR overlay f=0.4 during those stress months. Next refit 2027-01-31.

## 2026-08-23 — MACRO drawdown filter: credit-spread widening on the regime-switch (SR 1.751, dd -19.5%)

**User ask (recurring loop):** "use all macro indexes and market data to filter
the drawdown without affecting the annual return and Sharpe."

**Approach (exhaustive):** took the SR 1.715 regime-switch champion
(vol-targ + DXY + MR-in-downside) and tested EVERY macro series in the deck
as an ADDITIONAL de-risk layer: credit (aaa, baa, BAA-AAA), rates (us10y/2y/
30y/t10y2y/tbill3m), commodities (brent/wti/natgas/xau/slv), equity
(dow/spx), FX + vix, at 12m z-stress thresholds, various de-risk factors.

**Honest negative on most:** single macro gates (credit levels, rates,
curve, gold, momentum) all FAIL to cut dd while keeping SR>=1.715/ann — same
failure mode as the earlier standalone gates (they lag the drawdown or
mis-time the recovery; aggressive trims cut ann to single digits).

**The one that works — CREDIT WIDENING (BAA-AAA z, supplemental layer):**

| Config | SR | ann | dd |
|---|---|---|---|
| raw combo | 1.447 | +24.1% | -38.6% |
| champion (vol-targ+DXY+MR) | 1.715 | +25.6% | -23.8% |
| **+ credit z>1.3 -> 0.5** | **1.751** | **+24.7%** | **-19.5%** |

First time the book's MaxDD breaks below -20% while SR stays >=1.7 and ann
~+25%. Credit flags 33/210 months (16%) across genuine credit-stress eras
(7 in 2015, 7 in 2018, 6 in 2022, 2 in 2020) — real economic signal, not
lucky month picks.

**Why it works:** credit widening marks the credit-stress regimes (2015-16,
2018 Q4, 2020, 2022) where an equity L/S book's TAIL risk concentrates but
which the dollar-stress (DXY) and trailing-vol do not fully anticipate. It
de-risks ONLY those ~33 months; stacking it lightly on the champion (not
standalone, which over-trims the recovery) keeps the good months at full tilt
and cuts the tail.

**Robustness (flat plateau, no knife-edge):** window 9-12 x threshold 1.0-1.5
x de-risk 0.5-0.7 ALL improve the champion on all three axes (SR 1.73-1.76,
dd -19.5% to -21.2%, ann +23.7% to +25.2%). Chose center config
(win12/thr1.3/f2 0.5, SR 1.751, ann +24.7%, dd -19.5%) to avoid overfitting
the single best point (win9/thr1.3/f2 0.5 = SR 1.757).

**All net of 6 bps/side (overlay churn charged), no lookahead (credit z
lagged one month).** Artifacts: `xgb_combo_credit_macro.py`/`.json`.

**Deployment:** vol-targ whole combo (win12@0.14 cap1.5) + DXY z>1.5->0.5 +
MR k5_n30 overlay f=0.4 in DXY-stress + credit BAA-AAA z>1.3->0.5 de-risk.
Full stack: SR 1.751 / ann +24.7% / dd -19.5%. Next refit 2027-01-31.

## 2026-08-23 — MR-in-downside, UNION activation gate (SR 1.760, dd -18.2%)

**Refinement** of the credit-macro champion (SR 1.751 / ann +24.7% / dd
-19.5%). User's recurring loop directive (MR during downside + all macro data
to filter drawdown).

**The one change:** broaden the market-neutral MR k5_n30 sleeve's ACTIVATION
gate from DXY-stress ONLY to **DXY OR credit-widening** (the union of the two
validated downside/stress signals). All other params identical to the prior
champion — this isolates exactly the MR-union contribution.

| Config | SR | ann | dd |
|---|---|---|---|
| champion (MR on DXY only) | 1.751 | +24.7% | -19.5% |
| **MR on DXY ∪ credit** | **1.760** | **+24.7%** | **-18.2%** |

Strictly dominates: same ann +24.7%, +0.009 SR, -1.3pp dd. Why: the MR
sleeve pays in BOTH dollar-stress AND credit-stress downside months
(+1.05%/mo across the 33 credit-stress months); activating on the union adds
19 credit-only months (not already covered by DXY) where MR earns its
drawdown premium, pulling the tail lower at zero ann cost. MR active 60/210
months (union of 41 dollar- + 33 credit-stress).

**Robustness:** full plateau credit win9-12 x thr1.0-1.5 x f2 0.5-0.7 x MR
f0.3-0.5 all give SR 1.76-1.78 / dd -17.8 to -19.2% / ann +24.5-25.9% — a
robust region, not a lone overfit pick. Chose the minimal-change config (same
champion params, only MR activation broadened) for clean attribution.

**All net of 6 bps/side (overlay churn), no lookahead (exogenous lagged).**
Artifacts: `xgb_combo_mr_union.py`/`.json`.

**Deployment:** vol-targ combo (win12@0.14 cap1.5) + DXY z>1.5->0.5 + credit
BAA-AAA z>1.3->0.5 + MR k5_n30 f=0.4 active in DXY∪credit stress months.
Full stack: SR 1.760 / ann +24.7% / dd -18.2%. Next refit 2027-01-31.

## 2026-08-23 — BLEND-WEIGHT re-opt under full overlay (w1y=0.75; SR 1.774, dd -16.5%)

**User ask (recurring loop):** MR-in-downside + all macro to filter dd + improve
using all possible methods / more data input.

**Improvement:** re-optimize the combo blend weight w1y (weight on the
1y-ex1st leg vs 1m-ensemble) CONDITIONAL on the full overlay stack, rather
than the original ~0.65 tuned on the RAW combo before any drawdown overlay
existed. A legitimate "use more of the available information" improvement.

| Config | SR | ann | dd |
|---|---|---|---|
| raw combo | 1.447 | +24.1% | -38.6% |
| w1y=0.65 (MR-union champion) | 1.760 | +24.7% | -18.2% |
| **w1y=0.75 (re-optimized)** | **1.774** | **+24.8%** | **-16.5%** |

Better on all three axes; MaxDD a new low -16.5%.

**Why the optimum shifts up:** under vol-targeting + macro de-risk gates, the
higher-Calmar 1y-ex1st leg is disproportionately protected across the
overlays (its higher-drawdown months are de-risked), so tilting heavier into
it (less of the lower-Calmar 1m-ensemble) harvests its superior per-unit
risk better.

**Robustness:** plateau w1y=0.68-0.82 all give SR 1.764-1.774, ann +24.8%
(flat), dd -16.5 to -17.5% — a wide stable region, not a single spike. 0.75
chosen as center. 

**Also tested this iteration (honest negatives / no change):**
- MR data-input: tested k3_n30 sleeve (standalone higher SR 0.366) and
  avg(k3,k5) as the MR overlay — NEITHER beats k5_n30 in the overlay (k3:
  SR 1.66; avg: 1.748 vs k5 1.760), because k3's crash episodes (esp. 2018
  Q4) are less reliable. k5_n30 stays the MR data input.
- COT positioning: no clean USD-index contract in the data (dollar markets
  are nat-gas); building a dollar spec-positioning early-warning from
  EUR/JPY/GBP is too noisy/ambiguous for reliable payoff — not pursued.

**All net of 6 bps/side (overlay churn), no lookahead (exogenous lagged).**
Artifacts: `xgb_combo_w1y_opt.py`/`.json`.

**Deployment (full stack):** vol-targ combo (win12@0.14 cap1.5) + DXY
z>1.5->0.5 + credit BAA-AAA z>1.3->0.5 + MR k5_n30 f=0.4 in DXY|credit, all
with blend weight w1y=0.75. Full stack: SR 1.774 / ann +24.8% / dd -16.5%.
Next refit 2027-01-31.

## 2026-08-23 — TESTED-NEGATIVE: adding large-VIX activation for MR does NOT beat champion

**User hypothesis:** "market neutral mean reversal strategies work well during
large VIX; try to add it during large VIX time to our champion and test if it
makes results better."

**Direct test on the SR 1.774 / ann +24.8% / dd -16.5% champion** (w1y=0.75,
vol-targ + DXY + credit + MR k5_n30 f=0.4 on DXY|credit). Tested MR activation
via VIX-large as (a) added to the existing DXY|credit union and (b) standalone
replacement, across VIX level thresholds 25/28/30/35 and VIX-spike ratios
1.5/2.0/2.5, and fine VIX-spike k 1.4-2.5 x MR f 0.3-0.5.

**RESULT: no large-VIX config beats the champion.** 
- VIX-large ONLY (replaces union): SR 1.67-1.72, ann +23.1-23.9% (crushes
  ann ~1pp) — clearly worse.
- VIX-large added to union: mostly SR 1.68-1.74 (below 1.774); best was
  VIXsp>2.0 (RX 1.772/+25.0%, SR marginally below 1.774) — a wash, not a
  strict improvement. Fine sweep k1.4-2.5 x f0.3-0.5: NO config exceeds 1.774.
- Adding VIX-level as de-risk factor (0.7) also worse (1.75-1.76).

**WHY (the mechanism, verified):** only 17 of the champion's 60 MR-active
months have VIX>25 (28%). The DXY|credit gate already activates MR in 43
downside months where VIX is NOT elevated — dollar-stress and credit-widening
capture downside/financial-stress regimes that high-VIX alone misses (slow
grinds, credit-squeeze periods where VIX is subdued but the L/S book bleeds).
So the user's large-VIX MR hypothesis is ALREADY captured by the champion's
macro-stress union; explicitly adding VIX-large pulls in high-VIX-but-not-
crashing months where MR doesn't reliably pay (dilutes SR/ann) and is
redundant.

**Conclusion:** champion UNCHANGED (SR 1.774 / ann +24.8% / dd -16.5%).
The large-VIX MR edge is subsumed in the existing DXY|credit activation gate.
