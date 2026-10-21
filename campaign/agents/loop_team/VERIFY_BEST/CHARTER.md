# VERIFY_BEST — independent re-verification of the best results (track B, user: "double check if our so far best results are real")

READ-ONLY except this dir. Use the new campaign/bt framework (import campaign/bt.engine, bt.metrics,
bt.reconcile). Apply SUPERPOWERS rigor: evidence before claims, systematic-debugging root-cause.

OBJECTS TO VERIFY (independent rebuild, do NOT trust prior agents' numbers):
1. GOAL100_HONEST14V3_BALANCED_daily.csv (committed V3 champion): ann_geo 43.6%, SR_d 3.92,
   MaxDD -4.92%, 0/19 neg yrs (2008-03-31+), at capital-real GROSS 3.48x (leverage honesty:
   at <=1.6x + 4.5% margin it degenerates ~17-20%). Verify by running
   campaign/scripts/honest13_build.py --verify-v3 (byte-repro) AND an INDEPENDENT rebuild using
   the campaign/bt modules from the raw sleeve files in honest13_build POOL/NEW3. Confirm headline
   metrics with bt.metrics.report. Confirm no same-day leak (extra T+1 lag probe). Re-scan for
   flattening (ac1>0.5, uniqR<0.08) on every sleeve.
2. RAW-EW13@1.6x candidate (results/GOAL100_HONEST_RAWEW13_GEAR16_daily.csv): ann_geo 28.89%,
   SR_d 3.88, MaxDD -4.25%, 0/19 (worst +10.18), exactly 1.6x gross, 4.5% margin + 6.4bps charged.
   Rebuild independently from the 13 sleeve net files (POOL + NEW2 minus FF2) as EW @1.6x, confirm
   metrics match. Confirm leverage never exceeds 1.6 (bt.engine.capital_gross of the geared path).
3. Trade blotters reconcile: (a) per-book ledgers results/BLOTTER_HONEST14V3_{SAFE,AGGRESSIVE,
   BALANCED}.csv (bt.reconcile.ledgers_reproduce: ledger PnL == champion ~1e-16), (b) the
   RAW-EW14 blotter at agents/loop_team/AUDIT_LEVFRONTIER/BLOTTER_RAWEW14_GEAR16.csv.
4. Scramble/degeneracy: re-confirm the RETURN-roll scramble is degenerate (np.roll preserves SR)
   and that position-lag is the valid test (already known; confirm with a quick demo).

REPORT: campaign/agents/loop_team/VERIFY_BEST/FINDINGS.md — per-object verdict (PASS/FAIL) with the
independent numbers and the bt.metrics.report output. Flag ANY discrepancy. If everything passes,
state so with evidence. Wrote only in this dir. Last line exactly: VERIFY_BEST DONE
