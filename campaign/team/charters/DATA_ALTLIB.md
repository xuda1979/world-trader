# DATA_ALTLIB — no-key alt-data & market-breadth libraries
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Use the no-key open-source libraries from the source list to add NEW alt-data/breadth series the
campaign currently lacks: CoinPaprika / CoinGecko breadth, efinance / ml4t-data, sentiment/fear indexes
that aren't already on disk (check first). These feed decorrelation/regime engines.

## Source (pip libraries, direct HTTP under the hood)
- CoinPaprika (2000+ coins 1y, no key), CoinGecko free, efinance, ml4t-data.
- Cross check existing tools/quant/data/altme_fng, crypto_fg, defillama_stables, coingecko_breadth,
  cnn_fg, stocktwits — only ADD what's genuinely missing.

## Deliverable
- tools/quant/data/altlib/<family>/<SYM>.csv + manifest.csv. Prefer long-span breadths (count,
  dominance, funding, cross-sectional dispersion) usable for regime/decorrelation, not just prices.

## Rules
- DIRECT HTTP (no browser). Sleep between calls. Fail-closed lint. DATA-ONLY, no backtests.
- Only write inside tools/quant/data/altlib/. Do not overwrite existing alt dirs.

## Done marker
Last line of FINDINGS.md exactly: DATA_ALTLIB DONE
