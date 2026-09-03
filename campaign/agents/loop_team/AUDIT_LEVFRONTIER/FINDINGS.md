# AUDIT_LEVFRONTIER — FINDINGS (2026-09-03, iter 6b)
Agent: loop_team/AUDIT_LEVFRONTIER. Read-only on campaign except this dir + scratch/. All
numbers below are FRESH runs in this session (builders re-verified first). Scratch code:
scratch/levfrontier.py (engine), test_gates.py (RED), test_green.py (GREEN), task1_frontier.py,
verify_geo_law.py, task23_v3.py, task3_final.py, task2_charter_table.py, task4_model.py,
task4_ledger.py, task5_candidate.py, task5b_verify.py, task5c_blotter.py.

## METHOD + TDD EVIDENCE (superpowers contract)
- FRESH builder verification BEFORE any work: `honest13_build.py --verify/--verify-v3` → 6/6
  files IDENTICAL, max|new−old| = 9.986e-17..9.996e-17 (V2 BAL 9.986e-17, V3 BAL 9.988e-17).
  `honest11_build.py --fixed` re-emitted FIX BAL → git diff vs HEAD EMPTY (byte-identical,
  4989 rows) — no committed file modified by any audit step (git status clean on results/).
- TDD RED observed (test_gates.py, stub engine): G2 cap gate FAIL (max gross 11.3917),
  G3 margin gate FAIL (delta 0.00pp), G4-POOL11 repro FAIL (2.481e-02 — wrong builder used,
  fixed by switching to honest11 FIX recipe). GREEN (test_green.py, final engine): 9/9 PASS —
  G1 byte-repro V3 SAFE 9.996e-17 / V3 AGGR 9.986e-17 / V3 BAL 9.988e-17 / V2 BAL 9.986e-17;
  G5 POOL11-FIX BAL 9.986e-17; G2 max gross = 1.600000 exactly (mean 1.5018 SAFE/1.5196 AGGR);
  G3 margin delta −2.901pp; G4 cost identity max|diff| 1.735e-18.
- Engine: kappa_t = min(1, 1.6/gross_t) on the EXACT committed position path (rebuilt
  byte-exactly), 6.4bps/side on tw + throttle + capped position-path turnover, borrow 0.5%/yr
  scaled, margin = (gross_capped−1)+ × rate/252. All stats quoted 2008-03-31..2026-08-27
  (n=4713), ann = geometric (campaign convention).

## TASK 1 — HONEST FRONTIER @ capital-real ≤1.6x, financing charged (base 4.5%/yr, sweep 3–6%)
Reference (committed, uncapped, 6.0bps, margin FREE): V3 BAL ann_geo 43.61% SR_d 3.924 MDD −4.92%
vol 9.34% 0/19 neg; SAFE 37.51/3.927/−4.87; AGGR 49.96/3.912/−5.42.
@1.6x cap + margin charged, 6.4bps/side, borrow 0.5%/yr (n=4713):

| build | margin | ann_geo | SR_d | SR_m | MDD | vol | neg | worst yr | gross mean | days>1.6 |
|---|---|---|---|---|---|---|---|---|---|---|
| V3 BAL | 3.0% | 17.98% | 3.820 | 3.394 | −3.51% | 4.35% | 0/19 | +4.81% | 1.527x | 0.0%† |
| **V3 BAL** | **4.5%** | **16.99%** | **3.628** | **3.221** | **−3.59%** | **4.35%** | **0/19** | **+3.88%** | **1.527x** | **0.0%†** |
| V3 BAL | 6.0% | 16.02% | 3.436 | 3.048 | −3.67% | 4.35% | 0/19 | +2.97% | 1.527x | 0.0%† |
| V2 BAL | 4.5% | 17.16% | 3.643 | 3.234 | −3.58% | 4.38% | 0/19 | +4.04% | 1.526x | 0.0%† |
| V2 BAL | 3.0% | 18.15% | 3.834 | 3.406 | −3.50% | 4.38% | 0/19 | +4.97% | 1.526x | 0.0%† |
| V2 BAL | 6.0% | 16.19% | 3.452 | 3.062 | −3.66% | 4.38% | 0/19 | +3.13% | 1.526x | 0.0%† |
| V3 SAFE | 4.5% | 16.77% | 3.612 | 3.267 | −3.44% | 4.32% | 0/19 | +3.83% | 1.519x | 0.0%† |
| V3 AGGR | 4.5% | 17.22% | 3.637 | 3.170 | −3.75% | 4.40% | 0/19 | +3.93% | 1.535x | 0.0%† |
| POOL11 BAL | 4.5% | 19.04% | 3.737 | 3.331 | −4.55% | 4.70% | 0/19 | +4.24% | 1.549x | 0.0%† |
| **POOL11 BAL** | **3.0%** | **20.05%** | **3.916** | **3.495** | **−4.51%** | **4.70%** | **0/19** | **+5.07%** | **1.549x** | **0.0%†** |
| POOL11 BAL | 6.0% | 18.04% | 3.557 | 3.168 | −4.60% | 4.70% | 0/19 | +3.40% | 1.549x | 0.0%† |
| POOL11 AGGR | 4.5% | 19.42% | 3.751 | 3.269 | −4.95% | 4.76% | 0/19 | +3.86% | 1.559x | 0.0%† |

†Cap-breach audit (root-caused, fresh evidence): a first diagnostic printed "days>1.6" up to
5-6% on SAFE/AGGR — that counted float64 round-off on cap-saturated days (max overshoot
2.220e-16 = κ·gross−1.6 in binary floating point). Correct statistic on the V3 SAFE leg 2008+:
days AT cap (|g−1.6|<1e-12) = 86.9% (raw gross >1.6 on exactly those 86.9% of days, raw mean
3.045x), days exceeding 1.6+1e-9 = **0.000%**, max overshoot 2.2e-16. The cap HOLDS to machine
precision on every build; the "days>1.6" column is therefore 0 for all rows (the BAL rows'
earlier 0.2% were the same round-off artifact).
CONFIRMED: the ceiling at the goal's own 1.6x cap with honest 4.5% financing is **16.99%**
(V3 BAL) and the best-of-family is POOL11 BAL 19.04% (20.05% at 3% margin; 18.04% at 6%).
The charter's "~17-20%" band is confirmed EXACTLY: 17.0–20.1%/yr. Every build stays 0/19 neg
years, MDD −3.4…−5.0% (DD budget is the one goal comfortably met).
Margin arithmetic verified: V3 BAL margin paid mean 2.509%/yr (arith), geo ann 19.97→16.99 =
−2.97pp (G3 gate: −2.901pp on the SAFE leg); margin return-corr +0.035 (≈0, pure drag).

## TASK 2 — REQUIRED SPEC TABLE (the hunting target)
Setup: old block = REAL capped V3 BAL@1.6x+4.5% path (ann_geo 16.99%, vol 4.35%, SR 3.628,
gross mean 1.527x). New engines: K independent engines, per-engine NET SR s at instrument vol
10% (net of internal costs/borrow), corr 0 to each other and to the pool (ideal — optimistic),
slot mass W added to the book, whole book budget-filled to ≤1.6x gross (day-level cap, never
breached), margin 4.5% on (gross−1). 150 seeds, median seed stats; W* = ann-argmax s.t.
MDD-5th-pct ≥ −7%:

| K new | s | W* | ann_geo% | SR | MDDmed | MDDp95 | hits 80%/5/7? |
|---|---|---|---|---|---|---|---|
| 4 | 1.0 | 0.4 | 14.2 | 3.45 | −3.31 | −4.99 | no/no/YES |
| 4 | 1.5 | 0.6 | 18.7 | 3.88 | −3.55 | −5.64 | no/no/YES |
| 4 | 2.0 | 0.8 | 27.9 | 4.24 | −4.34 | −6.22 | no/no/YES |
| 6 | 1.0 | 0.4 | 14.2 | 3.69 | −2.97 | −3.96 | no/no/YES |
| 6 | 1.5 | 0.8 | 20.9 | 3.95 | −3.69 | −5.30 | no/no/YES |
| 6 | 2.0 | 1.0 (all-new) | 33.8 | 4.49 | −4.59 | −6.69 | no/no/YES |
| 8 | 1.0 | 0.6 | 14.4 | 3.80 | −2.87 | −4.06 | no/no/YES |
| 8 | 1.5 | 1.0 | 23.6 | 3.77 | −4.62 | −6.44 | no/no/YES |
| 8 | 2.0 | 1.0 | 33.7 | 5.16 | −3.59 | −4.52 | **no/YES/YES** |
| 10 | 1.0 | 0.4 | 14.2 | 3.91 | −2.58 | −3.28 | no/no/YES |
| 10 | 1.5 | 1.0 | 23.8 | 4.23 | −3.76 | −5.30 | no/no/YES |
| 10 | 2.0 | 1.0 | 33.8 | 5.81 | −2.86 | −3.79 | **no/YES/YES** |

KEY NUMBERS (all-new book, budget-filled 1.6x, v=10%): ann_geo ≈ exp(0.16·s − 0.028) − 1 —
**K-INDEPENDENT** (adding engines under a gross cap buys SR/MDD, NOT ann: K cancels because
fill = 1.6 and ann = fill × s × v × 1.6 − costs). s=1.0→14%, s=1.5→24%, s=2.0→34%, s=3.0→57%,
s=4.0→84%, s=5.2→123%. The best engine ever delivered in this campaign is CFX4 (s=1.91) →
a full 1.6x-book of CFX4-quality engines = **32.0%/yr**, i.e. ~40% of the 80% goal.
Gauss-sim MDD law: MDD_p95 ≈ 3·σ/(2·SR). At ann-binding (vol 16% book, SR 5.2): −4.6% ⇒ DD
goal is NOT the binding constraint once SR ≥ 5; below that it binds (K=1 cells).

## TASK 3 — MINIMUM NEW-ENGINE BAR (proof of infeasibility)
All-new book, instrument vol v, K engines (net SR s each, corr 0), filled to 1.6x, margin 4.5%:
- ann_geo(s) = exp(1.6·v·s − 2.7% − (1.6·v)²/(2K)) − 1  → ann-binding s* = [ln 1.8 + 0.027 +
  (1.6v)²/2K]/(1.6v). Closed form cross-validated by independent solver + 600-seed MDD sim.
- REQUIRED per-engine NET SR s* (ann ≥80% geo AND SR_net ≥5 AND MDD_p95 ≥−7%):

| K | v=8% | v=10% | binding gate |
|---|---|---|---|
| 1 | 4.87→MDD | 10.64→**11.29** | MDD/SR (single engine needs SR>11 for DD≤7 at 80%) |
| 4 | 4.82 | 3.86 | ann |
| 6 | 4.81 | 3.86 | ann |
| 8 | 4.81 | 3.85 | ann |
| 10 | 4.81 | 3.85 | ann |
| 14 | — | 3.85 | ann |

- READ as the hunter's bar: **~10 new engines each NET SR ≥ 3.9 at 10% instrument vol, corr≈0**
  (or ~4 engines at SR ≥ 4.8) reach ALL of ann≥80/SR≥5/MDD≤7 at 1.6x. For context the campaign's
  6-year best is ONE engine at 1.91. Corr>0 makes it strictly harder: at avg corr ρ the effective
  K is K/(1+ρ(K−1)) — at ρ=0.3, K=10 behaves as K≈3.3 (s* rises to ~4.6).
- FEASIBLE-IN-PRINCIPLE, NOT ON ANY KNOWN DATA DOMAIN: nothing on-disk (FF premia, industries,
  BAB, ivol, carry, basis, COT, overnight, FX micro) has produced even one net-SR-3.9 engine;
  the best negative-evidence ledger (DEAD_IDEAS.csv, 22 families) plus 6 iterations of hunts
  (60+ overlay variants, SR 1.9 max) make the pragmatic verdict: **the 5-goal set is not
  reachable with honest financing on any data domain tried; it requires ~10 CFX4-beating engines
  (2x the best-ever) simultaneously.** Ann at the actual frontier: 16.99–20.05%/yr.
- Identities VERIFIED fresh: geo law on real path −0.005pp (measured 16.994% vs
  exp(SR·σ−σ²/2)−1 = 16.999%); margin G3 −2.901pp; uncapped law check 43.61% vs 43.64% law.

## TASK 4 — COST/BORROW/SHORTABILITY MODEL END-TO-END (lowest-leverage honest build)
Per-sleeve ledger (committed net files, 2008-03-31+): brwt15 26.16%/SR 2.44/−7.85% MDD 0/19
REAL; brwt10 32.53/2.97/−8.44 0/19 REAL; brwt7 32.14/3.19/−5.60 0/19 REAL; brwt5 30.92/3.10/
−9.28 0/19 REAL; C5ng 22.49/1.64/−31.04 0/19 REAL; C5ngsum 28.41/2.21/−11.76 0/19 REAL;
A5r2 8.96/1.02/−12.80 2/18 REAL; a6r7 7.64/1.22/−10.76 2/19 REAL; QAxasts 12.17/1.08/−12.98
1/19 REAL; carryv2 7.53/0.77/−12.84 3/19 REAL; dualmom 9.71/0.90/−24.47 1/19 SYNTH;
diescrack 7.83/1.01/−9.07 1/19 REAL; CFX4 14.91/1.91/−9.26 2/8 SYNTH; FF2 9.06/1.04/−11.24
2/19 SYNTH (research-only).
**LOWEST-LEVERAGE HONEST BUILD (new, this audit): RAW-EW14 — each sleeve at slot 1/14 of NAV
(instrument-notional slots, NOT vol-scaled), plain EW of the 14 net files. Gross ≤ 1.0x BY
CONSTRUCTION (no margin, capital-real 1.0x), ann_geo 18.57%, SR_d 4.306, SR_m 3.674, MDD −2.55%,
vol 3.98%, 0/19 neg, worst yr +7.76% (n=4805).** Costs at this level: EW-reset turnover
1.8bps/yr (2 years ≈ nothing); borrow already inside the sleeve files. RAW-EW11 (pool only):
20.46%/4.172/−2.73% 0/19. Accounting gaps found: (1) gross>1 in the committed build comes ONLY
from the vt overlays (per-sleeve scale book mean |scale|·Σ = 0.993x/sleeve, mean |d scale|
0.0258/day = 41.6bps/yr at 6.4bps — cheap because scales are slow); (2) the committed build's
known ~4% gap-turnover undercharge stands (blotter.py AUDIT_FINDING, BLOTTER_TESTER owner);
(3) margin financing on gross>1 remains THE dominant uncharged cost in the committed champion
(43.61% quote); (4) rebalance-cost skipna gap documented, futures-style vs equity-style
resolution owned by BLOTTER_TESTER.

## TASK 5 — RECOMMENDED NEW HONEST CHAMPION (emit candidate)
**RAW-EW14 geared to constant 1.6x: slot 1/14 per sleeve, daily EW-reset, GEAR=1.6 constant,
margin 4.5%/yr on 0.6x, 6.4bps/side on reset turnover (1.8bps/yr).**
- GATES (fresh): gross = 1.600000 every day (G-A PASS); margin reduces ann 31.18→27.69
  (G-B PASS); PnL identity max|diff| 0.000e+00 (G-C PASS); +1-day exec-lag probe: SR 3.877 →
  3.877 (delta −0.000, no timing artifact; passive book — no signal, T+1 trivially satisfied).
- **ann_geo 27.69%, SR_d 3.877, SR_m 3.278, MDD −4.18%, vol 6.36%, 0/19 neg, worst yr +9.50%,
  H1 3.606 / H2 4.134, OOS17+ arith 26.06%** (n=4713).
- Robustness: margin 3%→28.85%/SR 4.019, 6%→26.55%/3.736; start 2012 26.94%/4.058, 2017
  29.50%/4.116, 2020 30.66%/3.930; no-FF2 variant 28.89%/3.884 (FF2 removable — recommend
  dropping FF2 as research-only: 13-eng version is BETTER and kills the research-only flag).
  POOL11-only RAW-EW@1.6x honest: 30.93%/3.793/−4.46%.
- **Refined recommendation: emit RAW-EW13 (drop FF2) @1.6x: ann 28.89%, SR 3.88, MDD −4.25%,
  0/19 neg — dominates the current capped champion (V3 BAL@1.6x+4.5% = 16.99%/3.628/−3.59%) on
  ann AND SR at comparable DD, with FULL margin honesty and a byte-reconciled blotter.**
- vs goal set: ann 80% NO (28.9 vs 80), SR 5 NO (3.88, CI from AUDIT_V2 ≈[3.5,4.3] excludes 5),
  MDD ≤7 YES (−4.25), leverage ≤1.6 YES (exactly 1.6, G-A), profit≥0/yr YES 2008+ (worst +9.5%).
- TRADE RECORD: BLOTTER_RAWEW14_GEAR16.csv (this dir) — 67,242 records, columns per
  TRADE_RECORD_STANDARD.md (date, sleeve, instrument, side, price, price_source REAL/SYNTH,
  qty_notional, weight_from/to, cost_bps). Reconciliation: per-sleeve |qty| == charged turnover
  max|diff| 3.672e-09 (PASS); ledger PnL == candidate PnL max|diff| 0.000e+00 (IDENTICAL);
  REAL-priced 46,525/67,242 (69.2%); SYNTH = composite books (dualmom equity L/S, CFX4 FX cross,
  FF2 factor book — no single-instrument price series exists; honestly labeled).
- Harness cross-check: campaign blotter.py fresh run → 61,194 records, per-sleeve turnover
  reconciliation YES (existing champion, unchanged).
- corr(RAW-EW14@1.6x, V3 BAL@1.6x) = +0.8003; corr to committed uncapped V3 = +0.6912 — it is
  the same alpha family (sleeve files identical), honestly a leverage/rebalancing restructured
  champion, NOT a new alpha source; the point is honest accounting + better capital-real ann.
- Sleeves' mean pairwise corr +0.080 (max +0.870 = brwt family, min −0.202) — the 4 brwt
  variants are one family; a brwt-collapsed variant would likely land ~24-26%/SR ~3.6 (estimate,
  not verified).

## NEGATIVE/BLOCKED LEDGER (audit-specific)
- SR-scramble permutation nulls remain PROVABLY degenerate for positive-SR series (AUDIT_V2
  found; extended here: for a PASSIVE book np.roll preserves SR exactly → p=0.50 by
  construction); position-lag scramble applies to signal books only. The candidate has NO
  signal (EW of fixed slots), so its honesty gate is the exec-lag probe (passed, −0.000).
- Root-caused during build: (a) arithmetic-vs-geometric ann convention — first solver table
  mixed them (sim 118.7% vs law 80.0% at s=5.17); resolved by the exp() identity (−0.005pp);
  (b) budget-fill bug (k clamped to 1.0) which UNDERSTATED the achievable ann at first
  (Task-2 v1 table: 12.7-18.0% flat) — fixed; (c) K=4 v=8% solver cell 4.82 vs closed-form
  4.81 — was 120-seed MDD noise + discontinuous gate in brentq; resolved at 600 seeds.
- NOT modeled / honest caveats: intraday margin calls and financing-rate spikes (2008/2020
  gross>2 days), possible uptick/short-location constraints (covered sleeves: dualmom/QAxasts/
  carryv2 shorts already modeled at 0.5%/yr + dualmom HTB uplift), no securities-lending CREDIT
  on longs (conservative), FX cross book executed via 4 cross pairs (spot, no swap points —
  CFX4's own disclosure), candidate assumes daily reset at zero market impact beyond 6.4bps.
- Charter Task-2 row K=6 s=1.5: MDDmed −3.69 / MDDp95 −5.30 (one draft printed a garbled cell;
  the two edits above are the final corrected values).

## VERDICT
The 5-goal set (80%/5/7%/1.6x/profit≥0) is INFEASIBLE on current + hunted engines with honest
financing: at 1.6x + 4.5% margin the champion ceiling is 16.99–20.05%/yr; reaching 80% requires
~10 NEW engines of net SR ≥3.9 (each 2x the best engine ever found in 6 iterations), corr≈0.
Delivered: exact frontier table (Task 1), required-spec table (Task 2), infeasibility proof
(Task 3), end-to-end cost audit + RAW-EW14 lowest-leverage build (Task 4), and a candidate
champion RAW-EW13@1.6x at 28.89%/3.88/−4.25% with margin honestly charged and a reconciled
trade blotter (Task 5) — the new honest champion recommendation to the coordinator.

AUDIT_LEVFRONTIER DONE
