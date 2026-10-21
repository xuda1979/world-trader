# HUNT_CBOE_IV R8 - FINDINGS (CBOE historical vol surface)

Agent HUNT_CBOE_IV, round 8. Repo root /Users/daxu/software/world-trader.
Pre-registration written BEFORE any result: `work_r8/PRE_REGISTRATION.md`.
Engine: `work_r8/r8_engine.py`. Coverage: `work_r8/r8_coverage.{json,csv}`.
All numbers below are reproducible from those files (commands in section 10).

## 0. TL;DR - ALL THREE CANDIDATES REJECT (clean negative)

| candidate | corner | span | hand | n | SR | ann | MDD | neg yr | cost bp/yr | gross | corr champ | corr A5r2 | best-rung dAnn | V2 verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1_VOLBACK | back-end slope+curvature (VIX3M/VIX6M) | 2009-12-17..2026-08-28 | PREREG | 4042 | 0.0144 | -0.13% | -20.16% | 5 | 94.7 | 0.114 | -0.0515 | +0.3062 | -1.031pp | **REJECT** |
| C1_VOLBACK | best of 144 cells (L21/t0.5/slope, contango sign) | 2009-10-19..2026-08-28 | BESTCELL | 4083 | 0.6382 | +3.10% | -13.75% | - | - | - | +0.0023 | +0.4205 | -0.930pp | **REJECT** |
| C2_VRP | VIX minus Parkinson RV (SPX OHLC) | 2008-04-01..2026-08-28 | PREREG | 4462 | 0.0441 | +0.06% | -23.71% | 6 | 75.2 | 0.123 | -0.0747 | +0.3912 | -1.100pp | **REJECT** |
| C2_VRP | best of 72 cells (rv63/z63/t0, flip) | 2008-04-01..2026-08-28 | BESTCELL | 4462 | 0.3120 | +1.21% | -18.65% | - | - | - | -0.0047 | +0.5374 | -1.067pp | **REJECT** |
| C3_VOLDISP | IV dispersion VIX/GVZ/OVX | 2010-03-22..2026-08-28 | PREREG | 3983 | 0.3917 | +2.81% | -21.77% | 2 | 119.2 | 0.317 | -0.1067 | +0.5163 | -0.936pp | **REJECT** |
| C3_VOLDISP | best of 36 cells (z252/t0.5, flip) | 2010-09-20..2026-08-28 | BESTCELL | 3861 | 0.5313 | +3.73% | -15.01% | - | - | - | +0.0310 | +0.5956 | -0.917pp | **REJECT** |

**252 grid cells were evaluated in total across the three corners and ZERO reached the
contract SR bar of 1.0** (best single cell 0.6382). No candidate is close. Every candidate
also breaches the -7% MDD wall standalone and fails the signal-scramble gate.

Champion of record re-verified this session from disk:
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`
sha256 `8d7e711e6d05a2b1b77f06f18d850a90159924dd3df975a4f49bd407ad8fd079` (EXACT match to
the pinned hash), n=4806, SR 3.1951, ann 37.4923%, MDD -6.6922%. Champion untouched.

## 1. Data inspection first - honest coverage (V2 section 9a span_class)

Classified by VALUE, not filename (method in `r8_data_inspect.py`). All 46 files end
2026-09-09, i.e. PAST the champion's 2026-08-28.

**Confirmed option/volatility STATISTICS** (no tradeable volume; VIX-like band):
VIX 1990-01-02 (n=9269) | VVIX 2006-03-06 (n=5100, pre2007) | VIX6M 2008-01-02 (n=4701) |
VIX3M 2009-09-18 (n=4269) | GVZ 2009-09-18 (n=4267) | OVX 2009-09-18 (n=4267).

**Confirmed UNDERLYING PRICES** (real OHLCV): SPX 1975-01-02 (n=13030) | OEX 1983-03-11
(n=10953) | DJX 1997-09-29 (n=7281) | DIA/EEM/EFA/IEF/IWM/QQQ/SHY/SMH/SPY/TLT/TSM and
XLB/XLE/XLF/XLI/XLK/XLP/XLU/XLV/XLY all 2004-01-01..02 | VNQ 2004-09-29 | FXI 2004-10-08 |
GLD 2004-11-18 | SLV 2006-11-01 | HYG/JNK/EMB 2008-02-11 (2007plus).

**inception_fail - NOT hunt-eligible (V2 9a):** KWEB 2013-08-01, **RUT 2020-11-27**
(only 1451 rows - the file is NOT the long RUT index history), **VIX1D 2022-05-13** (n=1084).
No candidate was built on any of these. VIX1D was expected to be short and it is; it is
reported as a diagnostic only and is NOT used in any sleeve.

**Anomalies / honesty notes:**
- `LQD` and `VNQ` each carry a 306-CALENDAR-DAY interior gap (max_gap column of
  r8_coverage.csv); VVIX has a 21-day gap. I did not use these series as legs.
- SPX / OEX / DJX / VIX3M / VIX6M / VVIX / OVX carry a `volume` column that is
  identically 0. For the vol indices that zero-volume signature is itself corroborating
  evidence they are statistics, not traded prices.
- My value heuristic misclassified **OVX as price-like** because its close reached 325.15
  (oil vol spiked there in 2020). OVX IS a volatility statistic; the label in
  r8_coverage.csv is wrong on that one file and I flag it rather than let it stand.
- **The binding span limit for corners C1 and C3 is VIX3M / GVZ / OVX, all of which start
  2009-09-18.** There is no earlier back-end or cross-asset implied-vol history in this
  vintage. That forces the pre-2010 stability verdict to UNJUDGEABLE for C1/C3 (section 7).

## 2. What I built

Three PRE-REGISTERED corners (fixed before results, see PRE_REGISTRATION.md section 1),
each an SPX long/flat book, T+1 (`sig = pos.shift(1)`), 10% ann trailing-only vol target
(bt.engine.vol_target_scale, clip<=3), costed at 6.4bps one-side on FULL |dW| with the
day-1 establishment charged, gross clipped at 1.0 (unlevered). Long/flat only, so no borrow.

- **C1_VOLBACK** `back = VIX3M/VIX6M - 1`, `curv = VIX6M - 2*VIX3M + VIX`,
  `score = z(back,L) + z(curv,L)`. Grid L in {21,63,126,252} x thr in {0.5,1.0,1.5} x
  kind in {both,slope,curv}.
- **C2_VRP** `vrp = VIX - ParkinsonRV(SPX high/low, rv_win)`, `z(vrp,z_win)`.
  Grid rv_win in {10,21,63} x z_win in {63,252} x thr in {0.0,0.5,1.0}.
- **C3_VOLDISP** cross-sectional std of the trailing z-scores of {VIX, GVZ, OVX};
  long while dispersion <= thr. Grid z_win in {63,126,252} x thr in {0.5,1.0,1.5}.

**DISCLOSED SIGN AMBIGUITY IN MY OWN PRE-REGISTRATION.** I wrote C1 as "risk-on when the
back end is in contango", but defined the slope as `VIX3M/VIX6M - 1`, which is NEGATIVE in
the normal upward-sloping curve. Back-end contango is therefore the LOW-slope state, so the
economically-correct sign is the OPPOSITE of the as-written gate. Rather than quietly flip
it, I ran BOTH signs as a disclosed 2x expansion (variants PREREG / FLIP, plus continuous
`clip(score,0,1)` variants LIN_ASWRITTEN / LIN_FLIP). **All four variants x the whole grid
are reported in r8_results.json; nothing is hidden and nothing is cherry-picked.** The
outcome does not depend on the choice: under PREREG C1 has SR 0.0144; under FLIP its best
cell reaches only 0.6382. Neither is close to 1.0.


## 3. V2 gate verdict - PER CANDIDATE (all on the candidate's OWN admitted span)

`bt.gates.run(r=per-unit SPX returns, ref=champion, sig=positions, leak_check=True,
beats_passive=True, spy=,ief=,cta=)`. NOTE ON CONVENTION: gates.run judges the book
`sig*r`, which is GROSS of cost, so the gates `sr` printed below is the gross-book SR. The
contract bar (v1 section 3a) is the **net** SR, which I compute separately on the cost-charged
series. Both are shown; the binding number is the net one. (A contemporary R7 hunter script
passes `book_gross` as `r`, which double-applies the position - r_eff = sig^2*r; I did not
copy that.)

| gate | C1 PREREG | C2 PREREG | C3 PREREG | bar |
|---|---|---|---|---|
| net SR | **0.0144** FAIL | **0.0441** FAIL | **0.3917** FAIL | >= 1.0 |
| gates gross-book SR | 0.155 | 0.153 | 0.543 | - |
| halves H1/H2 | 0.290 / 0.036 FAIL | 0.173 / 0.132 FAIL | 0.897 / 0.203 FAIL | both >= 0.5 |
| neg years (worst) | 5 (-12.61%) FAIL | 6 (-18.32%) FAIL | 2 (-6.17%) pass | <= 2, floor -5% |
| MDD | -20.16% FAIL | -23.71% FAIL | -21.77% FAIL | >= -7% |
| ac1 | -0.235 pass | -0.180 pass | -0.177 pass | < 0.5 |
| uniq | 0.179 pass | 0.271 pass | 0.520 pass | >= 0.08 |
| corr to champion | -0.0507 pass | -0.0743 pass | -0.1066 pass | abs < 0.15 |
| scramble p (200x) | 0.790 FAIL | 0.800 FAIL | 0.590 FAIL | < 0.05 |
| leak_ok | True pass | True pass | True pass | required |
| beats_passive | FAIL (margin -0.678) | FAIL (-0.480) | FAIL (-0.297) | > 0 |
| **gates.run composite pass** | **False** | **False** | **False** | |

beats_passive detail (best passive on each matched span is always `sixty_forty`):
C1 spy_bh 0.789 / sixty_forty 0.833 / cta_trend -0.084;
C2 spy_bh 0.601 / sixty_forty 0.633 / cta_trend -0.074;
C3 spy_bh 0.795 / sixty_forty 0.840 / cta_trend -0.069.

**The single `beats_passive_ok=True` in the whole round is C1's BESTCELL (margin +0.109
vs sixty_forty 0.831) - and it is a GROSS-of-cost artefact.** On the net series that same
cell is SR 0.6382 vs the 0.831 benchmark, i.e. it FAILS by -0.19. It is also one cell out
of 252 after a 4-way sign/mode expansion, so it is not evidence of anything.

## 4. Overlay / champion-blend gate (V2 section 8) - ALL FAIL, and WHY

Ladder run through the RATIFIED reference implementation
`coord/HUNT_VOL2/work_r3/blend_r3_lib.py` (`blend_metrics` + `gates_for`): charter weight
convention w = SLEEVE slice, champion gets (1-w); rebalance-drift turnover charged at 6.4bps
FULL |dW|; margin re-priced on blended gross-1.

| ladder (PREREG) | w=2.5% | w=5% | w=7.5% | w=10% | w=15% |
|---|---|---|---|---|---|
| C1 dAnn (pp) | -1.031 | -2.056 | -3.074 | -4.085 | -6.087 |
| C1 dSR | +0.0023 | +0.0037 | +0.0041 | +0.0034 | -0.0025 |
| C2 dAnn (pp) | -1.100 | -2.193 | -3.278 | -4.355 | -6.487 |
| C2 dSR | +0.0041 | +0.0075 | +0.0099 | +0.0112 | +0.0096 |
| C3 dAnn (pp) | -0.936 | -1.867 | -2.793 | -3.713 | -5.539 |
| C3 dSR | +0.0135 | +0.0264 | +0.0386 | +0.0498 | +0.0683 |

`gates_for` verdicts: C1_PRIMARY **FAIL**, C1_BESTCELL **FAIL**, C2_PRIMARY **FAIL**,
C2_BESTCELL **FAIL**, C3_PRIMARY **FAIL**, C3_BESTCELL **FAIL**. `any_pass=False`,
`plateau=False` on every one. Blocking reason on all six: **8c dAnn > 0 is never met at any
rung** (best over everything = -0.917pp at w=2.5%), which also kills 8d (dSR>=0 holds
marginally but dH1<0 for C1/C2) and the plateau block.

**STRUCTURAL FINDING (this is the real content of the round).** The blend is a constant-mix
capital split, so to first order `dAnn ~= w * (ann_sleeve - ann_champion)`. The champion's
ann is **37.49%**; the best standalone sleeve I or anyone can build from this data is
~3.7% ann. Therefore `dAnn < 0` for EVERY w > 0, no matter how good the sleeve's Sharpe is.
This is arithmetic, not a property of the CBOE corners - it is exactly why ledger row 96
records "dAnn>0 needs w<0", and why VOL2-R3 (0/6), CRYPTO2-R3 (0/34) and SECTOR2-R3 all
failed the same way. **The champion-overlay track is closed to any low-ann sleeve.** A
CBOE vol sleeve would have to earn ~37%+ unlevered to clear 8c; nothing in this family does.

Note C3 does deliver the only MDD relief of the round (dMDD +0.136pp at w=2.5% rising to
+0.817pp at w=15%) and its delta halves are both positive - i.e. it is a genuinely
diversifying, mildly risk-reducing sleeve. It still dies on 8c. I record that plainly
rather than dress it up: **a low-corr sleeve with negative dAnn is a REJECT.**

**Placebo (V2.1 section 14) NOT run, deliberately.** Routing would be Class B
(all |corr to champion| < 0.11). Section 14c/14d are explicit that the placebo is a
NECESSARY-condition instrument that can never upgrade a candidate and that adoption still
requires 8c. Since 8c fails at every rung for every candidate, the B1 null cannot change
any verdict, so spending 200 block-bootstrap draws on it would be theatre.

## 5. Relation to A5r2 - the mandated caution (and it bites)

A5r2 = `A5_vol_cond/A5_r2_contango_rateshock.csv` is **already a VIX/VIX3M contango long-SPY
sleeve** (rule: long SPY while VIX/VIX3M < 1.02, flat when a 10y rate shock is on; vol
target 10%; window 2009-09-16..2026-08-11, the VIX3M constraint). Champion relw 0.864.
Re-measured this session: n=4249, **SR 1.0192, ann 8.9627%, MDD -12.7987%, corr to champion
+0.0248**.

My candidates are NOT orthogonal to it, and I say so plainly:

| candidate | corr to A5r2 |
|---|---|
| C1 PREREG | +0.3062 |
| C1 BESTCELL | +0.4205 |
| C2 PREREG | +0.3912 |
| C2 BESTCELL | +0.5374 |
| C3 PREREG | +0.5163 |
| C3 BESTCELL | +0.5956 |

C1 is the sharpest case: its winning sign is the contango sign, and its best cell is a
weaker re-expression of exactly the trade A5r2 already harvests at SR 1.02 - my version
gets 0.64 with a 0.42 correlation to it. **The 3M/6M back end adds nothing beyond the
front-end contango already in the champion.** C3 (dispersion) is the most correlated of all
(0.52-0.60) so it is largely the same risk factor re-labelled. This is a substantive
negative finding, not just a failed gate.


## 6. Leak probe (bt.leakcheck) - ALL CLEAN

Scalar probe of the candidate's positions against same-period SPX returns:

| candidate | same_period_corr | same_period_p | lag-0 | lag -1 (argmax) | leak verdict | n |
|---|---|---|---|---|---|---|
| C1 | -0.00748 | 0.634 | -0.0075 | -0.1721 | **False** (clean) | 4042 |
| C2 | -0.00644 | 0.667 | -0.0064 | -0.1212 | **False** (clean) | 4462 |
| C3 | -0.00124 | 0.937 | -0.0012 | +0.0365 | **False** (clean) | 3983 |

Same-period correlation is ~0 for all three (|corr| <= 0.0075 vs the 0.20 materiality
threshold), lag 0 is NOT the profile peak (lag -1 dominates, as it must for a causal book),
and `gates.run(..., leak_check=True)` reported `leak_ok=True` on every candidate. The
candidates are causally built and the framework agrees. This is the one thing that is
clean in this round; everything else is a negative.

## 7. Stability table (MANDATORY pre/post-2010 and IS/OOS)

| candidate | pre-2010 | post-2010 | IS (<2017) | OOS (>=2017) |
|---|---|---|---|---|
| C1 PREREG | **n=9 UNJUDGEABLE** | SR 0.0144, ann -0.13%, MDD -20.16%, 5 neg | SR 0.0431, ann +0.07% | SR -0.0055, ann -0.28% |
| C2 PREREG | SR **-0.4546**, ann -6.24%, n=429 | SR 0.1561, ann +0.76%, MDD -23.71%, 5 neg | SR 0.0242, ann -0.09% | SR 0.0648, ann +0.21% |
| C3 PREREG | **n=0 UNJUDGEABLE** | SR 0.3917, ann +2.81%, MDD -21.77%, 2 neg | SR 0.4889, ann +3.67% | SR 0.3206, ann +2.21% |

Honest reading:
- **C1 and C3 CANNOT be judged pre-2010** - VIX3M/GVZ/OVX simply do not exist before
  2009-09-18 in this vintage, so the pre-2010 cell is empty by construction, not by
  selection. I report UNJUDGEABLE rather than pretending either way. Their IS/OOS split is
  the substitute and it shows no stable edge: C1 is ~0 in both halves; C3 decays from
  0.489 IS to 0.321 OOS.
- **C2 is the only corner with a real pre-2010 sample, and it is NEGATIVE there**
  (SR -0.4546, ann -6.24% over n=429). Its entire weak positive is post-2010 and it is
  still only SR 0.16. Under the charter rule that an effect concentrated outside the early
  sample is a FAIL, C2 fails on stability as well as on level.
- None of the three shows a stable, era-robust edge. There is nothing to rescue here.

## 8. Honest conclusion - ADOPT / REJECT / UNJUDGEABLE

- **C1_VOLBACK (vol-curve back end 3M/6M, slope + curvature): REJECT.**
  Best of 144 cells SR 0.6382 << 1.0; pre-registered cell SR 0.0144; every ladder rung
  dAnn negative (best -0.930pp); corr to A5r2 0.31-0.42, i.e. a weaker re-run of the
  contango trade the champion already holds. Also UNJUDGEABLE pre-2010 (no data).
- **C2_VRP (VIX minus Parkinson realized vol): REJECT.**
  Pre-registered SR 0.0441, best of 72 cells 0.312; negative pre-2010 (-0.4546); every
  ladder rung dAnn negative (best -1.067pp).
- **C3_VOLDISP (cross-asset implied-vol dispersion VIX/GVZ/OVX): REJECT.**
  Pre-registered SR 0.3917, best of 36 cells 0.5313; corr to A5r2 0.52-0.60 (largely the
  same factor); delivers the round's only MDD relief (dMDD +0.136..+0.817pp) but dAnn is
  negative at every rung (best -0.917pp), so it fails the 8c HARD gate. Also UNJUDGEABLE
  pre-2010 (no GVZ/OVX before 2009-09-18).

**No candidate is ADOPT. No candidate is UNJUDGEABLE-eligible-as-a-sleeve** (all three have
admissible spans and were fully measured; the UNJUDGEABLE element is strictly the pre-2010
stability cell for C1/C3). Nothing was submitted, the champion was not touched, and no
target was tuned toward.

### DEAD_IDEAS row text for the coordinator

```
CBOE historical vol surface 1990-2026: back-end term structure (VIX3M/VIX6M slope+curvature),
variance risk premium (VIX - Parkinson RV from official SPX OHLC), and 3-asset implied-vol
dispersion (VIX/GVZ/OVX),dead,"252 cells (3 corners x pre-registered grids x 4 disclosed
sign/mode variants), 0 reach SR>=1.0 (best 0.638 C1_L21_t05_slope FLIP). PREREG cells:
C1 SR 0.0144 ann -0.13% cost 94.7bp/yr; C2 SR 0.0441 ann +0.06%; C3 SR 0.3917 ann +2.81%.
All leak_ok=True (same-period corr -0.0075/-0.0064/-0.0012). Ladder via ratified
HUNT_VOL2/work_r3/blend_r3_lib: dAnn NEGATIVE at every rung for all 6 (PREREG+BESTCELL)
objects, best -0.917pp; gates_for FAIL x6. NOT orthogonal to A5r2 (corr +0.31..+0.60):
C1's winning sign is the contango sign and is a weaker re-run of A5r2 (SR 1.02) - the 3M/6M
back end adds nothing. STRUCTURAL: dAnn~=w*(ann_sleeve-ann_champ) with champ ann 37.49% vs
best sleeve ann 3.7% => overlay adoption arithmetically unreachable for any low-ann sleeve
(reproduces ledger row 96 'dAnn>0 needs w<0'). Span limits: VIX3M/GVZ/OVX all start
2009-09-18 so pre-2010 stability UNJUDGEABLE for C1/C3 (no pre-2010 data exists); C2 IS the
only pre-2010 sample and is NEGATIVE (SR -0.4546 n=429). VIX1D 2022-05-13 and RUT
2020-11-27 are inception_fail (V2 9a), not hunt-eligible. Champion untouched sha
8d7e711e6d05a2b1b77f06f18d850a90159924dd3df975a4f49bd407ad8fd079. Repro:
HUNT_CBOE_IV/work_r8/r8_engine.py + r8_data_inspect.py + r8_results.json",HUNT_CBOE_IV-R8
```

## 9. What I could NOT determine (limits of this round)

- **Pre-2010 behaviour of C1 and C3** - impossible with this data vintage: VIX3M, GVZ and
  OVX all begin 2009-09-18 and the champion begins 2008-03-31. Not a measurement failure;
  the history does not exist here. Anyone wanting a pre-2010 read on the back end must find
  a different source.
- **VIX1D-based corners** - VIX1D starts 2022-05-13, so it is inception_fail (V2 9a) and NOT
  hunt-eligible. I inspected it and did not build on it, exactly as pre-registered.
- **The RUT file is unusable** (2020-11-27 start, n=1451) despite RUT being a long index -
  this vintage simply does not carry the long history, so no small-cap vol cross-section
  was possible.
- **§8h/§14 placebo** - not run, and I judge it correctly skipped rather than skipped for
  convenience: 8c (dAnn > 0) is a necessary condition that fails at every rung, and section
  14c states a placebo can never upgrade a candidate.
- **Whether a hysteresis / slower-moving version of these signals would do better** - not
  tested. All three signals churn hard (turnover cost 75-119 bp/yr against mean gross of
  0.11-0.32), which plausibly eats whatever weak signal exists. Adding hysteresis after
  seeing these results would be post-hoc tuning, so I did NOT do it; I flag it as the
  obvious untested follow-up for a future round with its own pre-registration.
- **Sector implied vol** - the charter's cross-sectional sector idea is not supportable:
  cboe_hist carries sector ETF PRICES (XLB..XLY) but no per-sector implied vol, so only a
  realized-vol dispersion could be built, which is a different (and untested) corner.

## 10. Repro commands (exact)

```
cd /Users/daxu/software/world-trader
python3 campaign/agents/chief/coord/HUNT_CBOE_IV/work_r8/r8_data_inspect.py
python3 campaign/agents/chief/coord/HUNT_CBOE_IV/work_r8/r8_engine.py
```

Outputs: `r8_coverage.json` / `r8_coverage.csv` (data inspection),
`r8_results.json` (every grid cell, every gate dict, every ladder row, leak probes),
`r8_candidate_<C1|C2|C3>_PRIMARY_daily.csv` (the pre-registered candidate daily nets).

Artifacts on disk in this directory:
- `PRE_REGISTRATION.md` (written before results)
- `r8_data_inspect.py`, `r8_coverage.json`, `r8_coverage.csv`
- `r8_engine.py`, `r8_results.json`
- `r8_candidate_C1_PRIMARY_daily.csv`, `_C2_`, `_C3_`
- `FINDINGS_R8.md` (this file)

ROUND 8 DONE
