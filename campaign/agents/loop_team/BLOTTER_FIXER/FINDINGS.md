# BLOTTER_FIXER — FINDINGS (iter 6.5, 2026-09-03)

Agent: BLOTTER_FIXER (ledger/emitter fixes per BLOTTER_TESTER FIX PLAN). Method: SUPERPOWERS RIGOR
TDD (RED first), verification-before-completion (all numbers re-run fresh in this session),
systematic-debugging (root causes below).

## DELIVERABLES
- `campaign/scripts/blotter_v2.py` — NEW per-book, cost-complete, honest-price emitter
  (`python3 campaign/scripts/blotter_v2.py [--verify]`), importable/re-runnable.
- `campaign/results/BLOTTER_HONEST14V3_SAFE.csv` (239,440 rows), `_AGGRESSIVE.csv` (239,502),
  `_BALANCED.csv` (239,505) — v2 per-book ledgers. The v1 `BLOTTER_HONEST14V3_BALANCED.csv`
  (61,194 records) was superseded (backup of the v1 artifact at
  `campaign/agents/loop_team/BLOTTER_FIXER/scratch/V1_BLOTTER_HONEST14V3_BALANCED.backup.csv`).
- TDD suite: `campaign/agents/loop_team/BLOTTER_FIXER/scratch/test_blotter_v2.py` — 18 tests.
- `campaign/TRADE_RECORD_STANDARD.md` — appended V2 LEDGER STANDARD (columns + gates).

## FROZEN-FILE INTEGRITY (hard constraint #1) — VERIFIED
sha256 before == after the whole session:
- `campaign/scripts/honest13_build.py` = bca89d0ee8e2c699850e951c97eca3c8cc7bb3107ba6dd8bbe0f8562b5143734
- `GOAL100_HONEST14V3_BALANCED_daily.csv` = fdbca6552b9a2e9e89cfba13b06eb5b0d61cc196b410d3cae2ba4d6149a907cb
- `GOAL100_HONEST14V3_SAFE_daily.csv` = eb1bb91be4e68bfc2a56c2fd4092611737db76f0e52b357b1d4a29fe8f53c82f
- `GOAL100_HONEST14V3_AGGRESSIVE_daily.csv` = a16c6b7c6dd5727f55bbd7fff678c042a568242304f8196f5ba973add4d5a13b

## TDD RED→GREEN TRACES (per bug)

RED state (fresh, before implementation): `pytest test_blotter_v2.py` →
**"1 failed, 1 passed, 14 errors"** — 14 tests errored on `ModuleNotFoundError: No module named
'blotter_v2'` + `test_t7_turnover_byte_identical_to_v1_on_aggr_rows` FAILED (no AGGRESSIVE ledger).
The only passing test was the frozen-file guard (which must pass at all times).
GREEN state (final): **"18 passed in 9.45s"**.

| Bug | RED evidence (observed) | GREEN evidence (observed, fresh run) |
|---|---|---|
| #1 CRITICAL per-book ledgers | v1: single AGG-only ledger covers 119.30% of BALANCED charged turnover (716.70x vs 600.78x — reproduced in revert probe); no `book` col, no SAFE/AGGRESSIVE files (tests errored) | `BLOTTER_HONEST14V3_SAFE.csv` reb turnover **484.8517x** == own book path; `_AGGRESSIVE.csv` **716.6999x** == own path; BAL implied **600.7758x** == Tester's 600.7758x; per-sleeve reconcile **EXACT** both books; BAL == (SAFE+AGG)/2 per record-pair, max diff **0.0** (239,437 pairs) |
| #6 MAJOR borrow + cost_total | v1 columns: none of book/borrow_charge/cost_total (probe: "NONE"); ledger covered only 45.87% NAV of charged cost | borrow rows 43,056/book; borrow Σ **6.391% NAV SAFE / 6.307% AGG** (0.3164%/0.3122% per yr) matches Tester's 6.349%/0.3146% (books differ); overlay_vt rows 5,084/book, throttle 4/66 (SAFE/AGG); **ledger Σcost_total == charged: SAFE 0.531441923081 == 0.531441923081; AGG 0.679014828979 == 0.679014828979** (exact); ledger-alone PnL vs champion **1.0e-16/1.1e-16/1.1e-16** |
| #4 MAJOR honest price maps | v1: carryv2 0 REAL rows (synth 96.47–752.76 "GLD"); a6r7/QAxasts "TREASURY FUT" labeled yields; brwt "FUT SPREAD" priced at Brent leg silently | carryv2 **4,567 REAL rows, px 711.80–5330.95 (xau.csv gold spot)** + 247 SYNTH; instrument strings: "US 2Y/10Y TREASURY YIELD (%, not futures price; DGS2/DGS10)", "BRENT/WTI FUT SPREAD — priced at Brent spot leg", "XAU GOLD SPOT (carryv2)"; REAL yield ranges 0.09–5.19 (DGS2) / 0.52–5.26 (DGS10) |
| #7 MINOR t−1 exec price | v1 stamps t close (Tester: mean 72.27bps vs t−1 on A5r2) | v2 = last print STRICTLY before day t: max|price − t−1 close| = **5.0e-7** (rounding at 6dp) on 4,039 A5r2 REAL rows; v2-vs-t mean gap **72.32bps** (≈ Tester's 72.27 — same convention shift); AGG trade-row qty/weights byte-equal v1 (test asserts <1e-12; PASS, 61,194 rows) |
| #8 MINOR holiday flag | v1 has no flag; 140 holiday trade records (96 dates) unflagged | `holiday_trade` on every row; trade-row census **140 records / 96 dates** (CFX4 71, FF2 39, diescrack 30 — exactly v1); full-ledger flag correctness test PASS (1,596 flagged rows incl. cost rows) |

### RED→GREEN regression proof (revert probes, run in-session)
Reverting to v1 behavior on the BALANCED book reproduces every bug: AGG-only turnover 716.70x vs
600.78x charged (119.30%); t-close convention mean gap 72.27bps; zero v1 columns for
book/borrow_charge/cost_total/holiday_trade; carryv2 REAL = 0 (v2: 4,567).

## ROOT CAUSES FOUND & FIXED DURING IMPLEMENTATION (systematic-debugging)
1. **Marks gross missing `sc`** — ledger-alone PnL initially off by exactly the throttle factor
   (worst day 2024-01-12: marks gross 0.04288457 == 2 × builder 0.02144229). Root cause: builder
   gross is `b*sc` where `b = vt(blend_of_Vnet)`; my mark line applied gb to V_net but omitted
   `.mul(sc)`. One-line fix → PnL diff 2.1e-2 → **1.1e-16**. (Also verified the transform-order
   asymmetry `vt(ΣW·V) ≠ ΣW·vt(V)` is real: max|b1−b2| = 0.0125, throttle triggers 143 vs 668 —
   so marks MUST sit on the V_net decomposition, not per-sleeve gb.)
2. **Cost rows leaked outside the charged window** — ledger total initially 0.5711 vs charged
   0.5314 (SAFE): `tw` has values from 1990 while the builder charges `tw.reindex(champion index)`
   only; uncharged excess 0.0397. Fix: restrict overlay_vt/throttle/borrow rows to the champion
   index (charged window). → ledger total == charged exactly.
3. **Closure bug in BlotterState** — charged-cost recompute used stale loop var `sf` (brwt5's 0.5)
   for every sleeve, mis-pricing carryv2 (0.3→0.5), QAxasts (0.4→0.5), dualmom. Fixed to
   `SHORTF[n]`; charged == ledger to the last bit.
4. **BAL pairwise-mean NaN handling** — BALANCED file round-trip failed at max|diff| **7.5e-5**
   (caught by the new gate): on SAFE-only throttle dates (2011-01-25/26, 2024-01-12) the
   NaN-keeping mean kept the full SAFE value instead of (SAFE+0)/2. Fix: both-denominators mean
   (missing book = 0). → BAL round-trip **7.3e-16**.

## RECONCILIATION GATE (evidence-only; all from THIS session's runs)
- Per-book per-sleeve: Σ|qty_notional| (trade rows) == own book `full.diff().abs()` turnover —
  **EXACT** (both books; tolerance 1e-8 rel, achieved ~1e-13 abs).
- Ledger cost completeness: Σcost_total == charged reb*6e-4 + (tw+dsc)*6e-4 + htb/252 —
  **exact to printed precision** (SAFE 0.531441923081; AGG 0.679014828979).
- Ledger-alone PnL == champion: **SAFE 1.023e-16, AGGRESSIVE 1.110e-16, BALANCED 1.110e-16**.
- Round-trip FROM THE EMITTED FILES ALONE (groupby date, Σpnl_contrib − Σcost_total vs champion):
  **6.783e-16 / 7.399e-16 / 7.321e-16** — the v2 standard's admissibility gate.
- Byte-reproducibility (`blotter_v2.py --verify`): SAFE/AGGRESSIVE/BALANCED **EXACT**.
- Finiteness: 0 inf, 0 NaN prices across 61,194×3 trade rows (Tester bug #2 guard).

## HONEST DISCLOSURES / RESIDUAL GAPS
1. **`cost_bps=6.4` label vs 6.0 charged**: `cost_total` now carries the ACTUALLY CHARGED 6.0bps
   value (no PnL misstatement possible); the `cost_bps` column keeps the 6.4 standard-minimum
   label, with `CHARGED_BPS=6.0` in code and the standard updated. The 6.0→6.4 re-price (+11.91bps/yr)
   is a builder re-audit decision (Tester #5), out of my charter.
2. **Sparse-gap skipna undercharge (Tester #3)** is in `honest13_build` — the ledger reproduces the
   (under)charged number exactly by design; not fixable in the record.
3. **t−1 fallback side-effect**: strict t−1 lookup demotes 79–104 rows/sleeve from REAL to SYNTH
   when the prior trading day has no print (e.g. first trade after a gap). These are honestly
   labeled SYNTH (v1 silently stamped the t print REAL, which was the actual defect).
4. **BAL side column**: on 341/61,194 trade-pairs SAFE and AGG disagree on side; BAL keeps SAFE's
   side (|qty| is the pairwise mean; sign of a mean of |deltas| is not recoverable). Disclosed.
5. **carryv2 SYNTH 247 rows** (pre-xau era 2006-12-29→2007-12-20 + print-gap days) remain SYNTH
   index (98.9–116.4) — xau.csv starts 2007-12-21; no gold series on disk before that.

## RECOMMENDATION
Ledger v2 IS champion-admissible per the v2 standard (all gates pass, ~1e-16, byte-reproducible,
frozen champion untouched): it is a complete, honest trade record of the champion AS-CHARGED. It
must be paired with the separate builder-cost re-audit wave (6.0→6.4bps, gap-convention,
Tester #3/#5) before any re-pricing of the champion PnL itself.

BLOTTER_FIXER DONE
