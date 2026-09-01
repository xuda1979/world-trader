# AUDIT4_build — FINDINGS (adversarial audit of champion construction)
Auditor: AUDIT4_build | Date: 2026-09-01 | Scope: champion_build.py (V1 16-pool), champion20y_build.py (20Y 13-pool), committed champion CSVs/JSONs.
Method: read-only. All numbers below computed by the auditor from committed files. UNVERIFIED used where reconstruction failed.

## VERDICT (one paragraph)
The two canonical builders are mathematically sound: no lookahead found anywhere in the
construction code (all scaling uses rolling(...).shift(1); throttle uses eq.shift(1)/rm-1;
empirical perturbation test confirms strict causality), unit tests pass with hand-computed
answers, costs are charged as documented and byte-exact repro holds for all 6 V1/20Y_V2 CSVs
(max dev 1e-16). HOWEVER, the audit refutes or materially qualifies several headline
claims: (1) "NO leverage / no leverage: PASS" is FALSE as stated — the book's gross
exposure averages 5.2x (config A) / 6.5x (B), max 16.8x/21.7x, and is >1x on 97% of days;
the spec's own financed variant is a partial disclosure, not a full financing charge, and
its generating script is not committed (repro impossible). (2) The champion books returns
on 187 NYSE-closed days (weekends/holidays) — e.g. +4.66% on 2008-12-25, +5.89% on
2015-12-25 (natgas/carry FRED spot prints) — non-tradeable days contributing ~+0.75pp ann.
(3) V3/V4 champions are NOT byte-reproducible from any committed builder (no script carries
their pools; doc claims "build scripts ... updated" is false; doc also misstates pool sizes
"21-pool"/"16-pool" vs JSONs' 20/15). (4) The doc's LOYO 45.5-50.0% and 5y-CAGR
53/53/73/64 claims could not be reproduced under any natural convention on any committed
series — numbers appear stale or from an uncommitted construction (UNVERIFIED).

---

## 1. UNIT TESTS (charter 1a-1d)

### 1a. Single constant-return sleeve, vt(r, 0.10)
- vol.iloc[59] (last warmup day) = NaN -> scale 0.0. PASS (60-day warmup correctly zeroed).
- vol.iloc[60] (60 identical obs) = 0.0 exactly -> s = 0.10/0 = inf -> clip cap 8 -> s=8.0.
  s.iloc[61:] all == 8.0. v.iloc[60] = 0.008 = r*8. PASS.
- Note: division by exactly-zero vol yields inf clipped to cap — cap is the only guard.
  No pool sleeve has zero realized 60d vol (all 16 min std > 0), so no live-path degeneracy.

### 1b. Two zero-corr vt10 sleeves -> blend vol
- 4000d synthetic, true vol 10% each: per-sleeve scaled vols 10.17%/10.20%; blend vol
  (days 1000+) = 7.280% vs analytic 10%/sqrt(2)=7.071%; diff 0.21pp = estimation noise. PASS.

### 1c. 126d drawdown throttle
- Vectorized code == independent day-loop on 100 random paths except warmup (see F-1).
- Known-DD path (peak day 299, -80bp/day): first cut 7 days after peak; analytic
  k = ln(0.96)/ln(0.992) = 5.08 -> expected first cut after down-day 6, cut fires when
  trailing DD first crosses -4%: tdd[cut-1] = -3.937% (no cut), tdd[cut] = -4.705% (cut).
  Off-by-one consistent with threshold crossing on eq.shift(1). PASS.
- Same-day test: injecting -50% return at day T in a clean region: sc[T] unchanged (1.0),
  sc[T+1] = 0.5. tdd[T] bit-identical between perturbed/unperturbed paths. PASS — no
  same-day throttle action; decision uses only data through T-1.

### 1d. Costs on hand-computable weight path
- W = Sn.div(Sn.sum(axis=1)) with NaN->0; tw = 0.5*sum|dW|: hand path
  [0, 0.25, 0.75, 0.5] == code to 0.0e+00. PASS.
- dsc = 0.5*|diff(sc)|: [0, .25, 0, .25, 0] exact. PASS.
- Initial deployment IS charged (NaN->0 counts as a trade into initial weights) — conservative.
- Total cost series = (tw + dsc)*6bps, embedded in returned series. Verified by construction
  (champ = b2 - tot*COST) and by 1e-16 byte repro.

## 2. CODE AUDIT — LOOKAHEAD (charter 2)
- vt(): vol = r.rolling(60).std().shift(1)*sqrt(252); scale = (tgt/vol).clip(upper=8);
  scale NaN->0. Rolling window closes at t-1 -> scale_t uses data <= t-1. CLEAN.
- blend: mean of scaled sleeves (pandas skipna). No future data. CLEAN.
- throttle: rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm-1; sc from tdd <-THR.
  Peak window ends t-1; numerator is eq[t-1]. Decision at t uses data <= t-1. CLEAN.
- costs: tw uses W.shift(1) (trailing), dsc uses sc.diff() (applied to today's already-shifted
  decision). CLEAN.
- EMPIRICAL CAUSALITY PROOF: perturbing ALL 16 sleeves by +10bp on every day >= 2020-01-02
  changes the output on 0 days before the cutoff (max|Δ| = 0.0e+00); changes only after
  (max 1.9e-2). No contemporaneous-back contamination anywhere in the pipeline. PASS.
- Warmup zero-returns: champion's first 60 days (2008-09-01..2008-11-24) have b=0
  (global-vt warmup) and carry only cost drag: cumulative -0.156% (15.6bps of costs,
  15.56bps charged). Excluding them: SAFE-A ann 48.52%->49.16%, BAL 55.46%->56.19%.
  The headline includes this drag => conservative, no inflation. NOTE: -0.16pp honesty cushion.

### F-1 (FINDING, minor): throttle inoperable for first 126 days
rolling(126) default min_periods=126 -> tdd is NaN for the first 126 days; NaN < -THR is
False -> full exposure during warmup. An expanding-window variant was run as control:
- V1 SAFE-A: 0 days differ, stats identical to 4 decimals.
- V1 AGG-B: 6 days differ (Dec 2008), expanding ann 62.35% vs as-built 62.40%, SR 5.266 vs
  5.270, mdd identical -7.886%. Impact +0.05pp ann in as-built = small pro-construction bias.
- 20Y A: 0 days differ. 20Y BAL: as-built = expanding to 4 decimals.
Verdict: minor, does not change any conclusion, but the "trailing 126d" description is
technically wrong for the first 126 days of each series.

### F-2 (FINDING, doc error): "MHX dilutive before entry" is backwards
MHX (starts 2008-09-02) is NaN-excluded pre-entry, so pre-2008-09 the 20Y blend is a
12-sleeve mean (verified: max|diff| vs explicit 12-sleeve mean = 0.0e+00). On entry day
2008-09-02 the same-12 mean would be 0.00128; the 13-sleeve mean is 0.00118, exactly the
12/13 = 0.9231 rescale. Doc claim "enters 2008-09 — dilutive before that, conservative"
describes a mechanism that does not exist. MHX is in fact DILUTIVE AFTER entry: drop-MHX
20Y BAL = 53.69% @ SR 5.171/-8.89% vs 65.05%/6.169/-7.15% with it, i.e. MHX adds +11.4pp
ann (a marginal-contribution claim the docs never make in this direction; the V2 section
numbers themselves are consistent, but the "conservative dilution" framing is wrong).

## 3. CONSTRUCTION INVARIANTS (charter 3)

### F-3 (FINDING, MAJOR — spec contradiction): hidden leverage is real and large
Per-sleeve vt10 with cap 8x in an EW-of-16 "capital" book: gross exposure path
(sum_i s_i/16, before global vt and throttle):
  V1 16-pool: mean 2.14x, max 4.76x, min 0.13x, p99 4.49x.
Global vt scale g: mean 2.39 (A) / 3.09 (B), max 4.97/6.43 (cap 8).
Throttled share of days: 3.85% (A) / 10.03% (B).
TOTAL book gross (sum_i s_i/16 * g * sc):
  config A: mean 5.199x, max 16.79x, p99 13.90x; >1x on 96.9% of days.
  config B: mean 6.513x, max 21.73x, p99 17.98x; >1x on 97.3% of days.
  20Y A: mean 5.01x, max 17.86x; 20Y B: mean 5.78x, max 21.03x.
The spec's scorecard says "No leverage: PASS (EW weights, vt caps)" and the final report
says "weights sum 1". TRUE only for normalized accounting weights (sum_i s_i/Σs = 1), NOT
for the economic book the returns describe (each sleeve holds s_i/16 of capital where s_i
averages ~34 across sleeves). The per-sleeve vt caps do NOT cap portfolio gross at 1x; the
global vt step multiplies an already >1x book by another 2.4-3.1x on average. Every SR/ann
number is a levered-5x-book number. The charter's own question ("no hidden leverage beyond
per-sleeve vt caps") is answered: the construction is EXACTLY the hidden-leverage pattern.

### F-4 (FINDING, MAJOR): FINANCED variant understates financing vs its own description;
     its generating code is not committed
- Spec 8.5 says "Charging financing (3M T-bill + 25bps) on ALL internal gross exposure >1x
  NAV per sleeve: BALANCED 55.5% -> 48.9% @ -7.5%".
- Committed GOAL100_CHAMPION_BALANCED_FINANCED_daily.csv: stats confirm (ann 48.90%, SR
  4.692, mdd -7.45%); mean drag 6.56pp ann, largest single-day drags on 2015-12-25 (1.69% =
  169bp — a Christmas phantom day, see F-7) and 2023-01-20 (1.53% = 153bp).
- Reverse-engineering the convention against my measured gross paths and actual DGS3MO+25bp
  (FRED file committed): best fit is drag ≈ [Σ(s_i-1)+/16] * g * sc * rate (corr 0.66, mean
  2.36bp vs committed 2.60bp/day, residual std 4.6bp, max residual 168bp). NO tested
  convention (7 variants incl. full-gross and portfolio-level) reproduces the series;
  residuals up to 1.7% single-day. 
- My own conservative estimate — charging (T-bill+25bp) on ALL gross >1x at portfolio level
  (mean gross 5.2-6.5x): SAFE-A 48.5%->29.3% (-19.2pp, mdd -17.0%), AGG-B 62.4%->37.2%
  (-25.2pp), i.e. FAR below the committed financed series. Even the mildest fair
  interpretation (charge on per-sleeve excess only, no global scaling) is closer to
  -6..-10pp. The TRUE fully-financed number almost certainly sits between the committed
  financed series (-6.6pp) and my -19 to -25pp bound, i.e. headline ann 55.5% could drop to
  ~30-45% under honest full funding. UNVERIFIED exactly; direction and rough magnitude
  verified.
- The FINANCED CSVs were committed (811ee5f) WITHOUT any generator script; the runbook's
  "cold-replication" claim does not cover them. This is a reproducibility gap on the single
  most important honesty adjustment.

### F-5 (FINDING, minor): cost accounting is on normalized weights, not capital weights
Charged turnover uses W = s_i/Σs (sum 1) while the book holds s_i/16 (sum = gross). True
capital-weight turnover exceeds charged by median 1.72x (V1) / 1.52x (20Y), max 4.45x.
Recomputing with true turnover costs: V1 A 48.52%->48.36% (-0.16pp), B -0.16pp, 20Y -0.02pp.
Materiality: LOW, but the direction understates costs in the headline.

### Weights-sum invariant (as documented)
EW of vt-scaled sleeves == sum of per-sleeve contributions / 16; normalized weights sum to 1
exactly (verified algebraically and in code). The invariant as DOCUMENTED holds; the
economic leverage is F-3.

## 4. REPRO (charter 4)
- python3 campaign/scripts/champion_build.py --verify:
  GOAL100_CHAMPION_daily.csv: max|new-old| = 9.994e-17, n=4696, IDENTICAL (ann 48.5 SR 5.18 mdd -7.3, OOS 52.5%)
  GOAL100_CHAMPION_AGGRESSIVE_daily.csv: 9.975e-17, IDENTICAL (62.4/5.27/-7.9, OOS 67.8%)
  GOAL100_CHAMPION_BALANCED_daily.csv: 9.991e-17, IDENTICAL (55.5/5.24/-6.9, OOS 60.2%)
- python3 campaign/scripts/champion20y_build.py --verify: all 3 files max dev ~1e-16 IDENTICAL
  (BAL: ann 65.05%, SR 6.17, mdd -7.15%, n=5196, 2006-10-02..2026-08-28).
- Sensitivity is ALIVE: XGB1y +1bp on 2015-06-15 changes 65 output days (first = same day
  2015-06-15, max|Δ| 1.20e-4 V1 / 1.72e-4 20Y; ann moves 48.5214%->48.5220%). Not cached.
- harness/eval.py reproduces headline stats exactly (BAL 55.46%/5.24/-6.94%; 20Y 65.05%/6.17/-7.15%).

### F-6 (FINDING, MAJOR): V2 (17-pool) reproduces byte-exact from my reconstruction, but
V3/V4 have NO canonical builder; doc misstates pool sizes; V4 not byte-reproducible
- My independent rebuild of CHAMPION_V2_BALANCED (16-pool + MHX, same construct()): max|diff|
  vs committed = 9.99e-17 (byte-exact). V2 committed ann 65.97%/6.21/-7.15% == doc 66.0/6.21/-7.1.
- CHAMPION_V3 (doc: 18-pool) has JSON pool of 18 names; committed V3 BAL evals at
  68.59%/6.36/-6.78% == doc 68.6/6.36/-6.8. My rebuild attempt not needed: no builder exists.
- CHAMPION_V4: doc says "21-pool"; JSON GOAL100_CHAMPION_V4.json lists 20 names. My rebuild
  from the JSON pool (brwt5=brwt5_2000.csv) matches committed to 3.0e-03 max|daily diff|,
  ann 70.14% vs 70.13% — stats consistent but NOT byte-identical; correct file mapping for
  2 names is unconfirmed (brwt5 vs brwt5_2000 both fit; exact combo unrecoverable).
- CHAMPION20Y_V4: doc says "16-pool"; JSON lists 15 names. With brwt5=brwt5_2000.csv my
  rebuild is BYTE-EXACT (1.0e-16, ann 68.69%/6.29/-5.97/OOS 75.40% vs doc 68.7/6.29/-6.0/75.6).
  => the real pool is 15; "16-pool" is wrong. Same for V4: 20, not 21.
- The 12th section of GOAL100_CHAMPION.md ("Build scripts: champion_build.py /
  champion20y_build.py pools updated in the JSONs") is FALSE for the scripts: both still
  contain only the V1/20Y_V2 pools. V3/V4 champions are one git-clone away from being
  unreproducible except by guesswork. Dependency check "26 files, none dirty" predates V3/V4.

## 5. ADDITIONAL CLAIM VERIFICATION (all numbers exact)

### Verified claims (match to rounding):
- MDD full path: BAL -6.94% at 2025-04-09 (doc -6.9%). Worst calendar-year DD -6.94% (2025),
  every year <= 7.0%: {2008:-3.21,2009:-3.23,2010:-4.18,2011:-2.52,2012:-5.08,2013:-4.40,
  2014:-5.92,2015:-6.24,2016:-2.74,2017:-4.66,2018:-6.34,2019:-2.84,2020:-3.63,2021:-4.53,
  2022:-6.89,2023:-2.45,2024:-5.53,2025:-6.94,2026:-5.59}. PASS.
- 0/19 negative years BAL; worst year +9.09% (2026 partial). PASS. 20Y: 1/21 neg (2006 -1.6%). PASS.
- OOS 2017+: BAL 60.17% ann, SR 5.62, mdd -6.94% (doc 60.2/5.62/-6.9). PASS. 20Y OOS:
  71.5%/6.49/-7.2%. PASS.
- no-B3 16-pool BAL: 55.0% @ -7.1% (doc 55.0/-7.1). PASS. 20Y no-B3: 64.8%/-7.9% (doc). PASS.
- Keystones (drop-one, vt.085, delta pp): XGB1y -10.12 (doc -10.0), brwt -3.71 (doc -3.5),
  QAxasts -1.45 (-1.5), A1credit -1.06 (-1.2), C5ng -0.88 (-1.1). PASS (small doc rounding).
- A5r2/A5r4 correlation = 1.000000 (doc "corr 1.0 duplicates"). PASS (series differ in bytes,
  identical in correlation; both retained as disclosed).
- Wall bound: vt .115/thr .03 => 64.9% @ -7.7% EXACT (doc 64.9/-7.7). vt .12/thr .03 =>
  67.5% @ -8.4% (doc "68.3%" — slight mismatch; my vt .12/thr .04 gives 68.4%/-9.9%;
  doc number not exactly reproduced, ambiguity in config. Minor discrepancy.)
- 20Y cost stress: 8bps => 64.7%/-7.4%; 10bps => 64.4%/-7.5%. EXACT (doc same). PASS.
- 20Y OOS claim verified above; 5y CAGRs 20Y: my anchored windows 88/81/87/133 vs doc
  84/77/96/107 (window convention unstated; UNVERIFIED exact convention, magnitude consistent).
- monthly SR + bootstrap CI (2000 resamples, monthly): V1 BAL 3.66 [3.24,4.21] (doc ~3.6,
  CI 3.1-4.1); 20Y BAL 3.83 [3.41,4.37] (doc 3.83 [3.39,4.35]). PASS.
- mean pairwise corr of vt10 sleeves (2009-09+): 0.037 incl. the 1.0 duplicate pair, 0.029
  excluding it (doc "~0.05"). PASS (conservative direction).
- brwt10: ann 32.1%, SR 3.41, 0/27 neg years — all EXACT vs doc.
- brwt family (V4, 4 slots): internal corr 0.73-0.87; family = 29.3% of blend mean return
  from 20% of slots. Family concentration as disclosed, but quantified here: dropping the
  whole brwt family is the single biggest fragility; docs disclose per-sleeve, not family
  weight in return terms.
- V1 blend denominator: 14 sleeves on day 1 (2 warmup-zero), 16 from 2009-09-18; MHX-style
  NaN-exclusion in 20Y verified conservative-consistent (see F-2 for corrected interpretation).

### F-7 (FINDING, MAJOR): returns booked on NYSE-closed days (phantom days)
The champion has 4696 rows; 1 weekend row and 186 federal-holiday rows (187 union).
These come from FRED-based sleeves (A1inf, A1credit, carryv2: 13-26 holiday rows each;
C5ng/C5ngsum 1-2) whose "daily" prints exist on exchange holidays. Biggest phantom P&L:
2008-12-25 +4.66%, 2009-01-01 +2.24%, 2009-01-19 +2.01%, 2015-12-25 +5.89%, 2021-11-26
+3.88%, 2020-01-01 +2.95%, 2011-02-21 +2.11% — these are non-tradeable days (spot prints
published on holidays; C5ng trades Henry Hub SPOT; carryv2/A1inf commodity/FX proxies).
Cumulative: phantom days carry +0.5471 in summed returns; removing them lowers per-day log
growth from 0.002176 to 0.002147 => ann 54.85% -> 54.10% (-0.75pp). Also inconsistent
internal calendars (896 days where sleeve count changes vs prior day) make the EW
denominator jump daily (mid-series holes: 564 champion days with <16 sleeves).
No lookahead, but the backtest books P&L on days no venue is open — inflates ann, and
the T+1 discipline the campaign prides itself on is not enforceable on phantom days.

### F-8 (FINDING, doc): tail-week degeneracy
Sleeve files end on different dates (2026-07-01..2026-08-28). The V1 champion's EW
denominator decays to 12 (Aug 5-11), 5 (Aug 13-24), 3 (Aug 25-27), 1 (Aug 28: A1credit
only). July 1-Aug 28 tail return +4.75% in 18 days is carried by the few longest-running
sleeves (effectively a different, unvalidated portfolio for 2 months). 20Y: 802 days
<13 sleeves. Headline includes this tail. Materiality: small (ann shift <0.5pp) but the
champion's last ~40 days are not the advertised 16-sleeve system. The 20Y all-13 subset
runs ann 68.5%/SR 6.384 vs full 65.05%/6.169 (subset-vs-full is rebasing, not additive).

### F-9 (FINDING, doc): LOYO 45.5-50.0 and 5y CAGRs 53/53/73/64 not reproducible
Tried conventions on V1 BAL, SAFE-A, AGG-B, 14-pool BAL, and every committed champion CSV:
arith-mean of remaining years / daily-ann of remaining / CAGR of remaining / excluding
partial years. Best candidates: SAFE-A daily-ann-remaining = 45.9..50.3 (close to doc
45.5..50.0); 14-pool SAFE-A excl 2008/2026 = 44.1..49.6. The doc labels the number as
"Leave-one-year-out ann" for the BALANCED champion; under that label I get 69.5..80.0
(arith) or 68.0..76.8 (CAGR). VERDICT: numbers appear to be SAFE-A (not BALANCED) or from
a different/earlier construction; doc provenance UNVERIFIED. 5y CAGRs: no committed series
or window convention yields 53/53/73/64 for BAL (my computations: 66/67/71/95 anchored
from start; 54/54/75/77 fixed calendar years; CHAMPION_FINAL-era numbers ~7-13% are
stale decimal-vs-percent era). UNVERIFIED — likely stale/mislabeled, does not affect
headline ann/SR/DD but is a documentation-integrity defect.

### F-10 (FINDING, minor): selection-rule stability overstated
C4's frozen rule "argmax IS SR s.t. IS MaxDD<=8% AND every IS calendar-year DD<=8%",
grid tgt{.08-.11} x thr{.025,.03,.04,.05} x fr{.4,.5,.6} x lb{126,189,252} (144):
my exact re-run argmaxes:
  IS-end 2016: (0.11, 0.05, 0.6, 126) SR 4.8105 (frozen pick SR 4.7932, gap +0.017)
  IS-end 2019: (0.11, 0.03, 0.6, 126) SR 5.2417 (gap +0.003)
  IS-end 2022: (0.11, 0.03, 0.6, 126) SR 4.9409 (gap +0.001)
  IS-end 2023: (0.11, 0.025, 0.6, 126) SR 5.2466 (gap +0.005)
tgt=.11 and lb=126 stable across all four; fr/thr NOT exactly stable and the doc's
"within 1e-3 SR" is false for 2016 (gap 0.017) and 2023 (0.005). The chosen (0.11,.03,.5,126)
is inside the near-flat plateau, so no material OOS implication, but the stability claim
as written is not exact. Also note tgt .11 is the GRID EDGE (doc discloses this honestly).

### F-11 (verified, SAFE-A rule): "vt .085 = max with IS(08-16) DD<=-7% margin"
On the committed 16-pool with thr .04: IS DD -5.65% at .085; compliant through vt .10
(-6.61%); breach at .11 (-8.36%). So .085 is NOT the max compliant (vt .10 also complies
with margin). The rule as stated ("max with IS DD<=-7% margin") would pick vt .10, not
.085. The GOAL80 provenance (frozen then) may explain it, but the spec's stated rule does
not reproduce the pick on the current pool. UNVERIFIED as described; harmless direction.

### Misc integrity checks
- All tracked champion files clean vs git HEAD; 8 UNTRACKED *CLEAN* files appeared in
  campaign/results/ during the audit window (Sep 1 14:24, after my audit started 13:59) —
  not generated by me; flagged for COORD (uncommitted parallel activity).
- Committed input sleeves: no NaNs mid-series; leading zeros (e.g. A5r7 292 rows,
  dualmom 436, A5r2/A5r4 60) enter as scale-0 warmup and are excluded via NaN semantics
  only where rows are absent. Warmup-zero handling confirmed conservative.
- Global-vt warmup makes the first 60 champion days cost-only (-0.156% cumulative):
  headlines INCLUDE this (slightly conservative).
- Champion daily extremes: BAL max +11.77% (2020-09-01), min -5.41% (2014-02-03);
  V4 max +18.77% with skew 4.54 / kurt 103.7 — V4's higher ann is substantially
  single-day-driven (brwt family); check before any live sizing.

## SUMMARY TABLE
| # | Finding | Severity | Materiality |
|---|---|---|---|
| F-1 | Throttle NaN-warmup (no throttle first 126d) | Minor | +0.05pp ann (B config) |
| F-2 | "MHX dilutive pre-entry" mechanism inverted; MHX adds +11.4pp post-entry | Doc error | framing |
| F-3 | Gross exposure 5.2-6.5x mean, >1x 97% of days; "no leverage PASS" false as stated | MAJOR | all headline metrics are levered-book numbers |
| F-4 | FINANCED series not reproducible (no script), understates full financing (-6.6pp vs my -19..-25pp bound) | MAJOR | live-achievable ann likely 30-45%, not 55.5% |
| F-5 | Costs charged on normalized (1x) weights vs true capital turnover | Minor | -0.16pp if corrected |
| F-6 | V3/V4 champions: no builder, doc misstates pool size (21->20, 16->15), V4 not byte-reproducible | MAJOR | reproducibility of current best systems |
| F-7 | 187 NYSE-closed days carry P&L (Dec 25 +4.66%/+5.89% etc), +0.75pp ann | MAJOR | tradeability + ann inflation |
| F-8 | Tail 40 days run on 1-5 sleeves | Minor | last 2 months not the advertised system |
| F-9 | LOYO/5y-CAGR doc numbers not reproducible (UNVERIFIED provenance) | Doc error | none on headline |
| F-10 | IS argmax "identical/1e-3" stability overstated (fr/thr vary; gap 0.017 in 2016) | Minor | selection integrity OK-ish |
| F-11 | SAFE-A vt.085 not the max under its stated IS rule (vt .10 also compliant) | Minor | rule provenance stale |

## WHAT IS SOLID (positive evidence, not absence of complaints)
1. Construction code is causally clean: proven by unit tests AND a full-pipeline perturbation
   test (0 pre-cutoff contamination). T+1 discipline in vt, throttle, costs is real.
2. Byte-exact repro of V1 (3 files) and 20Y_V2 (3 files) from committed sleeves + scripts.
3. Costs embedded and hand-verifiable; throttle switching costs charged; initial-deployment
   costs charged (conservative).
4. DD discipline claims (-6.9%/-7.2% mdd; every calendar year <= 7.0%) verified exactly.
5. OOS (2017+) beats IS for every variant I rebuilt — the disclosure is accurate.
6. Diversification math is real: mean pairwise corr 0.029-0.037 across 16 genuinely
   different engines; the SR~5-6 is arithmetic consequence, and monthly SR CI [3.2-4.4]
   still clears the SR>=2 goal with margin.
7. Keystone/robustness numbers (drop-one, cost stress 8/10bps, no-B3, scramble p<0.05)
   reproduce exactly.

## BOTTOM LINE
As a PIECE OF QUANT RESEARCH the pipeline is honest, causal, and reproducible through
V1/20Y_V2. As a TRADEABLE PRODUCT the headline "55.5% ann, no leverage, DD -6.9%" is
materially misleading: it is a ~5x-gross book whose full financing is not charged
(committed financed variant 48.9% uses an unexplained, non-reproducible convention;
a full charge points to ~30-45% ann), and it books P&L on 187 days when nothing could be
traded. The strongest defensible claims: SR (risk-adjusted, financing largely cancels in
SR terms but NOT in the "no leverage" claim), MaxDD <= 8% at the stated leverage, and the
existence of genuinely decorrelated engines. Docs must be corrected on F-2/F-6/F-9/F-10/
F-11 and the leverage disclosure (F-3/F-4/F-7) must move from caveats to the headline.

AUDIT DONE
