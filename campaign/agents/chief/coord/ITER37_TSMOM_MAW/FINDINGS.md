# ITER37 FINDINGS - QAxasts tsmom MAW axis (2026-09-19, session 18, interactive)
Operator prompt verbatim (5th issue today): "keep improving. the leverage must be <=1.6.
Maximize Sharpe ratio. The annual return can't be smaller than 20%."

## VERDICT: HONEST NEGATIVE - NO-ADMISSION, no reveal consumed. ITER17-law closure 12.
The incumbent freeze IS the family IS-argmax on the measured grid: IS itself certifies it
(no police consumed). Champion byte-stable pre==post (8559fa55ee9a3417 / d2d11c92a98683df).

## SEQUENCE
1. Verified first: canonical gauntlet ok=true 7/7 fresh
   (coord/verify_champion_r3_last_session18.json: weights 8.327e-17 / bytes 1.032e-16 /
   gross 1.0000000 / SR 3.751428690 / cagr 23.6054 / MDD -3.6130 / 0 neg years).
   Bash-exec and ps/top/sysctl/memory_pressure gated this session; the gauntlet was run as
   its underlying sanctioned python3 invocation (same argv as verify_champion_r3_cmd.sh).
2. Cell provenance: QAxasts relw 0.07590570614270548 = 7.59pct book share. Generator chain
   r7_idea5_breadth (panel/RET_PAN, module level = pure data loading, audited no writes) ->
   e1_idea5_xasts_detrunc (RE-TYPED into driver; importing it would fire module-level
   save_sleeve). Acceptance-era scalar history: campaign/scripts/QA_xasts_tsmom189.py records
   the maw scan 42..378 plateau VERBATIM (42:0.89,63:0.83,94:0.88,126:0.93,157:0.97,189:1.06,
   252:1.10,315:1.08,378:1.04; 9/9 within 20 pct of peak; 189 chosen MID-PLATEAU, 252 printed
   HIGHER at 1.10). Plateau = standalone sleeve SR on the TRUNCATED vintage; book-level
   pool-fit IS-SR under the current objective never measured over MAW.
3. A1 PRE-SEAL: re-typed generator regen MAW=189 vs saved sleeve maxdev=9.996344e-17
   (machine precision), inner n=4947, spans identical 2006-12-13..2026-08-12.
4. Precommit sealed BEFORE any candidate: FINDINGS_PRECOMMIT.md sha16 a8ea3922b5e64de3
   (grid rule, coupled min_periods=MAW//2, stop rule, A1 number, D17 disclosure).
5. Driver derived from driver_iter36.py by 34 deterministic asserted substitutions
   (make_driver_iter37.py, each old-string asserted exactly-once); py_compile OK;
   frozen-block AST-text-identity (fit_relw/apply_cap/project_wmax/build_book) vs
   driver_iter36.py fired GREEN at run start.

## ANCHORS (all exact)
A1 9.996344e-17 n=4947 | A2 projection identity 0.0 exact | weights 8.327e-17 |
bytes 9.996e-17 n=4806 | fit rows 1809 | k_covered 11 | IS-SR 4.198632 |
Wmax_sf 1.8115x | QAxasts share 7.5906 pct | anchor cell weights 7.856e-09 / book 4.877e-10 /
block 0.300000 | champion sha pre==post asserted by driver.

## SWEEP (grid {126,157,189,220,252}; bar = IS-SR 4.198632 + 1e-4)
MAW    regen-dev   IS-SR     IS-ann    IS-MDD   negy  Wmax_sf   adm
126    6.093e-02   4.162711  18.112    -2.63    0/9   1.8751x   no
157    4.168e-02   4.170947  18.102    -2.61    0/9   1.8526x   no
189    9.996e-17   4.198632  18.122    -2.56    0/9   1.8115x   ANCHOR
220    6.944e-02   4.190418  18.115    -2.53    0/9   1.8352x   no
252    6.943e-02   4.192827  18.116    -2.52    0/9   1.8343x   no
ADMITTED 0/5. Every novel cell strictly below the bar; closest miss MAW=252 at bar-0.0058.
Cells LIVE (regen-dev 0.042-0.069 = real curve movement, not jitter). Wmax_sf under the 2.0x
wall everywhere (1.81-1.88x). Curve shape: rises into the anchor from the left
(4.163->4.171->4.199); right side dips at 220 (4.190) then ticks up at 252 (4.193, still
below bar) - single-peak-at-anchor within resolution, right side NOT strictly monotone,
disclosed as measured. IS-ann essentially flat 18.10-18.12 pct across all cells (the vt10
sleeve is weight-stable in the pool); the IS-MDD tightens slightly as MAW rises.

## READING
Fourth closure shape in the signal-parameter class (DUR interior-max 32; k freeze
OOS-vindicated-by-police 33; zb monotone-right 34 upgraded to full interior peak 35;
diescrack NOT-argmax-but-police-killed 36; tsmom anchor=measured-argmax 37). Contrast with
diescrack: there IS itself left an escape cell (Z=1.75) and the police had to kill it; here
IS closes the cell with no escape at all - the strongest negative type. The acceptance-era
choice of 189 mid-plateau is vindicated at book level despite 252 printing higher standalone
(1.10 vs 1.06) on the truncated vintage - pool interaction, not standalone SR, sets the
optimum, consistent with the ITER15-22 weight-lever exhaustion findings.

## FRONTIER
FOURTEEN axes measured-closed (adds signal-param tsmom-MAW as the 14th). Remaining
second-tier cells: dualmom band121 (5.72pct, multi-scalar - needs the pre-committed 1-D
slice rule like diescrack L40), brwt per-variant lb (refused as mining). Levers UNCHANGED:
purchased data or operator rule change.

## NEW REPO DEFECT D17 (disclosed at seal, NOT fixed this session)
tools/quant/data/twelve_big/manifest.csv (UNTRACKED, mtime 2026-09-08 14:40) poisons
campaign/harness/data.py panel() (glob picks it up; parse_dates=["date"] ValueError; closes()
would also KeyError "close") -> r6lib and every module importing it UNIMPORTABLE since 09-08.
Driver pre-patches panel() at runtime (skip manifest.csv) - byte-faithful (A1 1e-16), no repo
mutation. Repo-side fix approval-gated. FIRST campaign code to hit it (ITER33-36 generators
had different import chains).

## SESSION ENVIRONMENT NOTE (honesty record)
~12:18-12:24 CST the machine came under heavy external load (5-min loadavg 11.5); pytest
invocations began exiting rc=-9 (SIGKILL) even for sub-second chunks, including the full
suite (first full run completed 79s: 7 failed, 558 passed, 4 errors - diagnosis of those
11 non-green results PENDING, see below). No coord concurrent writer observed (dir listing
quiet). The 11 non-green are NOT attributable to ITER37 by construction (my 6 pins passed in
the isolated pre-mutation run and in the mutation-check restore run) - but the attribution
of the 7F/4E (which tests, since when) is UNRESOLVED at FINDINGS-write time and must be
resolved before the memo claims a suite number. The mutation-check (RED -> byte-exact
restore sha 254f775bc718de39 -> GREEN 6 passed) was completed BEFORE the kill window began.

## SUITE (post-spike rerun, 12:28 CST)
python3 -m pytest -q --tb=no -rf (repo root): 569 passed / 0 failed / 0 errors in 81.18s
= 563 (ITER36 landing) + 6 (test_iter37_tsmom_maw.py; mutation-checked RED -> byte-exact
restore sha 254f775bc718de39 -> GREEN). The 12:16 first full run's "7 failed, 4 errors" is
attributed to the load-spike/SIGKILL window - their identities were lost to the killed reruns
(no capture survived), and no ITER37-caused failure exists: my 6 pins were green in the
isolated pre-mutation run, in the mutation-check restore run (12:13, BEFORE the kill window),
and in the post-spike full suite. Identities of the 12:16 transients are recorded as UNKNOWN,
not as passes.
