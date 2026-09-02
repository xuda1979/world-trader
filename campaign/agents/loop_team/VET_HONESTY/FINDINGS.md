# VET_HONESTY FINDINGS — GOAL100 loop parallel team (2026-09-02)

Role: adversarial gate-keeper. Ran every sibling candidate + committed champion claims
through an independent gate harness (`audit/gate_harness.py`, written fresh this session;
flatten/T+1 logic mirrors campaign/audit_harness.py, extended). All numbers below recomputed
by me, not copied. Sibling FINDINGS paths in the charter resolve under campaign/agents/
(LOOP_L16, LOOP_XGB1YFLAT), not campaign/ — read both.

## 1. Champion verification — ALL HEADLINES CONFIRMED exactly
| File | ann(geo) | SR_d | SR_m | MaxDD | worst-3y | neg yrs | worst yr | OOS17+ |
|---|---|---|---|---|---|---|---|---|
| HONEST11L16 BAL | **47.55%** | 4.177 | 4.173 | -4.85% | -4.85% | 0/19 | +15.28% | 43.9% |
| HONEST11 BAL | 47.9% | 4.216 | 4.187 | -4.85% | -- | 0/19 | +11.5% | 44.1% |
| HONEST11X804 BAL | 80.54% | 4.216 | 4.046 | -6.73% | -6.73% | 0/19 | +21.5% | 67.3% |
(OOS17+ = arithmetic ann on r≥2017-01-01; ann = geometric. "worst-3y" = worst MaxDD of any
4-year subwindow ≥3y+1d long, 2008-09..2026-07, first-day-of-year window starts.)

**Provenance (was a gap):** commit 63da4bd committed L16 CSVs with NO builder. I reconstructed
L16 from committed campaign/scripts/honest11_build.py with the disclosed recipe (per-sleeve vt
**0.08**, global SAFE 0.07/THR 0.04, AGGR 0.091/0.03; costs/borrow/throttle unchanged):
**max|diff| = 9.99e-17 over 4522 rows, all 3 files — REPRODUCED byte-for-byte.**
X804 = build(0.11, 0.04)/(0.14, 0.03): also reproduced (9.99e-17). HONEST11 --verify: IDENTICAL.
My rebuild stats match LOOP_L16's claims to rounding (ann 47.55 vs "47.6", SR_d 4.177 vs 4.18,
SR_m 4.173 vs 4.17, MDD -4.85, neg 0, worst yr +15.28 vs +15.3, OOS 43.9).

Flatten gate on champion + all 11 pool sleeves: **clean** (ac1 −0.074..+0.085, uniqR≥0.34,
max nonzero-constant-run = 1 day except a6r7 = 7d). The nonzero-flat vault scan found XGB1y
and ONLY XGB1y (210 runs, 4403/4684 days, ac1 0.951, Jan-2023 +21.1bps, Feb-2023 +35.8bps
constant — LOOP_XGB1YFLAT numbers CONFIRMED). The long zero-runs in 5 pool sleeves
(brwt15 up to 33d, a6r7 up to 461d, dualmom up to 436d, A5r2 112d, C5ngsum ~100d) are
**exact 0.0bps position-off periods** (seasonal off-season, gate-off, no-trend) — by design,
NOT flattening. My gate extension therefore counts only NONZERO constant runs.

## 2. MATERIAL FINDING — leverage "1.59x" is definition-dependent; capital-real all-in is ~3.0–3.8x
LOOP_L16 headline gate number (1.59x ≤ 1.6) is EW of per-sleeve |vt scale| ONLY — it EXCLUDES
the global vol-target scalar (mean 2.06x at g=0.070, 2.7x at 0.091). Capital-real all-in
(per-sleeve scale × global scale; the only definition that costs margin/financing):
- L16 SAFE 0.070: all-in mean **2.97x**, p95 6.09x, max 9.25x
- L16 AGGR 0.091: all-in mean **3.82x, p95 7.92x, max 12.02x** (BAL ≈ mean 3.4x, max ~10.6x)
- X804: EW-scale 1.919, global mean 2.542, **all-in mean 5.01x** (p95 10.03, max 15.18)
  — vs "~2.5x" disclosed in LOOP_SR_LEVERAGE table (= global scalar alone)
- X804 financing-charged @4.75% on (gross−1): ann 48.2%, SR_d 2.83, MDD −11.73% (MDD gate blown)
- L16 financing-charged @4.75%: ann 39.6% (vs 47.6), SR_d 3.59, MDD −5.30% (gates held)

**Definition arbitrage demonstrated:** raising ONLY the global TGT (0.11/0.143, per-sleeve vt
0.08) gives **ann 79.7%, SR_d 4.11, MDD −6.86%, 0 neg yrs with EW-scale mean 1.563** — i.e.
"Ann 80% at leverage ≤1.6" is *reachable* under LOOP_L16's own headline definition, contradicting
their infeasibility claim, which holds only under capital-real all-in (where ≤1.6x caps ann at
**~20%** at MDD ≤2.6%: TGT 0.033/0.0429 → ann 19.9%, all-in 1.617x; ≤1.6x → ann ≈17–20%).
Verdict: LOOP_L16's "leverage 1.59x" gate number is NOT capital-real; the feasibility verdict is
correct under capital-real accounting but the headline number mixes two definitions. Any
future "≤1.6x" gate must state the definition AND include the global scalar.

## 3. SIBLING CANDIDATE VETTING (chair list maintained)
Chair list — 9 HUNT_TAIL files + 1 HUNT_FUNDAMENTAL sleeve + 2 L16_AUDIT scratch (non-candidates):

| Candidate | Verdict | Exact numbers |
|---|---|---|
| HT_TAIL_{HL16,L16C,LEV16}_{SAFE,BAL,AGGR} ×9 | **REJECT** | ann 45.1–60.4% geo, SR_d 4.70–4.72, MDD −3.88..−6.72%, 0 neg yrs; **corr 0.9129–0.9152 to HONEST11** (gate <0.15). NOT new engines — re-vol-targeted champion variants. L16C ≡ LEV16 (md5 identical, 9 files = 6 distinct series); HL16 first rows byte-identical to L16C but later differ (family share build, differ in global TGT). Implied overlay (file−L16): SR 0.80, corr −0.28 to H11, mean +1.3bps/day — genuinely decorrelated but only ~3.2% ann contribution at 25.6bps/day vol; as standalone files they are 0.91-correlated rescalings and are rejected as "new decorrelated engine" claims. |
| HF_mom_cheap_daily.csv | **REJECT** | SR_d 0.90, ann 9.6% geo, MDD −24.5%, worst yr −6.3% (<−5% gate), forward-vol corr −0.134 (my T+1 probe), scramble proxies: boot p=0 but scrub5_SR 0.795 marginal; flat-clean (ac1 −0.106, uniqR 0.937, maxrunNZ 1). Fails ≥3 gates. |
| L16_AUDIT scratch repro_BAL.csv | note | max|diff| 5.07e-5 vs committed L16 BAL — near-reproduction (mine: 9.99e-17 exact). Their bal_gross_path mean 1.595/max 3.35 confirms they too measured EW-scale only (excluding global scalar). |
| HUNT_FXMICRO g1/g2/g3_grid.csv | note | parameter grids, not sleeves. Their self-reported corr −0.029 |corr|<0.15 gate pass, but no sleeve CSVs delivered (UNVERIFIED as sleeves). |
| HUNT_BASIS/CROSSREGIME/EQMOM/FF_STRATARB (sleeves/), HUNT_FUNDAMENTAL (sleeves/), HUNT_FXMICRO (sleeves/) | **NONE DELIVERED** | sleeves/ dirs empty at polls 15:57, 16:24, 16:30 CST. (HUNT_TAIL delivered 16:24; HUNT_FUNDAMENTAL/L16_AUDIT artifacts in scratch/, not sleeves/.) |

**0 of 10 candidate artifacts PASSED.** Under the honesty contract, the champion remains
HONEST11-L16 as committed — but see §2: its leverage gate number is definition-dependent.
Context: HUNT_BASIS/CROSSREGIME/EQMOM/STATS_REVIEW logs end in API 429 rate-limit errors
(no candidates ever produced); only HUNT_TAIL, HUNT_FUNDAMENTAL, L16_AUDIT, HUNT_FXMICRO
did real work. Anything those agents might have produced is UNVERIFIED (never existed).

## 4. Gate harness status
Permanent gate at campaign/agents/loop_team/VET_HONESTY/audit/gate_harness.py: T+1 forward-info
probe (lead-window mean/vol corr ≤0.08), flatten (ac1>0.5 / uniqR<0.08 / nonzero-const-run>10d),
SR≥0.6, halves≥0.3, negyrs, scramble (fixed mid-session: literal return-permutation is a no-op —
SR is permutation-invariant; replaced with 200x 10-day block-bootstrap p(SR≤0)≤0.05 + outlier
scrub5 SR≥0.3), |corr|<0.15 to HONEST11 BAL (committed). Costs NOT verifiable from return CSVs
alone — flagged UNVERIFIED-COST on every artifact; honest costs require the signal/turnover path
(reconstructable via honest11_build.build()). Gate rejects committed champion on CORR gate —
by design (candidates must be decorrelated NEW engines; the champion itself is not a candidate).

## 5. Honesty contract remainder (T+1, 6bps, no-flattening)
T+1: builder chain uses trailing 60d std shift(1), trailing 126d peak shift(1) — verified in
committed code (honest11_build.py lines 45-77, champion_build.py vt()). My forward-info probe on
the champion: worst |corr| 0.037 (lead 63d vol) — clean. 6bps/side on turnover charged in
builder (r_out = b − (tw+dsc)×6e-4); borrow fees charged; costs NOT independently reproducible
from CSVs alone (UNVERIFIED-COST by design of CSV-only candidates) — candidates claiming costs
must submit turnover metadata. No-flattening: §1 vault scan.

## 6. Bottom line for the loop
- Committed champion numbers: VERIFIED exactly (§1). Provenance gap: CLOSED (byte-repro 1e-16).
- Leverage ≤1.6 headline: **contested** — definition-dependent (§2); capital-real all-in is
  ~3.0–3.8x for L16, ~5.0x for X804; financing-charged X804 blows the 7% DD wall (−11.73%).
- Feasibility of {80%, ≤1.6x all-in} : CONFIRMED INFEASIBLE on current engines (§2, ann ~20% cap).
- Feasibility of {80%, EW-scale ≤1.6} : reachable (ann 79.7% @ EW 1.563) — loop must pick ONE
  leverage definition and disclose which; the current FINDINGS mix them.
- SR≥5: NOT met (4.13–4.22 honest, scale-invariant; HUNT_TAIL did not change this).
- Sibling candidates: 0/10 passed the permanent gate. Chair list current; will re-poll.
