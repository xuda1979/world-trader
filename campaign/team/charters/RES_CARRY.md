# RES_CARRY — FX/commodity carry engines (beyond CFX4)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Find >=1 NEW decorrelated DAILY engine from carry. The champion has CFX4 (FX 4-book z-rev) and
carryv2 (GLD) but NO broad multi-pair FX carry with a genuine funding mechanism. Carry is a
distinct return premia, decorrelated to momentum/reversal.

## Data (verify yourself)
- tools/quant/data/fx/ (8 pairs 2007+: EUR_USD,GBP_USD,USD_JPY,USD_CAD,AUD_USD,NZD_USD,USD_CHF,EUR_GBP)
- tools/quant/data/ecb_fx/, tools/quant/data/ecb_yc/, tools/quant/data/boe_curve (if present)
- FRED rates for funding differentials (DGS*, SOFR/T-bill proxies), cross-country 10y.

## Ideas
- FX carry: long high-yield vs low-yield currency basket (AUD/NZD vs JPY/CHF), funded via rate diff.
- Commodity carry (contango slope) on continuous futures/spot proxies.
- Funding-curve dl (rate differential momentum) only if T+1 causal survives.
- CARRY WARNING (empirical): EM/broad-dollar momentum FAILED before; prefer developed-pair carry.

## FIRST STEP
`python3 campaign/team/lib/corr_gate.py <cand.csv> 0.15` — reject if |corr| to champion >= 0.15.

## Gates (ALL, via campaign/bt/)
SR>=1.5 net; H1/H2>=0.5; <=2 neg yrs >-5%; 200x block-scramble p<0.05; |corr|<0.15 to champion;
T+1; 6.4bps/side full |dW|; flatten ac1<0.5 & uniqR>=0.08.

## Deliverable
Sleeve CSV + .meta + thin repro under campaign/team/agents/RES_CARRY/sleeves/. REJECT-with-numbers ok.

## Done marker
Last line of FINDINGS.md exactly: RES_CARRY DONE
