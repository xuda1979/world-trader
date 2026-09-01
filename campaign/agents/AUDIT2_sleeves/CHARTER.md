# AUDIT2_sleeves — forensic audit of the 10 inherited champion sleeves (read-only)

The champion pool (champion_build.py POOL) contains sleeves inherited from prior sessions.
Your job: for EACH, either verify from raw data or FAIL it.

Sleeves to audit: H21_f5, H21_br, XGB1y (ML books), A5r7, A5r2, A5r4 (VIX-contango),
a6r7 (bond2y), A1inf, QAxasts, dualmom, carryv2, A1credit (panel/macro books).
Repro scripts live in campaign/scripts/ and agent dirs — RUN THEM where they exist and
compare output to the committed CSV (report corr/max-diff/identical).

CRITICAL: explain the long interior ZERO-RUNS found by the coordinator:
  A5r7: 367d, a6r7: 461d, A5r2/A5r4: 112d, XGB1y: 105d, dualmom: 250d, C5ngsum: 111d, brwt: 33d.
  For each: flat-by-design (band gates, long-flat books, hysteresis) or MISSING DATA?
  Read the sleeve's construction code and find the exact mechanism; verify the zero-run
  dates against the gate conditions. A zero-run that is NOT explained by the strategy's
  design = FAIL the sleeve.

Also check each sleeve's T+1 discipline: find the shift(1) (or shift(-1) returns) in its
code; a sleeve whose signal enters PnL on the same day it was computed = FAIL.

Write campaign/agents/AUDIT2_sleeves/FINDINGS.md: per-sleeve verdict table with evidence.
Last line: AUDIT2 DONE
