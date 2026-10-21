# BLOTTER_TESTER — adversarial testing of the trade-record (blotter) infrastructure (iter 6)

USER REQUIREMENT (verbatim): "the backtesting must be super rigorous. We need all backtesting have
trading record which has instrument name, transaction price, timestamp etc. we must use multiple
agents to do testing work. any bug should be found and cleared at first place."

Coordinator has built a FIRST trade-record emitter: campaign/scripts/blotter.py ->
campaign/results/BLOTTER_HONEST14V3_BALANCED.csv (61,194 records). Your job: TEST it adversarially,
find every bug, and report PASS/FAIL per check with EXACT numbers. READ-ONLY except your own dir.

## DELIVERED ARTIFACTS TO TEST
1. campaign/scripts/blotter.py  (emitter; reconstructs champion position path + emits ledger)
2. campaign/results/BLOTTER_HONEST14V3_BALANCED.csv (columns: date, sleeve, instrument, side,
   price, price_source[REAL/SYNTH], qty_notional, weight_from, weight_to, cost_bps)
3. Champion: campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv (614? rows) +
   builder campaign/scripts/honest13_build.py (frozen, --verify-v3 reproduces byte-exact).

## CHECKS (run ALL, exact numbers, verdict)
A) RECONCILIATION: independently re-derive sum(|qty_notional|) per sleeve from the ledger and from
   the position path Sd/gb/sc (rebuild of honest13_build.make + vt). Verify they match and that the
   ledger's total turnover reconciles to the charged cost in the champion (6bps in builder vs the
   6.4bps user requirement — quantify the annualized cost gap between 6.0 and 6.4 on the champion).
B) PNL REPRO: from the ledger + sleeve raw returns, reconstruct the daily blended PnL and confirm
   it equals the committed champion BALANCED series (max|diff|). If it doesn't exactly — FIND WHY.
C) LOOKAHEAD: verify every trade's signals use data <= t-1 (T+1). The ledger BUY/SELL on date t
   must be executable at close t-1 price. Spot any same-day signal leak.
D) PRICE SANITY: scan the `price` column — flag values that are implausible for the instrument
   (e.g. carryv2/GLD synthetic showing ~189,832 which is WRONG; composite FX/FF2 SYNTH indexes).
   Confirm price_source labeling is honest (REAL vs SYNTH). Quantify how many records are REAL.
E) COST & BORROW: confirm the ledger's cost_bps accounting and whether borrow 0.5%/yr on short legs
   appears anywhere in the trade record (it is applied in the PnL in honest13_build but NOT in the
   ledger — recommend adding a borrow_charge column if absent).
F) SPARSE-GAP COST UNDERCHARGE (coordinator's AUDIT FINDING): the builder charges
   full.diff().abs().sum(axis=1) with NaN SKIPPED, so sparse NYSE-only sleeves undercharge re-entry/
   exit across gaps ~4%. Reproduce this exact number (>716.7 charged vs ~746 honest) and STATE it.
G) INSTRUMENT COMPLETENESS: confirm every sleeve has a mapping to a real tradable instrument name.
H) NEW ENGINE compliance: for ANY new engine a hunt agent lands, state the required blotter fields.

## OUTPUT
FINDINGS.md: per-check verdict + exact numbers; a BUG LIST (severity: critical/major/minor) and a
FIX PLAN the coordinator can apply. Last line exactly: BLOTTER_TESTER DONE
