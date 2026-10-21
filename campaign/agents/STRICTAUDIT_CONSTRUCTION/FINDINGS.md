# STRICTAUDIT_CONSTRUCTION — adversarial rebuild of the 12-sleeve STRICTTRADE blend

Agent: STRICTAUDIT_CONSTRUCTION | Date: 2026-09-02 | Read-only.
NOTE (coordinator transcript): the STRICTAUDIT_CONSTRUCTION claude process completed its full
rebuild work (all output artifacts on disk, see scratch/) but then STALLED (idle >45 min in
sleeping state) before writing this file. The coordinator finalized this report from the agent's
on-disk artifacts (scratch/rebuild_exact.py -> A/B/BAL_exact.csv), independently re-verified the
byte-exact match twice (corr=1.0000000000, maxdiff=0.000e+00), and reconciled against the
independent corroboration of STRICTAUDIT_SLEEVES (same recipe -> 4522/4522, max|d|=9.996e-17).
All numbers below were recomputed by the coordinator from the agent's outputs.

TARGET: campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv (12-sleeve, 49.4% ann, SR 5.24).

## 0. HEADLINE VERDICT
**The committed STRICTTRADE CSV IS byte-for-byte reproducible** from the 12 committed sleeve files
through the recovered construction recipe (per-sleeve vt10 cap8 -> EW -> global vt -> 126d
DD-throttle -> instrument costs + borrow fees -> NYSE-calendar with holiday-PnL summed into the
next trade day). Rebuilt BALANCED matches the committed file on all 4522 rows with max|daily
diff| = 0.0 (corr 1.0). **BUT the recipe itself is NOT committed anywhere in git** — it exists only
in a prior session log (recovered here) — so the artifact is NOT FROZEN under the campaign's own
provenance standard, and the documented champion_build.py (16-pool, no borrow layer) does NOT and
CANNOT produce this file.

## 1. THE RECOVERED RECIPE (scratch/rebuild_exact.py)
- Pool: exactly the 12 STRICTAUDIT.json files (brwt15/10/7/5 [E1 brwt15_2000 + COORD brwt10_2000/7/5],
  C5ng, C5ngsum [E1 weekday_prem + summer_weekday], A5r2, a6r7 [1990], QAxasts [2006], carryv2
  [GLD_2006], dualmom [band121], XGB1y [deploy]). A5r7/A1credit/A5r4/H21/MHX/B3 absent (confirmed).
- Calendar: USFederalHolidayCalendar (NYSE); each sleeve's weekend/holiday rows remove, their
  return SUMMED into the next NYSE trade day (accumulate, not drop).
- Per sleeve: vt10 = 0.10 / rolling-60d-vol.shift(1), clipped cap 8; NaN->0.
- Turnover-accounting weights W = S/sum(S); EW blend of vt-normalized sleeves.
- Instrument execution layer: EXEC bps {brwt*:1.5, C5ng/5, C5ngsum/5, A5r2/6, a6r7/5, QAxasts/8,
  carryv2/8, dualmom/15, XGB1y/15} charged on |dW| changes (INCREMENTAL above the 6bps already
  embedded in each sleeve CSV; not double-charging — see EXECUTION agent).
- Borrow-fee layer: SHORTF shares per sleeve (dualmom/XGB1y/QAxasts/carryv2/C5ng/C5ngsum/brwt ~0.3-0.5,
  A5r2/a6r7 0), charged (0.5% generic + 20% of XGB1y/dualmom shorts at 3%)/252 per day.
- Global vt + throttle: A=(TGT 0.070, THR 0.04, FR 0.5, LB 126), B=(TGT 0.091, THR 0.03); BAL = (A+B)/2.

## 2. REBUILD MATCH (verified three ways)
| Variant | ann | SRd | MaxDD | negYrs | OOS17+ ann | vs committed |
|---|---|---|---|---|---|---|
| SAFE A | 43.10% | 5.21 | -6.12% | 0/19 | 48.6% | n/a (no A file committed) |
| AGGRESSIVE B | 55.62% | 5.25 | -5.99% | 0/19 | 63.1% | n/a |
| **BALANCED** | **49.36%** | **5.24** | **-6.05%** | **0/19** | **55.9%** | **max|d|=0.0, corr 1.0 (4522 rows)** |

BALANCED reproduces the committed file EXACTLY. A and B are the two configs whose 50/50 average
is BAL — a self-consistent construction.

## 3. NO-LOOKAHEAD in the recovered recipe (code audit)
- Per-sleeve vt uses rolling().std().shift(1) — trailing only.
- Throttle trigger uses trailing 126d rolling-max of equity .shift(1) — no same-day action.
- Sleeve PnL uses shift(-1) returns / shift(1) weights (T+1), consistent with each sleeve's code
  (verified). No lookahead found in the construction.

## 4. HIDDEN-LEVERAGE / financing (charter job 4)
- Implied gross exposure of the rebuilt blend (sum |per-sleeve vt scale|/12, post-throttle):
  mean ~2.0x, p95 ~3.1x, max ~4.0x — same order as the memo's disclosed 1.43x-2.17x mean /
  ~4.4x max range (agents measured slightly differently; all agree it is >1x = internally
  vol-targeted leverage, never charged). Financing on gross>1x at T+25bp is NOT in this series;
  charging it (per EXECUTION agent's daily-accrual approximation) takes ann 49.4% -> ~43.8%,
  DD -6.05% -> -8.8%. "No leverage" holds only in normalized-accounting weights, not capital.
- The 4-brwt + 2-natgas + (A5r2&dualmom high-corr) grouping means the "12 sleeves" are ~8
  economically independent engines (see SLEEVES agent for full correlation matrix).

## 5. COST LAYER (charter job 5 — double-charge check)
- Rebuild matches the COMMITTED file when the incremental instrument-cost layer (1.5-15bp) is
  applied ON TOP of the sleeves' own embedded net-of-6bps returns. Removing that layer raises
  the reconstruction's ann to ~61.8% (coordinator's no-cost recon, matching EXECUTION's ~57-61%)
  vs committed 49.36% -> the committed file embeds ~12.4pp/yr of execution+borrow drag. The 6bps
  is NOT double-counted: the incremental layer is on weight turnover only)Skip, and A5r2 etc. pay
  their instrument bps as increments. Direction is conservative (A5r2 effectively ~12bps total).

## 6. WHAT THIS MEANS FOR THE AUDIT
- POSITIVE: the committed file is EXACTLY the product of a coherent, causally-clean construction.
  It is not a fabricated/fudged series — the recovered recipe regenerates it to the last bit.
- ADVERSE: the generator is not part of the repo. Only the 12 input sleeves + the CSV + JSON were
  committed (28c892b). Under the campaign's own H21/MHX standard ("generator state not in git ->
  removed"), the champion FILE is NOT FROZEN: today's CSV happens to be reproducible, but there is
  no committed, reviewed builder (no --verify) to regenerate it on demand or to audit the cost/
  calendar conventions line-by-line. The FINAL_STATE claim "committed, byte-verified" is therefore
  TRUE for the sleeves, NOT demonstrable for the blend until the recipe is committed.
- The cost/borrow/calendar choices the recovered recipe encodes (NYSE accumulate, exec bps,
  borrow schedule, TGT 0.07/0.091) were never reviewed by a committed gate — they are audit
  BYPASSED convention decisions that a future maintainer could change without a byte-diff.

## 7. RECOMMENDATION (to make "bet today" defensible)
1. Commit the recovered recipe as campaign/scripts/stricttrade_build.py with a --verify mode that
   asserts the 4522-row byte match (and regenerate GOAL100_STRICTTRADE.json without the malformed
   "excluded" string, which currently contains a sentence, not a pool name).
2. Freeze the calendar policy (NYSE accumulate on the 12 sleeve grid) and the cost/borrow table in
   the committed script so the conventions are auditable.
3. Then the 49.4% @ 5.24 @ -6.05% headline is a FROZEN, regenerable artifact; until then it is
   reproducible-but-unfrozen.

STRICTAUDIT_CONSTRUCTION DONE
