# ITER43_A5R2_VT — FINDINGS_PRECOMMIT (sealed BEFORE any candidate arm ran)

Session 23, 2026-09-19 ~18:2x CST. Operator directive (verbatim): keep improving.
the leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be
smaller than 20 pct. — SAME constraint set as ITER21..42; NO rule change granted,
NO purchased data. Objective function unchanged: max FS SR s.t. lev<=1.6, ann>=20 pct.

## Verify-first (pre-axis)
- Gauntlet 7/7 GREEN via campaign/bt/verify_champion.py r3 invocation (12 sleeves,
  shrink 0.70, brwt-cap 0.30, gear 1.0) -> coord/verify_champion_r3_last_session23.json.
  SR 3.751428690289051 / cagr 23.6054 pct / MDD -3.6130 pct / 0 neg years / gross 1.0.
- Coordinator invocation-typo DISCLOSED: first gauntlet run omitted --gear 1.0 ->
  verifier rebuilt at default gear 1.6 -> 4 checks fail-CLOSED (listed behavior;
  stats block reads champion bytes, checks rebuild). Corrected rerun green. No
  champion anomaly at any point.
- Champion sha16 8559fa55ee9a3417 / weights d2d11c92a98683df verified pre-run.
- Coord quiet since 16:07 (ITER42 closeout); no concurrent writer at seal time.

## THE CELL (19th axis candidate; 18 measured-closed per ledger #133)
A5r2 (A5_r2_contango_rateshock) VT axis. Book relw 5.522 pct (7th of 12; the
largest roster sleeve with NO campaign-swept frozen-scalar axis; carryv2 2.198 pct
is the only roster sleeve after it). Roster scalar program state: brwt zb (I34/35),
C5ng k (I33), a6r7 recipe grid incl VT (I30) + DUR (I32), diescrack L/Z (I36/40),
xasts MAW (I37), dualmom band/win (I38/39) — A5r2 and carryv2 unswept.

Why VT and not W/CHG/LVL/TH/HYST: agent-level coverage exists for those (r2 27-cell
grid W/CHG/LVL; TH/HYST from r1 plateau; mult axis monotone to endpoint 0.0) — but
ZERO coverage at ANY level for VT. Per-sleeve VT is an established campaign axis
class (ITER30 swept VT inside a6r7's grid). The agent's Idea-2 note ("vol target is
pure scale — SR invariant at every vt") holds only where the vol scaler never
clips; A5r2's scaler sc = VT/sigma_ann clipped at 2.0 with realized sleeve vol
8.8 pct < 10 pct target puts the anchor IN the clip regime -> VT is a genuine SHAPE
axis here (changes which days sit at the clip), not pure scale. This claim is
measured by the sweep, not assumed.

## GRID (frozen at seal)
VT in (0.06, 0.08, 0.10, 0.12, 0.15). VT=0.10 is the ANCHOR arm: it must reproduce
the committed A5r2 stream byte-exactly (A1a vs in-module import of
campaign/scripts/a5_r2_rate_shock_contango.py maxdev<1e-15; A1b vs committed CSV
campaign/agents/A5_vol_cond/sleeves/A5_r2_contango_rateshock.csv recon dev<1e-12,
full nonnan coverage). Anchor arm is IS-bar-INELIGIBLE by construction (it IS the
incumbent); its role is continuity only. ALL other generator bytes frozen:
TH=1.02 HYST=0.05 W=150 CHG=0.25 LVL=2.75 clip=2.0 min_periods=60 T+1 D.COST(harness)=6.0bps.

## HARNESS (frozen; text-identity enforced)
fit_relw / apply_cap / project_wmax / build_book AST-extracted and asserted
text-identical to driver_iter41.py AND driver_iter36.py. House rule: minsharpe,
shrink 0.70, brwt-cap 0.30 (B.BRWT_BLOCK = brwt10/7/5), Wmax wall 2.0x(k), IS end
2017-01-01, fit rows asserted 1809, k_covered asserted 11 (CFX4 zero-cov in IS),
gear 1.0, B.BPS 6.4 book layer. Swap convention: candidate stream replaces
df12[A5r2]; fit re-solves the 12-roster weights per arm (ITER42 convention).
D17 runtime pre-patch: harness data.panel wrapped to skip twelve_big/manifest.csv
BEFORE importing the a5 module (its import executes D.closes()); panel dict
otherwise identical -> byte-faithful (A1b is the end-to-end proof).

## ADMISSION (per non-anchor arm; all must hold)
is_sr > BAR 4.198632 (incumbent IS-SR continuity) AND is_mdd >= -0.06 AND
IS neg-years = 0 AND Wmax_sf <= 2.0x + 1e-9.

## REVEAL + OPERATOR GATES (single reveal of the IS-argmax admitted arm; none if no arm admitted)
G1 ann >= 20 pct PERCENT form: (cagr_pct >= 20.0) or (arith_pct >= 20.0)  [D18-fixed]
G2 capital-real gross <= 1.6 + 1e-9   G3 FS MDD >= -7 pct   G4 0 FS neg years
G5 CFX4 weight = 0   G6 Wmax_sf <= 2.0x
G7 OOS police: >=4/5 bins positive dSR vs champion AND min bin >= -0.10 AND
   FS SR > 3.751429. Bins: 2017-18 / 2019-20 / 2021-22 / 2023-24 / 2025-26.
G8 fit-window shrink <= 2 pct (rows 1809).

## STOP RULE (sealed)
ONE reveal, no second reveal, no re-fit-after-peek. If no non-anchor arm is
IS-admitted -> HONEST NEGATIVE, family closed, axis 19 measured-closed. Champion
byte-stability asserted pre/post driver run (sha16 8559fa55ee9a3417 /
d2d11c92a98683df). Any post-seal change = numbered Amendment re-sealed and
disclosed BEFORE the driver runs.

## SANDBOX profile (expected)
Write/Edit on repo denied; python3 heredoc writes are the path (driver split into
2 chunked writes, w-then-append, ~13KB parser limit); py_compile gate before run;
single-op shell commands; bash exec gated (python3 directly).

## Sealed
sha16 of this file at seal time: recorded in driver_iter43.py header assert.


## AMENDMENT 1 (sealed BEFORE the corrected re-run; no reveal has executed)
Run-1: NameError at def-time (frozen project_wmax default arg binds module-level
BRWT_BLOCK; line omitted from constants). Pre-computation, driver defect, fixed.
Run-2: full sweep ran; A1a anchor-vs-module maxdev=0.0, A1b committed-CSV recon
maxdev=9.975e-17 (regen fidelity proven) — then A2 FAIL-CLOSED at weights
maxdev=9.913e-09 / bytes maxdev=5.849e-10 (bar 1e-12). ROOT CAUSE: input-convention
asymmetry — the anchor arm fitted the REGEN stream, which differs from the
committed CSV parse by ~1e-16 (A1b), and SLSQP's landing point amplifies a 1e-16
covariance perturbation to ~1e-8 in weights. Every frozen-template driver (36/41/42)
ran A2 continuity on the COMMITTED incumbent frame; routing A2 through the regen
was a coordinator deviation from template, not a harness or champion defect.
REPAIR (toward template, no grid/gate/stop-rule change): A2 continuity re-runs on
the committed frame (B.load bytes, iter42-identical inputs; bar stays 1e-12);
candidate arms keep regen inputs (uniform footing for all novel cells); the
regen-vs-committed fit-landing delta is LOGGED as the measured jitter bound on
arm IS-SR comparisons, and admission margins are read against it. Observed at
run-2: jitter <= ~1e-6 IS-SR; arm margins over bar 2.5e-3..5.1e-3 (5-25x jitter).
Grid results seen at run-2 (IS level only, no FS reveal): monotone rising
4.188280 / 4.194835 / [4.198632] / 4.201156 / 4.203733; Wmax_sf 1.72-1.86x <= 2.0;
rows 1809 k 11 all arms; projection identity 0.0 all arms. Single-reveal budget
UNSPENT. Champion untouched (sha asserted both runs).


