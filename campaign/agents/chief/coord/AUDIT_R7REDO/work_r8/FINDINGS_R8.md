# AUDIT_R7REDO — Round 8 adversarial re-check of ROUND-7 REJECTIONS

Agent: AUDIT_R7REDO. Scope: `campaign/agents/chief/coord/AUDIT_R7REDO/` (nothing outside it was
modified; the champion and every existing sleeve are untouched).

**Champion of record, re-verified cold this round from its own build algebra:**
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv`
sha256[:16] `8d7e711e6d05a2b1`, n=4806, 2008-03-31..2026-08-28, ann 37.4923%, SR 3.1951,
MDD -6.6922%, 0 negative years. My independent rebuild of the 13-sleeve book reproduces the
committed bytes at max|dev| = **9.996e-17**.

**Vintage caveat that applies to every comparison below.** The R7 agents scored against champion
vintage `4358dfab95679b97` / n=4805 / end 2026-08-27. The champion of record is now
`8d7e711e6d05a2b1` / n=4806 / end 2026-08-28. My re-derivations therefore differ from the published
R7 numbers in the 3rd decimal (e.g. HOBR dAnn -0.9133pp vs their -0.9069pp). This is vintage drift,
not disagreement; no qualitative verdict below is sensitive to it.

**Method.** Every verdict comes from a script I ran, left on disk in `work_r8/`:
`s1_finra_span.py`, `s2_hobr_leverage.py`, `s3_hobr_admissible.py`, `s4_dvol_attack.py`,
`s5_treasfut_sweep.py`, `s6_fxcarry_attack.py`. Where a rejection has an engine, I imported the
agent's own module unmodified and reproduced its published headline FIRST, so the attack is on
their construction rather than on a paraphrase of it.

---

## 0. The R7 reject list (STEP 1)

`campaign/results/DEAD_IDEAS.csv` currently holds **153 data rows** (the charter said 154 — the
count moves by design; recount at round start). Seven rows carry an `-R7` source tag:

| # | row | idea | R7 status |
|---|---|---|---|
| 1 | 148 | Deribit DVOL + options chain (CRYPTO2 corner (a)) | blocked |
| 2 | 149 | FX carry via daily PIT overnight-deposit differentials | dead |
| 3 | 150 | FINRA bi-weekly equity short interest -> sector rotation | dead |
| 4 | 151 | ECB SDMX euro-area AAA yield-curve factors | dead |
| 5 | 152 | AUDIT R7 short/borrow curation refresh | verified (not a rejection) |
| 6 | 153 | AUDIT R7 2nd independent confirmation of FXCARRY2-R6 | verified (not a rejection) |
| 7 | 154 | RAWEW14_HOBR_CANDIDATE 14-sleeve book adoption | dead (adoption REJECTED) |

Sixteen agents ran a `work_r7/` round (AUDIT_FWBUGS, AUDIT_GATES2, CAMP_BORROW, CAMP_COST,
CAMP_SHORT, DATA_ETF_MORE, DATA_FREDMORE, HUNT_CREDIT2, HUNT_CRYPTO2, HUNT_FXCARRY2,
HUNT_INTERNATIONAL2, HUNT_MACRO2, HUNT_SECTOR2, HUNT_TIMESFM, HUNT_TREASFUT, HUNT_VOL2).
I attacked the **five actual rejections** (rows 148-151 and 154). Rows 152/153 are audit
confirmations, not rejections, and are out of scope.

---

## 1. RAWEW14_HOBR_CANDIDATE (row 154) — the HOBR overlay rejection

**Verdict: CONFIRMED-DEAD (contract-correct) — but it is a CAPITAL-CONTRACT kill, not an
absence-of-signal kill. Recorded in that precise form because the distinction matters.**

Repro: `python3 work_r8/s2_hobr_leverage.py`, `python3 work_r8/s3_hobr_admissible.py`.

**(a) Gate mis-application test.** The rejection rests on V2 section 8c (blend dAnn > 0, HARD). My
own 14-sleeve natural re-solve reproduces their number: dAnn **-0.9133pp**, dSR +0.0908, dMDD
+0.4568pp, HOBR mean NAV share 0.057573, max 0.099809 (theirs: -0.9069 / +0.0909 / +0.4568 /
0.05758 / 0.09981). The right gate was applied to the right quantity.

**(b) The +4.21pp artifact.** Their own audit (`HUNT_INTERNATIONAL2/work_r7/hobr_audit_r7.json`)
already identifies +4.21pp as the **fill-0 additive overlay** (`champ + w*sleeve`), whose blend
gross is 1.6146/1.6292/1.6438/1.6729 — a section 8e breach at every rung. I tested whether that
gain is arithmetic leverage by re-levering the PLAIN 13-sleeve champion to the same grosses:

| fill-0 gross | fill-0 dAnn | plain champion re-levered to that gross |
|---|---|---|
| 1.614586 | +0.8382pp | **+0.3368pp** |
| 1.629172 | +1.6786pp | **+0.6744pp** |
| 1.643758 | +2.5212pp | **+1.0126pp** |
| 1.672930 | +4.2128pp | **+1.6913pp** |

Leverage alone accounts for ~40% of the fill-0 dAnn; the remainder is the sleeve's own stream added
on top of an already-fully-invested champion. Either way it is **inadmissible**: it lives entirely
above the section 8e gross cap.

**(c) Is there ANY admissible construction with dAnn > 0?** No. Fine w-grid on the relw-scaled
re-solve, gross held at exactly 1.6 (their section 8g machinery):

| w | gross mean | gross max | dAnn_pp | dSR | dMDD_pp |
|---|---|---|---|---|---|
| 0.001 | 1.600000 | 1.600000000 | -0.0156 | +0.0017 | +0.0079 |
| 0.005 | 1.600000 | 1.600000000 | -0.0781 | +0.0085 | +0.0395 |
| 0.050 | 1.600000 | 1.600000000 | -0.7915 | +0.0798 | +0.3965 |
| 0.100 | 1.600000 | 1.600000000 | -1.6053 | +0.1454 | +0.7957 |
| 0.150 | 1.600000 | 1.600000000 | -2.4417 | +0.1912 | +1.1968 |
| 0.250 | 1.600000 | 1.600000000 | -4.1835 | +0.2026 | +1.8790 |
| 0.400 | 1.600000 | 1.600000000 | -6.9534 | -0.0267 | -0.9200 |

**Best admissible dAnn = +0.0000pp at w = 0.** dAnn is monotonically decreasing in w. Note dSR and
dMDD are strongly POSITIVE across w = 0.001..0.30 (+0.19 SR, +1.88pp MDD at w=0.25): the sleeve is
a genuine risk reducer that the 8c return gate rejects.

**Decisive structural finding (new this round).** The champion's gross is **pinned at exactly
1.600000000000000 every single day** (min 1.599999999999999, max 1.600000000000001, 0 days outside
+/-1e-9 — verified in `s3_hobr_admissible.py`). Consequently **every additive overlay breaches 8e
by construction**, and the only admissible form is a weight re-solve that keeps gross at 1.6, i.e.
trading champion exposure away. The R7 "+4.21pp" could never have been an acceptance path, whatever
its statistical reality. This is a contract observation, not an R7 defect.

**(d) What the rejection gives up (the honest counterfactual).** The 14-book runs at LOWER vol than
the champion, so a vol-matched (rather than gross-matched) comparison is positive:

| w | 14-book vol | champion vol | vol-match factor k | implied gross | vol-matched dAnn |
|---|---|---|---|---|---|
| 0.05758 (natural) | 9.6293% | 10.1267% | 1.0517 | 1.6826 | **+0.9475pp** |
| 0.150 | 8.9944% | 10.1267% | 1.1259 | 1.8014 | **+1.8947pp** |

Both implied grosses exceed 1.6 -> 8e breach -> inadmissible under the ratified contract. The gain
is real in risk-adjusted terms and unreachable under the current capital contract.

**(e) Ledger nuance.** DEAD_IDEAS row 133 records `RB_hobr_crack_hyst_w63_z10_zo10` as
`dead (adoption REJECTED on 8c)`, but the row's own evidence shows the sleeve **PASSES the
new-sleeve V2 battery** standalone (net SR 1.3498, corr_champ +0.0219, scr_p 0.000, beats_passive
1.603 > sixty_forty 0.602, plateau ok). I confirm the standalone sleeve scores SR **1.3599**
(ann 13.21%, vol 9.45%, n=4576) in my own run. The `dead` label is about its ADOPTION, not about the
sleeve. Nothing was hidden — but the wording conflates "dead sleeve" with "rejected adoption" and
will mislead a future reader who greps the ledger for `dead`.

---

## 2. Deribit DVOL / CRYPTO2 corner (a) (row 148) — blocked

**Verdict: CONFIRMED-DEAD. Two independent grounds; the attack found no admissible overlay gain.**

Repro: `python3 work_r8/s4_dvol_attack.py`.

**(c) Span/data-defect test.** The data claim is exactly right. I hashed the vintages myself:
`tools/quant/data/deribit_dvol/btc_dvol.csv` sha16 `a5ac2cc1443ccaae` n=1801, 2021-10-03..2026-09-07;
`eth_dvol.csv` sha16 `2c3cb8a0f8e36e90` n=1801, same span. Both MATCH the row's pins.
`bt.engine.COST_BPS = 6.4` confirmed at runtime, so the cost convention in their engine is the
full-|dW| one, and it also charges 0.5%/yr borrow on shorts. Their engine passes `book_gross` to
`gates.run` but the headline uses their own `net_sr` — the conservative reading.

**(a)/(d) Was a positive result discarded?** Their best config reproduces exactly: my run of their
engine gives `DVOL_ETH_VOV_60` n=1276, **netSR 0.7636** (published 0.764). That is well below the
SR >= 1.0 gate, and separately `span_class = inception_fail` (2021-10-03 > 2013-01-01, V2 9a), which
makes it not hunt-eligible regardless of SR.

I then tested the one thing the row leaves implicit — whether the near-zero correlation
(corr_champ +0.0049 in my run) makes it valuable as an OVERLAY despite the low standalone SR:

| construction | w | gross mean | dAnn_pp | dSR | dMDD_pp |
|---|---|---|---|---|---|
| additive `champ + w*dvol` | 0.05 | 1.6049 | +0.4021 | +0.0338 | +0.1077 |
| | 0.25 | 1.6243 | +2.0010 | +0.0887 | +0.4708 |
| gross-neutral `(1-w)*champ + w*dvol` | 0.05 | 1.5249 | -1.1734 | +0.0354 | +0.3729 |
| | 0.15 | 1.3746 | -3.5006 | +0.0831 | +1.1061 |
| | 0.50 | 0.8486 | -11.4387 | -0.3853 | +1.8941 |

Every additive row breaches 8e (gross > 1.6 — see the pinned-gross finding in section 1); every
gross-neutral row has dAnn < 0. Same geometry as HOBR: a low-SR, zero-correlation, vol-reducing
stream that improves SR/MDD and dilutes return. **No admissible gain.** The row's phrase
"decorrelation NOT the binding gate ... no alpha to carry it" is accurate.

UNJUDGEABLE sub-item: the OPTIONS-CHAIN (term-structure) half of the corner could not be tested by
the agent and could not be tested by me either — the network block is environmental. The DVOL-only
half is a confirmed honest negative; the term-structure half remains genuinely untested.

---

## 3. FINRA short interest / SECTOR2 (row 150) — dead on admission

**Verdict: CONFIRMED-DEAD. The data-admission claim is exactly right; the candidate was killed by
unreachable data and by on-disk span, not by a mis-applied gate.**

Repro: `python3 work_r8/s1_finra_span.py`.

The row claims `tools/quant/bigmove/data/finra_regsho` holds "181 daily files" spanning "2 DISJOINT
windows 2019-01..02 + 2024-01..08". Verified: **181 CSV files**, forming exactly two contiguous
runs — `20190102..20190215` (32 files) and `20240102..20240805` (149 files) — separated by a single
1782-calendar-day gap (2019-02-15 -> 2024-01-02). Distinct YYYYMM values are exactly
{201901, 201902, 202401..202408}.

The cited parquet is at `tools/quant/bigmove/data/finra_short_ratio_monthly.parquet` (a slightly
different directory from the daily CSVs, but the file exists): shape **104004 x 3**
(`month,ticker,short_ratio`), 10 distinct months = {2019-01, 2019-02, 2024-01..2024-08}. So the
"max 8 contiguous monthly obs -> materially-short span, UNJUDGEABLE (V2 9b)" characterisation is
**exactly correct**, as is the n=104004 row count.

The 7-observation 2024 diagnostic leg (-5.16%/yr ann, SR -0.376) is below any judgeable threshold and
adopting either sign from 7 observations would be p-hacking. The row's refusal to do so is correct.
I did not re-probe the six keyless routes (those hosts are environmentally WAF/DNS-blocked); my
attack was on the on-disk span claim, which survives intact.

---

## 4. ECB AAA yield-curve factors / TREASFUT (row 151) — dead

**Verdict: CONFIRMED-DEAD. The p-hacking-the-other-way attack was run and FAILED: no parameterization
reaches the gate, and the best value is a spike, not a plateau.**

Repro: `python3 work_r8/s5_treasfut_sweep.py` (imports their engine unmodified).

Faithful reproduction first — my re-run matches the published SR to 4 decimal places on all four
configurations:

| config | my SR | published SR |
|---|---|---|
| TREASFUT7_ECB_SLOPE_mom | +0.3938 | +0.3938 |
| TREASFUT7_ECB_SLOPE_rev | -0.4211 | -0.4211 |
| TREASFUT7_ECB_CURV_mom | +0.2724 | +0.2724 |
| TREASFUT7_ECB_CURV_rev | -0.3020 | -0.3020 |

**(b) Sign test — passes.** Both directions were tested: the momentum leg is positive and the
mean-reversion control is symmetrically negative (SLOPE +0.394/-0.421; CURV +0.272/-0.302). The
reported direction IS the tested direction; this is not a sign bug.

**(d) Parameter sweep (the real attack).** k=63 was pinned a-priori and never scanned. I swept k over
10 values with everything else at their conventions:

| k | 10 | 21 | 42 | 63 | 84 | 126 | 189 | 252 | 378 | 504 |
|---|---|---|---|---|---|---|---|---|---|---|
| SLOPE_mom SR | -0.177 | +0.027 | **+0.535** | +0.394 | +0.102 | -0.035 | -0.044 | +0.007 | -0.425 | -0.402 |
| CURV_mom SR | +0.002 | +0.177 | +0.081 | +0.272 | +0.214 | +0.108 | +0.308 | +0.364 | **+0.597** | +0.422 |

The best SLOPE momentum SR anywhere in the grid is **+0.5352** (k=42) and the best CURV is **+0.5974**
(k=378) — both far below `sr_min 1.0`, and both isolated spikes (SLOPE neighbours: k=21 +0.027,
k=63 +0.394, k=84 +0.102), not plateaus. A vol-target sweep (target 0.05 -> 0.30) is flat at SR
0.381-0.413, so leverage does not rescue it either. Post-2010 decay confirmed independently (best
CURV k=378: pre2010 +1.4095 vs post2010 +0.1195), and per the campaign rule a pre-2010-concentrated
effect FAILS.

**One documentation nit (does not change the verdict).** The row frames both families as
"PRE-2010-CONCENTRATED". That is accurate for CURV_mom (post2010 +0.047) but imprecise for SLOPE_mom,
whose post-2013 sub-era SR is **+0.4074 — higher than its own full-sample +0.3938**. SLOPE_mom is not
decaying to zero; it is simply small (0.39-0.41) everywhere. The verdict stands on `sr_min 1.0`
regardless.

---

## 5. FX carry via daily PIT overnight rates / FXCARRY2 (row 149) — dead

**Verdict: CONFIRMED-DEAD. All three attacks failed.**

Repro: `python3 work_r8/s6_fxcarry_attack.py` (imports their engine unmodified).

Faithful reproduction: my rebuild gives SR **+0.0731**, H1 +0.29 / H2 -0.22, 12 negative years, worst
-26.7%, n=5739 — an exact match to the published row.
(Disclosure: my first attempt gave SR +0.0248 because I passed the wrong return value of
`build_carry_book` — it returns effective weights first and decision weights second. I found and fixed
my own bug; the corrected run is byte-exact. The original discrepancy was mine, not theirs.)

**(a) Cost/gate convention — attack FAILS.** Their `net = tot` is spot P&L + overnight carry accrual,
i.e. the published headline SR is **pre-transaction-cost**. I applied the full convention (6.4bps
full |dW| + 0.5%/yr borrow on shorts) myself:

| | SR | ann | vol |
|---|---|---|---|
| uncosted (their headline) | +0.0731 | | |
| fully costed (mine) | **+0.0699** | -0.7381% | 20.9853% |

Mean cost drag is only **6.74 bp/yr** (monthly rebalance, mean gross |sig| 3.51), so the published
number is essentially the costed number (0.003 SR apart). No material undercharge.

**(b) Sign — attack FAILS.** Inverting the decision sign gives SR **-0.0731** exactly, with H1/H2
mirrored. The reported direction is the tested direction and is the economically correct carry
direction (long the positive-differential currency). No sign bug.

**(c) Span — attack FAILS.** The EUR leg is capped at 2021-12-29 by EONIA. I rebuilt the book
substituting the on-disk `EUR_ECBDFR` (1999-2026) as the EUR leg: SR **+0.2314** (H1 +0.39, H2 +0.02,
11 neg). Nearly triple the original — and still nowhere near 1.0. The span constraint is not what
killed this family.

**Era table — and a temptation correctly avoided.** The row reports post-2004 SR -0.198. The full era
table I computed is:

| era | 1999+ | 2004+ | 2008+ | 2015+ | 2019+ | 2021+ |
|---|---|---|---|---|---|---|
| n | 5739 | 4695 | 3652 | 1825 | 782 | 259 |
| SR | +0.0731 | -0.1979 | -0.1970 | -0.1084 | +0.3127 | **+1.8286** |

The `2021+` cell reads SR +1.83, which would clear the gate if quoted carelessly. It is **259
observations = a single calendar year** (the book ends 2021-12-29, so `2024+` is empty), and 9b makes a
materially-short span unjudgeable. The R7 agent did not quote it and neither will I: it is a one-year
tail, not evidence of a live regime. Recorded here as a trap for the next reader.

---

## 6. STEP 2 requirement — re-read the raw artifacts against the published conclusions

I checked the published row text against the on-disk artifacts for every rejection. **No misstatement
was found.** The published conclusions follow from the numbers on disk.

| rejection | artifact read | published vs on-disk |
|---|---|---|
| TREASFUT (151) | `HUNT_TREASFUT/work_r7/r7_ecb_curve_results.json` | SR 0.3938/0.2724/-0.4211/-0.3020; H1 0.5246 H2 0.2324; 11 negyr worst -0.1448; scr_p 0.155-0.855; corr_champ -0.034..+0.042; pre2010 0.6392 -> post2010 0.2903; post2013 0.4074 — **all match the row exactly** |
| FXCARRY2 (149) | `HUNT_FXCARRY2/work_r7/r7_overnight_carry_results.json` | SR 0.07314, H1 0.2867 H2 -0.2154, 12 neg, worst -0.2672, post-2004 -0.19787, scr_p 0.88, leak_ok True — **all match** |
| DVOL (148) | `HUNT_CRYPTO2/work_r7/btc_dvol.csv`, `eth_dvol.csv` | sha16 `a5ac2cc1443ccaae`/`2c3cb8a0f8e36e90`, n=1801, 2021-10-03..2026-09-07 — **both match the row's pins** |
| SECTOR2 (150) | `tools/quant/bigmove/data/finra_regsho/`, `finra_short_ratio_monthly.parquet` | 181 files / 2 disjoint runs; parquet 104004x3 / 10 distinct months — **matches** |
| HOBR (154) | `HUNT_INTERNATIONAL2/work_r7/hobr_audit_r7.json` (36 checks, 0 failed) | the audit is genuinely independent and internally consistent; I reproduced its headline dAnn -0.9069pp as -0.9133pp on the newer champion vintage |

Two caveats for the coordinator, neither material to any verdict:
1. Row 154 cites an inherited evidence gap ("gross-neutral -0.306pp/-1.565pp appear only as FINDINGS
   prose, no generator"). That gap is real and was **not** closed in R7 — the numbers remain
   unverifiable prose. The audit's own replacement construction gives -0.0452/-0.2260pp.
2. Row 154's `source` field is a long compound string (paths + prose) rather than a source tag, which
   is why it sorts oddly and is easy to miss when grepping for `-R7`.

---

## 7. STEP 3 — un-mined seam scan (already-owned data)

Method: full inventory of `tools/quant/data/` (78 source dirs, 3413 files) plus every `.csv`/`.meta`
under `campaign/agents/`, `campaign/team/agents/`, `campaign/results/` (1602 sleeve-ish filenames),
cross-referenced against all 153 ledger rows with hyphen/underscore/slash normalisation.

### 7a. A correction I owe the round (recorded because it is the exact defect class this round hunts)

My first pass concluded that `bis_eer`, `boe_curve`, `gilt` and `mof_jgb` were un-mined, and I
drafted sleeve proposals on the BoE gilt curve and on a BIS-REER FX-value factor. **That was wrong.**
My keyword scan matched on `bis_eer`/`boe_curve`/`gilt`, but the ledger spells them `BIS-EER`, `BoE`
and `JGB/BoE/ECB-YC/BIS-EER`, so a real row was missed. With normalised matching the row appears at
**DEAD_IDEAS row 50**:

> `sovereign-curve shape features (JGB/BoE/ECB-YC/BIS-EER) on FX/ETF proxies | dead | HUNT_CURVES`

and the owning agent's own verdict (`campaign/agents/loop_team/HUNT_CURVES/FINDINGS.md`, iter8) is:

> "NEGATIVE — 56 variants, ZERO reach SR 0.3. Best: eer_GB_mom21->GBP_USD 0.261 (4 neg),
> jgb_5Y30Y_mom->EWJ 0.252 (9 neg). ... Do not re-run: slope/butterfly z 63-252d mom/rev on
> USD_JPY/EUR_USD/GBP_USD/EWJ/EWG/EWL/EWA/UUP."

So the BoE gilt curve (nominal + real + OIS), the JGB curve (1974+, 15 tenors), the ECB AAA curve and
the BIS NEER/REER daily panel are **already mined and already negative**. The full screen is on disk
at `campaign/agents/loop_team/HUNT_CURVES/screen_curves.csv` (57 rows, best SR 0.261, most negative).
**Both of my drafted proposals are withdrawn.** The lesson generalises: `DEAD_IDEAS.csv` cannot be
searched by source-token, because rounds append prose that inlines the data directory names in
inconsistent styles.

### 7b. Genuinely un-mined seams that survive the corrected check

Normalised counts (LEDGER = occurrences across all 153 rows; SLEEVES = occurrences across 1602
sleeve filenames):

| asset | path | span / rows | LEDGER | SLEEVES |
|---|---|---|---|---|
| EIA regional + product storage | `tools/quant/data/eia_weekly/` | 1983/1986-2026 weekly | 1 (as "UNTESTED") | 0 |
| EU natural-gas storage | `tools/quant/data/gas_storage/` | 2011-01..2026-09 daily | 0 | 0 |
| China margin balance | `tools/quant/data/eastmoney_margin/` | 2010-03..2026-09 daily | 0 | 0 |
| HK Stock Connect northbound | `tools/quant/data/em_hsgt/` | 2014-11..2026-09 daily | 0 | 0 |
| SEC fails-to-deliver | `tools/quant/data/sec_ftd/_raw_zips/` | 2017-08..2026-08, 208 zips | 0 | 0 |
| Shiller CAPE | `tools/quant/data/shiller_cape/` | 1871-01..2023-09 monthly | 0 | 0 |
| TIC foreign holdings | `tools/quant/data/tic_mfh/` | 2000-01..2024-12 monthly | 0 | 0 |

### 7c. Recommendation — one seam is worth a round; the rest are not

**WORTH A ROUND: EIA regional + product-level storage (`tools/quant/data/eia_weekly/`).**
This is the only candidate the ledger itself documents as untested. Row 57 killed the *L48 aggregate*
natgas storage signal ("naive engines best SR 0.29; signal fully priced by publication, Wed 10:30 ET")
and then states verbatim: *"REGIONAL storage + crude prod/imports/supplied remain UNTESTED
affordances (13 series certified+linted, tools/quant/data/eia_weekly/)"*. I verified the files are
present and populated: `ng_storage_{east,midwest,other,salt,southnonsalt,southsalt,west}_weekly.csv`
(n=870 each) alongside `ng_storage_L48_weekly.csv` (n=870), `crude_prod_weekly.csv` (n=2122) and
`crude_imports_weekly.csv` (n=1913); the ~200-file `petstk_*` matrix covers 1983-2026 weekly.
Span is pre2007 -> hunt-eligible. Sleeve shape: a weekly **cross-sectional regional storage
dysregulation** signal (each region's storage vs its own 5-year seasonal band, demeaned across
regions) traded against the natgas complex, decision strictly after the Thursday EIA print with the
T+1 rule, 6.4bps full |dW| + 0.5%/yr borrow, VT10 cap 3. The honest prior is mixed: the L48
aggregate was priced by publication, so the burden is on the *regional cross-section* to carry
information the aggregate does not — that is exactly the untested hypothesis, and it is cheap.
Note the tradable problem: the regional spread is not directly ETF-expressible, so the realistic
implementation is a natgas/energy-equity proxy book and must clear `beats_passive` on its own.

**NOT worth a round (recorded so nobody re-derives them):**
- EU gas storage (`gas_storage/`, 2011+, daily): genuinely un-mined and span-eligible, but it is the
  same storage-cycle mechanism as the dead L48 family in a different region, and the L48 result
  already showed the information is priced at publication. Low expected value.
- SEC FTD (`sec_ftd/`, 208 zips): un-mined, and `build_ftd.py` exists — but its inception (2017-08)
  makes it **inception_fail** under V2 9a for the new-sleeve track, so it can only ever be an overlay
  input judged under section 8. Also note `build_ftd.py` emits only a **daily aggregate**
  (`ftd_daily.csv`: date,n,total_fails,total_notional), not a cross-sectional panel — a
  cross-sectional FTD book would need a new builder first.
- China margin / HK Connect / TIC / CAPE: un-mined, but each is either monthly, stale (CAPE ends
  2023-09), or expresses a mechanism already covered by dead flow/valuation families. Not recommended
  over the EIA regional cross-section.

**Honest framing:** none of the above is a gain. These are un-consumed *inputs*; whether any clears
`sr_min 1.0` is **untested**, and I make no claim that it does. The EIA regional cross-section is the
only one I would spend a round on, because the ledger itself flags it as the remaining untested half
of a family whose other half is already booked.

---

## 8. What I could NOT determine

1. **DVOL options-chain (term-structure) half** — genuinely untestable from this environment
   (network-blocked at the agent's round and still blocked now). Row 148's `blocked` status is correct
   and should stay `blocked`, not be converted to `dead`.
2. **Whether RB_hobr should be promoted as a standalone library sleeve** — it passes the V2
   new-sleeve battery in both their evidence and my run (SR 1.36, corr +0.02). That is a policy
   decision for the coordinator, not an audit finding.
3. **Champion vintage drift** — R7's numbers were computed on n=4805/`4358dfab`; the champion of
   record is n=4806/`8d7e711e`. I did not reconstruct the R7-time vintage, so my re-derived deltas
   differ in the 3rd decimal from the published ones. No verdict is sensitive to this, but a strict
   like-for-like audit of the R7 numbers would need the older vintage.
4. **Network-dependent admission claims** (SECTOR2's six keyless routes, DVOL's Deribit block) were
   not re-probed — those hosts are environmentally blocked. I verified their on-disk consequences
   instead, which is what the verdicts actually rest on.
5. **Exhaustiveness of the seam scan.** It is a keyword/namespace cross-reference, and section 7a is a
   worked example of exactly how that method fails. A seam whose data directory is never named in any
   ledger row and whose sleeves are named idiosyncratically could still be missed.

## 9. Bottom line

**Zero wrongly-applied rejections found.** All five R7 rejections survive adversarial attack: two are
data/span kills (SECTOR2, DVOL), one is a contract kill (HOBR, sections 8c/8e), one is a genuine
small-signal negative (TREASFUT, best-of-sweep SR 0.60), one is a genuine zero-signal negative
(FXCARRY2, costed SR 0.070, sign-correct, span-robust). No published R7 claim was found to misstate
its own artifacts.

The one durable new result is structural rather than a gain: **because the champion's gross is pinned
at exactly 1.6 every day, section 8e makes every additive overlay inadmissible by construction, and
section 8c then rejects every vol-reducing diversifier.** HOBR and DVOL both fit that shape — SR and
MDD improve, return dilutes, and the implied vol-matched re-lever needs gross 1.68-1.80. If the
campaign wants to monetize decorrelated risk reducers, that interaction is the thing to revisit, not
the sleeves.

The one new lead is the EIA regional/product storage cross-section (section 7c), which the ledger
itself records as untested.

ROUND 8 DONE
