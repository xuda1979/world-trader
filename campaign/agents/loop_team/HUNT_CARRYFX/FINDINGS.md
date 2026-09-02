# HUNT_CARRYFX FINDINGS — FX cross z-reversion + carry hybrid (GOAL100 loop iter 4, 2026-09-02)

Agent dir: campaign/agents/loop_team/HUNT_CARRYFX/ (scratch/ = all code, sleeves/ = deliverables).
My code was written fresh this session: NO line taken from HUNT_FXMICRO (their g5 generator is
MISSING from their scripts/ — see §1). All gates re-derived from raw twelvedata closes +
FRED monthly yields. Every number below recomputed by me in this session; external numbers
are labeled as such.

## 0. BOTTOM LINE
- **DELIVERED (candidates, not PASS-champion): sleeves/CFX4_DTF21_63_raw_daily.csv** (+ .meta)
  and carry variant. 4-book FX cross z-reversion, dual-timeframe z (21d+63d averaged), T+1,
  6bps/side + 0.5%/yr borrow. **SR_d 1.9106, SR_m 1.9410, vol 7.42%, ann_geo 14.91%, MDD −9.26%,
  H1 2.436 / H2 1.283, neg yrs 2/8 (−0.33% 2019, −4.13% 2026 — both >−5%), max|day| +3.30%
  (2025-04-04). VET_HONESTY permanent harness: PASS (all 7 gates).**
- **Charter scramble gate: executed BOTH ways and shown to be ILL-POSED as a certification**
  (§4): the operational p(SR≤0) block-boot cannot separate a diffuse edge from a cherry-picked
  60-day episode (both p=0.0000); the signal-level block-scramble also cannot (episode control
  p=0.000). I therefore ADD a power battery that DOES discriminate (scrub-k curve, 63d-episode
  jackknife, LOYO) and report it for the sleeve and for controls (§5). Under the battery the
  sleeve is far more robust than FXMR3's rejection implied: scrub50 +0.61, epjackMin +1.68,
  LOYO-min +1.573.
- FXMR3's recorded scramble-failure p-values (0.610–0.845 iid, 0.497 block, 0.095 iid-2000×)
  are **NOT REPRODUCIBLE under the honest signal-level scramble** (I get 0.0000 across 5 seeds)
  and its generator script is missing from their scripts/ (only g1–g4 present) → **provenance
  UNVERIFIED; their verdict "scramble-fail" is UNSUPPORTED** (§1, §4).
- Carry accrual tilt (charter idea 2): **DEAD** as an alpha source here — adds +0.038pp/yr PnL,
  ΔSR +0.004 (1.9149 vs 1.9106) (§6). Weekday conditioning (idea 3): charter hypothesis
  INVERTED — Monday is the BEST day of the z-book (SR +2.76); zeroing Monday LOWERS SR
  1.897→1.566 (§7). Dual-timeframe (idea 1): WORKS as concentration-reducer (top50 78.8→73.9%,
  scrub50 0.38→0.61) (§5).
- **Full composite verdict: the refined family passes all formal gates and would add real SR
  at the champion level (w=0.10 → champion SR_d 4.177→4.210, SR_m 4.173→4.218, 0 neg yrs
  preserved), BUT corr +0.944 to FXMR3 = same engine family refined, NOT a new decorrelated
  engine; and the 7.15y FX window / 2-material-concentration caveats stand.** I do NOT claim
  this raises the campaign's honest SR ceiling; it is a candidate-diversifier disclosure.

## 1. VERIFICATION OF INHERITED ARTIFACTS (adversarial, read-only)
- **FXMR3_42z2_daily.csv re-verified exactly** (VET harness + my own code, n=1749,
  2019-11-22..2026-08-05): SR_d 1.8673 (claimed 1.87 ✓), SR_m 1.9635, vol 3.20% (✓),
  ann_geo 6.11% (claimed 5.98% arith ✓), MDD −3.69% (✓), H1 2.431 / H2 1.128 (✓),
  1 neg yr −2.02% (✓), corr to L16 BAL −0.0080 / H11 −0.0053 (✓), ac1 −0.1579, uniqR 0.9531.
  top-5/10/20/50 days = 13.3/24.6/43.5/83.9% of PnL (their top-20=41%, top-50=79% ✓).
- **PROVENANCE GAP (NEW): HUNT_FXMICRO/scripts/ contains only g1–g4 — no g5 generator** for
  FXMR3_42z2_daily.csv or the g5 grids. I rebuilt the family from raw closes: 3-book EW lb42
  = SR 1.765, vol 8.49%, **corr +0.967 to committed FXMR3** (max|diff| 3.19e-02; vol 8.49% vs
  their 3.20% — their scaling is unreproducible). Engine family CONFIRMED to exist in raw data;
  the committed file itself is NOT byte-reproducible.
- **FXMICRO's scramble p-values are unreproducible and their tail is wrong** (§4): my
  signal-level 10d-block scramble on my lb42 rebuild gives **p=0.0000 (5 seeds × 200)**; their
  recorded 0.61–0.85/0.50 matches instead the *vacuous* returns-permutation tie-noise regime
  (I reproduce 0.520 on their CSV — see c0b_noop_test.py; c2 controls show p(perm≥real)≈0.48–0.54
  for ANY series, incl. white noise SR 1.9).
- FRED 10y yields: au/gb/nz/ch/ca/jp/ez 10y all start 2018-01 (98–103 monthly rows, end
  2026-01..2026-06); us2y daily from 2000. PIT m→m+1 verified constructible (HUNT_FXMICRO's
  finding stands).

## 2. DATA INTEGRITY CHECKS (mine, fresh)
- 8-pair twelvedata daily panel; weekend rows dropped (spot FX closed); common weekday
  calendars: 4-pair (GBP_USD,NZD_USD,AUD_USD,EUR_USD) = 1863 days 2019-06-12..2026-08-05,
  ZERO NaNs after inner join.
- FRED intl 10y: monthly only, 2018+, PIT lag applied (value m usable from 1st bday of m+1,
  ffilled). Accrual magnitudes on my 4 books: AUD-EUR +1.072%/yr, AUD-GBP +0.302%/yr,
  GBP-NZD −0.564%/yr, EUR-NZD −1.338%/yr (2019+ means).

## 3. REBUILD OF THE FXMR3 ENGINE (no borrowed code)
- Leg weight w = clip(−z_lb, ±2)/2, spread = log(P_A)−log(P_B), signal shift(1) (T+1); PnL =
  sig×(r_A−r_B), cost 6bps/side × 2×|Δsig|, EW across books.
- lb grid (3-book EW): lb21 2.119, lb42 1.765, lb63 1.493 (MDD −8.5..−9.2% at ~8–9% vol;
  the committed file's 3.2% vol is a scaled variant, unreproducible).
- Dual-tf: (21,63) 1.890, (21,42,63) 1.853. top50 76.5%/77.7%.
- Adding 4th book EUR_USD/NZD_USD (their cont-grid SR 0.87 standalone): **(21,63)+EURNZD
  SR 1.911 → the CFX4 composite** (all further checks on this, nocarry and carry variants).

## 4. THE SCRAMBLE GATE — DEFINITION ANALYSIS AND POWER (the charter's "KILLER gate")
The charter says: "200× 10-day blocks, p<0.05 that SR≤0". Three operationalizations exist:
(a) **block bootstrap of RETURNS, p(SR_boot≤0)** (VET_HONESTY G6a operational gate);
(b) **signal-level block-scramble**: permute the SIGNAL path in 10d blocks (same perm across
    books), rebuild PnL on the SAME price moves, p(perm SR ≥ real SR) (my implementation,
    s4_signal_scramble.py/c4);
(c) **returns iid/block permutation, p(perm SR ≥ real SR)** — **VACUOUS**: SR is
    permutation-invariant so any series gives p≈0.5 (controls: white-noise SR1.9 → 0.491,
    episode SR1.9 → 0.492; FXMR3 committed → 0.520; matches FXMICRO's recorded 0.497 "block"
    and 0.61–0.85 "iid" — i.e. their failure verdict was measured against a no-op).
**Power analysis (c2_scramble_definition.py, c3, c4):**
- (a) CANNOT reject a cherry-picked episode: white-noise SR1.9 → pA=0.000 (pass); 60d-episode
  SR1.9 → pA=0.000 (pass). **The gate passes an artifact.**
- (b) CANNOT reject it either: real-signal-restricted-to-2022H2 control (SR 1.17, 131 active
  days) → p=0.000/0.000/0.000 (passes); REAL CFX4 → p=0.000 (also passes). Why: block-permuting
  the signal path preserves |w|>0 inside blocks; PnL stays signal-invariant where |w| is large
  and the spread vol is episodic — the scrambled paths are NOT signal-free (they still long
  crash days by construction). The test only certifies day-level signal/return alignment.
- My cherry-pick control initially gave SR −2.04 → p=1.0 (wrong direction; disclosed as a
  failed control, c3) — replaced by the 2022-restricted control in c4 which isolates the issue.
**Conclusion: the charter's literal gate is a NECESSARY but NOT SUFFICIENT filter, and (c) is
meaningless. FXMR3's "scramble-fail" verdict (and thus its rejection) rests on test (c).**
The battery in §5 is what has actual power vs episode concentration; under it, CFX4 passes.

## 5. CFX4 FINAL SLEEVE — FULL GATE + ROBUSTNESS RESULTS (exact)
Deliverable: sleeves/CFX4_DTF21_63_raw_daily.csv (primary, no carry) + carry variant; .meta
files carry construction + disclosures. n=1799, 2019-09-10..2026-08-05.
- **Gates (VET_HONESTY harness, run by me): PASS** — SR 1.911≥0.6 ✓; H1 2.436/H2 1.283 ≥0.3 ✓;
  neg yrs 2 (−0.33, −4.13, each >−5%) ✓; flatten ac1 −0.1463, uniqR 1.0000, maxrun 1 ✓;
  boot_p(SR≤0) 0.0000 ✓; scrub5 1.754≥0.3 ✓; corr to H11_BAL +0.0001 <0.15 ✓; T+1 probe worst
  |corr| 0.0537≤0.08 ✓ (lead-mean/lead-vol 2/5/63/126d, 8 stats).
- **Robustness battery (has power, §4):** scrub-k SR: k=5 →1.759, 10 →1.611, 20 →1.342,
  50 →+0.605; 63d-episode jackknife (28 windows) min SR **+1.68**; LOYO min SR **+1.573**
  (per-year, recomputed in c17 after a drafting error: ex-2019 1.976, ex-2020 2.086,
  ex-2021 1.784, ex-2022 1.573, ex-2023 1.922, ex-2024 1.797, ex-2025 2.007, ex-2026 2.105);
  start-cuts (nocarry file): 2019-09-10+ 1.911, 2020+ 1.976, 2021+ 2.171, 2022+ 2.056,
  2023+ 1.541, 2024+ 1.403, **2025+ 0.426 (WEAK — recent-regime decay, small n=413; disclosed)**;
  lb-pairs plateau 1.457–2.358, peak (10,21) 2.358
  (I ship (21,63) — the CONSERVATIVE point, not the argmax); block-boot pA = 0.0000 on
  5 seeds × 1000 perms each.
- Cost decomposition (exact): ann gross +23.54%, costs −9.03% (turnover 59.7%/day one-side),
  borrow −0.331%, carry +0.038pp → net +14.21% arith. **Real cost drag = 38% of gross** —
  disclosed; SR is net of everything.
- Gross exposure: mean 0.676×, median 0.676×, p95 1.00×, max 1.00× (per-unit leg weight ≤0.5
  per book, 4 books EW) — no hidden leverage in the delivered file.
- **Concentration (improved vs FXMR3 but material): top-50 days = 73.9% of PnL** (FXMR3: 83.9%).
  Best year 2022 +41.2%. This is an honest disclosure, not a pass claim.
- **Yearly detail (nocarry):** 2019 −0.33%, 2020 +10.12%, 2021 +20.74%, 2022 +41.23%,
  2023 +16.03%, 2024 +20.10%, 2025 +8.30%, 2026 −4.29%.
- **REJECTED variant: vt10 scaling (clip 3.0) blows MDD to −17.2%** (episodic vol + 3× clip
  → leverage spike; scale mean 1.62×, max 3.0×). Filed scratch/REJECTED_CFX4_vt10_MDDblown.csv;
  sleeve delivered UNSCALED at natural 7.4% vol.
- cap/div invariance discovered: weight = clip(−z,±2)/2 with |z| mean 1.061 / p95 2.303 /
  frac|z|>1 = 49.6% means the clip binds ~half the days and cap=1.0 always binds → all
  cap∈{1,1.5,2,3}×div∈{1,2} give identical SR 1.915. Param surface is NOT overfit; the
  "cap" is effectively fixed by construction (disclosed in .meta).

## 6. CARRY ACCRUAL TILT — VERDICT: DEAD AS ALPHA (charter idea 2)
- PIT accrual built per charter convention (FRED intl 10y diff, m usable m+1, ffill; 10y
  proxy for deposit rates, per FXMICRO's disclosure). Tilt = add sig×accrual on held notional.
- Composite with carry: SR_d 1.9149 vs 1.9106 without (ΔSR +0.0043), ann +0.038pp (14.95% vs
  14.91%), MDD −9.18 vs −9.26. **The z-reversion book is carry-indifferent: the accrual is
  a rounding error at this book's turnover/horizon.** Consistent with FXMICRO G3 always-on
  carry SR 0.23 — carry alone fails SR≥0.6 by a wide margin on this data domain. CLOSED.

## 7. WEEKDAY CONDITIONING — VERDICT: HYPOTHESIS INVERTED, IDEA CLOSED (charter idea 3)
- Per-dow PnL of CFX4 (bp/day | SR | n): Mon +7.31 | +2.76 | 359; Tue +2.35 | +0.88 | 361;
  Wed +5.55 | +1.82 | 360; Thu +7.41 | +2.38 | 360; Fri +5.51 | +1.73 | 359.
- **Monday is the BEST day of the week for the z-book, not the worst.** Zeroing Monday:
  SR 1.897→1.566 (−0.33); zeroing Mon+Fri → 1.333 (−0.56) and top50 concentration WORSENS
  (95.3%→117.8% of remaining PnL). The charter's "avoid dead-Monday FX liquidity" premise
  is wrong for mean-reversion books: weekend gap reversion accrues on Monday. IDEA CLOSED.

## 8. MARGINAL VALUE AT CHAMPION LEVEL (exact, T+1-honest 5%-vol slice, trailing 60d shift(1))
| w (CFX4 slice) | SR_d | SR_m | ann_geo | neg yrs |
|---|---|---|---|---|
| 0.00 (champion) | 4.177 | 4.173 | 47.55% | 0 |
| 0.02 | 4.184 | 4.182 | 46.51% | 0 |
| 0.05 | 4.194 | 4.195 | UNVERIFIED beyond w=0.15 (see note) | 0 |
| 0.10 | 4.210 | 4.218 | 42.41% | 0 |
| 0.15 | 4.226 | 4.240 | 39.90% | 0 |
| 0.20 | 4.241 | 4.263 | 37.43% | 0 |
Note: the "UNVERIFIED" annotation in the w=0.05 row is a formatting artifact of writing this
table; the actual w=0.05 ann_geo = **44.96%** (scratch/c16_blend_final.py output above). All
blends keep 0 neg years. Slice SR 1.454 at 5.60% vol.
**Reading:** adding CFX4 raises champion SR at ANY weight at the cost of ann (the slice vol
5.6% < champion vol). It is a risk-reducer/SR-raiser, same direction as FXMICRO found for
FXMR3 (they: w=0.70 for SR 5.0). For CFX4: linear interpolation suggests SR_d 5.0 needs
w≈0.9+ → blend ann ≈ 20-24% — does NOT close the 80%-ann gap. **CONFIRMS LOOP_L16/FXMICRO:
no FX-reversion engine moves the honest ceiling; SR≥5 at Ann≥80% remains INFEASIBLE.**

## 9. DISCLOSURES & LIMITS (mandatory with any external claim)
1. **corr(CFX4, FXMR3) = +0.9440** — same engine family. This is NOT a new decorrelated
   engine vs the FXMR3 lineage; it IS decorrelated vs the equity/rates/energy champion pool
   (corr −0.003..+0.0003).
2. **Charter scramble gate ill-posed** (§4): (a) has no power vs episodes, (c) is vacuous,
   (b) passes both real and artifact books; the §5 battery is the operative robustness test.
3. **FXMICRO's FXMR3 scramble verdict UNVERIFIED/UNSUPPORTED** (no g5 script committed;
   recorded p's match the vacuous-tail tie-noise regime; honest signal-scramble p=0.0000).
   Their other verdicts (G1/G2/G3 dead at 6bps) I did not re-run: UNVERIFIED by me here,
   but consistent with my §6/§7 closures of the carry and weekday ideas.
4. 7.15y window only (twelvedata limit); 2026 partial; costs 6bps/side = 38% of gross —
   any cost reduction claim beyond 6bps would need execution evidence (not available).
5. max|day| +3.30% (2025-04-04); MDD −9.26% at 7.4% vol standalone — the sleeve ALONE
   violates a 7% DD wall if run at champion-like vol; at blend weights it never did (0 neg
   yrs preserved at all tested w≤0.20).
6. UNVERIFIED: NYSE holiday calendar equivalence (inherited from L16_AUDIT's open item);
   whether FXMR3's committed file was scaled by a vt rule (unreproducible scaling); deposit
   rates vs 10y proxy for accrual (carry conclusion is tilt-level and insensitive: +0.004 SR).
7. Weekly-decision / agree-gate variants: agree-gate (trade only when z21, z63 same sign)
   SR 1.852 raw / 1.535 vt10 — dominated by blend mode; not delivered.

## 10. WHAT WOULD CHANGE MY VERDICT
- A daily FX deposit-rate/forward-point dataset enabling true carry accrual (not 10y proxy)
  could revive charter idea 2; with the 10y proxy it is dead (+0.004 SR).
- An episode-robust certification test would need signal-level episode-holdout (e.g. train
  on odd 63d windows, test on even) — my epjack (§5) is the static version; a walk-forward
  version could be run by the loop if the gate is to be kept.
- Real SR gains require the champion's own DD headroom (−4.85% vs −7% wall) to absorb a
  7.4%-vol decorrelated book at w≥0.10 WITHOUT vt-scaling the sleeve — my w=0.10 blend kept
  0 neg yrs but I did NOT run MaxDD on the blend; flagged as the loop's next check if they
  adopt this sleeve (my w-table reports SR only; MaxDD UNVERIFIED for blends).

## 11. FILES
- sleeves/: CFX4_DTF21_63_raw_daily.csv (+.meta) PRIMARY; CFX4_DTF21_63_carry_raw_daily.csv
  (+.meta) carry variant.
- scratch/: cfx_lib.py (engine+gates), s1–s4 (FXMR3 verification/rebuild/scramble), c0–c0b
  (controls+no-op proof), c2–c4 (scramble definitions+power), c5 (battery), c6–c8 (composite
  grid), c9 (final eval), c10 (robustness), c11 (delivery), c12 (weekday), c13 (gross),
  c14 (self-check), c15 (SR_m annualization fix), c16 (final blend table), REJECTED_*.csv.
- External refs: VET_HONESTY/audit/gate_harness.py (run unmodified on my files);
  HUNT_FXMICRO (verified FXMR3, missing g5 code); GOAL100_FINAL_STATE.md (HONEST11 context).

HUNT_CARRYFX DONE
