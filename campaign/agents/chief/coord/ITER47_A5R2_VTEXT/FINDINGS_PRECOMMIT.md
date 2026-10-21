# ITER47_A5R2_VTEXT - FINDINGS_PRECOMMIT (sealed 2026-09-19 ~21:1x CST, session 27, BEFORE any candidate computation)
A1 anchors ran PRE-seal and are disclosed inside per the #117/#133 precedent.

### Operator directive (verbatim)
"keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%."

### Cell (23rd measured axis; per-sleeve scale class)
A5r2 per-sleeve vol-target VT UPPER-EDGE EXTENSION. The ITER43 sealed grid {0.06, 0.08, 0.10, 0.12, 0.15} ended AT the adopted champion cell VT=0.15 with the IS curve MONOTONE RISING into the edge and the argmax AT the edge (driver_iter43.log arms: 4.188280 / 4.194835 / [4.198632 anchor] / 4.201156 / 4.203733; admission [0.12, 0.15]; single reveal 8/8 ADOPTABLE; champion MOVED to e67446186e269b88). ITER43 FINDINGS verbatim: "IS gradient monotone rising with argmax AT THE SEALED-GRID EDGE (0.15). Grid extension after seeing results = iterative probing; FORBIDDEN by the sealed stop rule." - i.e. THAT seal could not measure beyond 0.15. THIS file is the fresh legal instrument: the ITER35 lower-envelope second-seal precedent (#126: "a lower-envelope extension seal is the natural next cell if this class is hunted further"), with the result-aware motivation DISCLOSED AT SEAL TIME as that precedent requires.

### Anti-dog-chase binding (pre-committed)
This is the SECOND and LAST seal on the A5r2-VT family. The measured envelope becomes 0.06..0.24 and the axis is CLOSED at seal end REGARDLESS of outcome; a still-rising curve at 0.24 will NOT be chased by a third seal. Any further movement on this family requires a NEW motivation class recorded in the ledger, not an edge continuation.

### Grid + anchor + bars
- ARMS = (0.18, 0.21, 0.24): equal-step 0.03 continuation of the ITER43 grid spacing beyond the adopted cell 0.15 (0.12 -> 0.15 -> 0.18 -> 0.21 -> 0.24). No other points. One shared generator scalar (per-cell grids = mining surface, refused).
- ANCHOR cell VT=0.15 = the COMMITTED champion cell (sleeve sha16 901eebdd3abef617); bar-ineligible by construction.
- IS bar BAR = 4.203733 (committed champion IS-SR, from the adopted fit). FS bar = 3.764764 (committed champion FS SR).
- Clip disclosure: sc = (vt / np.sqrt(252) / vol).clip(0, 2.0) - at vt above 0.15 the 2.0 clip binds on more days. In-family generator identity: the clip is NOT a knob here (the A5r2 mult axis was refused at #43 as monotone-to-endpoint).

### A1 anchors (run PRE-seal; coord/ITER47_A5R2_VTEXT/anchor_iter47_a1.log)
- A1a regen vt010 vs module G.net maxdev 0.000e+00 EXACT (n 4249 both) - the re-typed generator IS the committed generator; module import save-free (save guarded under __main__).
- A1b regen vt015 vs committed sleeve bytes maxdev 9.996344e-17, inner 4249 FULL (4249/4249) - the committed champion sleeve IS this generator at vt=0.15.
- Champion trio at seal: e67446186e269b88 / weights bde8612d0b295068 / vt015 sleeve 901eebdd3abef617. Session-27 verify-first: canonical gauntlet 7/7 fresh (verify_champion_r3_last_session27.json: weights_repro 8.327e-17, byte_repro 1.006e-16, half-turn rejected 1.61e-5, gross 1.0000000000006 n_over 0, 0 negy, MDD -3.66, SR 3.7647642, cagr 23.6813); baseline suite 624 passed / 0 failed own run 73.63s. Stray disclosed: cron-twin RAWEW15_REFRESH_CANDIDATE pair re-emitted 20:53 (deterministic refresh of the dead OPT_V-family artifact; champion re-hashed after it, unaffected).

### Method (driver derived from driver_iter43.py)
- make-driver with asserted-exactly-once substitutions (15): OUT dir; PRECOMMIT_SHA; BAR 4.198632->4.203733; FS_BAR 3.751429->3.764764; ARMS tuple; ANCHOR_VT 0.10->0.15; A5CSV -> committed vt015 path; A1a re-anchor block (regen vt010 vs module G.net, then anchor regen at ANCHOR_VT); header line; reveal incumbent label 3.751429->3.764764; driver log filename x2 (driver_iter47.log at birth - #136 inherited-name slip not repeated); A2/A2b label de-43-ification; admission jitter margin BAR -> BAR + 1e-4 (STRICTER than 43's raw >BAR, disclosed; 43's measured landing jitter 7.05e-10 IS-SR - the margin kills shadow-pricing-scale admissions).
- Frozen blocks (fit_relw / apply_cap / project_wmax / build_book) UNTOUCHED; run-start AST text-identity vs driver_iter41.py AND driver_iter36.py asserted in-driver.
- Coverage law: same-12-names membership; only the A5r2 column VALUES change; its NaN calendar is vt-invariant (vol warmup depends only on net0, not vt) -> per-arm assert rows==1809, k==11 stands. The #137 inherited-assert trap is a NEW-MEMBER class and does NOT apply here.
- A2 committed-frame continuity: regen-committed-frame refit vs weights bde8612d0b295068 <1e-12; book bytes vs e67446186e269b88 <1e-12; IS-SR = 4.203733 within 5e-6. A2b regen-vs-committed fit-landing jitter logged and disclosed.
- REVEAL: at most ONE, at IS-argmax of admitted; gates G1..G8 verbatim from the D18-fixed lineage (G1 percent form); G7 = at least 4/5 positive bins AND min dSR >= -0.10 AND f_sr > FS_BAR; G8 fit-window shrink <= 2pct.
- STOP RULE: no admission OR any gate fail => no second reveal, honest negative, family bracket CLOSED end-to-end.
- If 8/8 ADOPTABLE: full battery in-session BEFORE any adoption, per the #43 Amendment 2 protocol (canonicalization to bt/verify_champion.py's own algebra; independent gauntlet 7/7 on the canonical pair; coherence halves). Adoption then follows the #43 landing protocol (r3 cmd + builder PATHS update, re-pin wave with era adjudication, 6 mutation-checked pins, memo BEFORE suite, STANDUP, memory). Driver asserts champion + weights sha16 pre==post.

### Known risks disclosed
- SLSQP landing-jitter class (#43 run-2): the anchor arm fits the REGEN stream; ~1e-16 input deltas can amplify to ~1e-8 weights. Mitigated by A1b byte-exactness (9.996e-17) and A2 on the COMMITTED frame (43's Amendment 1 template, already in the base driver). If A2 fail-closes: Amendment appended and re-sealed BEFORE any corrected run; no verdict recorded from a failed run.
- Machine load: the #136 SIGKILL lesson - no heavy parallel work during pytest runs; driver run is single-process.

### Refused alternatives (recorded at seal, before results)
- carryv2 goldL third slice: two-slice standard (38/39); family CLOSED at #136.
- carryv2 natgas-months: membership-class-refused (#136).
- brwt per-variant lb: mining surface, refused (#128/#130).
- Census remainder: measured-closed END-TO-END at #137 (cad_govt_long was the last legal cell; police-killed).
- VT DOWNWARD extension: the 43 curve is monotone RISING through 0.15, so every lower cell is IS-dominated (ITER34/35 monotone class); refused without computation.
- Wmax relaxation / G7 relaxation / purchased data: operator rule changes, not cells; G7 price-tag curve on record (+0.0366/+0.0161/+0.0075/+0.0073/+0.0034/+0.0026/+0.0025/+0.0013), recommendation KEEP stands.
