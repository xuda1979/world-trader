# HUNT_BACKFILL — FINDINGS (verdict: MISS on free-tail-sleeve backfill; two free part-credits recorded)

Date: 2026-09-30. Charter: campaign/agents/HUNT_BACKFILL_results/PRECOMMIT.md (sealed
before any evaluation). Question: does any FREE source carry the H1 backfill spec
(≥3y daily EOD chains, 9 symbols, both required tails 2020-03 + 2024-08-05 in-sample,
deep-OTM strike grids with IV), so the H1 forward sleeve timeline can collapse from
~2029 (1 day/day accrual) to months?

## Verdict

**MISS** against the pre-registered HIT gates (all 9 symbols + daily cadence + both
tails + deep-OTM grid + ≥3y span). No free source comes close. The licensed-data
decision memo is now concrete (below). Two free part-credits are recorded, neither
adoption-eligible for the sleeve backfill:

**PART-CREDIT 1 — DoltHub `post-no-preference/options` (FREE, census-complete).**
A genuinely free, live-updated (through 2026-09-28) sampled OPRA EOD dataset.
118,906,740 option_chain rows, 2019-02-09 → present, per-row schema
`date, act_symbol, expiration, strike, call_put, bid, ask, vol (IV), delta, gamma,
theta, vega, rho` — every field the H1 factor needs. BUT the pre-registered gates
fail on four independent counts:
  (a) **Symbol coverage 5/9**: SPY/AAPL/MSFT/NVDA/TSLA present; QQQ/IWM/GLD/TLT
      NEVER present (probed 2019/2021/2024/2026 — zero rows every era; LIKE-scan on
      2026-09-28 confirms absence, nearest act_symbols are unrelated single names).
  (b) **2024-08-05 yen-carry tail ABSENT**: SPY zero rows 2024-07-30..2024-08-13
      (probed 07-30, 08-01, 08-02, 08-05, 08-06, 08-07, 08-08, 08-09, 08-12, 08-13
      — all 0; 2024-07-29=110 and 2024-08-14=114 bracket the hole). volatility_history
      also empty that day. H1_report requires the 2024-08 tail in-sample — hard fail.
  (c) **2020-03 COVID tail PARTIAL**: present 03-09/03-16/03-18/03-23, absent
      03-12/03-17/03-24 — early-era cadence is ~2-3 days/week, not daily.
  (d) **Sampled grid, not full chain**: SPY 2026-09-28 = 210 rows, 4 expiries
      (11d/25d/32d/53d), 33 strikes 535..995 vs our ground-truth CBOE capture
      (archive/20260929/SPY.csv) of thousands of rows spanning expiries to 2029.
      Early era ~66 rows/day. Density ~5-10% of full OPRA.
Cadence EVOLVED: sporadic (2019-2024, ~2-3 d/wk) → near-daily (2025-2026).
+ `volatility_history` table (FREE, live): daily per-symbol HV + IV series from
2019-02-09, same 5/9 symbol limitation, missing 2024-08-05.

**PART-CREDIT 2 — env POLYGON_KEY (free stocks-basic tier, confirmed live but
options-entitled = NO).** Reference endpoints 200 OK; options snapshot endpoint
403 NOT_AUTHORIZED ("upgrade your plan"). The existing key cannot serve any
historical option chain data. ThetaData has no advertised free options tier
(cheapest Options plan $40/mo, 6y history; Standard $80/mo 10y; Pro $160/mo 14y).

## What this changes

1. FINDINGS.md's "licensed-data decision, not free data" claim is now VERIFIED,
   not assumed — with one correction: a free sampled dataset DOES exist (DoltHub)
   and is live; it just fails the sleeve-backfill gates on symbols + tails + density.
2. The forward-collection harness (H1, launchd 04:20 CST daily) remains the ONLY
   free path to the H1 sleeve. Its daily accrual is now the binding constraint on
   the sleeve timeline (~2-3y to 500-750d of factor history). Backfill remains
   operator-payable only.

## Licensed-price memo (operator decision, concrete numbers)

| Source | Cheapest qualifying tier | Price | Coverage vs spec |
|---|---|---|---|
| ThetaData | Options ($40/mo) | $40/mo ($480/yr) | 6y EOD, full chains, OPRA — meets 3y min, tails in-sample |
| ThetaData | Options Standard | $80/mo | 10y, tick-level |
| Polygon (massive.com) | Options Starter-class | ~$29-199/mo (options tab not published; stocks tiers $29/$79/$199) | 2-20y by tier |
| historicaloptiondata.com | Per-symbol-year files | ~$2-20/file class | EOD chains w/ greeks+IV; 9 symbols × ~5y ≈ 45 files |
| ORATS / ivolatility / CBOE DataShop | — | not probed this session (pages JS-walled) | — |

Cheapest concrete path to spec: **ThetaData Options $40/mo** (6y, full EOD chains,
both tails in-sample) — one-month sub ($40) suffices to download the full 2019→2026
EOD history for 9 symbols if quota permits; or historicaloptiondata.com one-shot
file purchase. Both are single-digit dollars per symbol-year.

## Next steps (if operator funds backfill)

- Sub, bulk-download 2019→2026 EOD chains for the 9 symbols, convert to the
  h1_collect.py snapshot CSV schema (spot,exp,typ,strike,bid,ask,iv,oi,volume,
  delta,...), recompute the H1 factors panel, and run the H1_report §7 sleeve
  construction with 2020-03 + 2024-08 tails in-sample. This collapses the sleeve
  timeline from ~2029 to days.

## Honest limitations of this census

- Remote DoltHub SQL console: ~60s query deadline; aggressive probing rate-limited
  (observed curl timeouts, retried with backoff; every number above is from a
  successful query, no inference from failed cells).
- Polygon options pricing tiers: pricing page options tab is JS-rendered; stocks
  tiers captured but options tiers not enumerated (403 message confirms tier gate).
- ORATS/ivolatility/CBOE DataShop prices not probed (JS-walled pages this session).
- 2020-03/2024-08 cadence mapped by date-ladder probes on trading days, not
  exhaustive per-day enumeration (each cell a successful COUNT query).

DONE HUNT_BACKFILL
