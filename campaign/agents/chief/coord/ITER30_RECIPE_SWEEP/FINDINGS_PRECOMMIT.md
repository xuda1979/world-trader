## ITER30 PRE-COMMIT - A6R7 RECIPE-HYPERPARAMETER SWEEP (sealed BEFORE any candidate computation)
Sealed: 2026-09-19 ~06:2x, session #12 ("keep improving" #6). Operator objective (4th verbatim resend): keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%.

#### CHARTED-CELL PROVENANCE
Ledger #120 (2026-09-19, sessions #10/#11) charted the next legal unmeasured cell: the champion's own recipe hyperparameters (trend K378 / cadence 42 / VT12 / cap5) - never swept under the current objective. #121 spent the ITER29 label on the covariance-target axis instead, leaving THIS cell open. Prior partial evidence DISCLOSED: e1_idea2_a6r7_brwt_detrunc.py once printed a standalone K-plateau line (K in 252..504, standalone sleeve SR only - no pool fit, no gates, no reveal); a standalone screen does not close a pool-level cell (ITER17 law).

#### VERIFY-FIRST STATE (this session, before sealing)
Gauntlet ok=true 7/7 (coord/verify_champion_r3_last_iter30start.json): weights 8.327e-17 / bytes 1.032e-16 / gross 1.0000000 / SR 3.751428690 / CAGR 23.6054 / MDD -3.6130 / 0 neg years. Anchors (anchor_iter30.py -> anchors.json): A1 shas champion 8559fa55ee9a3417... weights d2d11c92a98683df... a6r7 sleeve e281e8c4cc5682fb...; A2 legacy generator reproduces the saved a6r7 stream max dev 9.975e-17 (n 9168, 1990-01-04..2026-08-27) - the sweep foundation IS the incumbent stream source; A3 12-pool mirror (IMPORTED from coord/ITER24_DATA_AXIS/driver_iter24.py - byte-verbatim by construction) byte dev 9.996e-17 / weights 8.327e-17 / n 4806 / IS-SR 4.198632 / FS-SR 3.751429 / k_covered 11. No concurrent writer (coord quiet since ITER29 05:3x).

#### SCOPE
Slot a6r7 ONLY; the other 11 slots byte-frozen at committed files. FROZEN internals: DGS2 data file, DUR=1.9 (instrument definition: synthetic 2y TR = -1.9 dy + y/252), sleeve cost 6.0 bps legacy (NOT the census transplant 6.4 - A2 pins the legacy path), T+1 (shift(1)), expanding(60) vol window. SWEPT knobs (the four named by #120): K, CAD, VT, CAP.

#### GRID (frozen, 90 cells)
K {252,315,378,441,504} x CAD {21,42,63} x VT {0.08,0.12,0.16} x CAP {3.0,5.0}. Cell (378,42,0.12,5.0) is the incumbent anchor cell -> 89 novel cells. No post-hoc cell additions.
#### PIPELINE PER CELL
Regenerate the a6r7 stream on the legacy path with knob substitution -> swap into the slot -> refit the 12-pool (fit_relw_mirror + apply_brwt_cap_mirror on the TRUE 12-union frame, IS < 2017-01-01, shrink 0.70 / brwt-cap 0.30 / CFX4 pinned 0) -> build book at gear 1.0 -> record the row. Every cell row lands in cells.json (the 90-row table; the ITER24 28-row convention).

#### FILTERS (admission = ALL five)
A. scale-free Wmax: max share x k_covered <= 2.0 + 1e-9 (k_covered = 11; #120 corrected convention, NEVER x13).
B. jitter: candidate IS-SR - incumbent IS-SR > 1e-4 (#120; solver noise is not alpha).
C. IS risk: IS-MDD >= -6 percent AND 0 IS negative years (census filter set verbatim).
D. operator cap: FS gross max <= 1.6 + 1e-9 (cap stands; #109 law; 4th resend re-affirms).
E. coverage: candidate union frame identical to incumbent (n 4806, same first/last dates) - no window shrink.

#### SELECTION + STOP RULE (frozen)
ONE global argmax among admitted cells by IS-SR; deterministic tie-break: smaller L1 distance to the incumbent cell (K,CAD,VT,CAP), then lexicographic. If NO cell is admitted, or argmax IS-SR <= bar + 1e-4: NO REVEAL, KEPT=[], honest negative. Otherwise exactly ONE reveal of the argmax cell, in order: (i) causality probe (3 fracs 0.25/0.5/0.75; pre-probe path dev must be 0.0); (ii) FS gates vs the committed champion: FS-SR > 3.751429; 5-bin OOS dSR (edges 2017/2019/2021/2023/2025) >= 4/5 positive AND full-OOS dSR > 0; CAGR >= 20 AND arith >= 20; MDD >= -7; 0 neg years; worst year > -5; gross <= 1.6. ALL pass => ADOPT as champion candidate (landing protocol: --emit round-trip, gauntlet, TDD pins, memo). ANY fail => REJECT, record, STOP. No second reveal.

#### DISCIPLINE
Mid-run defect => fail-closed, disclose in FINDINGS, full re-run before any verdict (ITER29 driver-defect discipline). No self-relaxation of any operator constraint. Disclosure of an implementation-risk surface: the knob substitution touches ONLY the generator constants (DUR/K/CAD/VT/CAP are module-level in the legacy snippet); if any cell produces NaN/empty stream the cell FAILS CLOSED (not dropped silently).


#### AMENDMENT 1 (mid-run, at the anchor gate - BEFORE any candidate verdict; run stopped fail-closed)
OBSERVED: incumbent-cell anchor FAILED on first execution - weights-vs-committed dev 5.483e-09 > 1e-9 gate, while gen-vs-saved stream dev was 9.975e-17 and IS-SR/FS-SR printed identical to 6dp (4.198632/3.751429). ROOT CAUSE: the anchor cell was computed on the REGENERATED stream; its 9.975e-17 float-CSV round-trip delta vs the saved file propagates through the SLSQP fit, whose optimum sits on the brwt-cap active-set boundary, jittering weights at ~5e-9. Not a mirror defect: A3 on committed bytes measured 8.327e-17. REPAIR (Amendment 1): the incumbent anchor cell is computed on the SAVED stream (committed bytes; A3 convention), regenerated streams are used for the 89 novel cells only; the bridge is A2 (regenerated == saved at 9.975e-17). Gate B/admission machinery unchanged; bar remains the in-run incumbent IS-SR. Full 90-cell re-run from scratch after the patch. New sealed sha16 recorded in FINDINGS.


#### AMENDMENT 2 (mid-run, post-first-complete-run - verdict INVALIDATED before recording; no reveal fired)
OBSERVED: NO_ADMIT verdict on run 2 is VOID - gate E as sealed (candidate stream last index == union last index) is failed BY THE INCUMBENT ITSELF: the a6r7/DGS2 calendar ends 2026-08-27 while the 12-slot union ends 2026-08-28 (structural one-day tail gap inherent to the slot); every one of the 90 rows incl. the champion anchor read E=0, so the admission machinery could never fire. x13-lesson class: a filter the live champion fails is definitionally wrong. Candidate STATS are valid and deterministic (recompute-identical); only the E flag was miscalibrated. REPAIR: gate E redefined as FIT-ROW CONTINUITY - the candidate IS fit-row count (have-coverage names, dropna - the fit rule own convention, CFX4 lesson) must EQUAL the incumbent count measured in-run on the same frame (run-2 incumbent count recorded in cells.json via ROWS_FIT_INC); all variants share the DGS2 quote calendar post-2008-03-31 so this is the exact no-window-shrink condition with none of the tail artifact. Stop rule unchanged; full 90-cell re-run; if admission now fires, the ONE reveal proceeds per seal.
