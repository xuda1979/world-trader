ITER36 FINDINGS - diescrack gate-Z axis at frozen L=40 (session 17, 2026-09-19).
Precommit 946c617d868816e8 sealed BEFORE any candidate; A1 pre-seal 9.980081e-17
(inner n=4615, saved sha16 c7d19f5bd0b2a603). Anchors ALL EXACT (A2 identity 0.0,
weights 8.327e-17, bytes 9.996e-17, rows 1809, k 11, IS-SR 4.198632, Wmax_sf 1.8115x;
incumbent diescrack share 10.8293 pct; anchor cell weights 6.450e-09 / book 8.494e-10).
NEW: frozen-block AST-text-identity assert vs driver_iter34.py (fit_relw/apply_cap/
project_wmax/build_book) - passed at run start.
SWEEP: 1.5 -> 4.189526 / 1.75 -> 4.204030 ADMITTED / 2.0 -> 4.198632 anchor /
2.25 -> 4.173041 / 2.5 -> 4.175864. Cells LIVE (regen-dev 0.034-0.092). Incumbent NOT
the family IS-interior argmax.
REVEAL Z=1.75: FS SR 3.758736 (+0.007307, third-strongest rejected candidate on record),
all operator gates PASS, G7 bins 2/5 positive (min -0.0060, far above the -0.10 floor;
magnitudes <= 0.012 = structure noise) => REJECT per sealed stop rule. No second reveal.
Champion sha16 pre==post True.
VERDICT: honest negative; ITER17-law closure 11; acceptance freeze Z=2.0 OOS-vindicated
(2nd closure shape). Frontier: THIRTEEN axes measured-closed. Remaining second-tier:
QAxasts tsmom189 (7.59 pct), dualmom band121 (5.72 pct), brwt per-variant lb (refused).
Levers unchanged: purchased data or operator rule change (G7 priced points now
+0.0366/+0.0075/+0.0073, all police-killed; KEEP stands).
Landed: 6 pins mutation-checked RED->restore(3fed7fe5b05a32b4)->GREEN; memo
campaign/GOAL100_ITER36_DIESCRACKZ.md; SUITE 563/0 (557+6, own run 70.84s).
