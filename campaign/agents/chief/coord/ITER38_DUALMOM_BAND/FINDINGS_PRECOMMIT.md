# ITER38 FINDINGS_PRECOMMIT - DUALMOM HYSTERESIS-BAND (BAND) 1-D SLICE AT FROZEN WIN=200
Sealed BEFORE any candidate computation. Session 19 (2026-09-19 ~13:1x CST), operator objective
verbatim: "keep improving. the leverage must be <=1.6. Maximize Sharpe ratio. The annual return
can't be smaller than 20%." Champion of record unchanged: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv
sha16 8559fa55ee9a3417 / weights RAWEW13v2_IS_SR_weights.csv sha16 d2d11c92a98683df / ann 23.6054 pct /
SR 3.751429 / MDD -3.6130 / gross 1.0. Canonical gauntlet ok=true 7/7 at 13:04
(verify_champion_r3_last_session19.json: weights 8.3267e-17 / bytes 1.0322e-16 / 0 neg yrs). Coord quiet
before this seal (newest artifact 12:30 = session 18 landing). Frontier at seal: FOURTEEN axes
measured-closed (#129); this is the last second-tier cell with an admissible 1-D slice (the other,
brwt per-variant lb, was REFUSED at #126 as a mining surface and stays refused).

## THE CELL
dualmom = QA_dualmom_band121 (A3_xs_quality r2 accepted sleeve, all 7 gates; the ONLY A3 contribution
per its FINDINGS) = Antonacci dual momentum on the 298-name harness panel:
- xs leg: 12-1 momentum sig = px.shift(21)/px.shift(252) - 1.0; long top tercile (FRAC=1/3) equal weight, min 10 names;
- regime gate: FF value-weighted market (1926+) vs its 200d MA (WIN=200, min_periods=WIN) with a
  +/-BAND hysteresis band (ON only above (1+BAND)xMA, OFF only below (1-BAND)xMA, else hold prior
  state, initial 0); flat when off;
- monthly month-end rebalance, T+1 effective, costs 6.4bps one-side on FULL |dW| (CAMP_COST R2
  costfix convention), vol-target 10 pct ann on trailing expanding window (min 60, cap 5) via
  engine.strategy_ret (trim at first invested day, drop 5 warmup rows).
Book share at the ITER37 A2 anchor: acceptance-recorded 5.72 pct (driver re-measures exactly).
THREE frozen scalars: WIN=200, BAND=0.03, FRAC=1/3 (plus the 21/252 xs lookbacks as strategy
identity). Its acceptance plateau was a 25-cell (MA win x band) grid - 21/25 cells within 20 pct of
peak, (200, 0.03) chosen interior "not a spike" (A3 FINDINGS; grid values in r2_scan5.py lines
38-39: win {150,175,200,225,250} x band {0.01,0.02,0.03,0.04,0.05}) - but that plateau was
STANDALONE sleeve SR on the PRE-costfix 6.0bps half-turn convention; the book-level pool-fit IS-SR
under the current operator objective was NEVER measured over any dualmom scalar.

## THE 1-D SLICE RULE (2-D surface REFUSED at seal - 25-cell mining, same refusal as diescrack L40/Z20)
Sweep BAND (the hysteresis threshold) at FROZEN WIN=200. Threshold-at-frozen-window = the diescrack
class rule. BAND is the sleeve's NAMESAKE scalar ("band121" = band + 12-1) and the FINDINGS-attributed
edge repair ("hysteresis band ... is what repairs 2022 (-6.7 -> -4.3) and 2008/2018").
GRID = {0.01, 0.02, 0.03, 0.04, 0.05} = EXACTLY the acceptance-printed band axis. All 5 points are
acceptance-printed (zero new points; no extensions or midpoints needed; anchor 0.03 centered).
min_periods is band-independent (=WIN) - no coupling rule required.
FROZEN AS IDENTITY (sweeping them = different strategy family, degenerate treatment): the 21/252 xs
lookbacks (the "12-1" in the sleeve name), FRAC=1/3 (documented load-bearing: the tercile
concentration is what fixes the yearly profile, 4 -> 1 neg yrs, +0.03 SR per A3 FINDINGS), WIN=200.
DISCLOSED UNMEASURED DIRECTIONS at seal: (a) the WIN slice {150..250} is acceptance-printed and is
the natural SECOND seal if this one leaves a one-sided open direction (ITER35 pattern: deterministic
reflection + motivation disclosed at seal time required, no free choice); (b) FRAC is a legal scalar
but lower priority (acceptance evidence says it is load-bearing near 1/3). Refused here and now:
the full 2-D (win x band) surface, any per-cell grids, and any non-printed grid values.

## METHOD + FILTER SET (canon, verbatim from ITER24/28/30/36/37)
House pool mirror: rawew13v2_build 12-slot frame from 2008-03-31, fit rows 1809, k_covered 11 (CFX4
zero-coverage, fit really 11 names, CFX4 relw pinned 0), Wmax invariant = max_share x k_covered <= 2.0
(scale-free convention), brwt-block share cap 0.30, shrink 0.70 diag target, gear 1.0, IS_END
2017-01-01, bar IS-SR 4.198632. Admission per cell: Wmax_sf <= 2.0 + 1e-9 AND IS-MDD >= -6 pct AND
0 IS-neg yrs AND IS-SR > 4.198632 + 1e-4 (jitter tolerance). Global argmax over admitted cells only
(tie-break |BAND - 0.03| then BAND). ONE reveal. Reveal battery G1-G8 verbatim: G1 FS ann >= 20 pct
(cagr or arith), G2 gross <= 1.6, G3 FS MDD >= -7 pct, G4 0 FS neg yrs, G5 CFX4 relw = 0, G6
Wmax_sf <= 2.0x (k=11), G7 OOS police = 5-bin (2017-18..2025-26) dSR >= 4/5 positive AND min bin
>= -0.10 AND FS SR > 3.751429, G8 fit-window shrink <= 2 pct (coverage-restricted rows).
STOP RULE: 0 admitted -> honest negative, NO reveal, no candidate CSV exists. Admitted but G7 or any
gate fails -> REJECT, NO second reveal, no other cell revealed. All 8 pass -> verdict "ADOPTABLE",
proceed to full battery + adoption memo + operator-visible swap as a SEPARATE verified step (no
auto-swap in this driver). Champion sha asserted pre==post in every path.

## A1 (run PRE-seal, disclosed inside per the #117/#33 precedent) - PASSED
anchor_iter38.py (persisted; its dualmom_build is byte-identical to the driver's - maker-asserted
via ast extraction): re-typed generator vs committed QA_dualmom_band121.csv
maxdev 9.996344e-17 (inner n=4743), INDEX IDENTICAL True, spans 2007-10-08..2026-08-12 n=4743 BOTH,
head 2007-10-08 = 0.0 both. Panel: 298 names, 2006-09-20..2026-08-12, 240 month-ends. The re-type
therefore reproduces the committed emission EXACTLY including calendar (stronger than the ITER36
re-type which kept 59 extra warmup rows - none here). This also proves the D17-patched panel
(manifest.csv skipped) content-equals the original 298-CSV panel (committed CSV emitted 2026-09-07,
pre-manifest). Provenance of committed bytes: CSV mtime 2026-09-07 10:59 = the CAMP_COST R2 costfix
re-emission vintage; .meta mtime Sep-2 = original acceptance meta (params WIN=200 BAND=0.03 FRAC=1/3,
SR=0.89 H1=0.99 H2=0.80 negYr=1); the on-disk QA script documents the costfix re-emission and A1
proves current text = current bytes.

## STRUCTURAL DISCLOSURES (all pre-run)
1. Stream trim semantics: strategy_ret trims at first nz>0 (= first month-end with >=10 valid sig
   names AND gate on), vol-targets on the active period (first ~59 rows scale 0), drops 5 warmup
   rows -> committed head 2007-10-08 = 0.0 reproduced exactly by the re-type.
2. Coverage-law expectation: ALL five cells are expected to share the IDENTICAL stream calendar
   (first eligible MES 2007-09-28 with gate ON for every band <= 0.05 per the 2003-07 bull history -
   A1 proves band=0.03; the driver asserts s.index.equals(anchor_idx) and equal notna counts per
   cell, FAIL-CLOSED). If a cell calendar moves, the run stops BEFORE any verdict and any repair
   follows the ITER30-A2 pre-verdict amendment pattern with full disclosure.
3. Band-independent precomputation (px/rets/MES/sig/FF market/MA200) cached once - numerically
   identical to the QA script's module-level order; per-band ops are gate + W loop + T+1 + trim.
4. Import safety: the QA script is NEVER imported (module-level save_sleeve would rewrite live
   sleeve bytes); A3 engine loaded by explicit spec from its file path (no sys.path luck).
5. D17: driver pre-patches harness panel() (skip twelve_big/manifest.csv) at runtime - byte-faithful
   per A1; repo fix remains approval-gated.

Driver: driver_iter38.py derived from driver_iter37.py by deterministic asserted-exactly-once
substitutions (maker persisted as make_driver_iter38.py); frozen pool blocks fit_relw / apply_cap /
project_wmax / build_book ast-text-identity-checked vs driver_iter36.py AND driver_iter37.py at run
start; precommit sha asserted at run start; log to driver_iter38.log.
