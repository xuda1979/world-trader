# HUNT_TIMESFM — FINDINGS (Google TimesFM 3.0 forecasting sleeves)

## ROUND 1 (registered 2026-09-07 ~17:4x CST by CIO)
Charter: use Google TimesFM 3.0 (pypi timesfm==3.0.1, JAX backend, no TF) to forecast
PIT asset series and build tradeable, decorrelated, cost-honest sleeves for the GOAL100
pool. Env: M4 17GB, jax already present, pypi+hf reachable. Install first + save proof.
Expected honest outcome may be 0/N passing sleeves; that is valid. T+1 / PIT / full-|dW|
@6.4bps / all gates / |corr|<0.15 vs champion. Champion of record 37.195% / SR 3.181 /
MDD -6.69% / 0 neg yrs.

====================================================================
## ROUND 4 (2026-09-07 evening)

### Step 0 — feasibility probe (FAIL-CLOSED, executed first, CIO recipe used verbatim)
* /tmp/tfvenv alive: `import timesfm, jax` -> OK, jax==0.11.1 (pin intact).
  One env defect found+fixed WITHOUT touching the jax pin: `orbax-checkpoint` was 0.1.1,
  which installs module `orbax_checkpoint` (old layout); timesfm 3.0.1 imports
  `orbax.checkpoint` -> ModuleNotFoundError. `pip install -U orbax-checkpoint` ->
  0.12.4. Re-verified jax still 0.11.1 after upgrade. (Env fix, not a strategy result.)
* Checkpoint: google/timesfm-2.5-200m-flax downloaded via huggingface_hub 1.30.0
  (15 files, ~60s, snapshot b99e9f6c). The 3.0/2.0 repos were NOT attempted (charter).
* Toy forecast (work_r4/install_proof.py, proof also saved to work_r1/install_proof.txt):
  context 512, horizon 1, on x=sin(t/10)+noise: point fcst -0.3332 vs expected sin(60)
  = -0.3048 (sane, correct sign/phase); output shape (1,1); load+compile+forecast 5.0s
  wall on CPU. FEASIBLE -> proceed to engine.

### A-PRIORI SIGNAL DECLARATIONS (made before seeing any TimesFM-vs-return result)
Declared BEFORE any backtest of the two families below, per charter. Instruments
a-priori: 6 liquid ETFs spanning the champion's own domains — QQQ, XLE, XLF, TLT, GLD,
EEM (champion window 2008-03-31..2026-08-27; EEM starts 2008-01-02 so its sleeve is
2008-01+). Execution a-priori: TimesFM 2.5-200m flax, context 512 (expanding, cap 512),
horizon h=1 day on DAILY CLOSE-TO-CLOSE log-price series; forecast on day T using closes
<= T; position held T+1 (strict T+1); refit EVERY bar (K=1) by construction (zero-shot,
no fit — K reported as 1); vol-target 10% trailing-only clip<=3; costs 6.4bps one-side
FULL |dW| + borrow 0.5%/yr + margin 4.5%/yr on (gross-1).
 (a) forecast-DIRECTION L/S per asset: pos=+1 if fcst[T+1]>last[T], -1 if <, 0 if =.
     Family risk declared up-front: this is a momentum-continuation RE-TEST if the
     model's point forecast reduces to "continue last move" — momentum/reversal families
     are CLOSED in DEAD_IDEAS.csv; (a) is adoptable ONLY if it beats that dead family,
     not merely pays costs.
 (b) forecast-MAGNITUDE vol overlay on the champion: scale champion exposure by
     |fcst[T+1]| percentile (hi |fcst| -> de-lever), 0.7x/1.0x mask, N=252 z/percentile
     machinery matched to HUNT_CREDIT2 (d). Mandatory content-free controls (adoptable
     only if it beats BOTH): (b1) champion's own trailing 252d realized-vol percentile
     mask (same machinery, zero TimesFM content); (b2) CONSTANT scale matched to the
     candidate's average exposure (SR is scale-invariant — a constant scale that matches
     isolates any non-uniform de-levering effect).
Baseline context declared up-front (from DEAD_IDEAS.csv + HUNT_CREDIT2 findings): naive
daily momentum on liquid ETFs at 6.4bps full-|dW| typically dies on turnover (~8x/day
gross -> ~52bps/day cost drag at ~10% vol, ~13 ann turnover), so bar (a) must clear the
DEAD momentum family, not just SR>0.


### EXECUTION (2026-09-07 ~21:45-22:35 CST; logs + CSVs in work_r4/, sleeves in sleeves/)
* TDD first: tests/test_tfm_engine_tdd_r4.py + test_overlay_tdd_r4.py -> `pytest -q`:
  **8 passed in 0.52s** (T+1 lag, entry-day cost charge, borrow/margin arithmetic,
  trailing-only VT clip, scramble NaN fail-closed, no-silent-fill ValueError;
  overlay constant-scale SR-neutrality, step-mask charges transitions only).
* Env re-verified this session: `/tmp/tfvenv/bin/python -c "import timesfm, jax"` -> OK,
  jax 0.11.1 (charter pin intact; orbax 0.12.4 fix from earlier still in place).
* Champion re-verified from committed CSV via bt.metrics: **SR=3.181 ann=37.20% negyr=0**
  (matches charter of record; nothing modified).
* Forecast integrity: fcst_{QQQ,XLE,XLF,TLT,GLD,EEM}.csv all 0 NaN, dates strictly
  monotone; QQQ/XLE/XLF/TLT/GLD span 2009-01-14..2026-09-03/04 (4437-4438 rows),
  EEM 2010-01-13..2026-09-04 (4187 rows, ETF inception). Context 512, h=1, strict T+1,
  refit K=1 every bar (zero-shot), PIT enforced by construction (ctx = closes <= T).

### (a) forecast-DIRECTION L/S per asset, VT10 clip3, 6.4bps full|dW|+borrow+margin — **DEAD**
Net (command output, run_a_r4.log):
  QQQ SR=-0.173 (h1 0.103/h2 -0.360, 8 negyr, worst -26.8%, corr -0.037, ann -2.2%, scr_p 0.94)
  XLE SR=-0.188 (10 negyr, scr_p 0.455)   XLF SR=-0.196 (9 negyr, scr_p 0.700)
  TLT SR=-0.750 (17 negyr, scr_p 0.710)   GLD SR=-0.800 (14 negyr, scr_p 0.915)
  EEM SR=-0.566 (13 negyr, scr_p 0.810)
  EW6 book SR=-0.848 H1=-0.715 H2=-0.963 negyr=15 worst=-13.34% ann=-4.13%
  corr_vs_champ=-0.064 n=4186; EW6 scramble_p=0.495 (real per-unit SR 0.372).
Anatomy (diag logs): gross SRs +0.204/+0.145/+0.065 (QQQ/XLE/XLF) are annihilated by
turnover — annTO 112x-154x gross per asset at 6.4bps. Direction hit ~0.50: 5/6 assets
p>0.26 binomial (XLE .505, XLF .506, TLT .498, GLD .508, EEM .493); QQQ 2323/4437
z=+3.14 p=0.0017 BUT hit_up 0.5561 vs base-up 0.5580 (no up-side skill) and hit_dn only
0.4321 — the tiny edge is ~3.4bp/day gross, ~1/20th of the cost drag.
DEAD-family check (charter requirement): TimesFM dir agrees with naive 1d momentum only
0.488-0.513 (chance) — this is NOT a momentum re-test; the model's point forecast is
genuinely non-naive, it just carries no post-cost alpha. Novel but alpha-less.
GATE VERDICT (a): fails SR>=1.0 (all negative), halves (negative), negyears (8-17),
scramble (p 0.455-0.94). ALL FAIL -> DEAD.

### (b) forecast-MAGNITUDE 0.7x overlay on champion (pct>0.8, N=252 trailing, PIT) — **NOT ADOPTED**
Candidate: dSR=+0.174 over champion (book SR 3.355 vs 3.181), days_on=112/4805 (2.3%).
Mandatory content-free controls (a-priori):
  b1 champ-own-vol mask, same machinery: dSR=+0.099 (days_on=1504)
  b2 constant 0.993x (mean-matched):   dSR=-0.006 (scale-invariance confirmed by TDD)
Kill-test results (diag logs):
  * PLATEAU FAILS both grids (bt.gates.plateau_ok): thr grid {0.6:-0.049, 0.7:+0.098,
    0.8:+0.174, 0.9:+0.118} -> neighbors +0.098/+0.118 < 0.1395 threshold -> False;
    scale grid {0.6:+0.221, 0.7:+0.174, 0.8:+0.120, 0.9:+0.059} -> neighbor 0.8 at
    0.120 < 0.1767 threshold -> False.
  * ERA FRAGILITY (HUNT_CREDIT2(d) kill pattern): top delta days are all 2020-03
    (+17.78% 03-19, +14.03% 03-20, +5.69% 03-09, +4.67% 03-18). dSR excl Mar-Apr20 =
    **-0.039**; excl all-2020 = **-0.037**; yearly delta negative in 15/19 years
    (e.g. 2008 -135bp, 2019 -109bp, 2025 -99bp; 2020 -1645bp). Era split: 08-12
    dSR -0.053, 13-19 -0.043, 20-26 +0.264. The ENTIRE lift is one 6-week window.
  * One real (non-adoptable) observation: TimesFM mask vs b1 vol-mask delta
    cand-minus-b1 = +1.886 dSR, 95%CI [+1.454, +2.284], P(diff>0)=1.000 (2000x paired
    bootstrap) — the |fcst| signal out-gated the vol mask specifically in Mar-2020.
    Mask scramble p=0.0. Statistically real, economically a single-event crisis de-lever,
    not a repeatable sleeve; span gate (>=8y of effect) fails by construction.
GATE VERDICT (b): fails plateau (2x) + era-robustness; overlay corr to champ 0.987 is
expected (not a decorrelated sleeve anyway). NOT ADOPTED; book saved as evidence.

### Evidence archived
sleeves/TIMESFM_DIR_EW6_daily.csv (+.meta, status=DEAD),
sleeves/TIMESFM_MAG_OVL_daily.csv (+.meta, status=NOT-ADOPTED);
work_r4/: run_a_r4.log, run_b_r4.log, diag_kill_r4.log, diag_kill_r4b.log,
diag_final_r4.log, save_sleeves_r4.log, all scripts, 6 forecast CSVs.
Bugs found+fixed in MY OWN save script (TDD: failing run before fix, both in log):
(1) pandas length-mismatch building the raw position frame (per-asset fcst lengths
differ 4437/4438/4187 -> outer-align per-asset Series instead); (2) literal '%' in the
meta template colliding with %-formatting -> plain string concat. No framework bugs found
(bt.engine/gates/metrics semantics confirmed by 8/8 tests).
For coordinator: please register 2 rows in DEAD_IDEAS.csv —
"TimesFM 2.5-200m h=1 forecast-direction L/S 6-ETF (novel, NOT momentum: 0.49-0.51 agree),dead,EW6 SR-0.848 negyr15; per-asset SR -0.17..-0.80; scr_p 0.46-0.94; gross +0.20 killed by 112-154x annTO @6.4bps; dir-hit ~0.50 (5/6 p>0.26)"
"TimesFM |fcst| pct>0.8->0.7x champion overlay,dead/NOT-ADOPTED,dSR +0.174 but plateau FAIL both grids; dSR excl Mar-Apr20 -0.039; lift 100% in 2020-03/04 (112 days); beats own-vol control (CI [1.45,2.28]) but single-era"
ROUND 4 VERDICT: 0/2 families adoptable. TimesFM 2.5-200m zero-shot daily h=1 point
forecasts carry NO post-cost alpha on liquid ETFs at 6.4bps full-|dW|; the one positive
dSR is a 2020-03/04-only crisis gate. Expected negative outcome confirmed.
ROUND 4 DONE


====================================================================
## ROUND 5 (2026-09-08 ~09:4x- CST) — PRE-REGISTRATION (written BEFORE any TimesFM-vs-return result)

READ FIRST done: GATES_CONTRACT_V2.md (RATIFIED; Step-2 flip EXECUTED in commit 539f50e -
leak_check default-ON, I pass sig= and leak_check=True explicitly per charter) +
DEAD_IDEAS.csv recounted MYSELF: 133 data rows (not 120 — dynamic by design). My 2 R4 rows
PRESENT (index 117 dir-L/S, 118 |fcst| overlay) -> nothing to register. Rows 125/126 are
other agents' (VOL2-R5, SECTOR2-R5). No duplicate TIMESFM registration exists.

CHAMPION VINTAGE PIN (V2 10b): campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
sha256 prefix 4358dfab95679b97 (recomputed this session) — matches charter of record.

DATA (cited, row counts + sha re-printed at run time; NO new scraping):
- tools/quant/data/newdata/NIKKEI225.csv  20,166 data rows 1949-05-16..2026-08-31,
  sha 92f09efca6eeb9fa. 976 NaN-value rows = Tokyo market holidays (1949-09-23 first,
  2026-08-11 last, spread every decade: 103-159/decade; e.g. Nov-23, Dec-29/30) ->
  DROP rows, NO ffill (faked prices would corrupt the log-price context). Post-drop
  19,190 quote days, 0 dups, 0 nonpos.
- tools/quant/data/more_fred/DPROPANEMBTX.csv  8,559 data rows 1992-07-09..2026-09-01,
  sha c71b0d1e89a2061a, 0 NaN, 0 dups, 0 nonpos (same file CMDT2-R5 used; valid id).
- Benchmarks trio pinned per V2 7c: twelvedata/SPY.csv, more_etf/IEF.csv,
  results/sleeve_library/CTA_15vol.csv (same pins as INTL2-R5/CMDT2-R5).
- Tradeability caveat declared up-front (charter named these spans anyway): NKY is a cash
  index (futures exist since 1988, ETF proxies post-2001); propane is a FRED spot index
  with NO directly tradeable instrument (CMDT2-R5 already flagged). This corner tests
  TimesFM zero-shot SKILL on the new spans; adoptability additionally requires the full
  V2 battery + these caveats to be weighed by the coordinator.

A-PRIORI SIGNAL (declared before seeing any TimesFM-vs-return number):
  Family: forecast-DIRECTION L/S at WEEKLY decision cadence (charter: "weekly TO") —
  NOT the dead R4 daily h=1 6-ETF config (120-row DEAD_IDEAS row 117) and NOT the dead
  |fcst| champion overlay (row 118); no overlay is run this round.
  Decision dates D_j = last trading day of each ISO week on the asset's OWN calendar.
  At D_j: context = last 512 log-closes <= D_j (expanding, trunc 512); TimesFM 2.5-200m
  flax (same checkpoint/config as R4: normalize_inputs=True, continuous quantile head,
  force_flip_invariance, fix_quantile_crossing); ONE model call per D_j at horizon 5;
  m_j(h) = pt[:,h-1] - last  (h=1: 1-day-ahead pt[:,0]; h=5: 5-day-ahead pt[:,4]) —
  BOTH horizons are pre-registered here, before any result (this is the whole grid, not
  a search): pos_j = sign(m_j) in {-1,0,+1}.
  Held weights: w_t = pos_j * v_j for all trading days t in (D_j, D_{j+1}], where v_j =
  VT scale TRAILING-ONLY through D_j (10% ann target, clip 3.0, min 60 obs; same
  formula as R4 engine but FROZEN at decision date so turnover is genuinely weekly —
  no daily VT drift). Strict T+1: first held day is the first trading day AFTER D_j.
  Costs: 6.4bps one-side on FULL |dW| (entry charged) + borrow 0.5%/yr on shorts +
  margin 4.5%/yr on (gross-1) — identical stack to R4/campaign engine.

PRE-REGISTERED CONFIG GRID (complete — no post-hoc cells): {NKY, PROP} x {h1, h5} = 4
configs, each evaluated on (i) its admitted span = full post-warmup history (NKY
pre2007-class span ~1951+; PROP ~1994+ after 512d warmup; span_class printed) and
(ii) champion-window sub-span 2007-03-31..2026-08-31 as a labeled SECONDARY diagnostic
(benchmarks measurable there; on the full 77y span the pinned trio cannot cover >=50%
of the span -> bp fail-closed by design, which I report as such, NOT as alpha absence).

MANDATORY CONTROLS (declared a-priori, same spirit as R4):
  c1 DEAD-FAMILY probe: agreement of pos_j with naive weekly momentum sign(ret[-5d]) —
     if agreement >~0.7 this is a momentum re-test (CLOSED family) and gets reported
     as such regardless of SR.
  c2 gates.run full V2 battery per config per span: sig=held weights, leak_check=True
     EXPLICIT, ref=champion, beats_passive=True + pinned spy/ief/cta trio (V2 6/7);
     scr_p, leak dict, per-benchmark SRs published. gates.run gets r=PER-UNIT net so
     sig*r_pu == held book exactly (contract; verified numerically in TDD).
  c3 halves/neg-year/plateau-by-construction: the grid has no continuous hyperparameter
     (cadence weekly, h in {1,5} both pre-registered); plateau applies to parameter
     grids — reported N/A with the two-point horizon set disclosed.

TDD FIRST (RED before GREEN): tests/test_tfm_r5_tdd.py must exist and fail before
work_r5/ modules exist: T+1 shift exact; truncation no-lookahead (weights byte-identical
when tail removed); PIT of VT freeze (v_j uses returns <= D_j only); sig*r_pu == net to
1e-15; weekly decision = last trading day of ISO week; zero-signal -> flat book; battery
call publishes leak dict + beats_passive block; NKY NaN rows dropped-not-filled.
Expected honest outcome: NEGATIVE (R4 prior); a pass must clear every V2 gate.

====================================================================
## ROUND 5 EXECUTION + RESULTS (2026-09-08 ~09:4x-11:0x CST) — 0/4 configs ADOPTABLE (all FAIL full V2 battery)

TDD: tests/test_tfm_r5_tdd.py RED-first (ModuleNotFoundError on tfm_r5_lib) -> **13/13 GREEN**
(3 test-expectation bugs of mine fixed along the way; 2 REAL library defects found+fixed via
the RED phase: (1) r_pu was UNSIGNED (net/|w|) breaking gates.run's sig*r_pu==net contract
for short weights -> signed net/w; (2) EXIT turnover landed on the flat exit day where sig=0,
so the battery's internal book would silently miss exit costs (fail-open) -> exit cost folded
into last active day, total conserved, identity exact on every day (new test locks it).
Whole-dir regression incl R4 suites: **21 passed**.

Env: /tmp/tfvenv alive, `import timesfm, jax` OK, jax==0.11.1 pin intact. Checkpoint
google/timesfm-2.5-200m-flax (cached from R4). Model compile 28s; throughput ~8.8 fcst/s.

Forecast integrity (files in work_r5/): fcst_r5_NKY.csv 3918 weekly rows 1951-06-01..2026-08-31
(0 NaN, 0 dup, strictly monotone); fcst_r5_PROP.csv 1677 rows 1994-07-22..2026-09-01 (0 NaN).
Context = last 512 log-closes <= D_j INCLUDING D_j (decision at close), horizon 5, one model
call per batch of 256; m1=pt[:,0]-last, m5=pt[:,4]-last. Signal scale sane: NKY m5 std 0.0055
vs realized 5d log-move std 0.0270; corr(m5, real5)=+0.129, corr(m1, real5)=+0.045.
NKY forecasts consumed 19,190 clean quote days (976 holiday rows DROPPED never filled).

FULL V2 BATTERY (gates.run(r=rpu, sig=w, leak_check=True EXPLICIT, beats_passive=True +
pinned trio twelvedata/SPY n=4999 / more_etf/IEF n=6064 / CTA_15vol n=4683, ref=champion
sha 4358dfab95679b97)) — exact numbers (eval_r5_results.json + command output):

  NKY_f1 FULL 1949-2026 n=19190 pre2007: SR 0.0284 (h1 +0.6555/h2 -0.3527), 36 negyr,
    worst -19.74%, ann -0.27%, corr -0.037, scr_p 0.945, leak same_corr -0.0596 leak_ok=True,
    bp_best 0.2801 (sixty_forty) bp_ok=False, agree_naive_mom5 0.549 -> FAIL (sr, halves,
    neg, scr, bp). CHAMPION-WINDOW secondary: SR -0.4439, 15 negyr, scr_p 0.835 -> FAIL.
  NKY_f5 FULL: SR 0.0184 (0.4951/-0.2715), 37 negyr, worst -28.16%, scr_p 0.87, bp fails,
    agree 0.606 -> FAIL. Champ-window SR -0.3845 -> FAIL.
  PROP_f1 FULL 1992-2026 n=8559 pre2007: SR 0.4548 (0.5812/0.3258 — best of grid), 10 negyr,
    ann +4.58%, corr -0.025, scr_p 0.555, leak -0.0321 leak_ok=True, bp_best 0.5643 (spy_bh)
    bp_ok=False, agree 0.599 -> FAIL (sr<1.0, halves<0.5, neg>2, scr, bp).
    Champ-window SR 0.3865 (0.3726/0.4004) -> FAIL.
  PROP_f5 FULL: SR 0.2828 (0.1905/0.3769), 11 negyr, scr_p 0.585, bp fails, agree 0.622 -> FAIL.
    Champ-window SR 0.2776 -> FAIL.

GATE VERDICT: 0/4 pass a SINGLE performance gate; the ONLY gates every config passes are
decorrelation (|corr| 0.019-0.037 < 0.15 — irrelevant when there is no alpha) and leak_ok
(T+1 clean by construction). Best cell PROP_f1 SR 0.455 is below even the retired SR>=0.6
scale (V2 10c relabel discipline) and fails beats-passive (spy_bh 0.564 on matched span).
c1 dead-family probe: dir-agreement with naive 5d momentum 0.549-0.622 — NOT a momentum
re-test (chance-level agreement; the model is not reducing to 'continue last move'), same
novel-but-alpha-less verdict as R4.
Span-discipline note: on the full 77y NKY span the pinned benchmark trio cannot cover >=50%
of the span, so beats_passive reports sixty_forty from partial overlap (0.2801) — reported
as designed fail-closed coverage, NOT treated as alpha absence; the champion-window
secondary rows give measurable benchmarks (0.53/0.58) and fail there too. PROP_f1's full-span
h1/h2 (0.58/0.33) mirrors CMDT2-R5's regime-split pattern (pre/post-2007 propane is a
different market), consistent with their structural-break note.

DEAD_IDEAS.csv: recounted 133 at round start (my 2 R4 rows present, indices 117/118 —
no duplicate registration; rows 125/126 belong to VOL2-R5/SECTOR2-R5). Appended 2 honest
negatives (dedupe-checked): row 133 'TimesFM weekly forecast-direction NKY 77y (h1/h5)' +
row 134 'TimesFM weekly forecast-direction propane spot DPROPANEMBTX (h1/h5)'. Final count
135 (also moved by other agents mid-round: 133->134 during my propane append check).

Evidence archived (V2 10a positions+signal published, 10b vintages pinned in every .meta):
  sleeves/: TIMESFM_R5_{NKY,PROP}_{f1,f5}_daily.csv (+w/rpu/net columns) x4,
            TIMESFM_R5_{key}_signal.csv (decision_date,pos,vt,m) x4, .meta x4
  work_r5/: gen_forecasts_r5.{py,log}, eval_r5.py, eval_r5_results.json, books_r5.csv,
            fcst_r5_NKY.csv, fcst_r5_PROP.csv, tfm_r5_lib.py
  tests/:   test_tfm_r5_tdd.py 13/13 GREEN (RED-first evidence in session log)
Tradeability caveat (declared a-priori): NKY is a cash index (futures 1988+, ETF proxies
2001+), propane a FRED spot index with no direct instrument — corner tests TimesFM zero-shot
SKILL on the new spans; adoptability would additionally need instrument mapping. Moot: no
alpha anywhere on the grid.

ROUND 5 VERDICT: 0/4 adoptable. TimesFM 2.5-200m zero-shot forecast-direction carries NO
post-cost alpha at weekly cadence on the two NEW 2026-09-08 spans (NKY 77y n=19190;
propane 1992+ n=8559) under the full V2 battery (leak-probe + beats-passive + scramble all
published, all fail honestly). Frontier UNCHANGED: champion ann 37.195% / SR 3.181 stands.
R4 generalization holds on the new spans: zero-shot point forecasts are novel signal
generators without economic alpha.

ROUND 5 DONE


====================================================================
## ROUND 6 (2026-09-08 ~17:2x-18:1x CST) — CONSOLIDATION: env preserved, 2 fraud-catch reproductions CLEAN, 4 DEAD_IDEAS rows verified

Round-6 start state honesty note: a prior launcher incarnation of THIS round (16:47-17:24
today) had already drafted work_r6/env_note.md + fraudcatch_r6.py (no FINDINGS entry, no
results). I ADOPTED the env_note (every claim re-verified fresh this session — pins, cache
size, snapshot hash all exact) and REWROTE the fraud-catch harness RED-first; the draft's
bugs are enumerated below as TDD catches.

### (a) Environment preservation (charter item a) — DECLARED EPHEMERAL-WITH-PROVEN-RECIPE
work_r6/env_note.md (adopted, claims re-verified this session):
  * /tmp/tfvenv FUNCTIONAL: python 3.14.7, timesfm 3.0.1, jax 0.11.1 + jaxlib 0.11.1
    (charter pin intact), flax 0.12.9, optax 0.2.8, einshape 1.0, orbax-checkpoint 0.12.4
    (R4 fix still in), huggingface_hub 1.30.0, pandas 3.0.5, numpy 2.5.3 — all re-read
    fresh via pip list this session.
  * Checkpoint cache ~/.cache/huggingface/hub/models--google--timesfm-2.5-200m-flax:
    818 MB (du -sh), snapshot b99e9f6c457ee0d14d563e4800cb63e239ffeda0 (refs/main read
    directly) — SAME commit as the R4 download. PERSISTENT (home dir, not /tmp).
  * DECLARATION: cache PERSISTENT-HEALTHY; venv EPHEMERAL-BY-LOCATION but rebuildable in
    ~5-10 min via the charter ENV block + `pip install -U orbax-checkpoint` (that step is
    NOT in the charter block and is REQUIRED — the R4 ModuleNotFoundError fix). Family
    CLOSED 0/8: NO new model corners, no further env spend. The two proven driver scripts
    (work_r4/gen_forecasts.py, work_r5/gen_forecasts_r5.py) + this note are the full
    preservation artifact.

### (b) FRAUD-CATCH (charter item b) — BOTH R5 verdicts REPRODUCE; ZERO fraud, ZERO material divergence
Harness: work_r6/fraudcatch_r6.py — MY OWN engine+metrics, NOTHING imported from the two
target agents; my sr/halves/neg-years cross-checked == bt.metrics to 1e-12
(tests/test_fraudcatch_r6.py). TDD: suite extended with 4 RED spec tests (expanding-VT ==
bt.engine, release->T+1 mapping, break-segmented PIT z, MOM_252_LF structural start) ->
**33/33 GREEN** (RED-first evidence: 5 failed -> 33 passed in this session's log).

leg1 ARTIFACT SCORING (12 published books scored with my metrics vs claimed; log
work_r6/leg1_scored_r6.log, table leg1_scored_r6.csv):
  * INTL2 9 books: |dSR| <= 0.0004 (MOM_252_LF 0.7354 vs claim 0.7354; SELLMAY 0.5350 vs
    0.535; TOY_dates 0.2669 vs 0.267; TOM_rank3 0.3691 vs 0.369). neg-years match exactly
    on 5/9; 4 INTL2 books differ by 1-3 calendar years (my calendar-year product vs their
    bucketing — MOM_126 34 vs 32, TOM_dates 27 vs 24, TOM_rank3 29 vs 28, TOY_dates 32 vs
    31); halves d <= 0.105. NON-VERDICT-CHANGING: every book fails SR>=1.0/halves/negyr
    under BOTH number sets.
  * COT2 3 books (C1/C3/C9): |dSR| <= 0.0004 (C9 0.5898 vs 0.590, halves 0.788/0.554 —
    exact to 3 decimals), negyr 6/3/3 all exact.

leg2 RAW REBUILD (my own engine from raw source data vs published books; leg2_rebuilds_r6.csv):
  * INTL2 4/4 configs: corr 1.0000, |dSR| <= 0.0001, identical n and start dates —
    MOM_252_LF corr 1.0000 dSR -0.0001 n=18788 start 1950-12-15 BOTH; CAL_SELLMAY,
    CAL_TOM_dates, CAL_TOY_dates likewise EXACT. This is a full independent reproduction:
    my own expanding-VT, my own net_book, their published config spec.
  * COT2 3/3 configs: C9 corr 1.0000 dSR 0.0000 (EXACT); C1 corr 0.9990 dSR +0.0025;
    C3 corr 0.9998 dSR -0.0021. Reaching exact required reproducing the published spec
    exactly, which I verified piecewise: (i) z source = panel's own z column (corr 1.0,
    maxdiff 0.0 vs my fresh re-derivation on gold/jpy/sp500 — the column IS a fresh PIT
    expanding z min26 ddof0), break families (nat_gas, lumber) ALWAYS re-derived
    segmented (panel z stitched-column never read); (ii) legs LIVE FROM FIRST RELEASE
    onward (gate-off days contribute 0.0 to the cross-leg mean, not NaN); (iii) Dealer_Long
    exists for exactly 10 FIN families (crude/nat_gas/copper/gold/silver have empty
    Dealer_Long z -> dropped, matching "families used 10"); (iv) EWMA vt63/min20 on the
    mean book, trim to first live leg. Residual C1/C3 deltas are rounding-scale.
leg3 VERDICT (my rebuilds, my gates): COT2 C1 SR +0.2456 h1 .334/h2 .211 negyr 6 -> FAIL;
  C3 +0.3326 negyr 3 -> FAIL; C9 +0.5898 h1 .788/h2 .554 negyr 3 worst -13.74% -> FAIL.
  INTL2 MOM_252_LF SR +0.7353, pre-1990 +1.2089 vs post-1990 +0.2573, negyr 22 -> FAIL,
  and the STRUCTURAL finding reproduces exactly (pre-1990-only effect); SELLMAY +0.5351
  (pre .946/post .252), TOM_dates +0.4021 (.734/.175), TOY_dates +0.2670 (.341/.202) all
  FAIL. Shared-battery cross-check: my C9 rebuild through campaign bt.gates.run (sig/rpu
  consistent feed, leak_check=True, ref=champion 4358dfab95679b97) -> sr 0.5796 sr_ok
  False, neg_ok False (3), scr_p 0.585, pass=False — same verdict as the R5 record.
FRAUD-CATCH VERDICT: both targets' R5 verdicts reproduce from published artifacts AND from
raw source data with my own code; the two defects I hit while reproducing were MINE
(documented TDD catches below), not theirs. No divergence to escalate.

### TDD catches this round (all MINE, all fixed, RED-first)
1. draft scramble_p indexed ['net'] on an already-renamed Series (DateParseError) —
   caught by the pre-existing failing test; rewritten to the circular-shift position null.
2. Wrong VT convention for INTL2 in the draft (EWMA) vs their actual bt expanding spec —
   caught by test_my_expanding_vt_matches_bt_engine; my implementation now == bt.engine
   (assert_series_equal exact).
3. COT2 rebuild spec deviations (found by rebuild-mismatch diagnosis, then verified
   piecewise against their published spec): break-first z precedence + live-from-first-
   release leg masking (deviation effects measured: live-mask alone swung C1 SR -0.196,
   both fixes together -> corr >= 0.999).
4. z column name bug (z_cnt_* vs z_Traders_*) — caught by CSV usecols ValueError.
5. Two weak test FIXTURES of mine (random-walk weights drown in turnover cost; returns
   passed where engine takes prices) — fixed the fixtures, not the module.

### (c) DEAD_IDEAS curation (charter item c)
Recounted MYSELF this session via csv module: **145 data rows** + header (146 file lines
with trailing newline; charter said 137 at R5-end — the file is dynamic, other agents
appended 8 rows since). My 4
rows PRESENT (file lines 128-131), verified verbatim + all repro paths resolve on disk:
work_r4/{run_a_r4.log, run_b_r4.log, diag_kill_r4.log, diag_kill_r4b.log, gen_forecasts.py},
work_r5/{gen_forecasts_r5.py, gen_forecasts_r5.log, eval_r5.py, eval_r5_results.json,
fcst_r5_NKY.csv, fcst_r5_PROP.csv}, sleeves/TIMESFM_{DIR_EW6,MAG_OVL,R5_NKY_f1,R5_NKY_f5,
R5_PROP_f1,R5_PROP_f5}_* with .meta/.csv.meta, tests/test_tfm_{engine_tdd_r4,overlay_tdd_r4,
r5_tdd}.py. No duplicate TIMESFM registrations. No new rows needed (R6 generated no new
strategy attempts — consolidation round). NO edits to DEAD_IDEAS.csv made or needed.

### Champion untouched
campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha256[:16] re-read this
session = 4358dfab95679b97 (matches charter of record). Nothing in bt/, campaign/*.md, or
any other agent's directory modified; targets read READ-ONLY.

ROUND 6 VERDICT: family CLOSED 0/8 confirmed; env declared EPHEMERAL-WITH-PROVEN-RECIPE
(cache persistent); both fraud-catch targets reproduce CLEAN (12/12 published books score
true to <=0.0004 SR; 7/7 raw rebuilds corr >= 0.999, 4/4 INTL2 exact); 4 DEAD_IDEAS rows
verified with working repro paths. Zero fraud found. Frontier UNCHANGED (champion ann
37.195% / SR 3.181 / MDD -6.69%).

ROUND 6 DONE

## ROUND 7 (2026-09-09 ~00:1x CST) - own-code AUDIT of DATA_COTMORE trader-count panel; env re-probe; curation. No TimesFM re-test (family CLOSED)

Charter R7 items: (a) audit DATA_COTMORE panel + ledger with MY OWN code, (b) no TimesFM
re-test + env honesty, (c) curate my 4 DEAD_IDEAS rows. Corner pre-registered here first:
reproduce the 29,051x51x35 panel from the RAW CFTC zips with an independent parser
(content-dispatching date normalizer - the 2010 zips' MM_DD_YYYY label lies, content is
ISO), independent duplicate/collision resolution, own source-name boundary detector +
|d|>=30% EXN gate, own PIT-expanding-z re-derivation, then full-cell diff vs the
committed CSV. Only shared code: tools/quant/data/more_cot/cot_matcher.py (campaign
infra). Their builder/lint/test files were read to LEARN semantics, never imported.
Evidence: work_r7/r7_cotmore_audit.py + r7_cotmore_audit.log (exit 0, ALL PASS),
work_r7/env_note.md. Zero gates.run calls (data-only round). bt/, campaign/*.md,
champion, and every other agent's directory untouched; reads READ-ONLY.

### (a) Panel audit - ALL PASS, every number below from my own code this session

- Recount from disk: sha16 9e2c82303acf4c24 (byte-match to MANIFEST_R5 pin), 29,051 data
  rows x 51 header cols (width census {51: 29051} - 0 malformed), 35 families, span
  2010-01-05..2026-09-01, 0 dup (family,report_date) keys, trailing newline intact.
- Own-code rebuild from raw: 34 canonical zips parsed (2 sep3.baks excluded), 29,244
  matched raw rows -> 29,051 after my own duplicate (newer as_of wins) + rename-collision
  (matcher priority wins) resolution - key set IDENTICAL to the panel's (0 panel-only,
  0 mine-only). All 697,224 cnt_* + open_interest cells: 0 mismatches.
- PIT expanding-z re-derivation (min_periods=26 counted as NON-BLANK obs, ddof=0,
  sd==0->0.0): max abs dev 3.375e-14 over 384,805 non-blank z cells.
- EXN break gates FAIL-CLOSED, asserted programmatically: my boundary detector walked
  18 real source-name transitions across 35 families and fired EXACTLY 2 -
  nat_gas_nymex 2022-02-08 Traders_Tot_All 281->40 (-85.77%, rounds to the claimed -86%)
  and lumber 2023-04-25 21->43 (+104.76%, claimed +105%). Set equality with the two
  charter-named EXNs held; the other 33 families measured quiet.
- eurodollar_3m: n=674, last report_date 2023-06-13 - unchanged.

NEW measured finding (disclosure, not a defect): 8 same-name weekly |dTotAll|>=30% jumps
exist that the rename-seam gate BY DESIGN cannot see (gate contract = "source-name
transition + count discontinuity"). 7 of 8 have exactly 1 raw row at that (family,date)
-> the jump is IN the CFTC source file (e.g. jpy 2011-08-09 112->76 -32.1%, lumber
2020-03-03 COVID -31.6%, eurodollar_3m 2023-04-18 sunset -32.7%, rough_rice 2019-02-19
+30.4%). The 8th, lumber 2023-04-18, is the rename seam itself: BOTH names appear in the
same raw file with the same as_of (RANDOM LENGTH LUMBER 21 / LUMBER 35, as_of 230418);
the panel resolves to the old-name 21 by matcher priority. Measured: under the OPPOSITE
priority the 04-25 lumber seam would read 35->43 = +23% and the EXN would NOT fire - the
shipped priority is the fail-closed direction. Downstream users should keep the FINDINGS
limit: use nat_gas/lumber z within-segment (or drop seam weeks); same-name >=30% weekly
jumps exist in 6 families and are source-truth, not stitching.

My own bugs hit while auditing (all MINE, all fixed RED-first in my own script; ZERO in
their code): (1) panel cnt cells are float-formatted ('23.0') where columns ever held NaN
(pandas upcast) -> int() ValueError; (2) checked newline with b'\\n' (2-byte backslash
escape, always False) instead of bytes([10]); (3) expanding-z warmup keyed on row index
vs pandas' non-NaN observation count -> false inf deviation; (4) z source col needs the
'cnt_' prefix (KeyError: 'Traders_Tot_All'); (5) two dead draft blocks removed before
final run. Final script exit 0.

### (b) Env honesty - re-probed READ-ONLY, no rebuild, no model run

/tmp/tfvenv/bin/python import probe -> OK, jax 0.11.1 (venv mtime Sep 7 17:50, unchanged
since R6's probe); HF cache models--google--timesfm-2.5-200m-flax present, 818 MB, mtime
Sep 7 21:30 unchanged; pytorch repo still not cached; gated 3.0/2.0 repos not attempted.
Declaration re-confirmed: cache PERSISTENT, venv EPHEMERAL-WITH-PROVEN-RECIPE (rebuild
recipe incl. the orbax-checkpoint extra step in work_r6/env_note.md). Family CLOSED 0/8
stands; NO new model corners, no downloads, no forecasts this round. Full note:
work_r7/env_note.md.

### (c) DEAD_IDEAS curation - recount 152; rows 135-137 verified; my 4 rows intact; no edits

Recounted with csv.DictReader this session: **152 data rows** (charter said 145-146 at
R6-end; +6 R7-tagged appends landed concurrently per design), ledger sha16 at read
d6873418ffa0da5e, 0 malformed rows, 0 byte-dup (idea,source) pairs, trailing newline
intact. Status census: 128 dead / 7 blocked / 4 data-acquired / 3 R2 dead / 2 R3 dead /
1 dead/NOT-ADOPTED / 1 'dead (adoption REJECTED on 8c / R7-audited)' / 6 verified.
Rows 135-137 (COT2-R6 trio) verified verbatim-in-content against HUNT_COT2's published
FINDINGS (all substantive claims present: 72/72 field-exact, scramble p=0.185,
held-book 28/28 FAIL, supplement-of-line-126/129 pointers) and all cited repro paths
resolve on disk (HUNT_COT2/verify_r6_cmdt2.csv, verify_r6_credit2.csv, r6/rerun_credit2_r5.py).
My 4 rows intact at file lines 128-131 (statuses dead / dead+NOT-ADOPTED / dead / dead);
all 15 cited repro paths resolve (work_r4 logs+gen_forecasts.py, work_r5 scripts+logs+
fcst CSVs, sleeves/ 6 sleeve CSVs + 5 .meta, tests/ 3 test files) and the 3 repro test
files re-ran green this session: 21 passed in 2.01s. One citation correction to MY OWN R6
prose (not the ledger, whose cells carry numbers not paths): the overlay test file is
tests/test_overlay_tdd_r4.py, not 'test_tfm_overlay_tdd_r4.py' as my R6 FINDINGS wrote.
No DEAD_IDEAS rows appended (no real defect surfaced - my R6 consolidation precedent
holds); no edits to any shared file.

### Verdict

Charter items (a)(b)(c) ALL PASS. Zero fraud found in the COTMORE panel: 697,224 data
cells + 384,805 z cells reproduce from raw to <=3.4e-14; EXN gates fail-closed on exactly
the 2 sanctioned exceptions with claimed magnitudes (-86%/+105% reproduce at
-85.77%/+104.76%). Champion of record untouched (ann 37.1954 pct / SR 3.1810 / MDD
-6.6922 pct / n=4805 / sha 4358dfab95679b97, coordinator-pinned 18:3x). Honest frontier
UNCHANGED (37.2 vs 80 goal). TimesFM family stays CLOSED.

ROUND 7 DONE
