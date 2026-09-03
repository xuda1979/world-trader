# AUDIT_FRAMEWORK — adversarial audit of the new campaign/bt backtest framework (track A completeness)
READ-ONLY except this dir. Goal: find bugs and gap in the reusable backtest framework before it is
trusted by hunts. Use superpowers systematic-debugging (root cause) + TDD where you add a test.

SCOPE: campaign/bt/{engine,metrics,gates,reconcile}.py + tests/. Verify:
1. bt.engine.vol_target_scale: NO lookahead (scale at row t uses returns r[0..t-1] only) — write a
   perturbation test; confirm the .shift(1) + expanding window semantics are right. Confirm floor=0.2/
   cap=3.0 bounds and that for a constant-vol series scale -> target/vol.
2. bt.engine.cap_leverage: exact day-level gross cap <= max_lev (incl. floating-point overshoot guard);
   kappa uses gross at the SAME day (not shifted) — check this is the intended convention and document.
3. bt.engine.cost_turnover: half-turn |dw|*0.5 x bps — reconcile to the campaign's 6.4bps one-side
   (TRADE_RECORD_STANDARD: qty=|dw| per record; one-side cost = |dw|*bps? or 0.5? VERIFY which the
   committed champion uses and flag any mismatch with the framework).
4. bt.engine.margin_cost: margin on (gross-1)+ only; confirm at gross<=1 it is 0.
5. bt.metrics: ann_geo/max_dd/neg_years correct on known inputs; sharpe guards near-zero-vol.
6. bt.gates: position_lag_scramble correctness vs a known-good reference; uniq_ratio/ac1/zruns right.
7. Correctness of the campaign/bt __init__/public API and any pandas-3.0 gotchas.
For EACH module write tiny adversarial tests that push edge cases (empty series, single row, all-zero,
NaNs, constant, extreme values). Report: per-module verdict (PASS/FAIL), any BUGS found with root
cause + a regression test you added (in your dir), and what's missing for the framework to be the
single trusted engine for all hunts (recommendations). Wrote only in this dir + a note in
campaign/bt/README.md if you add one (append). Last line exactly: AUDIT_FRAMEWORK DONE
