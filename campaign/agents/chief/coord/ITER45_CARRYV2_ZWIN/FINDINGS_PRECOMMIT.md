# ITER45_CARRYV2_ZWIN - FINDINGS_PRECOMMIT (sealed BEFORE any candidate arm ran)

Session 25 (interactive), 2026-09-19 ~20:1x CST. Operator directive (verbatim): keep
improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be
smaller than 20 pct. SAME constraint set as ITER21..44; no rule change, no purchased data.
Objective: max FS SR s.t. lev<=1.6, ann>=20 pct.

## Verify-first (pre-axis; this session = the crashed session-24 tail + this ITER)
- Champion triple re-hashed FRESH by this session (python3 hashlib, shasum gated):
  champion e67446186e269b88 / weights bde8612d0b295068 / canonical vt015 sleeve
  901eebdd3abef617 - all three byte-exact vs the #134/#135 record.
- Session-24 landing VERIFIED instead of re-landed (concurrent-writer rule): the session-24
  writer landed its own tail (test_iter44_carryv2_booktgt.py at bt/tests 19:58, campaign
  memo 20:01, STANDUP entry 20:02, memory #135 + index 20:03-20:04); this session found the
  landing mid-flight and did NOT duplicate any body. SUITE 612 passed / 0 failed OWN RUN
  this session (python3 -m pytest -q, 83.66s) - independent confirmation of the 24 claim.
- Coord quiet at seal time (no coord write since the 20:02:37 STANDUP entry). TWIN HAZARD
  DISCLOSED: the 20:00 cron fire (pid 26697 per session-24 disclosure) wrote
  RAWEW15_REFRESH_CANDIDATE_daily/weights into campaign/results at 20:00:19 (stray-writer
  rule); champion files re-hashed AFTER that write and byte-exact, so the stray touched
  nothing canonical. Next twin fire ~20:30 may land mid-driver: driver asserts champion
  sha16 pre==post and the single-flight lock does NOT serialize interactive vs twin - if a
  collision corrupts an artifact the A-gates fail closed.

## THE CELL (carryv2 family slice 2 - the LAST seal under the 38/39 two-slice standard)
carryv2 printed acceptance plateau (A1_trend_cta/FINDINGS.md line 177, 14 neighbors) has
FOUR printed scalar slices: book-tgt {7,8,9} (MEASURED, ITER44: reveal police-killed G7
3/5), zwin {63,252}, goldL {126,315}, natgas-month variants. SLICE-2 PICK = ZWIN by two
disclosed deterministic rules, fixed at seal time: (1) the namesake core-engine scalar -
the crude-brent z-fade is the lead construction of A1_carry_seasonal_v2 and zwin its
lookback, the same signal-lookback CLASS as closed iters 37 (tsmom MAW) / 39 (dualmom win)
/ 40 (diescrack L); (2) first-listed scalar in the frozen construction spec. goldL and
natgas-months remain UNMEASURED under the consumed two-slice envelope (frontier note;
mirrors 38/39 leaving xs 21/252 frozen as strategy identity). natgas-month variants would
be ineligible regardless (membership-flavored, ITER17-refused class). With this seal the
carryv2 family CLOSES: roster scalar program reaches the exhausted state; census
long-tail remains the only free-data direction.

## GRID (printed points ONLY; zero new points)
ARMS = (63, 126, 252); anchor 126 IS-bar-ineligible. min_periods: the generator rolling
carries NO explicit min_periods (default = window), so window/min_periods coupling is
automatic under the 126->zwin substitution at BOTH rolling sites (the 37/39/40 coupling
rule is structure here, not a choice).

## GENERATOR (re-type disclosure, same as 44)
e1_idea4_carryv2_a1inf.py has MODULE-LEVEL save_sleeve calls -> import would rewrite live
sleeve bytes (ITER33 law) -> carryv2 build RE-TYPED into the driver (the session-24 re-type
A1-proven exact), single scalar zwin parameterized at the line-28 rolling sites, everything
else byte-frozen INCLUDING the 0.08 book re-target (44's axis stays at its anchor value).
A1 anchor: zwin=126 rebuild vs committed E1_carryv2_GLD_2006.csv: maxdev < 1e-12 AND full
nonnan coverage 5179/5179 (the Amendment-1 uncut-emission form). Data-vintage risk
disclosed: GLD.csv mtime 08-13, FRED natgas/brent 08-12, wti_full 08-13, tbill3m 08-12 -
all UNMOVED since session-24's exact A1 pass; driver A-gate still fails closed on drift.

## HARNESS (frozen; text-identity enforced)
fit_relw / apply_cap / project_wmax / build_book asserted text-identical to driver_iter43.py
AND driver_iter36.py at run start (44's frozen check carried). House rules unchanged:
minsharpe, shrink 0.70, brwt-cap 0.30, Wmax 2.0x(k), IS end 2017-01-01, rows asserted 1809,
k_covered asserted 11, gear 1.0, B.BPS 6.4. Swap convention: candidate stream replaces
df12["carryv2"]; fit re-solves the 12-roster weights per arm (42/43/44 convention).

## ADMISSION (per non-anchor arm; all must hold)
is_sr > BAR 4.203733 AND is_mdd >= -0.06 AND IS neg-years = 0 AND Wmax_sf <= 2.0x + 1e-9.
A2 committed-frame continuity per the 36/41/42/44 template (identity 0, weights 8.3e-17,
bytes 1e-16, IS-SR = bar); A2b regen-vs-committed fit-landing jitter DISCLOSED;
FINDINGS reports the admission-margin-vs-jitter ratio.

## REVEAL + OPERATOR GATES (single reveal of the IS-argmax admitted arm; none if no arm admitted)
G1 ann >= 20 pct PERCENT form: (cagr_pct >= 20.0) or (arith_pct >= 20.0)  [D18-fixed form]
G2 capital-real gross <= 1.6 + 1e-9   G3 FS MDD >= -7 pct   G4 0 FS neg years
G5 CFX4 weight = 0   G6 Wmax_sf <= 2.0x
G7 OOS police: >=4/5 bins positive dSR vs the champion bytes AND min bin >= -0.10
   AND FS SR > 3.764764. Bins: 2017-18 / 2019-20 / 2021-22 / 2023-24 / 2025-26.
G8 fit-window shrink <= 2 pct (rows 1809).

## STOP RULE (sealed verbatim)
ONE reveal, no second reveal, no re-fit-after-peek. If no non-anchor arm is IS-admitted
-> HONEST NEGATIVE, slice closed AND carryv2 family CLOSED under the two-slice standard.
Champion byte-stability asserted pre/post driver run (e67446186e269b88 / bde8612d0b295068).
Any post-seal change = numbered Amendment re-sealed and disclosed BEFORE the driver runs.

## DERIVATION
driver_iter45.py derived from driver_iter44.py by asserted exact-count string
substitutions (the 37/42 pattern; make_driver_iter45.py persisted next to the driver),
py_compile gate before any run.

## Sealed
sha16 of this file at seal time is recorded in the driver_iter45.py header assert.


## AMENDMENT 1 (sealed BEFORE any corrected arm ran; no candidate computation has occurred)
Run-1 DIED AT A1 FAIL-CLOSED (pre-computation, derivation defect - MY substitution set, not
the session-24 re-type and not a data event): A1 recon ok=False maxdev=1.761e-01 with
inner=5179/5179 FULL coverage - pure value divergence, no coverage loss. ROOT CAUSE: in the
derivation from driver_iter44.py, renaming the build parameter tgt->zwin (correct for the
rolling sites) ALSO rewrote the SLEEVE BOOK RE-TARGET site: `sleeve = (m * (tgt / rv)...`
became `(m * (zwin / rv)...)` - the anchor arm was built at a 126 book re-target instead of
the FROZEN 0.08 (scale class 126/0.08 = 1575x clipped at 3: values shattered, support and
calendar identical - exactly the observed signature). Session-24's re-type was A1-exact
9.986e-17 twenty minutes earlier; committed CSV mtime 09-01 UNMOVED and byte-identical
(maxdev 0.0) to 44's saved anchor stream - data vintages exonerated (GLD 08-13, FRED
08-12/13). REPAIR (toward the precommit's own frozen-construction clause "everything else
byte-frozen INCLUDING the 0.08 book re-target"; no grid/gate/stop-rule change): the sleeve
line becomes the LITERAL `(m * (0.08 / rv).clip(0, 3))` - the build parameter feeds ONLY
the two rolling sites. make_driver_iter45.py's S7 pair carries the same defect and is
patched in the same asserted pass (both files py_compile gated); PRECOMMIT_SHA constants
updated to this amendment's hash. The A1 gate caught a coordinator defect pre-computation
- the fail-closed design working as intended; champion asserts had already passed.


## AMENDMENT 2 (sealed BEFORE any arm computation; no candidate computation has occurred)
Run-2 crashed AT THE FIRST ARM STREAM BUILD (pre-computation, same derivation-defect class
as Amendment 1): NameError `tgt` at the arm-loop call site `s = build_carryv2(tgt)` - the
substitution set renamed the loop variable but missed THIS call site (runtime NameError is
invisible to py_compile; the residual sweeps covered filenames/rolling/path tokens, not the
call). A1 anchor in the SAME run: ok=True maxdev=9.986e-17 inner=5179/5179 - Amendment 1's
repair PROVEN exact on the committed frame. REPAIR: call site -> `s = build_carryv2(zwin)`;
grep-audit: lowercase `tgt` token count in the driver is now ZERO (ANCHOR_TGT uppercase
unaffected); make_driver gains the missing sub pair + the new seal. No grid/gate/stop-rule
change; champion asserts already passed in run-2. Fail-closed catches: 2 for 2 pre-computation.
