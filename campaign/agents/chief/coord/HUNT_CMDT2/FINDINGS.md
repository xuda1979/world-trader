# FINDINGS — HUNT_CMDT2 (commodity ETF cross-asset)

Round 1 per CHARTER.md (a) carry (b) XS momentum (c) sector rotation (d) inflation regime.
All numbers below are from actual runs of `campaign/scripts/HUNT_CMDT2_round1.py`,
`campaign/scripts/HUNT_CMDT2_extensions.py` (copy of this dir's `extensions_r1.py` + EXT-E),
and inline repros; logs reproduced 2026-09-07 (this incarnation re-ran everything after the
prior incarnation died on 429 rate limits before writing findings). Gates per
`../GATES_CONTRACT.md`, fail-closed. TDD suite `tests_tdd.py`: **7/7 green** (carry gross
bounded, carry+momentum no-lookahead truncation probes, FRED spot publication-lag invariant,
hold-3 weight-constancy, warmup trim, negative-SR-must-fail-scramble).

## Context: prior incarnation's state found on disk
`HUNT_CMDT2_round1.py` (16.7k), `tests_tdd.py`, `extensions_r1.py` and 5 sleeve CSVs (01:58)
already existed; `logs/HUNT_CMDT2.log` showed 3 consecutive 429 kills (19:51 → 02:12) and no
FINDINGS.md. Coordinator's aggregate FINDINGS.md already carried "cmdt sector-rot SR 0.40"
as a round-1 negative. This incarnation: verified TDD green, re-ran the full sweep +
extensions to regenerate every number, byte-verified the saved sleeves, closed two coverage
gaps (MOO never tested; plateau grid never computed), saved a reproducible extensions script,
and wrote this file. No new sleeve passed; verdict unchanged.

## Data reality (drives what was testable)
- `more_etf` has: USO UNG GLD SLV CPER CORN WEAT SOYB CANE (CORE9, common live window
  2011-12→2026-09) + DBC GSG DBA MOO GDX. **DBE, DBP, USCI, BNO, COPX are MISSING on disk** —
  the charter's ETF term-structure carry proxies (DBE/DBP/USCI) and BNO (energy curve spread)
  are genuinely unavailable, so (a) carry was proxied via FRED spot indices (below).
- Charter universe coverage: USO,DBC,DBA,GSG,CANE,CORN,SOYB,WEAT,MOO,UNG,SLV,GLD,GDX all
  tested; GDX entered via EXT-A/EXT-C, MOO via EXT-E (it was absent from the original sweeps).

## (a) COMMODITY CARRY — HONEST NEGATIVE
No futures curve on disk → carry = ETF-vs-spot basis: annualized 63d (log spot − log ETF) gap,
spot = FRED global index per complex delayed **37d** for monthly publication (TDD-invariant:
S[t] must equal latest print stamped ≤ t−37d). Long backwardation / short contango, quarterly.
| corrChamp | note
carry k1 h3: SR=0.24 ann=2.8% H1=−0.05 H2=0.73 negyr=7 worst=−24.9% scram_p=0.000 corr=0.033 FAIL
carry k2 h3: SR=0.19 ann=1.9% H1=−0.00 H2=0.59 negyr=6 worst=−20.3% scram_p=0.000 corr=0.033 FAIL
carry k3 h3: SR=−0.16; all h1 variants negative (k1 −0.10, k2 −0.16, k3 −0.08). 6/6 configs fail
SR/halves/yearly. Saved sleeve `CMDT_CarryBasis_k2_h3.csv` recomputes to meta exactly
(SR 0.193, n=3689). Rationale is sound (roll drag is real) but the ETF-vs-FRED-spot gap is too
noisy a proxy — 8 neg years in 14 for the family.

## (b) XS MOMENTUM — HONEST NEGATIVE (all 27 grid points + long-only)
CORE9, rank trailing months, long top-k / short bottom-k, hold 3m, T+1 (mom at i−1), vt10%.
Charter config **mom 12m k3 h3: SR=−0.12 ann=−4.1% H1=−0.30 H2=0.15 negyr=8 worst=−27.0%
scram_p=0.000 corr=−0.019 FAIL** (saved sleeve `CMDT_XSMom_12m_k3_h3.csv` verified).
Full grid months∈{6,9,12,15,18}×k∈{2,3,4}: best **9m k2 SR=0.27** (H1=0.09 fails halves),
15m/18m rows ~0.0–0.22, 6m row negative. Hold∈{1,2,3,6} on 12m k3: −0.02/−0.10/−0.12/+0.02.
Long-only worse everywhere (best 9m k2 LO SR=0.07; 12m k3 LO SR=−0.28). Scramble p=0.000 on the
positive rows (signal is "real" but economically negligible) — **SR gate 0/27**.
Extended universes (EXT-A/EXT-E): +DBC/GSG/DBA best 9m k2 SR=0.21; +GDX best 9m k2 SR=0.29
(H1=0.19, worst −19.9%); +MOO best 9m k2 SR=0.35 (H1=0.24, 5 negyr); EXT13(+MOO) best 0.23.
No universe or param cell approaches SR 1.0.

## (c) SECTOR ROTATION — HONEST NEGATIVE, family best
ENE(USO,UNG)/PRE(GLD,SLV)/AGR(CORN,WEAT,SOYB,CANE) baskets, sector momentum, monthly hold.
Charter 12m LS: SR=0.31. 6m LS: SR=0.45 ann=5.8% H1=0.49 H2=0.40 negyr=7 worst=−17.5%
scram_p=0.000 corr=0.006 FAIL (saved `CMDT_SectorRot_6m_LS.csv` verified). 3m LS 0.21; long-only
slightly below LS everywhere. 4-bucket variant with GDX as PMX (EXT-C): best 12m LS SR=0.24 —
adding gold-miners HURT (0.45→0.22 at 6m). Plateau grid months∈{3,6,9,12}×hold∈{1,2,3}
(12 fresh runs): peak **(6m,h2) SR=0.577** ann=7.7% H1=0.46 H2=0.69 negyr=6 worst=−8.4%
(saved `CMDT_SectorRot_6m_h2_LS.csv`; reproduces from `run_sector_rotation(months=6,hold=2)`
with max dev 9.99e-17) — but **plateau gate FAILS: only 25% of grid neighbors ≥80% of peak**
(6m h1 0.524, 6m h3 0.445, 9m h2 0.460, 3m h2 0.264…), and SR 0.58 << 1.0 anyway. A lone
grid point, not a strategy.

## (d) INFLATION-REGIME — HONEST NEGATIVE, and the gate adds nothing
Long equal-weight CORE9 (gross 1–2) only when T10YIE 63d trend > 0 (lag 5d) or CPI y/y
accelerating vs 6m ago (lag 37d); flat otherwise. Best: infl t10yie g2.0 SR=0.10 ann=0.4%
H1=−0.32 H2=0.50 negyr=10 worst=−13.9% corr=−0.014 FAIL (saved
`CMDT_InflRegime_T10YIE_g2.csv` verified); cpi mode SR=0.08 both grosses.
**EXT-D value-add control**: unconditional passive long CORE9 (same vt/cost) SR=0.08 vs gated
0.09 (t10yie, gate ON 52% of days) / 0.08 (cpi, ON 53%). The inflation gate is a coin-flip
on/off that does not separate good from bad commodity periods in 2007–2026.

## EXT-B — USO/UNG short-run reversal (charter-flagged redundancy check): DEAD
5/10/21d sign-reversal books, T+1: **USO rev5 SR=−0.50** (scram_p=0.570, i.e. NOT better than
random), rev10 −0.39, rev21 −0.46; UNG −0.05/−0.01/−0.24 (scram_p 0.08–0.28). 250 flips/yr ×
6.4bps eats any edge. Decorr is moot (corr 0.003–0.019) but there is no signal to decorrelate.
The charter's worry (redundant vs champion brwt/natgas) is answered: it never gets that far.

## Champion decorrelation (gate f)
Every config measured: |corr| 0.003–0.053 vs GOAL100_RAWEW13v2_WEIGHTED_GEAR16 — the whole
commodity-ETF space is essentially orthogonal to the champion. Decorrelation was never the
binding constraint; SR ≥ 1.0, halves, and yearly were (0/70+ evaluated configs passed ALL gates).

## Gates scorecard (summary)
- FULL net SR ≥ 1.0: 0 of ~70 configs (family max 0.577, charter-config max 0.45).
- Halves H1,H2 ≥ 0.5: 0 pass (closest: sector 6m h2 H1=0.46).
- Yearly ≤2 neg, worst >−5%: 0 pass (best worst-year −8.4% at 6 negyr — fails both counts).
- Scramble 200x (p≤0.05 AND SR>0): passes on all positive-SR rows (p=0.000); correctly FAILS
  on negative-SR books (TDD-enforced).
- Plateau: fails at the only peak worth discussing (25% of neighbors).
- Decorr |corr|<0.15: passes everywhere (moot).
- T+1/costs: enforced in `net_of` (6.4bps full |dW| + 0.5%/yr borrow, vt10% clip 3);
  TDD truncation probes confirm no lookahead in carry & momentum weight paths.

## Artifacts (contract item 4)
- `campaign/scripts/HUNT_CMDT2_round1.py` — full charter sweep (reproducible, run 2026-09-07).
- `campaign/scripts/HUNT_CMDT2_extensions.py` — EXT-A..E (copied from this dir's
  extensions_r1.py + appended EXT-E MOO block; re-run green, 26 configs).
- `sleeves/` 5 CSVs+metas: XSMom_12m_k3_h3, CarryBasis_k2_h3, SectorRot_6m_LS,
  SectorRot_6m_h2_LS, InflRegime_T10YIE_g2 — all status=FAILED_NO_PROMOTION, all recomputed
  to their meta values to the 3rd decimal this session.
- `tests_tdd.py` 7/7 green.

## Suggested DEAD_IDEAS.csv rows (via coordinator)
1. `commodity ETF XS momentum (CORE9/EXT13, rank 6-18m, hold 1-6m, L/S+LO),dead,best SR 0.35
    (CORE9+MOO 9m k2); charter 12m k3 h3 SR -0.12; 0/27 grid + all universe variants fail
    SR/halves/yearly; scramble-real but tiny,HUNT_CMDT2`
2. `commodity sector rotation ENE/PRE/AGR(+PMX),dead,family peak 6m h2 SR 0.577 but plateau
    25% (lone grid point) and H1 0.46<0.5; 4-bucket w/ GDX drops 0.45->0.22; 16 cells all
    fail,HUNT_CMDT2`
3. `commodity ETF-vs-FRED-spot basis carry (37d pub lag),dead,best k1 h3 SR 0.24, h1 variants
    negative; proxy too noisy, 6-9 neg years; no curve data on disk (DBE/DBP/USCI missing),
    HUNT_CMDT2`
4. `inflation-regime gate on commodities (T10YIE trend / CPI yoy accel),dead,gated SR 0.08-0.10
    vs passive 0.08 (no value-add, gate ON 52-53%); 4 configs fail,HUNT_CMDT2`
5. `USO/UNG 5-21d reversal,dead,SR -0.50..-0.01, USO scram_p 0.37-0.57 (worse than random);
    250 flips/yr*6.4bps; also resolves charter redundancy question (moot),HUNT_CMDT2`

## Verdict
**ROUND 1 = HONEST NEGATIVE for HUNT_CMDT2.** Commodity ETF momentum/carry/rotation/regime
offers no champion-eligible sleeve: ~70 evaluated configs, family-best SR 0.577 (lone grid
point, fails plateau+halves), charter configs at or below SR 0.45, all fail SR≥1.0, halves and
yearly gates; decorrelation was never binding. The charter-named curve/term ETFs (DBE/DBP/
USCI/BNO/COPX) don't exist in more_etf, so true futures-curve carry and the USO-vs-BNO spread
remain untestable until that data lands (round-2 charter item c should not assume BNO).

ROUND 1 DONE


## ROUND 2 (2026-09-07 03:30-04:45) — positioning-confirmed trend, CPER/ratio, energy curve proxy, UNG seasonal

Charter round-2 items executed. New code: `campaign/scripts/HUNT_CMDT2_round2.py` (main sweep,
reuses R1 TDD-green net_of/evaluate machinery) + `HUNT_CMDT2_round2_ext.py` (plateau grid,
ablation, EXT-F/G/H). New TDD suite `tests_tdd_r2.py`: **11/11 green** (R1 suite kept green at
7/7 after one test fix, below). RED first (0/11 with module absent), then 4 real bugs caught by
the traps: COT family filenames are `crude_wti_nymex`/`nat_gas_nymex` not `wti`/`nat_gas`;
spread must be formed from each EIA leg's INDEPENDENTLY-latest known print (aligned-pair
subtract + dropna paired a fresh WTI against a stale Brent); +1d EIA shift lands on Saturdays
so the daily grid must be calendar-day; UNG vol-scale warmup was silent 0-weight (fixed to
explicit flat-warmup). 2 test-side fixes: gate ffill semantics (weekly stamp -> daily holding)
and sign-constancy instead of weight-constancy for the vol-scaled seasonal.

### (a) POSITIONING-CONFIRMED TREND — HONEST NEGATIVE
9 COT-mapped ETFs (USO UNG GLD SLV CPER CORN SOYB WEAT CANE). Momentum (9/12m, k2/k3, hold3)
gated by each name's OWN COT spec net-pct-OI expanding percentile: weight zeroed DAILY when
|pctl| > 1-thr (crowded); COT as-of Tuesday + 3d release lag (TDD-invariant vs raw as-of
stamps, 100+ sampled days exact). 16 gated + 4 ungated configs, 2012-08->2026-09:
- **Charter-adjacent best: cotmom 9m k2 thr0.2: SR=0.25 ann=3.0% H1=0.02 H2=0.61 negyr=7
  worst=-39.1% scram_p=0.000 corr=0.002 FAIL** (saved `CMDT2_CotGatedMom_9m_k2_thr0.2.csv`,
  recomputes to meta exactly, n=3543).
- 12m rows NEGATIVE (k2 -0.04..-0.26, k3 -0.25..-0.38); k3 rows weak (0.14-0.24).
- Plateau FAIL at the peak: fine grid months{6,9,12} x k{2,3} x thr{0,.1,.15,.2,.25,.3,.4}
  (42 cells) peaks 0.245 at (9m,k2,thr0.2); only 2/5 neighbors >= 80% of peak ((9,3,.2)=0.217,
  (9,2,.25)=0.216 OK; (9,2,.15)=0.175, (12,2,.2)=-0.103, (6,2,.2)=-0.333 FAIL). 6m row is
  uniformly NEGATIVE (-0.21..-0.42) — the 'plateau' is a spike on a cliff edge.
- **Ablation (does the gate add value?): YES but tiny — paired deltas across 6 month/k cells:
  helps 3, hurts 0, ties 3 (e.g. 9m k2 +0.033, 12m k3 +0.061, 12m k2 +0.164 vs ungated).
  Ungated 9m k2 SR=0.21 (saved `CMDT2_CotMom_9m_k2_UNGATED_ablation.csv`).** The crowded gate
  is a small consistent improvement on a signal that is itself too weak (0.21 -> 0.25 << 1.0).
- EXT-H (hold robustness on 9m k2, 15 cells h{1,2,3} x thr{.1..,.3}): h1 0.09-0.22, h2
  0.13-0.24, h3 0.15-0.25 — every cell fails halves (H1 < 0.5 everywhere, max H1=0.13).
- EXT-G (copper COT gate on (b) books): cper trend 252d gated drops 0.23->0.10; ratio books
  stay deeply negative (-0.34/-0.57). Gate doesn't rescue copper either.

### (b) CPER TREND + CPER/GLD RATIO — HONEST NEGATIVE
CPER (USCP daily, 2011-11+): trend sign(trailing) 63/126/252d: SR **-0.16 / -0.11 / +0.23**.
Best cper trend 252d: ann=2.3% H1=0.25 H2=0.24 negyr=6 worst=-4.6% scram_p=0.005 corr=0.021 —
fails SR/halves (both halves ~0.25, need 0.5). Saved `CMDT2_CPERtrend_252d.csv`.
Ratio momentum (copper-in-gold): **catastrophically negative — 63/126/252d SR -0.60/-0.52/
-0.41**, 9-11 neg years, worst year -62.5%. The ratio consistently mean-reverts at every horizon
tested; naive ratio momentum is the WRONG sign family here (a reversal study, not done, would
need its own charter to be honest about it). Saved `CMDT2_RatioCPERGLD_252d.csv` (SR=-0.41).

### (c) ENERGY CURVE PROXY + UNG SEASONAL — HONEST NEGATIVE
- **BNO confirmed missing on disk** (R1; still true) → WTI-vs-BNO spread untestable. Proxy used:
  EIA spot WTI minus Brent spread trend (both daily from eia_weekly/, +1d publication lag,
  TDD-invariant vs raw prints). Sign -> USO long/short, 21/63/126/252d: SR **-0.38 / 0.00 /
  -0.30 / -0.11**, 11-15 neg years. The location spread has no usable trend signal for USO.
  Saved `CMDT2_SpreadWTIBrent_63d.csv` (SR=0.00). 21d variant scram_p=0.345 (worse than random).
- UNG seasonal (short Mar-Oct / long Nov-Feb, 60d vol-scaled 10%): **SR=-0.08 ann=-1.3%
  H1=0.17 H2=-0.32 negyr=10 scram_p=0.300 FAIL** (saved `CMDT2_UNGseasonal_volscaled.csv`).
  The classic seasonality is DEAD in 2007-2026 UNG total-return data. Decisive diagnostic: the
  WINTER leg (the one the seasonal is LONG) returned **-44.5%/yr ann** over the sample — UNG's
  roll decay swamps the calendar effect in both seasons. EXT-F constant-short harvest: vol-
  scaled SR=0.37 (H1=0.74, H2=-0.01, scram_p=0.090 — fails halves + scramble), raw SR=0.42
  ann=8.7% but scram_p=1.000 and -50.5% worst year. Saved `CMDT2_UNGshortdecay_volscaled.csv`.
  The only consistently-positive UNG book is "always short the decay", which is borrow/roll
  harvesting, not a strategy the gates are designed to admit (and it fails H2 + scramble).
- (d) sugar/canola ag rotations: dropped per charter (CANE=sugar already in (a); canola COT is
  span-FAIL in the DATA_COTMORE manifest).

### ⚠ Mid-session data refresh (provenance note)
While the first main sweep was running (~04:10), another agent refreshed more_etf USO/GLD/SLV
(04:15-04:20, GLD extended to 2004-11). The first sweep's family-best row (cotmom 9m k2 thr0.2
SR=0.46, n=3564) was computed on the MIXED state and did NOT reproduce. All numbers above are
from re-runs on the stable 04:20+ state; the plateau grid, EXT-H and the final sweep agree
exactly (0.245 at (9,2,0.2), n=3543, start 2012-08-02). The R1 suite caught the same refresh:
`test_momentum_hold3_weights_constant_between_rebals` failed with 53 'non-rebalance' weight
changes — root cause was the GLD history extension rotating the hold-3 rebalance PHASE (panel
start 2006-10 -> 2004-11 moves month-seq%3 from Oct/Jan/Apr/Jul to Nov/Feb/May/Aug), NOT
lookahead; the test had hard-coded a calendar-quarter phase assumption and now derives the
rebalance set from the engine's own month-sequence (hold discipline invariant preserved).
Both suites green on final state: 7/7 + 11/11.

### Gates scorecard (round 2)
- FULL net SR >= 1.0: **0 of ~95 evaluated configs** (family max 0.25 gated / 0.42 raw-UNG-short).
- Halves >= 0.5/0.5: 0 pass (closest: UNG short-only H1=0.74 but H2=-0.01).
- Yearly <=2 neg > -5%: 0 pass (best negyr=5 with worst -47.4%).
- Scramble 200x: positive-SR books pass (p=0.000-0.090); negative-SR books correctly FAIL.
- Plateau: FAIL at the only grid peak (2/5 neighbors).
- Decorr |corr|<0.15: passes everywhere (|corr| <= 0.058) — moot, as in R1.
- T+1/costs: enforced in net_of (6.4bps full |dW| + 0.5%/yr borrow, vt10% clip 3); new TDD
  invariants: COT release-day stamp, EIA publication lag, daily crowded-mask, truncation
  probes on all 5 weight paths (gated mom, cper, ratio, spread, seasonal).

### Round-2 artifacts (contract item 4)
- `campaign/scripts/HUNT_CMDT2_round2.py`, `HUNT_CMDT2_round2_ext.py` (reproducible, run 04:22-04:40).
- `tests_tdd_r2.py` 11/11 (+ `tests_tdd.py` fix, 7/7).
- sleeves/ 7 new CSVs+metas, all status=FAILED_NO_PROMOTION, all recompute to meta exactly:
  CotGatedMom_9m_k2_thr0.2 (0.245), CotMom_UNGATED_ablation (0.212), CPERtrend_252d (0.234),
  RatioCPERGLD_252d (-0.410), SpreadWTIBrent_63d (0.000), UNGseasonal_volscaled (-0.078),
  UNGshortdecay_volscaled (0.367).

### Suggested DEAD_IDEAS.csv rows (via coordinator)
6. `COT-crowded-gated commodity ETF momentum (9 names, expanding pctl gate, daily mask),dead,
    best 9m k2 thr0.2 SR 0.25; gate adds +0.03-0.16 paired vs ungated 0.21 but plateau 2/5 and
    12m rows negative; 60 cells fail SR/halves,HUNT_CMDT2`
7. `CPER copper time-series trend 63-252d,dead,best 252d SR 0.23 (H1/H2 0.25/0.24 fail halves);
    COT-copper gate drops it to 0.10,HUNT_CMDT2`
8. `CPER/GLD ratio momentum 63-252d,dead,SR -0.41..-0.60 (consistently wrong sign; mean-revert
    family),HUNT_CMDT2`
9. `WTI-Brent spot-spread trend -> USO (BNO missing, EIA proxy),dead,21/63/126/252d SR
    -0.38/0.00/-0.30/-0.11, 11-15 neg yrs,HUNT_CMDT2`
10. `UNG Mar-Oct short / Nov-Feb long seasonal (vol-scaled),dead,SR -0.08 scram_p 0.30; winter
    leg itself -44.5%/yr ann (roll decay swamps calendar); constant-short decay harvest 0.37
    fails H2+scramble and is not an admissible sleeve,HUNT_CMDT2`

### Verdict
**ROUND 2 = HONEST NEGATIVE for HUNT_CMDT2.** Positioning confirmation (COT crowded gate) is a
real but tiny improvement (+0.03..+0.16 paired, never negative) stacked on a commodity-ETF
momentum signal whose ceiling is SR~0.25 gated — nowhere near 1.0. Copper trend is marginal,
the copper/gold ratio actively loses money as momentum, the WTI-Brent location spread carries
no USO-trend signal, and UNG's calendar seasonality is dead (its only persistent feature,
roll decay, shows up only as an always-short book that fails the gates by design). 0/95
configs passed all gates; decorrelation again never binding. Twice-dead families per round-2
charter (xs momentum, sector rotation) were NOT re-tested; new round-2 families are now also
dead on this data. Remaining untestable until data lands: true futures curve carry (DBE/DBP/
USCI/BNO/COPX still absent from more_etf).

ROUND 2 DONE


========================================================================
ROUND 3 — 2026-09-07 (session 12:48 CST; resumption of the 429-starved 07:55 instance)
========================================================================
Round-3 context: my 07:55 instance completed charter (a) (fetch) at 09:02-09:06 then died
without writing anything. This session verified that work item-by-item rather than trusting
it, then executed (b) hunts TDD-first and (c) curation. DEAD_IDEAS.csv (101 rows) +
GATES_CONTRACT.md read FIRST per charter; the dead BNO-vs-USO location spread was NOT redone.

### (a) DATA UNLOCK: DBE/DBP/USCI/BNO/CPER fetched under the coordinator 2007-waiver — VERIFIED
Prior-instance fetcher `campaign/scripts/HUNT_CMDT2_round3_fetch.py` (two-window stitch 2005-2012
head + 2013-tail, prepend-only, head-wins-at-seam) wrote 5 series to tools/quant/data/more_etf.
Independent verification THIS session (nothing trusted):
- Disk lint from bytes: DBE n=4948 (2007-01-05->2026-09-04), DBP n=4699 (2008-01-02+),
  USCI n=4043 (2010-08-10+), BNO n=4091 (2010-06-02+), CPER n=3722 (2011-11-15+). All
  monotonic, 0 dup dates, max calendar gap 5d, 0 days |ret|>50%, all end 2026-09-04 (fresh).
- Seam integrity: all 5 series have date-coverage-ratio 1.000 vs DBC's calendar and STABLE
  pre-2013 vs post-2013 daily-return corr to DBC (DBE .908/.929, USCI .896/.815, BNO
  .868/.880, DBP .491/.315, CPER .406/.291) — no discontinuity at the 2012-12-31 stitch.
- Live-API provenance probe (fresh TwelveData calls 2026-09-07, 2026-08-20..09-05 window):
  max|live-disk| = 0.000000 for DBE/USCI/BNO over 12 overlapping closes each. Disk bytes ARE
  the vendor bytes.
- Manifest rows present with span_class=2007plus, status PASS_WAIVER. Manifest zero_ret_rows
  reconciled = LONGEST zero-run (CPER 9 flat closes -> 8 zero-rows, DBE 2->1, BNO 6->5),
  matching the R2 standup disclosure; my total-flat-day count is a different metric (374
  CPER etc), both internally consistent.
- Inception-limited spans disclosed everywhere downstream; no series was extended by force.

### (b) SPREAD MOMENTUM HUNTS — HONEST NEGATIVE (16/16 configs FAIL SR>=1.0)
TDD: tests_tdd_r3.py written RED first (0/7, module absent), then GREEN 7/7 after
implementing campaign/scripts/HUNT_CMDT2_round3.py. Traps encoded: truncation invariance on
both REAL books (no lookahead), adversarial sign map on a toy frame (long-the-winner, L/S
dollar-neutral), long-only never-shorts (flat in DOWN regime, no phantom weights), weight
bounds <= gross, >=1500 live days per book, trailing-only vol damp. One framework fix during
GREEN (re-export trim_warmup; positional leg columns in spread_vol_scale) — no engine bugs;
R1 net_of/evaluate machinery reused untouched.

Pair 1 — USCI vs DBC (front-month basket vs broad basket, roll-profile spread), span
2010-08+ (inception-limited, disclosed):
- L/S 21/63/126/252d: SR **-1.06 / -0.34 / -0.38 / +0.10**. Short-horizon spread momentum is
  an ANTI-signal (structural mean-reversion). Sign-flip NOT run (charter: do not re-tune a
  dead signal into a new config). Saved CMDT3_Sprd_USCI_DBC_LS_21d.csv (SR=-1.062, worst
  year -27.4%, 13 negyrs) as the diagnostic anchor.
- Long-only 21/63/126/252d: SR 0.16 / 0.23 / **0.31** / 0.10. Best cell (LO 126d) fails
  halves (H1=-0.11 vs H2=0.68) and yearly (4 negyrs, worst -24.9%). Saved
  CMDT3_Sprd_USCI_DBC_LO_126d.csv.

Pair 2 — DBE vs DBP (energy vs precious-metals baskets, sector RV spread), span 2008-01+:
- L/S 21/63/126/252d: SR 0.25 / **0.71** / 0.30 / 0.32. Family peak = LS 63d: ann 8.2%,
  H1/H2 0.78/0.63 (halves PASS), 2 negyrs BUT worst year -13.0% (yearly FAIL), scram_p 0.000
  (real), corrChamp 0.031. Fails gate (a) SR>=1.0 by 29% and gate (d).
- Long-only 21/63/126/252d: SR 0.40 / **0.65** / -0.01 / 0.18. LO 63d: H1/H2 0.59/0.71, 6
  negyrs, worst -6.9% (yearly FAIL on worst-year, not count). Saved CMDT3_Sprd_DBE_DBP_LO_63d.csv.
- PLATEAU TEST on the peak (gate b): a-priori neighbors 21d (0.25) and 126d (0.30) are BOTH
  < 80% of 0.71 -> 0/2, FAIL. A fine grid (42..105d in 7d steps) shows a 42-63d ridge
  (0.61/0.68/0.60/0.71) — reported for completeness but it is POST-HOC; selecting it would be
  p-hacking per charter. The 63d cell is a local bump, not a robust plateau.

Gates scorecard (round 3): FULL net SR >= 1.0: **0 of 16 evaluated configs** (family max
0.709). Halves: DBE-DBP 63d variants pass; USCI-DBC none. Yearly: 0 pass (closest: DBE-DBP
LS 63d negyr=2 but worst -13.0% > 5% limit). Scramble: all positive-SR books p=0.000 (signal
real but sub-gate); USCI-DBC LS 21d correctly fails as a negative book. Decorrelation |corr|
< 0.15: passes everywhere (|corr| <= 0.046) — never binding, third round running. T+1,
6.4bps FULL |dW|, 0.5%/yr borrow, vt10% clip 3: enforced by the R1 net_of (unchanged,
TDD-green). Contract item 4: 4 CMDT3_ sleeves + metas saved, all status FAILED_NO_PROMOTION,
all 4 recompute from CSV to meta EXACTLY (SR/ann/n/span verified programmatically).

### (c) DEAD_IDEAS CURATION — 3 corrections + 1 new row; one STALE EVIDENCE catch
Audited all 10 HUNT_CMDT2 rows against sleeves-on-disk and fresh re-runs:
1. STALE EVIDENCE CAUGHT: row "commodity ETF cross-sectional momentum" quoted R1 family-best
   "SR 0.35 (CORE9+MOO 9m k2)". Re-running the EXACT R1 EXT-E config on current data gives
   **SR=0.172** (H1=-0.04, 6 negyr, n=3543) — the R2-documented GLD history extension
   (2006-10 -> 2004-11) rotated the hold-3 rebalance phase. VERDICT UNCHANGED (0.172 still
   fails everything); row now carries the stale-evidence disclosure. Evidence sleeve saved
   (CMDT_XSMom_CORE9MOO_9m_k2_familybest.csv, SR=0.172).
2. Row "commodity ETF-vs-FRED-spot basis carry": quoted k1 h3 SR 0.24 with NO sleeve on disk
   (only k2 h3 was saved). Re-ran + saved CMDT_CarryBasis_k1_h3_familybest.csv: SR=0.238 —
   reproduces the claim. Row updated with the sleeve name (evidence now complete).
3. Row "WTI-Brent spot-spread trend": "BNO missing" basis updated — BNO is now on disk
   (fetched under the waiver) but the BNO-vs-USO location spread STAYS on the do-not-redo
   list per charter.
4. NEW row appended: "commodity spread momentum USCI-vs-DBC + DBE-vs-DBP ... ,dead,"
   (the full round-3 family with exact numbers above), source HUNT_CMDT2-R3.
DEAD_IDEAS.csv now 101 data rows, parses clean, 0 malformed (csv.reader check).
Regression: tests_tdd.py 7/7 + tests_tdd_r2.py 11/11 + tests_tdd_r3.py 7/7, all green on the
final tree.

### Verdict
**ROUND 3 = HONEST NEGATIVE for HUNT_CMDT2.** The data unlock worked exactly as intended and
the two genuinely untested commodity spreads are now tested: USCI-vs-DBC roll-profile spread
momentum is an anti-signal at short horizons and weak-positive-but-sub-gate elsewhere; DBE-vs-DBP
sector RV spread momentum has a real, scramble-surviving, champion-uncorrelated 63d core
(SR 0.71, halves 0.78/0.63, 2 negyrs) that still fails the SR>=1.0 gate by 29%, fails the
yearly worst-year gate (-13.0%), and sits on a plateau-FAIL spike. 0/16 pass. No promotion.
Remaining untested commodity affordances are all families DEAD_IDEAS already lists, or
require data not on disk (true futures curve terms).

ROUND 3 DONE


## ROUND 4 (2026-09-07 17:xx-18:xx CST) — AUDIT ROTATION (fraud-catch duty)
Charter: reproduce 6 DEAD_IDEAS.csv rows from FAMILIES OTHER THAN HUNT_CMDT2, from their cited
saved scripts (not their FINDINGS prose). Verdicts per row below; exact numbers from live runs
on the current tree (pandas 3.0.3 / numpy 2.4.6, same engine). Zero writes outside
coord/HUNT_CMDT2/ (the one script that saves, HUNT_TREASFUT_round{1,2}.py, was run under a
save_sleeve no-op wrapper — coord/HUNT_CMDT2/audit_r4_treasefut_noop_save.py — identical
computation, prints, and gates, nothing saved anywhere). Champion of record independently
re-verified via bt/verify_champion_r3_cmd.sh -> /tmp/cmdt2_r4_verify_champion.json: ok=true,
ann_cagr 37.195%, SR 3.181, MDD -6.692%, 0 neg years, gear 1.6 — matches charter exactly.

--- AUDIT 1. "LQD-TLT log-spread momentum 126d" + row-mates (HUNT_CREDIT2, line 51/52/53/54)
Script: campaign/scripts/HUNT_CREDIT2_round2.py (+ _gate.py, _gate2.py). REPRODUCED.
 - (a) LQD-TLT k=126: net SR **-0.31** (quoted -0.31), H1/H2 -0.24/-0.44 (quoted -0.24/-0.44),
   13 negyr (quoted 13), worst -32.7% (quoted -32.7%), scram_p 0.000 (quoted 0.000),
   corrChamp 0.141 (quoted 0.142, 1e-3 drift). k-scan 63/252 = -0.24/-0.17 (quoted identical).
 - (b) T10YIE k=63: SR -0.80, H1/H2 -1.10/-0.45, 21 negyr worst -35.3% corr -0.050 (all exact).
 - (c) 2s10s IEF/TLT k=21: SR -0.54, H1/H2 -0.59/-0.50, 21 negyr worst -17.9% corr -0.128
   (all exact); k-scan 5/10/42/63 = -1.38/-0.93/-0.45/-0.38 (quoted "all negative" ok).
 - (d) HY-stress gate: round2 main prints delta +0.184 vs the row's quoted +0.198 — traced to
   the dedicated battery (round2_gate.py): grid deltas +0.184..+0.237, era split 2008-12
   +0.041 / 2013-19 -0.062 / 2020-26 +0.276 (COVID-concentrated, quoted "COVID-concentrated"),
   top-6 gated days all 2020-03/04 champ +18.3/+14.4/+5.7/+5.0/+4.7/+4.1% (quoted +18.3/+14.4),
   vol-gate control +0.204 >= credit gate (quoted +0.224 same conclusion), lag T+2..T+10
   +0.172..+0.209, cost 17.52bps/yr, and true-BAML overlap 15/4805 days (quoted 15/4805).
   The +0.198 is one cell of a +0.18..+0.24 grid; the row's own conclusion (content-free)
   is what reproduces. VERDICT: REPRODUCED (delta point-estimate drift +0.198->+0.184 disclosed).

--- AUDIT 2. "HY-vs-IG spread momentum on real HY ETFs" + row-mates (HUNT_CREDIT2-R3, line 96)
Script: campaign/scripts/HUNT_CREDIT2_round3.py. REPRODUCED (all 5 books, every number).
 - HYG/LQD k=63: net SR **-0.87** (quoted -0.87), gross k-scan family nonpositive_peak,
   H1/H2 -0.74/-1.07 (quoted same), 18 negyr worst -27.5% (quoted same), eras -0.55/-0.70/-1.03
   (quoted -0.55/-0.70/-1.03), corrChamp 0.018 (quoted 0.018).
 - JNK/IEF k=63: SR -0.30 (quoted -0.30), H1/H2 +0.08/-0.81 (quoted same), 15 negyr worst
   -13.8% (quoted same), eras +0.15/-0.59/-0.66 (quoted same), corrChamp 0.116 (quoted 0.116).
 - HY carry TR proxy: n=753 2023-09-06..2026-09-04 (quoted 753 2023-09..2026-09), SR -0.78
   gross -0.37-adj family, H1/H2 +1.01/-1.98, 2 negyr worst -31.4% (all quoted same).
 - Buy-the-dip meanrev HYG/JNK z-scan 0.5/1.0/1.5/2.0 = -0.11/-0.13/-0.03/+0.19 and
   -0.30/-0.35/-0.26/+0.06 (quoted exactly), plateau FAIL both (good_neighbors empty).

--- AUDIT 3. "2s10s treasury steepener (duration-balanced, FRED CMT synth TR)" (HUNT_TREASFUT,
line 59) + same-family rows 60/61/74. Scripts: HUNT_TREASFUT_round1.py + _round2.py. REPRODUCED.
 - round1 curve k=21: SR **-0.11** (quoted -0.11), H1/H2 0.92/-1.45 (quoted 0.92/-1.45),
   31 negyr (quoted 31), worst -6.2% (quoted -6.2%); k-scan {5,10,21,42,63,126} =
   -2.48/-1.09/-0.11/0.40/0.62/1.12 — k=126: SR **1.12**, H1/H2 **1.96/0.11** (quoted
   1.12 / 1.96/0.11), 20 negyr, SR_08+ **-0.22** (quoted -0.22), cA6R7 **+0.216** (quoted
   0.216>0.15), cA1CR -0.216. naive/sym -0.82/-2.50 (quoted -0.82/-2.50). ALL EXACT.
 - Bonus reproduction, rows 60/61/74 in the same run: TIPS grid all cells negative (20y 0.05,
   long-only -0.06 worst -36.7% — quoted exactly); butterfly N504/t1.0 SR -0.78 H2 -1.00
   33 negyr (quoted -0.78/-1.00/33); intlcarry lag0/lag1 0.77/0.70 corr 0.310/0.319 9/13
   negyr (quoted 0.77/0.70, 0.319-0.328, 13 negyr at lag1).
 - round2 (row 75, HUNT_TREASFUT-R2): 12/12 configs reproduced exactly incl. kink_2s30 SR 0.52
   H1/H2 0.89/0.09 18 negyr, SR_08+ range [-1.32,-0.10] (quoted [-1.32,-0.10]), curve2s10s
   charter-dur k=21 SR -0.59, fly -0.95, level+regime overlays -0.23/-0.33.

--- AUDIT 4. "FX carry nominal (8-pair EW, IRSTCI01 diffs)" (HUNT_FXCARRY2-R2, line 64)
Script: campaign/scripts/HUNT_FXCARRY2_round2.py. REPRODUCED (every quoted figure exact).
 - carry-nominal-EW: n=5680 (quoted 5680), net SR **-0.004** (quoted -0.004), ann **-0.18%**
   (quoted -0.2%), 11 negyr (quoted 11), worst **-19.4% in 2008** (quoted -19.4% (2008)),
   H=(-0.13,+0.16) (quoted (-0.13,0.16)), corrChamp 0.028 (quoted 0.028), scr_p **0.760**
   (quoted 0.760). Year map matches row-by-row.
 - Same-run row-mates: spotonly SR -0.228 14 negyr; real-carry SR -0.131 (quoted -0.131);
   +mom63 -0.026 (quoted -0.026); vol-scaled -0.097 (quoted -0.097).

--- AUDIT 5. "SPY/EWH/EWM RS-momentum rotation" (HUNT_INTERNATIONAL2-R2, line 65)
Script: campaign/scripts/HUNT_INTL2_round2.py. **DIVERGED (numbers), VERDICT REPRODUCED.**
 - Current run: 9/9 configs FAIL SR>=1.0 — same verdict as the row, same gate pattern
   (RS252 halves pass 0.61/0.59, all yearly fail, scram_p 0.000 real, |corr|<=0.069).
 - BUT point numbers drifted: RS126_LS SR **0.47** vs quoted 0.41 (H1 +0.09 vs quoted -0.05);
   RS252_LS SR 0.60 vs quoted 0.62; corrChamp -0.008..-0.069 vs quoted -0.009..-0.072.
 - ROOT CAUSE (data vintage, not code): EWH/EWM were re-fetched 2026-09-07 03:41/04:13 and now
   start 1996-03-18 (vs the Aug-13-era files), so the panel starts 2006-09-26 n=5000 vs the
   quoted run's 2006-10-19 n=4983 — a 17-row alignment shift at the head, SPY unchanged
   (ends 2026-08-12 in both). The documented EWM 2015-12-21 split artifact is STILL in the
   current file (I measure -26.48% on 2015-12-21).
 - Split-adjusted sub-claim re-derived independently (x0.7352 on pre-2015-12-21 rows, per
   /tmp/hunt_intl2_r2_splitfix.log; the fix script itself was NOT saved — noted):
   RS252_LS **0.54** vs quoted 0.56, RS126_LS 0.41 vs quoted 0.35, RS63 -0.05 vs -0.04;
   0 days |r|>15% after adjustment, matching the log. Same ~+/-0.02-0.06 drift, verdict
   (18/18 FAIL; adjusted best 0.5x loses to long-SPY 0.73) unchanged.
 - NAMED FILE for the divergence: tools/quant/data/more_etf/EWH.csv + EWM.csv (Sep-7 re-fetch,
   unadjusted split still present, panel head extended 1996->) — evidence-code itself is fine.

--- AUDIT 6. "HUNT_COT_ITER11 COT level/delta positioning" (line 100 / line 56)
Scripts: campaign/scripts/cot_positioning_hunt.py + cot_delta_momentum.py + cot_delta_weekly.py.
**REPRODUCED with 1 UNREPRODUCIBLE sub-path (crash) + 1 crash bug found and TDD-pinned.**
 - cot_positioning_hunt.py (fade): 6/6 configs NEGATIVE — SR -0.62/-0.74/-0.92/-0.27/-0.16/-0.88
   for (26,1.5)(26,1.0)(52,1.5)(13,1.5)(26,2.0)(26,0.75), negyr 10-14, corrChamp ~0.00 —
   inside the quoted fade band SR -0.58..-1.15 (exact cells differ: COT files re-fetched
   TODAY 17:06, 869 rows ending 2026-08-25, after the original run).
 - cot_delta_momentum.py (follow): SR -0.83/-0.83/-0.71/-0.58 for mom_lb 1/1/2/4 — quoted
   follow band -0.65..-0.81; my -0.58..-0.83 straddles it (same data-vintage cause).
 - KEY DIAGNOSTIC re-measured independently (weekly alignment Fri-Fri): same-period
   corr(delta_pos, week ret) = **+0.149..+0.212** across all 9 markets (quoted artifact band
   +0.12..+0.22) vs next-week corr = **-0.110..+0.040** (quoted +0.03 forward) — the
   contamination-artifact diagnosis reproduces exactly.
 - BUG (new, fraud-catch duty): cot_delta_weekly.py CRASHES for every z_thr>0 config —
   line 60 `sig=np.where(...)` yields numpy.ndarray, line 62 `sig.shift(1)` raises
   AttributeError, silently swallowed by build_weekly's `except: nets[m]=None` (line 74-76),
   then pd.DataFrame(all-None) raises ValueError("If using all scalar values..."). Net: only
   the z_thr=0.0 config runs (SR -0.64, negyr 12/15, corr -0.04); 3 of 4 advertised configs
   unrunnable. TDD: tests_tdd_r4_audit.py 2 tests, RED as of this round (AttributeError +
   ValueError reproduced). NOTE the row's headline numbers come from the delta/level engines,
   which do reproduce — the dead verdict is unaffected — but the saved repro path is broken
   for 3/4 of its configs. NAMED FILE: campaign/scripts/cot_delta_weekly.py lines 59-62, 74-76.
 - UNREPRODUCIBLE (partial): the exact -0.65..-0.81 follow / -0.58..-1.15 fade cells cannot be
   bit-reproduced because more_cot/*.csv were re-fetched today (17:06) after the quoted run —
   disclosed as data-vintage drift, direction and magnitude of the negative verdict reproduce.

--- ROUND 4 SCORECARD
  reproduced            : 4 of 6 rows outright (CREDIT2-R2, CREDIT2-R3, TREASFUT R1+R2,
                          FXCARRY2-R2) — every quoted figure within 1e-3 unless noted.
  reproduced-with-drift : 1 (INTL2-R2: verdict identical 9/9 FAIL, point SR drift +/-0.02-0.07,
                          root cause = Sep-7 EWH/EWM re-fetch; named).
  reproduced-partial    : 1 (COT-ITER11: verdict + contamination diagnostic reproduce; 3/4
                          weekly configs CRASH on a real bug in the saved script; named).
  unreproducible (script missing) : 0 rows. 1 sub-artifact noted: INTL2 split-fix script was
                          never saved as a file (only its /tmp log + sleeve meta) — I re-derived
                          it from the logged spec instead.
  fraud found           : 0. All six families' negatives are REAL.
  new bugs filed by me  : cot_delta_weekly.py z_thr>0 crash (TDD red tests in
                          tests_tdd_r4_audit.py; fix belongs to HUNT_COT2's owner — I did not
                          modify their script).
  champion of record    : re-verified ok=true, ann 37.195% / SR 3.181 / MDD -6.692% / 0 neg yrs.
  regression            : my suites tests_tdd.py + _r2 + _r3 = 25/25 green on the final tree.
ROUND 4 DONE
## ROUND 5 (2026-09-08 04:55-06:3x CST) — pre-registered propane corner (DPROPANEMBTX) — HONEST NEGATIVE, 0/28

READ FIRST done: GATES_CONTRACT_V2.md (RATIFIED; §0 two tracks, §6 Step-1 leak_probe, §7
beats-passive trio, §9 span discipline) + DEAD_IDEAS.csv recounted = 120 rows (wc -l 121
incl header; no propane hunt row exists — only SKILL_ALPHAAGM's data-acquired row 21, so the
corner is NOT in any dead family; my own rows 75-94 untouched). No dead-family re-test, no
re-tuned dead signal: seasonality/trend/spread-MR on propane were never tested here (R1-R3
covered ETF xs-momentum, sector rotation, carry-basis, COT gates, USCI-DBC / DBE-DBP spreads,
inflation gates — all distinct families). Champion of record independently re-verified this
round: bash campaign/bt/verify_champion_r3_cmd.sh -> /tmp/cmdt2_r5_verify_champion.json:
ok=true, 7/7 checks (weights_repro, byte_repro, cost_reconciliation, causality, gross,
yearly, mdd), SR 3.18099, ann 37.195%, MDD -6.692%, worst year +7.31%, 0 neg years —
matches the charter quote exactly.

DATA (cited, row counts re-printed by the script at run time):
- tools/quant/data/more_fred/DPROPANEMBTX.csv  8559 data rows 1992-07-09..2026-09-01,
  0 NaN, median 226 real level-changes/yr (max stale-print run 10 days) — genuinely daily,
  NOT the invalid DPROPANEMTXCF id (never used).
- tools/quant/data/more_etf/UNG.csv  4878 rows 2007-04-18..2026-09-04 (spread leg + span
  bound); benchmarks twelvedata/SPY.csv n=5000, more_etf/IEF.csv n=6065,
  results/sleeve_library/CTA_15vol.csv n=4683; champion n=4805 2008-03-31..2026-08-27.
- Test span disclosed honestly: n=4854 2007-04-18..2026-09-01 (bounded by UNG inception for
  the spread book and by the pre-2007 pre-shale/no-LPG-export structural break which I
  decline to trade; the 1992-2007 propane history exists but would be a different market).

PRE-REGISTRATION (fixed grid written into campaign/scripts/HUNT_CMDT2_round5.py BEFORE any
backtest ran; no post-hoc cell added, per the no-retune rule):
  (1) SEASONALITY: long Nov-Mar / flat, and long Dec-Feb / flat, x vt on/off  -> 4 configs
  (2) TREND: win {21,63,126,252} x {long-only, L/S} x vt on/off               -> 16 configs
  (3) SPREAD MR propane-vs-UNG: z-hysteresis (z_in {1,2}, z_out 0) on the ln-ratio,
      win {21,63,126,252}, dollar-neutral, vt                                 -> 8 configs
Engine: T+1 (shift(1) effective weights), 6.4bps FULL |dW| + 0.5%/yr borrow (bt.engine),
trailing vt 10% ann clip 3.0 (bt.engine.vol_target_scale). V2 battery on every config:
gates.run(sig=<positions>, leak_check=True, ref=champion, beats_passive=True, spy/ief/cta
pinned trio) per GATES_CONTRACT_V2 §0 new-sleeve track + §6 Step-1 + §7.

TDD: tests_tdd_r5.py 7/7 GREEN (RED first — 6 failed before the module existed): data-shape
guard; T+1 We == W.shift(1) exact; no-lookahead truncation probe (weights byte-identical
before the cut when the tail is removed); PIT publication-lag (+1-day delayed prints
reproduce the same weights shifted one row, positional array_equal); zero-signal book
exactly flat; spread book dollar-neutral to 1e-12; V2 battery must publish leak dict +
beats-passive block. Regression: my R1-R3 suites 25/25 still green on the final tree.

RESULTS — all 28 configs FAIL the SR>=1.0 gate; none pass halves or yearly either; the
decorrelation gate is the ONLY gate every config passes (|corr|<=0.052 — decorrelation from
champion/energy slots was never the binding constraint, alpha absence was):

  SEASONALITY (family best SR 0.21): 12-02 novt SR 0.205 ann 2.1% H1 -0.02 H2 0.44 negyr 8
    worst -36.8% corr -0.023; 12-02 vt SR 0.159 H1 -0.02; 11-03 rows NEGATIVE (-0.104/-0.324,
    9 negyr) — the classic winter premium is NOT in the spot series post-2007 (H1 ~0 for the
    Dec-Feb long; the Nov-Mar extended shoulder months actively lose).
  TREND (family best SR 0.47): w21 long-only vt SR 0.465 ann 3.8% H1 0.60 H2 0.16 negyr 8
    worst -20.8% corr -0.019 — positive H1 collapses in H2; every other cell 0.11-0.33 with
    one sign of the halves negative; L/S variants all worse (halves always fail); novt rows
    have -32..-71% worst years.
  SPREAD MR vs UNG (family best local SR 0.61): w63 z2 SR 0.609 BUT H1 -0.51 / H2 0.45
    (13 negyr) — regime-flipped at the shale/LPG-export break (~2012), consistent with the
    family's -0.73/+0.53 H1/H2 at z1 w63; all 8 cells |SR| <= 0.61 with 9-13 neg years.

V2 BATTERY — full transparency incl. one CONVENTION DEFECT found and corrected (self-caught):
- In-sweep battery (metas, 'v2:' line): 28/28 pass=False. 28/28 leak_ok=True (same-period
  |corr| 0.002-0.065, all below the 0.20 MIN_ABS_CORR bar); 27/28 beats_passive FAIL (best
  passive sixty_forty SR 0.573); the single bp_ok=True cell (prop_spreadmr_w63_z2_vt,
  'sr 0.607') was an ARTIFACT — see below.
- DEFECT: I passed r=NET returns with sig=post-vt weights, so gates.run's internal sig*r
  book (its sr/halves/neg + the beats-passive candidate) judged a distorted reconstruction
  instead of the held book. Contract (gates.run docstring): r must be PER-UNIT so sig*r IS
  the held book. Re-ran the battery contract-correct on all 28 (r=per-unit, sig=held
  weights; script v2_meta_append_r5.py, evidence /tmp/cmdt2_r5_v2_correct.json) and APPENDED
  a 'v2_corrected:' line to all 28 metas (the distorted line retained above it, labeled):
  28/28 pass=False AGAIN — corrected v2 SRs -0.185..0.148 (real book, no vt scaling gap),
  leak_ok 28/28 True, bp_ok 0/28 (candidate loses to sixty_forty 0.573 everywhere — the
  corrected battery is STRICTER and kills the w63_z2 artifact, whose 0.607 came from
  double-scaling the vt weights against net returns).
- Either way the verdict is identical and honest: ZERO adoptable alpha. beats-passive alone
  rejects every config even before SR/halves/yearly do (propane spot books at 10% vol earn
  1-4% ann net vs 60/40's 0.573 SR on the same span).

DEAD_IDEAS rows appended (2): propane seasonality + propane trend/spread-MR (family-level
honest negatives with exact numbers, scripts + TDD cited).

VERDICT: R5 corner CLOSED as honest-negative. The frontier is UNCHANGED (ann 37.2 vs 80
goal). The champion's energy slots (brwt/diescrack/C5ng) remain unbeaten: the new corner's
best decorrelated book (trend w21 LO, corr -0.019) earns 3.8% ann at SR 0.47 with 8 neg
years — no blend battery case to answer (§8 moot; nothing to overlay).

Artifacts: campaign/scripts/HUNT_CMDT2_round5.py (pre-registered engine + battery),
coord/HUNT_CMDT2/tests_tdd_r5.py (7/7), coord/HUNT_CMDT2/v2_meta_append_r5.py (contract-
correct re-battery), 28 sleeve CSVs + metas coord/HUNT_CMDT2/sleeves/prop_*.csv(.meta),
/tmp/cmdt2_r5_sweep.log, /tmp/cmdt2_r5_v2_correct.json, /tmp/cmdt2_r5_verify_champion.json.
ROUND 5 DONE

## ROUND 6 (2026-09-08 12:1x-12:5x CST) — CONSOLIDATION: fraud-catch cross-verification of HUNT_COT2's R5 trader-count verdicts + commodities DEAD_IDEAS curation. No new corner (none pre-registered; charter 6c). ZERO fraud found; ONE real evidence defect + ONE ledger-duplication defect found and filed.

READ FIRST done: GATES_CONTRACT_V2.md re-read in full (Step-2 flip in force; all my gates.run
calls below pass sig= and leak_check=True explicitly). DEAD_IDEAS.csv recounted at round start:
**137 data rows, 0 malformed** (csv.reader; charter's "137 at R5-end" confirmed). Champion of
record re-verified fresh by me this session from the CSV bytes: sha256[:16]
**4358dfab95679b97** (exact match), n=4805 2008-03-31..2026-08-27, ann_geo **37.1954%**,
SR(ddof0) 3.1813, MDD **-6.6922%**, 0 neg years — matches the charter quote exactly.

### (a) FRAUD-CATCH: HUNT_COT2 R5 trader-count verdicts — REPRODUCED IN FULL, own code

Target claims (HUNT_COT2 FINDINGS R5 + r5_output.log): C9 dealerLong-count HIGH 1.5 (10 fin
fams) SR 0.590 / ann +2.76% / H1 0.79 H2 0.55 / negyr 3 / worst -14.26% / MDD -16.2 / scr_p
0.055 / corr +0.027, leak=False same_period_corr +0.0293 p 0.0658; C3 Tot_All LOW 2.0 (21 fams)
SR 0.335 / H1 0.30 H2 0.39 / negyr 3 / corr +0.007; C1 Tot_All LOW 1.5 SR 0.243 / H1 0.33 H2
0.21 / negyr 6 / corr -0.022. Charter-mandated BREAKs: nat_gas 2022-02-08 TotAll -86% (OI -49%),
lumber 2023-04-25 +105% (OI +234%). Verdict 9/9 FAIL full V2.

My reproduction, THREE independent layers (script saved:
coord/HUNT_CMDT2/audit_r6_cot_rebuild.py; written from the documented spec, ZERO lib_r5 /
lib_hunt imports — own expanding z, own release->T+1 mapping, own 6.4bps full-|dW| + 0.5%/yr
borrow costs, own EWMA vol target):

1. SAVED-BOOK recompute (own stats code on their r5_book_*.csv): C9 n=3951
   2011-01-18..2026-09-04 SR 0.590 ann 2.76% H1/H2 0.79/0.55 negyr 3 worst -14.26% corr +0.0271
   (n_common 3945); C3 n=4087 2010-07-06+ SR 0.335 H1/H2 0.30/0.39 negyr 3 worst -2.64% corr
   +0.0070; C1 n=4087 SR 0.243 H1/H2 0.33/0.21 negyr 6 worst -3.92% corr -0.0217. EVERY quoted
   figure matches to the last printed digit. (MDD mine -15.4/-7.1/-8.9 vs their -16.2/-7.3/-8.9:
   C9/C3 small cumprod-convention drift, C1 exact — verdict-irrelevant, no gate uses MDD here.)
2. FROM-SCRATCH REBUILD from the raw panel (DATA_COTMORE/work_r4/trader_count_panel.csv,
   29,017 data rows): my z == panel z column to max|dev| 4.4e-16 on all 21 unbroken
   family/col pairs; my rebuilt books match the saved C9/C3 CSVs with **max|dev| 1.0e-16,
   corr 1.000000 over 3951/4087 overlapping days** — bitwise reproduction of the published
   books. Engine-convention note (not a defect, disclosed): lib_r5 drops warmup-NaN gate rows
   BEFORE building the live mask, so books start at the first DEFINED z (C9 2011-01-18, not
   first release 2010-07-26). Under my initially-more-conservative keep-the-zero-head
   convention C9 is SR 0.581 over n=4073 (starts 176d earlier, verdict identical). Family
   counts verified independently: exactly 10 fin-proxy families have non-blank Dealer_Long
   within the proxy map (13 have the col; eurodollar_3m/sofr_3m/vix excluded no-proxy) =
   matches the log's "families used 10"; C3/C1 = 21 as claimed; C7 = 11 disagg.
3. V2 BATTERY re-run on MY rebuilt positions (gates.run(sig=<my positions>, leak_check=True,
   beats_passive trio pinned per §7c)): C9 pass=False, leak same_period_corr **+0.029269**
   p 0.06575 -> leak=False leak_ok=True (their true-sig probe: +0.0293 p 0.0658 — exact),
   beats_passive False (candidate 0.4929 vs sixty_forty), neg_years 3, halves 0.64/0.45 fail,
   scramble fail (scr_p 0.35 under gates.run's internal scramble; their lib eval_gates prints
   0.055 — both conventions fail the 0.05 bar; estimator-convention difference disclosed by
   them at 0.493-vs-0.590). C3 pass=False, leak +0.0577 p 0.0002 leak_ok=True, bp False.
   **The 9/9-FAIL verdict is CONFIRMED under the flipped default with explicit sig/leak args.**

BREAK numbers re-derived from raw panel (charter-mandated): nat_gas_nymex 2022-02-08 TotAll
281->40 = **-86%**, OI 1,162,813->590,294 = **-49%**; lumber 2023-04-25 TotAll 21->43 =
**+105%**, OI 1,136->3,794 = **+234%** — all four exact.

**Fraud-catch verdict: 0 fraud, 0 arithmetic error. Every HUNT_COT2 R5 number I could touch
reproduces bitwise or to the last printed digit from the raw artifacts with my own code.**
Bookkeeping note for the ledger (their file, their call): DEAD_IDEAS still has no row for the
trader-COUNT-breadth family itself (my all-field grep breadth/cnt_/trader_count/traders_tot/
participant = the same ZERO hits they reported 09:0x) — the gap they escalated twice stands;
rows 137/138 are RES_BASIS-R1's, not COT's.

### (b) DEAD_IDEAS commodities curation — 16 rows audited; ONE evidence defect fixed via append

Audited all 16 commodity-family rows (14 pre-existing + 2 adjacent propane rows from
DATA_FREDMORE/TIMESFM): every cited script exists on disk (HUNT_CMDT2_round{1,2,2_ext,3,
3_fetch,5}.py + extensions + tests_tdd_r5.py + team/agents/RES_BASIS/{run_hunt,robust_r1}.py);
all 5 R3-fetched ETFs still on disk (DBE 4949 / DBP 4700 / USCI 4044 / BNO 4092 / CPER 3723
lines, mtimes 09-07 09:0x = unmodified since fetch).

- Sleeve<->meta integrity: **45/46 of my sleeve metas recompute from CSV EXACTLY** (SR to
  5e-4, n, status=FAILED_NO_PROMOTION); the 46th (CMDT3_Sprd_DBE_DBP_LO_63d) is csv 0.6525 vs
  meta 0.652 = 3-decimal rounding, not a mismatch. All 28 propane metas carry BOTH v2 and
  v2_corrected lines as row 129 claims (28/28 verified by count).
- Row 129 EVIDENCE DEFECT (found, fixed by append-only correction row 138): prose+row quote
  trend w21 LO vt **SR 0.465** — that number is the DISTORTED in-sweep battery SR
  (local_sr 0.4648 in /tmp/cmdt2_r5_v2_correct.json = the r=net+post-vt-sig book the R5 entry
  self-caught), NOT the held book. Net book SR = **0.370** (sleeve CSV 0.3701, meta SR=0.370,
  sweep-log line 22 SR=0.37, v2_corrected v2sr=0.422). H1 0.60/H2 0.16/negyr 8/worst -20.8/
  corr -0.019 all reproduce exactly. VERDICT UNCHANGED (0.370 fails SR>=1.0 by 63%; beats-
  passive fails it identically) — a citation-precision defect, not an alpha claim. The
  spread-MR prose (0.609) was honestly labeled "local" and reproduces (local_sr 0.6088);
  seasonality 0.205 reproduces under engine conventions (ann_geo 2.1%, bt.metrics worst
  -36.8% — my arith-ann/-39.4% first pass was a convention mismatch on MY side, theirs is
  self-consistent).
- LEDGER DEFECT (filed, coordinator-owned to fix): lines 117-121 are **byte-identical
  duplicates** of lines 70-74 (five HUNT_MACRO2 rows: USREC / T5YIFR / VIXCLS / TOTALSL /
  slot-level T10Y2Y-JOINT; csv all-4-fields equal) — residue of the 09-08 RES_BASIS §4
  repair re-derivation. Dedup is a deletion = coordinator's lane per v1 item 5; I appended a
  correction row (139) instead of deleting. All 5 duplicated rows' evidence is correct per
  the owning agent; verdicts unaffected. Verified NOT defects: rows 75 vs 84 (84 = R2
  superset of 75, proper supersession); the RES_BASIS-flagged reconstructed HUNT_VOL2-R5 row
  (line 124) — all 9 spot-checked numbers present verbatim in
  HUNT_VOL2/work_r5/recommendation_r5.json (best dAnn -0.429/-0.404pp, dSR -0.0032, dH2
  -0.0424, 148/224 counts, max |leak corr| 0.063, placebo z +10.3/+12.5).
- RES_BASIS row-137 cross-checks while in the neighborhood: sleeve sha256[:16] recomputed =
  **da0285b9a7a5e6a2** (exact match to row/charter); their FINDINGS' "13/25 leak_ok True"
  vs my count 26/26 metas leak_ok=True today = metas re-emitted 10:32-10:43 (post-flip
  re-run), consistent with the coordinator's 11:4x integration review; adoption itself is
  CAMP_COST R6's — not mine to judge.
- Ledger after my appends: **139 data rows, 0 malformed, prefix byte-preserved** (asserted
  pre/post; my first append created a stray blank line — self-caught, removed, re-verified:
  137 old rows intact + my 2 correction rows at 138/139).

### (c) No new corner
None pre-registered this round; per charter 6c the R5 regime-split note stands (pre/post-2007
propane is a different market; no data-backed gap was registered). Nothing passed gates this
round (audit round); sleeves/ untouched today except reading; champion untouched (read-only);
no bt/ or other agent's file modified (audit_r6_cot_rebuild.py + FINDINGS.md + the 2
DEAD_IDEAS appends are my only writes). Regression: my suites tests_tdd{,_r2,_r3,_r5}.py =
**32/32 green** on the final tree.

Artifacts: coord/HUNT_CMDT2/audit_r6_cot_rebuild.py (from-scratch panel rebuild + stats +
BREAKs), coord/HUNT_CMDT2/work_r6/my_rebuild_{C9,C3}_net.csv (rebuilt books, bitwise-equal to
saved), evidence above re-derivable from the cited logs (/tmp/cmdt2_r5_sweep.log,
/tmp/cmdt2_r5_v2_correct.json, r5_output.log).

Verdict: **ROUND 6 = CLEAN AUDIT.** HUNT_COT2's R5 trader-count negative is real, bitwise
reproducible, and verdict-stable under the flipped leak default; the commodities ledger is
accurate up to one SR-convention citation (fixed) and one coordinator-owned duplication
(filed); the frontier is UNCHANGED (ann 37.195% vs 80 goal).

ROUND 6 DONE

## ROUND 7 (2026-09-08 19:0x-19:1x CST) — charter (a) FRAUD-CATCH audit of HUNT_TREASFUT-R6's GOAL80 quarantine + (b) DEAD_IDEAS recount

Read first: coord/GATES_CONTRACT_V2.md (in force; no gates.run battery this round — audit-repro
round, sig=/leak_check n/a) + DEAD_IDEAS.csv recounted by ME at round start (see (b)).

### (a) Independent rebuild — every charter pin REPRODUCED, zero discrepancies
Method (TDD, own code): tests_tdd_r7_audit.py (NEW, 7 tests) written FIRST pinning the charter
numbers; my OWN builder is a fresh re-implementation of the documented recipe inside the test
module (raw-first per-sleeve vt@0.10 cap8 rolling60 shift1 on each sleeve's OWN index, EW mean,
global vt@0.08, 126d DD-throttle 4% FR0.5, 6bps HALF-turn blend+throttle, start 2008-09-01,
min_hist>=750) — no import of goal80_own_build.py, no import of AUDIT_CHAMP2 code. All 14 pool
inputs verified present (shas printed in the run log; dualmom = their b268e52~1 pin).
RED-first proven by a mutation check: dragging the drag pin 5.2644->5.5 turns test_e RED,
restore -> 7/7 GREEN (suite is claim-sensitive, not vacuous). One TDD-caught bug of mine: the
WT path needed 5 ups (HUNT_CMDT2 is one level shallower than their work_r6) - FileNotFoundError
RED, fixed, GREEN.

- Blob pin re-extracted FRESH by me: `git -C ~ show b268e52~1:software/world-trader/.../QA_dualmom_band121.csv`
  -> sha256[:16] 7132a167f70f3a6c, BYTE-IDENTICAL to their work_r6/dualmom_pre_myblob.csv
  (provenance clean: commit b268e52 "champion costfix re-emit" is exactly what rewrote
  QA_dualmom_band121.csv, so current-tree sha 7462a8dfa391b18f != blob — expected).
- Byte-exact: MY rebuild vs committed campaign/results/COORD_FINAL_daily.csv maxdev 1.0148e-16,
  n=4696, 2008-09-01..2026-08-28. Builder-agreement: MY builder vs THEIR goal80_own_build.py
  maxdev < 1e-12 at n=4696 (two independent implementations, same construction).
- Undamaged context pins (their R6 headline): arith 43.1918 / CAGR 53.3570 / SR 4.8373 /
  MDD -7.4817 / 0 neg yrs / worst +7.1263 — all reproduce to the 4th decimal.
- R7 CHARTER PINS (the quarantine numbers): POS-days n=4636, gross med 2.1303 / mean 2.1665 /
  p90 2.9812 / max 5.2947 (code cap 8.0 respected; realized max global scale 5.3249);
  financing drag (max(gross-1,0)*4.5%/252, POS-days) = 5.2644 %/yr — EXACT;
  financing-priced: arith 37.9947 (claim 37.9947) / CAGR 45.6044 (claim 45.6044) /
  SR_d 4.2629 (claim 4.2629) / MDD -9.2731 (claim -9.2731) / 0 neg yrs — ALL EXACT to 4dp;
  MDD -9.2731 breaches GOAL80's own DD<=8% envelope (verdict stands: keep GOAL80/GOAL100
  quarantined; financing-unpriced exposure is real).
- Costed-B3 re-derived: arith 43.1918 -> 41.9502 = -1.2416pp swapping ONLY B3momhml for
  E1_20yspan/work/B3momhml_costed.csv (claim -1.24pp) — CONFIRMED material.
- Blob pin LOAD-BEARING re-verified on the current tree (their test_6 direction, re-proven by
  MY test_g): rebuilding with current-tree QA_dualmom_band121.csv diffs the committed artifact
  at maxdev 1.1080e-3 (>> 1e-6) -> the b268e52~1 pin is load-bearing and their test_6 still
  FAILS the byte-exact expectation by design (I re-ran their tests_tdd_r6.py: 7/7 GREEN).

VERDICT: HUNT_TREASFUT-R6 audit = CLEAN. All claimed quarantine numbers reproduce exactly
under my own implementation; no fraud, no drift, no convention games found. Per their R6 duty
note and my charter, NO append to TRUTH20Y_QUARANTINE.md (nothing discrepant to record).

### (b) DEAD_IDEAS recount
145 data rows (146 lines incl. header) at my round start, re-recounted 145 at round end,
0 malformed field-count rows, trailing newline intact. No append by me this round (audit
reproduced an existing verdict; no new dead family — charter (c) explicitly pre-registers no
commodity corner this round, so nothing to add).

### Regression + hygiene
My suites on the final tree: tests_tdd{,_r2,_r3,_r4_audit,_r5,_r7_audit}.py = 41/41 GREEN
(34 prior + 7 new). HUNT_TREASFUT tests_tdd_r6.py re-run by me: 7/7 GREEN. Champion of record
untouched: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha256[:16] re-verified 4358dfab95679b97.
Ledger prefix byte-preserved (I appended nothing). bt/ and campaign/*.md UNTOUCHED by me —
git shows pre-existing M flags across bt/{README,engine,metrics,reconcile,shortability}.py +
7 test files from the in-flight AUDIT_GATES2 R7 (their charter lane), flagged for the
coordinator. My writes this round: tests_tdd_r7_audit.py (new), FINDINGS.md (this append).
Files read-only: HUNT_TREASFUT/{work_r6/*, tests_tdd_r6.py, FINDINGS.md}, AUDIT_CHAMP2/work/r5/*,
COORD_FINAL_daily.csv, all 14 pool sleeves.

ROUND 7 DONE
