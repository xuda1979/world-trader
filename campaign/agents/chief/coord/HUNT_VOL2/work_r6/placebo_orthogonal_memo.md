# Methodology Memo: Placebo Instruments per Candidate Class
**HUNT_VOL2 Round 6(b) — docs-only input to the GATES_CONTRACT_V3 discussion. NO gate or
threshold change is proposed or made here.**

Author: HUNT_VOL2. Date: 2026-09-08. Charter: R6(b) of
`coord/HUNT_VOL2/CHARTER.md` (coordinator standup 2026-09-08 11:5x CST). Inputs are
published, sha-pinned measurements; every number below is quoted from an artifact on
disk, not re-derived.

---

## 1. The instrument GATES_CONTRACT_V2 §8h mandates today

> 8h. Vol/corr-matched placebo, 200 draws: a delta the placebo reproduces is arithmetic
> (VOL2: 2/6 pure artifact, frac_pos=1.000; SECTOR2-R3: A11 +0.141@15% 100% reproduced).

Design intent (as applied in R2-R5): build 200 null candidates that match the real
candidate's risk fingerprint (own-vol or frequency/episode-length matched), run the SAME
integration machinery, and look at the distribution of the null dSR. Reading rule the
fleet converged on: if the REAL delta sits inside the null distribution — or worse, is
reproduced by a large fraction of the nulls — the delta carries no timing/signal content;
it is an arithmetic consequence of how the candidate was attached to the champion.

Two distinct instruments have flown under this one clause:

- **R-style (HUNT_VOL2, R5)**: frequency+episode-length-matched RANDOM TRIMS of the
  champion (seed 0, 200 draws), same cost algebra. Null = "de-lever the champion on
  days with no information."
- **C-style (coordinator, R6 standup)**: 200 CIRCULAR SHIFTS of the candidate's return
  stream at fixed w, blend, measure. Null = "the candidate's own P&L, mistimed
  arbitrarily."

## 2. The documented failure mode: orthogonal positive-mean candidates

Coordinator measurement (STANDUP_LOG.md:6367, 11:4x standup): RES_BASIS
RB_hobr_crack_hyst_w63_z10_zo10 (standalone V2-PASS, DEAD_IDEAS row 137, corr_champ
+0.0219) at w=0.25 — **169/200 mistimed circular-shift draws reproduce the blend dSR
delta.**

Why the circular-shift instrument fires spuriously here — the mechanism, in three steps:

1. **Mistiming can't destroy what the blend never used.** The blend delta at corr≈0 has
   a variance-reduction term (~w²·σ² sleeve vs champion variance) that is shift-invariant,
   plus a mean term from injecting positive-EV P&L that mistiming ALSO preserves on
   average (same total return mass, just re-ordered). dSR depends on both.
2. **The dSR metric rewards variance reduction.** SR = mean/σ; adding an independent
   stream at any fixed w lowers total σ faster (quadratic in the added variance) than it
   adds mean (linear in w). That benefit accrues for a COIN-FLIP stream with positive
   mean exactly as for a skilled one.
3. **The champion bar is 0-neg-years.** An orthogonal positive-mean injection also
   repairs years the champion barely scraped: it mechanically pushes the blend toward
   0 neg yrs and shallower MDD. Those 8a/8b "improvements" reproduce under mistiming
   too.

So for an orthogonal standalone candidate the circular-shift placebo is not a
significance test of SIGNAL — it is a significance test of the ARITHMETIC of adding a
positive-mean stream, which passes for any such stream, signal or not. 169/200 is not
"the sleeve failed the placebo"; it is "the instrument was applied outside its design
domain." The coordinator's own reading ("mean-injection-dominated … not a refutation")
matches this.

The complementary failure already documented for the OTHER domain: my R5 PCR overlay
placebo (recommendation_r5.json): real gates with genuine timing content (real-vs-null
z +10.3 / +12.5 vs frequency+episode-matched random trims) were still correctly rejected
on dAnn<0 — and a CORRELATED candidate (corr 0.94-0.98) could NOT dodge the circular
shift, because with a correlated stream mistiming destroys exactly the overlap the delta
lives in. VOL2-R3's frac_pos=1.000 (2/6 pure artifact) and SECTOR2-R3's 100%-reproduced
A11 were real kills by this instrument. **The instrument is valid precisely when the
candidate's information is expressed through co-movement with the champion — i.e., the
overlays it was built for.**

## 3. Correct instrument per candidate class (V3 proposal, not a contract edit)

### Class A — CORRELATED overlay (corr_to_champion > ~0.5)
Keep §8h as-is. Circular-shift or matched-trim placebo at the overlay's own trigger
frequency. Domain of validity: the delta must live in WHEN the overlay is on, so
mistiming kills it if the delta is signal, preserves it if it is arithmetic.
Worked examples (published): VOL2-R3 2/6 frac_pos=1.000 (artifact, killed);
SECTOR2-R3 A11 100% reproduced (killed); HUNT_VOL2-R5 real-vs-null z +10.3/+12.5
(timing real, but separately rejected on 8c dAnn<0 — instrument and gate did their jobs).

### Class B — ORTHOGONAL standalone candidate (|corr| < ~0.5), tested as blend/14th sleeve
§8h-as-circular-shift is NOT VALID as a significance gate. Replace with EITHER:

- **B1. Level-matched NULL candidate**: 200 draws of a synthetic stream matched to the
  candidate's (mean, vol, skew, autocorr) but with NO timing content — block-bootstrap
  of the candidate's own residuals after removing calendar structure, or iid
  resampling within sign-preserving blocks. Blend each draw, collect dSR.
  Reading: the real candidate's dSR must sit in the RIGHT TAIL of its own null
  distribution (e.g. p95+). A coin with the right mean sits at the CENTER, so
  mean-injection is priced OUT of the statistic instead of saturating it.
- **B2. Subsample-split timing F-test**: split the candidate's active episodes into
  halves by time; a real signal's edge concentrates (its own SR vs its null SR gap is
  stable across halves), a pure mean-injection shows no such structure. Weaker; use as
  corroborator only, per §11's diagnostics-not-gates rule.

Recommendation: **B1 as the Class-B gate, B2 as corroborator.** Preserve the 200-draw
convention and the "reproduced-by-the-null ⇒ arithmetic" reading rule so fleet
tooling/muscle-memory still applies.

### Class C — w-scaled mean injection (the honest description of what adoption is)
When the question is "should we ADD this stream at w," the right null is not
"mistimed version of itself" but "any other positive-mean stream of matched vol" —
which is B1. The coordinator's 8g rung grid (w=0.05/0.10/0.15 all dAnn>0, dMDD>0,
0 neg yrs for RB_hobr) is already the right monotonicity evidence for this class;
B1 adds the significance layer the rung grid lacks.

### Cross-class safety rules (apply in all classes)
- The placebo can never UPGRADE a candidate (it only detects arithmetic). It must never
  be the sole DOWNgrade either when applied outside its domain — hence the class split.
- Any candidate straddling classes (corr near the 0.5 boundary, or an overlay whose
  covariate is itself a standalone stream) runs BOTH instruments; the stricter of the
  two readings applies.
- Era-consistency (the R4 TimesFM kill: single-era lifts are not repeatable sleeves)
  applies to the DELTA stream in every class, not just the standalone.

## 4. Cost of the change

Zero thresholds move. 8a-8g, 8i, 8j are untouched. Only the §8h placebo's construction
is redefined per class. Re-analysis exposure: the fleet's §8h history (VOL2-R3 2/6,
SECTOR2-R3 A11) is all Class A — verdicts unchanged under the V3 rule. The one
Class-B case in flight (RES_BASIS row 137) has NOT been adopted or rejected on the
placebo; its CAMP_COST R6 adoption study is the live evidence path, and B1 would be the
instrument for its BOOK-level placebo at the adopted w.

## 5. Provenance

- Coordinator measurement: STANDUP_LOG.md:6367-6376 ("169/200 mistimed draws reproduce
  the dSR delta … mean-injection-dominated, as expected for an orthogonal candidate
  (corr_champ +0.0219); the 8h instrument was designed for CORRELATED overlays").
- R5 placebo numbers: coord/HUNT_VOL2/work_r5/recommendation_r5.json
  (placebo_s8h_analogue: real_dSR -0.0299 vs null median -0.7655 z=12.5; -0.0032 vs
  -0.7621 z=10.31; frac_pos 0.0 both).
- §8h text + Class-A precedents: coord/GATES_CONTRACT_V2.md §8 (VOL2 frac_pos=1.000;
  SECTOR2-R3 A11 100% reproduced).
- Class-B candidate in flight: DEAD_IDEAS row 137 (RB_hobr_crack_hyst_w63_z10_zo10,
  sleeve sha da0285b9a7a5e6a2), chartered to CAMP_COST R6.
- Charter: coord/HUNT_VOL2/CHARTER.md R6(b) — "NO gate/threshold changes — this is a
  memo for the V3 contract discussion, not a contract edit."
