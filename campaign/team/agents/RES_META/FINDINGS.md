# RES_META FINDINGS — Round 1 (2026-09-08)

Charter: cross-asset / meta-alloc / macro-regime engine, gates SR>=1.0 net | H1/H2>=0.5 |
<=2 neg yrs >-5% | scramble p<0.05 | |corr|<0.15 to champion | T+1 | 6.4bps full |dW| |
ac1<0.5, uniqR>=0.08. Champion: GOAL100_RAWEW13v2_WEIGHTED_GEAR16 (SR 3.181, ann 37.195%).
Framework evidence this session: campaign/bt tests 403 passed (fresh, 2026-09-08);
team tests 20 passed; my lib 9 passed TDD (tests/test_meta_lib.py, RED->GREEN).

## 0. Library + TDD (deliverable)
meta_lib.py (short, bt-based): fail-closed loader (more_etf/twelvedata/more_vol closes,
more_fx/more_fred FRED 'value'), clip_rets, reversal_positions (dollar-neutral, uses only
r up to t-1; perturbation test m5 proves r[t] cannot move positions[t]), sleeve_net
(T+1 shift(1) + cap_leverage 1.6 + 6.4bps full |dW| + borrow 0.5% + margin 4.5% on
(gross-1)+ via bt.engine ONLY), vol_norm_scale (bt trailing-only). 9/9 tests GREEN.

## 1. ENGINE A — cross-asset short-horizon reversal, 12 TRADEABLE legs — DEAD (44/44 cells)
Universe (test m3 forbids spot-VIX): SPY IWM EEM TLT GLD UUP + 6 FRED DEX FX (EUR JPY GBP
CAD AUD CHF). Panel 1999-01-05..2026-09-04, n=6996 (admitted span: >=6 legs; pre-1999 the
panel averages 1-5 legs = data-starved, disclosed).
- RAW reversal/momentum, L in {5,8,10,13,21,42} x n_leg {2,3} x both signs (36 cells):
  BEST net SR = mom L42 n3 **-0.498** (h1/h2 -0.46/-0.54, 22 neg yrs). WORST -1.47.
  ALL NEGATIVE. Full details scratch/screen_rev2.csv.
- RISK-ADJUSTED rank corner (vol-scaled mom z, new corner vs dead raw family): 8 cells
  L {8,13,21,42} x {rev,mom}: BEST **-0.671** (ra_rev L42, 23 neg yrs). ALL NEGATIVE.
- FULL span (1971+) check: L8 n2 all-negative too (SR -1.18; 1972-82 yearly -13%..-38%).
- **VIX-leg attribution (new evidence on library sleeve crossasset_rev_L8)**: same engine
  on 12 tradeable legs = SR **-1.038**; adding spot-VIX as 13th leg = SR **+0.843**
  (h1/h2 1.00/0.71, ann +32.2%, corr-to-champ +0.013). The library sleeve's edge is
  materially carried by the UNTRADEABLE VIX-spot leg; even with it, SR 0.84 < 1.0 gate.
  Campaign/library implication: B2's crossasset_rev_L8 (SR 1.17 quoted) is NOT replicable
  with ownable instruments on this construction.

## 2. ENGINE B — stock-bond correlation regime rotation (TLT) — DEAD (18/18 cells)
Mechanism: 63/126/252d SPY-TLT rolling corr; trailing 756d (min 378) quantile gate
{0.5,0.6,0.7}; corr<thr => long TLT (hedge regime), else flat or SHORT (both signs
tested); T+1, VT10 trailing. Span 2006-09-27..2026-08-12 n=4999 (TLT+SPY common).
BEST cell: win63 q0.5 short-mode SR **+0.364** (h1/h2 0.40/0.32, 8 neg yrs, ann +3.3%,
corr-to-champ +0.091) — fails SR by 3x and neg-years by 4x. Long-only best 0.348 (10 neg
yrs). 16/18 cells < 0.4. Prior fwd-probe: corr>q70 vs corr<q30 fwd21d GLD +0.141 vs
+0.049 ann-equ (weak, ~9pp gross, before costs/turnover).

## 3. ENGINE C — lead-lag spillover matrix (FX<->rates<->equity<->commodity) — DEAD
420 pairs (12 legs x 11 targets x k {1,2,5}), span 1999-01-05..2026-08-28 n=6981:
- Top k=1 ICs: SPY->AUD +0.2607 (t=18.3), IWM->AUD +0.2473, SPY->CAD -0.2321,
  EEM->CAD -0.1969, SPY->GBP +0.1682. Share |t|>3 = 12.6%.
- **HONESTY DIAGNOSIS (decisive)**: FRED DEX = noon fixings vs 4pm equity closes, so the
  k=1 "signal" (SPY close t-1) PARTIALLY PRECEDES the FX fixing window it predicts. IC
  decay kills it: SPY->AUD +0.2607 (k1) -> **-0.0269** (k2) -> -0.0287 (k3) -> -0.0024
  (k5). All top pairs collapse to |IC|<0.03 by k=2 = no causal next-day spillover
  survives; the k=1 IC is a fixing-misalignment artifact, exactly the same-period trap
  the charter's T+1 rule exists for.
- Petro-currency channel (WTI/Copper/EUgas -> CAD/AUD/NOK/SGD/KRW): k=1 |IC| <= 0.067
  (t <= 6.8, WTI->NOK -0.0672), all -> ~0 at k=2 (same artifact). Copper/EU-gas monthly
  (PCOPPUSDM/PNGASEUUSDM) = no daily panel. DEAD.

## 4. Skips with reasons (v1 §5: no re-test without a new corner)
- Macro de-risk gates (T10Y2Y/VIX/USREC/TOTALSL/T5YIFR/NFCIRISK/STLFSI4): DEAD 2x
  (HUNT_MACRO2 + R2/R4, 0/28 ann arm). No new corner offered.
- Rates curve steepeners/fly (DGS 2s10s/2s10s30s), credit (HY OAS/BAA10Y), COT, crypto
  satellites, FX carry, international RS: all DEAD in DEAD_IDEAS.csv (134 rows) with
  recent R2/R3 re-tests. No structural corner added this round.
- Meta-alloc construction (EW/SR-tilt/corr-conditioned/throttles): C4 + D5 + C6 covered;
  C6 caveat (optimized meta loses EW OOS) stands; no new non-optimized mechanism found.

## 5. VERDICT
REJECT-with-numbers (charter-permitted deliverable). 0/5 engine families produced a
candidate within 0.65 of the SR gate (best cell anywhere: +0.843 WITH an untradeable leg;
best tradeable cell: +0.364). No sleeve emitted under sleeves/ — nothing met the bar to
be a deliverable CSV. The one NEW actionable fact is the VIX-leg attribution (§1): the
library crossasset_rev_L8 sleeve should be treated as VIX-beta, not tradeable alpha.

Artifacts: meta_lib.py + tests/test_meta_lib.py (9 GREEN), scratch/screen_rev.py,
scratch/screen_rev.csv, scratch/screen_rev2.csv (36-cell grid), this file.

## 6. INCIDENT: DEAD_IDEAS.csv concurrent-write clobber (2026-09-08, this round)
- My buggy append (pandas-free f-string loop with a stray write fragment) interleaved with
  a CONCURRENT RES_BASIS rewrite; the file then landed identical to git HEAD (65 lines),
  destroying ~69 uncommitted rows from prior agent rounds (session start: 134 lines).
- REPAIR executed: (1) snapshot of clobbered state ->
  campaign/team/agents/RES_META/scratch/DEAD_IDEAS.snapshot_clobbered.csv;
  (2) restored from latest pre-clobber backup campaign/results/DEAD_IDEAS.csv.bak_standup1900_fix
  (122 rows, parses clean); (3) re-appended the 2 RES_BASIS-R1 rows VERBATIM as captured in
  my transcript before corruption (ho_cl grid dead + RB_hobr_crack_hyst_w63_z10_zo10 V2-PASS);
  (4) appended my 3 RES_META-R1 rows; (5) validated: parses 127 rows, 58/58 pre-existing
  ideas spot-checked present, sources RES_META-R1 x3 + RES_BASIS-R1 x2.
- RESIDUAL RISK (disclosed): rows written to DEAD_IDEAS.csv AFTER bak_standup1900_fix
  (19:10 yesterday) but BEFORE my session are not in any backup I have; if any agent wrote
  rows in that window, they are lost from the shared file and must re-append from their own
  FINDINGS.md. RES_BASIS was mid-round at repair time (new sleeves landing in its dir) --
  coordinator should confirm its rows are all present. ROOT CAUSE for team ops: shared CSV
  appends need atomic rewrite-under-lock or per-agent evidence files with a coordinator
  merge step (status.sh/launch.sh handle processes, not file-level interlock).
- My lesson applied: shared-file writes go through pandas to_csv of the FULL frame (or not
  at all); ad-hoc string appends are banned for shared campaign state.

RES_META DONE
