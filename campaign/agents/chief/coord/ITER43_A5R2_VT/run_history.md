# ITER43 driver run history (coordinator-recorded 2026-09-19 session 23)

Run-1 (~19:0x CST): NameError at def-time - frozen project_wmax default arg binds
module-level BRWT_BLOCK; the constant line was omitted from the driver header.
FAILED BEFORE any computation (frozen check, precommit assert, champion asserts and
all data loads had not executed). Fixed: added module-level
BRWT_BLOCK = ("brwt10", "brwt7", "brwt5"). Traceback not preserved on disk (tool-layer
capture only); recorded here per fail-closed disclosure discipline.

Run-2 (~19:1x CST): full sweep executed; A1a anchor-vs-module maxdev=0.000e+00,
A1b committed-CSV recon ok=True maxdev=9.975e-17, all 5 arms rows=1809 k=11
projection-identity 0.0; then A2 FAIL-CLOSED: anchor arm fitted the REGEN stream ->
weights maxdev=9.913e-09 / bytes maxdev=5.849e-10 vs bar 1e-12 (SLSQP landing-point
amplification of the ~1e-16 regen-vs-committed input delta). ROOT CAUSE = coordinator
deviation from the frozen template (templates 36/41/42 run A2 on the COMMITTED frame).
No reveal executed. Repair sealed as Amendment 1 (precommit sha16 2d9dd522e87f6088):
A2 re-anchored to the committed frame; arms keep regen inputs; jitter disclosed+logged.

Run-3 (amended, ~19:2x CST): GREEN end-to-end. A2 committed-frame continuity
weights maxdev=8.327e-17 bytes maxdev=9.996e-17; A2b jitter log (weights 9.913e-09,
IS-SR 7.050e-10); IS admission [0.12, 0.15]; single reveal VT=0.15 -> 8/8 ADOPTABLE.
Reveal log: campaign/agents/chief/coord/ITER43_A5R2_VT/driver_iter43.log.

Post-reveal: battery step 1 (independent verifier on the driver-fit pair) FAILED
weights_repro 3.816e-09 > tol 1e-9 -> canonicalization repair sealed as Amendment 2
(final precommit sha16 c77a81108d19b500); canonical pair (verifier-algebra rebuild)
re-asserted 8/8 gates; independent gauntlet on canonical pair 7/7 GREEN
(weights_repro 8.327e-17); adoption executed + final canonical gauntlet on the
ADOPTED files 7/7 GREEN.
