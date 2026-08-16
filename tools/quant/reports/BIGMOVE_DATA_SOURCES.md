# bigmove — New Data Sources: Feasibility Assessment (2026-08-15)

**Goal:** Add richer/independent data to raise IC -> push honest Sharpe toward
>=2 (current honest ceiling ~1.1 on OHLCV+macro ZA daily panel).

## Environment constraints (verified)
- **NO live network access** in this environment. All API/'e-fetch data sources
  are unreachable right now:
    - TwelveData, Polygon, Finnhub (earnings), CBOE (options), GDELT/news feeds.
  Direct probe of api.twelvedata.com returned nothing (no route).
- Therefore we can ONLY use data already cached on disk.

## Locally-available additional data (status)
| source | size/coverage | usable? |
|--------|---------------|---------|
| polygon_intraday | 17 names x ~3 months (5-min) | too short (no walk-forward) |
| pead earnings_events | 625 events, 2026-08-06..14 only | 2-wk window too short; tiny panel overlap |
| polygon_v2 | 351 names x ~2 yr (2024-08..2026-08) | larger universe but DAILY OHLCV (same info type, won't raise IC ceiling) |
| COT / FRED macro | long history | already partly in feature set (macro) |

## Validation run (earnings surprise signal)
Matched 625 recent earnings (eps surprise) to price panels -> only **n=15** had
next-day price overlap. Spearman corr(surprise, next-day return) = **0.17**
(directionally positive = earnings surprise DOES carry signal, as expected), but
**n=15 is far too small to be conclusive** for a deployable model layer.

## Honest conclusion
The recommended richer data is **not acquirable at the scale/history needed** in
this environment (no network; cached richer data too short). The data ceiling to
SR>=2 (OHLCV+macro) therefore still stands here. **Requires: (a) live network
access to a real provider (Polygon/Finnhub/CBOE/fundamentals), and (b) several
YEARS of history** (earnings/options/news) to train the 2018-2026 walk-forward.
Without those, adding a robust data layer is not possible in this sandbox.

Artifacts: this report; (analysis script): /tmp/pead.py.
