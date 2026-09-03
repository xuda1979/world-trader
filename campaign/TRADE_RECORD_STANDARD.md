# GOAL100 TRADE-RECORD (BLOTTER) STANDARD — mandatory for all backtests (iter 6)

USER REQUIREMENT (verbatim): "the backtesting must be super rigorous. We need all backtesting have
trading record which has instrument name, transaction price, timestamp etc."

## Rule: EVERY backtest delivered to the champion MUST be accompanied by a machine-readable,
instrument-level TRADE LEDGER with these REQUIRED columns:

| field | type | meaning |
|---|---|---|
| date | datetime | execution date (T+1 close-of-signal) — also serves as timestamp |
| sleeve | str | engine/sleeve id |
| instrument | str | the REAL tradable instrument name (Brent-WTI spread, Henry Hub NG, SPY, US 2Y, GLD, equity L/S, diesel-crack, FX cross book, FF factor book) |
| side | BUY/SELL | direction of the position change |
| price | float | transaction price at execution (REAL market price when a series exists; else SYNTH index=100 proxy, MUST be labeled) |
| price_source | REAL / SYNTH | honest source tag (REAL = actual instrument price series on disk; SYNTH = block-normalized proxy from the vol-targeted return path) |
| qty_notional | float | |position change| in fraction of NAV (one-side traded notional) |
| weight_from / weight_to | float | position weight before/after the trade |
| cost_bps | float | one-side cost applied (6.4 min) |

## RULE: Reconciliation gate (MUST pass, else the backtest is NOT admissible)
1. per-sleeve sum(|qty_notional|) == the turnover charged in the PnL cost function (within float tol ~1e-8 relative).
2. The ledger's blended PnL reproduces the champion return series byte-for-byte (max|diff| < 1e-12).
3. T+1: every signal uses data <= t-1; execution price is the close of t-1 (no same-day leak).
4. 6.4 bps/side on ALL turnover (incl. vol-target rebalance and throttle switching), borrow 0.5%/yr
   on short legs, IBKR call-rate and not-shortable caveats stated explicitly where not modeled.

## Implementation
- Champion blur: campaign/scripts/blotter.py -> campaign/results/BLOTTER_HONEST14V3_BALANCED.csv
  (61,194 records; per-sleeve turnover EXACTLY reconciles to charged; PnL byte-identical;
  carryv2 price bug FIXED 2026-09-03: synthetic drift, was inf, now sane index <=753).
- Every NEW engine from a hunt agent must state its instrument + the price path used in its
  FINDINGS.md, so the coordinator can append its blotter rows.

## Known audit finding (documented, to be resolved)
- committed honest13_build.py charges rebalance cost as full.diff().abs().sum(axis=1) with NaN
  SKIPPED -> sparse NYSE-only sleeves UNDERCHARGE re-entry/exit across gaps by ~4% of gross
  turnover (716.7 charged vs ~746 honest). Pending: per-sleeve standards (futures held across,
  equity flat across). See BLOTTER_TESTER verdict.

---

## V2 LEDGER STANDARD (iter6.5, BLOTTER_FIXER) — APPEND ONLY

Emitter v2: `campaign/scripts/blotter_v2.py` (byte-reproducible: `--verify`). Per-book ledgers
`BLOTTER_HONEST14V3_{SAFE,AGGRESSIVE,BALANCED}.csv`; BALANCED = pairwise mean of the two books'
records (matching the builder's BAL=(A+B)/2 charging). v2 adds/changes these mandatory fields:

| field | rule |
|---|---|
| book | SAFE / AGGRESSIVE / BALANCED — every record tagged; per-book ledger reconciles to ITS OWN book turnover |
| cost_stream | trade / overlay_vt / throttle / borrow / mark — ALL charged cost streams must have records (ledger must cover 100% of charged cost in BOTH books) |
| cost_total | the cost ACTUALLY CHARGED by this record (trade rows: 6.0bps × qty as charged by frozen honest13_build; overlay_vt/throttle rows: stream × 6.0bps; borrow rows: htb/252). Gate: Σcost_total == charged cost (<1e-8; achieved ~1e-16) |
| borrow_charge | daily short-leg financing per sleeve (SHORTF legs incl. dualmom HTB uplift) on borrow rows |
| pnl_contrib | gross daily PnL attribution per (date,sleeve) on mark rows. Gate (replaces the vacuous builder-internals gate): Σpnl_contrib − Σcost_total per day == champion daily return <1e-8 FROM THE EMITTED FILES ALONE (achieved ~7e-16) |
| holiday_trade | 1 if the record date is a US federal holiday |
| price (v2) | execution price = t−1 close (last print STRICTLY before the claimed PnL day); SYNTH fallback when no prior print exists (labeled SYNTH) |

Cost-label honesty: `cost_bps` on trade rows remains the 6.4 standard-minimum label; `cost_total`
carries the 6.0bps actually charged (gap = 11.91bps/yr, Tester #5) until the builder re-audit wave
re-prices the model. Ledger must NEVER misstate `cost_total`.

Known residual (documented, builder-scope, NOT fixable in the ledger): sparse-gap skipna
undercharge (~4.1% of gross reb turnover; Tester #3) — the v2 ledger reproduces the (under)charged
number exactly by design; fix requires an honest13_build re-emit wave.
