# AUDIT_H11FIX — adversarial audit of GOAL100_HONEST11FIX_* (2026-09-02)

Auditor: loop_team/AUDIT_H11FIX. Read-only on campaign; scratch (my own rebuild code,
no imports from the committed builder) in `scratch/`. All numbers below are MY
recomputation, not copied. Committed artifacts audited: commit 9004b67 (builder +
3 FIX CSVs; working-tree sha256 == committed: BAL 72475976…, SAFE 4eb1e699…,
AGGR 9e7e3c34…).

## 1. REPRODUCE — PASS (byte-exact, independent)
- `python3 campaign/scripts/honest11_build.py --verify` (HONEST11): max|new-old| =
  9.996e-17 BAL / 9.996e-17 SAFE / 9.996e-17 AGGR → IDENTICAL (<1e-12) for all three.
- `--verify-l16`: 9.986e-17 BAL / 9.996e-17 SAFE / 9.986e-17 AGGR → IDENTICAL.
- Independent rebuild of HONEST11FIX (fresh code from the 11 sleeve CSVs; recipe read
  from committed builder, then reimplemented — no import): overlap 4989/4989 rows on
  all three variants, ZERO index-only rows either side,
  **max|diff| = 9.986e-17 (SAFE), 9.986e-17 (BAL), 9.996e-17 (AGGR)** → byte-exact;
  nothing to localize. BAL == (SAFE+AGGR)/2 to 7.8e-17 (n=4989).
- The committed `--fixed` output is deterministic and reproducible from committed inputs.

## 2. CALENDAR FIX — VERIFIED superset; PASS with flags
- Row decomposition (vs committed-champion L16, n=4522, 2008-03-31..2026-07-31):
  FIX n=4989, added 467, removed 0 → **467 = 373 warmup (2006-10-02..2008-03-28) +
  94 recoveries (75 in-window 2008-03-31..2026-07-31 + 19 tail 2026-08-03..2026-08-27)**
  — matches the charter's 4616+94 arithmetic exactly (4989−373=4616).
- Weekends in FIX rows: 0. US-federal holidays in FIX rows: 0.
- Non-federal weekdays missing in-window: 0 → FIX now contains EVERY non-federal
  weekday 2008-03-31..2026-07-31 (inner-join loss fully cleared).
- KEPT rows that are NYSE-closed equity sessions (futures open, only futures sleeves
  print): **20 Good Fridays** (2007..2026; 1-sleeve rows on 2022/2024/2025 GF — e.g.
  2024-03-29 blend = 100% carryv2, −9.1bp) and **5 other full NYSE closures**:
  2007-01-02 (+36.6bp), 2012-10-29 (+4.2bp), 2012-10-30 (+7.7bp),
  **2018-12-05 (+253.5bp**: brwt5 +169.8, brwt7 +167.6, brwt10 +164.3, C5ng +103.2,
  carryv2 +54.5bp), 2025-01-09 (+4.5bp). These are NOT federal holidays; keeping them
  is defensible (real futures P&L, reweight-to-present convention) but note the blend
  is non-homogeneous there (1–2 sleeves, not 11).
- Composition of the 75 in-window recoveries: 18 Good Friday + 4 mourning/Sandy +
  53 other (mostly UK/equity-open-but-few-sleeve days; categorized programmatically,
  not individually inspected). Recovered-day P&L: mean +3.10bp/day vs +13.00bp/day all
  rows — still adverse-selected (keeping them is conservative).
- Pre-existing convention, unchanged: sn() lumps federal-holiday-closed sleeves' P&L —
  18 Columbus + 16 Veterans days (federal, NYSE OPEN, sleeves DID print: e.g.
  2008-10-13 brwt10 +162bp, QAxasts +114bp) are smeared into the next kept day
  (timing shift up to ~3 days, P&L not lost). Same convention as all prior champions.

## 3. COST CHARGE — charged exactly as specified; ~0.9%/yr CONFIRMED; but formula UNDERCHARGES the true position-path turnover
- Charged overlay-rebalance drag (6e-4 × turnover), 2008+ means:
  SAFE 0.872%/yr, **BAL 0.939%/yr**, AGGR 1.006%/yr (BAL turnover mean 620.9bp/d
  one-side; p95 day 1.46bp). The "~0.9%/yr" claim is CONFIRMED (BAL 0.94%).
- Row-level identity: r_(no-reb) − r_(reb) = turnover×6e-4 EXACTLY — max residual
  1.379e-17 over all 4989 rows. The charge is applied precisely as documented.
- T+1 / no-lookahead: turnover_t is built from diffs of scale_t = tgt/vol(t−1 window)
  (champion_build.vt verified: rolling(60).std().shift(1)·√252, cap 8; throttle uses
  eq.rolling(126).max().shift(1)); scale changes are knowable at t. corr(r_t, reb_t) =
  +0.027 vs corr(r_t, reb_{t+1}) = +0.369 (vol-clustering, not leakage). PASS.
- **NEW FINDING (mild): the formula `Σᵢ|d scaleᵢ|/N + |d global|` is not the actual
  position-path turnover.** True overlay turnover = Σᵢ|d(scaleᵢ × global × throttle)|/N;
  because both legs are vol-driven and the notional is global-scaled (mean ~2.6x), the
  formula undercharges by 1.66x (SAFE: 957.4 vs 576.4bp/d) and 2.08x (AGGR: 1386.3 vs
  665.3bp/d) — exact drag 1.448%/yr (SAFE), 2.096%/yr (AGGR), 2008+. Caveat: part of the
  gap overlaps the already-charged cap-weight turnover term; as an upper-bound
  counterfactual, charging the exact position path on BAL gives **ann 43.69%, SR_d
  3.936, MDD −5.74%, 0/19 neg yrs, worst +13.69%** (extra drag ~0.83%/yr). Verdict
  unchanged under either convention, but the fix is directionally still a (smaller)
  undercharge.

## 4. LEVERAGE (capital-real, all-in = meanᵢ|scaleᵢ|·global) — ≤1.6 does NOT hold
FIX construction, per-sleeve vt 0.08 + global 0.07 (SAFE)/0.091 (AGGR), gross on
scaled notional:
- SAFE: 2008+ mean **2.975x**, median 2.723x, p95 6.115x, max 9.247x; 85.1% of days >1.6x
- BAL: 2008+ mean **3.421x**, median 3.132x, p95 7.032x, max 10.634x; 92.0% of days >1.6x
- AGGR: 2008+ mean **3.868x**, median 3.540x, p95 7.949x, max 12.021x; 94.1% of days >1.6x
- Full-span BAL mean **3.277x** (reconciles the commit's "gross mean 3.25x" — reproduced
  to rounding; 2008+ is 3.42x).
- BAL yearly means ALL exceed 1.6x (min 1.92x in 2024, max 5.15x in 2023; e.g. 2022
  5.06x, 2023 5.15x, 2021 4.40x, 2012 4.44x).
- **Statement: "leverage ≤1.6" does NOT hold under capital-real accounting in ANY year,
  on ANY variant.** The commit message discloses this honestly (3.25x) — no inflation
  found on this item; the old L16 "1.59x" headline number is gone from the FIX claims.

## 5. GOAL CHECK (FIX committed full span 2006-10-02..2026-08-27, n=4989)
| Variant | ann(geo) | SR_d | SR_m | MaxDD | neg yrs 2008+ | neg full |
|---|---|---|---|---|---|---|
| SAFE | 38.28% | 3.994 | 3.996 | −5.82% | 0/19 (worst +14.51% 2011) | 1/21 (2006 −1.08%) |
| BALANCED | 44.82% | 4.019 | 3.934 | −5.60% | 0/19 (worst +15.12%) | 1/21 (2006 −1.21%) |
| AGGRESSIVE | 51.65% | 4.028 | 3.879 | −6.47% | 0/19 (worst +15.72% 2011) | 1/21 (2006 −1.34%) |
- ann ≥80%: **FAIL** — 44.82% BAL (SAFE 38.28, AGGR 51.65).
- SR ≥5 (daily AND monthly): **FAIL** — SR_d 4.019 / SR_m 3.934 (BAL).
- MaxDD ≤7%: **PASS** — −5.60% BAL; worst 756d-subwindow −5.60% (2021-03-24..2024-04-01);
  AGGR −6.47% also inside the wall.
- profit ≥0 every year 2008+: **PASS** — 0/19, worst +15.12% (BAL). BUT **full-span has
  1 negative year: 2006 stub −1.21% (n=61 days)** — decomposition: 60/61 days have zero
  signal (per-sleeve 60d vol warmup), the only signal day 2006-12-29 is −86.3bp, plus
  warmup cost drag; 2006 sum −1.082% of which reb-cost −0.205%. Any unscoped "0 neg
  years" claim on FIX is FALSE; it holds only for 2008+ (or 2008-01-01 onward: verified
  0/19 on 2008-01-01..2026-07-31, matching the commit's "comparable span" scoping).
- OOS17+: commit says 51.8% — reproduces ONLY as **geometric 51.78%**; arithmetic is
  **42.27%**. Prior campaign OOS figures (STRICTTRADE 55.9%, L16 43.9%) were arithmetic.
  **Convention switch inflates the headline by ~9.5pp** — flagged as new (minor) inflation.

## 6. ADVERSARIAL SWEEPS — all pass; no new fragility
- Flatten gate on FIX BAL: ac1 −0.0630, uniqR 1.0000 (4989/4989 distinct), 0 exact
  zeros → clean.
- Worst single days: +14.40% (2020-09-01, +24.5σ — the brwt gate-on day, unchanged from
  L16) and −3.68% (2008-09-19, −6.3σ); daily σ 0.588%. Single-day tail remains
  asymmetric and understated by DD metrics (inherited L16_AUDIT caveat (c)).
- T+1 extra-lag probe (all sleeve returns shifted +1 extra day, full rebuild): BAL
  ann 44.82%, SR_d 4.012, SR_m 3.952, MDD −5.08%, 0/19 — robust, no execution-timing
  artifact.
- Block-bootstrap SR (200×, 10-day blocks): full span bootstrap mean SR 4.026 (p5 3.663),
  p(SR≤0) = 0.0000; 2008+ mean 4.049 (p5 3.628), p(SR≤0) = 0.0000. SR is real.
- Leave-one-sleeve-out (11 rebuilds): NO single sleeve removal produces any negative
  year (0/19 everywhere). Largest degradations: −a6r7 ann 42.28% SR_d 3.807 MDD −5.96%;
  −carryv2 SR_m 3.729 MDD −6.08%; −C5ng SR_d 3.815 (worst yr falls to +8.08%). No
  single-sleeve dependency that kills the profit gate.
- NEW — tail homogeneity: 837/4989 rows (16.8%) have <11 sleeves; the 19-day extension
  runs down to 1 sleeve (2026-08-25..27 are a6r7-only, e.g. +190.5bp on 08-25). The
  committed headline span includes these thin rows; the 2026 tail contributed +3.92%
  over 19 days (mean 20.7bp/d vs 13.0bp/d full-sample). Comparable-window (…2026-07-31)
  ann 45.74% vs full 44.82% — thin tail + 2006 stub net ≈ −0.9pp effect.

## 7. VERDICT
Like-for-like (common window 2008-03-31..2026-07-31): FIX 45.57% / SR_d 4.020 / SR_m
4.082 / MDD −5.60% vs L16 47.55% / 4.177 / 4.173 / −4.85% — the two fixes give BACK
~2.0pp ann and ~0.75pp DD headroom (consistent with L16_AUDIT's predicted −0.5pp/−1.3pp
and +0.7pp DD).

Audit gates:
| Gate | Verdict |
|---|---|
| 1. Byte reproduction (H11, L16, FIX) | PASS (≤1.0e-16, independent) |
| 2. Calendar rows-kept, no fake days | PASS (0 weekends/0 federal; 20 GF + 5 NYSE-closure rows are real futures P&L; flags §2) |
| 3. Reb cost charged as claimed, T+1-safe | PASS (identity 1.4e-17; ~0.94%/yr) with caveat: formula undercharges exact path 1.66–2.08x |
| 4. Leverage disclosure | PASS as disclosure (3.28x full-span mean); ≤1.6 FAILS under capital-real (as disclosed) |
| 5. Goals | ann≥80 FAIL, SR≥5 FAIL (d & m), DD≤7 PASS (−5.60%), profit≥0 2008+ PASS (0/19) — full-span 1/21 neg (2006 −1.21%) |
| 6. Sweeps (flatten, T+1, bootstrap, LOO, tail) | PASS (no kill found) |

DISCREPANCIES found (all minor, none flips a gate):
1. OOS17+ "51.8%" is geometric; campaign convention was arithmetic → honest 42.27%.
   Convention switch = new mild inflation.
2. Full-span "0 neg years" is false unless scoped 2008+ (2006 stub −1.21% is warmup
   cost drag, 60/61 zero-signal days).
3. Reb-cost formula undercharges exact position-path turnover by ~1.7–2.1x (~0.8%/yr
   on BAL); exact-charge counterfactual: 43.69% ann, SR 3.936, MDD −5.74%, still 0/19.
4. Thin-sleeve rows (16.8% of rows; 19-day a6r7-only tail, 1–2-sleeve Good Fridays)
   are in the headline span — non-homogeneous blend, flagged.
5. Commit's "gross mean 3.25x" is full-span BAL; on the 2008+ window it is 3.42x —
   state the window when quoting.
UNVERIFIED (inherited, unchanged): economics of the 11 sleeve CSVs themselves; C5ng
print timing; NYSE-closure list asserted from known events (no exchange-holiday file
checked); the 53 "other" recovered days categorized but not individually inspected.

Is FIX MORE honest than committed L16? **YES, net.** It removes the inner-join
adverse-selection (recovered days are below-average P&L, so keeping them is
conservative) and charges the previously-free ~0.94%/yr overlay cost; headline
correctly drops to 44.8% ann with DD −5.60% and 0/19 neg (2008+). New inflation is
confined to the OOS convention switch (+9.5pp on that one stat) and the unscoped
neg-years claim; the reb formula still undercharges slightly. All five goal-gates
remain unmet exactly as before (ann and SR fail; the 5-goal set stays infeasible on
these engines at disclosed ~3.3x capital-real gross).

AUDIT_H11FIX DONE
