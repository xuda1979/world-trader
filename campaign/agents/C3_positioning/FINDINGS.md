# C3_positioning — FINDINGS (Round 1)

Environment: python3 + pandas; harness gates from B2_highfreq/gates.py; costs 6bps/side x
one-side turnover; T+1 execution enforced as pos.shift(1)*ret in build_ret
(campaign/scripts/c3_common.py). Data: data_cot/cot_tidy.csv (5 tradeable markets with
on-disk prices), tff_tidy.csv (spx/dow/us10y/eur/jpy/vix + more), prices in data_fred/.
Repro: campaign/scripts/c3_idea_sweeps.py (+ c3_common.py).

## CRITICAL FIX RECORDED
build_ret originally credited pos.shift(0)*ret (same-day = 1-day lookahead). Fixed to
pos.shift(1)*ret. Effect measured: oiXprice "SR 3.18, ann +126%" (wti) -> -0.26 honest.
ALL numbers below are post-fix.

1. Idea 1 — Money-manager net positioning z(52w), contrarian vs momentum, clipped ±1:
   Per-market best (all still far under gate a SR>=1.0):
   - wti mm z26 k1.5 momentum: SR +0.33, ann +7.6%, negy 8, worst -33.3%
   - natgas mm z104 k1.0 momentum: SR +0.28, ann +17.4%, negy 12, worst -58.6%
   - xau swap z52 contr: SR +0.11; slv mm z52 contr: SR +0.22 (negy 9)
   - copx mm z104 k1.5 momentum: SR +0.50, ann +11.1%, negy 9, worst -28.1%
   - spec_net == mm net almost exactly (corr ~1); swap variants SR 0.11-0.29.
   VERDICT: FAIL gate a (all SR < 0.51 standalone). Also fail c/d/e (negy 8-12, worst
   -30 to -59%).

2. Idea 2 — Positioning-momentum hybrid (follow mid-z, fade extremes, sign-flip at |z|>1):
   Best natgas SR +0.22 negy 15; slv +0.03; wti/xau/copx <= +0.2. No market beats its
   plain z-trend variant. VERDICT: FAIL gate a.

3. Idea 3 — TFF leveraged-fund (lf_net) vs asset-manager (am_net) positioning:
   - spx lf_net z52 k1.5 momentum: SR +0.43, ann +6.6%, negy 4, worst -17.2% (best TFF)
   - spx lf mom + am fade 50/50: SR +0.40
   - vix am_net z26 contr: SR +0.59, ann ~+12%, negy 5, worst -31.1% (vs 30% ann VIX vol
     -> implied vol-targeted ~ -; still fails gate a)
   - dow/us10y/fx TFF: all SR <= +0.27.
   VERDICT: FAIL gate a (0.59 max). negy 4-5 OK, worst fails gate d.

4. Idea 4 — OI-change z x price-change confirmation:
   WITHOUT lag (lookahead) wti SR +3.18 — bug found and fixed. Honest (T+1, and signal
   uses same-week price sign): SR -0.26 wti, -0.77 copx, all 5 markets negative.
   VERDICT: FAIL (and proved the harness bug's size: +3.4 SR of lookahead).

5. Idea 5 — Intraday (polygon 17 stocks, RTH 5-min, 2024-12 to 2025-06, ~6.5 months):
   - overnight (prev RTH close -> 09:30) mean -3.4bp/day, SR -0.31 raw, -1.41 net
   - intraday (09:30 -> close) mean +1.03bp/day, net SR -0.81
   - first-hour fade: pooled rest-of-day SR -0.22 raw / -0.74 net; corr(h1, rest)=+0.125
     (MOMENTUM sign, not fade); decile spread non-monotonic (dec0 -34.6bp vs dec9 +62.7bp)
   - window far too short for yearly gate (needs >=5yrs); charter says document caveat.
   VERDICT: FAIL all gates; window too short; effect sign is opposite to the charter's
   prior (first-hour momentum persists, it does not fade).

6. Idea 6 — Composite EW of per-market books (7 books, vol-normalized vt10%):
   - 7-book composite: SR 0.42, ann 5.9%, mdd -35.9%, negy 9, H1 0.11 vs H2 0.83,
     scramble p 0.825 (real SR at 17.5th pctile!), corr-to-blend 0.071 (passes f only)
   - drop-natgas 5-book: SR 0.53, ann 6.5%, negy 5, H1 0.18/H2 1.11, p 0.685
   - extremes-only fade composite (|z|>1.5 entry): SR -0.02, mdd -54.7, p 0.930.
   VERDICT: FAIL gates a/c/e/d decisively. Weekly positioning spread across these 5
   markets is too thin to clear SR 1.0.

7. Extra (not in charter, tried to rescue): delta-positioning flow momentum (diff(4/8)
   z(52/104)):
   - best: copx flow8 z52 momentum: SR +0.60, ann +16.6%, negy 5, worst -32.2%
   - wti flow8 z104: +0.37; natgas flow8 z104: +0.20; xau flow4 z104 fade: +0.43.
   VERDICT: FAIL gate a (0.60 < 1.0). Best single COT-family variant found; kept in
   repro script (c3_idea_sweeps.py) for possible Round-2 combination, but do NOT blend
   in yet (cherry-pick risk; negy/worst also fail).

## SWEEP COVERAGE (post-fix, ~450 variants)
Z-windows 26/52/104, clip k 1.0/1.5, contr+momentum, mm/spec/swap/OI, flow 4/8w,
TFF lf/am on 6 financials, extremes-only 1.25/1.5/2.0, trend-filters. Top 20 all
SR in [0.32, 0.60], i.e. a ~2x gap to gate (a) that no composite closes (composites
average SR ~0.4 because books are mutually weakly corr 0.02-0.37 but individually ~0).

## BOTTOM LINE (HONEST)
COT/TFF weekly positioning at report_date->T+1 has NO standalone sleeve that reaches
SR 1.0 net after 6bps on the 5 tradeable markets (wti/brent not separately COT-covered
pre-2022, natgas, xau, slv, copx) + TFF financials (spx best 0.43). Signature of the
data: weekly granularity = max ~52 independent obs/yr/market; spec positions are a
lagging echo of price (mm/spec z follows trend, corr to next-quarter price ~0); the
only large effects in the file were artifacts (lookahead). Recommendation to coordinator:
positioning CANNOT contribute a standalone gate-passing sleeve this round; revisit only
as a tertiary overlay/filter (e.g., extremes-only size modulation), never a core book.
Round 1 charter ideas 1-6 all executed; 0/6 passed; no sleeve CSVs saved (nothing met
the save contract).
ROUND 1 DONE
