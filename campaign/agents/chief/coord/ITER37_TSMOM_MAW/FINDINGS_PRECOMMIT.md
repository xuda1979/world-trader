# ITER37 PRECOMMIT - QAxasts tsmom MAW axis (sealed BEFORE any candidate run)
Sealed: 2026-09-19 ~12:2x CST, session 18 (interactive, operator prompt verbatim: "keep improving.
the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than 20%.")

## THE CELL
QAxasts = E1_QAxasts_tsmom189_2006.csv, relw 0.07590570614270548 = 7.59pct of book weight
(champion weights d2d11c92a98683df). One sleeve, ONE generator scalar MAW=189 inherited frozen
from the A3 r7 acceptance era (QA_xasts_tsmom189, campaign/scripts/QA_xasts_tsmom189.py), carried
unchanged into the E1 de-truncated variant (e1_idea5_xasts_detrunc.py, identical construction,
panel floor 2006-09, NO 2008 truncation, vt10 on full history). Construction: 5-leg cross-asset
TSMOM (OIL, GOLD, synth dur-8.5 BOND, FX=-DXY, VIXS=-VIX) on free FRED spot series;
s = sign(panel - panel.rolling(MAW, min_periods=MAW//2).mean()).fillna(0) * 0.2 (EW 20%/leg);
Wed rebalance, T+1, 6bps one-side (wback_rb), trailing expanding vt10 min-60d cap-3x.
Acceptance-era plateau was STANDALONE sleeve SR on the TRUNCATED vintage:
  "42:0.89,63:0.83,94:0.88,126:0.93,157:0.97,189:1.06,252:1.10,315:1.08,378:1.04 (9/9 within
   20% of peak)" - maw=189 chosen MID-PLATEAU (252 printed HIGHER at 1.10).
Book-level pool-fit IS-SR under the current objective (sharpe-max s.t. ann>=20 pct, gross<=1.6)
was NEVER measured over MAW. This axis is the largest remaining unmeasured second-tier cell.

## GRID RULE (pre-committed; no peeking, no per-variant grids - single sleeve, single scalar)
GRID = {126, 157, 189, 220, 252}:
  - 189 = anchor (frozen acceptance value);
  - 157, 252 = the two acceptance-PRINTED plateau neighbors (157:0.97, 252:1.10);
  - 126 = the printed outer neighbor of 157 (126:0.93);
  - 220 = midpoint of the remaining 189..252 gap (220.5 -> 220; integer rounding DISCLOSED HERE
    at seal time, before any run);
  - all five points lie INSIDE the acceptance scan envelope maw 42..378 (no envelope extension,
    no ITER35-degenerate direction; maw<42 or >378 NOT run).
min_periods=MAW//2 is a DERIVED quantity of the frozen construction, swept COUPLED with maw
(not a second free scalar). vt10, EW 20%/leg, Wed/T+1/6bps, panel and RET_PAN all frozen.

## STOP RULE (unchanged, sealed)
At most ONE reveal: the IS-argmax among admitted cells only. Admitted = IS-SR > 4.198632 + 1e-4,
Wmax_sf <= 2.0x, IS-MDD >= -6 pct, 0 IS neg years. Reveal runs the full 8-gate battery
(G7 police: >=4/5 OOS 2-yr bins positive AND min bin dSR >= -0.10 AND FS SR > 3.751429).
G7 FAIL => REJECT per sealed stop rule, no second reveal, no post-hoc re-adjudication.
NO-ADMISSION => honest negative at IS level, no reveal.

## A1 PRE-SEAL (run before this file was written; disclosed here)
Re-typed generator (import chain r7_idea5_breadth -> panel/RET_PAN; r6lib.wback_rb; r7lib.wed_rbd;
B2_highfreq.gates.vol_target; all libs write nothing at module level - audited) regenerated the
anchor MAW=189 stream: regen-vs-saved maxdev = 9.996344e-17 (machine precision), inner n=4947,
spans identical 2006-12-13..2026-08-12. The saved sleeve predates every input-file mtime change
relevant here (sleeve mtime Sep 7 10:59).

## NEW REPO DEFECT D17 (disclosed at seal; NOT fixed this session)
tools/quant/data/twelve_big/manifest.csv (UNTRACKED, mtime 2026-09-08 14:40, header
family,file,date_col,kind,rows,cols,exception) sits INSIDE the price-panel directory and is picked
up by campaign/harness/data.py panel() -> pd.read_csv(parse_dates=["date"]) raises
ValueError("Missing column provided to 'parse_dates': 'date'") -> D.closes() and every module that
imports r6lib at module level has been UNIMPORTABLE since 09-08 (closes() would also KeyError on
'close'). The tsmom generator path is the first campaign code to hit it. Driver-side mitigation
(runtime-only, no repo mutation): pre-patch campaign.harness.data.panel to skip manifest.csv
exactly (restores the original 298-CSV panel; the saved sleeve predates the manifest so this is
byte-faithful reconstruction, proven by the A1 1e-16 result above). Repo-side fix (move the
manifest out of twelve_big or teach panel() to skip non-price files) is APPROVAL-GATED - recorded
for the next grant window. Any agent chartering r6lib-dependent work before then must pre-patch
the same way.

## MACHINERY
driver_iter37.py derived from driver_iter36.py by deterministic asserted string substitutions
(builder asserts each old-string exists exactly once before substituting); frozen-block
AST-text-identity assert (fit_relw/apply_cap/project_wmax/build_book) vs driver_iter36.py fires
at run start. All A2 anchors as in ITER33-36: projection identity exactly 0 on the incumbent,
weights maxdev < 1e-12, bytes maxdev < 1e-12, fit rows 1809, k_covered 11, IS-SR 4.198632,
Wmax_sf 1.8115x; anchor cell reproduces committed weights (<1e-6) and champion book (<1e-9).
Champion shas asserted unchanged pre==post run (8559fa55ee9a3417 / d2d11c92a98683df).
