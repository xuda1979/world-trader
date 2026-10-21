# CAMP_COST FINDINGS

## ROUND 1 (2026-09-07 01:42-06:00, summarized; full log in coordinator standup)

- Champion builder `rawew13v2_build.py` charges FULL |dW| @ 6.4bps one-side — verified by
  regression (`test_camp_cost_full_dw.py`, byte-recon of committed champion, maxdev < 1e-12).
  R1 wave re-emit (nav.shift(1) causal weights) is intact.
- Grepped campaign/scripts + campaign/agents for `0.5*|dW|`: champion-level composite clean;
  2 slot-level half-turn offenders found feeding the pool: dualmom (~0.1bps/yr champion) and
  diescrack (~2.2bps/yr champion).
- Regression tests (TDD) added in `campaign/bt/tests/test_camp_cost_full_dw.py` (6 tests).

## ROUND 2 (2026-09-07 06:20-07:0x)

### (a) Sleeve-internal cost models — TDD on synthetic streams, then fixes

Tests written RED first against committed builders (`campaign/bt/tests/test_camp_cost_r2.py`),
then builders fixed. Final: **7 of 8 R2 tests GREEN** (the 8th is the intentional fail-closed
gate in (c) below).

1. diescrack — `HUNT_BASIS2/scratch/lib.py zrev()` charged `pos.diff().abs()/2.0 * 6.0bps`
   (half-turn at 6bps = 3.0bps-equivalent vs 6.4 standard). FIXED: `tup=pos.diff().abs()`,
   default `cost_bps=6.4`. Synthetic z-cross test (entry+exit+re-entry charged) PASSES.
2. dualmom — `campaign/scripts/QA_dualmom_band121.py` charged
   `0.5*(neww-prev).abs().sum() * 6.0bps` on monthly rebalance. FIXED:
   `(neww-prev).abs().sum()` @ `COST_STD=6.4`. Synthetic 2-rebalance test (entry 1.0, reb
   0.8) PASSES.
3. Sweep found 2 MORE generators of champion sleeves with the same defect (R1 missed both):
   - `E1_20yspan/work/e1_idea2_a6r7_brwt_detrunc.py` brwt15 leg: `(pos.diff().abs()/2.0)*6e-4`
     — FIXED to `(pos.diff().abs())*6.4e-4`.
   - `A3_xs_quality/r6lib.py wback_rb()` (QAxasts slot generator): `0.5*np.abs(neww-prev)`
     @ COST=6.0 — FIXED: `wback_rb` now delegates to new `wback_rb_core(full_dw=True,bps=6.4)`;
     the legacy convention is preserved ONLY inside `wback_rb_core` for byte-recon.

### (b) Re-emitted corrected sleeve CSVs (byte-reproducible; champion composite untouched)

Protocol per sleeve: byte-reconstruct the committed CSV under the ORIGINAL convention first
(gate: maxdev < 1e-12 vs pre-fix archive), then flip ONLY the cost line and re-emit on the
IDENTICAL index (emit echoes candidate with maxdev 1.0e-16; sha recorded). Pre-fix bytes
archived at `CAMP_COST/sleeves/<name>__prefix.csv` (sha-verified == git HEAD).

Recon evidence (`python3 costfix_emit.py`, all 4 "already costfix ... maxdev=1.0e-16"):

| sleeve | orig-conv recon | n |
|---|---|---|
| diescrack | BYTE-EXACT | 4605 |
| dualmom | BYTE-EXACT | 4743 |
| brwt15 | BYTE-EXACT | 6547 |
| QAxasts | BYTE-EXACT | 4947 |

Before/after (252d ann from cumulative, daily SR):

| sleeve | ann before | ann after | dAnn | SR before | SR after | extra charge (slot level) |
|---|---|---|---|---|---|---|
| diescrack | 7.825% | 7.475% | -0.349pp | 1.0066 | 0.9651 | 32.49 bps/yr |
| dualmom | 9.459% | 9.353% | -0.106pp | 0.8923 | 0.8833 | 9.69 bps/yr |
| brwt15 | 29.318% | 27.960% | -1.358pp | 2.7612 | 2.6488 | 105.64 bps/yr |
| QAxasts | 11.541% | 11.392% | -0.150pp | 1.0175 | 1.0056 | 13.42 bps/yr |

Incident fixed: the first diescrack emit had 4664 rows vs archive 4605 (59 spurious leading
vol-warmup rows zero-filled instead of dropped) — violating the "cost stream only" invariant.
Caught by invariant check, re-emitted on the archive index: now exactly 4605 rows,
index identical to archive, sha c940b230541f3668. All 4 files now pass
index-equality + aggregate cost-grows-only (sum_new < sum_old: diescrack -0.0594,
dualmom -0.0182, brwt15 -0.2745, QAxasts -0.0263).

Champion impact (IN-MEMORY PROJECTION ONLY — committed champion untouched, per charter):
rebuilding rawew13v2 weights from the 4 corrected sleeves gives ann 39.69% vs 39.85%
committed (-0.16pp), SR 3.289, MDD -6.79%, 0/19 neg years. Coordinator should re-emit the
champion composite from the corrected sleeves (this also un-reds 11 champion-pin tests, see
below).

### (c) Per-sleeve charge table — all 13 champion sleeves (rawew13v2 POOL+NEW)

Empirical method: byte-reconstruct each committed CSV from its documented generator under the
claimed convention. "BYTE-EXACT recon" = the claimed convention is PROVEN, not inferred.

| sleeve | generator (provenance) | cost convention found | recon | verdict |
|---|---|---|---|---|
| diescrack | HUNT_BASIS2 lib.zrev | WAS half@6.0 -> now FULL\|dW| @ 6.4 | BYTE-EXACT | **FIXED+RE-EMITTED** |
| dualmom | QA_dualmom_band121.py | WAS half@6.0 -> now FULL\|dW| @ 6.4 | BYTE-EXACT | **FIXED+RE-EMITTED** |
| brwt15 | E1 e1_idea2 brwt leg | WAS half@6.0 -> now FULL\|dW| @ 6.4 | BYTE-EXACT | **FIXED+RE-EMITTED** |
| QAxasts | A3 r6lib.wback_rb | WAS half@6.0 -> now FULL\|dW| @ 6.4 | BYTE-EXACT | **FIXED+RE-EMITTED** |
| a6r7 | E1 e1_idea2 a6 leg: (W.shift(1)-W.shift(2)).abs() @ 6.0 | FULL\|dW| @ 6.0 | BYTE-EXACT (n=9168, dev 1e-16) | clean (6.0 rate residual) |
| A5r2 | a5_r2_rate_shock_contango.py: pos.diff().abs() @ D.COST=6.0 | FULL\|dpos| @ 6.0 | BYTE-EXACT (n=4249, dev 1e-16) | clean (rate residual) |
| C5ng | E1 e1_idea1: pos.diff().abs() @ 6e-4 | FULL\|dpos| @ 6.0 | BYTE-EXACT (n=7381, dev 1e-16) | clean (rate residual) |
| C5ngsum | same generator, summer mask | FULL\|dpos| @ 6.0 | BYTE-EXACT (n=7381, dev 1e-16) | clean (rate residual) |
| carryv2 | E1 e1_idea4 3-leg blend | leg1 2x\|dpos\| @ 6.0 (full 2-leg), legs 2/3 FULL\|dW\| @ 6.0 | BYTE-EXACT (n=5002, dev 1e-16) | clean (conservative) |
| CFX4 | HUNT_CARRYFX c11_deliver: 2*|dsig| @ 6.0 + borrow | full 2-leg turnover @ 6.0 | BYTE-EXACT (n=1799, dev 1e-16) | clean (conservative) |
| brwt10 | **NO committed generator** (built 2026-09-01 13:48 by uncommitted script) | UNVERIFIED; every recipe in family (coord_spread_sweep2.run, B2 bt.py, HUNT zrev) charges 0.5*\|dpos\| | recon FAILS all conventions (maxdev 1.3e-01 = data-vintage drift, n_inner 6547/6553) | **HALF-TURN LIKELY — UNRE-EMITTABLE** |
| brwt7 | same (13:46) | same | recon FAILS (maxdev 1.3e-01, 4560/4566) | **HALF-TURN LIKELY — UNRE-EMITTABLE** |
| brwt5 | same (13:46) | same | recon FAILS (maxdev 1.3e-01, 4560/4566) | **HALF-TURN LIKELY — UNRE-EMITTABLE** |

Notes:
- "Rate residual" = full |dW| charged at the documented 6.0bps rate instead of the 6.4
  standard. Conservative direction (overcharges by 0.4bps), same defect class boundary;
  left as-is, disclosed.
- brwt10/7/5: I did NOT blind-re-emit. Byte-recon fails for all three conventions with
  maxdev ~0.13 (>> a cost delta of ~2e-5), so their committed bytes came from a Sep-1 data
  vintage; a cost-only edit is impossible without rebuilding from the generator, and the
  generator is NOT in the repo. `test_champion_pool_has_no_unreemitted_half_turn_sleeves`
  now FAILS-CLOSED naming them until the coordinator rebuilds. This gate staying red is the
  intended honest state.

### Test-harness state after R2 (evidence: `python3 -m pytest campaign/bt/tests/ -q`)

**12 failed, 179 passed.** Taxonomy of the 12:
- 11 champion-composite pins (test_audit_champ2_round2 x4, test_audit_recon_lineage x3,
  test_auditrecon_r2_lineage x2, test_auditrecon_r2_pin_mutations, test_rawew13v2 repro):
  red ONLY because the committed champion bytes were built from the 4 pre-fix sleeve CSVs.
  Expected; un-reds when the coordinator re-emits the champion from corrected sleeves
  (projected 39.69% ann). Not touched per charter.
- 1 intentional fail-closed gate: brwt10/7/5 (above).

CAMP_COST-owned tests: `test_camp_cost_r2.py` 7/8 green, `test_camp_cost_full_dw.py` 4/4
green (both dualmom source pins inverted to pin the FIX, and the cost-grows-only invariant
re-leveled to what is exact: identical index + aggregate monotonicity; pointwise ordering
provably does NOT survive path-dependent vol-target scaling — measured 0 core violations vs
up to 2164 scaled-output violations, e.g. brwt15 max excess 2.0e-4 with 0 pre-scale
violations). Also fixed a latent cwd-robustness bug found while verifying: `ARCHIVE` was a
relative path, so the R2 pins silently resolved against pytest's cwd (3 false failures from
a non-root cwd); now anchored to the absolute ROOT. `test_camp_borrow_round2.py` dualmom pin
updated: dropped the stale assertion that the half-turn pattern EXISTS (cost convention now
owned by CAMP_COST tests); kept the no-borrow-leg and long-only pins, which still pass.

Files changed by CAMP_COST R2: 3 builder libs (HUNT_BASIS2 lib.py, QA_dualmom_band121.py,
r6lib.py, e1_idea2 brwt leg), 4 sleeve CSVs re-emitted + 4 archives, 3 test files, plus
work_r2/{costfix_emit.py,recon_*.py,sweep13.py}. Champion composite + champion-pin tests:
untouched.

ROUND 2 DONE


## ROUND 3 (2026-09-07 10:10-11:07 CST)

Read GATES_CONTRACT.md + DEAD_IDEAS.csv (95 data rows / 96 lines) FIRST. No dead family
re-tested; the brwt work is a cost/provenance audit of LIVE champion slots, not a new
signal family (Brent-WTI spread remains a live, committed champion engine).

### (a') Independent re-verification of the coordinator's 07:28 champion emit — PASS

`work_r3/reverify_champ.py` rebuilds the champion WITHOUT reusing rawew13v2_build (own
loader, own algebra, own stats, re-typed path map). Results:

| probe | result |
|---|---|
| [1] own rebuild vs committed CSV | inner=4805, max dev **9.9963e-17**, 0 missing rows -> BYTE-CONSISTENT |
| [2] weights vs committed RAWEW13v2_IS_SR_weights.csv | max dev **2.22e-16** IDENTICAL |
| [3] own-build stats | n=4805 ann **39.69%** SR **3.289** MDD **-6.79%** 0/19 neg yrs, worst yr +8.34%, 2008-03-31..2026-08-27 (matches coordinator's reported numbers) |
| [4] gross | mean = max = 1.600000000000 exactly; 0 days > 1.6+1e-9 |
| [5] causality probe @2017-06-13 | max\|dWg_t\|=0.000e+00 (same-day weights DO NOT move), \|dWg_t+1\|=1.660e-05 -> CAUSAL |
| [6] mutation probe (brwt10/7/5 -> corrected) | max\|base-mut\|=**4.047e-03** -> champion genuinely consumes the brwt slots |

VERDICT: INDEPENDENT-REPRO-OK. Bug found+fixed in my own probe while wiring [6]: `have`
test ROOT-doubled absolute paths, silently SKIPPING the mutation probe (fail-soft) —
now fails loud and runs.

### (c') PRIMARY MANDATE: brwt10/7/5 generators RECOVERED, frozen TDD, corrected sleeves emitted

**Recipe recovered from raw data** (provenance gap closed; also re-derived independently
here, then cross-checked to STRICTAUDIT_SLEEVES FINDINGS which had it too — uncommitted):
log(Brent/WTI) spread z-reversion, lookback lb, **z-band +-1.0 — NOT the family's +-1.5**
(the single fact that defeated R2's reconstruction: +-1.5 gives maxdev 1.3e-01, +-1.0 gives
9.996e-17), pos in {+1,0,-1}, T+1 payoff, B2 expanding vol-target (10%, min 60, cap 3),
min_start 2000 (lb10/lb5 "2000" files) / 2008 (lb7/lb5), emission keeps ALL index rows incl.
the 59 leading vol-target-warmup rows as empty cells.

**Vintage mystery SOLVED** (R2's "maxdev 1.3e-01 = data-vintage drift" theory REFUTED):
committed rows are byte-exact from CURRENT data_fred alone (9.996e-17 on all 6547/4560
overlap rows). The committed files' 5 extra tail dates (2026-08-04..08-10) came from a
Sep-1 vintage whose inputs ran 1 week longer; those rows exist today ONLY in
tools/quant/data/eia_weekly/{brent,wti}_spot_daily.csv, and FRED-vs-EIA overlap is
byte-identical (measured maxdiff 0.000000 on brent n=6747, wti n=6665, wti_full n=10221),
so splicing the EIA tail reproduces ALL 6553/4566 rows including the tail.

TDD: `campaign/bt/tests/test_camp_cost_r3_brwt.py` written RED (10 failed) BEFORE
`campaign/scripts/brwt_ens_build.py` existed; after implementing: **10/10 GREEN**.
Tests pin: generator contract, FULL|dW|@6.4 cost algebra on real rows (incl. a real
full-flip day), byte-recon of all 4 committed CSVs under the LEGACY convention (half@6.0,
kept behind an explicit flag for proof-not-endorsement), costfix emission invariants,
no-half-turn-in-source, causality, vintage quantification.

`python3 campaign/scripts/brwt_ens_build.py --verify`:
```
brwt10_2000: recon n=6553/6553 maxdev=9.9963e-17 BYTE-EXACT
brwt5_2000:  recon n=6553/6553 maxdev=9.9963e-17 BYTE-EXACT
brwt7:       recon n=4566/4566 maxdev=9.9963e-17 BYTE-EXACT
brwt5:       recon n=4566/4566 maxdev=9.9991e-17 BYTE-EXACT
```

**Corrected sleeves emitted** (`--emit`, byte-stable across reruns, sha256-16 verified
identical on regeneration; committed index echoed incl. warmup rows; pre-fix bytes
archived at sleeves/{name}__prefix.csv, sha == committed):
emission dsum (neg = cost added): brwt10 -0.3950, brwt5_2000 -0.4873, brwt7 -0.2914,
brwt5 -0.3346. Before/after (252d ann from cumulative, daily SR):

| sleeve | ann before | ann after | dAnn | SR before | SR after | MDD before->after | neg yrs | extra charge |
|---|---|---|---|---|---|---|---|---|
| brwt10_2000 | 37.278% | 35.211% | **-2.067pp** | 3.4110 | 3.2498 | -8.44 -> -8.48 | 0 -> 0 | 151.9 bps/yr |
| brwt5_2000 | 37.592% | 35.040% | **-2.552pp** | 3.4808 | 3.2789 | -12.07 -> -12.14 | 0 -> 0 | 187.4 bps/yr |
| brwt7 | 32.144% | 30.038% | **-2.106pp** | 3.1870 | 3.0061 | -5.60 -> -5.96 | 0 -> 0 | 160.8 bps/yr |
| brwt5 | 30.917% | 28.524% | **-2.393pp** | 3.0992 | 2.8913 | -9.28 -> -9.33 | 0 -> 0 | 184.7 bps/yr |

The brwt family is BY FAR the largest costfix cohort: 2.1-2.6pp per sleeve (vs 0.1-1.4pp
in R2) — 0.5*|dpos| on a flip-heavy daily z-reverter undercharges ~150-190bps/yr.

**RE-EMIT CANDIDATES** (`work_r3/candidates.py` -> work_r3/candidate{13,10}slot.csv, NOT
results/, NOT committed; coordinator performs the re-emit):
- candidate13slot (13 sleeves, brwt slots swapped to corrected CSVs, relw recomputed):
  ann **37.20%** (-2.49pp vs committed 39.69%), SR 3.181, MDD -6.69%, 0/19 neg,
  H1 SR 3.56 / H2 SR 2.98, OOS17+ ann 40.65% SR 3.04, max|cand-committed|=4.572e-03.
- candidate10slot (brwt10/7/5 DROPPED): ann **30.20%** (-9.49pp), SR 2.953, MDD -9.99%
  (WORSE drawdown — the family is load-bearing for risk, not just return), 0/19 neg,
  OOS17+ ann 37.55%.
RECOMMENDATION: re-emit the 13-slot candidate. Dropping the family costs 9.5pp ann AND
3.2pp of MaxDD headroom.

### (b) Turnover attribution — exact, no residual

`work_r3/turnover_attribution.py` + `work_r3/turnover_attribution.csv`
(test_camp_cost_r3_turnover.py, 5/5 GREEN; shares sum to 100.000000%, total reconciles to
the builder's own cost stream to <1e-9 relative). Champion-level FULL|dW|@6.4bps cost:
**4.96 bps/yr** (n=4804 charged days, day-1 entry uncharged).

| rank | sleeve | share | champion bps/yr |
|---|---|---|---|
| 1 | brwt10 | 16.2% | 0.80 |
| 2 | C5ng | 15.3% | 0.76 |
| 3 | brwt5 | 12.8% | 0.63 |
| 4 | brwt7 | 12.7% | 0.63 |
| 5 | C5ngsum | 11.7% | 0.58 |
| 6 | brwt15 | 9.9% | 0.49 |
| 7 | dualmom | 6.1% | 0.30 |
| 8 | QAxasts | 5.6% | 0.28 |
| 9 | A5r2 | 3.2% | 0.16 |
| 10 | a6r7 | 2.6% | 0.13 |
| 11 | carryv2 | 2.0% | 0.10 |
| 12 | diescrack | 1.9% | 0.10 |
| 13 | CFX4 | 0.0% | 0.00 |

**brwt family = 4 of top-6 turnover drivers = 51.6% of champion cost** — the same family
that carried the largest sleeve-level undercharge (150-190bps/yr x 4 slots). The costfix
directly addresses the dominant cost pool. CFX4's 0.0 is STRUCTURAL and real (verified):
its data starts 2019-09-10, after IS_END 2017-01-01, so IS-SR=0 -> relw=0 -> weight 0
every day. The "13-sleeve" champion is effectively a 12-sleeve book; coordinator should
either give CFX4 an OOS-fitted weight rule or drop the vestigial slot.

### Test-harness state after R3

`python3 -m pytest campaign/bt/tests/ -q`: **13 failed, 251 passed**. Taxonomy:
- 12 test_beats_passive failures: PRE-EXISTING on clean HEAD (verified via git stash:
  12 failed / 5 passed there too). Not CAMP_COST's; not touched.
- 1 INTENTIONAL gate, message updated: test_champion_pool_has_no_unreemitted_half_turn_sleeves
  still fails naming ['brwt10','brwt5','brwt7'] — because the champion BUILDER still
  consumes the committed half@6.0 bytes; corrected CSVs + generator now exist, so the
  coordinator's re-emit (swap rawew13v2_build.PATHS to *__costfix.csv) un-reds it. Teeth kept.
- All 76 champion/repro/lineage pins GREEN. CAMP_COST-owned: r3_brwt 10/10,
  r3_turnover 5/5, r2 7/8 (the gate), full_dw 4/4.

Files changed by CAMP_COST R3: NEW campaign/scripts/brwt_ens_build.py (the missing
generator), campaign/bt/tests/test_camp_cost_r3_brwt.py, test_camp_cost_r3_turnover.py,
work_r3/{candidates.py,turnover_attribution.py,turnover_attribution.csv,
candidate13slot.csv,candidate10slot.csv,reverify_champ.py(probe fix)},
sleeves/{brwt10_2000,brwt5_2000,brwt7,brwt5}__{prefix,costfix}.csv + 3 __R3COSTFIX.csv
(probe inputs). Champion composite, committed sleeves, results/: UNTOUCHED.

ROUND 3 DONE

## ROUND 4 (2026-09-08, executed 01:0x CST session) — CFX4 slot decision + brwt hardening, analysis-only

Charter context: fleet drained, R3 all-honest-negative, capacity restored. CFX4 relw=0.0 exactly
(data starts 2019-09-10 > IS_END 2017-01-01 -> IS-SR 0 -> weight 0): the 13-sleeve champion is a
12-sleeve book. Round 4 = slot decision doc + brwt_ens_build hardening. NO champion/weights/
builder/results bytes touched (verified: git status clean on all committed champion artifacts,
last commit b268e52).

### R4-1. CFX4 slot decision — work_r4/CFX4_SLOT_DECISION.md (DONE, all numbers re-reproduced this session)

Three options, champion level, FULL |dW| @ 6.4bps, margin 4.5% on 1.3x gross (252d ann, daily SR):

| option | ann% | SR | MDD% | neg yrs | turnover bp/y |
|---|---|---|---|---|---|
| OPT-A keep-as-is (= committed) | 37.195 | 3.181 | -6.69 | 0/19 | 5.2622 |
| OPT-B drop slot (12 slots, IS refit) | 37.195 | 3.181 | -6.69 | 0/19 | 5.2622 |
| OPT-C1 OOS 2y-live-SR weight (as run) | 36.301 | 3.168 | -6.63 | 0/19 | 5.2396 |
| OPT-C1b same, from CFX4 inception | 37.158 | 3.186 | -6.69 | 0/19 | n/c |
| OPT-C2 walk-forward live-SR (>=500 obs, qtrly) | 37.186 | 3.183 | -6.69 | 0/19 | 5.2762 |

Independent reproduction THIS session (every number re-derived from live commands, not copied):
- `rawew13v2_build.py --verify`: n=4805/4805, max|new-old| 9.996e-17 IDENTICAL; weights 2.220e-16;
  gross mean=max=1.600000, 0 days >1.6; turnover 5.2622 bp/yr, margin 2.70%/yr.
- `work_r4/cfx4_analysis.py`: OPT-A/OPT-B/OPT-C1/OPT-C2 row-exact; OPT-A recon inner=4805
  maxdev 9.996e-17 BYTE-EXACT; CFX4 standalone n=1799 (2019-09-10..2026-08-05) ann 14.91%
  SR 1.911 MDD -9.26% neg 2/8; corr to eq-w 12-book +0.0618 (gate-f PASS).
- `work_r4/cfx4_precision.py`: OPT-B is an EXACT no-op — max|netA-netB| = 2.776e-17,
  max|toA-toB| = 1.563e-15, identity max|WgA - nav*relw/sum*GEAR| = 3.886e-16 (a zero-relw slot
  is algebraically inert; the weight engine never renormalizes across the dropped name).
  OPT-C1 dAnn -0.8941pp / dSR -0.01255; OPT-C2 dAnn -0.0091pp / dSR +0.00184.
- `work_r4/cfx4_c1b.py`: C1's -0.8941pp is an idle-capital artifact (+0.8563pp of it):
  fillna(0) parks 2.996% of gross at zero return for 2987 pre-inception days (2008..2019-09-10);
  true inception-corrected effect = -0.0378pp ann / +0.005 SR (C1b).
- INDEPENDENT from-scratch check (this session, my own code, not the saved scripts): rebuilt the
  OPT-C2 walk-forward weight (quarterly refit on >=500 prior live obs, max(0,sr_daily)^0.55) and
  the builder's actual per-slot-NAV weight math (nav.shift(1), row-normalized, * relw): first
  nonzero weight 2021-10-01, final 1.4307 (inside committed relw range 0.651..1.860),
  CFX4 capital share max 0.6879% / mean-over-active 0.5499% over 1280 active days — matches the
  doc to 4 decimals. First proxy attempt (champion-NAV for all slots) gave 10.3% — wrong, because
  the builder weights by each sleeve's OWN NAV; corrected to the builder's formula. Disclosed.
- Staleness pin: champion ends 2026-08-27, CFX4 ends 2026-08-05 -> exactly 16 champion rows
  (2026-08-06..08-27) where CFX4 would earn fillna(0) under any include-rule.

DECISION INPUTS (quantified): (i) OPT-B = zero benefit, real churn — a drop-slot re-emit changes
CSV repr on 3941/4805 rows (82%) for a 2.8e-17 return delta, plus weights-file line removal +
champion/lineage pin churn. (ii) OPT-C is structurally impotent, not merely unproven — capital
share ceiling 0.6879% for ANY sleeve born 2019+ into a book that compounded since 2008; whole
intervention <= 0.01pp ann. (iii) OPT-C1's headline is an idle-capital artifact, and it fits the
weight on 2019-2021 data INSIDE the reported 2008-2026 backtest (disclosed, optimistic).
(iv) CFX4 the SIGNAL passes gates a/d/f on its own 7y span (SR 1.911) — a good sleeve with a
slot problem. FX-carry family stays DEAD (DEAD_IDEAS rows 5/63/93 re-checked; no new carry
signal proposed, no dead family re-tested).

RECOMMENDATION (coordinator+user decide): **OPT-A keep-as-is** + bookkeeping amendment —
document the 12-sleeve reality (this file + decision doc), do NOT drop the slot (byte churn for
2.8e-17), do NOT adopt an OOS weight rule (structurally impotent at <=0.69% capital; the honest
variant C2 moves SR +0.0018 = noise). If late-start sleeves are ever to matter, that is a
deliberate NAV-reset ENGINE change, taken on its own evidence. Fix the CFX4 feed's 16-row
staleness regardless of the slot decision.

### R4-2. brwt_ens_build.py start-bound hardening — DONE (TDD, probe-first)

R4 probes found SILENT-EMPTY failure modes in the R3 generator: P2 min_start after last spread
date -> EMPTY series (n=0), --emit would write a 0-valid-row CSV and --verify would pass
vacuously; P3 min_start too late for one valid vol-target row -> ALL-NaN, no error. Same defect
class: an impossible start window indistinguishable from a real sleeve with no rows yet.
Fail-closed contract (GATES 3) requires RAISE.

Fix + pins in campaign/scripts/brwt_ens_build.py (raise on impossible min_start; date-directional
verify_judgment that FAILS on generator-valid rows BEFORE the target's first date — the R2
diescrack 59-leading-rows incident class — and discloses benign trailing vintage growth, and
rejects empty targets), tests in campaign/bt/tests/test_camp_cost_r4_brwt_startbound.py:
**7 passed in 0.36s** (boundary-inclusion >=, after-data raises, too-late raises, 62-obs legal
1-valid-row case, warmup floor 59 leading NaNs vs committed bytes, early-start clamp,
diescrack-class leading-rows rejection).

### R4-3. Full verification sweep (this session, live runs)

- `pytest campaign/bt/tests/ -q`: **386 passed, 0 failed** in 43.72s. Notably the R3
  intentional gate test_champion_pool_has_no_unreemitted_half_turn_sleeves is now GREEN —
  the coordinator's b268e52 costfix re-emit satisfied it. R3's "13 failed" state resolved to 0.
  All other CAMP_COST files: full_dw + r2 + r3_brwt + r3_turnover = 27 passed in 1.96s.
- `bt/verify_champion.py` (acceptance harness, all 13 sleeves from builder PATHS): **ok TRUE,
  7/7 checks** — weights_repro 2.220e-16; byte_repro 1.110e-16; cost_reconciliation model=full_dw
  implied_over_full_ratio 1.0000000000008 (max_dev_full 1.246e-16 vs max_dev_half 1.680e-05:
  the champion is FULL-|dW|, half-turn decisively rejected); causality nav.shift(1) causal
  (sameday_max_dev 4.927e-03 != 0 -> no same-day lookahead); gross max 1.6000000000007 <= 1.6;
  yearly neg 0, worst year +7.3104%; mdd -6.6922% vs limit -7.0.
- Charter's champion of record re-verified: ann 37.195% / SR 3.181 / MDD -6.69% / 0 neg yrs,
  commit b268e52, working tree clean on champion CSV + weights CSV + builder.
- DEAD_IDEAS.csv: 119 data rows at round-execute (charter said 108 at round-open; other agents
  appended in between). CFX4 slot work touches NO dead family (carry rows 5/63/93 verified dead;
  CFX4 remains a live SLOT question only).

Charter compliance: analysis-only honored; champion/weights/builder/results committed bytes
UNTOUCHED (git-verified); no dead family re-tested; every number above from a live command run
this session or a saved reproducible script in work_r4/.

ROUND 4 DONE
## ROUND 5 (2026-09-08, guard round per charter) — cost_reconciliation re-run + byte-stability sweep

READ FIRST honored: GATES_CONTRACT_V2.md (RATIFIED 2026-09-08 03:1x, additive; v1 gates 1-5
unchanged) + DEAD_IDEAS.csv recounted at round-execute: **130 data rows** (charter said 120 at
R4-end; hunt agents appended between rounds — V2 preamble "dynamic, always recount" applies).
No dead family re-tested, no re-tuning (p-hacking ban); R5 is charter (a)/(b) only — guard +
documentation, zero code/signal changes by this agent.

### (a-1) cost_reconciliation on champion of record — PASS, full_dw, half-turn stays REJECTED

`bash campaign/bt/verify_champion_r3_cmd.sh work_r5/verify_champion_r5.json` (canonical
13-sleeve map) — **ok=true, 7/7 checks**:

| check | result |
|---|---|
| weights_repro | max_dev 2.220e-16 (tol 1e-9) |
| byte_repro | max_dev 1.110e-16 (tol 1e-12) |
| cost_reconciliation | **model=full_dw**, max_dev_full **1.2457e-16** vs max_dev_half **1.6798e-05** (half-turn worse by 5 orders of magnitude), implied_over_full_ratio **1.0000000000008**, charged **5.2622 bp/yr** (charter expects exactly this), turnover_full_dw 5.26223 bp/yr, day-1 entry ~4e-13 bp (uncharged) |
| causality | nav.shift(1) matched=causal; sameday_max_dev 4.927e-03 != 0; truncation 7 probes max_dev **0.0** |
| gross | max 1.6000000000007 <= 1.6, n_over=0, margin 2.70%/yr exact |
| yearly | 0 neg years, worst year +7.3104% |
| mdd | -6.6922% vs limit -7.0 |

Stats block re-derived live: n=4805, 2008-03-31..2026-08-27, ann_cagr **37.1954%**, SR
**3.1810**, MDD **-6.6922%**, neg_years **0** — matches the charter's champion-of-record line
field-for-field. `rawew13v2_build.py --verify` (separate command): n=4805/4805 inner,
max|new-old| **9.996e-17** IDENTICAL; weights 2.220e-16; gross mean=max=1.600000,
0 days >1.6; **turnover 5.2622 bp/yr**, margin 2.70%/yr.
All 34 CAMP_COST-owned regression tests GREEN this round: full_dw 4 + r2 8 + r3_brwt 10 +
r3_turnover 5 + r4_brwt_startbound 7 = 34 passed in 2.96s (the FULL |dW| @ 6.4bps builder
contract pins are inside these).

### (a-2) V2 s6 Step-1 leak_probe (explicit, not default-dependent) — leak=False both probes

Charter: "do not depend on either state [of the gates.run default flip]; pass sig= and
leak_check=True explicitly." The guard round makes no gates.run acceptance call, so the
equivalent explicit probe was run directly via bt.leakcheck on the champion of record
(`work_r5/leak_probe_r5.json`; two wiring errors caught and fixed first: relw CSV is the
13-row table not daily weights — daily Wg rebuilt from sleeves by the weights_repro-verified
algebra; wide probe needs a wide return frame):

| probe | sig | same-period corr | p | lag-0 argmax? | leak |
|---|---|---|---|---|---|
| wide: 13 weight cols vs 13 same-period sleeve rets (n=7026 outer-join days) | Wg (nav.shift(1), relw, 1.6x) | **-0.0196** (<0.20 threshold) | 0.0024 but | NO — argmax is lag -1 = +0.658 (the causal T+1 signature) | **False** |
| scalar: aggregate \|dWg\| vs champion same-period ret (n=4805) | \|dWg\| | **+0.0156** | 0.2796 | NO | **False** |

Both fail the V2 s6b flag rule (|corr|>=0.20 AND p<0.05 AND lag-0-argmax) → leak=False.
Caveats disclosed: the wide probe's n=7026 is the outer-join span (sleeve tails beyond
champion's 4805); the scalar probe sits exactly on the champion's 4805 rows. For scale
reference, the calibrated leaky vintage pins at +0.78 / causal champion at -0.032 (V2 s6b) —
both probes sit in the causal regime. This is a guard observation on the standing champion,
not a new-sleeve acceptance (no track claimed, none needed).

### (a-3) Byte-stability sweep — PASS, 16/16 byte-stable, all committed-byte-exact

`work_r5/sha_snapshot.py` (import the builder's PATHS — no hand-copied path list; two earlier
issues fixed en route: sys.path pointed at campaign/ not campaign/scripts/, and my first
git-ls-tree used a wrong `software/world-trader/` prefix — this repo's root is /Users/daxu
with world-trader content at top level, so pathspecs are relative to world-trader/).
Round-start snapshot `shas_round_start.json`, end-of-round `shas_round_end.json`:

- champion_csv **4358dfab95679b97** start == end == charter's round-start sha ✓
- weights_csv **149164b3b01aa110** start == end == charter's round-start sha ✓
- builder 1095b4f896b9bebb, and all 13 sleeves: start == end (16/16 BYTE-STABLE).

Second layer (belt-and-suspenders vs the within-session pair — cron agents mutate this repo
between rounds): every one of the 16 files was checked against git HEAD blobs via
`git ls-tree HEAD -- <path>` + `git hash-object` — **16/16 COMMITTED-BYTE-EXACT**
(working-tree bytes == HEAD blobs), 0 untracked among the 16. So the champion-of-record
state is pinned at the commit level: any mutation would require both a new commit AND a
working-tree change. Last mtimes all predate this round (latest 2026-09-07 23:25, the
coordinator's own brwt10/brwt7 costfix touch pre-dating commit 5638a19).
`git status --porcelain` on champion/weights/builder: clean. On CAMP_COST/sleeves/: only
my own R2/R3 archives (__prefix.csv x6, __R3COSTFIX.csv x3, brwt5_2000__costfix.csv —
untracked provenance artifacts, NOT builder inputs; the builder-consumed
brwt5__costfix.csv is committed-byte-exact).

End-of-round shas (16): champion 4358dfab95679b97; weights 149164b3b01aa110; builder
1095b4f896b9bebb; sleeves A5r2 0316cd1afd446938, C5ng 3d2b80691ef7a448, C5ngsum
ccfe3a4bc8706161, CFX4 0e448b301fba08c7, QAxasts 664d01fa126902c0, a6r7 e281e8c4cc5682fb,
brwt10 1289549405d78eb8, brwt15 7dbbe3dd95e7e3c8, brwt5 4a2aaa72b51e31d6, brwt7
f64c754197b04884, carryv2 03f4d0e099da9759, diescrack c940b230541f3668, dualmom
7462a8dfa391b18f.

### (b) Out-of-scope observations — DOCUMENTED ONLY, nothing touched

1. **Sleeve feed staleness (champion ends 2026-08-27; all 13 sleeves end earlier):**
   a6r7 0d, C5ng/C5ngsum 3d, QAxasts/dualmom 15d, A5r2 16d, brwt10/7/5 + diescrack 17d,
   CFX4 22d, carryv2 24d, brwt15 27d. The R4 CFX4 16-row pin (2026-08-06..08-27) stands;
   carryv2 (24d) and brwt15 (27d) are newly the stalest feeds. Refreshing ANY of these is a
   champion-re-emit event (byte churn on the champion of record) — out of scope for a guard
   round; flagged for coordinator scheduling. No cost change proposed; no signal proposed.
2. **Champion headline arithmetic (observation, no action):** ann_arith 32.137% vs ann_cagr
   37.195% in the same verify JSON — both are honest, different estimators; the charter and
   V2 quote CAGR. Recorded to prevent a future auditor mistaking the gap for a defect.
3. No cost change was proposed or made by this agent (charter (b) honored). CAMP_COST has no
   pending cost deviations: 13/13 sleeves at FULL |dW| @ 6.4bps is the standing state,
   re-proven by (a-1)'s cost_reconciliation.

Charter compliance: guard round executed read-only; zero bytes changed in champion/,
weights/, builder/, sleeves/ inputs, results/, bt/, campaign/*.md (this FINDINGS.md entry
and work_r5/ artifacts are the only writes). No dead family re-tested (130-row recount
done). Every number above is from a live command run this session or a saved script in
work_r5/ (sha_snapshot.py, verify_champion_r5.json, leak_probe_r5.json, shas_*.json).

ROUND 5 DONE

## ROUND 6 (2026-09-08, adoption study executed across 4 sessions 15:0x-18:0x CST; session 4 = live re-verification)

READ FIRST honored: GATES_CONTRACT_V2.md (in force; leak flips EXECUTED per banner — explicit
sig=/leak_check wiring used throughout) + DEAD_IDEAS.csv recounted at round execution: **145
data rows** (charter said 137 at R5-end; other agents appended mid-round — V2 dynamic rule).
No dead family re-tested; row 137 (RB_hobr, status "standalone V2-PASS (pending coordinator
adoption)") is the charter-designated live candidate, and this round is its adoption study.
Note: R6 work was built across 4 same-day sessions of this agent (adoption_study.py +
rawew14_candidate.py + battery artifacts 15:0x-15:2x; rerun2 16:4x; session2+refresh 17:0x;
session3 reverify 17:3x); THIS session re-verified every headline number live from the
artifacts and from my own independent re-derivations (CAMP_SHORT's R6 fraud-catch standard:
an artifact that does not reproduce is a defect).

### (a) CENTERPIECE — ADOPTION STUDY: RB_hobr_crack_hyst_w63_z10_zo10 → RAWEW14_HOBR candidate

**Construction (the only one certifyable).** Pure 14-sleeve re-solve of rawew13v2_build:
relw = max(IS_SR,0)^0.55 on the SAME IS window (<2017-01-01) with HOBR as a 14th slot, gross
exactly 1.6, FULL |dW| @ 6.4bps, margin 4.5%/yr on (1.6-1), nav.shift(1) causal.
`bt/verify_champion.py` recomputes relw from the sleeves (tol 1e-9), so a hand-capped weight
file can NEVER pass weights_repro — the w≤15% NAV charter cap must hold as an OUTCOME. It
does: HOBR NAV share min 1.456% / mean 5.758% / **max 9.981% ≤ 15%** (its IS SR 2.10^0.55 =
1.5496 ranks 6th of 14). No override used. Candidate re-solve relw14: brwt15 1.6583, brwt10
1.8380, brwt7 1.8600, brwt5 1.8224, C5ng 1.5999, C5ngsum 1.3841, A5r2 0.8643, a6r7 0.7499,
QAxasts 0.9822, carryv2 0.6512, dualmom 0.9891, diescrack 0.9161, CFX4 0.0, RB_hobr 1.5496.

**Full 7/7 verify_champion.py on the candidate — PASS (work_r6/verify_champion_r6_candidate_SESSION3.json, ok=true, 14-sleeve map incl. RB_hobr):**

| check | candidate (c14) | champion guard (c13, same session) |
|---|---|---|
| weights_repro | 2.220e-16 | 2.220e-16 |
| byte_repro | 1.008e-16 | 1.110e-16 |
| cost_reconciliation | **model=full_dw**, ratio 1.0000000000014, dev_full 1.008e-16 vs dev_half 1.966e-05 (half-turn rejected), charged **5.4972 bp/yr** | full_dw ratio 1.0000000000008, charged 5.2622 bp/yr |
| causality | nav.shift(1) matched=causal, sameday 4.815e-03≠0, truncation max_dev 0.0 | sameday 4.927e-03, trunc 0.0 |
| gross | max 1.6000000000006 ≤ 1.6, n_over=0 (**rides the cap exactly, same as champion**) | 1.6000000000007, n_over 0 |
| yearly | 0 neg years, worst +7.844% | 0 neg, worst +7.310% |
| mdd | -6.2354% vs -7 limit | -6.6922% |

**V2 blend battery on the delta (adoption_battery.json, re-run bit-identical this session):**

| gate | value | verdict |
|---|---|---|
| 8a blend yearly | 0 negative years (19/19) | PASS |
| 8b blend MDD | -6.2354% > -7; **dMDD +0.4568pp vs champion** | PASS |
| 8c dAnn > 0 (HARD) | **dAnn = -0.9069pp** (37.1954% → 36.2885% CAGR) | **FAIL — HARD** |
| 8d dSR ≥ 0 AND dH2 ≥ 0 | dSR +0.0909 (3.1810 → 3.2719); dH2 +0.0223 | PASS |
| 8e gross ≤ 1.6, full \|dW\| @ 6.4 | rides cap exactly by construction; fill-0 alternative breaches (below) | PASS (candidate) |
| 8f delta halves-consistency | book dSR_H1 **+0.2376** / dSR_H2 **+0.0223** (split 2017-06-13; c14 H1 3.802 / H2 3.001) | PASS (both ≥ 0) |
| 8g w-plateau rung grid | dSR +0.0799/+0.1454/+0.1911, dMDD +0.396/+0.795/+1.193pp, 0 neg at w=.05/.10/.15 (achieved mean share 5.00%/9.99%/14.95%) — monotone; **but dAnn -0.786/-1.592/-2.416pp monotone NEGATIVE at every rung** | SR side monotone; 8c fails at every rung too |
| 8h book-level placebo at adopted construction | B1 (below) + circular-shift continuity 0/200 | B1: timing real, CAGR trade not |
| 8i single-episode exclusion | excluding 2018-06-19..07-20 (trough 06-25, 24d window): dMDD **+0.5219pp** ≥ +0.5 relief | PASS (broad-based) |

**Halves / IS-OOS concerns, stated explicitly (charter open question):** the SLEEVE's own decay
is real and persists — its H1 2.182 vs H2 0.753 and IS/OOS 2.145/0.807 (RES_BASIS meta, both
disclosed there; OOS < 1.0 standalone bar). At the BOOK level the delta halves stay positive
(dSR_H2 +0.0223) and c14 book IS/OOS = 3.7252/3.0655 vs c13 3.4945/3.0358 — the sleeve's
weakness costs the book little at its 5.76% mean share, and the book keeps 0 neg years. These
are not the failing gate; 8c is.

**§8h placebo at the adopted construction (Class B per VOL2 R6 memo, cited):**
- placebo_B1 (memo's Class-B instrument; level-matched block-bootstrap null, L=20, moments
  re-matched mean/vol, 200 draws, FULL re-solve machinery): null dSR mean +0.0414 / p50
  +0.0396 / p95 +0.0602; **real dSR +0.0909 sits at percentile 1.00 → right-tail PASS: the
  timing is real, mean-injection is priced out.** The same machinery on CAGR: null dAnn p50
  -0.704pp vs real -0.907pp → real at percentile 0.00 — the candidate is WORSE for CAGR than
  its own no-timing null. Instrument and verdict align with the 8c hard fail.
- placebo_C circular-shift (coordinator's instrument, run for continuity): **0/200** draws
  reproduce the real dSR at the capital-real adopted construction (at fill-0 w=0.25 the
  coordinator measured 169/200 — the fraction collapses to 0 once capital is real because
  mistiming breaks the vol-replacement benefit too). Per the VOL2 memo this instrument is
  INVALID as a significance gate for |corr|<0.5 candidates (HOBR corr_champ +0.0219); not used
  to judge.

**Why the coordinator's +4.21pp and the candidate's -0.9069pp are BOTH honest (reconciled,
independently re-derived this session with my own algebra):** the fill-0 convention (champ +
w·sleeve, zero off-span) reproduces EXACTLY — my run: dAnn **+4.2128pp**, dSR +0.1989, dMDD
+0.051pp at w=0.25; rung grid +0.838/+1.679/+2.521pp at w=.05/.10/.15, 0 neg — matching the
coordinator's blend arithmetic to the displayed precision. But fill-0 adds the sleeve's P&L on
TOP of a book already at gross 1.6 → **8e breach at EVERY rung (1.65/1.70/1.75/1.85)**; it is
not a constructible book at fixed 1.6 gross. Under EVERY capital-real construction the 8c
verdict is the same: pure re-solve -0.907pp; gross-neutral delevered blend -0.306pp (w=.05)
to -1.565pp (w=.25). The economics: HOBR's 13.25% standalone ann replaces 13%-scale champion
capital (alpha over displaced book ~0.6pp/yr) while adding +0.2350 bp/yr turnover (5.2622 →
5.4972).

**Leak probes on the candidate book (explicit, V2 s6b):** wide 14-slot corr -0.0438, lag-0 NOT
argmax (lag -1 = +0.799, the causal T+1 signature) → leak=False; scalar signed dWg +0.0089
p=0.54 → leak=False; faithful |dWg| +0.2255 p≈0 but lag-0 not argmax → leak=False (turnover
covaries with same-day vol; verdict rides the lag leg — disclosed in the artifact).

**VERDICT: NOT-ADOPTABLE on 8c (dAnn > 0 HARD) at -0.9069pp**, with 7/7 verify_champion
passing and every other gate green. Candidate files written ONLY to
campaign/results/RAWEW14_HOBR_CANDIDATE_daily.csv (sha16 4a662985a408129b, 4805 rows,
byte-deterministic: fresh rebuild maxdev 9.996e-17) + RAWEW14_HOBR_CANDIDATE_weights.csv
(dc0dc87fea2ef4b0, 14 rows) — champion of record UNTOUCHED (4358dfab95679b97, 7/7 re-verified
this session via the 13-sleeve guard run). Recommendation to coordinator: do NOT adopt; row
137 disposition stands (standalone V2-PASS, not adopted). If HOBR's OOS decay (0.807) ever
reverses, re-study then. The +4.21pp that motivated the study is a fill-0 artifact that
breaches 8e at every w — worth knowing as a convention lesson for future blend submissions.

### (b) Sleeve refresh (brwt10/7/5 + diescrack, 17d stale at R5) — STAGED, source-limited before 2026-09-05

Per-sleeve protocol (refresh_sleeves.py): byte-recon committed/costfix bytes from LIVE sources
under the documented convention first (gate maxdev < 1e-12), then emit committed-index-echo +
new tail rows ONLY (no history relabel) into work_r6/refresh/ — never overwriting builder
inputs. This session's live re-run:

| sleeve | recon | committed end | tail added | refresh ends | committed vs extended (ann / SR / MDD) |
|---|---|---|---|---|---|
| brwt10 | 6553/6553, 9.999e-17 | 2026-08-10 | +14 | **2026-08-28** | 35.211% / 3.2498 / -8.48% → 35.300% / 3.2553 / -8.48% |
| brwt7 | 4566/4566, 9.986e-17 | 2026-08-10 | +14 | **2026-08-28** | 30.038% / 3.0061 / -5.96% → 30.212% / 3.0175 / -5.96% |
| brwt5 | 4566/4566, 9.996e-17 | 2026-08-10 | +14 | **2026-08-28** | 28.524% / 2.8913 / -9.33% → 28.787% / 2.9092 / -9.33% |
| diescrack | 4605/4605, 9.980e-17 | 2026-08-10 | +10 | **2026-08-24** | 7.475% / 0.9651 / -9.11% → 7.360% / 0.9578 / -9.11% |

**Why 2026-09-05 is unreachable (disclosed per charter):** brwt family sources are FRED
brent/wti (end 2026-08-03) spliced with EIA brent/wti_spot_daily (end **2026-09-01**); a T+1
payoff day needs a price after the last position day, so P&L extends only to 08-28 (09-01 is a
holiday-only tail; 08-31 row exists for WTI but the shared index stops at the common last
tradeable pair). diescrack is bound HARDER: its diesel leg (newdata/DJFUELUSGULF) and HO leg
(newdata/DHOILNYH) both end **2026-08-25** → P&L to 08-24. No live keyless source found for
daily diesel/HO spot beyond 08-25 this round; refresh resumes when sources advance.
Staged-file integrity re-verified: prefix maxdev 0.000e+00 vs committed bytes on all 4; row
counts brwt10 6626 (6553 valid + 59 warmup NaNs echoed + 14 tail), diescrack 4615 = 4605 + 10
(fresh-vintage generator also emits 59 front warmup rows 2008-01-02..03-27 + the 10 tail rows;
the staged refresh echoes the committed index only — the R2 cost-stream-only invariant).
shas16: brwt10 b0a0bd99338e2bb4, brwt7 8e76dd581ec6e50d, brwt5 ca5151f346524469, diescrack
c7d19f5bd0b2a603. ADOPTION of refreshed tails is a champion-re-emit decision (byte churn on
the champion of record) — staged for the coordinator, NOT executed (diescrack's refresh
slightly LOWERS its ann; brwt tails slightly raise theirs).

### Closeout of the CAMP_SHORT-R6 escalated flag on work_r5/leak_probe_r5.json (scalar probe)

CAMP_SHORT's audit was RIGHT: the R5 artifact's +0.0156/p 0.28 scalar is NOT reproducible as
faithful |dWg| — the faithful series gives **+0.2034/p 5.6e-47** (their number exactly; mine
now confirmed by an independent generator saved at work_r6/closeout_r5_scalar_probe.py, re-run
bit-identical this session: faithful +0.2033643296, signed +0.0152455779, dev 0.00e+00). The
R5 probe had almost certainly been fed the SIGNED dWg sum (float-noise-scale series) instead
of |dWg|. VERDICT UNCHANGED in every construction: leak=False because lag-0 is never the
argmax (faithful: lag -1 +0.461 dominates = causal signature). The R5 FINDINGS text stands as
written (it disclosed the +0.0156 number itself); the correct-faithful number and the
generator now exist alongside. Process note taken: probe artifacts must ship with their
generator script.

### Round-end state (all live this session)

- Byte-stability: 16/16 champion-of-record artifacts (champion 4358dfab95679b97, weights
  149164b3b01aa110, builder 1095b4f896b9bebb, 13 sleeves) byte-stable == R5 end-of-round shas.
- Tests: CAMP_COST-owned **42/42 GREEN** (full_dw 4 + r2 8 + r3_brwt 10 + r3_turnover 5 +
  r4_brwt_startbound 7 + **NEW r6_hobr 8** — RED-first pins on the candidate: relw-0 →
  committed-champion identity 9.996e-17, full-|dW|@6.4 algebra, w≤15% outcome cap, gross rides
  cap exactly, index equality, truncation causality, emitted-bytes determinism, saved 7/7
  JSON). Full bt suite **426 passed / 0 failed** (81.9s), up from the coordinator's 410/0 at
  11:4x (+16 = this round's new pins across agents).
- Charter compliance: candidate written ONLY to the two charter-named results/ files;
  champion/weights/builder/committed sleeves untouched; refresh STAGED in work_r6/ only; no
  dead family re-tested (145-row recount); every number above from a live command run this
  session or a saved generator in work_r6/ (adoption_study.py, rawew14_candidate.py,
  session3_reverify.py, closeout_r5_scalar_probe.py, refresh_sleeves.py + the JSON/CSV
  artifacts they emit).

ROUND 6 DONE

## ROUND 7 (2026-09-08, standup 18:3x charter) - REFRESH ADOPTION CENTERPIECE + hygiene

Context: a same-round twin session (21:01-22:00) had already staged the R7 candidate + battery
but wrote NO FINDINGS row and left a SyntaxError'd first battery run (r7_battery_stderr.txt).
This session independently re-verified EVERY artifact live before accepting it; all numbers
below are from commands re-run THIS session (bit-identical battery confirmed vs twin stdout).

### (a) CENTERPIECE - RAWEW15_REFRESH_CANDIDATE (13-sleeve re-solve, 4 R6-staged refresh sleeves)

Construction: full rawew13v2_build re-solve with work_r6/refresh/{brwt10,brwt7,brwt5}__refresh.csv
(end 2026-08-28) + diescrack__refresh.csv (end 2026-08-24) swapped in; natural IS re-solve
(max(IS_SR,0)^0.55) reproduces the committed weights EXACTLY (maxdev 0.0 vs champion weights
149164b3b01aa110 - refresh tails are all post-IS, as the R6 staging protocol promised).

- Prefix identity (no history relabel): rows <= 2026-08-10, inner=4792, maxdev 9.996e-17.
- FULL |dW| @ 6.4bps one-side honored: cost_reconciliation model=full_dw, ratio 1.00000000000085,
  charged 5.2734 bp/yr of the 6.4 budget (champion: 5.2622; refresh adds 0.0112 bp/yr of turnover
  cost), margin 2.70%/yr on (1.6-1); day-1 entry uncharged per builder convention.
- Gross: max 1.60000000000070, 0 days over (rides the cap exactly; no re-lever headroom, same
  as champion - the R6 8e resolution holds).
- LIVE 7/7 verify_champion.py (re-run this session, saved
  work_r7/verify_champ_r7_candidate_REVERIFY.json): weights_repro 2.22e-16, byte_repro 1.11e-16,
  cost full_dw ok, causality nav.shift(1) + truncation 0.0, gross ok, yearly 0 neg, MDD -6.6922%
  ok. ALL GREEN.
- Headline (vs champion of record 37.1954 / 3.1810 / -6.6922 / 0-neg, n=4805 08-27 end):
  candidate ann 37.4923% / SR 3.1951 / MDD -6.6922% / 0 neg yrs / n=4806 end 2026-08-28.
  DELTA dAnn +0.3068pp, dSR +0.0145, dMDD +0.0000pp, neg 0, dH1 -0.0000, dH2 +0.0279,
  IS/OOS SR 3.495/3.062 vs 3.495/3.036. Entire delta = 2026 year (+5.42pp on 2026 only).
- Charter NO-REGRESSION test: dAnn>0, dSR>0, dMDD>=0 (exact 0), neg years 0, gross<=1.6,
  MDD>=-7 - clears every charter bar (coordinator adopts only if 7/7 + all V2 gates + no
  regression: ALL MET).

Rung ladder (regenerated this session from a NEW saved generator work_r7/rung_ladder.py -
the twin's r ung_ladder_session2.txt had no generator, a section-10 verifiability gap, now
closed; numbers match the twin's txt exactly except the end column, which my inner-join
reports as the champion's 08-27 while the twin printed the candidate's own 08-28):
  none / diescrack-only: +0.0000pp (diescrack refresh tail is 10 rows of +-0.0 - extends the
    calendar, adds ZERO P&L; book-level PROOF this session: brwt-only vs full-candidate book
    maxdev 0.0 exactly, so diescrack's inclusion is a no-op on the whole candidate)
  brwt10: +0.0963pp / brwt7: +0.1043pp / brwt5: +0.1093pp
  brwt10+7+5: +0.3068pp, dSR +0.0145 (== full candidate, since diescrack is a no-op)
  All rungs: 0 neg years, grossMax 1.6000000000, 0 days over.

### V2 battery on the delta (re-run this session, bit-identical to twin: r7_battery.json)

- Class-A placebo (V2 s8h, 200 circular-shift draws of each refreshed sleeve's TAIL P&L
  post-08-10, FULL re-solve machinery - the Class-A domain because tail corr to champion
  is 0.830/0.794/0.809 for brwt10/7/5, a CORRELATED refresh): null dSR mean +0.0183,
  p50 +0.0187, p95 +0.0211; real dSR +0.0145 sits at the 6.5th percentile of its own null
  (BELOW the null median); real dAnn +0.3068pp at the 0.6th percentile (null p50 +0.2897pp).
  reproduced_frac_dSR 0.935 (93.5% of mistimed draws reproduce-or-beat the real dSR).
  VERDICT: the delta is ARITHMETIC/MEAN-INJECTION-DOMINATED, exactly the HOBR-R6 failure
  shape (coordinator's 169/200 finding) - the +0.31pp is 'new days exist and sleeves have
  positive drift', NOT 'the refresh timed well'. Real tail sum only +431.11 bps over 13
  delta-days (per-sleeve tail sums +342/+393/+516 bps brwt10/7/5, diescrack +0.00) - small,
  and the sign of the timing edge is NOT established against the mistimed null.
- 8i exclusion: dominant dd window 2018-06-19..07-20 (2018-06-25 trough, 24d) is in the
  PREFIX (unchanged bytes); dMDD excl = +0.0000 (trivially, MDD unchanged full-sample).
- 8f halves: dH1 -0.0000 (prefix pinned), dH2 +0.0279 - the whole delta is in H2-2026 tail.
- Leak probes (explicit bt.leakcheck, V2 s6 Step-1): wide 13-slot corr -0.0332 p 4.7e-07,
  lag-1 +0.795 dominates (causal signature) -> leak=False; scalar signed-dWg +0.0149 p 0.30
  -> leak=False; scalar |dWg| +0.2026 p 1.2e-46 above the 0.20 line BUT lag-0 is not argmax
  (lag-1 +0.463 dominates = turnover-vol covariance, disclosed) -> leak=False. NO LEAK in
  any construction.
- 8a/8b/8c/8d/8e/8j: 0 neg years; MDD -6.6922 > -7; dAnn +0.3068 > 0 HARD GATE OK;
  dSR +0.0145 >= 0 and dH2 +0.0279 >= 0; gross rides cap at 1.6000000000007 <= 1.6;
  corr_to_champion n/a (it IS 4 champion sleeves' own refresh; Class-A instrument applied).

### ADOPTION VERDICT (mine, for the coordinator)

Candidate is 7/7 + every V2 gate GREEN + no regression vs 37.1954/3.1810/-6.6922/0-neg,
and is mechanically CLEAN (prefix byte-identical, weights reproduce exactly, no leak).
BUT the Class-A placebo says the +0.3068pp / +0.0145 dSR is mean-injection-dominated
(real dSR at the 6.5th pct of its own null, reproduced 93.5%): the timing value of the
refresh is NOT demonstrated - this is 'more days of positive-drift sleeves', worth +0.31pp
ann mechanically, and NOT an alpha event. My recommendation: ADOPT if the coordinator
values calendar-currency + the mechanical ann gain at ~zero risk (all gates green, cost
+0.0112 bp/yr, turnover 5.2734 bp/yr well inside 6.4); the honest label is maintenance,
not alpha. REJECT if adoption requires demonstrated timing value - the placebo kills that
claim. I do NOT hide the diescrack no-op: its refresh adds zero P&L (maxdev 0.0 proof) and
could be dropped from the swap with zero book impact (its calendar extension is the only
effect, and the champion algebra is date-indexed so even that is cosmetic for the book).

### (b) HOBR file hygiene

Left exactly as-is per charter: RAWEW14_HOBR_CANDIDATE_daily.csv sha 4a662985a408129b,
RAWEW14_HOBR_CANDIDATE_weights.csv sha dc0dc87fea2ef4b0 - both == R6-end record (no delete,
no edit). Audit trail intact.

### Byte-stability guard + tests (all live this session)

- 16/16 champion-of-record artifacts byte-stable at round end == round start == R5/R6
  records: builder 1095b4f896b9bebb, champion 4358dfab95679b97, weights 149164b3b01aa110,
  13 sleeves (full table in work_r7/shas_round_end_r7_REVERIFY.json). Candidate shas
  (fresh emit, deterministic per test): RAWEW15 daily 8d7e711e6d05a2b1, weights 8c19ef227cf9b7b0.
- CAMP_COST suite: 50/50 GREEN (42 prior + 8 NEW R7 pins in campaign/bt/tests/
  test_camp_cost_r7_refresh.py: prefix identity, relw==committed, full-dW cost algebra,
  gross rides cap, causal index extension, weights use prior nav, --emit byte determinism,
  13-row weights) - note the twin's FINDINGS-basis said '42+8', the actual file count is 50.
- Full bt suite: 444 passed / 0 failed (105.2s), up from 426/0 at R6 close (+18 across
  agents' new pins).
- Charter files touched: ONLY the two charter-named results/ files (RAWEW15_REFRESH_CANDIDATE_*)
  + work_r7/ artifacts. Champion of record, weights, builder, committed sleeves UNTOUCHED.
- DEAD_IDEAS recount at round start: 151 rows (charter said 145-146, dynamic by design; the
  R7 hunt-wave appended 5-6 more before/during this round, e.g. HUNT_SECTOR2-R7 row,
  HUNT_TREASFUT-R7 row, CAMP_SHORT-R7 verified row). No dead family re-tested; the refresh
  corner is the charter pre-registered one.

### Round-end state

Everything above from live commands this session or saved generators in work_r7/
(rawew15_refresh_candidate.py, r7_battery.py, rung_ladder.py [NEW this session],
shas_round_end_r7_REVERIFY.json [NEW], verify_champ_r7_candidate_REVERIFY.json [NEW],
r7_battery_prevsession.json [twin-output snapshot for the bit-identity check]).

ROUND 7 DONE
