# HUNT_FXCARRY2 — ROUND 2 FINDINGS (2026-09-07)

Charter: fix the R1 data-depth blocker first (FRED DEX daily + IRSTCI01 monthly rates,
linted into tools/quant/data/more_fx/), then re-test monthly carry at 2004+ with full
gates. Verdict: **hard negative on every charter variant**. Factor is dead post-2004.

## STEP (a) DATA — PASS (29/29 linted series written)
campaign/scripts/HUNT_FXCARRY2_round2_fetch.py -> tools/quant/data/more_fx/ + MANIFEST.md.
- Daily DEX FX: DEXUSEU 1999+ (6936 obs), DEXJPUS/DEXCAUS/DEXUSUK/DEXSZUS/DEXNOUS 1971-72+
  (~13.7k obs), DEXUSAL 1973+, DEXSIUS 1981+, DEXKOUS 1993+. All PASS lint, 0 splices.
- Monthly IRSTCI01 immediate rates (verified live: charter's IR3T01* ids do NOT exist on
  FRED; IRSTCI01 do): US 1954+, DE 1960+, FR 1955+, JP 1985+, GB 1978+, CA 1975+, CH
  1972-2024-03, AU 1990-08+, NZ 1985-2024-12, EZ 1994+, NO 1982+, KR 1991+. PASS.
- Monthly CPALTT01 CPI for real carry: US/DE/GB/CA/CH/FR 1955+, JP 1955-2021-06,
  NZ 1993-2024-03. No KRW/NOK CPI on FRED under CPALTT01 -> those pairs honestly dropped
  from the real-carry variant, not faked.
Note: rate depth is the binding constraint, not FX depth — the 8-pair basket is only
fully populated from the 1990s, so 2004+ is comfortably covered.

## STEP (b) CARRY — FAIL (all variants, exact numbers, 2004+ n=5680, net of 6.4bps FULL |dW| + 0.5%/yr borrow + 4.5%/yr margin, T+1, carry accrual credited daily)
Engine: campaign/scripts/HUNT_FXCARRY2_round2.py (reproducible). Monthly signal at
month-end t, position from t+1; interest-rate-parity accrual sign*(r_fgn-r_usd)/252
credited while held.

| variant | net SR | ann | negyr | worst yr | H1/H2 | corrChamp | scramble p | verdict |
|---|---|---|---|---|---|---|---|---|
| carry-nominal-EW (flagship) | -0.004 | -0.18% | 11 | -19.4% (2008) | -0.13/+0.16 | 0.028 | 0.760 | FAIL |
| carry-spotonly (R1-flaw repro) | -0.228 | -1.4% | 14 | -21.3% | -0.35/-0.07 | 0.028 | 0.760 | FAIL |
| carry-real-EW (CPI-deflated) | -0.131 | -0.9% | 17 | -9.7% | +0.28/-0.62 | -0.019 | 0.245 | FAIL |
| carry+mom63-EW | -0.026 | -0.2% | 13 | -4.6% | +0.24/-0.32 | 0.036 | 0.620 | FAIL |
| carry-volscaled-EW (inv-vol wts) | -0.097 | -0.6% | 13 | -20.4% | -0.23/+0.08 | 0.028 | 0.855 | FAIL |
| carry-HML2v2-rank-EW | +0.074 | +0.2% | 8 | -10.7% | -0.05/+0.27 | 0.007 | 0.700 | FAIL |
| carry-HML3v3-rank-EW | +0.009 | -0.1% | 9 | -17.5% | -0.16/+0.28 | 0.013 | 0.710 | FAIL |
| momentum252-only-EW (control) | -0.174 | -1.3% | 15 | -13.0% | -0.07/-0.32 | 0.029 | 0.530 | FAIL |

## Robustness: the factor is genuinely dead, not cost-killed or framework-broken
- GROSS (pre-cost) book SR = 0.106 vs net -0.004. Costs are NOT the story; there is no
  gross edge. Accrual-only drift = +1.25%/yr on the held book — an order of magnitude
  too small vs the -29.2% max-dd path. Spot component SR = -0.118.
- Engine sanity: the yearly signature is exactly the documented carry-crash profile
  (+6.7%/+3.7% 2004-05, -19.4% 2008, +11.5% 2009, then noise) — the sign conventions and
  T+1 machinery are behaving; the factor simply stopped paying after GFC in this universe.
- Window sweep (nominal carry): 1990+ net SR 0.230, 1999+ 0.177, 2004+ -0.004, 2012+
  0.092. The only remotely-positive stretches are pre-GFC; every window fails all gates
  (SR<<1.0, halves fail, scramble p 0.45-0.86 >> 0.05). No 0-neg year window exists.
- Scramble test at book level (200x random roll of all pair positions): real SR is
  indistinguishable from shuffled for every variant (p 0.245-0.855). The signal has
  zero timing information post-2004.
- Decorrelation gate trivially satisfied (|corr| 0.007-0.036 << 0.15) — irrelevant here
  since nothing else passes.

## Honest reading
FX carry in this 8-pair FRED universe is a pre-GFC factor. Post-2004 its interest-rate
differential (month-end IRSTCI01 immediate rates, which the charter specified) carries a
+1.2%/yr drift against a -19% crash tail — net-of-nothing SR ~0. The charter's own fix
for R1's flaw (deeper data, full accrual, 2004+) was implemented exactly and still
fails every performance gate. No param search was done to force a plateau pass because
no variant clears gate (a) SR>=1.0 anywhere near; per contract §5 this is logged as a
dead idea rather than iterated into a false positive.

## Artifacts
- campaign/scripts/HUNT_FXCARRY2_round2_fetch.py + tools/quant/data/more_fx/ (29 series + MANIFEST.md)
- campaign/scripts/HUNT_FXCARRY2_round2.py (engine, reproducible)
- campaign/agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R2_carry_nominal_EW.csv + .meta (flagship, FAIL, saved per contract §4)
- campaign/results/DEAD_IDEAS.csv row appended (HUNT_FXCARRY2-R2)

ROUND 2 DONE


# HUNT_FXCARRY2 — ROUND 3 FINDINGS (2026-09-07)

Charter: tail-controlled carry attacking the documented R2 failure mechanism
(-19.4% 2008 crash tail), each variant a full-gated standalone sleeve, post-2004
era only; + cross-verify HUNT_INTERNATIONAL2's R2 negative. Read DEAD_IDEAS first:
the carry family is already R2-dead (row HUNT_FXCARRY2-R2), so round 3 tested ONLY
the three chartered crash controls on top of the byte-identical R2 signal — no
re-tuning of the carry signal itself.

## PRE-REGISTERED CEILING — the family is dead by arithmetic
Before any mechanism, computed what a PERFECT crash oracle could deliver on the
R2 flagship book (n=5680, 2004+):
- Zero out ALL 2008 losses (unattainable by any trailing rule): SR -0.004 -> 0.183.
- Zero out ALL 11 negative years (requires oracle knowledge): SR -> 0.517.
Gate is SR >= 1.0. No crash control can pass because the factor has no positive
drift to protect: the crash is not the disease, it is the only symptom of a
factor whose gross drift post-2004 is ~0 (R2: gross SR 0.106).

## (b) CROSS-VERIFY HUNT_INTERNATIONAL2 — CONFIRMED, no escalation
Script: campaign/scripts/HUNT_FXCARRY2_r3_crossverify.py, from their sleeve CSV
alone (agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R2_RS252_LS.csv).
- n=4469, 2008-11-04 -> 2026-08-12, no gaps >5d: matches their claim exactly.
- Recomputed SR 0.5641 vs claimed 0.564 (delta 0.000); ann 6.5%, mdd -27.6%.
- 7 neg years recomputed = claimed (2011 -13.1%, 2012 -11.0%, 2017 -8.6%,
  2022 -10.0%, 2024 -5.2%, 2025 -2.8%, 2026 -1.6%), worst -13.05% = claimed.
- corrChamp -0.0336 vs claimed -0.033. H1 0.572 / H2 0.557.
- T+1 leak probe: lag-1 autocorr -0.0075 (indistinguishable from noise; the
  R1-champion same-day-leak precedent would show strongly here). No leak signal.
- Gates re-grade: sr_ok False, yearly_ok False (7 neg), halves True, corr True.
Their negative is real and their numbers are honest. VERDICT: CONFIRMED_NEGATIVE.

## TDD: machinery locked BEFORE any performance number
First version of the stop state machine had a real bug — it wiped pre-breach
history and zeroed the breach day itself (test caught days_stopped=5680 on a
book that never should have stopped before 2008). Wrote failing tests first
(campaign/tests/test_hunt_fxcarry2_r3_tail.py), then fixed:
- dd_stop: state at t uses only data <= t; breach day realized, flat from t+1;
  re-entry mom63>0 from t+1; never-breaching stop is byte-identical to baseline.
- crash-cap: hit day realized, exactly `halt` flat days i+1..i+halt, no double
  shift, past intact.
- monthly_losscap: breaching month m scales exactly month m+1, month m untouched
  (test also caught my own synthetic-calendar bug: Jan-2004 has 22 bdays, not 20).
6/6 green. All numbers below come from the corrected machinery.

## (a) RESULTS — ALL THREE CHARTERED MECHANISMS FAIL (post-2004 only, n=5680)
Baseline: R2 flagship SR -0.004, ann -0.18%, 11 negyr, worst -19.4% (2008).

| variant | net SR | ann | negyr | worst yr | H1/H2 | corrChamp | scramble p | verdict |
|---|---|---|---|---|---|---|---|---|
| R2 baseline (no control) | -0.004 | -0.18% | 11 | -19.4% | -0.13/+0.16 | 0.028 | 0.760 | FAIL |
| (i) dd-stop -10% + mom63 re-entry | -0.089 | -0.31% | 11 | -5.8% | -0.18/+0.03 | 0.020 | 0.910 | FAIL |
| (i) dd-stop -15% | -0.174 | -0.59% | 12 | -7.4% | - | - | - | FAIL |
| (ii) monthly loss-cap -3% halve | +0.062 | +0.18% | 11 | -12.1% | -0.07/+0.21 | 0.034 | 0.690 | FAIL |
| (ii) monthly loss-cap -5% halve | +0.006 | -0.12% | 11 | -18.3% | - | - | - | FAIL |
| (iii) EW 10%VT + crash-cap -2%/10d | -0.010 | -0.55% | 11 | -19.8% | -0.12/+0.10 | 0.029 | 0.555 | FAIL |
| (iii-b) inv-vol equal-risk + cap -2% | -0.095 | -0.59% | 13 | -19.7% | -0.24/+0.08 | 0.032 | - | FAIL |
| (iii-b) inv-vol equal-risk + cap -3% | -0.097 | -0.64% | 13 | -20.4% | -0.23/+0.08 | 0.027 | - | FAIL |

Plateaus (pre-registered grids): dd-stop {-0.05:0.007, -0.075:0.022, -0.10:-0.089,
-0.15:-0.174, -0.20:-0.285} best -0.075@0.022 (SR<<1.0 everywhere, no plateau);
loss-cap {-0.01:-0.048, -0.02:0.046, -0.03:0.062, -0.05:0.006, -0.08:0.006} best
-0.03@0.062 (a spike, not a plateau: -0.02 and -0.05 collapse).

## WHY TAIL CONTROL FAILS HERE (mechanism, not noise)
1. The stop cuts MORE gross P&L than crash losses. -10% stop goes flat for 3303
   of 5680 days (58% of the sample) because the book's drawdown hovers near -10%
   through 2009-2016's chop; SR falls -0.004 -> -0.089. Stop re-entry whipsaw
   (re-enter on mom63>0, re-breach, re-pay 6.4bps FULL |dW|) compounds it.
2. Scramble p rises with control quality (0.760 -> 0.910 for the -10% stop):
   conditioning on realized drawdown has ZERO timing information — the stopped
   book is statistically indistinguishable from a randomly-timed flat book.
3. Every variant keeps 11+ negative years. Worst-year improves only when the
   control is big enough to also kill the positive years (dd-stop -10%: worst
   -5.8% but ann -0.31% and H1 -0.18).
4. Decorrelation remains trivially satisfied (|corr| 0.020-0.034) — the only
   gate any variant passes, and meaningless at SR<0.1.

## HONEST READING
Tail control cannot rescue a factor with no drift. The R2 crash-tail was the
*symptom*; the disease is that post-2004 IRSTCI01 month-end rate differentials
carry no premium in this 8-pair universe (R2 gross SR 0.106 pre-cost). The
charter's three mechanisms were implemented exactly, on TDD-locked machinery,
with pre-registered params, era discipline (post-2004 only), and honest scramble
tests — all FAIL all performance gates. Per contract 5, this is a negative
result, not an iteration loop: the family stays dead.

## Artifacts
- campaign/scripts/HUNT_FXCARRY2_r3_crossverify.py (charter b, reproducible)
- campaign/scripts/HUNT_FXCARRY2_round3.py (charter a, reproducible)
- campaign/tests/test_hunt_fxcarry2_r3_tail.py (6/6 green, machinery locks)
- campaign/agents/chief/coord/HUNT_FXCARRY2/sleeves/FXCARRY2_R3_ddstop10_carry_EW.csv + .meta
  (charter-headline variant, FAIL, saved per contract 4)
- DEAD_IDEAS row appended (HUNT_FXCARRY2-R3, tail-controlled carry): future rounds
  should not re-test drawdown/loss-cap/crash-cap overlays on this signal — the
  oracle-ceiling arithmetic (max achievable SR 0.183-0.517 << 1.0) already rules
  out the entire tail-control family, not just these three configs.

ROUND 3 DONE

## ROUND 4 (2026-09-08, audit rotation per charter) — verdict: 6/6 DEAD_IDEAS rows REPRODUCED (0 diverged, 0 unreproducible among those audited) + 1 BONUS missing-script finding (row 105). No fraud found. My family stays closed; no engines run in HUNT_FXCARRY2.

Note on process: a prior session left unreported r4 artifacts in work_r4/ (logs 19:26-23:55 Sep 7).
I did NOT trust them: every number below comes from runs I executed myself this round, from the
cited scripts, with sha256 provenance before/after. Prior-session logs were used only as
cross-checks; where they exist they agree with my runs.

Champion of record re-verified FIRST (campaign/bt/verify_champion_r3_cmd.sh, exit 0, 7/7 checks ok:
weights_repro max_dev 2.2e-16, byte_repro 1.1e-16, cost_reconciliation full_dw ratio 1.0000,
causality nav.shift(1) + 7/7 truncation probes dev 0.0, gross 1.600<=1.6, yearly 0 neg, mdd -6.69%).
Headline recomputed from the committed CSV: geo ann 37.195% / SR 3.181 / MDD -6.69% / 0 neg yrs /
worst yr +7.3%. Matches charter exactly.

AUDIT PROTOCOL (no writes to other agents' dirs):
- sha256'd all 56 files in HUNT_TREASFUT/HUNT_FF2/HUNT_CMDT2 sleeves + 10 cited scripts/screens
  BEFORE; re-hashed AFTER: all byte-identical (work_r4/audit_r4_fxc2/sha_otherdirs_before.txt).
- Scripts that hard-code save paths into other agents' dirs were copied to my workspace with the
  OUTPUT PATH patched only (TREASFUT: 1 line, save dir). FF2 final1.py mirrored with its relative
  ../sleeves layout so the identical code ran in my tree. No logic edits anywhere.
- Verdicts below = per-row reproduced / diverged / unreproducible, with my fresh numbers vs the row.

| row | family | verdict | my numbers vs cited |
|---|---|---|---|
| 59 | TREASFUT 2s10s steepener | REPRODUCED (exact) | curve2s10s_k21 SR -0.11 H1/H2 0.92/-1.45 31neg worst -6.2% cA6R7 0.178; scan-best k126 1.12 H1/H2 1.96/0.11 SR_08+ -0.22 cA6R7 0.216>0.15; naive -0.82 sym -2.50; tipsrev_N252 -0.11; fly_N504 -0.78; intlcarry3 lag0/lag1 0.77/0.70 corrChamp 0.310/0.319 FAIL corr - ALL MATCH to 3rd decimal |
| 53 | TFF trader-category | REPRODUCED (exact) | 156 variants; best dow_emini levfade_DIA 0.275 6neg worst -6.6% (=lev_money_fade row); DIFF best gbp 0.203 8neg; sr>=0.6:0 sr>=0.3:0 sr>0:50 - ALL MATCH |
| 63 | COT2 cross-section/fade/mirror | REPRODUCED (3rd-decimal data-vintage drift) | fresh hunt_r1: 19/19 FAIL, pm lb8 0.027 (rec +0.031), k2 -0.579 (rec -0.581), sw-follow lb12 mirror 0.280 halves(-0.20,+0.59) negyr 4 scram 0.687 (rec 0.287 (-0.14,+0.58) 4 0.652). Drift cause VERIFIED: tools/quant/data/more_cot/*.csv rebuilt Sep 7 17:06:52, after their R1 run (hunt_r1.py mtime 00:56) - data vintage, not fraud; verdicts unchanged, drift <=0.007 SR |
| 84/75 | CMDT2-R2 COT-gated commodity mom | REPRODUCED (exact) | main: 9m k2 thr0.2 SR 0.25 best (PASS=False), ungated 0.21, 12m negative, CPER 252d 0.23, CPER/GLD -0.41/-0.52/-0.60, WTI-Brent -0.38..+0.00, UNG seasonal -0.08 (0/32 pass). round2_ext: peak 0.246 at (9m,k2,thr0.2), plateau 2/5 neighbors>=80% (their claim: 2/5); ablation gate deltas +0.027..+0.165 (their +0.03..+0.16) |
| 49 | CIT_AG ag z-scores | REPRODUCED (1 bit-rot caveat) | screen exact: 156 variants, top lean_hogs noncomm->SOYB 0.705, 11 rows >=0.3; coherent-mapping deep_check: 0.543 art. cell, param nbhd 0.440..0.580 (their 0.44..0.58); PCPS PSOYB 21d 0.464 (their 0.465). CAVEAT: deep_check.py scramble now returns (nan, nan) where FINDINGS cites p=0.005 - cause: bt/gates.py scramble_positions NaN fail-closed guard (AUDIT_GATES2 R2) POSTDATES their run; real-SR baseline recomputes fine by hand (0.606); their verdict rests on yearly+coherence gates, which reproduce |
| 2+110 | FF2 factor premia + corrections | REPRODUCED (byte-exact + exact) | final1.py mirror: sha 1adcb4b7fbbdc079 / 55a9b3e5661bd871 = IDENTICAL to delivered sleeves + row-110 prefixes. recon1: 44 cells, best tsmom_MKT_lb126_LF 0.58 (their 0.58); RAW 2008+ MKT +0.57 SMB -0.00 HML -0.01 MOM +0.11 (exact); recon2 decile books: HML_from_6pf -0.02, SMB -0.13, OP_Hi30_Lo30 +0.29 halves 0.34/0.24, INV +0.05, MomDec_HiLo +0.16, rotation -0.02 (ALL exact). EL factor momentum: cited repo script prints 2008+ SR -0.09 in my run vs documented -0.04 (minor drift, both dead-negative; 1963+ +0.19 confirms post-GFC decay) |

BONUS FINDING (fraud-catch duty, not one of my 6): DEAD_IDEAS row 105 (CREDIT2-R3 static HY
carry harvest, BAA10Y/DGS10 TR-proxy) has NO saved script and NO sleeve CSV anywhere in
HUNT_CREDIT2 - the numbers exist only in FINDINGS prose. The DECISIVE raw number does reproduce
exactly from data + the documented construction (my own re-derivation using their total_return()
plumbing only: raw 1:1 differential arith -1.90%/yr, n=4882, 2007-04-12..2026-09-04, 10 negyr -
exact match to the row), and the gate battery that produced netSR -0.30 is standard and
consistent with the raw number. But per the charter's own bar ("reproduce each from its cited
script"), row 105 should be flagged: cited-script-missing. Name the file: no file exists; nearest
evidence campaign/agents/chief/coord/HUNT_CREDIT2/FINDINGS.md lines 97-103. Suggested ledger note:
add repro script or downgrade row 105 to prose-only provenance. (Note: HUNT_CREDIT2_round3.py's
own carry leg uses BAMLEMHBHYCRPIOAS 2023+ n=753, not BAA10Y - different book.)

Also verified while auditing: bt/gates.py scramble_positions fail-closed NaN guard is the reason
several older scripts' scramble cells now print nan (CIT_AG deep_check). This is a KNOWN, documented
honesty fix, not a regression; older recorded p-values predate the guard and remain valid as
recorded, but re-runs of old scripts will report (nan, nan) on any NaN-contaminated input.

Artifacts (all mine, all reproducible):
- work_r4/audit_r4_fxc2/treas/ (patched script + r4_run.log + sleeves/)
- work_r4/audit_r4_fxc2/ff2/ (mirror final1/recon1/recon2 + logs + sleeves/ with matching shas)
- work_r4/audit_r4_fxc2/cit/, tff/, cot2/, cmdt2/ (r4_run.log each; cot2/sw_follow_mirror.py)
- work_r4/audit_r4_fxc2/sha_otherdirs_before.txt (provenance: 66 entries, all verified after)
- work_r4/r4_champion_verify.json (7/7 ok)

No new engines were run in my closed FX-carry family. No champion changes proposed. DEAD_IDEAS
verdicts for all audited rows stand as recorded.

ROUND 4 DONE


# HUNT_FXCARRY2 — ROUND 5 FINDINGS (2026-09-08)

Charter: (a) reproduce WHY CFX4 sits at exactly 0.000 relw in RAWEW13v2_IS_SR_weights.csv,
honestly from CFX4_DTF21_63_raw_daily.csv + its meta; (b) pre-registered NEW CORNER:
Frankfurter FX daily (keyless, live per altdata5) — carry/trend family, full V2 battery.
READ FIRST done: GATES_CONTRACT_V2.md (ratified 03:1x) + DEAD_IDEAS.csv recount = 129 rows
at round start (charter said 120 at R4-end; dynamic per V2 preamble), 130 after my R5 append.

## Champion of record re-verified FIRST
verify_champion_r3_cmd.sh exit 0, ok=true 7/7 checks (weights_repro 2.22e-16, byte_repro
1.11e-16, cost_reconciliation full_dw ratio 1.0000, causality nav.shift(1) + 7/7 truncation
probes dev 0.0, gross 1.6000<=1.6, yearly 0 neg worst +7.31%, mdd -6.69%). sha 4358dfab95679b97
unchanged. Matches the charter's stated numbers exactly.

## (a) CFX4 ZERO-WEIGHT — REPRODUCED, ALL 9 CHECKS PASS (script exits 0)
Script: campaign/scripts/HUNT_FXCARRY2_round5_cfx4repro.py (reproducible from raw artifacts,
no trust of CAMP_COST R4 prose). File sha256[:16] 0e448b301fba08c7, cols=[ret].
- A. CFX4 span 2019-09-10..2026-08-05, n=1799 — first obs AFTER the builder IS_END.
- B. Builder rawew13v2_build.py: IS_END=2017-01-01, P=0.55, is_sr() len<200 branch = 200.
- C. CFX4 obs inside the IS window (index < 2017-01-01): **0** (< 200).
- D. is_sr() -> 0.0; relw = max(0,0)^0.55 = 0.0 = committed weights row (CFX4,0.0); every
  other slot relw > 0 (min 0.6512 carryv2).
- E. Algebraic inertness: builder rebuild with the CFX4 slot matches the committed champion
  to maxdev 9.996e-17; rebuilding with the slot DROPPED entirely: maxdev 1.023e-16 — both
  float noise. Zero-relw slot contributes 0 to numerator AND denominator (nav.shift(1)
  causal builder, byte-faithful).
- F. The meta headline recomputes from the raw CSV: SR_d 1.9106, ann_geo 14.91% on
  2019-09-10..2026-08-05 — the sleeve is ALIVE (own-span SR ~1.9) but structurally
  unweightable by an IS-only rule requiring pre-2017 data. 100% of its history is OOS.
VERDICT: mechanism reproduced exactly — relw=0.0 is the builder's len<200 branch firing on
an EMPTY pre-2017 IS window, not a data or fraud issue; the slot is algebraically inert.

## (b) FRANKFURTER CORNER — DATA (fetched this round, keyless, live)
Script: campaign/scripts/HUNT_FXCARRY2_round5_fetch.py ->
work_r5/frankfurter/ (46 per-ccy CSVs + manifest.csv + fetch_meta.json + FRANKFURTER_EUR_wide.csv).
- Source api.frankfurter.dev/v1 (ECB euro reference rates), 28 year-chunks, 7087 dated rows,
  1999-01-04..2026-09-07. 46 currencies (26 full-span 1999+; late listings CNY/BRL/INR/ILS
  2000-01+; defeaters CYP/EEK/GRD/LTL/LVL/MTL/ROL/SIT/SKK/TRL pre-euro, RUB to 2022-03,
  BGN to 2025-12). Max gap 5d (=weekend; ECB TARGET calendar is the native one). sha256 per
  series in manifest.csv. span_class: full-span series start 1999 => pre2007-admissible span,
  but the R2-comparable carry universe needs FRED rates that end 2026-06; every table below
  carries its span (V2 s9).

EXPRESSIBILITY DISCLOSURE (artifact-pinned by tests): Frankfurter is SPOT-ONLY — no forward
points, deposits or short rates are published, so a Frankfurter-native carry book CANNOT be
built. The chartered carry corner is therefore constructed as: Frankfurter USD-cross panel
(9 currencies: EUR AUD CAD CHF GBP JPY KRW NOK NZD) + FRED IRSTCI01 monthly immediate rates
from my R2 fetch (more_fx/, PIT +1-month convention: month-m print usable from m+1), with
the interest-rate-parity accrual (r_ccy - r_usd)/252 credited daily on held legs and the USD
leg earning exactly 0. Trend needs no rates and runs on the spot panel. This is the same
rate source family as the R2/R3 negatives — the NEW content of the corner is the 46-ccy
Frankfurter panel itself (9-currency universe incl. EUR/KRW vs R2's 8 DEX pairs), the accrual
sign convention per funding leg, and the full V2 battery.

## (b) ENGINE — TDD FIRST, 12/12 GREEN (campaign/tests/test_hunt_fxcarry2_r5.py)
Written RED before any performance number (R3 precedent). The locks caught THREE real bugs
before any number was recorded:
 1. Zero-book scalarization: sig = signed net exposure of a dollar-neutral basket = 0 ->
    gates.run judged an empty book (corr nan, negyr 0, SR -2.17 on nothing). Fixed: sig =
    HELD GROSS UNITS (sum|We|), r_pu = net/sig; test pins sig*r_pu == net to 1e-15 on live
    days for both families.
 2. VT scale input: vol_target_scale fed the weight-gross series (constant 2.0 -> std 0 ->
    scale pinned at the 0.2 floor -> book at 1/5 size; earlier v1 run also showed the
    cap-blowing variant). Fixed: scale input = portfolio gross return series (campaign
    convention); test pins realized VT10 book vol in (3%,20%).
 3. Missing carry accrual + phantom USD leg: v1 credited NO carry (mislabeled spot book) and
    the USD "funding leg" secretly held EUR/USD spot. Fixed: fx_total_returns() adds the
    (r_ccy - r_usd)/252 accrual per leg and zeroes the USD leg; tests pin both (mid-June
    accrual must equal the MAY print over 252 — the PIT convention, exact to 1e-12).
Additional locks: T+1 effective weights == decision weights shifted 1; truncation probe
(truncated-sample rebuild byte-identical on the overlap, 1e-12); zero-signal book exactly
flat; rates file inventory (carry expressibility); V2 battery wiring (leak/leak_ok/
beats_passive keys present, sig feeds the scramble).
A FOURTH defect was caught by cross-checking outputs against the engine AFTER the battery
ran: an Edit to run_all duplicated a loop chunk leaving R bound to R_spot for every config,
so one committed artifact set (06:40) carried carry-book numbers with NO accrual (SR
-0.525..-0.946). The corrupted function was rewritten, stale pyc cleared, suite re-run
12/12, and the battery re-executed; saved CSVs were verified == final JSON (max delta 0.0)
and the metas carry a PROVENANCE note. Verdict unchanged either way (all FAIL).

## (b) RESULTS — ALL 9 CONFIGS FAIL THE V2 BATTERY (0/9; net of 6.4bps FULL |dW| +
0.5%/yr borrow + 4.5%*max(gross-1,0) margin, T+1, VT10 trailing cap3, 1999-2026 span)
Carry HML (12m-mean IRSTCI01 differential, long top vs short bottom, EW, accrual credited):
| config | n | SR | ann | MDD | H1/H2 | negyr | worst yr | corrChamp | scr_p | mtrx_p | bp_ok | leak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CARRY_EWtop2_12m | 6958 | -0.129 | -1.99% | -54.1% | -0.03/-0.35 | 16 | -34.5% | +0.007 | 0.725 | 0.010 | F | False |
| CARRY_EWtop3_12m | 6958 | -0.381 | -4.60% | -74.4% | -0.31/-0.51 | 21 | -38.8% | -0.032 | 0.845 | 0.035 | F | False |
| CARRY_EWtop4_12m | 6958 | -0.567 | -6.36% | -85.1% | -0.45/-0.76 | 22 | -36.5% | -0.040 | 0.805 | 0.015 | F | False |
Trend (monthly TS momentum sign on USD crosses, spot-only):
| config | n | SR | ann | MDD | H1/H2 | negyr | worst yr | corrChamp | scr_p | mtrx_p | bp_ok | leak |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TREND_mom63_LS | 7002 | -1.248 | -7.11% | -87.2% | -0.31/-1.10 | 23 | -12.8% | +0.011 | 1.000 | 0.110 | F | False |
| TREND_mom63_LF | 7002 | -0.509 | -2.80% | -59.4% | +0.19/-0.47 | 15 | -11.0% | -0.005 | 0.755 | 0.170 | F | False |
| TREND_mom126_LS | 6937 | -1.040 | -6.30% | -83.3% | -0.10/-0.96 | 23 | -13.1% | -0.010 | 0.995 | 0.015 | F | False |
| TREND_mom126_LF | 6937 | -0.621 | -3.21% | -60.1% | +0.15/-0.76 | 17 | -10.9% | -0.015 | 0.855 | 0.385 | F | False |
| TREND_mom252_LS | 6807 | -1.537 | -9.49% | -93.4% | -0.83/-1.28 | 25 | -15.3% | -0.007 | 1.000 | 0.875 | F | **True** (-0.231) |
| TREND_mom252_LF | 6807 | -0.829 | -4.56% | -72.3% | -0.40/-0.61 | 20 | -11.3% | -0.013 | 0.985 | 0.610 | F | False |
Battery detail per V2: gates.run carried sig= + leak_check=True + beats_passive trio +
ref=champion (sha 4358dfab95679b97) on every config. beats_passive 0/9 (best passive
spy_bh SR 0.533; margins -0.66..-1.55). Halves 0/9 (h_min 0.5 never approached). Yearly
0/9 (15-25 neg years vs <=2 allowed). corr gate moot (|corr|<=0.04). The mom252_LS leak
flag True is the probe firing on a same-period |corr| 0.231 of a LOSING book (SR -1.54) —
a failing sleeve either way; disclosed, not excused.

## Era discipline (post-2004 only counts; pre-2004 may support nothing)
Carry era SRs (full-span already negative, so nothing hinges on the early era):
| config | 1999+ | 2004+ | 2008+ | 2015+ | 2021+ |
|---|---|---|---|---|---|
| top2 | -0.129 | -0.125 | -0.251 | -0.416 | -0.177 |
| top3 | -0.381 | -0.395 | -0.473 | -0.595 | -0.382 |
| top4 | -0.567 | -0.550 | -0.607 | -0.747 | -0.505 |
No era of the carry book is positive at any breadth; the 2000s (the only era that ever
approached zero, +0.32 at top2) is exactly the pre-2008 window the era rule excludes from
supporting a pass. The chartered TimesFM bar (>=8y of effect) fails: there is NO era with
an effect, let alone two.

## WHY THE CORNER IS DEAD (mechanism, consistent with R2/R3)
1. The 2008 carry crash is present in the new universe too: top2 book 2008 = -38.8% gross
  (-25.7% on the book path before the 2009 bounce), with the per-leg attribution showing
  the classic unwind (NOK -9.6%, NZD -7.3%, JPY -6.9%, AUD -5.7% contribution). The
  Frankfurter panel reproduces the R2 mechanism rather than escaping it.
2. Accrual drift is tiny against the tails: mean |r_c - r_us| ~ 1.45%/yr across the panel
  — an order of magnitude below the -34..-39% worst years. Same arithmetic as the R3
  oracle ceiling: no crash control can rescue it, so none was tried (no re-tune of a dead
  family per contract s5).
3. Trend on the same panel is likewise unpaid post-1999 at every lookback (63/126/252) in
  both LS and LF forms — 0 positive era SRs anywhere in the grid, scramble p 0.755-1.000
  (zero timing information). Monthly-rebalance granularity was chosen a-priori to match the
  R2/R3 family convention; no frequency was swept to hunt a pass.
4. No plateau is possible: the natural breadth grid (top 2/3/4) is monotonically WORSE with
  breadth and negative everywhere — nothing clears SR>=1.0 at any neighbor, so per contract
  s5 this is logged dead rather than iterated.

## DEAD_IDEAS row appended (130 total now)
HUNT_FXCARRY2-R5: Frankfurter 46-ccy panel carry HML + trend, 9 configs, full V2 battery,
0/9 pass, with era table and provenance note. Future rounds: do not re-test this family on
this source without a pre-registered corner that changes the ECONOMICS (e.g. a genuine
forward/points or deposit-rate source for the EM legs — Frankfurter has none), not just
breadth/lookback knobs.

## Artifacts
- campaign/scripts/HUNT_FXCARRY2_round5_cfx4repro.py (charter a, exit-0 reproduction)
- campaign/scripts/HUNT_FXCARRY2_round5_fetch.py + work_r5/frankfurter/ (46 CSVs,
  manifest.csv with per-series sha256, fetch_meta.json, FRANKFURTER_EUR_wide.csv 7087x46)
- campaign/scripts/HUNT_FXCARRY2_round5.py (engine; carry+trend; V2 battery; 12/12 tests
  in campaign/tests/test_hunt_fxcarry2_r5.py)
- work_r5/r5_results.json (final battery output; sleeves FXCARRY2_R5_*.csv + .meta x9 in
  sleeves/, all FAILED_NO_PROMOTION, each with leak dict, beats_passive detail, era table,
  vintage-pinned champion sha, and the 06:40-run provenance note)
- DEAD_IDEAS.csv row HUNT_FXCARRY2-R5 (130th)

## HONEST READING
(a) CFX4's 0.000 weight is a data-spans-vs-IS-window artifact, reproduced exactly: the
sleeve is good (SR 1.91 on its own 2019+ span) and its slot is inert in the committed
champion. (b) The Frankfurter corner is a genuine negative: on a NEW 46-currency keyless
source fetched this round, with the accrual machinery correct (12/12 TDD locks), FX carry
HML and FX trend fail every performance gate of the V2 battery on every era sub-span —
IS-SR <= 0 IS the result, as the charter instructed. The 8-pair FRED universe (R2/R3) and
the 9-ccy ECB-panel universe (R5) agree: post-GFC FX carry/trend in G10-adjacent space
carries no harvestable premium at campaign costs. Family stays closed.

ROUND 5 DONE


# HUNT_FXCARRY2 — ROUND 6 FINDINGS (2026-09-08)

CONSOLIDATION round. READ FIRST done: GATES_CONTRACT_V2.md (in force; leak_check default-ON
post-flip commit 539f50e) + DEAD_IDEAS.csv recounted at round start = **143 data rows**
(charter said 137 at R5-end; dynamic per contract preamble). Champion of record untouched:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha256:16 4358dfab95679b97 re-verified this
session. Charter (c) respected: NO new FX-carry engine was run (no pre-registered
data-backed economic gap exists — Frankfurter is spot-only, the R2/R3/R5 negatives stand).

## (a) FRAUD-CATCH CROSS-VERIFICATION of HUNT_TREASFUT R5 — verdict CONFIRMED, 3 defects found

Charter asked: reproduce HUNT_TREASFUT's R5 verdicts from published artifacts with MY OWN
code (charter (a) names AUDIT_CHAMP2's GOAL80 repro; TREASFUT is the cross-verify target
actually assigned to me in the R6 pattern — R3/R4 rotation precedent). I rebuilt all 19 R5
books from raw inputs (tauctions.csv sha b0e243c4e4681e32 exact-match to their pin, n=7857;
DGS2/5/10/30 synth-TR, my own loaders — zero import of any HUNT_TREASFUT module).
Script: campaign/scripts/HUNT_FXCARRY2_r6_treasfut_repro.py (also in
work_r6/fxc2_r6_treasfut_repro.py); scorecard work_r6/r6_treasfut_repro_scorecard.json.

CONFIRMED EXACT (no fraud — every published number reproduces from a stated or
reconstructible convention):
- 15/15 primary sleeve CSVs byte-match my own honest single-T+1 rebuild: max dev 9.99e-17
  (POST5_30_long shown first: dev 9.888e-17); published positions CSVs match my effective
  weights to 0.0 exactly on all 15.
- All 19 .meta net_sr cells reproduce to 4dp from a DOUBLE net_of rebuild 19/19 (see
  defect #1), all 19 h1/h2/negyr/worst-year/corr cells reproduce to 4dp on the sig*r_pu
  battery feed 19/19, era cells 19/19 on the double book.
- Drift controls reproduce: post-window 5d drift 15.2/22.7/16.8/49.1bp vs all-days
  10.3/10.8/11.3/13.8bp for 2/5/10/30y (published 15.2/22.7/16.8/49.1 and 10.3/10.8/11.3/
  13.8 — identical); my Welch excess t = 1.93/3.04/0.74/1.84 vs published 2.01/3.20/0.79/
  1.84 (same conclusions: 2y/5y/30y significant, 10y not); published drift tables match my
  rebuild max dev 9.97e-17; 30y weak/strong conditional drift 28.5/80.6bp per 5d =
  published 0.285%/0.806% EXACT (the conditioner-anti-works finding stands).
- Honest leak probes on my rebuild: |same-period corr(pos_t, r_t)| <= 0.140 across all 19
  books (worst COND5_30 +0.1390) — consistent with their leak_ok True 19/19 claims.
- Row 61 (their R1 intl carry) cells re-verified from TREASFUT_intlcarry3_lag1_NEG.csv:
  SRm*sqrt12 = 0.7004 (claim 0.70), 13/38 neg years (claim 13/38) — exact.
- Book inventory exact: 370/315/153/92 fresh-issue auctions (2/5/10/30y), 30y suspension
  2006-02..2011-02 present; 2015-01-28 2y dedup-to-largest rule reproduces.

DEFECT #1 (CONVENTION, material but verdict-preserving — ESCALATED): the battery judged a
DOUBLE net_of book. Their per_unit_feed() calls net_of() on ALREADY-EFFECTIVE weights
(We = W.shift(1) VT-scaled), applying a second shift(1) + second VT10 + second cost pass.
Published CSVs = single-T+1 books; metas + FINDINGS table = double books. Honest numbers
differ materially: POST5_2 +0.291 honest vs +0.128 published; POST5_5 +0.216 vs -0.325
(SIGN FLIP); POST5_30 +0.441 vs +0.468; PRE5_30 -0.500 vs -0.182; POST10_10 +0.338 vs
+0.253. Family best (POST5_30) honest SR 0.441 < spy_bh matched-span 0.517, so its
nominal beats-passive "PASS by +0.0097" (meta: candidate 0.5267 vs spy 0.5169) is an
artifact of the double book's slightly different span/vol — honest verdict LOSES to
passive. ALL 19 V2 verdicts unchanged FAIL on honest books: max honest SR 0.441 << 1.0,
0/19 pass any acceptance arm, 0/19 beat spy_bh matched, halves/era fail everywhere
(honest era sign flips on the 2y/5y post books: +0.82/-0.32 and +0.52/-0.08). My own R5
metas carry the same r_eff-feed convention for H1/H2/negyr/worst (disclosed there in
FINDINGS, "r_pu convention"), so this is a FLEET-WIDE feed-convention pattern, not
TREASFUT-specific misconduct; the acceptance-relevant fact (0/19 pass) is identical
either way.

DEFECT #2 (ARTIFACT BUG — ESCALATED): the 4 plateau-neighbor CSVs TREASFUT5_POST3_10_long,
TREASFUT5_POST10_10_long, TREASFUT5_COND3_10, TREASFUT5_COND10_10 are byte-identical to
their k=5 siblings (sha-verified TRUE,TRUE,TRUE,TRUE) and their metas record k=5 —
save_artifacts() re-derived every published CSV from K_APRIORI regardless of the book's
own k. Their FINDINGS plateau numbers (POST3 -0.335, POST10 +0.253, COND3 -0.537, COND10
-0.147) ARE reproducible from the double-net rebuild (mine: -0.335/+0.253/-0.537/-0.147)
but NOT from the published CSVs (those print the k=5 books: +0.198/-0.272 twice). Plateau
FAIL verdict correct either way (post grid not on a plateau: k3 -0.335 / k5 +0.207 /
k10 +0.253 honest double-net).

DEFECT #3 (LEDGER ROW MISSING — ESCALATED TO COORDINATOR): TREASFUT R5 FINDINGS states
"DEAD_IDEAS.csv row 130 appended by me (129->130)" but NO auction-CYCLE/TREASFUT-R5 row
exists in any state of the ledger: current 143 rows (0 keyword hits for auction-CYCLE/
TREASFUT-R5/tauctions/concession/when-issue), git pickaxe -S "auction-CYCLE" over ALL
history = 0 commits, and both RES_META snapshots (DEAD_IDEAS.snapshot_104755.csv and
.snapshot_clobbered.csv, Sep 8 10:47/10:56) = 0 hits. Most likely lost in the RES_BASIS
section-4 repair (a snapshot-restore clobber that dropped rows appended between the
snapshot and the clobber — my R5 row 126 survived it, theirs did not). I appended a
curation row recording this and the full verification; the coordinator owns the re-append
of the actual row (file is append-only for hunt agents). 143 -> 144 data rows after my
append (my row = HUNT_FXCARRY2-R6, "verified").

## (b) DEAD_IDEAS CURATION — FX/carry rows (10 rows re-verified, all evidence cells stand)

- Row 6 (HUNT_CARRYFX 8-pair carry): verdict consistent with my R2 supersession (row 64);
  no artifact regression possible (pre-ledger provenance era); row 64 re-measured from MY
  published sleeve: FXCARRY2_R2_carry_nominal_EW.csv 2004+ n=5680 SR -0.0043 ann -0.18%
  11 negyr worst -19.40% — EXACT match to the row's cells.
- Row 94 (my R3 tail-controlled carry): ddstop10 CSV 2004+ SR -0.0894 vs row cell "-0.089"
  — exact.
- Row 126 (my R5 Frankfurter corner): all 9 sleeve CSVs re-measured with own code — SR
  cells exact on 9/9 (e.g. CARRY_EWtop2 -0.129, TREND_mom63_LF -0.509); H1/H2/negyr/worst
  in the .meta files are battery-feed (sig*r_pu) cells, reproduced exactly from the saved
  engine path (r_eff H1 +0.185 H2 -0.467 neg 15 worst -10.98% vs meta 0.19/-0.47/15/-11.0
  for mom63_LF); CSV-convention cells differ (H1 -0.203 H2 -0.843 neg 19 worst -13.0%) and
  are the honest-book numbers — disclosed convention, verdicts unchanged (all deeply
  negative). Era table in FINDINGS R5 (1999+/2004+/2008+/2015+/2021+ all negative) stands.
- Rows 17/33/34/61/63/104/105 (adjacent FX/carry-family rows from other agents): row 61
  verified exact above; rows 104/105 were flagged prose-only-provenance in my R4 audit and
  remain so (no change); 17/33/34/63 carry no testable artifact beyond what earlier
  rotations already confirmed — no discrepancies found.
- Era-table discipline note (from R5): the FX/carry family remains CLOSED post-2004 on
  every tested source (FRED 8-pair, Frankfurter 46-ccy); no era of any variant is positive,
  so no re-test is warranted without a NEW economic input (a genuine forward-points or
  PIT deposit-rate source for the legs — none exists keyless on the current roster).

## Charter compliance
No bt/ touches; no campaign/*.md touches; champion untouched (sha 4358dfab95679b97); only
my dir (work_r6/, scripts copy) + one append-only DEAD_IDEAS curation row. No new FX-carry
corner (charter c). Every number above from a saved script run this session.

## Artifacts
- campaign/scripts/HUNT_FXCARRY2_r6_treasfut_repro.py (independent TREASFUT R5 rebuild)
- work_r6/fxc2_r6_treasfut_repro.py (same, canonical location)
- work_r6/r6_treasfut_repro_scorecard.json (all 19 books x all cells + drift controls)
- DEAD_IDEAS.csv row HUNT_FXCARRY2-R6. COUNT DISCLOSURE (dynamic-ledger, concurrent
  writers): round-start recount 143 data rows; at my append time the coordinator's
  mid-session dedup (file mtime 13:49, .bak_standup1300) had moved it to 140, so my row
  landed as data row 140 (0-indexed) / 141 total; final file state verified 141 data
  rows, 0 duplicate (idea,src) pairs, all four FXCARRY2 rows + 5 TREASFUT rows intact.
  The DEFECT-#3 missing-row conclusion is unaffected: the TREASFUT-R5 row is absent from
  ALL historical states (pickaxe + snapshots), not just the deduped one.

ROUND 6 DONE


# HUNT_FXCARRY2 — ROUND 7 FINDINGS (2026-09-08)

READ FIRST done: GATES_CONTRACT_V2.md (in force; leak_check default-ON post-flip; V3
per-class placebo treated as PROPOSAL, not depended on) + DEAD_IDEAS.csv recounted
MYSELF at round start = **147 data rows** (charter said 145-146 at R6-end; dynamic per
contract preamble). Champion of record untouched: sha256:16 4358dfab95679b97
(computed from the committed file myself), verify_champion_r3_cmd.sh re-run this session:
exit 0, ok=true 7/7 checks (weights_repro 2.2e-16, byte_repro 1.1e-16, cost_reconciliation
full_dw ratio 1.0000 / turnover 5.2622 bp/yr, causality nav.shift(1) + 7/7 truncation
probes dev 0.0, gross 1.6000<=1.6, yearly 0 neg worst +7.31%, mdd -6.69%). Pinned
work_r7/verify_champ_r7.json. bt suite re-run this session from repo root: **426 passed /
0 failed**, 1 skipped (matches R6 close).

## (a) FRAUD-CATCH AUDIT of HUNT_COT2-R6 — verdict: CONFIRMED, ZERO FRAUD, no escalation

Protocol (R4 precedent): sha256'd all 180 files in HUNT_COT2 + HUNT_CREDIT2 BEFORE any
run; re-hashed AFTER: every audited file byte-identical (2 additions + 1 FINDINGS append
during my window are the concurrent HUNT_CREDIT2-R7 agent's own round, whose tail I read —
their verdict block, not my writes; non-FINDINGS delta = NONE). My own wrapper re-ran
their pipeline with save_sleeve no-op'd AND SLEEVES patched to my dir (belt+braces;
nothing written into their tree).

1. PIPELINE RE-EXECUTION (charter: "confirm the scr_p capture + both verdicts reproduce"):
   my independent wrapper work_r7/audit_cot2/fxc2_r7_cot2repro.py re-ran CREDIT2's
   HUNT_CREDIT2_round5.py main() offline and captured the FULL battery incl. scr_p:
   **44/44 configs, 264/264 cross-check fields (local_sr/v2_sr/scr_p/leak_ok/bp_ok/pass)
   match COT2's r6/credit2_rerun_battery.json EXACTLY (0 mismatches at 1e-9)**. Best cell
   CRED5_nfci_credit_k26_i_vt v2_sr=+0.2063 **scr_p=0.185** (COT2's headline claim),
   leak_ok True, bp_ok False, pass False; 0/44 composite pass; local_sr range
   -1.878..+0.112. The scr_p=0.185 was never serialized in any CREDIT2 meta (re-grepped:
   0/44 metas contain scr_p; CREDIT2 FINDINGS quotes it twice) — COT2's "capture" claim
   CONFIRMED: my re-run reproduces it exactly.
2. "BOTH VERDICTS" = CMDT2-R5 propane + CREDIT2-R5 credit-carry CSV recomputes: my own
   code (work_r7/audit_cot2/fxc2_r7_csv_recompute.py, independent stats from the published
   sleeve CSVs, no COT2 code): **credit2 44 rows + cmdt2 28 rows = 72/72 books, 0 field
   mismatches** (SR/corr to 5e-4, negyr exact, worst to 0.05pp, n exact, H1/H2 to 0.005).
   Verdict rollup from the books: 0/44 + 0/28 with SR>=1.0; best CREDIT2 book
   nfci_credit_k26_i_vt SR 0.112 (meta-disclosed v2 gross 0.2063), best CMDT2 book
   prop_trend_w21_lo_vt SR 0.370 H1/H2 0.60/0.16 neg 8. Both all-fail verdicts STAND.
   COT2's |v2corr|<0.15 count claim (28/44) reproduced from my own battery run: 28/44.
   run_log gates-line count 44, corr|<0.15:True count 28 — their counts exact; the
   "26/44 stale prose" call is confirmed (the artifact number is 28).
3. COT2's row-135/136 correction cells re-measured from their own artifacts: mortgage
   family best local SR **-0.739 (CRED5_mortgap_w252_mom_vt)** = claim; nfci best +0.112
   = claim; nfci_risk best +0.079 = claim; cpois best **-0.826 (w252_compress_novt)** =
   claim; negyr ranges 20-25 / 13-17 / 14-17 / 22-24 = claim's "13-25". CMDT2
   corrected-battery v2sr range re-derived from /tmp/cmdt2_r5_v2_correct.json (still on
   disk): **-0.1847..+0.4219** = claim's "-0.185..+0.422"; leak_ok 28/28 = claim;
   bp_ok 0/28 = claim. Held-book cells: prop_spreadmr_w63_z2_vt CSV SR **-0.0168** (their
   -0.017), prop_trend_w21_lo_vt CSV **0.3701** (their 0.370). EXACT.
4. ROWS 139-142 VERBATIM CHECK (current indices drifted to 132-141 by the coordinator's
   mid-round 5-row macro dedup — content is what was checked, per COT2's own index-drift
   disclosure): COT2's 3 R6 rows (now 134/135/136) carry the exact numbers re-measured
   above; the corrected source rows themselves (CREDIT2-R5 row 119, CMDT2-R5 row 122)
   indeed still carry the superseded run-1 / distorted-battery cells COT2 documented
   (0.62 mortgage / 0.465+0.609 propane) — corrections warranted, verdicts unchanged
   either way (0/44 + 0/28 all-fail is STRONGER than the stale cells).
5. CONCURRENT-APPEND REPAIR (row 139 at COT2's write time, now 132): the fused state is
   NOT recoverable from git (file uncommitted; R6 fusion+repair both happened between the
   12:57 backup and the appends) — but the POST-REPAIR state is structurally perfect:
   **148-line file, 4 columns x all rows, 0 empty fields, 0 fused-source tokens
   (R6CURHUNT / HUNT_COT2-R6HUNT: none), 0 byte-dup (idea,src) pairs**, and the
   coordinator's bak_standup1300 snapshot independently confirms both halves of the
   story: it contains the 2 CMDT2-R6CUR rows (intact, 4-col) AND the 5-row byte-dup
   HUNT_MACRO2 block (USREC/T5YIFR/VIXCLS/TOTALSL/T10Y2Y-JOINT x2) that COT2/CMDT2
   documented and the coordinator deduped (current file: 0 dups, macro block appears
   once). No content lost on either side of the repair.
6. MINOR FINDING (not fraud, disclosed for the record, verdict-strengthening): COT2's
   row-136 cell "beats_passive 0/28 vs sixty_forty 0.566-0.573" understates the matched-
   span benchmark range — the corrected JSON's bp_best_sr spans **0.566..0.636** across
   the 28 books (w252/mr cells carry sixty_forty up to 0.636 on shorter matched spans).
   Direction unchanged: 0/28 beat their benchmark either way.

## (b) NO NEW FX-CARRY CORNER — roster re-survey; ONE genuine new economic input FOUND; corner run on it; HONEST NEGATIVE

Charter (b) said the family reopens ONLY on "a genuine forward-points or PIT deposit-rate
keyless source - re-survey the roster endpoints and cite what you checked if none exists".
Survey executed live this session (every probe a real endpoint call):

FORWARD POINTS — NONE keyless:
- ECB data-api EXR dataflow: spot-only. Control D.USD.EUR.SP00.A returns 200 with
  csvdata payload; forward-type content probes D.USD.EUR.{FP00,EN00,XEB00}.A all 404.
- Frankfurter (R5 source): spot-only, artifact-pinned in R5.
- FRED full-text search "foreign exchange forward": only AUINTDDL/AUINTDGT (RBA spot+
  forward TRANSACTION COUNTS, discontinued at 2006-12-29, latest obs verified).
- BIS stats: no FX-forward dataflow (WS_CBPOL policy rates = MONTHLY, wrong class).
- global-rates.com 404; exchangerate.host key-gated; CBOE/Deribit = vol not FX-forwards.

PIT DEPOSIT/OVERNIGHT DAILY RATES — YES, PARTIAL (this is the charter's second opening):
- FRED (rostered, keyed): DFF (US fed funds, daily, 1954+, n=26363), SOFR (2018-04+,
  n=2105), IUDSOIA = GBP SONIA (1997-01+, n=7498), ECBESTRVOLWGTTRMDMNRT = EUR €STR
  (2019-10+, n=1776), EONIARATE = EUR EONIA (1999-01..2021-12-29, n=5888, discontinued
  print), ECBDFR (EUR deposit-facility policy rate, 1999+, n=10113).
- NEW keyless endpoint found: Bank of Canada valet (bankofcanada.ca/valet):
  CORRA_WEIGHTED_MEAN_RATE live 2020-06-12..2026-09-03 (n=1551, latest 2.3002 verified)
  + CORRA.COMPOUNDED.INDEX. Not previously in any agent roster I can find.
- CHECKED AND NOT AVAILABLE (daily): JPY (BoJ stat-search endpoints 404; FRED has only
  monthly IRSTCI01JP*), AUD (rba.gov.au CSV 403 WAF), CHF (SNB data-portal cubes monthly
  avg-repo only; snbpol 404), NZD (rbnz.govt.nz 403), NOK (data.norges-bank.no SDMX 404
  on NOWA keys), KRW (FRED monthly only).

So the ONLY fully-spanned daily PIT deposit-rate panel is **USD/GBP/EUR from 1999**
(DFF + SONIA + EONIA->€STR). This is precisely the input my own R5 dead-row caveat
pre-authorized ("a genuine ... deposit-rate source for the legs - Frankfurter has none"),
so a corner on it is NOT a dead-family re-test: the ECONOMICS change (daily-vintage
overnight differentials + daily accrual instead of month-end immediate-rate prints).

Fetch: campaign/scripts/HUNT_FXCARRY2_round7_fetch.py -> work_r7/rates/ (8 CSVs +
manifest.json with per-series sha16: DFF 56dd59b687d95989, SONIA 3ceeb1b8bc1af5e0,
EONIA e4972a44f69f7d5c, ESTER 766d6541d764c1a8, ECBDFR 96112ce867855ccc, SOFR
504a1d5c67edf1dd, CORRA 9bea776d47d7b3e8; all PIT daily prints; EONIA->ESTER splice at
2022-01 disclosed - both ECB-designated overnight vintages).

CORNER (pre-registered before any backtest, family conventions pinned — NO param sweep):
252bd trailing-mean sign of the daily differential, month-end decision, T+1, ffilled
daily book, overnight accrual (r_ccy - r_usd)/252 per held leg (USD leg 0), spot on the
sha-pinned R5 Frankfurter USD/GBP panel, full V2 battery (sig=, leak_check=True,
beats_passive trio, ref=champion, scramble 200).

TDD FIRST — 8/8 green (campaign/tests/test_hunt_fxcarry2_r7.py, RED-first; caught THREE
real defects before any verdict was recorded):
 1. month-end-only book index annualized ~30-day moves as daily ones (first run "SR 8.3,
    worst yr 0.0%" — a sqrt(21) scaling artifact; lock test_07 forces the ffilled DAILY
    book where a 1-day holding period is a 1-day move);
 2. percent-vs-decimal units: FRED/BoC quote rates in PERCENT; accruing a percent rate
    /252 inflates PnL 100x (book mean +175%/yr; lock test_08 forces decimal conversion);
 3. month-end-vs-bday date misalignment in the manual accrual check (test_03 caught it
    before it could mask a wrong formula).
The locks are the only reason the first two are honest negatives instead of false
positives — an untested run of the first version would have printed SR 8.3.

RESULT — HONEST NEGATIVE, ALL GATES FAIL (book 1999-12-31..2021-12-31, n=5739 daily;
EUR leg's EONIA print ends 2021-12-29 which caps the span — disclosed, not patched):
- Held book: SR 0.073, ann ~+0.5%, H1 +0.29 / H2 -0.22 (halves gate FAIL), **12 negative
  years** (yearly gate FAIL, <=2 allowed), worst year -26.7% (2014), 2008 -0.3%, 2010
  -19.5%, 2017 -25.1%, 2020 -21.3%.
- Era discipline (post-2004 is the only era that counts): **post-2004 SR -0.198**
  (n=4695), 2008+ -0.197, 2015+ -0.108; only 2021+ is positive (+1.83 on n=259, the
  EONIA/ESTER negative-rate unwind tail — single short era, fails the >=8y span rule).
- Full V2 battery: v2sr 0.073, corr_champ +0.014 (decorrelation trivially fine, moot),
  scr_p 0.88 (zero timing information), leak_ok True (same-period corr -0.0139, p 0.29),
  beats_passive FAIL (spy_bh 0.516 on matched span), composite pass **False**.
- CAD/CORRA arm: fetched and disclosed, NOT made into a sleeve — 2020-06 inception =
  inception_fail per V2 9a, cannot support any pass regardless of outcome.
- Mechanism (consistent with R2/R5, now measured on daily PIT rates): the overnight
  differential accrual is worth ~2.0%/yr gross on the held book — real, but an order of
  magnitude below the -26.7% crash years; the daily-vintage upgrade to the rate INPUT
  does not change the economics of unhedged spot carry. The family stays CLOSED: forward
  points do not exist keyless anywhere on the roster, and the one genuine new input the
  charter's rule admits has now been tested to a clean negative at full V2 rigor.

DEAD_IDEAS row appended (HUNT_FXCARRY2-R7): ledger 147 -> **148 data rows**, before-sha16
bd09cc6df3089397, after-sha16 1e9be8a045813b2c (after repairing MY OWN append's extra
trailing newline, which had briefly created a blank 0-column row 150; 4 columns x all
rows, 0 dup (idea,src) pairs re-verified post-repair; my row carries the trailing
newline per discipline).

## Charter compliance
bt/ and campaign/*.md untouched; champion untouched (sha 4358dfab95679b97); other agents'
trees read-only (sha-verified before==after; the only deltas in their dirs during my
window are the concurrent HUNT_CREDIT2-R7 agent's own round-7 artifacts, verified as not
mine by reading their FINDINGS tail); all writes inside HUNT_FXCARRY2/ + my scripts/tests
+ one append-only DEAD_IDEAS row.

## Artifacts
- work_r7/audit_cot2/fxc2_r7_cot2repro.py + fxc2_r7_cot2repro.log +
  fxc2_r7_credit2_rerun_battery.json (charter a: 44-config pipeline re-execution, 264/264)
- work_r7/audit_cot2/fxc2_r7_csv_recompute.py + fxc2_r7_csv_recompute.json (72-book own-code recompute)
- work_r7/sha_cot2_credit2_{before,after}.txt (audit provenance: 180 files, no audited file changed)
- work_r7/champ_verify_r7.log + verify_champ_r7.json (champion 7/7 fresh)
- campaign/scripts/HUNT_FXCARRY2_round7_fetch.py + work_r7/rates/ (8 series + manifest.json, sha16-pinned)
- campaign/scripts/HUNT_FXCARRY2_round7.py + campaign/tests/test_hunt_fxcarry2_r7.py (8/8)
- work_r7/r7_overnight_carry_results.json + sleeves/FXCARRY2_R7_overnight_carry_GBP_EUR.csv + .meta
- DEAD_IDEAS row HUNT_FXCARRY2-R7 (148th data row)

ROUND 7 DONE
