> SUPERSEDED 2026-09-19 (ITER43 A5r2-vt015 adoption): the champion of record is now **ann 23.68% / SR 3.764764 / MDD -3.66% / 0 neg years** (csv sha16 e67446186e269b88 / weights bde8612d0b295068; prior ITER21 pair 8559fa55ee9a3417 preserved in coord/ITER43_A5R2_VT/prior_champion_backup/). Headlines below are historical.
GOAL100 ITER37 - QAXASTS TSMOM MAW AXIS (SIGNAL-PARAMETER AXIS, LARGEST REMAINING
UNMEASURED SECOND-TIER CELL 7.59 PCT) - HONEST NEGATIVE; NO-ADMISSION, NO REVEAL CONSUMED;
INCUMBENT IS THE MEASURED-GRID IS-ARGMAX (ITER17-LAW CLOSURE 12) (2026-09-19, session 18)

Operator objective (6th verbatim issue): keep improving; leverage <= 1.6; maximize Sharpe;
annual return >= 20 pct. Champion of record UNCHANGED:
GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417 / weights
d2d11c92a98683df / ann 23.6054 pct / SR 3.751429 / MDD -3.6130 / gross 1.0 / 0 neg yrs.
Gauntlet ok=true 7/7 fresh this session (coord/verify_champion_r3_last_session18.json;
weights 8.327e-17 / bytes 1.032e-16 / gross 1.0000000). Session-18 sandbox: bash-exec,
ps/top/sysctl/memory_pressure and shell redirection gated; all execution through sanctioned
python3 heredoc/file paths.

# THE CELL
The diescrack gate-Z axis closed as ITER17-law closure 11 (#128). The largest remaining
UNMEASURED legal cell is QAxasts - measured 7.5906 pct book share at the A2 anchor - a SINGLE
sleeve with ONE acceptance-era frozen scalar MAW=189 (5-leg cross-asset TSMOM on free FRED
spot series: OIL, GOLD, synth dur-8.5 BOND, FX=-DXY, VIXS=-VIX; sign(px-MA) EW 20%/leg, Wed
rebalance, T+1, 6bps, vt10; E1 de-truncated variant, panel floor 2006-09). The acceptance-era
plateau (campaign/scripts/QA_xasts_tsmom189.py, recorded VERBATIM) was STANDALONE sleeve SR on
the TRUNCATED vintage: 42:0.89, 63:0.83, 94:0.88, 126:0.93, 157:0.97, 189:1.06, 252:1.10,
315:1.08, 378:1.04 - maw=189 chosen MID-PLATEAU (252 printed HIGHER at 1.10). Book-level
pool-fit IS-SR under the current objective was never measured over MAW. Honest attribution
carried from acceptance: the VIX-regime leg carries nearly all the edge (VIX-leg alone SR
1.08; drop-VIX 0.25) - sweeping MAW sweeps the VIX flip.

# PRECOMMIT (sealed BEFORE any candidate)
FINDINGS_PRECOMMIT.md sha16 a8ea3922b5e64de3. Grid = {126, 157, 189, 220, 252}: anchor 189 +
acceptance-PRINTED plateau neighbors 157/252 + printed outer neighbor 126 + midpoint 220.5->220
(rounding disclosed at seal). All points INSIDE the acceptance envelope 42..378 (no extension).
min_periods=MAW//2 swept COUPLED (derived, not a second scalar). Stop rule unchanged: at most
ONE reveal at the IS-argmax among admitted cells; NO-ADMISSION => no reveal. A1 pre-seal:
re-typed generator vs saved sleeve maxdev 9.996344e-17, inner n=4947, spans identical
2006-12-13..2026-08-12.

# NEW DEFECT D17 (disclosed at seal; NOT fixed this session)
tools/quant/data/twelve_big/manifest.csv (UNTRACKED, mtime 2026-09-08 14:40) poisons
campaign/harness/data.py panel(): the glob picks it up and parse_dates=["date"] raises
ValueError -> D.closes() and every module importing r6lib UNIMPORTABLE since 09-08 (closes()
would also KeyError "close"). FIRST campaign code to hit it. Mitigation: the driver pre-patches
panel() at RUNTIME to skip manifest.csv exactly - byte-faithful reconstruction (saved sleeve
predates the manifest; A1 1e-16 proves it), no repo mutation. Repo-side fix approval-gated.

# RESULT (driver_iter37.log)
- Machinery: driver_iter37.py derived from driver_iter36.py by 34 deterministic
  asserted-exactly-once substitutions (make_driver_iter37.py); py_compile OK; frozen-block
  AST-text-identity (fit_relw/apply_cap/project_wmax/build_book) vs driver_iter36.py GREEN
  at run start.
- Anchors ALL EXACT: A2 projection identity 0.0 exactly / weights 8.327e-17 / bytes 9.996e-17 /
  rows 1809 / k_covered 11 / IS-SR 4.198632 / Wmax_sf 1.8115x / QAxasts share 7.5906 pct;
  anchor cell weights 7.856e-09 (SLSQP boundary-jitter class) / book 4.877e-10 / block 0.300000.
- Sweep 5/5 cells LIVE (regen-dev 0.042-0.069, real curves): MAW 126 -> 4.162711,
  157 -> 4.170947, 189 -> 4.198632 (ANCHOR), 220 -> 4.190418, 252 -> 4.192827.
- ADMITTED 0/5 (jitter tolerance 1e-4). EVERY novel cell strictly below the bar; closest miss
  MAW=252 at bar-0.0058. Curve rises into the anchor from the left (4.163->4.171->4.199);
  right side dips at 220 (4.190) then ticks up at 252 (4.193, still below bar) - single-peak
  at anchor within resolution; right side NOT strictly monotone, disclosed as measured.
  IS-ann flat 18.10-18.12 pct; IS-MDD tightens slightly with MAW (-2.63 -> -2.52); Wmax_sf
  under the 2.0x wall everywhere (1.81-1.88x).
- NO REVEAL consumed (sealed stop rule). No candidate CSVs exist. Champion sha pre==post
  asserted by the driver.

# READING
Fifth closure shape in the signal-parameter class, and the strongest negative type available:
DUR interior-max (32); k freeze OOS-vindicated-by-police (33); zb monotone-right then upgraded
to full interior peak (34/35); diescrack NOT-argmax-but-police-killed (36); tsmom
anchor=measured-grid-argmax (37) - IS closes the cell with NO escape cell at all (contrast
diescrack, where IS left Z=1.75 and the police had to kill it). The acceptance-era mid-plateau
choice of 189 is vindicated at book level DESPITE 252 printing higher standalone (1.10 vs
1.06) on the truncated vintage: pool interaction, not standalone SR, sets the optimum -
consistent with the ITER15-22 weight-lever exhaustion findings.

# FRONTIER
FOURTEEN axes measured-closed (adds tsmom-MAW as the 14th). Remaining second-tier cells:
dualmom band121 (5.72pct, multi-scalar - needs the pre-committed 1-D slice rule like
diescrack L40), brwt per-variant lb (refused as mining). Levers UNCHANGED: purchased data
or operator rule change.

# VERIFICATION
test_iter37_tsmom_maw.py 6 pins (champion shas / precommit seal + mtime ordering / anchors /
sweep rows + argmax + no-candidate / verdict / cross-ITER family re-certification with
ITER35+ITER36 logs), mutation-checked RED (1 failed on a faked regen number) -> byte-exact
restore (driver_iter37.log sha16 254f775bc718de39) -> GREEN. Full suite from repo root:
569 passed / 0 failed / 0 errors in 81.18s (563 + 6). HONESTY RECORD: the 12:16 first full
suite run reported 7 failed / 4 errors under a machine load spike (5-min loadavg 11.5) that
then SIGKILLed every pytest spawn for ~10 minutes (rc=-9, sub-second chunks included, no
output captured); identities of those transients are UNKNOWN (output lost to the kills), the
post-spike rerun is fully green, and no ITER37-caused failure exists (my pins were green
before, during, and after the window).

# ARTIFACTS
coord/ITER37_TSMOM_MAW/: FINDINGS_PRECOMMIT.md (a8ea3922b5e64de3), FINDINGS.md (with suite
addendum + session environment note), make_driver_iter37.py, driver_iter37.py (16104 bytes),
driver_iter37.log (sha16 254f775bc718de39), arm_MAW{126,157,189,220,252}_weights.csv,
pytest_session18.txt (empty - killed run, kept for the record).
coord/verify_champion_r3_last_session18.json (fresh gauntlet 7/7).
