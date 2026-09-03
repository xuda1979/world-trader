# HUNT_OVNIGHT — overnight / gap-fade & intraday seasonality on twelve_big (iter6)

**VERDICT: NO DELIVERY.** No tradeable overnight/gap engine passes the charter gates at
6.4bps/side on the 298-name twelve_big panel. The charter's core premise is REFUTED in its
tradeable form and CONFIRMED in its paper form — with the paper form proven unownable at charter
costs. Full negative ledger + one paper-trap documented below so no future agent re-hunts it.

## 1. Data premise lint (charter-write-time requirement) — PASS
- 298 files in tools/quant/data/twelve_big, 1,358,122 rows total, columns exactly
  `date,open,high,low,close,vol` in 298/298 files (0 bad-column files).
- 0 NaN opens; 0 nonpositive OHLC cells. Earliest start 2006-09-20, latest end 2026-08-12
  (294/298 end 2026-08-12).
- Start-year counts: 237 in 2006, 61 spread 2007-2023 (IPOs/coverage).
- Decomposition identity `(1+on_t)(1+ic_t) = close_t/close_{t-1}` verified to max abs error
  **4.44e-16** over the whole panel (where open and prior close valid).
- Valid-cell fraction (open_t AND close_{t-1} present): 91.0%; median valid names/day 271
  (274 in 2008+); 244/298 names have >=95% coverage 2008+.
- **BUG FOUND+FIXED (data):** union calendar contained 6 stray rows with <50% name coverage,
  incl. 2009-07-26 (a SUNDAY) where only CVS traded — it manufactured a fake +144.6% overnight
  and a -59.2% next day, polluting the weekday-seasonality stat (Sunday-on mean 14,459bp/day).
  Fix: keep rows with >=50% coverage (drops 6 rows: 2006-09-20/21/22/25, 2009-07-26,
  2024-05-27). After fix weekday overnight drift (2008+, bp/day): Mon +2.69, Tue +5.88,
  Wed +4.46, Thu +1.46, Fri +2.57.

## 2. TDD record (IRON LAW compliance)
- `scratch/tdd_tests.py` written BEFORE `scratch/hunt_lib.py`. **RED observed: 0/8 pass**
  (ModuleNotFoundError ×8, exit=1).
- After implementing hunt_lib: 3/8 pass, 5 fail. Root-caused each failure:
  - 2 failures = MY test expectations wrong (entry 0->1 is a HALF-turn |dw|/2 = 3.2bps, not
    6.4bps; borrow accrues from entry day). Engine matched campaign convention (FF2 lib
    `turn=(p.diff().abs()/2)`). Tests corrected with documented reasoning.
  - 3 failures = REAL bugs in hunt_lib: pandas-4 boolean-DataFrame setitem mis-aligning in
    `xs_ls` (root cause: `R>(N-k)` with N a Series doesn't align to frame columns) — fixed via
    `np.broadcast_to` frame N; `position_lag_p` Series-vs-frame axis error — API contract
    fixed to frames.
- Final: **9/9 pass, exit=0** (incl. `test_two_stream_scramble` added later RED→GREEN).

## 3. Engine slate results (net T+1, 6.4bps/side, borrow 0.5%/yr, 2008+)
Signal IC (rank IC, mean fwd, 2008+, subsampled n=934): overnight-momentum (trailing mean of
overnight return) predicts NEXT overnight with t up to **+5.0** (lb21) — real cross-sectional
predictability. Intraday-momentum predicts next intraday: |t|<=1.3 — nothing. ON predicts next
IC NEGATIVELY (lb10 t=-2.2) — small fade. ONIC-spread predicts next cc: lb21 t=+3.1 — weak.

Charter gate battery (vt10 expanding-60 cap3, poslag 200x) on the naive OVNCAP family
(pos decided at close_t from 63-252d overnight-mean rank; earns `w·on − w·ic`, two-stream
scramble `position_lag_p2`):
| variant | SR 2008+ | H1/H2 | negy | poslag p | corr champ | verdict |
|---|---|---|---|---|---|---|
| lb126 k25 | 2.145 | 3.79/0.96 | 0/19 worst +3.4% | 0.025 | **-0.009** (n=4683) | 7/7 naive |
| lb189 k50 | 2.411 | 4.28/1.08 | 0/19 | 0.045 | -0.007 | 7/7 naive |
| lb252 k50 | 2.444 | 4.24/1.21 | 0/19 | 0.055 FAIL | -0.015 | 6/7 |
| lb252 k25 | 2.158 | 3.70/1.05 | 1/19 | 0.055 FAIL | -0.016 | 6/7 |
Plateau: flat across lb 63..252 (SR 1.63..2.44), all 12 variants |corr|<=0.018.

**WHY THIS IS A PAPER TRAP (self-caught, per verification-before-completion):**
`w·on − w·ic` is NOT a holdable position. Instrument-level audit (sample 2015-06-01 AAPL
w=+0.040): earning `+w·on` requires selling at the next OPEN; also earning `−w·ic` requires
SHORTING the same name from that open to close. That is 2 extra executions/name/day
(≈200% extra turnover ≈ 12.8bp/day) — my first cost model charged only close-position changes
(0.74bp/day actual). Honest costing:
| costing convention (lb126 k25, 2008+) | SR |
|---|---|
| paper (charge |Δw|/2 only) | **2.128 naive / 2.172 vt** |
| single-cost daily round-trip (turn=max(|Δw|/2,|w|)) | **0.725 naive** |
| double-cost RT (both legs rebuilt as separate books) | -0.822 |
| ON leg alone +RT: -0.654 (scratch -0.692), -IC leg +RT: -0.573 (scratch -0.589) | |
| EW-long ON +RT (classic overnight premium): **-0.753** | |
Discrepancy notes (systematic-debugging): scratch "both +RT" -0.855 vs repro -0.822 —
isolated to double-counted borrow; also a repro section-A sign slip (-ic passed where +ic
expected) produced SR 0.008 for one run — both fixed, repro now authoritative, all headline
numbers re-derived from `ovnight_repro.py`.

Also honest: OVNcc (ON signal, close-to-close target, correct costs) lb21..252 k15..50:
SR -0.44..+0.28 — the ON signal carries NO close-to-close edge. Plain cc momentum L/S on this
panel is NEGATIVE at all lookbacks (lb21 k25 SR -0.588). Weekday books (Mon->TueON long SR
+0.11, Fri->MonON -0.42, all-Tue long -0.34): dead. IC momentum/fade: dead (SR -1.59..+0.16).
ONIC-spread -> cc: dead (SR -0.91..+0.14).

## 4. Root cause of the poslag p=0.085..0.100 (first battery run)
My `gate_battery` scramble passed ONLY the ON-leg return matrix (single-stream) — mis-specified
for a two-stream book; the IC leg was ignored. Correct two-stream scramble (`position_lag_p2`,
TDD RED→GREEN) gives p=0.015..0.025 for the chosen variant (3 seeds: 0.025/0.015/0.025,
realSR 2.189). Block-PERMUTATION variant (10d blocks shuffled) is DEGENERATE again
(p=0.000, permSR mean 1.99 ≈ real 2.13) — consistent with FINAL_STATE; NOT used as evidence.
Static-random 25+25 longON/shortIC drift-control, 200 trials: SR mean **-0.033**, p95 0.708,
max 1.249 → real 2.128 is **z=4.49** above signal-free books (repro: mean -0.033 p95 0.708
z=4.47). The signal content is real — it is the EXECUTION that is not.

## 5. Why the tradeable edge cannot clear gates (the honest math)
- Control regression `on_{t+1} ~ on_t + rank(sig)`: t(sig)=+4.0 (n=495 days) — real next-day
  overnight alpha.
- But next-day overnight is only reachable by selling at tomorrow's open: with that + the
  intraday short leg, honest SR is 0.725 best-case (single-cost RT) / -0.82 conservative —
  **FAILS charter SR>=0.6** in the conservative case and fails robustness in the best case:
  regime split (gross): 2008-12 SR 4.31 → 2013-19 2.26 → 2020+ 0.95; 12m rolling SR min -0.57,
  p10 0.31; OOS17+ geo +13.4% ann (SR 1.02 on paper path).
- Weekly-rebalance variant (turnover 11.7bp/day, kills the open-exit burden): SR 2.145 paper —
  still the same paper trap. With LUNO haircut (paper 9.97bp/day edge vs 5.44bp/day equal-ann
  LUNO): 45% haircut → SR ~0.60 — fails SR>=0.6 gate outright.
- Market-purity: demeaning the book by equal-wt market ON (beta from 252d) leaves gross SR
  1.401 (vs 2.241 raw) — mostly cross-sectional, not beta, but still unownable per above.
- The classic EW-long overnight premium on this panel: +1.62bp/day gross with hold-only costs
  (SR 0.225), SR **-0.753** with honest daily RT costs — confirms the cost wall.
- Cost sensitivity of the PAPER book (for the record): 6.4bps→SR 2.128, 10→2.078, 15→2.008,
  25→1.868 (tiny, because paper costs are only 0.74bp/day — that's the tell).

## 6. Instrument / price-path / trade-record note (TRADE_RECORD_STANDARD.md)
- No sleeve delivered → no sleeve CSV. Had one passed: instrument = US large-cap equity
  (twelve_big 298 names), price path = `tools/quant/data/twelve_big/{NAME}.csv` columns
  open/close, price_source=**REAL** (unadjusted vendor OHLC; note: splits not adjusted in
  open-vs-prior-close gaps >10% count = 12 days panel-wide, all flagged in §1 lint).
- Engine files kept: `ovnight_repro.py` (canonical, byte-regenerates every number in this
  file), `scratch/hunt_lib.py` + `scratch/tdd_tests.py` (9/9), explorers in `scratch/`.

## 7. Gate cards (chosen naive variant, for the record — NOT delivered)
OVNCAP126k25 (vt10 cap3, 2008+, n=4683): SR 2.145 | H1 3.79 H2 0.96 | negy 0/19 worst +3.4% |
poslag2_p 0.025 (seeds 0.025/0.015/0.025) | corr -0.0086 full / +0.0021 (2017+) |
ac1 -0.019 | uniqR 1.000 | extra-lag probes 0/1/2/5d: 2.032/2.057/1.976/1.860 (no same-day
leak) | LOYO SR range 1.866..2.329 (min -2009) | scrub10 2.392 | cost 25bps 1.868 |
VIX-high SR 1.38 vs VIX-low 2.40.
**Every one of these is on the PAPER path. Honest-cost SR 0.725 / -0.822 → charter FAIL.**

## 8. Process integrity
- Charter-scramble wording ("200x 10d-block POSITION-LAG scramble") is ambiguous; implemented
  BOTH ways: 10d-block-lag p=0.040, any-lag p=0.015 on the paper book. Gate outcome (FAIL via
  honest costing) does not depend on this choice.
- 2 self-caught engineering bugs (data calendar, scramble spec) + 2 self-caught accounting bugs
  (repro sign slip, double-borrow) — all root-caused, documented, fixed, and re-verified.
- Reproducer fresh-run output matches every number quoted here (verification-before-completion).

## 9. Recommendation to DEAD_IDEAS ledger
`overnight/intraday decomposition harvesting (twelve_big),dead,"ON-mom t+5.0 next-day-ON real but unownable at 6.4bps; honest RT SR 0.725/-0.82 vs paper 2.13; cc books SR<=0.28; weekday/IC/ONIC dead",HUNT_OVNIGHT`
