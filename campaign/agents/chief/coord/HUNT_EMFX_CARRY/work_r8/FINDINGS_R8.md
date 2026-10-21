# HUNT_EMFX_CARRY -- ROUND 8 FINDINGS

**Agent:** HUNT_EMFX_CARRY (round 8).  **Data:** tools/quant/data/em_rates/ (landed 2026-09-11, unmined).
**Champion of record:** campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
sha256 prefix 8d7e711e6d05a2b1 -- **re-verified this round** (n=4806, 2008-03-31..2026-08-28,
ann 37.49%, SR 3.195, MDD -6.69%, 0 neg years). Not touched.

**HEADLINE: 7/7 pre-registered candidates REJECT; 12/12 pre-registered overlay configs REJECT.**
Two of the three chartered directions turned out to be **not expressible on this data estate**
(section 2). The negative is well-evidenced and, more usefully, it is *structural* (section 6) --
not a tuning failure.

---

## 1. DATA QUALITY / COVERAGE (inspected first, as required)

All eight files are **official central-bank sources** (BCB SGS, BCRP, NBP, CNB), pulled keyless by
em_rates_dl.py. Format date,value; all parse with **0 bad dates, 0 duplicate dates, 0 NaNs**.

| file | span | n | cadence | coverage vs business days | notes |
|---|---|---|---|---|---|
| brazil_selic | 1995-01-02 .. 2026-09-09 | 7954 | daily | 96.2% | 76.0% stale repeats -- **expected**: a policy rate is a step function |
| brazil_usdbrl | 1995-01-02 .. 2026-09-10 | 7955 | daily | 96.2% | max 1d move 11.1% on 1999-01-15 (the BRL devaluation), pre-window |
| brazil_ipca | 1995-01 .. 2026-07 | 379 | monthly | 100% of months | monthly **% rate**, not a level |
| czech_usdczk | 1995-01-02 .. 2026-09-10 | 7985 | daily | 96.6% | clean: 0 stale runs over 5d |
| czech_eurczk | 1999-01-01 .. 2026-09-10 | 6973 | daily | 96.5% | **5 stale runs over 5d, max 47 identical days** = the CNB EURCZK floor (2013-11..2017-04); a peg, not noise |
| peru_usdpen | 1997-01-02 .. 2026-09-09 | 7393 | daily | 95.5% | cleanest series; low vol (5.4% ann) |
| poland_usdpln | 2002-01-02 .. **2025-12-31** | 6062 | daily | 96.8% | **DEAD SERIES -- 8 months missing (all of 2026)** |
| poland_eurpln | 2002-01-02 .. **2025-12-31** | 6062 | daily | 96.8% | same dead tail |

### 1a. The FX series are CLEAN -- verified, not assumed

The charter warned that tools/quant/data/fx/ (twelvedata) is roughly half noise and that the
previously adopted **CFX4** sleeve was a vendor artifact. I confirmed CFX4's champion weight is
**exactly 0.0** (`grep CFX4 campaign/results/RAWEW13v2_IS_SR_weights.csv` returns `CFX4,0.0`).

These em_rates series are NOT that feed. Independent evidence:
- **Triangular consistency**: implied EURUSD derived from eurczk/usdczk and from eurpln/usdpln lies
  inside [0.83, 1.60] on **100.00%** of days (n=6973 and n=6062). A noisy feed fails this.
- Largest 1-day moves are all identifiable crisis dates (BRL 1999-01-15 devaluation; CZK 1997-05-28;
  PLN 2010-05-10), not vendor spikes.
- Only one stale-pricing regime exists (the CNB EURCZK peg); it is a real macro event, and I built
  on **usdczk**, not eurczk.

### 1b. UNIT VERIFICATION -- brazil_selic is a DAILY percent (a ~250x trap)

Anchored against published effective Selic. Annualizing as (1+v/100)^252 - 1:

| date | raw | annualized | published effective (target) |
|---|---|---|---|
| 2016-01-15 | 0.05253 | 14.15% | ~14.15% (14.25%) |
| 2020-08-14 | 0.00747 | 1.90% | ~1.90% (2.00%) |
| 2023-08-15 | 0.04904 | 13.15% | ~13.15% (13.25%) |

Treating the value as already-annual would have overstated carry ~250x. DFF **is** annualized
(2023-08 = 5.33). Carry is therefore selic/100 - (dff/100)/252 per day.

### 1c. Coverage inside the champion window (2008-03-31..2026-08-28)

BRL 96.3% / CZK 96.4% / PEN 95.1% / **PLN 93.3% and exactly 0% after 2025-12-31**.
PLN is masked flat from 2026-01-02 (its last valid T+1 signal is carried exactly 1 day, then exits;
verified). The 2026 PLN leg contributes **nothing** -- disclosed, not hidden.

---

## 2. WHAT IS NOT EXPRESSIBLE (honest limit, found before modelling)

The charter asked for policy-rate differential vs USD. **Only BRL has both a policy rate and an FX
pair on this estate.** Exhaustive sweep (find over all of tools/quant/data for *policy*, *selic*,
*rate*.csv, plus the full more_fred/manifest.csv) found only AUD/NOK/GoC/India policy files and
FRED's IRLTLT01* (DM long-term yields). **No CZK / PLN / PEN policy or money-market rate exists on
disk**, and FRED carries none in the fetched set.

Consequences, stated plainly:

- **Chartered direction "cross-sectional EM FX carry" (long high-yielders / short low-yielders) is
  UNJUDGEABLE -- not tested-and-rejected.** With 1 of 4 currencies carrying a rate there is no
  cross-section to rank. (Even with full rates, a **4-currency** basket is too small for a credible
  cross-section; C6 below confirms it empirically.)
- **C3-C7 (CZK/PLN/PEN legs) are SPOT-ONLY** -- no accrual is credited or charged for those three.
  This is a real limitation, not a conservative choice: the sign of the local-vs-USD differential
  flips across 2008-2026 (CZK ~0.05% in 2012-17 vs DFF 0.05-0.25%; CZK ~7% in 2022-23 vs DFF 5.33%),
  so the omission could move those sleeves either way by order 1-3 pp/yr. It does not affect BRL.

---

## 3. PRE-REGISTERED CANDIDATES (declared before any performance number)

Construction, all causal (weights use info through t-1 only): long-EM per-unit return
= -dlog(USDXXX) + carry; effective weight w_t = signal_(t-1) * volscale_(t-1); portfolio-level
trailing vol target 10% (cap 3), **gross capped at 1.0**. Costs **6.4bp on FULL |dW| one-side**,
+0.5%/yr borrow on short notional, +4.5%/yr margin on max(gross-1,0). Evaluated on the champion
window (n=4806) so the blend is index-identical.

| # | candidate | what it is |
|---|---|---|
| C1 | BRL_CARRY_L | long BRL vs USD (carry differential over 0) |
| C2 | BRL_CARRY_MED | C1 gated on carry level over its own expanding median |
| C3 | TSMOM_252 | 12m time-series momentum, 4 USD pairs, long/short, EW |
| C4 | TSMOM_126 | 6m variant |
| C5 | BRL_MOM_252 | BRL-only 12m momentum (isolates the single-currency question) |
| C6 | XS_252 | cross-sectional long strongest / short weakest (pre-registered as under-powered) |
| C7 | COMBO | carry sign (BRL) + momentum sign (all), EW |

### 3a. Standalone results + V2 gate verdict

| candidate | n | SR | ann % | MDD % | neg yrs | cost bp/yr | turns/yr | gross max | corr champ | scr_p | beats_passive | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C1_BRL_CARRY_L | 4806 | 0.104 | +0.53 | -34.37 | 11 | 0.9 | 0.14 | 1.00 | -0.0188 | 0.875 | False | **FAIL** |
| C2_BRL_CARRY_MED | 4806 | 0.336 | +2.59 | -40.45 | 5 | 5.1 | 0.79 | 1.00 | +0.0050 | 0.375 | False | **FAIL** |
| C3_TSMOM_252 | 4806 | -0.004 | -0.22 | -33.68 | 10 | 71.5 | 11.18 | 1.00 | -0.0340 | 0.575 | False | **FAIL** |
| C4_TSMOM_126 | 4806 | -0.394 | -3.00 | -47.83 | 11 | 120.6 | 18.84 | 1.00 | -0.0502 | 0.565 | False | **FAIL** |
| C5_BRL_MOM_252 | 4806 | -0.268 | -3.45 | -62.23 | 13 | 47.7 | 7.45 | 1.00 | -0.0131 | 0.665 | False | **FAIL** |
| C6_XS_252 | 4806 | -0.062 | -0.67 | -30.08 | 10 | 165.8 | 25.90 | 1.00 | +0.0199 | 0.485 | False | **FAIL** |
| C7_COMBO | 4806 | 0.109 | +0.55 | -35.27 | 10 | 81.3 | 12.70 | 1.00 | -0.0330 | 0.035 | False | **FAIL** |

Every candidate fails on **four independent gates**: sr_min (need at least 1.0; best 0.336),
halves (need both at least 0.5; best pair 0.26/-0.32), neg_max (need at most 2; best 5), and
**beats_passive** (best passive = sixty_forty SR **0.591** on the matched span; best candidate
0.336 -- margin -0.26 to -0.98). The corr gate is *not* what kills them: all seven are genuinely
orthogonal to the champion (|corr| at most 0.050). Per the charter, **low correlation with dAnn at
or below 0 is still a reject.**

Note on gross: C3/C4/C6/C7 sit at the 1.0 gross cap ~95% of days, so those four are effectively
constant-gross books at ~6-7% realized vol rather than true VT10. SR is scale-invariant so the
verdicts are unaffected, but the reported vol/MDD are those of the capped book.

### 3b. Stability: pre-2010 vs post-2010 (MANDATORY table)

| candidate | pre-2010 SR | pre-2010 ann % | post-2010 SR | post-2010 ann % | H1 SR | H2 SR |
|---|---|---|---|---|---|---|
| C1_BRL_CARRY_L | 0.135 | +0.89 | 0.100 | +0.49 | 0.098 | +0.11 |
| C2_BRL_CARRY_MED | -0.996 | -3.05 | 0.390 | +3.21 | 0.236 | +0.53 |
| C3_TSMOM_252 | 1.308 | +9.67 | -0.169 | -1.21 | 0.259 | -0.32 |
| C4_TSMOM_126 | -1.143 | -14.19 | -0.251 | -1.74 | -0.618 | -0.08 |
| C5_BRL_MOM_252 | 1.118 | +10.37 | -0.391 | -4.81 | -0.200 | -0.35 |
| C6_XS_252 | 0.141 | +0.72 | -0.082 | -0.82 | 0.153 | -0.28 |
| C7_COMBO | 0.482 | +5.71 | 0.038 | +0.02 | 0.304 | -0.16 |

**Pre-2010 concentration check -- the decisive era finding.** The only sub-period where any candidate
looked strong is pre-2010 (C3 TSMOM_252 SR +1.308 / ann +9.67%; C5 BRL_MOM SR +1.118 / ann +10.37%),
and both **decay to negative post-2010** (-0.169 and -0.391). That is exactly the pre-2010-concentrated
pattern the charter says must FAIL, and it matches the well-known decay of EM FX momentum after 2008.
C1 (plain BRL carry) is the most era-stable but the weakest (SR 0.10 in both). C2's post-2010 SR of
0.390 is the best modern number and is still far below 1.0.

### 3c. Causality / leak evidence (measured, not assumed)

- **Leak probe on the SIGNED weights** (bt.leakcheck, run directly on signed net exposure vs the
  per-unit return -- the meaningful probe): leak=False for all 7; max |same-period corr| **0.021**,
  smallest p 0.14; lag 0 is never the argmax.
- **Truncation-invariance rebuild**: recomputed each sleeve on the first 70% of the sample; the
  overlap is **byte-identical, max abs dev 0.000e+00** on all 7. This is proof-grade causality
  evidence, stronger than the statistical probe.
- Harness note: gates.run was called the house way (sig = held gross units, r_pu = net/sig, so
  sig*r_pu == net exactly), which makes the built-in scr_p scramble weak; I therefore report the
  signed-weight probe plus truncation dev as the real causality evidence.

### 3d. Blend ladder -- dAnn at every rung

| candidate | sleeve w | dAnn pp | dSR | dMDD pp | dAnn over 0? |
|---|---|---|---|---|---|
| C1_BRL_CARRY_L | 2.5% | -1.04 | +0.003 | +0.15 | **no** |
| C1_BRL_CARRY_L | 5.0% | -2.08 | +0.004 | +0.31 | **no** |
| C1_BRL_CARRY_L | 7.5% | -3.10 | +0.004 | +0.47 | **no** |
| C1_BRL_CARRY_L | 10.0% | -4.13 | +0.001 | +0.63 | **no** |
| C1_BRL_CARRY_L | 15.0% | -6.15 | -0.013 | +0.94 | **no** |
| C2_BRL_CARRY_MED | 2.5% | -0.97 | +0.006 | +0.16 | **no** |
| C2_BRL_CARRY_MED | 5.0% | -1.94 | +0.011 | +0.33 | **no** |
| C2_BRL_CARRY_MED | 7.5% | -2.90 | +0.015 | +0.49 | **no** |
| C2_BRL_CARRY_MED | 10.0% | -3.86 | +0.016 | +0.65 | **no** |
| C2_BRL_CARRY_MED | 15.0% | -5.76 | +0.012 | +0.98 | **no** |
| C3_TSMOM_252 | 2.5% | -1.07 | +0.001 | +0.16 | **no** |
| C3_TSMOM_252 | 5.0% | -2.14 | +0.002 | +0.32 | **no** |
| C3_TSMOM_252 | 7.5% | -3.20 | +0.001 | +0.49 | **no** |
| C3_TSMOM_252 | 10.0% | -4.25 | -0.000 | +0.65 | **no** |
| C3_TSMOM_252 | 15.0% | -6.33 | -0.007 | +0.98 | **no** |
| C4_TSMOM_126 | 2.5% | -1.17 | -0.005 | +0.17 | **no** |
| C4_TSMOM_126 | 5.0% | -2.32 | -0.011 | +0.34 | **no** |
| C4_TSMOM_126 | 7.5% | -3.48 | -0.018 | +0.51 | **no** |
| C4_TSMOM_126 | 10.0% | -4.62 | -0.028 | +0.69 | **no** |
| C4_TSMOM_126 | 15.0% | -6.88 | -0.053 | +1.03 | **no** |
| C5_BRL_MOM_252 | 2.5% | -1.17 | -0.007 | +0.15 | **no** |
| C5_BRL_MOM_252 | 5.0% | -2.34 | -0.018 | +0.31 | **no** |
| C5_BRL_MOM_252 | 7.5% | -3.49 | -0.032 | +0.46 | **no** |
| C5_BRL_MOM_252 | 10.0% | -4.64 | -0.049 | +0.62 | **no** |
| C5_BRL_MOM_252 | 15.0% | -6.91 | -0.098 | +0.93 | **no** |
| C6_XS_252 | 2.5% | -1.09 | -0.003 | +0.15 | **no** |
| C6_XS_252 | 5.0% | -2.17 | -0.007 | +0.29 | **no** |
| C6_XS_252 | 7.5% | -3.24 | -0.012 | +0.44 | **no** |
| C6_XS_252 | 10.0% | -4.31 | -0.019 | +0.59 | **no** |
| C6_XS_252 | 15.0% | -6.42 | -0.038 | +0.89 | **no** |
| C7_COMBO | 2.5% | -1.04 | +0.004 | +0.16 | **no** |
| C7_COMBO | 5.0% | -2.08 | +0.006 | +0.32 | **no** |
| C7_COMBO | 7.5% | -3.11 | +0.007 | +0.48 | **no** |
| C7_COMBO | 10.0% | -4.13 | +0.007 | +0.64 | **no** |
| C7_COMBO | 15.0% | -6.16 | -0.001 | +0.97 | **no** |

**dAnn is negative at every rung for every candidate.** V2 section 8c is a HARD gate, so all 7 also
fail as overlays. The best cell anywhere is C2 at 2.5% sleeve weight: dAnn **-0.97pp**, dSR +0.006.

---

## 4. SECOND WAVE -- EM-FX risk-off TIMING overlay (pre-registered before running)

**Why this form:** section 6 shows a capital-diluting sleeve cannot clear 8c here. The only remaining
form is a *timing* overlay that modulates the champion's own exposure (the VOL2/PCR precedent),
because that does not dilute the champion's return-per-unit.

**Pre-registered grid** (declared in emfx_overlay.py before results): signal family
{EW-basket, BRL-only} x lookback {21, 63, 126} x trim-to {0.0, 0.5} = 12 configs. Gate: risk-off when
the L-day long-EM log return is below 0. Champion-identical cost 6.4e-4 * 1.6 * |dp|, with p_t = g_(t-1).

| config | trim % | ann % | SR | MDD % | neg yrs | dAnn pp | dSR | dH2 | 8a | 8b | 8c | 8d |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| basket_L21_to0.0 | 50.7 | 10.54 | 1.963 | -7.10 | 2 | -26.95 | -1.232 | -0.895 | N | N | N | N |
| basket_L21_to0.5 | 50.7 | 23.40 | 3.163 | -5.25 | 0 | -14.09 | -0.033 | +0.129 | Y | Y | N | N |
| basket_L63_to0.0 | 51.2 | 12.43 | 2.322 | -8.29 | 0 | -25.06 | -0.873 | -0.890 | Y | N | N | N |
| basket_L63_to0.5 | 51.2 | 24.45 | 3.309 | -6.50 | 0 | -13.04 | +0.114 | +0.099 | Y | Y | N | Y |
| basket_L126_to0.0 | 55.6 | 11.49 | 2.152 | -4.91 | 1 | -26.00 | -1.043 | -1.066 | N | Y | N | N |
| basket_L126_to0.5 | 55.6 | 23.93 | 3.241 | -5.12 | 0 | -13.56 | +0.046 | +0.058 | Y | Y | N | Y |
| brl_L21_to0.0 | 51.5 | 10.25 | 1.821 | -6.42 | 4 | -27.24 | -1.374 | -1.371 | N | Y | N | N |
| brl_L21_to0.5 | 51.5 | 23.23 | 3.072 | -4.99 | 0 | -14.26 | -0.123 | -0.032 | Y | Y | N | N |
| brl_L63_to0.0 | 51.2 | 11.30 | 2.073 | -6.17 | 1 | -26.20 | -1.123 | -1.192 | N | Y | N | N |
| brl_L63_to0.5 | 51.2 | 23.82 | 3.198 | -5.33 | 0 | -13.67 | +0.002 | -0.008 | Y | Y | N | N |
| brl_L126_to0.0 | 54.3 | 11.84 | 2.157 | -5.33 | 1 | -25.65 | -1.038 | -1.444 | N | Y | N | N |
| brl_L126_to0.5 | 54.3 | 24.12 | 3.228 | -5.33 | 0 | -13.37 | +0.032 | -0.073 | Y | Y | N | N |

**0/12 clear section 8c.** The result is easy to read and is itself the finding:

- to=0.5 configs sit at **SR 3.07-3.31 vs the champion's 3.195** while halving exposure ~51% of the
  time. **The EM-FX "risk-off" signal carries essentially ZERO timing information** about this
  champion -- cutting exposure on half the days leaves risk-adjusted return unchanged, so the only
  effect is the ~13pp of return given away.
- to=0.0 configs are strictly worse (SR 1.82-2.32, dAnn -25.7 to -27.3pp).
- Best non-8c cell: basket_L63_to0.5 (dSR +0.114, dH2 +0.099, MDD -6.50% vs -6.69%, 0 neg years)
  still fails **dAnn -13.04pp**.

Because 8c fails everywhere, the section-8h placebo is **not reached** -- I record it as moot rather
than claiming a placebo reading I did not need to take.

---

## 5. VERDICT

**REJECT -- all 7 pre-registered candidates and all 12 pre-registered overlay configs.**

| direction | verdict |
|---|---|
| TS carry (BRL vs USD) | **REJECT** -- SR 0.104 (C1) / 0.336 (C2); ann 0.53% / 2.59%; MDD -34% / -40%. The carry is real (+8.15%/yr average) but BRL depreciated ~7.4%/yr against USD over the window, netting only +0.5 to +2.6% at ~9% vol |
| FX momentum / trend (BRL, CZK, PLN, PEN) | **REJECT** -- SR -0.394..-0.004; the only positive era is pre-2010 (C3 pre-2010 SR +1.31 decaying to post-2010 -0.17), which the charter fails as pre-2010-concentrated |
| Cross-sectional EM FX carry | **UNJUDGEABLE** -- no policy rates for CZK/PLN/PEN exist on disk (section 2); with 1 of 4 currencies carrying a rate there is no cross-section to rank. C6 (momentum cross-section, the proxy) returns SR -0.062 |
| EM-FX risk-off timing overlay | **REJECT** -- 0/12 clear 8c |

**ADOPT: nothing.**

## 6. THE STRUCTURAL FINDING (the durable result this round)

Measured and verified this round: for a constant-mix blend,

    dAnn  ~=  (1-w) * (ann_sleeve - ann_champion)  +  small negative variance residual

Controls that pin it: a flat 0%-return sleeve at 2.5% weight gives **-1.07pp** (predicted -0.94pp);
the champion blended with **itself** gives **+0.0023pp** (the null). The champion's ann_geo is **37.49%**.

**Therefore any capital-diluting sleeve must itself return more than 37.49%/yr to clear V2 section 8c.**
The best sleeve built here returns **2.59%/yr -- a 34.9pp gap.** This is arithmetic, not a modelling
failure, and it is the general reason overlay hunts keep rejecting: this champion is so strong
(SR 3.195, MDD only -6.69%) that (a) there is almost no drawdown left for a timing overlay to avoid --
halving exposure to save ~0.2-1.4pp of MDD costs 13pp of return -- and (b) any capital dilution must
beat a 37.5% annual return to pay for itself. A future EM-FX corner should be submitted as a
**levered standalone** judged on the NEW-SLEEVE track, or not at all.

## 7. WHAT I COULD NOT DETERMINE

1. **EM FX cross-sectional carry** -- no CZK/PLN/PEN policy rates on disk; and a 4-currency basket is
   too small for a credible cross-section regardless.
2. **Carry accrual for CZK/PLN/PEN** -- those legs are spot-only; the omission is unquantified on disk
   and could move their means by order 1-3 pp/yr in either direction.
3. **Poland in 2026** -- the NBP series ends 2025-12-31 (8 months missing); the PLN leg is masked flat.
4. **scr_p as a discriminator** -- the house sig = gross-units convention makes the built-in scramble
   weak; I substituted a signed-position leak probe plus a truncation-invariance rebuild. If a future
   round wants scr_p to bite, sig should carry sign.

## 8. ARTIFACTS + REPRO

All under campaign/agents/chief/coord/HUNT_EMFX_CARRY/work_r8/.

    python3 d01_inspect_em_rates.py   # data quality: coverage, cadence, gaps, stale runs
    python3 d02_deep.py               # unit verification (Selic daily-vs-annual) + triangular FX check
    python3 emfx_build.py             # 7 pre-registered candidates -> emfx_results.json + nets/
    python3 emfx_overlay.py           # 12 pre-registered overlay configs -> emfx_overlay.json
    python3 d05_structural.py         # the dAnn dilution arithmetic + null controls
    python3 d06_verify.py             # gross<=1.6, PLN dead-tail masking, weight checks

Outputs: emfx_results.json, emfx_overlay.json, d01_report.json, nets/*.csv (costed daily net series
per candidate), emfx_lib.py (shared construction).

**Two defects caught in my own code before any number was trusted** (disclosed because each would
have silently invalidated or inflated results):

1. ffill on the price panel extended Poland's dead 2025-12-31 price across all of 2026 -- 8 months of
   fake 0%-vol flat prices that would have driven the vol-target scale to its cap. Fixed by
   mask_stale=True in emfx_lib.panel.
2. In emfx_overlay.py I wrote -np.log(PX) without .diff() (unary minus binds looser than .diff()), so
   the rolling "signal" was a negative price *level*, not a return -- it reported a risk-off gate rate
   of 99.6%, which is impossible. The impossible number is what exposed it; fixed and re-run.

ROUND 8 DONE