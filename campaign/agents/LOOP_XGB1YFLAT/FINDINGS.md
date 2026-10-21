# FINDING: XGB1y is a MONTHLY-rebalance book FLATTENED to a constant DAILY return — inflates champion SR

Date: 2026-09-02 (in-loop real-time audit, /loop goal100)
Status: **CONFIRMED, MATERIAL** — bug identified live; not cleared by prior audits (they verified
byte-reproduction of the CSV, not semantic validity of the daily series).

## The bug
`campaign/results/sleeve_library/XGB1y_deploy.csv` (committed, in the STRICTTRADE champion pool)
is a **monthly-rebalance 20-name equity L/S book whose monthly PnL was ARTIFICIALLY FLATTENED
into a constant daily value** within each month (meta: "spread to daily").

Mechanical evidence (XGB1y_deploy.csv):
- Only **211 distinct return values across 4684 daily rows** (4.5% of days are unique).
- **Lag-1 autocorrelation = 0.951** (a real daily series of held equity positions has ac1≈0).
- Sample: every trading day of Jan-2023 = +21.1 bps; Feb-2023 = +35.8 bps (constant, no
  intra-month P&L path).
- Following the monthly PnL on a fair intra-month path (allocated by same-month SPX daily path)
  gives **ac1=-0.116 and honest daily SR≈0.06** vs the flattened 4.32.

A genuinely daily hold of a 20-name L/S book moves with the market every day; it does NOT earn a
constant daily rate. Flattening erases all intra-month volatility, so:
1. **Inflates the sleeve's daily Sharpe** (smaller denominator, same numerator).
2. **Understates the sleeve's true intra-month MaxDD contribution** at the portfolio level.

## Impact on the COMMITTED STRICTTRADE champion (exact rebuild of 4522-row construction)
Run with rebuild_exact.py recipe (per-sleeve vt10 cap8 -> EW -> global vt -> 126d DD-throttle ->
instrument costs + borrow fees -> NYSE calendar):

| Variant | ann | SR(d) | MaxDD | OOS17+ |
|---|---|---|---|---|
| As committed (XGB flat) | 49.36% | **5.241** | -6.05% | 55.9% |
| XGB dropped (11 sleeves) | 39.58% | 4.223 | -4.85% | 44.1% |
| XGB fairly reconstructed | 45.71% | **2.233** | -4.96% | 49.6% |

**Headline: the honest blended daily Sharpe is ~2.2 (or 4.2 if XGB is simply removed), NOT 5.24.**
The flattened-return sleeve is responsible for lifting the blended daily SR from ~2.2 to 5.24.

## Implication for the /loop goal (Ann>=80%, SR>=5, MaxDD<=7%)
- The **SR>=5 target is NOT met** by the current champion under honest handling of XGB1y
  (best defensible SR ≈ 4.2 with XGB removed; ≈2.2 with XGB fairly reconstructed).
- Ann return target is far from 80% either way (40-46% honest).
- The prior "0/19 neg years" and OOS positivity survive, and MaxDD stays within 7%, but the
  headline SR was inflated by a data-shaping artifact.

## Required fix (do not hand-wave)
1. XGB1y must be re-emitted as a **faithful daily P&L series** (re-run the monthly book at daily
   granularity from actual holdings, or drop it). The flattened CSV is NOT a valid sleeve.
2. Recompute the champion with the corrected daily series (or the 11-sleeve pool) and re-report
   honest SR/ann/DD/OOS.
3. All prior "SR 5.2-5.6" headlines across the campaign should be re-audited for the same
   flattening flaw (any sleeve with multi-day constant returns). Check whole sleeve vault.
