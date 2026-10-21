ITER40 FINDINGS PRECOMMIT - DIESCRACK GATE-L AXIS AT FROZEN Z=2.0 (SIGNAL-PARAMETER, THE OTHER PRINTED AXIS OF THE 36-REFUSED 2-D SURFACE)

Sealed 2026-09-19 ~14:25 CST, session 20 (interactive, operator prompt verbatim: "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%."), BEFORE any candidate computation. The driver hard-asserts this file sha16.

# MOTIVATION AND LEGALITY (predecessor-consistency)
- ITER36 sealed the Z-slice at frozen L=40 and disclosed "L is NOT swept" as the WITHIN-SEAL 1-D refusal (sweeping both scalars in one seal = the 2-D mining surface, refused there and refused here).
- ITER38/39 established the two-slice FAMILY standard on dualmom (band seal 38, win seal 39, "the OTHER printed axis ... per the ITER35 motivation+determinism principle"): a family is measured-closed only when every printed axis carries a book-level measurement.
- The same standard applied to diescrack leaves the lookback L (the generator's other scalar; acceptance-printed points L=15 and L=40 from the HUNT_BASIS2 delivered pairs (L15,Z1.5) and (L40,Z2.0)) unmeasured at book level. Memory #130's "signal-parameter program EXHAUSTED" predates this seal; this seal completes it with measurement (either direction of verdict).
- One sleeve (diescrack), one swept scalar (L). The 2-D surface stays REFUSED.

# GRID (pre-committed)
L in (15, 27, 40, 53) at frozen gate Z=2.0. Deterministic rule (the 36 convention mirrored): printed points 15 and 40 (the family's two delivered lookbacks), anchor 40 (the champion freeze), midpoint floor((15+40)/2) = 27, one equal-step extension 53 = 40 + (40-27). NO second extension (66): its first z-valid date would fall after the frame start 2008-03-31 - the coverage law truncates the extension, disclosed pre-seal (A1 diagnostic: first z-valid 2008-03-18 at L=53, inside the law). min_periods COUPLED (min_periods=lb - the generator's own frozen convention at L=40). Z<2.0 and Z>2.0 are NOT on this grid (the Z axis is 36-closed; the sibling gate Z=1.5 belonged to the delivered (15,1.5) pair).

# FROZEN (byte-verbatim)
Generator re-typed from the CAMP_COST R6 refresh_sleeves diescrack_build (the committed bytes' proven source; A1 proves the re-type): DJFUELUSGULF (tools/quant/data/newdata, dedup keep-last sorted) x 42.0 gal/bbl vs wti_full (FRED harness) spliced with EIA wti_spot_daily strictly AFTER the FRED last index; sp = log(diesel*42) - log(wti) dropna, truncated at 2008-01-01; rolling(lb, min_periods=lb) mean/std, sd zero-replaced NaN; z = (sp - m) / sd; pos +1.0 where z < -Z, -1.0 where z > Z, else 0.0; T+1 gross = pos * sp.diff().shift(-1); sleeve cost FULL |pos.diff()| x 6.4e-4; borrow 0.005/252 charged where pos or lagged pos nonzero (frozen mask); vol scale (0.08 / (expanding(60).std() * sqrt(252))) clip upper 3.0. Z is the frozen constant 2.0 in every cell.
Pool/fit/build identical to ITER32-39: 12-slot pool B.PATHS byte-frozen; frame from 2008-03-31; IS before 2017-01-01; fit_relw shrink 0.70 diagonal, SLSQP 3-start, W_MAX 2.0 then capped bounds; apply_cap brwt-block share cap 0.30 pro-rata; CFX4 pinned 0; project_wmax water-filling at k_covered 11; build_book gear 1.0, BPS 6.4 FULL |dW|, RATE 4.5 pct on max(gear-1, 0). The four frozen functions (fit_relw, apply_cap, project_wmax, build_book) are asserted AST-text-identical to driver_iter36.py pre-run.

# COVERAGE LAW (asserted per cell)
The regen index is L-invariant (every cell spans the full spread-dropna index from 2008-01-02; asserted index-equal to the anchor cell). Per cell: first z-valid (row L-1) must precede the frame start 2008-03-31 (degenerate-warmup guard); frame-window notna count unchanged; dfc index equals the frozen frame index; fit rows == 1809; k_covered == 11; CFX4 column pinned 0.

# ANCHORS (all must hold before any verdict; fail means STOP, no candidates)
A1 (done, pre-seal, anchor_iter40.log): regen (L=40, Z=2.0) vs the committed sleeve bytes maxdev 9.980081e-17 (inner n=4615, span 2008-03-28..2026-08-24, saved sha16 c7d19f5bd0b2a603 - identical to the 36 A1 vintage, data unmoved since the morning session). Disclosures carried from 36: (i) the regen retains 59 leading warmup rows (2008-01-02..2008-03-27) that the committed emission drops - all pre-frame-start, unreachable; (ii) the 2020-04-20 negative WTI print log() NaN bridge is frozen (pandas RuntimeWarning expected and harmless).
A2: projection identity on incumbent exactly 0.0; relw12 vs committed weights dev below 1e-12; book bytes vs champion dev below 1e-12; fit rows 1809; k_covered 11; incumbent IS-SR 4.198632 within 5e-6; Wmax_sf at k=11 equals 1.8115x.
Anchor cell L=40 in-sweep: weights dev vs committed below 1e-6; book dev vs champion below 1e-9.

# ADMISSION (per cell)
Wmax_sf at most 2.0 plus 1e-9, AND IS-MDD at least -6 pct, AND 0 IS-negative years, AND IS-SR above 4.198632 plus 1e-4 (jitter tolerance per the 2026-09-19 convention).

# SELECTION AND STOP RULE (sealed)
If no cell admitted: HONEST NEGATIVE, no reveal, no candidate CSV, done. Else ONE global argmax over admitted cells ranked by (-is_sr, abs(L - 40), L); ONE reveal. If the reveal fails ANY gate: REJECT, no second reveal, no other cell revealed regardless of its IS or FS numbers.

# REVEAL GATES (verbatim ITER32/33/34/35/36)
G1 cagr >= 20 pct or arith >= 20 pct; G2 gross <= 1.6; G3 FS MDD >= -7 pct; G4 zero FS negative years; G5 CFX4 relw == 0; G6 Wmax_sf <= 2.0x at k=11; G7 OOS police: at least 4/5 positive bin dSR AND min bin dSR >= -0.10 AND FS-SR above 3.751429; G8 fit-window shrink <= 2 pct. Bins 2017-18, 2019-20, 2021-22, 2023-24, 2025-26 vs the incumbent book. All 8 must pass for ADOPTABLE; anything else is REJECT.

# DISCLOSED RISKS AND PRE-ANALYSIS
(a) L=15 is the dominated sibling's lookback (L15/Z1.5 failed the SLEEVE 2017 neg-yr floor at acceptance); 2017 is inside the IS window, so the IS filters (0 IS-neg-yrs, IS-MDD >= -6 pct) are the natural catch at gate Z=2.0.
(b) Shorter L = faster mean-reversion = more dislocation trades = higher turnover and Wmax pressure (the ITER34 zb pattern: Wmax_sf rises as the scalar loosens). The 2021-22 energy-crisis bin remains the known G7 fragility for crack exposure (36 reading: the Z freeze is crisis-regime-protective; L plausibly too - stated BEFORE the run, not after).
(c) The sleeve is a FRED spot PROXY for the HO-CL calendar spread (roll/basis risk disclosed at acceptance); the convention is frozen and L-invariant except the rolling windows.
(d) Candidate streams are regenerated from CURRENT newdata/FRED/EIA bytes; A1 pins the vintage at 1e-16 against the sleeve-emission bytes.
(e) The champion is untouched throughout: read-only sweep; champion and weights sha16 asserted equal pre and post.
(f) D17 (twelve_big/manifest.csv poisons harness panel()) is NOT in this driver's dependency path: the pool loads via rawew13v2_build.load (direct CSV reads; proven by driver36 running clean and by the A1 byte-identity).
