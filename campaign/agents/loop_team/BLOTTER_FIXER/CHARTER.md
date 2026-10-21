# BLOTTER_FIXER — implement ledger fixes per BLOTTER_TESTER FIX PLAN (iter 6.5)

CONTEXT: BLOTTER_TESTER (iter6) adversarially audited campaign/scripts/blotter.py and the
delivered BLOTTER_HONEST14V3_BALANCED.csv. It found 9 bugs. Your job: FIX the ledger/emitter bugs
that DO NOT change the committed champion CSVs (those need a separate builder-cost re-audit wave).
Apply SUPERPOWERS RIGOR strictly: TDD (failing test FIRST, watch RED), verification-before-completion
(quote evidence), systematic-debugging (root cause first — already documented by BLOTTER_TESTER).

READ FIRST (all mandatory):
- campaign/agents/loop_team/BLOTTER_TESTER/FINDINGS.md  (the bug list + FIX PLAN, severity-ranked)
- campaign/scripts/blotter.py, campaign/scripts/honest13_build.py, campaign/TRADE_RECORD_STANDARD.md
- campaign/SUPERPOWERS_RIGOR.md

## YOUR SCOPED BUGS TO FIX (from BLOTTER_TESTER's plan — ALL non-champion-changing):
- **#1 (CRITICAL)**: emit PER-BOOK ledgers (SAFE TGT=0.07/THR=0.04 AND AGG TGT=0.091/THR=0.03) each
  with a `book` column; BALANCED = SAFE+AGG record-pairs (book-specific). Remove the hardcoded
  TGT=0.091. Every book's ledger must reconcile to ITS OWN book turnover.
- **#6 (MAJOR)**: add `borrow_charge` column (charged borrow per sleeve per day from
  honest13_build SHORTF + dualmom HTB) and a `cost_total` that includes 6.4bps*qty + borrow.
- **#4 (MAJOR)**: fix price maps — carryv2 -> REAL gold from tools/quant/hedge_fund_strats/data_fred/xau.csv
  (label instrument 'XAU (gold spot)' price_source REAL when xau prints; else SYNTH); relabel a6r7/QAxasts
  as 'US 2Y/10Y TREASURY YIELD (%, not futures price)' or price via futures proxy — chose the honest label;
  relabel brwt* as the true spread; set exec price = t-1 close (do NOT change the position path / PnL —
  the price column is a record, the return still uses the daily return; reconcile to the SAME charged cost).
- **#7 (MINOR)**: price column should reflect t-1 close convention for the claimed PnL day; if you change
  the price reference, the turnover/weight columns and charged cost must remain byte-identical.
- **#8 (MINOR)**: add a `holiday_trade` flag (1 if the trade date is a US federal holiday).

## HARD CONSTRAINTS (do not break these):
1. **DO NOT modify honest13_build.py.** DO NOT re-emit or alter GOAL100_HONEST14V3_*.csv.
2. The position path / charged turnover / PnL must stay EXACTLY as the builder produces it (the ledger
   must keep reconciling to the same charged cost — you are fixing the RECORD, not the model).
3. Champions are the source of truth; your output = clean per-book trade records.

## TDD METHOD (mandatory, per SUPERPOWERS_RIGOR):
1. FIRST write a failing test that asserts the target property (e.g. 'per-book AGG ledger turnover ==
   AGG full.diff().abs()'), watch it FAIL (RED), then implement, then watch PASS (GREEN).
2. For each fixed bug, write the failing test first. Log the RED->GREEN evidence.
3. Reconciliation gate: for EACH book, per-sleeve sum|qty_notional| == that book's charged turnover
   (tol 1e-8 rel); and ledger-based PnL (using cost_total) == the book's PnL after subtracting every
   charged cost stream (tw/dsc/reb/borrow) to <1e-8 daily — verify from the LEDGER ALONE where possible.

## DELIVER (in BLOTTER_FIXER/ only):
- scratch/*.py (repro + tests), a NEW emitter e.g. campaign/scripts/blotter_v2.py that emits
  BLOTTER_HONEST14V3_SAFE.csv, _AGGRESSIVE.csv, _BALANCED.csv (book column, borrow_charge, cost_total,
  holiday_trade, t-1-close exec price, real xau for carryv2).
- FINDINGS.md: per-bug RED->GREEN evidence, reconciliation proof (per-book byte checks), any residual
  gaps disclosed, and a one-line recommendation on whether the ledger v2 is champion-admissible.
- Update campaign/TRADE_RECORD_STANDARD.md ONLY if you add the mandatory columns (append, don't rewrite).
- Last line exactly: BLOTTER_FIXER DONE

## NOTE: your test files and the emitter should be importable/re-runnable. Do NOT touch the 6 running
agents' dirs; do NOT touch honest13_build.py or the results/*.csv champion files.
