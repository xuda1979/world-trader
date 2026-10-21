# RES_STATARB — relative-value / statistical-arbitrage engines
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Find >=1 NEW decorrelated DAILY engine from PAIRS / sector-relative mean-reversion on the big
panels. Distinct from RES_REVERSAL (single-name reversal) and RES_BASIS (commodity spreads):
this is cross-sectional relative value WITHIN equities/ETFs (long outperformer-vs-underperformer
in the SAME sector/theme), which is dollar-neutral and decorrelated to market direction.

## Data (verify yourself)
- tools/quant/data/twelve_big/12_extend/, tools/quant/data/more_etf/, kenfrench/.
- Sector ETF families (XLE/XLB/XLF/XLI/XLK/XLY/XLP/XLU/XLV/XLRE/XLC) for sector-relative.
- Same-theme pairs: gold miners GDX/GDXJ, semis SMH/SOX proxies, regional banks KBE/KRE, etc.

## Ideas
- Sector-relative momentum/reversal (long top sector vs short bottom sector, T+1, vol-managed).
- Cointegrated pairs z-reversion (log-price gap z) with a real economic link (like brwt worked).
- Theme-relative (growth vs value ETF basket) only if decorrelated to champion.

## FIRST STEP
`python3 campaign/team/lib/corr_gate.py <cand.csv> 0.15` — reject if |corr| to champion >= 0.15.

## Gates (ALL, via campaign/bt/)
SR>=1.5 net; H1/H2>=0.5; <=2 neg yrs >-5%; 200x block-scramble p<0.05; |corr|<0.15 to champion;
T+1; 6.4bps/side full |dW|; borrow + shortability modeled; flatten ac1<0.5 & uniqR>=0.08.

## Deliverable
Sleeve CSV + .meta + thin repro under campaign/team/agents/RES_STATARB/sleeves/. REJECT-with-numbers ok.

## Done marker
Last line of FINDINGS.md exactly: RES_STATARB DONE
