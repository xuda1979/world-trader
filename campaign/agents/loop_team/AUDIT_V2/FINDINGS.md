# AUDIT_V2 — adversarial audit of GOAL100_HONEST13V2_* champion (2026-09-02, iter 5)

Auditor: loop_team/AUDIT_V2. Read-only on campaign; all rebuild code is my own (fresh, in
`scratch/`, NO import from honest11_build.py / champion_build.py / prior agents' code; I read
those sources as documentation only). Committed artifacts audited: commit 05c62cf (+ 6c266e6
FINAL_STATE). Working tree == committed blobs for all three CSVs (sha256: BAL 0d6ac01f…,
SAFE b892af2e…, AGGR cbb79b94…; verified via git cat-file).

## 0. VERDICT SUMMARY
**NOT ADMISSIBLE AS COMMITTED — PROVENANCE HOLE.** The V2 builder was NEVER committed (the
charter predicted this; confirmed: commit 05c62cf contains ONLY the 3 CSVs + agent findings;
campaign/scripts/honest11_build.py has no V2 path). I attempted independent reproduction from
the 13 sleeve CSVs under ~30 recipe variants (slot conventions, calendar conventions, cost
conventions, per-sleeve vt targets): **best max|diff| = 1.59e-2 (SAFE) / 1.82e-2 (BAL); ZERO
of 4989 common rows match to <1e-12; only 2.9% match to <1e-6.** The exact recipe — including
which slot accounting produced the observed effective new-sleeve weights (~2.3–2.5% per unit,
matching NEITHER 0.10/12.2=0.82% NOR the charter's stated 4.55% capital share) — is not
recoverable from committed artifacts. Per charter item 1, that is a PROVENANCE HOLE.
Sub-verdicts: headline stats REPRODUCE under stated conventions (§3); new-sleeve gate claims
and the scramble-degeneracy claim VERIFY (§1–2); leverage claim ~HONEST (§4); dilution claim
~CONFIRMED (§5); sweeps clean (§6); no inflation found in the quoted numbers (§7) — but the
champion is not reproducible and must be rebuilt through a committed, frozen builder before
it can be the campaign champion.

## 1. REPRODUCE — **FAIL (provenance hole, charter item 1)**
- `git show 05c62cf --stat`: V2 commit adds 3 CSVs + agent dirs; **no builder**.
  `grep HONEST13V2 campaign/scripts/` → nothing. honest11_build.py --verify covers 11-pool only.
- My independent 11-pool FIX rebuild (fresh code, smear calendar, REBAL formula+KEEP) DOES
  reproduce committed FIX BAL to 9.986e-17 (4989/4989) — the 11-pool recipe is provenance-clean.
- V2 vs FIX: V2 has 5086 rows (2006-10-02..2026-08-27); all 97 V2-only rows are **federal
  holidays** (Columbus/Veterans/MLK/etc.). On those rows V2 prints ~cost-only values (mean
  −5.16bp, std 1.21bp, max +1.8bp; SAFE==AGGR to ~1.7e-4) instead of FIX's smeared 11-pool
  chunk → **V2 changed the 11-pool calendar/cost convention vs the committed FIX builder**
  (fed-row chunks are NOT carried; V2 also prints ~−5bp costs there). No committed code
  implements this.
- Regression of (V2−FIX) on the two new sleeves over 4989 common rows:
  V2 ≈ 0.9991·FIX + 0.02335·diescrack + 0.02472·CFX4 + c, residual rms 8.0e-4, max 2.48e-2.
  Per-unit weights 0.0233/0.0247 are inconsistent with every candidate slot convention:
  0.10/12.2=0.00820 (charter "total slots 12.2"), 0.10/11.2=0.00893, 1/22=0.0455, 0.0455
  (charter "new-sleeve capital share 4.55% each" ⇔ 0.10/2.2 — note the charter's own two
  numbers, 12.2 slots and 4.55%, are mutually inconsistent). Slopes also drift by year
  (FIX-slope 1.036 in 2008 → 0.931 in 2026), i.e. the difference is not a pure add-on.
- Recipe grid I ran (all FAIL ≥1.6e-2): smear vs rows-kept calendars; new sleeves as separate
  slots vs inside the 13-sleeve vt pool; slot ∈ {0.0082, 0.00893, 0.0455, 0.05, 1/22};
  reb-cost formula vs exact position-path; per-sleeve vt 0.08 vs 0.10; skipna vs zero mean.
  Best configs: SAFE 1.588e-2 (rows-kept, PS 0.08/0.10), BAL 1.805e-2, AGGR 2.047e-2.
- Distribution of |V2−FIX| (common rows): median 5.0e-5, p90 4.9e-4, p99 2.7e-3, max 2.48e-2;
  corr(V2, FIX) = 0.9906. V2 total return 2006+ is 142,859% vs FIX 152,672% on common rows —
  V2 is LOWER (fed-row chunk drop + extra cost rows ≈ −0.08%/yr), i.e. the unreproducible part
  is *conservative*, not inflated — but it is undisclosed and uncommitted.

## 2. NEW SLEEVES — gates VERIFY (charter item 2)
### diescrack_L40Z20 (sha e8a083df…, matches FINDINGS claim) — my raw rebuild from FRED
DJFUELUSGULF×42 / wti_full (own code) matches committed file max|diff| 2.2e-5 (733/4605 rows
>1e-12; worst 2.2bp, 2020-03-30 — floating-log/interpolation noise; SR 1.0128 vs 1.0066).
On the committed file I recompute: **SR_d 1.0066 (claim 1.01 ✓), SR_m 0.9346, vol 7.77%,
ann_geo 7.82%, MDD −9.07%, neg 1/19 (2013 −0.50%) ✓, H1 0.926 / H2 1.118 ✓, ac1 −0.0567,
uniqR 0.1594 ✓, corr to FIX BAL +0.0516 (n=4575) ✓ (claim 0.05/0.0516)**.
### CFX4 (sha 0e448b30…) — my raw rebuild from twelvedata closes (own code, per-book
aggregation) matches committed max|diff| 4.4e-3 (SR 1.8912 vs 1.9106 — small residual,
likely data refresh since delivery; gate conclusions unaffected). On the committed file:
**SR_d 1.9106 ✓ (claim 1.9106), SR_m 1.9410 ✓, vol 7.42% ✓, ann_geo 14.91% ✓, MDD −9.26% ✓,
neg 2/8 (−0.33% 2019, −4.13% 2026) ✓, H1 2.436 / H2 1.283 ✓, ac1 −0.1463, uniqR 1.0000 ✓,
max|day| +2.70% (2024-11-07; meta claims +3.30% 2025-04-04 — that is the max in MY rebuild,
minor discrepancy), corr to FIX BAL −0.0019 (claim +0.0001; both ≈0, PASS <0.15)**.
- **Concentration disclosure VERIFIED: top-5/10/20/50 days = 11.3/20.9/36.6/73.9% of PnL —
  claim "top-50d = 74%" ✓ exact.** Gross exposure mean |sig| 0.217, p95 0.668, max 0.997 ✓.
- Robustness battery reproduced on my rebuild: scrub-k 5/10/20/50 → 1.737/1.592/1.328/0.600
  (claim 1.754/1.611/1.342/+0.605 ✓), epjack63-min 1.642 (claim 1.68 ≈), LOYO-min 1.537
  (claim 1.573 ≈), start-cut 2025+ 0.392 (claim 0.426 ≈, still WEAK — disclosed), block-boot
  p(SR≤0)=0.0000 (3 seeds × 1000) ✓.

## 3. SCRAMBLE GATE — **DEGENERACY CONFIRMED (charter item 3)**
Literal return-permutation null (200×): diescrack iid p=1.000 / 10d-block p=0.555; CFX4 iid
p=0.535 / 10d-block p=0.530; committed net files p=0.545/0.485. A SR-based permutation null
cannot fail ANY positive-SR series (SR is permutation-invariant) → **the as-written charter
gate is VACUOUS. Confirmed.**
Discriminating position-lag circular scramble (shift position path vs price-move path, 200–300×,
lags 21..T−21): **diescrack p=0.0000; CFX4 p=0.0000 (per-book net rebuild, same-lag, per-book
and lags≥63 variants all 0.0000).** Both sleeves' edges are signal-alignment, not curvature.
Caution recorded: my first composite-level (aggregated) implementation of the CFX4 pos-lag test
gave p≈0.23–0.37 — the test must be applied per-book on the net engine (correct implementation),
not on pre-aggregated composites. The charter gate text should read "200× position-lag
scramble p<0.05" (as both iter4 hunt agents recommended).

## 4. V2 HEADLINES — REPRODUCE EXACTLY under stated conventions (charter item 4)
Committed GOAL100_HONEST13V2_BALANCED_daily.csv, n=5086, 2006-10-02..2026-08-27:
| window | ann(geo) | SR_d | SR_m | MaxDD | neg yrs | OOS17 arith |
|---|---|---|---|---|---|---|
| full span | 43.33% | 3.904 | 3.848 | −4.96% | 1/21 (2006 stub −1.38%) | 40.82% |
| 2008-03-31..2026-07-31 | 43.95% | 3.906 | 4.000 | −4.96% | **0/19, worst +13.92%** | 41.01% |
| 2008-03-31..end | **43.83%** | 3.905 | **3.993** | −4.96% | 0/19 | 40.82% |
→ commit's "ann 43.8% SR_d 3.91 SR_m 3.99 MaxDD −4.96% 0/19 OOS17arith 40.8%" all reproduce
(ann quoted as geo on the 2008-03-31..end slice; full-span file keeps the 2006 stub, −1.38%,
1 negative year — the "0 neg" claim is ONLY true scoped 2008+, same caveat AUDIT_H11FIX raised
on FIX; FINAL_STATE's "worst +13.9%" ✓ matches +13.92%).
- **BAL == (SAFE+AGGR)/2: YES — same 5086-row index, max|diff| 1.0e-16.**
- Worst-3y claim: worst within-756d-window MaxDD = −4.96% (both SAFE and BAL; AGGR −5.42%);
  MaxDD episode is 2011-01-03→2011-02-14 (recovered 2011-05-06). Worst calendar-3y window is
  +100.3% (2011-13) — i.e. "worst-3y −4.96%" means worst rolling-DD, not worst 3y return
  (which is hugely positive). Honest as a DD statement; misreadable as return.
- MaxDD ≤7 PASS with 2.04pp headroom; 0 negative trailing-252d windows (worst +11.66%);
  worst single day +14.57% (2020-09-01, brwt gate day — inherited tail caveat).

## 5. LEVERAGE (charter item 5) — claim ~HONEST (on my reconstruction)
gross_t = Σᵢ slotᵢ·|scaleᵢ|·global·throttle/(11+2·slot), slot=0.10, my rows-kept recon:
- BAL 2008+: **mean 3.449x, p95 7.177x, max 10.615x**; full span mean 3.399x.
  Commit claim "mean 3.45x / p95 7.18x / max 10.75x" → **mean and p95 reproduce to 0.2%**;
  max differs 10.62 vs 10.75 (1.2% — recon noise given §1).
- SAFE 2008+ mean 3.021x, AGGR 3.876x. Days >2× disclosed mean (>6.90x): **278/4804 (5.8%)**
  on BAL recon. Days >1.6x: 89.5%. Yearly means 2008+ ALL >1.6x: min 2.09x (2026), max
  5.16x (2023); 2022 5.13x, 2021 4.23x. → "leverage ≤1.6" FAILS every year, as disclosed.

## 6. NEW-SLEEVE DILUTION CHECK (charter item 6) — ~CONFIRMED, no cherry-pick
Slot sweep 0..0.5 on my recon (BAL): SR_d 4.002 (0) → 4.014 (0.10) → 4.024 (0.40) → 4.020
(0.50) — nearly flat; SR_m monotone DECREASING: 3.993 (0) → 3.989 (0.10) → 3.927 (0.50);
MaxDD −4.92% (0) → −4.89% (0.10) → −5.87% (0.50). **No weight lifts SR_d ≥5 (max 4.02) and
no weight achieves ann ≥80% at DD ≤7 (max ann 44.9%).** "0.10 ≈ diversification max before
dilution" is defensible: SR_m already decreasing at 0.10, SR_d surface is flat (0.10 is not
the argmax but within noise of it — no cherry-pick found). New sleeves contribute +5.8%
cumulative over 2006+ at effective weights (~0.85% of 2008+ simple-return sum) — modest,
honestly disclosed as slot-weight extension.

## 7. ADVERSARIAL SWEEPS (charter item 7) — all clean
- **Flatten gate** (committed BAL): ac1 −0.0641, uniqR 0.9998, 0 exact-zero rows, max
  constant-run 0. No flattening artifact.
- **T+1 extra-lag probe** (my recon, full rebuild): +1 day lag on the 2 new sleeves → SR_d
  4.034 (from 4.014) — no timing artifact; +1 day on ALL 13 → SR_d 4.009, MDD −4.91% — robust.
- **Block-bootstrap SR CI** (2000×, 10d blocks, committed BAL): 2008+ mean 3.914, **90% CI
  [3.501, 4.330]**, p(SR≤0)=0.0000; full span mean 3.924 [3.543, 4.307]. SR real; CI excludes 5.
- **Leave-one-out (13 rebuilds, my recon)**: ALL keep 0/19 neg (2008+). Largest swings:
  −C5ng worst-year +6.12% (from +14.24%), ann −1.8pp, MDD −6.02%; −dualmom MDD −6.08%;
  −a6r7 ann 44.16%. Removing either NEW sleeve changes little (−CFX4 SR_d 4.053, −diescrack
  4.050 vs 4.058 baseline) — the two additions are +0.005–0.02 SR, i.e. cosmetic at slot 0.10,
  consistent with the dilution math (§6) and honestly framed.
- Tail composition: 2026 tail beyond 07-31 (19 rows) = +1.24%; last 5 rows print only 1–3/11
  pool sleeves (thin-sleeve rows inherited from FIX — flagged by AUDIT_H11FIX, unchanged).
- corr(diescrack, CFX4) = 0.0117 — genuinely distinct engines.

## 8. VERDICT (charter item 8)
**V2 is NOT admissible as the committed champion in its current form.** Not because any number
is inflated — every quoted headline, gate claim, concentration disclosure, leverage stat and
the degenerate-scramble claim VERIFIED (§2–6) — but because the construction is not committed
and not independently reproducible (§1): the charter's own reproduction gate (1e-12) fails by
4 orders of magnitude, the slot accounting in the charter text is internally inconsistent
(12.2 slots ⇒ 0.82%/sleeve vs "4.55% each" ⇒ 2.2 slots; measured effective weight ≈2.3–2.5%
per-unit, matching neither), and V2 silently changes the 11-pool federal-holiday/cost
convention relative to the committed FIX builder (fed rows kept at ~−5.2bp cost-only values,
smeared chunks dropped — conservative, worth ~−0.08%/yr, but undisclosed and uncommitted).
**Inflation found: NONE in the quoted numbers.** The one pre-existing scoping caveat carries
over: full-span file has 1/21 negative years (2006 stub −1.38%); "0/19" holds only 2008+.
**Required remediation (same standard as honest11_build.py):** commit a parameterized
honest13_build.py with the slot-weight extension, the exact rows-kept/federal-row convention
actually used, the exact new-sleeve slot accounting, and a --verify mode reproducing the 3
committed CSVs ≤1e-12; until then HONEST11FIX (byte-reproducible, independently verified) must
remain the champion of record. Goal-set scoreboard (all variants): ann≥80 FAIL, SR≥5 FAIL
(CI [3.50,4.33]), DD≤7 PASS (−4.96%), lev≤1.6 FAIL (3.45x), profit≥0 2008+ PASS — unchanged,
and §6 shows NO slot weight 0..0.5 changes any verdict.

UNVERIFIED (do not exist / not checkable from committed material):
- The exact V2 recipe (§1) — the central unverified item.
- Instrument-cost adjustment ("capW.diff() on the slot-weighted scale book") and the exact
  reb/borrow/throttle terms as applied in V2 — inferred only through residuals.
- CFX4 meta "max|day| +3.30% (2025-04-04)" vs committed file max +2.70% (2024-11-07);
  +3.30% appears in my raw rebuild, not the delivered file — one of the two artifacts
  diverged (minor, does not affect gates).
- Whether the coordinator's uncommitted V2 heredoc applied vt-scaling to the new sleeves
  (meta says delivered UNSCALED; my best-fit weights are consistent with unscaled).

AUDIT_V2 DONE
