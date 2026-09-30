# HUNT_BACKFILL — PRE-REGISTERED PLAN (sealed before any evaluation)

Date: 2026-09-30. Seam: the H1 option-tail backfill gap (H1_report.md §Backfill:
"≥5y daily EOD chains for the 9 symbols (2020-03 and 2024-08 tails must be
in-sample; 3y minimum, 5y+ preferred). Sources to evaluate: CBOE DataShop, ORATS,
ivolatility.com, Polygon."). FINDINGS.md currently classifies backfill as "a
licensed-data decision, not free data" — that claim was never tested against
free sources. This HUNT tests it. If a free source carries the needed history,
the H1 forward sleeve timeline collapses from ~2029 (1 day/day accrual) to
months. If none does, the operator gets a concrete price-tagged decision memo.

## Data requirement (frozen from H1_report + h1_collect.py)

Per symbol-day: strike × expiry grid with bid/ask (or mid), IV, delta;
all expiries ≥7 DTE; full strike range incl. deep OTM (0.8S puts carry the p20
signal); ~30d and ~60d expiry brackets must be resolvable. 9 symbols:
SPY QQQ AAPL MSFT NVDA TSLA IWM GLD TLT. 2020-03 and 2024-08 tails must be
in-sample (H1_report requirement, non-negotiable).

## Stages (pre-registered, NO post-hoc variants)

S1 EXISTING-KEY PROBE: does any env API key already entitle historical options?
    (Polygon key found in env → plan tier identified via live endpoint probes.)
S2 FREE-SOURCE CENSUS: for each candidate free source (DoltHub post-no-preference/
    options option_chain + volatility_history; ThetaData free tier; Polygon free;
    CBOE free delayed_quotes history depth), establish: date span, symbols,
    per-symbol-day row counts, strike-grid moneyness range, expiry brackets,
    update cadence, 2020-03 presence, 2024-08-05 presence.
S3 VERDICT GATES (fail-closed, evaluated on S1+S2 evidence only):
    HIT  = a free source has (a) all 9 symbols, (b) daily or near-daily cadence,
           (c) both required tails present, (d) strike grid reaching deep-OTM
           (≤0.85S puts) with IV, (e) ≥3y span ending within 90d of today.
    NEAR = a free source has ≥5y span and daily cadence but misses ONE of the
           tails or some symbols — worth an operator decision before paying.
    MISS = no free source comes close; write the licensed-price memo instead.

## Probe discipline

Remote SQL console has ~60s query deadline and rate-limits aggressive probing
(observed: curl timeouts on >5 rapid queries). All census numbers below come
from successful queries only; timed-out cells are marked TO and re-probed once
with backoff. No number in the verdict tables is inferred from a failed query.
