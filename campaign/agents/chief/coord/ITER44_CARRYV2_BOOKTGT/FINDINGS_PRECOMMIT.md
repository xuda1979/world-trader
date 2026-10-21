# ITER44_CARRYV2_BOOKTGT - FINDINGS_PRECOMMIT (sealed BEFORE any candidate arm ran)

Session 24 (interactive), 2026-09-19 ~19:5x CST. Operator directive (verbatim): keep
improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be
smaller than 20 pct. SAME constraint set as ITER21..43; no rule change, no purchased data.
Objective: max FS SR s.t. lev<=1.6, ann>=20 pct.

## Verify-first (pre-axis)
- Session-23 adoption (ITER43 A5r2-VT015, champion e67446186e269b88 / weights
  bde8612d0b295068) INDEPENDENTLY VERIFIED by this session BEFORE any new work:
  all six sha16 identities byte-exact (champion, weights, vt015 sleeve 901eebdd3abef617,
  historical vt010 sleeve 0316cd1afd446938 untouched, backup pair 8559fa55/d2d11c92);
  independent gauntlet ok=true 7/7 dev-for-dev identical to the session-23 json
  (coord/verify_champion_r3_last_session24.json = MY OWN run);
  full suite re-run by this session = 606 passed / 0 failed AFTER fixing one landing-gap
  defect: GOAL100_ITER43_A5R2VT.md was landed after the session-23 suite run and tripped
  the round4b billing lint on the NEXT run (fix = the lint own additive prescription:
  champion filename + current headline 23.68% added to line 5; #120 race class repeating).
- Coord quiet (cron twin pid 41448 exited ~19:39; refresh-cron artifacts benign per the
  08:07 audit; no live writer at seal time).
- PRE-SEAL ANCHOR PROBE (disclosed; incumbent-frame measurements only, no candidate):
  committed 12-frame via updated B.PATHS: rows 1809 k 11; weights_repro 8.327e-17;
  champion bytes 9.991e-17; IS-SR 4.203733 = the NEW incumbent IS bar (exactly the
  ITER43 argmax-arm admission value); FS SR 3.764764 / cagr 23.6813 / MDD -3.6603;
  Wmax_sf 1.8604x; projection identity 0.0.

## THE CELL (20th axis candidate; 19 measured per ledger #134)
carryv2 (E1_carryv2_GLD_2006.csv, book relw 2.198 pct) = the LAST roster sleeve with
zero campaign-swept scalar axes (session-23 FINDINGS frontier note). Construction
(A1_carry_seasonal_v2 frozen, E1 de-truncated re-emission): EW 1/3 of crude-brent
z-fade (zwin 126, trig 1.0, re-entry 0.75) + natgas winter (months 11,12,1,2) + gold
carry-trend (252/84); member vt 0.10 cap 1.0/3.0; book re-target 8 pct cap 3.0;
GLD from twelvedata 2006-09; COST 6.0 in-generator; emission 2007-06+.

ACCEPTANCE PRINT (agents/A1_trend_cta/FINDINGS.md line 177 + LOG_r3): the saved v2
plateau = 14 neighbors - 6 weight grids +-0.1, zwin 63/252, goldL 126/315, natgas-month
variants, book-tgt 7/9 pct (min ratio 0.90, max 1.09). The printed SCALAR axes are
deterministic grids under the 38/39 two-slice standard; the weight-grid slice is REFUSED
as a mining surface (per-variant brwt-lb class). SLICE 1 (this seal): BOOK-TGT {7, 8, 9}
- the sleeve-level vol scalar, the same axis CLASS as the adopted ITER43 A5r2-VT; printed
points ONLY, zero new points. Remaining printed slices (zwin, goldL, natgas-months) are
unmeasured remainders, slice-2 eligible only under the 38/39 standard.

## GENERATOR (re-type disclosure)
e1_idea4_carryv2_a1inf.py has MODULE-LEVEL save_sleeve calls -> import would rewrite
live sleeve bytes (ITER33 law) -> the carryv2 build is RE-TYPED into the driver from the
generator source, single scalar tgt parameterized, everything else byte-frozen. A1
anchor: tgt=8 rebuild vs the committed CSV (inner-join maxdev < 1e-12, full nonnan
coverage). Data-vintage risk disclosed: regen reads CURRENT twelvedata/GLD.csv + FRED
bytes; any drift since the Sep-1 emission fails A1 closed (DHHNGSP precedent).

## HARNESS (frozen; text-identity enforced)
fit_relw / apply_cap / project_wmax / build_book asserted text-identical to
driver_iter43.py AND driver_iter36.py at run start. House rule unchanged: minsharpe,
shrink 0.70, brwt-cap 0.30, Wmax 2.0x(k), IS end 2017-01-01, rows asserted 1809,
k_covered asserted 11, gear 1.0, B.BPS 6.4. Swap convention: candidate stream replaces
df12["carryv2"]; fit re-solves the 12-roster weights per arm (ITER42/43 convention).

## ADMISSION (per non-anchor arm; all must hold)
is_sr > BAR 4.203733 AND is_mdd >= -0.06 AND IS neg-years = 0 AND Wmax_sf <= 2.0x + 1e-9.

## REVEAL + OPERATOR GATES (single reveal of the IS-argmax admitted arm; none if no arm admitted)
G1 ann >= 20 pct PERCENT form: (cagr_pct >= 20.0) or (arith_pct >= 20.0)  [D18-fixed form]
G2 capital-real gross <= 1.6 + 1e-9   G3 FS MDD >= -7 pct   G4 0 FS neg years
G5 CFX4 weight = 0   G6 Wmax_sf <= 2.0x
G7 OOS police: >=4/5 bins positive dSR vs the NEW champion bytes AND min bin >= -0.10
   AND FS SR > 3.764764. Bins: 2017-18 / 2019-20 / 2021-22 / 2023-24 / 2025-26.
G8 fit-window shrink <= 2 pct (rows 1809).

## STOP RULE (sealed)
ONE reveal, no second reveal, no re-fit-after-peek. If no non-anchor arm is IS-admitted
-> HONEST NEGATIVE, slice closed; slice-2 decision per the 38/39 standard. Champion
byte-stability asserted pre/post driver run (e67446186e269b88 / bde8612d0b295068). Any
post-seal change = numbered Amendment re-sealed and disclosed BEFORE the driver runs.

## Sandbox expectations
Write/Edit on repo denied; python3 heredoc writes are the path (driver split 2 chunks,
py_compile gate); single-op shell commands.

## Sealed
sha16 of this file at seal time is recorded in the driver_iter44.py header assert.


## AMENDMENT 1 (sealed BEFORE any arm ran; no candidate computation has occurred)
Run-1 DIED AT A1 FAIL-CLOSED (pre-computation, driver re-type defect): A1 recon
ok=False, maxdev=9.986e-17 (values EXACT) but inner=5002 vs committed_nonnan=5179.
ROOT CAUSE: my re-type applied the generator line-55 STATS-WINDOW cut
(e = sleeve[sleeve.index >= 2007-06-01], used only for the acceptance eval prints,
per the .meta wording "Eval 2007-06+") to the EMISSION. The generator line-88 saves
the UNCUT sleeve: save_sleeve(sleeve, ...) -> the committed CSV spans
2006-09-27..2026-08-03 (GLD bdate start .. the natgas/brent tail), 5179 rows. The
177 missing rows are exactly 2006-09-27..2007-05-31 business days. REPAIR (toward
the generator of record, no grid/gate/stop-rule change): build_carryv2 returns the
FULL sleeve (no emission cut); the book frame starts 2008-03-31 so no arm stream
inside the fit window is affected in any way. Diagnostics disclosed: committed head
2006-09-27 = GLD-driven intersection start; committed tail 2026-08-03 = the
natgas/brent calendar tail; GLD.csv mtime Aug-13 (unrefreshed); save_sleeve
fillna(0)s (no NaN in the committed file). Precommit section "GENERATOR" wording
"emission 2007-06+" is CORRECTED by this amendment to "emission = full sleeve from
the GLD start; 2007-06+ was the acceptance stats-print window".
