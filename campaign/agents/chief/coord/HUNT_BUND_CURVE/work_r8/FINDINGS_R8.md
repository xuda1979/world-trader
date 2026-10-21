# HUNT_BUND_CURVE - ROUND 8 FINDINGS
Agent: HUNT_BUND_CURVE (coord fleet, R8). Repo root `/Users/daxu/software/world-trader`.
Work dir: `campaign/agents/chief/coord/HUNT_BUND_CURVE/work_r8/`.
Champion of record sha256 verified **unchanged** at round start and round end:
`8d7e711e6d05a2b1b77f06f18d850a90159924dd3df975a4f49bd407ad8fd079`
(n=4806, 2008-03-31..2026-08-28). No champion, sleeve, `bt/` or ledger file was modified.

---

## 0. HEADLINE

**All 7 pre-registered candidates REJECT.** Best is `BUND_CARRY_ENG` (SR 1.175, ann +16.30%,
MDD -43.92%, 5 neg years, cost 0.8 bp/yr) - it clears the SR/halves/corr gates and even
`beats_passive`, but **fails neg-years, fails the scramble, and has negative dAnn at every
blend rung**. Independently: **the BUND source has an ADOPTION-BLOCKING coverage gap**
(section 1). The mission's alternative outcome - a clean confirmation of death on a second
independent curve source - is what landed for the slope and butterfly families.

---

## 1. COVERAGE / END-DATE FINDING - ADOPTION BLOCKER (stated plainly, not papered over)

Measured, not taken from the manifest:

| fact | value |
|---|---|
| manifest claims | `vintage=2026-08-03 lag=39d` per tenor |
| **actual last date, all 8 tenors** | **2026-08-03** |
| champion last date | **2026-08-28** |
| gap | **25 calendar days / 19 champion trading days unreachable** |
| champion days after the bund series ends | 19 of 4806 (0.40% of the champion record) |
| 30y tenor first date | 2000-08-01 (3 years shorter than the other 7 tenors) |

The manifest's `lag=39d` was already true at download time (2026-09-11) and the source is a
**research panel, not a live feed** (its own downloader docstring says so). All 8 tenors stop
on exactly the same day, so **no tenor reaches further** and no re-slicing fixes this.

**Consequence:** any sleeve built on this source is truncated to 2026-08-03. A champion blend
would drop the champion's final 19 sessions. Under the charter's rule this is an ADOPTION
BLOCKER and it is recorded as one. It is **not** the binding constraint here - the candidates
fail on their own alpha/risk numbers on the span they do have (section 3) - but the blocker
stands and would have to be cleared by a fresh vintage before any adoption could be
contemplated. `r8_bund_curve.py` re-prints the per-tenor last date on every run.

Source: `tools/quant/data/bund_daily/bund_{02,03,05,07,10,15,20,30}y.csv` (Bundesbank BBSIS
Svensson par-yield curve, keyless TSID `BBSIS.D.I.ZST.ZI.EUR.S1311.B.A604.R<tenor>XX.R.A.A._Z._Z.A`).

---

## 2. PRE-REGISTRATION (fixed before any number was read; no sweep, no tuning)

Four families, 7 candidates, all conventions pinned a-priori and **identical to HUNT_TREASFUT
R7** so the two rounds are directly comparable:

| # | name | signal |
|---|---|---|
| 1 | BUND_SLOPE_mom | `s = sign(delta_63(y10-y2))` |
| 2 | BUND_SLOPE_rev | control, `s` negated |
| 3 | BUND_FLY_mom | `s = sign(delta_63(y10 - 0.5*(y5+y30)))` |
| 4 | BUND_FLY_rev | control, `s` negated |
| 5 | BUND_CARRY_ENG | `s = sign(y10/DUR10 - y2/DUR2)` on the FLATTENER (harvests positive engine accrual) |
| 6 | BUND_CARRY_DV01 | `s = sign(y10 - y2)` on the FLATTENER (real-world DV01-normalised carry) |
| 7 | BUND_RV_UST | `s = -sign(z_252((y10-y2)_DE - (y10-y2)_US))` |

Pinned conventions: `k=63` bd (one quarter); `PUB_LAG_BD=1` (a decision at close t may use
prints only through t-1, the PIT rule); weekly **Wednesday** decisions, positions **held daily**
(ffill) then **T+1** shifted; vol-target 10% ann expanding, clip 3.0; costs **6.4 bps FULL
|dW|** one-side + **0.5%/yr borrow** on shorts; synthetic TR per unit notional
`r = -DUR*dy + y/252`; `DURS = {2:1.9, 5:4.6, 10:8.5, 30:19.0}` (campaign modDur convention).
US leg from `tools/quant/data/more_fred/DGS{2,10}.csv` (1962+/1976+, through 2026-09-03 - the
US source is **not** the coverage-limited one).

Sign rule made explicit and **numerically verified inside the run** (max deviation 5e-16):
weights are built as `w_c = -coeff_c / DUR_c`, so `s=+1` always means *long the factor*
(`P&L = +dF`). This matters - see the prior-art defect in section 8.

---

## 3. RESULTS - admitted span, full numbers

Every candidate judged on its **admitted span** (first day with non-zero exposure,
GATES_CONTRACT_V2 section 9c). Leading flat days trimmed: FLY -897 days (30y tenor starts
2000-08-01), RV -255, SLOPE -142. Padded-span numbers are unchanged in verdict.

| candidate | admitted span | n | SR | ann% | MDD% | negY | worst% | cost bp/yr | gross max | corr champ | corr a6r7 | corr A1cr | scr_p | leak_ok | beats_passive | **V2** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BUND_SLOPE_mom | 1997-11-13..2026-08-03 | 7288 | **0.322** | +3.20 | -40.19 | 13 | -25.9 | 9.4 | 1.274 | +0.001 | +0.044 | +0.008 | 0.965 | True | FAIL | **FAIL** |
| BUND_SLOPE_rev | 1997-11-13..2026-08-03 | 7288 | -0.342 | -4.75 | -85.87 | 18 | -37.6 | 9.4 | 1.274 | -0.001 | -0.044 | -0.008 | 0.035 | True | FAIL | **FAIL** |
| BUND_FLY_mom | 2000-11-02..2026-08-03 | 6539 | -0.041 | -1.30 | -40.73 | 16 | -11.0 | 7.5 | 0.758 | -0.047 | +0.033 | +0.018 | 0.175 | True | FAIL | **FAIL** |
| BUND_FLY_rev | 2000-11-02..2026-08-03 | 6539 | +0.027 | -0.51 | -46.55 | 14 | -20.7 | 7.5 | 0.758 | +0.046 | -0.033 | -0.018 | 0.775 | True | FAIL | **FAIL** |
| **BUND_CARRY_ENG** | 1997-08-14..2026-08-03 | 7352 | **1.175** | **+16.30** | -43.92 | 5 | -25.1 | 0.8 | 0.644 | +0.022 | +0.056 | +0.014 | 0.980 | True | **PASS** | **FAIL** |
| BUND_CARRY_DV01 | 1997-08-14..2026-08-03 | 7352 | -0.498 | -7.46 | -97.43 | 17 | -40.3 | 0.5 | 0.644 | +0.029 | -0.027 | +0.067 | 0.050 | True | FAIL | **FAIL** |
| BUND_RV_UST | 1998-08-27..2026-08-03 | 6862 | -0.191 | -4.33 | -78.66 | 17 | -25.2 | 9.8 | **3.864** | -0.002 | -0.135 | -0.023 | 0.215 | True | FAIL | **FAIL** |

`BUND_RV_UST` additionally **breaches the gross leverage hard constraint (3.864 > 1.6)** - the
vol-target's 3.0 clip is reached on a four-leg book; it is non-compliant as built.

### 3a. Warm-up robustness (the -43.92% MDD is not a warm-up artifact)
`CARRY_ENG`'s full-span MDD (-43.92%, trough 1997-10-22, i.e. 10 weeks after the series starts)
is driven by the 60-day expanding-vol warm-up running at scale 1.0. Excluding the first 12
months the MDD is **-16.66%** - still 2.4x the -7% bar. The reject is therefore robust. Same
check on the champion span (>= 2008-03-31): SR 1.199, ann +12.92%, MDD -16.66%, 4 neg years.
`CARRY_ENG` is also the **only era-stable candidate** in the set (section 4).

---

## 4. MANDATORY pre/post-2010 STABILITY TABLE (SR by era)

| candidate | full | pre2010 | 2010-2013 | post2010 | post2013 | post2015 |
|---|---|---|---|---|---|---|
| BUND_SLOPE_mom | +0.321 | +0.392 | **-0.224** | +0.257 | +0.426 | +0.281 |
| BUND_SLOPE_rev | -0.342 | -0.409 | +0.199 | -0.283 | -0.453 | -0.308 |
| BUND_FLY_mom | -0.041 | -0.056 | +0.150 | -0.034 | -0.113 | -0.150 |
| BUND_FLY_rev | +0.027 | +0.043 | -0.163 | +0.009 | +0.082 | +0.118 |
| **BUND_CARRY_ENG** | **+1.175** | **+1.358** | +0.476 | +1.046 | +1.248 | +1.148 |
| BUND_CARRY_DV01 | -0.498 | -1.363 | +0.243 | +0.595 | +0.720 | +0.575 |
| BUND_RV_UST | -0.191 | -0.152 | +0.098 | -0.230 | -0.353 | -0.349 |

Reading: `SLOPE_mom` is **not** pre-2010-concentrated (negative in 2010-2013, recovers
post-2013) but is unstable and far below the SR 1.0 bar in every era. The two carry books
**flip sign across the 2010 boundary** in opposite directions (ENG +1.36 -> +1.05, DV01 -1.36 ->
+0.60) - i.e. which side of the curve pays carry is regime-dependent, and the DV01-normalised
version is pre-2010-negative. `CARRY_ENG` is the only candidate stable across all eras, and it
still fails on MDD and neg-years.

---

## 5. CHAMPION-BLEND BATTERY (section 8) - dAnn is negative at EVERY rung for EVERY candidate

Blend = `(1-w)*champion + w*candidate` on the common span. Section 8c (dAnn > 0) is HARD.

| candidate | w=0.025 | w=0.05 | w=0.10 | w=0.15 |
|---|---|---|---|---|
| BUND_SLOPE_mom | dAnn -0.947pp | -1.889 | -3.758 | -5.609 |
| BUND_SLOPE_rev | -1.212 | -2.415 | -4.795 | -7.140 |
| BUND_FLY_mom | -1.107 | -2.207 | -4.383 | -6.528 |
| BUND_FLY_rev | -1.047 | -2.088 | -4.149 | -6.182 |
| **BUND_CARRY_ENG** | **-0.642** (dSR +0.029) | -1.282 (dSR +0.057) | -2.560 (dSR +0.109) | -3.832 (dSR +0.151) |
| BUND_CARRY_DV01 | -1.011 | -2.017 | -4.012 | -5.984 |
| BUND_RV_UST | -1.207 | -2.407 | -4.782 | -7.128 |

`CARRY_ENG` is the only candidate that *raises* blend SR at every rung (+0.029..+0.151) and it
still **fails 8c outright** - the champion earns 37.49%/yr at SR 3.195, so any allocation to a
SR~1.2 sleeve at 10-14% vol is a straight capital-real loss. 8a (0 neg years) also fails for
every candidate. **No overlay is adoptable.**

---

## 6. LEAK PROBE (`campaign/bt/leakcheck.py` via `gates.run(..., leak_check=True)`)

All 7 candidates: `leak=False` (causal). `same_period_corr` in [-0.016, +0.016], all
`leak_ok=True`. Strongest |same_period_corr| is `BUND_CARRY_ENG` at -0.0177 (p 0.128).
`lag_scan` argmax is at lag 0 for every candidate (the contract's 6b condition). No lookahead
in any booked series. The harness supplied `sig=` (the gross-exposure series) and
`leak_check=True` explicitly on every acceptance-track call per V2 section 6e.

---

## 7. MISSION OUTCOME vs HUNT_TREASFUT R7 - (b) CONFIRMATION, with one shape nuance

TREASFUT R7 rejected ECB euro-area AAA curve slope/curvature (SLOPE_mom SR 0.394, CURV_mom
SR 0.272, both pre-2010-concentrated). The BUND native source behaves **materially the same**:

| family | ECB AAA (TREASFUT R7) | BUND native (this round) |
|---|---|---|
| slope momentum, full SR | 0.394 | 0.322 |
| slope momentum pre2010 / post2010 / post2013 | 0.639 / 0.290 / 0.407 | 0.392 / 0.257 / 0.426 |
| slope reversion control | -0.421 | -0.342 |
| curvature/butterfly momentum | 0.272 | -0.041 |
| curvature reversion control | -0.302 | +0.027 |
| corr to champion | -0.034 | +0.001 |

Both sources give **slope momentum SR ~0.3-0.4, an order of magnitude below the SR 1.0 bar**,
with the same sign, the same post-2010 decay, and the same near-zero correlation to the
champion. Horizon 1997-2026 (BUND) vs 2004-2026 (ECB) shifts the level by ~0.07 SR; it does not
change the verdict. **This is a clean confirmation of death on a second, independent curve
source (different provider, different fitting method, different country, 7 extra years).**
Nuance: BUND slope is *not* strictly pre-2010-concentrated (2010-2013 is -0.224 and post-2013
recovers to +0.426) - the ECB's "pre-2010-concentrated" phrasing is partly a 2004-2010 window
effect - but the economic conclusion is identical either way.

---

## 8. DEFECTS FOUND THIS ROUND (harness / prior art) - for the coordinator

1. **[PRIOR ART, sign] HUNT_TREASFUT R7's `weights_fly` has the opposite sign convention to its
   `weights_slope`.** With `w = -coeff/DUR`, `weights_slope` yields `P&L = +s*d(slope)` but
   `fly_weights = {"2": -0.5/d2, "10": +1/d10, "30": -0.5/d30}` yields `P&L = -s*d(fly)`. So
   their `TREASFUT7_ECB_CURV_mom` (SR 0.272) is in fact the **mean-reversion** book and their
   `CURV_rev` (SR -0.302) is the momentum book. Their published conclusion is unaffected (both
   orientations were reported and both are dead), but the two labels are swapped. My weights use
   an explicit `w_c = -coeff_c/DUR_c` rule with an in-run assertion (max dev 5e-16) so the two
   families cannot disagree.
2. **[OWN, fixed] `book_rv` column-label alignment.** Multiplying `We[["de2","de10"]]` by
   `Rb[["2","10"]]` aligns on *labels*, so both RV legs silently became all-NaN -> `sum()` 0.0,
   producing a book with **zero market P&L and only costs** (`BUND_RV_UST` briefly read
   SR -2.779, vol 0.3%, `uniq_ratio` 0.001). Fixed with positional multiplication (`_vdp`) after
   the `uniq` diagnostic exposed it. Corrected numbers are in section 3. **Any other agent
   building multi-instrument books by label-joining differently-named frames has this bug.**
3. **[DIAGNOSTIC] Carry decomposition.** `CARRY_ENG`: accrual ann +17.728% (SR 16.03) vs duration
   ann -1.207% (SR -0.02). The entire positive return is the `y/252` accrual term and the entire
   variance is the duration term - a textbook carry profile, and the reason the vol-target levers
   it to 13.7% vol with MDD -43.9%. Recorded so the SR 1.175 is not mistaken for alpha.

---

## 9. VERDICTS

| candidate | verdict | primary reason (with number) |
|---|---|---|
| BUND_SLOPE_mom | **REJECT** | SR 0.322 << 1.0; 13 neg years; MDD -40.19%; scramble p 0.965 |
| BUND_SLOPE_rev | **REJECT** | SR -0.342 |
| BUND_FLY_mom | **REJECT** | SR -0.041 |
| BUND_FLY_rev | **REJECT** | SR +0.027, ann -0.51%, 14 neg years |
| BUND_CARRY_ENG | **REJECT** | SR 1.175 clears 3 gates but 5 neg years (worst -25.1%), MDD -43.92% (-16.66% ex-warmup), scramble p 0.980, section-8c dAnn -0.642pp at best rung |
| BUND_CARRY_DV01 | **REJECT** | SR -0.498; MDD -97.43% |
| BUND_RV_UST | **REJECT** | SR -0.191; MDD -78.66%; gross 3.864 **breaches the 1.6 cap** |

**Family verdict: the German Bund native curve is a DEAD family for this campaign on all four
corners tried (slope momentum/reversion, butterfly curvature, carry/rolldown, Bund-vs-UST RV).**
Everything decorrelates beautifully (|corr| <= 0.135 vs champion, a6r7 and A1credit) - this is
genuinely orthogonal data with no campaign-cost edge to carry it, exactly R7's finding.

**No ADOPT. No UNJUDGEABLE** - every candidate was judgeable on its admitted span; the coverage
gap (section 1) is a separate, independent blocker that would have applied to an otherwise
winning candidate and does not rescue any of these.

---

## 10. ON-DISK ARTIFACTS

```
campaign/agents/chief/coord/HUNT_BUND_CURVE/work_r8/
  r8_bund_curve.py             # main engine + pre-registered corners + V2 battery (primary)
  r8_gate_flags.py             # rebuilds the full V2 gate dict from the SAVED series/positions
  r8_bund_curve_results.json   # every number in sections 3/4/5 + coverage block
  r8_gate_flags.json           # per-candidate gate booleans + full leak dicts (section 10a)
  series/<name>_net.csv        # published net return series (artifact-verifiable, 10a)
  series/<name>_positions.csv  # published position series (artifact-verifiable, 10a)
```

## 11. EXACT REPRO COMMANDS

```bash
cd /Users/daxu/software/world-trader
python3 campaign/agents/chief/coord/HUNT_BUND_CURVE/work_r8/r8_bund_curve.py
python3 campaign/agents/chief/coord/HUNT_BUND_CURVE/work_r8/r8_gate_flags.py
```

---

## 12. LIMITATIONS / WHAT I COULD NOT DETERMINE

- **Revision behaviour of the source is unmeasurable.** Only ONE vintage is on disk, so I cannot
  tell whether the Bundesbank revises the Svensson curve between vintages. If it does, every
  backtest number here is on a single (possibly revised) snapshot. The downloader's own docstring
  flags the series as a stale research panel.
- **Whether the 39-day lag is structural or a one-off.** The served file says
  `last update 2026-08-03`; I cannot distinguish a permanent publication delay from a temporarily
  stale mirror, so I cannot say when a compliant vintage could be fetched.
- **The 30y tenor's shorter history (2000-08-01)** is unexplained in the manifest; it is why the
  butterfly corners lose their first 897 days. I did not substitute 20y/15y for 30y (that would
  be a post-hoc re-specification, not a pre-registered corner).
- **I did not test a 10s30s slope** as a separate corner (the charter offered it as an
  alternative to the 5s10s30s butterfly). Given the butterfly and the 2s10s slope both died and
  the R7 ECB analogue died, a third collinear slope corner was not pre-registered and I did not
  add it post hoc.
- **US-leg curve carry/rolldown and a full Bund-vs-UST *level* RV** were not tested - the
  charter's RV direction was scoped to the curve spread, and the curve-spread version is
  decisively dead.

ROUND 8 DONE
